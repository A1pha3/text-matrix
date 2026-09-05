---
title: "Hister：把你看过的一切变成可检索的私有搜索引擎"
date: 2026-09-01T03:45:00+08:00
lastmod: 2026-09-05T00:00:00+08:00
draft: false
slug: "asciimoo-hister-personal-fulltext-search-engine"
github_repo: "asciimoo/hister"
source_key: "gh:asciimoo/hister"
author: "钳岳"
canonical: "https://txtmix.com/posts/tech/asciimoo-hister-personal-fulltext-search-engine/"
categories: ["技术笔记"]
tags: ["Hister", "全文检索", "个人知识库", "MCP", "隐私", "Go"]
description: "Searx 作者 Adam Tauber 的新作 Hister：一个跑在本地的私有全文搜索引擎，索引你访问过的网页和本地文件的全部内容，通过 Web、终端和 MCP 三种方式检索。本文拆解它的检索模型、查询语法、隐私边界与上手路径。"
keywords: ["hister", "asciimoo", "Adam Tauber", "Searx", "全文检索", "个人搜索引擎", "MCP", "浏览器历史索引", "隐私优先", "语义检索"]
---

# Hister：把你看过的一切变成可检索的私有搜索引擎

> 浏览器历史记录只记标题和 URL，等你真正想找"上周读过的那段内容"时，它毫无用处。Hister 的答案很直接：把页面的**正文全文**索引进你自己的搜索引擎。

[Hister](https://github.com/asciimoo/hister) 自称 "Your own search engine"——你自己的搜索引擎。它索引你访问过的网页和本地文件的**完整内容**（而不只是标题和链接），然后让你从 Web 界面、终端 TUI/命令行，或通过 MCP（Model Context Protocol，模型上下文协议）连接的 AI 助手三种方式检索这些内容。

一个值得注意的背景：作者是 Adam Tauber（GitHub ID `asciimoo`）——隐私元搜索引擎 Searx 和 Go 爬虫框架 Colly 的作者（Colly 至今提交量榜首仍是 asciimoo）。一个做了十年"如何更好地搜索"和"如何更好地爬取"的人，转向"如何检索自己看过的东西"，这个谱系本身就说明了项目的定位：它不是又一个书签管理器，而是从搜索基础设施的视角重新设计个人知识的检索层。

截至本文写作时（2026-09-05），仓库约 3.6k Stars、169 Forks，最新版本 v0.19.0（2026-09-03 发布），最近一次提交也在 2026-09-03——维护活跃。语言为 Go，许可证 AGPLv3。官方提供[在线演示](https://demo.hister.org/)和[文档站](https://hister.org/docs)，可以不用部署先体验一遍检索界面。

## 它解决的是什么问题

个人知识的常见困境是这样的：信息看过了，但没存下来；存下来了，但找不到。浏览器历史记录只回答"我什么时候访问过哪个 URL"，回答不了"那篇讲 residual stream 的文章里具体说了什么"——因为历史数据库里只有 URL 和访问信息，根本没有页面内容。

Hister 的处理方式是把"访问"这个动作本身变成索引事件：浏览器扩展（Firefox/Chrome 官方商店均有上架）在你访问页面时，把页面内容发送到你配置的 Hister 服务器，服务器对全文建索引。已有的历史记录则通过 `hister import browser` 读回 URL 列表，再逐个抓取页面补上内容。加上本地文件导入与目录监听，你经手过的信息形成了一个可全文检索的私有语料库。

## 系统地图

Hister 是一个单二进制 Go 服务，整体结构可以这样看：

- **采集层**：浏览器扩展（自动索引新访问页面）、浏览器历史导入、内置爬虫、本地目录监听
- **索引层**：对页面和文件的正文做全文索引，可加语义检索（embeddings，向量嵌入），指向你自行配置的端点
- **查询层**：Web UI、终端 TUI、命令行客户端、MCP 服务端

### 一次查询如何穿过系统

以 `domain:github.com title:encryption -tutorial` 为例，追踪这条查询的完整路径：

1. 你在 Web / TUI / 命令行 / MCP 任一入口输入查询，字符串交给查询层
2. 查询层把语法拆成结构化条件：域名限定 github.com、标题含 encryption、排除标题含 tutorial 的文档
3. 索引层按这些条件召回候选文档，按相关性打分排序
4. 结果回到界面，每条附标题、URL、更新时间与正文摘要片段

对 AI 工作流的用户来说，MCP 接口是关键卖点：AI 助手可以通过 MCP 直接查询你的个人索引。这意味着"问 AI 我上周看过什么"这类需求有了落地路径——AI 检索的是你真实读过的全文内容，而不是它的训练记忆。

## 查询语言：一个正经搜索引擎的语法

Hister 的查询不是子串匹配，而是带字段、短语、通配与逻辑组合的检索语法，全部大小写不敏感：

```text
# 字段过滤：限定标题、域名、URL、文档类型
title:encryption
domain:github.com
url:*/security/*
type:file

# 精确短语
"end-to-end encryption"

# 通配符
secur*

# 否定
privacy -facebook
title:hister -url:*/issues/*

# 或
(security|privacy|encryption)

# 排序
golang sort:date
```

组合起来可以写出相当精准的查询，比如"GitHub 上标题涉及安全、排除旧教程的页面"：

```text
domain:github.com title:(security|vulnerability) -tutorial
```

字段还覆盖 `added:` / `updated:`（按时间过滤，支持 `>90d` 这类相对时间）、`visits:`（按访问次数）、`language:`（按检测语言）。完整字段清单见[查询语言文档](https://hister.org/docs/query-language)。

## 隐私边界：说清楚什么留在本地、什么会出去

隐私项目必须把数据流向讲透，Hister 的默认行为如下：

- **默认无遥测、无云同步**。数据（文档 + 索引）存储在你运行 Hister 的那台服务器上。
- 浏览器扩展只把索引的页面内容发给你配置的 Hister 服务器，唯一的例外是下载页面 favicon。扩展不会对你正在访问的站点发出任何请求，对索引的网站完全透明。
- **语义检索是显式的可选项**：开启后文档文本会发送到你配置的 embeddings 端点。如果你把端点指向第三方 API，等于把文档内容交了出去——官方文档明确提醒启用前审查隐私配置。

所以，"本地部署 + 不开语义检索"是一个完全闭环的形态：语义检索带来的能力提升以部分数据外流为代价，边界由你自己画。

## 上手：五分钟路径

个人本地部署不需要任何配置：

```bash
# 1. 从 release 下载对应平台的二进制，重命名为 hister
chmod +x hister
./hister listen
```

打开 `http://127.0.0.1:4433`，安装浏览器扩展（Firefox / Chrome 商店搜索 Hister），完成。此后你访问的页面会被自动全文索引。

已有的浏览器历史可以一次性导入：

```bash
# 自动检测本机常见浏览器的历史数据库
hister import browser
```

进阶用法包括多用户模式（共享服务器上每个用户的文档与检索结果相互隔离）、爬虫索引指定站点、配置语义检索端点。v0.19.0 还加入了 Safari 历史导入（macOS 需授予完全磁盘访问权限）与 `url_re:` 正则检索。

## 用 AI 检索你的阅读历史：MCP 接口

Hister 原生暴露 MCP 端点 `POST /mcp`，AI 助手连上后可以检索你的索引、读取页面快照。以 Claude Desktop 为例，往配置文件加一段即可：

```json
{
  "mcpServers": {
    "hister": {
      "url": "http://127.0.0.1:4433/mcp",
      "headers": {
        "Authorization": "Bearer <your-access-token>"
      }
    }
  }
}
```

默认本地部署不要求认证，`Authorization` 头只有在服务器配置了访问令牌时才需要。端点提供三个工具：`search`（按查询语言检索，可带日期范围与语义开关）、`get_preview`（按 URL 取回存储的页面快照）、`get_history`（查看最近索引或打开过的页面）。

一个需要注意的细节：索引里的标题、正文、元数据都来自你浏览过的网页，属于**不可信数据**。Hister 在 MCP 工具响应里把这些字段标为 `trust: "untrusted"`，并要求客户端渲染 HTML 前先消毒，防止网页里的提示注入影响 AI 助手。接 MCP 之前，先想清楚你的 AI 助手会不会被检索到的页面内容带偏。

## 适用边界

Hister 适合的场景：你大量阅读网页和本地文档，且经常需要"按内容回溯"；你在意隐私，希望检索基础设施自己掌控；你用 AI 助手并希望它能检索你的真实阅读历史。

它不适合的：它不是通用搜索引擎的替代品——只索引"你经手过的内容"；也不打算做知识管理（笔记、标注、双向链接都不在它的关注点上）。检索，只做检索。

如果按优先级排，最该先试的是"浏览器扩展 + Web 界面"这条链路：装一个扩展、跑一次服务器，十分钟内就能判断它对你是否顺手。决定长期使用前，值得先想清楚两件事：一是你是否需要语义检索（以及愿意为它把内容交给哪个 embeddings 端点），二是你的阅读量是否大到值得为它起一个常驻进程。

## 结语

Searx 解决的是"如何不被人窥探地搜索公开互联网"，Hister 解决的是"如何检索自己的私有语料"。从这两个项目的谱系看，作者对"搜索"这件事的理解是一致的：检索能力是基础设施，基础设施应该掌握在使用者手里。对任何被"看过但找不回"困扰的人，Hister 值得一次五分钟的试用。
