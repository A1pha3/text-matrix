---
title: "swc-project/swc 架构拆解：Rust 写的 TS/JS 编译器为何能在 33k+ star 仓库里保持单 crate 形态"
date: "2026-06-13T21:03:20+08:00"
slug: "swc-rust-typescript-compiler-architecture"
description: "拆解 swc-project/swc 架构：Rust 写的高性能 TS/JS 编译器，单 crate 聚合 parser/codegen/bundler，Rust 库 + Node 包双形态发行。"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "TypeScript", "编译器", "Babel", "Node.js"]
---

# swc-project/swc 架构拆解：Rust 写的 TS/JS 编译器为何能在 33k+ star 仓库里保持单 crate 形态

> 一句话核心判断：**SWC 是 Rust 写的 TypeScript/JavaScript 编译器，仓库看似只有一个根 crate（`swc`），但通过 Cargo workspace 聚合了 parser / codegen / bundler / CSS / 压缩器等几十个子 crate，对外同时暴露 Rust API 和 Node API（`@swc/core`）。它比 Babel 快 20–70 倍的核心原因是 Rust + 精心设计的 SIMD 优化，但工程上更值得学习的是"如何在大规模编译器项目里既保持单一发布入口、又不牺牲模块化"**。

## 一、项目坐标

| 字段 | 值 |
|------|------|
| 仓库 | [swc-project/swc](https://github.com/swc-project/swc) |
| 主语言 | Rust（编译器核心）+ Node.js binding（`@swc/core`） |
| Stars | 约 33.5k（截至 2026-06） |
| License | Apache-2.0 |
| MSRV | Rust 1.73 |
| Node 版本要求 | v10+ 用 / v20+ 开发 |
| 周边工具 | `@swc/cli`、`@swc/core`、`@swc/jest`、Next.js / Vite / Turbopack 集成 |

33.5k stars 的体量，背后是"Next.js 默认编译器 + Deno 内置 + Vite SWC 插件"这套生态——几乎所有现代 JS 工具链都会直接 / 间接调用 SWC。

## 二、为什么不是 Babel 的复制？

很多人第一次接触 SWC 时会问"Babel 不是已经够用了吗，为什么还要 SWC"。答案是**性能瓶颈**：

| 维度 | Babel | SWC |
|------|-------|-----|
| 语言 | JavaScript | Rust |
| 编译速度（中型项目） | 基准 1× | 约 20–70× |
| 插件系统 | JS in-process | Rust 编译时 + Node native binding |
| TypeScript 类型擦除 | 需 `@babel/preset-typescript` | 原生 |
| 体积（`@swc/core`） | — | 约 9 MB（含 native binding） |
| 生态 | 成熟 | 已成熟（Next.js / Deno / Vite 默认） |

性能差距的本质是**语言层**——Babel 跑在 V8 上，是解释执行 AST 转换；SWC 跑在 Rust 上，是编译后的 native 代码 + SIMD 优化。对 CI 这种"每次 push 都要重新编译"的工作流，20 倍速度差就是 30 秒 vs 10 分钟的差距。

## 三、系统地图：根 crate + workspace

很多人打开仓库第一反应是"怎么就一个 `Cargo.toml`？"——仓库根的 `Cargo.toml` 只是 workspace 入口，真正的代码在 `crates/` 下面分了几十个 crate：

```
swc-project/swc/
├── Cargo.toml              ← workspace 根（聚合所有 crates）
├── ARCHITECTURE.md
├── crates/
│   ├── swc/                ← "umbrella" crate，对外的主入口
│   │   ├── src/lib.rs      ← re-export 所有子 crate 的 public API
│   │   └── ...
│   ├── swc_ecma_parser/    ← ES 解析器（ts/tsx/js/jsx）
│   ├── swc_ecma_ast/       ← AST 类型定义
│   ├── swc_ecma_visit/     ← Visitor 模式 / Fold / helpers
│   ├── swc_ecma_transforms/← 内建 transform 模块
│   ├── swc_ecma_codegen/   ← 代码生成（ast → 源码）
│   ├── swc_css_parser/     ← CSS 解析
│   ├── swc_css_codegen/    ← CSS 代码生成
│   ├── swc_css_minifier/   ← CSS 压缩
│   ├── swc_minifier/       ← JS 压缩
│   ├── swc_module_graph/   ← 模块图（bundler 用）
│   ├── swc_bundler/        ← bundler 核心
│   ├── swc_cli/            ← CLI 入口（@swc/cli 对应）
│   ├── swc_node_bindings/  ← N-API / Neon 绑定（@swc/core 底层）
│   └── ...（几十个）
├── packages/               ← Node 包源码（@swc/core 等）
└── scripts/                ← 维护脚本
```

关键设计：

- **根 crate `swc` 是一个 umbrella**，只 `pub use` 所有子 crate 的 public API，用户写 Rust 代码只要 `use swc::*` 就能拿到所有东西；
- **子 crate 互相独立**，可以单独测试、单独发版（crates.io 上 `swc_ecma_parser` 等都有独立版本号）；
- **Cargo workspace 共享依赖图**，所有 crate 共用同一份 `Cargo.lock`，避免版本错位。

这种"根 crate 是 facade"的设计在大型 Rust 项目里很常见——好处是**外部用户 API 简洁，内部模块化清晰**；坏处是依赖图容易膨胀，需要 CI 严控子 crate 的边界。

## 四、核心流水线：Parse → Transform → Codegen

SWC 的核心编译流程和所有编译器一样，三段式：

```
┌──────────┐    ┌──────────────┐    ┌────────────┐
│  Source  │ →  │   Parser     │ →  │  AST       │
│  (.ts)   │    │  swc_ecma_   │    │ (swc_ecma_ │
│          │    │  parser      │    │  _ast)     │
└──────────┘    └──────────────┘    └────────────┘
                                          │
                                          ▼
                                   ┌──────────────┐
                                   │  Transform   │
                                   │  swc_ecma_   │
                                   │  transforms/ │
                                   └──────────────┘
                                          │
                                          ▼
┌──────────┐    ┌──────────────┐    ┌────────────┐
│  Output  │ ←  │   Codegen    │ ←  │  Modified  │
│  (.js)   │    │  swc_ecma_   │    │  AST       │
│          │    │  codegen     │    │            │
└──────────┘    └──────────────┘    └────────────┘
```

### 4.1 Parser：手写递归下降 + SIMD

`swc_ecma_parser` 用的是**手写递归下降**而不是 parser generator（如 LALRPOP）。这有两个原因：

1. **错误恢复**——手写 parser 能给出更人性化的错误信息（行列号 + 上下文），对 IDE 集成至关重要；
2. **性能控制**——能精细地插入 SIMD 优化、热路径内联、零拷贝字符串处理。

SWC 的 parser 对 ASCII 关键字走 SIMD 快速路径，整体解析速度比 esprima（最常见的 JS parser generator 产物）快 3–10 倍。

### 4.2 AST：带位置信息的 typed tree

AST 类型都在 `swc_ecma_ast` crate 里，用 Rust struct 表示。每个节点都带 `Span { lo: BytePos, hi: BytePos }`——位置信息在 parser 阶段就附上，后续所有 transform 都能用它生成 source map。

AST 设计的关键决策是**保留所有原始信息**（注释、token 位置、空白），codegen 阶段可以选择"完全重建"或"保留原格式"——后者用于最小化代码改动（只替换需要替换的部分）。

### 4.3 Transform：插件 vs 内建

SWC 有两种 transform 方式：

1. **内建 transform**（`swc_ecma_transforms/`）：用 Rust 写，性能最高，覆盖常见场景（TS 类型擦除、JSX → React.createElement、ES2015+ → ES5 等）；
2. **WASM 插件**（`swc_ecma_transforms::testing` + `@swc/plugin`）：用 JS / TS 写自定义 transform，编译成 WASM 加载。

内建 transform 是默认走的高速路径，WASM 插件给"必须自定义"的场景留口子（性能比纯 JS Babel 插件仍然快 5–10 倍）。

### 4.4 Codegen：与原格式保持一致

`swc_ecma_codegen` 的核心难点是**生成代码要和原代码尽量一致**——只在必要的地方做改动。这样配合 source map，调试时能直接跳回原文件原位置。

实现方式：

- 节点级别的"修饰器"决定是否保留原 token；
- 缩进、换行、空格策略单独配置；
- 输出格式（`es5` / `es2015` / `es2020` 等）通过 target 配置驱动。

## 五、@swc/core：Node.js 绑定

`@swc/core` 不是另一个编译器，它是 SWC 的 **N-API 绑定**——让 Node.js 代码能直接调 SWC 的 Rust 实现：

```typescript
import { transformSync } from '@swc/core';

const result = transformSync(
  `const greet = (name: string) => console.log('Hi ' + name);`,
  {
    jsc: {
      parser: { syntax: 'typescript' },
      target: 'es2020',
    },
  }
);
console.log(result.code);
// const greet = (name) => console.log('Hi ' + name);
```

底层 crate 是 `swc_node_bindings`：

```
Rust 编译器（swc_ecma_*）
       │
       ▼ N-API / Neon
Node.js native addon（@swc/core.node）
       │
       ▼ Node.js require
@swc/core JS wrapper
```

这种"重计算在 Rust、JS 只做胶水"的模式是 Node.js native module 的标准做法。性能上 Rust 计算 + JS 胶水的开销基本可以忽略不计（每次调用约 100ns FFI 开销 vs ms 级的编译开销）。

## 六、性能：从架构到 SIMD

SWC 比 Babel 快的 20–70 倍到底从哪来？拆开看：

| 优化层 | 收益 | 实现位置 |
|--------|------|---------|
| Rust vs JS | 5–10× | 全局 |
| SIMD 关键字识别 | 1.5–2× | parser |
| 零拷贝字符串 | 1.2–1.5× | parser + codegen |
| 紧凑 AST 表示 | 1.2× | ast |
| 并行 codegen | 2–4×（多文件时） | codegen |
| 编译时单态化 | 1.1–1.3× | generics |

注意"并行 codegen"对单文件收益不大，但对**大型项目 / monorepo** 的 CI 构建收益显著——SWC 能把多个文件的 codegen 任务并行化。

## 七、Bundler：SWC 1.5+ 的新方向

2023 年开始 SWC 团队投入了 bundler 实现，crates 在 `swc_bundler` / `swc_module_graph`：

```rust
use swc_bundler::{Bundler, Bundle};
use swc_common::{FileName, FilePathMapping};

let bundler = Bundler::new(
    &globals,
    swc_bundler::Config { .. },
    swc_bundler::Resolve::Real(swc_bundler::FsResolve::new()),
    swc_bundler::Load::Real(swc_bundler::FsLoad::new()),
    Hook,
);

let mut entries = vec![Entry { filename: FileName::Real("entry.ts".into()) }];
let bundle = bundler.bundle(entries)?;
```

特点：

- 完全用 Rust 实现，无 JS runtime；
- 支持 tree shaking（通过 `swc_ecma_visit` 的依赖图分析）；
- 支持 source map、自动 chunk splitting；
- 当前性能接近 esbuild，部分 benchmark 已经反超。

SWC bundler 还没完全替代 webpack，但已经被 Deno、Farm 等新一代构建工具采用。对 Rust 后端团队来说，"前端构建工具链也用 Rust"的意义不只是性能——**整个 dev loop（前端构建 + 后端编译）都是 native binary**，CI 缓存友好、跨平台一致。

## 八、版本同步：crates 同步升级工具

SWC 子 crate 数量多（30+），版本同步是个工程难题。仓库自带一个"一键升级所有 SWC crates"的脚本：

```bash
curl https://raw.githubusercontent.com/swc-project/swc/main/scripts/update-all-swc-crates.sh | bash -s
```

脚本依赖：

- `jq`：解析子 crate 的版本号；
- `cargo upgrade`：批量升级 `Cargo.toml` 依赖。

跑完会更新所有 crate 的版本号 + 跑 `cargo build` 确认还能编译。这把"几十个 crate 同步发版"的人工成本从小时级降到分钟级。

**注意 README 的关键承诺**：

> If you select the latest version of each crates, it will work

这是 SWC 工程文化的核心——任何时刻 crates.io 上所有 SWC crate 的最新版本组合都应该是能 compile 过的。对编译器这种"几十个 crate 互相耦合"的项目，这是个非常高的 SLA，需要严苛的 CI 流水线兜底。

## 九、和 esbuild 的差异

esbuild 是另一个用 Go 写的 TS/JS 编译/打包工具，常被拿来和 SWC 对比：

| 维度 | SWC | esbuild |
|------|-----|---------|
| 语言 | Rust | Go |
| 编译器架构 | parser + transform + codegen 三段 | parser + printer（无中间 AST transform） |
| Plugin | WASM（自定义 transform） | Go plugin（需重新编译） |
| Bundler | 有（`swc_bundler`） | 有（一开始就主打 bundler） |
| 性能 | 接近 / 部分领先 | 略快（Go 的 goroutine 调度友好） |
| 生态 | Next.js / Deno / Vite | Vite / tsup / tsx |

关键差异在**架构**——esbuild 用的是"解析后直接生成代码"的 printer 模型（没有显式 transform AST 阶段），适合做 bundler；SWC 的"parser → AST → transform → codegen"模型更适合需要复杂 transform 的场景（Next.js SWC compiler 那一套）。

实际选型：如果只是 bundle + minify，esbuild 够用；如果需要复杂 transform（如自定义 React Server Components 编译器），SWC 更合适。

## 十、采用建议

### 10.1 适合选 SWC 的场景

- **CI 构建时间是大瓶颈**——从 Babel 迁到 SWC，典型收益是 20–70×。
- **Next.js / Deno / Vite 用户**——这些工具已经默认用 SWC，直接受益。
- **需要自定义 transform**（如团队内部的代码规范检查、特殊编译期优化）——用 WASM 插件写，比 Babel JS 插件快很多。
- **跨语言工具链**——如果团队后端是 Rust、前端构建也想统一到 Rust（一个 native binary 跨平台），SWC 比 Babel 友好。

### 10.2 不太适合

- **已经用 Vite / esbuild 且够快**——没必要再叠一层 SWC。
- **需要复杂的 Babel 插件生态**——某些冷门 Babel 插件（如特殊的 CSS-in-JS 编译）在 SWC 里没有等价实现，需要自己写 WASM 插件。
- **Windows + 极简部署**——`@swc/core` 的 native binary 体积约 9 MB，对极简部署场景偏重。

### 10.3 工程上的注意点

- **`@swc/core` 版本**和 SWC 编译器版本强耦合——升级时一次性升 `@swc/core` + 周边包，不要分批。
- **Node 版本**：用 `@swc/core` 只需 Node v10+，但开发 SWC 本身需要 Node v20+。
- **MSRV**：Rust 1.73。如果你的项目锁了更低 Rust 版本，不能直接引入 `swc` 的子 crate。
- **crate 依赖**：在 Rust 项目里直接 `use swc_ecma_parser` 等子 crate 比 `use swc` 更稳定——根 crate 是 umbrella，API 表面更大，breaking change 概率更高。

SWC 是 Rust 编译器生态里"被广泛生产验证"的项目之一——Next.js 每天处理上亿次 SWC 编译调用，Deno 直接把它内置进 runtime。这种规模的工程验证，比任何 benchmark 都更说明它的稳定性。如果你正在被 Babel 的速度困扰，或者在规划一条"全 Rust 工具链"的路线，SWC 是几乎绕不开的环节——理解它的 workspace 架构、transform 模型、Node binding 边界，对整个现代 JS 工具链的设计取舍都会更清晰。