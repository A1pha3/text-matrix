---
title: "Vibe-Trading 完全指南：HKUDS 团队的「Vibe」式个人交易 Agent"
date: "2026-06-04T15:00:00+08:00"
slug: vibe-trading-hkuds-personal-trading-agent-guide
description: "Vibe-Trading 是 HKUDS 开源的个人交易 Agent 工作台，集成 36 个 MCP 工具、77 金融 skills、452 个 quant alpha 因子，覆盖 A股/港股/美股/加密多市场，支持 Robinhood 受限授权实盘。"
draft: false
categories: ["技术笔记"]
tags: ["量化交易", "AI Agent", "MCP", "Shadow Account", "Alpha Zoo", "Robinhood"]
---

# Vibe-Trading 完全指南：HKUDS 团队的「Vibe」式个人交易 Agent

## 核心判断

`Vibe-Trading`（仓库 [HKUDS/Vibe-Trading](https://github.com/HKUDS/Vibe-Trading)）是香港大学数据智能实验室（HKUDS）开源的"**Vibe 风格**"个人交易研究工作台——所谓"**Vibe**"，指的是"**自然语言描述想法 → 工具链自动跑完整套研究 + 回测 + 风控**"。

它的护城河在四件别家没拼齐的事：

1. **77 个金融 skills + 36 个 MCP 工具**：A 股/港股/美股/加密全覆盖，tushare/yfinance/akshare/mootdx/ccxt 五源自动 fallback
2. **452 个预置 alpha 因子**（qlib158 + alpha101 + gtja191 + academic 6）：一行命令 `vibe-trading alpha bench --zoo gtja191` 跑完一个因子动物园
3. **Shadow Account**（影子账户）：**解析你自己过去的交易记录** → 自动提取规则 → 用规则跑回测，告诉你"按你写的规则本来能赚多少"
4. **Connector-first Broker Architecture**（券商连接器优先）：同一套 API 切换 IBKR / Robinhood / 富途 / 老虎 / OKX / 币安 / 阿里帕卡；**Robinhood 实盘带硬限护栏**（mandate 承诺 + 文件级 kill switch + fail-closed pre-trade + 完整审计日志）

> 一句话：**Vibe-Trading = "AI Agent + 量化研究工作流 + 受限实盘"** 三位一体。如果你想"自己写交易想法，Agent 帮你跑"，这是目前最完整的开源方案。

## 项目地图

| 维度 | 关键信息 |
|------|----------|
| 仓库 | [HKUDS/Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) |
| 官网 | [vibetrading.wiki](https://vibetrading.wiki/) |
| 文档 | [vibetrading.wiki/docs](https://vibetrading.wiki/docs/) |
| PyPI | [pypi.org/project/vibe-trading-ai](https://pypi.org/project/vibe-trading-ai/) |
| 许可证 | MIT |
| 维护方 | HKUDS（Data Intelligence Lab @ HKU） |
| 当前版本 | v0.1.9（2026-06-01 发布） |

### 能力矩阵

| 维度 | 实现 |
|------|------|
| 自然语言研究 | 多 Agent loop（Plan → Ground → Execute → Validate → Deliver） |
| 多市场 | A 股 / 港股 / 美股 / 加密 / 期货 / 外汇 / 期权 |
| 数据源 | tushare / yfinance / akshare / mootdx / ccxt / 5 源自动 fallback |
| 后端 | Python 3.11+ / FastAPI |
| 前端 | React 19 |
| Broker | IBKR（TWS/Gateway）、Robinhood（OAuth MCP）、Tiger、Longbridge、Alpaca、OKX、Binance、Futu |
| Skills | **77 个**金融 skills，分 8 类 |
| MCP 工具 | **36 个** trading/data/research 工具 |
| Alpha 因子 | **452 个** 预置（qlib158 + alpha101 + gtja191 + academic） |
| Swarm 预设 | 29 套多 Agent 团队（投资委员会、量化台、加密交易台、宏观等） |
| 导出 | Pine Script v6 / 通达信 / MetaTrader 5 / MCP 服务 |
| 跨平台 | Docker 非 root 用户运行；macOS / Linux / Windows |

## 安装与快速上手

### 安装

```bash
pip install vibe-trading-ai
```

### 30 秒体验

```bash
# 自然语言研究
vibe-trading run -p "Backtest a BTC-USDT 20/50 moving-average strategy for 2024, summarize return and drawdown, then export the report"

# 一行 bench 整个 alpha zoo
vibe-trading alpha bench --zoo gtja191 --universe csi300 --period 2018-2025 --top 20
```

### 上传自己的交易记录

```bash
vibe-trading --upload trades_export.csv
vibe-trading run -p "Analyze my trading behavior, extract my shadow strategy, and compare it with my actual trades"
```

支持同花顺 / 东方财富 / 富途 / 通用 CSV 四种格式。

## 核心能力拆解

### 1. Skills 库（77 个金融技能 / 8 大类）

| 分类 | 数量 | 示例 |
|------|------|------|
| Data Source | 7 | `data-routing` / `tushare` / `yfinance` / `okx-market` / `akshare` / `mootdx` / `ccxt` |
| Strategy | 17 | `strategy-generate` / `cross-market-strategy` / `technical-basic` / `candlestick` / `ichimoku` / `elliott-wave` / `smc` / `multi-factor` / `ml-strategy` |
| Analysis | 17 | `factor-research` / `macro-analysis` / `global-macro` / `valuation-model` / `earnings-forecast` / `credit-analysis` / `dividend-analysis` |
| Asset Class | 9 | `options-strategy` / `options-advanced` / `convertible-bond` / `etf-analysis` / `asset-allocation` / `sector-rotation` |
| Crypto | 7 | `perp-funding-basis` / `liquidation-heatmap` / `stablecoin-flow` / `defi-yield` / `onchain-analysis` |
| Flow | 7 | `hk-connect-flow` / `us-etf-flow` / `edgar-sec-filings` / `financial-statement` / `adr-hshare` |
| Tool | 11 | `backtest-diagnose` / `report-generate` / `pine-script` / `doc-reader` / `web-reader` / `vnpy-export` / `alpha-zoo` |
| Risk | 1 | `ashare-pre-st-filter` |

> 这 77 个 skill 是 Vibe-Trading 跟"通用 Agent"的核心区别——它是**有金融领域纵深的 Agent**，不是"聊天 + 跑代码"。

### 2. Alpha Zoo（452 个预置 alpha 因子）

| Zoo | 数量 | 来源 | 许可证 |
|-----|------|------|--------|
| `qlib158` | 154 | Microsoft Qlib `Alpha158` | Apache-2.0 |
| `alpha101` | 101 | Kakushadze 2015（arXiv:1601.00991） | 数学公式 |
| `gtja191` | 191 | 国泰君安 2014 短周期因子报告 | 数学公式 |
| `academic` | 6 | Fama-French 5 + Carhart 动量 | 学术文献 |

一行命令跑完整个 zoo：

```bash
vibe-trading alpha bench --zoo gtja191 --universe csi300 --period 2018-2025 --top 20
```

输出每个 alpha 的 **IC / IR / alive / reversed / dead** 分类（避免"只是跟踪市场 beta"的伪 alpha）。

防护措施：

- **AST purity gate**：算子层禁掉未来数据
- **300-row lookahead sentinel test**：sentinel 测试防 look-ahead
- **`pytest-socket` 网络 kill-switch**：测试中禁网，避免偷偷拉数据
- **DCO 工作流**：社区 PR 必须签 Developer Certificate of Origin

### 3. Shadow Account（影子账户）

这是 Vibe-Trading 最具创意的功能。流程：

| 步骤 | Agent 输出 |
|------|------------|
| 1. 读交易记录 | 解析同花顺 / 东财 / 富途 / 通用 CSV |
| 2. 行为画像 | 持仓天数、胜率、盈亏比、回撤、处置效应、过度交易、追涨杀跌、锚定偏差 |
| 3. 规则提取 | 把反复出现的进出场动作转成显式策略 |
| 4. 跑影子 | 用提取出的规则回测，高亮规则破坏 / 提前出场 / 错过信号 / 替代交易路径 |
| 5. 出报告 | HTML / PDF 报告，可存档或再迭代 |

> 通俗讲：自己实盘+自己跑一遍规则回测，diff 出"按规则 vs 实际"的差距——这是行为金融学+量化的混合产物。

### 4. Broker Connector 架构（券商连接器优先）

v0.1.9（2026-06-02）落地的核心架构变更——**所有券商统一走 connector profile**：

```bash
vibe-trading connector list                  # 列所有可用 connector
vibe-trading connector use <name>            # 切换
vibe-trading connector check                 # 健康检查
vibe-trading connector account               # 看账户
vibe-trading connector positions             # 看持仓
vibe-trading connector orders                # 看订单
vibe-trading connector quote                 # 看报价
vibe-trading connector history               # 看历史
```

支持的 connector：

| Broker | 类型 | 状态 |
|--------|------|------|
| **IBKR（TWS/Gateway）** | 本地只读 | 稳定 |
| **Robinhood** | OAuth MCP 实盘 | **受 mandate 约束** |
| Tiger（老虎） | 模拟+实盘 | 2026-06-02 起 |
| Longbridge（长桥） | 模拟+只读 | API 不区分 paper/live |
| Alpaca | 模拟+实盘 | 受 mandate 约束 |
| OKX | 模拟+实盘 | 受 mandate 约束 |
| Binance | 模拟+实盘 | 受 mandate 约束 |
| Futu（富途） | 模拟+实盘 | 受 mandate 约束 |

### 5. Robinhood 实盘护栏（关键安全设计）

Robinhood 是**实盘**支持的代表。它的安全设计是**"显式承诺 + 文件级 kill switch + 失败关闭 + 审计日志"**：

- **Mandate（用户承诺）**：自己设定 symbol universe / order size / exposure / leverage / daily cap
- **Kill switch**：文件系统级别的"立即停"
- **Fail-closed pre-trade gate**：下单前自检，不通过直接拒
- **Audit ledger**：所有动作全留痕
- **Auto-expire mandate**：承诺过期自动失效

> ⚠️ **官方明确标注**：Experimental / use at your own risk。**没有资金托管，没有交易所权限**——broker 持资执行，Vibe-Trading 只传递意图。

### 6. Swarm（多 Agent 团队）

29 套预设团队覆盖主流场景：

| Preset | 工作流 |
|--------|--------|
| `investment_committee` | 多空辩论 → 风控复盘 → PM 终审 |
| `global_equities_desk` | A 股 + 港美 + 加密研究员 → 全球策略师 |
| `crypto_trading_desk` | funding/basis + liquidation + flow → 风控 |
| `earnings_research_dsk` | 基本面 + 修正 + 期权 → 财报策略师 |
| `macro_rates_fx_desk` | 利率 + 外汇 + 商品 → 宏观 PM |
| `quant_strategy_desk` | 筛选 + 因子研究 → 回测 → 风控审计 |
| `technical_analysis_panel` | 经典 TA + 一目均衡 + 谐波 + 艾略特 + SMC → 共识 |
| `risk_committee` | 回撤 + 尾风险 + regime review → 签字 |
| `global_allocation_committee` | A 股 + 加密 + 港美 → 跨市场配置 |

`vibe-trading --swarm-presets` 列全 29 套。

### 7. Research Goal（研究目标）运行时

类似"task runner"：goal 带 acceptance criteria / evidence / claims / open items，agent 工具可以创建 goal + 挂证据，CLI `/goal` 直接进入 goal 模式，REST/MCP 暴露 goal 快照，Web UI 实时刷新。

> 这是"长程研究"的硬支撑——你说"研究 X"，它就把 X 拆成可验证的 goal，逐步推进。

## 典型场景

### 场景 A：A股 quant researcher

```bash
# 1. bench 整个 191 个 GTJA 因子在 CSI300 的有效性
vibe-trading alpha bench --zoo gtja191 --universe csi300 --period 2018-2025 --top 20

# 2. 选 IC 最高的 5 个，多因子合成
vibe-trading run -p "Combine the top 5 GTJA alphas on CSI300 into a single factor with equal weight, backtest 2018-2025, output report"

# 3. 导出到通达信，跑实盘
vibe-trading export --format tdx --strategy output
```

### 场景 B：Crypto quant

```bash
vibe-trading run -p "Build a funding-rate + liquidation heatmap strategy for BTC-USDT perp on OKX, 2024, evaluate with walk-forward"
```

### 场景 C：自检交易行为

```bash
vibe-trading --upload my_futu_export.csv
vibe-trading run -p "Analyze my trading behavior, extract my shadow strategy, run backtest on the rules, show me how much I left on the table"
```

### 场景 D：跨市场组合

```bash
vibe-trading run -p "Composite backtest: 60% CSI300 + 30% BTC + 10% Gold, 2018-2025, with monthly rebalance, output benchmark-relative return and IR"
```

### 场景 E：受限实盘（Robinhood）

```bash
# 1. 配 mandate
vibe-trading mandate set --symbols "AAPL,MSFT,GOOG" --max-order 100 --max-daily-trades 5

# 2. 连 Robinhood OAuth
vibe-trading connector use robinhood
vibe-trading connector login

# 3. 自然语言下达
vibe-trading run -p "Buy 10 AAPL if RSI<30 and 5-day MA crosses above 20-day MA"

# 4. 任何时候 kill switch
touch ~/.vibe-trading/KILL_SWITCH
```

## 边界与盲点

- **0.1.x 早期项目**：v0.1.9（2026-06-01）才发布，**慎上生产实盘**——官方也说"Experimental"
- **Robinhood 实盘需要美股账户 + 接受 mandate + 接受 broker 风险**
- **Alpha zoo 是公式级**：452 个 alpha 是**公开数学内容**，不是"独家因子"——你自己的 alpha 仍然要写
- **多市场数据源依赖公网**：yfinance / ccxt / tushare 都需要稳定网络，**严格断网环境跑不通**
- **中文支持目前只 README**：UI 硬切到英文（2026-05-25 起），需要中文 UI 自己 PR
- **量化研究 = 长期投入**：alpha bench 跑完只是开始，**真正赚钱来自因子组合 + 仓位 + 风控 + 纪律**
- **Futu / 老虎 / OKX / 币安** 虽然有 connector，但 paper/live 区分是**结构性**的（account ID / host / demo flag），配错会**直接下实盘**——必须仔细 check

## 与同类的对比

| 工具 | 维度 |
|------|------|
| **Vibe-Trading** | 通用交易研究 + 量化回测 + **受限实盘** + 影子账户 + 77 skills + 452 alphas + 29 swarms |
| OpenBB | 数据终端 + 因子研究，**无实盘** |
| QuantConnect | 强回测，**Web 端**，不本地 |
| Backtrader | 老牌回测，**单进程**，无 Agent |
| Freqtrade | 加密交易 bot，**重实盘**，无金融研究深度 |
| TradingAgents | 多 Agent 投研，**无回测无实盘** |
| Hikyuu | A 股框架，**无 Agent** |
| Qlib | 微软量化平台，**无 Agent** |

> Vibe-Trading 的真正差异化是"**AI Agent + 量化研究 + 受限实盘**"三位一体——同价位几乎找不到能覆盖这三个的方案。

## 隐私 / 合规要点

- **API key 配置**：本地 `.env`，**不传任何云端**
- **不要在非官方部署上用生产 API key**——官方明确警告过
- **Mandate 过期 = 自动失效**：避免"我忘了关 Agent"
- **Audit ledger 全留痕**：出问题能回溯
- **Paper account 优先**：所有新策略先在模拟盘跑

## 采用建议

### 适合谁

- 想做"自然语言 + AI Agent + 量化研究"一体化工作流的个人/小团队
- 已经有自己的交易记录（券商 export），想跑 Shadow Account
- 想跑 GTJA 191 / Qlib 158 / alpha101 这些公开因子库的量化研究员
- 美股 Robinhood 用户想试"AI Agent 帮我做受限实盘"

### 不适合谁

- 期望"开箱即用稳定赚钱"——量化研究永远是长期投入
- 完全没有量化基础——至少要会读 IC / IR / drawdown
- 强合规场景（国内券商 PB 实盘）——connector 主要支持海外 broker
- 完全离线 / 纯内网环境

### 落地顺序

1. **先 paper**：在 Robinhood / Alpaca / OKX 模拟盘跑 Shadow Account + alpha bench
2. **再小资金实盘**：mandate 设紧（max order 10、daily cap 1 单）
3. **多策略分散**：alpha zoo 选 IC 高的 3-5 个组合
4. **审计回看**：每月底翻 audit ledger，审视"Agent 干了啥"

## 一句话总结

> Vibe-Trading 是当下"**AI Agent + 量化研究 + 受限实盘**"三位一体最完整的开源方案；77 skills、452 alphas、29 swarms、36 MCP 工具形成生态闭环；Robinhood 实盘护栏做得最认真，量化研究深度对齐 Qlib；v0.1.x 早期项目，**模拟盘优先、小资金实盘、严密审 mandate**。

---

*📚 仓库地址：[HKUDS/Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) · 官网：[vibetrading.wiki](https://vibetrading.wiki/) · PyPI：[pypi.org/project/vibe-trading-ai](https://pypi.org/project/vibe-trading-ai/) · License：MIT · 出品方：HKUDS（Data Intelligence Lab @ HKU）*
