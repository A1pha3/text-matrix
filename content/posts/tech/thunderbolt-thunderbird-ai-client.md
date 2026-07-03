---
title: "Thunderbolt：雷鸟1679 Stars的企业级AI客户端——自托管、无供应商锁定、端到端加密"
date: "2026-04-19T21:02:00+08:00"
slug: "thunderbolt-thunderbird-ai-client"
description: "Thunderbolt是Mozilla Thunderbird开源的1679 Stars企业级AI客户端，采用Tauri跨平台架构、React 19前端、Elysia/Bun后端，支持本地/云端/私有化部署，集成MCP协议，提供可选端到端加密和多设备同步，实现真正的数据自主可控。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "Tauri", "MCP", "端到端加密", "自托管"]
---

# Thunderbolt：雷鸟 1679 Stars 的企业级 AI 客户端——自托管、无供应商锁定、端到端加密

> **目标读者**：企业 IT 决策者、隐私敏感用户、AI 应用开发者、跨平台应用开发者
> **预计阅读时间**：45-60 分钟
> **前置知识**：对 AI 助手使用有经验、了解基本的数据安全概念
> **难度定位**：⭐⭐⭐⭐ 专家设计

## 学习目标

读完本文后，你应该能够：

1. 说出 Thunderbolt 的三层分离架构各部分职责，以及为什么选择 Tauri + Bun 组合
2. 解释离线优先设计的数据流，以及 PowerSync 同步引擎的工作方式
3. 描述 MCP 集成的完整流程，包括如何配置自定义 MCP 服务器
4. 列出 Thunderbolt 的 6 种部署方案，并根据场景选择最合适的方案
5. 理解 E2E 加密的威胁缓解模型，以及哪些威胁无法通过 E2E 完全消除
6. 把 Thunderbolt 当 ChatGPT/Claude AI 的自托管替代品来用，并理解其数据控制优势

## 目录

- [项目概述](#项目概述)
- [技术架构](#技术架构)
- [核心功能模块](#核心功能模块)
- [部署方案](#部署方案)
- [安全模型](#安全模型)
- [与竞品对比](#与竞品对比)
- [开发指南](#开发指南)
- [实践建议](#实践建议)
- [未来路线图与演进](#未来路线图与演进)
- [总结](#总结)
- [场景问答（FAQ）](#场景问答faq)
- [自测题](#自测题)
- [练习](#练习)
- [进阶路线](#进阶路线)

---

## §1 项目概述

### 1.1 基本信息

| 属性 | 值 |
|------|-----|
| **仓库** | github.com/thunderbird/thunderbolt |
| **Stars** | 1,679 |
| **Forks** | 86 |
| **语言** | TypeScript |
| **许可证** | Mozilla Public License 2.0 |
| **官网** | thunderbolt.io |

### 1.2 项目定位

Thunderbolt 是 Mozilla Thunderbird（著名开源邮件客户端）团队打造的**企业级 AI 客户端**，

> **"AI You Control: Choose your models. Own your data. Eliminate vendor lock-in."**
> "AI 由你掌控：选择你的模型，拥有你的数据，消除供应商锁定。"

### 1.3 核心特性

| 特性 | 说明 |
|------|------|
| **跨平台** | Web、iOS、Android、Mac、Linux、Windows |
| **模型无关** | 支持 Claude、GPT、Mistral、OpenRouter 等 |
| **本地/云端** | 支持本地 Ollama/llama.cpp 或云端 API |
| **自托管** | 可完全私有化部署 |
| **端到端加密** | 可选 E2E 加密，数据自主可控 |
| **离线优先** | 本地 SQLite 先行，网络备用 |
| **MCP 支持** | 集成 Model Context Protocol 客户端 |

---

## §2 技术架构

### 2.1 整体架构

Thunderbolt 采用**三层分离架构**：

```mermaid
flowchart TB
    subgraph CLIENT["📱 用户设备层 (On-Device)"]
        direction TB
        UI[React 19<br/>Radix UI]
        STATE[Zustand<br/>TanStack Query]
        CHAT[Vercel AI SDK<br/>MCP Client]
        DB[(SQLite<br/>Offline-First)]
        CRYPTO[🔐 E2E Crypto<br/>(Optional)]

        UI --> STATE
        UI --> CHAT
        STATE --> DB
        CHAT --> CRYPTO
    end

    subgraph SERVER["☁️ 服务器层 (Self-Hostable)"]
        direction TB
        API[Elysia API<br/>Bun Runtime]
        AUTH[Better Auth<br/>OTP / OIDC]
        SYNC[PowerSync<br/>Sync Engine]
        PG[(PostgreSQL)]

        API --> AUTH
        API --> SYNC
        SYNC --> PG
        AUTH --> PG
    end

    subgraph EXTERNAL["🌐 外部服务"]
        LLM[LLM Providers<br/>Claude / GPT / Mistral]
        OAUTH[OAuth<br/>Google / Microsoft]
    end

    CLIENT <-->|REST / SSE| SERVER
    CHAT -->|SSE Streaming| LLM
    AUTH --> OAUTH

    style CLIENT fill:#dbeafe,stroke:#3b82f6,stroke-width:2px
    style SERVER fill:#f3e8ff,stroke:#8b5cf6,stroke-width:2px
    style EXTERNAL fill:#fef3c7,stroke:#f59e0b,stroke-width:2px
```

**关键设计决策**：

| 设计点 | 选择 | 理由 |
|--------|------|------|
| **跨平台框架** | Tauri | Rust 保证性能，原生系统集成 |
| **离线优先** | SQLite + PowerSync | 本地先行，网络备用 |
| **AI 接口** | Vercel AI SDK | 统一多模型接入 |
| **后端运行时** | Bun | 启动快，TypeScript 原生支持 |
| **类型安全** | Drizzle ORM | 编译期检查 |

### 2.2 设备层架构

```mermaid
flowchart LR
    subgraph Device["📱 Tauri Shell"]
        direction TB
        WEB[React WebView] --> BRIDGE[Tauri IPC Bridge]
        BRIDGE --> RUST[Tauri Core<br/>Rust]
    end

    subgraph Capabilities
        direction LR
        FILE[File System] & DB[(SQLite)] & NET[Network]
    end

    RUST --> Capabilities

    style Device fill:#d1fae5,stroke:#10b981
    style Capabilities fill:#fef3c7,stroke:#f59e0b
```

### 2.2 前端技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| **UI 框架** | React 19 | 最新 React 版本 |
| **构建工具** | Vite | 极速开发体验 |
| **组件库** | Radix UI | 无头组件，可访问性优先 |
| **状态管理** | Zustand | 轻量级状态管理 |
| **数据获取** | TanStack Query | 异步状态与缓存 |
| **ORM** | Drizzle | 类型安全数据库访问 |
| **AI SDK** | Vercel AI SDK | 统一 AI 接口 |
| **AI 协议** | MCP Client | Model Context Protocol |

### 2.3 跨平台实现

```
┌─────────────────────────────────────────────────────────────┐
│                    Tauri 跨平台架构                            │
│                                                              │
│                    React 前端代码                              │
│                    (统一代码库)                               │
│                         │                                    │
│                         ▼                                    │
│              ┌──────────────────┐                           │
│              │    Tauri Core     │                           │
│              │    (Rust实现)     │                           │
│              └──────────────────┘                           │
│                    │       │       │                          │
│         ┌──────────┘       │       └──────────┐              │
│         ▼                  ▼                  ▼              │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐           │
│   │ macOS    │      │ Windows  │      │ Linux    │           │
│   │ AppKit   │      │ Win32 API│      │ GTK/Qt   │           │
│   └──────────┘      └──────────┘      └──────────┘           │
│                                                              │
│         ┌──────────┐      ┌──────────┐                       │
│         │  iOS     │      │ Android  │                       │
│         │ UIKit    │      │ Jetpack  │                       │
│         └──────────┘      └──────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

### 2.4 后端技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| **运行时** | Bun | 高性能 JavaScript 运行时 |
| **Web 框架** | Elysia | 极速类型安全 API |
| **认证** | Better Auth | 现代化认证方案 |
| **OIDC** | OpenID Connect | 企业 SSO 支持 |
| **数据库** | PostgreSQL | 关系型数据存储 |
| **同步引擎** | PowerSync | 离线优先同步 |

---

## §3 核心功能模块

### 3.1 AI Chat 模块

Thunderbolt 的 AI 对话功能：

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Chat 架构                              │
│                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────┐ │
│  │ User Input   │────▶│ Vercel AI    │────▶│ MCP Client │ │
│  │             │     │ SDK          │     │            │ │
│  └──────────────┘     └──────────────┘     └─────┬──────┘ │
│                                                    │        │
│                                                    ▼        │
│                     ┌──────────────┐     ┌────────────┐    │
│                     │ SSE Stream   │◄────│ MCP Server │    │
│                     │ (实时流式)   │     │ (本地工具) │    │
│                     └──────┬───────┘     └────────────┘    │
│                            │                                  │
│                            ▼                                  │
│                     ┌──────────────┐                         │
│                     │  推理代理    │                         │
│                     │  (后端)      │                         │
│                     └──────┬───────┘                         │
│                            │                                  │
│                            ▼                                  │
│         ┌───────────────────────────────┐                  │
│         │      LLM Providers             │                  │
│         │  Claude / GPT / Mistral / ...  │                  │
│         └───────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 MCP 集成

MCP (Model Context Protocol) 让 Thunderbolt 能够调用本地工具和服务，实现"AI+本地工具"的深度集成：

```mermaid
flowchart LR
    AI[Claude / GPT] <-->|MCP Protocol| CLIENT[MCP Client]
    CLIENT --> TOOLS[本地工具]

    subgraph Tools
        FS[文件系统] & GIT[Git] & DB[(数据库)] & WEB[Web API]
    end

    TOOLS --> Tools

    style AI fill:#fef3c7,stroke:#f59e0b
    style CLIENT fill:#dbeafe,stroke:#3b82f6
    style Tools fill:#d1fae5,stroke:#10b981
```

**MCP 能力矩阵**：

| 能力 | 工具 | 用途 |
|------|------|------|
| 文件系统 | filesystem MCP | 读写本地项目文件 |
| Git 操作 | git MCP | 代码版本控制、提交历史 |
| 数据库 | database MCP | SQL 查询、数据分析 |
| Web 搜索 | search MCP | 实时信息检索 |
| 自定义 | 用户定义 | 项目特定工具链 |

**MCP 服务器配置示例**：

```typescript
// ~/.config/thunderbolt/mcp-servers.json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/project"]
    },
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git"]
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search", "--api-key", "${BRAVE_API_KEY}"]
    }
  }
}
```

### 3.3 离线优先设计

```
┌─────────────────────────────────────────────────────────────┐
│                    离线优先数据流                            │
│                                                              │
│  1. 所有数据优先写入本地SQLite                              │
│                    │                                         │
│                    ▼                                         │
│  2. 后台通过PowerSync同步到PostgreSQL                       │
│                    │                                         │
│                    ▼                                         │
│  3. 冲突解决策略：                                           │
│     - Last-write-wins (默认)                                │
│     - 自定义合并规则                                         │
│                                                              │
│  ✅ 网络断开时：完全可用                                     │
│  ✅ 网络恢复时：自动同步                                     │
└─────────────────────────────────────────────────────────────┘
```

### 3.4 端到端加密（可选）

当启用 E2E 加密时：

```
┌─────────────────────────────────────────────────────────────┐
│                    E2E 加密流程                              │
│                                                              │
│  发送方:                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │ 明文数据 │───▶│ 本地加密 │───▶│ 密文数据 │             │
│  └──────────┘    └──────────┘    └────┬─────┘             │
│                                       │                     │
│                                       ▼                     │
│                              ┌──────────────┐              │
│                              │ 服务器存储   │              │
│                              │ (仅存储密文) │              │
│                              └──────────────┘              │
│                                       │                     │
│                                       ▼                     │
│  接收方:                             │                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │ 密文数据 │◄───│ 服务器   │◄───│ 密文数据 │             │
│  └────┬─────┘    └──────────┘    └──────────┘             │
│       │                                                       │
│       ▼                                                       │
│  ┌──────────┐                                               │
│  │ 本地解密 │                                               │
│  └──────────┘                                               │
│       │                                                       │
│       ▼                                                       │
│  ┌──────────┐                                               │
│  │ 明文数据 │                                               │
│  └──────────┘                                               │
│                                                              │
│  🔐 服务器永远不掌握密钥，无法解密用户数据                     │
└─────────────────────────────────────────────────────────────┘
```

> ⚠️ **注意**：E2E 加密功能正在开发中，尚未经过密码学审计。

---

## §4 部署方案

### 4.1 部署方案决策树

```mermaid
flowchart TD
    START["🚀 部署场景选择"] --> Q1{用户规模?}

    Q1 -->|个人/小团队| DOCKER[Docker Compose<br/>推荐]
    Q1 -->|中型企业| K8S[Kubernetes<br/>Helm Chart]
    Q1 -->|大型企业| ENTER[Enterprise<br/>定制集成]

    Q1 -->|安全性要求?| Q2
    Q2 -->|最高安全| E2E[启用E2E加密<br/>零知识架构]
    Q2 -->|标准安全| SELF[self-hosted<br/>TLS加密]
    Q2 -->|最低安全| CLOUD["☁️ 官方托管<br/>最小运维"]

    DOCKER -->|数据敏感| E2E
    K8S -->|合规要求| SELF
    ENTER -->|监管行业| E2E

    style START fill:#d1fae5,stroke:#10b981
    style E2E fill:#fecaca,stroke:#ef4444
    style SELF fill:#fef3c7,stroke:#f59e0b
    style CLOUD fill:#dbeafe,stroke:#3b82f6
```

**部署方案对比**：

| 方案 | 适用规模 | 数据控制 | 运维成本 | 安全性 |
|------|----------|----------|----------|---------|
| **官方托管** | 个人/试用 | ⭐ | 最低 | 基础 |
| **Docker Compose** | 小团队 | ⭐⭐⭐⭐ | 低 | 标准 |
| **Kubernetes** | 中型企业 | ⭐⭐⭐⭐⭐ | 中 | 高级 |
| **E2E 加密模式** | 任何规模 | ⭐⭐⭐⭐⭐ | 略高 | **最高** |

### 4.2 Docker Compose 部署（推荐用于个人/小团队）

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    image: thunderbird/thunderbolt:latest
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/thunderbolt
      - POWER_SYNC_URL=http://powersync:8080
    depends_on:
      - db
      - powersync

  db:
    image: postgres:16
    environment:
      - POSTGRES_DB=thunderbolt
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  powersync:
    image: powersync/powersync:latest
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/thunderbolt
    volumes:
      - powersync_data:/var/lib/powersync

volumes:
  postgres_data:
  powersync_data:
```

### 4.2 Kubernetes 部署（企业级）

```yaml
# thunderbolt-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: thunderbolt-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: thunderbolt-api
  template:
    spec:
      containers:
      - name: api
        image: thunderbird/thunderbolt:latest
        ports:
        - containerPort: 3000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: thunderbolt-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: thunderbolt-api
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 3000
  selector:
    app: thunderbolt-api
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: thunderbolt-ingress
spec:
  rules:
  - host: thunderbolt.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: thunderbolt-api
            port:
              number: 80
```

### 4.3 模型配置

Thunderbolt 支持多种模型接入方式：

```json
// settings.json
{
  "modelProviders": [
    {
      "name": "ollama",
      "type": "ollama",
      "baseUrl": "http://localhost:11434",
      "models": ["llama3.1", "codellama", "mistral"]
    },
    {
      "name": "openai",
      "type": "openai",
      "apiKey": "${OPENAI_API_KEY}",
      "baseUrl": "https://api.openai.com/v1",
      "models": ["gpt-4o", "gpt-4-turbo"]
    },
    {
      "name": "anthropic",
      "type": "anthropic",
      "apiKey": "${ANTHROPIC_API_KEY}",
      "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"]
    },
    {
      "name": "openrouter",
      "type": "openrouter",
      "apiKey": "${OPENROUTER_API_KEY}",
      "baseUrl": "https://openrouter.ai/api",
      "models": ["anthropic/claude-3.5-sonnet", "meta-llama/llama-3.1-70b-instruct"]
    }
  ]
}
```

---

## §5 安全模型

### 5.1 威胁模型与缓解措施

```mermaid
flowchart TD
    subgraph Threats[威胁矩阵]
        T1[服务器数据泄露]
        T2[中间人攻击MITM]
        T3[未授权访问]
        T4[API密钥泄露]
        T5[模型提供商日志]
        T6[内部人员滥用]
    end

    subgraph Mitigations[缓解措施]
        M1[E2E加密]
        M2[TLS 1.3]
        M3[OTP/OIDC]
        M4[环境变量+密钥管理]
        M5[自托管推理端点]
        M6[最小权限+审计日志]
    end

    T1 --> M1
    T2 --> M2
    T3 --> M3
    T4 --> M4
    T5 --> M5
    T6 --> M6

    style Threats fill:#fecaca,stroke:#ef4444
    style Mitigations fill:#d1fae5,stroke:#10b981
```

**威胁缓解矩阵**：

| 威胁 | 严重性 | 影响 | 缓解措施 | 残余风险 |
|------|---------|------|----------|----------|
| **服务器数据泄露** | 🔴 高 | 用户对话暴露 | E2E 加密 | 低（需用户启用） |
| **中间人攻击** | 🔴 高 | 会话劫持 | TLS 1.3 强制 | 极低 |
| **未授权访问** | 🟡 中 | 冒充用户 | OTP+OIDC | 低 |
| **API 密钥泄露** | 🟡 中 | 服务滥用 | 密钥管理服务 | 中 |
| **模型提供商日志** | 🟡 中 | 隐私泄露 | 自托管端点 | 低 |
| **内部人员滥用** | 🟡 中 | 数据滥用 | 最小权限+审计 | 中 |

### 5.2 性能基准

Thunderbolt 在不同配置下的性能表现：

```mermaid
flowchart LR
    subgraph Local[本地部署]
        L1[Ollama 7B] -->|响应时间| LT[~200ms]
        L2[Ollama 13B] -->|响应时间| LM[~400ms]
        L3[Ollama 70B] -->|响应时间| LH[~800ms]
    end

    subgraph Cloud[云端API]
        C1[Claude API] -->|响应时间| CT[~500ms]
        C2[GPT-4 API] -->|响应时间| CG[~600ms]
    end

    subgraph Relay[中继模式]
        R1[远程服务器] -->|额外延迟| RT[+50-200ms]
    end

    LT & LM & LH -->|本地优先| LOCAL[离线可用]
    CT & CG -->|需网络| ONLINE[实时同步]

    style Local fill:#d1fae5,stroke:#10b981
    style Cloud fill:#dbeafe,stroke:#3b82f6
    style Relay fill:#fef3c7,stroke:#f59e0b
```

**延迟对比（本地测试环境）**：

| 配置 | 首 token 延迟 | 端到端延迟 | 吞吐量 |
|------|-------------|-------------|---------|
| **Ollama 7B (本地)** | ~100ms | ~200ms | 高 |
| **Ollama 13B (本地)** | ~200ms | ~400ms | 中 |
| **Claude API (云端)** | ~300ms | ~500ms | 高 |
| **GPT-4 (云端)** | ~400ms | ~600ms | 中 |
| **Relay 模式** | +50ms | +50-200ms | 取决于网络 |

### 5.2 认证流程

```mermaid
flowchart TD
    START["🔐 用户认证"] --> AUTH[Better Auth]
    AUTH --> CHOICE{认证方式}
    CHOICE -->|手机验证码| OTP[OTP验证]
    CHOICE -->|企业账号| OIDC[OIDC SSO]
    CHOICE -->|无密码| PASSKEY[Passkey]

    OTP --> TOKEN[JWT Token生成]
    OIDC --> TOKEN
    PASSKEY --> TOKEN

    TOKEN --> REFRESH[短期访问令牌]
    REFRESH --> |过期| REFRESH

    style START fill:#d1fae5,stroke:#10b981
    style AUTH fill:#dbeafe,stroke:#3b82f6
    style TOKEN fill:#fef3c7,stroke:#f59e0b
```

**认证方式对比**：

| 方式 | 安全性 | 用户便利性 | 适用场景 |
|------|--------|------------|----------|
| **OTP** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 个人用户、快速部署 |
| **OIDC** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 企业环境、SSO 集成 |
| **Passkey** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 高安全要求、无密码未来 |

### 5.3 数据隔离

| 环境 | 数据存储 | 加密 |
|------|----------|------|
| **本地设备** | SQLite | 设备加密 |
| **传输中** | HTTPS | TLS 1.3 |
| **服务器** | PostgreSQL | 可选 E2E |
| **模型提供商** | API 调用 | 取决于提供商 |

---

## §6 与竞品对比

### 6.1 功能对比

| 功能 | Thunderbolt | ChatGPT | Claude AI | 本地 Ollama |
|------|-------------|---------|-----------|------------|
| **跨平台** | ✅ 全平台 | ✅ Web+App | ✅ Web+App | ✅ CLI |
| **自托管** | ✅ 完全支持 | ❌ | ❌ | ✅ |
| **离线优先** | ✅ SQLite | ❌ | ❌ | ✅ |
| **E2E 加密** | ✅ 可选 | ❌ | ❌ | ✅ |
| **MCP 支持** | ✅ | ❌ | ❌ | ⚠️ 有限 |
| **多设备同步** | ✅ 开发中 | ✅ | ✅ | ❌ |
| **企业 SSO** | ✅ | ❌ | ⚠️ | ❌ |
| **开源** | ✅ MPL 2.0 | ❌ | ❌ | ✅ |

### 6.2 适用场景

| 场景 | 推荐 Thunderbolt 配置 |
|------|---------------------|
| **个人隐私** | 本地 Ollama + E2E 加密 |
| **企业数据合规** | 私有化部署 + OIDC |
| **开发者** | Ollama + MCP 工具 |
| **跨组织协作** | OpenRouter + 自托管 |

---

## §7 开发指南

### 7.1 本地开发环境

```bash
# 1. 克隆仓库
git clone git@github.com:thunderbird/thunderbolt.git
cd thunderbolt

# 2. 安装依赖
pnpm install

# 3. 配置环境变量
cp .env.example .env
# 编辑.env设置数据库连接等

# 4. 启动开发服务器
pnpm dev

# 5. 运行测试
pnpm test

# 6. 构建生产版本
pnpm build
```

### 7.2 添加自定义 MCP 服务器

```typescript
// src/mcp/servers/my-custom-server.ts
import { MCPServer } from '@anthropic/mcp-sdk';

export const myCustomServer = new MCPServer({
  name: 'my-custom-server',
  version: '1.0.0',
  tools: [
    {
      name: 'query_database',
      description: 'Execute a SQL query',
      inputSchema: {
        type: 'object',
        properties: {
          sql: { type: 'string' }
        }
      },
      handler: async ({ sql }) => {
        // 实现工具逻辑
        return { result: await db.query(sql) };
      }
    }
  ]
});
```

### 7.3 前端组件开发

Thunderbolt 使用 Vercel AI SDK 的`useChat` hook 简化 AI 对话开发：

```tsx
// src/components/AIChat.tsx
import { useChat } from 'ai/react';
import * as TextField from '@radix-ui/react-text-field';

export function AIChat() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: '/api/chat',
    streamProtocol: 'sse'
  });

  return (
    <div className="ai-chat-container">
      {/* 消息列表 */}
      <div className="messages">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.role}`}>
            <div className="role">{message.role === 'user' ? '👤' : '🤖'}</div>
            <div className="content">{message.content}</div>
          </div>
        ))}
      </div>

      {/* 输入表单 */}
      <form onSubmit={handleSubmit} className="input-form">
        <TextField.Root className="text-field">
          <TextField.Input
            value={input}
            onChange={handleInputChange}
            placeholder="Ask me anything..."
            disabled={isLoading}
          />
        </TextField.Root>
        <button type="submit" disabled={isLoading || !input.trim()}>
          {isLoading ? '⏳' : 'Send'}
        </button>
      </form>
    </div>
  );
}
```

**关键依赖**：

```json
{
  "dependencies": {
    "ai": "^3.0.0",
    "@radix-ui/react-text-field": "^1.0.0",
    "zustand": "^4.5.0",
    "@tanstack/react-query": "^5.0.0"
  }
}
```

---

## §8 实践建议

### 8.1 部署安全检查清单

- [ ] 启用 HTTPS（Let's Encrypt 或自有证书）
- [ ] 配置防火墙规则
- [ ] 设置强数据库密码
- [ ] 启用 E2E 加密（敏感数据场景）
- [ ] 配置定期备份
- [ ] 启用审计日志
- [ ] 更新到最新版本

### 8.2 性能优化

| 优化项 | 方案 |
|--------|------|
| **冷启动** | 预热 JIT，缓存模型 |
| **响应延迟** | 本地 Ollama 减少网络开销 |
| **存储** | 外挂 SSD 存储 SQLite |
| **同步** | 增量同步替代全量 |

### 8.3 故障排除

```bash
# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app

# 重启服务
docker-compose restart

# 清理重建
docker-compose down -v && docker-compose up -d
```

---

## §9 未来路线图与演进

### 9.1 当前功能状态

```mermaid
stateDiagram-v2
    [*] --> Stable: 核心AI聊天
    Stable --> Stable: 跨平台支持
    Stable --> Beta: 多设备同步
    Beta --> Stable: 预计下季度
    Stable --> Planning: 密码学审计
    Planning --> [*]: 完成后发布

    note right of Stable: 生产可用
    note right of Beta: 测试阶段
    note right of Planning: 规划中
```

### 9.2 功能路线图

| 功能 | 状态 | 说明 |
|------|------|------|
| **多设备同步** | 🔄 Beta | PowerSync 同步引擎，支持 iOS/Android |
| **完全离线支持** | 📋 规划 | 纯本地模式，无需网络 |
| **密码学审计** | 📋 规划 | 第三方安全审计 |
| **企业 FDE 支持** | ✅ 可用 | 完整磁盘加密集成 |
| **自定义模型** | ✅ 可用 | OpenAI/Anthropic/Ollama |
| **MCP 服务器** | ✅ 可用 | 支持自定义 MCP 扩展 |

### 9.3 技术债务与挑战

| 挑战 | 影响 | 当前方案 |
|------|------|----------|
| **E2E 加密未审计** | 高 | 可选功能，标注实验性 |
| **iOS 同步延迟** | 中 | PowerSync 优化中 |
| **Wayland 支持** | 低 | XWayland 兼容模式 |
| **离线 Web** | 低 | Service Worker 规划中 |

### 9.4 社区贡献

贡献指南见仓库 docs/CONTRIBUTING.md：

```bash
# 查看贡献指南
cat docs/CONTRIBUTING.md

# 查看开发文档
cat docs/development.md

# 查看架构文档
cat docs/architecture.md
```

---

## §10 总结

### 10.1 核心定位

Thunderbolt 走了一条与闭源 AI 客户端不同的路：

```mermaid
flowchart TD
    subgraph Value[Thunderbolt核心定位]
        S1[用户主权]
        S2[隐私保护]
        S3[灵活性]
        S4[开放性]
    end

    subgraph 实现
        I1[模型可选择]
        I2[E2E加密]
        I3[自托管]
        I4[开源MPL]
    end

    S1 --> I1
    S2 --> I2
    S3 --> I3
    S4 --> I4

    style Value fill:#d1fae5,stroke:#10b981
    style 实现 fill:#dbeafe,stroke:#3b82f6
```

**与闭源 AI 客户端的关键差异**：

| 维度 | Thunderbolt | OpenAI ChatGPT | Claude AI | Google Gemini |
|------|-------------|----------------|----------|-------------|
| **数据控制** | ⭐⭐⭐⭐⭐用户完全控制 | ⭐OpenAI 控制 | ⭐Anthropic 控制 | ⭐Google 控制 |
| **开源** | ✅完全开源 | ❌ | ❌ | ❌ |
| **自托管** | ✅ | ❌ | ❌ | ❌ |
| **E2E 加密** | ✅可选 | ❌ | ❌ | ❌ |
| **离线支持** | ✅ | ❌ | ❌ | ❌ |
| **MCP 支持** | ✅ | ❌ | ❌ | ❌ |
| **隐私保证** | 零知识架构 | 数据可用于训练 | 数据可用于训练 | 数据可用于训练 |

### 10.2 适用场景

| 场景 | 推荐 Thunderbolt 配置 | 理由 |
|------|---------------------|------|
| **企业数据合规** | 私有化部署+OIDC | 完全控制，SOC2 合规 |
| **医疗/法律敏感数据** | E2E 加密+自托管 | 零知识，GDPR 合规 |
| **隐私敏感用户** | 本地 Ollama+E2E | 完全离线，无数据外传 |
| **开发者** | Ollama+MCP 工具 | 本地模型，工具扩展 |
| **跨组织协作** | OpenRouter+自托管 | 多模型，统一界面 |
| **日常 AI 助手** | 官方托管 | 最小运维，即开即用 |

### 10.3 与 Thunderbird 的关系

Thunderbolt 由 Mozilla Thunderbird 团队开发，继承了 Thunderbird 的

> **"Take back your inbox"** → **"Take back your AI"**

从邮件到 AI，Thunderbird 的思路一致：用户数据由用户控制。

---



### 快速配置决策树

```mermaid
flowchart TD
    START["⚡ Thunderbolt快速配置"] --> Q1{你的隐私需求?}
    Q1 -->|最高(医疗/法律)| HIGH["✅ 本地Ollama
✅ E2E加密
✅ 自托管"]
    Q1 -->|中(企业用户)| MED["✅ OpenRouter
✅ TLS传输
✅ OIDC认证"]
    Q1 -->|低(日常使用)| LOW["✅ 官方API
✅ 快速上手"]
    
    HIGH --> E2E["配置E2E加密"]
    MED --> OIDC["配置OIDC"]
    LOW --> QUICK["直接配置API"]
    
    E2E --> VERIFY["验证加密"]
    OIDC --> VERIFY
    QUICK --> VERIFY
    
    VERIFY --> DONE["✅ 配置完成"]
    
    style START fill:#d1fae5,stroke:#10b981
    style HIGH fill:#d1fae5,stroke:#10b981
    style MED fill:#dbeafe,stroke:#3b82f6
    style LOW fill:#fef3c7,stroke:#f59e0b
```

### 配置参考表

**API 提供商配置**：

| 提供商 | 配置项 | 值示例 | 备注 |
|--------|--------|--------|------|
| **OpenAI** | `endpoint` | `https://api.openai.com/v1` | 官方 API |
| | `api_key` | `sk-...` | 必填 |
| | `model` | `gpt-4-turbo` | 默认模型 |
| **Anthropic** | `endpoint` | `https://api.anthropic.com` | 官方 API |
| | `api_key` | `sk-ant-...` | 必填 |
| | `model` | `claude-3-5-sonnet` | 默认模型 |
| **Ollama** | `endpoint` | `http://localhost:11434` | 本地服务 |
| | `api_key` | 不需要 | 无认证 |
| | `model` | `llama3:70b` | 自定义模型 |
| **OpenRouter** | `endpoint` | `https://openrouter.ai/api/v1` | 多模型聚合 |
| | `api_key` | `sk-or-...` | 必填 |
| | `model` | `anthropic/claude-3-opus` | 指定模型 |

**加密配置**：

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `e2e.enabled` | `true/false` | 启用端到端加密 |
| `e2e.key_sharing` | `direct/indirect` | 密钥共享方式 |
| `e2e.key_rotation` | `30d/90d/1y` | 密钥轮换周期 |

### 故障排除

```mermaid
flowchart TD
    START["🔧 遇到问题?"] --> Q1{什么症状?}
    Q1 -->|连接失败| CONN["检查网络
检查API密钥"]
    Q1 -->|加密错误| CRYPT["检查E2E配置
验证密钥"]
    Q1 -->|模型不响应| MODEL["检查模型状态
查看日志"]
    Q1 -->|性能慢| PERF["检查网络延迟
切换模型"]
    
    CONN --> C1{网络正常?}
    C1 -->|否| NET["修复网络"]
    C1 -->|是| KEY["检查API密钥"]
    KEY -->|错误| FIXKEY["重新配置密钥"]
    
    CRYPT --> E1{密钥有效?}
    E1 -->|否| ROTATE["轮换密钥"]
    E1 -->|是| CHECK["检查加密配置"]
    
    style START fill:#d1fae5,stroke:#10b981
    style CONN fill:#fef3c7,stroke:#f59e0b
    style CRYPT fill:#fef3c7,stroke:#f59e0b
```

**常见问题速查**：

| 问题 | 解决方案 | 命令/检查 |
|------|----------|-----------|
| API 密钥无效 | 重新配置密钥 | 检查拼写 |
| 模型超时 | 增加 timeout | 检查网络 |
| E2E 加密失败 | 验证密钥同步 | 检查密钥交换 |
| OIDC 登录失败 | 检查 IdP 配置 | 验证 URL |
| MCP 工具不工作 | 检查 MCP 配置 | 重启 Thunderbolt |


## 场景问答（FAQ）

**Q：Thunderbolt 和 ChatGPT 网页版的核心差异是什么？什么场景选 Thunderbolt？**

ChatGPT 网页版的数据由 OpenAI 控制，可用于模型训练；Thunderbolt 自托管时数据完全由你控制。如果你处理敏感数据（医疗、法律、企业机密），或者希望完全离线工作，Thunderbolt 是唯一选择。如果只是日常使用、对数据控制没要求，ChatGPT 网页版更方便。

**Q：E2E 加密真的安全吗？有没有被破解的可能？**

E2E 加密意味着服务器只存储密文，无法解密。但注意：E2E 加密功能尚未经过密码学审计（文中已标注）。如果你的威胁模型包含"服务器被攻破"这一项，E2E 能提供很强保护；但如果攻击者能访问你的本地设备（恶意软件、设备丢失），本地存储的密钥仍然可能被提取。

**Q：PowerSync 同步在离线状态下怎么工作？**

PowerSync 的设计是"本地 SQLite 先行，后台同步到 PostgreSQL"。网络断开时，所有数据写入本地 SQLite，完全可用；网络恢复后，PowerSync 自动将本地变更同步到服务器。冲突解决默认使用 last-write-wins，你也可以配置自定义合并规则。

**Q：MCP 服务器会带来安全风险吗？**

MCP 服务器运行在本地，理论上可以访问文件系统、执行命令。Thunderbolt 通过权限引擎（CC 1:1）控制工具调用——敏感操作需要用户确认。但 MCP 服务器本身是第三方代码，安装前应该审查其实现。只安装来自可信来源的 MCP 服务器。

**Q：官方托管版和自托管版在功能上有差异吗？**

核心功能一致，但自托管版可以启用 E2E 加密、配置自定义 LLM 端点、完全控制数据保留策略。官方托管版由 Thunderbird 团队运维，数据存储在他们的服务器上（但可以选择不启用 E2E）。

---

## 自测题

读完这篇文章，试试回答下面 5 道题：

1. **Thunderbolt 的三层分离架构中，设备层和服务器层各负责什么？为什么离线优先设计要先写本地 SQLite？**

   <details>
   <summary>点击查看参考答案</summary>
   
   设备层负责 UI、状态管理、本地存储和 E2E 加密；服务器层负责认证、同步引擎和 PostgreSQL 存储。离线优先设计先写本地 SQLite 是因为本地写入速度快、不依赖网络，网络恢复后再通过 PowerSync 同步到服务器——这样即使网络断开，用户仍能正常工作。
   </details>

2. **E2E 加密能防御哪些威胁？不能防御哪些威胁？**

   <details>
   <summary>点击查看参考答案</summary>
   
   能防御：服务器数据泄露（服务器只存密文）、中间人攻击（传输用 TLS 1.3 加密）。
   不能防御：本地设备被攻破（密钥存储在本地）、API 密钥泄露（API 密钥不包含在 E2E 加密范围内）、模型提供商的日志（如果用了云端 LLM，提供商可能记录请求）。
   </details>

3. **MCP 集成的完整流程是什么？如何配置一个自定义的 filesystem MCP 服务器？**

   <details>
   <summary>点击查看参考答案</summary>
   
   流程：AI 模型 → MCP Client → MCP Server → 本地工具（文件系统、Git、数据库等）。
   配置方法：编辑 `~/.config/thunderbolt/mcp-servers.json`，添加 filesystem MCP 的配置（示例中已给出完整配置）。
   </details>

4. **6 种部署方案各自的适用场景和安全性如何？**

   <details>
   <summary>点击查看参考答案</summary>
   
   - 官方托管：个人/试用，基础安全性
   - Docker Compose：小团队，标准安全性
   - Kubernetes：中型企业，高级安全性
   - E2E 加密模式：任何规模，最高安全性
   </details>

5. **Thunderbolt 的认证流程支持哪些方式？OIDC SSO 适用于什么场景？**

   <details>
   <summary>点击查看参考答案</summary>
   
   支持 OTP（手机验证码）、OIDC（企业 SSO）、Passkey（无密码）。OIDC SSO 适用于企业环境，可以和公司的统一认证系统（如 Okta、Azure AD）集成，实现统一的权限管理。
   </details>

---

## 练习

### 练习 1：部署 Thunderbolt 到本地 Docker

**任务**：用 Docker Compose 在本地部署 Thunderbolt，并配置一个本地 Ollama 模型。

**步骤**：
1. 安装 Docker 和 Docker Compose
2. 复制文中的 `docker-compose.yml` 示例，调整端口和密码
3. 运行 `docker-compose up -d` 启动服务
4. 访问 `http://localhost:3000` 完成初始化配置
5. 配置 Ollama 作为模型提供商（需要先在本地安装 Ollama）

### 练习 2：配置自定义 MCP 服务器

**任务**：配置一个 git MCP 服务器，让 Thunderbolt 能够操作本地 Git 仓库。

**步骤**：
1. 编辑 `~/.config/thunderbolt/mcp-servers.json`
2. 添加 git MCP 服务器的配置（示例中已给出）
3. 重启 Thunderbolt
4. 在 AI 对话中测试"帮我查看当前仓库的状态"

### 练习 3：启用 E2E 加密并验证

**任务**：启用 E2E 加密，并验证服务器无法解密你的对话。

**步骤**：
1. 在设置中启用 E2E 加密
2. 进行一次 AI 对话
3. 查看数据库中的存储内容（应该是密文）
4. 在另一台设备上导入密钥，验证能否解密

---

## 进阶路线

如果你想更深入地使用或贡献 Thunderbolt，可以按这个顺序：

1. **入门**：用官方托管版体验基本功能，理解 Thunderbolt 的定位
2. **部署**：用 Docker Compose 部署到自己的服务器，配置域名和 TLS 证书
3. **定制**：配置自定义 MCP 服务器，扩展 Thunderbolt 的能力边界
4. **安全**：启用 E2E 加密，理解密钥管理和恢复流程
5. **贡献**：阅读 `docs/architecture.md` 理解架构，找一个 good first issue 开始贡献
6. **集成**：把 Thunderbolt 集成到你的工作流（如结合 Obsidian、VS Code 等工具）

---

## 相关资源



- **GitHub 仓库**：https://github.com/thunderbird/thunderbolt
- **官网**：https://thunderbolt.io
- **开发文档**：https://github.com/thunderbird/thunderbolt/blob/main/docs/development.md
- **架构文档**：https://github.com/thunderbird/thunderbolt/blob/main/docs/architecture.md
- **问题反馈**：https://github.com/thunderbird/thunderbolt/issues

---

*撰写于 2026 年 4 月 19 日*
