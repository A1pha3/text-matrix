---
title: "unclecode/crawl4ai：把 Web 抓成 LLM 友好 Markdown 的开源爬虫"
date: 2026-07-10T02:58:08+08:00
slug: "unclecode-crawl4ai-llm-friendly-web-scraper"
github_repo: "unclecode/crawl4ai"
source_key: "gh:unclecode/crawl4ai"
tags: ["LLM", "RAG", "Python", "Playwright"]
categories: ["技术笔记"]
description: "梳理 Crawl4AI 的核心机制——82K+ stars 的开源 Web 爬虫，专注把任意网页转成干净 Markdown，配合 LLM 抽取、CSS 选择器、深度爬取，喂给 RAG / Agent 流水线。"
---

## 核心判断

Crawl4AI 解决的是"把网页喂给 LLM"这一高频但烦人的工程问题：传统爬虫（Scrapy、BeautifulSoup）输出 HTML 或粗糙文本，LLM 直接消费效果差；商业 API（Firecrawl、Diffbot、Browserless）按量收费、有锁定。Crawl4AI 的赌注是：**完全开源、完全本地、内置浏览器与 LLM 抽取，给出 LLM 友好的 Markdown**。82K+ stars、PyPI 月下载约 135 万，说明这个定位踩中了当前 RAG / Agent 工程的真实需求。

## 基本盘

- GitHub：<https://github.com/unclecode/crawl4ai>
- Stars / Forks：约 82.5K / 8.5K（2026-09 核实）
- 主语言：Python
- 许可证：Apache 2.0（README 另附署名倡议，推荐使用者保留项目徽章或文字署名）
- 当前版本：v0.9.3（2026-08-31）
- 主作者：unclecode（Kidocode——东南亚一家编程与商业学校的创始人，常住新加坡）

## 一句话定位

> Crawl4AI turns the web into clean, LLM ready Markdown for RAG, agents, and data pipelines.

## 核心能力

Crawl4AI 提供三类关键能力，分别对应"抓 → 清 → 提"三个阶段：

1. **抓（Browser）**：内置 Playwright + Chromium/Firefox/WebKit，支持 JavaScript 渲染、动态内容、cookie 持久化、proxy、headers、user profiles
2. **清（Markdown Generation）**：输出结构化 Markdown，提供 BM25 过滤、Cosine Similarity 过滤、CSS 选择器提取、Fit Markdown（启发式去噪）
3. **提（LLM Extraction）**：可接入任意 LLM（OpenAI、Anthropic、Gemini、本地 Ollama），按 JSON schema 提取结构化数据

外加：

- **Deep Crawl**：BFS / DFS / Best-First 三种策略，配 `FilterChain` 做 URL 过滤
- **Screenshots**：截图、PDF 渲染
- **Caching**：磁盘缓存避免重复抓取
- **Crash Recovery**：v0.8.0 起支持 `resume_state` + `on_state_change` 回调，深度爬取中断后可续跑
- **Prefetch Mode**：v0.8.0 起的两阶段爬取，`prefetch=True` 时跳过 markdown 生成与抽取、只回传 HTML 和链接做快速 URL 发现（官方宣称提速 5-10×，未附基准细节）

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

抽取策略构造为 `LLMExtractionStrategy` 对象，经 `CrawlerRunConfig` 传入 `arun()`：

```python
import asyncio, json, os
from crawl4ai import (
    AsyncWebCrawler, BrowserConfig, CrawlerRunConfig,
    CacheMode, LLMConfig, LLMExtractionStrategy,
)
from pydantic import BaseModel

class Product(BaseModel):
    name: str
    price: str
    description: str

llm_strategy = LLMExtractionStrategy(
    llm_config=LLMConfig(
        provider="openai/gpt-4o-mini",
        api_token=os.getenv("OPENAI_API_KEY"),
    ),
    schema=Product.model_json_schema(),
    extraction_type="schema",
    instruction="Extract all product objects with name, price, and description.",
    chunk_token_threshold=1000,
    apply_chunking=True,
    input_format="markdown",
)

crawl_config = CrawlerRunConfig(
    extraction_strategy=llm_strategy,
    cache_mode=CacheMode.BYPASS,
)

async def main():
    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        result = await crawler.arun(
            url="https://www.example.com/products",
            config=crawl_config,
        )
        if result.success:
            products = json.loads(result.extracted_content)
            print(f"Extracted {len(products)} products")
            llm_strategy.show_usage()  # 打印 token 用量
        else:
            print(result.error_message)

asyncio.run(main())
```

两点容易踩坑：`price` 建议用 `str` 而不是 `float`，因为 LLM 会输出 `"$9.99"` 这类带符号的字符串，直接映射 float 会解析失败；`result.extracted_content` 是 JSON 字符串，需要 `json.loads()` 之后才能按列表遍历。

### 3. CLI（crwl 命令）

```bash
# 基础抓取，输出原始 markdown
crwl https://www.nbcnews.com/business -o markdown

# 输出去噪后的 markdown（等价于 Fit Markdown）
crwl https://www.nbcnews.com/business -o markdown-fit

# 用配置好的 LLM 对页面提问
crwl https://example.com -q "What is the main topic discussed?"
```

`-o` 支持四种取值：`all`（含 metadata 的完整结果）、`json`（使用抽取策略时的结构化输出）、`markdown`/`md`、`markdown-fit`/`md-fit`。首次使用 `-q` 会提示配置 LLM provider 和 API token，配置落在 `~/.crawl4ai/global.yml`，用 Ollama 则无需 token。注意 CLI 没有 `--deep-crawl` 参数，深度爬取只能走 Python API。

## 任务流案例：构建一个新闻 RAG 流水线

1. **安装**：`pip install crawl4ai && crawl4ai-setup`（后者自动下载浏览器）
2. **抓新闻**：写一个几十行的 Python 脚本，按 RSS 源读 URL，调 `AsyncWebCrawler().arun()` 抓 markdown
3. **去噪**：用 Fit Markdown 策略 + BM25 过滤无关段落
4. **分块**：用 `RegexChunking`（按空行切）或 `TopicSegmentationChunking`（TextTiling 主题切分）做分块，也可以接自己的分块器
5. **embedding**：调 OpenAI text-embedding-3-small 或本地 BGE-M3 把 chunk 转向量
6. **存向量库**：ChromaDB / Qdrant / Milvus
7. **查询**：用户问题 → embedding → top-k → 拼上下文 → LLM 生成

整个流水线的"抓取 + 清洗"阶段交给 Crawl4AI，剩下都是标准 RAG 工具。

## 与相似项目的对比

| 工具 | 类型 | 内置 LLM | 部署形态 | 计费 |
|---|---|---|---|---|
| Crawl4AI | 开源库 + 可选云服务 | ✅ | Python / Docker | 自托管免费 |
| Firecrawl | SaaS + 开源 SDK | ✅ | 云服务 | 免费层每月 1,000 credits，1 credit = 1 页基础抓取，付费 $16/月起 |
| Diffbot | 商业 API | ⚠️ | SaaS | 订阅制 |
| Scrapy + bs4 | 开源库 | ❌ | 自托管 | 免费，但需写大量代码 |
| Playwright | 开源库 | ❌ | 自托管 | 免费，浏览器自动化 |
| Jina Reader | 商业 API | ✅ | SaaS | 按用量计费 |
| Browserless | 商业 API | ❌ | SaaS / 自托管 | 订阅 |

Crawl4AI 的位置：**能力上最完整的开源方案**。它需要自己托管和写代码；愿意付钱买省心，Firecrawl 更合适；对成本敏感或数据不能出内网，Crawl4AI + 自托管是当前的默认选择。

## 适用边界

适合：

- **RAG 工程师**：要给知识库喂外部网页内容
- **AI Agent 开发者**：Agent 需要联网搜资料、做调研、写报告
- **数据团队**：要批量抓电商、新闻、博客、论坛的结构化数据
- **想替代商业爬虫 API**：成本压力下走开源

不适合：

- **JS-heavy 网站需要代理池 + 高频反爬**：Crawl4AI 反爬能力有限（依赖 Playwright + proxy 配置），比 Bright Data 这类专业反爬服务弱
- **超大规模（百万级 URL）**：单机靠 `arun_many()` + 内存自适应调度器（`MemoryAdaptiveDispatcher`，并发默认 10）可以撑住中量级，百万级 URL 需要自建分发队列和多机部署
- **纯 HTML 静态站**：用 BeautifulSoup + requests 就够了，没必要起浏览器

## 关键设计观察

1. **内置浏览器是关键差异化**：和 Scrapy 的"请求 + 解析"路线不同，Crawl4AI 走"真实浏览器渲染"路线，能处理 JS-heavy 站点，代价是资源占用和速度
2. **多语言 LLM 适配**：支持 OpenAI、Anthropic、Gemini、本地 Ollama、LMStudio、Bedrock，配置层面统一在 `LLMConfig`
3. **崩溃恢复**（v0.8.0 起）：深度爬取中断后从 `resume_state` 续跑，长任务不用从头再来
4. **零账号体验**：pip install 后即可使用，不注册、不联网验证
5. **安全响应是一条完整的线**：0.8.7 集中修复两个 CVSS 9.8 的前认证 RCE（AST 沙箱逃逸、hook 沙箱逃逸）和硬编码 JWT 密钥；0.9.0 干脆把 Docker API 重构成 secure-by-default——默认要求 `CRAWL4AI_API_TOKEN`，无 token 时只绑定 loopback，`js_code`、`proxy`、`cookies` 等敏感字段一律拒绝从网络请求传入（HTTP 400）；0.9.3 收尾 PDF 处理路径的 5 个协同披露漏洞。每个漏洞都有 GHSA 编号和研究者署名，这个响应节奏对自托管部署是重要信号

## 近期版本亮点

- **v0.9.3**（2026-08-31）：安全发布。修复 PDF 处理路径与 Docker Playground 的 5 个协同披露漏洞（任意文件写入 CWE-22、SSRF CWE-918、无上限 DoS CWE-400、两类 XSS CWE-79），附带 33 个 bug 修复；无新特性、无破坏性变更
- **v0.9.2 / v0.9.1**（2026-07）：维护版本
- **v0.9.0**（2026-06-18）：Docker API secure-by-default 改造。默认认证 + loopback 绑定、请求信任边界、声明式 hooks 取代任意 hook 代码、JWT 重签。仅影响自托管 Docker API，pip SDK 不受影响
- **v0.8.7**（2026-06-01）：集中安全加固（RCE ×2、硬编码 JWT、任意文件写入、SSRF ×2、鉴权绕过、存储 XSS），同时新增 DomainMapper 域名发现功能
- **v0.8.0**（2026-01-12）：深度爬取崩溃恢复（`resume_state` + `on_state_change`）、Prefetch 两阶段爬取、HTTP 策略代理支持

## 学习路径建议

1. **第 1 小时**：`pip install crawl4ai` → `crwl https://example.com -o markdown`
2. **第 1 天**：Python API 抓 5 个新闻网站，对比 markdown 质量
3. **第 3 天**：加上 LLM 抽取 schema，对一个电商网站做产品抓取
4. **第 7 天**：用 `BFSDeepCrawlStrategy` 抓一个 docs 网站，做 RAG 验证
5. **第 14 天**：用 Docker 部署 Crawl4AI 服务（记得先配 `CRAWL4AI_API_TOKEN`），评估并发性能

深度爬取的最小示例：

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(
        max_depth=2,
        include_external=False,
        max_pages=30,
    ),
    verbose=True,
)

async with AsyncWebCrawler() as crawler:
    results = await crawler.arun("https://docs.crawl4ai.com", config=config)
    for r in results:
        print(r.url, r.metadata.get("depth"))
```

## 参考

- 仓库：<https://github.com/unclecode/crawl4ai>
- 官方文档：<https://docs.crawl4ai.com/>
- CHANGELOG（含各版本安全公告与研究者致谢）：<https://github.com/unclecode/crawl4ai/blob/main/CHANGELOG.md>
- Deep Crawling 文档：<https://docs.crawl4ai.com/core/deep-crawling/>
- LLM 抽取文档：<https://docs.crawl4ai.com/extraction/llm-strategies/>
- CLI 文档：<https://docs.crawl4ai.com/core/cli/>
- PyPI：<https://pypi.org/project/crawl4ai/>
