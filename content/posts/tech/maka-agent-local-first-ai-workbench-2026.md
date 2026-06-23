---
title: "Maka：本地优先的 AI 桌面工作台，比 Cursor 更彻底的本地化与 6 组件 Runtime Kernel 演进"
date: "2026-06-23T18:32:23+08:00"
slug: "maka-agent-local-first-ai-workbench-2026"
description: "Maka 是一个 Electron 桌面 AI 工作台，把模型连接、会话、工具权限、文件读写、终端执行、搜索、机器人入口、开放网关和运行恢复放在一个本地优先的应用里。最近合并的 Runtime Kernel Extraction 把原来集中的 SessionManager / AiSdkBackend 拆成 6 个内部组件（ToolRuntime / ModelAdapter / RunTrace / AgentRun types & store / AgentRun execution / Startup recovery），同时保持了所有用户可见的会话/渲染/IPC/JSONL 兼容性。本文拆开它的 monorepo 拓扑、6 组件拆分、9 个 Memory Privacy Gates、凭据保护（Electron safeStorage）和多模型 / 多机器人接入架构，附上对独立 AI Agent 项目作者可复用的 5 条工程经验。"
draft: false
categories: ["技术笔记"]
tags: ["Maka", "Local-First", "Electron", "AI Agent", "Runtime Kernel", "Vercel AI SDK", "Google ADK", "Privacy Gates", "safeStorage", "OpenGateway", "Monorepo"]
hiddenFromHomePage: false
---

# Maka：本地优先的 AI 桌面工作台，比 Cursor 更彻底的本地化与 6 组件 Runtime Kernel 演进

## §1 项目定位

| 项目 | 内容 |
|------|------|
| **仓库** | github.com/Maka-Agent/maka-agent |
| **当前版本** | 0.1.0（活跃开发中） |
| **架构** | Electron + npm workspaces monorepo，5 个 packages + 1 个 desktop app |
| **目标用户** | 想在自己的电脑上跑一个可观察、可控、可持续恢复的 agent 的开发者 |
| **核心哲学** | 本地优先：模型连接元数据 / 会话 JSONL / 凭据加密 / 记忆文件 / 工具产物全部在用户文件系统里 |
| **接入模型** | 海外 3（Anthropic、OpenAI、Google Gemini）+ 国内 4（DeepSeek、Moonshot、Z.AI Coding Plan、Kimi Coding Plan）+ 本地 Ollama + 自定义 OpenAI Compatible + 账号订阅 3（Claude/Codex/Gemini CLI） |
| **机器人入口** | Telegram、飞书、企业微信、微信 iLink、Discord、钉钉、QQ |
| **设计文档** | 10 个 design docs（共 4888 行），其中 design-system.md 单文件 1622 行 |

Maka 不是另一个 chat demo，也不是 Cursor 的开源克隆。它的产品定位是**"本地优先的 AI 工作台"**——把模型供应商、工具执行、文件读取、终端命令、搜索、机器人消息、开放网关、运行恢复这 8 件事装进一个 Electron 桌面 app，让用户的数据**默认全部留在本地文件系统**。

这种定位决定了它的工程取舍：**不在云端提供"AI 服务"，而是在本地提供一个"AI 控制器"**。所以它的很多设计——凭据走 Electron `safeStorage`、Renderer 不拿明文密钥、9 个 memory privacy gates、Provider 状态真实呈现而不是假装可用——都不是"功能"，是**这套定位的必然推论**。

## §2 一张总览图

```
Maka
├── apps/
│   └── desktop/                   # Electron 桌面入口（main / renderer / preload）
├── packages/
│   ├── core/                      # 类型、contracts、领域模型（最纯的领域层）
│   ├── storage/                   # 文件持久化（JSONL / settings / credentials / run store）
│   ├── runtime/                   # Runtime 内核（ToolRuntime / ModelAdapter / AgentRun / RunTrace）
│   ├── headless/                  # 无桌面入口（CLI / CI / bot bridge / OpenGateway）
│   └── ui/                        # 渲染端通用组件库
├── docs/                          # 10 个设计文档
│   ├── runtime-kernel.md
│   ├── runtime-v2-architecture-evolution.md
│   ├── memory-threat-model.md
│   ├── workspace-privacy-context.md
│   ├── search-service-threat-model.md
│   ├── voice-threat-model.md
│   ├── ui-quality-plan.md
│   ├── design-system.md           # 1622 行
│   ├── full-product-test-plan.md
│   └── maka-capability-audit-v1.md
├── notes/                         # 工程笔记（reference-atlas / whitebox contract / bug flow audit）
├── scripts/                       # 构建 / 检查 / 截图 / 烟雾测试 / officecli 探测
└── package.json (npm workspaces)
```

仓库**只有 1 个 commit**（根目录 init commit），但**内容密度很高**——645 个文件、10 个 design docs、5 个 packages。代码组织遵循**"领域层在 core / 持久化在 storage / 运行时在 runtime / UI 通用组件在 ui / 入口在 apps"**的清晰分层。

## §3 Runtime Kernel Extraction：把大块拆成 6 个组件

### 3.1 改之前：所有事都在 `SessionManager` 和 `AiSdkBackend`

CHANGELOG 把这件事说得很清楚：

> "Maka already had the pieces of a local desktop coding agent: sessions, model streams, tool calls, permission prompts, abort handling, usage telemetry, bot and gateway entry points, and persisted session messages. The problem was that the core execution responsibilities were still concentrated in a few large runtime paths, especially `AiSdkBackend` and `SessionManager.sendMessage()`."

**症状**：每个用户 turn 的执行路径穿过 `SessionManager` → `AiSdkBackend` → 模型流 → 工具调用 → 权限检查 → abort → telemetry → RunTrace 写入，所有事交织在两个类里。

**问题**：
- 难推理——一次 turn 触发的边界太多，bug 经常不在你以为的地方
- 难恢复——中断后续启动要回放多个数据结构，没有单一 source of truth
- 难扩展——再加一个 provider 就要在 `AiSdkBackend` 里复制一遍 permission / tool / run / session-state 行为

### 3.2 改之后：6 个内部组件

```
SessionManager
  → AgentRun                              # 一次用户 turn 的执行单元
      → AiSdkBackend                       # Vercel AI SDK 桥接
          → ModelAdapter                   # provider 流 / 错误 / usage 归一化
          → ToolRuntime                    # 工具生命周期（验证 / 权限 / 看门狗 / abort / 失败分类 / 制品）
      → RunTrace                          # best-effort trace 写入（不致命）
      → AgentRunStore                      # sessions/<sid>/runs/<rid>/run.json + events.jsonl
```

6 个组件各自负责一个明确的边界：

| 组件 | 职责 | 不再属于谁 |
|------|------|------------|
| **ToolRuntime** | 验证工具输入、权限策略评估、parked 权限决策等待（带超时）、暂停/恢复流看门狗、abort 传播、工具失败分类、telemetry、制品记录、tool/permission trace events | 不再属于 `AiSdkBackend` |
| **ModelAdapter** | provider 流 / 错误 / usage 归一化、AI SDK 特定流分块、provider 错误映射 | 不再属于 `AiSdkBackend` 的 orchestration shell |
| **RunTrace** | best-effort 写入 model / tool / permission / abort / usage 事件；trace 失败不能影响主流程 | 独立路径，不进 renderer-visible `SessionEvent` |
| **AgentRun types** | `AgentRunHeader` / `AgentRunEvent` / `AgentRunStatus` / `AgentRunStore` 类型 | 不在 session JSONL 之外再发明结构 |
| **AgentRunStore** | 文件后端 run store（`sessions/<sid>/runs/<rid>/run.json` + `events.jsonl`） | 不在原 message 流上做 |
| **AgentRun execution** | 把重 turn 执行生命周期从 `SessionManager.sendMessage()` 移到 `AgentRun.execute()`（user message append / backend stream drive / 状态投影 / abort / 失败 / 持久化 trace 写入） | 不在 `SessionManager` |

### 3.3 这次改动的设计约束

CHANGELOG 明确写：

> "The intent is not to rewrite the runtime or replace the Vercel AI SDK. The goal is to make the existing runtime easier to reason about, easier to recover after interruption, and easier to extend with future backends or workflow integrations."

具体的设计约束：

1. **产品面稳定**——desktop / renderer / IPC / session JSONL / settings / bot / gateway 全部保持兼容，老用户升级无感
2. **Vercel AI SDK 仍为主流**——不换底层，AI SDK 仍作为主要 model / tool stepping 引擎
3. **启动恢复走 AgentRun ledger 优先**——`recoverInterruptedSessions()` 优先用 AgentRun ledger 修复 stale non-terminal runs，老 session 仍走 legacy message/turn-state 兜底
4. **RunTrace 是 best-effort**——trace 写入失败不能修改 model 或 tool 的执行结果

### 3.4 一句话总结这次改动

把"什么都在两个类里"的状态，拆成"6 个明确边界的内部组件 + 1 个文件后端 run store"，**用户面 0 改动、底层 6 倍清晰度**。

## §4 Runtime v2：下一阶段的中心是 Invocation + RuntimeEvent + AgentFlow

### 4.1 当前架构的不够

`docs/runtime-v2-architecture-evolution.md` 把"为什么还要继续改"说得很坦白：

> "The current architecture is better than the original monolithic path, but the runtime still lacks one stable center of gravity. The same run is currently represented through several related but separate structures:
> - `StoredMessage` in the session JSONL
> - renderer-facing `SessionEvent`
> - `AgentRunEvent` in the run ledger
> - best-effort `RunTraceEvent`
> - telemetry records
>
> That split makes the system hard to evolve. It also makes important questions harder than they should be:
> - Which facts are the real runtime truth?
> - Which objects are only UI projections?
> - Which events should be replayed into the next model request?
> - Which events are diagnostic-only?
> - Where should permission, tool, recovery, and telemetry semantics live?"

**核心问题**：同一个 run 被 5 个结构并行表示，5 个结构各自是"局部真相"——`StoredMessage` 是历史、`SessionEvent` 是 UI 投影、`AgentRunEvent` 是 ledger 事件、`RunTraceEvent` 是诊断、telemetry 是指标。当你要回答"哪些事件该回放到下一次模型请求"时，要在 5 个结构里交叉过滤。

### 4.2 参考 Google ADK Go 的分层

作者从 Google ADK Go 的 `Runner → Agent → Flow → Model/Tool → Event → Session` 分层里学到一条：

> "The useful lesson is not to copy type names directly. The useful lesson is the layering:
> - `Runner` owns the invocation shell and persistence boundary.
> - `Agent` owns lifecycle and routing.
> - `Flow` owns the model/tool loop.
> - `Event` is the shared runtime fact language.
> - `Session` stores durable history and scoped state.
> - tool, callback, plugin, instruction, workflow, entrypoint, and telemetry layers attach around that axis without becoming the axis themselves."

**关键洞察**：ADK 的分层是"围绕一条中心轴挂能力"，不是"每个能力自己一个轴"。Maka 的当前架构更像后者。

### 4.3 目标架构

```
RuntimeRunner                         # invocation shell + persistence boundary
  → InvocationContext                 # 单次调用的上下文
  → AgentFlow                         # model/tool 循环
      → AiSdkFlow                     # Vercel AI SDK streamText + ToolRuntime
  → RuntimeEvent ledger               # canonical 事件流
  → projections                       # 投影到 StoredMessage / SessionEvent / RunTrace / Telemetry
```

**关键的 shift**：

```
今天：
  SessionManager + StoredMessage / SessionEvent 接近 runtime 中心

目标：
  Invocation + RuntimeEvent + AgentFlow 是 runtime 中心
  StoredMessage、renderer SessionEvent、AgentRunStore、RunTrace、telemetry
  全部变成"投影 / ledger"，从 canonical 事件派生
```

### 4.4 迁移的 5 条边界

文档显式声明的迁移约束：

1. **AI SDK 仍为长期主流**——不替换 Vercel AI SDK
2. **保持 Electron + 现有 user-visible 行为**——JSONL 兼容性
3. **复用 `ToolRuntime` / `AgentRunStore` / `RunTrace`**——不推倒重来
4. **避免 flag day**——不一次性换掉所有 storage 和 UI 投影
5. **坚持 AI 适配本地产品约束**——不照搬 ADK 类型名

**一句话总结 Runtime v2**：把"5 个并列真相"收敛为"1 个 canonical 事件 + 5 个投影"，迁移以"复用 + 渐进"为底线。

## §5 9 个 Memory Privacy Gates：本地记忆的隐私设计

`docs/memory-threat-model.md` 是 Maka 最值得读的设计文档之一。PR-MEMORY-1 标注为 **contract-only**——只定义类型和 validator，不加 IPC、storage、UI、settings。

### 5.1 源分离（gate #8 + 类型系统）

Memory 不是一个 surface，contract types 把它们分开，避免"准记忆观察"通过类型变成"持久记忆条目"：

```ts
type MemorySource = 'user_authored' | 'chat_extracted';         // 可持久
type MemoryCandidateSource =
  | 'voice_transcript'
  | 'activity_observation'
  | 'cu_observation'
  | 'search_recall'
  | 'daily_review';                                            // 不可持久

interface DurableMemoryEntry  { source: MemorySource; ... }
interface DraftMemoryEntry    { source: MemoryCandidateSource; ... }
```

`MemorySource` 和 `MemoryCandidateSource` 是**不相交的两个 enum**。语音转写稿永远 type-check 不进 `DurableMemoryEntry`，连 validator 都走不到。

### 5.2 9 个 Privacy Gates 全表

| # | Gate | 落实位置 |
|---|------|----------|
| 1 | **default-off** | `MEMORY_MODES` 含 `'off'`；新装 snapshot 必须是 `'off'`；validator step #1 拒 `MemoryBlockReason='mode_off'` |
| 2 | **manual confirm before durable write** | durable `'active'` 路径必填 `confirmedAt`；缺失/无效时拒 `MemoryBlockReason='manual_confirm_required'` |
| 3 | **reversible delete/export** | v1 contract 无 auto-write；下游 packet 加任何 write driver 前必须先有 `delete` + `export` shape |
| 4 | **incognito read+write disable** | `MemoryWriteRequestContext.incognitoActive` 短路 validator；未来 read path 也必须用同一 flag gate |
| 5 | **no auto sleep consolidation** | `MemorySource` 和 `MemoryCandidateSource` 都不含 automated consolidation source；加一个就是 contract change |
| 6 | **visible citation** | `MemoryUsePolicy` 只允许 `'never'` 或 `'cited_only'`，**没有 `'silent'`**；加 `'silent'` 必须扩 enum |
| 7 | **no hidden activity promotion** | `activity_observation` / `cu_observation` 只在 `MemoryCandidateSource`；validator 拒 `persistenceState='active'` |
| 8 | **provider+embedding leakage boundary** | `MemoryCapabilitySnapshot.embeddingProvider` 硬编码 `'disabled'`；下游 wiring provider 必须扩 snapshot type |
| 9 | **renderer cannot forge provenance/readiness** | `MemoryWriteRequestContext.originatedFromRenderer=true` 直接拒 durable `'active'` 写——即使 `confirmedAt` 合法 |

### 5.3 准记忆的 exclusion list

这 9 个 surface 都含**用户相关数据**，但都不能被当成 `MemorySource`、不能自动升级：

- `settings.json`（个性化字段、onboarding milestones）
- `skills/`（用户安装的 skill 内容）
- `usage_log`（历史查询 / 延迟 / 错误）
- `sessions/*/session.jsonl`（会话历史）
- `workspace/` 指令文件（prompt-time injection only）
- Capability snapshot + runtime probe history（Health Center）
- Visual-smoke 固定数据
- Daily Review 候选（post-Daily Review lane）
- Search index hits
- Voice transcripts
- CU / Activity observations

### 5.4 关键洞察：9 个 gate 是 design decision，不是 feature

这 9 个 gate 不是"实现一个安全开关"那种 feature——是**对"AI 主动学用户"这件事的边界声明**。每一条都在说：AI 不能在你不知道的时候把信息写进它的记忆。

具体说：

- **Gate 1 + 2**：默认关 + 手动确认。意味着用户**主动打开** + **逐条确认**才能加 memory，不是开了就持续写
- **Gate 4**：隐身模式下连 read 都要 disable。意味着隐身不是"读但不写"，是"完全无状态"
- **Gate 5**：无自动睡眠合并。意味着不会半夜偷偷合并你的 memory entry
- **Gate 6**：没有 silent 引用。意味着 agent 引用 memory 时一定 visible 标注
- **Gate 8**：embedding provider 硬编码 disabled。意味着 v1 不会偷偷把 memory 发到 OpenAI 做 embedding
- **Gate 9**：renderer 端不能伪造 provenance。意味着恶意扩展不能"代表用户"加 memory

## §6 凭据保护：4 类密钥走 Electron safeStorage

README 把凭据保护说得很直白：

> "Provider 连接元数据和 session JSONL 在本地文件系统。**API key、OAuth token、bot token、proxy password、gateway token、Tavily key 等敏感值走 Electron `safeStorage` 加密后写入 `credentials.json`**。Renderer 不直接拿明文密钥；Settings 只显示 masked 状态和测试结果。"

### 6.1 4 类密钥的处理路径

| 密钥类型 | 加密 | 存储位置 | Renderer 可见性 |
|----------|------|----------|-----------------|
| Provider API key | safeStorage | `credentials.json` | masked（不显示明文） |
| OAuth token | safeStorage | `credentials.json` | masked |
| Bot token（Telegram/飞书/Discord 等） | safeStorage | `credentials.json` | masked |
| Proxy password | safeStorage | `credentials.json` | masked |
| Gateway token | safeStorage | `credentials.json` | masked |
| Tavily key | safeStorage | `credentials.json` | masked |
| LLM 连接元数据 | 不加密 | `llm-connections.json` | 完整 |
| Session JSONL | 不加密 | `sessions/` | 完整 |
| 用户 settings | 不加密 | `settings.json` | 完整 |

### 6.2 设计意图

- **凭据分层**——secret 和 metadata 分离：metadata 让用户能查"我接了哪些 provider"，secret 让 renderer 只能问"这个连接能不能用"
- **Renderer 不持密**——preload 暴露的是 "test connection" 这种操作接口，不是 "read api key" 这种读取接口
- **Settings 只显示 masked**——比如 `sk-••••••••••••••••••abcd`，不显示明文
- **测试结果可读**——连接成功/失败、延迟、错误类别可读，方便用户排查

**这是"本地优先"的必然推论**——既然数据全在本地，凭据就是最大风险源。把凭据做对了，本地优先的隐私承诺才真正成立。

## §7 多模型接入：13 个入口的 provider 抽象

README 列出已接入的模型类型：

```
海外 API：Anthropic、OpenAI、Google Gemini
国内 API：DeepSeek、Moonshot、Z.AI Coding Plan、Kimi Coding Plan
本地模型：Ollama
自定义网关：OpenAI Compatible endpoint
账号订阅入口：Claude Subscription、Codex Subscription、Gemini CLI
```

13 个入口的接入方式在 `packages/core/src/llm-connections.ts` 和 `packages/runtime/src/model-factory.ts` 实现，关键设计：

### 7.1 真实连接状态 vs 伪装可用

README 反复强调一件事：

> "账号订阅入口：Claude Subscription、Codex Subscription、Gemini CLI 等**仍按实验/可用状态分开呈现，未接入发送链路的入口不会伪装成可用**。"

落到 UI 上：用户看到的"已接入"列表和实际能用的列表必须严格一致。如果某个 provider 接了 OAuth 但还没接通消息发送链路，UI 必须显示"实验/不可用"——不能为了让界面好看而伪装修好了。

### 7.2 首跑引导根据真实连接状态

> "首次进入 Maka 时，如果还没有可用模型连接，首屏会引导你完成 AI 配置，而不是直接给一个不能发送的空聊天框。推荐路径是：打开 设置 → 模型 → 选择一个真实模型供应商，填写 API key 或完成已接入的账号登录 → 测试连接并选择默认模型 → 回到首屏。"

**关键设计**：首屏不是空 chat box + 错误提示，而是**主动引导补配置**。这是 CLI/桌面工具的标准做法，但很多 AI 工具反而在 web 端养成了"空 chat box + 错误"的坏习惯。

### 7.3 Provider error mapping 走 ModelAdapter

CHANGELOG 把 `ModelAdapter` 的职责明确：

> "`ModelAdapter` is the provider-facing stream and error normalization layer. It keeps AI SDK-specific stream chunks, provider setup, usage normalization, and provider error mapping out of the higher-level backend orchestration shell."

**关键设计**：provider 错误归一化（rate limit / auth fail / timeout / model overloaded）都在 `ModelAdapter` 收口。**未来加新 provider 不会污染 `AiSdkBackend` 的 orchestration**。

## §8 OpenGateway + 多机器人入口：让 AI 工作台接入既有消息流

### 8.1 OpenGateway

README 描述：

> "**开放网关**：本地 HTTP/SSE API，用 token 保护外部读取会话状态、事件、能力和健康摘要。"

这是一个**本地 HTTP/SSE 入口**——其他程序可以通过 token 读取 Maka 的会话状态、事件、能力、健康摘要。

**关键设计意图**：让 Maka 不只是"一个 Electron app"，而是"一个本地 AI 控制器"——其他工具（IDE、CI、自定义脚本）能**只读**地观察它的状态。

**和 memory threat model 的一致性**：本地 HTTP 入口需要 token 保护，token 走 safeStorage 加密。这与"memory 不允许 unauthenticated local route"是同一条隐私规则。

### 8.2 7 个机器人入口

```
Telegram、飞书、企业微信、微信 iLink、Discord、钉钉、QQ
```

每个入口都走同一套**配置/测试/运行状态框架**。这是 6-21 跨平台发布脚本的反向案例——Maka 把"消息入口"做成了**统一框架**，不是每个平台写一套。

设计意图：用户在 Telegram 上的对话和 UI 内的对话**共享同一套 session 存储**——`sessions/*/session.jsonl` 是不分入口的。bot 入口只是"消息来源"不同。

## §9 启示：给独立 AI Agent 项目作者的 5 条工程经验

读完 Maka 的代码和文档，5 条对独立项目作者可复用的工程经验：

### 9.1 Runtime 不要"以 SessionManager 为中心"

Migrating from "所有事在一个大类里"到"6 个边界清晰的内部组件"，用户面 0 改动——这是 6 月所有 AI Agent 项目都应该走的路。

**反模式**：在 `SessionManager` / `BotManager` / `Agent` 这种"大管家"类里塞所有逻辑
**正路**：把 runtime 拆成 6+ 个内部组件（ToolRuntime / ModelAdapter / RunTrace / AgentRun types & store / AgentRun execution / Startup recovery），让一个用户 turn 沿一条明确的边界链执行

### 9.2 把"5 个并列真相"收敛成"1 canonical + N 投影"

Runtime v2 演进的核心是把 `StoredMessage` / `SessionEvent` / `AgentRunEvent` / `RunTraceEvent` / `telemetry` 5 个结构收敛成一个 `RuntimeEvent` 中心 + 5 个投影。

**反模式**：5 个数据结构并行存在，每次改一个就要同步改 5 个
**正路**：先识别 1 个 canonical 事件流，再决定哪些字段进哪个投影

### 9.3 隐私设计靠"9 个 gate"，不靠"1 个开关"

大多数 AI Agent 项目用 1 个 "memory on/off" 开关来假装有隐私。Maka 拆成 9 个独立可验证的 gate（default-off / manual confirm / reversible / incognito / no auto consolidation / visible citation / no hidden promotion / embedding provider disabled / renderer can't forge）。

**反模式**：1 个总开关 → 内部随便写
**正路**：9 个独立 gate → 每个 gate 单独 validator 拒绝特定情况，类型系统 + 校验器双层防护

### 9.4 凭据分层 + Renderer 不持密

凭据走 `safeStorage` 加密，Renderer 不持明文，Settings 只显示 masked。

**反模式**：把 API key 存在 localStorage / settings.json / window 对象里
**正路**：secret 走 OS 级加密（safeStorage / Keychain / libsecret），metadata 走普通存储，Renderer 只暴露"操作接口"不暴露"读取接口"

### 9.5 Provider 真实可用 vs 伪装可用

UI 上"已接入"的 provider 必须和"实际能用"的 provider 严格一致。

**反模式**：为了让界面好看显示"已接入 OpenAI"但实际没接通
**正路**：provider 接通链路有明确状态（实验 / 可用 / 不可用），UI 必须按真实状态显示

## §10 关联阅读

| 主题 | 推荐阅读顺序 |
|------|--------------|
| **想看完整 Runtime Kernel 改动** | `docs/runtime-kernel.md`（277 行）→ `CHANGELOG.md` |
| **想看 Runtime v2 演化方向** | `docs/runtime-v2-architecture-evolution.md`（660 行）→ `docs/runtime-v2-implementation-notes.md` |
| **想看 Memory 隐私设计** | `docs/memory-threat-model.md`（119 行）→ `docs/workspace-privacy-context.md`（142 行） |
| **想看设计系统** | `docs/design-system.md`（1622 行）→ `docs/ui-quality-plan.md` |
| **想看测试计划** | `docs/full-product-test-plan.md`（544 行） |
| **想看能力清单** | `docs/maka-capability-audit-v1.md`（734 行） |

仓库只 commit 1 次（根 init），但 645 个文件 + 4888 行 design docs + 5 个 package + 1 个 desktop app 的内容密度，是值得反复读的工程样例。

---

**参考来源**：

- GitHub 仓库：github.com/Maka-Agent/maka-agent（v0.1.0，npm workspaces monorepo）
- 关键设计文档：`docs/runtime-kernel.md`、`docs/runtime-v2-architecture-evolution.md`、`docs/memory-threat-model.md`、`docs/workspace-privacy-context.md`、`docs/design-system.md`
- CHANGELOG：Runtime kernel extraction + Hardening phases 1-5
- Package 结构：packages/{core,storage,runtime,headless,ui} + apps/desktop
