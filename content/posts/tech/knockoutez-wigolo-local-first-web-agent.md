---
title: "wigolo：把 AI Agent 的 Web 层搬回本地磁盘，无 API Key 跑 MCP"
date: 2026-07-20T03:02:36+08:00
lastmod: 2026-10-01
categories: ["技术笔记"]
tags: ["MCP", "Local-First", "AI Agent", "RAG"]
description: "wigolo 是一个本地优先的 AI Agent Web 智能层：10 个工具（搜索、抓取、爬取、提取、缓存、find_similar、research、agent、diff、watch）通过 MCP、REST、SDK 暴露，18 个直连搜索引擎本地融合重排，零云、零 API key、零按次计费，AGPL-3.0 开源，public beta。"
slug: knockoutez-wigolo-local-first-web-agent
github_repo: "KnockOutEZ/wigolo"
source_key: "gh:KnockOutEZ/wigolo"

---

# wigolo：把 AI Agent 的 Web 层搬回本地磁盘，无 API Key 跑 MCP

## 一句话判断

wigolo 把 AI Agent 需要的 Web 能力——搜索、抓取、爬取、提取、缓存、相似查找、研究、自主收集、页面变化跟踪——装进一个本地引擎，对外暴露成 MCP（Model Context Protocol，模型上下文协议）server、REST API 或 SDK。它的卖点不是"付费工具的免费替身"，而是三件付费 API 给不了的事：每条结果带逐字引文和字节级出处，成本不随查询量增长，数据不出 `~/.wigolo/`。对一个每天跑上百次 web query 的 coding agent 用户来说，SerpAPI 式的按次账单直接归零。

## 项目档案

| 项目 | 现状（2026-10-01 GitHub API 读数） |
|------|------|
| 仓库 | `KnockOutEZ/wigolo`，TypeScript，AGPL-3.0 + 商业双许可 |
| 热度 | 5,435 stars / 446 forks（文章首发时 1.7K stars） |
| 版本 | npm latest v0.2.1（2026-07-19）；main 分支持续推进，近两月未发新版 |
| 状态 | public beta，README 自述由约 7,600 个测试保障 |
| 要求 | Node ≥ 20，预留约 1.5 GB 磁盘（模型与浏览器按需下载，空闲占用约 47 MB） |
| 团队 | 单人主导（Towhid Khan，约 2,000 次提交），少量社区贡献，TestMu AI 赞助 |
| 官网 | [wigolo.app](https://wigolo.app) |

## 系统地图

wigolo 是一个 Node 进程，通过 stdio 或 HTTP 说 MCP。核心工具默认不需要任何 API key，重的活（浏览器渲染、向量检索、重排）都在本机完成：

| 模块 | 职责 | 是否需要 key |
|------|------|--------------|
| Fetch router | 分层抓取：HTTP → TLS 仿真 → 隐身浏览器，逐域学习 | ❌ |
| Search 管线 | 18 个直连引擎并行 → RRF 融合 → 本地重排 → 可解释评分 | ❌ |
| 本地缓存 | `~/.wigolo/wigolo.db`，全文 + 向量双索引，跨会话复用 | ❌ |
| On-device ML | bge-small-en-v1.5 嵌入 + 进程内 ONNX 重排模型 | ❌ |
| MCP / REST / SDK | 同一套 10 工具的三种访问面 | ❌ |
| research / agent / 答案合成 | 用 LLM 把证据写成成文报告 | ⚠️ 可选，免费 Gemini key 或本地 Ollama |

设计的关键是 key 边界的划法：读 Web 的六个操作（search、fetch、crawl、extract、cache、find_similar）完全 keyless；只有当任务变成"写"——把散落的证据综合成一篇带引文的答案——才需要 LLM。而 agent 的日常调用恰恰九成在读。没有 key 时写作类工具也不是失败，而是降级：返回原始 brief 和证据列表，让宿主 agent 自己组装。

## 关键机制拆解

### 1. 十个工具，一套实现

| 工具 | 做什么 |
|------|--------|
| 🔎 `search` | 多引擎搜索。query 传数组并行展开，支持按域名、时间范围、精确短语过滤，四档深度（`ultra-fast` 纯缓存 ≤300ms 到 `deep` 全管线），可返回图片结果 |
| 📄 `fetch` | 单页抓取，分层路由自动升级，输出干净 markdown；处理 PDF、认证会话、页内动作（点击/输入/滚动/截图） |
| 🕸️ `crawl` | 多页爬取：BFS、DFS、sitemap 或仅建 URL 地图；遵守 robots.txt，逐域限速，样板去重 |
| 🧩 `extract` | 结构化提取：表格、JSON-LD、命名 schema（Article/Recipe/Product 等）、自定义 JSON Schema——任何模式都不需要 LLM |
| 💾 `cache` | 查询本机已见的一切：关键词（BM25）或混合语义检索，附统计、清理、变化检测 |
| 🧲 `find_similar` | 给一个 URL 或一个概念，本地嵌入 + 关键词 + 实时 Web 三路融合找相似页 |
| 🧠 `research` | 问题分解 → 子查询并行 → 交叉验证 → 结构化 brief，每条结论带逐 claim 出处 |
| 🤖 `agent` | 自主收集循环：规划 → 搜索 → 抓取 → 提取 → 合成，带步骤日志、时间预算、可选输出 schema |
| 🔁 `diff` | 对比两版内容：活页面对缓存副本、两个 URL、两段 markdown；输出 git 风格 patch 或行数摘要 |
| ⏱️ `watch` | 对 URL 注册变化监视任务，最小间隔 60 秒，可推送到 webhook（带 SSRF 防护） |

这十个工具在 MCP、REST、CLI、SDK 上参数名完全一致。diff 和 watch 是容易被忽略的两个：它们让 wigolo 从"查一次算一次"变成"盯着 Web 的增量变化"，这是多数付费搜索 API 根本没有的能力。

### 2. 搜索管线：18 个引擎怎么变成一条引文

`search` 把查询变体并行发给 18 个直连适配器——不是只有 Google/Bing 的通用搜索，还包括 HN/Algolia、Stack Overflow、GitHub 代码搜索、MDN、DevDocs、Wikipedia、arXiv、Semantic Scholar、crates.io、Marginalia、Mojeek 等面向开发者与研究的垂直源。结果用倒数排名融合（RRF）合并，再经本机重排模型打分。

每条结果都带可解释的评分分解——`base_rrf`（引擎融合排名）、`context_cosine`（与查询意图的语义接近度）、`domain_quality`、`lexical_alignment`、`recency_boost`、`engine_consensus`（多少引擎独立命中）——外加一行自然语言的 `explanation`。引文部分给 `citation_id` 和 `source_span`（出处原文的精确字符区间），agent 可以逐字引用而不是转述。引擎失败、缓存过期、弱结果被自判为 junk，都如实标注在响应里，而不是悄悄吞掉。

这个设计赌的是"引擎会失效、会反爬"：18 个引擎任何一个挂掉对结果影响很小，`engines_telemetry` 数组逐个报告每个引擎的延迟、命中数与结局。

### 3. fetch 阶梯：从裸 HTTP 到隐身浏览器

抓取真实网页的难点是反爬和 JS 渲染。wigolo 的 fetch 路由器按信号逐级升级：先走普通 HTTP；命中反爬信号时切到 TLS 指纹仿真层（呈现 `chrome_142` 等浏览器指纹）；还不行就升起 Playwright 管理的无头浏览器（默认 chromium 家族，池大小 `MAX_BROWSERS=3`，浏览器层指纹加固走 patchright stealth 驱动）。

升级不是按域名猜的，而是逐域学习：哪个域名需要哪一层、已解开的 challenge cookie 按域复用、被反复拦就礼貌退避。`wigolo tune list` 能看到它对每个域名学到了什么，`tune reset` 清掉。等 15 秒（`WIGOLO_CHALLENGE_COMPLETION_MS`）仍过不去的墙，返回的是标注 `blocked_by_challenge` 的失败——是诚实的错误，不是把验证码页面当正文交上来。

要说明一个诚实上限：靠 IP 信誉打分的托管质询网络，数据中心 IP 无论客户端多像真浏览器都拿不到放行。官方 self-hosting 文档明说了这一点，给出的出路是可选代理。爬取礼仪也有硬约束：robots.txt 默认遵守、同域请求间隔 500ms、页数预算按研究体量设计——这是文档索引工具，不是批量收割机。

### 4. 本地模型与"去 Python"架构

0.1.x 时代 wigolo 依赖一个 Python sidecar 做重排，0.2.0（2026-07-17）起默认路径完全去 Python：嵌入模型 bge-small-en-v1.5 经 fastembed 跑 ONNX，重排是 Transformers.js 的进程内 cross-encoder，检索融合、去重、schema 匹配这些确定性工作全部留在代码里不碰 LLM。副产物是新装的引擎空闲足迹只有约 47 MB，模型和浏览器引擎都推迟到首次实际使用才下载。每个 LLM 请求的调用次数硬上限为 1（`WIGOLO_LLM_MAX_CALLS_PER_REQUEST`），LLM 填的字段会对照原文校验，查无即置 null——作者对"让模型编"这件事的防御写进了架构。

### 5. 缓存优先：查过的永远免费

每个抓过、爬过、搜过的页面都落进 `~/.wigolo/wigolo.db`（SQLite，全文 FTS5 + 向量 sqlite-vec 双索引）。`cache` 工具先用 BM25 或混合语义查一遍本机，命中就不再出网；缓存搜索结果保留 1 天、页面内容 7 天（均可配），`force_refresh: true` 跳过。`wigolo backfill` 给历史缓存补算嵌入。这既是省钱机制也是离线机制——断网时，查过的东西照常可用。

## 一个任务流：盯住 Node.js 的发版页面

把上面的机制串成一个真实任务：让 agent 盯住 Node.js 官网的发布页，有变化就报告。全程 keyless。

```json
{ "action": "create", "url": "https://go.dev/doc/devel/release",
  "interval_seconds": 3600, "notification": "inline" }
```

1. **入缓存**：先 `fetch` 或 `crawl` 目标页，正文和元数据落进本地库——这一步建立了 diff 的基准副本。
2. **注册监视**：`watch` 创建任务（示例参数如上，来自官方 tools 文档），每 3600 秒复查一次。注意一个实现细节：watch 任务的执行是惰性的——只在 `wigolo serve` 常驻进程或活跃 MCP 会话期间检查，一次性 CLI 调用能注册但不能调度。
3. **变化即对比**：页面更新后，`diff` 拿活页面对缓存副本，`granularity: "section"` 沿 H1/H2/H3 边界定位，`output: "summary"` 给增删行数——你只需要知道"改了 12 行"还是"整个表格重写了"。
4. **写报告**：需要成文摘要时才用 LLM——`research` 或 `search format=answer`，配免费 Gemini key 或本地 Ollama；没配就退回带引文的 brief，宿主 agent 自己读。

同一套流程换个目标就是"盯竞品 changelog""盯 API 文档废弃公告"。对 agent 工作流来说，这把"定期重新搜索"的低效循环换成了"变化驱动的推送"。

## 接入面：同一个引擎的六种入口

- **MCP**：`npx wigolo init --agents=claude-code,cursor,codex` 一条命令写好配置，支持 claude-code、cursor、codex、gemini-cli、opencode、vscode、windsurf、zed、antigravity。`init` 默认无人值守（CI 安全），组件下载失败不让整体失败，逐组件报告修法。
- **REST**：`wigolo serve` 起在 `127.0.0.1:3333`，`POST /v1/{tool}` 覆盖全部十个工具，`GET /openapi.json` 是 OpenAPI 3.1 契约。绑定到非 loopback 必须配 bearer token，默认 fail closed；另有一个可选的 Firecrawl 兼容 shim（`/compat/firecrawl`），现有 Firecrawl SDK 改个 base URL 就能跑。
- **SDK**：TypeScript `npm install wigolo-sdk`（零依赖，Node/Bun/Deno/edge）、Python `pip install wigolo`（纯标准库，sync + async），都带嵌入式本地模式——自动找到或拉起守护进程，不用单独 serve。
- **CLI**：每个工具都能 `wigolo search "…" --json` 单发；`wigolo shell` 是交互式 REPL，支持 NDJSON 管道脚本。
- **Agent skills**：`wigolo skills add` 装 11 个 skill 包（每工具一个 + 总览），教 agent 缓存优先、query 数组、怎么读 evidence score；安装走收据模型，卸载只删自己写入且未被改动的文件。
- **框架包**：LangChain（工具 + Retriever）、CrewAI、LlamaIndex（Reader）、Vercel AI SDK 各有官方薄封装，核心不依赖任何框架。

Docker 两条镜像（slim 按需惰性加载模型、`:full` 预装浏览器）加 Homebrew、`curl | sh`、单文件二进制，分发面在同类项目里算齐全的。

## 隐私边界与资源账

隐私模型是结构性的，不是政策承诺：软件跑在你机器上，状态全在 `~/.wigolo/`，没有厂商后端可发。出网连接只有三类——你查询的目标网站、你配置的 LLM provider、你自己设置的遥测端点（默认无）。遥测默认关闭，开了也只写本地 NDJSON 文件。密钥不进 `config.json`，走 OS keychain；`rm -rf ~/.wigolo` 即完全卸载。

资源账要读两个数：预留约 1.5 GB 磁盘（浏览器引擎 + 排序和嵌入模型，FAQ 原话是"云服务跑在它们那边并向你计费的东西"），装完空闲占用约 47 MB，首次实际使用相应组件时才下载；模型加载约 1 秒，可用 `WIGOLO_EAGER_WARMUP=1` 提前付掉。

## 成熟度与风险

- **测试与定位**：README 自述约 7,600 个测试，beta 的含义被作者定义为"打磨标准而非稳定性问题"——原话是"直到足够多的人用过、砸过、star 过，叫 v1 才有意义"。
- **发版节奏**：npm 上 latest 停在 0.2.1（2026-07-19），近两个多月未发新版，但 main 分支持续推进（截至 2026-09-30 仍有提交），修复和新功能只能等下个 tag。介意"用旧版还是追 main"的话，这是当前的实际取舍。
- **单人项目**：代码基本出自一位开发者（约 2,000 次提交对社区合计两位数），响应快是优点，总线因子低是风险。商业许可和赞助（TestMu AI）是其公开的可持续模式，AGPL-3.0 保证它不会被转成闭源托管产品。
- **热度与使用量的口径差**：5,435 stars 对应的 npm 月下载约 3,600 次（2026-10-01 读数）——star 增速明显快于装机量，属于话题热度领先于生产渗透的阶段，正常但值得知道。

## 和付费云 API 比，公平的说法是什么

官方 Benchmark 段给的是一次直播演示而非排行榜：同一条冷查询在 Claude 会话里同时发给四个工具（内置 WebSearch、wigolo、Tavily、Exa），让 agent 只看证据评判。官方自述四个工具收敛到同一答案，wigolo 独有逐字引文 + 字节级出处 + 评分分解 + 自标弱结果，同时承认付费工具在部分深度抽取边缘案例上仍占优、爬取是 wigolo 最强项。这是自述口径、单查询、未经独立复现——读它的价值不在结论，而在"每次结果都带评分分解，你可以自己跑一条验证"这个可复核性本身。

官方对比表（2026 年 7 月口径）里真正难替代的三行：逐字引文钉在字节级出处上、本地持久记忆（重复查询即时且离线可用）、查询数据不出本机。反过来说，需要 SLA、发票和按量保障的团队，付费 API 仍然是省心的选择——wigolo 自己也把商业许可留着作为这条路径。

## 谁该用，谁该等

**建议现在就上**：每天大量 web query 的 agent 重度用户（按次账单归零，缓存复用越用越快）；做 RAG 或引用密集型应用、需要逐字出处而不是转述的开发者；数据合规要求 Web 数据不出本机的团队；需要盯页面变化的工作流（watch/diff 在付费 API 里是额外订阅）。

**建议观望或并行**：生产关键路径（beta + 单人维护 + npm 两个多月未发版）；指望数据中心 IP 大规模抓取的场景（IP 信誉上限是结构性的，官方文档明说）；需要 24/7 支持承诺的企业（那条路是商业许可）。

**起步路径**：`npx wigolo init` → `npx wigolo doctor` 确认组件状态 → `wigolo skills add` 给 agent 装使用手册 → 需要成文综述时再配 `WIGOLO_LLM_PROVIDER=gemini`（免费档够用）或 `WIGOLO_LOCAL_LLM=auto` 接本地模型，走到这一步仍然零 key、零费用。

## 仓库地址

https://github.com/KnockOutEZ/wigolo

## 阅读路径建议

1. `npx wigolo init --agents=claude-code`，一条命令接入并看逐组件报告
2. 在 Claude Code 里问一条真实的文档检索问题，观察返回里的 `evidence_score` 分解和 `source_span` 引文
3. `npx wigolo tune list` 看抓取路由器对你的常用域名学到了什么
4. 读 `docs/configuration.md` 的 "Keyless local ladder" 一节，把合成环节也搬到本地模型上
