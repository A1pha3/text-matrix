---
title: "Plannotator：AI 编码 Agent 交互式计划与代码审查工具完全指南"
date: 2026-03-31T15:40:00+08:00
slug: "plannotator-ai-code-review-guide"
description: "全面解析 Plannotator (3.7k Stars)：交互式计划与代码审查工具，支持 Claude Code/Codex/OpenCode/Pi。可视化审核 AI 计划，端到端加密，零知识存储。"
draft: false
categories: ["技术笔记"]
tags: ["Plannotator", "AI Agent", "Claude Code", "Codex", "OpenCode", "代码审查", "计划审查"]
---

# Plannotator：AI 编码 Agent 交互式计划与代码审查工具完全指南

## §1 学习目标

完成本文档后，你将能够：

- ✅ 理解 Plannotator 的核心定位与设计理念
- ✅ 掌握 Plannotator 的五大核心功能
- ✅ 熟练安装和配置 Plannotator（支持 Claude Code、Copilot CLI、OpenCode、Pi、Codex）
- ✅ 使用 Visual Plan Review 审核 Agent 计划
- ✅ 使用 Code Review 功能审查代码差异
- ✅ 配置团队协作与分享功能
- ✅ 理解端到端加密原理
- ✅ 为 Plannotator 贡献代码

---

## §2 项目概述

### 2.1 什么是 Plannotator？

**Plannotator**（官方仓库：[backnotprop/plannotator](https://github.com/backnotprop/plannotator)）是一个**交互式计划与代码审查工具**，专门为 AI 编码 Agent 设计。

**官方描述**：

> Interactive Plan & Code Review for AI Coding Agents. Mark up and refine your plans or code diffs using a visual UI, share for team collaboration, and seamlessly integrate with Claude Code, OpenCode, Pi, and Codex.

**翻译**：Plannotator 为 AI 编码 Agent 提供交互式计划与代码审查。使用可视化 UI 标记和完善计划或代码差异，与团队协作分享，并与 Claude Code、OpenCode、Pi 和 Codex 无缝集成。

### 2.2 核心价值主张

| 价值 | 说明 |
|------|------|
| **可视化审查** | 在浏览器中可视化地审核 Agent 的计划 |
| **内联标注** | 支持删除、插入、替换、评论等操作 |
| **一键反馈** | 批准或请求修改，反馈自动发送给 Agent |
| **代码审查** | 查看 Git diff 或远程 PR，并在代码行上评论 |
| **团队协作** | 分享计划给同事，收集反馈意见 |
| **隐私安全** | 端到端加密，服务器无法读取内容 |

### 2.3 核心数据

```
Stars:     3,700 (3.7k)
Forks:     233
Watchers:  15
贡献者:    54 人
提交数:   401 次
分支数:    112 个
标签数:    68 个
发布版本:  68 个
最新版本:  v0.16.2 (2026-03-31)
许可证:    MIT OR Apache-2.0 (双许可证)
```

### 2.4 支持的 AI 平台

| 平台 | 支持情况 |
|------|----------|
| **Claude Code** | ✅ 完整支持 |
| **Copilot CLI** | ✅ 完整支持 |
| **OpenCode** | ✅ 完整支持 |
| **Pi** | ✅ 完整支持 |
| **Codex** | ✅ 完整支持（无 Plan Mode）|

---

## §3 核心功能详解

### 3.1 Visual Plan Review（可视化计划审查）

**功能说明**

在 Agent 完成计划后，Plannotator 在浏览器中打开可视化 UI，允许你对计划进行内联标注。

**支持的操作**

| 操作 | 说明 |
|------|------|
| **Delete** | 删除计划中的某一行 |
| **Insert** | 插入新内容 |
| **Replace** | 替换现有内容 |
| **Comment** | 添加评论和意见 |

**工作流程**

```
Agent 完成计划
    ↓
Plannotator 打开浏览器 UI
    ↓
你标注（删除/插入/替换/评论）
    ↓
┌─────────────┬─────────────┐
│ Approve     │ Request Changes │
└─────────────┴─────────────┘
    ↓              ↓
执行实现     标注作为结构化反馈
              发送给 Agent
```

### 3.2 Plan Diff（计划差异对比）

**功能说明**

当 Agent 修订计划时，自动显示变更内容，让你看到修改了什么。

### 3.3 Code Review（代码审查）

**命令**：`/plannotator-review`

**功能**

- 查看 Git diff 或远程 PR
- 在代码行上添加评论
- 向 AI 询问关于代码的问题

```bash
# 审查当前变更
!plannotator review

# 审查 GitHub PR
!plannotator review <pr-url>

# 标注 Markdown 文件
!plannotator annotate file.md

# 标注 Agent 最后一条消息
!plannotator last
```

### 3.4 Annotate Any File（标注任意文件）

**命令**：`/plannotator-annotate`

**功能说明**

标注任意 Markdown 文件，并将反馈发送给 Agent。

### 3.5 Annotate Last Message（标注最后消息）

**命令**：`/plannotator-last`

**功能说明**

标注 Agent 的最后一条响应，发送结构化反馈。

---

## §4 工作原理

### 4.1 工作流程

**当 AI Agent 完成计划时，Plannotator 执行以下步骤：**

1. 在浏览器中打开 Plannotator UI
2. 让你可视化地标注计划（删除、插入、替换、评论）
3. 根据你的选择：
   - **批准（Approve）** → Agent 继续执行实现
   - **请求修改（Request Changes）** → 标注作为结构化反馈发送回 Agent

**代码审查流程类似，额外支持：**

- 在代码差异的具体行上评论

### 4.2 计划分享机制

**小型计划**

完全编码在 URL 哈希中：
- 无需服务器
- 不会存储在任何地方

**大型计划**

使用短链接服务，**端到端加密**：

| 特性 | 说明 |
|------|------|
| **加密方式** | AES-256-GCM |
| **加密时机** | 在你的浏览器中加密 |
| **服务器存储** | 仅存储密文（无法读取） |
| **解密密钥** | 仅存在于你分享的 URL 中 |
| **自动删除** | 7 天后自动删除 |

**安全特性**

- 零知识存储（类似 PrivateBin）
- 完全开源
- 支持自托管

---

## §5 安装与配置

### 5.1 Claude Code 安装

**安装 plannotator 命令**

**macOS / Linux / WSL：**

```bash
curl -fsSL https://plannotator.ai/install.sh | bash
```

**Windows PowerShell：**

```powershell
irm https://plannotator.ai/install.ps1 | iex
```

**在 Claude Code 中安装插件：**

```
/plugin marketplace add backnotprop/plannotator
/plugin install plannotator@plannotator

# 重要：安装插件后重启 Claude Code
```

### 5.2 Copilot CLI 安装

**安装 plannotator 命令**

同上（curl 或 irm 命令）。

**在 Copilot CLI 中安装插件：**

```
/plugin marketplace add backnotprop/plannotator
/plugin install plannotator-copilot@plannotator
```

重启 Copilot CLI。计划审查在你使用计划模式时自动激活（`Shift+Tab` 进入计划模式）。

### 5.3 OpenCode 安装

**添加到 opencode.json：**

```json
{
  "plugin": ["@plannotator/opencode@latest"]
}
```

**运行安装脚本：**

```bash
curl -fsSL https://plannotator.ai/install.sh | bash
```

**Windows：**

```powershell
irm https://plannotator.ai/install.ps1 | iex
```

重启 OpenCode。

### 5.4 Pi 安装

```bash
pi install npm:@plannotator/pi-extension
```

使用 `--plan` 参数启动 Pi 进入计划模式，或在会话中用 `/plannotator` 切换。

### 5.5 Codex 安装

**安装 plannotator 命令**

同上（curl 或 irm 命令）。

**在 Codex 中使用：**

```bash
!plannotator review           # 审查当前变更
!plannotator review <pr-url> # 审查 GitHub PR
!plannotator annotate file.md # 标注文件
!plannotator last            # 标注最后消息
```

**注意**：Codex 目前不支持 Plan Mode。

---

## §6 团队协作

### 6.1 协作流程

Plannotator 允许你与同事私下分享计划、标注和反馈：

1. 创建计划并标注
2. 生成分享链接
3. 同事查看并添加反馈
4. 你导入反馈并发送给编码 Agent

### 6.2 安全机制

| 计划类型 | 安全机制 |
|----------|----------|
| **小型计划** | 完全在 URL 中，无服务器存储 |
| **大型计划** | AES-256-GCM 端到端加密，服务器无法读取 |
| **自托管** | 支持完全自托管，完全控制数据 |

---

## §7 项目架构

### 7.1 Monorepo 结构

| 目录 | 说明 |
|------|------|
| `apps/hook/` | Claude Code Hook 应用 |
| `apps/copilot/` | Copilot CLI 插件 |
| `apps/opencode/` | OpenCode 插件 |
| `apps/pi-extension/` | Pi 扩展 |
| `apps/codex/` | Codex 集成 |
| `apps/marketing/` | 营销网站 |
| `packages/` | 共享包 |
| `tests/` | 测试 |
| `.agents/skills/` | Agent Skills |
| `.claude-plugin/` | Claude 插件配置 |

### 7.2 配置文件

| 文件 | 说明 |
|------|------|
| `package.json` | 主包配置 |
| `bunfig.toml` | Bun 配置 |
| `openpackage.yml` | 开源包配置 |
| `AGENTS.md` | Agent 说明文档 |

### 7.3 技术栈

| 语言 | 占比 |
|------|------|
| **TypeScript** | 85.7% |
| **CSS** | 4.5% |
| **Shell** | 4.2% |
| **Astro** | 3.1% |
| **HTML** | 1.6% |
| **PowerShell** | 0.5% |

---

## §8 常见问题

### Q1：Plannotator 和普通代码审查工具有什么区别？

| 特性 | Plannotator | 普通审查工具 |
|------|-------------|-------------|
| **目标用户** | AI Agent | 人类开发者 |
| **反馈目标** | 发送给 Agent | 发送给开发者 |
| **交互方式** | 可视化 UI + 结构化反馈 | 评论和讨论 |
| **Plan Mode** | ✅ 支持 | ❌ 不支持 |
| **Agent 集成** | ✅ Claude/Codex/OpenCode/Pi | ❌ 不支持 |

### Q2：我的计划是否安全？

**小型计划**：完全在 URL 中，无服务器存储，100% 私密。

**大型计划**：使用 AES-256-GCM 端到端加密。服务器仅存储密文，无法读取内容。解密密钥仅存在于你分享的 URL 中。

### Q3：支持自托管吗？

**支持**。你可以完全自托管 Plannotator，完全控制你的数据。详见官方文档。

### Q4：支持哪些 Git 平台？

| 平台 | 支持情况 |
|------|----------|
| **GitHub** | ✅ PR 审查 |
| **GitLab** | ✅ MR 审查 |
| **Gitea** | ✅ 支持 |

### Q5：如何为 Plannotator 贡献？

1. Fork 仓库
2. 查看 `CONTRIBUTING.md`
3. 提交 PR

### Q6：Codex 和 Claude Code 的区别？

| 特性 | Claude Code | Codex |
|------|-------------|-------|
| Plan Mode | ✅ 支持 | ❌ 不支持 |
| 插件系统 | ✅ 支持 | ✅ 支持 |
| Code Review | ✅ | ✅ |

---

## §9 总结

### 9.1 核心优势

| 优势 | 说明 |
|------|------|
| **可视化审查** | 浏览器中直观地审核 AI 计划 |
| **多 Agent 支持** | Claude Code / Copilot / OpenCode / Pi / Codex |
| **结构化反馈** | 标注作为结构化反馈发送给 Agent |
| **端到端加密** | AES-256-GCM，零知识存储 |
| **团队协作** | 分享计划，收集同事反馈 |
| **开源免费** | MIT/Apache-2.0 双许可证 |

### 9.2 适用场景

| 场景 | 推荐指数 |
|------|----------|
| AI Agent 开发监督 | ⭐⭐⭐⭐⭐ |
| 团队代码审查 | ⭐⭐⭐⭐⭐ |
| 计划审核批准 | ⭐⭐⭐⭐⭐ |
| 多人协作 | ⭐⭐⭐⭐ |

### 9.3 项目信息

- Stars：3.7k
- Forks：233
- 贡献者：54 人
- 最新版本：v0.16.2 (2026-03-31)
- 许可证：MIT OR Apache-2.0

### 9.4 相关资源

| 资源 | 链接 |
|------|------|
| 官方网站 | https://plannotator.ai |
| GitHub | https://github.com/backnotprop/plannotator |
| 文档 | https://plannotator.ai/docs |
| 安装脚本 | https://plannotator.ai/install.sh |

---

*文档版本 1.0 | 撰写日期：2026-03-31 | 基于 v0.16.2 (2026-03-31) | Stars: 3.7k ⭐*