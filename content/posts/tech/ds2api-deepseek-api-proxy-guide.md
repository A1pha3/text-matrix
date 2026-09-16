---
title: "DS2API：为 DeepSeek Web 对话装上 OpenAI/Claude/Gemini 兼容接口"
slug: "ds2api-deepseek-api-proxy-guide"
github_repo: "CJackHwang/ds2api"
source_key: "gh:CJackHwang/ds2api"
description: "DS2API 是一个以 Go 实现的协议适配中间件，把 DeepSeek Web 对话能力转成 OpenAI、Claude、Gemini 甚至 Ollama 兼容的 HTTP 接口。用邮箱/手机号登录托管账号、自动刷新 token，支持多账号轮询与并发队列，可部署到 Docker、Vercel、Zeabur 或本机。"
date: "2026-04-28T11:35:00+08:00"
categories: ["技术笔记"]
tags: ["DeepSeek", "API代理", "OpenAI兼容", "Go", "模型代理"]
hiddenFromHomePage: false
draft: false
---

# DS2API：为 DeepSeek Web 对话装上 OpenAI/Claude/Gemini 兼容接口

> **项目信息**
>
> - **GitHub**: [CJackHwang/ds2api](https://github.com/CJackHwang/ds2api)（仓库已归档，本数据以 GitHub API 2026-09-16 核验）
> - **Stars**: 4,755 | **Forks**: 1,632 | **License**: AGPL-3.0
> - **语言**: Go（Vercel 流式桥接使用少量 Node Runtime）| **前端**: React WebUI 管理台
> - **状态**: 仓库于 2026-05-10 停止推送后归档，仅作参考实现
> - **部署**: 本地 / Docker / Vercel / Zeabur / Linux systemd

## 一句话判断

DS2API 解决的不是"调用 DeepSeek"——这件事 DeepSeek 自己的 API 就能做。它解决的是：**让已经写好的 OpenAI/Claude/Gemini SDK 代码，不改一行就能跑在 DeepSeek Web 后端上**。仓库定位是技术探索项目，最后推送到 2026-05-10 后被归档，适合当参考实现，不适合作为新的生产依赖。

## 架构总览

```mermaid
flowchart LR
    Client["客户端 / SDK<br/>(OpenAI / Claude / Gemini / Ollama)"]
    Router["chi Router + 中间件<br/>(RequestID / RealIP / Logger / Recoverer / CORS)"]
    HTTP["HTTP API Surface<br/>OpenAI /v1/* · Claude /anthropic/*<br/>Gemini /v1beta/models/* · Ollama /api/*<br/>Admin /admin · Health /healthz /readyz"]
    Compat["PromptCompat<br/>(厂商消息 → 网页纯文本上下文)"]
    Runtime["Completion Runtime<br/>(Session / PoW / Completion)"]
    Turn["AssistantTurn<br/>(输出语义归一)"]
    Auth["Auth Resolver<br/>(api key / bearer / x-goog-api-key)"]
    Pool["Account Pool + Queue<br/>(并发槽位 + 等待队列)"]
    DSClient["DeepSeek Client<br/>(Session / Auth / Completion / Files)"]
    Pow["PoW 实现<br/>(DeepSeekHashV1, 纯 Go)"]
    Tool["Tool Sieve<br/>(工具调用解析 + 防泄漏)"]
    Upstream["DeepSeek Web API"]

    Client --> Router --> HTTP
    HTTP --> Compat --> Runtime
    Runtime --> Turn --> Client
    Runtime --> Auth --> DSClient --> Upstream
    Runtime --> Pool
    Runtime --> Tool
    Runtime --> Pow
```

架构里两条容易混淆的边界：

- **PromptCompat 和 DeepSeek Client 是两层不同的东西**。PromptCompat 只管把各厂商的消息格式翻译成 DeepSeek Web 能处理的纯文本上下文；DeepSeek Client 管的是与 DeepSeek Web 的实际通信——Session 维护、Auth、PoW 计算、文件上传。
- **Account Pool + Queue 是夹在中间的一层调度器**。每个账号有独立的 in-flight 上限，超出上限的请求排队等待，不是简单轮询。

## 兼容的接口面

DS2API 对外暴露的不止一个协议，而是一套分立的 HTTP surface，统一走同一个 chi Router：

| 协议 | 主要路径 | 说明 |
|------|----------|------|
| **OpenAI** | `/v1/chat/completions`、`/v1/responses` | 单次请求主路径；另暴露 `/v1/models`、`/v1/embeddings`、`/v1/files` |
| **Claude** | `/anthropic/v1/messages`（及快捷路径 `/v1/messages`） | 面向 Anthropic SDK |
| **Gemini** | `/v1beta/models/{model}:generateContent`、`:streamGenerateContent` | 面向 Google SDK |
| **Ollama** | `/api/version`、`/api/tags`、`/api/show` | 轻量兼容层 |
| **Admin** | `/admin` | React WebUI 管理台，静态托管 |
| **探针** | `/healthz`、`/readyz` | 存活 / 就绪探测，便于容器编排 |

`/v1/*` 是推荐的规范路径；同时提供 `/models`、`/chat/completions`、`/embeddings` 等根路径快捷别名，方便只配置了 DS2API 根地址的第三方客户端。

## 问题拆解：DeepSeek Web 与 SDK 之间缺了什么

DeepSeek 给了两条访问路径：Web 界面和官方 API。官方 API 要申请、有调用配额；Web 对话功能完整，但只能通过浏览器用，没法被 OpenAI SDK 或 Anthropic SDK 调用。两个协议之间隔着四层差距：

| 差距 | 说明 |
|------|------|
| **消息格式** | OpenAI 的 `{role, content}` 结构 vs DeepSeek Web 的纯文本上下文 |
| **认证机制** | SDK 用 `api_key` header vs DeepSeek Web 用登录凭据 + token |
| **会话管理** | SDK 无状态 vs DeepSeek Web 需要维护 Session、定时刷新 token |
| **安全校验** | DeepSeek Web 要求 PoW（工作量证明），SDK 不会做 |

DS2API 做的事，就是在这些差距之间填一层翻译层。后端用 Go 全量实现，不依赖 Python 运行时；前端管理台用 React 构建，以静态文件托管在 `/admin` 路径。

## 一次请求走过系统

用一个具体场景把抽象模块串起来。假设用 Python 写了这段代码：

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-key-in-config",
    base_url="http://localhost:5001/v1"
)

response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[
        {"role": "system", "content": "你是技术助手"},
        {"role": "user", "content": "解释一下什么是 PoW"}
    ]
)
```

这段代码发出的 HTTP 请求在 DS2API 内部会经历以下步骤：

1. **chi Router 接入** — 请求到达 `/v1/chat/completions`，经过 RequestID、RealIP、Logger、Recoverer、CORS 中间件。
2. **Auth Resolver 校验身份** — 判断 `api_key` 是否在 `config.keys` 里，决定走托管账号模式还是直通 token 模式。
3. **PromptCompat 翻译消息格式** — `{role, content}` 结构被转成 DeepSeek Web 能处理的纯文本上下文。system 消息作为 prompt 前缀注入，user 消息作为对话内容。
4. **Account Pool 选账号** — 从账号池中选一个当前 in-flight 未达上限的账号。
5. **DeepSeek Client 发起对话** — 用该账号的登录态向 DeepSeek Web 发起请求。如果 Web 端返回 PoW 挑战，毫秒级 Go 实现完成计算后重试。
6. **响应回译** — Web 端返回的内容被重新包装成 OpenAI 兼容的 `ChatCompletion` 格式，流式输出通过 SSE 逐块返回。

整个过程对调用方透明——SDK 代码感知不到中间经过了协议翻译。

## 核心模块

| 模块 | 职责 |
|------|------|
| `PromptCompat` | 厂商消息格式 → DeepSeek Web 纯文本上下文的双向翻译 |
| `Completion Runtime` | 一次对话的完整生命周期：Session、PoW、Completion |
| `AssistantTurn` | 输出语义归一，把网页返回整理成稳定的接口形态 |
| `Auth Resolver` | 解析 api key / bearer / x-goog-api-key 三种凭据 |
| `Account Pool + Queue` | 多账号轮询调度，每账号独立 in-flight 上限和等待队列 |
| `DeepSeek Client` | 向 DeepSeek Web 发起对话：Session、Auth、Completion、文件上传 |
| `PoW` | DeepSeekHashV1 工作量证明的 Go 实现，毫秒级完成 |
| `Tool Sieve` | 工具调用解析和防泄漏处理 |

PoW 和 Tool Sieve 是两个容易混淆的模块：PoW 解决的是"DeepSeek 让不让你发消息"的问题，Tool Sieve 解决的是"模型输出里哪些是工具调用"的问题。两者在请求链上是先后关系，不是替代关系。

## 模型支持与别名映射

模型被分成 `default` / `expert` / `vision` 三类，`/v1/models` 返回规范化后的 DeepSeek 原生模型 ID：

| 模型类型 | 模型 ID | thinking | search |
|----------|---------|----------|--------|
| default | `deepseek-v4-flash` | 默认开启，可由请求参数控制 | ❌ |
| default | `deepseek-v4-flash-nothinking` | 永久关闭 | ❌ |
| expert | `deepseek-v4-pro` | 默认开启，可由请求参数控制 | ❌ |
| expert | `deepseek-v4-pro-nothinking` | 永久关闭 | ❌ |
| default | `deepseek-v4-flash-search` | 默认开启 | ✅ |
| expert | `deepseek-v4-pro-search` | 默认开启 | ✅ |
| vision | `deepseek-v4-vision` | 默认开启 | ❌ |

- `-nothinking` 后缀显式关闭思考；`-search` 后缀开启联网搜索。
- 调用时也接受常见 alias（`gpt-4.1`、`gpt-5`、`o3`、`claude-*`、`gemini-*`），会被映射到对应原生模型；alias 带 `-nothinking` 时同样映射到强制关闭思考的模型。
- 上游视觉模型只暴露 `vision` 通道，不提供独立的视觉搜索变体——这也解释了为什么 Vision 能力有限。
- 别名到原生模型的映射可在 `config.json` 的 `model_aliases` 里覆盖。

Claude 侧的常见映射（可在 `model_aliases` 覆盖）：

| 客户端模型 | 映射到 DeepSeek |
|------------|-----------------|
| `claude-sonnet-4-6` | `deepseek-v4-flash` |
| `claude-haiku-4-5` | `deepseek-v4-flash` |
| `claude-opus-4-6` | `deepseek-v4-pro` |

## 认证与多账号

这是最容易踩坑的地方。DS2API 的鉴权分两层，别和 DeepSeek 账号搞混：

**第一层：调用方怎么证明身份。** 三种方式任选其一：`Authorization: Bearer <token>`、`x-api-key: <token>`、Gemini 的 `x-goog-api-key`（或 `?key=` / `?api_key=` 查询参数）。token 命中 `config.keys` → **托管账号模式**，自动在账号池里轮询；token 不命中 → **直通 token 模式**，直接作为 DeepSeek token 使用。

**第二层：用哪个 DeepSeek 账号去兜底。** 在 `config.accounts` 里填 DeepSeek 的邮箱/手机号 + 密码：

```json
{
  "accounts": [
    { "name": "主账号", "email": "you@example.com", "password": "your-password-1" },
    { "name": "备用账号", "mobile": "12345678901", "password": "your-password-2" }
  ]
}
```

DS2API 用这些凭据自动登录并定时刷新 token，不需要手动去网页复制 Cookie。几个细节值得记住：

- **指定目标账号**：可选请求头 `X-Ds2-Target-Account`（值为 email 或 mobile）强制走某个账号；账号不存在或队列已满时返回 429。
- **容错切换**：若某个账号因上游 thinking-only 空输出等原因报 429，托管账号模式会切到下一个可用账号重试一次。
- **并发模型**：`DS2API_ACCOUNT_MAX_INFLIGHT` 控制单账号并发（默认 2），超出进入等待队列而非立即拒绝；总承载（in-flight + 队列）大致是"账号数 × 4"，再超才返回 `429`。Admin UI 会根据历史请求给出建议并发值。

## 部署

推荐按顺序选：Release 构建包 > Docker > Vercel/Zeabur，源码编译留给要改代码的人。所有部署方式的通用第一步都是准备配置：

```bash
cp config.example.json config.json
# 编辑 config.json：填 keys 和 accounts
```

### 方式一：Release 构建包

每次 Release 时 GitHub Actions 会自动构建多平台二进制包（linux/darwin/windows 的 amd64/arm64 等）。从 [Release 页面](https://github.com/CJackHwang/ds2api/releases) 下载：

```bash
tar -xzf ds2api_<tag>_linux_amd64.tar.gz
cd ds2api_<tag>_linux_amd64
cp config.example.json config.json
./ds2api
```

默认监听 `PORT`（`.env` 里默认 5001），走 `config.json` 配置。

### 方式二：Docker

仓库提供 `docker-compose.yml`，默认把宿主机 `6011` 映射到容器内 `5001`：

```bash
cp .env.example .env
cp config.example.json config.json
# 编辑 .env，至少设置 DS2API_ADMIN_KEY
docker-compose up -d
```

`config.json` 会被挂载到容器 `/data/config.json`，并设置 `DS2API_CONFIG_PATH=/data/config.json`，避免 `/app` 只读导致运行时 token 持久化失败。想直接暴露 5001，设 `DS2API_HOST_PORT=5001`。更新镜像用 `docker-compose up -d --build`。镜像也会推送到 GHCR（`ghcr.io/cjackhwang/ds2api`）。

### 方式三：Vercel

Fork 仓库后在 Vercel 导入，先只填 `DS2API_ADMIN_KEY`，部署后在 `/admin` 导入配置，或用 `DS2API_CONFIG_JSON`（把 `config.json` 转成 Base64 注入）在部署前一次性写入。要注意一条流式差异：

Vercel 上 `/v1/chat/completions` 由 `api/chat-stream.js`（Node Runtime）承接流式输出，但鉴权、账号选择、会话与 PoW 准备仍由 Go 侧的 prepare 接口完成；根路径快捷别名 `/chat/completions` 仍走 Go 主链路。所以需要实时流式时，请使用 `/v1/chat/completions`。

### 方式四：源码编译

前置要求 Go 1.26+，Node（`20.19+` 或 `22.12+`，仅在需要构建 WebUI 时）：

```bash
git clone https://github.com/CJackHwang/ds2api.git
cd ds2api
cp config.example.json config.json
go run ./cmd/ds2api
```

默认绑定 `0.0.0.0:5001`，同一局域网的设备可通过内网 IP 访问。首次启动若 `static/admin` 尚不存在，会自动尝试 `npm ci --prefix webui` 并构建 WebUI。

## SDK 调用

### OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-key-in-config",  # 需与 config.keys 一致
    base_url="http://localhost:5001/v1"
)

response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[{"role": "user", "content": "Hello"}]
)
print(response)
```

### Claude SDK

```python
from anthropic import Anthropic

client = Anthropic(
    api_key="your-key-in-config",
    base_url="http://localhost:5001"
)

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
)
```

Claude 模型名会通过别名表映射到 DeepSeek 原生模型（如 `claude-sonnet-4-6` → `deepseek-v4-flash`）。Gemini SDK 走 `/v1beta/models/*`，同样支持。启用工具调用时，客户端请求哪种协议，DS2API 就按该协议返回工具调用结构（OpenAI/Claude/Gemini 各自原生形态）。

### Claude Code 接入

README 里有一条实测避坑经验：`ANTHROPIC_BASE_URL` 直接指向 DS2API 根地址（如 `http://127.0.0.1:5001`），Claude Code 会请求 `/v1/messages?beta=true`。`ANTHROPIC_API_KEY` 需与 `config.keys` 一致。若系统设了代理，给 DS2API 配上 `NO_PROXY=127.0.0.1,localhost,<你的主机IP>`，避免本地回环请求被代理拦截。

## 工具调用（Tool Calling）的几个注意点

DS2API 对工具调用做了防泄漏与转译，识别并非无脑开启：

- **只在非 Markdown 代码上下文启用执行型识别**——fenced code block 和行内 code span 里的示例默认不触发。
- **推荐的可执行格式是半角管道符 DSML 外壳**：`<|DSML|tool_calls>` → `<|DSML|invoke name="...">` → `<|DSML|parameter name="...">`；兼容层也接受旧式 canonical XML（`<tool_calls>` → `<invoke name="...">` → `<parameter name="...">`）。旧式 `<tool_use>`、`<function_call>`、纯 JSON `tool_calls` 片段不会执行，会作为普通文本处理。
- `/v1/responses` 流式严格使用官方 item 生命周期事件（`response.output_item.*`、`response.content_part.*`、`response.function_call_arguments.*`），并支持 `tool_choice`。

## 适用边界

**适合的场景：**

- 已有基于 OpenAI/Claude SDK 构建的项目，想低成本试 DeepSeek。
- 需要在多个模型厂商之间切换，不想维护多套 SDK 集成代码。
- 开发调试阶段，通过 `/admin` 的 WebUI 可视化对话记录。

**不适合的场景：**

- 对可用性 SLA 有硬要求的生产服务——DS2API 依赖 DeepSeek Web 而非官方 API，稳定性受 Web 端影响，且仓库已归档、不再维护。
- 需要 Vision 等高级多模态功能的场景——上游视觉模型只暴露 `vision` 通道，能力受限。
- 不想维护账号登录态的场景——账号登录或刷新失败时，相关请求会返回 401/429。

如果你的场景是"已经写好了 OpenAI SDK 代码，想试试切到 DeepSeek 能省多少钱"，DS2API 是最低成本的验证路径；因为仓库已归档，跑通思路后建议转向官方 API 或仍活跃的替代方案。