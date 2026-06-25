---
title: "PM Skills Marketplace 解读：68 个产品经理 Agent Skill + 42 个链式工作流 + 9 个插件"
date: "2026-06-25T21:05:13+08:00"
slug: "phuryn-pm-skills-product-management-agent-skills-guide"
description: "phuryn/pm-skills 是面向 PM 的 Claude Code / Codex Skills Marketplace，9 个插件覆盖 68 个 skill 和 42 个 command，从发现、策略、执行到发布与 AI 代码审核。本文拆解它的 skill/command/plugin 三层结构、9 插件边界与安装路径。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "PM", "Agent Skills", "产品管理", "MCP"]
---

# PM Skills Marketplace 解读：68 个产品经理 Agent Skill + 42 个链式工作流 + 9 个插件

`phuryn/pm-skills` 想做的事情在 Claude Code / Codex 生态里并不寻常——它要在一个"开发者向"的 Agent 工具市场里，做一个**专为产品经理（PM）**的 Skills Marketplace。截至 2026-06-25，这个 21,014 Stars、2,135 Forks、MIT License 的项目（创建于 2026-03-01）已经把"发现、策略、执行、市场研究、数据分析、GTM、市场增长、PM 工具箱、AI 代码审核" 9 大领域打包成 **9 个插件 / 68 个 skill / 42 个 command**，并通过 Claude Code 官方 marketplace 机制、Codex CLI 兼容、Claude Cowork 一键安装，让 PM 可以在自己的 AI 工具里直接用 Teresa Torres / Marty Cagan / Alberto Savoia 的产品管理框架。本文是一篇项目导读，文章会拆 PM Skills 的"skill / command / plugin"三层抽象、9 插件的领域边界、Claude Code / Codex / Cowork 三套安装路径、与 Claude Code / Cursor / OpenCode 的 skill 兼容关系，并讨论为什么产品经理需要一个"被框架约束"的 Agent 工具。

## 一、核心判断：PM Skills 的"框架嵌入"不是 prompt 套话，而是 skill-as-knowledge

PM Skills 的 README 第一段话划定了它的产品边界：

> Generic AI gives you text. PM Skills Marketplace gives you structure.
>
> Each skill encodes a proven PM framework — discovery, assumption mapping, prioritization, strategy — and walks you through it step by step. You get the rigor of Teresa Torres, Marty Cagan, and Alberto Savoia built into your daily workflow, not sitting on a bookshelf.

三个关键词决定了它和"普通 prompt 模板"或"PM checklist 文档"的根本差异：

- **skill encodes a framework**：每个 skill 不是"提示词模板"，而是一个完整的"PM 知识结构 + 引导流程"——把"机会解法树（Opportunity Solution Tree）"或"RICE 优先级"等方法论**内化到 skill 的工作流**里
- **walks you through it step by step**：AI 不是一次性给答案，而是分步骤引导 PM 走完框架——和"问 AI 帮我做个 RICE"完全不同
- **built into your daily workflow, not sitting on a bookshelf**：在 Claude Code / Cowork 里直接 `/discover`、`/strategy`、`/write-prd`，而不是 PM 自己"想起来才去看书"

这意味着 PM Skills 的目标不是"教 PM 用 AI"或"提供 PM 工具箱"，而是"把 PM 知识库嵌入到 PM 每天已经在用的 AI 工具里"。

## 二、系统地图：Skill / Command / Plugin 三层抽象

PM Skills 的代码组织是清晰的"三层抽象"：

```
┌────────────────────────────────────────────────────────────────┐
│  L3 Plugin（插件）                                               │
│    pm-product-discovery / pm-product-strategy / pm-execution    │
│    pm-market-research / pm-data-analytics / pm-go-to-market     │
│    pm-marketing-growth / pm-toolkit / pm-ai-shipping            │
│    ── 9 个插件，按 PM 工作流领域切分                            │
├────────────────────────────────────────────────────────────────┤
│  L2 Command（命令）                                              │
│    /discover /strategy /write-prd /plan-launch                  │
│    /sprint /interview /north-star /red-team-prd /ship-check     │
│    ── 42 个 command，一个 command = 一次端到端 PM 工作流        │
│    ── 一个 command 调用 1~4 个 skill                            │
├────────────────────────────────────────────────────────────────┤
│  L1 Skill（技能）                                                │
│    brainstorm-ideas / identify-assumptions / prioritize-...     │
│    product-strategy / startup-canvas / pricing-strategy         │
│    ── 68 个 skill，一个 skill = 一个 PM 框架 / 工作流步骤        │
│    ── 一些 skill 是"被动调用"（独立参考），一些是"主动命令"    │
├────────────────────────────────────────────────────────────────┤
│  L0 Universal Skill Format（SKILL.md）                          │
│    所有 skill 用同一 YAML 格式描述：name / description           │
│    Claude Code / Codex / Cursor / OpenCode / Gemini CLI 全部兼容│
└────────────────────────────────────────────────────────────────┘
```

下面逐层看每一层的关键判断。

## 三、L3 插件层：9 大领域切分

PM Skills 用 9 个插件把 PM 工作流切成 9 个领域：

| # | 插件 | 领域 | Skills | Commands | 核心场景 |
|---|---|---|---|---|---|
| 1 | `pm-product-discovery` | 产品发现 | 13 | 5 | 创意 / 实验 / 假设测试 / OST / 访谈 |
| 2 | `pm-product-strategy` | 产品策略 | 12 | 5 | 愿景 / 商业模式 / 定价 / 竞争分析 |
| 3 | `pm-execution` | 执行 | 16 | 11 | PRD / OKR / 路线图 / Sprint / 复盘 / Stakeholder |
| 4 | `pm-market-research` | 市场研究 | 7 | 3 | 用户画像 / 细分 / 旅程图 / 市场规模 / 竞品 |
| 5 | `pm-data-analytics` | 数据分析 | 3 | 3 | SQL / 队列分析 / A/B 测试 |
| 6 | `pm-go-to-market` | GTM | 6 | 3 | Beachhead / ICP / 增长循环 / GTM / Battlecard |
| 7 | `pm-marketing-growth` | 营销增长 | 5 | 2 | 营销创意 / 定位 / 价值主张 / 命名 / North Star |
| 8 | `pm-toolkit` | PM 工具箱 | 4 | 5 | 简历 / NDA / 隐私政策 / 校对 |
| 9 | `pm-ai-shipping` | AI 代码审核 | 2 | 5 | AI 代码 ship 包 / 文档 / 审计 |

**9 个插件的边界设计原则**：

- **按 PM 工作流阶段切分**：发现 → 策略 → 执行 → 增长 → GTM
- **按 PM 子专业切分**：市场研究 / 数据分析 / 营销增长
- **按"AI 时代 PM"扩展**：pm-ai-shipping（AI 写的代码怎么 ship）

注意 `pm-ai-shipping` 是 9 个里最"AI Native"的——它解决"AI agent 写代码快但没有'意图记录'"的问题。这是个**新问题**——传统 PM 不需要它，但 2026 年的 PM 在 vibe-coding 工作流里必须面对它。

## 四、L2 命令层：42 个 command 把"几步 skill"串成"端到端工作流"

Command 的本质是"几个 skill 的链式调用"——把一个 PM 工作流从"AI 知道 step 1、step 2、step 3"变成"AI 自动按顺序跑完"。

### 4.1 链式工作流示例

**`/discover` 完整工作流**：

```text
/discover AI-powered meeting summarizer for remote teams
  ↓
  Step 1: brainstorm-ideas-new  (多视角创意)
  ↓
  Step 2: identify-assumptions-new  (8 类风险假设识别)
  ↓
  Step 3: prioritize-assumptions  (Impact × Risk 矩阵排序)
  ↓
  Step 4: brainstorm-experiments-new  (Alberto Savoia 精益原型实验)
  ↓
  输出：完整产品发现文档
```

**`/ship-check` 完整工作流**：

```text
/ship-check the payments service
  ↓
  Step 1: document-app  (反向生成系统文档)
  ↓
  Step 2: shipping-artifacts  (生成 ship 包)
  ↓
  Step 3: security-audit-static  (静态安全审计)
  ↓
  Step 4: performance-audit-static  (静态性能审计)
  ↓
  Step 5: derive-tests  (测试覆盖映射)
  ↓
  输出：reviewer-ready shipping packet
```

### 4.2 command 间互相推荐

PM Skills 的 command 设计成"互相衔接"——`/discover` 完成后会推荐下一步 `/write-prd` 或 `/interview`，`/write-prd` 完成后会推荐 `/red-team-prd`，`/red-team-prd` 完成后会推荐 `/ship-check`。

这让 PM 的工作流变成"沿着 command 树走"——不用每次重新规划"下一步该干嘛"。

## 五、L1 技能层：68 个 skill 是"知识载体"

Skill 是 PM Skills 的"知识原子"——每个 skill 是一个独立的 PM 框架或工作流步骤。

### 5.1 Skill 的两种用法

- **被动调用（reference skill）**：一些 skill 是"参考类"——比如 `prioritization-frameworks`、`opportunity-solution-tree`、`product-strategy`。Claude 在需要时会自动加载，不需要显式调用。
- **主动命令（active skill）**：一些 skill 是"主动执行"——比如 `brainstorm-ideas`、`identify-assumptions`、`sql-queries`。需要 PM 显式触发或作为 command 的子步骤。

### 5.2 Skill 来源

PM Skills 的 68 个 skill 不是"作者拍脑袋"——它们来自经典 PM 框架：

- **Teresa Torres** — *Continuous Discovery Habits*（OST / 持续发现）
- **Marty Cagan** — *INSPIRED* / *TRANSFORMED*（产品领导力 / 数字化转型）
- **Alberto Savoia** — *The Right It*（精益原型 / pretotype）
- **Dan Olsen** — *Lean Product Playbook*（精益产品）
- **Roger L. Martin** — *Playing to Win*（战略选择）
- **Ash Maurya** — *Running Lean*（Lean Canvas）
- **Strategyzer** — *Business Model Generation* / *Value Proposition Design*
- **Christina Wodtke** — *Radical Focus*（OKR）
- **Anthony W. Ulwick** — *Jobs to Be Done*
- **Alistair Croll & Benjamin Yoskovitz** — *Lean Analytics*
- **Sean Ellis** — *Hacking Growth*
- **Maja Voje** — *Go-To-Market Strategist*

每个 skill 的 reference 一栏会标注"基于谁的方法论"——PM 看到来源就知道权威性。

## 六、安装路径：Claude Cowork / Claude Code / Codex / 其他

PM Skills 走"统一 skill 文件 + 多种安装方式"的策略。

### 6.1 Claude Cowork（推荐非开发者）

1. 打开 **Customize**（左下角）
2. 进入 **Browse plugins** → **Personal** → **+**
3. 选择 **Add marketplace from GitHub**
4. 输入：`phuryn/pm-skills`

9 个插件全部自动安装——commands（`/discover`、`/strategy` 等）和 skills 都可用。

### 6.2 Claude Code（CLI）

```bash
# Step 1: 添加 marketplace
claude plugin marketplace add phuryn/pm-skills

# Step 2: 安装具体插件
claude plugin install pm-toolkit@pm-skills
claude plugin install pm-product-strategy@pm-skills
claude plugin install pm-product-discovery@pm-skills
claude plugin install pm-market-research@pm-skills
claude plugin install pm-data-analytics@pm-skills
claude plugin install pm-marketing-growth@pm-skills
claude plugin install pm-go-to-market@pm-skills
claude plugin install pm-execution@pm-skills
claude plugin install pm-ai-shipping@pm-skills
```

### 6.3 Codex CLI（OpenAI）

Codex 读取和 Claude Code 同一个 plugin marketplace 文件，无需转换：

```bash
# Step 1: 添加 marketplace
codex plugin marketplace add phuryn/pm-skills

# Step 2: 安装具体插件
codex plugin add pm-toolkit@pm-skills
...
```

**Codex 与 Claude Code 的差异**：
- Skills 可用（自动加载或显式调用）
- `/discover` 等 slash command **不可用**（Codex 插件不暴露 command）
- 替代方式：让 Codex 用自然语言描述工作流——比如"用产品发现流程处理 [你的想法]：先 brainstorm，再 map assumptions，再 prioritize，最后 design experiments，**每步之间暂停**"
- 进阶：让 Codex 把 command 文件转成 native Codex skill

### 6.4 其他 AI 工具（skill 兼容）

PM Skills 的 `skills/*/SKILL.md` 文件遵循 universal skill format——任何读取这个格式的工具都能用：

| 工具 | 用法 |
|---|---|
| **Gemini CLI** | 复制 skill 文件夹到 `.gemini/skills/` |
| **OpenCode** | 复制 skill 文件夹到 `.opencode/skills/` |
| **Cursor** | 复制 skill 文件夹到 `.cursor/skills/` |
| **Kiro** | 复制 skill 文件夹到 `.kiro/skills/` |

例如把全部 skills 装到 OpenCode：

```bash
for plugin in pm-*/; do
  mkdir -p .opencode/skills/
  cp -r "$plugin/skills/"* .opencode/skills/ 2>/dev/null
done
```

注意：**只有 skills 跨工具兼容，commands 是 Claude Code 专用**。

## 七、9 个插件的代表性 skill 速览

### 7.1 `pm-product-discovery`（13 skills / 5 commands）

- `brainstorm-ideas-existing` / `brainstorm-ideas-new`：多视角创意（PM / 设计师 / 工程师）
- `identify-assumptions-existing` / `-new`：识别假设（4 类 / 8 类风险）
- `prioritize-assumptions`：Impact × Risk 矩阵排序
- `opportunity-solution-tree`：Teresa Torres OST（outcome → opportunities → solutions → experiments）
- `interview-script` / `summarize-interview`：用户访谈脚本 + 总结
- `/discover` / `/brainstorm` / `/triage-requests` / `/interview` / `/setup-metrics`

### 7.2 `pm-product-strategy`（12 skills / 5 commands）

- `product-strategy`：9 段 Product Strategy Canvas
- `startup-canvas`：Startup Canvas（产品策略 + 商业模式）
- `value-proposition`：6 段 JTBD（Jobs To Be Done）价值主张
- `lean-canvas` / `business-model`：精益 / 商业模式画布
- `monetization-strategy` / `pricing-strategy`：变现 + 定价
- `swot-analysis` / `pestle-analysis` / `porters-five-forces` / `ansoff-matrix`：战略分析工具集
- `/strategy` / `/business-model` / `/value-proposition` / `/market-scan` / `/pricing`

### 7.3 `pm-execution`（16 skills / 11 commands）

- `create-prd`：8 段 PRD 模板
- `brainstorm-okrs` / `outcome-roadmap`：OKR + 成果路线图
- `sprint-plan` / `retro` / `release-notes`：Sprint 生命周期
- `pre-mortem`：Tiger / Paper Tigers / Elephants 风险分类
- `stakeholder-map`：Power × Interest 矩阵
- `user-stories` / `job-stories` / `wwas`：需求拆解
- `prioritization-frameworks`：9 种优先级框架参考
- `strategy-red-team`：对抗式压力测试
- `/write-prd` / `/plan-okrs` / `/transform-roadmap` / `/sprint` / `/pre-mortem` / `/red-team-prd` / `/meeting-notes` / `/stakeholder-map` / `/write-stories` / `/test-scenarios` / `/generate-data`

### 7.4 `pm-ai-shipping`（2 skills / 5 commands）—— 9 个里最 AI Native

- `shipping-artifacts`：核心 + 条件 ship 文档集（架构、用户/权限流、权限、变量/密钥、测试覆盖映射）
- `intended-vs-implemented`：找"文档说做什么 vs 代码实际做什么"的 gap
- `/ship-check` / `/document-app` / `/derive-tests` / `/security-audit-static` / `/performance-audit-static`

## 八、与 PM Brain / burnstop / claude-usage 的协作

PM Skills 是 PM Compass 生态的一部分：

- **[PM Brain](https://github.com/phuryn/pm-brain)**：本地 markdown 文件夹的"PM 第二大脑"——Claude 读它、写到它、每周自动整理
- **[burnstop](https://github.com/phuryn/burnstop)**：Claude 用量跟踪 + 避免 burn（限流）
- **[claude-usage](https://github.com/phuryn/claude-usage)**：Claude API 用量分析

PM Skills = "PM 工作流的 skill 库"
PM Brain = "PM 个人记忆 / 上下文"
burnstop = "避免 rate limit / 用量超限"
claude-usage = "用量分析"

四者组合起来给 PM 一个"AI 时代 PM 工作流"。

## 九、与 ad-hoc prompt 模板的取舍对比

| 维度 | PM Skills | ad-hoc prompt 模板 | 普通 PM checklist 文档 |
|---|---|---|---|
| **框架权威性** | Teresa Torres / Marty Cagan / Alberto Savoia 等 | 自己写 | 自己写 |
| **流程结构** | 多步引导，每步暂停 | 一次性给答案 | 静态文档 |
| **AI 工具集成** | Claude Code / Cowork / Codex 全部支持 | 任意 prompt | 不在 AI 工具里 |
| **可重复使用** | ✅（marketplace 机制） | ❌（散落各处） | ❌ |
| **可分享** | ✅（PM 团队装同一份） | ❌ | 静态文件 |
| **可审计** | ✅（skill 文件本身可审） | ❌ | ❌ |
| **可扩展** | ✅（自己写新 skill 提交 PR） | ❌ | ❌ |

## 十、当前版本的硬约束

截至 2026-06-25 的版本（持续更新），硬约束包括：

- **Codex 无 slash command**：Codex 插件不暴露 `/discover` 等 command——必须用自然语言描述工作流
- **Claude Code marketplace 格式**：当前依赖 Claude Code 0.2.x 以上的 plugin marketplace 协议，未来协议变化可能需要适配
- **Windows Cowork 不稳定**：已知问题（`claude-code/issues/27010`）——`CoworkVMService` 经常挂掉，README 给了 PowerShell 脚本救活 90% 场景
- **Skill 不是 100% 通用**：一些 skill 依赖 Claude Code 的工具调用 / 资源管理机制，移植到其他 AI 工具可能行为不完全一致
- **依赖 PM 自己**：`/discover` 是"引导 PM 走完流程"，不是"AI 自己完成产品发现"——最终判断仍要 PM 自己做
- **框架来源只到 2024**：新方法论（如 AI Native PM 框架）可能没覆盖

## 十一、快速上手路径

### 11.1 第一次接触

1. 装 Claude Code 或 Cowork
2. 添加 marketplace：`phuryn/pm-skills`
3. 试 `/discover` + 一个具体想法（"AI-powered meeting summarizer"）
4. 试 `/strategy` + 一个具体场景（"B2B project management tool for agencies"）
5. 试 `/write-prd` + 一个具体功能（"Smart notification system"）

### 11.2 第一次给团队装

1. Cowork 用户：一人装，团队成员走相同路径
2. Claude Code 用户：把 marketplace 加入脚本，新成员 `git pull` + `claude plugin install` 即可
3. 写一个 `TEAM-AGENTS.md`，列 PM Skills 的 9 个插件 + 团队最常用的 5 个 command

### 11.3 第一次扩展

1. 找一个内部 PM 模板（比如你们公司的 PRD 模板）作为新 skill
2. 按 `skills/*/SKILL.md` 格式写一份
3. `git clone` + `cp` 到 `pm-*/skills/` 目录
4. PR 到 upstream 仓库

## 十二、这篇文章没覆盖什么

- **每个 skill 的具体模板 / 提问清单**：68 个 skill 全部展开太大，README 里有完整列表
- **PM Brain 的具体配置**：第二个项目
- **burnstop / claude-usage 的具体使用**：第三 / 四个项目
- **实际跑 9 插件的 case study**：建议读者自己跑 `/discover` 体验
- **PM Skills 与 Linear / Notion / Jira 的具体集成**：当前主要通过 slash command，不深度集成项目管理工具

## 十三、采用建议

### 13.1 什么 PM 该用 PM Skills

- **每天用 AI 写文档的 PM**：把"AI 写"升级为"AI 引导 + 你判断"
- **需要"框架约束"的 PM**：自己 prompt 太发散，需要 OST / RICE / 优先级框架约束
- **想用 PM 框架但不想读 12 本书的 PM**：skill 把框架简化成引导流程
- **AI Coding 团队的 PM**：pm-ai-shipping 直接把 vibe-coded 项目的 ship 流程跑起来
- **跨职能协作 PM**：和其他 PM 共享同一份 skill 库，大家说同一种话

### 13.2 什么 PM 暂时不用

- **只需要"快速生成 PRD"**：ad-hoc prompt 够用
- **AI 工具是 Notion AI / ChatGPT 而非 Claude Code / Codex**：当前生态不覆盖
- **PM 流程已经非常稳定**：自己写 prompt 模板更顺手
- **预算不到位的 PM 团队**：每人 Cowork 订阅费用需要评估

## 十四、总结

PM Skills 的真正价值不是"给 PM 装了一堆 prompt"，而是它把"PM 方法论"和"AI 工具"和"工作流"三件事**合并成了一个 marketplace**。PM 不再需要"想起 OST 时去翻书"或"问 AI 帮忙 RICE"——直接 `/discover` 或 `/write-prd`，框架就内嵌在 skill 里。

挑 PM Skills 的核心问题只有一个：**你愿意让 AI"按框架引导你"而不是"按你的 prompt 自由发挥"吗？** 答案是 Yes，PM Skills 就是答案；答案是 No，ad-hoc prompt 模板仍然是更顺手的工具。
