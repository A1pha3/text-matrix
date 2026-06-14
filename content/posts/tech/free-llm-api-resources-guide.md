---
title: "free-llm-api-resources：免费LLM API资源汇总清单"
date: "2026-05-06T20:05:34+08:00"
slug: "free-llm-api-resources-guide"
description: "free-llm-api-resources是免费LLM API清单，含OpenRouter、Google AI Studio、NVIDIA NIM、Groq等，适合开发者快速测试与探索。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "API", "免费", "开发者资源"]
---

free-llm-api-resources 是一个由社区维护的**免费 LLM API 资源清单**，帮助开发者快速找到可以免费使用或试用的大语言模型 API 服务。该项目持续更新，涵盖了从免费层到试用积分等多种形式的资源。

> ⚠️ 项目作者特别提醒：请勿滥用这些免费服务，否则我们可能会失去这些宝贵的资源。

## 免费服务提供商

### OpenRouter

OpenRouter 提供聚合式的 LLM API 访问，支持数十个模型。部分模型提供**永久免费额度**（$0）：

- Gemma 3 12B Instruct（免费）
- Gemma 3 27B Instruct（免费）
- Llama 3.3 70B Instruct（免费）
- Qwen3 Coder（免费）
- DeepSeek 系列部分模型（免费）

限制：20 请求/分钟，50 请求/天。充值 $10 可提升至 1000 请求/天。

**特点**：统一接口访问多个模型，支持模型对比。

### Google AI Studio

Google AI Studio 提供 Gemini 系列模型的免费试用：

| 模型 | 速率限制 | 每日请求 |
|------|----------|----------|
| Gemini 3 Flash | 250,000 tokens/分钟 | 20 请求/天 |
| Gemini 3.1 Flash-Lite | 250,000 tokens/分钟 | 500 请求/天 |
| Gemini 2.5 Flash | 250,000 tokens/分钟 | 20 请求/天 |
| Gemma 3 27B/12B/4B/1B | 15,000 tokens/分钟 | 14,400 请求/天 |

> ⚠️ 注意：在英国、瑞士、欧洲经济区等地区以外使用时，数据会用于模型训练。

### NVIDIA NIM

NVIDIA NIM（NVIDIA Inference Microservices）提供部分模型免费访问：

- Nemotron 3 Nano 30B A3B（免费）
- Nemotron 3 Super 120B A12B（免费）
- GPT-OSS 120B / 20B（免费）

适合需要较大参数模型但预算有限的开发者。

### Groq

Groq 以推理速度快著称，提供以下免费模型：

- Llama 3.2 3B Instruct
- Llama 3.1 8B Instruct
- Mixtral 8x7B

Groq 的免费层限制较为宽松，适合需要低延迟响应的应用场景。

### Cerebras

Cerebras 提供超大参数模型的免费访问：

- Llama 3.1 405B（免费，速率有限）
- Llama 3.1 70B（免费）

Cerebras 的最大亮点是超大模型免费访问，适合研究和小规模应用测试。

### Cloudflare Workers AI

Cloudflare Workers AI 提供边缘部署的免费 LLM 推理：

- 多种开源模型可用
- 基于 Cloudflare 全球边缘网络，低延迟

适合需要在边缘部署 AI 推理能力的应用。

### HuggingFace Inference Providers

HuggingFace 汇总了多个推理提供商的免费端点，覆盖大量开源模型。适合需要快速测试各类开源模型（如 Mistral、Qwen、Yi 等）的开发者。

### Vercel AI Gateway

Vercel AI Gateway 聚合多个 LLM 提供商，支持统一接口管理 API Key 和用量。免费层支持基础聚合功能。

## 试用积分服务商

部分服务商不提供永久免费层，但提供试用积分：

| 服务商 | 说明 |
|--------|------|
| Fireworks | 新用户赠送试用积分 |
| Baseten | 提供免费部署额度 |
| Nebius | 试用积分 |
| Novita | 新用户试用 |
| Hyperbolic | 试用积分 |
| SambaNova Cloud | 部分模型免费试用 |
| Modal | 计算资源试用 |

## 使用建议

### 避免滥用

免费资源之所以能持续提供，关键在于用户不滥用。以下是维护社区利益的建议：

- 遵守各平台的速率限制
- 不要使用免费资源运行商业生产服务
- 优先选择有试用积分的服务商进行开发测试
- 商业项目及时切换到付费层

### 选择合适的提供商

| 需求场景 | 推荐选择 |
|----------|----------|
| 低延迟推理 | Groq、Cloudflare Workers AI |
| 超大参数模型测试 | Cerebras、NVIDIA NIM |
| 快速原型开发 | OpenRouter、Google AI Studio |
| 开源模型探索 | HuggingFace Inference Providers |
| 边缘部署 | Cloudflare Workers AI |

### 安全注意事项

- 不要将 API Key 提交到公开代码仓库
- 使用环境变量管理敏感信息
- 定期轮换 API Key

## 项目信息

- **GitHub**：https://github.com/cheahjs/free-llm-api-resources
- **维护者**：社区驱动，持续更新
- **许可证**：MIT（推测，具体见仓库）

## 总结

free-llm-api-resources 是一个实用的开发者资源清单，尤其适合：

- 正在学习 LLM API 集成的初学者
- 需要快速测试不同模型能力的开发者
- 探索不同 LLM 提供商的研究人员
- 预算有限但需要使用大模型的独立开发者

建议收藏并在需要时查阅，但务必尊重各平台的使用条款，避免因滥用导致资源被回收。
