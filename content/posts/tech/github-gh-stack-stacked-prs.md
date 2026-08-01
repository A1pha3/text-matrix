---
title: "gh-stack：GitHub 官方推出的 Stacked PRs CLI 扩展"
date: 2026-08-02T02:59:48+08:00
slug: "github-gh-stack-stacked-prs"
description: "github/gh-stack 是 GitHub 官方出品的 gh CLI 扩展，把\"把大改动拆成一串互相依赖的小 PR\"这件事自动化：建栈、重定 base、批量 push、跨层导航都被一条 CLI 接管，并配套 gh-stack skill 让 AI 代理理解这套工作流。"
draft: false
categories: ["技术笔记"]
tags: ["GitHub", "Stacked PRs", "gh CLI", "代码评审", "Agent Skills"]
---

## 一句话判断

`github/gh-stack` 是 GitHub 官方对"Stacked PRs"工作流的工程化回答：用一个 `gh` 子命令把"建分支栈 → 改 base → 批量 push → 在层之间切换"全部接管，并配套发布 `gh-stack` 技能让 Claude Code/Cursor 等代理理解这套模式——避免"代理一次提一个超大 PR"的反模式。

## 为什么需要 Stacked PRs

普通 PR 工作流鼓励"一个 PR 做一件事"，但工程现实里很多改动天然有先后顺序：底层 API 改造 → 上层适配 → UI 适配。一次提一个巨型 PR 让 reviewer 失去耐心；拆成 5 个独立 PR 又因为依赖关系必须按顺序合并。

Stacked PRs 的解法是承认"PR 之间有依赖"，并提供工具链让这种依赖**可视化、可操作**：

- 每个 PR 单独 review、单独合并
- 底层 PR 合并后，上层 PR 自动重定 base
- 跨层切换 = 在分支栈里 `git checkout` 任意一层

## 命令一览

```bash
# 初始化（创建并切到第一个分支）
gh stack init

# 加新分支到栈顶
gh stack add api-endpoints

# 批量推送所有分支 + 对应 PR
gh stack push

# 查看栈
gh stack view
```

更完整的子命令覆盖创建、改 base、跨层导航、批量同步、与 GitHub 平台 PR base 字段联动。

## 安装与前置

```bash
gh extension install github/gh-stack
```

要求 GitHub CLI `v2.0+`。

## 让 AI 代理也懂 Stacked PRs

仓库专门给代理准备了一份配套技能：

```bash
gh skill install github/gh-stack
```

装上后，Claude Code/Cursor/Aider 等代理在判断"这是一个适合拆 stacked PR 的改动"时会自动调用技能描述，按层拆分提交，并正确设置每个 PR 的 `base` 分支。

这件事看着小，意义很大：

- **没有技能**：代理一次提一个 800 行的 PR，reviewer 看到直接 reject
- **有技能**：代理按"底层 API → 上层 adapter → UI"切成 3 个 PR，每个 PR 都在 200 行内

## 一次真实使用流

把"重构 OAuth2 授权层 + 接入新 UI"当样本：

1. `gh stack init`，仓库默认分支上创建 `oauth-rewrite/db` 分支
2. 在 `oauth-rewrite/db` 上提交数据库 schema 改动、push、`gh stack push`
3. `gh stack add oauth-rewrite/service`，在 db 上叠加 service 层重构
4. `gh stack add oauth-rewrite/ui`，最后叠加 UI 接入
5. `gh stack view` 看到 3 个 PR 的依赖关系清晰列在栈里
6. Reviewer 逐个 review；底层合并后 `gh stack push` 自动把上两层重定 base
7. 全栈合完 → 主分支获得完整 OAuth2 重构

如果用普通工作流，3 个 PR 的 base 关系必须人工维护，合并顺序错了整条链断掉。

## 适用边界与不适用边界

**适用**：

- 大型 feature flag 下线、API 重构、数据库迁移等需要"分阶段合并"的改动
- 团队规模在 3+ 工程师，必须多人评审同一改动
- 已经在用 GitHub PR（其他平台如 GitLab 的等价工具叫 `glab stack`，但本仓库仅覆盖 GitHub）

**不适用**：

- 单人小仓库，PR 永远 < 100 行（拆栈的成本大于收益）
- 强依赖 CI 单跑一个 PR 才能验证的流水线（拆栈后 CI 必须支持 base 链）
- 团队没有 review 文化：栈工具不能让无 review 的 PR 变得可读

## 与 Gerrit / Phabricator 的差异

栈型 PR 工具不是新概念——Gerrit 在 2010 年前后就提供了等价能力。但 Gerrit 的强约束（每个 commit 必须过 CI 才能被合并）在 GitHub PR 生态里很难实现。`gh-stack` 的折中是：

- **GitHub PR 是主舞台**，review 流程不需要切换系统
- **栈管理是辅助层**，只在分支层面做优化，不动 PR 状态机
- **代理技能配套**是它和 Gerrit 最大的差异点：把"如何拆栈"这件事教给 AI 代理

这个折中决定了它在 GitHub 生态里的可接受度——任何想迁移到 Gerrit 的团队都可以先用 `gh-stack` 试水。