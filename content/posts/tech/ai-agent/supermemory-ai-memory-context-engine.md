---
title: "Supermemory：从入门到精通 AI 记忆与上下文引擎"
date: "2026-03-31T01:20:00+08:00"
slug: supermemory-ai-memory-context-engine
aliases:
  - /posts/tech/supermemory-ai-memory-context-engine/
categories: ["技术笔记"]
tags: ["Supermemory", "AI记忆", "RAG", "上下文管理", "智能体", "向量数据库"]
description: "Supermemory 在 LongMemEval/LoCoMo/ConvoMem 三大 AI 记忆基准测试中全部排名第一。本文拆解其 Memory Engine、User Profiles、Hybrid Search 的工作机制，并给出 API 用法和框架集成方案。"
---

# Supermemory：从入门到精通 AI 记忆与上下文引擎

AI 记忆系统的核心矛盾不是"存不下"，而是"存了之后查不出来该用的那条"。Supermemory 在这件事上做对了一件事：把记忆检索和用户画像维护合并成一条通路，而不是让开发者在 RAG 和 Memory 两套系统之间来回切换。

本文假设你已有 AI 应用开发经验，预计阅读 30 分钟。读完你会理解 Supermemory 各子系统如何协作，以及它在什么场景下比传统 RAG 更合适。

> 难度：⭐⭐⭐⭐ | 预计动手时间：1-2 小时（入门），4-6 小时（精通）

---

## 一、项目概述

### 1.1 Supermemory 解决什么问题

[Supermemory](https://github.com/supermemoryai/supermemory)（20.5k Stars，MIT 协议）解决的是 AI 对话中的"跨会话失忆"：用户今天说过的事情，明天 AI 就忘了。它解决的是失忆链条上的三个具体问题：

1. 对话结束后，提取出的用户事实散落在日志里，下次对话时没有机制把它们注入到上下文窗口。
2. 同一个用户的前后说法可能矛盾（"我住 NYC" → "我刚搬到 SF"），传统方案要么全保留要么人工清理。
3. 临时信息（"明天有考试"）会一直占用存储，永远不会过期。

Supermemory 的方案是把这三个问题合并到一条处理链里：Memory Engine 负责提取和更新事实，User Profiles 负责聚合静态/动态上下文，Hybrid Search 负责在检索阶段同时返回知识库文档和用户个性化记忆。

```mermaid
graph LR
    A["用户对话"] --> B["Supermemory"]
    B --> C["Memory Engine"]
    B --> D["User Profiles"]
    B --> E["Hybrid Search"]
    
    C --> F["事实提取"]
    C --> G["矛盾处理"]
    C --> H["自动遗忘"]
    
    D --> I["静态事实"]
    D --> J["动态上下文"]
    
    E --> K["RAG"]
    E --> L["Memory"]
```textmermaid
graph TB
    A["对话输入"] --> B["事实提取"]
    B --> C{"事实已存在？"}
    
    C -->|"新事实"| D["添加记忆"]
    C -->|"更新"| E["时间戳更新"]
    C -->|"矛盾"| F["矛盾消解"]
    C -->|"过期"| G["自动遗忘"]
    
    D --> H["Memory Graph"]
    E --> H
    F --> H
    G --> H
```texttypescript
const { profile } = await client.profile({
    containerTag: "user_123"
});

// profile.static → 长期事实
// ["在 Acme 工作", "喜欢深色模式", "使用 Vim"]

// profile.dynamic → 近期上下文
// ["正在做 auth 迁移", "调试 rate limits"]
```texttypescript
const results = await client.search.memories({
    q: "如何部署？",
    containerTag: "user_123",
    searchMode: "hybrid"
});
// 返回：部署文档（RAG）+ 用户的部署偏好（Memory）
```textbash
# JavaScript/TypeScript
npm install supermemory

# Python
pip install supermemory
```texttypescript
import Supermemory from "supermemory";

const client = new Supermemory();

await client.add({
    content: "用户喜欢 TypeScript，偏爱函数式编程",
    containerTag: "user_123"
});

const { profile, searchResults } = await client.profile({
    containerTag: "user_123",
    q: "用户偏好的编程风格是什么？"
});
```

```python
from supermemory import Supermemory

client = Supermemory()

client.add(
    content="用户喜欢 TypeScript，偏爱函数式编程",
    container_tag="user_123"
)

result = client.profile(
    container_tag="user_123",
    q="编程风格偏好"
)
print(result.profile.static)
print(result.profile.dynamic)
```textbash
npx -y install-mcp@latest https://mcp.supermemory.ai/mcp --client claude --oauth=yes
```texttypescript
// 混合搜索（默认）— RAG + Memory
const results = await client.search.memories({
    q: "部署偏好",
    containerTag: "user_123",
    searchMode: "hybrid"
});

// 仅记忆搜索
const results = await client.search.memories({
    q: "用户偏好",
    containerTag: "user_123",
    searchMode: "memories"
});
```texttypescript
const { profile } = await client.profile({
    containerTag: "user_123"
});

// profile.static → ["Acme 高级工程师", "喜欢深色模式", "使用 Vim"]
// profile.dynamic → ["正在做 auth 迁移项目", "调试 API rate limits"]
```texttypescript
const doc = await client.documents.uploadFile({
    file: "./report.pdf",
    containerTag: "project_abc"
});

const docs = await client.documents.list({
    containerTag: "project_abc",
    filter: { type: "pdf" }
});
```texttypescript
import { withSupermemory } from "@supermemory/tools/ai-sdk";
import { openai } from "ai-sdk";

const model = withSupermemory(
    openai("gpt-4o"),
    "user_123"
);
```texttypescript
import { withSupermemory } from "@supermemory/tools/mastra";

const agent = new Agent(
    withSupermemory(config, "user-123", {
        mode: "full"
    })
);
```text
┌─────────────────────────────────────┐
│         Your App / AI Tool           │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│          Supermemory                 │
│  ┌────────────────────────────────┐ │
│  │     Memory Engine              │ │
│  │  · 事实提取                    │ │
│  │  · 时序变化追踪                │ │
│  │  · 矛盾消解                    │ │
│  │  · 自动遗忘                    │ │
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │     User Profiles              │ │
│  │  · Static Facts（静态事实）    │ │
│  │  · Dynamic Context（动态上下文）│ │
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │     Hybrid Search              │ │
│  │  · RAG（知识库检索）          │ │
│  │  · Memory（个性化记忆）        │ │
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │     Connectors                 │ │
│  │  · Google Drive / Gmail       │ │
│  │  · Notion / OneDrive         │ │
│  │  · GitHub / Web Crawler      │ │
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │     Multi-modal Extractors     │ │
│  │  · PDF / Images (OCR)         │ │
│  │  · Videos (Transcription)     │ │
│  │  · Code (AST-aware)          │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
```text
用户：我最近在做一个电商平台的支付系统，后端用 Go
AI：了解了，支付系统 + Go 后端
```text
用户：帮我设计支付模块的 API 接口
```text
supermemory/
├── apps/
├── packages/
├── skills/
│   └── supermemory/
├── .github/workflows/
├── turbo.json
├── biome.json
├── bun.lock
└── package.json
```text
用户：我想取消订阅
AI：
  → Supermemory 检索用户历史
  → 发现：用户于 2025年3月 订阅了年费会员
  → 自动将订阅状态、购买历史注入上下文
  → 提供精准的取消帮助
```text
用户1：我在做一个新项目，是电商平台的支付系统
用户1：我偏好使用 Stripe 而不是 PayPal

[第二天]

用户1：帮我设计支付模块
AI：
  → Supermemory 检索"用户偏好 Stripe"
  → 检索"电商项目背景"
  → 直接基于 Stripe 设计，不提 PayPal
```text
新员工：我们的技术栈是什么？
AI：
  → Supermemory 检索公司知识库
  → 结合员工背景（前端工程师）
  → 返回：React/Next.js 后端，部署在 Vercel
```textbash
bun run src/index.ts run -p supermemory -b longmemeval -j gpt-4o -r my-run
```texttypescript
await client.add({
    content: "用户正在开发支付系统",
    containerTag: "work_project_abc"
});

await client.add({
    content: "用户在学 Rust",
    containerTag: "personal_learning"
});
```texttypescript
const { profile } = await client.profile({
    containerTag: "user_123"
});

const systemPrompt = `
用户信息：
- 长期背景：${profile.static.join(", ")}
- 当前上下文：${profile.dynamic.join(", ")}
`;
```textbash
git checkout -b feature/new-feature
# 遵循 CONTRIBUTING.md 规范提交 PR
```

---

## 十一、采用建议

Supermemory 适合下面这些场景，按优先级排序：

**优先采用**：你的 AI 应用需要跨会话记住用户偏好和项目上下文，且当前用的是"把历史对话全文塞进 prompt"的笨办法。Supermemory 的 Memory Engine + User Profiles 组合可以显著减少 token 消耗，同时提升个性化回答的质量。

**值得评估**：你已经有了 RAG 管道，但知识库检索和用户记忆是两套独立系统，维护成本高。Hybrid Search 可以把它们合并成一次查询。

**可以等等**：你的应用场景是单轮问答（每次对话独立），或者用户量级在百万以上且对延迟极度敏感。Supermemory 目前的优势在记忆质量而非极致吞吐，建议先用 MemoryBench 在你的数据集上跑一轮再看。

**不要因为 benchmark 分数就选型**。第八章已经说清楚了：这些分数测的是记忆准确性，不是你的业务场景。把 Supermemory 和 Mem0、Zep 一起用 MemoryBench 测一遍，看哪个在你的数据上表现更好。

**从哪里开始**：

1. 装 npm 包，跑一个 `client.add()` + `client.profile()` 的完整回路（[快速开始](#三快速开始)）
2. 如果你用 Claude Code 或 Cursor，装 MCP Server 让 AI 直接获得记忆能力（[MCP 集成](#三 3-mcp-serverai-工具集成)）
3. 把 `profile()` 结果拼入你的系统提示词，对比有无记忆时的回答质量差异
4. 需要接入外部数据源时，再配置 Connectors

---

**文档信息**

- 难度：⭐⭐⭐⭐
- 更新日期：2026-03-31
- GitHub：https://github.com/supermemoryai/supermemory
- 官网：https://supermemory.ai
- 文档：https://supermemory.ai/docs

🦞 由钳岳星君撰写 | 项目源码：https://github.com/supermemoryai/supermemory