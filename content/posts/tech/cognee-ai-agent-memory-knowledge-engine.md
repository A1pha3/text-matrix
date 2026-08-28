---
title: "Cognee：让 Agent 拥有会自我修正的长期记忆"
date: "2026-04-17T16:32:00+08:00"
slug: "cognee-ai-agent-memory-knowledge-engine"
github_repo: "topoteretes/cognee"
description: "1.6 万＋ Star 的开源 AI 记忆平台。围绕 remember/recall/improve/forget 四个动词构建 Agent 长期记忆：会话缓存与知识图谱双存储，反馈驱动的自改进闭环，支持多格式数据、多种图/向量后端，可自托管或部署到云平台。"
draft: false
categories: ["技术笔记"]
topics: ["open-source-ai-tools"]
tags: ["AI Agent", "记忆系统", "知识图谱", "向量搜索", "LLM", "Python", "RAG"]
---

# Cognee：给 Agent 一张会自我修正的记忆

Cognee（[topoteretes/cognee](https://github.com/topoteretes/cognee)）常被概括成「给大模型加记忆的知识引擎」，但把它的价值停在「多了个向量库」上就低估了。它真正想解决的问题，不是把文件存起来，而是让记忆在被使用的过程中被修正——Agent 上一次答错了，下一次能少犯同样的错。面向这一点，它把全部能力压缩成四个动词：`remember`、`recall`、`improve`、`forget`，底层是向量检索加知识图谱的双轨存储。

本文先拆开这套系统里容易混在一起的三条线（写、读、改），再解释每个动词背后发生了什么，用一个客服场景把流程串起来，最后说明那篇相关论文究竟证明了什么。所有 API 与配置均以官方文档为准。

## 先分清几条线

读完 Cognee 的文档，比「记住/召回」更容易困惑的，是这套系统其实同时包含三条并行机制，别把它们当成一条单线故事：

```
写 ── remember：数据进来
   ├─ 会话缓存（快速、短暂）
   └─ 永久图谱（慢但持久）

读 ── recall：问题进来
   └─ 自动路由 → 13＋ 种检索策略之一

改 ── improve：答案被判定后
   └─ 反馈权重 → 重新排布图谱与缓存
```

- **存储面**：会话缓存（session）和永久知识图谱（knowledge graph）是两个不同的落盘位置，写入路径不同，生命周期不同。
- **检索面**：`recall` 不止一种搜索，而是一个自动路由到多种策略的入口。
- **改页面**：`improve` 不是定时整理，而是一条把「用户反馈」转成「图谱权重」的闭环，这是 Cognee 区别于普通 GraphRAG 框架的核心。

下面把这几条线分别讲清楚。

## 四个动词就是记忆的生命周期

### remember：写入

`remember` 是唯一的写入入口，两种模式对应上面的存储面：

- **永久记忆**：不传 `session_id` 时，一次调用就走完整个摄入管线——归一化数据、切块、抽取实体与关系、建图谱、做嵌入，最后写入一个带名字的数据集（默认 `main_dataset`）。
- **会话记忆**：传 `session_id` 时，先写入会话缓存用于快速短时记忆；若 `self_improvement=True`（默认），随后在后台跑一轮 `improve`，把会话内容桥接进永久图谱。

```python
import cognee

# 永久记忆：写入默认数据集 main_dataset
await cognee.remember(
    "The customer prefers quarterly summaries.",
    session_id="customer_42",
)
```

`remember` 接受的数据形态很宽：纯文本、本地文件路径、HTTP/HTTPS URL、S3 路径，以及带元数据的 `DataItem` 对象。

### recall：读出

`recall` 用自然语言提问，返回的是锚定在图谱上的回答，而不是凭空的上下文拼接。不显式指定检索类型时，它会自动路由，选一个合适的策略再检索。

```python
answers = await cognee.recall(
    query_text="What does this customer care about?",
    session_id="customer_42",
)
```

`top_k` 默认 15；想跳过最后的 LLM 组装、只拿原始上下文，可以用 `only_context=True`。如果你需要直接控制检索器，低层的 `cognee.search()` 仍然保留。

### improve：让记忆自我修正

`improve` 是 Cognee 与普通 RAG 拉开差距的地方。它把「反馈」转成图谱里的权重变化：一条答案被确认、被纠正或被打回，这个判定会变成命中了该答案的记忆节点/边上的信号——确认的记忆检索权重升高，被纠正或误导的记忆被压低。

```python
# 手动触发改进，可限定数据集或指定会话
await cognee.improve(dataset="main_dataset")
await cognee.improve(dataset="main_dataset", session_ids=["customer_42"])
```

调 `improve` 时，它实际上跑四件事：

1. 把反馈权重应用到本次会话问答用到的节点与边上；
2. 把会话问答内容按实体抽取，并入永久图谱（打上会话来源标记）；
3. 做一次 memify 富集——为（主语，谓语，宾语）三元组生成向量嵌入；
4. 把最近更新的图谱边同步回会话缓存。

### forget：删除

`forget` 干净地删掉一条记忆及其关联边，其余图谱保持完整，因此可以按需移除过期信息或履行删除请求，而不必重建整张图。

```python
await cognee.forget(dataset="main_dataset")
```

## 存储面：后端由谁承载

Cognee 把三种存储分开，各自可替换。本地开发用嵌入式默认后端，零外部服务即可跑通。

| 存储 | 默认（本地） | 可选后端 |
|---|---|---|
| 图 | Kuzu | Neo4j、Neptune、Postgres-graph |
| 向量 | LanceDB | Chroma、pgvector、Qdrant、Weaviate、Milvus |
| 关系/会话缓存 | SQLite | PostgreSQL、Redis |

权限上也做了多层设计：数据分数据集（Dataset）承载，配 User/Permission 控制谁能读；会话缓存按 `{user_id}:{session_id}` 组织，支持跨用户共享数据集与权限隔离。

## 检索面：多种策略与规则路由

`recall` 的自动路由不是靠 LLM 判断，而是一套基于关键词权重的规则分类器。它把查询分派到 13＋ 种搜索类型里的一种，常见的有：

- `GRAPH_COMPLETION`（默认）：LLM 结合图谱上下文作答
- `GRAPH_COMPLETION_COT`、`GRAPH_SUMMARY_COMPLETION`：更深的图推理模式
- `TRIPLET_COMPLETION`：基于三元组检索 + 补全
- `RAG_COMPLETION`：从检索分块作答
- `CHUNKS`、`CHUNKS_LEXICAL`：原始分块 / BM25 式词法检索
- `SUMMARIES`：层级摘要检索
- `TEMPORAL`：带时间感知的检索
- `CODING_RULES`：面向代码库的检索
- `CYPHER`：直接走图查询

路由与真正的检索解耦，意味着同一份 `recall` 调用，底层可以切到图遍历、向量近邻或词法排名组合出的不同策略。因混合检索需要做异构结果融合，这也正是图检索加向量检索一起工作而不互相打架的落点。

## 改页面：反馈如何变成图谱权重

Cognee 的两处设计让反馈能真正落进记忆：

- **反馈加权边**：图里的边带 `feedback_weight` 与 `importance_weight` 两个字段。用户确认过的记忆，对应边权重上调，未来的查询排序会更靠前；被打回的则下调。这让图谱的演化来自 Agent 的真实使用，而不只是批量导入文件。
- **三元组嵌入**：大多数 GraphRAG 只给节点做嵌入，Cognee 的 memify 额外给（主语，谓语，宾语）三元组做嵌入。于是可以按语义搜「关系本身」——想找所有和「某人就职于某机构」语义相似的三元组，也能做。

这两点合起来，回答了「记忆会越用越准吗」这个一般框架不回答的问题。

## 一次客服交互如何穿过系统

用一个最小场景把上面的机制接起来。

```
用户：我昨天的订单为什么还没发货？
  │
  ▼
recall("订单延误与处理历史", session_id="customer_42")
  │  规则路由 → 先查会话缓存，再查永久图谱
  ▼
拿到该客户历史工单 + 过往处理结论
  │
  ▼
Agent 组织答案回复用户
  │
  ▼
记住这次交互 remember(..., session_id="customer_42")
  │
  ▼
用户/系统判定这条回答是否有用
  │
  ▼
improve() → 把这次的反馈加权到相关边，"延误"相关结论权重更新
  │
  ▼
下一次该客户再问同类问题，排序更靠前的就是上次被确认的结论
```

这不是把整段对话塞进上下文，而是每次只在图谱里取回相关的那几条记忆。长期积累后，同一个客户的历史偏好和已确认的处置结论会自动变成下一次检索的更优先来源。

## 论文证明了什么，又没说证明什么

Cognee 团队在 [arXiv:2505.24478](https://arxiv.org/abs/2505.24478)「Optimizing the Interface Between Knowledge Graphs and LLMs for Complex Reasoning」中，研究的是知识图谱与 LLM 之间接口上的超参优化，而不是「Cognee 优于所有记忆系统」。它在三个多跳问答基准（HotPotQA、TwoWikiMultiHop、MuSiQue）上，针对切块、构图、检索和提示词做参数调优，用精确匹配、F1 和 DeepEval 的 LLM 正确性打分来评估。

读这份论文时要分清一个边界：它测的是**多跳英文问答**这一类任务，反映的是「在图谱增强的 RAG 管线上，超参选择和评估指标如何影响分数」，不能推出「Cognee 在任意 Agent 记忆任务上都最强」。agent 化的长期记忆（如跨会话纠错、反馈闭环）并不在这三个问答基准的覆盖范围内，仓库里也没有对应这类任务的基准结果。想评估 Cognee 是否适合你的 Agent，得按自己的任务类型去跑，而不是照搬论文数字。

## 生态、部署与上手

### 与 Agent 的接入

除了 Python SDK，Cognee 以多种形态接入现有的 Agent 生态：

- **MCP**：官方提供 [cognee-mcp](https://github.com/topoteretes/cognee/tree/main/cognee-mcp) 服务器，任何支持 MCP 的工具都能连上记忆。
- **官方集成仓库** [cognee-integrations](https://github.com/topoteretes/cognee-integrations)：提供 Claude Code 插件、Claude Agent SDK、Codex、Hermes、OpenAI Agents、LangGraph、CrewAI、Google ADK 等接入。
- **OpenClaw**：`@cognee/cognee-openclaw` npm 插件。
- **其他平台**：Dify、n8n、Strands，以及通过 MCP 实现的 VS Code / Copilot。

### 快速上手

```bash
uv pip install cognee
export LLM_API_KEY="your_openai_api_key"
```

```python
import asyncio
import cognee

async def main():
    await cognee.remember(
        "Cognee turns documents into agent memory.",
        session_id="customer_42",
    )
    answers = await cognee.recall(
        query_text="What does cognee do?",
        session_id="customer_42",
    )
    await cognee.improve(dataset="main_dataset")

asyncio.run(main())
```

也可以用命令行快速试一遍：

```bash
cognee-cli remember "Cognee turns documents into agent memory."
cognee-cli recall "What does cognee do?"
cognee-cli improve
cognee-cli -ui   # 启动本地 Web 界面
```

`cognee-cli doctor` 能先检查环境是否可正常运行；`remember` 的 `--dry-run` 可以在真正调用 LLM 前估算 token 用量与费用。早期的 `add / cognify / search / delete` 也仍保留为底层接口。

### 部署

推荐用官方镜像一条命令起服务：

```bash
echo 'LLM_API_KEY="your_openai_api_key"' > .env
docker run --env-file .env -p 8000:8000 --rm -it cognee/cognee:main
```

要么直接用 Cognee Cloud（托管、含 99.9% 可用性 SLA），要么自托管到 Modal、Railway、Fly.io、Render、Daytona 等平台。需要隐私隔离的场景完全可本地部署，数据不出机器。

## 什么时候用它，什么时候不必用

- **适合**：Agent 需要在多轮、跨会话间积累可检索的经验，尤其是「答错过一次、下次要规避同样错误」的场景（客服、运维排障、个人助理）。
- **可以等一等**：你只是在做一次性问答、记忆体量很小，或任务本身没有「必须记住上次结论」的需求——纯向量 RAG 就够，不必引入图谱和后端的运维成本。
- **评估建议**：先用 `--dry-run` 估一下 token 费用；再拿你真实的「多轮纠错」场景小批量验证反馈闭环是否生效，再决定是否上生产。自托管要同时维护图、向量、关系三个后端，规模上去之前的收益要仔细核算。

## 常见问题

**Cognee 和其他 RAG 框架有什么区别？**
它在向量检索之上叠加了知识图谱，并内置四个动词和反馈闭环；`improve` 把用户判定写回图谱权重，这是普通 RAG 没有的自我修正能力。

**支持哪些向量/图后端？**
图：Kuzu（默认）、Neo4j、Neptune；向量：LanceDB（默认）、Chroma、pgvector、Qdrant、Weaviate、Milvus；会话缓存可用 PostgreSQL、Redis。本地开发默认 SQLite + LanceDB + Kuzu。

**成本来源是什么？**
主要是 LLM 调用（建图谱的实体抽取、检索时的问答组装）。`--dry-run` 可预先估算。Cognee Cloud 有自己的计价与免费额度，自托管则用你自己的 LLM API Key。

**数据安全怎么保证？**
可完全本地部署，数据不出机。支持数据集级权限与用户隔离（RBAC），跨用户共享记忆通过权限授予完成。

**能处理多格式数据吗？**
能。文本、文件、URL、S3 路径及带元数据的 `DataItem` 均可摄入；文档、音视频转写等通过底层加载器归一化后再建图。

## 相关资源

- **GitHub**：[topoteretes/cognee](https://github.com/topoteretes/cognee)
- **文档**：[docs.cognee.ai](https://docs.cognee.ai/)
- **集成仓库**：[cognee-integrations](https://github.com/topoteretes/cognee-integrations)
- **论文**：[arXiv:2505.24478](https://arxiv.org/abs/2505.24478)
- **社区**：[Discord](https://discord.gg/NQPKmU5CCg)