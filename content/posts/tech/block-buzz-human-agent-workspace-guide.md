---
title: "Buzz：Block 开源的人机协作工作空间"
date: 2026-08-01T02:54:21+08:00
draft: false
categories: ["技术笔记"]
tags: ["Buzz", "Block", "Nostr", "AI Agent", "Rust", "人机协作"]
description: "Buzz 是 Block（Square）开源的自托管工作空间，将人类与 AI agent 放在同一个频道里协作。底层是 Nostr relay，每条消息、反应、工作流步骤都是签名事件，人和 agent 共享同一套身份模型和审计链。"
slug: block-buzz-human-agent-workspace-guide
github_repo: "block/buzz"

---

## 一句话判断

Buzz 的核心赌注是：一个社区、一套身份模型、一条事件日志，可以替代团队目前用聊天工具、代码托管、Bot、CI 面板、发布工具和搜索索引拼凑出来的协作体系。agent 不是外挂的 cron job，而是频道里有自己密钥和审计轨迹的正式成员。

## 项目概览

| 维度 | 数据 |
|------|------|
| 仓库 | block/buzz |
| Stars | ~19,200 |
| 语言 | Rust |
| 许可证 | Apache-2.0 |
| 背景 | Block（原 Square）出品 |

Buzz 是一个可自托管的工作空间，人类和 AI agent 在同一个房间里工作。一个 Buzz **社区（community）**就是用户通过 URL 访问的工作区。在当前的单 relay 部署模式下，relay URL 唯一确定一个社区。

它不是一个聊天工具加 AI 插件，而是一个以 Nostr relay 为底座的统一协作平台。

## 架构核心：Nostr Relay 作为事件日志

Buzz 的技术基础是 **Nostr relay**——每条消息、反应、工作流步骤、代码审查批准和 git 事件都是一条签名事件（signed event）。人与 process 使用相同的事件结构、相同的身份模型、相同的审计链。

这意味着：

- **可审计**：每个操作都有密码学签名，谁做了什么一目了然
- **可搜索**：因为所有内容都是同一种事件格式，搜索可以跨消息、补丁、工作流和审批
- **身份一致**：agent 和人类用同一种方式被 scope——靠身份而非权限标志位

Buzz 的设计哲学是"agent 是成员，不是 bot"。将 agent 加入频道的方式和加入一个人一样，agent 拥有自己的密钥对、自己的频道成员身份和自己的审计轨迹。

## 实际使用场景

项目 README 描述了三个典型工作流：

### 1. 事故记忆（Incident Memory）

凌晨 2 点，你问"我们之前见过这个错误吗？"频道中的 agent 检索六个月的历史，返回相关讨论串、根因和修复方案，并主动提出是否要通知当初提交修复的人。整个交互——问题、答案、证据——都留在频道里。

### 2. 分支即房间（Branch as Room）

你开一个 feature 分支，自动出现一个频道。补丁以 NIP-34 事件形式提交，CI 结果发到频道里，agent 做首轮代码审查，同事对关心的部分发表情回应，合并决定和证据都在同一个房间。

### 3. 自动化发布（Release That Writes Itself）

工作流在 git tag 时触发。agent 从项目频道中读取已合并的 PR，起草发布说明，提交人工审查。人类 reviewer 回一个 👍，agent 发布。每一步都有签名，每一步都可搜索。

## 功能成熟度

README 将功能分为三档：

| 状态 | 功能 |
|------|------|
| ✅ 可用 | Relay、频道、线程、私信、画布（canvas）、媒体、搜索、审计日志 |
| ✅ 可用 | 桌面客户端（Tauri + React） |
| ✅ 可用 | `buzz-cli`（agent 优先，JSON 输入/输出）+ ACP 适配器（Goose、Codex、Claude Code） |
| ✅ 可用 | YAML 工作流（消息/反应/定时/webhook 触发器） |
| ✅ 可用 | Git 事件（NIP-34：补丁、仓库公告、状态） |
| ✅ 可用 | Git 托管后端 |
| 🚧 开发中 | 移动客户端（iOS + Android，Flutter） |
| 🚧 开发中 | 工作流审批门控（基础设施已有，胶水代码仍在完善） |
| 💭 规划中 | 跨 relay 的信任网络（Web-of-trust reputation） |
| 💭 规划中 | 推送通知 |

## 部署方式

### 下载预编译版本

从 [GitHub Releases](https://github.com/block/buzz/releases/latest) 获取 macOS（.dmg）、Linux（.AppImage / .deb）或 Windows（.exe）安装包。默认连接 `ws://localhost:3000`。

### 从源码构建

依赖 Docker 和 Hermit（或 Rust 1.88+、Node 24+、pnpm 10+、just）：

```bash
git clone https://github.com/block/buzz.git && cd buzz
. ./bin/activate-hermit   # 锁定工具链版本
just setup && just build
```

`just setup` 会自动复制 `.env.example` 到 `.env`，下载所需工具，启动 Docker 服务和数据库迁移。

日常开发：

```bash
. ./bin/activate-hermit
just dev    # 启动开发服务器
```

### Block 内部用户

Block 员工有预配置的内部版本，连接 Block relay 和 agent provider，无需自行配置。

## 技术判断

Buzz 的架构选择值得深思的几个点：

**Nostr 作为协作底座**。大多数团队协作工具用数据库表结构建模实体（消息、PR、CI run），用 API 定义操作。Buzz 把所有东西都变成 Nostr 事件——统一的格式、统一的签名、统一的检索。这意味着扩展新功能时不需要设计新表和新 API，只需要定义新的事件类型（NIP）。

**Agent 一等公民**。agent 不是通过 webhook 或 API token 接入的外部系统，而是拥有自己 Nostr 密钥的频道成员。这让 agent 的操作天然受限于身份 scope，而不是中心化的权限管理。

**单社区语义边界**。在默认自托管部署中，一个 relay 托管一个社区。在多租户托管部署中，每个社区仍保持语义隔离，即使后端共享 Postgres、Redis 和对象存储。

风险方面：

- 项目明确标注"非常早期，预期有 bug"
- 目前**不接受大功能贡献**，仅考虑小修复
- 移动端尚未交付，桌面端是唯一完整客户端
- Nostr relay 作为协作底座的方案尚未被大规模验证

## 适用边界

**适合**：

- 希望将 AI agent 深度集成到开发工作流的团队
- 对数据自主性和审计有强需求的组织
- 对 Nostr 协议和事件驱动架构有技术兴趣的工程师
- Block 内部团队（有预配置版本）

**不适合**：

- 需要成熟稳定的生产级协作平台
- 依赖丰富第三方集成的团队（当前生态有限）
- 非技术团队（界面和概念对非技术用户偏重）

## 相关链接

- 仓库：[github.com/block/buzz](https://github.com/block/buzz)
- 架构文档：仓库内 ARCHITECTURE.md
- 愿景文档：仓库内 VISION.md / VISION_SOVEREIGN.md / VISION_AGENT.md
