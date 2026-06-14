---
title: "TencentDB Agent Memory 架构拆解：用 4 层语义金字塔 + Mermaid 符号图解决 Agent 长记忆的两难"
date: "2026-06-13T21:03:20+08:00"
slug: "tencentdb-agent-memory-layered-symbolic-architecture"
description: "拆解 TencentDB Agent Memory 的核心设计：4 层语义金字塔与 Mermaid 符号化短期记忆，解决 Agent 长记忆丢失证据、压缩不可逆的问题。"
draft: false
categories: ["技术笔记"]
tags: ["Agent", "LLM", "记忆系统", "MCP", "向量数据库"]
---

# TencentDB Agent Memory 架构拆解：用 4 层语义金字塔 + Mermaid 符号图解决 Agent 长记忆的两难

> 一句话判断：**TencentDB Agent Memory 把"长期记忆"切成 L0 → L1 → L2 → L3 四层语义金字塔，把"短期记忆"用 Mermaid 符号图（symbolic canvas）+ 全量日志外置（offload）做压缩。整套设计的重点是"记得可追溯"——任何抽象都能下钻回原始证据，避免传统记忆系统在压缩率与可解释性之间二选一**。

## 一、项目坐标

| 字段 | 值 |
|------|------|
| 仓库 | [TencentCloud/TencentDB-Agent-Memory](https://github.com/TencentCloud/TencentDB-Agent-Memory) |
| 形态 | OpenClaw 插件 + Hermes Gateway Adapter + npm 包 `@tencentdb-agent-memory/memory-tencentdb` |
| Stars | 约 5.4k（截至 2026-06） |
| License | MIT |
| 兼容框架 | OpenClaw（≥ 2026.3.13）、Hermes |
| 默认后端 | SQLite + sqlite-vec（零外部依赖，零配置启动） |

它的发布形式比较特殊：不是"一个独立后端服务"，而是"一个 Agent 框架侧的内存插件 + 一个本地 Gateway"。Gateway 默认监听 `:8420`，负责把 L1/L2/L3 的提取和检索请求转给 LLM，并把记忆写入 SQLite。这个仓库的本质是 **"Agent 记忆系统的参考实现 + 部署说明书"**，不是简单的 SDK。

## 二、问题域：为什么 Agent 记忆这么难？

任何跑过长期 Agent 工作流的人都会撞到两个硬伤：

1. **短期：上下文膨胀**。SWE-bench 这种长程任务跑下来，光 tool 输出就能堆出几百万 token；WideSearch 多轮搜索更是动辄上百兆；强行塞进 context 的后果是成本爆表、注意力涣散、模型开始重复犯错。
2. **长期：扁平向量检索漂移**。把所有对话打成 chunk 塞进向量库，看起来"全记住了"，召回时却是一堆毫无上下文的相似片段——查"用户偏好用什么编程语言"返回三段毫不相干的代码片段。

TencentDB Agent Memory 的解法是把记忆**结构化**：

- 用 4 层语义金字塔替代平面向量库（解决"长期记忆漂移"）；
- 用 Mermaid 符号图 + 全量日志外置替代直接堆 token（解决"短期记忆膨胀"）。

下面拆开看。

## 三、长期记忆：L0 → L1 → L2 → L3 语义金字塔

记忆的"层"按**抽象度**分。每一层只关心上一层的信息，下层只在需要细节时才被召回。

```
┌─────────────────────────────────────────────────┐
│ L3 Persona            用户画像 / 长期偏好         │ ← 每天/每个 N 条新记忆触发
│   "用户偏好 Rust、用 uv、不喜欢 emoji、日更     │
│    周报、写文档时不要 marketing 词"             │
├─────────────────────────────────────────────────┤
│ L2 Scenario           场景块（可复用的解题模式）   │ ← 同主题的多条 Atom 聚类
│   "调试 Rust 编译错误的标准流程"                │
│   "准备 AI 周报的固定模板"                       │
├─────────────────────────────────────────────────┤
│ L1 Atom               原子事实（带时间戳/实体）   │ ← 每 N 轮对话抽一次
│   "2026-06-12 调试 swc 时关掉 swcrc 的 jsc.target"
│   "2026-06-13 把 cross-publisher 改用 chrome-cdp"
├─────────────────────────────────────────────────┤
│ L0 Conversation       原始对话（Markdown 文件）   │ ← 全量留存，gitignored
│   "session_2026-06-13_21-03.md"                 │
└─────────────────────────────────────────────────┘
```

四层的关系是**单向可下钻**：

- L3 Persona 告诉你"用户喜欢 Rust"；
- 想知道具体场景，下钻到 L2 Scenario 看"调试 swc 的标准流程"；
- 还想看某次具体怎么解决的，下钻到 L1 Atom 看"2026-06-12 改 swcrc 的 jsc.target"；
- 最后想看原始对话，下钻到 L0 Conversation 看 `session_xxx.md`。

每一层都存为**人类可读的 Markdown**（不是向量、不是 JSON blob），这带来一个非常具体的工程收益：**调试时直接 `cat persona.md` 就能看到完整的"用户画像"，不用去查向量库看相似度分数**。这就是 README 里反复强调的"white-box debuggability"。

### 3.1 异构存储：上层 Markdown，下层 SQLite

分层不是纯逻辑概念，存储介质也不一样：

| 层 | 存储 | 理由 |
|----|------|------|
| L3 Persona / L2 Scenario | Markdown 文件 | 信息密度高、可人读、可 git diff、方便审计 |
| L1 Atom | SQLite（带 sqlite-vec） | 需要结构化字段（时间戳、实体、向量索引） |
| L0 Conversation | Markdown 文件 | 全量留存，体量大，靠文件系统足够 |
| 短期 Mermaid canvas + refs/*.md | Markdown / 文件系统 | 同上，符号图给人 + LLM 共读 |

**上层保留结构，下层保留证据**。这就是 README 里那句话的工程落地——"Lower layers preserve evidence; upper layers preserve structure"。

### 3.2 渐进式披露（Progressive Disclosure）

记忆召回也有讲究。回答不同问题，去不同层找：

| 问题类型 | 先看哪层 | 必要时下钻到 |
|----------|---------|-------------|
| 用户偏好、口吻、长期目标 | L3 Persona / L2 Scenario | L1 Atom / L0 Conversation |
| 具体事实、日期、项目细节 | L1 Atom / L0 Conversation | 扩大时间范围或回退到语义召回 |
| 继续一个长任务 | 当前会话的 Mermaid canvas | 看 JSONL 步骤、`refs/*.md` 原始日志 |
| 恢复一个历史任务 | 元数据任务入口 | 开 canvas → 找 `node_id` → 查 `result_ref` |

这样的好处是：**默认查询只命中高层、低成本、高密度**；碰到细节才付代价下钻——典型的"按需付出"。

## 四、短期记忆：Mermaid 符号图 + 日志外置

长期记忆搞清楚了金字塔，短期记忆怎么办？SWE-bench 50 轮任务，光 tool 输出就能堆出 200 万 token；WideSearch 那种搜索任务，单次返回几百 KB 的搜索结果是常态。

如果把这堆东西原样塞进 context：成本爆炸 + 注意力稀释 + 重复犯错。

TencentDB 的解法是两步：

### 4.1 第一步：全量日志外置（Context Offload）

把所有 verbose tool 日志原文写到 `refs/*.md`（文件系统 / refs/ 目录），context 里只留一个 `node_id` 指针。

```mermaid
graph LR
    Log["Verbose Logs<br/>(hundreds of thousands of tokens)"] -->|"1. Offload full text"| FS[("External FS<br/>(refs/*.md)")]
    Log -->|"2. Extract relations"| MMD["Mermaid Canvas<br/>(with node_id)"]

    MMD -->|"3. Light injection"| Agent(("Agent Context<br/>(a few hundred tokens)"))
    Agent -. "4. Recall via node_id" .-> FS

    style Log fill:#f1f5f9,stroke:#94a3b8,stroke-dasharray: 5 5,color:#475569
    style FS fill:#f8fafc,stroke:#cbd5e1,stroke-width:2px,color:#334155
    style MMD fill:#eff6ff,stroke:#3b82f6,stroke-width:2px,color:#1e3a8a
    style Agent fill:#fffbeb,stroke:#f59e0b,stroke-width:2px,color:#92400e
```

### 4.2 第二步：用 Mermaid 符号图代替 JSON 状态

state tracking 不写 JSON、不写散文，而是写成 Mermaid 图。Mermaid 是 LLM 友好、人也友好的"半结构化 DSL"——一行语法就能描述状态、转移、依赖。

```mermaid
graph TD
    A[Fetch trending daily] -->|success| B[Parse 14 repos]
    A -->|fail| Z[Retry with backoff]
    B --> C[Filter already written]
    C -->|new repos| D[Write article per repo]
    C -->|all covered| Y[Skip + report]
    D --> E[git add tech/*.md]
    E --> F[git commit + push]
    F --> G[Feishu notify]
```

把这段塞进 context 只有几百 token，但 LLM 仍然能完整理解任务流；要查某一步的细节，按 `node_id` 去 `refs/*.md` 取原始日志。

### 4.3 Benchmark：实际跑出来能省多少？

README 里给的数字比较具体（按 OpenClaw 默认配置、跑在 WideSearch / SWE-bench / AA-LCR / PersonaMem 上）：

| 能力维度 | Benchmark | 接入前 | 接入后 | 相对 Δ |
|---------|-----------|-------|-------|--------|
| 短期 | WideSearch | 33% 通过率 | 50% 通过率 | **+51.52%** |
| 短期 | WideSearch | 221.31M tokens | 85.64M tokens | **−61.38%** |
| 短期 | SWE-bench | 58.4% 通过率 | 64.2% 通过率 | **+9.93%** |
| 短期 | SWE-bench | 3474.1M tokens | 2375.4M tokens | **−33.09%** |
| 短期 | AA-LCR | 44.0% 通过率 | 47.5% 通过率 | **+7.95%** |
| 短期 | AA-LCR | 112.0M tokens | 77.3M tokens | **−30.98%** |
| 长期 | PersonaMem | 48% 准确率 | 76% 准确率 | **+59%** |

要点：

- **token 节省 30–61%**：靠的是 Mermaid 符号图 + 外置原始日志；
- **Pass rate 提升 8–52%**：靠的是"上层的 Persona/Scenario 提供宏观引导 + 必要时能下钻到原始日志"，模型不再在乱糟糟的工具输出里迷路；
- **PersonaMem 准确率 48% → 76%**：靠的是 L3 Persona 层的结构化画像 + L1/L2 的可追溯证据。

注意这些数据**测的是长程多轮会话**（SWE-bench 是 50 轮连续任务），不是单轮对话——这是 Agent 记忆评测的关键差别，单轮看不出 Mermaid 符号图带来的优势。

## 五、Pipeline：记忆是怎么"自动长出来"的？

把上面的金字塔和符号图串成一个 pipeline 后，整个 Agent 一次会话的"记忆生命周期"是：

```
对话流（user/assistant/tool 消息）
    │
    ▼
┌────────────────────────────────────────┐
│ L0 Conversation 捕获（全量 Markdown）    │
│   session_<时间戳>.md                  │
└────────────────────────────────────────┘
    │  everyNConversations（默认 5）
    ▼
┌────────────────────────────────────────┐
│ L1 Atom 提取（LLM 抽原子事实）           │
│   SQLite + sqlite-vec                  │
│   含去重 + 冲突检测（enableDedup）      │
└────────────────────────────────────────┘
    │  聚类
    ▼
┌────────────────────────────────────────┐
│ L2 Scenario 聚类（LLM 聚成可复用场景）  │
│   Markdown 块                          │
└────────────────────────────────────────┘
    │  triggerEveryN（默认 50 条新记忆）
    ▼
┌────────────────────────────────────────┐
│ L3 Persona 生成（LLM 蒸馏用户画像）      │
│   persona.md                           │
└────────────────────────────────────────┘
    │
    ▼
┌────────────────────────────────────────┐
│ 下一轮对话召回                           │
│   hybrid（BM25 + 向量 + RRF 融合）     │
└────────────────────────────────────────┘
```

所有这些步骤都是异步、批量的，不阻塞在线对话。

短期记忆那边的 pipeline 更轻：

```
tool_call 输出
    │
    ▼
┌────────────────────────────────────────┐
│ 写入 refs/<node_id>.md（外置）           │
└────────────────────────────────────────┘
    │
    ▼
┌────────────────────────────────────────┐
│ 更新 Mermaid canvas（增量追加节点）       │
│   <100 tokens 注入 context              │
└────────────────────────────────────────┘
```

## 六、部署形态：本地优先 + 可选云端

README 把部署分成 3 档：

### 6.1 OpenClaw 插件（最简）

```bash
openclaw plugins install @tencentdb-agent-memory/memory-tencentdb
openclaw gateway restart
```

写一段 5 行的配置启用：

```jsonc
{
  "memory-tencentdb": {
    "enabled": true
  }
}
```

这样就够用了——背后是 SQLite + sqlite-vec，零外部依赖。

### 6.2 Hermes 集成（中间档）

Hermes（NousResearch 的 Agent 框架）有自己的 Gateway 架构。TencentDB 走的是"在 Hermes 之外跑一个独立 Gateway + 通过 HTTP/WebSocket 通信"的路线，目录名必须是 `memory_tencentdb`（带下划线），不是 `memory-tencentdb`（带连字符）——这是 Hermes 的 provider key 约定。

最有意思的是 Hermes 集成里那个 `auto-discovery`：第一次对话时插件自动 `Popen()` 启动 Gateway，初次对话会慢一点，之后就稳定了。这种"懒启动"对单机用户非常友好。

### 6.3 Docker 一键部署（最重）

如果是从零启动一个 memory-enabled Hermes：

```bash
docker build -f docker/opensource/Dockerfile.hermes -t hermes-memory .
docker run -d --name hermes-memory --restart unless-stopped \
  -p 8420:8420 \
  -e MODEL_API_KEY="..." \
  -e MODEL_BASE_URL="https://api.lkeap.cloud.tencent.com/v1" \
  -v hermes_data:/opt/data \
  hermes-memory
```

镜像里默认带了 Tencent Cloud 的 DeepSeek-V3.2，可以直接用，也可以改 env 切到 OpenAI、Anthropic 等任意 OpenAI 兼容端点。

## 七、可调参数：三级暴露

调参文档按"日常 / 进阶 / 全量"三档展开，最常用的几个：

| 字段 | 默认 | 说明 |
|------|------|------|
| `timezone` | `"system"` | `"system"` / IANA 名 / `+08:00` |
| `storeBackend` | `"sqlite"` | 后端类型 |
| `recall.strategy` | `"hybrid"` | `keyword` / `embedding` / `hybrid`（RRF 融合） |
| `recall.maxResults` | `5` | 每次召回条数 |
| `pipeline.everyNConversations` | `5` | 每 N 轮触发 L1 提取 |
| `persona.triggerEveryN` | `50` | 每 N 条新记忆触发 Persona 生成 |
| `offload.enabled` | `false` | 是否启用短期压缩（Mermaid + refs） |
| `offload.mildOffloadRatio` | `0.5` | 上下文 50% 时开始轻度压缩 |
| `offload.aggressiveCompressRatio` | `0.85` | 85% 时激进压缩 |

注意 `offload.enabled` 默认是 `false`——这是有意的"保守默认"。短期压缩是工具，开了能省 token，但也会改变 Agent 的"看到的事实"，对某些场景反而不利。架构师把开关留给运营方按需打开，避免一上来就误伤调试期的可观测性。

## 八、安全：Gateway 鉴权

Gateway 默认监听 `:8420`，对 `GET /health` 永远开放（给 orchestrator 探活用），其他端点默认无鉴权。一旦想把它从"本地 localhost 工具"升级成"内网服务"，需要：

```bash
TDAI_GATEWAY_API_KEY="<your-secret>"
TDAI_CORS_ORIGINS="https://app.example.com,https://admin.example.com"
```

设置后所有非 `/health` 路由强制 `Authorization: Bearer <apiKey>`，且比对走的是 constant-time 实现（防 timing attack）。Hermes 端的 plugin 通过 `MEMORY_TENCENTDB_GATEWAY_API_KEY`（plugin 端命名）把这个 secret 加进每个请求——**Gateway 端读的是 `TDAI_GATEWAY_API_KEY`，plugin 端读的是 `MEMORY_TENCENTDB_GATEWAY_API_KEY`**，两套命名是有意分开的，方便不同进程共用同一份 env 文件时只设一个变量。

## 九、和同类方案的差异

| 方案 | 长期记忆形态 | 短期记忆压缩 | 可追溯性 | 适用场景 |
|------|------------|-------------|---------|---------|
| MemGPT / Letta | 层级（核心/归档/召回） | 分页 + 召回 | 弱（依赖向量相似度） | 学术原型 |
| LangGraph Memory | 向量库 + checkpointer | 无 | 中（checkpointer 留痕） | LangGraph 应用 |
| Mem0 | 向量 + LLM 重写 | 无 | 弱（重写即覆盖） | 轻量个性化 |
| **TencentDB Agent Memory** | **L0/L1/L2/L3 语义金字塔 + Markdown** | **Mermaid canvas + refs 外置** | **强（每层都能下钻到证据）** | **生产级长程 Agent** |

关键差异：

- **不丢原始证据**。Mem0 这类方案习惯用 LLM 总结成"用户喜欢 Rust"就完事了，原始对话扔掉。TencentDB 永远保留 L0 Conversation + refs/*.md，需要时能下钻。
- **压缩可逆**。短期压缩的方案是符号化 + 外置；`node_id` 是双向指针，逻辑上完全可还原。
- **本地优先**。SQLite + sqlite-vec 是默认后端，不依赖任何云服务；云端只作为可选项存在。这对很多企业用户很关键——记忆里都是业务上下文，不愿意出本地。

## 十、采用建议

适合用 TencentDB Agent Memory 的场景：

- **SWE-bench / WideSearch 这类长程、多步、需要反复回查历史的任务**——SWE-bench 50 轮连续任务的 pass rate 提升 9.93% 不是凭空来的。
- **想给 Agent 做"用户级个性化"**，且不愿意把记忆交给 SaaS——SQLite 默认后端 + 本地 Markdown 文件可以完全 self-hosted。
- **生产环境需要可调试**——白盒 persona.md / scenario.md / refs/ 结构让 on-call 能像看日志一样定位"为什么 Agent 召回错了"。

不太适合的场景：

- **单轮 Q&A 或短对话**——这套 pipeline 的 warmup 成本和 LLM 抽取成本摊不到短会话上。
- **极端低延迟要求**（<100ms first token）——首次对话要触发 Gateway 懒启动，外加 L1 抽取是异步批处理。
- **强多租户隔离**——当前 SQLite 单库，没有 row-level 租户隔离；要做企业版需要补一层 plugin 包装。

如果你的 Agent 在生产里跑了几个月、用户开始抱怨"它每次都忘记我说过什么"，或者 token 账单里长期记忆这一栏涨得离谱，这个项目值得认真评估。它不像 Mem0 那样 "5 行代码接入"，但回报是真实的可追溯性 + 可控成本——这正是把 Agent 从 demo 推向生产必须付的代价。