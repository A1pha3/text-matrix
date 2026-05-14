---
title: "mimo2codex：让最新 Codex 无缝接入 MiMo/DeepSeek 的本地代理网关"
date: "2026-05-14T16:15:00+08:00"
slug: "mimo2codex-codex-local-proxy"
description: "深入解析 mimo2codex 0.2.4 的架构设计：Responses API 与 Chat Completions 的双向转换、reasoning_content 多轮透传机制、Provider 路由体系，以及如何用它把最新版 Codex CLI 接入小米 MiMo V2.5 或 DeepSeek V4 Pro。"
draft: false
categories: ["技术笔记"]
tags: ["TypeScript", "API网关", "OpenAI", "MiMo", "DeepSeek", "Codex", "协议转换", "本地代理"]
---

# mimo2codex：让最新 Codex 无缝接入 MiMo/DeepSeek 的本地代理网关

> **项目信息**：https://github.com/7as0nch/mimo2codex | ⭐ 153 | TypeScript | Node.js ≥ 18 | v0.2.4
>
> **核心定位**：纯本地协议网关，将 Codex 的 `Responses API` 实时翻译为上游的 `Chat Completions API`，按 `model` 字段自动路由到 MiMo、DeepSeek 或任何 OpenAI 兼容 provider。**不改任何代码、不重新发包**。

---

## 1. 问题背景：Codex 与 MiMo 的兼容性困局

小米米莫官方 [Codex 集成文档](https://platform.xiaomimimo.com/docs/zh-CN/integration/codex) 只支持 `wire_api = "chat"`，但**最新版 Codex 已经把这个开关变成硬错误**，官方建议是降级 Codex 到 0.80.0——但会丢失 pet 宠物、桌面端新功能和新工具。

mimo2codex 在中间挂一个本地代理，**Codex 用最新版、MiMo 服务端不变**，两边都不用改。

这本质上是 [openrouter](https://openrouter.ai)、[claude-code-router](https://github.com/musistudio/claude-code-router)、[y-router](https://github.com/luohy15/y-router) 的又一次实现——**纯协议网关**，中间层翻译，不碰业务逻辑。

---

## 2. 核心架构：三层协议转换

### 2.1 整体架构图

```
Codex (Responses API)
        │
        ▼
┌──────────────────────────┐
│      mimo2codex          │
│                          │
│  ┌────────────────────┐  │
│  │  server.ts         │  │ ← HTTP 服务入口 (端口 8788)
│  │  路由 + 异常处理    │  │
│  └────────┬───────────┘  │
│           │               │
│  ┌────────▼───────────┐  │
│  │  reqToChat.ts      │  │ ← Responses → Chat Completions 转换
│  │  (请求翻译)         │  │
│  └────────┬───────────┘  │
│           │               │
│  ┌────────▼───────────┐  │
│  │  Provider Registry  │  │ ← MiMo / DeepSeek / Generic
│  │  · 内置 Provider    │  │
│  │  · Generic Loader   │  │
│  └────────┬───────────┘  │
│           │               │
│  ┌────────▼───────────┐  │
│  │  respToResponses   │  │ ← Chat Completions → Responses 转换
│  │  streamToSSE       │  │ ← 流式处理 + SSE 封装
│  └────────────────────┘  │
└──────────────────────────┘
        │
        ▼
上游 Provider (Chat Completions API)
  · MiMo:    api.xiaomimimo.com/v1
  · DeepSeek: api.deepseek.com/v1
  · Generic: 任意 OpenAI 兼容端点
```

### 2.2 请求处理流程（server.ts）

```typescript
// src/server.ts 核心路由逻辑
async function handleRequest(req: IncomingMessage, res: ServerResponse) {
  const body = await readJsonBody<ResponsesRequest>(req);

  // 1. Provider 路由：根据 model 字段选择上游
  const { provider, upstreamModel, rewriteNotice } = selectProvider(body.model);

  // 2. 请求翻译：Responses → Chat Completions
  const chatReq = reqToChat(body, { model: upstreamModel, provider });

  // 3. 调用上游
  const upstreamResp = await callOpenAICompat(cfg, chatReq, signal);

  // 4. 响应翻译：Chat Completions → Responses (流式)
  await pipeChatStreamToResponses(upstreamResp, res, { exposeReasoning });
}
```

**关键设计点**：请求和响应都经过严格翻译，不是简单透传。因为 Codex 的 `Responses API` 和 OpenAI 的 `Chat Completions API` 在数据结构上有显著差异。

---

## 3. 协议转换：Responses ↔ Chat Completions

### 3.1 请求翻译（reqToChat.ts）

Codex 发送的是 `ResponsesRequest`，需要转换为 `ChatRequest` 发给上游 MiMo/DeepSeek。

```typescript
// src/translate/reqToChat.ts 核心逻辑
export function reqToChat(req: ResponsesRequest, ctx: PreprocessCtx): ChatRequest {
  const messages: ChatMessage[] = [];

  for (const item of req.input) {
    if (item.type === "message") {
      // role 转换: developer → system, assistant → assistant
      const role = mapRole(item.role);
      const content = partsToChatContent(item.content, ctx);

      messages.push({ role, content, ... });
    }
  }

  // 工具调用转换: Responses 的 function_call → Chat 的 tool_calls
  if (req.tools) {
    chatReq.tools = req.tools.map(t => ({
      type: "function",
      function: { name: t.name, description: t.description, parameters: t.parameters }
    }));
  }

  // reasoning_content 回传 (关键!)
  // 多轮工具调用时，Codex 会在下一轮把 reasoning_content 回传
  // mimo2codex 必须将之前的 reasoning_content 注入到对应 assistant message
  if (ctx.priorReasoning) {
    // 找到上一条 assistant message，注入 reasoning_content
    injectReasoningContent(messages, ctx.priorReasoning);
  }

  return chatReq;
}
```

### 3.2 响应翻译（respToResponses.ts）

上游返回 `ChatResponse`，需要转换回 `ResponsesObject` 给 Codex。

```typescript
// src/translate/respToResponses.ts
export function respToResponses(
  chat: ChatResponse,
  req: ResponsesRequest,
  opts: RespToResponsesOpts
): ResponsesObject {
  const output: ResponsesOutputItem[] = [];

  // 1. reasoning_content 处理 (最关键!)
  if (message.reasoning_content) {
    // 完整 reasoning 必须存入 encrypted_content
    // Codex 视为 opaque blob，回传时原样返回
    // reqToChat 再注入回 reasoning_content
    output.push({
      type: "reasoning",
      id: newReasoningId(),
      summary: opts.exposeReasoning ? [{ type: "summary_text", text: reasoning }] : [],
      encrypted_content: reasoning,  // ← 关键：全量透传
      status: "completed"
    });
  }

  // 2. content 处理：注入 url_citation 注解
  if (message.content) {
    const annotations = message.annotations?.map(a => ({
      type: "url_citation",
      url: a.url,
      title: a.title,
      snippet: a.summary
    })) ?? [];

    output.push({
      type: "message",
      role: "assistant",
      content: [{ type: "output_text", text: message.content, annotations }]
    });
  }

  // 3. 工具调用转换: Chat 的 tool_calls → Responses 的 function_call
  if (message.tool_calls) {
    for (const tc of message.tool_calls) {
      output.push({
        type: "function_call",
        call_id: tc.id,
        name: tc.function.name,
        arguments: tc.function.arguments,
        status: "completed"
      });
    }
  }

  return { id: newResponseId(), model: req.model, output, ... };
}
```

---

## 4. reasoning_content 多轮透传机制（核心难点）

### 4.1 问题根源

按 [MiMo 官方公告](https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/passing-back-reasoning_content)：

> **每一条带 `tool_calls` 的 assistant message 在后续轮次必须回传原始 `reasoning_content`**，否则 MiMo 直接 **400** `"The reasoning_content in the thinking mode must be passed back"` 或软退化成幻觉（agent 不调工具、自言自语、烧 token）。

### 4.2 失败模式

| 严重程度 | 现象 | 根因 |
|----------|------|------|
| 🔴 硬失败 | MiMo 400 `reasoning_content must be passed back` | 缺少 reasoning_content 字段 |
| 🟡 软退化 | 模型"自言自语"不调工具、编造无关内容 | reasoning 内容丢失导致上下文断裂 |

### 4.3 解决方案：encrypted_content 透传

mimo2codex 的解决方案精妙：

```
第一轮请求：
  Codex ──Responses API──► mimo2codex ──Chat API──► MiMo
             ◄──────────────────────────────
                    reasoning_content
                    (存入 encrypted_content)

第二轮请求：
  Codex ──带 encrypted_content 的Responses──► mimo2codex
             │ 提取 encrypted_content
             ▼
             注入到前一条 assistant message 的 reasoning_content
             ▼
          ──Chat API──► MiMo (完整上下文!)
```

```typescript
// reqToChat.ts 中的 reasoning 回填逻辑
function injectReasoningContent(messages: ChatMessage[], reasoning: string) {
  // 找到上一条 assistant message（index = length - 1 - tool_calls_count）
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].role === "assistant") {
      messages[i].reasoning_content = reasoning;
      break;
    }
  }
}
```

**为什么不能用 `summary`？** 旧版本（< 0.2.3）把 reasoning 塞 `summary[].text`，但 `--no-reasoning` 模式下完全丢弃。0.2.3+ 把完整 trace 存入 `encrypted_content`（Codex 视为 opaque blob，原样回传），无论终端是否显示 reasoning。

---

## 5. Provider 路由体系

### 5.1 内置 Provider（registry.ts）

```typescript
// src/providers/registry.ts
export const BUILTIN_PROVIDERS: readonly Provider[] = [mimo, deepseek];

export function selectProvider(clientModel: string): SelectedProvider {
  // 1. 遍历所有已注册 provider（内置优先）
  for (const p of providerListMutable) {
    if (p.resolveModel(clientModel) && hasApiKey(p)) {
      return { provider: p, upstreamModel: clientModel };
    }
  }

  // 2. 未匹配 → 使用默认 provider，model 重写为 defaultModel
  return { provider: defaultProvider, upstreamModel: defaultProvider.defaultModel };
}
```

### 5.2 MiMo Provider 细节（providers/mimo.ts）

```typescript
// src/providers/mimo.ts
const BUILTIN_MODELS = [
  { id: "mimo-v2.5-pro", supportsImages: false, supportsReasoning: true },
  { id: "mimo-v2.5", supportsImages: true, supportsReasoning: true },      // 视觉版
  { id: "mimo-v2-omni", supportsImages: true, supportsReasoning: true },  // 视觉+音频
  { id: "mimo-v2-flash", supportsImages: false },
];

// MiMo 双主机自动切换
const PAYG_BASE_URL = "https://api.xiaomimimo.com/v1";
const TOKEN_PLAN_BASE_URL = "https://token-plan-cn.xiaomimimo.com/v1";

function isTokenPlanRuntime(apiKey: string, baseUrl: string): boolean {
  return /token-plan/i.test(baseUrl) || apiKey.startsWith("tp-");
}
```

**关键设计**：
- `tp-*` key → token-plan 主机（国内优化）
- `sk-*` key → pay-as-you-go 主机
- 视觉能力：只有 `mimo-v2.5` / `mimo-v2-omni` 支持图片输入，`pro` / `flash` 不支持（会报 404）

### 5.3 Generic Provider 机制

```typescript
// src/providers/generic.ts
export interface GenericProvider {
  id: string;
  displayName: string;
  baseUrl: string;
  envKey: string;
  defaultModel: string;
  wireApi?: "chat" | "responses";  // chat=翻译, responses=直透
  models?: string[];  // 空=开放目录(any model)
}

// providers.json 示例
{
  "providers": [{
    "id": "qwen",
    "displayName": "Qwen (DashScope)",
    "baseUrl": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "envKey": "QWEN_API_KEY",
    "defaultModel": "qwen3-max",
    "models": ["qwen3-max", "qwen3"]
  }]
}
```

**路由规则**：
1. 客户端发送的 `model` 字段先在已注册 provider 的 catalog 中匹配
2. 命中且 provider 有 key → 路由到该 provider
3. 未命中 → 走默认 provider 的 `defaultModel`（admin 日志会记录 `client_model_rewritten`）

---

## 6. 流式处理（streamToSSE.ts）

Codex 要求 SSE 流式响应，每个事件必须包含 `type` 字段。

```typescript
// src/translate/streamToSSE.ts
function emit(sink: SseSink, state: StreamState, event: string, data: Record<string, unknown>) {
  // SSE event line + data line 都必须有 type
  sink.write(event, { type: event, ...data, sequence_number: state.nextSeq() });
}

// 流式输出序列
// 1. response.completed (stream start)
// 2. response.outputItem.added (reasoning chunk)
// 3. response.outputItem.done (reasoning done)
// 4. response.outputItem.added (message chunk)
// 5. response.outputItem.done (message done)
// 6. response.done (final)
```

**工具调用状态机**：

```typescript
interface ToolCallState {
  itemId: string;
  outputIndex: number;
  callId: string;
  name: string;
  argsBuffer: string;
  argsEmitted: boolean;
}

// 并行工具调用处理
// 每个 tool_call 对应一个 ToolCallState，逐步累积 arguments
// 完成时输出 response.outputItem.added (function_call)
```

---

## 7. Admin Web 控制台

启动后访问 `http://127.0.0.1:8788/admin/`，功能：

| Tab | 功能 |
|-----|------|
| 概览 | 24h/7d/30d Token 用量、错误率、按 provider/模型聚合统计 |
| 日志 | 按 provider 过滤、时间分页、状态码异常着色 |
| 模型 | 按 provider tab 切换；内置模型只读，可新增别名映射 |
| 设置 | provider 状态、base URL、默认模型；**API key 不在 UI 存储**（必须走 env） |

数据存储在 SQLite（`~/.mimo2codex/data.db`），可 `--data-dir` 自定义。

---

## 8. 快速上手

### 8.1 安装

```bash
npm install -g mimo2codex
# 或一键脚本（不需要全局安装）
curl -fsSL https://raw.githubusercontent.com/7as0nch/mimo2codex/main/scripts/install.sh | bash
```

### 8.2 启动（MiMo + DeepSeek 双 provider）

```bash
export MIMO_API_KEY=sk-xxxxxxxxxxxxxxxx
export DS_API_KEY=sk-xxxxxxxxxxxxxxxx
mimo2codex
```

启动横幅直接打印 `~/.codex/auth.json` 和 `config.toml` 内容，粘贴即可。

### 8.3 接入 Generic Provider（Qwen 为例）

```bash
export GENERIC_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export GENERIC_API_KEY=sk-your-qwen-key
export GENERIC_DEFAULT_MODEL=qwen3-max
mimo2codex --model generic
```

或写 `~/.mimo2codex/providers.json` 配置多实例。

---

## 9. 技术亮点总结

| 特性 | 实现方式 |
|------|----------|
| **Responses ↔ Chat 双向转换** | reqToChat.ts / respToResponses.ts，手动映射每个字段 |
| **reasoning_content 多轮透传** | encrypted_content 存储全量 reasoning，下一轮注入回 `reasoning_content` 字段 |
| **多 provider 自动路由** | 按 model 字段匹配 catalog，无匹配则走 defaultModel |
| **MiMo 双主机自动切换** | key 前缀检测（tp-/sk-）→ 选择对应 baseUrl |
| **工具调用状态机** | 流式处理中累积 arguments，支持并行 tool_calls |
| **Generic Provider 机制** | 写 providers.json 即可接入任何 OpenAI 兼容端点 |
| **cc-switch 集成** | `mimo2codex print-cc-switch` 输出粘贴片段 |

---

## 10. 与同类项目对比

| 项目 | 协议转换 | 内置 Provider | Generic | 特点 |
|------|----------|--------------|---------|------|
| mimo2codex | Responses ↔ Chat | MiMo + DeepSeek | ✅ JSON 配置 | 专注 Codex，针对 reasoning_content 做了深度处理 |
| openrouter | OpenAI compatible | 50+ provider | 付费 | 托管服务，不需要本地部署 |
| claude-code-router | Claude API → OpenAI | Claude | ❌ | 专注 Claude |
| y-router | 通用路由 | 通用 | ✅ | 更通用，无内置 MiMo/DeepSeek |

---

**相关链接**：

- GitHub: https://github.com/7as0nch/mimo2codex
- 通用 Provider 文档: https://github.com/7as0nch/mimo2codex/blob/main/doc/generic-providers.zh.md
- mimoskill 扩展: https://github.com/7as0nch/mimo2codex/blob/main/doc/mimoskill.zh.md