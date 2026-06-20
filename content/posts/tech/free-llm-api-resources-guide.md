---
title: "free-llm-api-resources：免费LLM API资源汇总清单"
date: "2026-05-06T20:05:34+08:00"
slug: "free-llm-api-resources-guide"
description: "free-llm-api-resources是免费LLM API清单，含OpenRouter、Google AI Studio、NVIDIA NIM、Groq等，适合开发者快速测试与探索。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "API", "免费", "开发者资源"]
---

# free-llm-api-resources：免费 LLM API 资源汇总清单

free-llm-api-resources 是一个由社区维护的免费 LLM API 资源清单，按提供商分类列出可用模型、速率限制和注意事项。项目地址：https://github.com/cheahjs/free-llm-api-resources

> ⚠️ 项目作者提醒：请勿滥用免费服务，否则可能失去这些资源。

## 目录

- [为什么需要这份清单](#为什么需要这份清单)
- [学习目标](#学习目标)
- [免费服务提供商](#免费服务提供商)
- [试用积分服务商](#试用积分服务商)
- [使用建议](#使用建议)
- [错误排查](#错误排查)
- [采用顺序与决策建议](#采用顺序与决策建议)
- [项目信息](#项目信息)

## 为什么需要这份清单

LLM API 的成本门槛会挡住原型验证和教学实验。免费层和试用积分让开发者能在不付费的前提下完成模型选型、Prompt 调试和小规模功能验证。但免费资源分散在各家服务商文档中，速率限制、地区限制、数据使用条款各不相同，逐个核实耗时。这份清单把分散信息聚合到一处，并标注关键限制条件。

## 学习目标

读完本文后，你能够：

- 说出 6 家提供永久免费层的 LLM API 服务商及其代表模型
- 根据延迟、参数规模、部署位置三个维度选择合适的免费提供商
- 识别免费层常见的限制类型（速率、每日配额、地区数据使用条款）
- 用 OpenRouter 统一接口调用多个免费模型进行横向对比
- 规避免费 API 使用中的常见错误（Key 泄露、配额耗尽、地区限制）

## 免费服务提供商

### OpenRouter

OpenRouter 是聚合式 LLM API 网关，用同一个 API Key 和接口访问数十个模型。部分模型标注 `$0` 表示永久免费：

- Gemma 3 12B Instruct
- Gemma 3 27B Instruct
- Llama 3.3 70B Instruct
- Qwen3 Coder
- DeepSeek 系列部分模型

速率限制：20 请求/分钟，50 请求/天。充值 $10 后提升至 1000 请求/天。

调用示例（OpenAI 兼容接口）：

```bash
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/llama-3.3-70b-instruct:free",
    "messages": [{"role": "user", "content": "用一句话解释 RAG"}]
  }'
```

统一接口的价值在于切换模型只需改 `model` 字段，便于横向对比同一 Prompt 在不同模型上的表现。

### Google AI Studio

Google AI Studio 提供 Gemini 系列和 Gemma 系列模型的免费层。截至撰写时，免费层模型与限制如下：

| 模型 | 速率限制 | 每日请求 |
|------|----------|----------|
| Gemini 2.5 Flash | 250,000 tokens/分钟 | 20 请求/天 |
| Gemini 2.5 Flash-Lite | 250,000 tokens/分钟 | 500 请求/天 |
| Gemini 2.0 Flash | 250,000 tokens/分钟 | 20 请求/天 |
| Gemma 3 27B/12B/4B/1B | 15,000 tokens/分钟 | 14,400 请求/天 |

> ⚠️ 在英国、瑞士、欧洲经济区以外地区使用免费层时，输入数据可能被用于模型训练。涉及敏感数据的场景应使用付费层或更换提供商。

### NVIDIA NIM

NVIDIA NIM（NVIDIA Inference Microservices）提供部分 NVIDIA 自研和合作模型的免费访问端点。截至撰写时可用的免费模型：

- Nemotron Nano 30B A3B
- Nemotron Super 120B A12B
- GPT-OSS 120B / 20B

NIM 端点适合需要较大参数模型进行基准测试的场景，速率限制较严格，不适合持续负载。

### Groq

Groq 使用 LPU 推理芯片，主打低延迟。免费层模型包括：

- Llama 3.2 3B Instruct
- Llama 3.1 8B Instruct
- Mixtral 8x7B

Groq 的 token 生成速度通常在数百 tokens/秒量级，适合需要实时交互的应用原型（如流式对话、低延迟代理）。免费层有每日 token 配额，高峰期可能限流。

### Cerebras

Cerebras 基于 Wafer-Scale Engine 提供免费推理：

- Llama 3.1 405B（速率有限）
- Llama 3.1 70B

405B 模型在多数服务商处需要付费，Cerebras 免费层适合研究超大模型行为的场景，例如对比 70B 与 405B 在同一任务上的能力差异。

### Cloudflare Workers AI

Cloudflare Workers AI 在全球边缘节点部署开源模型推理：

- 模型集合包含 Llama、Mistral、Qwen 等开源系列
- 推理在距离用户最近的边缘节点执行，延迟低
- 通过 Workers 绑定调用，与 Cloudflare 生态集成

适合需要在边缘侧集成 AI 推理的 Web 应用，每日有免费 token 额度。

### HuggingFace Inference Providers

HuggingFace 汇总了多家推理提供商的端点，覆盖 Mistral、Qwen、Yi 等开源模型。模型卡片页可直接发起推理请求，适合快速测试不同开源模型的能力边界。

### Vercel AI Gateway

Vercel AI Gateway 聚合多个 LLM 提供商，统一管理 API Key 和用量。免费层支持基础聚合功能，与 Vercel 部署的应用集成度高。

## 试用积分服务商

以下服务商不提供永久免费层，但为新用户提供一次性试用积分：

| 服务商 | 说明 |
|--------|------|
| Fireworks | 新用户赠送试用积分 |
| Baseten | 提供免费部署额度 |
| Nebius | 试用积分 |
| Novita | 新用户试用 |
| Hyperbolic | 试用积分 |
| SambaNova Cloud | 部分模型免费试用 |
| Modal | 计算资源试用 |

试用积分适合短期项目验证，长期使用需切换到付费层或迁移到永久免费提供商。

## 使用建议

### 避免滥用

免费资源能持续提供的前提是用户不超出使用边界：

- 遵守各平台的速率限制和每日配额
- 不使用免费层承载商业生产流量
- 开发测试优先使用试用积分，保留永久免费额度用于持续集成
- 商业项目上线前切换到付费层

### 按需求场景选择

| 需求场景 | 推荐选择 | 理由 |
|----------|----------|------|
| 低延迟推理 | Groq、Cloudflare Workers AI | LPU 和边缘节点延迟最低 |
| 超大参数模型测试 | Cerebras、NVIDIA NIM | 提供 405B 等超大模型免费端点 |
| 多模型横向对比 | OpenRouter | 单一 Key 切换数十个模型 |
| 开源模型探索 | HuggingFace Inference Providers | 模型覆盖最广 |
| 边缘部署 | Cloudflare Workers AI | 与 Workers 生态原生集成 |
| Google 生态 | Google AI Studio | Gemini 系列官方免费层 |

### 安全注意事项

- 不要将 API Key 提交到公开代码仓库
- 使用环境变量或密钥管理服务（如 `.env` 文件配合 `.gitignore`）
- 定期轮换 API Key，发现泄露立即吊销
- 免费层 Key 也具备调用权限，泄露后会被恶意消耗配额

## 错误排查

调用免费 LLM API 时常见错误及处理：

| 错误现象 | 可能原因 | 处理方式 |
|---------|---------|---------|
| 429 Too Many Requests | 触发速率限制 | 退避重试，降低请求频率 |
| 403 Forbidden | 地区限制或 Key 失效 | 检查服务商地区支持列表，重新生成 Key |
| 模型返回空或截断 | 触发内容过滤或超长 | 调整 Prompt，分段请求 |
| 503 Service Unavailable | 服务商临时过载 | 切换备用提供商或等待恢复 |
| 配额突然归零 | Key 泄露被恶意调用 | 立即吊销 Key，检查代码仓库历史 |

多提供商场景下，建议在代码中实现 Provider fallback：主提供商返回 429 或 5xx 时自动切换到备用提供商。

## 采用顺序与决策建议

如果你是初次接入免费 LLM API，建议按以下顺序：

1. **从 OpenRouter 入手**：一个 Key 接入多模型，快速建立对不同模型能力的直观认知
2. **按场景补充专用提供商**：低延迟需求加 Groq，超大模型需求加 Cerebras，Google 生态加 AI Studio
3. **教学或演示场景**：使用 Cloudflare Workers AI 或 HuggingFace，无需信用卡
4. **进入生产前**：选定主力模型后切换到对应服务商的付费层，保留免费层作为 fallback
5. **持续监控**：免费层条款可能调整，定期回看仓库 README 获取最新限制

## 项目信息

- **GitHub**：https://github.com/cheahjs/free-llm-api-resources
- **维护方式**：社区驱动，持续更新
- **许可证**：以仓库 LICENSE 文件为准
