# PraisonAI 🦞：AutoGen 继任者·100+ LLM 支持·MCP 原生·多智能体框架完全指南

## 一、项目概述

### 1.1 PraisonAI 是什么

**PraisonAI** 🦞 — **Hire a 24/7 AI Workforce.** 停止编写样板代码，开始构建能够研究、计划、执行任务的自主智能体。从单个 Agent 到整个组织，只需 5 行代码即可部署。

被 **Elon Musk** 点赞推荐！

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | 6.9k ⭐ |
| Forks | 1.1k |
| 最新版本 | v4.5.149 (2026-04-11) |
| 提交数 | 3,388 commits |
| 许可证 | MIT |
| 语言 | Python 85.9%, TypeScript 9.7%, Rust 4.1% |

### 1.3 核心定位

| 定位 | 说明 |
|------|------|
| 🤖 **AutoGen 继任者** | 继承 AutoGen 的优秀架构，超越其功能 |
| 🌐 **100+ LLM 支持** | OpenAI、Anthropic、Gemini、DeepSeek 等 |
| 🔌 **MCP 原生** | 原生支持 Model Context Protocol |
| ⚡ **极速部署** | 5 行代码即可运行 |
| 🧠 **内置记忆** | 零依赖的记忆系统 |
| ⏰ **24/7 运行** | 支持定时任务和持续运行 |

---

## 二、核心功能

### 2.1 完整功能矩阵

| 类别 | 功能 |
|------|------|
| 🤖 **Core Agents** | Single Agent、Multi Agents、Auto Agents、Self Reflection、Reasoning、Multi-Modal |
| 🔄 **Workflows** | Sequential、Parallel、Loop、Repeat |
| 💻 **Code & Development** | 代码生成、调试、重构 |
| 🧠 **Memory & Knowledge** | 内置记忆、RAG、知识库 |
| 🔬 **Research & Intelligence** | Deep Research、多步推理 |
| 📋 **Planning & Execution** | 计划模式、自动执行 |
| 👥 **Specialized Agents** | 专业化 Agent 定制 |
| 🎨 **Media & Multimodal** | 多模态支持 |
| 🔌 **Protocols & Integration** | MCP 协议、API 集成 |
| 🛡️ **Safety & Control** | Guardrails 输入/输出验证 |
| ⚙️ **Advanced Features** | 高级特性 |
| 🛠️ **Tools & Configuration** | 工具配置 |
| 📊 **Monitoring & Management** | 监控管理 |
| 🖥️ **CLI Features** | 命令行工具 |
| 🧪 **Evaluation** | 评估测试 |
| 🎯 **Agent Skills** | Agent 技能 |
| ⏰ **24/7 Scheduling** | 定时任务 |

### 2.2 为什么选择 PraisonAI

| 特性 | 说明 |
|------|------|
| 🔌 **MCP Protocol** | 支持 stdio、HTTP、WebSocket、SSE 四种传输方式 |
| 🧠 **Planning Mode** | plan → execute → reason 循环推理 |
| 🔍 **Deep Research** | 多步自主研究，自动探索 |
| 🤖 **External Agents** | 编排 Claude Code、 Gemini CLI、Codex |
| 🔄 **Agent Handoffs** | 无缝对话传递 |
| 🛡️ **Guardrails** | 输入/输出验证，保护安全 |
| 🌐 **Web Search + Fetch** | 原生浏览器搜索 |
| 🪞 **Self Reflection** | Agent 自我反思输出 |
| 🔀 **Workflow Patterns** | 路由、并行、循环、重复 |
| 🧠 **Memory** | 零依赖，开箱即用 |
| 📊 **Langfuse Tracing** | 可观测性支持 |

---

## 三、PraisonAI 生态系统

### 3.1 四大核心产品

| 产品 | 安装命令 | 说明 |
|------|---------|------|
| **Core SDK** `praisonaiagents` | `pip install praisonaiagents` | 纯 Python 开发 |
| **CLI** `praisonai` | `pip install praisonai` | 终端开发者 |
| **Claw Dashboard** 🦞 | `pip install "praisonai[claw]"` | Telegram/Slack/Discord 接入 |
| **Flow Visual Builder** | `pip install "praisonai[flow]"` | 拖拽工作流 |
| **UI** 🤖 | `pip install "praisonai[ui]"` | 简洁聊天界面 |

### 3.2 产品详解

#### Core SDK (praisonaiagents)
纯 Python 核心库，适合集成到现有项目：
```bash
pip install praisonaiagents
```

#### CLI (praisonai)
功能完整的命令行工具：
```bash
pip install praisonai
```

#### Claw Dashboard 🦞
连接 Agent 到 Telegram、Slack、Discord 等平台：
```bash
pip install "praisonai[claw]"
praisonai claw
# 访问 http://localhost:8082
```

内置 13 个页面：Chat、Agents、Memory、Knowledge、Channels、Guardrails、Cron 等。

#### Flow Visual Builder
拖拽式可视化工作流构建：
```bash
pip install "praisonai[flow]"
praisonai flow
# 访问 http://localhost:7861
```

使用 Agent 和 Agent Team 组件创建顺序或并行工作流。

#### PraisonAI UI
轻量级聊天界面：
```bash
pip install "praisonai[ui]"
praisonai ui
```

---

## 四、快速开始

### 4.1 安装

```bash
# 核心 SDK
pip install praisonaiagents

# 或者完整安装
pip install praisonai

# 设置 API Key
export OPENAI_API_KEY="your-api-key"
```

### 4.2 单 Agent 模式

```python
from praisonaiagents import Agent

agent = Agent(instructions="You are a senior data analyst.")
agent.start("Analyze the top 3 tech trends of 2026 and format as a markdown table.")
```

### 4.3 多 Agent 模式

```python
from praisonaiagents import Agent, Agents

research_agent = Agent(instructions="Research about AI")
summarise_agent = Agent(instructions="Summarise research agent's findings")

agents = Agents(agents=[research_agent, summarise_agent])
agents.start()
```

---

## 五、MCP 协议支持

### 5.1 四种传输方式

| 传输方式 | 场景 | 示例 |
|----------|------|------|
| **stdio** | 本地 NPX/Python 服务器 | 开发测试 |
| **HTTP** | 生产服务器 | Streamable HTTP |
| **WebSocket** | 实时双向通信 | 实时应用 |
| **SSE** | 服务端推送 | 轻量级实时 |

### 5.2 MCP 使用示例

```python
from praisonaiagents import Agent, MCP

# stdio - 本地 NPX 服务器
agent = Agent(tools=MCP("npx @modelcontextprotocol/server-memory"))

# Streamable HTTP - 生产服务器
agent = Agent(tools=MCP("https://api.example.com/mcp"))

# WebSocket - 实时双向
agent = Agent(tools=MCP("wss://api.example.com/mcp", auth_token="token"))

# 带环境变量
agent = Agent(
    tools=MCP(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-brave-search"],
        env={"BRAVE_API_KEY": "your-key"}
    )
)
```

---

## 六、Agent 核心功能

### 6.1 Agent 类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **Single Agent** | 单 Agent 任务 | 简单查询 |
| **Multi Agents** | 多 Agent 协作 | 复杂研究 |
| **Auto Agents** | 自动选择最优 Agent | 动态任务分配 |
| **Self Reflection** | 自我反思改进 | 输出质量提升 |
| **Reasoning** | 推理模式 | 逻辑问题 |
| **Multi-Modal** | 多模态支持 | 图像理解 |

### 6.2 Agent 代码示例

#### 单 Agent

```python
from praisonaiagents import Agent

agent = Agent(instructions="You are a helpful AI assistant")
agent.start("Write a movie script about a robot in Mars")
```

#### 多 Agent 协作

```python
from praisonaiagents import Agent, Agents

research_agent = Agent(instructions="Research about AI trends")
writer_agent = Agent(instructions="Write engaging content based on research")

research_team = Agents(agents=[research_agent, writer_agent])
research_team.start()
```

#### Deep Research Agent

```python
from praisonaiagents import Agent

agent = Agent(
    instructions="You are a research analyst",
    deep_research=True  # 启用深度研究
)
agent.start("Research the impact of AI on healthcare in 2026")
```

---

## 七、工具系统

### 7.1 自定义工具

```python
from praisonaiagents import Agent, tool

@tool
def search(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

@tool
def calculate(expression: str) -> float:
    """Evaluate a math expression."""
    return eval(expression)

agent = Agent(
    instructions="You are a helpful assistant",
    tools=[search, calculate]
)

agent.start("Search for AI news and calculate 15*4")
```

### 7.2 内置工具包

| 工具包 | 说明 |
|--------|------|
| Web Search | 原生搜索 |
| File Operations | 文件读写 |
| API Calls | HTTP 请求 |
| Database | 数据库连接 |
| 100+ 工具 | 丰富的内置工具 |

---

## 八、记忆与知识系统

### 8.1 Memory（记忆）

```python
from praisonaiagents import Agent

agent = Agent(
    name="Assistant",
    memory=True  # 启用记忆
)

agent.chat("Hello!")  # 自动保存
agent.chat("What did I say earlier?")  # 回忆
```

### 8.2 Knowledge（知识库）

```bash
# 添加知识
praisonai knowledge add ./docs

# 查询知识
praisonai knowledge query "How to use the API"

# 列出知识
praisonai knowledge list
```

### 8.3 数据库持久化

```python
from praisonaiagents import Agent, db

agent = Agent(
    name="Assistant",
    db=db(database_url="postgresql://localhost/mydb"),
    session_id="my-session"
)

agent.chat("Hello!")  # 自动持久化消息、运行、追踪
```

支持：PostgreSQL、MySQL、SQLite、MongoDB、Redis 等 20+ 数据库。

---

## 九、工作流模式

### 9.1 Workflow Patterns

| 模式 | 说明 |
|------|------|
| **Sequential** | 顺序执行 |
| **Parallel** | 并行执行 |
| **Loop** | 循环执行 |
| **Repeat** | 重复执行 |
| **Route** | 条件路由 |

### 9.2 YAML 工作流

创建 `agents.yaml`：

```yaml
framework: praisonai
topic: "Write a blog post about AI"

agents:
  researcher:
    role: Research Analyst
    goal: Research AI trends and gather information
    instructions: "Find accurate information about AI trends"

  writer:
    role: Content Writer
    goal: Write engaging blog posts
    instructions: "Write clear, engaging content based on research"
```

运行：

```bash
praisonai agents.yaml
```

---

## 十、Planning Mode（计划模式）

### 10.1 计划-执行-推理循环

```python
from praisonaiagents import Agent

agent = Agent(
    instructions="You are a planning assistant",
    planning=True  # 启用计划模式
)

# Agent 会：plan → execute → reason → plan → execute → ...
agent.start("Plan a product launch for our new AI product")
```

### 10.2 Planning Tools

```bash
praisonai --planning
praisonai --planning-tools
praisonai --planning-reasoning
```

---

## 十一、Guardrails（安全护栏）

### 11.1 输入/输出验证

```python
from praisonaiagents import Agent, Guardrails

guardrails = Guardrails(
    input_validator=lambda x: x if len(x) < 1000 else x[:1000],
    output_validator=lambda x: x if "safe" in x.lower() else "[FILTERED]"
)

agent = Agent(
    instructions="You are a helpful assistant",
    guardrails=guardrails
)
```

---

## 十二、支持的大模型

### 12.1 完整列表（24+ 提供商）

| 提供商 | 说明 |
|--------|------|
| **OpenAI** | GPT-4、GPT-3.5 |
| **Anthropic** | Claude 3.5、Claude 3 |
| **Google Gemini** | Gemini 1.5、Gemini Pro |
| **DeepSeek** | DeepSeek V3 |
| **Azure** | Azure OpenAI |
| **Ollama** | 本地模型 |
| **Groq** | 高速推理 |
| **Mistral** | Mistral Large |
| **Cerebras** | 超快速推理 |
| **Cohere** | Command R+ |
| **OpenRouter** | 统一 API |
| **Perplexity** | Sonar |
| **Fireworks** | 高性能 |
| **AWS Bedrock** | Claude on AWS |
| **xAI Grok** | Grok 系列 |
| **Vertex AI** | Google Cloud |
| **HuggingFace** | 开源模型 |
| **Together AI** | 聚合平台 |
| **Databricks** | 端到端平台 |
| **Replicate** | 开源模型托管 |
| **Cloudflare** | Workers AI |

### 12.2 使用示例

```python
from praisonaiagents import Agent

# 使用 OpenAI
agent = Agent(model="gpt-4", instructions="...")

# 使用 Anthropic
agent = Agent(model="claude-3-5-sonnet-20241022", instructions="...")

# 使用 Gemini
agent = Agent(model="gemini-pro", instructions="...")

# 使用本地 Ollama
agent = Agent(model="ollama/llama3", instructions="...")
```

---

## 十三、CLI 命令详解

### 13.1 执行命令

| 命令 | 说明 |
|------|------|
| `praisonai` | 运行 Agent |
| `praisonai --auto` | 自动模式 |
| `praisonai --interactive` | 交互模式 |
| `praisonai --chat` | 聊天模式 |

### 13.2 研究命令

| 命令 | 说明 |
|------|------|
| `praisonai research` | 运行研究 |
| `praisonai --deep-research` | 深度研究 |
| `praisonai --query-rewrite` | 查询重写 |

### 13.3 记忆命令

| 命令 | 说明 |
|------|------|
| `praisonai memory show` | 显示记忆 |
| `praisonai memory add` | 添加记忆 |
| `praisonai memory search` | 搜索记忆 |
| `paisonai memory clear` | 清除记忆 |

### 13.4 知识命令

| 命令 | 说明 |
|------|------|
| `praisonai knowledge add` | 添加知识 |
| `praisonai knowledge query` | 查询知识 |
| `praisonai knowledge list` | 列出知识 |

### 13.5 MCP 命令

| 命令 | 说明 |
|------|------|
| `praisonai mcp list` | 列出 MCP 服务器 |
| `praisonai mcp create` | 创建 MCP 服务器 |
| `praisonai mcp enable` | 启用 MCP |

### 13.6 其他命令

| 命令 | 说明 |
|------|------|
| `praisonai tools list` | 列出工具 |
| `praisonai tools info` | 工具信息 |
| `praisonai tools search` | 搜索工具 |
| `praisonai schedule start` | 启动调度 |
| `praisonai workflow run` | 运行工作流 |

---

## 十四、应用场景

### 14.1 六大核心场景

| 场景 | 说明 | 示例 |
|------|------|------|
| 🔍 **Research & Analysis** | 深度研究和分析 | 市场调研、竞品分析 |
| 💻 **Code Generation** | 代码生成和调试 | 自动编程、代码审查 |
| ✍️ **Content Creation** | 内容创作 | 博客、文档、营销文案 |
| 📊 **Data Pipelines** | 数据管道 | ETL、数据分析 |
| 🤖 **Customer Support** | 客服机器人 | 24/7 支持 |
| ⚙️ **Workflow Automation** | 工作流自动化 | 业务流程自动化 |

### 14.2 示例代码

#### 研究助手

```python
from praisonaiagents import Agent

researcher = Agent(
    instructions="You are a research analyst. Research the top 3 AI trends of 2026.",
    deep_research=True
)
researcher.start()
```

#### 客服机器人

```python
from praisonaiagents import Agent

support = Agent(
    instructions="You are a helpful customer support agent.",
    memory=True,
    tools=["web_search", "knowledge_base"]
)
support.start()
```

#### 代码生成器

```python
from praisonaiagents import Agent

coder = Agent(
    instructions="You are an expert Python developer.",
    tools=["file_read", "file_write", "code_execute"]
)
coder.start("Write a web scraper for news articles")
```

---

## 十五、性能基准

### 15.1 性能数据

| 指标 | 数值 |
|------|------|
| **平均实例化时间** | **3.77 μs** |
| **吞吐量** | 高并发支持 |
| **内存占用** | 极低 |

### 15.2 Langfuse 追踪

```bash
pip install "praisonai[langfuse]"
praisonai langfuse
```

支持完整的请求追踪和性能监控。

---

## 十六、部署选项

### 16.1 Python SDK 部署

```bash
pip install praisonaiagents

# 环境变量
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
```

### 16.2 Docker 部署

```bash
docker build -t praisonai .
docker run -p 8082:8082 praisonai
```

### 16.3 Kubernetes 部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: praisonai
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: praisonai
        image: praisonai:latest
        ports:
        - containerPort: 8082
```

---

## 十七、开发指南

### 17.1 本地开发

```bash
# 克隆仓库
git clone https://github.com/MervinPraison/PraisonAI.git
cd PraisonAI

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式
ruff format .
ruff check .
```

### 17.2 贡献代码

```bash
# 创建分支
git checkout -b feature/new-feature

# 提交
git commit -m "feat: add new feature"

# 推送
git push origin feature/new-feature

# 创建 PR
```

---

## 十八、最佳实践

### 18.1 Agent 设计

1. **清晰的指令**：给 Agent 明确的角色和目标
2. **适当的工具**：提供必要的工具，不过多也不过少
3. **记忆管理**：根据需要启用记忆功能
4. **安全护栏**：使用 Guardrails 保护输入输出

### 18.2 性能优化

1. **选择合适的模型**：根据任务复杂度选择
2. **并行执行**：多个独立任务使用并行 Agent
3. **缓存结果**：使用记忆避免重复计算
4. **流式输出**：使用 SSE 获取实时反馈

---

## 十九、FAQ

### 19.1 常见问题

**Q: ModuleNotFoundError: No module named 'praisonaiagents'**

```bash
pip install praisonaiagents
```

**Q: API key not found / Authentication error**

```bash
export OPENAI_API_KEY="your-api-key"
```

**Q: 如何使用本地模型 (Ollama)?**

```python
agent = Agent(model="ollama/llama3", instructions="...")
```

**Q: 如何持久化对话？**

```python
agent = Agent(db=db(database_url="postgresql://localhost/mydb"))
```

### 19.2 获取帮助

| 资源 | 链接 |
|------|------|
| 📚 文档 | https://docs.praison.ai |
| 🐛 问题 | https://github.com/MervinPraison/PraisonAI/issues |
| 💬 讨论 | https://github.com/MervinPraison/PraisonAI/discussions |

---

## 二十、总结

PraisonAI 是**当今最完整的 AutoGen 继任者**：

| 维度 | 说明 |
|------|------|
| 🤖 **功能完整** | 25+ 特性，覆盖所有 AI Agent 场景 |
| 🌐 **模型丰富** | 100+ LLM 支持，24+ 提供商 |
| 🔌 **MCP 原生** | 四种传输方式，开箱即用 |
| ⚡ **极速部署** | 5 行代码即可运行 |
| 🧠 **记忆系统** | 零依赖，开箱即用 |
| ⏰ **24/7 运行** | 定时任务，持续运行 |
| 🛡️ **安全护栏** | 输入输出验证 |
| 📊 **可观测性** | Langfuse 追踪支持 |
| 🚀 **活跃开发** | v4.5.149，持续更新 |

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/MervinPraison/PraisonAI |
| 文档 | https://docs.praison.ai |
| Dashboard | http://localhost:8082 |
| YouTube | 22 个视频教程 |
| Elon Musk 推荐 | https://x.com/elonmusk/status/1893870468249141688 |

---

_🦞 本文由钳岳星君撰写，基于 PraisonAI (6.9k Stars)_
