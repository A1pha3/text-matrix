---
title: "AI Berkshire：把四位价值投资大师的对抗塞进 Claude Code 的 16 个 Skill"
date: "2026-06-25T21:06:02+08:00"
slug: "xbtlin-ai-berkshire-multi-agent-value-investing-guide"
description: "xbtlin/ai-berkshire 是 1.5k+ Stars 的价值投资研究框架，基于 Claude Code 构建 Skill + 多 Agent 编排。它把巴菲特、芒格、段永平、李录四位大师的方法论做成可对抗的视角，配 16 个 Skill + decimal.Decimal 金融严谨性工具 + 三情景估值。文章拆解 Skill/Agent/Tool 三层架构、4 大师对抗机制、/investment-team 任务流、与同类 AI 投研工具的边界。"
draft: false
categories: ["技术笔记"]
tags: ["AI 投研", "Claude Code", "价值投资", "多 Agent", "Skill 框架"]
---

# AI Berkshire：把四位价值投资大师的对抗塞进 Claude Code 的 16 个 Skill

## §1 先给判断

`xbtlin/ai-berkshire` 不做"AI 帮你分析公司"——它做的是**带纪律的投研流程**：把"普通 AI 投研"最容易出问题的三件事（两面讨好的分析、模型心算错单位、缺乏结构化输出）从根上拆掉。

到 2026-06-25 仓库 1.5k+ Stars、266 Forks、Python 实现、MIT License，2026-04-07 立项至今不到 3 个月，README 上的实盘收益（2024 年 +69.29%、2025 年至今 +66.38%）来自富途证券真实账户截图。

它的核心架构是三层：

- **Skill 层（16 个）**：把"你要做什么"抽象成 16 个斜杠命令入口（深度研究、财报分析、行业筛选、持仓管理、思维工具）
- **Agent 层**：每个 Skill 内部都是 4 个 Agent 并行研究（段永平看商业模式、巴菲特看财务估值、芒格看行业竞争、李录看风险管理层）
- **工具层（Python `decimal.Decimal`）**：精确十进制算术、市值验算、多源交叉验证、Benford 定律检测——保证 LLM 心算不出错

**核心判断**：这是一套把 Claude Code 范式（Skill + Agent + Tool）用在投研领域的方法论框架。它不解决"AI 能不能分析公司"的问题（Claude 本身就能），它解决"AI 给的分析能不能拿来做决策"的问题。答案是：通过四大师对抗 + 强制结论 + 金融严谨性工具 + 镜子测试，把"看起来对"的分析变成"可验证、可执行"的报告。

## §2 整体架构：Skill → Agent → Tool 三层设计

仓库 `assets/architecture.mmd` 给出完整 Mermaid 架构图。三层设计的边界划得很清：

```
┌─────────────────────────────────────────────┐
│              Skill 层（16 个）               │
│  /investment-research  /investment-team    │
│  /earnings-review      /industry-research   │
│  /portfolio-review     /news-pulse          │
│  ... 16 个斜杠命令入口                       │
├─────────────────────────────────────────────┤
│              Agent 层（4 个并行）             │
│  段永平视角  巴菲特视角  芒格视角  李录视角    │
│  商业模式    财务估值    行业竞争   风险管理层   │
│  独立搜索    独立分析    独立判断   独立结论    │
│  Team Lead 汇总综合报告                       │
├─────────────────────────────────────────────┤
│              工具层（Python）                │
│  financial_rigor.py  +  decimal.Decimal     │
│  市值验算 / 三情景估值 / 多源交叉 / Benford   │
└─────────────────────────────────────────────┘
```

**Skill 层的职责**是把"场景"封装成入口。16 个 Skill 不是"16 个 prompt"，而是 16 个独立的工作流——每个 Skill 的 `SKILL.md` 文件定义触发条件、参数解析、内部 Agent 调度顺序、输出模板。同一份"四大师分析"在 `/investment-research`（单公司深度）和 `/investment-team`（多 Agent 并行）里用不同方式被复用。

**Agent 层的职责**是"上下文隔离 + 视角对抗"。每个 Agent 拿到的 system prompt 不同：段永平 Agent 的视角是"先问这是不是好生意"，巴菲特 Agent 的视角是"先问护城河能不能量化"，芒格 Agent 的视角是"先问什么情况下会死"，李录 Agent 的视角是"先问 10 年后还在不在"。四个 Agent 独立跑搜索、独立给评分，最后 Team Lead 综合——这种对抗不是为了"四个答案平均一下"，而是为了暴露单一视角的盲点。

**工具层的职责**是"数据严谨性"。`tools/financial_rigor.py` 是个独立的 Python CLI，所有计算用 `decimal.Decimal` 精确十进制（不浮点近似），关键数据至少 2 个独立来源交叉验证，误差>1% 告警。这是和"普通 AI 投研"最关键的区别——LLM 直接心算 PE，市值单位搞混港币人民币，整个分析可能都是错的。

## §3 边界拆分：四位大师的视角差异（并行机制）

这套框架的核心创新不是"用 AI 模拟巴菲特"，是"让四位大师的视角**互相挑战**"。README 直接给出了拼多多的案例，四个视角的真实矛盾：

| 视角 | 代表问题 | 拼多多评分 | 核心判断 |
|------|---------|:--------:|---------|
| **段永平**（商业模式） | "这门生意的本质是什么？用户为什么用？" | 3.7/5 | C2M 模式难以复制，平台型生意 |
| **巴菲特**（财务估值） | "护城河多宽？现金流多稳？估值多便宜？" | 4.4/5 | 扣现金 PE 仅 6.3x，印钞机级别 |
| **芒格**（逆向思考） | "什么情况下这家公司会死？护城河是不是太浅？" | 3.5/5 | 抖音 3 年做到 4 万亿 GMV，护城河比想象中浅 |
| **李录**（长期确定性） | "管理层文化如何？10 年后还在吗？" | 2.0/5 | 管理层文化有隐患，10 年确定性不足 |

巴菲特说"真便宜"，李录说"不确定就不买"——**这种冲突才是投资决策的真实状态**。单一 prompt 没法制造这种多视角对抗，这是 AI Berkshire 区别于"用 AI 问巴菲特怎么看某公司"的关键设计。

四大师的分工不是简单"按主题分"，而是按**思维模式**分：段永平看"对的生意"（定性问题）、巴菲特看"对的估值"（定量问题）、芒格看"对的反面"（逆向问题）、李录看"对的未来"（时间问题）。这种四象限划分让每个 Agent 的 system prompt 极简——不需要写 2000 字的复杂 prompt，只需要把"大师的思维锚点"写清。

## §4 任务流案例：从 `/investment-team` 跑一遍拼多多

`/investment-team` 是这套框架的旗舰 Skill，4 个 Agent 并行研究的完整流程如下：

```bash
# 1. 启动 Claude Code
claude

# 2. 触发 Skill
/investment-team 拼多多
```

**Step 1（Skill 入口）** — 加载 `skills/investment-team.md`，解析出 4 个独立 Agent 的调度计划。

**Step 2（4 Agent 并行）** — 启动 4 个 subagent，每个拿独立的 context window + 独立 system prompt + 独立工具集：

- **Agent 1（段永平视角）**：搜索拼多多的商业模式、C2M 拼工厂链路、用户心智、农产品起家逻辑 → 独立给"商业模式"维度评分
- **Agent 2（巴菲特视角）**：调用 `financial_rigor.py` 跑市值验算（拼多多 510 美元 × 9.11e9 股 vs 报告 4.65e12 港元）和 PE/PB/FCF Yield 精确十进制计算 → 独立给"财务估值"维度评分
- **Agent 3（芒格视角）**：搜索抖音电商入侵、跨境业务（Temu）监管风险、低价护城河是否被算法侵蚀 → 独立给"行业竞争"维度评分
- **Agent 4（李录视角）**：搜索陈磊/赵佳臻管理层背景、组织文化迭代速度、长期主义 vs 短期 GMV 导向 → 独立给"风险管理层"维度评分

**Step 3（数据交叉验证）** — 每个 Agent 拿到的关键数字（市值、收入、用户数）至少 2 个独立来源对比，误差>1% 触发告警；市值的港币/人民币单位差异由 `verify-market-cap` 强制校验。

**Step 4（Team Lead 综合）** — Team Lead 把 4 份独立报告整合成最终研报，包含：四维评分总表、综合评级（通过/有条件/灰色）、分层投资建议（激进/稳健/保守 三档价格区间）、镜子测试（5 句话说不清就不买）。

**Step 5（输出固化）** — 最终研报按统一模板输出，存到 `reports/拼多多/`，下次复评可直接对比变化。

关键创新在 Step 2：4 个 Agent **真的独立搜索**，不是把一个 prompt 拆 4 段。1 个 Agent 跑就是 1 倍搜索量；4 个并行 = 4 倍搜索量 + 4 个独立视角 = 接近 4 倍信息源。这种"上下文隔离 + 并行计算"是 Claude Code Agent 范式在投研领域的标准应用。

## §5 16 个 Skill 的分类与定位

16 个 Skill 按场景切成 5 类，每类解决一个独立问题：

| 分类 | Skill | 适用场景 | 内部机制 |
|------|-------|---------|---------|
| **🔬 深度研究**（5） | `/investment-research` | 单公司全方位深度研究 | 7 模块顺序执行：数据→生意→护城河→逆向→管理层→文明趋势→估值 |
| | `/investment-team` | 多 Agent 并行（4 个独立研究） | 上面 §4 详述 |
| | `/management-deep-dive` | 管理层纵深研究 | 单独挖"买股票就是买人"的核心变量 |
| | `/private-company-research` | 未上市公司（蚂蚁、SpaceX） | 招股书+融资+行业数据多源拼凑 + 置信度标注 🟢🟡🔴 |
| | `/deep-company-series` | 公众号级 8 篇长文 | 12 万字系列拆一家公司 |
| **📊 财报分析**（2） | `/earnings-review` | 只读原始财报 | 巴菲特式年报精读，不依赖二手研报 |
| | `/earnings-team` | 四大师并行解读 + 公众号发布 | 解读→润色→评审→可发布文章 |
| **🏭 行业筛选**（4） | `/industry-research` | 产业链全景扫描 | 按产业链环节切片，全市场→头部 |
| | `/industry-funnel` | 行业漏斗（30→10→3） | 全市场粗筛≤10→精细≤10→终选 3 家 + 组合互补 |
| | `/quality-screen` | 去劣快速筛选 | 7 条硬指标排除非一流公司 |
| | `/investment-checklist` | 巴菲特 6 关 Checklist | 10 分钟决定是否值得深入研究 |
| **📈 持仓管理**（3） | `/portfolio-review` | 仓位审视+再平衡 | 从"研究公司"升级到"管理组合" |
| | `/thesis-tracker` | 买入后纪律系统 | 持续跟踪投资论文是否被证伪 |
| | `/news-pulse` | 股价异动快速归因 | 4 维并行侦察（公司/监管/对手/情绪），10-15 分钟出归因 |
| **🧠 思维工具**（2） | `/dyp-ask` | 段永平问答 | 以段永平方式思考任何问题 |
| | `/financial-data` | 财务数据获取+交叉验证规范 | 强制 2 个独立来源，误差>1% 告警 |

**重点提一下 `/investment-funnel`**：这是把"AI 漏斗"做对的关键。普通 AI 给"全市场→3 家"的输出是黑箱——你不知道中间 27 家为什么被淘汰。`/investment-funnel` 强制每层留下/淘汰标准，淘汰的标的写明理由，终选 3 家按"组合互补性"（高确定性 + 中等弹性 + 高弹性）选，不是按打分前 3 名——这种"组合配置视角"是单一 Agent 做不到的。

## §6 金融严谨性工具：`tools/financial_rigor.py`

LLM 心算不可靠是 AI 投研的隐形杀手。仓库里的 `tools/financial_rigor.py` 是个独立 Python CLI，5 个核心命令：

| 命令 | 解决的问题 | 示例 |
|------|-----------|------|
| `verify-market-cap` | 股价 × 总股本精确验算，检测单位错误 | `python3 tools/financial_rigor.py verify-market-cap --price 510 --shares 9.11e9 --reported 4.65e12 --currency HKD` |
| `verify-valuation` | PE/PB/ROE/FCF Yield 精确十进制 | 替换 LLM 浮点近似（`0.1 + 0.2 = 0.3` 在金融场景不允许失败） |
| `cross-validate` | N 个来源同一数据自动比对，>1% 告警 | 多家数据源 PE 对比 |
| `three-scenario` | 乐观/中性/悲观三情景精确计算目标价 | 估值必备 |
| `benford` | Benford 定律检测财务数据首位数字分布异常 | 财报造假检测 |

**设计原则**：所有计算用 Python `decimal.Decimal` 精确十进制，不用 `float` 浮点近似。这是一个被绝大多数 AI 投研工具忽略的细节——一个 0.1% 的浮点误差在 PE 计算里可能放大到 1 美元的目标价差异。

`/financial-data` Skill 是这套工具的入口：任何"获取财务数据"的动作都强制走 2 个独立来源 + `cross-validate` 校验，把"数据严谨性"从工具内置成工作流。

## §7 镜子测试：决策纪律的最后一关

仓库所有 Skill 的最终输出都强制过"镜子测试"——一段话，5 句话说不清就不买，没有例外。腾讯的镜子测试示例：

> "我以 380 港元买入腾讯，因为：
> 1. 这门生意的本质是**社交网络+数字内容平台**，我理解它；
> 2. 它的护城河是**12 亿用户的社交关系链**，而且在变宽；
> 3. 管理层**Pony Ma 低调务实、资本配置优秀**，值得信赖；
> 4. 当前价格相当于内在价值的**8 折**，有一定安全边际；
> 5. 即使我错了，下行风险可控，因为**账上净现金超 2000 亿、游戏现金流强劲**。"
>
> ✅ 通过镜子测试

这个测试是"反 AI 幻觉"的关键设计：AI 给的"分析"看起来都对，但没法拿来做决策，因为答案里没有"我愿意为这个判断押多少钱"。镜子测试强制把"研究"和"决策"绑死——研究做得再深，过不了镜子测试就不能进组合。

## §8 适用边界

**适合**：

- 你已经在用 Claude Code，希望把"AI 投研"从"问问就忘"升级到"可复用的研究流程"
- 你认同价值投资框架（能力圈、好生意、护城河、管理层、安全边际、决策纪律），希望 AI 帮你把这套纪律工程化
- 你在做长期投资研究（不是高频量化），需要跨公司、跨时间的可比输出
- 你要扩展单 Agent Claude 投研到多 Agent 并行（4 Agent = 4 倍搜索量 + 4 个视角对抗）

**不适合**：

- 短线 / 量化 / 高频交易——这是价值投资研究框架，不是择时工具
- 完全没读过《聪明的投资者》或《巴菲特致股东的信》——这套框架假设你理解基础概念
- 寻找"AI 推荐股票"——它不推荐股票，只生成可决策的研究报告；最终买入决策要由你做
- 投资金额 < 100 万——研究深度边际效益不够，等你研究规模到了再考虑

**下一步**：

- 想看实际报告：仓库 `reports/` 目录有拼多多、腾讯、7 家公司对比的真实研报
- 想复现工作流：`git clone https://github.com/xbtlin/ai-berkshire && cp ai-berkshire/skills/*.md ~/.claude/commands/`
- 想接实时数据：路线图里有"基于 MCP 的实时数据接入（Wind/Bloomberg/Yahoo Finance）"待办

## §9 外部资源

- [仓库主页](https://github.com/xbtlin/ai-berkshire) — 16 个 Skill + 4 大师方法论的完整入口
- [架构图（Mermaid 源）](https://github.com/xbtlin/ai-berkshire/blob/main/assets/architecture.mmd) — Skill/Agent/Tool 三层设计
- [拼多多投资报告](https://github.com/xbtlin/ai-berkshire/tree/main/reports/拼多多) — `/investment-team` 真实输出
- [腾讯投资报告](https://github.com/xbtlin/ai-berkshire/tree/main/reports/腾讯) — `/investment-research` 真实输出
- [7 家公司 Checklist 对比](https://github.com/xbtlin/ai-berkshire/blob/main/reports/多公司对比-checklist-20260408.md) — 茅台/腾讯/英伟达/美团/快手/拼多多/泡泡玛特
- [金融严谨性工具](https://github.com/xbtlin/ai-berkshire/tree/main/tools) — `financial_rigor.py` 源码
- [行业漏斗（AI 算力/模型/应用/电力）](https://github.com/xbtlin/ai-berkshire/tree/main/reports) — `/industry-funnel` 4 子赛道终选
- [Claude Code Skills 官方文档](https://code.claude.com/docs/en/skills) — Skill 范式的权威说明
