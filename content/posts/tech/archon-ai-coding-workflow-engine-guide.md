---
title: "Archon：让AI编程变得可重复、可追溯的开源工作流引擎"
date: "2026-04-09T20:20:00+08:00"
slug: "archon-ai-coding-workflow-engine-guide"
description: "Archon 是一个面向 AI 编程的工作流引擎，通过 YAML 定义 DAG，把规划、实现、验证、评审与 PR 创建变成可重复、可审计、可复用的开发流程。本文系统拆解其工作流模型、worktree 隔离、默认工作流、上手路径与自定义方式。"
draft: false
categories: ["技术笔记"]
tags: ["Archon", "AI编程", "工作流引擎", "YAML", "Claude Code"]
---

如果你已经在使用 Claude Code、Codex 这类编码 Agent，很快会遇到同一个瓶颈：模型越来越强，但开发流程仍然靠“临时提示词 + 人工盯执行 + 手动补审查”维系。Archon 瞄准的缺口就在这里——让 Agent 按你定义的工程流程稳定工作。

一句话概括：Archon 是一个面向 AI 编程的 workflow engine（工作流引擎），也是一个 AI coding harness builder。你把开发流程写成 YAML，它负责把规划、实现、验证、评审、批准、PR 创建这些步骤编排成可重复执行的工程流水线。

> 本文基于 2026 年 4 月 11 日公开资料撰写。GitHub About 页显示，Archon 约有 18.3k Stars、2,861 Forks，最新 release 为 v0.3.6，项目采用 MIT 许可证，主体代码为 TypeScript。需要注意的是，官方文档面向入门用户时仍以 17 个核心 workflow 为主目录，但更完整的文档与源码里还能看到 additional workflows；最稳妥的确认方式始终是运行 `archon workflow list`。

学习目标

读完本文，可以：

1. 理解 Archon 的真正定位，以及它和“直接对着编码 Agent 下指令”之间的差别。
2. 说清 workflow、DAG、node、artifact、worktree isolation（工作树隔离）这些核心概念。
3. 判断 Archon 适合什么团队、不适合什么场景。
4. 通过官方推荐路径完成首次安装、运行和常用 CLI 操作。
5. 理解如何把内置 workflow 扩展成团队自己的开发流程。
6. 识别 Archon 当前文档体系中哪些信息稳定，哪些信息需要以本机实测为准。

导读

- 如果只需先判断 Archon 值不值得用，先看“先说结论”和“它适合谁，不适合谁”。
- 如果你想理解技术含量，重点看“工作流引擎是怎么运作的”和“为什么 worktree 隔离是工程核心”。
- 如果你准备马上试一遍，直接跳到“三条上手路径”和“真正常用的 CLI 操作”。
- 如果你打算把它引入团队流程，重点看“自定义 workflows”“边界与注意事项”“实践建议”。

术语速览

如果你是第一次系统接触 Archon，先把下面 6 个词记住，后面的理解成本会立刻下降。

| 术语 | 在 Archon 里的含义 | 先记住什么 |
| ------ | ------ | ------ |
| workflow | 用 YAML 定义的一条开发流程 | 它决定步骤、顺序、门禁和输出 |
| node | workflow 里的单个执行单元 | 可以是 AI、bash、script、approval 等动作 |
| DAG | 有向无环图执行模型 | 没有依赖的节点可以并行，有依赖的节点顺序执行 |
| artifact | 运行过程中生成的产物 | 可以是计划、总结、PR 编号、审查结果等 |
| worktree isolation | 基于 git worktree 的隔离执行环境 | 让多个任务并发运行而不互相污染 |
| approval gate | 人工审批门 | 让关键动作前的人工判断进入系统，而不是靠临时口头介入 |

先说结论：Archon 到底是什么

Archon 的定位在编排层，不在模型层。它把开发过程拆成有顺序、有依赖、有门禁的步骤——AI 只在需要智能的地方发挥作用，测试、脚本、验证、审批、分支隔离、工件沉淀这些工程动作则放进确定性框架里。

| 你关心的问题 | 直接使用单个 Agent 的典型状态 | Archon 提供的能力层 |
| ------ | ------ | ------ |
| 同一个需求每次结果都不一样 | 流程取决于模型当时怎么理解指令 | 用 workflow 固定步骤、顺序和门禁 |
| 多个任务并行容易互相污染 | 共用工作区，分支和文件状态容易冲突 | 每次运行默认进入独立 worktree |
| 很难知道 AI 到底做了什么 | 只能看零散终端输出或最终结果 | DAG 执行、事件、工件、状态全程可追溯 |
| 想在关键步骤插入人工审核 | 往往只能临时打断，流程不稳定 | approval / interactive 节点内建 human-in-the-loop |
| 团队希望复用同一套开发流程 | 最终只剩提示词，难以长期维护 | YAML workflow 可提交到仓库，团队共享同一流程 |
| 希望在 CLI、Web、聊天平台之间保持一致 | 不同入口各做一套 | 同一套 workflow 可跨 CLI、Web UI、Slack、Telegram、GitHub、Discord 复用 |

Archon 管的是“AI 如何进入工程体系”，不管“模型本身有多强”。

它适合谁，不适合谁

适合的场景

- 你已经在高频使用编码 Agent，希望把规划、验证、评审、PR 创建这些步骤标准化。
- 你所在的团队不只关心“能不能写出来”，还关心“过程是否可审计、可复用、可回放”。
- 你有并发任务，且不想让多个 AI 任务互相污染本地工作区。
- 你准备把团队实践建议沉淀成仓库内的 workflow 文件，而不是把经验散落在聊天记录里。

不太适合的场景

- 你只是偶尔问几个代码问题，或者只想让 Agent 快速看一段代码。
- 你的任务非常短平快，工作流编排的固定成本已经高于收益。
- 你当前真正缺的是“更强模型”或“更懂代码的提示词”，而不是流程治理。

最短判断标准只有一句话：如果你的痛点已经从“怎么让 AI 干活”转成“怎么让 AI 稳定地按流程干活”，Archon 才会显著放大价值。

为什么 Archon 值得关注

Archon 的讨论度来自一个事实：它把几个长期存在但一直没有工程化解决的问题，一次性拉进了同一套系统。

. 把随机聊天，变成可重复执行的流程

对着 Agent 说"修复这个 bug"，结果常常取决于模型这次有没有先规划、会不会主动运行测试、会不会遵守团队的 PR 模板。Archon 的做法是：把这些"不一定会发生"的步骤，提前写进 workflow。

. 把“看结果”升级成“看过程”

在团队环境里，最终 diff 只是结果的一小部分。更重要的问题是：它读了哪些上下文、跑了哪些验证、在哪一步卡住、为什么重试、人工是在什么环节介入的。Archon 通过 workflow run、event、artifact、review 这些对象，让过程本身变成可回放资产。

. 把单人技巧升级成团队流程资产

如果某个同事写出了一套非常有效的“规划 → 验证 → 审查 → PR”流程，传统做法通常只能把它存成提示词。Archon 的做法更接近基础设施：把流程写成 YAML，随仓库提交，交给整个团队反复复用和演进。

一个真实 workflow 是怎么跑完的

如果把 Archon 只理解成“写 YAML 然后交给 AI 跑”，还是太抽象。更贴近工程现实的理解方式，是把一次 workflow run 拆成下面这条执行链：

1. 你在 CLI、Web UI 或聊天平台发出需求。
2. Orchestrator 识别意图，解析 workflow 名称，必要时自动匹配最接近的 workflow。
3. 如果当前目录是一个 Git 仓库，Archon 会注册 codebase，并准备 workflow 运行上下文。
4. 对于会写代码的任务，隔离层创建或复用独立 worktree，并生成对应分支。
5. Workflow Executor 按 DAG 依赖关系启动节点；能并行的节点并行，必须等待的节点顺序执行。
6. AI 节点读上下文、调用模型；确定性节点执行测试、构建、脚本或 Git 操作。
7. 节点输出被写入 artifact 或结构化 output，供后续节点继续消费。
8. 如果流程中包含人工门禁，workflow 会暂停，等待 `approve` 或 `reject` 指令继续。
9. 完成后，结果、事件、消息、运行状态会被保留下来，供 Web UI、CLI 和后续排查使用。

走完这 9 步，输出就不再是聊天框里的一段回复了——它被保存为一条有状态、有产物、有历史、可排查的工程运行记录。

工作流引擎是怎么运作的

. Workflow 说到底是一个 DAG

Archon 把 workflow 定义成 directed acyclic graph（有向无环图，DAG）。每个 node（节点）声明自己要做什么，以及依赖哪些上游节点。没有依赖的节点可以并行运行；有依赖的节点等前置结果就绪后再执行。

下面是官方 authoring 文档里的典型结构，能比较准确地反映当前设计方向：

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

这个模型有三个工程价值：

1. **顺序是显式的**：流程不再藏在一大段提示词里，而是写成节点依赖图。
2. **并行是天然的**：同一依赖层的节点可以并发跑，例如多个 review agent 并行审查。
3. **输出可被消费**：上游节点的输出可以通过 `$nodeId.output` 传给下游，用于路由和条件判断。

. Archon 不只是“AI 节点 + Bash 节点”

很多介绍只会提 prompt 和 bash，但现在的 Archon 实际上已经有更丰富的工作流原语。

| 节点 / 能力 | 作用 | 什么时候用 |
| ------ | ------ | ------ |
| `command:` / `prompt:` | 让 AI 做规划、实现、审查、总结 | 需要模型推理和代码理解时 |
| `bash:` | 执行确定性的 shell 命令 | 跑测试、lint、构建、Git 操作 |
| `script:` | 运行内联 TypeScript / Python，或调用 `.archon/scripts/` | 需要比 shell 更可控的逻辑时 |
| `when:` | 根据上游输出做条件分支 | bug / feature 分流，复杂度分级 |
| `output_format:` | 约束 AI 输出为结构化 JSON | 路由、决策、下游消费 |
| `context: fresh` | 强制节点在新上下文里执行 | 避免长链任务上下文污染 |
| `provider:` / `model:` | 为节点指定 AI provider / model | 需要按任务类型切模型时 |

`script:` 特别值得关注。从官方 release 信息看，v0.3.3 开始，Archon 已经支持 script node，允许通过 `bun` 或 `uv` 运行内联 TypeScript / Python 或 `.archon/scripts/` 中的脚本。这让它不再只是“YAML + 提示词”的编排器，而更接近一个真正的工程自动化 runtime。

. Human-in-the-loop 不是一个开关，而是两种模式

Archon 在文档里明确区分了两种常见的人机协同模式。

Interactive loop

适合“看一版 → 给反馈 → 再迭代”的往返式过程，例如方案评审、PRD 打磨、PIV 循环。

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

Approval with on_reject

适合“先过门，再修复”的 gate-then-fix 模式。人类只在批准或驳回时介入；如果驳回，再由 AI 按明确原因修订。

```yaml
- id: review
  approval:
    message: "Review the report. Approve or request changes."
    capture_response: true
    on_reject:
      prompt: "Revise based on: $REJECTION_REASON"
      max_attempts: 5
```

Archon 在这里做对了一件事：把人类介入从临时行为提升成流程原语。

为什么 worktree 隔离是 Archon 的工程核心

Archon 最有工程含量的设计，是默认把可写任务放进独立 git worktree 里执行——YAML 编排只是它的表达层。

```bash
显式指定分支名运行 workflow
archon workflow run archon-idea-to-pr --branch feat/export-csv "Add CSV export to the reports page"

让 Archon 自动生成分支 / worktree
archon workflow run archon-idea-to-pr "Add CSV export to the reports page"

仅在确实需要时，才跳过 worktree 隔离
archon workflow run archon-assist --no-worktree "How does error handling work here?"
```

worktree 隔离直接解决了四个工程痛点：

- **并行安全**：多个任务可以同时运行，不用担心互相改坏同一个工作目录。
- **主工作区更干净**：AI 不需要直接在你的 live checkout 上反复试错。
- **结果天然可追踪**：每次运行对应一个分支 / worktree，方便回溯和清理。
- **和 PR 生命周期天然对齐**：从 feature 分支到 review，再到 merge，路径一致。

对团队来说，这几乎是 Archon 和“普通脚本编排 + Agent”之间最关键的差别。

架构拆解：从一句指令到一次工作流运行

从系统视角看，Archon 可以拆成 5 层：

| 层 | 组件 | 职责 |
| ------ | ------ | ------ |
| 入口层 | CLI、Web UI、Slack、Telegram、GitHub、Discord | 接收用户指令，触发 workflow |
| 编排层 | Orchestrator | 路由消息、管理上下文、决定调用哪个 workflow |
| 执行层 | Workflow Executor | 解析 YAML、执行 DAG、处理依赖、条件和循环 |
| AI 层 | Claude / Codex 等 Assistant Clients | 在指定节点执行推理、生成代码、做审查 |
| 数据层 | SQLite / PostgreSQL | 持久化 codebases、conversations、sessions、workflow runs、isolation environments、messages、workflow events |

这套架构的一个直接后果：同一套 workflow 在 Web UI、命令行和聊天平台之间行为一致。Archon 说到底是一个可被多入口复用的编排系统，本地 CLI 只是其中一个入口。

默认 workflows 怎么选，不要一上来就用最重的

官方 README 和 Getting Started 文档面向入门用户时，仍以 17 个核心 workflows 作为主目录。它们足够覆盖大多数团队的第一阶段需求。

个核心 workflows

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

真正常用的选型建议

| 你的目标 | 优先选择 |
| ------ | ------ |
| 先问代码库问题、做探索 | `archon-assist` |
| 从自然语言需求直接做功能 | `archon-idea-to-pr` |
| 你已经有成熟 plan，只想稳妥落地 | `archon-plan-to-pr` 或 `archon-feature-development` |
| 你只想 review 当前 PR | `archon-smart-pr-review` 或 `archon-comprehensive-pr-review` |
| 你要修 GitHub Issue | `archon-fix-github-issue` |
| 你要做人机反复协作的开发闭环 | `archon-piv-loop` |

一个容易踩坑但必须知道的事实

截至本文撰写时，官方不同位置对“默认 workflows 的数量”并不是完全同一套口径：

- README 和 Getting Started 强调的是面向用户最常用的 17 个核心 workflows。
- 更完整的文档还会出现 `archon-interactive-prd`、`archon-adversarial-dev`、`archon-workflow-builder` 等 workflow。
- 源码里和 binary distribution 相关的 bundled defaults 又可能比完整文档目录更精简。
- 不同文档示例的 YAML 语法也在演进，例如旧示例里常见 `fresh_context: true`，而新的 authoring 文档更强调 `context: fresh`、`approval`、`loop.interactive` 这套表达方式。

这不是文档错误那么简单，而是说明 Archon 仍在快速迭代。实践里不要死记清单，直接在目标仓库运行下面这条命令最可靠：

```bash
archon workflow list
```

如果你准备自己写 workflow，建议把 README 当成概念导览，把 [Authoring Workflows](https://archon.diy/guides/authoring-workflows/) 当成实际语法基准。

三条上手路径：别把普通用户、工作流作者、自托管用户混在一起

高质量技术文档最重要的一点，就是不要把不同读者的操作路径混在一起。Archon 至少有三条常见上手路线。

路线 A：第一次接触，用官方 setup wizard

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

向导会引导你完成 CLI 安装、认证配置、平台选择，以及把 Archon skill 复制到目标项目中。官方文档还特别强调了一点：**真正开始工作时，要在你的目标仓库里启动 Claude Code，而不是一直待在 Archon 自己的仓库里。**

路线 B：你已经装好 Claude Code，只想装 CLI

如果你已经具备 Claude Code 环境，只想快速拿到 Archon CLI，可以走 quick install。

```bash
macOS / Linux
curl -fsSL https://archon.diy/install | bash

Windows (PowerShell)
irm https://archon.diy/install.ps1 | iex

Homebrew
brew install coleam00/archon/archon

Docker
docker run --rm -v "$PWD:/workspace" ghcr.io/coleam00/archon:latest workflow list
```

安装后先做两步验证：

```bash
archon version
archon workflow list
```

路线 C：你想用 Web UI 观察和管理 workflows

Archon 不只有 CLI。官方文档显示，binary installs 可以直接通过 `archon serve` 下载并启动 Web UI；源码运行则可以从 Archon 仓库启动前端开发环境。

Web UI 最值得看的通常有四个页面：

| 页面 | 你会看到什么 |
| ------ | ------ |
| Chat | 实时对话与工具调用可视化 |
| Dashboard | workflow 监控、项目 / 状态 / 日期过滤 |
| Workflow Builder | 可视化拖拽编辑 DAG |
| Workflow Execution | 节点级进度和历史回放 |

如果你是团队引入者，Web UI 的价值不在“替代 CLI”，而在于让 workflow 运行从“个人终端事件”变成“团队可见事件”。

真正常用的 CLI 操作

除了 `archon setup`，实际使用中最常见的命令其实只有下面这些：

```bash
查看当前目录可用的 workflows
archon workflow list

运行 workflow
archon workflow run archon-idea-to-pr "Add dark mode to the settings page"

指定分支名运行
archon workflow run archon-idea-to-pr --branch feat/dark-mode "Add dark mode"

对另一个目录运行
archon workflow run archon-idea-to-pr --cwd /path/to/repo "Add dark mode"

不使用 worktree，直接在当前 checkout 上运行
archon workflow run archon-assist --no-worktree "How does error handling work here?"

查看运行状态
archon workflow status

恢复失败的 workflow
archon workflow resume <run-id>

放弃一个非终态 workflow
archon workflow abandon <run-id>

批准或驳回人工门禁
archon workflow approve <run-id> "Looks good, proceed"
archon workflow reject <run-id> "Please split the migration into two steps"
```

对实践者来说，有三个细节特别重要：

1. 写操作默认优先配合 worktree 隔离，不要把 `--no-worktree` 当常态。
2. `archon workflow list` 读取的是**当前工作目录**的可用 workflows，而不是某个全局固定目录。
3. 如果仓库里有和内置 workflow 同名的文件，仓库版本会覆盖 bundled default。

第一次成功的最小闭环

如果你不想一上来就跑最重的 feature workflow，最稳妥的首次体验顺序是：

```bash
. 确认 CLI 和 workflow 已就绪
archon version
archon workflow list

. 用轻量问题确认编排器能正常工作
archon workflow run archon-assist "What workflows are available here?"

. 再运行一个真正会创建 worktree 的写任务
archon workflow run archon-idea-to-pr --branch feat/hello-archon "Add a tiny docs-only improvement"

. 查看状态
archon workflow status
```

当你能稳定完成这四步，才算真正跑通了 Archon 的最小价值闭环：CLI 可用、workflow 可发现、AI 节点可执行、worktree 隔离生效。

新手最容易踩的 个坑

. 把 README 示例当成完整语法真相

README 适合快速建立直觉，但不适合作为 workflow authoring 的最终依据。真正写 YAML 时，应以 authoring 文档和本机 `archon workflow list` 的实际行为为准。

. 只关心 AI prompt，不关心验证门

很多人第一次写 workflow 时，会把精力全花在 prompt 上，却忘了把 lint、test、build 或 review gate 写进流程。这样得到的只是“更长的提示词”，不是“更强的工程流程”。

. 误把 `--no-worktree` 当默认选项

`--no-worktree` 适合只读探索，不适合常规写操作。你一旦习惯在 live checkout 上让 AI 反复试错，Archon 最重要的隔离价值就被你自己抹掉了。

. 写 interactive loop 时漏掉 `gate_message`

根据当前 workflow 校验逻辑，interactive loop 通常需要明确的 `gate_message`，否则用户很难知道在暂停点该输入什么，某些配置下也会直接触发加载错误。

. 忘了“同名文件覆盖默认 workflow”

如果仓库里放了和内置 workflow 同名的文件，它会覆盖 bundled default。这个特性非常强大，但也意味着你需要像维护 CI 配置一样认真维护这些 YAML。

自定义 workflows：Archon 的上限取决于你怎么建流程

Archon 的长期上限不取决于那 17 个默认 workflows。它取决于你能不能把自己的团队流程产品化——写成可提交、可复用、可演进的 workflow 文件。

自定义文件放在哪里

- workflow 文件放在 `.archon/workflows/`
- command 文件放在 `.archon/commands/`
- script node 相关脚本可放在 `.archon/scripts/`

官方文档明确说明：这些文件会从**当前仓库**运行时动态加载，而不是从一个全局模板目录静态拷贝。也就是你可以把 workflow 当作仓库基础设施的一部分来维护。

一个更接近真实团队流程的示例

下面这个例子展示的是“审查 → 人工批准 → 驳回后自动修订”的 gate-then-fix 模式：

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

这种设计比“让 AI 自己 review 自己”强得多，因为它把不可逆动作前的人类判断显式写进了系统。

还有一个细节值得记住：在 Web UI 里，带人工审批门的 workflow 通常还需要 workflow 级的 `interactive: true`，这样它会以前台交互方式运行，而不是完全丢到后台。这个约束在参考文档里写得比 README 更明确。

自定义时最值得坚持的 条原则

1. 一个节点只做一件事，不要把规划、实现、验证混在同一个 AI prompt 里。
2. 所有 AI 节点后面都跟一个确定性验证步骤，至少是测试、lint 或构建之一。
3. 重要决策前加 approval gate，例如数据库迁移、批量删除、PR 创建。
4. 从默认 workflow 复制再改，而不是第一天就从空白 YAML 重新发明流程。

动手练习

如果你想把“看懂”真正变成“会用”，建议按下面顺序做 3 个练习。

练习 ：确认你本机的真实 workflow 目录

目标：验证文档和本机 live list 的差异。

```bash
archon workflow list
```

做完后回答自己两个问题：

- 你本机看到的默认 workflows，和文章里列出的 17 个核心 workflows 有什么差异？
- 哪些 workflow 明显更适合你的当前项目，而不是“看起来最强大”的那个？

练习 ：跑一次只读探索 + 一次隔离写任务

目标：亲手感受 `archon-assist` 和 `archon-idea-to-pr` 的差异。

```bash
archon workflow run archon-assist "How is this repo structured?"
archon workflow run archon-idea-to-pr --branch feat/archon-practice "Add a tiny docs improvement"
```

重点观察三件事：

- 只读问题是否真的不需要进入复杂 workflow。
- 写任务是否创建了独立 branch / worktree。
- 运行状态和结果是否比普通聊天式操作更容易回溯。

练习 ：自己写一个最小审批流

目标：把“人类审核”从口头习惯变成系统流程。

1. 在 `.archon/workflows/` 新建一个极小 workflow。
2. 放入一个 review 节点、一个 approval gate、一个 publish 节点。
3. 用一个 docs-only 改动验证它能否暂停、等待批准并继续。

做完这一步，你就真正跨过了“用户”与“workflow author”之间的门槛。

边界与注意事项

顶级技术导读不能只讲优点，不讲边界。Archon 当前至少有 5 个现实限制需要先说明白。

. Archon 解决的是流程治理，不是模型能力替换

如果底层模型看不懂你的代码，Archon 不会把它变聪明。它解决的是流程确定性、隔离性和可追溯性。

. Workflow 设计水平会直接决定输出上限

坏流程会把坏结果稳定放大。把流程写成 YAML 并不会自动得到好工程实践，反而要求你把隐含经验显式化。

. 不是所有任务都值得进 workflow

如果只是问一个函数是做什么的、为什么测试失败，直接用 `archon-assist` 或普通 Agent 往往更省成本。Archon 最有价值的地方，是多步、可审计、需验证、需隔离的任务。

. 文档目录变化很快，实际以本机 live list 为准

默认 workflow 数量、命名、bundled set 与文档目录的差异，是当前 Archon 非常真实的状态。不要把某一页 README 当唯一真相。

. 人工审核仍然不可省略

Archon 提供了更好的审批点，但并不意味着你可以在数据库迁移、大规模重构、权限改造这类任务上完全放弃人工 review。

实践建议

- 从 `archon-idea-to-pr`、`archon-plan-to-pr`、`archon-feature-development` 三者中选一个作为团队起点，不要一开始就铺满所有 workflow。
- 任何会改代码的任务，默认保留 worktree isolation；只有只读探索才考虑 `--no-worktree`。
- 把 workflow 当仓库资产来维护，和 CI、lint、脚本一样进入版本控制。
- 在 workflow 里优先放“组织步骤”和“验证门禁”，不要试图把所有聪明都塞进长 prompt。
- 每次升级 Archon 版本后，先运行 `archon workflow list` 和 `archon version`，再决定是否需要同步更新团队的自定义 workflow。

常见问题

Archon 是不是 Claude Code 的替代品？

不是。Archon 是把 Claude Code、Codex 等编码能力拉进可编排流程的一层系统。它和底层 Agent 更像“编排器与执行器”的关系。

为什么我本机看到的默认 workflows 数量和文章里不一样？

因为 Archon 现在同时存在用户向导型文档、完整参考文档、源码中的 bundled defaults、仓库自定义 overrides 这几套来源。你本机的 live list 才是最终答案。

`archon-idea-to-pr`、`archon-plan-to-pr`、`archon-feature-development` 应该怎么选？

- 需求还只有一句描述，用 `archon-idea-to-pr`
- 已经有人给出 plan，用 `archon-plan-to-pr`
- 团队流程比较轻，只想从现有计划快速实现并发 PR，用 `archon-feature-development`

一定要用 Web UI 吗？

不一定。CLI 已经足够完成大多数个人使用场景。Web UI 的价值主要在于共享可见性、监控和团队协作。

我能不能只把 Archon 当作 workflow authoring system 来用？

可以，而且这恰恰是很多团队最终最看重的价值：把 workflow 作为仓库内可维护的工程资产，而不是把实践建议停留在某个成员脑子里。

自测清单

如果你读完本文后，能明确回答下面 5 个问题，说明你已经真正理解了 Archon：

1. 为什么 Archon 的关键价值不在“更聪明”，而在“更稳定”？
2. 为什么 worktree isolation 是它区别于普通脚本编排的重要工程能力？
3. 什么时候该用 interactive loop，什么时候该用 approval with on_reject？
4. 为什么默认 workflow 数量要以 `archon workflow list` 为准，而不是死记某一页文档？
5. 如果你要把团队的“实现后必须过 lint + test + 人工批准”写成系统流程，你会把哪些步骤做成 node？

进阶路径

如果你准备继续深入，推荐按下面顺序推进，而不是随机翻文档。

1. 先用 `archon-assist` 和 `archon-idea-to-pr` 跑通一次最小闭环，建立使用直觉。
2. 再读 Authoring Workflows，重点理解 `depends_on`、`when`、`output_format`、`approval`、`context`。
3. 然后查看 CLI Reference，把 `run`、`status`、`resume`、`approve`、`reject` 这些高频命令吃透。
4. 最后再去读 The Book of Archon 和 Architecture 相关文档，把“怎么用”升级成“为什么这样设计”。

这条顺序的目的只有一个：先建立操作感，再建立语法感，最后再建立系统设计感。这样学习成本最低，迁移到团队也最快。

总结

Archon 做的事情可以用一句话收住：把 AI 编程从一次性聊天，升级为可定义、可执行、可审计、可共享的工程流程。

如果你只是偶尔调用编码 Agent，这套编排可能显得偏重。但如果你已经在处理多任务并行、流程漂移、验证缺失、PR 质量不稳、团队经验无法沉淀这些问题，Archon 很可能是当前开源生态里最值得认真对待的一种答案。

官方资源

- [GitHub 仓库](https://github.com/coleam00/Archon)
- [官方文档](https://archon.diy/)
- [Getting Started](https://archon.diy/getting-started/installation/)
- [Authoring Workflows](https://archon.diy/guides/authoring-workflows/)
- [CLI Reference](https://archon.diy/reference/cli/)
- [The Book of Archon](https://archon.diy/book/what-is-archon/)
