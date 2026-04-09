---
title: "Archon：让AI编程变得可重复、可追溯的开源工作流引擎"
date: 2026-04-09T20:20:00+08:00
slug: "archon-ai-coding-workflow-engine-guide"
description: "Archon是首个开源的AI编程harness构建器，将开发流程定义为YAML工作流，实现规划→实现→验证→PR创建的自动化执行。本文深入解析其工作流引擎、DAG执行模型、并行工作树隔离、17个内置工作流模板。"
draft: false
categories: ["技术笔记"]
tags: ["Archon", "AI编程", "工作流引擎", "Claude Code", "YAML", "自动化开发", "开源", "harness"]
---

# Archon：让AI编程变得可重复、可追溯的开源工作流引擎

## §1 项目概述

### 1.1 核心定位

**Archon**是首个开源的AI编程harness构建器，让AI编程变得**可重复**和**可追溯**。

> "Like what Dockerfiles did for infrastructure and GitHub Actions did for CI/CD - Archon does for AI coding workflows. Think n8n, but for software development."

```
┌─────────────────────────────────────────────────────────────┐
│              Archon 核心价值                                        │
├─────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  传统AI编程问题                          │   │
│  │  "修复这个bug" → 结果取决于模型心情                      │   │
│  │  可能跳过规划 | 可能忘记运行测试 | 可能PR描述不合规         │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                     │
│                      Archon 解决                                │
│                           ↓                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  工作流 = 结构，AI = 智能                  │   │
│  │  流程定义权归你 | AI在各步骤填充智能 | 结果可重复          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                                │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 核心特性对比

| 特性 | 传统AI编程 | Archon工作流 |
|------|-----------|--------------|
| **可重复性** | 每次运行结果不同 | 相同流程、相同顺序 |
| **隔离性** | 多任务易冲突 | git worktree并行无冲突 |
| **可追溯** | 执行过程黑盒 | DAG可视化、步骤可追溯 |
| **人工审核** | 难以介入 | 内置审核节点（interactive） |
| **自动化** | 一次性完成 | Loop循环 + 验证门控 |

### 1.3 项目统计

| 指标 | 数值 |
|------|------|
| **Stars** | 14.1k |
| **Forks** | 2.4k |
| **最新版本** | v0.3.2 (2026-04-08) |
| **语言** | TypeScript 97.6% |
| **许可证** | MIT |
| **提交数** | 1,124 commits |
| **文档** | archon.diy |

## §2 工作流引擎深度解析

### 2.1 核心概念

**工作流 = DAG（有向无环图）**

```yaml
# .archon/workflows/build-feature.yaml
nodes:
  - id: plan                    # 节点1: 规划
    prompt: "探索代码库，创建实施计划"

  - id: implement               # 节点2: 实现（依赖plan）
    depends_on: [plan]
    loop:                       # AI循环 - 迭代直到完成
      prompt: "阅读计划，实现下一个任务，运行验证"
    until: ALL_TASKS_COMPLETE   # 循环终止条件
    fresh_context: true         # 每次迭代全新会话

  - id: run-tests               # 节点3: 运行测试（确定性）
    depends_on: [implement]
    bash: "bun run validate"    # 无AI，纯脚本

  - id: review                  # 节点4: 代码审查
    depends_on: [run-tests]
    prompt: "根据计划审查所有变更，修复任何问题"

  - id: approve                 # 节点5: 人工批准（暂停等待）
    depends_on: [review]
    interactive: true            # 暂停等待人工输入

  - id: create-pr               # 节点6: 创建PR
    depends_on: [approve]
    prompt: "推送变更并创建Pull Request"
```

### 2.2 节点类型系统

```
┌─────────────────────────────────────────────────────────────┐
│                 Archon 节点类型                                    │
├─────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              AI节点 (Prompt Node)                        │   │
│  │  prompt: 自然语言指令                                 │   │
│  │  loop: 循环迭代（until条件）                         │   │
│  │  fresh_context: 每次迭代重置上下文                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              确定性节点 (Deterministic Node)              │   │
│  │  bash: 执行shell命令                                  │   │
│  │  输出结果确定，无AI参与                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              交互节点 (Interactive Node)                  │   │
│  │  interactive: true                                   │   │
│  │  暂停等待人工输入/批准                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              循环节点 (Loop Node)                       │   │
│  │  until: ALL_TASKS_COMPLETE / APPROVED / conditions   │   │
│  │  fresh_context: 全新会话 vs 累积上下文                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                                │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 工作树隔离机制

**Archon的核心创新：每个工作流运行使用独立的git worktree**

```bash
# 传统方式 - 多任务冲突
cd project
git checkout -b fix-1     # 任务1
git checkout -b fix-2     # 任务2 → 冲突！

# Archon方式 - worktree隔离
→ Creating isolated worktree on branch archon/task-fix-1...
→ Creating isolated worktree on branch archon/task-fix-2...
→ 5个修复并行执行，0个冲突
```

**优势**：

| 优势 | 说明 |
|------|------|
| **并行无冲突** | 每个worktree独立分支 |
| **主分支安全** | 不在主分支操作 |
| **结果可追溯** | 分支即工作流历史 |
| **合并即发布** | PR合并=工作流完成 |

## §3 架构深度解析

### 3.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Archon 系统架构                                    │
├─────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           平台适配层 (Platform Adapters)                   │   │
│  │  Web UI | CLI | Telegram | Slack | Discord | GitHub   │   │
│  └──────────────────────────┬────────────────────────────┘   │
│                             │                                   │
│                             ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    编排器 (Orchestrator)                    │   │
│  │              消息路由 & 上下文管理                         │   │
│  └─────────────┬───────────────────────┬─────────────────┘   │
│                │                       │                       │
│    ┌───────────┴───┐       ┌────────┴────────┐           │
│    ↓               ↓       ↓                 ↓           │
│ ┌────────┐   ┌──────────┐ ┌────────────────────┐         │
│ │Command │   │ Workflow │ │ AI Assistant Clients │         │
│ │Handler │   │ Executor │ │ (Claude / Codex)    │         │
│ │(Slash) │   │  (YAML) │ │                    │         │
│ └────────┘   └──────────┘ └────────────────────┘         │
│                │                       │                       │
│                └───────────┬───────────┘                       │
│                            ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              数据层 (Data Layer)                            │   │
│  │  SQLite / PostgreSQL (7 Tables)                          │   │
│  │  Codebases | Conversations | Sessions | Workflow Runs     │   │
│  │  Isolation Environments | Messages | Workflow Events      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                                │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 核心组件

| 组件 | 职责 |
|------|------|
| **Platform Adapters** | 连接各种平台（Web/CLI/Telegram/Slack等） |
| **Orchestrator** | 消息路由、上下文管理、任务分发 |
| **Command Handler** | 处理斜杠命令（如`/archon-idea-to-pr`） |
| **Workflow Executor** | YAML工作流解析与DAG执行 |
| **AI Assistant Clients** | Claude/Codex API抽象层 |
| **Data Layer** | SQLite/PostgreSQL持久化 |

## §4 17个内置工作流模板

Archon提供17个开箱即用的工作流：

### 4.1 工作流总览

| 工作流 | 功能 |
|--------|------|
| **archon-assist** | 通用问答/调试/探索 |
| **archon-fix-github-issue** | Issue → 分类→调查→实现→PR |
| **archon-idea-to-pr** | 功能想法 → 计划→实现→PR（5并行审查） |
| **archon-plan-to-pr** | 执行现有计划 → 实现→PR |
| **archon-issue-review-full** | 全面的Issue修复+多Agent审查 |
| **archon-smart-pr-review** | PR复杂度分类→定向审查→综合 |
| **archon-comprehensive-pr-review** | 多Agent PR审查（5并行审查者） |
| **archon-create-issue** | 问题分类→上下文收集→创建Issue |
| **archon-validate-pr** | PR验证（主分支+特性分支） |
| **archon-resolve-conflicts** | 冲突检测→分析→解决→验证→提交 |
| **archon-feature-development** | 计划→实现→验证→PR |
| **archon-architect** | 架构扫频、复杂度降低、代码健康改进 |
| **archon-refactor-safely** | 安全重构（类型检查+行为验证） |
| **archon-ralph-dag** | PRD实现循环（迭代直到完成） |
| **archon-remotion-generate** | Remotion视频生成/修改 |
| **archon-test-loop-dag** | 测试循环工作流 |
| **archon-piv-loop** | PIV循环（计划-实施-验证+人工审核） |

### 4.2 典型工作流：archon-idea-to-pr

```yaml
# archon-idea-to-pr 工作流详解
nodes:
  # 阶段1: 规划
  - id: plan
    prompt: "分析需求，探索代码库，创建详细实施计划"

  # 阶段2: 实现循环
  - id: implement
    depends_on: [plan]
    loop:
      prompt: "阅读计划，实施下一个任务，运行验证"
    until: ALL_TASKS_COMPLETE
    fresh_context: true

  # 阶段3: 验证
  - id: run-tests
    depends_on: [implement]
    bash: "bun run validate && bun run test"

  # 阶段4: 审查（5并行）
  - id: review
    depends_on: [run-tests]
    # 5个并行审查Agent
    agents:
      - 安全性审查
      - 性能审查
      - 代码风格审查
      - 测试覆盖审查
      - 文档审查

  # 阶段5: 自我修复
  - id: self-fix
    depends_on: [review]
    loop:
      prompt: "根据审查反馈修复问题"
    until: NO_ISSUES_REMAIN

  # 阶段6: PR创建
  - id: create-pr
    depends_on: [self-fix]
    prompt: "推送变更，创建符合规范的Pull Request"
```

## §5 安装与配置

### 5.1 完整安装（5分钟）

```bash
# 1. 克隆仓库
git clone https://github.com/coleam00/Archon
cd Archon

# 2. 安装依赖
bun install

# 3. 运行设置向导
claude

# 4. 告诉AI： "Set up Archon"
# 向导会引导配置：
#   - CLI安装
#   - 认证设置
#   - 平台选择
#   - 目标项目配置
```

### 5.2 快速安装（30秒）

```bash
# macOS / Linux
curl -fsSL https://archon.diy/install | bash

# Windows (PowerShell)
irm https://archon.diy/install.ps1 | iex

# Homebrew
brew install coleam00/archon/archon
```

### 5.3 使用方式

```bash
# 进入目标项目
cd /path/to/your/project

# 启动Claude Code
claude

# 告诉它你要做什么
What archon workflows do I have?
Use archon to fix issue #42
Use archon to add dark mode
```

## §6 Web UI与平台集成

### 6.1 Web UI功能

| 页面 | 功能 |
|------|------|
| **Chat** | 实时流式对话，工具调用可视化 |
| **Dashboard** | 工作流监控，filter by 项目/状态/日期 |
| **Workflow Builder** | 可视化DAG编辑器，拖拽创建工作流 |
| **Workflow Execution** | 步骤级进度视图 |

### 6.2 平台集成

| 平台 | 安装时间 | 指南 |
|------|----------|------|
| **Telegram** | 5分钟 | Telegram Guide |
| **Slack** | 15分钟 | Slack Guide |
| **GitHub Webhooks** | 15分钟 | GitHub Guide |
| **Discord** | 5分钟 | Discord Guide |

```bash
# Telegram集成示例
# 1. 创建Bot获取token
# 2. 配置环境变量
ARCHON_TELEGRAM_BOT_TOKEN=xxx

# 3. 启动
./archon start --platform telegram
```

## §7 自定义工作流

### 7.1 创建自定义工作流

```yaml
# .archon/workflows/my-workflow.yaml
nodes:
  - id: context
    prompt: "收集相关代码上下文"

  - id: implement
    depends_on: [context]
    loop:
      prompt: "实施任务项"
    until: ALL_TASKS_COMPLETE

  - id: test
    depends_on: [implement]
    bash: "npm test"

  - id: lint
    depends_on: [implement]
    bash: "npm run lint"

  - id: pr
    depends_on: [test, lint]
    prompt: "创建Pull Request"
```

### 7.2 覆盖默认工作流

```bash
# 你的项目可以覆盖默认工作流
# 复制默认模板到你的项目
cp .archon/workflows/defaults/archon-idea-to-pr.yaml \
   .archon/workflows/my-idea-to-pr.yaml

# 修改为你想要的流程
# 提交到仓库
git add .archon/workflows/my-idea-to-pr.yaml
git commit -m "feat: 使用我们团队的PR模板"
```

## §8 与Claude Code的集成

### 8.1 工作原理

```bash
# 用户在Claude Code中输入
Use archon to fix issue #42

# Archon处理流程
1. Command Handler识别"archon"命令
2. Workflow Executor加载对应YAML
3. DAG解析，确定执行顺序
4. AI Assistant Client调用Claude API
5. 每个节点的结果写入数据库
6. Dashboard实时显示进度
```

### 8.2 与内置Agent的对比

| 维度 | 内置Agent | Archon工作流 |
|------|-----------|---------------|
| **结构** | 自由形式 | YAML强制结构 |
| **可重复** | 低 | 高 |
| **验证门控** | 无 | 内置验证节点 |
| **人工介入** | 困难 | interactive节点 |
| **并行执行** | 有限 | worktree隔离 |

## §9 最佳实践

### 9.1 工作流设计原则

```yaml
# 好的工作流设计
nodes:
  # 1. 规划先行
  - id: plan
    prompt: "先理解问题，再实施方案"

  # 2. 小步骤
  - id: implement
    loop:
      prompt: "每次只做一件事"
    until: ALL_TASKS_COMPLETE

  # 3. 验证紧随
  - id: verify
    depends_on: [implement]
    bash: "bun run validate"

  # 4. 人工审核点
  - id: review
    interactive: true  # 重要决策前暂停
```

### 9.2 团队协作

```bash
# 团队工作流管理
# 1. 在模板仓库定义工作流
.archon/workflows/
├── defaults/           # 内置模板
│   ├── archon-idea-to-pr.yaml
│   └── archon-fix-github-issue.yaml
└── team/               # 团队定制
    ├── security-review.yaml
    └── api-pr.yaml

# 2. 提交到仓库
git commit -m "feat: 添加安全审查工作流"

# 3. 团队成员自动获得更新
```

## §10 总结

### 10.1 核心价值

Archon重新定义了AI编程的范式：

- ✅ **确定性**：相同流程，相同结果
- ✅ **隔离性**：worktree并行无冲突
- ✅ **可追溯**：每个步骤都有记录
- ✅ **可组合**：AI节点+确定性节点混合
- ✅ **可扩展**：YAML工作流易于修改
- ✅ **跨平台**：Web/CLI/Telegram/Slack/Discord

### 10.2 适用场景

| 场景 | 价值 |
|------|------|
| **团队AI编程规范** | 统一工作流，强制代码审查 |
| **大规模重构** | worktree隔离，并行安全 |
| **自动化PR创建** | 规范化PR描述和审查流程 |
| **AI辅助开发** | 结构化AI工作，减少随机性 |

---

**官方资源**：

- GitHub：github.com/coleam00/Archon
- 文档：archon.diy
- 最新版本：v0.3.2 (2026-04-08)

---

🦞 文档版本：v1.0 | 写作日期：2026-04-09
