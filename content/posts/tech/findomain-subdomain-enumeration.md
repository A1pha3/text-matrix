---
title: "Findomain：5秒挖掘8万子域名——域名发现与监控从入门到精通"
date: "2026-04-14T22:10:00+08:00"
slug: "findomain-subdomain-enumeration"
description: "Findomain 是 3.7K Stars 的极速子域名发现工具，基于 Rust 实现，支持 14+ 数据源（Certspotter、Crt.sh、Virustotal 等）。5.5秒发现 84,110 个子域名，内置 Discord/Slack/Telegram Webhook 监控告警，支持 DNS over TLS 和暴力枚举。"
draft: false
categories: ["技术笔记"]
tags: ["安全", "BugBounty", "OSINT", "子域名枚举", "Findomain", "Rust"]
---

# Findomain：用证书透明日志做被动子域名发现

> **快速信息卡**
>
> | 项目 | 信息 |
> |------|------|
> | GitHub | [Findomain/Findomain](https://github.com/Findomain/Findomain) |
> | Stars | 3,761+ |
> | Forks | 395+ |
> | License | GPL-3.0 |
> | 语言 | Rust |
> | 最后更新 | 2026-06-25 |

在子域名发现这件事上，工具可以分成两类：一类向目标发包，一类不向目标发包。Findomain 属于后者，它解决的是"被动子域名发现"问题——通过查询公开的证书透明日志（Certificate Transparency Logs，CT）和第三方威胁情报 API，把已经存在过的子域名捞回来，全过程不向目标发送任何探测包。它不解决"主动枚举"问题，也就是不能用字典去硬撞 DNS。

这种被动定位对应几类典型场景：Bug Bounty 猎人在 recon 阶段需要快速摸清目标资产面；企业安全团队需要监控自有域名的新子域名出现；红队在打点前需要被动收集而不暴露指纹。这些场景的共同诉求是快、广、不留痕。代价也明确——召回率受限于数据源，一个从未申请过证书、也从未被任何威胁情报平台收录的内网子域名，Findomain 发现不了。

## 学习目标

读完这篇，你将能：

- 区分被动子域名发现和主动枚举的边界，并说明 CT 日志为什么是被动发现的首选数据源。
- 解释 Merkle Tree 如何保证 CT 日志的不可篡改性和可审计性，以及 O(log N) 验证的具体含义。
- 描述 Findomain 用 tokio 异步运行时实现多数据源并发查询的工程机制，包括 15 秒超时上限的来源。
- 复现 `findomain -t example.com` 从参数解析到结果输出的完整流程，指出通配符检测和 HashSet 去重的位置。
- 设计一条 Findomain + dnsgen + massdns 的组合 recon 流水线，并说明每一步解决的是哪类子域名发现问题。

## 目录

- [子域名发现的三条技术路线](#子域名发现的三条技术路线)
- [证书透明日志：为什么是首选数据源](#证书透明日志为什么是首选数据源)
- [Findomain 的工程实现](#findomain-的工程实现)
- [数据源：覆盖差异和 API 限制](#数据源覆盖差异和-api-限制)
- [性能数据：5.5 秒 84110 子域名意味着什么](#性能数据55-秒-84110-子域名意味着什么)
- [任务如何流过系统：findomain -t example.com 的完整流程](#任务如何流过系统findomain--t-examplecom-的完整流程)
- [与 massdns、dnsgen 的组合使用](#与-massdnsdnsgen-的组合使用)
- [子域名监控：新子域名往往意味着新攻击面](#子域名监控新子域名往往意味着新攻击面)
- [安装与基本使用](#安装与基本使用)
- [与其他被动发现工具的对比](#与其他被动发现工具的对比)
- [采用顺序与决策建议](#采用顺序与决策建议)
- [实战技巧](#实战技巧)
- [常见问题](#常见问题)
- [练习与自测](#练习与自测)
- [学习路径和资源](#学习路径和资源)

后续章节按"技术路线 → CT 日志机制 → 工程实现 → 数据源差异 → 性能解读 → 任务流 → 工具组合 → 监控 → 安装 → 对比 → 采用建议 → 实战 → FAQ → 自测 → 资源"的顺序展开。

## 子域名发现的三条技术路线

在进入 Findomain 之前，先把子域名发现的整体技术版图理清楚。目前主流的做法有三条路线，它们的边界很明确。

第一条是**证书透明日志查询**。CA 在签发证书时必须把证书提交到公开的 CT 日志，否则主流浏览器会拒绝信任。这意味着任何申请过 TLS 证书的子域名都会在 CT 日志里留下记录，而且是公开可查的。这条路线的特点是免费、无需授权、覆盖广，但只能发现"有证书的"子域名。

第二条是**第三方 API 聚合**。Virustotal、SecurityTrails、Urlscan.io 这类平台长期爬取和聚合互联网资产数据，它们的数据库里往往有大量历史 DNS 记录和扫描结果。这条路线能补充 CT 日志覆盖不到的部分（比如曾经解析过但没证书的子域名），但受限于 API 的速率限制和数据新鲜度，部分 API 还需要付费 key。

第三条是**暴力枚举**。拿一个字典文件去拼装候选子域名，然后逐个发 DNS 查询看是否解析。这条路线理论上能发现任何"曾经或正在解析"的子域名，包括内网子域名，但代价是流量大、噪音多、容易被目标感知。massdns 是这条路线的代表工具。

Findomain 的策略是前两条路线的组合：以 CT 日志为主力，辅以多个第三方 API，把暴力枚举作为可选补充。这个组合在大多数 recon 场景下能拿到 80% 以上的子域名，而且不向目标发包。

## 证书透明日志：为什么是首选数据源

要理解 Findomain 为什么把 CT 日志当主力，得先搞清楚 CT 日志到底是什么。

### CT 日志的架构

证书透明（Certificate Transparency）是 Google 在 2013 年主导推动的开放框架，目的是解决 CA 错误签发或恶意签发证书的问题。在 CT 出现之前，如果一个 CA 被攻破或者操作失误，签发了一张 `*.google.com` 的证书给攻击者，外界几乎无法发现。CT 改变了这个流程：它要求 CA 把签发的每一张证书都提交到公开的、只能追加（append-only）的日志里，否则 Chrome 等主流浏览器会拒绝信任这张证书。

CT 日志的核心数据结构是 Merkle Tree（默克尔树）。每张证书被提交后，日志会把它作为一个叶子节点插入树中，然后重新计算从该叶子到根的哈希路径。整个树的根哈希会被公开发布并签名。这种结构保证了两个性质：第一，日志只能追加不能修改历史记录，因为任何修改都会改变根哈希；第二，任何人都可以通过验证一条 Merkle 路径来确认某张证书确实在日志里。这两个性质让 CT 日志成为可公开审计、不可篡改的证书数据库。

具体来说，Merkle Tree 的验证过程是这样的。假设日志里有 N 张证书，每张证书是一个叶子节点。叶子节点两两配对做哈希，得到 N/2 个中间节点；中间节点再两两配对做哈希，直到最后只剩一个根节点。要验证某张证书 C 确实在日志里，你只需要提供从 C 到根路径上的兄弟节点哈希（这叫 Merkle proof），然后本地重新计算根哈希，看是否和公开的根哈希一致。这个验证过程是 O(log N) 的，即使日志里有几亿张证书，验证也只需要几十次哈希计算。

这个设计对子域名发现的意义在于：CT 日志是公开的、可程序化查询的、不可篡改的。任何人都可以拉取整个日志或者查询特定域名的记录，不需要授权，不需要付费。这就是为什么 CT 日志成为被动子域名发现的首选数据源。

CT 日志生态里有几个角色分工。日志运营商（如 Google、Cloudflare、Sectigo）负责维护日志本身，接收 CA 提交的证书并更新 Merkle Tree。监控者（monitor）定期拉取日志的根哈希和新增条目，检测是否有可疑证书被签发（比如监控者发现了一张不属于域名所有者的证书，就可以告警）。审计者（auditor）验证日志的一致性，确保日志运营商没有篡改历史记录。这三个角色共同保证了 CT 日志的可信度。对于 Findomain 这类工具来说，它扮演的是"查询者"角色——不参与日志的维护和验证，只查询日志内容来发现子域名。

### CT 日志的查询入口

CT 日志本身是分布式的，全球有多个日志运营商（Google、Cloudflare、Sectigo 等）各自维护日志。要查询某个域名的证书记录，不需要直接去遍历这些日志，有几个聚合查询入口可用。

`crt.sh` 是最常用的入口，由 Sectigo（原 Comodo CA）维护。它把多个 CT 日志的证书数据聚合到一个 PostgreSQL 数据库里，提供 SQL 查询接口和 Web 界面。访问 `https://crt.sh/?q=example.com` 就能看到所有包含 `example.com` 的证书记录，包括证书的 SAN（Subject Alternative Name）字段里列出的所有子域名。crt.sh 免费、无需 API key、覆盖最广，是 Findomain 默认的第一个数据源。

crt.sh 还提供 JSON 输出接口，加 `&output=json` 参数就能拿到结构化数据。每条记录包含证书的 `issuer_ca_id`、`common_name`、`name_value`（SAN 列表，换行分隔）、`entry_timestamp`、`not_before`、`not_after` 等字段。Findomain 解析的就是 `name_value` 字段，把它按换行符拆开就得到子域名列表。

`Certspotter` 由 SSLMate 提供，是另一个 CT 日志监控和查询服务。它提供 REST API，免费层每小时可以查询 100 次，付费层没有限制。Certspotter 的优势是 API 响应结构化、适合程序化调用，缺点是免费层有速率限制。它的 API 端点是 `https://api.certspotter.com/v1/issuances?domain=<domain>&include_subdomains=true&expand=dns_names`，返回的 JSON 里每条记录对应一张证书，`dns_names` 字段是子域名数组。

`Facebook CT` 是 Facebook 维护的 CT 日志查询接口，需要登录 Facebook 账号才能使用。它的覆盖范围和 crt.sh 有重叠但也有差异，作为补充数据源有价值。Facebook CT 的 API 需要通过 Facebook 的应用认证流程获取 access token，配置比 crt.sh 复杂，但能补充一些 crt.sh 索引延迟的记录。

除了这三个，还有 `CTSearch`（Entrust 维护）、`Censys`（提供 CT 日志搜索作为其更广泛互联网扫描服务的一部分）等入口。Findomain 接入了其中几个，把它们的结果合并去重。

### CT 日志的边界

CT 日志不是万能的。它只能发现"申请过证书的"子域名。如果一个子域名只跑了 HTTP（没上 TLS），或者用了自签名证书，或者只在内网解析，CT 日志里就没有它的记录。这就是为什么 Findomain 还要接入 Virustotal、SecurityTrails 这类 API——它们能补充 CT 日志覆盖不到的部分，比如曾经被扫描器扫到过但没证书的子域名。

还有一个细节：CT 日志的索引有延迟。CA 签发证书后，需要把证书提交到 CT 日志，日志运营商把它加入 Merkle Tree 后才会出现在查询接口里。这个延迟通常是几小时到一天，极端情况下可能更长。所以 CT 日志查不到"刚刚签发的"证书，只能查到"已经索引的"证书。

CT 日志的边界在这里：它免费、广覆盖、无需授权，是首选数据源，但不是唯一数据源。Findomain 的价值在于把多个数据源的结果去重合并，给出一个尽可能完整的子域名清单。

## Findomain 的工程实现

Findomain 用 Rust 写成（GitHub 仓库里 Rust 占 93.7%），这个选择不是偶然。子域名发现是一个典型的 I/O 密集型任务——大部分时间花在等 HTTP 响应和 DNS 解析上，CPU 计算很少。Rust 的异步模型（基于 tokio 运行时）在这种场景下能提供接近 C 的性能，同时保持内存安全。

### Rust 异步模型与并发控制

Rust 的异步模型基于 `Future` trait 和 async/await 语法。和 Go 的 goroutine 不同，Rust 的异步任务是协作式调度的，由 tokio 运行时管理。一个异步任务在等待 I/O 时会主动让出执行权，运行时把 CPU 让给其他就绪的任务。这种模型在 I/O 密集型场景下非常高效——单个线程可以并发处理成千上万个连接，没有线程切换开销。

Findomain 利用这个模型实现了数据源查询的全并行。它对每个启用的数据源启动一个异步任务，所有任务同时跑在 tokio 运行时上。当某个任务在等 HTTP 响应时，其他任务可以继续处理已经返回的响应。这意味着如果你接入了 10 个数据源，Findomain 会同时向这 10 个 API 发请求，而不是一个接一个。这是它能做到"最大 15 秒超时"的基础——15 秒是最慢的那个 API 的超时时间，而不是所有 API 查询时间之和。

HTTP 客户端用的是 `reqwest` crate（Rust 的生态里 HTTP 客户端的事实标准）。reqwest 支持连接池复用、HTTP/2、超时配置，这些对 Findomain 的性能都很关键。连接池复用避免了每次请求都重新建立 TCP 连接和 TLS 握手；HTTP/2 的多路复用让多个请求可以共享一个连接；超时配置保证单个 API 不会拖垮整体。

### 子域名解析的并行化

子域名解析是另一个并行化点。Findomain 在拿到子域名清单后，会并行做 DNS 解析来验证哪些子域名当前是存活的。根据 README 的说明，在良好的网络条件下，Findomain 每分钟可以解析约 3500 个子域名。这个数字受 `--threads` 参数控制，默认值是 60+ 每秒。

DNS 解析用的是 `rusolver`（也是 Findomain 作者 Edu4rdSHL 写的异步 DNS 解析库）。rusolver 是一个纯 Rust 的异步 DNS 客户端，支持自定义 DNS 服务器、UDP/TCP/DoT 协议。它的设计目标是高并发解析，和 Findomain 的需求匹配。

Findomain 还内置了通配符检测。当一个域名配置了通配符 DNS（比如 `*.example.com` 解析到同一个 IP），任何随机子域名都会解析成功，这会导致误报。Findomain 会在解析前先检测通配符——向几个随机生成的子域名（比如 `a1b2c3d4e5.example.com`）发查询，如果它们都解析到同一个 IP，就判定配置了通配符，后续解析结果会过滤掉这个 IP。这个检测避免了把随机字符串当成有效子域名。

### 速率限制处理

第三方 API 普遍有速率限制。Virustotal 免费 key 每分钟只能查几次，SecurityTrails 付费 key 也有每分钟请求数上限。Findomain 的处理方式是：对需要 key 的 API，只在用户显式启用 `--include-key-api` 时才查询；对免费 API，依赖并行查询和超时机制来规避速率问题。如果某个 API 触发了速率限制，Findomain 会在 15 秒超时后跳过它，继续处理其他数据源的结果。

这种处理方式的代价是：在速率限制严格的场景下，单个数据源可能拿不到完整结果。这也是为什么 Findomain 接入了 14+ 个数据源——冗余覆盖，单个数据源失败不影响整体召回。从工程角度看，这是一个典型的"用冗余换可用性"的取舍：宁可多查几个数据源，也不在单个数据源的速率限制重试上浪费时间。

### 错误处理与配置管理

Findomain 的错误处理策略是"失败隔离"。每个数据源的查询是独立的异步任务，一个任务失败（网络错误、API 返回错误码、JSON 解析失败）不会影响其他任务。失败的任务会被记录到日志，然后跳过，最终结果只包含成功返回的数据源的子域名。这种设计让 Findomain 在部分数据源不可用时仍然能给出结果，而不是整体失败。

配置管理上，Findomain 支持多种配置文件格式（TOML、JSON、HJSON、INI、YAML），这是为了适配不同用户的偏好。配置文件里主要存放 API token 和一些默认参数。Findomain 也支持环境变量传入 API token，这在 CI/CD 环境里更方便——不需要把 token 写进文件，直接从环境变量读取。

一个值得注意的细节是 Findomain 对 Facebook CT 的配置。Facebook CT 需要 Facebook 账号的邮箱和密码，而不是标准的 API token。这是因为 Facebook 的 CT 查询接口是基于会话认证的，不是 OAuth token 认证。配置时需要填 `facebook_ct_email` 和 `facebook_ct_password` 两个字段。这种认证方式的安全性值得注意——你的 Facebook 凭据会存在 Findomain 的配置文件里，建议只在受控环境使用，并且配置文件权限设为 600。

## 数据源：覆盖差异和 API 限制

Findomain 支持的数据源列表（来自项目 README）包括以下这些。它们的覆盖差异和限制直接决定 Findomain 在不同场景下的召回率。

**CT 日志类数据源**：Crt.sh（无需 key，覆盖最广，是 Findomain 的默认主力）、Certspotter（无需 key，免费层每小时 100 次）、Facebook CT（需要 Facebook 登录）、CTSearch（Entrust 维护）。这类数据源的覆盖范围取决于它们聚合了哪些 CT 日志，理论上应该高度重叠，但实际查询接口的索引延迟和查询能力有差异。Crt.sh 因为是 SQL 查询接口，能做模糊匹配和历史回溯，覆盖最完整。

**威胁情报类数据源**：Virustotal（免费 key 可用，但有严格速率限制；付费 key 无限制）、Threatcrowd、Threatminer、C99（需要付费 key）。这类数据源的价值在于它们聚合了多源数据——Virustotal 不仅有自己的扫描数据，还接入了大量第三方提交，能发现 CT 日志覆盖不到的子域名。比如某个子域名曾经被某个安全研究员提交到 Virustotal 做扫描，即使它没有证书，也会出现在 Virustotal 的数据库里。

**DNS 历史类数据源**：SecurityTrails（需要付费 key）、Bufferover。这类数据源保存的是历史 DNS 解析记录，能发现曾经解析过但现在已经不存在的子域名。对于资产盘点和历史攻击面分析特别有用。比如一个子域名 `old-admin.example.com` 曾经解析过，后来下线了，CT 日志里可能没有（如果没申请证书），但 SecurityTrails 的历史记录里会有。

**其他数据源**：Sublist3r（聚合多个来源的子域名）、AnubisDB、Urlscan.io（网页扫描结果）。这些数据源的覆盖比较杂，作为补充。Urlscan.io 的特点是它记录的是用户主动提交的网页扫描结果，所以能发现一些被研究人员扫描过的子域名。

需要 key 的数据源（README 里标 `**` 的）包括 Facebook、Virustotal with apikey、SecurityTrails、C99。要启用这些数据源，需要在配置文件里填入对应的 API token。Findomain 支持 TOML、JSON、HJSON、INI、YAML 格式的配置文件。

实际使用中，Crt.sh + Certspotter + Virustotal（免费 key）这三个免费数据源就能拿到大部分子域名。要追求极限召回，再加上 SecurityTrails 和付费 Virustotal key 会有明显提升。从作者在 README 和 Medium 文章里给出的经验比例看，Crt.sh 通常能贡献 60%-70% 的子域名，其他数据源补充剩下的 30%-40%。这个比例的前提是目标域名有一定历史且申请过较多证书；对新建或小众域名，Crt.sh 的占比会下降，第三方 API 的补充作用更明显。

## 性能数据：5.5 秒 84110 子域名意味着什么

Findomain 的 README 里有一个常被引用的性能数据：5.5 秒发现 84110 个子域名。这个数字需要放在上下文里理解，不能直接拿来当通用基准。

测试条件来自 README：测试目标是 `aol.com`，测试环境是一台 BlackArch 虚拟机（KVM/QEMU，Intel Skylake 4 核 2.904GHz，3943MiB 内存），用 Linux `time` 命令测量，结果是 `real 0m5.515s`，CPU 和内存使用都标注为 "Very Low"。README 同时说明，这个测试用的是 Findomain 的 premium 版本，free 版本的表现可能不同。

这个数字测的是什么？它测的是 Findomain 向所有已配置数据源发起查询、拿到结果、去重合并的端到端时间。它不包含 DNS 解析验证的时间——84110 是"发现的子域名数量"，不是"解析成功的子域名数量"。如果加上 `--resolve` 选项做 DNS 验证，时间会显著增加，因为每分钟只能解析约 3500 个，84110 个子域名全部解析需要 20 分钟以上。

这个数字能推出什么？它能说明 Findomain 的 API 并发查询设计是有效的——15 秒超时上限内完成了所有数据源的查询。它不能推出 Findomain 在你的目标域名上的表现，因为 `aol.com` 是一个老牌大型域名，CT 日志和威胁情报平台对它的覆盖非常完整。换成一个中等规模的域名，发现数量会少很多，但时间也会更短。

这个数字不能推出什么？它不能推出 Findomain 比 massdns 快——两者测的不是同一件事。massdns 测的是 DNS 解析吞吐，Findomain 测的是 API 查询延迟。拿这两个数字直接对比没有意义。它也不能推出 Findomain 在所有网络环境下都这么快——如果你的网络到 crt.sh 的延迟很高，或者某个 API 触发了速率限制，时间会拉长。

正确的理解方式是：5.5 秒这个数字反映了 Findomain 在理想网络条件下、对高覆盖度域名的 API 查询延迟下限。实际使用中，对中等规模域名，Findomain 的典型耗时在 5-15 秒之间（受最慢 API 的影响）。

## 任务如何流过系统：findomain -t example.com 的完整流程

把前面的机制串起来，看一个完整的任务流程。假设你执行 `findomain -t example.com`，Findomain 内部会发生这些事。

第一步，Findomain 解析命令行参数，确定目标是 `example.com`。如果配置文件里填了 API token，会加载这些 token；如果没有，只用免费数据源。同时初始化 tokio 运行时，准备异步任务调度。

第二步，Findomain 同时向所有启用的数据源发起查询。对于 Crt.sh，它会请求 `https://crt.sh/?q=%25.example.com&output=json`（`%25` 是 URL 编码的 `%`，匹配 `*.example.com`），拿到一个 JSON 数组，里面每条记录对应一张证书，证书的 `name_value` 字段包含所有 SAN 子域名。对于 Certspotter，它请求 `https://api.certspotter.com/v1/issuances?domain=example.com&include_subdomains=true&expand=dns_names`。对于 Virustotal，它请求 `https://www.virustotal.com/v2/domain/report?domain=example.com&apikey=<key>`。这些请求是并行的，Findomain 不会等一个完成再发下一个——所有请求几乎在同一时刻发出，然后异步等待响应。

第三步，每个数据源的响应回来后，Findomain 解析响应体，提取子域名。Crt.sh 的响应里可能有 `example.com`、`www.example.com`、`api.example.com` 等等。Findomain 把这些子域名加入一个全局的 HashSet，自动去重。如果同一个子域名被多个数据源返回（比如 `www.example.com` 同时出现在 Crt.sh 和 Virustotal 的结果里），HashSet 保证它只出现一次。这个去重是实时进行的——每个数据源的响应一回来就立即合并到 HashSet，不需要等所有数据源都返回。

第四步，所有数据源都返回或者超时（最长 15 秒）后，Findomain 得到一个去重后的子域名清单。如果你没有指定 `--resolve`，Findomain 直接输出这个清单，任务结束。这就是 5.5 秒那个数字测量的范围。

第五步，如果你指定了 `--resolve`，Findomain 会对清单里的每个子域名做 DNS 解析。它会先检测通配符 DNS——向几个随机子域名（比如 `random123abc.example.com`）发查询，如果都解析到同一个 IP，说明配置了通配符，后续解析结果需要过滤掉这个 IP。然后它用 `--threads` 指定的并发数（默认 60+ 每秒）并行解析所有子域名，只保留解析成功的。如果你启用了 DNS over TLS（`--dot` 参数），解析会走 DoT 通道，加密 DNS 查询，避免被中间人窥探。

第六步，输出结果。默认输出到 stdout，每行一个子域名。如果指定了 `-o results.txt`，写入文件。如果指定了 `--json`，输出 JSON 格式，包含子域名和对应的 IP。如果指定了 `--ip`，额外输出每个子域名解析到的 IP 地址。

整个流程的关键设计点有三个：查询阶段全并行、去重用 HashSet、解析阶段有通配符检测。查询阶段的并行性让它能在 15 秒内完成所有数据源的查询；HashSet 去重让结果干净；通配符检测避免了把随机字符串当成有效子域名的误报。这三点共同支撑了 Findomain 在中等规模域名上 5-15 秒的典型耗时区间。

## 与 massdns、dnsgen 的组合使用

Findomain 拿到的是"曾经存在过"的子域名，但攻击面不止于此。一个成熟的 recon 流程通常是三个工具的组合：Findomain 发现种子子域名，dnsgen 基于种子生成变形候选，massdns 对候选做高速 DNS 解析验证。

dnsgen 的工作原理是拿种子子域名做模式变形。比如种子里有 `api.example.com` 和 `api-v2.example.com`，dnsgen 会生成 `api-v3.example.com`、`api2.example.com`、`api-internal.example.com` 这类候选。它能识别常见的命名模式（数字后缀、环境前缀如 dev/staging/prod、协议前缀如 api/admin/portal），然后排列组合生成大量候选子域名。dnsgen 的变形规则包括：在已有子域名前后加数字、加环境前缀、加协议后缀、替换分隔符（`-` 换 `_`）、基于词库的智能变形等。

massdns 的工作原理是高速 DNS 解析。它用自定义的网络栈绕过操作系统的 DNS 解析限制，能并发解析数万个域名。它的吞吐量远高于 Findomain 内置的解析器，因为它是专门为 DNS 解析优化的，而 Findomain 的解析只是辅助功能。massdns 的核心技巧是：自己构造 DNS 查询包，用 raw socket 发送，绕过 libc 的 DNS 解析器（libc 的解析器有线程数限制和缓存开销），直接和递归 DNS 服务器通信。

组合使用的完整流程：

```bash
# 第一步：Findomain 被动发现种子子域名
findomain -t example.com -o subdomains.txt

# 第二步：dnsgen 基于种子生成变形候选
dnsgen subdomains.txt > mutations.txt

# 第三步：massdns 高速解析验证候选
massdns -r resolvers.txt -t A -o S mutations.txt > resolved.txt

# 第四步：从 massdns 输出里提取解析成功的子域名
awk '{print $1}' resolved.txt | sed 's/\.$//' > live_subdomains.txt
```

这个组合的逻辑是：Findomain 解决"已知子域名"的发现问题，dnsgen + massdns 解决"未知但可能存在的子域名"的发现问题。前者快但召回有限，后者慢但能发现 Findomain 漏掉的子域名。两者解决的是不同子集的问题，组合使用才能覆盖更完整的攻击面。

实际使用中，Findomain 的结果质量决定了 dnsgen 的种子质量。如果 Findomain 漏掉了一个关键子域名（比如 `internal-api.example.com`），dnsgen 就不会生成 `internal-api-v2.example.com` 这类变形。所以在大规模 recon 里，通常会同时跑 Findomain、subfinder、amass 这几个被动工具，把结果合并后再喂给 dnsgen。

一个更完整的 recon 流水线可能是这样的：

```bash
# 多工具被动发现，结果合并
findomain -t example.com -o findomain.txt
subfinder -d example.com -o subfinder.txt
amass enum -passive -d example.com -o amass.txt
cat findomain.txt subfinder.txt amass.txt | sort -u > seeds.txt

# dnsgen 变形 + massdns 解析
dnsgen seeds.txt > mutations.txt
massdns -r resolvers.txt -t A -o S mutations.txt | \
  awk '{print $1}' | sed 's/\.$//' | sort -u > live.txt

# HTTP 存活验证
cat live.txt | httprobe -c 50 > live_http.txt

# 漏洞扫描
nuclei -l live_http.txt -t cves/ -t exposures/
```

这个流水线里，Findomain 占的位置是"快速被动发现的第一步"——5 秒内拿到第一批种子，让后续步骤可以尽早开始。subfinder 和 amass 会补充更多种子，但它们更慢（amass 的被动枚举可能要几分钟）。

## 子域名监控：新子域名往往意味着新攻击面

Findomain 的监控功能（`--monitoring`）解决的是另一个问题：持续监控某个域名，当出现新子域名时通过 Webhook 告警。这个功能的价值在于，新子域名的出现往往意味着目标开了新业务、部署了新服务，而这些新服务往往还没经过完整的安全测试。

典型的监控场景：一家公司在 `example.com` 下新部署了 `staging-checkout.example.com`，用于测试新的支付流程。这个 staging 环境可能用了弱认证、暴露了调试接口、或者运行着未打补丁的依赖。对 Bug Bounty 猎人来说，这种新出现的 staging 环境是高价值目标——它比生产环境更可能有问题，而且往往被忽视。对企业安全团队来说，监控自有域名的新子域名出现，等于监控了新的攻击面。

Findomain 的监控实现是周期性跑一次完整的子域名发现，把结果和上一次的结果做 diff，新增的部分通过 Webhook 推送。它支持 Discord、Slack、Telegram 三个渠道：

```bash
findomain -t example.com --monitoring \
  --webhook-url "https://discord.com/api/webhooks/xxx" \
  --target example.com
```

这个机制的局限是：它依赖 Findomain 被定期触发（通常配合 cron），不是实时监控。CT 日志本身有索引延迟（从证书签发到可查询通常是几小时到一天），所以监控的端到端延迟是 CT 日志延迟加上 cron 间隔。对于需要分钟级告警的场景，Findomain 的监控不够实时，但对于日常 recon 已经够用。

一个典型的 cron 配置是每小时跑一次：

```bash
# crontab
0 * * * * /usr/local/bin/findomain -t example.com --monitoring \
  --webhook-url "https://discord.com/api/webhooks/xxx" \
  --target example.com >> /var/log/findomain.log 2>&1
```

需要注意的是，Findomain 项目在 2025 年 9 月的提交里提到 "Monitoring service was shut down"，这指的是官方托管的监控服务关闭，本地 `--monitoring` 配合 Webhook 的功能仍然可用，只是需要用户自己搭 cron 调度。官方托管的监控服务原本提供云端调度和结果存储，关闭后这些需要用户自己实现。

## 安装与基本使用

Findomain 提供多平台预编译二进制。Linux 和 macOS 的安装方式：

```bash
# Linux
wget https://github.com/Findomain/Findomain/releases/latest/download/findomain-linux.zip
unzip findomain-linux.zip
chmod +x findomain
sudo mv findomain /usr/local/bin/

# macOS
brew install findomain
```

基本使用命令：

```bash
# 基础发现（只用免费数据源）
findomain -t example.com

# 使用所有 API（包括需要 key 的）
findomain -t example.com --include-key-api

# 输出 JSON 格式
findomain -t example.com --json

# 保存到文件
findomain -t example.com -o results.txt

# 解析验证子域名是否存活
findomain -t example.com --resolve

# 启用 DNS over TLS
findomain -t example.com --resolve --dot

# 从文件读取多个目标
findomain -f targets.txt

# 暴力枚举模式（使用字典）
findomain -t example.com --bruteforce -w wordlist.txt
```

配置 API token 时，Findomain 支持多种配置文件格式。以 TOML 为例，配置文件里需要列出各个数据源的 token：

```toml
# Findomain 配置文件示例
[findomain]
virustotal_api_key = "your_virustotal_key"
securitytrails_api_key = "your_securitytrails_key"
c99_api_key = "your_c99_key"
facebook_ct_email = "your_facebook_email"
facebook_ct_password = "your_facebook_password"
```

配置文件路径可以通过 `--config` 参数指定，默认会查找 `~/.config/findomain/config.toml`。出于安全考虑，建议把配置文件的权限设置为 600（只有所有者可读写），避免 API token 泄露。

## 与其他被动发现工具的对比

Findomain 不是唯一的被动子域名发现工具。在这个领域里，subfinder 和 amass 是另外两个主流选择。三者各有侧重，选错工具会让 recon 流水线的某一段变慢或漏召回。

`subfinder` 是 ProjectDiscovery 出品的被动子域名发现工具，也是用 Go 写的。它的设计哲学和 Findomain 类似——多 API 聚合，不做主动枚举。subfinder 的数据源列表和 Findomain 高度重叠，但它和 ProjectDiscovery 生态（httpx、nuclei、subjs 等）无缝集成，管道操作很顺畅。subfinder 的性能比 Findomain 稍慢（Go 的 GC 开销），但差距不大。

`amass` 是 OWASP 项目的子域名发现工具，功能最全面。它集成了被动发现、主动枚举、DNS 图分析、SSL 证书查询等多种技术。amass 的被动枚举比 Findomain 和 subfinder 更慢（因为它会做更深入的数据源查询和交叉验证），但召回率最高。amass 还能绘制子域名之间的关系图，适合做深度资产测绘。

三者侧重不同：Findomain 用 Rust 实现，启动快、内存占用低，适合放在 recon 流水线最前面快速拿种子；subfinder 和 ProjectDiscovery 工具链配合顺畅，适合后续管道操作；amass 做更深入的数据源交叉验证和图分析，适合需要完整资产测绘的场景。实际使用中，三者结果合并是常见做法——每个工具的数据源和查询策略有差异，合并能拿到最全的子域名清单。

从性能角度看，Findomain 的 Rust 实现让它在内存占用和启动时间上有优势。一个典型的对比（来自作者 README 和社区实测，目标为同一中等规模域名）：Findomain 跑完需要 5-10 秒，subfinder 需要 10-20 秒，amass 被动模式需要 1-5 分钟。召回率上，amass 通常能比 Findomain 多发现 5%-15% 的子域名，具体幅度取决于目标域名的特征——老牌大型域名差异小，新建小众域名差异大。

## 采用边界：什么时候用 Findomain，什么时候用别的

Findomain 的能力边界由它的数据源决定。下面按场景说明它能不能用、为什么、用不上时该换什么。

**Bug Bounty recon 阶段**是 Findomain 的主场。5 秒级响应让它适合作为 recon 流水线的第一步，先拿到一批种子再决定后续投入。**企业自有资产监控**也合适，配合 cron 定期跑，新子域名通过 Webhook 告警。**红队被动信息收集**同样适用——Findomain 全程不碰目标服务器，不会触发目标的入侵检测。**大规模域名清单的初步筛选**是另一个典型用法，从几千个域名里用 `--quiet` 模式快速过滤出有子域名的目标。

但有几类问题 Findomain 解决不了。**内网子域名或无证书子域名**的发现就是其一，CT 日志和威胁情报 API 都覆盖不到这部分，得换 massdns 暴力枚举。**实时监控新子域名出现**也做不到，Findomain 的监控是周期性的，CT 日志本身也有索引延迟，端到端延迟在小时级，分钟级告警需要其他手段。**子域名接管（subdomain takeover）检测**不在 Findomain 的能力范围内，它只发现子域名，不检测 CNAME 悬挂，结果要喂给 subjack 或 nuclei 的 takeover 模板。**对召回率要求极高的场景**下，Findomain 单独跑可能不够，目标域名很新或很小众时 CT 日志和威胁情报平台可能都没有记录，需要 subfinder、amass 多工具组合，加上 dnsgen + massdns 的暴力变形。**非标准端口服务发现**也不是 Findomain 的事，它只发现子域名不做端口扫描，端口扫描要靠 nmap 或 rustscan。

## 采用顺序与决策建议

把 Findomain 放进 recon 流水线时，建议按下面的顺序决策。

**第一步：判断任务是否需要被动发现。** 如果任务允许向目标发包（比如自己公司的资产盘点），可以直接用主动枚举工具，Findomain 不是必需。如果任务要求不暴露指纹（红队、Bug Bounty 初期），Findomain 是首选。

**第二步：判断目标域名特征。** 老牌大型域名（如 `aol.com` 这种）CT 日志覆盖完整，Findomain 单独跑就能拿到大部分子域名。新建或小众域名 CT 日志记录少，必须配合 subfinder、amass 多工具合并，再喂给 dnsgen + massdns 做变形枚举。

**第三步：判断是否需要监控。** 一次性 recon 用 `findomain -t` 就够。持续监控用 `--monitoring` 配合 cron 和 Webhook，但要接受小时级延迟。需要分钟级告警的场景，Findomain 不合适，得考虑直接监控 DNS 区域传送或用其他实时方案。

**第四步：判断召回率要求。** Bug Bounty 初期摸底，Findomain + subfinder 合并通常够用。要做完整资产测绘或合规审计，必须加上 amass 被动模式，再跑 dnsgen + massdns 主动变形。

**第五步：组装流水线。** 典型顺序是：被动 recon 第一步用 Findomain（快）+ subfinder（广）+ amass（深），三者结果合并去重；主动枚举第二步用 dnsgen 变形 + massdns 解析，补充被动工具漏掉的子域名；存活验证第三步用 httpx 或 httprobe 探测 HTTP 服务，nuclei 跑漏洞模板；Takeover 检测第四步用 subjack 或 nuclei 的 takeover 模板；端口扫描第五步用 rustscan 快速扫全端口，nmap 做服务识别。

Findomain 在这条流水线里占的位置是"快速被动发现的第一步"——它的强项是 5 秒内拿到第一批种子让后续步骤尽早开始，召回率的极致要靠 amass 和 dnsgen + massdns 来补。

## 实战技巧

几个实际使用中值得注意的技巧。

**处理 crt.sh 偶尔的超时**。crt.sh 是 Findomain 的主力数据源，但它偶尔会因为负载高而响应慢。如果发现 Findomain 经常在 15 秒超时，可以单独跑 `curl 'https://crt.sh/?q=%25.example.com&output=json'` 看 crt.sh 是否正常。crt.sh 也有镜像站点，但 Findomain 默认用的是主站。

**输出格式处理**。Findomain 的默认输出是每行一个子域名，适合管道操作。但如果要做后续分析，`--json` 输出更有用，因为它包含了数据源信息。可以用 `jq` 处理 JSON 输出：

```bash
# 提取所有子域名
findomain -t example.com --json | jq -r '.subdomains[]'

# 只保留解析成功的子域名
findomain -t example.com --json --resolve | jq -r 'select(.resolved == true) | .subdomain'
```

**大规模目标处理**。如果要从文件读取几千个目标，用 `-f` 参数。但要注意 Findomain 是串行处理文件里的目标的（每个目标跑完再跑下一个），大规模场景下建议用 GNU parallel 并行化：

```bash
cat targets.txt | parallel -j 10 "findomain -t {} -o {}.txt"
```

**避免触发目标告警**。Findomain 本身不向目标发包，但如果启用了 `--resolve`，DNS 解析会发到递归 DNS 服务器，间接可能被目标感知（如果目标监控 DNS 查询日志）。要完全无感知，只用 `findomain -t example.com`，不加 `--resolve`。

**结果去重和合并**。多次跑 Findomain 或者和其他工具结果合并时，用 `sort -u` 去重：

```bash
cat findomain.txt subfinder.txt amass.txt | sort -u > all_subdomains.txt
```

**监控多域名**。如果要监控多个域名，写一个简单的 shell 脚本遍历：

```bash
#!/bin/bash
while read domain; do
  findomain -t "$domain" --monitoring \
    --webhook-url "https://discord.com/api/webhooks/xxx" \
    --target "$domain"
done < targets.txt
```

注意监控模式下，Findomain 会在本地维护一个数据库记录每个域名的历史子域名，用于 diff。这个数据库的位置可以通过 `--database` 参数指定。

## 常见问题

**Findomain 跑出来结果很少怎么办？** 首先检查是不是只用免费数据源。`findomain -t example.com` 默认只用免费数据源，要启用需要 key 的数据源，加 `--include-key-api` 并配置好 API token。其次检查网络——crt.sh 偶尔会慢，如果 15 秒超时，结果会少一大块。可以单独 `curl 'https://crt.sh/?q=%25.example.com&output=json'` 测试 crt.sh 是否正常。最后，如果目标域名很新或者很小众，CT 日志和威胁情报平台可能确实没有记录，这种情况下需要配合主动枚举工具。

**Findomain 和 subfinder 哪个好？** 两者定位不同。Findomain 用 Rust 写，启动快、内存占用低，适合作为 recon 流水线的第一步快速拿到种子。subfinder 用 Go 写，和 ProjectDiscovery 生态（httpx、nuclei）集成更好，适合后续管道操作。实际使用中两者结果合并是常见做法，因为它们的数据源和查询策略有差异，合并能提高召回率。

**监控告警延迟很高怎么办？** CT 日志本身有索引延迟（几小时到一天），这是机制限制，Findomain 无法绕过。如果对实时性要求高，需要配合其他监控手段，比如直接监控目标域名的 DNS 区域传送（如果允许）、或者用 zone transfer 监控。对于大多数 recon 场景，小时级延迟是可以接受的。

**Findomain 会暴露我的 IP 吗？** Findomain 本身不向目标发包，只向 CT 日志和第三方 API 发请求。所以目标看不到你的 IP。但你查询的第三方 API（Virustotal、SecurityTrails 等）会记录你的查询行为和 IP。如果需要匿名，走代理或者 Tor，但要注意这会显著增加延迟。

**为什么 Findomain 发现的子域名解析不出来？** CT 日志记录的是"曾经签发过证书"的子域名，不代表这个子域名现在还在用。很多子域名申请了证书但后来下线了，DNS 解析会失败。这就是为什么 `--resolve` 选项有用——它过滤掉已经不存在的子域名，只保留当前存活的。但要注意，`--resolve` 会显著增加总耗时（每分钟约 3500 个）。

## 练习与自测

下面 5 道题用来检验对 Findomain 技术细节的掌握。每题先自己答，再对照参考答案。

**题目 1**：Findomain 的 5.5 秒 84110 子域名性能数据，测的是哪段时间？包含 DNS 解析验证吗？

**题目 2**：CT 日志的 Merkle Tree 如何保证不可篡改性？验证一张证书在日志里需要多少次哈希计算（数量级）？

**题目 3**：Findomain 用 HashSet 做去重，为什么选择 HashSet 而不是排序后去重？这个选择对实时合并有什么影响？

**题目 4**：`--resolve` 选项启用后，Findomain 为什么要先向随机子域名（如 `a1b2c3d4e5.example.com`）发查询？这个检测解决的是什么问题？

**题目 5**：在一个 recon 流水线里，Findomain、subfinder、amass、dnsgen、massdns 各自解决哪类子域名发现问题？为什么不能只用其中一个？

**参考答案与自检标准**：

- 题 1：测的是 Findomain 向所有已配置数据源发起查询、拿到结果、去重合并的端到端时间，不含 DNS 解析验证。84110 是"发现的子域名数量"，不是"解析成功的子域名数量"。加上 `--resolve` 后，按每分钟约 3500 个的解析速度，84110 个全部解析需要 20 分钟以上。自检：能区分"API 查询延迟"和"DNS 解析吞吐"两个概念。
- 题 2：Merkle Tree 的叶子节点是证书，两两哈希得到中间节点，直到根节点。任何历史记录的修改都会改变根哈希，而根哈希是公开发布并签名的，所以不可篡改。验证一张证书需要提供从该证书到根路径上的兄弟节点哈希（Merkle proof），本地重算根哈希比对，复杂度是 O(log N)，几亿张证书也只需几十次哈希。自检：能说出"只能追加"和"O(log N) 验证"两个性质。
- 题 3：HashSet 的插入和查询是 O(1)，每个数据源的响应一回来就能立即合并去重，不需要等所有数据源都返回再排序。排序后去重是 O(N log N)，且必须等全部结果到齐。HashSet 让 Findomain 可以流式合并，这是 15 秒超时上限能成立的前提之一。自检：能解释"流式合并"和"批量去重"的差异。
- 题 4：通配符 DNS（如 `*.example.com` 解析到同一 IP）会让任何随机子域名都解析成功，导致误报。Findomain 先向几个随机子域名发查询，如果都解析到同一 IP，就判定配置了通配符，后续解析结果会过滤掉这个 IP。这个检测解决的是"把随机字符串当成有效子域名"的误报问题。自检：能说出通配符 DNS 的特征和过滤策略。
- 题 5：Findomain、subfinder、amass 都是被动发现，靠 CT 日志和第三方 API 拿"曾经存在过"的子域名，三者数据源和查询策略有差异，合并能提高召回。dnsgen 基于种子生成变形候选（如 `api` → `api-v2`、`api-internal`），解决"未知但可能存在"的子域名发现问题。massdns 对候选做高速 DNS 解析验证，吞吐量远高于 Findomain 内置解析器。不能只用其中一个：被动工具漏掉的子域名要靠 dnsgen + massdns 补，主动工具的种子质量又依赖被动工具的结果。自检：能区分"被动发现"和"主动枚举"的边界，并说明互补关系。

## 学习路径和资源

按"CT 日志机制 → 工具生态 → DNS 解析工程实现"的顺序深入，能从用到懂。

先理解证书透明日志的机制。Google 的 CT 官方文档（certificate-transparency.org）是权威来源，讲清楚了 Merkle Tree 日志的结构和验证机制。crt.sh 的查询界面（crt.sh）可以直接上手查任何域名的证书记录，感性认识 CT 日志能发现什么。如果想深入理解 Merkle Tree 的实现，可以读 RFC 6962（Certificate Transparency）规范，它定义了 CT 日志的数据结构和协议。

再理解子域名发现的工具生态。除了 Findomain，subfinder（ProjectDiscovery 出品）和 amass（OWASP 项目）是另外两个主流被动发现工具。subfinder 的设计哲学和 Findomain 类似（多 API 聚合），amass 更重，集成了主动枚举和图分析。对比这三个工具的实现，能看出不同设计取舍。subfinder 的源码用 Go 写成，可读性好，适合和 Findomain 的 Rust 实现对比。

最后理解 DNS 解析的工程实现。massdns 的论文和源码值得读，它解释了如何用自定义网络栈绕过操作系统 DNS 解析的限制。dnsgen 的源码不复杂，读一遍能搞清楚子域名变形的常见模式。如果对异步 DNS 解析感兴趣，rusolver（Findomain 用的 DNS 库）的源码也是好材料，它展示了如何用 Rust 的 tokio 实现高并发 DNS 客户端。

**进阶路径**：读完上述材料后，可以尝试两个方向。一是改造 Findomain 的数据源列表，接入国内可用的 CT 查询入口或自建 CT 日志镜像，对比召回率变化。二是用 Rust 实现一个简化版的被动子域名发现工具，复现 tokio 并发查询、HashSet 流式去重、通配符检测这三个核心机制，理解工程取舍。

**资源清单**：

- Findomain 官网：[findomain.app](https://findomain.app)
- Findomain GitHub：[github.com/Findomain/Findomain](https://github.com/Findomain/Findomain)
- Findomain Discord：[discord.gg/y5JaRbX](https://discord.gg/y5JaRbX)
- 证书透明官方文档：[certificate-transparency.org](https://www.certificate-transparency.org/)
- RFC 6962（Certificate Transparency 规范）
- crt.sh 查询入口：[crt.sh](https://crt.sh)
- 作者的深度文章：[Subdomains Enumeration: what is, how to do it, monitoring automation using webhooks](https://medium.com/@edu4rdshl/subdomains-enumeration-what-is-how-to-do-it-monitoring-automation-using-webhooks-and-5e0a0c6d9127)
- subfinder GitHub：[github.com/projectdiscovery/subfinder](https://github.com/projectdiscovery/subfinder)
- amass GitHub：[github.com/owasp-amass/amass](https://github.com/owasp-amass/amass)
- massdns GitHub：[github.com/blechschmidt/massdns](https://github.com/blechschmidt/massdns)
- dnsgen GitHub：[github.com/ProjectAnte/dnsgen](https://github.com/ProjectAnte/dnsgen)

Findomain 的源码本身也是学习 Rust 异步工程的好材料。它用 tokio 做异步运行时，用 reqwest 做 HTTP 客户端，用 rusolver 做异步 DNS 解析。读它的 `src/` 目录，能看到多个数据源并发查询、结果聚合、通配符检测的完整实现。对于一个想理解"如何用 Rust 写一个高并发 I/O 工具"的开发者，Findomain 是一个规模适中、复杂度合理的参考项目——它不像生产级 Web 框架那么庞大，但涵盖了异步 I/O、并发控制、错误处理、配置管理等核心主题。
