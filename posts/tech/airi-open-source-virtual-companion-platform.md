---
title: "AIRI：开源虚拟存在平台，让每个人拥有自己的数字伴侣"
date: "2026-05-25T23:09:09+08:00"
slug: "airi-open-source-virtual-companion-platform"
description: "AIRI 是一个开源虚拟存在平台，灵感来自 Neuro-sama，基于 Web 技术栈构建，支持浏览器、桌面和移动端多端部署，集成了十余种 LLM API，可与 Discord、Telegram 聊天，并在 Minecraft、Factorio 等游戏中与用户互动。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "VTuber", "WebGPU", "WebAssembly", "LLM", "TypeScript"]
---

在 AI 虚拟存在（又称"数字人"）这个方向上，Neuro-sama 是目前最成熟的案例——能打游戏、能聊天、能与观众互动。但它是闭源的，直播结束后就无法再交互。

**AIRI** 想做的事很简单：让每个人都能拥有自己的数字伴侣，而且源码开放、平台自选。

这不是又一个"套壳 LLM 对话机器人"。AIRI 的核心差异化在于，它从第一天起就选择了一条少有人走的路——**基于 Web 技术栈构建跨端虚拟存在引擎**，同时在桌面版通过 HuggingFace Candle 支持 NVIDIA CUDA 和 Apple Metal，在不损失性能的前提下保留了 Web 生态的部署灵活性。

## 系统总览

AIRI 并不是一个单体应用，而是一个由多个子项目构成的**平台级系统**，涵盖从前端渲染到后端推理的完整链路。

```
Core（核心逻辑层）
├── xsAI（统一 LLM 接口层，支持 20+ API 提供商）
├── Server SDK / Server Runtime（游戏代理与服务器通信）
└── STT / TTS（语音识别与合成）

Apps（多端实现）
├── Stage Web     → 浏览器版（airi.moeru.ai）
├── Stage Tamagotchi → 桌面 Electron 版
└── Stage Pocket  → 移动端（Capacitor + PWA）

UI 组件生态
├── Stage UI（VTuber 渲染界面）
├── @proj-airi/ui-transitions
├── @proj-airi/ui-loading-screens
└── 字体组件（@proj-airi/font-cjkfonts-allseto 等）

游戏代理子项目
├── AIRI Minecraft（基于 Mineflayer）
└── AIRI Factorio（基于 Factorio RCON API）

辅助工具链
├── unspeech（ASR/TTS 统一端点代理）
├── hfup（HuggingFace Spaces 部署工具）
├── MCP Launcher（模型上下文协议服务器构建器）
└── duckdb-wasm（浏览器端嵌入数据库）
```

从架构图可以看到三条主线并行：

- **渲染链路**：VRM / Live2D 模型 → Stage UI → 多端前端
- **AI 链路**：LLM API → xsAI → Core → 语音合成
- **游戏链路**：游戏服务器（Mineflayer / Factorio RCON）→ Server Runtime → LLM 决策

三条链路在 Core 层交汇，这也是 AIRI 最核心的价值所在——把 AI 对话、语音交互和游戏操作整合在同一个调度框架里。

## 多端部署：Web 技术栈的边界与突破

### 浏览器版（Stage Web）

AIRI 最初的设计目标就是"能在浏览器里跑"。Stage Web 部署在 `airi.moeru.ai`，用户无需安装任何客户端，直接打开网页即可与虚拟角色对话。

这带来了一个工程上的天然矛盾：Web 环境受限于浏览器的沙箱和渲染管线，性能远不如原生应用。但 AIRI 的解决思路很务实——**浏览器版的意义不是替代桌面版，而是展示 Web 技术栈能做到什么程度的边界**。

Stage Web 使用的技术栈：

- **WebGPU**：承担 3D 模型渲染（VRM 格式）的计算密集工作
- **WebAssembly**：运行 DuckDB WASM 实现浏览器端嵌入数据库查询
- **Web Workers**：将语音识别模型推理移出主线程，避免 UI 阻塞
- **WebAudio**：处理实时音频流，与语音合成管线对接
- **WebSocket**：连接后端 Server Runtime，支持 Discord 和 Telegram 消息的实时推送

### 桌面版（Stage Tamagotchi）

如果浏览器版是技术展示，那桌面版才是真正的性能释放。

Tamagotchi 基于 Electron，但渲染层走的仍然是 Web 技术（Vue.js + Web 布局引擎），只是在**推理层面**借助了 HuggingFace [Candle](https://github.com/huggingface/candle) 项目，获得了直接调用 NVIDIA CUDA 和 Apple Metal 的能力——无需配置复杂的本地 Python 环境或安装 torch/cuDNN。

Candle 是 Rust 写的轻量级 ML 推理框架，天然适合嵌入 Electron 的 IPC 通信层。AIRI 桌面版在后台默默地把 LLM 推理请求路由到 Candle，享受原生 GPU 加速，同时前端依然保持 Web 开发体验。

### 移动端（Stage Pocket）

移动版通过 Capacitor 将 Web 代码打包为 iOS/Android 应用，同时保留了 PWA 的渐进增强特性。开发团队提到，如果要让 Pocket 版在无线模式下连接 Tamagotchi 后端，需要以 root 权限启动桌面版并开启安全 WebSocket——这更多是开发/调试场景的约束，而非日常使用的限制。

## AI 管线：xsAI 统一接口层

AIRI 并没有自己训练模型，而是扮演了一个**模型编排层**的角色。它通过子项目 [xsAI](https://github.com/moeru-ai/xsai) 接入 20+ LLM API 提供商：

| 提供商 | 接入状态 | 说明 |
|--------|----------|------|
| OpenAI | ✅ | 含 Azure OpenAI |
| Anthropic Claude | ✅ | |
| DeepSeek | ✅ | |
| Qwen（阿里云） | ✅ | |
| Google Gemini | ✅ | |
| xAI（Grok） | ✅ | |
| Groq | ✅ | |
| vLLM / SGLang | ✅ | 自托管 |
| Ollama | ✅ | 本地模型 |
| Mistral | ✅ | |
| Cloudflare Workers AI | ✅ | |
| Together.ai | ✅ | |
| Fireworks.ai | ✅ | |
| Novita | ✅ | |
| Zhipu（智谱） | ✅ | |
| SiliconFlow | ✅ | |
| Stepfun | ✅ | |
| Minimax | ✅ | |
| Moonshot AI | ✅ | |
| 小米 Mimo | ✅ | |

xsAI 的定位类似 [LiteLLM](https://github.com/BerriAI/litellm)——统一不同提供商的对接接口，但体积更小，专注于 AIRI 实际需要的 LLM 调用场景。

这个设计让用户可以自由切换模型提供商，而不需要修改 AIRI 的核心代码。

## 游戏代理：让虚拟存在"会玩游戏"

这是 AIRI 与大多数 AI 对话平台拉开差距的地方。

### Minecraft 代理

基于 [Mineflayer](https://github.com/Mineflayer/mineflayer) 构建。Minecraft 服务器在后台运行，AIRI 通过 LLM 生成决策指令，Mineflayer 将指令转换为具体的游戏操作（移动、攻击、放置方块等），游戏状态再反馈回 LLM 形成闭环。

这本质上是一个 **LLM + 游戏 API 的 agent 框架**，不是游戏"辅助工具"，而是让 AI 有能力理解游戏世界的当前状态并采取行动。

### Factorio 代理

Factorio 的自动化复杂度比 Minecraft 更高——AI 需要理解工厂流水线的逻辑（资源采集、加工、装配、运输），而不是简单的空间操作。

AIRI Factorio 子项目通过 [Factorio RCON API](https://github.com/nekomeowww/factorio-rcon-api) 与游戏服务器通信，[autorio](https://github.com/moeru-ai/airi-factorio/tree/main/packages/autorio) 库负责把 LLM 的高层指令翻译为可执行的流水线操作序列。

### 正在开发中的游戏支持

- Kerbal Space Program（已预告，正式发布日期待定）
- Helldivers 2（进行中）

## 虚拟形象：VRM 与 Live2D 双轨支持

虚拟存在的"形象层"通过两条并行路径实现：

**VRM 路径**：基于 pixiv 的 [ChatVRM](https://github.com/pixiv/ChatVRM) 项目，支持控制 VRM 模型姿态、自动眨眼、视线追踪（look-at）和待机时的微眼动。浏览器版和桌面版均支持。

**Live2D 路径**：支持 Live2D 模型动画，同样具备自动眨眼、视线追踪和待机微动。适合已有大量 Live2D 资产的创作者。

两条路径共享同一个 Stage UI 渲染框架，只是模型格式不同。加载对应模型文件即可切换形象，核心逻辑无需改动。

## 语音管线：从听到说的完整链路

AIRI 的语音管线分三层：

1. **语音输入（Ears）**：
   - 浏览器端：使用 WebAudio API 采集麦克风音频流
   - Discord：直接接收语音频道音频
   - 语音检测（VAD）：客户端本地完成说话检测，避免无效帧上传
   - 语音识别（STT）：客户端 Whisper 推理，文字送入 LLM

2. **LLM 对话（Brain）**：接收文字，生成回复文本

3. **语音输出（Mouth）**：使用 ElevenLabs 将文字合成语音，输出到浏览器音频或 Discord 语音频道

这条链路最值得关注的设计点是**客户端本地 STT**——语音识别不需要上传到云端服务器，在浏览器或桌面客户端本地完成，既降低了延迟，也保护了隐私。

## 子项目生态：平台化的标志

AIRI 不只是一个应用，而是一个持续生长的工具链生态。子项目被收纳在独立的 [@proj-airi](https://github.com/proj-airi) 组织下，说明项目方有意将它们发展为可独立使用的库和工具：

- **unspeech**：ASR/TTS 统一代理端点，类似 LiteLLM 但是面向语音服务
- **hfup**：帮助开发者将模型和数据集部署到 HuggingFace Spaces
- **xsai-transformers**：🤗 Transformers.js 的 xsAI provider，实验性质
- **@proj-airi/drizzle-duckdb-wasm**：Drizzle ORM 的 DuckDB WASM 驱动
- **@proj-airi/duckdb-wasm**：DuckDB WASM 的易用封装
- **MCP Launcher**：一站式 MCP（Model Context Protocol）服务器构建和启动工具，"Minecraft 式的模型服务管理"
- **🥺 SAD**：`self-host and browser running LLMs` 的文档与笔记集合
- **Awesome AI VTuber**：AI VTuber 相关项目和资源的精选列表

这些子项目如果独立发展，AIRI 平台的可扩展性会持续增强——用户不仅可以"使用"AIRI，还可以在它的基础设施上构建自己的应用。

## 一个任务如何流过 AIRI 系统

以"在 Discord 语音频道和 AIRI 聊天"为例：

```
1. 用户在 Discord 语音频道说话
         ↓
2. Discord 语音网关接收音频流
         ↓
3. Server Runtime 的 STT 层进行本地语音活动检测（VAD）
         ↓ 通过 unspeech 调用本地 Whisper 推理
4. 音频 → 文字
         ↓
5. 文字送入 xsAI，由配置的 LLM（假设是 Claude）生成回复
         ↓
6. 回复文本通过 ElevenLabs 合成语音
         ↓
7. 语音流推回 Discord 语音频道
         ↓
8. 若用户触发游戏指令（如"帮我造个自动采矿机"）
         ↓
9. Server Runtime 将指令路由给 Factorio RCON API
         ↓
10. Factorio Agent 调用 autorio 执行具体操作序列
```

整个链路的关键瓶颈在 STT（本地推理质量）和 LLM 响应延迟。浏览器版和桌面版的差异在这里体现得最明显——桌面版可以用 Candle 做本地 GPU 加速推理，而浏览器版只能依赖外部 API。

## 技术栈全景

| 层级 | 技术选型 |
|------|----------|
| 语言 | TypeScript（全栈） |
| 前端框架 | Vue.js |
| 3D 渲染 | WebGPU（浏览器）/ 原生 Metal（桌面） |
| 模型推理 | HuggingFace Candle（桌面）、WebAssembly（浏览器） |
| 嵌入数据库 | DuckDB WASM / pglite |
| 语音合成 | ElevenLabs |
| 语音识别 | Whisper（客户端本地） |
| 虚拟形象 | VRM + Live2D |
| 游戏集成 | Mineflayer（Minecraft）、Factorio RCON API |
| 通信平台 | Discord、Telegram |
| 包管理器 | pnpm（Monorepo） |
| 构建工具 | Vite |

## 适用边界与采用建议

**AIRI 适合哪些团队和场景：**

- 有实时对话需求的 AI VTuber 直播项目
- 希望在自有产品中嵌入数字人能力的应用开发者
- 对"AI + 游戏"交叉方向感兴趣的研究者和独立开发者
- 想基于成熟开源架构快速搭建 AI 陪伴产品的团队

**目前需要谨慎评估的边界：**

- 内存和延迟敏感的实时交互场景——浏览器版的语音响应质量与本地推理能力正相关
- 生产级游戏代理——Minecraft 和 Factorio 代理仍在活跃开发中，API 稳定性可能有波动
- 多语言支持——中文文档和社区资源相对较少，主要活跃社区在 Discord

**从哪个版本开始：**

如果只是想体验 AIRI 的基本能力，从 [Stage Web](https://airi.moeru.ai) 开始，无需安装任何东西。如果要深入开发或做游戏代理实验，推荐从 [Tamagotchi 桌面版](https://github.com/moeru-ai/airi/releases/latest)入手，获取完整的本地 GPU 加速能力。

## 小结

AIRI 不是一个简单的"AI 对话机器人"，而是一个把 **LLM 对话、实时语音交互、多端渲染和游戏世界代理** 整合在同一套框架里的平台级项目。它的核心工程挑战——在 Web 技术栈约束下实现接近原生的 AI 推理和 3D 渲染——目前已经有了一套可行的解决方案，并通过多端部署策略覆盖了从"零门槛体验"到"高性能桌面"的不同需求层次。

在开源虚拟存在方向，AIRI 是目前社区积累较深、生态较活跃的项目之一。如果你的目标是拥有自己的数字伴侣、或者在游戏场景里构建 AI Agent，这套架构和工具链值得深入研究。