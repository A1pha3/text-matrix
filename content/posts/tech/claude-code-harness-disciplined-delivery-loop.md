---
title: "Claude Code Harness：给 AI 编程助手加一套有约束的交付流程"
date: 2026-05-28T09:15:00+08:00
lastmod: 2026-10-04T00:00:00+08:00
slug: "claude-code-harness-disciplined-delivery-loop"
github_repo: "Chachamaru127/claude-code-harness"
source_key: "gh:Chachamaru127/claude-code-harness"
aliases:
  - "/posts/tech/chachamaru127-claude-code-harness-delivery-loop/"
description: "Claude Code Harness 把「让 AI 写代码」收束为「让 AI 按合同交付」：写 Spec→实施→验证→独立 Review→打包证据，Go 守护引擎在每次工具调用执行前裁决，五类运行时下限没有全局开关。本文基于 v5.15.0，覆盖审批前置、模型角色路由与多会话协作。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "AI 编程", "工作流", "Skill", "Go"]
---

# Claude Code Harness：给 AI 编程助手加一套有约束的交付流程

> **快速信息卡**
> - **GitHub**: [Chachamaru127/claude-code-harness](https://github.com/Chachamaru127/claude-code-harness)
> - **Stars**: 3,147 / **Forks**: 301（GitHub API 2026-10-04 验证）
> - **License**: MIT
> - **主语言**: Shell（守护引擎为 Go，预编译二进制分发）
> - **当前版本**: v5.15.0（2026-09-06）
> - **main 分支最近提交**: 2026-09-06

Claude Code 很能写。但任务一超过 3 个文件，就容易出现同一类问题：计划散落在几轮对话之前，测试在 deadline 前被跳过，Review 变成合并之后的事后安慰，PR 描述靠记忆拼凑。这不是某个模型的问题，而是任何没有外部约束的自主 Agent 都会有的倾向。

**Claude Code Harness**（下称 CCH）没想着让模型更聪明，它改的是 Agent 外面的流程和边界。核心是一条可重复的路径：**写 Spec → 只实施已批准的任务切片 → 验证 → 独立 Review → 打包证据**。它把"让 AI 写代码"这个开放命题，收束成"让 AI 按合同交付"。

## 两条主线：流程约束 + 安全边界

CCH 看起来是"一个插件"，实际是两层东西，强度刻意不同：

| 层 | 裁决什么 | 可配置性 |
|------|------|----------|
| **运行时下限（5 类）** | 计费、网络出口、读取密钥、生产部署、任务 worktree 之外的破坏性操作 | 没有全局关闭开关；只存在有限的例外清单（目的地、读取目标等） |
| **守护规则（R01-R16）** | 直推 main、写受保护路径、强制 push、改写历史等 | deny / confirm / warn 三态，部分可按项目配置 |

下限层的实现值得看一眼源码：`go/internal/runtimefloor` 的 `CheckCommand` 在结构上就不读取任何 disable 开关、环境变量或项目配置——想让它失效，只能改代码重新编译。命中后工具调用被拒绝，原因带上 `RUNTIME_FLOOR:<类别>` 前缀，Human 必须介入。但"没有全局开关"不等于"毫无例外"，五类各有精确的豁免口径：

- **money-billing**：无任何豁免。
- **网络出口（egress）**：`HARNESS_RUNTIME_FLOOR_EGRESS=off` 可以整类关闭——这是五类里唯一的环境变量开关。
- **secret-read**：`HARNESS_RUNTIME_FLOOR_SECRET_ALLOW` 环境变量或项目配置可按路径声明读取白名单；全开放不可、配置解析失败时全拒绝（fail-safe）、项目外绝对路径无效。
- **prod-deploy**：`runtimefloor.releaseAuto: true` 可选放开"发布最后一步"子集（`git push origin v*`、`gh release` 非破坏动词）；`gh release delete`、`npm publish`、`kubectl`、`terraform` 放开后照样拦。
- **worktree-escape**：OS 保证可清理的临时区（`/tmp`、`$TMPDIR`、`~/.cache` 等）放行；`~/Desktop`、`~/Documents`、`/etc` 这类真实数据路径必须人工判断。

守护规则是日常要调的那层。现行 16 条的完整清单：R01 禁 sudo、R02/R03 保护路径写入、R04 项目外写入需确认、R05 `rm -rf` 需确认、R06 禁强制 push、R07 Codex 模式禁写、R08 Reviewer 角色禁写、R09 密钥文件读取告警、R10 禁 git 绕过旗标、R11 保护分支禁 `reset --hard`、R12 保护分支直推需确认、R13 受保护评审路径告警、R14 源码写入需测试、R15 禁暂存密钥文件、R16 禁自我批准。

两层的分工逻辑：下限管"不允许 Agent 自己想通的事"，规则管"每个项目自己定的事"。每次工具调用在**执行前**就被 Go 引擎裁决，而不是事后看 diff——README 原话是：网络发送和删除必须做命令级检查，因为文件 diff 无法反映这类效果。

## 五个动词，把交付闭环钉死

CCH 的门面只有 5 个核心命令，对应交付闭环的每个阶段。README 徽章的完整口径是 "5 core / 23 total"——5 个动词之外还有 harness-loop、harness-progress 等 18 个辅助技能，但主流程就这五步。表面越小，越难绕路。

| 动词 | 做什么 | 关键门控 |
|------|--------|----------|
| `/harness-plan` | 把需求转成 `spec.md` + `Plans.md`（范围、验收标准、依赖、未知项、停止条件） | 合同要你批准或修正 |
| `/harness-work` | 实施已批准任务，按任务数自动选单干或组队 | 标了 TDD 的任务走红-绿循环 |
| `/harness-review` | 独立验证实施结果 | 实现者不能审自己；重大发现阻塞完成 |
| `/harness-sync` | 对比计划与实际实现，报告漂移 | 只报告，不打包 |
| `/harness-release` | 把已核实的证据打包进 CHANGELOG、tag 和 release | 发布 preflight 必须通过 |

`/harness-setup` 只在安装时跑一次。`/harness-work all` 跑完整计划，README 的建议是"先让单任务跑通、仓库基线清楚了"再用。

几个值得注意的细节：

- **审批前置到计划阶段**。计划确定时，CCH 会把这次工作里可能需要的敏感操作（读密钥、外发、破坏性操作）收集成"事前确认区"，随合同一次性问清楚，批准之后 `/harness-work` 可以跑完而不中断。计划里没声明的操作照旧拦截。每条审批绑定任务范围（phase + task）、带过期时间、限使用次数（默认 10 次）——一次批准不会变成永久漏洞。
- **每次拦截都被记录**。守护规则和下限的每次发火写进 `.claude/state/audit/guardrail-fires.jsonl`：规则 ID、类别、裁决、工具名。命令文本本身不落盘，只记 SHA256 哈希和长度；密钥读取和计费两类连哈希都不记。日志写入失败被刻意忽略——可观测性不允许反过来影响裁决。
- **未知项保持未知**。Agent 没见过但计划里需要的数据，停在 `unknown`，而不是被悄悄编出来。
- **完成标记带证据**。任务完成时 Plans.md 里写入 `cc:完了 [hash]` 这类带哈希的标记，状态对账靠观察到的证据，不靠 Agent 自述。

## Go 原生守护引擎

守护层是编译为单二进制的 Go 引擎，`go/internal/` 下按职责拆了几十个模块（guardrail、runtimefloor、policy、auditlog、hookhandler、plans、session、lifecycle 等）。README 明确：**Go 原生 guardrail 引擎不需要 Node.js**。hook 调用统一收敛成 `bin/harness hook <event>` 一种入口，`hooks.json` 里所有 PreToolUse 都指向同一个 shim。

shim 本身只有几十行 shell：按平台分发到预编译的 `harness-darwin-arm64` 等二进制。有一个行为必须如实说——**找不到对应平台的二进制时，shim 向 stderr 打一条诊断，然后以空 stdout 退出 0**。在 Claude Code 的 hook 协议里，这等于"没有裁决"，工具调用照常执行。也就是说守护层装坏了不会把仓库锁死，但也不会有保护；`bin/harness doctor` 就是用来发现这种状态的。

为什么值得用 Go 写这一层：守护引擎在每次工具调用时都被 hook 触发，要走 stdio 解析、规则匹配、返回裁决，路径必须够快，否则会拖慢 Agent 的每一次动作。这正是"热路径"该有的形态。

## 从 v4 到 v5：这篇文章发表后发生的事

本文初版发表于 2026-05-28，当时项目在 v4.12.11。四个多月后写下这些更新时，版本线已经走到 v5.15.0，中间隔了一次大版本重设计。把演进时间线摆出来，比孤立地描述现状更有用：

| 时点 | 版本 | 发生什么 |
|------|------|----------|
| 2026-05-28 | v4.12.11 | 本文发表时。守护规则 R01-R14，共 10 个 Go 内部模块，无下限层、无审计日志、审批在实施中途逐次进行 |
| 2026-06-12 | v4.16.0 | 五类运行时下限引入（Phase 92.2.1），`CheckCommand` 结构上不可配置禁用 |
| 2026-07-05 | v5.0.0 前 | R15 密钥文件暂存阻断进入规则集，随 v5.0.0 发布 |
| 2026-07-08 | v5.0.0 | "0 基线再设计"转正：skills 构成、hooks 配线、生成物 layout 全面刷新（Breaking）；审批前置到计划阶段；secret-read 白名单 |
| 2026-07-28 | v5.5 线 | 守护发火接入审计日志（guardrail-fires.jsonl）；计划时预审批接通 R12 确认抑制 |
| 2026-08-31 | v5.14 线 | R16 禁自我批准；deferred-ops 审批流（Phase 140.2） |
| 2026-09-06 | v5.15.0 | 模型角色路由刷新（Fable 5.1 / GPT-6 astra 一线） |

这个时间线里最值得注意的事实是：**审批前置、五类下限、审计日志这三个如今最容易被当作"招牌"的机制，全部是文章发表之后才落地的**。v4 时代的 CCH 靠的是 R01-R14 规则加流程纪律；现在的双层模型是三个月里逐步长出来的。看这类快速演进的项目，"招牌机制是什么时候出现的"和"招牌机制是什么"同样重要。

## 任务流：一个 SaaS 功能穿一遍闭环

下面是个示意案例，把上面的抽象机制串起来——给一个 SaaS 项目加"团队邀请"功能。

1. **生成合同**：`/harness-plan Add team invitation feature...`。CCH 读项目结构，产出 `spec.md`（范围、验收标准、未知项、停止条件）和 `Plans.md`（编号任务清单，如 1.1 建 invitations 表、1.2 加 POST 接口、2.1 邮件服务、3.1 集成测试），同时生成事前确认区。
2. **审批修正**：你发现邮件服务商还没定，在合同里回复"2.1 先做 Resend SDK 抽象层，provider 用环境变量切换；2.3 实时更新先用 30s 轮询，WebSocket 放 v2"，并批准计划里声明的密钥读取。合同据此调整，之后实施不再中途停下问权限。
3. **逐切片执行**：`/harness-work 1.1`、`/harness-work 1.2`……每跑完一个切片，写入带哈希的完成标记。标了要测试的切片，先写测试（红）再写实现（绿）。
4. **独立 Review**：`/harness-review` 不依赖实施上下文重跑，Reviewer 是只读角色（Read/Grep/Glob）。发现格式函数重复这类 minor 问题，你可以手动修掉后标记通过；重大发现会阻塞完成。
5. **打包发布**：`/harness-release` 的 preflight 检查 CHANGELOG、tag 指向、所有任务状态、Review 证据是否齐全，然后生成 PR 描述（What / Changes / Evidence）。

跑完这一圈，你实际做了三件事：审批合同、修一个代码重复、点合并。其余由 CCH 驱动 Agent 完成，每一步都有证据可查。

## v5 的新能力：循环、角色路由、会话互见

**harness-loop**。`/harness-loop` 让执行在限次内循环推进，默认 8 轮，卡住时咨询 Advisor，保留停止原因和重启信息；`/harness-loop status` 看进度，`/harness-loop stop` 停止。中断后用 `/harness-work --resume latest` 恢复，计划、diff、验证结果和剩余验收标准都会带回来。README 特意提醒：到达循环上限或没有可跑任务，不等于所有任务完成——这是两种不同的停止。

**模型角色路由**。CCH 按角色给模型和建议的推理力度，主会话的选择和技能设置仍然优先：

| 角色 | 模型 | Effort |
|------|------|--------|
| Claude 疑难决策与建议（deep/advisor） | Fable 5.1 | high |
| Claude 普通实施 | Sonnet 5 | medium |
| 独立 Claude Reviewer | Sonnet 5 | xhigh |
| Codex 标准工作、决策、评审 | GPT-6 astra | xhigh |
| Codex Breezing 实施 Worker | GPT-5.6 luna | max |

路由表是角色默认值，不是硬编码：手动指定模型和力度始终权威，改父会话不会重调所有子角色。

**会话互见**。同一仓库开多个对话时，`bin/harness session list` 列出各 worktree 里的活跃会话，`bin/harness inbox send` 可以跨会话发消息。消息在接收方的回合边界送达，且被包装成"待核实的数据"而非指令——对方消息是报告，不是命令。开启 `[livemsg] verification = "on"` 后，消息里提到的文件和 commit 会被核实是否存在，"工作区已干净"的说法也会对照实际状态，验证不过的消息被扣下并回执原因。这套机制纯本地，不依赖可选的 harness-mem。

**给非工程师的三块决策面**。Plan Brief（计划定稿时：理解、选项、风险、验收标准）、Progress（进行中：WIP/TODO/done 计数和待决事项）、Acceptance（发布前：逐条验收标准的通过/失败，给出 ship/wait/reject）三张单屏 HTML 页面，让不读代码的负责人也能拍板。`/harness-progress` 只查看状态，不会把工作标记为完成。页面刷新有 60 秒节流；完成百分比是任务数之比，不等于验收通过率。

**auto-approve（实验特性）**。`HARNESS_AUTO_APPROVE=on` 把门控结果记入编排台账，但审批提示**并不因此跳过**——默认关闭，这是一个还在演化的观察性开关。

## 安装路径：四个 supported 不是一个平均数

| 工具 | Tier | 路径 |
|------|------|------|
| Claude Code | `supported` | 插件市场，然后 `/harness-setup` |
| Codex CLI | `supported` | `scripts/setup-codex.sh --user`；更新后重跑并重启 Codex |
| Cursor | `supported` | `scripts/setup-cursor.sh`——隔离在 harness 侧实现 |
| Grok | `supported` | `scripts/setup-grok.sh` |
| Codex app / OpenCode / Hermes Agent / Copilot CLI | `candidate` / `internal-compatible` | 各自受限路径 |
| Antigravity CLI | `future/unsupported` | 暂无端用户安装路径 |

这张表在文章发表时是另一个样子：当时 Cursor 只是 candidate（仅 PM 移交研究）、Grok 根本不在表里、Codex CLI 是 internal-compatible。四个 `supported` 是 7 月中下旬才凑齐的，每个晋升都要过 H1-H8 门禁——实测 H4 是 2026-07-17，发布 preflight 的 fail-closed 接线（H7）是 2026-07-19。README 专门警告：有安装脚本只意味着有入口路径，不等于同等保障；`not_observed != absent`，本地没证据只说明"此处未证实"。

## 谁适合先上，谁可以等等

**适合用：**

- 团队用 Claude Code / Codex CLI / Cursor / Grok，但 PR 质量方差大。
- 需要可验证的交付物，半年后还能回溯"当时为什么改了那个文件"。
- 有明确的 PR / Sprint 流程，想把 AI 嵌进去而不是绕开它。
- 有安全合规要求——禁读敏感文件、拦危险命令、限网络出口，这些不是"实践建议"而是硬约束。

**可以先不急着上：**

- 探索性原型——半小时内要试 5 种方案时，合同-审批-执行循环会拖慢节奏。
- 零依赖的单文件脚本——改一个 50 行的脚本不需要 spec.md。
- 还没把原始的 Claude Code 用顺手——先习惯裸工具，再上约束。

## 常见问题

### 和 Claude Code 自带 Plan Mode 有什么区别？

Plan Mode 是只读窗口：Agent 能读代码、搜索、推理，但不能写文件或执行副作用命令。它保证"先想清楚再动手"，但不保证"想清楚了就做对了"，也没有交付闭环。CCH 在 Plan Mode 之上加的是：结构化合同（spec.md + Plans.md，含验收标准和停止条件）、实施后的独立 Review、发布前的 preflight。Plan Mode 告诉你"先规划"，CCH 要求"规划要成合同、合同要审批、实施要验证、Review 要独立、发布要有证据"。

### 守护层失效了怎么办，会静默变成无保护运行吗？

会退到无保护状态，但不是静默的——这要拆开说。引擎内部的各种失效路径大多是 fail-closed：发布 preflight 任一 host smoke 失败就停发布、plans 状态锁拿不到就中断处理而不是抢写、git 不可用时提交守卫维持原判、secret-read 白名单配置解析失败时全拒绝。但最外层的 shim 是另一种取舍：平台二进制缺失时以退出码 0 结束，hook 协议视为"无裁决"，工具调用继续走，只在 stderr 留一条诊断。设计者的理由写在注释里：shim 不知道当前是哪个 hook，打印错误格式的 JSON 反而会破坏整个 hook 协议。所以装完第一件事应该跑 `bin/harness doctor`，升级或换机器后也要跑——保护是否存在，取决于二进制是否真的在它该在的位置。

### 小任务也要走完整闭环吗？

不用的判断是内置的。era 版 README 就写明 typo、文档、状态更新这类小变更保持轻量；现在的计划技能用 `team_validation_mode: not_required_lightweight` 标记轻量任务，跳过团队校验。判断标准是影响面：单文件、非逻辑变更算轻量；多文件、涉及业务逻辑、需要迁移库表算非轻量。

### 多 Agent 协作时会不会互相覆盖？

标准团队是五个角色：Lead 一个、Worker 1-3 个、Reviewer 一个、Advisor 和 Scaffolder 至多一个。分工的硬边界写在角色契约里：Worker 用 worktree 隔离（`isolation: worktree`），写文件归属按组划分，同一文件绝不给两个 Worker；Reviewer 和 Advisor 的工具清单只有 Read/Grep/Glob，物理上写不了文件；只有 Lead 能 spawn 队友。Plans.md 的状态由 CCH 的命令和对账机制维护，Watcher 会在每次 Write/Edit 后重新聚合标记，配合带哈希的完成标记，Worker 想偷偷把任务标成完成并没有意义。

### 想保留原来的规划习惯，能共存吗？

可以。如果你习惯 planning-with-files 那套三文件组织（task_plan.md、findings.md、progress.md），可以在 CCH 的 Plans.md 体系里手动维护对应文件，或在小任务上用轻量那套、在需要严格流程的任务上切到 CCH。两者不是非此即彼——CCH 约束的是"执行前有合同、执行后有证据"，不规定你用什么格式想问题。

---

*项目地址：[github.com/Chachamaru127/claude-code-harness](https://github.com/Chachamaru127/claude-code-harness)*
