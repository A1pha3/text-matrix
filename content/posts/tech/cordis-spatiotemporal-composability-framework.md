---
title: "Cordis：把「可逆副作用」做成插件框架的元框架"
date: "2026-08-23T03:20:00+08:00"
lastmod: "2026-10-04T17:30:00+08:00"
slug: cordis-spatiotemporal-composability-framework
github_repo: "cordiverse/cordis"
source_key: "gh:cordiverse/cordis"
description: "Cordis 是 DeepSeek Harness 底层以 vendor 方式引入的插件元框架，把插件、上下文、服务依赖、类型化事件与可逆副作用做成运行时机制。本文对照 main 分支源码（core 4.0.0-rc.10）与官方文档，核实五大概念、五种事件分发模式与 vendor 前后的双包名，并用一个插件从加载到卸载的完整任务流串起全部机制。"
draft: false
categories: ["技术笔记"]
tags: ["插件框架", "依赖注入", "Cordis", "DeepSeek Harness"]
---

# Cordis：把「可逆副作用」做成插件框架的元框架

## 核心判断

插件框架最常见的死法是：**插件装上容易，卸掉时副作用清不干净**。Cordis 把「清理」从约定升级成机制——每个注册都对应一个 disposer（资源释放函数），卸载时按序撤销。这是它和普通依赖注入容器的分水岭。Cordis 自我定位为「时空可组合性的元框架」（Meta-Framework of Spatiotemporal Composability）；core 包在 main 分支的版本是 `4.0.0-rc.10`（2026-10-04 核实），README 明说 API 尚未稳定、可能无通知变更。

它最值得注意的身份是 **DeepSeek Harness（DSH）的插件底座**。DSH 主仓（`deepseek-ai/deepseek-harness`，2026-10-04 时约 24.3 万 stars）README 的原话是 "built on an **everything-is-a-plugin** architecture and powered by Cordis"，并把设计论文直接链到了 Cordis。DSH 的 `vendor/` 目录以 vendor 方式引入了 cordis 全套：`cordis`、`cosmokit`、`group`、`hmr`、`include`、`loader`、`logger-console`、`schemastery`、`timer`。理解 Cordis，等于理解 DSH 插件体系的工作方式。

另一个身份常被忽略：**Cordis 不是 DSH 时代的新框架**。仓库 2022 年 5 月创建（2026-10-04 时约 9.0k stars），而 Koishi——一个 2019 年建仓的跨平台聊天机器人框架——其核心包 `@koishijs/core` 的依赖表里至今写着 `cordis: ^3.18.1`。这套内核先在 Koishi 生态跑了多年生产环境，才被 DSH vendor 进来。评估「4.0 未稳定」的风险时要把这段历史算进去：不稳定的是 4.0-rc 这条线，不是这套代码。

## 它与论文仓库的分工

`cordiverse/cordis` 和 `cordiverse/paper` 是两个仓库，对应「工程实现」和「理论基础」。`paper` 存放论文 *A Programming Paradigm for Spatiotemporal Composability*（arXiv:2608.25512，92 页，2026-08-26 提交，作者 Yifan Shi、Wei Zhang、Tianyi Cui，单位为北京大学与 DeepSeek-AI）：把 effect/coeffect 这对编程语言概念抬升为运行时机制，形式化「可逆副作用」（revertible effects）与「响应式共效应」（reactive coeffects）。`cordis` 是这套理论的工程实现。读理论看 paper，动手写插件看 cordis——两者互补，不重复。

## 系统地图：五个核心概念

Cordis 的全部设计可以压缩成五个概念，官方 cordis-primer 文档的表述与源码一一对应：

| 概念 | 一句话 | 关键机制 |
|------|--------|----------|
| 插件（Plugin） | 实现 Service 的对象：带可选 `inject` 和 `apply(ctx)` 的函数，或 Service 子类 | 生命周期由 Cordis 挂载到上下文 |
| 上下文（Context） | 服务的容器，一个服务占据一个稳定的 `ctx.<key>` | 通过 key 查找服务，而非 import 具体实现 |
| 依赖注入（inject） | 插件声明所需服务，就绪后才启动 | 加载顺序由依赖表达，不靠手动编排 |
| 类型化事件（Events） | 通过 TypeScript 声明合并注册事件名 | emit / waterfall / parallel / serial / bail 五种分发 |
| 可逆副作用（Effects） | 注册是带清理函数的副作用 | `ctx.effect()` / `ctx.on()` 安装，reload/teardown 时撤销 |

一个最小插件长这样（出自官方教程第 1 章）：

```ts
import type { Context } from '@deepseek-ai/cordis'

export const name = 'hello'

export function apply(ctx: Context) {
  console.log('hello from my first plugin')
}
```

加载它的方式不是写启动代码，而是写一份 YAML：

```yaml
- name: './hello.ts'
```

启动器创建根 Context、挂载 Loader 插件，Loader 读取这份 `cordis.yml` 并挂载 `hello.ts`，然后 Cordis 调用 `apply(ctx)`。配置项并发启动，列表位置不决定加载顺序——顺序由 `inject` 声明的服务依赖推导。插件描述贡献，配置组合应用，这是 Cordis 和「main 函数里排一串 init()」的根本区别。

### 上下文即服务容器

Cordis 里没有「拿到组件实例」这种写法。一个服务占据一个稳定的 `ctx.<key>`，例如 `ctx.tools`、`ctx.llm`、`ctx.sessions`；其他插件通过 key 查找服务，而不是直接 import 实现类。按 key 寻址让服务实现可以被替换、mock，或在不同环境（桌面 / 浏览器 / 测试）注入不同实例。

### 依赖声明取代启动编排

插件用 `inject` 字段声明自己需要的服务，Cordis 等这些服务就绪后再启动插件。新增一个插件，只要声明好依赖，框架负责把它排进正确的位置。

### 事件：五种分发模式

事件是插件间通信的主干。源码里 `DispatchMode` 枚举了五种：`'emit' | 'parallel' | 'serial' | 'bail' | 'waterfall'`。每种事件绑定一种模式，只能通过对应方法分发——模式是事件公开约定的一部分，DSH 的新事件用 `@mode` 标签记录模式，让生成的目录能与分发调用点交叉校验：

| 模式 | 是否 await | 分发顺序 | 返回值 |
|------|-----------|----------|--------|
| emit | 否 | 按注册顺序观察 | 无 |
| waterfall | 否 | 按注册顺序观察 | 有 |
| parallel | 是 | 所有监听器并行观察 | 无 |
| serial | 是 | 按注册顺序观察，首个非 `null`/`false`/`undefined` 返回值胜出并停止 | 有 |
| bail | 否 | serial 的同步版本 | 有 |

`parallel` 的实现在源码里走 `Promise.allSettled`，有监听器失败时把全部错误聚合成一个 `AggregateError` 抛出——部分失败不会被静默吞掉。

其中 `ctx.waterfall` 是最有 Cordis 特色的一个。监听器接收 `(...args, next)`，调用 `next()` 执行下游监听器，下游的返回值通过 `next()` 回到当前层，可包装后继续向外返回；不调用 `next()` 直接返回则**短路**（官方文档称之为「否决」）。链条上所有监听器都调用了 `next()` 时，执行的是分发调用方传入的兜底函数。对单决策事件，短路是设计意图——策略监听器拥有决策权时可以直接拍板，只做观察的监听器则必须委托。官方教程第 4 章的示例把两种行为放在同一个事件里：

```ts
import type { Context } from '@deepseek-ai/cordis'

declare module '@deepseek-ai/cordis' {
  interface Events {
    'demo/transform'(input: string, next: () => Promise<string>): Promise<string>
  }
}

export function apply(ctx: Context) {
  // 监听器 1：包装下游结果
  ctx.on('demo/transform', async (input, next) => {
    const downstream = await next()
    return downstream.toUpperCase()
  })

  // 监听器 2：拥有决策权时短路
  ctx.on('demo/transform', async (input, next) => {
    if (input.includes('blocked')) return '** blocked **'
    return next()
  })
}
```

同一个 `next()` 调用两次会直接抛 `Error('next() called multiple times')`——环绕中间件的协议由运行时强制，不靠约定自觉。

### 可逆副作用：机制而不是约定

每个注册都对应一个 disposer。core 源码里 `ctx.on()` 的注册最终落到一行 `this.ctx.fiber.effect(() => {...})`——监听器本身就是 effect，撤销逻辑由框架持有。自己管理的外部资源（定时器、连接、watcher）用 `ctx.effect()` 包装，返回清理函数即可：

```ts
ctx.effect(() => {
  const timer = setInterval(() => console.log('tick'), 200)
  return () => clearInterval(timer)
})
```

effect 主体在加载期间运行，disposer 在卸载期间运行；生命周期与插件一致的资源不需要手动调 disposer。如果 teardown 顺序有要求，把相关工作放进同一个 effect。reload 和 teardown 时这些注册按声明撤销——「时间可组合性」在工程层的落点就在这里。

## Loader 与配置

Cordis 的插件加载器（`@cordisjs/plugin-loader`）配合 `@cordisjs/plugin-include` 工作，后者把 YAML 里的 `!!js` 节点解析为表达式（源码里对应 `tag:yaml.org,2002:js` 类型）。Loader 在声明的注入激活后，基于插件上下文（`ctx.serviceName`）插值条目的 config；每次挂载决策时再基于 loader 上下文插值 `disabled` 字段，`disabled` 沿父条目链向下传播。需要按环境选择插件时使用 overlay。

包名有一处容易踩坑：cordis 仓库内是 `@cordisjs/plugin-include`，被 DSH vendor 之后改用 DeepSeek 的 scope——官方教程里 import 的是 `@deepseek-ai/cordis` 与 `@deepseek-ai/cordis-plugin-include`。看 DSH 文档照抄 import 到 cordis 仓库的环境会找不到包，反之亦然。

仓库用 yarn 4（`packageManager: yarn@4.14.1`）workspaces 管理九个包：`core`（npm 包名 `cordis`）、`create`（脚手架 `create-cordis`）、`group`、`hmr`（热更新）、`include`、`loader`、`logger-console`、`timer`、`utils`。core 的运行时依赖只有 `cosmokit` 与 `@standard-schema/spec` 两个，`sideEffects` 为 false，具备 tree-shaking 条件。

## 任务流案例：一个插件从加载到卸载

把五个概念串成一次真实流转。官方教程第 3、4 章给了两个文件。`stats.ts` 定义一个计数服务，每次计数变化时发出事件：

```ts
import { Service, type Context } from '@deepseek-ai/cordis'

declare module '@deepseek-ai/cordis' {
  interface Context {
    stats: StatsService
  }
  interface Events {
    'stats/report'(name: string, count: number): void
  }
}

export class StatsService extends Service {
  private counts = new Map<string, number>()

  constructor(ctx: Context) {
    super(ctx, 'stats')
  }

  bump(name: string) {
    const next = (this.counts.get(name) ?? 0) + 1
    this.counts.set(name, next)
    this.ctx.emit('stats/report', name, next)
  }
}

export function apply(ctx: Context) {
  ctx.plugin(StatsService)
}
```

`reporter.ts` 声明依赖这个服务，并监听它的事件：

```ts
import type { Context } from '@deepseek-ai/cordis'
import type {} from './stats.ts'

export const name = 'reporter'
export const inject = ['stats']

export function apply(ctx: Context) {
  ctx.on('stats/report', (name, count) => {
    console.log(`[stats] ${name} -> ${count}`)
  })
  ctx.stats.bump('tool_call')
  ctx.stats.bump('tool_call')
  ctx.stats.bump('prompt')
}
```

用 YAML 把两个文件组合起来：

```yaml
- name: './stats.ts'
- name: './reporter.ts'
```

运行后输出：

```
[stats] tool_call -> 1
[stats] tool_call -> 2
[stats] prompt -> 1
```

这条流转里每一步都是机制在起作用：加载顺序不靠列表位置——`reporter` 声明了 `inject: ['stats']`，无论两个条目在 `cordis.yml` 里谁前谁后，Cordis 都会让它等 `StatsService` 占据 `ctx.stats` 再启动；`ctx.on()` 注册的监听器是一个 effect，插件卸载时自动移除，永远不需要手写 `removeListener`；`interface Events` 的声明合并让 `emit` 和 `on` 两端都拿到完整类型——运行时没有任何接线，类型纯粹是编译期约定。

卸载走 fiber 的状态机：每个已加载插件实例是一个 fiber，沿 `PENDING → LOADING → ACTIVE → UNLOADING → DISPOSED` 转换，`apply` 或配置校验抛异常则进入 `FAILED`。`fiber.dispose()` 会等全部清理工作（包括异步 disposer）完成才结束，并递归卸载子插件。

## 排查：三个常见症状

- **插件没有任何输出**：先查 fiber 是否卡在 `PENDING`——已经声明，但 `inject` 的服务不可用。官方教程把这列为「为什么我的插件没有输出」的第一答案。
- **新增配置项毫无反应**：模块**解析失败**（路径或包名拼写错误）时 Cordis 通过 logger 服务报告错误而不崩溃，启动早期这条报告还可能在 console 导出器开始观察之前丢失。先查拼写。注意这和 `apply` 抛异常是两条路径：后者会让进程直接终止，失败被显式暴露。
- **npm 上装不到 4.0**：npm 的 `latest` 标签目前停在 `3.18.1`，4.0 线在 npm 上最高只发布到 `4.0.0-beta.5`，`rc` 系列只存在于 GitHub main 分支（2026-10-04 核实）。要试 rc 只能直接依赖仓库。

## 实践规则：什么该放哪

官方文档给出三条分层规则，直接决定写插件时把逻辑放哪：

1. **按能力域归属**：工具流水线事件属于 `ctx.tools`，模型流式输出属于 `ctx.llm`，实时 agent 协调属于 `ctx.agents`，不混放
2. **观察用事件，调用用方法**：拦截和策略优先使用事件，直接能力调用优先使用服务方法
3. **每个注册都要有 disposer**：要么从 `ctx.effect()` 返回一个，要么用框架辅助方法自动处理；teardown 顺序有要求时放进同一个 effect

## 采用建议与边界

- **想理解 DSH 插件体系**：这是必读框架。入口按顺序走：[cordis-primer](https://deepseek-harness.github.io/deepseek-harness/reference/cordis-primer)（概念）→ [官方教程](https://deepseek-harness.github.io/deepseek-harness/develop/cordis-tutorial/)（七章动手实践，无需 API 密钥）→ DSH 子系统页面的服务/事件参考。先吃透本文五个概念再进子系统，不会迷路
- **想写自己的插件框架**：「可逆副作用 + 按 key 寻址 + 五种事件分发」是值得抄的骨架，尤其是 waterfall 的环绕中间件语义和 bail 的同步决策语义——后者是多数事件系统缺失的一块
- **想直接在生产依赖 cordis**：区分两条线。3.x 稳定线经过 Koishi 生态多年验证（`@koishijs/core` 至今依赖 `^3.18.1`）；4.0-rc 是活跃开发线，API 可能无通知变更，直接依赖需评估版本锁定成本。单独的 API 参考还在演进中，目前以 cordis-primer 形式随 DSH 文档站发布
- **边界**：本文只讲框架本身的使用与架构，不展开论文的形式化证明（revertible effects / reactive coeffects 的理论细节见 arXiv:2608.25512 与 cordiverse/paper），也不覆盖 DSH 子系统如何逐个映射到这些概念

---

本文事实核查基准（2026-10-04）：GitHub API（cordiverse/cordis 8,994 stars、MIT、TypeScript、创建于 2022-05-17；deepseek-ai/deepseek-harness 243,104 stars；cordiverse/paper 3,005 stars）、npm registry（cordis latest 3.18.1，4.0.0-beta.5）、main 分支源码（packages/core/package.json 版本 4.0.0-rc.10、events.ts 的 DispatchMode、fiber.ts、include 包源码）、arXiv:2608.25512（92 pages）及论文 PDF 首页、cordis-primer 与官方教程（deepseek-harness.github.io）。
