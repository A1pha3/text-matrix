---
title: "unclecode/crawl4ai：把 Web 抓成 LLM 友好 Markdown 的开源爬虫"
date: 2026-07-10T02:58:08+08:00
slug: "unclecode-crawl4ai-llm-friendly-web-scraper"
tags: ["Crawl4AI", "Web Scraper", "LLM", "RAG", "Python", "Playwright"]
categories: ["技术笔记"]
description: "梳理 Crawl4AI 的核心机制——71K+ stars 的开源 Web 爬虫，专注把任意网页转成干净 Markdown，配合 LLM 抽取、CSS 选择器、深度爬取，喂给 RAG / Agent 流水线。"
---

## 核心判断

Crawl4AI 解决的是“把网页喂给 LLM”这一高频但烦人的工程问题：传统爬虫（Scrapy、BeautifulSoup）输出 HTML 或粗糙文本，LLM 直接消费效果差；商业 API（Firecrawl、Diffbot、Browserless）按量收费、有锁定。Crawl4AI 的赌注是：**完全开源、完全本地、内置浏览器与 LLM 抽取，给出 LLM 友好的 Markdown**。71K+ stars、PyPI 月下载百万级，证明这是开发者社区真正用脚投票的方向。

## 基本盘

- GitHub：<https://github.com/unclecode/crawl4ai>
- Stars / Forks：约 71.7K / 7.4K（2026-07）
- 主语言：Python
- 许可证：Apache 2.0 + 商业服务
- 当前版本：v0.9.1（持续快速迭代）
- 主作者：unclecode（Vadim Markovtsev）

## 一句话定位

> Crawl4AI turns the web into clean, LLM ready Markdown for RAG, agents, and data pipelines.

## 核心能力

Crawl4AI 提供三类关键能力，分别对应“抓 → 清 → 提”三个阶段：

1. **抓（Browser）**：内置 Playwright + Chromium/Firefox/WebKit，支持 JavaScript 渲染、动态内容、cookie 持久化、proxy、headers、user profiles
2. **清（Markdown Generation）**：输出结构化 Markdown，提供 BM25 过滤、Cosine Similarity、CSS 选择器提取、Fit Markdown（启发式去噪）
3. **提（LLM Extraction）**：可接入任意 LLM（OpenAI、Anthropic、Gemini、本地 Ollama），按 JSON schema 提取结构化数据

外加：

- **Deep Crawl**：BFS/DFS 策略，爬取整个站点子树
- **Screenshots**：截图、PDF 渲染
- **Caching**：磁盘缓存避免重复抓取
- **Crash Recovery**：v0.8 起支持 `resume_state` + `on_state_change` 回调
- **Prefetch Mode**：v0.8 起新模式，URL 发现提速 5-10×

## 系统地图

```
URL 列表
    ↓
[Browser Manager] Playwright 多浏览器复用
    ↓
[Page Renderer] 执行 JS + 等待动态内容 + 截图
    ↓
[DOM Tree] 解析 HTML
    ↓
[Markdown Generator] Clean / Fit / Citation 三种策略
    ↓
[Optional: BM25 / Cosine] 过滤无关段落
    ↓
[Optional: LLM Extraction] 按 JSON schema 抽取
    ↓
输出 Markdown + 抽取 JSON + 截图 + metadata
```

## 三种使用方式

### 1. Python API（核心）

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
        )
        print(result.markdown)

asyncio.run(main())
```

### 2. LLM 抽取 + Schema

```python
import asyncio, json
from crawl4ai import AsyncWebCrawler, LLMConfig
from pydantic import BaseModel

class Product(BaseModel):
    name: str
    price: float
    description: str

schema = json.loads(Product.schema_json())

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.example.com/products",
            extraction_strategy="llm",
            llm_config=LLMConfig(provider="openai/gpt-4o-mini"),
            extraction_schema=schema,
        )
        for item in result.extracted_content:
            print(item)

asyncio.run(main())
```

### 3. CLI（v0.9 之后）

```bash
# 基础抓取
crwl https://www.nbcnews.com/business -o markdown

# 深度爬取，BFS，最多 10 页
crwl https://docs.crawl4ai.com --deep-crawl bfs --max-pages 10

# LLM 抽取，问“所有产品价格”
crwl https://www.example.com/products -q "Extract all product prices"
```

## 任务流案例：构建一个新闻 RAG 流水线

1. **安装**：`pip install crawl4ai && crawl4ai-setup`（自动下载浏览器）
2. **抓新闻**：写一个 50 行 Python 脚本，按 RSS 源读 URL，调 `AsyncWebCrawler().arun()` 抓 markdown
3. **去噪**：用 Fit Markdown 策略 + BM25 过滤无关段落
4. **分块**：用 `ChunkingStrategy(topic_based)` 把 markdown 分块
5. **embedding**：调 OpenAI text-embedding-3-small 或本地 BGE-M3 把 chunk 转向量
6. **存向量库**：ChromaDB / Qdrant / Milvus
7. **查询**：用户问题 → embedding → top-k → 拼上下文 → LLM 生成

整个流水线的“抓取 + 清洗”阶段交给 Crawl4AI，剩下都是标准 RAG 工具。

## 与相似项目的对比

| 工具 | 类型 | 内置 LLM | 部署形态 | 计费 |
|---|---|---|---|---|
| Crawl4AI | 开源 + 服务 | ✅ | Python / Docker / Cloud | 自托管免费 / 云服务按量 |
| Firecrawl | 商业 API | ✅ | SaaS | $0.06/页起 |
| Diffbot | 商业 API | ⚠️ | SaaS | 订阅制 |
| Scrapy + bs4 | 开源库 | ❌ | 自托管 | 免费，但需写大量代码 |
| Playwright | 开源库 | ❌ | 自托管 | 免费，浏览器自动化 |
| Jina Reader | 商业 API | ✅ | SaaS | 订阅 |
| Browserless | 商业 API | ❌ | SaaS / 自托管 | 订阅 |

Crawl4AI 的位置：**最完整的开源方案**，能力上接近 Firecrawl，但**需要自己托管和写代码**；如果你愿意付钱买 SLA，Firecrawl 更省事；如果你想完全免费，Crawl4AI + 自托管是当前最好的折中。

## 适用边界

适合：

- **RAG 工程师**：要给知识库喂外部网页内容
- **AI Agent 开发者**：Agent 需要联网搜资料、做调研、写报告
- **数据团队**：要批量抓电商、新闻、博客、论坛的结构化数据
- **想替代商业爬虫 API**：成本压力下走开源

不适合：

- **JS-heavy 网站需要代理池 + 高频反爬**：Crawl4AI 反爬能力有限（依赖 Playwright + proxy），比专业反爬服务（如 Bright Data）弱
- **超大规模（百万级 URL）**：单机部署成本高，建议用 Crawl4AI Cloud（其官方云服务）
- **纯 HTML 静态站**：用 BeautifulSoup + requests 就够了，没必要上 Crawl4AI

## 关键设计观察

1. **内置浏览器是关键差异化**：和 Scrapy 的“请求 + 解析”路线不同，Crawl4AI 走“真实浏览器渲染”路线，能处理 JS-heavy 站点
2. **多语言 LLM 适配**：支持 OpenAI、Anthropic、Gemini、本地 Ollama、LMStudio，配置层面统一 LLMConfig
3. **崩溃恢复**（v0.8 起）：深度爬取中断后可从 `resume_state` 恢复，对长任务关键
4. **零账号体验**：pip install 后即可使用，对个人开发者友好

## 近期版本亮点

- **v0.9.1**（2026-07）：12 个 bug 修复，新增 `preserve_classes`/`preserve_tags` 白名单、Windows 浏览器崩溃修复、Docker auth gate
- **v0.9.0**：Docker API 服务 secure-by-default 改造，绑定 loopback 除非给出 token
- **v0.8.7**：安全加固，修复多个 Docker API 漏洞（RCE、SSRF、auth bypass、文件写入、XSS、硬编码 JWT）
- **v0.8.0**：崩溃恢复 + Prefetch Mode（5-10× URL 发现提速）

## 学习路径建议

1. **第 1 小时**：`pip install crawl4ai` → `crwl https://example.com -o markdown`
2. **第 1 天**：Python API 抓 5 个新闻网站，对比 markdown 质量
3. **第 3 天**：加上 LLM 抽取 schema，对一个电商网站做产品抓取
4. **第 7 天**：跑 Deep Crawl 抓一个 docs 网站，做 RAG 验证
5. **第 14 天**：用 Docker 部署 Crawl4AI 服务 + Playwright pool，评估大规模性能

## 参考

- 仓库：<https://github.com/unclecode/crawl4ai>
- 官方文档：<https://docs.crawl4ai.com/>
- Discord：<https://discord.gg/jP8KfhDhyN>
- v0.9.1 Release Notes：<https://github.com/unclecode/crawl4ai/blob/main/docs/blog/release-v0.9.1.md>
- 趋势榜：Trendshift #1 开源爬虫
- PyPI：<https://pypi.org/project/crawl4ai/>
