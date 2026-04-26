---
title: "Beads：给 AI 编程 Agent 用的分布式图结构 Issue 追踪器，Powered by Dolt"
date: 2026-04-27T01:14:00+08:00
slug: beads-ai-agent-issue-tracker
description: "Beads 是一个 AI 编程 Agent 的持久化记忆工具，用 Dolt（版本控制 SQL 数据库）取代杂乱的 Markdown 计划。依赖感知图结构、自动-ready 任务检测、语义压缩防止上下文窗口溢出。支持多 Agent 和多分支工作流，Hash ID 防止合并冲突。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Issue Tracker", "Dolt", "Task Management", "Go", "多Agent协作"]
---

# Beads：给 AI 编程 Agent 用的分布式图结构 Issue 追踪器，Powered by Dolt

AI 编程 Agent 处理长周期任务时，记忆会丢失——上下文窗口有限，Markdown 计划杂乱无章，任务之间的依赖关系不清晰，多 Agent 协作时更是一团糟。

Beads 解决这个问题。

GitHub 21.5k stars，Go 语言开发，用 Dolt（版本控制 SQL 数据库）作为存储后端，提供一个依赖感知图结构的任务追踪器，取代杂乱的 Markdown 计划。支持 cell-level merge、分支、原生同步，自动-ready 任务检测，语义压缩防止上下文窗口溢出。

**一个 CLI 工具，装一次，所有项目都能用。**

---

## 一、核心问题：AI Agent 的任务管理为什么这么难

现有 AI Coding Agent 的任务管理方式：
- **Markdown 计划文件**：随着任务推进变得杂乱，难以追踪依赖
- **上下文窗口限制**：长任务的历史信息撑爆窗口
- **多 Agent 冲突**：多个 Agent 修改同一计划文件，合并困难
- **缺乏结构**：任务之间的关系（blocks、relates_to、duplicates）无法表达

Beads 的解题思路：用结构化的图数据库替代 Markdown，用版本控制替代文件锁。

---

## 二、核心特性

### 2.1 Dolt 驱动的存储

Beads 基于 Dolt——一个版本控制的 SQL 数据库：

- **Cell-level merge**：不只是文件级合并，是单元格级别的合并
- **原生分支**：每个任务图可以有分支，实验性工作不影响主线
- **内置同步**：通过 Dolt remotes 实现数据同步
- **SQL 查询**：所有数据都是结构化的 SQL，可用 `dolt sql` 查询

### 2.2 Agent 优化的输出

- **JSON 输出**：便于 AI Agent 解析
- **依赖追踪**：自动检测任务间的 blocks/related 关系
- **自动-ready 任务检测**：`bd ready` 只列出没有 open blockers 的任务

### 2.3 零冲突设计

- **Hash-based ID**：`bd-a3f8` 这样的 ID 替代自增 ID
- **多 Agent 安全**：多个 Agent 或多个分支可以同时操作，不会合并冲突
- **语义合并**：即使两人改了同一个任务的不同字段，也能智能合并

### 2.4 语义压缩（Memory Decay）

长时间运行的项目，关闭的旧任务会积累占用上下文窗口。Beads 有自动压缩机制：

- 关闭的任务被语义压缩，保留关键信息但大幅减少 token 占用
- 保持审计追踪，必要时可以展开

### 2.5 消息类型（Messaging）

Beads 支持一种特殊的 issue 类型——**Message**：

- 支持 threading（`--thread`）
- 有临时生命周期（ephemeral lifecycle）
- 可以委托处理（mail delegation）

适合在任务追踪系统里处理讨论和通知，而不只是状态管理。

### 2.6 图关系链接

支持完整的任务关系建模：
- `relates_to`：关联
- `duplicates`：重复
- `supersedes`：替代
- `replies_to`：回复

---

## 三、层级 ID 结构

Beads 支持层级 ID，用于表达 epic-task-subtask 的结构：

```
bd-a3f8        # Epic（史诗级大任务）
bd-a3f8.1      # Task（Epic 下的子任务）
bd-a3f8.1.1    # Sub-task（再下一级）
```

---

## 四、工作模式：Contributor vs Maintainer

在开源项目中工作，两种角色：

**Contributor（fork 的仓库）**：运行 `bd init --contributor`，规划任务路由到独立数据库（例如 `~/.beads-planning`），保持实验性工作不在 PR 里出现。

**Maintainer（有写权限的仓库）**：Beads 自动检测 maintainer 角色（通过 SSH URL 或带凭证的 HTTPS）。只有在使用无凭证的 GitHub HTTPS 但有写权限时才需要手动配置 `git config beads.role maintainer`。

---

## 五、存储模式：Embedded vs Server

### Embedded 模式（默认）

```bash
bd init
```

Dolt 进程内运行，不需要外部服务器。数据存储在 `.beads/embeddeddolt/`。单 writer（通过文件锁强制）。

### Server 模式

```bash
bd init --server
```

连接外部 `dolt sql-server`。数据存储在 `.beads/dolt/`。支持多个并发 writer。

可通过 flag 或环境变量配置连接：
| Flag | Env Var | Default |
|------|---------|---------|
| `--server-host` | `BEADS_DOLT_SERVER_HOST` | `127.0.0.1` |
| `--server-port` | `BEADS_DOLT_SERVER_PORT` | `3307` |
| `--server-socket` | `BEADS_DOLT_SERVER_SOCKET` | (none; uses TCP) |

**Unix domain socket 支持**：用 `--server-socket` 替代 TCP，避免端口冲突。Dolt 服务器需以 `dolt sql-server --socket <path>` 启动。

---

## 六、Git-Free 模式

Beads 可以完全不需要 git 就能工作：

```bash
export BEADS_DIR=/path/to/your/project/.beads
bd init --quiet --stealth
```

`BEADS_DIR` 指定 `.beads/` 数据库目录位置，绕过 git 仓库发现。`--stealth` 设置 `no-git-ops: true`，禁用所有 git hook 安装和 git 操作。

适合：
- **非 git VCS**（Sapling、Jujutsu、Piper）
- **Monorepos**：指向特定子目录
- **CI/CD**：隔离的任务追踪，无仓库级副作用
- **评估/测试**：`/tmp` 中的临时数据库

---

## 七、快速开始

```bash
# 安装（系统级，不要 clone 到项目里）
curl -fsSL https://raw.githubusercontent.com/gastownhall/beads/main/scripts/install.sh | bash

# Homebrew
brew install beads

# npm（Node.js 用户）
npm install -g @beads/bd

# 在项目里初始化
cd your-project
bd init

# 告诉 Agent
echo "Use 'bd' for task tracking" >> AGENTS.md
```

### 核心命令

| 命令 | 动作 |
|------|------|
| `bd ready` | 列出没有 open blockers 的任务 |
| `bd create "Title" -p 0` | 创建 P0 任务 |
| `bd update <id> --claim` | 原子性认领任务（设置 assignee + in_progress）|
| `bd dep add <child> <parent>` | 链接任务（blocks/related/parent-child）|
| `bd show <id>` | 查看任务详情和审计轨迹 |

---

## 八、与传统 Issue 追踪工具的对比

| 对比 | 传统 Issue 追踪（GitHub Issues/Jira） | Beads |
|------|-------------------------------------|-------|
| 目标用户 | 人类 | AI Agent |
| 数据格式 | 非结构化 | 结构化 SQL |
| 依赖追踪 | 手动 link | 自动依赖图 |
| 合并冲突 | 文件级锁/merge conflict | Hash ID，零冲突 |
| 版本控制 | 无 | Dolt 原生版本控制 |
| 上下文压缩 | 无 | 语义压缩防止溢出 |
| 多 Agent 支持 | 差 | 原生支持 |

---

## 九、安全验证

在信任任何下载的二进制文件之前，验证其 checksum 与 release `checksums.txt` 一致。install 脚本默认验证 checksum。macOS 上安装脚本默认保留下载的签名。

---

## 十、适用场景

- **AI 编程 Agent**：Claude Code / Cursor / Copilot 等的记忆工具
- **多 Agent 协作**：多个 Agent 同时在同一个项目上工作，不会冲突
- **长周期项目**：语义压缩防止上下文窗口溢出
- **Monorepo**：复杂的依赖关系管理
- **开源贡献**：Contributor 模式下规划工作不影响 PR

---

## 总结

Beads 解决的是 AI Coding Agent 的记忆问题——当任务变多、时间拉长，Agent 会丢失上下文，依赖关系不清晰，多 Agent 时更有合并冲突。

用 Dolt 作为存储后端，带来版本控制、分支、cell-level merge 等特性，解决了多 Agent 协作的核心痛点。Hash ID 设计让合并冲突成为历史。语义压缩防止上下文窗口溢出。

21.5k stars，说明社区对这个方向的认可。Go 语言开发，单 CLI 工具装一次所有项目都能用。

**相关链接：**

- GitHub：https://github.com/gastownhall/beads（21.5k stars）
- 文档：https://gastownhall.github.io/beads/
- npm：https://www.npmjs.com/package/@beads/bd
- PyPI：https://pypi.org/project/beads-mcp/

🦞 每日08:00自动更新