---
title: "Switchyard：让编码智能体无缝对接开源模型的 LLM 路由代理"
date: 2026-08-15T03:24:06+08:00
slug: "switchyard-llm-routing-proxy"
github_repo: "NVIDIA-NeMo/Switchyard"
source_key: "gh:NVIDIA-NeMo/Switchyard"
description: "Switchyard 是 NVIDIA NeMo 团队开源的 Rust LLM 流量代理与库，负责跨提供方路由请求、在 OpenAI 与 Anthropic API 间翻译、记录运维指标，并提供类型化、可组合的路由算法。目标是让 Claude Code、Codex 等编码智能体原生对接 vLLM、NVIDIA NIM、Ollama 等开源端点。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "路由", "Rust", "OpenAI API", "Anthropic API", "NVIDIA"]
---

# Switchyard：让编码智能体无缝对接开源模型的 LLM 路由代理

**核心判断**：Switchyard 解决的是一个很具体的现实问题——Claude Code、Codex 这类编码智能体只会说自己的原生 API（Anthropic Messages 或 OpenAI Responses），而你想让它跑在一个开源模型（vLLM、NVIDIA NIM、Ollama）上。Switchyard 做的就是在中间做协议翻译 + 路由，让智能体"继续讲母语"，后端却换成了你选的模型。它的价值在于：协议转换 + 可组合路由算法 + 运维指标，三者打包成一个 Rust 代理/库。

**成熟度提醒**：README 明确标注这是 **pre-alpha 软件，正在快速演进，不用于生产**。API 与算法在 v1.0 前预计会有显著变化。写这篇文章时把它定位为"值得评估的方向"，而非可直接上生产的方案。仓库 2026 年 5 月才开源，采用 Apache-2.0 许可，2026 年 8 月时约 330 stars——足够新，API 快速变动并不意外。

## 系统地图

```
Clients（Claude Code / Codex / OpenClaw ...）
      │  保持各自原生 API（OpenAI / Anthropic）
      ▼
┌──────────────────────────────────────────┐
│  Switchyard：路由 · 翻译 · 回退          │
│  接受 OpenAI Chat / OpenAI Responses /   │
│  Anthropic Messages                      │
└──────────────────────────────────────────┘
      │  以 backend 原生格式转发
      ▼
Backends（vLLM / NVIDIA NIM / Ollama / OpenAI 兼容端点）
```

## 核心能力

### 协议翻译

在 OpenAI Chat、Anthropic Messages、OpenAI Responses 三种格式之间转换。这是"用开源模型跑闭源智能体"的关键桥接层——后端把请求按它自己的原生格式处理，Switchyard 再把响应翻译回客户端期望的形状。

### 多后端路由

内置多种路由策略，或自定义算法：

| 策略 | 适用场景 | route type |
|------|---------|-----------|
| LLM Classifier | 请求内容应决定用弱档还是强档模型 | `llm_classifier` |
| Stage Router | 会话中已有的信号（工具结果、错误）决定大部分轮次，避免额外模型调用 | `stage_router` |
| Escalation Router | 每轮先跑弱档，judge 读取答案判断是否把同一请求送到强档 | `llm_classifier` + `mode="escalation"` |
| Random | 需要固定流量切分做 A/B、基线或成本实验 | `random` |

另外 `passthrough` 路由只注册一个 target 对应一个 model ID，不做路由决策。

### 运维指标

通过 Prometheus 暴露指标，覆盖请求数、错误、延迟、token 用量与路由开销。这让"把流量分给多个模型"这件事变得可观测、可对比。

## 三种使用方式

### 1. Launcher 路径（跑 Claude Code / Codex / OpenClaw）

安装工具并启动：

```bash
uv tool install --python 3.10 "nemo-switchyard[cli]"
export OPENROUTER_API_KEY="your-openrouter-key"
switchyard launch claude --model switchyard
switchyard launch codex --model switchyard
switchyard launch openclaw --model switchyard
```

用自定义 TOML 部署则传路由 ID 与配置：

```bash
switchyard launch claude --model my-route --config routes.toml
```

### 2. Server 路径（独立 Rust 代理）

```bash
cargo install --locked switchyard-server
export OPENROUTER_API_KEY="your-openrouter-key"
switchyard-server --config routes.toml --dry-run
switchyard-server --config routes.toml --host 127.0.0.1 --port 4000
```

验证：

```bash
curl http://localhost:4000/health
```

### 3. Library 路径（嵌入自己的 Rust 应用）

`switchyard-libsy` 把路由算法嵌入你自己的 Rust 应用。它自己从不调用模型——由算法决定用哪个 target，再把模型调用交还给你，因此可以塞进现有 proxy、gateway 或 agent runtime，而不必拥有 HTTP 栈；若想让它替你完成模型调用，再配合 `switchyard-llm-client` crate 即可。

```toml
[dependencies]
switchyard-libsy = { git = "https://github.com/NVIDIA-NeMo/Switchyard.git" }
switchyard-protocol = { git = "https://github.com/NVIDIA-NeMo/Switchyard.git" }
```

## 适用边界

- **适合**：评估"如何让编码智能体跑开源模型"的架构可行性；需要跨 OpenAI/Anthropic 协议桥接；需要信号驱动的模型路由或 A/B 对比。
- **不适合**：当前是 pre-alpha，**不用于生产**；API 和算法会快速变化，锁定版本做长期依赖需谨慎。
- **关联澄清**：它与 NVIDIA NeMo（对话式 AI 框架）、SkillSpector（skill 安全扫描器）是不同的项目，只是同属 NVIDIA 系开源生态，三者无功能重叠。

## 进一步阅读

- 快速上手与完整配置：`docs/getting_started.md`
- 路由算法总览：`docs/routing_algorithms/overview.md`
- crates 文档：`switchyard-server` / `switchyard-libsy` / `switchyard-protocol` / `switchyard-translation`
