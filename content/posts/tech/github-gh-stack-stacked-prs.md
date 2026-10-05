---
title: "gh-stack：GitHub 官方把 Stacked PRs 做成了平台能力"
date: 2026-08-02T02:59:48+08:00
slug: "github-gh-stack-stacked-prs"
github_repo: "github/gh-stack"
source_key: "gh:github/gh-stack"
description: "github/gh-stack 是 GitHub 官方推出的 Stacked PRs CLI 扩展：一条 gh 子命令接管建栈、级联 rebase、批量 push、创建 PR 与层间导航，并配套 gh-stack 技能让 AI 代理学会按层拆分改动。"
draft: false
categories: ["技术笔记"]
tags: ["GitHub", "Stacked PRs", "gh CLI", "代码评审", "Agent Skills"]
keywords: ["gh-stack", "Stacked PRs", "堆叠式 PR", "级联 rebase", "GitHub CLI"]
toc: true
---

# gh-stack：GitHub 官方 Stacked PRs CLI 扩展

## 一句话判断

`github/gh-stack` 是 GitHub 官方对 Stacked PRs 工作流的工程化实现：一条 `gh` 子命令接管建栈、级联 rebase、批量推送、创建 PR 和层间导航，并配套 `gh-stack` 技能，让 AI 代理也学会"把大改动拆成一串小 PR"。它不是又一款第三方栈式评审工具，而是 GitHub 把这套工作流收进平台的第一步——栈在 GitHub 上是一等公民，分支保护和 merge queue 都认识它。

## 先分清：平台能力、CLI 扩展、agent 技能

gh-stack 这个名字下面其实是三样东西，解决的问题不同：

| 组成 | 形态 | 解决什么 |
|------|------|----------|
| Stacked PRs 平台能力 | GitHub 网页与 API，公开预览 | 栈作为一等公民：栈视图、按栈底评估规则、整体合并、merge queue 适配 |
| `gh stack` CLI 扩展 | Go 写的 gh 扩展，MIT 协议 | 本地工作流：建分支、级联 rebase、批量推送、层间导航 |
| `gh-stack` agent 技能 | `gh skill install` 安装的 SKILL.md | 教 AI 编码代理按层拆分改动、设置正确 base |

三者可以独立使用：不用 CLI 也能在网页上建栈管栈，GitHub 文档明确说这背后"底层的 Git 操作是标准的"（The underlying Git operations are standard）；反过来，用 jj 或 Sapling 管理本地分支的团队，可以只拿 `gh stack link` 把现成 PR 链接成栈，不需要 CLI 接管本地分支。CLI 扩展于 2026 年 2 月建仓，4 月发 v0.0.1，9 月初到 v0.1.1，处于活跃开发期。

## 为什么需要 Stacked PRs

普通 PR 工作流默认"一个 PR 做一件事"，但工程现实里很多改动天然有先后顺序：先改底层 API，再改上层适配，最后改 UI。一次提一个巨型 PR，reviewer 很容易失去上下文，反馈质量下降；拆成几个互相依赖的独立 PR，又必须手工维护 base 分支关系，合并顺序一错整条链就断了。

Stacked PRs 承认"PR 之间有依赖"，并把这种依赖变成平台能力：每个 PR 单独 review、单独合并，底层合并后上层自动重定 base，跨层切换只是一个 `git checkout`。

## 栈的结构

一个栈是同一仓库里的一串 PR，每个 PR 的目标分支是它下方那个 PR 的分支，最终落在主干分支上：

```
frontend      → PR #3 (base: api-endpoints) ← top
api-endpoints → PR #2 (base: auth-layer)
auth-layer    → PR #1 (base: main)          ← bottom
─────────────
main (trunk)
```

- **trunk（主干）**：栈底 PR 的目标分支，默认是仓库默认分支（main），也可以是 release 分支或长期特性分支。
- **bottom**：最靠近 trunk 的一层。
- **top**：离 trunk 最远的一层。

每个分支从它下面那层继承而来，导航命令就按这个模型工作：`up` 是远离 trunk，`down` 是朝向 trunk。

## 安装与前置

```bash
gh extension install github/gh-stack
```

要求：

- GitHub CLI `v2.0+`，且已通过 `gh auth login` 认证
- Stacked PRs 处于公开预览阶段，行为可能变化；仓库未开放该功能时命令会失败（CLI 退出码 9 就是"Stacked pull requests are not enabled for this repository"），管理员可按官方的 Roll out 教程分批开放给组织

升级用 `gh extension upgrade stack`。

## 命令总览

CLI 共 20 个子命令：

| 命令 | 作用 |
|------|------|
| `gh stack init` | 在当前仓库初始化一个栈，自动启用 `git rerere` 记住冲突解法 |
| `gh stack add <branch>` | 在当前栈顶新增一个分支；带 `-Am` 可顺带暂存并提交 |
| `gh stack view` | 查看当前栈的状态，支持 `--short` 与 `--json` |
| `gh stack checkout` | 按栈号 / PR 号 / URL / 分支名切换分支 |
| `gh stack modify` | 交互式 TUI 重组当前栈：删层、折叠、插入、重命名、排序 |
| `gh stack unstack` | 从本地跟踪移除该栈，并在 GitHub 上取消栈链接（别名 `delete`） |
| `gh stack submit` | 推送全部分支并创建 / 更新 PR 与栈 |
| `gh stack sync` | 一条命令完成拉取、级联 rebase、推送、同步 PR 与栈状态 |
| `gh stack rebase` | 从远端拉取并执行级联 rebase |
| `gh stack push` | 推送当前栈中活跃的分支 |
| `gh stack link` | 不经本地跟踪，把现有分支或 PR 链接进一个栈 |
| `gh stack merge` | 一次合并一个或多个栈内 PR |
| `gh stack switch` | 交互式切换到栈中另一个分支 |
| `gh stack up / down / top / bottom / trunk` | 在栈内上移 / 下移 / 跳到顶 / 跳到底 / 跳回主干 |
| `gh stack alias` | 生成命令别名（默认 `gs`） |
| `gh stack feedback` | 打开仓库 Discussion 提反馈 |

命令有统一的退出码约定：3 是 rebase 冲突、6 是分支属于多个栈需要消歧、8 是栈被其他进程锁定、10 是 modify 会话中断需要恢复。写脚本时可以按退出码分支处理。

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

`submit` 在交互终端里是一个全屏编辑器：左栏列出所有还没有 PR 的分支，按 `Ctrl+X` 勾选；右栏逐层草拟标题和描述，带 Markdown 预览，也可以唤起 `$EDITOR`。不进编辑器就加 `--auto`，用自动生成的标题创建。选分支时注意联动：去掉中间一层，它上面的层会一起被去掉——毕竟上层 PR 的 base 挂在被去掉的分支上。

还有一条更省键位的路：`gh stack add -Am "Auth middleware"`。一条命令完成暂存、提交、建分支，分支名从提交信息自动生成（形如 `03-24-auth_middleware`）。刚 `init` 完、当前分支还没有提交时，这个命令会把提交直接落在当前分支上，而不是再开一层。

## 一次评审意见如何流过整条栈

把上面所有命令放进一次真实评审，工作流是这样的：reviewer 在第一层 PR 上点了 request changes。你 `gh stack bottom` 跳回栈底修问题，提交后 `gh stack rebase` 把上面的层依次重放上去，`gh stack push` 推送各层，等第一层最终被合并，跑一次 `gh stack sync`——它会把主干快进到最新、清掉已合并的分支（交互终端会提示，`--prune` 可以免提示自动清理），栈里剩下的层继续等待评审。

整个过程里你不需要手工改任何 PR 的 base 分支：底层合并后，GitHub 会把上层 PR 的目标自动重定向到栈的 base；本地侧，`gh stack rebase` 遇到某层 PR 已合并时也会自动切换为 `--onto` 模式，不把已合并的 commit 重复带入上层。

## 级联 rebase：栈的骨架

栈最麻烦的不是建分支，而是底层变更后上层的 base 维护。`gh stack rebase` 从 trunk 开始逐层向上 rebase，支持 `--downstack` / `--upstack` 只处理当前层的下半段或上半段，`--no-trunk` 跳过主干。遇到冲突时操作会暂停并列出冲突文件和行号，解决后 `--continue` 继续，`--abort` 整体回退到 rebase 前的状态。

手工维护这套 base 链不可持续：3 个 PR 就要维护 2 条 base 关系，任何一层合入或 trunk 前移都会牵动上面所有层。工具的优势在于它知道栈的结构，而 Git 本身不知道。网页端也补了同一块拼图：merge box 里有 **Rebase stack** 按钮，点一下由服务端做级联 rebase，不装扩展的协作者同样能修栈。

栈的跟踪元数据是 `.git/gh-stack` 下的一个 JSON 文件，记录哪些分支属于哪个栈、顺序如何；中断的 rebase 状态单独放在 `.git/gh-stack-rebase-state`。两者都在 `.git` 目录里，不会提交，也就不会污染仓库历史。

## 合并：整栈落，或落一部分

合并粒度可以选：整个栈、单个 PR、或者横跨连续几层的部分栈，方向必须自底向上。合并栈顶等于整栈落库，逐层合并与一次性合并产生的提交历史相同。CLI 的 `gh stack merge` 更进一步：从所选层到栈底作为一次 all-or-nothing 操作合入，任何一层合不进去，整批都不动。

三种合并方式都支持：

- **Merge commit**：为整组 PR 生成一个合并提交，保留每层完整历史
- **Squash**：每层压成一个干净的提交，合并 n 个 PR 产生 n 个提交
- **Rebase**：把每层提交重放到 base 分支上，形成无合并提交的线性历史

如果合并点在栈的中间，它下面的层随之一起合并，上面的 PR 保持打开，目标分支自动重定向到栈的 base。

Merge queue 同样适配：栈内 PR 按正确顺序整体入队，一个 PR 被移出队列，它上面的层也会一并移出。为了让整条栈待在同一组里，merge queue 允许合并组超过配置上限最多 50%；栈太大塞不进一组时，会自动拆到连续的几个合并组。注意一点：队列模式下合并方法由队列决定，`--merge-method` 等参数会被忽略并给出警告。线性历史是合并的硬性要求——任何一层 base 前移都会破坏它，需要 `gh stack rebase` 恢复。

## 分支保护与 CI：按栈底执行

栈中每个 PR 的规则都不是按它的直接 base 评估，而是按**栈的 base（通常就是 main）**评估：required reviews、required status checks、CODEOWNERS、代码扫描都遵循这一规则。也就是说，栈中间的 PR 与最底层 PR 执行同一套标准，不会因为"中间层 base 是另一个 PR 分支"而绕过保护。合并某个 PR 的前提是它下面的所有 PR 也满足同样要求。

GitHub Actions 同理：配置为 `pull_request` 且针对 main 的工作流，会对栈中**每一个** PR 触发，无需为栈改 workflow。栈的元数据可通过 `github.event.pull_request.stack` 在 workflow 表达式中读取。

## AI 代理集成

```bash
gh skill install github/gh-stack
```

装上后，AI 编码代理在判断"这是一次适合拆栈的改动"时会按层拆分提交，并给每个 PR 设置正确的 base，而不是把所有改动塞进一个大 PR。

这个技能随仓库持续维护，v0.1.1 做过一次专门瘦身：`SKILL.md` 从约 891 行（约 10.8K token）精简到约 183 行（约 2.1K token），核心说明加按需加载的引用结构让 token 占用下降约 81%；在两个模型的评测里通过了全部受测工作流，工具调用更少，输入 token 比旧版省约 34%。对按 token 计费的代理会话来说，技能本身的体积就是运行成本的一部分。

## 与其他工具的差异

栈式评审不是新概念——Google 内部的 Critique、Gerrit、以及第三方的 Graphite、ghstack、git-spice 都实现了类似能力。gh-stack 的差异在"平台原生"：

| 维度 | gh-stack | 第三方工具（Graphite 等） |
|------|----------|--------------------------|
| 安装 | `gh extension install` 一行 | 需单独注册账号或部署服务 |
| GitHub 集成 | 原生：栈是一等公民，规则按栈底执行，merge queue 适配 | 依赖第三方界面或浏览器插件 |
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
- 需要跨 fork 协作的仓库（栈要求所有分支在同一仓库，跨 fork 栈不受支持）

## 局限

- 公开预览阶段的功能，命令与行为可能变化
- 栈内所有分支必须在同一仓库，不支持跨 fork；GitHub Desktop 不支持栈操作
- `gh stack modify` 对仓库状态要求严格：栈已在本地检出、工作树干净、没有进行中的 rebase、没有 PR 正在排队合并、提交历史线性（无 merge commit、无分叉）。现实里这五条常常凑不齐
- 底层合并后，上方 PR 自动重定向到栈的 base，该层 CI 需要重新跑
- modify 会话被中断时需要显式恢复（退出码 10）

## 结尾判断

gh-stack 值得关注的不是命令本身，而是位置：栈第一次成为 GitHub 平台认识的对象，分支保护、CI 触发、merge queue 都按栈的语义执行，这是 Graphite 这类工具拿不到的待遇。已经在 GitHub 上、被大 PR 拖累评审效率的团队，现在就可以在预览阶段试起来，从一条三层的栈开始感受 `gh stack` 的日常节奏；需要跨平台、或对自动化有更复杂要求的团队，可以等预览期结束再评估，届时第三方工具的成熟度优势还剩多少，会是一个更有意思的问题。

## 参考

- 官方站点：[github.github.com/gh-stack](https://github.github.com/gh-stack/)
- 仓库：[github.com/github/gh-stack](https://github.com/github/gh-stack/)
- CLI 命令参考：[docs.github.com · Stacked PRs CLI commands](https://docs.github.com/en/pull-requests/reference/stacked-prs-cli-commands)
- Stacked PRs 规则：[docs.github.com · Stacked pull requests](https://docs.github.com/en/pull-requests/reference/stacked-pull-requests)
