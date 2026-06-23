+++
date = '2026-05-28T16:18:30+08:00'
draft = false
title = 'AIRI：自托管 AI 数字伴侣'
slug = 'airi-self-hosted-grok-companion-guide'
description = 'AIRI 是受 Neuro-sama 启发的开源项目，通过 Live2D/VRM 技术将 AI 虚拟角色带到桌面，支持 ChatGPT、Claude 等多款大模型，本地部署，数据完全自持。'
categories = ['技术笔记']
tags = ['AI', '开源', 'Live2D', '自托管']
+++

# AIRI：自托管 AI 数字伴侣

AIRI 是目前开源生态中对 Neuro-sama 复现最完整的项目（截至 2026 年 5 月，依据项目 README 与 moeru-ai 组织公开仓库）。它通过 Live2D/VRM 技术把 AI 虚拟角色带到桌面，支持 ChatGPT、Claude 等多款大模型，本地部署，数据完全自持。AIRI 的工程价值在于把渲染、AI、游戏三条链路收敛到同一调度框架，从而具备普通 AI 陪伴产品缺失的"实时感知 + 外部执行"能力。

---

## 系统总览

AIRI 的核心是三条并行链路在同一个调度框架内汇合：

| 链路 | 入口 | 关键依赖 | 出口 |
|------|------|----------|------|
| 渲染链路 | VRM / Live2D 模型 | Stage UI、WebGPU、Candle | 浏览器、桌面、移动端 |
| AI 链路 | LLM API | xsAI、Core | STT 输入、TTS 输出 |
| 游戏链路 | Minecraft / Factorio 服务器 | Mineflayer、RCON、`autorio` | agent 执行动作 |

三条链路通过 Core 调度层耦合：渲染链路决定角色如何被看见，AI 链路决定角色如何思考与说话，游戏链路决定角色如何对外部世界产生作用。AIRI 与普通"AI 角色壳子"的差异即在此——后者通常只覆盖前两条链路。

[AIRI](https://github.com/moeru-ai/airi) 出生于 moeru-ai 组织，定位是"数字灵魂容器"，目标是把 Neuro-sama 这类 AI vtuber 的交互体验带到普通用户手里。支持平台覆盖 Windows/macOS/Linux，底层依赖 Live2D 和 VRM 两种虚拟角色格式，后端有配套的 `@proj-airi` 组织提供 RAG（检索增强生成）、记忆系统、嵌入式数据库等模块。

Neuro-sama 是目前最知名的游戏+聊天双能力 AI vtuber，但属于商业闭源项目。AIRI 通过逆向其交互逻辑，在开源生态里给出了完整度较高的复现方案，具体体现在四个方面：多模态感知（能读取屏幕内容、分析用户当前操作，对话上下文不局限于文字输入）、多模型灵活切换（默认支持 ChatGPT/Claude，也可接入其他兼容 API 的模型）、完整角色生态（`@proj-airi` 组织持续输出 Live2D 工具、RAG 模块、记忆系统等周边组件）、完全自托管（数据留在本地，不经过任何第三方服务器）。

---

## 技术骨架

### 多端部署的三个 Stage

AIRI 的多端策略明确分成三个 stage，避免把同一套页面硬塞进不同壳子导致体验割裂：

- **Stage Web**：直接在浏览器里运行，承担"零安装体验"的入口角色，重点依赖 WebGPU、WebAssembly、WebAudio 和 WebSocket。选择 Web 技术栈是为了让用户首次接触时无需安装即可试用。
- **Stage Tamagotchi**：基于 Electron，推理层通过 HuggingFace Candle 走本地 CUDA / Metal 加速桌面端的实时交互。桌面端需要本地 GPU 算力支撑低延迟推理，Candle 在这里的角色是把 PyTorch 生态的模型权重直接搬到 Rust 运行时。
- **Stage Pocket**：通过 Capacitor 和 PWA 把 Web 代码封装到移动端，覆盖陪伴场景下更自然的入口。复用 Web 代码是为了避免维护两套 UI。

三个 stage 的分工对应不同的部署场景：浏览器端负责首次体验，桌面端负责持续运行时的低延迟推理，移动端负责陪伴场景的随身入口。

### xsAI：模型接入层的抽象

AIRI 的关键基础设施之一是 `xsAI`。它负责把 OpenAI、Claude、Gemini、Grok、Ollama、vLLM 等 20+ 模型提供商（依据项目 README 模型提供商列表）抽象成统一接口。

AIRI 本身不绑定某一个模型品牌。对使用者来说，换模型提供商不需要改核心代码；对开发者来说，这相当于一个面向虚拟角色场景的模型编排层。这种抽象之所以必要，是因为虚拟角色场景对延迟、流式输出、函数调用、多模态输入的要求与普通聊天 API 不完全一致，xsAI 在统一接口之上补齐了这些差异。

### 游戏代理能力

AIRI 把 AI 角色接进了真实的游戏运行时：

- **Minecraft**：通过 Mineflayer 把 LLM 生成的决策翻译成移动、攻击、放置方块等操作。Mineflayer 提供了 Node.js 端的 Minecraft bot 协议实现，AIRI 在其之上加了一层"高层目标 → 动作序列"的翻译层。
- **Factorio**：通过 RCON API 和 `autorio` 把高层目标拆成流水线执行步骤。RCON 是游戏服务器远程控制协议，`autorio` 负责把"建造一条铁板生产线"这类自然语言目标拆解为可执行的指令序列。

Neuro-sama 风格体验之所以难复现，难点即在于此——LLM 生成文本容易，把文本决策可靠地映射到游戏世界状态难。AIRI 的游戏链路正是针对这层映射做的工程化封装。

### 语音和本地数据层

AIRI 的语音链路和本地数据层是一起设计的，"陪伴感"能持续依赖于此：

- 语音输入侧有本地 VAD / STT，减少无效上传和延迟。VAD（Voice Activity Detection）先判断是否在说话，再决定是否触发 STT，避免一直上传静音片段。
- 语音输出侧可以把 LLM 回复回推到浏览器或 Discord 语音频道。
- 数据侧通过 DuckDB WASM、记忆系统和 RAG 模块，把长期上下文沉淀下来。DuckDB WASM 让浏览器端也能跑嵌入式 SQL，记忆系统负责跨会话的对话摘要与检索，RAG 模块负责外部知识注入。

语音链路负责实时交互，数据层负责跨会话记忆——两者结合让 AIRI 具备持续积累上下文的能力，而不仅仅是一次性对话演示。

---

## 任务流案例：一句"陪我玩 Minecraft"如何流过系统

假设用户对角色说"陪我玩 Minecraft"，系统的处理流程大致如下：

1. **AI 链路入口**：本地 VAD 检测到语音活动，STT 把"陪我玩 Minecraft"转成文本，送入 Core
2. **Core 调度**：Core 把文本连同当前屏幕状态、游戏服务器连接状态一起打包，通过 xsAI 调用配置好的 LLM。这里 Core 会附带系统提示词，告知 LLM 当前可调用的工具（连接服务器、移动、攻击、说话等）。
3. **LLM 决策**：LLM 返回结构化决策，例如"连接到 Minecraft 服务器 → 走向玩家 → 说'我来了'"。决策以函数调用格式返回，便于 Core 解析路由。
4. **游戏链路执行**：Core 把决策路由到 Minecraft agent，Mineflayer 把"走向玩家"翻译成 bot 的 pathfinding 调用。bot 的坐标变化会实时回写到 Core 的状态机。
5. **渲染链路同步**：角色在 Stage UI 中播放对应的 Live2D/VRM 动作，TTS 把"我来了"合成语音输出。动作触发与语音合成是异步的，避免互相阻塞。
6. **数据层沉淀**：这次交互被记忆系统记录摘要，下次进入游戏时角色能回忆起"上次和玩家一起玩过"。摘要写入 DuckDB WASM，RAG 模块在下次对话时检索相关片段注入上下文。

三条链路是并行触发的——LLM 在生成决策的同时，渲染层已经在准备动作动画，数据层在异步写入记忆。Core 的职责是协调这些并行任务的时序，避免 LLM 还没返回就触发动作执行，也避免动作执行完才合成语音导致画面与声音不同步。

---

## 安装与快速开始

### Windows 用户（推荐 Scoop）

```bash
scoop bucket add airi https://github.com/moeru-ai/airi
scoop install airi/airi
```

### macOS / Linux

项目 README 提供了 Docker 部署路径，适合有 Docker 环境的用户快速上手。

### 安装前提

- Node.js 18+（部分功能依赖）
- Live2D Cubism SDK（如果要用 Live2D 模型）
- VRM 模型文件（角色外观）

### 角色配置

项目支持两种主流虚拟角色格式：

| 格式 | 说明 |
|------|------|
| Live2D（.moc3/.model3.json） | 2D 纸片人路线，社区资源丰富 |
| VRM（.vrm） | 3D 模型路线，兼容 VRChat 等平台 |

---

## 核心模块与周边生态

AIRI 背后有一个专门的 `@proj-airi` 组织在维护子项目：

| 模块 | 用途 |
|------|------|
| RAG 模块 | 让 AI 能基于文档/知识库作答 |
| 记忆系统 | 持久化对话记忆，角色能记住之前聊过的事 |
| 嵌入式数据库 | 本地数据存储，不依赖云端 |
| Live2D 工具 | 角色动画相关工具链 |
| 图标库 | 角色 UI 相关的图标资源 |

模块化拆分让 AIRI 本身保持入口框架的角色，具体能力由周边模块组合而来。如果只需要其中某几个能力，可以单独引入对应模块。

---

## 适用边界

**适合：**
- 有一定技术背景，想本地部署 AI 虚拟角色的用户
- 想要类似 Neuro-sama 体验但不希望依赖官方服务的用户
- 对 Live2D/VRM 虚拟角色有一定了解，愿意自己配置模型的开发者

**不适合：**
- 完全没有技术背景、想要开箱即用的普通用户（安装步骤有一定门槛）
- 想用现成 3D 角色的用户（模型需要自己准备或购买）
- 期待功能与 Neuro-sama 完全一致的用户（开源复现与原版有差距）

---

## 采用建议

按以下顺序评估是否采用 AIRI：

1. **先验证模型接入**：本地跑 Stage Web，配置一个已有 API Key 的 LLM，确认 xsAI 抽象层在你的模型提供商上工作正常
2. **再验证角色渲染**：准备一个 Live2D 或 VRM 模型，确认 Stage UI 能正确加载并播放动作
3. **最后验证游戏链路**：如果你关心 agent 能力，单独跑 Minecraft 集成，观察 Mineflayer 的动作执行稳定性
4. **生产部署前**：评估记忆系统和 RAG 模块的存储占用，DuckDB WASM 在浏览器端的内存消耗需要单独压测

如果前三步有任何一步卡住，建议先暂停——AIRI 的价值在于三条链路协同，单链路跑通不等于整体可用。

想深入理解架构的读者，建议按以下顺序阅读源码：先看项目 README 了解整体架构，再进入 `@proj-airi` 组织页面了解周边模块能力，最后优先阅读 `xsAI`、游戏代理和语音链路几个子项目的实现。

---

## 相关项目

如果你对 AI vtuber 方向感兴趣，同期趋势榜上还有一些相关项目值得关注（Stars 数据截至 2026 年 5 月，可能已变化）：

- [taste-skill](https://github.com/Leonxlnx/taste-skill)（19.7k Stars）——给 AI 编程工具注入"品味"，减少机械感的 skill 文件
- [knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)（15.5k Stars）——Anthropic 官方的知识工作插件集

---

*如需了解 AIRI 的记忆系统实现原理，可以进一步阅读 `@proj-airi` 组织的 RAG 和 memory 相关模块源码。*
