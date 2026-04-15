# Web3早报数据源

## 核心来源

| 来源 | 网址 | 特色 | 状态 |
| ------ | ------ | ------ | ------ |
| CoinIndex | [https://coinindex.top/](https://coinindex.top/) | 实时加密货币价格、行情数据 | ⚠️ 备用 |
| CoinGecko API | [https://api.coingecko.com/api/v3/](https://api.coingecko.com/api/v3/) | 主流币种价格、24h/7d涨跌 | ✅ **主用** |
| CoinDesk | [https://www.coindesk.com/](https://www.coindesk.com/) | 权威加密货币新闻 | ⚠️ 备用 |
| CoinTelegraph | [https://cointelegraph.com/](https://cointelegraph.com/) | 英文加密货币新闻 | ✅ **主用** |
| 华尔街见闻Crypto | [https://wallstreetcn.com/](https://wallstreetcn.com/) | 中文加密货币快讯 | ⚠️ 备用 |

## 价格数据采集（API优先）

### 主用：CoinGecko API

```bash
# 主流币种价格（含24h和7d涨跌）
curl -s "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,ripple,cardano,binancecoin&vs_currencies=usd&include_24hr_change=true&include_7d_change=true"
```

**可用币种**：
- bitcoin (BTC)
- ethereum (ETH)
- solana (SOL)
- ripple (XRP)
- cardano (ADA)
- binancecoin (BNB)

### 备用：CoinIndex

如果 CoinGecko 不可用，使用浏览器打开 CoinIndex 获取价格数据。

### 格式要求

```markdown
| 币种 | 价格 | 24h涨跌 | 7d涨跌 |
|------|------|---------|--------|
| BTC | $74,536 | +5.24% | +12.35% |
| ETH | $2,386 | +9.07% | +18.42% |
```

## 新闻数据采集

### 主用：CoinTelegraph

1. 打开 `https://cointelegraph.com/` 获取新闻列表
2. 逐条打开新闻链接，验证 `datePublished` 字段
3. 只采集过去24小时内的新闻

**验证方法**：
```bash
# 在页面HTML中搜索 datePublished 字段
grep -oE '"datePublished":"[^"]+"' page.html
```

### 备用：CoinDesk

如果 CoinTelegraph 不可用，尝试 CoinDesk 新闻。

### 采集要求

1. **只采集过去24小时内发布的新闻**
2. **每个来源优先采集1-3条高信息密度新闻**
3. **必须找到具体文章URL**，不能只写"数据来源:CoinTelegraph"
4. **必须逐条打开原文页验证**：标题、正文、发布时间
5. **新闻来源与行情来源分开计算，不要混写**

## 网络故障切换机制

### 自动检测流程

1. **价格数据**：依次尝试 CoinGecko API → CoinIndex
2. **新闻数据**：依次尝试 CoinTelegraph → CoinDesk → 华尔街见闻

### 检测命令

```bash
# 检测 CoinGecko API
curl -s --connect-timeout 5 "https://api.coingecko.com/api/v3/ping"

# 检测 CoinTelegraph
curl -s --connect-timeout 5 "https://cointelegraph.com/" | head -20
```

### 故障处理

- **CoinGecko 不可用**：回退到 CoinIndex 浏览器采集
- **CoinTelegraph 不可用**：回退到 CoinDesk
- **全部不可用**：标注"数据源网络受限，行情数据仅供参考"

## 分类建议

- 🔥 今日热点(安全事件、监管动态)
- 💼 机构动态(交易所、资管公司布局)
- 📊 市场分析(BTC/ETH走势、情绪指标)
- 🔬 技术前沿(Layer2、DeFi、量子安全)
- ⚠️ 风险提示

## 格式要求

### 价格表格

```markdown
## 📊 今日行情

| 币种 | 价格 | 24h涨跌 | 7d涨跌 |
|------|------|---------|--------|
| BTC | $74,536 | +5.24% | +12.35% |
| ETH | $2,386 | +9.07% | +18.42% |
| SOL | $86.2 | +5.25% | +15.80% |
| XRP | $1.37 | +3.54% | +8.21% |
| ADA | $0.245 | +2.61% | +6.45% |
| BNB | $618.55 | +3.50% | +9.87% |

*行情来源：CoinGecko API*
```

### 新闻条目

```markdown
### 标题
来源: CoinTelegraph
原文: [原文](https://cointelegraph.com/news/xxx)
摘要: 2-3句描述
```

## 重要提醒

- **禁止使用模型知识库数据**，必须用 API 或 Browser 采集真实数据
- **禁止使用占位价格**（如 BTC $142,000 等幻觉价格）
- **禁止使用超过24小时的新闻**
- **禁止不打开原文就写摘要**
- 每条新闻必须包含 `[原文](url)` 格式的链接
- 不要新增"情绪""立场"这类主观字段，除非原文明确给出
- 文末"数据来源"需区分 行情来源 与 新闻来源，且只列实际使用来源
