# 早报模板

## 共用 frontmatter 规则

- 所有早报都使用 `categories: ["行业快讯"]`。
- 所有早报都必须包含 `draft: false` 和 `hiddenFromHomePage: true`。
- `date` 使用北京时间完整格式 `YYYY-MM-DDTHH:MM:SS+08:00`。
- `slug` 使用主 SKILL 中定义的固定模式，不要自行改写。
- `description` 为 50 到 100 字纯文本摘要。
- 每条新闻的原文字段固定写为 `原文: [原文](url)`。

## AI 新闻早报模板

```markdown
---
title: "AI新闻早报 YYYY-MM-DD"
date: YYYY-MM-DDTHH:MM:SS+08:00
slug: ai-morning-news-YYYY-MM-DD
description: "YYYY年MM月DD日 AI 新闻早报，精选过去 24 小时内值得关注的模型、产品、融资与行业动态。"
draft: false
categories: ["行业快讯"]
tags: ["AI", "新闻", "行业动态"]
hiddenFromHomePage: true
---

# AI 新闻早报 YYYY-MM-DD

🦞 每日08:00自动更新

---

## 💰 融资财报

### 标题
来源: 来源名称
原文: [原文](url)
摘要: 2-3句描述

## 🚀 产品发布

### 标题
来源: 来源名称
原文: [原文](url)
摘要: 2-3句描述

---

🦞 每日08:00自动更新

**数据来源**：36kr、量子位、机器之心、FT中文网、Hacker News
```

## 经济财经早报模板

```markdown
---
title: "经济财经早报 YYYY-MM-DD"
date: YYYY-MM-DDTHH:MM:SS+08:00
slug: financial-morning-news-YYYY-MM-DD
description: "YYYY年MM月DD日经济财经早报，汇总过去 24 小时内市场、宏观、商品与政策的重要变化。"
draft: false
categories: ["行业快讯"]
tags: ["财经", "早报", "美股", "市场"]
hiddenFromHomePage: true
---

# 经济财经早报 YYYY-MM-DD

🦞 每日08:30自动更新

---

## 📊 全球市场

### 标题
来源: 来源名称
原文: [原文](url)
摘要: 2-3句描述

## 🌍 地缘政治

### 标题
来源: 来源名称
原文: [原文](url)
摘要: 2-3句描述

---

🦞 每日08:30自动更新

**数据来源**：华尔街见闻、金十数据、新浪财经

**原文链接（已逐条核实）：**
- ✅ url1 - 说明
- ✅ url2 - 说明
```

## AI 副业早报模板

```markdown
---
title: "AI副业早报 YYYY-MM-DD"
date: YYYY-MM-DDTHH:MM:SS+08:00
slug: ai-side-hustle-morning-YYYY-MM-DD
description: "YYYY年MM月DD日 AI 副业早报，精选过去 24 小时内招聘、项目、工具与真实赚钱机会。"
draft: false
categories: ["行业快讯"]
tags: ["AI副业", "招聘", "赚钱", "V2EX"]
hiddenFromHomePage: true
---

# AI 副业早报 YYYY-MM-DD

🦞 每日09:00自动更新

---

## 🔥 今日热门

### 标题
来源: V2EX
发布者: xxx
原文: [原文](url)
摘要: 2-3句描述

标签: #标签1 #标签2

---

🦞 每日09:00自动更新

**数据来源**：V2EX、Reddit、微信公众号

**⚠️ 链接核查清单（已逐条验证）：**
- ✅ url1 - 已验证内容匹配
- ✅ url2 - 已验证内容匹配
```

## Web3 早报模板

```markdown
---
title: "Web3早报 YYYY-MM-DD"
date: YYYY-MM-DDTHH:MM:SS+08:00
slug: web3-morning-news-YYYY-MM-DD
description: "YYYY年MM月DD日 Web3 早报，汇总过去 24 小时内加密货币价格、监管、机构与链上生态动态。"
draft: false
categories: ["行业快讯"]
tags: ["Web3", "加密货币", "BTC", "ETH"]
hiddenFromHomePage: true
---

# Web3 早报 YYYY-MM-DD

🦞 每日08:00自动更新

---

## 📊 市场速览

| 币种 | 价格 | 24h涨跌 | 7d涨跌 |
| ------ | ------ | ------ | ------ |
| BTC | $00,000 | +0.00% | +0.00% |
| ETH | $0,000 | +0.00% | +0.00% |

## 🔥 今日热点

### 标题
来源: CoinDesk
原文: [原文](url)
摘要: 2-3句描述

## ⚠️ 风险提示

### 标题
来源: 华尔街见闻
原文: [原文](url)
摘要: 2-3句描述

---

🦞 每日08:00自动更新

**数据来源**：CoinMarketCap、CoinDesk、华尔街见闻
```

## 链接格式规范

### ✅ 正确格式

```markdown
原文: [原文](https://example.com/article/123)
```

### ❌ 错误格式

```markdown
- 原文: https://example.com/article/123  （裸URL）
- 来源: example.com  （无链接）
- 详情: 见原文  （无链接）
```

## frontmatter规范

```yaml
---
title: "AI新闻早报 2026-04-02"  # 必须包含日期
date: 2026-04-02T08:00:00+08:00  # 北京时间
slug: ai-morning-news-2026-04-02  # 小写英文连字符
description: "描述文字"  # 50-100字
draft: false
categories: ["行业快讯"]  # 早报统一用行业快讯
tags: ["AI", "新闻"]  # 2-5个精准标签
hiddenFromHomePage: true
---
```
