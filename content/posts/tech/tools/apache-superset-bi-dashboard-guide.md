---
title: "Apache Superset：从入门到精通 开源企业级BI与数据可视化平台"
date: "2026-03-31T01:00:00+08:00"
slug: apache-superset-bi-dashboard-guide
github_repo: "apache/superset"
source_key: "gh:apache/superset"
aliases:
  - /posts/tech/apache-superset-bi-dashboard-guide/
categories: ["技术笔记"]
tags: ["Python"]
description: "Apache Superset 是 Apache 软件基金会的顶级开源 BI 平台，64.5k Stars。本文从入门到精通，涵盖 47+ 图表类型、SQL Lab、权限管理、生产部署和自定义插件开发。"
---

# Apache Superset：使用指南 — 开源企业级 BI 与数据可视化平台

**目标读者**：数据分析师、BI 开发工程师、数据工程师、前端开发者。
**前置知识**：了解 SQL 与数据可视化概念；有 Python 或 JavaScript 基础更佳。
**体量与节奏**：入门约 2-3 小时，精通约 8-12 小时。

读完本文，你会掌握 Apache Superset 的定位与架构、三种常见的安装方式、数据库连接与虚拟数据集、47+ 图表与仪表板构建、基于角色的权限控制、生产部署，以及自定义可视化插件的开发路径。每节都给出可照做的命令或配置，动手卡住时在对应小节就能找到答案。

---

## 一、项目概述

### 1.1 它是什么

Apache Superset（[apache/superset](https://github.com/apache/superset)）是 Apache 软件基金会的顶级开源项目，一款企业级的 BI 与数据可视化平台。它起源于 Airbnb 内部工具，后捐赠给 Apache，如今由社区维护。

它想解决的是数据团队普遍面对的问题：业务要看数，但每次都写 SQL、查结果、再导进 Excel 拼图表太慢。Superset 把"连接数据源 → 写查询 → 做图表 → 拼仪表板 → 分享给同事"这条链路收进一个界面，多数场景不需要写代码。

```mermaid
graph TB
    A["数据源"] --> B["Superset"]
    B --> C["SQL Lab"]
    B --> D["可视化图表"]
    B --> E["仪表板"]

    C --> D
    D --> E

    F["用户"] --> E
    G["数据分析师"] --> C
    H["管理层"] --> E
```

### 1.2 项目数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | **64.5k** |
| GitHub Forks | **23.9k** |
| 许可证 | Apache-2.0 |
| 主要语言 | Python 77.0%，TypeScript 16.3% |
| 社区 | Twitter、Netflix、Zalando 等 200+ 企业贡献 |

> 以上 star、fork 与语言占比为撰写时点数据，具体以 [apache/superset](https://github.com/apache/superset) 仓库当前页面为准。

### 1.3 核心能力

| 能力 | 说明 |
|------|------|
| 47+ 图表类型 | 折线、柱状、饼图、地图、热力图、桑基图等 |
| SQL Lab | 内置 SQL 工作台，支持结果导出与保存为数据集 |
| 无代码可视化 | 拖拽式构建图表与仪表板 |
| 多级缓存 | 提升重复查询与仪表板加载速度 |
| 细粒度权限 | 基于角色的访问控制，可细化到数据集与数据表 |
| 插件系统 | 支持开发自定义可视化插件 |
| 多种认证 | OAuth、LDAP、DB 等后端 |
| 嵌入式 | Embedded Analytics SDK 可将图表嵌入第三方应用 |

### 1.4 适用场景

- 运营仪表板：实时盯业务指标
- 管理驾驶舱：给高管看核心经营数据
- 自助分析：分析师自己探索数据，不依赖开发排期
- 嵌入式 BI：把图表嵌进已有的 SaaS 产品
- 周期性报表：定时生成并分发

### 1.5 与同类工具的取舍

| 工具 | 图表数 | SQL 支持 | 权限模型 | 嵌入能力 | 学习曲线 |
|------|--------|----------|-----------|-----------|-----------|
| Superset | 47+ | 强 | 细粒度 | SDK | 中等 |
| Metabase | 15+ | 弱 | 简单 | API | 低 |
| Grafana | 30+ | 弱 | 中等 | API | 低 |
| Tableau | 50+ | 弱 | 强 | 强 | 高 |
| Power BI | 100+ | 中等 | 强 | 强 | 高 |

选择建议：团队重视 SQL 自由度与开源可控，选 Superset；需要更轻量、人人能上手的问答式分析，Metabase 更容易；对监控告警而非 BI 报告，Grafana 更对路。

---

## 二、快速开始：30 分钟跑起来

### 2.1 安装方式对比

| 安装方式 | 适用场景 | 难度 |
|----------|-----------|------|
| Docker | 快速体验、开发 | 低 |
| pip | 单机生产 | 中 |
| Kubernetes | 生产集群 | 高 |
| 源码 | 二次开发、贡献代码 | 高 |

### 2.2 Docker 安装（推荐）

先用仓库自带的 docker-compose 起一个完整环境：

```bash
git clone https://github.com/apache/superset.git
cd superset

docker-compose up -d

# 访问 http://localhost:8088
```

首次启动后需初始化数据库并创建管理员：

```bash
docker-compose exec superset superset db upgrade
docker-compose exec superset superset fab create-admin \
  --username admin --firstname Admin --lastname User --email admin@example.com \
  --password admin
docker-compose exec superset superset init
docker-compose restart superset
```

只想临时体验，也可以用官方镜像单容器拉起：

```bash
docker pull apache/superset:latest

docker run -d -p 8088:8088 \
  -e "SUPERSET_SECRET_KEY=your-secret-key" \
  --name superset \
  apache/superset
```

单容器模式同样要先执行 `superset db upgrade`、`superset fab create-admin`、`superset init` 这三步，账号才能生效。

### 2.3 pip 安装

```bash
python3 -m venv superset-env
source superset-env/bin/activate

pip install apache-superset

superset db upgrade

export FLASK_APP=superset
superset fab create-admin
superset init          # 初始化自带角色与默认权限

# 可选：加载示例数据，方便看效果
superset load_examples

superset run -p 8088 --with-threads --reload --debugger
```

### 2.4 首次配置

1. 打开 http://localhost:8088
2. 用上一步创建的管理员账号登录
3. 连接数据库：`Settings → Database Connections`
4. 建数据集：`+` → `Dataset`
5. 做图表：`+` → `Chart`
6. 拼仪表板：`+` → `Dashboard`

---

## 三、核心概念

### 3.1 数据模型层次

Superset 的数据模型从数据库一路向下到字段：

```mermaid
graph TB
    A["Database 数据库"] --> B["Schema 模式"]
    B --> C["Table 数据表"]
    C --> D["Column 列"]
    C --> E["Metric 指标"]

    D --> F["Dimension 维度"]
    E --> G["Measure 度量"]
```

| 概念 | 说明 |
|------|------|
| Database | 数据库连接，如 MySQL、PostgreSQL、BigQuery |
| Schema | 数据库内的模式 / 命名空间 |
| Table | 数据表，包含列与指标 |
| Column | 表的列，可作维度或指标 |
| Metric | 聚合计算，如 COUNT、SUM、AVG |
| Virtual Dataset | 基于 SQL 查询生成的虚拟数据集 |

为什么先要有虚拟数据集这一层：对复杂业务，直接在图表里拖原始表会写很长很碎的查询。先在虚拟数据集里把口径定义好，后面每张图都复用同一个口径，避免"A 图口径 A、B 图口径 B"的矛盾。

### 3.2 SQL Lab

SQL Lab 是 Superset 的核心工作台，也是它相对轻量 BI 工具的差异化所在——可以跑完整 SQL，而不是只做拖拽。

```sql
SELECT
    d.department,
    DATE_TRUNC('month', o.order_date) AS month,
    COUNT(DISTINCT c.customer_id) AS customers,
    SUM(o.amount) AS revenue,
    AVG(o.amount) AS avg_order_value
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN departments d ON c.dept_id = d.id
WHERE o.order_date >= '2025-01-01'
GROUP BY d.department, DATE_TRUNC('month', o.order_date)
ORDER BY month DESC
```

常用能力：自动补全、语法高亮、查询历史、把查询结果保存为数据集、导出 CSV / Excel。长查询建议开异步执行，避免浏览器停在等待。

### 3.3 权限模型

Superset 用 Flask-AppBuilder 的基于角色的访问控制（RBAC）。核心角色：

| 角色 | 权限 |
|------|------|
| Admin | 全部权限，包括安全配置 |
| Alpha | 可创建与编辑数据集、图表、仪表板，访问全部数据 |
| Gamma | 只读，只能访问被授权的数据 |
| sql_lab | 能否使用 SQL Lab 的开关，通常与 Gamma / Alpha 组合 |

按职责组合角色是常见做法：给分析师 `Alpha + sql_lab`，给只看报表的同事只配 `Gamma`。`sql_lab` 并不是一个独立账号层级，而是附加在角色上的权限，需要单独勾选。

要限定用户只能访问某些 schema，通过自定义安全管理器实现：

```python
# superset_config.py
from superset.security.manager import SupersetSecurityManager

class CustomSecurityManager(SupersetSecurityManager):
    def get_schemas_accessible_by_user(self, user, database):
        # 返回该用户可访问的 schema 列表
        return ['public', 'analytics']
```

---

## 四、可视化图表

### 4.1 图表分类

Superset 支持 47+ 图表类型，主要分三类。

基础图表：

| 图表类型 | 适用场景 |
|-----------|-----------|
| 折线图（Line Chart） | 趋势分析、时间序列 |
| 柱状图（Bar Chart） | 分类对比 |
| 堆叠柱状图（Stacked Bar） | 占比与构成 |
| 饼图（Pie Chart） | 比例展示 |
| 面积图（Area Chart） | 累积趋势 |
| 散点图（Scatter Plot） | 变量关联 |

高级图表：

| 图表类型 | 适用场景 |
|-----------|-----------|
| 热力图（Heatmap） | 矩阵数据、相关性 |
| 桑基图（Sankey Diagram） | 流量 / 流向分析 |
| 旭日图（Sunburst） | 层级占比 |
| 平行坐标图（Parallel Coordinates） | 多维数据对比 |
| 地图（Map） | 地理分布 |
| 日历热力图（Calendar Heatmap） | 按日期密集查看 |
| 关系图（Graph） | 网络关系 |

专用图表：

| 图表类型 | 适用场景 |
|-----------|-----------|
| 透视表（Pivot Table） | 多维交叉汇总 |
| 时间线（Timeline） | 事件序列 |
| Word Cloud | 文本词频 |
| Gauge | 单个 KPI 完成度 |
| Funnel | 转化漏斗 |

### 4.2 创建一个图表

创建入口：`+` → `Chart` → 选数据库与数据表 → `Create Chart`。

以"各部门每月营收"为例，在配置面板里填：

```
X轴（时间）: order_date
Y轴（指标）: SUM(revenue)
Group by: department
图表类型: Line Chart
```

图表的数据配置本质上是一段"取数说明"。想精确控制时，可以直接在高级选项里给出编码（Vega-Lite 语法），例如：

```json
{
  "encoding": {
    "x": {
      "field": "order_date",
      "type": "temporal",
      "axis": { "format": "%Y-%m" }
    },
    "y": {
      "field": "revenue",
      "type": "quantitative",
      "aggregate": "sum"
    }
  },
  "mark": { "type": "line", "color": "#1DA1F2", "strokeWidth": 2 }
}
```

---

## 五、仪表板构建

### 5.1 结构

仪表板由若干个 Tab 组成，每个 Tab 放若干图表，图表之间用过滤器联动。

```mermaid
graph TB
    A["Dashboard 仪表板"]
    A --> B["Tab 1: 概览"]
    A --> C["Tab 2: 销售"]
    A --> D["Tab 3: 用户"]

    B --> B1["Chart 1"]
    B --> B2["Chart 2"]
    B --> B3["Filter: 日期范围"]

    C --> C1["Chart 3"]
    C --> C2["Chart 4"]

    D --> D1["Chart 5"]
    D --> D2["Chart 6"]
```

### 5.2 过滤器

| 过滤器类型 | 说明 |
|-----------|------|
| Time Range | 日期范围 |
| Select | 单选 / 多选 |
| Date Time | 日期时间选择 |
| Numeric Range | 数值范围 |
| Freeform | 自由输入 |

一个日期过滤器示例：

```
Filter Name: order_date
Dataset: orders
Filter Type: Time Range
Default Value: Last 30 days
Time Column: order_date
```

同一个过滤器挂到多个图表上，切换时间范围时这些图表一起刷新，这是仪表板"概览体验"的关键。

### 5.3 缓存策略

缓存把 DB 查过一次的结果存起来，降低重复查询压力。Superset 的缓存分为几层：数据表缓存、图表缓存、SQL Lab 查询缓存。通过 `superset_config.py` 统一配置：

```python
CACHE_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_HOST': 'localhost',
    'CACHE_REDIS_PORT': 6379,
    'CACHE_DEFAULT_TIMEOUT': 300,   # 5 分钟
    'CACHE_KEY_PREFIX': 'superset_',
}

VIZ_CACHE_TIMEOUT = 300   # 图表缓存
SQL_CACHE_TIMEOUT = 300   # 查询缓存
```

缓存时间要按数据变化频率权衡：数据每秒在变的指标，缓存 5 分钟会给错误信号；每天凌晨更新的报表，缓存到中午都合理。

---

## 六、数据库连接

### 6.1 支持的数据库

Superset 通过 SQLAlchemy 方言连接各类数据库，原生支持 60+ 数据源：

| 数据库 | 连接字符串示例 |
|--------|---------------|
| PostgreSQL | `postgresql://user:pass@localhost:5432/db` |
| MySQL | `mysql://user:pass@localhost:3306/db` |
| BigQuery | `bigquery://project/dataset` |
| Snowflake | `snowflake://user:pass@account/db` |
| Redshift | `redshift+psycopg2://user:pass@host:5439/db` |
| Presto | `presto://localhost:8080/catalog/schema` |
| Trino | `trino://localhost:8080/catalog/schema` |
| DuckDB | `duckdb:///path/to/db` |
| SQLite | `sqlite:///path/to/db` |

### 6.2 连接示例

PostgreSQL：

```bash
pip install psycopg2-binary
# Database: postgresql://username:password@host:5432/dbname
```

BigQuery：安装驱动并指向服务账号 JSON，再把证书路径放进环境变量。

```bash
pip install pybigquery
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
# SQLAlchemy URI: bigquery://project-id/dataset
```

### 6.3 虚拟数据集

虚拟数据集就是一个保存下来的 SQL，作为图表的数据来源：

```sql
SELECT
    u.id AS user_id,
    u.name AS user_name,
    COUNT(o.id) AS order_count,
    SUM(o.amount) AS total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.created_at >= '2025-01-01'
GROUP BY u.id, u.name
```

---

## 七、安全与认证

### 7.1 认证方式

| 认证方式 | 说明 |
|---------|------|
| Database | Superset 内置的用户名 / 密码 |
| OAuth | Google、GitHub、Okta 等提供商 |
| LDAP | 对接企业目录服务 |
| REMOTE_USER | 由反向代理提供 SSO 身份 |

### 7.2 配置 OAuth

以 Google 为例，在 `superset_config.py` 里启用 OAuth 并提供提供商配置：

```python
from flask_appbuilder.security.manager import AUTH_OAUTH

AUTH_TYPE = AUTH_OAUTH

OAUTH_PROVIDERS = [
    {
        'name': 'google',
        'icon': 'fa-google',
        'token_key': 'access_token',
        'remote_app': {
            'client_id': 'YOUR_CLIENT_ID',
            'client_secret': 'YOUR_CLIENT_SECRET',
            'server_metadata_url': 'https://accounts.google.com/.well-known/openid-configuration',
            'client_kwargs': {'scope': ['openid', 'email', 'profile']},
        },
    }
]
```

### 7.3 数据权限

按角色分好权限后，还需要限定"哪些用户能看哪些行 / 哪些 schema"：

- schema 级访问：在自定义安全管理器里重写 `get_schemas_accessible_by_user`。
- 行级权限：在 `Security → Row Level Security` 里为角色定义行过滤规则，让不同角色看到同一张表的不同子集。

数据权限的正确姿势是先按角色放开"能看什么表"，再用行级规则做"能看哪些行"，两层叠加才会既不越权又不会误伤。

---

## 八、生产部署

### 8.1 单机 + 依赖服务

生产环境建议把元数据库换成 PostgreSQL，并引入 Redis 做缓存与消息队列：

```yaml
services:
  superset:
    image: apache/superset:latest
    ports:
      - "8088:8088"
    environment:
      SUPERSET_SECRET_KEY: ${SECRET_KEY}
      DATABASE_URL: postgresql://user:pass@db:5432/superset
    depends_on:
      - db
      - redis
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: superset
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
  redis:
    image: redis:7-alpine
```

### 8.2 Kubernetes 部署

Apache 官方发布了 Helm Chart，适合集群部署：

```bash
helm repo add superset https://apache.github.io/superset
helm install superset superset/superset \
  --set secretKey=${SECRET_KEY} \
  --set databaseUrl=${DATABASE_URL}
```

### 8.3 性能与异步

让 sudo 界面和查询结果分享体验更稳的关键是把重型查询交给异步 worker，而不是阻塞在 Web 进程里：

```python
# superset_config.py
CELERY_CONFIG = {
    'broker_url': 'redis://redis:6379/0',
    'result_backend': 'redis://redis:6379/1',
}

SUPERSET_WORKERS = 4

SQLLAB_ASYNC_TIME_LIMIT_SEC = 300   # SQL Lab 异步查询超时
VIZ_CACHE_MAXAGE = 3600             # 图表缓存上限，1 小时
```

---

## 九、自定义可视化插件

当内置图表满足不了业务时，可以开发插件。插件是独立的前端包，用 @superset-ui 开发。

### 9.1 目录结构

```
my-custom-viz/
├── package.json
├── src/
│   ├── plugin/
│   │   ├── index.ts
│   │   ├── controlPanel.ts
│   │   └── transformProps.ts
│   └── images/
│       └── thumbnail.png
└── tsconfig.json
```

### 9.2 插件入口

```typescript
// src/plugin/index.ts
import { ChartPlugin } from '@superset-ui/core';
import ControlPanel from './controlPanel';
import transformProps from './transformProps';

export default class CustomVizPlugin extends ChartPlugin {
  constructor() {
    super({
      loadChart: () => import('./CustomChart'),
      controlPanel: ControlPanel,
      transformProps,
      metadata: {
        name: 'Custom Chart',
        description: 'A custom visualization',
        credits: ['My Company'],
      },
    });
  }
}
```

### 9.3 注册

把插件注册进 Superset 前端入口：

```javascript
// superset-frontend/src/preamble.ts
import { configure } from '@superset-ui/core';
import CustomVizPlugin from './src/plugins/CustomViz';

configure([new CustomVizPlugin().configure()]);
```

---

## 十、推荐做法

### 10.1 仪表板设计

- 一张图只回答一个问题，不要挤多信息
- 颜色、口径全站统一
- 最重要的指标放左上角，按重要性从左上向右下排
- 用过滤器应对'想换个维度看'的需求，而不是再做一张图
- 单个仪表板不要堆太多图表，加载速度会拖垮体验

### 10.2 性能

- 复杂聚合用物化视图预计算
- 汇总表 + 明细表分层，避免每次都全量扫明细
- 合理设置缓存时间
- 必要查询加索引
- 对分析频繁的宽表，用扁平模型降低 join 成本

### 10.3 安全

- 对外访问一律 HTTPS
- 定期升级版本，跟进漏洞修复
- 最小权限：谁的只读，谁的开 sql_lab，别一刀切 Admin
- 开启审计日志，重大操作可追溯
- 敏感字段做脱敏或不下数据集

---

## 十一、常见问题

**Q1：数据量大时怎么办？**

先聚合减少返回量，再配置查询超时兜底，复杂指标用物化视图，实在撑不住再考虑换 ClickHouse 等 OLAP 引擎。SQL Lab 的长查询务必开异步执行。

**Q2：怎么实现只让销售看销售自己的数据？**

用行级权限（Row Level Security），为对应角色定义过滤条件。想在 SQL Lab 里更精细地取当前用户，也可以拿到用户上下文后拼接过滤；但首选还是 RLS，规则集中、好维护：

```sql
SELECT *
FROM orders
WHERE region IN (SELECT region FROM user_region WHERE user_id = {{ current_user_id() }})
```

**Q3：怎么把图表嵌到自己的应用里？**

用 Embedded Analytics SDK。Superset 为指定仪表板签发 guest token，你在前端加载 SDK 并挂载图表：

```javascript
import { SupersetEmbedding } from '@superset-ui/embedded-sdk';

SupersetEmbedding({
  id: 'your-chart-id',
  supersetUrl: 'https://superset.example.com',
  guestToken: 'your-guest-token',
  mountPoint: document.getElementById('chart'),
});
```

**Q4：怎么备份？**

元数据都在元数据库里，导出即可；配置单独备份：

```bash
pg_dump -U user -h host superset > superset_backup.sql
cp superset_config.py /path/to/backup/
```

---

## 十二、收尾

Superset 的价值在于把 SQL 的自由度和 BI 的易用性放进一个开源系统里：分析师照写 SQL，管理层看仪表板，IT 只用维护一套平台，没有许可费用。

接下来可以按这条路继续：

- 用 Docker 把环境跑起来，导入示例数据熟悉界面
- 连上自己的业务库，从一张图和一张仪表板开始
- 把关键查询沉淀成虚拟数据集，统一口径
- 稳定后按第八章部署到生产，并配好缓存与异步 worker

**文档信息**

- 难度：进阶
- 类型：完整教程
- 更新日期：2026-03-31
- 预计学习时间：2-3 小时入门，8-12 小时精通
- GitHub：https://github.com/apache/superset

由钳岳星君撰写 | 项目源码：https://github.com/apache/superset