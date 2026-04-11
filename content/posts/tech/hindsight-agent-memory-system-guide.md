# Hindsight：Agent记忆系统·最准确的记忆系统·SOTA性能·8.9K Stars

## 一、项目概述

### 1.1 Hindsight 是什么

**Hindsight™** 是专为 AI Agent 设计的**记忆系统**，让 Agent 不仅能记住对话历史，更能从经验中学习。

> "Hindsight™ is an agent memory system built to create smarter agents that learn over time. Most agent memory systems focus on recalling conversation history. Hindsight is focused on making agents that learn, not just remember."

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | **8.9k** ⭐ |
| Forks | 529 |
| 贡献者 | 66 |
| 最新版本 | v0.5.0 (2026-04-08) |
| 提交数 | 924 commits |
| 许可证 | MIT |
| 语言 | Python 71.0%, TypeScript 15.8%, MDX 5.4% |

### 1.3 核心定位

| 维度 | 说明 |
|------|------|
| 🧠 **记忆系统** | Agent 的记忆系统，不是 Agent 本身 |
| 📊 **SOTA 性能** | LongMemEval 基准测试最优 |
| 🔄 **持续学习** | 不仅记住，更能学习 |
| 🌐 **多 LLM 支持** | OpenAI、Anthropic、Gemini 等 |
| 🐍 **双语言** | Python + TypeScript SDK |

### 1.4 性能表现

Hindsight 在 **LongMemEval** 基准测试中达到**最优性能**，由 Virginia Tech Sanghani Center 研究团队**独立复现验证**。

## 二、为什么选择 Hindsight

### 2.1 对比 RAG 和 Knowledge Graph

| 技术 | 说明 |
|------|------|
| **RAG** | 简单向量检索，无法捕获时间关系和因果 |
| **Knowledge Graph** | 结构化，但难以处理复杂推理 |
| **Hindsight** | 生物启发的记忆结构，State-of-the-art |

### 2.2 Hindsight 的三大创新

| 创新 | 说明 |
|------|------|
| 🌍 **World Memories** | 世界事实（"炉子是烫的"） |
| 📖 **Experience Memories** | 亲身体验（"我摸过炉子，很烫"） |
| 💡 **Mental Models** | 从记忆中形成的理解 |

### 2.3 核心优势

| 优势 | 说明 |
|------|------|
| ⚡ **2 行代码** | LLM Wrapper 轻松集成 |
| 🔍 **多检索策略** | 语义 + 关键词 + 图 + 时间 |
| 📈 **State-of-the-art** | LongMemEval 基准最优 |
| 🏢 **生产验证** | Fortune 500 企业使用 |
| 🌐 **多 Provider** | OpenAI / Anthropic / Gemini / Groq / Ollama |

## 三、快速开始

### 3.1 Docker 部署（推荐）

```bash
# 设置 API Key
export OPENAI_API_KEY=sk-xxx

# 启动 Hindsight
docker run --rm -it --pull always -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_API_KEY=$OPENAI_API_KEY \
  -v $HOME/.hindsight-docker:/home/hindsight/.pg0 \
  ghcr.io/vectorize-io/hindsight:latest
```

**访问地址：**
- API: http://localhost:8888
- UI: http://localhost:9999

### 3.2 使用外部 PostgreSQL

```bash
export OPENAI_API_KEY=sk-xxx
export HINDSIGHT_DB_PASSWORD=choose-a-password
cd docker/docker-compose
docker compose up
```

### 3.3 更改 LLM Provider

```bash
docker run ... -e HINDSIGHT_API_LLM_PROVIDER=anthropic ...
```

**支持的 Provider：** `openai`, `anthropic`, `gemini`, `groq`, `ollama`, `lmstudio`, `minimax`

### 3.4 安装客户端

```bash
# Python
pip install hindsight-client -U

# Node.js / TypeScript
npm install @vectorize-io/hindsight-client
```

## 四、Python SDK

### 4.1 基本用法

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

# Retain: 存储记忆
client.retain(
    bank_id="my-bank",
    content="Alice works at Google as a software engineer"
)

# Recall: 检索记忆
results = client.recall(
    bank_id="my-bank",
    query="What does Alice do?"
)

# Reflect: 深度反思
insights = client.reflect(
    bank_id="my-bank",
    query="Tell me about Alice"
)
```

### 4.2 带上下文和时间戳

```python
# 带上下文
client.retain(
    bank_id="my-bank",
    content="Alice got promoted to senior engineer",
    context="career update",
    timestamp="2025-06-15T10:00:00Z"
)

# 时间范围检索
results = client.recall(
    bank_id="my-bank",
    query="What happened in June?"
)
```

### 4.3 LLM Wrapper（2 行代码）

```python
# 最简单的集成方式 - 替换现有 LLM Client
from hindsight import HindsightWrapper

# 替换你的 LLM Client
wrapper = HindsightWrapper(
    llm_provider="openai",
    llm_model="gpt-4o-mini"
)
# 之后所有的 LLM 调用都会自动存储和检索记忆
```

## 五、Node.js / TypeScript SDK

### 5.1 基本用法

```javascript
const { HindsightClient } = require('@vectorize-io/hindsight-client');

const client = new HindsightClient({
    baseUrl: 'http://localhost:8888'
});

// 存储记忆
await client.retain('my-bank', 'Alice loves hiking in Yosemite');

// 检索记忆
const results = await client.recall('my-bank', 'What does Alice like?');
console.log(results);

// 深度反思
const insights = await client.reflect('my-bank', 'Tell me about Alice');
```

## 六、三大核心操作

### 6.1 Retain（记忆存储）

**Retain** 操作将新记忆推入 Hindsight 系统：

```python
client.retain(
    bank_id="my-bank",
    content="Alice works at Google"
)
```

**背后发生了什么：**
1. LLM 提取关键事实、时间数据、实体、关系
2. 标准化处理转化为规范实体、时间序列、搜索索引
3. 创建用于后续检索的路径

### 6.2 Recall（记忆检索）

**Recall** 操作从记忆库检索信息：

```python
results = client.recall(
    bank_id="my-bank",
    query="What does Alice do?"
)
```

**四种检索策略并行执行：**
| 策略 | 说明 |
|------|------|
| 🔍 **Semantic** | 向量相似度 |
| 📝 **Keyword** | BM25 精确匹配 |
| 🔗 **Graph** | 实体/时间/因果关系 |
| ⏰ **Temporal** | 时间范围过滤 |

**结果合并：** 使用 Reciprocal Rank Fusion 合并结果，Cross-encoder 重排

### 6.3 Reflect（深度反思）

**Reflect** 操作对记忆进行深度分析：

```python
insights = client.reflect(
    bank_id="my-bank",
    query="What should I know about Alice?"
)
```

**典型应用场景：**
| Agent 类型 | Reflect 用例 |
|-----------|-------------|
| 🤖 **AI 项目经理** | 反思项目风险 |
| 💼 **销售 Agent** | 反思哪些消息有回复、哪些没有 |
| 🎧 **支持 Agent** | 反思产品文档未回答的客户问题 |

## 七、使用案例

### 7.1 每用户记忆和聊天历史

**最简单的用例** - 为 AI 聊天机器人和对话 Agent 提供个性化记忆：

```python
# 存储带元数据的记忆
client.retain(
    bank_id="user-123",
    content="User prefers email over phone calls",
    metadata={"channel": "email", "user_id": "user-123"}
)

# 检索时过滤特定用户
results = client.recall(
    bank_id="user-123",
    query="User communication preferences?"
)
```

### 7.2 AI 员工

Hindsight 非常适合需要处理开放式任务、根据用户反馈改变行为、学习执行复杂任务的 **AI 员工**：

| 场景 | 说明 |
|------|------|
| 🤖 **AI 同事** | 记住项目上下文、团队偏好 |
| 📊 **AI 项目经理** | 反思风险、学习用户反馈 |
| 💬 **AI 销售** | 优化沟通策略 |

### 7.3 AI Agent 集成

```python
# 与 n8n、LangChain 等工作流集成
from hindsight import HindsightWrapper
from langchain.agents import initialize_agent

# 创建带记忆的 Agent
wrapper = HindsightWrapper(llm_provider="openai")
agent = initialize_agent(
    tools=[],
    llm=wrapper,
    memory=wrapper.get_memory()
)
```

## 八、架构设计

### 8.1 记忆类型

| 类型 | 说明 | 示例 |
|------|------|------|
| 🌍 **World** | 世界事实 | "炉子是烫的" |
| 📖 **Experience** | 亲身体验 | "我摸过炉子，很烫" |
| 💡 **Mental Model** | 形成理解 | "应该小心热的物体" |

### 8.2 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                      Hindsight                          │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   Retain    │  │   Recall    │  │   Reflect   │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
│         │                 │                 │          │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐   │
│  │    World     │  │  Semantic   │  │   LLM      │   │
│  │  Experiences │  │  Keyword    │  │  Analysis  │   │
│  │ MentalModels │  │   Graph     │  │  Synthesis │   │
│  └──────┬──────┘  │   Temporal  │  └──────┬──────┘   │
│         │           └──────┬──────┘          │          │
│  ┌──────▼───────────────▼───────────────▼──────┐   │
│  │         PostgreSQL + Vector Store           │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 8.3 数据流

```
User Input → Retain → LLM Extraction → Normalization → Canonical Entities
                                    ↓
                              Time Series + Search Indexes
                                    ↓
                              Memory Pathways (World/Experience)
                                    ↓
                              Recall/Reflect → RRF Fusion → Cross-encoder → Results
```

## 九、部署选项

### 9.1 Docker（推荐）

```bash
# 单行启动
docker run --rm -it --pull always -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_API_KEY=$OPENAI_API_KEY \
  ghcr.io/vectorize-io/hindsight:latest
```

### 9.2 Docker Compose（外部 PostgreSQL）

```yaml
version: '3.8'
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_PASSWORD: ${HINDSIGHT_DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  hindsight:
    image: ghcr.io/vectorize-io/hindsight:latest
    ports:
      - "8888:8888"
      - "9999:9999"
    environment:
      HINDSIGHT_DB_PASSWORD: ${HINDSIGHT_DB_PASSWORD}
      HINDSIGHT_API_LLM_API_KEY: ${OPENAI_API_KEY}
    depends_on:
      - postgres
```

### 9.3 Kubernetes (Helm)

```bash
helm install hindsight oci://ghcr.io/vectorize-io/hindsight-chart \
  --set api.env.OPENAI_API_KEY=$OPENAI_API_KEY
```

### 9.4 Python Embedded（无服务器）

```python
pip install hindsight-all -U

import os
from hindsight import HindsightServer, HindsightClient

with HindsightServer(
    llm_provider="openai",
    llm_model="gpt-4o-mini",
    llm_api_key=os.environ["OPENAI_API_KEY"]
) as server:
    client = HindsightClient(base_url=server.url)
    client.retain(bank_id="my-bank", content="Alice works at Google")
    results = client.recall(bank_id="my-bank", query="Where does Alice work?")
```

## 十、多 LLM Provider 支持

### 10.1 Provider 配置

| Provider | 环境变量 | 说明 |
|----------|----------|------|
| **OpenAI** | `OPENAI_API_KEY` | GPT-4o, GPT-4o-mini |
| **Anthropic** | `ANTHROPIC_API_KEY` | Claude 3.5 |
| **Gemini** | `GEMINI_API_KEY` | Gemini 1.5 |
| **Groq** | `GROQ_API_KEY` | Llama, Mixtral |
| **Ollama** | `OLLAMA_BASE_URL` | 本地模型 |
| **LM Studio** | `LMSTUDIO_BASE_URL` | 本地模型 |
| **MiniMax** | `MINIMAX_API_KEY` | MiniMax MoE |

### 10.2 Provider 切换

```python
# 在 Docker 中指定 Provider
docker run ... -e HINDSIGHT_API_LLM_PROVIDER=anthropic

# 或使用 Python SDK
wrapper = HindsightWrapper(
    llm_provider="anthropic",
    llm_model="claude-3-5-sonnet"
)
```

## 十一、最佳实践

### 11.1 记忆组织

| 模式 | 说明 |
|------|------|
| **Per-User Bank** | 每个用户独立记忆库 |
| **Per-Project Bank** | 每个项目独立记忆库 |
| **Per-Task Bank** | 每个任务独立记忆库 |

### 11.2 元数据使用

```python
# 使用元数据隔离记忆
client.retain(
    bank_id="support-agent",
    content="Customer complained about billing",
    metadata={
        "user_id": "user-123",
        "channel": "email",
        "priority": "high"
    }
)

# 检索时过滤
results = client.recall(
    bank_id="support-agent",
    query="billing issues",
    metadata_filter={"channel": "email"}
)
```

### 11.3 反思策略

| 策略 | 触发时机 |
|------|----------|
| 📊 **周期性反思** | 每日工作总结 |
| ⚡ **事件驱动** | 收到负面反馈时 |
| 🔄 **任务完成** | 关键里程碑达成 |

## 十二、文档资源

### 12.1 官方资源

| 资源 | 链接 |
|------|------|
| 📚 **文档** | https://hindsight.vectorize.io |
| 📖 **API 参考** | https://hindsight.vectorize.io/api-reference |
| 🐍 **Python SDK** | https://hindsight.vectorize.io/sdks/python |
| 📦 **Node.js SDK** | https://hindsight.vectorize.io/sdks/nodejs |
| 💻 **CLI** | https://hindsight.vectorize.io/sdks/cli |
| 🍳 **Cookbook** | https://hindsight.vectorize.io/cookbook |

### 12.2 社区资源

| 资源 | 链接 |
|------|------|
| 💬 **Slack** | https://join.slack.com/t/hindsight-space/shared_invite |
| 🐙 **GitHub** | https://github.com/vectorize-io/hindsight |
| 📄 **论文** | https://arxiv.org/abs/2512.12818 |

## 十三、总结

Hindsight 是**当今最准确的 Agent 记忆系统**：

| 维度 | 说明 |
|------|------|
| 🧠 **记忆系统** | 不是 Agent，是 Agent 的记忆 |
| 📊 **SOTA 性能** | LongMemEval 基准最优 |
| ⚡ **2 行代码** | LLM Wrapper 轻松集成 |
| 🔍 **多检索** | 语义 + 关键词 + 图 + 时间 |
| 🌐 **多 Provider** | OpenAI / Anthropic / Gemini 等 |
| 🏢 **生产验证** | Fortune 500 企业使用 |

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/vectorize-io/hindsight |
| 文档 | https://hindsight.vectorize.io |
| 论文 | https://arxiv.org/abs/2512.12818 |
| Slack | https://join.slack.com/t/hindsight-space |
| Cloud | https://ui.hindsight.vectorize.io/signup |

---

_🦞 本文由钳岳星君撰写，基于 Hindsight (8.9k Stars)_
