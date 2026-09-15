---
title: "oMLX：macOS 菜单栏里的 LLM 推理服务器，连续批处理 + 热冷 KV 缓存"
date: "2026-05-11T13:10:00+08:00"
slug: "omlx-apple-silicon-llm-inference-server"
github_repo: "jundot/omlx"
source_key: "gh:jundot/omlx"
description: "深度解析 jundot/omlx：Apple Silicon 原生 LLM 推理服务器，支持连续批处理和热冷两级 KV 缓存，从 macOS 菜单栏一键管理，兼容 OpenAI 与 Anthropic API。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "Apple Silicon", "macOS", "MLX", "本地部署", "性能优化"]
hiddenFromHomePage: true
---

> "我试过的每个 LLM 服务器都要我在便利性和控制性之间二选一。我想把常用模型固定在内存里，让更重的模型按需自动换入换出，还能设置上下文限制——全部从菜单栏管理。"
>
> "oMLX 把 KV cache 持久化在内存热层和 SSD 冷层之间——即使对话中途上下文发生变化，所有历史上下文依然缓存可复用。这让本地 LLM 在 Claude Code 这类工具里真正可用。这就是我造它的原因。"

---

## 学习目标

读完本文，你应该能回答这些问题：

- oMLX 在 mlx-lm、Ollama 已经存在的情况下，补上了哪块空缺
- 连续批处理、热冷两级 KV 缓存分别解决什么问题，代价是什么
- 怎么安装和启动 oMLX（macOS App、Homebrew、源码三条路），哪些功能默认关闭需要手动开
- 管理面板能做什么，怎么把它接到 Claude Code 等编程工具上
- 什么场景该用它，什么场景不该

---

## 目录

- [一句话定位](#一句话定位)
- [解决什么问题](#解决什么问题)
  - [连续批处理](#连续批处理)
  - [热冷两级 KV 缓存](#热冷两级-kv-缓存)
  - [Claude Code 优化](#claude-code-优化)
- [核心功能](#核心功能)
  - [支持的模型类型](#支持的模型类型)
  - [多模型同时服务](#多模型同时服务)
  - [API 层](#api-层)
  - [管理面板](#管理面板)
- [安装方式](#安装方式)
  - [macOS App（推荐）](#macos-app推荐)
  - [Homebrew](#homebrew)
  - [从源码](#从源码)
- [快速开始](#快速开始)
- [技术架构](#技术架构)
  - [架构总览](#架构总览)
  - [KV 缓存实现细节](#kv-缓存实现细节)
  - [内存守护](#内存守护)
- [与同类工具的比较](#与同类工具的比较)
- [适用场景](#适用场景)
- [常见问题与故障排查](#常见问题与故障排查)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [总结](#总结)

---

## 一句话定位

[oMLX](https://github.com/jundot/omlx) 是一个 Apple Silicon 专属的 LLM 推理服务器，三件事构成了它的识别度：

- **连续批处理**（Continuous Batching）：多个请求共享同一轮 GPU 前向计算
- **热冷两级 KV 缓存**：内存热层 + SSD 冷层，缓存落盘后重启服务也不丢
- **macOS 菜单栏 App**：不用碰终端也能管理模型、监控内存、跑 benchmark

项目用 Python 写核心、SwiftUI 写菜单栏 App，Apache 2.0 许可证，2026 年 2 月创建。它从 [vllm-mlx](https://github.com/waybarrios/vllm-mlx) v0.1.0 分叉而来，之后在多模型服务、分级 KV 缓存、VLM 分页缓存、管理面板和菜单栏 App 上走了很远的路。写作时（2026-09）GitHub ⭐ 21.7k，最新版本 v0.6.4。

---

## 解决什么问题

在 Apple Silicon 上跑本地 LLM，mlx-lm 给了推理引擎，Ollama 给了开箱即用。oMLX 补的是中间那层"服务器"能力——并发调度、缓存复用、内存治理，也就是 vLLM 在数据中心里提供的那类东西，但针对 Mac 的统一内存重新设计。

### 连续批处理

传统做法要么串行处理请求，要么攒满一批再算，前者浪费 GPU 空转，后者拖累先到的请求。连续批处理让每个生成步都重新组批：某个请求生成完了，下一个请求立刻补进槽位。

oMLX 的调度器是 FCFS（先到先服务），批处理交给 mlx-lm 的 BatchGenerator 执行。并发上限通过 `--max-concurrent-requests` 控制，默认 8，CLI 和管理面板都能改。调大吞吐更高，代价是内存占用上升——Apple Silicon 的统一内存就那么多，这个参数实际上是在拿内存换并发。

### 热冷两级 KV 缓存

这是 oMLX 最下功夫的部分。KV 缓存（KV cache）保存 prompt 和已生成内容的注意力中间结果，算一次不便宜；如果每次请求都从零算，多轮对话和长 system prompt 的场景就浪费掉了。

oMLX 把 KV cache 分成两级：

```text
┌────────────────────────────────────────────────┐
│  GPU 分页缓存（PagedCacheManager）              │
│  block 化管理，支持 CoW 和 prefix 共享          │
├────────────────────────────────────────────────┤
│  热层（Hot Cache，内存）                        │
│  常用上下文的 KV block 常驻内存，恢复零拷贝      │
├────────────────────────────────────────────────┤
│  冷层（PagedSSDCacheManager，SSD）              │
│  热层放不下的 block 落盘为 safetensors          │
│  下次命中这段 prefix 时从 SSD 读回内存          │
└────────────────────────────────────────────────┘
```

两级缓存都默认关闭，需要显式开启——这是很多读者会踩的第一个坑：

```bash
# 冷层：指定目录即启用，默认目录是 ~/.omlx/cache
omlx serve --model-dir ~/models --paged-ssd-cache-dir ~/.omlx/cache

# 热层：默认 "0"（禁用），按需给容量，支持绝对值或百分比
omlx serve --model-dir ~/models --hot-cache-max-size 20%
```

落盘的是 safetensors 格式，不做压缩。缓存上限默认自适应（约为 SSD 容量的 10%），可用 `--paged-ssd-cache-max-size` 显式指定。

它换来三个实际收益：

- **多轮对话复用**：同一对话的历史上下文只算一次，轮次越多省得越多
- **会话切换不抖**：作者引语里那句"对话中途上下文变化也能复用"针对的正是 Claude Code 的 auto-compact 场景——压缩后 prompt 变了，但变化前的 KV 还在缓存里，能按最长公共前缀命中
- **重启不丢**：SSD 上的缓存跨进程存活，重启服务后老会话依然能秒级恢复

### Claude Code 优化

一个细分但实用的设计。小上下文模型跑在 Claude Code 里有两个具体麻烦：上下文用量报告不准导致 auto-compact 触发时机不对；长 prefill 期间客户端读超时。oMLX 的对策：

- **上下文缩放**（context scaling）：按模型实际窗口缩放上报的 token 数，让 auto-compact 在正确时机触发
- **SSE keep-alive**：长 prefill 期间持续发协议级心跳，防止读取超时。`--sse-keepalive-mode` 可选 `chunk`（默认，协议兼容的空事件）、`comment`（旧的 `: keep-alive` 注释行）、`off`

---

## 核心功能

### 支持的模型类型

| 类型 | 示例 | 说明 |
|------|------|------|
| LLM | mlx-lm 支持的任意文本模型 | 纯文本生成 |
| VLM | Qwen3.5 系列、GLM-4V、Pixtral 等 mlx-vlm 模型 | 多图对话，base64/URL/文件三种图片输入 |
| OCR | DeepSeek-OCR、DOTS-OCR、GLM-OCR | 自动检测并套用优化过的 prompt |
| Embedding | BERT、BGE-M3、ModernBERT | 文本向量化 |
| Reranker | ModernBERT、XLM-RoBERTa | 检索重排 |

模型放在 `--model-dir` 的子目录下即被自动发现，支持 `mlx-community/model-name/` 这类两级目录，不用手动注册。类型由自动检测决定，检测错了可以在管理面板里手动覆盖。

### 多模型同时服务

一个实例同时加载多个模型，内存治理有五层手段：

- **LRU 驱逐**：内存吃紧时自动卸载最久未用的模型
- **模型固定（Pin）**：常用模型钉在内存里，不参与驱逐
- **Per-model TTL**：给单个模型设空闲超时（`ttl_seconds`），到点自动卸载；跑 benchmark 时会自动暂停
- **手动加载/卸载**：管理面板里点状态徽章完成
- **进程内存强制（ProcessMemoryEnforcer）**：总内存上限默认 `系统 RAM - 8GB`，防止把系统整体拖进 OOM

每个模型还有独立的设置面：采样参数、chat template 参数、TTL、**别名**（`/v1/models` 返回别名，请求用别名或目录名都认）、**类型覆盖**、**Profile**。Profile 值得单独说一句：把一组模型设置存成命名配置，还能直接暴露成 `<model>:<profile>` 这样的模型 ID——比如 `qwen3-8b:thinking` 跑在同一引擎上，按请求叠加 Profile 设置，不额外占内存、不用重新加载。

### API 层

服务器是 FastAPI 实现的，兼容两套协议：

- **OpenAI API**：`/v1/chat/completions`、`/v1/models`、`/v1/embeddings`、rerank、Responses API，支持工具调用、grammar 约束、reasoning 输出
- **Anthropic API**：直接对接按 Anthropic 协议说话的客户端，Claude Code 属于这一类

此外还有音频转写（`/v1/audio/transcriptions`）、MCP 工具集成（`--mcp-config` 挂载配置文件）、内置 websearch 路由。

### 管理面板

Web UI 在 `/admin`，能力覆盖日常运维：

- 实时监控（内存水位、请求延迟）
- 模型管理（加载/卸载/固定/TTL/别名/Profile）
- 内置聊天：历史记录、模型切换、深色模式、reasoning 输出、VLM/OCR 图片上传
- 模型下载器：直接搜 HuggingFace，看模型卡和文件大小，一键下载
- Benchmark：测 prefill（PP）和生成（TG）速度，带部分前缀缓存命中测试，数字更接近真实使用
- 集成配置：OpenClaw、OpenCode、Codex、Codex App、Hermes Agent、Copilot、Pi、Claude 一键写入配置

界面有英、中、韩、日、法、俄、西、巴西葡语 8 种语言，CDN 依赖全部 vendored，断网也能用。

---

## 安装方式

### macOS App（推荐）

从 [Releases](https://github.com/jundot/omlx/releases) 下载 `.dmg` 拖进 Applications。内置自动更新，升级一键完成。App 会顺带装一个 `~/.omlx/bin/omlx` 的 CLI shim，终端命令和 Apple 快捷指令照样能控制 App 托管的服务。

### Homebrew

```bash
brew tap jundot/omlx https://github.com/jundot/omlx
brew install jundot/omlx/omlx

# 升级
brew update && brew upgrade omlx

# 后台服务方式运行（崩溃自动重启）
omlx start

# 可选：MCP 支持
/opt/homebrew/opt/omlx/libexec/bin/pip install mcp
```

### 从源码

```bash
git clone https://github.com/jundot/omlx.git
cd omlx
pip install -e .          # 仅核心
pip install -e ".[mcp]"   # 含 MCP 支持

# GLM-5.2 / MiniMax M3 / Qwen3.5 的原生自定义内核（服务这些模型家族强烈建议）
OMLX_WITH_CUSTOM_KERNEL=1 pip install -e .
```

要求：macOS 15.0+（Sequoia）、Python 3.11–3.13、Apple Silicon（M1–M5）。

自定义内核值得注意：普通的 `pip install -e .` **不会**编译它们，受影响的模型家族会静默回退到慢得多的通用路径——GLM-5.2 的 fused DSA prefill 有内核时约 845 tok/s，回退后约 29 tok/s（M3 Ultra 实测，差 30 倍左右），且回退路径更耗内存。编译内核需要完整 Xcode 的 Metal 工具链，仅装 Command Line Tools 不够。不想折腾就选官方 DMG，内核是预编译好的。装完可以验证：

```bash
python -c "from omlx.custom_kernels import native_kernel_status; print(native_kernel_status())"
```

---

## 快速开始

```bash
# 托管后台服务（macOS App / Homebrew 安装可用）
omlx start    # 启动
omlx stop     # 停止
omlx restart  # 重启

# 前台启动（默认 memory guard = balanced）
omlx serve --model-dir ~/models

# 服务发现目录下所有模型，API 地址：http://localhost:8000/v1
# 内置聊天：http://localhost:8000/admin/chat
```

接入编程工具用 `launch` 子命令，它替你写好配置再拉起工具：

```bash
# 支持的工具：claude, copilot, codex, codex_app, opencode, openclaw, hermes, pi
omlx launch claude --model qwen3-coder-next-8bit

# Claude Code 可以映射三档模型（Opus/Sonnet/Haiku 请求分别落到哪些本地模型）
omlx launch claude --opus gpt-oss-120b --sonnet qwen3-coder-next-8bit --haiku qwen3-8b
```

手动配置也行——设置 OpenAI 兼容环境变量：

```bash
export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_API_KEY=any
```

两条安全规则要记住：服务默认只绑 `127.0.0.1`；一旦改绑到 LAN 地址或 `0.0.0.0`，必须先设 API key（`--api-key` 或 `OMLX_API_KEY`），否则服务器直接拒绝启动。所有设置持久化在 `~/.omlx/settings.json`，CLI 标志优先于文件。

---

## 技术架构

### 架构总览

```text
FastAPI 服务器（OpenAI / Anthropic API）
    │
    ├── EnginePool（多模型、LRU 驱逐、TTL、手动加载/卸载）
    │   ├── BatchedEngine（LLM，连续批处理）
    │   ├── VLMEngine（视觉语言模型）
    │   ├── EmbeddingEngine
    │   └── RerankerEngine
    │
    ├── ProcessMemoryEnforcer（总内存上限、TTL 检查）
    │
    ├── Scheduler（FCFS，可配置并发）
    │   └── mlx-lm BatchGenerator
    │
    └── 缓存栈
        ├── PagedCacheManager（GPU，block 化，CoW，prefix 共享）
        ├── Hot Cache（内存热层，默认 write-back）
        └── PagedSSDCacheManager（SSD 冷层，safetensors 格式）
```

### KV 缓存实现细节

缓存按 block 组织，每个 block 64 个 token（`block_size=64`）。相同前缀的请求通过 copy-on-write 共享 block 引用，多个会话共用同一段 system prompt 的计算结果，只有分叉之后的 block 才各自持有。

热层默认 write-back：block 先落内存，择机写 SSD。如果要更强的持久性保证，`--hot-cache-write-through` 让每个热层 block 立即同步落盘——恢复速度不变，代价是写放大。冷层命中后把 block 从 SSD 读回内存重建。启动时可用 `--initial-cache-blocks`（默认 256）预分配 block，减少大上下文场景的动态分配开销。

不需要这套缓存时，`--no-cache` 整体关掉，KV 状态退回 mlx-lm BatchGenerator 的进程内管理。

### 内存守护

内存治理的顶层开关是 memory guard，四档：

```bash
omlx serve --model-dir ~/models --memory-guard safe        # 给系统留更多余量
omlx serve --model-dir ~/models --memory-guard balanced    # 默认档
omlx serve --model-dir ~/models --memory-guard aggressive  # 尽量多给 oMLX 用
omlx serve --model-dir ~/models --memory-guard-gb 48       # 自定义上限
```

guard 会在水位接近上限时节流 prefill、按 LRU 卸载引擎，而不是等 macOS 的内存压缩和 swap 兜底——后者正是本地跑大模型"越跑越卡"的常见根源。

---

## 与同类工具的比较

| 工具 | 平台 | 并发批处理 | KV 缓存持久化 | 图形管理界面 |
|------|------|-----------|--------------|-------------|
| **oMLX** | macOS（Apple Silicon） | ✅ BatchGenerator | ✅ 热冷两级，SSD 落盘，重启保留 | ✅ 菜单栏 + Web 面板 |
| **llama.cpp server** | 跨平台 | ✅ 并行 slots | 部分（内存内前缀复用） | ❌ 依赖第三方前端 |
| **Ollama** | 跨平台 | ✅ 并行请求 | 部分（会话内前缀复用） | ✅ 桌面 App |
| **mlx-lm server** | Apple Silicon | ✅ BatchGenerator | ❌ 进程退出即失 | ❌ |
| **vLLM** | Linux/GPU 为主 | ✅ PagedAttention | ✅ 前缀缓存（内存级，可外接 LMCache 落盘） | ❌ 需第三方工具 |

读这张表的正确方式：并发批处理在成熟的推理服务器里已是标配，oMLX 的差异不在"有"，而在**打包方式**——SSD 级 KV 持久化、菜单栏 App、管理面板、Claude Code 适配，这几样凑齐在 macOS 上没有第二个选择。如果你在 Linux + NVIDIA 卡的环境里，vLLM 生态仍然更成熟。

---

## 适用场景

**合适：**

- Apple Silicon 用户要本地跑 LLM（隐私、成本、离线任一理由都成立）
- Claude Code、OpenCode、OpenClaw 等编程工具想接本地模型后端
- 多模型共存：一个实例伺候 LLM + VLM + embedding + reranker，省掉多套进程
- 长对话、长 system prompt 的多轮场景，KV 复用的收益随轮次放大
- 想要图形面板而不是记一堆 CLI 参数的团队

**不合适：**

- Linux、Windows 或非 Apple 硬件——oMLX 是 macOS 专属
- 极致单请求延迟优先的场景，llama.cpp 的精调路径可能更快
- 生产级高并发服务，vLLM 的调度和生态更抗压

---

## 常见问题与故障排查

### 模型加载失败，日志报内存不足

Apple Silicon 统一内存有限，大参数模型装不下是物理约束。处理顺序：换量化模型（4-bit/8-bit）；给不常用的模型设 per-model TTL 自动卸载；把常用模型固定、其余手动卸载；检查 memory guard 档位是否过紧，必要时用 `--memory-guard-gb` 放宽。

### 多轮对话没有变快，KV 缓存像是没生效

按可能性排查：两级缓存是否开了（`--paged-ssd-cache-dir` 和 `--hot-cache-max-size` 默认都关闭）；请求的 prompt 前缀是否真的相同——system prompt 差一个字符就整段不命中；管理面板里看缓存命中率统计确认是"没命中"还是"命中了但 prefill 本来就快"。保持客户端侧 prompt 模板稳定是命中的前提。

### Claude Code 连不上 oMLX

先确认服务活着：`curl http://localhost:8000/v1/models`。再查端口占用 `lsof -i :8000`。环境变量用 `launch` 子命令可以免配——`omlx launch claude` 会替你写好。也可以在管理面板的集成页一键配置。改过 host 之后连不上，多半是触发了非回环绑定必须设 API key 的安全规则。

### 推理速度不如预期

看管理面板并发数（默认 8，排队会在监控里显示）；看缓存命中率；用内置 benchmark 区分 prefill 慢还是 decode 慢——前者常是缓存未命中，后者常是内存带宽打满。服务 GLM-5.2 / MiniMax M3 / Qwen3.5 时确认自定义内核状态（见安装一节的验证命令），回退到通用内核会慢一个数量级。系统层面用活动监视器确认是否已经进入内存压缩/swap。

---

## 自测题

### 连续批处理的边界

**问题**：oMLX 的连续批处理为什么能提高并发吞吐？把 `--max-concurrent-requests` 无限调大会发生什么？

<details>
<summary>参考答案</summary>

批处理把多个请求合进同一轮 GPU 前向计算，GPU 的矩阵运算单元在单请求下本来就有闲置，合批后单位计算摊到更多 token 上，吞吐随之上升，且不显著拉长单请求延迟。

但每多一个并发请求就多一份 KV 状态和激活内存。Apple Silicon 统一内存总量固定，并发调过头后 memory guard 会节流 prefill、LRU 卸载模型，吞吐反而下降，甚至触发系统级 swap。默认值 8 是吞吐与内存的折中，不是性能上限。
</details>

### 热冷两级缓存

**问题**：oMLX 的 KV 缓存分几层？各层什么时候生效？哪一层让"重启服务后老会话依然秒恢复"成为可能？

<details>
<summary>参考答案</summary>

三层：GPU 分页缓存（block 化、CoW、prefix 共享，始终在）→ 内存热层（默认禁用，需 `--hot-cache-max-size` 开启，write-back 语义）→ SSD 冷层（需 `--paged-ssd-cache-dir` 开启，safetensors 格式落盘）。

跨重启的是 SSD 冷层：落盘的 block 不随进程消亡，服务重启后命中同一段 prefix 时直接从 SSD 读回内存，跳过整段 prefill。热层负责"恢复零等待"，冷层负责"存量不丢"。
</details>

### Claude Code 优化

**问题**：小上下文模型跑在 Claude Code 里会遇到哪两个具体问题？oMLX 分别怎么解？

<details>
<summary>参考答案</summary>

一是上下文用量报告不准：模型实际窗口比 Claude Code 假设的小，auto-compact 触发时机错位，要么触发太晚爆上下文，要么太早浪费缓存。oMLX 的 context scaling 按真实窗口缩放上报的 token 数，让触发点回到正确位置。

二是长 prefill 期间客户端读超时：长 prompt 处理时间长，HTTP 连接静默。oMLX 在 prefill 期间发 SSE keep-alive（默认 `chunk` 模式，协议级空事件），保住连接不超时。
</details>

### 与 vLLM 的异同

**问题**：oMLX 和 vLLM 在设计上最像的一点是什么？最大的分野在哪里？

<details>
<summary>参考答案</summary>

最像的是内存管理哲学：vLLM 用 PagedAttention 把 KV cache 切成页，oMLX 把 KV cache 切成 64-token 的 block，都借鉴了操作系统虚拟内存的思路（分页、CoW、共享）。oMLX 本身就从 vllm-mlx 分叉而来。

分野在硬件与部署面：vLLM 面向 Linux + NVIDIA GPU 的数据中心场景，缓存分层在内存级（落盘要外接 LMCache 这类方案）；oMLX 面向 Mac 的统一内存，把 SSD 直接做进缓存层级，并配了菜单栏 App 和面板，瞄准个人与小组件的本地部署。
</details>

### 场景判断

**问题**：以下场景该不该用 oMLX？说明理由。
1. 32GB 的 M4 MacBook Air，想给 Claude Code 接一个本地 8B 编码模型
2. Linux 服务器，100 人共用的内部 API
3. Windows 台式机 + RTX 4090
4. 多轮客服机器人，system prompt 很长，M3 Max 64GB

<details>
<summary>参考答案</summary>

1. **该用**。8B 量化模型在 32GB 上绰绰有余；context scaling 和 keep-alive 正为这种用法设计；launch 一条命令完成接入。
2. **不该用**。平台不符，且这个量级应该上 vLLM。
3. **不该用**。oMLX 不支持 Windows/NVIDIA，选 Ollama 或 llama.cpp。
4. **适合但要看指标**。长 system prompt 是 KV 复用收益最大的场景，开启两级缓存后命中收益随并发会话数放大。64GB 足够，但应设置 memory guard 和模型 TTL，避免多个长会话叠加把系统拖进 swap。
</details>

---

## 进阶路径

**阶段 1：把功能用全。** 过一遍 `omlx serve --help`（参数比本文多）；在管理面板里把 per-model 设置、Profile、benchmark 各跑一遍；用 `--hf-endpoint` 接 HuggingFace 镜像加速模型下载。

**阶段 2：理解推理优化这摊事。** 连续批处理、paged KV cache、量化、speculative decoding 四件套是所有推理服务器的通用语言；补一下 Apple 统一内存（Unified Memory）的带宽特性，很多"为什么慢"的答案在那里。

**阶段 3：读源码。** 缓存栈在 `omlx/cache/`（`paged_cache.py`、`paged_ssd_cache.py`、`factory.py` 是入口）；调度在 `omlx/scheduler.py`；`omlx/speculative/` 和 `omlx/specprefill/` 是投机解码与 prefill 优化的实现；量化相关看 `oQ_Quantization.md` 和 MoE 专家卸载的 `MoE_Expert_Offload.md`（docs 目录下）。

**阶段 4：走向更远的部署。** `omlx cluster` 子命令和 `docs/distributed-cluster.md` 描述了实验性的跨 Mac 流水线并行（一台模型拆到两台内存不等的 Mac 上跑）；`docs/heterogeneous-cluster.md` 里有 Mac + NVIDIA 的异构实验。想给 oMLX 提贡献，从 `docs/CONTRIBUTING.md` 进入。

---

## 总结

oMLX 把 vLLM 一系的工程能力——连续批处理、分页 KV 缓存——搬到了 Apple Silicon 上，又补了三样数据中心方案不会给你配的东西：SSD 级缓存持久化、菜单栏 App、对 Claude Code 这类编程工具的针对性适配。

它的短板同样清晰：macOS 专属、单机定位、分布式支持还在实验期。对在 Mac 上写代码、想让编程工具吃上本地模型的开发者来说，它是当前完成度最高的选择；对其他平台，前文对比表里的工具依然是更合适的答案。

---

**项目信息**

- GitHub：[jundot/omlx](https://github.com/jundot/omlx) ⭐ 21.7k（2026-09 核实）
- 版本：v0.6.4（2026-08-29 发布）
- 语言：Python（核心）、Swift（菜单栏 App）
- 平台：macOS 15.0+ Apple Silicon（M1–M5）专用
- 许可证：Apache 2.0
- 官网：[omlx.ai](https://omlx.ai)
