---
title: "Claudian：把 Claude Code、Codex 等编码 Agent 嵌入 Obsidian 笔记库"
date: "2026-04-09T20:40:00+08:00"
lastmod: "2026-09-29T00:00:00+08:00"
slug: "claudian-obsidian-ai-collaboration-guide"
github_repo: "YishenTu/claudian"
source_key: "gh:YishenTu/claudian"
description: "Claudian 是一个把编码 Agent（Claude Code、Codex CLI、Grok Build、OpenCode、Pi）嵌入 Obsidian 笔记库的插件，笔记库即 Agent 的工作目录。本文按 2026-09-29 的仓库状态拆解它的交互机制、MCP 演进、隐私边界与维护模式。"
draft: false
categories: ["技术笔记"]
tags: ["Obsidian", "Claude Code", "知识管理", "MCP", "第二大脑"]
---

# Claudian：把 Claude Code、Codex 等编码 Agent 嵌入 Obsidian 笔记库

大多数 Obsidian AI 插件止步于"问答 + 生成文字"，笔记库对模型来说只是一段被粘贴进上下文的文本。Claudian 换了一条路：它把现成的编码 Agent（Claude Code、Codex CLI、Grok Build、OpenCode、Pi）直接嵌进 Obsidian，让笔记库成为 Agent 的工作目录——读文件、写文件、搜索、跑 shell 命令、多步工作流，开箱即用。模型对笔记的修改直接落在 vault 的文件系统里，你能用 Obsidian 本身的版本管理去审查它。

这个定位带来的分工很清晰：Claudian 只做界面、会话管理和 Agent 适配，不实现任何模型逻辑；推理、工具调用、审批这些事全部交给底层的 Agent CLI 或 SDK。理解了这个分工，就理解了它所有的功能形态，也理解了它的边界——底层 CLI 跑不了的环境（比如移动端），它就无能为力；模型对笔记的每一处修改都直接落在 vault 的文件里，审查和回滚走你已有的文件级工具（Git、备份、Obsidian 的文件恢复快照都行）。

> **项目地址**：[github.com/YishenTu/claudian](https://github.com/YishenTu/claudian)（MIT 许可证）
> **安装入口**：Obsidian 社区插件市场搜索 "Claudian"（插件 id 为 `realclaudian`）
> **数据口径**：本文数据按 2026-09-29 的仓库状态与 GitHub API 读数核实

## 项目数据（2026-09-29）

| 指标 | 数值 |
|------|------|
| Stars / Forks | 15,536 / 1,049 |
| 社区市场下载量 | 约 225.7 万 |
| 最新版本 | 2.3.9（2026-09-29） |
| 2.x 系列发布数 | 69 个（2026-04-06 起，不足 6 个月） |
| 语言构成 | TypeScript 96.9% |
| 运行要求 | Obsidian v1.13.0+，仅桌面端（macOS/Linux/Windows） |

这是一个创建于 2025-12-05 的年轻项目，不到一年涨到 1.5 万 Stars。发布节奏是它的显著特征：2.x 系列平均每周出两三个版本，9 月一个月就发了 10 个。喜欢快节奏迭代的人会如鱼得水，把它当稳定基础设施用的人则需要知道这个节奏的另一面——下文细说。

## 一、系统地图：两层结构，五个 Agent 入口

Claudian 的代码分两层，理解这两层就够了：

| 层 | 位置 | 职责 |
|------|------|------|
| 功能层 | `src/features/` | 侧边栏聊天（多 Tab）、内联编辑、设置面板——纯 Obsidian UI |
| 适配层 | `src/providers/` | 把各 Agent 的接入协议翻译成统一的运行时接口 |

适配层现在是五个入口，各走各的协议：

| Agent | 接入方式（源码 `src/providers/`） |
|-------|-----------------------------------|
| Claude Code | Claude Agent SDK 适配器 |
| Codex CLI | app-server 适配器，JSON-RPC 传输，JSONL 历史 |
| Grok Build | ACP（Agent Client Protocol）适配器 |
| OpenCode | 独立适配器（已支持 OpenCode v2；v1 支持将于 2026-10-30 停止） |
| Pi | RPC 适配器，含模型发现与 JSONL 历史 |

五个入口共用 `src/core/` 的与 provider 无关的执行契约和 `src/providers/acp/` 的共享 ACP 传输层。这条多 provider 架构是 2.0.0（2026-04-06）定下的，当时只有 Claude 和 Codex 两个，其余三个是之后陆续加入的。

选哪条入口，取决于你已有的账号和模型：有 Claude 订阅，接 Claude Code 最省事；用其他模型（Kimi、GLM、DeepSeek 等兼容 OpenRouter 的提供商），Claude Code 和 OpenCode 都能通过配置切换底层模型端点；想用 OpenAI 系，走 Codex。

## 二、核心机制：对话之外的四条交互线

聊天本身和用惯的编码 Agent 没有区别，真正为笔记库设计的是下面四条机制。

### 内联编辑

选中笔记中的一段文字（或把光标放在插入点），按快捷键唤起编辑框，Agent 的修改以词级别 diff 预览呈现，确认后才落笔。这是全文里最"笔记应用"的功能：改一句话不用把整个文件丢给 Agent，也不用担心它顺手改了别处。

### Slash 命令与 Skills

输入 `/` 或 `$` 会呼出两类东西，源码里分得很清楚：

- **内置系统命令**：`/clear`（别名 `/new`）、`/resume`、`/fork`、`/fast`、`/side`（别名 `/btw`）。源码注释特意说明这些是"执行动作的系统命令，不是提示词展开"。
- **Skills 与提示词模板**：来自用户级和 vault 级两个作用域。vault 内的目录约定是 `.agents/skills/` 或 `.claude/skills/`，每个 Skill 一个目录、一个 `SKILL.md` 文件，设置面板里有专门的管理页。

注意 Skills 不是插件预置的——README 原话是 "reusable prompt templates or Skills from user- and vault-level scopes"，清单来自你自己的目录。想定制 Agent 行为，写 SKILL.md 放进 vault 即可，这和 Claude Code 的 Skills 体系是同一套约定。

### @提及

输入 `@` 引用 vault 内的文件和文件夹，路径解析带缓存（源码在 `src/shared/mention/`）。这是把上下文精确交给 Agent 的主要手段——与其描述"我上周写的那篇关于检索的笔记"，不如直接 @ 它。

### Side Chat

`/side` 或 `/btw` 从最近一次回复发起一个独立、临时的旁路对话，可以追问、可以用工具，但主对话的状态不受影响。处理"顺手查个东西但不想污染当前任务上下文"的场景，这个设计比开新 Tab 轻。

### 会话管理

单栏模式下多 Tab 并存；2.1.0（2026-08-05）加入双栏模式后，聊天面板旁边有一个持久的会话管理器。会话支持历史恢复（resume）、整体分叉（fork）和上下文压缩（compact）。存储位置按 provider 各自的约定落盘：Claudian 自己的设置和会话元数据在 `vault/.claudian/`，Claude provider 的会话文件在 `vault/.claude/`，转写历史在 `~/.claude/projects/`（Claude）与 `~/.codex/sessions/`（Codex）。

> 2.0.x 时期的 README 还把 Plan Mode（`Shift+Tab` 切换）和 Instruction Mode（`#` 前缀）列为独立功能。现行 README 的功能列表已不再单列这两项——前者本质是底层 Agent（如 Claude Code 的 EnterPlanMode/ExitPlanMode 工具）自带的能力，Claudian 作为前端透传；后者并入了输入框的指令细化。

## 三、任务流案例：整理一场散落的讨论

把机制串起来看一次真实使用。假设 vault 里散着三篇会议记录，你要整理成一份项目周报：

1. 在侧边栏聊天里 `@` 三篇记录，让 Agent 通读并起草周报。Agent 通过文件工具直接读 vault 文件，你不需要复制粘贴任何内容。
2. 初稿写进一篇新笔记。你对其中一段不满意，选中那段文字触发内联编辑，只改这一段，diff 确认后落笔。
3. 想试另一种组织结构，又不想丢掉当前对话的上下文，`/fork` 把整个会话分叉出去试。
4. 中途冒出一个无关问题，`/side` 开旁路对话问掉，主线不动。

这条链路里每一步都是既有机制的组合，没有一步需要离开 Obsidian。反过来说，它的能力上限也就是"文件读写 + 搜索 + shell + Agent 自带工具"——需要外部数据的地方走 MCP（下一节），除此之外没有别的魔法。

## 四、MCP 的演进：从应用内管理到 CLI 托管

这一节值得单独写，因为它牵涉一次架构转向，老用户容易踩坑。

2.0.x 时期，Claude provider 的 vault 内 MCP 由 Claudian 在应用内管理，Codex 走自己 CLI 管的配置——两套并存。2.3.0（2026-09-18）起方向反转：MCP 设置区从 Claudian 里整体移除，所有 provider 统一改用各自 Agent 的原生 CLI 配置（比如 Claude Code 的 `claude mcp add`）；旧版留在 `.claude/mcp.json` 的遗留配置有专门的清理代码负责删除。

现行口径下，想给 Claude Code 接外部工具，去配 Claude Code 自己的 MCP 配置；换一个 provider，就配那个 provider 的 CLI。Claudian 不再做中间层。这个取舍和它"只做界面与适配"的定位一致——MCP 配置本来就是 CLI 的领地，做一层 GUI 反而要维护两套真相。

## 五、安装与配置

### 安装

首选社区市场：Settings → Community plugins → Browse，搜 "Claudian" 安装启用。也可以从[社区插件页面](https://community.obsidian.md/plugins/realclaudian)直达。开发者可以从源码构建——把仓库克隆进 vault 的 `.obsidian/plugins/` 目录，`npm install && npm run build` 后启用。

前置条件只有两条：至少装有一个上表中的 Agent CLI，以及 Obsidian v1.13.0+ 的桌面端。认证不需要在 Claudian 里填 API key——它跟随底层 CLI 的认证方式（Claude 订阅登录或 API 提供商）。设置里的 Environment 面板可以按"共享"或"单 provider"两个作用域注入环境变量，共享作用域有白名单（PATH、代理、CA 证书等），API 类的变量配在对应 provider 名下。

### CLI 找不到怎么办

GUI 应用继承不到 shell 的 PATH，是这类插件最常见的问题。典型报错是 `spawn claude ENOENT`，用 nvm、fnm、volta 等 Node 版本管理器时尤其常见。README 给的排查顺序：

1. 先把 CLI path 设置留空，让 Claudian 自动检测；
2. 检测失败再手动填路径（Settings → Advanced → Claude Code CLI path），用 `which claude`（macOS/Linux）或 `where.exe claude`（Windows）找到可执行文件；
3. 或者把 Node.js 的 bin 目录加进 Settings → Environment → Custom variables 的 PATH。

Windows 用户注意两点：避免 `.cmd` 和 `.ps1` 包装脚本，原生安装填 `claude.exe`，npm 安装填 `cli-wrapper.cjs`（`cli.js` 只是旧版 npm 包的回退）；还要确认 `claude` 和 `node` 在同一环境里，路径不同时 GUI 应用会找不到 Node。

## 六、隐私与数据边界

README 的 Privacy 一节写得直接，值得照录要点：

- **发给 API 的内容**：你的输入、附加文件、图片和工具调用输出。发往哪里取决于选的 provider——Anthropic（Claude）、OpenAI（Codex）、xAI（Grok），或 OpenCode/Pi 里配置的提供商。
- **无遥测、无未请求的后台活动**：Claudian 不跑遥测信标；UI 轮询定时器只读本地 Obsidian/编辑器选区状态；网络活动限于显式的 provider 运行时工作、已配置的 MCP 端点和回答请求所需的 SDK/CLI 调用。
- **本地落盘**：会话与设置都在本地（位置见第二节），不经过 Claudian 的服务器。

要补的一句是：数据边界止步于 Claudian 本身。你接的底层模型服务（Anthropic、OpenAI 或第三方兼容端点）各有各的数据政策，那部分以各服务商的条款为准。

## 七、版本节奏与维护模式

| 版本 | 日期 | 关键变化 |
|------|------|----------|
| 2.0.0 | 2026-04-06 | 多 provider 架构，加入 Codex 运行时 |
| 2.1.0 | 2026-08-05 | 双栏会话管理 |
| 2.2.0 | 2026-08-21 | Collab 协作模式（现为独立插件 [claudian-collab](https://github.com/YishenTu/claudian-collab)） |
| 2.3.0 | 2026-09-18 | 云协作与 Project Update、回复样式；移除 MCP 设置区 |
| 2.3.9 | 2026-09-29 | 本文核实时的最新版 |

两条维护层面的信息，选型时值得掂量。

**单人维护，且边界划得很硬。** 作者在 CONTRIBUTING.md 里自述是唯一维护者，并明确写死一条政策：不接受新增 provider 的 PR。给的四条理由都很实际——合并后的每个集成都要自己长期维护；各 provider 必须保持一致的功能集和体验，历史上的部分集成很难追平；有些 CLI 能力不足（点名 Antigravity CLI 不暴露 ACP 或同类协议、Cursor CLI 不允许完全自定义 system prompt）；给每家模型厂商的 CLI 都做一遍集成不可持续，OpenCode 和 Pi 本身已支持多厂商。这不是不开放，是单人项目对维护成本的诚实定价。界面国际化（10 种语言）、Skills 管理这类外围改进的 PR 仍然欢迎。

**商业化已经启动。** README 的赞助区有 Kimi（Moonshot AI）和贝壳（BEIKE/MOMA）两家，Kimi 的合作条款里注明 Claudian 不拿返佣。对用户来说，这意味着项目有持续投入的经费来源，也意味着 README 里有商业链接，阅读时自行分辨即可。

## 八、采用建议：谁该现在用，谁该等等

**适合现在就上的人**：vault 已经是主要工作区、同时重度使用编码 Agent 的人——Claudian 解决的正是"Agent 在终端里，笔记在 Obsidian 里"的割裂；想在笔记里跑多步工作流（整理、重构、批量修改）的知识工作者。五条 harness 里选一条自己已有账号的即可，成本几乎为零。

**建议等等的人**：把它当关键业务基础设施的团队——每周数发的版本、单人维护、社区市场页面上"未经 Obsidian 官方人工审核"的标注（社区插件市场的自动收录说明），三件事放在一起，意味着你需要自己承担版本回滚和备份（vault 有 Git 管理的，压力小很多）。移动端用户不必尝试，`isDesktopOnly` 是硬前提。

**不建议的场景**：只想在笔记里问答和生成文字——这类需求用更轻的 AI 插件更合适；指望 Claudian 替你管理 MCP 或模型路由——2.3.0 之后它明确不做这些，配置归各 CLI。

一句话收束：Claudian 的价值不在"又一个 AI 插件"，而在它把成熟的编码 Agent 生态原封不动搬进了笔记库——你得到的是 Claude Code 等工具的全部能力，付出的是"信任一个快节奏的单人项目"的代价。这笔交易对个人知识工作者划算，对求稳的团队需要再评估。

## 资料与口径说明

- 仓库与源码：[github.com/YishenTu/claudian](https://github.com/YishenTu/claudian)（main 分支，2026-09-29 核实）；内置命令清单出自 `src/core/commands/builtInCommands.ts`，Skills 目录约定出自 `src/core/skills/AgentSkillRepository.ts`，provider 环境变量机制出自 `src/core/providers/providerEnvironment.ts`，MCP 遗留配置清理出自 `src/providers/claude/storage/LegacyMCPConfigCleanup.ts`。
- 数据读数：Stars/Forks/贡献者/语言占比为 2026-09-29 GitHub API 读数；下载量 2,257,522 为同日 Obsidian 官方 community-plugin-stats 读数；版本时间线以 GitHub Releases 为准（共 83 个 release，其中 2.x 69 个）。
- 功能与政策口径：以 README（main 分支）与 CONTRIBUTING.md 原文为准；2.0.1 时期的历史口径（应用内 MCP、Plan Mode 快捷键、Obsidian v1.4.5 最低版本）仅用于交代演进，不再是现行行为。
