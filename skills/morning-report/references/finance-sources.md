# 经济财经早报数据源

## 核心来源（人工浏览）

| 来源 | 网址 | 特色 | 抓取 |
| ------ | ------ | ------ | ------ |
| 华尔街见闻 | [https://wallstreetcn.com/](https://wallstreetcn.com/) | 快讯+资讯+行情，真实文章链接 | 🆕 Google 聚合 RSS |
| 金十数据 | [https://www.jin10.com/](https://www.jin10.com/) | 实时快讯流（非文章，仅人工浏览） | ❌ 无 RSS |
| 新浪财经 | [https://finance.sina.com.cn/](https://finance.sina.com.cn/) | 全面财经新闻 | ❌ RSS 已下线（404） |

## 🆕 RSS 可抓取来源（2026-07-31 新增，采集阶段推荐）

> **2026-07-31 源优化**：国内财经媒体普遍无原生 RSS，36氪是少数有稳定 RSS 的；华尔街见闻用 Google News 聚合绕过无 RSS 限制（`site:wallstreetcn.com` 查询，带中文标题+发布时间）。`fetch_feeds.py finance` 已验证 3 源可用。

| 来源 | RSS | 特色 | 状态 |
| ------ | ------ | ------ | ------ |
| 36氪 | 36kr.com/feed | 国内科技+财经，稳定 30 条，标题完整 | ✅ 主用 |
| 华尔街见闻（Google 聚合） | news.google.com/rss/search?q=site:wallstreetcn.com+when:2d | Google 聚合华尔街见闻近 2 天，带中文标题 | ✅ 主用 |
| Reddit r/Economics | reddit.com/r/Economics/.rss | 海外宏观视角补充 | 🟡 辅用（间歇 429） |

## 🆕 RSS 候选快速发现（采集阶段推荐）

**先用 RSS 发现候选 URL，再用 Browser 逐条核验（铁律不变）**：

```bash
# 抓 3 源最新素材池 → JSON
python3 ~/.openclaw/workspace/fetch_feeds.py finance
# 输出 ~/.openclaw/workspace/feeds/finance-<date>-<time>.json（约 36 条）
```

- 3 源已验证：36氪 / 华尔街见闻（Google 聚合）/ Reddit Economics
- **华尔街见闻** RSS 的 link 是 Google News 重定向（`news.google.com/rss/articles/...`），Browser 核验时**必须跟随到真实 wallstreetcn.com 文章页**再记录原文 URL
- 发现候选后，**仍必须**按下方流程逐条 Browser 核验
- `fetch_feeds.py` 统一管理 ai/web3/finance/side-hustle/dev 五类早报源

## 采集要求

1. **至少覆盖 3 个来源**，不足时再补充其他可靠财经媒体
2. **每个来源优先采集 1-3 条高信息密度新闻**
3. **必须找到具体文章 URL**，不能只写"数据来源：xxx"
4. **只选择 24 小时内发布的文章**
5. **逐条打开原文页验证标题、正文、发布时间**
6. **市场数据要包含具体数字**

## 分类建议

- 📊 全球市场（美股、A股、港股）
- 🌍 地缘政治
- 🛢️ 大宗商品（原油、黄金）
- 💵 外汇市场
- 📈 经济数据

## 重要提醒

- **必须为每条新闻添加具体原文链接**
- 格式：`[原文](https://wallstreetcn.com/articles/xxxxx)`
- 不要只写"数据来源：华尔街见闻"
- 不能把快讯流、行情列表页、频道页当成原文页

## 微型示例

**✅ 正确**：摘要写"纳指收涨 1.8%，10 年期美债收益率回落至 4.12%，正文同时提到市场在 CPI 数据公布前转向观望"，既有数字也有正文依据。

**❌ 错误**：摘要写"美股大涨，市场情绪回暖"，没有关键数字，也没有交代驱动因素。

## 关键新闻网站文章URL格式

- 华尔街见闻：`https://wallstreetcn.com/articles/xxxxx`
- 金十数据：`https://www.jin10.com/xxxxx`（快讯流，仅人工浏览）
- 新浪财经：`https://finance.sina.com.cn/xxxxx`
