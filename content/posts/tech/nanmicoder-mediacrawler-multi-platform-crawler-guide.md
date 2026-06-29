---
title: "MediaCrawler：多平台自媒体数据采集工具的 CDP 实践"
date: "2026-06-26T18:02:04+08:00"
slug: "nanmicoder-mediacrawler-multi-platform-crawler-guide"
description: "深度解析 GitHub 53k+ Star 的 MediaCrawler 多平台爬虫项目，覆盖小红书/抖音/B站/微博等 7 大平台，基于 Playwright + CDP 模式绕过 JS 逆向。"
draft: false
categories: ["技术笔记"]
tags: ["Python", "Playwright", "爬虫", "CDP", "开源工具"]
---

# MediaCrawler：多平台自媒体数据采集工具的 CDP 实践

## 一、项目核心判断

MediaCrawler 是 GitHub 上一个聚焦"国内自媒体平台公开数据采集"的开源项目，作者 NanmiCoder（relakkes）。它在没有走传统 JS 逆向路线的前提下，靠 Playwright 浏览器自动化 + CDP（Chrome DevTools Protocol，Chrome 开发者工具协议）模式同时接入了小红书、抖音、快手、B 站、微博、百度贴吧、知乎七个平台。截至 2026 年 6 月，仓库 Star 数 53,176，Fork 数 10,955，License 为作者自定的 `NON-COMMERCIAL LEARNING LICENSE 1.1`（非商业学习许可证），与主流 OSI（Open Source Initiative，开源促进会）协议不兼容。

这个项目最值得关注的不是平台覆盖广度，而是它的"反直觉"技术选择：在一个大多数爬虫项目都会堆逆向代码的领域，它选择用浏览器登录态缓存 + JS 表达式取签名参数的方式绕过加密算法，把技术门槛从"逆向工程师"降到了"会用浏览器的人"。这种范式选择对个人开发者做小规模数据分析、运营做竞品监控、研究者做舆情样本采集都有直接价值。

下文会先给一张七平台覆盖矩阵作为系统地图，再拆解 CDP 模式的工程取舍，最后给出可直接跑起来的最小上手步骤和适用边界。

## 二、系统地图：七平台覆盖矩阵

MediaCrawler 把"爬什么"和"怎么爬"做了清晰拆分。每个平台共享同一套 CLI（命令行界面）参数（`--platform`、`--lt` 登录方式、`--type` 爬取类型），但底层签名逻辑各自实现。下表来自 README 的能力矩阵，整理后便于一眼看清支持范围。

| 平台 | 关键词搜索 | 指定帖子 ID | 二级评论 | 指定创作者主页 | 登录态缓存 | IP 代理池 | 评论词云图 |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 小红书 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 抖音 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 快手 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| B 站 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 微博 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 百度贴吧 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 知乎 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

所有平台能力对齐，意味着换平台时不需要重写业务逻辑，只需改 `--platform` 参数。这一点是它与很多"单平台脚本合集"型仓库的本质区别。

## 三、架构亮点：CDP 模式 vs JS 逆向

### 3.1 传统爬虫的痛点

国内自媒体平台的接口基本都做了双重防护：登录态校验 + 参数签名（signature，对请求参数做的加密摘要，常见算法有 MD5、SHA1、HMAC 等）。传统的反爬绕过方式有两条路：

1. **JS 逆向**：用 AST（抽象语法树）解析、Hook（钩子，即拦截浏览器内部函数调用）还原加密算法，再纯 Python 重写一遍。维护成本高，平台一改版本就废。
2. **协议模拟**：用 requests/httpx 直接请求签名接口，签名失败率高，且容易被风控。

两条路都要求对加密算法有深入理解，门槛高、迭代慢。

### 3.2 MediaCrawler 的取舍

MediaCrawler 走了第三条路：直接接管用户本地已经登录好的 Chrome 浏览器，在那个浏览器上下文里执行爬取逻辑。具体来说：

- **CDP 接入**：通过 `chrome://inspect/#remote-debugging` 开启 Chrome 远程调试（默认端口 9222），MediaCrawler 用 Playwright 的 `connect_over_cdp` 模式接管这个浏览器实例，**复用用户已经登录的 Cookie（浏览器存储的登录凭证）**。
- **签名现取**：在浏览器里执行 JS 表达式直接拿到 X-s、X-s-common 等签名参数，不在 Python 端做任何加密还原。
- **登录态持久化**：第一次扫码登录后，登录态被序列化到本地（README 提到的"登录态缓存"），后续启动直接复用，**不需要每次重新扫码**。

这套设计的工程意义是：平台的签名算法升级时，只要浏览器端没失效，Python 端就不需要改动。对个人开发者来说，升级成本从"逆向工程师改代码"降到了"重启 Chrome 一次"。

### 3.3 代价

这套方案不是免费的，有几个明显代价：

- **必须保留浏览器进程**：爬虫运行期间，Chrome 浏览器不能关闭。README 明确要求"Chrome 弹出确认对话框需在 60 秒内点击接受"。
- **依赖真实登录态**：单账号高频访问仍会被风控（这是所有登录态方案的共性问题，MediaCrawler 不能解决），需要配合 IP 代理池使用。
- **不可商用**：作者 License 明确禁止商业用途，且免责声明里写了"严禁用于任何非法目的或非学习、非研究的商业行为"。

## 四、快速上手

下面以小红书关键词搜索为例，给出最小可运行步骤。完整命令均来自 README 验证可复现。

### 4.1 环境准备

- **Python 包管理**：项目推荐用 [uv](https://docs.astral.sh/uv/getting-started/installation)（Rust 写的 Python 包管理工具，比 pip 快 10-100 倍）。安装后用 `uv --version` 验证。
- **Node.js**：版本 >= 16，下载 [https://nodejs.org/en/download/](https://nodejs.org/en/download/)。
- **Chrome**：版本 >= 144，开远程调试（`chrome://inspect/#remote-debugging` 勾选 Allow remote debugging）。
- **Node.js 抖音/知乎依赖**：这两个平台的签名依赖 Node.js 内的 JS 模块（README 提到）。

### 4.2 安装与运行

```bash
# 1. 克隆并进入项目
git clone https://github.com/NanmiCoder/MediaCrawler.git
cd MediaCrawler

# 2. 用 uv 同步依赖（推荐，uv 会自动管理 Python 版本）
uv sync

# 3. 第一次启动：以小红书为例，扫码登录
uv run main.py --platform xhs --lt qrcode --type search

# 4. 后续启动会复用已保存的登录态，无需再次扫码
```

> `uv run` 会激活虚拟环境并执行命令，等价于 `source .venv/bin/activate && python main.py ...`。

### 4.3 配置项速查

主要开关在 `config/base_config.py` 里集中管理，关键项：

- `ENABLE_CDP_MODE`：是否启用 CDP 模式，默认 `True`。设为 `False` 切换为标准 Playwright 模式（需要 `playwright install` 下载浏览器驱动）。
- `ENABLE_GET_COMMENTS`：是否爬评论，默认 `False`（**第一次用很容易漏掉这一项**）。
- 关键词、创作者 ID 列表、爬取页数等都在 `base_config.py` 同文件中。

### 4.4 WebUI 模式

如果不习惯命令行，README 提供了 WebUI 入口：

```bash
uv run uvicorn api.main:app --port 8080 --reload
# 浏览器打开 http://localhost:8080
```

可视化界面支持配置平台、登录方式、爬取类型，实时查看日志和导出数据。

## 五、数据存储

MediaCrawler 支持六种数据落盘方式，README 链接的 [`docs/data_storage_guide.md`](https://github.com/NanmiCoder/MediaCrawler) 给了详细说明。简单归纳：

- **本地文件**：CSV、JSON、JSONL（每行一条 JSON，适合大文件流式处理）、Excel。个人小规模分析够用。
- **数据库**：SQLite（零配置，适合单机）、MySQL（多机/团队协作）。
- **可视化**：评论词云图（在 `docs/static/images/` 下有示例）。

选择上没有绝对优劣，看数据量级和后续分析链路。一次性几百条数据用 JSONL 就够，长期追踪+聚合分析用 MySQL 更稳。

## 六、适用边界与法律风险

这部分必须单独强调，因为这是合规学习的底线：

1. **License 限制**：`NON-COMMERCIAL LEARNING LICENSE 1.1` 是作者自定的许可证，**禁止商业用途**。拿这套代码做产品、二次销售、SaaS 化（Software as a Service，软件即服务）都构成违反协议。
2. **平台用户协议**：所有目标平台（小红书/抖音/B 站/微博等）的 ToS（Terms of Service，服务条款）都不允许未授权的大规模数据抓取。商业级抓取可能触发账号封禁、法律诉讼。
3. **数据保护法**：抓取用户头像、昵称、评论原文涉及个人信息，需符合《个人信息保护法》。建议**只用于公开数据分析、学术研究、运营内部参考**，不要对外发布包含个人信息的原始数据集。
4. **爬虫行为边界**：README 免责声明里点名了[《爬虫违法违规的案件》](https://github.com/HiddenStrawberry/Crawler_Illegal_Cases_In_China)汇总仓库，用前值得扫一眼。

作者在 README 顶部用 ⚠️⚠️⚠️ 强调"大家请以学习为目的使用本仓库"，这不是客套话，是 License 与司法案例双重支撑下的硬约束。

## 七、谁适合用，怎么用

总结一下适用场景和人群：

- **运营/市场分析**：用关键词搜索 + 评论词云做小规模竞品分析、舆情样本采集，**单账号低频调用**。
- **数据科学/学术研究**：用指定帖子 ID 或创作者主页模式做研究样本采集，配合 SQLite/MySQL 落到本地数据库做后续分析。
- **爬虫学习者**：研究 CDP 模式如何替代 JS 逆向，是浏览器自动化方向的好范例；架构上 JS 签名与 Python 业务逻辑的解耦也值得参考。
- **不适合**：商业数据产品、大规模舆情监控、跨平台账号矩阵运营。

MediaCrawler 的真正价值不在于"能爬多少数据"，而在于把"多平台 + 免逆向 + 登录态复用"这三件事用工程化方式串起来，让个人开发者第一次能在一个下午内跑通七平台爬虫。如果你的需求刚好落在这个区间，它是当前 GitHub 上最成熟的选项之一；如果不在这个区间，要么接受 License 与法律边界，要么自己另起炉灶。

## 参考

- 仓库：[https://github.com/NanmiCoder/MediaCrawler](https://github.com/NanmiCoder/MediaCrawler)
- 文档站：[https://nanmicoder.github.io/MediaCrawler/](https://nanmicoder.github.io/MediaCrawler/)
- 作者 B 站：[https://space.bilibili.com/434377496](https://space.bilibili.com/434377496)
- 相关项目：[CrawlerTutorial](https://github.com/NanmiCoder/CrawlerTutorial)（作者维护的爬虫入门教程）
- 同类项目：[NewsCrawlerCollection](https://github.com/NanmiCoder/NewsCrawlerCollection)（新闻爬虫合集）
