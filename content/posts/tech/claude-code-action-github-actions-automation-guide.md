---
title: "Claude Code Action：把 Claude 变成 GitHub 仓库的自动化协作者"
date: 2026-10-01T03:20:00+08:00
slug: "claude-code-action-github-actions-automation-guide"
github_repo: "anthropics/claude-code-action"
source_key: "gh:anthropics/claude-code-action"
description: "Claude Code Action 是 Anthropic 官方的 GitHub Action，把 Claude Code 接入 PR 与 Issue 工作流：自动代码审查、问题回复、简单修复与新功能实现。本文讲解工作原理、最小配置、触发方式、权限边界与典型自动化场景。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "GitHub Actions", "CI/CD", "AI 编程", "代码审查"]
---

# Claude Code Action：把 Claude 变成 GitHub 仓库的自动化协作者

Claude Code 在终端里很强大，但它默认只在开发者主动召唤时工作。Claude Code Action 要解决的问题是：**当 PR 合入、Issue 被指派、有人在评论区 @ 机器人时，让 Claude 自动出现在 GitHub 工作流里**——审代码、回答问题、甚至直接改代码提交 PR。

这个项目是 Anthropic 官方维护的 GitHub Action（TypeScript 实现，MIT 许可，约 9.3k stars），底层复用 Claude Code 与 Agent SDK。它不是把终端工具搬上网页，而是把"AI 编程助手"变成"仓库的常驻协作者"。本文基于仓库 README、官方文档与 v1.0 配置说明，讲清楚它能做什么、怎么接入、边界在哪。

## 一、它解决什么问题

终端里的 Claude Code 是"人驱动"的：你敲命令，它执行。仓库协作场景则反过来——事件驱动：`issue_comment` 创建了、PR 更新了、Issue 被指派了，AI 应该自己判断要不要介入。

Claude Code Action 的核心机制是**智能模式检测**：不需要配置"这个事件走 review 模式、那个事件走 implement 模式"，Action 根据工作流上下文自动选择执行模式。比如在 PR 上被 @ 就做代码审查，在 Issue 里被指派就去实现需求，在自动化任务里给了 `prompt` 就按指令执行。

## 二、最小接入

最省事的安装方式不是手写 workflow，而是在终端里打开 Claude Code 执行：

```bash
claude
# 然后运行
/install-github-app
```

该命令会引导你完成 GitHub App 安装与 secrets 配置（需要仓库管理员权限）。这种方式只覆盖 Anthropic 直连 API 用户；用 Bedrock、Vertex AI、Foundry 的团队走 `docs/cloud-providers.md` 的云厂商路径。

手写 workflow 同样简单。新建 `.github/workflows/claude.yml`：

```yaml
name: Claude Assistant
on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  issues:
    types: [opened, assigned, labeled]
  pull_request_review:
    types: [submitted]

jobs:
  claude-response:
    runs-on: ubuntu-latest
    steps:
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

这一段就够让 Claude 在评论触发时（默认触发词 `@claude`）回答问题、审查代码。几个关键输入：

| 输入 | 作用 |
|------|------|
| `anthropic_api_key` | Anthropic 直连 API 密钥（或换 OAuth token / 工作负载身份联邦） |
| `prompt` | 自动化任务的指令模板，可用 `${{ github.event.* }}` 注入上下文 |
| `claude_args` | 透传给 Claude CLI 的参数，如 `--max-turns 10 --model claude-4-0-sonnet-20250805` |
| `trigger_phrase` | 评论触发词，默认 `@claude` |
| `track_progress` | 用置顶评论显示任务进度勾选清单 |
| `use_bedrock` / `use_vertex` | 切换云厂商认证（OIDC，无需静态密钥） |

## 三、三种工作模式

v1.0 废弃了旧的 `mode` 参数，改为自动检测：

1. **交互式问答**：PR 或 Issue 评论里 @ Claude，它回答代码、架构、编程相关问题。
2. **代码审查**：分析 PR 变更，给出改进建议，支持内联评论（inline comment），还能生成"Fix this"链接让开发者一键把问题带回终端修复。
3. **代码实现**：在 Issue 场景下自动创建分支干活，在 PR 场景下直接往现有分支推提交，完成后回链一个预填好的 PR 创建页。

分支处理有明确规则：从 Issue 触发永远新建分支；从打开的 PR 触发直接推送到该 PR 分支；从已关闭的 PR 触发则新建分支（原分支已不可用）。

## 四、典型自动化场景

仓库官方 Solutions Guide 提供了 8 类可直接套用的模式，最实用的几个：

**自动 PR 审查**——PR 打开或更新时触发，Claude 分析代码质量、潜在 bug、安全隐患与性能问题，用 `gh pr comment` 输出总评，用 `mcp__github_inline_comment__create_inline_comment` 标注具体代码行：

```yaml
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      id-token: write
    steps:
      - uses: actions/checkout@v6
        with: { fetch-depth: 1 }
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            REPO: ${{ github.repository }}
            PR NUMBER: ${{ github.event.pull_request.number }}
            请审查此 PR：代码质量、潜在 bug、安全隐患、性能。
            用 gh pr comment 输出总评，用 inline comment 标注具体问题。
          claude_args: |
            --allowedTools "mcp__github_inline_comment__create_inline_comment,Bash(gh pr comment:*),Bash(gh pr diff:*),Bash(gh pr view:*)"
```

**Issue 自动分类打标**——新 Issue 打开时按内容自动打 label、指派负责人，省掉人工 triage。

**定时仓库巡检**——用 `schedule` 触发，让 Claude 定期检查依赖、README 与 CI 健康度，把发现写成 Issue。

**文档同步**——API 变更后自动更新对应文档段落。

值得注意的细节：`classify_inline_comments`（默认 `true`）会把不带 `confirmed: true` 的内联评论先缓存，用 Haiku 分类过滤掉测试性评论，避免子代理的试探性评论刷屏 PR。

## 五、安全边界：它不能做什么

官方 Capabilities & Limitations 文档明确列出了能力上限，这些限制本身就是安全设计：

- **不能提交正式的 PR Review**（GitHub 的 review 对象），只能发评论
- **不能批准 PR**——这是刻意的安全约束
- **只能更新自己的初始评论**，不能到处发多条评论
- **默认不能执行任意 Bash 命令**，必须用 `claude_args` 显式放行（如上面例子里的 `--allowedTools`）
- **不能做 merge、rebase 等 git 写操作**，只能推送提交
- **作用域被限制在触发它的仓库与 PR/Issue 上下文内**

权限控制是重点：`allowed_bots` 控制哪些 bot 账号能触发（默认全部禁止，公开仓库若设 `'*'` 外部 App 可能借机调用）；`allowed_non_write_users` 被官方标注 RISKY，仅配合自定义 `github_token` 使用。

## 六、认证方式与适用判断

认证按团队基础设施选：Anthropic 直连 API 用密钥或 **workload identity federation**（GitHub OIDC token 换 Anthropic token，免静态密钥，推荐）；AWS 团队用 Bedrock + OIDC；Google 团队用 Vertex AI + OIDC；微软生态用 Foundry。

**适合接入的场景**：团队 PR 审查流程明确、Issue triage 人力成本高、希望把"改个小问题"这类机械任务交给 AI 的仓库。

**暂不适合的场景**：对审查结论有强合规要求的项目（AI 不产生正式 review 对象）；需要 AI 操作多仓库或复杂 git 流程的编排；以及——它仍在 beta，`docs/faq.md` 明说 API 可能变动，生产环境要盯 release 节奏（当前约每日发布 v1.0.x 版本）。

## 七、快速决策表

| 问题 | 答案 |
|------|------|
| 用什么触发 | 评论 @ 机器人 / Issue 指派 / label / 定时 / 自动化 prompt |
| 最小改动接入 | `claude` 里跑 `/install-github-app`，或贴一段 20 行 workflow |
| 审查结论以什么形式落 | 评论 + 内联标注，不是正式 review |
| 密钥怎么管 | 直连 API 密钥，或 OIDC 联邦免静态密钥 |
| 官方定位 | 通用型 Action，beta 阶段，文档齐全 |

一句话判断：如果你的仓库已经接受"AI 辅助代码审查"这个工作方式，Claude Code Action 是当前把 Claude Code 接进 GitHub 协作流的最短路径——官方维护、事件驱动、权限边界清楚。如果团队连人工 review 流程都还没跑顺，先别急着上 AI 审查，它放大的是已有流程，而不是替代流程。
