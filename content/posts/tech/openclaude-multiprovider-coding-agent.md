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

编程智能体（coding agent）市场正分成两派：绑死单一模型提供方的官方 CLI，和只认某一家云平台的商业化工具。OpenClaude 站在两派中间——它保留 Claude Code 风格的一体化终端工作流，却把模型后端做成可插拔层：OpenAI 兼容 API、Gemini、GitHub Models、Codex、Ollama、Atomic Chat 等都能接进来，共用同一套 prompt、工具、agent、MCP 与流式输出。对同时跑云端模型和本地模型的人，省下的是反复切换 CLI、重学命令的心智成本。

截至本文写作时，项目 v0.30.0（2026-08-31 发布），GitHub 32.5k stars，TypeScript 实现。代码由 Claude Code 衍生而来，多后端改造后以 MIT 许可对外发布（衍生部分归属 Anthropic）。

## 系统定位

OpenClaude 的默认姿势是终端优先，全部能力与具体模型解耦：

- **一套工作流，多后端**：bash、文件读写、grep、glob、agents、tasks、MCP、slash 命令、流式输出，不绑定任何模型
- **引导式配置**：`/provider` 做逐步设置并保存 profile；`/onboard-github` 专门处理 GitHub Models 引导
- **会话管理**：`--resume <session-id>` 按 ID 续聊，`--continue` 接续当前目录最近会话，`--fork-session` 把历史分支成新会话
- **后台会话**：`--bg` 把长任务从终端剥离，`openclaude ps / logs / kill` 管理，不启动 daemon、不开网络服务

## 后端矩阵：支持什么

| 后端 | 接入方式 | 备注 |
|---|---|---|
| OpenAI 兼容 | `/provider` 或环境变量 | OpenRouter、DeepSeek、Groq、Mistral、LM Studio 等 `/v1` 服务 |
| Z.AI GLM Coding Plan | `/provider` | 默认 `glm-5.2`，可选视觉版 `glm-5.3-flash` |
| Gemini | `/provider` | 仅 API key |
| GitHub Models | `/onboard-github` | 交互式引导 |
| Codex OAuth / Codex | `/provider` | ChatGPT 登录或复用 Codex CLI 认证 |
| Ollama | `/provider` 或环境变量 | 本地推理，无需 API key |
| Atomic Chat | `/provider` | 本地模型提供方，自动探测已加载模型 |
| Bedrock / Vertex / Foundry | 环境变量 | Anthropic 系云端路由；Vertex 仅指 Claude on Vertex AI |
| Cloudflare Workers AI | `/provider` | OpenAI 兼容的 CF 端点，用账号 token 认证 |
| Fireworks AI | `/provider` | 276 个精选模型，走 `FIREWORKS_API_KEY` |
| Xiaomi MiMo | `/provider` | 默认 `mimo-v2.5-pro`，走 `MIMO_API_KEY` |
| NEAR AI | `/provider` | 统一网关（Claude、GPT、Gemini + 开放模型），走 `NEARAI_API_KEY` |
| OpenCode Zen / Go | `/provider` | 按量付费（48 模型）或订阅制（13 模型），共用一把 key |

表格之外还有一层"按需接的网关"：Gitlawb Opengateway（新装默认）、Hicap、OpenCode Zen 之外的 AI/ML API、Concentrate、LLMTR、ApiSmart、LongCat、ClinePass 等，都以 OpenAI 兼容协议接入，配置方式相同。需要哪一个就在 `/provider` 里选，不必记各自的 SDK。

一个值得注意的默认：Ollama 接入时，OpenClaude 在每次请求上要求 32768 token 的上下文窗口，避免同一会话历史被 Ollama 的兼容层静默截断；需要其他尺寸可设 `OLLAMA_CONTEXT_LENGTH`。

## 一次任务如何流过 OpenClaude

把"前端跑云端模型、本地模型兜底"的常见工作流串一遍，能看清各部分如何配合。

1. **保存云端 profile**：首次进入后运行 `/provider`，按引导选 OpenAI 兼容并填入 key，凭据存入用户级 profile。下次直接以该 profile 启动。
2. **前台交互**：让云端模型做代码库梳理、写实现。中途要换上下文，`--continue` 接续当前目录最近会话；想试验另一条思路不污染主线，`--fork-session` 分支一份历史。
3. **切本地模型**：需要离线、省钱或处理敏感代码时，启动时用环境变量指向 Ollama（`OPENAI_BASE_URL=http://localhost:11434/v1`），同一套工作流继续用。
4. **长任务下放后台**：编译、批量重构这类跑得久的任务用 `openclaude --bg "refactor auth middleware"` 剥离终端；`openclaude ps` 看状态，`openclaude logs <name> -f` 跟输出，`openclaude kill <name>` 停止。

这条路径里每一步都只是"换后端、换会话、换执行位置"，命令和工具不变——这正是 OpenClaude 与"每换一家模型就重学一套 CLI"的区别所在。

## 快速上手

环境要求：Node.js ≥ 22.0.0。

```bash
npm install -g @gitlawb/openclaude@latest
```

Arch Linux 用户可走 AUR 包：

```bash
paru -S openclaude
```

若后续报 `ripgrep not found`，系统装好 ripgrep 并确认 `rg --version` 在同一终端可用即可。

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

进终端后，`/provider` 做引导式配置并保存 profile；`/onboard-github` 走 GitHub Models 引导。装完先用 `openclaude --version` 确认版本，再开始干活。

## 几个值得注意的设计点

- **不自动加载 `.env`**：OpenClaude 不读项目 `.env`，凭据推荐走 `/provider` 存进 profile；要环境变量就显式导出，或 `openclaude --provider-env-file .env`
- **独立配置目录**：配置在 `~/.openclaude`，不读 `~/.claude`，迁移需手动精选，严禁整目录拷贝
- **WebSearch 默认走 DuckDuckGo**：非 Anthropic 模型默认免费搜网；DuckDuckGo 是抓取搜索结果实现，可能被限流，要更可靠可配 Firecrawl（免费档 500 credits），Firecrawl 同时接管 WebFetch 的 JS 渲染抓取
- **repo map（代码库感知）**：`REPO_MAP` 开启时，按 PageRank 排序的结构化仓库地图自动注入上下文，默认 2048 token，`/repomap` 查看
- **按 agent 路由模型**：可在 `~/.openclaude.json` 配置 `agentRouting`，让不同子智能体（如 Explore）走不同模型，用于成本优化或按任务强度分配
- **伙伴系统**：`/buddy` 孵化一个像素伙伴，按 Enter 时放技能（箭、能量波、冲击拳等），尊重 `prefersReducedMotion`——这是产品气质的一部分，不是功能列表的凑数

## 适用边界

- **模型行为不完全一致**：Anthropic 专属能力在其他提供方上可能缺失；小模型在长多步工具循环里可能吃力；部分提供方输出上限低于 CLI 默认值
- **工具质量取决于模型**：tool calling 弱的模型会拖慢整体体验
- **后台会话是本地子进程**：`openclaude attach` 目前只报告会话并指向 `logs -f`，完整终端重挂载尚未实现
- **代码由 Claude Code 衍生**：若你的团队对 Anthropic 授权条款敏感，需先过一遍 LICENSE 再采用

## 结论

OpenClaude 的价值不在某一家模型的 API 封装，而在"一套工作流 + 可插拔后端"本身。对要在云端 API 和本地模型之间来回切换的开发者，它把多套 CLI 的心智成本压缩成一处，是务实的选项；对想完全自托管、不依赖厂商工具的团队，MIT 许可和可扩展后端也留足了改造空间。

采用顺序建议：先单接一个 OpenAI 兼容后端跑通日常，再加 Ollama 做本地兜底，随后按需补 `/provider` 里的其他后端——一步只引入一个变量，出问题时容易定位。最不合适的场景是"只信一家云、完全不需要本地模型"——那直接用官方工具更省事。
