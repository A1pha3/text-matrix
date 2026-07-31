# AI新闻早报数据源

## 中文优先来源

| 来源 | 网址 | 特色 |
| ------ | ------ | ------ |
| 36kr AI频道 | [https://www.36kr.com/information/AI/](https://www.36kr.com/information/AI/) | AI行业权威媒体 |
| 量子位 | [https://www.qbitai.com/](https://www.qbitai.com/) | AI技术前沿 |
| 机器之心 | [https://www.jiqizhixin.com/](https://www.jiqizhixin.com/) | AI深度分析 |
| FT中文网 | [https://www.ftchinese.com/](https://www.ftchinese.com/) | 国际视角 |
| 虎嗅AI | [https://www.huxiu.com/channel/1008](https://www.huxiu.com/channel/1008) | 商业洞察 |

## 海外补充来源

> **🆕 2026-07-31 源优化**:新增 5 个已验证英文 / 官方源(Import AI / DeepMind / Anthropic / HuggingFace / Ben's Bites),带 RSS / sitemap,可被 `fetch_feeds.py` 自动抓取。官方研究源(DeepMind / Anthropic / HuggingFace)是 AI 主线信号的一手来源,优先级高于通用科技媒体。

| 来源 | 网址 | RSS / sitemap | 特色 | 状态 |
| ------ | ------ | ------ | ------ | ------ |
| Import AI | importai.substack.com | importai.substack.com/feed | 英文研究深度(Jack Clark 周刊) | ✅ 主用 |
| Google DeepMind | deepmind.google | deepmind.google/blog/rss.xml | 官方研究 / 产品(Gemini / Robotics) | ✅ 主用 |
| Anthropic | anthropic.com | sitemap.xml + lastmod(filter `/news/` + `/research/`) | 官方安全 / 研究 / 模型 | ✅ 主用 |
| HuggingFace | huggingface.co | sitemap-blog.xml + lastmod | 社区 / 模型 / 安全事件 | ✅ 主用 |
| Ben's Bites | bensbites.com | bensbites.com/feed | 工具 / 创业 / 产品视角 | ✅ 主用 |
| Hacker News AI | news.ycombinator.com | news.ycombinator.com/rss | 工程师热点 / 社区信号 | ✅ 主用 |
| TechCrunch AI | techcrunch.com/category/artificial-intelligence/ | — | 创业投资 | 🟡 辅用 |
| Wired AI | wired.com/tag/ai/ | — | 深度报道 | 🟡 辅用 |

## 🆕 RSS 候选快速发现(2026-07-31 新增,采集阶段推荐)

**先用 RSS / sitemap 发现候选 URL,再用 Browser 逐条核验(铁律不变)**:

```bash
# 抓 7 源最新素材池 → JSON
python3 ~/.openclaw/workspace/fetch_feeds.py ai
# 输出 ~/.openclaw/workspace/feeds/ai-<date>-<time>.json(约 78 条)
```

- 7 源已验证可用:量子位 / Import AI / Ben's Bites / DeepMind / Hacker News / HuggingFace(sitemap)/ Anthropic(sitemap)
- **HuggingFace** 用 `sitemap-blog.xml`、**Anthropic** 用 `sitemap.xml` + lastmod filter `/news/` + `/research/`(两者均无原生 RSS,靠 sitemap+lastmod 解决,不必自建 RSSHub)
- 发现候选后,**仍必须**按下方流程逐条 Browser 核验
- `fetch_feeds.py` 同时管理 Web3 早报 7 源,早报架构统一

## 采集要求

1. **至少覆盖 3 个来源**，其中至少 2 个中文来源、1 个海外来源
2. **单个来源优先采集 1-3 条高质量新闻**，不要为凑数保留重复稿
3. **只选择 24 小时内发布的文章**
4. **逐条打开记录原文 URL**
5. **原文链接必须是最终文章页**，不能把频道页、标签页、聚合页当原文
6. **筛选标准**：重要性高、信息增量高、与 AI 主线直接相关

## 聚合来源说明

- Hacker News 主要用于发现候选条目；若帖子指向外部报道，优先使用外部文章页作为原文。
- 若确实要引用 Hacker News 讨论本身，摘要只能基于该讨论帖可见内容，不能擅自补写外部事实。

## 微型示例

**✅ 正确**：在 Hacker News 看到 OpenAI 融资讨论帖，点进外部报道页后确认发布时间与正文，再把外部报道页写为原文链接。

**❌ 错误**：只在 Hacker News 列表看到标题，就把该标题改写成“OpenAI 完成新一轮融资并将加速全球扩张”。

## 分类建议

- 💰 融资财报
- 🚀 产品发布
- 🔬 技术进展
- 📰 行业动态
- 🛠️ 开源工具
- 💼 商业应用
