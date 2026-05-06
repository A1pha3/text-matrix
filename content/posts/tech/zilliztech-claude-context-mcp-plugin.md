---
title: "zilliztech/claude-context：MCP语义代码搜索插件，让Claude理解整个代码库"
slug: zilliztech-claude-context-mcp-plugin
date: "2026-04-22T16:35:00+08:00"
description: "zilliztech/claude-context 是一个 MCP 插件，为 Claude Code 提供语义代码搜索功能，使用 Zilliz Cloud 向量数据库存储代码库，实现百万行代码的精准检索。"
categories: ["技术笔记"]
tags: ["MCP", "Claude Code", "语义搜索", "向量数据库", "Zilliz"]
---

# zilliztech/claude-context：MCP语义代码搜索插件，让Claude理解整个代码库

## 🎯 概述

**zilliztech/claude-context** 是一个 MCP（Model Context Protocol）插件，为 Claude Code 和其他 AI 编码助手提供**语义代码搜索**功能，将整个代码库作为上下文提供给 AI。

> **GitHub**: [zilliztech/claude-context](https://github.com/zilliztech/claude-context)  
> **Stars**: 6,906 ⭐  
> **许可证**: MIT  
> **依赖**: Node.js 20+

### 核心特点

| 特点 | 说明 |
|------|------|
| **全代码库上下文** | 语义搜索百万行代码 |
| **成本优化** | 按需加载相关代码，避免全量输入 |
| **多客户端兼容** | Claude Code、Codex CLI、Gemini CLI |
| **零配置接入** | 一键添加 MCP 服务器 |

---

## ⚡ 快速开始

### 1. 配置 Zilliz Cloud

注册 [Zilliz Cloud](https://cloud.zilliz.com/signup) 获取免费向量数据库 API Key。

### 2. 添加 MCP 服务器

```bash
claude mcp add claude-context \
  -e OPENAI_API_KEY=sk-your-openai-api-key \
  -e MILVUS_ADDRESS=your-zilliz-cloud-public-endpoint \
  -e MILVUS_TOKEN=your-zilliz-cloud-api-key \
  -- npx @zilliz/claude-context-mcp@latest
```

### 3. 开始使用

现在 Claude Code 可以语义搜索整个代码库：

```bash
# 询问关于代码库的问题
claude "这段代码的架构是怎样的？"
```

---

## 💡 工作原理

```
代码库 → 向量化存储(Zilliz Cloud) → 语义搜索 → 上下文注入 → Claude 回答
```

1. **代码向量化**：将代码片段转换为向量嵌入
2. **语义存储**：存储在 Zilliz Cloud 向量数据库
3. **智能检索**：根据查询语义检索相关代码
4. **上下文注入**：将检索结果注入 Claude 上下文

---

## 🔗 资源链接

| 资源 | 链接 |
|------|------|
| GitHub | [zilliztech/claude-context](https://github.com/zilliztech/claude-context) |
| Zilliz Cloud | [cloud.zilliz.com](https://cloud.zilliz.com) |
| VS Code 扩展 | [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=zilliz.semanticcodesearch) |

---

*🦞 zilliztech/claude-context：让 AI Agent 真正理解整个代码库。*
