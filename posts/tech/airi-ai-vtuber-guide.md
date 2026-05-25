---
title: "AIRI：开源 AI 虚拟陪伴与 VTuber 系统"
date: "2026-05-25T20:08:27+08:00"
slug: "airi-open-source-ai-vtuber-companion"
description: "AIRI 是一个开源的 AI 虚拟角色陪伴系统，目标是复现 Neuro-sama 的效果。支持实时语音对话、Minecraft 和 Factorio 游戏互动、VRM 虚拟形象。本文解析其架构和功能。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "VTuber", "VRM", "Live2D", "开源", "语音交互"]
---

# AIRI：开源 AI 虚拟陪伴与 VTuber 系统

AIRI 是一个开源项目，旨在创建一个"AI 灵魂容器"——将二次元角色、数字生命带入现实世界。项目对标的是 Virtual YouTuber Neuro-sama，目标是通过 AI 技术让虚拟角色具备实时对话、游戏互动等能力。目前获得 39,553 颗 Stars，架构基于 TypeScript，支持 Web、macOS 和 Windows。

## 核心定位

AIRI 的定位是一个**自托管的 AI 陪伴系统**，用户可以完全控制自己的虚拟角色和数据。与 Character.ai、Poe 等商业平台不同，AIRI 强调"you-owned"——你的角色、对话数据、行为记忆都保存在本地。

主要特性：

- 实时语音对话（Voice Chat）
- 游戏互动能力（Minecraft、Factorio）
- VRM 虚拟形象支持
- Live2D 动画支持
- 跨平台桌面客户端（Web / macOS / Windows）

## 系统架构

AIRI 的技术栈以 TypeScript 为核心，核心模块包括：

| 模块 | 职责 |
|------|------|
| WebUI | 用户界面，角色交互入口 |
| Voice Engine | 语音识别与合成，处理实时音频 |
| LLM Backend | 连接大语言模型（支持多种 Provider） |
| Game Bridge | 与游戏进程通信，发送指令和读取状态 |
| VRM/Live2D Renderer | 虚拟形象渲染和动画驱动 |

架构上，AIRI 采用了插件化设计，游戏支持和虚拟形象渲染均为可插拔模块。这种设计允许用户在不改变核心逻辑的前提下扩展新的游戏支持或虚拟形象格式。

## 虚拟形象

AIRI 支持两种虚拟形象格式：

1. **VRM**：行业标准的 3D 虚拟形象格式，支持骨骼动画和表情系统
2. **Live2D**：2D 层次动画方案，适合静态插图驱动的角色

用户可以使用现成的 VRM 模型，也可以自己制作或购买。官方和社区提供了一些预制模型的下载链接。

## 游戏集成

目前 AIRI 重点支持两款游戏：

- **Minecraft**：通过 Mineflayer 或类似桥接方案，让 AI 可以感知游戏世界状态、发送指令、与玩家协作
- **Factorio**：类似地，AI 可以读取工厂状态、规划布局、执行建造指令

游戏集成是 AIRI 的差异化能力所在，也是最复杂的部分——需要处理游戏状态同步、异步指令队列和错误恢复。

## 部署方式

官方提供编译好的二进制文件，覆盖 Windows 和 macOS（Apple Silicon）平台：

```bash
# Windows 下载
# https://github.com/moeru-ai/airi/releases/download/v0.10.2/AIRI-0.10.2-windows-x64-setup.exe

# macOS 下载
# https://github.com/moeru-ai/airi/releases/download/v0.10.2/AIRI-0.10.2-darwin-arm64.dmg
```

也可以通过源码构建：

```bash
git clone https://github.com/moeru-ai/airi.git
cd airi
pnpm install
pnpm run build
```

## 与 Neuro-sama 的关系

AIRI 明确表示目标是从工程层面复现 Neuro-sama 的体验，而非使用 Neuro-sama 的模型或内容。Neuro-sama 的核心技术细节并未开源，AIRI 是社区自发用开源技术栈重新构建的类似方案。

## 适用场景

- 想拥有自己 AI 角色的个人用户
- 二次元爱好者的本地化虚拟陪伴
- 研究 AI + 游戏互动的开发者
- 寻找 Live2D/VRM 集成方案的技术团队

---

*本文档基于 GitHub 仓库 2026 年 5 月最新信息编写，Stars：39,553，License：MIT。*