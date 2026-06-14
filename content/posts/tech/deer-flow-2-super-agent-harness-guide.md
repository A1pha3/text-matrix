---
title: "DeerFlow 2.0：字节跳动超级智能体框架完全指南"
date: "2026-05-06T20:05:34+08:00"
slug: "deer-flow-2-super-agent-harness-guide"
aliases:
  - "/posts/tech/ai-agent/deerflow-super-agent-harness/"
description: "DeerFlow 2.0是字节跳动开发的开源超级智能体框架，通过编排子智能体、记忆系统和沙箱环境实现复杂任务自动化。本文详细解析其架构设计、主要特性、本地部署及适用场景。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "DeerFlow", "字节跳动", "子智能体", "开源"]
---

DeerFlow（**D**eep **E**xploration and **E**fficient **R**esearch **Flow**）是字节跳动旗下火山引擎开发的开源超级智能体框架，2026 年 2 月 28 日登顶 GitHub Trending 第一。2.0 版本为完全重写，与 1.x 无任何共享代码。仓库地址：[github.com/bytedance/deer-flow](https://github.com/bytedance/deer-flow)。

如果用一个比喻来理解 DeerFlow，它更像一个「AI 工头」而不是「AI 员工」。它不亲自执行每个任务，而是把复杂问题拆解后分派给一群子智能体，协调它们通过共享记忆和消息总线协作，最后汇总结果。

## 架构总览

下图展示了 DeerFlow 2.0 的组件关系和数据流向：

```mermaid
graph TB
    subgraph Input["入口层"]
        A[用户 / API 请求]
    end

    subgraph Orchestrator["编排层"]
        B[任务解析器]
        C[子智能体调度器]
        D[消息总线]
    end

    subgraph Agents["子智能体集群"]
        E1[研究员 Agent]
        E2[代码 Agent]
        E3[数据分析 Agent]
        E4[自定义 Agent ...]
    end

    subgraph Infrastructure["基础设施层"]
        F1[(长期记忆<br/>向量数据库)]
        F2[(短期记忆<br/>会话上下文)]
        G[技能库 / Tools]
        H[沙箱环境<br/>Docker / 本地]
        I[可观测性<br/>LangSmith / Langfuse]
    end

    subgraph External["外部服务"]
        J[LLM API<br/>Doubao / DeepSeek / Kimi]
        K[搜索服务<br/>InfoQuest / SerpAPI]
        L[代码执行<br/>Python / Node.js]
    end

    A --> B
    B --> C
    C --> D
    D --> E1 & E2 & E3 & E4
    E1 & E2 & E3 & E4 --> D
    E1 & E2 & E3 & E4 <--> F1 & F2
    E1 & E2 & E3 & E4 --> G
    E1 & E2 & E3 & E4 --> H
    C --> I
    J & K & L --> G
```

整个系统围绕一条原则设计：**每个组件只做一件事，通过 Harness 层的消息总线串联**。这种设计使得新增一个子智能体或工具不需要改动已有代码，只需注册到调度器中即可。

## 组件拆解

### 子智能体（Sub-Agents）

子智能体是 DeerFlow 的执行单元。每个子智能体有独立的系统提示词、工具集和记忆视图。在执行过程中，调度器根据任务类型匹配对应的子智能体，通过消息总线传递上下文。

一个典型的研究任务可能涉及三个子智能体：

- **研究员 Agent**：调用 InfoQuest 或 SerpAPI 搜索资料，提取关键信息
- **分析师 Agent**：对收集到的信息进行交叉验证和结构化整理
- **写作者 Agent**：基于分析结果生成最终报告

子智能体间共享一份长期记忆（持久化到向量数据库），因此即使研究员和分析师是先后启动的不同子智能体，分析师也能直接读取研究员写入记忆的结果，不需要重复传递。

### 技能库与工具链

DeerFlow 通过 LangChain 的 Tool 抽象层接入外部能力。目前已内置的工具有：

| 工具 | 用途 | 来源 |
|------|------|------|
| InfoQuest | 智能搜索与网页爬取 | 火山引擎自研 |
| Python REPL | 沙箱内执行 Python 代码 | 内置 |
| 文件读写 | 读写沙箱文件系统 | 内置 |
| Shell | 执行 Shell 命令 | 内置 |
| MCP 协议工具 | 通过 MCP 接入任意第三方工具 | 社区扩展 |

添加自定义工具只需实现 LangChain 的 `BaseTool` 接口并在配置中注册。例如接入企业内部 API：

```python
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

class InternalAPISchema(BaseModel):
    query: str = Field(description="发送给内部 API 的查询")

class InternalAPITool(BaseTool):
    name: str = "internal_api"
    description: str = "访问公司内部知识库，检索文档和报告"
    args_schema: type[BaseModel] = InternalAPISchema
    api_key: str = Field(default="")

    def _run(self, query: str) -> str:
        import requests
        resp = requests.post(
            "https://internal-api.example.com/search",
            json={"q": query},
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["result"]
```

然后在 `deerflow.yaml` 中注册：

```yaml
tools:
  - name: internal_api
    type: custom
    module: tools.internal_api
    class: InternalAPITool
    env:
      INTERNAL_API_KEY: ${INTERNAL_API_KEY}
```

### Claude Code 集成

DeerFlow 支持让 Claude Code 作为子智能体在沙箱中自主编程。典型工作流是：

1. DeerFlow 将任务描述和代码库上下文传给 Claude Code Agent
2. Claude Code Agent 在沙箱中读取文件、编辑代码、运行测试
3. 完成后将结果（代码 diff、测试报告）写入共享记忆
4. 其他子智能体（如代码审查 Agent）读取结果进行下一步处理

这个能力让 DeerFlow 可以胜任「从需求分析到代码提交」的端到端开发流程，而不只是生成代码片段。

### 沙箱环境

每个子智能体的代码执行和数据操作都在沙箱中隔离。DeerFlow 提供两种沙箱模式：

- **Docker 沙箱**（生产推荐）：每个子智能体在独立容器中运行，有独立的文件系统和网络命名空间
- **本地模式**（开发调试）：子智能体直接在当前环境中运行，适合快速迭代

Docker 模式下，你可以限制每个沙箱的内存上限、CPU 核心数和执行超时时间：

```yaml
sandbox:
  mode: docker
  image: deerflow-sandbox:latest
  limits:
    memory: 2g
    cpus: 2
    timeout_seconds: 600
```

### 长期记忆

DeerFlow 使用向量数据库（默认 ChromaDB，可切换为 Milvus 或 Pinecone）存储长期记忆。每个子智能体可以在执行过程中写入记忆，后续的任何子智能体都能读取。

记忆数据有「命名空间」隔离——同一个项目的多次执行共享一个命名空间，不同项目互不干扰。对于长周期研究任务（如持续数天的行业跟踪），这意味着昨天的分析结果今天仍然可以直接被新一轮任务使用。

## 实战案例

### 案例一：端到端技术调研报告

**场景**：某团队需要调研「2026 年 WebAssembly 在浏览器之外的应用现状」，输出一份 Markdown 格式技术报告。

**配置**：

```yaml
project: wasm-research
agents:
  - name: researcher
    type: research
    model: deepseek-v3.2
    tools: [infoquest, serpapi, file_read]
    max_iterations: 10
  - name: analyst
    type: analysis
    model: deepseek-v3.2
    tools: [file_read, python_repl]
    max_iterations: 5
  - name: writer
    type: writing
    model: kimi-2.5
    tools: [file_write]
    max_iterations: 8
memory:
  namespace: wasm-research
  retention_days: 30
```

**执行过程**：

1. **研究员 Agent** 通过 InfoQuest 检索了 23 篇相关文章（包括 GitHub 仓库、技术博客、论文摘要），过滤出 12 篇高质量来源，提取关键信息写入记忆
2. **分析师 Agent** 读取研究员的结果，使用 Python REPL 统计了 Wasm 运行时（WasmEdge、Wasmtime、WAMR）的 GitHub Star 增长趋势和社区活跃度数据，生成对比图表数据，写入记忆
3. **写作者 Agent** 读取前两个阶段的所有中间结果，生成了一份 4 页 Markdown 报告，包含引言、运行时对比、应用案例（边缘计算、插件系统、区块链智能合约）、趋势预测四个章节

**最终产出**：一份结构化的技术调研报告，耗时约 8 分钟（不含 LLM API 排队时间），总成本约 $0.60（以 DeepSeek v3.2 计费）。

### 案例二：自动化代码审查流水线

**场景**：每次 Pull Request 提交后，自动运行 DeerFlow 进行代码审查，检查安全漏洞、代码质量和实践建议合规性。

**配置**：

```yaml
project: code-review-pipeline
agents:
  - name: security_reviewer
    type: security
    model: doubao-seed-2.0-code
    tools: [github_pr, file_read, shell]
    system_prompt: |
      你是安全审查专家。识别以下类型的问题：
      - SQL 注入、XSS、CSRF
      - 硬编码的密钥和 Token
      - 不安全的依赖版本
      - 缺失的输入校验
  - name: quality_reviewer
    type: quality
    model: doubao-seed-2.0-code
    tools: [github_pr, file_read, shell]
    system_prompt: |
      你是代码质量审查专家。检查以下方面：
      - 圈复杂度超过 15 的函数
      - 超过 200 行的文件
      - 重复代码块
      - 缺少类型注解的函数
  - name: report_aggregator
    type: reporting
    model: kimi-2.5
    tools: [github_pr, file_write]
triggers:
  - type: github_webhook
    event: pull_request
```

**GitHub Actions 集成**：

```yaml
name: DeerFlow Code Review
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run DeerFlow Review
        run: |
          docker compose run --rm deerflow run \
            --config projects/code-review-pipeline.yaml \
            --input "review PR #${{ github.event.pull_request.number }}"
```

**审查结果示例**（写入 PR Comment）：

| 类别 | 严重程度 | 文件 | 问题描述 |
|------|----------|------|----------|
| 安全 | 高 | `src/auth.py` | 第 47 行硬编码了 JWT Secret |
| 质量 | 中 | `src/handler.py` | `process_request` 函数 78 行，圈复杂度 18 |
| 安全 | 低 | `requirements.txt` | `requests==2.31.0` 存在 CVE-2024-xxxxx |

### 案例三：多源新闻摘要

**场景**：每天早上 8:00 自动抓取指定 RSS 源和 Twitter 账号的最新内容，生成一份中文早报。

**配置**：

```yaml
project: daily-digest
schedule: "0 8 * * *"
agents:
  - name: collector
    type: research
    model: deepseek-v3.2
    tools: [rss_reader, infoquest, file_write]
    max_iterations: 20
  - name: summarizer
    type: writing
    model: kimi-2.5
    tools: [file_read, file_write, python_repl]
inputs:
  rss_feeds:
    - https://news.ycombinator.com/rss
    - https://www.theverge.com/rss/index.xml
    - https://feeds.arxiv.org/rss/cs.AI
  twitter_accounts:
    - @OpenAI
    - @AnthropicAI
    - @LangChainAI
output:
  format: markdown
  path: /output/daily-digest-{{date}}.md
```

每天早上自动执行后，生成的摘要文件通过企业微信机器人推送到团队群聊。

## 部署

### 环境要求

| 组件 | 版本要求 |
|------|----------|
| Python | ≥ 3.12 |
| Node.js | ≥ 22 |
| Docker | ≥ 24（使用沙箱模式时必需） |
| uv | ≥ 0.4（Python 包管理） |

### Docker 部署（推荐）

```bash
git clone https://github.com/bytedance/deer-flow.git
cd deer-flow

cp .env.example .env
docker compose up -d

open http://localhost:7860
```

`.env` 文件中需要配置的内容：

```bash
LLM_PROVIDER=doubao
LLM_API_KEY=your-api-key
LLM_MODEL=doubao-seed-2.0-code

INFOQUEST_API_KEY=your-infoquest-key

MEMORY_BACKEND=chromadb
MEMORY_PERSIST_DIR=./data/memory

SANDBOX_MODE=docker

OBSERVABILITY_PROVIDER=langfuse
LANGFUSE_PUBLIC_KEY=pk-xxx
LANGFUSE_SECRET_KEY=sk-xxx
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 本地开发

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh

cd backend && uv sync
cd frontend && npm install

cd backend && uv run fastapi dev src/main.py

cd frontend && npm run dev
```

### 一键引导（适用于 AI 编程助手）

如果你使用 Claude Code、Codex、Cursor 或 Windsurf，直接把下面这句话发给助手即可完成本地引导：

> Help me clone DeerFlow if needed, then bootstrap it for local development by following https://raw.githubusercontent.com/bytedance/deer-flow/main/Install.md

## DeerFlow 1.x vs 2.0

| 维度 | 1.x | 2.0 |
|------|-----|-----|
| 代码关系 | 原始版本 | 完全重写，无共享代码 |
| 架构 | 单体设计 | 模块化 Harness |
| 子智能体 | 基础支持 | 完整编排能力 |
| 记忆系统 | 有限 | 长期持久化记忆 |
| 沙箱 | 无 | Docker 沙箱支持 |
| 部署 | 复杂 | Docker 一键部署 |

## 推荐模型

DeerFlow 对模型有较强的推理和工具调用能力要求。经过实测，以下模型表现稳定：

- **Doubao-Seed-2.0-Code**（火山引擎）：代码生成和工具调用能力最强，延迟低
- **DeepSeek v3.2**：性价比最优，长文本理解和多轮推理表现出色
- **Kimi 2.5**（Moonshot）：中文写作和结构化输出质量高

不建议使用参数量低于 70B 的开源模型，工具调用的准确率会明显下降。

## FAQ

### 1. DeerFlow 和 LangChain / CrewAI 有什么区别？

LangChain 是通用的 LLM 应用框架，提供工具链和链式调用基础设施。CrewAI 专注于多 Agent 角色扮演。DeerFlow 的定位更偏向「超级智能体框架的运行时」——它在 LangChain 之上构建了完整的子智能体调度、沙箱隔离和长期记忆系统。你可以把 LangChain 看作建造材料，CrewAI 看作装配线，DeerFlow 看作整座工厂。

### 2. 没有 Docker 能用吗？

可以不使用 Docker 沙箱，在 `.env` 中设置 `SANDBOX_MODE=local` 即可。但生产环境建议启用 Docker 沙箱，否则子智能体执行的任意代码会直接在你的宿主机上运行。

### 3. 子智能体之间如何通信？会不会出现消息丢失或重复？

子智能体通过「消息总线 + 共享记忆」两层机制通信。消息总线负责即时事件传递（带确认机制），共享记忆负责持久化上下文。如果消息总线因网络抖动丢失消息，子智能体会从共享记忆中读取最新状态作为兜底。

### 4. 一次任务的成本大概是多少？

取决于任务复杂度、使用的模型和子智能体数量。以技术调研（3 个子智能体，约 25 次 LLM 调用）为例，使用 DeepSeek v3.2 的成本约 $0.50-0.80（2026 年 5 月价格）。成本的大头是研究阶段的多次搜索和阅读调用。

### 5. 可以只用一部分功能吗？比如只用子智能体编排，不用沙箱？

可以。DeerFlow 的组件是松耦合的。你在 `deerflow.yaml` 中配置 `sandbox.mode: local` 就能跳过沙箱隔离。同样，不配置可观测性后端也不会影响主要功能。

### 6. 子智能体可以调用不同的 LLM 模型吗？

可以，且这是推荐做法。研究员用 DeepSeek（性价比高，适合大量检索调用），写作者用 Kimi（中文输出质量好），代码 Agent 用 Doubao-Seed-Code（编程能力强）。每个 Agent 在配置文件中独立指定 `model` 字段即可。

### 7. 长期记忆存在哪里？数据安全吗？

默认使用 ChromaDB，数据持久化到本地 `./data/memory` 目录。生产环境建议切换到 Milvus 或 Pinecone。如果你处理敏感数据，可以使用私有化部署的 Milvus 或启用 ChromaDB 的传输加密。

### 检查项 1：服务健康状态

```bash
curl http://localhost:7860/api/health
```

预期返回 `{"status": "ok", "version": "2.0.x"}`。

### 检查项 2：Docker 沙箱可用性

```bash
docker compose exec deerflow python -c "
from deerflow.sandbox import DockerSandbox
sb = DockerSandbox()
result = sb.run('echo sandbox_ok')
print(result.stdout)
"
```

预期输出 `sandbox_ok`。

### 检查项 3：LLM 连接测试

```bash
docker compose exec deerflow python -c "
from deerflow.llm import get_llm
llm = get_llm()
resp = llm.invoke('Reply with only: pong')
print(resp.content)
"
```

预期输出 `pong`（如果输出其他内容，说明模型未正确配置或 API Key 无效）。

### 检查项 4：运行最小测试任务

创建一个测试配置文件 `test-task.yaml`：

```yaml
project: test
agents:
  - name: tester
    type: general
    model: deepseek-v3.2
    tools: [python_repl]
    max_iterations: 3
```

执行：

```bash
docker compose exec deerflow deerflow run \
  --config test-task.yaml \
  --input "计算 123 * 456 的结果，并用一句话描述计算过程"
```

预期在输出中看到 `56088` 和对计算过程的简要描述。

### 检查项 5：可观测性连通性

如果你配置了 Langfuse，打开 Langfuse Dashboard，检查是否有名为 `deerflow` 的 Trace 记录。如果 30 秒内没有出现，检查 `.env` 中 Langfuse 相关配置是否正确。

### 检查项 6：记忆持久化验证

```bash
docker compose exec deerflow python -c "
from deerflow.memory import LongTermMemory
mem = LongTermMemory(namespace='test-memory')
mem.store('test_key', 'hello_from_test')
retrieved = mem.retrieve('test_key')
assert retrieved == 'hello_from_test', f'Expected hello_from_test, got {retrieved}'
print('Memory persistence OK')
"
```

预期输出 `Memory persistence OK`。

### 检查项 7：多子智能体协作测试

```yaml
project: multi-agent-test
agents:
  - name: agent_a
    type: general
    model: deepseek-v3.2
    tools: [python_repl, file_write]
    max_iterations: 3
  - name: agent_b
    type: general
    model: deepseek-v3.2
    tools: [file_read, python_repl]
    max_iterations: 3
```

```bash
docker compose exec deerflow deerflow run \
  --config multi-agent-test.yaml \
  --input "Agent A: 生成10个随机数存入文件。Agent B：读取文件中的随机数并计算平均值"
```

预期 Agent B 能正确读取 Agent A 生成的数据并输出平均值。

## 安全提示

- **生产环境必须使用 Docker 沙箱模式**。本地模式下子智能体执行的代码直接在宿主机上运行
- **API Key 不要明文写入 `.env` 后提交到 Git**。使用 Docker secrets 或环境变量注入
- **限制沙箱网络访问**。在 Docker Compose 中为沙箱容器配置 `network: none` 或仅允许白名单出口 IP
- **设置资源上限**。`sandbox.limits.timeout_seconds` 建议不超过 1800 秒，防止子智能体陷入死循环消耗大量 Token
- **定期清理记忆数据**。长期记忆会持续增长，建议按项目设置 `retention_days` 过期策略

## 官方资源

- **官网**：https://deerflow.tech
- **GitHub**：https://github.com/bytedance/deer-flow
- **文档**：https://docs.byteplus.com（InfoQuest 相关部分）