---
title: "claude-tap：把 9 个 agent CLI 的 API 流量变成可追溯可对比的本地 trace"
date: 2026-06-27T02:40:00+08:00
draft: false
categories:
  - 技术笔记
tags:
  - AI-Agent
  - 可观测性
  - 开源项目
  - 调试工具
slug: liaohch3-claude-tap-agent-api-trace-viewer
author: 钳岳星君
description: "liaohch3 的 claude-tap（MIT，2021 stars），支持 13 个 agent 客户端的本地 API 流量拦截与 trace viewer；用 reverse proxy + forward proxy（TLS MITM）+ SQLite 本地存储 + 嵌入式 HTML viewer，把 agent 的实际 API 请求变成可逐字段对比的调试材料。"
---

# claude-tap：把 9 个 agent CLI 的 API 流量变成可追溯可对比的本地 trace

## 核心判断

[liaohch3/claude-tap](https://github.com/liaohch3/claude-tap) 是 2026 年 2 月开源的 agent API 流量拦截工具，发布 4 个月到 2021 stars / 203 forks，是 agent 可观测性赛道目前社区认可度最高的工作。命令名 `claude-tap`，把任何 agent CLI 的所有 LLM API 请求截下来、存到本地 SQLite、渲染成可对比的浏览器 viewer，**所有 trace 数据不出本机**。

支撑这个判断的是这个项目的覆盖宽度。claude-tap v0.1.x 当前支持 **13 个客户端**：

| 类型 | 客户端 |
|---|---|
| **原生支持（9 个）** | Claude Code、Codex CLI、Codex App、Gemini CLI、Kimi CLI、MiMo Code、OpenCode、OpenClaw、Pi、Hermes Agent、Cursor CLI |
| **Forward proxy 模式（4 个）** | Qoder CLI、Antigravity CLI、CodeBuddy CLI |

13 个客户端覆盖了 2026 年中所有主流 coding agent CLI。GitHub Description 直接列出来：「Intercept and inspect Coding Agent API traffic from Claude Code, Codex CLI, Gemini CLI, Cursor CLI, OpenCode, Kimi/Kimi Code, Pi, and Hermes in a local trace viewer」——**这是 agent observability 赛道的「一家通吃」工具**。

把 claude-tap 放进 agent 基础设施六联篇来看，它的卡位在「**比 Phistory 更底层**」：

- [Phistory](https://txtmix.com/posts/tech/weifeng2333-phistory-system-prompt-version-archive/) 在 claude-tap 之上构建——用 claude-tap 的 `--tap-export-prompt` capture-only 模式做系统提示词版本归档
- [SkillSpector](https://txtmix.com/posts/tech/nvidia-skillspector-agent-skill-security-scanner/) 在 skill 维度做安全扫描
- [Virtue AI](https://txtmix.com/posts/tech/meta-poaches-virtue-ai-agent-security-talent-war/) 是人才与组织战争
- [FTShare SDK](https://txtmix.com/posts/tech/ftshare-python-sdk-financial-data-agent-access-layer/) 是 skill 的数据接入
- [DAO Code](https://txtmix.com/posts/tech/tigicion-dao-code-deepseek-coding-agent-cache-engineering/) 是 agent 工程取舍
- **claude-tap 是 agent 的「X-Ray」**——看 agent 实际在和 LLM 说什么

claude-tap 不是 prompt 归档、不是 skill 安全、不是数据接入，是**「agent ↔ LLM 之间那条看不见的线」的观测器**。任何一个写 agent、debug agent、研究 agent 行为的人，都离不开这条路。

## 学习目标

读完本文后，你应当能够：

1. 说出 claude-tap 在 agent 基础设施六联篇里的卡位（X-Ray 工具），以及它和 Phistory、SkillSpector、Virtue AI、FTShare SDK、DAO Code 的关系。
2. 解释 reverse proxy 和 forward proxy 两种模式的核心差异（client 显式连 claude-tap vs client 走 HTTP_PROXY + CONNECT + TLS MITM），以及为什么 forward proxy 能保留 OAuth 认证。
3. 列出 claude-tap 支持的 13 个客户端及其分类（9 个原生 / 4 个 forward proxy），并指出每个客户端对应的 upstream URL 模式。
4. 描述 SQLite 本地 trace 存储 + Live Viewer Server WebSocket 广播 + 嵌入式 HTML viewer（viewer.html 单文件自包含）这三层的数据流。
5. 解释 `SENSITIVE_HEADER_KEYS` 包含 authorization / cookie / x-api-key / cosy-key / cosy-machinetoken 等敏感 header 的脱敏策略，以及为什么 Qoder / Cosy 客户端的运行时 header 会被特别保护。
6. 跑 `claude-tap -- --model claude-sonnet-4-6 -p "hello"` 在本地启动一个 trace viewer，看浏览器里逐字段的请求/响应 diff。

## 目录

- [核心判断](#核心判断)
- [学习目标](#学习目标)
- [生态卡位：agent 的 X-Ray](#生态卡位agent-的-x-ray)
- [总览图：一次 trace 抓取的 4 大支柱](#总览图一次-trace-抓取的-4-大支柱)
- [Reverse Proxy 模式：client 显式连 claude-tap](#reverse-proxy-模式client-显式连-claude-tap)
- [Forward Proxy 模式：CONNECT + TLS MITM](#forward-proxy-模式connect--tls-mitm)
- [SQLite 本地 trace + 统计累积](#sqlite-本地-trace--统计累积)
- [Live Viewer Server + viewer.html 单文件自包含](#live-viewer-server--viewerhtml-单文件自包含)
- [敏感 header 脱敏策略](#敏感-header-脱敏策略)
- [13 个客户端的 upstream URL 模式](#13-个客户端的-upstream-url-模式)
- [任务如何流过系统：一次完整 trace](#任务如何流过系统一次完整-trace)
- [决策启示：agent 作者 / debug 用户 / 团队 lead / 审计各看什么](#决策启示agent-作者--debug-用户--团队-lead--审计各看什么)
- [采用顺序与边界](#采用顺序与边界)
- [参考资料](#参考资料)

## 生态卡位：agent 的 X-Ray

claude-tap 的卡位要先从「agent 调试为什么难」讲起。传统的 web 应用调试，浏览器开发者工具 Network 面板能直接看 HTTP 请求。但 agent CLI 跑在终端里、和 LLM provider 走 HTTPS、请求体是 SSE 流式 JSON——开发者看不到 agent 实际发了什么、改了什么、收到了什么。

claude-tap 解决的三个具体问题：

1. **prompt 调试**——agent 报告「system prompt 没生效」，但实际 prompt 里某个开关是 `false`——怎么验证？
2. **token 计数**——「这一轮花了多少 token」「cache hit ratio 是多少」「prompt cache 实际命中了多少」
3. **跨请求 diff**——「上一轮和这一轮有什么字段变了」「某个工具调用到底错在哪一步」

对应这三类问题的三类读者：

| 读者 | 用 claude-tap 干什么 |
|---|---|
| agent 开发者 | 调试 agent prompt 设计，验证 model 收到的真实 prompt |
| agent 用户 | 排查 agent 行为异常，看实际请求参数 |
| agent 研究者 | 写 agent 行为分析文章，引用具体 trace 证据 |
| 团队 lead | 监控团队 agent 使用成本，发现 prompt 泄露 |
| 审计 | 验证 agent 不发敏感数据出去，看 redact 后的字段 |

claude-tap 不是 prompt 工程工具（不改 prompt）、不是 agent 框架（不调度工具）、不是 LLM 可观测性平台（不存储调用历史到云端）。它是**纯本地、纯 Python、单进程的 trace 拦截器**——和 Linux 下的 `tcpdump`、Chrome 的 DevTools Network 面板定位类似。

## 总览图：一次 trace 抓取的 4 大支柱

```text
                        Agent CLI
                            │
                            │ HTTPS 请求
                            ▼
    ┌───────────────────────────────────────────┐
    │  Reverse Proxy (proxy.py)                 │
    │  或 Forward Proxy (forward_proxy.py)      │
    │  - HTTPS termination / TLS MITM          │
    │  - Header 过滤 (SENSITIVE_HEADER_KEYS)    │
    │  - SSE 流重组 (SSEReassembler)            │
    └──────────┬────────────────────────────────┘
               │
               ▼
    ┌───────────────────────────────────────────┐
    │  TraceWriter (trace.py)                   │
    │  - async SQLite writer                    │
    │  - 统计累积（input/output/cache tokens）  │
    │  - Live WebSocket 广播                     │
    └──────────┬────────────────────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
   SQLite store    Live Viewer Server
   (本地持久)      (WebSocket 广播)
                       │
                       ▼
                  viewer.html
                  (嵌入式单文件)
```

四大支柱：

1. **Proxy 层**——reverse 或 forward，截获 agent ↔ LLM 的 HTTPS 流量
2. **TraceWriter 层**——async SQLite writer，累积统计 + Live 广播
3. **SQLite 存储层**——本地持久化 trace session（可跨重启读）
4. **Live Viewer + HTML viewer**——浏览器实时看 + 可导出自包含 HTML 分享

## Reverse Proxy 模式：client 显式连 claude-tap

Reverse proxy 是最常见的模式。Client 启动时把 `--tap-client claude` 之类的参数传给 claude-tap，claude-tap 在本地启 HTTP server（默认 0.0.0.0:8888），agent 启动后所有 LLM API 请求被改写到 claude-tap。

```bash
# Claude Code 走 reverse proxy
claude-tap -- --model claude-sonnet-4-6 -p "hello"
```

`cli_clients.py` 里 `run_client()` 负责根据 `--tap-client` 选不同的 AgentSpec，调 `forward_proxy.py` 或 `proxy.py`：

```python
# proxy.py 核心：拦截 client 请求、转发到 upstream、记录 trace
class proxy_handler:
    async def handle(self, request):
        # 1. 过滤敏感 header
        filtered_headers = filter_headers(dict(request.headers))
        # 2. 解析请求体（提取 system prompt / messages / tools）
        parsed_body = _parse_request_body_for_trace(request_body)
        # 3. 转发到 upstream
        upstream_response = await self.forward(request, ...)
        # 4. 重组 SSE 流 + 解析 usage
        sse_events = SSEReassembler.feed(upstream_response)
        usage = normalize_usage(upstream_response)
        # 5. 写 trace
        await self.trace_writer.write(record)
        return upstream_response
```

Reverse proxy 的优点是简单——client 启动参数一改即可，所有 API 请求都过 claude-tap。**缺点是要改 client 启动命令**——这在「agent CLI 是 npm 全局安装 + 我想不污染我的 shell 配置」时不便。

## Forward Proxy 模式：CONNECT + TLS MITM

Forward proxy 是更巧妙的设计。client 用 `HTTP_PROXY` / `HTTPS_PROXY` 环境变量把流量发给 claude-tap，claude-tap 走 HTTP CONNECT 协议在本地建 TLS MITM 隧道，把 HTTPS 解密后再转发给真实 upstream：

```python
# forward_proxy.py 注释（核心解释）
"""HTTP forward proxy with CONNECT tunneling and man-in-the-middle TLS termination.

Flow:
  1. Client sends CONNECT api.anthropic.com:443
  2. Proxy responds 200 Connection Established
  3. Client starts TLS handshake; proxy presents a cert signed by our CA
  4. Client sends plaintext HTTP request inside the TLS tunnel
  5. Proxy reads the request, records the trace, forwards to real upstream via HTTPS
  6. Proxy returns the upstream response through the tunnel
"""
```

TLS MITM 的关键是 `certs.py` 维护的本地 CA：

```python
# certs.py 核心
class CertificateAuthority:
    """本地 CA，自动生成自签证书，macOS 上自动 trust 到 keychain"""

    def generate_cert_for_host(hostname: str) -> CertPair:
        # 用本地 CA 签发 host-specific 证书
        ...
```

client 的 TLS 握手时，claude-tap 拿到 client 的 SNI（Server Name Indication，比如 `api.anthropic.com`），用本地 CA 签发一个 host-specific 证书返回给 client。client 因为已经 trust 了 claude-tap 的 CA（macOS 上 `trust_macos_ca()` 自动加进 keychain），会接受这个证书。

**这是 forward proxy 能保留 OAuth 认证的关键**——client 的 OAuth token 还是发给 `api.anthropic.com`，只是网络路径经过 claude-tap。claude-tap 解密后用**客户端原始 Authorization header**转发给真实 upstream，OAuth 流程完全不变。

forward proxy 对**客户端完全透明**——用户不用改 client 启动命令，只要：

```bash
export HTTPS_PROXY=http://127.0.0.1:8888
claude  # 正常启动，所有流量过 claude-tap
```

## SQLite 本地 trace + 统计累积

`trace.py` 的 `TraceWriter` 是 trace 写入的核心：

```python
class TraceWriter:
    def __init__(self, session_id, live_server=None, ...):
        self.session_id = session_id
        self._lock = asyncio.Lock()
        self.count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cache_read_tokens = 0
        self.total_cache_create_tokens = 0
        self.models_used: dict[str, int] = {}

    async def write(self, record: dict) -> None:
        async with self._lock:
            self._write_locked(record)
        if self._live_server:
            await self._live_server.broadcast(record)
```

关键设计：

1. **asyncio.Lock** 保护并发写——多请求并发转发时，trace 写不互相覆盖
2. **统计累积**——每个请求写完后更新 token 计数，viewer 可以直接显示本 session 累计花费
3. **Live broadcast**——每次写完调 `live_server.broadcast()` 推给 WebSocket，浏览器实时刷新

`trace_store.py` 的 SQLite 表结构（推断）：

```
trace_sessions (id, created_at, agent, total_input_tokens, ...)
trace_records (session_id, turn, request_body, response_body, usage, ...)
```

`dashboard.py` 是 session-first dashboard——把所有 session 列出来，每个 session 显示「agent / 时间 / token 总数 / 状态」，点进去看具体 trace。

## Live Viewer Server + viewer.html 单文件自包含

claude-tap v0.1.75+ 默认开启 Live Viewer（`--tap-no-live` 可关闭）。`live.py` 的 `LiveViewerServer` 启动一个 WebSocket server，TraceWriter 写每条记录都广播过去。

`viewer.py` 把整段 trace 渲染成单文件 HTML：

```python
LAZY_THRESHOLD = 50  # 超过 50 条记录用 lazy mode
VIEWER_JS_PATHS = (
    "state.js", "responses.js", "lazy_loading.js",
    "i18n_ui.js", "live_bootstrap.js", "filters_search.js",
    "sidebar.js", "detail_trace.js", "renderers.js",
    "sections_json.js", "diff.js", "utilities_mobile.js",
)
```

12 个 JS 模块各司其职——state 是响应式 state 容器、renderers 渲染各种 trace 字段、diff 做跨请求 diff、lazy_loading 处理大 trace 分页、i18n_ui 多语言支持、live_bootstrap WebSocket 初始化。

`viewer.html` 模板 + CSS + JS 全部打包进单文件，浏览器可以直接打开。`export.py` 把 trace 导出成单文件 HTML，可以邮件发给同事——对方不需要装 claude-tap 也能看。

i18n 是亮点——`viewer_i18n.json` 多语言字典（README 提到有中英两套），screenshot 里有 light/dark 模式切换、diff modal 弹窗、Structured diff across adjacent requests。

## 敏感 header 脱敏策略

`proxy.py:30-50` 的 `SENSITIVE_HEADER_KEYS` 是关键的安全设计：

```python
SENSITIVE_HEADER_KEYS = frozenset({
    "authorization",
    "cookie",
    "set-cookie",
    "set-cookie2",
    "x-api-key",
    "x-amz-security-token",
    # Qoder/Cosy 运行时 headers can carry account, machine, or token-derived
    # identifiers and must not be persisted in trace evidence.
    "cosy-key",
    "cosy-machinetoken",
    "cosy-machine-token",
    "cosy-machineid",
    ...
})
```

脱敏三类：

1. **认证类**：`authorization` / `cookie` / `x-api-key` / `x-amz-security-token`（AWS Bedrock SigV4 token）
2. **OAuth state**：`set-cookie` / `set-cookie2`（OAuth 流程的 state token）
3. **国产客户端运行时**：`cosy-key` / `cosy-machinetoken` / `cosy-machine-token` / `cosy-machineid`（Qoder/Cosy 是腾讯的 CodeBuddy 系）

注释特意提到 Qoder/Cosy headers：「can carry account, machine, or token-derived identifiers and must not be persisted in trace evidence」。这是对国产 agent 客户端的特别保护——它们可能在 header 里塞用户标识符 / 机器指纹 / token 派生值，存到 trace 里就泄露了。

`filter_headers()` 在 trace 写入前把这些 header 替换为 `REDACTED`，viewer 里看到的就是「REDACTED」而不是真值。

**测的是什么、不能推出什么**：脱敏测的是「已知敏感 header 不会被持久化」。**不能推出**「请求体里没有泄露」——如果 prompt 里出现 `os.environ["API_KEY"]`，脱敏不会保护请求体里的内容。这是 prompt engineering 责任，不是 claude-tap 责任。

## 13 个客户端的 upstream URL 模式

`upstream.py` 的 `KNOWN_UPSTREAM_ENDPOINT_PATHS` 列了 7 类标准 endpoint：

```python
KNOWN_UPSTREAM_ENDPOINT_PATHS = (
    "/v1/chat/completions",
    "/chat/completions",
    "/v1/messages",
    "/messages",
    "/v1/responses",
    "/responses",
    "/v1/completions",
    "/completions",
)
```

13 个客户端的 upstream 分类：

| 客户端 | Endpoint 路径 | 认证 | 模式 |
|---|---|---|---|
| Claude Code | `/v1/messages` | ANTHROPIC_API_KEY / OAuth / Bedrock SigV4 | Reverse |
| Codex CLI | `/v1/responses` 或 `/chat/completions` | OPENAI_API_KEY / ChatGPT OAuth | Reverse |
| Codex App | (本地 CDP WebSocket) | ChatGPT OAuth | CDP Listener |
| Gemini CLI | (Google API) | Google OAuth / Code Assist | Reverse |
| Kimi CLI | (Moonshot API) | MOONSHOT_API_KEY | Reverse |
| MiMo Code | (Xiaomi fork of OpenCode) | 多 provider | Reverse |
| OpenCode | (multi-provider) | 多 provider | Reverse |
| OpenClaw | (multi-provider) | 多 provider | Reverse |
| Pi | (OpenAI Codex OAuth) | OAuth | Reverse |
| Hermes Agent | (NousResearch) | 多 provider | Reverse |
| Cursor CLI | (Cursor Agent) | Cursor OAuth | Reverse + Transcript Import |
| Qoder CLI | (Qoder Agent) | cosy-* headers | Forward |
| Antigravity CLI | (Google) | Google OAuth | Forward |
| CodeBuddy CLI | (Tencent) | Tencent OAuth | Forward |

`cli_clients.py` 的 `_BEDROCK_HOST_RE` 检测 AWS Bedrock SigV4-signed endpoints（`bedrock-runtime.us-east-1.amazonaws.com` 等）——这是 Claude Code 走 AWS Bedrock 时的特殊路径，claude-tap 要重写 URL 避免变成 `/v1/messages/v1/messages` 这种重复。

`build_upstream_url()` 注释特别说明：

```python
"""Join a configured upstream target with a forwarded request path.

Some users pass a complete request endpoint such as
``https://gateway.example/v1/messages`` to ``--tap-target``. Avoid turning
a client request for ``/v1/messages`` into ``/v1/messages/v1/messages``.
"""
```

这是 forward proxy 模式常见的坑——target 已经是 endpoint，forward 的 path 又拼一遍，导致 `/v1/messages/v1/messages`。claude-tap 显式避免这个重复。

## 任务如何流过系统：一次完整 trace

为了让 4 大支柱抽象落地，看一个具体的「用 Claude Code 跑 hello」怎么走完整 trace 流程。

**命令**：

```bash
claude-tap -- --model claude-sonnet-4-6 -p "hello"
```

**Step 1：CLI 解析 + 选 AgentSpec**

`cli.main_entry()` 解析参数，发现 `--tap-client` 没指定但有 `--`，自动从「claude」detect。`cli_clients.py:run_client('claude', ...)` 选 `CLAUDE_CONFIG`，启动 reverse proxy server on 8888。

`ANTHROPIC_BASE_URL` 没设（默认走 api.anthropic.com），所以 reverse proxy 把请求改写到 `http://localhost:8888`。

**Step 2：启动 Claude Code 子进程**

claude-tap 用 subprocess 启动 `claude --model claude-sonnet-4-6 -p "hello"`，env 里设 `ANTHROPIC_BASE_URL=http://localhost:8888`，让 Claude Code 把所有 LLM 请求发到本地 proxy。

**Step 3：Claude Code 发起请求**

Claude Code 准备发送 system prompt + `user: "hello"`，HTTP POST 到 `http://localhost:8888/v1/messages`。

**Step 4：proxy_handler 拦截**

`proxy.py:proxy_handler.handle()`：

1. 过滤 headers（SENSITIVE_HEADER_KEYS → REDACTED）
2. 解析请求体（提取 system prompt / messages / tools / model）
3. 通过 `TraceWriter.write_next_turn()` 分配 turn number + 写 trace
4. 转发到 upstream `https://api.anthropic.com/v1/messages`（使用原始 Authorization header）
5. 接收 upstream SSE 流
6. `SSEReassembler` 重组流式 chunks
7. `normalize_usage` 提取 token usage（input/output/cache_read/cache_create）
8. 写第二条 trace（response）
9. 更新 TraceWriter 的累计统计（total_input_tokens += ...）
10. `live_server.broadcast(record)` 推给 WebSocket
11. 返回响应给 Claude Code

**Step 5：Claude Code 收到响应**

Claude Code 拿到 SSE 流式响应（"hi there!"），显示给用户，结束。

**Step 6：viewer 渲染**

用户浏览器打开 `http://localhost:8888/dashboard`（或者 Live Viewer 默认 URL）：

- dashboard 列出本 session（含 token 总数 / 请求数 / 状态）
- 点进 session 看每条 trace
- 左右栏 diff 跨请求字段差异
- 系统 prompt / messages / tool calls / SSE 重组后的完整响应 全部可读

**Step 7：导出（可选）**

`claude-tap export --output trace.html` 把整个 session 打包成单文件 HTML，发给同事 review——对方不需要装 claude-tap，浏览器打开就能看。

## 决策启示：agent 作者 / debug 用户 / 团队 lead / 审计各看什么

claude-tap 对四类读者的信号不同。

**agent 作者**——claude-tap 是 agent 调试的「必备 X-Ray」。具体动作：

- 写 agent prompt 时开 `--tap-live` 看每次请求的完整 system prompt + messages，验证设计意图和实际发出去的一致
- 调 `--model` / `--permission-mode` 等参数时看 trace 变化，确认改动生效
- 调试 tool use 错误时看具体 tool call 参数和返回，比看 agent 终端输出直观得多

**debug 用户**——遇到 agent 行为异常（答非所问、工具调用失败、莫名卡住）时，第一步用 claude-tap 看实际请求：

- 答非所问：检查 system prompt 是否被截断 / 上下文是否完整
- 工具调用失败：检查 tool schema 是否对得上 / 返回值是否在 context 里被消化
- 莫名卡住：检查是否某个 request 在 retry loop 里死循环

**团队 lead**——claude-tap 提供 agent 使用成本的可观测性：

- 每月一次全员 agent trace review，看 token 使用 / cache hit / 高频 prompt pattern
- 监控 prompt 泄露风险——trace 里看到 PII / 公司代码片段就能及时提醒
- 培训新人时用真实 trace 做案例（「看，这就是 Claude Code 实际发的 system prompt」）

**审计 / 合规**——claude-tap 是「agent 实际发出去什么」的权威证据：

- 第三方 agent SDK 接入时用 claude-tap 抓 1 周，看实际请求里有没有可疑调用
- 内部 agent 出问题时回放 trace，证明 agent 行为符合预期
- 在合规报告里附 trace snapshot（记得脱敏！）

## 采用顺序与边界

对想用 claude-tap 的读者，按以下顺序最经济：

**第一步：`uv tool install claude-tap`**——一行装上，命令立即可用。

**第二步：跑一次最小 trace**——`claude-tap -- -p "say hi"` 看浏览器默认 URL（通常 http://localhost:8888/dashboard 或类似）打开的 viewer。理解一次请求的 5 个字段（system / messages / tools / response / usage）。

**第三步：把真实工作流接入**——在你日常用的 agent CLI 前面加 `claude-tap`（或 export HTTPS_PROXY），开始记录真实任务。**注意：这会记录所有 API 请求的 prompt——敏感信息不要在 prompt 里直接出现**。

**第四步：跨请求 diff 调 bug**——遇到 agent 异常行为时，对比「正常 turn」和「异常 turn」的 trace diff，定位具体哪个字段变了。

**第五步：导出 + 分享**——`claude-tap export --output trace.html` 生成可分享的单文件，发给同事 / 贴 issue。

**不一定要做的事**：

- 不要把 trace 存到云端——claude-tap 设计就是「本地」，上传云端会泄露 prompt 内容
- 不要在生产环境长开——claude-tap 增加 ~10-50ms 延迟，dev / debug 阶段用
- 不要给多用户共享机器开——trace SQLite 是用户隔离的，混用会泄露不同人的 prompt
- 不要假设脱敏完整——`SENSITIVE_HEADER_KEYS` 保护 header，但请求体里如果出现 API key（agent 代码 bug）脱敏管不到

**边界**：claude-tap 主要覆盖「agent ↔ LLM 之间的 HTTP 流量」，对以下场景只能部分覆盖：

- **Tool 内部副作用**——tool 调用 shell command 的 stdout / stderr 不在 trace 里（除非 agent 把它们塞进 tool result）
- **文件系统操作**——agent 读 / 写文件的内容不在 trace 里（除非通过 Read tool 发回 LLM）
- **非 HTTP 客户端**——某些 agent 用 gRPC / WebSocket 时需要 codex_app_cdp 模式（best-effort）
- **云端 LLM provider 内部**——claude-tap 看到的是 client 发出的请求，看不到 provider 内部处理

最后一个边界值得强调——claude-tap 是「client-side」可观测性。Provider 端（Anthropic / OpenAI 自己的 trace）claude-tap 看不到。这和传统 APM 的 server-side tracing 互补。

## 参考资料

- [liaohch3/claude-tap GitHub 仓库](https://github.com/liaohch3/claude-tap)，MIT 协议，截至 2026-06-27 共 2021 stars / 203 forks，v0.1.75+
- [claude_tap/proxy.py](https://github.com/liaohch3/claude-tap/blob/main/claude_tap/proxy.py)——reverse proxy handler + `SENSITIVE_HEADER_KEYS` 定义
- [claude_tap/forward_proxy.py](https://github.com/liaohch3/claude-tap/blob/main/claude_tap/forward_proxy.py)——CONNECT + TLS MITM forward proxy
- [claude_tap/cli.py](https://github.com/liaohch3/claude-tap/blob/main/claude_tap/cli.py)——CLI 入口 + `--tap-client` 调度
- [claude_tap/cli_clients.py](https://github.com/liaohch3/claude-tap/blob/main/claude_tap/cli_clients.py)——13 个客户端的 launch + target detection
- [claude_tap/certs.py](https://github.com/liaohch3/claude-tap/blob/main/claude_tap/certs.py)——本地 CA 自动 trust 到 macOS keychain
- [claude_tap/trace.py](https://github.com/liaohch3/claude-tap/blob/main/claude_tap/trace.py)——async SQLite TraceWriter
- [claude_tap/viewer.py](https://github.com/liaohch3/claude-tap/blob/main/claude_tap/viewer.py)——单文件 HTML viewer 生成（12 个 JS 模块）
- [claude_tap/upstream.py](https://github.com/liaohch3/claude-tap/blob/main/claude_tap/upstream.py)——upstream URL 构造（避免 `/v1/messages/v1/messages` 重复）
- [docs/guides/agent-trace-viewer.md](https://github.com/liaohch3/claude-tap/blob/main/docs/guides/agent-trace-viewer.md)——本地 trace viewer 使用指南
- [Phistory: WEIFENG2333/phistory](https://github.com/WEIFENG2333/phistory)——claude-tap 下游消费者（系列）
- [NVIDIA SkillSpector](https://txtmix.com/posts/tech/nvidia-skillspector-agent-skill-security-scanner/)——agent skill 安全（系列）
- [Meta 挖角 Virtue AI](https://txtmix.com/posts/tech/meta-poaches-virtue-ai-agent-security-talent-war/)——agent 安全人才战（系列）
- [FTShare Python SDK](https://txtmix.com/posts/tech/ftshare-python-sdk-financial-data-agent-access-layer/)——agent skill 数据接入（系列）
- [DAO Code](https://txtmix.com/posts/tech/tigicion-dao-code-deepseek-coding-agent-cache-engineering/)——agent 工程（系列）
