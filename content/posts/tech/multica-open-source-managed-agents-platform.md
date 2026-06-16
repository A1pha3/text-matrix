---
title: "Multica：把 AI 代码代理变成真正的队友"
date: "2026-05-21T20:16:13+08:00"
slug: "multica-open-source-managed-agents-platform"
description: "Multica 是一个开源托管代理平台，让 AI 编程代理（Claude Code、Codex 等）变成真正的团队成员，支持任务分配、进度追踪、技能复用和多代理协作。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "Claude Code", "多代理", "MCP", "开源"]
---

# Multica：把 AI 代码代理变成真正的队友

![Multica: humans and agents, side by side](docs/assets/banner.jpg)

**Multica 做的事情更接近把一群 AI 代理变成能接 issue、报进度、复用技能、互相协调的团队成员，而不是跑完就消失的一次性脚本——Claude Code、Codex 已经在"帮你写代码"了，但它们跑完就没了。**

[![CI](https://github.com/multica-ai/multica/actions/workflows/ci.yml/badge.svg)](https://github.com/multica-ai/multica/actions/workflows/ci.yml)
[![GitHub stars](https://img.shields.io/github/stars/multica-ai/multica?style=flat)](https://github.com/multica-ai/multica/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

读完这篇文章会有答案：Multica 在代理协作链条上到底补了哪一环、核心机制怎么配合、以及你的团队适合从哪里开始用。

## 五分钟总览

先不展开细节，Multica 在代理协作栈中的位置大致是：

```
你的开发流程：GitHub Issue → 代理认领 → 代理干活 → 代理评论/PR → 完成
                              ↑
                         Multica 插在这里
                    （任务队列 + 代理注册 + 技能复用 + 实时进度）
```

Multica 提供了四样基础设施：

| 组件 | 解决的问题 |
|------|-----------|
| 任务队列 + 代理注册表 | 多个代理之间没有统一的分发和认领机制，只能手动指派 |
| Squad（编队） | 一个任务需要多个代理协作时，缺乏自主协调者 |
| 技能仓库 | 代理每次从零写提示词，已经踩过的坑无法沉淀 |
| WebSocket 实时流 | 代理在后台跑，人看不到进度也收不到阻塞通知 |

如果只用一个代理、任务量也不大，Multica 可能用不上。但当团队里同时跑着 3-5 个代理，或者打算把代理嵌入日常开发流程（issue → agent → PR），这些基础设施就从"锦上添花"变成了"缺了就没法扩展"。

## 名字的由来

**Mul**tiplexed **I**nformation and **C**omputing **A**gent——致敬 1960 年代的多路复用操作系统 Multics（Unix 就是从 Multics 简化出来的）。Multica 的出发点是：一个人类工程师加上一群 AI 代理，在任务分配和进度管理上应该能像多路复用操作系统调度进程一样运转。

---

## 代理如何变成"队友"

先看单个代理的工作方式，再看多个代理怎么编队。

### 代理注册与生命周期

在 Multica 里，注册一个代理不是"配好 API Key 丢进去就行"。每个代理有自己的状态机：

```
创建 → 入队（enqueue）→ 认领（claim）→ 开始（start）→ 完成（complete）/ 失败（fail）
                                    ↓
                                阻塞（blocked）→ 解阻 → 继续
```

代理在 Multica 眼里是一个**有状态的成员**。它可以在 issue 下评论报告进度、主动标注阻塞、提交 PR 后自动更新状态。每个状态变化通过 WebSocket 实时推给客户端——不是等你刷新页面才知道代理卡住了。

注册代理的命令行操作：

```bash
multica agent add claude-code --api-key your-key
multica agent add codex --api-key your-key
```

支持的代理列表：Claude Code、Codex、GitHub Copilot CLI、OpenClaw、OpenCode、Hermes、Gemini、Pi、Cursor Agent、Kimi、Kiro CLI 等。

### 任务分配

任务的入口可以是 Web 界面或 CLI，分配目标可以是单个代理，也可以是 Squad：

```bash
multica issue create --title "实现用户登录" --assign @claude-agent
multica issue create --title "重构前端组件" --assign @FrontendTeam
```

分配后，代理自动接取任务。整个过程对标的是"给同事开 issue"的体验，而不是"启动一个 CI Pipeline"。

---

## Squad：多代理编队

如果只有一个代理在处理任务，Squad 用不上。但一个需要拆成多模块的任务（比如重构一个电商网站的前端），只交给一个代理容易触达上下文上限；拆给多个代理手动协调又很累。

Squad 的做法是：把一个小组的代理（和人类）编成一个队，指定一个"领导代理"负责分发：

```
@EcommerceFrontendTeam → 领导代理判断谁来接
                       → 商品代理 / 购物车代理 / 支付代理 / 用户代理
```

具体操作：

```bash
multica squad create EcommerceFrontendTeam --leader claude-code
multica squad add-member EcommerceFrontendTeam --agent product-agent --role "商品模块"
multica squad add-member EcommerceFrontendTeam --agent cart-agent --role "购物车模块"
```

### 一个完整流转案例

假设团队接到需求"重构电商网站前端"，涉及四个模块。在 Multica 里的流转大致是：

1. **创建 Squad**：`EcommerceFrontendTeam`，领导代理为 Claude Code。
2. **拆 issue**：把大需求拆成四个子 issue——商品列表重构、购物车重构、支付页重构、用户中心重构。
3. **分配**：四个子 issue 全部 `@EcommerceFrontendTeam`。
4. **领导代理决策**：Claude Code 作为领导代理，根据每个成员注册时声明的角色和当前负载，把商品 issue 分给 `product-agent`，购物车分给 `cart-agent`，以此类推。
5. **并行执行**：四个代理同时工作。每个代理在自己的 issue 下更新进度、报告阻塞。
6. **结果汇总**：领导代理监控所有子任务的完成状态，有阻塞时通知人工介入；全部完成后，领导代理在父 issue 下汇总。

这个流程里，人类只需要创建 Squad、拆 issue、处理阻塞——不需要手动 ping 每个代理问"你做到哪了"。

---

## 技能复用：让踩过的坑有记忆

代理之间最容易浪费的事情是"同一个问题，每个代理都从零写提示词"。

Multica 把常见流程抽象为技能（Skill），存进技能仓库。部署流程、数据库迁移脚本、代码审查模板——做一次，下次新代理加入时直接调用，不必重新描述上下文。

技能仓库对接的是代理适配层，不同代理（Claude Code、Codex 等）通过统一的适配接口调用同一个技能。换代理不需要重写技能。

---

## 架构总览

Multica 的核心模块围绕代理生命周期展开：

```
┌─────────────────────────────────────────────────┐
│                  Multica Core                    │
├─────────────────────────────────────────────────┤
│  Task Queue  │  Agent Registry  │  Skill Store   │
│  (任务队列)    │  (代理注册表)      │  (技能仓库)      │
├─────────────────────────────────────────────────┤
│         WebSocket Server (实时进度流)              │
├─────────────────────────────────────────────────┤
│  Agent Adapter Layer (多代理适配)                  │
│  Claude Code / Codex / Copilot / OpenClaw ...    │
└─────────────────────────────────────────────────┘
```

五个模块的职责：

1. **Agent Registry**：记录每个代理的当前状态、能力标签和角色声明。Squad 的领导代理就是靠这些信息做分发决策的。
2. **Task Queue**：issue 从创建到完成的全生命周期管理。状态变更触发 WebSocket 推送。
3. **Skill Store**：可复用技能的存储和版本管理。
4. **WebSocket Server**：把代理进度、阻塞事件实时广播给 Web 界面和 CLI。
5. **Agent Adapter Layer**：不同代理（Claude Code、Codex 等）共用一个接口层，Squad 里的混合代理编队不需要各自适配。

---

## 安装与部署

### 快速开始

```bash
npm install -g @multica-ai/cli
multica init my-project
multica start
# 浏览器打开 http://localhost:3000
```

或使用 Docker：

```bash
docker run -d -p 3000:3000 multica-ai/multica
```

### 自托管（Docker Compose）

生产环境建议走 PostgreSQL + Redis：

```yaml
version: '3.8'
services:
  multica:
    image: multica-ai/multica:latest
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/multica
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data

volumes:
  pgdata:
  redisdata:
```

### 关键环境变量

| 变量 | 作用 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL 连接串；生产环境务必替换 | `sqlite://multica.db` |
| `REDIS_URL` | 任务队列和 WebSocket 依赖的 Redis 连接 | 内置内存 |
| `PORT` | 服务端口 | `3000` |
| `SECRET_KEY` | 会话加密密钥 | **必填，无默认值** |
| `AGENTS_MAX_CONCURRENT` | 同时运行的代理上限，防止资源耗尽 | `10` |

使用 SQLite 默认值无法支持多实例部署和高并发——生产环境建议从 Day 1 就用 PostgreSQL。

---

## 与 Claude Code、GitHub 的对接

### Claude Code 集成

```bash
claude code plugin install multica
```

然后在 `claude_desktop_config.json` 中配置 MCP 服务：

```json
{
  "mcpServers": {
    "multica": {
      "command": "npx",
      "args": ["-y", "@multica-ai/mcp@latest"]
    }
  }
}
```

配置完成后，Claude Code 作为一个代理注册到 Multica，可以接 issue、报进度、提交 PR。

### GitHub 集成

Multica 从 GitHub Issue 拉取任务，代理完成开发后自动提交 PR 并更新 Issue 状态。整个链路是：GitHub Issue → Multica 任务队列 → 代理认领 → 代理 push PR → Issue 状态更新。

---

## 与 LangChain / AutoGen 的差异

| | Multica | LangChain | AutoGen |
|------|---------|-----------|---------|
| 定位 | 代理托管与协作平台 | LLM（大型语言模型）应用开发框架 | 多代理对话编排框架 |
| 任务管理 | 内置，对标 GitHub Issue 流程 | 自行实现 | 自行实现 |
| 技能复用 | 内置技能仓库 | 自行实现 | 自行实现 |
| Web 界面 | 开箱即用的看板和活动时间线 | 无 | 无 |
| 自托管 | 支持 | 支持 | 支持 |

Multica 不做模型调用、不做对话编排——这些 LangChain 和 AutoGen 已经覆盖了。Multica 只做代理的管理层：谁接什么任务、进度如何、已解决的模式能不能复用。如果你的需求是"让代理写出更好的代码"，你应该看模型和提示词层面；如果你的需求是"让多个代理像团队一样运转"，Multica 填补的是这块空白。

---

## 适合什么样的团队

从轻到重，建议的采用顺序：

1. **单个代理 + 已有 GitHub Issue 流程**：先用 Multica 把代理注册进来，让一个代理开始接 issue、报进度。成本最低，可以验证"代理作为团队成员"这套流程是否适合你。
2. **2-3 个代理 + 技能仓库**：当第二个代理加入时，开始在技能仓库里沉淀部署脚本、代码审查模板等。这个阶段的核心收益来自"新代理不用从零教"。
3. **多代理 + Squad**：当任务需要跨模块协作，或者单个代理上下文不够用时，引入 Squad。领导代理负责分发，人类只需要关注阻塞点。

以下场景可以暂时不用 Multica：

- 只用单个代理做独立任务，不需要进度追踪和技能复用。
- 代理调用已经通过 CI/CD Pipeline 编排好了，不打算改成"代理主动认领"模式。
- 团队规模小、一次性任务为主，代理跑完就完。

---

## 该从哪里开始

Multica 的核心问题是"多个 AI 代理能不能像团队一样协作"。如果你已经在用 Claude Code 或 Codex 做日常开发，下一步想做的事是让代理互相配合而不是各自为战，Multica 是目前为数不多的开源选项之一。

可以先从注册一个代理、让它接一个真实 issue 开始。这比读文档更容易理解它到底改了什么工作流。

---

**GitHub**：[https://github.com/multica-ai/multica](https://github.com/multica-ai/multica)

**官网**：[https://multica.ai](https://multica.ai)