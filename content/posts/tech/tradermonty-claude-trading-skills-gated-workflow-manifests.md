---
title: "Claude Trading Skills：交易工作流的正确抽象不是「策略」，而是带前置闸门的工作流清单"
date: "2026-11-20T01:27:19+08:00"
slug: "tradermonty-claude-trading-skills-gated-workflow-manifests"
description: "Claude Trading Skills 是面向个人投资者的 74 技能交易工作流工具包，用 YAML 清单定义 14 条工作流的步骤、决策闸门与产物契约。本文拆解其「先定仓位姿态再找机会」的门控设计、consumes/produces 产物契约与日英双语强制校验，并说明它为何不做信号服务。"
draft: false
categories: ["技术笔记"]
tags: ["交易系统", "AI Agent", "工作流编排", "Claude Skills", "风险管理"]
github_repo: "tradermonty/claude-trading-skills"
source_key: "gh:tradermonty/claude-trading-skills"
---

## 核心判断

市面上的「AI 交易工具」通常在卖两样东西之一：信号，或者回测。这个项目两样都不卖。

Claude Trading Skills 的自我定位是**流程工具包**（toolkit），目标用户是「时间受限的个人投资者」—— 以长期投资、ETF 和股息股为核心，在市场条件合适时用有纪律的波段交易做卫星策略。作者写得很直接：

> 目标不是把买卖决策外包给 AI。目标是**结构化**市场复盘、风险管理、交易计划、日志与持续改进。

这决定了它的架构重心不在「找出好股票」，而在**约束「什么时候不该交易」**。

整个项目的技术核心是一个判断：**工作流的正确抽象不是策略，是带前置闸门的清单**。

这不是抽象概念，而是一个具体的工程决策。仓库里的 14 条工作流是 YAML 清单，每条声明自己依赖哪些上游产物、在什么条件下**不该**运行、以及每一步消费和产出什么。最典型的一条：

```yaml
when_not_to_run: >-
  Do not run when the latest market-regime-daily exposure_decision is
  cash-priority or restrictive. Do not use as a standalone screener without
  the regime gate.
```

翻译成白话：**当天是「现金优先」或「限制仓位」的日子，就不要跑这个选股工作流**。选股器不能单独使用。

这个约束在传统交易系统里通常靠人的纪律维持。在这里，它被写成了机器可校验的清单字段。

必须先说清楚免责边界：**README 明确声明这不是信号服务、不承诺盈利、不构成投资建议、不是券商执行平台**，全部决策、仓位大小、税务合规和券商使用都是用户自己的责任。所有决策、仓位大小、税务合规和券商使用都是用户自己的责任。仓库的免责声明里还专门加了一句：过往业绩、回测、选股结果、报告和 AI 生成的分析都不保证未来结果。

截至 2026 年 11 月 20 日，这个仓库有 7195 stars、1456 forks，Python 为主，MIT 许可，2025 年 10 月创建，11 月 19 日仍在更新。

## 系统地图

```
workflows/*.yaml          ← 14 条工作流清单（规范定义，优先于一切散文）
   │
   ├─ steps[]             ← 每步恰好一个技能
   ├─ decision_gate       ← 需要 decision_question + 日文版
   ├─ artifacts[]         ← 命名产物：produced_by_step / required
   ├─ consumes/produces   ← 步骤间的数据契约
   └─ manual_review       ← 人必须逐项确认的清单
        │
        ↓
skills/*.md              ← 74 个技能，各自一个 SKILL.md
        │
        ↓
scripts/*.py             ← 真正的计算：评分引擎、检测器
        │
        ↓
reports/*.json           ← 产物文件，被上游工作流消费
```

关键的一条规则写在 `workflows/README.md` 开头：

> 这些文件是**多技能工作流的规范定义**。如果其它任何地方（`README.md`、`CLAUDE.md`、博客、文档站）与这个目录里的清单不一致，**以 YAML 为准**。

这是很成熟的工程约定 —— **机器可读的清单是唯一真相来源，散文随时可能过期，YAML 不会**。而且有 validator 在守着。

## 机制一：先定姿态，再找机会

`market-regime-daily` 是门控设计的核心，也是最短的一条工作流（`estimated_minutes: 15`，`difficulty: beginner`）。

它跑三个技能：`market-breadth-analyzer`、`uptrend-analyzer`、`exposure-coach`。

`exposure-coach` 是个合成器，它把八个上游技能的 JSON 输出整合成一个控制面决策：

| 上游技能 | 输出文件模式 | 提供的信号 |
|---|---|---|
| market-breadth-analyzer | `breadth_*.json` | 涨跌比、新高/新低 |
| uptrend-analyzer | `uptrend_*.json` | 上升趋势参与度百分比 |
| macro-regime-detector | `regime_*.json` | 当前 regime（集中 / 扩散 / 收缩…） |
| market-top-detector | `top_risk_*.json` | 分布日计数、顶部概率评分 |
| ftd-detector | `ftd_*.json` | Follow-Through Day 质量（底部确认） |
| theme-detector | `theme_detector_*.json` | 活跃主题与轮动 |
| sector-analyst | `sector_*.json` | 板块表现排名 |
| institutional-flow-tracker | `institutional_*.json` | 机构净买入/卖出 |

它回答的是个人交易者最核心的那个问题：**「我现在该往股市投多少资本？」** —— 在任何个股分析开始之前。

输出是一页 Market Posture 摘要：净敞口上限、成长 vs 价值偏好、参与广度、以及「允许新开仓 / 现金优先」的结论。

README 里的预览图展示了三种典型输出，其中一张是：**36% 敞口上限、REDUCE_ONLY 姿态、LOW 置信度，因为关键输入缺失**。

最后这半句是这套设计的诚实之处 —— **缺输入时它降低置信度，而不是硬给一个结论**。注意置信度低的那张图，姿态是最保守的那个。

而 `market-regime-daily` 的 `when_not_to_run` 又反向声明：

> 不要把这个输出当作独立的买卖信号。`exposure_decision` 是**姿态**（allow / restrict / cash-priority），不是指令。

三层防护：姿态不是信号 → 现金优先的日子不跑选股 → 选股器不能单独用。

## 机制二：产物契约

工作流之间靠**命名产物**传递数据，每个产物都声明谁产出、是否必需：

```yaml
artifacts:
  - id: market_breadth_report
    produced_by_step: 1
    required: true
    downstream_hints:
      - swing-opportunity-daily
      - monthly-performance-review
```

`downstream_hints` 是给人和 agent 的导航提示，告诉谁会消费这个产物。

### `consumes:` 的语义很微妙

`workflows/README.md` 里专门用一节解释了这件事，因为它很容易被误读：

> 步骤的 `consumes:` 列表记录该步骤**如果**前面的步骤产出了产物，**可以**读取哪些。它是否在运行期实际存在，取决于产出它的步骤是否跑过：
>
> - 如果产出步骤是**非可选**的，产物必然存在，**当作必需输入处理**。
> - 如果产出步骤是**可选**的（`optional: true`），消费步骤必须优雅处理缺失的情况。
>
> 这是有意保持最小化的 —— 没有单独的 `optional_consumes:` 字段。**可选性放在生产者身上，消费者负责处理缺失。**

这个设计决定值得单独拎出来。绝大多数编排框架会在每个边上都标一遍可选性，结果是 N 个边 × M 种状态，出错空间巨大。这里把可选性收敛到**生产点**一个地方，消费点只需要一个规则：「上游可选则你得能处理没有」。

单一职责也贯彻得很彻底：**每个 step 恰好一个 skill**。没有「这一步同时做三件事」。

### 决策闸门

步骤可以是 `decision_gate`，但要求同时提供 `decision_question` 和 `decision_question_ja`。这保证了闸门的存在形式是**一个待回答的问题**，而不是一个自动分支。

## 机制三：日英双语是强制的

`workflows/README.md` 里有一条不起眼但很硬的规则：

> 在 `--strict-workflows` 下，所有面向人看的日文字段都是强制的（`WF014`）。**日语文档生成失败，而不是静默回退到英文。**

也就是说，如果某个字段的日文版缺失，构建**直接失败**。

这条规则解决的是一个很常见的国际化失败模式：日文文档悄悄退化成英文，用户以为「有日文版」，实际是半成品。**让生成失败比静默降级好得多** —— 后者你永远不会发现。

机器标识符、状态值、CLI 选项、文件路径和 API profile 则保持不翻译。这个边界划得清楚。

## 14 条工作流

| 工作流 | 节奏 | 耗时 | API profile | 锚点技能 |
|---|---|---|---|---|
| `market-regime-daily` | 每日 | ~15 分钟 | mixed（基础无需 key） | market-breadth-analyzer, uptrend-analyzer, exposure-coach |
| `portfolio-holdings-review` | 每周 | ~15 分钟 | no-api-basic | portfolio-manager |
| `core-portfolio-weekly` | 每周 | ~60 分钟 | alpaca-required | portfolio-manager, kanchi-dividend-review-monitor, trader-memory-core |
| `swing-opportunity-daily` | 每日 | ~40 分钟 | fmp-required | vcp-screener, drawdown-circuit-breaker, position-sizer, pre-trade-discipline-gate |
| `multi-asset-opportunity-daily` | 每日 | ~45 分钟 | mixed | macro-regime-detector, theme-detector, trade-hypothesis-ideator |
| `stockbee-ep-daily` | 每日 | ~40 分钟 | mixed | drawdown-circuit-breaker, stockbee-episodic-pivot-analyzer, position-sizer, pre-trade-discipline-gate |
| `stockbee-20pct-study-daily` | 每日 | ~30 分钟 | mixed | stockbee-20pct-study |
| `stockbee-fluency-loop` | 每日 | ~20 分钟 | no-api-basic | stockbee-setup-fluency-trainer |
| `trade-memory-loop` | 每笔平仓后 | 不定 | no-api-basic | trader-memory-core, signal-postmortem |
| `monthly-performance-review` | 每月 | ~90 分钟 | no-api-basic | trader-memory-core, signal-postmortem, backtest-expert |
| `shapiro-contrarian` | 每周 | ~60 分钟 | fmp-required | cot-contrarian-detector, contrarian-setup-gate, futures-position-sizer… |
| `kanchi-dividend-weekly` | 每周 | ~60 分钟 | mixed | kanchi-dividend-sop, value-dividend-screener, dividend-growth-pullback-screener |
| `earnings-weekly` | 每周 | ~60 分钟 | fmp-required | earnings-trade-analyzer, pead-screener, drawdown-circuit-breaker, position-sizer |
| `strategy-research-pipeline` | 不定 | ~60 分钟 | no-api-basic | edge-candidate-agent, edge-hint-extractor, backtest-expert |

**`api_profile` 这一列值得看**：它明确标注每条工作流需要哪些付费数据 API（Alpaca、FMP），哪些**完全不需要**。`no-api-basic` 的那几条（`trade-memory-loop`、`monthly-performance-review`、`portfolio-holdings-review`、`stockbee-fluency-loop`）是纯本地的。

这让「先免费用起来」的路径是明确的：日志复盘、月度回顾、持仓检查都不需要 key。

注意 `swing-opportunity-daily` 的锚点技能里有 `pre-trade-discipline-gate` 和 `drawdown-circuit-breaker` —— **纪律闸门和熔断器是跟选股器绑在一起的**，不是可选步骤。

## 74 个技能

技能目录涵盖的维度比「技术分析」宽得多：

- **市场状态**：market-breadth-analyzer、uptrend-analyzer、macro-regime-detector、market-top-detector、market-environment-analysis、downtrend-duration-analyzer、crypto-regime-analyzer
- **选股器**：vcp-screener、canslim-screener、finviz-screener、pead-screener、pair-trade-screener、contrarian-setup-gate、dividend-growth-pullback-screener
- **风险**：drawdown-circuit-breaker、exposure-coach、position-sizer 类、futures-position-sizer、pre-trade-discipline-gate
- **组合与股息**：portfolio-manager、kanchi-dividend-sop、kanchi-dividend-review-monitor、kanchi-dividend-us-tax-accounting
- **记忆与复盘**：trader-memory-core、signal-postmortem、news-reaction-failure-analyzer
- **研究与边缘发现**：edge-pipeline-orchestrator、edge-candidate-agent、edge-strategy-designer、edge-signal-aggregator、edge-concept-synthesizer、edge-strategy-reviewer、edge-hint-extractor
- **回测**：manifoldbt-backtester、backtest-expert、mt5-robot-tester
- **其它**：earnings-calendar、economic-calendar-fetcher、ftd-detector、institutional-flow-tracker、ibd-distribution-day-monitor、cot-contrarian-detector、data-quality-checker、dual-axis-skill-reviewer

`edge-*` 这一组值得注意 —— 它是一条**从「提示」到「可检验策略」的流水线**：edge-pipeline-orchestrator 调度，edge-hint-extractor 抽线索，edge-candidate-agent 提候选，edge-concept-synthesizer 做概念综合，edge-strategy-designer 出策略，backtest-expert 回测，edge-strategy-reviewer 评审，edge-signal-aggregator 汇总。

`data-quality-checker` 的存在也说明了作者对 AI 在金融数据上的判断 —— **数据质量本身需要被检查**，不是默认可信。

## 一条完整工作流的结构

以 `swing-opportunity-daily` 为例，它的 YAML 完整结构是：

```yaml
schema_version: 1
id: swing-opportunity-daily
display_name: Swing Opportunity Daily
cadence: daily
estimated_minutes: 40
target_users: [part-time-swing-trader]
difficulty: intermediate
api_profile: fmp-required

when_to_run: >-
  Only after market-regime-daily has produced a non-restrictive exposure
  decision. Identifies swing trade candidates and builds entry plans.
when_not_to_run: >-
  Do not run when the latest market-regime-daily exposure_decision is
  cash-priority or restrictive. Do not use as a standalone screener without
  the regime gate.

required_skills:
  - vcp-screener
  - drawdown-circuit-breaker
  - technical-analyst
  - position-sizer
  - trader-memory-core
  - pre-trade-discipline-gate

prerequisite_workflows:
  - id: market-regime-daily
    artifact: exposure_decision
    rationale: >-
      New swing trade risk requires a non-restrictive exposure decision.

artifacts:
  - id: circuit_breaker_decision
    produced_by_step: 1
    required: true
  - id: vcp_candidates
    produced_by_step: 2
    required: true
  # ...后续产物，多为 optional: false
```

注意 `prerequisite_workflows` 上方那行注释：

> 仅作信息用途 —— **校验器不强制工作流间的顺序**。

这条注释坦率地承认了一个限制：跨工作流的顺序约束**写在文档里，不在机器里**。清单能保证「这一步消费什么、产出什么」，但保证不了「你必须先跑 regime-daily」。

这个诚实的标注比假装有强制力要好，但它确实是这套系统的一个真实缺口 —— 用户跳过 regime-daily 直接跑选股，机器不会拦。**这条约束目前只靠 `when_not_to_run` 的文字和人的自觉。**

## 半自动，不是自动

每条工作流都有 `manual_review` 段：

> 与条目对齐的检查清单，人类必须逐项确认。**工作流是半自动的，不是自动执行。人的判断仍在回路里。**

加上 `journal_destination`（哪个技能负责记录结果；只读的持仓工作流没有）和 `final_outputs`（只有 `monthly-performance-review` 有，它把**交易侧改进**和**仓库侧改进**分开 —— 改策略 vs 改工具本身）。

最后这个区分很有意思：**用工具时发现是策略的问题还是工具的问题，是两种不同的改进**。很多工具把这两者混在一起，导致「因为工具输出不好看所以改策略」这种本末倒置。

## 边界

**它明确不做的事**：不提供信号、不做自动交易、不承诺盈利。README 写明「不适合全自动交易、信号外包、短线剥头皮」。

**不覆盖内网 AD 那类东西** —— 无关，但同样重要的是：**它不覆盖税务和合规**。有一个 `kanchi-dividend-us-tax-accounting` 技能，但这只是辅助，不是专业税务意见。

**74 个技能的深度不均。** 核心的 `exposure-coach`、`drawdown-circuit-breaker`、`trader-memory-core` 有真实的 Python 脚本；边缘的一些技能可能主要是 Markdown 流程。**用之前自己看一眼你依赖的那条链是不是真有实现。**

**工作流间的顺序约束不在机器里**（见上）。

**金融领域的内容需要你自己有判断。** 免责声明是认真的，回测结果不是收益承诺。

## 采用顺序

1. **先读 `workflows/README.md` 的 "How to read a manifest" 一节**，再读 `market-regime-daily.yaml`。这两个文件是理解整个项目的最短路径 —— 项目刻意把它们写清楚了。
2. **从 `trade-memory-loop` 或 `portfolio-holdings-review` 开始**，它们是 `no-api-basic`，**不需要任何付费 API key**。先跑通「日志 → 复盘」这条纯本地链路，验证你真的会用它。
3. **再建 `market-regime-daily` 基线**。这是所有波段工作流的前置，API profile 是 mixed（基础路径无需 key）。
4. **最后才接 FMP / Alpaca**，跑 `swing-opportunity-daily`。**不要一上来就跑它** —— 没有 regime 门控的选股结果没有意义。
5. **每次平仓后跑 `trade-memory-loop`，每月跑 `monthly-performance-review`。** 这两条是整个系统真正产生复利的地方，也是最少人做的地方。
6. **新建工作流时，遵守「YAML 是规范，散文不是」这条约定。** 文档与清单冲突时改文档，不要改清单。

## 排查：按现象定位

| 现象 | 先查这里 |
|---|---|
| 不知道现在该不该交易 | 跑 `market-regime-daily`，看 `exposure_decision`；别直接跑选股 |
| 选股器给出结果但没意义 | 检查当天 `exposure_decision` 是不是 cash-priority / restrictive；这条约束目前靠自觉，机器不拦 |
| 缺上游产物 | 看消费步骤的 `consumes:` 里那个产物的生产步骤是不是 `optional: true`；可选产物缺失时消费步骤应优雅降级 |
| 找不到某个 API 能不能免 | 看工作流的 `api_profile` 字段；`no-api-basic` 的那几条不需要任何 key |
| 日文文档不完整 | `--strict-workflows` 下会直接失败（`WF014`）而不是回退英文；补上 `*_ja` 字段 |
| 日文文档看着是英文 | 检查是不是没开 `--strict-workflows`，导致静默回退了 |
| 清单和文档说法不一致 | **以 YAML 为准**（`workflows/README.md` 的明确约定）；修文档 |
| 某个技能的结论可疑 | 先确认 `data-quality-checker` 跑过了 —— 这个仓库把数据质量当成需要独立验证的东西 |
| 想验证某个策略 | 走 `strategy-research-pipeline`，末尾是 `backtest-expert`；记住回测不保证未来 |

## 参考

- 仓库：<https://github.com/tradermonty/claude-trading-skills>
- 文档站：<https://tradermonty.github.io/claude-trading-skills/>
- 项目愿景：仓库内 `PROJECT_VISION.md`
- 工作流清单规范：仓库内 `docs/dev/metadata-and-workflow-schema.md`
- 新手第一周：仓库内 `docs/en/your-first-week.md`
- 隐私政策与安全策略：仓库内 `docs/en/privacy.md`、`SECURITY.md`
