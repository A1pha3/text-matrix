---
title: "Tailwind CSS v4 的混合架构：Rust 管扫描，TypeScript 管编译"
date: 2026-08-08T03:35:00+08:00
slug: "tailwindcss-v4-architecture"
github_repo: "tailwindlabs/tailwindcss"
source_key: "gh:tailwindlabs/tailwindcss"
description: "Tailwind v4 常被说成『Rust 重写』，仓库拆开看是另一回事：扫描与候选提取下沉到 Rust oxide，候选编译成 CSS 的核心仍是主包 TypeScript，CSS 优化走 lightningcss。本文基于 tailwindcss 仓库（97.7k★）的 crates + packages 双轨结构拆解这套混合架构，附 v4 与 v3 的关键边界差异。"
draft: false
categories: ["技术笔记"]
tags: ["Tailwind CSS", "CSS 工具类", "Rust", "PostCSS", "前端工程化", "oxide"]
---

> **先给判断**：Tailwind v4 常被概括成「Rust 重写」，仓库拆开看并不是。它是一次分层重构：扫描与候选提取下沉到 Rust（oxide），CSS 优化交给 lightningcss（Rust 内核），而把候选编译成 CSS 的核心仍是主包里的 TypeScript。三层职责各自落进一个包边界——`@tailwindcss/oxide`、`tailwindcss`、`@tailwindcss/node`——这个划分比「全 Rust」的说法更值得看清，因为它决定了升级 v4 时哪里能期待数量级的提速（扫描、优化），哪里的行为仍由 JS 侧代码定义（编译语义）。

## 1. 仓库身份与版本位置

- **仓库**：`tailwindlabs/tailwindcss`（97.7k★ / 6.9k forks，主仓库也是 monorepo 根）。
- **License**：MIT（根 `package.json` 声明）。
- **版本线**：v4.0 于 2025-01-22 正式发布；截至 2026 年 9 月，主线在 v4.3.3（2026-07-16），此前两个月连发 v4.3.1 / v4.3.2。
- **根 `package.json`**：`"@tailwindcss/root"` + `"private": true`——仓库本身就是工作区，发布到 npm 的是 `packages/*` 子包。

`crates/` 与 `packages/` 双轨并存是判断这套架构的第一个信号：Rust 不止是构建工具，它是被发布的产品的一部分；但 Rust 也不止一处，CSS 优化用的 lightningcss 是另一个独立的 Rust 项目。把「用了 Rust」拆成「哪部分用了谁的 Rust」，是读懂 v4 的起点。

## 2. 总览：三层职责与包边界

先看地图，再进细节。v4 把一次构建拆给三个包，每个包对应仓库里的一层：

| 包（npm） | 仓库位置 | 语言 | 职责 |
| --- | --- | --- | --- |
| `@tailwindcss/oxide` | `crates/oxide` + `crates/node` | Rust（NAPI 绑定） | 扫描源文件、提取候选 class |
| `tailwindcss` | `packages/tailwindcss` | TypeScript | 编译核心：候选 → CSS AST → CSS 文本 |
| `@tailwindcss/node` | `packages/@tailwindcss-node` | TypeScript | Node 编排：加载配置、解析 `@import`、调 lightningcss 优化 |

`@tailwindcss/vite`、`@tailwindcss/postcss`、`@tailwindcss/cli`、`@tailwindcss/webpack`、`@tailwindcss/turbopack` 是同一层的三种入口，它们不实现编译逻辑，只负责把自己的构建钩子接到上面三个包上——依赖声明也印证了这一点：这几个包全部同时依赖 `@tailwindcss/oxide`、`@tailwindcss/node`、`tailwindcss` 三者。

## 3. crates/：Rust 承担扫描与候选提取

```
crates/
├── oxide/                 # 扫描器与候选提取器
│   └── src/
│       ├── scanner/       # 目录遍历、自动源检测（auto_source_detection.rs）
│       ├── extractor/     # 从文本中提取候选 class
│       ├── cursor.rs / fast_skip.rs  # 字节级高速读取与跳过
│       ├── glob.rs / paths.rs        # glob 匹配与路径处理
│       └── throughput.rs
├── node/                  # NAPI 绑定：把 Scanner 暴露给 Node.js
├── ignore/                # vendored 自 ripgrep 的 .gitignore 匹配库
└── classification-macros/ # ClassifyBytes 字节分类 derive 宏
```

`crates/oxide/src/lib.rs` 的公开导出全部围绕 `Scanner`：`scan`、`scan_files`、`get_candidates_with_positions`、`globs`、`normalized_sources`。没有 CSS 解析，没有 AST，没有代码生成——oxide 的产出是一组字符串（候选 class）和它们在源文件里的位置。「编译成 CSS」不在这里发生。

三个配套 crate 各有明确分工：

- **`ignore`** 不是自己写的，而是把 ripgrep 作者 BurntSushi 的同名 crate（v0.4.33）vendor 进了工作区，提供 `.gitignore` / `.ignore` 规则匹配。2026-08-07 合并的 PR #20397（"Don't scan ignored folders using `.gitignore` safelist setup"）让 safelist 配置下的扫描也尊重 ignore 规则，是这个 crate 的直接受益者。
- **`node`** crate 是 NAPI 3 绑定（`crate-type = ["cdylib"]`），把 `Scanner` 类的方法暴露给 JavaScript。它发布到 npm 后就是 `@tailwindcss/oxide` 包——注意不要和纯 TypeScript 的 `@tailwindcss/node` 混淆，后者依赖前者。`@tailwindcss/oxide` 通过 `optionalDependencies` 按平台分发预编译二进制（`@tailwindcss/oxide-linux-x64-gnu` 这类），安装时只拉本机那份。
- **`classification-macros`** 提供一个 `ClassifyBytes` derive 宏，用 `#[bytes(b'a', b'c')]`、`#[bytes_range(b'0'..=b'9')]` 这类标注生成字节分类代码，服务 extractor 里的高频字节判断，避免手写冗长的 match 链。

自动源检测（`scanner/auto_source_detection.rs`）值得单独一提：v4 之所以不再需要 `content` 数组，就是因为扫描器默认从项目根出发、按启发式圈定源文件范围，再用 ignore 规则排除——配置少了，代价是边界情况（比如 monorepo 里该扫哪几个包）从配置问题变成了约定问题。

## 4. packages/：编译核心与适配层

`packages/` 下 11 个子包，按角色分三组：

**编译核心与编排**：

| 包 | 职责 |
| --- | --- |
| `tailwindcss` | 编译核心。`src/` 下是纯 TypeScript：`candidate.ts` 解析候选语法，`utilities.ts` / `variants.ts` 定义工具类与变体，`css-parser.ts` 处理 CSS 文本，`compile.ts` 导出 `compile()` / `compileAst()` 入口。**零运行时依赖** |
| `@tailwindcss/node` | Node 编排层。用 jiti 加载 TS/ESM 配置与插件，用 enhanced-resolve 解析 `@import`，`optimize.ts` 调 lightningcss 做压缩与前缀处理，并维护 source map |

**用户入口**：`@tailwindcss/cli`（独立 CLI）、`@tailwindcss/postcss`（PostCSS 插件）、`@tailwindcss/vite`（Vite 插件）、`@tailwindcss/webpack`（Webpack loader）、`@tailwindcss/turbopack`（Turbopack 集成）、`@tailwindcss/browser`（浏览器内运行版本）、`@tailwindcss/standalone`（自带二进制的独立可执行形态）。

**辅助**：`@tailwindcss-upgrade`（v3 → v4 迁移工具）、`internal-example-plugin`（内部示例，见 §8）。

这里最容易误读的是主包 `tailwindcss`：v3 时代它是「CLI + PostCSS 插件 + 编译」的合体，v4 里它的 `dependencies` 是空的，`exports` 只暴露编译 API、`theme` / `plugin` 工具和几个 CSS 入口文件（`index.css`、`theme.css`、`utilities.css`、`preflight.css`）。CLI 和 PostCSS 插件各自独立成包，需要单独安装——从 v3 升级时「装完 `tailwindcss` 就能用命令行」的习惯会直接失效。

## 5. v4 与 v3 的关键边界差异

| 维度 | v3 | v4 |
| --- | --- | --- |
| 候选扫描 | JS 实现，围绕 PostCSS 上下文（`src/lib/setupContextUtils.js` 等） | Rust oxide（`crates/oxide`），源码检测自动化 |
| 源文件圈定 | `tailwind.config.js` 的 `content` 数组 | 自动检测 + `.gitignore` 规则（vendored ripgrep ignore 库），`@source` 补充 |
| 候选 → CSS 编译 | JS（主包内） | JS（主包 `packages/tailwindcss`，`candidate.ts` → `utilities.ts` → CSS） |
| CSS 解析 / 优化 | PostCSS 生态插件链 | lightningcss（Rust 内核，经 `@tailwindcss/node` 调用） |
| 配置位置 | `tailwind.config.js` | CSS-first（`@theme`、`@source`） |
| 模板语法适配 | 按配置的扩展名提取 | 扫描所有文本文件；特殊语法由 extractor 适配，如 Ruby percent literal（PR #20387）、`--default(…)` 原样输出（PR #20392） |

表格里最能纠正误解的一行是「候选 → CSS 编译」：v3 → v4 这一环没有换语言，换的是它上下游。真正下沉到 Rust 的是扫描（这一环在 v3 里恰恰是大型仓库的性能瓶颈——每个候选提取都要过一遍 JS），而编译语义留在 TS 里继续以插件、主题变量的形式演进。官方 v4.0 发布公告的措辞也印证了这个边界：只说 "ground-up rewrite"，全篇未提 Rust。

## 6. 一次构建的任务流：Vite 项目里的 Tailwind v4

把三层串起来看一次真实构建：

1. 项目里装了 `@tailwindcss/vite`，`app.css` 第一行是 `@import "tailwindcss";`，配置直接写在同一文件的 `@theme { ... }` 块里。
2. Vite 插件拦截这个 CSS 资源的构建，先通过 `@tailwindcss/oxide` 的 `Scanner` 扫描项目：oxide 遍历目录（自动源检测圈范围、ignore 规则做排除），从 HTML、TSX、Vue、Ruby 等文本文件里提取候选 class，返回字符串集合。
3. 插件拿到候选后调用主包 `tailwindcss` 导出的 `compile()`：这一步在 TypeScript 里解析候选语法、对照 `@theme` 定义的 design tokens、生成工具类，产出最终 CSS——期间通过 `@tailwindcss/node` 的 jiti / enhanced-resolve 加载用户配置和处理 `@import`。
4. 生成的 CSS 交给 `@tailwindcss/node` 的 `optimize()`，由 lightningcss 做压缩、vendor 前缀和现代语法降级（按 `browserslist`）。
5. 结果连同 source map 一起回传 Vite，注入资源管线。开发模式下文件变动时，Scanner 用 `ChangedContent` 只重扫变更的文件，多数命中缓存的重建在微秒级完成。

链路里 JS 和 Rust 各出现两次，交替进行：Rust 扫一遍（候选），JS 编一遍（CSS），Rust 的另一个项目再优化一遍（产物）。三个包的边界就是这三次交接的接口。

## 7. 性能数字怎么看

官方在 v4.0 发布时给过一组基准（以 Catalyst 项目为样本，对比 v3.4 与 v4.0 的中位数构建时间）：全量构建 378ms → 100ms（3.8 倍）；有新 CSS 的增量重建 44ms → 5ms（8.8 倍）；无新 CSS 的增量重建 35ms → 192µs（182 倍）。公告摘要的口径是 "up to 5x faster" 与 "over 100x faster"。

按本文的架构图拆这组数字，每一段都能对上位置：

- **全量与增量的主要收益来自扫描下沉**。v3 里候选提取跑在 JS，大仓库扫描耗时随文件数线性增长；oxide 用 rayon（Rust 数据并行库）并行遍历、字节级 extractor 提取，这一环的提速直接体现在总时长里。
- **192µs 的数字测的是「扫描后确认无需重新编译」的路径**，即 Scanner 重扫后候选集合未变、直接复用缓存，全程没有进编译环节。它能说明扫描层足够快，不能说明任何一次真实改样式都是微秒级。
- **不能从这组数字推出「Rust 化让一切快了百倍」**：编译核心仍在 TS，复杂工具类、自定义插件的编译路径不会有扫描层那样的数量级差异。官方对全量构建的措辞（3.5–5 倍）与增量（8 倍+）的差距，本身就是分层的证据。

## 8. 自定义内容的接入点

v4 的扩展入口几乎都在 CSS 里，先于任何 JS API：

- **让扫描器多扫一个位置**：`@source "../shared-ui";` 或 `@source not "**/legacy/**";`。扫描规则本身不可编程——不需要也不支持「注册自定义扫描器」，因为 extractor 按文本提取，任何文本格式里的合法 class 都会被扫到。想让公司内部的 `.tpl` 模板被覆盖，正确做法是一条 `@source` 指令指过去，而不是写包。
- **新增工具类与变体**：`@utility` 定义自定义工具类，`@variant` 定义自定义变体；传统 JS 插件 API（`plugin(function({ addUtilities, addVariant }) { ... })`）仍通过主包导出的 `plugin` 支持。
- **`packages/internal-example-plugin`** 是仓库里的最小 JS 插件示例，全文只有两行逻辑：`addVariant('inverted', ...)` 和 `addVariant('hocus', ...)`。它是 `private: true` 的内部包，不发布到 npm，演示的也只是变体注册这一件事——拿它当「自定义扫描」的范本会走进死胡同，那样的 API 在 v4 里不存在。

## 9. 采用顺序与迁移

适合现在升级到 v4 的场景：

- 项目已用 Vite / Turbopack / Webpack 5+，且仓库规模让 v3 的 JS 扫描成了构建瓶颈——这是 v4 收益最大的位置。
- 想把样式配置统一到 CSS-first（`@theme` / `@source` / `@variant`），去掉 `tailwind.config.js` 这一层间接。
- 从零起的新项目，没有理由再用 v3。

可以缓一缓的场景：

- 深度依赖 v3 的 PostCSS 插件链（`postcss-import` + `tailwindcss/nesting` 组合）：v4 内置了 `@import` 处理和 nesting，老的插件组合要先拆掉才能迁。
- 团队刚接触 utility-first，先在 v3 上把概念跑通也没有损失——不过新项目仍建议直接 v4，省掉一次迁移。
- 构建环境特殊、装不上预编译二进制的（`@tailwindcss/oxide` 依赖平台包），需要确认目标平台有对应的 optionalDependency。

仓库自带迁移工具 `@tailwindcss-upgrade`，会自动改写大部分配置，但三处最容易走形的位置值得逐个核对：

**配置位置搬迁**。`theme.extend` 里的颜色、间距、字体转成 `@theme { --color-*: …; --spacing-*: …; }`，`content` 数组转成 `@source`。跑完迁移工具后核对 `@theme` 里是否保留了真正被用到的变量，不要整段照搬。

**自定义插件写法**。v3 的 `plugin(function({ addUtilities }) { … })` 在 v4 仍可用，但新能力优先用 `@utility` / `@variant` 表达，JS 插件留给 CSS 表达不了的场景。

**验收不能省**。迁移不报错不等于迁移成功：跑一次生产构建，diff 迁移前后的 CSS 产物，确认没有样式丢失或意外新增的 utility；抽查几个高频 class（响应式断点、暗色模式）；对比构建耗时是否达到预期量级。注意「还在走 `@tailwindcss/postcss`」并不代表没吃到 Rust 收益——PostCSS 入口同样调 oxide 扫描，真正的检查点是产物 diff 和构建时长本身。

## 10. 入口

```text
仓库：https://github.com/tailwindlabs/tailwindcss
关键路径：
  crates/oxide                    扫描器与候选提取器（发布为 @tailwindcss/oxide）
  crates/ignore                   vendored 自 ripgrep 的 ignore 规则库
  crates/node                     NAPI 3 绑定
  packages/tailwindcss            编译核心（TypeScript，零运行时依赖）
  packages/@tailwindcss-node      Node 编排（jiti / enhanced-resolve / lightningcss）
  packages/@tailwindcss-vite      Vite 入口
  packages/@tailwindcss-postcss   PostCSS 兜底入口
  packages/@tailwindcss-upgrade   v3 → v4 迁移工具
文档：https://tailwindcss.com（仓库 README 指向）
```

读 v4 代码时，「全 Rust」的预设会持续误导——`crates/` 下没有 CSS 编译器，`packages/tailwindcss/src` 里也没有扫描循环。把三层各自落回自己的包边界，再顺着 §6 的任务流走一遍，这套架构的真实形状就清楚了：Rust 接管了数据量大、可并行的部分，语言无关语义的部分留在 TS 里继续演化。
