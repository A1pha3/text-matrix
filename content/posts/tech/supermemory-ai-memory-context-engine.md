---
title: "Supermemory：AI 记忆与上下文引擎从入门到精通"
date: 2026-03-28T16:10:00+08:00
slug: "supermemory-ai-memory-context-engine"
description: "深度解析 Supermemory AI 记忆与上下文引擎：Memory Engine 事实提取、User Profiles 用户画像、Hybrid Search 混合搜索、Connectors 数据连接器，详解原理、架构、API 使用与二次开发。"
draft: false
categories: ["技术笔记"]
tags: ["AI记忆", "RAG", "User Profiles", "混合搜索", "Supermemory"]
---

# Supermemory：AI 记忆与上下文引擎从入门到精通

> **目标读者**：想要深入理解 AI 持久记忆系统、用户画像构建、混合搜索 RAG 技术的开发者与产品经理
> **核心问题**：如何让 AI 在多轮对话中记住用户信息、构建个性化上下文、实现真正的持久记忆？
> **难度**：⭐⭐⭐⭐（专家设计）
> **预计阅读时间**：45 分钟

---

## 一、原理分析：为什么 AI 需要记忆系统

### 1.1 当前 AI 的记忆困境

当我们与 AI 助手对话时，每次会话都是「从零开始」。AI 无法：

**记住用户偏好**：用户喜欢什么编程语言、什么样的代码风格、如何命名变量——每次都要重新解释。

**跨会话积累知识**：上个月讨论的项目背景、技术选型决策、踩过的坑——下次对话完全消失。

**理解用户是谁**：AI 无法区分同一个团队中的不同开发者，无法针对用户的专业水平调整解释深度。

**处理信息变化**：用户上周说「我在 NYC」，这周说「我搬到了 SF」——AI 还在引用旧信息。

### 1.2 传统 RAG 的局限性

**传统 RAG（检索增强生成）只能检索文档**，存在以下问题：

| 维度 | 传统 RAG | Supermemory |
|------|----------|-------------|
| **检索内容** | 文档片段（无状态） | 用户事实（有个性化） |
| **记忆持久性** | 文档是静态的 | 事实随时间演变 |
| **矛盾处理** | 无 | 自动检测和解决 |
| **过期遗忘** | 无 | 临时事实自动过期 |
| **用户画像** | 无 | 自动构建和维护 |

**关键洞察**：Memory 不是 RAG。RAG 检索文档碎片——对所有人都一样。Memory 提取和追踪**关于用户的实时事实**。

### 1.3 Supermemory 的核心思想

Supermemory 提出了一个关键范式：**Memory = RAG + Personalized Facts + Temporal Context**

它同时解决两个问题：

1. **知识库检索（RAG）**：从文档、网页、代码库中检索相关内容
2. **用户记忆（Memory）**：从对话中提取和追踪用户的事实、偏好、历史

通过 `Hybrid Search`，一次查询同时返回知识库结果和用户个性化上下文。

---

## 二、架构分析：系统是如何设计的

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Supermemory 系统架构                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Your App / AI Tool                            │  │
│  │         (Claude Code, Cursor, OpenClaw, 自定义应用)                  │  │
│  └──────────────────────────────┬───────────────────────────────────────┘  │
│                                 │                                            │
│                                 ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Supermemory API                                │  │
│  │                                                                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Memory    │  │    User     │  │   Hybrid    │  │   Connectors │  │  │
│  │  │   Engine    │  │  Profiles   │  │   Search    │  │             │  │  │
│  │  │             │  │             │  │             │  │  Google Drive│  │  │
│  │  │ • 事实提取  │  │ • 静态事实  │  │ • RAG + Mem │  │  Gmail      │  │  │
│  │  │ • 矛盾检测  │  │ • 动态上下文│  │ • 一次查询  │  │  Notion     │  │  │
│  │  │ • 过期遗忘  │  │ • ~50ms    │  │ • 混合排序  │  │  GitHub     │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  │                                                                       │  │
│  │  ┌───────────────────────────────────────────────────────────────┐   │  │
│  │  │              Multi-modal Extractors                          │   │  │
│  │  │    PDF (OCR) | Images | Videos (Transcription) | Code (AST)   │   │  │
│  │  └───────────────────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心模块详解

#### 2.2.1 Memory Engine（记忆引擎）

Memory Engine 是 Supermemory 的核心创新。它不只是存储，还**理解和管理知识**。

**事实提取（Fact Extraction）**

```python
# 当用户说："我已经用 TypeScript 3 年了，喜欢函数式编程"
# Memory Engine 自动提取：
{
    "fact": "Loves TypeScript",
    "confidence": 0.95,
    "source": "conversation_2026_03_28",
    "extracted_at": "2026-03-28T10:30:00Z"
}
```

**时间感知（Temporal Awareness）**

```
场景：用户说「我上周在 NYC」，现在说「我搬到了 SF」

Memory Engine 处理：
1. 检测矛盾：地点从 NYC → SF
2. 标记旧事实为过期：「用户在 NYC」（2026-03-20 已过期）
3. 创建新事实：「用户现在在 SF」（2026-03-28 生效）
4. 自动遗忘：旧事实不会在检索中出现
```

**矛盾解决（Contradiction Resolution）**

当新信息与旧事实冲突时，Memory Engine 会：

1. 标记旧事实为「已替代」
2. 存储新事实及其来源
3. 保留历史供审计追踪

**自动遗忘（Automatic Forgetting）**

```
临时事实：「我明天有考试」
→ 过期日期：2026-03-29
→ 2026-03-30 自动从记忆中移除
```

#### 2.2.2 User Profiles（用户画像）

User Profiles 是 Memory Engine 的产物，提供结构化的用户上下文。

**静态事实（Static Facts）**

用户长期不变的偏好和背景：

```json
{
  "static": [
    "Senior engineer at Acme Corp",
    "Prefers TypeScript over Python",
    "Uses Vim keybindings",
    "Lives in San Francisco"
  ]
}
```

**动态上下文（Dynamic Context）**

用户近期活动和当前项目：

```json
{
  "dynamic": [
    "Working on auth migration project",
    "Debugging rate limit issues",
    "Recently joined the infrastructure team"
  ]
}
```

**API 调用**

```javascript
const { profile } = await client.profile({
  containerTag: "user_123"
});

// profile.static → ["Senior engineer...", "Prefers TypeScript..."]
// profile.dynamic → ["Working on auth migration..."]
```

**性能**：单次调用 ~50ms，即插即用到 system prompt。

#### 2.2.3 Hybrid Search（混合搜索）

Hybrid Search 同时检索**知识库文档**和**用户记忆**，一次查询返回所有相关内容。

**搜索模式**

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| `hybrid`（默认） | RAG + Memory 混合 | 需要两者兼顾 |
| `memories` | 仅用户记忆 | 只需要用户上下文 |
| `documents` | 仅知识库文档 | 只需要检索文档 |

**示例**

```javascript
// 用户问：「上次我怎么部署的？」
const results = await client.search.memories({
  q: "how do I deploy?",
  containerTag: "user_123",
  searchMode: "hybrid"
});

// 返回：
// - 知识库：部署文档片段
// - 用户记忆：用户上次部署到 Vercer 的偏好
```

#### 2.2.4 Connectors（数据连接器）

Connectors 实现外部数据的自动同步：

| 连接器 | 支持的数据 | 同步方式 |
|--------|----------|---------|
| Google Drive | 文档、表格、幻灯片 | 实时 Webhook |
| Gmail | 邮件 | 实时 Webhook |
| Notion | 页面、数据库 | 实时 Webhook |
| OneDrive | 文档 | 实时 Webhook |
| GitHub | Issues, PRs, 代码 | Webhook |
| Web Crawler | 任意网页 | 按需抓取 |

**工作原理**

```
Google Drive 文件更新
       ↓
  Webhook 触发
       ↓
  Supermemory 处理
  - 内容提取
  - 语义分块（Semantic Chunking）
  - 向量化存储
       ↓
  用户下次检索时可用
```

#### 2.2.5 Multi-modal Extractors（多模态提取器）

Supermemory 支持多种文件类型的自动提取和索引：

| 类型 | 处理方式 | 输出 |
|------|---------|------|
| PDF | 文本提取 | 可搜索文本 |
| 图片 | OCR 识别 | 文本 + ALT |
| 视频 | 语音转录 | 时间戳文本 |
| 代码 | AST 感知分块 | 结构化片段 |

**代码分块（AST-aware Chunking）**

```javascript
// 代码文件自动按函数/类分块，而不是固定字数
// 检索时返回完整函数，而不是碎片

// 分块结果：
chunk_1: "function authenticateUser() {...}"
chunk_2: "class PaymentProcessor {...}"
chunk_3: "async function processRefund() {...}"
```

### 2.3 技术选型

#### 2.3.1 为什么选择 Cloudflare Workers

**边缘部署**：Memory 查询需要低延迟，Workers 部署在全球边缘节点。

**KV 存储**：Cloudflare KV 提供高读写性能的键值存储，适合事实存储。

**可扩展**：Workers + KV 可以从小规模无缝扩展到百万用户。

#### 2.3.2 为什么支持 npm + pip 双端

**前端集成**：Web 应用、VS Code 插件、浏览器扩展用 npm。

**后端集成**：Python 数据管道、ML 应用、数据科学用 pip。

这让 Supermemory 可以同时服务前端和后端场景。

### 2.4 基准测试表现

Supermemory 在三大 AI Memory 基准测试中均排名第一：

| 基准测试 | 测试内容 | 结果 |
|---------|---------|------|
| **LongMemEval** | 跨会话长期记忆 + 知识更新 | **81.6% — #1** |
| **LoCoMo** | 单跳/多跳/时间性/对抗性事实召回 | **#1** |
| **ConvoMem** | 个性化和偏好学习 | **#1** |

---

## 三、使用说明：从安装到实战

### 3.1 用户场景：给 AI 添加记忆

#### 3.1.1 安装 Supermemory App

访问 https://app.supermemory.ai 注册，无需代码即可使用。

#### 3.1.2 浏览器扩展

Chrome/Edge 扩展会在你浏览网页时自动提取和存储相关内容。

#### 3.1.3 Claude Code / Cursor / OpenCode 插件

**Claude Code**

```bash
npx -y install-mcp@latest https://mcp.supermemory.ai/mcp --client claude --oauth=yes
```

**Cursor**

```bash
npx -y install-mcp@latest https://mcp.supermemory.ai/mcp --client cursor --oauth=yes
```

**其他客户端**

```bash
npx -y install-mcp@latest https://mcp.supermemory.ai/mcp --client <your-client>
# 支持：vscode, windsurf, claude-desktop 等
```

#### 3.1.4 MCP 手动配置

在 MCP 客户端配置中添加：

```json
{
  "mcpServers": {
    "supermemory": {
      "url": "https://mcp.supermemory.ai/mcp"
    }
  }
}
```

或使用 API Key：

```json
{
  "mcpServers": {
    "supermemory": {
      "url": "https://mcp.supermemory.ai/mcp",
      "headers": {
        "Authorization": "Bearer sm_your_api_key_here"
      }
    }
  }
}
```

#### 3.1.5 AI 获得的工具

安装后，AI 会自动获得三个工具：

| 工具 | 功能 |
|------|------|
| `memory` | 保存或遗忘信息。AI 自动调用，记住用户分享的重要内容。 |
| `recall` | 按查询搜索记忆。返回相关记忆 + 用户画像摘要。 |
| `context` | 将完整用户画像（偏好、近期活动）注入对话开头。在 Cursor 和 Claude Code 中只需输入 `/context`。 |

### 3.2 开发者场景：API 集成

#### 3.2.1 安装

```bash
npm install supermemory   # 或
pip install supermemory   # Python
```

#### 3.2.2 快速开始

**TypeScript / JavaScript**

```typescript
import Supermemory from "supermemory";

const client = new Supermemory();

// 存储对话内容
await client.add({
  content: "User loves TypeScript and prefers functional patterns",
  containerTag: "user_123",
});

// 获取用户画像 + 搜索记忆（一次调用）
const { profile, searchResults } = await client.profile({
  containerTag: "user_123",
  q: "What programming style does the user prefer?",
});

// profile.static → ["Loves TypeScript", "Prefers functional patterns"]
// profile.dynamic → ["Working on API integration"]
// searchResults → 按相似度排序的相关记忆
```

**Python**

```python
from supermemory import Supermemory

client = Supermemory()

# 存储内容
client.add(
    content="User loves TypeScript and prefers functional patterns",
    container_tag="user_123"
)

# 获取画像和记忆
result = client.profile(container_tag="user_123", q="programming style")
print(result.profile.static)  # 长期事实
print(result.profile.dynamic)  # 近期上下文
```

#### 3.2.3 框架集成

Supermemory 提供主流 AI 框架的一键包装器：

**Vercel AI SDK**

```typescript
import { withSupermemory } from "@supermemory/tools/ai-sdk";

const model = withSupermemory(openai("gpt-4o"), "user_123");
```

**Mastra**

```typescript
import { withSupermemory } from "@supermemory/tools/mastra";

const agent = new Agent(
  withSupermemory(config, "user-123", { mode: "full" })
);
```

**支持的框架**：Vercel AI SDK、LangChain、LangGraph、OpenAI Agents SDK、Mastra、Agno、Claude Memory Tool、n8n

#### 3.2.4 API 方法一览

| 方法 | 用途 |
|------|------|
| `client.add()` | 存储内容——文本、对话、URL、HTML |
| `client.profile()` | 用户画像 + 可选搜索，一次调用 |
| `client.search.memories()` | 混合搜索记忆和文档 |
| `client.search.documents()` | 文档搜索，支持元数据过滤 |
| `client.documents.uploadFile()` | 上传 PDF、图片、视频、代码 |
| `client.documents.list()` | 列出和过滤文档 |
| `client.settings.update()` | 配置记忆提取和分块策略 |

### 3.3 搜索模式详解

#### 3.3.1 Hybrid 模式（默认）

```javascript
const results = await client.search.memories({
  q: "how do I deploy?",
  containerTag: "user_123",
  searchMode: "hybrid",
});

// 返回：
// - 部署相关文档（RAG）
// - 用户部署偏好（Memory）
```

#### 3.3.2 Memories 模式

```javascript
const results = await client.search.memories({
  q: "user preferences",
  containerTag: "user_123",
  searchMode: "memories",
});

// 仅返回用户记忆，不返回文档
```

### 3.4 Connectors 配置

#### 3.4.1 支持的连接器

- Google Drive
- Gmail
- Notion
- OneDrive
- GitHub
- Web Crawler

#### 3.4.2 工作流程

1. 在 Supermemory Dashboard 连接你的账户
2. 配置同步频率（实时/定时）
3. 文档自动处理、分块、可搜索

---

## 四、开发扩展：如何基于 Supermemory 做二次开发

> **说明**：以下代码示例为教学目的设计，用于说明扩展思路。实际开发时请参考官方文档。

### 4.1 创建自定义 Memory 处理器

```typescript
import { MemoryProcessor, MemoryEvent } from "supermemory";

class ProjectTrackingProcessor implements MemoryProcessor {
  name = "project_tracker";

  async process(event: MemoryEvent): Promise<MemoryEvent | null> {
    // 检测项目相关事件
    if (event.type === "conversation" && this.isProjectMention(event)) {
      return {
        ...event,
        tags: [...event.tags, "project", this.extractProjectName(event)],
        priority: "high",
      };
    }

    // 返回 null 表示不存储
    return null;
  }

  private isProjectMention(event: MemoryEvent): boolean {
    const keywords = ["project", "deadline", "milestone", "sprint"];
    return keywords.some((k) => event.content.toLowerCase().includes(k));
  }

  private extractProjectName(event: MemoryEvent): string {
    // 提取项目名称逻辑
    return "unknown";
  }
}

// 注册处理器
client.registerProcessor(new ProjectTrackingProcessor());
```

### 4.2 自定义 User Profile 聚合

```typescript
import { ProfileAggregator, Profile } from "supermemory";

class EngineeringProfileAggregator implements ProfileAggregator {
  async aggregate(memories: Memory[]): Promise<Profile> {
    const staticFacts: string[] = [];
    const dynamicContext: string[] = [];

    for (const memory of memories) {
      if (memory.type === "preference") {
        staticFacts.push(memory.content);
      } else if (memory.type === "activity") {
        dynamicContext.push(memory.content);
      }
    }

    // 添加工程特定推断
    if (this.hasCodingPatterns(memories)) {
      staticFacts.push("Software Engineer");
    }

    return {
      static: staticFacts,
      dynamic: dynamicContext,
      metadata: {
        memoryCount: memories.length,
        lastUpdated: new Date(),
      },
    };
  }
}
```

### 4.3 构建垂直领域 Memory 应用

```typescript
class LegalAssistantMemory {
  constructor(private client: Supermemory) {}

  async addContractAnalysis(contract: string, summary: string) {
    await this.client.add({
      content: `Contract: ${contract}\nSummary: ${summary}`,
      containerTag: `contract_${this.extractId(contract)}`,
    });
  }

  async addClientInteraction(
    clientId: string,
    interaction: string
  ) {
    await this.client.add({
      content: interaction,
      containerTag: `client_${clientId}`,
      metadata: {
        type: "client_interaction",
        timestamp: Date.now(),
      },
    });
  }

  async getClientContext(clientId: string) {
    const { profile, searchResults } = await this.client.profile({
      containerTag: `client_${clientId}`,
      q: "pending cases, recent discussions, client preferences",
    });

    return {
      profile,
      searchResults,
    };
  }
}
```

### 4.4 与现有系统集成

#### 4.4.1 集成到 LangChain

```typescript
import { SupermemoryRetriever } from "@supermemory/tools/langchain";

const retriever = new SupermemoryRetriever({
  containerTag: "user_123",
  searchMode: "hybrid",
});

const chain = RetrievalQAChain.fromLLM(
  llm,
  retriever
);
```

#### 4.4.2 集成到客服系统

```typescript
class CustomerSupportMemory {
  async handleTicket(ticketId: string, customerId: string) {
    // 获取客户历史上下文
    const { profile } = await this.client.profile({
      containerTag: `customer_${customerId}`,
    });

    // 构建 system prompt
    const systemPrompt = `You are helping ${profile.static[0] || "a customer"}.
Current project: ${profile.dynamic[0] || "none"}
${profile.static.slice(1).join(", ")}`;

    // 存储本次对话
    await this.client.add({
      content: `Ticket ${ticketId} resolved.`,
      containerTag: `customer_${customerId}`,
    });

    return { profile, systemPrompt };
  }
}
```

---

## 五、总结与展望

### 5.1 核心要点回顾

| 维度 | 要点 |
|------|------|
| **设计思想** | Memory = RAG + Personalized Facts + Temporal Context |
| **核心创新** | 事实提取、矛盾解决、自动遗忘、用户画像 |
| **架构优势** | Hybrid Search、Connectors 多平台、多模态提取 |
| **性能指标** | ~50ms 画像查询、#1 三大基准测试 |
| **适用场景** | AI 助手、客服系统、个性化推荐、知识管理 |

### 5.2 与同类项目对比

| 项目 | 记忆方式 | 用户画像 | 基准测试 | 开源 |
|------|---------|---------|---------|------|
| **Supermemory** | 事实 + RAG | ✅ 自动构建 | **#1 三项** | ✅ |
| Mem0 | 向量存储 | ⚠️ 有限 | 未公开 | ✅ |
| Zep | 对话历史 | ⚠️ 基础 | 未公开 | ✅ |
| Pinecone | 仅向量检索 | ❌ | N/A | ❌ |

### 5.3 适用与不适用场景

**适用**：
- 需要长期记忆用户的 AI 助手（Claude Code、Cursor 等）
- 需要个性化上下文的客服系统
- 需要文档 + 用户偏好联合检索的企业知识库
- 需要跨会话记住用户偏好的应用

**不适用**：
- 纯文档检索（用普通 RAG 即可）
- 无需用户个性化的场景
- 实时性要求极高的交易系统

### 5.4 未来发展方向

根据项目 Roadmap：

- **MemoryBench**：开源的 Memory 系统基准测试框架，支持对比 Supermemory、Mem0、Zep 等
- **更多 Connectors**：Slack、Notion、Confluence
- **企业特性**：SSO、RBAC、审计日志
- **性能优化**：更快的向量检索、更低的延迟

---

## 参考资源

| 资源 | 链接 |
|------|------|
| 项目主页 | https://supermemory.ai |
| GitHub | https://github.com/supermemoryai/supermemory |
| 官方文档 | https://supermemory.ai/docs |
| 快速开始 | https://supermemory.ai/docs/quickstart |
| Discord | https://supermemory.link/discord |
| npm | https://www.npmjs.com/package/supermemory |
| PyPI | https://pypi.org/project/supermemory/ |
| MemoryBench | https://supermemory.ai/docs/memorybench/overview |

---

**文档信息**

- 难度：⭐⭐⭐⭐ | 类型：专家设计 | 更新日期：2026-03-28 | 预计阅读时间：45 分钟
