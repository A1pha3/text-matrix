---
title: "Bun v1.3.14：90K Stars 的 all-in-one JavaScript 工具链完整指南"
date: "2026-05-16T03:11:38+08:00"
slug: "bun-javascript-runtime-all-in-one-toolkit"
description: "Bun 真正的差异化不是「快」，而是把运行时、打包、测试、包管理四件事合并到一个二进制里，改变了 JS 工具链的依赖结构。本文拆解 JavaScriptCore 选型动机、四合一架构的工程含义、一次 bun run 的完整执行路径，以及与 Node.js / Deno 的真实取舍和迁移风险。"
draft: false
categories: ["技术笔记"]
tags: ["JavaScript", "Bun", "Rust", "Node.js", "TypeScript", "打包工具"]
---

# Bun v1.3.14：90K Stars 的 all-in-one JavaScript 工具链完整指南

Bun 真正改变 JavaScript 工具链的点，是把运行时、打包器、测试运行器、包管理器四件事压进同一个二进制。这套合并带来的工程含义，比「启动快 4 倍」更值得拆开看：它改变了 JS 工具链的依赖管理方式——以前一个项目要 `node` + `esbuild` + `jest` + `npm` 四个独立工具，升级节奏对不齐、报错栈跨工具、锁版本要分别管，现在只有一个版本号要追。代价是 Node.js 兼容性不是 100%，部分原生模块仍要回退到 Node。

下文按「为什么这样选 → 四合一怎么落地 → 一次执行怎么流过去 → 什么时候该用什么时候该等」的顺序展开。版本基线 v1.3.14（2026-05-13），90,566 Stars，已越过实验阶段，进入生产可用区间，但生产可用不等于零风险——文末给出具体的迁移边界。

> **目标读者**：JS / TS 后端与全栈工程师；评估工具链升级的技术负责人
> **难度**：⭐⭐（中级；假设熟悉 Node.js 与 npm 工作流）
> **基线版本**：[Bun v1.3.14（2026-05-13）](https://bun.com/blog/bun-v1.3.14)

---

## 本文覆盖范围

1. 四合一架构到底改变了 JS 工具链的什么
2. 为什么选 JavaScriptCore 而不是 V8，以及这个选择的兼容性代价
3. 一次 `bun run index.tsx` 从入口到 JavaScriptCore 执行到模块解析的完整路径
4. 四个核心能力的真实工程用法和踩坑点
5. v1.3.14 改了什么、不改了什么
6. 什么时候该上 Bun，什么时候该再等等

---

## 总览：Bun 把什么压进了一个二进制

Bun 官方对自己的定义是「all-in-one toolkit for JavaScript and TypeScript apps」，拆开是四个职责。Node.js 生态里这四件事通常由四个独立工具承担，Bun 把它们合并到一个二进制里：

| 职责 | 替代对象 | 关键差异 |
|------|----------|----------|
| 运行时 | Node.js | 引擎换成 JavaScriptCore，冷启动和内存占用更低 |
| 打包器 | esbuild / Webpack / Vite | 内置在二进制里，不需要再装一个 dev 依赖 |
| 测试运行器 | Jest / Vitest | API 与 Jest 高度相似，迁移成本低 |
| 包管理器 | npm / yarn / pnpm | 全局缓存 + 硬链接，安装路径与 pnpm 思路接近 |

以前一个项目要 `node` + `esbuild` + `jest` + `npm`，现在只需要一个 `bun`。少装几个工具是直观收益，但真正改变开发体验的是版本对齐和配置共享——`bun build` 出来的产物和 `bun run` 跑的代码用同一个 transpiler，`bun test` 和 `bun run` 共享同一份模块解析逻辑。Node.js 生态里，esbuild 升级破坏 Jest snapshot、ts-node 和 Vite 的 TypeScript 配置不一致这类问题，在 Bun 里不会出现，因为四个工具共用同一套底层实现。

合并也有代价。Node.js 生态里 esbuild 出问题，可以换 swc 或 Vite；Bun 的打包器出问题，只能等官方修。这是单二进制架构的固有 trade-off：工具出问题不能换，但四个工具的行为永远对齐。

### 与 Node.js / Deno 的对照

| | Node.js | Deno | Bun |
|---|---|---|---|
| 引擎 | V8 | V8 | JavaScriptCore |
| 实现语言 | C/C++ | Rust | Zig |
| 包管理 | npm（独立工具） | 内置（去中心化 URL） | 内置（npm registry 兼容） |
| TypeScript | 需 tsc / ts-node / swc | 原生支持 | 原生支持（内置 transpiler） |
| 打包器 | 需单独安装 | 无内置打包器 | 内置 |
| 测试运行器 | 需单独安装 | 内置 | 内置 |
| Node.js 兼容 | 原生 | 通过 `npm:` 协议兼容 | 通过 `node:` 模块兼容层 |

三者真正的分歧在「如何对待 npm 生态」。Node.js 是 npm 生态本身；Deno 早期拒绝 npm，后来通过 `npm:` 协议兼容；Bun 一开始就做 npm registry 兼容，把 `package.json` 和 `node_modules` 当成事实标准保留下来。这个选择决定了 Bun 能直接跑大部分现有 Node.js 项目，而 Deno 的迁移成本更高——Deno 的迁移要改 import 路径，Bun 的迁移只需要换运行时。

---

## 为什么是 JavaScriptCore，以及代价是什么

Bun 与 Deno 最大的技术分歧是引擎选型。Deno 选 V8，是因为 V8 最成熟、性能上限最高，且 Deno 团队有 V8 经验。Bun 选 JavaScriptCore（WebKit 的 JS 引擎），盯着的是两个具体目标：冷启动和内存占用。

**冷启动开销低**。JavaScriptCore 的初始化路径比 V8 短。V8 启动时要构建完整的 isolate、初始化 JIT 编译器、加载内置库，这套开销在长期运行的服务端进程里被摊薄，但在 CLI 工具、Serverless 函数、脚本这类「跑一次就退出」的场景里占比很高。Bun 的目标场景里冷启动是常态，JSC 的这个特性刚好对上——Serverless 函数的冷启动延迟直接进用户感知的 P99，CLI 工具的启动延迟则卡在开发者每一次保存-运行的循环里。

**内存占用更紧凑**。JSC 的内存模型对短生命周期进程更友好。同样跑一个 Hello World HTTP 服务，Bun 的常驻内存通常比 Node.js 低 30-50%。在容器化部署、函数计算场景里，这直接影响实例密度——同样的内存预算下，能跑更多 Bun 实例，单位成本更低。

**Zig 在这里扮演的角色**。Bun 团队用 Zig 直接调用 JSC 的 C API，绕过了 V8 的 C++ 抽象层。Zig 的手动内存管理和 comptime 特性让 Bun 能在编译期做更多检查，运行时开销更低。这是 Bun 团队的技术判断，行业里没有共识——Deno 团队认为 V8 + Rust 的组合更稳，因为 V8 的成熟度和 Rust 的内存安全各有保障。

代价是兼容性。Node.js 生态里有一批包直接调用了 V8 的内部 API（典型的有 `node-bindings`、部分 native addon、用了 `v8.h` 的包），这些在 Bun 上跑不起来。Bun 通过 `node:` 模块兼容层覆盖了 `fs`、`path`、`process`、`Buffer` 等常用模块，但涉及 V8 内部接口的包需要 polyfill 或替代方案。具体的兼容性状态可以查 [Bun 的 Node.js 兼容性列表](https://bun.com/docs/runtime/nodejs-compat)——迁移前先跑一遍现有测试套件，比看文档更可靠。

---

## 一次 `bun run` 怎么流过系统

看一次真实执行。假设入口是 `index.tsx`，这条路径展示了 Bun 的四个组件如何协作：

```typescript
// index.tsx
import { Hono } from 'hono'

const app = new Hono()
app.get('/', (c) => c.text('Hello from Bun!'))

export default { port: 3000, fetch: app.fetch }
```

执行 `bun run index.tsx`，路径如下：

**1. 入口解析**。Bun 读取 `index.tsx`，识别出是 TypeScript + JSX。这里不调用 `tsc`，也不读 `tsconfig.json` 做类型检查——Bun 内置的 transpiler 只做语法转换（TS → JS、JSX → `createElement` 调用），不做类型诊断。类型检查交给 IDE 或独立的 `tsc --noEmit`。这是 Bun 启动快的关键之一：跳过了类型检查这一步。

**2. 模块图构建**。Bun 从 `index.tsx` 出发，递归解析 `import` 语句。遇到 `hono`，按 Node.js 模块解析算法查找 `node_modules/hono`，读到其 `package.json` 的 `exports` 字段，定位入口文件。整个模块图在内存里构建完成，每个模块记录自己的路径、依赖、转换后的代码。

**3. JavaScriptCore 接管**。模块图构建完成后，Bun 把转换后的代码喂给 JavaScriptCore。JSC 解析、编译（先用解释器 tier，热点代码再 JIT）、执行。`Hono` 的 `app.fetch` 被注册为 HTTP 请求处理函数。

**4. 内置 API 接入**。`Bun.serve`（由 `export default { fetch }` 触发的默认行为）底层走的是 Bun 用 Zig 实现的 HTTP 服务器，在 Linux 上用 io_uring，在 macOS 上用 kqueue。请求进来后不经过 libuv 这层，直接从内核事件循环到 JSC 回调。

**5. 进程退出**。HTTP 服务器保持运行，进程不退出。如果是脚本类入口（没有起服务），JSC 执行完顶层代码后 Bun 进程直接退出。

这条路径里和 Node.js 最大的差异在第 1、2 步：Node.js 跑 TypeScript 要么靠 `ts-node`（运行时 transpile，慢），要么靠 `tsc` 预编译（多一步构建），要么靠 `--loader` 钩子（生态碎片化）。Bun 把 transpiler 直接编进二进制，启动时一次性完成模块图构建和语法转换，没有跨进程通信开销。

---

## 四个核心能力的工程用法

### 运行时：直接跑 TypeScript 和 JSX

`node index.js` 在 Bun 里写成 `bun run index.tsx`，TypeScript 和 JSX 开箱即用，不需要 `tsconfig.json`、不需要 `ts-node`、不需要 `--loader`。

```bash
# 运行 TypeScript 文件
bun run index.tsx

# 运行 package.json 中的脚本
bun run start

# REPL
bun
```

内置 Web API 覆盖 `fetch`、`WebSocket`、`Streams`、`Crypto`，以及 Bun 特有的 `Bun.sql`、`Bun.redis`、`Bun.serve`、`Bun.file`。`node:` 模块兼容层覆盖了 `fs`、`path`、`process`、`Buffer`、`events` 等常用模块，但仍有少量缺失——遇到不兼容的包，先查兼容性列表，再决定是 polyfill 还是回退 Node。

一个容易踩的点：Bun 的 transpiler 不做类型检查。`bun run` 会愉快地跑过有类型错误的代码，只要语法能转换。这是有意的工程取舍——类型检查是静态分析，transpile 是语法转换，两件事分开做能让运行时路径更短。代价是类型错误不会在运行时暴露，生产构建前要单独跑 `tsc --noEmit` 或在 CI 里加类型检查步骤。一个可操作的配置是在 `package.json` 的 `prebuild` 脚本里挂 `tsc --noEmit`，让构建前自动检查一次。

### 打包器：Bun.build 与单文件可执行文件

Bun 的打包速度对标 esbuild（官标 1.75x），支持插件系统、代码分割、Tree-shaking、Minifier。配置走 `bun.config.ts`：

```typescript
// bun.config.ts
import { defineConfig } from "@bun/runtime";

export default defineConfig({
  entrypoints: ["./src/index.tsx"],
  outdir: "./dist",
  minify: true,
  target: "browser",
});
```

命令行等价写法：

```bash
bun build --entrypoints ./src/index.tsx --outdir ./dist --minify
```

Bun.build 最有差异性的能力是 `--compile`，把 JS 代码和 Bun 运行时一起打成一个独立的可执行文件：

```bash
bun build --compile --entrypoints ./src/cli.ts --outfile mycli
```

产物是一个不依赖系统 Node.js / Bun 的二进制，适合分发 CLI 工具。这件事在 Node.js 生态里要靠 `pkg` 或 `nexe`，且这两个工具维护活跃度已明显下降。

注意 `--compile` 出来的二进制体积通常在 50-90 MB 量级（包含整个 Bun 运行时），不适合对体积敏感的分发场景。如果目标平台是资源受限的嵌入式设备或要求秒级下载的 CLI 分发，还是要回到 `pkg` + Node.js 的精简方案，或者用 `deno compile` 对比体积。

什么时候选 Bun.build，什么时候继续用 esbuild / Vite？判断标准是「项目其他工具是否也在 Bun 生态内」。如果运行时和测试都已经切到 Bun，打包器一起切能消除一份配置和一份依赖——`bun.config.ts` 和 `bunfig.toml` 共享同一份解析逻辑，构建产物和运行时行为一致。如果项目还在 Node.js 上跑、只是想试 Bun 的打包速度，esbuild / Vite 的生态成熟度（插件、文档、社区案例）仍是更稳的选择，Bun.build 的插件 API 相对年轻，复杂场景的踩坑成本更高。

### 测试运行器：Jest / Vitest 用户零配置迁移

```typescript
// sum.test.ts
import { describe, test, expect } from "bun:test";

function sum(a: number, b: number) {
  return a + b;
}

describe("math", () => {
  test("adds two numbers", () => {
    expect(sum(1, 2)).toBe(3);
  });
});
```

```bash
bun test
```

`bun:test` 的 API 与 Jest 高度相似：`describe`、`test`、`expect`、`beforeEach`、`afterEach`、Mock、Snapshot 都覆盖了。从 Jest 迁移主要改 import 路径（`jest` → `bun:test`）和配置文件（`jest.config.js` → `bunfig.toml`）。Vitest 用户迁移成本更低，因为 Vitest 的 API 本来就借鉴 Jest。

迁移时有三类场景会失败，按出现频率排：第一类是 `jest.mock()` 的 module factory 行为差异——Bun 对 ESM/CJS 混合模块的 mock 注入路径和 Jest 不完全一致，依赖 `jest.mock("node:fs", ...)` 这类核心模块 mock 的测试要逐个验证；第二类是 `jest.useFakeTimers()` 的实现细节——Bun 的 fake timer 不支持 Jest 的 `"modern"` / `"legacy"` 切换，依赖特定行为的测试要重写；第三类是 Snapshot 序列化——Bun 的 Snapshot 格式与 Jest 不完全兼容，迁移时第一次运行会重新生成所有 Snapshot，要人工 review 一次确保格式没漂移。

DOM 测试通过 `bun:test` 的 jsdom 兼容层支持，但这个层不如 Vitest 的 happy-dom 集成成熟，复杂组件测试可能踩坑。如果项目里有大量 React Testing Library 测试，建议先在 Vitest 上跑稳，再评估是否切到 Bun——前端组件测试对 DOM 模拟的依赖度很高，Bun 在这块的兼容性还在迭代。

### 包管理器：npm 兼容，安装路径接近 pnpm

```bash
bun install          # 等价于 npm install
bun add <pkg>        # 等价于 npm install <pkg>
bun add -d <pkg>     # 等价于 npm install -D <pkg>
bun remove <pkg>     # 等价于 npm uninstall <pkg>
bunx cowsay 'Hello!' # 等价于 npx cowsay
bun upgrade          # 升级 bun 自身
```

Bun 的包管理器兼容 npm registry，可以直接读 `package.json` 和 `package-lock.json`（会生成自己的 `bun.lockb` 二进制锁文件）。安装速度比 npm 快，原因是**全局缓存 + 硬链接**：包在全局缓存里只存一份，每个项目的 `node_modules` 通过硬链接指过去，不重复占磁盘。这个思路和 pnpm 一致，区别在于 Bun 用 Zig 重写了下载、解压、链接的全流程，没有 Node.js 进程启动开销。

一个迁移注意点：`bun.lockb` 是二进制格式，不能像 `package-lock.json` 那样直接读 diff。要查依赖变化用 `bun install --dry-run` 或 `bun pm why <pkg>`。如果团队里有人用 npm 有人用 Bun，锁文件冲突会是个问题——建议统一工具链。

什么时候选 Bun install，什么时候保留 pnpm？两者都用全局缓存 + 硬链接，性能差异不大，决策点在「团队是否接受二进制锁文件」和「是否需要 workspace 的高级特性」。pnpm 的 `pnpm-workspace.yaml` 在 monorepo 场景里更成熟，支持 `catalogs`、`overrides` 这类高级依赖管理特性；Bun 的 workspace 支持覆盖了基本场景，但复杂依赖拓扑下的边界行为还在收敛。如果 monorepo 里有跨包依赖覆盖、版本 catalog 这类需求，pnpm 仍是更稳的选择；如果是单包或简单 monorepo，Bun install 的速度收益更直接。

---

## v1.3.14 改了什么（2026-05-13）

v1.3.14 是 2026 年 5 月中旬的稳定版本，11 位贡献者参与。这个版本的看点在「兼容性收尾」——TypeScript 6 对齐和 SQLite 性能优化都是把已有能力做稳，没有开新坑。对评估迁移的团队来说，这种版本比大版本更值得关注：兼容性收敛意味着之前因为边缘语法或性能问题卡住的场景可能解封。主要更新：

- **TypeScript 6 支持**：`--tsconfig` 全面对齐 TypeScript 6 的新语法特性。TypeScript 6 本身还在迭代，部分边缘语法可能仍有兼容问题，遇到问题查 [Bun 的 TypeScript 兼容性文档](https://bun.com/docs/runtime/typescript)。如果项目刚升 TS 6，这个版本是第一个能稳定跑的 Bun 版本。
- **SQLite 性能优化**：`bun:sqlite` 的查询性能进一步提升，主要在 prepared statement 复用路径上。对用 `Bun.sql` 做 embedded 数据库的场景（本地缓存、单机服务）收益直接；对走外部 Postgres / MySQL 的服务无影响。
- **bun build 改进**：支持更多输出格式，包括 ESM/CJS 双格式 bundle。这对发布到 npm 的库有意义——一次构建同时产出 ESM 和 CJS 入口，不用再配 `tsup` 或 `microbundle`。
- **Bug 修复**：涵盖 Windows arm64 兼容性、HTTP/2 流处理等问题。Windows arm64 的修复对 Surface 设备和 ARM 服务器场景是硬需求，HTTP/2 流修复对用 Bun 做 HTTP 反向代理或流式响应的服务是关键修复。

> [完整 Release Notes](https://bun.com/blog/bun-v1.3.14)

---

## 性能数字：测的是什么，不能推出什么

Bun 官方和社区的基准测试数据（因环境而异，仅供参考）：

| 操作 | Node.js | Bun | 倍数 |
|---|---|---|---|
| HTTP Hello World (req/s) | ~25k | ~85k | 3.4x |
| `npm install` (cold) | 15s | 2s | 7.5x |
| TypeScript 编译 (cold) | 8s | 0.8s | 10x |
| `bun test` (Jest 项目迁移) | 12s | 1.5s | 8x |

这些数字各自测的是不同的东西，不能笼统说「Bun 比 Node.js 快 N 倍」：

- **HTTP Hello World** 测的是「最小请求的吞吐上限」，反映的是 HTTP 栈和事件循环的基线开销。真实业务请求带数据库、缓存、序列化，瓶颈不在 HTTP 栈，这个倍数会显著收窄。
- **`npm install` cold** 测的是「冷缓存下的安装耗时」，反映的是下载、解压、链接的全流程。Bun 快的原因是 Zig 实现没有 Node.js 进程启动开销 + 全局缓存命中率高。热缓存下差距会缩小。
- **TypeScript 编译 cold** 测的是「启动到首字节输出」，反映的是 transpiler 启动开销。Bun 不做类型检查，`tsc` 做——这本质上是两个不同的工作，倍数反映的是「跳过类型检查能省多少时间」，而不是「Bun 的 transpiler 比 tsc 快 10 倍」。
- **`bun test` vs Jest** 测的是「测试发现 + 执行 + 报告」全流程。Bun 快的原因是测试运行器和运行时共用进程，没有 Jest 的 worker 进程启动开销。

真实项目里的体感差距通常比这些数字小。但「`npm install` 从 15 秒到 2 秒」这种在 CI 上每天跑几十次的操作，体感差距是实打实的。

这些数字不能推出几件事，迁移决策时要记住：第一，不能从「HTTP Hello World 3.4x」推出「业务接口 3.4x」——业务接口的瓶颈在数据库、缓存、序列化，HTTP 栈占比通常不到 10%；第二，不能从「TypeScript 编译 10x」推出「Bun 的 transpiler 比 tsc 快 10x」——前者跳过了类型检查，后者做了完整类型诊断，测的不是同一件事；第三，不能从「`bun test` 8x」推出「测试套件整体快 8x」——如果测试里有大量 IO（数据库、网络、文件），IO 等待时间不变，整体提速会被稀释。判断自己的项目能拿到多少，最直接的方法是在分支上跑一次 `bun test` 和 `bun run`，对比 CI 耗时——比看任何 benchmark 都准。

---

## 什么时候该用 Bun，什么时候该再等等

### 适合用 Bun 的场景

- **新项目启动**：不需要在 `node` + `esbuild` + `jest` + `npm` 之间来回配置，一个二进制搞定。
- **对启动速度敏感**：CLI 工具、Serverless 函数、脚本类场景，冷启动开销直接进 P99。
- **TypeScript 优先项目**：零配置 TypeScript 支持，省掉 `ts-node` / `swc` / `vite` 的选型决策。
- **需要单文件分发**：`bun build --compile` 输出独立可执行文件，适合 CLI 工具分发。
- **Monorepo**：Bun 的 workspace 支持与 yarn / pnpm 一致，安装速度更快，`bun test` 跨 workspace 跑测试也比 Jest + Nx 配置简单。

### 仍建议用 Node.js 的场景

- **强依赖 Node.js 原生模块**：某些 npm 包内部调用了 V8 特定 API（如 `node-bindings`、部分 native addon、用了 `v8.h` 的包），在 Bun 上跑不起来。迁移前先用 `bun run` 跑一遍现有测试套件，看哪些包报错。
- **需要 Node.js 生态里的企业级中间件**：部分微服务框架、APM agent、Service Mesh sidecar 的 Node.js 集成在 Bun 上的验证还不充分。
- **Windows arm64 生产环境**：Bun 在这块的稳定版支持相对较新，生产环境建议再观察一两个版本。
- **强依赖 Jest 生态**：`jest-styled-components`、`jest-image-snapshot` 这类深度集成 Jest 的包，迁移到 `bun:test` 可能要改 mock 注入方式。

两个列表看似在列场景，背后其实只有一个判断变量：**项目对 Node.js 生态的耦合度有多深**。耦合度低（新项目、标准 API、少量原生依赖）→ Bun 收益直接；耦合度高（企业中间件、native addon、深度 Jest 集成）→ 迁移成本会吃掉速度收益。中间地带的项目，按下面的排查指引做一次试运行，比看文档判断更准。

### 迁移排查指引

从 Node.js 迁移到 Bun，按这个顺序排查：

1. **`bun install` 能否装上依赖**。部分依赖 postinstall 脚本的包（如 `esbuild`、`sharp`）在 Bun 上可能行为不同。报错先看 `bun install --verbose`。
2. **`bun test` 能否跑通现有测试**。Jest 项目直接 `bun test` 通常能跑，但 mock 行为、timer mock、module mock 的实现细节有差异，遇到不通过的测试逐个排查。
3. **`bun run` 能否启动服务**。HTTP 服务、定时任务、队列消费者都跑一遍，观察 `node:` 模块兼容层的报错。
4. **生产环境灰度**。先在非核心服务上跑，观察内存、CPU、错误率。Bun 的内存模型和 Node.js 不同，常驻内存下降是正常的，但 GC 行为差异可能导致长跑服务的内存增长曲线不一样。

---

## 快速安装

```bash
# Linux/macOS（推荐）
curl -fsSL https://bun.sh/install | bash

# Windows
powershell -c "irm bun.sh/install.ps1|iex"

# npm 安装（跨平台）
npm install -g bun

# Homebrew
brew tap oven-sh/bun
brew install bun

# 升级
bun upgrade
```

---

## 常见问题

**Bun 能完全替代 Node.js 吗？** 不能。Bun 覆盖了 Node.js 的大部分常用 API 和主流包，但涉及 V8 内部接口的 native addon、部分企业级中间件、某些边缘 `node:` 模块仍不兼容。一个可操作的判断方法是：如果项目依赖列表里没有 `node-gyp` 构建的包、没有用 `v8.h` 的包、没有深度集成 APM agent，Bun 大概率能跑通；只要踩到这三类之一，就要评估替代方案或回退 Node。生产迁移前必须跑一遍现有测试套件。

**Bun 的 TypeScript 支持和 tsc 一样吗？** 不一样。Bun 只做语法转换，不做类型检查。`bun run` 会跑过有类型错误的代码。类型检查要单独跑 `tsc --noEmit` 或在 IDE 里做。这个差异源于职责不同——tsc 的类型检查是静态分析工具，Bun 的 transpiler 是运行时组件。把类型检查放在 CI 或 pre-commit hook 里，比让运行时承担类型诊断更合理。

**`bun.lockb` 为什么是二进制？** 为了解析速度。二进制格式读取比 JSON 快，但不可读。查依赖变化用 `bun pm why <pkg>` 或 `bun install --dry-run`。如果团队对锁文件可读性有硬性要求（比如要在 code review 里看依赖 diff），可以配 `bun install --save-yaml-lockfile` 生成 `bun.lock` 的 YAML 版本，可读性接近 `package-lock.json`。

**Bun 和 Deno 该选哪个？** 看你对 npm 生态的依赖程度。重度依赖现有 npm 包选 Bun（兼容性更好）；从零开始、想要更干净的权限模型和 TypeScript 优先体验选 Deno。两者都在向对方靠拢——Deno 加了 `npm:` 兼容，Bun 在加强权限模型。一个更具体的判断：如果项目要跑在 Cloudflare Workers / Deno Deploy 这类边缘运行时上，Deno 的权限模型和部署体验更顺；如果要跑在传统 VPS / 容器 / Serverless 函数上，Bun 的 Node.js 兼容性让迁移路径更短。

**Bun 生产环境稳定吗？** v1.3.x 已经被多家公司用于生产（包括 Vercel 部分内部工具、Clerk 等），但稳定不等于零 bug。关键路径服务建议先灰度，观察 1-2 个版本周期再全量切换。灰度时要重点观察三个指标：长跑服务的内存增长曲线（Bun 的 GC 行为和 Node.js 不同）、HTTP 服务的错误率（特别是用了 `Bun.serve` 的流式响应）、`node:` 模块兼容层的边缘 case（某些 API 行为可能和 Node.js 有细微差异）。

---

## 采用顺序建议

1. **个人工具和脚本**：直接用。CLI 工具、自动化脚本、本地开发环境，Bun 的零配置和启动速度收益最大，风险最低。
2. **新项目后端**：可以用。从零开始没有迁移成本，Bun.serve + Bun.sql 的组合适合中小型 API 服务。
3. **现有项目灰度**：先跑测试套件，再灰度非核心服务。观察 1-2 个版本周期。
4. **企业核心系统**：再等等。等 Node.js 兼容性进一步收敛、APM / Service Mesh 集成更成熟后再评估。

四个工具合到一个二进制里，省掉的不只是 npm + esbuild + jest + ts-node 这套配置组合，还有它们之间对不齐的成本。对新项目或个人工具来说，零配置就能跑起来是真实的效率提升，速度收益是附带效果。

v1.3.x 持续迭代、TypeScript 6 支持到位、Bun.build 能力增强——这个 90K Stars 的项目已经越过了「值得关注」的阶段，到了「值得实际试试」的时候。「试试」和「全量切换」之间，隔着完整的测试套件跑通和灰度观察，这两步省不掉。

**官网**：https://bun.com
**文档**：https://bun.com/docs
**GitHub**：https://github.com/oven-sh/bun（90,566 ⭐）

---

🦞 钳岳星君整理 | 2026 年 5 月 16 日
