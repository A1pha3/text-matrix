---
title: "dotnet/skills：.NET官方AI编码智能体技能库完全指南"
date: 2026-05-23T12:15:00+08:00
slug: "dotnet-skills-microsoft-agent-skills-guide"
aliases:
  - "/posts/tech/dotnet-skills-microsoft-agent-skills/"
description: "dotnet/skills是微软官方维护的AI编码智能体技能库，为Copilot CLI、Claude Code、VS Code、Cursor、Codex等主流AI编程工具提供12个专项插件，覆盖.NET开发、数据访问、性能诊断、构建优化、包管理、迁移升级、MAUI开发、AI集成、测试等全栈场景。本文解析其标准架构、各插件能力、安装配置及与Agent Skills标准的集成方式。"
draft: false
categories: ["技术笔记"]
tags: ["C#", ".NET", "AI Agent", "Agent Skills", "智能体", "微软", "Copilot", "Claude Code"]
---

# dotnet/skills：.NET 官方 AI 编码智能体技能库完全指南

## 项目概览

**dotnet/skills**（https://github.com/dotnet/skills）是微软官方 `.NET` 团队维护的 AI 编码智能体技能库，为主流 AI 编程工具提供针对 .NET 生态的专项能力扩展。截至目前仓库拥有 **2,575 Stars**、**202 Forks**，持续活跃维护中。

该仓库的关键价值在于：它将 `.NET` 开发中的专业知识封装为标准化的"技能"（Skills），使 AI 编码智能体能够准确处理 `.NET` 特有的工程问题——而不是给出泛泛的通用建议。

### 关键元数据

| 维度 | 数据 |
|------|------|
| 官方定位 | .NET Team Curated Core Skills & Custom Agents for Coding Agents |
| Stars / Forks | 2,575 / 202 |
| 活跃 Issues | 85 |
| 主要语言 | C# |
| 创建时间 | 2026-02-03 |
| 最近更新 | 2026-05-23（当日最新提交） |
| 遵循标准 | [agentskills.io](https://agentskills.io) |
| License | 官方 LICENSE 文件 |

---

## 为什么值得看

`.NET` 生态拥有大量特有的工程模式和工具链——MSBuild 项目结构、NuGet 包管理、.NET 升级迁移、ASP.NET Core 中间件、Entity Framework 数据访问——这些场景中通用 AI 建议往往不够精确甚至误导。`dotnet/skills` 的出现改变了这一局面。

微软 `.NET` 团队将多年的工程经验和实践建议封装为可被 AI 理解的技能文档，使 AI 编码智能体能够在 .NET 项目中给出真正专业级的指导。对于在 .NET 环境中使用 Copilot CLI、Claude Code、Cursor 等工具的开发者，这是目前最权威、最系统的专项技能扩展。

---

## 核心能力：12 个专项插件

### 插件一览

| 插件名称 | 定位 | 核心覆盖场景 |
|----------|------|-------------|
| `dotnet` | 核心技能 | 常见 .NET 编程任务 |
| `dotnet-data` | 数据访问 | Entity Framework 及数据层操作 |
| `dotnet-diag` | 性能诊断 | 性能调查、调试、故障分析 |
| `dotnet-msbuild` | 构建系统 | MSBuild 失败诊断、构建优化、代码质量 |
| `dotnet-nuget` | 包管理 | NuGet 依赖管理和现代化 |
| `dotnet-upgrade` | 迁移升级 | .NET 版本迁移、语言特性升级 |
| `dotnet-maui` | 跨平台 UI | .NET MAUI 环境配置和故障排查 |
| `dotnet-ai` | AI/ML 集成 | LLM 集成、智能体工作流、RAG、MCP、ML.NET |
| `dotnet-template-engine` | 模板引擎 | 模板发现、项目脚手架、模板创作 |
| `dotnet-test` | 测试 | 测试执行、诊断和迁移（MSTest 为主） |
| `dotnet-aspnet` | Web 开发 | ASP.NET Core 中间件、端点、实时通信、API 模式 |
| `dotnet11` | 新版特性 | .NET 11 新 API 和语言特性 |

### dotnet-ai：AI 与 ML 专项技能

`dotnet-ai` 是与 AI 技术最直接相关的插件，其下包含 5 个技能：

- **`mcp-csharp-create`**：C# 项目创建与结构初始化
- **`mcp-csharp-debug`**：C# 调试与问题诊断
- **`mcp-csharp-publish`**：C# 项目发布与部署
- **`mcp-csharp-test`**：C# 单元测试执行
- **`technology-selection`**：AI/ML 技术选型（涵盖 LLM 集成、智能体、RAG、MCP）

这意味着 AI 编码智能体不仅能帮你写 .NET 代码，还能帮你选型 AI 技术路线、理解 Agentic Workflow，以及接入 MCP（Model Context Protocol）协议。

### dotnet-upgrade：迁移利器

`.NET` 版本升级历来是工程痛点。`dotnet-upgrade` 技能专门处理跨框架版本的迁移任务，包括：

- 旧版 .NET Framework → .NET 6/7/8/11 的迁移路径
- 语言特性升级（新版 C# 特性适配）
- 兼容性目标调整

### dotnet-diag：生产级诊断

`dotnet-diag` 覆盖 .NET 生产环境的性能调查和故障分析，包括 dotnet-trace、dotnet-counters、dotnet-dump 等官方诊断工具的正确使用场景。

---

## Agent Skills 标准

`dotnet/skills` 遵循开源的 **[Agent Skills 标准](https://agentskills.io)**，这意味着：

1. **跨工具兼容**：技能不绑定特定 AI 产品，可用于 Copilot CLI、Claude Code、VS Code、Cursor、OpenAI Codex CLI 等任何支持该标准的平台
2. **标准化结构**：每个技能包含描述、触发条件、执行动作和验收标准，AI 智能体可理解其边界
3. **Marketplace 分发**：通过 `/plugin marketplace add dotnet/skills` 即可将整个技能库添加到 AI 编码工具

---

## 安装与配置

### Copilot CLI / Claude Code

```bash
# 1. 添加市场
/plugin marketplace add dotnet/skills

# 2. 安装所需插件
/plugin install dotnet-ai@dotnet-agent-skills
/plugin install dotnet-upgrade@dotnet-agent-skills
/plugin install dotnet-diag@dotnet-agent-skills

# 3. 重启加载插件
# 4. 查看可用技能
/skills

# 5. 查看可用智能体
/agents

# 6. 按需更新
/plugin update dotnet-ai@dotnet-agent-skills
```

### VS Code / VS Code Insiders

```jsonc
// settings.json
{
  "chat.plugins.enabled": true,
  "chat.plugins.marketplaces": ["dotnet/skills"]
}
```

### Cursor

通过 Cursor 插件市场搜索 `.NET` 安装，或本地开发模式：

```bash
# 将本地仓库链接到 Cursor 插件目录
ln -s /path/to/dotnet/skills ~/.cursor/plugins/local/dotnet-agent-skills
# 重启 Cursor 或执行 Developer: Reload Window
```

### Codex CLI

```bash
skill-installer install https://github.com/dotnet/skills/tree/main/plugins/dotnet-ai/skills/technology-selection
```

---

## 适用边界

**适合**：
- 在 .NET / C# 项目中使用 AI 编码智能体的开发者
- 需要进行 .NET 版本迁移（尤其 .NET Framework → 现代 .NET）的团队
- 使用 Entity Framework、ASP.NET Core、.NET MAUI 的工程师
- 需要在 .NET 环境中接入 LLM 或构建 AI Agent 的团队

**不适合**：
- 非 .NET 技术栈的开发者（技能库专为 .NET 生态设计）
- 寻求"通用 AI 编程建议"的场景（该仓库提供的是专项深度技能）

---

## 文章结构参考

本文覆盖了项目的主要插件和能力，以下是各专项技能的深入阅读路径：

- 想用 AI 辅助 .NET 开发 → 从 `dotnet` 核心插件开始
- 需要 LLM/RAG/MCP 集成方案 → `dotnet-ai` 插件
- 正在进行 .NET 版本迁移 → `dotnet-upgrade` 插件
- 生产环境性能问题排查 → `dotnet-diag` 插件
- 想构建自己的 Agent Skills → 参考仓库的 `.agents` 和 `AGENTS.md`

---

## 总结

`dotnet/skills` 代表了 AI 编码智能体发展的一个重要方向：**专业化垂直技能库**。它将 .NET 开发的专业知识系统化、标准化，使 AI 真正成为 .NET 工程师的专业助手，而不只是泛泛的代码补全工具。

随着 Agent Skills 标准的推广，这种"官方团队维护专项技能库"的模式可能会扩展到更多技术栈，值得持续关注。