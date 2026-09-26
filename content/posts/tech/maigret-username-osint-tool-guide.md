---
title: "Maigret 拆解：难点不在发请求，而在让 5203 条会过期的断言保持可用"
date: "2026-04-30T10:07:02+08:00"
lastmod: "2026-09-20T00:00:00+08:00"
slug: "maigret-username-osint-tool-guide"
github_repo: "soxoj/maigret"
source_key: "gh:soxoj/maigret"
description: "对着 soxoj/maigret 0.6.6 的源码、data.json 与 sites.md 逐条核查后拆解它：用户名存在性检查为什么不是一个请求问题而是一个知识库维护问题，22 个引擎如何分摊 5897 条站点条目，58.58% 的弱信号检查怎样决定误报率，递归为什么没有深度参数，以及哪些调查场景应该直接换手段。"
draft: false
categories: ["技术笔记"]
tags: ["OSINT", "Python", "开源工具", "架构分析", "开源项目解读"]
---

> **判断**：用户名枚举在表面上是一个网络问题——构造 URL、发请求、看返回。Maigret 的实际工程量不在这里，而在第二件事：让五千多条「某个站点上 X 意味着账户存在」的断言长期保持可用。下面三件事决定了它的全部结构——站点知识如何压缩存储（引擎继承）、单次检查的可信度有多高（检查类型分布）、断言失效后如何被发现（自动更新与自检）。README 里那句 "site checks break over time and need active maintenance" 不是免责声明。它就是这个项目存在的形式。
>
> **读完后能做什么**：说清 Maigret 与 Sherlock 的分工差异从哪来；判断一次 `-a` 全量扫描里有多少结果是弱信号撑起来的；解释递归为什么不需要深度参数、又为什么可能收不住；把库嵌进自己的 Python 代码而不踩到空数据库那个坑；以及哪些调查目标应该直接换手段而不是调参数。
>
> **依据**：[soxoj/maigret](https://github.com/soxoj/maigret) `main@0be8038`（末次提交 2026-09-19），PyPI 最新 0.6.6（2026-09-18 发布）。GitHub API（应用程序接口）在 2026-09-20 读到 37,804 stars / 2,973 forks / 63 open issues，仓库创建于 2020-06-27，MIT 许可证。站点统计出自 `maigret/resources/data.json` 与由它生成的 `sites.md`（2026-09-17 更新），参数与默认值出自 `maigret/maigret.py`、`maigret/sites.py`、`maigret/resources/settings.json` 逐条对照，运维结论出自 `TROUBLESHOOTING.md` 与 `docs/source/`。

## 目录

- [先把三条主线分开](#先把三条主线分开)
- [站点知识库：5897 条条目压成 22 个模板](#站点知识库5897-条条目压成-22-个模板)
- [置信度写在检查类型里](#置信度写在检查类型里)
- [一次搜索在系统里怎么走](#一次搜索在系统里怎么走)
- [断言会过期：自动更新与自检](#断言会过期自动更新与自检)
- [上手：装、跑、出报告](#上手装跑出报告)
- [嵌进 Python：正确的调用姿势](#嵌进-python正确的调用姿势)
- [常见故障按现象分类](#常见故障按现象分类)
- [什么时候不该用它](#什么时候不该用它)
- [采用的顺序](#采用的顺序)
- [五道自测题](#五道自测题)
- [下一步读哪份代码](#下一步读哪份代码)
- [参考](#参考)

## 先把三条主线分开

Maigret 收集一个人的公开身份痕迹：只给一个用户名，它去大量站点上查这个用户名是否被占用，占用就把页面上能机器抽取的字段一并取回来。项目的自我定位写在 `docs/source/philosophy.rst` 里——"Username => Dossier"。抽取目标包括其他用户名、真实姓名、头像链接、生日、所在地区、性别，每个字段带固定标签名（`follower_count`、`created_at`），好让结果能被下游系统解析入库。

名字来自 Georges Simenon 笔下的法国警探 Jules Maigret，这位警司靠「理解人的性格与彼此的关系」办案，而不是物证。这一层不是装饰：它对应了工具与 Sherlock 一类纯枚举器的实际分野——Maigret 把「找到账户」当成管道中段而不是终点。仓库自己的说明也承认这层血缘：**Maigret 起步于 Sherlock 的一个 fork（派生版本）**，`philosophy.rst` 的原话是后来在覆盖面、抽取深度和检查可靠性三方面都超出了原项目。

读这套代码时容易混淆的是把三条并行主线讲成一条。它们各自的职责、数据结构和失效模式都不同：

| 主线 | 负责什么 | 主要载体 | 失效方式 |
|------|----------|----------|----------|
| 站点知识库 | 记住「在 X 站点，用户名怎么拼进 URL、什么响应算存在」 | `resources/data.json`（5897 条目 + 22 个引擎模板） | 站点改版、加了反爬，断言静默变假 |
| 检查执行 | 并发发出请求并把响应判成四种状态之一 | `checking.py` 的 7 个 checker 类 + `sites.py` 的判定 | 网络出口被 WAF（Web 应用防火墙）拉黑，判定整体失真 |
| 身份扩展 | 把一次结果里的新标识符推回队列再查一轮 | `maigret.py` 的工作队列 + socid_extractor | 同名不同人，扩散出一堆无关账户 |

三条线各自还带一套配套机制：知识库有自动更新与自检，检查执行有代理与重试，身份扩展有去重与 ID 类型过滤。下面按这个顺序展开。

## 站点知识库：5897 条条目压成 22 个模板

`maigret/resources/data.json` 只有三个顶层键：`sites`、`engines`、`tags`。2026-09-17 生成的 `sites.md` 给出的口径是 **5897 个条目，其中 5203 个启用**（88.23%），剩下 694 个被标记禁用。README 与仓库描述里那句 "3000+ sites" 已经滞后于数据库。0.6.6 的 CHANGELOG 记得很明确：启用数从 0.6.5 的 2611 涨到 5203。引用这个项目的数字时最好说明取的是条目数还是启用数，两者差 694。

关键在于**这 5897 条不是 5897 份手写规则**。按站点条目实际携带的 `engine` 字段统计：

| 引擎 | 覆盖站点数 | 引擎提供的字段 |
|------|-----------|----------------|
| `DiscourseJson` | 1232 | `checkType: status_code`、`url: {urlMain}/u/{username}`、`urlProbe: {urlMain}/u/{username}.json` |
| `uCoz` | 709 | 索引页 URL 模板与标记 |
| `XenForo` | 337 | `/members/?username=` 模板 |
| `MediaWikiJson` | 222 | API 查询式判定 |
| `Lemmy` | 143 | `/u/{username}` |
| `vBulletin` | 132 | 搜索式判定 |
| `phpBB/Search` | 126 | `search.php?author=` |

余下还有 `Discourse`、`MediaWiki`、`Flarum`、`Mastodon`、`Vanilla`、`Wordpress/Author`、`engine404` 等，合计 **3424 个条目（58%）继承引擎，2473 个条目自带完整规则**。`engines` 段一共定义了 23 个模板，其中 22 个被实际引用，`engine404message` 悬空未用——模板表本身也需要清理。

继承的省法很直观。`discourse.mozilla.org` 在 `data.json` 里的全部内容就是五个字段：

```json
{
  "urlMain": "https://discourse.mozilla.org",
  "engine": "DiscourseJson",
  "usernameClaimed": "adamlui",
  "usernameUnclaimed": "noonewouldeverusethis7",
  "tags": ["discussion", "forum", "tech"]
}
```

URL 怎么拼、按状态码还是按文本判存在、探测地址是什么，全部由引擎补上。给一个新 Discourse 论坛加支持不需要写任何检测逻辑，这解释了为什么这个库能在几个月里翻倍。

`maigret/sites.py` 里 `update_from_engine()` 处理冲突的方式值得看一眼：站点自己写过的字段优先于引擎值，并且会在加载时打一条 `Site %s overrides engine %s field %s` 的调试日志；`strip_engine_data()` 在保存时把与引擎一致的值从条目里剔掉，避免模板改动被固化成五千份副本。实测全库只有 **46 个引擎站点覆盖了自己的 `checkType` 或 `url`**——例外存在，但被刻意压在很小的量级。

`tags` 则是第三种复用。它同时装主题标签、国家码和引擎名：`forum` 2971、`discussion` 1991、`social` 803、`wiki` 591、`tech` 522、`gaming` 518、`coding` 332。国家维度合计 77 个标签被用到，另有 3373 个条目（57.2%）不带国家标签。这个缺失是有意设计的：`docs/source/tags.rst` 写明 GitHub、YouTube、Reddit 这类全球站点「有账号说明不了人在哪」，所以不该打国家标签。带标签最多的是 `ru`（1398），其次 `de`（131）、`ua`（126）、`us`（115）、`cn`（48）。

因为 `ranked_sites_dict()` 的过滤函数把引擎名也当标签匹配（`is_engine_ok`），`--tags ucoz` 和 `--tags coding` 是同一套语法的两种命中路径。

## 置信度写在检查类型里

站点条目最终解析出的判定方式只有三种。对 5203 个启用站点统计：

| 检查类型 | 数量 | 占比 | 判定依据 |
|----------|------|------|----------|
| `status_code` | 2669 | 51.3% | 只看 HTTP 状态码 |
| `message` | 2457 | 47.22% | 页面文本里找存在/不存在标记串 |
| `response_url` | 77 | 1.48% | 看最终跳转地址 |

`sites.md` 还给出一个更该被记住的合并指标：**弱信号检查 3048/5203 = 58.58%**。口径是「仅凭状态码判定」，再加上「文本检查缺一侧标记串」的那两类——缺存在串的 379 个，只剩缺席串可依赖的 242 个。

这组数字决定了误报率的下限。只看状态码的站点，服务器返回一个自定义 200 页面就算存在；文本检查缺存在串的站点，靠「没出现 404 字样」反推账户存在。也就是说，一次全量扫描里过半结论不是由账户证据支撑的，而是由「没有反证」支撑的。默认只扫排名前 500 个站点这件事，除了省时间，实质是把结论压在检测配置相对更严的高流量站点上。

顺带说明排名来源：字段名是 `alexa_rank`，属于历史遗留命名，`sites.md` 末尾注明实际排名数据取自 Majestic Million 按域名的统计。

## 一次搜索在系统里怎么走

抽象机制放到一条真实命令里看更清楚。以官方文档中 `soxoj` 这一条为例：

```bash
python3 -m maigret soxoj --timeout 5
```

**第一步，选站点。** 参数解析之后从工作队列取出 `soxoj`，调用 `ranked_sites_dict(top=500, tags=[], excluded_tags=[], names=[], disabled=False, id_type="username")`：按标签/引擎/名称/ID 类型过滤，按排名排序，取前 500。

这里有个不显眼但影响结果完整性的设计——**镜像补挂**。排名切片会漏掉小站点，而 `source` 字段把一个站点标成另一个平台的镜像（例如 Instagram 的第三方查看器 Picuki）。当父平台进入前 500 名，镜像即使自身排名靠后也会被追加进扫描集；且父排名的候选池包含禁用条目，所以官方站点被禁用时镜像仍能入选。

**第二步，发请求。** 默认 100 并发（`-n`/`--max-connections`），单请求超时 30 秒。检查器不只有一个实现，`checking.py` 里是一组按能力分层的类：

| Checker | 用途 |
|---------|------|
| `CheckerBase` | 抽象基类，下面几个都从这里派生或替换它 |
| `SimpleAiohttpChecker` | 默认路径，直连 aiohttp |
| `ProxiedAiohttpChecker` | 走 `--proxy` 时替换 |
| `AiodnsDomainResolver` | 域名解析，另一条 `--dns-resolver` 可回退线程池 getaddrinfo |
| `CurlCffiChecker` | 伪造浏览器 TLS 指纹，对应库里 104 个 `tls_fingerprint` 站点 |
| `CloudflareWebgateChecker` | 把检查外包给本地 FlareSolverr，默认关闭 |
| `CheckerMock` | 测试替身 |

部分条目还带 `urlProbe` 探测地址，先探再判可以避开主站点的反爬。解析后共 1966 个站点配了探测地址，其中条目自己显式写的只有 172 个，其余由引擎补上——上面的 `DiscourseJson` 就顺手给 1232 个论坛都配了 `{urlMain}/u/{username}.json`，判定因此走 JSON 端点而不是解析 HTML。

**第三步，判状态。** 每个站点的结论落在四个值之一：`CLAIMED`（用户名被占）、`AVAILABLE`（未占用）、`UNKNOWN`（出错无法判断）、`ILLEGAL`（该站点不允许这种用户名，比如含被禁字符）。命中后 `is_found()` 返回真，socid_extractor 把页面字段抽成 `ids_data`。

**第四步，扩展。** 一次扫描结束后 `extract_ids_from_results()` 从结果里收集两样东西：`ids_usernames`（页面里抽出的别的用户名及其 ID 类型）和 `ids_links`（外链，再交给 `db.extract_ids_from_url()` 反解出平台 ID）。官方文档展示的真实效果是：GitHub 主页抽到 `twitter_username: sox0j`，队列里就多出一个 `sox0j`，第二轮扫描在 Telegram 上命中 `https://t.me/sox0j`。

**递归没有深度参数。** 循环体写的是 `while usernames:`——弹出队首、跑完整轮、把新标识符 `usernames.update(...)` 推回队列。收敛靠两个集合：`already_checked` 按小写用户名去重跳过，`--ignore-ids` 把已知无关的标识符排除。

控制成本的手段因此只有三类：缩小站点集（默认 500，或用 `--tags` 收窄）、从源头少抽标识符（`--no-extracting` 关掉页面解析，`--no-recursion` 只关扩散）、以及中途按 Ctrl+C。第一次中断只是停止从队列取新目标，已经跑完的结果仍会照常生成报告。

这也解释了扩散为什么会失控：队列长度不受参数约束，取决于目标在多少个平台上留下了可解析的标识符。同名不同人的账户会被一并带进来，这是它主要的噪声来源。

## 断言会过期：自动更新与自检

内置 `data.json` 是发版时的快照。`db_updater.py` 的做法是：每次运行去拉一个轻量元文件，判断是否要比本地新，再决定是否下载整库。元文件 `db_meta.json` 当前长这样：

```json
{
    "version": 1,
    "updated_at": "2026-09-17T09:37:44Z",
    "sites_count": 5897,
    "min_maigret_version": "0.5.0",
    "data_sha256": "ef6ca66efa174209c10205ff86f7e975b591128681710639fdc786ff05e662da",
    "data_url": "https://raw.githubusercontent.com/soxoj/maigret/main/maigret/resources/data.json"
}
```

三个细节值得照搬到自己的项目里：检查间隔默认 24 小时（`autoupdate_check_interval_hours`），下载后校验 SHA-256，`min_maigret_version` 用来拒绝本地代码读不懂的新库。下载库缓存在 `~/.maigret/data.json`，状态记在 `~/.maigret/autoupdate_state.json`。离线或下载失败时回退到包内快照——`maigret/maigret.py` 里那层 `try/except` 会打印 "Falling back to bundled database"。`--no-autoupdate` 关掉整个机制，`--force-update` 立刻强制刷新。

**失效怎么被发现。** 每个站点条目都带一对哨兵用户名：上面例子里的 `usernameClaimed: adamlui` 和 `usernameUnclaimed: noonewouldeverusethis7`。`--self-check` 就是拿这两个已知答案去跑真实站点，看判定是否仍与预期一致；`--auto-disable` 让不通过的条目自动置为禁用，`--diagnose` 打印每处失败的检查类型与建议。单个站点抛异常不会中断整轮，错误被记录后继续跑，所以 `maigret -a --self-check` 能一次过五千多个站点。

这套哨兵机制也解释了 CHANGELOG 里 `[LAPOINTE] Add N sites` 与 `Fixes of false positives` 这类提交为什么高频出现——维护工作的主体就是新增条目与修正失效断言两件事。0.6.6 里 "Stop reporting blocked LinkedIn responses as free usernames" 是一条典型的误报修复。

**反爬的真实边界。** 库里 244 个条目带 `protection` 标记：`tls_fingerprint` 104、`cf_js_challenge` 57、`ip_reputation` 45、自定义 23、`cf_firewall` 15。需要真浏览器解 JS 挑战的那两类通常直接留在禁用状态，因为 aiohttp 和 curl_cffi 都过不去。想覆盖它们要显式开启 `--cloudflare-bypass`（默认 `cloudflare_bypass.enabled` 为 false），配一个本地 FlareSolverr 容器。这里有个容易踩的坑：官方推荐 FlareSolverr，因为它回传上游真实状态码和最终地址，`status_code` 与 `response_url` 两类检查仍能工作；另一个后备 CloudflareBypassForScraping 只返回渲染后的 HTML，状态码丢失，`status_code` 检查会一律当成 200 而误判。开启后同一域名会复用 FlareSolverr 会话共享 `cf_clearance`，官方文档说后续请求快 5–10 倍。

早期 PR #2308（2026-03-22 合并）走的是更朴素的路线：给 taplink.cc 换浏览器 `User-Agent` 以过 Cloudflare。个案补丁与通用绕过机制是两回事，前者解决一个站点，后者按 `protection` 标签整批路由。

还有一层比反爬更根本的机制是**认证态**。6 个站点配了 activation：OnlyFans、ProtonMail、Twitter、Vimeo、Weibo、WikimapiaSearch。命中特定错误后，由自定义函数去访问一个专用端点，拿回 cookies/JWT 写进本地库里该站点的配置。它默认开启且当前无法关闭，而且因为是在报错后才触发，通常需要重试或再跑一轮才能拿到有效响应。

## 上手：装、跑、出报告

Python 3.10 以上即可（`pyproject.toml` 声明 `python = "^3.10"`，分类器覆盖到 3.14），Linux/macOS/Windows 通用，核心功能无系统依赖。

```bash
pip install maigret
maigret YOUR_USERNAME
```

`command not found` 的话，二进制通常装在 `~/.local/bin`（Linux/macOS）或 `%APPDATA%\Python\Scripts`（Windows），把它加进 PATH，或者直接用 `python3 -m maigret` 这种形式。仓库同时文档化了 pipx、Linux Snap（`sudo snap install maigret`，amd64/arm64，不需要本机 Python）和 Windows standalone 可执行文件三种分发。

不想装任何东西也有路可走：社区维护的 Telegram bot（源码在 soxoj/maigret-tg-bot，官方文档提示实例可能换托管方）、Google Cloud Shell、Colab notebook。Docker 有两个镜像变体：

```bash
# CLI 模式，把宿主目录挂到容器内的报告目录
docker run -v /mydir:/app/reports soxoj/maigret:latest username --html

# Web UI 模式，浏览器打开 http://localhost:5000
docker run -p 5000:5000 soxoj/maigret:web

# 换端口
docker run -e PORT=8080 -p 8080:8080 soxoj/maigret:web
```

本地起 Web 界面用 `maigret --web`，不给端口时默认 5000。

几条常用命令：

```bash
maigret user                 # 默认：排名前 500 站点
maigret user -a              # 全部启用站点
maigret user --tags photo,dating
maigret user --exclude-tags ru          # 黑名单式排除
maigret user --tags forum --exclude-tags ru
maigret user1 user2 user3 -a            # 多个目标
maigret --permute hope dream            # 由词根生成用户名变体
maigret --parse https://steamcommunity.com/profiles/76561199113454789
maigret 10001 --id-type qq_id           # 按数字 ID 而非用户名查
maigret user -n 20 --timeout 60 --retries 2   # 降低并发、放宽超时
maigret user --print-errors            # 看每个站点为什么判失败
maigret -a --self-check --diagnose     # 逐站点体检，打印检查类型与建议
```

`--permute` 至少给两个词根才有意义，官方文档的例子里 `hope dream` 展开成 12 个候选（`hopedream`、`hope_dream`、`hope-dream`、`hope.dream` 及反序六种）。`--parse` 接受账户页也接受在线文档，文档里那个 Google 表格的例子会顺着 Drive 元数据端点取回 `fullname`、`email`、`gaia_id`，然后把 `email_username` 当新目标继续查——这是「从一个链接扩散成一份档案」的入口。

除用户名外还有 25 个条目按其他 ID 类型检索：`gaia_id`、`steam_id`、`vk_id`、`ok_id`、`yandex_public_id`、`qq_id`、`bilibili_id`、`orcid` 等（完整列表见 `docs/source/supported-identifier-types.rst`）。`--id-type` 用来指定查询的标识符类型，`type` 与之不符的站点会被跳过——`maigret 10001` 默认按 `username` 查，不会去问 QQ。

报告格式一次给足：

```bash
maigret user --html    # 带头像与字段表格的网页报告
maigret user --pdf     # 需要额外依赖，见下
maigret user --xmind   # 思维导图
maigret user --json ndjson
maigret user --csv
maigret user --txt
maigret user --md
maigret user --graph   # 交互式 HTML 关系图
maigret user --neo4j   # 幂等的 Cypher 脚本，可反复导入
```

JSON 有 `ndjson` 和 `simple` 两种排版；`--neo4j` 导出的 `.cypher` 可重复导入，适合把多轮调查结果累进同一个图库。HTML 与 PDF 报告除字段表外还会给一份「推测的个人信息」（姓名、性别、地区），依据是所有命中账户上的统计聚合。这部分是推断而非证据，看报告时要和直接抽取到的字段分开对待。XMind 那条 `-X` 的输出是 legacy XML，再加一份让新版阅读器能打开的 manifest；官方文档里另有一处「XMind 8 与 XMind 2022 不兼容」的旧警告尚未同步，以你手上的阅读器实测为准。

PDF 是可选扩展，默认不装的原因写得很具体：底层 `pycairo` 在 PyPI 上没有 Linux/macOS 的 wheel，需要系统 libcairo 加 pkg-config 现场编译。

```bash
pip install 'maigret[pdf]'
```

注意扩展名是 `pdf` 而不是 `full`，渲染走 xhtml2pdf（会连带装 arabic-reshaper 和 python-bidi 处理 RTL 文本），不涉及 WeasyPrint。

## 嵌进 Python：正确的调用姿势

CLI（命令行工具）只是异步函数的薄包装，官方导出在 `maigret/__init__.py` 里：`search`（即 `maigret.checking.maigret`）、`MaigretDatabase`、`MaigretSite`、`MaigretEngine`、`Notifier`。

这里有一个足以让人困惑半天的坑：**`MaigretDatabase()` 构造出来是空的**。它只是把 `_sites`/`_engines`/`_tags` 三个列表初始化成空，必须再 `load_from_path()` 才有内容；也没有 `get_all_sites()` 这个方法，过滤靠 `ranked_sites_dict()`。下面这份是按 0.6.6 源码写通的最小示例：

```python
import asyncio
import logging
import os

import maigret
from maigret import search as maigret_search
from maigret.sites import MaigretDatabase

# 用包内快照，避免依赖当前工作目录
BUNDLED_DB = os.path.join(os.path.dirname(maigret.__file__), "resources", "data.json")

db = MaigretDatabase().load_from_path(BUNDLED_DB)
sites = db.ranked_sites_dict(top=500)          # 与 CLI 默认同样的切片

results = asyncio.run(
    maigret_search(
        username="soxoj",
        site_dict=sites,
        logger=logging.getLogger("maigret"),
        timeout=30,
        is_parsing_enabled=True,   # 打开才会有 ids_data
    )
)

for site_name, result in results.items():
    if result["status"].is_found():
        print(site_name, result["url_user"], result.get("ids_data"))
```

`ranked_sites_dict()` 的过滤参数与 CLI 一一对应，可以直接表达「只看某引擎」「排除某类」：

```python
by_tag = db.ranked_sites_dict(top=200, tags=["coding"])
by_exclude = db.ranked_sites_dict(excluded_tags=["nsfw", "dating"])
by_name = db.ranked_sites_dict(names=["GitHub", "Reddit", "VK"])  # 名称或 URL 都行
with_disabled = db.ranked_sites_dict(disabled=True)
```

返回值是 `Dict[str, SiteResult]`，而 `SiteResult` 是 `TypedDict`——按键取值没问题，但它被设计成分三阶段填充的，所以要用对键名。检索阶段可依赖的是 `status`（带 `is_found()` 的对象）、`url_user`、`http_status`、`rank`、`ids_data`、`ids_usernames`、`ids_links`、`response_text`。注意两点：`found` 这个布尔键要到生成报告阶段才被写进去，直接查库时判断存在应当用 `result["status"].is_found()`；抽到的字段挂在 `ids_data` 上，不是 `extract_data`。

`maigret_search` 的关键字参数还包括 `proxy`、`tor_proxy`、`i2p_proxy`、`id_type`、`max_connections`、`retries`、`check_domains`、`cookies`、`keywords`、`cloudflare_bypass`、`output_container`，语义与同名 CLI 选项一致。已有事件循环（FastAPI、Discord bot）里直接 `await`，别再套 `asyncio.run`。

## 常见故障按现象分类

`TROUBLESHOOTING.md` 开篇就说这是收到最多的报告，而它的第一条建议不是调参数，是**换网络出口**。同一命令、同一目标，结果质量按出口差别很大。移动网络通常最好：运营商 NAT（网络地址转换）让一个 IP 后面跟着成千上万真实用户，WAF 不敢整段拉黑。家用宽带一般。云主机与 VPS 最差，数据中心网段被多数 WAF 整段处置，于是大量假阴性与 403。判断一次空结果是不是工具坏了，最快的办法是换一条网络重跑做对比。

确认出口没问题后，按顺序试：放宽超时（默认 30 秒，`--timeout 60`）、开启重试（`--retries 2`，默认 0 次）、降低并发（默认 100，`-n 20` 让它不像扫描器）、换住宅代理（`--proxy http://user:pass@host:port`）。注意最后一条与直觉相反：**Tor 在这里基本不帮忙**，多数 WAF 对出口节点的封锁强度不亚于数据中心 IP。`--tor-proxy`/`--i2p-proxy` 的用途是把 `.onion`/`.i2p` 站点路由到对应网关，不带这两个参数时暗网站点会被静默跳过；想让整轮都走 Tor（例如 Tails 上）用的是 `--proxy socks5://127.0.0.1:9050`，而网关本身要你自己起，Maigret 不负责管理。

其余几类现象：

- **个别站点永远失败。** 参数无关，多半是断言已失效（站点改版、换了 WAF、标记串过期）。用 `--print-errors` 取输出后提 issue，维护者要的就是这段。
- **结果比预期多。** 先看命中的是不是弱信号站点——51.3% 的启用站点只凭状态码判定，`--use-disabled-sites` 和 `--tags disabled` 会把帮助文档里明说「会产生很多误报」的条目也纳入。
- **SSL/证书错误。** 通常是企业 MITM 代理或 `certifi` 过期，`pip install --upgrade certifi`，并让 Maigret 走同一条路（`--proxy "$HTTPS_PROXY"`）。
- **装了扩展仍出不了 PDF。** `pycairo` 需要系统 libcairo 与 pkg-config，按 `docs/source/installation.rst` 的对应平台步骤装。
- **同类错误超过 3%。** 工具会主动打警告并给建议——这类错误一般来自网络审查的拦截占位页与验证码页，不是 bug。

## 什么时候不该用它

有些边界是机制本身决定的，调参数不能越过：

- **它不碰认证系统。** 只能看到未登录状态下公开可访问的内容。账号在登录墙后、或站点强制 JS 挑战且你没配 FlareSolverr，结论就是 UNKNOWN 而不是「不存在」。
- **它不认识「人」。** 判的是字符串是否被占用。同名账户会被一并带进递归结果，需要人工甄别，工具没有身份消歧能力。
- **它覆盖的是已知站点的集合。** 目标在小众或私有部署的平台上，数据库里没有条目就永远不会命中；`--submit URL` 是把它加进库的入口。
- **深度匿名性评估不适用。** 它无法发现「没有用这个用户名」的账户，也无法证明不存在。
- **不要用它做批量骚扰或人肉。** 项目的免责声明很短：仅用于教育与合法用途，GDPR/CCPA 等合规责任在使用者，作者对滥用不承担责任。

隐私面值得单独说清，因为「本地工具」这个说法容易被过度理解。`docs/source/privacy.rst` 的口径是：整个流程在你机器上跑，无遥测、无统计、不向维护者回传任何东西，报告只落本地文件。但要意识到两件事：其一，被搜索的用户名会作为 URL 的一部分发到每个被查站点——这本来就是检查的原理；其二，自动更新会让你的 IP 在 GitHub 的 raw 域名上留下记录，需要严格静默时加 `--no-autoupdate`。唯一涉及第三方的功能 `--ai` 是显式开关且要你自己的 key。

## 采用的顺序

如果你是安全/风控方向，关心的是暴露面：**先默认 500 站点跑一轮**，看命中分布与标签聚类，再对具体平台用 `-a` 或 `--tags` 定点确认，最后 `--html` 或 `--graph` 出可视化交付物。别一上来就 `-a`——全量扫描的误报率明显高于高流量切片，而 500 个站点的耗时在秒级。

如果你在建自己的调查工具链：**把 Maigret 当库用，而不是 subprocess 调 CLI**，重点是 `ranked_sites_dict` 的过滤能力和 `ids_data` 的结构化字段；需要图谱就把 `--neo4j` 的幂等 Cypher 接进图库。上游依赖 socid-extractor（2026-07-13 的 0.1.1）负责字段抽取，两个项目是分工而非替代关系。

如果你只需要一次性的「这个用户名还在哪些平台注册过」：Web 界面或 Docker 的 `:web` 变体够用，不必装 Python。但注意 `--web` 与 Render 一键部署的实例**默认不带任何鉴权**，谁拿到 URL 谁就能用，不要把它挂到公网当团队服务。

至于要不要为此付费：开源版本 MIT 许可、商用不设限。作者在售的是两件不同的东西——每天更新的私有站点库（自述 5000+ 站点）和 username-check API，联系 maigret@soxoj.com。判断依据很实在：你的场景能否接受断言按周失效。Social Links API、Social Links Crimewall 和 UserSearch 这几款商业产品都把它作为组件，可见维护频率对下游确实是硬约束。

## 五道自测题

**一、Maigret 与 Sherlock 的关系是什么，差异体现在哪一层？**

Maigret 起步于 Sherlock 的 fork，`philosophy.rst` 里直接写了这一句。差异不在「有没有递归」这种功能开关层面，而在定位：Sherlock 类工具把用户名存在性检测当终点，Maigret 把它当中段。配套动作是抽取结构化身份字段、把发现的 ID 推回队列继续扩散、输出可入库的关系图谱。官方列出的超出方向有三个：覆盖面、抽取深度、检查可靠性。

**二、为什么「支持 5897 个站点」和 README 里的「3000+」都对，但不该直接引用后者？**

5897 是 `data.json` 的条目数，5203 是其中启用的（694 个带 `disabled` 标记），而 "3000+" 是仓库描述与 README 沿用的概数。0.6.6 的 CHANGELOG 记录启用数从 2611 涨到 5203，说明概数已经明显滞后于数据库。引用时要区分条目数与启用数，并交代统计日期。

**三、为什么一次全量扫描的误报率天然偏高？有没有参数能改变这个下限？**

5203 个启用站点里 2669 个只用状态码判定，另有 379 个文本检查缺存在串，合并成弱信号占比 58.58%。这些站点把「没有反证」当成「账户存在」。没有任何参数能改变这个下限，因为它写死在数据库里——能改变的是选择哪一批站点：默认前 500 名切片、按标签收窄、或核对疑似结果时看它的 `check_type` 和 `http_status`。

**四、递归搜索没有深度参数，那它靠什么停下？成本怎么控？**

`while usernames:` 每次弹出一个目标跑完整轮，再把新抽到的标识符推回队列；终止条件是 `already_checked` 的去重让队列不再增长，以及 `--ignore-ids` 主动排除。控成本只有三条路：缩小站点集（默认 500、`--tags`/`--site`）、`--no-extracting` 或 `--no-recursion` 从源头减少扩散、第一次 Ctrl+C 中断后仍会基于已收集结果出报告。

**五、结果里出现一堆明显不属于目标的账户，是 bug 吗？**

不是。工具判的是字符串是否被占用，不做身份消歧，同名账户会被合法地检出，并可能再带出更多同名。可行的收敛办法有三种：用 `--tags` 限定领域、用 `--exclude-tags` 排除噪声类目、对可疑命中去查它的 `http_status` 与检查类型是不是弱信号。另一个实用信号是字段完整度——带完整 `ids_data`（头像、注册日期、地区彼此印证）的站点，比只报一个 URL 的站点可信得多。

## 下一步读哪份代码

按你的目的挑，不用按顺序：

| 想搞清 | 读 |
|--------|-----|
| 站点条目与引擎到底怎么组织 | `maigret/resources/data.json` 的 `engines` 段，以及 `maigret/sites.py` 的 `MaigretSite.update_from_engine` / `strip_engine_data` |
| 判定为什么误报 | `maigret/sites.py` 里 `check_type` 的四个分支，配合 `sites.md` 的 "Check strength" 一节 |
| 并发与反爬路径 | `maigret/checking.py` 的 Checker 类族，特别是 `CurlCffiChecker` 与 `CloudflareWebgateChecker` |
| 递归的确切边界 | `maigret/maigret.py` 的 `extract_ids_from_results` 与 `while usernames:` 那段循环 |
| 想给项目提 PR | `CONTRIBUTING.md`：要求直接改 `data.json`（不许 `json.load`/`json.dump` 往返），再跑 `./utils/update_site_data.py` 重新生成 `sites.md` 与元文件 |
| 自己维护一份库 | `--self-check --auto-disable` 的语义，以及 `db_updater.py` 的 sha256 与版本兼容检查 |

一句提醒：这个项目最有价值的资产不是 `maigret/` 包里那 8559 行 Python，而是带哨兵用户名、能被机器批量复检的五千多条站点断言。fork 一份代码容易，把断言维持在可用状态这件事没有捷径——这也是它和同类工具拉开差距的地方。

## 参考

- 仓库：https://github.com/soxoj/maigret
- 站点数据库与统计：https://github.com/soxoj/maigret/blob/main/sites.md
- 官方文档：https://maigret.readthedocs.io/ （`quick-start`、`installation`、`usage-examples`、`features`、`philosophy`、`privacy`、`supported-identifier-types`、`tags`、`command-line-options`、`library-usage`、`settings`、`tor-and-proxies`）
- 故障排查：https://github.com/soxoj/maigret/blob/main/TROUBLESHOOTING.md
- PyPI：https://pypi.org/project/maigret/
- 字段抽取上游库：https://github.com/soxoj/socid_extractor （文档 https://socid-extractor.readthedocs.io/ ）
- 社区 Telegram bot 源码：https://github.com/soxoj/maigret-tg-bot
- 作者关于用户名检查器的批评文章：What's wrong with namecheckers（https://soxoj.medium.com/whats-wrong-with-namecheckers-981e5cba600e ）
- 用户名检查工具横向清单：https://github.com/soxoj/osint-namecheckers-list
- SOWEL 方法分类：https://sowel.soxoj.com/other-platform-accounts
