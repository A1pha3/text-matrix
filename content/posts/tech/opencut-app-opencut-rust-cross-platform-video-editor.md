---
title: "OpenCut：用 Rust 重写的开源跨平台视频编辑器"
date: 2026-07-24T03:02:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Video Editor", "Rust", "Cross-Platform", "Open Source", "MCP"]
description: "一个从零开始重写的开源视频编辑器，目标是用 Rust 核心统一覆盖 Web、桌面和移动端，并原生支持 AI agent 通过 MCP 协议接入。"
---

## 项目定位

OpenCut 是一个免费开源的视频编辑器，覆盖 Web、桌面和移动三个平台。项目目前正在**从零开始全面重写**——旧版本（opencut-classic）仍在线运行，新版本架构设计已经公布。

这个项目值得关注的理由不在当前的稳定版，而在于它的重写方向：**用 Rust 核心统一渲染层、把插件作为一等公民、原生支持 AI agent 接入**。

## 重写方向：新架构是什么

OpenCut 的重写不是简单的代码重构，而是对"开源视频编辑器应该长什么样"的重新思考。README 中明确列出了新架构的关键特征：

| 特征 | 含义 |
|------|------|
| Editor API | 暴露编辑器内部能力，允许外部程序控制编辑流程 |
| 插件优先架构 | 第三方插件是一等公民，不再通过 hack 扩展 |
| Rust 核心 + 多平台前端 | 一套核心逻辑，Web/桌面/移动各自渲染 |
| MCP Server | AI agent 可以通过 Model Context Protocol 直接操作编辑器 |
| Headless 模式 | 无界面自动化渲染，支持批处理和流水线 |
| 编辑器内脚本面板 | 在编辑器内部直接写脚本控制时间线 |

这套架构的核心判断是：**视频编辑器的未来不是纯粹的 GUI 工具，而是可以被程序化和 agent 化操控的"渲染引擎 + 编辑API"**。

## 与现有方案的差异

开源视频编辑器领域已经有 DaVinci Resolve（部分开源）、Kdenlive、Olive 等选择。OpenCut 的差异化体现在两个方向：

**技术栈选择**：用 Rust 作为核心语言，而不是 C++（DaVinci/Olive）或 Python（Kdenlive 的部分逻辑）。这意味着内存安全、更少的崩溃风险，以及天然适合 WASM 编译以支持 Web 端。

**AI-native 设计**：MCP Server 的内置支持让 AI agent 可以直接操作时间线、添加特效、剪辑素材。这不是"AI 辅助"的营销话术，而是把编辑器的每个操作都暴露为可编程接口。在 AI agent 快速发展的当下，这种设计让 OpenCut 有可能成为 agent 自动化视频制作的底层工具。

## 开发状态与采用建议

README 中非常坦诚地说明了当前状态：

- **旧版本**（opencut-classic）：可以在 [opencut.app](https://opencut.app) 使用，是当前可用的版本
- **新版本**：正在开发中，预览地址 [new.opencut.app](https://new.opencut.app)，尚未对外接受代码贡献
- **协议**：MIT 许可证
- **赞助**：fal.ai 是当前赞助商

### 开发工具链

新版本使用 [proto](https://moonrepo.dev/proto) 管理工具链，[moon](https://moonrepo.dev/moon) 作为构建系统：

```sh
proto use           # 安装 .prototools 中固定的工具链
moon run web:dev    # Web 端开发服务器 localhost:5173
moon run api:dev    # API 服务器 localhost:8787
moon run desktop:dev # 桌面端开发
```

## 适用边界

**适合关注**：

- 关注开源视频工具发展方向的开发者
- 需要 headless 视频渲染能力的自动化流水线
- 想通过 AI agent 自动化视频制作的探索者
- 对 Rust 在多媒体领域应用感兴趣的技术人

**现阶段不适合**：

- 需要稳定可用的视频编辑器（当前经典版功能有限，新版仍在重写）
- 专业级后期制作（DaVinci Resolve 仍是更成熟的选择）
- 需要立即投入生产环境的团队

## 阅读路径

- [GitHub 仓库](https://github.com/OpenCut-app/OpenCut) — 源码和开发文档
- [opencut.app](https://opencut.app) — 在线试用经典版
- [Discord 社区](https://discord.gg/zmR9N35cjK) — 参与讨论
