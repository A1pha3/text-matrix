---
title: "OpenSpec 拆解：真正可复用的不是命令模板，而是把变更折叠回 specs 的归档器"
date: 2026-06-28T18:06:10+08:00
slug: "fission-ai-openspec-spec-driven-development-guide"
github_repo: "Fission-AI/OpenSpec"
source_key: "gh:Fission-AI/OpenSpec"
description: "对照 @fission-ai/openspec 1.13.1 与仓库 main 分支实跑一遍 openspec 的变更闭环：specs 与 changes 两个目录怎么分、delta spec 的四种操作、归档时怎么合并回真相、40 个工具目标靠 30 个命令适配器和 10 个 skills-only 落地，以及遥测在什么条件下才真的发出第一条数据。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Spec-Driven Development", "Claude Code", "Cursor"]
lastmod: "2026-09-21T10:05:00+08:00"
---

> **读者**：用过 Claude Code、Cursor 一类编码助手，正在判断「要不要把 spec 写进仓库、以及写进去的东西能不能跨工具活下来」的工程师。
>
> **读法**：先给系统地图，再把「数据格式」和「工具适配」两条线分开讲，最后给采用顺序、排查清单和一条一条可以照着跑的复核命令。
>
> **核对基线**：`@fission-ai/openspec` **1.13.1**（npm 发布于 2026-09-17）与仓库 `main` 分支提交 `bae58cf`（2026-09-17），核对日期 2026-09-21。本地实跑了 `init --tools claude,cursor`、`new change`、`validate`、`status`、`archive`、`list`、`doctor`、`config list`，在一个临时 git 仓库里走完一个真实变更的闭环，文中的命令输出都是这次跑出来的。没有实跑的是各 AI 工具客户端里的斜杠命令触发——那要装齐 40 个客户端；这类断言一律写成文档口径（标 `docs/...`），不和实测混在一起。

## 目录

- [一句话判断](#一句话判断)
- [仓库速览](#仓库速览)
- [系统地图](#系统地图)
- [五个概念](#五个概念)
- [实跑一遍完整闭环](#实跑一遍完整闭环)
- [命令行这一半](#命令行这一半)
- [工具适配这一半](#工具适配这一半)
- [两个独立开关](#两个独立开关)
- [与同类方案的差异](#与同类方案的差异)
- [遥测默认发什么](#遥测默认发什么)
- [适用边界与采用顺序](#适用边界与采用顺序)
- [出问题先查这几条](#出问题先查这几条)
- [仓库地址与参考](#仓库地址与参考)
- [自测题](#自测题)
- [练习](#练习)
- [下一步读哪里](#下一步读哪里)
- [常见问题](#常见问题)

## 一句话判断

OpenSpec 里最值得留下的东西，不是那 12 条工作流命令的提示词模板，而是两样更朴素的东西：一份可以 diff 的「系统当下行为」（`openspec/specs/`），和一个会把提案合并回这份行为的归档器。

理由来自它自己的代码组织。命令模板那一层要为 40 个目标各写一遍：30 个目标有专属的命令适配器，另外 10 个连命令文件都不生成、只靠 skill 触发。同一个意图在 Claude Code 叫 `/opsx:propose`、在 Cursor 叫 `/opsx-propose`、在 Amazon Q 要打成 `@opsx-propose`、在 Codex 是 `$openspec-propose`。一个需要按工具各写一遍的东西，本身就是被适配的对象，不是资产。而「delta 怎么并进主 spec」只有一份实现（`src/core/specs-apply.ts`），归档后落到磁盘上的又只是一种 Markdown 目录结构。工具换了，模板要重新生成，specs 不用重写。

所以判断是：**把它当数据格式加进来是划算的，把它当提示词框架加进来是脆弱的。** 下面按这个判断展开。

## 仓库速览

| 项目 | 信息（核对时间 2026-09-21） |
|------|------|
| 仓库 | [github.com/Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) |
| 描述 | Spec-driven development (SDD) for AI coding assistants. |
| 语言 / 许可证 | TypeScript / MIT |
| 仓库建立 | 2025-08-05；npm 首个版本 `0.1.0` 发布于 2025-09-06 |
| 当前版本 | `1.13.1`，npm 发布 2026-09-17；累计发布 49 个版本 |
| 关注度 | 69,684 stars、4,772 forks；开放 issue 125 个、开放 PR 119 个。注意 GitHub 的 `open_issues_count` 字段把两者合并报（此刻是 244），很多脚本把它当「issue 数」用 |
| 安装 | `npm install -g @fission-ai/openspec@latest` |
| 运行要求 | Node.js 20.19.0 及以上（`package.json` 的 `engines`） |
| 运行时依赖 | 10 个：commander、zod、yaml、chalk、ora、fast-glob、diff、cross-spawn、@inquirer/core、@inquirer/prompts |
| 代码规模 | `src/` 196 个 `.ts` 文件、47,978 行；`test/` 209 个文件 |
| 工具目标 | 注册表 `AI_TOOLS` 共 40 项（`src/core/config.ts:41` 起），README 对外写的是 "30+ tools" |

「仓库 2025-08-05 建立」和「npm 首发 2025-09-06」是两个不同的日期，很多介绍会把它俩混成一个。星标数这类数字只会随时间变，看的时候以自己现场查一次 GitHub 的结果为准。

## 系统地图

`docs/overview.md` 用一张图放下全部结构，我按当前版本的工作流名单重画一遍：

```text
                ┌──────────────────────────────────────────────┐
                │                  openspec/                   │
                │                                              │
                │  ┌────────────────┐      ┌───────────────┐   │
                │  │    specs/      │      │   changes/     │   │
                │  │                │ ◄─── │  一个变更一个   │   │
                │  │ 系统当下行为    │ 归档  │  文件夹        │   │
                │  │ <域>/spec.md   │ 合并  │  proposal.md   │   │
                │  │                │      │  design.md     │   │
                │  │ 需求 + 场景     │      │  tasks.md      │   │
                │  │                │      │  specs/<域>/    │   │
                │  └────────────────┘      │   spec.md ←差异 │   │
                │                          ├───────────────┤   │
                │                          │ archive/      │   │
                │                          │ 2026-09-21-xxx│   │
                │                          └───────────────┘   │
                │  config.yaml：schema: spec-driven + 项目上下文 │
                └──────────────────────────────────────────────┘

        你的终端（命令行工具）                    AI 助手的对话框
   ┌───────────────────────────┐      ┌──────────────────────────────┐
   │ openspec init             │ 装进 │ /opsx:explore                │
   │ openspec list / view      │ ───► │ /opsx:propose add-dark-mode  │
   │ openspec validate / show  │ 文件 │ /opsx:apply                  │
   │ openspec archive          │      │ /opsx:update · sync · archive│
   └───────────────────────────┘      └──────────────────────────────┘
      引擎：知道规则                      方向盘：每个工具各一种手感
```

两条二分法撑起整个项目：

1. **数据二分**：`specs/` 回答「现在是怎么回事」，`changes/` 回答「打算改成什么样」。归档是两者之间唯一的写入通道。
2. **执行二分**：`openspec ...` 跑在终端，`/opsx:...` 跑在对话框。`docs/how-commands-work.md` 专门为此写了一整页，因为最常见的第一次失败就是把 `/opsx:propose` 敲进 shell。

## 五个概念

`docs/overview.md` 把模型收在五个词上。下面每个都补一条我在这一版里能验证的细节。

### 一、Specs 是当下真相

放在 `openspec/specs/`，按域分目录（`auth/`、`payments/`、`ui/`）。一份 spec 由需求（"The app SHALL ..."）和场景（`#### Scenario:` 配 `WHEN`/`THEN`）组成，格式就是普通 Markdown。

细节：这个「普通」是有硬边的。校验器要求**每条需求至少带一个场景**，否则 `openspec validate` 直接报 ERROR（`src/core/validation/validator.ts:306`）。我故意写了一条没场景的需求，拿到的原文是：

```text
✗ [ERROR] ui/spec.md: ADDED "No scenarios" must include at least one scenario
```

### 二、Change 是一个工作单元

想加、改、删某种行为，就建一个 change：`openspec/changes/<名字>/` 一个文件夹装下这件事的全部产物。命令行工具（CLI）这一侧的 `openspec new change <名字>` 只会建目录和一个 `.openspec.yaml`，里面记两样东西：用哪套工作流模式（值是 `spec-driven`），以及创建日期。四份文档要由助手或你自己写，三处结构要求各不相同：proposal 认 `## Why` 与 `## What Changes`，缺了只给警告；`specs/` 里的 delta 标题和场景是 ERROR 级，写错就过不了校验；`design.md` 与 `tasks.md` 没有强制标题。proposal 那条警告我故意撞过一次，归档照样成功。

### 三、Delta specs 只描述差异

change 里不重写整份 spec，只写差异。差异标题**恰好四种**：`## ADDED Requirements`、`## MODIFIED Requirements`、`## REMOVED Requirements`、`## RENAMED Requirements`（`src/core/parsers/requirement-blocks.ts:277`）。`MODIFIED` 不是补丁——它要带着保留下来的全部场景整体替换旧块，所以 `openspec show <change> --diff` 才存在：把新块和它替换掉的旧块并排 diff 出来。

这一条决定了它对存量系统的可用性。官方口径写在 `docs/overview.md`：「Deltas mean you can specify a change to a 50,000-line app without first documenting the whole thing」——不用先把五万行文档化，才能开始下一处改动。

### 四、产物互相递进，但依赖是软的

```text
proposal ──► specs ──► design ──► tasks ──► implement
   why        what       how       steps      do it
```

「软」在源码里看得见。`openspec status` 会告诉你依赖关系，但用的是可绕过的措辞而不是拒绝：

```text
Progress: 0/4 artifacts complete

[ ] proposal
[-] specs (blocked by: proposal)
[-] design (blocked by: proposal)
[-] tasks (blocked by: specs, design)
```

写完全程也没有门禁拦你。文档管这叫 enablers, not gates。代价是纪律：没有任何机制阻止 `design.md` 和实现各走各路。

### 五、归档把变更折回真相

`archive` 做两件事：把 delta 并进主 specs，再把 change 文件夹搬进 `changes/archive/<日期>-<名字>/`。这一步的实跑输出我完整贴在下一节。

值得单独说的是：`/opsx:sync` 是这条合并逻辑的独立入口。合并本身归档时就会做（我实跑的 `archive` 输出里那几行 `Applying changes to ...` 就是它），文档也说归档会按需提示同步，所以日常不必手动跑 `sync`。真要用它的场景是「长命 change 想让主 specs 先追上」或「几个并行 change 都依赖同一份基线」（`docs/commands.md:450`）。sync 不归档，change 仍然活着。

## 实跑一遍完整闭环

以下是我在临时仓库里实跑抓到的输出，没有改写过任何一行；`$` 开头的命令行是我补上的（个别命令把进度提示写到 stderr，我是两个流合起来截的，用 `2>/dev/null` 复跑时会少掉 `- Setting up Claude Code...` 那几行）。这段顺带回答了「归档到底往磁盘上写了什么」这个多数介绍不会展示的问题。

```console
$ git init -q . && openspec init --tools claude,cursor --no-animation
- Creating OpenSpec structure...
▌ OpenSpec structure created
- Setting up Claude Code...
✔ Setup complete for Claude Code
- Setting up Cursor...
✔ Setup complete for Cursor

OpenSpec Setup Complete

Created: Claude Code, Cursor
6 skills and 6 commands in .claude, .cursor/
Config: openspec/config.yaml (schema: spec-driven)

Getting started:
  Start your first change: /opsx:propose "your idea" (Claude Code)
  Start your first change: /opsx-propose "your idea" (Cursor)

Note: 6 more workflows are available (new, continue, ff, bulk-archive, verify, onboard).
Add them with `openspec config profile`.

Learn more: https://github.com/Fission-AI/OpenSpec
Feedback:   https://github.com/Fission-AI/OpenSpec/issues

Restart your IDE to refresh commands.
```

注意两处细节：它按你选的工具分别打印可点的调用形式，末尾还要你重启集成开发环境。这两件事都不是装饰——同一个 `propose` 在两个工具里确实是两种拼法，而多数工具只在启动时扫一遍 skill 目录。

```console
$ openspec new change add-dark-mode
Created change 'add-dark-mode' at openspec/changes/add-dark-mode/
Schema: spec-driven
Next: openspec status --change add-dark-mode

$ # 手写 proposal.md / specs/ui/spec.md / design.md / tasks.md
$ openspec validate add-dark-mode
Change 'add-dark-mode' is valid

$ openspec archive add-dark-mode -y
Task status: ✓ Complete

Specs to update:
  ui: create
Applying changes to openspec/specs/ui/spec.md:
  + 1 added
Totals: + 1, ~ 0, - 0, → 0
Specs updated successfully.
Change 'add-dark-mode' archived as '2026-09-21-add-dark-mode'.
```

`Totals` 那行的四个记号就是四种 delta 操作的合并结果。归档后 `openspec/specs/ui/spec.md` 长这样：

```markdown
# ui Specification

## Purpose
TBD - created by archiving change add-dark-mode. Update Purpose after archive.

## Requirements

### Requirement: Theme selection
The app SHALL let users switch between light and dark themes, defaulting to
the system preference.

#### Scenario: User toggles dark mode
- **WHEN** the user clicks the theme toggle
- **THEN** the app switches to dark mode and persists the choice
```

新建能力时 `Purpose` 会留成 `TBD`，并明写「归档之后去补」。这是归档器诚实的地方，也是容易被忽略的义务：机器能把需求并进去，不能替你写出这个域到底负责什么。

另外两件实测出来的行为，对判断「能不能信它」比上面那段更关键：

- **没做完的任务不会拦住归档。** `tasks.md` 里留一个未勾选项，`openspec archive` 在交互模式下会问你（默认答案是不），带 `-y` 时只打一行警告继续（`src/core/archive.ts:1365`）；`--json` 且没有 `--yes` 才抛错，错误码 `archive_tasks_incomplete`。
- **归档目标名在动任何 spec 之前算好。** 同一天第二次归档同名 change 是常事，若等到合并之后再发现冲突，specs 已经被改而变更没归档（`src/core/archive.ts` 在那段前面留了注释说明这个次序是刻意的）。

## 命令行这一半

`openspec --help` 在 1.13.1 下列出 23 个顶层条目，早就不止 `init` / `list` / `view` 三个：

```text
init  update  list  view  change  archive  spec  config  schema  schemas
store  doctor  context  workset  validate  show  feedback  completion
status  instructions  templates  new  help
```

其中 `doctor`、`context`、`workset`、`store` 属于较新的「多仓库/共享规划」那条线，`instructions` 和 `templates` 是给助手用的取数出口（`openspec instructions proposal --change X --json`）。这一半是引擎，也刻意做成可被程序读的：仓库里专门有一份智能体契约（`docs/agent-contract.md`），把机器可读输出当成一等接口来写。它在文件头声明所有形状都是从发射它的代码里推出的（`verified against src/`，2026-06-11 的一次审计），但正文只给 JSON 键名与语义，没有逐条标到 `文件:行号`。三条最实用的约定：

- 一次 `--json` 调用只输出一个 JSON 文档，人类可读文字、进度动画和 store 横幅一律走 stderr，所以管道不会被污染。
- 每条机器诊断共用一个信封：`severity` / `code` / `message` / `target` / `fix`，`fix` 里是一条能直接抄的命令。
- 键名风格按输出面不同：store、doctor、context 用 `snake_case`，工作流类输出（`status`、`instructions`、`validate`、`list`）用 `camelCase`。契约文档自己也把它列为已知不一致，写脚本时别按一套猜。

我实测的 `openspec list --json` 输出：

```json
{
  "changes": [],
  "root": { "path": "/private/tmp/osx/demo", "source": "nearest" }
}
```

`root.source` 是根目录解析来源（`nearest` / store 指针 / 全局默认），脚本据此判断「我到底在替哪个仓库规划」。而在没有 `openspec/` 的目录里跑，得到的是：

```text
✖ Error: No OpenSpec root found from the current directory.
Fix: Run openspec init to create a root here.
```

## 工具适配这一半

`src/core/config.ts:41` 起的 `AI_TOOLS` 有 40 项，全部标着 `available: true`。最后一项是兜底目标 `agents`，显示名直接叫 "Other / Universal (shared .agents skills)"，服务的是名单之外的助手。它还带九个搜索别名（`universal`、`other`、`generic`、`vendor-neutral`、`agents.md` 之类），因为光看一个目录名没人猜得到该选什么。40 这个数字可以拆开核对：`src/core/command-generation/adapters/` 下有 30 个工具适配器（该目录另有 1 个汇总入口），`docs/supported-tools.md` 的路径表里有 10 行标着 "Not generated"。30 + 10 = 40，两边对得上。

它生成的东西分两类，路径随工具而异：

| 工具 | 斜杠命令怎么写 | 命令文件路径 |
|------|----------------|--------------|
| Claude Code | `/opsx:propose` | `.claude/commands/opsx/<id>.md` |
| Cursor | `/opsx-propose` | `.cursor/commands/opsx-<id>.md` |
| GitHub Copilot | `/opsx-propose` | `.github/prompts/opsx-<id>.prompt.md`（提示词文件） |
| Amazon Q | `@opsx-propose` | `.amazonq/prompts/opsx-<id>.md` |
| Gemini CLI | `/opsx:propose` | `.gemini/commands/opsx/<id>.toml` |
| Codex | `$openspec-propose` | 不生成（只有 skill，落在 `.agents/skills/`） |
| Kimi Code | `/skill:openspec-propose` | 不生成（只有 skill，落在 `.kimi-code/skills/`） |
| Devin Desktop | `/opsx-propose` | `.devin/workflows/opsx-<id>.md` |

「命令文件不生成」不代表不支持，只是换一种触发方式。`docs/supported-tools.md` 里有 10 行这么标；官方排错页把它列成第六步排查项，点名的却只有 8 个：Codex、CodeArts、ForgeCode、Hermes、Kimi Code、Mistral Vibe、Zed Agent 和兜底的 `.agents`。少写的那两个各有各的原因——MiniMax Code 只写用户目录下的 `~/.minimax/skills/`，Rovo Dev CLI 则根本没有斜杠命令这一层，只能靠它自己按名字或描述挑中 skill。在这些工具里 `/opsx` 永远不会自动补全，这是设计如此。

三个改名值得单独记住，因为网上大量介绍写的是改名前的状态：

- **Windsurf 已是 Devin Desktop。** 上游在 2026-06-02 改名并搬了配置目录，现在读写用 `.devin/`，`.windsurf/` 降级为只读回退。工具 ID 是 `devin`，但 `--tools windsurf` 仍然解析到它，老脚本不会坏。
- **Codex 从 `.codex/` 换到共享根 `.agents/`。** 它现在是 skills-only：不再生成 `$CODEX_HOME/prompts/` 下的全局提示文件，`$openspec-propose` 才是可打的形式，`/openspec-propose` 在 Codex CLI 里不被识别。
- **Kimi CLI 改名 Kimi Code，目录从 `.kimi/` 换成 `.kimi-code/`**，旧安装会被自动迁移。

还有一处容易写错的映射：命令 ID 和 skill 名不是一一对应。`/opsx:apply` 对应的 skill 叫 `openspec-apply-change`，`/opsx:sync` 叫 `openspec-sync-specs`。我在 Claude Code 目录下看到的 6 个文件夹是 `openspec-{propose,explore,apply-change,update-change,sync-specs,archive-change}`。想凭 `/opsx:<id>` 拼 skill 目录名，会有一半拼不上。

生成出来的每份 skill 都带一行 `allowed-tools: Bash(openspec:*)`，字面读法是把这条 skill 允许的命令面收在 `openspec` 前缀上。它在你机器上究竟换来多少次免确认，我没有装客户端去实测，属于要自己验的一格；能确认的是这一行是刻意加的而不是模板残留——仓库里那条还没归档的 change `add-skill-cli-auto-approval` 就是在推进它。

命令文件里则写死了计划边界：`propose` 的正文要求助手只产出计划文档，产出后停下、不在同一轮开始实现，等一次新的用户指令再走 apply——即便最初那句话听起来像是在要求修 bug。

## 两个独立开关

profile 和 delivery 常被混为一谈，实际是两个维度（`src/core/global-config.ts:11`）：

```console
$ openspec config list
featureFlags: {}
profile: core
delivery: both

Profile settings:
  profile: core (default)
  delivery: both (default)
  workflows: propose, explore, apply, update, sync, archive (from core profile)
```

这份输出取自一个干净的用户目录。首次告知弹过之后，`profile` 之上还会多出 `telemetry:` 一段，里面是 `noticeSeen` 和一个匿名 ID。

- **profile 决定装哪几条工作流**：`core` 是 6 条（`propose`、`explore`、`apply`、`update`、`sync`、`archive`，见 `src/core/profiles.ts:14`），`custom` 是你自己挑。全部可选的是 12 条，多出来的 6 条为 `new`、`continue`、`ff`、`verify`、`bulk-archive`、`onboard`。`profile` 只有 `core` 和 `custom` 两个字面值，`docs/` 里把后一组称作 expanded workflows，那是描述不是取值。
- **delivery 决定每个工具落成什么形态**：`both`（默认）、`skills`、`commands`。选 `commands` 时那 10 个 skills-only 工具里只有 Codex 还能拿到东西——文档为它单开了例外：`delivery` 设成 `commands` 也照样给它装 `.agents/skills/`。其余 9 个这次什么都不落地，`init` 会点名它们并打出「跑 `openspec config set delivery both` 才能生成」这句纠正。我实跑过这一格：`.kimi-code/` 压根没被创建，`.agents/skills/` 里六份 skill 齐全。

`openspec update` 是这一版里值得记住的日常入口。它管的是「已生成的文件与当前 CLI 是否一致」：升级 CLI 之后在项目里跑一次，会重刷 skill 与命令文件，也会把手改坏或被截断的 `SKILL.md` 恢复回来。比对范围在 1.13.0 扩大过一次，命令文件的内容现在也一起比（CHANGELOG 1.13.0）。文档对「命令不见了」的第二条建议就是它。

## 与同类方案的差异

README 里三段对比是原话，我把能核对的部分量化了一遍：

**vs GitHub Spec Kit。** README 的说法是 "Thorough but heavyweight. Rigid phase gates, lots of Markdown, Python setup"。安装面这一条可以直接核：Spec Kit 的主仓库确实是 Python（看 GitHub 的 `language` 字段）。OpenSpec 这边是一个 npm 包、10 个运行时依赖，本文所有命令都在一台没有配任何模型密钥的机器上跑通。但这条差异只覆盖上手成本，不覆盖产物重量——OpenSpec 一个 change 也是四份 Markdown。

**vs AWS Kiro。** README 的说法是 "Powerful but you're locked into their IDE and limited to Claude models"——锁在自研的集成开发环境里，模型也只剩一家可选。OpenSpec 侧的对应事实是它不持有模型通道，只在 README 里给建议：「works best with high-reasoning models」，推荐 Codex 5.5 与 Opus 4.7。这是建议不是限制。

**vs 不写 spec。** README 的说法是 "AI coding without specs means vague prompts and unpredictable results"。补一条我自己认同的：不写 spec 时丢失的不是可预测性，而是**六个月后能复核的现场**。聊天历史里没人回去找。

## 遥测默认发什么

`src/telemetry/` 是唯一出口，读码即可定案。README 那边只给了摘要："We collect only command names and version"，源码里的边界比这句更值得看：

- 事件名 `command_executed`，属性是 `command`、`version`、`surface: "cli"`，并且显式写了 `$ip: null` 关掉 IP 追踪；发往 PostHog 的 `/batch/`，host 是自己的 `edge.openspec.dev`（遥测模块第 179 行拼属性、第 146 行发请求、第 32 行定义那个 host）。
- **首次告知未出现之前，一条都不发。** `trackCommand` 先看 `noticeSeen`，没告知过就直接 return——不发数据也不生成匿名 ID。而 `--json` 模式会推迟告知（打印会破坏机器可读输出）。也就是说，如果你所有调用都带 `--json`，实际上从未被统计过（同文件 173 行的提前返回）。
- 关闭方式按优先级：`OPENSPEC_TELEMETRY` 取任何非「开」值即关；`DO_NOT_TRACK` 取任何非「关」值即关；`CI` 为真即关；`openspec config set telemetry.enabled false` 关。配置文件读不出来时也**当作关**——注释里的原话是 "Unknown is not consent"。

这套判断值得在意，因为「默认收集匿名统计」这类摘要，容易让人以为环境变量才是唯一的闸门。

## 适用边界与采用顺序

**先说什么时候不必用它。** 三类：

- 一行文案级修复。四份产物的仪式对它是净成本，而它也不会在 `specs/` 里留下任何新真相。
- 纯玩具的 greenfield 项目。`specs/` 的价值在于描述一份已经存在、且会被人或助手改坏的行为；还没有行为时它是空转。
- 拒绝归档纪律的团队。这是我认为唯一真正致命的负收益场景：delta 并进主 specs 只发生在归档那一刻，绕开归档改代码，`specs/` 立刻从资产变成一份会说谎的文件，而且比没有文件更糟。

**采用顺序**（每一步都给了可核对的验收条件）：

1. **第一次：在临时目录跑完闭环，不碰真实项目。** 验收：`openspec archive` 打出 `Totals` 行，且 `openspec/specs/<域>/spec.md` 里能看到需求与场景，`changes/archive/<日期>-<名>/` 里有原文件。我上面那串命令可以照抄。
2. **第二次：给一个真实但不关键的项目初始化，只写 delta。** 验收：`openspec validate <change>` 通过，并且你能用 `openspec show <change> --diff` 指出这条 `MODIFIED` 替换掉了哪一段。
3. **第三次：连做三个真实变更，只看不改。** 验收：第三个变更后 `openspec/specs/` 仍然描述得清系统当前的行为，`Purpose` 里的 `TBD` 都补掉了。补不掉说明归档在攒债。
4. **然后才谈团队。** 配置 `--tools` 按团队实际组合挑，别一上来 `--tools all`——40 个目标会在你的仓库里生成一大片目录。

   跨仓库规划是 `store` 的位置：`.openspec-store/store.yaml` 给一个纯规划仓库做身份，`openspec store` 的 `setup / register / unregister / remove`（另有 `list` 与 `doctor`）管理本机注册表。README 与 stores 指南都把它标成 beta；指南里还有一句边界值得原样抄下来——"OpenSpec never clones, syncs, or pushes anything on its own"，同步仍然完全交给你自己的 git。

**几个常被忽略的入口**：`openspec init --language "Portuguese (pt-BR)"` 把语言要求写进 `openspec/config.yaml` 的 `context`，生成的产物用该语言；但结构性标题和 `SHALL`/`MUST` 会保持英文，因为校验依赖它们（`docs/multi-language.md`）。`--force` 用来不询问地清理历史文件。`--copilot-cloud` / `--no-copilot-cloud` 单独决定要不要顺手配 GitHub 托管的云端编码代理。

## 出问题先查这几条

照录官方排错页的六步（它自己就是按「最快能查」排的）：

1. **先看是不是敲错了地方。** `/opsx:propose` 进终端不会有任何反应，斜杠命令只在对话框里生效；反过来说 `openspec` 开头的小写命令也不是助手会执行的。
2. **跑一次 `openspec update`。** 它按已装 CLI 重新生成全部 skill 与命令文件。文档特别提醒：指令文件来自**已安装**的那份 CLI，旧 CLI 会把一切都报成「已是最新」却永远写不出新工作流，所以它会主动提议升级。
3. **重启助手。** 多数工具只在启动时扫一次目录，开新窗口即可。
4. **确认文件真的存在。** Claude Code 看 `.claude/skills/` 下有没有 `openspec-*` 文件夹，其他工具看各自的目录。
5. **确认你初始化的是当前这个项目。** skill 是按项目写的，克隆新仓库或切目录后要再 `init` 或 `update`。
6. **确认你的工具是否属于 skills-only 那一组。** 它们没有命令文件，`/opsx` 不补全是设计如此，不是坏了。

另外三条我撞到过、文档没排在显眼处的：

- `openspec new change` 不接受 `--no-interactive`（会报 `unknown option`）。非交互开关每条命令叫法都不一样：`validate` 是 `--no-interactive`，`archive` 是 `-y` 与 `--json`，别猜。
- 需求漏写场景是最高频的 ERROR，报错位置精确到 `<域>/spec.md`，并直接给你 `openspec show <change> --json --deltas-only` 去看解析结果。
- proposal 少写 `## What Changes` 只是非阻塞警告，我故意缺过一次，归档照样成功；而归档后 `Purpose` 里那行 `TBD` 连警告都没有，只能自己回去补。这两处都不该被读成「已经写对了」。

## 仓库地址与参考

- 仓库：[github.com/Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) · 站点：[openspec.dev](https://openspec.dev/) · 包：[@fission-ai/openspec](https://www.npmjs.com/package/@fission-ai/openspec)
- 本文引用的仓库内文档：

  ```text
  docs/overview.md            五个概念与那张系统地图
  docs/how-commands-work.md   终端与对话框两半分工
  docs/supported-tools.md     40 个目标、路径表与 How To Invoke
  docs/commands.md            斜杠命令参考，含 /opsx:sync 的语义
  docs/agent-contract.md      机器可读输出的一等约定
  docs/multi-language.md      --language 与保留英文的结构标题
  docs/troubleshooting.md     命令不出现时的六步排查
  ```

- 源码定位（本文标出的行号都出自这些文件）：

  ```text
  src/core/config.ts                        工具注册表 AI_TOOLS
  src/core/profiles.ts                      CORE_WORKFLOWS / ALL_WORKFLOWS
  src/core/global-config.ts                 Profile 与 Delivery 两个维度
  src/core/parsers/requirement-blocks.ts    四种 delta 标题
  src/core/validation/validator.ts          需求必须带场景
  src/core/archive.ts                       未完成任务与归档目标名
  src/core/specs-apply.ts                   delta 合并进主 spec
  src/telemetry/index.ts                    事件形状、noticeSeen 闸门
  ```

- 想核对本文的版本边界，一条命令就够：`git show v1.4.1:src/core/config.ts | grep -c "available: true"` 输出 30，当前同一处输出 40。很多「OpenSpec 支持 25+ 工具、Codex 把命令装进 `$CODEX_HOME/prompts`」的说法，是 1.4.x 那一版的快照。

## 自测题

先自己想一遍，再展开对照：

<details>
<summary>1. 一个 change 的 delta 有哪几种操作？为什么 MODIFIED 需要带全场景？</summary>

四种：`ADDED`、`MODIFIED`、`REMOVED`、`RENAMED`（`src/core/parsers/requirement-blocks.ts:277`）。`MODIFIED` 在合并时是整块替换而不是打补丁，所以要保留它继续生效的全部场景，否则那些场景在合并后消失。想知道替换掉什么，用 `openspec show <change> --diff`。
</details>

<details>
<summary>2. 归档会做几件事？如果 tasks.md 里还有未勾选项会怎样？</summary>

两件事：把 delta 并进 `openspec/specs/`，把 change 文件夹搬到 `changes/archive/<日期>-<名字>/`。未完成任务不会硬拦：交互模式弹确认且默认不继续，带 `-y` 只警告后继续，`--json` 且没有 `--yes` 才抛错，错误码 `archive_tasks_incomplete`（`src/core/archive.ts:1365`）。
</details>

<details>
<summary>3. profile 和 delivery 各管什么？</summary>

profile 管装哪几条工作流，取值只有 `core`（6 条，含 `update`）和 `custom`；`docs/` 里的 expanded workflows 指的是后一组可选项，不是合法取值。delivery 管每个工具落成什么形态，取值 `both` / `skills` / `commands`。两者独立，`commands` 配上 skills-only 工具（Codex 除外）会得到空结果，`init` 会提示这一处配置矛盾。
</details>

<details>
<summary>4. 为什么在 Codex 里 `/opsx` 永远不自动补全？</summary>

因为 Codex 是 skills-only 目标：OpenSpec 只给它写 `.agents/skills/openspec-*/SKILL.md`，不生成命令文件。它的可打形式是 `$openspec-propose`，而 `/openspec-propose` 在 Codex CLI 里不被识别。其余同样没有命令文件的目标，正文已把 10 个列全。
</details>

<details>
<summary>5. 哪种情况下 OpenSpec 会明显帮倒忙？</summary>

团队不遵守归档的时候。delta 只在归档那一刻并进主 specs，绕开归档直接改代码，`specs/` 就落后于实现；一份会说谎的文档比没有文档更贵，因为下一个人和下一个助手都会照它行动。修复方式是把差异补成一个 change 再归档，长期做法是「改行为必过 change」。
</details>

## 练习

四条都在本地跑，不需要装任何 AI 工具。

### 练习 1：不看文档复现一次闭环（约 30 分钟）

在临时目录里 `git init -q .`，`openspec init --tools claude`，`openspec new change t1`，然后只凭「每条需求至少一个场景」这一条规则写四份产物，跑 `openspec validate t1` 与 `openspec archive t1 -y`。

做完回答三件事：`openspec/specs/` 下多了什么？`Purpose` 里那行 `TBD` 是谁的义务？`changes/archive/` 下的目录名是怎么拼出来的？

### 练习 2：故意让校验器报错，再读它的自述（约 15 分钟）

写一条不带场景的需求，跑 `openspec validate <change>`，把报错里的三行 Next steps 逐条试一遍：按它给的标题重命名、补一个 `#### Scenario:`、再跑 `openspec show <change> --json --deltas-only` 看解析器眼中的 delta 到底是几条。

这个练习的价值在于让你相信「它报错时会给你能抄的修法」这条判断。

### 练习 3：数一遍你项目里的适配面（约 20 分钟）

`openspec init --tools claude,cursor,amazon-q,devin`，然后把四家的入口文件各打开一份对比头部：

```bash
head -6 .claude/commands/opsx/propose.md .cursor/commands/opsx-propose.md \
        .amazonq/prompts/opsx-propose.md .devin/workflows/opsx-propose.md
```

记录四件事：Claude 靠什么把命令命名空间隔开（看目录，不看文件名）；Cursor 的 `name` 字段为什么带前导斜杠；Amazon Q 那份为什么没有 `name` 只有 `description`；Devin 为什么把文件放进 `workflows/` 而不是 `commands/`。前两问的线索就在 frontmatter 里。后两问要回到 `docs/supported-tools.md` 的 How To Invoke 一节才答得上来——这恰好说明「文件名怎么起」是各工具自己的事，不是 OpenSpec 能统一的。

### 练习 4：把遥测关掉并证明它关了（约 10 分钟）

先 `openspec config list` 看当前状态，再依次试三种方式：`export OPENSPEC_TELEMETRY=0`、`export DO_NOT_TRACK=1`、`openspec config set telemetry.enabled false`。然后用 `openspec config get telemetry.enabled` 读回配置，用 `openspec config path` 看这份配置落在磁盘哪里。

有一处会让人误判：环境变量那条路**不会**出现在 `config get` 的输出里，它是读取时的硬覆盖而不是被写进文件；而 `telemetry.enabled` 从未显式设置过时，`config get` 也没有值可返回。所以「配置里没写关闭」和「实际没在上报」完全可以同时成立。想验证后者，只能看网络侧，或者信任「源码定位」里列出的那个遥测模块中的优先级判断。

## 下一步读哪里

按你的问题选入口，不必按顺序读完文档：

- **只想确认「该在哪敲命令」**：`docs/how-commands-work.md`，全文就在回答这一件事。
- **要给存量系统（brownfield）落地**：`docs/existing-projects.md`，再配 `docs/overview.md` 里那句「描述差异而不是目的地」。
- **要把 openspec 接进脚本或平台**：`docs/agent-contract.md`，然后 `docs/cli.md`；先从 `openspec list --json` 的 `root` 块读起，这是判断「我在替哪个仓库工作」最直接的入口。
- **要跨仓库共享规划**：`docs/stores-beta/user-guide.md`，它开头就把 beta 意味着什么写清楚了——命令名、参数、文件格式与 JSON 输出在版本之间都还会变形状。
- **想看真实的大规模用法**：这个仓库自己的 `openspec/specs/` 与 `openspec/changes/`，README 直接把它当示例目录挂着。

## 常见问题

**Q1：所有改动都得写 proposal + specs + design + tasks 吗？**

不必。依赖关系在 `openspec status` 里表现为「blocked by」提示，不是拒绝写入；归档遇到未完成任务在 `-y` 下只是警告。它确实不打算设门禁，所以真正需要约定的是「哪些改动必须走 change」这件事本身，团队里最好写成一句能判的话。

**Q2：`/opsx:update` 和 `openspec update` 是同一件事吗？**

不是。前者（`update` 工作流）改的是**一个 change 内部的计划产物**，让 proposal、specs、design、tasks 在你调整方案后重新自洽；它自己生成的命令文件里那句描述就是这意思：`revise existing planning artifacts and keep them coherent (Experimental)`。后者改的是**生成的 skill 与命令文件**，让它们跟已安装的 CLI 对齐。名字撞车是这一版里最容易踩的歧义。

**Q3：不用 spec 直接让 AI 写代码会怎样？**

README 的原话是「AI coding without specs means vague prompts and unpredictable results」：当次提示词含糊、结果不可预期。长期看，正文「vs 不写 spec」一段点过名——失去的是六个月后能复核的现场。所以更好的问法是「哪些改动值得走一遍 change」：一行文案级修复、还没有行为的玩具项目、不打算遵守归档纪律的团队，都不必上这套流程，判定标准见「适用边界与采用顺序」。

**Q4：上下文会被这套文件吃掉多少？**

`docs/` 里没有给出会占多少词元的数字，我也没测——要准确回答得在你自己的工具里逐条量。README 只给了一条建议：实现前清上下文、保持会话里的上下文卫生。能说的是 OpenSpec 自己不往每次请求里塞东西，产物文件由助手按需读；至于哪些内容会被常驻（例如 skill 的描述行），那是各工具的行为，不在本文核对范围内。

**Q5：它支持我的工具吗？**

看 `docs/supported-tools.md` 那张 40 行的表。不在表里的助手，选兜底目标 `agents`，OpenSpec 会把 skill 写进共享的 `.agents/skills/`，由你的工具按自己的 skill 机制发现；这一条能不能生效取决于你的助手读不读那个目录，属于要自己验的事。

**Q6：怎么确认本地这份 CLI 能支撑上面的结论？**

跑三条就够：`openspec --version`（应为 1.13.x）、`openspec config list`（看 profile 与 delivery 与 workflows 那行）、`openspec init --help`（看 `--tools` 后面列出的目标数）。版本更低时，工具数、Codex 与 Kimi 的路径、`update` 工作流是否属于 core，都可能是旧答案。
