---
title: "OpenCut：用 Rust 重写的开源跨平台视频编辑器"
date: 2026-07-24T03:02:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Rust", "Open Source", "MCP"]
description: "一个从零开始重写的开源视频编辑器，目标是用 Rust 核心统一覆盖 Web、桌面和移动端，并原生支持 AI agent 通过 MCP 协议接入。"
slug: opencut-app-opencut-rust-cross-platform-video-editor
github_repo: "OpenCut-app/OpenCut"

---

## 项目定位

OpenCut 是一个免费开源的视频编辑器，目标是覆盖 Web、桌面和移动三个平台。项目目前正在**从零开始全面重写**——旧版本（opencut-classic）仍在线运行，新版本架构已经对外公布。

这个项目值得关注的理由不在当前的稳定版，而在于它的重写方向：**用 Rust 核心统一三端、把第三方插件作为一等公民、原生支持 AI agent 通过 MCP 接入**。它是少见的"为 AI agent 时代重新设计"的开源视频编辑工具。

## 重写方向：新架构是什么

OpenCut 的重写不是简单的代码重构，而是对"开源视频编辑器应该长什么样"的重新思考。README 中明确列出了新架构的六个关键特征：

| 特征 | 含义 |
|------|------|
| Editor API | 暴露编辑器内部能力，允许外部程序控制编辑流程 |
| 插件优先架构 | 第三方插件是一等公民，不再通过 hack 扩展 |
| Rust 核心 + 多平台前端 | 一套核心逻辑，Web/桌面/移动各自渲染 |
| MCP Server | AI agent 可以通过 Model Context Protocol 直接操作编辑器 |
| Headless 模式 | 无界面自动化渲染，支持批处理和流水线 |
| 编辑器内脚本面板 | 在编辑器内部直接写脚本控制时间线 |

这套架构的核心判断是：**视频编辑器的未来不是纯粹的 GUI 工具，而是可以被程序化和 agent 化操控的"渲染引擎 + 编辑 API"**。

其中的技术取舍值得拆开来看：

- **一套 Rust 核心，三端复用**。时间线、轨道、剪辑、特效渲染这些重逻辑只写一次，用同一份 Rust 代码同时支撑浏览器、桌面应用和移动端。Rust 的内存安全特性能显著减少传统 C++ 视频编辑器常见的崩溃问题，且天然适合编译到 WASM 以支撑 Web 端。
- **以"渲染引擎 + 编辑 API"为定位**。传统编辑器把操作封装在界面里，想自动化只能靠脚本模拟点击；OpenCut 则把"剪切、插入、添加特效、导出"每一步都暴露成接口。这样无论是脚本、云端流水线还是 AI agent，都能像调用库一样调用编辑器。
- **后端配套**。重写采用 monorepo 结构，除了前端还有独立的 API 服务器，为 Web 端和未来的协作、云端渲染预留入口。

## 与现有开源编辑器的差异

开源视频编辑器领域已经有不少选择，但它们大多沿用"C++/Qt + 桌面优先"的路线：

| 项目 | 核心语言 | 界面框架 | 定位 |
|------|----------|----------|------|
| DaVinci Resolve | 闭源核心 + 部分开源 | 自研 | 专业调色与后期，免费版功能强大 |
| Kdenlive | C++ | Qt，KDE 生态，底层 MLT | 桌面级非线性编辑 |
| Shotcut | C++ | Qt，底层 MLT | 跨平台桌面编辑 |
| Olive | C++ | Qt/QML | 桌面编辑，开发一度停滞 |
| OpenCut（重写中） | Rust | 多平台前端 | 三端统一 + AI agent |

OpenCut 的差异化体现在两个方向：

**技术栈选择**：用 Rust 作为核心语言。相对于 C++（DaVinci/Olive、Kdenlive/Shotcut 得益于 MLT）或桌面优先的 Qt 路线，Rust 在内存安全与 WASM 支持上更有优势，这直接决定了它能用一套核心覆盖浏览器端，而非局限于桌面。

**AI-native 设计**：内置 MCP Server，让 AI agent 可以读取时间线、执行剪切与添加特效、触发渲染。这不是"AI 辅助剪辑"的营销话术，而是把编辑器的每个操作都暴露为可编程接口。在 agent 快速发展的当下，这种设计让 OpenCut 有机会成为 agent 自动化视频制作的底层工具——例如批量生成短视频、按脚本自动剪辑、把渲染接入 CI 流水线。

## 开发状态与采用建议

README 中非常坦诚地说明了当前状态：

- **旧版本**（opencut-classic）：可以在 [opencut.app](https://opencut.app) 使用，是当前可用的版本
- **新版本**：正在开发中，预览地址 [new.opencut.app](https://new.opencut.app)，尚未正式开放对外代码贡献
- **协议**：MIT 许可证
- **赞助**：fal.ai 是当前赞助商

关键提醒：以上高级特性（Editor API、插件、MCP、headless）都属于**正在重写的新版本**，不是经典版已经具备的能力。经典版仍是传统桌面式编辑器。如果你是基于这些特性来判断是否采用，请务必确认发布进度，而非当前的稳定版。

### 开发工具链

重写采用 monorepo 加 [proto](https://moonrepo.dev/proto) 管理工具链、[moon](https://moonrepo.dev/moon) 作为构建系统：

```sh
proto use           # 安装 .prototools 中固定的工具链
moon run web:dev    # Web 端开发服务器 localhost:5173
moon run api:dev    # API 服务器 localhost:8787
moon run desktop:dev # 桌面端开发
```

端口配置体现了多端协同思路：Web 前端默认跑在 `5173`（Vite 默认端口），API 服务默认跑在 `8787`，桌面端则在自己目录下单独维护运行方式。

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
