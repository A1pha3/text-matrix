---
title: "Claude-Mem：65K Stars的Claude Code持久记忆系统，从架构到实战的全面解析"
slug: claude-mem-persistent-memory-65k-stars
aliases:
    - "/posts/tech/claude-mem-persistent-memory-system-guide/"
date: "2026-04-22T07:25:00+08:00"
description: "全面解析Claude-Mem：开源的Claude Code持久记忆系统，65K Stars，5大生命周期钩子自动捕获上下文，3层搜索工作流节省10x Token，SQLite+Chroma混合存储，支持OpenClaw网关和多种IDE。"
categories: ["技术笔记"]
tags: ["Claude-Mem", "AI记忆", "Claude Code", "向量数据库", "TypeScript", "OpenClaw"]
---

# Claude-Mem：65K Stars的Claude Code持久记忆系统，从架构到实战的全面解析

## 概述

**Claude-Mem** 是为 Claude Code 打造的持久化记忆压缩系统，通过自动捕获编码会话中的工具使用观察、生成语义摘要，并将其注入未来会话，使 Claude 能够在会话结束或重新连接后保持对项目的知识连续性。

> **GitHub**: [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem)
> **Stars**: 65,133 ⭐
> **Forks**: 5,494
> **语言**: TypeScript
> **版本**: 6.5.0
> **许可证**: AGPL-3.0

**"Persistent memory for Claude Code — Context survives across sessions"** —— 让 Claude Code 的上下文跨越会话持久存在。

| 痛点 | 传统方案 | Claude-Mem |
|------|---------|-----------|
| 会话结束上下文丢失 | 手动复制粘贴摘要 | 自动捕获、自动注入 |
| 新会话缺乏背景 | 每次重新解释项目 | 记忆自动传承 |
| 长项目上下文膨胀 | Token 成本高昂 | 3层渐进式披露，节省 10x Token |
| 跨会话搜索困难 | grep 历史记录 | 自然语言语义搜索 |
| 隐私敏感内容 | 难以区分 | `<private>` 标签保护 |

---

## 系统架构

### 核心组件全景

```mermaid
graph TB
    subgraph ClaudeCode["Claude Code 会话"]
        HS[SessionStart Hook]
        UP[UserPromptSubmit Hook]
        PT[PostToolUse Hook]
        ST[Stop Hook]
        SE[SessionEnd Hook]
    end

    subgraph ClaudeMem["Claude-Mem 系统"]
        Install[Smart Install<br/>Pre-Hook]
        Worker[Worker Service<br/>Port 37777]
        SQLite[(SQLite<br/>FTS5 Search)]
        Chroma[(Chroma<br/>Vector DB)]
        Skill[mem-search Skill]
        WebUI[Web Viewer UI<br/>localhost:37777]
    end

    HS --> Worker
    UP --> Worker
    PT --> Worker
    ST --> Worker
    SE --> Worker
    Install --> Worker

    Worker <--> SQLite
    Worker <--> Chroma
    Worker --> Skill
    Worker --> WebUI

    SQLite --> FTS[(Full-Text<br/>Search)]
    Chroma --> Vec[(Vector<br/>Search)]
```

### 5个生命周期钩子

Claude-Mem 通过 5 个生命周期钩子自动捕获会话上下文：

| 钩子 | 时机 | 功能 |
|------|------|------|
| **SessionStart** | 会话开始 | 加载历史记忆、注入上下文 |
| **UserPromptSubmit** | 用户提交提示 | 记录用户意图、更新记忆索引 |
| **PostToolUse** | 工具使用后 | 捕获工具输出、生成观察摘要 |
| **Stop** | 停止时 | 保存检查点、写入会话状态 |
| **SessionEnd** | 会话结束 | 最终摘要、记忆归档 |

### 数据存储架构

```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    project_path TEXT,
    start_time DATETIME,
    end_time DATETIME,
    summary TEXT
);

CREATE TABLE observations (
    id INTEGER PRIMARY KEY,
    session_id INTEGER,
    type TEXT,
    content TEXT,
    file_refs TEXT,
    concept_tags TEXT,
    created_at DATETIME,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE VIRTUAL TABLE observations_fts USING fts5(
    content, concept_tags, file_refs
);
```

---

## 3层搜索工作流

Claude-Mem 提供了独特的 **3层渐进式披露** 搜索模式，避免一次性加载所有记忆，节省约 **10x Token**：

### 工作流设计

```mermaid
sequenceDiagram
    participant User as 用户/AI
    participant Search as search()
    participant Timeline as timeline()
    participant GetObs as get_observations()

    User->>Search: 1. search(query, limit=10)
    Search-->>User: Compact Index (~50-100 tokens/result)
    Note over User: 过滤、选择相关 ID

    User->>Timeline: 2. timeline(observation_ids)
    Timeline-->>User: Chronological Context
    Note over User: 查看时间上下文

    User->>GetObs: 3. get_observations(ids=[123,456])
    GetObs-->>User: Full Details (~500-1000 tokens/result)
    Note over User: 仅获取最终需要的详情
```

### 搜索操作详解

| 操作 | 功能 | Token 消耗 | 适用场景 |
|------|------|-----------|---------|
| **search** | 全文+向量混合搜索 | ~50-100 tokens/result | 快速定位、广泛扫描 |
| **timeline** | 获取观察周围的时间上下文 | ~100-200 tokens | 理解上下文发展 |
| **get_observations** | 获取完整观察详情 | ~500-1000 tokens/result | 深入分析、具体引用 |

### 10种搜索类型

| 搜索类型 | 命令 | 功能 |
|---------|------|------|
| 观察搜索 | `search_observations` | 跨观察的全文搜索 |
| 会话搜索 | `search_sessions` | 跨会话摘要的搜索 |
| 提示搜索 | `search_prompts` | 搜索原始用户请求 |
| 概念搜索 | `search_by_concept` | 按概念标签查找 |
| 文件搜索 | `search_by_file` | 查找引用特定文件的观察 |
| 类型搜索 | `search_by_type` | 按类型查找（决策/bug修复/功能） |
| 最近上下文 | `recent_context` | 获取项目的最近会话上下文 |
| 时间线 | `timeline` | 获取特定时间点周围的时间线 |
| API 帮助 | `api_help` | 获取搜索 API 文档 |

---

## 核心特性详解

### 1. 持久化记忆

Claude-Mem 自动捕获并持久化：

- **工具使用模式**：哪些命令被频繁使用
- **Bug 修复历史**：问题的发现和解决方案
- **架构决策**：关键的技术选型理由
- **项目知识**：领域特定的概念和术语
- **文件变更**：哪些文件被修改及原因

### 2. 渐进式披露（Progressive Disclosure）

Claude-Mem 的核心理念：**按需加载，避免上下文膨胀**

| 层级 | 触发条件 | 内容粒度 |
|------|---------|---------|
| L1: 索引 | 每次搜索 | ~50-100 tokens/result |
| L2: 时间线 | 用户选择后 | ~100-200 tokens |
| L3: 详情 | 明确需要后 | ~500-1000 tokens/result |

### 3. 混合存储：SQLite + Chroma

```mermaid
graph LR
    A[用户查询] --> B[Chroma Vector Search]
    A --> C[SQLite FTS5]
    B --> D[语义相似结果]
    C --> E[关键词匹配结果]
    D --> F[混合排序]
    E --> F
    F --> G[最终结果]
```

- **Chroma**：向量嵌入，支持语义相似性搜索
- **SQLite FTS5**：全文搜索，支持精确关键词匹配
- **混合排序**：综合语义相关性和关键词匹配度

### 4. Web Viewer UI

Claude-Mem 提供本地 Web 界面（http://localhost:37777）：

| 功能 | 说明 |
|------|------|
| 记忆流 | 实时查看观察记录 |
| 搜索界面 | 可视化搜索和过滤 |
| 版本切换 | 切换 Stable/Beta 版本 |
| 设置管理 | 配置 AI 模型、Token 限制等 |

### 5. Privacy Control

```typescript
/* 使用 <private> 标签排除敏感内容 */
/* <private>
   API_KEY=sk-xxx
   </private> */
/* 这段内容不会被存储到记忆系统 */
```

### 6. 多 IDE 支持

Claude-Mem 不仅支持 Claude Code，还支持：

| IDE | 安装方式 |
|-----|---------|
| **Claude Code** | `npx claude-mem install` |
| **Gemini CLI** | `npx claude-mem install --ide gemini-cli` |
| **OpenCode** | `npx claude-mem install --ide opencode` |
| **OpenClaw Gateway** | `curl -fsSL https://install.cmem.ai/openclaw.sh \| bash` |

---

## 安装与配置

### 快速安装

```bash
npx claude-mem install

npx claude-mem install --ide gemini-cli

npx claude-mem install --ide opencode

curl -fsSL https://install.cmem.ai/openclaw.sh | bash
```

### 系统要求

| 组件 | 版本要求 |
|------|---------|
| Node.js | 18.0.0+ |
| Bun | 自动安装 |
| uv | 自动安装（Python 向量搜索） |
| SQLite | 内置 |

### 配置管理

配置文件位置：`~/.claude-mem/settings.json`

```json
{
  "CLAUDE_MEM_MODE": "code",
  "CLAUDE_MEM_MODEL": "claude-sonnet-4-20250514",
  "CLAUDE_MEM_PORT": 37777,
  "CLAUDE_MEM_DATA_DIR": "~/.claude-mem",
  "CLAUDE_MEM_CONTEXT_LIMIT": 4000,
  "CLAUDE_MEM_LOG_LEVEL": "info"
}
```

### 语言模式配置

| 模式 | 语言 | 说明 |
|------|------|------|
| `code` | English | 默认英文模式 |
| `code--zh` | 简体中文 | 中文观察模式 |
| `code--ja` | 日本語 | 日文观察模式 |

---

## 使用指南

### 自然语言查询示例

```
"What bugs did we fix last session?"
"How did we implement authentication?"
"What changes were made to worker-service.ts?"
"Show me recent work on this project"
"What was happening when we added the viewer UI?"
```

### MCP 工具调用

```typescript
search(query="authentication bug", type="bugfix", limit=10)

get_observations(ids=[123, 456])
```

---

## 端到端实战：从安装到查询记忆

以下是一个完整的端到端流程，演示如何在一个真实的 TypeScript 项目中使用 Claude-Mem 建立持久记忆。

### 场景设定

你正在维护一个名为 `task-board` 的 TypeScript 全栈项目。上周你花了三个会话修复了一个 WebSocket 断连重连的 bug，今天你打开新会话需要继续工作。

### Step 1：在项目中安装 Claude-Mem

```bash
cd ~/projects/task-board
npx claude-mem install
```

安装完成后，Claude-Mem 会在项目根目录生成 `.claude/settings.json`，并将 5 个钩子脚本注入 Claude Code 配置中。

```bash
cat .claude/settings.json | grep claude-mem
```

### Step 2：启动 Claude Code 会话，验证记忆注入

```bash
claude
```

会话启动时，Worker Service（`localhost:37777`）自动执行 `SessionStart` 钩子，从 SQLite + Chroma 中检索 `task-board` 项目的历史记忆。Claude 会收到一段类似如下的注入上下文：

```
[Memory Context — task-board]
Recent sessions summary:
- 2026-04-20: Fixed WebSocket reconnection race condition in ws-manager.ts.
  Root cause: event listener not cleaned up before new connection.
  Solution: Added cleanup() method called before each reconnect().
- 2026-04-18: Migrated from socket.io to native WebSocket.
  Decision: reduce bundle size by 12KB gzipped.
- 2026-04-15: Added exponential backoff to retry logic. Max 5 attempts, 30s cap.
```

你不需要做任何操作——Claude 已经"记住"了上几次会话的内容。

### Step 3：在新会话中继续工作

你现在要向 Claude 提问，验证它确实继承了之前的记忆：

```
User: The WebSocket reconnection fix from last time, does it also handle
      the case where the server sends a 1006 close code?

Claude: Based on the memory context, the fix was in ws-manager.ts.
        The cleanup() method is called before each reconnect(), which
        should handle the 1006 case since it tears down all listeners.
        Let me check the current code to confirm...
```

Claude 准确引用了 "cleanup() method called before each reconnect()" 这一记忆条目。

### Step 4：主动搜索特定记忆

当你需要查找某个具体的决策或修复时，可以显式调用搜索：

```
User: /mem-search "What was the bundle size impact of the WebSocket migration?"

Claude-Mem: Found 1 observation:
  [decision] Migrated from socket.io to native WebSocket
  Files: ws-manager.ts, package.json
  Context: Reduced bundle size by 12KB gzipped. Removed socket.io-client
           dependency (32KB → 20KB after migration).
  Session: 2026-04-18
```

### Step 5：使用 Web Viewer UI 浏览记忆流

打开浏览器访问 `http://localhost:37777`，你会看到：

- **记忆流面板**：按时间线展示所有观察记录，每条记录标注类型标签（`bugfix`、`decision`、`feature`）
- **搜索栏**：输入 `WebSocket` 可以过滤出所有相关记忆
- **设置面板**：可以切换语言模式，例如改成 `code--zh` 让后续记忆以中文记录

### Step 6：查看记忆的完整性

关闭 Claude Code 会话时，`SessionEnd` 钩子自动触发，生成最终摘要并归档：

```
[Claude-Mem] Session ended. 8 observations recorded.
             Summary: Continued WebSocket robustness work.
             Memory index updated.
```

下次打开会话时，这 8 条观察会自动出现在注入上下文中。

---

## 与其他记忆系统的对比

### Claude-Mem vs AgentMemory

| 维度 | Claude-Mem | AgentMemory |
|------|------------|-------------|
| **定位** | Claude Code 专用持久记忆 | 通用 Agent 记忆框架 |
| **集成方式** | 5个生命周期钩子自动注入 | Python SDK，手动集成到 Agent 代码 |
| **存储** | SQLite + Chroma（本地优先） | SQLite + Qdrant/Chroma（可切换） |
| **搜索策略** | 3层渐进式披露，Token 感知 | 统一向量检索，无分层 |
| **Token 优化** | 内置 10x Token 节省 | 需用户自行控制返回量 |
| **多 Agent 支持** | 单一 Claude 会话 | 原生支持多 Agent 隔离 |
| **安装复杂度** | 一行 `npx` 命令 | 需编写集成代码 |
| **适用场景** | 个人开发者，Claude Code 用户 | 多 Agent 系统，自定义工作流 |

**选型建议**：如果你只用 Claude Code 做开发，Claude-Mem 开箱即用。如果你在构建一个多 Agent 系统（LangChain/CrewAI 等），AgentMemory 的隔离机制更有优势。

### Claude-Mem vs Mem0

| 维度 | Claude-Mem | Mem0 |
|------|------------|------|
| **定位** | Claude Code 会话记忆 | 通用用户级个性化记忆 |
| **记忆粒度** | 会话级（工具调用、代码变更） | 用户级（偏好、历史交互） |
| **更新策略** | 会话结束时批量归档 | 实时增量更新（每条交互后） |
| **记忆类型** | 决策、bug修复、文件变更 | 用户偏好、事实、事件 |
| **搜索接口** | MCP 工具（search/timeline/get_observations） | REST API + Python/JS SDK |
| **云端支持** | 纯本地 | 本地 + Mem0 Cloud（托管） |
| **隐私模型** | `<private>` 标签本地过滤 | 云端加密 + 用户级隔离 |
| **适用场景** | 代码项目跨会话连续 | 聊天机器人、个性化推荐 |

**选型建议**：Claude-Mem 面向代码项目上下文，Mem0 面向用户画像和个性化。两者的记忆模型本质不同——Claude-Mem 记录"代码变更过程"，Mem0 记录"用户是谁"。

### Claude-Mem vs SuperMemory vs MemGPT

| 特性 | Claude-Mem | SuperMemory | MemGPT |
|------|------------|-------------|--------|
| **Stars** | 65k | 20k | 12k |
| **目标** | Claude Code | 通用知识管理 | 通用 Agent |
| **存储** | SQLite + Chroma | PGlite | SQLite |
| **搜索** | 3层渐进式 | 全文+向量 | 全文 |
| **Token 优化** | 10x 节省 | 无 | 无 |
| **Hook 架构** | 5个钩子 | 无 | 无 |
| **Web UI** | 有 | 无 | 无 |
| **OpenClaw** | 支持 | 不支持 | 不支持 |
| **许可证** | AGPL-3.0 | MIT | MIT |

---

## 架构设计分析

### 设计决策回顾

| 决策 | 权衡 | 选择理由 |
|------|------|---------|
| **3层工作流** | 额外 API 调用 vs Token 节省 | 10x Token 节省，显著降低成本 |
| **SQLite + Chroma** | 双存储复杂度 vs 搜索质量 | 关键词+语义双重保障 |
| **Hook 架构** | 侵入性 vs 自动捕获 | 零人工干预是核心价值 |
| **AGPL-3.0** | 商业限制 vs 开源精神 | 确保社区贡献可见 |

### 可复用的架构经验

1. **渐进式披露优于全量加载**：大上下文场景下的 Token 优化典范
2. **Hook 驱动的自动捕获**：零人工干预的实现模式
3. **混合存储策略**：结构化数据 + 向量搜索的平衡
4. **隐私标签机制**：灵活的内容过滤控制

---

## 故障排除

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 记忆未加载 | 会话开始钩子失败 | 重启 Claude Code |
| 搜索无结果 | Chroma 服务未启动 | 运行 `claude-mem doctor` |
| Token 超出 | 上下文限制 | 调整 `CLAUDE_MEM_CONTEXT_LIMIT` |
| 隐私泄露 | 敏感内容未标记 | 使用 `<private>` 标签 |

---

## 常见问题（FAQ）

**Q1：Claude-Mem 的记忆数据存储在哪里？体积会很大吗？**

记忆数据存储在 `~/.claude-mem/` 目录下，包含 SQLite 数据库文件和 Chroma 向量索引。实际测试表明，一个活跃开发 3 个月的中型项目（日均 2-3 次会话），数据库体积约 50-150MB。你可以在配置中设置 `CLAUDE_MEM_DATA_DIR` 自定义存储路径，也支持定期手动清理旧会话数据。

**Q2：多个项目之间记忆会互相污染吗？**

不会。Claude-Mem 使用 `project_path` 字段隔离不同项目的记忆。每次会话启动时，只加载当前项目路径的历史记忆，不同项目的记忆完全隔离。你可以同时为 10 个项目安装 Claude-Mem，它们各自维护独立的记忆空间。

**Q3：Claude-Mem 如何处理大型代码仓库（1000+ 文件）？**

3层搜索工作流正是为此设计的。第1层只返回紧凑索引（~50-100 tokens/条），不会因为项目文件数量而膨胀。但注意，记忆质量取决于会话中实际操作的代码范围——如果你只修改过 5 个文件，记忆也只会覆盖这 5 个文件，而不是整个仓库。建议在涉及新模块时，主动在会话中解释模块结构，帮助 Claude-Mem 建立更完整的项目知识图谱。

**Q4：AGPL-3.0 许可证影响商业使用吗？**

AGPL-3.0 要求如果你修改了 Claude-Mem 的源码并通过网络提供服务，必须公开修改后的源码。如果你只是在自己的开发环境中安装使用（不修改源码也不对外提供记忆服务），则不受此限制。如果你的公司有严格的许可证合规要求，建议法务团队评估是否可以使用未经修改的 AGPL-3.0 软件作为开发工具。

**Q5：可以用自己的向量数据库替代内置的 Chroma 吗？**

Claude-Mem 当前版本（6.5.0）深度集成 Chroma，没有提供向量数据库的插件式切换接口。如果你需要使用 Qdrant、Weaviate 或 Pinecone，需要修改 Worker Service 源码中的向量存储层。社区有讨论计划在后续版本中抽象向量存储接口，但目前没有明确时间表。

**Q6：Claude-Mem 的 `<private>` 标签在代码中如何正确使用？**

在任意代码文件或配置文件中，用 HTML 注释格式包裹敏感内容即可：

```html
<!-- <private> -->
API_SECRET=prod-key-do-not-leak
<!-- </private> -->
```

PostToolUse 钩子在解析工具输出时，会识别并跳过 `<private>` 标签对之间的所有内容。注意标签必须成对出现，且不区分大小写。这个机制是纯字符串匹配，不会解析语言语法，因此适用于任何文本文件。

**Q7：切换项目后，之前的记忆还能访问吗？**

可以，但需要手动指定。Claude-Mem 默认只加载当前项目路径的记忆。如果你需要跨项目查询，可以通过 Web Viewer UI 的全局搜索功能，或者使用 `search_observations` 工具时不限制 `project_path` 参数来查询所有项目的记忆。这在从旧项目迁移代码到新项目时特别有用。

---

## 自检测试

完成 Claude-Mem 安装后，按以下清单逐项验证：

**1. Worker Service 运行状态检查**

```bash
curl -s http://localhost:37777/health
```

返回 `{"status":"ok"}` 表示 Worker Service 正常运行。如果返回连接拒绝，运行 `claude-mem doctor` 诊断。

**2. 钩子文件完整性检查**

```bash
ls -la .claude/hooks/*.sh | wc -l
```

应该恰好输出 `5`（对应 5 个生命周期钩子）。如果少于 5，重新运行 `npx claude-mem install`。

**3. 会话启动记忆注入验证**

```bash
claude --print "What do you remember about this project?" 2>&1 | head -20
```

如果 Claude-Mem 正常工作，输出中应包含类似 `[Memory Context]` 或历史会话摘要的文本段。如果是全新项目，会显示"no prior memory found"，这也是正常状态。

**4. 记忆写入验证**

在 Claude Code 中执行一个明确的代码操作（例如添加一个新文件或修复一个 bug），然后正常退出会话：

```bash
echo "// test comment" > src/test-mem.ts
# 在 claude 会话中对这个文件做一些操作，然后退出
```

退出后检查记忆数据库：

```bash
sqlite3 ~/.claude-mem/claude-mem.db "SELECT COUNT(*) FROM observations WHERE file_refs LIKE '%test-mem.ts%';"
```

返回值应 >= 1，表示刚才的操作已被记录。

**5. Web Viewer UI 可访问性检查**

```bash
curl -s http://localhost:37777 | head -5
```

应返回 HTML 内容（而不是错误或空响应）。然后手动打开浏览器访问 `http://localhost:37777`，确认记忆流面板有数据显示。

**6. Chroma 向量数据库状态检查**

```bash
curl -s http://localhost:37777/api/search -H "Content-Type: application/json" \
  -d '{"query":"test","limit":1}'
```

返回正常的 JSON 结果（即使空数组 `[]` 也算正常），而不是 `500` 或连接错误。

**7. 多项目隔离验证**

```bash
mkdir -p /tmp/test-project-2 && cd /tmp/test-project-2
npx claude-mem install
# 用 claude 启动一个简短会话后退出
npx claude-mem search --project /tmp/test-project-2
```

返回结果中不应包含你主项目的记忆条目，确认项目隔离生效。

---

## 资源链接

| 资源 | 链接 |
|------|------|
| GitHub | [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem) |
| 官方文档 | [docs.claude-mem.ai](https://docs.claude-mem.ai/) |
| Web UI | http://localhost:37777 |
| Discord | [Join Discord](https://discord.com/invite/J4wttp9vDu) |
| 作者 | [@thedotmack](https://github.com/thedotmack) |