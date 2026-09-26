---
title: "Beads：给 AI 编程 Agent 用的分布式图结构 Issue 追踪器，Powered by Dolt"
date: "2026-04-27T01:14:00+08:00"
lastmod: "2026-09-24T10:00:00+08:00"
slug: beads-ai-agent-issue-tracker
github_repo: "gastownhall/beads"
source_key: "gh:gastownhall/beads"
description: "Beads 是一个 AI 编程 Agent 的持久化记忆工具，用 Dolt（版本控制 SQL 数据库）取代杂乱的 Markdown 计划。依赖感知图结构、自动-ready 任务检测、语义压缩防止上下文窗口溢出。支持多 Agent 和多分支工作流，Hash ID 防止合并冲突。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Go", "多Agent协作"]
---

# Beads：给 AI 编程 Agent 用的分布式图结构 Issue 追踪器，Powered by Dolt

AI 编程 Agent 跑长周期任务时，记忆会丢。上下文窗口有限，Markdown 计划写到后面自己都看不懂，任务之间的依赖关系埋在自然语言里，多 Agent 协作时还要抢同一个文件。Beads 把这个问题当成存储与并发问题来解：用 Dolt（版本控制 SQL 数据库）做后端，把任务图存成结构化数据，让 Agent 之间能像 git 分支一样并行工作。

Beads 由 Steve Yegge 创建，2025 年 10 月开源，Go 实现，单 CLI 工具（`bd`）装一次所有项目都能用。本文判断它为什么值得看，拆开四层并行机制，给一个任务流案例和采用顺序建议。文中机制与命令以 v1.3.0（2026-09-15 发布）和 2026-09-24 的仓库状态为口径。

> **快速信息卡**
> - **GitHub**: [gastownhall/beads](https://github.com/gastownhall/beads)
> - **Stars**: 27,393（2026-09-24 查询）
> - **Forks**: 1,854
> - **License**: MIT
> - **语言**: Go
> - **最新版本**: v1.3.0（2026-09-15）
> - **最后更新**: 2026-09-23

## 学习目标

读完本文应能：

- 说清 Beads 用 Dolt 做后端的核心原因，以及 cell-level merge 如何解决多 Agent 写冲突
- 识别 Beads 的四层并行机制（存储层、ID 层、协作层、上下文层）各解决什么问题
- 对照传统 Markdown 计划文件，判断 Beads 在哪些环节做了结构化改进
- 完成一个"创建任务 → 建立依赖 → 查询 ready → 认领 → 关闭"的完整任务流
- 评估把 Beads 引入 AI Agent 工作流的适用场景和风险

## 目录

- [快速信息卡](#快速信息卡)
- [总览：Beads 的四层并行机制](#总览beads-的四层并行机制)
- [为什么 AI Agent 需要专门的 Issue 追踪器](#为什么-ai-agent-需要专门的-issue-追踪器)
- [存储层：Dolt 驱动的 SQL 后端](#存储层dolt-驱动的-sql-后端)
- [ID 层：Hash ID 与层级结构](#id-层hash-id-与层级结构)
- [协作层：角色、存储模式与 Git-Free](#协作层角色存储模式与-git-free)
- [上下文层：记忆、语义压缩与消息类型](#上下文层记忆语义压缩与消息类型)
- [任务流案例](#任务流案例)
- [快速开始](#快速开始)
- [与传统 Issue 追踪工具对比](#与传统-issue-追踪工具对比)
- [采用建议](#采用建议)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [常见问题](#常见问题)

## 总览：Beads 的四层并行机制

Beads 不是把 Markdown 换成 SQL 这么简单。它把"Agent 任务管理"拆成四层可以独立讨论的机制，每层解决一个具体问题：

| 层 | 解决的问题 | 关键机制 |
|------|------|------|
| 存储层 | 多 Agent 写冲突、历史不可回溯 | Dolt cell-level merge + 原生分支 |
| ID 层 | 自增 ID 合并必冲突 | Hash-based ID（`bd-a3f8`）+ 层级 ID |
| 协作层 | 角色与仓库边界 | Contributor/Maintainer 自动检测、Git-Free 模式 |
| 上下文层 | 旧任务撑爆上下文窗口 | `bd prime`/`bd remember`、语义压缩（Memory Decay）+ Message 类型 |

下面按这四层展开，再给一个任务从创建到完成的完整流程，最后是采用建议。

## 为什么 AI Agent 需要专门的 Issue 追踪器

先看现有 AI Coding Agent 的任务管理方式实际跑长任务时会遇到什么：

- **Markdown 计划文件**：任务推进后内容越改越乱，依赖关系只能靠自然语言描述，Agent 重读时容易漏掉
- **上下文窗口限制**：长任务的历史信息累积到一定程度会挤掉当前需要的上下文
- **多 Agent 冲突**：多个 Agent 改同一个计划文件，合并时要么靠锁串行，要么手动解决冲突
- **缺乏结构**：任务之间的 `blocks`、`relates-to`、`duplicates` 关系无法在文件里直接表达

为什么 Markdown 不够用？因为 Markdown 是写给人读的文档，没有 schema，没有事务，没有合并语义。Agent 需要的是可以查询、可以原子更新、可以并行写入的结构化存储。Beads 选 Dolt 的原因就在这里：它既是 SQL 数据库，又是 git 风格的版本控制系统，cell-level merge 让字段级的修改可以自动合并。

## 存储层：Dolt 驱动的 SQL 后端

Beads 基于 Dolt。Dolt 的关键能力直接决定了 Beads 能做什么：

- **Cell-level merge**：合并粒度到单元格级别。两个 Agent 同时改同一个任务的不同字段（一个改 status，一个改 assignee）能自动合并，不需要手动解冲突
- **原生分支**：每个任务图可以有分支，实验性工作不影响主线，分支可以 merge 回主分支
- **内置同步**：通过 Dolt remotes 实现数据同步，多机器协作时不需要自己搭同步层
- **SQL 查询**：所有数据是结构化 SQL，Agent 可以直接解析 JSON 输出

跨机器同步走 `bd dolt push` / `bd dolt pull`，数据推到 git remote 的 `refs/dolt/data` 引用上。注意 `.beads/issues.jsonl` 这个文件只是给查看器和数据交换用的导出件，官方明确它既不是数据源也不是备份——真值始终在 Dolt 数据库里。

这层还藏着一个实用设计：**Schema 版本守卫**。`bd` 在打开数据库时检查 schema 版本，如果数据库被更新的二进制迁移过、旧二进制试图打开，`bd` 会直接报出可执行的错误提示（"database is at v45, binary knows up to v42"），而不是抛一堆晦涩的 SQL 错误。确实要强行继续时，`BD_IGNORE_SCHEMA_SKEW=1` 是官方留的逃生门。

为什么这层重要？因为多 Agent 协作的核心痛点是写冲突。传统方案要么文件锁串行（慢），要么手动 merge（不可靠）。Dolt 的 cell-level merge 让并发写成为默认能力，Agent 不需要额外设计同步逻辑。

## ID 层：Hash ID 与层级结构

### Hash-based ID 防冲突

Beads 用 `bd-a3f8` 这样的 Hash ID 替代自增 ID。原因：自增 ID 在多分支合并时必然冲突（两个分支都创建了 ID=5 的任务），Hash ID 天然全局唯一，合并时不需要重新编号。README 把这条列为 "Zero Conflict" 特性。

### 层级 ID 表达 epic-task-subtask

Beads 支持层级 ID，用于表达任务的结构关系：

```text
bd-a3f8       # Epic（史诗级大任务）
bd-a3f8.1     # Task（Epic 下的子任务）
bd-a3f8.1.1   # Sub-task（再下一级）
```

层级 ID 不是创建任务时自动生成的，需要用 `bd create --parent <epic-id>` 显式挂到父任务下面。挂上之后，Agent 看 ID 就知道"这个任务属于哪个 Epic"，不需要额外查依赖表。

### 图关系链接

除了层级关系，Beads 还支持完整的任务关系建模：

- `relates-to`：关联
- `duplicates`：重复
- `supersedes`：替代
- `replies-to`：回复

这些关系存在 SQL 表里，可以查询。比如"找出所有被 `bd-a3f8` supersede 的旧任务"是一条 SQL，不需要 Agent 通读全文找。依赖关系本身也是一种类型化的边：`bd dep add` 的 `--type` 参数支持 `blocks`、`tracks`、`parent-child`、`discovered-from` 等多种类型，默认 `blocks`。

## 协作层：角色、存储模式与 Git-Free

### Contributor vs Maintainer

在开源项目中工作，两种角色走不同路径：

**Contributor（fork 的仓库）**：运行 `bd init --contributor`，规划任务路由到独立数据库（例如 `~/.beads-planning`），保持实验性工作不进 PR。

**Maintainer（有写权限的仓库）**：Beads 自动检测 maintainer 角色（通过 SSH URL 或带凭证的 HTTPS）。只有在使用无凭证的 GitHub HTTPS 但有写权限时才需要手动配置 `git config beads.role maintainer`。

为什么需要区分？因为 Contributor 不能把规划数据库推到上游仓库，否则会污染 PR。Beads 用角色检测把规划数据路由到本地独立数据库，让 PR 只包含代码改动。

### 存储模式：Embedded vs Server

**Embedded 模式（默认）**：

```bash
bd init
```

Dolt 进程内运行，不需要外部服务器。数据存储在 `.beads/embeddeddolt/`。单 writer，通过文件锁强制——同一时刻只有一个进程可以写。

**Server 模式**：

```bash
bd init --server
```

连接外部 `dolt sql-server`。数据存储在 `.beads/dolt/`。支持多个并发 writer。

Server 模式连接参数：

| Flag | Env Var | Default |
|------|---------|---------|
| `--server-host` | `BEADS_DOLT_SERVER_HOST` | `127.0.0.1` |
| `--server-port` | `BEADS_DOLT_SERVER_PORT` | `3307` |
| `--server-socket` | `BEADS_DOLT_SERVER_SOCKET` | (none; uses TCP) |
| `--server-user` | `BEADS_DOLT_SERVER_USER` | `root` |
| | `BEADS_DOLT_PASSWORD` | (none) |

**Unix domain socket 支持**：用 `--server-socket` 替代 TCP，避免端口冲突。Dolt 服务器需以 `dolt sql-server --socket <path>` 启动。

为什么默认 Embedded？单 Agent 场景下进程内运行免去了维护数据库服务的负担，官方也明确 Embedded "recommended for most users"；Server 模式留给多 Agent 并发写的场景。

### Git-Free 模式

Beads 可以完全脱离 git 工作：

```bash
export BEADS_DIR=/path/to/your/project/.beads
bd init --quiet --stealth
```

`BEADS_DIR` 指定 `.beads/` 数据库目录位置，绕过 git 仓库发现。`--stealth` 设置 `no-git-ops: true`，禁用所有 git hook 安装和 git 操作。

适用场景：

- **非 git VCS**：Sapling、Jujutsu、Piper
- **Monorepos**：指向特定子目录
- **CI/CD**：隔离的任务追踪，无仓库级副作用
- **评估/测试**：`/tmp` 中的临时数据库

## 上下文层：记忆、语义压缩与消息类型

### 项目记忆：bd prime 与 bd remember

Beads 对自己的定位是 "a memory upgrade for your coding agent"，除了任务管理，它还有专门的记忆机制：

- `bd remember "insight"`：把一条项目洞察存进数据库，成为持久记忆
- `bd prime`：打印工作流上下文和已存记忆，Agent 每次开工时跑一遍就能接上上下文

官方给 Agent 的集成模板里明确写着"用 `bd remember` 存持久记忆，不要建 MEMORY.md 文件"——记忆放在图结构里，可以被查询、跟着数据库走，而不是散落在 Markdown 文件里。

### 语义压缩（Memory Decay）

长时间运行的项目，关闭的旧任务会累积占用上下文窗口。Beads 的处理方式是语义压缩：把关闭已久的旧任务摘要化，保留关键信息，大幅减少 token 占用。

有几个精确的边界值得知道：

- 压缩是**永久性的**（官方原话 "permanent graceful decay"）——摘要生成后原始内容会被丢弃，不是"随时可以展开还原"
- 官方 Tier 1 档位对关闭超过 30 天的任务做语义压缩，宣称约 70% 的体积缩减；更激进的 Tier 2（90 天）在文档里标注为规划中、尚未实现
- 触发命令是 `bd admin compact`，有三种模式：Analyze（导出压缩候选清单供 Agent 审查，不需要 API key）、Apply（采纳 Agent 生成的摘要）、Auto（AI 全自动压缩，需要 `ANTHROPIC_API_KEY`）

为什么需要这层？Agent 重读项目历史时不需要看每一条旧任务的全文，只需要知道"这个任务做过什么、结果是什么"。压缩后 token 占用下降，Agent 能在有限上下文窗口里处理更长的项目历史。

### 消息类型（Messaging）

Beads 支持一种特殊的 issue 类型——**Message**：

- 支持 threading（`--thread`）
- 有临时生命周期（ephemeral lifecycle）
- 可以委托处理（mail delegation）

为什么要在任务追踪系统里加消息类型？因为 Agent 之间的讨论和通知本来就和任务状态变更耦合在一起。如果讨论在 IM 里、任务在 Issue 里，Agent 要在两个系统之间同步上下文。Message 类型让讨论和任务共享同一个图结构，`replies-to` 关系可以直接表达"这条消息是回复哪个任务的"。

## 任务流案例：一个 P0 任务从创建到完成

把上面四层串起来。假设一个多 Agent 项目里，需要修复一个 P0 bug，流程如下（为便于阅读，ID 沿用 README 的示例 `bd-a3f8`；实际创建时 `bd` 生成随机 Hash ID）：

```bash
# 1. 创建 Epic
bd create "Fix login timeout bug" -t epic
# 输出：Created bd-a3f8

# 2. 在 Epic 下拆子任务（--parent 生成层级 ID），并建立依赖
bd create "Reproduce in staging" --parent bd-a3f8 -p 0
# 输出：Created bd-a3f8.1
bd create "Patch retry logic" --parent bd-a3f8 -p 0
# 输出：Created bd-a3f8.2

# bd dep add <A> <B> 的语义是"A 依赖 B"（B 未完成时 A 不可认领）
# 复现（.1）完成之前，改补丁（.2）不该开工：
bd dep add bd-a3f8.2 bd-a3f8.1
# 等价写法：bd dep bd-a3f8.1 --blocks bd-a3f8.2

# 3. Agent A 认领复现任务（原子操作：同时设置 assignee 与 in_progress）
bd update bd-a3f8.1 --claim

# 4. Agent B 查询可认领的任务
bd ready
# bd-a3f8.2 有未解除的 blocker，不会出现在列表里

# 5. Agent A 完成复现，关闭任务（关闭即释放 blocker）
bd close bd-a3f8.1 "Reproduced: retry loop never backs off"

# 6. bd-a3f8.2 解锁，出现在 bd ready，Agent B 认领
bd ready
bd update bd-a3f8.2 --claim

# 7. 修复完成，关闭子任务
bd close bd-a3f8.2 "Retry cap fixed"

# 8. 子任务全部关闭后，检查并关闭 Epic
bd epic status
bd epic close-eligible --dry-run   # 预览哪些 Epic 满足关闭条件
bd epic close-eligible
```

这个流程里发生了什么：

- **存储层**：Agent A 和 Agent B 同时操作，Dolt cell-level merge 保证字段级合并不冲突
- **ID 层**：`bd-a3f8.2` 这种 Hash ID 在分支合并时不会重编号；层级 ID 来自 `--parent`
- **协作层**：`--claim` 是原子操作，两个 Agent 不会同时认领同一个任务；`bd ready` 只给"真正可认领"的工作
- **上下文层**：任务关闭并超过保留期后进入语义压缩候选，Agent 重读历史时的 token 占用随之下降

顺带一提：`bd close` 支持 `--reason` 记录关闭原因、`--suggest-next` 列出 newly unblocked 的任务，还有别名 `done`。`bd update --status closed` 语法上也合法，但官方工作流模板统一用 `bd close`。

## 快速开始

### 安装

```bash
# 安装脚本（系统级 CLI，装一次到处用；不要把仓库 clone 进项目）
curl -fsSL https://raw.githubusercontent.com/gastownhall/beads/main/scripts/install.sh | bash

# Homebrew（README 推荐方式）
brew install beads

# npm（Node.js 用户）
npm install -g @beads/bd
```

支持 macOS、Linux、Windows、FreeBSD。

Go 开发者也可以用 `go install`，但要注意两点：模块路径仍是 `github.com/steveyegge/beads`（仓库已迁到 gastownhall org，Go 模块路径为兼容保持不变）；且编译模式决定能力——`CGO_ENABLED=0 go install github.com/steveyegge/beads/cmd/bd@latest` 得到的是仅 Server 模式的二进制（必须外接 `dolt sql-server`），要默认的 Embedded 后端得用 `CGO_ENABLED=1 GOFLAGS=-tags=gms_pure_go go install github.com/steveyegge/beads/cmd/bd@latest`。不需要特别理由的话，Homebrew/npm/脚本三选一即可。

### 初始化

```bash
# 在项目里初始化；bd init 默认创建或更新 AGENTS.md，让 Agent 发现 beads 工作流
cd your-project
bd init

# 为特定 Agent 安装更完整的集成
bd setup claude   # Claude Code：hooks/settings
bd setup codex    # Codex CLI：skill + AGENTS.md guidance + hooks
bd setup --list   # 查看全部支持：cursor、factory、mux 等
```

如果用的 Agent 不在 `bd setup` 覆盖范围内，`bd onboard` 会打印一段可直接粘贴的说明片段。

### 核心命令

| 命令 | 动作 |
|------|------|
| `bd ready` | 列出没有未解除 blocker 的任务 |
| `bd create "Title" -p 0` | 创建 P0 任务 |
| `bd update <id> --claim` | 原子性认领任务（设置 assignee + in_progress）|
| `bd dep add <A> <B>` | 建立依赖（A 依赖 B；类型支持 blocks/parent-child/related 等）|
| `bd close <id>` | 关闭任务并释放 blocker |
| `bd show <id>` | 查看任务详情和审计轨迹 |
| `bd prime` | 打印工作流上下文与持久记忆 |
| `bd remember "insight"` | 存一条项目记忆，供 `bd prime` 注入 |

## 与传统 Issue 追踪工具对比

| 对比项 | 传统 Issue 追踪（GitHub Issues/Jira） | Beads |
|------|------|------|
| 目标用户 | 人类 | AI Agent |
| 数据格式 | 非结构化 | 结构化 SQL |
| 依赖追踪 | 手动 link | 依赖图 + 自动 ready 检测 |
| 合并冲突 | 文件级锁/merge conflict | Hash ID，官方口径"零冲突" |
| 版本控制 | 无 | Dolt 原生版本控制 |
| 上下文压缩 | 无 | 语义压缩防止溢出 |
| 多 Agent 支持 | 差 | 原生支持 |

为什么传统工具不够？它们假设读者是人类，输出格式是 HTML/Markdown，Agent 要解析得自己写爬虫或调 API。Beads 的输出原生面向程序消费，`bd ready --json` 直接给出结构化的可认领任务列表，Agent 不需要额外适配层。

## 安全验证

在信任任何下载的二进制文件之前，验证其 checksum 与 release `checksums.txt` 一致。install 脚本安装前会默认校验 checksum；手动安装的场景需要自己做这一步。macOS 上脚本默认保留下载二进制的原始签名，本地 ad-hoc 重签名需要显式设置 `BEADS_INSTALL_RESIGN_MACOS=1` 主动开启。

## 采用建议

### 适合用 Beads 的场景

- **AI 编程 Agent 主导的项目**：Claude Code / Cursor / Copilot 等需要持久化记忆的工具
- **多 Agent 协作**：多个 Agent 同时在同一个项目上工作，需要并发写不冲突
- **长周期项目**：语义压缩防止上下文窗口溢出，旧任务不会挤掉当前上下文
- **Monorepo**：复杂的依赖关系管理，Git-Free 模式可以指向特定子目录
- **开源贡献**：Contributor 模式下规划工作不影响 PR

### 不适合的场景

- **纯人类团队、不用 AI Agent**：传统 Issue 追踪器更顺手，Beads 的输出面向程序而非人
- **任务量极小**：单文件 Markdown 就能搞定，引入 Dolt 后端是过度设计
- **需要严格权限管理**：Beads 目前没有 Jira 那种细粒度权限体系

### 推荐采用顺序

1. 先在单 Agent 项目里跑 `bd init`，用 `bd create` / `bd ready` / `bd update --claim` / `bd close` 跑通基本流程
2. 让 Agent 用 `bd remember` 存项目记忆，观察 `bd prime` 注入上下文的效果
3. 任务量上来后用 `bd admin compact` 的 Analyze 模式评估语义压缩收益，再决定是否 Apply
4. 多 Agent 协作时切到 Server 模式，让多个 writer 并发
5. 开源协作场景再引入 Contributor/Maintainer 角色区分

---

## 自测题

1. **Beads 的四层并行机制各解决什么问题？**
   - 参考答案：存储层（多 Agent 写冲突、历史不可回溯，用 Dolt cell-level merge + 原生分支解决）；ID 层（自增 ID 合并必冲突，用 Hash-based ID + 层级 ID 解决）；协作层（角色与仓库边界，用 Contributor/Maintainer 自动检测和 Git-Free 模式解决）；上下文层（旧任务撑爆上下文窗口，用项目记忆、语义压缩和 Message 类型解决）

2. **为什么 Beads 使用 Dolt 而不是传统数据库或文件？**
   - 参考答案：Dolt 既是 SQL 数据库，又是 git 风格的版本控制系统。cell-level merge 让字段级的修改可以自动合并，原生分支支持多 Agent 并行工作，SQL 查询支持结构化数据访问，内置同步支持多机器协作。

3. **Beads 的 Hash ID 和层级 ID 各有什么作用？层级 ID 怎么产生？**
   - 参考答案：Hash ID（如 `bd-a3f8`）替代自增 ID，防止多分支合并时冲突；层级 ID（如 `bd-a3f8.1`）表达 epic-task-subtask 结构关系。层级 ID 通过 `bd create --parent <epic-id>` 显式挂载产生，不是自动生成。

4. **`bd compact` 和 `bd admin compact` 有什么区别？**
   - 参考答案：`bd compact` 是 Dolt 提交历史的 squash（把 N 天前的 commit 合并成一个，存储优化）；`bd admin compact` 才是语义压缩（把关闭已久的旧任务摘要化，减少 token 占用）。语义压缩是永久性的——摘要生成后原始内容被丢弃。

5. **如果你想评估 Beads 是否适合你的团队，你会从哪几个方面测试？**
   - 参考答案：1) 在单 Agent 项目里跑 `bd init`，用基本命令跑通流程；2) 让 Agent 用 `bd remember`/`bd prime` 验证记忆注入效果；3) 用 `bd admin compact` 的 Analyze 模式评估语义压缩收益；4) 多 Agent 协作时切到 Server 模式测试并发写；5) 开源协作场景验证 Contributor 角色隔离。

---

## 进阶路径

### 阶段一：快速验证（1 周）
- 目标：理解 Beads 的基本机制和核心命令
- 行动：安装 Beads，运行 `bd init`，用 `bd create` / `bd ready` / `bd update --claim` / `bd close` 跑通基本流程
- 验收：能解释 Beads 的四层并行机制，熟练使用基本命令

### 阶段二：实际项目试用（2-4 周）
- 目标：在真实项目中用 Beads 管理任务，评估适用边界
- 行动：在真实 AI Agent 项目中配置 Beads，观察多 Agent 协作时的写冲突处理，用 `bd admin compact` Analyze 模式评估语义压缩效果
- 验收：能判断 Beads 是否适合团队的工作流，识别需要人工介入的场景

### 阶段三：高级功能与定制化（1-3 个月）
- 目标：理解 Embedded vs Server 模式、Contributor/Maintainer 角色、Git-Free 模式
- 行动：阅读 Dolt 后端指南（`docs/architecture/dolt.md`），尝试 Server 模式多 Agent 并发写与 Unix socket 连接，配置 Contributor/Maintainer 角色区分
- 验收：能根据团队规模和工作流选择合适的存储模式和角色配置

### 阶段四：生态扩展与贡献（长期）
- 目标：与现有工具链集成，贡献到 Beads 项目
- 行动：用 `bd setup` 接入 Claude Code/Codex/Cursor 等 Agent，把 `bd dolt push/pull` 同步纳入 CI/CD 流程；关注 `docs/community-tools.md` 里的社区 UI 与编辑器扩展；提交 PR 改进文档或功能
- 验收：能把 Beads 完整接入团队的 AI Agent 工作流，并能贡献改进

---

## 常见问题

### Q1: Beads 和 GitHub Issues 有什么区别？
**A**: GitHub Issues 设计给人用，Beads 设计给 AI Agent 用。Beads 的数据是结构化 SQL，支持依赖图与自动 ready 检测、原子认领、语义压缩、Hash ID 防冲突、Dolt 版本控制，这些功能对 AI Agent 协作至关重要。

### Q2: Embedded 模式和 Server 模式有什么区别？
**A**: Embedded 模式（默认）在进程内运行 Dolt，单 writer（文件锁强制），不需要外部服务器，适合单 Agent；Server 模式连接外部 `dolt sql-server`，支持多个并发 writer，适合多 Agent 协作。跨机器同步两种模式都走 `bd dolt push/pull`。

### Q3: 语义压缩是什么？怎么触发？会丢数据吗？
**A**: 语义压缩（官方称 memory decay）把关闭已久的旧任务摘要化，减少 token 占用。触发命令是 `bd admin compact`（Analyze/Apply/Auto 三种模式，Auto 需要 API key）。会丢数据——官方明确这是永久性衰减，摘要生成后原始内容被丢弃，所以官方推荐先跑 Analyze 模式人工审查候选清单。

### Q4: Beads 支持哪些 VCS？
**A**: Beads 默认与 git 集成，也支持 Git-Free 模式（完全脱离 git 工作），适用于 Sapling、Jujutsu、Piper 等非 git VCS，以及 Monorepos、CI/CD、评估/测试场景。

### Q5: 如何保证多 Agent 并发写不冲突？
**A**: 两层保障：ID 层用 Hash ID 保证多分支合并时任务 ID 不冲突；存储层用 Dolt 的 cell-level merge 保证字段级并发写自动合并（一个 Agent 改 status、另一个改 assignee，互不覆盖）。

### Q6: 升级 `bd` 二进制要注意什么？
**A**: 官方升级指引的核心步骤：先同步 remote 后端数据库并用 `bd export --all` 备份，再换二进制，然后跑 `bd info --whats-new` 和 `bd version` 确认。如果升级跨了 schema 迁移，remote 后端的数据库要由一个指定副本跑 `bd migrate` 和 `bd dolt push`，其他副本装新二进制后跑 `bd bootstrap`。旧二进制打开新 schema 的数据库时，Schema 版本守卫会拦截并给出明确指引。

---

## 相关链接

- GitHub：https://github.com/gastownhall/beads
- 文档站：https://beads.gascity.com/
- npm：https://www.npmjs.com/package/@beads/bd
- MCP Server（PyPI）：https://pypi.org/project/beads-mcp/
- 社区工具索引：https://github.com/gastownhall/beads/blob/main/docs/community-tools.md

---

## 练习

### 练习1：安装初始化并创建第一个任务

**任务**：安装 Beads，初始化任务图，创建第一个任务并查看详情。

**步骤**：
1. 安装 Beads（`brew install beads`，或用 install.sh / npm 任一渠道）
2. 在项目目录下运行 `bd init`（注意观察自动生成的 `AGENTS.md` 和 `.beads/` 目录）
3. 运行 `bd create "实现用户登录功能" -p 1` 创建第一个任务，记下生成的 Hash ID
4. 运行 `bd show <task-id>` 查看任务详情与审计轨迹

**参考答案**：
- 成功后项目目录出现 `.beads/` 目录（Embedded 模式下数据库在 `.beads/embeddeddolt/`）
- 任务 ID 是随机 Hash ID（形如 `bd-xxxx`），每次创建都不同
- `bd ready` 应该能看到这个任务——它没有 blocker，优先级 P1

---

### 练习2：依赖与 ready 检测

**任务**：创建两个任务并设置依赖，观察 `bd ready` 如何随 blocker 变化。

**步骤**：
1. 创建任务 A："实现 API 接口"；创建任务 B："编写 API 测试"，都用 `--parent` 挂到同一个 Epic 下（没有 Epic 就先 `bd create "API 模块" -t epic`）
2. 运行 `bd dep add <任务B的ID> <任务A的ID>`——B 依赖 A
3. 运行 `bd ready`，确认列表里有 A 没有 B
4. `bd update <A> --claim` 认领 A，再跑 `bd ready` 观察 in_progress 的 A 也不再出现
5. `bd close <A> "done"` 关闭 A，再跑 `bd ready` 确认 B 出现

**参考答案**：
- `bd ready` 排除的是有 open blocker、in_progress、blocked、deferred 状态的任务，只给"真正可认领"的工作
- `bd dep list <B> --direction down` 可以查看 B 的依赖；`bd dep tree <B>` 能看整棵阻塞树
- 关闭 A 的瞬间 B 的 blocker 解除——这就是 README 工作流图里 "blockers released" 那条边

---

### 练习3：体验语义压缩的安全边界

**任务**：理解语义压缩的候选评估流程，验证它是永久性操作。

**步骤**：
1. 创建几个任务，关闭它们
2. 运行 `bd admin compact --help` 查看三种模式（Analyze/Apply/Auto）的参数
3. 跑 Analyze 模式导出压缩候选清单，检查哪些任务在列
4. 在测试数据库里跑一次 Apply，再 `bd show <已压缩任务>` 对比压缩前后的内容差异

**参考答案**：
- 压缩只作用于关闭已久（Tier 1：超过 30 天）的任务，新关闭的任务不会被立即压缩
- Analyze 模式不需要 API key，它只导出候选；真正改写内容的是 Apply/Auto
- 压缩后原内容不可恢复（官方口径 "permanent graceful decay"）——这正是官方推荐先 Analyze 审查再 Apply 的原因；另注意 `bd compact` 是 Dolt 历史 squash，与语义压缩无关

---

## 资料口径说明

1. **信息来源与时效性**：本文基于 Beads GitHub 仓库（gastownhall/beads）的 README、`docs/cli-reference/` 全部 109 个命令文档、`docs/architecture/dolt.md`、`docs/getting-started/installation.md` 核实，版本口径为 v1.3.0（2026-09-15 发布），仓库数据（27,393 stars / 1,854 forks）为 2026-09-24 查询值。项目创建于 2025-10-12，处于活跃开发状态。

2. **技术细节验证**：四层机制涉及的存储模式路径、连接参数默认值、CLI 命令与 flags、依赖类型枚举、语义压缩模式与档位数字，均对照上述官方文档逐条核实。项目官方文档站为 beads.gascity.com（仓库 README 的 Docs 字段与 repo homepage 一致）。

3. **解读框架声明**："四层并行机制"是本文组织内容的解读框架，不是官方分类。官方 README 按 Features/Commands/Storage Modes/Git-Free 等主题组织，本文的四层划分是对同一组事实的另一种切法。

4. **判断与建议的边界**：本文对 Beads 适用场景的判断基于其设计目标（AI Agent 任务管理）。Beads 不适合纯人类团队的任务管理（请用 GitHub Issues、Jira 等），不适合任务量极小的单 Agent 场景（引入 Dolt 后端是过度设计），不适合需要细粒度权限管理的场景。

5. **未覆盖的内容**：本文未展开 MCP Server（PyPI 包 beads-mcp）的接入细节、多分支工作流的操作步骤、`bd mol`（molecule）等高级概念，以及 Jira/Linear/ADO 等外部同步命令。这些内容参考官方文档站的对应页面。

6. **术语使用说明**：本文使用"Issue 追踪器"、"Dolt"、"cell-level merge"、"语义压缩"等术语，首次出现时附英文原词。任务关系类型（`relates-to`、`replies-to` 等）沿用 README 的连字符拼写。
