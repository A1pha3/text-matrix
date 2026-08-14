---
title: "DeepSeek Harness 主仓库深度解析：93K stars 的 agent harness 平台——everything is a plugin 与 Model-visible means logged"
date: "2026-08-15T01:05:00+08:00"
slug: "deepseek-harness-everything-is-a-plugin-cordis-architecture"
description: "从 Cordis「everything is a plugin」哲学、append-only session log 的「Model-visible means logged」invariant、Turn flow 全链路（pre-step waterfall → llm/stream → tools/execute → step/end），到 30+ core/extension packages 的 capability seam 三角色与 17 个扩展点机制，拆解 deepseek-ai/deepseek-harness v0.x 如何把整个 AI agent 平台做成可插拔。"
categories: ["技术笔记"]
tags: ["AI Agent", "开源项目深拆", "TypeScript", "Cordis", "DeepSeek", "Plugin Architecture", "Platform Engineering"]
toc: true
band: review
gates: ["事实性", "去AI味", "观点依据"]
github_repo: "deepseek-ai/deepseek-harness"
---

## 这篇文章在回答什么

`deepseek-ai/deepseek-harness`（93,077 stars / 2026-08-13 创建 / 7,412 文件 / 30+ packages / 62 docs）是 DeepSeek 在 2026 年 8 月开源的 **agent harness 平台**——不是单个产品，是「**能跑 AI agent 应用的运行时**」。

README 第一句话定位很重：

> DeepSeek Harness (`dsh`) is an open-source agent harness developed by DeepSeek AI. It uses an architecture where **everything is a plugin**, and is powered by [Cordis](https://github.com/cordiverse/cordis), whose design is described in [_A Programming Paradigm for Spatiotemporal Composability_](https://github.com/cordiverse/paper).

三个关键词：「**everything is a plugin**」（平台本体就是 plugin 组合）、「**Cordis**」（一个 vendored 的 plugin framework，不是 Koishi 那个 cordis）、「**Spatiotemporal Composability**」（论文标题——时空可组合性）。

前面三个反写任务（dsh-at-file 1742 行、dsh-genui 5860 行、arXiv 2608.09696）和这个主仓库是什么关系？

- **dsh-at-file**（8-12 v0.4.0）是 DSH 的 `@path` 提及插件——一个 out-of-tree plugin
- **dsh-genui**（8-13 v0.8.1）是 DSH 的 GenUI 渲染层插件——另一个 out-of-tree plugin
- **arXiv 2608.09696**（Murphy 论文）和 DSH 没有直接关系——独立第三方论文

dsh-at-file 和 dsh-genui **都是这个主仓库的子集切片**——它们引用的 `ctx.typert` / `ctx.tools` / `ctx.session.event` / `ctx.settings` / `ctx.agents` 全部来自主仓库的 core packages。本文是**母体**。

文章回答五件事：

1. **Cordis 的「everything is a plugin」具体意味着什么**——model adapter 是 plugin、tool registry 是 plugin、session log 是 plugin、agent loop 本体也是 plugin
2. **「Model-visible means logged」 invariant**——任何进模型的东西必须能从一个 append-only session log 重构（dsh-at-file 的 mention 注入 + dsh-genui 的 panel 持久化都基于这条）
3. **Turn flow 全链路**——pre-step waterfall → llm/stream → tools/execute → step/end 一条线 8 个 events
4. **30+ core/extension packages 的 capability seam 三角色**——Service Definition / Service Provider / Consumer，一个 provider swap 改整个产品
5. **「Where new behavior goes」17 个扩展点**——加 model provider 怎么挂、加 tool 怎么挂、加 subagent 怎么挂，全表对应

## 系统地图：7,412 个文件怎么分

主仓库布局：

```text
vendor/      vendored Cordis 框架源码 + cosmokit/group/hmr/loader 等
packages/    @deepseek-ai/dsh-<pkg> workspaces（54 个）
  core/        product API 脊柱
    session          append-only SessionEvent log (1157 行)
    agent            Agent interface + live registry (706 行)
    agent-loop       默认 driver (713 行)
    tools            tool registry + JSON schema (1946 行，最大)
    system-prompt    prompt section + tool schema assembly (545 行)
    scope            per-agent scoped-registration primitive
    agent-default-model   默认模型适配
    agent-tool-presentation  tool 展示策略
  api/         Remote BFF assembly + Typert RPC gateway
  typert/      type graph generator + loader + runtime registry
  llm/         LLM capability + DeepSeek providers + replay
  e2b/         E2B POC: sandbox + FS/subprocess adapters
  shell/       bash capability + local/pwsh providers
  subprocess/  subprocess capability + local process-tree provider
  terminal/    persistent terminal sessions
  fs/          filesystem capability + policy
  lsp/         language-server capability
  skill/       skill provider registry + catalog/loader
  web/         web capability (search/fetch providers)
  compaction/  compaction capability + basic provider
  context/     request-context plugins
  subagent/    subagent capability + delegation
  bundle/      installable dsh --profile patch-layer bundles
  workflow/    workflow capability + worker-thread provider
  todo/        todo_write tool
  plan/        plan mode as logged state
  preset/      per-session agent composition
  guard/       loop-hygiene + tool-timeout
  self-modification/   the agent inspects/mounts its own plugins
  hooks/       Claude Code/Codex hook bridges + wire-protocol
  session/     durable session data: persistence, projection, titles, telemetry
  identity/    anonymous identity
  settings/    user-settings capability
  credentials/ credential-reference capability
  acp/         automation-only Agent Client Protocol server
  interaction/ approval/interaction/permission/commands/ask-user
  boot/        shared app-bin glue
  sdk/         JSON-RPC protocol + server + TS client
  examples/    demo bundles
  support/     dev/test infrastructure
  util/        zero-dependency utilities
python/       Python SDK + bundled runtime
native/       @deepseek-ai/node-addon-landlock-run source of record
examples/     runnable cordis.yml leaves
.agents/      Agent workflows + Agent Notes
docs/         62 个文档（architecture, generated catalogs, postmortems, cookbook）
scripts/      repo gates + generators
website/      VitePress projection of selected bilingual docs/
```

**和 dsh-at-file / dsh-genui 的体量比较**：

| 项目 | 文件数 | 源码行数 | 角色 |
|---|---|---|---|
| **deepseek-harness**（本文） | 7,412 | ~13K+ (仅 5 个 core) / 全 54 packages 数万行 | 平台本体 |
| dsh-genui | 32 | 5,860 | 主仓插件：GenUI 渲染层 |
| dsh-at-file | 17 | 1,742 | 主仓插件：`@path` 提及 |

主仓是 7,412 文件 / 30+ packages 的庞然大物，dsh-at-file 是主仓的 0.23%，dsh-genui 是主仓的 0.43%。三个反写任务加起来不到主仓的 1%。

## Cordis「everything is a plugin」的具体含义

docs/cordis-primer.md 用五个 idea 把这个哲学讲清楚：

```text
1. A plugin is a object that implements Service.
   - 它是带 inject + apply(ctx) 的函数，或者是 Service 子类

2. A context is a repository of services.
   - 服务声明 ctx.<key>（如 ctx.tools / ctx.llm / ctx.sessions）

3. Declare service dependency via inject.
   - 插件命名依赖的服务后才装载——不靠手写 boot 顺序

4. Typed Events for communication.
   - TypeScript declaration merging 声明事件名
   - 四种 dispatch mode: emit / waterfall / parallel / serial

5. Registrations are reversible effects.
   - 所有注册都通过 ctx.effect() 或 ctx.on()
   - 卸载/重载时 unwinding 可预测
```

**关键 invariant 1**：没有 privileged core 给用户去 patch。architecture.md 原文：

> There is no privileged core to patch: you extend dsh by mounting a plugin beside the others, and registrations are effects that unwind when their plugin unloads.

翻译：「**没有特权核**让你去 hot-patch。你加能力的方式是挂一个 plugin 旁边，注册是可逆 effect，plugin 卸载时它们也回滚。」

这条 invariant 的工程后果是——model adapter 是 plugin、tool registry 是 plugin、session log 是 plugin、agent loop 本体也是 plugin。**`packages/core/agent-loop/src/index.ts` 713 行只是默认 driver，理论上可以被另一个 driver 完全替换。**

**关键 invariant 2**：service key 是稳定的接口契约。`ctx.llm` 的契约是「`ctx.llm.chat()` + `ctx.llm.stream()` + 注册 model provider」，但具体实现可以是 DeepSeek provider / Anthropic provider / OpenAI provider / local Ollama provider。**一个 swap 改整个产品**——这是 capability seam 的核心。

## Profiles + Bundles：plugin 树的分层组装

architecture.md 把运行时组成讲成「**plugin tree composed at boot from ordered layers**」：

```text
Profile
  - 命名 composition，存在 Harness home 里
  - 列出要叠的 bundles
  - 持有用户的 cordis.patch.yml
  - web / headless 是模板

Bundle
  - Cordis config rows + 代码的 distribution 格式
  - 每个 bundle 在自己的 package.json 里声明 dsh.bundle: <patch-file>
  - 上面 layers 可以 patch 它

dsh-base     所有 profile 的第一层（model adapters / tools / persistence / sandbox / approval / settings / credentials / telemetry）
dsh-web-app  Web 应用（在 base 之上）
dsh-headless one-shot runner（无 server）

加载顺序（apply 到空 entry list）：
  1. profile 列出的 bundles 按序
  2. profile 的 cordis.patch.yml
  3. home 级别的 cordis.patch.yml
  4. 任何 --patch overlay
```

layer 之间的 patch 关系是**target a row by id and replace its whole config, or insert new rows**——精确的 config rows 替换，不是模糊字符串替换。这条让 plugin 配置版本化、可追溯、可回滚。

**配置 dump 命令**：

```sh
dsh --profile web --dump-config
```

任何一行都能被自己的 patch 替换。

`packages/bundle/` 是 bundles 的实现仓库——`base` / `web-app` / `headless` 三种 bundle 是发行版入口。

## Session Log：Model-visible means logged

architecture.md 的「Session log」段是整个平台的**第二核心 invariant**：

> **Model-visible means logged.** Anything that reaches a model request must be reconstructable from the log, and a runtime invariant asserts it. This is why a new model-visible input requires a new session event: extend `SessionEventMap` and render from the log.

翻译：「**进模型的东西必须能从一个 append-only session log 重构**——runtime invariant 断言这条。所以要加一个新的 model-visible 输入必须加一个新的 session event：扩展 `SessionEventMap` 然后从 log render。」

这条 invariant 的工程后果极深：

**1. 整个平台的状态管理是 event-sourced，不是 mutable**。`packages/core/session/src/index.ts` 1157 行实现 `SessionStore`：append-only `SessionEvent` 流 + 内存里的 store + 从 log 派生 LLM message history。`SurfaceManager`（surface.ts 460 行）做「**事件到派生历史的投影**」。

**2. 持久化是 plugin 的事，不是 store 的事**。session 模块的 docstring 直接说：

> Persistence is a plugin concern (subscribe to `session/event`, drain on `session/flush`).

——持久化通过订阅 `session/event` + `session/flush` 实现，由专门的 persistence plugins（`session-persistence-jsonl` / `session-persistence-sqlite`）负责。`SessionStore` 本身只管内存。

**3. fork / resume / transcripts / telemetry / persistence 全部从这条流派生**。任何需要重建历史的 feature 都不需要重新实现——只要订阅同一组事件。

**4. `assistant/chunk` 事件保留原始 token 序列**——不只是拼好的 `assistant/message`，每个 chunk 都进 log。这是为什么「model-visible means logged」能严格成立：进模型的每一个字节都进 log。

dsh-at-file 的 `<workspace-reference path="docs/spec.pdf" />` 是这种机制的扩展——每条引用是一条新事件 `at-file-mention`，进 log、可从 log 重构、模型可见。dsh-genui 的 panel 持久化是同样的事——panel 状态通过事件投影，不存额外 mutable state。

## Turn flow：8 个 events 串成一条线

docs/agent-lifecycle.md 给出了完整的 mermaid sequenceDiagram。**driver 实现 Agent 接口**（`packages/core/agent-loop/src/agent.ts` 496 行 + `agent-loop/src/index.ts` 713 行），按下面顺序串起 8 个 events：

```text
turn/start (durable)
  ↓ claim next-step input + one queued message
  ↓
agent/pre-step  (waterfall：listeners wrap (messages, signal, next))
  - reject | enter(messages)
  - reject / 空 enter → close turn with no step
  ↓
step/start (durable)
  ↓ append entered messages as user/message
  ↓
agent/request (waterfall) → llm/stream (waterfall)
  ↓ StreamChunk* → assistant/chunk* → assistant/message (durable)
  ↓
tool/call (durable) → tools/pre-execute (waterfall) → tools/execute (parallel) → tools/post-execute (waterfall) → tool/result (durable)
  ↓ loop barriers and bounded rolling pool, reclassify before start
  ↓
step/end (durable)
  ↓
agent/turn-stopping (serial terminal checkpoint，无 next())
  ↓
turn/end (durable)
```

**每条 event 都有 dispatch mode 标签**（architecture.md + cordis-primer.md）：

| 事件 | dispatch mode | 谁能监听 |
|---|---|---|
| `session/event` | emit | 任意 plugin 持久化 / SDK / telemetry |
| `agent/*` | 大多 waterfall / parallel / serial | live coordination |
| `agent/pre-step` | waterfall | 可以改 messages / 拒绝 |
| `agent/request` | waterfall | 可以改 request body |
| `llm/stream` | waterfall | 可以拦截 stream chunks |
| `tools/pre-execute` | waterfall | 可以改 argv / 拒绝 |
| `tools/execute` | parallel | 实际执行 backend |
| `tools/post-execute` | waterfall | 可以改 result |
| `agent/turn-stopping` | serial | 决定 turn 是否提前关闭 |

**两种事件分类**：

- **Session events**（durable）：进 log、能 replay、能 fork、能 resume。`session/event` 是它们的总线。
- **Capability events**（swappable）：挂到 seam（`fs/*` / `tools/*` / `telemetry/*`）上，不 import 主 loop。

dsh-at-file 的 `agent/pre-step` 监听是 capability event 的典型用例——挂在 waterfall 上、读 messages、inject 引用消息、return next() 把 control 交还。dsh-genui 的 panel 持久化挂在 `session/event` emit 链上。

## Capability seams：三角色

`docs/capability-seams.md` 是 `scripts/gen-doc-graphs.ts` 生成的 mermaid 图——把 50+ packages 和 30+ services 的依赖关系画出来：

```text
A seam = swappable capability with three roles
  - Service Definition (声明接口)
  - Service Provider (实现接口)
  - Consumer (使用接口)
```

一个 package 可能同时承担多个角色，但「**只承担一个角色不算 seam**」——加 capability 必须设计完整三角色。

**典型例子：filesystem seam**

```text
Service Definition:  packages/fs        声明 ctx.fs 接口
Service Providers:  packages/fs-local  本地 fs 实现
                    e2b (sandbox backend)
Consumers:          packages/tool-fs    Read / Write tool
                    packages/shell      bash redirect 到 ctx.fs
```

**一个 provider swap 改整个产品**——把 `fs-local` 换成 `e2b`（云端 sandbox），`Read` / `Write` / `Bash` / `PTY` / `LSP` 全部跟着去远程，因为它们共享一个 execution world。这是 dsh 子代理（subagent provider）的同构设计：**换 provider = 换实现、换部署 target、换权限边界**。

## 「Where new behavior goes」17 个扩展点

architecture.md 给出了一张表，把「**我想要加 X，去哪里挂**」的 17 种情况全部覆盖：

| 目标 | 机制 |
|---|---|
| 加 model provider | 在 `ctx.llm` 注册 adapter |
| 加 model-facing capability | 在 `ctx.tools` 注册，schema 加入 prompt assembly |
| 给一个 session 不同的能力集 | 组合 agent preset；service row 需要 `isolate` realm |
| 加 shell execution | 注册 `ctx.shell` backend；local 后端 spawn 通过 `ctx.subprocess` |
| 加 persistent terminal execution | 注册 `ctx.terminals` backend + `dsh-tool-terminal` |
| 加 human command | 注册 `ctx.commands`；不触发模型 turn 直接 dispatch |
| 加 background work | 注册 `ctx.jobs`；`job_*` tools collect or stop it |
| 加 filesystem access or policy | 注册 `ctx.fs` provider 或监听 `fs/*` events |
| Confine spawned processes | 用 `ctx.sandbox` backend；consumer wrap argv 后 spawn |
| 拦截 request / tool / turn | 用对应 `agent/*` 或 `tools/*` event；`agent/turn-stopping` 停 turn |
| 加 model-facing context | 调 `agent.inject()`；进入下一个 admitted request |
| 加 UI / editor integration | drive `ctx.agents` 并从 `session/event` render |
| 加 Web Client Chat node | 注册 `ConversationNodeDefinition` + keyed renderer |
| 加 durable session state | 扩展 `SessionEventMap`；从 log render 和 replay |
| Generate session titles | 注册唯一的 `ctx.sessionTitle` provider |
| 管理同 session 的 objective | 用 `ctx.goals`；通过 `agent/*` 继续 |
| Fork a live session | `ctx.sessions.fork(source, boundary?, childSessionId?)` |
| Scope 注册到一个 agent | 用那个 agent 的 `agent.ctx` |

17 行表格读一遍大概 30 秒——这是「**我想加 X 应该改哪里**」的 query→action 映射表。dsh-at-file 和 dsh-genui 都在用这套映射：

- dsh-at-file：「拦截 request」→ `agent/pre-step` 监听 + 「加 durable session state」→ 不需要（它是 stateless reference marker）
- dsh-genui：「加 model-facing capability」→ `ctx.tools` 注册 `render_ui` 和 `validate_dsh_ui` 两个 tool + 「加 durable session state」→ 扩展 `SessionEventMap` 让 panel 状态从 log 投影

## 一个具体的 step：用户说"打开 docs/spec.pdf"

把抽象的事件流落到一段具体对话，看数据在 14 跳里怎么流：

**跳 1**：用户输入 `review @docs/spec.pdf`，输入通过 inbox。

**跳 2**：driver 收到 wake signal，`agent/status = running`，`turn/start` 进 log。

**跳 3**：driver claim pending next-step input + queued messages；`agent/inbox/claimed` 广播。

**跳 4**：`agent/pre-step` waterfall 触发：
- `dsh-at-file` 的 mention 监听执行 → 扫 `<user-message>` 的 `@[^\s@]+` → `expandMentions` 验证路径 → inject `<workspace-reference path="docs/spec.pdf" />` 消息
- listeners 调用 `next()` 把权威决定传下去

**跳 5**：决定是 `enter`（带新消息），driver 写 `step/start` 进 log，append `user/message`（包含原文 + inject 的 reference 标记）。

**跳 6**：driver 拉所有 prompt sections + tool schemas，触发 `agent/request` waterfall → 调 `ctx.llm.stream()` 走 `llm/stream` waterfall。

**跳 7**：模型返回 stream，driver 把每个 chunk 写 `assistant/chunk` 进 log；最终写 `assistant/message`（含 usage + sourceEventSeqs）。

**跳 8**：模型调 `read_file("docs/spec.pdf")` 工具，driver 写 `tool/call` 进 log。

**跳 9**：`tools/pre-execute` waterfall → `tools/execute`（parallel，local fs provider 跑 read）→ `tools/post-execute` waterfall → `tool/result` 进 log。

**跳 10**：loop 检查「模型还要不要 next step」——这里模型要 next step（基于 PDF 内容继续分析），claim 下一个 input，回到跳 4。

**跳 11**：（第二轮）重复跳 4-9，直到模型 `end_turn`。

**跳 12**：`step/end` 进 log。

**跳 13**：`agent/turn-stopping` serial checkpoint（无 next()，决定 turn 是否提前关）→ 通过。

**跳 14**：`turn/end` 进 log，`agent/status = idle`。

**整个 session 的全部事实现在都在 log 里**：用户输入 + dsh-at-file inject 的 reference + 每一 chunk 的 stream + 工具调用 + 工具结果 + 步骤边界 + turn 边界。任何后续的 fork / resume / transcript / telemetry 都能从这条流派生。

## 工程取舍：哪些决策是钉死的

**「No privileged core to patch」**。这条让 hot-patch 没有意义——加能力是挂 plugin 不是改主循环。代价是一些「**应该是在 core 但其实在 plugin**」的事变得笨拙（例如想改 agent loop 的内部状态只能监听 `agent/turn-stopping`）。

**「Model-visible means logged」 invariant + runtime assert**。任何进模型的东西必须能 log 重构。代价是新加 model-visible 输入必须先扩展 `SessionEventMap`。这条 invariant 是 dsh 整套 replay / fork / resume 能力的基础。

**`dsh-base` 是第一层**。所有 profile 都包含 dsh-base（model adapters / tools / persistence / sandbox / approval / settings / credentials / telemetry）。代价是 profile 不能「**完全空**」——至少要 base 的最小集。

**Capability seam 的三角色必须完整**。光定义 service definition + provider 不算 seam——必须还有 consumer。这条让一些「**纯内部能力**」必须外露为可消费接口。代价是 API surface 增大。

**Pre-release stance：foundation over blast radius**。AGENTS.md 第一条：

> With no external consumers, prefer the correct foundation over compatibility shims: rename or repackage freely and update every reference together. Backends reject old on-disk formats. SQLite uses monotonic `SCHEMA_VERSION`; `dsh-session` keeps `SESSION_FORMAT_VERSION` at `0` with no compatibility promise.

——因为还没正式 release，**优先正确地基而不是兼容垫片**。SQLite 用单调 `SCHEMA_VERSION`，`dsh-session` 维持 `SESSION_FORMAT_VERSION` 为 `0` 不承诺兼容。这意味着早期版本切换要重置数据，但**地基正确**比兼容性更重要。

**Snapshot testing**。`pnpm run test:snapshot` 是 keyless 的 ACP / headless replay vs 期望输出对比。这是 dsh 的「**replay-everywhere**」哲学——任何 replay 差异都是测试失败。代价是 snapshot 维护负担。

**Coverage 100% per-file**。`pnpm run test:coverage` 是 CI coverage gate：**per-file 100% on `packages/*/*/src`**。这条比 dsh-at-file 的 coverage 100% 更严——per-file 不是 per-package。代价是新加代码时必须补齐测试。

## 它故意没做的事

**没有跨 session 状态共享**。每个 session 独立 log；fork 是「**复制到子 session**」不是「**共享 mutable state**」。这是 event-sourced 的本质——但意味着「**两个 session 协作**」需要靠 fork / merge / external sync。

**没有内置的多模态输入支持**。Session event types 是文本流的扩展；图像 / 音频 / 视频要么作为 attachment 走（`pkg_attachment_local` / `pkg_host_runtime` 提供 attachment 服务），要么作为 binary blob 进 user message。模型原生多模态（GPT-4V / Claude vision）走 attachment 路径。

**没有内置的 user-facing auth**。`packages/identity/` 是 anonymous identity——session 之间的身份标识，但不假设企业级 SSO / OAuth / RBAC。这些由 deployment 自己加（plugin 路径）。

**没有内置的 billing / metering**。`ctx.tokenMeter` 是 **replay token measurement**——用于 replay 时算 token 成本，不是运行时计费。运行时的计费 / quota / 限流靠 deployment 自己。

**没有内置的 multi-tenant 隔离**。虽然 service row 可以指定 `isolate` realm，但 multi-tenant 数据隔离是 deployment 责任。

## 这件事为什么重要

dsh 主仓库回答的根本命题是：

> **AI agent 应用的运行时应该是可插拔的——没有 privileged core，没有热补丁，只有 plugin 组合。**

这条命题的工程落地是：把 model adapter / tool registry / session log / agent loop 本体全部做成 plugin，靠 Cordis 的 service registry + inject + reversible effects 串起来。下放换来三件事：

1. **一个 provider swap 改整个产品**——换 fs / sandbox / subagent provider，所有 consumer 自动跟着改
2. **turn flow 的每一步都能拦截**——pre-step 改 messages、llm/stream 改 chunks、tools/pre-execute 改 argv、turn-stopping 停 turn
3. **任何 model-visible 的东西都从 log 派生**——fork / resume / transcript / telemetry 都不需要重新实现

代价也很清楚：

- **plugin 边界严格**——核心 loop 改动需要修改多个 package 协同
- **pre-release 阶段没有兼容性承诺**——升级要重置数据
- **测试覆盖严格**——per-file 100% 是高门槛

代码层面，`Cordis service registry + append-only session log + agent pre-step waterfall + capability seam 三角色` 是这个范式能工程化落地的四个钉子。少一个，要么 plugin 边界失效、要么 replay 失败、要么 model 看到 log 看不到的东西、要么换 provider 不能传播。

`v0.x`（developer preview）阶段的 7,412 文件 / 30+ packages 是这件事的当前最优解。下一版本会是什么——也许 multi-tenant 隔离做进 core / 也许 SDK 升级到 typed streaming / 也许 `dsh-bundle-cloud` 上线做 SaaS——但「**everything is a plugin**」和「**Model-visible means logged**」这两个核心 invariant，大概率会留下。

## 维护指引：从 dsh 主仓库读后续工作的几件事

**和 dsh-at-file / dsh-genui 的关系**。这两个是 out-of-tree plugin——`dsh plugin --profile web add` 安装。它们挂的位置全部在 `Where new behavior goes` 表里。dsh-at-file 挂在 `agent/pre-step`（拦截 request）+ dsh-genui 挂在 `ctx.tools`（加 model-facing capability）+ `session/event`（加 durable state）。

**和 Cordis 论文的关系**。`Spatotemporal Composability` 是 Cordis 的设计哲学论文——「时空可组合性」意味着 plugin 在「**什么时候**」（time / lifecycle）+「**什么上下文**」（space / scope）两个维度可组合。`packages/core/scope/` 实现 scoped-registration primitive，`agent.ctx` 是这个 scope 的物理载体。

**和 Claude Code / Codex 的关系**。`packages/hooks/` 提供 Claude Code / Codex 的 hook bridges + wire-protocol library——这意味着 Claude Code 的 hooks 模型和 Codex 的 hooks 模型都被映射到 Cordis 的事件系统。`CLAUDE.md → AGENTS.md` 的符号链接不是修辞——Claude Code 直接读 AGENTS.md。

**vs Anthropic Claude Code / OpenAI Codex CLI**。dsh 的差异化定位是「**底层运行时 + plugin 协议**」而不是「**应用 + 命令行**」——Claude Code 是产品，dsh 是给产品用的平台。这条区别决定了 dsh 的 ergonomic 不一定对终端用户友好（要写 cordis.yml + 知道 service key + 知道 event dispatch mode），但**对构建 LLM 应用的团队**友好——所有人共用同一个 plugin 协议。

**Self-modification 路径**。`packages/self-modification/` 让 agent inspect/mount 它自己的 plugins。这条意味着 dsh 可以用于「**agent 修改自身运行时**」的场景——和 Cordis 的 reversible effects 哲学一致：所有 effect 都有 disposer，agent 改自己时也是干净的。

**测试哲学**。38 个测试类别覆盖：unit + snapshot + e2e（real-API）+ duplication detection + coverage 100%。`test:snapshot` 是 dsh 独有——keyless replay 对比期望输出。这意味着 dsh 的 regression coverage 偏向**端到端行为快照**而不是单元函数。

**未来路线图猜测**。基于「**Pre-release stance：foundation over blast radius**」原则，下一版本大概率继续修地基而不是堆 feature。可能性：multi-tenant 隔离进 core / `dsh-bundle-cloud` SaaS bundle / Python SDK 升 GA / typed streaming 替换部分 webhook 路径。

**Python SDK 现状**。`python/` 目录是 Python SDK + bundled runtime，但和 Node.js runtime 是两个 stack——Cordis 是 Node 框架，Python SDK 通过 JSON-RPC 协议调 Node runtime（`packages/sdk/` 的 JSON-RPC）。这意味着 Python agent 不是 in-process Python——是 RPC client 模式。

**Vendoring 决定**。`vendor/cordis` / `vendor/cosmokit` 等都是 vendored 源码（不是 npm dependency）。manifest + sync procedure 在 `vendor/README.md`。这条决策让 dsh 不依赖外部 npm registry 的可用性——**所有依赖都跟着仓库走**。代价是 PR 体积可能很大（升级 vendored package 时）。