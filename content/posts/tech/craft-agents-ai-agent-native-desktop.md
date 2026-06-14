---
title: "Craft Agents：4K Stars的AI Agent原生桌面应用——用自然语言操控Linear/Slack/Gmail"
date: "2026-04-18T15:45:00+08:00"
slug: "craft-agents-ai-agent-native-desktop"
description: "Craft Agents是lukilabs出品的AI Agent桌面应用，基于Agent Native软件原则。用自然语言连接Linear/Gmail/Slack等60+服务，支持多LLM提供商，可视化编程体验。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "桌面应用", "MCP", "多LLM", "Craft", "工作流自动化"]
---

# Craft Agents：4K Stars 的 AI Agent 原生桌面应用——用自然语言操控 Linear/Slack/Gmail

> **目标读者**：AI 助手重度用户、企业知识工作者、追求高效工作流的开发者
> **预计阅读时间**：40-50 分钟
> **前置知识**：了解 AI 助手基本概念，有 API/MCP 使用经验更佳
> **难度定位**：⭐⭐⭐⭐ 专家设计

---

## §1 学习目标

1. **理解 Agent Native 软件原则**：什么是，为何重要
2. **掌握 Craft Agents 核心功能**：多会话、Sources、Skills、MCP 集成
3. **能够连接外部服务**：Linear/Slack/Gmail 等
4. **理解多 LLM 支持**：Google AI Studio/Copilot/OpenAI API 等
5. **能够进行自定义开发**：Skills 创建和自动化配置

---

## §2 Agent Native 软件原则

### 2.1 传统软件的局限

传统软件（如 Notion/Slack/Linear）设计时假设"人类是操作者"。当 AI Agent 介入时：
- 需要将操作分解为 API 调用
- 需要维护上下文状态
- 需要处理错误恢复

### 2.2 Agent Native 的定义

**Agent Native 软件**的设计原则：
- **自然语言优先**：用户描述目标，AI 理解意图并执行
- **工具即服务**：外部能力通过 Skills/Sources 即插即用
- **无配置体验**：无需编辑配置文件，无需重启
- **实时响应**：变更即时生效

### 2.3 Craft Agents 的实践

Craft Agents 是首批基于 Agent Native 原则设计的桌面应用之一。用 AI 的视角重新设计工作流，让 AI 可以真正"驾驶"软件。

---

## §3 核心架构

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                   Craft Agents 桌面应用                  │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │                  UI Layer                       │    │
│  │  (Electron + 多会话管理 + 状态系统)              │    │
│  └─────────────────────────────────────────────────┘    │
│                           │                              │
│  ┌────────────────────────┴────────────────────────┐   │
│  │              Agent Engine Layer                   │   │
│  │  (Claude Agent SDK + Craft自研增强层)         │   │
│  └─────────────────────────────────────────────────┘    │
│                           │                              │
│  ┌────────────────────────┴────────────────────────┐   │
│  │              Integration Layer                    │   │
│  │  (Sources + Skills + MCP Servers)                │   │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Agent Engine

Craft Agents 的核心 Agent 引擎建立在两大支柱之上：
- **Claude Agent SDK**：Anthropic 官方 Agent 开发工具链，负责核心推理和工具调用
- **Craft 自研增强层**：补充官方 SDK 的能力边界，增强对外部服务的集成

### 3.3 Sources 系统

Sources 是连接外部服务的方式：

| Source 类型 | 示例 | 实现方式 |
|-----------|------|----------|
| **MCP Servers** | Linear, Slack | 标准 MCP 协议 |
| **REST APIs** | Google, Microsoft | OpenAPI 规范 |
| **本地文件** | 文件系统 | Stdio MCP |

**连接示例**：
```
用户：添加Linear作为Source
AI → 发现Linear公共API和MCP服务器 → 读取文档 → 配置凭据 → 完成连接
```

---

## §4 核心功能详解

### 4.1 多会话收件箱（Multi-Session Inbox）

- **会话管理**：状态工作流（Todo/In Progress/Done）
- **标记系统**：快速分类和筛选
- **会话共享**：团队协作

### 4.2 多 LLM 提供商

| 提供商 | 支持情况 |
|--------|----------|
| **Claude** | ✅ 官方集成 |
| **Google AI Studio** | ✅ |
| **ChatGPT Plus** | ✅ |
| **GitHub Copilot** | ✅ |
| **OpenAI API** | ✅ |
| **自定义** | ✅ |

每个工作区可设置默认 LLM。

### 4.3 Craft MCP 集成

Craft 自家平台提供丰富的文档工具（通过 MCP 协议接入）：
- **Blocks 操作**：创建、编辑、删除文档块
- **Collections 管理**：管理文档集合和分类
- **搜索**：全文搜索和语义搜索
- **Tasks**：任务创建、分配和追踪

### 4.4 Skills 系统

**创建 Skill**：
```
用户：创建一个GitHub PR审查Skill
AI → 理解需求 → 生成Skill定义 → 保存到工作区
```

**导入 Skill**：
```
用户：从Claude Code导入我的Skills
AI → 发现Claude Code配置 → 迁移所有Skills
```

### 4.5 权限模式（Permission Modes）

| 模式 | 描述 | 适用场景 |
|------|------|----------|
| **Explore** | 探索模式，禁止修改 | 新接触 |
| **Ask to Edit** | 询问确认后执行 | 谨慎场景 |
| **Auto** | 自动执行 | 信任环境 |

### 4.6 自动化（Automations）

基于事件的触发器：
- Label 变更时创建会话
- 定时执行
- 工具使用时触发

---

## §5 安装与快速开始

### 5.1 一键安装

**macOS/Linux**：
```bash
curl -fsSL https://agents.craft.do/install-app.sh | bash
```

**Windows (PowerShell)**：
```powershell
irm https://agents.craft.do/install-app.ps1 | iex
```

### 5.2 源码构建

```bash
git clone https://github.com/lukilabs/craft-agents-oss.git
cd craft-agents-oss
bun install
bun run electron:start
```

### 5.3 依赖要求

- Node.js
- Bun（用于开发）
- Electron

---

## §6 使用指南

### 6.1 连接 MCP 服务

**已有 MCP 配置 JSON？**
直接粘贴，AI 处理剩余配置。

**本地 MCP 服务器？**
支持 Stdio 模式，指向 npx 命令、Python 脚本或任意本地二进制文件。

### 6.2 连接 REST API

**自定义 API？**
直接粘贴 OpenAPI 规范、端点 URL 或文档截图，AI 理解并引导完成配置。

### 6.3 多文件 diff

VS Code 风格窗口，查看每个 Turn 的文件变更。

---

## §7 FAQ

### Q1: Craft Agents 免费吗？
核心功能开源免费（Apache 2.0 许可证）。Craft 云服务提供付费计划，包含额外的协作功能和团队管理能力。

### Q2: 与 Claude Code 桌面版有何区别？

| 特性 | Craft Agents | Claude Code 桌面版 |
|------|---------------|-------------------|
| 架构 | Agent Native 桌面应用 | CLI 封装为桌面应用 |
| 外部服务 | Sources 系统原生集成 | 需要手动配置 |
| 多会话 | Multi-Session Inbox | 单会话为主 |
| 权限控制 | 三级权限模式 | 简单确认机制 |

### Q3: Sources 支持多少种服务？
支持主流的 MCP 协议服务，以及任何提供 REST API 的服务。具体数量取决于社区贡献和维护状态。

### Q4: 支持本地 MCP 服务器吗？
完全支持。Craft Agents 支持 stdio 模式的 MCP 服务器，可以本地运行任何兼容 MCP 的工具。

### Q5: 如何导入 Claude Code 的 Skills？
在 Craft Agents 中告诉 Agent：
```
导入我在Claude Code的Skills
```
Agent 会自动发现并迁移你的 Skills 配置。

### Q6: 数据存储在哪里？
- 云端使用 Craft 的服务器
- 本地部署时数据存储在你的服务器
- 支持自托管模式

### Q7: 支持中文界面？
Craft Agents 有多语言支持计划，具体支持的语言版本请参考官方发布说明。

---

## §8 练习：连接外部服务

### 练习目标

使用 Craft Agents 连接一个真实的外部服务（以 GitHub 为例）

**前置准备**：
- 已安装 Craft Agents
- 拥有 GitHub 账号
- 有一个可访问的 GitHub 仓库

### 详细步骤

**Step 1：安装并启动**
```bash
# macOS/Linux
curl -fsSL https://agents.craft.do/install-app.sh | bash

# Windows
irm https://agents.craft.do/install-app.ps1 | iex
```

**Step 2：首次配置**
1. 启动 Craft Agents
2. 创建新工作区
3. 选择默认 LLM（推荐 Claude）

**Step 3：连接 GitHub**
在 Craft Agents 对话框中输入：
```
添加GitHub作为Source
```

Craft Agents 会引导你完成：
- 选择 GitHub MCP 服务器
- 完成 OAuth 授权
- 选择要访问的仓库权限

**Step 4：验证连接**
输入：
```
列出我的GitHub仓库
```
你应该能看到仓库列表。

**Step 5：执行实际操作**
输入：
```
为我的第一个仓库创建一个新issue
```

### 验证标准
- [ ] 成功完成 GitHub OAuth 授权
- [ ] Agent 能列出你的仓库
- [ ] Agent 成功创建了 Issue
- [ ] 可以在 GitHub 网页上看到创建的 Issue

**进阶挑战**：
- 让 Agent 审查一个 PR
- 让 Agent 总结某个 Issue 的讨论

---

## §9 相关资源

- [GitHub仓库](https://github.com/lukilabs/craft-agents-oss)
- [官方文档](https://agents.craft.do/)
- [视频演示](https://www.youtube.com/watch?v=xQouiAIilvU)
- [Discord社区](https://discord.gg/jn4EGJjrvv)

---

*🦞 撰写于 2026 年 4 月 18 日*
