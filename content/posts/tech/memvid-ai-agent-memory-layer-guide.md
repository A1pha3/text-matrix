---
title: "Memvid：单文件 AI 智能体记忆层指南"
date: "2026-04-12T02:31:39+08:00"
lastmod: "2026-09-28T00:00:00+08:00"
slug: memvid-ai-agent-memory-layer-guide
github_repo: "memvid/memvid"
source_key: "gh:memvid/memvid"
description: "Memvid 用一个 .mv2 文件装下数据、向量、索引和 WAL，把 RAG 管线里的向量库、嵌入服务、API 服务器换成零运维的单文件。本文以 v2.0.140 源码与 memvid-cli 2.0.140 实测为口径，覆盖 Smart Frames 结构、检索模式与自适应召回、时间旅行回放、实体记忆卡、容量票证与加密，并核对四端 SDK 的真实 API。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "记忆系统", "向量检索", "Rust"]
---

# Memvid：单文件 AI 智能体记忆层指南

> 单文件持久化 · 无数据库 · 词法+语义混合检索 · 时间旅行回放 · AES-256-GCM 加密

## 目录

- [一、项目概述](#一项目概述)
- [二、性能口径：宣传数字与可复现基准](#二性能口径宣传数字与可复现基准)
- [三、为什么需要单文件记忆层](#三为什么需要单文件记忆层)
- [四、核心概念：Smart Frames 与 .mv2 格式](#四核心概念smart-frames-与-mv2-格式)
- [五、快速开始](#五快速开始)
- [六、核心功能详解](#六核心功能详解)
- [七、Feature Flags](#七feature-flags)
- [八、多模态支持](#八多模态支持)
- [九、使用场景与适用边界](#九使用场景与适用边界)
- [十、实践建议](#十实践建议)
- [十一、API 参考](#十一api-参考)
- [十二、VS 其他方案](#十二vs-其他方案)
- [十三、故障排除](#十三故障排除)
- [十四、FAQ](#十四faq)
- [十五、资源链接](#十五资源链接)
- [十六、总结与进阶路径](#十六总结与进阶路径)

## 一、项目概述

### 1.1 Memvid 是什么

Memvid 是一个面向 AI 智能体的**单文件记忆层**：数据、嵌入向量、检索索引、预写日志全部装进一个 `.mv2` 文件，不需要部署向量数据库。

> **官方定义**："Memvid is a single-file memory layer for AI agents with instant retrieval and long-term memory. Persistent, versioned, and portable memory, without databases."

它解决的问题是结构性的：传统 RAG 需要同时维护向量库、嵌入服务和 API 服务，数据进出都要走网络；Memvid 把这三件事压缩进文件内部，检索发生在本地进程里，迁移就是拷贝文件。

值得一提的是项目的历史：Memvid v1 走的是「把文本编码成二维码、塞进视频帧」的路线，这条线**已被官方弃用**——README 明确写着 "Memvid v1 (QR-based memory) is deprecated. If you are referencing QR codes, you are using outdated information"。如今的 v2 是 Rust 重写的单文件存储引擎，网上不少旧教程还在讲二维码方案，阅读时注意区分。

### 1.2 项目数据

| 指标 | 数值（2026-09-28 读数） |
|------|------|
| **Stars** | **16,559** |
| **Fork** | 1,419 |
| **贡献者** | 23 |
| **最新版本** | **v2.0.140**（2026-05-27 发布，crates.io 同步） |
| **npm / PyPI 包版本** | 2.0.160（CLI 二进制自报版本为 2.0.140） |
| **许可证** | Apache-2.0 |
| **核心语言** | Rust 约 98.5%（languages API 字节数折算） |
| **发布形态** | CLI（npm 预编译二进制）/ Node.js SDK / Python SDK / Rust crate |

本文口径：源码与文件格式以 main 分支提交 `e6bd9f7`（2026-07-14）和 `MV2_SPEC.md` v2.1 为准，命令行以 memvid-cli 2.0.140 实测为准，官方文档以 docs.memvid.com 当前版本为准。项目仍在活跃开发，API 细节以你使用的版本为准。

### 1.3 定位

| 维度 | 说明 |
|------|------|
| **单文件** | 数据、嵌入、索引、WAL 都在一个 `.mv2` 里，无 `.wal`/`.lock`/`.shm` 等旁车文件 |
| **无数据库** | 进程内嵌入式引擎，不需要单独部署和维护存储服务 |
| **模型无关** | 嵌入可走本地 ONNX 模型，也可接 OpenAI 等 API；LLM 只在 `ask` 问答时用到 |
| **离线优先** | 词法检索和本地嵌入全程可离线 |
| **版本化** | 每帧带时间戳，支持按帧号/时间戳回溯历史状态 |

README 用五个概念概括 v2 的能力：Living Memory Engine（持续追加与演化）、Capsule Context（自包含记忆胶囊）、Time-Travel Debugging（回放任意历史状态）、Smart Recall（官方称 sub-5ms 本地访问与预测缓存）、Codec Intelligence（按代自动升级压缩）。

## 二、性能口径：宣传数字与可复现基准

Memvid 的性能声明有两套口径，分开看才不会被数字带偏。

**第一套是 README 的头条数字**：LoCoMo 基准准确率 +35% SOTA，多跳推理 +76%、时间推理 +56%（相对行业平均）；延迟 0.025ms P50、0.075ms P99，吞吐量为标准向量库的 1,372 倍。官方称基准可复现（10 段约 26K token 的 LoCoMo 对话、开源评测、LLM-as-Judge），但这组延迟数字没有随附具体测试环境和方法学，建议当作定性参考。

**第二套是官方文档的可复现基准**（[introduction/benchmarks](https://docs.memvid.com/introduction/benchmarks)），方法学交代得完整：Wikipedia 数据集 39,324 篇文档、2,500 条自然语言查询，对比 Chroma 0.4.x、LanceDB、Qdrant、Weaviate 四个向量库，全部默认配置、同一嵌入模型、Apple M 系列 Mac、每查询一次无缓存，测试套件开源（仓库 `benchmarks/python`）。核心结果：

| 系统 | Top-1 准确率 | MRR | 查询延迟 p50 | QPS | 冷启动 |
|------|------------|-----|------------|-----|--------|
| **Memvid v2**（hybrid） | **92.72%** | **0.949** | 16.0ms | 61 | **0.5ms** |
| LanceDB | 84.24% | 0.888 | 16.0ms | 61 | 72.4ms |
| Qdrant | 84.24% | 0.888 | 28.0ms | 36 | 71.8ms |
| Weaviate | 80.68% | 0.849 | **5.3ms** | **180** | 147.7ms |
| Chroma | 78.24% | 0.823 | 55.6ms | 18 | 66.3ms |

怎么读这张表：

- **准确率是 Memvid 的强项**：Top-1 比最强的竞品高 8.5 个百分点，检索错误率 7.28%，比 Chroma 少 66%。
- **稳态延迟不是**：p50 16ms 与 LanceDB 持平，慢于 Weaviate 的 5.3ms。Memvid 的优势在**冷启动**——0.5ms 对 66–148ms，快 130–300 倍，这正是单文件、无服务架构的差异化场景（Serverless、按需拉起、CLI 工具）。
- 综合质量除以延迟，官方算出 4.2 倍于 Chroma 的 accuracy-per-ms。

一句话：如果你的负载是常驻高 QPS 服务，Weaviate 这类专用引擎仍然更快；如果是 Agent 记忆、边缘部署、CLI 工具这类「冷启动频繁、单机本地」的场景，这组数字对 Memvid 有利。

## 三、为什么需要单文件记忆层

传统 RAG 栈的痛点不在于功能，而在于组件数量：文档摄取、嵌入服务、向量库、API 服务，每个都要部署、配置、监控；数据在组件间走网络，延迟叠加；云向量库按量计费，且数据要出境。对个人开发者和小团队，为一个 Agent 记忆维护一套向量数据库，运维成本经常超过业务本身。

Memvid 的解法是把整条管线收进一个文件：

```text
传统 RAG：
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ 文档摄取  │ → │ 嵌入服务  │ → │  向量库   │ → │ API 服务  │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
    四个组件、三次网络往返、四份运维

Memvid：
┌─────────────────────────────────────────────┐
│                knowledge.mv2                 │
│   帧 + 嵌入 + 词法/向量/时间索引 + WAL        │
└─────────────────────────────────────────────┘
    一个文件、进程内检索、拷贝即迁移
```

代价同样清楚：写入吞吐受单机限制，容量由授权档位封顶（见第六节），多进程并发写入不被支持。它是「每台机器一份记忆」的模型，不是共享存储。

**什么是 RAG？** 检索增强生成（Retrieval-Augmented Generation）指在语言模型生成回答前，先从外部知识库检索相关内容拼进上下文。传统实现需要独立的向量数据库做检索那一环。

## 四、核心概念：Smart Frames 与 .mv2 格式

### 4.1 Smart Frames

Memvid 从视频编码借的是**组织方式**而不是存储介质：记忆被组织成可追加的 Smart Frames 序列。按官方 README 的定义，Smart Frame 是一个不可变单元，存储内容、时间戳、校验和与基本元数据；帧按组打包，便于压缩、索引和并行读取。

对照源码里的 `Frame` 结构（`src/types/frame.rs`），一帧实际包含：

| 字段组 | 内容 |
|--------|------|
| 标识 | `id`（帧号）、`timestamp`、`anchor_ts`（时间锚点） |
| 定位 | `payload_offset` / `payload_length`（数据段内偏移与长度）、`checksum`（SHA-256） |
| 描述 | `title`、`uri`、`kind`、`track`、`tags`、`labels`、`metadata`、`content_dates` |
| 结构 | `chunk_manifest`（分块清单）、`parent_id` / `chunk_index`（PDF 等父文档与分块关系）、`role` |

这个设计直接带来四个性质：

- **只追加**：新数据追加写，已提交的帧不可变，崩溃后已提交内容不受影响；
- **时间旅行**：每帧带时间戳，可以查询任意历史时点的记忆状态；
- **可演进追踪**：同一实体的信息随时间形成序列，能回答「当时它是什么」；
- **高效压缩**：数据段用 zstd/LZ4 压缩（Cargo.toml 依赖），向量另有乘积量化（`vec_pq.rs`）可选，官方把这套按内容自动选型升级的机制称作 Codec Intelligence，思路取自视频编码的帧间压缩。

### 4.2 .mv2 文件格式

`MV2_SPEC.md`（v2.1）定义了完整的文件布局：

```text
┌────────────────────────────┐
│ Header (4 KB)              │  魔数、版本、WAL 位置与进度
├────────────────────────────┤
│ Embedded WAL (1–64 MB)     │  崩溃恢复预写日志
├────────────────────────────┤
│ Data Segments              │  压缩后的帧数据
├────────────────────────────┤
│ Lex Index                  │  Tantivy 全文索引（BM25）
├────────────────────────────┤
│ Vec Index                  │  HNSW 向量索引
├────────────────────────────┤
│ Time Index                 │  时间线索引
├────────────────────────────┤
│ TOC (Footer)               │  段目录 + 各段校验和
└────────────────────────────┘
```

Header 固定 4096 字节，关键字段：偏移 0 处的魔数 `MV2\0`（`0x4D 0x56 0x32 0x00`），格式版本与规范版本号，`wal_offset`（恒为 4096）、`wal_size`、`wal_sequence`（当前 WAL 序号），以及 TOC 段的 SHA-256 校验和。多字节整数一律小端。

WAL 是崩溃恢复的关键，条目格式为：8 字节序号 + 1 字节类型 + 4 字节载荷长度 + 载荷 + 4 字节 CRC32。类型覆盖帧追加（`0x01`）、更新（`0x02`）、删除墓碑（`0x03`）和索引更新（`0x04`）。WAL 容量按文件目标容量分档：小于 100 MB 用 1 MB，小于 1 GB 用 4 MB，小于 10 GB 用 16 MB，更大用 64 MB；占用超过 75% 或每 1000 笔事务触发一次检查点，把 WAL 合并进正式段。

整份文件自包含：没有 `.wal`、`.lock`、`.shm` 或任何旁车文件，拷贝一个 `.mv2` 就是完整备份。

## 五、快速开始

### 5.1 安装

| 形态 | 安装命令 | 环境要求 |
|-----|----------|---------|
| **CLI** | `npm install -g memvid-cli` | Node ≥ 14；命令名是 `memvid` |
| **Node.js SDK** | `npm install @memvid/sdk` | Node ≥ 14 |
| **Python SDK** | `pip install memvid-sdk` | Python ≥ 3.8，内置原生绑定 |
| **Rust** | `cargo add memvid-core` | Rust ≥ 1.85 |

npm 包 `memvid-cli` 是安装器，按平台拉取预编译 Rust 二进制（macOS arm64/x64、Linux x64/arm64、Windows x64）。macOS 与 Linux 也可以用官方安装脚本（会调用 Homebrew/apt/dnf 等系统包管理器）：`curl -fsSL https://get.memvid.com | sh`。文档提取基于 Apache Tika（二进制内打包了 `libtika_native.dylib`），PDF、DOCX、XLSX、PPTX、HTML、Markdown、CSV、JSON 乃至带 OCR 的图片都能摄取。

Windows 有一个已知限制：本地 ONNX 嵌入模型不可用，语义检索需改用 OpenAI 嵌入（CLI 文档明确说明）。

### 5.2 CLI：五分钟跑通

以下命令在 memvid-cli 2.0.140 上实测：

```bash
# 创建记忆文件（默认 Free 档，容量 50 MB）
memvid create knowledge.mv2

# 写入内容：正文从 stdin 读入，元数据用 flag 传
echo "Memvid is a single-file memory layer for AI agents." | memvid put knowledge.mv2 --title "Intro"

# 从目录批量摄取整批文档（put --input 只收单个文件；模型用 --embedding-model 指定）
memvid put-many knowledge.mv2 --input ./docs/ --embedding-model bge-small

# 检索：默认混合模式（词法 + 语义重排），返回 top-k
memvid find knowledge.mv2 --query "memory layer" --top-k 5

# 问答式检索（需要 OPENAI_API_KEY 做答案合成；--no-llm 则只检索不合成）
memvid ask knowledge.mv2 --question "What is Memvid?"
memvid ask knowledge.mv2 --question "What is Memvid?" --no-llm --sources

# 查看容量、帧数与索引状态
memvid stats knowledge.mv2
```

实测输出长这样：

```text
$ memvid create demo.mv2
✓ Created memory at demo.mv2
  Tier: Free
  Capacity: 50.0 MB (52428800 bytes)

$ memvid find demo.mv2 --query "memory layer"
mode: Hybrid (lexical + semantic)   k=8   time: 1 ms
hits: 1 (showing 1)
#1 mv2://frames/07933a1e-... (matches 4)
  Title: Intro
  Relevance: 100%
```

注意 `put` 的正文走 **stdin**（或 `--input <PATH>` 指定文件），没有 `--text` 参数；`--timestamp` 接受 Unix 秒或 "Jan 15, 2023" 这类人类可读日期。

### 5.3 Rust 快速上手

这段与仓库 README 逐字一致：

```rust
use memvid_core::{Memvid, PutOptions, SearchRequest};

fn main() -> memvid_core::Result<()> {
    // 创建新的记忆文件
    let mut mem = Memvid::create("knowledge.mv2")?;

    // 添加文档（带元数据）
    let opts = PutOptions::builder()
        .title("Meeting Notes")
        .uri("mv2://meetings/2024-01-15")
        .tag("project", "alpha")
        .build();
    mem.put_bytes_with_options(b"Q4 planning discussion...", opts)?;
    mem.commit()?;

    // 搜索
    let response = mem.search(SearchRequest {
        query: "planning".into(),
        top_k: 10,
        snippet_chars: 200,
        ..Default::default()
    })?;

    for hit in response.hits {
        println!("{}: {}", hit.title.unwrap_or_default(), hit.text);
    }

    Ok(())
}
```

写入后必须 `commit()`，数据才落盘成段。`put_bytes_with_options` 返回帧号（`Result<u64>`），可用于后续按帧删除或查看。

### 5.4 Python 快速上手

以官方文档的推荐写法为准。两个容易踩的坑：`create()` 对已存在的文件会**直接覆盖**；`use()` 的参数顺序是 kind 在前、path 在后。

```python
import os
from memvid_sdk import create, use

path = "knowledge.mv2"

# 防止 create() 覆盖已有数据
if os.path.exists(path):
    mem = use("basic", path)   # 打开已有文件（kind 在前！）
else:
    mem = create(path)         # 新建文件

# 写入：词法索引默认开启
mem.put(
    title="会议记录",
    label="notes",
    metadata={"source": "slack"},
    text="Alice mentioned she works at Anthropic...",
)

# 检索立即生效；返回 dict，命中在 hits 键下
results = mem.find("who works at AI companies?", k=5, mode="lex")
print(results["hits"])

# 问答
answer = mem.ask("What does Alice do?", k=5, mode="lex")
print(answer["answer"])

# 结束时 seal（提交变更）
mem.seal()
```

### 5.5 Node.js 快速上手

Node SDK 用普通对象传参，没有 `PutOptions` 类：

```typescript
import { create } from "@memvid/sdk";

const mem = await create("knowledge.mv2");

await mem.put({
  title: "会议记录",
  label: "meeting",
  text: "Q4 planning discussion...",
});

const results = await mem.find("planning", { k: 10 });
console.log(results.hits);

// 密封文件（只读化）
await mem.seal();
```

`@memvid/sdk` 还内置了一批框架适配器，可直接把记忆挂进 LangChain、LlamaIndex、CrewAI、Vercel AI、OpenAI、AutoGen、Haystack、LangGraph、Semantic Kernel、Google ADK，或作为 MCP server 暴露给支持工具调用的 Agent（Python SDK 也有对应的 `adapters` 模块）。

## 六、核心功能详解

### 6.1 检索模式与自适应召回

三个 SDK 和 CLI 的检索入口都围绕同一个 `mode` 参数：

| 模式 | 行为 | 依赖 |
|------|------|------|
| `lex` | 纯词法检索，Tantivy BM25 | 无，开箱即用 |
| `sem` | 纯向量语义检索 | 摄入时生成过嵌入 |
| `auto`（默认） | 词法检索 + 语义重排 | 摄入与查询侧都有嵌入 |
| `clip` | 图文互搜（文本查图） | `clip` feature |

语义检索的嵌入既可以在摄入时生成（`put --embedding -m bge-small`，`--embedding` 是开关、`-m` 选模型），也可以在查询时现场计算：CLI 用 `--embedding-model`，Node/Python SDK 的 `find` 接受 `embedder` 参数直接注入自定义嵌入提供方，或传 `queryEmbedding` 用预计算向量（离线安全）。

CLI 的 `find` 还有两组值得知道的开关。**自适应截止**默认开启（`--adaptive-strategy combined`）：按相关性曲线自动决定返回几条，`--min-relevancy 0.5` 表示低于最高分 50% 的结果被剔除，`--max-k 100` 限制过度召回上限，`--no-adaptive` 回到固定 top-k。**图感知过滤**（`--graph`/`--hybrid`）则借助记忆卡里的实体关系先按 "who lives in X" 这类关系模式过滤再排序。

此外还有 sketch 预过滤（快速剪枝候选段，`SearchRequest.no_sketch` 可关闭）和按 `uri`/`scope` 前缀圈定检索范围的能力。

### 6.2 时间旅行与 Session Replay

时间旅行有两层机制。

**第一层是查询时回溯**。`find`、`timeline`、`stats` 都接受 `--as-of-frame <N>` 或 `--as-of-ts <UNIX_TS>`，把视图过滤到该帧号/时间戳之前的状态——「去年十月这条知识库认为……」可以直接查：

```bash
memvid find knowledge.mv2 --query "config" --as-of-frame 100
memvid timeline knowledge.mv2 --as-of-ts 1704067200
memvid stats knowledge.mv2 --as-of-frame 50
```

Node/Python SDK 的 `find` 对应 `asOfFrame` / `as_of_frame` 参数；Rust 侧是 `SearchRequest` 的同名字段。

**第二层是 Session Replay**。`memvid session start` 开始录制之后的所有 `put`/`find`/`ask` 操作，`session end` 落盘，之后可以 `session replay` 重放：调试模式重新执行检索（验证「今天重跑还能不能召回」），审计模式用冻结上下文重现当时的答案（合规审计用），还能换模型 A/B 对比、检查接地（grounding）检测幻觉。会话可以打检查点、对比两次会话差异。

```bash
memvid session start demo.mv2 --name "experiment-1"
# ... 正常 put / find / ask ...
memvid session end demo.mv2
memvid session list demo.mv2
memvid session replay demo.mv2 --session <id> --use-model openai:gpt-4o
memvid session replay demo.mv2 --session <id> --audit --diff   # 审计模式，冻结上下文并对比差异
```

注意：README 营销语境里的 "branch"（分支演化）在当前 v2 代码中没有对应的分支 API——演化追踪靠帧的时间序列与回放机制实现。读到「创建记忆分支」类描述时，以你手上版本的 API 为准。

### 6.3 记忆卡与实体状态

默认开启的 `extract_triplets` 让摄入过程自动从文本抽取「主-谓-宾」三元组，存成 Memory Cards（记忆卡）。这带来一组 O(1) 的结构化查询能力：

```bash
# 查询实体当前状态（把散落在各帧里的信息聚合成最新画像）
memvid state knowledge.mv2 --entity "Alice"
memvid state knowledge.mv2 --entity "Alice" --slot employer

# 浏览与审计事实
memvid memories knowledge.mv2
memvid facts knowledge.mv2          # 带来源的变更审计
memvid export knowledge.mv2 --format nt   # 导出 N-Triples / JSON / CSV
```

Node/Python SDK 同名方法为 `state(entity, slot?)`，返回 `{ entity, found, slots }` 结构。这组能力解决的是 Agent 记忆的经典痛点：用户半年前说自己在 A 公司、上个月换到 B 公司，`state` 直接给出当前值，而 `facts` 保留完整变更历史和出处。

底层的实体关系图在源码里叫 Logic Mesh，`follow` 命令可以沿关系边遍历，配合 `find --graph` 做图感知检索：

```bash
memvid follow traverse k.mv2 --start "Alice" --link "manager" --hops 2
memvid follow entities k.mv2    # 列出全部实体
memvid follow stats k.mv2       # 关系图统计
```

### 6.4 加密胶囊与访问控制

`encryption` feature 提供密码加密胶囊（`.mv2e`）：AES-256-GCM 做内容加密，Argon2id 做密钥派生（参数按 OWASP 2024 建议）。CLI 命令：

```bash
# 加密；默认删除原 .mv2，--keep-original 保留
memvid lock knowledge.mv2 --out knowledge.mv2e

# 解密回 .mv2
memvid unlock knowledge.mv2e --out knowledge.mv2
```

CI/脚本场景用 `--password-stdin` 传密码，避免进 shell 历史。Node/Python SDK 顶层都有对应的 `lock(path, { password, output })` / `unlock(...)` 函数。密码丢失即数据不可恢复——没有后门，这也是把它用于敏感数据的先决条件：密钥管理要先于加密启用。

更细粒度的访问控制是 ACL（Permission-Aware Retrieval）：`SearchRequest` 带 `acl_context` 与 `acl_enforcement_mode`（`audit` 只审计、`enforce` 强制过滤），可以按调用者身份裁剪可见帧。另有内置的 PII 检测与掩码能力（`maskPii`）。

### 6.5 容量与票证：单文件也有配额

这是选型时最容易忽略的机制：**`.mv2` 文件有硬容量上限，由 Ed25519 签名的票证（ticket）控制**。本地 `create` 出来的文件默认是 Free 档：

| 计划 | 总容量 | 单文件上限 | 价格 |
|------|--------|-----------|------|
| Free | 50 MB | 50 MB | 免费 |
| Starter | 25 GB | 5 GB | $9.99/月 |
| Pro | 125 GB | 25 GB | $49.99/月 |
| Enterprise | 不限 | 不限 | 联系官方 |

容量状态可以随时查：`memvid stats` 会打印 "Usage: 70.4 KB used / 50.0 MB total"，超限写入会报容量错误。需要扩容时在官方控制台获取 `mv2_*` API Key（环境变量 `MEMVID_API_KEY`），通过 `memvid tickets` / SDK 的 `sync_tickets` 同步票证到文件。换言之，「免费自托管」的合理预期是单文件 50 MB 的小规模记忆；更大的容量是订阅服务。

## 七、Feature Flags

Rust 侧 `memvid-core` 按需编译，依赖最小化（README 原表）：

| Feature | 说明 |
|---------|------|
| `lex` | BM25 全文检索（Tantivy） |
| `pdf_extract` | 纯 Rust PDF 文本提取 |
| `vec` | 向量检索（HNSW + 本地 ONNX 文本嵌入） |
| `clip` | CLIP 视觉嵌入，图片搜索 |
| `whisper` | Whisper 音频转录 |
| `api_embed` | OpenAI 云端嵌入（需网络） |
| `temporal_track` | 自然语言时间解析（"last Tuesday"） |
| `parallel_segments` | 多线程摄入 |
| `encryption` | 密码加密胶囊（.mv2e） |
| `symspell_cleanup` | PDF 文本修复（把 "emp lo yee" 修成 "employee"） |

另有未列入 README 表的 `extractous` feature（Cargo.toml 注释注明）：启用后走 Tika 原生提取，支持 PDF/DOCX 等完整文档格式，但 GraalVM 原生编译在 Windows ARM/WSL2 ARM 上不可用。

推荐组合：最小化 `["lex"]`；通用 `["lex", "vec"]`；PDF 处理加 `pdf_extract`；图片/音频分别加 `clip`/`whisper`；合规场景加 `encryption`。

```toml
[dependencies]
memvid-core = { version = "2.0", features = ["lex", "vec", "temporal_track"] }
```

## 八、多模态支持

### 8.1 Whisper 音频转录

`whisper` feature 内置转录能力，README 原表：

| 模型 | 大小 | 速度 | 适用场景 |
|------|------|------|----------|
| `whisper-small-en` | 244 MB | 最慢 | 最高精度（默认） |
| `whisper-tiny-en` | 75 MB | 快 | 均衡 |
| `whisper-tiny-en-q8k` | 19 MB | 最快 | 快速测试、资源受限 |

```rust
use memvid_core::{WhisperConfig, WhisperTranscriber};

// 默认 FP32 small；with_quantization() 用量化 tiny；with_model() 指定型号
let config = WhisperConfig::default();
let transcriber = WhisperTranscriber::new(&config)?;
let result = transcriber.transcribe_file("audio.mp3")?;
println!("{}", result.text);
```

环境变量 `MEMVID_WHISPER_MODEL` 可在不动代码的情况下切模型。

### 8.2 CLIP 视觉搜索

`clip` feature 支持以文搜图。仓库自带可运行的示例：

```bash
cargo run --example clip_visual_search --features clip
```

### 8.3 文本嵌入模型

`vec` feature 的本地嵌入走 ONNX，模型需手动下载到 `~/.cache/memvid/text-models/`（README 给了 HuggingFace 直链），README 原表：

| 模型 | 维度 | 大小 | 定位 |
|------|------|------|------|
| `bge-small-en-v1.5` | 384 | ~120MB | 默认，快 |
| `bge-base-en-v1.5` | 768 | ~420MB | 更高质量 |
| `nomic-embed-text-v1.5` | 768 | ~530MB | 多用途 |
| `gte-large` | 1024 | ~1.3GB | 最高质量 |

`api_embed` feature 走 OpenAI：`text-embedding-3-small`（1536 维，默认）、`text-embedding-3-large`（3072 维）、`text-embedding-ada-002`（遗留）。嵌入模型一旦混用会污染索引，可以用 `set_vec_model("bge-small-en-v1.5")` 把实例绑定到指定模型，之后换模型会直接报 `ModelMismatch` 错误——这是防止「用 BGE 索引配 OpenAI 查询」的显式保险。

## 九、使用场景与适用边界

### 9.1 官方列出的使用场景

README 的 Use Cases 清单：长期运行 Agent、企业知识库、离线优先系统、代码库理解、客服 Agent、工作流自动化、销售与市场 Copilot、个人知识助手、医疗/法律/金融 Agent、可审计可调试的工作流，以及自定义应用。共同特征是：**单机或单实例、本地数据、追加快写、按语义和实体检索**。

### 9.2 不适用场景

| 场景 | 原因 | 更合适的选择 |
|------|------|--------------|
| 超大规模（TB/PB 级）共享语料 | 单文件模型 + 容量档位上限 | 专用向量数据库（Qdrant、Milvus 等） |
| 多进程/多机并发写入 | 单写者文件锁模型 | PostgreSQL + pgvector 等服务端存储 |
| 高 QPS 常驻检索服务 | 稳态延迟不占优（见第二节） | Weaviate 等专用引擎 |
| 强事务、多表关联 | 无跨帧事务与关系约束 | 传统关系型数据库 |
| 需要合规**认证**而非机制 | 官方未宣称 HIPAA/SOC 等认证 | 以厂商合规文档为准 |

最后一条值得展开：加密、本地处理、审计回放这些**机制**对合规工作流有实际价值，但官方没有宣称通过任何第三方合规认证，采购材料里不要替它写。

## 十、实践建议

### 10.1 摄入优化

```rust
// Rust 侧：批量并行构建（parallel_segments feature）
use memvid_core::BuildOpts;

mem.put_parallel(&pdf_paths, BuildOpts::default())?;  // 多文件并行生成段
mem.commit_parallel(BuildOpts::default())?;           // 并行提交
```

`BuildOpts` 可调段大小（默认 2048 token 或 4 页）、工作线程数、zstd 压缩级别（默认 3）与内存上限（默认 4 GiB）。

几个源码里可以直接看到的摄入参数：`PutOptions::dedup(true)` 按内容 BLAKE3 哈希跳过重复帧；`instant_index` 默认开启（写入后立即软提交 Tantivy，秒级可检索）；`extraction_budget_ms` 默认 350ms，控制单文档提取时间预算以保障摄入吞吐。文档切分方面，Node SDK 的 `putFile` 默认 chunkSize 1000 字符，PDF 每页、表格每张会成为带父子关系的独立帧。

### 10.2 检索调优

语义检索想要生效，摄入和查询两端要用**同一个**嵌入模型（或交给 `mode=auto` 统一处理）。高质量语料先用 `--mode lex` 验证词法召回是否正常，再排查嵌入链路——大部分「搜不到」是模型不一致或模型文件没下载，而不是索引坏了。精确短语匹配靠 BM25，模糊语义靠向量，`auto` 模式的自适应截止通常比手动调 top-k 更稳。

### 10.3 维护与备份

```bash
# 完整性校验（--deep 检查全部校验和）
memvid verify knowledge.mv2 --deep

# 修复与优化：重建索引、真空压缩
memvid doctor knowledge.mv2 --rebuild-lex-index
memvid doctor knowledge.mv2 --vacuum
```

删除是墓碑标记，空间在 doctor 的 vacuum 后回收。备份就是拷文件；生产环境建议配合 `--keep-original` 使用 `lock`（它默认会删掉原文件），并在 CI 里用 `--password-stdin` 传密码：

```yaml
- name: 加密备份
  env:
    MEMVID_PASSWORD: ${{ secrets.MEMVID_PASSWORD }}
  run: |
    echo "$MEMVID_PASSWORD" | memvid lock memory.mv2 --password-stdin --out backup.mv2e --keep-original
```

## 十一、API 参考

### 11.1 CLI 命令

`memvid --help` 实测共 40 余个子命令，按用途分组：

| 分组 | 命令 |
|------|------|
| 数据 | `create` `open` `put` `put-many` `update` `delete` `view` `correct` `api-fetch` |
| 检索 | `find` `vec-search` `ask` `audit` `when`（自然语言时间查询） |
| 浏览 | `timeline` `stats` `tables`（PDF 表格提取） |
| 实体 | `enrich` `memories` `state` `facts` `export` `schema` `follow` |
| 时间旅行 | `session start/end/list/view/checkpoint/delete/save/load/replay/compare` |
| 维护 | `verify` `doctor` `process-queue` `verify-single-file` `sketch`（候选剪枝索引） |
| 安全与容量 | `lock` `unlock` `who` `nudge` `tickets` `plan` `binding` |
| 配置 | `config` `status` `models` `version` |

常用 flag：`find --query --top-k（默认 8）--mode auto/lex/sem/clip --as-of-frame/--as-of-ts --json`；`put --input --title --timestamp --label --embedding-model`；`ask --question --context-only`；`lock/unlock --password-stdin --out --keep-original`。环境变量：`OPENAI_API_KEY`、`OPENAI_BASE_URL`、`NVIDIA_API_KEY`、`MEMVID_MODELS_DIR`、`MEMVID_API_KEY`。

### 11.2 Rust SDK（memvid-core 2.0）

```rust
use memvid_core::{Memvid, SearchRequest, TimelineQuery};

// 生命周期
let mut mem = Memvid::create("k.mv2")?;      // 新建
let mut mem = Memvid::open("k.mv2")?;        // 打开（可写）
let mem = Memvid::open_read_only("k.mv2")?;  // 只读

// 写入：返回帧号
let frame_id = mem.put_bytes(b"content")?;
let frame_id = mem.put_bytes_with_options(b"content", opts)?;
mem.commit()?;                               // 落盘
mem.commit_skip_indexes()?;                  // 跳过索引重建的快速提交

// 检索：SearchRequest 字段
//   query, top_k, snippet_chars, uri, scope, cursor,
//   temporal（temporal_track feature）, as_of_frame, as_of_ts,
//   no_sketch, acl_context, acl_enforcement_mode
let resp = mem.search(SearchRequest { ..Default::default() })?;

// 专项检索与其他
mem.search_lex("query", 10)?;                          // 纯词法
mem.timeline(TimelineQuery::builder().limit(20).build())?; // 时间线
mem.set_vec_model("bge-small-en-v1.5")?;     // 绑定嵌入模型
mem.path();                                  // 文件路径
```

### 11.3 Python SDK（memvid-sdk 2.0.160）

```python
from memvid_sdk import create, use, lock, unlock

mem = create("k.mv2")            # 新建（覆盖已有文件！）
mem = use("basic", "k.mv2")      # 打开（kind 在前，path 在后）

mem.put(title="T", text="...", tags=["a"], timestamp="2026-01-15")
mem.put_file("doc.pdf")          # 文档摄取，按页/表切帧

res = mem.find("query", k=10, snippet_chars=480, mode="auto",
               as_of_frame=100)  # 返回 dict，命中在 res["hits"]
ans = mem.ask("question", k=5)   # 返回 dict，答案在 ans["answer"]

mem.state("Alice")               # 实体状态（O(1)）
mem.session_start("s1")          # 录制会话 → session_end / session_replay
mem.sync_tickets(api_key="mv2_...")  # 容量票证同步
lock("k.mv2", password="...", output="k.mv2e")   # 加密胶囊
```

### 11.4 Node.js SDK（@memvid/sdk 2.0.160）

```typescript
import { create, open, use, lock, unlock, configure } from "@memvid/sdk";

const mem = await create("k.mv2");

await mem.put({ title: "T", text: "...", tags: ["a"] });   // PutInput 普通对象
await mem.putFile("doc.pdf", { chunkSize: 1000 });

await mem.find("query", { k: 10, mode: "auto", asOfFrame: 100 });
await mem.ask("question", { k: 5 });

await mem.state("Alice");        // { entity, found, slots }
await mem.timeline({ limit: 20 });
await mem.stats();
await mem.verify();              // 对应 CLI verify
await mem.doctor({ vacuum: true });
await mem.sessionStart("s1");    // 会话录制 → sessionEnd / sessionReplay
await mem.seal();                // 密封
```

`Memvid` 接口还有 `remove`（按帧号墓碑删除）、`correct`（存入带检索加权的更正）、`view/viewByUri`（取全文）、`extractAsset`（抽取原始文件）、`addMemoryCards`（写入结构化事实）等，完整清单见 `dist/types.d.ts`。

## 十二、VS 其他方案

把官方可复现基准（第二节）和架构差异合到一张选型表：

| 维度 | Memvid | Chroma | LanceDB | Qdrant | Weaviate |
|------|--------|--------|---------|--------|----------|
| 部署形态 | 进程内单文件 | 嵌入式/服务器 | 嵌入式/服务器 | 服务器 | 服务器 |
| Top-1 准确率（官方基准） | **92.72%** | 78.24% | 84.24% | 84.24% | 80.68% |
| 查询 p50 | 16.0ms | 55.6ms | 16.0ms | 28.0ms | **5.3ms** |
| 冷启动 | **0.5ms** | 66.3ms | 72.4ms | 71.8ms | 147.7ms |
| 时间回溯 | 查询级 as-of + 会话回放 | ❌ | 版本级 time travel | ❌ | ❌ |
| 本地加密胶囊 | ✅（AES-256-GCM + Argon2id） | 依赖部署层 | 云版提供 | 依赖部署层 | 有加密模块 |
| 许可证 | Apache-2.0 | Apache-2.0 | Apache-2.0 | Apache-2.0 | BSD-3 |

两点提醒：其一，这份准确率与延迟数据全部来自 Memvid 官方基准，硬件、数据集、配置都是它指定的，竞品未背书，选型前建议用 `benchmarks/python` 套件在自己的数据上复测；其二，「时间回溯」一列不要读成 Memvid 独有——LanceDB 也有版本级 time travel，Memvid 的差异在于查询级 as-of 过滤与操作级会话回放的组合。

## 十三、故障排除

| 症状 | 可能原因 | 处理 |
|------|----------|------|
| `create` 或 `put` 报容量错误 | Free 档 50 MB 上限，或票证未同步 | `stats` 看用量；清理或删帧后 `doctor --vacuum`；需要更大容量见 6.5 节 |
| 语义检索无结果 | 嵌入模型文件未下载 / 两端模型不一致 / Windows 无本地嵌入 | 确认 `~/.cache/memvid/text-models/`；统一 `--embedding-model`；Windows 用 `openai-small` |
| 词法也搜不到 | 未提交，或文本提取失败 | 确认 `commit()`/`seal()`；`view <frame>` 看帧内容是否为空 |
| 换嵌入模型后报 ModelMismatch | 索引已绑定其他模型 | 换回原模型，或重建索引 |
| 打开文件报锁定 | 其他进程持有写锁 | `memvid who <file>` 查持有者，`nudge` 请求其释放；确认无写入后强收 |
| 文件损坏 / 索引异常 | 崩溃或磁盘问题 | `verify --deep` 定位；`doctor --rebuild-lex-index` / `--vacuum` 修复 |
| `.mv2e` 密码丢失 | Argon2id 派生无后门 | 不可恢复，依赖密钥管理预防 |

排查命令速查：

```bash
memvid stats k.mv2          # 容量、帧数、索引状态
memvid verify k.mv2 --deep  # 完整性（头部/TOC/WAL/时间索引排序）
memvid doctor k.mv2         # 诊断与修复（dry-run 可先看方案）
memvid open k.mv2           # 查看元数据与清单
```

错误的完整代码清单见官方 [Error Code Reference](https://docs.memvid.com/errors/reference)，每个错误码附建议处置。

## 十四、FAQ

### Q1：Memvid 和传统向量数据库的核心区别是什么？

架构位置不同。向量数据库是独立服务，存算分离、跨网络访问；Memvid 是进程内嵌入式引擎，整条「存储+索引+检索」收进一个文件，没有服务进程和网络往返。它是向量库的替代品吗？在「单机 Agent 记忆」这个粒度上是；在「多机共享、高 QPS、海量数据」的粒度上不是，见第二节与第九节。

### Q2：.mv2 文件有大小限制吗？

有，而且是硬限制：容量由签名票证决定，本地默认 Free 档 50 MB，付费档单文件上限 5 GB（Starter）到 25 GB（Pro）。官方没有给出超出档位后的「建议值」——到达档位上限就该拆文件或升档，而不是硬塞。

### Q3：支持并发吗？

单进程多线程没问题（`parallel_segments` 加速摄入、并行读段也是设计目标）。跨进程写入是单写者模型：文件锁保证同一时刻只有一个写者，`memvid who` 查看持锁进程，`nudge` 请求其在安全时释放。多机共享写入请换服务端存储。

### Q4：词法、语义、混合怎么选？

精确关键词（代码标识符、错误码、人名）用 `lex`；语义模糊查询用 `sem`（前提是摄入时生成了嵌入）；不确定就 `auto`（默认），它以词法打底、语义重排。注意 `sem`/`auto` 需要查询侧有嵌入——本地模型首次使用会下载，离线环境可在查询时传预计算向量（SDK 的 `queryEmbedding`）。

### Q5：加密怎么用？丢了密码怎么办？

`memvid lock k.mv2 --out k.mv2e`（或 SDK 的 `lock()`），AES-256-GCM + Argon2id。密码不落盘、无后门，丢了即数据不可恢复——加密前先把密码进密钥管理。

### Q6：已有 JSONL 数据怎么导入？

用 Python SDK 循环 `put`：

```python
import json
from memvid_sdk import create

mem = create("imported.mv2")
with open("data.jsonl", encoding="utf-8") as f:
    for line in f:
        item = json.loads(line)
        mem.put(title=item["title"], text=item["content"])
mem.seal()
```

十万行以上的批量导入建议用 `put_many` / `put-many` 批量接口，CLI 侧加 `--embedding-model bge-small` 一次生成语义索引。

### Q7：怎么备份？

单文件的好处在这里兑现：备份就是拷贝。Rust 侧 `mem.path()` 拿路径后 `fs::copy`，其他形态直接复制文件。要注意加密文件的备份策略——`.mv2e` 本身就可安全外发，明文 `.mv2` 备份要控制存放位置。

### Q8：能用于医疗、法律、金融场景吗？

机制层面：数据全程本地处理、AES-256-GCM 加密胶囊、会话审计回放、PII 掩码，这些对合规工作流是实打实的能力。但要分清「机制」与「认证」：官方没有宣称通过 HIPAA/GDPR/SOC 2 等第三方合规认证，这类场景的采购结论需要你的合规团队基于机制自行评估。

## 十五、资源链接

| 资源 | 链接 |
|------|------|
| 官网 | https://www.memvid.com |
| 在线沙盒 | https://sandbox.memvid.com |
| 文档 | https://docs.memvid.com |
| 可复现基准 | https://docs.memvid.com/introduction/benchmarks |
| 容量与计划 | https://docs.memvid.com/concepts/capacity-and-plans |
| 时间旅行回放 | https://docs.memvid.com/concepts/time-travel-replay |
| v1 弃用说明 | https://docs.memvid.com/memvid-v1-deprecation |
| 错误码参考 | https://docs.memvid.com/errors/reference |
| GitHub | https://github.com/memvid/memvid |
| Discord | https://discord.gg/7RUve6Zrrv |
| Crates.io | https://crates.io/crates/memvid-core |
| docs.rs | https://docs.rs/memvid-core |

## 十六、总结与进阶路径

Memvid 把「给 Agent 一份可携带的长期记忆」做成了一件事：一个 `.mv2` 文件。词法 + 语义 + 时间三路索引、O(1) 实体状态、查询级时间旅行和会话回放、AES-256-GCM 加密，全部在进程内完成，冷启动 0.5ms。代价是单机单写者模型与容量档位——免费档 50 MB，更大的容量走订阅票证。选型判断可以压缩成一句话：**数据是每台机器自己的、规模在档位内、要离线和可审计，它几乎是最省心的方案；要共享写入或常驻高并发检索，用服务端向量库。**

### 进阶路径

| 级别 | 主题 | 推荐资源 |
|------|------|----------|
| 入门 | 创建、写入、检索 | 官方沙盒（sandbox.memvid.com）；[5-Minute Quickstart](https://docs.memvid.com/quickstart/five-minute-guide) |
| 进阶 | 自适应检索与图搜索 | [Adaptive Retrieval](https://docs.memvid.com/concepts/adaptive-retrieval)、[Graph Search & Logic Mesh](https://docs.memvid.com/concepts/graph-search) |
| 深入 | 时间旅行与审计 | [Session Replay](https://docs.memvid.com/concepts/time-travel-replay) |
| 深入 | 文件格式内幕 | 仓库 `MV2_SPEC.md`（v2.1，含 Header/WAL/TOC 逐字节定义） |
| 专家 | 性能调优与基准复测 | [Performance Tuning](https://docs.memvid.com/concepts/performance-tuning)、`benchmarks/python` 套件 |

### 资料与口径说明

- 版本锚点：memvid/memvid main 分支提交 `e6bd9f7`（2026-07-14）、release v2.0.140（2026-05-27）、memvid-cli 2.0.140 实测（macOS arm64）；npm/PyPI 分发包版本号 2.0.160。
- GitHub 数据（stars/forks/contributors）为 2026-09-28 API 读数；语言占比按 languages API 字节数计算。
- CLI 命令与 flag 均在 2.0.140 二进制上实测核对；Python/Node SDK 签名分别对照 memvid-sdk 2.0.160 源码包与 @memvid/sdk 2.0.160 的 `types.d.ts`。
- README 头条性能数字（0.025ms P50、1,372× 等）为官方宣传口径，官方可复现基准另有方法学完整的数字，两组数字在第二节分开呈现。
