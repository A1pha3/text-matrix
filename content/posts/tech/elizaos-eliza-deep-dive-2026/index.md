---
title: "elizaOS 深度解构:18.9K stars 的本地优先 AI Agent OS 到底在做什么"
date: 2026-08-03T15:42:00+08:00
draft: false
slug: "elizaos-eliza-deep-dive-2026"
tags: ["agent", "ai-os", "typescript", "open-source", "architecture", "elizaOS"]
categories: ["tech"]
description: "18,886 stars 的 elizaOS/eliza 不只是又一个 agent 框架。它把自己定位成 agentic operating system,把 runtime、agent loop、plugin model、memory/state primitives、整机的 Linux/Android 系统镜像、桌面/移动 app、optional cloud 全塞进一个 monorepo。本文逐层拆开。"
---

# elizaOS 深度解构:18.9K stars 的本地优先 AI Agent OS 到底在做什么

仓库:[github.com/elizaOS/eliza](https://github.com/elizaOS/eliza)
代码量:仅 `@elizaos/core/src/runtime.ts` 一文件就 11,782 行
维护方:elizaOS(原 ai16z 团队,基于 Shaw 的 eliza 框架演进)
最新版本:v2.0.4 · MIT 协议
本文完成时:18,886 stars / 5,604 forks / 447 issues / 146 watchers

## 1. 一句话定位:Agent 的操作系统

`elizaOS` 把自己叫 **agentic operating system**——这个定语不是修辞。

读 README 第一段就能看出它和 LangChain / CrewAI / AutoGen 这类"agent 框架"的差别:

| 维度 | 框架 | elizaOS |
|---|---|---|
| 部署形态 | Python/Node 包,嵌入到你的 app | 一套完整 OS(可启动的 Linux desktop、Android system image)+ 跨平台 app(web/desktop/mobile)+ runtime + cloud |
| 数据归属 | 调用方服务,数据上云 | **local-first**,agent、数据、模型全在设备上,cloud 完全可选 |
| 模型来源 | 单一 provider 或多 provider 调用 | 自家 **Eliza-1** 模型家族(Gemma-4 衍生,~2B 跑手机,~27B 跑桌面)+ OpenAI / Anthropic / Gemini / Grok / Llama 全部可选 |
| 运行时 | 一次推理调用 | **AgentRuntime** 11k 行类,长期驻留进程 |
| 边界 | 业务代码 | **app 一等公民**——plugin 可以成为 surface,在 runtime 里被 install/launch/track,跨重启存活 |

LangChain 是写一个调用 LLM 的程序。elizaOS 是装一个会说话的操作系统。差别是部署形态、生命周期和资产归属三个维度同时翻转。

## 2. 仓库结构:42 个子包的全景

`packages/` 下不是按 feature 切,而是按 **runtime / surface / capability / tooling** 四层切:

```
packages/
├── 运行时核心
│   ├── core/              ← @elizaos/core:AgentRuntime + plugin model
│   ├── agent/             ← @elizaos/agent:AgentRuntime 实例化层
│   └── elizaos/           ← CLI:create / info / upgrade
│
├── Surface(用户看得见的壳)
│   ├── app/               ← Eliza app UI(Vite + React)
│   ├── app-core/          ← app 运行的 API + dashboard host
│   ├── cloud-ui/          ← 云端 dashboard
│   └── homepage/          ← elizaos.ai 官网
│
├── 操作系统本体
│   ├── os/linux/          ← amd64 / arm64 / riscv64 bootable Linux desktop
│   ├── os/android/        ← Android system image,Eliza 当 launcher
│   ├── native/            ← 硬件抽象层
│   └── eliza-computer/    ← 整机协调
│
├── Capability 插件
│   ├── plugin-browser/    ← 浏览器自动化
│   ├── plugin-documents/  ← RAG
│   ├── plugin-phone/      ← 电话 / SMS
│   ├── plugin-task-coordinator/
│   ├── plugin-anthropic/  plugin-openai/  plugin-groq/  plugin-zai/
│   ├── plugin-local-inference/  plugin-ollama/
│   ├── plugin-agent-orchestrator/
│   └── plugin-sql/        ← Postgres(PGlite)+ 关系数据库适配
│
├── 云端(可选)
│   ├── cloud/             ← 托管后端
│   ├── contracts/         ← 链上合约
│   └── eliza-hub/         ← app marketplace
│
└── 工具链
    ├── docs/              ← 文档
    ├── benchmarks/        ← lifeops-bench 等
    ├── scenario-runner/   ← e2e 场景
    ├── corpus-tools/      ← 训练数据
    ├── training/          ← 模型训练
    ├── evidence/          ← PR review evidence store
    └── registry/          ← plugin registry
```

42 个 workspace 包 + 36 个 root dependencies(其中 11 个是 `@elizaos/*` workspace 插件)+ 48 个 devDependencies,引擎 `node@24.15.0`。这不是 demo 项目,这是产品级的 monorepo。

## 3. 运行时核心:`AgentRuntime` 11,782 行

`@elizaos/core/src/runtime.ts` 是整个仓库的"宪法"。文件头注释(原文翻译):

> `AgentRuntime` 是每个 Eliza agent 跑在上面的中央编排器,具体实现 `IAgentRuntime`。一个实例拥有一个 agent 的整个世界:它的 actions / providers / evaluators / services、model-handler registry 和 `useModel` dispatch/routing/fallback 层、plugin 集和它的生命周期(register / unload / reload / config)、memory 和 state(database adapter / embeddings / `stateCache` / working memory),以及跑 provider → model → action → evaluator 的 message loop。Plugin 贡献 capability,runtime 装配并跑它们。**`@elizaos/core` 几乎全部和每个 plugin 最终都和这个类对话**。
>
> 文件大约 1 万行——**按符号导航,不要从上往下读**。

### 3.1 三条不变式

`runtime.ts` 文件头注释里写明了三条 invariant:

**不变式 1:多租户不读 env**
```ts
// getSetting() 解析 per-agent config,DELIBERATELY 永不读 process.env
// ——在多租户进程里,这会把宿主秘密泄漏到每个 agent
// 宿主应该把 dotenv 折进构造函数 settings map
```

这种注释级别说明作者考虑过多租户场景下的 env 泄漏问题。

**不变式 2:embedding 宽度 pin 到首次应答的 provider**
```ts
// Embedding 宽度 pin 在首次回答 boot dimension probe 的 TEXT_EMBEDDING provider 上
// 来自不同 provider 的后续 embedding 可能 emit 一个 SQL adapter 静默丢掉的宽度 (#8769)
// 如果所有 provider 都 fail probe,initialize() 非致命 catch EmbeddingDimensionProbeError
// 并禁用 embedding generation 而不是 crash boot
```

`#8769` 是 GitHub issue 编号——跨文件引用 issue 是生产级代码的常见做法。

**不变式 3:无 database adapter 的降级路径**
```ts
// 没有 database adapter 时,initialize() 仅在 ALLOW_NO_DATABASE 时
// 才会 fallback 到 in-memory adapter
```

`ALLOW_NO_DATABASE` 是显式 opt-in 开关——**默认拒绝 in-memory fallback**,要求显式选择内存模式,这是个安全/正确性的取舍。

### 3.2 消息循环骨架

```
message → providers(state/context)
       → dynamicPrompt
       → model(useModel dispatch,带 fallback chain)
       → response handlers
       → actions(模型可调用)
       → evaluators(后置评估)
       → memory persist(stateCache → DB)
       → post-delivery tasks
```

`useModel` 是 runtime 提供的统一调用入口,内部走:
1. `resolveChain` 决定调用顺序
2. `executeChainWithFallback` 跑 + fallback
3. `maybeReroute` 处理错误重路由

**模型无关**(model-agnostic)不是说模型不重要,而是说换 provider 是配置改动,不是代码改动。

## 4. 2026 年的最新演进:从 CHANGELOG 看到的三个方向

读 `@elizaos/core/CHANGELOG.md` (Unreleased 部分),能看到 elizaOS 在 2026 年的三个工程方向。

### 4.1 Prompt caching 段标记(prompt segments)

传统 prompt 调用的问题是每次调用重发整个 system prompt。2026 年 Anthropic ephemeral cache、OpenAI/Gemini prefix cache 都要求主动声明"哪些段是稳定的"。

`elizaOS` 的解法:`GenerateTextParams` 新增可选字段 `promptSegments?: PromptSegment[]`,每个 segment 是 `{ content, stable }`。runtime 在 `dynamicPromptExecFromState` 里把动态 prompt 按 stable 边界切段:

| 段 | stable? |
|---|---|
| format prefix | ✅ |
| variable block | ❌ |
| validation/middle block | ❌ |
| format suffix | ✅ |
| end block | ❌ |

CHANGELOG 原文解释:_"Marking validation or variable content as stable would prevent cache hits because that content changes every call; splitting format from validation ensures the stable segments are actually cacheable."_

然后 plugin 层各自实现:
- **Anthropic plugin**:每个 segment 一个 content block,stable 的打 `cache_control: { type: "ephemeral" }`
- **OpenAI / Gemini plugin**:stable 段前置(前缀缓存靠的就是"前面那 N token 一样")

core 表达语义、plugin 做 provider-specific 优化,这是 runtime 层的合理切分。

### 4.2 跨 runtime 任务调度器(cross-runtime task scheduler)

`TaskService` 在 2026 之前是每个 agent 一个 setInterval。问题显而易见:N 个 agent = N 个 DB query / 秒。

新版提供三种调度模式,按部署形态选:

| 模式 | 适用 | 行为 |
|---|---|---|
| **local timer** | 单进程 | 每个 TaskService 一个 setInterval |
| **per-daemon** | 多 agent 守护进程 | host 调 `startTaskScheduler(adapter)`,共享 timer + 批 `getTasks(agentIds)` |
| **serverless** | 无长进程 | `runtime.serverless === true`,host 用 cron / per-request 调 `runDueTasks()` |

`serverless?: boolean` 是 `AgentRuntime` 构造参数。elizaOS 已经准备好跑在 Lambda / Vercel / Cloudflare Workers 这种 ephemeral runtime 里,这是传统 agent 框架较少考虑的场景。

任务系统本身也升级:`TaskMetadata` 加了 `notBefore` / `notAfter` / `paused` / `failureCount` / `maxFailures` / `lastError` / `baseInterval`,dead-letter 机制首次出现。

### 4.3 共享 batch queue 子系统

之前的痛点:每个 service 都自己写一个 queue + retry + task 的小循环,然后这些实现慢慢 drift。

2026 年的统一:`utils/batch-queue` 模块提供 `PriorityQueue` / `BatchProcessor`(信号量并发 + retry)/ `TaskDrain` / 组合 `BatchQueue` / 共享 `Semaphore`。

CHANGELOG 原文解释:_"The runtime is not globally 'batching-bound'; a minimal fix in one service could be a few lines. The goal here is forward-looking consolidation so embedding drains, action-index embedding, batcher affinity scheduling, and shared throttling do not each grow a bespoke queue + task + retry stack that drifts over time."_

## 5. Plugin model:四件套 primitives

文档明确写了 plugin 的四类出口:

```ts
export interface Plugin {
  actions: Action[]            // agent 能做什么
  providers: Provider[]        // 给 prompt 提供上下文
  services: Service[]          // 长生命周期单例
  evaluators: Evaluator[]      // 后置处理(reflection, summarization)
}
```

加上面提到的 `character`(角色设定 / system prompt 主体)和 `routes`(HTTP API),一个 plugin 就把"能干、能想、能持久、能演"四件事都接上。

举例:
- `plugin-browser` 提供一个 `service`(浏览器连接池)+ 一组 `actions`(click/type/navigate)+ 一个 `provider`(当前 URL/DOM 摘要)
- `plugin-anthropic` 只贡献一个 `model handler`,把 `useModel` 调用转发到 Anthropic API

你贡献的是 capability,不是孤立的代码。

### 5.1 实战:跑一个最小 plugin

```bash
# 1. 装 CLI
bun add -g elizaos@beta

# 2. 起一个新 plugin workspace
elizaos create my-plugin -t plugin
# 输出:一个带 package.json + src/index.ts 的最小 plugin 工程

# 3. 写 src/index.ts
```

```ts
import type { Plugin, Action } from "@elizaos/core";

const greetAction: Action = {
  name: "GREET_USER",
  similes: ["say_hi", "wave_hello"],
  description: "Greets the user by name.",
  validate: async (runtime, message) => true,
  handler: async (runtime, message, state, options, callback) => {
    const name = state?.values?.name ?? "stranger";
    const text = `Hello, ${name}!`;
    await callback({ text });
    return { success: true, text };
  },
  examples: [
    [{ user: "user", content: { text: "say hi to Alex" } },
     { user: "assistant", content: { text: "Hello, Alex!" } }],
  ],
};

export const myPlugin: Plugin = {
  name: "my-plugin",
  description: "Tiny greeting plugin.",
  actions: [greetAction],
};
```

```bash
# 4. 在 dev runtime 里挂上
bun run dev
# 你的 plugin workspace 通过 turbo task 被 runtime 自动加载
# 在 app 里发 "say hi to Alex" → agent 调 GREET_USER → 回复 "Hello, Alex!"
```

### 5.2 实战:在 plugin 内部调 model

```ts
import { elizaLogger } from "@elizaos/core";
import type { Action } from "@elizaos/core";

const summarizeAction: Action = {
  name: "SUMMARIZE_TEXT",
  description: "Summarize a long text using the configured model.",
  validate: async (runtime, message) => {
    return (message.content as any)?.text?.length > 200;
  },
  handler: async (runtime, message, state, _options, callback) => {
    const input = (message.content as any).text as string;

    // useModel 是统一入口,内部走 resolveChain + fallback chain
    const result = await runtime.useModel(
      "TEXT_LARGE",                       // model type (注册于 model-gateway)
      {
        prompt:    `Summarize:\n\n${input}`,
        // Prompt segment 切分 — runtime 复用 prompt cache
        promptSegments: [
          { content: "You are a concise summarizer.\n\n", stable: true  },
          { content: `Text: ${input}`,                   stable: false },
          { content: "\n\nReply in one sentence.",      stable: true  },
        ],
        temperature: 0.2,
        maxTokens:  120,
      }
    );

    const summary = (result as string).trim();
    await callback({ text: summary });
    elizaLogger.info("summarize.done", {
      agentId:   runtime.agentId,
      inputLen:  input.length,
      outputLen: summary.length,
      modelUsed: result?.$meta?.provider,   // fallback 用了哪个 provider
    });

    return { success: true, text: summary };
  },
  examples: [
    [{ user: "user", content: { text: "a long text…" } },
     { user: "assistant", content: { text: "a one-line summary" } }],
  ],
};
```

这一段把 4.1 节的 prompt segments、3.2 节的 useModel 调用、6 节的 logger 一次性串起来,展示了 runtime 的核心调用范式。

整个流程 5 分钟,不用碰 YAML、不用写 Dockerfile、不用写 deployment script。

## 6. 安全与隐私

`@elizaos/core/src/security/` 下三个关键目录:

- `redact/` —— 日志/对象/字符串 secret 脱敏,`redactSecrets` / `redactObjectSecrets` / `redactLogArgs` / `redactSensitiveText`
- `secret-swap/` —— `SecretSwapSession`,运行时用一次性 placeholder 替换真实 secret,只在出站前还原
- `index.ts` —— PII 识别 + owner-exclusive disclosure,带 `PseudonymSession` 和 `GuardedStreamScanner`

README 上专门一段叫 "Private by default"。`Eliza-1` 模型家族 + 语音本地推理 + 图像本地描述是工程承诺,不是 marketing 词。`ALLOW_NO_DATABASE` 这种开关,以及 `#8769` 这种 issue 的存在,说明安全/隐私默认是 ON。

## 7. 操作系统层:`packages/os`

只看 `app/` 会觉得这是一个 AI 桌面应用。看 `packages/os/` 才会意识到这是一个真操作系统。

```
packages/os/
├── linux/    ← amd64 / arm64 / riscv64 bootable Linux desktop
├── android/  ← Android system image,Eliza 当 launcher
```

README 上明说:

> [`packages/os`](packages/os) is the real, bootable distribution. Downloads and hardware are at [os.elizacloud.ai](https://os.elizacloud.ai).
>
> - **Linux** — boots a full desktop with Eliza built in from a USB stick. amd64 · arm64 · **riscv64**.
> - **Android** — Eliza is the system launcher and assistant, on Pixel-class devices.

注意 **riscv64** —— 这说明它不是 x86 专属。`scripts/build:riscv64-artifacts` / `verify:riscv64` / `check:riscv64-artifacts` 在 root `package.json` 里,是真实构建目标。

## 8. 商业层:Eliza Cloud

Cloud 是 **optional** 的。README 反复强调:

> Eliza Cloud (optional) — Optional managed backend for going beyond one device. **Never required — local-only is first-class.**

Cloud 做的事:
1. **Auth**(OAuth / SIWS,Solana-attested login)
2. **Hosted inference** + 跨 provider 模型路由
3. **Deploy** —— 把 agent/app push 到容器,带自己的 domain
4. **Sync & bridge** —— 跨设备状态同步,从云 dashboard 驱动本地的 agent
5. **Monetization** —— app / agent / MCP 可以 metered + creator 收益

第五点值得注意:这是个 agent 经济系统,不只是 serving 平台。`contracts/` 目录下应该有链上合约实现 creator earnings 分账。

## 9. 给工程师的 takeaway

1. **runtime ≠ framework**——elizaOS 把 runtime 当 OS。思考"长期驻留进程 + 多 capability 装配",不是"调用一次函数"
2. **local-first 是工程承诺**——`ALLOW_NO_DATABASE` / `#8769` / `security/redact` 都指向安全默认 ON 的设计原则
3. **prompt cache 段标记是 2026 必修课**——Anthropic/OpenAI/Gemini 都按"stable 段"计费,你不切段就是在烧钱
4. **serverless runtime 是新坐标**——`serverless?: boolean` 意味着 agent 不一定活在 long-lived 进程里
5. **plugin 四件套是 agent runtime 的通用语**——`actions / providers / services / evaluators` 这套 vocabulary 会被更多 framework 复用