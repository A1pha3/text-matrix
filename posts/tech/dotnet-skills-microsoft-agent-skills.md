---
title: "dotnet/skills：微软官方出品的 .NET AI编程智能体技能库"
date: "2026-05-22T09:10:00+08:00"
slug: "dotnet-skills-microsoft-agent-skills"
description: "dotnet/skills 是微软 .NET 团队维护的官方技能库，为 AI 编程智能体提供 12 个专项插件，涵盖 Web开发、数据访问、性能诊断、包管理、升级迁移、MAUI、机器学习等场景。支持 Copilot CLI、Claude Code、Cursor、VS Code 等主流 AI 编程工具。"
draft: false
categories: ["技术笔记"]
tags: [".NET", "AI编程智能体", "微软", "MCP", "C#"]
---

# dotnet/skills：微软官方出品的 .NET AI编程智能体技能库

AI 编程工具能写代码，但遇上具体的 .NET 场景——Entity Framework 查询性能怎么查、.NET 11 新 API 怎么用、MSBuild 编译失败怎么诊断——经常卡在"知道要做什么，但不知道具体怎么操作"。**dotnet/skills** 解决的就是这个问题。

这是微软 .NET 团队维护的官方技能库，为 AI 编程智能体提供 12 个专项插件，涵盖 Web 开发、数据访问、性能诊断、包管理、升级迁移、MAUI 开发等场景。支持 Copilot CLI、Claude Code、Cursor、VS Code 等主流 AI 编程工具。

## 核心价值：让 AI 智能体真正能干活

AI 编程工具在通用代码生成上越来越强，但 .NET 生态有自己的上下文：csproj 文件结构、dotnet CLI 命令、EF Core 迁移、ASP.NET Core 中间件……没有针对性的技能提示，智能体只能靠训练数据里残缺的信息猜着写，容易出纰漏。

dotnet/skills 的思路是：把 .NET 团队自己在内部编程中积累的实战技能，显式地灌给 AI 智能体。每个插件里的 skill 文件，记录的不是通用编程知识，而是 .NET 特定的操作规程、诊断命令和避坑经验。

## 包含哪些插件

仓库一共收录了 12 个插件，覆盖 .NET 开发的主要垂直场景：

| 插件 | 职责 |
|------|------|
| `dotnet` | 通用 .NET 技能：常见编码任务的标准操作路径 |
| `dotnet-data` | Entity Framework 和数据访问相关任务 |
| `dotnet-diag` | 性能调查、调试和事件分析 |
| `dotnet-msbuild` | MSBuild 构建诊断、性能优化、代码质量 |
| `dotnet-nuget` | NuGet 包管理和依赖现代化 |
| `dotnet-upgrade` | .NET 版本迁移：框架、语言特性、兼容性目标 |
| `dotnet-maui` | .NET MAUI 开发环境配置和故障排除 |
| `dotnet-ai` | .NET AI/ML：LLM 集成、Agent 工作流、RAG、MCP、ML.NET |
| `dotnet-template-engine` | .NET 模板引擎：模板发现、项目脚手架 |
| `dotnet-test` | 测试运行、诊断和迁移：MSTest 工作流 |
| `dotnet-aspnet` | ASP.NET Core：中间件、端点、实时通信、API 模式 |
| `dotnet11` | .NET 11 新 API 和语言特性 |

每个插件里的技能文件（`.md` 或遵循 agentskills.io 标准的格式），对应一个具体操作场景。AI 智能体在执行相关任务时加载对应技能文件，即可获得针对性的操作指引。

## 如何安装使用

### Copilot CLI / Claude Code

最直接的方式，通过 `/plugin` 命令安装：

```
/plugin marketplace add dotnet/skills
/plugin install <plugin>@dotnet-agent-skills
```

例如安装 `dotnet-data` 插件：

```
/plugin install dotnet-data@dotnet-agent-skills
```

安装后查看可用技能和 Agent：

```
/skills
/agents
```

按需更新插件：

```
/plugin update <plugin>@dotnet-agent-skills
```

### VS Code / VS Code Insiders（预览）

在 `settings.json` 中启用插件市场：

```jsonc
{
  "chat.plugins.enabled": true,
  "chat.plugins.marketplaces": ["dotnet/skills"]
}
```

配置后在 Copilot Chat 中输入 `/plugins` 浏览和安装插件。

### Cursor

Cursor 支持直接从 Cursor Marketplace 搜索并安装 `.NET` 相关插件：

1. 打开 Cursor Marketplace 面板
2. 搜索 `.NET` 或访问 [cursor.com/marketplace](https://cursor.com/marketplace)
3. 安装所需插件

如需本地开发或未发布版本，可将仓库 checkout 到 `~/.cursor/plugins/local/dotnet-agent-skills`，然后重启 Cursor。

### Codex CLI

skills 文件遵循 [agentskills.io](https://agentskills.io) 开放标准，可配合 OpenAI Codex 使用。使用 `skill-installer` CLI 安装单个技能：

```bash
$ skill install https://github.com/dotnet/skills/blob/main/plugins/dotnet-ai/skill.md
```

## dotnet-ai 插件：.NET AI 能力的重点区域

在所有插件中，`dotnet-ai` 是最值得关注的一个。它覆盖 .NET 上 AI 落地的核心场景：

- **LLM 集成**：在 .NET 应用中接入 OpenAI、Azure OpenAI、Hugging Face 等模型
- **Agentic 工作流**：用 .NET 实现多步骤自主执行链
- **RAG 管道**：检索增强生成的技术选型和实现
- **MCP 支持**：Model Context Protocol 在 .NET 生态的集成方式
- **经典 ML**：ML.NET 的使用路径和典型场景

如果你在 .NET 环境中做 AI 应用选型或架构设计，先看这个插件。

## 适用边界

**适合的场景：**
- 团队使用 Claude Code、Copilot CLI、Cursor 等工具做 .NET 开发
- 需要在 .NET 项目中接入 LLM 或搭建 AI 工作流
- 项目涉及跨 .NET 版本迁移（尤其是 .NET Framework → .NET 6/7/8/11）
- 需要 EF Core、ASP.NET Core、MAUI 等特定技术栈的深度诊断支持

**不太适合的场景：**
- 纯通用编程问题，不涉及 .NET 特定操作
- 需要在非 Windows 环境运行完整的 .NET 工具链（部分插件对环境有要求）

## 相关资源

- [Dashboard（技能准确率和效率评分趋势）](https://dotnet.github.io/skills/)
- [agentskills.io 标准规范](https://agentskills.io)
- [npm 包（chrome-devtools-mcp）](https://npmjs.org/package/chrome-devtools-mcp)

---

**总结一下：** dotnet/skills 的核心价值不是"多了什么新能力"，而是把 .NET 团队自己积累的实战操作规程，变成 AI 智能体可以直接调用的技能文件。如果你做 .NET 开发 + AI 编程工具，这是一个值得先装上的基础技能库。