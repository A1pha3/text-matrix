---
title: "FreeToken：把 753B MoE 模型塞进家用 GPU 的那群人"
date: "2026-08-26T00:30:00+08:00"
slug: "freetoken-flashml-edge-moe-serving"
description: "FlashML-org/FreeToken 深度解析：edge-native MoE serving 引擎如何在 RTX 5090 跑 284B 模型、工作站 GPU 跑 753B 的 GLM-5.2，以及支撑这一切的 q* 带宽自适应策略和 CUDA-graph 兼容的 LRU 专家缓存。"
draft: true
categories: ["技术笔记"]
tags: ["MoE", "边缘推理", "LLM Serving", "vLLM", "SGLang", "FTW"]
github_repo: "FlashML-org/FreeToken"
source_key: "gh:FlashML-org/FreeToken"
---

## Berkeley Sky Lab 在做一件什么

Matei Zaharia、Ion Stoica、Song Han、Kurt Keutzer、Chenfeng Xu 出现在同一篇 arXiv 论文的作者栏里，写的是「怎么在你的家用 RTX 5090 上跑 753B 的 GLM-5.2」。仓库 [FlashML-org/FreeToken](https://github.com/FlashML-org/FreeToken) 在 35 天内拿到 7111 个 star、612 个 fork，149 个 open issues 在持续讨论「我的 3090 能不能跑 Qwen3.6-35B-A3B」。

它不是又一个 vLLM 改 fork 换 logo 的项目。论文 [arXiv:2608.16157](https://arxiv.org/abs/2608.16157) 的判断是：本地 AI 的瓶颈早就不只是显存够不够，而是怎么把一台游戏电脑的算力、内存、总线、网络整体编排成一个推理引擎。FreeToken 把这条路走到底——35B 跑在笔记本、284B 跑在游戏台式机、753B 跑在单卡工作站，三种场景用同一份代码。

把同一种设计沿用到 agent 工作负载、并且在 OpenCode / Claude Code / OpenClaw 这些真实工具调用场景下做评测，是这篇论文区别于同档 serving 引擎的地方。它要解决的不是 demo 视频里的好看数字，而是 agentic 时代一个具体到毫秒级的问题：tool call 之间几十秒的 prefill 不能让用户干等。

## 数据先摆出来

下面这张表是论文 + README + models.md 三处交叉验证的事实：

| 机器 | GPU | VRAM | PCIe | 跑的模型 | decode tok/s | vs 最强基线 |
|-----|-----|------|------|---------|------------|------------|
| 笔记本 | RTX 4060 laptop | 8 GB | x8 | Qwen3.6-35B-A3B NVFP4 | 可用 | 论文 §5.3 Figure 5 无具体数字 |
| 游戏台式机 | RTX 3090 / 4090 / 5090 | 24-32 GB | x16 (PCIe 4/5) | Qwen3.6 BF16 / DSV4-Flash MXFP4 | 22-83 | 1.5-2.3× |
| 工作站 | RTX PRO 6000 Blackwell | 96 GB | x16 | GLM-5.2 (753B-A40B) NVFP4 | 见 §5 | 单卡唯一方案 |

笔记本能跑 35B 早就是事实——llama.cpp、MLX-LM 都做得到。FreeToken 让人多看两眼的是另外三件事：

1. 284B 在单卡 32GB VRAM 上能跑出 22-25 tok/s，prefill 还能稳住。
2. prefill TTFT 在长 prompt 下不会塌陷。
3. agentic 场景——OpenCode、Claude Code、OpenClaw 真实工具调用 trace——下，吞吐不像基线那样因为多轮累积 KV 而掉 30%+。

第三件事最关键。论文 §5.2 给出的判断是「Single-stream benchmarks overstate baseline agentic performance」——单流 benchmark 会高估基线的 agentic 表现。FreeToken 的 evaluation 直接拿四个真实 agent workload 跑，包括 Claude Code + SWE 和 OpenClaw + Email/Cal 这种工程化场景。

---

## 它在解一个什么问题

MoE 模型的稀疏激活是边缘推理的天选架构——一个 284B 的 DeepSeek-V4-Flash，每个 token 实际只激活几十个专家（top-k 很小），理论上 8GB VRAM 的笔记本就能跑。但「理论上」和「跑得起来」之间隔着三层现实，恰好对应论文 §3 的三个核心机制：

### prefill 不是稀疏的

decode 阶段每个 token 只走 top-k 个专家，但 prefill 阶段一次性处理几千个 token，路由到的专家几乎覆盖整个专家池。一篇 2 万 token 的请求，光搬权重就要 5-10 秒（PCIe 4.0 x16 约 25 GB/s 流 140 GB），然后才能开始计算。

FreeToken 的处理是 full-layer double buffering：GPU 算第 l 层的时候，一个独立的 transfer stream 已经把第 l+1 层的专家集从 PCIe 搬过来。两个 buffer 互换角色，连续流过整个模型。论文 §5.3 给的量化结果是打开 double buffer 后，每个 8192-token 的 prefill chunk 都在 1.19-1.22 秒，跟 PCIe 5.0 x16 链路传输 64.4 GB 专家池的理论下限一致。关掉第二个 buffer，4k prompt 吞吐掉 19%，16k prompt 掉 26%。

### decode 的 cache miss 会让 PCIe 闲置

llama.cpp 和 KTransformers 的策略是「load time 把热专家钉在 GPU」。但 routing 随 token 移动——一段 prompt 触发的专家分布和下一段完全不同，prefill 时钉住的「热集」到 decode 时可能完全冷下来。论文 §2.2 给的数字是固定 placement 下 routed traffic 大部分 fall to CPU，GPU 和 PCIe 同时闲置。

FreeToken 的解是 semantic-aware LRU expert cache——一个在 GPU 上、跟着 routing 走的专家缓存。每次 router 触发，cache 自动更新 LRU 顺序，热门专家停留，冷门让位。Cache 大小不是模型加载时锁死的常量，是 runtime 可调的弹性资源。

但 LRU 也只解决一部分。cold start、工作集突移、cache 容量受限都会产生 miss。剩下这批 miss 怎么办？

### miss 的去向不能拍脑袋

一个专家 miss 有两条路：从 host RAM 通过 PCIe 传过来；或者在 CPU 上直接算。哪条更快取决于机器上两条路径的实际带宽——而这个数字因机而异。

FreeToken 的策略叫 q\* bandwidth-adaptive policy。`ft bench bw` 把机器的 PCIe 带宽（B_P）和 CPU 端 MoE 算子带宽（B_H）测出来，每次 decode step 决策：「这一批 miss 的 q\* 个走 PCIe，其余走 CPU，overlap」。论文里写得很直接：「the correct division of miss work between the two paths is hardware-specific」。q\* 不是常数，是机器的函数。

这件事的工程含义是用户的硬件不需要遵守 FreeToken 的假设——FreeToken 来适配用户的硬件。同一份代码在 RTX 3090 DDR4 平台上是某个 q\*，在 RTX 5090 DDR5 平台上是另一个 q\*，在笔记本 PCIe x8 上又不同。

---

## 三个工程机制的细节

设计层讲完了。下面这三个机制决定了 FreeToken 能不能扛住真实工作负载。

### CUDA-graph 兼容的 LRU 缓存

LRU 在 host 上做需要每步 device-host 同步——decode 阶段每个 MoE 层都要更新 LRU 表，每更新一次就一次隐式同步，在 100 tok/s 这种吞吐量下会被同步开销反噬。

FreeToken 把 LRU 的所有控制路径放进 CUDA graph 内部：每个 MoE 层一个 GPU kernel，去重路由结果、对照 residency 表、计算带宽感知 fetch count、选 eviction victim、把 logical expert id 重写成 physical slot id——全部静态捕获成图。每次 decode step 不需要 host 介入。

victim 选择避免了一个经典坑：传统 LRU eviction 需要扫整个 cache 找最旧元素。FreeToken 写了一个 single-pass kernel，一次找出 K 个 least-recently-used 候选，miss path 取前 q ≤ K 个用。不论 miss 多少，victim discovery 永远是一次扫描。

### Semantic anchors：让 agent 的 tool call 不重算

这是论文里我觉得最被低估的一段。

现代 MoE 模型多采用 hybrid-attention——full attention 层和 sliding-window attention 层交错。sliding-window 层的 recurrent state 本质上是有状态的循环结构。tool call 触发 context edit 后，传统引擎会整段重 prefill，把已经算过的 recurrent state 全部丢掉。

FreeToken 在 special token（tool call、thinking block）边界设置 semantic anchor checkpoint，把那个时刻的完整 KV cache + recurrent state 持久化。下一次 context edit 后，引擎从最近的 anchor 恢复，只重 prefill 新增的后缀。

一个 Claude Code session 里用户问一个问题、agent 调用 tool、tool 返回结果、agent 再调用下一个 tool——传统引擎每个 tool call 都重新 prefill 整段对话历史，TTFT 累积增长。FreeToken 只 prefill 新增的 tool 结果，TTFT 跟上下文长度解耦。论文 §5.2 给的具体数字是 FreeToken 的 mean TTFT 在每个 agent workload 上都接近 prompt 长度对应的 baseline，而不是历史长度的线性函数。

### FTW 格式：消除加载时的发现成本

引擎启动时要把几十 GB 专家权重从磁盘读到 host memory，再决定怎么搬到 GPU。传统流程：先发现 tensor 拓扑（每个模型不一样），再 repack 到 runtime layout，再加载。这三步加起来，对 FP4 的 DeepSeek-V4-Flash 大约 20 秒（7 GB/s NVMe × 140 GB）。

FreeToken 提供 FTW（FreeToken Weight）格式——把权重提前转成 runtime bank 布局（leading dimension 是 flattened `l × E + e`），存成定长对齐块。引擎启动时直接 `O_DIRECT` 读盘到固定大小的 host bank，跳过发现和 repack。

`ft checkpoint` 是这个转换的命令。它是可选的——直接加载 HF safetensors 也能跑——但加载速度的差距是「几十秒 vs 几秒」。

---

## supported models 与 CLI

FreeToken 现在支持的 frontier MoE 模型（README + docs/models.md 验证）：

- DeepSeek-V4-Flash-0731 (deepseek-ai)
- GLM-5.2 / GLM-4.7 (nvidia/NVFP4)
- Qwen3.6 / Qwen3.5 MoE (Qwen + nvidia NVFP4)
- Qwen3.6 dense (Qwen + nvidia NVFP4)
- Qwen3-MoE (Qwen)
- gpt-oss-120b / gpt-oss-20b (openai)
- Gemma-4 (google + nvidia NVFP4)
- MiniMax-M2.5 (nvidia NVFP4)
- Muse-Glimmer-30B (meta-models + RedHatAI NVFP4)

CLI 入口是 `ft`，子命令六个：`serve` / `shell` / `ctl` / `launch` / `checkpoint` / `bench bw`。`ft serve --model <path-or-hf-id>` 起一个本地 API server（默认 `127.0.0.1:1919`），同时暴露 OpenAI 兼容 (`/v1/chat/completions`、`/v1/responses`、`/v1/models`) 和 Anthropic 兼容 (`/v1/messages`、`/v1/messages/count_tokens`) 的端点。

`ft launch claude` / `codex` / `dsh` / `hermes` / `openclaw` / `opencode` 把对应 coding agent 的 provider config 写好并启动。`ft launch openclaw` 把 OpenClaw 的 provider 指向 `127.0.0.1:1919`，你的本地 FreeToken 立刻变成 OpenClaw 的 MoE 后端。

quantization format 支持 NVFP4 / MXFP4 / FP8 / BF16。NVFP4 是 NVIDIA Blackwell（RTX 50 系）的首选；老硬件（RTX 30/40）也能跑但建议 BF16 或 FP8。

---

## 它和 vLLM / SGLang / llama.cpp 的关系

README 致谢里写得很清楚：FreeToken 的设计「deeply inspired by mini-sglang」，并「learned and reused code」自 SGLang、vLLM、FlashInfer、flash-linear-attention、LightLLM、llama.cpp。代码层面不是从零写。

它跟这三类引擎的分工：

- **vLLM / SGLang**：data center serving。假设 GPU 足够装下整个模型，paged KV + continuous batching 极致优化。它们在 FreeToken 想跑的硬件上根本起不来——GLM-5.2 753B 装不进 96 GB VRAM。
- **llama.cpp**：edge 上的 MoE offloading 早期实现。它能跑，但 §5 里给出的数字是 FreeToken 在 decode 上 1.8-2.3×、TTFT tail 低数倍。llama.cpp 的 expert placement 是 load-time 固定的，cache miss 处理也比较朴素。
- **KTransformers / MoE-Infinity**：更晚的 hybrid 引擎。KTransformers 走「hot set pin 在 GPU + CPU 兜底」，MoE-Infinity 走「request-level activation 预测」。前者静态 placement 的毛病它有，后者只能在第一轮生效（多轮 agent 累积不在它模型里）。论文 §5 给的数字是 W2 之后两者吞吐掉 30%+，FreeToken 只掉 12%。

FreeToken 的差异化点是「hybrid offload + agentic state reuse + runtime-adjustable cache」三件套。一个 RTX 5090 用户跑 OpenClaw agent 做开发工作，FreeToken 比 llama.cpp / KTransformers / MoE-Infinity 都更接近 Claude Code 云的体验——这正是 FreeToken 把评测场景放在真实 agent workload 上的原因。

---

## 怎么跑起来

依赖条件（docs/install.md 验证）：

- Linux x86_64、CUDA 13、driver r580+
- Python ≥ 3.10，推荐 [uv](https://docs.astral.sh/uv/)

最简安装 + 启动：

```bash
uv venv && source .venv/bin/activate
uv pip install "freetoken[accel]"
ft serve --model ~/models/Qwen3.6-35B-A3B
```

首次启动需要 NVCC + CUDA 13 toolkit on PATH，CUDA kernel 是 JIT 编译。`[accel]` 这个 extra 装的是 FlashInfer 和 sglang-kernel——裸 Triton kernel 也能跑，但慢。

测一下带宽，让 FreeToken 决定 q\*：

```bash
ft bench bw
```

这条命令只跑一次。FreeToken 把 PCIe 带宽和 CPU 端 MoE 算子带宽都测了，写到本地 profile，下次 serve 时自动用。论文 §5.1 给的数字：笔记本 14 核 DDR5 47.5 GB/s、台式机 16 核 DDR5 53.8 GB/s、RTX 5090 服务器 6 线程 77.3 GB/s。`ft bench bw` 是「我的机器跑什么 MoE backend」这个问题的官方答案。

---

## 几个停下来想过的点

### `ft serve` 默认 127.0.0.1

`--host` 默认绑回环地址。2026 年的开源工具越来越多倾向「开箱 0.0.0.0，方便远程」，FreeToken 反着走：默认拒绝任何非本地访问。结合 Anthropic API 兼容 + OpenAI API 兼容两个端点，本地模型作为 cloud API 的 drop-in replacement 时不会意外暴露——这件事在 multi-tenant 开发环境里比想象的重要。

### `--max-running-requests` 默认 4

`ft serve --max-running-requests 4` 是默认并发数。OpenClaw + Claude Code + OpenCode 这些 agent 工作流，一次只会发起 1-2 个并发请求——4 是「够用且不浪费 batch 优化红利」的选择。vLLM 默认 256 是 data center serving 假设；FreeToken 默认 4 是 edge serving 假设。

### `ft launch` 不只是 wrapper

`ft launch claude` 写 Claude Code 的 `~/.claude/settings.json` 加上 OpenAI-compatible provider，指向 `127.0.0.1:1919`。这个工作流看起来 trivial，但它是把「本地 MoE」从「技术演示」带到「个人工作流」的关键一步。一个 developer 不需要切换任何习惯，本地 FreeToken 就是 Claude Code 的 backend。

### 8 GB VRAM 跑 35B 的真实含义

8 GB VRAM 跑 35B MoE 听起来像营销话术。论文 §5.3 给的实测是 RTX 4060 laptop + NVFP4 Qwen3.6-35B-A3B 的 decode 吞吐稳定、TTFT 可接受。NVFP4 + 笔记本 PCIe x8 + DDR5 14 核的组合，让「带显卡的笔记本就是 inference machine」从口号变成可重复的工程事实。FreeToken 不是这个事实的唯一原因，但它把这件事工程化到了 production-grade。

---

## 它还差什么

公平起见，看清边界：

- **Windows 桌面 GUI 在 README 里被推**：「Download FreeToken for Windows or Linux at flashml.ai」。GitHub 上没看到 Windows 构建脚本；Linux 是第一公民。
- **Mac 不在支持范围**：pyproject.toml classifiers 写得很明确：`Operating System :: POSIX :: Linux`、`Environment :: GPU :: NVIDIA CUDA`。Apple Silicon 用户得继续用 MLX-LM / llama.cpp。
- **多 GPU 不在主线**：测评机器全是单 GPU。FreeToken 的设计是为单 GPU + heterogeneous host resources 优化的，多卡扩展是后续工作。
- **Quantization 受硬件限制**：NVFP4 需要 Blackwell（RTX 50 系）；老 GPU 只能 BF16/FP8，模型大小会膨胀。这不是 FreeToken 的问题，是 NVIDIA 硬件路线的问题。
- **149 个 open issues**：35 天、7111 stars、149 open issues——对一个 35 天的新项目这是正常的早期信号，但 issue 堆积意味着 FreeToken 的「production-grade」还差最后一公里。

---

## 资料来源

- FreeToken GitHub: <https://github.com/FlashML-org/FreeToken>。访问时间：2026-08-26。
- Yang et al., "FreeToken: Efficient Edge-Native MoE Serving with Bandwidth-Adaptive Execution", arXiv:2608.16157, 2026. <https://arxiv.org/abs/2608.16157>。
- FreeToken supported models: <https://github.com/FlashML-org/FreeToken/blob/main/docs/models.md>。
- FreeToken CLI reference: <https://github.com/FlashML-org/FreeToken/blob/main/docs/cli.md>。
- FreeToken quick start: <https://github.com/FlashML-org/FreeToken/blob/main/docs/quickstart.md>。
- FreeToken install: <https://github.com/FlashML-org/FreeToken/blob/main/docs/install.md>。
