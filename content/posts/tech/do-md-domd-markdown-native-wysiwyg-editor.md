---
title: "DOMD:把 Markdown 当成编辑模型,而不是输出格式"
slug: do-md-domd-markdown-native-wysiwyg-editor
date: 2026-08-21 21:24:00
draft: false
tags: ["markdown", "wysiwyg", "editor", "react", "ai-streaming", "crdt", "local-first", "open-source", "DOMD", "@do-md/core-react"]
categories: ["技术笔记"]
github_repo: "do-md/domd"
source_key: "gh:do-md/domd"
description: "DOMD 是一个 30 KB 的 Markdown-native WYSIWYG 编辑器内核。它最反直觉的设计是拒绝中间模型——Markdown 文本本身是编辑源真理。本文拆解它的解析器、操作流、CRDT 接缝、双层 GPL+商业许可,以及它为什么是 LLM 流式输出最干净的渲染层。"
keywords: ["DOMD", "@do-md/core-react", "Markdown WYSIWYG", "AI 流式 Markdown", "CRDT 编辑器", "ProseMirror 替代"]
---

# DOMD:把 Markdown 当成编辑模型,而不是输出格式

> 一句话:**DOMD 不把 Markdown 文本转成 AST 再转回 Markdown。Markdown 文本本身就是它的模型。**

[do-md/domd](https://github.com/do-md/domd) 是一个 30+ KB Brotli 后体积的 React Markdown 编辑器内核。它从零实现了 Markdown 解析、渲染、编辑、撤销重做、流式注入和分块加载——**没有用 ProseMirror、Slate、Lexical 这些通用富文本框架**。它的输出是 macOS 原生应用 + Web 编辑器 + Agent CLI 三件套,GitHub 530+ stars,作者 Jayden Wang,npm 包 [`@do-md/core-react`](https://www.npmjs.com/package/@do-md/core-react) 38 个版本,内核双层许可(GPL-3.0 + 商业许可 + 小实体豁免)。

但体积数字不是这篇文章的重点。重点是它做了一件 WYSIWYG Markdown 编辑器领域 **没有人认真做过** 的事:**拒绝中间模型**。

---

## 一、WYSIWYG Markdown 编辑器的老问题:中间模型的两难

过去二十年,几乎所有"所见即所得"的 Markdown 编辑器都在做同样的事:

```text
用户键入 → 转成富文本 AST → 编辑富文本 AST → 序列化回 Markdown
```

这就是所谓的"中间模型"。它的代价非常具体:

1. **拖慢**。每次按键都要在两个模型之间往返同步,大型文档卡顿。
2. **丢失**。中间模型和 Markdown 文本之间的转换不是无损的——尾随空格、原始链接、HTML 内嵌、注释、属性会悄悄被吞掉。
3. **割裂**。WYSIWYG 视图里看到的、和导出的 Markdown 源码、和你用 Git diff 看到的不一定是同一个东西。

DOMD 的反直觉方案是:**取消中间模型。Markdown 文本是源真理,编辑器直接在它上面操作。**

> "The Markdown document itself is the editing source of truth."
> ——DOMD README,标题段落原话

听起来很美。但要在 React 里实现"在 Markdown 文本上直接做所见即所得编辑",意味着你**不能依赖 contenteditable 的默认行为**(它本质上是 HTML 树编辑),必须自己接管每一个 DOM mutation event。这就是 DOMD 选择从零写解析器的原因——**它不是在 ProseMirror 之上加一个 Markdown 适配层,而是在 DOM 层之上重新定义 Markdown 解析。**

---

## 二、30 KB 怎么装下整个编辑器

先看官方给的体积数字,然后我们拆开看里面装的是什么。

| 指标 | 数字 |
|---|---|
| 内核 Brotli 后体积 | **30+ KB** |
| 运行时依赖 | 仅 `react` 和 `immer` |
| 已测文档规模 | 平滑编辑 20,000 行 Markdown |
| 流式场景 | chunk-by-chunk 渲染,中途半成品不闪烁 |

30 KB 装得下 WYSIWYG 编辑器的全部逻辑,是因为它的架构做了一个非常硬的约束:**所有解析、渲染、编辑、撤销重做、流式注入、分块加载,全部建模成内核内部的确定性状态变化。**

这意味着:

- **没有"渲染 Markdown"的独立模块**——渲染是状态变化的一个可观察副产物。
- **没有"撤销重做"的独立模块**——撤销就是回到上一个状态。
- **没有"流式注入"的独立模块**——流式就是持续的状态变化。

把可独立模块全部"折叠"进状态机,体积自然就下来了。代价是:**所有的逻辑都长在同一个状态机里,代码复用靠状态机内部组合,而不是靠 import。**

我们看一下内核的目录结构来验证这个判断:

```
.packages/@do-md/core/
├── src/
│   ├── data-parse/           # 解析器(Pure data,无 DOM 依赖)
│   │   ├── parse/
│   │   │   ├── parseBlock.ts         # 13 KB 块级
│   │   │   ├── parseInline.ts         # 50 KB 内联级(最大)
│   │   │   ├── parseTable.ts
│   │   │   ├── parseCode.ts          # 12 KB
│   │   │   └── ... (12 个块级解析器)
│   │   ├── inline-rules.ts   # 18 KB 内联语法引擎
│   │   ├── inline-rule-params.ts
│   │   └── parseMarkdown.ts  # 入口
│   ├── editor/
│   │   ├── controller/
│   │   │   └── EditorController.ts   # 103 KB(单文件)
│   │   ├── model/            # 数据层(序列化/替换/合并/光标/选区/同步)
│   │   ├── render/           # React 渲染层
│   │   ├── store/
│   │   │   ├── chain/                # Immer chain producers
│   │   │   └── index.ts              # 90 KB 单一 store 文件
│   │   └── type/
│   ├── index.ts              # 4 KB 公共导出
│   └── style.css             # 297 B
```

四个观察:

1. **最大单文件不是解析器,而是 `EditorController.ts`(103 KB)。** 这意味着 DOMD 的核心复杂度不在"Markdown 怎么解析",而在"键入时光标怎么走、删除时符号怎么折叠、回车时文档树怎么重组"。
2. **解析器是 pure data 层**(`data-parse/`),**不依赖 DOM**。这是它能做"分块加载 20,000 行文档"和"流式注入半成品 Markdown"的前提。
3. **`store/` 下全是 Immer chain producers**——所有状态变更走 Immer,Undo/Redo 是 Immer 的 patch 自动反演,不需要单独维护历史栈。
4. **`render/` 是唯一接触 DOM 的层**。它把 pure data 树映射到 React 元素,所有 mutation 由 EditorController 拦截。

这套架构有一个隐含的代价:**DOMD 内核不是 WYSIWYG 编辑器领域的"框架"——它是一个完整的、不可拆分的产品形态。** 想用它的 inline syntax 引擎自己搞一套 UI?你必须把整个 EditorController + Store + Renderer 都带上。后面我们会看到,作者没有回避这个问题,反而把它做成了产品边界。

---

## 三、Markdown-native 真正解决了什么:流式 AI 输出

如果你只用过"中间模型"那一派编辑器,你大概会以为 WYSIWYG Markdown 编辑器的痛点是光标跳、撤销栈断、图片粘贴错位。**这些 DOMD 都解决了,但它真正的杀手锏是 LLM 流式输出。**

LLM 输出 Markdown 是一段一段来的。常见的 chunk 边界长这样:

```text
"Here is a list:\n\n- item 1"
"Here is a list:\n\n- item 1\n- item 2"
"Here is a list:\n\n- item 1\n- item 2\n\n```pyt"
"Here is a list:\n\n- item 1\n- item 2\n\n```python\ndef"
"Here is a list:\n\n- item 1\n- item 2\n\n```python\ndef f():\n    return 1\n```"
```

中间状态里:`- item 1` 是一个未完成的列表项,`\`\`\`pyt` 是一个未闭合的代码块开始 fence,`def f():\n    return 1` 是一个未完成的代码块。这些状态在中间模型编辑器里会触发 re-render 抖动——因为中间模型的"已完成"判定会反复在"未完成"和"完成"之间来回切换。

DOMD 的处理方式写在 `parseInline.ts` 的注释里:

> "The kernel ingests those streams chunk by chunk and renders them live. Open fences, half-built tables, and partial lists render correctly mid-stream, then absorb their real terminators without flicker when they arrive."

具体怎么实现的?两层机制:

**第一层:解析器层**。`parseMarkdown` 接受任意半成品 Markdown 文本,产出 stable 的 `RootRenderData` 树。每个节点带 `uuid_`,每次 reparse 之后,un-touched 的子树是 reference-equal 的(因为它走 Immer)。这意味着 React 的 React.memo 会自动跳过未变化的子树,reparse 成本只与变化量成正比。

**第二层:渲染触发层**。`EditorController` 内部维护一个 `triggerReg_` 触发正则——只有当新输入 chunk 命中已注册的 inline rule 结构时,才走 immediate reparse;否则走 debounced 路径。**这条正则不是完整解析器,是"这块文本里可能有内联规则构造"的粗糙检测器。**

为什么这样设计?因为:

- **走 immediate reparse 的代价**:整棵子树 reparse + React reconcile,虽然只触碰变化节点,但仍然是 O(变化量)。
- **走 debounced 的代价**:等待下一次 reparse 之前的窗口里,UI 可能短暂显示"未格式化"状态。

DOMD 的策略是:**只在格式可能正在形成时付出 immediate reparse 的代价,其他时候用 debounce 兜底**。这种"什么时候值得付出 X 代价"的判断,在通用富文本框架里是写不出来的——ProseMirror 给你的抽象层级太高,你根本看不到下面的 token stream。

[DOMD Streaming Playground](https://www.domd.app/playground) 可以现场看到流式渲染——把任意 Markdown 文本粘贴进去,它会按字符级别"流"出来,你可以直接观察未闭合代码块、未完成列表、未闭合链接的中间状态。

---

## 四、CRDT 适配层:为什么 Yjs 必须在外面

DOMD 是 local-first 编辑器。要做多人协同,你得有 CRDT。CRDT 库最强的是 [Yjs](https://github.com/yjs/yjs),Yjs 的模型是基于嵌套 `Y.Array`/`Y.Map`/`Y.Text` 的树。

**但 DOMD 不用 Yjs 当主模型。** README 里写得很明确:

> "The editor kernel itself is CRDT-agnostic. It emits a structured operation stream for ordinary edits; an optional CRDT plugin observes that stream, translates each change into transactions on nested Yjs shared types, and maintains a mergeable `Y.Doc` replica."

也就是说:

- **DOMD 的主模型是它自己的 `RootRenderData` 树。**
- **CRDT 是可选的外挂适配器。**

它提供了一个 `renderDataOps` 接缝,精确地把 DOMD 的状态变化翻译成可序列化的 op stream:

```typescript
// editor/model/sync/renderDataOps.ts (节选)
export type RenderDataOp =
    | { op: "insert"; parent: string; index: number; node: SerializedRenderData }
    | { op: "delete"; parent: string; index: number }
    | { op: "set"; uuid: string; key: "type" | "text" | "props" | "mdSymbols" | "tagName" | "isAutoFill" | "children"; value: unknown }
    | { op: "replaceRoot"; node: SerializedRenderData };
```

每个 op 都按 `(parent uuid, index)` 或 `(node uuid)` 寻址。宿主应用(Yjs 插件、automerge 插件、自家持久化引擎)把这个 op stream 翻译成 CRDT 事务:

```text
insert/delete → Y.Array.splice(index, count, content)
set           → Y.Map.set(uuid, value)  // 宿主维护 uuid → node 索引
replaceRoot   → 全树替换(罕见,只在 resetMD / load document 时触发)
```

反向亦然:外部 op 通过 `applyRenderDataOpsToDraft` 应用到 Immer draft 上,走 immer 的结构共享——只有从根到被触碰节点这条路径上的对象会重新分配,其他子树 reference-equal,React.memo 全面命中,渲染成本 O(变化量)。

**为什么不直接把 Yjs 当主模型?**

这是这个项目最让我拍案叫绝的工程决策。理由有三层:

**理由一:WYSIWYG 编辑器的 caret/selection/IME 状态机不是 CRDT 的强项。**

CRDT 擅长的是"两台设备同时改了同一文档,合并后谁都不丢"。它不擅长描述"光标在第 3 段第 5 个字符之后、第 2 个字符之前"。这些是本地交互状态,跟协作关系不大。让 Yjs 来管本地 IME 状态会引入大量不必要的协调开销。

**理由二:DOMD 的 merge 算法是 span-level 的,不是 paragraph-level 的。**

README 里特别强调:

> "Conflict-free merging **within a paragraph** instead of treating each paragraph as a single last-write-wins value."

Yjs 的 `Y.Text` 是字符级别的 CRDT,两个用户在同一段的不同位置打字可以正确合并(因为它是基于字符位置的 CRDT)。但 Yjs 在段落级是 LWW(last-write-wins)——两个用户同时改同一段的两端,Yjs 的合并结果取决于字符级 lamport timestamp,大多数 WYSIWYG 编辑器暴露给用户的是段落级 LWW,体验差。

DOMD 的 `mergeInlineBlock.ts`(11.8 KB)+ `mergeStructural.ts`(14.4 KB)两个文件实现了**段内字符级合并**——两台设备离线改同一段的两端,合并后两端修改都保留,而不是段落级 LWW。

**理由三:产品哲学——local-first 不是协作-first。**

DOMD 的产品定位是"本地优先"(local-first),核心卖点是"5 KB 的笔记和 1 MB 的文档打开速度一样",以及"macOS 原生体验 + Quick Look 预览"。协作是锦上添花,不是核心。把 Yjs 钉死在主模型里,会让 local-first 的所有性能优化都得绕着 CRDT 的协调开销走。**把 CRDT 做成可选适配器,既给了协作能力,又不污染主模型的纯净。**

[Yjs CRDT Playground](https://www.domd.app/playground/crdt) 可以现场看到两台浏览器实例同时编辑同一文档时的段内合并行为。

**最小 Yjs 挂载示例**(README + `renderDataOps.ts` 接口推断,实际仓库未提供官方 adapter——这部分需要你自己写,大概 200~400 行):

```typescript
import * as Y from "yjs";
import { DOMD, DOMDProvider } from "@do-md/core-react";
import {
    serializeRenderData,
    deserializeRenderData,
    diffRenderData,
    applyRenderDataOpsToDraft,
    type RenderDataOp,
} from "@do-md/core-react";

// 1. 创建 Yjs 文档,宿主应用维护 root → Y.Map 的映射
const ydoc = new Y.Doc();
const yRoot = ydoc.getMap("domd-root"); // Y.Map<uuid, SerializedRenderData>

// 2. 把 DOMD 的渲染树装载到 Yjs(可选,新会话时跳过)
const initialOps: RenderDataOp[] = [];
// ... 从持久化层 / 远端拉取初始 ops 列表
applyRenderDataOpsToDraft(
    { renderData_: editorStore.renderData_ },
    initialOps,
);

// 3. 订阅本地编辑,把 diff ops 应用到 Yjs
const unsubscribe = editorStore.subscribe((newState, prevState) => {
    const ops = diffRenderData(prevState.renderData_, newState.renderData_);
    ydoc.transact(() => {
        for (const op of ops) {
            if (op.op === "set") {
                yRoot.set(op.uuid, serializeRenderData(/* 找到节点 */));
            }
            // insert / delete / replaceRoot 类似处理
        }
    });
});

// 4. 订阅 Yjs 远端更新,把外部 ops 应用到 DOMD 草稿
ydoc.on("update", (update: Uint8Array) => {
    // 从 update 解析出 RenderDataOp[],应用
    applyRenderDataOpsToDraft(
        { renderData_: editorStore.renderData_ },
        remoteOps,
    );
});
```

实际生产 adapter 还要处理光标 snapshot(`CursorSnapshot`)、presence、awareness、文本字段(`set "text"` 要走 `Y.Text` 而不是 `Y.Map`)。这是一个**接口契约清晰但实现需要打磨**的扩展点——大约 200~400 行代码,取决于你要多深的 presence/awareness 支持。

---

## 五、Inline Syntax 引擎:可扩展的 Markdown 内联语法

Markdown 工具最大的一个痛点是:**内联语法是写死的。**

要做高亮、@mention、#hashtag、wikilink、评论,传统方案是:

1. 预处理文本(在解析之前替换成占位符)。
2. fork 解析器(自己实现一个支持扩展语法的 parser)。
3. 退回原始 HTML(让用户写 `<span class="mention">@Alice</span>`)。

DOMD 在 0.6 版本做了一个激进的设计:**inline syntax 本身就是内核的一等扩展点。**

```text
==highlight==                              plain highlight
=={red}highlight==                         tinted — a positional parameter
=={.comment author="Alice"}highlight==     a semantic type with attributes
```

参数语法直接借鉴 Pandoc/Djot 的 inline-attribute 家族(Pandoc、Quarto、kramdown、markdown-it 都遵循这个约定)。

**关键设计:语法和语义是分离的。**

```text
=={.mention id=1}Alice==   ≡   <{.mention id=1}Alice>
```

`==` 这种 delimiter 本身不带任何含义。`.mention` 这种 `.word` 选择一个 **variant**——variant 是作为纯数据注册的语义类型。同一个 variant 可以挂在任何 delimiter 上,适配你产品的语气:

- 你的产品是高亮系统?用 `==`。
- 你的产品是 mention 系统?用 `@` 或 `<`。
- 你的产品是评论系统?用 `<` 或 `>>`。
- 你想自己 fork delimiter?`open` 和 `close` 接受任意标点符号。

**Variant 还可以绑定一个 React 组件:**

```typescript
{
    open: "@",
    close: "",
    tagName: "span",
    parseInner: true,
    variants: {
        mention: {
            component: MentionBadge,   // ← 一个 React 组件
            className: "mention",
            attrs: {
                "data-id": "{id}",     // 模板替换:{id} 来自参数
                href: "/users/{id}",
            },
        },
    },
}
```

`MentionBadge` 组件会拿到解析后的参数和 children,在文档里就地渲染。这样一个内联规则就**不只是样式钩子,而是产品功能的嵌入面**——可以做 issue 卡片、天气小组件、工作流控件。

`inline-rules.ts` 的编译期做了几件硬约束的安全检查:

| 检查项 | 行为 |
|---|---|
| delimiter 含字母/空白 | 警告并丢弃(必须纯标点) |
| delimiter 含 `` ` ``、`\`、`{`、`}` | 警告并丢弃(代码域/转义/参数语法主权) |
| tagName 不在白名单(`b/i/s/em/strong/del/u/mark/sub/sup/kbd/ins/small/abbr/cite/q/var/span`) | 警告并降级为 `span` |
| attrs 含 `on*` 事件处理器 | 编译期不可达(白名单拦截) |
| `href` 是 `javascript:` URL | 渲染时丢弃 |

也就是说,**用户传入的 inline rules 永远不能执行任意 JS、不能注入未授权 HTML 标签、不能绕过代码域主权。** 这对一个"内核暴露给宿主任意扩展点"的系统来说是底线安全。

---

## 六、双层许可:GPL-3.0 + 商业许可 + 小实体豁免

DOMD 的许可策略值得单独拆开说,因为它精确反映了一个事实:**Markdown 编辑器内核是高价值、低天花板的产品。**

```text
┌────────────────────────────────────────────┐
│ 应用层 (Application Layer)                  │
│ macOS app · Web app · helper libraries    │
│ 许可证: MIT                                │
├────────────────────────────────────────────┤
│ 内核层 (Editor Kernel)                     │
│ @do-md/core-react                          │
│ 许可证: GPL-3.0-only + 额外授权           │
│  · 小实体豁免:营收<100万美金 或 融资<200万美金│
│  · FOSS 例外:与 MIT/Apache/BSD/MPL 等组合 │
│  · 商业许可:联系 effyouapp@gmail.com      │
└────────────────────────────────────────────┘
```

**三层规则:**

**第一层:小实体豁免(Small entity exception)**。个体、非营利、或营收 < 100 万美金且融资 < 200 万美金的营利实体,可以**把内核链接进非 GPL 软件并按自己的条款发布**,只要:

- a. 对内核本身遵守 GPL(公开源代码)。
- b. 保留所有版权声明、license、归属,一起发布 LICENSE 和 LICENSE-EXCEPTIONS。
- c. 不在未经书面许可的情况下用程序名或作者名做背书。

而且这条豁免**不可撤销**:一旦某个版本带这个文件发布,该版本永远在这些条款下可用。你也不需要追踪——只要你符合条件,你的"接收方"能否继续在非 GPL 条款下转售,取决于**他们自己**的资格,不取决于你。

如果你**不再**符合条件(比如突然融资超过 200 万美金),你有 90 天宽限期去补 GPL 合规或谈商业许可。**已经发出去的版本永远在原条款下可用。**

**第二层:FOSS 例外(FOSS license exception)**。你可以把内核和以下许可证之一的"独立作品"组合,把整个作品按那个独立作品的许可证发布:

- Apache 2.0、BSD-2-Clause、BSD-3-Clause、EPL-2.0、ISC、MIT、MPL-2.0、zlib

大多数这些许可证本来就和 GPL 兼容——可以组合在 GPL 下发。这个例外增加的是:**可以按独立作品自己的许可证发,不是 GPL**。但是 GPL 仍适用于内核本身。

**第三层:商业许可(Commercial licensing)**。如果你既不符合小实体豁免、又不想按 GPL 发,买商业许可即可。

**最重要的"不要误解"指南**(LICENSE-EXCEPTIONS.md 末尾有原文):

> "Trying it, building with it, running it internally — no obligations at all. The GPL attaches only when you convey. **Shipping a web app that loads this kernel — that *is* conveying**: your build reaches your users' browsers."

这一句点破了最常被误解的点:**你写了个 SaaS,前端用 React 加载 DOMD 内核的 npm 包,这就已经是 convey 了**——你的前端进入了用户的浏览器。如果你不满足小实体豁免也不满足 FOSS 例外,你整个前端都得 GPL。

作者还在 README 里直接补了一句:

> "Shipping a web app that loads it in the browser counts."

这是非常清醒的产品边界:**GPL 不是为了刁难用户,而是为了强制大型玩家(融资过 200 万或营收过 100 万美金的公司)要么开源要么付费,让中小开发者免费用上能用的内核。** 内核本身在 npm 上公开可下载可试用,本地开发、内部测试、build pipeline 跑通都不触发 GPL。

CLA(Contributor License Agreement)的存在让这一切可执行:**贡献者保留自己代码的版权,但授予项目方在商业许可中使用的权利。** 没有 CLA,贡献过的代码将来无法纳入商业许可版本,只能留在 GPL 版本里——这对一个依赖商业许可养活的项目是致命的。

这种"双层 + 豁免 + CLA"的组合,在 WYSIWYG 编辑器领域非常少见。CKEditor 用一种,Ghost 用另一种,TipTap 用一种,DOMD 用的是**最接近"项目方与开源社区利益一致"的版本**:你小,我免费;你大,你付钱;你开源,我们组合得更灵活。

---

## 七、和 LLM 流式输出的真实契合

如果你在 2026 年做一个 LLM 驱动的产品——AI 写作、AI 笔记、AI 客服、AI 教育——你大概率需要一个"AI 流式输出 + 用户在线编辑"的混合场景。

这个场景的典型需求:

1. AI 输出 Markdown 流,用户能实时看到中间状态。
2. 用户中途停下来在 AI 没写完的地方改一个错别字。
3. AI 继续输出,得无缝接上用户的修改。
4. 多人协作(产品经理、设计师、运营)在同一份文档上跟 AI 协同。
5. 文档得能存进 Git(因为产品技术文档需要 diff/review),所以存的就是 Markdown 源码,不是某个私有 AST。

DOMD 是我目前见过的**唯一一个**同时满足这五条需求的开源内核:

| 需求 | DOMD 的实现 |
|---|---|
| 1. 流式渲染中间状态 | parseMarkdown 接受任意半成品,`triggerReg_` 控制 reparse 触发 |
| 2. 用户中途修改 | 编辑即 Markdown 文本 mutation,模型就是文本 |
| 3. AI 继续接上 | AI 看到的还是 Markdown,接上是文本拼接,无需额外转换 |
| 4. 多人协作 | 可选 Yjs 适配器,段内字符级合并 |
| 5. 存进 Git | Markdown 文本就是源真理,`toMarkdown` 序列化无丢失 |

如果你今天要从零做一个 AI-native 的协作笔记产品,你**至少**绕不开这套需求栈。传统方案是 ProseMirror + Yjs + 自定义 Markdown 适配层——这套方案能做,但你得维护 ProseMirror schema、Markdown ↔ AST 双向转换器、Yjs 协作层、AI 流式适配层。**DOMD 把前三层合并成一个内核,只让你写 AI 流式适配层。**

---

## 八、版本节奏与产品状态

我整理了 npm 上的 38 个版本(截至 2026-08-21):

```text
0.2.5  2026-06-16  首次公开
0.2.6  2026-06-16  +1 天,bugfix 节奏
0.2.9  2026-06-24  +8 天
0.2.12 2026-07-22
0.4.0  2026-08-01  +10 天,版本号跨越
0.5.0  2026-08-05
0.8.3  2026-08-07  inline rules v2 重写
0.9.0  2026-08-10  一周一迭代
0.10.0 2026-08-18  GPL 切换
0.11.0 2026-08-20  小实体豁免登场
0.11.2 2026-08-21  最新
```

38 个版本在 ~2 个月内发完,基本是 daily/weekly 的迭代节奏。8-07 那个 0.8.3 是 `inline rules v2` 重写——前面 18 KB 的 inline-rules.ts 是这次重写的产物。8-18 0.10.0 是 GPL 切换——之前的版本是 PolyForm Noncommercial 1.0.0,8-18 之后切到 GPL-3.0 + 额外授权。这个节奏说明项目**仍在快速演进**,AI 流式协作这个方向的产品形态尚未稳定。

仓库本身也有几个值得注意的数字:

- **530+ stars** · **32 forks** · **0 open issues**(是的,0!)
- **1497 KB** 仓库大小(主要是 macOS app 的 Tauri binary resources)
- **TypeScript** 主语言
- 创建日期 **2026-05-25**

0 open issues 在一个高频迭代的 TypeScript 项目里是极其罕见的——要么说明 issue tracker 流转非常高效,要么说明大部分用户是直接用 npm 包提 issue 而不是 GitHub Issues。考虑到 GitHub Issues 已经被打开但项目方的 issue 跟踪可能在 Discord/邮件,这个数字本身就是一个产品成熟度信号。

---

## 九、它不适合谁

为了不让你读了半天兴冲冲去集成然后踩坑,明确说边界:

**不适合一:你需要 Slate/ProseMirror 的开箱即用插件生态。** Slate 有 100+ 社区插件(表格、数学公式、Markdown 快捷键、协同光标),DOMD 是封闭内核,你要么接受它的扩展点,要么 fork 整个内核。这不是 bug,这是产品边界。

**不适合二:你需要 WYSIWYG 编辑非 Markdown 内容。** DOMD 的核心卖点是 Markdown 是源真理。如果你的产品需要编辑 JSON、YAML、reStructuredText、AsciiDoc,DOMD 不是给你做的。

**不适合三:你不能接受 GPL 的传染性。** 内核是 GPL。如果你的产品整体要按 MIT/Apache/BSD 等更宽松的许可证发,且你公司营收 ≥ 100 万美金 或 融资 ≥ 200 万美金,你需要买商业许可。**这是设计,不是 bug**——DOMD 的整个商业模式就建立在这条边界上。

**不适合四:你期望"Markdown 适配层是免费的、独立的"。** Markdown ↔ 富文本 适配层是 DOMD 内核的一部分,不能单独提取。整个内核(~30 KB)作为一个不可拆分的单元分发。这是产品形态决定的事实,不是技术债务。

---

## 十、对 AI 时代的编辑器选型的启示

WYSIWYG 编辑器领域过去 20 年沉淀的"中间模型"范式,是基于一个隐含假设:**人类编辑为主、机器输出为辅。** 在这个假设下,中间模型是合理的——人类编辑体验优先,机器输出退化为"导出为 Markdown"按钮。

LLM 流式输出把这个假设翻转了:**机器输出为主、人类编辑为辅。** 整个 UX 设计、AI agent 设计、AI 协作工具设计都开始围绕"机器输出 → 用户中途修改 → 机器继续输出"这个循环。

DOMD 是**第一个把"机器输出为主"作为一等公民的内核**——它没有中间模型,所以没有"机器输出需要先转换成中间模型再让用户编辑"的延迟;它是 Markdown-native,所以"机器输出的就是用户看到的,用户改完就是机器下一轮的输入";它的 CRDT 适配器在外面,所以你不需要为协同付出额外的内核改造代价。

如果你正在评估 2026 年的编辑器选型——尤其是在 AI 协作、AI 笔记、AI agent 产品方向——**DOMD 是少数值得从内核层评估的项目,而不是把它当成另一个"npm 包"装上试试。**

---

## 参考链接

- 仓库:[github.com/do-md/domd](https://github.com/do-md/domd)
- npm 包:[@do-md/core-react](https://www.npmjs.com/package/@do-md/core-react)
- Web 在线版:[domd.app/editor](https://www.domd.app/editor)
- Streaming Playground:[domd.app/playground](https://www.domd.app/playground)
- CRDT Playground:[domd.app/playground/crdt](https://www.domd.app/playground/crdt)
- Real-time Sync Playground:[domd.app/playground/live](https://www.domd.app/playground/live)
- Input Playground:[domd.app/chat](https://www.domd.app/chat)
- LICENSE-EXCEPTIONS:[.packages/@do-md/core/LICENSE-EXCEPTIONS.md](https://github.com/do-md/domd/blob/main/.packages/%40do-md/core/LICENSE-EXCEPTIONS.md)
- CONTRIBUTING / CLA:[CONTRIBUTING.md](https://github.com/do-md/domd/blob/main/CONTRIBUTING.md)