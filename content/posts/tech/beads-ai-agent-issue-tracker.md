---
title: "Beads：给 AI 编程 Agent 用的分布式图结构 Issue 追踪器，Powered by Dolt"
date: "2026-04-27T01:14:00+08:00"
slug: beads-ai-agent-issue-tracker
description: "Beads 是一个 AI 编程 Agent 的持久化记忆工具，用 Dolt（版本控制 SQL 数据库）取代杂乱的 Markdown 计划。依赖感知图结构、自动-ready 任务检测、语义压缩防止上下文窗口溢出。支持多 Agent 和多分支工作流，Hash ID 防止合并冲突。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Issue Tracker", "Dolt", "Task Management", "Go", "多Agent协作"]
---

# Beads：给 AI 编程 Agent 用的分布式图结构 Issue 追踪器，Powered by Dolt

AI 编程 Agent 跑长周期任务时，记忆会丢。上下文窗口有限，Markdown 计划写到后面自己都看不懂，任务之间的依赖关系埋在自然语言里，多 Agent 协作时还要抢同一个文件。Beads 把这个问题当成存储与并发问题来解：用 Dolt（版本控制 SQL 数据库）做后端，把任务图存成结构化数据，让 Agent 之间能像 git 分支一样并行工作。

截至 2026-04-27，GitHub 21.5k stars，Go 实现，单 CLI 工具装一次所有项目都能用。本文判断它为什么值得看，拆开四层并行机制，给一个任务流案例和采用顺序建议。

> **快速信息卡**
> - **GitHub**: [gastownhall/beads](https://github.com/gastownhall/beads)
> - **Stars**: 24,771+
> - **Forks**: 1,660+
> - **License**: MIT
> - **语言**: Go
> - **最后更新**: 2026-06-25

## 目录

- [快速信息卡](#快速信息卡)
- [总览：Beads 的四层并行机制](#总览beads-的四层并行机制)
- [为什么 AI Agent 需要专门的 Issue 追踪器](#为什么-ai-agent-需要专门的-issue-追踪器)
- [存储层：Dolt 驱动的 SQL 后端](#存储层dolt-驱动的-sql-后端)
- [ID 层：Hash ID 与层级结构](#id-层hash-id-与层级结构)
- [协作层：角色、存储模式与 Git-Free](#协作层角色存储模式与-git-free)
- [上下文层：语义压缩与消息类型](#上下文层语义压缩与消息类型)
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
| 上下文层 | 旧任务撑爆上下文窗口 | 语义压缩（Memory Decay）+ Message 类型 |

下面按这四层展开，再给一个任务从创建到完成的完整流程，最后是采用建议。

## 为什么 AI Agent 需要专门的 Issue 追踪器

先看现有 AI Coding Agent 的任务管理方式实际跑长任务时会遇到什么：

- **Markdown 计划文件**：任务推进后内容越改越乱，依赖关系只能靠自然语言描述，Agent 重读时容易漏掉
- **上下文窗口限制**：长任务的历史信息累积到一定程度会挤掉当前需要的上下文
- **多 Agent 冲突**：多个 Agent 改同一个计划文件，合并时要么靠锁串行，要么手动解决冲突
- **缺乏结构**：任务之间的 `blocks`、`relates_to`、`duplicates` 关系无法在文件里直接表达

为什么 Markdown 不够用？因为 Markdown 是写给人读的文档，没有 schema，没有事务，没有合并语义。Agent 需要的是可以查询、可以原子更新、可以并行写入的结构化存储。Beads 选 Dolt 的原因就在这里：它既是 SQL 数据库，又是 git 风格的版本控制系统，cell-level merge 让两个字段级的修改可以自动合并。

## 存储层：Dolt 驱动的 SQL 后端

Beads 基于 Dolt。Dolt 的关键能力直接决定了 Beads 能做什么：

- **Cell-level merge**：合并粒度到单元格级别。两个 Agent 同时改同一个任务的不同字段（一个改 status，一个改 assignee）能自动合并，不需要手动解冲突
- **原生分支**：每个任务图可以有分支，实验性工作不影响主线，分支可以 merge 回主分支
- **内置同步**：通过 Dolt remotes 实现数据同步，多机器协作时不需要自己搭同步层
- **SQL 查询**：所有数据是结构化 SQL，可以用 `dolt sql` 跑任意查询，Agent 也能直接解析 JSON 输出

为什么这层重要？因为多 Agent 协作的核心痛点是写冲突。传统方案要么文件锁串行（慢），要么手动 merge（不可靠）。Dolt 的 cell-level merge 让并发写成为默认能力，Agent 不需要额外设计同步逻辑。

## ID 层：Hash ID 与层级结构

### Hash-based ID 防冲突

Beads 用 `bd-a3f8` 这样的 Hash ID 替代自增 ID。原因：自增 ID 在多分支合并时必然冲突（两个分支都创建了 ID=5 的任务），Hash ID 天然全局唯一，合并时不需要重新编号。

### 层级 ID 表达 epic-task-subtask

Beads 支持层级 ID，用于表达任务的结构关系：

```text
bd-a3f8       # Epic（史诗级大任务）
bd-a3f8.1     # Task（Epic 下的子任务）
bd-a3f8.1.1   # Sub-task（再下一级）
```

层级 ID 让 Agent 可以快速判断"这个任务属于哪个 Epic"，不需要额外查依赖表。

### 图关系链接

除了层级关系，Beads 还支持完整的任务关系建模：

- `relates_to`：关联
- `duplicates`：重复
- `supersedes`：替代
- `replies_to`：回复

这些关系存在 SQL 表里，可以查询。比如"找出所有被 `bd-a3f8` supersede 的旧任务"是一条 SQL，不需要 Agent 通读全文找。

## 协作层：角色、存储模式与 Git-Free

### Contributor vs Maintainer

在开源项目中工作，两种角色走不同路径：

**Contributor（fork 的仓库）**：运行 `bd init --contributor`，规划任务路由到独立数据库（例如 `~/.beads-planning`），保持实验性工作不在 PR 里出现。

**Maintainer（有写权限的仓库）**：Beads 自动检测 maintainer 角色（通过 SSH URL 或带凭证的 HTTPS）。只有在使用无凭证的 GitHub HTTPS 但有写权限时才需要手动配置 `git config beads.role maintainer`。

为什么需要区分？因为 Contributor 不能把规划数据库推到上游仓库，否则会污染 PR。Beads 用角色检测把规划数据路由到本地独立数据库，让 PR 只包含代码改动。

### 存储模式：Embedded vs Server

**Embedded 模式（默认）**：

```bash
bd init
```

Dolt 进程内运行，不需要外部服务器。数据存储在 `.beads/embeddeddolt/`。单 writer（通过文件锁强制）。

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

**Unix domain socket 支持**：用 `--server-socket` 替代 TCP，避免端口冲突。Dolt 服务器需以 `dolt sql-server --socket <path>` 启动。

为什么默认 Embedded？因为单 Agent 场景下进程内运行最快，不需要额外维护一个数据库服务。Server 模式留给多 Agent 并发写的场景。

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

## 上下文层：语义压缩与消息类型

### 语义压缩（Memory Decay）

长时间运行的项目，关闭的旧任务会累积占用上下文窗口。Beads 的自动压缩机制：

- 关闭的任务被语义压缩，保留关键信息但大幅减少 token 占用
- 保持审计追踪，必要时可以展开查看完整历史

为什么需要这层？因为 Agent 重读历史任务时不需要看每一条评论的全文，只需要知道"这个任务做过什么、结果是什么"。压缩后 token 占用下降，Agent 能在有限上下文窗口里处理更长的项目历史。

### 消息类型（Messaging）

Beads 支持一种特殊的 issue 类型——**Message**：

- 支持 threading（`--thread`）
- 有临时生命周期（ephemeral lifecycle）
- 可以委托处理（mail delegation）

为什么要在任务追踪系统里加消息类型？因为 Agent 之间的讨论和通知本来就和任务状态变更耦合在一起。如果讨论在 IM 里、任务在 Issue 里，Agent 要在两个系统之间同步上下文。Message 类型让讨论和任务共享同一个图结构，`replies_to` 关系可以直接表达"这条消息是回复哪个任务的"。

## 任务流案例：一个 P0 任务从创建到完成

把上面四层串起来。假设一个多 Agent 项目里，需要修复一个 P0 bug，流程如下：

```bash
# 1. 创建 Epic（Maintainer 角色，Embedded 模式）
bd create "Fix login timeout bug" -p 0
# 输出：bd-a3f8 created

# 2. 拆子任务，建立依赖
bd create "Reproduce in staging" -p 0
# 输出：bd-a3f8.1 created
bd create "Patch retry logic" -p 0
# 输出：bd-a3f8.2 created
bd dep add bd-a3f8.2 bd-a3f8.1
# bd-a3f8.2 blocks bd-a3f8.1，先复现才能改

# 3. Agent A 认领复现任务（原子操作，避免抢任务）
bd update bd-a3f8.1 --claim
# 同时设置 assignee + in_progress

# 4. Agent B 查 ready 任务，看到 bd-a3f8.2 还被 block
bd ready
# 只列出没有 open blockers 的任务，bd-a3f8.2 不会出现

# 5. Agent A 完成复现，关闭 bd-a3f8.1
bd update bd-a3f8.1 --status closed

# 6. 此时 bd ready 会列出 bd-a3f8.2，Agent B 认领
bd update bd-a3f8.2 --claim

# 7. 修复完成，关闭子任务，Epic 自动判断是否完成
bd update bd-a3f8.2 --status closed
bd show bd-a3f8
# 查看任务详情和审计轨迹
```

这个流程里发生了什么：

- **存储层**：Agent A 和 Agent B 同时操作，Dolt cell-level merge 保证字段级合并不冲突
- **ID 层**：`bd-a3f8.2` 这种 Hash ID 在分支合并时不会重编号
- **协作层**：`--claim` 是原子操作，两个 Agent 不会同时认领同一个任务
- **上下文层**：任务关闭后会被语义压缩，下次 Agent 重读项目历史时 token 占用更小

## 快速开始

### 安装

```bash
# 安装（系统级，不要 clone 到项目里）
curl -fsSL https://raw.githubusercontent.com/gastownhall/beads/main/scripts/install.sh | bash

# Homebrew
brew install beads

# npm（Node.js 用户）
npm install -g @beads/bd
```

### 初始化

```bash
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

## 与传统 Issue 追踪工具对比

| 对比项 | 传统 Issue 追踪（GitHub Issues/Jira） | Beads |
|------|------|------|
| 目标用户 | 人类 | AI Agent |
| 数据格式 | 非结构化 | 结构化 SQL |
| 依赖追踪 | 手动 link | 自动依赖图 |
| 合并冲突 | 文件级锁/merge conflict | Hash ID，零冲突 |
| 版本控制 | 无 | Dolt 原生版本控制 |
| 上下文压缩 | 无 | 语义压缩防止溢出 |
| 多 Agent 支持 | 差 | 原生支持 |

为什么传统工具不够？因为它们假设读者是人类，输出格式是 HTML/Markdown，Agent 要解析得自己写爬虫或调 API。Beads 默认 JSON 输出，`bd ready` 直接给出可消费的任务列表，Agent 不需要额外适配层。

## 安全验证

在信任任何下载的二进制文件之前，验证其 checksum 与 release `checksums.txt` 一致。install 脚本默认验证 checksum。macOS 上安装脚本默认保留下载的签名。

## 采用建议

### 适合用 Beads 的场景

- **AI 编程 Agent 主导的项目**：Claude Code / Cursor / Copilot 等需要持久化记忆的工具
- **多 Agent 协作**：多个 Agent 同时在同一个项目上工作，需要并发写不冲突
- **长周期项目**：语义压缩防止上下文窗口溢出，旧任务不会挤掉当前上下文
- **Monorepo**：复杂的依赖关系管理，Git-Free 模式可以指向特定子目录
- **开源贡献**：Contributor 模式下规划工作不影响 PR

### 不适合的场景

- **纯人类团队、不用 AI Agent**：传统 Issue 追踪器更顺手，Beads 的 JSON 输出对人类不友好
- **任务量极小**：单文件 Markdown 就能搞定，引入 Dolt 后端是过度设计
- **需要严格权限管理**：Beads 目前没有 Jira 那种细粒度权限体系

### 推荐采用顺序

1. 先在单 Agent 项目里跑 `bd init`，用 `bd create` / `bd ready` / `bd update --claim` 跑通基本流程
2. 任务量上来后启用语义压缩，观察 token 占用变化
3. 多 Agent 协作时切到 Server 模式，让多个 writer 并发
4. 开源协作场景再引入 Contributor/Maintainer 角色区分

---

## 自测题

1. **Beads 的四层并行机制各解决什么问题？**
   - 参考答案：存储层（多 Agent 写冲突、历史不可回溯，用 Dolt cell-level merge + 原生分支解决）；ID 层（自增 ID 合并必冲突，用 Hash-based ID + 层级 ID 解决）；协作层（角色与仓库边界，用 Contributor/Maintainer 自动检测和 Git-Free 模式解决）；上下文层（旧任务撑爆上下文窗口，用语义压缩和 Message 类型解决）

2. **为什么 Beads 使用 Dolt 而不是传统数据库或文件？**
   - 参考答案：Dolt 既是 SQL 数据库，又是 git 风格的版本控制系统。cell-level merge 让两个字段级的修改可以自动合并，原生分支支持多 Agent 并行工作，SQL 查询支持结构化数据访问，内置同步支持多机器协作。

3. **Beads 的 Hash ID 和层级 ID 各有什么作用？**
   - 参考答案：Hash ID（如 `bd-a3f8`）替代自增 ID，防止多分支合并时冲突；层级 ID（如 `bd-a3f8.1`）表达 epic-task-subtask 结构关系，让 Agent 可以快速判断任务归属。

4. **Beads 适合用在什么场景？不适合什么场景？**
   - 参考答案：适合 AI 编程 Agent 主导的项目、多 Agent 协作、长周期项目、Monorepo、开源贡献；不适合纯人类团队、任务量极小、需要严格权限管理的场景。

5. **如果你想评估 Beads 是否适合你的团队，你会从哪几个方面测试？**
   - 参考答案：1) 在单 Agent 项目里跑 `bd init`，用基本命令跑通流程；2) 任务量上来后启用语义压缩，观察 token 占用变化；3) 多 Agent 协作时切到 Server 模式；4) 开源协作场景引入角色区分。

---

## 进阶路径

### 阶段一：快速验证（1 周）
- 目标：理解 Beads 的基本机制和核心命令
- 行动：安装 Beads，运行 `bd init`，用 `bd create` / `bd ready` / `bd update --claim` 跑通基本流程
- 验收：能解释 Beads 的四层并行机制，熟练使用基本命令

### 阶段二：实际项目试用（2-4 周）
- 目标：在真实项目中用 Beads 管理任务，评估适用边界
- 行动：在真实 AI Agent 项目中配置 Beads，观察多 Agent 协作时的写冲突处理，评估语义压缩效果
- 验收：能判断 Beads 是否适合团队的工作流，识别需要人工介入的场景

### 阶段三：高级功能与定制化（1-3 个月）
- 目标：理解 Embedded vs Server 模式、Contributor/Maintainer 角色、Git-Free 模式
- 行动：阅读四层机制的详细文档，尝试 Server 模式多 Agent 并发写，配置 Contributor/Maintainer 角色区分
- 验收：能根据团队规模和工作流选择合适的存储模式和角色配置

### 阶段四：生态扩展与贡献（长期）
- 目标：与现有工具链集成，贡献到 Beads 项目
- 行动：集成到 CI/CD 流程，开发与 Claude Code / Cursor / Copilot 的深度集成，提交 PR 改进文档或功能
- 验收：能把 Beads 完整接入团队的 AI Agent 工作流，并能贡献改进

---

## 常见问题

### Q1: Beads 和 GitHub Issues 有什么区别？
**A**: GitHub Issues 设计给人用，Beads 设计给 AI Agent 用。Beads 的数据是结构化 SQL，支持自动依赖图、原子认领、语义压缩、Hash ID 防冲突、Dolt 版本控制，这些功能对 AI Agent 协作至关重要。

### Q2: Beads 的 Embedded 模式和 Server 模式有什么区别？
**A**: Embedded 模式（默认）在进程内运行 Dolt，不需要外部服务器，适合单 Agent；Server 模式连接外部 `dolt sql-server`，支持多个并发 writer，适合多 Agent 协作。

### Q3: 语义压缩是什么？为什么需要它？
**A**: 语义压缩是 Beads 的自动压缩机制，关闭的任务被语义压缩，保留关键信息但大幅减少 token 占用。需要它是因为长周期项目中，关闭的旧任务会累积占用上下文窗口，压缩后 Agent 能在有限上下文窗口里处理更长的项目历史。

### Q4: Beads 支持哪些 VCS？
**A**: Beads 默认与 git 集成，也支持 Git-Free 模式（完全脱离 git 工作），适用于 Sapling、Jujutsu、Piper 等非 git VCS，以及 Monorepos、CI/CD、评估/测试场景。

### Q5: 如何保证多 Agent 并发写不冲突？
**A**: Beads 用 Dolt 的 cell-level merge 保证并发写不冲突。两个 Agent 同时改同一个任务的不同字段（一个改 status，一个改 assignee）能自动合并，不需要手动解冲突。

---

## 相关链接

- GitHub：https://github.com/gastownhall/beads（截至 2026-04-27，21.5k stars）
- 文档：https://gastownhall.github.io/beads/
- npm：https://www.npmjs.com/package/@beads/bd
- PyPI：https://pypi.org/project/beads-mcp/

🦞 每日 08:00 自动更新
