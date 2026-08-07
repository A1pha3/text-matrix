---
title: "Neko Master：当一只猫安静地盯住你的网关"
slug: neko-master-traffic-dashboard-2026
date: 2026-08-06T04:18:00+08:00
draft: false
tags: ["network", "dashboard", "open-source", "nextjs", "fastify", "sqlite", "clickhouse", "review"]
categories: ["技术笔记"]
description: "一个 6 个月大、3141 stars 的全栈流量分析仪表盘：从 Docker 体验到 ClickHouse 双写架构、从 Real-timeStore 的内存 delta 到跨 LAN Agent 协议的工程哲学。"
keywords: ["neko-master", "traffic dashboard", "Clash", "Mihomo", "Surge", "OpenClash", "Next.js", "Fastify", "WebSocket", "SQLite", "ClickHouse"]
github_repo: "foru17/neko-master"
---

# Neko Master：当一只猫安静地盯住你的网关

> "The cat sat on the mat, observed the bytes, and said nothing."

如果有一类工具你希望它**永远静默、但样样留痕**，那就是家里的网关。我家里跑着 OpenClash，DNS 查询、规则匹配、节点延迟、流量分布——这些数据每天都在产生，可它就像空气一样：你知道它在，但你从不看它。

直到有人把它变成一只猫。

`foru17/neko-master` 就是一个 6 个月大、3141 stars、202 个 fork 的网关流量分析仪表盘。它给自己的定位写得很克制：**"A modern and elegant dashboard for network traffic visualization and analysis."** —— 注意它**不是**代理工具、**不是**订阅转换、**不**提供任何跨境网络访问服务。它是只趴在你网关旁边的猫，安静地盯着每一条流经的字节，然后给你画几张漂亮的图。

读完 1013 行 README、完整的系统架构图、`AGENTS.md` 的 6 条关键契约、以及 `apps/collector/package.json` 里那个 `maxmind` + `better-sqlite3` + `fastify` + `ws` 的依赖组合后，我得说一句：这只猫的设计哲学，是我今年读到的最让我舒服的"小型全栈"案例之一。

## 一、名字里的姿态

> **Neko**（ねこ）在日语里是"猫"。读音 **/ˈneɪkoʊ/**（NEH-ko）。
> 像猫一样，Neko Master 安静、精确地观察网络流量。
> 它是为现代网关环境设计的轻量级分析仪表盘。

作者在 README 顶部把"名字是什么"这件事说得比"功能是什么"还靠前。这在开源项目里不常见——大多数人的标题是 "Fastest X" 或 "Modern Y"，他写的是"一只猫"。

这不是营销话术。这背后是一个**架构选择**——观察者不参与流量转发、不做 DNS 解析、不拦截任何连接。它只是**读**。Clash/Mihomo 通过 WebSocket `/connections` 推送流量事件，Surge 通过 HTTP API 每 2 秒轮询 `/v1/requests/recent`，Neko Master 把这些事件**归一化**、**缓冲**、**刷盘**、**画图**。

读写分离、被动观察，这只猫的"猫性"是写在架构里的。

## 二、让人惊讶的事实

在拆解之前，我先列几个让我盯着屏幕看了几秒的事实：

- **3141 stars、202 forks、6 个月大**。项目创建于 2026-02-05，最后一次 commit 是 2026-08-05（昨天）。一个流量分析仪表盘在 6 个月里长到这个体量，依赖的是**功能克制**而非堆叠。
- **语言占比**：TypeScript 1.71 MB（前端 + collector + shared）、Go 59 KB（Agent probe）、Shell 71 KB（一键脚本 + Agent 服务管理）。一个全栈应用靠 TS + Go + Shell 三件套搞定，没有 Python、没有 Java、没有 Rust。
- **仓库里没有 `requirements.txt`、`pyproject.toml`、`Cargo.toml`、`go.mod`** 之外的语言生态——但有 `pnpm-workspace.yaml`、`.claude/skills/*`、以及一份 100 多行的 `AGENTS.md`。**它把"工程基础设施"做到了极致**。
- **README 是 1013 行**。但英文/中文各一份，架构/Agent/Quick Start/FAQ/Troubleshooting 全部分开。文档结构比代码量还重。
- **`.claude/skills/` 目录**：里面有 `verify-changes`、`add-stats-dimension`、`release`、`ui-conventions`、`db-conventions`、`agent-probe-dev` 这 6 个 SKILL.md。**这是一个把"给 AI 编码助手的指令"和"给人看的文档"分得清清楚楚的仓库**。
- **README 顶部有一段 `> [!IMPORTANT] Disclaimer`**："This project is a traffic analysis and visualization tool for local gateway environments. It does not provide any network access service, proxy subscription, or cross-network connectivity." —— **作者主动在顶部写"我不做什么"**，这是合规意识，也是工程伦理。

这只猫的姿态，从命名到 disclaimer，已经立住了。

## 三、技术栈的"选择"哲学

`AGENTS.md` 第一行写的是：

> "This file is the single source of truth for agent guidance — `CLAUDE.md` and `.github/copilot-instructions.md` are thin pointers to it."

—— 这是我见过的最干净的"AI 协作基础设施"。三层：单源真相 → AI 助手快捷方式 → 共享 skill。一句话告诉你：**所有规则都在 AGENTS.md，别的文件只是引用**。

技术栈选型我列一下，不带任何"X 最强"式的比较，只说 Neko Master 选了谁、为什么：

| 层 | 选了什么 | 关键依赖 | 不选什么 |
|---|---|---|---|
| **前端框架** | Next.js 16 + React 19 | App Router | 不是 Remix、不是 SvelteKit、不是纯 Vite |
| **样式** | Tailwind CSS + shadcn/ui | 三态 dark mode | 不是 MUI、不是 Ant Design、不是 styled-components |
| **图表** | Recharts | inline SVG 切主题 | 不是 ECharts、不是 D3 |
| **国际化** | next-intl | 中英双语消息文件 | 不是 i18next |
| **后端** | Fastify 5 + WebSocket | `ws` 8.x | 不是 Express、不是 Koa、不是 NestJS |
| **存储** | SQLite (`better-sqlite3`) 主存 + ClickHouse 可选 | WAL 模式 | 不是 PostgreSQL、不是 Redis |
| **GeoIP** | `maxmind` + LRU 缓存 + 在线 API fallback | IP-API.com → IPInfo.io | 不是纯在线 API |
| **Agent** | Go（独立进程） | `nekoagent` CLI 服务管理 | 不是 Rust、不是 C |
| **构建** | pnpm workspace + Turborepo | pnpm 9.15.9 | 不是 npm、不是 yarn |

注意一个有意思的细节：**整个项目没有 ORM**。`AGENTS.md` 里提到的 `traffic-writer.repository.ts` 是手写的 SQL 仓储层，作者甚至在 Key Contract #4 里专门写了一句：

> "CSV column dedup uses the delimiter-aware `INSTR(','||col||',', ','||@v||',')` pattern — never bare `INSTR`."

—— **手写 SQL 也能干净，关键是 DDL 集中在 `database/schema.ts` 一个文件**。`add-stats-dimension` 这个 SKILL.md 大概率就是教 AI 助手"加一个统计维度时要改哪 7 处"。

这种"技术选型克制 + 工程文档克制 + AI 协作基础设施克制"的三重克制，构成了 Neko Master 的工程哲学：**少即是多，但不是简陋。**

## 四、架构的四个层次

`docs/architecture.en.md` 的系统图是一个 ASCII art 的五层架构，但我把它**重新组织**成更易读的四个层次。

### 4.1 Frontend 层：Next.js 16 的 App Router + React Query

```
Next.js 16 (App Router)
├── Dashboard / Overview / Charts / Interactive Tables
├── React Query (TanStack)
│   ├── API data fetching and caching
│   ├── Optimistic updates and state management
│   └── Auto-retry and error handling
└── useStatsWebSocket Hook
    ├── WebSocket connection management
    ├── Real-time data subscription
    └── Auto-reconnect and heartbeat
```

关键点不是"它用了 Next.js"，而是**WebSocket 客户端被抽象成一个 hook**。所有页面通过 `useStatsWebSocket(backendId, options)` 拿到实时数据，自动重连、自动心跳、自动按 `backendId` 隔离推送。架构图最右边明确写了 **"backendId-tagged pushes"** —— 一个面板可以同时监控家里、公司、出租屋三个网关，每个网关的数据独立推送、独立缓存。

### 4.2 Collector 层：Fastify + WebSocket + Gateway Collectors

```
API Server (Fastify)
├── REST: /api/backends /api/stats /api/auth /api/domains
│         /api/ips /api/proxies /api/rules /api/devices
│         /api/gateway/* /api/retention
└── WebSocket Server (ws)
    ├── Client Connections / Subscription / Broadcast Stats
    ├── Summary cache (2s TTL)
    └── Policy cache sync (Surge Policy Sync, 10min)

Gateway Collectors
├── Clash Collector × N (WebSocket, real-time)
└── Surge Collector (HTTP polling, 2s)

RealtimeStore (in-memory delta cache)
├── summaryByBackend / minuteByBackend / domainByBackend
├── ipByBackend / proxyByBackend / deviceByBackend
└── ruleByBackend / countryByBackend
    └── merge*() methods merge DB data with real-time deltas
```

这一层是整个系统的"心脏"，但我特别想说的是 **`RealtimeStore`** 这个设计。

Clash 每秒可能推送成百上千条 `connections` 事件。如果每次事件都写 SQLite，磁盘 IO 会爆；如果攒 30 秒再写，**这 30 秒内页面就看不到实时数据**。

`RealtimeStore` 用了一个**两层存储**的设计：

1. **DB 层**（SQLite）：30 秒一次的批量写入 `batchUpdateTrafficStats`，一次原子事务，覆盖所有统计表（domain/ip/proxy/rule/device/country/minute/hourly/daily 共 9 张表）。
2. **内存层**（RealtimeStore）：DB 写入之间的 30 秒窗口里，新事件累积为 **delta**，按 `backendId` 隔离、按维度（domain/ip/proxy/...）分桶。
3. **查询时**：`merge*()` 方法把 DB 的快照数据 + 内存的 delta 合并起来返回。

我把 `apps/collector/src/modules/realtime/realtime.store.ts` 拉下来数了一下：**1535 行**。这是单个模块的体量。这套设计在模式上对应 CQRS（Command Query Responsibility Segregation）+ 增量聚合，但 Neko Master 选择自己实现，而不是引入 Kafka 或 EventStore。**问题规模不需要事件溯源框架，一个 in-memory Map 加 30 秒 batch flush 就够了。**

### 4.3 Storage 层：SQLite 主存 + ClickHouse 双写

> **2026-07-04 的深度 Code Review 报告**（`docs/dev/deep-review-2026-07.md`）暴露了一个**正在造成数据缺失的 P0 缺陷**：`deleteOldMinuteStats` 用 connectionLogsDays（默认 7 天）的 cutoff 同时删除 `hourly_dim_stats` 和 `hourly_country_stats`，而 `resolveFactTable` 把所有 >6 小时的范围查询路由到 `hourly_dim_stats`。
>
> 后果：**用户选"最近 30 天"时 domain/IP/rule/device 维度只有 7 天数据**——不是查询失败，是数据已被物理删除。
>
> 我读到这一段的时候手心出汗。这是个典型的"**两个独立的注册表没人同步**"的 bug：retention 政策表（按分钟聚合）和查询路由表（按时段聚合）走的是同一张事实表，但清理函数用错了字段。这种 bug 单元测试抓不到、集成测试不跑、只有真实数据累积超过 7 天才会暴露。**而 Neko Master 把这个事故公开写进 AGENTS.md 第 4 条 Key Contract 的"regressed in v1.3.9"注释里**——这是工程伦理。
>
> 同一份报告还列了另外 4 个 P0：P0-2（ClickHouse 写侧精简与读侧回退互不知情，CH 抖动时回退结果"合法但错"）、P0-3（OpenWrt 探针锁误判 → procd 重试耗尽可永久静默下线）、P0-4（`getAllRuleChainFlows` O(R×N) 合并 + 全表无 LIMIT 可秒级卡死事件循环）、P0-5（世界地图未适配暗色模式）。
>
> 一个 6 个月大的项目，公开承认 5 个 P0 正在造成错误——这本身比"项目没有 bug"更让人信任它。

```
┌─────────────────────┐         ┌─────────────────────────┐
│ SQLite (WAL)        │         │ ClickHouse (optional)   │
│ ─────────────────   │         │ ─────────────────────   │
│ Statistics:         │         │ Buffer Tables (~5min):  │
│  domain/ip/proxy    │         │  traffic_detail_buffer  │
│  rule/country/device │  dual-  │  traffic_agg_buffer     │
│  minute/hourly/daily│  write  │     │ merge              │
│                     │◄────────►     ▼                    │
│ Config:             │         │ SummingMergeTree:       │
│  backend_configs    │         │  traffic_detail         │
│  geoip_cache        │         │  traffic_agg            │
│  asn_cache          │         │  country_stats          │
│  auth_config        │         │                         │
│  retention_config   │         │                         │
└─────────────────────┘         └─────────────────────────┘
```

ClickHouse 在这里是**可选的**，但选得极其优雅：

1. **默认 SQLite** 写入统计 + 配置元数据，配置元数据**永远写 SQLite**，不挪走。
2. 启用 ClickHouse 后进入**双写模式**：同一份统计数据同时写 SQLite 和 ClickHouse，`STATS_QUERY_SOURCE` 控制读源。
3. **`CH_UNHEALTHY_THRESHOLD=5`** 连续失败 5 次自动把 ClickHouse 标记为不健康，**自动 fallback 到 SQLite**——即使你设了 `CH_ONLY_MODE=1`，CH 挂掉时也不会丢数据。
4. **三阶段迁移**（dual-write 观察期 → 切换读源 → CH-only 模式）+ 一键回滚（`CH_ENABLED=0` 全链路恢复 SQLite-only）。

这段设计有几个让我点头的瞬间：

- **"哪怕你切了 CH-only，CH 挂了照样 fallback"** —— 数据丢失的兜底在应用层做，不在数据库层做。
- **"配置和元数据永远在 SQLite"** —— ClickHouse 只承担**统计流量数据**的职责，分工明确。
- **`CH_COMPARE_ENABLED=0` 默认开启一致性校验**（其实是默认关，用户自己开）—— 作者没把"自己挖的坑"藏起来，README 直接告诉你**如何验证双写的一致性**。

### 4.4 Agent 层：跨 LAN 的 Go Probe

```
Neko Master Panel  ◄──HTTP API──►  Agent  ◄──WS / HTTP──►  Gateway
(single central)                  (Go probe)              (OpenWrt/Linux/macOS)
                                         on remote host
```

如果你的 Neko Master 跑在云 VPS，而 Clash 跑在家里的小米路由器上，**collector 默认没法直接连路由器的 9090 端口**（NAT、私网、防火墙）。

`Agent` 模式解决的就是这个：**把 collector 反向拆成 collector（中央）+ agent（侧车）**。

1. Panel 上加一个 `agent://<agent-id>` backend，系统生成一个 token。
2. Agent 装在网关附近（OpenWrt、Linux、macOS），通过环境变量 `NEKO_SERVER` / `NEKO_BACKEND_ID` / `NEKO_BACKEND_TOKEN` / `NEKO_GATEWAY_TYPE` 一键启动。
3. Agent 本地拉取 Clash/Surge 数据，**批量上报**到 Panel 的 `/api/agent/report`，**心跳**到 `/api/agent/heartbeat`。
4. Dashboard 看到的是一个**统一的 backend**，不区分数据是 direct 来的还是 agent 来的。

安全模型也很干净：

- **`agentId` 派生自 token 的 SHA-256 前 16 位**，重启后稳定。
- **Token 与 agentId 强绑定**：换一台机器用同一个 token，**即使你改了 `--agent-id`，也会被拒绝**。
- **`AgentProtocolVersion`**：payload 变化必须**同时** bump Go 端和 collector 端的版本号，**同一个 commit**。

`nekoagent` CLI 是一个 POSIX-sh 服务管理器，能装 systemd（Linux）或 procd（OpenWrt），单台机器可以跑多个实例（一个家里 Clash、一个公司 Surge），每个实例独立的 PID lock、config、log。

这是分布式系统的**最小化形态**：没有 etcd、没有 Consul、没有 service mesh，**一个 token + 一个 PID 文件 + 一个版本号协议**，搞定多实例、多 LAN、多 gateway 类型。

## 五、三条让我停下来想的设计哲学

### 5.1 契约优先，DRY 居次

`AGENTS.md` 列了 6 条 **"Key Contracts (violating these has caused real regressions)"**：

1. **Rule 命名**：多跳链路聚合到顶层策略组（最后一个 chain hop），只有 `buildRuleName` 实现。Web 流图和 gateway 规则匹配都依赖它（v1.3.9 回归过一次）。
2. **单一流量写入路径**：`batchUpdateTrafficStats` 一个原子外事务，**永远不要加并行写入实现**。
3. **Schema 变更是多注册表**：schema.ts + migration + retention + `deleteBackendData` + ClickHouse writer/reader parity + shared types —— 改一个统计维度要改 7 处（`add-stats-dimension` SKILL.md 是清单）。
4. **CSV 列去重**：用定界符感知的 `INSTR(','||col||',', ','||@v||',')`，**永远不要用裸 `INSTR`**。
5. **i18n + dark mode**：每个用户可见字符串在 `messages/{zh,en}.json` 两份；每个 light-palette Tailwind class 有 `dark:` 对应；inline SVG/chart 颜色 switch on `resolvedTheme`。
6. **Agent 协议**：payload 变化 bump `AgentProtocolVersion`，Go 端和 collector 端的最小版本**同一个 commit**。

这 6 条不是"风格指南"，是**已经踩过的坑**。其中第 1 条明确说 "regressed in v1.3.9 — see `docs/dev/deep-review-2026-07.md`" —— 作者把回归事故**写进了 AGENTS.md**，让未来的 AI 助手不再踩同一个坑。

第 3 条的 7 处清单不是 DRY 焦虑，是**真实复杂度**。改一个统计维度（比如新增"运营商"维度）确实要改 schema + 写入路径 + 读取路由 + ClickHouse 镜像 + retention + 删除 + 前端查询 key。**它不是"重复"，是"分布式注册表"**。

### 5.2 故障兜底在应用层

三个让我拍大腿的设计：

1. **`CH_UNHEALTHY_THRESHOLD=5`** 连续失败自动 fallback 到 SQLite，**即使在 `CH_ONLY_MODE=1` 下也不丢数据**。
2. **`WS_EXTERNAL_PORT`** 配置项专门处理"反代不转发 WS 时的 fallback"——如果 WS 没路由，应用自动 fallback 到 HTTP 轮询（~5 秒）。
3. **`FORCE_ACCESS_CONTROL_OFF`** 紧急模式：忘记 token 时临时打开进入设置页改密码，**改完立即关掉**。

这不是"防御性编程"，这是**承认现实**：网络会挂、数据库会挂、用户会忘密码、CDN 会限流。**每一层兜底都写在应用代码里，不依赖外部组件**。

### 5.3 "AI 协作基础设施"是仓库的一部分

`.claude/skills/` 目录下 6 个 SKILL.md，是**任务型 checklist**：

- `verify-changes`：任何修改后的最小验证集
- `add-stats-dimension`：统计维度变更的 7 处注册表
- `release`：版本号、CHANGELOG、tag、CI
- `ui-conventions`：i18n、dark mode、三态视图
- `db-conventions`：查询、仓储、ClickHouse 拓扑、数据漂移调试
- `agent-probe-dev`：`apps/agent` 下任何修改

这意味着：**作者不只是在写代码，他在写"给 AI 助手的 onboarding 文档"**。Claude Code、Copilot、Cursor、Codex 任何 AI 工具打开这个仓库，AGENTS.md + skills 自动加载，AI 立刻知道"加一个统计维度要改哪 7 处"。

这不是炫技，是**对未来 AI 协作工作流的投资**。当 5 年后某个 AI agent 来给这个项目提 PR，它会自动读到"v1.3.9 在 rule naming 上回归过，请用 buildRuleName 不要自己拼字符串"。

## 六、一键部署的体验

我不想在这篇文章里贴一堆 docker-compose YAML，但有三点**用户体验设计**值得说：

1. **`setup.sh` 一键脚本**自动检测端口冲突，如果 3000/3001/3002 被占用，**自动建议可用端口**。这是**给非技术用户的第一道护城河**。
2. **三种部署形态的清晰分工**：Docker Compose（推荐）→ Docker Run（控制更细）→ Source Code（开发者）。文档不是"我推荐 Docker 所以其他不写"，是"每种都写完整"。
3. **`.env` 变量命名规范**：`WEB_EXTERNAL_PORT` / `API_EXTERNAL_PORT` / `WS_EXTERNAL_PORT` 三个变量**专管"对外端口"**，**`WEB_PORT` / `API_PORT` / `COLLECTOR_WS_PORT` 三个变量专管"容器内端口"**。内外清晰分离，文档明确说"`NEXT_PUBLIC_WS_PORT` 是 build-time only，Docker runtime 设了无效"。

这是**认真读过生产事故的作者**写的文档。`NEXT_PUBLIC_` 前缀在 Next.js 里意味着"打进 bundle 的环境变量"，Docker runtime 设了等于没设——这种事不踩过坑的人不会写进 README。

## 七、它不解决的问题

诚实地说几个 Neko Master **没有做也不打算做**的事：

1. **不做 DNS 解析**。它读 Clash 的 `connections` 事件，不知道某个域名为什么被路由到某个节点——那是 Clash dashboard 的活。
2. **不做规则调试**。它画"每个域名走了哪个节点"，但**不**告诉你"为什么这个域名没被你的规则匹配"。
3. **不做延迟测量**。它画"每节点用了多少流量"，**不**画"每节点延迟是多少"。
4. **不做多用户/多租户**。它假设一个家庭/一个办公室共享同一组 backends。
5. **不做实时告警**。如果某节点流量突然 10 倍，它**不**通知你。

这是它的"猫性"——**只观察，不干预**。你想做规则调试，去翻 Clash 原生日志；你想做告警，写一个 cron 定期查 `/api/stats` 然后发 webhook。**Neko Master 给你"原料"，不给你"成品菜谱"**。

## 八、给我的启发

我读完这个项目，最大的三个收获：

**第一，"克制"是一种可以被工程化的能力**。技术选型克制（Next.js + Fastify + SQLite + Go，没有 React state library 之外的奇技淫巧）、文档克制（README 是 1013 行但每行都是必要的）、AI 协作克制（AGENTS.md 一份而不是 CLAUDE.md + copilot-instructions.md + cursor-rules 各一份）。**每一处克制都有"为什么"，不是"懒得做"。**

**第二，兜底是写在应用代码里的，不是写在数据库配置里的**。ClickHouse 挂了 fallback 到 SQLite、WS 挂了 fallback 到 HTTP 轮询、token 丢了有 `FORCE_ACCESS_CONTROL_OFF` 紧急入口。**没有 Redis Sentinel，没有 Kafka mirror，没有 service mesh retry**。**JavaScript 里的 `try/catch + fallback` 也是企业级架构**。

**第三，AGENTS.md 是这个项目最被低估的资产**。它不是"给 AI 助手的 README"，它是**项目级别的契约文档**——"v1.3.9 我们在 rule naming 上回归过，所以这一条要 buildRuleName 不要自己拼"。**6 条 Key Contracts 每一句都是事故复盘**，未来任何人（包括 AI）来改这个项目，第一时间知道哪些地方不能碰。

---

最后一句话。

Neko Master 是一只安静的猫。它不抓老鼠、不叫、不蹭你腿。它只是趴在网关旁边，眯着眼睛，记下每一条流过的字节。**当你某天想知道"上周三晚上 11 点我在用什么节点看 B 站"的时候，它会睁开眼睛，给你一张图。**

然后继续趴着。

> 项目仓库：[foru17/neko-master](https://github.com/foru17/neko-master)
> 文档入口：[docs/README.md](https://github.com/foru17/neko-master/blob/main/docs/README.md)
> AGENTS.md：[foru17/neko-master/AGENTS.md](https://github.com/foru17/neko-master/blob/main/AGENTS.md)
> Docker 镜像：[hub.docker.com/r/foru17/neko-master](https://hub.docker.com/r/foru17/neko-master)