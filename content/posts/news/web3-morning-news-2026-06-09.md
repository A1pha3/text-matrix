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

🦞每日08:00自动更新

**数据来源**：行情：CoinMarketCap（Chrome DevTools Protocol 抓取，每个币种单独打开 `coinmarketcap.com/currencies/{slug}/` 页面，从 `[data-test="text-cdp-price-display"]` 读取价格，从页面正文 `0.21% (24h)` 等可见字段读取 24h 涨跌百分比，2026-06-09 12:22 北京时间；CDP 9222 端口 Chrome 进程 PID 88570；原始响应体保留在 `/tmp/cmc-fresh-2026-06-09.json`）。BNB 当日 CMC 页面仍返回 "Oops! Looks like something went wrong. Please try again later." 提示（多次重试均失败，疑似 CMC 限流），BNB 行改用 CoinGecko API 备用数据（2026-06-09 12:23 BJT 抓取，原始响应中 `binancecoin.usd=598.42, usd_24h_change=0.2735%`）。新闻：CoinDesk（5 篇，Chrome 逐篇打开原文页，JSON-LD `datePublished`处于 2026-06-08T13:00:00Z ~2026-06-08T18:41:04Z 窗口内，对应 BJT 2026-06-08 21:00 ~2026-06-09 02:41），CoinTelegraph（2 篇，Chrome 抓取 `[data-testid="post-article-meta__publish-date"]`字段确认 `Published Jun8,2026`）。链接 HEAD 核验（cron 9c412432 补做时 12:18 BJT）：`/tmp/web3-link-check-2026-06-09-1218.json`，8/8 HTTP 200。

**📎 已核验原文链接清单（仅列正文实际引用，按发布时间从早到晚排序）：**
- ✅ https://www.coindesk.com/tech/2026/06/08/metamask-launches-ai-agent-wallet-with-built-in-security-for-crypto-trades （CoinDesk，JSON-LD `datePublished`:2026-06-08T13:00:00Z，对应 BJT06-0821:00，og:description 与正文主题一致）
- ✅ https://www.coindesk.com/markets/2026/06/08/blame-bitcoin-s-tumble-on-rising-inflation-not-strategy-10xresearch-argues （CoinDesk，JSON-LD `datePublished`:2026-06-08T14:37:27.634Z，对应 BJT06-0822:37，og:description 与正文主题一致）
- ✅ https://www.coindesk.com/business/2026/06/08/aave-labs-founder-stani-kulechov-deflects-responsibility-in-usd8-billion-run-on-stage （CoinDesk，JSON-LD `datePublished`:2026-06-08T15:17:44.044Z，对应 BJT06-0823:17，og:description 与正文主题一致）
- ✅ https://www.coindesk.com/policy/2026/06/08/sam-bankman-fried-officially-asks-donald-trump-for-a-presidential-pardon （CoinDesk，JSON-LD `datePublished`:2026-06-08T15:41:10.280Z，对应 BJT06-0823:41，正文段落含 clemency petition、Office of the Pardon Attorney 等关键事实）
- ✅ https://www.coindesk.com/business/2026/06/08/live-updates-bitcoin-above-usd63-400-as-strategy-adds-usd100-million-btc-in-latest-purchase （CoinDesk，JSON-LD `datePublished`:2026-06-08T17:04:38.358Z，对应 BJT06-0901:04，正文含 BTC $63,300、Strategy1,550 BTC增持、STRC $96.85、Strive32 BTC同步购入等关键数字）
- ✅ https://www.coindesk.com/business/2026/06/08/influential-research-firm-that-caused-ai-stock-meltdown-lays-out-hyperliquid-as-compelling-idea （CoinDesk，JSON-LD `datePublished`:2026-06-08T18:41:04.109Z，对应 BJT06-0902:41，正文含 Citrini Research报告原文引语、Hyperliquid10.6 亿年化费用、2,200 亿30 天交易量）
- ✅ https://cointelegraph.com/news/galaxy-drops-clarity-act-passage-odds-to-60-percent-as-time-runs-out （CoinTelegraph，文章内 `[data-testid="post-article-meta__publish-date"]` 显示 `Published Jun8,2026`，og:description明确 "Galaxy Digital dropped its odds of the Senate passing the CLARITY Act this year from75% to60%"）
- ✅ https://cointelegraph.com/news/bitcoin-etfs-outflows-ether-altcoin-funds （CoinTelegraph，文章内 `[data-testid="post-article-meta__publish-date"]` 显示 `Published Jun8,2026`，og:description明确 "Spot Bitcoin ETFs posted a fourth straight week of billion-dollar outflows"）

**已丢弃候选条目说明**：
- **CoinDesk06-08 /06-09候选池中丢弃**：
 - `forehead-tattoos-and-alcohol-dares...memecoin-craze`（06-0906:58）：主题为 MEME 文化乱象，与 Web3早报常规板块（市场/监管/机构）不匹配，丢弃。
 - `a-crucial-bitcoin-market-indicator...worst-of-the-crypto-crash-might-be-over`（06-0820:02）：与已收录的第5 条「10xResearch通胀归因」在分析结论上重合（同指 ETF抛售 +接近公允价值），合并为正文交叉引用，未单列。
 - `bitcoin-holds-steady-after-sunday-s-rally...reversal-may-take-longer`（06-0819:00）：与已收录的第1 条「BTC 重回6.3 万 + Strategy增持」在事件和数字上完全重叠，丢弃。
 - `gold-slips-below-200-day-moving-average...glimmer-of-hope-for-bitcoin-bulls`（06-0817:57）：与已收录的市场分析条目（10xResearch / BTC指标）方向一致但维度分散（黄金技术面），未单列。
 - `u-s-inflation-european-central-bank-rate-decision...crypto-week-ahead`（06-0817:46）：本周展望综述，与第5 条10xResearch关注周三 CPI 数据相呼应，未避免重复未单列。
 - `cme...bitcoin-volatility-index-futures`（06-0816:19）：衍生品产品信息，信息密度不足，丢弃。
 - `zcash-bounces-45...ironwood-upgrade`（06-0816:10）：Zcash单一项目升级，主流叙事密度不足，丢弃。
 - `xrp-steadies-above-usd1-10...four-month-lows`（06-0814:06）：与行情表 XRP $1.15 一致但事件已包含在第1 条普涨叙述中，丢弃。
 - `bitmine-bought-the-dip...biggest-ether-purchase-in-2026`（06-0820:53）：Bitmine 单家公司行为，未上升到行业叙事，丢弃。
 - `europe-s-strict-new-crypto-rules...crushing-small-startups-ledger-cto-says`（06-0815:38）：MiCA监管议题重要但与已收录的 Galaxy CLARITY Act 同属监管线，避免过度集中丢弃。
 - `bybit-challenges-wall-street-with-tokenized-u-s-stock-ipos`（06-0811:34）：Bybit SpaceX IPO 代币化产品重要但与已收录的 Hyperliquid / Aave / Strategy / MetaMask 主线叙事距离较远，未单列。
 - `strategy-buys-1-550-bitcoin-boosts-cash-reserves...`（06-0820:12）：与第1 条 CoinDesk Live updates 完全重叠（同一事件的另一稿件），丢弃。
- **CoinTelegraph06-08 /06-09候选池中丢弃**：
 - `sbf-clemency-bid-trump-pardon-ftx-fraud-conviction`（Published Jun9,2026）：与已收录的 CoinDesk SBF 特赦条完全重叠（同一事件 CoinTelegraph同期报道），避免重复丢弃。
 - `strategy-resumes-bitcoin-purchases-1550-btc-buy`（Published Jun8,2026）：与已收录的 CoinDesk Strategy1,550 BTC 条完全重叠（同一事件 CoinTelegraph同期报道），避免重复丢弃。
 - `man-who-memorized-wallet-mnemonic-jailed-in-china-for-107-btc-theft`（Published Jun8,2026）：og:description 显示"中国东部一男子因记忆12词助记词窃取107 BTC 被判10 余年"，信息密度高但属于已结束的法律案件而非24h内的政策/事件动态，按早报定位丢弃。
 - `south-korea-police-raid-bithumb-over-lawmaker-hiring-favoritism-probe-report`（Published Jun8,2026）：韩国地方监管事件，与已收录的 CLARITY Act 同属监管线但地理范围不同，避免监管条目过载丢弃。
 - `strategys-saylor-signals-btc-buy-as-preferred-dividend-pay-date-vote-looms`（Published Jun8,2026）：Saylor 周日暗示加仓已在06-08早报正文覆盖（参见 https://txtmix.com/posts/news/web3-morning-news-2026-06-08/），按24h窗口约束本日不重复。
 - `tokenized-rwas-stocks-gold-real-estate-institutional-adoption-binance`（Published Jun9,2026）：Binance报告 RWA增长600%，重要但属于综合性行业数据而非单一可锚定事件，避免与今日热点中的代币化条目（如已丢弃的 Bybit SpaceX IPO）冲突丢弃。
- **CoinTelegraph06-05 /06-06 /06-04 /06-03 /05-29 /06-07候选**：均早于24h窗口起点2026-06-0800:00Z，已在历史早报覆盖，本日不重复收录（详情见 `/tmp/ct_20260609.json`候选池与 `/tmp/web3-verify-2026-06-09.json`验证记录）。

**Chrome抓取原始数据快照**：12:22 BJT 补抓 CMC：`/tmp/cmc-fresh-2026-06-09.json`（CoinMarketCap 6 币种价格 + 24h 涨跌，12:22 BJT 抓取，CDP 9222 端口 Chrome PID 88570；BNB 仍限流 Oops!）。上一次抓取（11:48 BJT）快照保留作证据链：`/tmp/cmp2_20260609.json`（同 11:48 BJT，BNB 抓取失败记录见 `body: "Oops!..."`字段）；`/tmp/cmp_20260609.json`（11:23 BJT 第一次抓取）；`/tmp/cg_20260609.json`（CoinGecko 备用，11:47 BJT 抓取，用于 BNB 行）；本次补充 CoinGecko 12:23 BJT 备用响应通过 `curl` 获取（原始 JSON 在 cron 执行日志中可追溯）。新闻侧：`/tmp/cd_20260609.json`（CoinDesk 首页候选 URL列表）；`/tmp/ct_20260609.json`（CoinTelegraph 首页候选 URL列表）；`/tmp/web3-verify-2026-06-09.json`（34 条候选页面 datePublished / og:description验证记录）；`/tmp/web3-deep2-2026-06-09.json`（18 条精选页面正文段落 + JSON-LD + og:description核验记录）。链接 8 条 HEAD 快速核验（cron 9c412432 补做时 12:18 BJT）：`/tmp/web3-link-check-2026-06-09-1218.json`，8/8 HTTP 200。
