---
title: "Anthropic Claude GitHub App：把 Claude Code 接进 Pull Request 工作流"
date: "2026-05-24T11:47:01+08:00"
lastmod: "2026-09-29T19:30:00+08:00"
slug: "anthropic-claude-github-app-pr-workflow"
github_repo: "apps/claude"
source_key: "gh:apps/claude"
description: "Anthropic 官方的 Claude GitHub App（github.com/apps/claude）配合开源的 claude-code-action，让团队在 PR 和 Issue 里 @claude 直接改代码、修 CI。本文按官方仓库文档与 GitHub API 读数梳理其两层架构、权限模型、安全边界与接入步骤。"
draft: false
categories: ["技术笔记"]
tags: ["Anthropic", "Claude", "GitHub", "Pull Request", "代码审查"]
---

## 学习目标

读完本文，可以：

1. 说清 Claude GitHub App 的两层架构：App 管什么、跑在你仓库里的 workflow 管什么
2. 判断它是否适合你的团队：能干什么、明确不干什么
3. 用 `/install-github-app` 或手动三步完成接入，并知道每一步在装什么
4. 理解它的权限模型与安全设计：谁触发、commit 归谁、怎么防注入
5. 避开常见的接入坑：@claude 没反应、CI 日志读不到、私有仓库不能 assign

## 目录

- [一句话判断](#一句话判断)
- [架构：App 与 Action 各管一层](#架构app-与-action-各管一层)
- [工作机制](#工作机制)
- [任务流案例：一次 CI 报错的处理](#任务流案例一次-ci-报错的处理)
- [与 GitHub Copilot coding agent 的对比](#与-github-copilot-coding-agent-的对比)
- [接入方式](#接入方式)
- [技术边界与采用建议](#技术边界与采用建议)
- [常见问题](#常见问题)
- [练习](#练习)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [资料口径说明](#资料口径说明)

## 一句话判断

Anthropic 官方的 Claude GitHub App（`github.com/apps/claude`，2025 年 4 月底上架）把 Claude Code 接进 PR 和 Issue：reviewer 在评论里 `@claude`，它读对话、改文件、推 commit、回复进度。App 本身不做执行——真正的活儿由你仓库里一个引用 `anthropics/claude-code-action` 的 GitHub Actions workflow 完成，跑在你自己的 runner 上，用你自己的 Anthropic 凭证。App 的官方描述也写明：它基于公开的 Claude Code SDK 构建。

这套设计和"托管服务"是两回事：代码执行完全发生在你自己的 runner 上，只有模型调用发给你选定的 API 提供方。适合已经在用 Anthropic 模型、希望 AI 在 PR 里直接动手的团队；只想自动合并或做 PR 摘要的场景有更便宜的工具。

## 架构：App 与 Action 各管一层

Claude 的 GitHub 集成由两个部件拼成，混为一谈会看不懂它的权限和行为：

| 部件 | 是什么 | 职责 |
|------|--------|------|
| Claude GitHub App | Anthropic 托管的 GitHub App（slug `claude`） | 接收 webhook、以 `claude[bot]` 身份发评论；持有 GitHub 侧权限 |
| claude-code-action | 开源仓库 `anthropics/claude-code-action`（MIT，TypeScript），你在 workflow 里引用的 Action | 装好 Claude Code CLI 并执行，处理触发词、分支和评论逻辑 |

数据流是：事件发生 → App 收到 webhook → 你仓库里的 workflow 被触发 → `claude-code-action` 在你的 runner 上启动 Claude Code → Claude 用 GitHub API 和文件工具干活 → 通过 App 身份把结果写回评论。

官方示例 workflow（`examples/claude.yml`）只监听四类事件：

```yaml
on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  issues:
    types: [opened, assigned]
  pull_request_review:
    types: [submitted]
```

也就是说，日常使用只有两种入口：在评论、Issue 正文或标题里写 `@claude`（词边界匹配，`@claude-bot` 这种不会触发），或者把 Issue 分配给指定用户（默认即 Claude）。CI 挂了不会自动叫醒它——得有人在 PR 里喊一声。

## 工作机制

### 触发层：谁能叫动它

- **写权限门槛**：只有对仓库有 write 权限的用户能触发 Claude。这是防滥用的第一道闸，外部协作者默认叫不动。
- **机器人默认不触发**：其他 GitHub App（包括 dependabot）的评论不会唤起 Claude，需要用 `allowed_bots` 显式放行。这同时避免了两个机器人互相触发打无限循环。
- **GitHub 自身的限制**：`github-actions[bot]` 发的评论触发不了后续 workflow，这是 GitHub 防死循环的机制。想让自动化流程调用 Claude，得用 PAT（Personal Access Token，个人访问令牌）或自己的 App token 发评论。
- **自定义触发**：`trigger_phrase` 可把 `@claude` 换成 `/claude`；Issue 侧还支持 `assignee_trigger` 和 `label_trigger`。

### 执行层：Claude 在你的 runner 上干什么

`claude-code-action` 底层是 `anthropics/claude-code-base-action`，负责安装并运行 Claude Code CLI。执行环境有几个默认值值得知道：

- **工具收敛**：默认只开 GitHub MCP（Model Context Protocol）server 和文件操作两类工具；Bash 默认禁用，要用 `claude_args: --allowedTools "Bash(npm test),Bash(git status)"` 这种写法逐条放行。
- **浅克隆**：PR 场景只拉最近 20 个 commit，新建分支只拉 1 个。要完整历史得自己在 checkout 步骤里配。
- **单条评论**：Claude 的全部输出——进度 checkbox、中间状态、最终结果——都更新在同一条评论里，不刷屏。
- **自动化模式**：workflow 里给了 `prompt` 输入就立即执行（不等 @claude），适合定时巡检、路径触发的自动审查这类场景。

### 权限与身份层

App 安装页申请的 GitHub 权限（GitHub Apps API，2026-09-29 读数）覆盖 Actions、Checks、Contents、Discussions、Issues、Pull requests、Repository hooks、Workflows 的 write，加 Members、Metadata、Statuses 的 read。但官方安全文档明确区分了"申请了"和"在用"：**当前实际使用的只有 Contents、Pull requests、Issues 的读写**，其余是为未来功能预留的。

workflow 这边还有一层自己的 permissions，官方示例是：

```yaml
permissions:
  contents: write
  pull-requests: write
  issues: write
  id-token: write    # App 认证走 OIDC，必须给
  actions: read      # 想让 Claude 读 CI 结果就加这行
```

commit 身份归属 `claude[bot]`（App 安装身份），不归属触发评论的开发者。默认 commit 不带签名；要 verified 标记有两条路：`use_commit_signing: true`（走 GitHub API 创建 commit，简单但做不了复杂 git 操作），或者配 SSH 签名密钥（保留完整 git 能力）。

## 任务流案例：一次 CI 报错的处理

把上面的机制串成一个真实场景：

1. PR 上 lint 挂了。**没有人工触发，Claude 不会动**——它不监听 `check_run` 事件
2. reviewer 在 PR 里评论：`@claude CI 挂了，看下日志修一下`
3. workflow 触发，PR 里出现一条带 checkbox 的评论，Claude 开始干活
4. 因为 workflow 配了 `actions: read`，Claude 能拉取 workflow run 和 job 日志，定位到 `src/api/handler.py` 的类型错误
5. Claude 在本地改文件、跑测试（如果 `--allowedTools` 放行了测试命令），往 PR 分支推一个 commit
6. 新 commit 触发新一轮 CI，过了；那条评论同步更新结果

注意第 4 步的前提：`actions: read` 要在两处都配上——workflow 顶层 permissions 和 action 的 `additional_permissions` 输入。漏一处就读不到日志，这是最常见的接入坑之一。

整个流程里每次触发都是一次独立会话：Claude 看到的上下文来自当前 PR 对话和仓库现状，不记得上次对话说过什么。

## 与 GitHub Copilot coding agent 的对比

可对比的同类产品里，GitHub Copilot coding agent 是最接近的一个。按各自公开文档：

| 维度 | Claude GitHub App | GitHub Copilot coding agent |
|------|------------------|----------------------------|
| 触发方式 | 评论里 `@claude`，或 assign Issue | 把 Issue 分配给 Copilot |
| 运行位置 | 你自己的 Actions runner | GitHub 托管的 Actions |
| 模型与计费 | 自带 Anthropic API key 或订阅凭证，按 API 用量计费 | Copilot 订阅内含 |
| 开源程度 | Action 开源（MIT），行为可审计 | 托管服务 |
| 产出 | 直接往 PR 分支推 commit | 创建 draft PR |

两者都会在分支上留下 commit 并等人审查，都刻意不替你合并。区别主要在计费模型和可控性：Claude 方案的成本跟 API 用量走，且整条执行链路开源可查；Copilot 方案对已有订阅的团队几乎零配置。市面上 Mergify 这类合并自动化工具解决的是另一个问题（合并队列和规则引擎），它们不写代码，和这两个不是一类东西。

## 接入方式

**最省事的路**（要求直连 Anthropic API）：在装了 Claude Code 的终端里运行 `claude`，执行 `/install-github-app`，它会引导你装 App、配 secrets。

手动三步（要求仓库 admin 权限）：

1. 在 [github.com/apps/claude](https://github.com/apps/claude) 点 Install，选目标仓库
2. 在仓库 Secrets 里加认证：`ANTHROPIC_API_KEY`，或 `CLAUDE_CODE_OAUTH_TOKEN`（Pro/Max 订阅用户可在本地跑 `claude setup-token` 生成）。不想存静态密钥的话，还有 Workload Identity Federation 方案——用 workflow 的 OIDC token 换短期凭证，免保管
3. 把 [examples/claude.yml](https://github.com/anthropics/claude-code-action/blob/main/examples/claude.yml) 拷进你仓库的 `.github/workflows/`

第 3 步不能省：只装 App 不放 workflow，事件到了没有任何东西响应它。用 Bedrock 或 Vertex AI 的团队没法用 `/install-github-app`，走手动路径并参考仓库里的 `docs/cloud-providers.md`。

组织层面装第三方 App 可能被策略拦住，官方也提供了自建 custom GitHub App 的清单和工具（`docs/setup.md`）。

**验收**：在一个测试 PR 里评论 `@claude 你好，介绍一下这个 PR 改了什么`，观察 Actions 页的运行日志和 PR 里的评论回复。

官方文档：<https://docs.claude.com/en/docs/claude-code/github-actions>

## 技术边界与采用建议

### 明确不做的事

官方能力清单写得很硬，这些事它不做：

- **不自动创建 PR**：推完 commit 给你一个预填好的 PR 创建链接，人点了才算数——保住分支保护规则和人工把关
- **不提交正式 PR review，不 approve PR**：审查意见以普通评论形式给出
- **不做危险 git 操作**：不 merge、不 rebase、不 force push，只在被调用的分支或自己新建的分支上推 commit（这个约束写在系统提示里，放宽工具权限也绕不开）
- **不改 workflow 文件**：官方 FAQ 明确出于安全原因限制了 workflow 写权限，防止 AI 改动 CI 配置引发连带后果
- **不出仓库**：App token 是短期的、锁定在当前仓库，跨仓库写操作做不了

### 安全设计

几处值得知道的防御：

- **配置文件防篡改**：PR 场景下，`CLAUDE.md`、`.claude/`、`.mcp.json` 等配置从 PR 的 base 分支恢复，PR 里改动的版本只存到 `.claude-pr/` 目录做参考——外部贡献者没法借改 CLAUDE.md 给 Claude 塞指令
- **注入内容清洗**：HTML 注释、不可见字符、隐藏 HTML 属性等常见注入载体会被剥离；还可以用 `include_comments_by_actor` 只把指定用户的评论喂给 Claude
- **`allowed_non_write_users` 是高危口子**：放行无写权限用户会绕过主安全机制，官方标注 RISKY，只建议在权限收得很窄的自动化 workflow 里用

### 采用建议

值得接入：团队已有 Anthropic API 或订阅；review 带宽紧张，想让 AI 处理"修 lint、补测试、按规范改代码"这类明确任务；希望执行链路开源可审计。

不必接入：想要的是自动合并、分支纪律这类规则自动化（Mergify 类工具更对口）；没有 Anthropic 预算但已有 Copilot 订阅（coding agent 开箱即用）；合规上硬性要求 commit 实名到开发者个人——默认归属 `claude[bot]`，改用 SSH 签名密钥虽然可以把 commit 归到指定账号，但那通常也得是个专门的服务账号，而不是操作者本人。

## 常见问题

### @claude 发了评论却没反应？

按顺序查：评论者对仓库有无 write 权限；`.github/workflows/` 里是否放了 workflow（只装 App 不够）；触发词是不是完整匹配 `@claude`；Actions 是否被仓库设置禁用。

### 能让它盯着 CI、挂了自动修吗？

默认不能。它不订阅 `check_run` 之类的 CI 事件，需要人先在 PR 里 @ 它。可以自己扩展 workflow 监听 `workflow_run` 失败事件并调 Claude，但官方安全文档提醒：这类事件以 base 仓库 secrets 运行，且要检查上游触发者的写权限，别照搬 `pull_request_target` 的不安全写法。

### 它推的 commit 能追溯到人吗？

不能，归属 `claude[bot]`。变通办法是团队约定在评论里说明意图，审计时按"谁叫的 Claude"追。对实名要求硬性合规的团队，这个归属方式本身就是接入的否决项，先过合规再谈别的。

### 私有组织仓库里为什么没法把 Issue assign 给 Claude？

GitHub 限制私有组织仓库只能 assign 组织成员，Claude 不是。官方 FAQ 给的替代是用 `assignee_trigger` 指向一个真实存在的机器人账号，或用 label 触发。

### 两个 AI 机器人会不会在 PR 里打起来？

默认不会。其他 bot 的评论不触发 Claude（`allowed_bots` 默认为空）。放行时别用 `'*'`——官方安全文档特别警告：公开仓库上任何人的 App 都可能通过发评论来驱动你的 workflow，要列具体名字。

## 练习

### 练习一：跑通第一次对话

1. 在测试仓库完成接入三步（装 App、配 secret、放 workflow）
2. 在 PR 里评论 `@claude 用一句话说明这个 PR 的改动`
3. 观察：Actions 页的运行记录、PR 里的单条评论如何更新
4. 记录：从评论到回复的耗时

### 练习二：让它修一个真实的 CI 报错

1. 在 workflow 里给 `actions: read`（permissions 和 `additional_permissions` 两处）
2. 制造一个 lint 错误并推上 PR，等 CI 挂
3. 评论 `@claude 看下失败的日志并修复`
4. 观察：它是否读到了日志、改动是否通过新一轮 CI、`--allowedTools` 是否需要放行测试命令

### 练习三：搭一条自动化 PR 审查

1. 复制官方 `docs/solutions.md` 里的自动审查示例 workflow
2. 在 workflow 里传入 `prompt: "Review this PR for security issues"`，体验自动化模式与交互模式的差别
3. 对比：同样一个 PR，自动化模式和 `@claude` 模式的触发与输出有何不同
4. 评估：你的团队更适合把 Claude 放在哪几个环节

## 自测题

1. Claude GitHub App 和 `claude-code-action` 各负责什么？为什么说"装了 App 不等于能用了"？
2. 默认配置下哪些事件能触发 Claude？为什么 CI 挂了它不会自动响应？
3. `actions: read` 为什么要配两处？漏一处会怎样？
4. 它推的 commit 归属谁？默认带签名吗？两种签名方案各牺牲了什么？
5. `CLAUDE.md` 在 PR 场景下从哪里读取？这个设计防的是什么攻击？

## 进阶路径

准备在生产使用，按这个顺序推进：

1. **读官方 FAQ 与安全文档**——`claude-code-action` 仓库的 `docs/faq.md` 和 `docs/security.md` 覆盖了绝大多数接入问题，比社区帖可靠
2. **收敛权限**——workflow permissions 按需最小化，`--allowedTools` 逐条放行命令，不开 `allowed_non_write_users`
3. **建立使用规范**——明确什么任务 @claude、谁负责审它的 commit、出问题找谁
4. **需要深度定制时再看 Agent SDK**——App 和 Action 都基于 Claude Code 的 Agent SDK 构建，SDK 文档（[docs.claude.com/en/docs/claude-code/sdk](https://docs.claude.com/en/docs/claude-code/sdk)）是理解执行内核的入口
5. **持续跟进**——Action 仍在快速迭代（v1.0 于 2025 年 8 月发布，此前 v0.x 的多个输入已废弃），升级前先看 `docs/migration-guide.md`

## 资料口径说明

本文事实核查基于 2026-09-29 取得的以下来源：

1. **GitHub API**：`anthropics/claude-code-action` 仓库元数据（9,233 stars / 2,176 forks，TypeScript，MIT；创建于 2025-05-19）、Claude App 的公开 App 信息（slug `claude`，创建于 2025-04-30，权限与事件清单）
2. **官方仓库文档**：`claude-code-action` 的 README 及 `docs/` 下的 `faq.md`、`setup.md`、`usage.md`、`security.md`、`capabilities-and-limitations.md`，以及 `examples/claude.yml`
3. **官方产品文档**：<https://docs.claude.com/en/docs/claude-code/github-actions>

该集成仍在活跃开发中（官方文档标注 beta），权限、输入参数和行为可能变化，接入前请以官方文档为准。
