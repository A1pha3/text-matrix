---
title: "new-api：26.7K Stars 的 LLM 网关——多模型聚合与支付计费的从入门到精通"
date: "2026-04-14T20:30:00+08:00"
slug: "new-api-llm-gateway"
description: "new-api 是 26.7K Stars 的开源 LLM 网关，支持 OpenAI Claude Gemini 等多模型聚合，智能路由负载均衡，内置支付计费和用户管理系统，支持 Docker 一键部署，适合需要聚合多个 AI API 的开发者和企业。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "API网关", "AI", "Claude", "OpenAI", "GPT"]
---

# new-api：26.7K Stars 的 LLM 网关——多模型聚合与支付计费的从入门到精通

> **目标读者**：需要聚合多个 AI API 的开发者、企业技术负责人、Bug Bounty 开发者
> **预计阅读时间**：45-60 分钟
> **前置知识**：Python 基础、API 概念、Docker 基础
> **难度定位**：⭐⭐⭐⭐ 专家设计

---

## §1 学习目标

完成本篇文章后，你将能够：

1. **理解 LLM API 网关的核心价值**：为何需要聚合多个 AI 提供商
2. **掌握 new-api 的核心架构**：格式转换引擎、智能路由、负载均衡
3. **能够完成生产级部署**：Docker 部署、数据库配置、反向代理
4. **理解支付计费系统**：如何实现按量计费、用户管理
5. **掌握 API 调用方式**：如何从 OpenAI 切换到 Claude

---

## §2 原理分析：LLM API 网关的需求与价值

### 2.1 痛点问题

**多 AI 模型管理的困境**：

| 问题 | 说明 |
|------|------|
| **模型分散** | OpenAI Claude Gemini 各有 API，需要维护多个客户端 |
| **价格差异** | 不同模型价格不同，需要成本控制 |
| **Key 管理** | 每个模型有独立 Key，难以集中管理 |
| **负载不均** | 单模型调用量大容易触发限流 |

### 2.2 new-api 的解决方案

new-api 是一个统一入口，将多个 LLM API 聚合为一个：

```
┌─────────────────────────────────────────────────────────────────┐
│                      new-api 网关架构                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   客户端（OpenAI 格式）                                         │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                   new-api 网关                           │   │
│   │                                                         │   │
│   │   ┌─────────────┐    ┌─────────────┐                   │   │
│   │   │ 格式转换器   │───▶│ 智能路由器  │                   │   │
│   │   │ OpenAI→X    │    │ 负载均衡   │                   │   │
│   │   └─────────────┘    └──────┬──────┘                   │   │
│   │                              │                            │   │
│   └──────────────────────────────┼────────────────────────────┘   │
│                                  │                                 │
│          ┌───────────────────────┼───────────────────────┐       │
│          ▼                       ▼                       ▼       │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐      │
│   │  OpenAI    │     │  Claude    │     │  Gemini    │      │
│   │   API      │     │   API      │     │   API      │      │
│   └─────────────┘     └─────────────┘     └─────────────┘      │
│                                                                 │
│   ┌─────────────┐     ┌─────────────┐                           │
│   │ 支付计费    │     │ 用户管理    │                           │
│   └─────────────┘     └─────────────┘                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## §3 核心功能

### 3.1 多模型聚合

支持以下模型：

| 提供商 | 模型 |
|--------|------|
| **OpenAI** | GPT-4o, GPT-4-turbo, GPT-3.5-turbo |
| **Anthropic** | Claude 3.5 Sonnet, Claude 3 Opus |
| **Google** | Gemini 1.5 Pro, Gemini 1.5 Flash |
| **其他** | Ollama, Groq, Cloudflare Workers AI 等 |

### 3.2 格式转换

```python
# 客户端使用 OpenAI 格式
response = openai.ChatCompletion.create(
    model="claude-3-5-sonnet",
    messages=[{"role": "user", "content": "Hello"}]
)

# new-api 自动转换为 Claude 格式
# 返回时再转回 OpenAI 格式
```

### 3.3 智能路由

```yaml
# 智能路由配置示例
routing:
  - path: /v1/chat/completions
    upstream:
      - provider: openai
        weight: 50
      - provider: claude
        weight: 50
```

---

## §4 使用说明

### 4.1 Docker 部署

```bash
# 下载配置
git clone https://github.com/QuantumNous/new-api.git
cd new-api

# 修改配置
cp config.example.yaml config.yaml
vim config.yaml

# 启动服务
docker-compose up -d
```

### 4.2 API 调用

```bash
# 设置 API 地址
export OPENAI_API_BASE="http://localhost:3000/v1"

# 正常使用 OpenAI SDK
curl http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

---

## §5 支付计费系统

### 5.1 额度管理

```yaml
# 用户额度配置
billing:
  - user: user123
    credits: 1000
    models:
      gpt-4o: 0.01  # 每 1K tokens $0.01
      claude-3-5-sonnet: 0.015
```

### 5.2 使用量统计

```bash
# 查看用户使用量
curl http://localhost:3000/admin/usage \
  -H "Authorization: Bearer $ADMIN_KEY"
```

---

## §6 相关资源

| 资源 | 链接 |
|------|------|
| **GitHub** | [github.com/QuantumNous/new-api](https://github.com/QuantumNous/new-api) |

---

**文档信息**
难度：⭐⭐⭐⭐ | 类型：专家设计 | 更新日期：2026-04-14 | 预计阅读时间：45-60 分钟
