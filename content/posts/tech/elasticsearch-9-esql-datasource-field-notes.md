---
title: "Elasticsearch 9.x：老牌搜索引擎的 AI 时代改造现场"
date: 2026-09-29T03:30:00+08:00
slug: "elasticsearch-9-esql-datasource-field-notes"
github_repo: "elastic/elasticsearch"
source_key: "gh:elastic/elasticsearch"
description: "Elasticsearch 是老牌分布式搜索与分析引擎，9.x 版本正在向向量检索与 RAG 场景纵深演进。本文基于 2026 年 9 月的 master 分支提交证据，观察 ES|QL 数据源扩展与工作流可查询化两条改造主线，梳理版本节奏与升级观察点。"
draft: false
categories: ["技术笔记"]
tags: ["Elasticsearch", "搜索", "ES|QL", "向量检索"]
---

# Elasticsearch 9.x：老牌搜索引擎的 AI 时代改造现场

## 核心判断

Elasticsearch 的自我定位已经写进 README 第一句：**分布式搜索与分析引擎、可扩展数据存储、为生产规模负载的速度与相关性优化的向量数据库**（vector database）。三个身份并列，最后一个是新加的筹码——RAG（检索增强生成）、向量搜索（vector search）、全文检索、日志、APM 都被列为一级用例。

但对一个 2010 年立项、7.8 万 Star 的老项目，比定位更重要的是**改造在哪儿发生**。从 2026 年 9 月的 master 分支提交看，两条主线最活跃：ES|QL 的外部数据源能力（ES|QL|DS 系列），以及"工作流执行结果作为可查询数据"（#156669）。这两条线共同指向一个方向：让搜索引擎变成统一查询层。本文拆这两条主线，并给出版本节奏与升级观察点。

## 仓库速览（2026-09-28 取证）

| 项目 | 数据 |
|------|------|
| 仓库 | elastic/elasticsearch |
| 描述 | Free and Open Source, Distributed, RESTful Search Engine |
| Stars / Forks | 78,040 / 26,094 |
| 主语言 | Java |
| License | Other（非标准 OSI 许可，AGPL/SSPL/Elastic License 多许可可选） |
| 最新稳定版 | 9.5.4（2026-09-15 发布） |
| 同期维护线 | 8.19.22（2026-09-23 发布） |
| 最近提交 | 2026-09-28（当天多次合入） |

两点先划出来：**8.x 维护线仍在发补丁**（8.19.22 比 9.5.4 还晚八天发布），且 master 当天有活跃合入——老项目的双线甚至三线维护是常态，选版本线时要看清自己吃到的是哪个通道。

## 主线一：ES|QL 接外部数据源（ES|QL|DS）

ES|QL（Elasticsearch Query Language）是 8.x 时代引入的管道式查询语言，用来替代部分 DSL 场景。9 月的提交记录里，`ES|QL|DS` 前缀密集出现，几乎构成一个独立子项目：

- 数据源注册的行为声明（"A declaration for external-datasource behaviour, demonstrated on dataset registration"）
- 数据源注册密钥不进审计日志（"Keep dataset registration secrets out of the audit log"）
- 数据源失败状态保留（"Preserve ES|QL datasource failure status"）
- 解析期数据源警告（"Deliver resolve-time datasource warnings"）
- `_test` 数据源藏在 feature flag 后（"Gate datasource `_test` behind a feature flag"）

把这几条合起来读，能看出工程上的谨慎程度：

1. **外部数据源是方向**。ES|QL 想查的不只是本集群索引，还有注册进来的外部数据集。
2. **安全先行**。密钥不落审计日志这类提交出现在能力铺开之前，而不是事故之后。
3. **灰度控制**。`_test` 数据源挂 feature flag，说明整套能力还在特性开关后面逐步放量。

对使用者的含义：短期内这不是"马上能用在生产的能力"，但值得跟踪——一旦稳定，ES 会从"存什么查什么"走向"注册什么查什么"，数据集成方式会变。

## 主线二：工作流执行结果可查询化

PR #156669 的标题是 "Workflow executions as queryable data: ES side"。把工作流（workflow）的每次执行落成可查询数据，意味着 ES 不只存储业务索引，也开始承接"系统自身行为"的观测面。结合 Elasticsearch 在日志、APM 领域的既有地位，这条线可以理解为把可观测性的数据模型再往下挖一层：不仅记录事件，还记录流程。

同日的修复类提交（如 #160152 "Fix query phase losing a listener in remote reduction rejection"，查询阶段在远程归约被拒时丢失监听器）则提示：分布式查询的边界路径仍是日常修 bug 的主战场——这正是一个 16 年项目的真实体感。

## 系统地图

```
Elasticsearch 9.x
├── 查询层
│   ├── DSL（既有 JSON 查询语言）
│   └── ES|QL ──► ES|QL|DS（外部数据源，feature flag 后）
│        └── 数据集注册 / 密钥治理 / 失败状态 / 警告
├── 存储层
│   ├── 全文索引（Lucene）
│   └── 向量索引（vector search / RAG 用例）
└── 观测层
    ├── 日志 / 指标 / APM（既有）
    └── 工作流执行数据（#156669，进行中）
```

三条线各回答一个问题：查询层回答"怎么查得更远"（跨数据源），存储层回答"怎么存得更多样"（向量），观测层回答"怎么连自己的行为一起看"。

## 采用建议

- **版本线选择**：新部署直接上 9.x（当前 9.5.4）；存量 8.x 不必恐慌迁移，8.19 维护线仍在发补丁，按 Elastic 官方 EOL 时间表规划即可。官方 release notes 在 elastic.co/docs/release-notes/elasticsearch，比仓库 tag 说明更详细。
- **license 注意**：仓库标注非标准许可。自托管选部署方式、云上托管选服务商时，先确认 AGPL / SSPL / Elastic License 哪一份适用于你的场景——这是这个项目与 MIT 类项目最大的差异点。
- **跟踪 ES|QL|DS 的正确姿势**：订阅 release notes 中 ES|QL 章节，关注 feature flag 何时默认打开；在非生产集群上先试数据集注册流程。
- **AI 检索场景**：README 把 RAG 与向量搜索放在用例前两位，配合 Search Labs（elastic.co/search-labs）的示例入手比直接啃源码划算。
- **本文不覆盖**：ES|QL 语法教学、集群容量规划、与 OpenSearch 的分家史及横向对比。

## 证据边界

文中版本号、时间戳、PR 编号均取自 GitHub 仓库 release 与 commit 记录（取证时间 2026-09-28/29）。ES|QL|DS 与工作流可查询化均处于开发进行中，feature flag、行为细节在正式发布前可能调整；具体能力以各版本官方 release notes 为准，本文未做独立功能验证。
