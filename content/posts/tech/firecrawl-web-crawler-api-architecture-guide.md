---
title: "Firecrawl：把整个 Web 变成 LLM 能直接吃的 Markdown 上下文 API 完全拆解"
date: "2026-07-07T02:59:57+08:00"
slug: "firecrawl-web-crawler-api-architecture-guide"
description: "Firecrawl（146k stars / AGPL-3.0）把网页爬取、JS 渲染、结构化抽取、爬虫调度四件事打包成一个 REST API，专为 LLM 上下文设计：支持 search / scrape / crawl / batch scrape / extract。本文拆解它的接口形态、可靠性边界、与同类工具（jina reader / tavily / playwright）的差异点。"
draft: false
categories: ["技术笔记"]
tags: ["Web Scraping", "LLM Context", "AI Agent", "API", "Firecrawl"]
---

# Firecrawl：Web → Markdown，给 LLM 当上下文

我们已经在 2026 年习惯"让 LLM 读网页"这件事了——但你只要真的让 LLM 去抓一个现代网页（React SPA、需要登录、有反爬、有无限滚动），就会撞上三件事：JS 没渲染就拿到了空壳、HTML 标签噪音淹没 prompt 的有效信息、爬到一半被 Cloudflare 拦下。Firecrawl（146k stars / AGPL-3.0）就是把这三件事兜起来的"web context API"——本文拆它的接口形态和它为什么是 Agent 时代最常被点名的爬虫。

## 它在 API 维度做了四件事

Firecrawl 把"读 web"切成 4 个端点，每个对应一类用户场景：

| 端点 | 用途 | 典型用法 |
|------|------|----------|
| `search` | 搜并返回完整页面内容 | "搜 LLM evaluation 论文给我带全文" |
| `scrape` | 单 URL 转 markdown/HTML/screenshot/JSON | 单页结构化抽取 |
| `crawl` | 全站爬取（一组 URL） | 整个 docs site、整个博客 |
| `batch scrape` | 异步并发数千 URL | 一次性把一堆 URL 拉成 markdown |

外加一个面向 AI Agent 的 `extract`——自然语言描述 schema，Firecrawl 自己用 LLM 从页面里抠字段。

## 为什么是 LLM Context API 而不是 Crawler

普通爬虫（Scrapy、Playwright、Crawlee）给你的是 HTML 字符串或裸 JSON，要你自己 parse 标签、去噪、提取正文。Firecrawl 在中间层替你做了：

1. **JS 渲染**：headless 浏览器跑 React/Vue/SPA，等 hydration 完成再 snapshot。
2. **Markdown 转换**：HTML → Markdown，保留代码块、表格、链接、标题层级，去掉 nav/footer/广告。
3. **结构化抽取**：`extract` 端点接受 JSON Schema 或自然语言描述，从页面里抽出结构化字段（产品价格、规格、作者）。
4. **绕过反爬**：内置 proxy rotation、UA rotation、stealth 模式。官方 benchmark 声称覆盖 96% 的 web（包括 JS-heavy 页面）。
5. **Action 序列**：可以先 click / scroll / write / wait / press 再抽取，处理"翻页后才看到列表"这种交互场景。

输出默认是 markdown（保留可读性 + 适配 LLM prompt 长度限制），也可以指定 HTML、screenshot、JSON。

## 怎么用：4 个最小例子

```python
from firecrawl import Firecrawl

app = Firecrawl(api_key="fc-...")

# 1. Scrape：单 URL → Markdown
result = app.scrape(
    "https://example.com/article",
    formats=["markdown", {"type": "json", "schema": {...}}],
)
print(result.markdown)
print(result.json)

# 2. Search：搜并带全文
results = app.search("LLM evaluation benchmarks 2026", limit=5)

# 3. Crawl：整站爬（异步任务）
job = app.crawl(
    "https://docs.example.com",
    limit=500,
    include_paths=["/guide/*"],
    exclude_paths=["/api/*"],
)
# job.id 用于异步轮询

# 4. Extract：自然语言 schema
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "price": {"type": "number"},
    }
}
extracted = app.extract(
    ["https://shop.example.com/p1", "https://shop.example.com/p2"],
    schema=schema,
)
```

CLI 也有一行入口：

```bash
firecrawl scrape https://example.com --format markdown
firecrawl crawl https://docs.example.com --limit 100
```

## Agent 时代的杀手锏：MCP 一行接入

Firecrawl 的另一个差异化点是 [MCP server](https://docs.firecrawl.dev)——你不用写 Python 绑定，直接让 Claude Code / Cursor / Continue / Cline 等 MCP-aware agent 通过 `mcp.json` 接入：

```json
{
  "mcpServers": {
    "firecrawl": {
      "command": "npx",
      "args": ["-y", "firecrawl-mcp"],
      "env": {"FIRECRAWL_API_KEY": "fc-..."}
    }
  }
}
```

之后 agent 多了三个 tool：`firecrawl_scrape` / `firecrawl_crawl` / `firecrawl_search`。这是 Firecrawl 能在 2025–2026 增长到 146k stars 的核心驱动——它把"agent 联网"做成了 declarative 的"加 mcp server"而不是 imperative 的"写 Python 调用"。

## 与同类工具的边界

读到这里你大概想问：**这跟 jina reader / tavily / playwright 有什么区别？**

| 工具 | 定位 | 强项 | 弱项 |
|------|------|------|------|
| **Firecrawl** | LLM context API | 端到端全栈（爬+渲染+抽+结构化）+ MCP + agent ready | AGPL-3.0（自托管要注意）+ 按 credit 计费 |
| **jina reader** | 单页 reader | 免费层慷慨、输出干净 markdown | 不擅长批量爬、无 extract 端点 |
| **tavily** | 搜索 API | 搜索结果带 LLM 摘要 | 不擅长整站爬 |
| **playwright** | 浏览器自动化 | 完全可控、JS 交互 | 要自己写 parse、要自己处理反爬 |

Firecrawl 的位置是**jina reader 的全栈版**+**playwright 的 agent 版**——你愿意为"开箱即用"付钱就用 Firecrawl，你愿意写代码就 Playwright。

## 自托管的现实

Firecrawl 主仓库是完整的 TypeScript + Playwright + Redis 队列实现，可以 docker-compose 起来。但有几件事要注意：

1. **AGPL-3.0**：你 fork / 修改后必须开源，如果你要做闭源产品必须用 hosted 版本（[firecrawl.dev](https://firecrawl.dev)）。
2. **反爬 IP 池**：自托管版本要自己配 proxy rotation，否则跑几小时就被 Cloudflare 拦。
3. **JS 渲染成本**：headless Chrome 是吃内存大户，单机起 5 个 worker 就吃 ~8GB RAM。
4. **LLM 抽取的 token 成本**：`extract` 端点背后是 LLM 调用，长页面 token 消耗要注意。

对于"我要给内部 agent 做联网功能 + 不在意付费"的场景，hosted 版本是合理选择。对于"我要做 to C 产品 + 想白嫖"——直接用 jina reader + 自己写一层批量调度。

## 适用边界

- **真要快且免费**：jina reader 单页比 Firecrawl 快几倍。
- **真要可控**：Playwright + 自己 parse。
- **真要给 agent 用**：Firecrawl 的 MCP server 是当前最低摩擦的接入方式。
- **真要做闭源产品**：注意 AGPL-3.0，hosted 版本规避风险。
- **真要规模化**：Firecrawl hosted 按 credit 计费，1k credits 起卖，超大规模前自己算 TCO。

## 仓库地址

- 仓库：`firecrawl/firecrawl`
- 主页：https://firecrawl.dev
- 协议：AGPL-3.0（自托管强制开源）
- 主语言：TypeScript（API server）+ Python SDK + Node SDK
- stars：146k / forks 8.4k

如果你只想快速体验，`pip install firecrawl-py` + 拿一个 API key 就能在 5 分钟内跑通第一个 `scrape` 调用——这是它能在 Agent 时代拿下 14 万 stars 的根本原因：摩擦低到接近自然语言查询。