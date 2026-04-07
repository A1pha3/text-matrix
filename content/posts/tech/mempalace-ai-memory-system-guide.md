---
title: "MemPalace：7.7k Stars史上最高分AI记忆系统，96.6% R@5零API调用"
date: 2026-04-07T21:20:00+08:00
slug: mempalace-ai-memory-system-guide
description: "深度解析MemPalace：基于记忆宫殿原理的AI记忆系统。使用Palace结构组织记忆（Wings/Halls/Rooms）、AAAK无损压缩（30x）、本地SQLite知识图谱。96.6% LongMemEval R@5，零API调用，完全本地运行。"
categories: ["技术笔记"]
tags: ["AI记忆", "记忆宫殿", "AAAK压缩", "知识图谱", "MCP"]
draft: false
---

# MemPalace：7.7k Stars史上最高分AI记忆系统

## 项目概述

**MemPalace**是由milla-jovovich团队开发的开源AI记忆系统，核心特点是「基于记忆宫殿原理，让AI记住一切，检索速度提升34%」。与传统的记忆系统不同，MemPalace不依赖云API、不需要订阅、完全本地运行，且在LongMemEval基准测试中取得了**史上最高分96.6%**。

| 指标 | 数值 |
|------|------|
| **GitHub Stars** | 7.7k |
| **Forks** | 805 |
| **贡献者** | 3 (milla-jovovich, bensig, claude) |
| **最新提交** | 2026-04-07（16小时前） |
| **最新版本** | v3.0.0 |
| **许可证** | MIT |
| **技术栈** | Python 98.3%, Shell 1.7% |

**官方Slogan：** "The highest-scoring AI memory system ever benchmarked. And it's free."

**核心优势：**
- 🏆 **史上最高分**：96.6% LongMemEval R@5（零API调用）
- 💰 **完全免费**：无需API Key，无需订阅，本地运行
- 🔒 **隐私优先**：所有数据本地存储，无需云端
- ⚡ **极速检索**：170 tokens wake-up上下文，30x AAAK压缩

---

## 核心问题：AI对话记忆的困境

### 传统方案的局限

当你与AI进行日常对话时——每一个决策、每一次调试、每一次架构讨论——对话都会在会话结束时消失。六个月的工作，白费了。

**每年19.5M tokens的对话量**：
- 相当于19.5M tokens无法放入任何上下文窗口
- 传统的LLM摘要方案需要约$507/年
- 摘要会丢失上下文和细节

### 现有记忆系统的痛点

| 方案 | 加载Tokens | 年成本 | 问题 |
|------|-----------|--------|------|
| 粘贴全部 | 19.5M（塞不下） | - | 无法工作 |
| LLM摘要 | ~650K | ~$507/年 | 丢失上下文 |
| MemPalace wake-up | ~170 | ~$0.70/年 | 完整记忆 |

---

## 技术架构解析

### 整体架构：The Palace（记忆宫殿）

MemPalace的核心创新是「记忆宫殿」结构——仿照古代希腊演说家西塞罗（ Cicero）使用的方法：

```
┌─────────────────────────────────────────────────────────────┐
│                    WING: Person                           │
│                                                             │
│  ┌──────────┐ ──hall── ┌──────────┐                      │
│  │ Room A   │          │ Room B   │                      │
│  └────┬─────┘          └──────────┘                      │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────┐ ───▶ ┌──────────┐                         │
│  │ Closet   │       │ Drawer   │                         │
│  └──────────┘       └──────────┘                         │
└─────────────────────────────────────────────────────────────┘
                           │
                        tunnel │
┌─────────────────────────────────────────────────────────────┐
│                    WING: Project                          │
│                                                             │
│  ┌────┬─────┐ ──hall── ┌──────────┐                      │
│  │ Room A│          │ Room C   │                      │
│  └────┬─────┘          └──────────┘                      │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────┐ ───▶ ┌──────────┐                         │
│  │ Closet   │       │ Drawer   │                         │
│  └──────────┘       └──────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### 核心数据结构

| 结构 | 说明 | 示例 |
|------|------|------|
| **Wing** | 一个人或项目 | `wing_kai`, `wing_driftwood` |
| **Room** | Wing内的具体主题 | `auth-migration`, `graphql-switch` |
| **Hall** | 同一Wing内的房间连接 | `hall_facts`, `hall_events` |
| **Tunnel** | 不同Wing间的跨域连接 | auth相关房间跨项目连接 |
| **Closet** | 压缩摘要，快速AI读取 | AAAK格式的摘要 |
| **Drawer** | 原始文件 | 完整原文，永不丢失 |

### Hall类型（记忆类型）

```python
hall_facts      # 已做出的决策
hall_events     # 会议、里程碑、调试
hall_discoveries # 突破、新洞察
hall_preferences # 习惯、喜好
hall_advice     # 建议和解决方案
```

### Tunnel的威力

```python
# 同一Room在多个Wing中出现，自动创建Tunnel
wing_kai / hall_events / auth-migration 
  → "Kai debugged the OAuth token refresh"

wing_driftwood / hall_facts / auth-migration 
  → "team decided to migrate auth to Clerk"

wing_priya / hall_advice / auth-migration 
  → "Priya approved Clerk over Auth0"
```

---

## AAAK压缩：30x无损压缩

### AAAK是什么？

AAAK（Ant Asset Keyword）是一种无损的简化语言，专为AI记忆设计：

**English原文（约1000 tokens）：**
```
Priya manages the Driftwood team: Kai (backend, 3 years), Soren (frontend), Maya (infrastructure), 
and Leo (junior, started last month). They're building a SaaS analytics platform. 
Current sprint: auth migration to Clerk. Kai recommended Clerk over Auth0 based on pricing and DX.
```

**AAAK压缩后（约120 tokens）：**
```
TEAM: PRI(lead) | KAI(backend,3yr) SOR(frontend) MAY(infra) LEO(junior,new) 
PROJ: DRIFTWOOD(saas.analytics) | SPRINT: auth.migration→clerk 
DECISION: KAI.rec:clerk>auth0(pricing+dx) | ★★★★
```

### AAAK的设计原则

| 原则 | 说明 |
|------|------|
| **无损** | 不丢失任何信息 |
| **通用** | 任何LLM都能读取 |
| **简洁** | ~30x压缩率 |
| **自动学习** | AI在wake-up时自动学会 |

---

## 四层记忆栈（L0-L3）

```
┌─────────────────────────────────────────────────────────────┐
│ L0 Identity       │ 身份：这是哪个AI？      │ ~50 tokens │ 常驻加载  │
│ L1 Critical Facts│ 关键事实：团队/项目/偏好│ ~120 tokens│ 常驻加载  │
│ L2 Room Recall   │ 房间回忆：近期会话      │ 按需       │ 话题触发  │
│ L3 Deep Search   │ 深度搜索：全量语义检索  │ 按需       │ 显式询问  │
└─────────────────────────────────────────────────────────────┘
```

**wake-up后AI拥有~170 tokens的关键上下文，知道你的世界。**

---

## Benchmarks：96.6%史上最高分

### 标准基准测试

| Benchmark | 模式 | 分数 | API调用 |
|-----------|------|------|---------|
| **LongMemEval R@5** | Raw (ChromaDB) | **96.6%** | 零 |
| **LongMemEval R@5** | + Haiku重排 | **100%** | ~500 |
| LoCoMo R@10 | Raw, session level | 60.3% | 零 |
| Personal palace R@10 | Heuristic | 85% | 零 |
| Palace structure | Wing+Room过滤 | **+34%** | 零 |

### vs 已发布系统

| 系统 | LongMemEval R@5 | 需要API | 成本 |
|------|-----------------|--------|------|
| **MemPalace (hybrid)** | 100% | 可选 | 免费 |
| Supermemory ASMR | ~99% | 是 | - |
| **MemPalace (raw)** | 96.6% | 否 | 免费 |
| Mastra | 94.87% | 是 (GPT) | API费用 |
| Mem0 | ~85% | 是 | $19-249/月 |
| Zep | ~85% | 是 | $25/月+ |

---

## MCP Server：19个工具

### 连接MemPalace

```bash
# 一行命令连接
claude mcp add mempalace -- python -m mempalace.mcp_server
```

### 19个工具总览

**Palace读取工具：**
| 工具 | 功能 |
|------|------|
| `mempalace_status` | Palace概览+AAAK规范 |
| `mempalace_list_wings` | 列出所有Wings |
| `mempalace_list_rooms` | 列出Wing内Rooms |
| `mempalace_get_taxonomy` | 完整分类树 |
| `mempalace_search` | 语义搜索（支持Wing/Room过滤） |
| `mempalace_check_duplicate` | 存入前检查重复 |
| `mempalace_get_aaak_spec` | AAAK方言参考 |

**Palace写入工具：**
| 工具 | 功能 |
|------|------|
| `mempalace_add_drawer` | 存入原文 |
| `mempalace_delete_drawer` | 删除（按ID） |

**知识图谱工具：**
| 工具 | 功能 |
|------|------|
| `mempalace_kg_query` | 实体关系查询（支持时间过滤） |
| `mempalace_kg_add` | 添加事实 |
| `mempalace_kg_invalidate` | 标记事实过期 |
| `mempalace_kg_timeline` | 实体编年史 |
| `mempalace_kg_stats` | 图谱概览 |

**导航工具：**
| 工具 | 功能 |
|------|------|
| `mempalace_traverse` | 从Room穿越Wings |
| `mempalace_find_tunnels` | 找到连接两个Wings的Rooms |
| `mempalace_graph_stats` | 图连通性概览 |

**Agent Diary工具：**
| 工具 | 功能 |
|------|------|
| `mempalace_diary_write` | 写AAAK日记 |
| `mempalace_diary_read` | 读最近日记 |

---

## 矛盾检测

MemPalace在存储前会检查事实矛盾：

```python
Input: "Soren finished the auth migration"
Output: 🔴 AUTH-MIGRATION: attribution conflict 
        — Maya was assigned, not Soren

Input: "Kai has been here 2 years"
Output: 🟡 KAI: wrong_tenure 
        — records show 3 years (started 2023-04)

Input: "The sprint ends Friday"
Output: 🟡 SPRINT: stale_date 
        — current sprint ends Thursday (updated 2 days ago)
```

---

## 快速开始

### 安装

```bash
pip install mempalace
```

### 初始化

```bash
# 设置你的世界
mempalace init ~/projects/myapp

# 挖掘数据
mempalace mine ~/projects/myapp          # 项目代码和文档
mempalace mine ~/chats/ --mode convos     # 对话导出
mempalace mine ~/chats/ --mode convos --extract general  # 自动分类

# 搜索
mempalace search "why did we switch to GraphQL"
```

### 三种挖掘模式

| 模式 | 说明 |
|------|------|
| `projects` | 代码和文档 |
| `convos` | 对话导出 |
| `general` | 自动分类（决策/偏好/里程碑/问题） |

---

## Agent集成

### 与Claude/ChatGPT/Cursor（MCP兼容工具）

```bash
# 连接（只需一次）
claude mcp add mempalace -- python -m mempalace.mcp_server
```

现在问AI：
> "What did we decide about auth last month?"

AI会自动调用`mempalace_search`，获取结果后回答你。你无需输入任何命令。

### 与本地模型（Llama/Mistral）

**方法1：Wake-up命令**
```bash
mempalace wake-up > context.txt
# 把context.txt粘贴到本地模型的系统提示
```

**方法2：CLI搜索**
```bash
mempalace search "auth decisions" > results.txt
# 将results.txt包含到提示中
```

**Python API：**
```python
from mempalace.searcher import search_memories
results = search_memories("auth decisions", palace_path="~/.mempalace/palace")
```

---

## 知识图谱：时间敏感的实体关系

```python
from mempalace.knowledge_graph import KnowledgeGraph

kg = KnowledgeGraph()

# 添加三元组（带时间窗口）
kg.add_triple("Kai", "works_on", "Orion", valid_from="2025-06-01")
kg.add_triple("Maya", "assigned_to", "auth-migration", valid_from="2026-01-15")
kg.add_triple("Maya", "completed", "auth-migration", valid_from="2026-02-01")

# 查询Kai现在做什么？
kg.query_entity("Kai")
# → [Kai → works_on → Orion (current), Kai → recommended → Clerk (2026-01)]

# 2026年1月20日Maya在做什么？
kg.query_entity("Maya", as_of="2026-01-20")
# → [Maya → assigned_to → auth-migration (active)]

# 时间线
kg.timeline("Orion")
# → 项目的编年史
```

### vs Zep (Graphiti)

| 特性 | MemPalace | Zep (Graphiti) |
|------|-----------|----------------|
| 存储 | SQLite（本地） | Neo4j（云） |
| 成本 | 免费 | $25/月+ |
| 时间有效性 | 是 | 是 |
| 自托管 | 始终 | 仅企业版 |
| 隐私 | 全部本地 | SOC 2, HIPAA |

---

## 专业Agent：每个Agent有自己的记忆

```bash
~/.mempalace/agents/
├── reviewer.json   # 代码质量、模式、bug
├── architect.json  # 设计决策、权衡
└── ops.json        # 部署、故障、基础设施
```

你的CLAUDE.md只需一行：
```
You have MemPalace agents. Run mempalace_list_agents to see them.
```

每个Agent：
- 有自己的专注领域
- 用AAAK写日记，跨会话持久化
- 通过读自己的历史建立专业能力

---

## 自动保存Hook

两个Claude Code的自动保存Hook：

**保存Hook** - 每15条消息触发一次结构化保存
**PreCompact Hook** - 在上下文压缩前紧急保存

```json
{
  "hooks": {
    "Stop": [{
      "matcher": "",
      "hooks": [{"type": "command", "command": "/path/to/mempalace/hooks/mempal_save_hook.sh"}]
    }],
    "PreCompact": [{
      "matcher": "",
      "hooks": [{"type": "command", "command": "/path/to/mempalace/hooks/mempal_precompact_hook.sh"}]
    }]
  }
}
```

---

## 项目结构

```
mempalace/
├── mempalace/              # 核心包
│   ├── cli.py              # CLI入口
│   ├── mcp_server.py      # MCP服务器（19工具）
│   ├── knowledge_graph.py # 时间敏感实体图
│   ├── palace_graph.py    # Room导航图
│   ├── dialect.py         # AAAK压缩
│   ├── miner.py           # 项目文件摄入
│   ├── convo_miner.py    # 对话摄入
│   ├── searcher.py       # ChromaDB语义搜索
│   └── onboarding.py     # 引导设置
├── benchmarks/            # 可复现基准测试
│   ├── longmemeval_bench.py
│   ├── locomo_bench.py
│   └── membench_bench.py
├── hooks/                # Claude Code自动保存
│   ├── mempal_save_hook.sh
│   └── mempal_precompact_hook.sh
├── examples/             # 使用示例
└── tests/                # 测试套件
```

---

## 所有命令参考

```bash
# 设置
mempalace init <dir>              # 引导设置+AAAK引导

# 挖掘
mempalace mine <dir>              # 挖掘项目文件
mempalace mine <dir> --mode convos  # 挖掘对话
mempalace mine <dir> --wing myapp  # 指定Wing

# 分割
mempalace split <dir>              # 分割串联的记录
mempalace split <dir> --dry-run    # 预览

# 搜索
mempalace search "query"          # 搜索全部
mempalace search "query" --wing myapp  # Wing内搜索
mempalace search "query" --room auth-migration  # Room内搜索

# 记忆栈
mempalace wake-up                 # 加载L0+L1上下文
mempalace wake-up --wing driftwood  # 项目特定上下文

# 压缩
mempalace compress --wing myapp    # AAAK压缩

# 状态
mempalace status                  # Palace概览
```

---

## 团队使用场景

### 独立开发者管理多个项目

```bash
# 挖掘每个项目的对话
mempalace mine ~/chats/orion/ --mode convos --wing orion
mempalace mine ~/chats/nova/ --mode convos --wing nova
mempalace mine ~/chats/helios/ --mode convos --wing helios

# 6个月后：
mempalace search "database decision" --wing orion
# → "Chose Postgres over SQLite because Orion needs concurrent writes
#    and the dataset will exceed 10GB. Decided 2025-11-03."
```

### 团队负责人管理产品

```bash
# 挖掘Slack和AI对话
mempalace mine ~/exports/slack/ --mode convos --wing driftwood
mempalace mine ~/.claude/projects/ --mode convos

# 问：
mempalace search "Soren sprint" --wing driftwood
# → 14条相关记录：OAuth重构、暗色模式、组件库迁移

mempalace search "Clerk decision" --wing driftwood
# → "Kai recommended Clerk over Auth0 — pricing + developer experience.
#    Team agreed 2026-01-15. Maya handling the migration."
```

---

## MemPalace vs 其他系统

| 系统 | LongMemEval | 需要API | 成本 | 自托管 |
|------|-------------|---------|------|--------|
| **MemPalace (hybrid)** | 100% | 可选 | 免费 | ✓ |
| Supermemory | ~99% | 是 | - | - |
| **MemPalace (raw)** | 96.6% | 否 | 免费 | ✓ |
| Mastra | 94.87% | 是 | API费用 | - |
| Mem0 | ~85% | 是 | $19-249/月 | - |
| Zep | ~85% | 是 | $25/月+ | 企业版 |

---

## 安装与配置

### 前置条件

| 依赖 | 版本 |
|------|------|
| Python | 3.9+ |
| ChromaDB | >= 0.4.0 |
| PyYAML | >= 6.0 |

### 安装

```bash
pip install mempalace
```

### 配置

**全局配置（~/.mempalace/config.json）：**
```json
{
  "palace_path": "/custom/path/to/palace",
  "collection_name": "mempalace_drawers",
  "people_map": {"Kai": "KAI", "Priya": "PRI"}
}
```

**Wing配置（~/.mempalace/wing_config.json）：**
```json
{
  "default_wing": "wing_general",
  "wings": {
    "wing_kai": {"type": "person", "keywords": ["kai", "kai's"]},
    "wing_driftwood": {"type": "project", "keywords": ["driftwood", "analytics", "saas"]}
  }
}
```

---

## 项目地址

| 项目 | 地址 |
|------|------|
| **GitHub** | https://github.com/milla-jovovich/mempalace |
| **Discord** | https://discord.com/invite/ycTQQCu6kn |

---

## 总结

MemPalace代表了AI记忆系统的范式转变：

1. **结构化记忆**：Wings/Halls/Rooms的组织方式，+34%检索提升
2. **AAAK压缩**：30x无损压缩，任何LLM都能读取
3. **完全本地**：SQLite存储，无需云端，隐私优先
4. **史上最高分**：96.6% LongMemEval R@5，零API调用
5. **MCP原生**：19个工具，与Claude/Cursor无缝集成
6. **免费开源**：MIT许可证，无隐藏成本

**适用场景：**
- ✅ 独立开发者管理多个项目记忆
- ✅ 团队负责人管理产品和人员上下文
- ✅ AI Agent的长期记忆
- ✅ 本地优先的隐私敏感场景

**MemPalace让你记住一切，但只加载AI需要的。**

---

*本文基于MemPalace项目编写，发布时间：2026-04-07*
