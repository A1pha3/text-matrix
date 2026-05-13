# Memoir：AI Agent 的"Git"——用版本控制思想彻底重构 AI 记忆系统

> AI 记忆是"全局变量反模式"（Global Variable anti-pattern）。每个生产级 Agent 都会遇到三堵墙：上下文污染、Token 租费、记忆漂移。Memoir 带来了 AI 记忆的版本控制。——项目 README 开篇

在 AI Agent 的世界里，记忆系统长期是个被忽视的角落。开发者把 `CLAUDE.md`、`MEMORY.md` 当作万能记忆仓库，向量数据库被当作救命稻草，但没有人认真想过一个问题：**AI 的记忆需不需要版本控制？**

今天要拆解的项目 `zhangfengcdt/memoir`，正是这个问题的系统性回答。它用 Git 的思想重建 AI 记忆系统，将隐式向量检索替换为显式、可审计、带加密签名的分层记忆存储。截至 2026 年 5 月，已获得 **398 Stars、30 Forks**，支持 Claude Code 和 Codex 两大主流 AI Coding Agent，野心不小。

---

## 1. 问题的本质：AI 记忆的三大灾难

### 1.1 上下文污染（Context Contamination）

每个用 `git checkout` 切换分支的开发者都会遇到这个问题：Agent 在一个分支上学会了"实验性重构模式"，切到稳定分支后，这些模式依然存在于它的记忆里，开始把热修补丁当成重构机会。

这就是**上下文污染**——Agent 的记忆不是分支感知的（branch-aware），它把全局状态当成唯一状态。

### 1.2 Token 租费（Token Rent）

用 `CLAUDE.md` 或 `MEMORY.md` 作为全局存储，每次小幅更新都会让整个前缀缓存失效。下一次对话开始时，Agent 不得不重新处理整个对话历史的全量 Token——这是"Token 租费"，你每次都在为上一次的记忆付全款。

### 1.3 记忆漂移（Memory Drift）

向量数据库和 scratchpad 式的记忆本质上是**只可追加的 Blob**。一次糟糕的会话会污染整个记忆存储。没有 `memoir blame` 或 `memoir checkout`，既无法审计"是谁教给 Agent 这个规则"，也无法在不使用全量擦拭的情况下回滚一个幻觉。

**Memoir 的核心论点**：这三个问题本质上都源于同一个缺失——**AI 记忆没有版本控制**。

---

## 2. 核心概念：Git for AI Memory

Memoir 的设计哲学是把 Git 的成功经验引入 AI 记忆管理。Git 解决了代码协作的三个核心问题：版本历史、可审计的变更、并行分支——Memoir 把这三个能力带给 AI 记忆。

### 2.1 分层语义路径（Semantic Paths）替代 UUID

传统记忆系统用向量相似度匹配来检索记忆，本质上是"猜"。Memoir 用**语义路径**替代 UUID key，让记忆有可读的结构：

```
profile.professional.skills.python      # 可读，可预测
memories/occupation/techcorp/engineer  # 同样可读
```

这些路径构成了一个**语义树**（Semantic Taxonomy），预定义了约 200 个固定路径，Agent 和用户都可以直接引用。

### 2.2 记忆聚合（Memory Aggregation）

Memoir 不是把每条记忆独立存储，而是把相关记忆**聚合在语义路径下**：

```
# 传统方式
uuid-1234-5678 → "I work at TechCorp"
uuid-9876-5432 → "I'm a software engineer"
uuid-1111-2222 → "I've been coding for 5 years"

# Memoir 方式
profile.professional.occupation → {
  "memories": [
    {"content": "I work at TechCorp", "confidence": 0.95},
    {"content": "I'm a software engineer", "confidence": 0.87},
    {"content": "I've been coding for 5 years", "confidence": 0.82}
  ],
  "count": 3,
  "last_updated": "2024-01-15"
}
```

同一路径下的多条记忆可以被统一处理、聚合查询，不需要逐条扫描。

### 2.3 Git 式版本控制

每一条记忆操作都是一次**commit**，完整的历史链用 SHA-256 加密签名保证完整性。支持完整的 Git 式操作：

- `memoir branch` — 创建记忆分支
- `memoir commit` — 提交记忆变更
- `memoir merge` — 合并分支记忆
- `memoir checkout` — 切换记忆分支
- `memoir blame` — 审计记忆变更来源

---

## 3. 系统架构：四层分离的清洁架构

Memoir 的架构文档中有一句关键表述：**"Dependency Injection: Clean separation of concerns"**。整个系统分为四层，每层各司其职，通过依赖注入组合。

```
┌──────────────────────────────────────┐
│       Memory Manager (编排层)          │
│  - 事务管理                          │
│  - 版本控制                          │
│  - 性能监控                          │
└──────┬─────────┬─────────┬────────────┘
       │         │         │
 ┌─────▼──┐ ┌───▼────┐ ┌──▼──────────┐
 │存储层   │ │分类层   │ │搜索引擎层    │
 │Store   │ │Classifr │ │Search Eng.  │
 │        │ │        │ │             │
 │Prolly  │ │Semantic│ │Intelligent  │
 │Tree    │ │Taxonomy│ │Breadth/Depth│
 └────────┘ └────────┘ └─────────────┘
```

### 3.1 存储层（Storage Layer: `memoir.store`）

核心数据结构是基于 **ProllyTree** 的版本化键值存储。

**ProllyTree**（Probabilistic B-Tree）是一种自平衡的树结构，专门为键值存储场景优化。与传统 B-Tree 的区别在于：它的平衡是"概率性的"而非确定性的，这使得它在写入密集型场景下性能更好，维护成本更低。

Memoir 的存储层核心能力：
- SHA-256 加密签名保证完整性
- O(log n) 前缀搜索
- 分支感知的版本历史
- 记忆聚合（同一路径下的记忆自动聚合）

```python
from memoir.store.prolly_adapter import ProllyTreeStore

store = ProllyTreeStore(
    path="./memory_store",
    enable_versioning=True,
    cache_size=10000
)
```

### 3.2 分类层（Classification Layer: `memoir.classifier`）

分类层决定"这条记忆应该放在哪个路径下"。Memoir 实现了两级分类器：

**SemanticClassifier（快速分类器）**
- 基于预定义模式的快速匹配，延迟仅 **1-5ms**
- 无需 LLM 调用，不消耗 API 配额
- 适合结构明确的记忆（如编程偏好、时间格式）

**IntelligentClassifier（智能分类器）**
- LLM 驱动，动态扩展 taxonomy
- 延迟 **100-500ms**（含 LLM 调用）
- 置信度阈值可配置：
  - `high (≥0.8)`：自动存储
  - `medium (≥0.5)`：待审核
  - `low (<0.5)`：拒绝

```python
from memoir.classifier.intelligent import IntelligentClassifier

classifier = IntelligentClassifier(
    llm=llm,
    confidence_thresholds={
        "high": 0.8,
        "medium": 0.5,
        "low": 0.0
    }
)
```

### 3.3 搜索引擎层（Search Engine Layer: `memoir.search`）

Memoir 的搜索不依赖向量相似度，而是采用了更聪明的路径选择 + 树结构检索：

**IntelligentSearchEngine**：
- LLM 先理解查询意图，选择合适的语义路径
- 在选定的路径范围内做 O(log n) 树搜索
- 支持多种策略：广度优先、深度优先、最佳匹配

性能对比（来自架构文档）：

| 搜索方式 | 平均延迟 |
|---------|---------|
| 语义搜索（Pattern） | 0.1-1ms |
| 智能搜索（LLM） | 100-500ms |
| 传统向量搜索 | 150-750ms |

### 3.4 记忆管理器（Memory Manager: `memoir.core`）

编排层，通过依赖注入组合上述三层：

```python
from memoir.core.memory import ProllyTreeMemoryStoreManager

memory_manager = ProllyTreeMemoryStoreManager(
    prolly_store=store,        # 注入的存储
    classifier=classifier,     # 注入的分类器
    search_engine=search_engine # 注入的搜索引擎
)
```

---

## 4. Taxonomy 系统：约 200 个预定义路径

Memoir 内置了一个约 200 个预定义路径的语义分类体系，核心结构：

```
profile.
├── identity.
│   ├── name.{first,last,full}
│   └── demographics.{age,location}
├── professional.
│   ├── occupation.{role,company}
│   └── skills.{technical,soft}
└── personal.
    ├── interests.{hobbies,sports}
    └── relationships.{family,friends}
```

**固定 Taxonomy** 的价值在于：
1. 快速模式匹配，不需要 LLM 调用
2. 一致性保证，记忆永远不会"迷路"
3. 可预测的路径结构，便于 Agent 引用

**动态 Taxonomy** 则允许 LLM 在固定 taxonomy 无法覆盖时动态扩展路径。

---

## 5. CLI 使用详解：五命令掌握核心流程

Memoir 的 CLI 设计极其简洁，5 个核心命令覆盖完整流程：

### 5.1 `memoir new` — 创建记忆仓库

```bash
memoir new my-memoir-store
cd my-memoir-store
```

等价于 `git init`，初始化一个本地 `.memoir/` 目录。

### 5.2 `memoir remember` — 存储记忆

两种模式：

**显式路径模式**（离线，无需 LLM）：
```bash
memoir remember "Sarah prefers tabs and 2-space indents" -p preferences.coding.style
```

**自动分类模式**（需要 LLM API Key）：
```bash
memoir remember "I work in Pacific time"
# LLM 自动选择路径，输出类似 "profile.identity.location.timezone"
```

### 5.3 `memoir get` — 按路径读取

```bash
memoir get preferences.coding.style
# 返回该路径下聚合的所有记忆（离线，O(log n)）
```

### 5.4 `memoir recall` — 语义搜索

```bash
memoir recall "what does Sarah prefer?"
# LLM 解析意图 → 选择路径 → 搜索 → 返回聚合结果
```

支持 `--model` 参数切换模型，默认使用 `claude-haiku-4-5`。

### 5.5 `memoir ui` — 可视化浏览器

```bash
memoir ui
# 自动在浏览器打开，支持 Tree/Graph/Timeline/Places 四种视图
```

---

## 6. Claude Code 与 Codex 插件：从工具到基础设施

Memoir 最有战略价值的部分，是它对 **Claude Code** 和 **Codex** 的深度集成——这意味着它不是一个独立的记忆工具，而是被嵌入了 AI Coding Agent 的工作流。

### 6.1 Claude Code 插件

```bash
# 在 Claude Code 会话中
/plugin marketplace add zhangfengcdt/memoir
/plugin install memoir@memoir
```

插件会自动注册三个 **lifecycle hooks**：
- `session start`：注入历史记忆到上下文
- `user-prompt-submit`：自动捕获关键记忆
- `stop`：持久化本次会话产生的记忆

不需要手动 `pip install`，只要 PATH 上有 `uv` 即可自动解析到 `uvx --from memoir-ai memoir`。

### 6.2 Codex 插件

配置方式类似，在 Codex 中注册 marketplace：

```bash
codex plugin marketplace add zhangfengcdt/memoir
```

Codex 插件额外包含：
- `memory-recall`、`memoir-onboard`、`memoir-remember`、`memoir-status`、`memoir-ui` 等 **5 个 Skills**
- Codex 特定的 transcript 解析
- 生命周期 hooks：`memory-recall`、`memoir-onboard`、`memoir-remember`

需要在 `~/.codex/config.toml` 中启用 `[features].hooks = true`。

---

## 7. 技术亮点与工程细节

### 7.1 ProllyTree：写入密集型场景的更好选择

传统的 B-Tree 维护平衡是精确的（所有叶子深度相同），但这意味着每次写入都可能触发再平衡，代价较高。ProllyTree 使用概率性平衡，允许叶子深度有一定分布差异，这使得它在**写入密集型场景**（这正是 Agent 记忆的特点）下性能更好、维护成本更低。

### 7.2 SHA-256 加密签名

所有 commit 都附带 SHA-256 哈希，这意味着记忆历史是不可篡改的。任何人无法在不留痕迹的情况下修改历史。这对于需要合规审计的场景（医疗、金融、法律）尤其有价值。

### 7.3 多搜索引擎架构

Memoir 的搜索层被设计为**可插拔**的：
- `KeywordSearchEngine`：纯关键词匹配，0.1-1ms 延迟
- `IntelligentSearchEngine`：LLM 驱动的语义路径选择
- 未来可以接入任何自定义搜索引擎

### 7.4 分支感知（Branch-Aware）

这是 Memoir 与其他 AI 记忆工具（如 Cline 的 memory、Continue 的记忆系统）最本质的区别。它真正理解 `git branch` 的语义：

```
main branch
│
├─ commit: "Initial user profile"
│  └─ memories: profile.identity.*
│
├─ commit: "Added work info"
│  └─ memories: profile.professional.*
│
└─ branch: experiment
   ├─ commit: "Testing new classifier"
   └─ merge → main
```

Agent 在 `experiment` 分支上的实验性规则，不会污染 `main` 分支的生产环境记忆。

---

## 8. 性能实测数据（来自官方 benchmarks）

Memoir 的架构文档给出了明确的性能数据：

| 操作 | 耗时 |
|------|------|
| 记忆分类（Pattern） | 1-5ms |
| 记忆分类（LLM） | 100-500ms |
| 存储操作 | 20-30ms |
| 版本控制操作 | 50-100ms |
| 语义搜索 | 0.1-1ms |
| 智能搜索 | 100-500ms |
| 可扩展规模 | 最高 100 万条记忆 |

---

## 9. 竞争格局：为什么现有的方案都是"半成品"？

| 方案 | 记忆组织 | 版本控制 | 分支感知 | 语义路径 |
|------|---------|---------|---------|---------|
| `CLAUDE.md` / `MEMORY.md` | 扁平文件 | ❌ | ❌ | ❌ |
| 向量数据库 (Pinecone etc.) | 向量相似度 | ❌ | ❌ | ❌ |
| Cursor Memory | 会话级 | ❌ | ❌ | ❌ |
| **Memoir** | 分层语义树 | ✅ | ✅ | ✅ |

所有现有方案的共同缺陷：**记忆是"追加式 Blob"**。Memoir 第一次把"代码的版本控制"这个经过五十年实践检验的思想，系统性地引入 AI 记忆领域。

---

## 10. 适用场景与局限性

**最佳场景：**
- 长期运行的 AI Coding Agent（Claude Code / Codex 用户）
- 需要记忆审计能力的合规场景（医疗、金融、法律）
- 多 Agent 协作环境（Memoir 明确支持多 Agent 会话）
- 需要在分支间隔离实验性规则的开发工作流

**当前局限性：**
- Alpha 状态，生产环境使用需谨慎
- LLM 驱动的智能分类依赖 API Key 和网络
- 默认模型 `claude-haiku-4-5` 对复杂分类场景可能不够强
- 依赖 uv 作为运行时管理器，对非 uv 用户有一定门槛

---

## 总结

Memoir 是一个**概念先于实现**的项目。它的核心贡献不是某个算法突破，而是一个思维框架的升级：**AI 记忆应该像代码一样被管理**。

Git 解决了"代码为什么需要版本控制"这个问题，花了十年才成为开发者的肌肉记忆。AI 记忆的版本控制意识才刚刚觉醒——Memoir 是这个方向的先驱探索者。

对于已经在用 Claude Code 或 Codex 的开发者，Memoir 是目前最完整的 Agent 记忆解决方案。对于构建 AI Agent 基础设施的工程师，Memoir 的架构设计（分层 + 依赖注入 + 可插拔搜索引擎）本身就是一份高质量的参考实现。

---

**项目信息**

- **仓库**：[zhangfengcdt/memoir](https://github.com/zhangfengcdt/memoir)
- **Stars**：398 ⭐ | **Forks**：30
- **官网**：[memoir-ai.dev](https://www.memoir-ai.dev/)
- **文档**：[zhangfengcdt.github.io/memoir](https://zhangfengcdt.github.io/memoir/)
- **许可证**：Apache 2.0
- **语言**：Python

🦞 每日 21:00 自动更新