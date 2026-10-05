---
title: "Supermemory：AI时代的记忆与上下文引擎完全指南"
date: "2026-05-31T20:07:02+08:00"
lastmod: "2026-10-01"
slug: "supermemory-ai-memory-context-engine-guide"
github_repo: "supermemoryai/supermemory"
source_key: "gh:supermemoryai/supermemory"
description: "Supermemory是面向AI的记忆与上下文引擎，官方研究页声称在LongMemEval、LoCoMo、ConvoMem三大AI记忆基准上均列第一。本文解析其记忆引擎、用户画像、混合搜索、Connectors、多模态提取，以及2026年7月起新增的本地自托管方案Supermemory local。"
draft: false
categories: ["技术笔记"]
tags: ["AI记忆", "RAG", "MCP", "自托管"]
---

# Supermemory：AI 时代的记忆与上下文引擎完全指南

几乎所有 AI 工具——ChatGPT、Claude、Cursor——在每次新对话时都会"失忆"，用户不得不反复解释自己的偏好、正在做的项目和过往讨论的背景。Supermemory 解决的就是这件事：让 AI 在跨会话中积累、检索和利用个人上下文。

按官方 README 的说法，它是一个"面向 AI 的记忆与上下文引擎"（memory and context engine），背后是一个围绕该引擎打造插件和工具的研究团队。这个定位值得注意——它做的基础设施，而不是聊天插件；接入方既可以是 Claude Code、Cursor 这类工具的用户，也可以是需要记忆能力的 Agent 开发者，还能在 2026 年 7 月之后把它完整跑在自己机器上。

## 项目概览

| 指标 | 数值 |
|------|------|
| 仓库 | [supermemoryai/supermemory](https://github.com/supermemoryai/supermemory) |
| Stars / Forks | 31,048 / 2,726（2026-10-01 GitHub API 读数） |
| 许可证 | MIT |
| 主要语言 | TypeScript |
| 创建时间 | 2024-02-27 |
| 基准排名 | LongMemEval、LoCoMo、ConvoMem 均列第一（官方口径，见下文基准解读） |

## 系统地图：先分清三条使用路径

Supermemory 容易被讲成一团"记忆功能"，实际它给三类人各准备了一条路径，共用同一个引擎：

| 路径 | 面向谁 | 接入方式 |
|------|--------|----------|
| 插件 / MCP | 用 AI 工具的人 | 给 Claude Code、Cursor、Codex 等装官方插件，或接 MCP 服务器 |
| API / SDK | 构建 AI 产品的开发者 | `npm install supermemory` 或 `pip install supermemory`，一个客户端覆盖记忆、RAG、画像、文件处理 |
| Supermemory local | 想自己跑的人 | `npx supermemory local` 或官方安装脚本，单二进制，本地 API 服务 |

三条路径调用的是同一套记忆结构。官方 README 用一张五组件图描述引擎内部：记忆引擎（提取事实、跟踪更新、消解矛盾、自动遗忘过期信息）、用户画像（静态事实 + 动态上下文）、混合搜索（RAG 与记忆一次查询）、Connectors（外部数据实时同步）、文件处理（PDF、图片、视频、代码转为可检索片段）。

## 核心机制

### 记忆引擎：带时间维度的记忆

传统的向量库存的是"文本块"，Supermemory 的记忆引擎存的是"关于用户的事实"，并且维护这些事实的生命周期。README 明确列出了三种能力：

- **矛盾消解**：新信息与已有事实冲突时自动处理。官方举的例子是"我刚搬到旧金山"会取代"我住在纽约"，而不是两条并存；
- **自动遗忘**：临时性事实（"我明天有个考试"）在日期过后自动过期，噪音不会变成永久记忆；
- **增量更新**：事实随对话持续修正，而不是简单堆叠。

这也是它和"把聊天记录存进向量库"方案的本质区别——记忆有状态，会随时间演化。

### 用户画像：一次调用拿到"这个人是谁"

传统记忆方案依赖搜索——你得先知道该问什么。Supermemory 为每个用户自动维护画像，把稳定事实和近期活动分开：

```typescript
const { profile } = await client.profile({ containerTag: "user_123" });

// profile.static  → ["Senior engineer at Acme", "Prefers dark mode", "Uses Vim"]
// profile.dynamic → ["Working on auth migration", "Debugging rate limits"]
```

官方口径是一次调用约 50ms 返回，直接注入系统提示词，Agent 就知道自己在跟谁说话。记忆按 `containerTag`（容器标签）隔离，可以按项目、用户或客户分开维护工作与个人上下文。

### 混合搜索：RAG 与记忆同查

官方在文档中专门写了一个立场性命题："Memory is not RAG"——RAG 检索文档块，无状态，每个人得到相同结果；记忆提取并跟踪用户事实，随时间演化。Supermemory 默认两者一起跑，一次 `search()` 调用同时返回知识库文档和个性化记忆：

```typescript
// Hybrid（默认）——RAG + Memory 一次查询
const results = await client.search({
  q: "how do I deploy?",
  containerTag: "user_123",
  searchMode: "hybrid",
});
// 返回部署文档（RAG）+ 该用户的部署偏好（Memory）

// 只要记忆
const results = await client.search({
  q: "user preferences",
  containerTag: "user_123",
  searchMode: "memories",
});
```

### Connectors：外部数据自动入库

支持六个数据源自动同步进知识库：Google Drive、Gmail、Notion、OneDrive、GitHub、Web Crawler。走实时 webhook，文档自动完成处理、分块和索引，不需要手动导入。这让 Supermemory 不只是对话记忆工具，也是一个能主动抓取外部信息的个人知识库。

### 多模态提取

通过 `documents.uploadFile()` 上传文件，系统按内容类型自动选择提取器：

| 类型 | 处理方式 |
|------|----------|
| PDF | 文本提取 |
| 图片 | OCR |
| 视频 | 字幕转录 |
| 代码 | AST 感知分块（保留代码结构） |

## 开发者集成：一个 API 覆盖上下文栈

```typescript
import Supermemory from "supermemory";

const client = new Supermemory();

// 存储对话
await client.add({
  content: "User loves TypeScript and prefers functional patterns",
  containerTag: "user_123",
});

// 一次调用同时拿画像 + 相关记忆
const { profile, searchResults } = await client.profile({
  containerTag: "user_123",
  q: "What programming style does the user prefer?",
});

// profile.static  → ["Loves TypeScript", "Prefers functional patterns"]
// profile.dynamic → ["Working on API integration"]
// searchResults   → 按相似度排序的相关记忆
```

Python SDK 同等能力（`pip install supermemory`，PyPI 当前版本 3.62.0）：

```python
from supermemory import Supermemory

client = Supermemory()

client.add(
    content="User loves TypeScript and prefers functional patterns",
    container_tag="user_123"
)

result = client.profile(container_tag="user_123", q="programming style")

print(result.profile.static)   # 长期事实
print(result.profile.dynamic)  # 近期上下文
```

官方 README 的 "API at a glance" 列了七个方法，可以当能力清单读：

| 方法 | 用途 |
|------|------|
| `client.add()` | 存储内容——文本、对话、URL、HTML |
| `client.profile()` | 画像 + 可选搜索，一次调用 |
| `client.search()` | 跨记忆与文档的混合搜索（`searchMode`） |
| `client.search.documents()` | 带元数据过滤的文档搜索（legacy v3 响应结构） |
| `client.documents.uploadFile()` | 上传 PDF、图片、视频、代码 |
| `client.documents.list()` | 列出并过滤文档 |
| `client.settings.update()` | 配置记忆提取与分块 |

框架侧提供包装器，官方列了八家：Vercel AI SDK、LangChain、LangGraph、OpenAI Agents SDK、Mastra、Agno、Claude Memory Tool、n8n。以 Vercel AI SDK 为例，包一层就能给现有模型加上记忆：

```typescript
import { withSupermemory } from "@supermemory/tools/ai-sdk";
const model = withSupermemory(openai("gpt-4o"), { containerTag: "user_123", customId: "conv-1" });
```

对开发者而言，这套 API 的实际意义是：不配置向量数据库、不设计 embedding 流水线、不研究分块策略，记忆与 RAG 当作一个托管服务用。

## MCP 与插件生态

Supermemory 提供托管 MCP 服务器（`https://mcp.supermemory.ai/mcp`），走 OAuth 认证，不需要手动配 API key。手动配置示例：

```json
{
  "mcpServers": {
    "supermemory": {
      "url": "https://mcp.supermemory.ai/mcp"
    }
  }
}
```

官方文档列出的核心工具包括 `search_memory`、`get_profile`、`add_memory`、`list_documents`、`get_document`、`list_memories`、`list_spaces`、`who_am_i`，另有上传文件、记忆图谱等交互组件。支持的客户端：Claude Desktop、Cursor、Windsurf、VS Code、Claude Code、OpenCode、OpenClaw、Hermes。

一个查证提示：README 的 "What your AI gets" 表格写的还是 `memory`/`recall`/`context` 三个工具名，MCP 服务器源码（`apps/mcp`）注册的却是上面这批 snake_case 名称——README 表格滞后于源码，以源码和官方 MCP 文档为准。

官方开源的插件仓库已覆盖七个工具：

- Claude Code：[supermemoryai/claude-supermemory](https://github.com/supermemoryai/claude-supermemory)
- Muse Code：[supermemoryai/muse-supermemory](https://github.com/supermemoryai/muse-supermemory)
- Cursor：[supermemoryai/cursor-supermemory](https://github.com/supermemoryai/cursor-supermemory)
- Codex：[supermemoryai/codex-supermemory](https://github.com/supermemoryai/codex-supermemory)
- OpenClaw：[supermemoryai/openclaw-supermemory](https://github.com/supermemoryai/openclaw-supermemory)
- OpenCode：[supermemoryai/opencode-supermemory](https://github.com/supermemoryai/opencode-supermemory)
- Hermes（Supermemory 作为其 memory provider）：[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)

插件的工作方式是后台运行：你正常和 AI 对话，Supermemory 提取值得记住的部分（事实、偏好、项目上下文，而非噪音），下一次对话时 AI 已经认识你。

## Supermemory local：2026 年 7 月起可以完全自托管

这是 2026 年 5 月之后最重要的变化（本文首发于当月）。早期 Supermemory 只有云服务，数据必须上传；2026 年 7 月 22 日仓库开始发布 `supermemory-server` 二进制（最新 server-v0.0.8，2026-08-17，macOS arm64 版 258MB），README 现在的口号是 "One binary. Zero config."：

```bash
curl -fsSL https://supermemory.ai/install | bash
# 或
npx supermemory local
```

首次启动会初始化嵌入的记忆图引擎和本地嵌入模型，配置凭据后打印一个 API key，完整的 Memory API（文档、记忆、画像、混合搜索）跑在 `http://localhost:6767`。SDK 侧只改一处：

```typescript
const client = new Supermemory({
  apiKey: "sm_...",
  baseURL: "http://localhost:6767", // 仅此一处改动
});
```

几个关键性质：

- **模型随意换**：OpenAI、Anthropic、Gemini、Groq 或任何 OpenAI 兼容端点，首次启动的向导引导配置；
- **嵌入默认本地**：默认 `Xenova/bge-base-en-v1.5`，不需要 API key；可选 OpenAI、Gemini 或 Ollama；
- **可以完全离线**：接入 Ollama（官方推荐 `gpt-oss:20b`）后没有任何数据离开本机；
- **数据单目录**：全部数据在 `./.supermemory`，便于备份和迁移；
- **与云平台同 API**：本地原型验证后，改 `baseURL` 即可切到托管平台。

官方为此专门提供了自托管文档，覆盖快速开始、配置、嵌入模型与 local 与 Enterprise 版差异（见文末链接）。对数据不能出内网的团队，先跑 local 再评估云平台，顺序不必反过来。

## 基准解读：三榜第一应该怎么读

先说清楚三个基准各自测什么（口径来自官方 README 的基准表）：

| 基准 | 测什么 | 官方声明结果 |
|------|--------|--------------|
| [LongMemEval](https://github.com/xiaowu0162/LongMemEval) | 跨会话长期记忆与知识更新 | #1 |
| [LoCoMo](https://github.com/snap-research/locomo) | 长对话事实召回（单跳、多跳、时间、对抗） | #1 |
| [ConvoMem](https://github.com/SalesforceAIResearch/ConvoMem) | 个性化与偏好学习 | #1 |

数字层面，README 给出的 LongMemEval 成绩是：**95% Recall@15，仅引入约 720 tokens 上下文——上下文缩减 99.4%**（@10 为 99.6%，@5 为 99.8%）；按类别拆分：知识更新 99%、助手召回 100%、用户召回 97%、多会话 93%、时间推理 91%、偏好 90%。官方研究页另有 LongMemEval-S 口径：97% Recall@20（500 题、六类），对比 Zep 的 71.2% 和全上下文的 60.2%。两个口径并存（@15 与 @20），引用时注意区分。

怎么读这些数字：Recall@k 高而 token 增量低，说明的是检索器"用很小的上下文挑对片段"的能力——这直接决定记忆功能的实用成本，往系统提示词里塞 720 tokens 比塞整个对话历史便宜得多。六类拆分里时间推理（91%）和偏好（90%）偏低，恰好对应记忆系统最难的两件事：事实随时间失效，以及把零散陈述聚合成偏好。

不能推出什么：三榜第一是厂商自报口径，官方自己也知道这点——研究页的口号就是"记忆系统应该公开测量"，并开源了 [MemoryBench](https://supermemory.ai/docs/memorybench/overview) 基准框架，支持对 Supermemory、Mem0、Zep 等做可复现的对比测试，还提供了让企业自测自家方案的 Agent skill（`npx skills add supermemoryai/memorybench`）。拿它做选型时，这个可复现路径比任何榜单名次都更有用。另外，基准成绩不能直接推出生产环境的延迟、并发与成本表现。

官方还做了 Supermemory Filesystem（SMFS），在 110 题的 xAFS 基准上，Claude 端累计 token 消耗降到约 1/3（24M vs 72M），Codex 端约 1/1.75。这组数字测的是"文件系统形态的上下文供给"对 Agent 长任务的 token 效率，与记忆基准是两回事，不要混用。

## 一次对话如何流过系统

把上面的机制串起来，看一条真实链路：

1. 用户在 Cursor 里说："我偏好函数式风格，别给我写 class。"插件在后台调用 `add_memory`，记忆引擎提取事实写入 `containerTag` 隔离的记忆库；
2. 同一个项目里，用户往挂了 GitHub Connector 的仓库提了几个 PR，相关文档经 webhook 同步进知识库；
3. 下一次会话开始，插件调用 `get_profile` 拿到画像（static：偏好函数式；dynamic：正在做某个迁移），注入系统提示词——这一步约 50ms；
4. 用户问"这个部署报错怎么解"，`search_memory` 以 hybrid 模式同查：知识库返回部署文档，记忆返回"这位用户上次部署用的参数"，AI 的回答同时带上文档依据和个人上下文。

整条链路里，用户只在第 1 步和第 4 步露面，其余都是后台自动完成。

## 适用边界与采用建议

**适合**：

- 个人用户想让 Claude Code、Cursor 等工具有跨会话记忆——装插件或 MCP 是成本最低的路径；
- Agent / AI 产品开发者需要记忆 + RAG + 画像的完整上下文层——一个 API 起步，八家主流框架有官方包装器；
- 数据不能出内网的场景——Supermemory local 全离线模式（Ollama + 本地嵌入）可以直接试，不必像早期那样只能放弃。

**需要注意**：

- `server-v0.0.8` 的版本号说明本地版还年轻（2026 年 8 月），生产使用前建议先在本地验证功能覆盖；
- 三榜第一是官方口径，选型时用 MemoryBench 跑自己的工作负载，比引用榜单更有说服力；
- 记忆质量依赖对话中有可提取的稳定事实——一次性、单轮的工具场景收益有限。

对一个 2024 年 2 月创建、目前 31k stars 的项目来说，从"云 API"走到"单二进制本地部署"、从"记忆工具"走到"可复现基准框架"，方向是一致的：把记忆变成可验证的基础设施。跨会话记忆正在成为 AI 助手实用性的分水岭，Supermemory 是这个方向上目前值得关注的开源实现。

## 资源链接

- 文档：https://supermemory.ai/docs
- 自托管（Supermemory local）：https://supermemory.ai/docs/self-hosting/overview
- MemoryBench：https://supermemory.ai/docs/memorybench/overview
- 研究页（基准详情）：https://supermemory.ai/research
- Memory 与 RAG 的区别：https://supermemory.ai/docs/concepts/memory-vs-rag
- Discord：https://supermemory.link/discord
