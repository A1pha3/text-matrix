---
title: "Zod 4.5：TypeScript 模式校验库的 AOT 编译快路径"
date: "2026-09-03T03:25:00+08:00"
slug: "zod-v4-aot-compilation-schema-validation"
github_repo: "colinhacks/zod"
source_key: "gh:colinhacks/zod"
description: "Zod 是 TypeScript 生态最流行的运行时模式校验库，4.5 引入 z.compile() 预先编译（AOT）快路径，官方报告对象、数组、联合等容器类型解析提速约 3-8 倍。本文解析其用法、编译机制与代价边界。"
draft: false
categories: ["技术笔记"]
tags: ["TypeScript", "校验", "Zod", "AOT 编译"]
---

# Zod 4.5：TypeScript 模式校验库的 AOT 编译快路径

面向在写 TypeScript 接口边界的工程师，做请求参数校验、表单校验、API 响应校验的读者。前置知识：TypeScript 基础类型，运行时与编译期的差异，ESM 模块。

读完本文能说清：Zod 解决什么矛盾；`parse` / `safeParse` / 异步变体怎么取舍；`z.compile()` 与全局 AOT 模式怎么用；编译为什么快、对什么输入快；哪些 schema 编不了、代价是什么；按自己的热点判断是否该开 AOT。

## 目录

1. 一句话判断
2. 为什么需要 Zod
3. 环境与安装
4. 核心用法：定义 schema 与三种解析
5. AOT 编译：`z.compile()` 与全局模式
6. 编译机制：它为什么快
7. 哪些 schema 编不了
8. 派生的 schema 要重新编译
9. 性能：测的是什么、能推出什么
10. 工程要点
11. 适用边界
12. 常见问题 FAQ
13. 自测题
14. 延伸

## 一句话判断

Zod 是 TypeScript 生态里最主流的运行时模式校验库：定义一个 schema，用它解析未知输入，得到强类型、已校验的结果。它把"类型系统只在编译期有效、运行时数据没有保障"这个矛盾，压进一个值里解决。

4.5（2026-08-28 发布）带来 `z.compile()`：预先编译（Ahead-of-Time，AOT）快路径。提速幅度取决于 schema 形态：官方混合负载图里，对象、数组、联合这类容器提速约 3-8 倍，结构越复杂收益越大；裸标量几乎没有提升。但提速不是免费：编译会吃掉约 7 KB gzip 的包体积，而且只对合法输入见效。下面逐步展开这个判断的依据。

## 为什么需要 Zod

TypeScript 的 `type` 和 `interface` 在编译期被擦除，运行时并不存在。可现实里大部分数据来自运行时：API 响应、表单提交、本地存储、第三方回调。这些值在编译期被当成"可信类型"，在运行时却是"不可信输入"——类型擦除之后，没人替你兜底。

Zod 用一个值（schema）同时承担校验与类型推导：定义一次，既拿到运行时校验，又让 TypeScript 自动推导出静态类型。两端同一处演化，不会出现"类型改了、校验却忘了改"的漂移。

```ts
import * as z from "zod";

const Player = z.object({
  username: z.string(),
  xp: z.number(),
});

// 校验并返回内联的强类型结果
const data = Player.parse({ username: "billie", xp: 100 });
// data 的类型是 { username: string; xp: number }
```

`Player` 的推导类型来自校验逻辑本身。改一侧，另一侧跟着变。

## 环境与安装

### 前置条件

- TypeScript 项目，能正常跑 tsc 或 bundler。
- Node.js 18+ 或现代浏览器；Zod 本身无外部运行时依赖。

### 安装

```bash
npm install zod@^4.5.0
```

验证装上了带 AOT 的版本：

```bash
node -e "const z = require('zod'); console.log(typeof z.compile);"  # => function
```

`z.compile()` 是 4.5+ 的能力，`^4.5.0` 保证拿到它。`npm ls zod` 可核对实际安装版本。

## 核心用法：定义 schema 与三种解析

### 定义 schema

基本类型、对象、数组、枚举、联合、可选、可空都有对应 API。接口是链式的、不可变的——每个方法返回新实例，不修改原对象。

```ts
const User = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  role: z.enum(["admin", "user"]),
  tags: z.array(z.string()).optional(),
});
```

### 三种解析方式

- `.parse()`：合法返回结果，非法抛 `ZodError`。
- `.safeParse()`：返回 `{ success: true, data }` 或 `{ success: false, error }`，不抛异常，适合不想用 try/catch 的路径。
- `.parseAsync()` / `.safeParseAsync()`：schema 里含 async 的 refine 或 transform 时必须用异步版本。

`.parse()` 抛出的 `ZodError` 携带细粒度问题列表，能定位到具体字段，而不是一句笼统的"校验失败"：

```ts
try {
  User.parse({ id: "nope", email: "bad", role: "guest" });
} catch (e) {
  console.log(e.issues);
  // issues 里每条都标注了 path、code、message，可直接拼给表单
}
```

## AOT 编译：`z.compile()` 与全局模式

先把三条路径摆在一起：

| 路径 | 怎么开启 | 快路径覆盖范围 |
|------|----------|----------------|
| 默认（不编译） | 什么都不做 | 无，全部走标准解析器 |
| 单个编译 | `z.compile(Schema)` | 只有这一个 schema |
| 全局模式 | 入口 `import "zod/compile"` | import 之后构造、且真被 parse 的 schema |

### 编译单个 schema

对校验频率很高的热路径（例如高频请求参数校验），4.5 提供：

```ts
const CompiledPlayer = z.compile(Player);
CompiledPlayer.parse({ username: "billie", xp: 100 });
```

`z.compile(schema)` 返回一个带编译快路径的 schema 副本，原 schema 不变。它的接口和原版一致：`parse` / `safeParse` / `extend` / `optional` 都在，推导类型、issue、报错都一样。合法输入走编译后的快路径，非法输入回退到标准解析器。

### 全局开启

把 `import "zod/compile"` 放在定义 schema 的模块之前，之后构造的 schema 首次被 parse 时自动编译：

```ts
import "zod/compile"; // 必须早于任何定义 schema 的模块
import * as z from "zod";

const schema = z.object({ name: z.string() });
schema.parse({ name: "ok" }); // 首次 parse 时编译
```

编译是惰性的，只有真被 parse 过的 schema 才会编译。这条 import 只应出现在应用入口，库代码里别用——它会让每个消费你的库的项目静默开启全局编译。

不想动源码也行，用 CLI 旗标保证它在任何模块定义前先跑：

```bash
node --import zod/compile app.js   # ESM
node --require zod/compile app.cjs # CommonJS
```

Bun 与 Nub 走各自的 preload 配置（`bunfig.toml` / `nub.jsonc`），效果等同。

## 编译机制：它为什么快

`z.compile()` 会走一遍整个 schema，产出一段扁平、无循环的校验函数，用 `new Function` 在进程内执行。比如 `{ x: number; y: number }` 会生成类似这样的片段：

```javascript
const isPoint = new Function(
  "input",
  `if (typeof input !== "object" || input === null) return false;
   if (typeof input.x !== "number") return false;
   if (typeof input.y !== "number") return false;
   return true;`,
);
```

对多数输入，跑的是直通的 `typeof` 检查和属性读取，中间没有 interpreter，快在这。对象键多、嵌套深、union 分支多的 schema，逐节点派发和分配被压平，收益越大。

当快路径判定输入非法，它返回一个 `INVALID` 哨兵，schema 回退到标准解析器——报错仍来自标准解析器的完整逻辑，字段定位是完整的。这带来两个结果：

- 非法输入要付"快路径 + 回退"两遍，编译**不**加速失败。
- refine / transform 在合法输入上跑一遍，非法输入上最多跑两遍。

把一次校验从头到尾串起来：应用入口 import 了 `zod/compile`，订单模块随后构造一个 20 键的 schema——此刻它还没被编译。第一个请求进来，`parse` 发现这是它第一次被调用，于是先编译：`new Function` 生成扁平校验函数并挂回 schema。之后的合法输入都走那段生成的代码，一串 `typeof` 检查直通返回。某天上游把金额传成了字符串，快路径返回 `INVALID`，schema 换标准解析器重跑，产出带 `path` 的完整 issues；再下一个请求合法，又回到快路径。编译只发生一次，回退按输入逐次发生。

## 哪些 schema 编不了

`z.compile()` 碰到编不了的部分会"退出编译"，原样返回 schema。比如 async refine：

```ts
const Schema = z.string().refine(async (val) => isAvailable(val));
z.compile(Schema); // 返回 Schema 本身，未编译
```

完整不支持清单：async 的 refine / transform / check；`z.xor()`；递归 schema；`z.coerce.*`；自定义 `when` 的 check；`.catch()` 传入回调的（`.catch(value)` 传常量可以编译）。

在对象 / 数组 / 元组 / record / intersection 里，某个不支持的子节点会退回标准解析器，外层结构仍保持编译。但 union 含不支持的成员或 `.catch()` 回调、或任意子树里出现 async，会让整个 schema 整体回退。此外，编码方向（`z.encode()` 与 codec 的反向转换）和异步解析入口始终走标准解析器——快路径只服务 `parse` 方向的同步校验。

想确认热点 schema 真的编上了，传 `strict` 让不能编译的直接抛错：

```ts
z.compile(Schema, { strict: true }); // 抛 ZodCompileAsyncError / ZodCompileUnsupportedError
```

async schema 抛 `ZodCompileAsyncError`，其他情况抛 `ZodCompileUnsupportedError`；两个错误只在传了 `strict` 时抛。

## 派生的 schema 要重新编译

凡是派生出一个**新** schema 的方法（`.refine()`、`.extend()`、`.optional()`、`.meta()` 等），返回的都是未编译版本。要编的是最终形态，不是中间结果：

```ts
// ❌ .refine() 的结果没有编译
const s = z.compile(z.string()).refine((v) => v.length > 1);

// ✅ 先建好完整 schema，最后再编译
const s2 = z.compile(z.string().refine((v) => v.length > 1));
```

## 性能：测的是什么、能推出什么

官方给的加速比是相对值，随 schema 复杂度、输入分布和 JS 引擎变化。官方数字有两组，要分开读。

一组是单 schema 独测：每个 schema 单独放进步骤紧凑的循环里反复跑——这是标准解析器的最优工况，比值因此普遍偏低：

| schema | 提速 |
|--------|------|
| object，5 键 | 1.8x |
| object，10 键 | 2.2x |
| object，20 键 | 5.0x |
| object，50 键 | 10.2x |
| tuple，1 项 | 2.2x |
| tuple，3 项 | 2.5x |
| tuple，5 项 | 3.0x |
| tuple，10 项 | 3.7x |

另一组是更接近真实负载的混合工作负载图：八个场景全部落在 2.8x-7.8x，容器类型（对象、数组、联合）约 3-8 倍，其中 20 键对象 7.8x、10 个对象组成的数组 5.5x、3 对象联合 5.3x。第三方 Moltar 基准（TypeScript Runtime Type Benchmarks）的 parseSafe 项目上，编译后的 Zod 与 typia 同一量级：Node 22 下约 48.4M 对 48.1M ops/s，未编译 Zod 约 14.9M，约 3.2 倍（结果站数字随每次运行浮动，截至 2026-09 查询）。趋势清楚：schema 越大越深，编译收益越大。

不能推出什么：

- 这不是"所有校验都会快 2.4 倍"。裸 `z.string()` 几乎没有提升——编译去掉的是逐节点派发与分配，单次 `typeof` 没什么可省。
- 不加速非法输入。失败路径要付快路径 + 回退两遍，可能更慢。
- 基准是项目方自报的对照数据。不同硬件、不同引擎、不同 schema 结构，绝对值会变。该不该开 AOT，基于你自己的热点 profile 决定，而不是照抄这里的数。

## 工程要点

- **包体积代价**：编译器本身是不少代码。只要调用 `z.compile()` 或 `import "zod/compile"`，它就会进 bundle，约 +7 KB gzipped（+28 KB minified）。以四个键的 object schema 为例，Zod 主包从 24.1 KB 到 31.1 KB（gzipped），Zod Mini 从 4.6 KB 到 13.2 KB。从不调用编译的 bundle 会被完全 tree-shake 掉，不付这份。
- **不可变 API**：方法返回新实例，方便复用与组合。
- **`new Function` 与 CSP**：编译依赖 `new Function`，在 CSP / 禁 `eval` 环境（如部分 edge runtime）不可用。全局模式检测到 `jitless` 会停用：

  ```ts
  z.config({ jitless: true });
  ```

  显式 `z.compile()` 是主动选择，会照常尝试产出代码；若环境拒绝 `new Function`，schema 和普通拒绝一样回来未编译。4.6 新增 `z.withParser()`：安装一个在构建期生成的解析器，绕开运行时 `new Function`，适合 CSP 严格的部署环境。
- **内置 JSON Schema 转换**：`z.toJSONSchema()` 把 Zod schema 转成 JSON Schema，方便跨语言 / 跨服务复用。
- **生态成熟**：周边表单校验、API schema、RPC 框架大多围绕 Zod 集成，`z.compile()` 保持同一套 API，迁移几乎没有改动。

## 适用边界

适合：需要"运行时校验 + 静态类型推导"同步的 TypeScript 项目；API 边界数据校验；表单与用户输入校验；高频校验路径需要提速、且 schema 偏容器型（对象 / 嵌套 / union）的场景（可评估 AOT）。

不适合：需要最小 bundle 且完全不需要运行时校验的场景（那应该用纯类型）；CSP 严格禁用动态代码执行、又无法接受关闭编译的环境（用 `jitless` 或干脆不编译）；纯基础类型、几乎无热点可言的场景——编译没有收益。

## 常见问题 FAQ

**Q：`import "zod/compile"` 会让所有 schema 自动编译吗？**
只对 import 之后构造、且真被 parse 的 schema 惰性编译。库作者别在库代码里用这条 import，它是给应用入口准备的。

**Q：非法输入会更慢吗？**
可能。失败路径付快路径 + 回退两遍。若你的场景非法输入占比高、又在意失败延迟，先实测再决定。

**Q：`z.compile()` 之后还能 `.extend()` / `.refine()` 吗？**
能，但结果是未编译的。要在完整形态上再 `z.compile()` 一次。

**Q：编译会不会改变报错？**
不会。设计上合法输入走快路径、非法回退标准解析器，issue 与未编译完全一致。

**Q：用了 `z.config({ jitless: true })` 就彻底不用编译了？**
全局模式停用，但显式 `z.compile()` 仍会尝试。只有环境拒绝 `new Function` 时才真正回退为未编译。

## 自测题

1. TypeScript 的 `type` 在运行时还存在吗？Zod 是怎么让"类型"活到运行时的？
2. `parse` 与 `safeParse` 的失败行为差别是什么？什么场景该用后者？
3. `z.compile()` 返回的是副本还是改写原 schema？对派生方法（`.extend()`）要不要再编一次？
4. 编译快路径为什么对非法输入不友好？
5. 拿 `z.compile(z.object({ a: z.string() }))` 说一句生成的校验逻辑大概长什么样，快在哪。
6. 你的高频 schema 里含一个 `async` refine。`z.compile()` 会编译它吗？怎么确认？
7. 为什么 `import "zod/compile"` 不该出现在库代码里？

## 延伸

- 仓库：<https://github.com/colinhacks/zod>
- `z.compile()` 技术说明：<https://zod.dev/blog/introducing-z-compile>
- 编译文档：<https://zod.dev/compile>
- 版本节奏：v4.5.0（2026-08-28）引入 `z.compile()`；v4.6（2026-09-09）让 `z.validate()` 直接从编译快路径回答非法输入——在编译 schema 上比 `.safeParse().success` 快至 35 倍，并新增 `z.withParser()`。当前最新 v4.6.5（2026-09-13 发布）。