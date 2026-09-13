---
title: "Bun 拆解：96K Stars 的 all-in-one JavaScript 工具链，如何把运行时、打包器、测试器、包管理器压进一个二进制"
date: "2026-05-16T03:11:38+08:00"
slug: "bun-javascript-runtime-all-in-one-toolkit"
github_repo: "oven-sh/bun"
source_key: "gh:oven-sh/bun"
description: "Bun 把运行时、打包、测试、包管理四件事合并到一个二进制里，改变了 JS 工具链的依赖结构。拆解 JavaScriptCore 选型动机、四合一架构的工程含义、一次 bun run 的完整执行路径，以及与 Node.js / Deno 的真实取舍和迁移风险。2026-09 复核：补入 Anthropic 收购与 Zig→Rust 重写时间线。"
draft: false
categories: ["技术笔记"]
tags: ["JavaScript", "Bun", "Rust", "Node.js", "TypeScript"]
---

# Bun 拆解：96K Stars 的 all-in-one JavaScript 工具链，如何把运行时、打包器、测试器、包管理器压进一个二进制

Bun 把运行时、打包器、测试运行器、包管理器四件事压进同一个二进制。合并的收益不只是少装几个工具：一个典型的 Node.js 项目要同时追 `node` + `esbuild` + `jest` + `npm`（或 pnpm）四套版本和配置，报错栈跨工具、升级节奏对不齐；现在只剩一个版本号要看。代价同样清楚——Node.js 兼容性不是 100%，迁移前得先过一遍自己的代码。

本文以 2026 年 5 月的稳定版 v1.3.14 为基线，2026 年 9 月按官方博客与文档复核。这几个月 Bun 变化不小：2025 年 12 月被 Anthropic 收购，2026 年 7 月宣布用 Rust 重写核心，8 月的 v1.4 起正式以 Rust 交付。时间线在文中相应位置都有标注；性能与兼容性结论以 v1.3.14 时代的一手数据为准，读到时请结合自己拿到的版本判断。

---

## 快速信息卡

| 项目 | 信息 |
|------|----------|
| **Stars** | 约 96K（截至 2026-09） |
| **Forks** | 约 5.0K |
| **许可证** | MIT |
| **归属** | Anthropic（2025-12 收购，保持开源） |
| **实现语言** | Zig → Rust（2026-07 宣布重写，v1.4 起交付） |
| **仓库** | [oven-sh/bun](https://github.com/oven-sh/bun) |

---

## 总览：Bun 把什么压进了一个二进制

Bun 对自己的定义是「all-in-one toolkit for JavaScript and TypeScript apps」，拆开是四个职责。Node.js 生态里这四件事通常由四个独立工具承担，Bun 把它们合并到一个二进制里：

| 职责 | 替代对象 | 关键差异 |
|------|----------|----------|
| 运行时 | Node.js | 引擎换成 JavaScriptCore，冷启动和内存占用更低 |
| 打包器 | esbuild / Webpack / Vite | 内置在二进制里，不需要再装一个 dev 依赖 |
| 测试运行器 | Jest / Vitest | API 与 Jest 高度相似，迁移成本低 |
| 包管理器 | npm / yarn / pnpm | 全局缓存 + 链接复用，安装路径与 pnpm 思路接近 |

少装几个工具是直观收益，真正改变开发体验的是底层实现共享：`bun build` 出来的产物和 `bun run` 跑的代码走同一个 transpiler，`bun test` 和 `bun run` 用同一份模块解析逻辑。Node.js 生态里「esbuild 升级破坏 Jest snapshot」「ts-node 和 Vite 对 TypeScript 配置理解不一致」这类跨工具漂移，在 Bun 里缺乏滋生的土壤。

合并也收走了另一份自由度：工具不可换。esbuild 不合手，Node.js 用户可以换 swc 或 Vite；Bun 的打包器出问题，只能等官方修或在 GitHub 追 issue。单二进制架构的取舍就在这里——四个工具的行为永远对齐，换工具的逃生门没有了。

### 与 Node.js / Deno 的对照

| | Node.js | Deno | Bun |
|---|---|---|---|
| 引擎 | V8 | V8 | JavaScriptCore |
| 实现语言 | C/C++ | Rust | Zig → Rust（v1.4 起） |
| 包管理 | npm（独立工具） | 内置（URL 导入 + npm 兼容） | 内置（npm registry 兼容） |
| TypeScript | 24+ 可直接跑（类型剥离，枚举等语法需 transform-types） | 原生支持 | 原生支持（内置 transpiler） |
| 打包器 | 需单独安装 | 无内置 | 内置 |
| 测试运行器 | node:test 内置；Jest/Vitest 需安装 | 内置 | 内置 |
| Node.js 兼容 | 原生 | Deno 2 起直接支持 package.json / node_modules | `node:` 模块兼容层 |

三者的根本分歧在如何对待 npm 生态。Node.js 就是 npm 生态本身；Deno 早期拒绝 npm，1.x 用 `npm:` 前缀做桥，Deno 2（2024-10）起才直接认 `package.json` 和 `node_modules`；Bun 从第一天就把 npm registry 兼容当产品目标，`package.json` 和 `node_modules` 原样保留。对存量项目，这个差别决定迁移面：Bun 的兼容性以「Node.js 的测试套件能直接跑通」为标尺——v1.4 一次就新增 1,517 项通过的 Node 测试用例，官方称之为 1.0 以来最大的一次兼容性跃进。存量项目迁 Bun，多数时候换掉运行时命令就能开工。

---

## 为什么是 JavaScriptCore，以及代价是什么

Bun 与 Deno 在引擎上分了岔。Deno 用 V8，理由是成熟度、性能上限，加上团队本身有 V8 经验。Bun 选 JavaScriptCore（WebKit 的 JS 引擎），动机指向冷启动和内存。

JSC 的初始化路径比 V8 短。V8 启动要构建 isolate、初始化 JIT 编译器、加载内置库，这套开销在长期运行的服务进程里会被摊薄，但落在 CLI 工具、Serverless 函数、脚本这类「跑一次就退出」的场景里占比很高——Serverless 函数的冷启动延迟直接进用户感知的 P99，CLI 的启动延迟卡在开发者每一次「保存-运行」的循环里。内存同理，JSC 的模型对短生命周期进程更友好，官网基准里 Express Hello World 场景 Bun 常驻 105 MB、Node.js 142 MB。容器和函数计算按内存计费，这个差值直接换算成实例密度和账单。

实现语言这边，JSC 的嵌入接口是 C API，和 Zig 手写的 FFI 正好咬合；V8 的嵌入层是 C++ 抽象，用 Zig 去绑要多一层胶水。Zig 的手动内存管理和 comptime 让编译期检查更多、运行时开销更低。这是 Bun 团队的技术判断，不是行业共识——Deno 给出的答案是 V8 + Rust。

代价在兼容性。`node:` 兼容层覆盖了 `fs`、`path`、`process`、`Buffer` 等常用模块；官方兼容性页面（对照 Node.js v26）目前只有 `node:sea` 完全未实现——官方的建议就是改用 `bun build --compile`。但另有 17 个模块部分支持，几处常踩的语义差异值得记住：

- `async_hooks` 的底层 API（`createHook`、`executionAsyncId` 等）是 stub，async id 恒为 0。依赖它们做调用链追踪的自研逻辑和部分 APM agent 会受影响（`AsyncLocalStorage` 本身可用，走的是另一条实现路径）。
- `node:v8` 的 `serialize` / `deserialize` 用的是 JavaScriptCore 的序列化格式，产物与 V8 不通用，跨运行时交换二进制数据前要先验证。
- `node:tls` 基于 BoringSSL，`renegotiate()` 恒定失败，跨进程会话恢复不可用。
- `node:test` 多数选项抛 `ERR_NOT_IMPLEMENTED`，官方建议直接换 `bun:test`。

官方对兼容性的立场写在页面上：「包在 Node.js 能跑、在 Bun 不能跑，就是 Bun 的 bug」。迁移前先跑一遍现有测试套件，比读文档可靠。

> **时效说明**：本文基线 v1.3.14（2026-05-13），当时运行时核心仍是 Zig。此后官方于 2026-07-08 发布《Rewriting Bun in Rust》，以内存安全为目标把核心从 Zig 迁到 Rust；2026-08-20 的 v1.4 是 Rust 版首个正式发布，公告提到 Claude Code 已在 Rust 移植版上运行数月，空闲 CPU 降低 5 倍、内存最多省 35%。2026-09 复核时最新版为 v1.4.2。若你已在用 v1.4+，文中涉及 Zig 的实现细节应以新版为准；引擎选型、四合一结构、兼容性边界这些架构层面的分析不受重写影响。

---

## 一次 `bun run` 怎么流过系统

假设入口是 `index.tsx`，这条路径展示了 Bun 的四个组件如何协作：

```typescript
// index.tsx
import { Hono } from 'hono'

const app = new Hono()
app.get('/', (c) => c.text('Hello from Bun!'))

export default { port: 3000, fetch: app.fetch }
```

执行 `bun run index.tsx`，路径如下：

**1. 入口解析**。Bun 读取 `index.tsx`，识别出 TypeScript + JSX。这里不调用 `tsc`，也不读 `tsconfig.json` 做类型检查——内置 transpiler 只做语法转换（TS → JS、JSX → `createElement` 调用），不做类型诊断。类型检查交给 IDE 或独立的 `tsc --noEmit`。Bun 启动快，跳过类型检查是原因之一。

**2. 模块图构建**。从 `index.tsx` 出发递归解析 `import`。遇到 `hono`，按 Node.js 模块解析算法查找 `node_modules/hono`，读其 `package.json` 的 `exports` 字段定位入口文件。整个模块图在内存里构建完成，每个模块记录自己的路径、依赖和转换后的代码。

**3. JavaScriptCore 接管**。转换后的代码喂给 JSC：先解释执行，热点代码再 JIT 编译。`Hono` 的 `app.fetch` 被注册为 HTTP 请求处理函数。

**4. 内置 API 接入**。`export default { fetch }` 触发 Bun 的默认行为——启动 `Bun.serve`。底层是 Bun 原生实现的 HTTP 服务器，Linux 上走 io_uring，macOS 上走 kqueue，请求不经过 libuv，直接从内核事件循环进 JSC 回调。

**5. 进程退出**。HTTP 服务器保持运行，进程不退出；脚本类入口（没有起服务）在顶层代码执行完后直接退出。

这条路径与 Node.js 的差异集中在第 1、2 步。Node.js 24 起也能直接跑 TypeScript（默认做类型剥离，枚举、命名空间这类需要转换的语法要开 `--experimental-transform-types`），更早的版本要在 `ts-node`、`tsc` 预编译和各种 loader 钩子之间选，每个方案都多一层配置或多一步构建。Bun 把 transpiler 编进二进制，模块图构建和语法转换在一次进程内完成。

---

## 四个场景的工程用法

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

内置 Web API 覆盖 `fetch`、`WebSocket`、`Streams`、`Crypto`，外加 Bun 特有的 `Bun.serve`、`Bun.file`，以及内置的 SQL 客户端（`import { sql } from "bun"`）和 Redis 客户端（`import { redis } from "bun"`，要求 Redis 服务器 7.2+）。`node:` 兼容层的边界见上一节的清单；遇到不兼容的包，先查 [Bun 的 Node.js 兼容性列表](https://bun.com/docs/runtime/nodejs-compat)，再决定是替换还是回退 Node。

Bun 的 transpiler 不做类型检查，`bun run` 会跑过有类型错误的代码。类型检查是静态分析，语法转换是运行时路径上的活，Bun 把前者完全交给了外部：生产构建前单独跑 `tsc --noEmit`，或在 CI 里加一步。常见做法是挂进 `package.json` 的 `prebuild` 脚本，让构建前自动检查一次。

### 打包器：Bun.build 与单文件可执行文件

Bun 的打包器对标 esbuild，支持插件、代码分割、Tree-shaking 和压缩。配置入口是 `Bun.build()` API（已转正的稳定 API），写在脚本里用 `bun run` 执行：

```typescript
// build.ts —— 用 Bun.build API 配置打包
const result = await Bun.build({
  entrypoints: ["./src/index.tsx"],
  outdir: "./dist",
  minify: true,
  target: "browser",
});

if (!result.success) {
  for (const log of result.logs) {
    console.error(log);
  }
  process.exit(1);
}

console.log(`Build OK: ${result.outputs.length} files`);
```

```bash
bun run build.ts
```

命令行等价写法适合简单场景，不需要可编程配置时直接用：

```bash
bun build --entrypoints ./src/index.tsx --outdir ./dist --minify
```

> 打包配置只有两条入口：`Bun.build()` API 和命令行旗标。`bunfig.toml` 管运行时、安装器和 `bun test` 的行为，不承载打包配置；网上流传的 `bun.config.ts` 写法不是官方 API，不要照搬。

Bun.build 最具差异化的能力是 `--compile`，把 JS 代码和 Bun 运行时一起打成独立可执行文件：

```bash
bun build --compile --entrypoints ./src/cli.ts --outfile mycli
```

产物不依赖目标机器上的 Node.js 或 Bun，适合分发 CLI 工具。这件事在 Node.js 生态里一直缺正规答案：`pkg` 已被 Vercel 归档停止维护，`nexe` 更新缓慢，Node 官方的单文件可执行方案（SEA）多年停在实验性。

注意产物体积在几十 MB 量级（包含整个运行时，随平台和版本浮动），对下载速度敏感的分发场景要先评估。

Bun.build 和 esbuild / Vite 之间怎么选，取决于项目其他工具是否也在 Bun 生态内。运行时和测试都已切到 Bun，打包器一起切能消掉一份配置和一份依赖——构建产物和运行时行为天然一致。项目还在 Node.js 上跑、只是想借打包速度，esbuild / Vite 的插件生态和社区案例仍是更稳的选择，Bun.build 的插件 API 相对年轻，复杂场景的踩坑成本更高。

### 测试运行器：Jest / Vitest 用户低成本迁移

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

`bun:test` 的 API 面向 Jest 兼容设计：`describe`、`test`、`expect`、`beforeEach`、Mock、Snapshot 都有对应物。从 Jest 迁移主要改 import 路径（`jest` → `bun:test`）；Vitest 本身借鉴 Jest，迁移更省事。

有三类场景要在迁移时逐个验证：一是 `jest.mock()` 对 ESM/CJS 混合模块的注入路径与 Jest 不完全一致，核心模块 mock（如 `jest.mock("node:fs", ...)`）的测试要过一遍；二是 fake timer 的实现细节有差异，依赖 Jest 特定行为的测试可能要改写；三是 Snapshot 的序列化格式与 Jest 不通用，首次运行会重新生成全部快照，要人工 review 确认没有语义漂移。

DOM 测试没有内置环境，靠第三方库配合：官方文档列出的兼容对象是 HappyDOM、DOM Testing Library 和 React Testing Library，通过 `--preload` 挂载环境。这条路线能跑通，但成熟度不及 Vitest 生态的默认体验；重前端组件测试的项目建议先在 Vitest 上跑稳，再评估是否值得切。

### 包管理器：npm 兼容，安装路径接近 pnpm

```bash
bun install          # 等价于 npm install
bun add <pkg>        # 等价于 npm install <pkg>
bun add -d <pkg>     # 等价于 npm install -D <pkg>
bun remove <pkg>     # 等价于 npm uninstall <pkg>
bunx cowsay 'Hello!' # 等价于 npx cowsay
bun upgrade          # 升级 bun 自身
```

Bun 的包管理器兼容 npm registry，从 `package.json` 出发解析依赖；项目里已有 `package-lock.json`（lockfileVersion 2/3/4）、yarn.lock v1 或 pnpm-lock.yaml 时，首次 `bun install` 会自动迁移成自己的锁文件。默认锁文件自 v1.2 起是文本格式的 `bun.lock`，能直接 diff、能进 code review；旧版的二进制 `bun.lockb` 已退居遗留格式，官方迁移命令是 `bun install --save-text-lockfile --frozen-lockfile --lockfile-only`，跑完手动删掉旧文件即可。

安装快的原因是全局缓存加内容寻址的链接：包在全局缓存里只存一份，项目的 `node_modules` 里放指向它的链接（macOS 走 clonefile，Linux 是硬链接），不重复占磁盘。思路与 pnpm 一致，区别在下载、解压、链接的全流程都是原生代码，没有 Node.js 进程的启动开销。官网标称对 npm「最多快 30 倍」，冷缓存首装的对比样本是 1.41 秒对 18.12 秒。

团队协作只有一条要约定：锁文件统一由 Bun 生成并提交，别让 npm 和 Bun 同时管依赖——两个工具会各自维护自己的锁文件和 `node_modules` 布局，产生无意义的 churn。

Bun install 和 pnpm 之间怎么取舍，看团队对 workspace 特性的需求。两者都用全局缓存加链接复用，纯速度差距不大。pnpm 的 `pnpm-workspace.yaml` 在 monorepo 场景更成熟，支持 `catalogs`、`overrides` 这类高级依赖管理；Bun 的 workspace 覆盖基本场景，复杂依赖拓扑下的边界行为还在收敛。monorepo 里有跨包版本统一、依赖覆盖需求的，pnpm 仍是更稳的选择；单包或简单 monorepo，Bun install 的速度和低配置更舒服。

---

## v1.3.14 改了什么（2026-05-13）

v1.3.14 是 2026 年 5 月中旬的稳定版本，把 Bun 从「更快的 Node.js」往「自带基础设施的运行时」推了一步，主要更新集中在图像处理、安装链路和 HTTP 现代协议：

- **Bun.Image：内置图像处理**。本版本最大的新能力，做的是 Node.js 生态里要靠 `sharp`（原生 C++ 模块，装一次就要 node-gyp 编译环境）才能做的活。JPEG、PNG、WebP、GIF、BMP 的编解码内置且全平台一致；HEIC、AVIF、TIFF 在 macOS / Windows 上走系统后端。API 是链式的，`.resize()` → `.rotate()` → `.webp()` 一路接下去，实例可以直接当 `Response` body 返回，由运行时补上 `Content-Type`。官方 benchmark（对比 sharp 0.34.5，linux/x64）：读取元数据 `metadata()` 快约 70 倍，常见 resize 快 1.2 到 1.4 倍；除 `metadata()` 外处理都在主线程之外执行。省掉 `sharp` 意味着 CI 不再为一个缩略图场景装 libvips，也没有原生二进制与架构不匹配的报错。
- **全局虚拟存储（Global Virtual Store）**。`bun install` 的 isolated linker 新增 `install.globalStore = true`：每个包只在全局缓存中实例化一次，项目 `node_modules` 里放指向它的 symlink。官方用约 1,400 个包的前端项目做预热安装测试（Apple Silicon，hyperfine `--warmup 3 --runs 10`）：优化前约 841 ms、clonefile 调用 1,387 次，开启后约 115 ms、0 次——快了约 7 倍，受益最大的是 CI 反复重建依赖的路径。注意这是实验特性，默认关闭，且只有来自不可变缓存源的包才有资格进全局存储。
- **Bun.serve 支持 HTTP/3（QUIC）**。加一个 `http3: true` 就能同一端口同时监听 TCP（HTTP/1.1 + 2）和 UDP（HTTP/3），底层是 lsquic（C 语言实现的 QUIC 协议栈）。官方基准（Linux x64 单进程 loopback）里静态路由吞吐 509,135 req/s，对比 HTTPS/1.1 的 189,130 和 HTTP/1.1 的 239,476；代价是约一半 CPU 时间花在 lsquic 内部，且不支持 WebSocket over HTTP/3、0-RTT 被禁用。官方标为高度实验性，明确警告别上生产。
- **fetch() 的 HTTP/2 / HTTP/3 客户端（实验）**。按请求指定 `{ protocol: "http2" | "http3" }`，同 origin 的并发请求可共享多路复用连接；HTTP/3 客户端能按 `Alt-Svc` 头自动升级到 QUIC，但要靠 `--experimental-http3-fetch` 或对应环境变量显式打开，同为高度实验性。
- **重写的 `fs.watch` 后端**。Linux / macOS / FreeBSD 上直接对接 inotify、FSEvents、kqueue，修了递归监听漏掉新增目录、文件删除重建后不再触发 `change` 等问题。
- **`--no-orphans`**。父进程死掉（哪怕被 SIGKILL）时 Bun 自动退出，并递归终止自己派生的所有子进程（Linux 走 prctl，macOS 走 kqueue；Windows 上是空操作），适合被 Electron、CI runner 这类 supervisor 拉起、中途强杀的场景。

其他值得一提的：JavaScriptCore 合入上游 565 个提交；ESM 模块加载快约 12%；FreeBSD 和 Android 首次有官方一方原生构建。

> [完整 Release Notes](https://bun.com/blog/bun-v1.3.14)

---

## 性能数字：测的是什么，不能推出什么

先交代出处：下面的数字取自官网基准（Linux x64，3 次取中位数），换机器、换负载都会变，当作数量级看：

| 操作 | Node.js | Bun | 倍数 | 测的是什么 |
|---|---|---|---|---|
| Express Hello World HTTPS 吞吐 | 25,181 req/s | 48,243 req/s | 1.9x | HTTP 栈与事件循环的基线开销 |
| 常驻内存（同场景） | 142 MB | 105 MB | — | 运行时基线内存 |
| 首次安装（冷缓存） | 18.12s | 1.41s | ~13x | 下载、解压、链接全流程 |
| Next.js 应用安装（热缓存） | 4.45s | 0.21s | ~21x | 缓存命中后的链接与布局 |

这些数字测的是不同的东西，不能笼统说「Bun 比 Node.js 快 N 倍」：

- **HTTPS 吞吐**测的是最小请求的极限，反映 HTTP 栈和事件循环的基线开销。真实业务请求带着数据库、缓存、序列化，瓶颈多半不在 HTTP 栈，这个 1.9 倍到业务接口上会收窄很多。
- **首次安装**测的是包管理全流程，快在缓存设计和原生实现。CI 上每天跑几十次的操作，十几倍的差距是实实在在的体感；热缓存下倍数更高，但绝对时长本来就在一秒以内。
- **常驻内存**的差值在按内存计费的容器环境直接换算成实例密度，不过基线内存低不代表长跑服务的内存曲线低——GC 行为差异要单独观察。

从这些数字不能推出的东西，迁移决策时尤其要记住：不能从「Hello World 1.9x」推出「业务接口 1.9x」；不能从冷缓存安装的倍数推出热缓存也能省同样多的时间（绝对值已经很小）；也不能拿官网的极致场景当自己的负载。判断自己的项目能拿到多少，在分支上跑一次 `bun install` 和 `bun test` 对比 CI 耗时，比看任何 benchmark 都准。

---

## 什么时候该用 Bun，什么时候该再等等

### 适合用 Bun 的场景

- **新项目启动**：不需要在 `node` + `esbuild` + `jest` + `npm` 之间来回配置，一个二进制搞定。
- **对启动速度敏感**：CLI 工具、Serverless 函数、脚本类场景，冷启动开销直接进 P99。
- **TypeScript 优先项目**：零配置 TypeScript 支持，省掉 transpiler 选型。
- **需要单文件分发**：`bun build --compile` 输出独立可执行文件，适合 CLI 工具分发。
- **Monorepo**：workspace 支持加全局缓存安装，v1.4 起还有 `bun test --parallel` 和 `--shard`，跨包跑测试比 Jest + Nx 的配置省事。

### 仍建议用 Node.js 的场景

- **深度依赖 `async_hooks` 底层语义的服务**：`createHook` 等底层 API 在 Bun 里仍是 stub，自研调用链追踪和部分 APM agent 会受影响。
- **依赖特定 `node:` 模块完整语义**：`node:v8` 序列化格式不通用、`node:tls` 的 `renegotiate()` 不可用，涉及跨运行时数据交换或连接重协商时要先验证。
- **Windows ARM64 生产环境**：原生支持 v1.4（2026-08）才补上，生产部署建议再观察一两个版本。
- **强依赖 Jest 深度集成的生态**：`jest-styled-components`、`jest-image-snapshot` 这类包，迁移到 `bun:test` 要动 mock 方式。

两份清单背后是同一个变量：**项目对 Node.js 生态的耦合深度**。耦合浅，Bun 的收益拿得直接；耦合深，迁移成本会吃掉速度收益。中间地带的项目，按下面的顺序做一次试运行，比看任何文档都准。

### 迁移排查指引

从 Node.js 迁移到 Bun，按这个顺序排查：

1. **`bun install` 能否装上依赖**。Bun 默认只给 `package.json` 里 `trustedDependencies` 白名单中的包执行生命周期脚本，依赖 postinstall 的包（如 `esbuild`、`sharp`）行为可能不同；报错先看 `bun install --verbose`。
2. **`bun test` 能否跑通现有测试**。Jest 项目直接 `bun test` 通常能跑，但 mock 注入、fake timer、snapshot 的实现细节有差异，不通过的测试逐个排查。
3. **`bun run` 能否启动服务**。HTTP 服务、定时任务、队列消费者都跑一遍，观察 `node:` 兼容层的报错。
4. **生产环境灰度**。先在非核心服务上跑，观察内存、CPU、错误率。Bun 的 GC 行为和 Node.js 不同，长跑服务的内存增长曲线要单独看。

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

# Docker
docker pull oven/bun

# 升级
bun upgrade
```

---

## 常见问题

**Bun 能完全替代 Node.js 吗？** 接近，但不是。官方兼容页（对照 Node.js v26）上完全未实现的只剩 `node:sea`，可部分实现的 17 个模块里有真实的语义差异（上文列过 `async_hooks`、`node:v8`、`node:tls`）。经验判断：依赖树里没有直接摸 V8 内部的包、没有自研的 hooks 追踪逻辑、没有深度集成的 APM，Bun 大概率能直接跑通；踩到其中任何一类，先做替代方案评估再动。生产迁移前跑一遍现有测试套件，这条没有捷径。

**Bun 的 TypeScript 支持和 tsc 一样吗？** 不一样。Bun 只做语法转换，不做类型检查，`bun run` 会跑过有类型错误的代码。tsc 的类型检查是静态分析工具，Bun 的 transpiler 是运行时组件，职责不同。类型检查放进 CI 或 pre-commit hook，比让运行时承担更合理。

**锁文件还是二进制的吗？** 不是了。v1.2 起默认锁文件是文本格式的 `bun.lock`，能直接 diff、能进 code review；`bun.lockb` 是遗留格式，官方迁移命令 `bun install --save-text-lockfile --frozen-lockfile --lockfile-only`。查某个依赖为什么被装进来，用 `bun why <pkg>`（支持通配符，`--top` 只看顶层）。

**Bun 和 Deno 该选哪个？** 看两件事：现有依赖和目标平台。存量 npm 项目、想以最小改动换性能，选 Bun——兼容性是它的产品目标，迁移往往就是换掉运行时命令。从零开始、在意权限模型，选 Deno；Deno 2 起也能直接用 `package.json` 和 `node_modules`，但它对 npm 生态的整合仍是桥接姿态。部署目标上：跑在 Deno Deploy 上自然选 Deno；Cloudflare Workers 用的是自家 workerd 运行时，和这个选型无关。

**Bun 生产环境稳定吗？** 有几条可核实的信号：Anthropic 把 Claude Code 建在 Bun 上——官网原话是「Claude Code is a single file with Bun inside it」，1.4 公告还提到 Claude Code 已在 Rust 移植版上跑了数月；Midjourney 的图片通知走 Bun 的 WebSocket 服务；Railway 的 serverless Functions 建在 Bun 上。灰度建议不变：非核心服务先行，重点观察长跑内存曲线、流式响应错误率、`node:` 兼容层的边缘行为，各看 1-2 个版本周期再全量。

---

## 采用顺序建议

1. **个人工具和脚本**：直接用。CLI 工具、自动化脚本、本地开发环境，收益最大，风险最低。
2. **新项目后端**：可以用。从零开始没有迁移成本，`Bun.serve` 加内置 SQL / Redis 客户端能省掉一截依赖。
3. **现有项目灰度**：先跑测试套件，再灰度非核心服务。已在 1.4+ 的注意这是 Rust 重写后的首发系列，等 1.4.x 小版本收敛几个再全量。
4. **企业核心系统**：再等等。APM / Service Mesh 集成的验证面大，`async_hooks` 语义差异需要逐项确认，等兼容性进一步收敛后再评估。

落地时按这个清单逐项打勾：

- [ ] 在一个非核心脚本上跑通 `bun run`，确认 transpiler 行为符合预期
- [ ] 现有测试套件用 `bun test` 跑一遍，记录失败的测试和原因
- [ ] `bun install` 装一遍依赖，对比锁文件的依赖树差异
- [ ] 选一个非核心服务灰度，监控内存、CPU、错误率 1-2 个版本周期
- [ ] 在 `package.json` 的 `prebuild` 里挂 `tsc --noEmit`，补上类型检查
- [ ] 对照 `node:` 兼容层清单，列出需要替换或回退的包
- [ ] 约定锁文件策略：统一由 Bun 生成并提交

**官网**：https://bun.com
**文档**：https://bun.com/docs
**GitHub**：https://github.com/oven-sh/bun（96K+ ⭐）

钳岳星君整理 | 2026 年 5 月 16 日
