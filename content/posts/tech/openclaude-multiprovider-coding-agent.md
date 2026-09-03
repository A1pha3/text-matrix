---
title: "OpenClaude：一个终端吃遍云端与本地大模型的编程智能体"
date: 2026-09-04T03:27:35+08:00
slug: "openclaude-multiprovider-coding-agent"
github_repo: "Gitlawb/openclaude"
source_key: "gh:Gitlawb/openclaude"
description: "OpenClaude 是开源的编程智能体 CLI，把 OpenAI 兼容 API、Gemini、Ollama、Codex 等十余类模型后端统一进一个终端工作流，内置 bash、文件、MCP、子智能体与 slash 命令，还带一个会射箭的像素伙伴。本文拆解其定位、支持的后端矩阵与快速上手路径。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "CLI", "LLM", "MCP", "开源"]
---

## 核心判断

编程智能体（coding agent）市场正在分裂成两派：绑死单一模型提供方的官方 CLI，和只认某一家云平台的商业化工具。OpenClaude 选择站在这两派的中间——它保留 Claude Code 风格的一体化终端工作流，却把模型后端抽象成可插拔层：OpenAI 兼容 API、Gemini、GitHub Models、Codex、Ollama、Atomic Chat 等都能接进来，用同一套 prompt、工具、agent、MCP 与流式输出。对同时跑云端模型和本地模型的人来说，这省掉的不是配置，而是心智负担。

截至本文写作时，项目 v0.30.0（2026-08-31 发布），GitHub 32.3k stars，TypeScript 实现，MIT 许可。它由 Claude Code 代码库衍生而来，做了大量多后端改造。

## 系统定位

OpenClaude 不是又一个聊天套壳，它把"终端优先"作为默认姿势：

- **一套工作流，多后端**：bash、文件读写、grep、glob、agents、tasks、MCP、slash 命令、流式输出，全部与具体模型解耦
- **引导式配置**：`/provider` 提供逐步设置与已保存的 profile；`/onboard-github` 专门做 GitHub Models 引导
- **会话管理**：`--resume` 按会话 ID 续聊，`--continue` 接续当前目录最近会话，`--fork-session` 分支对话历史
- **后台会话**：`--bg` 把长任务从终端剥离，`openclaude ps / logs / kill` 管理，不启动 daemon、不开网络服务

## 后端矩阵：支持什么

| 后端 | 接入方式 | 备注 |
|---|---|---|
| OpenAI 兼容 | `/provider` 或环境变量 | OpenRouter、DeepSeek、Groq、Mistral、LM Studio 等 `/v1` 服务 |
| Z.AI GLM Coding Plan | `/provider` | 默认 `glm-5.2`，可选视觉版 `glm-5.3-flash` |
| Gemini | `/provider` | 仅 API key |
| GitHub Models | `/onboard-github` | 交互式引导 |
| Codex OAuth / Codex | `/provider` | ChatGPT 登录或复用 Codex CLI 认证 |
| Ollama | 环境变量 | 本地推理，无需 API key |
| Atomic Chat | `/provider` | 本地模型提供方，自动探测已加载模型 |
| Bedrock / Vertex / Foundry | 环境变量 | Anthropic 系云端路由 |
| Cloudflare Workers AI | `/provider` | OpenAI 兼容的 CF 端点 |

一个值得注意的默认：Ollama 接入时，OpenClaude 会在每次请求上要求 32768 token 的上下文窗口，避免同一会话历史被 Ollama 的兼容层静默截断。

## 快速上手

环境要求：Node.js ≥ 22.0.0。

```bash
npm install -g @gitlawb/openclaude@latest
```

若后续报 `ripgrep not found`，系统装好 ripgrep 并确认 `rg --version` 可用即可。

最快的 OpenAI 兼容接入：

```bash
export CLAUDE_CODE_USE_OPENAI=1
export OPENAI_API_KEY=sk-your-key-here
export OPENAI_MODEL=gpt-4o
openclaude
```

最快的本地 Ollama 接入：

```bash
export CLAUDE_CODE_USE_OPENAI=1
export OPENAI_BASE_URL=http://localhost:11434/v1
export OPENAI_MODEL=qwen2.5-coder:7b
openclaude
```

进终端后，`/provider` 做引导式配置并保存 profile；`/onboard-github` 走 GitHub Models 引导。

## 几个值得注意的设计点

- **不自动加载 `.env`**：OpenClaude 不读取项目 `.env`，凭据推荐走 `/provider` 存进 `.openclaude-profile.json`；要环境变量就显式导出，或 `openclaude --provider-env-file .env`
- **独立配置目录**：配置在 `~/.openclaude`，不读 `~/.claude`，迁移需手动精选，严禁整目录拷贝
- **WebSearch 默认走 DuckDuckGo**：非 Anthropic 模型默认免费搜网；要更可靠可配 Firecrawl（免费档 500 credits）
- **repo map（代码库感知）**：`REPO_MAP` 开启时，按 PageRank 排序的结构化仓库地图自动注入上下文，`/repomap` 查看
- **伙伴系统**：`/buddy` 孵化一个像素伙伴，按 Enter 时放技能（箭、能量波、冲击拳等），尊重 `prefersReducedMotion`——这是产品气质的一部分，不是功能列表的凑数

## 适用边界

- **模型行为不完全一致**：Anthropic 专属能力在其他提供方上可能缺失；小模型在长多步工具循环里可能吃力；部分提供方输出上限低于 CLI 默认值
- **工具质量取决于模型**：tool calling 弱的模型会拖慢整体体验
- **后台会话是本地子进程**：`openclaude attach` 目前只报告会话并指向 `logs -f`，完整终端重挂载尚未实现

## 结论

OpenClaude 的价值不在某一家模型的 API 封装，而在"一套工作流 + 可插拔后端"这件事本身。对要在云端 API 和本地模型之间来回切换的开发者，它是把多套 CLI 的心智成本压缩成一处的务实选项；对想完全自托管、不依赖厂商工具的团队，MIT 许可和可扩展后端也留足了改造空间。它最不合适的场景是"只信一家云、完全不需要本地模型"——那直接用官方工具更省事。
