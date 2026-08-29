---
title: "Bun：让你可以放弃 npm/yarn/vite/jest 的 JavaScript 运行时"
date: "2026-05-16T15:10:00+08:00"
slug: "bun-javascript-runtime-all-in-one"
github_repo: "oven-sh/bun"
description: "Bun 是用 Zig 编写的高性能 JavaScript 运行时、bundler、测试框架和包管理器。本文从核心概念、安装配置、运行时、包管理、打包、测试、框架集成六个维度，对这个 2021 年起步、如今已全面生产可用的项目做完整技术解读。"
draft: false
categories: ["技术笔记"]
tags: ["Bun", "JavaScript", "TypeScript", "测试框架", "Zig", "Node.js", "性能优化"]
---

# Bun：让你可以放弃 npm/yarn/vite/jest 的 JavaScript 运行时

2021 年起步的 Bun，到 2024 年起进入多家头部公司的生产环境，早已不是"值得关注的实验品"。它把运行时、bundler、测试框架和包管理器收进一个可执行文件，工程界也因此开始重算前端与后端工具链的搭建方式。Bun 迭代很快，本文写于 2026 年 5 月，涉及的具体版本号以 [官方发布页](https://github.com/oven-sh/bun/releases) 为准。

Bun 是一个可执行文件，同时是运行时、bundler、测试框架和包管理器。你不再需要 node + npm + vite + jest，只需要 `bun`。

本文从运行时、包管理、打包、测试、框架集成五个维度，对 Bun 做一次系统性的技术解读，并在结尾给出适用场景与采用顺序建议。

## 目录

- [什么是 Bun：定位与技术栈](#什么是-bun定位与技术栈)
- [安装与快速开始](#安装与快速开始)
- [运行时：Node.js 的直接替代品](#运行时nodejs-的直接替代品)
- [包管理器：与 npm/yarn/pnpm 的性能对比](#包管理器与-npmyarnpnpm-的性能对比)
- [打包工具：Bun.build](#打包工具bunbuild)
- [测试框架：Jest 兼容的测试运行器](#测试框架jest-兼容的测试运行器)
- [框架与工具链集成](#框架与工具链集成)
- [配置文件：bunfig.toml](#配置文件bunfigtoml)
- [性能基准：测的是什么，不能说明什么](#性能基准测的是什么不能说明什么)
- [已知限制](#已知限制)
- [FAQ：常见问题与错误排查](#faq常见问题与错误排查)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [适用场景与采用顺序](#适用场景与采用顺序)

## 学习目标

完成本文阅读和动手实践后，你应该能：

- 说清 Bun 与 Node.js 在引擎、事件循环、模块系统上的核心差异，判断这些差异对你的项目意味着什么。
- 在本地装好 Bun，用它跑 TypeScript 文件、装依赖、跑测试、打包产物，替换掉至少两个现有工具。
- 识别 Bun 的内置 API（`Bun.serve`、`Bun.SQL`、`bun:sqlite` 等）的适用场景，以及哪些场景仍需第三方库。
- 根据项目类型（新项目、迁移现有 Node.js 项目、CI 加速）选择合适的采用策略。

## 什么是 Bun：定位与技术栈

Bun 是一个用 **Zig** 编写、底层基于 **JavaScriptCore**（WebKit 引擎，与 Node.js 使用的 V8 不同）的 JavaScript 运行时。它的设计目标是成为 Node.js 的**直接替代品**，同时内置打包、测试和包管理功能。

三个差异让 Bun 与众不同：

**第一，启动速度和内存占用远低于 Node.js。** JavaScriptCore 比 V8 轻量，加上 Zig 的系统级控制，Bun 的冷启动时间通常是 Node.js 的 1/4 到 1/10。这对 CLI 工具和 Serverless 场景尤其重要。

**第二，所有工具共用一个进程。** 不需要为 npm 创建一个进程，再为 vite 创建另一个进程。包解析、文件监听、HTTP 服务都在同一个可执行文件里，省掉了进程间通信的开销。

**第三，Node.js 兼容性开箱即用。** 大部分 npm 包不需要修改即可在 Bun 上运行，包括 Express、Fastify、Prisma、Next.js 等主流框架。

技术栈概览：

| 层级 | 技术选型 |
|------|---------|
| 语言 | Zig |
| 引擎 | JavaScriptCore（WebKit） |
| 包管理器 | 自研，与 npm 完全兼容 |
| 构建工具 | 自研，打包速度对标 esbuild |
| 测试框架 | 自研，与 Jest API 高度兼容 |
| 系统 | macOS（x64 + Apple Silicon）、Linux（x64 + arm64）、Windows |

## 安装与快速开始

### 安装方式

```sh
# 方式一：官方安装脚本（推荐）
curl -fsSL https://bun.sh/install | bash

# 方式二：npm 全局安装
npm install -g bun

# 方式三：Homebrew（macOS）
brew tap oven-sh/bun
brew install bun

# 方式四：Docker
docker pull oven/bun
docker run --rm --init --ulimit memlock=-1:-1 oven/bun

# 升级
bun upgrade
# 尝鲜版（每次 main 分支提交自动构建）
bun upgrade --canary
```

版本号变化很快，具体值以官方发布页为准；安装后可用 `bun --version` 确认本机版本。

### 快速上手

```sh
# 运行 TypeScript/JSX 文件，无需任何配置
bun run index.tsx

# 运行 package.json 中的脚本
bun run start

# 安装依赖
bun install

# 执行一个包（类似 npx）
bunx cowsay 'Hello, world!'

# 运行测试
bun test
```

## 运行时：Node.js 的直接替代品

### 基本用法

```typescript
// index.ts - TypeScript 和 JSX 开箱即用，不需要 tsconfig.json
import { Hono } from 'hono'

const app = new Hono()

app.get('/', (c) => c.text('Hello from Bun!'))

export default {
  port: 3000,
  fetch: app.fetch,
}
```

```bash
bun run index.ts
# 启动速度比 node + ts-node 快 10 倍以上
```

### Bun.serve — 原生 HTTP 服务器

Bun 不需要 Express 或 Fastify 就能创建高性能 HTTP 服务器：

```typescript
const server = Bun.serve({
  port: 3000,
  fetch(req) {
    const url = new URL(req.url)
    if (url.pathname === '/api/users') {
      return Response.json([{ id: 1, name: 'Alice' }])
    }
    return new Response('Not Found', { status: 404 })
  },
})

console.log(`Listening on http://localhost:${server.port}`)
```

`Bun.serve` 底层的事件循环实现是平台相关的：在 Linux 上基于 io_uring，在 macOS 上基于 kqueue，在 Windows 上基于 IOCP。这种平台特化让它在各平台都能用上尽可能优的异步 I/O 接口。在同等硬件下，Bun HTTP 服务器的吞吐量通常明显高于 Node.js + Express 组合，但差距有多大取决于路由与业务逻辑的复杂程度，别拿 Hello World 的数字去推生产负载。

### Bun.serve 进阶：声明式路由与服务器选项

手写 `fetch` 里一串 `if (req.url)` 很快会失控。`Bun.serve` 支持对象形式的 `routes`，把路径、方法和处理器写在一起，类型也能被自动推导：

```typescript
const server = Bun.serve({
  port: 3000,
  development: true,          // 开发模式：开启 HMR 相关特性
  idleTimeout: 10,            // 空闲连接断开时间（秒），0 表示不限制
  onError(error) {
    console.error(error)
    return new Response('Something went wrong', { status: 500 })
  },
  routes: {
    // 静态路由
    '/': () => new Response('home'),
    // 路径参数，自动注入到回调
    '/users/:id': (req) => {
      const id = req.params.id
      return Response.json({ id })
    },
    // 按方法区分
    '/api/users': {
      GET: () => Response.json([{ id: 1 }]),
      POST: async (req) => Response.json({ created: true }, { status: 201 }),
    },
  },
})
```

几个值得留意的选项：

- `development: true` 会在响应里带上带源码位置的错误页，适合本地调试；生产环境记得关掉。
- `idleTimeout` 对长连接、WebSocket 场景要按需调整，默认行为以[官方 `serve` 文档](https://bun.sh/docs/api/http)为准。
- `onError` 统一兜底未捕获异常，配合日志中间件能收敛线上错误面。
- 相对路径可配 `static` 托管静态资源、`fetch` 兜底其余请求，几个处理器可以同时存在。

### Web API 全覆盖

Bun 原生实现了大量 Web API，不需要 polyfill：

```typescript
// Blob, File, FormData, URL, URLSearchParams
const formData = new FormData()
formData.append('name', 'Alice')
formData.append('avatar', new Blob(['fake'], { type: 'image/png' }))

// WebSocket
const ws = new WebSocket('wss://echo.example.com')
ws.addEventListener('message', (e) => console.log(e.data))

// Streams（ReadableStream, TransformStream, etc.）
const stream = new ReadableStream({
  start(controller) {
    controller.enqueue('Hello')
    controller.close()
  }
})

// SubtleCrypto（Web Crypto API）
const hash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('hello'))
```

### Node.js 兼容性

Bun 实现了 `node:` 模块前缀的兼容层：

```typescript
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { EventEmitter } from 'node:events'
```

对于没有完全兼容的包，可以查看 [Bun 的 Node.js 兼容性列表](https://bun.sh/docs/runtime/nodejs-apis)，大多数主流包都已覆盖。

### 内置 API：Bun.*

Bun 在全局对象上提供了一组高性能原生 API。下表列出的是官方文档确认存在的 API（截至 1.3.x），具体用法以 [bun.sh/docs](https://bun.sh/docs/runtime/bun-apis) 官方文档为准。

```typescript
// 文件 I/O（比 node:fs 快）
const file = Bun.file('package.json')
const content = await file.text()

// SQLite（内置，无需安装 better-sqlite3）
import { Database } from 'bun:sqlite'
const db = new Database('app.db')
const rows = db.query('SELECT * FROM users').all()

// 统一 SQL 客户端（Bun.SQL，支持 PostgreSQL/MySQL/SQLite）
import { sql, SQL } from 'bun'
const pg = new SQL('postgres://user:pass@localhost/db')
const users = await sql`SELECT * FROM users WHERE active = ${true}`

// Redis 客户端（内置，Bun 1.3+）
import { redis } from 'bun'
await redis.set('greeting', 'Hello from Bun!')
const greeting = await redis.get('greeting')

// S3 / R2 对象存储客户端（内置，Bun 1.2+，支持 AWS S3、R2、MinIO 等）
import { S3Client } from 'bun'
const s3 = new S3Client({ bucket: 'my-bucket' })
await s3.file('data.json').write(JSON.stringify({ ok: true }))
// const data = await s3.file('data.json').json()

// Cron 定时任务
// Bun.cron('*/5 * * * *', () => {
//   console.log('Runs every 5 minutes')
// })

// 无头浏览器（Bun.WebView，macOS，实验性）
// import { WebView } from 'bun'
```

几点说明：

- `Bun.SQL` 是从 `bun` 包导出的大写 `SQL`/`sql`（不是 `bun:sql` 模块）。它用标记模板字面量执行查询，`${}` 占位符会被自动参数化，防 SQL 注入。Bun 1.3 起用同一套 API 覆盖 PostgreSQL、MySQL、MariaDB、SQLite 四种数据库；PostgreSQL 客户端更早在 1.2 就可用。注意它只能以标记模板方式调用，当普通函数调用会抛错。
- `bun:sqlite` 是独立模块，API 更接近 `better-sqlite3` 的同步风格（`.query(...).all()`），`Bun.SQL` 返回 Promise，风格更现代。两者 SQLite 能力有重叠，按项目习惯二选一。
- `Bun.S3`（`S3Client` / `s3`，Bun 1.2+）是内置的 S3 兼容对象存储客户端，可用于 AWS S3、Cloudflare R2、DigitalOcean Spaces、MinIO 等，无需引入 `@aws-sdk`。
- `Bun.redis`（Bun 1.3+）是内置 Redis 客户端，覆盖常用命令；Bun 官方基准称其明显快于 `ioredis`，但集群、流和 Lua 脚本仍待后续版本补齐。
- `Bun.cron`、`Bun.WebView`（macOS）等较新 API 仍在演进，使用前以 [官方文档](https://bun.sh/docs/runtime/bun-apis) 为准。

### Bun.shell：把 Shell 脚本写进 JavaScript

`Bun.shell`（从 `bun` 导出为 `$`）帮你用标记模板把命令拼成可调用的脚本，环境变量、错误处理和并发都能直接写在一起：

```typescript
import { $ } from 'bun'

// 逐字执行命令，捕获输出
const result = await $`echo hello`
console.log(result.stdout.toString()) // "hello"

// 临时变量会做转义，命令行注入风险低
const name = 'bob'
await $`echo ${name}`

// 命令输出与变量互换
const files = (await $`ls`).stdout.toString().trim().split('\n')

// 出错即抛异常，可用 try/catch 拦截
try {
  await $`exit 1`
} catch (err) {
  console.error('命令失败', err)
}

// Promise.all 并发执行，适合批量任务
await Promise.all([
  $`git pull`,
  $`bun install`,
])
```

在 Node.js 生态里做类似的事通常要 `execSync`/`spawn` 加一堆引号处理与转义；`Bun.shell` 把这些收进模板字面量，输出会从原生文件描述符直接流式出来，不会像 `child_process` 那样默认缓冲全部内存。写脚本、做适配器、跑批量任务的场景很顺手。

### 子进程与文件 I/O

`Bun.spawn` 提供了比 `node:child_process` 更直白的子进程接口，配合 `Bun.file` / `Bun.write` 做文件读写：

```typescript
import { spawn } from 'bun'

// 起一个子进程，拿到 stdout 给 Bun.file 用
const child = spawn(['echo', 'hello'], { stdout: 'pipe' })
const out = await new Response(child.stdout).text() // "hello"

// 直写文件，不必先 Buffer
await Bun.write('out.txt', 'hello world')
const file = Bun.file('out.txt')
console.log(await file.text()) // "hello world"
```

## 包管理器：与 npm/yarn/pnpm 的性能对比

### 核心命令

```bash
bun install              # 安装 package.json 中的依赖
bun add <pkg>           # 添加依赖（等同于 npm install <pkg>）
bun add -d <pkg>        # 添加 devDependency
bun remove <pkg>        # 移除依赖
bun update <pkg>        # 更新依赖
bun outdated           # 检查过时依赖
bun audit              # 安全审计
bun why <pkg>           # 解释为什么某个包被安装
bun info <pkg>         # 查看包信息
bun pm                  # 包管理器子命令（清理缓存、查看全局缓存等）
```

### 速度对比

Bun 的包管理器用 Zig 重写，安装速度比 npm 快 **5-20 倍**，比 pnpm 快 **2-5 倍**。原因：

1. **并行下载**：同时下载多个文件
2. **全局缓存**：已下载的包永不重复下载
3. **锁文件优化**：`bun.lockb` 格式支持增量更新
4. **跳过元数据解析**：直接读取 npm registry 的 tarball URL

### Workspaces 支持

```json
// package.json
{
  "workspaces": ["packages/*"]
}
```

Bun 的 workspace 支持与 yarn/pnpm 相同，但安装速度更快。

### 私有注册表

```bash
# 在 .npmrc 中配置
@myorg:registry=https://npm.myorg.com/
//npm.myorg.com/:_authToken=MY_TOKEN
```

Bun 的 `.npmrc` 解析与 npm 完全兼容，支持作用域注册表、认证令牌、环境变量替换。

## 打包工具：Bun.build

Bun 内置的打包器（bundler）速度对标 esbuild，功能覆盖 Vite 的大部分场景：

```typescript
import { build } from 'bun'

await build({
  entrypoints: ['src/index.tsx'],
  outdir: './dist',
  minify: process.env.NODE_ENV === 'production',
  target: 'browser',
  format: 'esm',
  splitting: true,       // 代码分割
  sourcemap: 'linked',   // 源码映射
  loader: {
    '.tsx': 'tsx',
    '.ts': 'ts',
    '.css': 'css',
    '.png': 'file',
  },
})
```

### 插件系统

```typescript
import { build } from 'bun'

await build({
  entrypoints: ['src/index.ts'],
  outdir: './dist',
  plugins: [
    {
      name: 'my-plugin',
      setup(build) {
        build.onLoad({ filter: /\.custom$/ }, ({ path }) => {
          return { exports: ['default'], contents: `export default "${path}"` }
        })
      }
    }
  ]
})
```

### 单文件可执行文件

```bash
bun build --compile --outfile myapp src/index.ts
# 输出一个 ~50MB 的独立可执行文件，不需要 Node.js 或任何运行时
```

### 热模块替换（HMR）

Bun 的打包器内置 HMR 支持：

```typescript
// 配合 Bun.serve 的 watch 模式
bun --watch index.tsx
```

### 与 Vite 的关系

Bun 的打包器定位与 Vite 不同——它更轻量，插件生态也更小。如果你的项目依赖 Vite 特有的插件体系，可以继续用 Vite，同时用 `bun install` 加速依赖安装。如果你的项目比较简单，直接用 `Bun.build` 可以省掉整个 Vite 工具链。

## 测试框架：Jest 兼容的测试运行器

### 基本用法

```typescript
import { describe, test, expect, beforeAll } from 'bun:test'

describe('Math utils', () => {
  beforeAll(() => {
    // setup
  })

  test('adds numbers', () => {
    expect(1 + 2).toBe(3)
  })

  test('arrays match', () => {
    expect([1, 2, 3]).toEqual([1, 2, 3])
  })
})
```

```bash
bun test
# 支持 watch 模式
bun test --watch
```

### Jest 迁移

Bun 的测试 API 与 Jest 高度兼容，大多数 Jest 测试**无需修改**即可在 Bun 上运行：

```typescript
// Jest 风格（直接兼容）
expect(spy).toHaveBeenCalled()
expect(fn).toThrow()
expect(value).toBeTruthy()

// Bun 特有的 DOM 测试（配合 happy-dom）
import { describe, test, expect } from 'bun:test'
import { Window } from 'happy-dom'

test('button click', () => {
  const window = new Window()
  document = window.document
  document.body.innerHTML = '<button id="btn">Click</button>'
  
  document.getElementById('btn')?.click()
  // ...
})
```

### Mock 函数

```typescript
import { test, expect, fn, mock } from 'bun:test'

test('mocks a function', () => {
  const consoleLog = mock((msg: string) => msg)
  console.log('hello')
  expect(consoleLog).toHaveBeenCalledWith('hello')
})
```

### 覆盖率报告

```bash
bun test --coverage
# 生成覆盖率报告，输出到 stdout 和 coverage/ 目录
```

### 快照测试

```typescript
import { test, expect } from 'bun:test'

test('snapshot', () => {
  expect({ foo: 'bar' }).toMatchSnapshot()
})
```

### 与 Jest 的对比

| 特性 | Bun test | Jest |
|------|---------|------|
| 启动速度 | <100ms（冷启动） | 3-10 秒 |
| 运行速度 | 快 5-10 倍 | 较慢 |
| Jest 兼容性 | 极高 | — |
| 内置 DOM 测试 | 是（happy-dom） | 需要 jsdom |
| 覆盖率报告 | 内置 | 需要 jest-coverage |
| 配置文件 | bunfig.toml | jest.config.js |

## 框架与工具链集成

### Hono（推荐组合）

Hono 是为 Bun 优化的轻量 Web 框架：

```typescript
import { Hono } from 'hono'
import { cors } from 'hono/cors'

const app = new Hono()

app.use('/*', cors())

app.get('/api/health', (c) => c.json({ status: 'ok' }))
app.post('/api/users', async (c) => {
  const body = await c.req.json()
  return c.json({ created: true, id: 1 })
})

export default {
  port: 3000,
  fetch: app.fetch,
}
```

### Next.js

Bun 可以运行 Next.js 应用：

```bash
# Next.js 14+ 兼容 Bun
bun add next react react-dom
bun run next dev  # 仍使用 Next.js 的打包器，但 Bun 处理依赖安装
```

### 数据库集成

```typescript
// Prisma
import { PrismaClient } from '@prisma/client'
const prisma = new PrismaClient()

// Drizzle ORM（有直接适配 bun:sqlite 的驱动）
import { drizzle } from 'drizzle-orm/bun-sqlite'
import { sql } from 'drizzle-orm'

// bun:sqlite 直接使用
import { Database } from 'bun:sqlite'
const db = new Database('blog.db')
```

### 在 GitHub Actions 中使用

```yaml
# .github/workflows/test.yml
- name: Install Bun
  uses: oven-sh/setup-bun@v2
  with:
    bun-version: latest

- name: Install dependencies
  run: bun install --frozen-lockfile

- name: Run tests
  run: bun test --coverage

- name: Build
  run: bun build --compile --outfile app src/index.ts
```

## 配置文件：bunfig.toml

Bun 的全局配置通过 `~/.bunfig` 或项目根目录的 `bunfig.toml` 管理：

```toml
# 日志级别
logLevel = "debug"

# 安装相关
[install]
registry = "https://registry.npmjs.org/"
# 离线模式
# offline = true
# 全局缓存目录
# cacheDir = "~/.bun/install/cache"

# 运行相关
[run]
# 自动安装缺失的包
autoInstallPeers = true
# watch 模式
# watch = true

# 测试相关
[test]
# 覆盖率阈值
coverageThreshold = 80
# 并发数
concurrency = 8
```

## 性能基准：测的是什么，不能说明什么

不直接给精确数字，因为具体值随版本、硬件和被测负载浮动，抄一份数字很容易骗到你自己。按[Bun 官方基准](https://bun.sh/blog)与非官方复测的稳定结论，可以放心记住的是相对量级：

| 操作 | 量级结论 | 主要来自哪部分开销 |
|------|---------|------------------|
| 冷启动（空脚本） | Bun 显著更快，常为数量级差 | JavaScriptCore 初始化 + 模块解析 |
| 依赖安装（缓存命中） | Bun 明显更快 | 下载并发 + 解压 + 硬链接复用 |
| 依赖安装（冷缓存） | 差距缩小 | 网络下载本身成为瓶颈 |
| HTTP QPS（空响应） | Bun 更高 | 事件循环 + HTTP 解析器 |
| 测试运行（纯断言） | Bun 更快 | 测试框架启动 + 用例调度 |
| 打包（纯转译） | 与 esbuild 接近 | 解析 + 转译 + 写盘 |

这些量级只反映各自最容易命中"快"的那一段，别外推到别的场景：

- **冷启动**的优势不等于业务逻辑运行得快。它测的是进程起动与模块加载，业务代码一旦真正执行，优势可能被抹平。
- **包安装**在缓存命中时差距最大；第一次装（冷缓存）更多受网络带宽约束，收益明显收窄。
- **HTTP QPS**用空响应测，反映事件循环与 HTTP 层；真实接口带着数据库查询、复杂 JSON 序列化时，瓶颈会转移。
- **测试**用纯断言测，启动快是共识；但含大量磁盘/网络 I/O 的集成测试，收益要看读写本身。
- **打包**接近 esbuild 是 Bun 官方目标，但插件生态与复杂项目分割场景仍可能存在差异。
- 任何一份数字都受硬件、操作系统、Bun 与依赖版本影响。真要评估换不换，用自己项目跑一遍[官方基准脚本](https://bun.sh/docs/guides)或直接 `time` 三个命令对比，比抄别人的表可靠。

## 已知限制

以下场景需要注意：

**1. V8 特有功能缺失**
Bun 使用 JavaScriptCore，不是 V8。如果你的代码依赖 `v8.*` API（如 `v8.Serializer`），会不兼容。大部分 npm 包不受影响，但某些 Node.js 内部工具链可能有问题。

**2. Native Addon 支持有限**
`node-gyp` 编译的 C++ addon 支持还不完整。使用 `better-sqlite3`、`sharp` 这类 native addon 时，建议先测试。

**3. Windows 生态相对不成熟**
macOS 和 Linux 仍然是 Bun 的最佳运行环境。Windows 版本虽然可用，但部分边缘功能可能有 bug。

**4. 生态仍在成熟**
npm 上的包大多数可以在 Bun 上运行，但某些包的特定功能（如 Vite 的某些插件）可能需要调整。查阅 [Bun 兼容性列表](https://bun.sh/docs/runtime/nodejs-apis) 确认。

**5. 版本稳定性**
Bun 仍在活跃开发中，版本之间可能有 breaking change。使用 `bun.lockb` 锁定依赖版本，避免升级导致的不兼容。

**6. Bun.SQL 的批量插入在某些数据形态下开销大**
`sql(rows)` 批量插入若含可空列，Bun 会对不同 null 组合各编译预编译语句，数据库端语句可能不断累积，极端情况推高内存。真实命中过的话，可在项目 issue 里搜 `Bun.SQL batch nullable` 确认当时是否已修复。批量写入的列含可空字段时，先小批量压测再上生产。

## FAQ：常见问题与错误排查

**Q1：`bun install` 报 `ENOENT` 或网络错误**

先检查网络代理设置。Bun 默认从 `registry.npmjs.org` 拉包，如果你在大陆环境，在 `bunfig.toml` 里配置镜像：

```toml
[install]
registry = "https://registry.npmmirror.com/"
```

如果报的是 SSL 错误，确认系统 CA 证书是否过期。

**Q2：`bun run` 跑某些 Node.js 脚本报错**

Bun 对 `node:` 模块的兼容性在持续改进，但仍有少数 API 未覆盖。运行时如果报 `NotImplemented`，先 `bun upgrade` 到最新版，仍不行则查阅 [兼容性列表](https://bun.sh/docs/runtime/nodejs-apis) 确认该 API 是否支持。临时方案是用 `node` 跑这个脚本，其余任务仍用 Bun。

**Q3：`Bun.serve` 在 macOS 上性能不如 Linux**

macOS 上 `Bun.serve` 基于 kqueue，Linux 上基于 io_uring。io_uring 在高并发下的开销显著低于 kqueue，所以同样的代码在 Linux 上的 QPS 通常更高。如果你的服务要部署到生产，建议以 Linux 为目标环境做基准测试。

**Q4：`bun test` 跑 Jest 测试时部分 mock 不生效**

Bun 的 mock API 与 Jest 高度兼容但不完全一致。常见差异：`jest.fn()` 在 Bun 里是 `fn()` 或 `mock()`，`jest.spyOn` 的行为略有不同。迁移时先跑一遍 `bun test`，按报错逐个调整。

**Q5：`bun build` 打包后产物在浏览器里跑不起来**

检查 `target` 参数。默认是 `browser`，但如果你的代码用了 Node.js 内置模块，需要确认这些模块是否在浏览器环境有 polyfill。另外 `format` 参数（`esm`/`cjs`/`iife`）必须与目标环境的模块系统匹配。

**Q6：Bun 的 `Bun.SQL` 和 `bun:sqlite` 该用哪个？**

`bun:sqlite` 是早期就有的同步 SQLite 接口，API 风格接近 `better-sqlite3`，适合简单场景。`Bun.SQL` 是 1.3 统一的 SQL 客户端，支持 PostgreSQL/MySQL/MariaDB/SQLite，用标记模板字面量，自带连接池和参数化。新项目建议用 `Bun.SQL`，老项目用 `bun:sqlite` 也可以。

## 自测题

以下问题用于检验你对 Bun 核心机制的理解，答案可在对应章节或官方文档找到。

1. Bun 用 JavaScriptCore 而不是 V8，这个选择带来了哪些优势和代价？提示：从启动速度、内存占用、V8 特有 API 兼容性三个角度想。
2. `Bun.serve` 在 Linux 和 macOS 上分别基于什么事件循环机制？这种平台特化对生产部署意味着什么？
3. `bun install` 比 `npm install` 快的四个原因是什么？其中哪些优势在冷缓存（首次安装）场景下会减弱？
4. `Bun.SQL` 和 `bun:sqlite` 在 API 风格和适用场景上有什么区别？如果你要连 PostgreSQL，应该用哪个？
5. Bun 的 `bun:test` 与 Jest 在 mock API 上有哪些已知差异？迁移时如何快速定位不兼容的断言？
6. `bun build --compile` 生成的单文件可执行文件大小约 50MB，这个体积主要来自什么？这种打包方式适合什么场景，不适合什么场景？
7. 在什么情况下你应该**不**用 Bun 替换 Node.js？至少给出三个具体场景。

## 进阶路径

掌握 Bun 基础后，可以按以下方向深入：

**全栈应用**：用 `bun init` + Hono + Drizzle ORM + `Bun.SQL` 搭一个全栈应用，体验"零配置"开发。Hono 的路由设计、Drizzle 的类型安全 schema、Bun 的内置数据库客户端三者组合，可以省掉 Express + Prisma + pg 的一堆依赖。

**CLI 工具**：用 `bun build --compile` 把 CLI 工具打包成单文件可执行文件，分发给没有 Node.js 环境的用户。配合 `Bun.spawn` 调用子进程，`Bun.file` 读写配置，能做出比 Node.js + pkg 更轻量的 CLI。

**CI/CD 加速**：在 GitHub Actions 里用 `bun install --frozen-lockfile` 替换 `npm ci`，用 `bun test` 替换 `jest`。大型 monorepo 的 CI 时间通常能缩短 30-50%。注意先在本地跑通 `bun test`，确认没有兼容性问题再上 CI。

**Edge Function 与 Serverless**：Bun 的冷启动优势在 Serverless 场景下最明显。Bun 官方提供了 `bun deploy` 命令部署到 Bun Edge，Cloudflare Workers、Vercel Edge Functions 等平台也在逐步支持 Bun 运行时。

**插件与工具链**：学习 `Bun.plugin` 的 API，为自定义文件类型（如 `.graphql`、`.vue`）写加载器。如果你维护一个内部工具链，可以用 Bun 的插件系统替换 Webpack loader 或 Vite plugin。

## 练习

以下问题用于检验你的实际操作能力，建议动手实践后回答：

**练习 1：替换现有项目的包管理器**

找一个你现有的 Node.js 项目（使用 npm 或 yarn），执行以下步骤：
1. 备份现有的 `node_modules` 和 `package-lock.json` / `yarn.lock`
2. 删除 `node_modules` 目录
3. 运行 `bun install`
4. 对比安装时间和生成的 `bun.lockb` 文件大小
5. 运行 `bun run dev`（或你的启动命令），检查是否正常工作

**练习 2：用 Bun.serve 替换 Express**

创建一个简单的 HTTP 服务器，比较 Bun.serve 和 Express 的性能：
```typescript
// bun-server.ts
const server = Bun.serve({
  port: 3000,
  fetch(req) {
    return new Response('Hello from Bun!')
  }
})
```

```javascript
// express-server.js
const express = require('express')
const app = express()
app.get('/', (req, res) => res.send('Hello from Express!'))
app.listen(3000)
```

使用 `ab`（ApacheBench）或 `wrk` 进行压力测试，对比 QPS 和响应时间。

**练习 3：用 bun test 替换 jest**

在一个现有项目中：
1. 安装 `bun`
2. 将现有的 jest 测试文件重命名为 `*.test.ts`（如果需要）
3. 运行 `bun test`
4. 记录启动时间和运行时间
5. 如果有 mock 不兼容，记录具体差异

**练习 4：打包单文件可执行文件**

创建一个简单的 CLI 工具，然后打包成单文件可执行文件：
```typescript
// cli.ts
console.log('Hello from CLI!')
```

运行 `bun build --compile --outfile mycli cli.ts`，然后在没有 Node.js 环境的机器上运行 `./mycli`。

**练习 5：集成 Bun.SQL 进行数据库操作**

创建一个简单的 CRUD 应用，使用 `Bun.SQL` 连接 PostgreSQL：
```typescript
import { sql } from 'bun'

const users = await sql`SELECT * FROM users`
console.log(users)
```

对比使用 `pg` 库的传统方式，记录代码行数和类型安全差异。

---

## 适用场景与采用顺序

**Bun 适合的场景：**

- 新项目的起始脚手架（`bun init` + Hono + Drizzle）
- 需要极致启动速度的 CLI 工具和脚本
- 大型 monorepo 的依赖管理和 CI 加速
- 高并发 HTTP 服务（API server、edge function）
- 需要内置 SQLite/PostgreSQL 的全栈应用
- 快速原型和迭代（不需要配置 ts-node/jest/vite 一堆工具）

**需要谨慎的场景：**

- 严重依赖 Node.js 内部 API 或 `node-gyp` 编译的 addon
- 需要 V8 特定功能（大部分业务代码不会遇到）
- 团队对 Node.js 生态有强烈偏好且转换成本高

**采用顺序建议**

如果决定引入 Bun，建议按以下顺序渐进采用：

1. **先用包管理器**：在现有 Node.js 项目里把 `npm install` 换成 `bun install`，风险最低，收益立竿见影。
2. **再替换测试框架**：把 `jest` 换成 `bun test`，先在单个子包里试，确认 mock 和快照兼容后再推广。
3. **然后试运行时**：在开发环境用 `bun run` 替换 `node`，观察是否有兼容性问题。
4. **最后考虑生产部署**：在 staging 环境跑一段时间，确认稳定后再上生产。

这个顺序的好处是每一步都可回滚，且每一步都能拿到性能收益。反过来，如果你一开始就把生产服务从 Node.js 切到 Bun，遇到兼容性问题时的回滚成本会很高。

Bun 能走到这一步，有几个具体原因：创始人 **Jarred Sumner**（前 Stripe 工程师）深知大型项目里 npm 的痛点；用 Zig 编写给了团队对性能的极致控制；JavaScriptCore 的选择避开了 V8 的许可问题，同时获得了更好的启动性能；渐进式兼容策略让它在 Node.js 兼容性上逐步完善。

如果你还没用过 Bun，可以从今天开始：

```bash
curl -fsSL https://bun.sh/install | bash
bun init my-project
cd my-project
bun add hono
# 编辑 src/index.ts，然后：
bun run src/index.ts
```

**仓库链接**：https://github.com/oven-sh/bun
**文档地址**：https://bun.sh/docs
**版本**：以 [Bun 发布页](https://github.com/oven-sh/bun/releases) 为准

---

---

_本文基于 Bun 文档（bun.sh/docs）整理。API 名称、模块路径与版本以 [Bun 官方文档](https://bun.sh/docs) 为准。文中涉及的具体版本能力（如 Bun 1.2/1.3 新增的内置客户端）请以对应版本号查证。_
