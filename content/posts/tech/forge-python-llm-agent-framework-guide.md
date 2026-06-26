---
title: "Forge - Python 自托管 LLM 工具调用与多步 Agent 框架"
date: 2026-05-22T15:54:25+08:00
description: "Forge 是一个 Python 框架，用于自托管 LLM 工具调用和多步 Agent 工作流。支持 Claude/Ollama/LLaMA.cpp 等模型，内置 RAG、代码执行、浏览器操作等能力。本文详解安装、配置、实战案例和进阶用法。"
slug: forge-python-llm-agent-framework-guide
categories: ["技术笔记"]
author: 钳岳星君 🦞
created: 2026-05-22
tags: [LLM, Agent, Python, RAG, 工具调用, 自托管]
---

## 学习目标

读完本文你能：

1. **解释** Forge 的核心设计哲学——为什么自托管 LLM 工具调用需要独立框架，而非直接调云端 API
2. **配置** Forge 连接多种后端（Claude/Ollama/LLaMA.cpp），理解统一工具调用接口如何屏蔽模型差异
3. **实现** 一个完整的多步 Agent 工作流（RAG 搜索 → 代码执行 → 结果汇总），处理中间步骤的失败和重试
4. **评估** Forge 与 LangChain/LlamaIndex 的适用边界，判断你的项目是否适合迁移到 Forge
5. **部署** Forge 到生产环境，配置安全沙箱、API 密钥管理和多用户隔离

## 项目速览

> **Forge** — 自托管 LLM 工具调用与多步 Agent 框架

| 项 | 值 |
|---|---|
| GitHub | `antoinezambelli/forge` |
| Stars | 2,132+ |
| Forks | 157+ |
| 许可证 | MIT |
| 语言 | Python |
| 创建时间 | 2026-02-16 |
| 最新更新 | 2026-06-26 |
| 支持模型 | Claude, Ollama, LLaMA.cpp, Llamafile |

## 目录

- [项目概览](#项目概览)
- [核心特性](#核心特性)
- [安装与快速开始](#安装与快速开始)
- [多模型支持详解](#多模型支持详解)
- [内置工具库](#内置工具库)
- [多步工作流设计](#多步工作流设计)
- [安全沙箱与隔离](#安全沙箱与隔离)
- [适用场景与实战案例](#适用场景与实战案例)
- [与主流框架对比](#与主流框架对比)
- [常见问题与故障排查](#常见问题与故障排查)
- [自测题](#自测题)
- [进阶路径](#进阶路径)

---

## 项目概览

**GitHub:** [antoinezambelli/forge](https://github.com/antoinezambelli/forge)

**一句话定义:** Forge 是一个 Python 框架，用于构建自托管的 LLM 工具调用和多步 Agent 工作流。它的核心承诺是：**让你完全掌控 AI 数据流，而不依赖云端 API 的可用性和隐私政策**。

### 为什么需要 Forge？

当前 LLM 工具调用生态有两个极端：

1. **云端 API（Claude/GPT）**：强大但数据出境，费用不可控，有速率限制。
2. **自托管模型（Ollama/LLaMA.cpp）**：数据私有但工具调用能力弱，需要自己组装 prompt 和解析输出。

Forge 的位置： **用统一的 Python API 屏蔽模型差异，让你写一次工具调用代码，无缝切换 Claude 或本地 LLaMA**，同时保证数据不离开你的服务器。

---

## 核心特性

### 1. 多模型支持

Forge 提供统一的工具调用接口，底层可以切换不同的 LLM 后端：

| 模型后端 | 说明 | 适用场景 |
|----------|------|---------|
| **Claude 系列** | Claude 3.5 Sonnet、Claude 3 Opus 等 | 需要最强推理能力，可接受数据出境 |
| **Ollama** | 本地运行 LLaMA 3/Mistral 等开源模型 | 数据私有，离线可用 |
| **LLaMA.cpp** | C++ 推理引擎，支持 GPU 加速 | 需要极致性能，自己管理模型文件 |
| **Llamafile** | 单二进制运行，无需安装 | 快速试用，单机部署 |

**统一接口示例**：

```python
from forge import Agent, ClaudeModel, OllamaModel

# 用 Claude
agent_claude = Agent(model=ClaudeModel.SONNET, api_key="sk-...")

# 切换到 Ollama，代码不用改
agent_local = Agent(model=OllamaModel.LLAMA3_70B, base_url="http://localhost:11434")

# 同一个 tool 定义，两个后端都能用
@agent_claude.tool()
@agent_local.tool()
def search_docs(query: str) -> str:
    """从知识库检索相关文档"""
    return vector_db.search(query)
```

### 2. 内置工具库

Forge 提供开箱即用的工具集，覆盖常见 Agent 场景：

| 工具 | 功能 | 典型用例 |
|------|------|---------|
| **RAG Search** | 私有知识库检索增强生成 | 企业文档问答、技术手册查询 |
| **Code Executor** | 安全执行 Python/JS 代码 | 数据分析、数学计算、图表生成 |
| **Web Browser** | 网页浏览与内容抓取 | 实时信息获取、价格比对 |
| **File System** | 本地文件读写操作 | 文档生成、日志分析 |
| **HTTP Client** | API 调用与 Webhook 触发 | 第三方服务集成、通知推送 |

**RAG Search 示例**：

```python
from forge import Agent, RagTool

agent = Agent(model="claude-3-5-sonnet")

# 配置 RAG 工具
rag = RagTool(
    docs_dir="./knowledge_base",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    top_k=5
)

@agent.tool()
def answer_from_docs(question: str) -> str:
    """从私有知识库回答问题"""
    results = rag.search(question)
    context = "\n\n".join([r.text for r in results])
    return agent.chat(f"基于以下上下文回答问题：\n{context}\n\n问题：{question}")

# 使用
answer = answer_from_docs("公司的报销流程是什么？")
```

### 3. 多步工作流

Forge 的 `Chain` 原语让你可以把多个步骤串联成一个可追踪、可重试的工作流：

```python
from forge import Agent, Chain

agent = Agent(model="claude-3-5-sonnet")

# 定义多步链
chain = Chain([
    # 步骤 1：搜索文档
    agent.create_step(
        name="search_docs",
        tool=rag.search,
        args={"query": "{$user_query}"}
    ),
    # 步骤 2：生成摘要
    agent.create_step(
        name="write_summary",
        prompt="基于以下搜索结果生成摘要：\n{search_docs.result}",
        depends_on=["search_docs"]
    ),
    # 步骤 3：发送邮件
    agent.create_step(
        name="send_email",
        tool=email_sender.send,
        args={
            "to": "team@company.com",
            "subject": "查询结果",
            "body": "{write_summary.result}"
        },
        depends_on=["write_summary"]
    )
])

# 执行
result = chain.run(user_query="Q3 技术架构文档")
print(result["send_email"].output)  # 最终输出
```

**关键点**：

- 步骤之间通过 `{step_name.result}` 引用上游输出。
- `depends_on` 定义执行顺序，Forge 会自动解析依赖图。
- 任意步骤失败，整个链会暂停并报告错误，不会继续执行。

### 4. 安全沙箱

代码执行在隔离的沙箱环境中，防止恶意代码损害主机：

```python
from forge import CodeExecutor, SandboxConfig

# 配置沙箱
sandbox = SandboxConfig(
    timeout=30,          # 执行超时（秒）
    memory_limit="512M", # 内存上限
    network="disabled",  # 禁用网络（可选）
    allowed_modules=["numpy", "pandas", "matplotlib"]  # 白名单模块
)

executor = CodeExecutor(sandbox=sandbox)

@agent.tool()
def run_analysis(code: str) -> str:
    """执行数据分析代码"""
    result = executor.run(code)
    return result.output
```

**安全特性**：

- 超时杀死进程，防止无限循环。
- 内存上限防止 OOM 攻击。
- 可选禁用网络，防止数据外泄。
- 模块白名单，防止导入 `os.system` 等危险操作。

---

## 安装与快速开始

### 安装

```bash
pip install forge-ai
```

### 最小示例

```python
from forge import Forge, ClaudeModel

# 初始化
forge = Forge(api_key="your-claude-key")

# 定义工具
@forge.tool()
def search_kb(query: str) -> str:
    """从私有知识库检索"""
    return forge.rag.search(query)

# 定义 Agent
@forge.agent(model=ClaudeModel.SONNET)
def research_task(task: str):
    results = search_kb(task)
    return forge.summarize(results)

# 运行
result = research_task("查找 Q3 技术架构文档")
print(result)
```

### 配置本地模型（Ollama）

```python
from forge import Forge, OllamaModel

# 指向本地 Ollama 实例
forge = Forge(
    model=OllamaModel.LLAMA3_70B,
    base_url="http://localhost:11434"
)

# 后续代码和 Claude 版本完全一致
@forge.tool()
def search_kb(query: str) -> str:
    # ...
```

---

## 多模型支持详解

### 支持的后端列表

| 后端 | 安装要求 | 配置参数 |
|------|----------|---------|
| Claude | `pip install forge-ai` | `api_key`, `model` |
| Ollama | 安装 Ollama | `base_url` |
| LLaMA.cpp | 编译或用预编译二进制 | `model_path`, `n_ctx` |
| Llamafile | 下载 `.llamafile` 二进制 | `binary_path` |

### 切换后端的成本

Forge 的统一接口意味着**切换后端理论上零代码改动**。但实际需要注意：

1. **工具调用能力差异**：Claude 支持并行 tool call，Ollama 可能只支持串行。
2. **上下文长度差异**：Claude 200k tokens，LLaMA 3 8k tokens，长文档场景需要切分。
3. **推理速度差异**：本地模型慢 10-100 倍，需要调 `timeout` 和 `max_retries`。

**推荐策略**：

- 开发阶段用 Claude（快速迭代）。
- 生产环境如果数据敏感，切到 Ollama/LLaMA.cpp。
- 用环境变量控制后端切换：

```python
import os
from forge import Forge, ClaudeModel, OllamaModel

MODEL_BACKEND = os.getenv("MODEL_BACKEND", "claude")

if MODEL_BACKEND == "claude":
    forge = Forge(model=ClaudeModel.SONNET, api_key=os.getenv("ANTHROPIC_API_KEY"))
else:
    forge = Forge(model=OllamaModel.LLAMA3_70B, base_url="http://localhost:11434")
```

---

## 内置工具库

### RAG Search 详解

RAG（Retrieval-Augmented Generation）是 Forge 的核心工具之一：

**配置示例**：

```python
from forge.tools import RagTool

rag = RagTool(
    docs_dir="./docs",                          # 文档目录
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",  # 嵌入模型
    chunk_size=512,                             # 分块大小
    chunk_overlap=50,                           # 重叠 token 数
    top_k=5,                                    # 返回 top 5 结果
    rerank=True                                 # 启用重排序
)

# 索引文档（首次运行或文档更新时）
rag.index()

# 搜索
results = rag.search("如何申请年假？")
for r in results:
    print(r.text, r.score)  # 文本和相似度分数
```

**支持的文件格式**：`.txt`, `.md`, `.pdf`, `.docx`, `.html`

### Code Executor 详解

```python
from forge.tools import CodeExecutor

executor = CodeExecutor(
    timeout=60,
    memory_limit="1G",
    network="enabled",       # 允许网络（慎用）
    allowed_modules=["numpy", "pandas", "matplotlib", "seaborn"]
)

@forge.tool()
def analyze_csv(file_path: str, question: str) -> str:
    """分析 CSV 文件"""
    code = f"""
import pandas as pd
df = pd.read_csv('{file_path}')
# 用户问题：{question}
# 生成分析代码...
"""
    result = executor.run(code)
    return result.output
```

### Web Browser 详解

```python
from forge.tools import WebBrowser

browser = WebBrowser(
    headless=True,       # 无头模式
    timeout=30,
    user_agent="Forge/1.0"
)

@forge.tool()
def fetch_webpage(url: str) -> str:
    """抓取网页内容"""
    page = browser.get(url)
    return page.markdown  # 返回 Markdown 格式
```

---

## 多步工作流设计

### Chain 原语进阶

`Chain` 支持条件分支和循环：

**条件分支**：

```python
from forge import Chain, Condition

chain = Chain([
    agent.create_step("check_intent", prompt="判断用户意图：技术/商务/其他"),
    agent.create_step(
        "tech_response",
        prompt="技术回答：{check_intent.result}",
        condition=Condition.equals("check_intent.result", "技术")
    ),
    agent.create_step(
        "biz_response",
        prompt="商务回答：{check_intent.result}",
        condition=Condition.equals("check_intent.result", "商务")
    )
])
```

**循环**：

```python
chain = Chain([
    agent.create_step("search", tool=google_search, args={"query": "{$query}"}),
    agent.create_step(
        "should_continue",
        prompt="搜索结果是否满足需求？如果否，返回新的搜索词。如果是，返回 DONE。",
        max_iterations=5  # 最多循环 5 次
    )
])
```

### 错误处理与重试

```python
from forge import RetryPolicy

chain = Chain(
    steps=[...],
    retry_policy=RetryPolicy(
        max_retries=3,
        backoff="exponential",  # 指数退避
        on_failure="pause"      # 失败暂停，等待人工介入
    )
)
```

---

## 安全沙箱与隔离

### 多用户隔离

如果 Forge 部署为服务，需要隔离不同用户的执行环境：

```python
from forge import Forge, UserSandbox

forge = Forge()

# 每个用户独立的沙箱
def handle_user_request(user_id: str, query: str):
    sandbox = UserSandbox(
        user_id=user_id,
        work_dir=f"./sandboxes/{user_id}",
        quota={"cpu": 2, "memory": "2G", "disk": "10G"}
    )
    agent = forge.create_agent(sandbox=sandbox)
    return agent.run(query)
```

### API 密钥管理

```python
from forge import KeyVault

vault = KeyVault(
    backend="env",  # 从环境变量读取
    # 或者用加密文件：backend="encrypted_file", path="./keys.enc"
)

forge = Forge(api_key=vault.get("ANTHROPIC_API_KEY"))
```

---

## 适用场景与实战案例

### 场景 1：企业私有知识库问答

**需求**：员工问答系统，基于内部文档（PDF/Word/Markdown），数据不能出境。

**方案**：

1. 用 Forge + Ollama 部署本地实例。
2. 配置 `RagTool` 索引内部文档。
3. 写一个简单的 Web UI（Flask/FastAPI）调用 Forge Agent。
4. 用 `UserSandbox` 隔离不同部门的访问权限。

**代码示例**：

```python
from flask import Flask, request, jsonify
from forge import Forge, OllamaModel, RagTool

app = Flask(__name__)
forge = Forge(model=OllamaModel.LLAMA3_70B)
rag = RagTool(docs_dir="./internal_docs")
rag.index()

@forge.agent()
def answer_question(question: str) -> str:
    results = rag.search(question)
    context = "\n\n".join([r.text for r in results])
    return forge.chat(f"上下文：\n{context}\n\n问题：{question}")

@app.route("/ask", methods=["POST"])
def ask():
    question = request.json["question"]
    answer = answer_question(question)
    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### 场景 2：自动化代码审查

**需求**：提交 PR 后自动审查代码，检查规范、安全漏洞、性能问题。

**方案**：

1. 用 Forge + Claude（代码理解能力强）。
2. 配置 `GitTool` 获取 PR diff。
3. 多步链：`获取 diff` → `静态分析` → `LLM 审查` → `生成报告`。

### 场景 3：网页数据采集与监控

**需求**：定期抓取竞品价格，存入数据库，价格异常时报警。

**方案**：

1. 用 Forge + `WebBrowser` 抓取页面。
2. 用 `CodeExecutor` 解析 HTML 提取价格。
3. 用 `Chain` 定时执行（配合 cron 或 APScheduler）。
4. 用 `HTTPClient` 发送报警 Webhook。

---

## 与主流框架对比

| 特性 | Forge | LangChain | LlamaIndex |
|------|-------|-----------|------------|
| **自托管** | ✅ 优先支持 | ⚠️ 可配置 | ✅ 支持 |
| **工具调用** | ✅ 内置，统一接口 | ✅ 支持，但抽象复杂 | ⚠️ 需扩展 |
| **RAG** | ✅ 开箱即用 | ⚠️ 需组合多个模块 | ✅ 专注 RAG |
| **代码执行** | ✅ 安全沙箱内置 | ❌ 无内置 | ❌ 无内置 |
| **多模型切换** | ✅ 统一接口 | ✅ 支持但需要改代码 | ⚠️ 部分支持 |
| **学习曲线** | 低（Pythonic API） | 高（抽象层级多） | 中 |
| **社区生态** | 小（新项目） | 大 | 中 |
| **文档质量** | 中等 | 高 | 高 |

**选型建议**：

- 如果你需要**自托管 + 工具调用 + RAG**，Forge 是最简洁的选择。
- 如果你已经用 LangChain，迁移成本取决于工具调用的复杂度。
- 如果你只需要 RAG，LlamaIndex 更专业。

---

## 常见问题与故障排查

### 1. Ollama 后端连接失败？

**症状**：`ConnectionRefusedError: connect to localhost:11434`

**排查步骤**：

1. 确认 Ollama 在运行：
   ```bash
   ollama list  # 应该能看到已安装的模型
   ```

2. 确认端口正确：
   ```bash
   netstat -an | grep 11434  # macOS/Linux
   ```

3. 如果是远程 Ollama，检查防火墙和 `base_url` 配置。

**解决**：启动 Ollama 服务，或者改用 Claude 后端临时测试。

### 2. RAG 搜索结果不相关？

**原因**：嵌入模型不合适，或者文档分块太大/太小。

**解决**：

1. 换更好的嵌入模型：
   ```python
   rag = RagTool(
       embedding_model="sentence-transformers/all-mpnet-base-v2",  # 效果更好
       # ...
   )
   ```

2. 调整分块大小：
   ```python
   rag = RagTool(
       chunk_size=256,    # 更小，更精准
       chunk_overlap=100, # 更大重叠，保留上下文
       # ...
   )
   ```

3. 启用重排序：
   ```python
   rag = RagTool(rerank=True, rerank_model="cross-encoder/ms-marco-MiniLM-L-6-v2")
   ```

### 3. Code Executor 执行超时？

**原因**：代码太慢，或者进入死循环。

**解决**：

1. 增大 `timeout`：
   ```python
   executor = CodeExecutor(timeout=300)  # 5 分钟
   ```

2. 在沙箱里禁用无限循环：
   ```python
   executor = CodeExecutor(
       timeout=30,
       max_iterations=1000  # 限制循环次数
   )
   ```

### 4. Claude API 速率限制？

**症状**：`RateLimitError: Too many requests`

**解决**：

1. 添加重试逻辑：
   ```python
   forge = Forge(
       model=ClaudeModel.SONNET,
       retry_policy={"max_retries": 5, "backoff": "exponential"}
   )
   ```

2. 切换到 Ollama 处理低优先级任务。

### 5. 生产环境部署有哪些坑？

** checklist**：

- [ ] API 密钥用环境变量或密钥管理服务，不要硬编码。
- [ ] 用 `UserSandbox` 隔离不同用户。
- [ ] 配置日志和监控（Prometheus/Grafana）。
- [ ] 用 Nginx 反向代理，启用 HTTPS。
- [ ] 限制并发请求数，防止资源耗尽。
- [ ] 定期清理沙箱目录，防止磁盘占满。

---

## 自测题

1. **Forge 的核心设计哲学是什么？它如何解决「云端 API」和「自托管模型」之间的断层？**
   <details>
   <summary>答案</summary>
   Forge 的核心哲学是「统一的 Python API 屏蔽模型差异」。它解决断层的方式是：提供统一的工具调用接口，底层可以切换 Claude/Ollama/LLaMA.cpp 等后端，让开发者写一次代码，无缝切换，同时保证数据不离开服务器（自托管场景）。
   </details>

2. **Forge 的 `Chain` 原语支持哪些高级特性？如何处理步骤失败？**
   <details>
   <summary>答案</summary>
   Chain 支持：条件分支（Condition）、循环（max_iterations）、依赖管理（depends_on）、错误处理（RetryPolicy）。步骤失败时，整个链会暂停并报告错误，不会继续执行；可以通过 RetryPolicy 配置自动重试或暂停等待人工介入。
   </details>

3. **RAG Search 的效果受哪些因素影响？如何优化搜索结果的相关性？**
   <details>
   <summary>答案</summary>
   影响因素：嵌入模型质量、分块大小（chunk_size）、重叠 token 数（chunk_overlap）、是否启用重排序（rerank）。优化方案：换更好的嵌入模型（如 all-mpnet-base-v2）、调整分块大小、启用重排序、增加 top_k 并后处理。
   </details>

4. **Forge 的安全沙箱有哪些隔离层级？生产环境部署需要注意什么？**
   <details>
   <summary>答案</summary>
   隔离层级：超时杀死、内存上限、网络禁用、模块白名单、多用户隔离（UserSandbox）。生产环境注意：API 密钥管理、日志监控、HTTPS、并发限制、磁盘清理。
   </details>

5. **如何选择合适的 LLM 后端？Claude 和 Ollama 在 Forge 里有哪些实际差异？**
   <details>
   <summary>答案</summary>
   选择依据：数据隐私（是否可出境）、推理能力（Claude 更强）、成本（Ollama 免费但基于硬件）、速度（Claude 快但受速率限制）。实际差异：工具调用能力（Claude 支持并行）、上下文长度（Claude 200k vs LLaMA 8k）、推理速度（本地模型慢 10-100 倍）。
   </details>

---

## 进阶路径

### 阶段 1：跑起来，理解统一接口（1-2 天）

- 安装 Forge，配置 Claude 后端。
- 运行文档里的最小示例。
- 切换到 Ollama 后端，验证「零代码改动」。

**目标**：理解 Forge 的核心价值——统一接口屏蔽模型差异。

### 阶段 2：用 RAG + Code Executor 解决实际问题（3-5 天）

- 配置 `RagTool` 索引你的私有文档。
- 写一个简单的问答 Agent。
- 用 `CodeExecutor` 做数据分析和图表生成。

**目标**：掌握两个最核心的内置工具，能解决真实问题。

### 阶段 3：设计多步工作流，部署到生产（1-2 周）

- 用 `Chain` 实现多步 Agent（如自动化代码审查）。
- 配置安全沙箱和多用户隔离。
- 部署为 Web 服务（Flask/FastAPI），配置 HTTPS 和监控。

**目标**：从原型到生产，理解 Forge 的工程化能力。

### 阶段 4：贡献和深度定制（2 周+）

- 读 Forge 源码，理解工具调用抽象和模型适配层。
- 写自定义 Tool 或集成第三方服务。
- 提交 PR 修复 bug 或添加新 feature。

**目标**：从用户变成 contributor，影响项目方向。

---

## 总结

Forge 定位明确：**让开发者完全掌控 AI 工作流**。相比云端 API 方案，Forge 强调私有部署和数据安全，内置的工具库覆盖了从 RAG 到代码执行的完整链路，适合企业级 AI 应用落地。

**核心优势**：

- 统一接口，无缝切换模型后端。
- 内置 RAG、代码执行、浏览器等操作，开箱即用。
- 安全沙箱，适合生产环境。

**适用场景**：

- 企业私有知识库问答。
- 自动化代码审查。
- 网页数据采集与监控。

**不适用场景**：

- 需要极强推理能力且数据可出境（直接用 Claude API 更简单）。
- 只需要 RAG（LlamaIndex 更专业）。

如果你对数据隐私有要求，又不想从零搭建 Agent 基础设施，Forge 值得一试。

---

**相关工具**：

- [Oh-My-Pi](https://github.com/can1357/oh-my-pi) - AI Coding Agent 终端
- [CLI-Anything](https://github.com/HKUDS/CLI-Anything) - 通用 CLI Agent 框架
- [LangChain](https://github.com/langchain-ai/langchain) - LLM 应用开发框架
- [LlamaIndex](https://github.com/run-llama/llama_index) - 专注于 RAG 的框架
