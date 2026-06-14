---
title: "cmux：11k Stars 的 AI 终端多路复用器，让终端成为 AI 工作流中心"
date: "2026-03-28T20:30:00+08:00"
slug: "cmux-ai-terminal-multiplexer"
aliases:
  - /posts/tech/cmux-ai-terminal-multiplexer/
description: "深度解读 mana flow.ai 的 cmux：11k Stars 的 AI 终端多路复用器，整合 Claude AI、Skills 系统、远程 SSH、工作流自动化，支持 26+ 语言本地化。"
draft: false
categories: ["技术笔记"]
tags: ["cmux", "终端", "Claude", "多路复用器", "macOS", "Ghostty", "AI工作流"]
---

# cmux：11k Stars 的 AI 终端多路复用器，让终端成为 AI 工作流中心

> 预计阅读时间：25分钟 | 难度：⭐⭐⭐

---

> **目标读者**：希望将终端升级为 AI 工作流中心的开发者
> **前置知识**：终端基础、命令行操作、了解 Claude API 基本概念
> **预计阅读时间**：18 分钟
> **核心价值**：把 Claude AI 能力装进终端，实现工作流自动化

---

## 一句话理解 cmux

cmux（[manaflow-ai/cmux](https://github.com/manaflow-ai/cmux)，11k Stars）是 **mana flow.ai** 打造的下一代 AI 终端。核心思路：

```
传统终端：输入命令 → 输出文本 → 纯文本交互
cmux 终端：输入命令 → AI 增强 → 智能自动化 → 跨设备同步
```

**简单说**：把 Claude AI 装进终端，加上多路复用和远程 SSH，让终端成为真正的 AI 工作流中心。

---

## 为什么关注这个项目

| 亮点 | 说明 |
|------|------|
| **原生 macOS 应用** | 基于 Swift + libghostty，性能优秀 |
| **Claude 深度整合** | 内置 Claude AI 命令和 Skills |
| **Skills 系统** | 可扩展的 AI 技能框架 |
| **远程 SSH** | 支持远程终端和 daemon |
| **26+ 语言** | 完善的国际化支持 |

对比传统方案：

| 方案 | AI 能力 | 终端复用 | 远程 SSH | 开发活跃度 |
|------|---------|----------|----------|------------|
| tmux | ❌ | ✅ | ❌ | 中 |
| Warp | ✅ 内置 | ✅ | ❌ | 高 |
| **cmux** | ✅ Claude 集成 | ✅ | ✅ | **极高**（每日提交）|

---

## 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | **11k** |
| Forks | **760** |
| 提交数 | 1,894 次 |
| 分支数 | 602 个 |
| Tags | 124 个 |
| 许可证 | AGPL-3.0 + 商业许可 |
| 最新版本 | v0.x.x（预发布） |
| 开发节奏 | **每日提交**（最新 17 分钟前）|

---

## 工作原理

### 核心架构

```
┌─────────────────────────────────────────────────────┐
│                    macOS 桌面                         │
│  ┌─────────────────────────────────────────────┐     │
│  │  cmux App (Swift + libghostty)              │     │
│  │  ┌─────────────────────────────────────┐    │     │
│  │  │  GhosttyTabs: 垂直标签页管理        │    │     │
│  │  │  Claude Integration: AI 能力嵌入     │    │     │
│  │  │  Skills System: 可扩展技能框架        │    │     │
│  │  └─────────────────────────────────────┘    │     │
│  └─────────────────────────────────────────────┘     │
├─────────────────────────────────────────────────────┤
│                    CLI 层                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │ cmux CLI     │  │ Remote SSH   │  │ omo      │  │
│  │ 命令行工具    │  │ 远程终端     │  │ Agent集成│  │
│  └──────────────┘  └──────────────┘  └──────────┘  │
├─────────────────────────────────────────────────────┤
│                   Skills 层                          │
│  ┌──────────────┐  ┌──────────────┐                  │
│  │ Claude      │  │ Custom       │                  │
│  │ Commands    │  │ Skills       │                  │
│  └──────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────┘
```

**关键技术选型**：

| 组件 | 技术 | 优势 |
|------|------|------|
| 终端渲染 | libghostty | GPU 加速、高性能 |
| 开发语言 | Swift | 原生 macOS 体验 |
| 构建工具 | Xcode / Swift PM | 标准化 |
| 远程 daemon | Go | 跨平台、高性能 |

---

## 核心功能详解

### 1. 终端多路复用

类似 tmux 的能力，但专为 macOS 优化：

| 功能 | 快捷键 | 说明 |
|------|--------|------|
| 新建标签页 | `Cmd+T` | 垂直标签页 |
| 垂直分屏 | `Cmd+D` | 上下分屏 |
| 水平分屏 | `Cmd+[` | 左右分屏 |
| 会话持久化 | 自动 | 关闭不丢失 |

### 2. Claude AI 整合

**内置 Claude 命令**：

```bash
# 直接调用 Claude
cmux claude "解释这段代码的逻辑"

# 使用 Claude 分析项目
cmux claude --analyze .

# 自动化代码审查
cmux claude --review src/
```

**上下文感知**：cmux 能感知当前终端上下文（所在目录、Git 状态、最近命令），生成更准确的响应。

### 3. Skills 系统

Skills 是 cmux 的扩展框架，允许自定义 AI 能力：

**目录结构**：

```
skills/
├── git-helper/
│   └── SKILL.md          # Git 辅助技能
├── code-review/
│   └── SKILL.md          # 代码审查技能
└── ...
```

**创建自定义 Skill**：

```markdown
# skills/my-skill/SKILL.md

# My Skill

## 触发条件
当用户输入 /my-skill 或匹配关键词时激活

## 执行逻辑
1. 读取上下文
2. 调用 Claude API
3. 返回格式化结果

## 配置参数
- api_key: API 密钥
- model: 使用哪个模型
- temperature: 创造性程度
```

### 4. 远程 SSH 支持

**远程 Daemon**（Go 实现）：

```bash
# 远程服务器上启动
cmux daemon start --port 8080

# SSH 隧道连接
ssh -L 8080:localhost:8080 user@remote-server

# 本地连接远程
/cmux connect user@remote-server:8080
```

**omo 集成**：与 oh-my-openagent 对接，支持现有 Agent 工作流。

### 5. CLI 工具

```bash
# 安装
brew install manaflow-ai/tap/cmux

# 基本命令
cmux help              # 查看帮助
cmux launch            # 启动 GUI
cmux claude "prompt"   # 直接调用 Claude
cmux omo               # oh-my-openagent 集成
cmux daemon            # 远程 daemon 管理
```

---

## 安装与快速开始

### macOS 安装

```bash
# Homebrew（推荐）
brew install manaflow-ai/tap/cmux

# 或下载预编译包
# https://github.com/manaflow-ai/cmux/releases
```

### 源码构建

```bash
# 克隆仓库
git clone https://github.com/manaflow-ai/cmux.git
cd cmux

# Xcode 打开
open GhosttyTabs.xcodeproj

# 或命令行构建
swift build
```

### 配置

**环境变量**：

```bash
# Claude API（必需）
export CLAUDE_API_KEY=sk-ant-...

# 远程 daemon 端口
export CMUX_DAEMON_PORT=8080
```

**配置文件**：

`~/.cmux/` 目录下：
- `config.toml` - 主配置
- `themes/` - 主题文件
- `skills/` - 自定义 Skills
- `commands/` - 自定义命令

---

## 项目结构

```
cmux/
├── AppIcon.icon/           # 应用图标
├── Assets.xcassets/        # 资产目录
├── CLI/                    # 命令行工具
├── GhosttyTabs.xcodeproj/  # Xcode 项目
├── Sources/                # 核心源码
├── cmuxTests/              # 单元测试
├── cmuxUITests/            # UI 测试
├── daemon/remote/          # 远程 daemon (Go)
├── docs/                   # 文档
├── ghostty/                # Ghostty 子模块
├── skills/                 # Skills 技能文件
├── tests/                  # 测试套件
├── tests_v2/               # 测试套件 v2
├── web/                    # Web 界面
├── .claude/commands/        # Claude 命令
├── scripts/                # 构建脚本
└── vendor/                # 第三方依赖
```

---

## 快速使用指南

### 基本操作

**启动应用**：

```bash
# 启动 GUI
cmux launch

# 或直接打开
open -a cmux
```

**终端快捷键**：

| 快捷键 | 功能 |
|--------|------|
| `Cmd+T` | 新建标签页 |
| `Cmd+D` | 垂直分屏 |
| `Cmd+[` | 水平分屏 |
| `Cmd+W` | 关闭当前 pane |
| `Cmd+,` | 偏好设置 |

### Claude 命令使用

```bash
# 解释代码
cmux claude "解释这个函数的逻辑"

# 代码审查
cmux claude --review ./src

# 项目分析
cmux claude --analyze .

# 自动生成测试
cmux claude --generate-tests ./tests
```

### 远程工作流

**1. 在远程服务器启动 daemon**：

```bash
ssh user@remote-server
cmux daemon start --port 8080
```

**2. 本地连接**：

```bash
# SSH 隧道
ssh -L 8080:localhost:8080 user@remote-server

# 连接
/cmux connect localhost:8080
```

---

## 国际化

cmux 支持 26+ 种语言，README 有多个语言版本：

| 语言 | 文件 |
|------|------|
| English | README.md |
| 简体中文 | README.zh-CN.md |
| 繁体中文 | README.zh-TW.md |
| 日语 | README.ja.md |
| 韩语 | README.ko.md |
| 俄语 | README.ru.md |
| 乌克兰语 | README.uk.md |
| 越南语 | README.vi.md |
| 泰语 | README.th.md |
| 土耳其语 | README.tr.md |

---

## 与同类项目对比

| 项目 | Stars | AI 整合 | 终端复用 | 远程 SSH | 平台 |
|------|-------|---------|----------|----------|------|
| **cmux** | 11k | Claude 深度整合 | ✅ | ✅ | macOS |
| tmux | 33k | ❌ | ✅ | ❌ | 全平台 |
| screen | 2k | ❌ | ✅ | ❌ | 全平台 |
| Ghostty | 26k | ❌ | ❌ | ❌ | macOS/Linux |
| Warp | 20k | 内置 AI | ✅ | ❌ | macOS/Linux |

**cmux 的独特优势**：

1. **原生 macOS**：Swift + libghostty，性能优秀
2. **Claude 深度整合**：不只是 AI 提示，而是系统级集成
3. **Skills 可扩展**：开放的技能框架
4. **远程工作流**：真正的跨设备 AI 工作站

---

## 适用场景

| 场景 | 说明 | 推荐度 |
|------|------|--------|
| AI 开发 | 将 Claude 能力融入日常终端 | ⭐⭐⭐⭐⭐ |
| 远程开发 | SSH 远程 + AI 辅助 | ⭐⭐⭐⭐⭐ |
| 工作流自动化 | 自定义 Skills 实现自动化 | ⭐⭐⭐⭐ |
| 跨设备开发 | 多设备同步工作流 | ⭐⭐⭐⭐ |
| 代码审查 | Claude 辅助代码审查 | ⭐⭐⭐⭐⭐ |

---

## 常见问题

### Q1：cmux 和 Warp 有什么区别？

| 对比 | cmux | Warp |
|------|------|------|
| AI 整合 | Claude API（可切换模型）| Warp 内置 AI |
| 扩展性 | Skills 框架完全可定制 | 有限扩展 |
| 远程 SSH | ✅ 原生支持 | ❌ 不支持 |
| 许可证 | AGPL-3.0 + 商业 | 专有 |

### Q2：需要付费吗？

核心功能免费。AGPL-3.0 许可证下可免费使用，商业使用需联系 mana flow.ai 获取商业许可。

### Q3：Windows/Linux 支持吗？

目前主要支持 macOS。Linux 支持在规划中（Ghostty 已有 Linux 版本）。

### Q4：Skills 和 Claude Commands 有什么区别？

- **Claude Commands**：简单的指令触发，执行单一任务
- **Skills**：复杂的工作流，包含多步骤逻辑、配置参数、上下文管理

---

## 总结

### 价值总结

| 维度 | 传统终端 | cmux 终端 |
|------|----------|-----------|
| AI 能力 | 无 | Claude 深度整合 |
| 操作方式 | 纯手动 | 智能自动化 |
| 使用范围 | 单机 | 跨设备同步 |
| 扩展方式 | 固定功能 | Skills 可扩展 |

### 相关资源

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/manaflow-ai/cmux |
| 官网 | https://cmux.dev |
| 发布页 | https://github.com/manaflow-ai/cmux/releases |
| Homebrew | `brew install manaflow-ai/tap/cmux` |

---

*文档版本 1.1 | 更新日期：2026-03-28 | Stars: 11k ⭐*
