---
title: "Cordis：把「可逆副作用」做成插件框架的元框架"
date: "2026-08-23T03:20:00+08:00"
slug: cordis-spatiotemporal-composability-framework
github_repo: "cordiverse/cordis"
source_key: "gh:cordiverse/cordis"
description: "Cordis 是 DeepSeek Harness 底层以 vendor 方式引入的插件元框架，把插件、上下文、服务依赖、类型化事件与可逆副作用五大概念做成运行时机制。本文解析其核心概念、事件分发模式与 Loader 配置，并说明它与同组织论文仓库的分工。"
draft: false
categories: ["技术笔记"]
tags: ["插件框架", "依赖注入", "Cordis", "DeepSeek Harness"]
---

# Cordis：把「可逆副作用」做成插件框架的元框架

## 核心判断

插件框架最常见的死法是：**插件装上容易，卸掉时副作用清不干净**。Cordis 把「清理」从约定升级成机制——每个注册都对应一个 disposer，卸载时按序撤销，这是它和普通依赖注入容器的分水岭。Cordis 自我定位为「时空可组合性的元框架」（Meta-Framework of Spatiotemporal Composability），目前处于活跃开发期，API 尚未稳定（core 包版本为 `4.0.0-rc.8`）。

它最值得注意的身份是：**DeepSeek Harness（DSH）底层以 vendor 方式引入的插件框架**。DSH 主仓 README 明确说过「everything is a plugin, powered by Cordis」——理解 Cordis，等于理解 DSH 插件体系的工作方式。

## 它与论文仓库的分工

`cordiverse/cordis` 和 `cordiverse/paper` 是两个仓库。`paper` 是 DeepSeek 与北京大学联合发布的 88 页论文《A Programming Paradigm for Spatiotemporal Composability》的存放处，讲的是 effect/coeffect 抬升为运行时机制的理论；`cordis` 是这个理论的工程实现。读理论看 paper，动手写插件看 cordis——两者互补，不重复。

## 系统地图：五个核心概念

Cordis 的全部设计可以压缩成五个概念。理解了这五个词，就理解了它：

| 概念 | 一句话 | 关键机制 |
|------|--------|----------|
| 插件（Plugin） | 实现 Service 的对象，可以是个带 `inject`/`apply(ctx)` 的函数，也可以是 Service 子类 | 生命周期由 Cordis 挂载到上下文 |
| 上下文（Context） | 服务的容器，一个服务占据一个稳定的 `ctx.<key>` | 通过 key 查找服务，而非 import 具体实现 |
| 依赖注入（inject） | 插件声明所需服务，就绪后才启动 | 加载顺序由依赖表达，不靠手动编排 |
| 类型化事件（Events） | 通过 TypeScript 声明合并注册事件名 | emit / waterfall / parallel / serial 四种分发 |
| 可逆副作用（Effects） | 注册是带清理函数的副作用 | `ctx.effect()` / `ctx.on()` 安装，reload/teardown 时撤销 |

### 上下文即服务容器

Cordis 里没有「拿到组件实例」这种写法。一个服务占据一个稳定的 `ctx.<key>`，例如 `ctx.tools`、`ctx.llm`、`ctx.sessions`；其他插件通过 key 查找服务，而不是直接 import 实现类。这套按 key 寻址的设计，让服务实现可以被替换、mock、或在不同环境（桌面 / 浏览器 / 测试）注入不同实例。

### 依赖声明取代启动编排

插件用 `inject` 字段声明自己需要的服务。Cordis 会等这些服务就绪后再启动插件，因此启动顺序是**从依赖关系推导出来的**，不是写死在 main 函数里的一串 `init()`。新增一个插件，只要声明好依赖，框架负责把它排进正确的位置。

### 事件：四种分发模式

事件是插件间通信的主干，每种事件有且只有一种分发模式，公开约定一部分：

- **emit**：不 await，监听器按注册顺序观察，无返回值
- **waterfall**：不 await，按顺序观察，有返回值（环绕中间件语义）
- **parallel**：await，所有监听器并行观察，无返回值
- **serial**：await，按注册顺序执行，有返回值

其中 `ctx.waterfall` 是最有 Cordis 特色的一个。监听器接收 `(...args, next)`，调用 `next()` 会执行下游监听器，下游的返回值通过 `next()` 回到当前层，可包装后继续向外返回；不调用 `next()` 直接返回则**短路**。对单决策事件，短路是设计意图——策略监听器拥有决策权时可以不走 `next()` 直接拍板，只做观察的监听器则必须委托给下游。

### 可逆副作用：本文开头那个判断

每个注册都对应一个 disposer（资源释放函数），来源有两种：`ctx.effect()` 返回的清理函数，或 Cordis 提供的辅助方法自动处理。如果 teardown 顺序有要求，把相关工作放在同一个 effect 里，保证资源按预期顺序释放。reload 和 teardown 时，这些注册按声明撤销——这就是「时间可组合性」在工程层的落点。

## Loader 与配置

Cordis 的插件加载器配合 `@cordisjs/plugin-include` 工作，配置条目支持 `!!js` 表达式节点。Loader 在声明的注入激活后，基于插件上下文（`ctx.serviceName`）插值条目的 config；在每次挂载决策时，基于 loader 上下文插值 `disabled` 字段。需要按环境选择插件时，使用 overlay。

仓库以 yarn 4 workspaces 管理多个包：`core`（核心）、`create`（脚手架）、`group`、`hmr`（热更新）、`include`、`loader`、`logger-console`、`timer`、`utils`。核心只依赖 `cosmokit` 与 `@standard-schema/spec` 两个运行时依赖，sideEffects 为 false，具备 tree-shaking 条件。

## 实践规则：什么该放哪

Cordis 的官方文档给出了三条相当明确的分层规则，直接决定你写插件时把逻辑放哪：

1. **工具流水线事件属于 `ctx.tools`**，模型流式输出属于 `ctx.llm`，实时 agent 协调属于 `ctx.agents`——按能力域归属，不混放
2. **拦截和策略优先使用事件**，直接能力调用优先使用服务方法——观察用事件，调用用方法
3. **每个注册都要有 disposer**——要么从 `ctx.effect()` 返回一个，要么用框架辅助方法自动处理

## 采用建议与边界

- **想理解 DSH 插件体系**：这是必读框架。DSH 的子系统页面（服务/事件参考）全部建立在 Cordis 概念之上，先读本文五个概念，再进子系统，不会迷路
- **想写自己的插件框架**：Cordis 的「可逆副作用 + 按 key 寻址 + 事件分发」三角是值得抄的骨架，尤其是 `ctx.waterfall` 的环绕中间件语义
- **边界**：Cordis 处于活跃开发期，API 可能无通知变更，生产项目直接依赖需评估版本锁定成本；官方文档目前以 `cordis-primer` 形式随 DSH 文档站发布，单独的 API 参考还在演进中

本文只讲框架本身的使用与架构，不展开论文里的形式化证明（revertible effects / reactive coeffects 的理论细节见同组织 `cordiverse/paper` 的解读文章）。
