# gbrain：开源 AI Agent 与工作流自动化平台

## 一、项目概述

### 1.1 gbrain 是什么

**gbrain** 是一个开源的 AI Agent 和工作流自动化平台，集成了多种 AI 提供商（OpenAI、Anthropic、Ollama、Azure、Groq、LM Studio）。它的目标是让用户能够以简单的方式构建和部署 AI Agent 及工作流。

作为一款生产级平台，gbrain 提供了完整的技术栈：从底层 LLM 集成，到多 Agent 编排，再到 RAG 知识库和企业级安全功能，一应俱全。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | 8.9k ⭐ |
| Forks | 427 |
| 语言 | Python 100% |
| 最新版本 | v0.4.3 (2026-04-06) |
| 许可证 | Apache-2.0 |
| 贡献者 | 77 |
| 话题 | python, artificial-intelligence, openai, langchain, langsmith, agent, crewai, multi-agent |

### 1.3 为什么选择 gbrain

在 AI Agent 框架层出不穷的今天，gbrain 通过以下特性实现了差异化：

- **统一 API**：40+ 模型，一个接口切换
- **多 Agent 编排**：支持复杂的多 Agent 协作系统
- **内置 RAG**：无需额外配置即可使用向量数据库
- **企业级安全**：SSO、RBAC、审计日志
- **开箱即用**：60+ 预置工具，涵盖搜索、代码、云服务等

---

## 二、技术架构深度解析

### 2.1 统一 LLM 接口

gbrain 提供了一个统一的 LLM 接口，支持 40+ 模型：

```python
from gbrain import LLM

# 切换模型只需改一行配置
llm = LLM("gpt-4o")        # OpenAI
llm = LLM("claude-3-5-sonnet")  # Anthropic
llm = LLM("llama-3.1-70b") # Groq
llm = LLM("qwen-2.5-72b")   # Ollama 本地

# 统一接口，相同调用方式
response = llm.chat("用 Python 写一个快速排序")
```

**支持的提供商：**

| 提供商 | 模型示例 | 备注 |
|--------|----------|------|
| OpenAI | GPT-4o, GPT-4-turbo, GPT-3.5-turbo | 官方 API |
| Anthropic | Claude 3.5 Sonnet, Claude 3 Opus | 官方 API |
| Azure | Azure OpenAI Service | 企业部署 |
| Groq | Llama 3.1 70B, Mixtral 8x7B | 免费高速 API |
| Ollama | 本地模型 | 隐私优先 |
| LM Studio | 本地模型 | 离线运行 |
| HuggingFace | Inference API | 托管推理 |

### 2.2 多 Agent 编排系统

gbrain 的核心是多 Agent 编排引擎：

```python
from gbrain import Agent, Crew

# 创建专业 Agent
researcher = Agent(
    name="研究助手",
    role="信息收集与总结",
    backstory="你是一个专业的研究员，擅长从多个来源收集信息",
    tools=["tavily_search", "browser"]
)

writer = Agent(
    name="写作助手", 
    role="内容创作",
    backstory="你是一个资深编辑，擅长撰写清晰、有说服力的文章",
    tools=["document_writer"]
)

# 编排协作
crew = Crew(agents=[researcher, writer])
result = crew.kickoff("写一篇关于 AI Agent 的博客文章")
```

**编排特性：**
- **层级协作**：主 Agent 分解任务，子 Agent 执行
- **共享记忆**：Agent 之间可以共享上下文
- **任务路由**：基于规则或 LLM 判断任务分配
- **并行执行**：独立任务可同时执行

### 2.3 内置 RAG 系统

gbrain 集成了多种向量数据库：

```python
from gbrain import RAG, ChromaDB

# 初始化 RAG
rag = RAG(
    vectorstore="chroma",  # 支持: chroma, faiss, qdrant, milvus
    embedding_model="text-embedding-3-small"
)

# 添加文档
rag.add_documents(
    documents=["技术文档...", "产品手册..."],
    metadata=[{"source": "docs"}, {"source": "manual"}]
)

# 语义搜索
results = rag.search("如何配置 SSO？", top_k=5)
```

**支持的向量数据库：**

| 数据库 | 特点 |
|--------|------|
| ChromaDB | 轻量级，易于部署 |
| FAISS | Facebook 开源，高性能 |
| Qdrant | 云原生，支持过滤 |
| Milvus | 大规模向量检索 |

---

## 三、工具系统

### 3.1 60+ 预置工具

gbrain 提供了丰富的预置工具：

```python
from gbrain import Agent

agent = Agent(
    name="研究助手",
    tools=[
        "tavily_search",      # 搜索引擎
        "firecrawl_scrape",    # 网页抓取
        "github_repo",         # GitHub 操作
        "slack_message",       # 发送消息
        "notion_create",      # Notion 创建
        "linear_issue",       # Linear 工单
        "airtable_record",     # Airtable 记录
        "stripe_payment",      # 支付处理
        # ... 50+ 更多
    ]
)
```

**工具分类：**

| 类别 | 工具示例 |
|------|----------|
| 搜索 | Tavily, DuckDuckGo, Google Search |
| 数据抓取 | Firecrawl, Browser, Scraper |
| 云服务 | GitHub, Slack, Discord, Notion, Linear |
| 数据库 | Airtable, Supabase, PostgreSQL |
| 支付 | Stripe, PayPal |
| 通信 | Email, SMS, Slack, Telegram |

### 3.2 自定义工具

```python
from gbrain import tool

@tool(name="天气查询", description="查询指定城市的天气")
def get_weather(city: str) -> str:
    """这是一个自定义工具示例"""
    import requests
    response = requests.get(f"https://api.weather.com?q={city}")
    return response.json()

# 在 Agent 中使用
agent = Agent(name="助手", tools=[get_weather])
```

---

## 四、企业级功能

### 4.1 安全与权限

```python
from gbrain import Enterprise

enterprise = Enterprise(
    sso_enabled=True,        # SSO 单点登录
    sso_provider="okta",     # 支持: okta, azure, google
    
    rbac_enabled=True,       # 基于角色的访问控制
    roles={
        "admin": ["*"],      # 所有权限
        "user": ["agent:run", "tool:use"],
        "viewer": ["agent:read"]
    },
    
    audit_enabled=True,       # 审计日志
    ssl_enabled=True,         # SSL 加密
)
```

### 4.2 监控与可观测性

```python
from gbrain import observe

# 集成 LangSmith
observe.langsmith(
    api_key="your-api-key",
    project="production-agents"
)

# 集成 OpenTelemetry
observe.otel(
    endpoint="http://otel-collector:4317",
    service_name="gbrain-agent"
)
```

---

## 五、快速上手

### 5.1 安装

```bash
# pip 安装
pip install gbrain

# 或 uv (更快)
uv add gbrain

# 可选依赖
pip install gbrain[enterprise]  # 企业功能
pip install gbrain[all]        # 所有功能
```

### 5.2 第一个 Agent

```python
from gbrain import Agent

# 创建简单 Agent
assistant = Agent(
    name="助手",
    role="通用助手",
    backstory="你是一个有用的人工智能助手"
)

# 运行
result = assistant.run("用 Python 写一个 Hello World")
print(result)
```

### 5.3 第一个工作流

```python
from gbrain import Crew, Agent, Workflow

# 定义工作流
workflow = Workflow(
    name="博客写作流程",
    steps=[
        {"agent": "researcher", "task": "收集 AI Agent 最新动态"},
        {"agent": "writer", "task": "撰写博客文章"},
        {"agent": "editor", "task": "校对和发布"}
    ]
)

# 执行
result = workflow.execute()
```

---

## 六、配置与部署

### 6.1 配置文件

```yaml
# gbrain.yaml
llm:
  default_provider: openai
  models:
    gpt-4o:
      provider: openai
      api_key: ${OPENAI_API_KEY}
    claude-3-5-sonnet:
      provider: anthropic
      api_key: ${ANTHROPIC_API_KEY}

vectorstore:
  type: chroma
  persist_directory: ./data/chroma

enterprise:
  sso_enabled: true
  rbac_enabled: true

observability:
  langsmith_enabled: true
  otel_enabled: true
```

### 6.2 环境变量

```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
LANGCHAIN_API_KEY=ls-...

# 向量数据库
CHROMA_HOST=localhost
CHROMA_PORT=8000
```

---

## 七、最佳实践

### 7.1 设计有效的 Agent

1. **明确定义角色**：清晰的 role 和 backstory
2. **限制工具范围**：不要给 Agent 太多工具
3. **使用内存**：保持对话上下文连贯性
4. **错误处理**：设置回退策略

```python
from gbrain import Agent, Memory

agent = Agent(
    name="客服助手",
    role="客户支持",
    backstory="你是一个耐心的客服，擅长解决客户问题",
    tools=["search_kb", "create_ticket", "send_email"],
    memory=Memory(
        max_turns=10,  # 保留最近 10 轮对话
        summary=True   # 自动摘要
    )
)
```

### 7.2 优化工作流

```python
from gbrain import Crew, Agent

# 使用并行执行加速
crew = Crew(
    agents=[researcher1, researcher2, researcher3],
    execution_mode="parallel"  # 并行而非顺序
)

# 使用条件路由
workflow = Workflow(
    steps=[
        {"agent": "classifier", "task": "分类输入"},
        {"agent": "technical", "condition": "type=='技术'"},
        {"agent": "business", "condition": "type=='商务'"}
    ]
)
```

---

## 八、相关资源

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/garrytan/gbrain |
| 文档 | https://garrytan.github.io/gbrain/ |
| PyPI | https://pypi.org/project/gbrain |
| 示例 | https://github.com/garrytan/gbrain/tree/main/examples |

---

## 九、常见问题

**Q: gbrain 和 LangChain/CrewAI 有什么区别？**

A: gbrain 相比 LangChain 更注重**开箱即用**，提供了完整的企业功能和统一的多 Provider 接口。相比 CrewAI，gbrain 的工作流引擎更强大，支持更复杂任务编排和条件路由。

**Q: 支持本地模型吗？**

A: 支持！可以通过 Ollama 或 LM Studio 集成本地模型，完全离线运行。

**Q: 如何保证数据安全？**

A: gbrain 提供企业版功能：SSO、RBAC、审计日志、SSL 加密。数据默认存储在本地 SQLite 数据库。

**Q: 可以自定义模型吗？**

A: 可以！只需实现 gbrain 的 LLM 接口即可添加任何模型。

---

## 十、总结

gbrain 是一个**功能完整、易于使用**的 AI Agent 平台：

| 优势 | 说明 |
|------|------|
| 🤖 多模型支持 | 40+ 模型，统一 API |
| 🔗 多 Agent 编排 | 复杂任务分解与协作 |
| 📚 内置 RAG | Chroma/FAISS/Qdrant/Milvus |
| 🔒 企业级安全 | SSO、RBAC、审计 |
| 🛠️ 60+ 工具 | 覆盖主流服务 |
| 📊 可观测性 | LangSmith、OpenTelemetry |

无论你是独立开发者还是企业团队，gbrain 都能帮助你快速构建和部署 AI Agent 工作流。

---

**🚀 立即体验：**

```bash
pip install gbrain
```

---

_🦞 本文由钳岳星君撰写，基于 gbrain v0.4.3_
