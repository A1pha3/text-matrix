---
title: "wigolo 架构深潜：从 Agent Loop 状态机到端侧 ML 栈的工程决策"
date: 2026-08-05T22:30:00+08:00
draft: false
summary: "逐层拆解 wigolo 的核心工程决策：agent tool 的 plan-fetch-synthesize 状态机、research 的 fan-out 流水线、find_similar 的三路融合、持久化缓存的变更检测、端侧 ML 模型选型、11 个 skill catalog 的训练注入，以及 slim/full 双 Docker 镜像策略——每个模块的 trade-off 都基于 README 一手信息反推。"
tags: ["MCP", "Local-First", "AI Agent", "Architecture", "On-Device ML"]
categories: ["技术笔记"]
authors: ["钳岳"]
github_repo: "KnockOutEZ/wigolo"
description: "跳过 MCP 介绍和无 API key 叙事，直入 wigolo 的工程内核：agent loop 状态机、research fan-out 流水线、find_similar 三路融合、cache 变更检测、端侧 ML 栈选型、skill catalog 注入机制、Docker 双镜像策略。所有细节基于 README 一手信息反推，标注置信度。"
slug : knockoutez-wigolo-local-first-web-intelligence-mcp-2026

---

## 一句话判断

wigolo 的 10 个 tool 构成一条**从"单次抓取"到"自主采集循环"的渐进管线**，每个模块的 trade-off 都被"本地优先 + 零查询费"这两个约束倒逼出了独特形态。本文跳过已经讲过的 MCP 接入和无 API key 叙事，直入工程内核：agent loop 的状态机怎么跑、research 的 fan-out 怎么分解、find_similar 的三路融合为什么能发现关键词搜不到的页面、cache 的变更检测怎么实现、端侧 ML 模型栈怎么选型、11 个 skill catalog 怎么给 coding agent 注入领域知识。

## 为什么再写一篇 wigolo

已有两篇文章分别覆盖了 MCP 接入体验（「wigolo：本地优先的 AI Agent Web 智能层，无 API Key 跑 MCP」）和核心检索机制（「wigolo 拆解：零 API Key 的本地优先 Web 智能层如何给 AI Agent 赋能」中的 rank fusion、tiered fetch、evidence scoring）。但 wigolo 的工程深度远不止于此——它的真正价值在于把"搜索 → 抓取 → 提取 → 综合 → 自主采集"压缩成一个**可在本地完整运行的 pipeline**，且每个环节都有精心设计的降级策略和置信度信号。本文补上这条链路里尚未被讨论的六个模块。

## 模块一：Agent Tool 的 Plan-Fetch-Synthesize 状态机

### 设计意图

`agent` 是 wigolo 10 个 tool 中最复杂的一个。它是一个有状态的采集循环，远超朴素的"LLM + search"组合：

```
plan → search → fetch → extract → synthesize → (validate) → done | retry
```

每一步的输入是前一步的输出加上一个 **step log**——一个追加式的执行轨迹，记录"搜了什么、抓了什么、提了什么"。这个 log 的消费者是 Agent 自身（而非人类读者），它在下一轮决策时提供完整的"我已做过什么"视图。

### 与朴素 Agent Loop 的区别

标准的 LLM agent loop（如 ReAct 模式）是"思考 → 行动 → 观察"的无限循环，直到 LLM 自己决定停止。wigolo 的 `agent` tool 在此基础上加了三个工程约束：

1. **Time budget**：整个循环有一个硬性时间预算。超时后进入 graceful degradation——把已收集到的证据打包返回，附带 `incomplete: true` 标记。Agent 拿到的是"尽力而为"的结果，而非超时异常。
2. **Step cap**：限制最大迭代轮数。这防止了 LLM 在"搜了又搜但抓不到"的死循环里空转。
3. **Output schema（可选）**：调用方可以传入一个 JSON Schema，`agent` 会在 synthesize 阶段按此 schema 输出结构化结果。这对"帮我调研 X 并以表格形式返回"这类场景非常关键——schema 充当了 synthesize 阶段的"模板"，降低了 LLM 自由发挥导致格式漂移的风险。

### 降级路径

当 `agent` 在循环中发现搜索结果质量不够（evidence score 普遍偏低），它不会硬着头皮 synthesize，而是**先尝试拓宽搜索**（换引擎组合、放宽 query 约束）。如果拓宽后仍然不够，synthesize 阶段会在输出中显式标注 `confidence: low`，并把"哪些子问题没答好"列出来。

> ⚠️ **置信度标注**：以上状态机的具体状态名（plan / search / fetch / extract / synthesize）基于 README 对 `agent` tool 的描述反推。代码层面的确切接口签名和内部状态变量名需验证源码。

## 模块二：Research Tool 的 Fan-Out 流水线

### 与 Agent Tool 的定位差异

`research` 和 `agent` 都做"综合分析"，但定位不同：

| 维度 | `research` | `agent` |
|------|-----------|---------|
| 输入 | 一个问题 | 一个任务描述 + 可选 output schema |
| 自主性 | 中等：自动分解子问题 | 高：自主决定搜索策略 |
| 输出 | 综述报告（带引用） | 结构化结果（按 schema） |
| 适用场景 | "X 是什么？为什么重要？" | "帮我调研 X 并以 JSON 返回" |

`research` 的核心流水线是：

```
问题分解 → 子查询 fan-out → 并行 fetch → 证据聚合 → 综述写作
```

### 问题分解的实现思路

`research` 收到一个复杂问题后，第一步是把它拆成若干子查询。README 没有给出确切的分解算法，但从行为推断，这使用了 LLM 的 in-context 能力（需要 API key），把"如何理解 PostgreSQL 逻辑复制"拆成"什么是逻辑复制"、"逻辑复制 vs 物理复制"、"逻辑复制配置步骤"等子问题。

分解后的子查询并行扇出到 18 个搜索引擎适配器，每个子查询独立走 rank fusion → ML reranking 流程。然后结果按子问题聚合，去重后进入综述阶段。

### Keyless 降级

没有 LLM key 时，`research` 跳过"综述写作"步骤，返回一个 **raw brief**：按子问题组织的证据列表，每条带 source span 和 evidence score。宿主 Agent（如 Claude Code）拿到这个 brief 后，由宿主自己的 LLM 完成综述。

> ⚠️ **基于 README 反推**：README 原文是 "research, agent, and search format=answer use an LLM to write the synthesized, cited answer — without one they hand back a raw brief and evidence for your agent to assemble." 上述流水线描述是基于这句话的合理推断。

## 模块三：Find_Similar 的三路融合

### 问题：关键词搜不到的相似页面

传统的"找相似页面"靠两种方法：一是用当前页面的关键词重新搜索（关键词召回），二是用 embedding 相似度匹配（语义召回）。前者漏掉"换了说法但讲同一件事"的页面，后者漏掉"语义接近但关键词不同"的页面。

wigolo 的 `find_similar` 用三路融合：

1. **关键词路**：从当前页面提取 top-N 关键词，用常规搜索引擎查询。
2. **语义路**：用当前页面的 embedding 在本地缓存中做最近邻搜索。
3. **实时 Web 路**：直接用 URL 作为 `related:` 查询发到搜索引擎（类似 Google 的 `related:` 操作符）。

三路结果融合后，按**三路命中加权**：如果一页同时被关键词路和语义路命中，它的 evidence score 会比只被一路命中的更高。这种设计确保了"关键词搜不到但语义接近"和"关键词匹配但语义偏远"的两种边界情况都能被覆盖。

### 本地缓存的角色

语义路依赖本地缓存中的 embedding 索引。这意味着 `find_similar` 的语义召回质量随使用时间提升——你用 wigolo 越多、缓存越丰富，语义匹配的覆盖面越宽。冷启动时（缓存为空），find_similar 主要依赖关键词路和实时 Web 路。

## 模块四：持久化 Cache 与变更检测

### 混合检索架构

wigolo 的 `cache` tool 不是简单的 HTTP 缓存（URL → response body）。它是一个**混合检索引擎**：

- **关键词索引**：对缓存页面的正文建倒排索引，支持全文检索。
- **向量索引**：对缓存页面生成 embedding，支持语义相似度查询。
- **元数据过滤**：按域名、时间戳、evidence score 等维度过滤。

查询时可以同时使用关键词条件和语义条件，例如"在我缓存的 PostgreSQL 文档中找讲逻辑复制的页面"。

### 变更检测机制

`diff` 和 `watch` 两个 tool 依赖 cache 层的变更检测：

- `diff`：对单个 URL，比较当前抓取版本和缓存版本的差异。差异在**内容层**计算（先 extract 成结构化文本，再比较文本差异），跳过 HTML 层 diff。这避免了"广告位换了导致 diff 告警"的噪音。
- `watch`：定时复检一组 URL，变更时推送到 webhook。`watch` 的设计是 fire-and-forget：设置一次后持续运行，变更检测的粒度可配（任何变化 / 语义变化 / 关键段落变化）。

### 缓存生命周期

缓存数据持久存储在 `~/.wigolo/` 下。没有强制 TTL——缓存不会自动过期。`cache` tool 提供 `stats` 查看缓存大小、`clear` 清空缓存。实际使用中，缓存增长主要靠两个信号管理：

1. 磁盘空间阈值：当 `~/.wigolo/` 超过设定大小时，按 LRU（Least Recently Used）淘汰最久未访问的页面。
2. 手动 clear：用户或 Agent 主动清空。

> ⚠️ **基于 README 反推**：README 提到 cache 支持 keyword / hybrid query 和 change detection，但未给出确切的 LRU 实现细节和默认磁盘阈值。上述生命周期描述是基于通用缓存设计模式的推断。

## 模块五：端侧 ML 模型栈

### 模型组成

wigolo 的 ~1.5 GB 磁盘占用主要来自三个组件：

| 组件 | 大小（估） | 职责 |
|------|-----------|------|
| Browser engine（Chromium 内核） | ~500 MB | 渲染 SPA、绕过 JS challenge |
| Embedding model | ~100–200 MB | 生成页面/查询的向量表示 |
| Reranker model | ~300–500 MB | 对搜索结果做语义精排 |
| 其他（搜索引擎配置、缓存索引、skill catalog） | ~100–200 MB | 杂项 |

> ⚠️ **大小为估算**：README 只给出总磁盘 ~1.5 GB，未拆分各组件。上表是基于典型 Chromium + SBERT 级 embedding + Cross-Encoder 级 reranker 的合理估算，实际数值需验证安装目录。

### "Code Beats Model" 原则

wigolo 在架构上有一个贯穿性的设计哲学：**能用确定性代码解决的事，不调用 LLM**。

- **Canonicalization**（URL 规范化、HTML 清洗）：纯代码，不调模型。
- **Rank fusion**（多引擎结果合并）：数学公式（Reciprocal Rank Fusion 等），不调模型。
- **Dedup**（去重）：哈希 + URL 规范化，不调模型。
- **Schema matching**（结构化提取的模板匹配）：规则引擎，不调模型。

模型只在"判断"环节出场：

- **Embedding**：语义相似度计算。
- **Reranking**：对 fusion 后的候选列表做精细排序。
- **Synthesis**（可选）：research / agent 的综述写作。

任何 LLM 填入的字段都会与原始来源比对，不存在则置 null。这个设计的关键含义是：**wigolo 的搜索结果质量不完全依赖模型质量**。即使 reranker 模型偏弱，rank fusion 和 engine consensus 仍然提供了合理的基线排序。反之，即使 LLM synthesis 出现幻觉，byte-pinned source spans 让幻觉可被检测——Agent 只需检查 source span 是否指向真实内容即可识破。

### 模型存储与更新

所有模型文件存储在 `~/.wigolo/` 下。`wigolo doctor` 会检查模型完整性。模型更新通过 `wigolo update`（或 init 时自动检查）拉取新版本。模型版本与 wigolo 软件版本解耦——可以在不升级 wigolo 本体的情况下更新模型，反之亦然。

## 模块六：Skill Catalog 与 Agent 增强

### 11 个 Skill 是什么

wigolo 在 `init` 时自动安装 11 个 skill。这些 skill 的本质是**领域知识包**——为 coding agent 提供"怎么用 wigolo 做某类任务"的结构化指引，而非代码插件。

从 README 列出的 skill catalog 看，这些 skill 覆盖了典型的 web research 场景：

- 文档查证（API reference 查找、changelog 追踪）
- 技术选型对比（多源采集 + 对比矩阵）
- 代码示例搜索（跨引擎 code search）
- 错误诊断（错误信息 → 已知 issue / fix）
- 安全公告追踪（CVE / advisory 监控）

> ⚠️ **基于 README 反推**：README 提到 "11 skill catalog (init auto-install)"，但未逐一列出 skill 名称。上述场景是基于 wigolo 作为 coding agent web tool 的定位推断的典型用法。

### Skill 如何注入 Agent

skill 的注入路径是 MCP protocol：`wigolo init --agents=claude-code` 会在 Claude Code 的 MCP 配置中注册 wigolo server，同时把 skill catalog 作为 MCP resource 暴露。Claude Code 在 session 启动时加载这些 resource，相当于"wigolo 教 Claude Code 怎么用自己"。

这种设计的意义在于：coding agent 不需要用户手动写 prompt 来"教它用 wigolo"。Skill catalog 已经告诉它"查 API 文档用 search + include_domains"、"调研技术选型用 research"、"监控变更用 watch"——工作流注入在 `init` 阶段自动完成，Agent 拿到的不只是工具列表，还有使用策略。

## 模块七：Docker 双镜像策略

### Slim vs Full

wigolo 提供两个 Docker image：

| 镜像 | 大小 | 浏览器引擎 | 模型文件 | 适用场景 |
|------|------|-----------|---------|---------|
| `wigolo:slim` | 小 | 不含（懒加载） | 不含（首次用时下载） | CI/CD、快速启动、磁盘敏感 |
| `wigolo:full` | 大 | 预装 | 预装 | 离线环境、稳定生产、首次启动延迟敏感 |

slim 镜像的设计哲学是"按需加载"：首次调用需要浏览器的 fetch 时才下载 Chromium 内核，首次调用需要 reranker 时才下载模型。这降低了初始部署成本，但代价是首次请求的延迟较高。

full 镜像则预装所有组件，适合"不能容忍首次延迟"或"网络受限无法懒加载"的场景。

### 部署模式总览

结合 Docker 策略，wigolo 实际上支持四种部署模式：

1. **直接安装**（`npx wigolo init`）：最常见，模型和浏览器引擎下载到 `~/.wigolo/`。
2. **Docker slim/full**：容器化部署，适合服务器环境。
3. **SDK 嵌入**（TypeScript / Python）：把 wigolo 作为库嵌入到自己的 Agent 框架中。SDK 提供 `local_client()` 方法，自动复用已运行的 daemon 或启动新实例。
4. **REST API**（`wigolo serve`）：监听 `127.0.0.1:3333`，off-loopback 需 token 认证。适合非 MCP 的编排系统（n8n、自定义 pipeline）。

## 工程决策的系统性审视

把以上七个模块放在一起看，wigolo 的架构决策遵循三条系统性原则：

### 原则一：渐进式降级是默认行为

| 场景 | 完整模式 | 降级模式 |
|------|---------|---------|
| 有 LLM key | research 输出综述报告 | 返回 raw brief + 证据列表 |
| 浏览器引擎就绪 | fetch 走完整渲染 | 返回 `blocked_by_challenge` 标记 |
| 缓存命中 | 即时返回 + 混合检索 | 降级为实时抓取 |
| 引擎全可用 | 18 引擎 rank fusion | 部分引擎失败时降级为可用引擎子集 |
| Agent time budget 足够 | 完整 plan-synthesize 循环 | 超时返回 `incomplete: true` + 已有证据 |

每一个降级路径的含义都是"减少能力但保持可用"，而非抛错中断。这让 wigolo 在各种环境（满配开发机、CI runner、离线环境、弱网）中都能产出可用结果，避免了 all-or-nothing 的脆弱性。

### 原则二：可观测性嵌入结果

wigolo 不把可观测性当作"运维事后补"的日志系统，而是**嵌入到每次返回的结果中**：

- 搜索结果带 `evidence_score` 分解（semantic / lexical / engine_consensus）
- fetch 结果带 `freshness_signal`（发布时间 + 置信度）
- agent 结果带 `step log`（执行轨迹）和 `confidence`（整体置信度）
- 失败结果带明确标签（`blocked_by_challenge`、`incomplete: true`、`junk`）

这种设计让 coding agent 可以用**结构化方式评估自己拿到的信息质量**，而不是靠"看起来对不对"来猜。对 Agent 的决策链路来说，这是比"多召回 5%"重要得多的能力。

### 原则三：本地化是约束，不是卖点

wigolo 的本地优先有一条常被忽视的深层原因：本地化是**让渐进式降级和可观测性嵌入在经济上可行的唯一路径**。如果每次降级判断都要调云 API，降级本身就引入了新的成本和延迟。把 reranker、embedding、缓存全部放本地，意味着所有"质量判断"都是零边际成本的——Agent 可以肆意调用、反复验证，不需要担心"这次评估要花多少钱"。

这是 wigolo 与 Firecrawl / Exa / Tavily 的根本差异所在：**经济模型不同导致 Agent 使用模式不同**。metered API 下，Agent 的每次质量检查都是成本；wigolo 下，质量检查是免费的副产品。

## 边界与风险

### AGPL-3.0 的传染性

wigolo 采用 AGPL-3.0 许可证。这对商业部署有实际影响：

- **直接使用 wigolo（MCP server / REST）**：作为独立服务运行，不链接到你的代码，通常不触发 AGPL 传染。
- **SDK 嵌入**：把 wigolo SDK 链接到你的 Agent 代码中，可能触发 AGPL 的 copyleft 条款——你的代码也需要开源。
- **修改 wigolo 源码并部署为网络服务**：AGPL 的 "Network Use" 条款要求，即使只是提供网络服务（不分发二进制），也需要向用户提供修改后的源码。

> ⚠️ **非法律建议**：以上是基于 AGPL-3.0 许可证文本的通用理解。商业部署前应咨询法律顾问，确认你的具体使用模式是否触发传染条款。

### Datacenter IP 的反爬挑战

wigolo 在 README 中明确指出，datacenter IP（如云服务器、VPS）在面对某些网站的反爬系统时会遇到更多 challenge。这是因为许多反爬服务（Cloudflare、Akamai 等）会对 IP 做信誉评级，datacenter IP 段通常被评为高风险。

wigolo 的应对策略是：

1. **明确报告失败**：不伪装成功，返回 `blocked_by_challenge`。
2. **支持 opt-in 代理**：用户可以配置自己的代理服务器。
3. **带浏览器 Profile 的请求**：需要登录态的场景可以复用已有的浏览器 cookie。

但这意味着在 datacenter 部署 wigolo（比如 Docker full 镜像跑在 VPS 上）对某些网站的覆盖率会低于在家用宽带 + 本地机器上跑。这是 local-first 设计的一个内在矛盾：**真正的"本地"是家用网络，不是云服务器**。

## 结语：wigolo 的架构给 Agent 工程的启示

wigolo 的价值不在于"免费替代 Tavily"。把七个模块拆开看，它展示了一个完整的命题：**当 Web 检索从"云服务 API"变成"本地基础设施"时，Agent 的行为模式会发生质变**。

- Agent 可以在每次决策时都检查 evidence score，不需要考虑成本。
- Agent 可以在 agent loop 里跑十轮，每轮都拉新数据，不需要担心账单。
- Agent 的失败是结构化的（`junk` / `blocked_by_challenge` / `incomplete`），而不是模糊的"结果不好"。
- 所有质量信号（consensus、freshness、confidence）都是机器可读的，可以直接驱动 Agent 的下一步决策。

这些行为的共同前提是：**每次调用都是零边际成本**。wigolo 的工程决策最终指向的目标，是消除"Agent 思考就要付费"这个隐藏约束——它的野心从来不在"做一个更好的搜索 API"。

## 参考

- **wigolo 仓库**：[KnockOutEZ/wigolo](https://github.com/KnockOutEZ/wigolo)
- **已有文章 1**：[wigolo：本地优先的 AI Agent Web 智能层，无 API Key 跑 MCP](https://txtmix.com/posts/tech/knockoutez-wigolo-local-first-web-agent/)
- **已有文章 2**：[wigolo 拆解：零 API Key 的本地优先 Web 智能层如何给 AI Agent 赋能](https://txtmix.com/posts/tech/wigolo-local-first-web-intelligence-ai-agents/)
- **MCP 协议**：[Model Context Protocol Specification](https://modelcontextprotocol.io/)
- **Reciprocal Rank Fusion**：Cormack et al., "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods", SIGIR 2009
