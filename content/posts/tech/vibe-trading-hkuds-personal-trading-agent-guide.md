---
title: "Vibe-Trading 完全指南：HKUDS 团队的「Vibe」式个人交易智能体（Agent）"
date: "2026-06-04T15:00:00+08:00"
slug: vibe-trading-hkuds-personal-trading-agent-guide
description: "HKUDS 开源的 Vibe-Trading 个人交易智能体工作台：88 个金融 skills、460+ alpha 因子、12 家券商连接器、9 个市场回测，含 Shadow Account 行为复盘与 Robinhood 受限实盘护栏解析。"
draft: false
categories: ["技术笔记"]
tags: ["量化交易", "AI Agent", "MCP"]
---

# Vibe-Trading 完全指南：HKUDS 团队的「Vibe」式个人交易智能体（Agent）

## 一、学习目标

读完本文，你能回答四个问题：

- Vibe-Trading 到底解决了什么问题？
- 它跟"聊天 + 跑代码"的通用 Agent 差在哪？
- 它的 452 个 alpha 因子和 Shadow Account 是怎么防"未来函数"的？
- Robinhood 实盘那套护栏，为什么是"显式承诺 + 文件级 kill switch + fail-closed"？

动手层面，你要能独立完成安装，跑一次因子回测。再上传交易记录做行为复盘，把受限实盘策略安全地接到模拟盘上。

- ✅ 说清 Vibe-Trading 的核心定位：它护城河在哪、跟 OpenBB / Qlib / TradingAgents 的差异
- ✅ 掌握 7 大核心能力（Skills / Alpha Zoo / Shadow Account / Broker Connector / Swarm / Research Goal / 持久化记忆）
- ✅ 完成 pip / Docker 两种安装，跑通 30 秒体验命令
- ✅ 用 Shadow Account 分析自己的交易记录，读懂"规则 vs 实际"的差距
- ✅ 用 Alpha Zoo 跑因子回测，看懂 IC / IR / alive / reversed / dead 分类
- ✅ 配置多 Agent Swarm 与研究目标（Research Goal）长程任务
- ✅ 排查常见问题（安装错误、数据源连接失败、权限配置）
- ✅ 在 mandate 约束下安全使用 Robinhood 等券商的受限实盘，理解 kill switch 与审计日志的作用

---

## 二、目录

- [一、学习目标](#一学习目标)
- [二、目录](#二目录)
- [三、核心判断](#三核心判断)
- [四、项目地图](#四项目地图)
- [五、安装与快速上手](#五安装与快速上手)
- [六、核心能力拆解](#六核心能力拆解)
- [七、典型场景](#七典型场景)
- [八、边界与盲点](#八边界与盲点)

- [九、与同类的对比](#九与同类的对比)
- [十、隐私合规要点](#十隐私合规要点)
- [十一、采用建议](#十一采用建议)
- [十二、自测题](#十二自测题)
- [十三、练习](#十三练习)
- [十四、进阶方向](#十四进阶方向)
- [十五、资料口径说明](#十五资料口径说明)
- [十六、一句话总结](#十六一句话总结)

---

## 三、核心判断

[Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) 来自香港大学数据智能实验室（HKUDS）。它是一个开源的个人交易研究工作台，风格被官方称为"Vibe"。

所谓 Vibe，指"用自然语言描述想法，工具链自动跑完研究 + 回测 + 风控 + 报告"。翻译成人话，就是"你负责想，它负责跑"。

它凭什么跟别的开源项目拉开差距？四个别人没拼齐的点：

1. **88 个金融 skills + 68 个研究工具**：A 股 / 港股 / 美股 / 加密全覆盖，19 个免费数据源按 IP 封禁风险自动 fallback，零配置也无单点故障
2. **460+ 个预置 alpha 因子**：来自 Qlib Alpha158、Kakushadze 101、国泰君安 191 与学术因子（Fama-French / Carhart / PIT 安全基本面因子）。一行命令 `vibe-trading alpha bench --zoo gtja191` 就能跑完一个因子动物园
3. **Shadow Account（影子账户）**：解析你自己过去的交易记录 → 提取行为规则 → 用规则跑回测。它 diff 出的不是收益率，而是"按你实际执行的规则，本来能赚多少、在哪一步丢了钱"
4. **Connector-first Broker Architecture（券商连接器优先）**：同一套 CLI（命令行工具）在 12 家券商之间切换（IBKR / Robinhood / 富途 / 老虎 / OKX / 币安 / Trading 212 等）。Robinhood 实盘带硬护栏：mandate 承诺 + 文件级 kill switch + fail-closed pre-trade + 审计日志 + 自动过期

一句话概括：**Vibe-Trading = "AI Agent + 量化研究工作流 + 受限实盘"三位一体**。想自己写交易想法、Agent 帮你跑？它是最完整的开源方案。

需要先泼一盆冷水：它定位是研究、模拟、回测和审计工具，实盘是 opt-in 且默认只读的。它不托管资金、不运行交易执行场所，也不构成投资建议。把预期放在"研究加速器"上，而不是"自动印钞机"上。

---

## 四、项目地图

| 维度 | 关键信息 |
|------|----------|
| 仓库 | [HKUDS/Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) |
| 官网 | [vibetrading.wiki](https://vibetrading.wiki/) |
| 文档 | [vibetrading.wiki/docs](https://vibetrading.wiki/docs/) |
| PyPI | [pypi.org/project/vibe-trading-ai](https://pypi.org/project/vibe-trading-ai/) |
| 许可证 | MIT |
| 维护方 | HKUDS（Data Intelligence Lab @ HKU） |
| 当前版本 | v0.1.12（2026-07-22 发布） |

### 4.1 能力矩阵

研究能力一览：

| 维度 | 实现 |
|------|------|
| 自然语言研究 | 多 Agent loop（Plan → Ground → Execute → Validate → Deliver） |
| 多市场回测 | A 股 / 美股 / 港股 / 印度 / 韩国 / 加密 / 外汇 / 期权 / USD-M 永续，共 9 个市场 |
| 免费数据源 | 19 个（tushare / yfinance / akshare / mootdx / ccxt / 腾讯 / 东财 / OKX / 币安等），自动 fallback |
| 付费数据源 | QVeris 数据市场，63+ 家提供商 |
| Alpha 因子 | **460+** 个预置（Qlib158 + Kakushadze 101 + GTJA 191 + 学术 + PIT） |
| Swarm 预设 | 30 套多 Agent 团队（投资委员会、量化台、加密交易台、宏观等） |
| IM 渠道 | 16 个（Telegram / Slack / Discord / QQ / 微信 / 飞书 / 钉钉 / Teams / email 等） |

工程底座一览：

| 维度 | 实现 |
|------|------|
| 后端 | Python 3.11+ / FastAPI |
| 前端 | React 19 |
| Broker | 12 家（IBKR、Robinhood、Tiger、Longbridge、Alpaca、OKX、Binance、Futu、Trading 212、Dhan、Shoonya、MT5-Exness） |
| Skills | **88 个**金融 skills，分 9 大类 |
| 研究工具 | 68 个（Research Autopilot），18 个只读数据工具经 MCP 暴露 |
| 导出 | Pine Script v6 / 通达信 / MetaTrader 5 / vnpy / MCP 服务 |
| 跨平台 | Docker 非 root 用户运行；macOS / Linux / Windows |

---

## 五、安装与快速上手

### 5.1 pip 安装

```bash
pip install vibe-trading-ai
```

可选扩展按需安装：

```bash
pip install "vibe-trading-ai[telegram]"    # Telegram 渠道
pip install "vibe-trading-ai[deepseek]"    # DeepSeek 原生适配器
pip install "vibe-trading-ai[harmonic]"    # 谐波形态检测
```

### 5.2 Docker 部署

```bash
git clone https://github.com/HKUDS/Vibe-Trading.git
cd Vibe-Trading
cp agent/.env.example agent/.env    # 编辑 .env，至少填 OPENAI_API_KEY
docker compose up --build
```

启动后打开 `http://localhost:8899`，前后端都在一个容器里。依赖用哈希锁定（hash-locked），数据落在命名卷，升级可回溯。

### 5.3 30 秒体验

```bash
# 自然语言研究：写想法 → 自动选数据源/技能 → 回测 → 出报告
vibe-trading run -p "Backtest a BTC-USDT 20/50 moving-average strategy for 2024, summarize return and drawdown, then export the report"

# 一行 bench 整个 alpha zoo
vibe-trading alpha bench --zoo gtja191 --universe csi300 --period 2018-2025 --top 20
```

### 5.4 上传自己的交易记录

```bash
vibe-trading --upload trades_export.csv
vibe-trading run -p "Analyze my trading behavior, extract my shadow strategy, and compare it with my actual trades"
```

支持同花顺 / 东方财富 / 富途 / 通用 CSV 四种格式。

### 5.5 四种交互方式

项目把同一套能力暴露在四个入口，按场景挑：

- **CLI（命令行工具）**：`vibe-trading` 开头的全部命令，适合脚本化和本地研究
- **Web UI**：三栏式界面，左侧策略树 + 中央对话流 + 右侧回测图表，适合边看边调
- **REST API（表述性状态转移，应用程序接口）**：`vibe-trading serve` 起服务后暴露 HTTP 接口，适合二次开发
- **MCP 服务**：接入 Claude Desktop / Cursor / OpenClaw 等 MCP 客户端，让现有 Agent 直接调金融工具

---

## 六、核心能力拆解

### 6.1 Skills 库（88 个金融技能 / 9 大类）

先澄清一个命名上的坑：这里的 Strategy 分类指交易策略的生成与筛选，不是设计模式里的策略模式（Strategy Pattern）。

顺便说一句，这种命名冲突在金融软件里很常见，遇到别慌，看上下文就知道指的是哪个。

研究类 skill：

| 分类 | 示例 |
|------|------|
| Data Source（数据源） | `data-routing` / `tushare` / `yfinance` / `okx-market` / `akshare` / `mootdx` / `ccxt` |
| Strategy（策略） | `strategy-generate` / `cross-market-strategy` / `technical-basic` / `candlestick` / `ichimoku` / `elliott-wave` / `smc` / `multi-factor` / `ml-strategy` |
| Analysis（分析） | `factor-research` / `macro-analysis` / `global-macro` / `valuation-model` / `earnings-forecast` / `credit-analysis` / `dividend-analysis` |
| Asset Class（资产类别） | `options-strategy` / `options-advanced` / `convertible-bond` / `etf-analysis` / `asset-allocation` / `sector-rotation` |
| Crypto（加密） | `perp-funding-basis` / `liquidation-heatmap` / `stablecoin-flow` / `defi-yield` / `onchain-analysis` |

交易与工具类 skill：

| 分类 | 示例 |
|------|------|
| Flow（资金流） | `hk-connect-flow` / `us-etf-flow` / `edgar-sec-filings` / `financial-statement` / `adr-hshare` |
| Tool（工具） | `backtest-diagnose` / `report-generate` / `pine-script` / `doc-reader` / `web-reader` / `vnpy-export` / `alpha-zoo` |
| Research（研究） | `strategy-dev-manager` / `correlation-regime` / `earnings-revision` / `pair-trading` / `sentiment-analysis` |
| Risk（风控） | `ashare-pre-st-filter` |

这 88 个 skill 是 Vibe-Trading 跟通用 Agent 的核心分水岭。通用 Agent 拿到"分析一下宁德时代"，只能靠通用推理硬猜。

这里每个 skill 是带数据接入、参数约定和输出契约的模块：`ashare-pre-st-filter` 会真的去拉 ST 名单，`perp-funding-basis` 会真的去取资金费率。它是**有金融领域纵深的 Agent**，不是"聊天 + 跑代码"。

### 6.2 Alpha Zoo（460+ 个预置 alpha 因子）

| Zoo | 来源 | 许可证 |
|-----|------|--------|
| `qlib158` | Microsoft Qlib `Alpha158` | Apache-2.0 |
| `alpha101` | Kakushadze 2015（arXiv:1601.00991） | 数学公式 |
| `gtja191` | 国泰君安 2014 短周期因子报告 | 数学公式 |
| `academic` | Fama-French 5 + Carhart 动量 + Frazzini-Pedersen BAB + Jegadeesh 反转 + Amihud 非流动性 + PIT 安全基本面因子 | 学术文献 |

一行命令跑完整个 zoo：

```bash
vibe-trading alpha bench --zoo gtja191 --universe csi300 --period 2018-2025 --top 20
```

输出里每个 alpha 会打上 **IC / IR / alive / reversed / dead** 五类标签。这组标签值得花 30 秒理解，它决定你该不该用这个因子：

- **IC（信息系数）**：因子值与未来收益的秩相关，衡量"这个因子预测方向对不对"，绝对值越大越好，0 附近说明跟扔硬币差不多
- **IR（信息比率）**：IC 的均值除以波动，衡量"预测的稳定性"，IR 高说明不是偶尔蒙对一次
- **alive**：IC 显著且方向正确，可以直接进组合
- **reversed**：IC 显著但方向和原始公式反了——这类因子别扔，**取反号往往就是有效因子**，很多量化团队靠这个白捡 alpha
- **dead**：IC 不显著，跟踪的是市场 beta 的伪 alpha，剔除

防止因子"作弊"的防护是这一层最硬核的设计，分三道闸：

- **AST purity gate**：因子表达式先编译成抽象语法树（AST），再逐算子检查，从语法层面禁掉未来数据。比如"当天收盘后才知道的当日成交额"被用在当天信号里，这类前视引用直接被拒
- **300-row lookahead sentinel test**：往序列里插入"未来会发生的事件"哨兵，跑一遍回测，看因子是否提前反应。如果因子在事件发生前就异动，说明存在数据泄漏，测试必挂
- **`pytest-socket` 网络 kill-switch**：测试进程里直接禁网。pytest-socket 库在 Python 层面拦截套接字（socket）调用，防止"测试偷偷联网拉未来数据"这种不可能通过代码审查的作弊

另外，社区 PR 走 DCO 工作流：每个贡献者要签 Developer Certificate of Origin（开发者原创证书），保证因子来源可追溯。

### 6.3 Shadow Account（影子账户）

这是 Vibe-Trading 最具创意、也最容易被低估的功能。它解决一个真实痛点：**你实盘做了几百笔交易，但你说不清自己的交易系统到底是什么**。直觉是"低买高卖"，实际上可能一直在追涨杀跌。Shadow Account 把"你以为的"和"你实际做的"都摆到桌面上：

| 步骤 | Agent 输出 |
|------|------------|
| 1. 读交易记录 | 解析同花顺 / 东财 / 富途 / 通用 CSV |
| 2. 行为画像 | 持仓天数、胜率、盈亏比、回撤、处置效应、过度交易、追涨杀跌、锚定偏差 |
| 3. 规则提取 | 把反复出现的进出场动作转成显式策略（含 RSI、前 5 日收益等条件入场） |
| 4. 跑影子 | 用提取出的规则回测，高亮规则破坏 / 提前出场 / 错过信号 / 替代交易路径 |
| 5. 出报告 | HTML / PDF 报告 + 可复用的策略代码，可存档或再迭代 |

两个工程细节让它比"拍脑袋复盘"可信：

- **PIT（Point-in-Time，时点）安全的入场上下文**：规则里记录的是入场那一刻的 `entry_rsi14`、`prior_5d_return` 等快照，而不是用事后才知道的数据补写入场理由——复盘时不会"事后诸葛亮"
- **规则与代码共享同一套 `PRICE_FEATURES` 契约**：提取出的规则和生成的信号引擎代码字段一致，规则说得通，代码就能跑，不存在"报告是一套、实现是另一套"

通俗讲：自己实盘 + 自己跑一遍规则回测，diff 出"按规则 vs 实际"的差距。这是行为金融学和量化的混合产物：行为金融学解释"你为什么会亏"，回测引擎量化"你本来能赚多少"。

### 6.4 Broker Connector 架构（券商连接器优先）

v0.1.9 落地的核心架构变更：**所有券商统一走 connector profile**。同一套命令，切换券商只改一个参数：

```bash
vibe-trading connector list                  # 列所有可用 connector
vibe-trading connector use <name>            # 切换
vibe-trading connector check                 # 健康检查
vibe-trading connector account               # 看账户
vibe-trading connector positions             # 看持仓
vibe-trading connector orders                # 看订单
vibe-trading connector quote                 # 看报价
```

为什么是"connector-first"而不是每个券商写死一个插件？因为券商接口千差万别：有的是 REST、有的是 FIX、有的是 OAuth MCP。但交易语义是通用的：账户、持仓、订单、报价、历史。

接入层按适配器模式（adapter）组织：把通用语义抽成 profile，把差异留在 adapter 里。新接一家券商只写 adapter，上层研究逻辑一行不改。截止 v0.1.12 已支持 12 家：

国际与加密券商：

| Broker | 类型 | 状态 |
|--------|------|------|
| **IBKR（TWS/Gateway 网关）** | 本地只读 | 稳定 |
| **Robinhood** | OAuth MCP 实盘 | **受 mandate 约束** |
| Tiger（老虎） | 模拟 + 实盘 | 可用 |
| Longbridge（长桥） | 模拟 + 只读 | API 不区分 paper/live |
| Alpaca | 模拟 + 实盘 | 受 mandate 约束 |
| OKX | 模拟 + 实盘 | 受 mandate 约束 |

其他地区券商：

| Broker | 类型 | 状态 |
|--------|------|------|
| Binance | 模拟 + 实盘 | 受 mandate 约束 |
| Futu（富途） | 模拟 + 实盘 | 受 mandate 约束 |
| Trading 212 | 模拟 + 实盘 | 可用 |
| Dhan / Shoonya | 印度券商 | 模拟 + 实盘 |
| MetaTrader 5（Exness） | 外汇/贵金属 | 可用 |

### 6.5 Robinhood 实盘护栏（关键安全设计）

Robinhood 是**实盘**支持的代表。它的安全设计值得单独拆开讲，因为这是"AI 托管真金白银"这类系统的范本。

设计目标要回答一个问题：**Agent 拿到下单权限后，怎么保证它无法造成超出你预期的损失？** 答案是五层叠加：

- **Mandate（用户承诺）**：你自己限定 symbol universe / 单笔 order size / 总 exposure / 杠杆 / 每日交易数上限。Agent 的命令只在 mandate 范围内有效
- **Kill switch（紧急停止）**：文件系统级别的"立即停"，`touch ~/.vibe-trading/KILL_SWITCH` 一行命令，Agent 下一次动作前检查到文件就冻结，不依赖 UI、不依赖网络
- **Fail-closed pre-trade gate（下单前自检）**：每笔订单执行前先过校验，任何一项不满足直接拒绝下单——宁可错过也不越界，这是 fail-closed 和 fail-open 的本质区别
- **Audit ledger（审计账本）**：所有动作（谁、什么时间、什么指令、结果如何）全量留痕，出问题能回溯
- **Auto-expire mandate（自动过期）**：承诺有过期时间，到点自动失效，避免"我忘了关 Agent"这种最朴素的翻车方式

v0.1.12 又加了一层 **PreTradeAdvisoryInterface**：下单前，Agent 把"准备做什么"发给一个咨询接口过一遍，自查订单是否超限、是否在禁售名单内。相当于下单前多一道人工/规则复查。

> ⚠️ 官方明确标注：Experimental / use at your own risk。**没有资金托管，没有交易所权限**——broker 持资执行，Vibe-Trading 只传递意图。出问题的是你的券商账户，不是它的服务器。

### 6.6 Swarm（多 Agent 团队）

为什么需要多 Agent？因为单 Agent 研究一个标的时，很容易"自己提假设自己验证"，缺少对抗。Swarm 把不同角色的 Agent 组织成委员会，让结论经过辩论和复核。30 套预设覆盖主流场景：

投研委员会类预设：

| Preset | 工作流 |
|--------|--------|
| `investment_committee` | 多空辩论 → 风控复盘 → PM 终审 |
| `global_equities_desk` | A 股 + 港美 + 加密研究员 → 全球策略师 |
| `crypto_trading_desk` | funding/basis + liquidation + flow → 风控 |
| `earnings_research_desk` | 基本面 + 修正 + 期权 → 财报策略师 |
| `macro_rates_fx_desk` | 利率 + 外汇 + 商品 → 宏观 PM |

策略与风控类预设：

| Preset | 工作流 |
|--------|--------|
| `quant_strategy_desk` | 筛选 + 因子研究 → 回测 → 风控审计 |
| `technical_analysis_panel` | 经典 TA + 一目均衡 + 谐波 + 艾略特 + SMC → 共识 |
| `risk_committee` | 回撤 + 尾风险 + regime review → 签字 |
| `global_allocation_committee` | A 股 + 加密 + 港美 → 跨市场配置 |

`vibe-trading --swarm-presets` 列全 30 套。

Swarm 引擎按 DAG 编排：某些 worker 的产出是另一些 worker 的输入，依赖不满足就阻塞。每个 worker 的状态（waiting / running / done / failed / blocked / retrying）实时渲染在 Web UI 和聊天时间线里，谁卡住了、卡在哪一步，一眼可见。

### 6.7 Research Goal（研究目标）运行时

类似"task runner"的长期任务机制。goal 自带四样东西：acceptance criteria（验收标准）、evidence（证据）、claims（结论）、open items（待办）。Agent 工具可以创建 goal 并挂证据；CLI 的 `/goal` 命令直接进入 goal 模式；REST/MCP 暴露 goal 快照；Web UI 实时刷新。

它的价值在于把"研究 X"这种模糊指令变成可验证的推进过程："研究 X"被拆成若干可验证目标，每完成一个挂上证据，卡住的地方明确标成 open item。长程研究（比如"评估一个行业的所有标的"）不会做着做着变成一团乱麻。

### 6.8 Research Autopilot（研究自动驾驶）

v0.1.10 之后新增的端到端流程：**假设 → 研究目标 → 回测**，中间不需要人盯着。支持 cron 定时执行——你可以让系统每周一自动跑一遍"沪深 300 动量因子周度复检"。结果落到 run card（运行卡），记录研究参数、数据版本、结果，保证可复现。

### 6.9 持久化记忆（Persistent Memory）

项目内置分层记忆（Tier 2 结构）：短期记忆记录当前会话上下文，长期记忆沉淀跨会话的事实与结论。记忆带质量评分，按 Ebbinghaus 遗忘曲线衰减，支持可选 GC。

意义在于：上周你让它研究过的行业、你纠正过它的偏好，这周再开新会话它还记得，不用重复交代。---

## 七、典型场景

### 场景 A：A 股量化研究员

```bash
# 1. bench 整个 191 个 GTJA 因子在 CSI300 的有效性
vibe-trading alpha bench --zoo gtja191 --universe csi300 --period 2018-2025 --top 20

# 2. 选 IC 最高的 5 个，多因子合成
vibe-trading run -p "Combine the top 5 GTJA alphas on CSI300 into a single factor with equal weight, backtest 2018-2025, output report"

# 3. 导出到通达信，接本地实盘流程
vibe-trading export --format tdx --strategy output
```

### 场景 B：加密量化

```bash
vibe-trading run -p "Build a funding-rate + liquidation heatmap strategy for BTC-USDT perp on OKX, 2024, evaluate with walk-forward"
```

资金费率策略的要点在这里：永续合约的资金费率是"持仓者给对手方付利息"的显式价格。费率极端时，往往对应市场情绪极端，是比价格本身更干净的情绪信号。

### 场景 C：自检交易行为

```bash
vibe-trading --upload my_futu_export.csv
vibe-trading run -p "Analyze my trading behavior, extract my shadow strategy, run backtest on the rules, show me how much I left on the table"
```

"how much I left on the table"（我在桌上留下了多少钱）是 Shadow Account 报告里最扎心的一行，也最有行动价值。它把"交易纪律问题"翻译成了具体金额。

### 场景 D：跨市场组合

```bash
vibe-trading run -p "Composite backtest: 60% CSI300 + 30% BTC + 10% Gold, 2018-2025, with monthly rebalance, output benchmark-relative return and IR"
```

### 场景 E：受限实盘（Robinhood）

```bash
# 1. 配 mandate，先把笼子焊死
vibe-trading mandate set --symbols "AAPL,MSFT,GOOG" --max-order 100 --max-daily-trades 5

# 2. 连 Robinhood OAuth
vibe-trading connector use robinhood
vibe-trading connector login

# 3. 自然语言下达（只在 mandate 范围内生效）
vibe-trading run -p "Buy 10 AAPL if RSI<30 and 5-day MA crosses above 20-day MA"

# 4. 任何时候 kill switch
touch ~/.vibe-trading/KILL_SWITCH
```

### 场景 F：定时研究（Autopilot）

```bash
vibe-trading schedule add --cron "0 9 * * 1" -p "Weekly CSI300 momentum factor health check, top 10 changes, output run card"
```

每周一早上 9 点自动跑因子健康检查，结果落 run card 可复现——适合长期跟踪策略是否失效。

---

## 八、边界与盲点

- **0.1.x 早期项目**：v0.1.12（2026-07-22）仍是 0.1.x，**慎上生产实盘**——官方自己也标 Experimental。每周都在高频迭代，升级前先看 changelog
- **Robinhood 实盘需要美股账户 + 接受 mandate + 接受 broker 风险**；Docker 镜像建议用官方 digest 锁定版本，不要 tag 漂移
- **Alpha zoo 是公式级**：460+ 个 alpha 是**公开数学内容**，不是"独家因子"——它帮你省的是实现和回测时间，不是提供圣杯，你自己的 alpha 仍然要写
- **多市场数据源依赖公网**：yfinance / ccxt / tushare 都需要稳定网络，**严格断网环境跑不通**；免费数据源有 IP 封禁风险，fallback 链按风险排序自动切换
- **中文支持目前只到 README**：Web UI 硬切英文（2026-05-25 起），要中文界面得自己 PR
- **量化研究 = 长期投入**：alpha bench 跑完只是开始，**真正赚钱来自因子组合 + 仓位 + 风控 + 纪律**——工具只负责把"想法的验证成本"降下来
- **Futu / 老虎 / OKX / 币安** 的 paper/live 区分是**结构性**的（account ID / host / demo flag），配错会**直接下实盘**——上线前必须 `connector check` 核对账户环境
- **谨防仿冒资产**：官方从未发行或背书任何代币 / memecoin，X 账号 `VibeTrading_HKU`、Virtuals 项目 101845、代币合约 0x640B... 均非官方；社区出现过钓鱼 Discord 邀请，只认官方服务器

---

## 九、与同类的对比

工作台与回测类：

| 工具 | 定位 | 与 Vibe-Trading 的差异 |
|------|------|------|
| **Vibe-Trading** | 通用交易研究 + 量化回测 + **受限实盘** + 影子账户 | 88 skills + 460 alphas + 30 swarms + 12 brokers |
| OpenBB | 数据终端 + 因子研究 | **无实盘**，无 Agent |
| QuantConnect | 云端强回测平台 | **Web 端**，不本地，无自然语言 Agent |
| Backtrader | 老牌回测框架 | **单进程**，无 Agent，无因子库 |

Agent 与框架类：

| 工具 | 定位 | 与 Vibe-Trading 的差异 |
|------|------|------|
| Freqtrade | 加密交易 bot | **重实盘**，无金融研究深度 |
| TradingAgents | 多 Agent 投研 | **无回测无实盘** |
| Hikyuu | A 股量化框架 | **无 Agent**，无多市场 |
| Qlib | 微软量化平台 | **无 Agent**，无实盘 |

Vibe-Trading 真正的差异化，是"**AI Agent + 量化研究 + 受限实盘**"三位一体。单看任何一环，都有更强的专用工具：回测不如 QuantConnect，实盘不如 Freqtrade。但把三环收进一个自然语言工作台的，目前开源世界里没有第二家。

---

## 十、隐私合规要点

- **API key 配置**：写在本地 `.env`，**不上传任何云端**；不要在非官方部署上用生产 API key
- **Mandate 过期 = 自动失效**：防止"我忘了关 Agent"这类最朴素的失控
- **Audit ledger 全留痕**：所有动作可回溯，这是出事时自证清白的唯一凭据
- **Paper account 优先**：所有新策略先在模拟盘跑，确认行为符合预期再接实盘
- **安全审计已收尾**：2026-07-10 完成外部安全审计，10 项发现全部修复——回测沙箱用 AST 加固（禁网络/子进程/eval），另有 CSRF（跨站请求伪造）/ SSRF 防护和 API 认证加固
- **认准官方资产**：官方从无代币；任何"Vibe-Trading 代币""官方群拉你连钱包"的消息都是诈骗

---

## 十一、采用建议

### 11.1 适合谁

- 想做"自然语言 + AI Agent + 量化研究"一体化工作流的个人 / 小团队
- 已有自己的交易记录（券商 export），想跑 Shadow Account 做行为复盘
- 想跑 GTJA 191 / Qlib 158 / alpha101 这些公开因子库的量化研究员
- 美股 Robinhood 用户想试"AI Agent 帮我做受限实盘"

### 11.2 不适合谁

- 期望"开箱即用稳定赚钱"——量化研究永远是长期投入，工具省的是验证成本不是亏钱
- 完全没有量化基础——至少要能读懂 IC / IR / drawdown
- 强合规场景（国内券商 PB 实盘）——connector 主要支持海外 broker
- 完全离线 / 纯内网环境

### 11.3 落地顺序

1. **先 paper**：在 Robinhood / Alpaca / OKX 模拟盘跑 Shadow Account 和 alpha bench
2. **再小资金实盘**：mandate 设紧（max order 10、daily cap 1 单），跑两周看 audit ledger
3. **多策略分散**：alpha zoo 选 IC 高的 3-5 个组合，区分 alive / reversed
4. **审计回看**：每月底翻 audit ledger，审视"Agent 干了啥、有没有越界"

---

## 十二、自测题

### 12.1 Vibe-Trading 的核心差异化是什么？

<details>
<summary>点击查看答案</summary>

护城河在四件事：
1. **88 个金融 skills + 68 个研究工具**：A 股 / 港股 / 美股 / 加密全覆盖
2. **460+ 个预置 alpha 因子**：一行命令跑完一个因子动物园
3. **Shadow Account**：解析你自己过去的交易记录，提取规则并回测，diff 出"规则 vs 实际"
4. **Connector-first Broker Architecture**：同一套 API 切换 12 家券商，Robinhood 实盘带硬护栏

</details>

### 12.2 alpha 因子分类里 reversed 是什么意思？该不该扔掉？

<details>
<summary>点击查看答案</summary>

reversed 表示因子的 IC 显著但方向与原始公式相反。**不要扔，取反号往往就是有效因子**——很多量化团队靠这个白捡 alpha。真正要剔除的是 dead（IC 不显著，只是跟踪市场 beta 的伪 alpha）。

</details>

### 12.3 Alpha Zoo 靠什么防止"未来函数"（lookahead）作弊？

<details>
<summary>点击查看答案</summary>

三道闸：
1. **AST purity gate**：因子表达式先编译成 AST 逐算子检查，语法层面禁掉未来数据引用
2. **300-row lookahead sentinel test**：插入"未来事件"哨兵，跑回测看因子是否提前反应，有泄漏必挂
3. **`pytest-socket` 网络 kill-switch**：测试进程禁网，防止偷偷联网拉数据

</details>

### 12.4 Shadow Account 的工作流程是什么？

<details>
<summary>点击查看答案</summary>

1. **读交易记录**：解析同花顺 / 东财 / 富途 / 通用 CSV
2. **行为画像**：持仓天数、胜率、盈亏比、回撤、处置效应、过度交易、追涨杀跌、锚定偏差
3. **规则提取**：把反复出现的进出场动作转成显式策略（含 RSI、前 5 日收益等条件入场）
4. **跑影子**：用提取出的规则回测，高亮规则破坏 / 提前出场 / 错过信号
5. **出报告**：HTML / PDF 报告 + 可复用策略代码

关键在 PIT（Point-in-Time）安全的入场上下文：规则记录入场那一刻的 `entry_rsi14`、`prior_5d_return` 快照，复盘不会"事后诸葛亮"。

</details>

### 12.5 Robinhood 实盘的护栏设计是什么？

<details>
<summary>点击查看答案</summary>

五层叠加 + 一层咨询：
1. **Mandate（用户承诺）**：自己设定 symbol universe / order size / exposure / leverage / daily cap
2. **Kill switch**：文件系统级"立即停"，`touch ~/.vibe-trading/KILL_SWITCH`
3. **Fail-closed pre-trade gate**：下单前自检，不通过直接拒——宁可错过也不越界
4. **Audit ledger**：所有动作全留痕，可回溯
5. **Auto-expire mandate**：承诺过期自动失效
6. **PreTradeAdvisoryInterface（v0.1.12）**：下单前把"准备做什么"过一遍咨询接口

</details>

### 12.6 Vibe-Trading 和 OpenBB 有什么区别？

<details>
<summary>点击查看答案</summary>

1. **实盘支持**：Vibe-Trading 有受限实盘（mandate 约束），OpenBB 无实盘
2. **Agent 支持**：Vibe-Trading 有 AI Agent 与多 Agent Swarm，OpenBB 无
3. **Alpha 因子**：Vibe-Trading 有 460+ 预置，OpenBB 无
4. **Shadow Account**：Vibe-Trading 有行为复盘，OpenBB 无

</details>

---

## 十三、练习

### 练习 1：安装 Vibe-Trading 并跑 Alpha Zoo

**任务**：在你的系统上安装 Vibe-Trading，跑 GTJA 191 因子在 CSI300 的回测，并解释 top 20 里 reversed 因子的处理方式。

**步骤**：
1. 运行 `pip install vibe-trading-ai`
2. 运行 `vibe-trading alpha bench --zoo gtja191 --universe csi300 --period 2018-2025 --top 20`
3. 观察输出的 IC / IR / alive / reversed / dead 分类
4. 选 IC 最高的 5 个因子，多因子合成并回测

**验收标准**：命令跑通且输出含五类标签；能说出为什么 reversed 因子取反后值得测试而不是直接丢弃。

### 练习 2：使用 Shadow Account 分析自己的交易记录

**任务**：上传你自己的交易记录（或使用示例 CSV），用 Shadow Account 分析交易行为。

**步骤**：
1. 准备一个交易记录 CSV（或使用示例）
2. 运行 `vibe-trading --upload trades_export.csv`
3. 运行 `vibe-trading run -p "Analyze my trading behavior, extract my shadow strategy, run backtest on the rules, show me how much I left on the table"`
4. 查看 HTML / PDF 报告，找到"left on the table"金额

**验收标准**：报告包含行为画像与影子策略回测；你能指出自己交易中至少一个可改进点（如处置效应、过度交易）。

### 练习 3：配置 Robinhood 模拟盘并跑受限实盘

**任务**：配置 Robinhood connector，在模拟盘跑一个简单的策略，并验证 kill switch 生效。

**步骤**：
1. 注册 Robinhood 账户（如果没有）
2. 运行 `vibe-trading connector use robinhood`
3. 运行 `vibe-trading connector login`（OAuth 授权）
4. 配 mandate：`vibe-trading mandate set --symbols "AAPL,MSFT" --max-order 10 --max-daily-trades 3`
5. 跑模拟盘：`vibe-trading run -p "Buy 10 AAPL if RSI<30"`
6. 创建 kill switch 文件，再发一条指令，确认被冻结：`touch ~/.vibe-trading/KILL_SWITCH`
7. 查看审计日志：`cat ~/.vibe-trading/audit_ledger.log`

**验收标准**：mandate 外指令被拒；kill switch 后指令被冻结；审计日志里能看到每一步动作。

---

## 十四、进阶方向

### 14.1 理解量化交易的基础理论

- 阅读官方文档（https://vibetrading.wiki/docs/），重点看 data-sources 和 shadow-account 两篇
- 理解 IC / IR / alive / reversed / dead 分类的业务含义
- 研究 Alpha Zoo 四个池的来源差异：Qlib 因子偏价量统计、Kakushadze 101 偏公式化、GTJA 191 偏短周期、学术因子偏经济逻辑

### 14.2 掌握 Shadow Account 的行为分析机制

- 研究行为画像各维度（处置效应、过度交易、锚定偏差）的行为金融学原理
- 理解 PIT 入场上下文与 PRICE_FEATURES 契约的设计动机
- 学习如何解读"规则 vs 实际"差距报告，把复盘结论转成交易纪律

### 14.3 构建自定义金融 Skills

- 学习 88 个 Skills 的分层结构与 9 大类职责边界
- 拆解一个现有 skill（如 `ashare-pre-st-filter`），理解它的数据接入与输出契约
- 构建自己的 Skill 并注册到系统

### 14.4 参与 Alpha Zoo 的贡献

- 在 GitHub 上提交 Issues 和 Pull Request（拉取请求）
- 贡献新的 alpha 因子：数学公式 + 回测验证 + DCO 签名
- 参与社区讨论（官方 Discord）

### 14.5 研究多 Agent Swarm 的协作机制

- 研究 `investment_committee` 的多空辩论与 PM 终审机制
- 理解 `risk_committee` 的签字门禁在流程中的位置
- 学习用 YAML 自定义 Swarm 预设与 DAG 依赖

### 14.6 安全使用券商实盘

- 研究 Connector-first 架构与 mandate 设计
- 验证 fail-closed pre-trade gate 与 kill switch 的边界行为
- 学习审计日志的解读与月度复盘方法

### 14.7 构建生产级量化系统

- 设计多因子组合策略，注意 alive / reversed 因子的差异化处理
- 实现实时仓位管理与风控（mandate 动态收紧）
- 用定时研究（Autopilot）做策略健康监控，策略失效及时下线

---

## 十五、资料口径说明

1. **信息来源**：本文参考 Vibe-Trading 官方 GitHub 仓库、官网（vibetrading.wiki）、PyPI 页面与公开技术文档，数字以官方为准
2. **版本时效性**：本文基于 2026-08-02 时点的 v0.1.12（2026-07-22 发布）。项目每周高频迭代，API / 命令 / 功能可能随版本变化，使用前请核对官方文档最新版
3. **技术细节验证**：Shadow Account 流程、Alpha Zoo 防护、Robinhood 护栏等细节基于官方文档描述，未在真实环境逐一验证；关键决策前请自行验证
4. **性能数据未验证**：本文不包含独立性能测试。alpha 的 IC/IR 分数、回测准确性、券商延迟都依赖你的数据源与网络环境，需要自己跑一遍
5. **安全建议边界**：文中实盘护栏是项目官方设计，不是投资建议。高风险场景请咨询专业合规与安全团队
6. **数字口径**：skills（88）、alpha（460+）、broker（12）、swarm（30）、市场（9）等数字随版本演进，文中已标注版本来源；同一时点不同渠道（README / PyPI / 官网 docs）口径可能略有差异，以仓库 README 与 `vibe-trading --help` 实际输出为准

---

## 十六、一句话总结

> Vibe-Trading 是目前"**AI Agent + 量化研究 + 受限实盘**"三位一体覆盖最全的开源方案：88 个 skills、460+ 个 alphas、30 套 swarms、12 家券商连接器把研究流程串完整，Shadow Account 把交易行为量化成可复盘的差距，Robinhood 实盘护栏是"AI 托管真金白银"的教科书设计；但它是 v0.1.x 早期项目，**模拟盘优先、小资金实盘、严审 mandate、常翻 audit ledger**。

---

*📚 仓库：[HKUDS/Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) · 官网：[vibetrading.wiki](https://vibetrading.wiki/) · 文档：[vibetrading.wiki/docs](https://vibetrading.wiki/docs/) · PyPI：[pypi.org/project/vibe-trading-ai](https://pypi.org/project/vibe-trading-ai/) · License：MIT · 出品方：HKUDS（Data Intelligence Lab @ HKU）*
