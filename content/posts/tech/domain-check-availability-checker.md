---
title: "domain-check：极速域名可用性检查——1,200+ TLDs + AI 代理支持的从入门到精通"
date: "2026-04-14T22:25:00+08:00"
slug: "domain-check-availability-checker"
description: "domain-check 是 261 Stars 的 Rust 域名检查工具，支持 1,200+ TLDs、RDAP+WHOIS 双协议、100 并发。内置 11 个预设（startup、tech、creative 等），支持域名生成模式，提供 CLI/Rust库/MCP Server 三种形态，可集成到 Claude、Cursor 等 AI 代理。"
draft: false
categories: ["技术笔记"]
tags: ["域名", "RDAP", "WHOIS", "Rust", "MCP", "域名检查", "品牌保护"]
---

# domain-check：极速域名可用性检查——1,200+ TLDs + AI 代理支持

创业团队在产品发布前往往要抢注 8 个 TLD 的域名——`.com` 保品牌、`.io` 给开发者看、`.ai` 拿融资叙事、`.app` 上移动端。手动去 Namecheap 或 GoDaddy 一个个搜，8 个 TLD × 5 个候选名 = 40 次点击，等注册商前端渲染完已经过去半小时。`domain-check` 解决的就是这个真问题：用 Rust 写的命令行工具，1,200+ TLD 一次拉满，RDAP 优先 + WHOIS 兜底，100 并发流式输出，2.7 MB 二进制零依赖部署。

它不解决的是子域名发现和暴力枚举。如果你想从 `example.com` 找出 `api.example.com`、`staging.example.com`，应该用 `subfinder`；想拿字典跑未注册的短域名，应该上 `massdns`。`domain-check` 的定位是**已知 base name、未知 TLD 可用性**的快速判定，边界清晰。

## 系统地图：三层形态共享一个引擎

`domain-check` 不是单纯的 CLI，而是同一个 Rust 引擎暴露的三种形态：

```
┌─────────────────────────────────────────────────┐
│            domain-check-lib (核心引擎)            │
│  ┌─────────────┐  ┌──────────┐  ┌────────────┐  │
│  │ RDAP 客户端 │  │ WHOIS    │  │ 域名生成器 │  │
│  │ (reqwest)   │  │ (tokio)  │  │ (pattern)  │  │
│  └─────────────┘  └──────────┘  └────────────┘  │
│         ↓ IANA Bootstrap + 32 TLD 硬编码兜底      │
└─────────────────────────────────────────────────┘
        ↑                    ↑                    ↑
   CLI 二进制            MCP Server          Rust 库
   (clap)              (stdio JSON-RPC)    (domain-check-lib)
```

CLI 给人用，MCP Server 给 AI 代理用，Rust 库给嵌入式场景用。三者共享同一套协议实现、同一套预设、同一套并发模型，区别只在入口。这种设计的好处是：你在 CLI 里调通的预设和参数，原封不动搬到 MCP 配置里就能用，不用学第二套语义。

工具的核心能力边界可以这样拆分：

| 维度 | 能做 | 不能做 |
|------|------|--------|
| 协议覆盖 | RDAP（约 85% TLD）+ WHOIS 兜底（约 189 个 ccTLD） | DNS 解析、注册商 API 下单 |
| 检查范围 | 1,200+ TLD 的可用性 + 注册商/日期信息 | 子域名枚举、历史 WHOIS 查询 |
| 生成能力 | `\w` `\d` `?` 通配符 + 前缀后缀笛卡尔积 | 模糊匹配、语义化命名建议 |
| 集成形态 | CLI / Rust 库 / MCP Server | Web UI、SaaS API |

理解了这个边界，后面看协议层差异和工程实现就不会跑偏。

## 协议层差异：WHOIS 是 1985 年的遗物，RDAP 是 2015 年的补丁

要理解 `domain-check` 为什么搞双协议，得先看这两个协议在 IETF 标准里到底是什么东西。

WHOIS 的规范是 **RFC 3912**，2004 年发布，但它本身只是把 1985 年的实践文档化了一下。协议极其简单：客户端向服务器的 TCP 43 端口建立一个连接，发送查询关键字加 `\r\n`，然后接收服务器返回的纯文本，连接关闭。没有请求头、没有状态码、没有结构化字段、没有鉴权、没有加密。服务器返回什么完全取决于注册局的心情——Verisign 的 `.com` WHOIS 一套格式，PIR 的 `.org` 另一套，Nominet 的 `.uk` 又是一套。解析 WHOIS 输出本质上是在做正则匹配 + 启发式猜测，每个注册局都要单独适配。

更麻烦的是 GDPR 之后，欧盟注册局开始大量遮蔽 WHOIS 里的注册人信息，部分 ccTLD（如 `.es`、`.eu`）甚至直接关停了公开 WHOIS。加上 WHOIS 服务器普遍限流严重——`.com` 的 WHOIS 几十次查询就会被临时封 IP——这个协议在工程上越来越难用。

RDAP（Registration Data Access Protocol）是 IETF 在 2015 年推出的替代方案，规范是 **RFC 7480 到 7484** 这一组：

- **RFC 7480**：HTTP 协议使用规范，明确 RDAP 跑在 HTTPS 上
- **RFC 7481**：安全服务（TLS、OAuth）
- **RFC 7482**：查询语法（`/domain/example.com` 这样的 RESTful 路径）
- **RFC 7483**：JSON 响应结构（标准化字段名、状态码、事件日期）
- **RFC 7484**：Bootstrap——IANA 维护的注册表，告诉你某个 TLD 该去哪个 RDAP 服务器查

RDAP 的核心改进是**结构化 JSON 响应**。同一个查询，WHOIS 返回的是 30 行格式各异的纯文本，RDAP 返回的是带 `events`、`status`、`entities` 字段的 JSON，解析器不用猜。再加上 HTTPS 传输、标准化的 404（域名可用）和 200（域名已注册）状态码，工程上可控多了。

但 RDAP 没有完全取代 WHOIS。IANA 的 RDAP Bootstrap 注册表覆盖了绝大多数 gTLD（`.com`、`.org`、`.io`、`.ai` 等），但约 189 个 ccTLD 仍然只有 WHOIS——典型的有 `.es`（西班牙）、`.co`（哥伦比亚，虽然商业上很流行）、`.eu`（欧盟）、`.jp`（日本）。这些注册局要么没资源实现 RDAP，要么本地法规不允许公开结构化注册数据。

这就是 `domain-check` 双协议策略的根因：**RDAP 优先拿结构和速度，WHOIS 兜底拿覆盖率**。

## 双协议引擎的降级策略

`domain-check` 的检查流程不是简单的"先 RDAP 后 WHOIS"，而是带状态判定的降级链：

```
输入域名 (e.g. myapp.es)
    │
    ▼
IANA Bootstrap 查询 → 找到 RDAP 服务器？
    │
    ├─ 是 → RDAP HTTPS 请求
    │       │
    │       ├─ 200 → 域名已注册，解析 JSON 返回 TAKEN
    │       ├─ 404 → 域名可用，返回 AVAILABLE
    │       └─ 超时/5xx → 降级到 WHOIS
    │
    └─ 否 → 直接走 WHOIS
              │
              ├─ 解析纯文本，匹配 "No match" / "AVAILABLE" 等模式
              ├─ 命中可用模式 → AVAILABLE
              ├─ 命中注册信息 → TAKEN
              └─ 无法判定 → UNKNOWN
```

这里有个工程细节值得展开：RDAP 返回 404 不一定意味着域名真的可用。某些 RDAP 服务器在内部错误时也会返回 404，直接判定 AVAILABLE 会误报。`domain-check` 在 CHANGELOG 里专门提过这个修复（commit `6445f37`，对应 issue #30）——把 RDAP 404 当作 inconclusive，defer 到 WHOIS 二次确认。这种"协议层不信任"的设计在分布式系统里很常见，本质是**别把下游的语义错误当成业务事实**。

WHOIS 兜底也不是万能的。WHOIS 输出格式不标准，`domain-check` 内部维护了一套正则模式库来识别"域名可用"的信号——比如 `No match for`、`NOT FOUND`、`No Data Found`、`No entries found` 等几十种变体。遇到没见过的注册局格式，就会返回 `UNKNOWN` 而不是瞎猜。这是工程上的诚实：宁可让用户重试，也不输出错误结论。

降级策略的另一个考量是**超时控制**。RDAP 走 HTTPS，默认超时 8 秒；WHOIS 走 TCP 43，超时通常更短（注册局服务器响应快但限流狠）。`domain-check` 允许通过 `--timeout` 和配置文件调整，CI 场景里建议显式设置，避免某个慢注册局拖垮整个批次。

## 并发模型：tokio 的 100 路并发意味着什么

`domain-check` 的并发上限是 100，默认 20。这个数字背后的工程含义需要拆开看。

Rust 的异步运行时是 tokio，采用的是 **M:N 调度模型**——M 个 async task 跑在 N 个 OS 线程上（默认 N = CPU 核心数）。100 并发不是 100 个线程，而是 100 个被 tokio 调度的 task。每个 task 大部分时间在 `await` 网络 I/O，不占线程，所以 100 路并发对内存的消耗远低于 100 个 OS 线程（每个线程默认栈 2 MB，100 线程就是 200 MB；tokio task 栈按需增长，100 路通常在几十 MB 量级）。

但 100 并发不是越大越好。RDAP/WHOIS 服务器有限流，并发太高会被封 IP。`.com` 的 Verisign RDAP 服务器对单 IP 的限流比较宽松，但一些小注册局（比如某些 ccTLD）几个并发就会返回 429。`domain-check` 默认 20 并发是个保守值，覆盖大多数场景；`--concurrency 100` 适合批量跑 gTLD，跑 ccTLD 建议降回 10-20。

流式输出（`--streaming`）是并发的自然延伸。100 路并发发起后，谁先返回谁先输出，不等最慢的那个。这对长批次任务很重要——1000 个域名跑 30 秒，如果等全部完成再输出，用户盯着空白屏幕 30 秒会以为卡死了。流式输出让用户看到进度，也能在发现异常时 Ctrl+C 提前中断。实现上，`domain-check` 用 tokio 的 `mpsc` channel 把结果从 worker task 推回主线程，主线程边收边打印，spinner 写到 stderr 不污染 stdout 的结构化输出。

工程上还有一个细节：非 TTY 环境（管道、CI）下，`domain-check` 自动禁用 spinner 和颜色，避免 ANSI 转义码污染 JSON/CSV 输出。这是 CLI 工具的基本素养，但很多早期项目做不到——`domain-check` 在 0.9.1 版本里把这个行为固化了。

## 域名生成模式：通配符语义和组合算法

`domain-check` 的域名生成不是简单的字符串拼接，而是一个小的模式语言。三种通配符：

- `\w`：匹配一个字母（`[a-z]`，小写）
- `\d`：匹配一个数字（`[0-9]`）
- `?`：匹配字母或数字（`[a-z0-9]`）

`--pattern "app\d"` 会展开成 `app0`、`app1`、`app2`...`app9` 共 10 个候选名。`--pattern "go\w\w"` 展开成 `goaa`、`goab`...`gozz` 共 676 个。组合是笛卡尔积，所以 `--pattern "\w\d"` 是 26 × 10 = 260 个名字。

前缀后缀是另一维度的展开。`domain-check myapp --prefix get,try --suffix hub,ly -t com,io` 实际生成的域名是：

```
基础名: myapp
前缀: [get, try]  →  getmyapp, trymyapp
后缀: [hub, ly]   →  myapphub, myapply
前缀+后缀:        →  getmyapphub, getmyapply, trymyapphub, trymyapply
TLD: [com, io]
最终域名: 4 × 2 = 8 个
```

这里有个组合爆炸的陷阱：前缀 5 个 × 后缀 5 个 × TLD 10 个 = 250 个域名，再加 `\w` 通配符就是 250 × 26 = 6500 个。`domain-check` 提供 `--dry-run` 预览生成的域名列表而不实际查询，强烈建议先 `--dry-run` 看一眼数量再决定是否加 `--force` 跳过确认提示。

算法上，生成器是惰性的——用 Rust 的迭代器（`Iterator` trait）逐个 yield，不会一次性把 6500 个字符串全放进内存。这对大规模生成很重要，避免内存峰值。查询端再用 `buffer_unordered` 并发消费这个迭代器，实现"边生成边查"的流水线。

## 11 个预设背后的 TLD 选择逻辑

预设不是随便挑的 TLD 列表，每个都对应一种真实场景的域名策略。理解这些选择逻辑，能帮你判断该用哪个预设或自定义。

`startup` 预设是 `com, org, io, ai, tech, app, dev, xyz` 这 8 个。逻辑是：`com` 必抢（用户默认输入）、`org` 给非营利或开源、`io` 是开发者圈子的默认假设、`ai` 是 2023 年后融资叙事必备、`tech`/`app`/`dev` 覆盖技术定位、`xyz` 作为便宜的兜底（注册费常年在 $1-3）。这 8 个 TLD 覆盖了科技创业公司 90% 的注册需求。

`tech` 预设扩展到 10 个：`io, ai, app, dev, tech, cloud, software, tools, code, systems`。这些是开发者工具类产品的"身份 TLD"——看到 `vercel.app`、`replit.dev`、`cursor.com`，开发者立刻知道这是同类产品。选这些 TLD 不是因为 SEO，而是因为**目标用户的认知锚点**。

`finance` 预设的 `finance, capital, fund, money, investments, bank, pay, trading, markets, crypto` 则是另一套逻辑：金融产品的信任感构建。`.bank` 有严格准入（必须是持牌银行），`.fund`、`.capital` 给资管机构，`.pay`、`.trading` 给支付和交易类产品。这些 TLD 本身就是行业信号。

`country` 预设是 `us, uk, de, fr, ca, au, br, in, nl`——G7 加几个大经济体。做国际化业务时，本地 ccTLD 能提升当地用户的信任度，但要注意很多 ccTLD 有本地存在要求（比如 `.fr` 早期要求法国地址，`.eu` 要求欧盟居民/公司）。

`creative`、`ecommerce`、`web`、`trendy` 类似，每个预设的 TLD 选择都对应一类产品的品牌定位。如果预设不合适，配置文件里可以自定义：

```toml
[custom_presets]
my_stack = ["com", "io", "dev", "app"]
```

自定义预设和内置预设在 CLI 里用法完全一样：`domain-check mybrand --preset my_stack`。

## 一次完整的检查流程：myapp 在 startup 预设下

把前面的概念串起来，看一次实际查询怎么流过系统。假设你跑：

```bash
domain-check myapp --preset startup --pretty
```

第一步，CLI 解析参数，`--preset startup` 展开成 8 个 TLD，生成 8 个待查域名：`myapp.com`、`myapp.org`、`myapp.io`、`myapp.ai`、`myapp.tech`、`myapp.app`、`myapp.dev`、`myapp.xyz`。

第二步，引擎启动，默认并发 20（8 个域名远低于上限，会一次性全部发起）。对每个域名：

1. 查 IANA RDAP Bootstrap 注册表，找该 TLD 的 RDAP 服务器地址。`.com` 指向 `https://rdap.verisign.com/com/v1/`，`.io` 指向 `https://rdap.nic.io/`，`.ai` 指向 `https://rdap.nic.ai/`，等等。
2. 发起 HTTPS GET 请求到 `https://rdap.verisign.com/com/v1/domain/myapp.com`。
3. 收到 200 → TAKEN，解析 JSON 提取注册商和日期（如果带 `--info`）；收到 404 → AVAILABLE；超时或 5xx → 降级 WHOIS。

第三步，8 个请求并发返回，tokio 调度器把结果通过 channel 推给主线程。主线程按完成顺序接收，但 `--pretty` 模式下会先缓冲所有结果，最后按 AVAILABLE/TAKEN 分组打印：

```
domain-check v1.0.2 — Checking 8 domains
Preset: startup | Concurrency: 20

── Available (3) ──────────────────────────────
 myapp.ai
 myapp.tech
 myapp.xyz

── Taken (5) ──────────────────────────────────
 myapp.com
 myapp.org
 myapp.io
 myapp.app
 myapp.dev

8 domains in 0.8s | 3 available | 5 taken | 0 unknown
```

第四步，如果某个 TLD（比如 `.ai`）的 RDAP 服务器超时，引擎降级到 WHOIS。`.ai` 的 WHOIS 服务器是 `whois.nic.ai`，TCP 43 端口连接，发送 `myapp.ai\r\n`，解析返回的纯文本判断可用性。这一步对用户透明，只在 `--json` 输出的 `method` 字段里能看到是 `RDAP` 还是 `WHOIS`。

整个流程 0.8 秒完成，瓶颈是网络 RTT，不是 CPU。这也是 Rust + tokio 的价值——把 I/O 等待时间用来跑其他并发 task，而不是阻塞线程。

## 安装与基本使用

安装有三种方式，按推荐顺序：

```bash
# Homebrew（macOS 首选，自动处理依赖）
brew install domain-check

# Cargo（跨平台，需要 Rust 工具链）
cargo install domain-check

# GitHub Releases（CI/CD 场景，下载预编译二进制）
curl -L https://github.com/saidutt46/domain-check/releases/latest/download/domain-check-linux.tar.gz | tar -xz
```

基本用法覆盖 90% 场景：

```bash
# 检查单个域名
domain-check example.com

# 检查多个 TLD
domain-check myapp -t com,org,io,ai

# 使用预设，pretty 输出
domain-check myapp --preset startup --pretty

# 检查所有 TLD（1200+，需要 --batch 跳过确认）
domain-check mybrand --all --batch

# 获取注册商和日期信息
domain-check mycompany.com --info
```

域名生成：

```bash
# 通配符模式，先 dry-run 预览
domain-check --pattern "app\d" -t com --dry-run

# 前缀后缀组合
domain-check myapp --prefix get,try --suffix hub,ly -t com,io

# 大规模生成 + 流式输出
domain-check --pattern "go\w\w" -t io,app --concurrency 50 --streaming
```

CI/CD 场景的关键参数：

```bash
# 非交互式 JSON 输出，管道友好
domain-check --file required-domains.txt --json --yes

# 离线模式，只用 32 个硬编码 TLD（确定性优先）
domain-check mybrand --no-bootstrap --batch

# 大批量强制执行，跳过所有确认
domain-check --file huge-list.txt --all --force --yes --csv > results.csv
```

`--no-bootstrap` 是个值得注意的参数。默认情况下 `domain-check` 启动时会从 IANA 拉取 RDAP Bootstrap 注册表（一个 JSON 文件，几百 KB），用于动态发现 TLD 的 RDAP 服务器。但 CI 环境里你可能想要完全确定性的行为——不依赖网络拉取 bootstrap，只用内置的 32 个硬编码 TLD。这个模式下覆盖率降低但可重复性强，适合回归测试。

## MCP Server：把域名检查塞进 AI 代理

`domain-check-mcp` 是独立的 crate，把引擎暴露为 MCP（Model Context Protocol）工具，让 AI 代理能直接调用。MCP 是 Anthropic 推出的协议，本质是给 LLM 一个标准的"外部工具调用"接口——类似 function calling，但协议层标准化、跨客户端通用。

安装和接入 Claude Code：

```bash
# 安装 MCP Server
cargo install domain-check-mcp

# 注册到 Claude Code
claude mcp add domain-check -- domain-check-mcp
```

注册后，Claude Code 会话里可以直接用自然语言：

```
用户：帮我查一下 coolstartup 在 startup 预设下的可用性
Claude：[调用 check_with_preset 工具，参数 {name: "coolstartup", preset: "startup"}]
       coolstartup.com 已被注册
       coolstartup.io 已被注册
       coolstartup.ai 可用
       coolstartup.tech 可用
       ...
       建议优先抢注 coolstartup.ai 和 coolstartup.app
```

MCP Server 暴露 6 个工具：`check_domain`（单域名）、`check_domains`（批量）、`check_with_preset`（预设查询）、`generate_names`（模式生成）、`list_presets`（列出预设）、`domain_info`（详细信息）。工具签名和 CLI 参数一一对应，AI 代理不需要学新概念。

实际场景里，MCP 集成的价值不是"省几条命令"，而是把域名检查嵌入到 AI 的工作流里。比如你让 Claude 帮你起一个 SaaS 产品名，它可以一边生成候选名一边查可用性，把"名字好听但被注册了"的候选直接过滤掉，最后给你一个可用名单。这个闭环在纯 CLI 时代需要人工来回切换，MCP 让 AI 代理自己完成。

支持的客户端除了 Claude Code，还有 Claude Desktop、VS Code Copilot、Cursor、Windsurf、JetBrains AI Assistant、OpenAI Codex CLI、Gemini CLI——基本上所有支持 MCP stdio 的客户端都能接。

## 采用边界：什么时候不该用 domain-check

工具选型最怕"拿着锤子看什么都是钉子"。`domain-check` 的适用场景和不适用的场景需要划清楚。

**适合用**：

- 创业团队发布前抢注品牌域名（已知 base name，扫多个 TLD）
- 商标保护审计（扫所有 TLD 看是否有抢注）
- 域名投资人快速筛选（模式生成 + 批量查）
- CI/CD 里集成域名可用性检查（如监控自家域名状态）
- AI 代理工作流里的域名查询环节（MCP 集成）

**不适合用**：

- 子域名发现：想找 `example.com` 下有哪些子域名，用 `subfinder` 或 `amass`，它们爬证书透明度日志、DNS 数据库、搜索引擎缓存
- 暴力枚举短域名：想跑 `a.com`、`b.com`...`z.com` 这种字典攻击，用 `massdns` + 字典文件，`massdns` 的 DNS 解析速度比 `domain-check` 的 RDAP/WHOIS 查询快两个数量级
- 历史 WHOIS 查询：`domain-check` 只查当前状态，要看历史注册人/变更记录用 DomainTools 或 WhoisXML API
- 注册商 API 操作：`domain-check` 只查不下单，要自动注册得用 Namecheap/Cloudflare/Porkbun 的 API
- DNS 解析问题排查：用 `dig`、`dnsutils`、`dnsmasq`

一个简单的判断标准：**你的问题是"这个名字在哪些 TLD 下可用"吗？** 是就用 `domain-check`；是"这个域名下有哪些子域名"就用 `subfinder`；是"这个域名历史上注册过什么"就用 DomainTools。

## Rust 库：嵌入到自己的项目

如果 CLI 和 MCP 都不满足，可以直接用 `domain-check-lib` 嵌入到 Rust 项目里：

```toml
[dependencies]
domain-check-lib = "1.0.2"
```

```rust
use domain_check_lib::DomainChecker;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let checker = DomainChecker::new();
    let result = checker.check_domain("example.com").await?;
    println!("{} -> {:?}", result.domain, result.available);
    Ok(())
}
```

库的 API 设计是异步优先，所有查询方法返回 `Future`，调用方自己决定并发策略。`DomainChecker` 内部管理连接池和缓存，多次查询复用底层 HTTP 客户端。典型用法是用 `futures::stream::iter` + `buffer_unordered` 实现并发批量查询，和 CLI 内部的实现一致。

## 配置与环境变量

`domain-check` 支持三层配置覆盖，优先级从高到低：

1. 命令行参数（`--concurrency`、`--preset` 等）
2. 环境变量（`DC_CONCURRENCY`、`DC_PRESET` 等）
3. 配置文件（TOML）
4. 内置默认值

配置文件查找顺序：`./domain-check.toml` > `~/.domain-check.toml` > `~/.config/domain-check/config.toml`。项目级配置覆盖用户级，符合常见约定。

一个完整的配置文件示例：

```toml
[defaults]
concurrency = 25
preset = "startup"
pretty = true
timeout = "8s"
bootstrap = true

[custom_presets]
my_startup = ["com", "io", "ai", "dev", "app"]

[generation]
prefixes = ["get", "my"]
suffixes = ["hub", "ly"]
```

环境变量适合 CI/CD 场景，不用维护配置文件：

```bash
DC_CONCURRENCY=50 DC_PRESET=startup DC_TLD=com,io,dev \
DC_PRETTY=true DC_TIMEOUT=10s DC_BOOTSTRAP=true \
domain-check myapp
```

## 可靠性注意事项

`domain-check` 的输出有三种状态：AVAILABLE、TAKEN、UNKNOWN。UNKNOWN 不是 bug，是协议层的诚实表达。

RDAP 服务器偶尔返回 5xx 或超时，WHOIS 服务器限流时直接断连，这些都会导致 UNKNOWN。批量查询时如果 UNKNOWN 比例超过 5%，建议降低并发或增加超时重试。CI 场景里可以用 `jq` 过滤掉 UNKNOWN 重跑：

```bash
domain-check --file domains.txt --json --yes | \
  jq -r '.[] | select(.available == null) | .domain' > retry.txt
domain-check --file retry.txt --json --yes
```

WHOIS 解析质量因注册局而异。gTLD（`.com`、`.org` 等）的 WHOIS 格式相对统一，`domain-check` 的正则库覆盖良好。小众 ccTLD 的 WHOIS 格式可能没适配，输出 UNKNOWN。如果遇到这种情况，可以提 issue 反馈，作者会补充正则模式。

RDAP 404 的处理在 v1.0.2 里做了修复（issue #30）。早期版本会把 RDAP 404 直接判定为 AVAILABLE，但某些 RDAP 服务器在内部错误时也返回 404，导致误报。现在 404 被当作 inconclusive，defer 到 WHOIS 二次确认，牺牲一点速度换准确性。

## 学习路径与资源

刚接触域名检查和 RDAP/WHOIS 的开发者，建议按这个顺序看：

1. **RFC 3912**（WHOIS）：3 页，10 分钟读完，理解协议有多简单
2. **RFC 7483**（RDAP JSON 响应）：看 `rdapConformance`、`events`、`status` 字段定义
3. **IANA RDAP Bootstrap 注册表**：`https://data.iana.org/rdap/dns.json`，看看 TLD 到 RDAP 服务器的映射长什么样
4. **`domain-check` 源码**：`domain-check-lib/src/` 目录，重点看 `rdap.rs` 和 `whois.rs` 的降级逻辑

工具本身的文档：

- GitHub 仓库：[github.com/saidutt46/domain-check](https://github.com/saidutt46/domain-check)
- CLI 完整参考：[docs/CLI.md](https://github.com/saidutt46/domain-check/blob/main/docs/CLI.md)
- Rust 库文档：[docs.rs/domain-check-lib](https://docs.rs/domain-check-lib)
- MCP Server 配置：[domain-check-mcp/README.md](https://github.com/saidutt46/domain-check/blob/main/domain-check-mcp/README.md)
- 自动化指南：[docs/AUTOMATION.md](https://github.com/saidutt46/domain-check/blob/main/docs/AUTOMATION.md)
- FAQ：[docs/FAQ.md](https://github.com/saidutt46/domain-check/blob/main/docs/FAQ.md)

相关工具对比：

- `subfinder`：子域名发现，爬证书透明度日志和被动 DNS
- `massdns`：DNS 解析引擎，适合暴力枚举，速度比 RDAP/WHOIS 快两个数量级
- `amass`：综合 OSINT 工具，子域名 + 网络拓扑
- DomainTools / WhoisXML API：商业 WHOIS 历史、威胁情报

`domain-check` 的定位是这些工具的补充，不是替代。理解了 RDAP/WHOIS 的协议层差异和 `domain-check` 的双协议降级策略，你就能在合适的场景选对工具，而不是拿 RDAP 客户端去跑子域名枚举这种事倍功半的活。
