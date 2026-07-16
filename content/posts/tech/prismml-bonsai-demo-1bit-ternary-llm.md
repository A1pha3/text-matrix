---
title: "PrismML-Eng/Bonsai-demo 拆解：当 1-bit / Ternary LLM 走到 27B，能装进手机的同时还能做 vision + tool + thinking 的工程现实"
date: 2026-07-17T02:58:33+08:00
lastmod: 2026-07-17T02:58:33+08:00
draft: false
categories: ["技术笔记"]
tags: ["Bonsai", "1-bit LLM", "Ternary", "llama.cpp"]
description: "Bonsai-demo 是 PrismML 的 1-bit / Ternary LLM 本地 demo，27B/8B/4B/1.7B 通过 llama.cpp + MLX 跑在 Mac/Linux/Windows，27B 支持 vision + thinking + tool calling + MCP。"
weight: 1
slug: "prismml-bonsai-demo-1bit-ternary-llm"
author: text-matrix
---

## 一句话判断

**Bonsai-demo（[PrismML-Eng/Bonsai-demo](https://github.com/PrismML-Eng/Bonsai-demo)）是 PrismML 团队为 1-bit Bonsai 与 Ternary-Bonsai 两个家族的 LLM 提供的"本地一行启动"演示仓库，截至 2026-07 在 GitHub 上约 1.5k stars，Apache-2.0。** 它不是一个模型仓库（模型在 HuggingFace `prism-ml` 命名空间下），而是 **把模型 + llama.cpp fork + MLX fork + chat server + Open WebUI agentic demo + 12 路安装路径** 拼装成一条"在 Mac / Linux / Windows 上跑 27B 1-bit 视觉模型"的工程流水线。

如果你正在评估"在笔记本 / iPhone / 工位机上本地跑 27B 视觉 + 工具调用 LLM"的可行性，或者想搞清楚"1-bit / Ternary 和 Q4_K_M 究竟差多少内存、能装进什么设备"，这篇文章值得完整读完。

---

## 系统地图

Bonsai-demo 的真实架构不是 README 顶部的 logo，而是"模型层 + 运行时层 + 部署形态 + agentic 演示"四层：

```
┌──────────────────────────────────────────────────────────────────────┐
│  模型层 (Model family × size, in HuggingFace prism-ml namespace)      │
│  ┌──────────────────────────────┐  ┌─────────────────────────────┐  │
│  │ Bonsai (1-bit)               │  │ Ternary-Bonsai              │  │
│  │ Q1_0 in llama.cpp            │  │ Q2_0 / Q2_0_g64 in llama.cpp│  │
│  │ MLX 1-bit                    │  │ MLX 2-bit                   │  │
│  │ Sizes: 27B / 8B / 4B / 1.7B  │  │ Sizes: 27B / 8B / 4B / 1.7B │  │
│  └──────────────────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────┐
│  运行时层 (Two runtimes, auto-detected per platform)                  │
│   llama.cpp (CPU/Metal/CUDA/Vulkan/ROCm, via PrismML fork)            │
│   MLX (Apple Silicon, via PrismML fork)                                │
│   Fork status: Q1_0 已合入 mainline; Ternary 部分 backend 在迁移中    │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────┐
│  部署形态 (12 路 install / build paths)                                │
│   macOS Apple Silicon (Metal) / macOS Intel (CPU)                    │
│   Linux CPU / Linux CUDA / Linux Vulkan / Linux ROCm                 │
│   Windows CUDA / Windows CPU                                         │
│   统一入口: ./setup.sh (Unix) 或 setup.ps1 (Windows)                  │
│   重新跑幂等 (skip 已完成步骤)                                          │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────┐
│  Agentic Demo (chat server + Open WebUI)                              │
│   llama-server with built-in chat UI (port 8080)                      │
│     - thinking (reasoning effort: Off/Low/Med/High/Max)               │
│     - tool calling (OpenAI-style native tool_calls)                   │
│     - MCP client (HF + DeepWiki preconfigured, per-chat opt-in)       │
│     - vision (image upload, image_url in API)                         │
│     - 256K+ context, optional 4-bit KV cache (BONSAI_KV4=1)          │
│     - optional speculative decoding (BONSAI_SPECULATIVE=1, ~1.8-2x)  │
│   Open WebUI (可选) → 完整 agentic demo + Jupyter code interpreter    │
└──────────────────────────────────────────────────────────────────────┘
```

这张图最重要的一条路径：**"模型层 → 运行时层 → 部署形态 → agentic demo"**。**模型家族和运行时是解耦的**——同一个 27B 模型既可以走 llama.cpp 也可以走 MLX；**部署形态是平台自动检测的**——同一份 `setup.sh` 在 Mac 和 Linux 上自动选对应二进制。

---

## 边界与角色划分

把 Bonsai-demo 拆成 6 组"不变项"，可以一次性回答它和 llama.cpp 官方仓库 / Ollama / LM Studio / MLX-LM 的差别：

| 维度 | Bonsai-demo 的不变项 | 工程含义 |
|------|----------------------|---------|
| 形态 | Demo 仓库（非模型仓库） | 模型在 HF prism-ml；本仓库是"把模型跑起来"的脚手架 |
| 模型族 | 1-bit Bonsai + Ternary-Bonsai | 不止 1-bit，还有 Ternary（~1.7 bpw 打包到 2-bit）作为更高质量选项 |
| 尺寸 | 27B / 8B / 4B / 1.7B（4 档 × 2 族） | 用 `BONSAI_MODEL` 切换；`all` 一次性下全套 |
| 运行时 | llama.cpp + MLX 双 runtime | 同一模型在 CPU/Apple Silicon/GPU 上都能跑 |
| 部署 | `./setup.sh` 一键 | 自动检测平台、装依赖、下模型、下二进制、构建 venv |
| Agentic | llama-server 内置 chat UI + MCP + tool calling + vision | 不依赖 Open WebUI 也能跑，Open WebUI 是增强 demo |

要注意的几个边界：**Bonsai-demo 不是 llama.cpp**——它依赖 llama.cpp fork，是"在 llama.cpp 之上的安装/运行封装"；**不是 Ollama / LM Studio**——它不提供模型市场、不提供 GUI 下载器；**不是 MLX-LM**——它在 MLX fork 上跑，但脚本和入口是 Bonsai 团队自己的。

---

## 关键机制

### 1. 两个模型族：1-bit Bonsai vs Ternary-Bonsai

Bonsai 有两个并行家族：

**Bonsai (1-bit)**：

- 真正的 1-bit 量化（约 1.125 bits per weight）
- `Q1_0` 已经在主版 llama.cpp 合并：CPU（generic / NEON / x86 优化）/ Metal / CUDA / Vulkan 均支持
- MLX 1-bit 在等上游 [mlx#3161](https://github.com/ml-explore/mlx/pull/3161) 合入；在此之前用 PrismML 的 fork `prism` 分支
- 27B 1-bit 权重 ≈ 3.53 GiB，可以装进"现代 iPhone 无需 memory offloading"

**Ternary-Bonsai**：

- 约 1.7 bpw，打包到 2-bit（用于加速 kernel）
- 是这个 demo 的**默认选项**
- 在主版 llama.cpp 的迁移中各 backend 进度不同（见下文）
- 27B Ternary 权重 ≈ 6.66 GiB，质量比 1-bit 高

**两个家族的尺寸选项**：

| 尺寸 | 用途 |
|------|------|
| 27B | 默认；vision-language；支持 thinking / tool calling / MCP / 256K context |
| 8B | 中等场景；速度/质量折中 |
| 4B | 笔记本 / 工位机友好 |
| 1.7B | 边缘 / 嵌入式场景 |

`BONSAI_FAMILY=ternary|bonsai|all` × `BONSAI_MODEL=27B|8B|4B|1.7B|all` 自由组合。

### 2. 内存占用：装进什么设备的关键数据

README 给出的 27B 内存对比表（weights + activations + FP16 KV cache + ~1.2 GiB 开销，文本-only）：

| 模型 | 格式 | 权重 | 4K ctx | 100K ctx |
|------|------|------|--------|----------|
| Bonsai-27B (1-bit) | llama.cpp Q1_0 | 3.53 GiB | 4.8 GiB | 10.8 GiB |
| Bonsai-27B (1-bit) | MLX 1-bit | 3.92 GiB | 5.5 GiB | 11.4 GiB |
| Ternary-Bonsai-27B | llama.cpp Q2_0 | 6.66 GiB | 7.8 GiB | 13.7 GiB |
| Ternary-Bonsai-27B | MLX 2-bit | 7.05 GiB | 8.6 GiB | 14.4 GiB |
| **参考: 27B 16-bit** | GGUF BF16 | **47.73 GiB** | 49 GiB | 55.2 GiB |
| 参考: 27B "4-bit" | llama.cpp UD Q4_K_M | 15.73 GiB | 17.2 GiB | 23.2 GiB |
| 参考: 27B "4-bit" | MLX 4-bit | 13.3 GiB | 17.0 GiB | 22 GiB |

**关键观察**：

- 27B 1-bit 比 27B 16-bit 内存压缩 **13.5 倍**（47.73 → 3.53 GiB）
- 27B 1-bit 比 27B Q4_K_M 还省 **4.5 倍**（15.73 → 3.53 GiB）
- 启用 `BONSAI_KV4=1`（4-bit KV cache）后，100K ctx 从 ~13.7 GiB 降到 ~9.2 GiB
- 100K context 在 Q1_0 上"很多消费设备都能装"（10.8 GiB）

这条数据是判断"我这台设备能不能跑 27B"的决定性参考。

### 3. setup.sh 的工程化细节

`./setup.sh` 在一台新机上做 8 件事：

1. 检查/装系统依赖（macOS Xcode CLT / Linux build-essential）
2. 装 [uv](https://docs.astral.sh/uv/)（user-local 的 Python 包管理器，不是全局）
3. 创建 Python venv 并 `uv sync`（cmake / ninja / huggingface-cli）
4. 从 HuggingFace 下载模型（27B 需要 `BONSAI_TOKEN`，HF read-only token）
5. 从 [GitHub Release](https://github.com/PrismML-Eng/llama.cpp/releases/tag/prism-b9591-62061f9) 下载预编译二进制（或从源码 build）
6. **macOS 上从源码 build MLX fork**（克隆 prism 分支，装 mlx-lm / torch / transformers）
7. **装 Open WebUI** 到 venv（agentic demo，`BONSAI_OPENWEBUI=0` 跳过）
8. **build code-interpreter venv**（`.venv-jupyter`：Jupyter + matplotlib / pandas / numpy / scipy / sympy / yfinance；`BONSAI_CODE_INTERPRETER=0` 跳过）

**关键工程约束**：重新跑 `setup.sh` 是幂等的——已完成的步骤会被跳过。这意味着"先跑一次基线，后面用环境变量换模型 / 关 demo"不会浪费时间。

### 4. 上游迁移状态：哪部分还要 fork

README 明示"Q1_0 已经全 merged upstream，Q2_0 还在迁移中"——这一节是判断"什么时候可以扔掉 fork"的关键：

**Q1_0 (1-bit Bonsai) 上游状态**：

| Runtime | Status |
|---------|--------|
| llama.cpp (CPU, Metal, CUDA, Vulkan) | ✅ Merged upstream, works out of the box |
| MLX (1-bit) | ⏳ Pending [mlx#3161](https://github.com/ml-explore/mlx/pull/3161); 之前用 [PrismML-Eng/mlx](https://github.com/PrismML-Eng/mlx) branch `prism` |

**Q2_0 (Ternary-Bonsai) 上游状态**（三种 GGUF 变体在不同 backend）：

| 文件 | Format | 跑在哪 |
|------|--------|--------|
| `*-Q2_0.gguf` | Group size 128（demo 用这个） | PrismML fork 二进制 |
| `*-Q2_0_g64.gguf` | Group size 64 (2.25 bpw，主版 llama.cpp 格式) | 主版 llama.cpp CPU + Metal |
| `*-PQ2_0.gguf` | fork 计划中，type id 与 Q2_0 共存 | 等 fork 支持 |

各 backend 迁移状态：

| Backend | Status | Where |
|---------|--------|-------|
| CPU (ARM NEON + scalar) | ✅ Merged | [ggml-org/llama.cpp#24448](https://github.com/ggml-org/llama.cpp/pull/24448) |
| Metal | ✅ Merged | [ggml-org/llama.cpp#25419](https://github.com/ggml-org/llama.cpp/pull/25419) |
| Vulkan | 🔄 In progress | [ggml-org/llama.cpp#25430](https://github.com/ggml-org/llama.cpp/pull/25430) |
| CUDA | 🔄 In review | [ggml-org/llama.cpp#25707](https://github.com/ggml-org/llama.cpp/pull/25707) |
| x86 (AVX-512-VNNI) | ⏳ Pending | TBD |

**实用结论**：CPU + Metal 现在用主版 llama.cpp 跑 `Q2_0` 不需要 fork（用 `*-Q2_0_g64.gguf`）；CUDA 和其他 backend 暂时还是要用这个 demo（它带 fork 的预编译二进制）。

### 5. 27B 的 agentic 能力

27B 是这个 demo 里最完整的展示对象——vision / thinking / tool calling / MCP / 长 context / 4-bit KV cache / speculative decoding 全有：

**Thinking**：在 chat UI 里点"灯泡"选 Reasoning effort（Off / Low 512 tokens / Med 2048 / High 8192 / Max unlimited），选完按浏览器持久化，每个请求都带上。慢硬件上 thinking 通常是主要等待时间——选 Low 显著加速。

**Tool calling**：原生 OpenAI-style `tool_calls` 完整往返；chat UI 内置 MCP 客户端，Hugging Face + DeepWiki 预配置（per-chat 选开，不开启不付费）。自定义 server 看 `TOOLS.md`。

**Vision**：chat UI 里 `+` 上传图片；API 走 `image_url` parts；script 自动加载 vision projector，慢 backend 大图自动降采样。`VISION.md` 有成本与 OCR 建议。

**Context size**：27B 支持到 **262,144 tokens**。FP16 KV cache 64 KiB/token，100K 上下文约 6.3 GiB——"很多消费设备能装"。启用 `BONSAI_KV4=1` 后 KV cache 降到约 18 KiB/token，100K 约 1.8 GiB（节省 ~4.5 GiB）。

**Speculative decoding**（`BONSAI_SPECULATIVE=1`）：27B 配 dspark drafter，code/reasoning 上约 **1.8-2x** decode 加速，CUDA 上先支持，Apple Silicon 后续。

**4-bit KV cache**（`BONSAI_KV4=1`）：约 **3.5x** KV-cache 内存压缩；可选 calibration bias（`./scripts/make_kv_bias.sh`）进一步提质量。

### 6. 可选 Open WebUI：完整 agentic demo

不强制——`./scripts/start_llama_server.sh` 直接给一个 llama-server 内置 chat UI（端口 8080）就够了。Open WebUI 提供：

- 完整 chat / agentic 体验
- Code interpreter：Jupyter venv + matplotlib / pandas / numpy / scipy / sympy / yfinance
- 与 llama-server 配合

`BONSAI_OPENWEBUI=0` 跳过；`BONSAI_CODE_INTERPRETER=0` 跳过 code interpreter venv。

### 7. 环境变量速查

| 变量 | 默认 | 用途 |
|------|------|------|
| `BONSAI_FAMILY` | `ternary` | `ternary` / `bonsai` / `all` |
| `BONSAI_MODEL` | `27B` | `27B` / `8B` / `4B` / `1.7B` / `all` |
| `BONSAI_TOKEN` | — | 仅 27B 私有时需要；HF read-only token |
| `BONSAI_OPENWEBUI` | 1 | 1 = 装 Open WebUI |
| `BONSAI_CODE_INTERPRETER` | 1 | 1 = build code-interpreter venv |
| `BONSAI_SPECULATIVE` | 0 | 1 = 启 speculative decoding |
| `BONSAI_KV4` | 0 | 1 = 启 4-bit KV cache |

`all` 只对 `setup.sh` / `setup.ps1` / `download_models.sh` 有效——run/server 脚本需要具体 family/size。

---

## 一个部署如何流过 Bonsai-demo

下面以"M2 MacBook Pro 上跑 Ternary-Bonsai-27B + thinking + tool calling"走一遍：

```
用户在 M2 Mac 上:
        │
        ▼
git clone https://github.com/PrismML-Eng/Bonsai-demo.git
cd Bonsai-demo
        │
        ▼
export BONSAI_TOKEN="hf_xxx"          # 27B 私有时需要
./setup.sh                            # ≈ 10-30 min
  1. 检查 Xcode CLT ✓
  2. 装 uv (user-local)
  3. uv sync → cmake/ninja/huggingface-cli
  4. 下载 Ternary-Bonsai-27B GGUF + MLX 2-bit (双份)
  5. 下载 macOS Metal llama.cpp 二进制 (PrismML fork release)
  6. 从源码 build MLX (prism 分支) → 装 mlx-lm/torch/transformers
  7. 装 Open WebUI + Jupyter venv (可选)
  8. 幂等检查: 已完成步骤跳过
        │
        ▼
./scripts/run_llama.sh -p "Hello!"
  - 自动检测: Mac + Apple Silicon → Metal
  - 自动选: Ternary-Bonsai-27B Q2_0 + llama.cpp
  - 输出 27B 响应
        │
        ▼
./scripts/start_llama_server.sh
  - llama-server 启动在 :8080
  - 内置 chat UI 可访问
  - vision projector 自动加载
  - tool calling + MCP 客户端预配置 (HF + DeepWiki)
        │
        ▼
用户在 chat UI:
  - 上传论文截图 → vision ✓
  - 点灯泡 → 选 Reasoning effort = High
  - 选 MCP = HuggingFace → tool_calls 真实调用 HF API
  - 100K context + 启用 BONSAI_KV4=1 → 内存从 ~13.7 GiB 降到 ~9.2 GiB
        │
        ▼
(可选) 启用 BONSAI_SPECULATIVE=1 → code/reasoning 1.8-2x decode 加速
        │
        ▼
Open WebUI (./scripts/start_openwebui.sh) → 完整 agentic demo + Jupyter 代码解释
```

这个流程覆盖了 **M2 MacBook Pro 上跑 27B vision + thinking + tool calling + MCP + 长 context + 可选 speculative / KV4 / Open WebUI** 的完整能力链。关键看 5 件事：

1. **同一脚本在 macOS / Linux / Windows 上自动选 runtime**（Metal / CPU / CUDA / Vulkan / ROCm）
2. **env var 自由组合 family × size × optional features**
3. **thinking / tool / vision / MCP 都是 27B 原生能力**，不是额外 wrapper
4. **fork 状态是显式标注的**——Q1_0 已 merged upstream，Q2_0 还在迁移
5. **重新跑 setup.sh 是幂等的**——不会浪费时间重做已完成步骤

---

## 采用顺序与适用边界

### 推荐采用顺序

1. **第一次跑 `./setup.sh`**——选默认（Ternary-Bonsai-27B），先验证 baseline 跑得动
2. **`./scripts/run_llama.sh -p "..."`**——CLI 跑通一个 prompt，验证推理链路
3. **`./scripts/start_llama_server.sh`**——起 llama-server 内置 chat UI，验证 UI 链路
4. **试 vision + thinking + tool calling**——上传图片 + 开灯 + 选 MCP server
5. **按需启用 BONSAI_SPECULATIVE=1 / BONSAI_KV4=1**——慢硬件上这两个对体验影响最大
6. **再考虑 Open WebUI**——只在想要 code interpreter + 完整 agentic demo 时启用
7. **想要 build from source**——按 README 给的 7 路 build 指引（macOS Apple Silicon / macOS Intel / Linux CPU / CUDA / Vulkan / ROCm / Windows CUDA / Windows CPU）

### 适用边界

| 适合 | 不适合 |
|------|--------|
| 想在 MacBook / iPhone / 工位机上本地跑 27B | 想要生产级 API 服务（这个 demo 不是 inference server） |
| 关心"模型量化到 1-bit 还能 vision / tool call"的工程可行性 | 不想折腾 llama.cpp fork 的纯下游用户 |
| 想跑 OpenAI-style tool_calls + MCP + thinking 的完整链 | 只想跑个 chat UI（Ollama / LM Studio 更轻量） |
| 想对比 1-bit / Ternary / 4-bit / 16-bit 的内存与质量 | 想要模型市场 / GUI 下载器 |
| 愿意维护自己的 fork 二进制 | 锁死主线 llama.cpp 的项目 |
| 想在 M2 / M3 / M4 上用 MLX | 非 Apple Silicon（MLX 仅 Mac） |

### 风险与未知项

- **27B 仓库当前 private**——README 明示 27B 仍需 `BONSAI_TOKEN`，发布后会去掉；建议部署前先看 HF 仓库是否已 public
- **fork 状态是动态的**——Q2_0 在主版 llama.cpp 各 backend 迁移中；建议每 1-2 月看一次 README "Upstream Status" 段或 [PrismML-Eng/llama.cpp releases](https://github.com/PrismML-Eng/llama.cpp/releases/tag/prism-b9591-62061f9)
- **三种 Ternary GGUF 变体**——`Q2_0` (group 128) / `Q2_0_g64` (group 64) / `PQ2_0` (计划中) 在不同 backend 上跑的位置不同；部署前看 README 的"three ternary GGUF variants"表确认你的 backend 跑哪个
- **MLX 仅 Mac Apple Silicon**——Intel Mac 上没有 MLX 路径，只能走 CPU llama.cpp
- **Open WebUI 与 code interpreter 是 demo**——README 标注 `BONSAI_OPENWEBUI=0` / `BONSAI_CODE_INTERPRETER=0` 可关；不要把它们当作生产服务
- **HF token 仅 read-only**——下载用，不要给 write 权限

---

## 一处延伸阅读

如果想继续深入：

- [PrismML-Eng/Bonsai-demo 仓库](https://github.com/PrismML-Eng/Bonsai-demo)——主仓库，README 的 "Upstream Status" 段是判断 fork 必要性的关键
- [Prism ML HF Collections](https://huggingface.co/collections/prism-ml/bonsai-27b)——27B vision-language 模型集
- [Whitepapers: Bonsai 27B / 1-bit Bonsai 8B / Ternary-Bonsai 8B](https://github.com/PrismML-Eng/Bonsai-demo/tree/main)——设计原理与质量数据
- [VISION.md](VISION.md) / [TOOLS.md](TOOLS.md) / [SPECULATIVE.md](SPECULATIVE.md) / [KV-CACHE.md](KV-CACHE.md)——27B 各项能力的详细文档
- [PrismML-Eng/llama.cpp release prism-b9591-62061f9](https://github.com/PrismML-Eng/llama.cpp/releases/tag/prism-b9591-62061f9)——demo 默认下载的预编译二进制
- [PrismML-Eng/mlx branch prism](https://github.com/PrismML-Eng/mlx)——MLX 1-bit 上游合入前的 fork
