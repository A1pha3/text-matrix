---
title: "Supermemory：AI时代的记忆与上下文引擎完全指南"
date: "2026-05-31T20:07:02+08:00"
slug: "supermemory-ai-memory-context-engine-guide"
description: "Supermemory是面向AI的记忆与上下文引擎，在LongMemEval、LoCoMo、ConvoMem三大AI记忆基准上均排名第一。本文详细解析其核心记忆结构、用户画像系统、混合搜索、Connectors生态、多模态提取能力，以及面向AI产品开发者的单API集成方案。"
draft: false
categories: ["技术笔记"]
tags: ["AI记忆", "Supermemory", "RAG", "MCP", "上下文管理"]
---

# Supermemory：AI 时代的记忆与上下文引擎完全指南

当前几乎所有 AI 工具——ChatGPT、Claude、Cursor——在每次新对话时都会"失忆"。用户不得不反复解释自己的偏好、正在做的项目、过往讨论的背景。**Supermemory** 试图解决这个问题：让 AI 在跨会话中积累、检索和利用个人上下文，成为真正的"第二大脑"。

## 项目概览

| 指标 | 数值 |
|------|------|
| 仓库 | [supermemoryai/supermemory](https://github.com/supermemoryai/supermemory) |
| Stars | 23,042 |
| Forks | 2,085 |
| 主要语言 | TypeScript |
| 基准排名 | LongMemEval #1、LoCoMo #1、ConvoMem #1 |

## 为什么值得看

Supermemory 不仅仅是一个"记住对话"的工具，它在三个行业公认的记忆类 AI 基准测试中同时排名第一，验证了其记忆提取和检索能力的专业性。它的定位更接近一个**面向 AI 产品开发者的记忆基础设施**，而不是一个简单的聊天插件。

## 核心能力解析

### 记忆结构与时间维度

Supermemory 的记忆系统不是静态的向量存储，它具备处理时间维度信息的能力：

- **自动遗忘**：能够识别过期的信息并主动遗忘
- **矛盾检测**：当新信息与已有事实冲突时，系统能够识别并处理
- **增量更新**：随着对话增加，记忆库动态扩展而非简单堆叠

这一点对于长期使用的个人 AI 助手尤为重要——它避免了记忆库随时间膨胀导致的检索质量下降。

### 用户画像系统

通过 `profile()` 接口，可以在 ~50ms 内获取用户的稳定事实（long-term facts）和近期活动（recent context）：

```typescript
const { profile, searchResults } = await client.profile({
  containerTag: "user_123",
  q: "What programming style does the user prefer?",
});

// profile.static → ["Loves TypeScript", "Prefers functional patterns"]
// profile.dynamic → ["Working on API integration"]
```

`containerTag`（容器标签）是 Supermemory 组织记忆的基本单元，可以按项目、用户或场景分离不同的上下文域。

### 混合搜索：RAG + Memory

传统的 RAG（检索增强生成）只能检索知识库文档，而 Supermemory 将 RAG 和个性化记忆融合在同一个查询中。搜索结果既包含知识库中的通用信息，也包含与该用户相关的个性化上下文。

### Connectors 生态

Supermemory 支持与主流数据源自动同步：

- Google Drive
- Gmail
- Notion
- OneDrive
- GitHub

这些连接器通过 Webhook 实现实时同步，不需要手动导入。Connectors 的存在使得 Supermemory 不仅仅是对话记忆工具，而是一个可以主动抓取外部信息并纳入记忆体系的系统。

### 多模态提取

Supermemory 的提取器支持：

| 类型 | 处理方式 |
|------|----------|
| PDF | 文本提取 |
| 图片 | OCR |
| 视频 | 字幕转录 |
| 代码 | AST 感知分块（保留代码结构） |

上传文件后，系统自动判断内容类型并使用对应提取器处理，不需要用户手动指定。

### Supermemory API：面向 AI 产品开发者

如果你是 AI 应用或 Agent 的开发者，Supermemory 提供了完整的上下文层 API：

```typescript
import Supermemory from "supermemory";

const client = new Supermemory();

// 存储对话
await client.add({
  content: "User loves TypeScript and prefers functional patterns",
  containerTag: "user_123",
});

// 获取用户画像 + 相关记忆
const { profile, searchResults } = await client.profile({
  containerTag: "user_123",
  q: "What programming style does the user prefer?",
});
```

Python SDK 同等能力：

```python
from supermemory import Supermemory
client = Supermemory()
client.add(content="...", container_tag="user_123")
result = client.profile(container_tag="user_123", q="...")
print(result.profile.static)
```

**核心卖点**：不需要配置向量数据库、不需要设计 embedding 流水线、不需要研究 chunking 策略——一个 `client.add()` 搞定记忆存储，一个 `client.profile()` 搞定记忆检索。

### MCP 服务器

Supermemory 还提供了标准 MCP（Model Context Protocol）服务器实现，可接入任何兼容 MCP 的 AI 客户端：

```json
{
  "mcpServers": {
    "supermemory": {
      "url": "https://mcp.supermemory.ai/mcp"
    }
  }
}
```

支持客户端：Claude Desktop、Cursor、Windsurf、VS Code、Claude Code、OpenCode、OpenClaw、Hermes。

快速安装 MCP：

```bash
npx -y install-mcp@latest https://mcp.supermemory.ai/mcp --client claude --oauth=yes
```

### 面向 C 端用户的 App

Supermemory 也提供了面向终端用户的网页应用和浏览器插件，无需任何代码即可使用。App 包含内置 Agent「Nova」，可以直接对话并自动记住对话中的关键信息。

## Supermemory Plugins

Supermemory 官方为多个主流 AI 工具提供了插件实现：

- [OpenClaw 插件](https://github.com/supermemoryai/openclaw-supermemory)
- [Claude Code 插件](https://github.com/supermemoryai/claude-supermemory)
- [OpenCode 插件](https://github.com/supermemoryai/opencode-supermemory)
- [Hermes Agent Provider](https://github.com/NousResearch/hermes-agent)（Supermemory 作为 Hermes 的 memory provider）

## 适用边界

**适合**：
- 需要 AI 助手记住跨会话上下文的个人用户
- 开发 AI 产品（助手、Agent、应用），需要将记忆能力快速集成到产品中
- 需要 RAG + 个性化记忆融合检索的场景

**不适合**：
- 需要严格数据主权控制的场景（云服务模式，数据需要离开本地）
- 需要毫秒级实时性的极高并发场景（当前版本面向低频记忆查询优化）
- 完全不需要记忆能力的单次任务工具

## 与其他记忆工具对比

Supermemory 与 OpenAI Memory、[Recall](https://github.com) 等竞品的核心差异在于：

1. **基准验证**：三大行业基准同时第一，不是营销宣传
2. **多客户端插件生态**：覆盖主流 AI 开发工具，而非单一客户端
3. **开发者优先**：提供完整的 API/SDK，而非仅提供聊天界面
4. **时间维度**：主动遗忘和矛盾检测使记忆库随时间保持高质量

## 结语

Supermemory 提供了一个在 AI 应用中快速集成记忆能力的完整方案。对于 Agent 开发者而言，它省去了从零构建记忆系统的工程成本；对于终端用户而言，它让 AI 真正开始"认识"使用它的人。跨会话记忆正在成为 AI 助手实用性的分水岭，Supermemory 是目前这个方向上基准成绩最好的开源实现。
