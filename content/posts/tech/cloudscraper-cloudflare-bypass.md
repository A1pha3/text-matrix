---
title: "cloudscraper 解读：真正执行 JavaScript 的只有 v1，另外三条路在提交表单"
date: "2026-04-14T22:00:00+08:00"
lastmod: "2026-09-21T00:00:00+08:00"
slug: "cloudscraper-cloudflare-bypass"
github_repo: "VeNoMouS/cloudscraper"
source_key: "gh:VeNoMouS/cloudscraper"
description: "对照 VeNoMouS/cloudscraper 的 master（提交 9ea528a，v3.0.0）与 PyPI 1.2.71 逐条读源码：四类挑战页各自的检测判据、只有 v1 会调用 JS 解释器算出 jschl_answer、v2 提交空应答、v3 回退到哈希或随机数、get_tokens 返回的是二元组，以及默认开启的节流与密码套件轮换带来的每秒请求数上限。"
draft: false
categories: ["技术笔记"]
tags: ["Python", "爬虫", "Cloudflare", "JavaScript"]
---

> **目标读者**：手上已有 `requests` 代码、遇到 Cloudflare 拦截页在挑工具的人；以及已经用了 cloudscraper、需要判断它为什么在某些站点失效的维护者。
> **核心问题**：这个库到底解掉了什么，没解掉的部分靠什么补，以及默认配置替你做了哪些决定。
> **事实边界**：本文核对的是 `VeNoMouS/cloudscraper` 默认分支 `master` 的提交 `9ea528a`（版本号 3.0.0）、PyPI 上 `cloudscraper` 1.2.71 的 wheel 内容，以及 2026-09-21 通过 GitHub 应用程序接口（API）读到的仓库数据。机制描述尽量指到仓库内的文件与行号；官方未给出的通过率、耗时数字，本文只写测试脚本实际测到的东西。

## 一句话判断

cloudscraper 值得看的不是「能不能绕过 Cloudflare」，而是它把一件事做得很干净、其余三件事做成了占位：**只有 v1 那一类拦截页会真的把脚本交给 JS 解释器执行并算出答案**（`cloudscraper/cloudflare.py:231`）。v2 的 JS 挑战走的是提交一张 `h-captcha-response` 为空串的表单，v3 在算不出答案时回退到哈希值或六位随机数，Turnstile 则把求解整个外包给付费服务商。

三条路径的完成度差得很远，README 却把它们并列成四个「✅ NEW / ✅ FIXED」。把它当成 v1 时代的专用钥匙，它的改造成本几乎为零；把它当成现代 Cloudflare 的通用钥匙，你会把时间花在调参数上，而问题在页面上。

还有一点必须先进视野：仓库最后一次提交是 2025-06-10，README 里那句「Cloudflare 会定期换手法，因此本仓库会频繁更新」所承诺的事，此后没有再发生。对一个与远端算法赛跑的项目，15 个月的空档本身就是结论的一部分。

## 项目坐标（2026-09-21 核对）

| 字段 | 值 |
|------|------|
| 仓库 | [VeNoMouS/cloudscraper](https://github.com/VeNoMouS/cloudscraper)，默认分支 `master`，建仓 2019-04-16，最近推送 2025-06-10 |
| Stars / Forks | 6,751 / 640（GitHub API 当日读数） |
| 开放议题与合并请求 | 36（该字段是两者之和） |
| 协议 | MIT。`LICENSE` 里有三行版权：`copyright (c) 2025 Zied Boughdir`、`Copyright (c) 2019 VeNoMouS`、`Copyright (c) 2015 Anorov`，最后一行是这条血缘的起点 |
| 代码版本 | `cloudscraper/__init__.py:44` 写 `__version__ = '3.0.0'`，`pyproject.toml` 同步为 3.0.0，标签 `3.0.0` 与 GitHub Release 均在 2025-06-10 |
| 发布版本 | PyPI 最新仍是 1.2.71（上传于 2023-04-25，历史共 78 个发行版） |
| 语言构成 | 纯 Python，`cloudscraper/` 下 26 个 `.py` 文件、约 5,160 行 |
| 增强版作者 | `pyproject.toml` 的 authors 为 VeNoMouS 与 Zied Boughdir 两人，README 顶部署名「Enhanced by Zied Boughdir」 |

CHANGELOG 顶部把 3.0.0 标为 2025-01-09，而标签和 Release 记录都是 2025-06-10，中间隔着 2.5.2、2.7.0 等若干只出现在提交信息里的版本号，却没有对应标签。读提交史比读 CHANGELOG 更可靠。

## 系统地图：四条路径各自接什么

cloudscraper 内部有四个互不复用的处理器，外面再套一个负责分派的循环。先记住这张分工表，后面所有排查都落在这里。

| 处理器 | 文件 | 判定条件（全部要求 `Server` 头以 `cloudflare` 开头） | 拿到页面之后做什么 |
|--------|------|------|------|
| v1 | `cloudflare.py` | 429/503 + 页面含 `images/trace/jsch/`（其前缀 `/cdn-cgi/` 是内容分发网络（CDN）的固定路径） + 表单 action 含 `__cf_chl_f_tk=`；或 403 + `trace/(captcha\|managed)/` | 提取脚本交给解释器算 `jschl_answer`，或把验证码交给求解服务商 |
| v2 | `cloudflare_v2.py` | 403/429/503 + `cpo.src = '…/orchestrate/jsch/v1'`；403 + `…/orchestrate/(captcha\|managed)/v1` | 前者 POST 一张空 `h-captcha-response` 的表单，后者调服务商取令牌再填 |
| v3 | `cloudflare_v3.py` | 403/429/503 + `orchestrate/jsch/v3` 或 `window._cf_chl_ctx=` 或 action 含 `__cf_chl_rt_tk=` | 拼一段合成 JS 交给解释器，拿不到答案就回退哈希或随机数 |
| Turnstile | `turnstile.py` | 403/429/503 + `class="cf-turnstile"` 或 `turnstile/v0/api.js` 或 40 位 `data-sitekey` | 提取站点密钥交给验证码服务商，回填 `cf-turnstile-response` |

注意判据里的版本标签并不自洽：`cloudflare_v2.py` 认的是 URL 里的 `orchestrate/jsch/v1`，而 `cloudflare.py` 那条线认的是 `images/trace/jsch/`。仓库内部把「新版」叫 v2，跟 Cloudflare 自己写在 URL 里的 `v1`/`v3` 不是一回事。读源码时以文件名为准，别拿名字推逻辑。

除这四条主线外，`__init__.py` 里还挂着三件与 Cloudflare 无关的配套设施：会话健康监控（`_should_refresh_session`、`_refresh_session`）、请求节流与密码套件轮换（`_apply_request_throttling`、`_rotate_tls_cipher_suite`）、以及 `stealth.py` 和 `proxy_manager.py`。它们决定了每个请求发出去之前先睡多久、以什么 TLS 客户端特征发出去。

## 版本分界：PyPI 与 master 不是同一个东西

这是用 cloudscraper 前最容易踩空的一步，因为两条线的参数集和解算范围都不一样。

| | PyPI `cloudscraper` 1.2.71 | `master`（3.0.0） |
|---|---|---|
| 默认解释器 | `native`（`kwargs.pop('interpreter', 'native')`） | `js2py`（`__init__.py:135`） |
| 依赖 | 只要 requests、requests-toolbelt、pyparsing | 另加 js2py、pyOpenSSL、pycryptodome、websocket-client（WebSocket 客户端库）、brotli、certifi |
| 模块数 | `cloudflare.py` 一个处理器 | 多出 v2、v3、turnstile、stealth、proxy_manager 五个模块 |
| 遇到 v2 页面 | 抛 `CloudflareChallengeError`，文案为「This feature is not available in the opensource (free) version.」 | 进 `cloudflare_v2.py` 的处理分支 |
| 节流 / 403 恢复 | 无 | 有，且默认开启 |

所以「装哪个」不是口味问题：`pip install cloudscraper` 拿到的是 2023 年的 1.2.71，它对 v2 之后的页面只会抛错；而 `master` 的 3.0.0 从未上传到 PyPI，尽管 `pyproject.toml` 里的包名就叫 `cloudscraper`、CI 里也确实写了 `twine upload dist/*`（只在 publish release 时触发）。仓库有 30 个 GitHub Release 记录，最新一个是 3.0.0，说明发布通道走通了 GitHub 那一半。

要用增强能力，从版本控制装：

```bash
pip install git+https://github.com/VeNoMouS/cloudscraper.git
# 或者克隆后 pip install .
```

装错方向的代价很实在：1.2.71 的依赖表里没有 js2py，你若按 master 的 README 去配 `interpreter='js2py'`，拿到的是 `ImportError`；反过来在 1.2.71 上传 `enable_stealth`，参数会被静默丢掉，因为它压根没有这个分支。

一个容易忽略的连续性事实：v1 那条线在两版之间没有演化。1.2.71 的 `cloudflare.py`、`interpreters/native.py`、`interpreters/encapsulated.py` 与 master 上的同名文件逐行相同（只差行尾符），`user_agent/browsers.json` 更是字节一致，均为 1,206,600 字节。增强版加的是旁路，不是把主路修好了。

## 安装与最小可用

```bash
pip install cloudscraper        # 1.2.71，只有 v1
```

最小用法与 `requests.Session` 一致：

```python
import cloudscraper

scraper = cloudscraper.create_scraper()   # 返回 CloudScraper 实例
resp = scraper.get('https://example.com')
print(resp.status_code)
```

`CloudScraper` 继承 `requests.Session`，`get`/`post` 语义不变，因此已有代码的改动量是把 `requests.Session()` 换成 `create_scraper()` 一行。`create_scraper`、`session`、`get_tokens`、`get_cookie_string` 都是模块级别名（`__init__.py:813` 起），`cloudscraper.session()` 与 `cloudscraper.create_scraper()` 等价。

## 唯一真正执行 JavaScript 的路径：v1

v1 是这套代码里唯一完整跑通「读页面 → 执行脚本 → 得到数值 → 提交」的链路，其余三条都没有这一步。

它的入口判据之后，`IUAM_Challenge_Response`（`cloudflare.py:200`）做三件事。先从表单里抠出 `r`、`jschl_vc`、`pass` 三个字段，再把整个响应体和域名交给解释器算答案：

```python
payload['jschl_answer'] = JavaScriptInterpreter.dynamicImport(
    interpreter
).solveChallenge(body, hostParsed.netloc)
```

`solveChallenge` 的收尾是 `'{0:.10f}'.format(float(...))`，即把执行结果格式化成 10 位小数的字符串——这正是 Cloudflare 页面里那句 `a.value=...toFixed(10)` 的镜像。

为什么要真的执行：v1 页面把答案计算写成了一段 JSFuck 风格的表达式，混淆后的字符集只有 `!+[]()` 这几种。cloudscraper 的选择是不去反混淆，而是给 JS 引擎造一个最小假的运行环境，让它自己算。这个假环境在 `interpreters/encapsulated.py` 的 `template()` 里：

```python
js = re.search(
    r'setTimeout\(function\(\){\s+(.*?a\.value\s*=\s*\S+toFixed\(10\);)',
    body, re.M | re.S
).group(1)
```

匹配不到就 `raise ValueError('Unable to identify Cloudflare IUAM Javascript on website.')`。后面还有两件事：把 `k='xxx'` 与 `<div id="kNNN">…</div>` 里的子变量抓出来拼成 `subVars`，以及给 `document.getElementById`、`String.prototype.italics` 打补丁。

理解这段判据很重要，因为它是**整个解释器体系的地基**：js2py、nodejs、v8、chakracore 四个入口都在调用 `template()` 之后才把代码丢给引擎，`native` 则用自己那份 `setTimeout(function(){ var …` 正则。五个解释器因此共享同一个前置条件——页面必须是 v1 那个形状。页面不是 v1 形状时，切换解释器不会改变结果，因为失败发生在进入解释器之前。

顺带解释了一件事：为什么 `debug=True` 有时打印的是 `Unable to identify Cloudflare IUAM Javascript`。这不是解释器算错了，是提取阶段就没通过。

v1 的提交延时也不是常量。若没显式传 `delay`，代码从页面里把 `submit(); }, <毫秒>` 的数值读出来除以 1000（`cloudflare.py:384`）。v2、v3、Turnstile 三个模块则是 `self.delay = self.cloudscraper.delay or random.uniform(1.0, 5.0)`。README 里「首次访问睡约 5 秒」这句，准确说法是：延时来自页面本身，或者是一个 1 到 5 秒的均匀随机数。

`doubleDown` 是 v1 验证码分支里的一个小机关（默认 True）：某些站点只检查 `cf_clearance` 是否已填充，于是先发一次原请求把 cookie 落下来，再看第二次响应是不是仍然要求验证码，是才去调服务商。这个参数存在的理由写在源码注释里。

## 解释器：五个入口，一条模板

README 列了五个解释器，`interpreters/` 目录下也确实各有一个模块文件。它们的差别在于把 `template()` 拼好的那段代码丢给谁跑。

| 取值 | 依赖 | 执行方式 | 备注 |
|------|------|---------|------|
| `js2py` | js2py ≥ 0.74（master 的硬依赖，1.2.71 不带） | 纯 Python 解释器，`disable_pyimport()` + 新建 `EvalJs` 上下文 | master 默认 |
| `native` | 无外部依赖 | 自带 JSFuck 求值器 | 1.2.71 默认 |
| `nodejs` | 系统装有 Node.js | base64 传参，`require("vm").runInNewContext(…, {timeout: 4000})` | 超时 4 秒写死在字符串里 |
| `v8` | `v8eval`（索尼维护） | 未安装即 `RuntimeError` | 需要额外装包 |
| `chakracore` | ChakraCore 动态库 | `ctypes.CDLL` 载入 | 需要引擎二进制 |

js2py 那一行还藏着一个兼容补丁：先用一段 JSFuck 探针判断版本，若结果不对就打印升级警告并对负载跑 `jsunfuck()`。这段逻辑来自 js2py 旧版本对某些表达式求值有误的历史问题。

选择原则因此比「哪个更快」更朴素：**先确认页面是 v1 形状**，再在解释器之间换。`nodejs` 的 4 秒超时和真 V8 语义，对超出 Python 模拟能力的大脚本确实更稳，但它救不了格式不匹配。

## v2：JS 挑战与 hCaptcha 挑战是两条不同的路

`cloudflare_v2.py` 里有两个入口，被 `request()` 分派到不同的处理函数，完成度差得很远。

`is_V2_Captcha_Challenge`（第 70 行）那条线是完整的：提取 `data-sitekey`，调 `Captcha.dynamicImport(provider).solveCaptcha('hCaptcha', …)`，把服务商返回的令牌写进 `payload['h-captcha-response']`（第 249 行）。它不猜，只是花钱。

`is_V2_Challenge` 那条线则没有解算步骤。`handle_V2_Challenge`（第 161 行）依次做四件事：用正则找 `window._cf_chl_opt=({…});`、`time.sleep(self.delay)`、调 `generate_challenge_payload`、POST 到表单 action。中间没有任何一行碰解释器。而它提交的载荷长这样（第 127 至 141 行）：

```python
payload = {
    'r': r_token.group(1),
    'cf_ch_verify': 'plat',
    'vc': '',
    'captcha_vc': '',
    'cf_captcha_kind': 'h',
    'h-captcha-response': ''
}
```

`cf_captcha_kind` 是 `h`，`h-captcha-response` 是空串。这段代码的语义是「把 r 令牌和页面数据原样还回去，答案栏留空」。能不能过，取决于目标站点的 Cloudflare 配置是否接受一个不带验证码令牌的重提交，而不是取决于本地算力。把 `interpreter` 换成任何值都不会影响这条路径，因为它根本不进解释器。

还有一个容易读漏的相互作用：`cloudflare.py` 的 `is_Challenge_Request` 里保留着两处 `simpleException`，遇到「new captcha」或「new IUAM」页面就抛「此功能不在开源版本里」。但 `request()` 的检查顺序是 Turnstile → v3 → v2 → v1（`__init__.py:397` 起），而 `is_New_IUAM_Challenge` 的判据是 `is_IUAM_Challenge` 且 `orchestrate/jsch/v1`，后者与 `is_V2_Challenge` 的条件重合。于是这类页面在进入 v1 之前就被 v2 接住了，v1 里那句「not available in the opensource version」在 3.0.0 的实际执行路径中基本不可达。1.2.71 没有 v2 模块，这句话才真的会抛出来。

## v3：合成上下文与兜底数字

v3 是 README 标得最响的一项（「Handle the latest and most sophisticated Cloudflare protection」），代码结构也最绕，值得逐层看。

`cloudflare_v3.py` 的 `extract_v3_challenge_data` 抓四样东西：`window._cf_chl_ctx`、`window._cf_chl_opt`、表单 action，以及一段包含 `window._cf_chl_enter` 的 `<script>` 内容。然后 `execute_vm_challenge`（第 144 行）自己造了一个假的浏览器环境，把上面两个对象注进去，末尾拼上抓来的脚本，再要求解释器返回 `_cf_chl_answer`：

```python
if (typeof window._cf_chl_answer !== 'undefined') {
    window._cf_chl_answer;
} else if (typeof _cf_chl_answer !== 'undefined') {
    _cf_chl_answer;
} else {
    Math.random().toString(36).substring(2, 15);
}
```

关键在于「拿不到」时的两级退让。第一级是这段 JS 自带的 `Math.random()` 分支；第二级在 Python 侧——`eval` 抛任何异常都会被 `except Exception` 吞掉并转去 `generate_fallback_response`（第 220 行）：

```python
if 'chlPageData' in opt_data:
    response = str(hash(page_data) % 1000000)
elif 'cvId' in ctx_data:
    response = str(hash(cv_id) % 1000000)
else:
    response = str(random.randint(100000, 999999))
```

第二级几乎必然会走到，因为传给解释器的是 `js_context` 这种合成串，而 `js2py`、`nodejs`、`v8`、`chakracore` 四个入口的 `eval()` 都先过 `template()`，那个正则要求页面里有 `setTimeout(function(){…a.value=…toFixed(10);`——v3 的挑战页不提供这个形状。于是 `ValueError` 被抛出、被捕获，答案变成一个 `hash()` 取模得到的六位数哈希（散列）。

这里还有个环境层面的细节值得知道：Python 的 `hash()` 对字符串默认带随机盐（PYTHONHASHSEED），同一份页面数据在不同进程里会得到不同的兜底值。这不影响判断「它是猜的」，但影响复现。

所以 v3 这条线的真实语义是：**能识别 v3 页面、能完成一次表单往返，但没有针对 v3 虚拟机的求解实现**。README 说 v3 支持 js2py、nodejs、native 三种解释器「都能跑」，从代码上看不成立——它们跑的是同一条退让路径。

## Turnstile：把求解外包

`turnstile.py` 是四条线里最诚实的一条：它不尝试自己解。

`handle_Turnstile_Challenge`（第 117 行）第一件事就是检查 `cloudscraper.captcha` 里有没有 `provider`，没有就抛 `CloudflareTurnstileError("Cloudflare Turnstile detected, but no captcha provider configured")`。有则提取站点密钥，交给 `solveCaptcha('turnstile', …)`，把返回的令牌填进 `cf-turnstile-response`，再 POST 回表单 action。

配合的服务商在 `cloudscraper/captcha/` 下共 6 个模块：`2captcha`、`9kw`、`anticaptcha`、`capmonster`、`capsolver`、`deathbycaptcha`。README 还多列了一个 `__return_response__`，代码里对应的判法是 `captcha['provider'] == 'return_response'`（`cloudflare.py:364`）——它不解码，只把原始响应还给你，用途是喂给浏览器扩展或其他解码端。

配置形状是 `captcha={'provider': '2captcha', 'api_key': '…'}`，`api_key` 缺失时服务商模块会直接报错。这条路径的成本是每次求解一单的现金，与 CPU 无关。

## 一次请求在增强版里的完整顺序

把上面的零件串起来。`CloudScraper.request()`（`__init__.py:295`）覆写了 `requests.Session.request`，一次调用的实际顺序是：

1. `_apply_request_throttling()`：距上次请求不足 `min_request_interval` 就补足睡眠；若 `current_concurrent_requests` 已达 `max_concurrent_requests`，进入每 0.1 秒一轮的等待循环。
2. `_rotate_tls_cipher_suite()`：按当前浏览器的套件列表换一组密码套件，换成功就重新 `mount` 一次 `https://` 适配器。
3. `_should_refresh_session()`：会话年龄超过 `session_refresh_interval`，或者 60 秒内出现过 403，就执行 `_refresh_session(url)`。
4. 代理分配：调用方没传 `proxies` 且代理池非空时，取一个挂上。
5. `enable_stealth` 为真则套用人机延迟、请求头随机化与浏览器怪癖。
6. 计数自增，执行 `requestPreHook`，然后才真正 `perform_request()`。
7. 网络异常（代理错误、连接错误）时把代理计入失败并**保证并发计数自减**，再抛出。
8. 响应回来后依次判 Turnstile、v3、v2、v1，命中即递归处理并返回。
9. 都没命中且不是重定向、状态码不在 429/503：解算深度计数归零，200 且不在重试中则 403 重试次数归零。
10. 状态码为 403 且 `auto_refresh_on_403`：未超 `max_403_retries` 就刷新会话并递归重发，超过则原样返回 403。

第 1 与第 3 步之间有一个相互作用值得单独看。`_should_refresh_session` 只要发现 60 秒内出现过 403 就返回 True。**任何一次 403 之后的 60 秒窗口内，每个请求都会先跑一遍会话刷新**，包括再发一次到站点根路径的探测请求。403 若来自 IP 被拒这类与会话无关的原因，这里就是在成倍放大流量。

## 增强版默认就开的那些旋钮

README 把节流、403 恢复、TLS 轮换写成「feature」，读起来像需要用户显式启用。实际默认值如下（全部来自 `__init__.py:162` 至 `:191`）：

| 参数 | 默认 | 行为 | 副作用 |
|------|------|------|--------|
| `min_request_interval` | 1.0 | 两次请求的最小间隔秒数 | 单会话硬上限 1 请求/秒 |
| `enable_stealth` | True | 启用整套隐蔽技术 | 又叠一层睡眠，见下 |
| `stealth_options.min_delay` / `max_delay` | 0.5 / 2.0（代码），README 写 1.0 / 5.0 | 人机间隔 | 与节流相加 |
| `rotate_tls_ciphers` | True | 每请求换一组密码套件 | 每请求重建 HTTPS 适配器与连接池 |
| `max_concurrent_requests` | 1 | 并发闸门 | 计数自减依赖异常分支 |
| `session_refresh_interval` | 3600 | 会话主动刷新周期 | 刷新含一次根路径探测 |
| `auto_refresh_on_403` | True | 403 自动恢复 | 最多 3 次递归重发 |
| `solveDepth` | 3 | 解算递归深度 | 超了抛 `CloudflareLoopProtection` |

于是「换个类名就能当 `requests` 用、没有额外代价」这句常见判断，在 master 上并不成立。真实开销：

- 节流和 stealth 是**两处独立睡眠，会叠加**。默认配置下每个请求至少 1.0 秒，再叠 `random.uniform(0.5, 2.0)`，且该随机数有 10% 概率乘 1.5、上限截到 10 秒。平均下来每个请求多等 2.3 秒左右，单会话吞吐在 0.43 请求/秒附近。
- 密码套件轮换会在每次换组时重新 `mount('https://', CipherSuiteAdapter(...))`。新建适配器意味着新建连接池，会话级的连接复用被丢掉，TLS 握手每请求重来一次。
- 隐蔽技术会重写请求头顺序，若你自己在 `headers` 里排好了顺序，会被覆盖。

这些开销不是 bug，是这套默认值选择站在「隐蔽」一边、把吞吐让出去的结果。批量抓取不受 Cloudflare 保护的接口时，显式关掉更划算：

```python
scraper = cloudscraper.create_scraper(
    min_request_interval=0.0,
    enable_stealth=False,
    rotate_tls_ciphers=False,
)
```

并发那条要看清边界：`current_concurrent_requests` 是裸整数自增，检查与自增之间没有锁，`max_concurrent_requests=1` 只保证「大多数时候串行」。多线程共享同一个 scraper 时不要把它当信号量用。

stealth 的三个子开关各自还有一层语义（`stealth.py`）：`human_like_delays` 会先跳过第一次请求的延迟；`randomize_headers` 随机挑选 `Accept` 与 `Accept-Language`，并有 50% 概率注入 `DNT: 1`；`browser_quirks` 按用户代理（User-Agent）里的 `Firefox/` 或 `Chrome/` 选一组 Chrome/Firefox 请求头顺序。三者默认全为 True。

## 生产配置示例

下面这套是面向长期任务、以稳定为先的完整示例。要点是**先关掉不需要的开销，再对需要的调参**，而不是把参数堆满。

```python
import cloudscraper

scraper = cloudscraper.create_scraper(
    interpreter='js2py',      # master 默认；1.2.71 要显式传
    browser='chrome',         # 固定 UA 族，减少头与套件的组合漂移
    enable_stealth=True,
    stealth_options={
        'min_delay': 1.0,
        'max_delay': 3.0,
        'human_like_delays': True,
        'randomize_headers': True,
        'browser_quirks': True,
    },
    min_request_interval=2.0,
    session_refresh_interval=1800,
    auto_refresh_on_403=True,
    max_403_retries=3,
    rotating_proxies=[
        'http://user:pass@proxy1.example.com:8080',
        'http://user:pass@proxy2.example.com:8080',
    ],
    proxy_options={'rotation_strategy': 'smart', 'ban_time': 300},
    debug=False,
)
```

`rotation_strategy` 有三个取值：`sequential`（默认，下标递增）、`random`、`smart`。`smart` 的选择函数是 `success / (success + failure + 0.1)` 取最大。这个式子对全新代理（成功与失败都是 0）算出来是 0，于是它会被排在哪怕只有一次成功记录的代理之后。冷启动阶段这种排序会让试探顺序看起来没有道理，池子越大越明显。

代理的封禁逻辑是：`ProxyError` 或 `ConnectionError` 即把该代理写入 `banned_proxies`，`ban_time` 秒内不再选；全部被封时取「最早被封」的那个并立即解封。**403 不算代理失败**，所以换 IP 的速度取决于网络错误，不取决于被拒。

若你只需要 HTTP 代理，传纯 `host:port` 也可以——`ProxyManager` 会给无前缀的条目补上 `http://`。但 SOCKS 不能省前缀，`socks5://…` 会被那套补全规则拼成 `http://socks5://…`。

要提吞吐量，正确做法是多进程各持一个会话，而不是在单会话里堆线程：节流状态、解算深度计数、403 重试计数都是会话级可变状态。

## get_tokens 返回的是两个值

想只把解算结果拿给别的客户端用，接口是 `get_tokens` 与 `get_cookie_string`。这里的常见写法错误来自 README 自己也语焉不详：两个函数返回的都是**二元组**，第二个元素是本次解算所用的用户代理字符串（`__init__.py:701`、`:785`）。

```python
cookies, user_agent = cloudscraper.get_tokens('https://example.com')
cookie_string, user_agent = cloudscraper.get_cookie_string('https://example.com')
```

`get_tokens` 会 `raise_for_status()`，非 2xx 直接抛；随后从会话里挑出 `cf_clearance`、`cf_chl_2`、`cf_chl_prog`、`cf_chl_rc_ni`、`cf_turnstile` 中实际存在的项组成字典，域名匹配要求是站点根域或其点号前缀形式，找不到就抛 `CloudflareIUAMError`。`get_cookie_string` 只是把字典拼成 `k=v; k=v` 再原样带上用户代理。

为什么必须把用户代理一起带走：`cf_clearance` 与生成它的 TLS 与用户代理特征是绑定的，只把 cookie 塞进另一个客户端、请求头里的用户代理不同，服务端会判为不匹配。这也是这两个函数把两者打包返回的原因。

另外，这两个函数是类方法，内部会 `create_scraper()` 新建会话（`__init__.py:716`），不复用你手上那个实例的 cookie 与状态。想复用已有会话，直接读 `scraper.cookies`。

`create_scraper` 还能接受一个已有会话：

```python
scraper = cloudscraper.create_scraper(sess=existing_requests_session)
```

它会从传入对象搬 `auth`、`cert`、`cookies`、`headers`、`hooks`、`params`、`proxies`、`data` 这八个属性（`__init__.py:689`），其余不搬。README 也直说这里「不是所有属性都能顺利迁移」，遇到奇怪行为就把源头会话直接换成 `cloudscraper.create_scraper()`。

## 指纹素材的实际质量

`rotate_tls_ciphers=True` 的注释容易让人以为手里有若干套现成的浏览器指纹在轮播。实际数据量比这小，而且来源很旧。

密码套件列表读自 `cloudscraper/user_agent/browsers.json` 的 `cipherSuite` 字段：chrome 16 条、firefox 18 条。轮换逻辑（`__init__.py:602`）是取 `min(8, 列表长度)` 作为一个窗口，每请求把窗口起点往后挪一位，截出的片段用 `:` 连起来喂给 `SSLContext.set_ciphers`。所谓「轮换」，是在同一份固定列表上做滑动窗口截取，而不是在 8 套预设指纹之间切换。

这带来两个后果。其一，窗口内成员顺序恒定（沿用列表原序），变化的是子集；TLS 密码套件顺序正是 JA3 指纹的输入之一，一个既不属于 Chrome 也不属于 Firefox 的子集，产出的哈希只会是一个浏览器不会产生的值。其二，两处会让它静默失效：`CipherSuiteAdapter.__init__` 只在 `ssl_context` 为空时才调 `set_ciphers`，所以调用方自传 `ssl_context` 时换组结果被完全忽略，而适配器照样重建、连接池照样丢；`set_ciphers` 若因 OpenSSL 编译选项拒绝某个套件，异常被整段 `except Exception` 吞掉，只在 `debug=True` 下留一行「TLS cipher rotation failed」。

`CipherSuiteAdapter` 能碰到的旋钮一共四个：TLS 版本区间（写死 1.2 到 1.3）、`set_ciphers`、`set_ecdh_curve('prime256v1')`、以及 `source_address`。扩展列表、支持版本压缩算法这些 ClientHello 字段由 OpenSSL 决定，Python 侧无法重排；HTTP/2 的帧与头部顺序则根本不在 `requests` 这一层。所以它做的是 SSL 上下文参数定制，不是复现浏览器握手。

用户代理池的问题更直接。`browsers.json` 里有 7,822 条 UA 字符串，Chrome 版本号去重后 515 个，最高 76.0.3788.1；Firefox 34 个，最高 68.0。这是一份停在 2019 年年中的数据集，而它在 1.2.71 与今天的 master 之间一个字节都没变。UA 的挑选过程（`user_agent/__init__.py:52`）是从 5 个平台里随机取一个，再随机取 chrome 或 firefox，从对应列表里随机抽一条，并套用该浏览器的请求头顺序。

所以随机化本身带来一层反向效果：抽到的很可能是已经没有真实用户在用的版本组合。若目标站点只看 UA 新旧，这是噪声；若它做浏览器指纹一致性校验，UA 与 TLS 层的错配反而是显眼的信号。

## 通过率：这组数字测的是什么，不能推出什么

README 有六个条目写着 100%：基础请求、UA 处理、v1、v2、v3、stealth。要正确读它，得看 `tests/` 里到底有什么。

`tests/__init__.py` 提供了一个 `mockCloudflare` 装饰器：用 `responses` 库把请求拦在本地，按测试夹具（fixture）文件名决定返回 503 还是 403，再把 POST 载荷与期望比对。`tests/fixtures/` 下六个 HTML 存档，文件名里带的日期最晚的是 2021-07-01，其余落在 2019-12 与 2020-05。

而 `tests/test_modern.py` 里 18 个用例，没有一个 import 这个装饰器。它测的是：默认参数装配、UA 与浏览器挑选、会话健康字段、stealth 开关、代理管理器、403 处理（用 `Mock()` 这个模拟对象造一个 status_code 为 403 的响应）、cookie 清理、模块版本号。真正发出网络的只有 `TestIntegration` 的两个用例，目标是 `httpbin.org`，且都包在 `try/except` 里，失败就 `pytest.skip`。

把这三层摊开，可以定出这组 100% 的准确含义。它测的是：在构造好的本地响应上，配置装配与 403 状态机这些代码路径会按预期执行；fixture 侧则是在 2019 至 2021 年的页面存档上，v1 的提取与提交仍然成立。它没有测：任何一次对真实 Cloudflare 端点的 v2、v3 或 Turnstile 往返。

不能推出的结论也就是 README 暗示的那个：今天能解的站点下周未必能解，而且「v3 挑战 100% 通过」与上文那条兜底路径不可能同时为真——如果提交的是 `random.randint(100000, 999999)`，通过与否就不由代码决定。另一个可查的读数是维护状态本身：36 个未关闭的议题与合并请求（GitHub 把两类合并在一个字段里报出），最近一次推送停在 2025-06-10。自报通过率与真实绕过率之间的差距，同时也体现在这条时间线上。

自报成功率要打折看是通用规则，这里额外有一层：能测到的东西恰好是不涉及远端算法的东西。

## 打包成可执行文件

README 用一整节宣称 v2.7.0 修好了 PyInstaller、cx_Freeze、auto-py-to-exe 三类产物的用户代理问题。代码里实际做的是一条三级回退（`user_agent/__init__.py:75` 起）：

1. 先按安装位置读 `cloudscraper/user_agent/browsers.json`。
2. 读不到时，若 `getattr(sys, 'frozen', False)` 为真，就去 `sys._MEIPASS` 下找 `cloudscraper/user_agent/browsers.json`；否则退到当前工作目录的 `browsers.json`。
3. 仍读不到才用硬编码集合。

第 3 级的大小与第 2 级的判断都需要说准。硬编码集合是 15 条 UA（README 称 70+），Chrome 和 Firefox 全部写 120 版，分布在 windows、linux、darwin、android、ios 五个平台。第 2 级里对 `sys._MEIPASS` 的访问没有属性保护——cx_Freeze 会设 `sys.frozen` 但不设 `_MEIPASS`，此时抛出的 `AttributeError` 不在 `except (FileNotFoundError, IOError)` 覆盖范围内，会一路抛出构造函数。被点名「已彻底修复」的三类工具里，代码实际覆盖到的只有 PyInstaller 系（auto-py-to-exe 底层即 PyInstaller）。

结论是别依赖回退：把数据库带进产物。

```bash
pyinstaller --add-data "cloudscraper/user_agent/browsers.json;cloudscraper/user_agent/" your_app.py
```

Windows 上 `--add-data` 的分隔符是 `;`，Linux 与 macOS 是 `:`。回退到硬编码集合的表现是行为退化而非崩溃：UA 仍按 `headers` 里的 chrome 或 firefox 二选一，密码套件只剩每个浏览器 6 条固定的 TLS 名，与真实浏览器的差距反而更大。

## 适用边界与替换方案

值得用的场景收敛得很窄：目标是 v1 那一类 `trace/jsch/` 页面、你已有 `requests` 代码、并且能接受 UA 池停在 2019 年。这个组合在 2026 年不算常见，但确实存在——不少老配置的 `I'm Under Attack Mode` 仍是这个形状，此时 cloudscraper 的改造成本仍是最低的。

| 场景 | 更合适的选择 | 理由 |
|------|-------------|------|
| 403 由 TLS/JA3 或 HTTP/2 指纹引起 | curl_cffi | 直接构造浏览器 ClientHello，不是重排密码套件子集 |
| v2/v3 或 Managed Challenge 页面 | FlareSolverr、Playwright | 需要真实浏览器执行虚拟机里的载荷，库内没有这条实现 |
| 只要 `cf_clearance` 给别处用 | 保留 cloudscraper + 正确解包 | 它确实把解算做完了，且返回配套用户代理 |
| 需要绕过 Turnstile 交互 | 任一验证码求解服务商 | 库本身不解，只对接 |
| 目标站点叠加行为分析与设备指纹 | 人工或专业风控方案 | 代码层不具备这类信号 |

判断该走哪条，有一个不依赖直觉的次序：

1. 先拿到一次被拦的原始响应，看状态码是 403、429 还是 503，页面里有没有 `trace/`、`orchestrate/jsch/v1`、`orchestrate/jsch/v3`、`cf-turnstile` 这四组特征之一。这一步决定是不是 v1，也就决定 cloudscraper 是否有用。
2. 是 v1 就直接试，默认配置足够；不是 v1 就换浏览器方案，别在这里调参数。
3. 确认能拿到 200 与正文之后，再考虑要不要 Stealth、节流与 403 恢复。
4. 长期任务里出现间歇 403 才加会话参数；`session_refresh_interval` 调小会提高刷新频率，同时也提高被观测到的请求量。

参数不是堆得越多越稳。上面那条刷新与 403 的相互作用就是反例：默认配置的自愈机制一旦归因错了，会把一个问题放大成一轮流量。

合规这一层不因为工具开源而消失。只对你拥有或获得授权的站点使用，遵守目标站点的 `robots.txt` 与服务条款；未经授权抓取受版权保护或明确禁止自动访问的内容，可能构成违约或侵权。Cloudflare 的挑战是站点所有者设置的安全控制，本文读它的源码是为了理解工具的行为边界，不构成绕过他人访问控制的建议。

## 排查：常见故障按异常类定位

`cloudscraper/exceptions.py` 里有 18 个异常类：10 个 `Cloudflare*`（其中 `CloudflareException` 是基类，实际抛出的是其余 9 个）与 8 个 `Captcha*`。排查可以先按类名定位到分支，不必从日志里猜。

| 现象 | 异常 | 成因与动作 |
|------|------|-----------|
| 页面里出现 `cf-error-code">1020` | `CloudflareCode1020` | IP 或地域被防火墙规则直接拒，与会话无关。换出口 IP，或判定该站点不适用 |
| `Unable to identify Cloudflare IUAM Javascript` | `ValueError` | 页面不是 v1 形状，`template()` 的正则未命中。这是判据问题，换解释器无效 |
| `Error trying to solve Cloudflare IUAM Javascript` | `CloudflareSolveError` | 解释器执行完但结果转不成浮点数，即引擎求值不准。v1 页面可试 `interpreter='nodejs'` 或 `native` |
| 提交后仍反复回 503，最终抛 `!!Loop Protection!!` | `CloudflareLoopProtection` | 答案被服务端拒收，同一请求连续解算达到 `solveDepth`（默认 3）。此时先回到上面的判据分类，确认页面到底是不是 v1 |
| 抛「此功能不在开源版本里」 | `CloudflareChallengeError` | 你用的是 1.2.71，页面是 v2。要么换 master，要么换浏览器方案 |
| 出现 `cf_clearance` 却仍被拦 | 无异常 | 用户代理或 TLS 特征与解算时不一致。用 `get_tokens` 返回的第二个值 |
| Turnstile 页面报错 | `CloudflareTurnstileError` | 未配 `captcha['provider']`。接服务商，或改走浏览器方案 |
| 长时间稳定后整体 403 | 无异常 | 先看是否落在「403 后 60 秒每请求都刷新」的放大里，再判断 IP 层面 |

「一直 403，参数都试过了」这一类，最常见的两类根因是上表第 1 行与第 5 行：IP 或规则层被直接拒绝，以及版本装错。前者换会话参数不会有任何变化，后者只要看一眼 `cloudscraper.__version__` 就能定案。

## 自测清单

读完之后，下面五件事应能直接回答：

1. 传 `interpreter='nodejs'` 之后 v3 挑战页面仍未解算，为什么这与解释器无关？
2. 单会话跑一个不受保护的接口，默认配置下大概多少请求每秒，两处睡眠分别来自哪个参数？
3. `cloudscraper.get_tokens(url)` 的返回值形状是什么，第二个值为什么不能丢？
4. 用 `rotation_strategy='smart'` 冷启动，为什么一个全新代理会被排后面？
5. 目标站点返回 403 且页面里有 `orchestrate/jsch/v1`，你装的 master 会走哪个函数，提交的载荷里 `h-captcha-response` 是什么？

答案分别在前面的「解释器：五个入口，一条模板」「增强版默认就开的那些旋钮」「get_tokens 返回的是两个值」「生产配置示例」「v2」五节里，都能在源码对应行号上验证。

## 下一步读哪份代码

如果只为决策：先读 `cloudscraper/__init__.py:295` 的 `request()`，它是全部行为的路由表，一百行内能看清哪些请求会走哪条分支。

如果要动手改：`interpreters/encapsulated.py` 只有 62 行，但它是整个解算体系的咽喉——`template()` 那条正则决定了这个库能接哪种页面。想让 v3 真的可解，需要替换的是这一层的抽象（从「提取 v1 载荷」变成「驱动一个 JS 虚拟机」），而不是给解释器加参数。

如果目标是找替代：先读 curl_cffi 的 TLS 指纹实现，它处理的是这一层最容易被忽略的部分，即 ClientHello 构造。

如果只想确认自己的环境没有先天问题：`python -m cloudscraper.help` 会打印一段 JSON，字段是 platform、interpreter、cloudscraper、requests、urllib3 与 OpenSSL（含可用密码套件列表）。另外 `__init__.py` 在导入时就检查 `ssl.OPENSSL_VERSION_INFO < (1,1,1)`，命中则打印一条 DEPRECATION，提示当前 OpenSSL 不支持 Cloudflare 需要的 TLS 1.3。

## 参考

- 仓库与源码：[VeNoMouS/cloudscraper](https://github.com/VeNoMouS/cloudscraper)（`master` @ `9ea528a`）
- [README.md](https://github.com/VeNoMouS/cloudscraper/blob/master/README.md)、[CHANGELOG.md](https://github.com/VeNoMouS/cloudscraper/blob/master/CHANGELOG.md)、[PRODUCTION_READY_SUMMARY.md](https://github.com/VeNoMouS/cloudscraper/blob/master/PRODUCTION_READY_SUMMARY.md)
- [PyPI: cloudscraper 1.2.71](https://pypi.org/project/cloudscraper/)
- 解释器依赖：[Js2Py](https://github.com/PiotrDabkowski/Js2Py)、[v8eval](https://github.com/sony/v8eval)、[chakra-core/ChakraCore](https://github.com/chakra-core/ChakraCore)（README 里仍写作 `microsoft/ChakraCore`，该路径已 301 跳转）
- 替代方案：[curl_cffi](https://github.com/lexiforest/curl_cffi)、[FlareSolverr](https://github.com/FlareSolverr/FlareSolverr)、[Playwright](https://playwright.dev/python/)
