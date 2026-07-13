---
title: "Google Cloud Knowledge Catalog：一个面向代理式 AI 的结构化数据与模型上下文目录"
date: 2026-07-14T03:13:50+08:00
slug: "googlecloudplatform-knowledge-catalog-structured-data-agentic-discovery"
description: "Knowledge Catalog 是 Google Cloud 推出的 AI 驱动数据目录（前身 Dataplex），配套仓库提供官方 SDK、Discovery Agent 与实验性质的 Open Knowledge Format（OKF）规范。本文从仓库内容出发，拆解它的定位、已发布的工具与样本、以及 OKF 这套新人机通用知识表示的边界。"
draft: false
categories: ["技术笔记"]
tags: ["Google Cloud", "Knowledge Catalog", "Dataplex", "AI Agent", "Open Knowledge Format"]
---

# Google Cloud Knowledge Catalog：一个面向代理式 AI 的结构化数据与模型上下文目录

> **目标读者**：负责把企业数据接入 AI Agent / RAG（Retrieval-Augmented Generation，检索增强生成）系统的数据工程师、平台架构师，以及对模型上下文协议（MCP，Model Context Protocol）和代理式 AI（Agentic AI）生态感兴趣的从业者
> **预计阅读时间**：18-22 分钟
> **前置知识**：了解 Google Cloud 基本术语（BigQuery、AlloyDB、Vertex AI），熟悉 Python 与 LangChain / Google ADK 等 Agent 框架的基本概念
> **适用版本**：仓库 master 分支（README、`okf/SPEC.md` 与 `samples/*` 截止 2026-07-13 的内容）

读完这篇，你应该能回答这几个问题：

- Knowledge Catalog 这套 Google Cloud 服务和它背后的开源仓库到底是什么关系？
- 它现在能交付的能力里，哪些是稳定可用的，哪些仍然在快速变化？
- `okf/SPEC.md` 描述的 Open Knowledge Format（OKF）到底是个新格式、还是另一种 markdown 工具？
- `samples/discovery` 跑的 Discovery Agent 与 `samples/enrichment` 提供的 enrichment 工具，二者在上下文层各负责什么？
- 现在是否值得在生产环境里接它，还是先观望一段时间？

阅读建议：先把"项目定位 → 已验证信号 → 风险与未知项 → 适用人群"读懂，勾勒出仓库轮廓；再按需回到具体模块做技术细节阅读。

---

## 项目定位

知识目录（Knowledge Catalog，代号层面紧随原 Dataplex 改名而来）不是一套新的数据库或 ETL 工具，而是 Google Cloud 在 2025-2026 年间把 Dataplex 重新包装成"AI Agent 的统一上下文层"后对外的产品。仓库地址 [github.com/GoogleCloudPlatform/knowledge-catalog](https://github.com/GoogleCloudPlatform/knowledge-catalog) 自述："Knowledge Catalog (formerly Dataplex), is an AI-powered data catalog and metadata management platform. It provides a dynamic knowledge graph of all your data, structured and unstructured, to provide semantics and business context to AI agents. This repository features tools, agents, and samples that demonstrate Knowledge Catalog features, and building context management, enrichment and retrieval solutions."

读这一段要把握两个关键点：

- **它不是底座（foundation）而是中间层（context layer）**。底层 BigQuery / AlloyDB / Spanner / Cloud SQL / Firestore / Looker 继续各管各的。Knowledge Catalog 不替代它们，而是把它们的元数据和技术 schema 拉过来、再加上"业务语义"，统一暴露给 AI Agent。
- **配套仓库是 sample + SDK + 实验性规范三件套**，不是服务自身。服务本体托管在 GCP 控制台，开源仓库更多是用来展示 SDK 调用方式、原型 Agent 和一个正在孵化的 OKF 规范。

仓库当前 Star 数 6858、Forks 562（GitHub API 实时数据），主要语言按占比记为 HTML（含诸多文档与示例应用），Apollo 项目根级 license 是 Apache-2.0。最近一次提交时间是 2026-07-13，main 分支根目录为 `okf/`（Open Knowledge Format 实验性子项目）、`samples/`（使用示例）、`toolbox/`（可独立复用的工具集）三个目录。repository size 约 876 KB——比正常 Python SDK 仓库轻得多，因为生产化服务本身不在开源范围内。

从产品路线图的角度看，Google Cloud Knowledge Catalog 的官方页（[https://cloud.google.com/products/knowledge-catalog](https://cloud.google.com/products/knowledge-catalog)）把它定位成 "universal context engine for your enterprise, helping agents execute complex tasks with accuracy"，核心主张有四点：

- **自动数据治理（Automated governance）**：在 BigQuery / AlloyDB / Spanner / Cloud SQL / Firestore（Preview）/ Looker（Preview）等底座上自动采集 technical metadata；
- **持续学习式 enrichment**：通过 Gemini 抽取非结构化实体、构建业务语言层（natural language glossaries）和 SQL 模式（SQL patterns）作为"golden queries"；
- **语义搜索 + 子秒延迟检索**：让 Agent 能拿到权限内可见、上下文足够准确的 catalog 结果；
- **可量化的上下文评估（evaluation）框架**：用于持续优化喂给 Agent 的上下文质量。

配套开源仓库对应三个交付面：

| 仓库目录 | 角色 | 状态 |
|---------|------|------|
| `samples/discovery` | Discovery Agent：调用 Knowledge Catalog 的语义搜索能力，做多查询 + 重排序 | 较稳定，可在本机 ADK CLI 跑通 |
| `samples/enrichment` | Enrichment Agent：根据用户问句给 catalog 写入更丰富的 metadata | 较稳定，但输出格式在不同时期有差异 |
| `toolbox/mdcode` | "Metadata as Code"：把 metadata 用源码方式管理与同步 | 较稳定，是仓库里工程化程度最高的一块 |
| `toolbox/enrichment` | 一个可定制的 harness，让团队自己包装 enrichment 流程 | 较新，可能仍有 API 调整 |
| `okf/` | Open Knowledge Format 规范与 proof-of-concept Agent + 可视化器 | 实验性（仓库自述 "proof of concept"） |

`README.md` 末尾留了一句话："This repository and its contents are not an official Google product."——所以从治理级别看，仓库是 GCP 团队主导、但 release 与稳定性按 sample 级别处理，不应当作 enterprise-support 等价物来用。

## 目录

- [目录](#目录)
- [项目定位](#项目定位)
- [仓库构成](#仓库构成)
- [已验证信号](#已验证信号)
- [核心机制拆解：Discovery 与 Enrichment 两条主线](#核心机制拆解：discovery-与-enrichment-两条主线)
- [Open Knowledge Format（OKF）：一个想成为 Markdown-of-Knowledge 的实验](#open-knowledge-format（okf）：一个想成为-markdown-of-knowledge-的实验)
- [风险与未知项](#风险与未知项)
- [适用人群](#适用人群)
- [常见翻车现场](#常见翻车现场)
- [常见问题](#常见问题)
- [总结](#总结)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [项目资源](#项目资源)

---

## 仓库构成

把仓库根级目录拉出来对照 README，可以看清"哪些是产品示例，哪些是规范孵化"。

| 目录/文件 | 作用 | 维护方 |
|----------|------|--------|
| `README.md` | 仓库定位、Getting Started、Cloud Shell 入口 | Google Cloud Knowledge Catalog 团队 |
| `CONTRIBUTING.md` | CLA、PR 流程 | 同上 |
| `LICENSE.md` | Apache-2.0 全仓库条款 | 同上 |
| `CODE_OF_CONDUCT.md` | 社区行为准则 | 同上 |
| `okf/` | Open Knowledge Format 规范、Python 实现、bundles 可视化 | 实验性子项目 |
| `samples/discovery` | Discovery Agent（ADK 风格）+ `tools.py` 包装 Knowledge Catalog API | sample 维护 |
| `samples/enrichment` | Enrichment Agent 的最小可运行样例 | sample 维护 |
| `toolbox/mdcode` | Metadata as Code 工具集，把 metadata 当源码管理 | 工程化工具 |
| `toolbox/enrichment` | 用户可定制的 enrichment harness | 实验性工具 |

值得注意的是 `okf/` 子项目内有自己的 `pyproject.toml`、`tests/`、`bundles/`（已预生成三个参考 bundle：GA4 / Stack Overflow / Bitcoin block 数据）、`samples/` 与 `src/`。它的存在意味着 Knowledge Catalog 团队在开源仓库里养了一条独立规范线，OKF 与底下的 Knowledge Catalog 服务是松绑的——可以单独用 OKF 而不接 GCP 服务，这点对不想立刻绑定云的团队很关键。

## 已验证信号

仓库里能直接验证、文档里也明确写了的能力有 6 条。下面每一条都给出出处与可观察行为。

### 1. Discovery Agent 的可运行样例

`samples/discovery/` 是一个以 Google ADK CLI 形式跑的 Agent。它的入口在 `agent.py`：

- Prerequisites 明确列出了三个 API：`dataplex.googleapis.com`（Knowledge Catalog）、`aiplatform.googleapis.com`（Vertex AI）、`serviceusage.googleapis.com`（Service Usage），以及三组 IAM（Identity and Access Management）权限（`dataplex.projects.search`、`aiplatform.endpoints.predict`、`serviceusage.services.use`）。
- `tools.py` 暴露 `knowledge_catalog_search(query: str) -> dict`，内部调用 `dataplex_v1.CatalogServiceClient` 向 `dataplex.googleapis.com:searchEntries` 发请求，再把结果包装成字典。
- `SKILL.md` 是给 ADK 框架读的 skill description，描述 Agent 能力。

这意味着两点：第一，Discovery Agent 不是 demo，是真的跑在生产 IAM 路径上；第二，Knowledge Catalog 当前对外暴露的搜索接口是 `searchEntries`，调用者只需要 dataplex viewer + aiplatform user 这两个相对基础的 role。这一行代码确认了仓库在 Knowledge Catalog 公开 API 上的最小可观察面。

### 2. Enrichment Agent 样本链路

`samples/enrichment/` 提供的 Enrichment Agent 不是单纯的产物展示，而是可启动的 harness。它的 README 直接指向 `toolbox/enrichment`，后者作为一个独立 Python 包存在，封装了"用 Agent 跑 enrichment 流程"的模板。仓库把这一块作为"团队快速构造自家 enrichment 流程"的脚手架。

注意：仓库 README 的 disclaimer（"not an official Google product"）意味着这一块按 sample 维护，schema 变动可能在不通知的情况下发生。

### 3. "Metadata as Code"工具

`toolbox/mdcode/` 是仓库里工程化最完整的一块，按 README 描述提供"manage metadata in the form of source code artifacts that can be sync'd with metadata in Knowledge Catalog"。

这条信号的关键不在工具本身，而在它所暗示的设计取向：Knowledge Catalog 的 metadata 不是锁死在管控台里的 DB row，而是可以被纳入 CI / PR 流程的源代码。这与 OKF 的设计哲学高度一致（下面单独拆），意味着 GCP 团队把"metadata as code"作为长期路线。

### 4. OKF 已发布 `SPEC.md v0.1` 与三份参考 bundle

`okf/SPEC.md` 明确写明 "Version 0.1 — Draft"。`okf/bundles/` 里已经预生成 GA4、Stack Overflow、Bitcoin 三份示例 bundle，每份都有一个可双击打开的 `viz.html` 文件浏览知识图谱。

这意味着 OKF 已不是"只有规范"的纸面草案，而是有可执行转换器（`okf/src/` 的 Python 包）和可视化的端到端演示。这点在评估时很关键——多数知识表示格式还停留在白皮书阶段，OKF 已经能让人看完一整个 GA4 电商数据的目录图。

### 5. Cloud Shell 一键拉起入口

README 顶部那个 "Open in Cloud Shell" 按钮指向 `https://console.cloud.google.com/cloudshell/editor?cloudshell_git_repo=...knowledge-catalog.git`。这意味着 GCP 把仓库 clone + 起步这个步骤做成了 zero-setup。这一项虽然不算技术能力，但说明了官方对"开发者上手时间"的优先级。

### 6. 第三方集成白名单

GCP 官方页面列出的合作集成包括 Ab Initio、Anomalo、Atlan、Collibra、Datahub——这是 catalog 系统通常会对外公布的 partner list。它意味着：就算企业已经有了 Unity Catalog / Collibra 类工具，Knowledge Catalog 在产品层面承诺能接入这些系统作为 source of truth。这一点对评估"是否要扔掉已有 catalog"很关键。

## 核心机制拆解：Discovery 与 Enrichment 两条主线

仓库的 sample 表面看是两个独立 Agent，骨子里是同一条价值链的两端：Discovery 是"读完 catalog 给 Agent 用"，Enrichment 是"往 catalog 里写更多高质量 metadata"。下面把这两条线的具体动作拆开。

### Discovery：把"问 catalog"封装成 Agent 工具

`samples/discovery/tools.py` 暴露的 `knowledge_catalog_search(query)` 是把一次语义搜索压成单个工具：

1. 通过 `dataplex_v1.CatalogServiceClient` 创建 catalog 客户端，endpoint 指向 `dataplex.googleapis.com`；
2. 用 `projects/{project}/locations/global` 作为 `parent_name`；
3. 调 `search_entries(request={"name": parent_name, ...})`，这是 Knowledge Catalog 在 GCP 上的 public API；
4. 把响应里 entries 的 `name`/`system` 等字段包装成 `{'results': [...]}` 返回。

Discovery Agent（`agent.py` 里声明的 `discovery_agent`）可以以 `root_agent` 形态跑在 ADK CLI 上，也可以以 `AgentTool` 形式嵌入更大的 multi-agent 系统（README 引用的官方文档 [adk.dev/agents/multi-agents](https://adk.dev/agents/multi-agents) 给出了标准模式）。这条路径把 Knowledge Catalog 暴露成一个标准 MCP 工具，对接 LangChain / ADK / 自研 Agent 都自然。

需要注意的边界：当前 sample 演示的"multi-query generation + reranking"能力（即 README 关于"semantic decomposition of complex questions"的描述），具体实现并不在 `tools.py` 这一薄层里，而是依赖上层 Agent 自身的链路。仓库只保证"Knowledge Catalog 搜索 API 可被工具化"，并不保证所有 Agent 框架的 multi-step 行为对最终用户一致。

### Enrichment：从 LLM 灌出 metadata 并回写到 catalog

`samples/enrichment/` 与 `toolbox/enrichment/` 是同一件事的两个层次：

- `samples/enrichment` 给出最小可跑入口，强调"如何用 LLM 给 catalog 添业务 metadata"；
- `toolbox/enrichment` 是一个可被复制的 harness，团队可以基于它定制自己的 enrichment 流程（在 sample 这一层之上加更多 LangChain / ADK 步骤、加上 review 等）。

回写端是怎么完成的？仓库 README 与 SPEC 都没有给完整 PoC 代码到"实际调 writeEntries API"的级别。`toolbox/enrichment/README.md` 提到该工具用于"produce, evolve/improve and maintain metadata within Knowledge Catalog"。结合 GCP 官方页"Smart Storage and Object Context APIs auto-tag and embed files"的表述，可以判断：完整 enrichment 的回写路径在 Google Cloud 私有 API 上，sample 仓库只演示 Agent 部分，写入端的 RPC 由服务本身处理。

### 两条主线协同起来的角色

把两条主线按上下文层视角摆一下：

- **数据层（Data Plane）** BigQuery / AlloyDB / Spanner / Cloud SQL / Firestore / Looker 存真实数据。
- **元数据/语义层（Context Plane）** Knowledge Catalog 自动 harvesting technical metadata，Enrichment 给它贴业务标签、生成 natural language glossaries 与 verified queries。
- **检索层（Retrieval Plane）** Discovery Agent / 自建 RAG 用 `searchEntries` + Gemini reranker 得到合用上下文。
- **Agent 层（Consumption Plane）** 任何接 ADK / LangChain 的 agent 用 MCP 工具形态调 Discovery Agent 取得上下文。

OKF 想把这四层中"语义层"以可移植的 markdown 形态抽出来，下面单独拆。

## Open Knowledge Format（OKF）：一个想成为 Markdown-of-Knowledge 的实验

仓库里最不像"实验性"的一块，是 `okf/` 子项目。它有自己的规范（`SPEC.md`）、Python 实现（`pyproject.toml`、`src/`、`tests/`）、proof-of-concept Agent、和三份参考 bundle。SPEC 自我定位写得非常直接：

> "A universal, vendor-neutral format for representing knowledge as plain markdown files with YAML frontmatter. It is not tied to any particular agent, framework, model provider, or serving system."

### 设计取向

`okf/README.md` 总结出来 7 条特性，可以归纳成两类决策：

- **"知识应该是文件"路线**：OKF 用 `markdown + YAML frontmatter` 当容器。这一选择让它天然 git-diffable、cat-able、与既有 markdown 工具生态（Obsidian / Hugo / Jekyll / MkDocs / Notion）兼容。
- **"轻 schema、强组合"路线**：spec 只规定极小的 required keys（如 concept id、type 等），其余字段 free-form；bundles 用 `index.md` 自动产生层级，让 Agent 不一次性把全表塞进 context。

这两条选择不是新发明，而是延续 Hugo / Jekyll 等静态站点范式推到了"知识图谱"形态。SPEC 把 representation 推到 vendor-neutral，也意味着 OKF bundle 能从 Dataplex / Unity Catalog / Collibra 双向导出。

### OKF 的关键概念

- **Knowledge Bundle**：一组 markdown 文件组成的 self-contained 知识目录，是发行单位。
- **Concept**：bundle 里的一个 markdown 文件，可以是具体资产（表、API）也可以是抽象（一个 metric、一段业务流程）。
- **Concept ID**：去掉 `.md` 后缀的文件路径。

这一组定义是 SPEC v0.1 全文最重要的部分——它把"目录条目（catalog entry）"与"文件路径"绑成同一概念，这是 OKF 能用 markdown 生态做事的关键。

### Proof-of-concept 与 bundles

`okf/bundles/` 预生成三份 demo：

| Bundle | 描述 | 可视化入口 |
|--------|------|------------|
| `ga4` | GA4 电商数据集 | `bundles/ga4/viz.html` |
| `stackoverflow` | Stack Overflow 公开数据集 | `bundles/stackoverflow/viz.html` |
| `crypto_bitcoin` | Bitcoin 区块/交易数据 | `bundles/crypto_bitcoin/viz.html` |

这些 bundle 都是 agent "production"出来的样本（README 明示），用来让评审者快速感受到"OKF 长什么样"。它们不是生产数据。

### OKF 与 Knowledge Catalog 的关系

把这两件事合起来：OKF 是 Knowledge Catalog 的导出格式之一，但 OKF 不绑定 Knowledge Catalog。在仓库里 OKF 是 PoC 阶段，成熟度低于 `samples/*`。如果你的团队只想做"把 metadata 当代码管理"，OKF bundle 本身是单点可用的；如果要接 Knowledge Catalog 服务本身，要评估 GCP 私域 SLA。

## 风险与未知项

按"项目导读 + 实验性评估"的形态要求，必须把不确定的部分事先标出来。下面是值得留意的 7 项。

### 1. 仓库 disclaimer 明文写"非官方 Google product"

README 的最后一句明确："This repository and its contents are not an official Google product."这意味着 SLA / support 渠道按 community 走，sample 代码可能在无人通知下做 breaking change。

### 2. OKF 处于 v0.1 Draft 状态

SPEC 自己标注 "Draft"。`bundles/` 只给了三份参考，schema 变动风险显著。任何生产集成都应在仓库外保留自己兼容层。

### 3. Discovery Agent 与上层 Agent 框架的耦合点有限证据

仓库没有完整的 benchmark 数据（如检索准确率、p50/p99 延迟、成本曲线）。`tools.py` 里能看到搜索 RPC 的最小封装，但 README 中关于"semantic decomposition of complex questions, generating multiple relevant search queries, and reranking"的描述，分布在哪个 prompt 模板、哪种 reranker 模型上仍不清晰。

### 4. Enrichment 回写到 Knowledge Catalog 的端到端示例未公开

`samples/enrichment` 演示了"Agent 怎么生成 metadata"，但"最后写回 catalog"的 RPC 不是 sample 可见。这条对希望做端到端自动化的团队是一道坎——他们必须自己摸索或等官方 SDK 升级。

### 5. 第三方 catalog 集成是单向还是双向？

GCP 官方页列出 Ab Initio、Anomalo、Atlan、Collibra、Datahub 等 partner，但仓库里没看到具体 connector 代码。双向同步的延迟、冲突解决策略、权限继承在 README 中没有写明。

### 6. knowledge-catalog vs 原 Dataplex 命名的连续性

官方页写"formerly Dataplex"，但仓库 README 与 cloud SDK（`dataplex_v1`）在 import 路径上仍保留旧名。这影响短期内的代码与文档对齐——团队在迁移时需要在两个名字之间切换。

### 7. 仓库主要语言被 GitHub 标记为 HTML

这表明 GitHub 视角下"主要语言"由仓库内 HTML 文档占比决定，而不是 Python 或 TypeScript。这会影响 star/fork 数量上的体感，但与运行能力无关；只是看到 star 数时要警惕"这个仓库代码占比不高"的现实。

## 适用人群

上面这些信号合起来，哪些团队值得接，哪些团队更应该观望？

### 适合现在或半年内尝试

- **已经在 GCP 落地 + 数据分散在 BigQuery/AlloyDB/Spanner 的大中型企业数据平台团队**。Knowledge Catalog 的 harvesting 直接省掉他们自建 metadata pipeline 的时间成本。
- **正在做 multi-agent 系统的工程团队**，且需要"给 Agent 喂 catalog 上下文"能力，OKF + Discovery Agent 是相对成熟的入口；至少拿来做 PoC，不需要立刻锁定 vendor。
- **希望用 Markdown 管理 metadata 的小团队或个人**。OKF bundle 与 `toolbox/mdcode` 提供了一条无需绑定 GCP 的路径。

### 适合保持观望

- **已经在用 Collibra / Unity Catalog 等成熟 catalog 的企业**。这些生态体量、connector 数量、长期支持模式都比 Knowledge Catalog 仓库样本大；观望 OKF 与 connector 进展再做迁移决策更稳妥。
- **非 GCP 优先的公司**。当前 Discovery Agent 的 RPC endpoint 是 `dataplex.googleapis.com`，跨云私有网络访问通常要付额外 egress 成本。除非你愿意把数据迁到 GCP，否则收益可能不及预期。
- **把 repository 当 production SDK 用的下游消费者**。disclaimer + sample 维护节奏意味着重大变更不保证 backward compatibility，做 dependency 时要绑版本号并保留 lockfile。

### 不适合

- **想要"一键 metadata catalog 投入生产"的轻量需求**。Knowledge Catalog 是一个企业级系统，运维 metadata catalog 不像读 README 那么简单。如果只想要"查询表结构"，直接用 BigQuery INFORMATION_SCHEMA 更划算。
- **强实时同步需求**。Knowledge Catalog 的 harvesting 是周期性 + 触发式混合，目前未在 sample 仓库中提供 webhook 形态的实时回写。

## 常见翻车现场

把团队接 Knowledge Catalog 仓库时最容易踩的坑列一下，遇到类似症状时可以从这里起手。

### 翻车 1：Discovery Agent 跑通但 search 结果空

- **症状**：ADK CLI 启动 Agent，问 "What tables do I have in BigQuery?"，返回 `{"results": []}` 或报 IAM error。
- **原因**：消费者项目（consumer project）权限或 Knowledge Catalog 实际开启状态未对齐；`samples/discovery/tools.py` 的 `get_consumer_project` 用环境变量推断。
- **修法**：确认 `GOOGLE_CLOUD_PROJECT` 变量已设置且该 project 已 enable `dataplex.googleapis.com`，被查询方已给 `roles/dataplex.viewer`。

### 翻车 2：Enrichment 输出不稳定

- **症状**：同一条业务问句两次跑 enrichment，生成 metadata 字段结构不一致。
- **原因**：enrichment agent 行为强烈依赖于 prompt 模板，仓库 sample 默认 prompt 在 LLM 模型版本变化下会有 schema drift。
- **修法**：固定上游 Gemini 模型版本、把 prompt 模板挪到仓库里加单测；写入 catalog 时用 schema 强校验兜底。

### 翻车 3：OKF bundle 转出与原 catalog 字段对不上

- **症状**：用 OKF 导出某个 catalog，运行后某些字段（`tags`、`timestamp`）丢。
- **原因**：OKF 把字段拆成 required keys + extra frontmatter；extra keys 在 export 路径上可能被工具悄悄丢弃。
- **修法**：在 export 工具调用前先 enumerate 字段，做出 diff report；保留一份"原始 catalog → OKF bundle → 原始 catalog" round-trip 集成测试。

### 翻车 4：把 sample 直接当成库依赖

- **症状**：`pip install google-cloud-knowledge-catalog`（不存在），或者错装某 sample 的源码包。
- **原因**：仓库并没有 publish 一个顶层 production-ready Python package；sample 目录是可独立 pip install 的脚本，OKF 子项目有 `pyproject.toml` 但功能范围较窄。
- **修法**：只把 OKF 与 sample 当 template；正式生产代码用 [`google-cloud-dataplex`](https://pypi.org/project/google-cloud-dataplex/) SDK，仓库做参考。

## 常见问题

**Q：knowledge-catalog 仓库和 google-cloud-dataplex 是什么关系？**
A：Google Cloud 的产品现在叫 Knowledge Catalog，但底层 API 沿用旧名 `google.cloud.dataplex_v1`。仓库 sample 沿用 `dataplex_v1` import，因为它调用的是公开 API。命名迁移尚未完成所有文档和 SDK 命名。

**Q：Discovery Agent 一定要用 Google ADK 吗？**
A：sample 默认是 ADK 风格，但 `tools.py` 里只暴露了普通 Python 函数，可以被 LangChain / 自研 Agent 通过"包装普通函数到 tool"流程复用；OKF 也可以被任何 agent 加载。

**Q：OKF 是 OMG 之类标准化组织的草案吗？**
A：不是。`okf/SPEC.md` 是 GCP 团队起的 vendor-neutral 格式草案，没有标注 ISO/W3C 等标准化组织背景。SPEC version 0.1 — Draft。

**Q：如何从仓库 sample 升级到生产？**
A：仓库本身不能直接读。建议把 sample 当参考实现，落到标准 SDK `google-cloud-dataplex`、自有 MCP 工具包装，加上自己的 evaluation harness。这一步把仓库 sample 的不确定性与生产代码解耦。

**Q：Knowledge Catalog 的 retrieval 延迟是多少？**
A：官方页 headline 是"sub-second"，但 sample 没有给出具体 benchmark。生产前应自己跑一遍：`searchEntries` RPC 延迟、Agent 多跳 + reranker 总延迟，端到端发到 Claude / GPT 之后的 cost 都要自测。

**Q：第三方集成（Atlan / Collibra 等）能同写吗？**
A：官方页只确认 Knowledge Catalog 支持读取这些来源。bidirectional sync 与冲突解决策略需要看具体 connector 实现——目前样本仓库里没有 reference code。

## 总结

把全文最核心的判断整理成三句话：

- **仓库角色**：Knowledge Catalog 是产品名、Dataplex 是 API 沿用名，仓库是 sample + OKF 实验性子项目混合体；不是 enterprise SDK 也不仅是一个 demo。
- **可验证信号**：Discovery Agent 有可调 RPC（`dataplex_v1.CatalogServiceClient.searchEntries`）；Enrichment 与 mdcode 是工程化雏形；OKF 是带 bundles 的 v0.1 Draft 规范。
- **适用与不适合**：已经在 GCP 中重度落地的数据团队值得现在就接入做 PoC；用其它 catalog 的企业应继续观望；需要 vendor-neutral 知识表示的小团队可以直接拿 OKF 起手。

配套开源仓库现在的成熟度，按"读 README → clone 跑 sample → 接入 PoC → 上生产"分四档：前三档都可以做，最后一档需要自建工程层，不要把仓库 sample 当 enterprise SDK 的等价物。

## 自测题

1. Knowledge Catalog 的"formerly Dataplex"重命名对你写代码有何影响？请至少列出两条具体措施。
2. 给一个 multi-agent 系统装上 Discovery Agent 之前，至少应该准备哪些 IAM 权限？针对这些权限的最小 role 是什么？
3. OKF 把 knowledge 表示成 markdown + YAML frontmatter，这一选择带来的最少 3 个收益与 2 个代价是什么？
4. `samples/discovery` 与 `samples/enrichment` 在上下文层各有哪一段职责？如果缺失其中一段，上下文链路会断在哪？
5. 仓库 README 末尾的 disclaimer 在评估 SLA 时意味着什么？这对下游 production 依赖有哪两条具体工程动作？

## 进阶路径

- **Open Knowledge Format 规范文档**：`okf/SPEC.md`（v0.1 Draft）。把它当 RFC 来读，再决定是否纳入项目依赖。
- **Google Cloud `google-cloud-dataplex` SDK**：使用 API 的官方路径，[pypi](https://pypi.org/project/google-cloud-dataplex/)。
- **MCP / ADK Agent Tool 模板**：把 `samples/discovery/tools.py` 包装成 MCP tool 或 ADK AgentTool，让它能在 Claude / GPT-based agent 框架里复用。
- **Atlan / Collibra 对接现状**：Atlan 的 [Google Cloud Knowledge Catalog connector](https://atlan.com/) 与 Collibra 的官方目录管理页面可以跟进，但任一个当下都不保证双向 sync 完整。
- **Dataplex 历史文档**：原 Dataplex 文档站仍有大量可用材料，理解背景能更好理解 Knowledge Catalog 的迁移选择。

## 项目资源

- 仓库：[github.com/GoogleCloudPlatform/knowledge-catalog](https://github.com/GoogleCloudPlatform/knowledge-catalog)
- 产品主页：[cloud.google.com/products/knowledge-catalog](https://cloud.google.com/products/knowledge-catalog)
- 发布与博客：[cloud.google.com/products/knowledge-catalog](https://cloud.google.com/products/knowledge-catalog) 页底 "What's new"
- Cloud Shell 一键入口：仓库 README 顶部 `Open in Cloud Shell` 按钮
- OKF 规范：[okf/SPEC.md](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
- Discovery Agent sample：[samples/discovery/README.md](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/samples/discovery/README.md)
- Enrichment sample：[toolbox/enrichment/README.md](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/toolbox/enrichment/README.md)
- License：Apache-2.0（[LICENSE.md](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/LICENSE.md)）
