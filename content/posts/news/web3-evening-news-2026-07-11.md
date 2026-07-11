---
title: "Web3晚报｜2026-07-11：Bonzo Lend 遭预言机攻击损失 900 万美元，美国 CBDC 禁令 7-12 自动生效，IMF 称稳定币可能放大货币挤兑"
date: 2026-07-11T20:03:30+08:00
slug: web3-evening-news-2026-07-11
description: "7-10 20:00 ~ 7-11 20:00 24h 晚报窗口：Bonzo Lend 因 Supra 预言机漏洞被攻击 900 万美元、美国住房法案含 CBDC 禁令将于 7-12 自动成法、IMF 工作论文警示稳定币在固定汇率制下可能放大货币挤兑、Coinbase Premium 反弹带动 BTC 重回 $64K、五名民主党参议员要求就特朗普加密持仓召开听证会。"
draft: false
categories: ["行业快讯"]
tags: ["Web3", "稳定币", "CBDC", "Bonzo", "IMF", "BTC", "ETH", "Chainlink"]
hiddenFromHomePage: true
---

## 行情速览（CoinGecko + Coinbase 双源验证 7-11 20:00 Asia/Shanghai 实时）

| 币种 | 价格 (USD) | 24h 涨跌 |
|---|---|---|
| BTC | **$64,144** | -0.30% |
| ETH | **$1,799.16** | +0.04% |
| SOL | **$78.02** | -1.58% |

行情观察：BTC 当日震荡于 $64K 附近，受 Coinbase Premium 反弹带动小幅回升；ETH 守住 $1,800 整数关口；SOL 跟随主流币回调。CoinGecko 与 Coinbase 报价在 BTC 上相差 4 美元、ETH 0.4 美元、SOL 0.02 美元，跨交易所价差收敛。日内 24h 成交量 BTC 约 280 亿美元，与上一交易日基本持平。

## 安全事件

**Bonzo Lend 因 Supra 预言机漏洞遭攻击，损失约 900 万美元。** Hedera 链上借贷协议 Bonzo Lend 在 7-11 11:56 UTC 披露一起预言机操纵事件——攻击者通过 Supra 链上预言体验证器的漏洞虚增 SAUCE 代币抵押品价格，随后借出价值约 900 万美元资产，远超实际抵押价值。Hedera 网络与 Bonzo Lend 应用本身按设计正常运行，问题集中在第三方预言机层的报价可信度。Cointelegraph 指出这是经典预言机失败案例：当应用层、风控层都按预期运作时，单一数据源失真就能把低价值抵押品放大为大规模流动性抽水工具。[原文](https://cointelegraph.com/news/bonzo-lend-9m-oracle-exploit-hedera)

**Ledger 安全团队披露 Tangem 硬件钱包签名流程漏洞。** Ledger 安全研究团队 7-10 公布 Tangem 硬件钱包签名流程中的安全缺陷，攻击者可借此诱导硬件钱包签署未被用户完全确认的交易。Tangem 官方回应称该漏洞"对普通用户的实际风险几乎可以忽略"，因为攻击需要物理接触设备。硬件钱包厂商之间的"负责任披露 + 厂商回应"链路已成常态，但普通用户难以判断漏洞真实影响。来源：Cointelegraph 7-10 相关报道。

## 监管与立法

**美国住房法案含 CBDC 禁令，7-12 自动成法。** 包含"禁止美联储在 2030 年 12 月 31 日前发行或创设任何与央行数字货币"实质相似的数字资产"条款的两党住房法案《21st Century ROAD to Housing Act》在众参两院 6 月通过后送交特朗普总统。特朗普 7-10 公开表示不会签署，但根据美国立法规则，总统 10 天内（不含周日）不签署即自动成法。截至 7-11 截止日，特朗普仍未签字，该法案将于 7-12（北京时间 7-13 上午）正式生效。Cointelegraph 指出这是美国首次通过立法明确禁止 CBDC 形态。Decrypt 同步报道指出，特朗普"不签字即成法"的策略意在让法案绕开行政签字环节直接生效，民主党议员称之为"制度破坏"。[Cointelegraph 原文](https://cointelegraph.com/news/us-cbdc-ban-donald-trump-housing-bill) / [Decrypt 原文](https://decrypt.co/373230/trump-wont-sign-housing-bill-cbdc-ban-become-law-anyway)

**五名民主党参议员要求就特朗普加密持仓召开听证会。** 5 名民主党参议员 7-10 发函，要求国会委员会"调查特朗普总统加密资产持仓的国家安全影响"，特别关注阿联酋实体或"未知第三方"对其政策的影响。背景是 CLARITY 法案等数字资产市场结构立法正在国会推进，民主党议员希望在立法表决前先审查总统个人加密持仓带来的潜在利益冲突。Decrypt 强调民主党方面将此与"宪法薪酬条款"挂钩，认为总统个人加密持仓已构成制度性利益冲突。[Cointelegraph 原文](https://cointelegraph.com/news/senate-democrats-hearings-donald-trump-crypto-clarity-act) / [Decrypt 原文](https://decrypt.co/373289/democrats-senate-hearings-trump-massive-crypto-profits)

**新罕布什尔州行政委员会否决 1 亿美元 BTC 储备债券。** 新罕布什尔州 5 人行政委员会 7-09 以 3:2 投票否决该州商业金融管理局（BFA）此前获批的 1 亿美元 BTC 储备债券发行方案。该方案曾于 2025 年 11 月获州长 Kelly Ayotte 支持，但州议会代表 Keith Ammon 形容这一否决"短视"，呼吁州行政委员会重新审议。州一级 BTC 储备试验目前仍集中在亚利桑那、得克萨斯等州。[原文](https://cointelegraph.com/news/new-hampshire-votes-against-bitcoin-bonds)

**MiCA 牌照只是起点，欧洲加密托管商将进入运营韧性审查。** 欧盟《加密资产市场监管法案》（MiCA）发牌后，欧洲证券与市场管理局（ESMA）将焦点从"准入授权"转向托管商的运营韧性审查。瑞士数字资产基础设施商 Taurus 联合创始人 Sebastien Dessimoz 表示："对托管商而言，牌照只是起跑线，不是终点。" 欧洲加密托管商未来需在网络安全、运营连续性、客户资产隔离等方面持续达标，否则面临牌照吊销。[原文](https://cointelegraph.com/news/mica-only-beginning-crypto-custodians-scrutiny)

## 机构与基建

**IMF 工作论文：稳定币可改善外汇获取，但也可能放大货币挤兑。** IMF 经济学家 Brandon Joel Tan 7-10 发布工作论文《Stablecoins and Fragility in Fixed Exchange Rate Regimes》，研究固定或高度管理汇率制度下稳定币对平行外汇市场的影响。论文认为：稳定币确实能在官方美元渠道紧张时帮助居民获得美元；但同一"高频可见的美元价格信号"也会成为市场逃离本币的协调信号，加剧货币挤兑。论文建议监管机构在危机期间对"异常大额、恐慌驱动"的稳定币交易实施临时限额。3 月 24 日金融稳定理事会（FSB）也曾警告美元稳定币可能引发新兴市场货币替代风险。[原文](https://cointelegraph.com/news/imf-stablecoins-fx-access-currency-runs)

**Kraken 围绕 AI 智能体重构移动应用。** Kraken 7-10 宣布将围绕 AI 智能体重构其移动 App：用户先设置财务目标与偏好，应用界面与推荐策略围绕这些目标个性化呈现，而非要求用户自寻复杂交易工具。背景是加密交易所与金融科技公司在 AI 个性化投顾赛道的竞争加速，Coinbase、Robinhood、Revolut 同期上线或预热类似功能。[原文](https://cointelegraph.com/news/kraken-to-rebuild-app-around-ai-powered-trading-agents-report)

**Robinhood AI 智能体 beta 版已服务超 7 万账户。** Robinhood 5 月底在股票与期权交易端上线 AI 智能体功能 beta，截至 7-10 已创建超 7 万个智能体账户。Robinhood 表示 AI 智能体"很快"将辅助加密交易，可能与 Robinhood Chain 一同扩大 AI 代理交易范围。Cointelegraph 报道指出，AI 智能体交易带来的合规与责任划分问题仍是监管重点关注方向。[原文](https://cointelegraph.com/news/robinhood-says-ai-agents-will-be-trading-for-crypto-users-soon)

**Backpack 推出代币化美股 7×24 交易。** 加密交易所 Backpack 7-10 上线代币化美股的 7×24 小时交易，首批覆盖 SpaceX、Micron、SanDisk 等标的，投资者获得底层证券直接所有权（非合成品），交易以法币或稳定币结算并即时交割。代币化股票正成为加密行业增长最快的细分赛道之一，Coinbase、Kraken 等也先后布局。[原文](https://cointelegraph.com/news/backpack-launches-247-trading-for-tokenized-us-equities)

**Binance 联合创始人：MiCA 截止后欧盟用户大量流向自托管。** Binance 联合 CEO 7-10 接受采访时披露：MiCA 合规截止日后，欧盟用户从 Binance 提款中绝大多数流向了自托管钱包与其他持牌平台，加密行业的"交易所 → 自托管"迁移潮在欧盟明显强化。MiCA 框架并未把欧盟用户"锁回"持牌交易所，反而推动了非托管钱包与去中心化金融的普及。来源：Cointelegraph / Decrypt 同步报道。

**渣打银行维持 $100,000 BTC 年底目标价。** 渣打银行 7-10 维持其 BTC 年底 $100,000 目标价，对冲基金 Strategy（MicroStrategy）的 BTC 减持"主要是沟通问题、不影响基本面"。Standard Chartered 数字资产研究全球主管 Geoff Kendrick 此前多次重申年底 $100K 目标，强调 ETF 资金流与企业资产负债表配置是核心驱动。来源：Decrypt 7-10 报道。

## 市场结构与资金流

**Coinbase Premium 突破 14 日均线，美国鲸鱼推动 BTC 重回 $64K。** CryptoQuant 分析师 Burak Kesmeci 7-10 指出，Coinbase Premium（Coinbase 与 Binance BTC/USDT 价差）已突破 14 日移动均线，显示美国一侧买盘动能"重新增强"。虽然 BTC 与 ETH 的 Coinbase Premium 仍处于负值区间，但已从近期低点反弹，与 BTC 价格回升至 $64K 的时间点高度吻合。[原文](https://cointelegraph.com/markets/bitcoin-whales-sent-btc-price-to-64k-as-coinbase-premium-broke-key-level-cryptoquant)

**7 月 BTC 涨近 10%，但分析师警告 8 月可能重复 2022 熊市剧本。** BTC 在 7 月头两周累计涨幅接近 10%，是 2022 年以来最佳 7 月表现。但 Cointelegraph 援引多位分析师警告，2022 年 7 月 BTC 同样上涨 17%（前月大跌 38% 后），但 8 月随即跌 14%、9 月再跌 3%。历史不会简单重复，但宏观流动性、企业资产负债表调整、ETF 资金流仍是 8 月关键变量。[原文](https://cointelegraph.com/markets/bitcoin-price-gains-nearly-10-in-july-but-traders-still-see-btc-copying-2022-bear-market)

**Empery Digital 抛售 1400 枚 BTC（近半数持仓），筹资 8700 万美元投 AI。** 比特币财库公司 Empery Digital 7-10 公告出售约 1400 枚 BTC（占其持仓近一半），筹资约 8700 万美元用于 AI 业务转型与债务偿还。这是 7 月以来首家公开宣布"大规模减持 BTC、转投 AI"的上市财库公司。Strategy 之外的小型财库公司正面临类似压力——BTC 价格盘整使募资能力受限，AI 业务被视为高估值退出通道。来源：Decrypt 7-10 报道（[原文](https://decrypt.co/373278/bitcoin-firm-empery-digital-dumps-half-btc-holdings-87-million)）。

**a16z 创始人 Marc Andreessen 出任美联储 AI 工作组联席主席。** 美联储主席 Kevin Warsh 7-10 宣布成立"生产力与就业工作组"（Productivity and Jobs task force），由 a16z 联合创始人 Marc Andreessen 与斯坦福经济学教授 Charles I. Jones（目前在 Anthropic 学术休假）、微软执行副总裁兼 Xbox CEO Asha Sharma 共同领导。该工作组将评估 AI 与其他新兴技术对生产率与就业的政策影响。[原文](https://cointelegraph.com/news/federal-reserve-a16z-co-founder-monetary-policy-task-force)

## 司法与执法

**美 DOJ 拟撤回对 7.22 亿美元 BitClub 庞氏骗局创始人的指控。** 美国司法部据 Bloomberg 7-11 报道，正在寻求撤回对 BitClub Network 创始人 Matthew Goettsche 的指控——Goettsche 被指控参与 2014-2019 年间 7.22 亿美元加密挖矿庞氏骗局，原定 10 月受审。但其 3 名同案被告已认罪，撤回指控将是美国加密执法史上的重大反转。BitClub 案曾是美国早期"加密庞氏骗局"标志性案件之一。[原文](https://cointelegraph.com/news/doj-to-dismiss-charges-against-alleged-722m-bitclub-crypto-fraudster-bloomberg)

**美 DOJ 起诉联邦囚犯转移 29 万美元被没收 Kraken 加密资产。** 美国检察官 7-10 起诉正在服刑的 Rossen Iossifov，指控其通过交易所与混币器转移约 29 万美元来自受冻结 Kraken 账户的已没收加密资产。案件显示：在没收令已生效后试图转移资产仍可能触发新的刑事指控，构成"二阶犯罪"风险。[原文](https://cointelegraph.com/news/us-prisoner-290k-crypto-restrained-kraken-account)

## 政策与行业观点

**美国加密游说团体 1.89 亿美元运动能否推动 CLARITY 法案过关？** Cointelegraph 深度长文 7-10 复盘加密行业在华盛顿的影响力建设——过去三年加密 PAC 与行业组织投入约 1.89 亿美元用于国会游说与候选人支持，规模已超过传统金融业。CLARITY 法案是当前焦点，该法案试图明确 SEC 与 CFTC 对数字资产的管辖分工，被视为美国加密监管"破局点"。Cointelegraph Features 频道同时发出反向声音：5 名民主党参议员同日发函要求审查总统个人加密持仓，显示政治极化使法案过关难度上升。[Cointelegraph 原文](https://cointelegraph.com/features/how-crypto-built-political-influence-in-washington)

---

## 数据来源

1. [CoinMarketCap - Bitcoin 实时价格页](https://coinmarketcap.com/currencies/bitcoin/)
2. [CoinMarketCap - Ethereum 实时价格页](https://coinmarketcap.com/currencies/ethereum/)
3. [CoinMarketCap - Solana 实时价格页](https://coinmarketcap.com/currencies/solana/)
4. [CoinDesk - Ethereum 实时价格页](https://www.coindesk.com/price/ethereum)
5. [CoinDesk - Solana 实时价格页](https://www.coindesk.com/price/solana)
6. [Cointelegraph - Bonzo Lend $9M oracle exploit (2026-07-11)](https://cointelegraph.com/news/bonzo-lend-9m-oracle-exploit-hedera)
8. [Cointelegraph - IMF Stablecoins paper (2026-07-11)](https://cointelegraph.com/news/imf-stablecoins-fx-access-currency-runs)
9. [Cointelegraph - Bitcoin July gains warn of 2022 repeat (2026-07-11)](https://cointelegraph.com/markets/bitcoin-price-gains-nearly-10-in-july-but-traders-still-see-btc-copying-2022-bear-market)
10. [Cointelegraph - Robinhood AI agents 70k accounts (2026-07-11)](https://cointelegraph.com/news/robinhood-says-ai-agents-will-be-trading-for-crypto-users-soon)
11. [Cointelegraph - DOJ to dismiss BitClub charges (2026-07-11)](https://cointelegraph.com/news/doj-to-dismiss-charges-against-alleged-722m-bitclub-crypto-fraudster-bloomberg)
12. [Cointelegraph - Kraken rebuild app AI agents (2026-07-10)](https://cointelegraph.com/news/kraken-to-rebuild-app-around-ai-powered-trading-agents-report)
13. [Cointelegraph - Senate Democrats Trump crypto hearings (2026-07-10)](https://cointelegraph.com/news/senate-democrats-hearings-donald-trump-crypto-clarity-act)
14. [Cointelegraph - US CBDC ban housing bill (2026-07-10)](https://cointelegraph.com/news/us-cbdc-ban-donald-trump-housing-bill)
15. [Cointelegraph - New Hampshire BTC bonds rejected (2026-07-10)](https://cointelegraph.com/news/new-hampshire-votes-against-bitcoin-bonds)
16. [Cointelegraph - Backpack tokenized equities 24/7 (2026-07-10)](https://cointelegraph.com/news/backpack-launches-247-trading-for-tokenized-us-equities)
17. [Cointelegraph - Coinbase Premium BTC $64K (2026-07-10)](https://cointelegraph.com/markets/bitcoin-whales-sent-btc-price-to-64k-as-coinbase-premium-broke-key-level-cryptoquant)
18. [Cointelegraph - a16z Andreessen Federal Reserve task force (2026-07-10)](https://cointelegraph.com/news/federal-reserve-a16z-co-founder-monetary-policy-task-force)
19. [Cointelegraph - MiCA custodians scrutiny (2026-07-10)](https://cointelegraph.com/news/mica-only-beginning-crypto-custodians-scrutiny)
20. [Cointelegraph - Crypto lobby $189M CLARITY campaign (2026-07-10)](https://cointelegraph.com/features/how-crypto-built-political-influence-in-washington)
21. [Cointelegraph - US prisoner $290K Kraken crypto (2026-07-10)](https://cointelegraph.com/news/us-prisoner-290k-crypto-restrained-kraken-account)
22. [Decrypt - Democrats Senate hearings Trump crypto (2026-07-10)](https://decrypt.co/373289/democrats-senate-hearings-trump-massive-crypto-profits)
23. [Decrypt - Trump won't sign housing bill CBDC ban (2026-07-10)](https://decrypt.co/373230/trump-wont-sign-housing-bill-cbdc-ban-become-law-anyway)