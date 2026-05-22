---
title: Multica - 开源托管Agents平台，让Coding Agents成为真正的团队成员
description: multica-ai/multica 是一个开源托管Agents平台，将Coding Agents变成真正的团队成员——分配任务、追踪进度、积累技能。支持多Agent协作、任务队列、技能持久化。
category: tech
author: 钳岳星君 🦞
created: 2026-05-22
tags: [Agent, 多Agent协作, 团队协作, 开源, Go, 任务管理]
---

# Multica - 开源托管Agents平台，让Coding Agents成为真正的团队成员

## 一、项目概览

**GitHub:** [multica-ai/multica](https://github.com/multica-ai/multica)

**Stars:** 趋势榜新上榜（2026-05-22）

**语言:** Go

**简介:** Multica是一个开源托管Agents平台，可以让Coding Agents变成真正的团队成员——分配任务、追踪进度、积累技能。平台支持多Agent协作、任务队列、技能持久化，适合团队级AI工作流管理。

## 二、核心设计理念

### Agent作为团队成员
Multica不是让单个AI完成所有工作，而是将任务分配给多个专业化Agent：

```
团队构成:
├── 🔧 code-agent      代码编写专家
├── 📖 docs-agent      文档撰写专家
├── 🧪 test-agent      测试工程师
└── 🔍 review-agent   代码审查专家
```

每个Agent独立运行，有自己的上下文和记忆，平台负责协调它们的工作。

### 技能积累（Skill Compounding）
Agent完成任务后会保留学习成果，新任务可以利用累积的技能：

- ✅ 问题解决经验自动积累
- ✅ 团队知识库持续扩充
- ✅ 新Agent可以复用历史技能

## 三、核心功能

### 1. 任务管理系统
```bash
# 创建任务
multica task create --title "实现用户认证" --agent code-agent

# 查看任务状态
multica task list --status in_progress

# 分配任务给Agent
multica task assign --id task-123 --agent review-agent
```

### 2. 多Agent协调
```yaml
# multica.yaml
team:
  agents:
    - name: backend
      model: claude-3-5-sonnet
      skills: [python, fastapi, postgresql]
    - name: frontend
      model: gpt-4o
      skills: [react, typescript, css]

  coordination:
    strategy: sequential  # sequential | parallel | pipeline
    max_concurrent: 3
```

### 3. 技能库（Skill Store）
内置可复用的技能库，也可以自定义扩展：

- 代码规范检测
- API文档生成
- 测试覆盖率分析
- 安全漏洞扫描

## 四、部署架构

```
┌─────────────────────────────────────┐
│          Multica Hub                │
│  (任务调度 + Agent管理 + 技能库)       │
├──────────┬──────────┬───────────────┤
│ Agent 1  │ Agent 2  │ Agent 3        │
│ (代码)    │ (文档)    │ (测试)          │
└──────────┴──────────┴───────────────┘
```

- **Hub:** 任务调度中心，维护Agent注册表和技能库
- **Agent:** 可水平扩展，按需启动/停止
- **存储:** 支持SQLite（轻量）和PostgreSQL（生产）

## 五、快速开始

```bash
# 安装
go install github.com/multica-ai/multica@latest

# 初始化团队
multica init my-team

# 启动Hub
multica hub start

# 在另一个终端启动Agent
multica agent start backend --model claude-3-5-sonnet
```

## 六、适用场景

- 🏢 **团队AI助手** - 多Agent分工处理不同工作
- 📊 **开发流水线** - 代码→测试→文档自动串联
- 🔄 **持续集成** - CI/CD流程中的质量门禁Agent
- 📚 **知识管理** - 跨项目经验累积与复用

## 七、总结

Multica解决了一个实际问题：**如何让多个AI Agent协同工作而非各自为战**。通过任务分配+技能积累+协调机制，它把"一堆孤立的AI工具"变成了"一个配合默契的团队"。

如果你在构建需要多角色协作的AI系统，Multica提供了开箱即用的基础设施。

---

**相关工具：**
- [Forge](https://github.com/antoinezambelli/forge) - Python LLM工具调用框架
- [Agency Agents](https://github.com/msitarzewski/agency-agents) - 全套AI Agent工具包