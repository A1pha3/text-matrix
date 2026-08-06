---
title: "Claude Code Harness：给 AI 编程助手加一套有约束的交付流程"
date: 2026-05-28T09:15:00+08:00
slug: "claude-code-harness-disciplined-delivery-loop"
github_repo: "Chachamaru127/claude-code-harness"
aliases:
  - "/posts/tech/chachamaru127-claude-code-harness-delivery-loop/"
description: "Claude Code Harness 把「让 AI 写代码」收束为「让 AI 按合同交付」：写 Spec→实施→验证→独立 Review→打包证据，用 Go 守护引擎在每次工具调用前拦截越权操作，支持 Claude Code、Codex CLI、Cursor、Grok。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "AI 编程", "工作流", "Skill"]
---

# Claude Code Harness：给 AI 编程助手加一套有约束的交付流程

> **快速信息卡**
> - **GitHub**: [Chachamaru127/claude-code-harness](https://github.com/Chachamaru127/claude-code-harness)
> - **Stars**: 3,045 / **Forks**: 299（GitHub API 2026-08-05 验证）
> - **License**: MIT
> - **主语言**: Shell（守护引擎为 Go 原生）
> - **最近推送**: 2026-08-05

Claude Code 很能写。但任务一超过 3 个文件，就容易出现同一类问题：计划散落在几轮对话之前，测试在 deadline 前被跳过，Review 变成合并之后的事后安慰，PR 描述靠记忆拼凑。这不是某个模型的问题，而是任何没有外部约束的自主 Agent 都会有的倾向。

**Claude Code Harness** 没想着让模型更聪明，它改的是 Agent 外面的流程和边界。核心是一条可重复的路径：**写 Spec → 只实施已批准的任务切片 → 验证 → 独立 Review → 打包证据**。它把"让 AI 写代码"这个开放命题，收束成"让 AI 按合同交付"。

## 两条主线：流程约束 + 安全边界

Harness 看起来是"一个插件"，实际是两层东西，强度刻意不同：

| 层 | 作用 | 能否绕过 |
|------|------|----------|
| **运行时下限（5 类）** | 计费、网络出口、读取密钥、生产部署、任务 worktree 之外的破坏性操作，直接拒绝 | 不能。任何配置、环境变量、权限模式都不行 |
| **守护规则（R01-R15）** | 直接 push 到 main、写受保护路径、强制 push、改写历史等，返回 deny/confirm/warn | 部分可配置 |

运行时下限是一个独立代码路径，不带任何关闭开关，所以一次自主运行没法"说服"自己绕过它。守护规则才是你日常去调的那一层，按项目配置。这是 Harness 区别于"一个 prompt 模板"的地方：每次工具调用在**执行前**就被 Go 引擎裁决，而不是事后看 diff——因为 diff 看不到一次网络请求或一次删除。

## 五个动词，把交付闭环钉死

Harness 只暴露 5 个核心命令，对应交付闭环的每个阶段。表面越小，越难绕路。

| 动词 | 做什么 | 关键门控 |
|------|--------|----------|
| `/harness-plan` | 把需求转成 `spec.md` + `Plans.md`（范围、验收标准、依赖、未知项、停止条件） | 合同要你批准或修正 |
| `/harness-work` | 实施一个已批准任务，任务要求时强制加测试 | 标了 TDD 的任务走红-绿循环 |
| `/harness-review` | 独立验证实施结果 | 实现者不能审自己；重大发现阻塞完成 |
| `/harness-sync` | 对比计划与实际实现，报告漂移 | 只报告，不打包 |
| `/harness-release` | 把已核实的证据打包进 CHANGELOG、tag 和 release | 发布 preflight 必须通过 |

`/harness-setup` 只在安装时跑一次。README 口径里，还有一个 `/harness-work all` 跑完整计划，但"先让单任务跑通、仓库基线清楚了"再用。

几个值得注意的细节：

- **审批前置到计划阶段**。Harness 会把一次计划里需要的风险操作收集起来，在开始执行前一次性问清楚，而不是中途打断。每条审批都有过期时间、任务范围和次数限制，一次批准不会变成一个永久漏洞。
- **每次拦截都会被记录**。规则 ID、类别、裁决落到 JSONL 日志里；命令文本本身不落盘，只记哈希和长度，密钥读取和计费连这些都不记。你能精确数出到底被什么拦住了，而不是靠猜。
- **未知项保持未知**。Agent 没见过但计划里需要的数据，会停在 `unknown`，而不是被悄悄编出来。

## Go 原生守护引擎

v4 的守护层用 Go 重写，`go/` 目录下是一个编译为单二进制的引擎，`go/internal/` 里是 `guardrail`、`event`、`hook`、`session`、`state`、`plans`、`lifecycle` 等模块。README 明确：**Go 原生 guardrail 引擎不需要 Node.js**。hook 调用统一收敛成 `bin/harness hook <event>` 这种模式，而不是一堆散落的 shell 脚本。

为什么值得用 Go 写这一层：守护引擎可能在每次工具调用时都被 hook 机制触发，要走 stdio 解析、规则匹配、返回裁决，路径必须够快，否则会拖慢 Agent 的每一次动作。这正是"热路径"该有的形态。

## 任务流：一个 SaaS 功能穿一遍闭环

下面是个示意案例，把上面的抽象机制串起来——给一个 SaaS 项目加"团队邀请"功能。

1. **生成合同**：`/harness-plan Add team invitation feature...`。Harness 读项目结构，产出 `spec.md`（范围、验收标准、未知项、停止条件）和 `Plans.md`（编号任务清单，如 1.1 建 invitations 表、1.2 加 POST 接口、2.1 邮件服务、3.1 集成测试）。
2. **审批修正**：你发现邮件服务商还没定，在 Plans.md 里回复"2.1 先做 Resend SDK 抽象层，provider 用环境变量切换；2.3 实时更新先用 30s 轮询，WebSocket 放 v2"。合同据此调整。
3. **逐切片执行**：`/harness-work 1.1`、`/harness-work 1.2`……每跑完一个切片，Agent 更新 Plans.md 对应任务状态。标了要测试的切片，先写测试（红）再写实现（绿）。
4. **独立 Review**：`/harness-review` 不依赖实施上下文重跑。发现格式函数重复这类 minor 问题，你可以手动修掉后标记通过。
5. **打包发布**：`/harness-release` 的 preflight 检查 CHANGELOG、tag 指向、所有任务状态、Review 证据是否齐全，然后生成 PR 描述（What / Changes / Evidence）。

跑完这一圈，你实际做了三件事：审批合同、修一个代码重复、点合并。其余由 Harness 驱动 Agent 完成，每一步都有证据可查。

## 谁适合先上，谁可以等等

**适合用：**

- 团队用 Claude Code（或 Codex CLI / Cursor / Grok），但 PR 质量方差大。
- 需要可验证的交付物，半年后还能回溯"当时为什么改了那个文件"。
- 有明确的 PR / Sprint 流程，想把 AI 嵌进去而不是绕开它。
- 有安全合规要求——禁止读敏感文件、禁止危险命令、限制网络出口，这些不是"实践建议"而是硬约束。

**可以先不急着上：**

- 探索性原型——半小时内要试 5 种方案时，合同-审批-执行循环会拖慢节奏。
- 零依赖的单文件脚本——改一个 50 行的脚本不需要 spec.md。
- 还没把原始的 Claude Code 用顺手——先习惯裸工具，再上约束。

## 常见问题

### 和 Claude Code 自带 Plan Mode 有什么区别？

Plan Mode 是只读窗口：Agent 能读代码、搜索、推理，但不能写文件或执行副作用命令。它保证"先想清楚再动手"，但不保证"想清楚了就做对了"，也没有交付闭环。Harness 在 Plan Mode 之上加的是：结构化合同（spec.md + Plans.md，含验收标准和停止条件）、实施后的独立 Review、发布前的 preflight。Plan Mode 告诉你"先规划"，Harness 要求"规划要成合同、合同要审批、实施要验证、Review 要独立、发布要有证据"。

### 失败时会不会静默降级成无保护运行？

README 的设计是 fail-closed：守护层不可用时拒绝启动，而不是退化回无保护。因为如果你选 Harness 是为了安全约束，约束没了就该停，而不是假装还在。特殊场景（比如隔离 CI 里跑构建）需要绕过时，走受控路径，且每次绕过都留审计记录。

### 小任务也要走完整闭环吗？

Harness 区分轻量任务。typo、文档更新这类影响面小的变更，plan 会生成简化合同、work 不强制 TDD、review 快速通过。判断标准是影响面：单文件、非逻辑变更算轻量；多文件、涉及业务逻辑、需要迁移库表算非轻量。

### 多 Agent 协作时会不会互相覆盖？

Harness 用 Git worktree 隔离和 Plans.md 状态标记来避免冲突：Worker 在独立 worktree 里干活，Reviewer 读 Worker 的 diff 但不在同一个 worktree 操作，Planner/Critic 只在规划阶段给建议、不写文件。计划标记由 Harness 自己的命令更新，Worker 不能手改。

### 想保留原来的规划习惯，能共存吗？

可以。如果你习惯了另外一套"写计划、记进度"的文件组织（比如 planning-with-files 的三文件风格），可以在 Harness 的 Plans.md 里手动维护对应文件，或在小任务上用轻量的那套、在需要严格流程的任务上切到 Harness。两者不是非此即彼。

---

*项目地址：[github.com/Chachamaru127/claude-code-harness](https://github.com/Chachamaru127/claude-code-harness)*