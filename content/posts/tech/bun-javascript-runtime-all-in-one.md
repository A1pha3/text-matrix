---
title: "Bun：从入门到精通——唯一让你放弃 npm/yarn/vite/jest 的 JavaScript 运行时"
date: "2026-05-16T15:10:00+08:00"
slug: "bun-javascript-runtime-all-in-one"
description: "Bun 是用 Zig 编写的高性能 JavaScript 运行时、 bundler、测试框架和包管理器，GitHub 星标已突破 9 万。本文从核心概念、安装配置、运行时、包管理、打包、测试、框架集成六个维度，对这个 2021 年起步、如今已全面生产可用的项目做完整技术解读。"
draft: false
categories: ["技术笔记"]
tags: ["Bun", "JavaScript", "TypeScript", "运行时", "bundler", "包管理器", "测试框架", "Zig", "Node.js", "性能优化"]
---

# Bun：从入门到精通——唯一让你放弃 npm/yarn/vite/jest 的 JavaScript 运行时

2026 年 5 月，GitHub 星标突破 **90,685**，最新版本 1.3.14，最近一次提交就在 6 小时前。这个项目的活跃度和影响力，已经远超一般开源工具的范畴。

**Bun** 是什么？一句话：**一个可执行文件，同时是运行时 bundler + 测试框架 + 包管理器。** 你不再需要 node + npm + vite + jest，只需要 `bun`。

这不是概念炒作。从 2024 年起，Bun 已进入多家头部公司的生产环境。本文对 Bun 做一次系统性的完整解读。

---

## 1. 什么是 Bun

Bun 是一个用 **Zig** 编写、底层基于 **JavaScriptCore**（WebKit 引擎，与 Node.js 使用的 V8 不同）的 JavaScript 运行时。它的设计目标是成为 Node.js 的**直接替代品**，同时内置打包、测试和包管理功能。

### 核心定位

```
Bun = JavaScript 运行时 + 包管理器 + 打包工具 + 测试框架
```

三件事让它与众不同：

**第一，启动速度和内存占用远低于 Node.js。** JavaScriptCore 比 V8 轻量，加上 Zig 的系统级控制，Bun 的冷启动时间通常是 Node.js 的 1/4 到 1/10。

**第二，所有工具共用一个进程。** 不需要为 npm 创建一个进程，再为 vite 创建另一个进程。包解析、文件监听、HTTP 服务都在同一个可执行文件里。

**第三，Node.js 兼容性开箱即用。** 大部分 npm 包不需要修改即可在 Bun 上运行，包括 Express、Fastify、Prisma、Next.js 等主流框架。

### 技术栈

| 层级 | 技术选型 |
|------|---------|
| 语言 | Zig |
| 引擎 | JavaScriptCore (WebKit) |
| 包管理器 | 自研，与 npm 完全兼容 |
| 构建工具 | 自研，打包速度对标 esbuild |
| 测试框架 | 自研，与 Jest API 高度兼容 |
| 系统 | 支持 macOS (x64 + Apple Silicon)、Linux (x64 + arm64)、Windows |

---

## 2. 安装与快速开始

### 安装方式

```sh
# 方式一：官方安装脚本（推荐）
curl -fsSL https://bun.com/install | bash

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

当前稳定版本 `1.3.14`，本地安装版本 `1.3.6`。

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

---

## 3. 运行时：Node.js 的直接替代品

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

Bun.serve 底层基于 Linux 的 io_uring（异步 I/O），吞吐量远超 Node.js 的 libuv。在同等硬件下，Bun HTTP 服务器的 QPS 通常是 Node.js + Express 的 2-4 倍。

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

对于没有完全兼容的包，可以查看 [Bun 的 Node.js 兼容性列表](https://bun.com/docs/runtime/nodejs-compat)，大多数主流包都已覆盖。

### 内置 API：Bun.*

Bun 在全局对象上提供了一组高性能原生 API：

```typescript
// 文件 I/O（比 node:fs 快）
const file = Bun.file('package.json')
const content = await file.text()

// SQLite（内置，无需安装 better-sqlite3）
import { Database } from 'bun:sqlite'
const db = new Database('app.db')
const rows = db.query('SELECT * FROM users').all()

// PostgreSQL（使用 Bun.sql）
import { Bun.sql } from 'bun:sql'
const db = await Bun.sql.connect('postgres://user:pass@localhost/db')

// Redis（内置驱动）
import { Redis } from 'bun:redis'
const redis = await Redis.connect()
await redis.set('key', 'value')

// S3 客户端
import { S3Client } from 'bun:s3'
const s3 = new S3Client({ bucket: 'my-bucket', region: 'us-east-1' })

// Cron 定时任务
Bun.cron('*/5 * * * *', () => {
  console.log('Runs every 5 minutes')
})

// WebView（macOS）
import { WebView } from 'bun:webview'
```

---

## 4. 包管理器：性能碾压 npm/yarn/pnpm

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

---

## 5. 打包工具：Bun.build

Bun 内置的打包器（bundler）速度对标 esbuild，功能覆盖 Vite：

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

Bun 的打包器不是 Vite 的替代品，而是**更快的替代品**。如果你的项目使用 Vite 特有的插件生态，可以继续用 Vite，同时用 `bun install` 加速依赖安装。如果你的项目比较简单，直接用 `Bun.build` 可以省掉整个 Vite 工具链。

---

## 6. 测试框架：Jest 兼容的极速测试

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

---

## 7. 框架与工具链集成

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

// Drizzle ORM（性能更好）
import { drizzle } from 'drizzle-orm/bun-sqlite'
import { sql } from 'drizzle-orm'

// Bun:sqlite 直接使用
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

---

## 8. 配置文件：bunfig.toml

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

---

## 9. 性能基准：数字说话

Bun 官方基准测试（在 M2 MacBook Pro 上）：

| 操作 | Node.js | Bun | 提速比 |
|------|---------|-----|--------|
| `bun run` 冷启动（空文件） | ~80ms | ~8ms | **10x** |
| `bun install`（500 包，hot cache） | ~18s | ~1.2s | **15x** |
| HTTP QPS（Hello World，linux-aarch64） | ~72k | ~198k | **2.7x** |
| `bun test` 运行 1000 个测试用例 | ~12s | ~1.8s | **6.7x** |
| 打包 1000 个 TS 文件（prod minify） | esbuild: ~0.8s | ~0.6s | **1.3x** |

实际表现因项目规模、硬件和操作系统而异。但在大规模项目中，Bun 的优势会更加明显。

---

## 10. 当前限制与注意事项

Bun 并不完美，以下场景需要谨慎：

**1. V8 特有功能缺失**
Bun 使用 JavaScriptCore，不是 V8。如果你的代码依赖 `v8.*` API（如 `v8.Serializer`），会不兼容。大部分 npm 包不受影响，但某些 Node.js 内部工具链可能有问题。

**2. Native Addon 支持有限**
`node-gyp` 编译的 C++ addon 支持还不完整。使用 `better-sqlite3`、`sharp` 这类 native addon 时，建议先测试。

**3. Windows 生态相对不成熟**
macOS 和 Linux 仍然是 Bun 的最佳运行环境。Windows 版本虽然可用，但部分边缘功能可能有 bug。

**4. 生态仍在成熟**
npm 上的包大多数可以在 Bun 上运行，但某些包的特定功能（如 Vite 的某些插件）可能需要调整。查阅 [Bun 兼容性列表](https://bun.com/docs/runtime/nodejs-compat) 确认。

**5. Long-term 稳定性**
Bun 仍在活跃开发中，版本之间的 API 可能有 breaking change。使用 `bun.lockb` 锁定依赖版本，避免升级导致的不兼容。

---

## 11. 适用场景

**Bun 非常适合：**

- 新项目的起始脚手架（`bun init` + Hono + Drizzle）
- 需要极致启动速度的 CLI 工具和脚本
- 大型 monorepo 的依赖管理和 CI 加速
- 高并发 HTTP 服务（API server、edge function）
- 需要内置 SQLite/PostgreSQL/Redis 的全栈应用
- 快速原型和迭代（不需要配置 ts-node/jest/vite 一堆工具）

**Bun 需要谨慎的场景：**

- 严重依赖 Node.js 内部 API 或 `node-gyp` 编译的 addon
- 需要 V8 特定功能（大部分业务代码不会遇到）
- 团队对 Node.js 生态有强烈偏好且转换成本高

---

## 12. 总结

Bun 解决的根本问题是：**现代 JavaScript 工具链太碎片化了。**

做一个新项目，你需要 node、npm、typescript、vite、jest、eslint、prettier……每一个都需要安装、配置、维护。Bun 把这些全部整合到一个可执行文件里，启动速度还快 10 倍。

它的成功不是偶然的：
- **Jarred Sumner**（创始人）是前 Stripe 工程师，深知大型项目里 npm 的痛点
- 用 Zig 编写给了团队对性能的极致控制
- JavaScriptCore 的选择避开了 V8 的许可问题，同时获得了更好的启动性能
- 渐进式兼容策略：先做 Node.js 替代品，再逐步扩展

如果你还没用过 Bun，**今天就可以开始**：

```bash
curl -fsSL https://bun.com/install | bash
bun init my-project
cd my-project
bun add hono
# 编辑 src/index.ts，然后：
bun run src/index.ts
```

一个命令，5 分钟，感受一下什么是真正的速度。

**仓库链接**：https://github.com/oven-sh/bun
**文档地址**：https://bun.com/docs
**当前版本**：bun-v1.3.14（2026-05-13）