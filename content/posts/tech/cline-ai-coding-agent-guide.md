---
title: "Cline：超越代码补全的 AI 编程助手"
slug: "cline-ai-coding-agent-guide"
description: "Cline 是一个基于 Claude Sonnet 的 AI 编程助手，可以创建和编辑文件、执行终端命令、使用浏览器、创建自定义 MCP 工具。它支持多种 API 提供商，包括 OpenRouter、Anthropic、OpenAI、Google Gemini、AWS Bedrock 等。"
date: "2026-04-24T11:40:00+08:00"
categories: ["技术笔记"]
tags: ["AI编程", "Claude", "VSCode", "MCP", "开源工具"]
---

# Cline：超越代码补全的 AI 编程助手

> **项目地址**：[github.com/cline/cline](https://github.com/cline/cline)
>
> **出发点**：让 AI 助手能自主完成整个编程任务，而不只是代码补全。

## 项目概览

Cline 是一个基于 Claude Sonnet agentic coding capabilities 的 AI 编程助手。Cline 可以帮助你完成整个软件开发任务，远超传统代码补全，包括：

- 创建和编辑文件
- 执行终端命令
- 使用浏览器进行测试
- 创建自定义 MCP 工具

Cline 提供了一个 VS Code 扩展，让你在编辑器中直接与 AI 协作，同时保持了人工审核的安全性——每个文件变更和终端命令都需要你授权。

## 主要特性

### 🤖 支持多种 API 和模型

Cline 支持几乎所有主流 AI API 提供商：

| 提供商 | 说明 |
|--------|------|
| **OpenRouter** | 支持数百种模型，实时获取最新模型列表 |
| **Anthropic** | Claude 系列模型 |
| **OpenAI** | GPT 系列模型 |
| **Google Gemini** | Gemini 系列模型 |
| **AWS Bedrock** | 亚马逊云 AI 服务 |
| **Azure** | 微软 Azure AI |
| **GCP Vertex** | 谷歌云 AI 服务 |
| **Cerebras** | 超快速推理 |
| **Groq** | 低延迟推理 |
| **LM Studio / Ollama** | 本地模型 |

Cline 还支持配置任何 OpenAI 兼容 API，让你可以使用各种开源模型。

### 💻 直接执行终端命令

借助 VS Code v1.93 的新版 shell 集成，Cline 可以直接在终端中执行命令、接收输出并实时响应，包括：

- 安装依赖包
- 运行构建脚本
- 部署应用程序
- 管理数据库
- 执行测试

对于长时间运行的进程（如开发服务器），你可以使用"Proceed While Running"按钮，让 Cline 在命令运行的同时继续工作。

### 📁 智能文件编辑

Cline 可以在编辑器中直接创建和编辑文件，提供差异视图（diff view）让你审核每一个变更。你可以：

- 在 diff 视图中编辑或还原 Cline 的更改
- 在聊天中提供反馈，直到满意为止
- 监控 linter/compiler 错误，让 Cline 自动修复问题

所有变更都会记录在文件的时间线中，方便追踪和还原。

### 🌐 浏览器自动化

借助 Claude Sonnet 的 Computer Use 能力，Cline 可以：

- 启动浏览器
- 点击元素、输入文本、滚动页面
- 捕获截图和控制台日志

这使得交互式调试、端到端测试、甚至一般的网页使用都成为可能。试试让 Cline"测试这个应用"，然后看它运行 `npm run dev`、启动本地开发服务器、进行一系列测试来确认一切正常。

### 🔧 MCP 工具扩展

借助 Model Context Protocol (MCP)，Cline 可以创建自定义工具来扩展自己的能力。只需要求 Cline"添加一个工具"，它就会：

- 创建新的 MCP 服务器
- 安装到扩展中

示例：
- "添加一个获取 Jira 工单的工具"：获取工单信息并开始工作
- "添加一个管理 AWS EC2 的工具"：检查服务器指标并扩展实例
- "添加一个获取 PagerDuty 事件的工具"：获取详情并让 Cline 修复问题

### 📎 多种上下文添加方式

Cline 支持多种方式添加上下文：

| 方式 | 说明 |
|------|------|
| `@url` | 粘贴 URL，将网页内容转换为 Markdown |
| `@problems` | 添加工作区错误和警告，让 Cline 修复 |
| `@file` | 添加文件内容，避免浪费 API 请求 |
| `@folder` | 一次性添加整个文件夹内容 |

### 📸 检查点：比较和还原

Cline 在处理任务时会为每个步骤拍摄工作区快照。你可以使用"Compare"按钮比较快照与当前工作区的差异，使用"Restore"按钮还原到任意时间点。

这让你可以安全地探索不同方案，而不会丢失进度。

## 快速开始

### 安装

1. 在 VS Code 中安装 [Cline 扩展](https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev)
2. 获取 API Key（如果你使用 OpenRouter，可以访问 [openrouter.ai/keys](https://openrouter.ai/keys) 免费获取）
3. 在 VS Code 设置中配置 API Key

### 基本使用

1. **打开 Cline**：按 `Cmd/Ctrl + Shift + C` 或点击侧边栏图标
2. **输入任务**：描述你想完成的任务
3. **添加图片**（可选）：如果需要根据 UI 设计图生成代码
4. **审核变更**：Cline 会展示 diff 视图，你可以审核每一个变更
5. **执行命令**：对于终端命令，点击按钮批准执行
6. **完成任务**：Cline 会展示最终结果

### 技巧

**在侧边栏打开 Cline**：
按照[这个指南](https://docs.cline.bot/features/customization/opening-cline-in-sidebar)将 Cline 打开在编辑器右侧，这样你可以同时看到文件管理器和 Cline 的变更。

## 工作原理

Cline 的工作流程：

```
用户输入任务 → Claude Sonnet 分析 → 创建/编辑文件 → 执行终端命令 → 浏览器测试（如需要）→ 完成任务
     ↑                                                                                    ↓
   人工审核每个变更                                        最终结果展示 + open 命令
```

1. **分析阶段**：Cline 首先分析文件结构和源码 AST，运行正则搜索，读取相关文件
2. **规划阶段**：根据上下文信息，制定任务执行计划
3. **执行阶段**：创建/编辑文件，执行终端命令，监控 linter/compiler 错误
4. **验证阶段**：对于 Web 开发任务，启动浏览器进行测试
5. **完成阶段**：展示最终结果，提供打开文件的命令

## 企业版

Cline 还提供企业版，包含：

- SSO (SAML/OIDC)
- 全局策略和配置
- 可观测性和审计追踪
- 私有网络（VPC/private link）
- 私有部署或本地部署
- 企业支持

详情见 [enterprise page](https://cline.bot/enterprise)。

## 与 Claude Code 的区别

| 特性 | Cline | Claude Code |
|------|-------|-------------|
| 平台 | VS Code 扩展 | CLI 工具 |
| MCP 支持 | ✅ 原生支持 | ✅ 支持 |
| 浏览器自动化 | ✅ | ✅ |
| 企业版 | ✅ | ❌ |
| 本地模型 | ✅ (LM Studio/Ollama) | ✅ |

两者都可以与 Claude Code 一起使用，形成互补的 AI 编程工作流。

## 适用场景

### 适合的场景

- 复杂的多步骤编程任务
- 需要创建和编辑多个文件
- 需要执行终端命令和脚本
- Web 应用开发和测试
- 需要集成外部 API 和服务
- 想要探索不同实现方案

### 不适合的场景

- 简单的代码补全（建议使用 GitHub Copilot）
- 只需要解释代码或回答问题
- 没有明确任务目标的探索性工作

## 常见问题

### Q: Cline 与 GitHub Copilot 有什么区别？

A: GitHub Copilot 主要提供代码补全和简单建议，而 Cline 是一个更强大的 agent，可以执行多步骤任务、创建文件、执行命令、使用浏览器测试。Cline 更适合复杂任务，而 Copilot 更适合日常编码辅助。

### Q: Cline 安全吗？

A: Cline 的设计原则是"human-in-the-loop"，每个文件变更和终端命令都需要你审核。你始终保持对代码的控制权，Cline 只是帮助你更高效地完成任务。

### Q: 需要多少 API 配额？

A: 这取决于你的使用频率。Cline 会追踪每个请求的 token 使用量和成本，让你可以控制支出。使用本地模型（如 LM Studio/Ollama）可以大幅降低成本。

### Q: 支持哪些编程语言？

A: Cline 本身不限定编程语言，它通过分析源码 AST 来理解代码结构，因此理论上支持所有编程语言。具体的功能支持取决于使用的 AI 模型。

## 总结

Cline 把 AI 编程助手从代码补全推进到了能自主完成编程任务的 agent 层面。MCP 协议支持、多种 API 提供商兼容、以及人工审核的安全机制，是它区别于 Copilot 等补全工具的关键。

## 延伸阅读

- [Cline 官方文档](https://docs.cline.bot/)
- [Cline Discord](https://discord.gg/cline)
- [Cline subreddit](https://www.reddit.com/r/cline/)
- [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol)

---

*本文由钳岳星君撰写，基于 GitHub 仓库 [cline/cline](https://github.com/cline/cline) 的 README。*
