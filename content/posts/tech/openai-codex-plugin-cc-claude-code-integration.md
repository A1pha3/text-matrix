---
title: "openai/codex-plugin-cc 拆解：8 个 slash command、一条 app-server 桥，与一个能拦住 Claude 的 review gate"
date: 2026-07-17T02:57:12+08:00
lastmod: 2026-09-20T00:00:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["OpenAI Codex", "Claude Code", "Plugin", "Code Review", "AI Agent", "Codex app server", "Anthropic"]
description: "codex-plugin-cc 把本机的 Codex 接进 Claude Code，v1.0.6 有 8 个 slash command。按源码核读拆开三件事：只读的 review 如何在 inline-diff 与自取证据之间切换、rescue 为什么会带上 workspace-write 写权限、/codex:transfer 的方向其实是 Claude Code 交给 Codex。再加上后台任务状态机与 Stop 钩子里那道会拦停 Claude 的 review gate。"
slug: "openai-codex-plugin-cc-claude-code-integration"
github_repo: "openai/codex-plugin-cc"
source_key: "gh:openai/codex-plugin-cc"
author: text-matrix
---

## 1. 判断：它换的是调度权，不是模型

[openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc) 让 Claude Code 的会话里能喊 Codex 干活，用的还是本机那份 `codex` 和它的登录态、配置。装完之后，Claude 仍在主线程跟你说话，重活交给另一个模型跑，结果原样贴回来。

值得读它的原因不在"多了个模型"。这套东西真正的设计取舍来自三处：**review 保持只读、耗时的活一律异步、Codex 凭证不经过 Claude 进程**。这三条决定了后面所有细节——为什么有 8 条命令而不是一条，为什么需要 broker，为什么 Stop 钩子里还藏了一道可以拦住 Claude 的检查。

下面按这三条线索拆开，再给一次完整流转和按症状的排查。

## 目录

- [1. 判断：它换的是调度权，不是模型](#1-判断它换的是调度权不是模型)
- [2. 仓库现状与核实口径](#2-仓库现状与核实口径)
- [3. 系统地图](#3-系统地图)
- [4. 三条主线，失效方式各不相同](#4-三条主线失效方式各不相同)
- [5. 八条命令的分工，以及谁能触发](#5-八条命令的分工以及谁能触发)
- [6. review 要决定两件事：审哪个目标、用什么证据](#6-review-要决定两件事审哪个目标用什么证据)
- [7. adversarial-review：把"先怀疑"写进提示词](#7-adversarial-review把先怀疑写进提示词)
- [8. 结果为什么能一字不改地返回](#8-结果为什么能一字不改地返回)
- [9. rescue：全流程唯一会写文件的那条路](#9-rescue全流程唯一会写文件的那条路)
- [10. transfer：手是从 Claude Code 递给 Codex](#10-transfer手是从-claude-code-递给-codex)
- [11. 后台任务的状态机与落盘位置](#11-后台任务的状态机与落盘位置)
- [12. review gate：在 Claude 停笔之前拦一道](#12-review-gate在-claude-停笔之前拦一道)
- [13. 一次任务如何流过整个系统](#13-一次任务如何流过整个系统)
- [14. 和另外两条路子的取舍](#14-和另外两条路子的取舍)
- [15. 按症状排查](#15-按症状排查)
- [16. 该不该装，以及按什么顺序上](#16-该不该装以及按什么顺序上)
- [17. 五个自测题](#17-五个自测题)
- [18. 下一步读哪份代码](#18-下一步读哪份代码)
- [19. 参考来源](#19-参考来源)

## 2. 仓库现状与核实口径

| 项 | 值（2026-09-20） |
|---|---|
| 版本 | 1.0.6（`package.json`、`plugins/codex/.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json` 三处一致） |
| 最新提交 | `db52e28`，2026-07-07，*Remove shell expansion for git commands (#447)* |
| 最近推送 | 2026-07-08（`pushed_at` 字段）——距今约 11 周没有新提交 |
| 创建时间 | 2026-03-30 |
| Stars / Forks / 未关闭议题 | 33,331 / 2,311 / 505 |
| 主语言 / 许可证 | JavaScript / Apache-2.0 |
| 运行时要求 | Node.js 18.18 以上，Codex 需已登录（ChatGPT 账号，含 Free，或 API（应用程序接口）密钥） |
| 脚本体量 | `plugins/codex/scripts/` 合计约 5.4k 行，其中 `codex-companion.mjs` 1,073 行、`lib/codex.mjs` 1,219 行 |

仓库已经过了最热的阶段：三个月里从 0 冲到 3.3 万星，然后停在 1.0.6。505 个未关闭议题说明使用量仍在，提交节奏说明短期内你要按这一版的语义来用。

本文的口径需要交代清楚：所有行为断言来自 README、`commands/*.md`、`prompts/*.md`、`agents/*.md`、`hooks/hooks.json` 与 `scripts/` 的源码对读，命令文本里的引文均逐字取自 v1.0.6。本机没有 Codex 登录态，也没有 Claude Code 会话，因此**未做实机端到端运行**——涉及"屏幕上会长什么样"的描述，来自提示词要求的渲染规则和脚本的输出逻辑，不当作实测结论。第 15 节的错误文本、第 11 节的阶段名同样按这个标准给出。

## 3. 系统地图

```text
Claude Code 会话
├─ /codex:review              只读审查，工作树或相对某个 base
├─ /codex:adversarial-review  同一条链路，换成对抗式提示 + 可选焦点文本
├─ /codex:rescue              经 subagent 派活，唯一带写权限的路径
├─ /codex:transfer            把当前 Claude 会话变成可续的 Codex 线程
├─ /codex:status / result / cancel   后台任务的看、取、停
└─ /codex:setup               就绪自检 + review gate 开关
      │
      │  每条命令 = plugins/codex/commands/<name>.md
      │  （提示正文 + allowed-tools + disable-model-invocation）
      ▼
codex-companion.mjs        8 个子命令，外加 task-resume-candidate
├─ review / adversarial-review
│    lib/git.mjs 选目标与取证 → 协议方法 review/start
├─ task（rescue 的转发目标）
│    thread/start + turn/start，--write 决定沙箱是否可写
├─ transfer
│    externalAgentConfig/import → 打印 codex resume <session-id>
└─ status / result / cancel
     读 state.json 与 jobs/，cancel 落到 turn/interrupt
      │
      │  lib/app-server.mjs：要么自己 spawn codex app-server，走 stdio
      │  收发 JSONL；要么连上 broker，复用长驻的那一条
      ▼
app-server-broker.mjs      unix socket（Windows 上是命名管道）
      │
      ▼
本机 Codex 登录态 + ~/.codex/config.toml
      （项目级 .codex/config.toml 只在仓库受信时叠加）

旁路：
  agents/codex-rescue.md            subagent，model: sonnet，只有 Bash 工具
  hooks/hooks.json                  SessionStart / SessionEnd（5s）、Stop（900s）
  skills/                           codex-cli-runtime、codex-result-handling、
                                    gpt-5-4-prompting
  schemas/review-output.schema.json 审查输出的 JSON 契约
  状态目录                           state.json、jobs/<id>.json、jobs/<id>.log、
                                    broker.json
```

主链路一句话：**命令把参数交给 companion 脚本，脚本对 `codex app-server` 说 JSONL 协议，Claude 的 `Bash` 负责那一跳是否真的 detach**。它不往 Claude Code 里塞 Codex 的凭证，也不自己实现一个 agent（智能体）循环。

## 4. 三条主线，失效方式各不相同

拆开看是三层，混着看会读不懂：

1. **提示层**：`commands/`、`prompts/`、`agents/` 三个目录，全是 Markdown。它规定每条命令能说什么话、能用哪些工具、结果怎么呈现。
2. **桥接层**：`codex-companion.mjs` 与 `lib/`，负责选审查目标、取 git 证据、发协议请求、渲染输出。
3. **状态与钩子层**：`state.json`、`jobs/`、`broker.json`，加两个可执行钩子（会话生命周期、Stop 时的 review gate）。

为什么要先分层：三层的失效方式不同。改提示层不动运行逻辑，但会改变 Claude 的行为；桥接层跟着 Codex 版本走，协议字段一改就断；状态层的目录位置取决于 Claude Code 注入的 `CLAUDE_PLUGIN_DATA`，变量缺失时行为会静默变化（第 11 节）。

## 5. 八条命令的分工，以及谁能触发

| 命令 | companion 子命令 | 声明的 allowed-tools | 模型可自行触发 |
|---|---|---|---|
| `/codex:review` | `review` | Read、Glob、Grep、`Bash(node:*)`、`Bash(git:*)`、AskUserQuestion | 否 |
| `/codex:adversarial-review` | `adversarial-review` | 同上 | 否 |
| `/codex:rescue` | `task`（经 subagent 转发） | `Bash(node:*)`、AskUserQuestion、Agent | **是** |
| `/codex:transfer` | `transfer` | `Bash(node:*)` | 否 |
| `/codex:status` | `status` | `Bash(node:*)` | 否 |
| `/codex:result` | `result` | `Bash(node:*)` | 否 |
| `/codex:cancel` | `cancel` | `Bash(node:*)` | 否 |
| `/codex:setup` | `setup` | `Bash(node:*)`、`Bash(npm:*)`、AskUserQuestion | **是** |

"模型可自行触发"这一列来自各命令 frontmatter 里的 `disable-model-invocation`。8 条里有 6 条写了 `true`——只有用户打出斜杠命令才会执行；`rescue` 和 `setup` 没有这一行。意图很直白：审查必须是人发起的，派活和自检状态可以让模型自己走。`codex-rescue` subagent 的描述也印证了这点——"*Proactively use when Claude Code is stuck, wants a second implementation or diagnosis pass*"。

也就是说，主线程的 Claude 判断自己卡住时，可以不经你点头把任务派给 Codex。这一条值得先知道，因为它决定了第 9 节的写权限为什么要认真对待。

`rescue` 另有一条被真实故障钉出来的坑位：`codex:codex-rescue` 是 subagent，不是 skill，走错入口会把会话挂住。它的来龙去脉放在第 9 节末尾。

## 6. review 要决定两件事：审哪个目标、用什么证据

`/codex:review` 的 frontmatter 参数提示是 `[--wait|--background] [--base <ref>] [--scope auto|working-tree|branch]`。第一层决策是审什么：工作树，还是当前分支相对某个 base。

分支模式先算 `git merge-base HEAD <base>`，再按 `<merge-base>..HEAD` 取差异，摘要文本长这样：`Reviewing branch feature/x against main from merge-base <sha>.`。默认分支探测不出来时，脚本会抛：

```text
Unable to detect the repository default branch. Pass --base <ref> or use --scope working-tree.
```

`--scope` 只接受 `auto`、`working-tree`、`branch`，写成 `staged` 会得到 `Unsupported review scope "staged". Use one of: auto, working-tree, branch, or pass --base <ref>.` 工作树审查则会同时看 `git diff --shortstat --cached`、`git diff --shortstat` 和 `git status --short --untracked-files=all`，未跟踪文件算可审内容——只看 `--shortstat` 为空就判定无货，是会漏的。

第二层决策更关键：**这份证据是塞进提示词，还是让 Codex 自己去取**。`lib/git.mjs` 的默认阈值是两个：

```text
DEFAULT_INLINE_DIFF_MAX_FILES = 2
DEFAULT_INLINE_DIFF_MAX_BYTES = 256 * 1024
```

文件数与 diff 字节数（`git diff --binary --no-ext-diff --submodule=diff` 的输出长度）都在线内，走 `inline-diff`；否则走 `self-collect`，此时附给 Codex 的只是一份摘要，提示词要求它："*Inspect the target diff yourself with read-only git commands before finalizing findings.*" 未跟踪内容另有 24 KiB 的上限（`MAX_UNTRACKED_BYTES`）。

这个分岔解释了一个常见困惑：为什么 12 个文件的改动，review 只给结论不给逐行引用。改动大时插件不做整包投喂，改为让对端自己去读——代价是慢，好处是大 diff 不会把上下文挤爆后给出泛泛之谈。

第三层决策才是给用户看的：审多大、要不要等。带 `--wait` 或 `--background` 时不问；两者都没写，命令要求 `AskUserQuestion` **恰好一次**，两个选项 `Wait for results` 与 `Run in background`，推荐项放第一个并在标签后加 `(Recommended)`。推荐规则很保守：只有明显是 1-2 个文件的小改动才推荐等，其余包括"大小看不清楚"都推荐后台。原文还有一句：

> When in doubt, run the review instead of declaring that there is nothing to review.

前台流程跑 `node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" review "$ARGUMENTS"`，要求把 stdout 原样返回，不解释、不追加评论。后台流程用 `Bash` 配 `run_in_background: true` 启动同一行命令，然后告诉用户："*Codex review started in the background. Check `/codex:status` for progress.*"

注意这里有一处容易被忽略的分工：命令文件自己写着，脚本会解析 `--wait` 和 `--background`，但真正把进程摘走的是 Claude Code 的 `run_in_background`。参数是给脚本看的，detach 是宿主做的。

`/codex:review` 只到这一步。它不接焦点文本，也不支持只审暂存区或只审未暂存，命令原文："`/codex:review` is native-review only. It does not support staged-only review, unstaged-only review, or extra focus text."

## 7. adversarial-review：把"先怀疑"写进提示词

`/codex:adversarial-review` 的目标选择、`--base`、`--wait`/`--background`、询问规则与 `review` 完全一致，多出来的只有 flag 之后那段焦点文本。差别全在 `prompts/adversarial-review.md` 这 90 来行提示词里。

开篇就是角色定义：

> You are Codex performing an adversarial software review.
> Your job is to break confidence in the change, not to validate it.

随后是三段可操作约束。**攻击面**列了七类：auth/权限/租户隔离与信任边界；数据丢失、损坏、重复与不可逆状态变更；回滚安全、重试、部分失败与幂等缺口；竞态、顺序假设、脏状态与重入；空值、超时与依赖降级；版本漂移、表结构漂移与迁移兼容；会把失败藏起来的观测缺口。

**立场**要求默认怀疑："*Do not give credit for good intent, partial fixes, or likely follow-up work*"，只走通正常路径的实现算真缺陷。**门槛**要求每条发现回答四问：能出什么事、这条路径为什么脆弱、影响面、什么改动能降低风险；样式和命名反馈明确排除。

约束最紧的是这两条：

> Every finding must be defensible from the provided repository context or tool outputs.
> Do not invent files, lines, code paths, incidents, attack chains, or runtime behavior you cannot support.

以及 `approve` 的用法被限定为"拿不出站得住的对抗性发现时才用"，`needs-attention` 则对应"有任何值得卡住不上线的实质风险"。校准段还要求宁可一条强发现，不要用几条弱发现稀释。

设计上的含义很清楚：这类 review 的失败模式是产出看起来合理但没有依据的担忧，提示词于是把"可追溯"和"少而重"写死。它仍然是只读的，命令文件里的原话是 "*This command is read-only. It does not fix code.*"

```bash
/codex:adversarial-review
/codex:adversarial-review --base main challenge whether this was the right caching and retry design
/codex:adversarial-review --background look for race conditions and question the chosen approach
```

## 8. 结果为什么能一字不改地返回

`schemas/review-output.schema.json` 规定了对端必须交回什么：`verdict`、`summary`、`findings`、`next_steps` 四项必填，`additionalProperties: false`。`verdict` 只有 `approve` 与 `needs-attention` 两个取值。每条 finding 又必填八项：`severity`（critical/high/medium/low）、`title`、`body`、`file`、`line_start`、`line_end`、`confidence`（0 到 1）、`recommendation`。

命令侧的配套要求是"搬运不改写"。`result.md` 让你把完整载荷原样呈现，并点名保留哪些东西：Job ID 与状态、verdict/summary/findings/artifacts/next steps、**文件路径与行号按报告原样**、错误消息与解析错误，以及 `/codex:status <id>` 和 `/codex:review` 这类后续命令。`status.md` 则要求把当前与历史运行压成一张 Markdown 表，保留 job ID、kind、status、phase、耗时、summary 与后续命令。

为什么要这么设计：两个模型串成一条链时，最容易出的问题不是第二个模型能力不够，而是它把第一个模型的结论改写、软化、补上自己的建议。契约把 Codex 的判断钉在文件与行号上，Claude 这一侧只剩呈现职责，`commands/review.md` 的三句 "Do not paraphrase, summarize, or add commentary" 就是为此。

代价也直接：你看到的内容里没有任何 Claude 的加工，格式、措辞、置信度的呈现都归 Codex。想让主线程解释结论，得自己再问一句。

## 9. rescue：全流程唯一会写文件的那条路

`/codex:rescue` 用 `Agent` 工具调 `codex:codex-rescue` subagent，把用户原始请求整段转过去。这个 subagent 的定义只有 40 行左右，`model: sonnet`、`tools: Bash`，并挂了 `codex-cli-runtime` 与 `gpt-5-4-prompting` 两个 skill。它的规则几乎全是"不许做"：

> Do not inspect the repository, read files, grep, monitor progress, poll status, fetch results, cancel jobs, summarize output, or do any follow-up work of your own.

一次 `Bash` 调用转发给 `codex-companion.mjs task ...`，stdout 原样返回。`gpt-5-4-prompting` 那个 skill 也只允许用来把用户请求收紧成一条更好的 Codex 提示，不许拿它先看代码。

写权限是这条路径的关键差异。桥接层的线程默认值是 `approvalPolicy: "never"`、`sandbox: "read-only"`，而 subagent 的规则是：

> Default to a write-capable Codex run by adding `--write` unless the user explicitly asks for read-only behavior or only wants review, diagnosis, or research without edits.

`--write` 在脚本里映射为 `sandbox: "workspace-write"`。所以 `/codex:rescue` 默认让 Codex 在工作区里改文件，且 `approvalPolicy` 是 `never`——中途不会回来问你。要只读排查，得在请求里说明；这也是它和两条 review 命令最本质的分工：review 只说，rescue 会动。

前后台的默认值在两处不一致，值得留意。`commands/rescue.md` 写的是"两个 flag 都没给时默认前台"；subagent 规则则按任务形态判断：小而明确的走前台，复杂、开放、多步、可能长跑的走后台。README 的建议偏向后者：

> Depending on the task and the model you choose these tasks might take a long time and it's generally recommended to force the task to be in the background or move the agent to the background.

线程续跑的判断走脚本。没写 `--resume`/`--fresh` 时，先问一次 `codex-companion.mjs task-resume-candidate --json`；报 `available: true` 才用 `AskUserQuestion` 问一次，两个选项 `Continue current Codex thread` 与 `Start a new Codex thread`；用户话说得像续做（"continue"、"apply the top fix"、"dig deeper"）就把继续一项放前面加 `(Recommended)`，否则把新建一项放前面。报 `available: false` 就不问，正常开跑。`--resume` 到了 subagent 一层翻译成 `--resume-last`。

```bash
/codex:rescue investigate why the tests started failing
/codex:rescue fix the failing test with the smallest safe patch
/codex:rescue --resume apply the top fix from the last run
/codex:rescue --model gpt-5.4-mini --effort medium investigate the flaky integration test
/codex:rescue --model spark fix the issue quickly
/codex:rescue --background investigate the regression
```

模型与推理档不由插件写死：不传就由 Codex 自己的配置决定；`--model spark` 会映射成 `gpt-5.3-codex-spark`；`--effort` 接受 `none|minimal|low|medium|high|xhigh`。`gpt-5.4-mini` 与 `spark` 是 README 给的示例名，不是一份受支持型号清单——能填什么取决于你本机 Codex 的版本与账号。

还有一条更省事的用法：直接说"让 Codex 把数据库连接改得更抗故障"，README 明确支持这样自然语言派活，不必打命令。

`Agent` 这个入口是被一次故障换来的，过程记在提交 `bb38412`（2026-04-18，修 #234）里。此前 `rescue.md` 的 frontmatter 带着 `context: fork`，也就是把命令体派生（fork）到一个 general-purpose subagent 里执行，正文只用一句"Route this request to the `codex:codex-rescue` subagent"点明目标、没点明载体。被派生出来的那个 subagent 手里没有 `Agent` 工具，于是它先试 `Skill(codex:codex-rescue)`（没有这个 skill），再退回 `Skill(codex:rescue)`，重入本命令，会话一直挂到你手动取消——按提交描述，一个 Codex 任务都没建出来。修复要两处配合才能生效：删掉 `context: fork`，让命令体在调用方上下文里内联跑，`Agent` 才在作用域内；同时把载体写死，并给 `allowed-tools` 补上 `Agent`，免得这次调用弹权限框。

这处历史还留下一条少见做法：**提示词本身被测试钉住**。`tests/commands.test.mjs` 用正则断言 `rescue.md` 里必须出现 `subagent_type: "codex:codex-rescue"`、必须出现那句 "do not call `Skill(codex:codex-rescue)`"，并且行首不允许再出现 `context: fork`。仓库 8 个测试文件合计约 3.0k 行，命令文本、渲染结果、状态迁移与 broker 端点都在覆盖范围内。命令文件是行为契约而不只是文档，这条约束方式比注释可靠。

## 10. transfer：手是从 Claude Code 递给 Codex

`/codex:transfer` 常被读反。README 的定义是："*Creates a persistent Codex thread from the current Claude Code session and prints a `codex resume <session-id>` command.*" 也就是把你和 Claude 正在跑的这段上下文打包给 Codex，让你换到 Codex 的 TUI 或 App 里接着干；反向的接续不靠它。

```bash
/codex:transfer
/codex:transfer --source ~/.claude/projects/-Users-me-repo/<session-id>.jsonl
```

正常情况下不用给 `--source`：钩子声明里的 `SessionStart` 已经把当前 transcript 路径带进来了，`session-lifecycle-hook.mjs` 负责记录，`--source` 只是手动覆盖。走的是 Codex 的外部 agent 会话导入器（协议方法 `externalAgentConfig/import`），与在 Codex App 里导入 Claude 历史同一套转换规则，会产生可见的 turn，之后能在 App 或 TUI 里续。

边界有三条：源文件必须在 `~/.claude/projects` 之下；太旧的 Codex 版本没有 session import，要先升级；命令声明 `disable-model-invocation: true`，它不会自己发生。

## 11. 后台任务的状态机与落盘位置

`status`、`result`、`cancel` 三个子命令读的是同一份本地状态。`status` 的参数在命令侧是 `[job-id] [--wait] [--timeout-ms <ms>] [--all]`，脚本侧还接受 `--json`；后台轮询间隔 2 秒（`DEFAULT_STATUS_POLL_INTERVAL_MS = 2000`）。

阶段与状态的取值在源码里可以数出来。`phase` 有 `queued`、`starting`、`investigating`、`reviewing`、`editing`、`finalizing`、`failed`、`cancelled`；`status` 有 `queued`、`running`、`completed`、`failed`、`cancelled`。一次 review 的正常轨迹是 `investigating → reviewing → finalizing → completed`，rescue 里出现 `editing` 就说明那边真的在改文件。`/codex:cancel` 落到 `turn/interrupt` 协议调用。

落盘位置由 `lib/state.mjs` 决定：

```text
$CLAUDE_PLUGIN_DATA/state/<repo-slug>-<hash>/
  state.json        任务列表（jobs 数组，会被裁剪）
  jobs/<job-id>.json   单个任务的载荷
  jobs/<job-id>.log    单个任务的输出日志
  broker.json       broker 端点与 pid/log 位置
```

`CLAUDE_PLUGIN_DATA` 没注入时退回 `<tmpdir>/codex-companion/` 下的同名子目录；broker 的 pid 与日志还能用 `CODEX_COMPANION_APP_SERVER_PID_FILE`、`CODEX_COMPANION_APP_SERVER_LOG_FILE` 两个环境变量单独指定。状态目录按仓库路径分开，所以同时开两个仓库不会串任务表。

broker 这一层解决了重复启动的开销。`lib/app-server.mjs` 会直接 `spawn("codex", ["app-server"])` 用 stdio 收发 JSONL，但常态是 `ensureBrokerSession(cwd)` 先探活：有可用端点就通过 unix socket（Unix 域套接字，Windows 上是命名管道）连上去复用，探活等待默认 2s；没有才拉起 broker 子进程。端点不通时的报错文本能帮你定位：`codex app-server exited unexpectedly (...)`、`Failed to parse codex app-server JSONL: ...`、`codex app-server client is closed.`

还有一处小但值得学的实现约束：所有 git 调用都以 `shell: false` 执行，仓库派生的参数不过 shell。v1.0.6 的最后一次提交（#447）做的就是这件事，源码注释写得很直接："Git is directly executable on Windows. Repository-derived arguments must never pass through a shell."

## 12. review gate：在 Claude 停笔之前拦一道

`/codex:setup` 除了自检，还管一个开关：

```bash
/codex:setup --enable-review-gate
/codex:setup --disable-review-gate
```

开启后生效的是 `hooks/hooks.json` 里注册的 `Stop` 钩子，指向 `stop-review-gate-hook.mjs`，超时 **900 秒**。它的动作是再起一次 Codex 任务，标记文本固定为 `Run a stop-gate review of the previous Claude turn.`，提示词把审查对象收到极窄：只看上一轮，且只看那一轮真正做出的直接编辑；纯状态输出不算可审工作——连 `/codex:setup`、`/codex:status` 的输出都点名排除；如果上一轮只是状态、总结、登录自检或评审结果，立刻 `ALLOW` 并且不再往下查。

回答格式硬约束在首行：

```text
ALLOW: <short reason>
BLOCK: <short reason>
```

`BLOCK` 会让 Claude 停下来先把问题处理掉。判定还要求"别把上一轮的回复当成证据"：是否真的改了代码，得从仓库状态自己验证，也不许拿更早轮次的编辑来卡这一次的停笔。

失败路径都留了文案，第 15 节会按症状列出来。README 的警告值得单独抄一遍：

> The review gate can create a long-running Claude/Codex loop and may drain usage limits quickly. Only enable it when you plan to actively monitor the session.

它的定位也要摆正：这道闸是"再问一遍 Codex"，不是 linter，也不跑测试。拦得准不准，取决于那一次 review 能看到的上下文与模型状态，且每拦一次就多烧一轮。

## 13. 一次任务如何流过整个系统

把三层串起来。场景：`feature/retry-budget` 分支上改了缓存与重试策略，12 个文件，Claude 已经把改动写完。

1. 你打 `/codex:review --background`。提示层不问了（有 `--background`），直接 `Bash` + `run_in_background: true` 启动 `codex-companion.mjs review`。脚本判范围：工作树非空，`--scope` 未给即 `auto`。文件数 12 > 2，`inputMode` 落到 `self-collect`，附一句"用只读 git 命令自己把目标 diff 看一遍"。
2. 协议层 `review/start`，通过 broker 复用已经在跑的 app-server；状态表里先 `queued`，随后 `investigating` → `reviewing` → `finalizing` → `completed`。这期间 Claude 主线程正常跟你说话。
3. `/codex:status` 出一张表，含 job ID（形如 `task-abc123`）、kind、status、phase、耗时与后续命令；`/codex:status task-abc123` 看单条全量输出。`/codex:result task-abc123` 把载荷原样贴回：`verdict: needs-attention`，两条 finding 带文件、行区间、confidence 与 recommendation。
4. 你对"这个重试预算设计得对不对"更感兴趣，于是 `/codex:adversarial-review --base main challenge whether this was the right caching and retry design`。目标选择换成 `merge-base..HEAD`，机制与上一步同一条，提示词换成对抗版。
5. 结论里有真问题，你要它改：`/codex:rescue --background apply the top fix from the last run`。命令先跑 `task-resume-candidate --json`，说这边有可续线程；你说"apply the top fix"，所以 `Continue current Codex thread (Recommended)` 排在第一。选定后带 `--resume` 转给 subagent，subagent 翻成 `--resume-last` 并默认补 `--write`——Codex 在 `workspace-write` 沙箱里动手。
6. 你想回 Codex 那边看它跑的全过程：`/codex:result` 里的 session ID 直接 `codex resume <session-id>`。若这段调试本来就在 Claude 里进行、要整段搬去 Codex，用 `/codex:transfer`。
7. 如果开了 review gate：Claude 报"改完了"要停笔时，Stop 钩子起一次窄范围评审，发现重试上限仍旧写死，回 `BLOCK: ...`，于是它继续修；这一步最长 15 分钟。

## 14. 和另外两条路子的取舍

同样是"在 Claude Code 里用上 Codex"，三条路的差别在谁承担调度与状态。

| 维度 | 本插件 | 自己包一层 MCP | 直接开第二个终端 |
|---|---|---|---|
| 触发 | 8 个 slash command | 自己定义工具与提示 | 手敲 `codex` |
| 谁把任务摘走 | Claude Code 的 `run_in_background` | 你的 server 自己管进程 | 终端本身 |
| 任务状态 | `state.json` + `jobs/`，按仓库隔离 | 自己实现 | 无，关掉即散 |
| 结果呈现 | 原样返回 + 固定 JSON 结构约束 | 取决于你 | Codex 自带界面 |
| 写权限边界 | `review` 只读；`task` 默认只读、`--write` 才写 | 自己决定 | Codex 自己的配置 |
| 停笔前拦截 | Stop 钩子可选开启 | 需要宿主支持等价钩子 | 无 |
| 会话搬运 | `externalAgentConfig/import`，Claude → Codex | 自己实现 | 手工复述上下文 |
| 凭证与配置 | 复用本机 Codex 登录态与 `config.toml` | 通常要自己拿 key | 原生 |
| 登录 | ChatGPT 账号（含 Free）或 API（应用程序接口）密钥 | 取决于实现 | 同 |

值得装的理由集中在三件不好自己攒的事：**按仓库隔离的后台任务状态机**、**Stop 钩子这道可选的停笔闸**、**与 Codex 会话导入器对齐的 transfer**。只要这三件里有一件是你真实工作流的一部分，自己包 MCP 的工时就不会白省。反过来，如果你只想偶尔跑一次 review，另开一个终端跑 `codex` 更省——少一个进程、少一层协议、也不会给主线程的 Claude 留下可以自行派活的 `rescue`。

## 15. 按症状排查

下面的次序按出现频率排：先是就绪与登录，再是范围与阈值，最后才是 broker 与那道闸。

| 现象 | 先看哪里 |
|---|---|
| `/codex:setup` 说 Codex 未就绪 | 未安装：`setup` 会问一次是否 `Install Codex (Recommended)`，随后跑 `npm install -g @openai/codex` 再自检；未登录：按提示执行 `!codex login`（ChatGPT 或 API key 都可）；Node 低于 18.18 时装不上 |
| 打 `/codex:` 没有补全 | 三步都要做：`/plugin marketplace add openai/codex-plugin-cc` → `/plugin install codex@openai-codex` → `/reload-plugins`；`/agents` 里应能看到 `codex:codex-rescue` |
| 分支审查报 `Unable to detect the repository default branch...` | 显式给 `--base <ref>`，或 `--scope working-tree` |
| 报 `Unsupported review scope "..."` | 只有 `auto`、`working-tree`、`branch` 三个值 |
| 大改动 review 不给逐行依据 | 落进了 `self-collect`（超过 2 个文件或 256 KiB 就不内联 diff），等它自己读；小改动改回 `--scope working-tree` 只审当前 |
| 改动很小却被推荐后台跑 | 正常：只有明确 1-2 个文件才推荐等待，看不准一律推荐后台 |
| Codex 动了你没打算让它动的文件 | `rescue` 默认带 `--write`（`workspace-write`），且 `approvalPolicy` 为 `never`；只要诊断就在请求里写清只读 |
| rescue 每次都问要不要续线程 | 该仓库有可续线程；直接加 `--fresh` 或 `--resume` 就不再问 |
| 想指定便宜模型没生效 | 不传 `--model` 时由 Codex 配置决定；`spark` 映射为 `gpt-5.3-codex-spark`；`--effort` 六档，拼错会被拒 |
| `/codex:status` 表是空的 | 状态按仓库目录隔离，先确认 Claude 会话的工作目录；后台任务是否已进 `failed`/`cancelled` |
| 任务卡住或找不到日志 | 状态目录在 `$CLAUDE_PLUGIN_DATA/state/...`，变量缺失时落 `<tmpdir>/codex-companion/...`；单任务日志是 `jobs/<id>.log`，broker 另有 `broker.json` 与 pid/log |
| 报 `codex app-server exited unexpectedly` 或 JSONL 解析失败 | 桥接层跟着 Codex 版本走，先升级全局 `@openai/codex`；仍异常看 broker 的日志文件 |
| 停笔被反复拦、额度掉得快 | 关掉闸：`/codex:setup --disable-review-gate`；`The stop-time Codex review task timed out after 15 minutes.` 之后要手动跑 `/codex:review --wait` |
| 闸没生效 | 输出里会写 `Codex is not set up for the review gate. ... Run /codex:setup.` |
| 想让插件走自建网关 | 沿用本机 Codex 配置：`openai_base_url`；默认值写在 `~/.codex/config.toml`，项目级 `.codex/config.toml` 只在仓库受信时叠加 |

## 16. 该不该装，以及按什么顺序上

**适合现在装**：

- 想让 review 变成异步、可查、可取消的流程，而不是把对话占住十分钟。
- 团队要求改动上线前有独立一次审查记录，且要能落到文件行号。
- 主线程 Claude 卡住时，愿意把一段调试整体交给另一个模型继续，同时保留 `codex resume` 可回查。
- 已经在用 Codex CLI（命令行工具），想复用登录态与配置而不多带一套凭证。
- 想用便宜型号跑第一轮粗筛，再回到 Claude 修。

**先别装**：

- 没有 Codex 账号也不想配 API key，`/codex:setup` 会停在登录。
- 不接受主线程模型有自行派活的路径：`rescue` 与 `setup` 没有 `disable-model-invocation`，而 `rescue` 默认带写权限。真有这条约束，就把 review 的用法限制到只读那两条。
- 只想跑一次 review，多开一个终端零成本。
- 想让 Codex 长期盯着 Claude 的每轮改动：review gate 的形态是每次停笔前再起一次 15 分钟上限的评审，成本和噪声都不小。

**采用顺序**（按前面踩后面的代价排）：

1. 装 marketplace 与插件，跑 `/codex:setup`，确认已登录、`/agents` 里能看到 `codex:codex-rescue`。
2. 只开 `/codex:review`，用 `--wait` 跑一次小改动，熟悉结果里 `verdict` / `findings` / `confidence` 的表达密度。
3. 换成 `--background` 跑一次目录级改动，习惯 `status` 表与 `result` 的分工。
4. 加 `--base main`，再试 `adversarial-review` 的焦点文本，看它是否比你手写的提示更狠。
5. 确认 `rescue` 的写边界之后再用它派活；第一次建议显式说明只读。
6. review gate 最后开，且只在盯得住的会话里开；随时准备 `--disable-review-gate`。

## 17. 五个自测题

1. 一次 40 个文件的改动跑 `/codex:review --wait`，它为什么可能不引用具体行？答的方向是阈值和 `inputMode`。
2. `/codex:transfer` 把上下文从哪儿搬到哪儿，源文件有什么限制？
3. 哪两条命令不要求用户显式触发，其中哪一条会带来工作区写入？
4. `phase` 出现 `editing` 意味着什么，`reviewing` 呢？
5. 开启 review gate 之后，一次纯汇报的回合会被拦住吗？为什么？

## 18. 下一步读哪份代码

- 想确认审查约束的原文：`plugins/codex/commands/review.md` 的 "Core constraint" 与 "Argument handling" 两段。
- 想知道对抗式审查怎么被措辞推动：`plugins/codex/prompts/adversarial-review.md`。
- 想接手后台任务与协议：`plugins/codex/scripts/lib/codex.mjs`（1,219 行，评审驱动与协议调用）与 `lib/app-server.mjs`（354 行，spawn 与 broker 两条路）。
- 想改结果呈现：`lib/render.mjs`（465 行）。
- 想理解状态目录：`lib/state.mjs` 与 `lib/broker-lifecycle.mjs`。
- 想加写权限护栏：`agents/codex-rescue.md` 的 "Operating rules" 一节。

## 19. 参考来源

- 仓库与 README：<https://github.com/openai/codex-plugin-cc>
- 命令定义：[`review.md`](https://github.com/openai/codex-plugin-cc/blob/main/plugins/codex/commands/review.md)、[`adversarial-review.md`](https://github.com/openai/codex-plugin-cc/blob/main/plugins/codex/commands/adversarial-review.md)、[`rescue.md`](https://github.com/openai/codex-plugin-cc/blob/main/plugins/codex/commands/rescue.md)、[`transfer.md`](https://github.com/openai/codex-plugin-cc/blob/main/plugins/codex/commands/transfer.md)、[`setup.md`](https://github.com/openai/codex-plugin-cc/blob/main/plugins/codex/commands/setup.md)
- subagent：[`agents/codex-rescue.md`](https://github.com/openai/codex-plugin-cc/blob/main/plugins/codex/agents/codex-rescue.md)
- 提示词模板：[`prompts/adversarial-review.md`](https://github.com/openai/codex-plugin-cc/blob/main/plugins/codex/prompts/adversarial-review.md)、[`prompts/stop-review-gate.md`](https://github.com/openai/codex-plugin-cc/blob/main/plugins/codex/prompts/stop-review-gate.md)
- 桥接与取证：[`scripts/codex-companion.mjs`](https://github.com/openai/codex-plugin-cc/blob/main/plugins/codex/scripts/codex-companion.mjs)、[`lib/app-server.mjs`](https://github.com/openai/codex-plugin-cc/blob/main/plugins/codex/scripts/lib/app-server.mjs)、[`lib/git.mjs`](https://github.com/openai/codex-plugin-cc/blob/main/plugins/codex/scripts/lib/git.mjs)、[`stop-review-gate-hook.mjs`](https://github.com/openai/codex-plugin-cc/blob/main/plugins/codex/scripts/stop-review-gate-hook.mjs)
- 输出契约：[`schemas/review-output.schema.json`](https://github.com/openai/codex-plugin-cc/blob/main/plugins/codex/schemas/review-output.schema.json)、marketplace 元数据 [`/.claude-plugin/marketplace.json`](https://github.com/openai/codex-plugin-cc/blob/main/.claude-plugin/marketplace.json)
- 提示词的回归测试：[`tests/commands.test.mjs`](https://github.com/openai/codex-plugin-cc/blob/main/tests/commands.test.mjs)
- 两次修复各自的提交：[#447](https://github.com/openai/codex-plugin-cc/pull/447)（去掉 git 命令的 shell 展开）、[#234](https://github.com/openai/codex-plugin-cc/issues/234)（`rescue` 的 Skill 递归，修复合入 `bb38412`）
- Codex 侧文档：[app server](https://developers.openai.com/codex/app-server)、[pricing](https://developers.openai.com/codex/pricing)、[config-basic](https://developers.openai.com/codex/config-basic)、[config-advanced](https://developers.openai.com/codex/config-advanced#project-config-files-codexconfigtoml)、[`codex login` 参考](https://developers.openai.com/codex/cli/reference/#codex-login)

核查用的数据快照：GitHub API 于 2026-09-20 取到的 stars 33,331、forks 2,311、未关闭议题 505，以及 v1.0.6（提交 `db52e28`）源码。模型名、阶段枚举与阈值会随版本变化，重读时以上面这几处的当前内容为准。
