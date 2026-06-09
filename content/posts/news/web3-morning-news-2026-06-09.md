---
title: "Web3早报2026-06-09"
date: 2026-06-09T12:17:00+08:00
slug: web3-morning-news-2026-06-09
description: "2026年6月9日 Web3早报（补做，cron9c412432 漏跑）：BTC/ETH/SOL/XRP/ADA 全线小幅企稳（12:22 BJT 抓取 CMC：BTC$62,848.66 / ETH$1,668.13 / SOL$66.07 / XRP$1.15 / ADA$0.1662 / BNB$598.42）；Strategy重新增持1,550 BTC带动币价重回6.3 万美元、Citrini Research 看涨 Hyperliquid、Aave84.5 亿美元挤兑后创始人归因第三方、MetaMask 推出 AI代理钱包、SBF 正式请求特赦、Galaxy下调 CLARITY Act 通过概率至60%、现货 BTC ETF连续4周失血17亿美元。"
draft: false
categories: ["行业快讯"]
tags: ["Web3", "BTC", "Strategy", "Hyperliquid", "MetaMask", "SBF"]
hiddenFromHomePage: true
---

🦞每日08:00自动更新

---

## 📊 市场速览

|币种 | 价格 (USD) |24h涨跌 | 来源 |
| ------ | ------ | ------ | ------ |
| BTC | $62,848.66 | +0.21% |
| ETH | $1,668.13 | +0.01% |
| SOL | $66.07 | +0.26% |
| XRP | $1.15 | +0.5% |
| ADA | $0.1662 | +1.86% |
| BNB | $598.42 | +0.27% |

*行情来源：CoinMarketCap（Chrome DevTools Protocol 抓取，2026-06-09 12:22 北京时间，每个币种单独打开 `coinmarketcap.com/currencies/{slug}/` 页面，从 `[data-test="text-cdp-price-display"]` 读取价格，从页面正文 `0.21% (24h)` 等可见字段读取 24h 涨跌百分比；CDP 9222 端口 Chrome 进程 PID 88570，`/tmp/cmc-fresh-2026-06-09.json` 留有原始 body 字段证据）。BNB 当日 CMC 页面仍返回 "Oops! Looks like something went wrong. Please try again later."（多次重试均失败，疑似 CMC 触发了限流保护），BNB 行改用 CoinGecko API 备用数据（`https://api.coingecko.com/api/v3/simple/price?ids=binancecoin&vs_currencies=usd&include_24hr_change=true`，2026-06-09 12:23 BJT 抓取，原始响应中 `binancecoin.usd=598.42, usd_24h_change=0.2735%`），与 CMC 同时段数据（BTC $62,857 / -0.01%、ETH $1,668.71 / +0.28%、SOL $66.09 / +0.58%、XRP $1.15 / +0.82%、ADA $0.166148 / +2.04%）同向但 CoinGecko 的 BTC 24h 仍报 -0.01%（CG API 缓存延迟 vs CMC 实时，与昨日 06-08 早报记录的双源小幅偏差同模式）。表中未列 7d 字段，原因是 CMC 当日页面未提供统一的 7d 数字展示区域（多个 7d 候选值散落在「Why is BTC's price down today?」「Volume (24h)7.54%」「Vol/Mkt Cap」等不同区块），为避免幻觉本表不列 7d。注：表中 BTC/ETH/SOL/XRP/ADA 24h 涨幅均为小幅正值，与昨日 06-08 早报「BTC/ETH/SOL/XRP/ADA/BNB 普涨 4-8%」相比动能显著减弱——周一市场在 Strategy 重新增持与 ETF 持续流出之间拉锯，价格围绕 6.27-6.30 万美元窄幅震荡，12:22 BJT 较 11:48 BJT（上一轮本地抓取快照：BTC $62,761.61）上涨约 87 美元（+0.14%）。*

## 🔥今日热点

### Strategy重新增持1,550 BTC（约1.013亿美元），BTC 重回6.3 万美元上方、Strive同步购入32 BTC
来源: CoinDesk
原文: [原文](https://www.coindesk.com/business/2026/06/08/live-updates-bitcoin-above-usd63-400-as-strategy-adds-usd100-million-btc-in-latest-purchase)
摘要: CoinDesk实时直播报道，**周一美股收盘后 BTC 在 $63,300附近交易，24h涨3%**，盘中一度冲高突破 $64,000；ETH、SOL、XRP同步涨4-6%。Strategy（MSTR）宣布购入1,550 BTC（总价约1.013亿美元，CoinTelegraph同步确认），股价当日涨5.6%；其高息优先股 STRC 从上周低点 $91反弹至 $96.85。**Strive Asset Management也在同一日购入32 BTC，数量恰好等于 Strategy 上周抛售的32 BTC**，形成显著的"对手盘"叙事。萨尔瓦多 Bitcoin Office 显示该国仍在按总统承诺日均购入 ≥1 BTC。

### Citrini Research 看涨 Hyperliquid（HYPE）：与多数加密币（含 BTC）不同，HYPE 有真实现金流和回购机制
来源: CoinDesk
原文: [原文](https://www.coindesk.com/business/2026/06/08/influential-research-firm-that-caused-ai-stock-meltdown-lays-out-hyperliquid-as-compelling-idea)
摘要: CoinDesk报道，**曾于2 月引发 AI板块股灾式抛售的 Citrini Research 周一发布新报告，将去中心化永续合约交易所 Hyperliquid及其代币 HYPE列为"令人信服"的新标的**。报告原文称："与多数加密币（含 BTC）不同，HYPE 有合法的现金流；除此之外，它还有回购机制。" DeFiLama数据显示，Hyperliquid平台年化费用收入已达约10.6亿美元，30 天永续合约交易量约2,200亿美元。CoinDesk指出，HYPE 是2026 年内表现最好的加密币之一，在整个数字资产板块下跌中逆势上行。这是 Citrini Research首次公开将加密资产列为"令人信服"标的，与2 月 AI恐慌叙事形成显著反差。

### Aave 在84.5亿美元"挤兑"事件后，创始人 Stani Kulechov 称协议"韧性"、将责任归因"第三方"
来源: CoinDesk
原文: [原文](https://www.coindesk.com/business/2026/06/08/aave-labs-founder-stani-kulechov-deflects-responsibility-in-usd8-billion-run-on-stage)
摘要: CoinDesk报道，**最大 DeFi借贷协议 Aave 的创始人兼 CEO Stani Kulechov 在巴黎 Proof of Talk论坛公开回应4 月桥接漏洞触发的84.5亿美元 TVL 出逃事件，将责任归因于"第三方实体"对去中心化金融脆弱性的利用**。Kulechov强调 Aave协议的"韧性"，未承认协议自身的风险架构存在缺陷。CoinDesk 在导语中明确指出，**独立数据揭示 Aave自身风险架构存在严重缺口**，与 Kulechov 的"韧性"表述形成直接冲突。这是 DeFi历史上首次出现创始人公开淡化单一桥接漏洞（波及数十亿美元 TVL）影响的表态，社区对其后续治理走向高度关注。

### MetaMask推出 AI代理钱包，内置交易安全机制，应对"AI代理执行交易"新场景
来源: CoinDesk
原文: [原文](https://www.coindesk.com/tech/2026/06/08/metamask-launches-ai-agent-wallet-with-built-in-security-for-crypto-trades)
摘要: CoinDesk报道，**Consensys旗下 MetaMask 周一发布 AI代理钱包（AI Agent Wallet），内置针对 AI代理执行加密交易的安全机制**。官方说明显示，新产品的设计背景是"AI代理越来越多地作为加密市场参与者，为用户执行交易和管理资金"。CoinDesk指出，这是首批主流钱包厂商将"AI代理可编程交易"作为产品主线，而非作为辅助功能集成；内置安全机制包含交易白名单、金额上限和代理身份签名校验三类。这一发布时点正值 AI代理在加密市场（尤其 Hyperliquid 等链上永续合约平台）交易份额上升、但因交易失误或恶意提示词造成用户资产损失的案例增多。

###10xResearch：BTC近期下跌的真正元凶是4 月美国通胀数据驱动的 ETF抛售，不是 Strategy 上周的减持
来源: CoinDesk
原文: [原文](https://www.coindesk.com/markets/2026/06/08/blame-bitcoin-s-tumble-on-rising-inflation-not-strategy-10xresearch-argues)
摘要: CoinDesk报道，**10xResearch创始人 Markus Thielen 周一撰文指出，BTC近期弱势的主要驱动是4 月美国通胀数据"过热"后 ETF资金卖出，并非 Strategy 上周的小额 BTC抛售**。Thielen 在文中明确表示，反弹能否延续的关键阻力是周三即将公布的 CPI 数据。该结论与 NYDIG周末"AI叙事+IPO抽资+量子叙事+Strategy抛压"四股力量叠加的框架形成补充：NYDIG强调叙事面，10xResearch强调宏观面；两者并不矛盾，但都将 Strategy 单点抛售的影响进一步稀释。这与 CoinDesk同步报道「BTC关键市场指标（市场价格接近已实现公允价值）显示本轮抛售的最坏时刻可能已过」相互印证。

## ⚖️监管与政策

### SBF正式向特朗普请求总统特赦，CoinDesk指出其在"押注"特朗普对加密人士的赦免历史
来源: CoinDesk
原文: [原文](https://www.coindesk.com/policy/2026/06/08/sam-bankman-fried-officially-asks-donald-trump-for-a-presidential-pardon)
摘要: CoinDesk报道，**正服刑25 年的 FTX 前 CEO Sam Bankman-Fried（SBF）已通过美国司法部"总统特赦办公室"（Office of the Pardon Attorney）正式提交特赦申请**，目前案件状态显示为"待审查"。CoinDesk同步指出 SBF押注的是特朗普过去对加密圈人士（如 BitMEX联合创始人等）已有赦免记录，但**特朗普此前曾公开表态让 SBF"不要指望"特赦**，SBF此次申请仍属"逆风下注"。CoinDesk回顾了 FTX倒闭路径——2022 年11 月 CoinDesk 首先披露 Alameda Research资产负债表问题，暴露 FTX80亿美元客户资金缺口并触发挤兑；SBF2023 年被判欺诈和合谋罪名成立。CoinTelegraph 同日独立报道此事件（标题为 "Sam Bankman-Fried files formal Trump pardon request"），两侧报道时间窗口均在06-08 ~06-09 之间。

### Galaxy Digital 将美国《CLARITY Act》年内通过概率从75% 下调至60%，认为参议院时间窗口紧迫
来源: CoinTelegraph
原文: [原文](https://cointelegraph.com/news/galaxy-drops-clarity-act-passage-odds-to-60-percent-as-time-runs-out)
摘要: CoinTelegraph报道，**Galaxy Digital 周一发布报告，将美国参议院年内通过《CLARITY Act》（加密市场结构立法）的概率从75% 下调至60%**。报告核心理由是立法者在11 月中选前能利用的国会时间正在迅速减少，法案涉及 SEC 与 CFTC 对数字资产管辖权划分、稳定币监管、DeFi报税义务等议题，谈判复杂度高。CoinTelegraph指出，CLARITY Act 的命运直接决定美国境内加密交易所、稳定币发行方和 DeFi协议的合规成本结构；Galaxy此次下调概率，是立法窗口从"基本能通过"切换为"有显著不确定性"的关键修正。

## 🐋链上与机构

###现货 BTC ETF连续4 周失血，单周（截至6/5）净流出17.2亿美元；ETH ETF同期失血1.73亿美元
来源: CoinTelegraph
原文: [原文](https://cointelegraph.com/news/bitcoin-etfs-outflows-ether-altcoin-funds)
摘要: CoinTelegraph报道，**据 SoSoValue 数据，截至6 月5 日的一周，现货 BTC ETF净流出约17.2亿美元，延续自5 月15 日以来连续4 周的十亿美元级赎回潮**。Farside Investors进一步数据显示，压力集中在6 月前3 个交易日，分别失血4.838 亿、5.191 亿、3.966亿美元；BlackRock IBIT贡献了大部分赎回，Fidelity 和 Grayscale旗下产品也有显著流出。同期 ETH ETF净流出1.73亿美元。这一资金面数据与同日 CoinDesk报道的"BTC 重回6.3 万美元上方"形成方向冲突：价格层面在企稳，但 ETF资金面仍在持续失血，说明本轮反弹更多由现货市场大户（如 Strategy增持）推动，而非机构资金回流——这是06-08早报 "BTC ETF资金流向与2 月截然相反"趋势的延续。

---


