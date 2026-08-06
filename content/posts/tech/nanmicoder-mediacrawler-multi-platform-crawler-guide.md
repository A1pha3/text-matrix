---
title: "MediaCrawler：不做 JS 逆向，靠浏览器登录态取签名的多平台爬虫"
date: "2026-06-26T18:02:04+08:00"
slug: "nanmicoder-mediacrawler-multi-platform-crawler-guide"
github_repo: "NanmiCoder/MediaCrawler"
description: "梳理 GitHub 上 5.9 万 Star 的 MediaCrawler：用 Playwright 接管已登录浏览器、以 JS 表达式现取签名的思路，覆盖小红书/抖音/B 站/微博等 7 个平台，并说明 CDP 模式的适用范围与边界。"
draft: false
categories: ["技术笔记"]
tags: ["Python", "Playwright", "爬虫", "CDP", "开源工具"]
---

# MediaCrawler：不做 JS 逆向，靠浏览器登录态取签名的多平台爬虫

## 一、这个项目解决了什么

MediaCrawler 是作者 NanmiCoder 维护的开源项目，用 Playwright 浏览器自动化抓取国内自媒体平台的公开数据，覆盖小红书、抖音、快手、B 站、微博、百度贴吧、知乎七个平台。截至 2026 年 8 月 6 日（GitHub API），Star 约 5.96 万，Fork 约 1.17 万，主语言 Python。License 是作者自定义的 `NON-COMMERCIAL LEARNING LICENSE 1.1`，明确禁止商业用途，和常规 OSI 开源协议不兼容。

它真正的取舍在于：多数爬虫靠 JS 逆向还原加密算法，它反着来——让浏览器自己完成登录和签名，Python 端只负责调度和落盘。门槛因此从"能逆向的人"降到"会用浏览器的人"。CDP（Chrome DevTools Protocol，Chrome 开发者工具协议）只是其中小红书和抖音两个平台的接入方式，不是全部手段，这点下面会拆开讲。

## 二、系统地图：七个平台共用一套接口

MediaCrawler 把"爬什么"和"怎么爬"分开。七个平台共享同一套命令行参数（`--platform` 选平台、`--lt` 选登录、`--type` 选爬取类型），底层签名逻辑各自实现。下表是 README 的能力矩阵：

| 平台 | 关键词搜索 | 指定帖子 ID | 二级评论 | 指定创作者主页 | 登录态缓存 | IP 代理池 | 评论词云 |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 小红书 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 抖音 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 快手 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| B 站 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 微博 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 百度贴吧 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 知乎 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

平台能力对齐，换平台不用重写业务逻辑，只改 `--platform`。

## 三、技术路线：浏览器登录态 + JS 取签名

### 3.1 传统两条路的问题

国内自媒体接口普遍有双重防护：登录态校验 + 参数签名（signature，对请求参数做的加密摘要，常见算法有 MD5、SHA1、HMAC 等）。绕过方式通常两条：

1. **JS 逆向**：用 AST 解析、Hook 还原加密算法，再纯 Python 重写。维护成本高，平台一改版本就失效。
2. **协议模拟**：用 requests/httpx 直接拼签名请求，失败率高，容易被风控。

### 3.2 MediaCrawler 的第三条路

它接管用户已经登录好的浏览器，在真实浏览器上下文里执行爬取：

- **登录态复用**：第一次扫码登录后，登录态序列化到本地缓存，之后直接复用，不用每次重扫。
- **签名现取**：在浏览器里执行 JS 表达式直接拿到 X-s、X-s-common 等签名参数，Python 端不做任何加密还原。
- **CDP 接入**：对小红书（`xhs`）和抖音（`dy`）两个平台，可以开远程调试后让 Playwright 用 `connect_over_cdp` 接现有浏览器。README 明确 CDP 目前只开放这两个平台；其余平台走标准 Playwright 模式（需要 `playwright install` 下载浏览器驱动）。

这样平台升级签名算法时，只要浏览器端还能跑，Python 端就不用动。对个人来说，成本从"逆向工程师改代码"变成"重启一次浏览器"。

### 3.3 代价

- **要留着浏览器**：爬取期间浏览器进程不能被关掉，否则登录态和签名来源就断了。
- **依赖真实登录态**：单账号高频访问仍会被风控，需要配合 IP 代理池；这是所有登录态方案的共性，MediaCrawler 解决不了。
- **不可商用**：License 禁止商业用途，免责声明也写明只供学习研究。

## 四、快速上手

下面以小红书关键词搜索为例，串起一次完整任务。

### 4.1 前置准备

- **uv**：项目推荐用它管理 Python 环境和依赖，装完用 `uv --version` 验证。
- **Node.js**：>= 16。爬抖音和知乎需要，这两个平台的签名依赖 Node.js 里的 JS 模块。
- **浏览器**：用 CDP 模式时，需要一个较新的 Chrome/Edge，并开启远程调试（`chrome://inspect/#remote-debugging` 勾选 Allow remote debugging，或用命令行参数 `--remote-debugging-port=9222` 启动）。

### 4.2 安装与运行

```bash
git clone https://github.com/NanmiCoder/MediaCrawler.git
cd MediaCrawler

uv sync

uv run main.py --platform xhs --lt qrcode --type search
```

首次扫码登录，之后复用登录态缓存，不用再扫。

### 4.3 关键配置

集中在 `config/base_config.py`：

- `ENABLE_CDP_MODE`：是否用 CDP 模式，默认 `True`。`CDP_CONNECT_EXISTING` 控制是连接已开远程调试的浏览器还是启动新实例。
- `ENABLE_GET_COMMENTS`：是否爬评论，默认 `True`。
- 关键词、创作者 ID、爬取页数、`CRAWLER_MAX_NOTES_COUNT` 等都在这个文件里，带中文注释。

### 4.4 WebUI

不习惯命令行的可以用 WebUI：

```bash
uv run uvicorn api.main:app --port 8080 --reload
# 打开 http://localhost:8080
```

界面里可以选平台、登录方式、爬取类型，实时看日志和数据。

## 五、数据存储

支持多种落盘方式，用 `--save_data_option` 指定，默认 JSONL：

- **文件**：CSV、JSON、JSONL（默认，每行一条、追加写性能好）、Excel（多工作表、带格式化）。
- **数据库**：SQLite（零配置、适合个人）、MySQL（`--init_db mysql` 初始化、`--save_data_option db` 存储）、PostgreSQL（官方推荐生产环境）。README 提到存数据库自带去重。

小规模一次性分析用 JSONL 就够；要长期追踪、聚合分析再上数据库。

## 六、适用边界与合规

这部分是底线：

1. **License**：`NON-COMMERCIAL LEARNING LICENSE 1.1` 禁止商业用途，拿去做产品、SaaS、二次销售都违约。
2. **平台条款**：各目标平台的条款都不允许未授权的大规模抓取，可能触发封号或诉讼。
3. **个人信息**：抓取头像、昵称、评论原文涉及个人信息，建议只做公开数据分析、学术研究、运营内部参考，别对外发布原始数据集。
4. **司法案例**：README 免责声明点名了[《爬虫违法违规的案件》](https://github.com/HiddenStrawberry/Crawler_Illegal_Cases_In_China)汇总仓库，用前值得扫一眼。

作者在 README 顶部用警告强调"以学习为目的使用本仓库"，这是 License 和司法案例双重支撑的硬约束。

## 七、谁适合用、怎么用

- **运营/市场分析**：关键词搜索 + 评论词云做小规模竞品分析、舆情样本采集，单账号低频调用。
- **数据科学/研究**：用指定帖子 ID 或创作者主页模式做研究样本采集，落到 SQLite/MySQL 做后续分析。
- **爬虫学习者**：研究"浏览器登录态 + JS 取签名"怎么替代 JS 逆向，是浏览器自动化方向的有效范例。
- **不适合**：商业数据产品、大规模舆情监控、跨平台账号矩阵运营。

这套方案把"多平台 + 免逆向 + 登录态复用"串成一条能跑的工程链路，个人开发者一下午能跑通七个平台。只是 CDP 目前只覆盖小红书和抖音，其余平台仍是标准 Playwright 模式，别把它当成全平台免逆向的万能方案。

## 参考

- 仓库：[NanmiCoder/MediaCrawler](https://github.com/NanmiCoder/MediaCrawler)
- 在线文档：[https://nanmicoder.github.io/MediaCrawler/](https://nanmicoder.github.io/MediaCrawler/)
- 作者爬虫教程：[CrawlerTutorial](https://github.com/NanmiCoder/CrawlerTutorial)
- 进阶版：[MediaCrawlerPro](https://github.com/MediaCrawlerPro)（断点续爬、多账号、去 Playwright 依赖等）