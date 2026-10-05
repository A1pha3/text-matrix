---
title: "Pi Subagents：把子代理委托做成控制层的 Pi 扩展"
date: "2026-05-31T20:07:02+08:00"
lastmod: "2026-10-03T00:00:00+08:00"
slug: "pi-subagents-async-subagent-delegation-framework-guide"
github_repo: "nicobailon/pi-subagents"
source_key: "gh:nicobailon/pi-subagents"
description: "pi-subagents 是 Pi 编码代理的子代理委托扩展：一个父会话雇佣多个专注子代理，任务有合同、完成要证据、越界有守卫。内置 7 个角色，还能把 Claude Code、Codex、Cursor 作为子代理纳入，配 FleetView 观测、mission 存档与可选 watchdog 审查。本文按 v0.75.0 拆解其机制与采用路径。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "工作流编排", "Pi", "开源"]
---

# Pi Subagents：把子代理委托做成控制层的 Pi 扩展

修一个功能时想让人同时做代码审查、技术调研和另一个模块的实现，常规做法是开几个终端窗口，手动复制上下文，再祈祷没人改错文件。pi-subagents 给 [Pi 编码代理](https://github.com/earendil-works/pi)（原 badlogic/pi-mono，已迁至 earendil-works，主仓 11.2 万星）加了一层委托机制：父会话把任务交给专注的子会话去做，结果带回主对话，子代理跑在受监督的轨道上——有启动合同、有递归守卫、有可检查的运行痕迹。

它值得看的理由不在"多代理"这个字眼，而在项目对"信任"的处置方式。VISION.md 里有一句立意声明："A child saying it is done is not enough"——子代理说自己做完了不算数，完成必须有证据：具体产出、变更文件、验证结果，或者一个明确的阻塞状态。证明不了的行为按失败处理，而不是报告乐观的成功。这个原则贯穿了它的角色设计、外部代理接入，甚至配置校验：给已删除的配置键赋值，加载时直接报错，不做静默兼容。

**版本提示**：本文初版发表于 2026 年 5 月 31 日（v0.26.0 时代），本次更新锚定 v0.75.0（2026-10-02）。四个月里发了 63 个版本，有三处变化会直接影响老读者：内置角色从 8 个变为 7 个（`planner`、`context-builder` 被移除，新增 `evidence-auditor`）；实现循环的推荐路线从 planner 换成了 scout；配置键 `fallbackModels` 已删除，照旧配置会导致加载报错。文中机制均按 v0.75.0 核对。

## 项目概览

| 指标 | 数值 |
|------|------|
| 仓库 | [nicobailon/pi-subagents](https://github.com/nicobailon/pi-subagents)（Nico Bailon） |
| Stars / Forks | 3,824 / 773（2026-10-03，GitHub API 读数；文章发表当天快照为 1,696★） |
| 版本 | v0.75.0（2026-10-02），npm 累计 142 个版本 |
| 语言 / 协议 | TypeScript / MIT |
| 前置要求 | Pi 编码代理本体；安装：`pi install npm:pi-subagents` |
| 可选配套 | pi-intercom（子代理回话通道）、pi-web-access（researcher 取网）、Herdr（远程机器） |

一个细节能说明维护强度：仓库创建于 2026 年 1 月 7 日，九个月发了 142 个 npm 版本，平均每周三四个，CHANGELOG 有 2,900 多行，每条修复大多带 issue 编号和贡献者致谢。

## 系统地图：委托层的六个部件

把 pi-subagents 拆开看，它是一组职责清晰的部件，而不是一团"多代理"概念：

| 部件 | 职责 | 入口 |
|------|------|------|
| `subagent` 工具 | 唯一委托入口，Pi 模型决定何时调用、派谁 | 自然语言或 `/run` 命令 |
| 角色体系 | 7 个内置 Pi 子代理 + 6 个外部 CLI 桥代理 | `agents/` 目录下的 Markdown 文件 |
| 前台/后台执行 | 前台在父进程内跑；后台在独立 runner 进程里跑 | `/run ... --bg` 或对话里说"后台跑" |
| 观测面 | FleetView 面板、运行工件、mission 存档 | `/subagents-fleet`、`~/.pi/agent/missions/` |
| 安全边界 | 递归守卫、上下文过滤、生成数上限 | 默认生效，配置可收紧 |
| 编排 | 提示词模板、workflowScript 脚本、council 辩论 | `/parallel-review`、`/council` 等 |

下面按这个顺序展开。每部分先说机制怎么运作，再说它为什么长这样。

## 安装即增强，不自动接管

安装只需一步，不需要建配置、定义代理模板或学命令格式。装完后用自然语言说话就行：

```text
Use reviewer to review this diff.
```

```text
Run parallel reviewers: one for correctness, one for tests, and one for unnecessary complexity.
```

README 把边界讲得很清楚：装扩展不会自动启动后台审查者。"Complexity alone does not authorize delegation"——任务描述得再复杂，也不会自动触发委托；只有你的请求或项目指令明确授权，Pi 才会调工具。想让每次实现都被审查，就把规则写进 prompt 或项目指令：

```text
When you finish implementing, run a reviewer subagent before summarizing.
```

工具的呈现方式也经过计算。在支持的模型上，新会话先暴露一个很小的 `subagents_enable` 加载器，等你真正提到委托时才展开完整的 `subagent` 工具表——因为在一个固定工具列表的对话里中途加工具，会让供应商的 prompt 缓存失效，重发整个上下文。这个行为由 `toolActivation` 配置控制：默认 `auto` 按模型能力决定，`dynamic` 总是先加载器，`eager` 从第一轮就给全量工具。恢复会话时会记住当时的选择，激活过的会话不会退回冷状态。

## 角色体系：7 个内置角色与 6 个外部 CLI 桥

角色即文件：每个代理是 `agents/` 目录下一个带 YAML frontmatter 的 Markdown 文件，frontmatter 声明名字、描述和工具清单，正文就是系统提示词。发现优先级从低到高是内置、已装包、用户（`~/.pi/agent/agents/`）、项目（`.pi/agents/`）——同名即覆盖，想改内置角色不用 fork 任何东西。

v0.75.0 的 7 个内置角色：

| 角色 | 用途 |
|------|------|
| `scout` | 快速本地代码侦察：相关文件、入口、数据流、风险点，以及下一个人该从哪接手 |
| `researcher` | 带来源的文档/网络调研，产出简要研究纪要（子会话需装 pi-web-access） |
| `evidence-auditor` | 独立核查研究纪要里的重要论断是否真被来源支撑（v0.67.0 新增） |
| `worker` | 实现工作：改文件、跑验证、拿不准的决策上报而不是猜 |
| `reviewer` | 代码审查与小修：对照任务/计划、测试、边界情况和简洁性 |
| `oracle` | 行动前的第二意见：挑战假设、发现漂移，不改文件 |
| `delegate` | 轻量通用委托，行为接近父会话 |

官方给的口诀按决策链排：不理解代码先 `scout`，不信外部事实先 `researcher`，重要结论依赖前先 `evidence-auditor`，实现交给 `worker`，检查交给 `reviewer`，决策本身有风险时问 `oracle`。

**两个被删掉的角色值得记一笔。** 本文初版写作时内置 8 个角色，多出的两个是 `planner`（从现有上下文生成实现计划）和 `context-builder`（规划前收集代码上下文、写 handoff 材料）。2026 年 8 月 7 日的 v0.43.0 把它们连同配套的交接模板一起移除了——不是因为做得不好，而是项目把脚本编排（workflowScript）定为唯一公共执行面之后，"先收集上下文再出计划"这类固定管线可以直接写成脚本，角色反而多余。这份 CHANGELOG 是理解项目品味的入口：它不做静默兼容，旧路径删干净，测试同步更新。`advisor` 是 `oracle` 在 Claude Code 兼容命名下的同一个角色，功能完全一致。

**外部 CLI 桥是 0.56.0 之后的大变化。** Claude Code、Codex、Cursor Agent 三种命令行代理可以作为子代理被"雇佣"，各有只读和写工作区两个 profile（如 `codex-exec` 只读分析，`codex-exec-writer` 做工作区修改）。这些适配器的合同很紧：一次性会话、审批策略固定为 never、输出按不可信数据处理，只有收到合法的完成事件和有界的最终消息才算成功。VISION.md 对外部代理的态度是"earn trust"——声明真实能力、接受刻意的交接而不是假装拥有本地上下文、行为证明不了就失败关闭。父会话永远是 Pi；外部 CLI 只是带着自己的合同进场的工人。

## 前台与后台：两种执行形态

前台子会话是父 Pi 进程里创建的一个 session，进度流式打进对话，默认 30 分钟墙钟超时（可按调用或代理覆盖）。后台子会话跑在一个独立的 detached runner 进程里，控制权回到你之后继续工作；npm 安装的 Pi 用 Node runner，官方 Pi 0.86.1 Linux x64 独立二进制则通过内嵌 SDK 加载同一个 runner——这条边界在 docs/standalone-background.md 里有明确的支持范围声明，其他版本、系统和打包方式不属于完全验证目标。

后台并行运行时，每个子代理的进度在父会话里直接可见，逐代理分别汇报。这是初版文章提过的老卖点，如今有了更完整的观测面：

- **FleetView**：TUI 里编辑器下方的常驻面板，活跃工作不消失；`/subagents-fleet` 打开实时检查器，可以浏览子会话、读完整转录、转向（steer）运行中的子代理或直接停掉它。
- **运行工件**：后台运行镜像事件到 `events.jsonl` 和 `output-<index>.log`，事后可查。
- **mission 存档**：每次工作流启动默认创建一条持久 mission，存在 `~/.pi/agent/missions/projects/<project-hash>/` 下，关联目标、运行 ID、生命周期状态、决策、工件路径和交付凭据（receipt——比如一个 PR 或 CI 检查的链接）。项目文档给的概念表很清楚：项目是"在哪干活"，mission 是"为什么存在、之后怎么找回"，run 是"一次实际执行"，receipt 是"外部结果的证据"。

## 安全边界：委托不等于放权

子代理能拿到什么、能走多远，是这套系统设计得最认真的部分。四条边界全部在运行时强制：

1. 子会话不继承 `pi-subagents` skill（避免它学会再派子代理）。
2. forked 上下文会过滤父辈的子代理痕迹：旧的隐藏编排指令、slash/status/control 消息、父辈 `subagent` 工具调用历史都被清掉，普通对话和无关工具调用保留。
3. 默认子代理不注册 `subagent` 工具，并收到明确指令：你不是编排器，不得提议或运行子代理。
4. 例外只有一个——代理定义的 `tools` 里显式包含 `subagent`，这个子代理才拿到一个"子安全版"委托工具，用于父代理分派的扇出任务，且仍受深度限制。

深度限制默认两层：主会话 → 子代理 → 孙代理，更深的调用被拦截并引导直接完成任务。配置点有三个，从环境变量 `PI_SUBAGENT_MAX_DEPTH` 到 `config.maxSubagentDepth`，再到代理 frontmatter 里的 `maxSubagentDepth`（只能收紧，不能放宽）。另一侧还有总量阀：`maxSubagentSpawnsPerRun` 限制单棵运行树的累计子代理数，默认 64。

`bg_wait` 和 supervisor 应答不受工具激活机制影响，始终可用——被阻塞的子代理可以先向 supervisor 求助，而不是直接打断用户。权限模型遵循"清晰即权威"：用户意图和策略清楚时，安全的常规操作可以推断授权；两边任何一方的指令都可以收紧或放宽这个边界。

## Watchdog：第二个模型盯着第一个

watchdog 是可选的对抗性审查机制：一个独立模型复查主代理刚做了什么，把发现推回对话转录。它找的是遗漏的约束、正确性风险、测试缺口、不安全改动、循环风险和范围漂移；这一轮干净就什么都不说。文档特意强调一句："It is not the `reviewer` subagent"——它审查的是主会话和子会话的行为流，不是替你审代码 diff 的那个角色，配置也完全独立。

触发方式有三种，对应三类风险：

| 触发 | 时机 | 条件 |
|------|------|------|
| 边界审查 | 主或子代理每轮结束时 | 仓库发生了变更；一整轮的修改合并成一次终态审查 |
| 节奏审查 | 每隔 N 个工具结果（最小 5） | 显式开启 |
| LSP 预检 | 边界审查前 | 有 TypeScript/JavaScript 文件变更；诊断直接变成发现，不花模型调用 |

发现的分级决定去向：high 级别转向模型处理，low/medium 只持久化给用户看，不占用模型上下文。主会话和子会话都能配，子代理可以按角色覆盖节奏或干脆关掉（比如让 `reviewer` 不再被 watchdog 审）。这个机制的灵感来自开源项目 Scopey。

## 编排：从一句自然语言到一个脚本

编排有三级，按需取用：

**提示词模板**。五个打包好的常用形：`/parallel-review`（多角度审查后汇总）、`/review-loop`（worker/reviewer 循环到干净或封顶）、`/parallel-research`、`/gather-context-and-clarify`、`/parallel-cleanup`。`/parallel-review` 和 `/parallel-cleanup` 加 `autofix` 后缀，只应用汇总后有价值的修复。

**单次命令**。`/run <agent> [task] [--bg] [--fork]` 跑一个代理，模型可以在方括号里临时覆盖：

```text
/run reviewer[model=anthropic/claude-sonnet-4:high] "Review this diff"
```

**workflowScript**。v0.43.0 起唯一的公共执行面：普通 JavaScript 语句体，`await runs.all([...])` 做并行扇出，`runs.run` 做串行，`state.get/set` 做 mission 级持久状态，写完可以用 `{ action: "validate", workflow: true }` 静态校验而不真正启动。旧的 `/chain`、`/parallel`、`/run-chain` 命令已注销——这就是 planner/context-builder 退场的另一半原因。

另有一个不太一样的入口：`/council` 用多个模型顾问辩论一个重要决策，包装成 council-mode skill 和文档化的 `council-*` profile 示例，顾问由你在自己的代理目录里配置。

## 一次实现任务的完整流转

把机制串起来。假设你让 Pi 给支付模块加重试逻辑：

1. **澄清**。父会话先问清边界：哪些错误码重试、重试几次、要不要幂等键。这一步不上子代理。
2. **侦察**。`scout` 子会话带着任务出发，摸清支付模块的文件结构、现有错误处理和调用方，返回一份"从哪开始"的简报。
3. **实现**。`worker` 接手。注意现在的默认上下文是 fresh——它从分派的简报开工，而不是继承父会话没聊完的半截思路（v0.26.0 时代默认还是 forked，这个反转值得老读者注意）。它改文件、跑测试，遇到没被授权的决策就上报。
4. **审查**。三个 fresh `reviewer` 并行开工，一个盯正确性、一个盯测试、一个盯多余复杂度；每完成一个就通知父会话，不等齐。
5. **修复收口**。父会话汇总反馈，交给 `worker` 应用有价值的修复，复核后把结果带给你。

全程如果放在后台跑，FleetView 面板里能看到每个子会话的状态树；watchdog 开着的话，worker 每轮结束的 diff 都会被第二个模型过一遍；跑完之后 mission 里留着这次委托的完整档案——谁被雇佣、改了什么、谁验证的、证据在哪。

## 模型与配置：覆盖谁、怎么覆盖

内置角色默认继承父会话的默认模型，新装不依赖任何特定供应商。想给某个角色钉死模型，单次用 `/run` 方括号语法，持久覆盖写在 Pi 的设置文件里（用户级 `~/.pi/agent/settings.json`，项目级 `.pi/settings.json`）：

```json
{
  "subagents": {
    "agentOverrides": {
      "reviewer": {
        "model": "anthropic/claude-sonnet-4",
        "thinking": "high"
      }
    }
  }
}
```

同一个 `agentOverrides` 块能改的东西比名字暗示的多：`tools`、`skills`、继承上下文、提示词文本，或者 `disabled: true` 直接停用一个内置角色。完整的可覆盖字段清单在 docs/agents.md，共 19 个。

一个必须提醒的破坏性变化：本文初版的配置示例里有 `fallbackModels` 字段（供应商失败时按序切换备用模型），这个字段已随版本演进被删除，现在写进配置会让加载直接报错——源码里的报错信息是 "uses removed field 'fallbackModels'; configure one model instead."。按官方建议给角色配一个模型就好；模型解析的完整优先级是：单次覆盖 → 供应商级角色覆盖 → `agentOverrides` → 代理 frontmatter → `subagents.defaultModel` → 父会话模型。

pi-subagents 自己还有一层配置，在 `~/.pi/agent/extensions/subagent/config.json`，管超时、watchdog、调度这类运行参数，与设置文件分工明确。出问题先跑 `/subagents-doctor`，装好版本的用法问 `/subagents-guide`——后者支持 11 个主题，从 workflows 到 watchdog 各有一份内置指南。

## 适用边界

**适合**：

- 长时间用 Pi 做复杂软件任务，需要审查、侦察、调研多路并行，又不想开一堆终端窗口。
- 想要"第二意见"但不信任单个模型的自我审查——evidence-auditor 和 watchdog 都是为此设计的。
- 已有 Claude Code 或 Codex 订阅，想让它们在 Pi 的监督和观测体系里干活，而不是各跑各的。

**不适合**：

- 父会话必须是 Pi。不用 Pi 的用户装不了这套东西；Pi 生态概览可以看站内那篇 oh-my-pi 的[深度解读](/posts/oh-my-pi-coding-agent-deep-dive/)。
- 找企业级多代理平台的请绕行。VISION.md 写得直白：这个项目服务"一个 Pi 操作者"，单个人用一场会话撬动更多产出；它不做通用项目管理、不碰 CI 和发布策略，只向这些系统报告证据。
- 需要"后台默默替我审查每次改动"的默认行为——这违反项目原则，委托必须由你直接或通过指令发起。

## 结语

多角色协作的玩法到处都有，pi-subagents 的差别在于它把委托当成一个信任问题而不是并发问题：每个子代理有明确的合同，完成要交证据，嵌套有深度阀，外部 CLI 要先证明能力才被当回事，连配置键的死亡都是显式的。四个月 49 个版本的迭代里，这个品味没有松动过——它删掉自己两个月前还推荐的角色时，眼都不眨。

如果你已经重度使用 Pi，现在就值得装；如果你在观望 Pi 生态本身，先读上面那篇 oh-my-pi，再回头看这篇，理解会顺很多。
