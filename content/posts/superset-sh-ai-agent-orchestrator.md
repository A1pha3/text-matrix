---
title: "Superset：9 个月 12.8k stars 的 AI Agent 指挥舱是怎么长出来的"
date: 2026-08-07T16:45:00+08:00
draft: false
tags: ["AI Agent", "Developer Tools", "TypeScript", "Electron", "Git Worktree", "Open Source"]
categories: ["技术文章", "AI Agent 基础设施"]
description: "GitHub 12.8k stars 的 Superset 把 Claude Code、Codex、Cursor、Gemini、Kimi、Grok 全部装进同一个工作台——9 个月 12.8k stars 不靠营销，靠把 git worktree 做成产品。"
slug : superset-sh-ai-agent-orchestrator

---

# Superset：9 个月 12.8k stars 的 AI Agent 指挥舱是怎么长出来的

`superset-sh/superset` 在 GitHub 上是 12.8k stars 的项目。

2025-10-21 创建，到 2026-08-07 共 291 天——9.5 个月。Elastic 2.0 开源。CLI、TypeScript SDK、MCP Server 三件套一应俱全。

读到这些数字你大概不会划走。但你也不会太意外——AI Agent 赛道今年涨星快。

读完之后我改主意了。**Superset 做的事不是"做一个 IDE"，是把"代码编辑器"这个品类整个翻过来**——原来 IDE 是人写代码的工具，现在 IDE 是指挥 AI 写代码的工具。9 个月做到 12.8k stars，不靠营销，靠把"git worktree"做成产品。

---

## 一、先看一眼它是什么

Superset 是一台桌面应用（Electron + React + TypeScript），发布在 macOS 和 Linux，配套一支 CLI、一个 TypeScript SDK、一个 MCP Server。它只做一件事：**让你的本地机器同时跑 10+ 个 AI 编程 Agent**，每个 Agent 占一个 git worktree，互不打架。

支持列表看一眼就破防：

| Agent | 状态 |
|---|---|
| Claude Code | ✅ |
| OpenAI Codex CLI | ✅ |
| Cursor Agent | ✅ |
| Gemini CLI | ✅ |
| GitHub Copilot | ✅ |
| Grok (xAI) | ✅ |
| Kimi Code (Moonshot) | ✅ |
| OpenCode | ✅ |
| Mistral Vibe | ✅ |
| Amp Code | ✅ |
| Droid (Factory) | ✅ |
| Mastracode | ✅ |
| Polygraph | ✅ |
| Pi | ✅ |
| 任何 CLI Agent | ✅（无需配置） |

"如果它能在终端跑，它就能在 Superset 跑。"——这是它的兼容宣言。

这里的关键词不是"多"。每个 Agent 都有自己的 CLI、自己的 prompt 模板、自己的 model picker、自己的 session 协议——Cursor 偏 GUI、Codex 偏云、Claude Code 偏本地、Gemini 偏 Google 自家生态。Superset 干的事，是把它们**统一沉淀到同一个工作台**。

---

## 二、核心模型：五个概念搞定一切

Superset 文档里有一节叫 "The Superset Model"，把整套产品抽象成五个概念：

1. **Workspace** — 一个隔离的工作区，本质是一个 git worktree。这意味着：每个 Agent 跑在自己的分支、自己的目录、自己的端口、自己的终端里，谁也不会踩到谁。
2. **Host** — 一台机器。Superset 桌面 app、CLI、SDK、MCP 都在跟 Host 通信。桌面可以同时连多台 Host（比如你的 MacBook 操控 Mac mini 上的 Agent）。
3. **Project** — 一个 GitHub 仓库链接到某个 Host 后的投影。多个 Workspace 可以属于同一个 Project。
4. **Task** — 一个可被调度的任务单元。可关联到 PR、Issue、Slack 消息、Linear 工单。
5. **Automation** — 一个定时任务，按 RFC 5545 RRule 触发，落地是一个新的 Workspace。

读到这里你应该感觉到了——Superset 其实在做一个**"用 Git 做分布式账本"**的事：每个工作区是 commit，每个 Agent 是 worker，PR 是同步协议。"worktree" 一词是这个比喻的物理载体。

对开发者来说，这意味着 **git workflow 不再被 AI 终结，而是被 AI 放大**。原来 PR 是终态，现在 PR 是中间状态——多 Agent 并发写，多个 PR 横向对比，最终 merge 赢家。

---

## 三、把"Terminal"做对

终端是 Superset 最朴素但最厚重的部分。我读它的 Features 表时注意到了一个细节：

> "Tabs, infinite splits, presets, and persistent sessions that survive restarts. Press ⌘I for a rich prompt editor with multiline editing and @-file mentions."

注意到三件事：

1. **persistent sessions** —— 关闭 app 不会杀掉 Agent 进程，下次打开还活着。
2. **⌘I 召唤富 prompt 编辑器** —— 多个 Agent 共享同一个 prompt 编辑器，可以 `@file/path` 引用文件。
3. **@-file mentions** —— 这就是 Cursor、Claude Code 用户最熟悉的"@file"语法，但 Superset 让它跨 Agent 工作。

第三点解释了为什么 Superset 不是一个"换皮终端"：它把**指令层**从"Agent CLI"提升到了"工作台"。原本你只能在 Claude Code 里 `@README.md`，现在你能在 Superset 里 `@README.md` 喂给任何 Agent。

底层栈：Electron + React + Tailwind + Bun + Turborepo + Vite + Biome + Drizzle ORM + tRPC + Neon Postgres + Caddy 反代。语言统计 TypeScript 占 15.7M 行（约 98%），其它加起来只占 2%——**纯 TS 单语言 monorepo**。

我注意到它没选 Rust、Tauri、Swift——选 Electron 有理由：跨平台 + 调试顺手 + 跟"Agent 终端"这个场景天然亲。终端本身就是 Electron 弱项，但 Superset 用 xterm.js + 自研 CloudTerminal 填了。**sidex 选 Tauri 是另一种哲学，Superset 选 Electron 也是另一种哲学**——前者要"轻"，后者要"快出活"。

### 自己跑一次的步骤

```bash
# macOS 桌面版
curl -fsSL https://superset.sh/cli/install.sh | sh   # 或 brew install superset-sh/tap/superset
# 下载桌面 dmg: https://github.com/superset-sh/superset/releases/latest
# Linux: x64 AppImage（macOS 是主要目标平台）

# CLI 单跑
superset new                 # 创建新 workspace
superset new --branch fix/x  # 指定分支
superset automations list    # 看定时任务

# MCP 接入 Claude Code
claude mcp add superset --transport http https://api.superset.sh/mcp
```

开发 setup 走 `./.superset/setup.local.sh`（Docker 起本地 Postgres + Electric + Caddy HTTPS 反代 + 种子账号）。文档里明说**不需要 Neon 账号或第三方 credentials**——这是给贡献者看的本地开发环境。

---

## 四、把"批量管理"做对

并行 worktree 模式其实不新鲜——tmux、git worktree 各自的命令行工具、早一批 Kiro 风格的 IDE 都有。Superset 把"批量管理"这件事做到了桌面级：

- **批量动作** —— ⌘-click 多选、⇧-click 区间选；选中后整个 Projects header 变成 toolbar，可以 Move / Ungroup / Delete。
- **删除前的 dry-run** —— "Bulk delete previews every workspace and flags dirty or unpushed changes before you confirm"——这是 Git 老炮才写得出来的产品细节。
- **侧栏靠前显示** —— 把 Pinned 工作区钉在 Project 上面，剩下才是普通的。
- **Ahead/Behind 量化** —— 侧栏实时显示当前分支比远端超前 / 落后多少 commit。`↑N` `↓N` 两个图标的字面直接镜像 git status。

> "The sidebar now works like a file manager." —— 8 月初 changelog 里那句原话。

把"侧栏"做成"文件管理器"是一个**隐喻的胜利**。JetBrains、VS Code 一直在用"文件树"做隐喻；Superset 把"工作区"做成了隐喻。这跟 AI Agent 时代契合：你不是打开一个文件，是**打开一个 Agent 的过程**。

---

## 五、把"Agent 接入"做对

Superset 接 Agent 的方式很克制——**不抄 SDK、不收编协议，只做终端**。

它把 Agent 抽象成三类命令：

- `Command (No Prompt)` — 终端型 Agent 的启动命令
- `Command (With Prompt)` — 带 prompt 的启动命令
- `Prompt Command Suffix` — 启动后追加的命令后缀

然后你可以给每个 Agent 配自己的 icon、model override、prompt 模板。要加一个新 Agent？去 Settings → Agents → Add agent，按图标填命令，完事。

这是**把"插件化"做到 SDK 之下的极致路径**。它没问 Claude Code / Codex 要 API key，也没用 MCP 协议——它只是**让 Agent 在它的终端里跑**。这跟 Linear 接 Figma、Slack 接 GitHub 完全两套思路：前者"接内核"，后者"接显示"。

MCP 反而是另一个入口：Superset 自己**对外暴露**了一个 MCP server（`https://api.superset.sh/mcp`），让别的 Agent 能反过来**操控** Superset。比如你让 Claude Code 帮你"在 Superset 里并行起 3 个 Agent，一个跑测试、一个写文档、一个做 review"——Claude Code 通过 MCP 调 Superset CLI，Superset 起 3 个 workspace 然后回到 Claude Code 继续汇报。

这是一个**反过来的乐高**：原本是 Agent 操控应用，现在应用操控 Agent，两端都有 MCP。

---

## 六、把"Skills"做对

Superset 落地 8 个内置 Skill，全部 `superset:` 命名空间：

| Skill | 作用 |
|---|---|
| `superset:setup` | 把任意仓库变成 Superset-ready（写 `.superset/config.json`） |
| `superset:orchestrate` | 让当前 Agent 变成"协调器"，并行调度多个 Agent |
| `superset:automate` | 把一次性任务变成定时 Automation |
| `superset:standup` | 每个早晨的工作区 / 任务 / Agent 状态摘要 |
| `superset:doctor` | 诊断 Superset 自身问题（auth、host、版本） |
| `superset:feedback` | 把 bug 反馈给 Superset 团队（带账号、可以回复） |
| `superset:10x` | 审计你用 Superset 的方式，推荐高级功能 |
| `superset:contribute` | 一键准备好给 Superset 提 PR 的全套环境 |

这套 Skill 的反直觉在于：**App 主动教 Agent**。通常 App 等 Agent 来接入；Superset 主动给 Agent 写 Skill。安装方式就一行：

```bash
npx skills add superset-sh/skills
```

或者在 Claude Code 里：

```
/plugin marketplace add superset-sh/superset
```

每个 Skill 在桌面 app 启动时自动写入到 `~/.claude/skills/superset/`、`~/.agents/skills/`、`~/.agents/commands/`。**管理文件带 marker，用户自己写的同名 Skill 不会被盖**。这个细节我读了两遍——它承认了一件事：用户是 Agent 生态的真正主人，App 只在用户没占坑的地方占。

---

## 七、把"调度"做对

Automation 用的不是 cron 表达式（不易读），是 RFC 5545 RRule：

```text
FREQ=DAILY;BYHOUR=9;BYMINUTE=0
FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=9
```

每个 Automation 落地成一个新 Workspace，火起来是某个真实 Host 上的某个 Agent Session。原文特别提到：

> "At-least-once delivery: Automations may dispatch more than once in rare cases (e.g. dispatcher retries). **Design prompts that are safe to re-run.**"

这是分布式系统老炮才写得出来的告警——重做一次可能产生重复 PR / 重复 commit，prompt 本身必须幂等。

文档里也明说还没做"completion tracking"——Automation 跑到 dispatched 就停了，不知道 Agent 写完没写完；打开 workspace 才知道。这是**"诚实的小步走"**——做不出来就别假装做了。

---

## 八、把"定价"做对

> "The desktop app is free forever. Running agents in parallel on your own machine will never require payment. Anything we charge for will be an optional service on top."

直白、不绕弯。**桌面 app 永久免费**——这意味着 12.8k stars 背后是真的开源产品，不是 SaaS 圈用户。**收费的将是云端服务**（Cloud Workspace 跨设备同步、企业版的多人协作、MCP Server 高级 SOP）。

这套商业模型让人想起 GitLab：工具开源、企业版收费。区别是 GitLab 卖的是"私有部署"，Superset 卖的是"Agent 编排云"。

---

## 九、用户怎么说

网站首页挂了 9 条真实推荐，挑三条原文：

- **Abhi Aiyer** (Mastra Co-founder & CTO): *"Just realized that I have done all my work in @superset_sh since Dec 26."*
- **Zach Dive** (Adam Co-founder & CEO): *"if you're not using @superset_sh, you're getting left behind in 2026."*
- **Felipe Coury** (Codex at OpenAI): *"If you prefer a more GUI-oriented approach to multiple agents in parallel, it seems like @superset_sh is doing a tremendous job."*

最后一条尤其值得玩味——**OpenAI 内部负责 Codex 的人公开推荐第三方工具**。这不是八卦，是信号：连 Agent 的开发者都承认，**"前端 Agent 编排" 不该自家做**。

---

## 十、它没做对的事

12.8k stars 不等于一切正确。我读完材料后，看到四个未解的硬伤：

1. **Windows 不支持**——只有 macOS Apple Silicon、macOS Intel、Linux x64 AppImage。Windows 用户在桌面 OS 市占占大头，这个真空是 Superset 团队自己说的"not yet available"。
2. **Sandbox Access 还没做稳**——Agent 访问工作区外的文件需要 prompt 权限，这本身是好设计，但文档里承认 "files outside its workspace" 流程还有 friction。
3. **Completion 跟踪缺失**——Automation 跑出去就 dispatched，不知道 Agent 写完了没；点开 workspace 才知道。这让"早上一觉醒来看到昨晚 3 个 PR 都 ready"的体验打了折扣。
4. **Elastic 2.0 不是 OSI 开源**——协议允许自用、修改、内部托管，**禁止打包成 SaaS 转卖**。这是"开源但不自由"的典型取舍。GitLab 早期选 AGPL 也是同样考虑，结果反而催生企业版收入。如果你只是想用，完全免费；如果你想卖 Superset-as-a-Service——条款里说不允许。

这些问题都不是不能解决，但把它们写出来——是 Superset 团队的诚实。

---

## 十一、把它放在更大的地图里

Superset 不是第一个吃 AI Agent 多任务并行螃蟹的。文档里自己列了同类：

> Conductor, Vibe Kanban, Agentastic, Crystal, FleetCode, Emdash, Sculptor

外加 LLM workflow studio（AutoGen Studio、LangGraph Studio 等）——但这些更偏"图形化编排 LLM 调用图"，跟 Superset 的"worktree 隔离 + Agent 终端 + PR 流"不是同一类需求。

Superset 跟它们相比，三个**差异化护城河**：

1. **真桌面 + 真本地**——不是 SaaS、不是 web 工具。CLI 真存在、MCP 真能本地跑。
2. **Git worktree 原生**——不是"container 隔离"，是"git 隔离"。diff、commit、PR 全套都顺。
3. **Agent 协议中立**——不抄 SDK、不收编协议、不做"我的 Agent 比你强"。**最强的兼容性策略是"我们不选边"**。

第三条是哲学问题。Cursor、Codex、Claude Code 都在做"自己的 Agent 平台"，想做"Agent 之上的一层"。Superset 反过来——**做"Agent 之下的调度层"**。这是个明确定位，也有代价：它的天花板被 Agent 本身锁住，Agent 不再重要时它就不重要。

但 2026 年，Agent 显然正在变得更重要。

---

## 十二、读完它我重新理解了"工作台"

Superset 让我重新审视一件事：在一个 AI Agent 写代码的时代，**"工作台"到底是什么**。

过去 30 年我们默认工作台就是 IDE：左边文件树、右边编辑器、下边终端、上边工具栏。JetBrains 把它打磨到极致，VS Code 把它打磨到普及，Cursor 把它打磨到 AI 化。

但 Cursor 的天花板是——**它只能编排一个 Agent**。你要同时跑 3 个 Agent 做 3 个 PR，Cursor 不行；你要同时跑 1 个 Agent 在 MacBook、1 个 Agent 在 Mac mini，Cursor 不行；你要批量管理 30 个工作区，Cursor 不行。

Superset 做的事情是：**把"工作台"从编辑器升级为"指挥舱"**。左边是 Agent 队列，右边是 git diff，下边是终端池，上边是 prompt 编辑器。

这是 9 个月长出来的产品，不是 9 年。这是 12.8k stars 跑出来的方向，不是 1000 万 DAU 堆出来的方向。

它的下一步未必是 IDE 取代——更可能是**让 IDE 退回到"编辑器"这个原始角色**，而组合其他工具（Agent、git、调度）由指挥舱统一。

---

## 写在最后

读完 Superset 之后，我最想转发给身边做工具的朋友的一句话是：

> "The Code Editor for the AI Agents Era."

不需要更多修饰。

它不是 IDE 的新版本，它是 IDE 这个品类的**重新定义**。

而这种重新定义，是 2026 年工具圈最稀缺、也最值得抄的能力。

---

**仓库**：[superset-sh/superset](https://github.com/superset-sh/superset) · 12,801 stars · TypeScript 98% · Elastic 2.0
**官网**：[superset.sh](https://superset.sh)
**文档**：[docs.superset.sh](https://docs.superset.sh)
**团队**：Avi (@avimakesrobots) · Kiet (@flyakiet) · Satya (@saddle_paddle)