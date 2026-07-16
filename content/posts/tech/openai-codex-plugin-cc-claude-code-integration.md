---
title: 'openai/codex-plugin-cc 快速上手：让 OpenAI Codex 在 Claude Code 里跑 review / 派任务 / 接管的 7 个 slash command'
date: 2026-07-17T02:57:12+08:00
lastmod: 2026-07-17T02:57:12+08:00
draft: false
categories: ["技术笔记"]
tags: ["OpenAI Codex", "Claude Code", "Plugin", "Code Review", "AI Agent", "Anthropic"]
description: "codex-plugin-cc 是 OpenAI 官方维护的 Claude Code 插件，28.9k stars，把 Codex CLI 装进 Claude Code 用 /codex:review 做只读审查、/codex:adversarial-review 做 steerable 挑战、/codex:rescue 派任务、/codex:transfer 接管会话。本文拆解它的 7 个 slash command、codex-companion.mjs 桥接脚本、以及背景任务的实际工作流。"
weight: 1
slug: "openai-codex-plugin-cc-claude-code-integration"
author: text-matrix
---

## 一句话判断

**codex-plugin-cc（[openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc)）是 OpenAI 官方维护的 Claude Code 插件，28.9k stars**，把 Codex CLI 装进 Claude Code，让你用 `/codex:review` / `/codex:adversarial-review` 在 Claude Code 里跑 Codex 级别的代码审查，用 `/codex:rescue` 把任务派给 Codex（含失败测试排查、bug 调查、继续上次任务），用 `/codex:transfer` 把 Codex 跑出来的会话结果接回 Claude Code。整条链路靠一个 `scripts/codex-companion.mjs` 桥接脚本把 Claude Code 的 `Bash` 工具调用转给本地 `@openai/codex` CLI，并保留 `--wait` / `--background` / `--resume` / `--fresh` 等状态管理。

如果你是 Claude Code 重度用户，但偶尔想要"换个角度看代码 / 派个不贵的模型先排查 / 把长跑任务丢给 Codex 后台"，这篇文章值得读完整。

---

## 系统地图

```
┌────────────────────────────────────────────────────────────────────────┐
│                 Claude Code (主战场)  +  Codex 插件                       │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Claude Code                                                       │ │
│  │    ├─ /codex:setup             安装 / 登录状态检测 / 自动装 Codex   │ │
│  │    ├─ /codex:review            只读 review（当前变更 / base 分支） │ │
│  │    ├─ /codex:adversarial-review steerable 挑战 review（带 focus）  │ │
│  │    ├─ /codex:rescue            派任务给 Codex（含 resume / fresh） │ │
│  │    ├─ /codex:transfer          接管 Codex 会话 / 接续工作          │ │
│  │    ├─ /codex:status            查看后台任务状态                    │ │
│  │    ├─ /codex:result            拿后台任务结果                      │ │
│  │    └─ /codex:cancel            取消后台任务                        │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                  ↓                                       │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  codex-companion.mjs (Node.js 桥接脚本)                            │ │
│  │    ├─ 解析 Claude Code 传入的 --wait / --background / --base       │ │
│  │    ├─ 调本地 @openai/codex CLI                                     │ │
│  │    ├─ 流式 stdout → Claude Code 渲染                               │ │
│  │    └─ 后台任务状态写入 job state file                              │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                  ↓                                       │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  @openai/codex (本地 npm 全局包)                                   │ │
│  │    └─ Codex CLI binary + login + API key                          │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  codex:codex-rescue subagent（/agents 中可见）                      │ │
│  │    └─ Claude Code subagent，封装 /codex:rescue 的 subagent 调用   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
                                  ↓
                          Codex 模型后端
                                  ↓
                       gpt-5 / gpt-5.4-mini / spark 等
```

这张图最重要的一条路径：**Claude Code 的 `Bash` 工具 → `codex-companion.mjs` → 本地 `@openai/codex` CLI → Codex 模型后端**。Claude Code 不直接调 Codex API，而是通过自家 bash 工具调用桥接脚本，桥接脚本负责解析参数 + 转发 + 流式回传 + 后台任务管理。

---

## 边界与角色划分

codex-plugin-cc 的工程边界可以按"谁负责"分三组：

| 角色 | 谁负责 | 谁不允许 | 关键文件 |
|---|---|---|---|
| Slash command 定义 | `plugins/codex/commands/<name>.md`（8 个） | 直接调 Codex CLI | `commands/review.md` 等 |
| 桥接逻辑 | `plugins/codex/scripts/codex-companion.mjs` | 改 Claude Code 自身行为 | `scripts/` |
| Subagent 封装 | `plugins/codex/agents/codex-rescue.md` | 自动跑 rescue 不经用户 | `agents/` |

不变项之外，**codex-plugin-cc 明确不做**的事：

- ❌ **不**做只读之外的任何 review 行为。`commands/review.md` 第一段就是 "This command is review-only. Do not fix issues, apply patches, or suggest that you are about to make changes."
- ❌ **不**让 `/codex:review` 支持 staged-only / unstaged-only / 自定义 focus text——这些功能只在 `/codex:adversarial-review` 里。
- ❌ **不**自动接管 Codex 会话——`/codex:transfer` 必须由 Claude Code 用户显式触发。
- ❌ **不**让 Claude Code 直接调 Codex API。所有调用走 `Bash(node: ...)` → `codex-companion.mjs` → 本地 CLI，避免在 Claude Code 进程里嵌入 Codex 凭证。

这四条"不做"恰好决定了 codex-plugin-cc 的设计取舍——下面拆开看。

---

## 关键机制：7 个 slash command 怎么工作

### 1. 安装：先 add marketplace，再 install plugin

```bash
# 在 Claude Code 里
/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex
/reload-plugins

# 检测 + 自动装 Codex CLI
/codex:setup
```

`/codex:setup` 是 onboarding 入口：检查 Codex 是否安装、未装就尝试 `npm install -g @openai/codex`；检查是否登录、未登录就提示 `!codex login`。Node.js 18.18+ 是硬要求。

### 2. `/codex:review` — 默认 review-only

`commands/review.md` 的核心约束：

> This command is review-only.
> Do not fix issues, apply patches, or suggest that you are about to make changes.
> Your only job is to run the review and return Codex's output verbatim to the user.

它会先用 `git status --short --untracked-files=all` + `git diff --shortstat --cached` + `git diff --shortstat` 估算 review 规模：

- 工作树小（1-2 文件）→ 推荐 wait
- 工作树大 / 不确定 → 推荐 background
- 用 `AskUserQuestion` 一次性问用户（两个选项：Wait / Run in background），**Recommended 后缀**给推荐项

```bash
# 推荐用法
/codex:review --background

# 等结果
/codex:status
/codex:result

# 或者直接同步等
/codex:review --wait
```

支持 `--base <ref>` 做分支对比：`/codex:review --base main`。不支持 staged-only / unstaged-only / focus text——`commands/review.md` 写得直接："`/codex:review` is native-review only."

### 3. `/codex:adversarial-review` — steerable 挑战 review

`commands/adversarial-review.md` 是 review 的"带压测"版本：

- 同样的 review target selection（包含 `--base <ref>`）
- 同样的 `--wait` / `--background`
- **额外**可以接受 focus text——把用户写的"challenge whether this was the right caching and retry design"作为压力测试方向
- 用途：challenge the direction, not just the code details；压测 auth / data loss / rollback / race conditions / reliability

```bash
/codex:adversarial-review --base main challenge whether this was the right caching and retry design
/codex:adversarial-review --background look for race conditions and question the chosen approach
```

仍然只读——不修复代码。

### 4. `/codex:rescue` — 派任务给 Codex subagent

`commands/rescue.md` 通过 `codex:codex-rescue` subagent 派任务，适合：

- investigate a bug
- try a fix
- 继续上次的 Codex 任务（`--resume`）
- 用便宜/快的模型（`--model gpt-5.4-mini --effort medium` / `--model spark`）

```bash
/codex:rescue investigate why the tests started failing
/codex:rescue fix the failing test with the smallest safe patch
/codex:rescue --resume apply the top fix from the last run
/codex:rescue --model gpt-5.4-mini --effort medium investigate the flaky integration test
/codex:rescue --model spark fix the issue quickly
/codex:rescue --background investigate the regression
```

**关键默认**：rescue 任务默认 long-running，必须 `--background` 或把 agent 移到 background（README 写"it's generally recommended to force the task to be in the background"）。

### 5. `/codex:transfer` — 接管 Codex 会话

把 Codex 跑出来的结果（或完整会话上下文）接管到 Claude Code 里继续工作。适合：rescue 跑了一半、你想用 Claude Code 的工具链继续改。

### 6. `/codex:status` / `/codex:result` / `/codex:cancel` — 后台任务管理

三件套：

- `status`：列当前所有 background Codex 任务的进度
- `result`：拿某个 task 的 stdout 结果（verbatim）
- `cancel`：停掉某个 task

设计意图：**review 是异步的，不阻塞 Claude Code 主对话**。用户能同时开多个 review / rescue 并行跑。

### 7. bridge 脚本：`codex-companion.mjs`

`scripts/codex-companion.mjs` 是整个插件的运行时心脏：

```javascript
// 伪代码（基于 commands/review.md 给出的 Bash 调用）
node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" review "$ARGUMENTS"
node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" rescue "$ARGUMENTS"
// status / result / cancel 同理
```

桥接脚本的工作：

1. 解析参数（`--wait` / `--background` / `--base` / `--resume` / `--fresh`）
2. 调本地 `@openai/codex` CLI（已登录、有 API key）
3. 流式回传 stdout（Claude Code 原样显示 verbatim）
4. 后台任务写入 job state file（`/codex:status` 读这个）

注意 README + commands 都强调："The companion script parses `--wait` and `--background`, but Claude Code's `Bash(..., run_in_background: true)` is what actually detaches the run"——detach 是 Claude Code 的 `run_in_background: true` 做的，不是 companion script 做的。

---

## 任务流案例：用 Codex 在 Claude Code 里做一次代码 review

**Step 1：装插件 + 装 Codex**

```bash
# 在 Claude Code 里
/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex
/reload-plugins
/codex:setup

# 或手动装 Codex CLI
npm install -g @openai/codex
!codex login
```

**Step 2：当前分支有未提交改动**

```bash
git diff --shortstat
# 12 files changed, 340 insertions(+), 89 deletions(-)
```

**Step 3：跑 review**

```bash
/codex:review --background
```

Claude Code 用 `AskUserQuestion` 问你 "Wait for results" / "Run in background"——选 Run in background。

**Step 4：检查进度**

```bash
/codex:status
```

显示 task_id + 当前阶段（parsing diff / running review / finalizing）。

**Step 5：拿结果**

```bash
/codex:result
```

输出 Codex 的完整 review（verbatim），Claude Code 不改一字。

**Step 6：steerable 挑战 review**

```bash
/codex:adversarial-review --base main challenge the chosen retry design
```

针对 retry 逻辑做专项挑战——"what if rate limit is bursty rather than steady?"

**Step 7：派任务**

```bash
/codex:rescue --background investigate why the integration test started flaking after the cache refactor
```

Codex 在后台跑调查，Claude Code 主对话不阻塞。

**Step 8：取消 / 接管**

```bash
/codex:cancel              # 取消某 task
/codex:transfer            # 接管 Codex 跑出来的会话上下文
```

---

## 与同类项目的横向对照

| 维度 | codex-plugin-cc | claude-code-templates MCP | 直接用 Codex CLI |
|---|---|---|---|
| 形态 | Claude Code 插件（marketplace + install） | npm CLI 装 MCP | 独立 CLI |
| Review 触发 | `/codex:review` / `/codex:adversarial-review` | 自己写 slash command | `codex review` 直接跑 |
| 后台任务 | ✅ `/codex:status` / `/codex:result` / `/codex:cancel` | 自己实现 | `codex review &` + 手动管理 |
| Steerable focus | ✅ adversarial-review 接受额外文本 | 自己实现 | ❌ |
| 接管会话 | ✅ `/codex:transfer` | 自己实现 | ❌ |
| 多模型切换 | `--model gpt-5.4-mini / spark` | 看 MCP server 配置 | `codex --model` |
| Claude Code 集成深度 | 高（用 `Bash` + `run_in_background` + `AskUserQuestion`） | 中（靠 MCP tool） | 无 |
| Stars | 28.9k | n/a（n/a 含在 Claude Code Templates 总量） | n/a |
| License | Apache-2.0 | MIT（Claude Code Templates） | Apache-2.0（Codex CLI） |
| 维护方 | OpenAI 官方 | Daniel Avila（社区） | OpenAI 官方 |

这张表想表达一件事：**codex-plugin-cc 是少数同时把"review / rescue / transfer / status / result / cancel"六个工作流封装成 slash command，并由 OpenAI 自己维护的 Claude Code 插件**。它的工程深度（steerable focus + 接管会话 + 后台任务状态机）不是 MCP + 通用 CLI 能简单复刻的。

---

## 适用边界

**推荐使用**：

- 已经在用 Claude Code 写代码、想给 review 加一个"换 Codex 角度看"的视角
- 团队内对 review 流程有要求、希望 review 是异步、可追踪、可取消
- 想要在不离开 Claude Code 的前提下，派长跑任务（bug 调查、regression 排查）给 Codex 后台
- 想要用更便宜的模型（`gpt-5.4-mini` / `spark`）做第一轮排查，确认方向后再用 Claude Code 主力模型修复
- 已经在用 Codex CLI，想复用登录态 + 已有 review 配置

**不推荐使用**：

- 已经在用 Claude Code 默认 review / 不想再多一个 slash command → 切换收益评估
- 强依赖 Claude Code 内置 subagent、不愿意让 Codex 介入 → 跳过
- 没有 Codex 订阅 / API key → `/codex:setup` 会卡在 login
- 想做"既能 review 又能自动修"的工作流 → `/codex:review` 是 read-only，要修代码走 `/codex:rescue`
- Node.js < 18.18 → 装 `@openai/codex` 会失败

---

## 决策建议

按工作流现状选：

1. **Claude Code 重度用户 + 偶尔想换模型看代码** → 直接装插件，从 `/codex:review --background` 开始
2. **团队有严格 review 流程** → 用 `--background` + `/codex:status` 做异步 review 队列
3. **长跑 bug 调查 / regression 排查** → 用 `/codex:rescue --background` + `/codex:transfer` 接管
4. **多模型偏好、想用便宜模型先排查** → `/codex:rescue --model gpt-5.4-mini --effort medium` + `/codex:rescue --model spark`
5. **已经是 Codex CLI 重度用户** → 装插件复用登录态 + 让 Claude Code 也能 trigger 同一套 Codex
6. **完全不用 Claude Code** → 直接用 Codex CLI，无需装此插件

---

## 阅读路径

按需读：

- **只想上手**：README + `/codex:setup` + `/codex:review --background`
- **想理解 review 的核心约束**：`plugins/codex/commands/review.md`（前 30 行必读）
- **想用 steerable review**：`plugins/codex/commands/adversarial-review.md`
- **想派任务**：`plugins/codex/commands/rescue.md` + `plugins/codex/agents/codex-rescue.md`
- **想接管会话**：`plugins/codex/commands/transfer.md`
- **想看桥接脚本**：`plugins/codex/scripts/codex-companion.mjs`
- **想看 marketplace 元数据**：`.claude-plugin/marketplace.json`

---

## 边界声明

本文基于 `openai/codex-plugin-cc` 仓库 README（2026-07-16 抓取）、`plugins/codex/commands/review.md`、`plugins/codex/commands/rescue.md`、`.claude-plugin/marketplace.json`、GitHub API 仓库元数据（28.9k stars、1.8k forks、JavaScript 主语言、Apache-2.0 license）。仓库处于活跃迭代期，slash command 列表（review / adversarial-review / rescue / transfer / status / result / cancel / setup）与 `--base` / `--background` / `--wait` / `--resume` / `--fresh` 等 flag 语义可能在未来版本变化；`@openai/codex` 自身版本与模型可用性会影响插件能力。具体行为以 `plugins/codex/commands/<name>.md` 与 `codex --help` 为准。

codex-plugin-cc 是少数同时把"review + 派任务 + 接管 + 后台任务管理"塞进同一个 Claude Code 插件的开源项目，且由 OpenAI 官方维护；如果你的工作流强依赖某个 MCP 的特定版本，需要关注 `@openai/codex` 升级时是否同步更新插件。
