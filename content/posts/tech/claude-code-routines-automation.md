---
title: "Claude Code Routines：让 AI Agent 实现无人值守自动化——定时触发、API 调用与 GitHub 事件驱动的云端自动化框架"
date: 2026-04-15T02:15:00+08:00
slug: "claude-code-routines-automation"
description: "Claude Code Routines 是官方推出的云端自动化框架，支持定时调度、API 调用、GitHub 事件触发三种方式，让 AI Agent 实现 24/7 无人值守运行。适用场景包括：Backlog 维护、告警分级、代码审查自动化、部署验证、文档漂移检测、SDK 跨语言同步。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "AI Agent", "自动化", "GitHub", "DevOps", "云端", "工作流"]
---

# Claude Code Routines：让 AI Agent 实现无人值守自动化——定时触发、API 调用与 GitHub 事件驱动的云端自动化框架

> **目标读者**：Claude Code 用户、DevOps 工程师、AI 自动化实践者、想要实现 AI 工作流自动化的开发者
> **预计阅读时间**：45-60 分钟
> **前置知识**：Claude Code 基础用法、Git/GitHub 基础、了解过 MCP 连接器
> **难度定位**：⭐⭐⭐⭐ 专家设计

---

## §1 学习目标

完成本篇文章后，你将能够：

1. **理解 Routines 的核心定位**：为何需要将 Claude Code 变成"无人值守"的自动化 Agent
2. **掌握三种触发器机制**：定时调度、API 调用、GitHub 事件
3. **理解云端执行架构**：Anthropic 托管的基础设施如何实现 24/7 运行
4. **能够设计自动化工作流**：根据真实场景设计合适的 Routine 方案
5. **掌握权限与安全边界**：Routine 的身份标识、访问范围、配额限制
6. **理解与本地开发的区别**：何时用 Routine，何时用本地 Claude Code

---

## §2 背景与动机：为何需要 Routines

### 2.1 Claude Code 的定位转变

Claude Code 最初是**交互式开发助手**——你坐在电脑前，它帮你写代码、调试、解释。你控制它何时开始、何时停止。

Routines 将 Claude Code 变成了**无人值守的自动化 Agent**——你定义规则，它在云端自动执行，无需你的电脑在线。

### 2.2 传统自动化的问题

| 传统方案 | 问题 |
|----------|------|
| Cron + 脚本 | 逻辑简单，难以处理复杂判断 |
| CI/CD 流水线 | 适合构建测试，不适合灵活任务 |
| 桌面 Agent | 依赖本地电脑，无法 24/7 运行 |
| **Routines** | **结合 LLM 智能 + 云端托管 + 事件驱动** |

### 2.3 Routines 的核心价值

```
你定义规则 ──▶ Claude 在云端自动执行 ──▶ 结果推送给团队

✅ 电脑关闭也能运行
✅ 支持 LLM 级别的复杂判断
✅ 事件驱动，实时响应
✅ GitHub 深度集成
```

---

## §3 核心概念：Routine 的构成

### 3.1 Routine = 配置包

一个 Routine 由三部分组成：

| 组件 | 说明 |
|------|------|
| **Prompt** | 你想让 Claude 执行什么任务 |
| **Repositories** | Claude 在哪些代码库工作 |
| **Connectors** | Claude 可以调用哪些外部服务（Slack、Linear 等）|

### 3.2 执行模型

Routines 运行在 **Anthropic 托管的云端基础设施**上：

- 每次运行创建一个新的 Cloud Session
- 无需 Permission Mode 选择器，运行过程无审批提示
- 可以执行 shell 命令、使用 skills、调用 connectors
- 访问范围由仓库权限、环境变量、连接器共同决定

### 3.3 身份与权限

**重要**：Routine 属于你的个人账户，不与团队共享。Routine 通过你的 GitHub 身份操作：

| 操作 | 身份标识 |
|------|----------|
| Git 提交 | 你的 GitHub 用户 |
| Pull Request | 你的 GitHub 用户 |
| Slack 消息 | 你关联的 Slack 账户 |
| Linear 工单 | 你关联的 Linear 账户 |

---

## §4 三种触发器详解

### 4.1 定时触发器（Schedule）

预设频率：

| 频率 | 说明 |
|------|------|
| **Hourly** | 每小时整点运行 |
| **Daily** | 每天某个时间点 |
| **Weekdays** | 每个工作日 |
| **Weekly** | 每周一次 |
| **Custom cron** | 自定义 cron 表达式 |

### 4.2 API 触发器

通过 HTTP POST 触发 Routine：

```bash
# 触发 Routine
curl -X POST https://api.claude.ai/routines/{routine-id}/trigger \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"text": "Alert: Error threshold exceeded in production"}'
```

触发时可以将数据作为 `text` 字段传递给 Routine。

### 4.3 GitHub 触发器

支持的事件：

| 事件 | 触发时机 |
|------|----------|
| `pull_request.opened` | 新 PR 打开 |
| `pull_request.closed` | PR 关闭（可筛选已合并）|
| `push` | 代码推送 |
| `issues.opened` | Issue 创建 |
| `workflow_run.completed` | CI/CD 工作流完成 |

可以过滤 PR，只处理特定条件下的事件。

---

## §5 实战场景：6 个典型自动化工作流

### 场景 1：Backlog 维护（定时触发）

**目标**：每个工作日晚间自动整理 Issue 队列

**配置**：
- 触发器：Weekdays 18:00
- 连接器：Linear + Slack
- Prompt：读取自上次运行以来的新 Issue，根据代码区域自动打标签、分配负责人，生成 Slack 摘要

**效果**：团队每天早上看到已整理好的 Issue 队列

### 场景 2：告警分级（API 触发）

**目标**：监控系统检测到错误阈值时自动生成修复方案

**配置**：
- 触发器：API（监控系统调用）
- 数据：告警内容、堆栈跟踪
- Prompt：根据堆栈跟踪关联到最近的提交，推荐修复方案，创建 Draft PR

**效果**：工程师从空白终端开始 → 直接 Review AI 生成的修复方案

### 场景 3：代码审查自动化（GitHub 触发）

**目标**：每个新 PR 自动执行团队审查清单

**配置**：
- 触发器：`pull_request.opened`
- Prompt：在 PR 上添加安全、性能、风格的 inline 评论，添加总结评论

**效果**：人工 Reviewer 专注于设计审查，机械性检查由 AI 完成

### 场景 4：部署验证（API 触发）

**目标**：CD 流水线完成后自动验证部署质量

**配置**：
- 触发器：API（CD 平台调用）
- Prompt：运行冒烟测试、扫描错误日志、检查回归，发布结果到发布频道

**效果**：部署窗口关闭前自动获得"通过/不通过"判断

### 场景 5：文档漂移检测（定时触发）

**目标**：每周检测文档是否与代码脱节

**配置**：
- 触发器：Weekly（周一 09:00）
- Prompt：扫描自上次运行以来合并的 PR，检查涉及 API 变更的文档，创建更新 PR

**效果**：文档始终与代码保持同步

### 场景 6：SDK 跨语言同步（GitHub 触发）

**目标**：一个 SDK 的变更自动同步到另一个语言版本

**配置**：
- 触发器：`pull_request.closed`（过滤已合并）
- Prompt：将变更 port 到平行 SDK，创建匹配的 PR

**效果**：多语言 SDK 保持同步，无需人工重复实现

---

## §6 创建 Routine：从 Web、CLI 到 Desktop

### 6.1 创建流程概览

```
1. 打开创建表单（Web / CLI / Desktop）
2. 命名 Routine + 编写 Prompt
3. 选择仓库（可多选）
4. 选择环境（环境变量）
5. 选择触发器（Schedule / API / GitHub）
6. 检查连接器（默认全部包含，可移除不需要的）
7. 点击创建
```

### 6.2 Web 创建

访问 claude.ai/code/routines，点击 **New routine**。

### 6.3 CLI 创建

在任意 Claude Code Session 中运行：

```bash
/schedule daily PR review at 9am
```

Claude 会对话式引导你完成配置。

### 6.4 Desktop App 创建

点击 **New task** → **New remote task**。

> ⚠️ 注意：选择 **New local task** 会创建本地 Desktop 定时任务，不是 Routine。

---

## §7 仓库与环境配置

### 7.1 仓库权限

- Routine 开始运行时从默认分支克隆仓库
- Claude 在 `claude/` 前缀的分支上创建更改
- 如需推送到任意分支，启用 **Allow unrestricted branch pushes**

### 7.2 云端环境

Environment 控制 Routine 的访问范围：

| 设置项 | 说明 |
|--------|------|
| **环境变量** | API Keys、Tokens、其他密钥 |

Routines 使用云端环境，与本地 Desktop 环境隔离。

---

## §8 连接器与 MCP

### 8.1 默认行为

所有已连接的 MCP Connectors 默认包含在 Routine 中。

### 8.2 权限最小化原则

移除 Routine 不需要的 Connectors，减少安全攻击面。

### 8.3 支持的 Connectors

Slack、Linear、Google Drive 等 —— 任何通过 MCP 连接的外部服务都可以使用。

---

## §9 配额与限制

### 9.1 可用计划

Routines 需要以下计划并启用 Claude Code on the Web：

| 计划 | 可用性 |
|------|--------|
| Pro | ✅ |
| Max | ✅ |
| Team | ✅ |
| Enterprise | ✅ |
| Free | ❌ |

### 9.2 使用配额

Routine 运行计入账户的每日运行配额。

---

## §10 Routine vs 本地 Claude Code：何时用哪个

| 场景 | 推荐 |
|------|------|
| 复杂调试、需要即时反馈 | 本地 Claude Code |
| 定期整理任务、自动化 | Routine |
| 事件驱动（PR 打开时）| Routine |
| 需要交互式探索 | 本地 Claude Code |
| 24/7 无人值守 | Routine |
| 一次性任务 | 本地 Claude Code |

---

## §11 常见问题（FAQ）

### Q1：Routine 和本地 Desktop Scheduled Task 有什么区别？

A：Routine 运行在云端，无需电脑在线。Desktop Scheduled Task 运行在本地机器。

### Q2：Routine 的代码变更推送到哪里？

A：Claude 在 `claude/` 前缀的分支上创建更改，你需要手动合并或开启 Unrestricted branch pushes。

### Q3：Routine 可以访问哪些数据？

A：取决于你选择的仓库、环境变量中的密钥、以及包含的 Connectors。

### Q4：Routine 失败时会发生什么？

A：Routine 会在你的 Session 列表中显示失败状态，你可以查看日志排查问题。

### Q5：Routine 可以并行运行吗？

A：可以，每个 Trigger 都会创建一个新的独立 Session。

---

## §12 相关资源

| 资源 | 链接 |
|------|------|
| **官方文档** | [code.claude.com/docs/en/routines](https://code.claude.com/docs/en/routines) |
| **Routine 管理** | [claude.ai/code/routines](https://claude.ai/code/routines) |
| **Claude Code 概述** | [code.claude.com/docs/en/overview](https://code.claude.com/docs/en/overview) |
| **MCP 连接器** | [code.claude.com/docs/en/mcp](https://code.claude.com/docs/en/mcp) |
| **云端环境** | [code.claude.com/docs/en/claude-code-on-the-web](https://code.claude.com/docs/en/claude-code-on-the-web) |

---

**文档信息**
难度：⭐⭐⭐⭐ | 类型：专家设计 | 更新日期：2026-04-15 | 预计阅读时间：45-60 分钟
