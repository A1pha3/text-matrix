---
title: "wigolo：本地优先的 AI Agent Web 智能层，无 API Key 跑 MCP"
date: 2026-07-20T03:02:36+08:00
categories: ["技术笔记"]
tags: ["mcp", "local-first", "web-search", "ai-agent", "rag"]
description: "wigolo 是一个本地优先的 AI Agent Web 智能层，通过 MCP 把搜索、抓取、爬取、提取、缓存全部装进 ~1.5 GB 磁盘，零云、零 API key、零查询费用，公开 beta 已对接 Claude Code / Cursor / Codex / Gemini CLI。"
---

# wigolo：本地优先的 AI Agent Web 智能层，无 API Key 跑 MCP

## 一句话判断

wigolo 把 AI Agent 需要的所有 Web 能力——搜索、抓取、爬取、提取、缓存、find-similar、research——全部塞进一个本地引擎，对外暴露成 MCP（Model Context Protocol，模型上下文协议）server 或 REST，**零云、零 API key、零查询费用**，搜索 / 抓取 / 爬取 / 提取 / 缓存 / find-similar 全部 keyless，只有 research / agent / `search format=answer` 需要一个 LLM key（免费的 Gemini key 即可）。对一个每天跑 100+ web query 的 coding agent 用户来说，这意味着账单消失。

## 项目定位

- **仓库**：`KnockOutEZ/wigolo`，TypeScript 实现
- **GitHub Stars**：1.7K，Forks 105（2026-07-19 数据）
- **状态**：public beta
- **覆盖工具**：search / fetch / crawl / extract / cache / find-similar / research / agent
- **安装要求**：Node ≥ 20，~1.5 GB 磁盘
- **支持客户端**：Claude Code、Cursor、Codex、Gemini CLI、VS Code、Windsurf、Zed、Antigravity、LangChain、CrewAI、LlamaIndex、Vercel AI SDK、n8n、任意 MCP client、纯 REST

## 系统地图

| 模块 | 责任 | 是否需要 API key |
|------|------|------------------|
| Browser engine | 抓取 / 渲染 SPA（Single Page Application，单页应用） | ❌ keyless |
| On-device models | 提取 / 摘要 / query 改写 | ❌ keyless |
| Cache layer | 跨 session 的本地缓存 `~/.wigolo/` | ❌ keyless |
| MCP server | 把上述能力暴露成 MCP 协议 | ❌ keyless |
| REST endpoint | 同上，REST 风格 | ❌ keyless |
| Research / Agent | 写总结 / 写结构化答案 | ⚠️ 推荐免费 Gemini key |

设计的关键是 **"默认 keyless，key 只用于'写'"**。抓、搜、爬、提取全部走本地引擎；只有当用户真的需要一段"经过 LLM 综合、引文组织"的答案时，才走 key。这一刀切在"agent 90% 的调用是 fetch/crawl/extract"的位置，把成本和延迟同时砍掉。

## 关键机制拆解

### 1. 一行命令接入

wigolo 把 setup 压成一行：

```bash
npx wigolo init --agents=claude-code,cursor,codex
```

`init` 是 unattended by default，**不弹 prompt**，CI / 脚本场景安全。它会做四件事：

1. 下载 browser engine
2. 下载 on-device models
3. 跑 health check
4. 打印每个组件的状态 summary

任何一步失败都不会让 `init` 整体 fail——它会打印哪个组件没 ready + 修复方法 + 仍然把 agent 端 MCP config 配好。这是 public beta 阶段最重要的体验设计：用户拿到的是"当前可用的工具"而不是"全失败"。

### 2. 浏览器引擎本地化

抓取真实网页的痛点是"被反爬、被 JavaScript 渲染"。wigolo 直接下载一个浏览器引擎（基于 Chromium 内核）到本地，所有 fetch / crawl 调用都跑在本地引擎里，避免云端被封 IP、避免云端被计费。这和"调用 Bright Data / ScraperAPI / SerpAPI"的 SaaS 路径完全相反——所有数据都不出 `~/.wigolo/`。

### 3. on-device models

提取 / 摘要 / query 改写都用本地小模型（on-device models）。这些模型体积小、推理快、专门为 web extraction 训练过。这意味着 wigolo 在"用户没填 API key"时仍然能产出结构化结果，而不是返回"原始 HTML 让 agent 自己解析"。

### 4. `research` / `agent` 的 keyless 退化

README 给出的细节：

> `research`, `agent`, and `search format=answer` use an LLM to *write* the synthesized, cited answer — without one they hand back a raw brief and evidence for your agent to assemble.

没 key 时，`research` 退化成"返回 brief + 证据列表"，由 agent 自己组装。这是个聪明的降级设计——**没 key 不是 fail，而是减功能**。用户可以一边用一边慢慢申请 key，体验不会断。

### 5. 隐私边界

> Nothing it touches leaves `~/.wigolo/`

所有数据——抓到的网页、提取的结果、缓存的 query——全部留在本地磁盘。这对企业用户（数据合规）和隐私敏感用户（不想让第三方看到搜索历史）都是决定性优势。

## 适用人群

- **个人 / 小团队 agent 开发者**：不想为每次 web query 付 SerpAPI 费用的人
- **企业用户**：web 数据合规要求"数据不出本地"的人
- **多 agent 用户**：Claude Code / Cursor / Codex 混着用的人，需要统一的 web 智能层
- **隐私敏感用户**：不想让自己的搜索历史被任何云端索引

## 不适合谁

- **需要超大规模并发 web query 的人**：本地 browser engine 的吞吐受单机资源限制
- **想要成熟 SLA / 商用支持的人**：wigolo 是 public beta，团队规模 1.7K stars
- **只能接受 HTTP API（不愿跑 MCP server）的人**：wigolo 同时提供 REST，但它的 MCP-first 设计意味着 REST 是次级接口

## 仓库地址

https://github.com/KnockOutEZ/wigolo

## 阅读路径建议

1. `npx wigolo init --agents=claude-code`，5 分钟接入
2. 在 Claude Code 里问 "search for the latest React 19 release notes"，看返回
3. `npx wigolo doctor` 检查每个组件是否 ready
4. 读 docs/configuration.md，理解怎么切到 Ollama 做 100% keyless