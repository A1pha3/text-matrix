---
title: "agentmemory：基于真实世界基准的AI编码Agent持久记忆方案"
date: "2026-05-14T16:09:00+08:00"
slug: "agentmemory-persistent-memory-ai-coding-agent"
description: "agentmemory是基于iii引擎构建的AI编码Agent持久记忆系统，在真实世界基准测试中达到95.2%的检索R@5和92%的token节省，支持Claude Code、Cursor、Gemini CLI、Codex等主流Agent，提供51个MCP工具和12个自动Hook，零外部数据库依赖。"
draft: false
categories: ["技术笔记"]
tags: ["AI Coding Agent", "持久记忆", "MCP", "TypeScript", "知识图谱"]
---

# agentmemory：基于真实世界基准的AI编码Agent持久记忆方案

## 项目概览

**agentmemory** 由 rohitg00 开发，星数 **8,294**，Forks 700，是一个为 AI 编码 Agent 提供持久记忆能力的开源库，基于自研的 [iii](https://github.com/iii-hq/iii) 引擎构建。

项目解决了 AI 编码 Agent 面临的核心痛点：每次新会话都要重新向 Agent 解释上下文。agentmemory 让 Agent 记住一切，核心指标出色：R@5 检索精度 95.2%，Token 节省 92%，提供 51 个 MCP 工具和 12 个自动 Hook，零外部数据库依赖。

## 核心特性

### 多Agent共享记忆

agentmemory 支持多 Agent（Claude Code、Cursor、Gemini CLI、Codex、OpenClaw、pi、OpenCode 等）共享同一个记忆服务器。这意味着在一个 Agent 中积累的知识可以在另一个 Agent 中被调用，无需重复解释。

### 知识图谱 + 混合搜索

记忆系统不仅仅是一个键值存储，而是一个带有置信度评分、生命周期的知识图谱。它结合向量搜索和混合检索策略，能够在需要时准确召回相关的上下文。

### 基准测试表现

| 指标 | 数值 |
|------|------|
| 检索精度 R@5 | 95.2% |
| Token 节省 | 92% |
| MCP 工具数 | 51 |
| 自动 Hooks | 12 |
| 测试用例通过 | 827 |

### 安装与使用

通过 npm 安装：

```bash
npm install @agentmemory/agentmemory
```

支持多种集成方式：

- **Hooks**：为 Claude Code 等 Agent 提供 12 个自动 Hook，自动保存上下文
- **MCP**：51 个 MCP 工具供 Agent 调用
- **REST API**：提供 HTTP 接口，可被任何 Agent 通过 HTTP 调用

### 与 OpenClaw 的集成

agentmemory 提供了 [OpenClaw 集成插件](https://github.com/rohitg00/agentmemory/tree/main/integrations/openclaw)，可以通过 MCP + Plugin 的方式为 OpenClaw 增添持久记忆能力。

### 实时查看器与 iii Console

项目还提供了实时查看器（Real-Time Viewer）和 iii Console，方便可视化记忆状态、调试检索效果、监控 Agent 行为。

## 技术架构

- **语言**：TypeScript
- **引擎**：iii（自研，向量+图谱混合存储引擎）
- **依赖**：零外部数据库（SQLite 或内存存储可选）
- **测试**：827 个测试用例全部通过

## 适用场景

- 使用多编码 Agent 的团队，希望 Agent 间共享上下文
- 需要长期记忆的项目（如大型代码库、复杂业务逻辑）
- 希望减少每次对话中 token 消耗的开发者
- 构建需要 Agent 间协作的多智能体系统

---

**延伸阅读**：[GitHub 仓库](https://github.com/rohitg00/agentmemory) · [npm 包](https://www.npmjs.com/package/@agentmemory/agentmemory) · [iii 引擎](https://github.com/iii-hq/iii) · [OpenClaw 集成](integrations/openclaw/)