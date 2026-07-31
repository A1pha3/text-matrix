---
title: "T3 Code：Theo 的 Agent 控制台，远程驾驭 Claude Code 与 Codex"
date: 2026-08-01T02:54:21+08:00
draft: false
categories: ["技术笔记"]
tags: ["T3 Code", "Agent", "Claude Code", "Codex", "Cursor", "远程开发"]
description: "T3 Code 是 Theo（pingdotgg）开发的 AI 编程 agent 控制台，提供 iOS/Android/Web/桌面四端客户端，统一管理本机的 Claude Code、Codex、Cursor、Grok Build 和 OpenCode agent，支持远程操控编码任务。"
---

## 一句话判断

T3 Code 解决的核心问题是：AI 编程 agent（Claude Code、Codex 等）都跑在你的电脑上，但你不想一直坐在电脑前盯着终端。T3 Code 给这些 agent 加了一层远程控制界面——手机、浏览器或桌面应用都能操控，agent 还在你机器上跑。

## 项目概览

| 维度 | 数据 |
|------|------|
| 仓库 | pingdotgg/t3code |
| Stars | ~16,000 |
| 语言 | TypeScript |
| 许可证 | MIT |
| 作者 | Theo Browne（pingdotgg） |

T3 Code 自称是 "agent harness control surface"——agent 线束控制面板。它不替代 Claude Code 或 Codex，而是在它们之上加一层 UI 和远程访问能力。

## 支持的 Agent

T3 Code 目前支持五种 agent 后端，前提是它们已在本机安装并认证：

| Agent | 认证命令 |
|-------|----------|
| Claude Code | `claude auth login` |
| Codex | `codex login` |
| Cursor | `agent login` |
| Grok Build | `grok login` |
| OpenCode | `opencode auth login` |

如果这些 agent 在你电脑上能正常跑，T3 Code 就能接管它们。

## 四端客户端

T3 Code 提供四种使用方式：

1. **iOS App**：App Store 上架
2. **Android App**：Google Play 上架
3. **Web App**：[app.t3.codes](https://app.t3.codes)，浏览器直接用
4. **桌面 App**：Electron，GitHub Releases 下载

最快体验方式无需安装——只要 Node.js 22.16+：

```bash
npx t3@latest
```

这会在本机启动 T3 Code 后端和本地 Web 应用。

### 桌面安装

```bash
# Windows
winget install T3Tools.T3Code

# macOS
brew install --cask t3-code

# Arch Linux
yay -S t3code-bin
```

## 核心价值：远程访问

T3 Code 最实用的场景是**远程控制**。你在公司电脑上跑着 Claude Code 处理一个大重构，然后出门 lunch。手机上打开 T3 Code App，查看 agent 进度，发消息指导方向，回来时代码已经改好了。

这是传统终端 agent 做不到的——你被绑在键盘前。T3 Code 把这个约束解掉了。

项目文档特别强调了几个能力：

- **权限模式**：控制 agent 能做什么、不能做什么
- **源码控制集成**：agent 的代码变更可追踪
- **多账号**：支持同时使用多个 Codex 或 Claude 账号
- **键盘快捷键**：完整的键绑定体系
- **Linux 后台服务**：可作为 systemd 服务运行

## 技术判断

T3 Code 的技术选择反映了几层思考：

**不做 agent，做 agent 的壳**。T3 Code 不自己跑模型、不自己做代码生成。它假设你已经有了 Claude Code 或 Codex 的订阅和认证，它只负责提供更好的操控界面。这意味着 T3 Code 的成功与 agent 生态深度绑定。

**TypeScript + Electron + React Native（推测）**。四端覆盖的技术代价是 Electron 桌面 + Web + 移动原生，这对小团队来说是合理的快速覆盖策略。

**开源但不接受大贡献**。README 明确说"mostly not accepting contributions yet"——小修复可能考虑，大功能不接受。这更像是一个产品团队的开源发布，而非社区项目。

**Vite+ 构建**。项目使用了 Vite+（vp）作为构建工具，需要全局安装 `vp` CLI。这是较新的工具链选择。

## 快速上手

```bash
# 最简方式（需 Node.js 22.16+/23.11+/24.10+）
npx t3@latest

# 查看完整 CLI 选项
npx t3@latest --help
```

桌面用户安装后直接启动即可。默认连接本机的 agent 后端。

远程访问配置参见 [docs/user/remote-access.md](https://github.com/pingdotgg/t3code/blob/main/docs/user/remote-access.md)。

## 适用边界

**适合**：

- 已经在用 Claude Code / Codex / Cursor agent 的开发者
- 需要远程监控和指导 agent 工作的场景
- 希望用手机或平板控制电脑上编码 agent 的用户
- 同时使用多种 agent 后端的团队

**不适合**：

- 没有 agent 订阅的用户（T3 Code 不提供 agent 能力本身）
- 需要深度定制的团队（项目当前不接受大功能贡献）
- 对 Electron 应用有性能顾虑的场景

## 相关链接

- 仓库：[github.com/pingdotgg/t3code](https://github.com/pingdotgg/t3code)
- Web App：[app.t3.codes](https://app.t3.codes)
- iOS：[App Store](https://apps.apple.com/us/app/t3-code-remote-claude-more/id6787819824)
- Android：[Google Play](https://play.google.com/store/apps/details?id=com.t3tools.t3code)
- Discord：[discord.gg/jn4EGJjrvv](https://discord.gg/jn4EGJjrvv)
