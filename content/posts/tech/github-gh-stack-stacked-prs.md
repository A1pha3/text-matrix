---
title: "gh-stack：GitHub 官方推出的 Stacked PRs CLI 扩展"
date: 2026-08-02T02:59:48+08:00
slug: "github-gh-stack-stacked-prs"
github_repo: "github/gh-stack"
description: "github/gh-stack 是 GitHub 官方推出的 Stacked PRs CLI 扩展：一条 gh 子命令接管建栈、级联 rebase、批量 push、创建 PR 与层间导航，并配套 gh-stack 技能让 AI 代理学会按层拆分改动。"
draft: false
categories: ["技术笔记"]
tags: ["GitHub", "Stacked PRs", "gh CLI", "代码评审", "Agent Skills"]
keywords: ["gh-stack", "Stacked PRs", "堆叠式 PR", "级联 rebase", "GitHub CLI"]
toc: true
---

# gh-stack：GitHub 官方 Stacked PRs CLI 扩展

## 一句话判断

`github/gh-stack` 是 GitHub 官方对 Stacked PRs 工作流的工程化实现：一条 `gh` 子命令接管建栈、级联 rebase、批量推送、创建 PR 和层间导航，并配套 `gh-stack` 技能，让 AI 代理也学会"把大改动拆成一串小 PR"。

## 为什么需要 Stacked PRs

普通 PR 工作流默认"一个 PR 做一件事"，但工程现实里很多改动天然有先后顺序：先改底层 API，再改上层适配，最后改 UI。一次提一个巨型 PR，reviewer 很容易失去上下文，反馈质量下降；拆成几个互相依赖的独立 PR，又必须手工维护 base 分支关系，合并顺序一错整条链就断了。

Stacked PRs 承认"PR 之间有依赖"，并把这种依赖变成平台能力：每个 PR 单独 review、单独合并，底层合并后上层自动重定 base，跨层切换只是一个 `git checkout`。

## 栈的结构

一个栈是同一仓库里的一串 PR，每个 PR 的目标分支是它下方那个 PR 的分支，最终落在主干分支上：

```
frontend → PR #3 (base: api-endpoints) ← top
api-endpoints → PR #2 (base: auth-layer)
auth-layer → PR #1 (base: main) ← bottom
─────────────
main (trunk)
```

- **trunk（主干）**：栈底 PR 的目标分支，默认是仓库默认分支（main），也可以是 release 分支或长期特性分支。
- **bottom**：最靠近 trunk 的一层。
- **top**：离 trunk 最远的一层。

## 安装与前置

```bash
gh extension install github/gh-stack
```

要求：

- GitHub CLI `v2.0+`，且已通过 `gh auth login` 认证
- Git `2.20+`
- Stacked PRs 目前处于预览阶段，仓库需启用该功能后才能使用

可选：运行 `gh stack alias` 把 `gh stack` 简写为 `gs`。

## 命令总览

| 命令 | 作用 |
|------|------|
| `gh stack init` | 在当前仓库初始化一个栈 |
| `gh stack add <branch>` | 在当前栈顶新增一个分支 |
| `gh stack view` | 查看当前栈的状态 |
| `gh stack checkout` | 按栈号 / PR 号 / URL / 分支名切换分支 |
| `gh stack modify` | 交互式重组当前栈 |
| `gh stack unstack` | 从本地跟踪移除该栈，并在 GitHub 上取消栈链接 |
| `gh stack submit` | 推送全部分支并创建 / 更新 PR 与栈 |
| `gh stack sync` | 一条命令完成拉取、rebase、推送、同步 PR 状态 |
| `gh stack rebase` | 从远端拉取并执行级联 rebase |
| `gh stack push` | 推送当前栈中活跃的分支 |
| `gh stack link` | 不经本地跟踪，把现有 PR 链接进一个栈 |
| `gh stack merge` | 一次合并一个或多个栈内 PR |
| `gh stack switch` | 交互式切换到栈中另一个分支 |
| `gh stack up / down / top / bottom` | 在栈内上移 / 下移 / 跳到顶 / 跳到底 |

## 快速上手

```bash
cd my-project

gh stack init            # 提示命名第一个分支，开始跟踪
# ... 写代码、commit ...

gh stack add api-routes  # 在栈顶加一层新分支
# ... 写代码、commit ...

gh stack push            # 推送所有分支到远端
gh stack submit          # 为每层创建 PR，并链接成栈
gh stack view            # 查看每层的 PR、状态与最新提交
```

`submit` 会自动设置每个 PR 的 base：第一个分支指向 main，`api-routes` 指向第一个分支。reviewer 在 GitHub 上看到的是单层 diff，而不是整个改动。

## 级联 rebase：栈的骨架

栈最麻烦的不是建分支，而是底层变更后上层的 base 维护。`gh stack rebase` 从 trunk 开始逐层向上 rebase；遇到某层 PR 已合并时，会自动切换为 `--onto` 模式，不把已合并的 commit 重复带入上层。

手工维护这套 base 链不可持续：3 个 PR 就要维护 2 条 base 关系，任何一层合入或 trunk 前移都会牵动上面所有层。工具的优势在于它知道栈的结构，而 Git 本身不知道。

栈的跟踪元数据保存在本地（local tracking），不写进仓库历史，因此不会污染提交记录。

## 合并：整栈落，或落一部分

在 GitHub 上点**栈顶 PR 的 Merge**，它和下方所有未合并的 PR 会从下往上一起合入（一次原子操作）；点**栈中某个较低层的 PR**，则只合并它以下的层，上方的 PR 保持打开，并自动 rebase 到新的 base。

三种合并方式都支持：

- **Merge commit**：为整组 PR 生成一个合并提交，保留每层完整历史
- **Squash**：每层压成一个干净的提交，合并 n 个 PR 产生 n 个提交
- **Rebase**：把每层提交重放到 base 分支上，形成无合并提交的线性历史

Merge queue 同样支持：栈内 PR 按正确顺序整体入队；某一层被移出队列，其上各层也会一并移出。线性历史是合并的硬性要求——任何一层 base 前移都会破坏它，需要 `gh stack rebase` 恢复。

## 分支保护与 CI：按栈底执行

栈中每个 PR 的规则都不是按它的直接 base 评估，而是按**栈的 base（通常就是 main）**评估：required reviews、status checks、CODEOWNERS、代码扫描都遵循这一规则。也就是说，栈中间的 PR 与最底层 PR 执行同一套标准，不会因为"中间层 base 是另一个 PR 分支"而绕过保护。

GitHub Actions 同理：配置为 `pull_request` 且针对 main 的工作流，会对栈中**每一个** PR 触发，无需为栈改 workflow。栈的元数据（如 base 分支）可通过 `github.event.pull_request.stack` 在 workflow 表达式中读取。

## AI 代理集成

```bash
gh skill install github/gh-stack
```

装上后，AI 编码代理在判断"这是一次适合拆栈的改动"时会调用技能描述，按层拆分提交，并给每个 PR 设置正确的 base。没有技能时，代理倾向一次提一个 800 行的大 PR；有技能后，它会按"底层 API → 上层适配 → UI"切成几个 200 行内的小 PR。

这个技能随仓库持续维护：v0.1.1 把 `SKILL.md` 从约 891 行精简到约 183 行，token 占用下降约 81%，同时通过了两类模型的全部测试工作流。

## 与其他工具的差异

栈式评审不是新概念——Google 内部的 Critique、Gerrit、以及第三方的 Graphite、ghstack、git-spice 都实现了类似能力。gh-stack 的差异在"平台原生"：

| 维度 | gh-stack | 第三方工具（Graphite 等） |
|------|----------|--------------------------|
| 安装 | `gh extension install` 一行 | 需单独注册账号或部署服务 |
| GitHub 集成 | 原生：stack map、规则按栈底执行 | 依赖第三方界面或浏览器插件 |
| AI 集成 | `gh skill install` 开箱即用 | 各家自行对接 |
| 适用范围 | 仅 GitHub | 部分工具支持多平台 |

代价也很明确：gh-stack 只服务 GitHub，第三方工具在 CLI 打磨和跨平台上是更成熟的选择。

## 适用与不适用

**适用**：

- 大型改动天然分阶段：API 重构、数据库迁移、feature flag 下线
- 团队 3 人以上、多人评审同一改动，reviewer 需要小 diff
- 已经在 GitHub 工作流内，不想引入第二套系统

**不适用**：

- 单人小仓库，PR 长期小于 100 行（拆栈的成本大于收益）
- CI 必须在单一 PR 上全量验证的流水线（栈内每层都会触发 CI）
- 没有评审文化的团队（工具自动化了繁琐部分，但改变不了评审质量）
- 需要跨 fork 协作的仓库（栈要求所有分支在同一仓库）

## 局限

- 预览期功能，命令与行为可能变化
- 栈内所有分支必须在同一仓库，不支持跨 fork
- 不支持 GitHub Desktop
- `gh stack modify` 这类重组命令对工作区状态要求较高（干净工作树、无进行中的 rebase、线性历史），现实里常不满足
- 部分合并后剩余层会自动 rebase，CI 需要重新跑

## 参考

- 官方站点：[github.github.com/gh-stack](https://github.github.com/gh-stack/)
- 仓库：[github.com/github/gh-stack](https://github.com/github/gh-stack/)
- CLI 命令参考：[docs.github.com · Stacked PRs CLI commands](https://docs.github.com/en/pull-requests/reference/stacked-prs-cli-commands)
- Stacked PRs 规则：[docs.github.com · Stacked pull requests](https://docs.github.com/en/pull-requests/reference/stacked-pull-requests)
