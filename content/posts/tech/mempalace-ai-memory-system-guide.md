---
title: "MemPalace：47.3k Stars史上最高分AI记忆系统，96.6% R@5零API调用"
date: "2026-04-13T10:30:00+08:00"
slug: mempalace-ai-memory-system-guide
description: "深度解析MemPalace：基于记忆宫殿原理的AI记忆系统，采用Wings/Halls/Rooms结构组织记忆。本地ChromaDB向量检索与SQLite知识图谱双引擎驱动，96.6% LongMemEval R@5，零API调用，完全本地运行。"
categories: ["技术笔记"]
tags: ["AI记忆", "记忆宫殿", "知识图谱", "MCP", "本地向量数据库"]
draft: false
---

# MemPalace：47.3k Stars 的 AI 记忆系统，96.6% R@5 零 API 调用

## 项目概述

**MemPalace**是由 milla-jovovich 团队开发的开源 AI 记忆系统，核心特点是「基于记忆宫殿（Method of Loci）原理，让 AI 记住一切」。与传统的记忆系统不同，MemPalace 不依赖云 API、不需要订阅、完全本地运行，且在 LongMemEval（长程记忆评估基准）基准测试中取得了**史上最高分 96.6%**。

| 指标 | 数值 |
|------|------|
| **GitHub Stars** | 47.3k (47,262) |
| **Forks** | 6,174 |
| **贡献者** | 3 (igorls, bensig, tmuskal) |
| **最新提交** | 2026-04-07（16 小时前） |
| **最新版本** | v3.0.0 |
| **许可证** | MIT |
| **技术栈** | Python 98.3%, Shell 1.7% |

**官方 Slogan：** "The highest-scoring AI memory system ever benchmarked. And it's free."

**核心特点：**
- **96.6% LongMemEval R@5**：零 API 调用，Raw 模式
- **完全免费**：无需 API Key，无需订阅，本地运行
- **隐私优先**：所有数据本地存储，无需云端
- **极速唤醒**：~170 tokens wake-up 上下文

---

## 核心问题：AI 对话记忆的困境

### 传统方案的局限

当你与 AI 进行日常对话时——每一个决策、每一次调试、每一次架构讨论——对话都会在会话结束时消失。六个月的工作，白费了。

**每年 19.5M tokens 的对话量**：
- 相当于 19.5M tokens 无法放入任何上下文窗口
- 传统的 LLM 摘要方案需要约$507/年
- 摘要会丢失上下文和细节

### 现有记忆系统的痛点

| 方案 | 加载 Tokens | 年成本 | 问题 |
|------|-----------|--------|------|
| 粘贴全部 | 19.5M（塞不下） | - | 无法工作 |
| LLM 摘要 | ~650K | ~$507/年 | 丢失上下文 |
| MemPalace wake-up | ~170 | ~$0.70/年 | 完整记忆 |

---

## 技术架构解析

### 整体架构：The Palace（记忆宫殿）

MemPalace 的核心创新是「记忆宫殿」结构——仿照古代希腊演说家西塞罗（Cicero）使用的方法：

```
┌─────────────────────────────────────────────────────────────┐
│                    WING: Person                             │
│                                                             │
│  ┌──────────┐ ──hall── ┌──────────┐                        │
│  │ Room A   │          │ Room B   │                        │
│  └────┬─────┘          └──────────┘                        │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────┐ ───▶ ┌──────────┐                             │
│  │ Closet   │       │ Drawer   │                             │
│  └──────────┘       └──────────┘                             │
└─────────────────────────────────────────────────────────────┘
                           │
                        tunnel │
┌─────────────────────────────────────────────────────────────┐
│                    WING: Project                            │
│                                                             │
│  ┌────┬─────┐ ──hall── ┌──────────┐                        │
│  │ Room A│          │ Room C   │                        │
│  └────┬─────┘          └──────────┘                        │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────┐ ───▶ ┌──────────┐                             │
│  │ Closet   │       │ Drawer   │                             │
│  └──────────┘       └──────────┘                             │
└─────────────────────────────────────────────────────────────┘
```

### 核心数据结构

| 结构 | 说明 | 示例 |
|------|------|------|
| **Wing** | 一个人或项目 | `wing_kai`, `wing_driftwood` |
| **Room** | Wing 内的具体主题 | `auth-migration`, `graphql-switch` |
| **Hall** | 同一 Wing 内的房间连接 | `hall_facts`, `hall_events` |
| **Tunnel** | 不同 Wing 间的跨域连接 | auth 相关房间跨项目连接 |
| **Closet** | 摘要，指向原始内容的指针 | 原始内容的压缩摘要 |
| **Drawer** | 原始文件 | 完整原文，永不丢失 |

### Hall 类型（记忆类型）

```python
hall_facts       # 已做出的决策
hall_events      # 会议、里程碑、调试
hall_discoveries  # 突破、新洞察
hall_preferences  # 习惯、喜好
hall_advice      # 建议和解决方案
```

### Tunnel 的威力

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

## Raw 模式：96.6%的真正来源

MemPalace 的 96.6%成绩来自**Raw 模式（ChromaDB 直存）**，而非压缩或摘要：

**核心设计原则：**
- **存储一切**：原始对话 verbatim 存入 ChromaDB，不做摘要、不做提取
- **语义检索**：让语义搜索找到内容，而非依赖 AI 判断"什么值得记住"
- **零 LLM 干预**：存储阶段不调用任何 LLM API

**与 AAAK 的关系：**
- AAAK 是**独立的压缩层**，用于 wake-up 时的上下文加载
- AAAK**不是存储格式**，存储默认使用 Raw verbatim 模式
- Raw 模式 96.6% > AAAK 模式 84.2%，差距 12.4 个百分点

---

## AAAK 方言（实验性）

### AAAK 是什么？

AAAK（Ant Asset Keyword）是一种**有损**的简化语言，专为 AI 上下文的**唤醒加载**设计：

**设计目标：**
- 在多次会话重复提及同一实体时，通过实体代码减少 token 消耗
- 任何能读文本的 LLM 都能解析，无需解码器

**重要澄清（官方 2026 年 4 月 7 日说明）：**

| 声明 | 实际情况 |
|------|----------|
| "30x 无损压缩" | AAAK 是**有损**的（entity codes、sentence truncation），且在小规模场景下 token 数反而增加 |
| " token 节省示例" | 官方用 OpenAI tokenizer 实测：英文原文 66 tokens，AAAK 压缩后 73 tokens |
| "存储层默认 AAAK" | 存储默认是**Raw verbatim**，AAAK 是可选的压缩层 |

**适用场景：**
- 大规模重复实体：同一团队成员、同一项目在数千次会话中被提及
- 实体代码的边际成本随提及次数降低

### AAAK 的设计原则

| 原则 | 说明 |
|------|------|
| **有损** | 使用正则缩写、实体代码、句子截断 |
| **通用** | 任何 LLM 都能读取，无需解码器 |
| **规模效应** | 重复实体越多，压缩效果越明显 |
| **上下文加载** | 用于 wake-up 时的上下文压缩，不影响存储 |

---

## 四层记忆栈（L0-L3）

```
┌─────────────────────────────────────────────────────────────────┐
│ L0 Identity       │ 身份：这是哪个AI？         │ ~50 tokens  │ 常驻加载  │
│ L1 Critical Facts│ 关键事实：团队/项目/偏好   │ ~120 tokens │ 常驻加载  │
│ L2 Room Recall   │ 房间回忆：近期会话         │ 按需        │ 话题触发  │
│ L3 Deep Search   │ 深度搜索：全量语义检索     │ 按需        │ 显式询问  │
└─────────────────────────────────────────────────────────────────┘
```

**wake-up 后 AI 拥有~170 tokens 的关键上下文，知道你的世界。**

---

## Benchmarks：96.6% R@5

### 标准基准测试

| Benchmark | 模式 | 分数 | API 调用 |
|-----------|------|------|---------|
| **LongMemEval R@5** | Raw (ChromaDB) | **96.6%** | 零 |
| **LongMemEval R@5** | + Haiku 重排 | **100%** | ~500（pipeline 未公开） |
| LoCoMo R@10 | Raw, session level | 60.3% | 零 |
| Personal palace R@10 | Heuristic | 85% | 零 |
| Palace structure | Wing+Room 过滤 | **+34%** | 零 |

### vs 已发布系统

| 系统 | LongMemEval R@5 | 需要 API | 成本 |
|------|-----------------|--------|------|
| **MemPalace (hybrid)** | 100% | 可选 | 免费 |
| Supermemory ASMR | ~99% | 是 | - |
| **MemPalace (raw)** | 96.6% | 否 | 免费 |
| Mastra | 94.87% | 是 (GPT) | API 费用 |
| Mem0 | ~85% | 是 | $19-249/月 |
| Zep | ~85% | 是 | $25/月+ |

### 关于+34%的说明

官方明确指出：**+34%是 ChromaDB 标准 metadata filtering 功能**，不是 MemPalace 独有的检索机制。这是 ChromaDB 的内置特性，用于缩小搜索范围。

---

## MCP Server：19 个工具

### 连接 MemPalace

**方式一：插件市场安装（推荐）**
```bash
claude plugin marketplace add milla-jovovich/mempalace
claude plugin install --scope user mempalace
# 重启Claude Code，输入 /skills 验证 mempalace 出现
```

**方式二：MCP 手动连接**
```bash
claude mcp add mempalace -- python -m mempalace.mcp_server
```

### Gemini CLI 集成

MemPalace 与 Gemini CLI 原生集成，自动处理服务器启动和保存 Hook。详见 [Gemini CLI Integration Guide](https://github.com/MemPalace/mempalace)。

### 19 个工具总览

**Palace 读取工具：**
| 工具 | 功能 |
|------|------|
| `mempalace_status` | Palace 概览+AAAK 规范 |
| `mempalace_list_wings` | 列出所有 Wings |
| `mempalace_list_rooms` | 列出 Wing 内 Rooms |
| `mempalace_get_taxonomy` | 完整分类树 |
| `mempalace_search` | 语义搜索（支持 Wing/Room 过滤） |
| `mempalace_check_duplicate` | 存入前检查重复 |
| `mempalace_get_aaak_spec` | AAAK 方言参考 |

**Palace 写入工具：**
| 工具 | 功能 |
|------|------|
| `mempalace_add_drawer` | 存入原文 |
| `mempalace_delete_drawer` | 删除（按 ID） |

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
| `mempalace_traverse` | 从 Room 穿越 Wings |
| `mempalace_find_tunnels` | 找到连接两个 Wings 的 Rooms |
| `mempalace_graph_stats` | 图连通性概览 |

**Agent Diary 工具：**
| 工具 | 功能 |
|------|------|
| `mempalace_diary_write` | 写 AAAK 日记 |
| `mempalace_diary_read` | 读最近日记 |

---

## 矛盾检测（实验性，未集成）

MemPalace 提供了**独立的**矛盾检测工具 `fact_checker.py`，但**尚未接入知识图谱操作**。这是官方正在修复的问题（跟踪 Issue #27）。

**工具能力演示：**
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

### 分割串联记录

有些对话导出工具会把多个会话合并成一个大文件：

```bash
mempalace split ~/chats/                      # 分割为会话文件
mempalace split ~/chats/ --dry-run            # 预览
mempalace split ~/chats/ --min-sessions 3    # 只分割包含3+会话的文件
```

---

## 实战练习

### 练习一：构建你的第一个 Palace

**目标**：使用 MemPalace 管理一个个人项目的记忆

**步骤**：

1. **初始化项目目录**
```bash
# 创建练习目录
mkdir -p ~/mempalace-practice
cd ~/mempalace-practice

# 初始化MemPalace
mempalace init ~/mempalace-practice
```

2. **创建示例对话文件**
```bash
# 创建模拟对话导出
mkdir -p ~/mempalace-practice/chats
cat > ~/mempalace-practice/chats/session1.txt << 'EOF'
User: 我们决定用PostgreSQL替代MySQL
Assistant: 好的，PostgreSQL对复杂查询支持更好。

User: 什么时候做的这个决定？
Assistant: 2025-11-03。

User: 原因是数据量会超过10GB吗？
Assistant: 是的，而且需要并发写入支持。
EOF
```

3. **挖掘对话**
```bash
mempalace mine ~/mempalace-practice/chats --mode convos --wing practice-project
```

4. **验证存储**
```bash
mempalace status
# 预期：看到practice-project wing和对应room
```

5. **搜索验证**
```bash
mempalace search "database decision"
# 预期：返回PostgreSQL相关的记忆
```

**验收标准**：
- [ ] `mempalace status` 显示新创建的 wing
- [ ] `mempalace list_wings` 能看到 practice-project
- [ ] `mempalace search` 能找到存入的记忆

---

### 练习二：知识图谱时间旅行

**目标**：体验时间敏感的知识图谱查询

**步骤**：

1. **Python 交互式验证**
```python
from mempalace.knowledge_graph import KnowledgeGraph

kg = KnowledgeGraph()

# 添加历史事实
kg.add_triple("Dev", "joined", "Team", valid_from="2025-01-01")
kg.add_triple("Dev", "promoted", "Senior", valid_from="2025-06-01")
kg.add_triple("Dev", "left", "Team", valid_from="2026-01-01")

# 查询当前状态
print("当前状态：", kg.query_entity("Dev"))

# 查询历史状态
print("2025年3月状态：", kg.query_entity("Dev", as_of="2025-03-01"))
print("2025年7月状态：", kg.query_entity("Dev", as_of="2025-07-01"))
```

**验收标准**：
- [ ] 当前状态只显示 Dev 已离开 Team
- [ ] 2025 年 3 月状态显示 Dev 是 Team 成员
- [ ] 2025 年 7 月状态显示 Dev 已被提升为 Senior

---

### 练习三：MCP 工具集成

**目标**：将 MemPalace 连接到 Claude Desktop

**前置条件**：已安装 Claude Desktop 或 Claude Code

**步骤**：

1. **检查 MCP 配置位置**
```bash
# macOS
ls ~/Library/Application\ Support/Claude/claude_desktop_config.json
# 或
ls ~/.config/claude/claude_desktop_config.json
```

2. **添加 MemPalace MCP 服务器**
```json
{
  "mcpServers": {
    "mempalace": {
      "command": "python",
      "args": ["-m", "mempalace.mcp_server"]
    }
  }
}
```

3. **验证连接**
```bash
# 重启Claude Desktop后，输入
/claude mcp list
# 预期：看到mempalace server
```

4. **测试工具调用**
```
Ask: "用mempalace_status查看我的记忆状态"
```

**验收标准**：
- [ ] MCP 配置正确添加
- [ ] Claude 能识别 mempalace 工具
- [ ] 能够调用 mempalace_status 等工具

---

### 练习四：Wing 与 Room 结构化检索

**目标**：体验 Palace 结构带来的精确检索

**步骤**：

1. **创建多 Wing 数据**
```bash
# 项目A的决策
mempalace mine ~/project-a-chats/ --mode convos --wing project-a
# 项目B的决策
mempalace mine ~/project-b-chats/ --mode convos --wing project-b
```

2. **测试范围搜索**
```bash
# 搜索全部（跨Wing）
mempalace search "API设计"

# 限制在project-a
mempalace search "API设计" --wing project-a

# 限制在auth room
mempalace search "API设计" --room auth
```

3. **观察结果差异**
- 全局搜索：返回所有 wing 的相关结果
- Wing 过滤：只返回 project-a 的结果
- Room 过滤：只返回 auth room 的结果

**验收标准**：
- [ ] Wing 过滤显著减少结果数量
- [ ] 同一查询不同过滤器返回不同子集
- [ ] 理解 metadata filtering 的作用

---

### 练习五：Auto-Save Hook 配置

**目标**：配置 Claude Code 自动保存记忆

**步骤**：

1. **定位 Claude Code 配置**
```bash
ls ~/.claude/projects/
# 或项目级
cat ~/.claude/projects/default/.claude.json
```

2. **添加 Hook 配置**
```json
{
  "hooks": {
    "Stop": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "/absolute/path/to/mempalace/hooks/mempal_save_hook.sh"
      }]
    }]
  }
}
```

3. **设置自动摄入目录（可选）**
```bash
export MEMPAL_DIR=~/my-chats
# 这样Hook会自动挖掘指定目录
```

4. **验证 Hook 触发**
```bash
# 在Claude Code中进行多次对话
# 观察Hook是否被触发
tail -f /tmp/mempalace_hook.log
```

**验收标准**：
- [ ] Hook 配置成功加载
- [ ] 对话结束后记忆被保存
- [ ] 自动摄入目录中的新文件被挖掘

---

### 常见问题排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| `mempace: command not found` | 安装失败 | 重新 `pip install mempalace` |
| `mempalace status` 显示空 | 尚未挖掘数据 | 运行 `mempalace mine` |
| MCP 工具不可见 | Claude 未重启 | 完全退出重启 Claude |
| Hook 不触发 | 路径不正确 | 使用绝对路径检查文件存在 |
| ChromaDB 错误 | 版本不兼容 | 检查 Issue #100，固定版本 |

---

## Agent 集成

### Claude Code（推荐）

通过插件市场一键安装，AI 会自动发现和加载 MemPalace 工具集。

### MCP 兼容工具（Claude/ChatGPT/Cursor/Gemini）

```bash
# 连接（只需一次）
claude mcp add mempalace -- python -m mempalace.mcp_server
```

现在问 AI：
> "What did we decide about auth last month?"

AI 会自动调用`mempalace_search`，获取结果后回答你。你无需输入任何命令。

### 本地模型（Llama/Mistral）

**方法 1：Wake-up 命令**
```bash
mempalace wake-up > context.txt
# 把context.txt粘贴到本地模型的系统提示
```

**方法 2：CLI 搜索**
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

# 事实过期时，标记结束时间
kg.invalidate("Kai", "works_on", "Orion", ended="2026-03-01")
# 后续查询Kai当前工作时，不会返回Orion
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

## 专业 Agent：每个 Agent 有自己的记忆

```bash
~/.mempalace/agents/
├── reviewer.json   # 代码质量、模式、bug
├── architect.json  # 设计决策、权衡
└── ops.json        # 部署、故障、基础设施
```

你的 CLAUDE.md 只需一行：
```
You have MemPalace agents. Run mempalace_list_agents to see them.
```

每个 Agent：
- 有自己的专注领域
- 用 AAAK 写日记，跨会话持久化
- 通过读自己的历史建立专业能力

---

## 自动保存 Hook

两个 Claude Code 的自动保存 Hook：

**保存 Hook** - 每 15 条消息触发一次结构化保存
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

**可选自动摄入**：设置环境变量 `MEMPAL_DIR` 指向某个目录路径，Hook 会在每次触发时自动对该目录运行 `mempalace mine`（Stop 时后台运行，PreCompact 时同步运行）。

---

## 项目结构

```
mempalace/
├── mempalace/              # 核心包
│   ├── cli.py              # CLI入口
│   ├── mcp_server.py       # MCP服务器（19工具）
│   ├── knowledge_graph.py # 时间敏感实体图
│   ├── palace_graph.py     # Room导航图
│   ├── dialect.py          # AAAK压缩（实验性）
│   ├── miner.py            # 项目文件摄入
│   ├── convo_miner.py     # 对话摄入
│   ├── searcher.py        # ChromaDB语义搜索
│   └── onboarding.py      # 引导设置
├── benchmarks/             # 可复现基准测试
│   ├── longmemeval_bench.py
│   ├── locomo_bench.py
│   └── membench_bench.py
├── hooks/                 # Claude Code自动保存
│   ├── mempal_save_hook.sh
│   └── mempal_precompact_hook.sh
├── examples/              # 使用示例
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

| 系统 | LongMemEval | 需要 API | 成本 | 自托管 |
|------|-------------|---------|------|--------|
| **MemPalace (hybrid)** | 100% | 可选 | 免费 | ✓ |
| Supermemory ASMR | ~99% | 是 | - | - |
| **MemPalace (raw)** | 96.6% | 否 | 免费 | ✓ |
| Mastra | 94.87% | 是 | API 费用 | - |
| Mem0 | ~85% | 是 | $19-249/月 | - |
| Zep | ~85% | 是 | $25/月+ | 企业版 |

---

## 官方诚实说明（2026 年 4 月 7 日）

社区在项目发布后数小时内发现了多个问题，官方团队直接回应：

### 已被修正的错误

| 原声明 | 实际情况 |
|--------|----------|
| AAAK 示例"30x 无损压缩" | AAAK 是**有损**的，token 计数有误 |
| LongMemEval 96.6%来自 AAAK 模式 | 96.6%来自**Raw 模式**，AAAK 模式仅 84.2% |
| "+34% palace boost"是独特机制 | 这是 ChromaDB 标准**metadata filtering** |
| 矛盾检测已集成到 KG 操作 | 是独立工具 `fact_checker.py`，**尚未集成** |
| "100% with Haiku rerank"已有 pipeline | 结果真实，但**pipeline 未公开** |

### 仍然成立的结论

- 96.6% R@5（Raw 模式，零 API 调用）已由社区独立复现（M2 Ultra，~5 分钟）
- 完全本地、免费、无订阅、无云端
- Wings/Rooms/Closets/Drawers 架构真实有效

### 官方正在修复

- 重写 AAAK 示例，使用真实 tokenizer 计数
- 添加模式区分文档（raw / aaak / rooms）
- 将 fact_checker.py 接入 KG 操作
- 修复 Issue #100（ChromaDB 版本固定）、#110（Shell 注入）、#74（macOS ARM64）

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

**Wing 配置（~/.mempalace/wing_config.json）：**
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
| **GitHub** | https://github.com/MemPalace/mempalace |
| **Discord** | https://discord.com/invite/ycTQQCu6kn |

---

## 进阶路径

### 学习路径图

```
┌─────────────────────────────────────────────────────────────────┐
│                      MemPalace 学习路径                          │
└─────────────────────────────────────────────────────────────────┘

  初学者 ─────────────────────────────────────────────────────────▶ 进阶
    │                                                           │
    ▼                                                           ▼
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 基础使用 │ → │ 结构设计 │ → │ MCP集成 │ → │ 自动化工 │ → │ 深度定制 │
│         │    │         │    │         │    │         │    │         │
│• 安装    │    │• Wing命名│    │• 19工具 │    │• Hook   │    │• 源码   │
│• init   │    │• Room划分│    │• AI对话 │    │• 自动挖掘│    │• Benchmark│
│• mine   │    │• Hall类型│    │• Agent  │    │• 定时任务│    │• AAAK改进 │
│• search │    │• Tunnel  │    │         │    │         │    │         │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
    │              │              │              │              │
    ▼              ▼              ▼              ▼              ▼
 练习一        练习四         练习三         练习五         官方Issue
 入门           进阶检索       MCP集成        Hook配置        参与贡献
```

---

### 阶段一：基础使用（1-2 天）

**目标**：能够使用 MemPalace 管理个人项目记忆

**学习内容**：
- 安装与初始化
- 基本挖掘与搜索命令
- Palace 状态查看

**推荐资源**：
- 官方 Quick Start 文档
- 练习一：构建你的第一个 Palace

**验收标准**：
- [ ] 能够独立初始化一个新项目
- [ ] 能够挖掘对话并成功搜索
- [ ] 理解 Wing/Room 的基本概念

---

### 阶段二：结构设计（3-5 天）

**目标**：设计适合个人/团队的记忆结构

**学习内容**：
- Wing 命名规范与划分策略
- Room 主题划分与 Hall 类型选择
- Tunnel 跨域连接的价值

**推荐资源**：
- 练习四：Wing 与 Room 结构化检索
- 官方 The Palace 文档

**验收标准**：
- [ ] 能够设计多 Wing 记忆结构
- [ ] 理解不同 Hall 类型的适用场景
- [ ] 能够利用 Tunnel 进行跨域检索

---

### 阶段三：MCP 集成（1-3 天）

**目标**：将 MemPalace 深度集成到 AI 工作流

**学习内容**：
- MCP 协议与工具注册
- 19 个工具的组合使用
- Agent 专业化的实现

**推荐资源**：
- 练习三：MCP 工具集成
- 官方 MCP Tools 文档

**验收标准**：
- [ ] 能够配置 MCP 服务器
- [ ] 能够在 AI 对话中调用 MemPalace 工具
- [ ] 理解 Agent 专业化的价值

---

### 阶段四：自动化（3-7 天）

**目标**：实现完全的自动化记忆管理

**学习内容**：
- Claude Code Hook 配置
- 自动挖掘与定时任务
- MEMPAL_DIR 环境变量使用

**推荐资源**：
- 练习五：Auto-Save Hook 配置
- 官方 Auto-Save Hooks 文档

**验收标准**：
- [ ] 能够配置完整的 Hook 流程
- [ ] 理解自动挖掘的边界
- [ ] 能够设置定时摄入任务

---

### 阶段五：深度定制（持续）

**目标**：根据需求定制 MemPalace

**学习内容**：
- 阅读源码，理解核心模块
- 自定义挖掘器与处理器
- AAAK 方言的改进方向
- 参与开源贡献

**推荐资源**：
- 官方 Benchmarks 文档
- GitHub Issue #27（AAAK 迭代）
- GitHub Issue #100/110/74（已知问题）

**验收标准**：
- [ ] 能够阅读并理解核心源码
- [ ] 能够自定义挖掘逻辑
- [ ] 能够为社区做贡献

---

### 相关项目推荐

| 项目 | 说明 | 适用场景 |
|------|------|----------|
| [Zep](https://www.getzep.com) | 云端记忆服务 | 需要托管服务的团队 |
| [Mem0](https://mem0.ai) | 多层记忆 API | 需要云端 API 的开发者 |
| [Mastra](https://mastra.ai) | AI 开发框架 | 构建完整 AI 应用的团队 |
| [Graphiti](https://github.com/getzep/graphiti) | 时序知识图谱 | 需要复杂时间查询的场景 |

### 延伸阅读

| 资源 | 说明 |
|------|------|
| [ChromaDB文档](https://docs.trychroma.com) | 向量检索的底层原理 |
| [西塞罗记忆宫殿](https://en.wikipedia.org/wiki/Method_of_loci) | Palace 架构的思想起源 |
| [GitHub: MemPalace](https://github.com/MemPalace/mempalace) | 项目源码与最新动态 |

---

## 总结

MemPalace 的核心特征：

1. **Raw verbatim 存储**：96.6%成绩来自 ChromaDB 直存，不做摘要
2. **Palace 结构**：Wings/Halls/Rooms 的组织方式，配合 ChromaDB metadata filtering 实现+34%检索提升
3. **AAAK 压缩层**：有损压缩，用于上下文加载，不是存储格式
4. **完全本地**：SQLite/ChromaDB 存储，无需云端，隐私优先
5. **96.6% LongMemEval R@5**：零 API 调用
6. **MCP 原生**：19 个工具，与 Claude/Cursor/Gemini 无缝集成
7. **免费开源**：MIT 许可证，无隐藏成本

**适用场景：**
- 独立开发者管理多个项目记忆
- 团队负责人管理产品和人员上下文
- AI Agent 的长期记忆
- 本地优先的隐私敏感场景

**MemPalace 让你记住一切，但只加载 AI 需要的。**

---

*本文基于 MemPalace 项目编写，最后更新：2026-04-13*
