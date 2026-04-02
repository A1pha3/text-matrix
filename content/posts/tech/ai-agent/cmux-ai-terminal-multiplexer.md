---
title: "cmux：11k Stars 的 AI 终端多路复用器，让终端成为 AI 工作流中心"
date: 2026-03-28T20:30:00+08:00
slug: "cmux-ai-terminal-multiplexer"
aliases:
  - /posts/tech/cmux-ai-terminal-multiplexer/
description: "深度解读 mana flow.ai 的 cmux：11k Stars 的 AI 终端多路复用器，整合 Claude AI、Skills 系统、远程 SSH、工作流自动化，支持 26+ 语言本地化。"
draft: false
categories: ["技术笔记"]
tags: ["cmux", "终端", "Claude", "多路复用器", "macOS"]
---

# cmux：11k Stars 的 AI 终端多路复用器，让终端成为 AI 工作流中心

> **目标读者**：希望将终端升级为 AI 工作流中心的开发者
> **核心问题**：如何让终端具备 AI 能力并实现工作流自动化？
> **难度**：⭐⭐⭐⭐（专家设计）
> **来源**：GitHub manaflow-ai/cmux，2026-03-28

---

## 一、项目概览

### 1.1 为什么这个项目值得关注

[cmux](https://github.com/manaflow-ai/cmux) 是 mana flow.ai 打造的下一代 AI 终端多路复用器。与传统终端复用器（如 tmux、screen）不同，cmux 深度整合 Claude AI 能力，将 AI 工作流直接嵌入终端环境。

**核心数据：**

| 指标 | 数值 |
|------|------|
| GitHub Stars | 11k |
| Forks | 760 |
| Commits | 1,894 |
| Branches | 602 |
| Tags | 124 |
| License | AGPL-3.0 + 商业许可 |
| 最新版本 | v0.x.x（预发布） |

### 1.2 核心定位

**官方网站**：https://cmux.dev

> cmux = Claude Terminal Multiplexer
> 将 Claude AI 能力深度融入终端，实现工作流自动化

### 1.3 项目特色

| 特色 | 说明 |
|------|------|
| **原生 macOS 应用** | 基于 Swift 和 libghostty 构建 |
| **Claude 深度整合** | 内置 Claude AI 命令和 Skills |
| **Skills 系统** | 可扩展的 AI 技能框架 |
| **远程 SSH** | 支持远程终端和 daemon |
| **CLI 工具** | 强大的命令行接口 |
| **国际化** | 支持 26+ 种语言 |

---

## 二、技术架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────┐
│                     cmux                              │
├─────────────────────────────────────────────────────┤
│  macOS App (Swift + libghostty)                      │
│  ┌─────────────────────────────────────────────┐     │
│  │  GhosttyTabs: 垂直标签页管理                  │     │
│  │  Claude Integration: AI 能力嵌入              │     │
│  │  Skills System: 可扩展技能框架                 │     │
│  └─────────────────────────────────────────────┘     │
├─────────────────────────────────────────────────────┤
│  CLI & Daemon                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐   │
│  │ cmux CLI    │  │ Remote SSH  │  │ omo集成    │   │
│  │ 命令行工具   │  │ 远程终端    │  │ oh-my-open │   │
│  └──────────────┘  └──────────────┘  └────────────┘   │
├─────────────────────────────────────────────────────┤
│  Skills & Commands                                   │
│  ┌──────────────┐  ┌──────────────┐                   │
│  │ Claude      │  │ Custom      │                   │
│  │ Commands    │  │ Skills      │                   │
│  └──────────────┘  └──────────────┘                   │
└─────────────────────────────────────────────────────┘
```

### 2.2 技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 平台 | macOS | 原生应用 |
| 语言 | Swift | 核心开发语言 |
| 终端 | libghostty（Ghostty 终端渲染库） | 高性能终端渲染 |
| 构建 | Xcode | macOS 标准构建工具 |
| 包管理 | Swift Package Manager | 依赖管理 |
| 测试 | XCTest | 单元和 UI 测试 |

### 2.3 核心目录结构

```
cmux/
├── AppIcon.icon/           # 应用图标资源
├── Assets.xcassets/        # 资产目录
├── CLI/                    # 命令行工具
├── GhosttyTabs.xcodeproj/  # Xcode 项目
├── Sources/                # 核心源代码
├── cmuxTests/              # 单元测试
├── cmuxUITests/            # UI 测试
├── daemon/remote/          # 远程 daemon (Go)
├── docs/                   # 文档
├── ghostty/                # Ghostty 终端子模块
├── skills/                 # Skills 技能文件
├── tests/                  # 测试套件
├── tests_v2/               # 测试套件 v2
├── web/                    # Web 界面
├── .claude/commands/        # Claude 命令
├── scripts/                # 构建脚本
└── vendor/                # 第三方依赖
```

---

## 三、核心功能

### 3.1 终端多路复用

cmux 提供与现代终端复用器类似的功能：

| 功能 | 说明 |
|------|------|
| 垂直标签页 | GhosttyTabs 垂直管理多个终端会话 |
| 分屏 | 支持多 pane 布局 |
| 快速切换 | 高效的会话切换机制 |
| 状态持久化 | 会话状态持久化存储 |

### 3.2 Claude AI 整合

**Claude Commands：**

通过 `.claude/commands/` 目录，cmux 支持自定义 Claude 命令，可用于：
- 快速执行常见 AI 任务
- 自动化工作流
- 代码生成和审查

**Skills 系统：**

cmux 的 Skills 系统允许扩展 AI 能力：
- 可配置的技能模块
- 预加载和自动发现
- 上下文分叉支持

### 3.3 远程 SSH 支持

**Remote Daemon：**

cmux 的远程 daemon（Go 语言实现）支持：
- SSH 会话远程连接
- 远程终端复用
- 跨设备工作流同步

**omo 集成（oh-my-openagent）：**

cmux CLI 包含 `omo` 命令（oh-my-openagent 集成），支持与现有 Agent 工作流无缝对接。

### 3.4 CLI 工具

```bash
# 安装 cmux
brew install manaflow-ai/tap/cmux

# 基本命令
cmux help          # 查看帮助
cmux omo           # oh-my-openagent 集成
cmux [command]     # 执行 Claude 命令
```

---

## 四、快速开始

### 4.1 安装

**macOS 安装：**

```bash
# 使用 Homebrew 安装
brew install manaflow-ai/tap/cmux

# 或下载预编译包
# 访问 https://github.com/manaflow-ai/cmux/releases
```

**源码构建：**

```bash
# 克隆仓库
git clone https://github.com/manaflow-ai/cmux.git
cd cmux

# 使用 Xcode 打开
open GhosttyTabs.xcodeproj

# 或命令行构建
swift build
```

### 4.2 配置

**环境变量：**

```bash
# Claude API 配置
export CLAUDE_API_KEY=your_api_key

# 远程 daemon 配置
export CMUX_DAEMON_PORT=8080
```

**配置文件：**

cmux 配置文件位于 `~/.cmux/`，支持：
- 主题配置
- 快捷键绑定
- Skills 路径
- 远程连接设置

### 4.3 基本使用

**启动应用：**

```bash
# 启动 GUI
cmux launch

# 或直接打开
open -a cmux
```

**创建新会话：**

```bash
# 在应用中
# Cmd+T: 新建标签页
# Cmd+D: 垂直分屏
# Cmd+[: 左右分屏
```

**使用 Claude 命令：**

```bash
# 在终端中
cmux claude "解释这段代码"
```

---

## 五、Skills 与扩展

### 5.1 Skills 目录

cmux 的 Skills 存放在 `skills/` 目录：

```bash
skills/
├── skill1/
│   └── SKILL.md
├── skill2/
│   └── SKILL.md
└── ...
```

### 5.2 自定义 Skill

创建自定义 Skill：

```markdown
# skills/my-skill/SKILL.md

# My Skill

## 描述
这个 Skill 用于...

## 使用方法
执行特定任务

## 配置
- 参数 1: 说明
- 参数 2: 说明
```

### 5.3 Claude Commands

在 `.claude/commands/` 中创建命令：

```bash
.claude/commands/
├── my-command.md
└── another-command.md
```

命令文件格式：

```markdown
# My Command

## 用途
这个命令用于...

## 使用方法
/cmds my-command [参数]
```

---

## 六、远程工作流

### 6.1 SSH Remote Daemon

**启动远程 Daemon：**

```bash
# 在远程服务器上
cmux daemon start --port 8080

# 或使用 SSH 隧道
ssh -L 8080:localhost:8080 user@remote-server
```

**连接到远程：**

```bash
# 在本地 cmux 中
/cmux connect user@remote-server:8080
```

### 6.2 多设备同步

cmux 支持跨设备工作流同步：
- 会话状态同步
- 终端历史同步
- AI 上下文持久化

### 6.3 omo 集成

`cmux omo` 命令支持 oh-my-openagent 集成，可与现有 Agent 工作流对接。

---

## 七、国际化

cmux 支持 26+ 种语言的本地化：

| 语言 | 文件 | 语言 | 文件 |
|------|------|------|------|
| 英文 | README.md | 韩文 | README.ko.md |
| 中文简体 | README.zh-CN.md | 乌克兰文 | README.uk.md |
| 中文繁体 | README.zh-TW.md | 越南文 | README.vi.md |
| 日文 | README.ja.md | 泰文 | README.th.md |
| 韩文 | README.ko.md | 土耳其文 | README.tr.md |

---

## 八、与同类项目对比

### 8.1 终端复用器对比

| 项目 | 定位 | Stars | AI 整合 | 平台 |
|------|------|-------|---------|------|
| **cmux** | AI 终端多路复用 | 11k | 深度整合 | macOS |
| **tmux** | 传统终端复用 | 33k | 无 | 全平台 |
| **screen** | 传统终端复用 | 2k | 无 | 全平台 |
| **Ghostty** | 现代终端 | 26k | 无 | macOS/Linux |
| **Warp** | AI 终端 | 20k | 内置 | macOS/Linux |

### 8.2 cmux 的独特优势

1. **原生 macOS**：基于 Swift 和 libghostty，性能优秀
2. **Skills 可扩展**：开放的技能框架，可自定义 AI 能力
3. **远程工作流**：支持 SSH 远程和 daemon
4. **Active 开发**：每日都有新提交（最新17分钟前）

---

## 九、总结与展望

### 9.1 核心价值

| 传统终端 | cmux 终端 |
|----------|-----------|
| 纯文本界面 | AI 能力嵌入 |
| 手动操作 | 智能自动化 |
| 单机使用 | 跨设备工作流 |
| 固定功能 | Skills 可扩展 |

### 9.2 适用场景

| 场景 | 说明 |
|------|------|
| **AI 开发者** | 将 Claude 能力融入日常终端工作 |
| **远程工作** | SSH 远程 + AI 辅助 |
| **工作流自动化** | 自定义 Skills 实现自动化 |
| **跨设备开发** | 多设备同步工作流 |

### 9.3 资源链接

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/manaflow-ai/cmux |
| 官网 | https://cmux.dev |
| 发布页 | https://github.com/manaflow-ai/cmux/releases |
| Homebrew | `brew install manaflow-ai/tap/cmux` |

---

**相关话题标签**

#cmux #终端 #Claude #多路复用器 #macOS

**来源**

- GitHub：https://github.com/manaflow-ai/cmux

---

*cmux 由 mana flow.ai 开发，采用 AGPL-3.0 + 商业许可双授权模式。*
