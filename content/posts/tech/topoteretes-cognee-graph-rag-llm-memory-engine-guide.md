---
title: "cognee：把知识图谱塞进 LLM 长期记忆的开源引擎怎么工作"
date: "2026-06-28T21:14:10+08:00"
slug: "topoteretes-cognee-graph-rag-llm-memory-engine-guide"
description: "cognee 是面向 AI Agent 的开源长期记忆引擎，把知识图谱作为召回主干而非纯向量检索；本文拆解其存储层、Pipeline、17 个 SearchType 与多源 Recall 路由机制，并结合 BEAM benchmark 解读 GraphRAG 的真实工程边界。"
draft: false
categories: ["技术笔记"]
tags: ["cognee", "GraphRAG", "LLM记忆", "知识图谱", "RAG"]
---

# cognee：把知识图谱塞进 LLM 长期记忆的开源引擎怎么工作

`cognee` 这个仓库真正解决的不是「让 LLM 记住对话」，而是**让 Agent 拥有一个可独立部署、可换数据库、可改 Schema 的长期记忆层**。24k+ Star、Apache-2.0、Python 1.2.2（2026-06-26 发布），它把传统 RAG 的「向量检索 → 文档片段」改写成「图谱实体 + 关系 + 嵌入」三元召回，并对外同时暴露 `add/cognify/search`（V1 任务流水线 API）与 `remember/recall/improve/forget`（V2 记忆语义 API）。理解它要先拆清它里面其实并行着三套互相独立但被同一份数据编织在一起的机制：任务流水线、知识图谱本体、以及多源召回路由。

## 系统地图

cognee 把记忆层抽象成三个**可独立替换**的物理后端，但**逻辑上必须协同**。先看整体，再讲机制。

### 三层存储 + 双层 API

| 层 | 在 cognee 里的角色 | 默认后端（v1.2.x） | 可替换 |
| --- | --- | --- | --- |
| 向量库 | 实体 / 文本块的嵌入存储 | Postgres + pgvector | LanceDB、Qdrant、ChromaDB、Weaviate、Milvus、社区适配器 |
| 图数据库 | 实体关系 / 知识图谱本体 | cognee 内置 Postgres graph backend | Neo4j、Amazon Neptune |
| 会话缓存 / 元数据 | session 问答、tracing、user/dataset 元数据 | SQL（Postgres 或 SQLite） | Redis |
| LLM | 实体抽取、关系推理、Query 改写 | 任何 OpenAI 兼容接口 | Ollama、Anthropic、Bedrock、vLLM 等 |

> 一个常被忽略的事实：在 1.0 之后的版本里，**整套记忆层可以全部跑在单实例 Postgres 上**——pgvector 存嵌入，cognee 自己的 Postgres graph backend 存关系，SQL session cache 存短期问答，关系数据库存元数据。README 自述在 CI benchmark 里 Postgres-only 模式比「专用图 + 专用向量」组合还要快约 10%（来源：cognee README 「Run the Whole Memory Layer on Postgres」 段落）。

这意味着两件事：

1. **「GraphRAG 必须搭 Neo4j + Pinecone」是一种错觉**。cognee 用 Postgres 单一实例就把传统四件套（Neo4j + 向量 DB + Redis + Postgres）替换掉了，把架构复杂度从 4 个进程压成 1 个。
2. **「持久图 vs 临时会话」是两个不同生命周期**。会话缓存是为了「Agent 当前对话里的几次往返」服务的，由 `remember(session_id=...)` 写入、按 `recall(scope="auto")` 自动参与召回，但生命周期短于图本体——这跟传统 LangChain ConversationBufferMemory 类似，但 cognee 把它们明确分成两个数据通路，下文会拆。

### 双层 API 不是冗余，是两个抽象级别

```text
                ┌──────────────────────────────────────────────┐
   V1 任务语义   │  add / cognify / search / memify / prune    │ ← Pipeline 视角
                │  ─ Pipeline 由 Task 列表组成，可自定义      │
                ├──────────────────────────────────────────────┤
   V2 记忆语义   │  remember / recall / improve / forget       │ ← 业务视角
                │  ─ 自动路由、多源召回、可走 Cognee Cloud    │
                └──────────────────────────────────────────────┘
                                  ↓
                  同一份数据：add → cognify 写入图本体
                              remember → 写入 session 缓存
                              recall  → 从 session、trace、graph_context、session_context、graph 五源合并
```

V1 是给「想做图谱 ETL」的人准备的：你能直接调 `add()` 灌数据、`cognify()` 跑 Pipeline、`search(query_type=GRAPH_COMPLETION)` 出结果；V2 是给「Agent 业务代码」准备的：你只用关心 `remember("...")` 和 `recall("...")`，里面帮你决定走哪条管道、跑哪个 Pipeline、回哪条数据。两者底层共享同一份知识图谱。

## 边界拆分：容易被混成一团的三条主线

理解 cognee 最常见的误区是把「任务流水线」「图谱构建」「召回路由」当成同一条直线。事实上它们是三条**独立但被同一份数据串联**的机制：

| 主线 | 关心什么 | 谁负责 | 失败时 |
| --- | --- | --- | --- |
| **任务流水线**（Pipeline） | 怎么把原始数据一步步变成图 | `cognee.modules.pipelines.run_pipeline` + `Task` 列表 | 默认任务列表里的某一步出错，pipeline 有 `cognify_rollback_handler` 做回滚 |
| **知识图谱本体** | 实体 / 关系 / 嵌入的物理存放 | 三套后端（向量 / 图 / 会话） | 数据没丢失，只是不同位置不一致 |
| **召回路由**（Recall） | 同一句 query 应该走哪些源、按什么顺序合并 | `cognee.api.v1.recall.recall` + `query_router` | 返回空结果集而不是报错，业务侧需自行判定 |

举一个反例：如果读者只看了 README 的 Quickstart，就以为 `remember("...")` 直接写图——其实 `remember` **默认只写 session 缓存**，永久图谱写入要靠 `remember` 内部走 `add + cognify + improve` 链路（README 注释：「Store permanently in the knowledge graph (runs add + cognify + improve)」）。把 session 缓存当成长期记忆就是典型误解。

## 核心机制：cognify 流水线怎么把文本变成图

### 默认 Pipeline（来自 `cognee/api/v1/cognify/cognify.py`）

```python
default_tasks = [
    Task(classify_documents),                                          # EXTRACT: 文档分类
    Task(extract_chunks_from_documents,
         max_chunk_size=chunk_size or get_max_chunk_tokens(),
         chunker=chunker),                                             # EXTRACT: 语义分块
    Task(extract_graph_and_summarize,
         graph_model=graph_model,
         config=config,
         custom_prompt=custom_prompt,
         task_config={"batch_size": chunks_per_batch}),                # COGNIFY: 实体+关系抽取 + 摘要
    Task(add_data_points,
         embed_triplets=embed_triplets,
         task_config={"batch_size": chunks_per_batch}),                # LOAD: 持久化
    Task(extract_dlt_fk_edges),                                        # EXTRACT: 结构化源外键边
]
```

这条流水线读起来比传统 RAG 多了两步、少了三步：

- **多出「分类 + DLT 外键」**：先把文档类型定下来（PDF / 代码 / CSV），再把结构化数据源（DLT Source）里隐含的「主键—外键」关系显式建边。这正是 README 提到的「cognitive-science-grounded ontology generation」对应的工程化路径——不是 LLM 自己脑补实体关系，而是显式建模 schema。
- **少了「embedding + 检索」分离**：传统 RAG 是 chunk → embed → 存向量 → 检索时再 embed query；cognee 的 `extract_graph_and_summarize` 把实体抽取和摘要生成合并在一次 LLM 调用里，`add_data_points` 一次写入图节点、关系、和嵌入。

### 时间敏感场景：Temporal Cognify

cognee 还提供了一条**时间线优先**的备选 Pipeline（`get_temporal_tasks`），用 `extract_events_and_timestamps` + `extract_knowledge_graph_from_events` 替换默认的实体抽取任务。它把文本里的「事件 + 时间戳」先提取出来，再围绕事件构造图谱。这条流水线适合「按时间线回答问题」（「过去 30 天 X 的变化」），但因为要做两轮 LLM 抽取，默认 `chunks_per_batch=10`（默认流水线是 100），代价不低。

### Schema 不是写死的：graph_model + ontology resolver

`cognify(graph_model=KnowledgeGraph, ...)` 接收一个 Pydantic Model 作为图谱的实体模板。默认是通用 `KnowledgeGraph`，但你可以传自定义模型（比如 `ScientificPaper`）让抽取 LLM 知道要识别 `authors / methodology / findings`。配合 `ontology_file_path` + `get_ontology_resolver_from_env`，cognee 还支持从 OWL 本体文件加载预定义词汇表，让实体名自动对齐到既有术语。这是它与传统 GraphRAG 最大的工程差异：**图谱 schema 既是数据也是约束**。

## 核心机制：16 个 SearchType 怎么被一条 query 路由到一条路径

召回层的复杂度主要不在搜索本身，而在**怎么把一句自然语言问句映射到正确的搜索策略**。`cognee/modules/search/types/SearchType.py` 里硬编码了 17 种：

```text
SUMMARIES / CHUNKS / RAG_COMPLETION / HYBRID_COMPLETION / TRIPLET_COMPLETION
GRAPH_COMPLETION / GRAPH_COMPLETION_DECOMPOSITION / GRAPH_SUMMARY_COMPLETION
GRAPH_COMPLETION_COT / GRAPH_COMPLETION_CONTEXT_EXTENSION / FEELING_LUCKY
CYPHER / NATURAL_LANGUAGE / TEMPORAL / CODING_RULES / CHUNKS_LEXICAL
AGENTIC_COMPLETION
```

设计上，**GRAPH_COMPLETION 是默认推荐**，它把图谱上下文 + LLM 推理结合；CHUNKS / RAG_COMPLETION 是给「我只要原文档片段」用的退路；CYPHER 是把问句当成图查询语言直跑。TEMPORAL 走上面提到的 temporal cognify 路径；CODING_RULES / CHUNKS_LEXICAL 给代码检索和精确匹配专用。

### Query Router：规则打分，不调 LLM

`recall()` 默认开启 `auto_route=True`，调用 `cognee.api.v1.recall.query_router.route_query` 给问句打分——**纯正则 + 加权打分，不调任何 LLM**。这是工程上很务实的选择：路由这一步如果再调一次 LLM，每次召回的成本和延迟就翻倍了。

举几个判定规则（来自 `query_router.py`）：

- 含 `MATCH` / `RETURN` / `CREATE` 开头 → CYPHER（权重 10.0）
- 含 `def ` / `return ` / `async ` / `await ` / `import ` / `class X(` / `.py` / `function X(` → CODING_RULES（权重 3.0–5.0）
- 整句是 `"exact phrase"` → CHUNKS_LEXICAL（权重 8.0）
- 含 `why` / `explain` / `reasoning` / `step by step` / `chain of thought` → GRAPH_COMPLETION_COT（权重 4.0）
- 命中失败时退到 GRAPH_COMPLETION

每个 SearchType 都维护一个 `runner_up`，路由结果带置信度——业务侧可以据此决定要不要让用户确认「我理解对了你的问题吗」。

### Recall 多源合并：5 个数据源、auto_fallthrough 短路逻辑

`recall()` 内部把可召回的数据源定义成 5 个：

```python
runners = {
    "session": _run_session,                # session 缓存：QAEntry 关键词匹配
    "trace": _run_trace,                    # session 缓存：TraceEntry（工具调用追踪）
    "graph_context": _run_graph_context,    # session 生命周期衍生的图上下文快照
    "session_context": _run_session_context,# 主动构建的会话级 lessons 块
    "graph": _run_graph,                    # 永久图本体（走 search()）
}
```

`scope` 决定哪些源参与，默认 `"auto"` 走三种逻辑：

1. 只传 `session_id`（没有 datasets / query_type）：先跑 session，命中就**短路**（auto_fallthrough=True），不查永久图——这是「当前对话里的事实」优先语义。
2. 传 `session_id + datasets / query_type`：session 和 graph 都参与，两边结果合并（auto_fallthrough=False）。
3. 不传 `session_id`：只跑 graph，相当于经典 GraphRAG。

这条策略解释了为什么 `recall()` 返回的每条结果都带 `_source` 字段（`session` / `graph` / `trace` / `graph_context` / `session_context`）。下游 Agent 用 `source` 字段就能判断这条事实是「会话内短期」还是「永久知识」，决定要不要把它写入下一轮 prompt。

## 任务流案例：一次 `remember → recall` 跑过的完整路径

把上面的机制串起来，下面是 `await cognee.remember("用户偏好详细解释")` → `await cognee.recall("用户偏好什么解释风格?")` 在 cognee 内部走过的路径（结合 `remember/remember.py` 与 `recall/recall.py`）：

1. **入口分发**：`remember()` 检查 `cognee.serve(url=...)` 是否已注册远端客户端。已注册 → 调远端 HTTP；否则本地 `SessionManager.add_qa(user_id, session_id, question="", answer=text)`。
2. **session 写入**：QAEntry 落进 SQL session cache（默认 Postgres / SQLite）；同时判断是不是文件占位符（`[UploadFile]`），是的话跳过避免污染召回。
3. **远端/本地分支**：`recall()` 同理会分流；本地分支跑 5 个 runner。
4. **query 路由**：`route_query("用户偏好什么解释风格?")` 命中不到任何特殊模式，落到 GRAPH_COMPLETION（runner_up 通常是 RAG_COMPLETION）。
5. **session 检索**：`_search_session` 把 query 做关键词分词（长度 ≥ 2 的 `\b\w+\b`），匹配 session QAEntry；命中 → 加进 `merged`。
6. **auto_fallthrough 短路**：因为只传了 `session_id` 没传 datasets，session 有命中就直接 `break`，**不跑 `_run_graph`**。
7. **返回结果**：list of `RecallResponse`，每条带 `source="session"`，可被 Agent 直接拼成 prompt 上下文。

如果第 2 步是 `remember("Cognee turns documents into AI memory")`（不带 session_id），`remember()` 内部走 `add + cognify + improve` 链路：先入 dataset（`main_dataset`）→ 跑默认 Pipeline → 实体和关系进入永久图。**两条入口，一条写永久图，一条写 session 缓存**——这就是为什么 cognee 的 Quickstart 同时演示两种用法。

## Benchmark 解读：BEAM 在测什么、不在测什么

cognee README 给出 BEAM 上的成绩：100K tokens 时 0.79（>0.8 with per-question routing），10M tokens 时 0.67，而上一代 SOTA 是 0.735 / 0.641，传统 Obsidian / RAG baseline 约 0.33。

在把这些数字当成「cognee 比传统 RAG 强两倍」之前，先拆清 BEAM 是什么：

1. **测的是什么**：BEAM 是 cognee 团队自己提出的长上下文对话记忆 benchmark，专门测试一个系统能不能在「对话越长、上下文越乱」的情况下仍然跟踪状态变化——这比传统 needle-in-a-haystack 更贴近 Agent 真实工作。
2. **数字反映系统的哪部分**：因为 cognee 默认走 `GRAPH_COMPLETION` + 时间敏感的实体抽取，BEAM 上它对「状态变化」「实体引用更新」类问题天然占优；纯向量检索在「同义词替换」「代词指代消解」上的劣势在 100K+ 量级会被放大。
3. **不能推出什么**：
   - 不能推出「cognee 在所有 RAG 任务上都比传统向量检索强」——BEAM 偏 Agent 记忆，不是通用问答。
   - 不能推出「0.79 是绝对分数」——README 自己注明「These numbers are a directional signal rather than a definitive measure」。
   - 不能推出「在小语料（<10K tokens）上同样比例提升」——基准本身是在 100K / 10M 这种长上下文设定的。

一句话：BEAM 验证的是「图谱在长上下文对话里是不是比纯向量更有用」，**对短文档问答场景的优劣没有直接证据**。

## 采用顺序：谁应该先用，谁可以等等

cognee 不是「装上就能用的开箱即用 RAG」，它对运维和 LLM 调用预算有明确要求。结合仓库现状（v1.2.2，2026-06-26 发布，活跃度很高，331 个 open issues）给一组建议：

**先上**：已经在生产里跑 Agent、需要跨会话长期记忆、且对图谱 schema 有定制诉求的团队。具体来说就是：

- 客服 / 售后 Agent，历史工单需要长期累积成「客户画像」
- SQL Copilot / 代码评审工具，专家查询模式需要可复用
- 多 Agent 协作，知识需要共享而不是各 Agent 各自维护

**可以等等**：

- 文档问答量 < 1K 条 / 项目：图谱抽取的 LLM 成本远超收益，直接用向量检索 + 简单重排足够
- 强隐私 / 离线场景：默认依赖 OpenAI 兼容接口，本地 LLM 需要自己接通 Ollama / vLLM
- 「我要 RAG 但不想碰图谱」的轻量需求：LangChain / LlamaIndex 的标准 RAG 仍是更轻的入门

**起步路径**：

1. 先用 Postgres + pgvector 跑通 Quickstart（不需要 Neo4j）
2. 用 `remember()` + `recall()` 跑一周，确认多源召回是不是你想要的
3. 把领域 `KnowledgeGraph` 换成自定义 Pydantic 模型，提升抽取精度
4. 必要时再切换到 Neo4j / Qdrant / LanceDB 等专用后端

## 结尾判断

cognee 把「记忆」这件事拆成了一个**显式可拆的工程子系统**——存储层、Pipeline、召回路由三件事各自独立，Agent 业务只通过 `remember/recall` 这条窄接口碰它。这是它和「在 LangChain 里塞 ConversationBufferMemory」最本质的区别：cognee 把记忆当成**和业务逻辑同等重要的基础设施**，而不是一个被遗忘在 prompt 模板里的字符串。

但也别高估它：图谱抽取每条都要调 LLM，**长期记忆的真实成本是 LLM 调用预算**；BEAM benchmark 0.79 漂亮，但小语料上的代价是否值得，需要结合业务场景实测。把它当「Agent 长期记忆的操作系统内核」看，比当「更好的 RAG」看更接近它的工程定位。

仓库链接：<https://github.com/topoteretes/cognee>