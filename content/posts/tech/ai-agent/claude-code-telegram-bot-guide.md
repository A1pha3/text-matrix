---
title: "Claude Code Telegram Bot：远程访问 AI 编程助手的完全指南"
slug: "claude-code-telegram-bot-guide"
aliases:
  - /posts/tech/claude-code-telegram-bot-guide/
date: "2026-04-01T01:08:00+08:00"
categories: ["技术笔记"]
tags: ["Claude Code", "Telegram Bot", "AI编程", "远程开发", "Claude", "智能体", "Webhook", "事件驱动", "Python", "自动化"]
description: "深度解析 Claude Code Telegram Bot (2.3k Stars)：通过 Telegram 远程访问 Claude Code，支持智能体模式和经典终端模式，提供自然语言代码交互、会话持久化、Webhook 自动化、完整安全审计等 23 项功能特性。"
---

# Claude Code Telegram Bot：远程访问 AI 编程助手的完全指南

> 预计阅读时间：25分钟 | 难度：⭐⭐⭐

---

## 学习目标

完成本文档后，你将能够：

- ✅ 理解 Claude Code Telegram Bot 的核心定位与设计理念
- ✅ 掌握 Claude Code Telegram Bot 的安装与配置方法
- ✅ 理解两种交互模式（智能体模式/经典模式）的使用方法
- ✅ 使用 Telegram 与 Claude 进行自然语言代码交互
- ✅ 配置 Webhook 实现事件驱动自动化
- ✅ 掌握安全机制（访问控制/目录隔离/速率限制）
- ✅ 使用项目线程模式实现多项目管理

---

## §2 项目概述

### 2.1 什么是 Claude Code Telegram Bot？

**Claude Code Telegram Bot**（[GitHub 仓库](https://github.com/RichardAtCT/claude-code-telegram)）是一个将 Telegram 与 Claude Code 连接的工具，提供对话式 AI 编程界面。

**官方描述**：

> A Telegram bot that gives you remote access to Claude Code. Chat naturally with Claude about your projects from anywhere -- no terminal commands needed.

**核心功能**：无论身在何处，都可以通过 Telegram 与 Claude 进行自然语言交流，完成代码分析、编辑和解释。

### 2.2 核心数据

| 指标 | 数值 |
|------|------|
| **Stars** | 2,294 (2.3k) |
| **Forks** | 303 |
| **Watchers** | 8 |
| **提交数** | 226 |
| **发布版本** | 7 个 |
| **贡献者** | 22 |
| **许可证** | MIT |

### 2.3 技术栈

| 类别 | 技术 | 占比 |
|------|------|------|
| **核心语言** | Python | 99.6% |
| **构建** | Makefile | 0.4% |

### 2.4 核心特性概览

| 类别 | 功能数量 | 说明 |
|------|----------|------|
| **交互模式** | 2 种 | 智能体模式（默认）/ 经典终端模式 |
| **认证** | 多层 | 白名单 + 可选令牌认证 |
| **安全** | 6 层 | 访问控制/目录隔离/速率限制/注入防护等 |
| **持久化** | 3 种 | SQLite + 会话 + 审计日志 |
| **可配置工具** | 16 个 | 允许清单/禁止清单控制 |
| **通知** | 3 种 | Webhook/定时任务/主动推送 |

---

## §3 两种交互模式

### 3.1 智能体模式（默认）

智能体模式是默认的对话式交互模式。用户直接与 Claude 自然对话，无需特殊命令。

**可用命令**：

| 命令 | 说明 |
|------|------|
| `/start` | 开始新会话 |
| `/new` | 开始新对话 |
| `/status` | 查看状态 |
| `/verbose` | 控制详细程度 |
| `/repo` | 列出/切换仓库 |
| `/sync_threads` | 同步项目线程 |

**详细级别**：

| 级别 | 说明 |
|------|------|
| `0` (quiet) | 仅显示最终响应 |
| `1` (normal，默认) | 实时显示工具名称和推理片段 |
| `2` (detailed) | 显示工具名称、输入和更长的推理文本 |

### 3.2 经典模式

经典模式提供完整的终端式界面，包含 13 个命令和内联键盘。

**可用命令**：

| 命令 | 说明 |
|------|------|
| `/start` | 开始会话 |
| `/help` | 帮助信息 |
| `/new` | 开始新对话 |
| `/continue` | 继续上次对话 |
| `/end` | 结束对话 |
| `/status` | 查看状态 |
| `/cd` | 切换目录 |
| `/ls` | 列出文件 |
| `/pwd` | 显示当前目录 |
| `/projects` | 列出项目 |
| `/export` | 导出会话 |
| `/actions` | 快捷操作 |
| `/git` | Git 操作 |
| `/sync_threads` | 同步项目线程 |

### 3.3 模式对比

| 方面 | 智能体模式 | 经典模式 |
|------|------------|----------|
| **交互方式** | 自然语言对话 | 终端命令 |
| **命令数量** | 6 个 | 13 个 |
| **易用性** | 更高 | 较低 |
| **灵活性** | 较高 | 更高 |
| **适用场景** | 日常使用 | 高级用户 |

---

## §4 安装与部署

### 4.1 环境要求

| 要求 | 说明 |
|------|------|
| **Python** | 3.11+ |
| **Claude Code CLI** | 必须安装并认证 |
| **Telegram Bot Token** | 通过 @BotFather 获取 |

### 4.2 安装方式

#### 方式一：使用 uv 安装（推荐）

```bash
uv tool install git+https://github.com/RichardAtCT/claude-code-telegram@v1.3.0
```

#### 方式二：使用 pip 安装

```bash
pip install git+https://github.com/RichardAtCT/claude-code-telegram@v1.3.0
```

#### 方式三：从源码安装（开发用）

```bash
git clone https://github.com/RichardAtCT/claude-code-telegram.git
cd claude-code-telegram
make dev
```

### 4.3 配置

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置
nano .env
```

**必需配置**：

```env
TELEGRAM_BOT_TOKEN=1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_BOT_USERNAME=my_claude_bot
APPROVED_DIRECTORY=/Users/yourname/projects
ALLOWED_USERS=123456789
```

### 4.4 运行

```bash
# 生产环境运行
make run

# 调试模式运行
make run-debug
```

---

## §5 配置详解

### 5.1 必需配置

| 配置项 | 说明 |
|--------|------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot 令牌（从 @BotFather 获取） |
| `TELEGRAM_BOT_USERNAME` | Bot 用户名 |
| `APPROVED_DIRECTORY` | 允许访问的基础目录 |
| `ALLOWED_USERS` | 允许使用的用户 ID（逗号分隔） |

### 5.2 Claude 配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | 从 CLI 认证继承 |
| `CLAUDE_MAX_COST_PER_USER` | 每用户最大消费（美元） | 无限制 |
| `CLAUDE_TIMEOUT_SECONDS` | 操作超时时间 | 300 |
| `CLAUDE_ALLOWED_TOOLS` | 允许的工具列表 | 全部允许 |

### 5.3 模式配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `AGENTIC_MODE` | 启用智能体模式 | true |
| `VERBOSE_LEVEL` | 详细级别 | 1 |

### 5.4 速率限制

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `RATE_LIMIT_REQUESTS` | 每窗口请求数 | 10 |
| `RATE_LIMIT_WINDOW` | 窗口大小（秒） | 60 |

### 5.5 Webhook 和调度器

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `ENABLE_API_SERVER` | 启用 Webhook 服务器 | false |
| `API_SERVER_PORT` | 服务器端口 | 8080 |
| `ENABLE_SCHEDULER` | 启用定时任务 | false |
| `NOTIFICATION_CHAT_IDS` | 通知聊天 ID | 无 |

---

## §6 核心功能详解

### 6.1 自然语言交互

在智能体模式下，直接用自然语言与 Claude 交流：

```
You: Can you help me add error handling to src/api.py?
Bot: I'll analyze src/api.py and add error handling...
Claude: [分析代码并提出改进建议]

You: Looks good. Now run the tests.
Bot: Running pytest...
Claude: All 47 tests passed.
```

### 6.2 会话持久化

自动为每个用户/项目目录保持会话上下文。切换项目时 Claude 会自动恢复相关会话。

### 6.3 文件上传与处理

| 功能 | 说明 |
|------|------|
| **文件上传** | 支持压缩包自动解压 |
| **图片分析** | 支持截图和问题图片上传 |
| **语音转录** | 支持 Mistral Voxtral / OpenAI Whisper / 本地 whisper.cpp |

### 6.4 GitHub 集成

Claude Code 已经熟悉 `gh` CLI 和 `git`。配置认证后，可以对话操作仓库：

```bash
# 服务器上认证
gh auth login

# 对话操作
You: List my repos related to monitoring
Claude: [运行 gh repo list]

You: Clone the uptime one
Claude: [克隆到 workspace]
```

### 6.5 项目线程模式

支持按项目自动路由到对应的 Telegram 话题：

```env
ENABLE_PROJECT_THREADS=true
PROJECT_THREADS_MODE=private
PROJECTS_CONFIG_PATH=config/projects.yaml
```

---

## §7 事件驱动自动化

### 7.1 Webhook 接收

```env
ENABLE_API_SERVER=true
GITHUB_WEBHOOK_SECRET=your_secret
```

支持的触发事件：
- GitHub push、PR、issues
- 自定义 Webhook 提供商

### 7.2 定时任务

```env
ENABLE_SCHEDULER=true
```

使用 cron 表达式配置定时任务，例如每日代码健康检查。

### 7.3 主动通知

```env
NOTIFICATION_CHAT_IDS=123,456
```

向配置的聊天 ID 主动推送通知。

---

## §8 安全机制

### 8.1 安全层次

| 层次 | 功能 | 说明 |
|------|------|------|
| **访问控制** | 白名单认证 | 仅允许授权用户访问 |
| **目录隔离** | 沙箱限制 | 限制在批准目录内操作 |
| **速率限制** | 请求/成本限制 | 防止滥用 |
| **输入验证** | 注入防护 | 防止注入和路径穿越攻击 |
| **Webhook 认证** | HMAC-SHA256 | GitHub HMAC 验证 |
| **审计日志** | 完整追踪 | 记录所有用户操作 |

### 8.2 目录隔离

- 所有文件操作限制在 `APPROVED_DIRECTORY` 内
- 自动阻止路径穿越攻击（`../` 等）
- 项目目录独立隔离

### 8.3 速率限制

使用令牌桶算法实现：
- 请求速率限制
- 每用户成本限制

---

## §9 开发与贡献

### 9.1 开发命令

| 命令 | 说明 |
|------|------|
| `make dev` | 安装所有依赖 |
| `make test` | 运行测试（含覆盖率） |
| `make lint` | Black + isort + flake8 + mypy |
| `make format` | 自动格式化代码 |
| `make run-debug` | 调试模式运行 |
| `make run-watch` | 代码变更自动重启 |

### 9.2 版本管理

| 命令 | 说明 |
|------|------|
| `make bump-patch` | 补丁版本 (1.2.0 → 1.2.1) |
| `make bump-minor` | 次版本 (1.2.0 → 1.3.0) |
| `make bump-major` | 主版本 (1.2.0 → 2.0.0) |

### 9.3 代码标准

- Python 3.11+
- Black 格式化（88 字符）
- 类型提示必需
- pytest 覆盖率 >85%

---

## §10 项目结构

### 10.1 目录结构

```
claude-code-telegram/
├── src/                    # 源代码
├── tests/                  # 测试
├── docs/                    # 文档
├── config/                  # 配置文件
├── .github/workflows/       # GitHub Actions
├── .env.example             # 环境变量示例
├── pyproject.toml           # Python 项目配置
├── poetry.lock              # 依赖锁定
├── Makefile                # 构建脚本
└── README.md              # 项目文档
```

### 10.2 核心模块

| 模块 | 说明 |
|------|------|
| **src/** | 核心 Bot 逻辑 |
| **tests/** | 测试套件 |
| **docs/** | 详细文档 |
| **config/** | 配置文件 |

---

## §11 常见问题

### Q1：Bot 不响应怎么办？

检查项：
- `TELEGRAM_BOT_TOKEN` 是否正确
- 用户 ID 是否在 `ALLOWED_USERS` 中
- Claude Code CLI 是否已安装
- 调试模式运行：`make run-debug`

### Q2：Claude 集成不工作？

```bash
# SDK 模式（默认）
claude auth status
# 或检查 ANTHROPIC_API_KEY

# CLI 模式
claude --version
claude auth status
```

### Q3：如何控制成本？

```env
CLAUDE_MAX_COST_PER_USER=10.0  # 每用户 10 美元上限
```

使用 `/status` 监控使用情况。

### Q4：如何查找 Telegram 用户 ID？

向 @userinfobot 发送消息，它会返回用户 ID。

---

## §12 总结

### 12.1 核心优势

| 优势 | 说明 |
|------|------|
| **远程访问** | 随时随地通过 Telegram 与代码交互 |
| **自然语言** | 无需终端命令，直接对话 |
| **会话持久化** | 自动保持项目上下文 |
| **事件自动化** | Webhook + 定时任务 + 主动通知 |
| **安全可靠** | 多层安全保护，完整审计日志 |

### 12.2 适用场景

| 场景 | 适用性 |
|------|--------|
| **移动开发** | 外出时代码审查和修改 |
| **自动化** | Webhook 触发 CI/CD 事件处理 |
| **监控** | 定时任务推送代码健康报告 |
| **团队协作** | 多用户白名单控制 |

### 12.3 项目信息

| 项目 | 信息 |
|------|------|
| **Stars** | 2.3k |
| **Forks** | 303 |
| **许可证** | MIT |
| **最新版本** | v1.6.0 |

### 12.4 相关链接

| 资源 | 链接 |
|------|------|
| **GitHub** | https://github.com/RichardAtCT/claude-code-telegram |
| **文档** | docs/ 目录 |
| **Telegram Bot** | @BotFather 创建 |

---

## §13 附录：命令参考

### 13.1 智能体模式命令

| 命令 | 说明 |
|------|------|
| `/start` | 开始新会话 |
| `/new` | 开始新对话 |
| `/status` | 查看状态 |
| `/verbose 0|1|2` | 控制详细程度 |
| `/repo` | 列出仓库 |
| `/repo <name>` | 切换到指定仓库 |
| `/sync_threads` | 同步项目线程 |

### 13.2 经典模式命令

| 命令 | 说明 |
|------|------|
| `/start` | 开始会话 |
| `/help` | 帮助信息 |
| `/new` | 开始新对话 |
| `/continue` | 继续上次对话 |
| `/end` | 结束对话 |
| `/status` | 查看状态 |
| `/cd <dir>` | 切换目录 |
| `/ls` | 列出文件 |
| `/pwd` | 显示当前目录 |
| `/projects` | 列出项目 |
| `/export` | 导出会话 |
| `/actions` | 快捷操作菜单 |
| `/git <cmd>` | Git 操作 |

---

*文档版本 1.0 | 撰写日期：2026-04-01 | 基于 Claude Code Telegram Bot (2.3k Stars) | 最新版本 v1.6.0*