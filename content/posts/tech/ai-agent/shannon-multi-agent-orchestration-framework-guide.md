---
title: "Shannon：生产级多智能体编排框架完全指南"
slug: "shannon-multi-agent-orchestration-framework-guide"
github_repo: "Kocoro-lab/Shannon"
source_key: "gh:Kocoro-lab/Shannon"
aliases:
  - /posts/tech/shannon-multi-agent-orchestration-framework-guide/
date: "2026-04-01T10:15:00+08:00"
lastmod: "2026-09-25T00:00:00+08:00"
categories: ["技术笔记"]
tags: ["Shannon", "多智能体", "Multi-Agent"]
description: "Shannon 把多智能体编排从原型推到生产：Temporal 工作流保证可回放、WASI 沙箱隔离代码执行、硬性 Token 预算防止成本失控，10+ LLM 提供商，MIT 许可证。"
---

# Shannon：把多智能体编排推到生产环境

Shannon 做的事超出了在多个模型之间做路由。它用 Temporal 工作流引擎把每次执行变成可回放的记录，用 WASI 沙箱把代码执行锁在隔离环境里，再用硬性 Token 预算把成本钉在可控范围。它和 LangChain 这类原型框架的区别在哪、什么场景值得引入你的基础设施，是这篇文章要回答的问题。

---

## 项目概述

### 什么是 Shannon

**Shannon**（[GitHub 仓库](https://github.com/Kocoro-lab/Shannon)）是一个面向生产的多智能体编排框架，README 里的自我定位只有一句：

> **"Ship reliable AI agents to production."** — 把可靠的 AI 智能体部署到生产环境。

大多数 AI Agent 框架解决的是"怎么调用模型、怎么串联工具"。Shannon 解决的是调用之后的事：执行过程能不能回放？成本会不会跑飞？代码执行有没有隔离？多租户之间怎么不互相干扰？

**官网**：[shannon.run](https://shannon.run)（在线 Demo）
**文档**：[docs.shannon.run](https://docs.shannon.run)
**最新版本**：v0.5.1（2026 年 6 月发布）

### 项目数据

Shannon 于 2025 年 8 月开源，MIT 许可证，主语言 Go，辅以 Python、TypeScript 和 Rust。截至 2026 年 9 月下旬，社区积累约 2,260 Stars、350 Forks，核心贡献者 6 位，主分支保持活跃提交。

### 五个核心设计选择

| 特性 | 说明 |
|------|------|
| **Temporal Workflows** | 时间旅行调试 — 逐步重放任何一次执行 |
| **Hard Token Budgets** | 每个任务/智能体硬性 Token 预算，超 80% 触发告警并自动降级到更便宜的模型 |
| **Real-time Dashboard** | 实时事件流，Prometheus 指标，OpenTelemetry 追踪 |
| **WASI Sandbox** | WASI 沙箱执行 Python 代码，OPA 策略管控，多租户隔离 |
| **Multi-Vendor** | 10+ 提供商（OpenAI、Anthropic、Google、xAI、DeepSeek、MiniMax、Groq、本地 Ollama 等），自动故障转移 |

### Shannon 解决什么问题

| 你在生产环境遇到的问题 | Shannon 的应对方式 |
|------|----------------|
| 智能体静默失败，查不出原因 | Temporal 工作流 + 时间旅行调试 — 逐步重放任何执行 |
| Token 消耗失控，账单意外暴涨 | 每个任务/智能体硬性预算 + 预算告警事件 + 自动模型降级 |
| 执行过程黑盒，不知道发生了什么 | 实时事件流、Prometheus 指标、OpenTelemetry 追踪 |
| 代码执行安全风险 | WASI 沙箱执行 Python、OPA 策略、多租户隔离 |
| 被单一 LLM 提供商绑定 | 10+ 提供商接入，提供商之间自动故障转移 |

---

## 核心架构

### 技术栈

Shannon 用三种语言各管一层：Go 承担高并发的编排与状态，Rust 负责需要内存安全的执行强制与沙箱，Python 则享用最丰富的 LLM SDK 生态。

| 组件 | 语言 | 职责 |
|------|------|------|
| **Gateway** | Go | REST API，JWT/API Key 鉴权，限流 |
| **Orchestrator** | Go | Temporal 工作流、任务分解、复杂度路由、预算管理 |
| **Agent Core** | Rust | 执行强制网关：WASI 沙箱、令牌计数、熔断器 |
| **LLM Service** | Python | 提供商抽象、MCP 工具、技能系统、agent loop |
| **Playwright Service** | Python | 浏览器自动化（可选组件，默认不启动） |

### 数据层与语言占比

状态存储用 PostgreSQL（含 pgvector 扩展，向量记忆直接落在 Postgres 里），会话与缓存用 Redis。早期的 Qdrant 已不在默认部署中。

按 GitHub 语言统计口径（字节），仓库当前构成大致是：Go 约 46%、Python 约 32%、TypeScript 约 10%、Rust 约 7%、Shell 约 5%，其余为 PLpgSQL、Go Template、Makefile 等。

### 架构主线

请求沿一条主线流动，四个服务各司其职，旁路挂存储与时间旅行调试：

```text
客户端 ─▶ Gateway:8080 ─▶ Orchestrator:50052 ─▶ Agent Core:50051 ─▶ LLM Service:8000 ─▶ 模型/工具
REST/SDK    鉴权·限流        Temporal 工作流      执行强制·WASI 沙箱    提供商抽象·技能
OpenAI兼容                   复杂度路由·预算管理   令牌计数·熔断器       MCP 工具·agent loop

旁路：PostgreSQL(状态+向量) · Redis(会话/缓存) · Temporal:7233(UI:8088, 时间旅行) · Playwright:8002(可选)
```

### 服务端口

| 服务 | 端口 | 用途 |
|------|------|------|
| **Gateway** | 8080 | REST API、SSE/WebSocket 事件流、OpenAI 兼容 `/v1`、健康检查 |
| **Orchestrator** | 50052（gRPC）+ 8081 | 编排服务；8081 提供健康检查与事件接入 |
| **Agent Core** | 50051（gRPC，内部） | 执行强制、WASI 沙箱 |
| **LLM Service** | 8000 | 模型调用、工具执行 |
| **Playwright** | 8002 | 浏览器自动化（需 `--profile browser` 启动） |
| **Temporal** | 7233（gRPC）+ 8088（UI） | 工作流引擎与调试界面 |
| **PostgreSQL / Redis** | 5432 / 6379 | 状态存储 / 会话缓存 |

---

## 快速开始

### 环境要求

- Docker 和 Docker Compose（v2）
- 至少一家 LLM 提供商的 API Key（OpenAI、Anthropic 或任意 OpenAI 兼容端点）

### 一键安装

```bash
curl -fsSL https://raw.githubusercontent.com/Kocoro-lab/Shannon/main/scripts/install.sh | bash
```

安装脚本做的不只是下载：它会把 `deploy/compose/docker-compose.release.yml` 落盘为安装目录里的 `docker-compose.yml`，连同 `.env` 模板、配置文件、合成模板、工作流示例、三个核心技能（code-review、debugging、test-driven-dev）、WASI Python 3.11.4 解释器和数据库迁移一起下载到 `./shannon`，然后拉取 Docker 镜像、启动全部服务，并轮询 `http://localhost:8080/health` 直到网关就绪。想固定版本，可以加环境变量：`SHANNON_VERSION=v0.5.1`。

### 写入 API Key 并重启

脚本启动时 `.env` 还没有你的 Key，编辑之后重启一遍让配置生效：

```bash
cd shannon       # 安装目录，默认在当前目录下
nano .env        # 填入 OPENAI_API_KEY 或 ANTHROPIC_API_KEY
docker compose down
docker compose up -d
```

### 验证安装

```bash
# 检查所有服务状态
docker compose ps

# Gateway 健康检查
curl http://localhost:8080/health

# Orchestrator 健康检查
curl http://localhost:8081/health
```

两个 `/health` 都返回正常，网关就绪，可以提交第一个任务。

---

## 与 Shannon 交互

### 提交第一个任务

通过 REST API 提交最简单，响应里会带 `task_id`，用它接手后续状态和事件。

```bash
# 提交任务
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the capital of France?",
    "session_id": "demo-session"
  }'

# 实时流式事件（workflow_id 即 task_id）
curl -N "http://localhost:8080/api/v1/stream/sse?workflow_id=task-dev-123"

# 获取最终结果
curl "http://localhost:8080/api/v1/tasks/task-dev-123"
```

### Python SDK

```bash
pip install shannon-sdk
```

```python
from shannon import ShannonClient

with ShannonClient(base_url="http://localhost:8080") as client:
    handle = client.submit_task(
        "What is the capital of France?",
        session_id="demo-session"
    )
    result = client.wait(handle.task_id)
    print(result.result)
```

### 桌面应用

Shannon 的桌面端是 Tauri v2 + Next.js 应用，带实时执行时间线和研究过程可视化。两种获取方式：

- 从 [GitHub Releases](https://github.com/Kocoro-lab/Shannon/releases/latest) 下载对应平台的安装包（macOS、Windows、Linux）；
- 或从源码构建：

```bash
cd desktop
npm install
npm run tauri:build
```

桌面应用连接的是本机已启动的后端服务。

### OpenAI 兼容接入

现有 OpenAI 代码可以零改造接入。把 base URL 指向 Shannon 网关，SDK 传参逻辑不变：

```bash
export OPENAI_API_BASE=http://localhost:8080/v1
# 你的现有 OpenAI 代码保持不变
```

网关还提供一组 `shannon-*` 虚拟模型名，把模型选择映射到编排配置。例如 `shannon-deep-research` 对应"深度研究 + 迭代精炼"工作流，`shannon-quick-research` 对应快速研究。调用形如 `POST /v1/chat/completions`，`model` 填这些虚拟名即可，映射关系在 `config/openai_models.yaml` 里维护。

### 执行策略：按复杂度自动路由

Shannon 的一个容易被忽略的设计是：任务提交后先过一遍复杂度评估，再决定用哪种策略执行，而不是让调用方自己猜。当前共八种策略：

| 策略 | 触发条件 | 适用场景 |
|------|----------|----------|
| **Simple** | 复杂度 < 0.3 | 单智能体直接回答 |
| **DAG** | 多步任务（默认） | 扇出/扇入 + 依赖追踪 |
| **ReAct** | 迭代推理 | 推理 + 工具调用循环 |
| **Research** | 多步研究 | 分层模型调度，README 口径可省 50-70% 成本 |
| **Exploratory** | 探索性任务 | 思维树并行假设 |
| **Browser Use** | 网页交互 | Playwright 驱动的浏览器智能体 |
| **Domain Analysis** | 领域分析 | 多源结构化领域研究 |
| **Swarm** | 自主团队 | 主导智能体编排多智能体协作，带收敛检测 |

策略可以用 `context` 字段显式指定。最常用的两种：

**研究型（Research）**：编排多个研究智能体，综合发现与引用，适合对比分析、资料汇总。

```bash
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare renewable energy adoption in EU vs US",
    "context": {
      "force_research": true,
      "research_strategy": "deep"
    }
  }'
```

`research_strategy` 支持 `quick`、`standard`、`deep`、`academic` 四档，档位越深调用的模型层级和迭代次数越多。

**集群协作（Swarm）**：让多个智能体并行分工再汇总，适合一题多角度、分工明确的任务。

```bash
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze this dataset from multiple perspectives",
    "context": {
      "force_swarm": true
    }
  }'
```

`context` 里还有一批可组合的控制字段：`budget_max`（本任务 Token 预算）、`budget_agent_min`（单智能体最低预算）、`model_tier` / `model_override` / `provider_override`（模型与提供商覆盖）、`max_iterations`、`max_concurrent_agents`、`enable_verification`。这些都是网关请求结构里的真实字段，可按任务粒度覆盖默认行为。

### 人工审批（Human-in-the-Loop）

涉及敏感操作时，让工作流暂停等人批准再继续：

```bash
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Update the production database schema",
    "context": {
      "require_approval": true
    }
  }'
```

两个前置条件要留意：一是审批门控受环境变量 `APPROVAL_ENABLED` 控制（默认 `false`），部署时要显式打开；二是审批不是在 HTTP 响应里等，而是通过 WebSocket 路由到连接中的 daemon 客户端，由它提交决策：

```bash
curl -X POST http://localhost:8080/api/v1/approvals/decision \
  -H "Content-Type: application/json" \
  -d '{"workflow_id": "<workflow_id>", "approval_id": "<approval_id>", "approved": true}'
```

相关环境变量还有 `APPROVAL_COMPLEXITY_THRESHOLD`（默认 0.5，复杂度超过即触发审批）、`APPROVAL_DANGEROUS_TOOLS`（默认 `file_system,code_execution`）和 `APPROVAL_TIMEOUT_SECONDS`（默认 1800 秒）。

### 定时任务（Scheduled）

用 cron 表达式挂载周期任务，适合日报、周报类自动化：

```bash
curl -X POST http://localhost:8080/api/v1/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Market Analysis",
    "cron_expression": "0 9 * * *",
    "task_query": "Analyze market trends",
    "max_budget_per_run_usd": 0.50
  }'
```

schedules 接口是完整 CRUD，另有 `pause`、`resume`、`runs` 子端点；请求字段还包括 `timezone`、`task_context`、`timeout_seconds`。`max_budget_per_run_usd` 给每次运行设美元成本上限，防止一个定时任务在无人看管时烧穿预算。

### 会话上下文与技能

同一 `session_id` 会把多轮请求串起上下文，后续轮次自动带上历史：

```bash
# 第一轮
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"query": "What is GDP?", "session_id": "econ-101"}'

# 后续轮次记得上下文
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"query": "How does it relate to inflation?", "session_id": "econ-101"}'
```

技能把固定流程封装成可复用入口，用 `skill` 字段指定：

```bash
# 列出可用技能
curl http://localhost:8080/api/v1/skills

# 使用技能执行任务
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Review the auth module for security issues",
    "skill": "code-review",
    "session_id": "review-123"
  }'
```

安装器自带三个核心技能（code-review、debugging、test-driven-dev），自定义技能放在 `config/skills/user/`（目录默认不存在且被 gitignore，需要自己创建）。

### 订阅事件流

用 SSE 实时观察执行过程。事件类型定义在 orchestrator 源码里，从工作流级到工具级都有覆盖：

```bash
curl -N "http://localhost:8080/api/v1/stream/sse?workflow_id=task-dev-123"

# 常见事件类型：
# - WORKFLOW_STARTED, WORKFLOW_COMPLETED
# - AGENT_STARTED, AGENT_COMPLETED
# - TOOL_INVOKED, TOOL_OBSERVATION
# - LLM_PARTIAL, LLM_OUTPUT
# - BUDGET_THRESHOLD（预算告警）
# - APPROVAL_REQUESTED, APPROVAL_DECISION（审批流转）
```

WebSocket 侧提供 `/api/v1/stream/ws`，daemon 客户端走 `WS /v1/ws/messages` 接收审批与定时任务分发。

### 接入 MCP 工具

Shannon 的 MCP 接入是 HTTP 无状态调用，不是本地子进程方式：LLM Service 按约定向 MCP 服务器 `POST {"function": <名称>, "args": {...}}`，拿回 JSON 结果。服务地址与安全边界全部由环境变量控制：

```bash
# .env 中的 MCP 相关配置
MCP_ALLOWED_DOMAINS=localhost,127.0.0.1   # URL 域名白名单，逗号分隔
MCP_MAX_RESPONSE_BYTES=10485760           # 响应体积上限，默认 10 MB
MCP_TIMEOUT_SECONDS=10                    # 单次调用超时
MCP_RETRIES=3                             # 失败重试次数
MCP_CB_FAILURES=5                         # 熔断阈值：连续失败 5 次
MCP_CB_RECOVERY_SECONDS=60                # 熔断恢复等待
```

白名单默认只放行本机地址，通配符 `*` 可以绕过校验但只建议在开发环境使用。要接入自己的工具，实现一个接受上述 POST 约定的 HTTP 服务，并把域名加进白名单即可。

---

## 一次任务的完整流转

把前面的机制串起来。假设提交一条研究任务"对比欧盟与美国的可再生能源 adoption"：

1. **Gateway（8080）** 鉴权、限流后，把请求转给 Orchestrator。
2. **Orchestrator** 做复杂度评估。这条查询带 `force_research: true`，直接进 Research 策略；否则按复杂度分数在 Simple、DAG、ReAct 之间自动选择。任务被拆成子问题，启一个 Temporal 工作流，预算管理器为任务登记 Token 预算。
3. **Agent Core（Rust）** 作为执行强制网关，负责令牌计数与策略执行；涉及代码生成的部分进 WASI 沙箱执行。
4. **LLM Service** 按研究策略选分层模型（子问题分析用便宜的小模型，综合阶段用大模型），调用搜索/抓取提供商取资料，执行 MCP 工具。
5. 每一步都发事件：`AGENT_STARTED`、`TOOL_INVOKED`、`LLM_PARTIAL`……Gateway 把事件推给订阅了 SSE 的客户端，Prometheus 和 OpenTelemetry 同步记录指标与追踪。
6. 任务结束，结果、令牌用量与完整事件历史落 PostgreSQL。之后任何时候都可以用 Temporal UI 或重放脚本逐步回放这次执行。

理解了这条链路，文章余下部分的安全与成本机制，都能对应到链路上的具体环节。

---

## 安全与成本控制

### WASI 沙箱执行代码

Shannon 的代码执行不依赖容器，而是把 Python 3.11.4 编译好的 WASI 解释器（安装器自动下载到 `wasm-interpreters/`）跑在 Rust 实现的 Agent Core 里：无网络访问、文件系统按会话工作区隔离、内存和时长都有硬限制。危险系统调用在解释器层面就被挡下：

```bash
./scripts/submit_task.sh "Execute Python: import os; os.system('rm -rf /')"
# 结果：os.system 触发的系统调用被 WASI 沙箱拦截
```

这个脚本走 gRPC 直连 Orchestrator（50052），依赖本机装有 grpcurl；日常走 REST API 提交效果相同。

相关环境变量：

```bash
PYTHON_WASI_WASM_PATH=./wasm-interpreters/python-3.11.4.wasm  # 解释器路径
WASI_MEMORY_LIMIT_MB=512       # 内存上限
WASI_TIMEOUT_SECONDS=60        # 单次执行超时
PYTHON_WASI_SESSION_TIMEOUT=3600   # 会话工作区存活时间
SHANNON_USE_WASI_SANDBOX=0     # 文件操作是否路由经沙箱，默认关闭
```

边界也要说清：沙箱里只有标准库可用，依赖 C 扩展的三方包（numpy 之类）装不进去；需要重计算的任务更适合交给外部工具而非沙箱内联代码。

### Token 预算与自动降级

给任务的 `context` 设 `budget_max`（单位 Token）。预算管理器的默认值：单任务 10K、单会话 50K，可通过配置调整。消耗超过 80% 阈值时发 `BUDGET_THRESHOLD` 告警事件，并按模型分层配置自动切到更便宜的档位（small 档优先模型，配置缺失时回退 `gpt-5-nano`），把成本锁在设置范围内。

```bash
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Generate a market analysis report",
    "context": {
      "budget_max": 5000
    }
  }'
```

注意预算字段挂在 `context` 下，不是独立的 `config` 对象；降级模型由模型分层配置决定，请求里没有 `fallback_model` 这样的字段。想更细可以再加 `budget_agent_min`，保证 Swarm 里每个智能体分到最低预算。

### OPA 策略限权

Orchestrator 侧用 Open Policy Agent 统一执行策略，策略文件在 `config/opa/policies/`：`base.rego`、`security.rego` 是全局基线，每个团队一个子目录，比如 `teams/data-science/policy.rego`。一条真实的团队策略长这样：

```rego
package shannon.task

import future.keywords.if
import future.keywords.in

# 数据科学团队可用高档模型，预算上限 50K
allow_model(model) if {
    input.context.team == "data-science"
    model in ["gpt-5-2025-08-07", "claude-sonnet-4-5-20250929"]
}

max_tokens := 50000 if {
    input.context.team == "data-science"
}

allow_tool(_) if {
    input.context.team == "data-science"
}
```

策略按 `input.context.team` 匹配请求上下文，产出 `allow`、`max_tokens`、`allow_tool` 三类决策。"哪个团队能用哪个模型、哪些团队禁用什么工具"都在这一层收口，不用散落到各服务里。

### 搜索与抓取提供商

研究策略依赖搜索和网页抓取，两者都可选多家提供商：

```bash
# 搜索：searchapi | serper | serpapi | bing | exa | firecrawl
WEB_SEARCH_PROVIDER=searchapi
SEARCHAPI_API_KEY=your-searchapi-key
# 或 SERPAPI_API_KEY / SERPER_API_KEY / BING_API_KEY / EXA_API_KEY

# 抓取：firecrawl | exa | python
WEB_FETCH_PROVIDER=firecrawl            # 生产推荐，支持 JS 渲染与深度抓取
FIRECRAWL_API_KEY=your-firecrawl-key
```

`python` 抓取档免费快速，但不渲染 JS、只抓单页，适合内网或静态页面。

### 时间旅行调试

生产上的失败任务可以整条重放：每个决策、每次工具调用、每个状态变化都会被还原出来。入口有两个——脚本重放和 Temporal UI（8088 端口）：

```bash
./scripts/replay_workflow.sh task-prod-failure-123

# 输出显示每个决策、工具调用和状态变化
```

这依赖一个前提：所有状态都走 Temporal 持久化，事件历史落 PostgreSQL。这也是为什么 Shannon 把"可回放"当成架构属性而不是事后补的日志功能。

---

## 排错

### 服务起不来

先查环境变量、端口占用，再重启容器：

```bash
# 检查 .env 是否有所需 API Key
grep API_KEY .env

# 确保端口未被占用
netstat -an | grep -E '8080|8081|50052'

# 重启服务
docker compose down
docker compose up -d
```

### 任务提交报认证/配置错误

按顺序核对 Key、日志和配置目录：

```bash
# 验证 API Key 已导入容器环境（Key 注入在 llm-service）
docker compose exec llm-service env | grep API_KEY

# 检查 orchestrator 日志
docker compose logs -f orchestrator

# 确认配置文件在位
ls config/
```

### 内存或历史占用过高

收缩 WASI 内存上限和历史窗口，再看 Docker 侧的资源限制：

```bash
# 降低 WASI 内存限制（默认：512MB）
WASI_MEMORY_LIMIT_MB=256

# 降低历史窗口（默认：50条消息）
HISTORY_WINDOW_MESSAGES=20

# 检查容器资源占用
docker stats
```

### 查看日志

需要定位跨服务问题时，按服务维度取日志：

```bash
docker compose logs -f                    # 所有服务
docker compose logs -f orchestrator       # 编排与预算
docker compose logs -f gateway            # REST 与事件流
docker compose logs -f llm-service        # 模型调用与工具
```

---

## 项目结构

```text
Shannon/
├── go/orchestrator/          # 编排器与网关（Go）
│   ├── cmd/gateway/          # REST 网关：鉴权、限流、路由
│   └── internal/             # 工作流、策略、预算管理、活动
├── rust/agent-core/          # 执行强制网关与 WASI 沙箱（Rust）
├── python/llm-service/       # 提供商抽象、MCP 工具、agent loop（Python）
├── desktop/                  # Tauri v2 + Next.js 桌面应用
├── clients/python/           # Python SDK（shannon-sdk）
├── protos/                   # 共享 protobuf 定义
├── config/                   # YAML 配置：shannon.yaml、models.yaml、
│                             #   features.yaml、openai_models.yaml、
│                             #   research_strategies.yaml、rate_limits.yaml、
│                             #   opa/policies/、skills/
├── deploy/compose/           # 本地开发与 release 的 Docker Compose
├── migrations/               # PostgreSQL 迁移
├── scripts/                  # install.sh、replay_workflow.sh 等自动化脚本
├── docs/                     # 架构与 API 文档
├── examples/                 # 示例
└── tests/                    # 端到端与集成测试
```

---

## 总结与采用建议

### Shannon 强在哪里

Shannon 的竞争力不在模型调用层——这块 LangChain、CrewAI 都能做。它的差异在于把多智能体执行改造成一套可观测、可回放、可审计的系统：

- **Temporal 工作流**让每次执行都变成可回放的时间线。生产上的智能体出问题不是 if 而是 when，能回放意味着能定位。
- **硬性 Token 预算**不是建议而是硬限制——80% 阈值触发告警事件并自动降级，成本不会在你睡觉时飞涨。
- **WASI 沙箱**把代码执行锁进无网络、文件系统隔离的解释器里，和 OPA 策略、多租户隔离一起构成多层防线。
- **10+ 提供商 + 自动故障转移**让你不绑在任何一家模型上，Research 策略的分层调度还能把研究类任务的成本压下来。

### 什么场景适合引入

| 场景 | 为什么 Shannon 合适 |
|------|------|
| 企业内部 AI 应用 | 多租户隔离、审计追踪、本地部署，合规需求直接满足 |
| 需要多智能体协作的研究/分析任务 | Research + Swarm + Domain Analysis 覆盖从研究综合到 P2P 协作 |
| 涉及代码执行或敏感操作的自动化 | WASI 沙箱 + Human-in-the-Loop 审批构成安全防线 |
| 需要定时运行的日报/周报/分析任务 | Scheduled 接口原生支持 cron 与单次运行成本上限 |

### 什么场景不必急着上

- 只是链式调用几个 LLM、不需要多智能体协作——LangChain 或直接调 API 更轻量。
- 团队还在做原型验证、没进生产——Temporal + WASI + OPA 这一层对原型阶段是过度设计。
- 任务以单次对话为主，没有多步执行和状态管理需求。

### 从哪里开始

建议的采用路径：

1. 用安装脚本跑起来，走通一条 Research 任务，对照"一次任务的完整流转"理解 Gateway → Orchestrator → Agent Core → LLM Service 的分工。
2. 配置 `context.budget_max`，观察 `BUDGET_THRESHOLD` 事件触发后模型如何降级。
3. 打开 `APPROVAL_ENABLED`，提交一条 `require_approval: true` 的任务，用 daemon 客户端或审批端点走完一次审批闭环。
4. 按团队写 OPA 策略，把模型和工具权限收口。
5. 最后接 Prometheus 指标和 OpenTelemetry 追踪，建立持续的可观测性。

### 项目信息

| 项目 | 信息 |
|------|------|
| **许可证** | MIT |
| **最新版本** | v0.5.1（2026-06-02） |
| **主语言** | Go（~46%）、Python（~32%）、TypeScript（~10%）、Rust（~7%） |
| **官网** | [shannon.run](https://shannon.run) |
| **文档** | [docs.shannon.run](https://docs.shannon.run) |
| **GitHub** | [github.com/Kocoro-lab/Shannon](https://github.com/Kocoro-lab/Shannon) |

---

## 参考来源与口径说明

- 仓库数据（Stars/Forks/贡献者/语言占比）：GitHub API，2026-09-25 核对。
- 版本信息：GitHub Releases，v0.5.1 发布于 2026-06-02。
- 安装流程、执行策略、提供商清单、端口表：仓库 README（main 分支）。
- 预算阈值、MCP 环境变量、schedules 字段、OPA 策略结构：`go/orchestrator/internal/budget/manager.go`、`python/llm-service/llm_service/mcp_client.py`、`go/orchestrator/internal/schedules/types.go`、`config/opa/policies/teams/data-science/policy.rego` 等源码文件，2026-09-25 核对。
- "Research 策略省 50-70% 成本"为项目 README 自述口径，未独立复测。
