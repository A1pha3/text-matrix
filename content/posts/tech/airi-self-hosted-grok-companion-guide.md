+++
github_repo = "moeru-ai/airi"
source_key = "gh:moeru-ai/airi"
date = '2026-05-28T16:18:30+08:00'
draft = false
title = 'AIRI：自托管 AI 数字伴侣'
slug = 'airi-self-hosted-grok-companion-guide'
description = 'AIRI 是 moeru-ai 复现 Neuro-sama 的开源项目：把 Live2D/VRM 虚拟角色带到桌面与手机，能实时语音对话、接入近 30 家大模型提供商，还能进 Minecraft、Factorio 玩游戏，数据自持。'
categories = ['技术笔记']
tags = ['开源', 'Live2D', '自托管']
+++

# AIRI：自托管 AI 数字伴侣

AIRI 是 moeru-ai 为复现 Neuro-sama 而做的开源项目：把 AI 角色装进 Live2D/VRM 的身体，能实时语音对话，也能进 Minecraft、Factorio 玩游戏。官方在 GitHub 上称它为「you-owned Grok Companion」「数字灵魂容器」；文档站的定位更直白：Neuro-sama 的开源复刻、Grok Companion 的开源替代，以及一个会玩游戏、能感知应用的 SillyTavern 替代品。

把 AIRI 和只换皮肤的聊天壳子区分开的是工程结构。Web、桌面、移动三个 Stage 应用建在同一套共享层上：界面统一走 stage-ui，角色逻辑集中在 core-agent、core-character 两个领域包，Minecraft bot、Discord bot 这类集成通过 server SDK 接入，桌面端由 server-runtime 通道统一调度。聊天、看屏幕、玩游戏三条输入输出线汇进同一份角色状态，而不是各拉一套流程。

---

## 核心数据

以下数据来自 GitHub API 与仓库 README，观测时间 2026-09-14：

| 项 | 值 |
|------|------|
| Stars / Forks | 49,129 / 4,871 |
| 主要语言 | TypeScript |
| 开源协议 | MIT |
| 默认分支 / 最近推送 | main / 2026-09-14 |
| 最新 release | v0.12.0-beta.5（2026-08-29 发布，beta 通道） |
| 官方文档 | airi.moeru.ai/docs/ |

Releases 页面提供 Windows、macOS、Linux 安装包，以及 Android APK 和 iOS IPA；浏览器和移动端也可以走 PWA。项目仍在 0.x beta 阶段，winget、Homebrew 里的版本可能滞后于 GitHub Releases。

---

## 系统总览

AIRI 的工作方式可以概括为三条并行链路汇入同一个领域层：

```mermaid
flowchart LR
  VAD[VAD 检测 + STT] --> DOMAIN[core-agent · core-character 领域层]
  VIS[屏幕视觉输入] --> DOMAIN
  GAME[游戏服务器] --> DOMAIN
  DOMAIN --> XSAI[xsAI 模型接入层] --> LLM[ChatGPT / Claude / Ollama 等]
  LLM -->|结构化决策| DOMAIN
  DOMAIN --> RENDER[stage-ui · Live2D / VRM]
  DOMAIN --> TTS[TTS 语音输出]
  DOMAIN --> MC[Minecraft · minecraft-bot]
  DOMAIN --> FAC[Factorio · RCON / autorio]
  DOMAIN <--> MEM[记忆系统 · RAG · DuckDB / pglite]
```

图做了简化：仓库里 Minecraft bot、Discord bot 这类集成进程实际是通过 server-sdk 与桌面端的 server-runtime 通道通信，再进入领域逻辑，不是直接调用。

三条链路各自的职责：

| 链路 | 入口 | 关键依赖 | 出口 |
|------|------|----------|------|
| 渲染链路 | VRM / Live2D 模型 | stage-ui、stage-ui-live2d / stage-ui-three、WebGPU | 浏览器、桌面、移动端 |
| AI 链路 | LLM API | xsAI、core-agent | STT 输入、TTS 输出 |
| 游戏链路 | Minecraft / Factorio 服务器 | minecraft-bot、Mineflayer、RCON、`autorio` | agent 执行动作 |

渲染链路决定角色如何被看见，AI 链路决定角色如何思考与说话，游戏链路决定角色如何对外部世界产生作用。多数「AI 角色壳子」只覆盖前两条，AIRI 把第三条也拉进来了。

---

## 技术骨架

### 多端部署的三个 Stage

AIRI 把同一套逻辑拆成三个 stage，避免把一种界面硬塞进不同壳子：

- **Stage Web**：直接在浏览器里跑，承担零安装体验的入口，重点依赖 WebGPU、WebAssembly、WebAudio 和 WebSocket。官方在 airi.moeru.ai 提供在线试玩。
- **Stage Tamagotchi**：桌面版，基于 Electron。本地推理通过 HuggingFace 的 Candle 走 CUDA / Metal 加速——Candle 把 HuggingFace 生态的模型权重加载进 Rust 运行时，桌面端据此获得低延迟的本地推理，不必另配 Python 环境。
- **Stage Pocket**：用 Capacitor 复用 Web 代码封装移动端，仓库标注为 experimental。Releases 已附带 Android APK 和 iOS IPA；开发调试则需要用 Capacitor 连真机或模拟器。

三个 stage 的分工对应不同场景：浏览器负责首次体验，桌面端负责长期运行时的低延迟推理，移动端负责随身陪伴。

### xsAI：模型接入层的抽象

模型接入层是一个独立的 xsAI 模块（`moeru-ai/xsai`），把 OpenAI、Claude、Gemini、Ollama、vLLM、SGLang、DeepSeek、Qwen、xAI、Groq、Mistral，以及智谱、SiliconFlow、Moonshot、MiniMax、腾讯云、ModelScope、小米 MiMo 等近 30 家提供商抽象成统一接口。README 清单共列 32 家，29 家已支持，AWS Claude、讯飞 Spark、火山引擎标注「PR welcome」。

AIRI 本身不绑定某个模型品牌，换提供商不需要改核心代码。虚拟角色对延迟、流式输出、函数调用、多模态输入的要求和普通聊天 API 不完全一致，xsAI 在统一接口之上补齐这些差异。

### 游戏代理能力

AI 角色被接进了真实的游戏运行时：

- **Minecraft**：通过 Mineflayer 把 LLM 生成的决策翻译成移动、攻击、放置方块等操作。Mineflayer 提供 Node.js 端的 Minecraft bot 协议实现，AIRI 之上再加一层「高层目标 → 动作序列」的翻译。
- **Factorio**：通过 RCON 和 `autorio`（airi-factorio 仓库内的 Factorio 自动化库）把高层目标拆成流水线执行步骤。官方仓库 `moeru-ai/airi-factorio` 提供 PoC 和 demo，另有 `factorio-rcon-api` 把无头服务器的控制台包成 REST API。
- **Dome Keeper**：更新的尝试。子项目 `game-playing-ai-dome-keeper` 配套了数据采集与训练管线，2026 年 2 月的开发日志记录了进展。

集成清单里还提到 MCP。官方拆出的 MCP Launcher 子项目是一个 MCP 服务器启动器，给角色接外部工具有了现成入口。

Neuro-sama 风格体验难复现的难点正在于此：LLM 生成文本容易，把文本决策可靠地映射到游戏世界状态很难。AIRI 的游戏链路是针对这层映射做的工程化封装。

### 语音与本地数据层

语音链路和本地数据层是一起设计的：

- **输入**：客户端侧 VAD（Voice Activity Detection）先判断是否在说话，再触发客户端侧 STT，避免一直上传静音片段。音频输入支持浏览器和 Discord。
- **输出**：多提供商 TTS，包括 ElevenLabs、Microsoft/Azure Speech、OpenAI-compatible TTS、阿里云 Model Studio，以及本地的 Kokoro TTS。
- **数据**：DuckDB WASM 或 `pglite` 提供纯浏览器端嵌入式数据库，配合记忆系统与 RAG 模块沉淀跨会话上下文。

语音链路管实时交互，数据层管跨会话记忆：VAD 抓到的一段音频，STT 转成文本后既要立刻交给 LLM 决定怎么说，也要按主题沉淀进 DuckDB，下次提到相关内容时由 RAG 捞出来注入上下文。这是 AIRI 能越聊越「记得你是谁」、而不是每次从零开始的来源。

---

## 任务流案例：一句「陪我玩 Minecraft」如何流过系统

假设用户对角色说「陪我玩 Minecraft」，大致流程如下：

1. **AI 链路入口**：本地 VAD 检测到语音活动，STT 把「陪我玩 Minecraft」转成文本，送入领域层。
2. **领域层调度**：core-agent 把文本连同当前屏幕状态、游戏服务器连接状态打包，通过 xsAI 调用配置好的 LLM，并附带系统提示词，告知当前可调用的工具（连接服务器、移动、攻击、说话等）。
3. **LLM 决策**：LLM 返回结构化决策，例如「连接到 Minecraft 服务器 → 走向玩家 → 说『我来了』」。决策以函数调用格式返回，便于解析路由。
4. **游戏链路执行**：决策经 server 通道路由到 minecraft-bot，Mineflayer 把「走向玩家」翻译成 bot 的寻路调用，bot 的坐标变化实时回传。
5. **渲染链路同步**：角色在 stage-ui 中播放对应的 Live2D/VRM 动作，TTS 把「我来了」合成为语音输出。动作触发与语音合成是异步的，避免互相阻塞。
6. **数据层沉淀**：这次交互被记忆系统记录摘要，写入 DuckDB WASM；下次进入游戏时，RAG 模块检索相关片段注入上下文，角色能回忆起「上次和玩家一起玩过」。

三条链路是并行触发的——LLM 在生成决策时，渲染层已经在准备动作动画，数据层在异步写入记忆。领域层的职责是协调这些并行任务的时序，避免 LLM 还没返回就触发动作、动作执行完才合成语音导致画面与声音不同步。

---

## 能力现状与边界

README 的 roadmap 把能力分成 Brain、Ears、Mouth、Body 四块：

| 模块 | 状态 |
|------|------|
| Brain（游戏） | Minecraft 已支持；Factorio WIP（有 PoC 和 demo）；Kerbal Space Program 打勾但公告 TBD；Helldivers 2 联机 WIP 未打勾 |
| Brain（通信） | Telegram、Discord 聊天已支持 |
| Brain（记忆） | DuckDB WASM / pglite 已支持；Memory Alaya 与纯浏览器端（WebGPU）本地推理未打勾 |
| Ears（听觉） | 浏览器与 Discord 音频输入、客户端侧语音识别与说话检测均完成 |
| Mouth（发声） | 多提供商 TTS 完成，含本地 Kokoro |
| Body（身体） | VRM 与 Live2D 支持、动画、自动眨眼、自动注视、待机眼动均完成 |

两点边界要注意：Factorio 和 Helldivers 2 仍是实验状态，游戏集成可能随版本更新变化；Memory Alaya 还没落地，当前跨会话记忆依赖摘要 + 检索，不是完整上下文保留。

---

## 生态与同类项目

开发过程中，AIRI 拆出了一串子项目，分布在 @proj-airi 与 moeru-ai 两个组织下：

- **unspeech**：ASR / TTS 的通用代理端点，定位类似 LiteLLM，但服务的是语音
- **xsai-transformers**：给 xsAI 接 Transformers.js 的实验性 provider
- **MCP Launcher**：MCP 服务器的启动器
- **Velin**：用 Vue SFC 和 Markdown 写有状态的 LLM 提示词
- **drizzle-duckdb-wasm / duckdb-wasm**：DuckDB WASM 的 ORM 驱动与易用封装
- **airi-factorio、game-playing-ai-dome-keeper**：游戏集成的独立仓库

这些拆分说明项目不止于一个应用，而是在长一条 AI vtuber 工具链。

README 列出的同类开源项目可作横向参照：kimjammer/Neuro（七天复刻 Neuro-sama，被官方评价为完成度很高）、z-waif（游戏与自主性强）、amica（VRM 与 WebXR）、elizaOS/eliza（agent 集成的工程范例）、Open-LLM-VTuber。想找替代方案时，这份清单是好的起点。

一个来自官方的提醒：项目没有任何官方发行的加密货币或代币，出现「AIRI 币」一律是假冒。

---

## 安装与快速开始

不需要从源码编译，有现成的安装入口：

- **Windows**：`winget install MoeruAI.AIRI`，或用 Scoop：

```powershell
scoop bucket add airi https://github.com/moeru-ai/airi
scoop install airi/airi
```

- **macOS**：`brew install --cask airi`
- **Linux**：GitHub Releases 提供 deb 安装包，开发环境也可用 Nix 运行 `nix run github:moeru-ai/airi`
- **Android / iOS**：Releases 附带 APK 与 IPA（实验性）
- **浏览器**：直接访问 airi.moeru.ai 在线试玩，无需安装

角色配置需要两类文件：Live2D（`.moc3` / `.model3.json`，2D 纸片人路线，社区资源丰富）或 VRM（`.vrm`，3D 路线，兼容 VRChat 等平台）。项目本身不提供模型文件，需要自己准备或购买。

---

## 常见问题

**Q: AIRI 能替代 Neuro-sama 吗？**
A: 不能。Neuro-sama 是商业闭源项目，有持续的直播互动和社区运营；AIRI 是开源复现方案，功能与体验上有差距，优势是完全自托管、数据本地化。

**Q: 需要什么硬件配置？**
A: 桌面端做本地推理需要支持 CUDA 或 Metal 的 GPU，显存需求随模型大小、序列长度和并发数变化，社区经验认为 8GB 以上更稳妥。浏览器端不走本地推理，模型调用发往远端 API，对本地硬件几乎没有要求，延迟取决于网络与服务商。

**Q: 能接入商业大模型吗？**
A: 可以。xsAI 支持近 30 家提供商（README 清单 32 家、29 家已支持），包括 OpenAI、Claude、Gemini、Ollama、vLLM 等，需要自己配置对应的 API Key。

**Q: 游戏代理能力稳定吗？**
A: 不稳定。Minecraft 和 Factorio 的集成是实验性的，游戏版本更新可能导致协议变化。建议只在本地单机世界测试，不要用在多人服务器上。

---

## 适用边界

**适合：**
- 有一定技术背景、想本地部署 AI 虚拟角色的用户
- 想要类似 Neuro-sama 体验、又不想依赖官方服务的用户
- 对 Live2D/VRM 角色格式有了解、愿意自己配置模型的开发者

**不适合：**
- 完全没有技术背景、想要开箱即用的普通用户（安装和配置模型都有门槛）
- 想直接用现成 3D 角色的人（模型需要自己准备）
- 期待功能与 Neuro-sama 完全一致的用户（开源复现与原版有差距）

## 采用建议

按以下顺序评估是否采用 AIRI：

1. **先验证模型接入**：在浏览器跑 Stage Web，配置一个已有 API Key 的 LLM，确认 xsAI 抽象层在你的提供商上工作正常。
2. **再验证角色渲染**：准备一个 Live2D 或 VRM 模型，确认 stage-ui 能正确加载并播放动作。
3. **最后验证游戏链路**：如果你关心 agent 能力，单独跑 Minecraft 集成，观察 Mineflayer 的动作执行稳定性。
4. **落地前评估数据层**：记忆系统和 RAG 模块在浏览器端的内存占用，需要单独压测。

前三步任何一步卡住，建议先暂停。AIRI 的价值在于三条链路协同，单链路跑通不等于整体可用。

---

## 资料口径说明

本文基于 AIRI 官方仓库（github.com/moeru-ai/airi）与其 README 撰写，核心数据经 GitHub API 于 2026-09-14 验证。需要说明的边界：

1. **版本时效性**：项目处于活跃开发阶段（当天仍有提交），Stage 策略、xsAI 接口、游戏链路支持可能随版本变化，请以官方仓库最新代码为准。
2. **发布通道**：GitHub Releases 当前为 v0.12.0-beta.5（beta 通道），winget、Homebrew 中的版本可能滞后；Android APK 与 iOS IPA 属实验性质。
3. **模型文件依赖**：AIRI 本身不含 Live2D / VRM 模型文件，需要用户自行准备。不同模型格式的动画支持程度不同，本文无法保证所有模型都能正常运行。
4. **硬件要求**：文中提到的显存数值（8GB 以上）为社区经验值，实际需求会因模型大小、序列长度、并发数而变化。
5. **游戏链路稳定性**：Minecraft 和 Factorio 的集成是实验性的，游戏版本更新可能导致协议变化，建议在本地单机世界测试。
6. **语音链路依赖**：本地 VAD/STT 的识别质量依赖所选方案，本文未逐一验证；TTS 的延迟与音质随服务而异。
7. **数据隐私**：本地部署时数据自持，但接入商业大模型 API 时，对话内容会发送到对应服务商，请依据各服务商的隐私政策评估。
