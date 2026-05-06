---
title: "Scrapling：现代网页爬虫框架·自适应·反反爬"
date: "2026-04-12T02:31:39+08:00"
slug: scrapling-adaptive-web-scraping-framework-guide
description: "Scrapling 是一个现代网页爬虫框架，具有自适应解析、反反爬绕过、并发爬取等功能，性能比 MechanicalSoup 快 767 倍。"
draft: false
categories: ["技术笔记"]
tags: ["爬虫", "Python", "网页抓取", "反反爬", "并发"]
---

# Scrapling：现代网页爬虫框架——自适应、反反爬、并发爬取

## 一、项目概述

### 1.1 Scrapling 是什么

**Scrapling** 是 D4Vinci 开发的**自适应网页爬虫框架**，能够处理从单次请求到大规模爬取的各类场景。其核心特点是：

- **自适应解析**：网站结构变化时自动定位元素
- **反反爬绕过**：开箱即用绕过 Cloudflare Turnstile 等反爬机制
- **并发爬取**：支持 Scrapy 风格的 Spider 框架
- **AI 集成**：内置 MCP Server，支持 AI 辅助爬取

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | 36.1k ⭐ |
| Forks | 3.1k |
| 最新版本 | v0.4.5 (2026-04-07) |
| 许可证 | BSD-3-Clause |
| 语言 | Python 99.9% |
| 贡献者 | 17 |

### 1.3 为什么选择 Scrapling

| 特点 | 说明 |
|------|------|
| 🤖 自适应解析 | 网站改版后自动重新定位元素 |
| 🛡️ 反反爬 | 绕过 Cloudflare Turnstile |
| ⚡ 性能卓越 | 文本提取 2.02ms（比 MechanicalSoup 快 767 倍）|
| 🕷️ Spider 框架 | Scrapy 风格，支持并发、暂停/恢复 |
| 🔌 AI 集成 | MCP Server，AI 辅助数据提取 |
| 🐳 Docker 支持 | 一键部署，含所有浏览器 |

---

## 二、技术架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Scrapling                                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  Spiders   │  │  Fetchers  │  │   Parser   │       │
│  │ (爬取框架) │  │ (请求引擎) │  │ (解析引擎) │       │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
│         └────────────────┼────────────────┘              │
│                          ▼                                    │
│  ┌─────────────────────────────────────────────────┐     │
│  │              Core Engine                           │     │
│  │  • Session Management                            │     │
│  │  • Proxy Rotation                               │     │
│  │  • Adaptive Element Tracking                     │     │
│  │  • Checkpoint/Pause & Resume                   │     │
│  └─────────────────────────────────────────────────┘     │
│                          ▼                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   Fetcher   │  │StealthyFetcher│ │DynamicFetcher│     │
│  │  (HTTP)    │  │  (反反爬)   │  │  (浏览器)  │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件

| 组件 | 功能 | 适用场景 |
|------|------|----------|
| **Fetcher** | HTTP 请求，TLS 指纹伪装 | 静态页面 |
| **StealthyFetcher** | 高级反反爬，Cloudflare 绕过 | 反爬网站 |
| **DynamicFetcher** | 浏览器自动化，JS 渲染 | SPA/动态加载 |
| **Spider** | 并发爬取框架 | 大规模爬取 |
| **Selector** | CSS/XPath/文本解析 | 数据提取 |
| **MCP Server** | AI 辅助爬取 | 智能数据提取 |

---

## 三、Fetcher 详解

### 3.1 三种 Fetcher 对比

| Fetcher | 速度 | 反反爬 | JS 支持 | 适用场景 |
|---------|------|--------|--------|----------|
| **Fetcher** | ⚡⚡⚡ | ❌ | ❌ | 静态页面，高速请求 |
| **StealthyFetcher** | ⚡⚡ | ✅ Cloudflare | ❌ | 反爬网站，无需 JS |
| **DynamicFetcher** | ⚡ | ✅ | ✅ | SPA，动态内容 |

### 3.2 HTTP 请求（Fetcher）

```python
from scrapling.fetchers import Fetcher, FetcherSession

# 单次请求
page = Fetcher.get('https://quotes.toscrape.com/')
quotes = page.css('.quote .text::text').getall()

# 会话请求（保持 Cookie）
with FetcherSession(impersonate='chrome') as session:
    page = session.get('https://example.com/')
    data = page.css('.item::text').getall()
```

**特性：**
- TLS 指纹伪装（自动模拟浏览器）
- HTTP/3 支持
- 自动重试
- 请求延迟控制

### 3.3 反反爬（StealthyFetcher）

```python
from scrapling.fetchers import StealthyFetcher, StealthySession

# 单次请求（自动打开浏览器，完成后关闭）
page = StealthyFetcher.fetch(
    'https://nopecha.com/demo/cloudflare',
    solve_cloudflare=True
)
data = page.css('#padded_content a').getall()

# 会话请求（保持浏览器会话）
with StealthySession(headless=True) as session:
    page = session.fetch('https://example.com/')
    data = page.css('.content').getall()
```

**支持的防护：**
- Cloudflare Turnstile
- Cloudflare Interstitial
- 其他常见反爬机制

### 3.4 浏览器自动化（DynamicFetcher）

```python
from scrapling.fetchers import DynamicFetcher, DynamicSession

# 单次请求
page = DynamicFetcher.fetch(
    'https://quotes.toscrape.com/',
    headless=True,
    network_idle=True
)
data = page.css('.quote .text::text').getall()

# 会话请求
with DynamicSession(headless=True, disable_resources=False) as session:
    page = session.fetch('https://example.com/')
    # 使用 XPath 或 CSS 选择器
    data = page.xpath('//span[@class="text"]/text()').getall()
```

---

## 四、Spider 框架

### 4.1 基础 Spider

```python
from scrapling.spiders import Spider, Response

class QuotesSpider(Spider):
    name = "quotes"
    start_urls = ["https://quotes.toscrape.com/"]
    concurrent_requests = 10  # 并发数

    async def parse(self, response: Response):
        for quote in response.css('.quote'):
            yield {
                "text": quote.css('.text::text').get(),
                "author": quote.css('.author::text').get(),
            }

        # 跟进分页
        next_page = response.css('.next a')
        if next_page:
            yield response.follow(next_page[0])

# 启动爬虫
result = QuotesSpider().start()
print(f"Scraped {len(result.items)} quotes")
result.items.to_json("quotes.json")
```

### 4.2 多会话 Spider

```python
from scrapling.spiders import Spider, Request, Response
from scrapling.fetchers import FetcherSession, AsyncStealthySession

class MultiSessionSpider(Spider):
    name = "multi"
    start_urls = ["https://example.com/"]

    def configure_sessions(self, manager):
        # 添加不同类型的会话
        manager.add("fast", FetcherSession(impersonate="chrome"))
        manager.add("stealth", AsyncStealthySession(headless=True), lazy=True)

    async def parse(self, response: Response):
        for link in response.css('a::attr(href)').getall():
            if "protected" in link:
                # 受保护页面使用 stealth 会话
                yield Request(link, sid="stealth")
            else:
                # 快速页面使用 fast 会话
                yield Request(link, sid="fast", callback=self.parse)
```

### 4.3 暂停/恢复

```python
# 启动爬虫（带检查点）
result = QuotesSpider(crawldir="./crawl_data").start()

# 按 Ctrl+C 优雅停止 - 进度自动保存
# 之后重新运行时：
result = QuotesSpider(crawldir="./crawl_data").start()  # 自动从上次位置恢复
```

### 4.4 流式输出

```python
class StreamingSpider(Spider):
    name = "streaming"
    start_urls = ["https://example.com/"]

    async def parse(self, response: Response):
        for item in response.css('.item'):
            yield {"title": item.css('h2::text').get()}

# 流式处理（实时获取结果）
async for item in StreamingSpider().stream():
    print(item)  # 实时输出
    # 适合：UI 展示、数据管道、长时间爬取
```

---

## 五、解析引擎

### 5.1 选择器类型

```python
from scrapling.fetchers import Fetcher

page = Fetcher.get('https://quotes.toscrape.com/')

# CSS 选择器
quotes = page.css('.quote')

# XPath 选择器
quotes = page.xpath('//div[@class="quote"]')

# BeautifulSoup 风格
quotes = page.find_all('div', {'class': 'quote'})

# 文本搜索
quotes = page.find_by_text('quote', tag='div')
```

### 5.2 链式选择

```python
# 链式选择
first_quote = page.css('.quote')[0]
author = first_quote.css('.author::text').get()

# 元素关系导航
parent = first_quote.parent
siblings = first_quote.sibling_elements()
children = first_quote.css('.text')
```

### 5.3 自适应元素追踪

```python
# 保存元素（网站改版后自动重新定位）
page = StealthyFetcher.fetch('https://example.com/')
products = page.css('.product', auto_save=True)

# 后续使用（网站结构可能已变化）
# Scrapling 会自动尝试找到新位置的元素
products = page.css('.product', adaptive=True)
```

### 5.4 相似元素查找

```python
first_item = page.css('.product')[0]

# 查找相似元素
similar_items = first_item.find_similar()

# 查找下方元素
below_items = first_item.below_elements()
```

---

## 六、代理轮换

### 6.1 基础代理

```python
from scrapling.fetchers import Fetcher, ProxyRotator

# 单次请求使用代理
page = Fetcher.get(
    'https://example.com/',
    proxies=["http://proxy1:port", "http://proxy2:port"]
)

# 使用代理轮换器
rotator = ProxyRotator(["proxy1", "proxy2", "proxy3"])
page = Fetcher.get('https://example.com/', proxy=rotator)
```

### 6.2 高级配置

```python
from scrapling.fetchers import FetcherSession

# 按域名设置不同代理
session = FetcherSession(
    proxy={"example.com": "proxy1", "api.example.com": "proxy2"}
)

# 轮换策略
rotator = ProxyRotator(
    proxies=["p1", "p2", "p3"],
    strategy="cyclic"  # 或 "random"
)
```

---

## 七、AI 集成（MCP Server）

### 7.1 MCP Server 概述

Scrapling 内置 **MCP Server**，让 AI（Claude、Cursor 等）能够直接进行网页数据提取：

**优势：**
- 🤖 AI 理解网页结构
- ⚡ 减少 Token 消耗（只传递提取的数据）
- 🎯 精准定位目标内容

### 7.2 安装 MCP

```bash
pip install "scrapling[ai]"
```

### 7.3 使用示例

```python
# 在 Claude Code / Cursor 中使用
# AI 理解自然语言指令，自动调用 Scrapling 提取数据
```

---

## 八、安装与部署

### 8.1 pip 安装

```bash
# 仅解析器（无请求功能）
pip install scrapling

# 含请求功能
pip install "scrapling[fetchers]"

# 安装浏览器
scrapling install        # 正常安装
scrapling install --force  # 强制重装
```

### 8.2 Docker

```bash
# 从 DockerHub 拉取
docker pull pyd4vinci/scrapling

# 或从 GitHub Registry
docker pull ghcr.io/d4vinci/scrapling:latest
```

### 8.3 开发模式

```python
# 缓存第一次请求，后续复用（不重新请求目标服务器）
class DevSpider(Spider):
    name = "dev"
    start_urls = ["https://example.com/"]

    def configure_sessions(self, manager):
        manager.dev_mode = True  # 启用开发模式
```

---

## 九、性能基准

### 9.1 文本提取速度（5000 嵌套元素）

| 排名 | 库 | 时间(ms) | vs Scrapling |
|------|-----|----------|--------------|
| 1 | **Scrapling** | 2.02 | 1.0x |
| 2 | Parsel/Scrapy | 2.04 | 1.01x |
| 3 | Raw Lxml | 2.54 | 1.26x |
| 4 | PyQuery | 24.17 | ~12x |
| 5 | Selectolax | 82.63 | ~41x |
| 6 | MechanicalSoup | 1549.71 | ~767x |
| 7 | BS4 with Lxml | 1584.31 | ~784x |

### 9.2 元素相似性搜索

| 库 | 时间(ms) | vs Scrapling |
|-----|----------|--------------|
| **Scrapling** | 2.39 | 1.0x |
| AutoScraper | 12.45 | 5.2x |

---

## 十、最佳实践

### 10.1 选择合适的 Fetcher

```
静态页面，无反爬
└─→ Fetcher（最快）

有反爬（Cloudflare 等），无需 JS
└─→ StealthyFetcher

SPA/动态内容，需要 JS 渲染
└─→ DynamicFetcher
```

### 10.2 遵守 robots.txt

```python
class PoliteSpider(Spider):
    name = "polite"
    robots_txt_obey = True  # 遵守 robots.txt
    crawl_delay = 1  # 爬取间隔（秒）
```

### 10.3 检查点保存

```python
# 重要爬取任务使用检查点
class ImportantSpider(Spider):
    name = "important"
    concurrent_requests = 5  # 降低并发
    crawldir = "./checkpoints/"  # 检查点目录

# 按 Ctrl+C 保存进度
# 之后恢复继续
```

---

## 十一、CLI 与 Shell

### 11.1 命令行提取

```bash
# 提取为 Markdown
scrapling extract get 'https://example.com' content.md

# 指定 CSS 选择器
scrapling extract get 'https://example.com' content.txt \
    --css-selector '#main-content'

# 使用隐身模式
scrapling extract stealthy-fetch 'https://nopecha.com/demo/cloudflare' \
    captchas.html --css-selector '#padded_content a' \
    --solve-cloudflare
```

### 11.2 交互式 Shell

```bash
# 启动交互式爬虫 Shell
scrapling shell
```

---

## 十二、总结

Scrapling 是**现代网页爬虫的终极解决方案**：

| 维度 | 传统爬虫 | Scrapling |
|------|----------|-----------|
| 反反爬 | 手动绕过 | 开箱即用 |
| 网站改版 | 手动修复 | 自适应追踪 |
| 性能 | 慢 | 2ms（比 BS4 快 784 倍）|
| 规模 | 单线程 | 并发+暂停恢复 |
| AI 集成 | 无 | MCP Server |

无论你是数据工程师、AI 开发者还是安全研究员，Scrapling 都能让你**高效、稳定、合法**地获取网页数据。

---

**🚀 立即开始：**

```bash
pip install "scrapling[fetchers]"
scrapling install
```

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/D4Vinci/Scrapling |
| 文档 | https://scrapling.readthedocs.io |
| Discord | https://discord.gg/EMgGbDceNQ |
| MCP | https://clawhub.ai/D4Vinci/scrapling-official |

---

_🦞 本文由钳岳星君撰写，基于 Scrapling v0.4.5_
