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

AIRI 是目前开源生态中对 Neuro-sama 复现最完整的项目——通过 Live2D/VRM 技术将 AI 虚拟角色带到桌面，支持 ChatGPT、Claude 等多款大模型，本地部署，数据完全自持。

---

## 项目概览

[AIRI](https://github.com/moeru-ai/airi) 出生于 moeru-ai 组织，定位是"数字灵魂容器"——把 Neuro-sama 这类 AI vtuber 的交互体验带到普通用户手里。

支持平台覆盖 Windows/macOS/Linux，底层依赖 Live2D 和 VRM 两种虚拟角色格式，对话引擎可以接 ChatGPT、Claude 等主流大模型，后端有配套的 `@proj-airi` 组织提供 RAG（检索增强生成）、记忆系统、嵌入式数据库等模块。

AIRI 让 AI 虚拟角色同时具备"看见屏幕内容"和"与用户玩游戏/聊天"的能力，而不是只能打字回复。

如果把 AIRI 拆开看，它其实是三条链路在同一个调度框架里的汇合：

- **渲染链路**：VRM / Live2D 模型 → Stage UI → 浏览器、桌面、移动端
- **AI 链路**：LLM API → xsAI → Core → STT / TTS
- **游戏链路**：Minecraft / Factorio 等游戏服务器 → Server Runtime → agent 执行

这也是它和大多数"AI 角色壳子"的根本差异：AIRI 更像一个虚拟存在平台，而不是一个只会聊天的前端界面。

---

## 为什么值得看

Neuro-sama 是目前最知名的游戏+聊天双能力 AI vtuber，但她是商业闭源项目。AIRI 通过逆向其交互逻辑，在开源生态里给出了最完整的复现方案：

- **多模态感知**：不只是聊天，还能读取屏幕内容、分析你在做什么
- **多模型灵活切换**：默认支持 ChatGPT/Claude，也可以接入其他兼容 API 的模型
- **完整角色生态**：背后有专门的 `@proj-airi` 组织持续输出 Live2D 工具、RAG 模块、记忆系统等周边组件
- **完全自托管**：数据留在本地，不需要经过任何第三方服务器

---

## 技术骨架

### 多端部署不是简单套壳

AIRI 的多端策略不是把同一套页面硬塞进不同壳子里，而是明确分成三个 stage：

- **Stage Web**：直接在浏览器里运行，承担"零安装体验"的入口角色，重点依赖 WebGPU、WebAssembly、WebAudio 和 WebSocket
- **Stage Tamagotchi**：基于 Electron，但推理层通过 HuggingFace Candle 走本地 CUDA / Metal，加速桌面端的实时交互
- **Stage Pocket**：通过 Capacitor 和 PWA 把 Web 代码封装到移动端，覆盖陪伴场景下更自然的入口

这套设计的价值在于：同样是 Web 技术栈，AIRI 一头保留了浏览器的部署灵活性，一头又把桌面端的本地 GPU 能力吃了进去。

### xsAI 把模型接入层抽象掉

正式 README 更偏向产品介绍，但从工程角度看，AIRI 的关键基础设施之一其实是 `xsAI`。它负责把 OpenAI、Claude、Gemini、Grok、Ollama、vLLM 等 20+ 模型提供商抽象成统一接口。

这意味着 AIRI 本身不绑定某一个模型品牌。对使用者来说，换模型提供商不需要改核心代码；对开发者来说，这更像一个面向虚拟角色场景的模型编排层，而不是某个单模型应用。

### 游戏代理能力才是它和普通 AI 陪伴产品拉开差距的地方

AIRI 不只是能聊天。它已经把 AI 角色接进了真实的游戏运行时：

- **Minecraft**：通过 Mineflayer 把 LLM 生成的决策翻译成移动、攻击、放置方块等操作
- **Factorio**：通过 RCON API 和 `autorio` 把高层目标拆成流水线执行步骤

这说明 AIRI 的核心不是"会说话的数字人"，而是一个把 LLM、实时状态感知和外部执行环境连成闭环的 agent 框架。Neuro-sama 风格体验之所以难复现，难点也恰恰在这里。

### 语音和本地数据层补齐了"陪伴感"

旧稿里还有一个正式稿没展开的重要点：AIRI 的语音链路和本地数据层是一起设计的。

- 语音输入侧有本地 VAD / STT，减少无效上传和延迟
- 语音输出侧可以把 LLM 回复回推到浏览器或 Discord 语音频道
- 数据侧则通过 DuckDB WASM、记忆系统和 RAG 模块，把长期上下文沉淀下来

这让 AIRI 不只是一次性的对话演示，而更接近一个能持续积累记忆、跨场景存在的数字伴侣系统。

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

这种模块化拆分的思路意味着：AIRI 本身更像是一个入口框架，具体能力由周边模块组合而来。如果你只需要其中某几个能力，可以单独引入对应模块。

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

## 阅读路径

1. 先看项目 README，了解整体架构
2. 进入 `@proj-airi` 组织页面，了解周边模块能力
3. 根据自己的系统（Windows/macOS/Linux）选择对应安装方式
4. 准备一个 Live2D 或 VRM 角色模型
5. 配置大模型 API Key，开始体验
6. 如果你更关心架构而不是体验，优先看 `xsAI`、游戏代理和语音链路几个子项目

---

## 相关项目

如果你对 AI vtuber 方向感兴趣，同期趋势榜上还有一些相关项目值得关注：

- [taste-skill](https://github.com/Leonxlnx/taste-skill)（19.7k Stars）——给 AI 编程工具注入"品味"，减少机械感的 skill 文件
- [knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)（15.5k Stars）——Anthropic 官方的知识工作插件集

---

*如需了解 AIRI 的记忆系统实现原理，可以进一步阅读 `@proj-airi` 组织的 RAG 和 memory 相关模块源码。*