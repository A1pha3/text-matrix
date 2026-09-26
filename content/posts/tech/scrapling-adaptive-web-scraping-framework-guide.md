---
title: "Scrapling：现代网页爬虫框架·自适应·反反爬"
date: "2026-04-12T02:31:39+08:00"
lastmod: "2026-09-26"
slug: scrapling-adaptive-web-scraping-framework-guide
github_repo: "D4Vinci/Scrapling"
source_key: "gh:D4Vinci/Scrapling"
aliases:
    - /posts/tech/scrapling-adaptive-web-scraping-framework/
description: "Scrapling 是一个现代网页爬虫框架，具有自适应解析、反反爬绕过、并发爬取等功能，文本提取速度约为 MechanicalSoup 的 776 倍。"
draft: false
categories: ["技术笔记"]
tags: ["爬虫", "Python"]
---

# Scrapling：现代网页爬虫框架——自适应、反反爬、并发爬取

大多数爬虫脚本的寿命都不长：页面一改版，选择器失效；反爬一升级，请求被拦。Scrapling（D4Vinci 开发）把这两类维护成本做进了框架本身——解析器会记住元素特征，页面变化后自动重新定位；抓取层开箱即用地处理 Cloudflare Turnstile 一类的人机验证；需要上规模时，再切换到自带并发、检查点和流式输出的 Spider 框架。一个库覆盖从单次请求到全量爬取。

## 一、项目概述

### 1.1 Scrapling 是什么

**Scrapling** 是一个**自适应网页爬虫框架**，能够处理从单次请求到大规模爬取的各类场景。四条主线：

- **自适应解析**：网站结构变化时自动重新定位元素
- **反反爬绕过**：开箱即用绕过 Cloudflare Turnstile/Interstitial
- **Spider 框架**：Scrapy 风格，支持并发、多会话、暂停/恢复与流式输出
- **AI 集成**：内置 MCP Server 与 Agent Skill，AI 可以直接驱动网页数据提取

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | 83,729 ⭐ |
| Forks | 8,557 |
| 最新版本 | v0.4.15（2026-08-23） |
| 许可证 | BSD-3-Clause |
| 语言 | Python 99.9% |
| 贡献者 | 31 |

> 本文以 **v0.4.15** 为口径，GitHub 数据读数于 2026-09-26。

### 1.3 为什么选择 Scrapling

| 特点 | 说明 |
|------|------|
| 🤖 自适应解析 | 网站改版后自动重新定位元素 |
| 🛡️ 反反爬 | 绕过 Cloudflare Turnstile/Interstitial |
| ⚡ 性能 | 文本提取 1.99ms（约为 MechanicalSoup 的 776 倍）|
| 🕷️ Spider 框架 | Scrapy 风格，支持并发、暂停/恢复、自动限速 |
| 🔌 AI 集成 | MCP Server（13 个工具）+ Agent Skill + RAG 就绪 Markdown |
| 🐳 Docker 支持 | 每个版本自动构建含全部浏览器的镜像 |

---

## 二、技术架构

### 2.1 整体架构

```mermaid
graph TB
    subgraph ORCH["编排层"]
        SP["Spider 框架<br/>并发 / 多会话 / 检查点 / 流式"]
        MCP["MCP Server<br/>AI 直接调用"]
        CLI["CLI / Shell / Agent Skill"]
    end
    subgraph FETCH["抓取层"]
        F["Fetcher<br/>HTTP + TLS 指纹伪装"]
        SF["StealthyFetcher<br/>隐身浏览器，反反爬"]
        DF["DynamicFetcher<br/>浏览器自动化"]
    end
    subgraph PARSE["解析层"]
        P["Selector（lxml 内核）<br/>CSS / XPath / 文本查找"]
        AD["自适应元素追踪<br/>auto_save / adaptive"]
    end
    SP --> FETCH
    MCP --> FETCH
    CLI --> FETCH
    F --> P
    SF --> P
    DF --> P
    P --> AD
```

三层各管一件事：**抓取层**负责把页面拿回来（三种 Fetcher 对应不同的对抗强度），**解析层**负责从页面里定位数据（并在页面变化后重新定位），**编排层**负责规模与入口（Spider 管并发爬取，MCP/CLI 管人和 AI 的调用方式）。

### 2.2 核心组件

| 组件 | 功能 | 适用场景 |
|------|------|----------|
| **Fetcher** | HTTP 请求，TLS 指纹伪装 | 静态页面 |
| **StealthyFetcher** | 隐身浏览器，Cloudflare 绕过 | 反爬网站 |
| **DynamicFetcher** | 浏览器自动化，JS 渲染 | SPA/动态加载 |
| **Spider** | 并发爬取框架 | 大规模爬取 |
| **Selector** | CSS/XPath/文本解析 | 数据提取 |
| **MCP Server** | 13 个工具供 AI 调用 | 智能数据提取 |

### 2.3 一次典型爬取的任务流

一个上了 Cloudflare 的目标站点，任务通常会这样流过系统：

1. 先用 `Fetcher.get()` 发普通请求——带浏览器 TLS 指纹，静态内容一步到位；
2. 请求被拦截页顶回来，换 `StealthyFetcher.fetch(..., solve_cloudflare=True)`，隐身浏览器自动通过人机验证后返回页面；
3. 目标数据靠 JS 渲染，再换 `DynamicFetcher` 等网络空闲后提取，或者用 `capture_xhr` 直接收页面发出的 XHR/fetch 响应，省去逆向接口；
4. 页面结构稳定后给关键选择器开 `auto_save=True`，将来站点改版，`adaptive=True` 会按保存的元素特征自动重定位；
5. 单页逻辑跑通后迁到 Spider：`concurrent_requests` 控并发、按 `sid` 把受保护页路由给隐身会话、`crawldir` 落检查点，Ctrl+C 随时暂停；
6. 结果用 `result.items.to_json()` 导出；或者干脆不写代码，把 `scrapling-mcp` 注册给 Claude，让 AI 会话里直接完成提取。

---

## 三、Fetcher 详解

### 3.1 三种 Fetcher 对比

| Fetcher | 速度 | 反反爬 | JS 支持 | 适用场景 |
|---------|------|--------|--------|----------|
| **Fetcher** | ⚡⚡⚡ | ❌ | ❌ | 静态页面，高速请求 |
| **StealthyFetcher** | ⚡⚡ | ✅ Cloudflare | ❌ | 反爬网站，无需 JS |
| **DynamicFetcher** | ⚡ | ✅ | ✅ | SPA，动态内容 |

三者都有对应的 Session 类（`FetcherSession`/`StealthySession`/`DynamicSession` 及各自的 Async 版本），跨请求保持 Cookie 与浏览器状态。

### 3.2 HTTP 请求（Fetcher）

```python
from scrapling.fetchers import Fetcher, FetcherSession

# 单次请求
page = Fetcher.get('https://quotes.toscrape.com/')
quotes = page.css('.quote .text::text').getall()

# 会话请求（保持 Cookie）
with FetcherSession(impersonate='chrome') as session:
    page = session.get('https://quotes.toscrape.com/', stealthy_headers=True)
    data = page.css('.quote .text::text').getall()
```

**特性：**
- TLS 指纹伪装：`impersonate` 默认自动选最新 Chrome 版本
- HTTP/3 支持（`http3=True`，与 `impersonate` 同用时可能有问题）
- 自动重试：默认 3 次（`retries`），间隔 1 秒（`retry_delay`）
- `stealthy_headers` 默认开启，自动生成真实浏览器请求头
- 重定向默认走 "safe" 模式，拒绝跳往内网/私有地址

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
with StealthySession(headless=True, solve_cloudflare=True) as session:
    page = session.fetch('https://nopecha.com/demo/cloudflare', google_search=False)
    data = page.css('#padded_content a').getall()
```

**支持的防护：**
- Cloudflare Turnstile
- Cloudflare Interstitial
- 其他常见反爬机制（配合指纹伪装）

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
with DynamicSession(headless=True, disable_resources=False, network_idle=True) as session:
    page = session.fetch('https://quotes.toscrape.com/', load_dom=False)
    # XPath 或 CSS 选择器都可以
    data = page.xpath('//span[@class="text"]/text()').getall()
```

v0.4.15 之后，浏览器会话的标签页在请求完成后保持打开并可复用：下一次请求直接取一个空闲标签，不再冷启动浏览器；出错或卡死的标签会被关闭替换，`close_pages()` 可以一键清空。

---

## 四、Spider 框架

### 4.1 基础 Spider

```python
from scrapling.spiders import Spider, Response

class QuotesSpider(Spider):
    name = "quotes"
    start_urls = ["https://quotes.toscrape.com/"]
    concurrent_requests = 10  # 并发数（默认 4）

    async def parse(self, response: Response):
        for quote in response.css('.quote'):
            yield {
                "text": quote.css('.text::text').get(),
                "author": quote.css('.author::text').get(),
            }

        # 跟进分页：follow 接收 URL 字符串
        next_page = response.css('.next a')
        if next_page:
            yield response.follow(next_page[0].attrib['href'])

# 启动爬虫
result = QuotesSpider().start()
print(f"Scraped {len(result.items)} quotes")
result.items.to_json("quotes.json")
```

结果导出除了 `to_json()`，还有 `to_jsonl()`、`to_csv()`、`to_xml()`，或者接自己的 pipeline。

### 4.2 多会话 Spider

一个 Spider 里可以混用多种会话类型，按 `sid` 把不同请求路由到不同通道：

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
                # 受保护页面走 stealth 会话
                yield Request(link, sid="stealth")
            else:
                # 快速页面走 fast 会话
                yield Request(link, sid="fast", callback=self.parse)
```

### 4.3 暂停/恢复

```python
# 带 crawldir 启动，启用检查点
result = QuotesSpider(crawldir="./crawl_data").start()

# 按 Ctrl+C 优雅停止 - 进度自动保存
# 之后传同一个 crawldir 重新运行，自动从上次位置恢复
result = QuotesSpider(crawldir="./crawl_data").start()
```

检查点默认每 300 秒周期性保存一次（`interval` 参数可调）。

### 4.4 流式输出

```python
class StreamingSpider(Spider):
    name = "streaming"
    start_urls = ["https://example.com/"]

    async def parse(self, response: Response):
        for item in response.css('.item'):
            yield {"title": item.css('h2::text').get()}

# 流式处理（边爬边拿结果，附带实时统计）
async for item in StreamingSpider().stream():
    print(item)
    # 适合：UI 展示、数据管道、长时间爬取
```

### 4.5 内置模板：不写爬取逻辑

常规场景可以直接继承现成模板，跳过样板代码：

| 模板 | 用途 |
|------|------|
| `CrawlSpider` | 规则驱动的链接跟进 |
| `SitemapSpider` | 按 sitemap/robots.txt 驱动爬取 |
| `XMLFeedSpider` / `CSVFeedSpider` | 迭代 XML/RSS 与 CSV 数据源 |
| `ShopifySpider` | 通过 JSON API 抓取任意 Shopify 店铺全量商品（每变体一条） |
| `SiteToMarkdownSpider` | 整站爬成 Markdown 语料（v0.4.15 新增，见第七节） |

配套的 `LinkExtractor` 是独立的链接提取原语，支持 allow/deny 模式、域名过滤、CSS/XPath 限定范围和扩展名过滤，模板内外都能用。

### 4.6 自动限速（AutoThrottle）

Spider 能按每个域名的响应速度自动调节请求延迟：站点开始封锁或限流时，延迟加倍（或按响应的 `Retry-After` 等待），风头过后再恢复速度。被拦截的请求会被自动识别并按可定制逻辑重试（`max_blocked_retries`，默认 3 次）。

```python
class GentleSpider(Spider):
    name = "gentle"
    start_urls = ["https://example.com/"]
    autothrottle_enabled = True       # 默认关闭
    autothrottle_start_delay = 5.0    # 起始延迟（秒）
    autothrottle_max_delay = 60.0     # 延迟上限（秒）
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
quotes = page.find_all('div', class_='quote')

# 文本搜索
quotes = page.find_by_text('quote', tag='div')
```

选择器伪元素与 Scrapy/Parsel 相同（`::text`、`::attr(href)`），从 BeautifulSoup 或 Scrapy 迁移成本很低。不想发请求也可以直接用解析器：

```python
from scrapling.parser import Selector

page = Selector("<html>...</html>")
```

### 5.2 链式选择与导航

```python
# 链式选择
first_quote = page.css('.quote')[0]
author = first_quote.css('.author::text').get()

# 元素关系导航（siblings / children 是属性，不用加括号）
parent = first_quote.parent
siblings = first_quote.siblings
children = first_quote.children
```

### 5.3 自适应元素追踪

```python
# 保存元素特征（网站改版后用于重新定位）
page = StealthyFetcher.fetch('https://example.com/', headless=True)
products = page.css('.product', auto_save=True)

# 后续使用（网站结构可能已变化）
# Scrapling 会按保存的特征，用相似度算法找到元素的新位置
products = page.css('.product', adaptive=True)
```

`auto_save` 把命中元素的路径、属性、文本、兄弟节点等特征存入本地存储；之后同一站点即使类名或层级变了，`adaptive=True` 也能按相似度打分把元素找回来。这正是 Scrapling 名字里"自适应"的由来。

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

Fetcher 层有三个代理入口，形态各不相同：

```python
from scrapling.fetchers import Fetcher, ProxyRotator

# 1. 单个代理：proxy 接收一个 URL 字符串
page = Fetcher.get(
    'https://example.com/',
    proxy="http://username:password@localhost:8030"
)

# 2. 按域名配置：proxies 接收字典
page = Fetcher.get(
    'https://example.com/',
    proxies={"example.com": "http://proxy1:8080"}
)

# 3. 代理轮换：传给 proxy_rotator 参数
rotator = ProxyRotator(["http://p1:8080", "http://p2:8080", "http://p3:8080"])
page = Fetcher.get('https://example.com/', proxy_rotator=rotator)
```

三条规则值得记住：

- `proxy_rotator` 不能与 `proxy` 或 `proxies` 同时使用——要么静态代理，要么轮换，二选一；
- `ProxyRotator` 的成员可以是字符串，也可以是 `{"server": ..., "username": ..., "password": ...}` 形式的字典，空列表会直接抛 `ValueError`；
- 默认策略是顺序循环（cyclic）。`strategy` 参数接收**函数**而不是字符串——传字符串会抛 `TypeError`：

```python
from random import choice
from scrapling.fetchers import ProxyRotator

# 自定义策略：函数签名 (proxies, current_index) -> (proxy, next_index)
def random_rotation(proxies, current_index):
    return choice(proxies), current_index

rotator = ProxyRotator(
    ["http://p1:8080", "http://p2:8080", "http://p3:8080"],
    strategy=random_rotation
)
```

Spider 框架内同样支持代理轮换，且有配套的封锁检测：请求被拦会换代理重试。另外所有基于浏览器的 Fetcher 都支持内建广告拦截（约 3,500 个广告/追踪域名）与按域名阻断请求，配合代理可以显著降低被识别概率。

---

## 七、AI 集成（MCP Server 与 Agent Skill）

### 7.1 MCP Server 概述

Scrapling 内置 **MCP Server**，让 Claude、Cursor 等 AI 客户端直接进行网页数据提取。页面的净化在交给模型之前完成：先用 CSS 选择器收窄范围，再剥离脚本、样式和隐藏的提示词注入内容——AI 读得更少、花费更低，也不会被页面里埋的恶意指令劫持。

**13 个工具分两组：**

| 类别 | 工具 | 说明 |
|------|------|------|
| 一次性（6 个） | `make_request` | 任意 HTTP 方法，浏览器指纹伪装 |
| | `bulk_get` | 异步并发 GET 多个 URL |
| | `fetch` / `bulk_fetch` | Chromium/Chrome 动态抓取（单个/并发） |
| | `stealthy_fetch` / `bulk_stealthy_fetch` | 隐身模式绕 Cloudflare（单个/并发） |
| 会话（7 个） | `open_session` / `close_session` / `list_sessions` | 管理持久浏览器会话 |
| | `open_request_session` | 无浏览器的持久 HTTP 会话 |
| | `session_fetch` / `session_make_request` | 通过已开会话发请求，保持 Cookie 与状态 |
| | `screenshot` | 截图并以图像块返回，模型能直接"看到"页面 |

### 7.2 安装与接入

```bash
pip install "scrapling[ai]"
scrapling install   # 首次使用还需安装浏览器依赖
```

Claude Desktop 在配置文件（`~/Library/Application Support/Claude/claude_desktop_config.json`）中加入：

```json
{
  "mcpServers": {
    "ScraplingServer": {
      "command": "scrapling-mcp"
    }
  }
}
```

Claude Code 一行命令接入：

```bash
# 先定位可执行文件路径
which scrapling-mcp
# 注册到 Claude Code（路径替换为上一步的输出，如 /Users/<用户名>/.venv/bin/scrapling-mcp）
claude mcp add ScraplingServer /Users/<用户名>/.venv/bin/scrapling-mcp
```

`scrapling-mcp` 是 v0.4.13 加入的快捷命令，等价于 `scrapling mcp`。v0.4.15 重构了 MCP Server，**升级前注意破坏性变更**：Streamable HTTP 传输默认绑定 `127.0.0.1` 且强制认证（`--auth-token` 或环境变量 `SCRAPLING_MCP_AUTH_TOKEN`，`--no-auth` 可显式关闭）；一次性工具不再接受 `session_id`，改用 `session_fetch`；原 `get` 工具更名为 `make_request`。对外暴露服务时建议配 `--allowed-host` 开启 DNS 重绑定防护。

### 7.3 Agent Skill 与 RAG 就绪 Markdown

除了 MCP，还有两条给 AI 用的路：

**Agent Skill**：一个教编码 agent 用好 Scrapling 的技能包，让 agent 写出的代码贴合当前版本 API 而不是凭记忆猜。可从 [Clawhub](https://clawhub.ai/D4Vinci/scrapling-official) 安装到 OpenClaw 等支持的 agent 环境。

**RAG 就绪 Markdown**：一行代码把任意页面转成干净、已消毒的 LLM 输入（`pip install "scrapling[rag]"`）：

```python
from scrapling.fetchers import Fetcher

markdown = Fetcher.get("https://example.com").markdown(main_content_only=True)
```

脚本、样式和隐藏的提示词注入内容会先被剥离；传 `css_selector` 可以只转换需要的部分。配合 `SiteToMarkdownSpider` 能把整站爬成 Markdown 语料，全程无需 LLM 参与爬取环节。

---

## 八、安装与部署

要求 Python 3.10 或更高版本。

### 8.1 pip 安装

```bash
# 仅解析器（无请求功能）
pip install scrapling

# 含请求功能（fetchers + spiders + 浏览器控制）
pip install "scrapling[fetchers]"

# 安装浏览器依赖（Playwright Chromium 及系统依赖、指纹组件）
scrapling install        # 正常安装
scrapling install --force  # 强制重装
```

注意：只装 `scrapling` 的话，`import scrapling.fetchers` 或 `scrapling.spiders` 会直接抛 `ModuleNotFoundError`，用哪个 extra 要先想好。可选 extras 一览：

| Extra | 内容 |
|-------|------|
| `fetchers` | 抓取与爬虫功能 |
| `ai` | MCP Server |
| `rag` | Markdown 转换（含在 `ai`/`shell`/`all` 中） |
| `shell` | 交互式 Shell 与 `extract` 命令 |
| `all` | 全部功能 |

也可以在代码里触发浏览器依赖安装：

```python
from scrapling.cli import install

install([], standalone_mode=False)          # 正常安装
install(["--force"], standalone_mode=False) # 强制重装
```

### 8.2 Docker

```bash
# 从 DockerHub 拉取
docker pull pyd4vinci/scrapling

# 或从 GitHub Registry
docker pull ghcr.io/d4vinci/scrapling:latest
```

镜像含全部 extras 与浏览器，随每个 release 由 GitHub Actions 自动构建。

### 8.3 开发模式

```python
# 首次运行把响应缓存到磁盘，之后直接回放，
# 迭代 parse() 逻辑时不再重复请求目标服务器
class DevSpider(Spider):
    name = "dev"
    start_urls = ["https://example.com/"]
    development_mode = True             # 默认 False
    development_cache_dir = "./cache/"  # 可选，自定义缓存目录
```

---

## 九、性能基准

### 9.1 先说清测的是什么

下表测的是**解析器层**的文本提取：对 5000 个嵌套元素执行选择操作，纯 CPU 操作，所有数字为 100+ 次运行的平均值（方法论见仓库 `benchmarks.py`）。它不包含网络请求、浏览器启动和渲染的耗时。

### 9.2 文本提取速度（5000 嵌套元素）

| 排名 | 库 | 时间(ms) | vs Scrapling |
|------|-----|----------|--------------|
| 1 | **Scrapling** | 1.99 | 1.0x |
| 2 | Parsel/Scrapy | 2.06 | 1.035 |
| 3 | Raw Lxml | 2.56 | 1.286 |
| 4 | PyQuery | 23.98 | ~12x |
| 5 | Selectolax | 197.02 | ~99x |
| 6 | MechanicalSoup | 1545.15 | ~776.5x |
| 7 | BS4 with Lxml | 1562.1 | ~785x |
| 8 | BS4 with html5lib | 3412.73 | ~1715x |

怎么读这组数字：

- Scrapling 与 Parsel/Raw Lxml 在同一量级——它们共享 lxml 内核，真正拉开差距的是 BS4、PyQuery 这类在 Python 层做树遍历的库，以及 MechanicalSoup/BS4 的会话封装开销；
- 数字会随各库版本与测试环境变化（例如 Selectolax 在 v0.4.5 时读数为 82.63ms，v0.4.15 口径下为 197.02ms），对比时应以同一次发布的官方表格为准；
- **不能推出的结论**：实际爬取任务的瓶颈几乎总在网络往返与反爬对抗上，解析速度只在单页元素量很大或批量清洗时才成为主要因素。

### 9.3 元素相似性搜索

| 库 | 时间(ms) | vs Scrapling |
|-----|----------|--------------|
| **Scrapling** | 2.3 | 1.0x |
| AutoScraper | 12.58 | 5.47x |

这一项测的是"相似元素定位"——自适应重定位所依赖的能力。AutoScraper 是功能上最接近的替代品，慢约 5 倍，且它没有内建的抓取层。

---

## 十、实践建议

### 10.1 选择合适的 Fetcher

```
静态页面，无反爬
└─→ Fetcher（最快）

有反爬（Cloudflare 等），无需 JS
└─→ StealthyFetcher

SPA/动态内容，需要 JS 渲染
└─→ DynamicFetcher
```

按对抗强度递进，先试便宜的：Fetcher 请求被拦再升级到 StealthyFetcher，需要交互或等渲染再上 DynamicFetcher。

### 10.2 遵守 robots.txt

```python
class PoliteSpider(Spider):
    name = "polite"
    robots_txt_obey = True   # 遵守 Disallow / Crawl-delay / Request-rate
    download_delay = 1       # 每次请求间隔（秒）
```

`robots_txt_obey` 按域名缓存解析结果；配合 `download_delay` 和 AutoThrottle（见 4.6），基本可以做到"对目标站点足够温和"。

### 10.3 检查点保存

```python
# 重要爬取任务：降低并发 + 启用检查点
class ImportantSpider(Spider):
    name = "important"
    concurrent_requests = 5  # 降低并发（默认 4，按目标站点承受力调）

# crawldir 是构造参数，不是类属性
spider = ImportantSpider(crawldir="./checkpoints/")
result = spider.start()
# 按 Ctrl+C 优雅停止，进度自动保存
# 之后传同一个 crawldir 重新运行，从断点继续
```

---

## 十一、CLI 与 Shell

CLI 的 `extract` 与 `shell` 命令属于 `shell` extra（`pip install "scrapling[shell]"`），只装核心包时这两个子命令不可用。

### 11.1 命令行提取

```bash
# 提取为 Markdown（默认提取 body 内容；.txt 输出纯文本，.html 输出 HTML）
scrapling extract get 'https://example.com' content.md

# 指定 CSS 选择器
scrapling extract get 'https://example.com' content.txt \
    --css-selector '#main-content'

# 使用隐身模式
scrapling extract stealthy-fetch 'https://nopecha.com/demo/cloudflare' \
    captchas.html --css-selector '#padded_content a' \
    --solve-cloudflare
```

`extract` 下有 `get`/`post`/`put`/`delete`（HTTP）与 `fetch`/`stealthy-fetch`（浏览器）两组子命令，支持 `--impersonate`、`--proxy`、`--timeout` 等参数——不写一行 Python 也能完成大部分提取任务。

### 11.2 交互式 Shell

```bash
# 启动交互式爬虫 Shell（IPython 环境，内置 Scrapling 快捷方式）
scrapling shell
```

Shell 里有几个开发提效工具：把 curl 命令转成 Scrapling 请求、在浏览器里查看请求结果、用 `-c` 直接执行一段代码并退出。

---

## 十二、总结与采用建议

| 维度 | 传统爬虫 | Scrapling |
|------|----------|-----------|
| 反反爬 | 手动绕过 | 开箱即用 |
| 网站改版 | 手动修复 | 自适应追踪 |
| 解析性能 | BS4 量级 | 1.99ms（约 785 倍于 BS4+Lxml）|
| 规模 | 单线程 | 并发+检查点+自动限速 |
| AI 集成 | 无 | MCP Server（13 工具）+ Agent Skill + RAG |

**谁适合现在就用：**

- 爬取目标长期运行的团队——自适应追踪直接削减"站点改版后修选择器"的维护成本；
- 目标站点有 Cloudflare 类防护、又不想维护一套指纹对抗代码的开发者；
- 想给 AI 应用接网页能力的团队——MCP Server 的注入内容剥离在安全设计上想得比较周全。

**可以再等等的场景：**

- 一次性小脚本，`requests` + BeautifulSoup 十行搞定，引入框架不划算；
- 重度存量 Scrapy 项目不必迁移——用 `scrapling_response` 装饰器可以只把解析层换成 Scrapling，已有爬虫结构不动。

**起步路径**：`pip install "scrapling[fetchers]" && scrapling install`，从 `Fetcher.get()` 开始；遇到反爬升级 StealthyFetcher；要上规模再看第四节 Spider；想给 AI 用，直接跳到第七节。

---

**安装：**

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
| Agent Skill | https://clawhub.ai/D4Vinci/scrapling-official |
| MCP 文档 | https://scrapling.readthedocs.io/en/latest/ai/mcp-server.html |

---

### 参考来源与口径说明

- 版本口径：本文技术内容以 **v0.4.15**（2026-08-23 发布）为基准；文章最初发布时基于 v0.4.5（2026-04-07）。v0.4.5 之后仓库共发布 10 个版本，其中 v0.4.13 加入 `scrapling-mcp` 快捷命令，v0.4.15 重构 MCP Server（含破坏性变更）并新增 `Response.markdown()`、`SiteToMarkdownSpider` 与浏览器标签页复用。
- 数据读数：Stars/Forks/贡献者数为 2026-09-26 GitHub API 读数（83,729 / 8,557 / 31）；许可证 BSD-3-Clause；语言占比按仓库语言字节统计 Python 99.9%。
- 事实来源：仓库 README、releases 说明、源码（`scrapling/spiders/spider.py`、`scrapling/engines/static.py`、`scrapling/engines/toolbelt/proxy_rotation.py`、`scrapling/parser.py`、`scrapling/cli.py`、`scrapling/fetchers/__init__.py`）及官方文档 MCP Server 页；代码示例均对照上述源码与官方 README 核对。
- 性能数字：取自 v0.4.15 版 README 基准表（100+ 次运行平均），与 v0.4.5 时的读数存在差异（如 Selectolax 一项），正文已按现行口径标注。

---

_🦞 本文由钳岳星君撰写，基于 Scrapling v0.4.15_
