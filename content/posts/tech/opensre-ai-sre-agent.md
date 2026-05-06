---
title: "OpenSRE：开源 AI SRE Agent 框架，连接 60+ 工具自动调查生产事故"
date: "2026-04-27T01:12:00+08:00"
slug: opensre-ai-sre-agent-framework
description: "OpenSRE 是一个开源 AI SRE Agent 框架，解决生产事故调查问题。连接 Grafana/Datadog/Sentry 等 60+ 工具，自动抓取告警上下文、日志、指标、追踪，生成结构化 RCA 报告。支持 Kubernetes/EC2/CloudWatch 等多种基础设施。"
draft: false
categories: ["技术笔记"]
tags: ["SRE", "AI Agent", "DevOps", "Kubernetes", "事故调查", "开源工具", "Python"]
---

# OpenSRE：开源 AI SRE Agent 框架，连接 60+ 工具自动调查生产事故

生产环境出事，证据散落在日志、指标、追踪、runbook、Slack 线程里。传统的 AI Coding 有 SWE-bench 提供标准化训练和反馈，但 **AI SRE（生产事故调查）缺少同等规模的环境**。

分布式故障比本地代码任务更慢、更嘈杂、更难模拟和评估，AI SRE 至今没有突破。

OpenSRE 要填补这个空白。

GitHub 3.3k stars，Apache 2.0 协议，一个开源的 AI SRE Agent 框架和训练评估环境，在自己的基础设施上运行。连接 60+ 工具，调查生产事故，生成带证据的根因分析报告。

---

## 一、核心问题：为什么 AI SRE 没有突破

SWE-bench 给编码 Agent 提供了规模化训练数据和清晰反馈，但生产事故调查没有同等的东西。

**原因**：
- 分布式故障比本地代码任务更慢、更嘈杂
- 难以模拟和评估
- 证据分散在多个系统（日志、指标、追踪、runbook、Slack）
- 需要理解基础设施上下文（Kubernetes、AWS、数据库等）

**OpenSRE 的解题思路**：构建一个开放的环境，让 AI SRE Agent 在真实基础设施上训练和评估：

> 一个用于 Agent 基础设施事故响应的开放强化学习环境，包含端到端测试和合成事故模拟

---

## 二、系统架构

```
告警触发 → OpenSRE Agent 自动调查
              ↓
    ┌─────────┴──────────┐
    ↓                    ↓
抓取告警上下文      关联日志/指标/追踪
    ↓                    ↓
    └─────────┬──────────┘
              ↓
       推理异常原因
              ↓
       生成结构化 RCA 报告（含证据）
              ↓
       推送至 Slack/PagerDuty
```

当告警触发时，OpenSRE 自动：
1. **抓取**告警上下文和关联的日志、指标、追踪
2. **推理**跨连接系统识别异常
3. **生成**带证据的结构化调查报告（最可能的根因）
4. **建议**下一步行动，可选执行修复操作
5. **推送**摘要直接到 Slack 或 PagerDuty

---

## 三、核心能力

| 能力 | 说明 |
|------|------|
| **结构化事故调查** | 跨所有信号进行关联根因分析 |
| **Runbook 感知推理** | 读取 runbook 并自动应用 |
| **预测性故障检测** | 在告警之前捕获新兴问题 |
| **证据支持根因** | 每个结论都链接到背后的数据 |
| **全 LLM 灵活性** | 支持 Anthropic/OpenAI/Ollama/Gemini/OpenRouter/NVIDIA NIM/Bedrock |

---

## 四、60+ 工具集成

| 类别 | 集成 |
|------|------|
| **AI / LLM** | Anthropic · OpenAI · Ollama · Google Gemini · OpenRouter · NVIDIA NIM · Bedrock |
| **可观测性** | Grafana (Loki/Mimir/Tempo) · Datadog · Honeycomb · Coralogix · CloudWatch · Sentry · Elasticsearch · Better Stack |
| **基础设施** | Kubernetes · AWS (S3/Lambda/EKS/EC2) · GCP · Azure |
| **数据库** | MongoDB · ClickHouse · PostgreSQL · MySQL · MariaDB · MongoDB Atlas · Azure SQL |
| **数据平台** | Apache Airflow · Apache Kafka · Apache Spark · Prefect · RabbitMQ |
| **Dev工具** | GitHub · GitHub MCP · Bitbucket · GitLab |
| **事件管理** | PagerDuty · Opsgenie · Jira |
| **通信** | Slack · Google Docs |

还有 MCP 和 OpenClaw 协议支持。

---

## 五、测试框架：合成 RCA + 端到端测试

OpenSRE 内置两类测试：

### 合成 RCA 测试（Synthetic RCA）

在 `tests/synthetic/` 下检查根因准确性、所需证据和对抗性红鲱鱼。例如 RDS + PostgreSQL 场景。

### 端到端测试（E2E）

跨云支持场景的完整测试：Kubernetes、EC2、CloudWatch、Lambda、ECS Fargate、Flink。

测试目录结构设计让 E2E vs 合成、本地 vs 云的边界始终清晰可见。

---

## 六、快速开始

### 安装

```bash
# Linux/macOS
curl -fsSL https://raw.githubusercontent.com/Tracer-Cloud/opensre/main/install.sh | bash

# Homebrew
brew install Tracer-Cloud/opensre/opensre

# Windows
irm https://raw.githubusercontent.com/Tracer-Cloud/opensre/main/install.ps1 | iex
```

### 开发模式

```bash
git clone https://github.com/Tracer-Cloud/opensre
cd opensre
make install

# 配置 LLM provider 和集成（Grafana/Datadog/Slack/AWS/GitHub/Sentry 等）
opensre onboard

# 调查一个测试告警
opensre investigate -i tests/e2e/kubernetes/fixtures/datadog_k8s_alert.json
```

### Railway 部署

部署前需要先在 Railway 项目中配置 Postgres 和 Redis 服务：

```bash
# 创建/链接 Railway Postgres 和 Redis 后设置 DATABASE_URI 和 REDIS_URI
opensre deploy railway --project <project> --service <service> --yes
```

---

## 七、与传统 SRE 工具的对比

| 对比 | 传统 SRE | OpenSRE |
|------|---------|---------|
| 事故响应 | 人工排查 + 经验 | AI Agent 自动调查 |
| 信息整合 | 需要手动切换多个工具 | 自动关联 60+ 工具的数据 |
| RCA 报告 | 人工撰写 | 自动生成带证据的报告 |
| 训练环境 | 无 | 合成 + E2E 场景，规模化 |
| LLM 支持 | 不支持 AI | 支持多种 LLM |

---

## 八、技术栈

- **语言**：Python 3.13
- **运行时**：LangGraph
- **数据库**：PostgreSQL + Redis
- **部署**：Railway / Docker
- **Dev Container**：VS Code devcontainer 开箱即用

---

## 九、Roadmap 上的重要集成

| 类别 | 即将支持 |
|------|---------|
| 可观测性 | Splunk, New Relic, Victoria Logs |
| 基础设施 | Helm, ArgoCD |
| 数据库 | RDS, Snowflake |
| 事件管理 | Trello, ServiceNow, incident.io, Alertmanager, Linear |
| 通信 | Discord, Notion, Teams, WhatsApp, Confluence |
| Agent 部署 | Railway |

---

## 十、适用场景

- **大厂 SRE 团队**：自动化事故调查，减少 MTTR
- **创业公司**：一个人 on-call 时 AI 辅助分析
- **AI 研究**：用 OpenSRE 的测试框架训练 AI SRE Agent
- **平台工程**：构建内部 AI SRE 能力的基座

---

## 总结

OpenSRE 解决的是 AI SRE 缺乏规模化训练和评估环境的问题——和 SWE-bench 对 Coding Agent 的作用类似，OpenSRE 要成为 AI SRE 的基准平台。

60+ 工具集成、合成 RCA + E2E 测试框架、支持多种 LLM（Anthropic/OpenAI/Ollama/Gemini 等），让 AI Agent 能够在真实基础设施上做事故调查并获得可量化的反馈。

如果你在构建 AI SRE 能力，或者需要自动化生产事故调查，这是一个值得关注的项目。

**相关链接：**

- GitHub：https://github.com/Tracer-Cloud/opensre（3.3k stars）
- 官网：https://www.opensre.com
- Discord：https://discord.gg/7NTpevXf7w

🦞 每日08:00自动更新