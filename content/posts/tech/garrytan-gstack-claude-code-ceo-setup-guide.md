---
title: "garrytan/gstack：把 Claude Code 变成一支虚拟工程团队的 23 个角色"
date: "2026-06-26T18:07:05+08:00"
slug: "garrytan-gstack-claude-code-ceo-setup-guide"
description: "gstack 是 Garry Tan（YC CEO）公开的 Claude Code 配置库，核心是 23 个角色化 Skill + 8 个跨域 Power Tool，把 Think→Plan→Build→Review→Test→Ship→Reflect 的一套 sprint 流程固化成可执行命令，同时支持 10 款 AI 编码 Agent 与 OpenClaw 调度。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "AI Agent", "AI编程", "gstack", "工作流"]
---

[Y Combinator](https://www.ycombinator.com/) 总裁 Garry Tan 在 2026 年 3 月把一份用了 60 天、跑出 3 个生产服务 + 40 余个功能的 Claude Code 个人配置开源为 [garrytan/gstack](https://github.com/garrytan/gstack)。这不是又一份「prompt 集合」，而是一套把 **AI 编码 Agent 当作虚拟工程团队**来用的方法论固化产物：23 个角色化 Skill 排成 7 步 sprint，8 个跨域 Power Tool 覆盖安全、文档、第二意见与浏览器交互，所有能力都以斜杠命令形式挂在 Claude Code 上，单人即可同时跑 10-15 条并行 sprint。

本文先拆 sprint 七阶段与 23 角色的对应关系，再讲 8 个 Power Tool 与跨 Agent 适配机制，最后给出安装路径、真实任务流案例和适用边界。

## 学习目标

读完后你应当能够：

1. 说清 gstack 的核心设计：sprint 阶段、角色化 Skill、跨域 Power Tool 三层如何联动
2. 描述一个完整任务如何从 `/office-hours` 走到 `/ship`，在每个阶段被哪一个 Skill 接管
3. 区分 23 个核心 Skill 各自对应的「虚拟专家」职责与适用阶段
4. 解释 gstack 适配 10 款 AI 编码 Agent 与 OpenClaw 调用的工程机制
5. 在自己的项目中规划 gstack 的安装、团队模式与回退路径

## 目录

- [总览：把 Agent 当团队用的三层结构](#总览把-agent-当团队用的三层结构)
- [核心判断：sprint 阶段、角色化 Skill、跨域 Power Tool](#核心判断sprint-阶段角色化-skill跨域-power-tool)
- [系统地图：sprint 七阶段与 23 角色](#系统地图sprint-七阶段与-23-角色)
- [关键机制：每个 Skill 解决哪类失败模式](#关键机制每个-skill-解决哪类失败模式)
- [跨域 Power Tool：安全、文档、第二意见、浏览器、iOS QA](#跨域-power-tool安全文档第二意见浏览器ios-qa)
- [跨 Agent 适配与 OpenClaw 调度](#跨-agent-适配与-openclaw-调度)
- [任务流案例：从「想做个每日简报 App」到 PR](#任务流案例从想做个每日简报-app到-pr)
- [安装与配置](#安装与配置)
- [与其他 Claude Code 工具的关系](#与其他-claude-code-工具的关系)
- [并行 Sprint：单兵变 10-15 人团队](#并行-sprint单兵变-10-15-人团队)
- [适用边界与已知限制](#适用边界与已知限制)
- [采用建议](#采用建议)
- [FAQ](#faq)
- [自测题](#自测题)
- [进阶路径](#进阶路径)

> 说明：本文所有 Skill 名称、安装命令、统计数字、版本号均来自 [garrytan/gstack](https://github.com/garrytan/gstack) 仓库的 `README.md`、`CLAUDE.md` 与 `VERSION` 文件（截至 v1.58.5.0，2026-06-25）。Stars/Forks 等会随时间漂移的数字以抓取瞬间为准。

## 总览：把 Agent 当团队用的三层结构

gstack 的目录里有 90+ 个一级目录和 200+ 个 Skill 文件，肉眼看上去很容易把它当成「Skill 大杂烩」。但它其实只有三层：

```text
gstack
├── Sprint 阶段（流程骨架）
│   └── Think → Plan → Build → Review → Test → Ship → Reflect
├── 角色化 Skill（虚拟专家）
│   └── 23 个 /office-hours, /plan-ceo-review, /plan-eng-review, /plan-design-review,
│       /design-consultation, /design-shotgun, /design-html, /review, /investigate,
│       /design-review, /devex-review, /qa, /qa-only, /pair-agent, /cso, /ship,
│       /land-and-deploy, /canary, /benchmark, /document-release, /document-generate,
│       /retro, /browse
├── 跨域 Power Tool（横向能力）
│   └── /codex, /careful, /freeze, /guard, /unfreeze, /open-gstack-browser,
│       /setup-deploy, /setup-gbrain, /sync-gbrain, /gstack-upgrade
└── 跨 Agent 适配层
    └── setup --host {claude,codex,opencode,cursor,factory,slate,kiro,hermes,gbrain}
```

「sprint 阶段」是流程骨架，规定每一步的输入输出；「角色化 Skill」是虚拟专家，对应 sprint 阶段里的具体职责；「跨域 Power Tool」是横切能力，可以在任意阶段被调用——比如 `/careful` 在 build 阶段挡掉 `rm -rf`，`/cso` 在 review 阶段跑 OWASP 审计。

## 核心判断：sprint 阶段、角色化 Skill、跨域 Power Tool

gstack 的核心判断可以一句话概括：

> **个人 AI 编码的瓶颈不是模型能力，而是缺乏工程团队的多人协作纪律。把团队的角色分工、阶段交接、跨域工具写成斜杠命令，让单人也能跑出多人的工程节奏。**

围绕这个判断，三个设计选择值得专门指出：

1. **Skill 是 Markdown，不是 Python**。所有 23 个 Skill 本质上是结构化的 `SKILL.md` 提示词，setup 脚本把它们 symlink 到 `~/.claude/skills/`（或目标 Agent 的对应目录）。这种「Skill = 文件 = 命令」的设计，让 fork 即定制成为可能。
2. **每个 Skill 对应一个真实工程角色**。`/plan-ceo-review` 是 CEO，`/plan-eng-review` 是工程经理，`/plan-design-review` 是资深设计师，`/cso` 是首席安全官，`/qa` 是 QA 主管。命名强迫 Agent 切换心智模型，而不是继续沿用「万能助手」的角色。
3. **sprint 阶段让 Skill 形成流水线**。`/office-hours` 写出来的设计文档会被 `/plan-ceo-review` 读，`/plan-eng-review` 写出来的测试计划会被 `/qa` 接住，`/review` 抓出的 bug 会被 `/ship` 验证修复。Skill 之间通过文件传递上下文，而不是靠对话窗口里的聊天历史。

这个判断区别于大多数「Claude Code 配置」仓库：后者通常只优化 prompt 模板、或者只做几个常用快捷命令；gstack 试图把整个工程生命周期搬进 Agent 的命令面板。

## 系统地图：sprint 七阶段与 23 角色

下表把 sprint 七阶段、对应 Skill、虚拟专家角色和「输入 / 输出」一次性铺开，是后续详读的总览：

| Sprint 阶段 | 对应 Skill | 虚拟专家 | 输入 | 输出 |
|------------|-----------|---------|------|------|
| **Think** | `/office-hours` | YC Office Hours | 用户痛点描述 | 设计文档（自动喂给下游） |
| **Plan** | `/plan-ceo-review`、`/plan-ceo-review` 的 4 种 scope 模式 | CEO / Founder | 设计文档 | CEO 视角 10-section 审阅 |
| **Plan** | `/plan-eng-review` | 工程经理 | 设计文档 | 数据流图、状态机、测试矩阵 |
| **Plan** | `/plan-design-review` | 资深设计师 | 设计文档 | 0-10 分设计评估 + AI Slop 检测 |
| **Plan** | `/plan-devex-review` | DX Lead | 设计文档 | 20-45 道 DX 强制问题 |
| **Plan** | `/design-consultation`、`/design-shotgun`、`/design-html` | 设计合作伙伴 | 模糊设计意图 | 完整设计系统 + 4-6 套 mockup 变体 + 生产级 HTML |
| **Build** | （直接写代码） | 工程团队 | 已批准计划 | 工作树变更 |
| **Build** | `/investigate` | Debugger | 故障报告 | 根因 + 3 次修复尝试上限 |
| **Review** | `/review` | Staff Engineer | diff | 自动修复 + ASK 标记 |
| **Review** | `/design-review` | 会写代码的设计师 | diff | 原子提交 + 前后截图 |
| **Review** | `/devex-review` | DX 测试员 | dev 环境 | TTHW 计时 + 真实截图 |
| **Review** | `/cso` | 首席安全官 | 仓库 | OWASP Top 10 + STRIDE |
| **Test** | `/qa`、`/qa-only` | QA 主管 | staging URL | bug 列表 + 原子修复 + 回归测试 |
| **Ship** | `/ship` | 发布工程师 | 分支 | 测试 + PR |
| **Ship** | `/land-and-deploy` | 发布工程师 | 已批准 PR | merge + CI + 生产验证 |
| **Ship** | `/canary` | SRE | 生产环境 | 控制台错误 + 性能回归监控 |
| **Ship** | `/benchmark` | 性能工程师 | staging | 页面加载 + Core Web Vitals |
| **Reflect** | `/retro` | 工程经理 | 一周 git 活动 | 团队级 retro + 改进项 |
| **Reflect** | `/retro global` | 工程经理 | 跨项目数据 | 跨工具对比 |
| **Document** | `/document-release`、`/document-generate` | 技术文档作者 | diff | 同步更新所有过期文档 + Diataxis 覆盖图 |
| **Memory** | `/learn` | 长期记忆 | 任意阶段 | 跨会话学习的项目级模式库 |
| **Cross** | `/browse`、`/open-gstack-browser`、`/setup-browser-cookies` | QA 工程师 | URL | 真实浏览器截图 + 点击 |
| **Cross** | `/spec` | Spec 撰写人 | 模糊意图 | 5 阶段可执行 spec |
| **Cross** | `/autoplan` | 评审流水线 | 设计文档 | CEO→design→eng 一次性串起来 |

关键观察：**Plan 阶段最重**——一个产品决策要先后过 CEO、工程经理、设计师、DX Lead 四道闸门；**Build 阶段反而最轻**——Agent 直接写代码，没有专门的「写代码 Skill」；**Document/Memory 阶段横切**——`/document-release` 会在 `/ship` 末尾自动被调用，文档保持同步。

## 关键机制：每个 Skill 解决哪类失败模式

23 个 Skill 不是平铺的 feature list，每个都瞄准一种具体的 AI 编码失败模式。下表挑出最值得理解的几个：

### `/office-hours`：把「我想做 X」重写成「X 真正在解决的问题」

触发条件：用户说「我想做一个 XX」。

机制：先抛 6 道强制问题（具体例子而非假设、最近一次痛点、为什么是现在、谁付钱、什么算成功、什么算失败），把模糊需求转成结构化问题列表。然后**主动 push back**——如果你说「每日简报 App」，它会反问「你描述的其实是私人 chief of staff AI，为什么要做成 App？」。

输入：用户的痛点叙述。
输出：设计文档（自动写盘 + 喂给下游 Skill）。

为什么需要：普通 Agent 默认是「接收字面需求然后写代码」，结果就是造出没人要的 App。`/office-hours` 把「重写需求」当作独立阶段，强制把模糊度降到下游能接住的水平。

### `/plan-ceo-review`：四种 scope 模式强制对抗 scope creep

触发条件：`/office-hours` 写完设计文档之后。

机制：CEO 视角跑 10-section 审阅，最关键的是它暴露了 4 种 scope 模式：Expansion（扩大）、Selective Expansion（选择性扩大）、Hold Scope（守住）、Reduction（缩减）。每种都强迫 Agent 给一个明确推荐，而不是把「先做 MVP」当成万能逃逸。

输入：设计文档。
输出：CEO 视角的审阅意见 + scope 推荐。

### `/plan-eng-review`：把假设、状态机、错误路径 ASCII 画出来

触发条件：架构决策点。

机制：工程经理视角，强制产出 ASCII 数据流图、状态机、错误路径、测试矩阵。`ARCHITECTURE.md` 的文档结构就是这一阶段的产物模板。

输入：架构决策。
输出：可审计的架构草图 + 风险点清单。

### `/review`：把「CI 通过 ≠ 生产 OK」自动化

触发条件：任何带 diff 的分支。

机制：Staff Engineer 视角，先自动修复明显的 typo / lint / 简单 bug（标记 `[AUTO-FIXED]`），剩下的复杂度问题用 `[ASK]` 标记把决策权交回给用户。它不追求「找到所有 bug」，追求「找到 CI 漏掉的那种 bug」。

输入：git diff。
输出：自动修复 + 决策清单。

### `/qa`：让 Agent 真正「看见」Web 错误

触发条件：staging URL。

机制：QA 主管视角，**打开真实浏览器**（不是 headless phantom），点击用户路径、抓控制台错误、截屏证据，然后对每个 bug 跑「修复 + 自动写回归测试 + 验证修复」的闭环。`/qa-only` 是只报告不修的姊妹命令。

输入：URL。
输出：bug 列表 + 原子 commit + 回归测试。

### `/ship`：从分支到 PR 的一键流水线

触发条件：分支上有改动的 commit。

机制：发布工程师视角，自动 sync main、跑测试、审计覆盖率、推送、开 PR。如果项目没有测试框架，`/ship` 会先 bootstrap 一个（vitest / pytest / jest 任选）。

输入：git 分支。
输出：PR URL。

### `/retro`：把 git log 翻译成团队对话

触发条件：周末或冲刺结束。

机制：聚合本周的 commit 频率、PR 节奏、测试健康度，按贡献者拆分（`/retro` 是当前项目，`/retro global` 跨项目），生成「这周谁在拉胯、下周重点是什么」式的周报。

输入：git log + GitHub API。
输出：结构化周报。

### 失败模式覆盖：与 Karpathy 4 条原则的对应

[Andrej Karpathy](https://github.com/forrestchang/andrej-karpathy-skills) 公开过 AI 编码的 4 类典型失败：wrong assumptions（盲目假设）、overcomplexity（过度复杂）、orthogonal edits（正交修改）、imperative over declarative（命令式而非目标式）。gstack 的 7 阶段流水线**结构化地对抗**了所有四类：

- 盲目假设 → `/office-hours` 强制 6 道题、`/plan-eng-review` 强制把假设画成状态机
- 过度复杂 → `/review` 的 `[AUTO-FIXED]` 自动收敛简单问题、`/plan-ceo-review` 的 Reduction 模式
- 正交修改 → `/careful` 警告 + `/freeze` 锁定编辑目录
- 命令式 → `/ship` 把任务翻译成可验证目标，测试先于合并

## 跨域 Power Tool：安全、文档、第二意见、浏览器、iOS QA

8 个 Power Tool 不属于任何 sprint 阶段，可以从任意阶段被调用。

### `/cso`：把 OWASP + STRIDE 跑成可读清单

OWASP Top 10 + STRIDE 威胁建模是行业标准，但普通 Agent 大概率会输出一堆假阳性（每个 framework 都有这种问题）。`/cso` 的关键设计是**零噪音**：内置 17 个已知假阳性排除规则、8/10 置信度门控、独立发现验证（一个发现被两轮独立审计都标记才确认）。每条发现都附「具体可复现的 exploit 场景」，而不是泛泛说「存在 XSS 风险」。

### `/codex`：让 OpenAI Codex 给出独立第二意见

三种模式：review（pass/fail 闸门）、adversarial challenge（主动尝试破坏）、open consultation（带 session continuity 的咨询）。当 `/review`（Claude）和 `/codex`（OpenAI）都跑过同一分支时，gstack 输出**跨模型分析**：哪些发现两个模型都同意（高置信）、哪些只在一个模型出现（可能是单边盲点）。

### `/careful` + `/freeze` + `/guard`：三档安全护栏

- `/careful`：在执行任何破坏性命令前（`rm -rf`、`DROP TABLE`、`git push --force`、`git reset --hard`）弹警告，用户口头说「be careful」激活，可以临时 override。
- `/freeze`：把编辑锁在某个目录内，调试时防止 Agent 顺手「修复」无关代码。
- `/guard`：`/careful` + `/freeze` 同时激活，prod 环境工作的最大安全档。

### `/browse` + `/open-gstack-browser`：让 Agent 真正看见 Web

`/browse` 提供 ~100ms/命令的 fast headless 浏览器（基于 Playwright），用于 QA、自动化抓取。`/open-gstack-browser` 进一步启动带侧边栏的 GStack Browser 进程：抗反爬隐身（Layer C stealth）、自动模型路由（Sonnet 跑点击、Opus 跑分析）、一键 cookie 导入、子 Claude 代理（侧边栏输入自然语言就能让子 Claude 执行）。

浏览器还有 4 个**域级能力**：

- `$B domain-skill save`——把"LinkedIn Apply 按钮在 iframe 里"这种 site-specific 经验写进 per-domain 文件，下次自动应用（quarantined → 3 次成功转 active → 可提升为 global）。
- `$B cdp <Domain.method>`——raw Chrome DevTools Protocol 逃生口，deny-default：方法必须显式加入 `browse/src/cdp-allowlist.ts` 才允许调用。
- `$B handoff` / `$B resume`——AI 卡在 CAPTCHA / MFA / 登录墙时，开一个带 cookie 的可见 Chrome 给用户手动解决，结束 `$B resume` 接续。
- `/pair-agent`——把同一个浏览器共享给另一个 AI Agent（OpenClaw、Hermes、Codex、Cursor），通过 one-time setup key + scoped token，每个 Agent 独立 tab、互不干扰。

### `/setup-gbrain` + `/sync-gbrain`：给 Agent 装一个真·长期记忆

[GBrain](https://github.com/garrytan/gbrain) 是 gstack 的姊妹项目，本质是给 AI Agent 用的持久化知识库（Supabase 后端 + PGLite 本地两种模式）。`/setup-gbrain` 把 GBrain 装好 + 注册为 MCP server；`/sync-gbrain` 把当前 repo 的代码重新索引到 GBrain，并在 `CLAUDE.md` 写一段 `## GBrain Search Guidance`，让 Agent 优先调 `gbrain search` / `code-def` / `code-refs` 而不是原生 Grep。

### `/ios-qa` + 4 个 iOS 专项 Skill：USB CoreDevice 驱动真机

v1.43.0.0+ 的 `/ios-qa` 通过嵌入式 `StateServer` 驱动 USB 连接的 iPhone，读 Swift 源、生成类型化 `@Observable` 访问器、跑 agent loop。`--tailnet` 标志可以把设备暴露给 Tailscale 上的远程 Agent 跑 QA，本机不碰硬件。配套有 4 个 `/ios-*` Skill：bug-fix、HIG 设计审查、debug-bridge 清理、accessor 同步。

### `/document-release` + `/document-generate`：文档不再腐烂

`/document-release` 读项目里所有 doc 文件、交叉对比 diff、更新漂移的段落（README、ARCHITECTURE、CONTRIBUTING、CLAUDE.md、TODOS），输出 Diataxis 框架下的覆盖图（reference / how-to / tutorial / explanation 四象限），让文档缺口在 PR body 里直接可见。`/ship` 会**自动调用**它，所以「文档同步」是 shipping 的最后一步而不是可选项。`/document-generate` 是从零补缺版本的姊妹命令。

### `/spec`：5 阶段 spec 撰写 + Codex 质量门

5 阶段（why、scope、technical with mandatory code-reading、draft、file），Codex 给出 7/10 质量门禁（低于 7 不让 file），fail-closed 密钥脱敏，对照现有 issue 去重，spec 归档到 `$GSTACK_STATE_ROOT/projects/$SLUG/specs/`。`--execute` 标志在 fresh worktree 拉 `claude -p` 直接执行。

### 4 个原生 OpenClaw Skill（无需 Claude Code session）

通过 ClawHub 安装 4 个 conversational skill——`gstack-openclaw-office-hours`、`gstack-openclaw-ceo-review`、`gstack-openclaw-investigate`、`gstack-openclaw-retro`——直接在 OpenClaw chat 里用，不需要再 spawn Claude Code 会话。

## 跨 Agent 适配与 OpenClaw 调度

gstack 不绑定 Claude Code。`setup --host <name>` 适配 10 款 AI 编码 Agent：

| Agent | 标志 | 技能安装位置 |
|-------|------|-------------|
| OpenAI Codex CLI | `--host codex` | `~/.codex/skills/gstack-*/` |
| OpenCode | `--host opencode` | `~/.config/opencode/skills/gstack-*/` |
| Cursor | `--host cursor` | `~/.cursor/skills/gstack-*/` |
| Factory Droid | `--host factory` | `~/.factory/skills/gstack-*/` |
| Slate | `--host slate` | `~/.slate/skills/gstack-*/` |
| Kiro | `--host kiro` | `~/.kiro/skills/gstack-*/` |
| Hermes | `--host hermes` | `~/.hermes/skills/gstack-*/` |
| GBrain (mod) | `--host gbrain` | `~/.gbrain/skills/gstack-*/` |
| Claude Code | 默认 | `~/.claude/skills/gstack-*/` |

`docs/ADDING_A_HOST.md` 文档承诺「加一个新 Agent 只需一份 TypeScript config，零代码改动」。

### OpenClaw 调度约定

OpenClaw 通过 ACP 协议 spawn Claude Code 会话，所以 gstack skill 零配置即用。OpenClaw 端的 dispatch 约定：

- "Fix the typo in README" → 不走 gstack，spawn 普通 Claude Code 会话
- "Run a security audit on this repo" → spawn Claude Code + `Run /cso`
- "Build me a notifications feature" → spawn Claude Code + `/autoplan` → 实现 → `/ship`
- "Help me plan the v2 API redesign" → spawn Claude Code + `/office-hours` → `/autoplan`，**只保存 plan，不实现**

完整路由逻辑见 `docs/OPENCLAW.md`。

### Conductor 并发环境

[Conductor](https://conductor.build) 在每个 workspace 显式剥离 `ANTHROPIC_API_KEY` 和 `OPENAI_API_KEY`，导致 paid evals / gbrain embeddings 跑不起来。gstack 的解决是 `lib/conductor-env-shim.ts`（v1.39.2.0+）把 `GSTACK_ANTHROPIC_API_KEY` / `GSTACK_OPENAI_API_KEY` 在 gstack 入口提升为规范名。Conductor 用户需要在 workspace env 显式设这两个变量。

## 任务流案例：从「想做个每日简报 App」到 PR

README 里有完整对话 transcript，下面把关键节拍拆开来看：

```text
你:  我想做一个每日简报 App。
你:  /office-hours
Claude:
  [问痛点——具体例子不是假设]
  [从对话里提取 5 个你没意识到的能力]
  [质疑 4 个前提——你可以同意、不同意或调整]
  [生成 3 个实现方案 + 工作量评估]
  RECOMMENDATION: 先把最窄的 wedge 明天就发，从真实使用里学习。
  完整愿景是 3 个月项目——先把真正好用的每日简报做出来。
  [写设计文档 → 自动喂给下游 Skill]

你:  /plan-ceo-review
  [读设计文档，质疑 scope，跑 10-section 审阅]

你:  /plan-eng-review
  [ASCII 数据流、状态机、错误路径]
  [测试矩阵、失败模式、安全担忧]

你:  批准 plan。退出 plan mode。
  [11 个文件、2400 行代码。~8 分钟。]

你:  /review
  [AUTO-FIXED] 2 个问题。[ASK] 竞态条件 → 你批准修复。

你:  /qa https://staging.myapp.com
  [开真实浏览器，点过用户路径，发现并修了一个 bug]

你:  /ship
  测试: 42 → 51 (+9 new)。PR: github.com/you/app/pull/42
```

理解这段流程要看到三件事：

1. **「每天简报 App」被改写成「私人 chief of staff AI」**——`/office-hours` 没有照字面实现，而是先重新框定问题。
2. **8 个命令串起一个完整 sprint**——从需求重写到架构审阅到 PR，没有任何「接下来我该做什么」的人类决策点。
3. **9 个新测试是 `/qa` 自动生成的**——AI 不只是发现 bug，它为每个 bug 写回归测试，这是「vibe coding safe」和「yolo coding」的分水岭。

## 安装与配置

需求：[Claude Code](https://docs.anthropic.com/en/docs/claude-code)、Git、[Bun](https://bun.sh/) v1.0+、Windows 还需要 Node.js。

### 单机模式（30 秒）

打开 Claude Code，粘贴：

```text
Install gstack: run `git clone --single-branch --depth 1
https://github.com/garrytan/gstack.git ~/.claude/skills/gstack &&
cd ~/.claude/skills/gstack && ./setup`
```

setup 会在 `~/.claude/skills/` 下创建 symlink，并把一段「gstack section」追加到 `CLAUDE.md`（列出全部可用 Skill + 强制 Agent 用 `/browse` 而非 `mcp__claude-in-chrome__*`）。

### Team 模式（推荐）

仓库根目录粘贴：

```bash
(cd ~/.claude/skills/gstack && ./setup --team) && \
  ~/.claude/skills/gstack/bin/gstack-team-init required && \
  git add .claude/ CLAUDE.md && \
  git commit -m "require gstack for AI-assisted work"
```

效果：仓库里**不**落地 vendored 文件，teammate 拉下来第一次跑 Claude Code 时会自动 `git pull` 更新 gstack（节流到 1 次/小时，network-failure 安全）。把 `required` 换成 `optional` 表示软提示而不阻塞。

### 命令风格偏好

```bash
./setup --no-prefix   # /qa 而非 /gstack-qa（默认）
./setup --prefix      # /gstack-qa 而非 /qa（多 Skill 套件并用时建议）
```

### 升级

```bash
/gstack-upgrade
```

或在 `~/.gstack/config.yaml` 设 `auto_upgrade: true` 后自动升级。

### 卸载

```bash
~/.claude/skills/gstack/bin/gstack-uninstall
```

处理 skills、symlinks、`~/.gstack/`、browse daemons、临时文件。`--keep-state` 保留配置和 analytics，`--force` 跳过确认。

## 与其他 Claude Code 工具的关系

| 项目 | 主要定位 | 与 gstack 的差异 |
|------|---------|----------------|
| [Andrej Karpathy Skills](https://github.com/forrestchang/andrej-karpathy-skills) | 4 条原则 CLAUDE.md | 行为约束（instruction level），gstack 是 workflow 强制层 |
| 9arm / Agent Skills 类 | 单一 Skill 集 | 单点工具，gstack 提供跨 Skill 的 sprint 流水线 |
| 各 OpenClaw Skill | 通用技能 | 通用方法论，gstack 是 founder/CEO 视角的工程团队 |
| 各类 `/browse` 实现 | 浏览器自动化 | gstack 的 browse 是上层基础设施，包含 prompt-injection 防御 + pair-agent |

gstack 反复强调的卖点是「Karpathy 的 4 类失败模式已经被覆盖」——它把自己定位成 Karpathy Skills 的**执行层**而不是替代品。

## 并行 Sprint：单兵变 10-15 人团队

[Conductor](https://conductor.build) 在隔离 workspace 里并行跑多个 Claude Code 会话。Garry Tan 公开说他**日常跑 10-15 条并行 sprint**——

- 一条 `/office-hours` 跑新 idea
- 一条 `/review` 跑 PR
- 一条实现某个 feature
- 一条 `/qa` 跑 staging
- 其他 6 条在不同分支

「并行之所以能 work，是因为 sprint 结构本身提供了边界：每个 Agent 知道自己要做什么、什么时候停。」没有 sprint 流程的并行 10 个 Agent 等于 10 个混乱源。

### 语音输入

所有 Skill 都有 voice-friendly 触发短语，对接 AquaVoice / Whisper：「run a security check」→ `/cso`，「test the website」→ `/qa`。

## 适用边界与已知限制

gstack 不是万能的，下面这些场景**不建议**直接上 gstack：

1. **学习 / 教学场景**。学生刚学编程，需要的是「理解每一行」而不是「AI 帮我跑完 sprint」。gstack 假设你已经知道 sprint 应该长什么样。
2. **一次性脚本**。写个 30 行 Python 抓数据，setup 一套 gstack 反而是 overhead。`/office-hours` 的 6 道题在这种场景下是 noise。
3. **超大型 monorepo + 严苛合规**。gstack 默认 install 在 `~/.claude/skills/`，是用户级而非项目级。在金融、医疗这种需要审计的 monorepo，team 模式 + private registry 会更合适。
4. **不支持的 AI Agent**。`--host` 适配列表里的 10 个 Agent 是 v1.58.5.0 的覆盖范围，其他 Agent（如 Aider 类的 inline edit 工具）需要 `docs/ADDING_A_HOST.md` 的额外工作。
5. **prompt injection 防御**。`/open-gstack-browser` 带的 22MB ML classifier + Claude Haiku transcript check + canary token + 双分类器投票是「合理水平」而不是「绝对安全」。如果业务涉及对抗国家级对手，单独再叠一层。

### 已知摩擦点

- Conductor 环境下必须用 `GSTACK_*` 前缀 env（`ANTHROPIC_API_KEY` 会被 Conductor 剥掉）。
- Windows + MSYS2 / Git Bash 不开 Developer Mode 时，setup 退化为文件复制，`git pull` 后**必须**重跑 `./setup` 同步 skill。
- `/browse` 在 Windows 上会自动从 Bun 切到 Node.js（Bun 有 pipe transport bug，[oven-sh/bun#4253](https://github.com/oven-sh/bun/issues/4253)）。

## 采用建议

按风险递增的三档：

1. **试用（个人项目）**。在自己的 side project 跑 `--no-prefix` 单机模式，先用 `/office-hours` + `/plan-ceo-review` + `/ship` 三件套感受 sprint 节奏。2-3 个项目后再考虑扩展。
2. **团队采纳**。在团队仓库跑 `--team` + `required`，让新 contributor 自动拿到 gstack。配 `.gstack/config.yaml` 设 `auto_upgrade: true` 减少手动维护。
3. **生产化**。把 `/cso` 跑进 PR check（gate 评分 < 8/10 不让 merge），`/qa` 跑进 staging hook，`/document-release` 跑进 release pipeline。配合 `/sync-gbrain` 跨仓库 memory。

## FAQ

**Q：gstack 必须用 Claude Code 吗？**
A：不一定。`setup --host` 适配 10 款 Agent（Codex、OpenCode、Cursor、Factory、Slate、Kiro、Hermes、GBrain + 默认 Claude Code）。但 README 强调「其它 Agent 上 Skill 行为可能有细微差异，因为提示词是按 Claude Code 的 tool call 习惯写的」。

**Q：`/browse` 跟 Playwright / Puppeteer 有什么不同？**
A：`/browse` 是上层 Skill，底层是 Playwright + 自家 fast headless server（~100ms/命令）。它额外提供 `$B handoff`（人类接 CAPTCHA）、`$B cdp`（raw CDP 逃生口）、`/pair-agent`（跨 Agent 共享浏览器）。

**Q：gstack 是免费的吗？**
A：是。MIT license，没有 premium tier，没有 waitlist。

**Q：GBrain 是什么？必须用吗？**
A：GBrain 是 gstack 的姊妹项目——给 Agent 用的持久化知识库（Supabase + PGLite）。**不是**必须，但 `/setup-gbrain` 装上后 `/sync-gbrain` 可以让 Agent 跨会话累积项目级模式。

**Q：telemetry 默认开吗？**
A：默认**关**。第一次跑 gstack 会问要不要 share anonymous usage（Skill 名、耗时、success/fail、gstack 版本、OS）。代码、文件路径、repo 名、prompt 一律不收。schema 在 `supabase/migrations/`，可审计。`gstack-config set telemetry off` 随时关。

## 自测题

1. 把 sprint 七阶段按「Think → Plan → Build → Review → Test → Ship → Reflect」排出来，每个阶段列出至少 1 个对应 Skill。
2. `/office-hours` 的 4 个 scope 模式（Expansion、Selective Expansion、Hold Scope、Reduction）各自的适用场景是什么？
3. 解释 `/cso` 的「零噪音」设计：17 个假阳性排除规则、8/10 置信度门控、独立发现验证各自起什么作用？
4. 描述 `/codex` 三种模式（review / adversarial challenge / open consultation）以及跨模型分析如何产生。
5. 解释 Conductor 环境为什么必须用 `GSTACK_ANTHROPIC_API_KEY` 而不是 `ANTHROPIC_API_KEY`。

## 进阶路径

- 通读 [docs/skills.md](https://github.com/garrytan/gstack/blob/main/docs/skills.md) 拿到 23 个 Skill 的深度说明（含 Greptile 集成）
- 读 [ARCHITECTURE.md](https://github.com/garrytan/gstack/blob/main/ARCHITECTURE.md) 理解 system internals
- 读 [BROWSER.md](https://github.com/garrytan/gstack/blob/main/BROWSER.md) 拿到 `/browse` 的完整命令参考
- 读 [ETHOS.md](https://github.com/garrytan/gstack/blob/main/ETHOS.md) 体会 Garry Tan 的 builder philosophy（Boil the Ocean、Search Before Building、三层知识）
- 跑一次自己的 `/office-hours` → `/plan-ceo-review` → `/ship` 完整 sprint，把过程写到项目 README 里
