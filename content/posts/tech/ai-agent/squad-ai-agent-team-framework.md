---
title: "Squad：AI 智能体团队协作框架完全指南"
slug: "squad-ai-agent-team-framework"
aliases:
  - /posts/tech/squad-ai-agent-team-framework/
date: "2026-03-31T12:50:00+08:00"
categories: ["技术笔记"]
tags: ["Squad", "AI智能体", "GitHub Copilot", "多智能体", "协作框架", "团队开发"]
description: "全面解析 Squad：AI 智能体团队协作框架（1.5k Stars，MIT 许可证）。通过 GitHub Copilot Agent 模式创建 Frontend + Backend + Tester + Architect 多角色 AI 团队。支持持久化知识积累、决策日志记录、SDK-First 团队定义。从入门到精通，包含架构分析、CLI 命令详解和使用说明。"
---

# Squad：AI 智能体团队协作框架完全指南

> 预计阅读时间：30分钟 | 难度：⭐⭐⭐⭐

---

## 学习目标

学完本文档后，你将能够：

- 理解 Squad 的核心理念与价值主张
- 掌握 Squad 的多智能体协作架构
- 了解 GitHub Copilot Agent 模式的集成方式
- 学会在不同项目中初始化和配置 Squad 团队
- 掌握 15 个 CLI 命令的用法
- 理解团队决策日志和知识积累机制
- 学会在交互式 Shell 中与智能体团队协作
- 掌握 SDK-First 模式用 TypeScript 定义团队
- 了解 Squad 的扩展机制和插件系统

---

## §2 项目概述

### 2.1 什么是 Squad

Squad（官方仓库：[bradygaster/squad](https://github.com/bradygaster/squad)）是一个**AI 智能体团队协作框架**，通过 GitHub Copilot 的 Agent 模式，让你拥有一个**完整的 AI 开发团队**——包括前端、后端、测试、架构师等多个专业角色。

Squad 的核心理念：**一个命令，立即拥有一个与你代码共同成长的 AI 团队**。不同于传统 Copilot 的单一助手，Squad 创建的是一支能够跨会话持久化、在项目中积累知识、持续学习和改进的智能体团队。

### 2.2 核心数据

```
Stars:     1,532（1.5k）
Forks:     200
贡献者:    11 人
提交:     1,362 次
分支:     36 branches
标签:     38 tags
许可证:   MIT
主要语言: TypeScript 58.5%, JavaScript 34.2%
```

### 2.3 版本与发布

| 版本 | 状态 | 说明 |
|------|------|------|
| **v1.x** | 开发中 | 主分支为 `dev`，最新功能在 `dev` |
| **v0.x** | 稳定版 | 可用于生产环境 |

最新提交：`eb69444`（2026-03-30）- feat(ci): CI hardening phase 2

### 2.4 为什么需要 Squad

**传统 AI 助手的局限性**

单一 AI 助手（如 GitHub Copilot Chat）虽然强大，但存在以下问题：

- **上下文窗口限制**：大型项目无法一次性理解全部上下文
- **知识无法积累**：每次会话都要重新介绍项目背景
- **专业能力单一**：无法同时扮演多个专业角色
- **跨会话丢失**：关闭 IDE 后所有学习和决策都消失

**Squad 的解决方案**

Squad 通过**多智能体团队**和**持久化文件系统**解决了这些问题：

```
传统方式：单一助手 × 无记忆 = 每次重复工作
Squad 方式：专业团队 × 持久化知识 = 持续学习的团队
```

---

## §3 原理分析

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

```
用户消息
    │
    ▼
┌─────────────────┐
│   Coordinator    │  ← 路由智能体
│  (协调者)        │
└────────┬────────┘
         │
    ┌────┴────┬─────────┬─────────┐
    ▼         ▼         ▼         ▼
 Frontend   Backend   Tester   Architect
 (前端)    (后端)    (测试)   (架构)
```

协调者（Coordinator）接收用户消息，分析任务类型，将任务路由到最合适的智能体，必要时协调多个智能体协作。

### 3.2 持久化知识机制

Squad 将智能体的"记忆"存储在项目文件中，实现跨会话知识积累：

**核心文件结构**

```
.squad/
├── team.md              # 团队配置和成员信息
├── routing.md           # 消息路由规则
├── decisions.md          # 团队决策日志
├── casting/             # 团队角色定义
│   ├── roster.md       # 成员列表
│   └── policy.md       # 协作策略
├── agents/             # 各智能体的上下文
│   ├── frontend/       # 前端智能体的工作区
│   ├── backend/        # 后端智能体的工作区
│   ├── tester/        # 测试智能体的工作区
│   └── architect/      # 架构师的工作区
├── skills/             # 技能/知识积累
│   └── compressed/    # 压缩后的技能知识
├── identity/           # 智能体身份
│   ├── current.md     # 当前焦点
│   └── patterns.md    # 通用模式
└── history/            # 历史会话
    └── sessions/       # 过往会话记录
```

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
```

### 3.3 GitHub Copilot Agent 模式

Squad 基于 GitHub Copilot 的 **Agent 模式**实现。Copilot Agent 允许 AI 模型主动执行多步骤任务，而非简单补全代码。

**Agent vs Chat 模式对比**

| 维度 | Chat 模式 | Agent 模式 |
|------|----------|-----------|
| 交互方式 | 问答 | 自主执行 |
| 任务范围 | 单次操作 | 多步骤任务 |
| 工具使用 | 有限 | 完整工具集 |
| Squad 集成 | 不支持 | 原生支持 |

**Copilot Agent 的能力**

- 文件系统操作：读取、创建、修改文件
- Git 操作：提交、分支、合并
- Shell 命令：运行测试、构建项目
- 搜索和导航：理解代码结构

### 3.4 SDK-First 团队定义模式

Squad 支持用 **TypeScript 定义团队**，而非纯 Markdown 配置：

```typescript
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
```

---

## §4 架构分析

### 4.1 系统架构

```
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
```

### 4.2 核心模块

**CLI 模块**

| 模块 | 功能 | 入口命令 |
|------|------|---------|
| **init** | 初始化 Squad | `squad init` |
| **upgrade** | 更新 Squad 文件 | `squad upgrade` |
| **status** | 查看团队状态 | `squad status` |
| **triage** | 自动分类 Issues | `squad triage` |
| **copilot** | 管理 Copilot 代理 | `squad copilot add/remove` |
| **doctor** | 检查设置 | `squad doctor` |
| **link** | 连接远程团队 | `squad link` |
| **shell** | 交互式 Shell | `squad shell` |
| **export/import** | 导入导出 | `squad export/import` |
| **plugin** | 插件市场 | `squad plugin marketplace` |
| **upstream** | 上游管理 | `squad upstream` |
| **nap** | 上下文清理 | `squad nap` |
| **aspire** | Aspire 仪表盘 | `squad aspire` |
| **scrub-emails** | 清理邮箱 | `squad scrub-emails` |

**文件系统模块**

| 模块 | 功能 | 位置 |
|------|------|------|
| **casting** | 团队角色 | `.squad/casting/` |
| **agents** | 智能体上下文 | `.squad/agents/` |
| **skills** | 技能压缩 | `.squad/skills/` |
| **identity** | 身份管理 | `.squad/identity/` |
| **history** | 会话历史 | `.squad/history/` |

### 4.3 路由机制

Squad 的消息路由由 `routing.md` 定义：

```markdown
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
```

### 4.4 协作策略

Squad 的协作策略由 `casting/policy.md` 定义：

```markdown
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
```

---

## §5 功能详解

### 5.1 初始化与配置

**快速开始**

```bash
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
```

**squad init 做了什么**

```bash
$ squad init

✓ 创建 .squad/ 目录结构
✓ 初始化 team.md
✓ 设置默认路由规则
✓ 配置 casting/roster.md
✓ 初始化 decisions.md
✓ 完成！运行 'squad status' 查看团队
```

### 5.2 交互式 Shell

`squad shell` 启动交互式 Shell，支持以下命令：

| 命令 | 功能 |
|------|------|
| `/status` | 显示团队状态 |
| `/history` | 查看会话历史 |
| `/agents` | 列出所有智能体 |
| `/sessions` | 查看会话列表 |
| `/resume` | 恢复历史会话 |
| `/version` | 显示版本 |
| `/clear` | 清除当前会话 |
| `/help` | 显示帮助 |
| `/quit` | 退出 Shell |

**使用示例**

```bash
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
```

### 5.3 自动 Issue 分类

`squad triage` 监听 GitHub Issues，自动分类和分配：

```bash
# 启动自动分类
squad triage --watch

# 手动分类
squad triage classify --issue 123
```

**分类规则**

```yaml
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
```

### 5.4 Copilot 代理管理

**添加前端开发代理**

```bash
squad copilot add frontend \
  --name "frontend-dev" \
  --role "React/TypeScript 专家" \
  --instructions "你专注于 React 组件、样式优化和用户体验改进"
```

**查看当前代理**

```bash
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
```

### 5.5 知识管理

**技能压缩**

Squad 会定期将智能体的学习压缩到 `skills/compressed/`：

```bash
# 手动压缩
squad skills compress

# 查看技能列表
squad skills list
```

**上下文清理（nap）**

```bash
# 查看上下文使用情况
squad nap --stats

# 清理不必要的上下文
squad nap --aggressive
```

### 5.6 团队协作

**连接远程团队**

```bash
# 连接到远程团队
squad link https://github.com/org/remote-squad

# 同步知识
squad link --sync
```

**导出/导入团队配置**

```bash
# 导出
squad export --output team-config.zip

# 导入
squad import team-config.zip
```

---

## §6 使用说明

### 6.1 环境要求

- **Node.js** 18+
- **Git** 2.30+
- **GitHub CLI** (gh) 已认证
- **GitHub Copilot** 订阅
- **npm** 或 **yarn**

### 6.2 安装步骤

**方式一：npm 全局安装（推荐）**

```bash
npm install -g @bradygaster/squad-cli squad

# 验证安装
squad --version
# Squad CLI v1.0.0
```

**方式二：使用 npx**

```bash
# 初始化项目
npx @bradygaster/squad-cli init my-project
cd my-project

# 启动 shell
npx squad shell
```

**方式三：Docker 运行**

```bash
# 拉取镜像
docker pull bradygaster/squad:latest

# 运行
docker run -it --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  bradygaster/squad:latest squad shell
```

### 6.3 GitHub 认证

```bash
# 交互式登录
gh auth login

# 验证登录状态
gh auth status
# ✓ Authenticated as Brady Gaster
#   Token scope: repo, copilot, read:org
```

### 6.4 团队配置

**手动编辑 team.md**

```markdown
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
```

### 6.5 常用工作流

**日常开发**

```bash
# 1. 启动团队
cd my-project
squad shell

# 2. 分配任务
squad > 帮我实现用户注册功能

# 3. 查看状态
squad > /status

# 4. 退出
squad > /quit
```

**处理 Issue**

```bash
# 1. 启动 Issue 分类
squad triage --watch

# 2. 查看分配的任务
squad status --issues

# 3. 解决 Issue
squad shell
squad > 修复 #123 登录问题
```

---

## §7 开发扩展

### 7.1 创建自定义智能体

创建 `.squad/agents/custom-agent/` 目录并添加配置文件：

```markdown
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
```

### 7.2 插件开发

Squad 支持插件扩展。创建插件：

```typescript
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
```

**发布插件**

```bash
# 在 plugins 目录创建插件
mkdir -p .squad/plugins/my-plugin
cd .squad/plugins/my-plugin
npm init -y
# 添加插件代码...
```

### 7.3 自定义路由规则

修改 `.squad/routing.md` 添加自定义路由：

```markdown
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
```

### 7.4 与 GitHub Actions 集成

创建 `.github/workflows/squad.yml`：

```yaml
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
```

---

## §8 最佳实践

### 8.1 团队配置最佳实践

**智能体数量控制**

- **建议**: 3-5 个核心智能体
- **原因**: 过多智能体会增加协调成本
- **示例**: Frontend + Backend + Tester + Architect(可选) + Lead(可选)

**技能清晰定义**

```markdown
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
```

### 8.2 决策日志记录

**应记录的决策**

- 技术选型（数据库、框架、语言）
- 架构变更
- API 设计决策
- 安全相关决策
- 性能优化方案

**不应记录的决策**

- 日常任务分配
- 个人偏好（除非影响团队）
- 临时性实验

### 8.3 知识压缩策略

```bash
# 每周压缩一次
squad skills compress --weekly

# 保留最近 10 次会话的完整记录
squad skills prune --keep 10

# 查看压缩率
squad skills stats
```

### 8.4 故障排查

**Copilot Agent 无响应**

```bash
# 1. 检查认证状态
gh auth status

# 2. 检查 Squad 设置
squad doctor

# 3. 重启 Shell
squad shell --fresh
```

**路由不准确**

```bash
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

Squad 是 AI 开发协作的范式转变——从"一个人与 AI 对话"到"AI 团队与项目共同成长"。

**核心价值**

- **多智能体协作**: Frontend + Backend + Tester + Architect 专业分工
- **持久化知识**: `.squad/` 文件系统积累项目知识
- **决策可追溯**: `decisions.md` 记录所有重要决策
- **GitHub 原生**: 基于 Copilot Agent 模式
- **可扩展**: 支持自定义智能体、插件、路由规则

**适用场景**

- 中大型项目（需要多角色分工）
- 长期维护项目（知识积累价值大）
- 需要代码审查和架构决策的项目
- 团队成员需要 AI 辅助的项目

**链接资源**

- GitHub 仓库：https://github.com/bradygaster/squad
- 官方文档：https://github.com/bradygaster/squad#readme
- 插件市场：`squad plugin marketplace`
- 讨论区：https://github.com/bradygaster/squad/discussions

---

*🦞 文档版本 1.0 | 撰写日期：2026-03-31 | 基于仓库 commit eb69444 (2026-03-30)*