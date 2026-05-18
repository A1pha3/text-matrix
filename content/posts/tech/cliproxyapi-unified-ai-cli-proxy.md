---
title: "CLIProxyAPI：用一个代理把 Gemini CLI / Claude Code / Codex / Grok 变成统一 API 服务"
date: "2026-05-18T08:37:46+08:00"
slug: "cliproxyapi-unified-ai-cli-proxy"
description: "CLIProxyAPI 是一个用 Go 语言编写的开源代理服务器，通过暴露 OpenAI/Gemini/Claude/Codex/Grok 兼容接口，让 Claude Code、Gemini CLI、OpenAI Codex 等编程工具在没有官方 API 的情况下，通过 OAuth 认证直接调用订阅账户，算上生态项目已积累 33K GitHub Stars。"
draft: false
categories: ["技术笔记"]
tags: ["AI编程工具", "Claude Code", "Gemini CLI", "OpenAI Codex", "API代理", "Go"]
---

## 开场判断

CLIProxyAPI 解决的不是"调用哪个模型"的问题，而是**"没有 API Key 怎么调用模型服务"**的问题。

主流 AI 编程工具（Claude Code、Gemini CLI、OpenAI Codex、Grok Build）的付费模式都是月度订阅，而不是按 Token 计费。官方不提供可编程访问的 API，只提供本地 CLI 工具。如果你是一个桌面应用或 IDE 插件的开发者，想在产品里集成 Claude Code 的能力，你会发现官方只给了 CLI，没有给你留任何 HTTP 接口。

CLIProxyAPI 的做法是：把本地 CLI 工具的认证和请求流程**逆向成一组标准的 HTTP API 端点**，让任何 OpenAI 兼容客户端都能调用这些订阅服务。目前已支持 **OpenAI、Gemini、Claude、Codex、Grok** 五大后端，算上第三方生态项目（vibeproxy、Quotio、CodMate 等）已有 **33K+ Stars**。

---

## 系统地图

```
┌─────────────────────────────────────────────────────────────┐
│                      客户端（OpenAI 兼容）                   │
│   Cursor / Cline / VS Code / 桌面应用 / 任意 HTTP 客户端     │
└─────────────────────┬───────────────────────────────────────┘
                      │ OpenAI/Gemini/Claude 兼容格式
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   CLIProxyAPI（Go 代理）                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  OpenAI  │  │  Gemini  │  │  Claude  │  │   Grok  │       │
│  │  适配层  │  │  适配层  │  │  适配层  │  │  适配层  │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       └────────────┴──────────────┴──────────────┘           │
│                         │                                      │
│  ┌──────────────────────┴──────────────────────┐              │
│  │              认证与请求转发层                  │              │
│  │  OAuth 登录 / API Key / 负载均衡 / 多账户轮询   │              │
│  └──────────────────────┬──────────────────────┘              │
└─────────────────────────┼───────────────────────────────────────┘
                          │ 本地进程或网络
                          ▼
              ┌─────────────────────┐
              │  Gemini CLI          │
              │  Claude Code         │
              │  OpenAI Codex        │
              │  Grok Build          │
              └─────────────────────┘
              （运行在用户本机的 CLI 工具）
```

**两条并行主线在这里必须先拆开**：一条是"请求如何进来"（外部 HTTP 请求进入代理），另一条是"请求如何出去"（代理调用本地 CLI 工具）。这两条路径通过适配层连接，但遵循完全不同的协议和数据格式。

---

## 核心机制拆解

### 1. 兼容层：把各家协议统一成 OpenAI 格式

每个后端（Gemin i、Claude、Codex、Grok）有自己的请求和响应格式。CLIProxyAPI 在进入层做协议转换，把来自客户端的 OpenAI 兼容请求翻译成目标 CLI 工具能理解的方式。

以 `/v1/chat/completions` 端点为例，代理收到一个标准的 OpenAI 格式请求后，会根据请求里的 `model` 字段或请求路径里的 provider 前缀，路由到对应的适配层。适配层负责把 OpenAI 的消息格式转成目标后端的格式，并且把响应再转回 OpenAI 兼容的格式返回给客户端。

这个转换是双向的：请求出去要翻译一次，响应回来再翻译一次。

### 2. OAuth 认证：没有 API Key 怎么认证

这是 CLIProxyAPI 区别于普通代理的关键。大多数 API 代理用的是 API Key 认证，但 AI 编程工具的官方渠道（Claude Code、Codex、Grok Build）**只支持 OAuth 登录**，不提供纯 API Key 访问方式。

CLIProxyAPI 内置了一个 OAuth 认证流程管理模块。当用户首次使用某个后端时，代理会启动一个本地 HTTP 服务器，接收 OAuth 回调，然后换取并持久化 access token 和 refresh token。之后每次请求，代理就用这些 token 代表用户身份去调用对应的 CLI 工具。

```
用户首次请求 → 代理返回 401 + OAuth URL → 用户浏览器授权 → 
回调到本地代理服务器 → 代理存储 token → 重试原请求
```

这个流程对客户端是透明的——客户端以为自己调的是一个普通的 API，根本不知道背后发生了 OAuth 跳转。

### 3. 多账户轮询负载均衡

一个 CLI 工具的账户有速率限制（比如 Codex 有 5 小时配额窗口）。如果只有一个账户，高频使用时很快会遇到限速。

CLIProxyAPI 支持配置多个账户，代理会按轮询（round-robin）策略分配请求。当某个账户的配额用尽时，代理会自动切换到下一个可用账户。用户不需要在客户端做任何配置，客户端仍然只看到一个 API 端点。

这个机制对于**共享团队订阅**或**个人多账户管理**场景特别有价值。

### 4. 流式响应与 WebSocket

部分后端和操作模式支持流式响应（Server-Sent Events）。CLIProxyAPI 能把 CLI 工具的流式输出透传给客户端，保持端到端的流式体验。对于需要实时看到 AI 思考过程的应用（比如一个交互式 IDE 插件），这是必要的支持。

### 5. 函数调用（Tools）支持

Claude Code 和部分模型支持 function calling / tools。CLIProxyAPI 在适配层处理了工具调用的请求和响应转换，使得客户端可以用标准的 OpenAI Tools 格式来调用 CLI 工具的能力。

---

## 一次请求的任务流

以一个具体场景为例：**在 Cursor 中用 Codex（GPT 模型）回答代码问题**。

1. 用户在 Cursor 中提问，Cursor 发送一个 POST 请求到 `http://localhost:3000/v1/chat/completions`，请求体是标准的 OpenAI 格式。
2. CLIProxyAPI 根据请求中的 model 字段识别出这是 Codex 后端，将请求路由到 Codex 适配层。
3. Codex 适配层把 OpenAI 格式转成 Codex 能理解的消息格式，通过本地进程调用 `codex` CLI。
4. 如果这是首次使用，OAuth 模块触发认证流程（浏览器弹窗 → 用户授权 → token 存储）。
5. Codex CLI 执行请求，输出流式响应。
6. 适配层将响应转回 OpenAI 格式，通过同一个 HTTP 连接返回给 Cursor。
7. Cursor 收到标准 OpenAI 格式响应，渲染给用户。

整个过程里，Cursor 以为自己调的是 OpenAI API，实际上调的是本地运行的 Codex CLI。

---

## 适用边界

**适合的场景：**
- 桌面应用或 IDE 插件想集成 AI 编程能力，但不想自己对接各家 API
- 团队共享一个 Claude Code / Codex 订阅，需要多人并发使用
- 想在一个统一端点下路由到多个 AI 后端，用冗余提升可用性
- 已有的 OpenAI 兼容客户端想切换到其他 AI 服务，但不想改代码

**不适合的场景：**
- 需要官方 API Key 计费模式的使用方式（那是另一套使用路径）
- 追求极低延迟的实时交互（代理多了一层转换）
- 不想在本地运行额外服务的用户

---

## 生态与周边

CLIProxyAPI 催生了一个可观的周边生态。项目 README 列出了数十个基于它构建的第三方应用：

| 应用 | 平台 | 说明 |
|------|------|------|
| [vibeproxy](https://github.com/automazeio/vibeproxy) | macOS 菜单栏 | 用现有订阅直接驱动 AI 编程工具 |
| [Quotio](https://github.com/nguyenphutrong/quotio) | macOS 菜单栏 | 实时配额追踪 + 自动故障转移 |
| [CodMate](https://github.com/loocor/CodMate) | macOS SwiftUI | 统一管理多 CLI 会话 + Git 审查 |
| [ZeroLimit](https://github.com/0xtbug/zero-limit) | Windows Tauri | 配额监控 + 系统托盘 |
| [ProxyPilot](https://github.com/Finesssee/ProxyPilot) | Windows TUI | TUI 界面 + 多 provider OAuth |
| [霖君](https://github.com/wangdabaoqq/LinJun) | 跨平台桌面 | 统一管理多种 CLI 工具的跨平台应用 |

这些周边项目覆盖了 macOS/Windows/Linux 三大平台，从菜单栏小工具到完整桌面应用，形成了以 CLIProxyAPI 为后端的应用矩阵。

---

## 采用建议

如果你的产品需要集成 AI 编程能力，建议按以下顺序评估：

1. **先看官方方案**：Anthropic 的 API（需要单独申请）、OpenAI 的 API、各家官方 SDK。
2. **再看 CLIProxyAPI**：当你需要的是 CLI 工具的原生体验，又想让桌面应用通过 HTTP 接口调用它。
3. **最后看周边生态**：如果现有周边应用（vibeproxy、Quotio 等）已经满足你的需求，直接用这些现成产品会更省事。

CLIProxyAPI 的本质是**协议适配层 + 认证代理**，而不是一个新的 AI 服务。它的价值在于打通现有封闭生态，让订阅制服务的使用方式从"只能本地用 CLI"扩展到"任意客户端都能调用"。