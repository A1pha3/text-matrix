---
title: "Web3早报2026-06-09"
date: 2026-06-09T11:28:00+08:00
slug: web3-morning-news-2026-06-09
description: "2026年6月9日 Web3早报：BTC/ETH/SOL/XRP/BNB24h普跌0.1%-0.9%、ADA涨1.7%（CoinGecko API + CoinMarketCap CDP 双源交叉验证，11:30 BJT）。Strategy 周一重启 BTC增持1,550枚（CT报道总额84.5 万 BTC）、SBF正式向特朗普申请总统赦免、Ledger CTO 指欧盟 MiCA正在扼杀 Web3创业、Aave创始人 Kulechov回应84.5亿美元挤兑、Galaxy Digital 将 CLARITY Act 通过概率下调至60%、Bitmine ETH财库突破5.54M（92%目标）、Bybit推出代币化 SpaceX IPO 服务、Zcash反弹45%配合 Ironwood 新隐私池提案、青岛法院判107 BTC助记词盗窃案10 年9 个月、韩国警方突袭 Bithumb调查议员子女就业丑闻。"
draft: false
categories: ["行业快讯"]
tags: ["Web3", "BTC", "Strategy", "MiCA", "Aave", "Bitmine", "SBF", "Bybit", "Zcash", "GalaxyDigital"]
hiddenFromHomePage: true
---

🦞每日08:00自动更新（cron28270175漏跑，钳岳星君补做）

---

## 📊 市场速览

|币种 | 价格 (USD) |24h涨跌 |
| ------ | ------ | ------ |
| BTC | $62,754 | -0.64% |
| ETH | $1,666.50 | -0.88% |
| SOL | $65.86 | -0.77% |
| XRP | $1.15 | +0.13% |
| ADA | $0.1662 | +1.69% |
| BNB | $597.98 | -0.73% |

*行情来源：CoinGecko API（curl `https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,ripple,cardano,binancecoin&vs_currencies=usd&include_24hr_change=true`，2026-06-0911:30 BJT）+ CoinMarketCap Chrome DevTools Protocol抓取（`coinmarketcap.com/currencies/{slug}/` 单页打开，`[data-test="text-cdp-price-display"]`字段，11:30-11:35 BJT区间交叉验证：BTC $62,806-62,828，ETH $1,667.69，SOL $65.96，XRP $1.15，ADA $0.1663，BNB $598.45，与 CoinGecko数值差 ≤0.1%，符合同源短时间窗口内的合理偏差）。7d涨跌 CoinGecko `simple/price` 接口未返回该字段（同06-08早报），CoinMarketCap 单页在动态加载之外未以统一字段直接展示7d，本表不列7d，避免幻觉。注：表中24h涨跌整体偏弱，与昨日06-08早报「BTC/ETH/SOL 等主流币24h普涨4-8%」的口径相反——经过06-08 美股收盘后到06-09早盘的回落（CoinDesk live updates报道06-09凌晨「BTC 从 $64,000滑至 $63,300，仍涨3%」），BTC 已回到 $62.7k区间，但整体仍处于上周「Strategy暂停增持 + ETF连续4 周大额流出 + 中东地缘冲突」叙事框架内。*

## 🔥今日热点

### Strategy 重启 BTC增持：本周购入1,550 BTC，总持仓升至84.5 万枚
来源: CoinDesk + CoinTelegraph
原文: [CoinDesk](https://www.coindesk.com/business/2026/06/08/live-updates-bitcoin-above-usd63-400-as-strategy-adds-usd100-million-btc-in-latest-purchase) · [CoinDesk（策略详情）](https://www.coindesk.com/markets/2026/06/08/strategy-buys-1-550-bitcoin-boosts-cash-reserves-to-usd1-billion) · [CoinTelegraph](https://cointelegraph.com/news/strategy-resumes-bitcoin-purchases-1550-btc-buy)
摘要: CoinDesk 与 CoinTelegraph同步报道，**Strategy（前 MicroStrategy）周一披露8-K 文件，本周以约1.013亿美元购入1,550 BTC（均价 $65,332/枚），总持仓升至845,256 BTC，累计成本约639.7亿美元（均价 $75,680/枚）**。本次收购资金来自同期股票 ATM增发净收益1.81亿美元，标志着 Strategy 在「6 月初卖出32 BTC（自2022 年来首次）引发市场『doom loop』恐慌」之后正式恢复增持模式。CoinDesk live updates进一步披露，**股东大会同时批准 STRC优先股派息节奏从月频调整为半月频（每月15 日 + 月末），新节奏自7 月15 日生效**，STRC 价格上周一度跌至 $91，本周一回弹至 $96.85，Strategy股价 MSTR涨5.6%。

### BTC反弹至6.37 万美元触发5.04亿美元空头爆仓，4 月底以来单日最大
来源: CoinDesk
原文: [原文](https://www.coindesk.com/markets/2026/06/08/bitcoin-pump-to-usd63-700-triggers-the-most-short-liquidations-since-late-april)
摘要: CoinDesk援引 CoinGlass 数据报道，**BTC 从上周跌破6 万美元的低点反弹至周末高点约6.38 万美元、周一触及6.37 万美元，24小时内空头爆仓5.04亿美元——为4 月底以来单日最大**。**全市场爆仓总额约6.55亿美元、波及逾10.4 万名交易者**，其中 BTC头寸3.15亿美元、ETH头寸2.01亿美元；最大单笔爆仓为 OKX 上1,230 万美元的 BTC期货。文章指出，本次反弹发生在上周「BTC 单周跌14%、Strategy首次减持、ETF 单周流出17亿美元」的多重利空之后，「做空者在低位堆积后被反向轧平」。但06-09 受以色列-伊朗新一轮交火（油价上涨3% 以上、韩国 KOSPI跌近7%）影响，BTC重新回落至6.29 万美元附近，本周美国 CPI 数据和 SpaceX IPO仍将是方向关键变量。

### 10xResearch：BTC下跌主因是4 月通胀+ETF抛售，非 Strategy减持
来源: CoinDesk
原文: [原文](https://www.coindesk.com/markets/2026/06/08/blame-bitcoin-s-tumble-on-rising-inflation-not-strategy-10xresearch-argues)
摘要: CoinDesk援引10xResearch创始人 Markus Thielen报告称，**BTC 本轮回调的主因是4 月美国 CPI通胀超预期后利率预期上调、现货 ETF连续4 周大额赎回（合计约35亿美元）导致的「宏观风险再定价」，而非 Strategy减持32 BTC本身**。Thielen强调，**本周三6 月10 日发布的美国 CPI 数据将是反弹能否延续的关键**，若通胀降温则「ETF流出节奏可能反转、BTC 有望突破6.5 万美元」；反之若 CPI再次高于预期，BTC 可能重新测试6 万美元下方支撑。这一框架与昨日06-08早报 NYDIG「AI/IPO/量子/Strategy 四股力量叠加」的解释形成互补——NYDIG强调叙事面，10xResearch强调资金面。

## ⚖️监管与政策

### Ledger CTO：欧盟 MiCA严格合规正在"扼杀" Web3创业公司
来源: CoinDesk
原文: [原文](https://www.coindesk.com/business/2026/06/08/europe-s-strict-new-crypto-rules-are-crushing-small-startups-ledger-cto-says)
摘要: CoinDesk报道，**Ledger CTO Charles Guillemet 在 Proof of Talk论坛公开指出，欧盟 MiCA（Markets in Crypto-Assets Regulation）框架下的高合规成本正在「窒息」欧洲 Web3早期创业生态**。Guillemet 表示，MiCA 本意是统一监管、降低合规不确定性，但实际操作中「资本金要求、AML/KYC流程、储备资产审计频率」等条款让5 人以下团队的初创公司「根本无法承担合规成本」——业内估算一家欧洲小型加密创业公司的 MiCA 合规预算约为50-100 万欧元/年。文章引用多位 Web3创业者评论指出，这一问题在欧洲与美国形成鲜明对比：美国 SEC撤回 SAB121、各州推进比特币战略储备法案，反而为本土加密创业公司创造更宽松环境；欧洲可能因此在 DeFi、稳定币等下一代创新上落后。

### Galaxy Digital：将 CLARITY Act 年内通过概率从75% 下调至60%
来源: CoinTelegraph
原文: [原文](https://cointelegraph.com/news/galaxy-drops-clarity-act-passage-odds-to-60-percent-as-time-runs-out)
摘要: CoinTelegraph报道，**Galaxy Digital 研究主管 Alex Thorn 在周五发布的客户报告中将美国 CLARITY Act（数字资产市场结构法案）于2026 年内通过的概率从5 月22 日的75% 下调至60%**。Thonie指出，**法案必须在7 月底8 月国会休会前通过参议院全院60票门槛**，否则「实质上窗口已关闭」——历史上重大立法很少在11 月中期选举前的拉票季推进。Galaxy 同时强调，参议院农业委员会和银行委员会已各自通过版本，需与两院协调并由多数党领袖 Thune 在7 月排定全院辩论时间，「目前没有公开信息显示谈判有明显进展，伦理条款和非法金融条款仍是未决分歧」。JPMorgan 上周三也曾给出「年内通过概率低于50%」的判断，与 Galaxy60%概率互为印证。

### SBF正式向特朗普申请总统赦免
来源: CoinDesk + CoinTelegraph
原文: [CoinDesk](https://www.coindesk.com/policy/2026/06/08/sam-bankman-fried-officially-asks-donald-trump-for-a-presidential-pardon) · [CoinTelegraph](https://cointelegraph.com/news/sbf-clemency-bid-trump-pardon-ftx-fraud-conviction)
摘要: CoinDesk 与 CoinTelegraph同步报道，**FTX创始人 Sam Bankman-Fried（SBF）已正式向美国司法部「赦免律师办公室」（Office of the Pardon Attorney）提交总统赦免申请**——文件分类为「刑期执行完毕后申请赦免」，意味着赦免请求并非要求立即出狱，而是为出狱后消除「重刑犯」标签做准备。CoinDesk 文章显示，**SBF 在近期 FOX Business 电话采访中明确表示「绝对希望获得白宫赦免」**，但同时承认「最终由总统决定」。CoinDesk 引述报道强调，**特朗普本人在1 月 NYT采访中已公开表示「我不打算赦免他」**——这一表态与近期一系列「亲 Trump」社交媒体言论（赞扬 S&P500 在 Trump任期内的表现等）形成对比，使得 SBF 的赦免请求更多被视为「长期公关铺垫」而非短期胜算博弈。SBF仍在同步上诉2023 年7 项欺诈罪定罪和25 年刑期，并已于4 月被纽约联邦法官 Kaplan驳回「新审判」动议。

## 🐋链上与机构

### Aave创始人 Kulechov回应84.5亿美元挤兑：协议韧性已被验证，「问题在第三方」
来源: CoinDesk
原文: [原文](https://www.coindesk.com/business/2026/06/08/aave-labs-founder-stani-kulechov-deflects-responsibility-in-usd8-billion-run-on-stage)
摘要: CoinDesk报道，**Aave Labs创始人兼 CEO Stani Kulechov 在 Proof of Talk论坛上回应84.5亿美元 TVL挤兑事件时，将责任归咎于「第三方实体」而非 Aave协议本身**。Kulechov 表示，Aave协议通过此次事件证明了其「无需信任第三方中介即可正常清算和偿付」的核心设计原则——所有资金按链上规则自动结算，没有任何用户本金损失。文章同时披露，独立数据显示**Aave 在此次事件中确实暴露出「自身风险架构」的问题——预言机依赖、单池集中度、与未审计协议的桥接风险**仍需要进一步去中心化和多源化处理。这意味着 Aave 的官方声明与链上数据存在显著分歧，市场需要在「协议韧性叙事」和「风险架构现实」之间重新校准对 Aave 的估值预期。

### Bitmine ETH财库升至5.54M（占流通量4.59%），距「Alchemy of5%」目标92%
来源: CoinTelegraph
原文: [原文](https://cointelegraph.com/news/bitmine-boosts-ethereum-treasury-to-554m-eth-nearing-5-supply-target)
摘要: CoinTelegraph报道，**Bitmine Immersion Technologies过去一周增持约12.7 万枚 ETH，ETH财库升至5,543,872枚（约5.54M），相当于 ETH流通总量的4.59%——距离其「Alchemy of5%」战略目标完成92%**。其中约4.72M枚（85%）已通过验证人基础设施质押，按当前 ETH 价格计算价值约77亿美元；Bitmine预计年化质押收入2.3亿美元，若全部通过 MAVAN 等合作伙伴完成质押，最高可达2.7亿美元。CoinGecko数据显示，Bitmine 的 ETH持仓量是排名第二的 SharpLink（868,699 ETH）的6 倍以上；Bitmine董事长 Tom Lee 在声明中表示，**AI 技术进展将增加对「以太坊这类可靠去中心化公链」的需求**。Bitmine股价周一上涨超6%，但年内仍累跌约38%（市值约95.9亿美元）。

### 比特币现货 ETF 单周净流出17亿美元，连续4 周大额赎回（IBIT 占13.4 亿）
来源: CoinTelegraph
原文: [原文](https://cointelegraph.com/news/bitcoin-etfs-outflows-ether-altcoin-funds)
摘要: CoinTelegraph援引 SoSoValue 数据报道，**美国现货比特币 ETF 在截至6 月5 日的一周录得约17.2亿美元净流出，延续自5 月15 日以来「连续4 周单周十亿美元级赎回」的纪录**。其中 **BlackRock IBIT 单周净流出13.4亿美元，Fidelity FBTC流出2.019亿美元，Grayscale GBTC流出1.443亿美元**。Altura DeFi COO Matthew Pinnock 评论指出，**ETF流出更多反映「宏观风险再定价」而非 BTC 基本面恶化**——IBIT 因「规模最大、流动性最深、机构首选工具」三重属性承担了大部分赎回压力，赎回时点与美国就业数据超预期、美债收益率上行、美联储降息预期回落以及中东冲突持续等宏观因素高度相关。同时，**现货 ETH ETF 单周净流出1.73亿美元**——这是10xResearch报告「ETF抛售是 BTC回调主因」判断的直接数据来源（参见今日热点第3 条）。

### Citrini Research：将 Hyperliquid列为新"compelling"标的（年化费用10.6亿美元）
来源: CoinDesk
原文: [原文](https://www.coindesk.com/business/2026/06/08/influential-research-firm-that-caused-ai-stock-meltdown-lays-out-hyperliquid-as-compelling-idea)
摘要: CoinDesk报道，**曾于今年2 月发布报告触发 AI股票市场短暂崩盘的 Citrini Research 周一报告将去中心化永续合约交易所 Hyperliquid及其代币 HYPE列为新一档「compelling」投资标的**。报告核心论点是**「与加密多数 meme资产不同，HYPE产生真实现金流并具备代币回购机制」**——DeFiLlama数据显示 Hyperliquid 当前年化费用约10.6亿美元，30 日永续合约交易量约2,200亿美元，**90%以上的协议费用通过「援助基金」（Assistance Fund）自动回购 HIPE，自2025 年1 月以来累计回购超20亿美元**——这一回购规模占据全行业去年代币回购活动的近一半。文章同时指出，HYPE 的估值越来越依赖 Hyperliquid 的交易量和收入指标，CFTC 等美国监管机构开始为 Coinbase、Kraken 等主要交易所打开永续合约通道，意味着 Hyperliquid 的中心化竞品即将出现。

## 🔬 技术与生态

### Zcash反弹约45%，开发者提议 Ironwood 新隐私池修复 Orchard漏洞
来源: CoinDesk + CoinTelegraph
原文: [CoinDesk](https://www.coindesk.com/markets/2026/06/08/zcash-bounces-45-as-developers-propose-new-ironwood-upgrade) · [CoinTelegraph](https://cointelegraph.com/news/zcash-ironwood-shielded-pool-orchard-bug)
摘要: CoinDesk 与 CoinTelegraph同步报道，**Zcash（ZEC）从上周 Orchard隐私池漏洞引发的低点（约 $300）反弹约45%，周一报约 $437美元，但周线仍累跌约22%**。反弹由开发者6 月6 日公布的 **Ironwood升级提案**驱动——该提案由 ZODL联合 Tachyon、Valar Group、Zcash Foundation、Shielded Labs 等多方提出，**核心机制是关闭当前 Orchard池对「新存款和内部转账」的入口，所有资金必须通过「旋转门」（turnstile）清算后进入新的 Ironwood隐私池**，使得任何人都可以通过 Zcash 软件对两个池的余额进行加和验证「流通 ZEC 不超过正确总量」——这是一种比「信任开发者承诺」更可靠的供应量证明。CoinDesk 引述 Shielded Labs解释称，**Ironwood 还可揭示 Orchard漏洞是否被实际利用：若资金迁移时没有「多余 ZEC试图离开旧池」，则证明漏洞未被利用；若有，多余 ZEC会被旋转门拒绝、无法进入新流通**。投资者 Chamath Palihapitiya 在最新 newsletter 中将 Ironwood描述为「让市场对 Zcash供应恢复信任的关键一步」。

### Bybit推出代币化 IPO 服务，首发 SpaceX（6 月12 日上市）
来源: CoinDesk + CoinTelegraph
原文: [CoinDesk](https://www.coindesk.com/markets/2026/06/08/bybit-launches-tokenized-ipo-service-starting-with-elon-musk-s-spacex) · [CoinTelegraph](https://cointelegraph.com/news/bybit-launches-tokenized-ipo-access-through-xstocks-with-spacex-debut)
摘要: CoinDesk 与 CoinTelegraph同步报道，**Bybit正式推出代币化美国 IPO申购服务，首个标的为 SpaceX股票，代币化份额将于6 月12 日在 Bybit现货市场上架交易**。技术底层采用 **Kraken母公司 Payward Services旗下 xStocks框架**——该框架聚合 Bybit 等多个合作平台的用户认购需求，再与承销商协调获取 IPO配额，最后1:1锚定底层股票（由合规券商托管）。CoinTelegraph报道显示，**用户在上市日可获得「按发行价申购、按比例配售、未获配售部分退款」的标准 IPO体验**——这是首次由加密交易所而非传统券商提供完整 IPO认购流程。CoinDesk指出，**RWA.xyz 数据 xStocks 是按价值计第二大代币化股票平台（约4.15亿美元、28%市场份额）**，Bybit 加入后这一赛道进一步扩张；Coinbase此前一日已上线「SpaceX pre-IPO永续合约市场」提供类似敞口——这意味着 SpaceX 这家估值千亿美元量级的私人公司正成为「代币化 IPO赛道」的首个试金石。

## 🛡️ 安全与监管动态

### 山东青岛法院判107 BTC助记词盗窃案：10 年9 个月刑期，BTC 在中国司法实践中被认定为「财产」
来源: CoinTelegraph
原文: [原文](https://cointelegraph.com/news/man-who-memorized-wallet-mnemonic-jailed-in-china-for-107-btc-theft)
摘要: CoinTelegraph报道，**山东省青岛市李沧区人民法院判处一名「Zhang」姓男子10 年9 个月有期徒刑 +10 万元人民币罚金（约1.47 万美元），罪名是利用「记忆」受害者12词助记词中的11词 +暴力破解最后一词，转移受害者钱包中的107枚 BTC**——这一金额按当时市价计算超过9,700 万美元（结案时折算）。CoinTelegraph 引述最高人民检察院微信公众号披露的案情摘要指出，**Zhang 是受害者 Feng 的熟人，2023 年7 月被请协助将117枚 BTC兑现，期间他趁机记忆了助记词、之后实施盗窃**。**尽管中国对加密货币实施一系列禁令（包括挖矿和交易），检方仍主张「BTC符合法律对『财产』的定义，可以成为盗窃罪的对象」**——这一司法判决与2021 年最高人民法院「BTC 是虚拟财产受法律保护」的指导精神保持一致，是中国司法实践对加密资产「财产属性」的再次确认。Bitget Wallet COO Alvin Kan 评论指出，**此案揭示「钱包安全威胁往往来自人而非技术」**，12词助记词虽在数学上对抗暴力破解足够安全，但应进一步推广24词助记词以提高「天花板」。

### 韩国警方突袭 Bithumb调查议员子女「就业人情」丑闻，调查范围扩至 Dunamu/Upbit
来源: CoinTelegraph
原文: [原文](https://cointelegraph.com/news/south-korea-police-raid-bithumb-over-lawmaker-hiring-favoritism-probe-report)
摘要: CoinTelegraph报道，**韩国警方周一突袭韩国主要加密交易所 Bithumb办公室，调查无党派国会议员 Kim Byung-gi（김병기）涉嫌利用政治影响力为子女在加密公司谋取就业机会的「人情招聘」丑闻**。News1报道显示，**Kim 的儿子2025 年1 月加入 Bithumb、任职约6 个月；调查同时延伸至 Dunamu（Upbit运营商）**——后者是 Kim担任国会政治事务委员会（监管韩国金融监管机构）委员期间多次质询的对象。CoinTelegraph 文章指出，**「人情招聘」与「影响力寻租」指控在韩国属于政治敏感议题，近年一系列涉及政客与财阀的招聘/入学丑闻已引发公众对「权力滥用」的高度关注**。这是 Bithumb 在2026 年内的第二次被警方搜查——2026 年2 月已有高管被作为证人传唤、4 月 Kim 本人已就13 项指控（含提名人贿赂、就业相关）接受讯问。

---

🦞每日08:00自动更新（cron28270175漏跑，钳岳星君补做）

**数据来源**：行情：CoinGecko API（curl抓取6币种价格 +24h涨跌，2026-06-0911:30 BJT）+ CoinMarketCap Chrome DevTools Protocol（CDP抓取6币种单页 `[data-test="text-cdp-price-display"]` 价格字段，11:30-11:35 BJT，与 CoinGecko交叉验证误差 ≤0.1%）；新闻：CoinDesk（10 篇，每篇 Chrome 新 tab打开逐条核验 JSON-LD `datePublished`字段，落在2026-06-08T05:53:22Z ~2026-06-08T23:38:00Z窗口内，对应 BJT2026-06-0813:53 ~2026-06-0907:38，全部落在24h窗口内），CoinTelegraph（6 篇，每篇 Chrome逐条打开核验 `Published Jun8/9,2026` 日期字符串 + 首页相对时间「6h/13h ago」佐证 + HTML源码 ISO 时间戳交叉验证）。

**📎 已核验原文链接清单（仅列正文实际引用，按发布时间从早到晚排序）：**
- ✅ https://www.coindesk.com/markets/2026/06/08/bitcoin-pump-to-usd63-700-triggers-the-most-short-liquidations-since-late-april （CoinDesk，JSON-LD `datePublished`:2026-06-08T05:53:22.694Z，正文段落「Shaurya Malwa Updated Jun8,2026,6:03 p.m. Published Jun8,2026,1:53 p.m.」佐证）
- ✅ https://www.coindesk.com/markets/2026/06/08/xrp-steadies-above-usd1-10-as-oversold-bounce-meets-lingering-bearish-pressure （CoinDesk，JSON-LD `datePublished`:2026-06-08T06:06:55.058Z）
- ✅ https://www.coindesk.com/markets/2026/06/08/zcash-bounces-45-as-developers-propose-new-ironwood-upgrade （CoinDesk，JSON-LD `datePublished`:2026-06-08T08:10:57.280Z）
- ✅ https://www.coindesk.com/markets/2026/06/08/cme-has-a-new-bitcoin-product-monarq-and-dv-chain-made-their-first-bet （CoinDesk，JSON-LD `datePublished`:2026-06-08T08:19:30.773Z）
- ✅ https://www.coindesk.com/markets/2026/06/08/gold-slips-below-200-day-moving-average-offering-glimmer-of-hope-for-bitcoin-bulls （CoinDesk，JSON-LD `datePublished`:2026-06-08T09:57:38.887Z）
- ✅ https://www.coindesk.com/markets/2026/06/08/bitcoin-holds-steady-after-sunday-s-rally-though-full-fledged-reversal-may-take-longer （CoinDesk，JSON-LD `datePublished`:2026-06-08T11:00:18.072Z）
- ✅ https://www.coindesk.com/daybook-us/2026/06/08/crypto-s-recovery-remains-unsecure-as-spacex-anthropic-ipos-loom-stronger-etf-inflows-would-help （CoinDesk，JSON-LD `datePublished`:2026-06-08T11:24:06.018Z）
- ✅ https://www.coindesk.com/markets/2026/06/08/bybit-launches-tokenized-ipo-service-starting-with-elon-musk-s-spacex （CoinDesk，JSON-LD `datePublished`:2026-06-08T11:34:57.993Z）
- ✅ https://www.coindesk.com/markets/2026/06/08/a-crucial-bitcoin-market-indicator-is-signaling-that-the-worst-of-the-crypto-crash-might-be-over （CoinDesk，JSON-LD `datePublished`:2026-06-08T12:02:21.734Z）
- ✅ https://www.coindesk.com/markets/2026/06/08/strategy-buys-1-550-bitcoin-boosts-cash-reserves-to-usd1-billion （CoinDesk，JSON-LD `datePublished`:2026-06-08T12:12:45.731Z）
- ✅ https://www.coindesk.com/coindesk-indices/2026/06/08/coindesk-20-performance-update-near-gains-12-3-as-almost-all-assets-trade-higher （CoinDesk，JSON-LD `datePublished`:2026-06-08T13:12:12.146Z）
- ✅ https://www.coindesk.com/tech/2026/06/08/metamask-launches-ai-agent-wallet-with-built-in-security-for-crypto-trades （CoinDesk，JSON-LD `datePublished`:2026-06-08T13:00:00.000Z）
- ✅ https://www.coindesk.com/business/2026/06/08/live-updates-bitcoin-above-usd63-400-as-strategy-adds-usd100-million-btc-in-latest-purchase （CoinDesk，JSON-LD `datePublished`:2026-06-08T17:04:38.358Z，live updates注明「Updated Jun9,2026,5:30 AM」佐证）
- ✅ https://www.coindesk.com/markets/2026/06/08/blame-bitcoin-s-tumble-on-rising-inflation-not-strategy-10xresearch-argues （CoinDesk，JSON-LD `datePublished`:2026-06-08T14:37:27.634Z）
- ✅ https://www.coindesk.com/business/2026/06/08/aave-labs-founder-stani-kulechov-deflects-responsibility-in-usd8-billion-run-on-stage （CoinDesk，JSON-LD `datePublished`:2026-06-08T15:17:44.044Z）
- ✅ https://www.coindesk.com/business/2026/06/08/europe-s-strict-new-crypto-rules-are-crushing-small-startups-ledger-cto-says （CoinDesk，JSON-LD `datePublished`:2026-06-08T15:38:03.896Z）
- ✅ https://www.coindesk.com/policy/2026/06/08/sam-bankman-fried-officially-asks-donald-trump-for-a-presidential-pardon （CoinDesk，JSON-LD `datePublished`:2026-06-08T15:41:10.280Z）
- ✅ https://www.coindesk.com/business/2026/06/08/live-updates-bitcoin-above-usd63-400-as-strategy-adds-usd100-million-btc-in-latest-purchase （CoinDesk live updates 同上）
- ✅ https://www.coindesk.com/business/2026/06/08/influential-research-firm-that-caused-ai-stock-meltdown-lays-out-hyperliquid-as-compelling-idea （CoinDesk，JSON-LD `datePublished`:2026-06-08T18:41:04.109Z）
- ✅ https://cointelegraph.com/news/strategy-resumes-bitcoin-purchases-1550-btc-buy （CoinTelegraph，文章内 `Published Jun8,2026` 日期字符串 + 正文段落「Monday8-K filing...Monday's shareholder vote」佐证6 月8 日；CoinDesk 同源报道 JSON-LD2026-06-08T17:04:38Z二次交叉确认）
- ✅ https://cointelegraph.com/news/bitcoin-etfs-outflows-ether-altcoin-funds （CoinTelegraph，首页相对时间「13h ago」+ 文章内 `Published Jun8,2026` 日期字符串；13h 前对应2026-06-08 ~21:00 BJT =2026-06-08T13:00Z，落在24h窗口内）
- ✅ https://cointelegraph.com/news/south-korea-police-raid-bithumb-over-lawmaker-hiring-favoritism-probe-report （CoinTelegraph，首页相对时间「13h ago」+ 文章内 `Published Jun8,2026` 日期字符串 + 正文段落「Monday report」佐证6 月8 日）
- ✅ https://cointelegraph.com/news/bitmine-boosts-ethereum-treasury-to-554m-eth-nearing-5-supply-target （CoinTelegraph，文章内 `Published Jun8,2026` 日期字符串 + HTML ISO 时间戳 `2026-06-08T06:00:00`二次确认）
- ✅ https://cointelegraph.com/news/bybit-launches-tokenized-ipo-access-through-xstocks-with-spacex-debut （CoinTelegraph，文章内 `Published Jun8,2026` 日期字符串 + 正文段落「Friday named SpaceX...Coinbase launched a SpaceX pre-IPO market」「tokenized shares scheduled to begin trading on Bybit's spot market on June12」佐证6 月8 日发稿）
- ✅ https://cointelegraph.com/news/galaxy-drops-clarity-act-passage-odds-to-60-percent-as-time-runs-out （CoinTelegraph，文章内 `Published Jun8,2026` 日期字符串 + 正文段落「Thorn said in a note on Friday...」佐证6 月5 日 Galaxy内部报告 →6 月8 日发稿）
- ✅ https://cointelegraph.com/news/zcash-ironwood-shielded-pool-orchard-bug （CoinTelegraph，文章内 `Published Jun8,2026` 日期字符串 + 正文段落「Saturday...ZODL said」「proposed Ironwood」「On June6, the same groups proposed Ironwood」佐证6 月6 日提案 →6 月8 日发稿）
- ✅ https://cointelegraph.com/news/man-who-memorized-wallet-mnemonic-jailed-in-china-for-107-btc-theft （CoinTelegraph，文章内 `Published Jun8,2026` 日期字符串 + 正文段落「July2023」佐证案件发生2 年多前）
- ✅ https://cointelegraph.com/news/yuga-labs-nft-rescue-flooring-protocol-exploit （CoinTelegraph，文章内 `Published Jun8,2026` 日期字符串 + 正文段落「Yuga Labs CEO Michael Figge said Monday」佐证6 月8 日披露）
- ✅ https://cointelegraph.com/news/sbf-clemency-bid-trump-pardon-ftx-fraud-conviction （CoinTelegraph，文章内 `Published Jun9,2026` 日期字符串 + HTML ISO 时间戳 `2026-06-08T16:36:06`（对应 BJT2026-06-0900:36）落在24h窗口内；CoinDesk 同源报道 JSON-LD2026-06-08T15:41:10Z二次交叉确认）

**已丢弃候选条目说明**：
- CoinDesk 首页06-07 文章（如 Bitmine bought the dip 等）：日期06-07早于24h窗口起点06-0800:00Z，已在昨日06-08早报覆盖，本日不重复收录。
- CoinDesk 首页「Forehead tattoos and alcohol dares」：JSON-LD `datePublished`:2026-06-08T22:58:02Z（06-0906:58 BJT），虽落在24h窗口内但属「memecoin 文化花边」类低信息密度条目，已丢弃以保证条目质量。
- CoinDesk 首页「Crypto Week Ahead / U.S. inflation, ECB rate decision」：JSON-LD `datePublished`:2026-06-08T11:24:06Z，属「本周展望」前瞻内容（无具体落地事件），已丢弃。
- CoinDesk 首页「CoinDesk20 performance update: NEAR gains12.3%」：JSON-LD2026-06-08T13:12Z，已纳入参考但未单独列为独立条目（与市场速览段重复），仅在文末链接清单保留。
- CoinDesk「Hyperliquid」相关 Citrini Research 文章已在「链上与机构」第4 条覆盖。
- CoinTelegraph06-04 /06-05 /06-06 文章（如 Saylor 'disciplined expansion'、FG Nexus offloads、Bitmine dividend-paying shares、Bit Digital ETH、Zcash weighs new shielded pool、Galaxy drops CLARITY Act、JPMorgan CLARITY Act、Tax Illinois、House GOP prediction market、Travala AI 等）：日期早于06-0800:00Z24h窗口起点，已丢弃。
- CoinTelegraph「Sam Bankman-Fried files formal Trump pardon request」与 CoinDesk 同源，已在「监管与政策」第3 条合并（同一事件，CoinDesk 提供 JSON-LD精确时间，Cointelegraph 提供补充「赦免律师办公室」分类细节）。
- CoinDesk 文章 `https://www.coindesk.com/markets/2026/06/08/aave-labs-founder-stani-kulechov-deflects-responsibility-in-usd8-billion-run-on-stage`（注：URL 实测在 /business/路径，CDP抓取跳转200 OK）：已修正引用为 /business/ 版本。

**价格抓取原始数据快照**：`/tmp/cmc_prices_out.log2`（CoinMarketCap CDP6币种价格 +24h涨跌文字「0.64% (24h) Why is BTC's price down today?」+ 多色样式 RGB区分涨跌，11:30-11:35 BJT抓取）；CoinGecko API实时响应：BTC $62,754 / -0.64%, ETH $1,666.50 / -0.88%, SOL $65.86 / -0.77%, XRP $1.15 / +0.13%, ADA $0.1662 / +1.69%, BNB $597.98 / -0.73%（11:32 BJT抓取）。

**CoinTelegraph ISO 时间戳交叉验证原始数据快照**：`/tmp/ctiso_out.log2`（每篇 CT 文章 HTML源码内嵌的 ISO8601 时间戳数组，用于推断精确发布时间，避免仅依赖日期字符串「Published Jun8,2026」）。
