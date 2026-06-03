# 早报模板

## 共用 frontmatter 规则

- 所有早报都使用 `categories: ["行业快讯"]`。
- 所有早报都必须包含 `draft: false` 和 `hiddenFromHomePage: true`。
- `date` 使用北京时间完整格式 `YYYY-MM-DDTHH:MM:SS+08:00`。
- **`date` 硬性规则：必须等于或早于「本份早报实际写入磁盘的时刻」，严禁填入「计划发布时刻」**。例如「计划发布时刻」是 08:30、但实际写入磁盘可能是 08:27，如果 date 填 08:30，Hugo 提前构建会扫到该文件并判定为「未来页面」整篇排除（2026-06-03 financial-morning-news 故障即此原因）。
  - **推荐公式**：`date = 当前北京时间 - 5 分钟`（如实际生成 10:00 → date 填 09:55）。保证 5 分钟内的 Hugo 构建均不会判为未来。
  - **绝对禁止**：把「计划发布时刻」（如 08:00 / 08:30 / 09:00）直接作为 date 填入 frontmatter。
  - **验证**：生成后必须检查 frontmatter date < 当前系统时间，且 date 早于 git commit 时间。
- `slug` 使用主 SKILL 中定义的固定模式，不要自行改写。
- `description` 为 50 到 100 字纯文本摘要。
- 每条新闻的原文字段固定写为 `原文: [原文](url)`。
- 输出文件名固定为 `slug.md`。
- 文末“数据来源”只列正文实际引用过的来源，不要照抄模板示例。
- 正文不要再写 H1；页面主标题由 frontmatter 的 `title` 提供。

## 修稿场景通用规则

- 如果用户提供的是已有早报，先把现稿拆成“待核验条目清单”，不要把原稿摘要当事实来源。
- 无法打开稳定原文页、发布时间超出 24 小时、标题与正文不符的条目必须删除或替换。
- 修稿完成后，也要补齐 frontmatter、原文链接格式和文末数据来源，不允许只修正文不修结构。

## 生成后自检回执模板

生成或修复任一早报后，内部至少形成以下回执：

```text
文件名：slug.md
时间窗结果：通过 / 失败
已保留条目数：N
已丢弃条目数：N
丢弃原因：超出24h / 无稳定原文页 / 标题正文不符 / 信息密度不足 / 链接失效
来源数：N
结构检查：frontmatter / 原文字段 / 标签数 / 数据来源汇总 全部通过或列出失败项
```

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

**数据来源**：来源1、来源2、来源3（只列正文实际引用来源）
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

**数据来源**：来源1、来源2、来源3（只列正文实际引用来源）

**原文链接（已逐条核实，仅列正文实际引用链接）：**
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

**数据来源**：来源1、来源2、来源3（只列正文实际引用来源）

**⚠️ 链接核查清单（已逐条验证，仅列正文实际引用链接）：**
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

**数据来源**：来源1、来源2、来源3（只列正文实际引用来源）
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

## 短样稿示例

以下示例只展示成稿力度与结构，不可直接照抄；正式生成时必须替换为当日真实采集结果。

### AI 新闻早报短样稿

```markdown
---
title: "AI新闻早报 2026-04-07"
date: 2026-04-07T08:00:00+08:00
slug: ai-morning-news-2026-04-07
description: "2026年4月7日 AI 新闻早报，汇总过去 24 小时内模型发布、企业合作与行业投融资的关键变化。"
draft: false
categories: ["行业快讯"]
tags: ["AI", "模型发布", "企业服务"]
hiddenFromHomePage: true
---

🦞 每日08:00自动更新

---

## 🚀 产品发布

### 某模型厂商发布企业版智能代理平台
来源: TechCrunch
原文: [原文](https://example.com/ai-agent-platform)
摘要: 厂商在正文中公布了企业版智能代理平台的工作流编排、权限控制和 API 接入方式，重点面向客服与销售场景。文章还提到首批合作客户已开始灰度上线，说明产品已进入商业落地阶段，而不是停留在概念发布。

## 💼 商业应用

### 国内云厂商上线 AI 客服解决方案
来源: 36kr
原文: [原文](https://example.com/ai-support-suite)
摘要: 报道披露该方案将知识库检索、对话总结和工单分发打通，目标是缩短人工客服处理链路。正文还给出了企业试点后的响应时间改善情况，使这条新闻具备可量化的信息增量。

---

🦞 每日08:00自动更新

**数据来源**：TechCrunch、36kr
```

### Web3 早报短样稿

```markdown
---
title: "Web3早报 2026-04-07"
date: 2026-04-07T08:00:00+08:00
slug: web3-morning-news-2026-04-07
description: "2026年4月7日 Web3 早报，汇总过去 24 小时内主流币价格、监管动态与机构动作。"
draft: false
categories: ["行业快讯"]
tags: ["Web3", "BTC", "ETH", "监管"]
hiddenFromHomePage: true
---

🦞 每日08:00自动更新

---

## 📊 市场速览

| 币种 | 价格 | 24h涨跌 | 7d涨跌 |
| ------ | ------ | ------ | ------ |
| BTC | $68,420 | +1.8% | +4.1% |
| ETH | $3,540 | +2.3% | +5.0% |

## 🔥 今日热点

### 某国监管机构发布稳定币新规草案
来源: CoinDesk
原文: [原文](https://example.com/stablecoin-draft)
摘要: 正文显示，新规草案重点围绕储备透明度、发行人披露义务和跨境结算合规展开。文章同时提到多家交易平台正在评估对稳定币交易对和托管流程的影响，使这条新闻不仅有政策面信息，也有直接市场含义。

---

🦞 每日08:00自动更新

**数据来源**：行情：CoinMarketCap；新闻：CoinDesk
```
