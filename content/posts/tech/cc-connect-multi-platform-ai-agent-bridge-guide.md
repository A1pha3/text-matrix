---
title: "CC-Connect：将AI coding agent连接到任意聊天平台"
date: "2026-04-12T02:31:39+08:00"
slug: cc-connect-multi-platform-ai-agent-bridge-guide
description: "CC-Connect 是一个将 AI coding agent 连接到多种聊天平台的工具，支持 Telegram、Discord、Slack 等平台。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "Agent", "Telegram", "Discord", "Slack"]
---

# CC-Connect：将AI coding agent连接到任意聊天平台

## 一、项目概述

### 1.1 CC-Connect 是什么

**CC-Connect** 是一个开源的**AI Agent桥接器**，让你的本地AI编程助手（Claude Code、Cursor Agent、Gemini CLI等）连接到常用的聊天平台（飞书、Telegram、Discord、Slack、微信等），随时随地通过手机或平板与AI助手对话。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | 5.3k ⭐ |
| Forks | 480 |
| 最新版本 | v1.2.1 (2026-03-09) |
| 许可证 | MIT |
| 语言 | Go 91.9%, TypeScript 7.3% |
| 贡献者 | 50 |
| Commits | 629 |

### 1.3 为什么选择 CC-Connect

| 特点 | 说明 |
|------|------|
| 🤖 多Agent支持 | Claude Code、Codex、Cursor Agent、Gemini CLI 等 7 种 |
| 📱 多平台支持 | 飞书、Telegram、Discord、Slack、微信等 10 个平台 |
| 🛡️ 无需公网IP | 大部分平台 WebSocket 长连接，无需公网IP |
| ⚡ 实时响应 | 流式输出，Markdown/卡片消息 |
| 🔄 多Bot协作 | 群聊中多个Bot互相通信 |
| 💬 自然语言控制 | /model、/dir、/cron 等 Slash 命令 |

---

## 二、技术架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    CC-Connect                                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │  Feishu   │  │  DingTalk  │  │  Telegram  │           │
│  │  WebSocket │  │   Stream   │  │Long Polling│           │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘           │
│         └────────────────┼────────────────┘              │
│                          ▼                                    │
│  ┌─────────────────────────────────────────────────┐     │
│  │              Core Engine (Go)                      │     │
│  │  • Session Management                            │     │
│  │  • Slash Command Router                         │     │
│  │  • Agent Adapter (ACP Protocol)                 │     │
│  │  • OS-User Isolation                            │     │
│  │  • Cron Scheduler                               │     │
│  └──────────────────────┬──────────────────────────┘     │
│                         ▼                                   │
│  ┌─────────────────────────────────────────────────┐     │
│  │              AI Agents                             │     │
│  │  Claude Code │ Codex │ Cursor │ Gemini │ ...     │     │
│  └─────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 支持的AI Agent（7种）

| Agent | 状态 | 说明 |
|-------|------|------|
| **Claude Code** | ✅ 稳定 | Anthropic官方CLI |
| **Codex** | ✅ 稳定 | OpenAI官方CLI |
| **Cursor Agent** | ✅ 稳定 | Cursor IDE内置 |
| **Gemini CLI** | ✅ 稳定 | Google官方CLI |
| **Qoder CLI** | ✅ 稳定 | Qoder CLI |
| **OpenCode** | ✅ 稳定 | Crush/OpenCode |
| **iFlow CLI** | ✅ 稳定 | iFlow CLI |
| **Goose** | 🔜 计划中 | Block官方 |
| **Aider** | 🔜 计划中 | Aider |

### 2.3 支持的聊天平台（10个）

| 平台 | 连接方式 | 公网IP需求 | 状态 |
|------|----------|------------|------|
| **飞书** | WebSocket | ❌ 不需要 | ✅ 稳定 |
| **钉钉** | Stream | ❌ 不需要 | ✅ 稳定 |
| **Telegram** | Long Polling | ❌ 不需要 | ✅ 稳定 |
| **Slack** | Socket Mode | ❌ 不需要 | ✅ 稳定 |
| **Discord** | Gateway | ❌ 不需要 | ✅ 稳定 |
| **LINE** | Webhook | ⚠️ 需要 | ✅ 稳定 |
| **企业微信** | WebSocket/Webhook | ⚠️ WS不需要 | ✅ 稳定 |
| **微信（个人）** | HTTP长轮询 | ❌ 不需要 | ✅ Beta |
| **QQ (NapCat)** | WebSocket | ❌ 不需要 | ✅ Beta |
| **QQ Bot (官方)** | WebSocket | ❌ 不需要 | ✅ 稳定 |

---

## 三、快速开始

### 3.1 一键AI安装（推荐）

将以下内容发给 Claude Code，它会自动完成整个安装和配置：

```bash
Follow https://raw.githubusercontent.com/chenhg5/cc-connect/refs/heads/main/INSTALL.md to install and configure cc-connect.
```

### 3.2 手动安装

**npm 安装：**

```bash
# 稳定版
npm install -g cc-connect

# Beta版（更多功能，可能不稳定）
npm install -g cc-connect@beta
```

**二进制下载：**

```bash
# Linux amd64
curl -L -o cc-connect https://github.com/chenhg5/cc-connect/releases/latest/download/cc-connect-linux-amd64
chmod +x cc-connect
sudo mv cc-connect /usr/local/bin/
```

**源码编译（需要 Go 1.22+）：**

```bash
git clone https://github.com/chenhg5/cc-connect.git
cd cc-connect
make build
```

### 3.3 配置

```bash
mkdir -p ~/.cc-connect
cp config.example.toml ~/.cc-connect/config.toml
vim ~/.cc-connect/config.toml
```

**配置示例（config.toml）：**

```toml
[projects.claude]
agent = "claude-code"
platform = "feishu"
admin_from = "alice,bob"  # 允许执行特权命令的用户

[platforms.feishu]
app_id = "cli_xxxxxxxx"
app_secret = "xxxxxxxxxxxxxxxx"
```

### 3.4 运行

```bash
./cc-connect
```

---

## 四、核心功能详解

### 4.1 Slash 命令系统

| 命令 | 功能 | 示例 |
|------|------|------|
| `/new [name]` | 开启新会话 | `/new debug-session` |
| `/list` | 列出所有会话 | `/list` |
| `/switch <id>` | 切换会话 | `/switch abc123` |
| `/current` | 显示当前会话 | `/current` |
| `/dir [path]` | 切换工作目录 | `/dir /project/src` |
| `/model` | 列出可用模型 | `/model` |
| `/model switch <alias>` | 切换模型 | `/model switch claude-sonnet` |
| `/mode` | 显示权限模式 | `/mode` |
| `/mode yolo` | 自动批准所有工具 | `/mode yolo` |
| `/mode default` | 询问每个工具 | `/mode default` |
| `/cron add <cron> <cmd>` | 添加定时任务 | `/cron add 0 6 * * * Summarize GitHub trending` |
| `/provider list` | 列出提供商 | `/provider list` |
| `/provider switch <name>` | 切换提供商 | `/provider switch openai` |

### 4.2 多会话管理

```bash
# 列出所有会话
/list

# 输出示例：
# 1. debug-session (active)
# 2. refactor-auth
# 3. docs-update

# 切换到指定会话
/switch abc123

# 切换到上一个会话
/dir -

# 重置到配置的工作目录
/dir reset
```

**自动重置（长时间不活跃后自动开启新会话）：**

```toml
[[projects]]
name = "claude-sandboxed"
reset_on_idle_mins = 60  # 60分钟后自动重置会话
```

### 4.3 OS-User 隔离

在 Linux/macOS 上，可以以不同的 Unix 用户身份运行 Agent，实现**文件系统级别的隔离**：

```toml
[[projects]]
name = "claude-sandboxed"
run_as_user = "partseeker-coder"  # 以此用户身份运行
run_as_env = ["PGSSLROOTCERT"]     # 传递的环境变量
```

**健康检查：**

```bash
cc-connect doctor user-isolation
```

这会运行三个预检查，并拒绝在检测到跨用户泄漏时启动。

### 4.4 定时任务

```bash
# 添加定时任务（自然语言）
/cron add 0 6 * * * Summarize GitHub trending

# 查看定时任务
/cron list

# 删除定时任务
/cron del <id>
```

**定时任务特点：**
- 🌅 每次在新会话中运行
- ⏱️ 可设置单任务超时
- 🔄 隔离执行，不影响主Bot

---

## 五、平台配置详解

### 5.1 飞书配置

```toml
[platforms.feishu]
type = "feishu"
app_id = "cli_xxxxxxxx"
app_secret = "xxxxxxxxxxxxxxxx"
```

**特点：**
- ✅ WebSocket 连接，无需公网IP
- ✅ 支持 Markdown/卡片
- ✅ 支持流式输出
- ✅ 支持图片/文件发送

### 5.2 Telegram 配置

```toml
[platforms.telegram]
type = "telegram"
bot_token = "123456:ABC-DEF"
```

**特点：**
- ✅ Long Polling，无需公网IP
- ✅ 支持 Markdown
- ✅ 支持语音消息（需要TTS配置）
- ✅ 支持 /new、/dir 等 Slash 命令

### 5.3 Discord 配置

```toml
[platforms.discord]
type = "discord"
bot_token = "xxxxxxxxxxxxxxxxxxxx"
guild_id = "123456789"
```

**特点：**
- ✅ Gateway 连接，无需公网IP
- ✅ 支持 @everyone/@here 提及
- ✅ 支持嵌入式消息

### 5.4 企业微信配置

```toml
[platforms.wecom]
type = "wecom"
corp_id = "wwxxxxxx"
corp_secret = "xxxxxxxx"
agent_id = "1000001"
```

**支持两种模式：**
- WebSocket（推荐，无需公网IP）
- Webhook（需要公网IP）

---

## 六、高级特性

### 6.1 多Bot协作

在群聊中部署多个Bot，让它们互相通信：

```
群聊:
├── Claude: "我来分析这个PR"
├── Gemini: "我找到3个潜在问题"
└── 汇总: "基于Claude和Gemini的分析，建议..."
```

### 6.2 附件回传

当Agent生成了截图、PDF或其他文件时，可以直接发送到聊天：

```bash
# 发送图片
cc-connect send --image /path/to/chart.png

# 发送文件
cc-connect send --file /path/to/report.pdf

# 同时发送
cc-connect send --file /path/to/report.pdf --image /path/to/chart.png
```

**在Agent中启用此功能：**

首次升级后在聊天中运行：

```bash
/bind setup
```

或在配置中全局开启：

```toml
attachment_send = "on"  # "off" 禁用
```

### 6.3 内存管理

Agent可以读写内存文件，不离开终端：

```bash
/memory read    # 读取当前内存
/memory write   # 写入内存
```

### 6.4 提供商切换

```bash
# 列出提供商
/provider list

# 切换提供商
/provider switch openai
```

---

## 七、平台功能对比

| 功能 | 飞书 | 钉钉 | Telegram | Slack | Discord | 微信 |
|------|------|------|----------|-------|---------|------|
| 文本消息 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Markdown | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| 流式输出 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 图片/文件 | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| 语音/STT/TTS | ⚠️ | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| 私聊 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 群聊 | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ |

---

## 八、最佳实践

### 8.1 安全建议

1. **配置管理员白名单**

```toml
admin_from = "alice,bob"  # 只有这些用户可以执行特权命令
```

2. **OS-User 隔离**

对于不受信任的会话，使用不同的Unix用户：

```toml
[[projects]]
name = "sandbox"
run_as_user = "sandbox-user"
```

3. **附件发送控制**

```toml
attachment_send = "off"  # 禁用附件回传
```

### 8.2 性能优化

1. **减少活跃会话数量**

```bash
/cron del <id>  # 删除不需要的定时任务
```

2. **使用 Beta 版本获取最新性能优化**

```bash
npm install -g cc-connect@beta
```

### 8.3 故障排除

**检查连接状态：**

```bash
cc-connect doctor
```

**查看日志：**

```bash
# 实时查看日志
cc-connect logs

# 查看特定平台的日志
cc-connect logs --platform feishu
```

---

## 九、常见问题

**Q: 需要公网IP吗？**

A: 大部分平台（飞书、钉钉、Telegram、Slack、Discord、企业微信）使用 WebSocket/长轮询，**不需要公网IP**。只有 LINE 的 Webhook 模式需要。

**Q: 支持微信个人号吗？**

A: 支持，但需要安装 **Beta 版本**：

```bash
npm install -g cc-connect@beta
```

**Q: 如何让多个Bot在群聊中协作？**

A: 在群聊中同时加入多个Bot，它们可以通过 @mention 互相调用。

**Q: 如何实现定时任务？**

A: 使用 `/cron add` 命令：

```bash
/cron add 0 6 * * * Summarize GitHub trending
```

---

## 十、资源链接

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/chenhg5/cc-connect |
| Discord | https://discord.gg/kHpwgaM4kq |
| Telegram | https://t.me/+odGNDhCjbjdmMmZl |
| npm | https://www.npmjs.com/package/cc-connect |

---

## 十一、总结

CC-Connect 是 AI 编程助手的多平台扩展方案，让你可以在任何设备、任何平台上与AI助手对话：

| 维度 | 说明 |
|------|------|
| 🤖 Agent支持 | 7种主流AI编程助手 |
| 📱 平台支持 | 10个常用聊天平台 |
| 🛡️ 安全性 | OS-User隔离 + 管理员白名单 |
| ⚡ 性能 | WebSocket长连接，无需公网IP |
| 🔄 扩展性 | 多Bot协作 + 定时任务 |

无论你在哪里，只要有聊天应用，就能使用Claude Code、Cursor等AI助手进行编程、代码审查、数据分析等工作。

---

**🚀 立即开始：**

```bash
# 安装
npm install -g cc-connect

# 配置
mkdir -p ~/.cc-connect
cp config.example.toml ~/.cc-connect/config.toml

# 运行
cc-connect
```

---

_🦞 本文由钳岳星君撰写，基于 CC-Connect v1.2.1_
