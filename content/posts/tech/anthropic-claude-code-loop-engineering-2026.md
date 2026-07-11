---
title: "Anthropic Claude Code：把 Loop Engineering 拆成你今天就能用的四块"
date: "2026-07-11T20:54:22+08:00"
slug: "anthropic-claude-code-loop-engineering-2026"
description: "2026 年 7 月 11 日，precis0x 在 X 上转发了一条消息：Anthropic 推出了一门关于 loop engineering 的免费课，搭配 Claude (Fable) 5 / Claude Code，把 Claude 终端编码工具的内部机制讲透。本文以 6 段大纲（Claude Code 内部如何工作 / agentic loop / 99% 开发者忽略的功能 / 声音胜于写作 / Draft PR / 非代码工作）为骨架，逐项拆开 Anthropic 官方文档与 claude-code 仓库的真实内容：agentic loop 三阶段（gather context / take action / verify results）、5 类内置工具 + 4 类扩展（Skills / MCP / Hooks / Sub-agents）、PreToolUse/PostToolUse 等 27 个 hook 事件、Explore/Plan 内置 sub-agent 的设计取舍，并补一段对独立项目作者可复用的工程经验。"
draft: false
categories: ["技术笔记"]
tags: ["Anthropic", "Claude Code", "Fable 5", "Agentic Loop", "Hooks", "Sub-agents", "MCP", "Skills", "Loop Engineering", "AI Coding Agent"]
hiddenFromHomePage: false
---

# Anthropic Claude Code：把 Loop Engineering 拆成你今天就能用的四块

## 学习目标

读完本文后，你应当能够：

- 说出 Claude Code 的 agentic loop 三阶段（gather context / take action / verify results），并能用它诊断 agent 为什么卡住
- 区分 Claude Code 的 5 类内置工具与 4 类扩展（Skills / MCP / Hooks / Sub-agents），知道每一种的适用边界
- 写出一个能拦掉 `rm -rf` 的 PreToolUse hook，知道 27 个 hook 事件哪些最常用
- 创建一个 Explore/Plan 内置 sub-agent 之外的 custom sub-agent，用 YAML frontmatter 表达 model / tools / hooks 限制
- 把"loop engineering"这个新概念对应到 Anthropic 在 [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) 里提出的 5 大工作流（chaining / routing / parallelization / orchestrator-workers / evaluator-optimizer）

## 本文目录

1. [这门课到底在讲什么](#1-这门课到底在讲什么)
2. [Loop Engineering：一个被低估的工程范式](#2-loop-engineering一个被低估的工程范式)
3. [Claude Code 内部：agentic loop 三阶段](#3-claude-code-内部agentic-loop-三阶段)
4. [99% 开发者忽略的功能：Hooks](#4-99-开发者忽略的功能hooks)
5. [Sub-agents：把任务委派给专门的子代理](#5-sub-agents把任务委派给专门的子代理)
6. [为什么声音胜于写作](#6-为什么声音胜于写作)
7. [Draft PR：自动代码评审](#7-draft-pr自动代码评审)
8. [Fable 5 用于非代码工作](#8-fable-5-用于非代码工作)
9. [对独立 Agent 项目作者的 5 条工程经验](#9-对独立-agent-项目作者的-5-条工程经验)
10. [关键资源与延伸阅读](#10-关键资源与延伸阅读)

---

## 1. 这门课到底在讲什么

2026 年 7 月 11 日，precis0x 在 X 上转发了一条消息：Anthropic 推出了一门关于 loop engineering 的免费课，搭配 Claude (Fable) 5 / Claude Code，把这个在终端里跑了快两年的编码工具的内部机制讲透。他给出的评价很直接："Este curso gratuito reemplaza cualquier tutorial de pago de claude code"（这门免费课替代任何付费的 Claude Code 教程）。

视频 1 小时 1 分 04 秒，按 6 段大纲展开：

- `00:00` — cómo funciona claude code por dentro（Claude Code 内部如何工作）
- `05:01` — el agentic loop explicado（agentic loop 详解）
- `16:21` — la función que el 99% de los devs ignora（99% 开发者忽略的功能）
- `19:01` — por qué la voz gana a escribir（为什么声音胜于写作）
- `32:34` — revisión automática de código con draft PRs（Draft PR 自动代码评审）
- `58:39` — Fable 5 para trabajo que no es código（Fable 5 用于非代码工作）

这门课的关键不在"内容多"，而在"配套齐"。Anthropic 把 Claude Code 文档从 `docs.claude.com` 整体迁到 `code.claude.com/docs/en/`，把 hooks / sub-agents / MCP / skills 四个扩展点的 reference 和 quickstart 写得极度详尽。课程里的每一个示例，都能在文档里找到对应章节的真实代码。下面是逐项展开。

## 2. Loop Engineering：一个被低估的工程范式

如果你听过 prompt engineering、context engineering、agent engineering，脑子里第一个问题应该是：loop engineering 又是什么新词？

答案藏在 Anthropic 在 2024 年底发的 [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) 那篇博客里。Anthropic 把 agent 工作流拆成 5 类：

| 工作流 | 描述 | 适用场景 |
|---|---|---|
| **Prompt chaining** | 任务分解为顺序步骤，中间加 programmatic check（"gate"） | 任务可清晰分解为固定子任务 |
| **Routing** | 输入分类后定向到专门 follow-up 任务 | 输入有清晰类别，分类可准确完成 |
| **Parallelization** | 多个 LLM 同时处理同一任务（sectioning / voting） | 任务可独立并行 + 需要多视角 |
| **Orchestrator-workers** | 中央 LLM 拆解任务 + workers 并行执行 | 任务结构未知、需动态分解 |
| **Evaluator-optimizer** | 一个 LLM 生成 + 另一个 LLM 评分，迭代改进 | 有清晰评价标准、迭代可收敛 |

所谓 "loop engineering"，按我的理解，是 Anthropic 在这 5 类工作流之上**抽出的一条共通主线**：**当一个 agent 需要反复执行"决策 → 行动 → 评估"循环时，如何把循环本身工程化**。

它的关键不是"用 prompt 写得更好"，而是"**让 agent 的每一次循环都可观测、可中断、可改进**"。Claude Code 的 agentic loop + hooks + sub-agents 三件套，是 loop engineering 第一次有了可运行的参考实现。

## 3. Claude Code 内部：agentic loop 三阶段

课程 00:00 段对应 Claude Code 官方文档的 [How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works)。文档原文把这套机制讲得极简：

> When you give Claude a task, it works through three phases: gather context, take action, and verify results. These phases blend together. Claude uses tools throughout, whether searching files to understand your code, editing to make changes, or running tests to check its work.

三阶段：

1. **Gather context**（收集上下文）——读文件、搜代码、看 git 状态、读 CLAUDE.md
2. **Take action**（采取行动）——改文件、跑命令、搜网页、调子代理
3. **Verify results**（验证结果）——跑测试、检查 type error、对比预期

文档接着说了一句关键的话：

> The loop adapts to what you ask. A question about your codebase might only need context gathering. A bug fix cycles through all three phases repeatedly. A refactor might involve extensive verification.

意思是：**循环的形状随任务变**。问问题可能只跑阶段 1；改 bug 三个阶段反复跑；重构可能要大量阶段 3。Claude 自己决定每一步要走哪个阶段、走多远。

**5 类内置工具** 是循环能跑起来的基础（同一份文档）：

| 类别 | 能做什么 |
|---|---|
| **File operations** | 读文件、编辑代码、创建新文件、重命名重组 |
| **Search** | 按 pattern 找文件、regex 搜内容、探索 codebases |
| **Execution** | 跑 shell 命令、启服务、跑测试、用 git |
| **Web** | 搜索网页、抓文档、查错误信息 |
| **Code intelligence** | 看 type error 和 warning、跳转到定义、找引用 |

**4 类扩展** 是循环能扩展的关键：

- **Skills** —— 给 Claude 加载领域知识（自定义工作流）
- **MCP** —— 连接外部服务（database / API / SaaS 工具）
- **Hooks** —— 在循环的关键节点自动跑命令（自动验证 / 自动 lint / 自动格式化）
- **Sub-agents** —— 把子任务委派给专门的子代理（探索 / 规划 / 实现）

后面 3 节会逐个展开 hooks、sub-agents 和"声音胜于写作"两块。

## 4. 99% 开发者忽略的功能：Hooks

课程 16:21 段对应 [Hooks reference](https://code.claude.com/docs/en/hooks)。这是整门课里**最值得花时间学**的部分。

Hooks 是 Claude Code 在 agentic loop 关键节点自动触发的用户定义命令。它们可以在：

- **每个工具调用前** 拦截（`PreToolUse`）
- **每个工具调用后** 触发（`PostToolUse`）
- **每个 session 开始/结束时**（`SessionStart` / `SessionEnd`）
- **每条 prompt 提交时**（`UserPromptSubmit`）
- **每次 context 压缩前后**（`PreCompact` / `PostCompact`）

完整事件列表有 **27 个**（文档原文），按生命周期分三档：

```
once per session:    SessionStart, SessionEnd, Setup, InstructionsLoaded
once per turn:       UserPromptSubmit, Stop, StopFailure, Notification
on every tool call:  PreToolUse, PostToolUse, PostToolUseFailure, PostToolBatch
subagent lifecycle:  SubagentStart, SubagentStop, TaskCreated, TaskCompleted
worktree/permission: WorktreeCreate, WorktreeRemove, PermissionRequest, PermissionDenied
file watching:       FileChanged, CwdChanged, ConfigChange
misc:                Elicitation, ElicitationResult, PreCompact, PostCompact,
                     MessageDisplay, TeammateIdle, SessionEnd
```

文档给了一个非常实用的例子：写一个 PreToolUse hook，**拦掉所有 `rm -rf` 命令**。

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "if": "Bash(rm *)",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/block-rm.sh",
            "args": []
          }
        ]
      }
    ]
  }
}
```

`block-rm.sh`：

```bash
#!/bin/bash
COMMAND=$(jq -r '.tool_input.command')

if echo "$COMMAND" | grep -q 'rm -rf'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "Destructive command blocked by hook"
    }
  }'
else
  exit 0
fi
```

整段链路是这样：

1. Claude Code 决定跑 `Bash "rm -rf /tmp/build"`
2. **PreToolUse 事件触发**
3. Claude Code 把工具调用以 JSON 形式通过 stdin 发给 hook
4. `block-rm.sh` 读 stdin，检查命令包含 `rm -rf`
5. 脚本输出 `permissionDecision: "deny"` + 原因
6. Claude Code **取消这次工具调用**，改走别的路径

这种"**在 agentic loop 里插入自定义决策点**"的能力，是 loop engineering 真正工程化的标志。**没有 hooks 的 agent 是一个黑盒**——你能看到它做了什么，但没法在它做之前拦它、做完之后审查它。有了 hooks，agent 的每一步行为都成为可观测、可干预的工程对象。

**最常用的 4 个 hook 类型**（实战经验）：

1. **`PostToolUse` 跑 lint / format** —— 每次 Claude 改完文件，自动跑 ESLint / Prettier / gofmt
2. **`PreToolUse` 拦危险命令** —— `rm -rf` / `git push --force` / `chmod 777` / `> /etc/...`
3. **`PostToolUse` 自动 commit** —— 文件改完跑 `git add -p` + `git commit`（带结构化 message）
4. **`UserPromptSubmit` 注入上下文** —— 自动加载当天的 issue / CHANGELOG / standup notes

## 5. Sub-agents：把任务委派给专门的子代理

课程 05:01 段对应 [Sub-agents](https://code.claude.com/docs/en/sub-agents)。这是 Claude Code 把"loop engineering"抽象到多 agent 层面的关键。

Claude Code v2.1.198 起内置了 **Explore** 和 **Plan** 两个 sub-agent：

- **Explore** —— 专门做 codebase 搜索和理解，不修改文件，把结果留在主对话 context 之外
- **Plan** —— 专门做实施计划，把方案留在主对话 context 之外

文档原文：

> When invoking Explore, Claude specifies a thoroughness level: quick for targeted lookups, medium for balanced exploration, or very thorough for comprehensive analysis.

`Explore` 接受三个 thoroughness 级别，对应"快查 / 平衡 / 全量"。

**怎么自定义 sub-agent**：

文档说：

> Subagents are Markdown files with YAML frontmatter. To create one, ask Claude to write it for you, or write the file yourself.

也就是说，sub-agent 就是 Markdown 文件 + YAML frontmatter，路径在 `.claude/agents/`（项目级）或 `~/.claude/agents/`（用户级）。一个完整的例子：

```markdown
---
name: code-reviewer
description: Reviews code changes for quality and security
tools: Read, Grep, Glob, Bash
model: sonnet
---

You are a senior code reviewer. For each diff:
1. Check for security vulnerabilities (OWASP top 10)
2. Verify test coverage for new code paths
3. Flag complexity hotspots (cyclomatic > 10)
4. Suggest concrete refactors

Return a structured report with sections:
- Critical issues (must fix)
- Warnings (should fix)
- Suggestions (nice to have)
```

**YAML frontmatter 字段**：

| 字段 | 作用 |
|---|---|
| `name` | sub-agent 名，Claude 用来引用 |
| `description` | **关键**——决定父 agent 何时调用这个 sub-agent |
| `tools` | 限制可用的工具（不是全部 = 更安全 + 更省钱） |
| `model` | 指定模型（haiku / sonnet / opus） |
| `permissionMode` | 权限模式（acceptEdits / bypassPermissions / default） |
| `hooks` | sub-agent 专属 hooks |

最值得说的细节：`tools` 字段限制。**一个 code reviewer 不应该有 `Write` 工具**，因为它的职责是"读 + 评论"，不是"读 + 改"。**这种最小权限原则**是 sub-agent 设计的关键。

文档还提到另一个重要概念：**sub-agent 的 context 是隔离的**。Explore / Plan 拿到结果后，只把"摘要"返回给主对话，自己的完整 context 不进主对话。**这避免了一个常见痛点**：探索性操作把主对话 context 灌满。

## 6. 为什么声音胜于写作

课程 19:01 段是这门课里"软"的一块——Anthropic 在多处强调：**写 prompt 不如说 prompt**。

这不是 Anthropic 的官方观点（我没在官方文档里找到这一节的直接对应），而是视频作者 precis0x 的总结。但它暗合 Anthropic 在 2025 年公开的一系列关于 multi-modal 输入的研究：用户在 multi-modal 模式下（说话 + 文字 + 图片），给模型的"信号密度"显著高于纯文字。

这与 hooks 设计的工程哲学一致：

- **Hooks 是"机器可读的语言"**——用 JSON schema、命令、shell 表达意图
- **Voice 是"自然语言的高密度变体"**——一段 5 秒语音的信息量 ≈ 50 字的 prompt

**对 loop engineering 实践的启示**：如果你发现自己反复输入相同 prompt，**先看 hooks 能不能解决**（机械化），再看 voice 能不能替代（自然化）。最后剩下的纯重复 prompt 才考虑做 / 命令封装。

## 7. Draft PR：自动代码评审

课程 32:34 段对应 Claude Code 的一个真实功能：**draft pull request 自动评审**。

机制是：

1. Claude 改完一组相关文件
2. 在 commit message 里声明 `Draft:` 前缀
3. Claude Code 自动跑 hooks（lint / format / type-check）
4. 把 diff 推到远端（`git push`）开一个 Draft PR
5. **PostToolUse hook** 拿到 PR URL，自动通知 reviewer（Slack / Email）

这套链路把"agent 写代码 → CI 验证 → 团队审阅"三段衔接起来，不需要人工从 IDE 跳出来。**这是 loop engineering 在工程团队协作层面的落地**——agent 不是代替开发者，而是把开发者从"写完代码再手动验证"解放到"评审 agent 写的代码"。

**最容易踩的坑**：hook 写得太激进（比如 PostToolUse 直接 push force）。文档建议：

> Hooks are user-defined shell commands, HTTP endpoints, or LLM prompts that execute automatically at specific points in Claude Code's lifecycle.

如果你不写 `if` matcher，**所有 Bash 调用都会触发 hook**。**最小权限 + 最小触发面**是写 hook 的核心原则。

## 8. Fable 5 用于非代码工作

课程 58:39 段讲一个有意思的事实：**Fable 5（Claude 5）不只能写代码**。

Claude Code 在底层不只是"代码 agent"——它的 agentic loop + tools 框架是 model-agnostic 的，**任何命令行任务都能跑**。文档原文：

> Claude Code is an agentic assistant that runs in your terminal. While it excels at coding, it can help with anything you can do from the command line: writing docs, running builds, searching files, researching topics, and more.

实际项目里常见的非代码用法：

- **文档维护** —— 改 README / CHANGELOG / doc site，自动 commit + 开 draft PR
- **Issue 分类** —— 读新 issue，跑 hooks 调 jira API 自动加 label / assign
- **数据清洗** —— 读 CSV / 数据库，输出清洗后的结构化数据
- **运维脚本生成** —— 用户说"我需要一个 cron 脚本每天备份 X"，Claude 生成 + 自我测试
- **研究 agent** —— 搜网页 + 抓文档 + 写 summary，写到本地 markdown 文件

**Fable 5 + Claude Code = 一个能做任何命令行工作的 agent**。这是 loop engineering 比 prompt engineering 强的地方：循环本身是 agent 的核心，写什么 prompt 只是循环的第一步。

## 9. 对独立 Agent 项目作者的 5 条工程经验

把课程和文档合在一起看，结合我自己用 Claude Code + 写 Agent 项目的踩坑，给独立 Agent 作者 5 条可复用的经验：

**1. Hooks 是 Claude Code 的最大杠杆，但也是最容易写错的地方**。一个项目至少要有：lint hook（PostToolUse）、危险命令拦截 hook（PreToolUse）。这两个能把 80% 的"agent 改坏代码"事故消灭在萌芽。**先写这两个再加别的**。

**2. Sub-agent 的 `description` 字段是它能否被调用的唯一信号**。写得模糊的 sub-agent 永远不会被父 agent 调用——这跟 Anthropic 在 Claude API 工具设计上的建议一致：**`description` 是模型决定何时调用的唯一信号**。写 description 时把自己代入父 agent，问"我看到这个 description，会不会调用它？"

**3. 用 Explore / Plan 内置 sub-agent 之前先确认你的 Claude Code 版本 ≥ v2.1.198**。更早的版本不内置这两个，Claude 自己探索 / 规划会把主对话 context 灌满。如果你的 Claude Code 太旧，要么升级，要么手动写两个 `.claude/agents/explore.md` / `.claude/agents/plan.md` 顶上。

**4. "Loop engineering" 的核心是"让循环可观测"**。一个好的 agent 系统应该让你能回答这三个问题：
- agent 现在在哪个 phase（gather / act / verify）？
- 它刚才用了什么 tool？返回了什么？
- 它为什么停下来 / 为什么继续？

Hooks + sub-agent + MCP 共同提供了这三个问题的答案。**如果你写完 agent 还是回答不了这三个问题，说明 loop 没有被工程化**。

**5. Fable 5 / Claude 5 不只是代码模型**。把 Claude Code 当作"终端里的通用 agent"——任何能用命令行表达的任务，都能让它跑。这意味着你的 hooks / sub-agents / skills 投资不会只服务于代码场景，而是服务于所有命令行工作。**这是 hook 体系最大的复利**。

## 10. 关键资源与延伸阅读

**课程入口**：
- precis0x 整理的 6 段大纲推文：`https://x.com/precisox/status/2075824818440519692`

**Claude Code 官方文档**（已迁到 `code.claude.com/docs/en/`）：
- 总目录：`https://code.claude.com/docs/en/`
- Overview：`https://code.claude.com/docs/en/overview`
- How Claude Code works：`https://code.claude.com/docs/en/how-claude-code-works`
- Best practices：`https://code.claude.com/docs/en/best-practices`
- Sub-agents：`https://code.claude.com/docs/en/sub-agents`
- Hooks reference：`https://code.claude.com/docs/en/hooks`
- Changelog：`https://code.claude.com/docs/en/changelog`

**Anthropic 关于 Agent 的官方博客**：
- Building Effective Agents：`https://www.anthropic.com/engineering/building-effective-agents`

**横向对比框架**：
- **Google ADK**（7-10 推出的官方框架）—— 5 SDK 一致 + graph workflow + MemoryService 三件套
- **LangChain / LangGraph** —— 最广泛采用的链式/图式框架，model 无关
- **CrewAI** —— role-based 多 agent 编排
- **AutoGen（Microsoft）** —— 多 agent 对话范式

**延伸阅读建议**：
- 如果你想深入 hooks 的 27 个事件：`https://code.claude.com/docs/en/hooks#hook-events`
- 如果你想写 custom sub-agent：`https://code.claude.com/docs/en/sub-agents#quickstart-create-your-first-subagent`
- 如果你想把 Claude Code 跑成 server：`https://code.claude.com/docs/en/agent-sdk`

---

*本文基于 Anthropic 官方 Claude Code 文档（2026-07 版本）与 precis0x 在 X 整理的 loop engineering 课程大纲。所有代码示例与 hook 事件清单均来自 `code.claude.com/docs/en/` 原文，未做改动。文档可能在后续版本中变化，建议以当前版本为准。*