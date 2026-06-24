---
title: "no-mistakes：在 git push 之前插入 AI 评审闸门，Code Agent 时代的代码质量门"
date: 2026-06-24T20:55:27+08:00
slug: "kunchenguid-no-mistakes-git-ai-gate"
description: "no-mistakes 是一个本地 git 代理 + AI 评审闸门：把 push 路由到 disposable worktree，跑 review→test→docs→lint→PR→CI 全流程 AI 检查，全部通过后才转发到真实 remote。Agent 无关（claude/codex/rovodev/opencode/pi），人类保留终审权。"
draft: false
categories: ["技术笔记"]
tags: ["Git", "AI Agent", "Code Review", "PR 自动化", "Go", "Coding Agent"]
---

# no-mistakes：在 git push 之前插入 AI 评审闸门，Code Agent 时代的代码质量门

> **阅读时间**：约 14 分钟
>
> **适用读者**：Coding Agent 重度用户、想给 AI 生成的代码"加一道安检"的工程师、CI/CD 折腾爱好者
>
> **前置知识**：了解 git remote、worktree、CI 基础概念；用过任意一种 coding agent（Claude Code / Codex / Cursor / Cline）会更顺

## 这篇文章解决什么问题

2026 年 Coding Agent 已经能写完整 PR，但随之而来的问题是：**AI 写的代码谁来把关**？

传统 CI 只做"机械检查"（编译 / 测试 / lint），抓不住"逻辑漏洞 / 设计缺陷 / 文档缺失 / 接口不一致"这一类只有人能看出来——或者只有另一个 LLM 才能看出来——的问题。Hiring Agent 解决"AI 筛简历"，no-mistakes 解决**"AI 给 AI 写的代码做最后一道 AI 评审"**这件事。

这是一个**原理拆解 / 架构分析**形态的项目——它的价值不在"做了什么检查"，而在"怎么在不动开发者工作流的前提下插入一道 AI 闸门"。

## 项目身份卡

- **仓库**：[kunchenguid/no-mistakes](https://github.com/kunchenguid/no-mistakes)
- **主语言**：Go
- **License**：MIT
- **Stars / Forks**：1.8k / 128
- **首发**：2026-04-05（项目非常新）
- **最近更新**：2026-06-23
- **体积**：4.3 MB（含 docs site）
- **官方文档**：[kunchenguid.github.io/no-mistakes](https://kunchenguid.github.io/no-mistakes/)

## 核心判断：这是"git 代理 + AI gate"，不是"AI 自动修复"

第一眼很容易把它理解成"自动帮我修代码"——但 README 第一段明确：**"auto-fix or review findings, your call"**。

这意味着：

- **safe & mechanical 的修复**（拼写错误 / import 顺序 / 格式）→ AI 自动改
- **涉及意图 / 架构 / 业务的修复** → 升级到人类，由人 approve / fix / skip
- **全部绿灯才转发 push** → 否则卡在 gate

**和现成工具的差异**：

| 维度 | Pre-commit hook | GitHub Actions AI Review | no-mistakes |
|------|------------------|--------------------------|-------------|
| 触发点 | commit 前 | push 后 | push 前 |
| 运行环境 | 本地 hook | 云端 CI | 本地 disposable worktree |
| 能不能修代码 | 不能 | 不能（只 review） | 可以（safe fixes） |
| Agent 选择 | 写死 | 平台绑定 | claude / codex / rovodev / opencode / pi / acpx |
| 阻塞 PR 吗 | 阻塞 commit | 不阻塞 | 不阻塞 commit，只阻塞 push |

## 系统地图：git push 到 PR 完成的完整链路

```
 开发者本地                          no-mistakes gate                         远端
 ┌──────────┐                                                              ┌──────────┐
 │ working  │                                                              │          │
 │ tree     │                                                              │ origin   │
 │ (你的工作)│                                                              │ (GitHub) │
 └────┬─────┘                                                              └────▲─────┘
      │ git push no-mistakes                                                 │
      ▼                                                                     │
 ┌──────────────────────────────────────────────────────────────────────┐  │
 │ ① init: 一次性配置，remote 指向 gate                                  │  │
 │ ② gate 收到 push → 创建 disposable worktree (独立目录，独立 HEAD)     │  │
 │ ③ 在 worktree 跑 pipeline:                                            │  │
 │    review → test → docs → lint → (可选)push → (可选)open PR → watch CI│  │
 │ ④ 每个 step 产生 finding:                                             │  │
 │    - auto_fix → AI 直接改                                             │  │
 │    - ask_user → 升级给开发者，TUI 弹窗                                │  │
 │    - skip → 开发者主动跳过                                             │  │
 │ ⑤ 全部绿灯 → gate 把分支 push 到真实 origin，开 PR                    │──┘
 │ ⑥ 有红灯 → 卡住，开发者从 TUI 处理                                    │
 └──────────────────────────────────────────────────────────────────────┘
```

**关键设计**：

- **disposable worktree**——开发者本地 working tree 完全不动，gate 在 `~/.no-mistakes/repos/<hash>.git/` 跑独立副本
- **每步独立**——review 失败不会阻止 test 跑，开发者拿到完整 finding 列表
- **TUI 介入**——不靠 IDE 弹窗，靠 CLI 的 TUI 列出所有 finding 让开发者决策

## 核心机制逐条拆解

### 机制 1：本地 git remote 代理

`no-mistakes init` 在仓库里加一个名为 `no-mistakes` 的 git remote：

```bash
$ no-mistakes init
✓ Gate initialized
  repo   /Users/you/src/my-repo
  gate   no-mistakes → /Users/you/.no-mistakes/repos/abc123def456.git
  remote git@github.com:you/my-repo.git
  skill  /no-mistakes installed for agents at user level
```

从此 `git push no-mistakes <branch>` 不会真的把分支推到 GitHub，而是推到这个本地"中转仓库"。no-mistakes 守护进程持续监听这个仓库的引用变化，触发 pipeline。

**这与 GitHub Actions 的本质区别**：CI 在云端跑，需要你 push 完才知道有没有问题；no-mistakes 在 push **之前**就拦住，跑完再决定要不要真的推。

### 机制 2：disposable worktree

每个 push 在 `~/.no-mistakes/repos/<hash>.git/` 下创建一个临时 worktree——这是一个**完全独立的 git 目录**：

- 不会污染开发者的工作树
- 失败回滚零成本
- 多个 push 可以并行跑不同 worktree
- 跑完的 worktree 保留供事后审计

### 机制 3：Pipeline 编排

Pipeline 的每一步是一个独立 step，按顺序触发：

| 步骤 | 工具 / Agent | 输出 |
|------|------------|------|
| review | 选定的 coding agent | 行级 comment + 总结 |
| test | pytest / go test / vitest 等 | pass/fail + 失败 trace |
| docs | 文档检查 agent | 是否需更新 README / docstring |
| lint | 项目自带 linter | pass/fail + diff |
| push | 内部 git push | 真实 origin 接收 |
| PR | gh / 自家 PR 模板 | PR opened |
| CI | watch remote CI | 等 CI 绿 |
| auto-fix | 同一个 agent | 修 mechanical 问题 |

**每步可以单独配置**：比如你只想要 review + test，不要 docs 检查，编辑 config 即可。

### 机制 4：Finding 三分类

这是项目方设计哲学的核心——

| Finding 类型 | 处理方式 | 例子 |
|------------|----------|------|
| `auto_fix` | AI 直接改，提交一个 fixup commit | 拼写错误、未用 import、formatting |
| `ask_user` | 升级给开发者，TUI 弹窗让 approve / fix / skip | "这里要不要改 API 命名" |
| `skip` | 开发者之前标记过 skip，这次不再问 | 已知不修的 issue |

**"Human stays in charge"**：项目方在 README 里把这条放在和"Agent-agnostic"并列——意图很明确，**AI 不能悄悄改你的代码**。

### 机制 5：Agent 无关

支持 6 种 coding agent 作为 pipeline 驱动：

| Agent | 适配方式 |
|-------|---------|
| `claude` | Claude Code CLI |
| `codex` | OpenAI Codex CLI |
| `rovodev` | Rovo Dev CLI |
| `opencode` | OpenCode |
| `pi` | Pi agent |
| `acp:<target>` | 任意 ACP（Agent Communication Protocol）目标 |

**判断**：这种"agent 无关"的设计是给 6-12 那种"coding agent 工具链每 2 个月换一波"的现实留的活路。绑定单一 agent 的工具在 6 个月后大概率过时。

### 机制 6：`/no-mistakes` 技能（agent 原生）

README 提到 `/no-mistakes` 是一个**给 coding agent 用的技能**——当 agent 完成一个任务后可以自己调这个技能走 gate：

```
agent 完成代码 → /no-mistakes → 跑 gate → 通过则自动 push + 开 PR
```

**这是 agent-native 模式**——把 gate 嵌进 agent 的"完成 → 提交"循环里，而不是事后靠开发者手动触发。

## 典型使用流

### 场景 A：开发者手动 push 后等结果

```bash
$ git checkout my-branch
$ # ... 写代码 ...
$ git push no-mistakes
* Pipeline started

$ no-mistakes
# 打开 TUI 看每个 finding：
#   [auto_fix]  → 自动改完
#   [ask_user]  → 你 review 后选 approve / fix / skip
#   ...
# 全部绿灯后：
* Branch pushed to origin
* PR opened: https://github.com/you/my-repo/pull/42
* Watching CI...
* CI green ✓
```

### 场景 B：coding agent 完成后自己触发

```
User: 帮我给 foo.py 加单元测试

Claude Code: 写完测试后
> /no-mistakes
* Pipeline started
* review: 3 findings, 2 auto-fixed, 1 ask_user
* test: pass
* docs: updated docstring
* lint: pass
* PR opened: https://github.com/you/my-repo/pull/43
* CI green
```

### 场景 C：Fork 贡献

```bash
# 保持 origin 指向 upstream
$ no-mistakes init --fork-url git@github.com:you/fork.git
```

**特别适合**给开源项目提 PR：本地不污染、CI 帮你跑、PR 自动开。

## 优势：把"AI 写的代码"从"黑盒"变成"可审计链路"

**对比直接 `git push origin` + `gh pr create`**：

| 维度 | 裸 push | no-mistakes |
|------|---------|-------------|
| 失败的代码会污染 origin 吗 | 会 | 不会 |
| 跑完测试 / lint 才发现 bug | 是 | 否（push 前完成） |
| AI 写的逻辑有 bug 谁负责 | 你 | 有完整 finding 链可追溯 |
| CI 红灯后再回头改 | 是 | 否（gate 内就修了） |
| agent 切换代价 | 工作流绑死 | 6 种 agent 任意切 |

## 适用边界

**适合**：

- Coding Agent 重度用户（每天 5+ 个 AI 写的 PR）
- 团队想统一"AI 代码准入"标准
- 维护开源项目 / 给上游提 PR
- CI 已经很重、想前置一部分检查到 push 前

**不适合**：

- 简单仓库（< 100 行），搭 gate 成本不划算
- 完全不用 coding agent 的传统开发者（直接 husky + pre-commit 就够了）
- 不能装额外 CLI 的受限环境（CI runner、无 admin 权限的容器）
- 对"工作树有副本"有洁癖的人（每个 push 多个 worktree 副本，磁盘会涨）

## 安装

```bash
curl -fsSL https://raw.githubusercontent.com/kunchenguid/no-mistakes/main/docs/install.sh | sh
```

支持的安装方式：
- macOS / Linux：一键 curl
- Windows：见 [installation guide](https://kunchenguid.github.io/no-mistakes/start-here/installation/)
- Go install：`go install ...`
- Build from source：见 docs

## 自测题

1. 为什么不直接用 pre-commit hook？pre-commit + no-mistakes 在定位上有什么本质区别？
2. disposable worktree 和"开发者 working tree 共享同一个 .git"有什么区别？为什么这个区分重要？
3. Finding 三分类（auto_fix / ask_user / skip）的设计哲学是什么？项目方为什么强调"Human stays in charge"？
4. 假设你公司在用 Claude Code，团队里有同事在用 Codex——no-mistakes 怎么处理这个异构环境？

## 进阶阅读

- 官方文档：[kunchenguid.github.io/no-mistakes](https://kunchenguid.github.io/no-mistakes/)
- Agent Communication Protocol：[github.com/anthropics/agent-protocol](https://github.com/anthropics/acp) (假设地址)
- Git worktree 原理：[git-scm.com/docs/git-worktree](https://git-scm.com/docs/git-worktree)
- Pre-commit hook 框架：[pre-commit.com](https://pre-commit.com/)
- AI Code Review 工具对比：[coderabbit.ai](https://coderabbit.ai/) / [sourcery.ai](https://sourcery.ai/)

## 常见问题

**Q：会不会让 push 变慢？**
A：会。这是把"等 CI 反馈"前置到"push 前"的代价。但好的一面是 fail fast——红灯尽早暴露，节省事后回滚的工时。

**Q：多个 worktree 副本会不会吃光磁盘？**
A：会。git worktree 是真实副本，每个 push 多个 GB 不奇怪。建议在 `~/.no-mistakes/repos/` 上加个定期清理脚本。

**Q：AI 改坏了代码怎么办？**
A：项目设计里有 audit log（每个 worktree 保留），可以看哪个 step 改了什么、`ask_user` 类的 finding 都有明确提示。**但根本原则是：涉及意图的 finding 一定升级给你**，不会悄悄改。

**Q：能跟 GitHub Actions 配合吗？**
A：能，CI 步骤会 watch GitHub Actions 状态，全绿后才算 gate 通过。两者是串联关系，不冲突。

**Q：和 Husky / lint-staged 冲突吗？**
A：不冲突，可以叠用。Husky 跑 commit 前，no-mistakes 跑 push 前，GitHub Actions 跑 PR 后。**三道闸门，各管一段**。
