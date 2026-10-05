---
title: "Agency Agents 解读：把 AI 角色做成可分发资产的目录、转换器与安装器"
slug: "msitarzewski-agency-agents-ai-specialists-collection-guide"
github_repo: "msitarzewski/agency-agents"
source_key: "gh:msitarzewski/agency-agents"
date: 2026-06-29T21:02:57+08:00
lastmod: 2026-10-03T16:50:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["GitHub", "AI Agent", "Claude Code", "Cursor", "Prompt Engineering", "开源"]
description: "msitarzewski/agency-agents 把 267 个 AI 角色定义写成带 frontmatter 的 Markdown，用 divisions.json/tools.json 两份清单和一对 Shell 脚本把它们装进 17 种编码工具，再用一个 Tauri 桌面应用补上 AI 工具缺失的包数据库。本文拆解它的三层结构与真实边界。"
---

## 这个仓库真正在维护什么

用 Claude Code、Cursor、Codex 这类自带 Agent 能力的工具时，一个常见的摩擦是：想让模型稳定扮演某个专家角色，每次开新会话都得在提示词里重新声明一遍人设。这套声明散落在个人配置里，没法 diff、review、复用。

`msitarzewski/agency-agents`（155,850 star / 25,142 forks / MIT，2026-10-03 读数）给出的解法是把"角色定义"当成可版本化的资产：一个 agent 一个 Markdown 文件，写清身份、使命、工作流、交付物和验收指标，放进各工具约定的目录，下次会话启动时自动生效。

但把它理解为"一堆提示词文件"会低估这个仓库。它的核心资产其实是三层，每层解决不同的问题：

| 层 | 载体 | 解决的问题 |
|---|---|---|
| 目录 | 18 个 division、约 267 个 agent Markdown | 角色内容本身，按部门组织 |
| 转换与安装 | `divisions.json` + `tools.json` + `scripts/convert.sh` / `install.sh` | 同一份角色文件翻译成 17 种工具各自的格式和路径 |
| 桌面 App | `agency-agents-app`（Tauri 2，三平台） | 追踪装了什么、装到哪、有没有被改坏 |

仓库主语言是 Shell 而不是 Markdown——`convert.sh` 和 `install.sh` 才是这个项目的工程核心。GitHub 主页上那 267 个角色文件是内容，两份 JSON 清单加一对脚本是机制，App 是机制之上的分发界面。

项目起源也在 README 里写明：它诞生于一个 Reddit 帖子和随后的数月迭代，如今贡献账号数以千计（GitHub contributors API 分页 98 页，2026-10-03 读数）。

## 一个真实 agent 文件长什么样

拿 `engineering/engineering-frontend-developer.md` 解剖。每个 agent 文件以一段 YAML frontmatter 开头：

```yaml
---
name: Frontend Developer
description: Expert frontend developer specializing in modern web technologies...
color: cyan
emoji: 🖥️
vibe: Builds responsive, accessible web apps with pixel-perfect precision.
---
```

`name` 和 `description` 不是装饰——Claude Code 靠这两个字段注册 subagent，缺了它们文件放了也白放。`color`、`emoji`、`vibe` 服务于 UI 展示和角色气质。

正文是固定骨架，从身份到验收大约 11 节：

- `## 🧠 Your Identity & Memory`——角色定位、性格、记忆设定
- `## 🎯 Your Core Mission`——按任务域拆分的使命清单
- `## 🚨 Critical Rules You Must Follow`——硬约束（性能优先、WCAG 2.1 AA 等）
- `## 📋 Your Technical Deliverables`——带完整代码示例的交付物
- `## 🔄 Your Workflow Process`——四步工作流（架构→开发→优化→测试）
- `## 📋 Your Deliverable Template`——输出文档模板
- 之后是沟通风格、学习与记忆、成功指标、进阶能力

这个写法和 prompt 编译类工具（DSPy 这类把提示词当程序优化的路线）是两个方向：它把可读性、可审计性放在第一位，不引入任何运行时——上下文窗口里多了这段 Markdown，模型就按人设走。代价同样清楚：角色语义没有类型系统，无法在代码层被引用和断言，人设是否被遵守只能靠人事后检查输出。

## 安装机制的底座：tools.json 与三种安装形态

多工具支持不是靠脚本里堆 if-else，而是靠根目录的 `tools.json` 声明式描述每个工具的"安装合同"：检测目录、目标路径模板、渲染格式、安装机制。CI 里的 `check-tools.sh` 会在 tools.json 与 install.sh/convert.sh 不一致时直接挂掉构建——清单即事实源，脚本只是执行者。`divisions.json` 同理，管着部门清单与目录的一致性。

按 tools.json（2026-10-03 版，17 个工具），安装机制分三种，这个区分对理解产物形态很关键：

| installKind | 工具 | 产物 |
|---|---|---|
| `per-agent`（一角色一文件） | Claude Code（`.md`→`~/.claude/agents/`）、Codex（`.toml`→`~/.codex/agents/`）、Cursor（`.mdc`→`.cursor/rules/`）、Kimi（YAML）、OpenClaw（每个角色三文件 `SOUL.md`+`AGENTS.md`+`IDENTITY.md`）、Antigravity/Gemini CLI/Osaurus/DeepSeek Harness（`SKILL.md`）等 | 角色可单独增删 |
| `roster`（全部角色合并一文件） | Aider（`CONVENTIONS.md`）、Windsurf（`.windsurfrules`） | 单文件索引，重装即整体重写 |
| `plugin`（构建产物，不可按角色渲染） | Hermes（lazy-router 插件） | 只能 CLI 安装，App 不渲染 |

scope 也有差异：Cursor、Windsurf、Aider 只支持项目级安装；Kimi、OpenClaw、Hermes、Osaurus 只支持用户级。同一份角色文件，落到不同工具里的"形态"完全不同——这就是转换层存在的理由。

有一个实用坑值得单独说：OpenCode 的运行时目前只能注册约 119 个 agent，超出的部分会被静默丢弃（上游 bug，README 有链接）。267 个角色全量装进 OpenCode 会无声失败。`install.sh --division` 装子集可以避开上限，选择超限时安装器会警告。

脚本用法（README 口径）：

```bash
./scripts/install.sh --tool claude-code --division engineering,security
./scripts/install.sh --tool cursor --agent frontend-developer,ui-designer
./scripts/install.sh --list teams                       # 每个团队的角色数
./scripts/install.sh --tool opencode --division engineering --dry-run
```

只想试一个角色，直接复制文件也行：`cp engineering/engineering-*.md ~/.claude/agents/`。注意文件名规则不完全统一——engineering、security 等部门带 division 前缀，specialized、game-development、spatial-computing 等部门用裸名（`resume-tailor.md`、`economy-designer.md`）。

## App 补的是哪块短板：一个缺失的包数据库

`msitarzewski/agency-agents-app`（626 star，MIT）表面上是"浏览目录、一键安装"，但 App README 把动机说得更准：**AI 编码工具之间没有共享的包数据库**——Claude Code 不知道你给 Cursor 装过什么，手动复制过的文件没有来源记录，升级后改没改坏无从知晓。App 用本地台账补上这个缺口。

具体机制：每次通过 App 安装都记录源文件 hash、渲染后 hash、工具、目标路径、scope 和项目路径；之后通过对账（reconciliation）把磁盘上的文件分类成五种状态——current（与源一致）、outdated（源已更新）、modified（被外部改过）、removed、foreign（非 App 写入）。Dashboard 会汇总"需要关注"的项。对在团队环境里维护多工具安装的人来说，这比"一键安装"本身更有价值。

App 的功能围绕四个面板组织：Agents（谁）、Tools（怎么装）、Teams（装哪些）、Projects（装到哪个项目）。Teams 取代了早期版本的 "Loadouts" 概念，Agentfile 导入导出保留。技术栈是 Tauri 2 + SvelteKit/Svelte 5 前端加 Rust 后端（目录、渲染器、台账、对账、更新器都在后端），无遥测、可完全离线跑，GitHub OAuth Device Flow 是可选功能。

发布形态：macOS 13+（签名+公证的 .dmg，Apple Silicon 与 Intel），Linux x86_64（.deb/.rpm/.AppImage），Windows x64 与 ARM64（.exe，尚未签名，SmartScreen 会拦）。macOS 侧 v0.2.0 起支持应用内自动更新。Homebrew 路径：

```bash
brew install --cask msitarzewski/agency-agents/agency-agents
```

**一个容易误读的边界**：脚本支持 17 种工具，App 能直接安装的只有其中 8 种（Claude Code、Codex、Gemini CLI、GitHub Copilot、Qwen Code、Cursor、opencode、Osaurus）——即 App 内置渲染器实现了字节级一致输出的那些。Antigravity、Aider、Windsurf、OpenClaw、Kimi 等 9 种在 App 的 Tools 面板里显示为"已识别"（灰色），要装还是得回命令行跑脚本。README 对此很坦诚：那些产物形态"需要更多 App 工作才能成为一等安装目标"。

## 一次真实部署：给五人初创装一支团队

把三层机制串起来走一遍。假设一个五人团队要给 MVP 项目配 AI 角色：

1. **选团队**。仓库的 `strategy/runbooks.json` 预置了 4 个按场景打包的团队：startup-mvp（18 个角色）、enterprise-feature（22）、marketing-campaign（14）、incident-response（10）。startup-mvp 里从产品、设计到工程的角色已经配好比例。
2. **导出清单**。按 README 给的方式从 runbook 提取角色 slug 列表到 `team.txt`。
3. **批量安装**。`./scripts/install.sh --tool claude-code --agents-file team.txt`——每个角色的 Markdown 渲染后落到 `~/.claude/agents/`。
4. **跨工具分发**。给用 Cursor 的同事装项目级副本（`.cursor/rules/*.mdc`），给跑 Aider 的CI脚本生成 `CONVENTIONS.md`。同一份源文件，三种工具三种产物。
5. **交给 App 维护**。此后上游目录更新（三个月里 engineering 从 33 个角色涨到 65 个），App 的对账机制会标出哪些本机安装已 outdated，一键升级；谁手滑改了 `~/.claude/agents/` 里的文件，modified 状态会直接暴露。

这个流程里，角色内容、格式转换、安装追踪各自由一层负责——这也是它和 LangChain/AutoGen 那类框架不冲突的原因：框架管运行时，这里管的是上下文资产的版本化与分发。你完全可以把角色 Markdown 作为 system prompt 接进任何编排框架。

## 三个月里的变化：从 16 个部门到 18 个

这篇文章首发于 2026 年 6 月 29 日，彼时仓库正发布桌面 App（当天的提交就是 App 公告）。三个月间有几个值得留意的变化：

- **部门 16 → 18**：新增 healthcare（临床证据、主权医疗系统等 3 个角色）和 research（文献综合）。注意根目录的 `strategy/` 不是部门——那里放的是 playbook 和 runbook，没有 agent frontmatter；`integrations/` 是脚本输出目录，也不算。
- **工具 14 → 17**：新增 Mistral Vibe、ZCode、DeepSeek Harness。
- **安装路径迁移**：Antigravity 从 `~/.gemini/antigravity/skills/` 移到 `~/.gemini/config/skills/`；Gemini CLI 从 extension 机制改为直接的 `~/.gemini/agents/*.md`。老教程里的路径已失效。
- **角色规模**：官方口径从"232 agents across 16 divisions"改为"230+ agents across every division"（不再维护精确数），目录实测约 267 个 Markdown。
- **star**：发表时约 12 万，现 15.6 万。README 描述里那句 "Reddit community ninjas" 是修辞——营销部门的实际角色名是 Reddit Community Builder。

## 采用顺序与边界

适合先上的团队：

- 多人使用 AI 编码工具、希望统一"AI 在每个人手里的人设"，而不是各自维护 prompt；
- 同时用多种工具（Claude Code + Cursor + Codex 混编），需要同一份角色落到不同格式；
- 想要沉淀评审、测试、文案这类协作角色，而不只是单兵 coding agent。

可以先等等的场景：

- 需要严格自动调度的多 agent 协作——它没有运行时，编排还得靠 LangGraph/AutoGen；
- 角色语义需要在代码层引用与断言——Markdown 没有类型系统；
- 与具体项目强耦合的编码规约——这些更适合放各工具原生支持的 `AGENTS.md`/规则文件，而不是通用角色库。

落地建议从最小路径开始：挑一个部门 `cp engineering/engineering-*.md ~/.claude/agents/`，跑一两周看角色是否真的改变输出质量；有效果再换 `install.sh` 扩大到多工具，最后才考虑 App——App 的价值在维护期，不在第一次安装。

## 链接

- 仓库：https://github.com/msitarzewski/agency-agents
- 桌面客户端：https://github.com/msitarzewski/agency-agents-app
- App 官网：https://agencyagents.app
- License：MIT（主仓库与 App 仓库均为 MIT）
