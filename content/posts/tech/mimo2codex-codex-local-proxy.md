---
title: "mimo2codex 解读：新版 Codex 接上 MiMo 与 DeepSeek，难点在 reasoning 的跨轮回传"
date: "2026-05-14T16:15:00+08:00"
slug: "mimo2codex-codex-local-proxy"
github_repo: "7as0nch/mimo2codex"
source_key: "gh:7as0nch/mimo2codex"
description: "把 mimo2codex 0.5.29 跑起来读源码：Responses 与 Chat Completions 之间到底翻译了哪些字段、reasoning_content 为什么要借 encrypted_content 回传、provider 路由的四段优先级，以及上游那些不干净的行为被怎么兜住。"
draft: false
lastmod: "2026-09-21T06:30:00+08:00"
categories: ["技术笔记"]
tags: ["TypeScript", "Codex", "MiMo", "DeepSeek", "OpenAI 兼容", "协议网关"]
---

字段映射是这篇文章最不值得读的部分。

Responses 与 Chat Completions 两套 API（应用程序接口）的差异是公开的：一边把对话摊平成 `input` 里的带类型条目，一边沿用 `messages` 加 `role`。照着一份请求样例写两屏 `switch`，多数人都能把它跑通。作者 7as0nch 自己在 README 里把这层称作 "a thin protocol shim"。

真正吃掉大半代码量的是另外三件事。思考文本必须跨轮回到上游；每个上游对 OpenAI 兼容子集的理解各不相同；Codex 那几个私有状态文件还得在不动用户配置的前提下被读写。到 v0.5.29，`src/` 下有 72 个 TypeScript 文件、16,865 行代码，`translate/` 只占其中 2,843 行。

本文的判断：mimo2codex 值得读的地方，在于它把「协议网关」这个听起来很薄的定位做成了一台带自愈逻辑的适配器；代价随之出现——静默改模型、回写 Codex 私有状态、依赖客户端原样吐回一个它自己不解析的字段。

## 目录

- [三条主线，别混成一个故事](#三条主线别混成一个故事)
- [请求方向上的字段搬运](#请求方向上的字段搬运)
- [响应方向上的二十个事件](#响应方向上的二十个事件)
- [reasoning 的跨轮回传](#reasoning-的跨轮回传)
- [provider 路由的四段优先级](#provider-路由的四段优先级)
- [上游不干净时的四道自愈](#上游不干净时的四道自愈)
- [Codex 那一侧的写配置与会话迁移](#codex-那一侧的写配置与会话迁移)
- [三种部署形态与 admin 控制台](#三种部署形态与-admin-控制台)
- [装上、跑通、验一遍](#装上跑通验一遍)
- [一次多轮工具调用走完 mimo2codex](#一次多轮工具调用走完-mimo2codex)
- [与邻近项目的分工](#与邻近项目的分工)
- [常见故障与排查](#常见故障与排查)
- [五道自测题](#五道自测题)
- [谁该用，谁可以再等等](#谁该用谁可以再等等)
- [下一步读哪份代码](#下一步读哪份代码)
- [维护与复核指引](#维护与复核指引)
- [参考](#参考)

## 三条主线，别混成一个故事

`src/` 的目录划分和上面那三件事基本对得上。把它们混成「一个翻译层」，读完只会记住一堆文件名。

| 主线 | 位置 | 职责 | 规模 |
|------|------|------|------|
| 协议翻译 | `src/translate/` | Responses 与 Chat Completions 双向映射，含流式状态机 | 2,843 行 |
| 上游归一化 | `src/providers/` | 各家目录、鉴权主机、字段怪癖与错误翻译 | 1,316 行 |
| 运行时与运维 | `server.ts` 与 `db/` `admin/` `codex/` `auth/` | 路由决策、落库、控制台、Codex 配置读写、多用户 | 约 12,700 行 |

三条线之间有方向：运行时按 `model` 字段挑上游，把请求交给归一化层清洗，再由翻译层发出；回来的流经过翻译层还原成 Codex 认识的事件序列。单看哪一条都平淡，串起来才解释得清它为什么不是一个 300 行的脚本。

## 请求方向上的字段搬运

下面这段不是推测。我在本机把仓库跑起来（`npm install && npx tsc -p .`），用一个只回吐固定分片的本地假上游接住 `GENERIC_BASE_URL`，向 `http://127.0.0.1:8790/v1/responses` 发请求，再把上游收到的报文打印出来对比。假上游不含任何模型逻辑，因此两侧报文里看到的差异全部来自 mimo2codex。这个示例的作用就是把翻译层的输出摊到桌面上看。

发出去的 Responses 请求带 `instructions`、一条 `developer` 消息、一条 `user` 消息、一个 `read_file` 工具定义和 `reasoning: {effort: "medium"}`。上游收到的 Chat 请求：

```json
{
  "model": "mock-model",
  "messages": [
    { "role": "system", "content": "You are Codex." },
    { "role": "system", "content": "fix the typo" },
    { "role": "user", "content": "a.ts 里有个拼写错误" }
  ],
  "stream": true,
  "stream_options": { "include_usage": true },
  "tools": [
    { "type": "function",
      "function": { "name": "read_file", "description": "read a file",
                    "parameters": { "type": "object",
                                    "properties": { "path": { "type": "string" } } } } }
  ],
  "reasoning_effort": "medium"
}
```

四件事在这一次转换里同时发生：

1. `instructions` 落成一条 `system` 消息，`developer` 角色同样映射到 `system`；两条 system 按原顺序并存，没有合并。
2. `tools` 从 Responses 的扁平形状套上 `{type: "function", function: {...}}` 这层壳。
3. `stream_options.include_usage` 被强行加上。少了它，流式响应的最后一块不会带用量统计，控制台的面板就永远是空的。
4. `reasoning.effort` 摊平成 `reasoning_effort`。

翻译层里还有一条不长却很说明问题的分支。`server.ts:1249` 起的 `isResponsesProbe()` 专门识别 cc-switch「测试连接」这类只带 `model` 与流式开关、既无 `input` 也无 `instructions` 的请求，直接合成一个空 `output` 的 200 回掉，不转发——转发的话上游会因为 `messages: []` 回 400。issue #31 又给它补了字符串形态的 `input`：Codex 桌面端会发 `input: "write hello world"`，而早先只认数组形态，于是真实请求被误判成探针，用户看到的是一次不带任何错误信号的空回答。

同一轮请求换成 MiMo 上游时，报文还会多三处变化，来自 `src/providers/mimo.ts` 的 `normalizeMimoBody()`：注入 `thinking: {type: "enabled"}`、注入 `parallel_tool_calls: true`、删掉采样温度（`temperature`）与核采样概率（`top_p`）。我在请求里确实带了 `temperature: 0.2` 和 `tool_choice: "required"`，上游两者都没收到。

`thinking` 与采样参数的关系写在 `MIMO_THINKING_STRIPS_SAMPLING` 这个集合上（`mimo.ts:118`）：v2.5 家族在思考模式下强制 `temperature: 1.0`、`top_p: 0.95`，客户端传了也不生效，本地先删掉能让日志与实际行为一致。集合是逐个列举的，作者留了理由——将来某个 MiMo 模型若真的接受自定义采样，不希望被一条无条件规则盖掉。

## 响应方向上的二十个事件

流式回包是这套网关最容易写坏的一侧。Codex 只认带 `type` 的具名事件，顺序或配对错了，表现就是「回答卡住」或者「工具调用丢失」。

我抓到的完整序列：20 个事件，`sequence_number` 从 0 到 19，按类型收敛后是这样：

```text
response.created → response.in_progress
→ response.output_item.added (reasoning)
→ response.reasoning_summary_part.added
→ response.reasoning_summary_text.delta / .done
→ response.reasoning_summary_part.done
→ response.output_item.done (reasoning)
→ response.output_item.added (message)
→ response.content_part.added
→ response.output_text.delta / .done
→ response.content_part.done
→ response.output_item.done (message)
→ response.output_item.added (function_call)
→ response.function_call_arguments.delta ×2
→ response.function_call_arguments.done
→ response.output_item.done (function_call)
→ response.completed
```

三个细节值得单独看。

`reasoning` 与 `message` 是两个平行的输出条目，各自走完 added 到 done 的配对，`output_index` 分别是 0 和 1；工具调用是第 3 个条目，`output_index` 为 2。

工具的 `arguments` 是分片到达的。我的假上游把 `{"path":"a.ts"}` 切成 `{"pa` 与 `th":"a.ts"}` 两块发出，网关按分片转发 `function_call_arguments.delta`，直到 `.done` 才给出拼好的完整串。每个进行中的工具调用各自持有一个参数缓冲区，因此上游并行吐出多个 `tool_calls` 时不会串台。

`response.completed` 是终点，不是起点。它的 `usage` 里 `prompt_tokens` 被改名成 `input_tokens`，`prompt_tokens_details.cached_tokens` 与 `completion_tokens_details.reasoning_tokens` 分别挂到 `input_tokens_details` 与 `output_tokens_details` 之下（`respToResponses.ts:62-78`）。

非流式一侧还有个容易漏掉的分支：`finish_reason` 为 `length` 时，响应 `status` 写成 `incomplete` 并带上 `incomplete_details: {reason: "max_output_tokens"}`，代码里那句 `"completed"` 只是默认值。

## reasoning 的跨轮回传

小米在思考模式下会严格扫描整段对话历史：只要有一条历史 assistant 消息缺 `reasoning_content`，上游直接拒绝。代理与网络常见问题这份文档（`doc/proxy-faq.zh.md:349`）记着原始报错文本：

```text
Param Incorrect: The reasoning_content in the thinking mode must be passed back to the API.
```

DeepSeek V4 有同款校验。麻烦在于 Codex 客户端不会替你存思考文本。它按 Responses 的形状回传历史，那里的条目类型是 `reasoning`，可用字段只有 `summary` 与 `encrypted_content`，没有 `reasoning_content` 这个位置。

mimo2codex 的做法是借道 `encrypted_content`。`respToResponses.ts:98-116` 把上游返回的完整思考文本原样写进该字段，只在需要展示时填充 `summary`：

```typescript
if (message?.reasoning_content) {
  output.push({
    type: "reasoning",
    id: newReasoningId(),
    summary: opts.exposeReasoning
      ? [{ type: "summary_text", text: message.reasoning_content }]
      : [],
    encrypted_content: message.reasoning_content,
    status: "completed",
  });
}
```

Codex 把 `encrypted_content` 当成不透明块保存并原样吐回，网关在下一轮优先读它，回灌到对应 assistant 消息的 `reasoning_content` 上（`reqToChat.ts:757-770`）。`--no-reasoning` 只清空 `summary`，回传通路照旧工作。

这条边界我核对了 npm 上的历史包。0.2.2 的 `dist/translate/respToResponses.js` 里，构造 reasoning 条目的条件写作 `if (opts.exposeReasoning && message?.reasoning_content)`，`summary` 是唯一载体；同版本的 `reqToChat.js` 搜不到 `encrypted_content` 这个字面量。0.2.3 的三个翻译文件里它都出现了。`doc/tag-log.zh.md:269` 对 v0.2.3（2026-05-13）的记述正是「根据小米官方公告修复 MiMo `reasoning_content` 回传问题」。在 0.2.3 之前，关掉终端显示等于把跨轮上下文一起关掉。

回灌时的落位比取哪个字段更讲究。Codex 放 reasoning 条目的位置很不规律，可能在 `function_call` 之前，也可能夹在两个工具调用之间。`reqToChat.ts` 因而不立即成行，而是维护 `pendingAssistantText`、`pendingToolCalls`、`pendingReasoning` 三个缓冲区，把同一轮的片段合并进同一条 assistant 消息。我复现了这一情形：输入历史里放一条 `summary: []` 且带 `encrypted_content` 的 reasoning 条目，其后紧跟 `function_call` 与 `function_call_output`，上游收到的是三条消息，其中第二条是：

```json
{
  "role": "assistant",
  "tool_calls": [
    { "id": "call_1", "type": "function",
      "function": { "name": "read_file", "arguments": "{\"path\":\"a.ts\"}" } }
  ],
  "reasoning_content": "先看看要改哪个文件。"
}
```

拆成两条 assistant 消息就不行了：线格式会变成「带 `tool_calls` 的 assistant，后面跟一条普通 assistant，再跟 tool」。这违反 Chat Completions 那条「带 `tool_calls` 的 assistant 必须紧接 tool 消息」的约束，DeepSeek 会以 `insufficient tool messages following tool_calls message` 拒绝。`reqToChat.ts:775-780` 的注释把这条因果写得很明白。

还有一类历史缺口跟思考开关有关：会话中途关掉思考，前几轮的 assistant 消息天然没有思考文本，再打开时整段历史就脏了。mimo2codex 的对策是给这些消息补固定占位文本 `(this turn ran without thinking mode)`，让思考模式保持开启，同时把「这几轮其实没思考」显式暴露给模型。补了占位反而被上游拒时，兜底才把该请求降级成 `thinking: {type: "disabled"}`。

## provider 路由的四段优先级

`src/providers/registry.ts:9` 里内置上游只有两个：

```typescript
export const BUILTIN_PROVIDERS: readonly Provider[] = [mimo, deepseek];
```

通用 provider 由 `initRegistry()` 在启动时追加，注册表在进程生命周期内只迁移一次，没有热加载；自定义 id 与内置撞名会直接抛错。

真正的决策在 `server.ts:377` 的 `selectProvider()`，四段按顺序尝试：

1. 用户声明的通用 provider，且 `models[]` 非空、能解析出这个 model id、且配了运行时；
2. 内置的 mimo 与 deepseek；
3. 控制台上的运行时覆盖，仅当没有任何目录认领这个 id 时生效；
4. 默认 provider 兜底，把 model 重写成它的 `defaultModel`。

通用条目排在内置前面，为的是内部代理场景：企业给 MiMo 套一层内网网关、声明成通用并照抄 `mimo-v2.5-pro` 这个名字时，不该被内置条目截走。代价是同名模型下先来者赢。

开放目录式的通用 provider（`models[]` 留空表示接受任意 id）在自动匹配阶段被跳过，见 `registry.ts:62-68`。不跳的话它会把所有未知 id 全吞掉，让默认 provider 形同虚设；要走到它，只能显式把它设成默认 provider。默认 provider 的确定顺序是 `--model <id-or-shortcut>`，其次 `MIMO2CODEX_DEFAULT_PROVIDER`，最后落到 `mimo`。

这套优先级里藏着一个运维陷阱。Codex 配置文件里的 `model` 字段常常还是出厂默认值。`doc/proxy-faq.zh.md:322` 列了近些日子见过的字面量：`gpt-5`、`gpt-5-codex`、`gpt-5-mini`、`gpt-5.4`、`gpt-5.4-mini`。这些名字任何一个都不在 mimo2codex 的目录里，于是每条请求都被静默改写成默认 provider 的 `defaultModel`，对话过程里没有任何提示。这条改写会记成日志码 `client_model_rewritten`（`server.ts:497`），终端侧从 v0.2.18 起降为 INFO：

```text
INFO model fallback applied — client sent unknown model id, request continues with provider default
```

降为 INFO 有道理，请求确实成功了。但它同时意味着「你以为在用支持视觉的模型、传了图，实际落在一个不支持的模型上、图片被丢掉」这类问题只能靠控制台的模型映射记录或者日志翻查。配套的排查手段见后文表格。

## 上游不干净时的四道自愈

「OpenAI 兼容」在中文社区里覆盖了几百个网关，它们对同一份规范的理解差别，足以让一个薄翻译层失效。mimo2codex 的应对是四类具体的兜底动作，都落在源码里，也都能在测试套件里找到对应断言。

**参数残缺。** 上游被长度截断、或者自己吐出发疯的 JSON 时，`tool_calls[].function.arguments` 会是个残缺串。原样转发出去，Codex 把它存进历史，之后每一轮都在严格校验的上游那里撞 `unexpected end of data`。`salvageToolCallArguments()`（`respToResponses.ts:24-44`）解析失败就替换成 `"{}"` 并记一条 WARN，同时按 `finish_reason` 区分归因：`length` 时提示提高 `max_completion_tokens` 或者缩短会话。

**瞬时故障。** 可重试状态集合是 `{429, 500, 502, 503, 504}`，默认 6 次额外尝试（合计最多 7 次请求），指数退避封顶 12 秒，整段预算约 28 秒，够扛过一次多秒级的配额限流；带数字或 HTTP 日期的 `Retry-After` 会被遵守，但做了上限裁剪，免得 Codex 那边先超时。两个例外写得很清楚：undici 的头超时与体超时不重试，因为那表示已经等满了窗口，再发一次只是把同样的大请求重放一遍（`openaiCompatClient.ts:86-107`）。上游完全连不上时走的是流内错误事件，HTTP 状态仍是 200：

```text
event: error
data: {"type":"error","code":"upstream_unreachable","message":"failed to reach upstream: fetch failed (ECONNREFUSED: connect ECONNREFUSED 127.0.0.1:9099)","sequence_number":9999}
```

**上下文窗口。** MiMo 与 DeepSeek 都对外标称 1M 窗口。`mimo.ts:26-34` 的注释交代了为什么这么写：Codex 某些构建会按 `model_context_window` 提前触发压缩，声明小了就会出现「其实还早，但客户端先动手」。可真实上限在 128K 量级，所以自动压缩不能按标称窗口的百分比来算。`translate/autoCompact.ts` 用的是绝对阈值，默认 100,000 个估算词元（token，词元），按 4 字符一个词元粗算，图片每张固定计 1,024。命中后把中段历史摘要成一条笔记，开头的系统消息与最近几轮保持原文。它处理的是翻译之后的 `ChatMessage[]`，所以一套逻辑同时覆盖 MiMo、DeepSeek 与通用 chat 上游。上游真的回了 `context_length_exceeded` 时，`upstream/contextOverflow.ts` 负责换成带 `/compact` 引导的可读提示。

**私有字段的形状差异。** MiniMax 那类上游把思考写在正文里（`<think>...</think>` 内联），由 `translate/minimaxCompat.ts` 在生成 Responses 输出之前先切出到 `reasoning_content`，否则思考文本会当成回答内容显示给 Codex。Codex 桌面端的命名空间（namespace）工具是另一回事，例如 `multi_agent_v1` 下的 `spawn_agent`：响应里必须带 `namespace` 字段，网关靠 `namespaceMap` 补齐。少了它，客户端报 unsupported call。

## Codex 那一侧的写配置与会话迁移

网关要工作，Codex 得知道上游地址。这一步早期靠把片段贴进 `~/.codex/`。v0.5.29 上有三条路：`mimo2codex print-config` 打印片段；`print-cc-switch` 打印给 cc-switch 用的片段；控制台里的 Codex 启用页直接写文件。启动横幅不再自动打印这两份配置，命令行工具里的注释给了原因：用户反馈太啰嗦。

启用页背后是一组 `/admin/api/codex-*` 端点：`codex-state` 读当前配置状态、`codex-targets` 列出可写目标、`codex-apply` 写入、`codex-history` 与 `codex-history/:id/bundle` 保存并导出历史快照、`codex-import` 与 `codex-current-bundle` 负责反向导入。也就是说，改坏配置之后可以退回。

会话侧还有一处更硬的动作。Codex 桌面端把每个会话存在状态库 `~/.codex/state_<N>.sqlite` 的 `threads` 表里，并打上 `model_provider` 标记按它筛选。这正是「在 mimo2codex 里切了 provider 之后，两边会话互相看不见」的原因。v0.5.20 的会话页只读聚合这些会话，按 provider、项目目录、会话三层分组。它也提供迁移：改写该会话的 `model_provider`，数据库与 rollout 文件首行的 `session_meta` 一起改。重启 Codex 后，这条会话就归到所选 provider 下。动手前先把状态数据库（含 `-wal` 与 `-shm`）和 rollout 快照到 `~/.codex/.m2c-backups/sessions/<时间戳>/`；Codex 仍持有数据库锁时直接拒绝，返回 `409 codex_running`。这条能力只在本地模式可用，服务端部署接触不到操作者的 `~/.codex`，而且它改的是 Codex 私有、带版本号的状态：表结构一变，这一页会降级为不可用。

## 三种部署形态与 admin 控制台

README 把运行方式列成三条：命令行、Docker、桌面端。三者共用同一个服务端进程，差别在谁管密钥、谁碰得到本地会话状态。

| 形态 | 入口 | 关键差异 |
|------|------|----------|
| 命令行 | `npm install -g mimo2codex`，`mimo2codex init` 生成 `~/.mimo2codex/.env` | 单用户、零鉴权，`auth: off (local zero-auth mode)` |
| Docker | `docker compose up -d`，`--auth on` 或 `MIMO2CODEX_AUTH` | 登录、多用户、BYOK、OAuth、配置下发，上游密钥不外泄 |
| 桌面端 | `mimo2codex-desktop`（Electron 30） | 托盘常驻、开机自启、后台跑边车进程（sidecar），发版用独立的 `-desktop` tag |

监听地址默认 `127.0.0.1:8788`（`config.ts:76`），端口可被 `--port` 或 `MIMO2CODEX_PORT` 改。数据目录按四层优先级解析：`--data-dir` > `MIMO2CODEX_DATA_DIR` > 用户在控制台设过的指针文件 `~/.mimo2codex-pointer.json` > `~/.mimo2codex`，SQLite 落在其中的 `data.db`。

控制台是 `web/` 下那个 React 单页，挂在 `/admin/`，六个入口：概览、Codex 启用、会话、provider、模型、日志；登录模式下再加账户与用户两页。概览的时间范围是三档可选（24 小时、7 天、30 天），配 token 时序、错误分布与延迟分位数；日志页的状态筛选按区间实现（正常 200 至 399，错误 400 至 599），可按 provider 过滤。

密钥的处理在两种模式下不一样。本地模式仍从环境变量与 `.env` 读；多用户模式下 BYOK 密钥以 AES-256-GCM 密文入库，另存 nonce 与认证标签，用部署级主密钥封装。明文既不落盘，也不被列表接口返回（`db/upstreamKeys.ts`）。此外用户还能给自己签发访问用的 bearer 令牌。

0.5.27 修过一个很能说明工程成熟度的问题。Apple Silicon 上打进安装包的 SQLite 原生扩展若未签名，动态加载会被 AMFI 拒掉，服务随后把 `adminEnabled` 设为 false。于是访问 `/admin/` 返回一条看着完全无关的 `404 no route for GET /admin/`。修法分三层：把这类静默失败改回 `503 admin_db_unavailable`，带上原始错误与修复指引；打包时对边车进程做 ad-hoc 签名；再加一道打包后的端到端门禁，用打进包里的 Electron 实跑边车，断言健康检查报 `adminEnabled: true`。

## 装上、跑通、验一遍

命令都取自命令行工具自带的帮助文本与本机实测，可以照抄。

```bash
npm install -g mimo2codex          # 装完即可用 mimo2codex 这个命令
mimo2codex init                    # 生成 ~/.mimo2codex/.env，把 key 填进去
mimo2codex                         # 启动，监听 127.0.0.1:8788
```

`init` 是幂等的：每次刷新 `.env.example`，只在 `.env` 不存在时创建。要接一个环境变量式的通用上游，自带帮助文本里给的例子是：

```bash
GENERIC_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1 \
  GENERIC_API_KEY=sk-... GENERIC_DEFAULT_MODEL=qwen3-max \
  mimo2codex --model generic
```

多个上游就写 `~/.mimo2codex/providers.json`，再 `QWEN_API_KEY=sk-... mimo2codex --model qwen`。`--model` 挑的是默认 provider，不是模型名，这一点写在它的取值说明里（`<id-or-shortcut>`）。

起服务之后先探两下再回 Codex 里试：

```bash
curl -s http://127.0.0.1:8788/healthz
# {"ok":true,"name":"mimo2codex","provider":"generic","baseUrl":"http://127.0.0.1:9099/v1"}

curl -sN http://127.0.0.1:8788/v1/responses -H 'content-type: application/json' \
  -d '{"model":"mock-model","stream":true,"input":[{"type":"message","role":"user","content":[{"type":"input_text","text":"hi"}]}]}'
```

第二条命令的头两个事件是 `response.created` 与 `response.in_progress`，`sequence_number` 从 0 开始。如果只等到一个 `event: error`，先照后文那张表分辨是连不上还是密钥不对。

想知道翻译层到底动了什么，有个便宜的自测法：起一个只回吐固定分片的本地 HTTP 服务，把 `GENERIC_BASE_URL` 指过去，然后在服务端把收到的请求体整份落盘。两侧报文各存一份，diff 出来就是网关的全部动作。本文前两节的抓包就是这么来的，比读代码快，也比接真模型稳定。

## 一次多轮工具调用走完 mimo2codex

把前面几条线串起来。假设 Codex 已经指向本地 8788，`model` 写的是 `mimo-v2.5`，你在会话里让它读文件改一处拼写。

第一轮，Codex 发一个 `instructions` 加一条 `user` 消息的 Responses 请求。`selectProvider` 在第 2 段命中内置 MiMo，`resolveModel` 得到 `mimo-v2.5`（无改写，因此不会留下 `client_model_rewritten`）。归一化层注入 `thinking: {type: "enabled"}` 与 `parallel_tool_calls: true`，删掉客户端带的 `temperature`；翻译层把 `instructions` 与 `tools` 换成 Chat 形状，加上 `stream_options.include_usage`。上游吐出思考文本、一段说明和一个 `read_file` 调用，回到 Codex 侧就是上面那 20 个事件，思考条目里的 `encrypted_content` 装着全文。

第二轮，Codex 附上工具结果再发一次，历史里此时有 reasoning 条目、`function_call` 与 `function_call_output`。网关把三者合并成「一条带 `tool_calls` 且带 `reasoning_content` 的 assistant」加「一条 tool」，顺序保证 tool 紧跟其前，上游校验通过。若这一轮你其实关过思考，占位文本会补进缺口。

如果模型把回答写到长度上限，`finish_reason: length` 会让响应状态变成 `incomplete`，Codex 据此知道内容是被截断的，而不是自己结束。如果这一轮历史已经膨胀到 100,000 估算词元附近，中段先被摘要成一条笔记再发出去。

## 与邻近项目的分工

同类项目不少，共同身份都是协议路由器，差别在代理的是哪一套上游协议、以及为谁做兼容。星标与描述取自我核对当天的数字（2026-09-21）。

| 项目 | 定位 | 与 mimo2codex 的分界 |
|------|------|----------------------|
| mimo2codex | 让 Codex 的 Responses 形状落到 Chat Completions 上游 | 客户端固定，服务端可插拔；跨云部署时兼作多用户网关 |
| cc-switch（133,827 星标，Rust） | 桌面端多客户端配置切换器，覆盖 Claude Code、Codex 等 | 只换配置，不做协议翻译；mimo2codex 专门为它留了 `print-cc-switch` |
| claude-code-router（37,340 星标，TypeScript） | 面向本地编码智能体（agent）的控制面，职责接近一台路由器，自述是 "One local control plane for every AI agent" | 服务对象是 Claude Code 一系，路由与工具编排能力更宽 |
| y-router（384 星标，TypeScript） | 让 Claude Code 走 OpenRouter 的简单代理 | 目标客户端与目标上游都不同 |
| OpenRouter | 托管网关 | 流量出公网，不需要本地部署 |

## 常见故障与排查

下表按现象分类。左列是你会看到的原文或状态，右列是本次核对到的成因。

| 现象 | 成因与处置 |
|------|------------|
| 上游 400，含 `The reasoning_content in the thinking mode must be passed back to the API` | 历史里有 assistant 消息缺思考文本。确认 mimo2codex 在 0.2.3 之后；仍复现则看这条会话是否由旧版本产生，必要时新建会话 |
| 上游 400，含 `webSearchEnabled is false` | 联网搜索被显式打开，而账户未开通 MiMo 的 Web Search 插件（单独计费）。关掉搜索，或在平台控制台开通后重启服务 |
| 上游 401 | MiMo 两套主机与密钥前缀不匹配：`sk-` 走 `api.xiaomimimo.com`，`tp-` 走 `token-plan-cn.xiaomimimo.com`，跨用即 401。`inferBaseUrlFromKey()` 会自动选，手工设过 `MIMO_BASE_URL` 时容易覆盖它 |
| 带图的请求被 404 拒掉 | 图片发给了纯文本模型：目录里只有 `mimo-v2.5` 标着接受图片输入，`mimo-v2.5-pro` 与 UltraSpeed 不支持（`mimo.ts:16-19` 的注释里带着上游那句报错原文）。也可能是命中了下一条的静默改写 |
| 日志出现 `INFO model fallback applied` | 客户端 `model` 字段不在任何目录里，已被改写成默认模型。在 Codex 启用页把 `model` 写成真实模型 id，或接受这次兜底 |
| 上下文超限报错 | 检查是否触发自动压缩阈值；上游真回 `context_length_exceeded` 时按提示执行 `/compact` |
| 工具调用参数为空对象 | 看 WARN 里的 `salvaged to "{}"`，多半是 `finish_reason: length` 截断，提高输出上限或缩短会话 |
| `/admin/` 返回 503 `admin_db_unavailable` | SQLite 原生模块没加载成功（架构不匹配、ABI 不符，或 macOS 未签名被拒）。按报文里的指引重装或 `xattr -cr`；显式 `--no-admin` 时仍是原来的 404 |

## 五道自测题

1. 为什么思考文本要写进 `encrypted_content`，而不是 `summary`？后者在什么情况下是空的？
2. 一条带 `tool_calls` 的 assistant 消息与它的 tool 结果之间为什么不能插入别的消息？违反这条会在哪个上游看到什么报错？
3. 客户端发 `gpt-5.4`，上游却收到 `mimo-v2.5-pro`，中间发生了什么？在哪两个地方能查到这次改写？
4. MiMo 目录里为什么写 1M 上下文窗口，而自动压缩按 100,000 估算词元触发？这两个数字分别服务于谁？
5. 把 `mimo-v2-flash` 这个名字发给当前版本，上游会收到哪个模型名？这次解析对图片输入意味着什么变化？

## 谁该用，谁可以再等等

适合的情况：你已经在用最新版 Codex，需要在它下面挂一个只提供 Chat Completions 的上游；或者你同时用 MiMo、DeepSeek 与若干内网兼容网关，希望一个进程按模型名分流，并且要在本地留下可查的调用记录。

不太需要的情况：你的客户端是 Claude Code 一系，那是 claude-code-router 的地盘；你只想切换已有配置而不做翻译，cc-switch 更轻；你不介意流量经第三方，OpenRouter 省去运维。

上手顺序我建议这样。先 `mimo2codex init` 配好一个上游；用 `--model` 显式指定默认 provider，避开静默兜底带来的困惑；跑一次真实工具调用，在日志页确认没有 `client_model_rewritten`。之后再考虑要不要打开控制台里的运行时覆盖与多 provider。Docker 多用户模式留到最后：它引入主密钥与用户体系，一旦启用，密钥管理责任就从「环境变量在你 shell 里」变成了「加密数据在磁盘上」。

## 下一步读哪份代码

想验证本文的结论，或者要接手维护：

- `src/providers/types.ts`：`Provider` 接口是所有差异的收口处，先读它再读任何一家实现，能省掉来回跳。
- `src/translate/reqToChat.ts`：`pendingAssistantText`、`pendingToolCalls`、`pendingReasoning` 三个缓冲区怎么合并成一条消息，是全文最密的一段逻辑。
- `src/translate/streamToSse.ts`：事件配对的唯一真相来源，改任何流式行为前先看它的状态机。
- `src/server.ts:377`：`selectProvider`，配套回归测试在 `test/` 里按 provider 分文件。
- `doc/proxy-faq.zh.md`：错误文案与成因的对照表，比 issue 区可靠。
- `doc/tag-log.zh.md`：按 tag 倒序的变更史，很多「为什么现在这样」的答案在这份文件里。

测试套件是一台现成的断言放大器：50 个测试文件、678 项断言，`npm test` 在 3 秒内跑完并全绿。想知道某个边界行为是不是有意设计，先在 `test/` 里搜关键词，比猜快得多。

## 维护与复核指引

本文事实的核对时间是 2026-09-21，对象是 `main` 分支 HEAD `5cb6f5c`（提交时间 2026-07-04，与 npm 上 `latest` 的 0.5.29 同批），外加 npm registry。方法：浅克隆（`git clone --depth 1`）源码，装完依赖后 `npx tsc -p .` 构建，用本地假上游抓两侧报文。历史版本结论来自 `registry.npmjs.org` 上 0.2.2 与 0.2.3 两个 tarball 的比对。仓库自述以 `README.md`、`doc/` 与源码交叉核对，冲突处以代码与实跑结果为准。

以下断言随版本漂移的风险最高，复核时优先看它们：

- 规模类：`src/` 72 个文件、16,865 行、`translate/` 2,843 行、测试 50 文件 678 项。
- 目录类：MiMo 三个模型与两组别名、DeepSeek 四个条目及 2026-07-24 的旧别名弃用日期。
- 阈值类：重试 6 次与 28 秒预算、自动压缩 100,000 估算词元、默认端口 8788。
- 外部数字：GitHub 星标与同类项目数字只在抓取当天有效。

有一处我没能独立定案：MiMo 官方 Codex 接入页面的原文措辞。该页面是客户端渲染，本机抓取只拿到打包后的脚本。因此文中「官方接入只支持 `wire_api = "chat"`、新版 Codex 会硬报错」这句话的来源是 mimo2codex 自己的 README，我未能核对小米文档原文，也就不用它去支撑任何具体版本号建议。

## 参考

- mimo2codex 仓库：<https://github.com/7as0nch/mimo2codex>
- 通用 provider 与路由优先级：<https://github.com/7as0nch/mimo2codex/blob/main/doc/generic-providers.zh.md>
- 代理与网络常见问题：<https://github.com/7as0nch/mimo2codex/blob/main/doc/proxy-faq.zh.md>
- 按 tag 的变更史：<https://github.com/7as0nch/mimo2codex/blob/main/doc/tag-log.zh.md>
- Codex 启用与配置写回：<https://github.com/7as0nch/mimo2codex/blob/main/doc/codex-enable.zh.md>
- mimoskill 扩展：<https://github.com/7as0nch/mimo2codex/blob/main/doc/mimoskill.zh.md>
- npm 发布元数据：<https://www.npmjs.com/package/mimo2codex>
- cc-switch：<https://github.com/farion1231/cc-switch>
- claude-code-router：<https://github.com/musistudio/claude-code-router>
- y-router：<https://github.com/luohy15/y-router>
