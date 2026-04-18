---
title: "Craft Agents：4K Stars的AI Agent原生桌面应用——用自然语言操控Linear/Slack/Gmail"
date: 2026-04-18T15:45:00+08:00
slug: "craft-agents-ai-agent-native-desktop"
description: "Craft Agents是lukilabs出品的AI Agent桌面应用，基于Agent Native软件原则。用自然语言连接Linear/Gmail/Slack等60+服务，支持多LLM提供商，可视化编程体验。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "桌面应用", "MCP", "多LLM", "Craft", "工作流自动化"]
---

# Craft Agents：4K Stars的AI Agent原生桌面应用——用自然语言操控Linear/Slack/Gmail

> **目标读者**：AI助手重度用户、企业知识工作者、追求高效工作流的开发者
> **预计阅读时间**：40-50分钟
> **前置知识**：了解AI助手基本概念，有API/MCP使用经验更佳
> **难度定位**：⭐⭐⭐⭐ 专家设计

---

## §1 学习目标

1. **理解Agent Native软件原则**：什么是，为何重要
2. **掌握Craft Agents核心功能**：多会话、Sources、Skills、MCP集成
3. **能够连接外部服务**：Linear/Slack/Gmail等
4. **理解多LLM支持**：Google AI Studio/Copilot/OpenAI API等
5. **能够进行自定义开发**：Skills创建和自动化配置

---

## §2 Agent Native软件原则

### 2.1 传统软件的局限

传统软件（如Notion/Slack/Linear）设计时假设"人类是操作者"。当AI Agent介入时：
- 需要将操作分解为API调用
- 需要维护上下文状态
- 需要处理错误恢复

### 2.2 Agent Native的定义

**Agent Native软件**的设计原则：
- **自然语言优先**：用户描述目标，AI理解意图并执行
- **工具即服务**：外部能力通过Skills/Sources即插即用
- **无配置体验**：无需编辑配置文件，无需重启
- **实时响应**：变更即时生效

### 2.3 Craft Agents的实践

Craft Agents是首批基于Agent Native原则设计的桌面应用之一。用AI的视角重新设计工作流，让AI可以真正"驾驶"软件。

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

Craft Agents的核心Agent引擎建立在两大支柱之上：
- **Claude Agent SDK**：Anthropic官方Agent开发工具链，负责核心推理和工具调用
- **Craft自研增强层**：补充官方SDK的能力边界，增强对外部服务的集成

### 3.3 Sources系统

Sources是连接外部服务的方式：

| Source类型 | 示例 | 实现方式 |
|-----------|------|----------|
| **MCP Servers** | Linear, Slack | 标准MCP协议 |
| **REST APIs** | Google, Microsoft | OpenAPI规范 |
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

### 4.2 多LLM提供商

| 提供商 | 支持情况 |
|--------|----------|
| **Claude** | ✅ 官方集成 |
| **Google AI Studio** | ✅ |
| **ChatGPT Plus** | ✅ |
| **GitHub Copilot** | ✅ |
| **OpenAI API** | ✅ |
| **自定义** | ✅ |

每个工作区可设置默认LLM。

### 4.3 Craft MCP集成

Craft自家平台提供丰富的文档工具（通过MCP协议接入）：
- **Blocks操作**：创建、编辑、删除文档块
- **Collections管理**：管理文档集合和分类
- **搜索**：全文搜索和语义搜索
- **Tasks**：任务创建、分配和追踪

### 4.4 Skills系统

**创建Skill**：
```
用户：创建一个GitHub PR审查Skill
AI → 理解需求 → 生成Skill定义 → 保存到工作区
```

**导入Skill**：
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
- Label变更时创建会话
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

### 6.1 连接MCP服务

**已有MCP配置JSON？**
直接粘贴，AI处理剩余配置。

**本地MCP服务器？**
支持Stdio模式，指向npx命令、Python脚本或任意本地二进制文件。

### 6.2 连接REST API

**自定义API？**
直接粘贴OpenAPI规范、端点URL或文档截图，AI理解并引导完成配置。

### 6.3 多文件diff

VS Code风格窗口，查看每个Turn的文件变更。

---

## §7 FAQ

### Q1: Craft Agents免费吗？
核心功能开源免费（Apache 2.0许可证）。Craft云服务提供付费计划，包含额外的协作功能和团队管理能力。

### Q2: 与Claude Code桌面版有何区别？

| 特性 | Craft Agents | Claude Code桌面版 |
|------|---------------|-------------------|
| 架构 | Agent Native桌面应用 | CLI封装为桌面应用 |
| 外部服务 | Sources系统原生集成 | 需要手动配置 |
| 多会话 | Multi-Session Inbox | 单会话为主 |
| 权限控制 | 三级权限模式 | 简单确认机制 |

### Q3: Sources支持多少种服务？
支持主流的MCP协议服务，以及任何提供REST API的服务。具体数量取决于社区贡献和维护状态。

### Q4: 支持本地MCP服务器吗？
完全支持。Craft Agents支持stdio模式的MCP服务器，可以本地运行任何兼容MCP的工具。

### Q5: 如何导入Claude Code的Skills？
在Craft Agents中告诉Agent：
```
导入我在Claude Code的Skills
```
Agent会自动发现并迁移你的Skills配置。

### Q6: 数据存储在哪里？
- 云端使用Craft的服务器
- 本地部署时数据存储在你的服务器
- 支持自托管模式

### Q7: 支持中文界面？
Craft Agents有多语言支持计划，具体支持的语言版本请参考官方发布说明。

---

## §8 练习：连接外部服务

### 练习目标

使用Craft Agents连接一个真实的外部服务（以GitHub为例）

**前置准备**：
- 已安装Craft Agents
- 拥有GitHub账号
- 有一个可访问的GitHub仓库

### 详细步骤

**Step 1：安装并启动**
```bash
# macOS/Linux
curl -fsSL https://agents.craft.do/install-app.sh | bash

# Windows
irm https://agents.craft.do/install-app.ps1 | iex
```

**Step 2：首次配置**
1. 启动Craft Agents
2. 创建新工作区
3. 选择默认LLM（推荐Claude）

**Step 3：连接GitHub**
在Craft Agents对话框中输入：
```
添加GitHub作为Source
```

Craft Agents会引导你完成：
- 选择GitHub MCP服务器
- 完成OAuth授权
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
- [ ] 成功完成GitHub OAuth授权
- [ ] Agent能列出你的仓库
- [ ] Agent成功创建了Issue
- [ ] 可以在GitHub网页上看到创建的Issue

**进阶挑战**：
- 让Agent审查一个PR
- 让Agent总结某个Issue的讨论

---

## §9 相关资源

- [GitHub仓库](https://github.com/lukilabs/craft-agents-oss)
- [官方文档](https://agents.craft.do/)
- [视频演示](https://www.youtube.com/watch?v=xQouiAIilvU)
- [Discord社区](https://discord.gg/jn4EGJjrvv)

---

*🦞 撰写于2026年4月18日*
