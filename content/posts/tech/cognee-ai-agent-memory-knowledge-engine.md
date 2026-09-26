---
title: "Cognee：让 Agent 拥有会自我修正的长期记忆"
date: "2026-04-17T16:32:00+08:00"
lastmod: "2026-09-26T11:30:00+08:00"
slug: "cognee-ai-agent-memory-knowledge-engine"
github_repo: "topoteretes/cognee"
source_key: "gh:topoteretes/cognee"
description: "3 万+ Star（截至 2026-09）的开源 AI 记忆平台。围绕 remember/recall/improve/forget 四个动词构建 Agent 长期记忆：会话缓存与知识图谱双存储，九阶段自改进闭环，v1.6 起支持无 LLM Key 本地运行，可自托管或部署到云平台。"
draft: false
categories: ["技术笔记"]
topics: ["open-source-ai-tools"]
tags: ["AI Agent", "记忆系统", "知识图谱", "向量搜索", "LLM", "Python", "RAG"]
---

# Cognee：给 Agent 一张会自我修正的记忆

Cognee（[topoteretes/cognee](https://github.com/topoteretes/cognee)）常被概括成「给大模型加记忆的知识引擎」，但把它的价值停在「多了个向量库」上就低估了。它真正想解决的问题，不是把文件存起来，而是让记忆在被使用的过程中被修正——Agent 上一次答错了，下一次能少犯同样的错。面向这一点，它把全部能力压缩成四个动词：`remember`、`recall`、`improve`、`forget`，底层是向量检索加知识图谱的双轨存储。

本文先拆开这套系统里容易混在一起的三条线（写、读、改），再解释每个动词背后发生了什么，用一个客服场景把流程串起来，最后分清论文与官方评测各自证明了什么。文中的 API、参数与后端均对照 2026-09-26 的 main 分支源码与官方文档核实（v1.6），后续以官方文档为准。

## 先分清几条线

读 Cognee 的文档，比「记住/召回」更容易困惑的，是这套系统同时包含三条并行机制，别把它们当成一条单线故事：

```text
写 ── remember：数据进来
   ├─ 会话缓存（快、短命，按 user + session 隔离）
   └─ 永久图谱（经摄入管线构建，持久）

读 ── recall：问题进来
   └─ 规则路由 → 会话缓存优先，未命中走 HYBRID 图检索

改 ── improve：答案被判定后
   └─ 九个阶段 → 反馈权重、会话蒸馏、三元组富集写回图谱
```

- **存储面**：会话缓存（session）和永久知识图谱（knowledge graph）是两个不同的落盘位置，写入路径不同，生命周期不同。
- **检索面**：`recall` 的自动路由是「两条固定规则 + 一个默认策略」，不是智能调度；其余检索类型都要显式指定才会启用。
- **改进面**：`improve` 把「用户反馈」和「会话内容」一起转成图谱里的持久变化，这是 Cognee 区别于普通 GraphRAG 框架的地方。

下面把这几条线分别讲清楚。

## 四个动词就是记忆的生命周期

### remember：写入

`remember` 是唯一的写入入口，两种模式对应上面的存储面：

- **永久记忆**：不传 `session_id` 时，一次调用就走完整个摄入管线（`add()` + `cognify()`）——归一化数据、切块、抽取实体与关系、建图谱、做嵌入，最后写入一个带名字的数据集（默认 `main_dataset`）。
- **会话记忆**：传 `session_id` 时，先写入会话缓存用于快速短时记忆；若 `self_improvement=True`（默认），随后在后台跑一轮 `improve`，把会话内容桥接进永久图谱。桥接有防抖控制（`IMPROVE_DEBOUNCE_ENTRIES` / `IMPROVE_DEBOUNCE_SECONDS`），攒够新条目或等够时间才触发。

```python
import cognee

# 永久记忆：不传 session_id，直接建图
await cognee.remember(
    "The customer prefers quarterly summaries.",
    dataset_name="crm_notes",
)

# 会话记忆：传 session_id，先写会话缓存，后台桥接进图谱
await cognee.remember(
    "The customer prefers quarterly summaries.",
    session_id="customer_42",
)
```

`remember` 接受的数据形态很宽：纯文本、本地文件路径（含 `file://`）、HTTP/HTTPS 网页、S3 路径、二进制流，以及带元数据的 `DataItem` 对象。同内容重复写入是空操作；同路径不同内容的文件会要求你用 `update()` 显式替换，不会静默覆盖。

### recall：读出

`recall` 用自然语言提问，返回锚定在图谱上的回答，而不是凭空的上下文拼接。不显式指定检索类型时走自动路由（下节细说）；带 `session_id` 时先走快路径：按关键词匹配会话缓存里的问题、上下文与答案字段，命中就直接返回（结果带 `source="session"` 标记），没命中才落到永久图谱做检索（标记为 `source="graph"`）。

```python
answers = await cognee.recall(
    query_text="What does this customer care about?",
    session_id="customer_42",
)
```

`top_k` 默认 15；想跳过最后的 LLM 组装、只拿原始上下文，可以用 `only_context=True`。需要更细粒度控制时，旧版底层接口 `cognee.search()` 仍然保留。

### improve：让记忆自我修正

`improve` 是 Cognee 与普通 RAG 拉开差距的地方。调一次 `improve`，它按固定顺序跑九个阶段，每个阶段先判断当前配置下有没有活干，没活干就跳过并在结果里说明原因：

1. `feedback_weights`：把反馈权重写到本轮会话检索用到的节点与边上——高评分抬升来源记忆的影响力，低评分压低；
2. `persist_session_qa`：把会话问答内容经摄入管线并入永久图谱，归入 `user_sessions_from_cache` 节点集（带上会话来源标记）。这一步失败会中止整个 improve 并抛错，因为静默丢问答等于丢数据；
3. `persist_agent_traces`：把 Agent 与工具调用的结构化轨迹写进图谱，让工具执行结果也能成为长期记忆；
4. `extract_agent_context`：把待处理的轨迹窗口提炼成会话上下文经验；
5. `distill_sessions`：从会话中蒸馏「经验教训」文档（打上 `session_learnings` 标记）——起草、校对两道 LLM 关卡，只有通过置信度门槛、未被标为有害的内容才入库；
6. `update_user_preferences`：把评分与明确表达的偏好并入用户的偏好子图（需开启 `PERSONALIZATION_ENABLED`，默认关）；
7. `build_truth_subspace`（可选）：从蒸馏出的教训构建真值锚点；
8. `triplet_enrichment`：为图谱里的（主语，谓语，宾语）三元组生成向量嵌入并建索引；
9. `global_context_index`（可选）：构建数据集级的摘要索引，供后续检索前置注入。

其中 4、5、9 需要调用 LLM 起草文本；其余阶段不依赖 LLM。所以没配 API Key 时，improve 不会失败——依赖 LLM 的阶段以 `no_llm_configured` 跳过，反馈加权和会话桥接照常完成。

```python
# 手动触发改进，可限定数据集或指定会话
await cognee.improve(dataset="main_dataset")
await cognee.improve(dataset="main_dataset", session_ids=["customer_42"])
```

### forget：删除

`forget` 干净地删掉一条记忆及其关联边，其余图谱保持完整，因此可以按需移除过期信息或履行删除请求，而不必重建整张图。

```python
await cognee.forget(dataset="main_dataset")
```

## 存储面：后端由谁承载

Cognee 把三种存储分开，各自可替换。本地开发用嵌入式默认后端，零外部服务即可跑通：

| 存储 | 默认（本地） | 可选后端 |
|---|---|---|
| 图 | Ladybug | Kuzu、Neo4j（含 Aura）、Neptune、Postgres、Turso、Falkor |
| 向量 | LanceDB | pgvector、Turso、Qdrant（多用户模式） |
| 关系库/会话缓存 | SQLite | PostgreSQL、Redis、本地文件系统 |

Ladybug 是 Kuzu 的更名延续——源码注释自述这是「the Ladybug rename」，cognee 1.x 把它设为默认（`GRAPH_DATABASE_PROVIDER=ladybug`），并刻意沿用旧的 Kuzu 数据文件路径，本机已有 Kuzu 图的用户升级后不会丢数据；显式指定 `kuzu` 仍可切回。

Cognee 1.0 之后，还可以用**单个 PostgreSQL 实例**同时承载关系、嵌入、会话与元数据，把整个记忆层收敛到一个后端上。不过要注意官方在 README 里标出的边界：Postgres 充当图存储目前按 demo 特性发布，生产级版本是单独的授权产品。拿它做原型验证没问题，上生产前要掂量这一点。

权限上是多层设计：数据分数据集（Dataset）承载，配 User/Permission 控制谁能读；会话缓存按 `(user_id, session_id)` 隔离，同一 `session_id` 在两个用户下是两个会话；跨用户共享数据集通过权限授予完成。

## 检索面：两条规则，一个默认

`recall` 的自动路由不调用 LLM，是一张刻意做得很小的规则表（源码 `cognee/api/v1/recall/query_router.py`）：

| 查询长什么样 | 路由到 | 返回什么 |
|---|---|---|
| 整句是一个双引号短语，如 `"exact wording"` | `CHUNKS_LEXICAL` | 原始分块，不生成回答 |
| 问句提到 coding rules / standards / conventions 等 | `CODING_RULES` | 结构化条目，不生成回答 |
| 其余一切（所有正常问句） | `HYBRID_COMPLETION`（默认） | 一次 LLM 调用，同时检索分块、摘要与实体邻域并作答 |

设计意图写在源码注释里：规则只允许选「在默认构建的图谱上不差于 HYBRID」的策略，且不在没有明确信号时额外消耗 LLM 调用。HYBRID 本来就把分块、摘要、实体邻域一次查完，对普通问句已是正确操作；带时间、摘要、深推意图的问句（`TEMPORAL`、`SUMMARIES`、`GRAPH_COMPLETION_COT` 等）必须显式传 `query_type`。`CYPHER` 则干脆不允许自动路由——recall 链路只校验读权限，如果路由器能把任意文本送去执行图查询语句，等于让任何能读的人都能改图，所以它只接受调用方的显式指定。

两个兜底机制让这套小路由不至于帮倒忙：没配 LLM 时，默认策略退到 `CHUNKS`（纯向量检索分块），因为没有模型能生成补全回答；规则选中的类型被后端拒绝或返回空时，自动以 `HYBRID_COMPLETION` 重试一次——你自己指定的 `query_type` 不会被二次改写。想要「让 LLM 自己挑类型」，还有一个 `FEELING_LUCKY`，它是唯一由 LLM 选择策略的入口，选不出可用类型就退回 `RAG_COMPLETION`。

## 改进面：反馈如何变成图谱权重

Cognee 的几处设计让反馈能真正落进记忆：

- **用法驱动的权重**：图谱的演化来自 Agent 的真实使用，而不是批量导入文件。回答被判定后，`feedback_weights` 阶段把这条信号写到本轮检索用过的节点与边的 `feedback_weight` 上——被确认的记忆变强，后续查询更靠前；被纠正或误导的记忆被压低。
- **三元组嵌入**：大多数 GraphRAG 只给节点做嵌入，Cognee 的富集阶段额外给（主语，谓语，宾语）三元组生成向量嵌入。于是可以按语义搜「关系本身」——想找所有和「某人就职于某机构」语义相似的三元组，也能做。
- **会话蒸馏**：`distill_sessions` 把通过置信度门槛的会话指引提炼成 lesson 文档存入图谱，跨会话复用。上一轮答错被纠正的结论，可以以教训的形式沉淀下来。

这三点合起来，回答了「记忆会越用越准吗」这个一般框架不回答的问题。

## 一次客服交互如何穿过系统

用一个最小场景把上面的机制接起来。

```text
用户：我昨天的订单为什么还没发货？
  │
  ▼
recall("订单延误与处理历史", session_id="customer_42")
  │  会话缓存关键词匹配 → 命中则直接返回（source="session"）
  │  未命中 → HYBRID_COMPLETION 查永久图谱（source="graph"）
  ▼
拿到该客户历史工单 + 过往处理结论
  │
  ▼
Agent 组织答案回复用户，remember(...) 记录这次问答
  │
  ▼
用户/系统对这条回答打分（cognee-cli feedback add ...）
  │
  ▼
improve() → 反馈权重落到检索用过的节点与边，会话问答并入图谱
  │
  ▼
下一次该客户再问同类问题，排序更靠前的就是上次被确认的结论
```

这不是把整段对话塞进上下文，而是每次只在图谱里取回相关的那几条记忆。长期积累后，同一个客户的历史偏好和已确认的处置结论会自动变成下一次检索的更优先来源。

## 论文与官方评测各自证明了什么

Cognee 团队在 [arXiv:2505.24478](https://arxiv.org/abs/2505.24478)「Optimizing the Interface Between Knowledge Graphs and LLMs for Complex Reasoning」中，研究的是知识图谱与 LLM 之间接口上的超参优化，而不是「Cognee 优于所有记忆系统」。它在三个多跳问答基准（HotPotQA、TwoWikiMultiHop、MuSiQue）上，针对切块、构图、检索和提示词做参数调优，用精确匹配、F1 和 DeepEval 的 LLM 正确性打分来评估。

读这份论文时要分清一个边界：它测的是**多跳英文问答**这一类任务，反映的是「在图谱增强的 RAG 管线上，超参选择和评估指标如何影响分数」，不能推出「Cognee 在任意 Agent 记忆任务上都最强」。反馈闭环、跨会话纠错这类 Agent 化的长期记忆能力并不在这三个问答基准的覆盖范围内，论文里也没有对应这类任务的结果。

仓库自带的评测是另一条线：[BEAM 基准](https://github.com/topoteretes/cognee/blob/main/cognee/eval_framework/beam/REPORT.md)用合成长对话测「对话记忆」，以 LLM 评判打分，报告的两个口径是 100K tokens 上下文得 **0.79**、10M tokens 得 **0.67**（0–1 分制）。README 特意提醒：这两个数字来自不同的对话、不同的摄入模型和不同的检索选择流程，10M 那一行还是探索性结果，互比之前要先读报告里的方法论与局限。它能说明的是 Cognee 的记忆组件在长上下文对话场景下分数衰减平缓，不能直接换算成「比某个竞品强多少」。

## 生态、部署与上手

### 与 Agent 的接入

除了 Python SDK，Cognee 以多种形态接入现有的 Agent 生态：

- **MCP**：官方提供 [cognee-mcp](https://github.com/topoteretes/cognee/tree/main/cognee-mcp) 服务器，Cursor、Cline 等任何支持 MCP 的客户端都能连上记忆。
- **官方集成仓库** [cognee-integrations](https://github.com/topoteretes/cognee-integrations)：提供 Claude Code 插件、Codex 插件、Claude Agent SDK、LangGraph、CrewAI、Google ADK、Hermes、Mastra、Dify、n8n、Strands、OpenCode、Obsidian、Slack、Telegram 等接入。以 Claude Code 为例，插件市场两条命令装好：

```bash
claude plugin marketplace add topoteretes/cognee-integrations
claude plugin install cognee-memory@cognee
```

- **OpenClaw**：`@cognee/cognee-openclaw` npm 插件。
- **多语言与协议**：TypeScript SDK、REST API，以及 topoteretes 组织下的 Rust 版 [cognee-rs](https://github.com/topoteretes/cognee-rs)。
- **记忆迁移**：支持 COGX 交换格式，可从 Mem0、Letta、Zep、Graphiti 导入已有记忆。

### 快速上手

需要 Python 3.10–3.14：

```bash
uv pip install "cognee[gliner]"   # gliner：本地抽取模型，不配 Key 也能建图
export LLM_API_KEY="your_openai_api_key"   # 可选；要生成式回答再配
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
    await cognee.improve(dataset="main_dataset", session_ids=["customer_42"])

asyncio.run(main())
```

不配 Key 时，文本摄入、检索与会话存储照常工作，只是 `recall` 返回匹配的原文而非生成的回答。也可以用命令行快速试一遍：

```bash
cognee-cli demo                                  # 加载内置示例数据，无需 API Key
cognee-cli remember "Cognee turns documents into agent memory."
cognee-cli recall "What does cognee do?"
cognee-cli improve --dataset-name main_dataset   # 对指定数据集跑一轮改进
cognee-cli -ui                                   # 启动本地 Web 界面（需 Node.js/npm）
```

`cognee-cli doctor` 能先检查配置与本地服务是否可运行；`remember` 的 `--dry-run` 可以在真正调用 LLM 前估算 token 用量与费用。反馈也能从命令行灌入：`cognee-cli feedback add <session> <qa_id> --score 5` 给某次回答打分，`improve` 时把这些分数加权进图谱。`datasets` 子命令可以查看数据集与入库状态。新流程统一用 `remember / recall / improve / forget` 四个动词；旧接口 `add / cognify / search / delete` 仍保留为底层命令。

### 部署

本地 API 演示推荐官方预构建镜像：仓库提供单文件 compose 配置（`docs/minimal-docker-compose.md`，含持久卷与单用户演示说明），也可以直接一条命令起服务：

```bash
echo 'LLM_API_KEY="your_openai_api_key"' > .env
docker run --env-file .env -p 8000:8000 --rm cognee/cognee:main
```

起来后 `GET /health` 验活，`/docs` 是交互式 API 参考。注意默认镜像不含 GLiNER，想在容器里无 Key 建图，需要自带 `gliner` extra 的镜像。

要么直接用 Cognee Cloud（托管服务，2026-09 官网口径 $5/工作区/月 + $1/百万 tokens，含 Slack、Notion、Google Drive 集成；企业版定制定价，带支持 SLA 与 BYO cloud/私有化部署），要么用官方模板自托管到 Modal、Railway、Fly.io、Render、Daytona、Islo。需要隐私隔离的场景完全可本地部署，数据不出机器。

## 什么时候用它，什么时候不必用

- **适合**：Agent 需要在多轮、跨会话间积累可检索的经验，尤其是「答错过一次、下次要规避同样错误」的场景（客服、运维排障、个人助理）。
- **可以等一等**：你只是在做一次性问答、记忆体量很小，或任务本身没有「必须记住上次结论」的需求——纯向量 RAG 就够，不必引入图谱和后端的运维成本。
- **评估路径**：先 `cognee-cli demo` 零成本看一眼图谱长什么样；再用 `cognee[gliner]` 在本地无 Key 跑通摄入与检索；最后接真实 LLM，小批量验证反馈闭环是否生效，`remember --dry-run` 估算 token 开销，再决定是否上生产。自托管若不走单 Postgres 路线，要同时维护图、向量、关系三类后端，规模上去之前的收益要仔细核算。

## 常见问题

**Cognee 和其他 RAG 框架有什么区别？**
它在向量检索之上叠加了知识图谱，并把「记忆被使用后的判定」写回图谱：反馈权重、会话问答持久化、教训蒸馏都是普通 RAG 没有的通路。换言之，普通 RAG 只会检索，Cognee 的记忆会因为被使用而改变。

**为什么默认后端全是嵌入式组件？**
Ladybug、LanceDB、SQLite 都是进程内或单文件存储，零外部服务即可在本地跑通一条完整记忆链路。要把后端换成 Neo4j、Postgres、Redis，改环境变量即可，应用代码不动。

**不想用 LLM 能用到什么程度？**
文本摄入、向量与词法检索、会话存储、反馈加权、会话桥接都不需要 LLM；生成式回答、会话蒸馏、全局索引这几类需要起草文本的阶段会自动跳过。纯本地安装照样能把会话内容并入图谱。

**成本来源是什么？**
主要是 LLM 调用（建图谱的实体抽取、检索时的回答组装、蒸馏）。`remember --dry-run` 可预先估算。本地模式零 API 成本；Cognee Cloud 按订阅加 token 计费；自托管则用你自己的 LLM API Key。

**数据安全怎么保证？**
可完全本地部署，数据不出机。支持数据集级权限与用户隔离（RBAC），会话按 `(user_id, session_id)` 天然隔离，跨用户共享记忆通过权限授予完成。

**能处理多格式数据吗？**
能。文本、本地文件、网页 URL、S3 路径及带元数据的 `DataItem` 均可摄入；PDF 等文档、音视频转写经底层加载器归一化后再建图。已有记忆可经 COGX 格式从 Mem0、Letta、Zep、Graphiti 迁入。

## 相关资源

- **GitHub**：[topoteretes/cognee](https://github.com/topoteretes/cognee)
- **文档**：[docs.cognee.ai](https://docs.cognee.ai/)
- **集成仓库**：[cognee-integrations](https://github.com/topoteretes/cognee-integrations) ｜ **社区插件**：[cognee-community](https://github.com/topoteretes/cognee-community)
- **论文**：[arXiv:2505.24478](https://arxiv.org/abs/2505.24478) ｜ **BEAM 评测报告**：[cognee/eval_framework/beam/REPORT.md](https://github.com/topoteretes/cognee/blob/main/cognee/eval_framework/beam/REPORT.md)
- **社区**：[Discord](https://discord.gg/NQPKmU5CCg) ｜ [r/AIMemory](https://www.reddit.com/r/AIMemory/)
