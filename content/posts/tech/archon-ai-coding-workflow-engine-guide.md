---
title: "Archon：让AI编程变得可重复、可追溯的开源工作流引擎"
date: "2026-04-09T20:20:00+08:00"
slug: "archon-ai-coding-workflow-engine-guide"
github_repo: "coleam00/Archon"
description: "Archon 是面向 AI 编程的开源工作流引擎：开发流程写成 YAML 定义的 DAG，把规划、实现、验证、评审、批准与 PR 创建编排成可重复执行的工程流水线。本文讲清它的工作流模型、worktree 隔离、默认工作流、上手路径与自定义方式。"
draft: false
categories: ["技术笔记"]
tags: ["AI 编程", "Claude Code"]
---

用 Claude Code、Codex 这类编码 Agent 一段时间后，会撞上同一个瓶颈：模型能力在涨，开发流程却仍靠临时提示词、人工盯执行、手动补审查维系。Archon 解决的就是这一层——把 Agent 的执行收束成可审计的工程流程。

Archon 是一个面向 AI 编程的 workflow engine（工作流引擎），同时是一个 AI coding harness builder。开发流程写成 YAML，它负责把规划、实现、验证、评审、批准、PR 创建这些步骤编排成可重复执行的工程流水线。

GitHub API 2026-08-05 验证的仓库基本数据：

| 指标 | 数值 |
|------|------|
| GitHub Stars | 23,073 |
| Forks | 3,452 |
| 主语言 | TypeScript |
| License | MIT |
| 最新 release | v0.7.1（2026-08-04 发布）|
| 默认分支 | dev |
| 仓库描述 | The first open-source harness builder for AI coding. Make AI coding deterministic and repeatable. |

一个需要留意的口径差异：官方入门文档以 17 个核心 workflow 为主目录，更完整的文档与源码里还能看到 additional workflows。最稳妥的确认方式始终是运行 `archon workflow list`。

## 先说结论：Archon 到底是什么

Archon 的定位在编排层。它把开发过程拆成有顺序、有依赖、有门禁的步骤——AI 只在需要智能的地方发挥作用，测试、脚本、验证、审批、分支隔离、工件沉淀这些工程动作则放进确定性框架里。

| 你关心的问题 | 直接使用单个 Agent 的典型状态 | Archon 提供的能力层 |
| ------ | ------ | ------ |
| 同一个需求每次结果都不一样 | 流程取决于模型当时怎么理解指令 | 用 workflow 固定步骤、顺序和门禁 |
| 多个任务并行容易互相污染 | 共用工作区，分支和文件状态容易冲突 | 每次运行默认进入独立 worktree |
| 很难知道 AI 到底做了什么 | 只能看零散终端输出或最终结果 | DAG 执行、事件、工件、状态全程可追溯 |
| 想在关键步骤插入人工审核 | 往往只能临时打断，流程不稳定 | approval / interactive 节点内建 human-in-the-loop |
| 团队希望复用同一套开发流程 | 最终只剩提示词，难以长期维护 | YAML workflow 可提交到仓库，团队共享同一流程 |
| 希望在 CLI、Web、聊天平台之间保持一致 | 不同入口各做一套 | 同一套 workflow 可跨 CLI、Web UI、Slack、Telegram、GitHub、Discord 复用 |

Archon 解决的是 AI 如何进入工程体系的问题，模型本身的能力不在它的职责范围内。

理解 Archon 还需要先区分三层并行机制，它们各自独立，边界不清就会误判适用场景：

- **DAG 内并行**：同一依赖层的节点并发执行，例如多个 review agent 同时审查。
- **worktree 隔离**：多个 workflow run 之间互不污染，每个写任务独占一个 git worktree。
- **多入口复用**：CLI、Web UI、聊天平台共享同一套 workflow，入口不同行为一致。

这三层是 Archon 和普通脚本编排的差别所在，下面逐层展开。

## 它适合谁，不适合谁

### 适合的场景

- 你已经在高频使用编码 Agent，希望把规划、验证、评审、PR 创建这些步骤标准化。
- 你所在的团队不只关心"能不能写出来"，还关心过程是否可审计、能不能回放。
- 你有并发任务，且不想让多个 AI 任务互相污染本地工作区。
- 你准备把团队实践建议沉淀成仓库内的 workflow 文件，避免经验散落在聊天记录里。

### 不太适合的场景

- 你只是偶尔问几个代码问题，或者只想让 Agent 快速看一段代码。
- 你的任务非常短平快，工作流编排的固定成本已经高于收益。
- 你当前真正缺的是"更强模型"或"更懂代码的提示词"，流程治理还不是主要矛盾。

最短判断标准：如果你的痛点已经从"怎么让 AI 干活"转成"怎么让 AI 稳定地按流程干活"，Archon 才会显著放大价值。

## Archon 把几个长期问题拉进了同一套系统

下面三个问题，是编码 Agent 用久了都会遇到的。Archon 用 workflow 把它们一并处理。

### 把随机聊天变成可重复执行的流程

对着 Agent 说"修复这个 bug"，结果常常取决于模型这次有没有先规划、会不会主动运行测试、会不会遵守团队的 PR 模板。Archon 把这些"不一定会发生"的步骤提前写进 workflow，让它们从模型当时的判断变成流程里的固定节点。这样即使模型这次"忘了"跑测试，workflow 里的 bash 节点也会强制执行。

### 把"看结果"换成"看过程"

在团队环境里，最终 diff 只是结果的一小部分。更重要的问题是：它读了哪些上下文、跑了哪些验证、在哪一步卡住、为什么重试、人工是在什么环节介入的。Archon 通过 workflow run、event、artifact、review 这些对象，让过程本身变成可回放资产。排查"为什么这次 PR 没过 review"时，你能回放整条执行链，不必只看最终评论。

### 把单人技巧变成团队流程资产

如果某个同事写出了一套非常有效的"规划 → 验证 → 审查 → PR"流程，传统做法通常只能把它存成提示词。Archon 的做法更接近基础设施：把流程写成 YAML，随仓库提交，交给整个团队反复复用和演进。新人 clone 仓库后运行 `archon workflow list`，看到的就是团队当前的标准流程。

## 一个真实 workflow 是怎么跑完的

把 Archon 只理解成"写 YAML 然后交给 AI 跑"还是太抽象。把一次 workflow run 拆开看，是下面这条执行链：

1. 你在 CLI、Web UI 或聊天平台发出需求。
2. Orchestrator 识别意图，解析 workflow 名称，必要时自动匹配最接近的 workflow。
3. 如果当前目录是一个 Git 仓库，Archon 会注册 codebase，并准备 workflow 运行上下文。
4. 对于会写代码的任务，隔离层创建或复用独立 worktree，并生成对应分支。
5. Workflow Executor 按 DAG 依赖关系启动节点；能并行的节点并行，必须等待的节点顺序执行。
6. AI 节点读上下文、调用模型；确定性节点执行测试、构建、脚本或 Git 操作。
7. 节点输出被写入 artifact 或结构化 output，供后续节点继续消费。
8. 如果流程中包含人工门禁，workflow 会暂停，等待 `approve` 或 `reject` 指令继续。
9. 完成后，结果、事件、消息、运行状态会被保留下来，供 Web UI、CLI 和后续排查使用。

走完这 9 步，输出是一条有状态、有产物、可排查的运行记录，而不是聊天框里的一段回复。

## 工作流引擎是怎么运作的

### Workflow 是一个 DAG

Archon 把 workflow 定义成 directed acyclic graph（有向无环图，DAG）。每个 node（节点）声明自己要做什么，以及依赖哪些上游节点。没有依赖的节点可以并行运行；有依赖的节点等前置结果就绪后再执行。

DAG 模型让流程的顺序、并行和依赖关系都变成显式声明，避免藏在提示词里靠模型自己理解。这对团队协作的意义在于：流程变更会触发 code review，避免某天某个同事改了提示词就悄悄变了。

这是官方 authoring 文档里的典型结构，比较接近当前设计方向：

```yaml
name: classify-and-route
description: |
  Classify an issue as a bug or feature, then run the appropriate path.

nodes:
  - id: classify
    command: classify-issue
    output_format:
      type: object
      properties:
        type:
          type: string
          enum: [BUG, FEATURE]
      required: [type]

  - id: investigate
    command: investigate-bug
    depends_on: [classify]
    when: "$classify.output.type == 'BUG'"

  - id: plan
    command: plan-feature
    depends_on: [classify]
    when: "$classify.output.type == 'FEATURE'"

  - id: implement
    command: implement-changes
    depends_on: [investigate, plan]
    trigger_rule: none_failed_min_one_success
    context: fresh
```

DAG 模型的价值落在三处：

1. **顺序是显式的**：流程不再藏在一大段提示词里，而是写成节点依赖图。
2. **并行是天然的**：同一依赖层的节点可以并发跑，例如多个 review agent 并行审查。
3. **输出可被消费**：上游节点的输出可以通过 `$nodeId.output` 传给下游，用于路由和条件判断。

### Archon 不只是 AI 节点加 Bash 节点

早期介绍多停留在 prompt 和 bash 两类节点，当前 Archon 已经有更丰富的工作流原语。

| 节点 / 能力 | 作用 | 什么时候用 |
| ------ | ------ | ------ |
| `command:` / `prompt:` | 让 AI 做规划、实现、审查、总结 | 需要模型推理和代码理解时 |
| `bash:` | 执行确定性的 shell 命令 | 跑测试、lint、构建、Git 操作 |
| `script:` | 运行内联 TypeScript / Python，或调用 `.archon/scripts/` | 需要比 shell 更可控的逻辑时 |
| `when:` | 根据上游输出做条件分支 | bug / feature 分流，复杂度分级 |
| `output_format:` | 约束 AI 输出为结构化 JSON | 路由、决策、下游消费 |
| `context: fresh` | 强制节点在新上下文里执行 | 避免长链任务上下文污染 |
| `provider:` / `model:` | 为节点指定 AI provider / model | 需要按任务类型切模型时 |

`script:` 值得单独说。从官方 release 信息看，v0.3.3 开始，Archon 支持 script node，允许通过 `bun` 或 `uv` 运行内联 TypeScript / Python 或 `.archon/scripts/` 中的脚本。这让它在 YAML 加提示词的编排器之外，更像一个真正的工程自动化 runtime。需要解析 JSON、调用内部 API、做复杂条件判断时，script node 比纯 prompt 更可靠。

### Human-in-the-loop 有两种模式

Archon 在文档里明确区分了两种常见的人机协同模式。

#### Interactive loop

适合"看一版 → 给反馈 → 再迭代"的往返式过程，例如方案评审、PRD 打磨、PIV 循环。

```yaml
- id: refine-plan
  loop:
    prompt: |
      User feedback: $LOOP_USER_INPUT
      Read the current plan, revise it, and present the updated version.
    until: PLAN_APPROVED
    max_iterations: 10
    interactive: true
    gate_message: "Review the plan. Provide feedback or say approved."
```

#### Approval with on_reject

适合"先过门，再修复"的 gate-then-fix 模式。人类只在批准或驳回时介入；如果驳回，再由 AI 按明确原因修订。

```yaml
- id: review
  approval:
    message: "Review the report. Approve or request changes."
    capture_response: true
    on_reject:
      prompt: "Revise based on: $REJECTION_REASON"
      max_attempts: 5
```

两种模式差别在于：interactive loop 是多轮对话式协作，approval 是单次门禁式介入。一个松散、一个僵硬，选错模式流程就不对味。Archon 把人类介入从临时行为变成流程原语，这是它和普通脚本编排的一个差别。

## 为什么 worktree 隔离是 Archon 的工程核心

Archon 最有工程含量的设计，是默认把可写任务放进独立 git worktree 里执行——YAML 编排只是它的表达层。

```bash
# 显式指定分支名运行 workflow
archon workflow run archon-idea-to-pr --branch feat/export-csv "Add CSV export to the reports page"

# 让 Archon 自动生成分支 / worktree
archon workflow run archon-idea-to-pr "Add CSV export to the reports page"

# 仅在确实需要时，才跳过 worktree 隔离
archon workflow run archon-assist --no-worktree "How does error handling work here?"
```

git worktree 的优势在于它复用了团队已有的 Git 工作流，不需要额外的容器或虚拟机开销。

worktree 隔离直接解决了四个工程痛点：

- **并行安全**：多个任务可以同时运行，不用担心互相改坏同一个工作目录。
- **主工作区更干净**：AI 不需要直接在你的 live checkout 上反复试错。
- **结果天然可追踪**：每次运行对应一个分支 / worktree，方便回溯和清理。
- **和 PR 生命周期天然对齐**：从 feature 分支到 review，再到 merge，路径一致。

对团队来说，这是 Archon 和"普通脚本编排 + Agent"之间最关键的差别。没有 worktree 隔离，多个 AI 任务并发时会互相覆盖文件、抢占分支，最终只能串行执行，DAG 并行的价值也会被抵消。

## 架构拆解：从一句指令到一次工作流运行

从系统视角看，Archon 可以拆成 5 层：

| 层 | 组件 | 职责 |
| ------ | ------ | ------ |
| 入口层 | CLI、Web UI、Slack、Telegram、GitHub、Discord | 接收用户指令，触发 workflow |
| 编排层 | Orchestrator | 路由消息、管理上下文、决定调用哪个 workflow |
| 执行层 | Workflow Executor | 解析 YAML、执行 DAG、处理依赖、条件和循环 |
| AI 层 | Claude / Codex 等 Assistant Clients | 在指定节点执行推理、生成代码、做审查 |
| 数据层 | SQLite / PostgreSQL | 持久化 codebases、conversations、sessions、workflow runs、isolation environments、messages、workflow events |

同一套 workflow 在 Web UI、命令行和聊天平台之间行为一致，本地 CLI 只是其中一个入口。数据层统一持久化，无论从哪个入口触发，运行历史都能在 Web UI 里回放。

## 默认 workflows 怎么选，不要一上来就用最重的

官方 README 和 Getting Started 文档面向入门用户时，仍以 17 个核心 workflows 作为主目录。它们足够覆盖大多数团队的第一阶段需求。

### 17 个核心 workflows

| Workflow | 用途 |
| ------ | ------ |
| `archon-assist` | 通用问答、调试、探索代码库 |
| `archon-fix-github-issue` | GitHub Issue 修复全流程 |
| `archon-idea-to-pr` | 从功能想法到经过验证和审查的 PR |
| `archon-plan-to-pr` | 执行已有计划并完成 PR |
| `archon-issue-review-full` | 复杂 Issue 的修复与多 Agent 审查 |
| `archon-smart-pr-review` | 按 PR 复杂度做定向审查 |
| `archon-comprehensive-pr-review` | 5 个并行 reviewer 的全量 PR 审查 |
| `archon-create-issue` | 归类问题、收集上下文并创建 GitHub Issue |
| `archon-validate-pr` | 验证 feature branch 和 main 分支的 PR 行为 |
| `archon-resolve-conflicts` | 检测并解决合并冲突 |
| `archon-feature-development` | 从现有计划直接实现功能并创建 PR |
| `archon-architect` | 架构扫频、复杂度治理、代码库健康提升 |
| `archon-refactor-safely` | 带类型检查和行为验证的安全重构 |
| `archon-ralph-dag` | 按 story 迭代推进 PRD 实现 |
| `archon-remotion-generate` | 生成或修改 Remotion 视频组合 |
| `archon-test-loop-dag` | 迭代式测试-修复循环 |
| `archon-piv-loop` | 带人工审核的 Plan-Implement-Validate 循环 |

### 选型建议

| 你的目标 | 优先选择 |
| ------ | ------ |
| 先问代码库问题、做探索 | `archon-assist` |
| 从自然语言需求直接做功能 | `archon-idea-to-pr` |
| 你已经有成熟 plan，只想稳妥落地 | `archon-plan-to-pr` 或 `archon-feature-development` |
| 你只想 review 当前 PR | `archon-smart-pr-review` 或 `archon-comprehensive-pr-review` |
| 你要修 GitHub Issue | `archon-fix-github-issue` |
| 你要做人机反复协作的开发闭环 | `archon-piv-loop` |

### 默认 workflow 数量口径不一致

官方不同位置对"默认 workflows 的数量"口径并不一致：

- README 和 Getting Started 强调的是面向用户最常用的 17 个核心 workflows。
- 更完整的文档还会出现 `archon-interactive-prd`、`archon-adversarial-dev`、`archon-workflow-builder` 等 workflow。
- 源码里和 binary distribution 相关的 bundled defaults 又可能比完整文档目录更精简。
- 不同文档示例的 YAML 语法也在演进，例如旧示例里常见 `fresh_context: true`，而新的 authoring 文档更强调 `context: fresh`、`approval`、`loop.interactive` 这套表达方式。

这种差异反映的是 Archon 仍在快速迭代，文档错误只是表象。实践里不要死记清单，直接在目标仓库运行下面这条命令最可靠：

```bash
archon workflow list
```

如果你准备自己写 workflow，建议把 README 当成概念导览，把 [Authoring Workflows](https://archon.diy/guides/authoring-workflows/) 当成实际语法基准。

## 三条上手路径

不同读者的操作入口不一样，分开讲比混在一起更清楚。Archon 至少有三条常见上手路线。

### 路线 A：第一次接触，用官方 setup wizard

这条路径适合首次完整配置。官方 README 给出的前提是：你已经有 Bun、Claude Code 和 GitHub CLI。

```bash
git clone https://github.com/coleam00/Archon
cd Archon
bun install
claude
```

进入 Claude Code 后，对它说：

```text
Set up Archon
```

向导会引导你完成 CLI 安装、认证配置、平台选择，以及把 Archon skill 复制到目标项目中。官方文档还特别强调：**真正开始工作时，要在你的目标仓库里启动 Claude Code，不要一直待在 Archon 自己的仓库里。** 原因是 Archon 的 workflow 从当前仓库动态加载，待在 Archon 仓库里只会看到 Archon 自带的 workflows，无法加载你目标项目的 `.archon/workflows/`。

### 路线 B：你已经装好 Claude Code，只想装 CLI

如果你已经具备 Claude Code 环境，只想快速拿到 Archon CLI，可以走 quick install。

```bash
# macOS / Linux
curl -fsSL https://archon.diy/install | bash

# Windows (PowerShell)
irm https://archon.diy/install.ps1 | iex

# Homebrew
brew install coleam00/archon/archon

# Docker
docker run --rm -v "$PWD:/workspace" ghcr.io/coleam00/archon:latest workflow list
```

安装后先做两步验证：

```bash
archon version
archon workflow list
```

### 路线 C：你想用 Web UI 观察和管理 workflows

Archon 不只有 CLI。官方文档显示，binary installs 可以直接通过 `archon serve` 下载并启动 Web UI；源码运行则可以从 Archon 仓库启动前端开发环境。

Web UI 有四个页面值得看：

| 页面 | 你会看到什么 |
| ------ | ------ |
| Chat | 实时对话与工具调用可视化 |
| Dashboard | workflow 监控、项目 / 状态 / 日期过滤 |
| Workflow Builder | 可视化拖拽编辑 DAG |
| Workflow Execution | 节点级进度和历史回放 |

如果给团队引入，Web UI 让 workflow 运行从个人终端事件变成团队可见事件，它并不替代 CLI。多人协作时，Web UI 让运行状态、审批待办、历史回放对所有人可见，避免"只有跑命令的人知道发生了什么"。

## 常用 CLI 操作

除了 `archon setup`，实际使用中最常见的命令其实只有下面这些：

```bash
# 查看当前目录可用的 workflows
archon workflow list

# 运行 workflow
archon workflow run archon-idea-to-pr "Add dark mode to the settings page"

# 指定分支名运行
archon workflow run archon-idea-to-pr --branch feat/dark-mode "Add dark mode"

# 对另一个目录运行
archon workflow run archon-idea-to-pr --cwd /path/to/repo "Add dark mode"

# 不使用 worktree，直接在当前 checkout 上运行
archon workflow run archon-assist --no-worktree "How does error handling work here?"

# 查看运行状态
archon workflow status

# 恢复失败的 workflow
archon workflow resume <run-id>

# 放弃一个非终态 workflow
archon workflow abandon <run-id>

# 批准或驳回人工门禁
archon workflow approve <run-id> "Looks good, proceed"
archon workflow reject <run-id> "Please split the migration into two steps"
```

三个细节值得注意：

1. 写操作默认优先配合 worktree 隔离，不要把 `--no-worktree` 当常态。
2. `archon workflow list` 读取的是**当前工作目录**的可用 workflows，没有全局固定目录这一说。
3. 如果仓库里有和内置 workflow 同名的文件，仓库版本会覆盖 bundled default。

## 第一次成功的最小闭环

如果你不想一上来就跑最重的 feature workflow，最稳妥的首次体验顺序是：

```bash
# 确认 CLI 和 workflow 已就绪
archon version
archon workflow list

# 用轻量问题确认编排器能正常工作
archon workflow run archon-assist "What workflows are available here?"

# 再运行一个真正会创建 worktree 的写任务
archon workflow run archon-idea-to-pr --branch feat/hello-archon "Add a tiny docs-only improvement"

# 查看状态
archon workflow status
```

当你能稳定完成这四步，才算跑通 Archon 的最小闭环：CLI 可用、workflow 可发现、AI 节点可执行、worktree 隔离生效。

## 新手最容易踩的 5 个坑

### 把 README 示例当成完整语法真相

README 适合快速建立直觉，但不适合作为 workflow authoring 的最终依据。真正写 YAML 时，应以 authoring 文档和本机 `archon workflow list` 的实际行为为准。README 里的示例为了简洁会省略很多字段，照抄到生产环境往往会缺关键字段。

### 只关心 AI prompt，不关心验证门

很多人第一次写 workflow 时，会把精力全花在 prompt 上，却忘了把 lint、test、build 或 review gate 写进流程。这样得到的结果只是更长的提示词，工程流程并没有变强。判断一个 workflow 好不好，看的是它有多少确定性节点，AI prompt 写得多精细不是关键。

### 误把 `--no-worktree` 当默认选项

`--no-worktree` 适合只读探索，不适合常规写操作。你一旦习惯在 live checkout 上让 AI 反复试错，Archon 最重要的隔离价值就被你自己抹掉了。多个写任务并发时，没有 worktree 隔离还会导致分支和文件互相覆盖。

### 写 interactive loop 时漏掉 `gate_message`

根据当前 workflow 校验逻辑，interactive loop 通常需要明确的 `gate_message`，否则用户很难知道在暂停点该输入什么，某些配置下也会直接触发加载错误。`gate_message` 是人和流程之间的契约，漏掉它会让暂停点变成黑盒。

### 忘了"同名文件覆盖默认 workflow"

如果仓库里放了和内置 workflow 同名的文件，它会覆盖 bundled default。这很有用，但也意味着你需要像维护 CI 配置一样认真维护这些 YAML。升级 Archon 版本时，如果内置 workflow 更新了，你的覆盖文件不会自动同步，需要手动 diff。

## 自定义 workflows

Archon 的上限不在那 17 个默认 workflow，而在于你能不能把团队流程写成可提交、可维护的 workflow 文件。

### 自定义文件放在哪里

- workflow 文件放在 `.archon/workflows/`
- command 文件放在 `.archon/commands/`
- script node 相关脚本可放在 `.archon/scripts/`

官方文档明确说明：这些文件会从**当前仓库**运行时动态加载，没有全局模板目录静态拷贝这一步。你可以把 workflow 当作仓库基础设施的一部分来维护。这意味着同一个团队的不同项目可以有完全不同的 workflow 集合，新成员 clone 仓库后就能看到团队当前的标准流程。

### 一个更接近真实团队流程的示例

下面这个例子展示的是"审查 → 人工批准 → 驳回后自动修订"的 gate-then-fix 模式：

```yaml
name: team-review-gate
description: |
  Review changes, require explicit approval, then proceed.

interactive: true

nodes:
  - id: review
    command: review-pr

  - id: approve
    depends_on: [review]
    approval:
      message: "Review findings. Approve or request changes."
      capture_response: true
      on_reject:
        prompt: "Revise based on: $REJECTION_REASON"
        max_attempts: 3

  - id: publish
    command: create-pr
    depends_on: [approve]
```

它在不可逆动作前把人判断显式写进系统，比"让 AI 自己 review 自己"可靠。`create-pr` 一旦创建就会通知 reviewer、触发 CI，在它前面加 approval gate，能避免 AI 把不成熟的改动直接推到团队视野里。

另一个细节：在 Web UI 里，带人工审批门的 workflow 通常还需要 workflow 级的 `interactive: true`，这样它会以前台交互方式运行，避免被完全丢到后台。这个约束在参考文档里写得比 README 更明确。

### 自定义时最值得坚持的 4 条原则

1. 一个节点只做一件事，不要把规划、实现、验证混在同一个 AI prompt 里。混在一起会让失败定位变得困难——你不知道是规划错了、实现错了还是验证错了。
2. 所有 AI 节点后面都跟一个确定性验证步骤，至少是测试、lint 或构建之一。AI 节点的输出有随机性，确定性节点是兜底。
3. 重要决策前加 approval gate，例如数据库迁移、批量删除、PR 创建。判断标准是：这个动作的回滚成本高不高。
4. 从默认 workflow 复制再改，避免第一天就从空白 YAML 重新发明流程。默认 workflow 经过实战检验，复制再改能少踩很多语法坑。

## 边界与注意事项

工程选型先看边界。Archon 当前至少有 5 个限制：

### Archon 解决的是流程治理，不是模型能力替换

如果底层模型看不懂你的代码，Archon 不会把它变聪明。它解决的是流程确定性、隔离性和可追溯性。引入 Archon 前，先确认你的痛点是"流程不稳"还是"模型不够强"，后者换工具解决不了。

### Workflow 设计水平会直接决定输出上限

坏流程会把坏结果稳定放大。把流程写成 YAML 并不会自动得到好工程实践，反而要求你把隐含经验显式化。一个没有验证门的 workflow，比裸用 Agent 更危险，因为它会让坏结果披上"经过流程"的外衣。

### 不是所有任务都值得进 workflow

如果只是问一个函数是做什么的、为什么测试失败，直接用 `archon-assist` 或普通 Agent 往往更省成本。Archon 最有价值的地方，是多步、需要验证、需要隔离的任务。判断标准是：这个任务会不会被重复执行、需不需要回溯、错了能不能回滚。

### 文档目录变化很快，实际以本机 live list 为准

默认 workflow 数量、命名、bundled set 与文档目录的差异，是当前 Archon 非常真实的状态。不要把某一页 README 当唯一真相。升级版本后第一件事是跑 `archon workflow list`，确认本机实际可用的工作流。

### 人工审核仍然不可省略

Archon 提供了更好的审批点，但并不意味着你可以在数据库迁移、大规模重构、权限改造这类任务上完全放弃人工 review。approval gate 是流程里的一环，它不能替代有经验的工程师对不可逆动作的最终判断。

## 实践建议

- 从 `archon-idea-to-pr`、`archon-plan-to-pr`、`archon-feature-development` 三者中选一个作为团队起点，不要一开始就铺满所有 workflow。先让一个 workflow 跑稳，再扩展。
- 任何会改代码的任务，默认保留 worktree isolation；只有只读探索才考虑 `--no-worktree`。
- 把 workflow 当仓库资产来维护，和 CI、lint、脚本一样进入版本控制。workflow 变更应该走 code review，避免某个人偷偷改 YAML。
- 在 workflow 里优先放"组织步骤"和"验证门禁"，不要试图把所有聪明都塞进长 prompt。prompt 越长越难维护，验证门越多流程越稳。
- 每次升级 Archon 版本后，先运行 `archon workflow list` 和 `archon version`，再决定是否需要同步更新团队的自定义 workflow。内置 workflow 的语法和字段可能随版本变化，覆盖文件需要手动同步。

采用顺序：先在个人项目跑通 `archon-assist` 和 `archon-idea-to-pr` 的最小闭环，确认 worktree 隔离和 approval gate 对你有价值；再把一个团队高频流程（例如 PR 审查）写成自定义 workflow，验证它能否被团队复用；最后再考虑是否把所有开发任务都迁进 Archon。

## 常见问题

### Archon 是不是 Claude Code 的替代品？

Archon 不是 Claude Code 的替代品。它把 Claude Code、Codex 等编码能力拉进可编排流程，和底层 Agent 是编排器与执行器的关系。Claude Code 负责单个节点的推理和代码生成，Archon 负责把多个节点串成有依赖、有门禁的流程。

### 为什么我本机看到的默认 workflows 数量和文章里不一样？

因为 Archon 现在同时存在用户向导型文档、完整参考文档、源码中的 bundled defaults、仓库自定义 overrides 这几套来源。你本机的 live list 才是最终答案。文档目录展示的是"可能可用"的 workflow，本机 list 展示的是"实际可用"的 workflow。

### `archon-idea-to-pr`、`archon-plan-to-pr`、`archon-feature-development` 应该怎么选？

- 需求还只有一句描述，用 `archon-idea-to-pr`。它会先规划再实现。
- 已经有人给出 plan，用 `archon-plan-to-pr`。它跳过规划直接执行。
- 团队流程比较轻，只想从现有计划快速实现并发 PR，用 `archon-feature-development`。它的验证门更少，速度更快。

### 一定要用 Web UI 吗？

不一定。CLI 已经足够完成大多数个人使用场景。Web UI 的价值主要在于共享可见性、监控和团队协作。单人使用时 CLI 更轻量，团队引入时 Web UI 让运行状态对所有人可见。

### 我能不能只把 Archon 当作 workflow authoring system 来用？

可以，而且这恰恰是很多团队最终最看重的价值：把 workflow 作为仓库内可维护的工程资产，避免实践建议停留在某个成员脑子里。即使不使用内置 workflow，只用自己的 YAML，Archon 的编排引擎、worktree 隔离、approval gate 依然有效。

## 官方资源

- [GitHub 仓库](https://github.com/coleam00/Archon)
- [官方文档](https://archon.diy/)
- [Getting Started](https://archon.diy/getting-started/installation/)
- [Authoring Workflows](https://archon.diy/guides/authoring-workflows/)
- [CLI Reference](https://archon.diy/reference/cli/)
- [The Book of Archon](https://archon.diy/book/what-is-archon/)

---

## 资料口径说明

本文的判断基于以下来源和取径：

1. **项目文档分析**：分析了 `coleam00/Archon` 仓库的 GitHub README、官方文档（archon.diy）、Authoring Workflows 指南；仓库基本数据经 GitHub API 于 2026-08-05 验证（Stars 23,073、Forks 3,452、MIT、TypeScript、最新 release v0.7.1）
2. **CLI 命令验证**：基于 `archon workflow list` 的实际输出和官方文档中的命令说明
3. **架构分析**：基于文章中的 5 层架构拆解（入口层、编排层、执行层、AI 层、数据层）
4. **技术细节验证**：部分 YAML 语法和 CLI 命令来自官方文档和源码，实际使用时需要参考最新版本
5. **事实边界**：Archon 仍在快速迭代（截至 v0.7.1），文档和功能的对齐可能需要以本机实测为准

**局限性**：

- 默认 workflow 数量在官方文档不同位置可能有差异，本文以 README 提到的 17 个核心 workflows 为主
- YAML 语法在 v0.3.3 后有所演进（如 `context: fresh` 替代 `fresh_context: true`），需要注意版本兼容性
- 本文未实际运行所有 workflows，部分描述基于文档推断
- Web UI 功能可能需要额外配置，本文未深入安装细节

