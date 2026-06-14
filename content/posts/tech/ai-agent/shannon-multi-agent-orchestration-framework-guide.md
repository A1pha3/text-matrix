---
title: "Shannon：生产级多智能体编排框架完全指南"
slug: "shannon-multi-agent-orchestration-framework-guide"
aliases:
  - /posts/tech/shannon-multi-agent-orchestration-framework-guide/
date: "2026-04-01T10:15:00+08:00"
categories: ["技术笔记"]
tags: ["Shannon", "多智能体", "Multi-Agent", "Orchestration", "WASI", "Token Budget", "生产级AI", "Human-in-the-Loop", "Swarm", "Temporal"]
description: "Shannon 把多智能体编排从原型推到生产：Temporal 工作流保证可回放、WASI 沙箱隔离代码执行、硬性 Token 预算防止成本失控，15+ LLM 提供商，MIT 许可证。"
---

# Shannon：把多智能体编排推到生产环境

Shannon 不只是在多个模型之间做路由。它用 Temporal 工作流引擎把每次执行变成可回放的记录，用 WASI 沙箱把代码执行锁在隔离环境里，再用硬性 Token 预算把成本钉在可控范围。读完这篇文章，你会知道它和 LangChain 这类原型框架的区别在哪里，以及什么场景下值得把它引入你的基础设施。

---

## 学习目标

完成本文后，可以：

- 理解 Shannon 的定位与核心设计理念
- 掌握 Shannon 的四大核心执行策略
- 部署和配置 Shannon 开发环境
- 使用多种方式与 Shannon 交互（REST API / Python SDK / 桌面应用 / Web UI）
- 配置多 LLM 提供商和工具集成
- 理解 Swarm 多智能体协作机制
- 实施 WASI 沙箱安全代码执行
- 配置 Token 预算控制和自动模型降级
- 实现 Human-in-the-Loop 审批工作流
- 掌握时间旅行调试和问题排查

---

## 项目概述

### 什么是 Shannon？

**Shannon**（[GitHub 仓库](https://github.com/Kocoro-lab/Shannon)）是一个生产级多智能体编排框架。它的设计目标只有一个：

> **"Ship reliable AI agents to production."** — 把可靠的 AI 智能体部署到生产环境。

大多数 AI Agent 框架解决的是"怎么调用模型、怎么串联工具"。Shannon 解决的是调用之后的事：执行过程能不能回放？成本会不会跑飞？代码执行有没有隔离？多租户之间怎么不互相干扰？

**官网**：[shannon.run](https://shannon.run)
**文档**：[docs.shannon.run](https://docs.shannon.run)
**最新版本**：v0.3.1

### 项目数据

Shannon 于 2025 年 8 月开源，MIT 许可证，主语言 Go，辅以 Python、TypeScript 和 Rust。截至 2026 年 3 月，社区积累约 1,336 Stars、180 Forks，来自 15 位以上贡献者。

### 五个核心设计选择

| 特性 | 说明 |
|------|------|
| **Temporal Workflows** | 时间旅行调试 — 重放任何执行步骤 |
| **Hard Token Budgets** | 每个任务/智能体硬性 Token 预算，自动模型降级 |
| **Real-time Dashboard** | 实时仪表盘，Prometheus 指标，OpenTelemetry 追踪 |
| **WASI Sandbox** | WASI 沙箱安全代码执行，OPA 策略，多租户隔离 |
| **Multi-Vendor** | 支持 OpenAI、Anthropic、Google、DeepSeek、本地模型 |

### Shannon 解决什么问题

Shannon 的设计直接回应了生产环境 AI Agent 的几个高频故障模式：

| 你在生产环境遇到的问题 | Shannon 的应对方式 |
|------|----------------|
| 智能体静默失败，查不出原因 | Temporal 工作流 + 时间旅行调试 — 逐步重放任何执行步骤 |
| Token 消耗失控，账单意外暴涨 | 每个任务/智能体硬性 Token 预算 + 自动模型降级 |
| 执行过程黑盒，不知道发生了什么 | 实时仪表盘、Prometheus 指标、OpenTelemetry 追踪 |
| 代码执行安全风险 | WASI 沙箱代码执行、OPA 策略、多租户隔离 |
| 被单一 LLM 提供商绑定 | 支持 OpenAI、Anthropic、Google、DeepSeek、本地模型 |

---

## 核心架构

### 技术栈

| 组件 | 语言 | 说明 |
|------|------|------|
| **Orchestrator** | Go | 任务路由、预算执行、会话管理、OPA 策略 |
| **Agent Core** | Rust | WASI 沙箱、策略执行、会话工作区、文件操作 |
| **LLM Service** | Python | 提供商抽象（15+ LLM）、MCP 工具、技能系统 |
| **Data Layer** | PostgreSQL + Redis + Qdrant | 状态存储、会话、向量记忆 |

### 语言占比

| 语言 | 代码量 | 占比 |
|------|--------|------|
| **Go** | 3,604,681 bytes | 约 52% |
| **Python** | 2,388,087 bytes | 约 34% |
| **TypeScript** | 817,767 bytes | 约 12% |
| **Rust** | 472,131 bytes | 约 7% |

### 架构图

```text

### 服务端口

| 服务 | 端口 | 端点 | 用途 |
|------|------|------|------|
| **Gateway** | 8080 | `http://localhost:8080` | REST API，OpenAI 兼容 `/v1` |
| **Admin/Events** | 8081 | `http://localhost:8081` | SSE/WebSocket 流，健康检查 |
| **Orchestrator** | 50052 | `localhost:50052` | gRPC（内部） |
| **Temporal UI** | 8088 | `http://localhost:8088` | 工作流调试 |
| **Grafana** | 3030 | `http://localhost:3030` | 指标仪表盘 |

---

## 快速开始

### 环境要求

- **Docker 和 Docker Compose**
- **至少一个 LLM 提供商的 API Key**（OpenAI、Anthropic 等）

### 一键安装

```bash
curl -fsSL https://raw.githubusercontent.com/Kocoro-lab/Shannon/v0.3.1/scripts/install.sh | bash
```textbash
cd ~/shannon     # 或你的安装目录
nano .env        # 编辑 API Key
docker compose -f docker-compose.release.yml down
docker compose -f docker-compose.release.yml up -d
```textbash
# 检查所有服务状态
docker compose -f deploy/compose/docker-compose.release.yml ps

# Gateway 健康检查
curl http://localhost:8080/health

# Admin 健康检查
curl http://localhost:8081/health
```textbash
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
```textbash
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
```textbash
# 在后端运行后，新开终端
cd desktop
npm install
npm run dev

# 浏览器打开 http://localhost:3000
```textbash
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
```textbash
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze this dataset from multiple perspectives",
    "context": {
      "force_swarm": true
    }
  }'
```textbash
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Update the production database schema",
    "context": {
      "require_approval": true
    }
  }'
# 工作流暂停，等待明确的人工审批后继续
```textbash
curl -X POST http://localhost:8080/api/v1/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Market Analysis",
    "cron_expression": "0 9 * * *",
    "task_query": "Analyze market trends",
    "max_budget_per_run_usd": 0.50
  }'
```textbash
export OPENAI_API_BASE=http://localhost:8080/v1
# 你的现有 OpenAI 代码保持不变
```textbash
# 监控智能体执行（SSE）
curl -N "http://localhost:8080/api/v1/stream/sse?workflow_id=task-dev-123"

# 事件类型：
# - WORKFLOW_STARTED, WORKFLOW_COMPLETED
# - AGENT_STARTED, AGENT_COMPLETED
# - TOOL_INVOKED, TOOL_OBSERVATION
# - LLM_PARTIAL, LLM_OUTPUT
```textbash
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
```textbash
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Run this Python script and save the output",
    "session_id": "my-workspace"
  }'
```textbash
# 第一轮
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"query": "What is GDP?", "session_id": "econ-101"}'

# 后续记得上下文
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"query": "How does it relate to inflation?", "session_id": "econ-101"}'
# 智能体回忆同一会话的近期对话历史
```textyaml
# config/mcp.yaml
mcp_servers:
  - name: "filesystem"
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    enabled: true
```textbash
./scripts/submit_task.sh "Execute Python: import os; os.system('rm -rf /')"
# 结果：OSError - 系统调用被 WASI 沙箱阻止
```textbash
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
```textrego
# config/opa/policies/teams.rego
package shannon.teams

allow {
    input.team == "data-science"
    input.model in ["gpt-5", "claude-sonnet-4-5-20250929"]
}

deny_tool["database_write"] {
    input.team == "support"
}
```textbash
# 选择提供商
WEB_SEARCH_PROVIDER=serpapi             # serpapi | searchapi | google | bing | exa
SERPAPI_API_KEY=your-serpapi-key        # serpapi.com
```textbash
# 用于深度研究
WEB_FETCH_PROVIDER=firecrawl            # firecrawl | exa | python
FIRECRAWL_API_KEY=your-firecrawl-key   # firecrawl.dev（生产推荐）
```textbash
# 重放失败的工作流
./scripts/replay_workflow.sh task-prod-failure-123

# 输出显示每个决策、工具调用和状态变化
```textbash
# 检查 .env 是否有所需 API Key
cat .env | grep API_KEY

# 确保端口未被占用
netstat -an | grep -E '8080|8081|50052'

# 重启服务
docker compose -f deploy/compose/docker-compose.release.yml down
docker compose -f deploy/compose/docker-compose.release.yml up -d
```textbash
# 验证 API Key 有效
echo $OPENAI_API_KEY

# 检查 orchestrator 日志
docker compose -f deploy/compose/docker-compose.release.yml logs -f orchestrator

# 确保配置文件存在于 ./config/ 目录
ls -la config/
```textbash
# 降低 WASI 内存限制（默认：512MB）
WASI_MEMORY_LIMIT_MB=256

# 降低历史窗口（默认：50条消息）
HISTORY_WINDOW_MESSAGES=20

# 检查 Docker 内存限制
docker stats
```textbash
# 所有服务
docker compose -f deploy/compose/docker-compose.release.yml logs -f

# 指定服务
docker compose -f deploy/compose/docker-compose.release.yml logs -f orchestrator
docker compose -f deploy/compose/docker-compose.release.yml logs -f gateway
docker compose -f deploy/compose/docker-compose.release.yml logs -f llm-service
```text
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

## 总结与采用建议

### Shannon 强在哪里

Shannon 的核心竞争力不在模型调用层 — 这块 LangChain、CrewAI 都能做。它真正的差异在于把多智能体执行改造成了一套可观测、可回放、可审计的系统：

- **Temporal 工作流**让每次执行都变成可回放的时间线。生产上的智能体出问题不是 if 而是 when，能回放意味着能定位。
- **硬性 Token 预算**不是建议而是硬限制 — 80% 触发自动降级，成本不会在你睡觉时飞涨。
- **WASI 沙箱**把代码执行锁在无网络、只读文件系统的环境里，和 OPA 策略、多租户隔离一起构成三层安全。
- **15+ LLM 提供商 + 自动故障转移**让你不绑在任何一家模型上。

### 什么场景适合引入 Shannon

| 场景 | 为什么 Shannon 合适 |
|------|------|
| 企业内部 AI 应用 | 多租户隔离、审计追踪、本地部署，合规需求直接满足 |
| 需要多智能体协作的研究/分析任务 | Research + Swarm 策略覆盖从研究综合到 P2P 协作 |
| 涉及代码执行或敏感操作的自动化 | WASI 沙箱 + Human-in-the-Loop 审批构成安全防线 |
| 需要定时运行的日报/周报/分析任务 | Scheduled 策略 + cron 表达式原生支持 |

### 什么场景不必急着上

- 你只需要链式调用几个 LLM，不需要多智能体协作 — LangChain 或直接调 API 更轻量。
- 团队还没有在生产跑 AI Agent 的需求，只是在做原型验证 — Shannon 的 Temporal + WASI + OPA 三层对原型阶段是过度设计。
- 你的任务以单次对话为主，没有多步执行和状态管理需求。

### 从哪里开始

建议的采用路径：

1. 先用 REST API 或 Python SDK 跑通一个 Research 任务，理解 Gateway → Orchestrator → LLM Service → Temporal 的基本流转。
2. 配置 Token 预算和自动降级，观察不同模型在不同预算下的行为差异。
3. 引入 WASI 沙箱执行一个带代码生成的任务，确认隔离行为符合预期。
4. 根据业务需求接入 Human-in-the-Loop 或 Scheduled 策略。
5. 最后部署 Grafana 仪表盘和 Prometheus 指标，建立持续的可观测性。

### 项目信息

| 项目 | 信息 |
|------|------|
| **许可证** | MIT |
| **主语言** | Go（~52%），Python（~34%），TypeScript（~12%），Rust（~7%） |
| **最新版本** | v0.3.1 |
| **官网** | [shannon.run](https://shannon.run) |
| **文档** | [docs.shannon.run](https://docs.shannon.run) |
| **GitHub** | [github.com/Kocoro-lab/Shannon](https://github.com/Kocoro-lab/Shannon) |

---

*文档版本 1.0 | 撰写日期：2026-04-01 | 基于 Shannon v0.3.1 (MIT)*