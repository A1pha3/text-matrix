---
title: "Grafana：开源可观测性平台不是 dashboard 工具，理解它的边界比记住功能更重要"
date: 2026-06-26T21:03:36+08:00
slug: grafana-grafana-open-source-observability-platform-guide
description: "Grafana 已经从单一 dashboard 工具演化成数据源、面板、告警、探索四模块协同的可观测性平台。本文从架构、模块边界、OSS/Enterprise/Cloud 划分、与 Prometheus/Loki/Tempo 栈的协同关系四个角度重新理解它。"
draft: false
categories: ["技术笔记"]
tags: ["Grafana", "可观测性", "Prometheus", "Loki", "开源"]
---

# Grafana：开源可观测性平台不是 dashboard 工具，理解它的边界比记住功能更重要

**Grafana 真正的身份是"在数据源、面板、告警、探索四块之间做编排的可观测性前端平台"，而不是一个"画图的 dashboard 工具"。** 74k+ stars、AGPL-3.0、TS 前端 + Go 后端的双栈、v13.0 于 2026 年 4 月 GA——它当前的形态是"v12 引入 Dynamic Dashboards + Git Sync，v13 把它们一起做成 GA"的产物。要判断它是否适合你的技术栈，核心问题不是"Grafana 能不能画图"，而是"Grafana 在你已有数据后端（Prometheus / Loki / Tempo / Mimir / ES / CloudWatch）的位置上，到底补了哪一块"。

## 目录

- [学习目标](#学习目标)
- [一、核心判断：Grafana 是什么、不是什么](#一核心判断grafana-是什么不是什么)
- [二、系统地图：四大模块的边界与协同](#二系统地图四大模块的边界与协同)
- [三、架构分析：TS + Go 双栈、API 抽象、Plugin SDK](#三架构分析ts--go-双栈api-抽象plugin-sdk)
- [四、一次查询的完整任务流](#四一次查询的完整任务流)
- [五、OSS / Enterprise / Cloud 边界](#五oss--enterprise--cloud-边界)
- [六、与 Prometheus / Loki / Tempo 栈的协同关系](#六与-prometheus--loki--tempo-栈的协同关系)
- [七、最小部署](#七最小部署)
- [八、什么时候该用、什么时候不要用](#八什么时候该用什么时候不要用)
- [九、学习路径与延伸阅读](#九学习路径与延伸阅读)

## 学习目标

读完本文，你应当能够：

1. 用一句话定义 Grafana 在可观测性栈里的位置——它不是数据存储、不是指标采集器、不是告警管理器，而是把这些层组合起来的"前端平台"。
2. 说出数据源 / 面板 / 告警 / 探索四大模块的边界与协同方式，并能在自己的项目里指出"如果用 Grafana，这四块各自对应哪段工作"。
3. 区分 Grafana OSS / Enterprise / Cloud 的能力分界，知道哪些功能是开源能拿到的、哪些是 Enterprise 锁定的、哪些只能在 Cloud 里开箱即用。
4. 解释 Grafana 12.0（2025-04 GA）和 13.0（2026-04 GA）两个里程碑分别解决了什么遗留问题，并据此判断是否值得升级。
5. 在本机用 Docker 拉起一个最小可用的 Grafana 实例，配置好第一个数据源与第一张面板。

---

## 一、核心判断：Grafana 是什么、不是什么

把 Grafana 当成"画 dashboard 的工具"是最常见的认知错位。它当前的能力边界，可以用四个"不是"来划清楚：

- **不是数据存储**。Grafana 不保存你的时序数据、日志、追踪或 profile。所有原始数据都在它对接的数据源里——Prometheus 存指标、Loki 存日志、Tempo 存追踪、Pyroscope 存 profile、ES / CloudWatch / Postgres 各自管自己的数据。Grafana 内部有一个 SQL 存储（默认 sqlite，可换 mysql / postgres），但那只是放用户、组织、面板 JSON、告警规则元数据。
- **不是指标采集器**。它不会从你的应用里 pull / push 数据。采集端是 Prometheus Agent、Alloy、OpenTelemetry Collector、Telegraf、Vector 的事。Grafana 只在"已采集到的数据上做查询、可视化、告警评估"。
- **不是告警管理器**。它确实有告警规则引擎（Grafana-managed rules）和一个兼容 Prometheus Alertmanager 的通知路由层（自 v12 GA），但它是和 Alertmanager 平行存在的另一条线。Grafana-managed alerts 走的是它自己的评估器、自己的 notification policies、自己的 silences 体系。
- **不是单体应用**。它由 Go 后端（`pkg/`）、TypeScript 前端（`public/app/`）、插件 SDK（`pkg/plugins/`）、SQL 迁移系统（`pkg/services/sqlstore/migrations/`）和一套 Kubernetes 风格的 Resource API 构成。任何一个组件被裁掉，剩下的部分仍能跑——比如只用前端 + 一个 Prometheus 数据源，就能组成"最小画图"。

那么它**是**什么？官方仓库自述是 *The open and composable observability and data visualization platform*——一句"开源且可组合的可观测性与数据可视化平台"。这里的关键词是 **composable**（可组合）和 **platform**（平台）：

- "composable" 体现在数据源、面板、告警、探索四块之间通过 plugin SDK 解耦，每一块都可以独立替换或扩展；
- "platform" 体现在它给自己塞了一整套 GitOps（Git Sync）、RBAC、Provisioning、SCIM、Auditing、API server（apiserver）、Drilldown Apps、Investigations、Assistant 等围绕"团队使用"的能力，不再是个人开发者的画图工具。

这一定位直接决定了下文要展开的取舍：理解 Grafana 的关键，是理解它**如何编排**而不是它**能画出什么图**。

---

## 二、系统地图：四大模块的边界与协同

仓库 `public/app/features/` 目录就是这张地图的物理映射。下面四个目录对应四个一等公民模块，外加一条横切线是 provisioning / authentication / plugins。

### 2.1 数据源（datasources）

职责：把"外部存储的查询语言"翻译成 Grafana 内部的 `DataQueryRequest` / `DataQueryResponse`。

- 后端在 `pkg/tsdb/`，前端在 `public/app/features/datasources/`。每个数据源是一个 plugin，自带 `getBackendFactory` / `datasource` 工厂。
- 数据源插件类型分四类：data source（拉数据）、panel（画图）、app（顶层应用，如 drilldown apps）、renderer（截图服务）。其中 data source 数量最多。
- 13.0 起，仓库在做"数据源解耦"重构：MSSQL / PostgreSQL / InfluxDB / Tempo / Graphite 的前后端被拆成独立 plugin 仓库。这意味着 Grafana 仓库本身在瘦身，13.1.0 release notes 里仍能看到 `Finish decoupling mssql & postgresql - backend`、`Decouple InfluxDB frontend` 等条目。
- 12.0 引入的 Data Source API 异步化（`Introduce async APIs and hooks as replacement for datasourceSrv`）是一个常被忽略的信号：旧的 `datasourceSrv` 同步 API 正在被 React 友好的 async 钩子替换，前端架构在持续现代化。

> 实操含义：当你的数据不在已官方支持的数据源里时，先看 Grafana Plugin Hub 而不是自己去改 Grafana。composable 平台的核心就是"扩展点比内置实现更重要"。

### 2.2 面板与 Dashboard

职责：在"已查询到的结果"上做变换、绘制、交互。

- 后端目录 `public/app/features/panel/`，加上具体的 `canvas`、`logs`、`geo`、`dashboard-scene`、`dashboard`、`browse-dashboards` 等子模块。13.0 起引入了"Dynamic Dashboards"作为 V2 看板（v12 是 experimental，v13 GA），特性包括：section-level 变量、模板化面板、面板复用（LibraryPanels）、可恢复的删除（Restore deleted dashboards GA）。
- 内置 panel 仍包含：Graph（折线/柱状）、Stat、Gauge、Bar gauge、Table、Pie chart、Heatmap、Histogram、Logs、Geomap、Canvas、Trend、State timeline、Node graph、Text、News、Welcome、Datagrid、Sparkline、XY Chart 等几十种。
- 仪表板模型本身有两套：旧的 V1（JSON 直接存盘）+ V12 GA 的 V2 schema（`new-dashboards-schema` 已成为正式升级路径）。13.0 的迁移路径要求保留 V1 兼容入口，但新功能主要长在 V2 上。

### 2.3 探索（Explore）

职责：脱离 dashboard 的"临时查询工作台"，是排障的主入口。

- 目录 `public/app/features/explore/`，12.0 之后还有一个 `logs/` 单独目录承载独立的 Logs Drilldown App。
- 关键能力：ad-hoc 查询、metric ↔ log 切换时保留 label filters、split view（多查询并排）、流式日志（streaming）。13.0 把"ad-hoc filters" 改名为 "filters"（语义统一）。
- 与 dashboard 的差别：dashboard 是"事前设计好的视图"，explore 是"现场拼接的查询"。在 SRE 排障流程里，前者用于巡检和 review，后者用于事件响应。

### 2.4 告警（alerting）

职责：定义规则、评估状态、发送通知、记录历史。13.0 还在补 Alerts Activity UI（事件查看器）和 Instance Drawer 钻取。

- 后端 `public/app/features/alerting/`，加上 Go 端 `pkg/services/ngalert/`（NGA 体系，即 Next Gen Alerting）。
- 12.0 GA 的 Grafana-managed alerts + recording rules 是与 Prometheus-style rule files 平行的另一套体系，存储在 Grafana 自己的 SQL 里，与 Unified Storage（v12 把 folders + dashboards 统一存储的迁移）的方向一致。
- 12.0 还引入了 Alert Rule Migration Tool（v12 升级期常用），13.0 引入"Allow restricting contact point integration types"、Rules API v2、通知 API 迁移、Mimir Alertmanager auto-sync 等。

### 2.5 横切的"集成层"

把上面四块捏在一起的有四样东西，单独点名：

- **Provisioning**：把 datasource / dashboard / alert rule / folder / fine-grained access 用 YAML 文件落到磁盘或 Git 仓库。12.0 起 Git Sync GA，13.0 把 `_folder.json` 写入、Commit signing（GPG/SSH/S/MIME）、webhook replay protection、PR comment on multi-org 一起补完。
- **Plugin framework**：四类插件（datasource / panel / app / renderer）都走同一套 SDK，存放在 `pkg/plugins/`。composable 平台能持续扩张依赖的就是它。
- **AuthN / AuthZ**：内置基础认证 + OAuth（GitHub / GitLab / Google / Azure AD / Generic），Enterprise 补 SAML / LDAP / SCIM / Team sync / Enhanced LDAP。
- **Unified Storage**：12.0 GA 的 folders + dashboards 统一存储模型是 13.0 Dynamic Dashboards 的物理基础。

把上面这些用一句话串起来就是：**数据源负责"取数"、面板负责"画数"、告警负责"盯数"、探索负责"现拼"、Provisioning 负责"管配置"**——五块各司其职，composable 是它们之间的接缝。

---

## 三、架构分析：TS + Go 双栈、API 抽象、Plugin SDK

Grafana 仓库大小约 1.8 GB（`size: 1821447` KB，按 GitHub API），主语言从 GitHub Languages 维度显示为 TypeScript，因为后端 Go 占比相对前端+插件代码量在统计上低于 TS。它的工程结构有三个值得拆的点。

### 3.1 后端 Go 服务

`pkg/` 目录是后端 Go 代码的家，关键子包：

- `pkg/server/` 启动入口与 HTTP 服务；
- `pkg/api/` REST API handlers；
- `pkg/services/` 业务服务（`ngalert/` 告警、`sqlstore/` 数据访问、`dashboards/` 看板、`authn/` 认证、`provisioning/` 配置加载、`featuremgmt/` 特性开关）；
- `pkg/tsdb/` 时序数据后端抽象（TSDB interface + 各数据源实现）；
- `pkg/plugins/` plugin SDK 与插件生命周期；
- `pkg/apiserver/` Kubernetes 风格的 Resource API（folders / dashboards / provisioning repositories 都通过这套 API 暴露）；
- `pkg/storage/` Unified Storage 实现层；
- `pkg/expr/` 表达式（`$__expr`、`math` 等 transformation / expression 引擎）；
- `pkg/infra/` 通用基础设施（中间件、bus、设置）。

SQL 迁移系统 `pkg/services/sqlstore/migrations/migrations.go` 显式声明了三条铁律：

> 1. Never change a migration that is committed and pushed to main
> 2. Always add new migrations (to change or undo previous migrations)
> 3. Some migrations are not yet written (rename column, table, drop table, index etc)
> 4. Putting migrations behind feature flags is no longer recommended...

这是经验之谈：跨大版本的 schema 演进一旦写错就回不去。把"破坏性变更"统一用新的 migration 来表达，是它能维持十几年的工程基础。

### 3.2 前端 TypeScript 应用

`public/app/` 里的 features 目录就是上面四模块的物理实现。架构上，13.0 进一步清理了历史包袱：

- 12.0 拆掉 Angular 框架（`Removal of Angular` 是 12.0 的 breaking change）；
- 13.0 移除 `dashboardScene` 和 `publicDashboardsScene` feature toggle（v2 路径正式统一）；
- 13.0 引入 `forward_user_agent` 选项到数据源、Scenes 化的 `Dashboard` 目录、新 `panel-screenshot` API；
- 12.0 GA 的 Blazing fast table panel、SQL Expressions、Dynamic Dashboards 在 13.0 进入正式生命周期。

13.1.0 的 changelog 显示 30+ 项 Alerting 改动集中在"alerts activity drawer / instance drilldown / silence flow"上，这是告警模块从"规则引擎"演化为"事件响应中心"的明确信号。

### 3.3 Plugin SDK 与 Kubernetes 风格 API

13.0 有几件事需要点出来：

- **API server 化**：`pkg/apiserver/` 走 Kubernetes 风格的 Group / Version / Resource 模型。folders、dashboards、provisioning repositories、access control 都是 Kubernetes 风格的 resource。Provisioners 可以用 GitOps 工作流对它们做 reconcile 风格的读写。
- **Plugin decoupling**：13.0 把 MSSQL / PostgreSQL / InfluxDB / Tempo / Graphite 的前后端各自拆成独立 plugin 仓库。这等于把 Grafana 主仓库往"shell"方向瘦身，把数据源实现外包。
- **Data source async 化**：用 React 钩子替代旧的同步 `datasourceSrv`，为后续 V2 dashboard 跑在 React 18 并发模式下铺路。

理解这三件事，就理解了 Grafana 12 → 13 的真正含义：**主仓库在演化为 platform shell，业务实现（数据源、应用、面板）在演化为独立 plugin**。

---

## 四、一次查询的完整任务流

抽象出"一次查询"的任务流，能让四模块协同的边界一眼可见。

1. **用户在 Explore 输入 PromQL**：`{job="api", status="5xx"}`。
2. **Explore 把请求构造成 `DataQueryRequest`**：包含时间范围、interval、max data points、scoped variables，发送给 `prometheus` 数据源。
3. **数据源 plugin（前后端各一段）执行查询**：前端把 PromQL 序列化进 HTTP 请求，Go 后端 `pkg/tsdb/prometheus/` 把它转成对 Prometheus `/api/v1/query_range` 的调用；如果是 Loki，前端加 `X-Scope-OrgID`，后端 `pkg/tsdb/loki/` 调用 `/loki/api/v1/query_range`。
4. **数据帧（DataFrame）回到前端**：插件把 JSON 转换为 `DataFrame[]`（字段化表格），送到 panel 处理。
5. **Panel 拿到 DataFrame**：内置 Graph panel 走 `uPlot` 渲染（13.0 之前已是大头），Logs panel 在 v12 走专门优化的渲染路径。
6. **Explore 显示结果并保留 label filters**：用户点其中一个 label 值，前端把"过滤后的 label set"作为下次查询的额外参数送回 step 2——这就是 README 里说的"Experience the magic of switching from metrics to logs with preserved label filters"。
7. **可选步骤：保存为 dashboard**：把 step 2-5 的查询参数 + panel 配置存为 dashboard JSON（V1）或 V2 资源（V2 schema）。

把"告警"叠加进来：把 step 7 的查询复制到 alert rule，评估器会按 evaluation interval 重复 step 2-4，state machine（`Inactive / Pending / Firing / Resolved`）把变化送进通知路由。

这个任务流解释了一个常见困惑：为什么 Grafana 必须把 plugin SDK 设计成"前端代码 + 后端代码"两段？因为 step 3 必须分两段——前端做查询编辑器（语法高亮、指标补全），后端做对真实存储的 RPC 调用。两段都能用 Go（后端）+ TypeScript（前端）同仓维护，这是 composable 的工程基础。

---

## 五、OSS / Enterprise / Cloud 边界

Grafana 的商业模式建立在"开源可商用 → 大企业要 RBAC/SCIM/LDAP 等 → 想托管就用 Cloud"这条链上。仓库 LICENSE 是 AGPL-3.0，加 Apache-2.0 例外（见 `LICENSING.md`），意味着你可以自托管、可以商用、但改了源码必须公开对应修改；如果你想避开 AGPL 传染条款，要么买 Enterprise 许可证，要么用 Cloud。

三档边界（基于 `docs/sources/introduction/grafana-enterprise.md` 与 `docs/sources/setup-grafana/` 公开文档）：

| 能力 | OSS | Enterprise | Cloud |
|------|-----|------------|-------|
| 数据源 / 面板 / 告警 / Explore 核心 | ✅ | ✅ | ✅ |
| 官方 Premium 数据源（Oracle、Splunk、ServiceNow、Snowflake 等） | ❌ | ✅ | ✅ |
| SAML / SCIM / Enhanced LDAP / Team Sync | ❌ | ✅ | ✅ |
| 报表 / Reporting / Enterprise plugins | ❌ | ✅ | ✅ |
| Drilldown Apps（Metrics / Logs / Traces / Profiles） | 部分 | ✅ | ✅ |
| Investigations / SLO / IRM / OnCall / k6 / Frontend Observability | ❌ | ❌ | ✅ |
| Grafana Assistant（AI 查询助手） | ❌（13.0 引入 on-prem 评估中） | Enterprise 评估中 | ✅ |
| Git Sync（dashboard GitOps） | ✅ GA | ✅ | ✅ |
| Audit logging 完整版 | 基础 | 完整 | 完整 |
| 支持服务 | 社区 | 24x7 | 24x7 |

13.0 的 What's new 标注 `products: cloud / enterprise / oss` 三个标签，正是因为"同一版本三档能力不同"。12.0 GA 的 Drilldown、SCIM、Cloud Migration Assistant、Grafana-managed alerts、Plugin management 在三档上分布也遵循上表。

实际意义：

- **个人 / 小团队 / 自托管**——OSS 完全够用，配 Prometheus / Loki / Tempo / Mimir / Pyroscope 自托管栈是经典组合。
- **中型企业**——需要 SAML、SCIM、RBAC 精细化、报告、合规审计、Premium 数据源时，要么买 Enterprise License，要么考虑 Cloud（按用量计费、含托管的 Mimir/Loki/Tempo/Pyroscope）。
- **大企业**——当"运维一支 50+ 人的 SRE / 平台团队"成为长期成本时，Cloud 的边际成本开始低于自建。

---

## 六、与 Prometheus / Loki / Tempo 栈的协同关系

Grafana 自从 v7 之后已经基本退出"也做时序后端"的角色，转而和 Grafana 旗下的开源数据后端群结成"LGTM" 栈：**Loki（日志）+ Grafana（前端）+ Tempo（追踪）+ Mimir（指标长期存储）**，外加 **Pyroscope（profile / continuous profiling）**。它们之间的协同关系如下：

| 后端 | 角色 | 与 Grafana 的关系 |
|------|------|-------------------|
| **Prometheus** | 短期指标（默认 15 天） | 经典搭配，Prometheus scrape 一次、Grafana 查询一次 |
| **Mimir** | 长期指标（横向扩展、Cortex 后继） | Grafana Cloud 默认后端；13.0 的 `Mimir Alertmanager auto-sync` 让 Grafana 告警状态自动同步到 Mimir Alertmanager |
| **Loki** | 日志（label-based 索引） | 与 Grafana 通过 LogQL 集成；13.0 `Include error in Loki state history when exec_err_state is Alerting` 改善告警可观测性 |
| **Tempo** | 追踪（trace 存储） | 与 Grafana 通过 TraceQL 集成；v12 GA Traces Drilldown；Explore 中 trace ↔ log ↔ metric 跳转 |
| **Pyroscope** | Profile | 与 Grafana 通过 Pprof 集成；Profiles Drilldown |
| **Agent / Alloy** | 数据采集 | Grafana Agent 是 Prometheus + Loki + Tempo + Pyroscope 的统一采集端，13.0 起持续迭代为 Alloy |

这套栈的设计哲学是 **"Mimir/Loki/Tempo/Pyroscope 各管一摊不可观测性数据，Grafana 是查询它们的前端"**。它解决了三个老问题：

- 数据量上来后单实例 Prometheus 不够 → 用 Mimir 做横向扩展；
- Loki 用便宜的 object storage 存日志 → 比 ES 便宜 1-2 个数量级；
- Trace 不在指标里硬塞 → 用 Tempo 专门存。

> 当你的数据已经有现成的存储（自建 ES / CloudWatch / 自建 ClickHouse / Datadog 导出），Grafana 仍能作为查询前端——它对 30+ 数据源都有 plugin。把 Grafana 看作"对所有可观测性数据做统一查询"是更准确的定位。

---

## 七、最小部署

下面是一份可在本机跑起来的最小路径。仓库 13.0+ 推荐用官方 Docker 镜像 `grafana/grafana:13.0.3`（13.1.0 也已发布；专门的 OSS 变体 `grafana/grafana-oss` 在 Docker Hub 当前最高到 13.0.2，行为一致）。

```bash
# 1. 拉镜像
docker pull grafana/grafana:13.0.3

# 2. 启动一个最小实例（默认 sqlite 存储 + 3000 端口）
docker run -d \
  -p 3000:3000 \
  --name=grafana \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana:13.0.3

# 3. 浏览器打开 http://localhost:3000，默认账号 admin / admin
# 4. 第一个数据源：Configuration → Data sources → Add data source → Prometheus
#    URL: http://host.docker.internal:9090（指向宿主机的 Prometheus）
# 5. 第一个面板：Explore → 选 Prometheus 数据源 → 输入 PromQL
```

要让 Explore 有真实数据可看，最简单的搭配是本地起一个 Prometheus 并启动一个导出器：

```bash
# 启 Prometheus
docker run -d -p 9090:9090 --name=prom prom/prometheus

# 启 node_exporter（采集宿主机指标）
docker run -d -p 9100:9100 --name=node-exporter prom/node-exporter
```

进 Grafana → Data sources → Prometheus → URL 填 `http://host.docker.internal:9090` → Save & test。回到 Explore 输入 `up`，就能看到 1/0 的存活指标。

> **生产部署的最小清单**：1) 改 sqlite 为 mysql / postgres；2) 反向代理前置 + TLS；3) SMTP 配告警通知；4) 接入 SSO（OIDC 或 LDAP）；5) 用 Provisioning + Git Sync 配 datasource / dashboard / alert rule，让配置可审计。完整文档见 [Grafana Setup](https://grafana.com/docs/grafana/latest/setup-grafana/)。

---

## 八、什么时候该用、什么时候不要用

按上面拆出的边界做决策，比看 feature list 更有用。

**适合用 Grafana 的场景**

- 团队已经或准备用 Prometheus / Loki / Tempo / Mimir / Pyroscope 中的一个或多个，需要一个统一查询前端。
- 团队规模超过 3 个 SRE / 后端 / 数据工程师，需要把面板 / 告警 / 数据源以代码形式管理（Provisioning、Git Sync、Terraform provider）。
- 需要在同一个 UI 里给业务方、SRE、运维、管理层展示不同抽象层（业务 KPI + 系统指标 + 告警事件）。
- 需要 Drilldown 类高阶排障工作流：Metrics / Logs / Traces / Profiles 跳来跳去，跨数据源 label 透传。

**不建议用 Grafana 的场景**

- **只有 1 个服务、1 个指标、1 个开发者**——Grafana 太重。直接看 Prometheus / InfluxDB 自带的 UI 就行。
- **强依赖重型 APM（应用性能监控）能力**——Grafana 不做自动 instrumentation，也不做 flame graph 自动生成（Pyroscope 做采集、Grafana 展示）。如果想要"装个 agent 就能看到全链路"，Datadog / New Relic / Elastic APM 这类是更匹配的产品。
- **强依赖机器学习异常检测**——Grafana 13.0 的 Alerting 支持 group_by、silence、enrichment，但自动异常检测能力远不如 Cloud / Datadog。可以在 Cloud 档或自建 + 额外 ML 服务上做。
- **已经把可观测性数据全托管在单一 SaaS 里**——比如全在 Datadog，再叠一层 Grafana 通常只是给管理面加负担。除非有意把 vendor lock-in 拆掉。

**升级决策**

- 11.x → 12.x：是否需要 Dynamic Dashboards、V2 schema、Drilldown Apps、SCIM、SQL Expressions、Cloud Migration Assistant？需要 → 升。
- 12.x → 13.x：是否需要 Git Sync GA、Dynamic Dashboards GA、Annotation Clustering GA、Grafana Assistant（on-prem 评估）、Grafana Advisor GA、Restore deleted dashboards GA？需要 → 升。13.0 同期做了 Angular 移除、`_folder.json` 写入、Provisioning 文件协议升级，先在测试环境跑 upgrade guide。

---

## 九、学习路径与延伸阅读

按"先理解结构、再上手、再扩展"的顺序，给一条可执行的阅读路径：

1. **半小时理解结构**：官方文档 *Fundamentals* 与 *Introduction* → 再看 13.0 What's new 视频（`OYd0ahylGGI`，13.0 发布博文）→ 看本仓库 `public/app/features/` 顶层目录，建立物理直觉。
2. **一小时上手**：用第七节 Docker 步骤拉起一个最小实例，添加 Prometheus 数据源 + 一个 Stat 面板 + 一个 alert rule。
3. **一天做生产化**：把 sqlite 换成 mysql、接入公司 SSO、用 Provisioning 文件管理 datasource / dashboard，提交到一个 Git 仓库。
4. **一周扩展**：把 Loki / Tempo / Mimir / Pyroscope 各起一个，把数据采集换成 Grafana Agent / Alloy，跑通"指标 + 日志 + 追踪 + profile"全链路。
5. **一个月做平台化**：用 Terraform provider 管 datasource / folder，把 RBAC 配到 team 级别，把 alert rule 落到 `rules/` 目录走 Git Sync。

延伸阅读：

- 官方文档：[grafana.com/docs](https://grafana.com/docs/)
- What's new 13.0：[Grafana 13.0 release highlights](https://grafana.com/docs/grafana/latest/whatsnew/whats-new-in-v13-0/)
- What's new 12.0：[Grafana 12.0 release highlights](https://grafana.com/docs/grafana/latest/whatsnew/whats-new-in-v12-0/)
- 仓库：[github.com/grafana/grafana](https://github.com/grafana/grafana)
- Play 实例（在线试）：[play.grafana.org](https://play.grafana.org/)
- Plugin Hub：[grafana.com/grafana/plugins](https://grafana.com/grafana/plugins/)
- LGTM 栈说明：[grafana.com/oss](https://grafana.com/oss/)

---

**总结**：Grafana 是把"取数（datasource）、画数（panel）、盯数（alerting）、现拼（explore）、管配置（provisioning）"五件事组合起来的可观测性前端平台。理解它，先理解这五块的边界与协同；然后判断你的团队处在哪一档（OSS / Enterprise / Cloud）、你的数据后端是哪个（Prometheus / Mimir / Loki / Tempo / Pyroscope / 其它），剩下的就是落地配置。
