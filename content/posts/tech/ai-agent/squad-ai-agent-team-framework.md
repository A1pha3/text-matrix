---
title: "Squad：把 GitHub Copilot 变成一个 AI 开发团队"
slug: "squad-ai-agent-team-framework"
aliases:
  - /posts/tech/squad-ai-agent-team-framework/
date: "2026-03-31T12:50:00+08:00"
categories: ["技术笔记"]
tags: ["Squad", "AI智能体", "GitHub Copilot", "多智能体", "协作框架", "团队开发"]
description: "Squad 把 GitHub Copilot 的 Agent 模式扩展成一支多角色 AI 开发团队（1.5k Stars, MIT）。本文拆解它的多智能体协作、持久化知识和 SDK-First 团队定义机制，覆盖 CLI 命令、架构分析和实际使用场景。"
---

# Squad：把 GitHub Copilot 变成一个 AI 开发团队

---

## 学习目标

读完本文，你会搞清楚三件事：Squad 怎么把 Copilot Agent 扩展成一支多角色团队，这支团队怎么通过文件系统记住项目上下文和决策，以及你自己怎么在项目里搭一套并把它用起来。具体覆盖多智能体协作架构、GitHub Copilot Agent 模式集成、CLI 命令、决策日志与知识积累机制、交互式 Shell、SDK-First 团队定义和插件扩展。

---

## 2. 项目概述

### 2.1 什么是 Squad

Squad（官方仓库：[bradygaster/squad](https://github.com/bradygaster/squad)）是一个**AI 智能体团队协作框架**，通过 GitHub Copilot 的 Agent 模式，让你拥有一个**完整的 AI 开发团队**——包括前端、后端、测试、架构师等多个专业角色。

Squad 的做法不是把 Copilot 当成一个聊天窗口来用，而是在项目里部署一支带角色分工的 AI 团队——这条团队的信息存在 `.squad/` 目录下，跨会话保留，下次打开项目时它还记得之前做过什么决策、写过什么代码。

### 2.2 核心数据

```yaml

### 2.3 版本与发布

| 版本 | 状态 | 说明 |
|------|------|------|
| **v1.x** | 开发中 | 主分支为 `dev`，最新功能在 `dev` |
| **v0.x** | 稳定版 | 可用于生产环境 |

最新提交：`eb69444`（2026-03-30）- feat(ci): CI hardening phase 2

### 2.4 为什么需要 Squad

用 GitHub Copilot Chat 做大型项目时，三个问题会反复出现。一是上下文窗口装不下整个项目，每次只能看到当前文件附近的内容。二是上一轮会话里讨论过的决策，关掉 IDE 就丢了，下次要重新对齐。三是 Copilot 只有一个角色视角，遇到横跨前端、后端和测试的任务，你得自己来回切换。

Squad 用两条机制回应了这些问题：多智能体分工和基于文件系统的持久化。前者把前端、后端、测试、架构师拆成独立的智能体，各自维护自己的工作区；后者把团队配置、路由规则、决策记录全都落盘到 `.squad/` 目录。下次打开项目时，团队状态和之前的决策都在，不需要重新初始化。

---

## §3 原理分析

Squad 内部可以拆成三条主线来看：多智能体协作（谁做什么、任务怎么路由）、持久化知识（`.squad/` 目录里存了什么、跨会话怎么恢复）、以及 Copilot Agent 集成（模型怎么拿到文件系统权限并执行多步操作）。下面逐一展开。

### 3.1 多智能体协作原理

Squad 的核心是**协调式多智能体系统**（Coordinated Multi-Agent System）。每个智能体有明确的专业角色，智能体之间通过**消息路由**和**决策日志**进行协作。

**智能体角色分工**

| 角色 | 职责 | 典型任务 |
|------|------|---------|
| **Frontend Dev** | 前端开发 | React 组件、样式、性能优化 |
| **Backend Dev** | 后端开发 | API 设计、数据库、业务逻辑 |
| **Tester** | 测试工程 | 单元测试、集成测试、E2E |
| **Architect** | 架构师 | 技术选型、性能规划、安全审查 |
| **Lead** | 项目负责人 | 任务分配、进度跟踪、代码审查 |

**智能体间的消息路由**

```text

协调者（Coordinator）接收用户消息，分析任务类型，将任务路由到最合适的智能体，必要时协调多个智能体协作。

### 3.2 持久化知识机制

Squad 将智能体的"记忆"存储在项目文件中，实现跨会话知识积累：

**核心文件结构**

```text

**决策日志（decisions.md）**

每次重要决策都会被记录：

```markdown
# Squad 决策日志

## 2026-03-30 架构决策

### AD-001: 选择 PostgreSQL 作为主数据库
**日期**: 2026-03-30
**提出者**: Architect
**决策**: 采用 PostgreSQL 而非 MongoDB
**理由**: 
- 交易数据需要 ACID 保证
- 团队对 SQL 更熟悉
**影响**: 后端 API 需要适配 Prisma ORM
```texttypescript
// team.ts - Squad 团队定义
import { Squad, Agent, Skill } from '@bradygaster/squad-sdk';

const frontend = new Agent({
  name: 'frontend-dev',
  role: 'Frontend Developer',
  skills: [
    Skill.react(),
    Skill.typescript(),
    Skill.tailwindcss(),
  ],
  instructions: '你专注于创建美观、响应式的 React 组件。'
});

const backend = new Agent({
  name: 'backend-dev',
  role: 'Backend Developer',
  skills: [
    Skill.nodejs(),
    Skill.postgresql(),
    Skill.prisma(),
  ],
  instructions: '你专注于构建高性能、安全的 API。'
});

const team = new Squad({
  name: 'full-stack-team',
  agents: [frontend, backend],
  coordinator: 'auto',  // 自动选择协调者
});

export default team;
```text
┌─────────────────────────────────────────────────────────────┐
│                         Squad CLI                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │   init   │  │  status  │  │  copilot │  │  shell   │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
└───────┼──────────────┼──────────────┼──────────────┼──────────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                    .squad/ (本地文件系统)                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│  │ team.md │  │routing │  │decisions│  │ skills/ │      │
│  │         │  │   .md   │  │   .md   │  │         │      │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘      │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                   GitHub Copilot Agent                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│  │Frontend │  │Backend  │  │ Tester  │  │Architect│      │
│  │ Agent   │  │ Agent   │  │  Agent  │  │  Agent  │      │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘      │
└─────────────────────────────────────────────────────────────┘
```textmarkdown
# Squad 路由规则

## 任务类型 → 智能体映射

### 代码修改任务
- **前端组件** → Frontend Dev
- **API 实现** → Backend Dev
- **数据库修改** → Backend Dev
- **测试用例** → Tester

### 架构任务
- **技术选型** → Architect
- **性能审查** → Architect
- **安全审查** → Architect

### 协作任务
- **代码审查** → Lead + 相关智能体
- **任务分配** → Lead
- **进度报告** → Lead
```textmarkdown
# 协作策略

## 决策机制
- **日常决策**: 各智能体自主决定
- **重要决策**: 需要 Lead 批准并记录到 decisions.md
- **冲突解决**: Architect 作为最终仲裁者

## 并行执行
- 独立任务应并行执行以提高效率
- 需要共享资源的任务应串行执行

## 知识共享
- 每次会话结束后更新 skills/
- 重要发现记录到 decisions.md
- 通用模式记录到 identity/patterns.md
```textbash
# 1. 创建项目目录
mkdir my-project && cd my-project
git init

# 2. 安装 Squad CLI
npm install -g @bradygaster/squad-cli squad

# 3. GitHub 认证
gh auth login

# 4. 初始化 Squad 团队
squad init

# 5. 启动 Copilot Agent
copilot --agent squad --yolo
```textbash
$ squad init

✓ 创建 .squad/ 目录结构
✓ 初始化 team.md
✓ 设置默认路由规则
✓ 配置 casting/roster.md
✓ 初始化 decisions.md
✓ 完成！运行 'squad status' 查看团队
```textbash
$ squad shell

🤖 Squad Shell v1.0.0
📁 项目: my-project
👥 团队: 4 名成员 (Frontend, Backend, Tester, Lead)

squad > /status
┌─────────────────────────────┐
│  团队状态                     │
├─────────────────────────────┤
│  Frontend: ✅ 就绪            │
│  Backend:  ✅ 就绪            │
│  Tester:   ✅ 就绪            │
│  Lead:     ✅ 就绪            │
└─────────────────────────────┘

squad > 实现一个用户登录 API
✓ 已路由到 Backend Dev
✓ Backend Dev 正在实现...
✓ 完成！决策已记录到 decisions.md
```textbash
# 启动自动分类
squad triage --watch

# 手动分类
squad triage classify --issue 123
```textyaml
# .squad/triage-rules.yaml
rules:
  - pattern: "前端|UI|组件|样式"
    assignee: frontend-dev
    priority: medium
    
  - pattern: "后端|API|数据库"
    assignee: backend-dev
    priority: high
    
  - pattern: "测试|覆盖|bug"
    assignee: tester
    priority: high
    
  - pattern: "架构|性能|安全"
    assignee: architect
    priority: medium
```textbash
squad copilot add frontend \
  --name "frontend-dev" \
  --role "React/TypeScript 专家" \
  --instructions "你专注于 React 组件、样式优化和用户体验改进"
```textbash
$ squad status

👥 Squad 团队配置

┌────────────────┬──────────────────┬────────────┐
│ 智能体          │ 角色              │ 状态       │
├────────────────┼──────────────────┼────────────┤
│ frontend-dev   │ Frontend Dev     │ ✅ 活跃    │
│ backend-dev    │ Backend Dev      │ ✅ 活跃    │
│ tester         │ Tester           │ ✅ 活跃    │
│ architect      │ Architect        │ ✅ 活跃    │
└────────────────┴──────────────────┴────────────┘
```textbash
# 手动压缩
squad skills compress

# 查看技能列表
squad skills list
```textbash
# 查看上下文使用情况
squad nap --stats

# 清理不必要的上下文
squad nap --aggressive
```textbash
# 连接到远程团队
squad link https://github.com/org/remote-squad

# 同步知识
squad link --sync
```textbash
# 导出
squad export --output team-config.zip

# 导入
squad import team-config.zip
```textbash
npm install -g @bradygaster/squad-cli squad

# 验证安装
squad --version
# Squad CLI v1.0.0
```textbash
# 初始化项目
npx @bradygaster/squad-cli init my-project
cd my-project

# 启动 shell
npx squad shell
```textbash
# 拉取镜像
docker pull bradygaster/squad:latest

# 运行
docker run -it --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  bradygaster/squad:latest squad shell
```textbash
# 交互式登录
gh auth login

# 验证登录状态
gh auth status
# ✓ Authenticated as Brady Gaster
#   Token scope: repo, copilot, read:org
```textmarkdown
# .squad/team.md

## 团队信息
name: my-team
version: 1.0.0
created: 2026-03-30

## 成员列表
members:
  - name: frontend-dev
    role: Frontend Developer
    agent: copilot
    skills:
      - React
      - TypeScript
      - TailwindCSS
    status: active

  - name: backend-dev
    role: Backend Developer
    agent: copilot
    skills:
      - Node.js
      - PostgreSQL
      - Prisma
    status: active
```textbash
# 1. 启动团队
cd my-project
squad shell

# 2. 分配任务
squad > 帮我实现用户注册功能

# 3. 查看状态
squad > /status

# 4. 退出
squad > /quit
```textbash
# 1. 启动 Issue 分类
squad triage --watch

# 2. 查看分配的任务
squad status --issues

# 3. 解决 Issue
squad shell
squad > 修复 #123 登录问题
```textmarkdown
# .squad/agents/custom-agent/agent.md

## 智能体信息
name: custom-agent
role: Custom Developer
created: 2026-03-30

## 专业领域
- Go 语言开发
- Kubernetes 运维
- DevOps 自动化

## 工作目录
/squad/agents/custom-agent/workspace

## 历史贡献
### 2026-03-30
- 初始创建
- 定义专业领域为 Go + K8s
```texttypescript
// plugins/my-plugin/index.ts
import { SquadPlugin } from '@bradygaster/squad-sdk';

export default class MyPlugin implements SquadPlugin {
  name = 'my-plugin';
  version = '1.0.0';

  onInit(squad: Squad) {
    // 注册自定义命令
    squad.registerCommand('my-command', this.handleMyCommand);
  }

  async handleMyCommand(args: string[]) {
    console.log('My custom command:', args);
  }
}
```textbash
# 在 plugins 目录创建插件
mkdir -p .squad/plugins/my-plugin
cd .squad/plugins/my-plugin
npm init -y
# 添加插件代码...
```textmarkdown
## 自定义路由规则

### Go 相关任务
当任务描述包含以下关键词时：
- "golang"
- "go 服务"
- "grpc"

路由到: custom-agent (Go 专家)

### K8s 相关任务
当任务描述包含以下关键词时：
- "kubernetes"
- "k8s"
- "部署"

路由到: custom-agent (K8s 专家)
```textyaml
name: Squad CI

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main]

jobs:
  squad-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          
      - name: Install Squad
        run: npm install -g @bradygaster/squad-cli
        
      - name: Run Squad Tests
        run: |
          squad doctor
          squad copilot add tester --name "ci-tester"
          copilot --agent squad -- non-interactive-test
```textmarkdown
## Good Example
skills:
  - React 18 (5年经验)
  - TypeScript (strict mode)
  - TailwindCSS 3.x
  - GraphQL

## Bad Example  
skills:
  - 前端
  - 会写代码
```textbash
# 每周压缩一次
squad skills compress --weekly

# 保留最近 10 次会话的完整记录
squad skills prune --keep 10

# 查看压缩率
squad skills stats
```textbash
# 1. 检查认证状态
gh auth status

# 2. 检查 Squad 设置
squad doctor

# 3. 重启 Shell
squad shell --fresh
```textbash
# 查看当前路由规则
cat .squad/routing.md

# 测试路由
squad debug route "实现一个登录功能"
```

---

## §9 常见问题

### Q1：Squad 和 GitHub Copilot Chat 有什么区别？

| 维度 | Copilot Chat | Squad |
|------|-------------|-------|
| 智能体数量 | 单一 | 多团队 |
| 跨会话记忆 | 无 | 有（文件系统） |
| 决策日志 | 无 | 有 |
| 专业分工 | 无 | 有（角色分工） |
| 适用场景 | 快速问答 | 复杂项目 |

### Q2：需要多少 GitHub Copilot 订阅？

Squad 本身免费，但需要 **GitHub Copilot** 订阅才能使用 Agent 模式。Copilot Agent 功能通常包含在 Copilot Business 或 Copilot Enterprise 订阅中。

### Q3：可以离线使用 Squad 吗？

部分功能可以离线使用：

- ✅ 读取本地 `.squad/` 文件
- ✅ 查看决策日志
- ❌ Copilot Agent（需要网络）
- ❌ GitHub Issues 同步

### Q4：如何贡献插件？

1. Fork [squad](https://github.com/bradygaster/squad)
2. 在 `plugins/` 目录创建插件
3. 添加 `package.json` 和入口文件
4. 提交 Pull Request

### Q5：支持哪些 IDE？

Squad CLI 跨平台，Copilot Agent 支持：

- ✅ VS Code (原生)
- ✅ Visual Studio
- ✅ JetBrains IDEs (通过 Copilot 插件)
- ✅ Neovim (通过 Copilot.vim)
- ✅ 命令行 (copilot CLI)

### Q6：团队知识是否安全？

是的，Squad 的知识存储在本地 `.squad/` 目录：

- **默认**: 仅本地存储
- **可选**: 通过 `squad link` 连接到远程团队
- **敏感信息**: 建议添加到 `.gitignore`

---

## §10 总结

Squad 把 GitHub Copilot 从单次问答工具改造成了一支能跨会话记住项目状态的 AI 开发团队。

**几条关键设计**

- **多智能体分工**：Frontend、Backend、Tester、Architect 各自维护独立工作区，通过 Coordinator 路由任务。
- **持久化知识**：团队配置、路由规则、决策记录全部存为 `.squad/` 目录下的 Markdown 文件，跨会话保留。
- **决策日志**：`decisions.md` 按时间线记录重要技术决策、理由和影响范围。
- **GitHub 原生集成**：直接跑在 Copilot Agent 模式上，复用 GitHub 认证和 Copilot 订阅。
- **可扩展**：支持 TypeScript SDK 定义自定义智能体、插件和路由规则。

**什么时候值得一试**

- 项目大到单次 Copilot Chat 上下文装不下时，多智能体分工能把任务拆到各自的工作区。
- 项目周期长、需要持续维护时，`.squad/` 里的决策日志能减少每次重新对齐的成本。
- 你的项目横跨多个技术栈，想让 AI 也按这个边界分工——比如前端一个 Agent、后端一个 Agent，而不是一个助手来回切上下文。

如果项目还在原型阶段、代码量不大，或者团队只有一个人且不需要角色分工，先继续用 Copilot Chat 可能是更轻量的选择。Squad 的价值在项目复杂度和团队规模上升之后才会体现出来。

**链接资源**

- GitHub 仓库：https://github.com/bradygaster/squad
- 官方文档：https://github.com/bradygaster/squad#readme
- 插件市场：`squad plugin marketplace`
- 讨论区：https://github.com/bradygaster/squad/discussions

---

*🦞 文档版本 1.0 | 撰写日期：2026-03-31 | 基于仓库 commit eb69444 (2026-03-30)*