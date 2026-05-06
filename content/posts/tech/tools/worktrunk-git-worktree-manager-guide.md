---
title: "Worktrunk：AI 并行开发 Git Worktree 管理器完全指南"
slug: "worktrunk-git-worktree-manager-guide"
aliases:
  - /posts/tech/worktrunk-git-worktree-manager-guide/
date: "2026-03-31T15:35:00+08:00"
categories: ["技术笔记"]
tags: ["Worktrunk", "Git", "Worktree", "AI Agent", "Claude Code", "Rust", "CLI工具"]
description: "全面解析 Worktrunk (4k Stars)：专为并行运行 AI Agent 设计的 Git Worktree 管理器。wt switch/list/merge/remove 四个核心命令，支持 Hooks 自动化、LLM Commit、Merge Workflow。"
---

# Worktrunk：AI 并行开发 Git Worktree 管理器完全指南

## §1 学习目标

完成本文档后，你将能够：

- ✅ 理解 Worktrunk 的核心定位与设计理念
- ✅ 掌握 Worktrunk 的四个核心命令（switch/list/merge/remove）
- ✅ 熟练使用 Hooks 实现自动化工作流
- ✅ 配置 LLM Commit Messages 自动生成提交信息
- ✅ 使用 Merge Workflow 一键合并分支
- ✅ 启动多个 AI Agent 并行开发
- ✅ 调试和排查 Worktrunk 问题
- ✅ 为 Worktrunk 贡献代码

---

## §2 项目概述

### 2.1 什么是 Worktrunk？

**Worktrunk**（官方仓库：[max-sixty/worktrunk](https://github.com/max-sixty/worktrunk)）是一个 **Git Worktree 管理 CLI 工具**，专门为**并行运行 AI Agent** 而设计。

**官方描述**：

> Worktrunk is a CLI for git worktree management, designed for running AI agents in parallel. Worktrunk's three core commands make worktrees as easy as branches. Plus, Worktrunk has a bunch of quality-of-life features to simplify working with many parallel changes, including hooks to automate local workflows.

**翻译**：Worktrunk 是一个用于 Git Worktree 管理的 CLI，专门为并行运行 AI Agent 设计。Worktrunk 的三个核心命令让 Worktree 使用起来和普通分支一样简单。此外，Worktrunk 还有大量提升体验的功能，简化多并行变更的工作流程，包括 Hooks 来自动化本地工作流。

### 2.2 为什么需要 Worktrunk？

**Git Worktree 的痛点**

Git 原生的 Worktree 命令 UX 很繁琐。即使是创建一个新 Worktree 这样的小任务，也需要输入三次分支名：

```bash
git worktree add -b feat ../repo.feat
cd ../repo.feat
```

**Worktrunk 的解决方案**

Worktree 通过分支名寻址，路径由可配置模板自动计算：

| 任务 | Worktrunk | 原生 Git |
|------|-----------|----------|
| 切换 Worktree | `wt switch feat` | `cd ../repo.feat` |
| 创建并启动 Claude | `wt switch -c -x claude feat` | 繁琐的 3 步命令 |
| 清理 | `wt remove` | 多步操作 |
| 列出状态 | `wt list` | `git worktree list`（只显示路径）|

### 2.3 核心数据

```
Stars:     4,000 (4k)
Forks:     129
Watchers:  5
贡献者:    35 人
提交数:   3,267 次
分支数:    62 个
标签数:    95 个
发布版本:  94 个
最新版本:  v0.33.0 (2026-03-27)
许可证:    MIT OR Apache-2.0
语言:      Rust 99.4%
```

### 2.4 项目时间线

| 时间 | 事件 |
|------|------|
| 2025年 | 项目启动 |
| 2026年3月 | 正式发布，迅速成为最受欢迎的 Git Worktree 管理器 |

---

## §3 核心命令详解

### 3.1 wt switch — 切换/创建 Worktree

**基本用法**

```bash
# 切换到已存在的 worktree
wt switch feat

# 创建并切换到新 worktree
wt switch --create feature-auth
wt switch -c feature-auth
```

**创建并运行命令**

```bash
# -x 运行命令（agent），-c 创建分支
wt switch -x claude -c feature-a -- 'Add user authentication'
```

这会：
1. 从 main 创建新分支 feature-a
2. 创建 worktree
3. 在新 worktree 中启动 Claude

**参数说明**

| 参数 | 说明 |
|------|------|
| `-c, --create` | 创建新分支和 worktree |
| `-x, --exec` | 创建后执行命令 |
| `--` | 分隔参数，-- 后面的传给命令 |

### 3.2 wt list — 列出 Worktree

**基本用法**

```bash
# 简洁列表
wt list

# 完整模式（显示状态、提交信息、CI）
wt list --full
```

**输出示例**

```
Branch       Status  HEAD±  Remote⇅  Commit  Age    Message
@ feature-auth  +     ↑+27   -8     ↑1     4bc72dc9  2h    Add authentication module
^ main           ↕     ⇡     ⇡1     0e631add  1d    Initial commit

○ Showing 2 worktrees, 1 with changes, 1 ahead, 1 column hidden
```

**状态符号说明**

| 符号 | 含义 |
|------|------|
| `@` | 当前 worktree |
| `+` | 有 staged 变更 |
| `↑N` | 领先 N 个提交 |
| `⇡` | 有未推送提交 |
| `○` | 干净的 worktree |

### 3.3 wt merge — 合并分支

**基本用法**

```bash
# 合并到 main
wt merge main
```

**Merge Workflow 自动执行**

1. 生成提交信息（LLM）
2. 提交变更
3. Rebase 或 merge 到目标分支
4. 清理（删除 worktree 和分支）

### 3.4 wt remove — 清理 Worktree

**基本用法**

```bash
# 删除当前 worktree（需先切换到其他）
wt remove

# 删除指定的 worktree
wt remove feature-auth
```

---

## §4 AI Agent 并行开发

### 4.1 核心概念

AI Agent（如 Claude Code、Codex）可以处理更长的任务而不需要监督，因此**同时管理 5-10+ 个并行的 Agent** 成为可能。

Git 的原生 Worktree 功能给每个 Agent 自己的工作目录，这样它们不会互相踩踏对方的变更。

### 4.2 启动多个 Agent

```bash
# 并行启动三个 Agent
wt switch -x claude -c feature-a -- 'Add user authentication'
wt switch -x claude -c feature-b -- 'Fix the pagination bug'
wt switch -x claude -c feature-c -- 'Write tests for the API'
```

### 4.3 配置 post-start Hooks

配置 `post-start` Hooks 来自动化设置（安装依赖、启动开发服务器等）：

```yaml
# .worktrunk.yaml
hooks:
  post-start:
    - command: npm install
    - command: npm run dev
```

---

## §5 Hooks 自动化

### 5.1 支持的 Hook 类型

| Hook | 触发时机 |
|------|----------|
| `post-create` | Worktree 创建后 |
| `post-switch` | 切换到 worktree 后 |
| `pre-merge` | 合并前 |
| `post-merge` | 合并后 |
| `post-remove` | Worktree 删除后 |

### 5.2 配置示例

```yaml
# .worktrunk.yaml
hooks:
  post-create:
    - command: npm install
      description: Install dependencies
  
  post-switch:
    - command: echo "Switched to $(wt list --current)"
      description: Log switch
  
  post-merge:
    - command: npm test
      description: Run tests after merge
```

### 5.3 自动化开发服务器

每个 worktree 有唯一端口：

```yaml
hooks:
  post-create:
    - command: npm run dev -- --port {{ hash_port }}
      description: Start dev server on unique port
```

---

## §6 LLM Commit Messages

### 6.1 功能说明

Worktrunk 可以使用 LLM（通过 OpenAI/Anthropic API）自动从 diff 生成有意义的提交信息。

### 6.2 配置

```yaml
# .worktrunk.yaml
llm:
  provider: anthropic  # 或 openai
  model: claude-sonnet-4-5
  auto-commit: true
```

### 6.3 使用

```bash
# 自动生成并提交
wt merge main
# 输出：
# ✓ Generating commit message... (2 files, +53)
# Add authentication module
```

---

## §7 安装与配置

### 7.1 安装方式

**Homebrew（macOS & Linux）**

```bash
brew install worktrunk
wt config shell install
```

**Cargo**

```bash
cargo install worktrunk
wt config shell install
```

**Arch Linux**

```bash
paru worktrunk-bin
wt config shell install
```

### 7.2 Shell 集成

安装后运行：

```bash
wt config shell install
```

这允许命令自动切换目录。

### 7.3 配置文件

Worktrunk 使用 `.worktrunk.yaml` 作为配置文件：

```yaml
# .worktrunk.yaml
template: "{repo}.{branch}"  # worktree 路径模板
default-branch: main           # 默认分支
hooks:
  post-create:
    - command: npm install

llm:
  provider: anthropic
  model: claude-sonnet-4-5
```

---

## §8 进阶功能

### 8.1 Interactive Picker

交互式选择器，支持实时预览 diff 和日志：

```bash
wt switch --interactive
# 或简写
wt switch -i
```

### 8.2 PR/MR Checkout

直接跳转到 PR 的分支：

```bash
wt switch pr:123      # GitHub PR
wt switch mr:456       # GitLab MR
```

### 8.3 Copy Build Caches

在 worktrees 之间共享构建缓存：

```yaml
# .worktrunk.yaml
copy-build-caches:
  - target/
  - node_modules/
  - .venv/
```

跳过冷启动。

### 8.4 wt list --full

完整模式显示：

- CI 状态
- 每个分支的 AI 生成摘要

### 8.5 Dev Server Per Worktree

每个 worktree 有唯一端口（使用 `hash_port` 模板过滤器）。

---

## §9 工作流示例

### 9.1 PR 工作流

```bash
# 1. 创建特性分支
wt switch --create feature-auth

# 2. Agent 在此分支工作
# ...

# 3. 提交、推送、创建 PR
wt step commit
gh pr create

# 4. PR 合并后自动清理
# （PR 合并后）
wt remove
```

### 9.2 本地合并工作流

```bash
# 1. 创建特性分支并切换
wt switch --create feature-auth

# 2. Agent 在此分支工作
# ...

# 3. 自动生成提交信息、rebase、合并、清理
wt merge main
```

### 9.3 并行 Agent 工作流

```bash
# 并行启动多个 Agent
wt switch -x claude -c feature-auth -- 'Add authentication'
wt switch -x claude -c feature-api -- 'Create API endpoints'
wt switch -x claude -c feature-ui -- 'Build dashboard'

# 每个 Agent 在独立 worktree 中工作
# 互不干扰

# 完成后的合并
wt merge main  # 对每个分支依次执行
```

---

## §10 项目结构

### 10.1 仓库结构

| 目录 | 说明 |
|------|------|
| `.cargo/` | Rust 构建配置 |
| `.claude-plugin/` | Claude 插件配置 |
| `.claude/skills/` | Claude Skills |
| `.config/` | 项目配置 |
| `.github/` | GitHub Actions CI/CD |
| `benches/` | 性能基准测试 |
| `dev/` | 开发文件 |
| `docs/` | 文档 |
| `nix/` | Nix 打包 |
| `skills/worktrunk/` | Worktrunk Skills |
| `src/` | 源代码 |
| `templates/` | 模板 |
| `tests/` | 测试 |

### 10.2 核心源文件

| 文件 | 说明 |
|------|------|
| `src/main.rs` | CLI 入口 |
| `src/commands/` | 命令实现 |
| `src/worktree.rs` | Worktree 管理 |
| `src/hooks.rs` | Hook 执行 |
| `src/llm.rs` | LLM 集成 |

---

## §11 常见问题

### Q1：Worktrunk 和 git-worktree 有什么区别？

| 特性 | Worktrunk | 原生 git worktree |
|------|-----------|------------------|
| 创建 worktree | `wt switch -c feat` | `git worktree add -b feat ../repo.feat && cd ../repo.feat` |
| 切换 worktree | `wt switch feat` | `cd ../repo.feat` |
| 清理 worktree | `wt remove` | 多步手动操作 |
| Hooks | ✅ 支持 | ❌ 不支持 |
| LLM Commit | ✅ 支持 | ❌ 不支持 |
| 并行 Agent | ✅ 专为 AI Agent 设计 | 需要手动管理 |

### Q2：Worktrunk 支持哪些 Git 平台？

| 平台 | 支持情况 |
|------|----------|
| **GitHub** | ✅ 完整支持（PR） |
| **GitLab** | ✅ 支持（MR） |
| **Gitea** | ✅ 支持 |
| **其他** | ✅ 通过 generic MR/PR 兼容 |

### Q3：如何调试 Worktrunk？

```bash
# 查看详细输出
wt switch -vvv feat

# 查看当前配置
wt config show

# 查看所有 worktree
wt list --verbose
```

### Q4：Worktrunk 和 Zellij 集成？

Worktrunk 支持在 Zellij（终端多路复用器）中显示多个 Agent：

```bash
# 使用 Zellij 作为终端复用器
wt switch -x 'zellij attach -c' -c feature-a
```

### Q5：如何贡献 Worktrunk？

1. ⭐ Star 仓库
2. 反馈问题（哪怕是小摩擦或不完美的用户体验）
3. Fork 并提交 PR

### Q6：支持 Windows 吗？

**部分支持**。Windows 支持仍在完善中，主要通过 WSL 使用。

---

## §12 术语表

| 术语 | 说明 |
|------|------|
| **Worktree** | Git 工作树，允许在同一仓库有多个工作目录 |
| **Branch** | Git 分支 |
| **Hook** | 在特定时机自动执行的脚本 |
| **LLM Commit** | 使用 LLM 从 diff 自动生成的提交信息 |
| **Worktree Path Template** | Worktree 路径的命名模式 |

---

## §13 总结

### 13.1 核心价值

| 价值 | 说明 |
|------|------|
| **极简命令** | 三个核心命令替代繁琐的原生 Git 操作 |
| **AI Agent 友好** | 专为并行运行 AI Agent 设计 |
| **自动化 Hooks** | 自动化本地工作流 |
| **LLM 集成** | 自动生成有意义的提交信息 |
| **快速上手** | 安装简单，命令直观 |

### 13.2 适用场景

| 场景 | 推荐指数 |
|------|----------|
| 并行 AI Agent 开发 | ⭐⭐⭐⭐⭐ |
| 多特性并行开发 | ⭐⭐⭐⭐⭐ |
| 代码审查准备 | ⭐⭐⭐⭐ |
| 热修复分支管理 | ⭐⭐⭐⭐ |

### 13.3 项目信息

- Stars：4k
- Forks：129
- 贡献者：35 人
- 最新版本：v0.33.0 (2026-03-27)
- 许可证：MIT OR Apache-2.0

### 13.4 相关资源

| 资源 | 链接 |
|------|------|
| 官方网站 | https://worktrunk.dev |
| GitHub | https://github.com/max-sixty/worktrunk |
| 文档 | https://worktrunk.dev |
| Crates.io | https://crates.io/crates/worktrunk |

---

*文档版本 1.0 | 撰写日期：2026-03-31 | 基于 v0.33.0 (2026-03-27) | Stars: 4k ⭐*