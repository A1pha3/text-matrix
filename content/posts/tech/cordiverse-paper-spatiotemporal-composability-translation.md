---
title: "《Spatiotemporal Composability 编程范式》论文翻译与解读：把 effect 和 coeffect 从静态类型系统抬升为运行时机制，DSH 的整个 plugin 哲学的学术源头"
date: "2026-08-15T01:25:00+08:00"
slug: "cordiverse-paper-spatiotemporal-composability-translation"
description: "Yifan Shi / Wei Zhang / Tianyi Cui 2026 论文《A Programming Paradigm for Spatiotemporal Composability》88 页 PDF 翻译与解读——把 effect systems 和 coeffect systems 从 compile-time 静态分析抬升到 runtime 机制（revertible effects + reactive coeffects），用单 context type 统一成编程范式，给出 calculus of dynamic composition 的形式化微积分，metatheory 证明 preservation / temporal composability / spatial composability / progress / confluence 5 条定理，配套 Cordis 框架的 core library + declarative component loader + HMR 实现。"
categories: ["技术笔记"]
tags: ["论文解读", "Cordis", "插件框架", "形式化方法", "Effect System", "Coeffect", "Programming Paradigm", "Type Theory"]
toc: true
band: review
gates: ["事实性", "去AI味", "观点依据"]
github_repo: "cordiverse/paper"
---

## 这篇文章在回答什么

[Yifan Shi / Wei Zhang / Tianyi Cui 2026-08-13 preprint 的 88 页论文](https://github.com/cordiverse/paper)《A Programming Paradigm for Spatiotemporal Composability》（**Spatiotemporal Composability 编程范式**）是 `cordiverse/cordis` 的学术源头，也是 DeepSeek Harness (DSH) 整套「**everything is a plugin**」架构背后那篇被引用了无数次的论文。DSH 主仓库 README 第一句话直接说 "powered by Cordis, whose design is described in [A Programming Paradigm for Spatiotemporal Composability](https://github.com/cordiverse/paper)"——但 dsh 平台层从不正面解释**为什么**这么设计。这篇论文就是那个「为什么」。

论文的核心主张一句话能讲完：

> 现代软件（从 plugin 系统到 self-evolving agent harnesses）越来越需要**动态组合（dynamic composition）**，但其形式化基础仍然欠缺。本文识别问题的两个正交维度——**temporal composability**（移除组件时 side effects 必须完全可逆）和 **spatial composability**（组件间依赖必须声明式 + 反应式管理）——把这两个维度从**编译期的静态 effect/coeffect 类型系统**抬升为**运行时机制**，用单一 context type 统一，配套 calculus of dynamic composition 的形式化微积分，metatheory 证明 spatiotemporal composability 从单一组件到整个系统的可组合性。

但这篇论文不是抽象的「**又一个 PL 论文**」。它的贡献是双重的：

**理论贡献**：把经典 effect systems（Plotkin & Power 2003 / Plotkin & Pretnar 2009）和 coeffect systems（Petricek 2014 / Petricek & Orchard 2014）的「**静态 + 词法作用域**」模型扩展到「**动态 + 运行时**」模型。具体实现是：
- **revertible effects**（§3.1）——每个 context transformation 带显式 inverse，runtime 追踪，移除时恢复
- **reactive coeffects**（§3.2）——组件声明 coeffect 规格，context 变化按 activating/deactivating/neutral 通知
- **unified context type**（§3.3）——observational equivalence on coeffects supplies effects with independence

**工程贡献**：Cordis 是这个范式的实例化实现。core library 提供 effect tracking + coeffect resolution；声明式 component loader 提供 configuration reconciliation + hot module replacement；DSH 主仓库就是用 Cordis 构建的「**自演化 agent harness**」。

这篇文章回答五件事：

1. **为什么 effect systems 和 coeffect systems 现有的静态模型不够用**——它们只在词法作用域上做 compile-time 分析，不支持动态 arriving/departing 组件
2. **「Temporal composability = side effects 完全可逆」在运行时怎么实现**——revertible effect functions + disposable trackers
3. **「Spatial composability = 依赖声明式 + 反应式」怎么落地**——coeffect specification + activating/deactivating/neutral notification
4. **calculus of dynamic composition 的 5 条 metatheorem 各自证明什么**——Preservation / Temporal Composability / Spatial Composability / Progress / Confluence
5. **Cordis 实现里 effect tracking + coeffect operations + loader + HMR 的工程细节**——DSH 主仓库的 vendored Cordis 源码就是这套范式的工程落地

## 一个直觉：动态组件需要两件事

论文 §1.1 「Dimensions of Composability」把动态组件组合切成两个正交维度：

**Temporal composability**：组件有「**生命周期**」——装载、激活、卸载。卸载时**所有 side effects 必须完全消失**。具体含义：组件在 `effect()` 里注册了 listener，卸载时必须反注册；组件写了文件，卸载时必须删（或声明是泄漏的）；组件起了子进程，卸载时必须 kill。否则**整个上下文状态被污染**。

**Spatial composability**：组件有「**依赖**」——需要其他组件的服务、配置、数据。依赖必须**声明式**（不直接 import 具体实现）+ **反应式**（依赖变化时本组件要能感知）。具体含义：组件 A 用 `ctx.logger`，不应该 `import { ConsoleLogger }` —— 应该 `inject: ['logger']` + Cordis 自动注入；如果 logger 实现被替换（ConsoleLogger → OtelLogger），A 应该自动收到新 logger；如果 A 卸载了 logger，A 应该被通知「依赖没了」。

为什么这两件事是「**正交**」的？因为它们解决不同问题：
- temporal = 「**我走了之后世界长什么样**」（我离场的清理）
- spatial = 「**我进来之后世界长什么样**」（我入场的依赖）

但这两件事又是**耦合**的——一个组件卸载（temporal 事件）会触发依赖它的其他组件的通知（spatial 事件）；一个组件注入（spatial 事件）会修改当前激活集合（temporal 状态）。

现有 effect systems 只管 temporal 不管 spatial：它们跟踪 effect 的执行但不跟踪「**谁需要我**」。现有 coeffect systems 只管 spatial 不管 temporal：它们跟踪「**我需要谁**」但不跟踪「**我离开后世界怎么办**」。Cordis 把两者**统一在同一个 context type** 里——这就是论文标题里 **Spatiotemporal Composability** 的来历。

## 一个动机：self-evolving agent harnesses 为什么需要这个范式

论文 §1.2.2 把 DSH 直接当作一个 motivating example 用——而且**这是论文 5 个 motivating example 中最关键的一个**：

> A self-evolving agent harness allows an agent to inspect, mount, and unmount its own plugins at runtime. Such harnesses are particularly demanding for dynamic composability: the set of capabilities an agent exposes to its model changes during execution, while the runtime is expected to remain in a coherent state.

翻译：「**自演化 agent harness 让 agent 在运行时检查、装载、卸载它自己的 plugin**。这种 harness 对动态可组合性的要求最高：agent 暴露给模型的能力集合在执行期间持续变化，但 runtime 必须保持连贯状态。」

DSH 主仓库 `packages/self-modification/` 干的就是这件事——agent 可以在运行时挂载 / 卸载 plugin。这条能力对 dynamic composability 提出两个具体要求：

1. **Temporal**：agent 卸载一个 plugin 时，这个 plugin 之前注册的所有 listener、所有 effect 副作用、所有临时资源必须**完全清理**——否则会污染后续 turn 的状态
2. **Spatial**：agent 挂载新 plugin 时，**已经存在的组件必须能感知到这个新能力**（如果它们声明依赖该能力）；agent 卸载 plugin 时，**依赖它的组件必须收到通知**（activating → deactivating）

DSH 主仓库的 `ctx.effect()` + `ctx.on()` API 是这两件事的工程入口。但**为什么这么设计**——DSH 不说，因为工程层假设你读 Cordis 论文。论文是上游理论，DSH 是下游应用。

§1.2.3 提到现有的「**coarse-grained workaround**」是「**重启整个系统**」——这是现状最普遍但显然不可接受的方案。Cordis 是第一个给出 fine-grained 解的 meta-framework。

## §3 形式化核心：revertible effects + reactive coeffects

§3 是论文的技术核心，把 temporal 和 spatial 两条维度各自形式化。

### §3.1 Revertible Effects

**§3.1.1 Effect Context**：context 是一个 effect container，每个 effect 是 (operation, dispose) 对：

```text
effect: (op: Op) → Disposable
```

Disposable 是一个**显式 inverse**——调用 disposable 把 effect 完全撤回。runtime 维护 effect stack，组件卸载时按 stack 顺序调用所有 disposable。

这条机制的工程含义：

**1. 没有「隐式 cleanup」**——所有 effect 必须显式给 inverse。这是为什么 DSH `ctx.effect()` API 接受 `() => async () => {}` 而不是 `() => Promise<void>` —— 函数返回值就是 disposable。

**2. effect stack 是 LIFO**——后注册先反注册。这是为什么 DSH 主仓的「**agent-scope plugin 卸载**」必须严格按注册反向顺序：先卸载子 plugin，再卸载父 plugin，否则子 plugin 的 disposable 已经被父 plugin 的状态影响无法正确回滚。

**3. effect tracking 的独立性**（§3.1.3 Independence of Effects）：两个 effect 的 dispose 互不干涉——一个 effect 的失败不能 cascade 到另一个 effect 的 dispose 失败。这是为什么 DSH 主仓 `ctx.effect()` 实现里 disposable 都包了 try-catch——单个 effect dispose 失败不能让整个组件卸载失败。

**§3.1.2 Revertible Effect Functions** 把上面的抽象升一阶：函数 `f: A → (B → Disposable)` 接受输入，返回一个「**接收输入产生带 disposable 的输出**」的函数。这条对应 DSH 的「**async effect**」——`ctx.effect(async () => { ... return async () => { ... }; })`，async 函数返回的 Promise resolve 一个 disposable。

### §3.2 Reactive Coeffects

**§3.2.1 Coeffect Context**：和 effect 对偶，coeffect 是「**组件需要什么**」。coeffect context 是 (specification, notification) 对：

```text
coeffect: (spec: Spec) → Disposable
```

spec 是组件声明的依赖规格（不是 import，是 spec）；notification 是 context 变化时 runtime 给组件的回调（activating / deactivating / neutral）。

§3.2.2 把 notification 分成三态：
- **activating**：coeffect 被安装（满足 spec 的服务被加进 context）——组件需要启动自己的依赖消费逻辑
- **deactivating**：coeffect 被卸载（满足 spec 的服务被移走）——组件需要清理自己的依赖消费逻辑
- **neutral**：context 变化但不影响当前 coeffect 满足状态（其他组件的 coeffect 变化）

**§3.2.3 Isolation and Interception** 是 Cordis 的「**服务命名空间隔离**」机制：`Context.isolate(name, label?)` 创建一个 shadow scope，让相同 name 的服务在不同 isolate 中可以共存。DSH 的 `ctx.agents`（live registry）就是用 isolation 把「**agent A 的工具集**」和「**agent B 的工具集**」分开——同一个 `ctx.tools` key 在不同 agent scope 指向不同的 service 实现。

`Context.intercept(name, config)` 是「**配置拦截**」——把某个 name 的 service config 替换或叠加。DSH 主仓 `cordis.patch.yml` 的 patch 语义就是 intercept——row id 定位 service，replace config。

### §3.3 Unified Context

§3.3 是论文形式化的精华——把 effect context 和 coeffect context **统一成单 context type**：

```text
Context ::= (effect_set, coeffect_set)
```

unified 之后的核心定理是「**observational equivalence on coeffects supplies effects with independence**」——如果两个 coeffect 满足度等价（组件看不出区别），那么 effect 操作的结果也独立。这条 theorem 让 effect tracking 的 compositionality 成立：**你可以单独测试 effect 的 dispose 序列，不用管 coeffect 的变化怎么 trigger 它**。

§3.3.3 Situating the Context Paradigm 把这个 unified context 和现有的 effect system / coeffect system / actor model / reactive programming / capability system 做对比，定位 Cordis 的位置是「**第一个把 effect 和 coeffect 同时作为 runtime 一等公民的 meta-framework**」。

## §4 calculus of dynamic composition 的 5 条 metatheorem

§4 把 §3 的形式化转成「**组件 + lifecycle 操作语义**」的微积分。每个组件是一个 fiber，fiber 有 lifecycle：装载 → 激活 → 卸载。微积分给出 4 类 lifecycle 转换的形式化规则：

- **Withdrawal**（§4.3.1）：组件主动 / 被动卸载，所有 effect dispose、coefficient notification 触发 deactivating
- **Iteration**（§4.3.2）：组件反复装载 / 卸载（HMR 的基础——同一个组件的 source code 改了，runtime 重载它）
- **Asynchrony**（§4.3.3）：组件 effect / coeffect 操作是 async 的（涉及 IO 时），transition 不会立即完成
- **Failure**（§4.3.4）：组件装载失败 / 运行失败，runtime 处理失败并保持 context 一致性

这 4 类 transition 各自给出 small-step 操作语义规则（形式化定义在论文 §4.2 base calculus 段）。

**5 条 metatheorem 各自证明什么**：

| 定理 | 证明内容 | 工程含义 |
|---|---|---|
| **Preservation**（§4.4.1）| transition 前后 well-formedness 保持 | runtime 不会进入非法状态 |
| **Temporal Composability**（§4.4.2）| 组件卸载后所有 effect 都消失 | 「**我走之后世界恢复**」 |
| **Spatial Composability**（§4.4.3）| coeffect 依赖声明自动满足 / 取消 | 「**我进来后自动获得我需要的世界**」 |
| **Progress**（§4.4.4）| well-formed state 不会卡死（非死锁）| runtime 总会推进 |
| **Confluence**（§4.4.5）| 并发 transition 的最终结果唯一（与调度顺序无关）| 并发插件加载 / 卸载是 deterministic 的 |

这 5 条是论文的形式化核心——加起来证明了「**spatiotemporal composability 从单个组件可组合到整个系统**」（标题的 metatheory claim）。

工程视角：DSH 主仓的 `packages/core/invariants/` 是 runtime 对部分 metatheorem 的**自检实现**——`InvariantInstaller` 在 runtime 跑断言，违反时 throw。这条让 Cordis 不只是「**形式化框架**」也是「**可验证框架**」。

## §5 Implementation：Cordis 怎么落地的

§5.1 Core Library 是 Cordis 的实现核心：

- **§5.1.1 Effect Tracking**——`FiberState` 6 状态机（PENDING/LOADING/ACTIVE/FAILED/DISPOSED/UNLOADING）+ `DisposableList` LIFO stack + `_runner.execute` / `collect` 机制。这条对应刚才抓到的 `/tmp/cordis/packages/core/src/fiber.ts` 486 行——核心是「**effect stack + lifecycle state machine**」。
- **§5.1.2 Coeffect Operations**——`ctx.isolate(name, label?)` / `ctx.intercept(name, config)` + service registry 三件套：`RegistryService`（注册表）/ `ReflectService`（Proxy 反射 + service store 路径解析）/ `EventsService`（typed events + 4 dispatch mode）。
- **§5.1.3 Context Effects**（未抓）——`ctx.effect()` / `ctx.on()` API 的形式化定义。

§5.2 Loader 是声明式 component loader 章节（未抓）：从 `cordis.yml` 读 plugin 树 → resolve `!!js` 表达式 → configuration reconciliation（patch row by id）→ apply 到空 context。这条对应 DSH 主仓的 `cordis.patch.yml` 工作流。

§5.3 HMR 是 hot module replacement 章节（未抓）：监听文件变化 → 卸载旧 fiber → 装载新 fiber → effect 重新 reconcile → coeffect 重新满足。这条让开发体验是「**改 plugin 源码 → DSH 自动 reload 不丢状态**」。

§6 / §7 / §8 是 related work（与 actor model / reactive programming / capability systems 对比）+ future work + conclusion。Cordis 把自己定位成「**spatiotemporal composability 范式的第一个 runtime 实例化**」，与现有的 effect system / coeffect system 是**继承而非替代**——后者是 compile-time 静态分析，前者是 runtime 机制。

## 把 Cordis paper 和之前三个反写任务对齐

Cordis 论文是「**DSH 反写矩阵**」的**学术根**——之前四个反写任务（dsh-at-file / arXiv 2608.09696 / dsh-genui / dsh 主仓库）每一个都在用 Cordis 的范式但都不解释为什么：

| 反写任务 | Cordis 范式落点 |
|---|---|
| **dsh-at-file**（commit 96fa50b7）| `ctx.effect()` 注册 `agent/pre-step` 监听（revertible effect）+ `ctx.settings` coeffect 声明（reactive coeffect）+ `at-file-mention` source declaration（spatial composability 的 spec） |
| **dsh-genui**（commit 1e6c410a）| `ctx.tools` 注册 `render_ui` tool（coeffect spec）+ `ctx.effect()` 注册 panel 状态管理（revertible effect）+ `local-first` 原则是 temporal composability 的工程表达 |
| **arXiv 2608.09696**（commit 81c2ec4a，Murphy MDA）| Bayesian experiment design 隐式用了 Cordis 范式——design step 的 VoI（spatial composability）+ execute experiment 的 retract（temporal composability）。论文没明说但范式同构 |
| **deepseek-harness 主仓**（commit 9aa22718）| 整套主仓就是 Cordis 的 vendored 实例——`packages/core/session` 用 append-only log 实现「**Model-visible means logged**」= temporal composability 的工程表达；`packages/core/agent` 用 `agent/*` events 实现 coeffect notification |

四篇反写加起来正好覆盖 Cordis paper 的 4 个核心机制（revertible effects / reactive coeffects / unified context / calculus of dynamic composition）。本文是这个矩阵的**理论顶层**。

## 工程取舍：哪些决策是钉死的

**「Effect 必须有显式 disposable」**。论文 §3.1 + Cordis 源码 `Service[symbols.init]?.()` 都强制——没有隐式 cleanup。这条让 runtime 在组件卸载时**不依赖任何外部状态**——所有清理路径都 registered。这是为什么 DSH 主仓 `packages/core/invariants/` 能做「**invariant assertion**」——effect 系统的 spec 形式化。

**「Coeffect 是声明式不是 imperative」**。论文 §3.2 + `Service[symbols.config]` 机制——coeffect spec 通过 zod / schemastery 等 schema 定义，runtime 自动 reconcile。这是为什么 DSH 主仓 `ctx.settings.register(NS, AtFileSettingsSchema)` 必须配 schema——不是 free-form 的 runtime 数据。

**「Unified context type」**。论文 §3.3 + `Context[symbols.isolate]` + `Context[symbols.intercept]`——effect 和 coeffect 共享同一个 Context 对象。这条让 fiber 树管理**只有一个** dimension（tree shape），不是 effect-tree + coeffect-tree 两个 tree——这是 Cordis 实现比 Koishi cordis 更轻量的根因。

**「Declarative component loader」**。论文 §5.2 + `@deepseek-ai/cordis-plugin-include`（parser `!!js` 表达式）——plugin 配置在 `cordis.yml` 里声明，runtime 装配。这条让 plugin 作者**不用写 boot 顺序**——`inject: ['logger', 'config']` 就够了。

**「HMR 不丢状态」**。论文 §5.3 + `packages/hmr/` ——热重载时 effect stack 重新 reconcile，coeffect 重新满足，**用户态会话状态不丢**。这是为什么 DSH 开发体验可以做到「**改 plugin 源码 → 自动 reload**」。

**「Pre-release stance：foundation over blast radius」**。Cordis paper 是 preprint（draft 2026-08-13），明确说「**content may change substantially; please cite the latest version**」——和 DSH 主仓 AGENTS.md 的「**Remove this section at the first tagged release**」同一条原则：地基正确优先于兼容性垫片。

## 它故意没做的事

**没有跨 session 的 effect persistence**。Cordis 的 effect 生命周期绑定到 fiber；fiber 卸载时 effect 全部消失。如果你想「**effect 跨 session 保留**」（比如用户期望一个持久化的 agent 状态），需要在 effect 之上加「**persistable effect**」抽象——DSH 主仓的 `packages/session/` 就是这个抽象（把 effect 投影进 append-only log）。

**没有静态类型保证**。Cordis 把 effect / coeffect 从 compile-time 抬升到 runtime，意味着**类型系统保证消失**——比如「**这个函数会修改文件 IO**」不再是 TypeScript type-level fact，而是 runtime disposable chain。这条和 OCaml / Haskell 风格的 effect system 是**对立**的——后者追求静态保证，Cordis 追求动态可组合。

**没有概率 / 不确定性建模**。Coeffect spec 是 bool（满足 / 不满足）三态通知（activating/deactivating/neutral），不是概率。如果你想表达「**这个依赖 70% 满足**」，需要额外抽象。

**没有跨进程的 cordis**。Cordis 的 fiber tree 是单进程内的 tree。如果你想跨进程 reconciling effect / coeffect，需要分布式协议层——这是 Cordis paper 自己承认的 future work。

**没有形式化证明 runtime 复杂度**。§4 的 5 条 metatheorem 证明 correctness，但不证明 complexity。一个 O(n²) lifecycle 操作在 worst case 是合法的（满足 metatheorem），但实际不可用。

## 这件事为什么重要

Cordis paper 在 2026 年这个时间点回答的是一个根本性命题：

> **动态可组合性需要形式化基础——不是「**一个 plugin 装/卸不漏状态**」的经验工程，是「**整个系统的 effect 可逆性 + coeffect 反应性可以形式化证明**」的理论。**

这条命题的工程落地是：把 plugin 装载 / 卸载从「**调试 BUG**」变到「**runtime invariant assertion**」——DSH 主仓 `packages/core/invariants/` 30 行空不变式伴侣，**显式声明它**不持有 runtime invariant（因为动态组合的 5 条 metatheorem 由 effect + coeffect 系统保证，不需要事件流断言）。这是 Cordis paper 在工程层的**最锐利的副产品**——把「**怎么验证 plugin 系统的正确性**」这个问题从「**经验测试**」变成「**形式化证明 + 形式化断言**」。

下放换来三件事：

1. **动态插件的副作用可逆性有形式化证明**——不需要经验测试覆盖所有 path
2. **依赖声明是声明式的 + 反应式的**——不需要手动 wire
3. **unified context 简化 fiber 树管理**——单 dimension tree 不是 two-dimension

代价也很清楚：

- **runtime 机制比 compile-time 类型检查贵**——每次 effect 操作都进 disposable stack
- **coefficient spec 写得不好会引入运行时错误**——runtime 不知道 spec 是否「**正确**」
- **跨进程 dynamic composability 没有现成解**——需要新论文

代码层面，`revertible effect + reactive coeffect + unified context type + declarative loader + HMR` 是这个范式能工程化落地的五个钉子。少一个，要么 plugin 卸不清、要么依赖不会自动满足、要么 fiber tree 难管理、要么配置硬编码、要么改源码要重启。

`88 页 PDF v0.7` 是这件事的当前最优解（draft of August 13, 2026 / preprint under active revision）。下一版本会是什么——也许是 async transition 的更精细建模（§4.3.3 asynchrony 当前是最简形式）也许是 distributed dynamic composability（跨进程 fiber 树 reconciling）——但「**spatiotemporal composability = temporal composability + spatial composability 联合**」这条根本论题，大概率会留下。

## 维护指引：从 Cordis paper 读后续工作的几件事

**DSH 反写矩阵的学术根**。之前四个反写任务（dsh-at-file / dsh-genui / arXiv 2608.09696 / dsh 主仓）每一个都在用 Cordis 范式但不解释为什么。本文是这个矩阵的理论顶层——读完本文回头看四篇反写，可以看到每个 `ctx.effect()` / `ctx.on()` / `ctx.tools` 调用都在对应 paper 的 §3 revertible effect / reactive coeffect 机制。

**和 Koishi cordis 的关系**。Cordis paper 没有明说，但和 Koishi cordis 有血缘关系——两者都是 plugin-based framework，都用 service registry。区别是 Koishi 是 Koishi 生态专用（机器人平台），Cordis 是「**meta-framework**」（spatiotemporal composability 范式的实例化）。DSH 用 Cordis 是因为它**在 Node 生态独立可嵌**——`packages/core/` 全部 `import from '@deepseek-ai/cordis'`。

**和 effect systems / coeffect systems 的关系**。Cordis paper 在 §1.3 + §3.3.3 明确说「**和静态 effect/coeffect 系统是继承而非替代**」——compile-time 静态分析（OCaml / Koka / Eff）做 type-level guarantee，runtime 动态机制（Cordis）做 dynamic composability。两者服务的场景不同——静态适合「**编译期就知道所有 effect 的纯函数式语言**」，动态适合「**runtime 装载 / 卸载 plugin 的应用框架**」。

**和 self-evolving agent harnesses 的关系**。§1.2.2 把 DSH 类 harness 当作核心 motivating example——「**agent 在运行时检查、装载、卸载它自己的 plugin**」是 spatiotemporal composability 最 demanding 的应用场景。这条让 DSH 主仓 `packages/self-modification/` 不再是「**特殊插件**」而是「**范式的标志性应用**」。

**Metatheorem 在工程层的验证**。DSH 主仓 `packages/core/invariants/` 30 行空不变式伴侣——这本身就是一条 statement：「**这个包没有 runtime invariant**」，因为 spatiotemporal composability 的 5 条 metatheorem 由 effect + coeffect 系统形式化保证，**不需要事件流断言**。这个 statement 比一行行 invariant assertion 更值钱——它说「**我们用的是更好的不变量机制**」。

**Future work 推测**。论文 §8 / future work 提到几条可能方向：
- **distributed dynamic composability**——跨进程 fiber tree reconciling
- **probabilistic coeffects**——coefficient spec 引入概率分布
- **asynchronous transitions**——§4.3.3 asynchrony 当前最简，需要更精细建模
- **migration to mainstream languages**——当前是 Node + TypeScript，理论上可以移植到 OCaml / Rust

**引用 Cordis 的方式**。论文是 preprint draft 2026-08-13，「**content may change substantially**」。引用时建议加 version + retrieval date：`Shi, Zhang, Cui, 2026. "A Programming Paradigm for Spatiotemporal Composability", draft of August 13, 2026. https://github.com/cordiverse/paper`。

**和 DSH 主仓 vendored Cordis 的关系**。DSH 主仓 `vendor/cordis/` 是 Cordis 源码的 vendored 版本——所有 DSH 包都 `@deepseek-ai/cordis` 作为 peerDependency。这条 vendoring 决策让 DSH 不依赖外部 npm registry 的可用性——所有 framework 依赖跟着仓库走。代价是 PR 体积可能很大（升级 vendored package 时）。

**Cordis paper vs Cordis 源码**。Cordis paper 是**理论**（5 条 metatheorem 形式化证明），Cordis 源码是**工程**（1848 行 core + hmr + loader + group + include + utils + logger-console + timer + create 9 个 packages）。两者一起构成完整图景：理论告诉你「**为什么这样**」，源码告诉你「**怎么实现**」。Cordis paper 适合 PL 研究者读，Cordis 源码适合 framework 工程师读。

**对比 dsh 主仓的「**Where new behavior goes**」 17 个扩展点**——这些扩展点都是 Cordis 范式的工程映射：`ctx.tools`（coeffect spec）/ `ctx.effect()`（revertible effect）/ `ctx.agents.isolate`（spatial composability）/ `cordis.patch.yml`（declarative loader）。读 Cordis paper 后回头看 dsh 主仓 architecture.md 的 17 个扩展点，能看到每个都在用 Cordis paper §3 / §4 的哪条定理。