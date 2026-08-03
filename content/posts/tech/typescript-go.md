---
title: "TypeScript Go：微软用 Go 重写 TypeScript 编译器"
date: "2026-04-27T01:00:00+08:00"
slug: typescript-go-native-port
description: "微软将 TypeScript 编译器（tsc）从 TypeScript/JavaScript 重写为 Go 语言实现，GitHub 25k stars。解析这个 native port 的动机、架构设计、当前进度与未来影响。"
draft: false
categories: ["技术笔记"]
tags: ["TypeScript", "Go", "编译器", "微软", "性能优化", "编程语言"]
---

# TypeScript Go：微软用 Go 重写 TypeScript 编译器

2025 年，微软 TypeScript 团队将 tsc 从 TypeScript/JavaScript 重写为 Go。项目 `microsoft/typescript-go` 上线即获 25k stars，目前以 `@typescript/native-preview` npm 包提供预览版。

收益来自本地机器码、无运行时依赖、接近零的启动延迟、原生多线程。对小型项目感知不强，但百万行级别的 TypeScript 代码库中，增量构建和类型检查的耗时一直是开发体验的瓶颈。

---

## 为什么重写：编译器的自我编译困境

TypeScript 编译器自诞生以来就是用 TypeScript/JavaScript 写的——一个以"类型检查"为核心价值的工具，自身却运行在动态类型语言之上：

- **运行时依赖**：必须装 Node.js 才能跑 tsc
- **冷启动延迟**：JIT 预热前，编译器大部分时间在暖自己
- **内存开销**：JS 引擎的堆结构对长时间运行的编译器进程不友好
- **并行化受限**：事件循环模型下多核利用率低

| 维度 | TypeScript (JS) | Go |
|------|----------------|-----|
| 产物形态 | 依赖 JS 运行时 | 本地机器码，无依赖 |
| 启动延迟 | 高（JIT 冷启动） | 极低（直接执行） |
| 内存占用 | JS 引擎堆开销大 | 紧凑，GC 可调 |
| 多核利用 | 受限于事件循环 | Goroutine 原生并发 |
| 增量编译 | 受语言架构限制 | 成熟的高效实现 |

目标是将 tsc 变为可直接分发、本地执行的高效二进制工具，而非需要 JS 运行时支撑的解释型工具。

---

## 项目状态：预览阶段，功能表已铺开

截至 2026 年 4 月，TypeScript Go 仍处于预览阶段，以 `@typescript/native-preview` npm 包发布。功能覆盖情况：

| 功能 | 状态 | 说明 |
|------|------|------|
| 程序创建 | ✅ done | 与 TS 6.0 相同的文件解析和模块解析 |
| 解析/扫描 | ✅ done | 与 TS 6.0 完全一致的语法错误 |
| 命令行和 tsconfig.json 解析 | ✅ done | tsconfig 错误提示可能不如原版 |
| 类型解析 | ✅ done | 与 TS 6.0 相同的类型系统 |
| 类型检查 | ✅ done | 相同的错误、位置和消息 |
| JSX | ✅ done | — |
| JavaScript 推断和 JSDoc | 🔄 in progress | 大部分完成，部分功能有意缺失 |
| 声明文件 emit | 🔄 in progress | TypeScript 文件已完成，JS 文件未完成 |
| Emit（JS 输出） | ✅ done | — |
| Watch 模式 | 🔧 prototype | 文件变更重建，但无增量重检查 |
| 构建模式/项目引用 | ✅ done | — |
| 增量构建 | ✅ done | — |
| 语言服务（LSP） | 🔄 in progress | 几乎所有功能已实现 |
| API | ⏳ not ready | 尚未开始或距完成甚远 |

**状态说明：**
- **done**：已知无重大缺陷，可正常使用
- **in progress**：开发中，部分功能可能有效
- **prototype**：仅概念验证
- **not ready**：尚未开始

### 预览版安装

```bash
npm install @typescript/native-preview
npx tsgo  # 用法与 tsc 完全相同
```

VS Code 扩展也已上架，配置：

```json
{
    "js/ts.experimental.useTsgo": true
}
```

---

## 架构设计：从 TS 到 Go 的技术挑战

### 语法兼容性：逐字节对齐

TypeScript Go 的首要目标是 **与现有编译器输出完全相同的结果**：

- 解析阶段产生的 AST 必须与原版一致
- 类型检查的错误位置、错误信息必须完全匹配
- Emit 阶段的 JS 输出必须逐字节相同

这通过严格的回归测试套件保证——每个 PR 都会与原版 tsc 的输出做 Diff 对比，确保没有行为漂移。

### 模块解析

当前版本支持大多数标准模块解析模式，包括 Classic、Node、AMD/UMD/System、esModuleInterop 相关选项。边缘解析模式仍在完善中。

### Watch 模式和增量构建

Watch 模式（`tsc --watch`）处于原型阶段——可监听文件变化触发重建，但增量重检查尚未优化，每次变更后仍是全量类型检查。

增量构建已就绪，有 `.tsbuildinfo` 文件时能正确跳过未变更部分。

---

## 与原版 TypeScript 的关系：最终会合并

根据项目 README 的说明：

> **Long-term, we expect that this repo and its contents will be merged into `microsoft/TypeScript`.**

typescript-go 不是永久分叉，最终会合并回 TypeScript 主仓库。这意味着：

1. 用户不需要担心分裂——还是同一个 TypeScript，只是底层从 JS 变成 Go
2. npm 包只是过渡——合并完成后 `tsc` 本身就是 Go 二进制
3. 版本号延续——不会因为重写产生"TS 7"

---

## 与 TypeScript 6.0 的有意变更

项目维护了一份 [CHANGES.md](https://github.com/microsoft/typescript-go/blob/main/CHANGES.md)，记录了与 TypeScript 6.0 的**有意变更**。这些变更经过设计讨论，不是 bug。预览版中遇到与原版不同的行为，建议先查这份文档——很可能是有意为之。

---

## 性能基准

根据微软公布的数据（具体数字因项目规模而异）：

- **编译速度**：冷启动场景下比 Node.js 原版快 **5-10x**
- **内存占用**：降低约 **40-50%**
- **增量构建**：接近原版水平（watch 模式的增量重检查仍在优化中）

百万行级的企业项目中，`tsc --build` 从 30 秒缩至 5 秒。

---

## 使用场景与局限

### 适合的场景

- **大规模代码库**：性能提升最显著
- **CI/CD 流水线**：编译速度直接影响构建时间
- **Monorepo**：多包依赖链的增量构建收益明显
- **语言服务器（LSP）**：IDE 响应速度改善

### 当前局限

- **API 未完成**：编译器插件作者暂时无法使用 Go 版本
- **Watch 模式不完善**：增量重检查未完成，文件变更后响应不如原版
- **三端支持但未全优化**：Windows/Linux/macOS 部分平台的性能调优可能未完成

---

## Go 如何实现 TypeScript 的类型系统

TypeScript 的类型系统以复杂著称——协变/逆变推导、泛型约束、模板字面量类型、分布式条件类型。用 Go 实现意味着面对几个根本性挑战：

### 类型表示

Go 没有泛型模板（泛型通过反射或代码生成实现），TypeScript 的泛型系统在 Go 中需用接口加类型断言模拟，或通过代码生成在编译期展开。typescript-go 将类型表示为 Go 接口的层次结构：

```go
type Type interface {
    Kind() TypeKind
    String() string
}

type UnionType struct {
    Types []Type
}

type ObjectType struct {
    Properties map[string]Type
    // ...
}
```

这种表示方式比 JS 版更紧凑，因为 Go 的 struct 内存布局是确定的，没有 JS 对象的动态属性开销。

### 错误消息兼容

原版 tsc 的错误消息格式经过多年打磨，许多用户依赖特定格式做解析或国际化。Go 版本必须精确复现这些消息，包括位置信息、错误代码（如 `TS2322`）、建议文本。typescript-go 的做法是将错误模板编译为 Go 常量，运行时按需填充参数，避免字符串拼接的性能损失。

### 源码映射（Source Maps）

编译结果需要携带正确的源码映射，调试时才能正确映射回原始 TypeScript 源码。这部分与 JS 版本完全兼容，由同一个 Go 结构体序列化生成。

---

## 为什么是 Go 而不是 Rust

Rust 同样可编译为机器码，性能极强、内存安全，但微软选择了 Go：

| 考量 | Go 的优势 |
|------|----------|
| 团队技能 | 微软 TypeScript 团队更熟悉 Go（Azure 等项目积累）|
| 编译速度 | Go 的编译器比 Rust 快得多，更适合频繁重编译场景 |
| 工具链 | `go build`、`go test` 简单直接，降低维护成本 |
| 并发模型 | Goroutine 对编译器这种 IO 密集型任务天然友好 |
| 学习曲线 | 门槛低，社区贡献者容易上手 |

Rust 在内存控制和零成本抽象上更优，但 Go 的简洁在这个场景里更务实——TypeScript 团队的首要目标是产出与原版行为完全一致的编译器，技术选型服务于这个目标，而非追求理论最优。

---

## 时间线与未来展望

没有官方 ETA，从路线图可推断出大致节奏：

1. **近期**：完善 watch 模式的增量重检查、完成 API 层、完成 JS 文件的声明 emit
2. **中期**：所有功能达到 `done` 状态，发布稳定版 npm 包
3. **长期**：合并回 `microsoft/TypeScript` 主仓库，`tsc` 二进制默认使用 Go 版本

届时，所有 TypeScript 用户将无感地享受到 Go 版本带来的性能提升——只需升级 TypeScript 版本，无需改变任何使用习惯。

---

**相关链接：**

- GitHub：https://github.com/microsoft/typescript-go（25k stars）
- 公告博客：https://devblogs.microsoft.com/typescript/typescript-native-port/
- npm：https://www.npmjs.com/package/@typescript/native-preview
- VS Code 扩展：https://marketplace.visualstudio.com/items?itemName=TypeScriptTeam.native-preview