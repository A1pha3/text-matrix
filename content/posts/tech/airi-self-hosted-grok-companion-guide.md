---
title: "AIRI：自托管 GROK 数字伴侣，把 Neuro-sama 接回家"
date: 2026-05-26T09:35:00+08:00
slug: "airi-self-hosted-grok-companion-guide"
description: "AIRI 是受 Neuro-sama 启发诞生的开源项目，通过 Live2D/VRM 技术将 AI 虚拟角色带入现实世界，支持 ChatGPT、Claude 等多款大模型，可本地部署，数据完全自持，适合想拥有专属数字伴侣的用户。"
draft: false
categories: ["技术笔记"]
tags: ["AI Companion", "VRM", "Live2D", "Virtual Character", "Neuro-sama", "开源"]
---

# AIRI：自托管 GROK 数字伴侣，把 Neuro-sama 接回家

**一句话判断：AIRI 是目前开源生态中对 Neuro-sama 复现最完整的项目，适合有一定技术背景、想自托管 AI 虚拟伴侣的用户。**

---

## 项目概览

[AIRI](https://github.com/moeru-ai/airi)（39.7k Stars）出生于 moeru-ai 组织，定位是"数字灵魂容器"——把 Neuro-sama 这类 AI vtuber 的交互体验带到普通用户手里。

支持平台覆盖 Windows/macOS/Linux，底层依赖 Live2D 和 VRM 两种虚拟角色格式，对话引擎可以接 ChatGPT、Claude 等主流大模型，后端有配套的 `@proj-airi` 组织提供 RAG（检索增强生成）、记忆系统、嵌入式数据库等模块。

核心能力一句话：让 AI 虚拟角色同时具备"看见屏幕内容"和"与用户玩游戏/聊天"的能力，而不是只能打字回复。

---

## 为什么值得看

Neuro-sama 是目前最知名的游戏+聊天双能力 AI vtuber，但她是商业闭源项目。AIRI 通过逆向其交互逻辑，在开源生态里给出了最完整的复现方案：

- **多模态感知**：不只是聊天，还能读取屏幕内容、分析你在做什么
- **多模型灵活切换**：默认支持 ChatGPT/Claude，也可以接入其他兼容 API 的模型
- **完整角色生态**：背后有专门的 `@proj-airi` 组织持续输出 Live2D 工具、RAG 模块、记忆系统等周边组件
- **完全自托管**：数据留在本地，不需要经过任何第三方服务器

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

---

## 相关项目

如果你对 AI vtuber 方向感兴趣，同期趋势榜上还有一些相关项目值得关注：

- [taste-skill](https://github.com/Leonxlnx/taste-skill)（19.7k Stars）——给 AI 编程工具注入"品味"，减少机械感的 skill 文件
- [knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)（15.5k Stars）——Anthropic 官方的知识工作插件集

---

*如需了解 AIRI 的记忆系统实现原理，可以进一步阅读 `@proj-airi` 组织的 RAG 和 memory 相关模块源码。*