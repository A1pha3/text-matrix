---
title: "AirLLM：单卡 4GB 跑 70B，把显存从「装下模型」改成「装下一层」"
date: "2026-06-04T15:00:00+08:00"
slug: airllm-lyogavin-low-vram-llm-inference-guide
github_repo: "lyogavin/airllm"
source_key: "gh:lyogavin/airllm"
description: "AirLLM 把模型权重逐层流过显存：70B 用 4GB、405B 用 8GB、DeepSeek-V3 671B 约 12GB、Kimi K3 2.8T 用 3.72GB，v4.0 还能在 6GB 内 LoRA 微调 125B 模型；本文讲清机制边界、社区实测速度与采用决策。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "推理优化", "显存优化", "量化", "macOS"]
---

# AirLLM：单卡 4GB 跑 70B，把显存从「装下模型」改成「装下一层」

## 核心判断

`AirLLM`（仓库 [lyogavin/airllm](https://github.com/lyogavin/airllm)）解决的是一个被多数推理库放弃的问题：**在 4-8GB 显存的消费级硬件上，跑起 70B 甚至 405B、671B 参数的原始权重模型**。它走的是「分时换入」这条路——平时只把当前正在计算的那一层参数读进显存，其余层在磁盘上待机，算完即弃，下一层顶上。

这条路换来了几件别家没同时做到的事：

1. **4GB VRAM 跑 70B**：不量化、不蒸馏、不剪枝，权重保持原始 fp16/bf16 精度
2. **8GB VRAM 跑 405B Llama 3.1**：405B 的权重在 fp16 下约 810GB——原本得在多张高端 GPU 上才能装下推理，AirLLM 把它压到单卡 8GB
3. **约 12GB 跑 DeepSeek-V3（671B）**、**约 3GB 跑 Qwen3-235B**：对稀疏 MoE 模型不再整层加载，只流式加载单个 token 实际路由到的专家
4. **6GB 显存微调 125B 模型（v4.0）**：训练复用同一套逐层流式机制，冻结权重从磁盘过、LoRA 适配器留在 GPU——2026 年 9 月加入的能力，README 称 Qwen3.8-Flash-Next（125B）在一张 RTX 3060 Ti 上即可训练

2026-07 起支持 Kimi K3（2.8T，README 称之为迄今最大的开源模型），单张 RTX 6000 Ada 上端到端实测 3.72GB 显存跑通；2026-08 又接入 Qwen3.8-27B（27B 密集视觉模型，3.33GB）和 Qwen3.8-Flash-Next（125B MoE 加约 51B n-gram 嵌入表，5.95GB）。

代价同样明确。逐层换入意味着每生成一个 token 都要把模型层从磁盘读一遍，**吞吐低**。README 公布的从来是显存数字而非绝对速度（唯一的速度声明是量化「最高 3x」的相对倍数），官方定位是「单卡 4GB 跑 70B」；社区实测的速度跨度极大，从约 13 秒一个 token 到两分钟一个 token 都有（后面「性能特征」一节有具体数据）。AirLLM 适合论文复现、离线批处理、边缘设备验证这类对延迟不敏感、对显存极度敏感的场景；高 QPS 服务请直接走 vLLM / TensorRT-LLM。

读完这篇文章，你应当能判断：在什么样的模型规模、显存大小和延迟要求下，AirLLM 才是对的选择——而不是顺手就用。

## 项目地图

| 维度 | 关键信息 |
|------|----------|
| 仓库 | [lyogavin/airllm](https://github.com/lyogavin/airllm) |
| PyPI | [pypi.org/project/airllm](https://pypi.org/project/airllm/) |
| 许可证 | Apache-2.0 |
| Stars / Forks | 33,782 / 3,557（GitHub API，2026-09-07 快照） |
| 主语言 | Jupyter Notebook（推理内核为 PyTorch） |
| 定位 | 70B 推理跑在单张 4GB GPU 上（仓库官方描述） |
| 依赖要点 | 量化需 bitsandbytes；Kimi K3 另需 compressed-tensors、flash-attn |

### 版本里程碑

| 时间 | 事件 |
|------|------|
| 2023-11 | AirLLM 初始版本 |
| 2023-12 | v2.0：块级量化压缩，官方称最高 3x 提速 |
| 2023-12 | 补 safetensors 与 ChatGLM / QWen / Baichuan / Mistral / InternLM 支持 |
| 2023-12 | v2.5：预取（prefetching）重叠加载与计算，官方称约 10% 提升 |
| 2023-12 | v2.6：`AutoModel` 自动识别模型类型；v2.7：Mixtral；v2.8.2：macOS 跑 70B |
| 2024-04 | Llama3 70B 在 4GB 单卡原生支持 |
| 2024-07 | Llama 3.1 405B 支持，配 8bit/4bit 量化 |
| 2024-08 | v2.10：CPU 推理与非分片模型；v2.11：Qwen2.5 |
| 2026-06 | v3.0：FP8 模型支持，DeepSeek-V3（671B）约 12GB、Qwen3-235B 约 3GB |
| 2026-07 | v3.1：Kimi K3（2.8T）单卡 3.72GB 跑通 |
| 2026-08 | v3.2：Qwen3.8-27B（3.33GB）；v3.3：Qwen3.8-Flash-Next（5.95GB） |
| 2026-09 | v4.0：流式 LoRA 训练，125B 模型 6GB 显存内可训 |

## 机制总览：四条主线加一套训练

低显存能力来自四条机制：分层加载决定显存上限，块级量化决定磁盘占用与 IO 时间，预取决定 IO 与计算的重叠程度，稀疏 MoE 逐专家加载进一步压掉未参与计算的参数。v4.0 又把同一套流式机制搬进了训练。

```mermaid
flowchart LR
    subgraph 磁盘
        A[原始权重按层切分存盘<br/>可选 4bit/8bit 量化]
    end
    subgraph 显存
        B[当前层权重]
        C["KV cache + 激活"]
    end
    A -- 预取线程<br/>边算边读下一模块 --> B
    B -- 计算后释放 --> C
    D[稀疏 MoE<br/>逐专家流式加载] -.v3.0 起.-> A
    E[LoRA 训练<br/>适配器驻留 GPU] -.v4.0.-> A
```

| 机制 | 换什么 | 主要瓶颈 | 何时生效 |
|------|--------|----------|--------|
| 分层加载 | 用时间换显存 | 磁盘 IO 带宽 | 默认，无法关 |
| 块级量化 | 用磁盘换反量化计算 | GPU 反量化开销 | `compression` 参数开启 |
| 预取 | 用主机内存换延迟 | 后台线程调度 | 默认开，但**与量化互斥** |
| 稀疏 MoE 逐专家加载 | 用路由换显存 | 专家调度开销 | v3.0 起 MoE 模型自动走 |

注意第三行：源码里开启压缩会直接禁用预取（`airllm_base.py` 检测到两者同时启用时打印提示并关掉预取）。量化与预取二选一，这是后文很多取舍的前提。

## 工作原理

### 分层加载：用时间换显存

大模型推理是逐层矩阵乘法，第 N 层的输出是第 N+1 层的输入，任意时刻只有一层的权重真正参与计算。AirLLM 把模型按层切分成 shard 文件存盘，推理时只读当前层进显存，算完立即释放。

实现上（v3.x 重写后）有一点值得知道：真正的 transformers 模型被实例化在 `meta` 设备上——不占任何显存——AirLLM 只给每个大模块（embedding、每个 decoder 层、final norm、lm_head）挂 forward hook，模块运行前把权重从磁盘流到 GPU，运行后立刻释放，同时由一个后台工作线程预取下一模块。因为前向逻辑完全交给 transformers，新架构只要 transformers 支持，AirLLM 就能跑，这也是它模型覆盖面扩张很快的原因。

算一笔账就知道 4GB 为什么够：70B 模型 fp16 全量约 140GB，Llama 3 70B 共 80 层，单层权重约 1.75GB；显存里同时驻留的只有单层权重加上 KV cache 和激活，4GB 装得下。代价是每生成一个 token 都要完整读一遍 80 层，磁盘成为吞吐瓶颈。

这也解释了为什么 7B 模型没必要用它——7B 全量 fp16 只有 14GB，一张 24GB 卡整体装下，标准 `transformers` 推理快一个数量级。分层加载的价值随模型规模放大：模型越大，全量装载越不现实，逐层换入的相对代价才越可接受。

两个默认值容易踩坑：运行精度默认跟随模型自己的 `config.torch_dtype`（现代模型通常是 bfloat16；源码注释明确说 float16 对深层模型数值范围太窄，会溢出成 inf/NaN 静默毁掉输出），`max_seq_len` 默认 512。

### 块级量化：省的是磁盘，未必省时间

分层加载的瓶颈在磁盘一侧，块级量化（block-wise quantization）针对的就是它：把权重从 fp16 压到 4bit 或 8bit 再存盘，磁盘占用直接降到约四分之一或一半（70B 量化后约 35GB，405B 约 200GB）。量化在切分阶段离线完成，方案来自论文 [arXiv:2212.09720](https://arxiv.org/abs/2212.09720)，实现基于 bitsandbytes：4bit 走 NF4 格式（blocksize 64），8bit 走逐块 absmax 加码表（blocksize 2048）。没装 bitsandbytes 时传 `compression` 参数会直接抛 ImportError。

README 把它描述为「最高 3x 提速，精度损失几乎可忽略」。对这句话要保持清醒——2026 年 8 月有一个至今开放的 [issue #330](https://github.com/lyogavin/airllm/issues/330) 给出了反例：在 NVIDIA GB10 上实测 Qwen2.5-32B，无压缩 13.3 秒/token，8bit 反而慢 3.8 倍，4bit 慢 8 倍，而且每个压缩模式的显存峰值都比基线高。原因在源码里看得见：反量化发生在 GPU 上，每个 token、每一层都要把压缩权重展开回 fp16——**速度取决于反量化的工作量，而不是读了多少字节**。当存储足够快（该案例中 18GB 的切分整个躺在 76GB 页缓存里），压缩只剩成本没有收益。

所以对量化的准确定性是：它的确定收益是**磁盘占用**（62GB 切分变 18GB，普通硬盘用户感谢它），速度收益只在磁盘真的是瓶颈时存在。405B 模型必须配合量化，8GB 显卡才有意义跑它——这是磁盘换显存路径的极端案例。

### 预取：把 IO 藏进计算里

朴素实现是串行的：读层 N → 计算 → 释放 → 读层 N+1。预取用一个后台工作线程，在层 N 计算的同时把层 N+1 的权重读进主机锁页内存（pinned memory），计算和 IO 重叠。单层预取缓冲有 2GB 上限，更大的层退回普通分页内存。

README 称预取带来约 10% 提升，并注明目前只有 `AirLLMLlama2` 类支持预取。它有效的前提是计算时间和 IO 时间可比——存储极快时预取纯属多余，计算极快时预取线程来不及读完下一层。再叠加上一节那条规则：开了量化就没有预取。所以「4bit + 预取」不是一个可用配置，而是二选一。

### 稀疏 MoE：逐专家流式加载（v3.0）

MoE 模型每一层并不全量参与计算，而是由路由网络为每个 token 挑出少数几个专家。v3.0 据此把「整层加载」改成「只加载被路由到的专家」，这是 671B 的 DeepSeek-V3 能压到约 12GB 的原因。

最有说服力的案例是 Kimi K3。源码注释写得很直白：K3 每层 896 个专家，每个 token 只路由到其中 16 个；把一层的专家全部展开约 55GB，而单个 token 实际只需要其中约 1GB。按专家粒度流式加载，2.8T 的模型实测只需 3.72GB 显存，单张 RTX 6000 Ada 上端到端跑通。Qwen3.8-Flash-Next 同理，多出的约 51B 参数是 n-gram 嵌入表（PLE），这张表以文件映射方式留在主机内存——64GB 内存的机器就够——解码器层照常流式。

跑 K3 和 Flash-Next 各有一道依赖门槛，写在 README 更新日志里：K3 需要 `compressed-tensors` 和 `flash-attn`（它的模型代码强制 flash attention）、CUDA 12 版 torch（CUDA 13 尚无 flash-attn 预编译包）、`transformers` 4.56.x（remote code 在 5.x 上加载失败）；Flash-Next 需要 Git 版 `transformers`（内置 `qwen4_exp` 架构），并预留约 360GB 的 checkpoint 磁盘。

## 一次推理如何流过系统

以 70B 模型生成 20 个 token、不开压缩（预取生效）为例：

1. **切分阶段**（首次运行一次性成本）：`AutoModel.from_pretrained` 下载原始权重，按层切分成 shard 写入 HF cache。README 特别提醒切分非常耗磁盘，请保证缓存目录空间充足——70B 不开压缩切分后约 140GB，开 4bit 约 35GB。磁盘紧张可以传 `delete_original=True`，切完删掉原始权重，立省一半。
2. **prompt 编码**：tokenizer 把输入文本转成 token ids 放进显存，这一步不涉及权重读取。
3. **第一个 token（prefill）**：模型跑在 meta 设备上，forward hook 在每个模块计算前把它的权重从磁盘拉进显存，后台线程同步预取下一模块；80 层依次推进，最后一层输出经 lm_head 得到第一个 token。
4. **后续 token（decode）**：每个新 token 重走 80 层，KV cache 已存历史 K/V，attention 计算量随序列长度增长。每个 token 都触发一次完整的磁盘读取。
5. **开压缩时的差别**：预取被禁用，加载串行化；每层读进来的是压缩数据，在 GPU 上反量化回 fp16 再计算。

这个流程里有一个反直觉的细节：**生成长序列时，AirLLM 的单 token 延迟会随序列变长而上升**，因为 attention 计算量在涨，而每层的磁盘读取时间基本恒定。vLLM 这类批处理引擎的行为逻辑完全不同，主要受 batch 大小影响。

## 性能特征：数字在测什么

README 只公布显存数字，从不公布速度数字；唯一的官方速度声明是量化「最高 3x」，而上一节已经说明这个声明存在公开反例。可核实的社区实测目前有三组，正好覆盖三种典型配置：

- **NVIDIA GB10 + Qwen2.5-32B**（issue #330，2026-08）：无压缩 13.3 秒/token，4bit 压缩 106.7 秒/token。输出全部正确，纯粹是速度与显存差异。
- **RTX 3050 6GB + 机械硬盘 + Qwen2.5-Coder-32B**（issue #186 评论区）：4bit 压缩下约 2 分钟/token；把模型挪进内存盘后显著改善。磁盘介质在这里就是全部。
- **RTX 3090 12GB + Qwen2.5-7B**（issue #186）：40 分钟生成一句话。这个案例本身是用错了工具——7B 模型在 3090 上根本不需要 AirLLM——但它说明配置不合适时体验可以差到什么程度。

从这些数据能推出的结论：AirLLM 的速度由「磁盘介质 + 模型规模 + 是否量化」共同决定，数量级从秒级到分钟级不等；它适合交互不频繁或完全离线的任务，单次生成几十到几百 token、能等几分钟的场景。**不能**推出的结论同样重要：它不能证明 batch 吞吐（AirLLM 不支持 batch > 1 的高效推理，每层都要为每个样本重复读权重，IO 放大严重），也不能和 vLLM 直接对比——vLLM 测吞吐，AirLLM 只有单请求延迟，两者不在同一坐标轴上。

官方显存表倒是齐全，可以当作选型参考：

| 模型 | 规模 | 显存 |
|------|------|------|
| Qwen3 / Mistral / Phi | 8B | 约 1-2GB |
| Qwen3-30B / Mixtral（MoE） | 30-47B | 约 1-3GB |
| Qwen3.8-27B（密集视觉） | 27B | 3.33GB |
| Qwen3.8-Flash-Next（MoE + PLE） | 约 180B | 5.95GB |
| Qwen3-235B（MoE） | 235B | 约 3GB |
| Llama 3.x 70B（全精度） | 70B | 约 4GB |
| Llama 3.1 405B | 405B | 约 8GB |
| DeepSeek-V3 | 671B | 约 12GB |

## 快速上手

### 安装与推理

```bash
pip install airllm
```

```python
from airllm import AutoModel

MAX_LENGTH = 128
model = AutoModel.from_pretrained("garage-bAInd/Platypus2-70B-instruct")

input_text = ["What is the capital of United States?"]
input_tokens = model.tokenizer(
    input_text,
    return_tensors="pt",
    return_attention_mask=False,
    truncation=True,
    max_length=MAX_LENGTH,
    padding=False,
)

generation_output = model.generate(
    input_tokens["input_ids"].cuda(),
    max_new_tokens=20,
    use_cache=True,
    return_dict_in_generate=True,
)
print(model.tokenizer.decode(generation_output.sequences[0]))
```

`AutoModel` 接受任意 Hugging Face 模型 ID 或本地路径。官方列出的覆盖面：Llama（2/3/3.1/3.3/4）、Qwen（1/2/2.5/3/3.5/3.8，含 MoE、Flash-Next、FP8 与原生视觉）、DeepSeek（V2/V3/R1）、Mistral 与 Mixtral、Phi、Gemma、ChatGLM、Baichuan、InternLM、Yi、Kimi K3。已带量化配置的 checkpoint（如 compressed-tensors 格式）也能识别，加载时通过 hook 在线反压缩。

### 启用块级量化

```python
model = AutoModel.from_pretrained(
    "garage-bAInd/Platypus2-70B-instruct",
    compression="4bit",  # 或 "8bit"
)
```

量化把磁盘占用降到约四分之一或一半，磁盘空间或机械硬盘是主要约束时优先开。注意它会自动关闭预取。405B 模型必须配量化：

```python
model = AutoModel.from_pretrained(
    "meta-llama/Meta-Llama-3.1-405B-Instruct",
    compression="4bit",  # 或 "8bit"
)
```

### 关闭预取与自定义切分路径

预取默认开启；存储极快时它没有收益，可以关掉。切分结果默认存在 HF cache 旁边，`layer_shards_saving_path` 可以另指定位置：

```python
model = AutoModel.from_pretrained(
    "garage-bAInd/Platypus2-70B-instruct",
    prefetching=False,
    layer_shards_saving_path="/data/airllm_shards",
)
```

### 定位瓶颈

```python
model = AutoModel.from_pretrained(
    "...",
    profiling_mode=True,
)
```

`profiling_mode` 打印每层的加载与压缩耗时。各层耗时均匀且贴近磁盘读取速度，瓶颈在 IO，开量化或换更快的盘；某些层明显偏高，瓶颈在计算，考虑缩短序列或换卡。

### macOS / Apple Silicon

仅支持 Apple Silicon，安装后与 Linux 用法一致，另需装 [mlx](https://github.com/ml-explore/mlx) 和 torch：

```bash
pip install airllm mlx torch
```

```python
from airllm import AutoModel
# Meta-Llama-3-70B-Instruct 是 gated 模型，需传 hf_token（见「常见问题」）
m = AutoModel.from_pretrained(
    "meta-llama/Meta-Llama-3-70B-Instruct",
    compression="4bit",
    hf_token="hf_xxx",
)
```

4bit 后 70B 约占 35GB 统一内存，需要 64GB 以上内存的机型。

### LoRA 微调（v4.0）

训练是 2026 年 9 月加入的能力，机制与推理同源：冻结的基础权重逐层从磁盘流过，LoRA 适配器与优化器状态留在 GPU，反向传播所需的中间隐藏状态放在主机内存，backward 时带梯度重算（dropout 固定为 0，保证重算与 forward 一致），交叉熵分块计算。README 特别注明这不是 Hugging Face Trainer 也不是 bitsandbytes QLoRA——PEFT 之类的库要求把基础权重物化到显存，而 AirLLM 的权重根本不在显存里。

目前支持文本模态的 Qwen3.5 / Qwen3.8。数据是每行一个 JSON 对象的 jsonl 文件，`text` 字段做整句下一词预测，`prompt`/`completion` 字段则只对 completion 部分计算损失：

```json
{"text": "你的第一条训练文档。"}
{"prompt": "AirLLM 是什么？", "completion": "一个让大模型跑在小显存上的库。"}
```

命令行入口在仓库的 `air_llm/examples/` 下：

```bash
python air_llm/examples/train_qwen38_flash_next_lora.py \
  --data my_data.jsonl \
  --seq-len 512 \
  --epochs 1 \
  --save-adapter qwen38-flash-next-lora.pt
```

27B 密集模型换用 `train_qwen38_lora.py`。Python API 直接实例化训练器：

```python
from airllm import AirLLMLoRAQwen4Exp

trainer = AirLLMLoRAQwen4Exp(
    "Qwen/Qwen3.8-Flash-Next",
    max_seq_len=512,
    lora_r=16,
    delete_original=True,
)
tok = trainer.tokenizer
if tok.pad_token_id is None:
    tok.pad_token = tok.eos_token

encoded = tok("你的训练文本。", return_tensors="pt", truncation=True, max_length=512)
loss = trainer.train_step(
    encoded["input_ids"].cuda(),
    attention_mask=encoded.get("attention_mask"),
)
print(loss)
trainer.save_adapter("qwen38-flash-next-lora.pt")
```

27B 模型对应的类是 `AirLLMLoRA`。官方给出的显存参考：Flash-Next（125B）在 RTX 3060 Ti 的 6GB 内可训，27B 在序列长度 512 时约 2GB。`--steps N` 可以只跑 N 条样本做冒烟测试；省略 `--data` 时脚本会内置一小段文本做拟合验证。

## 常见问题

### MetadataIncompleteBuffer

```text
safetensors_rust.SafetensorError: Error while deserializing header: MetadataIncompleteBuffer
```

README FAQ 给出的最可能原因是**磁盘空间耗尽**——切分过程极其消耗磁盘，写 shard 写到一半失败就会留下这种损坏文件。扩容磁盘（或清理 HF cache）后重跑 `from_pretrained`。

### ValueError: max() arg is an empty sequence

原因是用手动的 `AirLLMLlama2` 类去加载 QWen 或 ChatGLM 模型。统一改用 `AutoModel` 即可：

```python
from airllm import AutoModel  # 代替 AirLLMLlama2
m = AutoModel.from_pretrained("Qwen/Qwen-7B")
```

### HuggingFace gated 模型鉴权

Llama 系列等 gated 模型需要传入 token：

```python
m = AutoModel.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    hf_token="hf_xxx",
)
```

### Asking to pad but the tokenizer does not have a padding token

部分模型的 tokenizer 没有填充 token，要么设置一个，要么直接关掉 padding：

```python
input_tokens = model.tokenizer(
    input_text,
    return_tensors="pt",
    return_attention_mask=False,
    truncation=True,
    max_length=MAX_LENGTH,
    padding=False,
)
```

### batch 推理 OOM 或极慢

AirLLM 不支持 batch > 1 的高效推理——每层权重要为 batch 中每个样本重复读取，IO 放大严重。需要 batch 走 vLLM / SGLang。

## 采用建议

### 适合谁

- 手里是 4-8GB 显存的卡（RTX 3060/4060、Jetson Orin、Apple Silicon 大内存机型），想跑 70B 到 2.8T 的模型做研究或验证
- 论文复现、离线批处理、边缘 demo——任务对延迟不敏感
- 想保原始精度评估大模型：fp16/bf16 不量化路径在这里是一等公民
- 想在小显存上微调大模型：6GB 训 125B 目前没有更省事的替代品

### 不适合谁

- 需要生产级 QPS 或低延迟：vLLM / TensorRT-LLM
- 已有 24GB+ 显卡：目标模型能整体装下时，标准 `transformers` 推理快一个数量级，逐层换入纯属负担
- 需要 batch 推理：IO 放大会让 batch 收益归零

### 落地顺序

1. **先跑通**：`pip install airllm`，用 Platypus2-70B 或更小的模型确认环境正常
2. **看磁盘**：检查切分后的磁盘占用，空间紧张开 `compression="4bit"` 并配合 `delete_original=True`；机械硬盘用户优先考虑把模型放进内存盘或 SSD
3. **再上大模型**：405B 需 8GB 显存加 4bit 量化；K3 需按前文核对三道依赖门槛
4. **最后试训练**：从 `--steps 5` 的冒烟测试开始，确认数据格式与显存占用后再跑完整 epoch

## 结尾判断

AirLLM 在「低显存跑超大模型」这个细分里走得很前：同样的逐层流式机制，先解决了推理（4GB 跑 70B 直到 3.72GB 跑 2.8T），现在又延伸到训练（6GB 微调 125B）。它的价值从来不在快，而在把「显存装不下」这个硬约束从不可行变成可行——代价是秒级到分钟级的单 token 延迟，以及几乎全部押注在磁盘介质上的性能表现。

判断该不该用它，看三个问题：显存是否真的装不下目标模型？能否接受单 token 秒级以上的等待？任务是否低频或可离线？三个都是「是」，AirLLM 是当前最直接的选择；任何一个是「否」，都有更顺手的方案。

## 读完自检

- 四条机制各用什么换什么：分层加载用时间换显存，块级量化省磁盘但增加 GPU 反量化工作，预取用主机内存换 IO 延迟且与量化互斥，稀疏 MoE 用路由换显存。
- 为什么 Kimi K3 2.8T 只要 3.72GB：每层 896 个专家每个 token 只路由 16 个，展开约 55GB 的单层只需要加载约 1GB。
- 为什么「4bit 最高 3x 提速」不能照单全收：速度取决于反量化工作量而非读取字节数，存储够快时压缩反而更慢（issue #330 实测）。
- v4.0 训练为什么能在 6GB 里跑：基础权重逐层流式、适配器驻留 GPU、隐藏状态放主机内存，显存里始终只有「一层 + 适配器」。

说不清就回到对应章节，再对照「采用建议」核对一遍自己的场景。

---

*仓库：[lyogavin/airllm](https://github.com/lyogavin/airllm) · PyPI：[pypi.org/project/airllm](https://pypi.org/project/airllm/)（最新 4.0.0，2026-09-05）· 许可证：Apache-2.0。显存与版本数据来自官方 README 与 PyPI，速度数据来自公开 issue 实测（#330、#186），数值因硬件配置而异；仓库与社区数据快照日期为 2026-09-07。*
