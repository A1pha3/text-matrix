---
title: "Shannon：生产级多智能体编排框架完全指南"
slug: "shannon-multi-agent-orchestration-framework-guide"
aliases:
  - /posts/tech/shannon-multi-agent-orchestration-framework-guide/
date: 2026-04-01T10:15:00+08:00
categories: ["技术笔记"]
tags: ["Shannon", "多智能体", "Multi-Agent", "Orchestration", "WASI", "Token Budget", "生产级AI", "Human-in-the-Loop", "Swarm", "Temporal"]
description: "深度解析 Shannon：生产级多智能体编排框架，支持Research/Swarm/Human-in-the-Loop/Scheduled四大策略，WASI沙箱安全执行，Token预算控制，15+ LLM提供商，MIT许可证，Go主语言。"
---

# Shannon：生产级多智能体编排框架完全指南

> 预计阅读时间：40分钟 | 难度：⭐⭐⭐⭐

---

## 学习目标

完成本文档后，你将能够：

- ✅ 理解 Shannon 的定位与核心设计理念
- ✅ 掌握 Shannon 的四大核心执行策略
- ✅ 部署和配置 Shannon 开发环境
- ✅ 使用多种方式与 Shannon 交互（REST API / Python SDK / 桌面应用 / Web UI）
- ✅ 配置多 LLM 提供商和工具集成
- ✅ 理解 Swarm 多智能体协作机制
- ✅ 实施 WASI 沙箱安全代码执行
- ✅ 配置 Token 预算控制和自动模型降级
- ✅ 实现 Human-in-the-Loop 审批工作流
- ✅ 掌握时间旅行调试和问题排查

---

## §2 项目概述

### 2.1 什么是 Shannon？

**Shannon**（[GitHub 仓库](https://github.com/Kocoro-lab/Shannon)）是一个**生产级多智能体编排框架**，核心理念是：

> **"Ship reliable AI agents to production."** — 将可靠的 AI 智能体部署到生产环境。

**官网**：[shannon.run](https://shannon.run)
**文档**：[docs.shannon.run](https://docs.shannon.run)
**最新版本**：v0.3.1

### 2.2 核心数据

| 指标 | 数值 |
|------|------|
| **Stars** | 1,336 |
| **Forks** | 180 |
| **贡献者** | 15+ |
| **License** | MIT |
| **主语言** | Go |
| **其他语言** | Python, TypeScript, Rust |
| **创建时间** | 2025-08-29 |
| **最新更新** | 2026-03-23 |

### 2.3 五大核心特性

| 特性 | 说明 |
|------|------|
| **Temporal Workflows** | 时间旅行调试 — 重放任何执行步骤 |
| **Hard Token Budgets** | 每个任务/智能体硬性 Token 预算，自动模型降级 |
| **Real-time Dashboard** | 实时仪表盘，Prometheus 指标，OpenTelemetry 追踪 |
| **WASI Sandbox** | WASI 沙箱安全代码执行，OPA 策略，多租户隔离 |
| **Multi-Vendor** | 支持 OpenAI、Anthropic、Google、DeepSeek、本地模型 |

### 2.4 Shannon 解决什么问题

| 问题 | Shannon 解决方案 |
|------|----------------|
| 智能体静默失败？ | Temporal 工作流 + 时间旅行调试 — 逐步重放任何执行步骤 |
| 成本失控？ | 每个任务/智能体硬性 Token 预算 + 自动模型降级 |
| 无法观测发生了什么？ | 实时仪表盘、Prometheus 指标、OpenTelemetry 追踪 |
| 安全顾虑？ | WASI 沙箱代码执行、OPA 策略、多租户隔离 |
| 供应商锁定？ | 支持 OpenAI、Anthropic、Google、DeepSeek、本地模型 |

---

## §3 核心架构

### 3.1 技术栈

| 组件 | 语言 | 说明 |
|------|------|------|
| **Orchestrator** | Go | 任务路由、预算执行、会话管理、OPA 策略 |
| **Agent Core** | Rust | WASI 沙箱、策略执行、会话工作区、文件操作 |
| **LLM Service** | Python | 提供商抽象（15+ LLM）、MCP 工具、技能系统 |
| **Data Layer** | PostgreSQL + Redis + Qdrant | 状态存储、会话、向量记忆 |

### 3.2 语言占比

| 语言 | 代码量 | 占比 |
|------|--------|------|
| **Go** | 3,604,681 bytes | 约 52% |
| **Python** | 2,388,087 bytes | 约 34% |
| **TypeScript** | 817,767 bytes | 约 12% |
| **Rust** | 472,131 bytes | 约 7% |

### 3.3 架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Shannon 平台架构                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │  REST API   │  │ Python SDK  │  │  Desktop    │  │  Web UI   │ │
│  │  :8080      │  │             │  │  App        │  │  :3000    │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬─────┘ │
│         │                │                │                │         │
│         └────────────────┼────────────────┼────────────────┘         │
│                          │                │                          │
│                    ┌─────┴────────────────┴─────┐                    │
│                    │       Gateway (:8080)       │                    │
│                    │  OpenAI 兼容 API /v1       │                    │
│                    └─────────────┬──────────────┘                    │
│                                  │                                    │
│                    ┌─────────────┴──────────────┐                    │
│                    │     Orchestrator (Go)      │                    │
│                    │  • 任务路由                 │                    │
│                    │  • 预算执行                 │                    │
│                    │  • 会话管理                 │                    │
│                    │  • OPA 策略                 │                    │
│                    └─────────────┬──────────────┘                    │
│                                  │                                    │
│         ┌────────────────────────┼────────────────────────┐          │
│         │                        │                        │          │
│  ┌──────┴──────┐        ┌───────┴───────┐        ┌──────┴──────┐  │
│  │ Agent Core  │        │  LLM Service   │        │  Temporal   │  │
│  │   (Rust)    │        │   (Python)    │        │  Workflow   │  │
│  │             │        │              │        │   Engine    │  │
│  │ • WASI 沙箱  │        │ • 15+ LLM    │        │             │  │
│  │ • 策略执行   │        │ • MCP 工具   │        │ • 时间旅行  │  │
│  │ • 会话工作区│        │ • 技能系统   │        │ • 重放调试  │  │
│  └─────────────┘        └───────────────┘        └─────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     数据层                                     │   │
│  │  PostgreSQL (状态)  │  Redis (会话)  │  Qdrant (向量记忆)  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.4 服务端口

| 服务 | 端口 | 端点 | 用途 |
|------|------|------|------|
| **Gateway** | 8080 | `http://localhost:8080` | REST API，OpenAI 兼容 `/v1` |
| **Admin/Events** | 8081 | `http://localhost:8081` | SSE/WebSocket 流，健康检查 |
| **Orchestrator** | 50052 | `localhost:50052` | gRPC（内部） |
| **Temporal UI** | 8088 | `http://localhost:8088` | 工作流调试 |
| **Grafana** | 3030 | `http://localhost:3030` | 指标仪表盘 |

---

## §4 快速开始

### 4.1 环境要求

- **Docker 和 Docker Compose**
- **至少一个 LLM 提供商的 API Key**（OpenAI、Anthropic 等）

### 4.2 一键安装

```bash
curl -fsSL https://raw.githubusercontent.com/Kocoro-lab/Shannon/v0.3.1/scripts/install.sh | bash
```

安装脚本会：
1. 下载配置文件
2. 提示输入 API Key
3. 拉取 Docker 镜像
4. 启动服务

### 4.3 配置 API Key

安装后，编辑 `.env` 文件：

```bash
cd ~/shannon     # 或你的安装目录
nano .env        # 编辑 API Key
docker compose -f docker-compose.release.yml down
docker compose -f docker-compose.release.yml up -d
```

**必需 API Key**（任选其一）：

| 提供商 | 环境变量 | Key 格式 |
|--------|----------|----------|
| **OpenAI** | `OPENAI_API_KEY` | `sk-...` |
| **Anthropic** | `ANTHROPIC_API_KEY` | `sk-ant-...` |
| **OpenAI 兼容端点** | `OPENAI_API_BASE` | `http://...` |

**可选但推荐**：

| 服务 | 环境变量 | 获取地址 |
|------|----------|----------|
| **Web 搜索** | `SERPAPI_API_KEY` | [serpapi.com](https://serpapi.com) |
| **Web 抓取** | `FIRECRAWL_API_KEY` | [firecrawl.dev](https://firecrawl.dev) |

### 4.4 验证安装

```bash
# 检查所有服务状态
docker compose -f deploy/compose/docker-compose.release.yml ps

# Gateway 健康检查
curl http://localhost:8080/health

# Admin 健康检查
curl http://localhost:8081/health
```

---

## §5 四种交互方式

Shannon 提供了四种与 AI 智能体交互的方式，选择最适合你的：

### 5.1 REST API

适用于：集成到现有应用、自动化脚本、跨语言集成。

```bash
# 提交任务
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the capital of France?",
    "session_id": "demo-session"
  }'

# 响应：{"task_id":"task-dev-123","status":"running"}

# 实时流式事件
curl -N "http://localhost:8080/api/v1/stream/sse?workflow_id=task-dev-123"

# 获取最终结果
curl "http://localhost:8080/api/v1/tasks/task-dev-123"
```

### 5.2 Python SDK

适用于：Python 应用、Jupyter notebooks、数据科学工作流、批处理。

```bash
pip install shannon-sdk
```

```python
from shannon import ShannonClient

# 创建客户端
with ShannonClient(base_url="http://localhost:8080") as client:
    # 提交任务
    handle = client.submit_task(
        "What is the capital of France?",
        session_id="demo-session"
    )

    # 等待完成
    result = client.wait(handle.task_id)
    print(result.result)
```

### 5.3 桌面应用

适用于：系统托盘集成、本地通知、离线任务历史、更好的性能。

**下载地址**（[GitHub Releases](https://github.com/Kocoro-lab/Shannon/releases/latest)）：

| 平台 | 安装包 |
|------|--------|
| **macOS (通用)** | Intel & Apple Silicon |
| **Windows (x64)** | MSI 或 EXE 安装包 |
| **Linux (x64)** | AppImage 或 DEB 包 |

桌面应用特性：
- 系统托盘集成 + 原生通知
- 离线任务历史（Dexie.js 本地数据库）
- 更低内存占用
- 自动从 GitHub Releases 更新

### 5.4 Web UI

适用于：快速测试和探索、开发调试、实时事件流可视化。

```bash
# 在后端运行后，新开终端
cd desktop
npm install
npm run dev

# 浏览器打开 http://localhost:3000
```

---

## §6 核心执行策略

Shannon 提供了四种核心执行策略，适应不同场景：

### 6.1 Research Workflow（研究工作流）

多智能体研究 + 自动综合，支持自动引用。

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
# 编排多个研究智能体，综合发现和引用
```

### 6.2 Swarm Workflow（蜂群工作流）

多智能体 P2P 消息传递协作。主管智能体规划并协调；工作智能体通过共享工作区执行。

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

### 6.3 Human-in-the-Loop（人在回路）

任务可在敏感操作前暂停等待人工审批。

```bash
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Update the production database schema",
    "context": {
      "require_approval": true
    }
  }'
# 工作流暂停，等待明确的人工审批后继续
```

### 6.4 Scheduled Tasks（定时任务）

使用 cron 语法调度任务。

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

---

## §7 核心功能详解

### 7.1 OpenAI 兼容 API

Shannon 提供 OpenAI 兼容 API，现有 OpenAI 代码无需修改即可迁移：

```bash
export OPENAI_API_BASE=http://localhost:8080/v1
# 你的现有 OpenAI 代码保持不变
```

### 7.2 实时事件流

```bash
# 监控智能体执行（SSE）
curl -N "http://localhost:8080/api/v1/stream/sse?workflow_id=task-dev-123"

# 事件类型：
# - WORKFLOW_STARTED, WORKFLOW_COMPLETED
# - AGENT_STARTED, AGENT_COMPLETED
# - TOOL_INVOKED, TOOL_OBSERVATION
# - LLM_PARTIAL, LLM_OUTPUT
```

### 7.3 技能系统

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

在 `config/skills/user/` 中创建自定义技能。

### 7.4 WASI 沙箱与工作区

每个会话在 `/tmp/shannon-sessions/{session_id}/` 有独立工作区：

```bash
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Run this Python script and save the output",
    "session_id": "my-workspace"
  }'
```

WASI 沙箱提供安全代码执行，无系统调用访问。

### 7.5 会话连续性

多轮对话，上下文记忆：

```bash
# 第一轮
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"query": "What is GDP?", "session_id": "econ-101"}'

# 后续记得上下文
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"query": "How does it relate to inflation?", "session_id": "econ-101"}'
# 智能体回忆同一会话的近期对话历史
```

---

## §8 支持的 LLM 提供商

Shannon 支持 **15+ LLM 提供商**，已充分验证：

| 提供商 | 模型示例 | 状态 |
|--------|----------|------|
| **OpenAI** | GPT-5.1, GPT-5 mini, GPT-5 nano | ✅ 充分验证 |
| **Anthropic** | Claude Opus 4.6, Sonnet 4.6, Haiku 4.5 | ✅ 充分验证 |
| **Google** | Gemini 2.5 Pro, Gemini 2.5 Flash, Gemini 3 Pro Preview | ✅ 充分验证 |
| **xAI** | Grok 4 | ✅ 充分验证 |
| **DeepSeek** | DeepSeek V3.2, DeepSeek R1 | ✅ 充分验证 |
| **Qwen** | Qwen 系列 | 🔶 支持但未充分验证 |
| **Mistral** | Mistral 系列 | 🔶 支持但未充分验证 |
| **Meta** | Llama 4 | 🔶 支持但未充分验证 |
| **Zhipu** | GLM-4.6 | 🔶 支持但未充分验证 |
| **Cohere** | Cohere 系列 | 🔶 支持但未充分验证 |
| **Ollama** | Llama, Mistral, Phi 等 | 🔶 支持但未充分验证 |
| **LM Studio** | 本地模型 | 🔶 支持但未充分验证 |
| **vLLM** | OpenAI 兼容端点 | 🔶 支持但未充分验证 |

**自动故障转移**：当主模型达到预算限制时，自动切换到备用模型。

---

## §9 MCP 集成

Shannon 原生支持 Model Context Protocol：

- 自定义工具注册
- OAuth2 服务器认证
- 速率限制和断路器
- MCP 工具使用成本追踪

### 9.1 MCP 配置示例

```yaml
# config/mcp.yaml
mcp_servers:
  - name: "filesystem"
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    enabled: true
```

---

## §10 安全机制

### 10.1 WASI 沙箱

Python 在隔离的 WASI 沙箱中运行 — 无网络、只读文件系统：

```bash
./scripts/submit_task.sh "Execute Python: import os; os.system('rm -rf /')"
# 结果：OSError - 系统调用被 WASI 沙箱阻止
```

### 10.2 Token 预算控制

```bash
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Generate a market analysis report",
    "config": {
      "budget": {
        "max_tokens": 5000,
        "fallback_model": "gpt-5-mini"
      }
    }
  }'
# 当消耗 80% 预算时自动切换到更便宜的模型
```

### 10.3 OPA 策略治理

```rego
# config/opa/policies/teams.rego
package shannon.teams

allow {
    input.team == "data-science"
    input.model in ["gpt-5", "claude-sonnet-4-5-20250929"]
}

deny_tool["database_write"] {
    input.team == "support"
}
```

### 10.4 多租户隔离

- 每个租户独立的记忆、预算和策略
- 完整的数据访问审计追踪
- 可部署在企业内部，无需云依赖

---

## §11 工具 API 配置

### 11.1 Web 搜索配置

```bash
# 选择提供商
WEB_SEARCH_PROVIDER=serpapi             # serpapi | searchapi | google | bing | exa
SERPAPI_API_KEY=your-serpapi-key        # serpapi.com
```

### 11.2 Web 抓取配置

```bash
# 用于深度研究
WEB_FETCH_PROVIDER=firecrawl            # firecrawl | exa | python
FIRECRAWL_API_KEY=your-firecrawl-key   # firecrawl.dev（生产推荐）
```

---

## §12 时间旅行调试

生产智能体失败了？本地逐步重放：

```bash
# 重放失败的工作流
./scripts/replay_workflow.sh task-prod-failure-123

# 输出显示每个决策、工具调用和状态变化
```

---

## §13 企业级特性

| 特性 | 说明 |
|------|------|
| **多租户隔离** | 每个租户独立的记忆、预算和策略 |
| **人在回路** | 审批中间件在敏感操作前暂停工作流等待人工审查 |
| **审计追踪** | 完整记录每个决策和数据访问 |
| **本地部署就绪** | 无云依赖，完全运行在你的基础设施 |

---

## §14 配置指南

Shannon 使用分层配置：

1. **环境变量**（`.env`）— API Key、密钥
2. **YAML 文件**（`config/`）— 功能开关、模型定价、策略

关键文件：

| 文件 | 用途 |
|------|------|
| `config/models.yaml` | LLM 提供商、定价、层级配置 |
| `config/features.yaml` | 功能开关、工作流设置 |
| `config/opa/policies/` | 访问控制规则 |
| `config/skills/user/` | 自定义技能 |

---

## §15 故障排查

### 15.1 服务不启动

```bash
# 检查 .env 是否有所需 API Key
cat .env | grep API_KEY

# 确保端口未被占用
netstat -an | grep -E '8080|8081|50052'

# 重启服务
docker compose -f deploy/compose/docker-compose.release.yml down
docker compose -f deploy/compose/docker-compose.release.yml up -d
```

### 15.2 任务执行失败

```bash
# 验证 API Key 有效
echo $OPENAI_API_KEY

# 检查 orchestrator 日志
docker compose -f deploy/compose/docker-compose.release.yml logs -f orchestrator

# 确保配置文件存在于 ./config/ 目录
ls -la config/
```

### 15.3 内存不足

```bash
# 降低 WASI 内存限制（默认：512MB）
WASI_MEMORY_LIMIT_MB=256

# 降低历史窗口（默认：50条消息）
HISTORY_WINDOW_MESSAGES=20

# 检查 Docker 内存限制
docker stats
```

### 15.4 查看日志

```bash
# 所有服务
docker compose -f deploy/compose/docker-compose.release.yml logs -f

# 指定服务
docker compose -f deploy/compose/docker-compose.release.yml logs -f orchestrator
docker compose -f deploy/compose/docker-compose.release.yml logs -f gateway
docker compose -f deploy/compose/docker-compose.release.yml logs -f llm-service
```

---

## §16 常见问题

### Q1: Shannon 和 LangChain Agents 有什么区别？

Shannon 专注于生产级多智能体编排，强调可靠性、可观测性和成本控制。LangChain 更偏向于链式调用和原型开发。

### Q2: 支持中国模型吗？

支持 DeepSeek（国产）、Zhipu（智谱 GLM），但验证程度不如 OpenAI/Anthropic/Google。

### Q3: 如何确保代码安全执行？

Python 等代码在 WASI 沙箱中执行，无系统调用权限、只读文件系统、无法访问网络。

### Q4: 支持私有化部署吗？

完全支持，无云依赖，所有数据留在本地。

### Q5: 如何参与贡献？

欢迎提交 PR！参见 [CONTRIBUTING.md](https://github.com/Kocoro-lab/Shannon/blob/main/CONTRIBUTING.md)。

---

## §17 项目结构

```
Shannon/
├── config/                    # 配置文件
│   ├── models.yaml            # LLM 模型配置
│   ├── features.yaml          # 功能开关
│   ├── opa/policies/          # OPA 策略
│   └── skills/user/           # 自定义技能
├── desktop/                   # 桌面应用（TypeScript）
├── docs/                      # 文档
│   └── images/                # 架构图
├── scripts/                   # 脚本
│   ├── install.sh             # 安装脚本
│   └── replay_workflow.sh    # 时间旅行调试
├── gateway/                   # API 网关（Go）
├── orchestrator/              # 编排器（Go）
├── agent-core/                # 智能体核心（Rust）
├── llm-service/               # LLM 服务（Python）
├── temporal/                  # Temporal 工作流引擎
├── deploy/
│   └── compose/
│       └── docker-compose.release.yml
├── CONTRIBUTING.md
├── LICENSE (MIT)
└── README.md
```

---

## §18 总结

### 18.1 核心优势

| 优势 | 说明 |
|------|------|
| **生产就绪** | 完整的可观测性、预算控制、审计追踪 |
| **多智能体编排** | Research、Swarm、Human-in-the-Loop、Scheduled 四种策略 |
| **安全执行** | WASI 沙箱隔离、OPA 策略治理 |
| **成本控制** | Token 预算、自动模型降级 |
| **多提供商** | 15+ LLM 支持，自动故障转移 |
| **本地部署** | 无云依赖，完全私有化 |

### 18.2 适用场景

| 场景 | 说明 |
|------|------|
| **企业 AI 应用** | 多租户隔离、审计追踪、合规 |
| **研究自动化** | 多智能体协作、自动引用 |
| **开发辅助** | 代码审查、自动化测试 |
| **定时任务** | 每日报告、定期分析 |
| **客服系统** | Human-in-the-Loop 审批 |

### 18.3 项目信息

| 项目 | 信息 |
|------|------|
| **许可证** | MIT |
| **主语言** | Go |
| **最新版本** | v0.3.1 |
| **官网** | [shannon.run](https://shannon.run) |
| **文档** | [docs.shannon.run](https://docs.shannon.run) |
| **GitHub** | [github.com/Kocoro-lab/Shannon](https://github.com/Kocoro-lab/Shannon) |

---

*文档版本 1.0 | 撰写日期：2026-04-01 | 基于 Shannon v0.3.1 (MIT)*