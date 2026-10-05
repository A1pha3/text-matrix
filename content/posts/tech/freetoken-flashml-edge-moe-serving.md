---
title: "FreeToken：让一台桌面电脑跑动 753B MoE 的那群人"
date: "2026-08-26T00:30:00+08:00"
lastmod: "2026-10-04T00:00:00+08:00"
slug: "freetoken-flashml-edge-moe-serving"
description: "FlashML-org/FreeToken 深度解析：edge-native MoE serving 引擎如何用双层缓冲 prefill、语义锚点状态缓存和 q⋆ 带宽自适应策略，让 35B 跑进 8GB 笔记本、284B 跑上游戏台式机、753B 的 GLM-5.2 跑上单卡工作站，并把 CUDA-graph 兼容的 LRU 专家缓存做成整套机制。"
draft: false
categories: ["技术笔记"]
tags: ["MoE", "边缘推理", "LLM Serving", "vLLM", "SGLang", "FTW"]
github_repo: "FlashML-org/FreeToken"
source_key: "gh:FlashML-org/FreeToken"
---

> 口径说明：本文 2026-08-26 首发于项目创建五周时，2026-10-04 按 GitHub 当次读数、main 分支文档与 arXiv:2608.16157 论文全文逐项复核并更新。项目迭代很快，采用前请以仓库现状为准。

## Berkeley Sky Lab 在做一件什么

Matei Zaharia、Ion Stoica、Song Han、Kurt Keutzer、Chenfeng Xu 出现在同一篇 arXiv 论文的作者栏里，写的是「怎么在你的家用电脑上跑 753B 的 GLM-5.2」。第一作者 Shuo Yang 是 UC Berkeley EECS 博士生、Sky Computing Lab 成员。仓库 [FlashML-org/FreeToken](https://github.com/FlashML-org/FreeToken) 创建于 2026-07-20，发文时（8 月 26 日）约 7,100 star、600 fork，截至 2026-10-04 涨到 14,136 star、1,411 fork、379 个 open issue 加 PR——一个多月翻了一倍。

它不是又一个 vLLM 改 fork 换 logo 的项目。论文 [arXiv:2608.16157](https://arxiv.org/abs/2608.16157)（2026-08-17 提交，11 位作者）的判断是：本地 AI 的瓶颈早就不只是显存够不够，而是怎么把一台桌面机器的算力、内存、总线、网络整体编排成一个推理引擎。FreeToken 把这条路走到底——35B 跑在 8GB 显存的笔记本上、284B 跑在游戏台式机上、753B 跑在单卡工作站上，三种场景用同一份代码。

把同一种设计沿用到 agent 工作负载、并且在 OpenCode、Claude Code、OpenClaw 这些真实工具调用场景下做评测，是这篇论文区别于同档 serving 引擎的地方。它要解决的不是 demo 视频里的好看数字，而是 agentic 时代一个具体到秒级的问题：tool call 之间几十秒的 prefill 不能让用户干等。论文里有一句很硬的注脚——OpenClaw 自带 120 秒空闲 watchdog，Claude Code 默认请求超时约十分钟，**tail TTFT 是可用性边界，不是延迟统计量**。

## 数据先摆出来

下面这张表是论文与 models.md 交叉验证后的事实。六个测试系统、两套模型的完整带宽读数在论文 §5.1 的 Table 1：

| 机器 | GPU | 显存 | PCIe | 跑的模型 | decode 吞吐 | 相对位置 |
|-----|-----|------|------|---------|------------|---------|
| 笔记本 | RTX 4060 Laptop | 8 GB | 4.0 x8 | Qwen3.6-35B-A3B NVFP4 | 39.3 tok/s | 超过生产环境 Codex 中位 decode 速度（33 tok/s） |
| 桌面 5090 主机 | RTX 5090 | 32 GB | 5.0 x16 | Qwen3.6 BF16 / DSV4-Flash MXFP4 | 77-83 / 22-25 | 各 workload 最强基线的 1.8-2.3x / 1.5-1.9x |
| 工作站 | RTX PRO 6000 Blackwell | 96 GB | 5.0 x16 | GLM-5.2 (753B-A40B) NVFP4 | 见论文 §5 | llama.cpp 同场景的 2 倍 |

77-83 与 22-25 是 RTX 5090 上的读数（论文 Figure 3）；3090、4090 与 4060 笔记本也在测试集里，五个消费级系统合起来，FreeToken 把 decode 吞吐提高了 1.3-2.1x。

笔记本能跑 35B 早就是事实——llama.cpp、MLX-LM 都做得到。FreeToken 让人多看两眼的是另外三件事：

1. 284B 的 DeepSeek-V4-Flash 在 32GB 显存里跑出 22-25 tok/s 的交互速度。
2. prefill 吞吐不随 prompt 变长而塌陷：16k token 时仍有 6.7k tok/s（论文 §5.3）。
3. agentic 场景——OpenCode+SWE、Claude Code+SWE、OpenClaw+Email/Cal 三类真实工具调用 workload——下，decode 速率始终保持在单轮基准值的 12% 以内，而最敏感的基线 KTransformers 在第二轮（W2）就掉了 31%。

论文 §5.2 的原话是「Single-stream benchmarks therefore overstate baseline agentic performance」——单流 benchmark 会高估基线的 agentic 表现。FreeToken 的评测直接拿四个 workload 跑：W1 是 AIME 数学题（单轮、无工具），W2 是 OpenCode 修 SWE-bench issue，W3 是同一个 issue 换 Claude Code 走 Anthropic 兼容端点（会话长到 56-65k token，还会起并发 subagent），W4 是 OpenClaw 驱动的邮件日历 agent（十三轮固定对话，约 24.5k token 的系统上下文）。

---

## 它在解一个什么问题

MoE 的稀疏激活是边缘推理的天选架构——论文 §2 的表述是「一个 MoE 层存 E 个专家，但每个 token 只路由到 k ≪ E 个」，DeepSeek-V4-Flash 总参 284B，每个 token 只激活 13B。但「理论上」和「跑得起来」之间隔着三层现实，恰好对应论文 §2 的三个小节：

### prefill 不是稀疏的

decode 阶段每个 token 只走 k 个专家，但 prefill 一次性处理几千个 token，路由的并集几乎覆盖整层专家池。后果由权重体积决定：FP4 部署的 DSV4-Flash 要流过约 140 GB 专家权重，在 PCIe 5.0 x16（约 60 GB/s）上约 2 秒，PCIe 4.0 x16（约 25 GB/s）的桌面机约 5 秒，笔记本常见的 x8 链路 10 秒起步——这些时间全部暴露为 GPU 空转。

FreeToken 的处理是 full-layer double buffering：GPU 算第 l 层的时候，一个独立的 transfer stream 已经把第 l+1 层的专家集从 PCIe 搬过来。两个 buffer 互换角色，连续流过整个模型。论文 §5.3 给的量化结果是：打开双层缓冲后，每个 8,192-token 的 prefill chunk 都在 1.19-1.22 秒完成——正好是把 64.4 GB 专家池按 52.7 GB/s（PCIe 5.0 x16 的实测天花板）流一遍的时间，专家计算完全藏进了传输里。关掉第二个 buffer，4k prompt 吞吐掉 19%，8k 掉 25%，16k 掉 26%，prompt 越长惩罚越重。

### decode 的 cache miss 会让 PCIe 闲置

llama.cpp 在加载时把 MoE 张量分配到设备，KTransformers 把一部分「热」专家钉在 GPU、其余落到 CPU。但 routing 随每个 token 移动——加载或 prefill 时冻结的 placement 只能接住一小部分路由流量，论文 §2.2 的结论是大部分专家计算 fall to CPU，GPU 和 PCIe 同时闲置。

FreeToken 的解是 semantic-aware LRU expert cache——一个在 GPU 上、跟着路由走的共享 LRU 驻留空间。decode 路由有很强的短程时间局部性（论文引了跨模型族的 routing-consistency 测量），缓存内容跟着每一步的选择持续换血。Cache 大小不是模型加载时锁死的常量——这落到工程层就是 `ft ctl cache` 的在线调整，后面讲。

### miss 的去向不能拍脑袋

一个专家 miss 有两条路：从 host RAM 通过 PCIe 传过来；或者在 CPU 上直接算。哪条更快取决于机器上两条路径的实际带宽——而这个数字因机而异。

FreeToken 的策略叫 q⋆ bandwidth-adaptive policy，公式写在论文 §3.2：**q⋆ ≈ m · B_P / B_H**，m 是这一步的 miss 数，B_P 是实测 PCIe 专家传输带宽，B_H 是 CPU 侧 MoE 算子的实测带宽。`ft bench bw` 把两个带宽在真实机器上测出来写成 profile，之后每层每步按当步 miss 数分配：「q⋆ 个走 PCIe，其余走 CPU，overlap」。论文里写得很直接：「the correct division of miss work between the two paths is hardware-specific」。q⋆ 不是常数，是机器的函数。

两个细节值得注意。其一，策略始终保留至少一次 cache fill——即便 CPU 接住了大部分 miss，缓存也在持续变暖。其二，这个公式覆盖所有硬件配比：当 B_H 接近 B_P 时 q⋆ 趋近 m，系统退化成纯按需拉取，不需要单独的策略分支。同一份代码在 RTX 3090（DDR4，B_H 56.7 GB/s）上是一个 q⋆，在 RTX 5090 租用服务器（DDR5，6 线程配额下 B_H 77.3 GB/s）上是另一个，在笔记本 PCIe x8 上又不同。用户的硬件不需要迁就 FreeToken 的假设——FreeToken 来适配用户的硬件。

---

## 三个工程机制的细节

设计层讲完了。下面这几个机制决定了 FreeToken 能不能扛住真实工作负载。

### CUDA-graph 兼容的 LRU 缓存

LRU 在 host 上做需要每步 device-host 同步——decode 阶段每个 MoE 层都要更新 LRU 表，每更新一次就一次隐式同步，在 100 tok/s 这种吞吐量下会被同步开销反噬。

FreeToken 把 LRU 的所有控制路径放进 CUDA graph 内部（论文 §4.1）：每个 MoE 层一个 GPU kernel，去重路由结果、对照 residency 表、计算带宽感知的 fetch 数、选 eviction victim、把 logical expert id 重写成 physical slot id——全部静态捕获成图。CPU 分支也捕获进同一张图：pinned I/O buffer、host 函数提交节点、同步节点一起录进 replay，每步 decode 不需要 host 介入，也不需要 per-token 的 Python 调度。CPU worker 是钉在物理核上的持久 C++ 线程池，用架构专属 SIMD 加 in-kernel 反量化吃专家权重。

victim 选择避免了一个经典坑：传统 LRU eviction 要扫全 cache 找最旧元素。FreeToken 写了一个 single-pass kernel，一次找出 K 个 least-recently-used 候选，miss path 取前 q ≤ K 个用。不论 miss 多少，victim discovery 永远恰好一次扫描。

### Semantic anchors：让 agent 的 tool call 不重算

这是论文里最容易被略过、但对 agent 用户最值钱的一段。

很多前沿模型采用 hybrid-attention：full attention 层与 sliding-window attention 层（如 DSV4-Flash、GPT-OSS）或 recurrent 层（如 Qwen3.6 里的 gated DeltaNet、Kimi-K3 里的 Kimi Delta Attention）交错。这些层把历史压缩成单一 state 或最近一段 KV 窗口，而每个 state 的内存相当于几百 token 的 KV cache——所以 serving 引擎只能保留很少的 checkpoint。agentic 负载几乎每轮都改上下文：tool call 会删旧输出、砍 thinking 段，checkpoint 一旦落在被改的位置就全部作废，引擎只能回退到上一个有效点整段重算。

FreeToken 的做法是在 special token 边界——thinking 段、tool call 与 tool 输出、对话轮次的分界——设 semantic anchor checkpoint，把那个时刻的 KV cache 加 recurrent state 一起存住。这些位置不是随便挑的：agent 框架的上下文编辑恰好都以 special token 块为单位——OpenClaw 把每轮 assistant 消息里除最新一条外的 thinking 块剥掉，OpenCode 把窗口外的 tool 输出换成固定占位符，SWE-agent 只保留最后 n 条观察。编辑删的是整块，块边界上的 anchor 天然幸存。上下文一改，引擎从最近的幸存 anchor 恢复：full attention 层复用编辑点之前的 KV，recurrent 层从 anchor 的 state 续起，只有真正新增的后缀被重新 prefill。Anchor 槽位本身用 LRU 回收，独立于 KV 池。

一个 Claude Code session 里用户问一个问题、agent 调 tool、tool 返回、agent 再调下一个 tool——传统引擎每个 tool call 都重新 prefill 整段对话历史，TTFT 随轮数累积。FreeToken 只 prefill 新增的 tool 结果。论文 §5.2 的读数是：六个多轮测试格子（两模型 × 三个 agentic workload）里 FreeToken 拿到五个最低 mean TTFT，唯一例外是 Qwen3.6 的 W3——KTransformers 的 GPU-prefill 分支更快；W1 的短单轮 prompt 则是 llama.cpp 占优。tail 差距更狠：FreeToken 最差的一轮不到 44 秒，三个基线都在某个设置下越过 150 秒——llama.cpp 232 秒、Ollama 179 秒、KTransformers 946 秒，全部越过真实客户端的放弃阈值。

### FTW 格式：消除启动时的发现与重排

引擎启动时要把整个专家池从磁盘读进 host 内存。对 FP4 的 DSV4-Flash，只算从 7 GB/s NVMe 读约 140 GB 就要 20 秒，还没算 warmup；边缘用户又偏偏是「用的时候才开、关掉腾机器、换模型重启引擎」的使用模式。

FreeToken 提供 FTW（FreeToken Weight）格式：把权重提前合并进 runtime bank 布局——每个 bank 用展平的「层-专家」标识 lE+e 做 leading dimension，GPU kernel 和 CPU executor 共享同一个逻辑专家身份。引擎启动时跳过 tensor 发现和 repack，用并行 direct I/O 把对齐块直读进定长的 host bank，填满后才 pin 住。`ft checkpoint` 是转换命令，可选——直接加载 HF safetensors 也能跑，FTW 省掉的是发现与重排两步。

这个格式已经踩过一次坑：量化重构之前的旧版 FTW 会在新版上加载失败（GLM-5.2-NVFP4 旧文件里的 runtime-fp8 权重需要反量化回 bf16，Qwen3.8-Flash-Next 旧文件缺 47.7 GiB 的 PLE n-gram 表）。仓库为此专门提供了 `scripts/ftw_hotfix.py` 修复工具，按字节区间只下载缺的 tensor，不重转全量。

---

## 一次 Claude Code 会话怎么流过 FreeToken

把上面的机制串起来。假设你在一台 RTX 5090 台式机上：

```bash
uv pip install "freetoken[accel]"
ft bench bw        # 一次性：测 B_P/B_H，写进 ~/.cache/freetoken/benchbw/<gpu-uuid>.json
ft launch claude   # 发现本机已 serve 的模型，配好 provider，启动 Claude Code
```

`ft launch` 先查 `/v1/models` 确认服务端在跑什么，然后把对应 agent 的 provider 配置写好（缺 CLI 就先装），再启动。对 Claude Code，它注入的是一组环境变量：`ANTHROPIC_BASE_URL` 指向本地服务、`ANTHROPIC_AUTH_TOKEN` 置为 freetoken、模型族映射全部指向本地模型，同时把 `ANTHROPIC_API_KEY` 置空——防止 agent 静默回退到付费云端。写配置文件的是另外几家：codex 写 `~/.codex/config.toml`，OpenClaw、Hermes 各有落点。

之后你问一个问题，agent 调 tool：prefill 阶段双层缓冲把专家流进 GPU，1.19 秒一个 chunk；tool 触发上下文编辑时，从最近的 semantic anchor 恢复，只重算新增后缀；decode 阶段命中 LRU 的专家直接进 GPU，miss 按 q⋆ 分给 PCIe 拉取和 CPU 现算，两路输出按 gate 精确合并。整个过程 host 不参与逐步调度——全在图里。

---

## 支持面与 CLI

FreeToken 直接加载 HF safetensors，官方验证过的模型清单（docs/models.md，2026-10-04 读数）已经扩到 14 个模型族、20 多个 checkpoint：

- DeepSeek-V4-Flash-0731（专家原生 MXFP4）
- GLM-5.2 / GLM-4.7 / GLM-5.3-Flash（NVIDIA/RedHatAI NVFP4）
- Qwen3.8-Flash-Next（FP8/NVFP4，注意它会钉一张 47.7 GiB 的 PLE n-gram 表在内存里）、Qwen3.6 / Qwen3.5 MoE、Qwen3.8 / Qwen3.6 dense
- Qwen3-MoE、Qwen3-VL（8B / 30B-A3B，图像输入）
- gpt-oss-120b / 20b、Gemma-4（含 NVFP4 版）、MiniMax-M2.5 / M3、Muse-Glimmer-30B

图像输入是实验特性：Qwen3-VL、Gemma-4、GLM-5.3-Flash 这些族带视觉编码器，OpenAI、Anthropic、Responses 三种协议都能收图，编码器权重默认流式驻留在 host 侧（一次两个 block 跟在计算后面）。工具结果里的图（比如 Claude Code Read 的截图）会被挪到后续 user turn——chat template 把 tool message 渲染成纯文本，这一点和 vLLM 一致。

CLI 入口是 `ft`。docs/cli.md 列了六个子命令——`serve` / `shell` / `ctl` / `launch` / `checkpoint` / `bench`——源码里其实还有第七个 `daemon`（持久引擎 supervisor），文档尚未收录。`ft serve --model <path-or-hf-id>` 起本地 API server，默认 `127.0.0.1:1919`，同时暴露 OpenAI 兼容（`/v1/chat/completions`、`/v1/responses`、`/v1/models`）和 Anthropic 兼容（`/v1/messages`、`/v1/messages/count_tokens`）两套端点。MoE 策略五档：`fused`（专家常驻）、`offload`（LRU 缓存 + PCIe 拉取）、`cpu`（miss 现算）、`hybrid`（两者 overlap）、`auto`（dense 归 fused；MoE 归 offload，有 bench profile 推荐时升 hybrid）。

量化格式支持 NVFP4 / MXFP4 / FP8 / BF16。NVFP4 的原生 kernel 路线需要 Blackwell（RTX 50 系）；RTX 30/40 上有 Marlin W4A16 备选路径（sm_80-99），但它借 vLLM 的 AOT wheel，与主依赖的 transformers 5.x 冲突，pyproject 里明确不进默认解析——需要的话在独立环境单独装。

---

## 它和 vLLM / SGLang / llama.cpp 的关系

README 致谢里写得很清楚：FreeToken 的设计「deeply inspired by mini-sglang」，并「learned and reused code」自 SGLang、vLLM、FlashInfer、flash-linear-attention、LightLLM、llama.cpp。代码层面不是从零写。

它跟这几类引擎的分工：

- **vLLM / SGLang**：data center serving 的主线是 GPU 装得下整个模型，paged KV + continuous batching 往极致做。GLM-5.2 的 753B 参数即便 NVFP4 也远超 96 GB 显存，weight-resident 的主线设计天然覆盖不到这个场景。
- **llama.cpp**：edge 上 MoE offloading 的早期实现。placement 在加载时固定，cache miss 的处理也朴素。评测里它在 W1 短单轮 prompt 上 mean TTFT 占优，但最差一轮 232 秒。
- **KTransformers / MoE-Infinity**：更晚的 hybrid 引擎。KTransformers 走「热专家钉 GPU + CPU 兜底」，静态 placement 的毛病它有；MoE-Infinity 走「request-level activation 预测」，但评测中只能跑 W1（8.8 tok/s）——它的 per-expert prefill staging 上限会中断更长的 prompt workload，自带的 server 也不跨请求保留 KV。

论文 §6 对自己定位的一句话是：这些系统的差别在预测 miss 的准确度，不在服务 miss 的方式——**每个 miss 最终都是一次 PCIe 传输**，预测再准，decode 延迟仍被链路卡死，host 算力闲着。FreeToken 保持路由计算精确、模型不做任何修改，改的是残余 miss 的服务方式，而不是预测方式。

---

## 怎么跑起来

依赖条件（docs/install.md）：

- Linux x86_64、NVIDIA GPU、driver r580+（CUDA 13）；AMD ROCm 指南在写（WIP），pyproject classifiers 已加 ROCm 条目
- Python ≥ 3.10，推荐 [uv](https://docs.astral.sh/uv/)（pip + venv 也行）

最简安装 + 启动（PyPI 路线）：

```bash
uv venv && source .venv/bin/activate
uv pip install "freetoken[accel]"
ft serve --model ~/models/Qwen3.6-35B-A3B
```

首次启动需要 CUDA 13 toolkit 的 `nvcc` 在 PATH 里——CUDA kernel 是 JIT 编译的。`[accel]` 这个 extra 装的是 FlashInfer（0.6.18.post1）和 sglang-kernel（0.4.5）——没有它们会回落到纯 Triton kernel，能跑但慢。不想本地编译可以走 nightly wheel：每晚 main 构建一对 wheel（runtime + 预编译 kernel cache），文件名带 `+g<sha>` 戳，官方明确说 pin URL 别 pin tag。

另有 Windows/Linux 桌面客户端在 [flashml.ai](https://www.flashml.ai/) 提供 GUI（跑模型、聊天、调引擎参数）。

测一下带宽，让 FreeToken 决定 q⋆：

```bash
ft bench bw
```

这条命令每个 GPU 跑一次就够。它用真实的 cpu/offload MoE kernel 测 host 内存与 PCIe 带宽，profile 写到 `~/.cache/freetoken/benchbw/<gpu-uuid>.json`，按专家格式 + GPU 键值隔离——换了卡或换了量化格式会自动忽略旧 profile。`ft serve --moe-strategy auto` 和 `--moe-hybrid-max-fetch -1` 会读它。`--threshold`（默认 2.0）定义推荐阈值：CPU 带宽超过 PCIe 的 2 倍才建议 hybrid。论文 §5.1 的实测可以当参照系：笔记本 14 核 LPDDR5 47.5 GB/s、台式机 16 核 DDR5 53.8 GB/s、租用的 RTX 5090 服务器 6 线程配额 77.3 GB/s。

---

## 几个值得停下来想的设计选择

### `ft serve` 默认 127.0.0.1

`--host` 默认绑回环地址。2026 年的开源工具越来越多倾向「开箱 0.0.0.0 方便远程」，FreeToken 反着走：默认拒绝任何非本地访问。结合两套兼容端点，本地模型当 cloud API 的 drop-in replacement 时不会意外暴露——这件事在多人共用的开发机上比想象的重要。

### `--max-running-requests` 默认 4

OpenClaw、Claude Code、OpenCode 这些 agent 工作流，单个会话一次只发 1-2 个并发请求——4 是「够用且不浪费 batch 优化红利」的选择，和数据中心引擎按高并发调参的思路是两个方向。配合 `--memory-ratio`（默认 0.9，权重+专家缓存+KV 共占空闲显存的比例）和 `--kv-reserve-tokens`（默认 8192，专家缓存自动扩容前给 KV 留的底线），单卡上的显存分配逻辑是完整自洽的。

### 缓存池可以在线改

这就是论文 §3.3 的 Elastic Memory Management 落到 CLI 的样子：专家缓存和 KV 池之间的显存划分配额不用重启引擎就能改——`ft ctl cache --moe 512k`、`--kv 120k`、`--swa 60k`，带 `--wait 300` 等重建完成。跑长 agent 会话时 KV 吃紧、闲时想把显存还给专家缓存，都不用动 `ft serve`。GET `/v1/stats` 会报当前各池占用。

### 8 GB VRAM 跑 35B 的真实含义

8 GB 跑 35B 听起来像营销话术，但这次有完整读数：RTX 4060 Laptop + NVFP4 Qwen3.6-35B-A3B 跑出 39.3 tok/s，超过 Codex 生产 trace 的中位 decode 速度（33 tok/s）。NVFP4 + x8 链路 + LPDDR5 的组合，让「带显卡的笔记本就是 inference machine」从口号变成可复核的工程事实——laptop 那一列的每个数字论文都给了测量条件。

---

## 它还差什么

公平起见，看清边界：

- **桌面客户端是新产品线**：Windows/Linux GUI 上架 flashml.ai，但源码仓库的 classifiers 与安装文档仍以 Linux x86_64 + CUDA 为第一目标，桌面端与 CLI 的功能对齐程度需要自行验证。
- **Mac 不在支持范围**：pyproject classifiers 写得很明确——`POSIX :: Linux` 加两张 NVIDIA/AMD GPU 条目，没有 macOS。Apple Silicon 用户继续用 MLX-LM / llama.cpp。
- **单 GPU 是主线**：评测机器全是单卡，论文口径就是「8GB 笔记本 GPU 到单张工作站 GPU」。多卡机器上可以用 `--gpu` 按 UUID 选卡，多卡并行服务不在当前设计里。
- **量化受硬件路线制约**：NVFP4 原生 kernel 要 Blackwell；老卡走 Marlin 路径得单独配环境。这不是 FreeToken 的锅，是 NVIDIA 硬件路线的现实。
- **379 个 open issue + PR**：从一个多月前的 149 涨到 379，讨论热度在涨，响应压力也在涨。issue 区是判断「你要的硬件组合有没有人踩过坑」的第一站。

---

## 谁该现在就上

- **有 16GB+ 显存 NVIDIA 卡、日常跑 coding agent 的开发者**：这是收益最直接的群体。装好、`ft bench bw` 一次、`ft launch` 接入现有 agent，改动只有 base URL；284B 档的本地交互体验目前没有同档对手。
- **想给 agent 配多模态后端的**：Qwen3-VL、Gemma-4 的图像输入已经能走三协议，但标着 experimental，先在非关键链路上试。
- **Apple Silicon 用户、需要多卡并行的团队**：等。前者不在支持范围，后者不在设计主线。
- **把「本地跑 frontier MoE」当生产承诺的**：再等一个版本周期。GitHub release 只有 v0.1.2、v0.1.3 两个正式版（2026-08-19 / 09-16）加一条 nightly 滚动线，量化重构刚弄出过一轮 FTW 不兼容——pin 版本、读 changelog 再升级。

---

## 资料来源

- FreeToken GitHub: <https://github.com/FlashML-org/FreeToken>。首访 2026-08-26，复核 2026-10-04（stars/forks/issues 为当日 API 读数）。
- Yang et al., "FreeToken: Efficient Edge-Native MoE Serving with Bandwidth-Adaptive Execution", arXiv:2608.16157, 2026. <https://arxiv.org/abs/2608.16157>。性能数字均出自该论文 §5 并注明小节。
- FreeToken supported models: <https://github.com/FlashML-org/FreeToken/blob/main/docs/models.md>。
- FreeToken CLI reference: <https://github.com/FlashML-org/FreeToken/blob/main/docs/cli.md>。
- FreeToken quick start: <https://github.com/FlashML-org/FreeToken/blob/main/docs/quickstart.md>。
- FreeToken install: <https://github.com/FlashML-org/FreeToken/blob/main/docs/install.md>。
- FTW 修复工具: <https://github.com/FlashML-org/FreeToken/blob/main/docs/ftw-hotfix.md>。
