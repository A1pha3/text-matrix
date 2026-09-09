---
title: "zilliztech/claude-context：MCP 语义代码搜索插件，让 Claude 理解整个代码库"
slug: zilliztech-claude-context-mcp-plugin
github_repo: "zilliztech/claude-context"
date: "2026-04-22T16:35:00+08:00"
description: "zilliztech/claude-context 是一个 MCP 插件，为 Claude Code 等 AI 编码助手提供混合检索（BM25 + 稠密向量）代码搜索，代码库入库 Zilliz Cloud 向量数据库，按需加载相关代码，官方评估约可节省 40% token。"
categories: ["技术笔记"]
tags: ["MCP", "Claude Code", "向量数据库"]
---

# zilliztech/claude-context：MCP 语义代码搜索插件，让 Claude 理解整个代码库

## 概述

**zilliztech/claude-context** 是一个 MCP（Model Context Protocol）插件，为 Claude Code 及其他 AI 编码助手提供代码库级语义搜索。它先把整个代码库索引进 Zilliz Cloud 向量数据库，之后按查询相关度只把命中的代码片段送入模型上下文，而不是每次把整个目录喂给 Claude。

> **GitHub**: [zilliztech/claude-context](https://github.com/zilliztech/claude-context)  
> **许可证**: MIT  
> **运行时**: Node.js ≥ 20

### 解决什么问题

直接读整个代码库代价很高：目录越大，上下文占得越多，费用越高。claude-context 的思路是**离线建索引，在线按需召回**——把代码存成向量，回答问题时只检索并注入相关片段。官方给出的对照评估约为**同等的检索质量下节省 40% token**。

### 核心特点

| 特点 | 说明 |
|------|------|
| **全库上下文** | 一次索引百万行代码，无需多轮翻找 |
| **混合检索** | 同时用 BM25 关键词与向量语义召回，召回更准 |
| **按需加载** | 只把相关代码送入上下文，控制成本 |
| **多端兼容** | Claude Code、Codex CLI、Gemini CLI、Cursor 等十余种客户端 |

---

## 快速开始

### 1. 前置条件

- 在 [Zilliz Cloud](https://cloud.zilliz.com/signup) 注册，创建一个免费向量数据库，拿到公网地址 `MILVUS_ADDRESS` 和 API Key `MILVUS_TOKEN`。
- 一个可用的 OpenAI API Key（用于 embedding 模型，形如 `sk-...`）。

### 2. 为 Claude Code 添加 MCP 服务器

```bash
claude mcp add claude-context \
  -e OPENAI_API_KEY=sk-your-openai-api-key \
  -e MILVUS_ADDRESS=your-zilliz-cloud-public-endpoint \
  -e MILVUS_TOKEN=your-zilliz-cloud-api-key \
  -- npx @zilliz/claude-context-mcp@latest
```

### 3. 使用

在项目目录启动 Claude Code，依次执行：

```text
Index this codebase            # 索引当前代码库
Check the indexing status      # 查看索引进度
Find functions that handle user authentication   # 用自然语言搜索
```

三条即可跑通：索引、查状态、语义检索。

---

## 提供的 MCP 工具

| 工具 | 作用 |
|------|------|
| `index_codebase` | 为当前目录建立索引，用于混合检索 |
| `search_code` | 用自然语言检索已索引代码库 |
| `clear_index` | 清空某个代码库的索引 |
| `get_indexing_status` | 查询索引状态，显示进行中代码库的进度百分比 |

---

## 工作原理

```
代码库 → 分段 → 稀疏(BM25) + 稠密(Embedding)向量 → 存入 Zilliz Cloud → 查询时混合召回 → 注入上下文 → 模型作答
```

1. **分段与特征化**：把代码拆成片段，同时生成 BM25 关键词信号和 Embedding 向量。
2. **向量入库**：特征写入 Zilliz Cloud 向量数据库，形成可检索索引。
3. **混合召回**：查询时关键词与向量双路并用，取相关片段。
4. **上下文注入**：把召回结果送回 Claude 当前上下文。

---

## 进阶配置

- **更换嵌入模型**：默认用 OpenAI embedding，可切换 `text-embedding-3-large`、`voyage-code-3` 等其他提供方（详见[各嵌入商配置示例](https://github.com/zilliztech/claude-context/blob/master/packages/mcp/README.md#embedding-provider-configuration)）。
- **文件包含 / 排除**：可自定义哪些文件入索引、哪些跳过，规则说明见[File Inclusion & Exclusion Rules](https://github.com/zilliztech/claude-context/blob/master/docs/dive-deep/file-inclusion-rules.md)。
- **自定义环境变量**：各 MCP 客户端的环境变量配置见 [Environment Variables Guide](https://github.com/zilliztech/claude-context/blob/master/docs/getting-started/environment-variables.md)。

---

## 支持的客户端

除 Claude Code 外，官方给出了 Codex CLI（TOML）、Gemini CLI、Qwen Code、Cursor、Void、Claude Desktop、Windsurf、VS Code、Cherry Studio、Cline、Augment、Roo Code、Zencoder 及 LangChain / LangGraph 的接入方式。服务器走标准 stdio 传输，任意兼容 MCP 的客户端都可用 `npx @zilliz/claude-context-mcp@latest` 拉起。

---

## 资源链接

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | [zilliztech/claude-context](https://github.com/zilliztech/claude-context) |
| Zilliz Cloud | [cloud.zilliz.com](https://cloud.zilliz.com) |
| 评估数据 | [evaluation 目录](https://github.com/zilliztech/claude-context/tree/master/evaluation) |