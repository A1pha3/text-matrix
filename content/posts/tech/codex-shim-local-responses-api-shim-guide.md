---
title: "codex-shim：让 Codex Desktop 支持任意自定义模型"
date: "2026-05-23T03:15:00+08:00"
lastmod: "2026-09-21T11:00:00+08:00"
slug: "codex-shim-local-responses-api-shim-guide"
github_repo: "sybil-solutions/codex-shim"
source_key: "gh:sybil-solutions/codex-shim"
aliases:
  - "/posts/tech/codex-shim-local-responses-api-shim/"
  - "/posts/tech/codex-shim-local-responses-api-shim-codex-desktop/"
description: "codex-shim 在 127.0.0.1:8765 上模拟 OpenAI Responses API，把 Codex 的请求按 slug 路由到 OpenAI chat completions、Anthropic Messages、ChatGPT 订阅或 Cursor 订阅，再把回流翻译回 Codex 的形状。本文按 main 分支源码拆解它的三类文件、四条路由、catalog 能力声明、ASAR picker patch 与环回安全边界，关键行为均在本机实跑验证。"
draft: false
categories: ["技术笔记"]
tags: ["Codex", "OpenAI", "AI 工具", "Python", "BYOK"]
---

# codex-shim：让 Codex Desktop 支持任意自定义模型

## 核心判断

codex-shim 的全部工作可以压成一句话：**在 `127.0.0.1:8765` 上摆一个 Responses 协议的门面，按 slug 查到上游，把请求翻译过去，再把回流翻译回来。** Codex 以为自己在一问一答地调用 OpenAI 的 /v1/responses。实际对面可能是 DeepSeek 的 Anthropic 兼容端点、本机的 Ollama，或者你自己的 ChatGPT 订阅。

值得读它的原因不是"又一个本地代理"。按 README 的说法，Codex Desktop 的模型列表由服务端 Statsig 配置下发，本地没有添加模型的入口；这个项目对此的解法相当粗暴——改掉 Electron 包里的一个 JS 布尔量。粗暴之外它把两件事分得很清楚：**能不能路由**是纯本地 Python 的事，**能不能看见**才轮到那个补丁负责。这个分层是全文的主线。

适合往下读的读者：已经在用 Codex CLI（命令行工具）或 Desktop，手上另有非 OpenAI 的模型 key 或订阅。前提是你不介意为了一个下拉框去重签 macOS 应用。

本文依据 main 分支 `9ef72ee`（2026-08-25，"fix catalog defaults for current Codex"）通读源码。性能与行为结论来自本机 Python 3.12.11 + aiohttp 3.13.2 环境上的实跑。README 与代码冲突的地方一律以代码为准，并在文中标出。

## 目录

1. [核心判断](#核心判断)
2. [系统地图：三类文件、四条出路](#系统地图三类文件四条出路)
3. [装好之后先跑一遍](#装好之后先跑一遍)
4. [配置文件的兼容面比看起来更宽](#配置文件的兼容面比看起来更宽)
5. [catalog 是写给 Codex 的能力声明](#catalog-是写给-codex-的能力声明)
6. [一次真实请求的往返](#一次真实请求的往返)
7. [ChatGPT passthrough 的入口由谁决定](#chatgpt-passthrough-的入口由谁决定)
8. [Cursor 订阅与 Auto Router](#cursor-订阅与-auto-router)
9. [Picker Patch：两段补丁、一次哈希重写](#picker-patch两段补丁一次哈希重写)
10. [环回地址不等于安全](#环回地址不等于安全)
11. [命令、错误与排查](#命令错误与排查)
12. [数字该怎么读](#数字该怎么读)
13. [谁该用，谁可以先等](#谁该用谁可以先等)
14. [五道自测题](#五道自测题)
15. [下一步读哪份代码](#下一步读哪份代码)
16. [项目信息](#项目信息)
17. [参考资料](#参考资料)

---

## 系统地图：三类文件、四条出路

先划清边界，再谈机制。整个系统只有三份文件在流动，请求则只有四条出路。

| 文件 | 谁写 | 谁读 | 装什么 |
|---|---|---|---|
| `~/.codex-shim/models.json` | 你 | shim 每次请求时现读 | 上游模型、baseUrl、凭据 |
| `.codex-shim/`（检出目录内，非家目录） | shim | Codex 与你 | 生成的 catalog、opt-in 配置、pid、日志 |
| `~/.codex/config.toml` | 仅 `enable` / `app` / `model use` | Codex | 一段带标记的托管块 |

第二行是最容易踩的位置歧义：配置**读**家目录的 `~/.codex-shim/`，运行**产物**却写在检出目录下的同名 `.codex-shim/`。`codex-shim doctor` 会把两者的绝对路径都打出来，怀疑找错文件时先看它。

第三条是理解"改不改我的配置"的关键：`generate`、`start`、`stop`、`restart`、`list`、`status`、`doctor`、`codex --` 都不动 `~/.codex/config.toml`；`enable`、`app`、`model use` 会写入托管块。`generate` 结束时打印的那行 `No files under ~/.codex were modified.` 就是这个约定的自检输出。

四条出路的顺序写在 `codex_shim/server.py` 的 `responses()` 里，短路式判定：

```text
Codex Desktop ── POST /v1/responses ──▶ codex-shim (127.0.0.1:8765)
                                          │
                                          ├─ 1. ChatGPT passthrough slug
                                          │     └─▶ chatgpt.com/backend-api/codex/responses
                                          │         Authorization: Bearer <auth.json access_token>
                                          │
                                          ├─ 2. Cursor passthrough slug
                                          │     └─▶ 子进程 cursor-agent --print（CLI OAuth）
                                          │
                                          ├─ 3. 判定为图像生成 / 图像追问
                                          │     └─▶ 强制走 passthrough，无视所选 slug
                                          │
                                          └─ 4. BYOK：按 provider 翻译
                                                ├─ openai / generic-chat-completion-api
                                                │    └─▶ baseUrl/chat/completions（Bearer apiKey）
                                                └─ anthropic
                                                     └─▶ baseUrl/messages（x-api-key: apiKey）
```

第 3 条容易让人意外。只要请求里带了图像生成类工具，或者对话历史里刚生成过图而最新一句是 "describe""look at" 这类话，shim 就把这一轮转给 ChatGPT passthrough。它是一层关键字与历史启发式，不是能力协商。自带密钥（BYOK, bring your own key）的上游通常没有服务端托管的图像生成能力，硬转过去只会 400，作者因此牺牲路由一致性来保住可用性。判断函数是 `server.py` 的 `_needs_image_gen()` 与 `_needs_image_followup()`。

## 装好之后先跑一遍

环境要求只有两条：Python 3.11+（`pyproject.toml` 的 `requires-python`，CI 矩阵跑 3.11 与 3.12），以及唯一运行时依赖 `aiohttp>=3.9`。

```bash
git clone https://github.com/sybil-solutions/codex-shim ~/codex-shim
cd ~/codex-shim
python3 -m pip install --user -e .        # 装出 codex-shim 命令
```

`bin/` 下的三个包装脚本可以直接软链进 `PATH`，但要知道它们的性质：

```bash
mkdir -p ~/.local/bin
ln -sf "$PWD/bin/codex-shim" ~/.local/bin/codex-shim
ln -sf "$PWD/bin/codex-app"  ~/.local/bin/codex-app
ln -sf "$PWD/bin/codex-model" ~/.local/bin/codex-model
```

`bin/codex-shim` 只有六行，实质是给 `python3 -m codex_shim.cli` 把检出目录塞进 `PYTHONPATH`。它不挑解释器，PATH 上的 `python3` 是谁就用谁。这台机器的 `/usr/bin/python3` 停在 3.9，命令照样能跑起来，但 `doctor` 会判一个 FAIL 并以退出码 1 收场。我正是先撞上这条，才看清它的判据。

最小闭环是四步：

```bash
codex-shim generate   # 读 models.json，写 catalog 与 opt-in 配置
codex-shim start      # 后台守护进程，监听 127.0.0.1:8765
codex-shim list       # 打印 slug、显示名、上游 model 与 provider
codex-shim status     # 探一次 /health，顺带报模型数
```

之后有两种接法，选哪种决定了你留下的痕迹：

```bash
codex-shim app .                     # 写托管块进 ~/.codex/config.toml，再启动 Desktop
codex-shim codex -- "总结这个仓库的架构"   # 一次性：10 组 -c key=value 内联传参
```

`codex --` 走 `catalog.py` 的 `codex_config_overrides()`，把 `model`、`model_provider`、`model_catalog_json`、provider 的 `base_url`/`wire_api`/重试与空闲超时等十项拼成参数，配置文件原样不动。想长期用就 `enable`，想撤销就 `disable`：它移除托管块、还原被顶掉的顶层键、停掉守护进程。

## 配置文件的兼容面比看起来更宽

推荐写法是 `models` 数组配 snake_case 字段：

```json
{
  "models": [
    {
      "model": "gpt-5.5",
      "provider": "openai",
      "base_url": "https://api.openai.com/v1",
      "api_key": "sk-…",
      "display_name": "OpenAI GPT-5.5",
      "max_context_limit": 400000
    },
    {
      "model": "claude-sonnet-4-5",
      "provider": "anthropic",
      "base_url": "https://api.anthropic.com/v1",
      "api_key_env": "ANTHROPIC_API_KEY",
      "display_name": "Claude Sonnet 4.5",
      "no_image_support": false
    },
    {
      "model": "llama3.2",
      "display_name": "Ollama Llama 3.2",
      "provider": "ollama"
    }
  ]
}
```

`settings.py` 的加载器实际认的东西多得多，列全是为了你能判断手头的旧配置会不会被静默吃掉：

- 顶层数组名认 `models`、遗留的 `customModels`、launch-model 风格的 `launchModels` / `launch_models`，甚至直接给一个数组。数组元素可以是裸字符串，会被补成 `generic-chat-completion-api` 加 `http://127.0.0.1:11434/v1`。
- 字段名 snake_case 与 camelCase 双认，另认 `name`→`display_name`、`baseURL`→`base_url`、`bearerToken`→`api_key`。
- `provider: "ollama"`、或 baseUrl 里含 `11434` / `ollama` 的行，一律归一为 `generic-chat-completion-api`，缺 baseUrl 时补本地 Ollama 地址。
- 凭据有两条解析路径。写了 `api_key_env` 时，取该环境变量的值，取不到才退回同行的 `api_key` 字面量。没写 `api_key_env` 时，`api_key` 先做 `${VAR}` 环境变量展开，仍为空则依次尝试读 `~/.codex-shim/cursor-api-key` 文件与 `CURSOR_API_KEY`——这条回落链对非 Cursor 模型同样生效。
- slug 由 `slugify()` 从 model 名生成（同一 model 名出现多次时改用 display_name），撞车就补上序号。`glm-4.5` 变成 `glm-4-5`。
- `model`、`provider`、`base_url` 三者缺任一，这一行被跳过，没有任何提示。
- 解析后仍没有 key 的行**不进 catalog**，但会出现在 `codex-shim list` 里并标注 `(missing API key)`。

用上面那份示例配置实跑（把 `api_key` 换成可辨识的哨兵串，并让 `api_key_env` 指向一个不存在的环境变量），真实输出是：

```text
$ codex-shim --settings example.json list
gpt-5-5            OpenAI GPT-5.5  ->  gpt-5.5 (openai)
claude-sonnet-4-5  Claude Sonnet 4.5 (missing API key)  ->  claude-sonnet-4-5 (anthropic)
llama3-2           Ollama Llama 3.2 (missing API key)  ->  llama3.2 (generic-chat-completion-api)

$ codex-shim --settings example.json generate
Generated 3 model entries:
  catalog: /private/tmp/cx/codex-shim/.codex-shim/custom_model_catalog.json
  config:  /private/tmp/cx/codex-shim/.codex-shim/config.toml
No files under ~/.codex were modified.
```

三行配置最后只有 `gpt-5-5` 进了 catalog：另外两行一个 `api_key_env` 指向缺失变量、一个压根没凭据，都被静默过滤。`Generated 3 model entries` 数的是配置行数而不是 catalog 条数，别拿它当"几个模型可用"。想验证凭据有没有外泄也很容易：把上面那句 `generate` 产出的 catalog 文件按哨兵串检索，命中数为 0。

`api_key_env` 指错变量名不会报错，只会让那个模型安静地从 catalog 消失——这一条能解释相当一部分"我明明配了但 picker 里没有"。

## catalog 是写给 Codex 的能力声明

`catalog_entry()` 给每个模型生成三十来个字段，看着啰嗦，实际每一项都对应 Codex 客户端的一个分支决策：能不能发图、要不要走智能体循环（agent loop）、什么时候压缩、把哪个 slug 排在 picker 前面。上面那份示例配置生成的条目，节选如下：

```json
{
  "slug": "gpt-5-5",
  "context_window": 400000,
  "max_context_window": 400000,
  "auto_compact_token_limit": 320000,
  "truncation_policy": {"mode": "tokens", "limit": 64000},
  "priority": 1000,
  "visibility": "list",
  "supports_search_tool": false,
  "supports_parallel_tool_calls": true,
  "input_modalities": ["text", "image"],
  "shell_type": "shell_command",
  "apply_patch_tool_type": "freeform",
  "web_search_tool_type": "text_and_image"
}
```

同一份配置写出的 opt-in provider 文件是 Codex 真正的入口：

```toml
# .codex-shim/config.toml
# Generated by codex-shim. This file is opt-in and is not ~/.codex/config.toml.
model = "gpt-5-5"
model_provider = "codex_shim"
model_catalog_json = "/private/tmp/cx/codex-shim/.codex-shim/custom_model_catalog.json"

[model_providers.codex_shim]
name = "Codex Shim"
base_url = "http://127.0.0.1:8765/v1"
wire_api = "responses"
experimental_bearer_token = "dummy"
request_max_retries = 3
stream_max_retries = 3
stream_idle_timeout_ms = 600000
```

文件顶部的注释就把自己和 `~/.codex/config.toml` 区分开了，这份是 opt-in 的产物。`wire_api = "responses"` 是整套机制的前提：Codex 只会对 Responses 协议说话，翻译才是 shim 的活。`experimental_bearer_token = "dummy"` 也不是随意占位——真实凭据由 shim 在转发时按上游各自的方案现拼，provider 这一层不需要。

数字全部有出处，`catalog.py` 里是硬编码公式：

| 字段 | 取值 |
|---|---|
| `context_window` | 显式 `max_context_limit` 优先；否则按名字猜：含 `claude` 200000、`gpt-5` 400000、`gemini` 1000000，其余 128000 |
| `auto_compact_token_limit` | `max(8000, context × 0.8)` |
| `truncation_policy` | `{"mode": "tokens", "limit": min(64000, max(8000, context × 0.32))}` |
| `priority` | `max(1, 1000 - index)`，BYOK 之间的先后即配置文件里的行序 |
| `shell_type` / `apply_patch_tool_type` | `shell_command` / `freeform` |
| `web_search_tool_type` | `text_and_image` |
| `supports_search_tool` | `false` |
| `supports_parallel_tool_calls` | `true` |
| `input_modalities` | `["text","image"]`；`no_image_support: true` 时降为 `["text"]`，同时关掉 `supports_image_detail_original` |
| `visibility` | 恒为 `"list"` |

上下文靠名字猜这一条会带来意外后果。一个自称 40 万窗口的第三方模型，只要 model 名里不含 `claude`、`gpt-5`、`gemini`，就按 128000 生成压缩阈值。要精确控制就显式写 `max_context_limit`。

`supports_search_tool = false` 也值得留意：BYOK 路由不声明 hosted search 能力，Codex 因此不会期待服务端替它检索；`web_search_tool_type` 却仍写着 `text_and_image`，两者并不矛盾，前者讲"谁去做"，后者讲"什么形态"。

## 一次真实请求的往返

这一节的输入输出都是本机实测，不是示意。做法是在 8899 端口起一个只会应答 chat completions 的假上游（mock），把 shim 指过去。然后按 Codex 的形状发一个带 function tool 的 /v1/responses 请求：

```json
{
  "model": "mock-1",
  "input": [
    {"type": "reasoning", "summary": []},
    {"role": "user", "content": [{"type": "input_text", "text": "read a.py"}]}
  ],
  "tools": [
    {"type": "function", "name": "read_file", "description": "read",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}}
  ]
}
```

上游实际收到的请求体：

```json
{
  "model": "mock-1",
  "messages": [{"role": "user", "content": "read a.py"}],
  "tools": [{"type": "function",
             "function": {"name": "read_file", "description": "read",
                          "parameters": {"type": "object",
                                         "properties": {"path": {"type": "string"}}}}}],
  "stream": false
}
```

五处变化逐个说明：

- `tools` 从 Responses 的平铺形状变回嵌一层 `function` 的形状，`name`/`description`/`parameters` 原样搬。这一条是桥接里最不起眼却最要紧的地方，形状错了上游就当没这回事。
- 请求 `input` 里那条 reasoning 项没有出现在 `messages` 里，被丢掉了。也就是说这条路由不向上游重放上一轮的思考内容——Anthropic 那条桥另有续读机制，下一节会讲。
- `model` 回填成 shim 的 slug，不是上游模型名；回复里写的也是 `mock-1`，Codex 看不出对面换过后端。
- `stream` 由 shim 补齐。
- 认证头是 `Authorization: Bearer sk-mock-123`，来自配置文件，转发时现取。

mock 回一个 `tool_calls` 加 `reasoning_content`，shim 返回给 Codex 的是：

```json
{
  "id": "cmp1", "object": "response", "status": "completed", "model": "mock-1",
  "output": [
    {"id": "reasoning_0", "type": "reasoning", "status": "completed",
     "summary": [{"type": "summary_text", "text": "先看一下文件"}]},
    {"id": "call_1", "type": "function_call", "status": "completed",
     "call_id": "call_1", "name": "read_file", "arguments": "{\"path\": \"a.py\"}"}
  ],
  "usage": {"input_tokens": 11, "output_tokens": 7, "total_tokens": 18}
}
```

`usage` 的键名做了映射（`prompt_tokens`→`input_tokens`、`completion_tokens`→`output_tokens`），这直接决定 Codex 会不会按累计量触发自动压缩。`reasoning_content` 被包成一条 reasoning 项。整轮请求在 `.codex-shim/shim.log` 里留一行摘要，形状是：

```text
[req] /v1/responses model='mock-1' stream=None tools=1 (['read_file']) input=2 (['reasoning', 'user'])
```

摘要级是刻意的：默认不落完整提示词（prompt），也不落 key。

一次工具往返还差后半程。Codex 下一轮会把 `{"type": "function_call", ...}` 和 `{"type": "function_call_output", ...}` 两类条目塞回 `input`，`translate.py` 再把连续的 `function_call` 合并成一条带 `tool_calls` 的 assistant 消息、把 `function_call_output` 变成 `{"role": "tool", "tool_call_id": ..., "content": ...}`；Anthropic 侧对应 `tool_use` 与 `tool_result` 两种块。这条回路走通，第三方模型才算待在智能体循环里；走不通，模型只能把调用意图写成正文，也就是排查章节里那条"工具调用变成一段文本"。

同一个 slug 换成 Anthropic 形状打 `/v1/messages`，拿回来的也是 Anthropic 形状：`content` 里是 `thinking` 与 `text` 两块，`stop_reason` 为 `end_turn`，`usage` 用 `input_tokens`/`output_tokens`。这条桥反过来也成立——shim 既收 Responses 也收 Messages，OpenAI 兼容上游会被二次翻译。

Anthropic 的 extended thinking 块要靠签名续读，第三方端点给不出真签名。shim 的做法是自己编码：前缀 `anthropic-thinking-v1:`，后面接 base64url 的思考内容，回流时按同一前缀识别并解码。`strip_think()` 另外会把 `<think>…</think>` 这类混进正文的片段剥掉。

四类失败有固定出口，排查时按状态码分辨即可：

| 状态 | 响应文本 | 触发 |
|---|---|---|
| 404 | `Unknown model slug/model: <x>` | slug 与 model 名都查不到，通常是改配置后没重新 `generate` |
| 401 | 缺 key 提示 | 路由命中了，但该行没有凭据 |
| 403 | `Forbidden: Host header not allowed` | Host 头不在环回白名单内 |
| 502 | `Unsupported model provider: <x>` | provider 三种之外的值 |

需要划清的边界：shim 只翻译工具调用的参数结构（schema）、只回传工具输出。`computer_use`、`local_shell`、`apply_patch`、`web_search` 这四类 Responses 原生工具在 BYOK 路由上会降级成普通 function tool，但**执行动作的始终是 Codex**。上游模型不吐合法 JSON 参数，翻译层也救不回来。

## ChatGPT passthrough 的入口由谁决定

条件只有一个：`~/.codex/auth.json` 里 `tokens.access_token` 非空。判据写在 `settings.py:39` 的 `chatgpt_passthrough_available()`，没有 `auth_mode` 参与判断。

条目也不止一个。shim 先读 `~/.codex/models_cache.json`，把其中 slug 以 `gpt-` 或 `codex-` 开头、且 `visibility` 不是 `hidden` 的模型全量搬进 catalog；读不到缓存文件才退回内置的七个 slug 兜底表（`gpt-5.5`、`gpt-5.4`、`gpt-5.4-mini`、`gpt-5.3-codex`、`gpt-5.3-codex-spark`、`gpt-5.2`、`codex-auto-review`）。

在这台机器上实测，本地缓存列出了七个模型，catalog 里便如实长出一串：

```text
['gpt-6-astra', 'gpt-reserve', 'gpt-5.6-sol', 'gpt-5.6-terra', 'gpt-5.6-luna', 'gpt-5.5', 'codex-auto-review']
```

`gpt-5.5` 被单独抬到 `priority: 10000` 并带 `isDefault: true`，其余沿用缓存里的排序值与 `context_window`（这里全是 272000，而不是内置兜底条目的 400000）。所以 passthrough 面板长什么样，取决于你这台机器的 Codex 客户端拉到过什么，不由 shim 决定。

这条事实还有副作用：仓库自带的 `tests/test_server.py::test_api_models_includes_chatgpt_when_auth_present` 断言 `/api/models` 第一个是 `gpt-5.5`，却把 `~/.codex/models_cache.json` 留作真实路径去读。在这台机器上它是唯一失败的用例（Python 3.12.11 下 182 通过 1 失败），失败原因是测试没隔离环境，不是路由错了。

两个兼容与关闭行为：

- 老配置里的 `openai-gpt-5-5` 仍被认作 passthrough 别名（`is_chatgpt_passthrough_slug()` 对 `openai-gpt-` 前缀直接放行），但发往上游的 model 会被改写成 `gpt-5.5`。
- `CODEX_SHIM_DISABLE_CHATGPT=1` 已经实现，是 `chatgpt_passthrough_available()` 的第一道检查，接受 `1`/`true`/`yes`/`on`。

`codex logout` 之后这些条目会在下一次 `generate` 时整体消失。作者的解释写在 README 里：宁可让 picker 少一项，也不留一个必然 401 的选项。passthrough 的请求体基本原样转发，只改 model 名，并把 ChatGPT 账号 id 随头带上。它走的是订阅配额，不是自带密钥。

## Cursor 订阅与 Auto Router

这两个是 6 月加进来的能力，都沿用同一条设计约束：**订阅态能用的时候才 advertise**。

Cursor/Composer passthrough 的 slug 是 `composer-2-5`，上游模型名 `composer-2.5`。它不打 HTTP 端点，而是为每个请求拉起 `cursor-agent --print` 子进程、解析其 `stream-json` 输出，用 CLI OAuth 会话计费。几处细节透露出作者对踩坑的态度：鉴权探测结果缓存 30 秒，免得每个请求都新开一个进程；子进程环境里显式 `pop("CURSOR_API_KEY")`，防止一个残留的控制台 API key 悄悄把订阅计费改成按量计费；Responses 里的图片会被替换成 `[image omitted for cursor-agent bridge]` 占位文本；`scripts/codex-shim-install-cursor-composer` 是个可选的一键接入脚本。

Auto Router 则往 picker 里加一个虚拟模型 `codex-auto`（显示名 `Auto (smart routing)`，`priority` 12000，排在所有条目最前）。`docs/AUTO_ROUTER.md` 开头就把目标摆明了：在不牺牲最强模型的前提下把成本压下来——琐碎轮次给便宜模型，硬骨头升级到强模型，而且只用你已经配好的那些。开关是 `models.json` 里一个可选的 `router` 块：

```jsonc
{
  "router": {
    "enabled": true,
    "classifier": "minimax-m3",
    "threshold": 0.7,
    "default": "minimax-m3",
    "cache": true,
    "candidates": [
      {"slug": "minimax-m3", "cost": 0.3, "supports_images": false,
       "card": "Cheap, fast. Single-file edits, codegen, simple refactors."},
      {"slug": "opus", "cost": 5.0, "supports_images": true,
       "card": "Frontier. Big multi-file refactors, hard debugging, images."}
    ]
  }
}
```

选路规则可以完整背下来。拿一个你指定的便宜模型当 classifier，让它对每个候选打 0.0 到 1.0 的分（"这次任务一次做对的概率"），然后在**过线候选里挑 cost 最小的**；一个都没过线就取最高分；带图任务里 `supports_images: false` 的候选分数直接归零；classifier 缺失、超时、返回垃圾，一律回落到 `default`，`default` 不在候选池就用最便宜的。缓存键是 `(是否带图, hash(最新一条用户文本))`，256 条写满就整表清空——不是 LRU，长会话里可能出现同任务重复分类。

三个数字：`threshold` 默认 0.7，classifier 调用超时 12.0 秒、`max_tokens` 600，任务文本超过 6000 字符时只保留头 3000 与尾 3000。

关键取舍是 classifier 看不到价格：capability card 里不注入 cost，成本只在过线后当决胜项用，避免"越贵分越高"的自证。`router.py` 因此是纯函数模块，网络调用由 `server.py` 注入，整套逻辑可以离线测。仓库为此留了 `examples/auto_router_demo.py`，起一个 mock 多后端、跑真 shim、不需要 key 和网络。实跑结果：

```text
#  Task                                         Classifier scores                Routed to      Cost
1  add a docstring to the foo() helper          cheap=0.90 mid=0.92 strong=0.95  cheap          $0.3
2  write a CRUD REST endpoint with tests        cheap=0.50 mid=0.85 strong=0.95  mid            $1.0
3  refactor the auth module across 8 files      cheap=0.40 mid=0.55 strong=0.95  strong         $5.0
4  what does this screenshot show?              cheap=0.90 mid=0.92 strong=0.95  strong         $5.0
5  (repeat task #1)                             served from cache                cheap          $0.3
Classifier was called 4 times for 5 requests (caching saved 1).  RESULT: PASS
```

第 4 行是硬约束的结果，不是评分的结果：cheap 与 mid 分数更高，但不支持图像，被直接归零。第 3 行走的是另一条分支——cheap 0.40 与 mid 0.55 都没过 0.7 这根线，只有 strong 过线，于是没有"挑最便宜"的余地。规则可以这样记：过线者多于一个时才谈成本，过线者唯一时就直接用。相关环境变量：`CODEX_SHIM_DISABLE_ROUTER`、`CODEX_SHIM_ROUTER_LOG`、`CODEX_SHIM_ROUTER_TIMEOUT`、`CODEX_SHIM_ROUTER_MAX_TOKENS`。

## Picker Patch：两段补丁、一次哈希重写

README 把隐藏行为归因于 Codex Desktop 的服务端 Statsig 配置：一个 `use_hidden_models` 开关，白名单外的 slug 一律不下发，本地 catalog 写了也白写。这个归因读者无法自行复核，但补丁的落点可以佐证——`catalog.py` 把 `visibility` 恒置为 `"list"`，说明拦截不在 catalog 这一层。于是只剩一条路：改客户端。

打包后的 JS 里那一处判断是 `` let u=c.useHiddenModels&&o!==`amazonBedrock`, ``，命中后由 `u` 决定要不要过滤隐藏项。补丁把它改成 `` let u=!1, ``，即永远不带隐藏过滤；picker 于是只看本地 `hidden` 标志，而 shim 生成的 catalog 从不设置它。`amazonBedrock` 那个例外被保留了，说明改的是判断而不是顺手清空整段逻辑。

`codex-shim patch-app` 打的是两段，第二段容易被忽略：侧栏的 `listRecentThreads()` 传的是 `modelProviders:null`，把 Codex 路由到 `codex_shim` 这个 provider 之后，历史会话会被过滤成空白列表，所以同时改成 `modelProviders:[]`。

手工流程与 CLI 流程不等价，这点必须说清：

- README 的手工步骤用 `npx --yes @electron/asar` 加一条字面量 `sed`；`patch-app` 内部调的是 `npx --yes asar`，needle 则是正则。
- 正则容忍变量名重排（`(?P<lhs>(?:let )?\w+=)` 与 `\w+\.useHiddenModels|\w+`），找文件时按 `models-and-reasoning-efforts-*.js` → `model-queries-*.js` → `*.js` 逐级放宽，不绑定文件名。
- 命中数不等于 1 就整个放弃并返回 1，避免误伤同名片段；已打过则打印 "patch is already applied" 并跳过。
- 备份写到 `.codex-shim/` 下：`app.asar.before-codex-shim-model-picker-patch`、一份带内容哈希前 12 位的版本化副本，以及 `Info.plist`。动手前会先退出正在运行的 Codex。
- `/Applications/Codex.app` 不可写时，它用 `ditto` 复制一份到 `~/Applications/Codex.app` 再改，无需 sudo；`restore-app` 从备份还原，同样 macOS-only，Windows/Linux 上直接返回 1。

哈希这一步漏掉就会崩，症状是启动即 `EXC_BREAKPOINT`。Electron 的 `ElectronAsarIntegrity` 存的**不是整个 app.asar 的 SHA-256**，而是 ASAR 归档 JSON 头部的 SHA-256。算法是：读前 16 字节按 `<4I` 解出四个 uint32，取第四个当 JSON 长度，再对那么长的字节求哈希。

```bash
python3 - "$APP/Contents/Resources/app.asar" <<'PY'
import struct, hashlib, sys
with open(sys.argv[1], 'rb') as f:
    data_size, header_size, _, json_size = struct.unpack('<4I', f.read(16))
    header_json = f.read(json_size)
print(hashlib.sha256(header_json).hexdigest())
PY
```

拿到哈希后改 `Info.plist` 的 `ElectronAsarIntegrity:Resources/app.asar:hash`，再 ad-hoc 重签（`codesign --force --deep --sign -`）。`patch-app` 用 `plistlib` 完成同样的事，比 `PlistBuddy` 更稳，因为它写的是解析后的结构而非文本。

组合补丁在 Codex Desktop `26.519.41501` / `codex-cli 0.133.0-alpha.1`（macOS arm64）上验证过。minified 变量名一改，针脚就得重对。README 的 Limitations 段自己也承认这份补丁 "version sensitive by nature"。

## 环回地址不等于安全

监听 `127.0.0.1` 只挡住了外网，挡不住你正在看的网页：一个把自身域名解析到 127.0.0.1 的页面可以直接打本地端口，而同源策略不会拦。这个 shim 手里的东西又很值钱——上游的 API key 和 ChatGPT 的访问令牌（access token），够别人白烧你的额度。

`hostguard.py` 的对策是 Host 头白名单：默认放行 `127.0.0.1`、`localhost`、`::1`，加上你配置的 bind host，再加 `CODEX_SHIM_ALLOWED_HOSTS`（逗号分隔）。其余一律 403，解析时会剥掉端口并正确处理 `[::1]:8765` 这种带方括号的 IPv6。实测用伪造 Host 访问 `/health` 返回 403，正常环回访问返回 200。

改状态的那条路由另有凭据。`/api/switch` 会重写 `~/.codex/config.toml` 里的 `model` 与 provider 显示名，这样 Desktop 界面顶部显示的是 "Kimi K2.6" 而不是笼统的 "Codex Shim"。它还能顺手重启 Codex，因此要求 `X-Codex-Shim-Picker-Token` 头：一个进程启动时用 `secrets.token_urlsafe(32)` 生成、只嵌在 `/picker` 页面里的令牌，服务端用 `secrets.compare_digest` 比对。不带令牌直接 POST 实测返回 `403 {"error": "forbidden"}`。

凭据与日志的边界前面已经验过：key 只留在 `models.json`，catalog 里没有；日志是摘要级。唯一需要额外上心的是 Windows——系统代理（Clash/V2Ray 之类）会把环回流量带走，得配 `NO_PROXY`/`no_proxy` 含 `127.0.0.1,localhost,::1`；`app` 与 `codex --` 会给子进程自动补上，手动跑 `codex.exe` 时不会。如果你把 prompt-catching proxy 摆在 shim 前面，日志与脱敏的责任就整体转移到那一层。

## 命令、错误与排查

全部子命令，取自 `cli.py` 的 argparse 注册表：

| 命令 | 作用 | 是否写 `~/.codex/config.toml` |
|---|---|---|
| `codex-shim generate` | 重生成 catalog 与 opt-in 配置 | 否 |
| `codex-shim list` | 列 slug、显示名、上游与 provider | 否 |
| `codex-shim start` / `stop` / `restart` | 守护进程生命周期 | 否 |
| `codex-shim enable` | 起进程并写托管块 | 是 |
| `codex-shim disable` | 还原托管块并停进程 | 是（移除） |
| `codex-shim status` | 探 `/health` 并报模型数 | 否 |
| `codex-shim doctor` | 只读诊断报告 | 否 |
| `codex-shim model list` | 与 `list` 同一实现 | 否 |
| `codex-shim model use <slug>` | 设默认模型 | 是 |
| `codex-shim codex -- <args>` | 内联 `-c` 跑一次 CLI | 否 |
| `codex-shim app [path]` | 启动 Desktop，可带 `-m <slug>` | 是 |
| `codex-shim patch-app` / `restore-app` | macOS picker 补丁与回滚 | 否（改 app 包） |
| `codex-shim opencode-go refresh` | 拉取 OpenCode Go 模型表写入配置 | 否 |

全局参数只有 `--settings` 与 `--port`。`patch-app` / `restore-app` 不吃 `--settings`。

出问题时先跑 `doctor`。它是只读的：不写配置、不启停进程、不碰上游、也不打印 key。报告按十段组织：Python、Dependencies、Codex CLI、Settings、Runtime files、Shim daemon、ChatGPT passthrough、Cursor passthrough、Proxy、Codex config，每行一个 OK/WARN/FAIL/INFO。只有出现 FAIL 才以 1 退出。在 3.9 解释器上跑，第一段就给出 `FAIL version: 3.9.6 / codex-shim requires Python 3.11+`，这条比任何手工排查都快。

按现象分类的常见故障：

- **picker 只有 `default`。** `generate` 后跑 `model list` 确认 catalog 有内容；有内容仍不渲染就是白名单，走 `patch-app`。Windows Store/MSIX 版本更严，可能把 `model = "<自定义 slug>"` 改回 `gpt-5.5` 并自行补上 `[tui.model_availability_nux]` 条目；这属于 Desktop 的 allowlist 行为而非 shim 路由，此时改用 `codex-shim codex --`，`patch-app` 对 `C:\Program Files\WindowsApps` 下的包无效。
- **模型在列表里但请求 404。** slug 不在当前 catalog 里，改完配置必须重新 `generate`。
- **上游 401/403。** key 错、过期、或该 provider 还缺自定义头（`extra_headers` 可补）；passthrough 则要重新 `codex login`。
- **工具调用变成一段文本。** 先用 passthrough 确认 Codex 本身在发 tools，是的话问题在上游不支持原生 tool call 或流式参数残缺 JSON；`shim.log` 里的 `tools=N (['name'])` 可以直接看出发了几个。
- **图片请求报错。** 给该模型加 `no_image_support: true` 再 `generate`，否则 Codex 会把 `image_url` 发给纯文本上游。
- **`list` 退出码 1 并报 No models available。** 既没配置模型也没登录，两条路任选一条。
- **打完补丁崩溃。** `restore-app` 回滚，再核对针脚是否随版本变了。

彻底重置更简单：`codex-shim stop`，删掉检出目录下的 `.codex-shim/`，再 `generate` + `start`。

## 数字该怎么读

README 里唯一一处性能表述是这样的：维护者在自己的内部 Codex 任务上，用 passthrough 加一层 prompt-catching proxy，拿到过"多倍"的计费输入 token 下降，墙钟时间也明显更快。同一句话里也写明了：仓库还没有可复现的基准脚本，请当 anecdata。

这句话的分寸值得学：不要把 "multi-x" 当结论。要自己测，仓库给的协议是同仓库、同提示词、同一条聚焦测试命令，跑基线路由与 shim 路由各一遍，只对比端到端成功的运行。记录项是墙钟时间、请求数、输入/输出 token 与工具调用次数。

```bash
/usr/bin/time -f 'wall=%E cpu=%P max_rss_kb=%M' codex-shim codex -- "你的任务"
```

从这类数字里能读出的是：这条路由在你这台机器、这个模型、这条提示词下的综合表现。读不出来的是翻译层的净开销——一个智能体回合要过几十次模型调用，多一跳 JSON 转换的成本被摊薄到难以单独观测，而它并没有被单独测量过。同理，`stream_idle_timeout_ms = 600000` 只能说明"作者预期真实编码回合会流很久"，不能用来论证 shim 对流式延迟做了什么。

## 谁该用，谁可以先等

按这个顺序决定：

1. 只用 Codex 内置模型、也不打算换：不需要它。
2. 想在一个 CLI 回合里试一次第三方模型：`codex-shim codex --`，一次性内联参数，配置文件不动，零残留。
3. 想让 Desktop 的 picker 长期带着自定义模型：准备 `models.json`，`generate` + `start`，再 `codex-shim app`（或 `enable`），并接受"配置里有托管块"这件事，随时可 `disable` 撤走。
4. 非要在 macOS Desktop 的界面上看到自定义条目：`patch-app`。这一步的代价是应用签名与版本耦合，Codex 每次自动更新都可能让你重来。
5. 只有 ChatGPT 订阅、没有别的 key：可以只用 passthrough，`models.json` 不存在也能起 catalog。
6. 想让任务自动落到不同模型：先读 `docs/AUTO_ROUTER.md`，跑 `examples/auto_router_demo.py` 看懂选路，再打开 `router` 块。

不适合的场景也说清：需要团队共享凭据的人（这是单用户本地工具，没有鉴权层）；要求工具调用零损耗的人（hosted tool 的高保真路径只有 passthrough）；以及不能接受改动官方应用二进制的人。

## 五道自测题

1. `codex-shim app .` 和 `codex-shim codex -- "…"` 在改不改 `~/.codex/config.toml` 上有什么区别？
   前者写托管块（`install_codex_config`），后者拼十组 `-c key=value` 传给 CLI，不落地。想复原前者用 `disable`。

2. 为什么 catalog 里没有你在 `models.json` 中写下的第三行模型？
   最可能是那行没有解析到任何凭据，被 `usable_byok_models()` 过滤掉了；`list` 里它会出现并标 `(missing API key)`。缺 `model`/`provider`/`base_url` 任一项也会消失，但连 `list` 都不出。

3. passthrough 面板里出现哪些 GPT 模型由什么决定？
   `~/.codex/models_cache.json` 的内容（slug 前缀 `gpt-`/`codex-` 且未被标记隐藏）；没有该文件才用内置七项兜底表。前提是 `auth.json` 里有 `tokens.access_token`。

4. 打了 picker 补丁没更新 `ElectronAsarIntegrity`，会看到什么？
   启动即 `EXC_BREAKPOINT` 崩溃。完整性字段是 ASAR 归档 JSON 头部的 SHA-256，不是整文件哈希。

5. Auto Router 里评分 0.9 的候选一定会被选中吗？
   不一定。带图任务时 `supports_images: false` 会被直接归零；过线候选中还要挑 `cost` 最小的那一个。

## 下一步读哪份代码

顺序按"先边界，再机制，最后兜底"：

- `codex_shim/settings.py`：前 40 行是全部默认值（配置路径、host、port、`gpt-5.5`），`_model_rows()` 是 schema 兼容面的真相。
- `codex_shim/server.py` 的 `responses()`：三十来行，四条出路的真实顺序。
- `codex_shim/catalog.py` 的 `catalog_entry()`：Codex 客户端到底在读取什么。
- `codex_shim/translate.py`：Responses 与 chat completions / Messages 三向转换，`SHIM_ENCRYPTED_CONTENT_PREFIX` 在这里。
- `codex_shim/router.py`：选路是纯函数，classifier 由外部注入，`resolve_auto()` 的每条分支都落回一个候选。
- `codex_shim/hostguard.py`：66 行，把环回安全这件事讲完。
- `tests/test_router.py` 与 `tests/test_router_integration.py`：合计 51 个用例，比任何文档都清楚地写着容错边界。

## 项目信息

- 仓库：[sybil-solutions/codex-shim](https://github.com/sybil-solutions/codex-shim)（`pyproject.toml` 的 Homepage 仍写 `0xSero/codex-shim`，GitHub API 会把后者解析到前者，即仓库做过 owner 转移）
- 分析基线：main `9ef72ee`，2026-08-25；30 个提交，首个 2026-05-22；无 tag、无 release，`pyproject.toml` 版本停在 `0.1.0`，CHANGELOG 自述 pre-1.0 不遵循语义化版本
- 规模：`codex_shim/` 十个模块共 6,779 行，`tests/` 九个文件 4,219 行，183 个用例；本机 Python 3.12.11 下 182 通过、1 失败（原因见上文，测试未隔离 `~/.codex/models_cache.json`）
- 依赖：运行时仅 `aiohttp>=3.9`；可选 `[dev]` 为 `pytest>=8` 与 `pytest-asyncio>=0.23`；CI 矩阵 Python 3.11 / 3.12
- 许可：MIT（`LICENSE` 与 pyproject classifier 一致）；Codex Desktop 是 OpenAI 商标，项目声明与之无关联
- 热度：2026-09-21 通过 GitHub API 查得 1,064 stars、106 forks，仓库体积 112 KB
- 已验证环境：Codex Desktop 26.519.41501 / codex-cli 0.133.0-alpha.1，macOS arm64

## 参考资料

- [sybil-solutions/codex-shim](https://github.com/sybil-solutions/codex-shim) — README、`docs/AUTO_ROUTER.md`、`docs/subscription-integration.md`、CHANGELOG
- 源码逐文件：`codex_shim/{settings,catalog,server,translate,router,hostguard,cursor_passthrough,cli}.py`
- `examples/auto_router_demo.py` — 离线选路验证脚本，本文引用的运行输出来自它
- [electron/asar](https://github.com/electron/asar) — ASAR 归档的头部布局，`ElectronAsarIntegrity` 哈希口径的出处
