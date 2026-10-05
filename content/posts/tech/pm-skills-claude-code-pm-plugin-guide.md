---
title: "pm-skills：把 Teresa Torres / Marty Cagan / Alberto Savoia 的 PM 框架做成 AI 工作流，69 个 skill + 42 条命令"
date: "2026-06-09T17:59:00+08:00"
lastmod: "2026-10-03T00:00:00+08:00"
slug: "pm-skills-claude-code-pm-plugin"
github_repo: "phuryn/pm-skills"
source_key: "gh:phuryn/pm-skills"
aliases:
  - "/posts/tech/pm-skills-claude-code-pm-plugin/"
description: "pm-skills 是 Paweł Huryn 维护的 Claude Code 插件市场：9 个插件、69 个 skill、42 条命令，把 OST、假设测试、9 种优先级框架、红队评审和 AI 代码审计做成可直接执行的产品工作流。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "产品经理"]
---

# pm-skills：把 Teresa Torres / Marty Cagan / Alberto Savoia 的 PM 框架做成 AI 工作流，69 个 skill + 42 条命令

产品经理让 AI 写 PRD、做优先级排序时，遇到的多半不是"AI 不会"，而是每次产出结构都不一样：有时漏掉非目标，有时把风险写成一句空话。pm-skills（全名 PM Skills Marketplace）的思路是把 PM 圈现成的方法论逐个拆成可执行的指令文件——技能里写死分析步骤和产出结构，命令把技能串成端到端流程，插件按 PM 职能打包。Claude 在对话中自动加载相关技能，产出的是固定结构、可对照检查的文档，而不是每次重新发挥的散文。

它选的框架都有出处：Teresa Torres 的 Opportunity Solution Tree 与连续发现习惯、Alberto Savoia 的 pretotype 实验设计、Marty Cagan 的产品战略，以及 Dan Olsen 的 Opportunity Score、Strategyzer 的商业模式画布等十余种，README 的 About 节列了完整书单。维护者是波兰产品顾问 Paweł Huryn（The Product Compass Newsletter 主理人）。

## 项目概览

| 维度 | 数据 |
|---|---|
| **仓库** | [phuryn/pm-skills](https://github.com/phuryn/pm-skills) |
| **Stars** | 26,739 ★（2026-10-03 读数；2026-06-09 本文首发时 13,085） |
| **License** | MIT（2026 Paweł Huryn） |
| **建仓** | 2026-03-01 |
| **规模** | 9 个插件，main 分支 69 个 skill + 42 条命令 |
| **最新版本** | v2.1.0（2026-07-03，此版本计数仍为 68，第 69 个 skill 待发布） |
| **配套项目** | [pm-brain](https://github.com/phuryn/pm-brain)（886 ★，Markdown 版 PM 第二大脑）、claude-usage、burnstop |

一个口径说明：技能数以 main 分支为准是 69——2026 年 7 月之后仓库在 Unreleased 段新增了 code-review 技能，README 与 marketplace.json 均已按 69 计数，但尚未随版本发布；装最新 release（v2.1.0）拿到的是 68 个。42 条命令在两个时点没有变化。

## 9 个插件的全景

装一次 marketplace 就拿到全部 9 个插件，每个对应一个 PM 职能域：

| 插件 | Skills / Commands | 代表内容 |
|---|---|---|
| **pm-product-discovery** | 13 / 5 | OST（Torres）、假设识别与排序、实验设计（Savoia pretotype）、用户访谈 |
| **pm-product-strategy** | 12 / 5 | 9 段 Product Strategy Canvas、Lean Canvas / BMC / Startup Canvas、PESTLE、Porter's Five Forces、Ansoff 矩阵 |
| **pm-execution** | 16 / 11 | 8 段 PRD、OKR、sprint 三模式、pre-mortem、9 种优先级框架、红队评审 |
| **pm-market-research** | 7 / 3 | 用户画像、市场细分、TAM/SAM/SOM、竞品分析、反馈情感分析 |
| **pm-data-analytics** | 3 / 3 | 自然语言生成 SQL（BigQuery/PostgreSQL/MySQL）、cohort 留存分析、A/B 测试判读 |
| **pm-go-to-market** | 6 / 3 | GTM 战略、beachhead 市场、理想客户画像（ICP）、增长循环、销售 battlecard |
| **pm-marketing-growth** | 5 / 2 | 营销点子、定位、North Star 指标、产品命名 |
| **pm-toolkit** | 4 / 5 | 简历评审与定制、NDA 草拟、隐私政策、文案校对 |
| **pm-ai-shipping** | 3 / 5（main） | AI 生成代码的文档化与审计（v2.0 新增，详见下文） |

有一处容易望文生义：优先级框架不在 pm-toolkit 里。pm-toolkit 装的是 PM 的杂物工具——改简历、拟 NDA、写隐私政策、校对文档；9 种优先级框架是 pm-execution 下的 prioritization-frameworks 技能。另外 README 的 pm-ai-shipping 一节自己也有一处没跟上：小节标题已按 3 个技能计数，正文清单却还列着 2 个（漏了 Unreleased 的 code-review）——以磁盘上的技能目录为准，这类不一致正是仓库自己的测试要拦的（见"维护与已知问题"）。

## 三层结构：Skill / Command / Plugin

```text
Plugin = 一个 PM 域的安装单元
  ├── Command = /command-name 触发的端到端工作流
  │     └── 串起一个或多个 Skill
  └── Skill = SKILL.md 文件，承载框架、决策树、检查清单
```

**Skill** 是构建块。Claude 判断对话内容与某个技能相关时自动加载它，不需要显式调用；要强制加载可以用 `/plugin-name:skill-name` 或裸的 `/skill-name`（Claude 会自动补前缀）。

**Command** 是用户主动触发的工作流。`/write-prd`、`/sprint` 这类斜杠命令按步骤串起若干技能，跑完一条会建议下一条——README 明说命令按 PM 工作流的顺序设计成可以互相衔接。

**独立参考技能**是第三种形态，介于两者之间：prioritization-frameworks 和 opportunity-solution-tree 不挂在任何命令下，Claude 在话题相关时直接取用。你问"50 条 backlog 该用哪个优先级框架"，走的就是这条路径，不需要任何命令。

## 一次 /discover 走完发现链

/discover 是整个市场的招牌命令，README 的原例就是拿它演示的。以"给远程团队做一个 AI 会议摘要工具"为输入，完整流程有 7 步，官方标注 15–30 分钟，每个检查点都可以重定向、跳过或深挖：

1. **确认上下文**——先问清这是存量产品的连续发现，还是新概念的初始发现，两条路径后面调用的技能不同；
2. **发散**——从 PM、Designer、Engineer 三个视角生成点子，列出前 10 个并给出理由，请你挑 3–5 个带入下一步；
3. **假设识别**——存量产品检查 Value、Usability、Viability、Feasibility 四类核心风险（Torres 的分类）；新概念扩展到 8 类，外加 Ethics、Go-to-Market、Strategy & Objectives、Team——技能里直接写着"好的团队默认至少四分之三的想法不会如愿"；
4. **假设排序**——把全部假设摆上 Impact × Risk 矩阵，附实验建议；
5. **实验设计**——对高优先假设每个配 1–2 个实验：存量产品走 A/B 测试、fake door、原型；新产品走 XYZ 假设、pretotype、concierge MVP（Savoia 的路数）；
6. **汇总发现计划**——产出一份 Markdown 文档：已探索的点子、带入验证的选择、按优先级排列的假设表、实验排期、决策框架（某实验成功则如何、失败则如何）；
7. **建议下一步**——问你要不要为胜出点子写 PRD、设计访谈提纲、搭实验指标，或估算工作量拆用户故事。

第 7 步的建议对应的是 /write-prd、/interview、/setup-metrics、/write-stories 这几条命令。衔接设计贯穿全库：/write-prd 跑完会接着问要不要做 pre-mortem、拆用户故事、给干系人写通报，命令链大体沿着"发现 → 战略 → PRD → 上线 → 指标"的 PM 生命周期排布。

## 三个值得单看的设计

**9 种优先级框架，各有适用场景。** prioritization-frameworks 技能是一份参考文档，覆盖 Eisenhower 矩阵、Impact vs Effort、Risk vs Reward、Opportunity Score、Kano、加权决策矩阵、ICE、RICE、MoSCoW 九种。技能对三种给出了推荐位：Opportunity Score（Dan Olsen 的 Importance × (1 − Satisfaction)）适合客户问题，ICE 适合快速排序，RICE（(Reach × Impact × Confidence) / Effort）适合规模化评估；对 MoSCoW 则标注了"出身项目管理"的谨慎提示。公式的细节也写死了——转述出错的空间被压到最小。

**红队评审是 Steelman 先行、按测试成本排序。** strategy-red-team 技能（v2.0 新增，对应 /red-team-prd 命令）的做法：先把方案的最强形态摆出来，再逐条攻击其承重假设，按"影响 × 可能性 × 验证成本"给失败模式排序，对每条假设给出最便宜的验证方法和 kill criteria——什么信号出现就放弃。它面向的是"大多数计划只挺过了客气的反馈"这个场景，产出直接服务高管评审前的自我攻击。

**AI Shipping Kit 审计 AI 写的代码。** pm-ai-shipping（v2.0.0，2026-06-05）针对一类新问题：AI agent 写代码很快，但不留"意图记录"——系统该做什么、谁能做什么、密钥在哪、哪些规则真的被测试覆盖。这套工具先把仓库逆向成文档（/document-app：架构、用户与权限流、变量与密钥、测试覆盖图，条件性补邮件/定时任务/SEO 文档），再审计"文档说的"与"代码做的"之间的落差（/security-audit-static、/performance-audit-static），最后由 /ship-check 汇总成可评审的交付包。

v2.1.0（7 月）给审计加了牙齿：安全审计的每条发现必须带 `file:line` 加逐字代码片段的证据行，出报告前逐条对回文件复核；超过约 30 个文件或 5,000 行的仓库触发 subagent 并行分片；N+1 查询和请求瀑布成为性能审计的专项；所有审计命令预授权只读工具集，只能写 `reports/`，不许改被审计的代码。最有意思的一条是把被审计仓库整体视为不可信输入——代码注释里嵌入的指令被当作 steering 攻击记录，本身就是一个 finding。Unreleased 的 code-review 技能则把 correctness 立为核心引擎，性能和安全成了它的子情形；/ship-check 相应加了第三步 correctness 评审和第六步"由第二个模型做一次独立、无引导的复核"。

## 安装与多平台

**Claude Cowork（非开发者推荐）**：左下 Customize → Browse plugins → Personal → + → Add marketplace from GitHub → 填 `phuryn/pm-skills`，9 个插件自动装好。

**Claude Code（CLI）**：

```bash
# 1. 加 marketplace
claude plugin marketplace add phuryn/pm-skills

# 2. 按需装插件（9 个可选装）
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

**Codex CLI**：读同一份 marketplace 文件，原生安装——`codex plugin marketplace add phuryn/pm-skills` 然后 `codex plugin add pm-execution@pm-skills`。差别在命令面：斜杠命令装得进去但不会注册成 Codex 的原生 slash command，跑工作流要用自然语言描述步骤（README 给的示例："Run product discovery on X: brainstorm options, map assumptions, prioritize the risky ones, then design experiments — pause between each step."）。官方还提供一条可选路径：让 Codex 把装进来的命令文件转成 Codex 技能，并说明这是模型驱动的尽力转换，部分 Claude 专有语法翻不过去。

**其他工具（仅技能）**：`skills/*/SKILL.md` 遵循通用技能格式，复制到对应目录即可——Gemini CLI 放 `~/.gemini/skills/`，OpenCode 放 `.opencode/skills/`，Cursor 放 `.cursor/skills/`，Kiro 放 `.kiro/skills/`。技能通用，命令是 Claude 专有的。

## 维护与已知问题

节奏上看这是个高投入的个人项目：2026 年 3 月建仓，66 个提交中 64 个来自作者本人，6 月 5 日 v2.0.0 引入 pm-ai-shipping 和红队技能，7 月 3 日 v2.1.0 强化审计，之后 code-review 等改动在 Unreleased 排队。v2.1.0 起仓库带了一套一致性测试（`tests/`），每次 PR 和推送都跑：marketplace.json 列的插件必须与目录一致、README 声明的技能/命令数必须与磁盘一致、全库单一版本号、CHANGELOG 格式合法、README 里每个 `/plugin:command` 引用必须指向真实命令文件。一个靠文档吃饭的市场，用 CI 锁住文档与实物的一致性，这个设计本身就值得同类项目抄。

已知问题两条。其一，Windows 上 Cowork 可能因 VM 服务起不来而启动失败（anthropics/claude-code#27010），README 给了一个计划任务监控脚本的 workaround，作者称能解决九成情况，剩下的手动启动 services.msc 里的 Claude 服务。其二，单维护者、依赖个人精力，技能质量取决于框架本身的成色——prioritization-frameworks 对每个框架的"不适用场景"都写了实话（比如 Impact vs Effort "对战略决策不够严谨"），但把方法论跑在真实业务上仍然是你自己的功课。

配套的 [pm-brain](https://github.com/phuryn/pm-brain) 是可选的记忆层：一个纯 Markdown 文件夹放在本地，Claude 回答前读、回答后写、每周五清扫一次，不引向量库、不上云。另有 claude-usage（本地 Claude Code 用量仪表盘）和 burnstop（按 token 或金额熔断会话）两个同作者小工具。

## 适用边界与采用顺序

**适合**：需要框架化产出的产品经理和创始团队（PRD、OKR、战略、GTM）；想让团队统一 PM 工作流的负责人——一次装市场，全员命令同名同结构；用 Claude Code / Cowork 验收 AI 生成代码的 PM 与独立开发者（pm-ai-shipping 的场景）。

**不适合**：指望 AI 替你做产品决策——技能给的是结构和方法，判断仍在人；完全不用 Claude 生态的团队——技能格式虽然通用，42 条命令链只有 Claude Code / Cowork 能完整跑；对 OST、JTBD、假设测试零基础的读者——技能按"你懂这些框架"的假设写，至少要先读过对应方法论。

**建议的采用顺序**：先在 Cowork 或 Claude Code 里装 marketplace，用 `/discover` 跑一遍手头真实的发现课题（15–30 分钟就能感受到检查点机制是否合拍）；顺手的话把 `/write-prd` 和 `/red-team-prd` 接进日常文档流程；pm-ai-shipping 留到你有第一个需要验收的 AI 生成项目时再上；pm-toolkit 这类杂物技能按需取用。数字会漂移、命令会增减，装之前扫一眼 README 的计数和 CHANGELOG 的 Unreleased 段即可对齐现状。

## 结语

pm-skills 的价值不在"AI 帮你写文档"，而在它把 PM 方法论里那些容易被省略的结构——假设要分类、实验要有 kill criteria、PRD 要有八段、审计要带证据行——变成了机器强制执行的步骤。方法论仍然来自 Torres、Cagan、Savoia 这些人，这个项目做的事是让你没法跳过它们。

---

**数据口径**：仓库结构（69 skills / 42 commands / 9 plugins）、v2.1.0 release 与 CHANGELOG、marketplace.json v2.1.0、各 SKILL.md 原文均核对自 2026-10-03 的 main 分支；stars 为当日 GitHub API 读数，安装命令与 README 当期版本逐字一致。
