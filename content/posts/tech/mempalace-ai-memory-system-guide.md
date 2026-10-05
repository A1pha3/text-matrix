---
title: "MemPalace：59.4k Stars 的开源 AI 记忆系统，96.6% R@5 零 API 调用"
date: "2026-04-13T10:30:00+08:00"
slug: mempalace-ai-memory-system-guide
github_repo: "MemPalace/mempalace"
source_key: "gh:MemPalace/mempalace"
description: "深度解析 MemPalace：基于记忆宫殿原理的 AI 记忆系统，采用 Wings/Halls/Rooms 结构组织记忆，原始对话逐字存储。默认 ChromaDB 检索、可插拔后端、SQLite 知识图谱，96.6% LongMemEval R@5，零 API 调用，完全本地运行。"
categories: ["技术笔记"]
tags: ["AI记忆", "知识图谱", "MCP"]
draft: false
---

# MemPalace：59.4k Stars 的开源 AI 记忆系统，96.6% R@5 零 API 调用

## 项目概述

**MemPalace** 是由 Milla Jovovich 与 Ben Sigman 发起的开源 AI 记忆系统，核心思路是「基于记忆宫殿（Method of Loci）原理，让 AI 记住一切」。它不依赖云 API、不需要订阅、完全本地运行，在 LongMemEval（长程记忆评估基准）上以纯检索、零 LLM 的方式拿到 **96.6% R@5**。

| 指标 | 数值（2026-10-01 核实） |
|------|------|
| **GitHub Stars** | 59.4k (59,375) |
| **Forks** | 7,564 |
| **贡献者** | 30+（igorls、mvalentsev、bensig、fatkobra 等） |
| **最新版本** | v3.10.0（2026-09-16 发布） |
| **许可证** | MIT |
| **技术栈** | Python 为主，检索后端可插拔，含 Rust 原生向量引擎 |

官方的定位写得很直白："The best-benchmarked open-source AI memory system. And it's free."

**核心特点：**

- **96.6% LongMemEval R@5**：Raw 模式，500 题，全程零 API 调用、零 LLM 参与
- **逐字存储**：对话原文直接入库，不摘要、不提取、不改写
- **完全本地**：数据不出机器，无云端依赖
- **有界唤醒**：wake-up 只加载约 600–900 tokens 的关键上下文，其余按需检索

一个安全提醒，来自官方 README 顶部的置顶警告：MemPalace 没有其他官网，唯一官方渠道是 GitHub 仓库、PyPI 包和文档站 [mempalaceofficial.com](https://mempalaceofficial.com)。`mempalace.tech` 等仿冒域名被确认分发恶意软件（2026 年 4 月 11 日公告，详见 `docs/HISTORY.md`）。

---

## 核心问题：AI 对话记忆的困境

### 对话结束，记忆清零

与 AI 的日常工作对话——每一个决策、每一轮调试、每一次架构取舍——默认随着会话结束而消失。半年下来，这些上下文全部归零。

把历史对话重新塞回上下文窗口并不现实：半年重度使用的对话量远超任何模型的窗口容量。用 LLM 做摘要可以压缩体积，但摘要是有损的——"团队决定迁移到 Clerk"这句话保留了结论，丢掉了为什么否决 Auth0、考虑过哪些备选、定价怎么算的。等半年后需要回溯这些细节时，摘要里已经没有了。

### MemPalace 的取舍

| 方案 | 加载量 | 代价 |
|------|-----------|--------|
| 全部塞进上下文 | 远超窗口容量 | 不可行 |
| LLM 摘要 | 小 | 丢失细节与推理过程 |
| MemPalace wake-up | ~600–900 tokens（L0+L1） | 完整原文都在本地，按需检索 |

MemPalace 的答案是：**存储阶段不做任何有损处理**。全部原文逐字保存，检索时用语义搜索找到相关片段，唤醒时只加载一份有界的关键上下文。摘要留在需要压缩的环节（AAAK，见下文），不碰存储层。

---

## 技术架构解析

### 整体架构：The Palace（记忆宫殿）

MemPalace 借用了古希腊演说家的记忆宫殿法：把信息挂在熟悉的空间位置上，靠位置关系组织检索。映射到软件，就是这套层级结构：

```text
WING: Person（人）
├── Room A ──hall── Room B
│     └──▶ Closet（摘要，指向 Drawer）
│           └──▶ Drawer（原文）
│
tunnel（跨 Wing 连接）
│
WING: Project（项目）
├── Room C ──hall── Room D
      └──▶ Closet ──▶ Drawer
```

### 核心数据结构

| 结构 | 说明 | 示例 |
|------|------|------|
| **Wing** | 一个人或一个项目 | `wing_kai`, `wing_driftwood` |
| **Room** | Wing 内的具体主题 | `auth-migration`, `graphql-switch` |
| **Hall** | 同一 Wing 内房间的连接，按记忆类型分 | `hall_facts`, `hall_events` |
| **Tunnel** | 不同 Wing 之间的跨域连接 | auth 相关房间跨项目连接 |
| **Closet** | 摘要，指向原始内容的指针 | 原文的压缩摘要 |
| **Drawer** | 原始文件，完整原文，永不丢失 | 逐字保存的对话或文档 |

### Hall 类型（记忆分类）

```python
hall_facts        # 已做出的决策
hall_events       # 会议、里程碑、调试
hall_discoveries  # 突破、新洞察
hall_preferences  # 习惯、喜好
hall_advice       # 建议和解决方案
```

### Tunnel 的作用

同一个 Room 主题可能出现在多个 Wing 里，系统会自动建立 Tunnel 把它们连起来：

```python
# auth-migration 这个主题横跨三个 Wing
wing_kai / hall_events / auth-migration
  → "Kai debugged the OAuth token refresh"

wing_driftwood / hall_facts / auth-migration
  → "team decided to migrate auth to Clerk"

wing_priya / hall_advice / auth-migration
  → "Priya approved Clerk over Auth0"
```

查询 auth 相关记忆时，可以顺着 Tunnel 跨 Wing 找全三个人的视角，而不是分别在三个 Wing 里搜三遍。

---

## Raw 模式：96.6% 的真正来源

96.6% 这个分数来自 **Raw 模式（逐字直存）**，而非压缩或摘要：

- **存储一切**：原始对话 verbatim 存入向量库，不做摘要、不做提取
- **语义检索**：让搜索模型找到内容，而不是让 AI 在写入时判断"什么值得记住"
- **零 LLM 干预**：存储与检索主路径不调用任何 LLM API

项目在 `benchmarks/BENCHMARKS.md` 里把这个发现讲得很明白：整个领域都在用 LLM 做记忆提取（Mem0 抽取事实、Mastra 用 GPT 观察对话、Supermemory 跑 agentic 搜索），默认假设是"需要 AI 决定什么值得记"。MemPalace 的基线只是把原话存下来再搜索——因为不丢信息，反而更强。

检索层是可插拔的，接口定义在 `mempalace/backends/base.py`。当前默认与全部官方后端：

| 后端 | 模式 | 安装 |
| ---- | ---- | ---- |
| `chroma`（默认） | 本地内嵌 | 内置 |
| `sqlite_exact` | 本地（NumPy 精确检索） | 内置 |
| `rust_exact` | 本地（Rust 原生向量引擎） | wheel / 编译 |
| `milvus` | 本地 Lite，服务端可选 | `mempalace[milvus]` |
| `qdrant` | 服务端（REST） | 内置 |
| `pgvector` | 服务端（Postgres） | `mempalace[pgvector]` |

通过 `--backend <name>`、环境变量 `MEMPALACE_BACKEND` 或 `config.json` 切换。`rust_exact` 与 `sqlite_exact` 共用同一个 SQLite 文件，切换无需迁移数据。

---

## AAAK 方言（实验性）

### AAAK 是什么

AAAK 是一种**有损**的缩写语言，为 AI 上下文的**唤醒加载**设计：用三字母实体码（`KAI=Kai`）、情绪码、标记位和句子截断来压 token。任何能读文本的 LLM 都能直接解析，不需要解码器。

它与存储层的关系需要特别说清楚，这也是这个项目发布初期被社区抓得最狠的地方：

| 当时的声明 | 实际情况（官方 2026-04-07 说明） |
|------|----------|
| "30x 无损压缩" | AAAK 是**有损**的；官方用 OpenAI tokenizer 实测：英文原文 66 tokens，AAAK 压缩后 73 tokens，小文本反而变贵 |
| "存储层默认 AAAK" | 存储默认是 **Raw verbatim**，AAAK 只是可选的压缩层 |
| "AAAK 模式跑出 96.6%" | 96.6% 来自 **Raw 模式**；AAAK 模式 84.2%，低 12.4 个百分点 |

**适用场景**只有一类：大规模重复实体。同一批团队成员、同一个项目在数百上千次会话里反复出现时，实体码的固定开销才能摊薄。

---

## 四层记忆栈（L0–L3）

```text
L0  Identity        身份：这是哪个 AI         ~50–100 tokens   常驻加载
L1  Essential Story 关键故事：最重要时刻       ~500–800 tokens  常驻加载
L2  Room Recall     房间回忆：按话题检索       ~200–500 tokens  话题触发
L3  Deep Search     深度搜索：全量语义检索     不定             显式询问
```

L0 是一份纯文本身份文件（`~/.mempalace/identity.txt`）；L1 从最近入库的 Drawer 中按重要性挑出约 15 个关键时刻，按 Room 分组，截断在 3200 字符以内；L2、L3 按需触发。典型 wake-up 加载 L0+L1，约 600–900 tokens。

官方文档对这组数字的措辞值得留意：记忆栈的目标是**有界的启动上下文**，而不是某个精确的固定 token 数——具体大小取决于你的身份文件和 L1 选中了什么。重要的问题是"唤醒成本有没有界"，而不是"界画在哪个数字上"。

---

## Benchmarks：两个诚实的数字

### 当前官方口径（v3.10.0，benchmarks/BENCHMARKS.md 可复现）

| Benchmark | 模式 | 分数 | LLM 参与 |
|-----------|------|------|---------|
| **LongMemEval R@5**（500 题） | Raw 语义检索 | **96.6%** | 无 |
| **LongMemEval R@5** | Hybrid v4，held-out 450 题 | **98.4%** | 无 |
| **LongMemEval R@5** | Hybrid v4 + LLM rerank（全 500 题） | ≥99% | 可选（Haiku/Sonnet/minimax-m2.7 均可） |
| LoCoMo R@10（1,986 题） | Raw，session 级 | 60.3% | 无 |
| LoCoMo R@10 | Hybrid v5，session 级 | 88.9% | 无 |
| ConvoMem（250 项） | 平均召回 | 92.9% | 无 |
| MemBench（ACL 2025，8,500 项） | R@5 | 80.3% | 无 |

官方把前两行并称为"两个诚实的数字"：96.6% 是产品故事——免费、私密、零 API key、完全离线；98.4% 是 hybrid 流水线在从未调参的 450 道 held-out 题上的成绩，是与 rerank 方案比较时的合理基准。

至于 rerank 后的 100%：结果文件真实存在，官方也用非 Anthropic 系模型（minimax-m2.7 走 Ollama Cloud）复现过，但从 99.4% 到 100% 的最后一步是盯着三道错题调出来的——`benchmarks/BENCHMARKS.md` 从 2 月起就把这标注为"teaching to the test"。所以 2026 年 4 月 14 日之后，100% 不再出现在任何官方标题里。

### 为什么没有竞品对比表

早期 README 有一张把 MemPalace 与 Supermemory、Mastra、Mem0、Zep 排在一起的成绩单。2026 年 4 月 14 日，社区审计（Issue #875）指出这是一次**指标类别错误**：MemPalace 列的是检索召回率（R@5/R@10，标注的会话有没有进前 5 候选），而竞品发布的多数是端到端 QA 准确率（生成的答案对不对）。两者不可比——检索召回 100% 的系统，QA 准确率可能只有 40%。

官方的处置是把对比表从 README 和官网全部撤下，只保留 `benchmarks/BENCHMARKS.md` 里带警示的历史存档，同时承认 Mem0 ~85%、Zep ~85% 这两个数字查无出处。读老文章时如果看到 MemPalace 与竞品同列的分数表，基本可以判断写于这次更正之前。

另外，早期宣传的"+34% palace boost"（Wing+Room 过滤带来的检索提升）也已撤回：metadata filtering 是向量库的标准功能，不是 MemPalace 独有的检索机制。过滤本身有用，但不是护城河。

---

## MCP Server：45 个工具

### 连接 MemPalace

**方式一：插件市场安装（推荐）**

```bash
claude plugin marketplace add MemPalace/mempalace
claude plugin install --scope user mempalace
# 重启 Claude Code，输入 /skills 验证 mempalace 出现
```

插件自带三个技能：`mempalace`（引导安装与运维）、`mempalace-recall`（回答前先检索）、`mempalace-task`（日志流委托）。

**方式二：MCP 手动连接**

```bash
claude mcp add mempalace -- python -m mempalace.mcp_server
# 或者用内置命令
mempalace mcp
```

### 45 个工具总览

45 个工具覆盖六类能力，完整清单见官方 [MCP Tools Reference](https://mempalaceofficial.com/reference/mcp-tools.html)：

| 类别 | 代表工具 | 功能 |
|------|------|------|
| **Palace 读取** | `mempalace_status`, `mempalace_search`, `mempalace_get_taxonomy` | 概览、语义搜索（支持 Wing/Room 过滤）、分类树 |
| **Palace 写入** | `mempalace_add_drawer`, `mempalace_mine`, `mempalace_sync` | 存原文、挖掘目录、同步、删除 |
| **知识图谱** | `mempalace_kg_query`, `mempalace_kg_add`, `mempalace_kg_invalidate`, `mempalace_kg_timeline` | 实体关系查询（支持时间过滤）、添加事实、标记过期、编年史 |
| **跨 Wing 导航** | `mempalace_traverse`, `mempalace_find_tunnels` | 从 Room 穿越 Wings、找两个 Wing 之间的连接 |
| **Agent 日记** | `mempalace_diary_write`, `mempalace_diary_read` | 写读专业 Agent 的持久日记 |
| **Agent 协作** | logstream 事件与 artifact 交接 | 多 Agent 间协调 |

相比发布初期的 19 个工具，主要扩充在写入路径（`mempalace_mine`、`mempalace_sync`、批量删除）和 Agent 协作（logstream）。

### Gemini CLI 与其他客户端

MemPalace 提供官方的 [Gemini CLI 集成指南](https://mempalaceofficial.com/guide/gemini-cli.html)，自动处理服务器启动和保存 Hook；Cursor IDE、Codex CLI、Antigravity 也有各自的接入文档。

---

## 矛盾检测（计划中，未端到端集成）

矛盾检测的目标是对照知识图谱里的实体事实检查新断言，官方文档演示了预期效果：

```text
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

截至 v3.10.0 的官方状态：代码库里有 `fact_checker.py` 和所需的时间知识图谱原语，但它**还没有作为完整工具接入 CLI 或 MCP 工作流**，官方文档明确标注这是 "planned capability"（计划能力），上面的输出展示的是设计意图而非现有命令行为。这条时间线从发布第一周（Issue #27）延续至今。

---

## 快速开始

### 安装

官方推荐把 CLI 装进隔离环境，避免与系统 Python 的 site-packages 冲突：

```bash
# 推荐：uv
uv tool install mempalace

# 或者 pipx
pipx install mempalace

# 或者在激活的虚拟环境里用 pip
python -m venv .venv && source .venv/bin/activate
pip install mempalace
```

也有 Docker 镜像（多架构，Apple Silicon 原生支持）：

```bash
docker pull ghcr.io/mempalace/mempalace:latest
```

Android/Termux 没有原生支持（ChromaDB 等编译依赖不发布 Android wheel），官方给的是 Debian PRoot 容器方案。

### 初始化与挖掘

```bash
# 初始化
mempalace init ~/projects/myapp

# 挖掘项目代码和文档
mempalace mine ~/projects/myapp

# 挖掘对话导出
mempalace mine ~/chats/ --mode convos

# 挖掘并自动分类（决策/偏好/里程碑/问题）
mempalace mine ~/chats/ --mode convos --extract general

# 搜索
mempalace search "why did we switch to GraphQL"
```

`--mode` 控制挖掘什么（`projects` 项目文件 / `convos` 对话导出），`--extract general` 是可选的自动分类器。

### 分割串联记录

有些对话导出工具会把多个会话合并成一个大文件：

```bash
mempalace split ~/chats/                      # 分割为会话文件
mempalace split ~/chats/ --dry-run            # 预览
mempalace split ~/chats/ --min-sessions 3     # 只分割包含 3+ 会话的文件
```

---

## 实战练习

### 练习一：构建你的第一个 Palace

**目标**：用 MemPalace 管理一个个人项目的记忆。

**步骤**：

1. **初始化目录**

```bash
mkdir -p ~/mempalace-practice/chats
mempalace init ~/mempalace-practice
```

2. **创建示例对话文件**

```bash
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

4. **验证存储与搜索**

```bash
mempalace status
# 预期：看到 practice-project wing 和对应 room

mempalace search "database decision"
# 预期：返回 PostgreSQL 相关的记忆
```

**验收标准**：

- [ ] `mempalace status` 显示新创建的 wing
- [ ] `mempalace search` 能找到存入的记忆

### 练习二：知识图谱时间旅行

**目标**：体验时间敏感的知识图谱查询。

**步骤**：

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

### 练习三：MCP 工具集成

**目标**：将 MemPalace 连接到 Claude Code。

**步骤**：

1. **安装插件并重启**

```bash
claude plugin marketplace add MemPalace/mempalace
claude plugin install --scope user mempalace
```

2. **验证连接**

```bash
claude mcp list
# 预期：看到 mempalace server
```

3. **测试工具调用**

在对话里直接问：

```text
用 mempalace_status 查看我的记忆状态
```

**验收标准**：

- [ ] Claude Code 能识别 mempalace 工具
- [ ] 能够调用 `mempalace_status` 等工具

### 练习四：Wing 与 Room 结构化检索

**目标**：体验 Palace 结构带来的范围检索。

**步骤**：

1. **创建多 Wing 数据**

```bash
mempalace mine ~/project-a-chats/ --mode convos --wing project-a
mempalace mine ~/project-b-chats/ --mode convos --wing project-b
```

2. **对比搜索范围**

```bash
# 全局搜索（跨 Wing）
mempalace search "API设计"

# 限制在 project-a
mempalace search "API设计" --wing project-a

# 再限制 room
mempalace search "API设计" --wing project-a --room auth
```

3. **观察结果差异**：全局搜索返回所有 wing 的相关结果；加 Wing 过滤只返回 project-a；再加 Room 过滤进一步收窄。

**验收标准**：

- [ ] Wing 过滤显著减少结果数量
- [ ] 同一查询不同过滤器返回不同子集

### 练习五：Auto-Save Hook 配置

**目标**：配置 Claude Code 自动保存记忆。

**步骤**：

1. **编辑项目级 Hook 配置** `.claude/settings.local.json`：

```json
{
  "hooks": {
    "Stop": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "/absolute/path/to/mempalace/hooks/mempal_save_hook.sh",
        "timeout": 30
      }]
    }],
    "SessionEnd": [{
      "hooks": [{
        "type": "command",
        "command": "/absolute/path/to/mempalace/hooks/mempal_session_end_hook.sh",
        "timeout": 10
      }]
    }],
    "PreCompact": [{
      "hooks": [{
        "type": "command",
        "command": "/absolute/path/to/mempalace/hooks/mempal_precompact_hook.sh"
      }]
    }]
  }
}
```

2. **设置可选的项目目录追加挖掘**

```bash
export MEMPAL_DIR=~/my-project
# Hook 本来就会自动挖掘对话转录（--mode convos）；
# MEMPAL_DIR 让它每次触发时额外挖掘这个目录的项目文件（--mode projects）
```

3. **验证 Hook 触发**

```bash
# 在 Claude Code 中进行多轮对话后，检查 palace 是否新增 drawer
mempalace status
```

**验收标准**：

- [ ] Hook 配置成功加载
- [ ] 对话结束后记忆被保存（Stop 每 15 条人类消息触发，PreCompact 在压缩前强制保存）

### 常见问题排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| `mempalace: command not found` | 安装失败或不在 PATH | 重新安装；`uv tool install` / `pipx install` 会放到稳定的全局路径 |
| `mempalace status` 显示空 | 尚未挖掘数据 | 运行 `mempalace mine` |
| MCP 工具不可见 | Claude 未重启 | 完全退出重启 |
| Hook 不触发 | 路径不正确 | 使用绝对路径，确认文件存在 |
| ChromaDB 版本冲突 | 依赖漂移 | 查看仓库 Issue 区，固定版本；或改用 Docker |
| Linux 挂载目录 PermissionError | Docker 镜像以 uid 1000 运行 | 让挂载目录对该 uid 可读，不要用 `--user` 绕过 |

---

## Agent 集成

### Claude Code（推荐）

插件市场一键安装后，Claude Code 自动发现并加载 MemPalace 的工具与技能。README 里有一条实用警告：**不接自动保存 Hook 的话，Claude Code 的会话转录 30 天后会过期**——官方为此专门做了一份[保留设置清单](https://mempalaceofficial.com/guide/claude-code-retention.html)：先接 Hook，再备份并回填既有 JSONL 转录（`mempalace mine ~/.claude/projects/ --mode convos`）。

### 其他 MCP 兼容工具

```bash
# 连接一次即可
claude mcp add mempalace -- python -m mempalace.mcp_server
```

之后直接问 AI：

> "What did we decide about auth last month?"

AI 会自动调用 `mempalace_search` 检索后作答，你不需要输入任何命令。

### 本地模型（Llama/Mistral）

```bash
# 方法 1：wake-up 命令生成上下文，粘进系统提示
mempalace wake-up > context.txt

# 方法 2：CLI 搜索，把结果放进提示
mempalace search "auth decisions" > results.txt
```

Python API：

```python
from mempalace.searcher import search_memories
results = search_memories("auth decisions", palace_path="~/.mempalace/palace")
```

---

## 知识图谱：时间敏感的实体关系

知识图谱基于本地 SQLite，每个事实带时间窗口：

```python
from mempalace.knowledge_graph import KnowledgeGraph

kg = KnowledgeGraph()

# 添加三元组（带生效时间）
kg.add_triple("Kai", "works_on", "Orion", valid_from="2025-06-01")
kg.add_triple("Maya", "assigned_to", "auth-migration", valid_from="2026-01-15")
kg.add_triple("Maya", "completed", "auth-migration", valid_from="2026-02-01")

# Kai 现在在做什么？
kg.query_entity("Kai")

# 2026-01-20 那天 Maya 在做什么？
kg.query_entity("Maya", as_of="2026-01-20")

# 项目编年史
kg.timeline("Orion")

# 事实过期时标记结束时间
kg.invalidate("Kai", "works_on", "Orion", ended="2026-03-01")
# 之后的"当前"查询不再返回 Orion，历史查询仍能找到

# 单值事实变化（如"用的哪个模型"）用 supersede 原子替换，而不是先 invalidate 再 add
kg.supersede("Kai", "uses_model", "gpt-4.1", "claude", at="2026-03-02")
```

设计要点：`invalidate` 用于"事实结束了"，`supersede` 用于"事实被替换"——它在一次事务里以同一个时间点关闭旧事实、打开新事实，避免手写 `invalidate` + `add_triple` 时新旧两个事实在同一天里重叠、as-of 查询双双命中的问题。`add_triple` 用于可共存的事实。时间维度是一等公民——"Kai 负责什么"这类问题的答案随提问时间变化，图谱把这点建进了查询接口。

---

## 专业 Agent：每个 Agent 有自己的记忆

每个专家 Agent 在 palace 里有自己的 wing 和日记，运行时通过 `mempalace_list_agents` 按需发现，不占用系统提示词：

```bash
~/.mempalace/agents/
├── reviewer.json   # 代码质量、模式、bug
├── architect.json  # 设计决策、权衡
└── ops.json        # 部署、故障、基础设施
```

在 CLAUDE.md 里加一行即可启用：

```text
You have MemPalace agents. Run mempalace_list_agents to see them.
```

每个 Agent 用 AAAK 写日记、跨会话持久化，靠读自己的历史积累专业上下文。多 Agent 之间通过 logstream 事件和 artifact 交接协作（v3.x 新增）。

---

## 自动保存 Hook

三个 Claude Code / Codex CLI 的自动保存 Hook（Cursor IDE 与 Antigravity 有独立版本，共享同一个 `~/.mempalace/hook_state/` 状态目录）：

| Hook | 触发时机 | 行为 |
|------|---------|------|
| **Save Hook** | 每 15 条人类消息 | 自动挖掘转录（含工具输出），然后阻塞 AI 强制保存主题/决策/引文 |
| **SessionEnd Hook** | 会话正常退出 | 后台补挖掘转录并写日记检查点，不拖慢退出 |
| **PreCompact Hook** | 上下文压缩前 | 紧急保存——在丢失上下文之前强制存下所有内容 |

Hook 是两层捕获：一层直接把 JSONL 转录逐字挖进 palace（连 Bash 输出、构建报错都存），另一层阻塞 AI 并要求它保存逐字工具输出和关键上下文。即使 AI 偷懒只存了摘要，原始记录也已经入库。

对于想按消息粒度入库的场景，官方还提供了 `mempalace sweep <transcript-dir>`：每条用户/助手消息存一个 verbatim drawer，幂等、可断点续跑。

---

## 项目结构

```text
mempalace/
├── mempalace/              # 核心包
│   ├── cli.py              # CLI 入口
│   ├── mcp_server/         # MCP 服务器（45 工具，包结构）
│   ├── backends/           # 可插拔检索后端（chroma/sqlite_exact/…）
│   ├── knowledge_graph.py  # 时间敏感实体图
│   ├── palace_graph.py     # Room 导航图
│   ├── layers.py           # 四层记忆栈
│   ├── dialect.py          # AAAK 压缩（实验性）
│   ├── fact_checker.py     # 矛盾检测原语（未端到端集成）
│   ├── miner.py            # 项目文件摄入
│   ├── convo_miner.py      # 对话摄入
│   ├── searcher.py         # 语义搜索
│   └── onboarding.py       # 引导设置（嵌入模型选择）
├── benchmarks/             # 可复现基准测试
│   ├── longmemeval_bench.py
│   ├── locomo_bench.py
│   ├── convomem_bench.py
│   └── membench_bench.py
├── crates/                 # Rust 原生向量引擎（rust_exact / mempalace-native）
├── hooks/                  # 自动保存 Hook（Claude Code / Codex / Cursor / Antigravity）
├── website/                # 官方文档站源码
└── tests/                  # 测试套件
```

---

## 所有命令参考

```bash
# 安装与更新
uv tool install mempalace         # 推荐（或 pipx install mempalace）
mempalace update                  # 自更新

# 设置
mempalace init <dir>              # 引导设置
mempalace init <dir> --yes        # 非交互模式

# 挖掘
mempalace mine <dir>              # 挖掘项目文件
mempalace mine <dir> --mode convos  # 挖掘对话
mempalace mine <dir> --wing myapp   # 指定 Wing

# 分割
mempalace split <dir>             # 分割串联的记录
mempalace split <dir> --dry-run   # 预览

# 搜索
mempalace search "query"          # 搜索全部
mempalace search "query" --wing myapp  # Wing 内搜索
mempalace search "query" --wing myapp --room auth  # Wing+Room 过滤

# 记忆栈
mempalace wake-up                 # 加载 L0+L1 上下文
mempalace wake-up --wing driftwood  # 项目特定上下文

# 压缩
mempalace compress --wing myapp   # AAAK 压缩（实验性）

# 运维
mempalace status                  # Palace 概览
mempalace audit                   # 评估宫殿组织度（只读）
mempalace sweep <transcript-dir>  # 逐消息入库（幂等）
mempalace repair                  # 索引修复
mempalace mcp                     # 启动 MCP 服务器
```

---

## 使用场景

### 独立开发者管理多个项目

```bash
mempalace mine ~/chats/orion/ --mode convos --wing orion
mempalace mine ~/chats/nova/ --mode convos --wing nova
mempalace mine ~/chats/helios/ --mode convos --wing helios

# 6 个月后：
mempalace search "database decision" --wing orion
# → "Chose Postgres over SQLite because Orion needs concurrent writes
#    and the dataset will exceed 10GB. Decided 2025-11-03."
```

### 团队负责人管理产品

```bash
mempalace mine ~/exports/slack/ --mode convos --wing driftwood
mempalace mine ~/.claude/projects/ --mode convos

mempalace search "Clerk decision" --wing driftwood
# → "Kai recommended Clerk over Auth0 — pricing + developer experience.
#    Team agreed 2026-01-15. Maya handling the migration."
```

---

## 官方诚实说明：两轮更正的完整时间线

MemPalace 发布后数小时内被社区找出多个问题，官方的回应方式是维护一份公开的更正档案 `docs/HISTORY.md`。这个项目处理错误的方式本身值得记录。

### 第一轮：2026-04-07，发布当周的更正

| 原声明 | 实际情况 |
|--------|----------|
| AAAK 示例"30x 无损压缩" | AAAK 是**有损**的，token 计数用的是粗糙启发式而非真 tokenizer；实测 66→73 |
| LongMemEval 96.6%来自 AAAK 模式 | 96.6%来自 **Raw 模式**，AAAK 模式仅 84.2% |
| "+34% palace boost"是独特机制 | 只是 ChromaDB 标准 **metadata filtering** |
| 矛盾检测已集成到 KG 操作 | `fact_checker.py` 是独立工具，未集成 |
| "100% with Haiku rerank"已有 pipeline | 结果真实，当时 pipeline 未公开 |

仍然成立、并经独立复现的结论：96.6% R@5（Raw 模式，零 API）由社区成员 @gizmax 在 M2 Ultra 上 5 分钟内复现（Issue #39）；完全本地、免费、无订阅；Wings/Rooms/Closets/Drawers 架构真实有效。

### 第二轮：2026-04-14，benchmark 表重写（Issue #875）

社区审计发现更根本的问题——**指标类别错误**：检索召回率和竞品的端到端 QA 准确率被放进了同一列。这一轮更正的内容：

- 竞品混比表从 README 和官网全部撤下（BENCHMARKS.md 保留带警示的历史存档）
- "100% with Haiku rerank"不再作为标题数字——最后 0.6% 是盯着三道错题调出来的；诚实口径是 **Hybrid v4 held-out 450 题 98.4%**
- LoCoMo "100% R@10 with top-50 rerank"撤下——top_k=50 时检索阶段按构造返回会话内全部 session，量的是 LLM 阅读理解，不是检索
- Mem0 ~85%、Zep ~85% 承认查无出处
- headline 统一为 **96.6% R@5 raw**，并在 Linux x86_64 上对 v3.3.0 完成了第二次独立复现

一个会写 `docs/HISTORY.md`、把每一处夸大和撤回都留档的项目，在 AI 工具赛道里不多见。这些更正记录本身，比 96.6% 这个数字更能说明这个团队怎么做事。

---

## 安装与配置

### 前置条件

| 依赖 | 版本 |
|------|------|
| Python | 3.9+ |
| chromadb | >= 1.5.4, < 2（pip 自动安装） |
| PyYAML | >= 6.0 |
| 磁盘 | 嵌入模型约 300 MB |

首次使用时 onboarding 会让你选嵌入模型：`embeddinggemma-300m`（多语言，支持 100+ 语言，推荐）或 `all-MiniLM-L6-v2`（仅英语，约 30 MB）。也可以把 embedding 计算交给任意 OpenAI 兼容的 `/v1/embeddings` 端点（LM Studio、llama.cpp、vLLM、Ollama 均可）——端点在本机或局域网时，数据不出你的网络。切换嵌入模型需要 `mempalace repair rebuild-index`（向量空间不同）。

### 配置

**全局配置（~/.mempalace/config.json）：**

```json
{
  "palace_path": "/custom/path/to/palace",
  "collection_name": "mempalace_drawers",
  "backend": "chroma",
  "people_map": {"Kai": "KAI", "Priya": "PRI"}
}
```

项目级配置用 `mempalace.yaml`，实体映射用 `entities.json`；`MEMPALACE_BACKEND`、`MEMPAL_DIR` 等环境变量见官方[配置文档](https://mempalaceofficial.com/guide/configuration.html)。

---

## 项目地址

| 项目 | 地址 |
|------|------|
| **GitHub** | https://github.com/MemPalace/mempalace |
| **文档站** | https://mempalaceofficial.com |
| **PyPI** | https://pypi.org/project/mempalace/ |
| **Discord** | https://discord.com/invite/ycTQQCu6kn |

再次提醒：上述之外的一切域名（尤其 `mempalace.tech`）都是仿冒站点，勿从其下载安装脚本。

---

## 进阶路径

建议按五个阶段推进，每个阶段都有明确的验收线：

**阶段一：基础使用（1–2 天）** — 安装、`init`、`mine`、`search`，能独立初始化一个项目并搜到存入的记忆。对应练习一。

**阶段二：结构设计（3–5 天）** — Wing 命名规范、Room 主题划分、Hall 类型选择、Tunnel 跨域检索。理解"结构是检索的前置投资"这件事。对应练习四。

**阶段三：MCP 集成（1–3 天）** — 插件安装、45 个工具的组合使用、Agent 专业化。对应练习三。

**阶段四：自动化（3–7 天）** — 三个 Hook 的配置与分工、`MEMPAL_DIR` 追加挖掘、`sweep` 逐消息入库、定时任务。对应练习五。

**阶段五：深度定制（持续）** — 读源码（`mempalace/backends/` 的后端契约、`crates/` 的 Rust 引擎）、自定义挖掘器、参与 [benchmarks 复现](https://github.com/MemPalace/mempalace/blob/develop/benchmarks/BENCHMARKS.md)、跟进 Issue 区的 AAAK 迭代。

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
| [ChromaDB 文档](https://docs.trychroma.com) | 默认检索后端的底层原理 |
| [Method of loci](https://en.wikipedia.org/wiki/Method_of_loci) | Palace 架构的思想起源 |
| [docs/HISTORY.md](https://github.com/MemPalace/mempalace/blob/develop/docs/HISTORY.md) | 官方更正与公告档案 |
| [benchmarks/BENCHMARKS.md](https://github.com/MemPalace/mempalace/blob/develop/benchmarks/BENCHMARKS.md) | 全部基准的方法论与复现步骤 |

---

## 总结

MemPalace 的核心特征：

1. **Raw verbatim 存储**：96.6% LongMemEval R@5 来自逐字直存加语义检索，存储路径零 LLM 介入
2. **Palace 结构**：Wings/Rooms/Halls/Tunnels 把"问什么"变成"去哪查"，配合 Wing/Room 过滤收窄搜索范围
3. **Hybrid 流水线**：held-out 98.4% 是加了关键词加权、时间邻近加权后的诚实数字；rerank ≥99% 但不作为卖点
4. **可插拔后端**：从本地 ChromaDB 到 pgvector 六种后端，Rust 原生引擎可选用
5. **AAAK 压缩层**：有损、实验性，只为大规模重复实体场景，不是存储格式
6. **完全本地**：SQLite/向量库都在本机，无云端、无订阅、MIT 许可
7. **MCP 原生**：45 个工具，自动保存 Hook 覆盖 Claude Code/Codex/Cursor

**适用场景**：独立开发者管理多项目记忆；团队沉淀决策与人员上下文；AI Agent 的长期记忆；本地优先的隐私敏感场景。

**不适用**：对存储体积敏感的场景——逐字存储的代价是磁盘占用随对话量线性增长；Android/Termux 原生环境（需走 PRoot 容器）；指望矛盾检测立即可用的场景（该能力尚未端到端交付）。

一句话概括它的设计哲学：**记住一切，但只加载 AI 需要的。**

---

*本文数据核实于 2026-10-01（GitHub API、README v3.10.0、docs/HISTORY.md、mempalaceofficial.com）。*
