---
title: "Semantica：给 AI Agent 装上可审计的图谱记忆与决策溯源"
date: 2026-08-11T03:22:16+08:00
slug: "semantica-graph-native-context-infrastructure"
github_repo: "semantica-agi/semantica"
source_key: "gh:semantica-agi/semantica"
description: "Semantica 是一个图原生的上下文基础设施，为 AI Agent 提供知识图谱构建、确定性推理、决策记录与 W3C PROV-O 溯源，支持 RDF/LPG 双模存储和 Databricks/Snowflake 原生连接器，面向金融、医疗等受监管领域的合规需求。"
draft: false
categories: ["技术笔记"]
tags: ["知识图谱", "AI Agent", "决策智能", "RAG", "合规"]
---

## 核心判断

AI Agent 最大的信任问题不是"它会不会出错"，而是"出了错无法追溯"。向量数据库存的是嵌入，不是语义；LLM 上下文窗口会遗忘；传统 RAG 无法回答"为什么"。Semantica 的定位不是替代这些组件，而是在它们**下面**铺一层图原生的上下文基础设施：把企业数据提取成知识图谱，把每次 Agent 决策记录为可查询的图节点，把推理链路做到确定性可解释——不需要 LLM 参与图谱构建和推理过程。

项目自称"The Open Source Palantir for AI Agents"，这个类比指向的是同一个方向：受监管领域（金融、医疗、法律、政府）需要的不是更强的生成能力，而是**可审计的决策链路**。

## 系统地图

Semantica 是一条端到端管线，每个阶段都是可独立导入的模块：

```
数据源 → 摄取 → 解析 → 标准化 → 分块 → 抽取 → 冲突检测 → 去重
    → 知识图谱 → [ 本体 · 推理 · 溯源 · 决策 ] → 增强图谱
    → 向量库 + 多模图存储 (RDF & LPG) → 导出 / 可视化 / REST · MCP · CLI
```

### 数据摄入层

支持多源异构数据：文件、网页、数据库、企业数据平台（Databricks Unity Catalog、Snowflake）、云存储（Google Drive、Elasticsearch）、流式（Kafka、Kinesis）、Git、邮件、MCP。

Databricks 和 Snowflake 连接器值得单独提一下：它们不是简单的 JDBC 拉数，而是直接对接 Unity Catalog / Snowflake Warehouse 的目录结构（catalog/schema/table/lineage），把已有的数据治理元数据转化为图谱中的节点和溯源边。这意味着不需要把数据导出到第三方 SaaS——表结构、列级血缘关系直接在仓库内部就被图谱化了。

### 抽取与冲突检测

从文档中做 NER（命名实体识别）、关系抽取、事件抽取，生成三元组。关键设计：**冲突检测先于合并**——当两个来源对同一事实给出矛盾陈述时，Semantica 不会默默覆盖旧值，而是标记冲突并保留两条记录及各自的来源。这在合规场景中至关重要：审计师需要看到的是"这个事实有两个版本，为什么"。

### 知识图谱与智能层

图谱之上叠加四个子系统：

| 子系统 | 能力 |
|--------|------|
| **本体治理** | SHACL 约束、OWL 生成本体、SKOS 词表管理、可视化编辑器 |
| **确定性推理** | 前向链式推理、Rete 网络、Datalog、SPARQL——全程可解释路径 |
| **溯源** | W3C PROV-O 标准的来源追踪，每条事实可追溯到原始文档和抽取过程 |
| **决策智能** | 决策作为一等图节点，支持因果链追溯、相似决策检索、影响分析 |

### 存储抽象

支持 RDF 三元组库（内嵌 Oxigraph、Blazegraph、Apache Jena、Eclipse RDF4J）和标号属性图（Neo4j、FalkorDB、Apache AGE、AWS Neptune），外加向量库。所有后端可互换，不改动上层代码。这种"多模图存储"设计意味着 Semantica 不会把用户绑定在单一图数据库上。

## 决策智能：Agent 的审计层

这是 Semantica 最有辨识度的模块。在传统 Agent 架构中，决策是一次性推理——LLM 生成答案，用完即丢。Semantica 把每次决策变成一个永久图节点：

```python
from semantica.context import ContextGraph

graph = ContextGraph(advanced_analytics=True)

# 记录一次贷款审批决策
app_id = graph.record_decision(
    category="credit_application",
    scenario="Personal loan, $85k income, 31% DTI",
    reasoning="Income meets threshold; employment stable",
    outcome="proceed_to_underwriting",
    confidence=0.88,
)
uw_id = graph.record_decision(
    category="loan_underwriting",
    scenario="Underwriting review for applicant",
    reasoning="DTI within policy; clean 36-month credit history",
    outcome="approved",
    confidence=0.94,
)

# 建立因果链
graph.add_causal_relationship(app_id, uw_id, relationship_type="CAUSED")

# 事后审计
chain = graph.trace_decision_chain(uw_id)      # 完整因果祖先
similar = graph.find_similar_decisions("personal loan approval")  # 先例检索
impact = graph.analyze_decision_impact(uw_id)   # 下游影响图
```

`relationship_type` 只接受三种值：`CAUSED`、`INFLUENCED`、`PRECEDENT_FOR`。这种约束保证了因果关系的语义一致性——不是任意连边，而是有类型、有方向、可验证的关系。

决策记录可导出为 W3C PROV-O、CSV 或 JSON 格式，直接用于监管提交。

## 与传统 RAG 的差异

| 维度 | 向量库 + RAG | 纯 LLM 上下文 | Semantica |
|------|-------------|---------------|-----------|
| 召回方式 | 嵌入相似度 | Token 窗口 | 图遍历 + 语义搜索 |
| 决策历史 | 不存储 | 不存储 | 一等可查询节点 |
| 溯源 | 无 | 无 | W3C PROV-O，链接到源 |
| 推理 | 无 | 黑箱 | 前向链式 / Rete / Datalog / SPARQL |
| 冲突处理 | 静默覆盖 | 静默覆盖 | 检测、标记、保留 |
| 时间旅行 | 无 | 无 | 点对时间图快照 |
| 合规导出 | 无 | 无 | PROV-O / SHACL / OWL / RDF |
| 多 Agent 上下文 | 每个 Agent 独立 | 每个 Agent 独立 | 共享智能层 |

关键区别：Semantica 不替代 LLM 或向量库，而是在它们之上添加图谱、推理、溯源和审计层。现有的 Agent 框架、LLM 和向量库保持不变，Semantica 补充的是"为什么"和"从哪来"。

## 安装与快速开始

```bash
pip install semantica
```

```python
from semantica.context import ContextGraph

graph = ContextGraph(advanced_analytics=True)

# 添加节点
graph.add_node("acme_corp", "Organization", name="Acme Corp", industry="SaaS")
graph.add_node("alice", "Person", name="Alice Chen", role="CTO")

# 添加有类型的边
graph.add_edge("alice", "acme_corp", edge_type="works_for", since="2019-03-01")

# 记录决策
decision_id = graph.record_decision(
    category="vendor_selection",
    scenario="Choose cloud provider for HIPAA workload",
    reasoning="AWS offers BAA and mature HIPAA tooling",
    outcome="selected_aws",
    confidence=0.93,
)
```

验证安装：

```bash
semantica doctor
# Python 3.11.9       pass
# semantica 0.6.0     pass
# faiss vector store  pass
# Config file         pass
```

当前版本 v0.6.0（2026-07-21 发布），3.9K Stars，Python 为主语言，MIT 协议。

## 适用边界

**适合**：

- 受监管行业（金融、医疗、法律、政府）需要可审计 AI 决策链路的场景
- 多源异构数据需要统一成知识图谱的企业数据平台团队
- 使用 Databricks 或 Snowflake 且希望在仓库内部完成图谱化的团队
- 需要确定性推理（非 LLM 推理）辅助决策的场景
- 多 Agent 共享上下文层的需求

**不适合**：

- 轻量级 RAG 需求（向量库 + LLM 足够，不需要图谱和溯源）
- 对确定性推理无需求的通用聊天机器人
- 不想维护图数据库基础设施的团队
- 数据量不足以构建有意义知识图谱的小型项目
- 需要 LLM 驱动的开放式知识发现（Semantica 的推理引擎是确定性的，不做生成式发现）
