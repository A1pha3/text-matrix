---
title: "OpenSwarm：基于 Claude Code 的自主式 AI Agent 编排框架完全指南"
slug: "openswarm-autonomous-ai-orchestrator-guide"
date: 2026-04-04T20:32:00+08:00
lastmod: 2026-04-04T20:32:00+08:00
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "多智能体", "编排框架", "自动化开发"]
description: "OpenSwarm 是由 Claude Code CLI 驱动的自主式 AI Agent 编排框架，通过 Linear 问题采集、Worker/Reviewer 配对流水线、Discord 实时控制、LanceDB 向量记忆和知识图谱，实现多 Agent 协同的自动化代码开发与 PR 自动修复。"
---

# OpenSwarm：基于 Claude Code 的自主式 AI Agent 编排框架完全指南

> 项目地址：[unohee/OpenSwarm](https://github.com/unohee/OpenSwarm)
>
> 今日Star：378（+0）| Forks：57 | License：MIT
>
> 核心定位：用 Claude Code CLI 驱动的自主式 AI 开发团队编排器，实现 Linear 问题自动采集、Worker/Reviewer 配对执行、Discord 进度汇报、LanceDB 长期记忆

## 学习目标

读完本文后，你应该能够：

1. 理解 OpenSwarm 的核心架构和设计理念
2. 掌握 Worker/Reviewer 配对流水线的工作原理
3. 理解 Decision Engine 的 Scope Guard 和任务调度机制
4. 学会配置 Cognitive Memory 和 Knowledge Graph
5. 熟练使用 Discord 命令控制自主执行
6. 理解 PR 自动改进流水线的完整流程
7. 能够部署和运维 OpenSwarm 守护进程

---

## 一、问题：单 Agent 的局限性

Claude Code 非常强大，但单 Agent 面临根本性限制：

1. **上下文窗口有限**：无法同时处理多个复杂任务
2. **没有长期记忆**：每次会话从头开始
3. **缺乏质量门禁**：生成的代码缺少自动审查
4. **无法并行工作**：一个任务完成前无法启动下一个
5. **孤立运作**：与团队工具链（Linear、GitHub CI、Discord）没有集成

OpenSwarm 的核心理念：**把 Claude Code 变成一个可以编排、可以协同、可以记忆的 Agent 系统**。

---

## 二、核心架构：五大组件

```
┌──────────────────────────┐
│      Linear API          │
│  (issues, state, memory) │
└─────────────┬────────────┘
              │
┌─────────────┼─────────────────────────────┐
│             v                                   │
│  ┌──────────────────┐  ┌──────────────────┐   │
│  │ AutonomousRunner │──│  DecisionEngine  │   │
│  │  (heartbeat loop)│  │  (scope guard)  │   │
│  └────────┬─────────┘  └──────────────────┘   │
│           │                                      │
│           v                                      │
│  ┌────────────────────────────────────────────┐  │
│  │            PairPipeline                    │  │
│  │  ┌────────┐ ┌──────────┐ ┌────────┐       │  │
│  │  │ Worker │──│ Reviewer │──│ Tester │──│...│
│  │  └────────┘ └──────────┘ └────────┘       │  │
│  └────────────────────────────────────────────┘  │
│             │                                      │
│             v                                      │
│  ┌────────────────────────────────────────────┐  │
│  │         CLI Adapters                       │  │
│  │    Claude (`claude -p`) | Codex (`codex`) │  │
│  └────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
              │
              v
   ┌───────────┼───────────┐
   v           v           v
┌────────┐ ┌────────┐ ┌────────┐
│Discord │ │Memory  │ │Knowledge│
│  Bot   │ │LanceDB │ │ Graph  │
└────────┘ └────────┘ └────────┘
```

### 五大组件职责

| 组件 | 职责 |
|------|------|
| **AutonomousRunner** | 心跳循环，Cron 调度，任务队列管理 |
| **DecisionEngine** | Scope 验证，限速，优先级排序，工作流映射 |
| **PairPipeline** | Worker → Reviewer → Tester → Documenter 流水线 |
| **CLI Adapters** | Claude Code 和 Codex 的统一接口 |
| **Memory/Knowledge** | 长期记忆和代码知识图谱 |

---

## 三、核心流程：从 Linear 到 PR 的完整流水线

```
Linear (Todo/In Progress)
    ↓
Fetch assigned issues
    ↓
DecisionEngine filters & prioritizes
    ↓
Resolve project path via projectMapper
    ↓
PairPipeline.run()
    ↓
Worker generates code (Claude CLI)
    ↓
Reviewer evaluates (APPROVE/REVISE/REJECT)
    ↓
Loop up to N iterations
    ↓
Optional: Tester → Documenter stages
    ↓
Update Linear issue state (Done/Blocked)
    ↓
Report to Discord
    ↓
Save to cognitive memory
```

---

## 四、Worker/Reviewer 配对模式

这是 OpenSwarm 最核心的创新：**双 Agent 协作生成代码**。

### 工作原理

```
Worker (生成者)
    ↓ 产出代码
    ↓
Reviewer (审查者)
    ↓ APPROVE → 接受，进入下一阶段
    ↓ REVISE → 打回 Worker 重做
    ↓ REJECT → 终止，可能 Escalate
    ↓
循环直到 APPROVE 或达到上限
```

### 配置示例

```yaml
autonomous:
  defaultRoles:
    worker:
      model: claude-haiku-4-5-20251001
      escalateModel: claude-sonnet-4-20250514
      escalateAfterIteration: 3
      timeoutMs: 1800000    # 30 分钟

    reviewer:
      model: claude-haiku-4-5-20251001
      timeoutMs: 600000     # 10 分钟
```

### 迭代上限与 Escalation

- 默认 Worker 最多迭代 3 次
- 第 3 次仍失败时，自动 Escalate 到更强的模型（claude-sonnet-4）
- Reviewer 返回 REJECT 时，记录原因到 cognitive memory

---

## 五、Decision Engine：Scope Guard

Decision Engine 是任务进入流水线前的**守门人**，确保：

1. **Scope 验证**：任务描述是否清晰可执行
2. **限速**：防止单个项目过度消耗资源
3. **优先级排序**：按紧急程度和依赖关系排序
4. **工作流映射**：根据任务类型选择合适的处理流程

### 限速配置

```yaml
autonomous:
  paceControl:
    rollingWindowHours: 5      # 5 小时滚动窗口
    maxTasksPerWindow: 10      # 每窗口最多 10 个任务
    perProjectLimits:
      my-project: 5           # 单项目最多 5 个并行
    turboMode: false            # 超速模式
    backoffMultiplier: 2       # 失败后指数退避
```

---

## 六、Cognitive Memory：混合记忆系统

OpenSwarm 使用 LanceDB 向量数据库 + Xenova E5 embeddings 实现长期记忆。

### 记忆类型

| 类型 | 说明 |
|------|------|
| `belief` | Agent 对系统/用户的信念 |
| `strategy` | 采用的策略和原因 |
| `user_model` | 用户偏好和工作模式 |
| `system_pattern` | 观察到的系统模式 |
| `constraint` | 约束条件 |

### 混合检索公式

```
Score = 0.55 × similarity
      + 0.20 × importance
      + 0.15 × recency
      + 0.10 × frequency
```

### 后台处理

- **Decay**：长时间未访问的记忆逐渐衰减
- **Consolidation**：定期将短期记忆整合为长期记忆
- **Contradiction Detection**：检测矛盾信息并标记
- **Distillation**：压缩冗余信息

---

## 七、Knowledge Graph：代码知识图谱

Knowledge Graph 是**静态代码分析引擎**，构建代码库的依赖关系和影响分析。

### 功能

1. **Dependency Mapping**：追踪模块间依赖关系
2. **Impact Analysis**：变更会影响到哪些文件
3. **Conflict Detection**：并发任务间是否有文件冲突
4. **Cross-Reference**：跨仓库引用关系

### 工作时机

- 任务开始前：确认项目路径和依赖
- 任务结束后：更新知识图谱
- 冲突检测：并发任务执行前

---

## 八、Discord 控制界面

OpenSwarm 提供完整的 Discord Bot 命令系统：

### 任务调度

| 命令 | 说明 |
|------|------|
| `!dev <repo> "<task>"` | 在指定仓库运行开发任务 |
| `!dev list` | 列出已知仓库 |
| `!tasks` | 列出运行中的任务 |
| `!cancel <taskId>` | 取消运行中的任务 |

### 自主执行

| 命令 | 说明 |
|------|------|
| `!auto` | 查看自主执行状态 |
| `!auto start [cron] [--pair]` | 启动自主模式 |
| `!auto stop` | 停止自主模式 |
| `!auto run` | 触发立即心跳 |
| `!approve / !reject` | 审批或拒绝待处理任务 |

### Worker/Reviewer 配对

| 命令 | 说明 |
|------|------|
| `!pair` | 查看配对会话状态 |
| `!pair start [taskId]` | 启动配对会话 |
| `!pair run <taskId> [project]` | 直接运行配对 |
| `!pair stop [sessionId]` | 停止配对会话 |
| `!pair history [n]` | 查看历史会话 |
| `!pair stats` | 查看配对统计 |

### Linear 集成

| 命令 | 说明 |
|------|------|
| `!issues` | 列出 Linear Issues |
| `!issue <id>` | 查看 Issue 详情 |
| `!limits` | 查看 Agent 日执行限制 |

### 调度管理

| 命令 | 说明 |
|------|------|
| `!schedule` | 列出所有调度 |
| `!schedule run <name>` | 立即运行调度 |
| `!schedule toggle <name>` | 启用/禁用调度 |
| `!schedule add <name> <path> <interval> "<prompt>"` | 添加调度 |
| `!schedule remove <name>` | 删除调度 |

---

## 九、PR 自动改进流水线

这是 OpenSwarm 的高级功能：**自动修复 CI 失败和合并冲突**。

### 工作流程

```
PR Opened/Updated
    ↓
Monitor CI Status
    ↓
CI Failed?
    ↓ Yes
Auto-fix via Worker/Reviewer
    ↓
Retry CI
    ↓
Conflict Detected?
    ↓ Yes
Auto-resolve via git
    ↓
Retry until all checks pass
    ↓ No (All Green)
Report Success
```

### 配置

```yaml
prProcessor:
  schedule: "0 * * * *"           # 每小时检查
  maxRetries: 3                   # 最多重试 3 次
  conflictResolver:
    preferLocalChanges: true       # 优先保留本地修改
```

---

## 十、多 Provider 适配器

OpenSwarm 支持 Claude Code 和 OpenAI Codex 两种 CLI：

| Adapter | CLI 命令 | 模型 | Git 管理 |
|---------|---------|------|----------|
| `claude` | `claude -p` | claude-sonnet-4, claude-haiku-4.5, claude-opus-4 | 手动（Worker 提交） |
| `codex` | `codex exec` | o3, o4-mini | 自动（--full-auto） |

### 运行时切换

```
!provider codex    # 切换到 Codex
!provider claude   # 切换回 Claude
```

### 按角色覆盖

```yaml
autonomous:
  defaultRoles:
    worker:
      adapter: codex
      model: o4-mini
    reviewer:
      adapter: claude
      model: claude-sonnet-4-20250514
```

---

## 十一、Rich TUI 聊天界面

```bash
openswarm
```

启动默认的 TUI 聊天界面：

### 快捷键

| 按键 | 动作 |
|------|------|
| `Tab` | 切换标签（Chat / Projects / Tasks / Stuck / Logs） |
| `Enter` | 发送消息 |
| `Shift+Enter` | 换行 |
| `i` | 聚焦输入框 |
| `Esc` | 退出输入聚焦 |
| `Ctrl+C` | 退出 |

状态栏显示：`provider · model · message count · cumulative cost`

---

## 十二、快速上手

### 安装

```bash
npm install -g @intrect/openswarm
openswarm
```

### 配置 config.yaml

```bash
git clone https://github.com/unohee/OpenSwarm.git
cd OpenSwarm
npm install
cp config.example.yaml config.yaml
```

### 配置环境变量 .env

```
DISCORD_TOKEN=your-discord-bot-token
DISCORD_CHANNEL_ID=your-channel-id
LINEAR_API_KEY=your-linear-api-key
LINEAR_TEAM_ID=your-linear-team-id
```

### 运行模式

```bash
openswarm              # TUI 聊天（默认）
openswarm chat        # 简单 readline 聊天
openswarm start        # 启动完整守护进程
openswarm run "Fix bug" -p ~/my-project  # 单次任务
openswarm exec "Run tests" --local --pipeline  # 通过守护进程执行
```

### macOS 守护进程（推荐）

```bash
npm run service:install   # 安装为系统服务
npm run service:start       # 启动
npm run service:status      # 查看状态
npm run service:logs        # 查看日志
```

---

## 十三、技术栈

| 类别 | 技术 |
|------|------|
| 运行时 | Node.js 22+ (ESM) |
| 语言 | TypeScript (strict mode) |
| Agent 执行 | Claude Code CLI (`claude -p`) 或 Codex CLI (`codex exec`) |
| 任务管理 | Linear SDK (@linear/sdk) |
| 通讯 | Discord.js 14 |
| 向量数据库 | LanceDB + Apache Arrow |
| Embeddings | Xenova/transformers (multilingual-e5-base, 768D) |
| 调度 | Croner |
| 配置 | YAML + Zod 验证 |
| 测试 | Vitest |
| 代码检查 | oxlint |

---

## 十四、项目结构

```
src/
├── index.ts                    # 入口
├── cli.ts                      # CLI 入口（run, exec, chat, init, validate, start）
├── cli/
│   └── promptHandler.ts        # exec 命令处理器
├── core/                       # 配置、服务生命周期、类型、事件中心
├── adapters/                   # CLI 适配器（claude, codex）
├── agents/
│   ├── pairPipeline.ts          # Worker → Reviewer → Tester → Documenter
│   ├── agentBus.ts             # Agent 间消息总线
│   └── cliStreamParser.ts      # Claude CLI 输出解析
├── orchestration/              # Decision Engine、任务解析器、调度器
├── automation/                 # 自主运行器、Cron 调度器、PR 处理器
├── memory/                    # LanceDB + E5 embeddings 认知记忆
├── knowledge/                  # 代码知识图谱
├── discord/                    # Bot 核心、命令处理器、配对会话 UI
├── linear/                     # Linear SDK 封装
├── github/                     # GitHub CLI 封装（CI 监控）
├── support/                    # Web Dashboard、Planner、回滚、Git 工具
└── locale/                    # i18n (en/ko)
```

---

## 十五、状态与数据存储

| 路径 | 说明 |
|------|------|
| `~/.openswarm/` | 状态目录（memory、codex、metrics、workflows） |
| `~/.claude/openswarm-*.json` | 流水线历史和任务状态 |
| `config.yaml` | 主配置 |
| `dist/` | 编译输出 |

---

## 十六、最佳实践

### 1. 合理设置限速

```yaml
autonomous:
  paceControl:
    rollingWindowHours: 5
    maxTasksPerWindow: 10
    perProjectLimits:
      large-project: 3    # 大项目限制更严
      small-project: 8
```

### 2. Worker/Reviewer 模型选择

- **简单任务**：worker: haiku → reviewer: haiku（成本最低）
- **复杂任务**：worker: sonnet → reviewer: sonnet（质量最高）
- **混合策略**：worker: haiku + escalate: sonnet（成本效益平衡）

### 3. 善用 Escalation

```yaml
worker:
  escalateAfterIteration: 3      # 3 次失败后升级
  escalateModel: claude-opus-4    # 升级到最强模型
```

### 4. PR 自动修复配置

```yaml
prProcessor:
  maxRetries: 3
  ciRetryDelayMs: 300000          # CI 失败后等 5 分钟
  conflictResolver:
    preferLocalChanges: true       # 保留本地修改
    autoCommit: true               # 自动提交解决
```

---

## 十七、总结

OpenSwarm 代表了 **AI Agent 编排的新范式**——不是单 Agent 孤军奋战，而是多 Agent 协同作战。

核心优势：

1. **自动化**：从 Linear 问题到 PR 的完整流水线，无需人工干预
2. **质量门禁**：Worker/Reviewer 配对确保代码质量
3. **长期记忆**：LanceDB 向量记忆让 Agent 越用越聪明
4. **团队集成**：与 Linear、Discord、GitHub CI 无缝对接
5. **可观测性**：Rich TUI + Discord 命令 + Web Dashboard

如果你正在运营一个需要持续代码开发的 AI Agent 系统，OpenSwarm 是目前最成熟的开源解决方案之一。

---

**相关链接：**
- GitHub：https://github.com/unohee/OpenSwarm
- npm：https://www.npmjs.com/package/@intrect/openswarm
- Discord 控制命令参考见官方 README
