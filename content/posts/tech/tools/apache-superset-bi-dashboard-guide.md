---
title: "Apache Superset：从入门到精通 开源企业级BI与数据可视化平台"
date: "2026-03-31T01:00:00+08:00"
lastmod: 2026-10-01T00:00:00+08:00
slug: apache-superset-bi-dashboard-guide
github_repo: "apache/superset"
source_key: "gh:apache/superset"
aliases:
  - /posts/tech/apache-superset-bi-dashboard-guide/
categories: ["技术笔记"]
tags: ["Python"]
description: "Apache Superset 是 Apache 软件基金会的顶级开源 BI 平台，75k Stars。本文从入门到精通，涵盖 40+ 可视化类型、SQL Lab、权限管理、生产部署和扩展开发。"
---

# Apache Superset：使用指南 — 开源企业级 BI 与数据可视化平台

**目标读者**：数据分析师、BI 开发工程师、数据工程师、前端开发者。
**前置知识**：了解 SQL 与数据可视化概念；有 Python 或 JavaScript 基础更佳。
**体量与节奏**：入门约 2-3 小时，进阶约 8-12 小时。

读完本文，你会掌握 Apache Superset 的定位与架构、官方推荐的安装方式、数据库连接与虚拟数据集、图表与仪表板构建、基于角色的权限控制、生产部署，以及扩展开发的路径。每节都给出可照做的命令或配置，动手卡住时在对应小节就能找到答案。

本文基于撰写时的最新稳定版 Superset 6.1.0（2026 年 5 月发布），关键命令与配置均对照过官方文档与仓库源码。

---

## 一、项目概述

### 1.1 它是什么

Apache Superset（[apache/superset](https://github.com/apache/superset)）是 Apache 软件基金会的顶级开源项目，一款企业级的 BI 与数据可视化平台。它起源于 Airbnb 的内部工具，2017 年进入 Apache 孵化器，2019 年毕业成为顶级项目，现在由社区维护。

它要解决的是数据团队的日常摩擦：业务要看数，但每次都写 SQL、查结果、导进 Excel 拼图表，动作重复且口径容易散架。Superset 把"连接数据源 → 写查询 → 做图表 → 拼仪表板 → 分享给同事"这条链路收进一个界面，多数场景不写代码。

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
| GitHub Stars | **75.0k** |
| GitHub Forks | **18.4k** |
| 许可证 | Apache-2.0 |
| 主要语言 | Python 约 53%，TypeScript 约 43%（按仓库代码字节数） |
| 当前稳定版 | 6.1.0（2026-05-13 发布） |

> 数据为 2026-10-01 从 GitHub API 读取的时点值，使用组织和贡献者名单见仓库 [In the Wild](https://superset.apache.org/inTheWild) 页面与 [contributors](https://github.com/apache/superset/graphs/contributors) 列表。

### 1.3 核心能力

| 能力 | 说明 |
|------|------|
| 40+ 预装可视化 | 官方预装 40 多种图表类型，覆盖折线、柱状、地图、透视表等（见 §4.1） |
| SQL Lab | 内置 SQL 工作台，支持异步执行、结果导出、保存为数据集 |
| 轻量语义层 | 在数据集上定义自定义维度与指标，图表复用同一口径 |
| 无代码构建 | 拖拽式构建图表与仪表板 |
| 缓存层 | 可配置的缓存，减轻数据库重复查询压力 |
| 细粒度权限 | 基于角色的访问控制，可细化到数据集、schema 与行 |
| 多种认证 | 数据库账号、OAuth、LDAP 等后端 |
| 定时报表 | Alerts & Reports 按计划截图或发邮件（需开启功能开关，见 §8.3） |
| 嵌入 | Embedded SDK 可把仪表板嵌进第三方应用（见 §11 Q3） |
| REST API | 图表、仪表板、数据集等资源均有 API，可编程管理 |

渲染层用的是 Apache ECharts——Superset 团队 2021 年公开过选型文章《Why Apache Superset is Betting on Apache ECharts》，ECharts 的图表种类与交互能力是主要理由。这一点决定了它能"开出"多少图：靠 ECharts 生态，而不是自己画。

### 1.4 适用场景

- 运营仪表板：实时盯业务指标
- 管理驾驶舱：给高管看核心经营数据
- 自助分析：分析师自己探索数据，不依赖开发排期
- 嵌入式 BI：把仪表板嵌进已有的 SaaS 产品
- 周期性报表：定时报表把仪表板截图或 CSV 发到邮箱

它不擅长的事也要说清楚：Superset 直连数据源做查询，不做数据建模、不做 ELT，也不存储业务数据。这些活在 dbt、Airflow 或数仓侧完成。

### 1.5 与同类工具的取舍

| 工具 | SQL 自由度 | 权限模型 | 嵌入 | 开源 |
|------|-----------|----------|------|------|
| Superset | 强（SQL Lab + 语义层） | 细粒度（角色 + 行级） | SDK + guest token | Apache-2.0 |
| Metabase | 弱（偏问答式） | 简单 | 收费版支持 | AGPL / 商业双许可 |
| Grafana | 弱（面向时序） | 中等 | API | AGPL |
| Tableau | 中等 | 强 | 强 | 商业 |
| Power BI | 中等 | 强 | 强 | 商业 |

各家版本迭代很快，具体图表数量与授权方式以官方页面为准。方向性的判断是：团队重视 SQL 自由度与开源可控，选 Superset；要更轻量、人人能上手的问答式分析，Metabase 更容易；监控告警场景，Grafana 更对路；预算充足且要端到端商业支持，再考虑 Tableau 与 Power BI。

---

## 二、快速开始：30 分钟跑起来

### 2.1 安装方式对比

| 安装方式 | 适用场景 | 难度 |
|----------|-----------|------|
| Docker Compose | 快速体验、开发环境 | 低 |
| pip | 单机部署 | 中 |
| Kubernetes Operator | 生产集群 | 高 |
| 源码 | 二次开发、贡献代码 | 高 |

### 2.2 Docker Compose 安装（官方推荐）

官方 quickstart 的完整流程：

```bash
git clone https://github.com/apache/superset
cd superset

# 切到最新稳定版对应的代码状态（以 Releases 页为准，撰写时为 6.1.0）
git checkout tags/6.1.0

# 用官方提供的 compose 文件启动
docker compose -f docker-compose-image-tag.yml up
```

首次启动会拉取镜像并加载示例数据，需要几分钟。初始化是自动的：`superset-init` 容器依次完成建表（db upgrade）、创建管理员、初始化角色权限（superset init）三步，不用手动执行。

全部容器就绪后，打开 http://localhost:8088，用默认账号登录：

```text
username: admin
password: admin
```

生产环境务必第一时间改掉这个默认密码。

两个注意点：

- 命令是 `docker compose`（空格，Compose V2）。旧命令 `docker-compose`（连字符）已在弃用路上，新版 compose 文件会报 env_file 格式错误。
- 官方明确说明 Docker Compose 适合沙箱和开发环境，不建议用于生产；生产走 §8 的方案。

只想要一个临时容器体验，也可以用官方镜像单容器拉起：

```bash
docker pull apache/superset:latest

docker run -d -p 8088:8088 \
  -e "SUPERSET_SECRET_KEY=your-secret-key" \
  --name superset \
  apache/superset
```

单容器没有 init 容器代劳，需要自己进容器执行 `superset db upgrade`、`superset fab create-admin`、`superset init` 三步，账号才能用。

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
| Database | 数据库连接，如 PostgreSQL、BigQuery |
| Schema | 数据库内的模式 / 命名空间 |
| Dataset | 数据集，绑到一张表或一段 SQL，图表的数据来源 |
| Column | 数据集的列，可作维度或指标 |
| Metric | 聚合计算，如 COUNT、SUM、AVG |
| Virtual Dataset | 基于 SQL 查询生成的虚拟数据集 |

为什么要有虚拟数据集这一层：复杂业务的取数逻辑写在图表里会很长很碎，而且每张图各写各的，口径迟早打架。先把 JOIN、过滤、聚合在虚拟数据集里定死，后面每张图复用同一个口径，"A 图营收 100 万、B 图营收 90 万"这类事故就从源头堵住了。

### 3.2 SQL Lab

SQL Lab 是 Superset 的工作台，也是它和轻量 BI 工具拉开差距的地方——能跑完整 SQL，而不只是拖拽。

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

常用能力：自动补全、语法高亮、查询历史、把查询结果保存为数据集、导出 CSV。跑长查询前先切到异步模式（界面上的 "Run asynchronously"），查询丢给 Celery worker 执行，浏览器不用干等，关掉页面结果也还在。

### 3.3 权限模型

Superset 用 Flask-AppBuilder 的基于角色的访问控制（RBAC）。内置的标准角色（对照仓库 `RESOURCES/STANDARD_ROLES.md`）：

| 角色 | 权限 |
|------|------|
| Admin | 全部权限，包括安全管理与用户管理 |
| Alpha | 可访问全部数据源，可添加数据源，可创建和修改自己拥有的图表与仪表板 |
| Gamma | 数据消费角色：只能查看被授权数据源上的图表与仪表板；也可以自己创建，但只能基于被授权的数据集 |
| Public | 给匿名访问用，只够看公开仪表板 |
| sql_lab | SQL Lab 的准入角色；Alpha 和 Gamma 即便有它，也要按数据库单独授权才能查询 |

典型的组合方式：给分析师 `Alpha + sql_lab`，给只看报表的同事配 `Gamma` 加上一个授权数据集的自定义角色。`sql_lab` 不是一个独立的用户层级，而是附加在角色上的权限集合。

要进一步收窄某类用户可见的 schema，可以继承 `SupersetSecurityManager` 做定制。源码里的过滤方法是：

```python
def get_schemas_accessible_by_user(
    self,
    database: "Database",
    catalog: Optional[str],
    schemas: AbstractSet[str] | list[str],
    hierarchical: bool = True,
) -> set[str]:
```

在 `superset_config.py` 里继承并覆写它，就能控制每个用户在指定数据库上能看到哪些 schema：

```python
# superset_config.py
from superset.security.manager import SupersetSecurityManager

class CustomSecurityManager(SupersetSecurityManager):
    def get_schemas_accessible_by_user(self, database, catalog, schemas, hierarchical=True):
        accessible = super().get_schemas_accessible_by_user(
            database, catalog, schemas, hierarchical
        )
        # 在原有判定之上，只保留业务允许的 schema
        return accessible & {"public", "analytics"}

# 最后让 Superset 用这个安全管理器
CUSTOM_SECURITY_MANAGER = CustomSecurityManager
```

行级的数据隔离不在这里做，走行级安全规则，见 §7.3。

---

## 四、可视化图表

### 4.1 图表分类

Superset 官方预装 40+ 可视化类型（官方口径 "40+ pre-installed visualization types"），按用途分三类。

基础图表：

| 图表类型 | 适用场景 |
|-----------|-----------|
| 折线图（Line Chart） | 趋势分析、时间序列 |
| 柱状图（Bar Chart） | 分类对比 |
| 堆叠柱状图（Stacked Bar） | 占比与构成 |
| 饼图（Pie Chart） | 比例展示 |
| 面积图（Area Chart） | 累积趋势 |
| 散点图（Scatter Plot） | 变量关联 |

进阶图表：

| 图表类型 | 适用场景 |
|-----------|-----------|
| 热力图（Heatmap） | 矩阵数据、相关性 |
| 桑基图（Sankey Diagram） | 流量 / 流向分析 |
| 旭日图（Sunburst） | 层级占比 |
| 平行坐标图（Parallel Coordinates） | 多维数据对比 |
| 地图（Map） | 地理分布 |
| 日历热力图（Calendar Heatmap） | 按日期密集查看 |
| 关系图（Graph Chart） | 网络关系 |

专用图表：

| 图表类型 | 适用场景 |
|-----------|-----------|
| 透视表（Pivot Table） | 多维交叉汇总 |
| 时间线（Timeline） | 事件序列 |
| 词云（Word Cloud） | 文本词频 |
| 仪表盘（Gauge Chart） | 单个 KPI 完成度 |
| 漏斗图（Funnel Chart） | 转化漏斗 |

### 4.2 创建一个图表

入口：`+` → `Chart` → 选数据集 → 选图表类型 → `Create Chart`，进入 Explore 视图。

以"各部门每月营收"的折线图为例，在左侧数据面板填：

```text
X-AXIS（时间轴）: order_date
METRIC（指标）:   SUM(revenue)
DIMENSION（系列）: department
```

配置好点 "Create chart" 出图，再 "Save" 保存并可以选择加进某张仪表板。

同一个图表换数据集、换聚合方式都很快，因为 Explore 的每一步改动只是改查询参数，图表即时重查。想复用一段固定的取数逻辑，别在每张图里重配，存成虚拟数据集（§6.3）再基于它建图。

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

仪表板顶部的过滤器栏（Filters）支持几类控件：

| 过滤器类型 | 说明 |
|-----------|------|
| Time Range | 日期范围 |
| Select | 单选 / 多选 |
| Date Time | 日期时间选择 |
| Numerical Range | 数值范围 |

一个日期过滤器的配置：

```text
Filter Name: order_date
Dataset: orders
Filter Type: Time Range
Default Value: Last 30 days
Time Column: order_date
```

过滤器可以设置作用范围（应用到哪些图表），一个日期过滤器挂到所有时间序列图上，切换时间范围时整页联动刷新——这是仪表板"总览"体验的来源。

### 5.3 缓存策略

Superset 用缓存把查过的查询结果存起来，重复访问不再打数据库。配置里有几个分工不同的缓存桶（对照 `superset/config.py`）：

```python
# superset_config.py

# 通用缓存（元数据类）
CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_REDIS_URL': 'redis://localhost:6379/1',
    'CACHE_DEFAULT_TIMEOUT': 300,   # 5 分钟
    'CACHE_KEY_PREFIX': 'superset_',
}

# 图表查询结果缓存
DATA_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_REDIS_URL': 'redis://localhost:6379/2',
    'CACHE_DEFAULT_TIMEOUT': 300,
}

# 过滤器状态与 Explore 表单数据缓存
FILTER_STATE_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_REDIS_URL': 'redis://localhost:6379/3',
    'CACHE_DEFAULT_TIMEOUT': 86400,
}
EXPLORE_FORM_DATA_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_REDIS_URL': 'redis://localhost:6379/4',
    'CACHE_DEFAULT_TIMEOUT': 86400,
}
```

超时时间按数据变化频率定：每秒都在变的指标，缓存 5 分钟就是错误信号；每天凌晨更新的报表，缓存一上午都合理。`DATA_CACHE_CONFIG` 里把 `CACHE_DEFAULT_TIMEOUT` 设为 0 可以对查询结果永久缓存，靠缓存失效机制更新，适合特别贵的查询。

---

## 六、数据库连接

### 6.1 支持的数据库

Superset 通过 SQLAlchemy 方言连接数据库：官方的口径是"任何会说 SQL 的数据源"，只要有对应的 Python DB-API 驱动和 SQLAlchemy 方言就能接入。官方文档的[支持列表](https://superset.apache.org/docs/databases)收录了几十种，从 PostgreSQL、MySQL 这类 OLTP 库，到 ClickHouse、Trino、Snowflake、BigQuery 这类分析型引擎都有现成驱动。

常用连接字符串示例：

| 数据库 | 连接字符串示例 |
|--------|---------------|
| PostgreSQL | `postgresql://user:pass@localhost:5432/db` |
| MySQL | `mysql://user:pass@localhost:3306/db` |
| BigQuery | `bigquery://project/dataset` |
| Snowflake | `snowflake://user:pass@account/db` |
| Redshift | `redshift+psycopg2://user:pass@host:5439/db` |
| Trino | `trino://localhost:8080/catalog/schema` |
| ClickHouse | `clickhousedb://user:pass@localhost:8123/db` |
| DuckDB | `duckdb:///path/to/db` |
| SQLite | `sqlite:///path/to/db` |

### 6.2 安装驱动与连接

PostgreSQL：

```bash
pip install psycopg2-binary
# SQLAlchemy URI: postgresql://username:password@host:5432/dbname
```

BigQuery：装驱动，把服务账号 JSON 的路径写进环境变量：

```bash
pip install sqlalchemy-bigquery
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
# SQLAlchemy URI: bigquery://project-id/dataset
```

Docker Compose 环境装驱动的姿势不一样：把包名写进 `./docker/requirements-local.txt` 再重建，容器里才会带上。

在 Superset 里填 URI 的位置是 `Settings → Database Connections → + Database`，高级参数（超时、开启异步等）在 Advanced 里配。

### 6.3 虚拟数据集

虚拟数据集就是一段保存下来的 SQL，作为图表的数据来源。入口：数据集列表页 `+ Dataset`，选库后切换到虚拟数据集方式粘贴 SQL：

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

另一条顺手的生产路径：在 SQL Lab 里把查询调通后直接点 "Save as dataset"，省去复制粘贴。

---

## 七、安全与认证

### 7.1 认证方式

| 认证方式 | 说明 |
|---------|------|
| Database | Superset 内置的用户名 / 密码 |
| OAuth / OIDC | Google、GitHub、Okta、Keycloak 等 |
| LDAP | 对接企业目录服务 |
| REMOTE_USER | 由反向代理提供身份 |

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

角色决定"能用哪些功能"，数据权限解决"能看哪些数据"。两层：

- schema 级：§3.3 的自定义安全管理器。
- 行级：Row Level Security（RLS），在设置菜单的 Row Level Security 页面为角色定义过滤规则。规则本质是追加到查询上的谓词，让不同角色看到同一张表的不同行。

RLS 的谓词里可以用 Jinja 宏取当前用户上下文（`current_username()`、`current_user_id()` 等），前提是管理员开启了 `ENABLE_TEMPLATE_PROCESSING` 功能开关。

数据权限的搭建次序：先用角色和数据集授权圈定"能碰哪些表"，再用 RLS 收细到"能看哪些行"。两层各管一段，出了问题也好定位是哪层漏了。

---

## 八、生产部署

### 8.1 单机：Compose + 外部依赖

生产环境的最小架构：元数据库换 PostgreSQL，加 Redis 做缓存和 Celery 消息队列，密钥从环境变量注入：

```yaml
services:
  superset:
    image: apache/superset:latest
    ports:
      - "8088:8088"
    environment:
      SUPERSET_SECRET_KEY: ${SECRET_KEY}
      DATABASE_URL: postgresql://user:pass@db:5432/superset
      REDIS_HOST: redis
    depends_on:
      - db
      - redis
  db:
    image: postgres:17
    environment:
      POSTGRES_DB: superset
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
  redis:
    image: redis:7
```

`SUPERSET_SECRET_KEY` 用于会话签名和敏感数据加密，必须是足够长的随机串，丢了它元数据库里的加密字段（如数据库连接密码）就解不开了，务必单独备份。

### 8.2 Kubernetes 部署

仓库里老的 Helm Chart（`helm/superset`）已被官方标记为 deprecated，新部署不要再基于它。官方现在维护的是 [Apache Superset Kubernetes Operator](https://github.com/apache/superset-kubernetes-operator)，通过 Kubernetes 自定义资源声明 Superset 实例，覆盖安装、升级、依赖配置等运维动作。已有 Helm 部署的团队按官方迁移指南逐步迁到 Operator。

### 8.3 异步任务与定时报表

重型查询不该阻塞在 Web 进程里。Superset 用 Celery 跑异步：SQL Lab 的异步查询、告警与报表的执行都交给 worker：

```python
# superset_config.py
CELERY_CONFIG = {
    'broker_url': 'redis://redis:6379/0',
    'result_backend': 'redis://redis:6379/1',
}

SQLLAB_ASYNC_TIME_LIMIT_SEC = 300   # SQL Lab 异步查询超时
```

定时报表（Alerts & Reports）按计划把仪表板截图或把图表数据发到邮件/Slack。它依赖两件事：开启 `ALERT_REPORTS` 功能开关（默认关闭），以及 worker 节点装好无头浏览器（Superset 用 Playwright 对仪表板截图）。

---

## 九、扩展开发

内置图表和功能满足不了时，有两条路。

### 9.1 扩展系统（6.x 推荐方向）

Superset 6.x 引入了新的扩展系统，思路接近 VS Code 的扩展模型：组织不改核心代码就能加功能，避免 fork 整个仓库带来的维护成本。

要点：

- 扩展是自包含的 `.supx` 包，可同时含前端（React/TypeScript）与后端（Python）组件
- 运行时通过 Webpack Module Federation 动态加载
- 扩展能做的事：自定义 UI 组件与面板、命令与菜单、`/extensions/` 命名空间下的 REST API 端点、面向 AI 智能体的 MCP 工具与 prompt
- 开发者可用的 UI 组件来自 `@apache-superset/core/components`，文档里有 Extension Compatible 标记标明可用范围

从零写一个扩展的完整流程见官方 developer-docs 的 Extensions 章节（Overview → Quick Start → Deployment）。要判断"该不该用扩展"，标准很直接：改动如果必须动 Superset 源码，就该做成扩展。

### 9.2 传统自定义图表插件

在扩展系统之前，自定义可视化的方式是写 ChartPlugin 前端插件：一个独立的前端包，包含图表元数据、控制面板（controlPanel）与数据转换逻辑（transformProps），用仓库自带的 Yeoman 生成器 `@superset-ui/generator-superset` 起项目，再打进前端构建。这条路径的官方文档已并入 developer-docs，新项目建议优先评估扩展系统；维护已有插件时，插件包在 `superset-frontend/plugins/` 下有大量官方实现可对照。

---

## 十、推荐做法

### 10.1 仪表板设计

- 一张图只回答一个问题，塞多种信息只会让读者都看不懂
- 颜色、口径全站统一；口径统一靠虚拟数据集，不靠人记
- 最重要的指标放左上角，按重要性从左上向右下排
- "想换个维度看"的需求用过滤器满足，别复制出十张相似的图
- 单张仪表板控制在十来张图以内，加载慢的仪表板没人看

### 10.2 性能

- 复杂聚合用物化视图预计算，让 Superset 查现成结果
- 汇总表 + 明细表分层，避免每张图都全量扫明细
- 按数据变化频率设置 `DATA_CACHE_CONFIG` 超时
- 高频过滤列建索引
- 大宽表用扁平模型降低 join 成本

### 10.3 安全

- 对外访问一律 HTTPS
- 定期升级版本，跟进安全公告
- 最小权限：看报表的给 Gamma，别一刀切 Admin；默认密码上线前必改
- 开启审计日志（`EVENT_LOGGER` 类配置），重大操作可追溯
- 敏感字段不进数据集，或用 RLS 挡住

---

## 十一、常见问题

**Q1：数据量大时怎么办？**

顺序是：先在虚拟数据集里聚合减少返回量；再确认长查询走异步；还不够就把重指标做成物化视图。以上都做完仍撑不住，说明该换引擎了——把分析负载迁到 ClickHouse、Trino 这类 OLAP 引擎，Superset 照样直连它们。

**Q2：怎么实现只让销售看销售自己的数据？**

用行级安全（RLS）。在 Row Level Security 页面为对应角色建规则，规则的 Clause 就是追加到查询的过滤谓词，支持 Jinja 宏（需开启 `ENABLE_TEMPLATE_PROCESSING`）：

```sql
region IN (SELECT region FROM user_region WHERE user_id = {{ current_user_id() }})
```

规则集中在一个页面管理，比在每张图里写过滤条件好维护得多。

**Q3：怎么把仪表板嵌到自己的应用里？**

用 Embedded SDK。嵌入的单位是仪表板，流程是三步：

1. 在 `superset_config.py` 开启功能开关并配置 JWT 密钥：

```python
FEATURE_FLAGS = {'EMBEDDED_SUPERSET': True}
GUEST_TOKEN_JWT_SECRET = 'a-strong-random-secret'   # 生产环境务必更换
```

2. 你的后端调 Superset REST API 为指定仪表板签发 guest token，并提供一个接口给前端拿 token。
3. 前端装 `@superset-ui/embedded-sdk` 并挂载：

```javascript
import { embedDashboard } from '@superset-ui/embedded-sdk';

embedDashboard({
  id: 'your-dashboard-id',          // 仪表板 ID，来自 Superset 嵌入入口
  supersetDomain: 'https://superset.example.com',
  mountPoint: document.getElementById('dashboard-container'),
  fetchGuestToken: () => fetchGuestTokenFromYourBackend(),
  dashboardUiConfig: { hideTitle: true },
});
```

SDK 以 iframe 方式嵌入仪表板页，guest token 决定了访问权限和有效期，你的应用用自己的认证体系，不用把 Superset 账号暴露给最终用户。

**Q4：怎么备份？**

Superset 的全部元数据（数据集、图表、仪表板、用户、RLS 规则）都在元数据库里，导出它就够了；配置文件单独备份：

```bash
pg_dump -U user -h host superset > superset_backup.sql
cp superset_config.py /path/to/backup/
```

别忘了 `SUPERSET_SECRET_KEY` 也在必须备份的清单里——没有它，元数据库里的加密字段无法解密。

---

## 十二、收尾

Superset 把 SQL 的自由度和 BI 的易用性放进了同一个开源系统：分析师写 SQL、管理层看仪表板、IT 只维护一套平台，没有许可费用。

接下来可以按这条路走：

- 用 Docker Compose 把环境跑起来，导入示例数据熟悉界面
- 连上自己的业务库，从一张图和一张仪表板开始
- 把关键查询沉淀成虚拟数据集，统一口径
- 稳定后按第八章部署到生产，配好缓存、Celery 与备份

**文档信息**

- 难度：进阶
- 类型：完整教程
- 更新日期：2026-10-01
- 基线版本：Apache Superset 6.1.0
- 预计学习时间：2-3 小时入门，8-12 小时进阶
- GitHub：https://github.com/apache/superset

由钳岳星君撰写 | 项目源码：https://github.com/apache/superset
