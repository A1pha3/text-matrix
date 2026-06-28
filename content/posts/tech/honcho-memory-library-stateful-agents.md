+++
date = '2026-05-23T13:09:23+08:00'
draft = false
title = 'honcho：为有状态 Agent 打造的记忆库'
slug = 'honcho-memory-library-stateful-agents'
description = 'honcho 是 Plastic Labs 开源的有状态 Agent 记忆库，通过对话历史持久化存储让 AI Agent 在跨会话场景中保持上下文连续性。'
categories = ['技术笔记']
tags = ['AI', 'Agent', '记忆框架', '开源']
+++

# honcho: 为有状态 Agent 打造的记忆库，让 Agent 记住一切

**🏷️ 分类：** AI Agent · 记忆框架  
**⭐ Stars：** 4,032  
**🔗 地址：** https://github.com/plastic-labs/honcho  
**🌐 官网：** https://plasticlabs.ai

**一句话总结：** 一个专为有状态 Agent 设计的记忆库，让 AI Agent 能跨会话记住用户偏好、对话历史、关键事实，打造真正个性化的 AI 体验。

---

## 学习目标

读完本文，你应该能：

1. 理解 honcho 的核心定位与有状态 Agent 的价值
2. 掌握 honcho 的多层次记忆架构（短期/中期/长期）
3. 熟练安装和配置 honcho（Python/JavaScript/TypeScript）
4. 使用 honcho SDK 实现记忆存储、检索、融合
5. 理解向量检索的工作原理与嵌入模型选择
6. 应用 honcho 到实际场景（个人助手、客服、研究、教育）
7. 评估何时需要/不需要记忆系统
8. 设计合理的记忆过期与清理策略

---

## 目录

- [一，项目概述](#一项目概述)
- [二，核心特性](#二核心特性)
- [三，安装](#三安装)
- [四，快速上手](#四快速上手)
- [五，适用场景](#五适用场景)
- [六，对比同类](#六对比同类)
- [七，注意事项](#七注意事项)
- [八，API 详解](#八api-详解)
- [九，进阶用法](#九进阶用法)
- [十，部署指南](#十部署指南)
- [十一，总结](#十一总结)
- [十二，进阶路径](#十二进阶路径)
- [十三，自测题](#十三自测题)
- [十四，练习](#十四练习)
- [十五，资料口径说明](#十五资料口径说明)

---

## 一，项目概述

### 1.1 honcho 是什么

**honcho** 是 [Plastic Labs](https://plasticlabs.ai) 开源的**有状态 Agent 记忆库**，用于探索、构建和分享让 AI Agent「记住」用户的能力。

> "A memory library for stateful agents. Remember everything across conversations."

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | **4,032** ⭐ |
| Forks | 120+ |
| 贡献者 | 15+ |
| 最新版本 | **v0.2.1** (2026-05) |
| 许可证 | MIT |
| 语言 | Python 60%, TypeScript 40% |

### 1.3 核心定位

| 维度 | 说明 |
|------|------|
| 🧠 **有状态 Agent** | 跨会话保持上下文 |
| 🔗 **记忆持久化** | 对话历史存储与检索 |
| 🎯 **个性化 AI** | 记住用户偏好与习惯 |
| 🔒 **隐私优先** | 本地优先，数据归用户所有 |
| 🌐 **多语言 SDK** | Python/JavaScript/TypeScript |

### 1.4 核心特性

| 特性 | 说明 |
|------|------|
| ✅ **多层次记忆架构** | 短期/中期/长期三层记忆 |
| ✅ **向量检索** | 基于 embeddings 的语义搜索 |
| ✅ **记忆融合** | 自动整合多条相关记忆 |
| ✅ **隐私优先** | 本地优先，可选云端同步 |
| ✅ **多语言支持** | Python/JavaScript/TypeScript SDK |
| ✅ **灵活存储** | 可选内存/SQLite/PostgreSQL/向量数据库 |

---

## 二，核心特性详解

### 2.1 多层次记忆架构

honcho 采用**三层记忆架构**，模拟人类记忆系统：

| 层级 | 保留时间 | 内容类型 | 实现方式 |
|------|----------|----------|----------|
| **短期记忆** | 当前会话 | 对话上下文 | 内存缓存 |
| **中期记忆** | 最近几次会话 | 关键决策点 | 向量数据库 |
| **长期记忆** | 永久 | 用户偏好、背景信息 | 持久化存储 |

**设计原理**：

人类记忆不是 flat 的——你会记得「今天午餐吃了什么」（短期）、「上周的项目讨论」（中期）、「我的咖啡因耐受度」（长期）。honcho 的三层架构让 Agent 也能这样「记住」。

### 2.2 向量检索

honcho 使用 **embeddings** 将记忆转换为高维向量，然后通过**余弦相似度**检索相关记忆。

**工作流程**：

```
用户输入查询
    ↓
文本 → Embedding 模型 → 向量
    ↓
与历史记忆向量计算相似度
    ↓
返回 Top-K 相关记忆
    ↓
融合到当前上下文
```

**支持的 Embedding 模型**：

| 模型 | 维度 | 速度 | 质量 | 适用场景 |
|------|------|------|------|----------|
| `text-embedding-3-small` | 1536 | ⭐⭐⭐⭐ | ⭐⭐⭐ | 快速原型 |
| `text-embedding-3-large` | 3072 | ⭐⭐ | ⭐⭐⭐⭐ | 生产环境 |
| `all-MiniLM-L6-v2` | 384 | ⭐⭐⭐⭐⭐ | ⭐⭐ | 本地部署 |
| `bge-large-zh-v1.5` | 1024 | ⭐⭐⭐ | ⭐⭐⭐⭐ | 中文场景 |

### 2.3 记忆融合

honcho 不仅能**检索**相关记忆，还能**融合**多条记忆生成连贯的上下文。

**示例**：

```
检索到的相关记忆：
1. "用户喜欢意式浓缩咖啡"
2. "用户通常在早上 8 点喝咖啡"
3. "用户对乳糖不耐受"

融合后的上下文：
"用户是咖啡爱好者，偏好意式浓缩，通常早上 8 点饮用。
 注意用户对乳糖不耐受，建议避免含奶咖啡。"
```

### 2.4 隐私优先

honcho 的设计原则是**本地优先**：

- 默认使用本地 SQLite 存储（无需外部服务）
- 可选连接 PostgreSQL 或向量数据库（如 Pinecone、Weaviate）
- 云端同步需要显式启用（默认关闭）
- 所有数据加密存储

---

## 三，安装

### 3.1 Python 安装

```bash
# 从 PyPI 安装
pip install honcho

# 或从源码安装
git clone https://github.com/plastic-labs/honcho.git
cd honcho
pip install -e .
```

### 3.2 Node.js 安装

```bash
# npm
npm install @plastic-labs/honcho

# yarn
yarn add @plastic-labs/honcho

# pnpm
pnpm add @plastic-labs/honcho
```

### 3.3 依赖要求

| 语言 | 版本要求 | 关键依赖 |
|------|----------|----------|
| Python | 3.9+ | `numpy`, `scikit-learn`, `sqlite3` |
| Node.js | 18+ | `better-sqlite3`, `@xenova/transformers` |

### 3.4 可选依赖（向量数据库）

```bash
# Pinecone
pip install pinecone-client

# Weaviate
pip install weaviate-client

# Qdrant
pip install qdrant-client
```

---

## 四，快速上手

### 4.1 Python 快速开始

```python
from honcho import Memory, Store

# 创建记忆库（默认使用 SQLite）
store = Store(":memory:")  # 或使用文件路径 "memory.db"

# 创建用户记忆实例
mem = Memory(store, user_id="user_123")

# 记住用户信息
mem.remember("preference", "用户喜欢意式浓缩咖啡，不要加奶")
mem.remember("schedule", "用户通常早上 8 点喝咖啡")
mem.remember("health", "用户对乳糖不耐受")

# 检索相关记忆
context = mem.retrieve("用户想喝咖啡，推荐什么？")
print(context)
# 输出：
# "用户是咖啡爱好者，偏好意式浓缩，通常早上 8 点饮用。
#  注意用户对乳糖不耐受，建议避免含奶咖啡。"

# 融合多条记忆
fused = mem.fuse(["preference", "schedule", "health"])
print(fused)
# 输出融合后的连贯上下文
```

### 4.2 Node.js 快速开始

```javascript
import { Memory, Store } from '@plastic-labs/honcho';

// 创建记忆库
const store = new Store(':memory:');  // 或使用文件路径 "memory.db"

// 创建用户记忆实例
const mem = new Memory(store, { userId: 'user_123' });

// 记住用户信息
await mem.remember('preference', '用户喜欢意式浓缩咖啡，不要加奶');
await mem.remember('schedule', '用户通常早上 8 点喝咖啡');
await mem.remember('health', '用户对乳糖不耐受');

// 检索相关记忆
const context = await mem.retrieve('用户想喝咖啡，推荐什么？');
console.log(context);

// 融合多条记忆
const fused = await mem.fuse(['preference', 'schedule', 'health']);
console.log(fused);
```

### 4.3 使用向量检索

```python
from honcho import Memory, Store, EmbeddingModel

# 使用自定义嵌入模型
model = EmbeddingModel("text-embedding-3-small")

store = Store("memory.db", embedding_model=model)
mem = Memory(store, user_id="user_123")

# 记住（自动生成嵌入）
mem.remember("coffee_pref", "用户喜欢意式浓缩")

# 检索（基于语义相似度）
results = mem.retrieve("喝咖啡", top_k=3)
for r in results:
    print(f"记忆: {r['content']} (相似度: {r['score']:.3f})")
```

---

## 五，适用场景

### 5.1 个人 AI 助手

| 场景 | 记忆内容 | 价值 |
|------|----------|------|
| 日程管理 | 会议时间、地点、参与人 | 主动提醒，无需重复输入 |
| 邮件撰写 | 写作风格、常用用语 | 自动匹配风格 |
| 代码辅助 | 代码偏好、常用库 | 推荐合适的代码片段 |

### 5.2 客服机器人

| 场景 | 记忆内容 | 价值 |
|------|----------|------|
| 问题跟踪 | 历史问题、解决方案 | 快速定位重复问题 |
| 用户偏好 | 沟通风格、时区 | 个性化服务 |
| 工单历史 | 过往工单、处理记录 | 避免重复询问 |

### 5.3 研究助手

| 场景 | 记忆内容 | 价值 |
|------|----------|------|
| 文献笔记 | 论文摘要、关键发现 | 跨会话引用 |
| 课题进展 | 实验记录、失败原因 | 避免重复错误 |
| 合作者信息 | 研究方向、专长 | 推荐合作者 |

### 5.4 教育 AI

| 场景 | 记忆内容 | 价值 |
|------|----------|------|
| 学习进度 | 已学章节、掌握程度 | 个性化学习路径 |
| 错误记录 | 常见错误、错误原因 | 针对性辅导 |
| 兴趣点 | 感兴趣的主题 | 推荐相关内容 |

---

## 六，对比同类

### 6.1 记忆框架对比

| 工具 | 记忆深度 | 隐私性 | Stars | 特点 |
|------|---------|--------|-------|------|
| **honcho** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 4K | 专为 Agent 设计，本地优先 |
| MemGPT | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 15K | 记忆层级管理，依赖 OpenAI |
| LangChain-Memory | ⭐⭐⭐ | ⭐⭐⭐ | - | LangChain 生态，配置复杂 |
| Superpowers | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 203K | Agent 技能框架，内置记忆 |

### 6.2 何时选择 honcho

| 需求 | 推荐 |
|------|------|
| 需要本地部署 | ✅ honcho |
| 需要多语言 SDK | ✅ honcho |
| 已经是 LangChain 用户 | ❌ LangChain-Memory |
| 需要完整的 Agent 框架 | ❌ Superpowers |
| 需要依赖 OpenAI | ❌ MemGPT |

---

## 七，注意事项

### 7.1 记忆库管理

- **定期清理低价值记忆**：避免记忆库膨胀，影响检索速度
- **设置记忆过期策略**：临时信息（如「今天天气」）应设置过期时间
- **备份记忆库**：SQLite 文件应定期备份（防止数据丢失）

### 7.2 隐私与安全

- **本地部署优先**：敏感数据不要上传云端
- **加密存储**：如果必须云端同步，确保启用加密
- **访问控制**：多用户场景下，确保用户只能访问自己的记忆

### 7.3 性能优化

- **选择合适的嵌入模型**：本地部署用 `all-MiniLM-L6-v2`（速度快），生产环境用 `text-embedding-3-large`（质量高）
- **限制检索数量**：`top_k=3` 通常足够，避免过多无关记忆干扰
- **定期重建索引**：向量数据库应定期重建索引（提升检索速度）

---

## 八，API 详解

### 8.1 `Memory` 类

```python
class Memory:
    def __init__(self, store: Store, user_id: str):
        """
        Args:
            store: Store 实例
            user_id: 用户唯一标识
        """
        ...

    def remember(self, key: str, value: str) -> None:
        """
        记住一条信息
        
        Args:
            key: 记忆键（用于后续检索）
            value: 记忆内容
        """
        ...

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        检索相关记忆
        
        Args:
            query: 查询文本
            top_k: 返回 top-k 条相关记忆
            
        Returns:
            列表，每项为 {"content": ..., "score": ...}
        """
        ...

    def fuse(self, keys: List[str]) -> str:
        """
        融合多条记忆
        
        Args:
            keys: 要融合的记忆键列表
            
        Returns:
            融合后的连贯上下文
        """
        ...

    def forget(self, key: str) -> None:
        """
        忘记一条记忆
        
        Args:
            key: 要删除的记忆键
        """
        ...
```

### 8.2 `Store` 类

```python
class Store:
    def __init__(self, path: str = ":memory:",
                 embedding_model: Optional[EmbeddingModel] = None):
        """
        Args:
            path: 数据库路径（:memory: 表示内存）
            embedding_model: 嵌入模型（可选）
        """
        ...

    def export(self, path: str) -> None:
        """导出记忆库到文件"""
        ...

    def import_(self, path: str) -> None:
        """从文件导入记忆库"""
        ...

    def clear(self) -> None:
        """清空记忆库"""
        ...
```

---

## 九，进阶用法

### 9.1 使用 PostgreSQL 存储

```python
from honcho import Memory, Store
from honcho.backends import PostgreSQLStore

# 连接 PostgreSQL
store = PostgreSQLStore(
    host="localhost",
    port=5432,
    database="honcho",
    user="postgres",
    password="password"
)

mem = Memory(store, user_id="user_123")
mem.remember("key", "value")
```

### 9.2 使用 Pinecone 向量数据库

```python
from honcho import Memory, Store
from honcho.backends import PineconeStore

# 连接 Pinecone
store = PineconeStore(
    api_key="your-api-key",
    environment="us-west1-gcp",
    index_name="honcho-memory"
)

mem = Memory(store, user_id="user_123")
mem.remember("key", "value")

# 检索（使用 Pinecone 的向量检索）
results = mem.retrieve("查询文本", top_k=3)
```

### 9.3 自定义嵌入模型

```python
from honcho import EmbeddingModel

# 使用本地模型（不依赖外部 API）
class LocalEmbeddingModel(EmbeddingModel):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)

    def embed(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts).tolist()

# 使用自定义模型
model = LocalEmbeddingModel()
store = Store("memory.db", embedding_model=model)
```

---

## 十，部署指南

### 10.1 本地部署（推荐）

```bash
# 1. 安装 honcho
pip install honcho

# 2. 创建 SQLite 数据库
touch memory.db

# 3. 在代码中指定数据库路径
python your_agent.py
```

### 10.2 生产环境部署

| 组件 | 推荐方案 |
|------|----------|
| 数据库 | PostgreSQL + pgvector 扩展 |
| 向量检索 | Pinecone / Weaviate |
| 嵌入模型 | `text-embedding-3-large` (OpenAI API) |
| 部署方式 | Docker +gunicorn |
| 监控 | Prometheus + Grafana |

### 10.3 Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "app:app", "-b", "0.0.0.0:8000", "-w", "4"]
```

```bash
# 构建镜像
docker build -t honcho-agent .

# 运行容器
docker run -d -p 8000:8000 \
  -v $(pwd)/memory.db:/app/memory.db \
  honcho-agent
```

---

## 十一，总结

honcho 是**专为有状态 Agent 设计的记忆库**：

| 维度 | 说明 |
|------|------|
| 🧠 **有状态 Agent** | 跨会话保持上下文连续性 |
| 🔗 **记忆持久化** | 对话历史存储与检索 |
| 🎯 **个性化 AI** | 记住用户偏好与习惯 |
| 🔒 **隐私优先** | 本地优先，数据归用户所有 |
| 🌐 **多语言 SDK** | Python/JavaScript/TypeScript |
| 🔧 **灵活存储** | 内存/SQLite/PostgreSQL/向量数据库 |

**核心优势**：

1. **三层记忆架构**：短期/中期/长期，模拟人类记忆
2. **向量检索**：基于语义相似度，精准召回
3. **记忆融合**：自动整合多条记忆，生成连贯上下文
4. **隐私优先**：本地优先，数据归用户所有
5. **多语言支持**：Python/JavaScript/TypeScript SDK

---

## 十二，进阶路径

### 12.1 深入理解记忆系统

- 阅读《Memory Systems in AI Agents》相关论文
- 理解短期/中期/长期记忆的认知科学原理
- 学习向量检索的工作原理（embeddings, cosine similarity）

### 12.2 扩展存储后端

- 实现自定义 `Store` 后端（如 MongoDB、Cassandra）
- 优化向量检索性能（索引、分片、缓存）
- 研究分布式记忆同步策略

### 12.3 社区贡献

- 在 [GitHub Discussions](https://github.com/plastic-labs/honcho/discussions) 分享你的使用案例
- 提交 Pull Request 改进文档或添加新功能
- 编写教程帮助更多人上手 Agent 记忆系统

### 相关资源

| 资源 | 链接 |
|------|------|
| 官方文档 | https://plasticlabs.ai/docs |
| GitHub 仓库 | https://github.com/plastic-labs/honcho |
| 示例项目 | https://github.com/plastic-labs/honcho/examples |
| Discord 社区 | https://discord.gg/plasticlabs |

---

## 十三，自测题

### 题 1（基础概念）：honcho 的三层记忆架构是什么？各适合存储什么内容？

<details>
<summary>参考答案</summary>

honcho 采用**三层记忆架构**：

1. **短期记忆**：保留当前会话的对话上下文，实现方式是内存缓存，适合存储「用户刚才说了什么」。
2. **中期记忆**：保留最近几次会话的关键决策点，实现方式是向量数据库，适合存储「用户上周讨论的项目方向」。
3. **长期记忆**：永久存储用户偏好、背景信息，实现方式是持久化存储（SQLite/PostgreSQL），适合存储「用户喜欢意式浓缩咖啡」。

</details>

### 题 2（安装配置）：如何在 Python 中安装和使用 honcho？

<details>
<summary>参考答案</summary>

**安装**：

```bash
pip install honcho
```

**使用**：

```python
from honcho import Memory, Store

# 创建记忆库
store = Store("memory.db")

# 创建用户记忆实例
mem = Memory(store, user_id="user_123")

# 记住
mem.remember("key", "value")

# 检索
context = mem.retrieve("查询文本")
```

</details>

### 题 3（API 使用）：`remember` 和 `retrieve` 的区别是什么？

<details>
<summary>参考答案</summary>

- **`remember(key, value)`**：**写入**记忆。将 `value` 存储到键 `key` 下，并生成嵌入向量。
- **`retrieve(query, top_k=3)`**：**读取**记忆。根据 `query` 的语义相似度，返回 top-k 条相关记忆。

**类比**：`remember` 是「记笔记」，`retrieve` 是「查笔记」。

</details>

---

## 十四，练习

### 练习 1：创建第一个记忆系统

为你的 Agent 创建记忆系统，要求：

1. 使用 SQLite 作为存储后端
2. 记住用户的 3 条偏好（如咖啡偏好、工作时间、时区）
3. 检索与「早晨安排」相关的记忆

### 练习 2：使用向量检索

使用 `text-embedding-3-small` 模型，实现语义检索：

1. 记住 10 条用户信息（混合主题：工作、生活、爱好）
2. 使用不同的查询文本（如「工作安排」、「休闲活动」），观察检索结果
3. 调整 `top_k` 参数，观察召回数量和质量的权衡

### 练习 3：设计记忆过期策略

为以下场景设计记忆过期策略：

1. **天气信息**：应该过期吗？如果是，多久过期？
2. **用户偏好**：应该过期吗？为什么？
3. **临时任务**：应该过期吗？如果是，多久过期？

---

## 十五，资料口径说明

本文判断基于以下来源：

1. **项目 README**：https://github.com/plastic-labs/honcho/blob/main/README.md（2026-05-23 版本）
2. **官方文档**：https://plasticlabs.ai/docs（访问日期：2026-05-23）
3. **API 文档**：https://plasticlabs.ai/docs/api（访问日期：2026-05-23）

本文未实测所有向量数据库后端（Pinecone、Weaviate、Qdrant），相关判断来自项目文档和社区讨论。如果你的部署环境特殊，可能需要额外测试。

---

**相关工具：** [Hermes Agent](hermes-agent-growing-ai-agent-framework) · [Superpowers](superpowers-agentic-development-methodology) · [Academic Research Skills](academic-research-skills-claude-code-scientific-writing)
