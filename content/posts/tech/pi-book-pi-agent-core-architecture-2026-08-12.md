---
title: "pi-book 深度解读：当一本中文架构书把 commit 钉死、把行号写在每句话里——它对 pi-agent-core 做了什么"
date: 2026-08-12T18:35:00+08:00
draft: false
tags: ["AI Agent", "开源项目深拆", "TypeScript", "Architecture", "技术写作"]
categories: ["技术笔记"]
description: "antinomie-lab/pi-book 是给 @earendil-works/pi-agent-core 写的中文架构书，锁定 commit cd20a8d2e、整体→局部→横切、每条论断附 文件:行号 与代码引文、插叙/岔路/为什么不去 三种反复出现的结构。这篇文章不走复述路线——讲的是这本书本身的写法如何决定它能写出什么，以及它对 runAgentLoop、四条拒绝、两个组合、waitForIdle 结算、prepareNextTurn 链、推 vs 拉事件、终止旗、长度截断的拆解到底走得多深。"
slug: "pi-book-pi-agent-core-architecture"
band: "review"
gates: ["事实性", "去AI味", "观点依据"]
github_repo: "antinomie-lab/pi-book"
---

## 这篇文章在回答什么

`antinomie-lab/pi-book` 不是代码，是给 `@earendil-works/pi-agent-core` 写的中文架构书。已发布三章——00 「从这里开始」、01 「它是什么：一个被做成库的 agent 循环」、02 「一次 prompt 的全程：从 prompt() 到 agent_end」。

把它当作普通"项目解读"来写很可惜。这本书最值得拆的不是它讲了什么，是**它怎么讲**：

- 它把基线钉在一个 commit 上——`cd20a8d2e`，pi 仓库 main 分支，v0.83.0+219。所有代码引用写成 `文件:行号`，路径相对 `packages/agent/`。
- 每一个 `文件:行号` 就地附上对应代码引文。读者不需要打开编辑器，就能核对书里任何一处论断。
- 正文之外有三种反复出现的结构：**插叙**（补一块与 pi 无关的背景知识，跳读不影响主线）、**岔路**（主干里折叠掉的自包含旁支）、**为什么不去**（章末，用设计文档或 git 历史回答"这里为什么不写得更简单"）。
- 组织方式是 **整体 → 局部 → 横切**。第一部分建立对系统的正确认知，不碰实现细节；第二部分按依赖顺序展开；第三部分处理跨部件问题。

这篇文章分两层。

第一层讲 pi-book **对 pi-agent-core 的拆解**——不是复述，是挑出它写得最重的几处：四条拒绝、两个组合在同一循环、waitForIdle 的结算语义、prepareNextTurn 在三层之间的适配、推 vs 拉的事件接收、长度截断下的整批放弃。这些点连起来才看得出一个 agent 循环库"作为库"该长什么样。

第二层讲 pi-book **这本书本身的写法**——锁定 commit + 行号就地引文 + 整体→局部→横切 这套组合，如何决定它能写出什么，以及为什么这种写法在 AI 时代突然变得稀缺而重要。

## 一、先承认一件事：这本书不会过时

技术书最大的敌人是 commit 漂移。`fastapi` 一升级，书里那段"启动流程"的截图就成历史；`react` 一次重构，hook 章节的代码就成了遗迹。pi-book 的解法很直接——[正文开头把基线钉死](https://github.com/antinomie-lab/pi-book/blob/main/agent/README.md)：

> **基线：commit `cd20a8d2e`（main，v0.83.0+219）**
>
> 全书对应 pi 仓库 main 分支上的这个提交。代码引用写成 `文件:行号`，路径相对于 `packages/agent/`。行号会随代码演进漂移，以文件内容为准。

这一句话做了三件事。第一，承认书会过时——行号会漂移，所以"以文件内容为准"。第二，给出一个明确的参考系——读者想知道书里说的 `cd20a8d2e` 在长什么样，`git checkout cd20a8d2e` 就能复现。第三，把所有 `文件:行号` 引用从"作者记忆"降级为"读者可验证锚点"——这才是它真正重要的地方。

紧接着是[第二段](https://github.com/antinomie-lab/pi-book/blob/main/agent/README.md)：

> 代码引用写成 `文件:行号`，并且**每一个 `文件:行号` 引用都就地附上对应的代码引文**——你不需要打开编辑器就能核对任何一处引用。

这一句定义了书的体例。后面所有章节、所有论断，都遵守它。你看到 `src/agent.ts:344` 这样的引用，下面紧跟的就是原文——从十几个字符到上百行的整段函数体，逐字逐句照抄。

这件事对 AI 时代的代码写作有结构性意义。AI 编造代码引用的冲动是真实存在的——一行不存在的函数、一个偏移过的行号、一个杜撰的 API 签名，读者不打开仓库很难发现。pi-book 的体例把这道防线从"作者自觉"提到"格式强制"：不附引文就违反体例；附了引文就要经得起 `git show cd20a8d2e:packages/agent/src/agent.ts` 的逐行比对。

代价是显白的——书变厚、节奏变慢、读者眼睛要从"作者的话"切到"代码"再切回来。但收益是结构性的：每一句话都能被验证，每一处论断都被钉在 commit 上。这是技术书这个品类少有的"诚实可证伪"形态。

## 二、pi-agent-core 是什么：四条拒绝就是答案

第 1 章开头给了一个具体的场景：

> 你在写一个应用，想在里面嵌入一个能"自己干活"的 AI agent：你给它一句话，它调模型，模型说要调工具，它执行工具，把结果喂回模型，如此往复，直到模型说"完了"。中间每一步你都想实时看到——文字是一个字一个字流出来的，工具是一个一个执行的——因为你要把这些渲染到 UI 上。

这个场景就是 `pi-agent-core` 的全部问题域。它的 README 一句话总结——"Stateful agent with tool execution and event streaming"。拆开是三样东西：一个循环、一层状态、一套装备。`pi-agent-core` 给的是这三样。

但 pi-book 不从这里展开。它先讲**这个库不做什么**，然后才讲它做什么。四条拒绝各自有引文：

**拒绝一：不认识任何模型厂商。** 循环对模型的全部依赖是一个函数类型：

```typescript
// src/types.ts:28
export type StreamFn = (
    model: Model<Api>,
    context: Context,
    options?: SimpleStreamOptions,
) => AssistantMessageEventStream | Promise<AssistantMessageEventStream>;
```

`StreamFn` 只见形状，不见厂商。`@earendil-works/pi-ai` 是另一个包，有自己的 provider 目录和模型元数据；本包对它的唯一依赖就是这几个类型。

**拒绝二：不碰 UI。** 包里没有一行渲染代码。全部对外沟通只有一种方式：发事件。`AgentEvent` 是一个十种类型的可辨识联合——`agent_start`、`agent_end`、`turn_start`、`turn_end`、`message_start`、`message_update`、`message_end`、`tool_execution_start`、`tool_execution_update`、`tool_execution_end`。文字流、工具进度、生命周期，全在这十种里。画成终端、网页还是日志文件，是消费者的事。

**拒绝三：核心不做持久化。** `Agent` 类的对话历史就是一个内存数组：

```typescript
// src/agent.ts:71
let tools = initialState?.tools?.slice() ?? [];
let messages = initialState?.messages?.slice() ?? [];
```

进程退出，一切归零。持久化在 harness 层（第 9 章待续），而且是"追加条目到树"的模型——核心循环对此一无所知。

**拒绝四：核心不碰运行时 API。** `src/` 根目录的七个文件里，没有任何 `node:fs`、`node:child_process`。全包（测试除外）`import "node:*"` 的文件只有一个：

```typescript
// src/harness/env/nodejs.ts:1
import { type ChildProcess, spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { constants, createReadStream } from "node:fs";
```

`package.json` 的 `exports` 字段把这条边界切成了三个公开面：

| 入口 | 内容 | 隐含承诺 |
|---|---|---|
| `.` | 核心层 + harness 几乎全部 | 不含任何 `node:*` import，浏览器可跑 |
| `./node` | `NodeExecutionEnv` | 唯一的 Node 绑定，显式 opt-in |
| `./experimental` | `experimental/session/` | 进行中，契约可以变 |

这不是打包便利，是架构声明。"哪部分代码敢碰运行时 API"被提升到了包边界。主入口能给浏览器用这件事，不靠文档自觉，靠的是 `node:fs` 在整个主入口的依赖闭包里物理不存在——全包只有一个文件 import 了 `node:*`，它通过 `./node` 单独导出。

四条拒绝里有三条各自留下了一个可替换的位置，替换方式各不相同——这个区分是第 1 章最值钱的一节，下一节展开。

## 三、三个可替换点对应三种耦合强度

把"拒绝"理解为"不在这里做"，是消极的。pi-book 把每条拒绝翻到另一面，看它留出了什么：

**1. `StreamFn`：注入替换。** 循环对模型层的全部依赖是一个函数形状。换 provider 库、换代理、换 mock，都是传一个不同的函数进来。每次调用都可以换——这是最松的耦合。

**2. Session 后端：接口替换。** 契约是一个接口，五个方法：

```typescript
// src/harness/session/repository.ts:22
export interface SessionRepository<...> extends AsyncDisposable {
    create(options: TCreateOptions): Promise<Session<TMetadata>>;
    open(metadata: TMetadata): Promise<Session<TMetadata>>;
    list(options?: TListOptions): Promise<TMetadata[]>;
    delete(metadata: TMetadata): Promise<void>;
    fork(source: TMetadata, options: SessionForkOptions & TCreateOptions): Promise<Session<TMetadata>>;
}
```

仓库里自带 JSONL 和内存两个实现，`experimental/` 里还有一套 conformance 测试用来验收第三方后端。构造时定——耦合强度居中。

**3. `ExecutionEnv`：能力替换。** 所有文件/shell 操作的能力接口。Node 实现是一种，浏览器里可以换成远程执行环境。整个工具层的行为都建立在它上面——耦合最重，但换来的是测试和移植性。

三种替换方式对应三种耦合强度的递进：函数注入（每次调用可换） → 接口实现（构造时定） → 能力接口（整个工具层）。这是一个抽象的标尺，不是教条——同一个包里三种都用，是因为它们对应的不确定性维度本来就不一样。

## 四、同一循环，两种组合

`pi-agent-core` 容易产生的误解：`Agent` 类和 `AgentHarness` 类是什么关系？继承？包装？都不是。看依赖方向：

```
agent-loop.ts  (runAgentLoop —— 无状态循环，792 行)
    ▲                    ▲
    │                    │
agent.ts           harness/agent-harness.ts
(Agent 类,         (AgentHarness 类,
 588 行)            1185 行)
```

两个类**都直接调用 `runAgentLoop`**，彼此之间没有调用关系。`Agent` 这一侧：

```typescript
// src/agent.ts:409
private async runPromptMessages(
    messages: AgentMessage[],
    options: { skipInitialSteeringPoll?: boolean } = {},
): Promise<void> {
    await this.runWithLifecycle(async (signal) => {
        await runAgentLoop(
            messages,
            this.createContextSnapshot(),
            this.createLoopConfig(options),
            (event) => this.processEvents(event),
            signal,
            this.streamFunction,
        );
    });
}
```

`AgentHarness` 这一侧：

```typescript
// src/harness/agent-harness.ts:658
return await runAgentLoop(
    messages,
    this.createContext(turnState, beforeResult?.systemPrompt),
    this.createLoopConfig(getTurnState, setTurnState),
    (event) => this.handleAgentEvent(event, signal),
    signal,
    this.createStreamFn(getTurnState),
);
```

参数形状几乎一样——上下文、循环配置、事件回调、信号、流函数——但参数的来源完全不同：`Agent` 给的是内存快照，`AgentHarness` 给的是 per-turn 快照。`AgentHarness` 不是 `Agent` 的子类，也不是它的包装——它是同一循环原语之上的另一层组合，只是组合进去的东西多得多：持久化、压缩、hook、大操作之间的互斥门禁。

为什么要并存两层？因为它们的"重"不一样。嵌入一个聊天面板，用 `Agent` 就够；造一个 coding agent，用 `AgentHarness`。循环本体只有一份，复杂功能是组合出来的，不是循环变复杂了。`agent-loop.ts` 停在 792 行，harness 自由长到 10k 行——这个比例本身就是这套设计的证据。

import 关系上的证据更直接：

- `harness/` 里 `grep "from \"../agent.ts\""`，**零命中**。
- `agent.ts` 也不知道 harness 的存在。想删掉整个 harness 目录，核心层一个 import 都不用改——`src/index.ts` 的导出列表除外。

依赖图近乎一棵树，箭头全部指向上游。两片叶子没画进去：`env/nodejs.ts` 和 `experimental/` 只被各自的入口文件（`node.ts` / `experimental.ts`）引用——主入口的依赖闭包里，它们物理不存在。

## 五、跟着 prompt() 走一遍

第 2 章是全书的肉。跟着 `agent.prompt("读一下 config.json")` 把控制流从头到尾走一遍。走完这一章，后面每一章的模块都见过了。

入口在 `Agent.prompt`：

```typescript
// src/agent.ts:344
async prompt(message: AgentMessage | AgentMessage[]): Promise<void>;
async prompt(input: string, images?: ImageContent[]): Promise<void>;
async prompt(input: string | AgentMessage | AgentMessage[], images?: ImageContent[]): Promise<void> {
    if (this.activeRun) {
        throw new Error(
            "Agent is already processing a prompt. Use steer() or followUp() to queue messages, or wait for completion.",
        );
    }
    const messages = this.normalizePromptInput(input, images);
    await this.runPromptMessages(messages);
}
```

第一件事和 AI 无关：检查 `activeRun`。**一个 Agent 实例同一时刻只跑一个 run**——想插队，走 `steer()` 或 `followUp()` 队列。

`runPromptMessages` 把活交给 `runWithLifecycle`，然后是 `runAgentLoop`，最后落在 `runLoop`。`runLoop` 里有**两个** `while`，这就是"两层结构"的字面出处。

**内层 `while`** 转一圈 = 一个 turn：注入插队消息（如果有）→ 调一次模型 → 执行工具（如果有）→ `turn_end`。它的退出条件 `hasMoreToolCalls || pendingMessages.length > 0` 读作"模型没要新工具，也没人插队"。

**外层 `while (true)`** 转一圈 = 一批 follow-up。内层耗尽后本来该结束了，但先问一句 follow-up 队列：有人排队就续命，没人 `break`。外层存在的全部理由就是这一问。

为什么要两层而不是一个大 while？因为两种队列的**检查时机**不同：steering 在每个 turn 之后都要看（用户在 agent 工作时随时插话），follow-up 只能在"agent 真的要停了"的点才看。合并成一个循环，就得在同一个条件里表达两种时机，代码会长出奇怪的旗标；两层 while 各管一种时机，条件读起来就是业务语义本身。

## 六、循环什么时候停：三种停法

内层循环的退出条件有两个，必须同时成立：模型这一轮没要新工具（`hasMoreToolCalls` 为假），并且没有人插队（`pendingMessages` 为空）。这是正常出口。此外还有两条提前停止的路径：

### 6.1 由 toolCall 决定：正常出口与终止旗

循环的正常出口是模型"不再调用工具"，跟举旗无关。`hasMoreToolCalls` 每圈开头先无条件置 `false`，执行完工具后按 `!executedToolBatch.terminate` 置回。`terminate` 什么时候是 `false`？判定函数只有三行：

```typescript
// src/agent-loop.ts:582
function shouldTerminateToolBatch(finalizedCalls: FinalizedToolCallOutcome[]): boolean {
    return finalizedCalls.length > 0 && finalizedCalls.every((finalized) => finalized.result.terminate === true);
}
```

这把"举不举旗"这件事变成了一道三道锁：

1. **没有任何工具举旗**——`terminate` 是工具结果上的可选 hint，绝大多数工具从不设置它。
2. **混合批次**——三个工具里两个举了旗、一个没举，`every` 不成立，整批继续。
3. **截断守卫路径**——`failToolCallsFromTruncatedMessage` 返回的批次硬编码了 `terminate: false`，因为整批的意义就是"让模型重发一遍"。

反过来说，`terminate: true` 只在**这批每个工具结果都显式举旗**时出现。举不举旗的决策是**工具作者**的，不是模型的——旗子写在工具结果上，`execute()` 返回什么就是什么。模型的角色是选择调用哪个工具（工具作者可以用 prompt 引导它在对的时机调用终点工具），宿主则可以用 `afterToolCall` 在 finalize 阶段代举或撤旗。三层各管一段：作者定义语义、模型选择时机、宿主保留否决权。

举旗的真实例子在兄弟包 `packages/coding-agent/examples/extensions/structured-output.ts`——它的文件头注释把动机写得很明白：

> **Structured Output Tool**
>
> Demonstrates `terminate: true` so the agent can end on a tool call without paying for an extra follow-up LLM turn.

场景是这样的：用户要结构化答案（JSON 式的总结、行动项列表），模型把答案**作为工具调用的参数**交出来——`headline`、`summary`、`actionItems` 都在参数里。工具要做的只是收下并存起来：

```typescript
// packages/coding-agent/examples/extensions/structured-output.ts:34
async execute(_toolCallId, params) {
    return {
        content: [{ type: "text", text: `Saved structured output: ${params.headline}` }],
        details: { headline: params.headline, summary: params.summary, actionItems: params.actionItems },
        terminate: true,
    };
}
```

判断一个工具该不该举旗，一句话就够：**这条 toolResult 回到模型手里之后，模型还有没有有意义的事可做？** 有，就是普通工具；没有，就是终点工具。

### 6.2 `shouldStopAfterTurn`：turn 边界上的优雅收尾

`shouldStopAfterTurn` 是宿主表达"优雅收尾"的正式通道。每个 `turn_end` 之后、poll 两条队列之前被调用，返回 `true`，循环发 `agent_end` 退出——连 steering 和 follow-up 队列都不再看。

"不看两条队列"本身就是一种设计决策，只不过它不是用 if/else 写出来的，而是用**位置**写出来的。可以设想另一种写法：退出前先看看队列——"有插队消息的话，还停不停？"——这样停止逻辑就和队列逻辑纠缠在一起，长出"要停但有消息""不停但队列为空"之类的组合分支。pi 的解法是让问题模型保持最简单：**每个回调只回答一个问题，没被问到的问题留给下一个 run。**

为什么 `shouldStopAfterTurn` 不是加强版 abort？abort 立刻切断 provider 流、`stopReason` 变 `aborted`；这个回调等当前 turn 完整结束、`turn_end` 发出之后，在 poll 队列和下一次 LLM 调用之前退出——不动流、不取消运行中的工具、不改 `stopReason`。动机写在 JSDoc 里：context 快满时体面收束，或服务关停时的交接。

### 6.3 abort：无条件出口

`agent.abort()` 的粒度：**结束的是整个 run，不是当前 turn**。它不看 `hasMoreToolCalls`，不等 `shouldStopAfterTurn`，两条队列也不再 poll；signal 让正在进行（或下一次）的模型请求以 `stopReason: "aborted"` 收尾，直接命中骨架里那个 `return` 的分支。

三种时刻各自怎么停取决于听到广播的三方多快响应：

- **正在流式输出**：signal 在发请求时已交进 `streamFn`，HTTP 层立刻断流。
- **正在执行工具**：循环不硬杀工具——signal 在 `execute()` 的参数里，怎么响应是工具自己的事（内置 bash 会杀子进程）。循环这一侧的承诺是"不再开新工作"。
- **正在 turn 与 turn 之间**：下一圈调 `streamFn` 时带上的还是那根已按下的 signal，立刻落入第一种情况。

三个时刻有一个共同点：**abort 结束的是整个 run，不是当前 turn。** 骨架里那个分支是 `return` 不是 `continue`——ESC 的语义是"这个 run 到此为止"，两条队列也不再 poll。

## 七、waitForIdle：旁观者的等待

`runWithLifecycle` 里那个"手动引爆的 Promise"——`new Promise` 的 executor 是同步执行，所以构造完成的瞬间，`resolvePromise` 就拿到了 resolve 函数。这个 Promise 的用途要拆成三个问题看。

它什么时候 resolve？`runWithLifecycle` 的结构：`executor` 跑完 → `finally` 里的 `finishRun()` → `resolvePromise()` 被调用。这个 Promise 的 resolve 时刻就是"run 彻底结束"的时刻——它比 `agent_end` 事件发出的时刻要晚，晚出的那一拍就是订阅器清理。

谁在 await 它？`Agent.waitForIdle()`：

```typescript
// src/agent.ts:328
waitForIdle(): Promise<void> {
    return this.activeRun?.promise ?? Promise.resolve();
}
```

没有 active run 时返回一个立即 resolve 的 Promise——"已经在 idle，不用等"。

为什么需要它？`prompt()` 完全可以不 await——发出去就撒手，UI 靠订阅事件更新；而另一个角落的代码（退出前的清理、测试里的断言、`reset()` 之前的护栏）需要一个"等它彻底安静"的手段，它手里没有 `prompt()` 返回的那个 Promise，只有 `agent` 引用。`waitForIdle()` 就是为这种"旁观者等待"准备的公开告示牌。

**保证的反面：在监听器里 await 它，会死锁。** 同一条结算语义，站错位置就是陷阱。把依赖关系摊开：监听器里 `await agent.waitForIdle()`，等的是结算；而结算在等你——`processEvents` 逐个 `await` 监听器，你不 return，`executor` 就不算跑完，`activeRun.promise` 就不 resolve；你又在等它 resolve——环闭合了。不需要线程参与，Promise 依赖成环就够了，而且没有任何超时或 abort 能打破它。

`docs/agent-harness.md` 把这个坑明确写了出来：

> listeners/hooks currently receive no facade; if they close over the raw harness and call settlement APIs such as `waitForIdle()` during the active run, they can deadlock. A future facade should expose `runWhenIdle()` instead.

`runWhenIdle()` 的出路在于换一个方向：把回调传进去，自己的监听器正常 return，结算照常完成；链走完后 harness 再来调这个回调，从登记那一刻起，你就不在依赖环里。它目前只是计划。

一句话记住这条边界：**`waitForIdle()` 是旁观者的工具，参与者碰不得。**

## 八、事件如何被接收：推 vs 拉

`emit` 只是一个函数参数，所以"事件如何被接收"没有唯一答案。这个包里有两个调用方，对应两种接收方式。

**推（`Agent` 类）**：事件先归约进 `state`，再逐个 await 订阅者：

```typescript
// src/agent.ts:584（Agent.processEvents 内，删减）
for (const listener of this.listeners) {
    await listener(event, signal);   // 你不 return，循环就不发下一个事件
}
```

**拉（裸 `agentLoop()`）**：不传监听器，而是把事件推进一个 `EventStream`，让调用方自己用 `for await` 拉：

```typescript
// src/agent-loop.ts:31
export function agentLoop(/* ... */): EventStream<AgentEvent, AgentMessage[]> {
    const stream = createAgentStream();
    void runAgentLoop(/* ... */, async (event) => {
        stream.push(event);
    }, /* ... */).then((messages) => {
        stream.end(messages);
    });
    return stream;
}
```

两种接收方式的差别，用一个问题就能问出来：**你的事件处理很慢的时候，循环会不会停下来等你？** 拉模式：不等，事件在队列里堆着，循环继续跑；推模式：等，你的处理时间是循环时间线上的一段。

各赔上一样东西，各换来一样东西。拉模式赔了**顺序与结算保证**，换来**解耦**；推模式赔了**速度**，换来的是**保证**——具体三条：

1. 你看到的事件流就是循环的时间线。第 N 个事件的所有监听器结束前，第 N+1 个不会发出。
2. `state` 和事件永远一致。监听器里读 `agent.state`，拿到的一定是这个事件**之后**的状态，不需要自己做同步。
3. 你的异步工作计入 run 的结算。在监听器里 await 的写库、网络请求，全被算进"run 结束"的定义——`waitForIdle()` 要等最后一个 `agent_end` 监听器跑完才 resolve。

选哪个取决于你要不要那个保证：做 UI 通常要——渲染需要一致的 `state`、写库需要结算屏障，选推（`Agent`）；做管道通常不要——把事件流转发到日志、分析、另一个系统，你只是过客，选拉（裸 `agentLoop()`）。

## 九、两圈之间换快照：`prepareNextTurn`

主干里折叠掉的那块，在每个 `turn_end` 之后、下一次 poll steering 之前，给宿主一个"换掉下一圈的装备"的机会。

看 agent 循环层的契约：

```typescript
// src/agent-loop.ts:226
const nextTurnContext = {
    message,
    toolResults,
    context: currentContext,
    newMessages,
};
const nextTurnSnapshot = await config.prepareNextTurn?.(nextTurnContext);
if (nextTurnSnapshot) {
    currentContext = nextTurnSnapshot.context ?? currentContext;
    config = {
        ...config,
        model: nextTurnSnapshot.model ?? config.model,
        reasoning:
            nextTurnSnapshot.thinkingLevel === undefined
                ? config.reasoning
                : nextTurnSnapshot.thinkingLevel === "off"
                    ? undefined
                    : nextTurnSnapshot.thinkingLevel,
    };
}
```

两个语义细节值得记住。一是合并方式：快照的每个字段都可缺省，缺省就 `??` 回落到当前值——宿主可以只换模型不动上下文，反之亦然。二是 `thinkingLevel: "off"` 被显式翻译成 `reasoning: undefined`，因为下游（`SimpleStreamOptions`）的契约是用"没有 reasoning 字段"而不是 `"off"` 来表达关闭——这个三层三元表达式就是在做词汇表对齐。

时机也有讲究：替换发生在 `turn_end` 之后、steering poll 之前。这意味着哪怕下一圈是为了回应一条插队消息，用的也已经是新快照——插队不会让宿主失去换装备的机会。

### 9.1 接缝：两个名字，一个适配器

`prepareNextTurn` 这个名字在 `Agent` 层出现在三个位置、`prepareNextTurnWithContext` 出现在两个，指的都不是同一个东西。先把三个位置分开：

- **入口**：`AgentOptions` 的两个同名键——宿主构造 `Agent` 时把函数传进来的地方；
- **槽位**：`Agent` 实例上的两个公开属性（`src/agent.ts:197`）——`Agent` 只定义签名、自己不提供实现；
- **出口**：`AgentLoopConfig` 的单一键 `prepareNextTurn`——装配时由槽位归一而来。

两个槽位的差别只有第一个参数：旧版只给 signal，新版多给刚结束的 turn 信息；返回值完全相同。装配时 `Agent` 读这两个槽位，归一成出口处的单一名字：

```typescript
// src/agent.ts:459（Agent.createLoopConfig 内）
prepareNextTurn:
    this.prepareNextTurnWithContext || this.prepareNextTurn
        ? async (context) => {
                if (this.prepareNextTurnWithContext) {
                    return await this.prepareNextTurnWithContext(context, this.signal);
                }
                return await this.prepareNextTurn?.(this.signal);
            }
        : undefined,
```

两个名字并存的原因是兼容性：旧版公开属性的签名不能直接改（CHANGELOG 0.80.3 记了这段历史），需要 turn 信息的人用新版。包装在中间做翻译——对循环始终暴露 `(context)` 形态，对内看槽位里装的是哪个，新版把 `context` 递过去，旧版扔掉 `context` 只递 `signal`。

### 9.2 实现：叠加与重建

coding-agent 叠加一层，每圈重读 systemPrompt、工具列表、模型和思考强度——

```typescript
// packages/coding-agent/src/core/agent-session.ts:526
private _installAgentNextTurnRefresh(): void {
    const previousPrepareNextTurnWithContext =
        this.agent.prepareNextTurnWithContext ??
        (this.agent.prepareNextTurn
            ? async (_turn: PrepareNextTurnContext, signal?: AbortSignal) =>
                await this.agent.prepareNextTurn?.(signal)
            : undefined);
    this.agent.prepareNextTurnWithContext = async (turn, signal) => {
        const previousSnapshot = await previousPrepareNextTurnWithContext?.(turn, signal);
        const previousContext = previousSnapshot?.context ?? turn.context;
        return {
            ...previousSnapshot,
            context: {
                ...previousContext,
                systemPrompt: this._systemPromptOverride ?? this._baseSystemPrompt,
                tools: this.agent.state.tools.slice(),
            },
            model: this.agent.state.model,
            thinkingLevel: this.agent.state.thinkingLevel,
        };
    };
}
```

赋值会整体替换槽里已有的函数，所以 coding-agent 的安装不是简单替换、而是**叠加一层**：先把旧值捕获进 `previousPrepareNextTurnWithContext`，新函数先调它、把它的快照垫在底下，再覆盖刷新四个字段——值全部从 `state` 现读，所以 run 中途的切换，下一圈生效。

harness 的实现是另一个风格：每圈先把 run 期间积压的延迟写入落盘，再从 session 重建整份快照：

```typescript
// src/harness/agent-harness.ts:527（AgentHarness.createLoopConfig 内，删减）
prepareNextTurn: async () => {
    await this.flushPendingSessionWrites();
    const nextTurnState = await this.createTurnState();
    setTurnState(nextTurnState);
    return {
        context: this.createContext(nextTurnState),
        model: nextTurnState.model,
        thinkingLevel: nextTurnState.thinkingLevel,
    };
},
```

两条路径——叠加与重建——对应两种"圈间装备"的来源。coding-agent 装备从 `agent.state` 实时读出，harness 装备从 session 落盘再重建。一个偏向"运行期可见状态"，一个偏向"持久化状态"。

### 9.3 还能这么用：run 内压缩

压缩是宿主层的事，coding-agent 的选择是**在 run 间做**——就是前面 `shouldStopAfterTurn` 那条路：停在这一圈，宿主压缩，开新 run。但"不中断 run、在圈内把上下文换掉"正是 `prepareNextTurnWithContext` 独占的能力：

```typescript
// 示意：run 内压缩（应用侧代码，不在 pi 仓库里）
agent.prepareNextTurnWithContext = async ({ context }) => {
    if (roughTokens(context.messages) <= 150_000) {
        return undefined;
    }
    const summary = await summarize(context.messages);
    return {
        context: {
            ...context,
            messages: [summaryMessage(summary), ...keepRecentTurns(context.messages)],
        },
    };
};
```

钩子的职责只有一件事：把新快照递回去。`undefined` 表示沿用当前上下文，返回对象则替换。命名撞车（两个 `prepareNextTurn`，两个 `prepareNextTurnWithContext`）作为兼容期的代价留着——CHANGELOG 0.80.3 之后旧签名不再扩展，新签名成为推荐入口。

## 十、长度截断：整批放弃的"抢救"陷阱

进入工具执行前有一个容易漏掉的守卫：

```typescript
// src/agent-loop.ts:208
const executedToolBatch =
    message.stopReason === "length"
        ? await failToolCallsFromTruncatedMessage(toolCalls, emit)
        : await executeToolCalls(currentContext, message, config, signal, emit);
```

输出被 token 上限截断时，每个工具调用的参数都可能是残缺的 JSON。**全部标记为错误，一个都不执行**，让模型自己重新发一遍。错误消息的措辞直接把原因告诉模型：

```typescript
// src/agent-loop.ts:395
result: createErrorToolResult(
    `Tool call "${toolCall.name}" was not executed: the response hit the output token limit, so its arguments may be truncated. Re-issue the tool call with complete arguments.`,
),
```

为什么不"抢救"一下？注释里把这个决策写死：

```typescript
// src/agent-loop.ts:374
/**
 * Fail all tool calls from an assistant message that was truncated by the
 * output token limit. Streamed tool-call arguments are finalized with a
 * best-effort JSON salvage parser, so a truncated message can yield tool calls
 * whose arguments parse and validate but are silently incomplete. None of them
 * are safe to execute; report each as an error so the model can re-issue them.
 */
```

流式累积的半截参数会被一个"尽力抢救"的 JSON 解析器补全——补全后能解析、能过 schema 校验，但可能**悄悄不完整**：少的是哪个字段，无从分辨。所以整批一个都不执行，让模型自己重发。PR #6285 评审中还否掉过一个更细粒度的方案——给 `ToolCall` 加 `malformedArguments` 字段、把判断推给调用方——理由是这条边界值得"硬"，推给调用方会变成无限个不同的判断口径。

这条决策是 pi-agent-core 的一个"宁可错杀"原型。"抢救"听起来友好，但悄悄不完整的工具调用比明显的错误更危险——它跑成功了，但写错了文件或删错了数据。拒绝抢救是对模型/用户的一个明确承诺：循环不会在边界模糊的情况下继续往前跑。

## 十一、调模型：两道闸门

内层循环的核心动作是 `streamAssistantResponse`。在真正发出请求之前，消息要过两道闸门：

```typescript
// src/agent-loop.ts:289
let messages = context.messages;
if (config.transformContext) {
    messages = await config.transformContext(messages, signal);   // AgentMessage[] → AgentMessage[]
}

const llmMessages = await config.convertToLlm(messages);
```

- `transformContext`（可选）：直接操作 agent 侧的消息数组——剪掉老消息、注入外部上下文。输入输出都是 `AgentMessage[]`。
- `convertToLlm`（必需）：把 `AgentMessage` 翻译成 LLM 侧的 `Message`。LLM 只认识 `user`/`assistant`/`toolResult` 三种角色，你的自定义消息类型要么被转换，要么被过滤掉。

这两道闸门是全书最重要的设计之一——循环本体从头到尾只说 `AgentMessage`，翻译只发生在 LLM 调用边界上。这句话就写在 `agent-loop.ts:1` 的文件头注释里：

```typescript
// src/agent-loop.ts:1
/**
 * Agent loop that works with AgentMessage throughout.
 * Transforms to Message[] only at the LLM call boundary.
 */
```

为什么这条边界这么重要？它把"循环的稳定性"和"厂商 API 的演变速度"解耦了——后者变，前者不需要变；前者写完一次，长期可用。

## 十二、消息的三件套与内容块

消息数据模型只有三种角色：

```typescript
// packages/ai/src/types.ts:442
export type Message = UserMessage | AssistantMessage | ToolResultMessage;
```

三种角色对应对话协议的三个动作：**user 说**，**assistant 做**，**toolResult 把工具结果喂回去**。循环的"模型 → 工具 → 模型"往复，落到数据上就是 assistant 消息和 toolResult 消息在数组里交替追加。

注意 `AssistantMessage.content` 的类型：**不是字符串，是内容块数组**。一条 assistant 消息是若干块的序列，每块三选一：`TextContent`（正文）、`ThinkingContent`（思考过程）、`ToolCall`（工具调用）。块按模型产出的顺序排列，所以一条消息可以"想一段、说一段、调两个工具"，全部混排在同一个数组里。

`message` 听起来像"一句话"，实际上它是**模型一轮输出的全部内容**的容器——"轮"才是它的单位，不是"句"。有了这个形状，骨架里那个 `filter((c) => c.type === "toolCall")` 就好懂了：**"模型这一步有没有要干活" = "这个数组里有没有 `type: "toolCall"` 的块"**。文本块和思考块不进工具管线，它们只是对话内容，留在数组里随消息一起进上下文。

## 十三、这本书本身——它的体例如何决定它能写出什么

到这里，对 pi-agent-core 的拆解可以告一段落。把视角拉远一层：pi-book **这本书本身的写法**才是它作为中文架构书稀缺的地方。

锁定 commit + 行号就地引文 + 整体→局部→横切——这套组合不是技术写作的金科玉律，但它解决了一个具体的写作问题：**当 AI 时代任何人都能五分钟写出一篇项目解读时，"认真读过代码"的稀缺性成了护城河**。

随便抽一条证据。[第 1 章在引完 `src/types.ts:28` 的 `StreamFn` 类型后](https://github.com/antinomie-lab/pi-book/blob/main/agent/01-what-it-is.md)，紧跟着的解释是"它只约定形状：给我 `Model` 和 `Context`，还我一个事件流。谁来提供这个函数？隔壁的 `@earendil-works/pi-ai`——那是另一个包"——这不是复述，是把"它只约定形状"这个判断从类型签名里抽出来，再用"隔壁的包"把它落地。这种"读到代码→抽出判断→告诉读者"的密度，是模板化写作做不出来的。

第 2 章更明显。它做了一件反直觉的事：**把循环拆成外层和内层两个 `while`**，然后用一个具体问题（"为什么需要两层，而不是一个大 while？"）把它们的语义差钉死。普通项目解读不会这样问——它会先讲架构图，再讲 API，再讲使用示例。pi-book 把代码读出来的"层"作为章节的轴，follow-up 队列的时机差成了内/外 while 的存在理由。这就是"按依赖顺序展开"的实际含义：不是先讲 API 再讲实现，是按代码的依赖方向走。

三种反复出现的结构——插叙、岔路、为什么不去——承担了不同的写作职责：

- **插叙**补背景知识。LLM 消息结构、`AbortController`/`AbortSignal`、消息的三件套——都是"读代码需要的常识，但不一定在读者脑子里"。跳读不影响主线，留下来不打扰主体节奏。
- **岔路**展开主干里折叠的细节。`prepareNextTurn` 那一节把"接缝：两个名字，一个适配器"和"实现：叠加与重建"抽出来——主干已经能讲清楚问题，但真要做宿主必须知道两个名字并存的兼容性历史。岔路容得下超出本章平均难度的内容，因为读者可以选择跳读。
- **为什么不去**用 git 历史或设计文档回答"为什么不写得更简单一点"。CHANGELOG 0.32.0 的 commit `d0a4c3702` 解释了 steer/follow-up 为何拆成两条（issue #403 "Queued Messages vs Steering: Mental Model Conflict"）；PR #6285 解释了为什么不抢救截断的工具调用；commit `9022a5b5e` 解释了 emit 为什么逐个 await 监听器。每一处都是"看起来应该那样写，但仓库选择了别的"——把决策的成本和收益钉在具体 PR/commit 上。

这种体例有一个隐含的承诺：**书里的每一句话都能被验证**。`git show cd20a8d2e:packages/agent/src/agent.ts` + 跳到 `line 344`，逐字核对，作者没引用错。这是技术书这个品类少有的"诚实可证伪"形态——大多数技术书做不到这一条，因为它们不附引文，或者引用是装饰性的。

代价也是显白的：书变厚、节奏变慢、读者眼睛要在"作者的话"和"代码"之间来回切。第 2 章 1423 行，是第 1 章（317 行）的 4.5 倍。但拆开来，每一节都对应一段代码和一个判断——没有水的内容能撑出这个长度。

## 十四、落地路径：怎么读这本书 + 怎么用它

读完上面那些，最常见的反应是"我也想写一本"。下面是按代价从小到大排的几条路径。

**1. 只读，不写。** 三章按顺序读就行。00 → 01 → 02，每章 30-60 分钟。读完后你应该能凭记忆画出 pi-agent-core 的模块图。

**2. 跟着书改 pi。** 把 pi 仓库 checkout 到 `cd20a8d2e`，对照书的章节读真实代码。把每个 `文件:行号` 当作锚点跳过去，看 5 行上下文。这条路径花时间最多，但收效最稳。

**3. 写自己的 pi-xxx-book。** pi-book 的体例——锁定 commit + 行号就地引文 + 整体→局部→横切——可以套到任何"代码即文档"的开源项目。门槛不在写作技巧，在"真的读完代码"。仓促写出的版本会立刻在第一处 `文件:行号` 上露馅。

**4. 用 `pi-agent-core` 做应用。** `pi-agent-core` 的 npm 包名是 `@earendil-works/pi-agent-core`，README 一句话告诉你它承诺什么（"Stateful agent with tool execution and event streaming"）。`Agent` 类用于嵌入聊天面板，`AgentHarness` 用于造 coding agent。这层使用不属于 pi-book 的范围——书只讲库本身，不讲它怎么用。

## 十五、一章小结

pi-book 拆的不是 pi-agent-core 的"功能"，是 pi-agent-core 的"结构"——四条拒绝、两个组合、三种替换方式、两层循环、四种停法、推 vs 拉、run 内 vs run 间、长度截断的整批放弃、消息的三件套。两件事连起来：

1. 这个库的设计哲学是"作为库的 agent 循环"——拒绝成为框架，模块即积木，组合即架构。`runAgentLoop` 只有一份，复杂功能是组合出来的，不是循环变复杂了。
2. 写它的书用了同样克制的体例——锁定 commit + 行号就地引文 + 整体→局部→横切 + 插叙/岔路/为什么不去。书没有塞进作者的全部理解，只塞进了从代码里能读出来的东西。

后面还有第二部分（局部）和第三部分（横切）待写。这篇文章停在第一部分已有的三章上——三章已经够画出系统的形状，剩下的章节会逐个填进模块。pi-book 自己也躺在仓库里：[`agent/00-start-here.md:42`](https://github.com/antinomie-lab/pi-book/blob/main/agent/00-start-here.md#L42)，写岔了欢迎去挑错。

## 为什么不去

> **为什么不把 `message.content` 简化成字符串？** 类型签名上的"内容块数组"看起来啰嗦——但它一次性解决了三件事：把文本/思考/工具调用混排在同一轮（`TextContent`/`ThinkingContent`/`ToolCall`）、让 assistant 消息可以"想一段、说一段、调两个工具"、给流式渲染提供 `contentIndex` 锚点（`AssistantMessageEvent` 里几乎每种增量事件都带 `contentIndex: number`）。字符串也可以工作，但每加一种内容类型就得改一次解析路径。
>
> **为什么不把 `terminate` 做成模型能控制的字段？** 因为它是工具作者用来声明"我的结果就是最终答案"的语义，模型的角色是"选择调用哪个工具"，宿主则可以用 `afterToolCall` 在 finalize 阶段代举或撤旗。**作者定义语义、模型选择时机、宿主保留否决权**——三层各管一段，让单一字段在三轮交互里都被充分审视。
>
> **为什么 `waitForIdle()` 的死锁不引入超时或 abort 打破？** 因为打破它的成本是把结算语义退化成"大致结束"，而结算语义是推模式提供的三条保证（"你看到的事件流就是循环的时间线"/"`state` 和事件永远一致"/"你的异步工作计入 run 的结算"）的根基。死锁不是 bug，是错误的代价——监听器里 await `waitForIdle()` 的人本来就在做不该做的事，把这件事留给 facade (`runWhenIdle`) 而不是循环本身。
}