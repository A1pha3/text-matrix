---
title: "claude-tap 复核：客户端长到 16 个，Codex App 和 Cursor 换了采集路线"
date: 2026-06-27T02:40:00+08:00
lastmod: 2026-10-05T00:00:00+08:00
draft: false
categories:
  - 技术笔记
tags: ["AI Agent", "可观测性", "开源项目", "调试工具"]
slug: liaohch3-claude-tap-agent-api-trace-viewer
github_repo: "liaohch3/claude-tap"
source_key: "gh:liaohch3/claude-tap"
author: 钳岳星君
description: "liaohch3 的 claude-tap（MIT，发文时 2,021 stars，2026-10-05 复核 3,260 stars，v0.1.145），用本地 reverse/forward 代理把 16 个 agent CLI 的 LLM API 流量截成逐字段可对比的 trace：SQLite 存储、SSE 实时广播、单文件 HTML viewer，数据不出本机。"
---

# claude-tap 复核：客户端长到 16 个，Codex App 和 Cursor 换了采集路线

## 核心判断

[liaohch3/claude-tap](https://github.com/liaohch3/claude-tap) 是 2026 年 2 月开源的 agent API 流量拦截工具：把 agent CLI 对 LLM provider 发出的 HTTPS 请求截下来，存进本地 SQLite，渲染成浏览器里逐字段可对比的 trace viewer。所有数据留在本机，README 的说法是「no hosted dashboard is required」。发文时（2026-06-27）它在 v0.1.122 附近、2,021 stars；2026-10-05 复核时 v0.1.145、3,260 stars——三个月发了 23 个版本，客户端从 14 个涨到 16 个，不是均匀铺量，而是两条采集路线（Codex App、Cursor）整体换了实现方式。

支撑判断的是覆盖宽度。`--tap-client` 现在接受 17 个 key、对应 16 个产品（Kimi 家族占两个 key），GitHub 仓库描述点名 Claude Code、Codex CLI、Gemini CLI、Cursor CLI、OpenCode、Kimi、Pi、Hermes。命令把任何 agent CLI 的 LLM 请求截下来、写进本地 SQLite、渲染成可对比的浏览器 viewer，**所有 trace 数据不出本机**。

本文基于现行 v0.1.145 与发文时点 commit（4d6e4c85，v0.1.122）双时点对照写成；直播流的广播机制、客户端默认代理模式这类易变口径，一律以源码与现行 README 为准。三个月里的形态级变化集中在 Codex App 与 Cursor 两节单独交代。

## 生态卡位：agent 调试缺的那块

Web 应用的调试有浏览器 DevTools Network 面板兜底；agent CLI 跑在终端里，和 provider 走 HTTPS + SSE 流式 JSON，开发者看不到它实际发了什么。claude-tap 对应三类具体问题：

1. **prompt 调试**——agent 声称「system prompt 已生效」，真实请求里的值是不是你想要的，看 trace 就知道；
2. **token 计量**——每轮 input/output/cache read/cache creation 四项用量，session 级累计；
3. **跨请求 diff**——相邻两次请求哪个字段变了，viewer 内置结构化 diff。

它的上游消费者已经出现：[Phistory](https://txtmix.com/posts/tech/weifeng2333-phistory-system-prompt-version-archive/)（WEIFENG2333/phistory）用 claude-tap 的 capture-only prompt 导出（`--tap-export-prompt`）做系统提示词版本归档，README 的 Built with claude-tap 一节点名了这个用法。相邻赛道还有 [SkillSpector](https://txtmix.com/posts/tech/nvidia-skillspector-agent-skill-security-scanner/)（skill 安装前安全扫描）、[Virtue AI 人才战](https://txtmix.com/posts/tech/meta-poaches-virtue-ai-agent-security-talent-war/)、[FTShare SDK](https://txtmix.com/posts/tech/ftshare-python-sdk-financial-data-agent-access-layer/)（数据接入层）和 [DAO Code](https://txtmix.com/posts/tech/tigicion-dao-code-deepseek-coding-agent-cache-engineering/)（缓存工程取舍）。claude-tap 自己的位置最底层：**agent 与 LLM 之间那条 HTTP 线的观测器**。写 agent、调 agent、研究 agent 行为，最后都要落到这层证据上。

## 系统总览：四层结构

```text
                 Agent CLI（claude / codex / gemini / …）
                     │  基址改写或 HTTP(S)_PROXY
                     ▼
   ┌─────────────────────────────────────────────┐
   │  Proxy 层                                    │
   │  reverse: proxy.py（改写 base URL 直连本地）  │
   │  forward: forward_proxy.py（CONNECT + TLS   │
   │           MITM，按 SNI 现签证书）             │
   │  - filter_headers()：14 项敏感 header 脱敏    │
   │  - 路径白名单 ALLOWED_PATH_PREFIXES          │
   │  - SSE/WS 流边收边转发，低开销                │
   └──────────────────┬──────────────────────────┘
                      ▼
   ┌─────────────────────────────────────────────┐
   │  TraceWriter（trace.py）                     │
   │  asyncio.Lock 串行写入；逐请求累积           │
   │  input/output/cache 四项 token 统计          │
   │  写完即经 SSE 向浏览器广播（live.py）         │
   └──────────────────┬──────────────────────────┘
                      ▼
   ┌────────────────────┐   ┌──────────────────┐
   │ SQLite（trace_store │   │ Live viewer /    │
   │ .py：5 张表，本地   │   │ dashboard：固定   │
   │ 持久，跨重启可读）  │   │ 端口，浏览器直开  │
   └────────────────────┘   └──────────────────┘
                      ▼
            export：单文件自包含 HTML
```

四层各自的职责：

1. **Proxy 层**——reverse 或 forward，截获 agent 与 LLM 之间的流量并按白名单过滤；
2. **TraceWriter 层**——async SQLite 写入器，顺带累积 token 统计并广播；
3. **存储层**——本地 SQLite，5 张表，重启后 dashboard 还能读历史 session；
4. **Viewer 层**——实时直播 + 静态导出两形态，单文件 HTML 无外部依赖。

## Reverse proxy：改写基址，不碰网络栈

Reverse 模式是大多数客户端的默认。claude-tap 启动本地代理，然后在子进程环境里把客户端的 base URL 环境变量（如 `ANTHROPIC_BASE_URL`）指到本地，客户端以为自己在和 provider 说话，流量全部落在代理上：

```bash
# -- 后面的参数原样传给被包裹的客户端
claude-tap -- --model claude-sonnet-4-6 -p "hello"
```

基址检测是自动的：claude 系读 `ANTHROPIC_BASE_URL`、`ANTHROPIC_BEDROCK_BASE_URL`、`ANTHROPIC_VERTEX_BASE_URL`（环境变量或 Claude settings），用户配了 DeepSeek/自建网关也能直接被记录，`--tap-target` 只在想手动覆盖时才需要。代理端口用 `--tap-port` 指定，不指定则自动分配——**不是**固定端口。

上游 URL 拼接有一个专门防呆设计。`upstream.py` 的 `build_upstream_url()` docstring 原话：

```python
"""Join a configured upstream target with a forwarded request path.

Some users pass a complete request endpoint such as
``https://gateway.example/v1/messages`` to ``--tap-target``. Avoid turning
a client request for ``/v1/messages`` into ``/v1/messages/v1/messages``.
"""
```

用户把完整 endpoint（带 `/v1/messages`）填进 `--tap-target` 时，转发路径再拼一遍就会产生 `/v1/messages/v1/messages` 这种重复——claude-tap 显式处理了这个分支。

reverse 模式的代价是改客户端启动方式。对 npm 全局安装、不想动 shell 配置的场景，forward 模式更合适。

## Forward proxy：CONNECT 隧道 + TLS MITM

Forward 模式不改客户端，只吃环境变量：

```bash
export HTTPS_PROXY=http://127.0.0.1:<port>
claude  # 照常启动，流量自动过 claude-tap
```

`forward_proxy.py` 模块 docstring 把六步流程写得很清楚，逐字引用：

```python
"""Forward proxy server with CONNECT/TLS termination.

Implements an HTTP forward proxy that handles CONNECT tunneling with
man-in-the-middle TLS termination. This allows claude-tap to intercept
HTTPS traffic while Claude Code uses the real api.anthropic.com endpoint
(preserving OAuth authentication).

Flow:
  1. Client sends CONNECT api.anthropic.com:443
  2. Proxy responds 200 Connection Established
  3. Client starts TLS handshake; proxy presents a cert signed by our CA
  4. Client sends plaintext HTTP request inside the TLS tunnel
  5. Proxy reads the request, records the trace, forwards to real upstream via HTTPS
  6. Proxy returns the upstream response through the tunnel
"""
```

TLS 侧由 `certs.py` 支撑：`ensure_ca()` 维护本地 CA，`CertificateAuthority.get_host_cert_pem(hostname)` 按客户端握手中的 SNI 现场签发 host 证书。macOS 上 `trust_macos_ca()` 把 CA 自动加进**当前用户的 login keychain**（不动 System keychain，也用不着 sudo），也有独立的 `claude-tap trust-ca` 子命令给想提前信任的场景。

这一设计的直接收益是 OAuth 流程零改动：客户端的 token 还是发给 `api.anthropic.com`，只是网络路径多了本地一跳，claude-tap 解密后带着原始 Authorization header 转发。对那些不暴露 base URL 配置的客户端（典型是各家桌面 App 和用多家 endpoint 的 CLI），forward 是唯一能抓到真实请求体的路径。

## 客户端矩阵：17 个 key，三种路线

`cli_clients.py` 的 `CLIENT_CONFIGS` 是客户端矩阵的权威源码。按默认代理模式分三组（2026-10-05 源码读数）：

**默认 reverse（7 个）**——单个 provider、有 base URL 环境变量可改写：

| 客户端 | base URL env | 默认上游 |
|---|---|---|
| claude（Claude Code） | `ANTHROPIC_BASE_URL`（另有 BEDROCK/VERTEX 两个附加 env） | `api.anthropic.com` |
| codex（Codex CLI） | `OPENAI_BASE_URL` | `api.openai.com`；OAuth 登录走 `chatgpt.com/backend-api/codex` |
| grok（Grok Build CLI） | `GROK_CLI_CHAT_PROXY_BASE_URL` | `cli-chat-proxy.grok.com/v1` |
| kimi / kimi-code | `KIMI_BASE_URL` / `KIMI_CODE_BASE_URL` | `api.kimi.com/coding/v1` |
| openclaw | `OPENAI_BASE_URL` | 按所选 provider 补丁临时配置文件 |
| codebuddy | `CODEBUDDY_BASE_URL` | 自动探测 `~/.codebuddy/local_storage/` 登录缓存，缺失时回退 `copilot.tencent.com/v2` |

**默认 forward（9 个）**——多家 endpoint 或不暴露 base URL 配置：

| 客户端 | 默认上游 / 说明 |
|---|---|
| codexapp（Codex App） | `chatgpt.com/backend-api/codex`，只记该路径的产品流量 |
| dsh（DeepSeek Harness） | `api.deepseek.com`，需 Node 支持 `--use-env-proxy` |
| gemini | 多个 Google endpoint，OAuth/Code Assist 流量 |
| opencode / mimo | 多 provider，任意 HTTPS 上游（MiMo Code 是小米的 OpenCode fork） |
| pi | 任意 HTTPS 上游，openai-codex OAuth 实测通过 |
| hermes | 任意 HTTPS 上游，凭证在 `~/.hermes/` |
| qoder | Qoder 多 endpoint，支持 `QODER_PERSONAL_ACCESS_TOKEN` |
| agy（Antigravity CLI） | `daily-cloudcode-pa.googleapis.com`，自动注入 `CLOUD_CODE_URL` |

**transcript-only（1 个）**：cursor。现行实现不碰网络——启动 `cursor-agent` 后监听 `~/.cursor/projects/*/agent-transcripts/*.jsonl`，每个对话 JSONL 生成一个 dashboard session。README 原话「It does not MITM `api2.cursor.sh`」。

这张表与直觉相悖的格子不少——Codex App 走 forward、Cursor 纯转录、CodeBuddy 反而是 reverse。发文时点的版本里，Codex App 是「本地 JSONL 导入 + best-effort CDP WebSocket 旁路」，Cursor CLI 默认 forward——两条路线后来都整体重写了，细节见下节。仓库的 `docs/support-matrix.md` 维护着 30 行 client × auth × target × transport 组合表（含实测状态列），接非主流网关前先查它。

## 三个月里的两条路线换向

这是发文后变化最大的部分，读旧版介绍的人需要校准：

**Codex App：从「转录导入」到「真抓请求」。** 发文时，`--tap-client codexapp` 不启动 App、不开代理，只从 `CODEX_HOME`/`~/.codex` 导入本地 session JSONL，App 有调试端点时再尽力补一份 CDP WebSocket 证据——README 当时自称「CDP capture is a side-channel observer, not a proxy」。现行版本反过来：通过 forward proxy 启动 Codex App（macOS 上是 `ChatGPT.app`，老 `Codex.app` 也认），抓真实的 `/backend-api/codex/responses` HTTP/WebSocket 请求体；已开着的 App 不受影响，claude-tap 会用独立 `--user-data-dir` 起一个隔证实例（`~/.claude-tap/codex-app-profiles/tap`），可能需要重新登录。原始 WebSocket/SSE 事件数组默认不存，`--tap-store-stream-events` 才持久化。

**Cursor：从「forward 抓流量」到「纯转录」。** 发文时 Cursor CLI 默认走 forward proxy。现行版本彻底放弃 MITM：监听本地 transcript JSONL，不碰 `api2.cursor.sh`。代价是看不到未写入 transcript 的流量，收益是零证书、零代理配置、对 IDE 内 Agent 也生效（`--tap-no-launch` 只监听不启动 CLI）。源码里 cursor 的 `default_proxy_mode` 字段还在但注释明说 unused，以 README 为准。

两条路线换向的方向一致：**抓不到真实请求时，退而求其次抓本地可验证的记录**，并把取舍写进 README 而不是藏起来。

## 安全设计：脱敏清单与路径白名单

`proxy.py` 顶部的 `SENSITIVE_HEADER_KEYS` 是 frozenset，共 14 项：通用的 `authorization`、`cookie`、`set-cookie`、`set-cookie2`、`x-api-key`、`x-amz-security-token`，加上 8 项 `cosy-*` 运行时 header。清单上方注释原话：

```python
# Qoder/Cosy runtime headers can carry account, machine, or token-derived
# identifiers and must not be persisted in trace evidence.
```

这 8 项 `cosy-*` 是给 CodeBuddy/Qoder 一类国产客户端的专门保护——它们的 header 里可能带账号、机器指纹或 token 派生值，落进 trace 就等于泄露。脱敏的输出形态也值得写准：默认值替换为 `***`；`authorization` 和 `x-api-key` 两项走 `PREFIX_REDACTED_HEADER_KEYS`，保留**前 12 个字符**加 `...`，方便分辨认证方式又不泄露完整密钥。viewer 里看到的就是这份处理后的值。

写入侧还有一层路径白名单：`ALLOWED_PATH_PREFIXES` 只放行已知 API 路径（`/v1/messages`、`/v1/responses`、Gemini 的 `/v1beta/models` 等 20 余条），扫描器打过来的 `/etc/passwd`、`/swagger`、`/metrics` 一律 404，不转发也不记录。

边界要写清楚：脱敏覆盖的是 header。**请求体不受保护**——prompt 里如果直接出现了 API key（agent 代码 bug），claude-tap 管不到，它会把 body 原样记录。

## 存储、viewer 与导出

`trace_store.py` 的 SQLite 有 5 张表：`sessions`（id、started_at、client、proxy_mode、status、record_count、summary_json 等）、`records`（主键 `(session_id, record_index)`，带 `turn` 序号，外键级联删除）、`proxy_logs`、`migration_state`、`record_blobs`。`TraceWriter`（trace.py）用一把 `asyncio.Lock` 串行化并发写入，`write_next_turn()` 在锁内分配 turn 序号；每写一条顺带更新 session 级累计——`total_input_tokens`、`total_output_tokens`、`total_cache_read_tokens`、`total_cache_create_tokens` 和 `models_used` 计数字典。viewer 顶栏的用量汇总直接来自这些累计值。

实时侧是 `live.py` 的 `LiveViewerServer`：每条记录写完即广播。**广播走 SSE**（README 原话「broadcasts updates to the browser via SSE」），v0.1.75 起默认开启，`--tap-no-live` 关闭。`claude-tap dashboard` 可以随时单独打开历史 session 浏览器（`dashboard stop` 关闭），dashboard 固定端口，`--tap-port` 只管代理端口——两套端口别混。

viewer 本体是单文件自包含 HTML，零外部依赖。`viewer.py` 的 `LAZY_THRESHOLD = 50`：超过 50 条记录自动切 lazy 加载。前端拆成 12 个 JS 模块打进单文件——state（响应式容器）、renderers、diff（相邻请求结构化对比）、lazy_loading、filters_search、sidebar、detail_trace、responses、sections_json、i18n_ui、live_bootstrap、utilities_mobile——文件名即职责。功能面上有按 endpoint 过滤、按模型分组、tool 卡片（名称/描述/参数 schema）、全文搜索、明暗主题、j/k 键盘导航、一键复制请求 JSON 或 cURL、iframe 嵌入参数。i18n 覆盖 8 种语言（英、简中、日、韩、法、阿拉伯、德、俄），字典在 `viewer_i18n.json`。

导出语法（现行 README）：

```bash
# compact 是默认导出格式（可移植 bundle，之后可再渲染）
claude-tap export <session-id> -o trace.ctap.json

# 从 JSONL 重新生成单文件 HTML viewer
claude-tap export .traces/2026-02-28/trace_141557.jsonl -o trace.html

# 从 compact bundle 再渲染
claude-tap export trace.ctap.json -o trace.html
```

生成的 HTML 可以直接发给同事，对方浏览器打开即可，不需要装 claude-tap。

## 任务流：一条 trace 的完整路径

以包裹 Claude Code 跑一条最小任务为例：

```bash
claude-tap -- --model claude-sonnet-4-6 -p "hello"
```

1. **CLI 解析**。`cli.py` 的 `main_entry()` 解析参数；`--tap-client` 不指定时默认 `claude`，`--` 之后的参数原样传给子进程。
2. **基址检测**。读环境变量与 Claude settings 里的 `ANTHROPIC_BASE_URL`（没配则默认 `api.anthropic.com`），启动本地 reverse proxy（端口自动分配），准备把子进程的 base URL 指向它。
3. **启动子进程**。claude-tap 用 subprocess 拉起 `claude --model claude-sonnet-4-6 -p "hello"`，环境里注入改写后的 base URL。
4. **请求拦截**。Claude Code 向本地代理 POST `/v1/messages`，带 system prompt、messages、tools。代理路径白名单放行，`filter_headers()` 脱敏，请求体解析出可读结构后写入第一条 trace。
5. **转发与重组**。请求带着原始认证头转发到真实上游；SSE 响应边收边转发回客户端，同时由代理侧重组，提取 usage 四项 token 数，写第二条 trace。
6. **实时与累计**。`TraceWriter` 更新 session 累计统计，`LiveViewerServer` 把新记录经 SSE 推给浏览器。
7. **收尾**。claude 退出时自动生成一份自包含 HTML viewer 并打开；浏览器里 dashboard 列出本 session（模型、请求数、token 四项累计），点进任意请求可看完整请求体、重组后的响应，以及与相邻请求的结构化 diff。

整条链路里 claude-tap 只做三件事：截、记、展。不修改 prompt，不调度工具，不上传任何数据。

## 采用顺序与边界

**第一步：安装**。要求 Python 3.11+，`uv tool install claude-tap` 或 `pip install claude-tap`；升级用 `claude-tap update`。项目迭代快（137 个 release），装完先升一次。

**第二步：最小 trace**。`claude-tap -- -p "say hi"` 跑一条，浏览器里把 system prompt、messages、tools、response、usage 五块各看一遍，建立「trace 长什么样」的直觉。

**第三步：接入日常工作流**。日常用的 agent CLI 前面套上 claude-tap（或 `HTTPS_PROXY` 指过去），开始记录真实任务。**注意这会记录全部 prompt 内容——敏感信息不要进 prompt**。macOS 用户可以考虑 `claude-tap build-macos-app` 做成菜单栏应用：Start Monitor 会把临时 base URL 写进 `~/.claude/settings.json` 与 `~/.codex/config.toml`，Stop Monitor 逐字节恢复，强杀后用 `claude-tap monitor-restore` 兜底。

**第四步：diff 调 bug**。agent 行为异常时，对比正常 turn 与异常 turn 的结构化 diff，定位是哪次请求的哪个字段变了——system prompt 截断、tool schema 不匹配、某请求在重试循环里打转，都藏不过这一步。

**不建议做的事**：

- 不要把 trace 传云端。工具的全部价值建立在「本地」上，上传等于主动泄露 prompt；
- 不要多用户共享同一台机器的 trace 库，session 里是别人的 prompt；
- 不要假设脱敏完备。header 有清单，请求体没有；
- 不要把它当常驻监控。它是调试与研究工具，不是 APM。

**覆盖边界**：claude-tap 看的是 agent 发出的 HTTP/WebSocket 流量。工具执行的本机副作用（shell stdout、文件读写）只在它们被塞进 tool result 回传时才出现在 trace 里；provider 内部处理完全不可见。它是 client-side 观测，与服务端 tracing 互补而非替代。Cursor 的 transcript-only 路线还要再窄一层：transcript 里没写的流量，任何模式下都看不到。

对四类读者的落点：agent 开发者用它验证「设计意图 == 实际发出的请求」；排查异常行为的用户用它拿到第一手证据；团队负责人用它看 token 用量与高频 prompt 模式（真实 trace 顺手就是培训案例）；安全/合规则用它回答「agent 到底往外发了什么」——发 trace 快照给别人前，记得先过一遍脱敏边界。

## 参考资料

- [liaohch3/claude-tap](https://github.com/liaohch3/claude-tap)——MIT，Python 3.11+；2026-10-05 读数 3,260 stars / 282 forks / 9 contributors，最新 release v0.1.145（2026-08-16），累计 137 个 release
- [docs/support-matrix.md](https://github.com/liaohch3/claude-tap/blob/main/docs/support-matrix.md)——client × auth × target × transport 权威组合表（[中文版](https://github.com/liaohch3/claude-tap/blob/main/docs/support-matrix.zh.md)）
- [claude_tap/cli_clients.py](https://github.com/liaohch3/claude-tap/blob/main/claude_tap/cli_clients.py)——`CLIENT_CONFIGS` 客户端矩阵
- [claude_tap/proxy.py](https://github.com/liaohch3/claude-tap/blob/main/claude_tap/proxy.py)——reverse proxy、`SENSITIVE_HEADER_KEYS`、路径白名单
- [claude_tap/forward_proxy.py](https://github.com/liaohch3/claude-tap/blob/main/claude_tap/forward_proxy.py)——CONNECT + TLS MITM 实现
- [claude_tap/certs.py](https://github.com/liaohch3/claude-tap/blob/main/claude_tap/certs.py)——本地 CA 与 macOS login keychain 信任
- [claude_tap/trace.py](https://github.com/liaohch3/claude-tap/blob/main/claude_tap/trace.py)——`TraceWriter` 与统计累积
- [claude_tap/trace_store.py](https://github.com/liaohch3/claude-tap/blob/main/claude_tap/trace_store.py)——SQLite 5 张表
- [claude_tap/viewer.py](https://github.com/liaohch3/claude-tap/blob/main/claude_tap/viewer.py)——单文件 viewer 生成（`LAZY_THRESHOLD`、12 个 JS 模块）
- [claude_tap/upstream.py](https://github.com/liaohch3/claude-tap/blob/main/claude_tap/upstream.py)——上游 URL 拼接与防重复端点
- [docs/guides/agent-trace-viewer.md](https://github.com/liaohch3/claude-tap/blob/main/docs/guides/agent-trace-viewer.md)——本地 trace viewer 使用指南
- [Phistory（WEIFENG2333/phistory)](https://github.com/WEIFENG2333/phistory)——claude-tap 下游消费者，capture-only prompt 导出做提示词归档
- [SkillSpector 解读](https://txtmix.com/posts/tech/nvidia-skillspector-agent-skill-security-scanner/) · [Virtue AI 人才战](https://txtmix.com/posts/tech/meta-poaches-virtue-ai-agent-security-talent-war/) · [FTShare SDK](https://txtmix.com/posts/tech/ftshare-python-sdk-financial-data-agent-access-layer/) · [DAO Code](https://txtmix.com/posts/tech/tigicion-dao-code-deepseek-coding-agent-cache-engineering/)（本站系列）
