---
title: "Grafana：开源可观测性平台不是 dashboard 工具，理解它的边界比记住功能更重要"
date: 2026-06-26T21:03:36+08:00
slug: grafana-grafana-open-source-observability-platform-guide
github_repo: "grafana/grafana"
source_key: "gh:grafana/grafana"
description: "Grafana 已经从单一 dashboard 工具演化成数据源、面板、告警、探索四模块协同的可观测性平台。本文从架构、模块边界、OSS/Enterprise/Cloud 划分、与 Prometheus/Loki/Tempo 栈的协同关系四个角度重新理解它。"
draft: false
categories: ["技术笔记"]
tags: ["可观测性", "开源"]
---

# Grafana：开源可观测性平台不是 dashboard 工具，理解它的边界比记住功能更重要

Grafana 常被当成"画 dashboard 的工具"，这个定位已经过时了。它现在做的事，是把数据源、面板、告警、探索四个模块编排成一个可观测性前端平台：数据留在 Prometheus、Loki、Tempo、Mimir、ES、CloudWatch 这些后端里，Grafana 负责在它们之上做查询、可视化和告警评估。仓库约 76k stars、AGPL-3.0、TypeScript 前端加 Go 后端，v13.0 已于 2026 年 4 月发布。判断它是否适合你的技术栈，问题不是"Grafana 能不能画图"，而是它在你的数据后端之上补了哪一块。

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
4. 解释 Grafana 12.0（2025-05 GA）和 13.0（2026-04 GA）两个里程碑分别解决了什么遗留问题，并据此判断是否值得升级。
5. 在本机用 Docker 拉起一个最小可用的 Grafana 实例，配置好第一个数据源与第一张面板。

---

## 一、核心判断：Grafana 是什么、不是什么

把 Grafana 当成"画 dashboard 的工具"是最常见的认知错位。它当前的能力边界，可以用四个"不是"来划清楚：

- **不是数据存储**。Grafana 不保存你的时序数据、日志、追踪或 profile。所有原始数据都在它对接的数据源里——Prometheus 存指标、Loki 存日志、Tempo 存追踪、Pyroscope 存 profile、ES / CloudWatch / Postgres 各自管自己的数据。Grafana 内部有一个 SQL 存储（默认 sqlite，可换 mysql / postgres），但那只是放用户、组织、面板 JSON、告警规则元数据。
- **不是指标采集器**。它不会从你的应用里 pull / push 数据。采集端是 Prometheus（agent 模式）、Alloy、OpenTelemetry Collector、Telegraf、Vector 的事。Grafana 只在已采集到的数据上做查询、可视化、告警评估。
- **不是告警管理器**。它确实有告警规则引擎（Grafana-managed rules）和一个兼容 Prometheus Alertmanager 的通知路由层，但它是和外部 Alertmanager 平行存在的另一条线：Grafana-managed alerts 走自己的评估器、自己的 notification policies、自己的 silences 体系。
- **不是单体应用**。它由 Go 后端（`pkg/`）、TypeScript 前端（`public/app/`）、插件 SDK（`pkg/plugins/`）、SQL 迁移系统（`pkg/services/sqlstore/migrations/`）和一套 Kubernetes 风格的 Resource API 构成。任何一个组件被裁掉，剩下的部分仍能跑——比如只用前端 + 一个 Prometheus 数据源，就能组成"最小画图"。

那它是什么？官方仓库自述是 *The open and composable observability and data visualization platform*——"开源且可组合的可观测性与数据可视化平台"。关键词是 composable（可组合）和 platform（平台）。composable 指数据源、面板、告警、探索四块通过 plugin SDK 解耦，每一块都能独立替换或扩展；platform 指它在画图之外配了围绕团队使用的一整套能力：GitOps（Git Sync）、RBAC、Provisioning、SCIM、审计、API server、Drilldown Apps、Assistant 等。个人开发者的画图工具不需要这些，平台需要。

所以理解 Grafana 的关键，是理解它如何编排，而不是它能画出什么图。

---

## 二、系统地图：四大模块的边界与协同

仓库 `public/app/features/` 目录就是这张地图的物理映射。下面四个目录对应四个一等公民模块，外加一条横切线是 provisioning / authentication / plugins。

### 2.1 数据源（datasources）

职责：把"外部存储的查询语言"翻译成 Grafana 内部的 `DataQueryRequest` / `DataQueryResponse`。

- 后端在 `pkg/tsdb/`，前端在 `public/app/features/datasources/`。每个数据源是一个 plugin，自带 `getBackendFactory` / `datasource` 工厂。
- 数据源插件类型分四类：data source（拉数据）、panel（画图）、app（顶层应用，如 drilldown apps）、renderer（截图服务）。其中 data source 数量最多。
- 13.x 起，仓库在做"数据源解耦"重构：MSSQL / PostgreSQL / InfluxDB / Tempo / Graphite 的前后端被拆成独立 plugin 仓库。这意味着 Grafana 仓库本身在瘦身，13.1.0 的 changelog 里能看到 `Finish decoupling mssql & postgresql - backend`、`InfluxDB: Decouple frontend` 这样的条目。
- 13.1 合入的 `Introduce async APIs and hooks as replacement for datasourceSrv` 是一个值得留意的信号：旧的 `datasourceSrv` 同步 API 正在被 React 友好的 async 钩子替换，前端架构在持续现代化。

> 实操含义：当你的数据不在已官方支持的数据源里时，先看 Grafana Plugin Hub 而不是自己去改 Grafana。composable 平台的扩展点比内置实现更重要。

### 2.2 面板与 Dashboard

职责：在"已查询到的结果"上做变换、绘制、交互。

- 前端目录 `public/app/features/panel/`，加上具体的 `canvas`、`logs`、`geo`、`dashboard-scene`、`dashboard`、`browse-dashboards` 等子模块。Dynamic Dashboards（V2 看板）在 v12 处于 experimental，13.0 起对所有自托管实例和 Cloud 用户默认开启，支持 section-level 变量、模板化面板、面板复用（LibraryPanels），另有一个独立的能力是删除恢复（Restore deleted dashboards，13.0 GA）。
- 内置面板以 Time series、Stat、Gauge、Bar gauge、Table、Pie chart、Heatmap、Histogram、Logs、Geomap、Canvas、Trend、State timeline、Node graph、XY chart、Text 等为主。旧的 Graph 面板已在 v11 被移除、由 Time series 取代，13.0 升级 React 19 时又从 `@grafana/ui` 清掉了 `Graph`、`GraphWithLegend` 等遗留组件——如果你在老文章里看到 Graph 面板的教程，注意它已经过时。
- 仪表板模型有两套：V1（JSON 直接存盘）和 v12 引入的 V2 schema（`new-dashboards-schema`）。13.0 起 Dynamic Dashboards 默认走 V2，新功能主要长在 V2 上。要注意 V2 有单向性：官方文档明确，一旦迁移到 dynamic dashboard（V2 schema），无法迁回。

### 2.3 探索（Explore）

职责：脱离 dashboard 的"临时查询工作台"，是排障的主入口。

- 目录 `public/app/features/explore/`。Metrics / Logs / Traces 三个 Drilldown App 在 v12 GA，作为面向"不写查询也能逛数据"的独立入口与 Explore 并存。
- Explore 的关键能力：ad-hoc 查询、metric ↔ log 切换时保留 label filters、split view（多查询并排）、流式日志（streaming）。
- 与 dashboard 的差别：dashboard 是事前设计好的视图，explore 是现场拼接的查询。SRE 排障流程里，前者用于巡检和 review，后者用于事件响应。

### 2.4 告警（alerting）

职责：定义规则、评估状态、发送通知、记录历史。

- 前端在 `public/app/features/alerting/`，Go 端在 `pkg/services/ngalert/`（Next Gen Alerting）。
- Grafana-managed alerts 和 recording rules 在 v12 GA，与 Prometheus-style 的 rule files 平行，规则存储在 Grafana 自己的 SQL 里。
- 13.x 期间告警模块的重心从"规则引擎"转向"事件响应"：13.1.0 的 changelog 里，Alerting 相关的改动集中在 Alerts Activity（事件查看器）、Instance drawer 钻取、silence 流程上，另有 Rules API v2、限制 contact point 集成类型、Mimir Alertmanager auto-sync 配置等。

### 2.5 横切的"集成层"

把上面四块捏在一起的有四样东西，单独点名：

- **Provisioning**：把 datasource / dashboard / alert rule / folder / fine-grained access 用 YAML 文件落到磁盘或 Git 仓库。Git Sync（dashboard 直接同步 GitHub / GitLab / Bitbucket 仓库，可在 UI 内 commit、发 PR）在 v12 是 experimental，13.0 GA；13.1.0 又补了 `_folder.json` 写入、commit signing 配置（GPG / SSH / S/MIME）、GitHub webhook 防重放、多 org 下 PR 评论修复等细节。
- **Plugin framework**：四类插件（datasource / panel / app / renderer）都走同一套 SDK，存放在 `pkg/plugins/`。composable 平台能持续扩张依赖的就是它。
- **AuthN / AuthZ**：内置基础认证 + OAuth（GitHub / GitLab / Google / Azure AD / Generic），Enterprise 补 SAML / LDAP / SCIM / Team sync / Enhanced LDAP。
- **Unified Storage**：folders + dashboards 统一存储是 13.0 Dynamic Dashboards 的物理基础。

一句话串起来：数据源负责取数，面板负责画数，告警负责盯数，探索负责现拼，Provisioning 负责管配置。五块各司其职，composable 是它们之间的接缝。

---

## 三、架构分析：TS + Go 双栈、API 抽象、Plugin SDK

Grafana 仓库按 GitHub Languages 统计，TypeScript 占 48% 左右、Go 占 45% 左右，前端体量略大于后端。它的工程结构有三个值得拆的点。

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

SQL 迁移系统 `pkg/services/sqlstore/migrations/migrations.go` 开头的注释写明了维护者的规矩，摘录前三条和最后一条：

> 1. Never change a migration that is committed and pushed to main
> 2. Always add new migrations (to change or undo previous migrations)
> 3. Some migrations are not yet written (rename column, table, drop table, index etc)
> 5. Adding a migration is a last resort. Resources are moving to the app platform, so schema added here is a dead end. Every migration also runs on every instance that upgrades and can never be rolled back or changed afterwards.

最后一条最有分量：schema 一旦加上就永远回不去，所以加 migration 是最后手段。跨大版本的 schema 演进一旦写错就没有撤销键，Grafana 能平滑升级十几年，靠的就是这类纪律。

### 3.2 前端 TypeScript 应用

`public/app/` 里的 features 目录就是上面四模块的物理实现。架构上，13.x 前后清理了不少历史包袱：

- 12.0 拆掉 Angular（Angular 插件支持在 11 关闭默认开关，12 彻底移除，是 12.0 的 breaking change）；
- 13.0 把核心应用从 React 18 升到 React 19，连带从 `@grafana/ui` 移除 `Graph`、`GraphWithLegend` 等旧组件；
- 13.0 起 Dynamic Dashboards 默认开启，V2 dashboard 路径正式统一；
- 12.0 重做的 Table 面板（官方说法是大表加载、排序、过滤快数倍）和 v12 露头的 SQL Expressions、Dynamic Dashboards，在 13.x 里继续迭代。

13.1.0 的 changelog 显示 30 多项 Alerting 改动集中在 alerts activity drawer、instance drilldown、silence flow 上，告警模块正从"规则引擎"往"事件响应中心"演化。

### 3.3 Plugin SDK 与 Kubernetes 风格 API

13.x 有几件事需要点出来：

- **API server 化**：`pkg/apiserver/` 走 Kubernetes 风格的 Group / Version / Resource 模型。folders、dashboards、provisioning repositories、access control 都是 Kubernetes 风格的 resource，Provisioner 可以用 GitOps 工作流对它们做 reconcile 式读写。
- **Plugin decoupling**：13.x 把 MSSQL / PostgreSQL / InfluxDB / Tempo / Graphite 的前后端各自拆成独立 plugin 仓库。这等于把 Grafana 主仓库往"shell"方向瘦身，把数据源实现外包。
- **Data source async 化**：13.1 用 React 钩子替代旧的同步 `datasourceSrv`，配合 13.0 的 React 19 升级，前端在往并发渲染的方向走。

理解这三件事，就理解了 Grafana 12 → 13 的主线：主仓库在演化为 platform shell，业务实现（数据源、应用、面板）在演化为独立 plugin。

---

## 四、一次查询的完整任务流

抽象出"一次查询"的任务流，能让四模块协同的边界一眼可见。

1. **用户在 Explore 输入 PromQL**：`{job="api", status="5xx"}`。
2. **Explore 把请求构造成 `DataQueryRequest`**：包含时间范围、interval、max data points、scoped variables，发送给 `prometheus` 数据源。
3. **数据源 plugin（前后端各一段）执行查询**：前端把 PromQL 序列化进 HTTP 请求，Go 后端 `pkg/tsdb/prometheus/` 把它转成对 Prometheus `/api/v1/query_range` 的调用；如果是 Loki，前端加 `X-Scope-OrgID`，后端 `pkg/tsdb/loki/` 调用 `/loki/api/v1/query_range`。
4. **数据帧（DataFrame）回到前端**：插件把 JSON 转换为 `DataFrame[]`（字段化表格），送到 panel 处理。
5. **Panel 拿到 DataFrame**：Time series panel 走 `uPlot` 渲染，Logs panel 在 v12 重做过专门优化的渲染路径。
6. **Explore 显示结果并保留 label filters**：用户点其中一个 label 值，前端把过滤后的 label set 作为下次查询的额外参数送回 step 2——README 里 Explore Logs 条目那句 "Experience the magic of switching from metrics to logs with preserved label filters" 说的就是这件事。
7. **可选步骤：保存为 dashboard**：把 step 2-5 的查询参数 + panel 配置存为 dashboard JSON（V1）或 V2 资源（V2 schema）。

把"告警"叠加进来：把 step 7 的查询复制到 alert rule，评估器会按 evaluation interval 重复 step 2-4，state machine（`Inactive / Pending / Firing / Resolved`）把变化送进通知路由。

这个任务流解释了为什么 plugin SDK 必须是"前端代码 + 后端代码"两段：step 3 天然分两段，前端做查询编辑器（语法高亮、指标补全），后端做对真实存储的 RPC 调用。两段分别用 TypeScript 和 Go 编写、同仓维护，这就是 composable 的工程基础。

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
| Drilldown Apps（Metrics / Logs / Traces / Profiles） | ✅（12.0 GA） | ✅ | ✅ |
| Investigations / SLO / IRM / OnCall / k6 / Frontend Observability | ❌ | 部分 | ✅ |
| Grafana Assistant（AI 查询助手） | ✅（13.0 起 public preview，需连接 Cloud 账号） | ✅（同左） | ✅ |
| Git Sync（dashboard GitOps） | ✅（13.0 GA） | ✅ | ✅ |
| Audit logging 完整版 | 基础 | 完整 | 完整 |
| 支持服务 | 社区 | 24x7 | 24x7 |

13.0 的 What's new 用 `products: cloud / enterprise / oss` 标签区分每项特性的适用档位，正是因为"同一版本，三档能力不同"。Assistant 是个值得注意的例子：13.0 起自托管用户（Enterprise 和 OSS）通过一键设置连接 Grafana Cloud 账号，也能用上 Assistant（public preview）——AI 能力没有完全锁在 Cloud 里，但依赖 Cloud 账号这一依赖关系仍然存在。

实际意义：

- **个人 / 小团队 / 自托管**——OSS 完全够用，配 Prometheus / Loki / Tempo / Mimir / Pyroscope 自托管栈是经典组合。
- **中型企业**——需要 SAML、SCIM、RBAC 精细化、报告、合规审计、Premium 数据源时，要么买 Enterprise License，要么考虑 Cloud（按用量计费、含托管的 Mimir/Loki/Tempo/Pyroscope）。
- **大企业**——当"运维一支 50+ 人的 SRE / 平台团队"成为长期成本时，Cloud 的边际成本开始低于自建。

---

## 六、与 Prometheus / Loki / Tempo 栈的协同关系

Grafana 自己不做存储，它和 Grafana 旗下的开源数据后端结成常说的 "LGTM" 栈：**Loki（日志）+ Grafana（前端）+ Tempo（追踪）+ Mimir（指标长期存储）**，外加 **Pyroscope（continuous profiling）**。它们之间的协同关系如下：

| 后端 | 角色 | 与 Grafana 的关系 |
|------|------|-------------------|
| **Prometheus** | 短期指标（默认保留 15 天） | 经典搭配：Prometheus 负责采集存储，Grafana 负责查询展示 |
| **Mimir** | 长期指标（横向扩展、Cortex 后继） | Grafana Cloud 默认指标后端；13.1 的 Mimir Alertmanager auto-sync 让 Grafana 告警配置自动同步到 Mimir Alertmanager |
| **Loki** | 日志（label-based 索引） | 与 Grafana 通过 LogQL 集成 |
| **Tempo** | 追踪（trace 存储） | 与 Grafana 通过 TraceQL 集成；v12 GA Traces Drilldown；Explore 中 trace ↔ log ↔ metric 跳转 |
| **Pyroscope** | Profile | 与 Grafana 通过 pprof 集成；Profiles Drilldown |
| **Alloy** | 数据采集 | Grafana Alloy 是 OTel Collector 的厂商中立发行版，把指标、日志、追踪、profile 的采集收进一个进程；它也是 Grafana Agent 系列的官方后继，官方提供从 Agent Static / Flow / Operator 迁移到 Alloy 的指南 |

这套栈解决的是三个常见瓶颈：单实例 Prometheus 撑不住规模时，用 Mimir 做横向扩展；日志量太大导致 ES 索引成本失控时，Loki 只对 label 建索引、正文进 object storage，用查询时的计算换存储成本，代价是全文检索能力弱于 ES；trace 不想硬塞进指标系统时，用 Tempo 专门存。

> 当你的数据已经有现成的存储（自建 ES / CloudWatch / 自建 ClickHouse / Datadog 导出），Grafana 仍能作为查询前端——官方维护的数据源插件覆盖了主流存储，Plugin Hub 上还有社区插件。把 Grafana 看作"对所有可观测性数据做统一查询"是更准确的定位。

---

## 七、最小部署

下面是一份可在本机跑起来的最小路径。截至 2026 年 9 月，最新的稳定版本线是 13.2（13.2.1 于 2026-09-02 发布），官方 Docker 镜像直接用版本号拉取即可；`grafana/grafana-oss` 这个独立 OSS 变体镜像更新较慢，目前最高只到 13.0.2，建议用主镜像。

```bash
# 1. 拉镜像
docker pull grafana/grafana:13.2.1

# 2. 启动一个最小实例（默认 sqlite 存储 + 3000 端口）
docker run -d \
  -p 3000:3000 \
  --name=grafana \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana:13.2.1

# 3. 浏览器打开 http://localhost:3000，默认账号 admin / admin
# 4. 第一个数据源：Connections → Data sources → Add data source → Prometheus
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
>
> **一个升级陷阱**：13.0.0 存在一个已知的迁移 bug，可能导致 dashboards 和 folders 丢失或回退（官方 What's new 明确警告）。生产环境升级不要停在 13.0.0，直接上 13.0.1 及以上；如果已经在 13.0.0 上遇到问题，官方给的路径是先恢复数据库再升 13.0.1。

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
- **强依赖机器学习异常检测**——Grafana 的告警是规则驱动（阈值、表达式、reduce 函数），自动异常检测不是它的强项；这类需求要么上 Cloud 档的机器学习能力，要么自建后接外部服务。
- **已经把可观测性数据全托管在单一 SaaS 里**——比如全在 Datadog，再叠一层 Grafana 通常只是给管理面加负担。除非有意把 vendor lock-in 拆掉。

**升级决策**

- 11.x → 12.x：是否需要 Drilldown Apps、Grafana-managed alerts GA、SCIM（preview）、SQL Expressions（preview）、Cloud Migration Assistant？需要 → 升。同时注意 12.0 的 breaking changes：Angular 移除（还在用 Angular 插件的先迁移）、数据源 UID 格式收紧、Tempo 的 Aggregate by 移除。
- 12.x → 13.x：是否需要 Git Sync GA、Dynamic Dashboards GA（V2 schema 默认开启）、Restore deleted dashboards GA、Assistant on-prem（preview）？需要 → 升。两个前置检查：一是 V2 schema 有单向性，dashboard 迁移成 dynamic 后无法迁回，先在测试环境验证存量看板；二是不要停在 13.0.0（迁移 bug），直接上 13.0.1+。13.0 还把核心应用从 React 18 升到 React 19，依赖旧 UI 组件的插件需要确认兼容性。

---

## 九、学习路径与延伸阅读

按"先理解结构、再上手、再扩展"的顺序，给一条可执行的阅读路径：

1. **半小时理解结构**：官方文档 *Fundamentals* 与 *Introduction*，再看 13.0 的 What's new 与升级指南，然后翻一下本仓库 `public/app/features/` 顶层目录，建立物理直觉。
2. **一小时上手**：用第七节 Docker 步骤拉起一个最小实例，添加 Prometheus 数据源 + 一个 Stat 面板 + 一个 alert rule。
3. **一天做生产化**：把 sqlite 换成 mysql、接入公司 SSO、用 Provisioning 文件管理 datasource / dashboard，提交到一个 Git 仓库。
4. **一周扩展**：把 Loki / Tempo / Mimir / Pyroscope 各起一个，数据采集换成 Alloy，跑通"指标 + 日志 + 追踪 + profile"全链路。
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

**总结**：判断要不要用 Grafana，只需要回答三个问题——你的数据在哪个后端（Prometheus / Mimir / Loki / Tempo / Pyroscope / 其它）、你的团队需要哪一档（OSS / Enterprise / Cloud）、你需要的是长期巡检的 dashboard 还是事件响应的 Explore。数据源、面板、告警、探索、Provisioning 五块的边界理清之后，剩下的都是配置工作。
