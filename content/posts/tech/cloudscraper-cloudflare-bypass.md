---
title: "cloudscraper：Python 反爬与 Cloudflare 绕过指南"
date: "2026-04-14T22:00:00+08:00"
lastmod: "2026-08-28T00:00:00+08:00"
slug: "cloudscraper-cloudflare-bypass"
github_repo: "VeNoMouS/cloudscraper"
description: "cloudscraper 是 Python 生态里专门处理 Cloudflare JS 挑战页的工具，通过 JavaScript 解释器执行挑战脚本、取回 cookie，再重放请求。本文基于官方文档梳理原理、解释器选择、版本差异、生产配置与适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["Python", "爬虫", "Cloudflare", "JavaScript"]
---

# cloudscraper：Python 反爬与 Cloudflare 绕过指南

## 平台定位

cloudscraper 处理的是一类非常具体的拦截：Cloudflare 在返回网页内容之前，先返回一个「正在检查你的浏览器」的挑战页。用 `requests` 抓这种站点，拿到的不是数据，而是 403 或一段挑战 HTML——因为 `requests` 不会执行 JavaScript，而 Cloudflare 要的正是那段 JS 算出来的 cookie。

这个库的思路很直接：不反混淆 Cloudflare 的 JS，而是找一个 JavaScript 解释器，把挑战脚本原样执行一遍，取回 cookie，再用同一个会话重放请求。正因为如此，它解决的是「能靠执行 JS + 取 cookie 解决的挑战」；凡是还叠加了行为分析、验证码交互或设备指纹的站点，单靠它不够用。

项目由 [VeNoMouS](https://github.com/VeNoMouS) 于 2019 年创建，MIT 协议，纯 Python 实现。截至 2026 年 8 月，[cloudscraper](https://github.com/VeNoMouS/cloudscraper) 在 GitHub 上有 6.7k Stars、640 Forks。

读完这篇，你应该能回答两个问题：自己的采集任务该不该用 cloudscraper；真要用了，从默认配置起步怎么一步步加固到能长期稳定跑。

## 版本差异：先弄清楚你装的是哪个

用 cloudscraper 之前，版本这个问题必须搞清楚，因为两边的参数和功能不一样：

| 来源 | 版本 | 覆盖挑战 | 默认解释器 | 特色 |
|------|------|---------|-----------|------|
| PyPI 包 `cloudscraper` | 1.2.71 | v1 / v2 | native | 稳定、保守，原版维护 |
| GitHub `master` 分支 | v3.0.0 增强版 | v1 / v2 / v3 / Turnstile | js2py | 403 自动恢复、Stealth Mode、代理轮换、可执行文件兼容 |

增强版由 Zied Boughdir 贡献到主仓库的 `master` 分支，官方 README 即增强版文档。两个版本的 API 保持一致，`pip install cloudscraper` 装到的是 PyPI 上的 1.2.71；要用增强版能力，需要从仓库安装。基本用法的代码两个版本都能跑，涉及增强版参数的写法会单独标注。

## 总览：挑战类型与 cloudscraper 的分工

要读懂 cloudscraper，先分清「Cloudflare 侧有什么挑战」和「cloudscraper 用什么接」两张表：

| 挑战 | 特点 | cloudscraper 支持 |
|------|------|-------------------|
| v1 | 页面嵌入一段 JS，执行后生成 cookie，已基本淘汰 | 支持，可用 `disableCloudflareV1=True` 关闭 |
| v2 | 更复杂的 JS 挑战（即 IUAM 页面），混淆程度高 | 支持 |
| v3 | JS VM 挑战，动态生成代码在沙箱中执行 | 增强版支持，需要 js2py 或 Node.js 这类完整解释器 |
| Turnstile | 验证码替代方案，可能要求交互 | 增强版支持，可接第三方验证码服务 |

| cloudscraper 组件 | 职责 |
|-------------------|------|
| `CloudScraper` 会话 | 继承 `requests.Session`，自动接管被挑战的请求 |
| 挑战检测 | 依据状态码与响应头识别 v1 / v2 / v3 / Turnstile |
| JS 解释器 | 执行挑战脚本，算出 cookie（js2py / native / Node.js / V8 / ChakraCore）|
| 会话维护 | 自动 403 恢复、cookie 清理、指纹轮换（增强版）|
| 请求治理 | 请求节流、并发限制、TLS 密码套件轮换（增强版）|

Cloudflare 的检测和 cloudscraper 的绕过是两套独立机制：前者决定「什么样的请求会被拦」，后者决定「拿到挑战之后怎么应付」。先看前者，再看后者。

## Cloudflare 反爬原理：为什么 JS 挑战能挡住大多数爬虫

访问一个受保护的站点，如果请求被判定可疑，服务器不返回页面正文，而是返回一段挑战 HTML。浏览器会显示这样一行提示：

```text
Checking your browser before accessing website.com.
This process is automatic. Your browser will redirect to your requested content shortly.
Please allow up to 5 seconds...
```

浏览器拿到这段 HTML 后，执行内嵌的 JS，算出结果并写进 cookie，然后自动重定向或重试。服务器核对 cookie 合法，才放行真实内容。

这个机制挡住普通爬虫的关键在于：`requests` 这类客户端是纯 HTTP 层工具，不解析 HTML，更不执行 JavaScript。它拿到挑战页后什么都做不了，只能拿到 403 或挑战页本身。cloudscraper 的绕过路径正是针对这个缺口——它给 `requests` 会话补了一个「能执行 JS」的部件。

需要说明的是，JS 挑战只是 Cloudflare 检测体系的一层。现代 Cloudflare 还会叠加 TLS/JA3 指纹、HTTP/2 指纹、鼠标键盘等行为分析、设备指纹。cloudscraper 管的是 JS 挑战这一层，其余各层要靠 TLS 指纹模拟（如 curl_cffi）、真实浏览器（如 Playwright）或风控规避去处理，这些在「适用边界」一节展开。

## cloudscraper 原理：执行，而不是反混淆

cloudscraper 的核心决策是不去解析 Cloudflare 的混淆 JS，而是让 JS 引擎直接把它跑完。挑战脚本在真实浏览器里怎么算，cloudscraper 就在解释器里怎么算，结果一致，cookie 自然一致。这省掉了反混淆这条路，也解释了为什么它需要一个可用的 JS 解释器。

解释器选择如下，默认值随版本不同：

| 解释器 | 说明 | 备注 |
|--------|------|------|
| `js2py` | 纯 Python 实现的 JS 解释器 | 增强版默认，随包安装 |
| `native` | cloudscraper 自带的原生 Python 求解器 | PyPI 原版默认，无外部依赖 |
| `nodejs` | 调用系统 Node.js | 速度快、兼容性好，但目标机器要有 Node |
| `v8` | 通过索尼的 v8eval 模块调用 V8 引擎 | 需要额外安装 v8eval |
| `chakracore` | 调用微软 ChakraCore 引擎 | 需要引擎二进制 |

选择原则：默认能跑就不折腾；遇到 js2py 解不了的复杂 v3 脚本，优先试 `nodejs`。

首次访问受挑战站点时，cloudscraper 会等待约 5 秒（挑战执行需要时间），之后的同一会话请求不再重复等待。这是 Cloudflare 挑战页的常规节奏，不是故障。

## 安装与基本使用

```bash
pip install cloudscraper
```

上面这条装的是 PyPI 上的原版 1.2.71。需要增强版的 v3 / Turnstile / 403 自动恢复能力时，从仓库安装：

```bash
pip install git+https://github.com/VeNoMouS/cloudscraper.git
# 或克隆后 pip install .
```

基本用法和 `requests.Session` 几乎一样：

```python
import cloudscraper

scraper = cloudscraper.create_scraper()
response = scraper.get("https://example.com")
print(response.status_code)
print(response.text[:200])
```

`create_scraper()` 返回 `CloudScraper` 实例，继承 `requests.Session`，`get` / `post` 等方法和原来一致。对没用 Cloudflare 的站点，它就是一个普通 Session，不会有额外开销。

想单独把解算出的 cookie 拿给其他客户端用（比如 curl、另一个语言写的脚本），有两个方法：

```python
# 返回以 cookie 名为键的字典，常见的解算结果是 cf_clearance
tokens = scraper.get_tokens("https://example.com")
print(tokens)

# 返回 "name=value; name2=value2" 形式的字符串，可直接粘进请求头
cookie_string = scraper.get_cookie_string("https://example.com")
print(cookie_string)
```

## 一次请求如何穿过 cloudscraper

拿「抓取一个受 v2 挑战保护的页面」为例，看一次请求在内部经历了什么：

1. 第一次 `scraper.get(url)` 发出，Cloudflare 返回 503 和挑战 HTML。
2. `CloudScraper` 会话检测到挑战响应，标记该请求需要解算。
3. 从挑战 HTML 中提取挑战脚本。
4. 交给配置的解释器（如 js2py）执行，得到目标 cookie。
5. 把 cookie 写入会话，重放原来的请求。
6. 服务器核对通过，返回真实页面内容。

整个过程对调用方透明，你看到的只是 `get()` 返回了 200 和正文。首次约 5 秒，之后同一会话内的请求直接复用 cookie，不再解算。想观察内部发生了什么，可以打开调试输出（增强版）：

```python
scraper = cloudscraper.create_scraper(debug=True)
```

调试模式下会打印检测到的挑战类型和解释器执行过程，排查「为什么没解成功」时很有用。

## 生产配置

单次抓取用默认配置就够了，长期跑、高频跑，需要按场景调参数。以下参数均为增强版。

### 应对持续 403：自动恢复

长时间运行后，会话的 cookie 可能失效，请求开始返回 403。增强版会在检测到 403 时自动刷新会话、清理 cookie、轮换指纹：

```python
scraper = cloudscraper.create_scraper(
    auto_refresh_on_403=True,   # 403 时自动恢复
    max_403_retries=3,          # 最多重试次数
    session_refresh_interval=1800,  # 每 30 分钟主动刷新一次
)
```

### 减小被行为分析命中的概率：Stealth Mode

Stealth Mode 模拟人类浏览节奏，降低触发行为分析的风险：

```python
scraper = cloudscraper.create_scraper(
    enable_stealth=True,
    stealth_options={
        "min_delay": 1.0,
        "max_delay": 3.0,
        "human_like_delays": True,
        "randomize_headers": True,
        "browser_quirks": True,
    },
)
```

延迟设太长会拖慢整体速度甚至触发超时，官方示例和建议集中在 1-3 秒区间。

### 高频与并发：节流 + TLS 指纹轮换

同时开多个请求时，TLS 握手的特征会被识别，导致集体 403。增强版通过请求节流和密码套件轮换来缓解：

```python
scraper = cloudscraper.create_scraper(
    min_request_interval=2.0,   # 两次请求最小间隔，防止 TLS 被限
    max_concurrent_requests=1,  # 强制串行，避免并发冲突
    rotate_tls_ciphers=True,    # 轮换 8 组密码套件，规避指纹检测
)
```

代价是吞吐量下降。要并发，建议开多个进程各自带独立会话，而不是在单会话里堆线程。

### IP 被限：代理轮换

```python
scraper = cloudscraper.create_scraper(
    rotating_proxies=[
        "http://user:pass@proxy1.example.com:8080",
        "http://user:pass@proxy2.example.com:8080",
    ],
    proxy_options={
        "rotation_strategy": "smart",
        "ban_time": 300,
    },
)
```

需要提醒的是：代理只解决 IP 维度的问题，TLS 指纹检测照样会发生，所以代理轮换要配合 `rotate_tls_ciphers` 和节流一起用，否则换多少个 IP 都还是 403。

### 遇到 Turnstile：接第三方验证码服务

Turnstile 可能要求交互，纯自动解法不稳定。增强版支持对接验证码求解服务：

```python
scraper = cloudscraper.create_scraper(
    captcha={
        "provider": "2captcha",
        "api_key": "你的 key",
    },
)
```

支持的服务商不止 2captcha（如 anticaptcha、CapSolver 等）。这属于付费外接能力，接口以项目 README 为准。

### 组合成一个生产示例

```python
import cloudscraper

scraper = cloudscraper.create_scraper(
    interpreter="js2py",
    delay=5,
    browser="chrome",
    enable_stealth=True,
    stealth_options={
        "min_delay": 1.0,
        "max_delay": 3.0,
        "human_like_delays": True,
        "randomize_headers": True,
        "browser_quirks": True,
    },
    rotate_tls_ciphers=True,
    min_request_interval=2.0,
    max_concurrent_requests=1,
    auto_refresh_on_403=True,
    max_403_retries=3,
    session_refresh_interval=1800,
)

response = scraper.get("https://example.com")
print(response.status_code)
```

这一套偏向稳定优先，适合长时间运行的采集任务；对速度敏感、目标站点防护较弱的场景，可以关掉 Stealth、放宽节流。

## 打包成可执行文件

把带 cloudscraper 的应用用 PyInstaller 打包时，常见坑是 `browsers.json`（User-Agent 数据库）没被带进产物，导致运行时 UA 相关报错。增强版对这一场景做了兼容处理：自动检测 PyInstaller 环境、尝试多个路径找 `browsers.json`，缺失时回退到内置的 70+ 条硬编码 User-Agent。

两种打包方式：

```bash
# 直接打包，依赖内置回退
pyinstaller your_app.py

# 推荐：把完整 UA 数据库带进产物
pyinstaller --add-data "cloudscraper/user_agent/browsers.json;cloudscraper/user_agent/" your_app.py
```

Windows 上 `--add-data` 的分隔符是 `;`，Linux / macOS 是 `:`。cx_Freeze、auto-py-to-exe 的兼容处理同理。

## 声称的通过率：测的是什么，不能推出什么

增强版 README 写着「All features tested with 100% success rate」（所有功能 100% 通过）。这个数字需要正确看待：

- 它测的是什么：项目自带的测试脚本，验证每个核心功能（基础请求、UA 处理、v1/v2/v3 挑战、Stealth）的代码路径能按预期走通。测的是「能识别挑战、完成解算流程」这条链路是否健壮。
- 它反映什么：代码本身的正确性，不是真实网络环境下的绕过成功率。
- 它不能推出什么：不能推出「能绕过任意 Cloudflare 站点」。真实成功率取决于目标站点是否叠加了行为分析、管理挑战、地区风控，以及 Cloudflare 当时是否刚更新过挑战算法。今天能解的站点，下周可能就解不了。这类项目自报的成功率要打折看，实际效果以你自己对目标站点的实测为准。

## 适用边界与决策建议

**什么时候值得用 cloudscraper**：目标是普通的 v1/v2/v3 JS 挑战保护、你已经有 `requests` 代码、想以最小成本接入绕过能力。它把 `requests` 升级成能过 JS 挑战的会话，改造成本极低。

**什么时候该换方案**：

| 场景 | 建议方案 | 原因 |
|------|---------|------|
| 403 由 TLS/JA3 指纹引起 | curl_cffi | 直接模拟浏览器 TLS 指纹，比轮换密码套件更接近真实浏览器 |
| 挑战难度高、需要完整浏览器环境 | Playwright / Selenium | 用真实浏览器执行，兼容性最强，但慢、重、耗资源 |
| 需要给多个客户端提供解算能力 | FlareSolverr | 把浏览器解算封装成独立服务，前端各语言都能调用 |
| 目标站点强烈依赖行为分析 | 人工或专业反爬风控 | 代码层面很难稳定绕过，不建议硬扛 |

**上手顺序**：先用默认配置跑通一个受保护站点，确认能拿到 200 和正文；再看调试输出确认挑战类型和解释器工作正常；然后按需加 Stealth、节流和 403 自动恢复。不要一开始就把所有参数堆上，参数多了反而难定位问题。

**合规提醒**：cloudscraper 是开源工具，但用它访问哪些站点由你自己负责。只对你拥有或获授权的站点使用，遵守目标站点的 `robots.txt` 与服务条款；未经授权爬取受版权保护或明确禁止自动访问的内容，可能构成违约或侵权。Cloudflare 的挑战机制本身是合理的安全措施，本文讲解原理是为了让读者理解其工作方式，不代表鼓励绕过他人设置的访问控制。

## 常见问题与排查

**一直 403，普通参数都试了**

先确认 403 是不是 Cloudflare 挑战引起的。如果启用了 TLS 指纹防护，试 `rotate_tls_ciphers=True` 或直接换 curl_cffi；如果站点强依赖行为分析，换 Playwright 更实际。也可以用浏览器打开目标站点，看是否有人工验证码——有的话 cloudscraper 单靠默认配置很难处理。

**js2py 解挑战失败或很慢**

换 `interpreter="nodejs"`，前提是运行环境装了 Node.js。v3 这类复杂脚本用 Node 的兼容性明显好于纯 Python 解释器。

**打包后报 UA / agent_user 相关错误**

确认 `browsers.json` 是否随产物一起分发，用带 `--add-data` 的命令重新打包；增强版有内置回退，一般不会崩，但行为可能退化到固定 UA。

**首次请求总是慢 5 秒左右**

正常现象。这是挑战执行所需的时间，第二次开始同一会话不再重复。如果是批量采集，把请求复用在同一个 `scraper` 实例上，不要每次新建。
