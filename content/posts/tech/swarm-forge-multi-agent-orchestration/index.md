---
title: "SwarmForge：用 tmux 把多智能体协作装进同一台终端"
date: 2026-08-08T03:30:00+08:00
slug: "swarm-forge-multi-agent-orchestration"
github_repo: "unclebob/swarm-forge"
source_key: "gh:unclebob/swarm-forge"
description: "SwarmForge 是 Robert C. Martin 团队维护的多智能体协作框架，用 tmux + git worktree + handoff 守护进程把多个 AI Agent 编入一条纪律严明的工程流水线。本文拆解它的角色拓扑、handoff 协议与构文章典机制。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "多智能体协作", "tmux", "TDD", "Uncle Bob", "工程实践"]
---

> **先给判断**：SwarmForge 不是又一套"Agent 调度框架"。它的核心是一套写在 `constitution.prompt` 里的工程纪律（测试驱动、重构、突变测试、验收测试），靠 tmux 和 git worktree 把它落到物理隔离的执行单元上，再用 `handoffd.bb` 守护进程把 Agent 之间的"对话"变成有签收的回执。要理解 SwarmForge，先把它当成"分布式 TDD 团队"而不是"AI Agent 编排器"。

## 1. 为什么是 tmux

`unclebob/swarm-forge` 主仓库的 README 第一行就点破了工程动机：

> SwarmForge is an agent coordination system that facilitates communication between agents working in different git worktrees.

它不调度 GPU、不维护消息队列、不跑云端任务。它只是把每个 Agent 关进自己的 tmux 窗口，让它们在各自的 git worktree 里写代码，再通过一个 Babashka 守护进程收发明文 handoff 文件。

选 tmux 不是技术怀旧，而是三条硬约束的合力：

- **可观察性**：开发者必须能在一个屏幕上看到所有 Agent 在做什么，这是单终端 multi-pane 唯一便宜的可视化方案。
- **离线**：Agent 进程崩溃、API 限流、网络抖动都是常态；tmux 不依赖任何外部服务就能保持会话不丢。
- **本地**：整套系统装在工作目录的 `.swarmforge/` 下，迁移项目等于复制一份目录。

## 2. 系统地图

```
┌──────────────────────────────────────────┐
│   swarmforge/swarmforge.conf（拓扑声明）  │
└───────────────┬──────────────────────────┘
                │ 启动期
                ▼
┌──────────────────────────────────────────┐
│          ./swarm 包装脚本                │
│  - 拉取 main 分支共享脚本/宪章            │
│  - 校验角色 prompt / 终端适配器           │
│  - 初始化 git worktree（按角色）          │
└───────────────┬──────────────────────────┘
                │
   ┌────────────┼───────────────────────────┐
   ▼            ▼                           ▼
worktree-1   worktree-2                 worktree-N
(specifier)  (coder)                    (QA/...)
   │            │                           │
   │  ┌─────────┴────────────┐              │
   │  │  swarm_handoff.sh    │              │
   │  │  ready_for_next.sh   │              │
   │  │  done_with_current.sh│              │
   │  └─────────┬────────────┘              │
   │            │ 草稿 handoff               │
   ▼            ▼                           ▼
┌──────────────────────────────────────────┐
│   handoffd.bb（Babashka 守护进程）         │
│   - 监听每个角色的 outbox                 │
│   - 校验草稿（commit 简码 / note 行长度） │
│   - 复制到收件人 inbox                    │
│   - 发送 tmux 唤醒通知（不带具体内容）    │
└──────────────────────────────────────────┘
```

`constitution.prompt` 是入口文件；启动时它指向 `constitution/articles/` 下的若干 `.prompt` 片段（`engineering.prompt`、`handoffs.prompt`、`workflow.prompt` 等）。每个角色再叠一份 `local-*.prompt` 做工作流特化。这是 SwarmForge 最容易被低估的设计：把"工程哲学"放在文件系统里，而不是写进 Agent 的 system prompt。

## 3. 三档工作流：two-pack / four-pack / six-pack

SwarmForge 把角色拓扑做成了可配置的"打包"：

| 打包 | 角色链路 | 适用场景 |
| --- | --- | --- |
| **two-pack** | coder → cleaner → coder | 小任务，TDD + 重构即可，不要验收测试 |
| **four-pack** | specifier → coder → refactorer → architect → specifier | 中等项目，需要 Gherkin 规范但不必拆解所有质量关 |
| **six-pack** | specifier → coder → cleaner → architect → hardender → QA | 大型项目，每个质量关由独立 Agent 负责 |

设计上有两点值得专门指出：

- **角色数 = 质量关的数量，而不是"用几个 Agent 比较合适"**。two-pack 没有 specifier，是因为 Gherkin 不在它的目标里；six-pack 把 hardender 单拎出来，是因为 mutation testing 是值得独占 Agent 的重活。
- **cleaner 与 refactorer 不是同义词**。two-pack 的 cleaner 兼做"代码清理 + 架构审视 + 语言突变加固"；four-pack 的 refactorer 把架构关切上提到 architect，自己只做行为保持的重构。

## 4. handoff 协议：把 Agent 间的对话变成有签收的回执

README 的 "Handoff Protocol" 一节是整个项目的精华。三个工具脚本各自负责一段状态机：

| 脚本 | 作用 | 关键校验 |
| --- | --- | --- |
| `swarm_handoff.sh <draft>` | 校验并入队 | git handoff 的 commit 简码必须是 10 位十六进制，且 `git rev-parse` 能解析到唯一提交 |
| `ready_for_next.sh` | 接受工作 | 按角色配置的 `receive` 模式接受 |
| `done_with_current.sh` | 完成工作 | 按角色配置的 `receive` 模式收尾 |

草稿 handoff 走两种格式：

```text
type: git_handoff
to: specifier,coder
priority: 03
task: implement-login-flow
commit: 1f3a9b2c5d
```

```text
type: note
to: cleaner
priority: 02
message: cleaner batch ready, see .swarmforge/inboxes/cleaner/
```

`handoffd.bb` 只看 inbox 队列，不读取具体内容。Agent 之间不能直接 tmux send-keys 抢话——这是架构上的硬隔离：内容由文件传输，tmux 只用来唤醒。

## 5. 构文章典的"分层覆盖"机制

`constitution/articles/` 里有三类文件：

- **共享默认值**（在 `main` 分支）：`engineering.prompt`、`handoffs.prompt`、`workflow.prompt`，所有打包都继承。
- **本地特化**（在运行分支）：`local-engineering.prompt`、`local-workflow.prompt`，命名约定 `local-*` 表示"追加或收紧"而不是"替换"。
- **本地覆盖**（在运行分支）：与共享文件同名的 `.prompt`，启动时不会用共享版本覆盖它。

这等价于一个 Git 风格的覆盖规则：

```text
if exists(local file with same name as shared):
    use local  # 完整替换
elif exists(local-*):
    append local-*  # 在共享之上叠加
else:
    use shared  # 默认
```

写六-pack 这种复杂打包的人不需要改 README，他只要在运行分支里提交 `local-workflow.prompt` 加一段"QA 必须重放六小时前的 acceptance suite"即可。

## 6. 一个最小任务流案例

让 six-pack 跑一遍"实现登录限流"：

1. **specifier** 写 5 条 Gherkin：`Given ... When ... Then ...`，等待 `ready_for_next.sh` 触发下一棒。
2. **coder** 拉 `git_handoff` 拿 commit `1f3a9b2c5d`（specifier 已合入规范的快照），在 `.worktrees/coder/` 里 TDD 写实现 + 生成 acceptance test 桩。
3. **cleaner** 在 coder 合入后批量读 inbox，做 CRAP / DRY / encapsulation / 语言突变扫描，产出 `coder-review.md` 后 `done_with_current.sh`。
4. **architect** 看 coder + cleaner 双方产物，决定模块边界、依赖方向，写 `architecture-review.md`。
5. **hardender** 用 mutation testing 把测试套件打到 80% 突变杀死率，发现没被覆盖的边界。
6. **QA** 把 specifier 的 Gherkin 转成可执行脚本，UI 走一遍验收，给 `completion-notify.md`。

每一步交接都是一个 commit 简码 + handoff 文件，不存在"Agent A 直接对 Agent B 喊话"。

## 7. 边界与适用人群

值得用的场景：

- 单人或小团队要把 AI Agent 编进真实的 TDD / 重构 / 验收纪律。
- 项目需要可重复的"Agent 工作流"模板（one workflow = one branch）。
- 不想上 LangGraph、AutoGen、Claude Agent SDK 这类带云依赖的方案。

不必用的场景：

- 一次性的 prompt 实验，拓扑就一个 Agent，没有 handoff 价值。
- 需要分布式多机部署——SwarmForge 明确假设单机 tmux。
- 需要 GPU 调度、向量库、长时记忆——这些都不在它的范围内。

## 8. 入口与排错

```sh
BRANCH=four-pack
curl -L "https://github.com/unclebob/swarm-forge/archive/refs/heads/${BRANCH}.tar.gz" \
  | tar -xz --strip-components=1
./swarm
```

排错路径：

- tmux 窗口没开：检查终端适配器是否在 `swarmforge.conf` 中正确声明。
- handoff 一直 stuck：先看 `.swarmforge/inboxes/<role>/` 是否有未处理草稿；`handoffd.bb` 会写自己的日志。
- commit 简码报 "ambiguous"：先用 `git rev-parse <abbrev>^{commit}` 看是否多于 1 个匹配，把 handoff 里的简码加长（最多 10 位仍是合法）。

## 9. 采用顺序建议

1. 先用 two-pack 在一个小功能上跑通 TDD → cleaner 闭环，体感一下"git_handoff + note 队列"的成本。
2. 升级到 four-pack，加 Gherkin 规范与 architect 角色，验证 `local-*.prompt` 的覆盖机制。
3. 真正做完整服务时切 six-pack，让 hardender 与 QA 各自独立。

不要一上来就 six-pack——六棒 handoff 在第一次跑通前看起来像过度工程，跑通一次后就知道每一棒砍掉都会丢一种质量信号。

---

> 这篇文章不是 SwarmForge 的官方教程。要看完整配置语法与最新打包变化，请直接读 `unclebob/swarm-forge` 仓库的 README 与对应工作流分支（`two-pack` / `four-pack` / `six-pack`）。