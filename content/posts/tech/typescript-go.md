---
title: "TypeScript 用 Go 重写编译器：这次换的是底层，不是语法"
date: "2026-08-14T01:00:00+08:00"
slug: typescript-go-native-port
github_repo: "microsoft/typescript-go"
source_key: "gh:microsoft/typescript-go"
description: "微软把 TypeScript 编译器从 JavaScript 移植到 Go，2026 年 7 月随 TypeScript 7.0 正式发布。解析这次移植的动机、架构取舍、性能数据与生态影响。"
draft: false
categories: ["技术笔记"]
tags: ["TypeScript", "Go", "编译器", "微软", "性能优化", "编程语言"]
---

# TypeScript 用 Go 重写编译器：这次换的是底层，不是语法

TypeScript 7.0 从底层换掉了编译器：`tsc` 不再是一份跑在 Node.js 上的 JavaScript 程序，而是用 Go 写成的原生二进制。2026 年 7 月 8 日，7.0 正式发布（npm 上的最新版本是 7.0.2），官方口径是在真实代码库上全量构建通常快 8-12 倍——VS Code 那套约 150 万行的代码库，全量构建从 TypeScript 6 的 125.7 秒降到 10.6 秒。

数字之外，更值得看的是实现路线。微软选择了**移植**：Go 版本保留了原编译器的结构和逻辑，官方的说法是类型检查逻辑与 TypeScript 6.0"结构同一"（structurally identical），报出的错误、错误位置和错误消息保持一致。升级之后，你项目里"该报的错"和"不该报的错"不会变，变的是出错前要等多久。

---

## 为什么换编译器：tsc 的瓶颈在运行时

TypeScript 编译器从诞生起就用 TypeScript/JavaScript 写，一个以"类型检查"为核心价值的工具，自身却跑在动态类型语言之上。对小型项目感知不强，但代码库到了几十万行，等待就变成了每天都要付的税：

- **运行时依赖**：必须装 Node.js 才能跑 `tsc`
- **冷启动延迟**：JIT 预热之前，编译器大部分时间在暖自己
- **内存开销**：JS 引擎的堆结构对长时间运行的编译器进程不友好
- **并行化受限**：JS worker 之间只能复制对象图，而类型检查遍历的恰恰是一整张共享的类型图，所以旧版只能单核跑

| 维度 | TypeScript (JS) | Go |
|------|----------------|-----|
| 产物形态 | 依赖 JS 运行时 | 原生机器码，无依赖 |
| 启动延迟 | 高（JIT 冷启动） | 极低（直接执行） |
| 内存占用 | JS 引擎堆开销大 | 更紧凑，GC 可调 |
| 多核利用 | 实际单线程 | Goroutine 原生并发 |
| 增量编译 | 受语言架构限制 | 成熟的高效实现 |

目标很直接：把 `tsc` 变成一个可直接分发、本地执行、默认就能吃满多核的二进制。快是最直观的收益，编辑器体验摆脱单线程限制，是另一层同样重要的收益。

---

## 现状：从预览到 7.0 正式落地

这条路线走了一年多：

| 时间 | 节点 |
|------|------|
| 2025 年 3 月 11 日 | Anders Hejlsberg 撰文宣布原生移植，仓库 `microsoft/typescript-go` 开放，当时只能从源码构建 |
| 2025 年 5 月 | 预览包 `@typescript/native-preview` 上线，命令叫 `tsgo` |
| 2026 年 4 月 21 日 | TypeScript 7.0 Beta 发布 |
| 2026 年 6 月 18 日 | 7.0 Release Candidate 发布 |
| 2026 年 7 月 8 日 | 7.0 正式发布，`typescript` 包的 `tsc` 默认就是 Go 二进制 |

安装方式随之收敛。预览期用 `@typescript/native-preview`，7.0 起回归到标准包：

```bash
npm install -D typescript
npx tsc --version   # 7.0 起指向 Go 实现
```

以 README 的功能状态表为准，7.0 时的覆盖情况如下：

| 功能 | 状态 | 说明 |
|------|------|------|
| 程序创建 | done | 文件收集与模块解析同 TS 6.0，部分解析模式尚未支持 |
| 解析 / 扫描 | done | 语法错误与 TS 6.0 完全一致 |
| 类型解析 | done | 与 TS 6.0 相同的类型 |
| 类型检查 | done | 错误、位置和消息与 TS 6.0 相同 |
| JSX | done | — |
| 声明文件 emit | done | JS/JSDoc 源文件的声明 emit 有意调整，输出更贴近手写 TS 声明的风格 |
| Emit（JS 输出） | done | — |
| Watch 模式 | done | 文件监听用 Parcel watcher 的 Go 移植版 |
| 构建模式 / 项目引用 | done | 支持并行构建 |
| 增量构建 | done | 复用 `.tsbuildinfo` 跳过未变更部分 |
| 语言服务（LSP） | in progress | 基于语言服务器协议，多线程；官方标注"几乎所有功能已实现" |
| API | not ready | 7.0 未发布稳定程序化 API，计划 7.1 |

API 是当前唯一的硬缺口：`typescript-eslint`、`ts-morph`、自定义 transformer 这类依赖编译器 API 的工具，暂时只能继续用 6.0。微软给出的时间点是 7.1。

---

## 架构：同语义移植，不是推倒重来

### 行为对齐

移植的首要约束是与现有编译器行为一致：

- 解析阶段的语法错误与原版完全一致
- 类型检查报出相同的错误、位置和消息
- 用 6.0（开启 `stableTypeOrdering`）能干净编译的代码，官方的说法是在 7.0 中编译结果一致

验证靠的是微软十年积累下来的测试套件——7.0 的每一步都跑在这套用例上，防止行为漂移。这也是它敢宣称"行为不变"的底气。边界也要说清，README 明确标注了两处例外：错误消息里类型的打印样式可能有差异；对 JS/JSDoc 源文件的声明 emit 是有意调整过的。这两类变更都收在 CHANGES.md 里，见下文。

### 配置项的收窄

7.0 把 6.0 里标记弃用的选项变成了硬错误，逐项核对 tsconfig 是迁移的主要工作量：

- `module` 的 `amd`、`umd`、`systemjs`、`none` 移除，推荐用 `esnext` 交给打包器处理
- `moduleResolution` 的 `node10` 与 `classic` 移除，推荐 `nodenext` 或 `bundler`
- `target` 的 `es5` 与 `downlevelIteration` 移除，最低目标是 `es2015`
- `baseUrl` 移除，路径别名统一收进 `paths`
- `esModuleInterop`、`allowSyntheticDefaultImports` 与 `alwaysStrict` 锁定为开启
- `strict` 默认开启；`module` 默认 `esnext`，`target` 默认取 `esnext` 前一个稳定的 ECMAScript 版本

还有几处默认值的变化更容易踩到：`noUncheckedSideEffectImports` 默认开启，副作用导入（如 `import "./foo.css"`）现在会被检查；`types` 默认收窄为 `[]`，不再自动引入 `node_modules/@types` 下的所有包，老行为可以用 `["*"]` 找回。

这些配置绝大多数现代项目本来就没用，或早已迁移。真正被影响的是带着 2021 年前后旧 tsconfig 一路搬过来的项目——它们升级时遇到的多是配置报错，而不是忽然冒出来的类型问题。

### Watch 与增量构建

Watch 模式在 7.0 里重做，文件变更后能增量重检查，不再像预览期那样每次全量跑。增量构建则继续依赖 `.tsbuildinfo`，正确地跳过未变更部分。

---

## 一次构建如何穿过这套系统

把 `tsc --build` 跑在一个 monorepo 上，看它一步步做什么：

1. **程序创建**：按项目引用的依赖图找到入口文件，递归解析每个模块，建立整棵程序树。
2. **并行检查**：类型检查被拆成多个 checker，共享同一份内存；默认 4 个，可用 `--checkers` 调，对 `--build` 下的多个项目还可用 `--builders` 并行建工程，`--singleThreaded` 则完全关闭并行（适合受内存限制的 CI 或调试）。结果会汇总成同一份错误列表——错误集合与 6.0 完全一致，只是等得更短。
3. **增量落盘**：检查通过后写出 `.tsbuildinfo`，记录哪些文件、哪些检查结果没变。
4. **发射产品**：每个文件转成 JS 与 sourcemap，供打包器使用。

下次再跑，只有变更波及的文件会重新检查，其余直接从 `.tsbuildinfo` 跳过。

---

## 性能：测什么、能推出什么、不能推出什么

7.0 的数字来自真实代码库，不是合成基准。官方测的是全量构建时间（默认 `--checkers 4`）：

| 代码库 | TS 6 | TS 7 | 提升 |
|--------|------|------|------|
| VS Code | 125.7 s | 10.6 s | 11.9x |
| Sentry | 139.8 s | 15.7 s | 8.9x |
| Bluesky | 24.3 s | 2.8 s | 8.7x |
| Playwright | 12.8 s | 1.47 s | 8.7x |
| tldraw | 11.2 s | 1.46 s | 7.7x |

关于这些数字，有三点要分清：

- **收益来自两件事叠加**：机器码本身，和共享内存多线程。旧的 JS 编译器在结构上就并行不起来；Go 版本默认用 4 个 checker 共享同一份类型图，把 `--checkers` 调到 8，VS Code 的构建能从 10.6 秒再压到 7.51 秒（对 TypeScript 6 是 16.7x），Sentry 和 Bluesky 也能分别到 11.6x 和 12.1x。官方明确说并行化的收益随代码库规模放大——几个文件的小项目感受不到太多差别，十万行往上的代码库才是主场。
- **内存下降幅度比速度温和**：VS Code 从 5.2 GB 降到 4.2 GB（-18%），五个项目降幅在 6%-26% 之间，Sentry 最小（-6%），Bluesky 最大（-26%）。
- **不能推出"所有流程都快 10 倍"**。编辑器打开含错误文件从 17.5 秒降到 1.3 秒以内，是另一条独立指标；watch 场景的体感还取决于文件监听和增量策略，与全量构建数字不是一回事。

### 团队实测的数字

微软公布的基准之外，参与预览的公司也报了几组能对上号的数字：

- Slack：CI 里类型检查从约 7.5 分钟降到 1.25 分钟，合并队列时间省了约 40%
- 微软某新闻服务团队：切到 7.0 后每月省下约 400 小时等待 CI 构建
- Canva：编辑器里看到第一个错误从 58 秒降到约 4.8 秒
- Vanta：最大的几个项目里，有一例提速约 9x

编辑器端的收益同样可量化：新的语言服务（基于 LSP）相比 6.0，失败的语言服务命令减少 80% 以上，崩溃减少 60% 以上——"重启 TS server"这个习惯动作会明显变少。

---

## 与原版的关系：开发已回到主仓库

README 对定位写得明确：typescript-go 只是 7.0 发布用的过渡仓库（staging repo），原生移植完成后，开发回到 `microsoft/TypeScript` 主仓库，typescript-go 仓库本身于 2026 年 9 月归档。也就是说，到 7.0 这一步：

1. 没有分裂——还是同一个 TypeScript，只是底层从 JS 变成 Go
2. `typescript` 这个包本身发布的 `tsc` 就是 Go 二进制（npm 上的 latest 是 7.0.2），预览包只是过渡
3. 版本号延续——7.0 就是正常递进，没有因为移植另起炉灶

过渡期官方给了并存方案：新增兼容包 `@typescript/typescript6`，提供 `tsc6` 可执行文件，并重新导出 6.0 的 API。这样工具链可以继续链接老 API，命令行又用上 7.0 的 `tsc`。做法是用 npm 别名把两个包都装上：

```json
{
  "devDependencies": {
    "@typescript/native": "npm:typescript@^7.0.2",
    "typescript": "npm:@typescript/typescript6@^6.0.2"
  }
}
```

项目维护了一份 [CHANGES.md](https://github.com/microsoft/typescript-go/blob/main/CHANGES.md)，记录与 TypeScript 6.0 的**有意变更**——这些变更经过设计讨论，属于取舍。预览期遇到与原版不同的行为，先查这份文档。举一个例子：模板字面量类型的推断现在按 Unicode 码点而不是 UTF-16 码元进行，emoji 这类字符会被当作一个字符而不是两个。

---

## 用 Go 表示 TypeScript 的类型系统

TypeScript 的类型系统以复杂著称：联合类型、泛型、条件类型、模板字面量类型。用 Go 实现时，一个常见的误解要先澄清——Go 自 1.18 起就有泛型，但它的泛型模型（类型参数 + 约束）和 TypeScript 的泛型（可实例化的结构化子类型）是两回事。Go 的原生泛型承载不了 TypeScript 的类型推导，所以 typescript-go 需要自己实现一套类型表示，而不是把 TS 的每个类型映射到一个 Go 泛型。

源码里的做法是：基础的 `Type` 是一个带 flags 的紧凑 struct，字面量类型、对象类型、联合类型等具体类型通过结构体嵌入共享这套基础布局，再用 `TypeData` 接口做判别。这样每个类型节点都是定长分配，没有 JS 对象那种动态属性开销，也没有 V8 的堆压力。编译器要长时间持有海量中间结构，这个差别会累积成可观的省内存。

### 错误消息兼容

原版 `tsc` 的错误消息格式经过多年打磨，很多工具链依赖特定格式做解析和国际化。typescript-go 的办法相当彻底：错误消息直接从原版 TypeScript 的 `diagnosticMessages.json` 生成 Go 代码（见 `internal/diagnostics/generate.go`），本地化文案同样由生成器产出。同一个来源，格式天然一致；消息以生成的常量形式存在于编译产物里，运行时按需填充参数，也避开了反复字符串拼接的开销。

### 源码映射（Source Maps）

编译结果要携带正确的源码映射，调试时才能映射回原始 TypeScript 源码。sourcemap 随 emit 一并生成，序列化逻辑与 JS 版本保持兼容。

---

## 为什么是 Go 而不是 Rust

移植公告本身没有解释语言选择。从团队后续的公开访谈和两门语言的特性看，理由大致落在下面几点：

| 考量 | 说明 |
|------|------|
| 先例 | esbuild 已经证明 Go 能做出极快的 JS 工具链 |
| 内存模型 | 编译器依赖一张共享、可变、互相引用的类型图，Go 的 GC 直接支持这种结构；Rust 的所有权模型则要求重新设计数据结构，与"照原样移植"的目标冲突 |
| 并发 | Goroutine 对类型检查这种可并行任务天然友好 |
| 迭代速度 | Go 编译快、工具链简单，从 JS 翻译过来的工作量和后续维护成本都更低 |

Rust 在零成本抽象和精细内存控制上更强，但这次的目标是产出一个与原版行为一致的编译器——结构和原版越像，验证成本越低。选 Go 服务于这个目标。

---

## 谁该先用、谁可以等

这个升级的收益和约束都很明确，按团队情况对号入座：

**现在就可以上：**
- 类型检查是 CI 瓶颈的团队。`tsc --noEmit` 在 CI 里从分钟级压到秒级，收益直接叠加在每次提交上
- 大 monorepo，编辑器打开和补全经常卡顿的团队，语言服务多线程收益明显

**建议等一等：**
- 深度依赖编译器 API 的团队——`typescript-eslint` 的类型感知规则、`ts-morph`、自定义 transformer，都要等 7.1 的稳定 API
- 用 webpack loader 或复杂 emit 管道的项目，7.0 没有 API 面可用，先停在 6.0（`@typescript/typescript6` 就是为这段过渡期准备的）

迁移前在两件事上花点时间：先升级到 6.0 平滑过渡（7.0 把 6.0 的弃用项变成了硬错误），再在分支上验证一遍构建——strict 默认开启和移除的 target 可能翻出之前被压住的问题，`types` 默认收窄也可能让某些全局类型悄悄消失。

---

## 相关链接

- GitHub：https://github.com/microsoft/typescript-go
- 原生移植公告：https://devblogs.microsoft.com/typescript/typescript-native-port/
- TypeScript 7.0 Beta 发布说明：https://devblogs.microsoft.com/typescript/announcing-typescript-7-0-beta/
- TypeScript 7.0 正式发布：https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/
- VS Code 团队用 TS 7 加速迭代：https://code.visualstudio.com/blogs/2026/06/26/iterating-faster-with-ts-7
