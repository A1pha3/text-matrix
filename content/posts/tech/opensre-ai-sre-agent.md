---
title: "OpenSRE：开源 AI SRE Agent 框架，连接 60+ 工具自动调查生产事故"
date: "2026-04-27T01:12:00+08:00"
slug: opensre-ai-sre-agent-framework
github_repo: "Tracer-Cloud/opensre"
source_key: "gh:Tracer-Cloud/opensre"
aliases:
  - "/posts/tech/opensre-ai-sre-framework/"
  - "/posts/tech/opensre-ai-sre-agent-toolkit/"
description: "OpenSRE 是一个开源 AI SRE Agent 框架，解决生产事故调查问题。连接 Grafana/Datadog/Sentry 等 60+ 工具，自动抓取告警上下文、日志、指标、追踪，生成结构化 RCA 报告。支持 Kubernetes/EC2/CloudWatch 等多种基础设施。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "DevOps", "Kubernetes", "开源工具", "Python"]
---

# OpenSRE：开源 AI SRE Agent 框架，连接 60+ 工具自动调查生产事故

OpenSRE 想做的不只是再给你一个监控面板，而是把"事故调查"本身做成一套可在真实基础设施上训练、评估的 Agent 环境。它默认只调查、不操作，输出带证据的 RCA 报告，把误操作风险挡在工作流之外。

它连接 60+ 工具，覆盖可观测性、基础设施、数据库、事件管理多个环节；采用 Apache 2.0 协议，GitHub 3.3k stars，可以在你自己的基础设施上跑。

## 一、核心问题：事故调查缺一个 SWE-bench

SWE-bench 给编码 Agent 提供了规模化的训练数据和清晰反馈，这是 AI Coding 快速推进的关键条件之一。生产事故调查一直缺对等的东西。

不是没人想做，而是分布式故障本身的特点卡住了这条路：

- 一次故障比本地代码任务更慢、更嘈杂，信号和噪声混在一起。
- 难以在可重复的前提下模拟和评估——本地能跑的用例，生产里复现不了。
- 证据散落在日志、指标、追踪、runbook、Slack 线程等多个系统。
- 判断依赖基础设施上下文（Kubernetes、AWS、数据库等），模型需要在线理解这些系统怎么运转。

OpenSRE 的解法是构建一个开放环境，让 AI SRE Agent 在真实基础设施上训练和评估，核心定位是"用于 Agent 基础设施事故响应的开放强化学习环境，包含端到端测试和合成事故模拟"。

## 二、系统地图：一次告警怎么流过 OpenSRE

先看整体，再拆细节。

```text
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

一次调查分五步，OpenSRE 会自动完成：

1. **抓取**告警上下文，以及关联的日志、指标、追踪。
2. **推理**跨连接系统之后，识别异常在哪。
3. **生成**带证据的结构化调查报告，指出最可能的根因。
4. **建议**下一步行动，可选执行修复操作。
5. **推送**摘要到 Slack 或 PagerDuty。

这套流程里有一个值得注意的边界：各数据源是作为独立集成接入的，Agent 调查时把它们当作多个证据来源，而不是嵌套在一个大系统里。

## 三、核心机制：四条主线拆开看

把"事件调查"拆开，OpenSRE 有三个相互独立的能力，加上一个跨层约束：

| 能力 | 职责 | 边界 |
|------|------|------|
| 结构化事故调查 | 跨所有信号做关联根因分析 | 只分析，不执行修复 |
| Runbook 感知推理 | 读取 runbook 并自动套用 | 依赖团队是否有可读的 runbook |
| 预测性故障检测 | 在告警之前捕获新兴问题 | 属于增值能力，不替代告警 |
| 证据支持根因 | 每个结论都链接到背后数据 | 结论可追溯，可被人工复核 |

跨层约束是"全 LLM 灵活性"：支持 Anthropic、OpenAI、Ollama、Gemini、OpenRouter、NVIDIA NIM、Bedrock。这意味着同一个 Agent 可以换模型跑，也可以使用本地模型。

## 四、一次真实任务怎么流过系统

用一个测试告警看整条链路。假设你的 Kubernetes 集群里，一个 Datadog 告警被触发：

```bash
opensre investigate -i tests/e2e/kubernetes/fixtures/datadog_k8s_alert.json
```

触发后，Agent 先抓取这个告警的上下文——关联的日志、指标和追踪数据从已配置的 Datadog、Grafana（Loki/Mimir/Tempo）等集成里取回。然后它跨这些系统做推理，判断异常是来自应用本身的代码问题，还是来自底层的资源、数据库或网络。中途如果存在 runbook，Agent 会读取并尝试套用其中的处置步骤。最终生成一份 RCA 报告，每个"最可能的根因"都带对应的证据链接，再推送到 Slack 或 PagerDuty 供人审阅。

这一步值得关注的是：报告里的结论不是模型空口说的，而是可以回溯到具体数据的。人工复核"它为什么这么判断"有据可依。

## 五、60+ 工具集成：覆盖了哪些环节

集成按类别展开，覆盖事故调查所需的几乎全部数据源：

| 类别 | 集成 |
|------|------|
| AI / LLM | Anthropic · OpenAI · Ollama · Google Gemini · OpenRouter · NVIDIA NIM · Bedrock |
| 可观测性 | Grafana (Loki/Mimir/Tempo) · Datadog · Honeycomb · Coralogix · CloudWatch · Sentry · Elasticsearch · Better Stack |
| 基础设施 | Kubernetes · AWS (S3/Lambda/EKS/EC2) · GCP · Azure |
| 数据库 | MongoDB · ClickHouse · PostgreSQL · MySQL · MariaDB · MongoDB Atlas · Azure SQL |
| 数据平台 | Apache Airflow · Apache Kafka · Apache Spark · Prefect · RabbitMQ |
| Dev 工具 | GitHub · GitHub MCP · Bitbucket · GitLab |
| 事件管理 | PagerDuty · Opsgenie · Jira |
| 通信 | Slack · Google Docs |

还支持 MCP 和 OpenClaw 协议，接入未列出的工具时可以作为补充通道。

## 六、测试框架：怎么评估一个 AI SRE

OpenSRE 内置两类测试，对应评估的两条主线。

**合成 RCA 测试（Synthetic RCA）**：在 `tests/synthetic/` 下检查根因准确性、所需证据和对抗性红鲱鱼。它测的是"面对一个受控故障，Agent 能不能找到设定好的根因，是否会被故意放进去的干扰信息带偏"。场景示例是 RDS + PostgreSQL。

**端到端测试（E2E）**：跨云支持场景的完整测试，覆盖 Kubernetes、EC2、CloudWatch、Lambda、ECS Fargate、Flink。它测的是"Agent 在接近真实的环境里能不能走完整条调查链路"。

两条主线的边界靠目录结构维持，E2E 与合成、本地与云的分界始终清晰。

需要说清楚的是：合成测试是受控环境，故障时长和影响范围都是预设的，通过它不代表生产可用；但它作为"最低质量标准"有意义——不通过合成测试一定有问题。

## 七、技术栈与部署

- **语言**：Python 3.13
- **运行时**：LangGraph
- **数据库**：PostgreSQL + Redis
- **部署**：Railway / Docker
- **Dev Container**：VS Code devcontainer 开箱即用

安装：

```bash
# Linux/macOS
curl -fsSL https://raw.githubusercontent.com/Tracer-Cloud/opensre/main/install.sh | bash

# Homebrew
brew install Tracer-Cloud/opensre/opensre

# Windows
irm https://raw.githubusercontent.com/Tracer-Cloud/opensre/main/install.ps1 | iex
```

开发模式：

```bash
git clone https://github.com/Tracer-Cloud/opensre
cd opensre
make install

# 配置 LLM provider 和集成（Grafana/Datadog/Slack/AWS/GitHub/Sentry 等）
opensre onboard

# 调查一个测试告警
opensre investigate -i tests/e2e/kubernetes/fixtures/datadog_k8s_alert.json
```

Railway 部署前，需要先在 Railway 项目中配置 Postgres 和 Redis，再设置 `DATABASE_URI` 与 `REDIS_URI`：

```bash
opensre deploy railway --project <project> --service <service> --yes
```

## 八、与传统 SRE 工具的对比

| 对比 | 传统 SRE | OpenSRE |
|------|---------|---------|
| 事故响应 | 人工排查 + 经验 | AI Agent 自动调查 |
| 信息整合 | 需要手动切换多个工具 | 自动关联 60+ 工具的数据 |
| RCA 报告 | 人工撰写 | 自动生成带证据的报告 |
| 训练环境 | 无 | 合成 + E2E 场景，规模化 |
| LLM 支持 | 不支持 AI | 支持多种 LLM |

这里要区分两类工具的关系：OpenSRE 不是告警管理工具，而是事故调查工具。PagerDuty / Opsgenie 负责告警路由、升级、值班表；OpenSRE 处理的是一个告警触发后"查清根因、出报告"这一段。两者互补，OpenSRE 可以把报告推送到 PagerDuty 作为注释，或创建一个跟进的 Jira 工单。

## 九、Roadmap 上的重要集成

| 类别 | 即将支持 |
|------|---------|
| 可观测性 | Splunk, New Relic, Victoria Logs |
| 基础设施 | Helm, ArgoCD |
| 数据库 | RDS, Snowflake |
| 事件管理 | Trello, ServiceNow, incident.io, Alertmanager, Linear |
| 通信 | Discord, Notion, Teams, WhatsApp, Confluence |
| Agent 部署 | Railway |

## 十、采用建议：谁该先上，谁可以等等

- **大厂 SRE 团队**：自动化事故调查，减少 MTTR，回报最直接。
- **创业公司**：一个人 on-call 时，AI 辅助分析能分担判断压力。
- **AI 研究**：用它的测试框架训练、评估 AI SRE Agent，是最有建设性的用途之一。
- **平台工程**：可以拿它当构建内部 AI SRE 能力的基座。

两类团队可以先等等：告警系统本身还很乱、runbook 没有沉淀的团队，直接上 Agent 收益有限；以及对自动排查可信度要求极高、必须人工逐条复核的受监管场景，更适合先只把它当辅助分析工具，不接自动流程。

落地前有几点要明确：

- 默认只调查、不执行修复；输出 RCA 报告需人工审核后才有下一步。若启用"可选执行修复操作"，务必先在测试环境充分验证，并把 Agent 权限限制在只读范围。
- 核心推理依赖 LLM。若 LLM 不可用，Agent 无法完成调查，建议配置至少一个备用 provider（例如主用 Anthropic，备用 OpenAI 或本地 Ollama），并设置 fallback 顺序。
- 对中文告警和日志不设语言限制——它抓取的是工具 API 返回的结构化数据，由 LLM 理解后生成报告。但合成测试目前以英文场景为主，中文场景需要自己写测试。
- 混合云（如 AWS + 自建机房）可以同时接入，集成是模块化的；跨云的网络连通性和权限配置需提前处理。

## 常见问题 FAQ

**Q1: OpenSRE 能直接在生产环境跑吗？会不会误操作？**

默认只做"调查"和"报告"，不执行修复。输出是结构化 RCA 报告，需人工审核。如果启用"可选执行修复操作"，务必在测试环境充分验证，并限制权限在只读范围。

**Q2: 如果 LLM 宕机或超时怎么办？**

核心推理依赖 LLM，不可用则调查无法完成。建议配至少一个备用 provider 并设 fallback 顺序。

**Q3: 合成 RCA 测试能替代真实事故评估吗？**

不能。合成测试是受控环境，真实事故更复杂、涉及更多系统和人员。把它理解为最低质量标准：通过不代表生产可用，不通过一定有问题。

**Q4: 支持中文告警和日志吗？**

不设语言限制——抓取的是结构数据，由 LLM 理解。只要 LLM 支持中文即可。合成测试目前以英文为主，中文场景需自建测试。

**Q5: 混合云能同时接入吗？**

可以。集成模块化，可同时启用 AWS CloudWatch 和自建机房 Prometheus/Grafana；注意提前处理跨云网络连通性和权限配置。

**Q6: OpenSRE 和 PagerDuty / Opsgenie 是什么关系？**

OpenSRE 是事故调查工具，不是告警管理工具。PagerDuty/Opsgenie 管告警路由、升级和值班；OpenSRE 处理告警后的调查与报告。两者互补。

## 相关链接

- GitHub：https://github.com/Tracer-Cloud/opensre（3.3k stars）
- 官网：https://www.opensre.com
- Discord：https://discord.gg/7NTpevXf7w

🦞 每日 08:00 自动更新