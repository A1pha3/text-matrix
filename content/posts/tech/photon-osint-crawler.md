---
title: "Photon：极速 OSINT 爬虫——域名发现、敏感信息提取与情报收集指南"
date: "2026-04-14T22:35:00+08:00"
slug: "photon-osint-crawler"
github_repo: "s0md3v/Photon"
source_key: "gh:s0md3v/Photon"
description: "Photon 是 Somdev Sangwan 开发的 13.2K Stars 极速 OSINT 爬虫，专为安全研究员设计。支持 8 种数据提取（URL/参数/Intel/文件/密钥/JS 端点/正则/DNS），多线程并发，集成 Wayback Machine 和 DNSdumpster 插件，可导出 JSON/CSV。"
draft: false
categories: ["技术笔记"]
tags: ["安全", "OSINT", "爬虫", "BugBounty", "信息收集", "渗透测试"]
---

# Photon：极速 OSINT 爬虫——域名发现、敏感信息提取与情报收集指南

> **目标读者**：安全研究员、渗透测试工程师、Bug Bounty 猎人、对 OSINT 感兴趣的开发者
> **预计阅读时间**：25-35 分钟
> **前置知识**：Python 基础、HTTP 协议、网络爬虫概念
> **难度定位**：⭐⭐⭐ 进阶

---

## §1 这是什么工具，能帮你做什么

在渗透测试或 Bug Bounty 的侦察阶段，你需要尽可能多地了解目标暴露了什么。手工一个个页面点开看效率太低，通用爬虫又太重、太慢。Photon 就是为这个场景而生的——它不渲染页面、不做内容分析，只抓安全研究人员关心的那几类结构化信息。

**一句话定位**：极速、轻量、只取目标数据的 OSINT 专用爬虫。

它能帮你回答这类问题：

- 目标域名下有哪些页面？哪些带参数？
- 公开页面里藏了哪些邮箱、IP、哈希、信用卡号？
- 目标的 JavaScript 文件里埋了哪些后端端点？
- Wayback Machine 最近半年存档了哪些 URL？
- 目标的子域名和 DNS 数据长什么样？

**关键事实**（2026-09-12 对照 GitHub 核实）

| 项目 | 值 |
|------|-----|
| GitHub Stars | 13,199 |
| 作者 | Somdev Sangwan（s0md3v） |
| 语言 | Python 3（3.2+） |
| 许可证 | GPL v3.0 |
| 版本 | master 为 v1.3.2；最新 release 标签 v1.3.0（2019 年 4 月） |
| 实质代码最后提交 | 2019 年 4 月（此后仓库只有 README 层面的微调） |
| 依赖 | requests、requests[socks]、urllib3、tld |
| 代码量 | 约 1,200 行 Python（主模块 + core + plugins） |
| Docker 镜像 | 103 MB（官方 README 数据，基于 python:3-alpine） |

有一件事必须先说清楚：这个项目从 2019 年起就没有实质性的代码更新了。功能已经稳定、也确实够用，但遇到 bug 别指望修复，新特性更不会有。它适合当作一把"够用的旧工具"来用，不适合长期押注。本文所有描述均以 master 分支（v1.3.2）的源码为准。

---

## §2 设计取向：为什么通用爬虫做不好这件事

### 2.1 通用爬虫 vs OSINT 爬虫

通用爬虫（Scrapy、Crawlee 等）的设计目标是"把整个网站的内容抓下来存好"。OSINT 爬虫的目标是"尽快找出目标暴露了什么"。这两个方向几乎是反着来的。

| 维度 | 通用爬虫 | Photon（OSINT） |
|------|----------|-----------------|
| 页面渲染 | 通常构建 DOM 树，部分场景执行 JS | 不渲染，整页文本直接跑正则 |
| 关注点 | 全文抓取、结构化存储 | URL、参数、情报字段、密钥等 |
| 内存占用 | 高（存储大量页面内容） | 低（只存提取出的字段） |
| 去重策略 | URL 去重 | 11 类数据各自用 `set` 去重 |
| 速度瓶颈 | DOM 解析、内容编码 | 网络 I/O（靠多线程摊薄） |
| 输出形式 | 数据库/文件系统批量存储 | 按类型分文件（internal.txt、intel.txt、keys.txt…） |

### 2.2 Photon 的三个核心设计决策

**跳过渲染，整页文本跑正则**。HTML 和 JavaScript 里的信息够用了，OSINT 场景不需要看到页面长什么样。这让内存占用降到很低，启动几乎是瞬时的。

**广度优先 + 可配置深度**。默认爬 2 层——从主页拿到的内部链接是第 1 层，第 1 层页面里发现的链接再爬一遍是第 2 层。安全研究里 2 层通常足够覆盖大部分入口点，更深会带来指数级的请求量。

**只收 text/html 和 text/plain**。请求器会检查响应头的 content-type，不是这两种的（图片、PDF、JSON 接口）直接丢弃。所以 Photon 自始至终只保存文本和提取结果——files.txt 里记的是 URL，而不是文件本身。

---

## §3 8 种数据提取能力

README 官方口径是 8 类提取。下面逐一说明提取逻辑和落盘位置，全部对照源码核实过。

### 3.1 URLs（站内 & 站外）

URL 提取只认 `<a href>`。表单的 `action`、图片的 `src` 都不在范围内——脚本文件走 `<script src>` 那条线（见 3.6）。提取时会去掉 `#` 锚点，相对链接会拼上当前页面路径变成完整 URL。

```text
# 输入页面片段
<a href="/admin/login">登录</a>
<a href="https://partner.example.net/">合作伙伴</a>

# 提取结果
internal.txt        https://target.com/admin/login
external.txt        https://partner.example.net/
```

区分站内和站外是有用的：站内 URL 意味着可能还能继续爬，站外 URL 通常只是引用。

### 3.2 URLs with parameters（带参数的 URL）

判定规则很简单：站内 URL 里含 `=` 号就算，存入 fuzzable.txt。这类 URL 往往对应动态页面，是注入、XSS 等漏洞的高概率入口，后续可以交给 fuzzer 做参数爆破。

```text
https://example.com/gallery.php?id=2&sort=asc
```

### 3.3 Intel（情报类字段）

v1.3.1 起，Intel 的实现整体换成了 [InQuest/python-iocextract](https://github.com/InQuest/python-iocextract) 的 IOC（失陷指标）正则集，共 15 类。注意：README 里"social media accounts、amazon buckets"的描述是旧版口径，现行代码里已经没有对应的正则了。

| 类别 | 识别内容 |
|------|----------|
| URL（6 种形态） | 普通链接、混淆变形（`hxxp://example[.]com` 这类 defang 写法）、反斜杠变形、十六进制编码、URL 编码、base64 编码 |
| IP 地址 | IPv4 / IPv6 |
| 邮箱 | 含 `admin[at]example[dot]com` 这类防爬变形 |
| 哈希 | MD5、SHA1、SHA256、SHA512 |
| YARA 规则 | 页面里内嵌的完整 YARA rule 块 |
| 信用卡 | 16 位卡号，过 Luhn 校验才会保留（排除凑数的串） |

intel.txt 里多数条目长这样——情报值和发现它的页面绑在一起，方便回溯：

```text
https://example.com/contact:EMAIL:admin@example.com
```

另外，指向 facebook.com、github.com、instagram.com、youtube.com 的站外链接也会记入 intel（这四个域名写在 core/config.py 的 INTELS 列表里，可自行扩充）。

### 3.4 Files（文件发现）

Photon 维护一张静态资源后缀表（core/config.py 的 BAD_TYPES）：bmp、css、csv、docx、ico、jpeg、jpg、js、json、pdf、png、svg、xls、xml。链接指向这些后缀时，URL 记入 files.txt，且不再对该地址发起爬取。

注意两点：一是这张表只覆盖普通静态资源，`.env`、`.sql`、`.pem` 这类敏感文件 Photon 并不认识，想找它们得自己用 `-r` 写正则（见 3.7）；二是 js 也在表里，但从 `<script src>` 引用的 JS 不走这条线，而是进 scripts.txt 做端点扫描。

### 3.5 Secret Keys（密钥/Token）

加 `--keys` 才会开启，因为熵检测在大页面上比较耗 CPU。实现是纯熵检测：先抓所有 16-45 位、由字母、数字、下划线、连字符组成的字符串，再算字节级香农熵，熵值 ≥4 才保留。README 对它的描述是 "auth/API keys & hashes"。

keys.txt 里每行是 `URL: 字符串` 的格式：

```text
https://example.com/js/app.js: xE7dK9mQ2pL8vR4tW6zY0aB3cD5fG7hJ
```

高熵检测抓的是"长得像密钥的东西"，不是已知格式。AKIA 开头的 AWS Key、`ghp_` 开头的 GitHub Token 只有恰好够长够随机时才会顺带被抓到；UUID、随机 ID、长哈希都会混进来当误报。想系统性地找已知格式凭据，应该交给 gitleaks、trufflehog 这类专门的密钥扫描器。

### 3.6 JavaScript files & Endpoints

分两步：爬取过程中收集 `<script src>` 引用的 JS 文件地址存入 scripts.txt；一轮爬取结束后，再对每个 JS 文件抓一次，从代码文本里抽取引号包裹的、以 `/` 或 `http` 开头的字符串，过滤掉含 `{}<>"'` 的代码碎片，剩下的存入 endpoints.txt。

这是发现**未公开 API** 的重要渠道——很多应用把 API 路径硬编码在前端 JS 里，但没有在任何文档中公开。

### 3.7 Custom Regex（自定义正则）

用 `-r` 传一个正则，Photon 会在所有爬取到的页面文本里做匹配，结果存入 custom.txt。这个能力补上了内置规则没涵盖的场景，比如 3.4 里提到的敏感文件路径：

```bash
# 例：匹配所有 10 位数字（可能是手机号）
python photon.py -u example.com --regex "\d{10}"
```

### 3.8 Subdomains & DNS data

通过 `--dns` 插件启用，分两步：先抓取 findsubdomains.com 上该域名的子域名页，解析出列表存入 subdomains.txt；再向 dnsdumpster.com 提交一次带 CSRF token 的表单请求，下载它生成的 DNS 关系图，以 `输出目录/域名.png` 命名保存。

```bash
python photon.py -u example.com --dns
# 输出：subdomains.txt + example.com.png
```

输出的子域名可以交给 `httpx` 进一步探测存活状态。

---

## §4 安装与部署

### 4.1 系统要求

- Python 3.2+（源码明确不支持 Python 2）
- 依赖：requests、requests[socks]（SOCKS 代理支持）、urllib3、tld
- 操作系统：Linux / macOS / Windows。Wiki 记录在 Arch、Debian、Ubuntu、Termux、Windows 7/10、macOS 上测试过，macOS 和 Windows 终端下输出无颜色
- 一个例外要留意：`--headers` 依赖 nano 编辑器和 fork 系统调用，只能在 Unix 系上用

### 4.2 两种安装方式

**方式一：pip 安装（得到的是"库"形态）**

```bash
pip install photon
```

要特别说明：PyPI 上的 photon 包停在 1.1.9（2018-2019 年间），而且 setup.py 没有注册命令行入口——装完后**没有 `photon` 命令**，只能当库 import（用法见 §11）。它比源码落后好几个版本，连后来被移除的 Ninja 模式都还在。

**方式二：源码安装（想用命令行就必须走这条路）**

```bash
git clone https://github.com/s0md3v/Photon.git
cd Photon
pip install -r requirements.txt
python photon.py -u example.com
```

### 4.3 Docker 部署

官方提供了基于 Alpine 的 Dockerfile，镜像体积 103 MB。

```bash
# 构建
docker build -t photon .

# 运行（结果保存在容器卷内，用 docker inspect 查看）
docker run -it --name photon photon:latest -u example.com

# 运行（挂载宿主机目录，结果直接落盘）
docker run -it --name photon \
  -v "$PWD:/Photon/example.com" \
  photon:latest -u example.com
```

### 4.4 代理

v1.3.2 起代理走 `-p/--proxy` 参数，接受 `IP:PORT` 或 `DOMAIN:PORT`，`http://`、`socks5://` 前缀可省（默认 http），也接受一个代理列表文件：

```bash
python photon.py -u example.com -p 127.0.0.1:8080             # HTTP 代理
python photon.py -u example.com -p socks5://127.0.0.1:1080    # SOCKS5
python photon.py -u example.com -p proxies.txt                # 代理列表，逐个轮换
```

启动时 Photon 会先逐个测试代理（拿 example.com 试连），不可用的直接剔除；一个都不可用就退出。列表文件里每行一个代理，格式同上。

---

## §5 完整命令行参考

```text
usage: photon.py [options]
```

### 5.1 核心参数

| 参数 | 全名 | 默认值 | 说明 |
|------|------|--------|------|
| `-u` | `--url` | 必填 | 目标根 URL（可省略 https://，会自动尝试） |
| `-l` | `--level` | `2` | 爬取深度（层数） |
| `-t` | `--threads` | `2` | 并发线程数 |
| `-d` | `--delay` | `0` | 每次请求间隔秒数 |
| `--timeout` | | `6` | HTTP 请求超时秒数 |
| `-o` | `--output` | 域名 | 结果输出目录名 |
| `-p` | `--proxy` | 无 | 代理，支持单个或列表文件 |
| `-v` | `--verbose` | 关 | 实时打印发现的数据 |

### 5.2 数据提取参数

| 参数 | 说明 |
|------|------|
| `--keys` | 启用高熵密钥/Token 检测 |
| `-r PATTERN` / `--regex=PATTERN` | 自定义正则匹配所有页面 |
| `--only-urls` | 只爬 URL——Intel、JS 扫描、fuzzable、熵检测全部跳过 |

### 5.3 种子与过滤

| 参数 | 说明 |
|------|------|
| `-s URL1 URL2` / `--seeds URL1 URL2` | 额外的起始 URL（空格分隔多个） |
| `--exclude="REGEX"` | 排除匹配正则的 URL |
| `--wayback` | 从 archive.org 拉最近半年的历史 URL 作为种子 |

### 5.4 插件与导出

| 参数 | 说明 |
|------|------|
| `--dns` | 抓取子域名并下载 DNS 关系图 |
| `-e json` / `-e csv` / `--export=json` | 导出格式化结果到单个文件 |
| `--stdout=VARIABLE` | 将指定数据集输出到 stdout，支持管道 |

`--stdout` 支持的变量名：`files`、`intel`、`robots`、`custom`、`failed`、`internal`、`scripts`、`external`、`fuzzable`、`endpoints`、`keys`。

### 5.5 其他

| 参数 | 说明 |
|------|------|
| `-c "COOKIE"` | 在请求中附加 Cookie |
| `--clone` | 把爬到的页面快照存进当前目录下的 `{域名}_mirror/` |
| `--headers` | 开关（不接值）：打开 nano 让你交互式填写请求头，仅 Unix 可用 |
| `--user-agent="UA1,UA2"` | 逗号分隔多个 UA，每次请求随机轮换 |
| `--update` | 检查更新，确认后从 GitHub 拉取新版覆盖本地 |

---

## §6 实战场景

### 6.1 快速侦察：5 分钟扫一遍目标

```bash
python photon.py -u https://example.com -t 10 -l 2 -v \
  --keys --dns --wayback -o recon_results
```

跑完后 `recon_results/` 目录下会有：

```text
recon_results/
├── internal.txt        # 站内 URL（爬取与输出的主干）
├── external.txt        # 站外引用
├── fuzzable.txt        # 含 = 的站内 URL（喂给 fuzzer）
├── files.txt           # 静态资源 URL
├── intel.txt           # IOC 情报（URL:类型:内容）
├── keys.txt            # 高熵字符串（--keys 产出）
├── scripts.txt         # JS 文件列表
├── endpoints.txt       # JS 中提取的后端端点
├── robots.txt          # 目标 robots.txt 里抓到的路径
├── subdomains.txt      # 子域名（--dns 产出）
└── example.com.png     # DNS 关系图（--dns 产出，以域名命名）
```

两个细节：custom.txt 只在用了 `-r` 时才会出现，failed.txt 只在发生失败请求时生成——Photon 只为非空的数据集写文件。

### 6.2 管道到下一个工具

`--stdout` 就是为串联其他 OSINT 工具设计的，数据不落盘、直接走管道：

```bash
# 把 JS 里提取的端点交给 nuclei 扫描
python photon.py -u example.com --stdout=endpoints | \
  nuclei -t /path/to/templates/

# 把带参数的 URL 交给 httpx 探活，看哪些真的活着
python photon.py -u example.com --stdout=fuzzable | \
  httpx -status-code -title
```

### 6.3 只爬 URL，跳过重提取

如果你已经有了 Photon 会提取的那些信息（比如用了 theHarvester 找邮箱、用 GitDorker 找密钥），可以只让 Photon 做广度爬取，速度也会更快：

```bash
python photon.py -u example.com --only-urls -t 20 -l 3
```

---

## §7 插件系统

Photon 有三个官方插件，对应三个命令行开关。

### 7.1 Wayback（`--wayback`）

调用 archive.org 的 CDX API，按主机名拉取该站的历史 URL。查询窗口是最近半年，不是全量历史——这个设计过滤掉了大量早已死链的旧 URL。拉回来的 URL 会并入种子参与正常爬取。

**为什么重要**：很多公司重构网站时会删除旧页面，但旧 URL 可能还留着敏感内容。archive.org 是发现这些"被遗忘的入口"的绝佳来源。

### 7.2 DNSdumpster（`--dns`）

如 §3.8 所述：子域名来自 findsubdomains.com 的页面抓取，DNS 关系图来自 dnsdumpster.com 的表单提交。拿到的子域名可以交给 `httpx` 探活。

### 7.3 Exporter（`-e json` / `-e csv`）

把全部 11 个数据集汇总写进输出目录下的 exported.json 或 exported.csv，方便后续做程序化分析，或导入 Maltego 这类可视化工具。

---

## §8 架构速览：一次爬取在 Photon 内部怎么走

全部代码约 1,200 行 Python，设计很直接：

```text
 种子收集 zap()：robots.txt 的 Allow/Disallow 路径
                 + sitemap.xml 的 <loc> URL
                 （--wayback 再并入 archive.org 最近半年的 URL）
        │
        ▼
 逐层 BFS（默认 2 层）：每层取 internal − processed 交给线程池
        │
        ▼
 ThreadPoolExecutor（默认 2 线程）── 每个页面一次请求
        │
        ├── <a href> 解析：站内入队 / 站外记录 / 静态资源记入 files
        ├── Intel：整页文本跑 15 类 IOC 正则
        ├── JS 文件：记录 <script src> 引用
        └── 可选：--keys 熵检测、-r 自定义正则
        │
        ▼
 爬取收尾：对收集到的 JS 文件再扫一轮，抽端点；internal 里含 = 的入 fuzzable
        │
        ▼
 writer()：非空数据集各写一个 .txt（--dns / --export / --stdout 随后执行）
```

拿 `python photon.py -u https://example.com` 走一遍：程序先请求 example.com/robots.txt，把里面不含通配符的 Allow/Disallow 路径补成完整 URL 作为第一批种子，再请求 sitemap.xml 把 `<loc>` 里的 URL 也并入。然后进入逐层循环：第 1 层抓主页，解析出的站内链接入队；第 2 层抓这些链接，同时每抓一个页面就跑一轮 Intel 正则、记下 JS 引用。循环结束后对 scripts.txt 里的每个 JS 文件再发一轮请求抽端点。最后统一落盘，终端会打出各类数据的计数、总请求数和耗时。

**几个值得注意的实现细节**：

- **去重与存储全靠 `set`**。11 类数据各自一个 set，`processed` 记录已爬 URL，入队前先过滤。
- **并发无锁**。线程池来自 `concurrent.futures`；共享状态只有 set 的 add 操作，CPython 的 GIL 保证了原子性，所以代码里没有任何显式锁。写盘集中在结束时由主线程完成。
- **请求器复用连接**。所有请求走同一个 `requests.Session`（v1.1.6 的优化，TCP 握手只做一次）；最多跟 3 次重定向；证书校验是关掉的（`verify=False`）；UA 每次请求从 core/user-agents.txt 随机取一个，`--user-agent` 可以覆盖。
- **SPA 的天然边界**。不执行 JS、不建 DOM，所以 React/Vue 应用动态渲染的内容 Photon 看不到。它会去爬 JS bundle，也能从压缩代码里抽端点——但压缩后的 bundle 里以 `/` 开头的字符串字面量很多，端点误报也会随之变多。

---

## §9 同类工具对比

Photon 不和子域名枚举器、目录爆破器抢活，它守的是"爬取 + 提取"这一层。

| 能力 | Photon | Amass | subfinder | httpx | SpiderFoot |
|------|--------|-------|-----------|-------|------------|
| 子域名枚举 | ⭐（--dns 插件） | ⭐⭐⭐ | ⭐⭐⭐ | ❌ | ✅ |
| 深度爬取 | ⭐⭐ | ⭐ | ❌ | ❌ | ⭐⭐ |
| 密钥/高熵串提取 | ⭐⭐ | ❌ | ❌ | ❌ | ⭐ |
| JS 端点发现 | ⭐⭐⭐ | ❌ | ❌ | ❌ | ⭐ |
| 邮箱/Intel | ⭐⭐⭐ | ❌ | ❌ | ❌ | ⭐⭐⭐ |
| 管道友好（stdout） | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ❌ |
| 依赖与启动 | Python / 秒级 | Go / 秒级 | Go / 毫秒级 | Go / 毫秒级 | Python + DB / 分钟级 |
| 适合场景 | Bug Bounty 侦察、轻量爬取 | 重型子域名发现 | 被动子域名发现 | 存活探测 | 可视化 OSINT 平台 |

**推荐组合拳**：

```bash
# 第一步：subfinder 批量枚举子域名
subfinder -d example.com -silent -o subdomains.txt

# 第二步：httpx 探测存活 + 标题 + 技术栈
httpx -l subdomains.txt -title -tech-detect -o live.txt

# 第三步：Photon 对存活目标做深度数据提取
while read url; do
  python photon.py -u "$url" -t 10 --keys --wayback \
    -o "results/$(echo $url | sed 's|https\?://||')"
done < live.txt
```

如果你的目标重 SPA、需要执行 JS 才能出链接，Photon 的替代品是 ProjectDiscovery 的 katana——它支持无头浏览器，且维护活跃。反过来，目标以服务端渲染为主、要的是快速把文本里的情报字段捞干净，Photon 依然顺手。

---

## §10 安全边界与合规

**Photon 只应该用于你有授权的目标**。包括但不限于：

- 你自己拥有的域名
- 客户书面授权的渗透测试目标
- HackerOne、Bugcrowd 等公开 Bug Bounty 平台的范围内目标

**不应用于**：

- 未授权的第三方网站
- 政府、医疗、金融等受监管行业的目标（除非有明确书面许可）

**降低被封禁的技巧**：

- 调高 `--delay`：每次请求间隔 1-3 秒
- 调低 `--threads`：2-5 个线程通常够用
- 把 `--level` 控制在 2-3 层，更深会指数级增长请求量
- UA 默认就是随机轮换的，一般不用额外处理

另一个值得知道的点：Photon 关闭了 SSL 证书校验（`verify=False`），在不可信网络里跑，抓回来的内容存在被中间人篡改的可能。对安全工具来说，这本身就是个需要权衡的风险。

---

## §11 常见问题

**Q：Photon 和 theHarvester 有什么区别？**

theHarvester 专门枚举邮箱、用户名、IP，数据源是搜索引擎和 API。Photon 是从实际爬取的页面里提取，能发现搜索引擎索引不到的、藏在 JS 里的端点和密钥。两者互补。

**Q：Photon 能处理 SPA（React/Vue）应用吗？**

部分能。Photon 会爬 JS bundle 文件，也会从里面尝试正则提取 API 端点。但 SPA 动态渲染出来的内容 Photon 看不到——它不执行 JS。如果目标是纯 SPA，建议配合 Playwright 或 puppeteer 先 dump 页面内容，再交给 Photon，或者直接换 katana。

**Q：`--keys` 检测出来的都是真的密钥吗？**

不是。熵检测抓的是"长得像密钥的字符串"，哈希值、UUID、随机 ID 都会产生误报。建议把 keys.txt 导出后人工筛一遍，或者用 nuclei 的密钥验证模板做二次确认。

**Q：能写成库调用吗？**

可以，这也是 PyPI 包唯一的打开方式：

```python
import photon

result = photon.crawl('http://example.com')   # 返回 dict
print(photon.results())                        # 随时查看结果
photon.clear()                                 # 换目标前清空
```

可选参数有 level、threads、timeout、keys、exclude、seeds 等，含义与命令行一一对应。注意这套接口属于 PyPI 上的 1.1.9 老版本；源码里的 core/flash.py 等模块也可以直接 import 拼装，但作者没把它们当公开 API 承诺，升级时可能变动。

---

## §12 相关资源

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | [github.com/s0md3v/Photon](https://github.com/s0md3v/Photon) |
| PyPI | [pypi.org/project/photon](https://pypi.org/project/photon/) |
| 官方 Wiki（含完整参数说明） | [Photon Wiki](https://github.com/s0md3v/Photon/wiki) |
| 版本历史 | [CHANGELOG.md](https://github.com/s0md3v/Photon/blob/master/CHANGELOG.md) |
| 兼容性说明 | [Compatibility & Dependencies](https://github.com/s0md3v/Photon/wiki/Compatibility-&-Dependencies) |
| 库调用 API | [Photon Library](https://github.com/s0md3v/Photon/wiki/Photon-Library) |

---

**文档信息**
类型：安全工具深度指南 | 事实核对：2026-09-12（对照 master v1.3.2 源码与 GitHub API，Stars 13,199） | 作者：Somdev Sangwan（s0md3v） | 许可证：GPL v3.0
