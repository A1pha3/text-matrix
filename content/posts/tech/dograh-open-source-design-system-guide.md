---
title: "Dograh：开源语音 Agent 平台，让每个人都能搭建电话 AI 助手"
date: "2026-05-17T20:10:00+08:00"
slug: "dograh-open-source-voice-agent-platform"
description: "深度解析开源语音 Agent 平台 Dograh 的核心架构与工作原理，涵盖 Workflow 图引擎、实时通话流水线、节点类型与边界触发器，并提供一键本地部署与自定义扩展的完整指南。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Voice AI", "语音助手", "开源", "FastAPI", "WebRTC"]
---

> **目标读者**：想搭建电话 AI 助手或外呼机器人的开发者，或对语音 AI 平台架构感兴趣的技术人员
> **核心问题**：Dograh 是怎么做到「2 分钟跑起来」的？它的 Workflow 图引擎和实时通话流水线是怎么协同工作的？如何在自己的基础设施上部署和扩展它？
> **难度**：⭐⭐（核心概念 · 系统讲解）
> **预计阅读时间**：20–30 分钟
> **前置知识**：了解 LLM 基本概念，知道语音识别（STT）和语音合成（TTS）是什么

---

## 1. 概述：Dograh 是什么

**Dograh** 是一个开源的语音 Agent 平台，可以理解为 Vapi / Retell 的开源替代品。它的核心能力是：让你用拖拽方式构建对话流，连接一条电话线路，然后拥有一个可以接听或拨打电话的 AI 语音助手。

与闭源 SaaS 相比，Dograh 的三个核心差异在于：

- **100% 开源**：所有代码透明，没有供应商锁定
- **可自托管**：一行 Docker 命令在本地跑起来，不依赖任何云服务
- **完全自主**：LLM、STT（语音转文本）、TTS（文本转语音）全部可以换成自己的供应商，或者直接用 Dograh 内置的免费堆栈，无需任何 API Key 就能测试

截至本文写作时，Dograh 在 GitHub 上已有约 1,420 颗星、333 个 Fork，社区活跃，文档完整。由 YC 校友和退出创始人创办，核心团队承诺将语音 AI 保持开源。

**官网**：[https://app.dograh.com](https://app.dograh.com)
**文档**：[https://docs.dograh.com](https://docs.dograh.com)
**GitHub**：[https://github.com/dograh-hq/dograh](https://github.com/dograh-hq/dograh)

---

## 2. 核心架构：一次通话背后发生了什么

理解 Dograh 的最好方式是从一次通话的生命周期开始。以下是 Dograh 官方文档中的核心流程图：

```mermaid
sequenceDiagram
    participant U as Dashboard / 你的 App
    participant API as Dograh API
    participant STT as 语音识别 (STT)
    participant LLM as LLM 提供商
    participant TTS as 语音合成 (TTS)
    participant Tel as 电话供应商
    participant Cal as 呼叫方

    U->>API: 触发通话（仪表盘或 API）
    API->>Tel: 发起外呼
    Tel->>Cal: 电话响铃
    Cal-->>Tel: 接听
    Tel-->>API: 原始音频流
    loop 对话循环
        API->>STT: 呼叫方音频
        STT-->>API: 转录文本
        API->>LLM: 转录文本 + Agent 提示词 + 上下文
        LLM-->>API: Agent 回复文本
        API->>TTS: 回复文本
        TTS-->>API: 合成音频
        API->>Tel: 音频流
        Tel->>Cal: Agent 说话
    end
    API->>API: 提取上下文、执行 Webhook
    API-->>U: Run 记录（转录文本、录音、采集数据）
```

整个流程分为以下几个关键模块：

### 2.1 电话供应商（Telephony）

Dograh 通过标准的电话供应商（Twilio、Vonage、Telnyx、Vobiz、Cloudonix 等）接入公共电话网（PSTN）。这意味着你可以自带电话号码，或者使用任何已接入的供应商。呼叫接入后，音频流以 WebRTC 方式在供应商和 Dograh 之间实时传输。

### 2.2 语音识别（STT）

呼叫方的语音被实时转录为文本。Dograh 将音频流发送给配置的 STT 提供商，拿回转录结果后驱动后续的 LLM 对话和最终的 Run 记录存档。

### 2.3 对话逻辑（Workflows）

Workflow 是 Dograh 的核心概念——在用户界面里它叫「Agent」，在 API 里它叫「Workflow」。本质上，它是一个**有向图**：节点（Nodes）定义了对话的每一步，边界（Edges）定义了条件触发器。

### 2.4 LLM 决策

LLM 接收当前节点的提示词和完整对话历史，决定 Agent 的下一句回复，同时评估边界条件——是否应该跳转到下一个节点。

### 2.5 语音合成（TTS）

LLM 输出的文本由 TTS 提供商转换为自然语音，传回给呼叫方。整个过程需要在数百毫秒内完成，否则对话会明显卡顿。

---

## 3. Workflow 图引擎详解

### 3.1 节点类型

Dograh 的 Workflow 图由以下几种节点组成：

| 节点类型 | 作用 |
|---|---|
| `startCall` | 电话入口节点，定义 Agent 接通后说的第一句话 |
| `agentNode` | LLM 驱动的对话步骤，核心构建块 |
| `globalNode` | 全局指令节点，定义 Agent 的语气、语言、异常处理策略 |
| `endCall` | 结束通话 |
| `trigger` | API 触发入口（非电话场景） |
| `webhook` | 触发 HTTP 请求，用于 CRM 更新、通知等 |
| `qa` | 对已完成通话做质量分析 |

### 3.2 边界与条件转移

节点之间通过**边界（Edges）**连接。每条边界有一个自然语言条件描述，LLM 根据对话上下文判断该条件是否满足，满足则跳转到目标节点。

边界还可以带一个 `transition_speech`（过渡语音）——在跳转到下一个节点之前，Agent 会说一句话再过渡。

### 3.3 版本管理

每次更新 Workflow 定义，Dograh 会保存一个新版本，同时保留历史记录。当前版本始终是实际运行的，旧版本用于审计和回滚。

---

## 4. 快速开始：60 秒跑起来

Dograh 最吸引人的特性之一就是**零配置启动**。一行命令，不需要任何 API Key，Dograh 会自动生成内置的 LLM/STT/TTS 堆栈。

### 4.1 一键本地启动

```bash
curl -o docker-compose.yaml https://raw.githubusercontent.com/dograh-hq/dograh/main/docker-compose.yaml && REGISTRY=ghcr.io/dograh-hq ENABLE_TELEMETRY=true docker compose up --pull always
```

> **注意**：首次启动需要下载所有 Docker 镜像，大约需要 2–3 分钟。启动后访问 http://localhost:3010 即可进入管理界面。

### 4.2 创建第一个语音 Agent

1. 打开 [http://localhost:3010](http://localhost:3010)
2. 选择 **Inbound**（呼入）或 **Outbound**（外呼）
3. 给 Bot 起个名字（比如「线索筛选」），用 5–10 个词描述使用场景（例如「保险表单提交意向筛查」）
4. 点击 **Web Call**，开始和 Bot 对话

**无需 API Key**：Dograh 开箱即用地提供了内置的 LLM/STT/TTS 堆栈。如果需要使用自己的供应商（OpenAI、ElevenLabs、Deepgram 等），随时可以在配置页面替换。

### 4.3 系统要求

| 项目 | 最低要求 | 推荐配置 |
|---|---|---|
| 内存 | 8 GB（Docker 占用 4 GB） | 16 GB |
| 存储 | 10 GB 可用空间 | 20 GB |
| CPU | 2 核（x86_64 或 ARM64） | 4 核 |
| 操作系统 | macOS 10.15+、Windows 10/11 (WSL2)、Linux | — |

需要开放的端口：`3010`（Web UI）、`8000`（API）、`5432`（PostgreSQL）、`6379`（Redis）、`9000` / `9001`（MinIO）。

---

## 5. 核心功能一览

### 5.1 内置电话能力

Dograh 已集成主流电话供应商（Twilio、Vonage、Telnyx、Vobiz、Cloudonix），支持：

- **呼入**：接听外部来电，触发 Workflow
- **外呼**：批量向外拨打电话，连接 CRM 数据源
- **呼叫转移**：对话中可将呼叫转接到人工客服

### 5.2 自带 LLM/STT/TTS 堆栈

不想折腾 API Key？Dograh 默认提供：

- **LLM**：内置模型（可配置为 OpenAI/Anthropic 等）
- **STT**：Deepgram / 其他主流供应商
- **TTS**：ElevenLabs / 其他主流供应商

随时在配置页面切换为自己的供应商。

### 5.3 测试模式（Test Mode）

在发布之前，可以在一个隔离环境中端到端测试 Agent，所有通话记录和数据不会影响生产环境。

### 5.4 内置 QA 节点

`qa` 节点可对已完成的通话做自动质量分析，评估提示词的有效性，帮助优化对话设计。

### 5.5 Webhook 集成

在 Workflow 的任意节点挂载 Webhook，可对接 CRM 系统、发送通知、更新数据库，实现业务闭环。

---

## 6. Dograh vs Vapi vs Retell

| | **Dograh** | **Vapi** | **Retell** |
|---|---|---|---|
| **许可证** | BSD 2-Clause（开源） | 专有 | 专有 |
| **自托管** | ✅ 一行 Docker 命令 | ❌ 仅 SaaS | ❌ 仅 SaaS |
| **定价** | 免费（自托管）· 按用量（云版） | 按分钟计费 SaaS | 按分钟计费 SaaS |
| **自带 LLM/STT/TTS** | ✅ 可用内置堆栈 | 在其集成范围内可配置 | 在其集成范围内可配置 |
| **源码级定制** | ✅ 全部开放 | ❌ 闭源 | ❌ 闭源 |
| **数据主权** | 自己的基础设施 | 对方云 | 对方云 |
| **供应商锁定** | 无 | 完全锁定 | 完全锁定 |

---

## 7. 部署方式

### 7.1 本地开发

Docker 一键启动，适合本地开发调试和快速验证创意。

### 7.2 远程服务器部署

文档提供了完整的远程服务器部署指南，包括 HTTPS 反向代理（Nginx/Caddy）、域名绑定、SSL 证书配置等步骤。参见 [Docker 部署文档](https://docs.dograh.com/deployment/docker)。

### 7.3 云版本

不想自己运维？官方提供托管云版本：[https://app.dograh.com](https://app.dograh.com)，按实际用量计费。

---

## 8. 技术栈与扩展开发

Dograh 的技术栈：

- **后端**：Python + FastAPI
- **前端**：Next.js（管理界面）
- **数据库**：PostgreSQL + Redis
- **对象存储**：MinIO（S3 兼容）
- **实时通信**：WebRTC + Pipecat（语音框架）
- **容器化**：Docker + Docker Compose

如果你想深度定制，比如开发自定义节点类型或集成私有 LLM，Python 为主体的架构让这类扩展相对直接。文档中的「Workflow Definition Schema」提供了完整的 API 字段参考。

---

## 9. 下一步

| 推荐内容 | 难度 | 说明 |
|---|---|---|
| [Dograh 工作原理（官方文档）](https://docs.dograh.com/core-concepts/how-dograh-works) | ⭐ | 官方核心概念图解 |
| [Workflows & Agents 详解](https://docs.dograh.com/core-concepts/workflows-and-agents) | ⭐⭐ | 节点类型、边界与版本管理 |
| [Calls & Runs](https://docs.dograh.com/core-concepts/calls-and-runs) | ⭐⭐ | 通话生命周期与 Run 记录 |
| [Docker 部署指南](https://docs.dograh.com/deployment/docker) | ⭐⭐ | 远程服务器完整部署流程 |
| [Pipecat 语音框架](https://github.com/pipecat-ai/pipecat) | ⭐⭐⭐ | Dograh 底层实时语音处理库 |

---

## 10. 总结

Dograh 做的事是把语音 AI 能力从「需要深度工程积累」变成「一个 Docker 命令就能跑起来」的东西。它的 Workflow 图模型让对话逻辑变得直观可视，内置的全栈（LLM/STT/TTS）让测试完全零成本，而开源属性则给了团队完全的数据主权和定制自由。

如果你正在评估语音 AI 平台，或者想快速搭一个外呼 / 客服机器人原型，Dograh 值得一试。

---

> **版权声明**：本文内容基于 Dograh 开源项目（BSD 2-Clause License）官方文档与 GitHub 仓库信息整理，保留了原始技术术语与核心描述。
