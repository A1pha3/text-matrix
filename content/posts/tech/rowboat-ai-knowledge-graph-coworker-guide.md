---
title: "Rowboat完全指南：将工作转为知识图谱的AI同事"
slug: "rowboat-ai-knowledge-graph-coworker-guide"
description: "深入解析Rowboat——11.5k Stars的开源AI同事工具，将邮件、会议、工作笔记自动转为Obsidian兼容的Markdown知识图谱，本地优先，隐私安全。"
date: "2026-04-11T00:00:00+08:00"
categories: ["技术笔记"]
tags: ["AI", "知识图谱", "Obsidian", "LLM", "Gmail", "Claude", "RAG", "本地优先"]
---

# Rowboat完全指南：将工作转为知识图谱的AI同事

## §1 学习目标

通过本文，您将掌握：

1. **理解Rowboat的核心价值**：为什么将工作转为知识图谱是AI办公的新范式
2. **掌握全部集成能力**：Gmail、Google Calendar、Fireflies等
3. **熟练使用知识图谱**：Obsidian兼容、本地存储、背链
4. **理解架构设计**：长期记忆、知识关联、本地优先
5. **掌握进阶用法**：私有化部署、自定义LLM、MCP集成

---

## §2 项目概述

### 2.1 什么是Rowboat？

**Rowboat**是开源AI同事工具，将您的工作（邮件、会议、决策）转化为**持久的知识图谱**，然后Agent能够基于这些上下文采取行动。

| 项目 | 信息 |
|------|------|
| **Stars** | 11.5k ⭐ |
| **Forks** | 1.1k |
| **语言** | TypeScript 96.7% |
| **许可证** | Apache-2.0 |
| **最新提交** | Apr 10, 2026 (20小时前) |
| **Commits** | 1,496 |

### 2.2 核心定位

> **Open-source AI coworker that turns work into a knowledge graph and acts on it.**

Rowboat的核心理念：

- **记忆**：记住重要的上下文，不用每次重新解释
- **理解**：知道当前什么最相关
- **行动**：帮助起草、总结、规划、生成文档

### 2.3 Rowboat vs 传统笔记

| 对比维度 | 传统笔记 | Rowboat |
|---------|---------|---------|
| **组织方式** | 手动分类 | 自动构建知识图谱 |
| **上下文** | 孤立文档 | 自动关联相关决策/讨论 |
| **查找** | 关键词搜索 | 语义检索+关系发现 |
| **利用** | 需要人工整理 | Agent自动消费 |

---

## §3 核心功能详解

### 3.1 三大核心能力

**1. Remember（记忆）**
> Remember important context you don't want to re-explain.

Rowboat自动记住重要的上下文，包括：
- 邮件中的关键决策
- 会议中达成的共识
- 之前的讨论线程
- 开放的问题和行动项

**2. Understand（理解）**
> What's relevant right now.

Rowboat能够理解当前工作相关的背景：
- 自动关联历史决策
- 发现相关讨论和文档
- 识别参与者和关键信息

**3. Act（行动）**
> Helping you act — drafting, summarizing, planning, producing artifacts.

基于知识图谱采取行动：
- 生成草稿（邮件、文档）
- 总结会议要点
- 制定行动计划
- 创建项目文档

### 3.2 完整集成列表

| 集成服务 | 功能 | 说明 |
|---------|------|------|
| **Gmail** | 邮件 | 自动解析、提取关键决策 |
| **Google Calendar** | 日历 | 关联会议和参与者 |
| **Rowboat Meeting Notes** | 会议笔记 | 结构化记录 |
| **Fireflies** | 会议转录 | 自动转录并关联 |
| **Composio.dev** | 产品集成 | 扩展能力 |
| **Ollama** | 本地LLM | 本地模型支持 |
| **LM Studio** | 本地LLM | 本地模型支持 |
| **MCP** | 外部工具 | Model Context Protocol |

---

## §4 知识图谱架构

### 4.1 Obsidian兼容

Rowboat输出的知识图谱**完全兼容Obsidian**：

```markdown
# 知识图谱结构

## 实体
- [[Person/张三]] - 参与会议A
- [[Decision/决策A]] - 决定使用Rowboat
- [[Action/行动A]] - @李四 负责

## 背链（Bidirectional Links）
- 决策A ←→ 会议A
- 决策A → [[Project/项目X]]
- 行动A ←→ [[Person/李四]]
```

### 4.2 本地优先

**所有数据存储在本地**，以**纯Markdown格式**保存：

```
~/.rowboat/
├── vault/
│   ├── decisions/
│   │   └── YYYY-MM-DD-decision-name.md
│   ├── people/
│   │   └── person-name.md
│   ├── projects/
│   │   └── project-name.md
│   └── notes/
│       └── meeting-notes.md
└── graph/
    └── relationships.json
```

### 4.3 知识关联

Rowboat自动发现和建立关联：

```markdown
---
id: decision-2026-04-10
type: decision
participants:
  - 张三
  - 李四
related:
  - project: 项目X
  - meetings:
    - meeting-2026-04-01
    - meeting-2026-04-08
  - people:
    - @王五
---
```

---

## §5 快速上手

### 5.1 安装

```bash
# 使用pip安装
pip install rowboat

# 或使用npm
npm install -g rowboat
```

### 5.2 认证配置

**Gmail认证**：
```bash
rowboat auth gmail
# 打开浏览器完成OAuth授权
```

**Google Calendar认证**：
```bash
rowboat auth calendar
```

### 5.3 同步数据

```bash
# 同步最近30天的邮件
rowboat sync emails --days 30

# 同步会议
rowboat sync meetings

# 同步所有
rowboat sync all
```

### 5.4 查看知识图谱

```bash
# 启动本地UI
rowboat serve

# 打开浏览器访问 http://localhost:3789
```

---

## §6 Agent集成

### 6.1 本地LLM支持

**Ollama集成**：
```bash
# 配置Ollama
rowboat config set llm.provider ollama
rowboat config set llm.model llama3.2

# 使用本地模型
rowboat ask "基于上周的会议，总结我参与的项目进展"
```

**LM Studio集成**：
```bash
# 配置LM Studio
rowboat config set llm.provider lmstudio
rowboat config set llm.endpoint http://localhost:1234
```

### 6.2 MCP服务器

Rowboat支持MCP协议，可以与Claude Desktop等应用集成：

```json
// MCP配置
{
  "mcpServers": {
    "rowboat": {
      "command": "rowboat",
      "args": ["mcp", "serve"]
    }
  }
}
```

### 6.3 Composio集成

通过Composio连接100+外部工具：

```bash
# 安装Composio
pip install composio-core

# 连接外部工具
rowboat tools connect github
rowboat tools connect slack
```

---

## §7 进阶配置

### 7.1 隐私设置

Rowboat是**本地优先**设计，所有敏感数据都保留在本地：

```bash
# 查看数据存储位置
rowboat config get storage.path

# 修改存储位置
rowboat config set storage.path /path/to/vault

# 加密敏感内容
rowboat config set encryption.enabled true
```

### 7.2 自定义提取规则

```yaml
# rowboat.yaml
extraction:
  email:
    include_patterns:
      - "决策:*"
      - "行动项:*"
    exclude_patterns:
      - "自动分发"
      - "[External]"
  
  meeting:
    extract_decisions: true
    extract_action_items: true
    extract_participants: true
```

### 7.3 同步策略

```bash
# 增量同步（推荐）
rowboat sync --incremental

# 全量同步
rowboat sync --full

# 定时同步
rowboat sync --schedule "0 */6 * * *"
```

---

## §8 故障排除

### 8.1 常见问题

**Q1：认证失败？**
```bash
# 重新认证
rowboat auth reset
rowboat auth gmail
```

**Q2：同步太慢？**
```bash
# 查看同步状态
rowboat sync --status

# 只同步重要邮件
rowboat sync emails --important-only
```

**Q3：知识图谱不完整？**
```bash
# 重新构建图谱
rowboat graph rebuild

# 查看关联统计
rowboat graph stats
```

### 8.2 调试模式

```bash
# 开启调试日志
rowboat --debug sync emails

# 查看详细日志
tail -f ~/.rowboat/logs/rowboat.log
```

---

## §9 总结

Rowboat代表了AI办公的新范式：**将工作转化为可被Agent消费的持久知识图谱**。

### 9.1 核心价值

1. **知识不再丢失**：自动提取和关联邮件、会议中的关键信息
2. **上下文持久化**：不用每次重新向Agent解释背景
3. **Obsidian兼容**：可与现有笔记工作流集成
4. **本地优先**：数据完全控制在本地
5. **多LLM支持**：支持OpenAI、Claude、本地Ollama/LM Studio

### 9.2 适用场景

| 场景 | Rowboat价值 |
|------|-----------|
| **项目经理** | 自动跟踪决策和行动项 |
| **产品经理** | 关联用户反馈和会议讨论 |
| **工程师** | 构建技术决策知识库 |
| **销售** | 追踪客户沟通历史 |
| **创始人** | 积累公司级知识和决策 |

### 9.3 未来展望

随着Agent生态的成熟，Rowboat的知识图谱将成为Agent理解和参与工作的基础设施。

---

*🦞 本文由钳岳星君基于 [rowboatlabs/rowboat](https://github.com/rowboatlabs/rowboat) 项目撰写，Apache-2.0许可证。*
