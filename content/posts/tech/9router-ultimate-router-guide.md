---
title: "9Router：给 AI 编程工具套一层免费用量的路由"
date: "2026-04-12T02:31:39+08:00"
slug: 9router-ultimate-router-guide
github_repo: "decolua/9router"
description: "9Router 是运行在本地的 AI 路由层，把 Claude Code、Cursor、Codex 等 CLI 工具接到订阅、廉价、免费三层后端，并用 RTK 压缩工具输出省 Token。本文拆它的机制、边界和该不该用。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Cursor", "Token 优化", "API网关"]
---

# 9Router：给 AI 编程工具套一层免费用量的路由

AI 编程工具烧钱的方式就那么几种：工具调用的输出占 Token、订阅额度每个月清零、主模型宕机或限流时工作停下来。9Router 把这三件事都收进一个本地运行的代理层，让 CLI 工具始终以为自己在跟同一个后端对话。

它和 OpenRouter、One API、LiteLLM 这类网关不一样的地方在于：目标不是"聚合多少家 API"，而是"怎么把已有的额度用干净"。订阅、廉价、免费三层自上而下自动降级，加上 RTK 对工具输出的压缩，是它区别于通用代理的核心。

## 系统总览：代理层里四条并列的机制

9Router 看起来像 OpenAI 兼容格式的反代——收到请求、换个格式、发出去。代理层内部实际跑了四条独立的线，各自解决一个问题：

| 机制 | 解决的问题 | 不解决的问题 |
|------|-----------|-------------|
| RTK Token Saver | `git diff`、`grep` 这类工具输出占 Token 多 | 不压缩对话历史、不压缩模型推理 |
| 三层自动降级 | 主模型额度耗尽或宕机后工具停工 | 不提升模型回答质量 |
| 配额追踪 | 订阅到期了额度还没用完 | 不帮你多拿额度 |
| 多账号轮询 | 单个账号的速率限制 | 不绕过服务商的并发上限 |

```mermaid
flowchart TB
 subgraph CLI["CLI 工具层"]
 CC["Claude Code"]
 CX["Codex"]
 OC["OpenClaw"]
 CS["Cursor / Cline / Copilot / ..."]
 end

 subgraph Router["9Router（localhost:20128）"]
 direction TB
 API["OpenAI 兼容 API :20128/v1"]
 RTK["RTK Token Saver<br/>工具输出压缩 20-40%（官方口径）"]
 FMT["格式翻译<br/>OpenAI ↔ Claude"]
 QT["配额追踪"]
 LB["多账号轮询"]

 API --> RTK
 RTK --> FMT
 FMT --> QT
 QT --> LB
 end

 subgraph Tier1["第一层：订阅账号"]
 CCSub["Claude Code 订阅"]
 CXSub["Codex 订阅"]
 GHSub["GitHub Copilot"]
 end

 subgraph Tier2["第二层：廉价 API"]
 GLM["GLM ~$0.6/1M"]
 MM["MiniMax ~$0.2/1M"]
 end

 subgraph Tier3["第三层：免费渠道"]
 Kiro["Kiro AI（50 credits/月）"]
 OpenCodeF["OpenCode Free（免认证）"]
 Vertex["Vertex AI（$300 赠金）"]
 end

 CLI --> API
 LB -.-> Tier1
 LB -.配额耗尽.-> Tier2
 LB -.预算触顶.-> Tier3
```

这四个机制里，RTK 和三层降级是最能拉开它和普通代理差距的两块，下面分别看。

## RTK：只压缩工具输出，不碰对话

工具调用是 CLI 编程里最烧 Token 的地方。一次修 bug 的过程大致是：Agent 读文件拿到全文、跑 `git diff` 拿到改动、跑测试拿到结果，然后把这些输出全部塞回下一次请求的上下文。一个中型项目的 `git diff` 可能就是几千 Token，而一次会话里这样的工具调用能触发上百次。

RTK（9Router 里的缩写，官方文档没给出完整展开）在代理层截获 `tool_result` 这类消息，做结构化压缩：去掉连续重复的输出、折叠超过设定行数的 diff 块、精简 JSON 的格式化空白。按官方口径能省 20-40% 的 Token，GitHub 仓库描述里写的数字是 -40%。

它只处理工具输出，不碰对话历史。原因很直接：工具输出是原始数据，压缩它不改变模型推理；对话历史里带着系统提示和此前的推理上下文，压缩这条线容易丢信息、改变模型行为。纯对话请求（没有工具调用）RTK 直接透传。

## 三层降级：订阅 → 廉价 → 免费

降级按两层条件触发，行为不同：

| 触发类型 | 表现 | 动作 |
|---------|------|------|
| 配额耗尽 | 订阅额度被用完 | 切到下一层 |
| 调用失败 | HTTP 429 / 5xx / 超时 | 重试若干次后切到下一层 |

三层结构：

1. **订阅层**：通过 OAuth 接 Claude Code、Codex、GitHub Copilot 等订阅账号，直接消费已付费额度。
2. **廉价层**：GLM（约 $0.6/百万 Token）、MiniMax（约 $0.2/百万 Token）这类按量付费但便宜的渠道。
3. **免费层**：Kiro AI、OpenCode Free、Vertex AI 这类零成本渠道。

对客户端来说切换是无感的——CLI 工具配置的永远是同一个 `localhost:20128/v1` 端点，额度耗尽后请求自动落到下一层，工具侧不感知。

## 免费渠道的现状，比想象中更波动

免费层是 9Router 宣传里最吸引人的部分，但也是政策变化最快的地方。README 里明确写了：

- **iFlow、Qwen Code、Gemini CLI** 的免费层在 2026 年已停用，不再作为可用渠道。
- **Kiro AI** 自 2025 年 9 月起转为付费模型，免费层现在是每月 50 credits，新账号头 30 天有 500 credits 试用；付费档从 $20/月起。
- **OpenCode Free** 免认证，但可用模型列表会浮动，部分模型只限时免费。
- **Vertex AI** 的 $300 赠金对新 GCP 账号仍然有效，但自 2026 年 3 月起 Gemini API 端点不再消耗赠金，要用 Vertex AI Studio 端点。

所以"Kiro 免费"这种印象已经不准了。真要看当前哪些渠道还能用，得打开 Dashboard 的 Providers 页面，而不是信旧文章。

## 配额与多账号：把订阅额度用干净

订阅额度每个月清零，是 9Router 盯上的第二个浪费点。配额追踪模块在 Dashboard 上展示每个订阅账号的剩余额度，配合降级策略优先消耗订阅额度，切到付费渠道之前先把订阅榨干。

多账号轮询则是把同一个提供商的多个账号做 round-robin 分配，把一个账号的速率限制分摊到多个账号上。它解决的是单账号的 RPM 限制，绕不开服务商按全局算的并发上限——用几个 Key 不会把并发上限变成几倍。

## Dashboard 与数据落点

9Router 自带一个 Web Dashboard（Next.js 构建），负责管理提供商的 OAuth 授权和 API Key、配置三层降级与每层模型偏好、看每个账号的剩余额度和 Token 用量、开关 RTK 并调压缩参数、生成客户端用的内部 API Key。

运行时数据存在本地 `~/.9router/` 目录下，请求日志只在内存里走一遍，不落盘。OAuth 订阅的 Token 和 API Key 都存在本地，9Router 本身不在线与外部服务交换这些凭据。

## 安装与接入

npm 全局安装后直接运行：

```bash
npm install -g 9router
9router
```

Dashboard 自动在 `http://localhost:20128` 打开，OpenAI 兼容端点是 `http://localhost:20128/v1`。从源码跑的方式是 `npm run dev` 或 `npm run build && npm run start`，需要设置 `NEXT_PUBLIC_BASE_URL`。要求 Node 18 以上。

CLI 工具的接法统一——把端点指向本地：

```bash
export OPENAI_BASE_URL=http://localhost:20128/v1
export OPENAI_API_KEY=<Dashboard 里生成的 Key>
```

这个 Key 是 Router 的内部标识，不是真实 API Key；真实凭据存在本地 SQLite 里。Cursor 这类工具在设置里把 base URL 和 API Key 填成同样的值即可。

## 该不该用

- **适合先上的**：Claude Code / Codex 这类工具调用频繁的重度用户，RTK 压缩的收益最直接；手里有多个订阅号或 API Key 的人，轮询能把速率限制分摊掉、额度集中消耗；想用免费渠道跑日常任务的人，9Router 让这些渠道和 CLI 工具对接起来不用改配置。
- **可以等等的**：只用一个模型、从不触达速率限制，直接配环境变量就够了，中间多一层代理只增加延迟；对请求延迟极其敏感的场景，直连更快；公司安全策略不允许本地起 HTTP 服务的话，这一条就卡死了。

真要试，顺序建议是先接免费渠道跑一段时间，对照 Dashboard 的用量统计看是否够用，够用再考虑把订阅号和廉价层加进来，最后再开 RTK——RTK 压缩 diff 可能丢掉关键上下文，先在非关键项目上验证一遍再放开。

## 结语

9Router 的实际工作集中在 RTK 压缩、三层降级和配额榨干三件事上，路由只是入口。单独看每一项都有替代方案，但三件事在一个 Dashboard 里完成、且不需要改 CLI 工具配置，这是它和通用代理方案的差异。

它的范围限定在 CLI 编程工具和 AI 后端之间——做精简、兜底和额度利用，不涉及多模型调度、prompt 管理或 RAG。OpenRouter、LiteLLM 这类网关覆盖的面更宽，9Router 走的是更窄的一条路。

仓库在 [github.com/decolua/9router](https://github.com/decolua/9router)，免费渠道的具体政策以 Dashboard 的 Providers 页面为准。