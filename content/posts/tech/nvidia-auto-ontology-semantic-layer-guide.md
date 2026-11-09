---
title: "Auto Ontology：把「口径」从 prompt 里搬进数据库，让 Agent 先学会拒绝回答"
date: "2026-11-10T03:30:16+08:00"
slug: "nvidia-auto-ontology-semantic-layer-guide"
description: "NVIDIA Auto Ontology 用编译—认证—回答三阶段，把业务术语、度量口径与表间关系沉淀进 Postgres 与 pgvector，向 Agent 提供只读 MCP 接口。本文拆解语义层结构、LangGraph 回答链路、覆盖度拒答机制与对照式 benchmark，并指出数据外传与明文凭据的治理代价。"
draft: false
categories: ["技术笔记"]
tags: ["NVIDIA", "语义层", "Text-to-SQL", "MCP", "企业数据"]
github_repo: "NVIDIA/auto-ontology"
source_key: "gh:NVIDIA/auto-ontology"
---

## 核心判断

企业数据问答的瓶颈通常不在模型推理能力，而在「口径」。同一句“收入”，财务系统按确认时点算，运营系统按下单时点算，另一个报表工具里它干脆是另一列的别名。模型再强，面对三个互不兼容的口径也只能挑一个猜——而猜错的那个数字，答得越快越有害。

NVIDIA Auto Ontology 的选择是把这层口径从 prompt 里搬出来，做成一层**可被人审核、可被版本化、只允许 agent 读取**的语义层，落在 Postgres 和 pgvector（Postgres 的向量扩展）里。它的 README 把问题说得很直白：一个营收指标答得再快，如果数字是错的就毫无价值。

有意思的是，这个项目真正的技术贡献不在 text-to-SQL（自然语言转 SQL）本身——那部分早有人做。它贡献的是两件更窄也更硬的东西：

1. **一套能让 agent 承认“这个问题我答不了”的机制**（`check_answerable` 与覆盖度评分），把拒答变成一等公民；
2. **一套 control / treatment 对照式的评测设计**（NVIDIA/auto-ontology-eval），让“语义层到底加了多少准确率”这个问题有个可测量的答案，而不是靠感觉。

不过认证这一环得打个折：它目前是**责任标记而非技术闸门**（下文细说），所以别把它当成“未认证的口径就自动失效”的保险栓。

截至 2026 年 11 月 10 日，这个仓库有 10960 stars、894 forks，Python 为主，Apache-2.0 许可，2026 年 4 月创建，11 月 5 日提交了 1.2.0 版本，11 月 9 日仍有提交。仓库明确写着**当前不接受外部 PR**。

## 系统地图

Auto Ontology 是一个六件套的部署栈，README 里列得很清楚：

| 组件 | 技术 | 职责 | 默认端口 |
|---|---|---|---|
| 前端 | Next.js 16、React 19、TypeScript、Tailwind 4、Better Auth、Prisma | Web UI、鉴权、公共 API 网关 | 3000 |
| 后端 | FastAPI（Python 3.12+）、LangChain | 文本转 SQL 智能体、目录与本体 API | 3001 |
| 摄取服务 | FastAPI（Python 3.12+） | 数据摄取与语义编译 | 3002 |
| MCP 服务 | FastMCP | 通过公共 API 暴露的只读智能体工具 | 3003 |
| Postgres + pgvector | PostgreSQL 17 | 目录、本体、应用数据、向量库 | 5432 |
| HashiCorp Vault | 可选 | 连接凭据存储 | — |

这套栈支持十种数据源引擎：PostgreSQL、MySQL、Databricks、Snowflake、ClickHouse、Trino、Apache Kyuubi、HeavyDB、DuckDB、SQLite。

部署有两条路：**Helm chart 装 Kubernetes**（官方安装方式，仓库有 `DEPLOYMENT.md`），或者 **Docker Compose 跑本地栈**。仓库里还有 `dev_tools/` 与 `docker-compose.yml` 两条开发路径。

快速上手用的是后者——README 的 Quickstart 拿 Microsoft 的销售样例库 Wide World Importers 跑完整流程：起 Postgres、灌样例数据、再 `docker compose up -d --build` 起全套。`.env` 里至少要填 `DEFAULT_MODELS_API_KEY`（`nvapi-...`，从 build.nvidia.com 取）、`AUTH_SECRET`、`APP_URL`、`POSTGRES_PASSWORD` 和 `AUTO_ONTOLOGY_ADMIN_PASSWORD`。README 特意提醒：Compose 会把 Postgres、pgAdmin 和 Web 应用都发布到宿主机上，**每个默认密码都要先换掉**。

还有一处容易踩的顺序问题：UI 加载完左导航栏就消失了，是浏览器存了过期的会话 cookie（`AUTH_SECRET` 变了或数据库重置都会触发），清掉 `localhost:3000` 的站点数据重新登录即可。

真正需要先记住的是**语义层里到底存了什么**。README 给的定义只有三类，但正是这三类构成了它与“向量库 + 表结构”的全部差别：

- **Terms（术语）**：业务概念，比如 *Customer*、*Invoice Line*，带描述与同义词，并映射到实际承载它的物理列；
- **SQL attributes（SQL 属性）**：挂在术语下、**经人工审阅过的 SQL 表达式**，比如毛利率、滚动汇总。智能体直接复用它们，于是同一个度量每次都按同一种算法算；
- **Relationships（关系）**：表之间如何 join，包括桥表（bridge tables），既从外键推断，也从数据本身推断。

Terms 管“这个词指什么”，SQL attributes 管“这个数怎么算”，Relationships 管“该往哪儿连”。只有第一类的话，本质上还是 RAG。

## 三阶段：编译、认证、回答

README 用一句话概括整个系统的工作方式：**生成本体、人来认证、agent 基于本体回答**。这个切分是理解全局的钥匙。

### 编译：机器先出一版草稿

摄取服务按四步走：

1. **读源**：抽取 schema、剖析列、把样本值写进目录；
2. **命名实体**：逐表抽取术语，把术语映射到列；
3. **解析关系**：推断表间 join 与桥表，并**从查询历史里建议 SQL 属性**；
4. **写本体**：术语、关系、SQL 属性落进 Postgres，嵌入向量进 pgvector。

结果是一张可以在 UI 里浏览的语义图。README 给了个具体数字：Wide World Importers 样例库一次编译产出 31 个术语；选中 *Order* 能看到它的描述、相关术语、映射到的列和 SQL 属性。

这一步有几个值得注意的工程细节，它们都写在源码里而不是文档里：

- `auto_ontology/semantic/compile.py` 里，语义编译把整段流程包在 `limit_inflight(SEMANTIC_LLM_MAX_INFLIGHT)` 里，默认并发上限 6。注释写明了原因：编译是表之间并行、表内再扇出，请求速率是乘积而非加和，很容易超过端点承载，之前撞上过 HTTP 503 ResourceExhausted。这个上限在编译期间单独生效，而不是放在共享的调用点上——否则连自己已经限流的调用方也会被一起压住。
- `semantic/deterministic.py` 里，列描述按每批 15 列切分（`_DESCRIPTION_BATCH_SIZE = 15`）。同样有注释：宽表会让模型在一次结构化输出里吐出一个包含所有列的 JSON，批次一大 token 就爆、就超时；分批后一个慢批次失败不会拖垮整张表的描述。

### 认证：让草稿变得可信

这一步没有自动化，因为它的意义就是**有人承担责任**：

1. 用真实问题在 Chat 里试，或者通过 MCP 调 `check_answerable` 与 `ask_question`；
2. 在 UI 或 API 里精修术语、描述与 SQL 属性；
3. 名称、描述、SQL 属性确认正确后，逐条认证。

认证完的内容才会被智能体当作可信口径复用。仓库还支持 Apache Ossie（语义模型交换开放标准）的双向导入导出（`Settings → Import / Export`，或 `POST /api/model/import` 与 `POST /api/model/export`），官方转换器在 `apache/ossie-converters` 仓库的 nvidia 目录下。

不过有个地方得说清楚，否则容易高估这层防护：`certified` 在当前实现里是**跟踪字段而不是准入闸门**。后端的 SQL 属性查询只把它投影出来，检索链路（`candidates_retrieval`、`sql_from_semantic`）里并没有按它过滤，语义编译的 system prompt 里也压根没提认证状态。所以未认证的属性照样会被智能体检索到。仓库自己的 management skill 写得更直接：“当前的认证字段不是一个原子的评审/晋级系统”，并要求在产品生命周期成型前**如实描述已评审状态，不要声称有原子的认证、晋级、取代或回滚**。

这不影响项目价值——认证的价值在于**给人一个明确的复核责任点和审计痕迹**，而不是技术上的强制拦截。但读者要是以为“不认证的条目智能体就用不了”，那就理解错了。

### 回答：一条有终止条件的状态机

回答链路由 LangGraph（LangChain 的状态图编排库）的 `StateGraph` 拼出来（`retrieval/text_to_sql/text_to_sql_graph.py`），节点包括意图分类、实体抽取、候选准备、候选检索、SQL 生成、解析校验、值校验、SQL 重建、结果为空时的值修复、证据精修、结果组装等一长串 agent。

其中最关键的两个常数是：

```python
# Stop after seven reconstruction calls.
MAX_RECONSTRUCTION_ATTEMPTS = 7
```

`route_sql_validation` 把每次校验结果分成三条路：`valid_sql` 执行、`invalid_sql` 重建、`unconstructable` 直接放弃。第三条是刻意留的——README 提到一个具体场景：数据库连不上时，任何重写 SQL 都救不回来，那种情况下继续重建只是烧 token，所以节点的判定结果会被原样透传，不被折叠进“还能修”那一支。

## 拒答：覆盖度检查是独立的一层

这是我认为这个项目最值得单独拿出来讲的设计。

`retrieval/entity_coverage/graph.py` 是一个独立的三节点图：

```
question_extraction → retrieve_candidates → coverage_grade → END
```

它回答的不是“这个问题怎么查”，而是“**这个数据集能不能回答这个问题**”。README 给了个很具体的例子：Wide World Importers 库里没有广告数据，于是问“这个商品的广告支出回报率是多少”时：

```text
Agent: check_answerable -> coverage 0.5; no term covers "ad spend"
Agent: 我能算出这个商品的营收，但这份数据里没有广告支出，所以算不出广告支出回报率。
       你想看 2015 年 6 月的营收吗？或者广告支出是不是在另一个我该接入的数据源里？
```

覆盖率 0.5 不是“置信度 50%”。源码里 `entity_coverage/agents/coverage.py` 的算法写得很直白——先按距离过滤检索命中，再算 **1/n entity coverage**：问题里抽出的实体中，有多少个被检索到的列属性命中覆盖到。0.5 就是“一半实体没找到对应定义”。这个数字把“我不知道”从一句自然语言变成了可被程序读取的结构化输出。

智能体的整体行为准则写进了 MCP server 的 instructions 里，顺序很讲究：`search_terms`（先弄清这里的业务词是什么意思，因为不同部署里“活跃客户”含义不同，不能靠猜）→ `check_answerable`（比 `ask_question` 便宜得多）→ `ask_question`（真正要答案时才用）。

还有一个容易被忽略的约束：**MCP 刻意不提供浏览数据库、schema、原始列的工具**。智能体只能对着术语表提问，不能绕过语义层直接翻表。README 的原话是——“问题是对着术语表回答的”。

## 任务流：两个真实问题

### 问题一：能回答的

> What was revenue for the USB food flash drive - sushi roll in Pennsylvania in June 2015?

回答附带完整 SQL 与推理步骤：

```text
Answer:  Revenue for USB food flash drive - sushi roll in Pennsylvania in
         June 2015 was $588.80, from 3 invoice lines.

SQL:     SELECT SUM(il.extendedprice) AS revenue, COUNT(*) AS invoice_lines
         FROM sales.invoicelines il
         JOIN sales.invoices i             ON il.invoiceid = i.invoiceid
         JOIN warehouse.stockitems si      ON il.stockitemid = si.stockitemid
         JOIN sales.customers c            ON i.customerid = c.customerid
         JOIN application.cities ct        ON c.deliverycityid = ct.cityid
         JOIN application.stateprovinces sp ON ct.stateprovinceid = sp.stateprovinceid
         WHERE si.stockitemname = 'USB food flash drive - sushi roll'
           AND sp.stateprovincename = 'Pennsylvania'
           AND i.invoicedate >= '2015-06-01' AND i.invoicedate < '2015-07-01'

Steps:   Resolved terms: Invoice Line (revenue), Stock Item, State Province, Invoice
         Joined: invoice line -> invoice -> customer -> city -> state province
         Validated the filter values against the data, then executed
```

三个动作值得注意：**术语解析**（把“revenue”落到 Invoice Line、把“state”落到 State Province）、**沿关系图推导 join 路径**（invoice line → invoice → customer → city → state province，agent 自己走关系，不需要人写 join）、**值校验**（把 Pennsylvania 这个过滤值拿去和数据比对，而不是直接塞进 SQL）。

结果里的 SQL 和 Steps 是可审计的——这是“答错了能追责”的前提。

### 问题二：不能回答的

同一份数据，问“这个商品的广告支出回报率是多少”。路径变成：`check_answerable` 给出 coverage 0.5 与“没有术语覆盖 ad spend”，agent 明确说明缺口并反问用户。**没有 SQL 被生成，没有数字被编造。**

## Benchmark：它到底测了什么

README 把 benchmark 放在一个单独的仓库里：NVIDIA/auto-ontology-eval（137 stars，25 forks，Apache-2.0），名字与主仓库 README 里给的链接指向同一处（`ontology-sql-eval` 会重定向过去）。

评测的核心设计是**对照**，而不是打分。同一批问题问同一个模型两次：

| 组 | 服务 | 模型拿到什么 |
|---|---|---|
| Control | `schema_only_sql` | 问题 + 一份 schema dump，塞在一个 prompt 里，无工具 |
| Treatment | `auto_ontology_sql` | 问题；Auto Ontology 的智能体自己去本体里检索上下文 |

两边产出的 SQL 和标准答案 SQL 会在同一个数据库上执行，然后比结果。每个数据集用官方规则打分：BIRD 系用 execution accuracy，BEAVER 用它自己的 `ex_acc`。**评分是确定性的，没有 LLM judge**——这点很关键，文本转 SQL 评测最容易被 LLM-as-judge 的随机性污染。

覆盖的数据集包括 BIRD（Dev 1534 题、Mini-Dev 500 题）、BEAVER（100 题 dw 样本）、FDABench-Lite（169 题）、Wide World Importers（41 题）、BIRD-Interact（Lite 约 300 题、Full 600 题，多轮）。

这个设计能支撑的结论是：**在同一个模型下，语义层相对“只给 schema”带来了多少准确率差**。它还输出被修复和被弄坏的题目列表，所以差异来自哪里是可查的。

不能直接推出的结论也有几条：

- **不能推出“Auto Ontology 比别的语义层产品好”**——对照组是 schema-only，不是竞品；
- **不能推出“某个模型在 Auto Ontology 上表现如何”**——两臂必须用同一个模型，README 反复强调这一点，否则测出来的是模型差异；
- **不能推出开了额外提示后的收益属于本体**——BIRD 的 SQL exemplars 与 value anchors 只喂给 treatment 臂，README 明确说“带着它们测出的差值同时包含了这些额外输入”，且这两项默认关闭（`--sql-examples-csv` / `--value-anchors-csv`）；
- **数字本身可能被健康检查拦下**——超过 5% 的题目没有模型输出，或任何一题缺结果，评测会**withhold 它的头号数字**。这是个好设计：限流跑挂了的分和弱模型的分开跑长得几乎一样。

## 治理代价：三处必须先看

这是我认为评估这个项目时最容易被略过、但恰恰最该先看的部分。

**MCP 是只读的，写操作走 Next.js 的 `/api/...` 面**——这是有意的边界设计，但意味着“谁能改语义层”和“谁能读语义层”是两套权限。

**开启 KumoRFM 会把数据传出去**。设置 `KUMO_RFM_API_KEY` 后，预测类问题会被路由到 KumoRFM 这个托管服务：回答需要把接入的表上传过去，默认上限 `KUMO_MAX_TABLES` 为 20 张，`KUMO_MAX_ROWS_PER_TABLE` 不设则不限。README 自己写了一句——“看看这会发送什么，并在启用前完成你们组织的数据审查”。

**凭据落点取决于有没有配 Vault**。不配 Vault 时，完整的连接对象（**包括密码**）会被序列化进 JSON，明文存在 Postgres 的目录行上；配了 Vault 才只存引用、以数据库名为查找键。

还有一条部署要求：**3001 和 3002 端口必须留在内网**。因为 FastAPI 信任前端转发过来的 `x-auto-ontology-user-id` 头，而摄取服务的 ingest / delete / reset / compile 端点**自身没有任何鉴权**——客户端统一走 3000 端口的 Web 应用进来。

Vault 的启用条件比想象中严格：必须**同时**设齐 `VAULT_ADDR`、`VAULT_NAMESPACE`、`VAULT_ROLE_ID`、`VAULT_SECRET_ID` 四个变量，Vault 才算开启。只配一部分会被忽略并给出警告，然后**静默退回明文存储**。这种“半配置即等于没配”的失败模式，值得在部署检查单里单列一条。

## 排查：五个会绊住你的点

仓库的 setup skill 里带了一份排障文档，以下几条是最容易撞上的。

**问不出东西（`ask_question` 返回空，且没有 SQL 也没有错误）**。先调 `check_readiness`。最常见的原因是根本没配数据库连接——但要注意，`databases` 列表非空并不能证明 SQL 能跑：**目录活得比它被摄取时的那条连接更久**。部署正常的话，剩下的问题就是问题的词汇不对，用 `search_terms` 查问题里的名词。

**提示“Auto Ontology cannot answer right now”**。通常是语义层压根没编译过，用 `check_readiness` 或 `GET /api/semantic-compilation/status` 确认；另一个原因是同一个 `conversation_id` 已有对话在跑（返回 409）。

**嵌入看起来是空的，或者摄取与查询结果对不上**。`EMBED_ENDPOINT` 和 `EMBED_MODEL` **必须在摄取和查询两侧完全一致**——不一致会让存量向量和查询向量落在不同空间里，表现出来就是“什么都找不到”。注意 `.env` 里 `EMBED` 三元组如果没设，会回退到 `DEFAULT_MODELS_MODEL`（那个聊天模型），所以要显式写死。

**MCP 客户端看不到任何工具**。先看客户端的 MCP 日志，服务端日志走 stderr；确认客户端 URL 带 `/mcp` 后缀，并且改完配置后**重启过客户端**。

**登录之后报 “Protected resource ... does not match expected”**。MCP server 广播的是它绑定的地址，而客户端用了同一部主机的另一种写法——几乎总是 `127.0.0.1` 与 `localhost` 的差别。把 `AUTO_ONTOLOGY_MCP_PUBLIC_URL` 设成客户端实际使用的那个 URL，或者干脆不设 `AUTO_ONTOLOGY_MCP_HOST`。

另外，**MCP 登录相关的表在 Prisma 的 `frontend` schema 里**，由 `frontend-migrate` 这个 job 同步，不在后端自己的 `auto-ontology-migrate` 里。这个 job 即使退出码为 0，也可能没干完活就把 MCP 登录搞坏——所以要看它的日志，而不只是看退出码。

## 采用建议

**适合先上**：口径混乱、多人共用同一套数、并且已经在为“agent 答错数”付代价的团队。先挑一个主题域（比如订单或收入）跑通编译—认证闭环，而不是一上来全库铺开。认证环节是人力成本的大头，README 把术语、描述和 SQL 属性的认证写成了显式步骤而不是自动流程，就是这个原因。
**适合搭配**：已有 MCP 客户端的智能体系统。服务端只暴露只读工具，客户端零配置接入，用户在 Auto Ontology 自己的登录页完成鉴权，权限每次调用都按账号实时判定——改角色、封号、删授权立刻生效。

**可以等等**：数据量小、口径本来就统一、或者只需要跑固定几个查询的场景。整条链路的部署复杂度（六个组件、私有端口、无 Vault 的明文密码）在那类场景里不划算。

**不推荐**：直接把 KumoRFM 打开当默认配置。数据外传这件事应该单独过一次审查，而不是顺手配个 key 了事。

## 结尾判断

Auto Ontology 的价值不在于把 text-to-SQL 做得更准，而在于把**“什么算对”这件事从模型内部搬到了数据库里，并且要求人来签字**。术语、认证过的 SQL 属性、以及覆盖度检查，这三样东西共同构成了它的护栏；其中任何一环松掉，它就退化成又一个“把 schema 塞进 prompt”的东西。

对正在评估“要不要让 agent 直接查生产库”的团队，它真正提供的是一个可讨论的中间答案：不是全信模型，也不是全靠人写报表，而是把口径固化下来、让人认证、让 agent 在覆盖范围内提问、并且在覆盖范围外明确说“答不了”。

下一步如果要看它值不值得上，建议先跑 NVIDIA/auto-ontology-eval 的 Wide World Importers 那 41 题——41 题、确定性打分、附带差异题目列表，成本低到可以当内部基准用，然后用自己的真实问题替换掉样例，再看差值还剩多少。
