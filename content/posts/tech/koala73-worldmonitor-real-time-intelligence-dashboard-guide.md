---
title: "World Monitor 架构解析：一个面向 OSINT 分析师的开源全球情报仪表盘，是怎么把 65+ 数据源拼成一张可读态势图的"
date: "2026-06-25T18:04:54+08:00"
slug: koala73-worldmonitor-real-time-intelligence-dashboard-guide
description: "koala73/worldmonitor 用 276 个 proto 文件定义 34 个服务域，65+ 上游数据源 + 双地图引擎 + Country Instability Index + Ollama 本地 AI 把冲突、军事、市场、灾害信号拼成一张实时态势图。本文拆解其分层架构、协议先行策略与 6 站点变体复用机制。"
draft: false
categories: ["技术笔记"]
tags: ["OSINT", "World Monitor", "TypeScript", "情报仪表盘", "Protocol Buffers"]
---

# World Monitor 架构解析：一个面向 OSINT 分析师的开源全球情报仪表盘，是怎么把 65+ 数据源拼成一张可读态势图的

**它解决的不是"画一张地图"，而是"在 60 秒内告诉分析师某地出事了，并且把出事的证据链摆在屏幕上"。**

如果你只把 World Monitor 当作"另一个 flightradar24 + 财经终端 + 地震地图的拼盘"，就低估了它真正的设计意图。真正花力气的地方是 Country Instability Index (CII) v8 这类**多信号汇聚评分**——单条新闻不可信，单个数据源也会撒谎，但当 ACLED 冲突事件 + UCDP 死亡数据 + OREF 火箭警报 + GPS 干扰六边形同时指向同一片国土时，它就把这种"多源汇聚"作为升级为 critical 警报的硬约束。这是一个面向开源情报分析师的端到端态势感知系统，从原始数据采集、本地 AI 推理、协议层 API 到地图渲染与桌面应用，全部由一个 TypeScript 仓库承载。

## 目录

- [为什么需要这样一张仪表盘](#为什么需要这样一张仪表盘)
- [系统地图：四层结构与一条冷启动路径](#系统地图四层结构与一条冷启动路径)
- [数据层：65+ 上游源的 3-tier 缓存与故障转移](#数据层65-上游源的-3-tier-缓存与故障转移)
- [协议层：276 个 proto 文件如何消灭前后端 schema drift](#协议层276-个-proto-文件如何消灭前后端-schema-drift)
- [前端层：双地图引擎、Panel 基类与无框架架构](#前端层双地图引擎panel-基类与无框架架构)
- [AI 层：本地 Ollama 是默认，Groq / OpenRouter 是降级链](#ai-层本地-ollama-是默认groq--openrouter-是降级链)
- [使用场景一：地缘政治事件追踪](#使用场景一地缘政治事件追踪)
- [使用场景二：金融 + 商品市场监测](#使用场景二金融--商品市场监测)
- [变体机制：6 套部署从同一份代码生成](#变体机制6-套部署从同一份代码生成)
- [桌面端：Tauri 2 + Node.js sidecar](#桌面端tauri-2--nodejs-sidecar)
- [隐私与合规边界：AGPL-3.0 + 商业许可](#隐私与合规边界agpl-30--商业许可)
- [采用建议与适用人群](#采用建议与适用人群)
- [结语](#结语)
- [学习目标](#学习目标)

## 为什么需要这样一张仪表盘

OSINT（开源情报）分析师、地缘政治研究员、跨境金融从业者每天面对同一个问题：信号太多而时间太少。UCDP 在更新 ACLED 死亡数据，OREF 在推送以色列空袭警报，Polymarket 押注正在位移，Cloudflare Radar 报告区域断网，弗吉尼亚州的地震仪刚刚记录到 4.7 级震动——它们散落在几十个网站、几十种格式、几十种时区里。

World Monitor 的答案是：把**所有**这些信号汇聚到同一张地图上，再用多源汇聚规则消除单源偏差。冲突事件升级到 critical 之前必须同时命中新闻 + 军事 + 市场 + 抗议四个流中至少三个；CII 评分把"不稳定"拆成四个加权分量（unrest、conflict、security、information velocity）强迫分析师分维度判断；Welford 在线算法为每一个信号类型维护滚动基线，50 次军事飞行如果当日基线是 15 次就是 3.3σ 异常，如果基线是 48 次就是噪声。

这套机制比"画地图"贵得多，但比"误报一个国家的内战"便宜得多。

## 系统地图：四层结构与一条冷启动路径

整个系统可以拆成四层 + 一条冷启动路径。理解这条路径是把 World Monitor 当作"一个工程"来读的关键。

```
┌─────────────────────────────────────────────────────────────────┐
│  1. 浏览器 / 桌面客户端                                           │
│     DeckGLMap (deck.gl) │ GlobeMap (globe.gl) │ Panel × 104      │
│     analysis.worker.ts  │ ml.worker.ts (ONNX)                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │ fetch /api/*
┌─────────────────────────▼───────────────────────────────────────┐
│  2. Vercel Edge Functions (60+) + Cloudflare CORS Preflight     │
│     proto 生成网关 + 手工 operational endpoints (auth/billing/MCP)│
│     3-tier Redis 缓存 (300s/600s/1800s/7200s/86400s)            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│  3. Railway Relay (AIS WebSocket、OREF、GramJS MTProto)          │
│     seed 循环: market / aviation / GPSJAM / risk / UCDP / events │
│     RSS 代理 + OREF 住宅代理 + 消费者价格爬虫                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│  4. Upstash Redis (缓存 + 限流 + seed-meta 新鲜度追踪)           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
              65+ 上游数据源 (Finnhub / OpenSky / CoinGecko / UCDP / FIRMS / ...)
```

**冷启动路径**：浏览器加载 → 并行 fetch `/api/bootstrap?tier=fast`（1200s s-maxage，3 秒超时）和 `tier=slow`（7200s s-maxage，5 秒超时）→ 38 个常用数据集从单条 Redis pipeline 批量读出 → 地图与面板直接消费已 hydrate 的数据，零冷启动延迟。

这套分层有两个值得注意的取舍：

- **Edge Function 数量是 60+ 而不是 1 个胖函数**：每个域一个 bundle，由 `createDomainGateway` 工厂统一施加 CORS / 限流 / 缓存头 / ETag 流水线。代价是部署单元多，好处是单个域失败不会污染其他域，CI 通过 `tests/edge-functions.test.mjs` 强制每个 bundle 不引入无关模块。
- **Railway Relay 是脏活集中地**：AIS WebSocket 长连接、GramJS MTProto 拉 56 个 Telegram 频道、OREF Akamai WAF 住宅代理、消费价格 Playwright 爬虫——所有需要长连接、需要绕反爬、需要浏览器指纹的活全在这层，Edge Function 只做无状态 RPC 转发。

## 数据层：65+ 上游源的 3-tier 缓存与故障转移

数据层的设计原则只有一条：**任何上游故障都不应该让地图变成空白**。围绕这条原则展开的有 4 个机制：

**1. 三级缓存（in-memory → Redis → upstream）**。Edge Function 的 `cachedFetchJson()` 走标准 lookup-or-fill，但额外加了一个**in-flight promise map**——同一 key 的并发请求不会各自去敲上游，而是共享同一个 Promise。这是经典的 cache stampede prevention，对 Yahoo Finance 这类对 429 敏感的 API 几乎是必备，否则一刷新就让 50 个用户同时打 50 次相同请求。

**2. Stale-on-error fallback**。任何上游 5xx 不会让请求直接失败，而是返回上一次成功的缓存值并在响应头打 `X-Cache: stale`。同时再叠加**negative caching**：上游失败状态本身被缓存 5 分钟（UCDP）或 30 秒（Polymarket），避免雷鸣群效应把一个挂掉的 API 砸出更长的恢复时间。

**3. 速率敏感 API 串行化**。Yahoo Finance 这种对 429 极敏感的源，所有请求被强制加 150ms inter-request delay 并用 sequential queue 调度。单用户感觉不到差异，但 100 个并发用户的雷鸣群不会让整层 Redis 雪崩。

**4. 智能 gap tracker**。35 个源组每个都被监控为 `fresh / stale / very_stale / no_data / error / disabled` 六态之一。当 GDELT 或 RSS 这种被标记为 `requiredForRisk` 的关键源失效时，Strategic Risk 面板会被强制进入"insufficient-data"硬态——不显示伪造的"低风险"。

**5. 协议层关键发现**。UCDP 事件数据走"自动版本发现"路径：同时探测多个 API 版本，记录哪个版本第一个返回 200，再把这个发现缓存 1 小时。如果某个版本今天罢工，明天恢复时会自动切换，不需人工干预。

## 协议层：276 个 proto 文件如何消灭前后端 schema drift

World Monitor 的 API 表面有 34 个服务域，覆盖 aviation / climate / conflict / cyber / displacement / economic / infrastructure / intelligence / maritime / market / military / news / prediction / research / seismology / supply-chain / trade / unrest / wildfire / sanctions 等垂直。每个域的请求、响应、字段约束都从 `proto/` 目录下的 276 个 `.proto` 文件生成。

生成流水线是这样的：

```
proto/*.proto
    ↓ buf generate (3 个自定义 sebuf 插件)
src/generated/client/   (typed fetch-based TS 客户端)
src/generated/server/   (TS 服务端消息类型)
docs/api/               (OpenAPI 3.1.0 specs)
```

代码生成产生 3 类产物：

- **`protoc-gen-ts-client`**：typed fetch 客户端类，开发者 import 后直接 `aviationClient.listAirportDelays({...})`。
- **`protoc-gen-ts-server`**：handler interface + route descriptor，开发者实现 handler 即可，由 router 负责注册。
- **`protoc-gen-openapiv3`**：OpenAPI 3.1.0 YAML/JSON 规范，直接喂给文档站。

`buf.validate` 字段约束（比如 latitude ∈ [−90, 90]）也是写在 proto 里的，handler 收到时数据**已经校验过**。这意味着破坏性 schema 变更会在 CI 阶段被 `buf breaking` 抓住，不会等到前端调用 4xx 才暴露。

**这套设计真正解决的是**：传统项目里"前端期望 `{ delay: number }`、后端发了 `{ delay: string }`"的经典 bug。当 34 个域、几百个 RPC 全部走这条流水线时，新人加一个字段的成本被压到"改一个 proto 文件 + 跑 make generate"两步，再没有"我忘了同步 Swagger 文档"这种借口。

## 前端层：双地图引擎、Panel 基类与无框架架构

前端层的设计选择更激进：**完全不用 React / Vue / Svelte**。

不是没有考虑过。仓库的 ARCHITECTURE.md 直接给出 4 条理由：

- **包体**：仪表盘加载几十个数据层、地图渲染器、ML 模型、实时视频流，框架 runtime 的每一个 KB 都在挤占情报数据本身。整个应用 shell（panel 系统、路由、状态管理）编译后的 JS 比 React runtime 还小。
- **DOM 控制**：Panel 系统直接操作 `innerHTML`（带 150ms debounce）+ 在稳定容器上做事件委托，框架的 virtual DOM diff 会和这个模式打架。
- **WebView 兼容**：Tauri 桌面端在 macOS WKWebView 和 Linux WebKitGTK 上对拖拽、剪贴板、自动播放、内存管理有各自怪癖，框架抽象反而是障碍。
- **长期简单**：没有框架升级、没有破坏性 API 迁移、没有 adapter 库。

替代品全部用浏览器标准实现：

| 关注点 | 解决方案 |
| --- | --- |
| 组件模型 | `Panel` 基类（render / destroy / setContent）+ 104 个 panel 子类 |
| 状态管理 | `localStorage`（用户偏好）+ `CustomEvent`（`wm:breaking-news` / `theme-changed` / `ai-flow-changed`）+ 中央 signal aggregator |
| 路由 | URL query params（`?view=&c=&layers=`）+ `history.pushState` |
| 响应式 | `SmartPollLoop` + `RefreshScheduler`，可见性感知调度、in-flight 去重 |
| 虚拟滚动 | 自研 `VirtualList`，DOM 元素池 + 上下 spacer div + rAF 批处理 |

**双地图引擎**是这个项目的视觉招牌：

- **GlobeMap**（globe.gl）：3D 交互地球，单一合并的 `htmlElementsData` 数组，marker 用 `_kind` discriminator 区分类型（conflict / flight / vessel / protest 等 15+ 种），自动旋转、shader 大气层。
- **DeckGLMap**（deck.gl + maplibre-gl）：WebGL 平面地图，支持 ScatterplotLayer / GeoJsonLayer / PathLayer / IconLayer / PolygonLayer / ArcLayer / HeatmapLayer / H3HexagonLayer，PMTiles 协议自托管底图，Supercluster 做 marker 聚合。

**discriminated union marker** 是一个值得单独提的工程细节。所有地图标记都是 plain object（不是 class 实例），用字面量类型字段 `_kind` 在编译期穷举匹配：

```typescript
type MapMarker =
  | { _kind: 'conflict'; lat: number; lon: number; severity: string }
  | { _kind: 'flight'; lat: number; lon: number; callsign: string }
  | { _kind: 'vessel'; lat: number; lon: number; mmsi: number }
  | { _kind: 'protest'; lat: number; lon: number; crowd_size: number }
  // ... 15+ additional marker kinds
```

这样标记可以无损地序列化到 JSON、写进 IndexedDB、通过 Web Worker transfer，渲染层用 `switch` 穷举，TypeScript 编译器会替你检查"新增 marker kind 后是否每个 case 都已处理"。

## AI 层：本地 Ollama 是默认，Groq / OpenRouter 是降级链

World Monitor 的 AI 集成走的是**本地优先 + 远程降级**的 4 步链：

1. **Ollama**（本地推理）—— 默认路径，不消耗 API key，可在断网环境运行
2. **Groq**（云端快速推理）—— 备选
3. **OpenRouter**（云端多模型路由）—— 备选
4. **Transformers.js + 浏览器侧 T5**（浏览器内推理）—— 终极降级

这条链的存在意味着：**没有 API key 时整个仪表盘仍然可用**。AI 摘要、新闻聚类、跨域关联这些 AI 增强在用户配齐 key 之前是 Ollama 本地推理，配齐 key 之后是 Groq 高速推理，浏览器侧 Transformers.js 是 fallback。

AI 增强的落地点集中在三个地方：

- **新闻聚类**：analysis.worker.ts 用 Jaccard 相似度把同一事件的多个来源聚成一个 cluster，避免地图上同一个事件被画 12 个点。
- **跨域关联检测**：worker 检测"今天 ACLED 在某地报告了 3 起冲突 + UCDP 死亡数据 +2 + 当地市场波动 4%"这种跨域信号，并把它们标为 focal point。
- **新闻摘要 / 翻译 / 情绪分析**：ml.worker.ts 跑 ONNX（MiniLM-L6 embeddings、sentiment、summarization、NER），用 IndexedDB 维护 in-worker vector store 做语义搜索。

注意：所有 AI 推理产物都被打上"AI 生成"标记，UI 不会让 AI 摘要覆盖原始 source。情报分析师仍然必须看到原始 RSS 源链接，AI 只是把 12 篇报道压缩成 3 句话。

## 使用场景一：地缘政治事件追踪

**任务**：监测 2026 年 6 月某周中东南亚某国的抗议活动是否升级为对 CII 评分的实质影响。

**1. 打开主站点**，加载后地图自动定位到目标国，CII 评分在右侧面板显示。

**2. 查看 Unrest 层**，ACLED + GDELT 双源抗议事件用 Haversine 去重，密度图叠加在地图上。CII 的 unrest 组件权重最大，对民主国家用 `log(protestCount)`（防止法国黄背心那种日常抗议拉高评分），对威权国家用线性（每次事件都是信号）。

**3. 切到 News 层**，500+ RSS 源按 4-tier 信誉分层（wire services → major outlets → specialty → aggregators），Telegram 56 个 OSINT 频道的 GramJS MTProto 实时流以"OSINT leads"形式呈现，注意它们被显式标记为"未背书真相"。

**4. 看 Strategic Risk 面板**，只有 unrest + conflict + security + information velocity 四个分量同时出现上升趋势时，评分才会被推到 critical。单独一个分量跳变不会触发 critical——这就是多源汇聚的硬约束。

**5. 切到 Country Brief**，AI 自动生成 200 词简报，附 12 条原始 source 链接。如果 Ollama 没配，自动降级到 Groq；如果 Groq key 也没配，降级到浏览器侧 T5。

**6. 把视图 URL 复制给同事**，URL 携带 `?c=THA&layers=unrest,cii,news` 状态，对端打开直接看到你正在看的内容。

整个流程从"打开浏览器"到"出简报"在 5 分钟内完成，不需要在 12 个网站之间切来切去。

## 使用场景二：金融 + 商品市场监测

切到 `finance.worldmonitor.app` 变体（同一份代码），自动启用：

- **29 个全球交易所**地图层（NYSE / NASDAQ / Shanghai / Euronext / Tokyo / Hong Kong / London / NSE/BSE / Toronto / Korea / Saudi Tadawul …）
- **19 个金融中心**（按 Global Financial Centres Index 排名）
- **14 个央行 / 超国家金融机构**（美联储 / ECB / BoJ / BoE / PBoC …）+ BIS 政策利率与 REER
- **10 个商品枢纽**（CME / ICE / LME / SHFE / DFE / TOCOM / DGCX / MCX + 鹿特丹 / 休斯敦物理枢纽）
- **Gulf FDI 投资层**（64 个沙特 / 阿联酋 FDI 项目按状态与金额可视化）

7-signal macro radar 把 BUY/CASH 复合判断叠在指数层上，用户自定义 watchlist（最多 50 个 ticker）持久化到 localStorage，跨 panel 通过 `CustomEvent` 同步。Polymarket 押注变化作为预测市场层独立呈现，走 4-tier fetch 链（bootstrap → RPC → browser-direct → Tauri native TLS）。

**关键风险**：Gulf 报价、Polymarket、ETF 流向走的都是 Yahoo Finance / CoinGecko / 自托管 scraping 拼接，单源失败会触发 stale-on-error，但用户看到的"实时"实际是"过去 8 分钟"。这个时延在 `Redis 缓存 + s-maxage=480s` 上是写死的配置项，不是个 bug——是设计取舍。

## 变体机制：6 套部署从同一份代码生成

仓库提供 6 套站点变体（world / tech / finance / commodity / happy / energy），全部从一个 codebase 部署：

- `worldmonitor.app` —— 综合地缘
- `tech.worldmonitor.app` —— 科技生态（Big Tech HQ、初创、云区域、加速器、会议）
- `finance.worldmonitor.app` —— 金融市场（29 交易所、19 金融中心、14 央行）
- `commodity.worldmonitor.app` —— 商品
- `happy.worldmonitor.app` —— 正面新闻
- `energy.worldmonitor.app` —— 能源

变体检测由 hostname 完成（`tech.worldmonitor.app` → tech variant），控制：默认启用 panel、地图层、刷新间隔、主题、UI 文案。变体切换会重置所有用户设置为默认值。开发者本地用 `npm run dev:tech` / `dev:finance` / `dev:commodity` / `dev:happy` / `dev:energy` 调试对应变体。

这个设计的工程价值是：**6 套部署共享同一套 CI / 同一套 Edge Function / 同一份数据 pipeline / 同一份维护负担**。新加一个能源数据集（energy variant 用）不需要重写 finance 的代码，只需要在 layer definition 里挂上 `variant: 'energy'`，CI 阶段会按 variant 切片做产物体积检查。

## 桌面端：Tauri 2 + Node.js sidecar

`worldmonitor.app/api/download?platform=*` 提供 macOS (Apple Silicon / Intel) / Windows (x64) / Linux (AppImage) 三平台原生应用，底层是 Tauri 2 (Rust) + Node.js sidecar。

为什么不用 Electron：Tauri 包体小、内存占用低、WKWebView / WebView2 启动快。代价是所有 WebKit 怪癖需要自己处理（dragndrop、clipboard、autoplay、memory pressure）。

sidecar 是个值得单独说的设计：**桌面应用的本地 sidecar 镜像了所有云端 API handler**。desktop 用户即使断网也能跑全部本地数据处理（缓存层、proto 路由、CII 计算、AI 推理走 Ollama 本地）。**桌面应用和云端使用同一份 TypeScript 代码**，不维护两套实现。

desktop ↔ sidecar 通信走 IPC 通道，安全模型有专门的章节在 SECURITY.md：renderer ↔ sidecar 信任边界、IPC 命令暴露、fetch patch 凭据注入都已被安全研究员 Cody Richard 在 2026 年披露并修复。

## 隐私与合规边界：AGPL-3.0 + 商业许可

仓库采用 **AGPL-3.0-only** 许可。这条许可比普通的 GPL 更严苛：

- 个人 / 研究 / 教育使用：✅ 允许（AGPL-3.0-only）
- 自托管实例：✅ 允许（AGPL-3.0-only）
- Fork & 修改：✅ 允许（在 AGPL 触发条件下需要共享源码）
- 商业 SaaS 部署：✅ 允许（遵守 AGPL 义务）
- 私有专有使用 / 官方品牌使用权：❌ 需单独商业 / 商标许可

**AGPL 的"网络服务触发开源"条款**意味着：如果你把 World Monitor 部署成对外服务的 SaaS，无论你是否修改源码，AGPL 都要求你向所有网络用户提供完整源代码。这是大多数商业团队部署前必须先评估的合规成本。

仓库同时提供商业许可作为非-AGPL 选项，团队如果需要把 World Monitor 嵌入专有产品、不公开派生代码，可以走商业许可。官方品牌（worldmonitor.app / World Monitor logo）需要单独商标许可。

**数据合规边界**：所有数据源来自 65+ 第三方开放 API（UCDP、ACLED、OpenSky、Cloudflare Radar、Yahoo Finance、CoinGecko、Polymarket …），World Monitor 本身**不收集**用户行为数据上报到中央服务器（除 Vercel Analytics 默认开启的匿名访问统计）。用户自定 watchlist / 偏好 / 面板布局持久化到本地 localStorage，不跨设备同步。

## 采用建议与适用人群

**适合采用**：

- **OSINT 分析师 / 地缘政治研究员**：CII v8 + 跨域汇聚 + 多源信号去重 + AI 摘要整套工具链直接覆盖日常工作流。
- **跨境金融 / 商品交易员**：finance / commodity 变体 + 7-signal macro radar + Gulf FDI 层 + 19 金融中心 + 实时 Polymarket 押注。
- **新闻编辑室 / 调查记者**：500+ RSS 源聚合 + 56 Telegram OSINT 频道 + AI 摘要 + URL 状态共享。
- **学术研究 / 公共政策研究**：自托管可重做所有数据 pipeline，AGPL 强制开源派生代码符合学术 reproducibility 要求。
- **应急响应 / 灾害管理团队**：USGS + GDACS + NASA EONET 三源灾害数据 + 0.1° 地理网格去重 + OREF 火箭警报。

**不适合**：

- **需要 100% 数据准确性 + 审计追踪** 的合规场景：AI 摘要层是 Ollama 本地模型，输出不可重现；Polymarket 押注是预测市场不是事实。
- **企业内部 BI 仪表盘替代品**：World Monitor 是面向全球信号的 OSINT 工具，不是内部数据可视化平台。
- **断网 / 极端低带宽环境**：默认部署依赖 60+ 上游 API，虽然 stale-on-error + 3-tier 缓存提供基本韧性，但仍然是为"网络可达"环境设计的。
- **法务 / 监管不允许使用 AI 摘要的领域**：所有 AI 增强是默认开启的，需要 UI 切换关闭。

**采用顺序**（建议三步走）：

1. **第一周**：克隆仓库跑 `npm install && npm run dev`，本地体验主站 + finance / energy 变体，熟悉 56 个 map layer、500+ RSS 源、CII 评分逻辑。
2. **第二周**：阅读 `docs/architecture.mdx` + `ARCHITECTURE.md`，重点看 65+ 数据源列表、缓存策略、Tauri 桌面端打包流程。配置 Ollama 本地推理体验 AI 摘要的本地化路径。
3. **第三周**：fork + 自托管（Vercel / Docker / static 部署三选一，参考 `SELF_HOSTING.md`），接入你所在团队需要的额外 RSS 源或私有数据源。

## 结语

World Monitor 不是"画一张地图的项目"，而是"把 65+ 个数据源的多源汇聚规则 + 本地 AI 推理 + 协议先行 API + 桌面端封装做成一个开源产品"的项目。它真正的工程价值在于：

- 协议先行（276 proto）让 34 个域、几百个 RPC 不会随时间漂移
- 三级缓存 + 故障转移让 65+ 上游源的单点故障不会清空地图
- 多源汇聚 + CII 评分让单源偏差被结构性压制
- 双地图引擎 + Panel 基类让 104 个数据层共享一套渲染框架
- Tauri sidecar 让桌面端和云端共享同一份 TypeScript 代码

对 OSINT、地缘政治、金融、新闻、应急响应领域的从业者，这是一个值得拆开来读三遍的项目——读完代码再读 `docs/design-philosophy.mdx`，会理解很多"为什么不直接用 React / 为什么每个 Edge Function 是独立 bundle / 为什么要做 6 套变体"这些问题的答案。

## 学习目标

读完本文后，你应当能够：

1. 画出 World Monitor 的四层结构（浏览器/桌面 → Vercel Edge → Railway Relay → Redis → 65+ 上游源）并解释每一层的核心职责
2. 解释 proto-first 协议先行策略如何消灭前后端 schema drift，以及 buf.validate 如何在 CI 阶段抓住破坏性变更
3. 复述 CII v8 评分的 4 个加权分量（unrest / conflict / security / information velocity）和多源汇聚触发 critical 的硬约束
4. 解释双地图引擎（globe.gl / deck.gl）各自的渲染场景和 discriminated union marker 的工程价值
5. 评估 AGPL-3.0 + 商业许可对你的团队 / 项目的合规影响
