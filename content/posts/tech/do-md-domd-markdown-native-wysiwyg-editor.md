---
title: "DOMD 把 Markdown 当编辑源真理：逐项核对这条口号"
slug: do-md-domd-markdown-native-wysiwyg-editor
date: 2026-08-21 21:24:00
lastmod: "2026-09-26T01:05:00+08:00"
draft: false
tags: ["markdown", "wysiwyg", "editor", "react", "ai-streaming", "crdt", "local-first", "open-source", "DOMD", "@do-md/core-react"]
categories: ["技术笔记"]
github_repo: "do-md/domd"
source_key: "gh:do-md/domd"
author: text-matrix
description: "DOMD 的内核 @do-md/core-react 把 Markdown 文本当作编辑源真理，不做中间模型。本文在 v0.10.0 源码与 npm 0.13.1 产物上逐条核对：源真理条款在往返里兑现到哪一步、30 KB 的实际口径、官方 Yjs 适配器在哪、流式写入的真实入口，以及双层许可的版本分界。"
keywords: ["DOMD", "@do-md/core-react", "Markdown WYSIWYG", "AI 流式 Markdown", "CRDT 编辑器", "Yjs 协同", "GPL 双许可"]
---

DOMD 是一个用 Tauri 打包的 macOS Markdown 编辑器，网页版和它共用同一个内核。内核发布在 npm 上，叫 [`@do-md/core-react`](https://www.npmjs.com/package/@do-md/core-react)。它对外最主要的一句话是：

> WYSIWYG editing happens directly on Markdown. The Markdown document itself is the editing source of truth.

所见即所得直接作用在 Markdown 上，文档本身就是编辑的源真理，没有另一份需要随时对齐的内部模型。这句话在很多项目里是宣传语，在这里却是一条能逐条验证的工程约束：它同时写进了解析器、撤销栈、协同接缝和批量替换接口的设计里。剩下的那些边角，只有跑起来才看得见。

本文的对齐基准是 2026-09-26 拉到的 `main`（提交 `1780d7f`，已打标签 `v0.10.0`），以及从 npm 装到的 `@do-md/core-react` 0.13.1。文中凡写"实测"的，都是我在本机（Apple M4、Node.js v26.3.0）跑出来的输出，对应命令一并给出，可以复算。

## 目录

1. [系统地图：四层各自是谁](#系统地图四层各自是谁)
2. [源真理条款能兑现到哪一步](#源真理条款能兑现到哪一步)
3. [一次按键穿过哪些层](#一次按键穿过哪些层)
4. [体积数字的三种口径](#体积数字的三种口径)
5. [撤销栈在一层通用状态库里](#撤销栈在一层通用状态库里)
6. [流式写入的真实入口换了](#流式写入的真实入口换了)
7. [大文档分块与它的两次事故](#大文档分块与它的两次事故)
8. [无头运行与命令行接口](#无头运行与命令行接口)
9. [协同：官方 Yjs 适配器在应用层](#协同官方-yjs-适配器在应用层)
10. [内联语法扩展点与它的告警盲区](#内联语法扩展点与它的告警盲区)
11. [双层许可与 0.11.0 这条线](#双层许可与-0110-这条线)
12. [一千多条断言里有两条是红的](#一千多条断言里有两条是红的)
13. [该怎么用这个项目](#该怎么用这个项目)
14. [下一步读哪几段代码](#下一步读哪几段代码)
15. [五个自测题](#五个自测题)
16. [参考](#参考)

## 系统地图：四层各自是谁

先划清边界，后面所有争论都发生在这几条缝上。

| 层 | 位置 | 许可证 | 职责 |
|---|---|---|---|
| 应用 | `app/` `features/` `common/` `src-tauri/` | MIT | Next.js 16 网页版、Tauri macOS 壳、菜单与持久化 |
| 应用插件 | `plugins/`（含 `collaboration/`） | MIT | 协同、工具栏、自定义渲染，消费内核的公开接缝 |
| 内核 | `.packages/@do-md/core/` | GPL-3.0-only + §7 附加权限 | 解析、渲染、编辑、撤销、流式注入、协同接缝 |
| 状态底座 | `.packages/@do-md/zenith/` | MIT（独立发布于 `@do-md/zenith`） | Immer 之上的通用 store、历史中间件、订阅选择器 |
| 内核插件包 | `.packages/@do-md/plugins/` | MIT | 命令、目录、搜索、虚拟滚动 |

两处容易看错的地方。第一，`plugins/collaboration/` 是应用层代码，Yjs 依赖挂在这里，内核里搜 `yjs` 只会命中 `renderDataOps.ts` 的一句注释——内核确实不认 CRDT 库。第二，版本号有三套各走各的：仓库根 `package.json` 是 0.10.0，内核 `package.json` 是 0.13.0，npm 上 latest 是 0.13.1。讨论任何行为都得先说清用的是哪一套。

## 源真理条款能兑现到哪一步

"文本是模型"最直接的检验方式不是读代码，而是喂一批形状奇怪的 Markdown，看序列化回来的字符串还差多少。我在 0.13.1 上跑了 15 例：

```text
SAME  行尾空格        "para with trailing   \n\nnext\n"
SAME  自动链接        "see <https://example.com> ok\n"
SAME  裸 HTML          "<div class=\"x\">hi</div>\n\nbody\n"
SAME  HTML 注释        "<!-- note -->\n\nbody\n"
SAME  引用式链接      "text [ref][1] here\n\n[1]: https://e.com \"t\"\n"
SAME  Setext 一级标题 "Title\n=====\n\nbody\n"
SAME  嵌套列表        "- a\n  - b\n    - c\n"
SAME  波浪号围栏      "~~~js\nlet a=1\n~~~\n"
SAME  引用块续行      "> a\nb\n"
SAME  脚注            "note[^1]\n\n[^1]: foot\n"
SAME  裸与号和尖括号  "a & b < c > d\n"
SAME  词内下划线      "snake_case_name here\n"
SAME  转义的 ==       "\\=\\=hi\\=\\=\n"
DIFF  未对齐的表格    "| a|b |\n|-|-\n|1|2\n|"  → 重新补白对齐
DIFF  松列表          "- a\n\n- b\n"          → "- a\n- b\n"
```

多数刁钻形状原样回来，两处会变。表格列被重新补白，这一条内核自己写在文档里；松列表被收紧，也就是 CommonMark 判定为 loose 的列表，重新序列化时丢掉条目之间的空行，渲染语义随之改变。

所以这句口号的准确读法是：**文本决定内容，不保证字节**。它是源真理，不是逐字还原承诺。任何"编辑器改完再存回去必须和 git 里那份一模一样"的需求，都要先按自己那批文档测一遍。

## 一次按键穿过哪些层

把一次输入拆开看，能看清这几层的分工。以在段落末尾敲 `#`、空格、`x` 为例：

```text
浏览器 beforeinput / input
  → EditorController：按 inputType 决定接管还是放行
  → EditorStore：pendingInput_ 暂存，命中触发条件就立即重解析
  → store/chain：一次 produce 算完块内替换、光标、补白符号
  → mergeInlineBlock / mergeStructural：把新解析出的块并进旧树
  → immer：产出 patches 与 inversePatches
  → diffRenderData：对照引用算出最小 op 流，发给宿主与协同端
```

接管判断写在 `editor/controller/lib/checkDomNeedRender.ts` 里，是一串或运算：列表与引用前缀、围栏开头、复选框形状、标题正则 `/^\s*(#{1,6})\s+.?\s*$/u`、内置内联语法正则、行首 URL，最后才是内联规则的触发正则。其中那条标题正则刻意只放行 0 到 1 个后继字符，注释给了原因。这段判断每次按键都要跑，若把尾部写成 `(.*)`，光标落在已成形的标题里时可见文本仍以 `# ` 开头——这一块就会在每次按键时重解析一遍。

内联规则的触发正则由编译期生成，注释就写在 `data-parse/inline-rules.ts` 的字段声明上：

```text
/**
 * Render-trigger regex for EditorController.checkRender_: a rough "this block may
 * contain a rule construct" test that decides immediate reparse vs the
 * debounced pending path. Loose on purpose — a false positive just costs
 * one reparse (the parser itself is the source of truth).
 */
triggerReg_: RegExp | null;
```

生成的形状是把每条规则拼成 `open` 加可选 `{…}` 捕获加内容加 `close`，规则之间用或分支连起来；与内置语法撞车的分隔符（`*`、`![`、单字符 `[` 和 `<`、`~~`）会把捕获段变成必选，因为不带 `{` 时规则本来就不可能生效。误报只多花一次重解析，代价由解析器兜底。

没命中这些条件时走防抖路径：`debounceApplyPendingText_` 是一个 400 毫秒的 RAF 防抖，把这段时间内的连续输入合并成一次模型写入。这就是"编辑即状态变化"落到实处的地方，也是内联规则必须自带触发正则的原因。注释里还记了一次真实事故：规则语法要等防抖兜底才成形，此前一直是字面文本，成形那一刻光标跳回错误位置。代码注释管它叫 "jjj jumped into the span" 事件。

## 体积数字的三种口径

README 顶部的徽章写的是 `core Brotli 30+ KB`。0.13.1 的实测数据：

```text
入口产物            原始        Brotli（质量 11）   Gzip（9 级）
ESM 入口         161,736 B        38,613 B        44,428 B
CommonJS 入口    160,821 B        38,427 B        44,304 B
样式             9,801 B          2,014 B          2,333 B
```

"30+ KB"说的是 ESM 产物的 Brotli 体积，当前落在 38 KB 这一头。构建脚本自带一个 `reportBrotliSize` 插件，用最高质量的 Brotli 在构建日志里打印每个产物的尺寸。注释把理由写得很明白：Vercel、Cloudflare、nginx 实际发给浏览器的是 Brotli，只报 gzip 是错的口径。这段自测每次构建都会跑，不是我一次性取样。

另一个常见误读是"依赖只有 React 和 Immer"。发布包没有 `dependencies` 字段，三个运行时要求全在 `peerDependencies`：`immer ^10.2.0 || ^11`、`react >=18`、`react-dom >=18`，其中 `immer` 被显式标成非可选。文档还提醒一句：store 会共用宿主应用的 Immer 实例，两边版本对不上是要当回事的。

## 撤销栈在一层通用状态库里

内核没有自己写历史栈，它复用 `@do-md/zenith`——同一位作者维护的 React 状态库，独立发布于 npm，最新 2.0.3。它的自我定位是"Engineering-grade React state management powered by Immer"。`EditorStore` 继承其中的 `ZenithStore`，撤销能力来自一处装配：

```typescript
const { undo, redo } = withHistory(this, {
    maxLength: 30, // max history length
    debounceTime: 300, // debounce window (ms)
});
```

中间件保存的是 immer 的 `patches` 与 `inversePatches` 数组，按 `maxLength` 裁剪、按 `debounceTime` 合并。这两个数字是行为，不是调优口味。实测：40 个字符逐个插入、每次间隔 520 毫秒，然后一路撤销。撤到 32 次时只有 31 次真的让文本变短，最后停在 9 个字符——最早那批编辑已经不在栈里。反过来，把 5 个字符连着快速打完，一次撤销就全没了：它们落在同一个防抖窗口里，被并成一步。

但协同 op 流消费的并不是这些 patch。`renderDataOps.ts` 的头注释给了原因：

```text
Note: this does not consume immer patches — for a splice in the middle of
an array immer emits a noisy "replace every following index" patch set,
whereas a reference diff is immune (reference == identity).
```

数组中部一次删除会让 immer 报出"其后每个下标都被替换"的噪声 patch，而引用相等就是身份相等，按引用做树差分的 `diffRenderData` 不受影响。撤销走 patch 反演，发给协同端走引用差分，两套机制各用各的。

公开的入口模块里还留着一处历史痕迹：`EditorStoreApi` 是 `EditorStore` 的类型别名，注释说明这个名字来自闭源时代手写的声明文件，为了让宿主代码不必改名而保留下来。

## 流式写入的真实入口换了

大模型逐块吐 Markdown，切点经常落在语法中间。内核文档给的流式写法是：用 `useEditor()` 拿到控制器，然后对每个分片调一次 `aiInsertInCursor`。0.13.1 的 README 里，示例和接口一览两处都还这么写。

但这个方法在当前产物里不存在。我解包比对了几个版本：

```text
0.9.3   tarball 的 index.js 与 index.cjs 各有 1 处 aiInsertInCursor
0.10.0  同上，仍在
0.11.0  两份产物 0 命中，只剩 index.d.ts 的两处注释
0.11.2  同上
0.13.1  同上
```

0.11.0 正是内核源码进公开仓库后发布的头一版，方法就是在这一步从产物里消失的，两处文档却没跟着改。当前源码里也搜不到它的定义，只剩几段注释还在提这个名字。

实际可用的入口是 store 上的 `insertText`。网页版的聊天窗、playground 的流式演示、macOS 编辑器都在用它：

```tsx
// features/chat/components/assistant-message.tsx（节选）
const put = (chunk: string) => {
    if (!seeded) {
        store.resetMD(chunk);
        seeded = true;
    } else {
        store.insertText(chunk);
    }
};
```

第一段用 `resetMD` 建立基线，其后每块走 `insertText`，出错时也走同一条路径把提示写进文档。playground 的驱动脚本额外做了两件事：块大小随机，以及极速模式下每 32 块 `await sleep(0)` 让浏览器有机会绘制。

中间态到底长什么样，可以直接打印模型形状。我把一段含列表和 Python 代码块的文本按 9 块喂进去：

```text
chunk 4 尾部 "``"        → … | P(Plain) | EmptyP(Br)
chunk 5 收到 "`python…"  → … | Pre(MdHideSymbol,HideSecondLine,PreCode,
                            HideSecondLine,MdHideSymbol) | EmptyP(Br)
最终                      toMarkdown() 与输入逐字节相等
```

未闭合的围栏在补全前是一段普通文本，闭合符号一到就变成真正的代码块，而不是先闪出一个空代码块再改内容。这与 README 的说法一致，而且是同一次运行的收尾结果：九块喂完，`toMarkdown()` 拿回的正是原串。

## 大文档分块与它的两次事故

`EditorStore` 构造时如果 `initMd` 超过 500 行，就只同步灌入前 500 行，剩下的异步追加。这个 500 是源码里的 `INITIAL_CHUNK_LINES`。实测：1200 行构造完，同步可见 500 行、`isLoadingChunks` 为真，16 毫秒后 1200 行齐备，`toMarkdown()` 与输入逐字节相等。

要同步拿全文，做法是构造时传空串再调用 `resetMD(fullText)`。

这个分块设计背后有过一次数据丢失。`scripts/verify-load-gate/run.mts` 的注释把事故写得很清楚：加载期间 `toMarkdown()` 返回的是文件前缀，自动保存和脏内容上报会把这个前缀落盘，把文件截断；更狠的是异步语法高亮到位后触发 `resetMD(toMarkdown())`，会取消尚未跑完的追加分块，截断从此固定下来。

另一条事故出在协同上：Yjs 的 `Y.Array.insert` 在附加进文档前会把内容按元素展开成函数实参，10 MB 文档约 19 万个顶层块，直接抛 `RangeError: Maximum call stack size exceeded`，文档根本进不了协同状态。修法是分批插入，`scripts/verify-collab-scale/run.mts` 用旧阈值两侧的块数各压一遍，确认 Y 树与序列化树完全对应。

这两条都不是为了覆盖率补的测试，而是把事故机理写进了脚本头。判断一个项目靠不靠谱，这类注释比徽章有用。

## 无头运行与命令行接口

内核可以在裸 Node.js 里跑，不需要 DOM、React 或 JSDOM。文档把这条路径的用途说得很具体：宿主在服务端起一份自己的 store 改文档，产出的 op 流再应用到浏览器里那份 store 上。改动归属、撤销和光标都会保留。下面是我实跑通的最小例子：

```ts
import { EditorStore } from "@do-md/core-react";

const s = new EditorStore({ editable: true, initMd: "# Hi\n\n- one\n- two\n" });
const ops = [];
const off = s.subscribeRenderDataOps((batch) => ops.push(...batch));
s.replaceText({ search: "one", replace: "ONE" });
off();
// "# Hi\n\n- ONE\n- two\n"，ops 长度 2：一条 delete、一条 insert
```

受支持的无头面包括构造与全部注入点、文档原语（`toMarkdown`、`resetMD`、`insertText`、`replaceText`、`replaceRanges`、`getTitle`）、同步接缝（`subscribeRenderDataOps`、`getRenderDataSnapshot`、`applyExternalRenderData`、`applyExternalRenderDataOps`、`flushPendingInput`、`getCursorSnapshot`、`subscribeCursorChange`）和三个序列化辅助函数。

`replaceRanges` 是这里最值得单独讲的接口。它同时服务两种场景：大模型习惯的精确文本搜索替换，以及外部差异回填。语义上有三条我实测确认过：

- 偏移一律相对调用前的 `toMarkdown()` 全文。前面的替换改变了长度，后面那条仍然按原偏移落点，不会被推着走；
- 失败按条计，越界、互相重叠、搜不到或有歧义只让那一条带原因失败，其余照常生效；
- 整批算一个撤销步——撤销一次就回到两条替换都没发生的状态。

一条值得先知道的边界：编辑列表项时，被改的那个 Ul 节点会换 uuid，而同一文档里没被碰到的标题、分隔与尾块 uuid 全部不动。`subscribeRenderDataOps` 为此只报出一条 delete 加一条 insert。这与合并模块自己声明的适用范围一致——段内合并只覆盖"同类型单块"的普通打字路径，"块类型变了、块被拆开、列表项"这几种都退回整块替换。

另一条入口是命令行工具 `domd-cli`，一个 368 行的 Rust 程序（`src-tauri/src/bin/domd_cli.rs`），通过 Unix 域套接字驱动桌面应用。子命令一共 9 个：`new`、`open`、`list`、`selection`、`content`、`insert`、`save`、`close`、`focus`。帮助文本里有两句约定值得抄走：

```text
Streaming is just repeated `insert` calls — there's no separate stream mode.

Output convention: single-value commands print plain text;
structured commands print JSON. Errors → exit nonzero + JSON on stderr.
```

## 协同：官方 Yjs 适配器在应用层

先把一件事说清楚：官方 Yjs 适配器是有的，只是没发到 npm。`plugins/collaboration/` 下两套实现都基于 Yjs：

```text
crdt-sync/       151 + 106 + 326 = 583 行
  index.ts       把 op 流镜像进一个 Y.Doc；离线合并与可合并持久化
  y-mapping.ts   SerializedRenderData ↔ Y 结构的共用映射层
realtime-sync/   2,230 行（含 WebRTC 传输与远端光标）
```

`y-mapping.ts` 把映射写在一行注释里：

```text
node     = Y.Map{type,uuid,text?,mdSymbols,props,tagName?,isAutoFill?,children?}
children = Y.Array<Y.Map>
props、mdSymbols 按整值 LWW
顶层键名 = "domdRenderData"
```

这套映射被离线合并与实时协同共用。

内核侧交给宿主的接缝是一份稳定的 JSON 契约，四种 op：

```typescript
export type RenderDataOp =
    | { op: "insert"; parent: string; index: number; node: SerializedRenderData }
    | { op: "delete"; parent: string; index: number }
    | { op: "set"; uuid: string; key: "type" | "text" | "props" | "mdSymbols" | "tagName" | "isAutoFill" | "children"; value: unknown }
    | { op: "replaceRoot"; node: SerializedRenderData };
```

`insert` 与 `delete` 按父节点 uuid 加子节点序号寻址，映射到 `Y.Array` 的切片；`set` 用 uuid 寻址，宿主自己维护 uuid 到节点的注册表；一批 op 是一个状态变化的事务，按序原子应用。反向入口是 `applyRenderDataOpsToDraft(rootHolder, ops)`，直接作用在 Immer draft 上。

之所以能只靠 `insert`/`delete` 表达，靠的是 span 不可变这条不变式，`mergeInlineBlock.ts` 的注释写得很直接：

```text
A span is an immutable atom: only ever created and deleted, never modified
— and that invariant is what keeps the CRDT side from ever needing a deep merge.
```

span 只被创建和删除，从不被就地修改，协同端因此永远不需要深度合并。合并算法分三步：先把两个容器各展平成带"格式签名"的字符流，签名是祖先 `htmlType_` 链加 href/src；再扫出公共前后缀；最后把变化区向外扩张到旧容器的顶层子节点边界。开销按容器文本长度线性。类型变化、块拆分等不匹配的情形由调用方整块替换兜底。

我拿仓库里的适配器做了一次双副本离线合并实验：两份 `EditorStore` 由同一份种子建立，A 改段落开头，B 改段落结尾，之后互推状态。

- 两次改动落在**不同 span**：合并后干净交织，`start **bold mid** end` 变成 `HEAD **BOLD CENTER** end`，两份副本输出完全一致。
- 两次改动落在**同一 span**：两边的删除与插入都存活，结果是并排的两份文本，不丢内容但也不自动交织。

第二种情形与 `crdt-sync` 入口文件自己声明的边界一致：并发写同一个 span 时"重复但不丢文本"，比静默 LWW 更安全。同一段注释里还有一条更危险的告诫——**必须共享同一来源**。两份独立建档的文档即使内容和 uuid 都一样，Yjs 的条目标识仍是各自生成的；合并时顶层 `Y.Map` 上的并发赋值退化成整值 LWW，输的那棵树会被静默丢掉。接入时务必从持久化里恢复既有文档，不要新建空文档再灌内容。

## 内联语法扩展点与它的告警盲区

0.6 起内联语法成了一等扩展点，内置的 `==高亮==` 本身就是第一条规则（`defaultInlineRules` 编译到 `tagName: "mark"`）。规则声明是 `open` + `close` 加渲染方式，`{…}` 参数块沿用 Pandoc/Djot 的内联属性家族。

编译期的校验我逐条实跑过，报错文案和处置方式都是确定的：

| 输入 | 处置 |
|---|---|
| `close: ""` | 丢弃整条规则：`open/close must be non-empty strings` |
| 分隔符含字母或数字 | 丢弃：`delimiters must not contain alphanumeric or whitespace chars` |
| 分隔符含 `` ` `` `\` `{` `}` | 丢弃：`code-span/escape/capture sovereignty` |
| `tagName: "script"` | 保留规则，标签降级为 `span` 并告警 |
| `attrs` 里写 `onclick` | 该属性丢弃，其余属性保留 |
| 变体名含空格 | 该变体丢弃，规则保留 |

标签白名单共 18 个：`b i s em strong del u mark sub sup kbd ins small abbr cite q var span`。属性只允许落到 `class style href title id` 以及 `data-*`、`aria-*` 前缀上，事件处理器根本不可达；`javascript:` 开头的链接在渲染时被丢掉。整条链路的姿态是"永不抛异常，只降级并告警"，宿主写错一条规则不会把编辑器弄挂。

问题出在后半句。构建的 terser 配置里 `drop_console: true`，同时把 `console.log`、`console.time`、`console.timeEnd` 声明为纯函数。我在 0.13.1 的产物里搜 `do-md] inlineRules`，0 命中。也就是说上面那张表里的告警只存在于源码和开发模式，生产构建里规则被静默丢弃。

排查手法因此要换个路子：`compileInlineRules` 产出的 `triggerReg_` 会暴露哪些规则活了下来。

```text
一条合法的 $$…$$ 规则        → /(?:\$\$(?:\{[^\n]*?\})?.+?\$\$)/
分隔符含字母，或 close 为空   → triggerReg_ 为 null（整条被丢）
与内置冲突的单个 < 号         → /(?:<\{[^\n]*?\}.+?>)/  捕获段变成必选
```

所以宿主侧的自检要换个抓手：注册之后拿编译结果断言 `triggerReg_` 非空、且串里含预期的转义分隔符，比等控制台输出可靠得多。

## 双层许可与 0.11.0 这条线

先纠正一条常被写错的时间线：GPL 切换不在 0.10.0。逐版拉 npm 的 `license` 字段，结果是：

```text
0.2.5        无 license 字段
0.2.6 – 0.10.0   PolyForm-Noncommercial-1.0.0
0.11.0 – 0.13.1  GPL-3.0-only
```

README 里有同样的说法：0.10.0 及之前是 PolyForm Noncommercial 1.0.0，0.11.0 起才是 GPL-3.0 加附加权限。2026-08-20 那次提交也对得上：内核源码从私有仓库整体搬进公开仓库，在此之前它只是依赖里一个内部属性被改名的 npm 包。

同一次提交里还有一条容易被忽略的工程决定：属性改名（`mangle.properties /_$/`）被彻底移除。terser 配置旁的注释给了原因：改名唯一的理由是闭源期的代码保护，改用 GPL 之后它只剩代价。运行时属性名每次构建都在变，就从源码生成不出可信的类型声明，只能退回手写窄声明文件。而正是手写声明这条路，让对外接口与实现漂移过一次。

`.packages/@do-md/core/LICENSE-EXCEPTIONS.md` 是按 GPL §7 授予的两条附加权限，读的时候有三处细节最容易被忽略：

**小实体豁免的两个条件是且关系。** 非营利组织与教育机构直接合格；个人和营利实体要同时满足 `Your Revenue` 低于 100 万美元**且** `Your Funding` 低于 200 万美元。两个口径都合并关联方（控制定义为持股超 50%），金额按 2026 年美元计并以 BLS 的 CPI 做通胀调整。豁免本身不可撤销：带该文件发布的版本永久在这些条款下可用；不再合格时有 90 天窗口去补齐合规或谈商业许可，此前已发出的副本对下游所有人永久有效。资格逐方判定，接收方能不能再分发，取决于它自己的规模。

**FOSS 例外多一个条件。** 能走这条的只有清单里那 8 个许可证：Apache-2.0、BSD-2-Clause、BSD-3-Clause、EPL-2.0、ISC、MIT、MPL-2.0、zlib。另有两个附加要求：组合作品里除内核外不能含其他 GPL 作品；必须连同 `LICENSE-EXCEPTIONS.md` 一起分发。

**在浏览器里加载就是 conveying。** 这是最容易误判的一条，文档里写得毫不含糊：

> **Shipping a web app that loads this kernel** — that *is* conveying: your build reaches your users' browsers. This is the point most people get wrong.

对应地，只在自家机器上跑的开发、测试和内部评估不构成 conveying。应用层的 MIT 源码单独看仍是 MIT，但打包了 GPL 内核之后，任何二进制或网页分发整体按 GPL 走——这句是 README 明写的，不是推论。

CLA 用的是 contributor-assistant 那条动作，v2.6.1 固定在提交哈希上。注释给了理由：这个 workflow 跑在 `pull_request_target` 上且带写权限，不能让上游 tag 换掉代码。签名以评论形式落在 `cla-signatures` 分支的一个 JSON 里。协议文本是 v1 版，开头就声明尚未经律师审阅。仓库目前只有这一个 workflow 文件。

## 一千多条断言里有两条是红的

这个项目最有意思的地方是它的测试形态。没有 vitest，也没有 Playwright，只有一批能独立跑的头脚本：用 esbuild 把源码打包出来再执行，断言连事故编号一起写在文件头。内核目录下有 13 个这样的套件目录，其中 11 个带 `run.sh`；仓库根的 `scripts/` 下另有 12 个 `verify-*`。我在 HEAD 上跑了内核侧 9 个套件和应用侧 2 个：

```text
verify-merge                  101 通过
verify-replace                157 通过，0 失败
verify-selection              295 通过，0 失败
verify-resolve-ranges         122 通过，0 失败
verify-table-ops              117 通过，0 失败
verify-img-group               58 通过，0 失败
verify-softbreak               32 通过，0 失败
verify-empty-blocks            40 通过，2 失败
verify-table-after-paragraph   20 通过，0 失败
应用侧 verify-load-gate        30 通过，0 失败
应用侧 verify-collab-scale     28 通过，0 失败
```
```bash
# 内核侧（需先在仓库根装 immer 与 nanoid）
cd .packages/@do-md/core && sh scripts/verify-merge/run.sh

# 应用侧（需先有内核产物 dist/index.js）
node --experimental-strip-types --import ./scripts/lib/register-ts-resolve.mjs \
     scripts/verify-load-gate/run.mts
```


内核侧 9 个套件合计 944 条，应用侧两个合计 58 条。两条失败都落在 `verify-empty-blocks` 上，重复执行结果一致：

```text
✗ structure: "- [ ] "
  got  Ul(CheckBoxLi(CheckBoxLabel(CheckboxesInput,Plain),EmptyP(Br)))|EmptyP(Br)
  want Ul(CheckBoxLi(CheckBoxLabel(CheckboxesInput,Plain),EmptyP(Br)))
✗ structure: "> "
  got  Blockquote(EmptyP(Br))|EmptyP(Br)
  want Blockquote(EmptyP(Br))
```

两条的形状差异完全一致：实际输出在块之后多了一个尾部补空白段落。同文件里锁定 `parse(serialize(x)) === parse(x)` 的那批断言照常通过，说明丢的不是内容，只是根的构造变了。时间线也对得上：这个套件最后一次改动是 2026-08-21（提交 `501c6f4`），而给结构末尾文档补下方光标的那次修复是 2026-08-27（提交 `7b1a534`）。红的大概率是期望串，不是内核。真正的问题在于没人提醒——`.github/workflows/` 里只有一个 CLA 检查，这批断言不会在提交时被跑一遍。

这不影响使用，但影响你怎么读它的测试。断言密度确实高，1,002 条覆盖光标、选区、表格操作、软换行、批量替换与序列化往返；同时它们全靠人手动跑，主干上就会漂着没人注意的红灯。

性能方面仓库给了 `bench-merge`，但它测的对象很窄，值得先看说明再看数字。每次按键都会重解析整个块，`mergeParsedBlock` 紧随其后走一遍，所以真正的问题不是"表格操作快不快"，而是这次合并相对那次重解析占多大比重。我的机器（Apple M4、Node.js v26.3.0）跑出来的结果：

```text
行列      单元格   重解析(ms)  合并(ms)  合并/重解析
3×3          9      0.027      0.030      1.11x
10×5        50      0.127      0.102      0.80x
25×8       200      0.656      0.370      0.56x
50×10      500      1.032      0.720      0.70x
100×12    1200      2.356      1.909      0.81x
200×20    4000     10.920      9.040      0.83x
```

读法：3×3 这一档合并比重解析还贵，表格极小时引用保持的开销并没有被省下；从 10×5 起比值落到 1 以下，在 25×8 处最低 0.56x。这不构成"编辑 4000 个单元格的表格不卡"的依据。两个绝对值都是每键毫秒，200×20 那一行两项加起来约 20 毫秒，已经接近一帧的预算；而且这里没有渲染、没有 React 协调、没有 DOM。想要端到端手感，还得自己在浏览器里测。README 里"20,000 行文档平滑编辑"是厂商数字，这个套件没有给出可比的口径。

## 该怎么用这个项目

按决策来排，不按功能来排。

**先确认许可路径。** 会把这个内核发给用户吗？网页加载、App Store、任何发送到用户设备的行为都算 conveying。会的话三条路选一条：符合小实体豁免（营收与融资两条线都要在限内）、按 8 个 FOSS 许可证之一整体发布（且组合里没有别的 GPL 作品）、买商业许可。只是内部试用、自己机器上开发构建，不触发义务。规模跨过 100 万美元营收或 200 万美元融资的公司，这条要在写代码之前谈。

**别把它当富文本框架。** `renderComponent` 能替换的官方目标目前声明为 `MarkdownType` 里的 `Img`、`ImgGroup`、`Link`、`Table`、`Pre`；`.packages/@do-md/plugins/` 那四个包（命令、目录、搜索、虚拟滚动）在仓库里，其中只有 `@do-md/commands` 上了 npm。ProseMirror 和 Slate 那种插件生态这里没有。

**接协同前先读那段同源告诫。** 直接用 `plugins/collaboration/crdt-sync/`，别自己从 op 流重造映射；文档副本必须从持久化恢复，不接受两份独立建档。上线前自己跑一遍同 span 并发编辑，看清楚"重复但不丢"这个既定语义是不是你能接受的取舍。

**AI 场景是它现在最扎实的用途，但要按 0.11+ 的接口写。** 服务端用裸 Node.js 起 `EditorStore`，模型输出走 `insertText`，成批修订走 `replaceRanges`，把 `subscribeRenderDataOps` 的 op 流推到浏览器那份 store 即可；`replaceRanges` 一条撤销回滚整批这个性质，对"让模型改完还能一键还原"的界面很友好。文档示例里那个 `aiInsertInCursor` 已经不在产物里，别照抄。

**不适合的几类：** 需要编辑 JSON、YAML 之类非 Markdown 内容的；要求存回磁盘必须与原文件逐字节相同（松列表会被收紧）；Windows 原生构建（README 明说暂不支持）；以及把 CI 当作质量底线、不接受主干上有手动跑的红灯的团队。

## 下一步读哪几段代码

想接着往下判断这套东西靠不靠得住，按这个顺序读最省时间，每处都能顺手跑一遍复算：

1. `.packages/@do-md/core/src/editor/model/merge/mergeInlineBlock.ts` 的头注释——span 不可变这条不变式，以及它为什么让协同端不需要深度合并；
2. `.packages/@do-md/core/src/editor/model/sync/renderDataOps.ts` 的头注释——op 流为什么不走 immer 的 patch；
3. `.packages/@do-md/core/src/editor/controller/lib/checkDomNeedRender.ts`——每次按键的放行条件，包括那条防止标题反复重解析的正则；
4. `.packages/@do-md/core/scripts/verify-selection/entry.ts` 与 `verify-empty-blocks/entry.ts`——前者 295 条断言，是全项目最密的一处；后者是主干上那两条红灯所在；
5. `.packages/@do-md/core/vite.config.ts` 里 terser 配置旁的注释——属性改名为何被移除，以及它和类型声明漂移的因果关系。

第 4、5 两处合起来，基本就能看出这个项目当前把精力花在哪、又在哪一处还没来得及收尾。

## 五个自测题

1. 同一文档，A 改段落开头的 span，B 改同段落另一个 span，离线后合并，结果是什么？如果 A 和 B 改的是同一个 span 呢？
2. `replaceRanges` 传入五条编辑，其中一条越界，其余四条会怎样？用户按一次撤销会退回到哪一步？
3. 内核产物里 `aiInsertInCursor` 有几个命中？由此能推出 README 的哪一句已经过期？
4. 一家融资 300 万美元、营收 40 万美元的公司，把内核装进自家网页产品的前端发给用户，能否主张小实体豁免？换成一家公司写一个纯内部工具呢？
5. 宿主注册了一条 `open` 含字母的内联规则，生产环境没有任何控制台输出，用什么办法确认它到底有没有生效？

答案都能在前面几节的命令里跑出来。真要验证第 5 题，去检查 `compileInlineRules` 的 `triggerReg_`。

## 参考

- 仓库：<https://github.com/do-md/domd>（本次核对基准提交 `1780d7f`，标签 `v0.10.0`）
- 内核包：<https://www.npmjs.com/package/@do-md/core-react>（0.13.1）
- 内核文档与接口一览：tarball 内的 `README.md`
- 附加权限全文：`.packages/@do-md/core/LICENSE-EXCEPTIONS.md`
- 贡献与 CLA：<https://github.com/do-md/domd/blob/main/CONTRIBUTING.md>、<https://github.com/do-md/domd/blob/main/CLA.md>
- 网页版与演示：<https://www.domd.app/editor>、<https://www.domd.app/playground>、<https://www.domd.app/playground/crdt>、<https://www.domd.app/playground/live>、<https://www.domd.app/chat>
- 状态底座：<https://www.npmjs.com/package/@do-md/zenith>
