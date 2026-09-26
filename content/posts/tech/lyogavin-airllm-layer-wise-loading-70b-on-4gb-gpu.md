---
title: "AirLLM 怎么把 70B 模型跑进 4GB 显存：把权重当数据流，而不是常驻显存"
date: 2026-07-20T03:02:36+08:00
lastmod: "2026-09-25T12:00:00+08:00"
categories: ["技术笔记"]
tags: ["LLM", "显存优化", "推理优化", "低资源"]
description: "AirLLM 不量化、不蒸馏、不剪枝，靠逐层流式加载把 70B 模型跑进单卡 4GB 显存，最新版本还支持 Kimi K3 2.8T 与小显存 LoRA 训练。本文对照 main 分支源码拆解 meta device + forward hook 的流式实现、MoE 按 expert 加载、block-wise 量化与 MLX 后端，并给出适用边界与排查表。"
slug: lyogavin-airllm-layer-wise-loading-70b-on-4gb-gpu
github_repo: "lyogavin/airllm"
source_key: "gh:lyogavin/airllm"

---

# AirLLM 怎么把 70B 模型跑进 4GB 显存：把权重当数据流，而不是常驻显存

常规推理把全部权重装进显存，70B 模型 FP16 就是约 140GB，多数卡直接出局。AirLLM 把这笔账反过来算：显存里永远只放一个模块的权重，其余的躺在磁盘上，用到哪层搬哪层。显存需求从「模型总大小」变成「最大单层大小」，代价是每个 token 都要把全部权重重新装载一遍——这是一笔用存储带宽换显存容量的交易，收益写在标题里，代价也写在明面上：快不起来。

本文的判断钉在三份证据上：GitHub API 2026-09-25 的仓库读数、main 分支 README、`air_llm/airllm/` 下的源码。凡是只有 README 口径或属于机制推断的，都在原位标出。

**目录**

- [仓库现状](#仓库现状)
- [系统地图](#系统地图)
- [为什么可行：显存装一层，不装整个模型](#为什么可行显存装一层不装整个模型)
- [生成一个 token 时发生了什么](#生成一个-token-时发生了什么)
- [MoE：按 expert 流式，粒度比层更细](#moe按-expert-流式粒度比层更细)
- [压缩：只量化权重，因为瓶颈在过盘](#压缩只量化权重因为瓶颈在过盘)
- [macOS：另一条 MLX 路径](#macos另一条-mlx-路径)
- [训练：v4.0 的新故事](#训练v40-的新故事)
- [小显存能装下什么：数字与口径](#小显存能装下什么数字与口径)
- [快速上手](#快速上手)
- [排查表](#排查表)
- [边界与采用建议](#边界与采用建议)
- [维护指引](#维护指引)

## 仓库现状

| 项目 | 读数 | 口径 |
|---|---|---|
| Stars / Forks | 34,769 / 3,660 | GitHub API，2026-09-25 |
| 协议 | Apache-2.0 | GitHub license 字段 |
| 仓库创建 / 最近推送 | 2023-06-12 / 2026-09-24 | GitHub API，持续活跃 |
| PyPI 最新版 | 4.0.0（2026-09-05 发布） | PyPI JSON API |
| 关键依赖约束 | `torch>=2.4`、`transformers>=4.49,<6` | PyPI `requires_dist` |

作者 Gavin Li，GitHub 主页标注 Anima AI 创始人；官方引用条目为 *AirLLM: scaling large language models on low-end commodity computers*（2023）。README 的致谢节写明：最初代码基于 SimJeg 在 Kaggle LLM Science Exam 比赛中的方案。

## 系统地图

AirLLM 的源码不大，职责分七块，读源码和排障时不要混：

| 模块 | 位置 | 职责 |
|---|---|---|
| 入口分发 | `auto_model.py` | 读模型 config 的 architectures 字段：非标准布局走 `ARCH_OVERRIDES` 专属子类，其余全部交给通用流式基类 |
| 流式引擎 | `airllm_base.py` | meta device 上建模型，用 forward hook 把每个模块的权重磁盘→GPU→meta 换入换出，单 worker 线程预取 |
| 分片持久化 | `airllm/persist/` | 首次加载时把 checkpoint 拆成逐层 safetensors shard，之后直接读分片 |
| MoE expert 流式 | `airllm_base.py` 内 `_setup_expert_streaming` | 不按层装，按 expert 装，只物化 token 实际路由到的 expert |
| 权重压缩 | `compression` 参数 | 4bit/8bit block-wise 量化，缩小过盘体积 |
| macOS 后端 | `airllm_llama_mlx.py` | darwin 平台自动切换到 MLX 实现，仅支持 Apple silicon |
| LoRA 训练 | `airllm_lora.py`、`lora_linear.py`、examples 脚本 | 冻结权重逐层流过，适配器驻留 GPU（v4.0 新增） |

## 为什么可行：显存装一层，不装整个模型

README 把原理压成一句话：显存需求取决于模型单层的大小，而不是模型总大小——因为 GPU 上同时只有一个层。以 Llama 3.x 70B 为例，全量 FP16 约 140GB，摊到 80 个 decoder 层，单层只有 1-2GB，4GB 显存装一层绰绰有余。MoE 巨兽不适用这笔算术——单个 MoE 层展开能有几十 GB——这正是后面「按 expert 流式」要解决的问题。

「只装一层」在源码里是三件事的叠加：

1. **meta device 建模型**。`init_model` 先在 meta 设备上实例化真正的 transformers 模型——不占任何内存，但 forward 和 generation 的全部逻辑都由 transformers 负责。注意力实现优先 `sdpa`，不支持时回退 `eager`。
2. **forward hook 换入换出**。embedding、每个 decoder 层、final norm、lm_head 各挂一对 hook：`_pre_hook` 在模块执行前从分片读出权重搬上 GPU，`_post_hook` 执行完立刻把参数放回 meta 并清理显存。
3. **预取**。算第 N 层时，一个单 worker 线程池在后台读第 N+1 层，让磁盘 IO 和计算重叠。v2.5 更新日志给的数字是提速 10%。注意单个预取层最多用 2GiB 锁页内存（源码 `max_pinned_layer_bytes`），更大的层退回普通分页内存。

两个例外值得知道：词表和 lm_head 共享权重的模型（tied embeddings），embedding 直接常驻 GPU，只流式 decoder 层；多模态模型的视觉塔、projector 这类不参与流式的模块也一次性常驻——README 源码注释说它们「远小于 1GB」。

## 生成一个 token 时发生了什么

把上面的机制串成一次真实推理（`generate` 调用路径）：

1. `AutoModel.from_pretrained(...)` 先查本地有没有分好的层 shard；没有就下载 checkpoint、按层拆分保存到 HuggingFace 缓存目录（可用 `layer_shards_saving_path` 另指定），这一步磁盘开销很大。
2. 初始化阶段在 meta 上建出完整模型，transformers 接管后续一切计算逻辑。
3. 每次 forward：embedding → 逐个 decoder 层（每层执行前读盘上 GPU，执行后释放）→ final norm → lm_head。开了预取的话，读盘发生在上一层计算期间。
4. `generate` 每生成一个新 token，就完整重复一遍第 3 步。

这就是慢的机制根源，不需要神秘数字：**每个 token，全部流式权重都要从分片重新装载一遍**（大分片能否被操作系统的页缓存兜住，取决于主机内存）。速度上限落在存储和内存带宽上，与 GPU 算力基本无关。想知道自己机器的真实吞吐，初始化时传 `profiling_mode=True`，各模块的耗时会被打出来——比相信任何别人的倍数都可靠。

## MoE：按 expert 流式，粒度比层更细

对稀疏 MoE，按层加载就浪费了。`_setup_expert_streaming` 的源码注释给了一组数字：Kimi K3 一层内的全部 expert 展开约 55GB，而一个 token 实际路由到的 expert 只有约 1GB。所以它给每个 expert 模块单独挂 hook，路由到谁才物化谁。

这条路径有两个依赖：分片必须是 safetensors（要能读单个 tensor）；compressed-tensors 注册的解压 hook 会被主动摘掉——那个 hook 会在首次 forward 时展开整个层，一层就变回 56GB，改由 AirLLM 在加载每个 expert 时自己解压。

另一类特例是 Qwen3.8-Flash-Next 的约 51B 参数 n-gram（PLE）表，bf16 下约 102GB：它不走流式也不上 GPU，直接以文件映射方式留在磁盘上由 CPU 查表（源码 `MmapEmbedding`），所以 README 说一台 64GB 内存的机器就能跑这个模型。

## 压缩：只量化权重，因为瓶颈在过盘

常规量化要同时压 weights 和 activations 才能真正加速，精度难保；AirLLM 的瓶颈在磁盘加载，只需要让过盘的体积变小——所以它只量化权重。README 对压缩能力的原话是：进一步把推理速度提到最高 3 倍，精度损失几乎可以忽略（"almost ignorable accuracy loss"）。方法出自 Dettmers 与 Zettlemoyer 的论文 *The case for 4-bit precision: k-bit Inference Scaling Laws*（arXiv:2212.09720）。

用法两步：装 `bitsandbytes`，初始化时传 `compression='4bit'` 或 `'8bit'`：

```python
model = AutoModel.from_pretrained("garage-bAInd/Platypus2-70B-instruct",
                     compression='4bit' # specify '8bit' for 8-bit block-wise quantization
                    )
```

一个容易被忽略的交互：源码里开了 compression 会自动关掉 prefetching（日志会提示），所以压缩省下的加载时间有一部分是靠牺牲预取换来的，实际收益建议用 `profiling_mode` 在自己机器上量。

## macOS：另一条 MLX 路径

`auto_model.py` 在 darwin 平台上不做流式分发，直接返回 `AirLLMLlamaMlx`——一套基于 MLX（Apple 的数组框架，跑在 Metal 上）的独立实现。要求 Apple silicon 芯片，装好 `mlx` 和 `torch` 后按 Linux 同样的代码跑。

注意 README 并没有承诺 Mac 上靠统一内存整模直载，那是另一回事；Mac 用户跑大模型确实比 4GB PC 显卡从容（统一内存可以大得多），但 AirLLM 的 Mac 路径是实现层面的分支，与 CUDA 流式引擎是两套代码。

## 训练：v4.0 的新故事

2026 年 9 月的更新把同一招用到了训练上：冻结的基础权重逐层从磁盘流过 GPU，只有 LoRA 适配器常驻。README 口径的实测数字：Qwen3.8-Flash-Next（125B）在 6GB 显存内可训练（RTX 3060 Ti），Qwen3.8-27B 在 seq 512 下约 2GB。

README 特意声明这不是 Hugging Face Trainer 也不是 bitsandbytes QLoRA。仓库提供两个脚本和对应 Python API：

```bash
python air_llm/examples/train_qwen38_flash_next_lora.py \
  --data my_data.jsonl \
  --seq-len 512 \
  --epochs 1 \
  --save-adapter qwen38-flash-next-lora.pt
```

Python 侧通过 `AirLLMLoRAQwen4Exp`（Flash-Next）或 `AirLLMLoRA`（27B）做 `train_step` / `save_adapter`，数据是每行一个 JSON 对象的 jsonl，支持 `text` 整段预测或 `prompt`/`completion` 只对补全部分计 loss。

## 小显存能装下什么：数字与口径

README 的显存表是其最常被引用的部分，注意这些都是官方自述的实测口径，测试卡 README 有逐条标注：

| 模型 | 规模 | 显存 | README 标注的测试卡 |
|---|---|---|---|
| Qwen3 / Mistral / Phi | ≈8B | ~1-2 GB | — |
| Qwen3-30B / Mixtral | 30-47B MoE | ~1-3 GB | — |
| Qwen3.8-27B（稠密 VL） | 27B | 3.33 GB | RTX 3090 |
| Qwen3-235B | 235B MoE | ~3 GB | — |
| Qwen3.8-Flash-Next | ~180B（125B MoE + PLE） | 5.95 GB | RTX 4090 |
| Llama 3.x 70B | 70B 全精度 | ~4 GB | — |
| Llama 3.1 405B | 405B | ~8 GB | — |
| DeepSeek-V3 | 671B | ~12 GB | — |
| Kimi K3 | 2.8T | 3.72 GB | RTX 6000 Ada |

从这些数字能推出的和不能推出的：显存数字成立的前提是接受流式速度，它们回答「装不装得下」，不回答「快不快」；MoE 模型的显存优势来自按 expert 流式，稠密模型没有这一层红利。

部分模型有附加门槛，README 逐条写明：Kimi K3 需要 `compressed-tensors` 与 `flash-attn`（其模型代码强制 flash attention）、CUDA 12 版 torch（flash-attn 尚无 CUDA 13 预编译轮子）、transformers 4.56.x（其 remote code 在 5.x 上加载失败）；Flash-Next 需要带 `qwen4_exp` 的 transformers git 版，且拆分阶段约需 360GB 检查点磁盘（`delete_original=True` 可在拆完后回收原件）。

支持范围由两件事决定：通用基类 `AirLLMBaseModel` 能流式任何标准 `*ForCausalLM`——「transformers 支持即支持」，所以 README 敢写「大多数新模型发布当天就能跑」；非标准模块布局的架构走 `ARCH_OVERRIDES` 里的 7 个专属子类（ChatGLM、QWen、Baichuan、InternLM、Kimi K3、Qwen3.5、Qwen4Exp）。

## 快速上手

```bash
pip install airllm
```

```python
from airllm import AutoModel

MAX_LENGTH = 128
model = AutoModel.from_pretrained("Qwen/Qwen3-32B")

input_tokens = model.tokenizer(['What is the capital of United States?'],
    return_tensors="pt",
    return_attention_mask=False,
    truncation=True,
    max_length=MAX_LENGTH,
    padding=False)

generation_output = model.generate(
    input_tokens['input_ids'].cuda(),
    max_new_tokens=20,
    use_cache=True,
    return_dict_in_generate=True)

print(model.tokenizer.decode(generation_output.sequences[0]))
```

唯一要提前准备的是磁盘：拆分阶段的开销接近原模型体积，缓存目录空间不足会直接报错。

## 排查表

README FAQ 覆盖的四类高频故障：

| 报错 | 原因与处理 |
|---|---|
| `MetadataIncompleteBuffer`（safetensors 反序列化失败） | 几乎都是磁盘满了。拆分很吃磁盘：清缓存或扩容后重跑 |
| `ValueError: max() arg is an empty sequence` | 用了 Llama2 类去加载 Qwen/ChatGLM。改用 `AutoModel.from_pretrained(...)` |
| `401 Client Error ... is gated` | 门控模型需要 token：`from_pretrained(..., hf_token='HF_API_TOKEN')` |
| `Asking to pad but the tokenizer does not have a padding token` | 该 tokenizer 无 pad token，把 `padding=False` 关掉填充 |

## 边界与采用建议

**适合**：显存极小的卡上做离线批处理——一次喂一批 prompt，等它慢慢算完；想在本机体验 235B、671B 乃至 2.8T 模型行为的开发者；layer-wise 推理的研究起点（代码量小，机制全在 `airllm_base.py` 一个文件里）；以及 v4.0 之后的小显存 LoRA 微调。

**不适合**：实时对话——每个 token 全权重过盘，这在机制上就快不起来，不是调参能解决的；高 QPS 生产服务——那是 vLLM、SGLang 的领地；长上下文场景——KV cache 驻留 GPU 且随序列长度线性增长，4GB 显存下很快被挤爆，README 示例把 `MAX_LENGTH` 限到 128、基类默认 `max_seq_len=512`，这不是随意取值。

采用顺序建议：先 `pip install airllm` 跑通 quickstart，确认你的机器能完成首次拆分；开 `profiling_mode` 量一下自己盘上的单 token 耗时，用真实数字判断延迟是否可接受；嫌慢再加 `compression='4bit'`（记得它会关掉预取，量化前后各量一次）；如果结论是延迟不可接受，问题不在 AirLLM 的参数，在「显存装不下模型」这个前提本身——换量化推理框架或租卡。

## 维护指引

本文数字的核实口径与失效条件：

- Stars/forks 与仓库活跃度：GitHub API，2026-09-25 读数。版本发布后这些数字会漂移，引用时更新日期重查即可。
- 显存表、模型支持范围、训练数字：README（main 分支，2026-09-25 读取），官方自述口径。以 README Updates 节为准判断是否过期。
- 流式机制、expert streaming、compression 与 prefetching 互斥、锁页内存上限：`air_llm/airllm/airllm_base.py` 与 `auto_model.py` 源码。函数名变了就重查。
- PyPI 版本与依赖约束：PyPI JSON API，4.0.0 / 2026-09-05。
- 任一依赖约束（如 transformers 版本上限）随上游发布变化频繁，跑不通时先对 PyPI 的 `requires_dist`。

## 链接

- 仓库：https://github.com/lyogavin/airllm
- PyPI：https://pypi.org/project/airllm/
- 量化论文：https://arxiv.org/abs/2212.09720
