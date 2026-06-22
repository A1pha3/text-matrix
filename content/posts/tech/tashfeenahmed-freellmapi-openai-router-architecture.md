---
title: "FreeLLMAPI 深度拆解：把 16 个免费 LLM 厂商聚合成一个 OpenAI 兼容端点的代理路由器"
date: "2026-06-22T15:05:40+08:00"
slug: "tashfeenahmed-freellmapi-openai-router-architecture"
categories: ["技术笔记"]
tags: ["LLM", "OpenAI 兼容", "API 路由", "架构分析", "TypeScript"]
description: "FreeLLMAPI 是一个本地自托管的 OpenAI 兼容代理,把 16 个 LLM 厂商的免费层聚合在 /v1/chat/completions 后面,核心难点在跨厂商的协议翻译、Per-key 限速追踪和中途切换的 Context Handoff。"
---

# FreeLLMAPI 深度拆解:把 16 个免费 LLM 厂商聚合成一个 OpenAI 兼容端点的代理路由器

## 核心判断

FreeLLMAPI 是一个**本地自托管的 OpenAI 兼容代理**,在 `:3001` 后面把 16 个 LLM 厂商(Google、Groq、Cerebras、Mistral、OpenRouter、GitHub Models、Cloudflare、Cohere、Z.ai、NVIDIA、HuggingFace、Ollama Cloud、Kilo、Pollinations、LLM7、OVH AI Endpoints)的免费层聚合起来,统一对外暴露 OpenAI、Responses、Anthropic Messages、Embeddings、Image、Audio 六种线缆格式(wire format)。

它的工程难点**不在 SDK 适配**,而在这三件事上:

1. **跨厂商语义翻译**——OpenAI 协议没有 grounding 字段,Anthropic 协议用 `anthropic-version` 头,Google Gemini 用 `functionDeclarations`,三种协议要在一台机器里相互转换。
2. **Per-key 限速追踪**——16 个厂商 × 每个厂商各自的 RPM/RPD/TPM/TPD 上限,必须实时计算"下一个还没爆的 key"才能稳定路由。
3. **中途切换的 Context Handoff**——多轮对话中途 429 了,要切到另一个 model,新 model 不知道前面聊了什么,需要注入一条紧凑的 system 消息告诉它"你接的是别人"。

理解了这三件事,FreeLLMAPI 99% 的设计取舍就有了解释。

## 系统地图

```
┌──────────────────┐   Bearer freellmapi-…   ┌─────────────────────────┐
│  OpenAI SDK /    │ ──────────────────────▶ │  Express proxy (:3001)  │
│  curl / any      │ ◀────────────────────── │  /v1/chat/completions   │
│  OpenAI client   │      streamed tokens    └────────────┬────────────┘
└──────────────────┘                                      │
                                                          ▼
                             ┌────────────────────────────────────────────────┐
                             │  Router                                        │
                             │   1. Pick highest-priority model that          │
                             │      (a) has a healthy key and                 │
                             │      (b) is under all its rate limits.         │
                             │   2. Decrypt key, call provider SDK.           │
                             │   3. On 429/5xx → cooldown + retry next model. │
                             └────────────────────────────────────────────────┘
                                          │
   ┌──────────────┬────────────┬──────────┴─────────┬─────────────┬──────────┐
   ▼              ▼            ▼                    ▼             ▼          ▼
 Google         Groq        Cerebras           OpenRouter        HF       …10 more
```

代码组织(仓库 `server/src/`):

| 模块 | 职责 |
| --- | --- |
| `services/router.ts` | 选 model:健康 key + 没爆限速 + 高优先级 |
| `services/ratelimit.ts` | RPM/RPD/TPM/TPD 计数器,SQLite 持久化,cooldown 状态机 |
| `services/health.ts` | 周期探针,标记 key 为 `healthy`/`rate_limited`/`invalid`/`error` |
| `providers/*.ts` | 每厂商一个文件,实现 `Provider` 基类的 `chatCompletion()` 和 `streamChatCompletion()` |
| `db/index.ts` | 种子数据:厂商 → 模型清单,初始限速配置 |
| `client/` | React + Vite + shadcn/ui 仪表盘 |

存储层:better-sqlite3 + **AES-256-GCM envelope encryption**——上游厂商 API key 在落盘前用 `ENCRYPTION_KEY` 加密,请求时解密到内存、用完即弃。

## 协议层:6 种 API 形态的翻译矩阵

| 路径 | 线缆格式 | 翻译规则 |
| --- | --- | --- |
| `POST /v1/chat/completions` | OpenAI | 透传,Tool/Stream/Image 全部走 OpenAI 协议 |
| `POST /v1/responses` | OpenAI Responses (Codex CLI) | 翻译 shim,完整 SSE 流 + tool calls |
| `POST /v1/messages` | Anthropic Messages | 通过 `anthropic-version` 头内容协商,翻译为内部统一格式,再下到 OpenAI-compatible 厂商 |
| `POST /v1/messages/count_tokens` | Anthropic | 单独实现的 token 计数端点 |
| `POST /v1/embeddings` | OpenAI | 严格 **family 隔离**(见下) |
| `POST /v1/images/generations` | OpenAI | 只下到支持 image 的厂商 |
| `POST /v1/audio/speech` | OpenAI | 只下到支持 TTS 的厂商 |

**`GET /v1/models`** 是内容协商的——带 `anthropic-version` 头时返回 Anthropic 形态的模型列表,否则返回 OpenAI 形态。

`/v1/messages` 的存在意味着 **Claude Code 官方 SDK** 可以直接指向这台机器,详见仓库 README 的"Anthropic / Claude clients"段。

## 边界拆分

### 厂商侧:16 个免费层 + 1 个 custom 槽

- **大厂直连**:Google(Gemini 2.5/3.x)、GitHub Models(GPT-4o/4.1)、Cloudflare Workers AI、NVIDIA NIM
- **OpenAI 兼容层**:Groq、Cerebras、Mistral、OpenRouter、HuggingFace、Cohere compat、Ollama Cloud
- **匿名层**:Pollinations、LLM7、OVH AI Endpoints(无需 API key)
- **Specialty**:Z.ai(智谱海外实体)、Kilo Gateway
- **Custom**:任何 OpenAI 兼容端点(llama.cpp、LM Studio、vLLM、本地 Ollama)

### 路由侧:Per-(platform, model, key) 限速账本

`rate_limited` 状态在 `services/ratelimit.ts` 维护:

- **4 个维度计数**:RPM(每分钟请求数)、RPD(每天请求数)、TPM(每分钟 token)、TPD(每天 token)
- **key 级别**:同一个厂商可以塞多个 key,Router 永远选"还剩额度"的那个
- **cooldown**:429 触发的 key 进短期冷却,cooldown 期内 Router 跳过这个 key

### 会话侧:Sticky Session

- 多轮对话在 30 分钟内固定同一个 model
- 原因:中途切 model 会带来"对话风格突变 + 上下文理解断层",sticky session 是用"短期不灵活"换"长期不幻觉"
- session key:`X-Session-Id` 头优先,否则 SHA-1(user 第一条消息)

### 加密侧:AES-256-GCM envelope

- 启动必须设置 `ENCRYPTION_KEY`(32 字节 hex)
- 上游厂商 key 加密后存 SQLite,请求时解密到内存,只活在该次请求生命周期内
- **fallback 仅在 `DEV_MODE=true` 且非 `production` 时启用**——README 明确警告不要用 fallback 配真实厂商 key

## 关键机制

### 机制 1:Fallback 链,最多 20 次尝试

Router 的核心循环:

```
for attempt in 1..20:
    model = pick_highest_priority(healthy_keys_under_caps)
    if not model: return 503
    try:
        return call_provider(model)
    except (429, 5xx, timeout):
        cooldown(model.key, duration=backoff(attempt))
        continue
```

最多 20 次后放弃。`X-Fallback-Attempts: N` 响应头告诉你这次请求跨了几个 model。

### 机制 2:Embeddings 严格 family 隔离

Embedding 路由**故意不做跨 model 切换**。原因:不同模型产出的向量空间不兼容,静默切 model 会把上层的 vector store 污染掉。

`/v1/embeddings` 接受三种 `model` 取值:

- `auto`——用 dashboard 配置的默认 family
- family name,如 `bge-m3`
- 厂商特定 ID,自动 resolve 到它的 family

内置 family(摘 README 表格):

| Family | 维度 | Failover 顺序 |
| --- | --- | --- |
| `gemini-embedding-001`(默认) | 3072 | Google |
| `text-embedding-3-large` | 3072 | GitHub Models |
| `bge-m3` | 1024 | Cloudflare → Hugging Face |
| `embeddinggemma-300m` | 768 | Cloudflare |

### 机制 3:Vision 自动路由

`/v1/chat/completions` 检测到请求里有 `image_url` content block → Router **只在 vision-tagged models 里选**,忽略纯文本 model。当前 vision 集合:Gemini 2.5/3.x、Llama 4 Scout/Maverick(Groq/NVIDIA)、GLM-4.6V Flash(NVIDIA OpenRouter)、Nemotron Nano 12B VL、GitHub GPT-4o/4.1。

如果 Fallback Chain 里没有任何 vision model,直接返回 `422` + `code: "no_vision_model"`,不静默丢图。

### 机制 4:Anthropic → OpenAI 翻译

`/v1/messages` 接 Claude Code 请求后,内部流程:

1. 收到 `anthropic-version: 2023-06-01` 头 → 内容协商,确定回应 Anthropic 形态
2. Claude model name 解析:dashboard 的 `Keys → Anthropic` 页里把 `opus/sonnet/haiku/default` 四个 family 映射成 `auto` 或 pinned model
3. 把 Anthropic 的 `messages`/`system`/`tools` 翻译成内部统一格式
4. 走 Router 选一个 OpenAI-compatible 厂商
5. 返回时把 OpenAI 的流式 chunk 翻译回 Anthropic 的 SSE 事件

### 机制 5:Context Handoff on Model Switch

多轮对话中途 fallback 触发时,Router 在出站请求里塞一条 system message:

```
FreeLLMAPI context handoff:
You are taking over an ongoing conversation from another model (groq:llama-3 → google:gemini-flash).
Continue the user's task using the conversation context already provided in this request.
Do not restart the task, re-ask already answered setup questions, or discard prior tool results.
Respect the user's latest message as the highest-priority instruction.
```

- 默认 **关**,要开就在 `.env` 设 `FREELLMAPI_CONTEXT_HANDOFF=on_model_switch`
- 消息存在内存(TTL 3 小时),不落盘
- 只在 model 真切换时注入,同 model 续接或第一条请求时不注入
- 限制:**恢复不了厂商内部的隐藏 state**,只能"看到请求里有的"

## 任务流案例

### 案例 A:Claude Code → FreeLLMAPI → Groq

```
$ export ANTHROPIC_BASE_URL=http://localhost:3001
$ export ANTHROPIC_AUTH_TOKEN=freellmapi-your-unified-key
$ claude
> 帮我写一个 Python script 拉 GitHub trending daily 榜单
```

走到 FreeLLMAPI 内部的流程:

1. `POST /v1/messages` 收到,带 `anthropic-version: 2023-06-01` + `x-api-key: freellmapi-…`
2. Anthropic wire format → 内部统一格式(把 `messages[].content` 数组化、`system` 提到顶)
3. Router 选 `groq:llama-3.3-70b-versatile`(高优先级 + 健康 key + 未爆 cap)
4. AES-256-GCM 解密 Groq key,放内存
5. 调 Groq SDK,带流式
6. 收到 SSE chunk → 翻译成 Anthropic 形态(`message_start`/`content_block_start`/`content_block_delta`/`message_delta`/`message_stop`)
7. Claude Code 收到 Anthropic 形态的流式响应,显示打字机效果
8. `X-Routed-Via: groq/llama-3.3-70b-versatile` 响应头

### 案例 B:Groq 429 → 自动切 Cerebras

1. Groq 触发 429(`rate_limit_exceeded`)
2. `services/ratelimit.ts` 把这个 (platform=groq, model=llama-3.3, key=hash) 标 cooldown 60 秒
3. Router 走 Fallback Chain 下一个:Cerebras Qwen3 235B
4. Cerebras 健康、未爆 cap,Router 调它
5. 返回成功,响应头 `X-Fallback-Attempts: 1`
6. 60 秒后 Groq cooldown 解除,下次请求优先 Groq

### 案例 C:Embeddings 同 family failover

```
$ curl http://localhost:3001/v1/embeddings \
    -H "Authorization: Bearer freellmapi-..." \
    -d '{"model": "text-embedding-3-small", "input": "hello world"}'
```

1. `text-embedding-3-small` 是 GitHub Models 的 1536 维 family
2. GitHub Models 健康 → 调它,返回 1536 维向量
3. 如果 GitHub Models 429 → cooldown → 切到同 family 的备份厂商(本例默认只有 GitHub Models 提供该 family)
4. **不会**切到 Google gemini-embedding-001(3072 维,会污染 vector store)→ 直接 503 + 明确的"family 不可用"错误

## Benchmark/测什么、不能推出什么

README **没有**内部 benchmark 数据。任何关于"哪个 provider 更快/更稳"的结论都需要自己测。

README 自己承认的 trade-off:

- **No frontier models**——免费层封顶在 Llama 3.3 70B / GLM-4.5 / Qwen 3 Coder / Gemini 2.5 Pro,拿不到 GPT-5 / Claude Opus 级
- **"Intelligence degrades as the day progresses"**——强 model(Gemini 2.5 Pro、GitHub GPT-4o)cap 最低,先耗尽,Router 自动降级到更弱 model,UTC 0 点重置
- **Latency 高度可变**——Cerebras / Groq 极快,其他不一定,Router 选"下一个还活着的",不一定选最快的
- **Free tiers change without notice**——厂商随时调 cap,出现 429 / auth 错误就要更新 catalog seed
- **No SLA, by definition**——这是个人实验项目,不是生产推理底座

## 采用建议

### 适合

- 开发者**个人 prototype**——想用 OpenAI/Anthropic SDK 但不想付费
- **多 free tier 试玩**——一次性把 Google + Groq + Cerebras + Mistral 全接上,体验不同 model
- **Claude Code 用户**——不想买 Anthropic API key 又想用 Claude Code,把 `ANTHROPIC_BASE_URL` 指过来
- **本地模型 + 远端混合**——custom 槽接 llama.cpp / LM Studio / vLLM,走同一端点

### 不适合

- **生产 SLA**——README 自己说"by definition" 没有
- **Frontier model**——拿不到 GPT-5/Claude Opus
- **多租户对外服务**——单用户设计,没有 multi-tenant auth
- **过度敏感场景**——厂商 ToS 不一定允许代理(详见 README 的 ToS 审查表,Google/Cohere/Z.ai/NVIDIA 都标了 Caution)

### 上手

最快路径(需要 Docker):

```bash
curl -fsSL https://freellmapi.co/install.sh | bash
```

会创建 `~/freellmapi`、生成 `ENCRYPTION_KEY`、拉 `:latest` 镜像、起容器。

不开 Docker 的本地开发路径:

```bash
git clone https://github.com/tashfeenahmed/freellmapi.git
cd freellmapi
npm install
ENCRYPTION_KEY="$(node -e 'console.log(require(\"crypto\").randomBytes(32).toString(\"hex\"))')"
printf "ENCRYPTION_KEY=%s\nPORT=3001\n" "$ENCRYPTION_KEY" > .env
npm run dev
```

- API + dashboard:http://localhost:3001
- 单独 dev UI:http://localhost:5173
- LAN 访问:`npm run dev:lan`(把 Vite 暴露到 `0.0.0.0`)

### 必读

1. **README 的 "Limitations" 段**——五条 trade-off,逐条对照自己的场景
2. **"Terms of Service review" 表**——16 个 provider 各自的 ToS 边界(Google/Cohere/NVIDIA/Z.ai 标了 Caution)
3. **`ENCRYPTION_KEY`** 一定要设,丢了就解不开 SQLite 里的厂商 key
4. **Premium($19/yr 或 $49 lifetime)**——只想用每月快照就 Free,想用 live feed 升级

## 适用边界

- FreeLLMAPI 自己声明 "personal experimentation, not production"
- 上游厂商 ToS 仍约束你和厂商的关系,代理不会改变 ToS
- 多账号/转售/对外公开暴露是普遍红线
- 缺 frontier model、缺 SLA、缺多租户——这三条是设计选择,不是 bug
