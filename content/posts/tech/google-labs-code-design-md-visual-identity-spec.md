---
title: "DESIGN.md 的散文承诺与导出边界：Google Labs 给 Coding Agent 的设计简报规范"
date: "2026-06-26T18:01:00+08:00"
lastmod: "2026-09-21T00:00:00+08:00"
slug: "google-labs-code-design-md-visual-identity-spec"
github_repo: "google-labs-code/design.md"
source_key: "gh:google-labs-code/design.md"
description: "对照 google-labs-code/design.md 的 main 分支、npm @google/design.md 0.4.0 与实跑输出读 DESIGN.md：PHILOSOPHY.md 的四条主张各自落在哪一层、11 条校验规则的真实严重级别与退出码、五种导出格式为什么丢掉了组件、文档与实现不一致的四处现场，以及动效令牌写进 front matter 之后会发生什么。"
draft: false
categories: ["技术笔记"]
tags: ["设计系统", "AI Agent"]
---

> **目标读者**：已经让编码智能体（Coding Agent）生成前端界面、发现每次生成的配色和字距都不一致的团队；以及在读 DESIGN.md 规范、需要判断"这套格式到底约束到哪一层"的工程师。
> **本文的读法**：先给一句判断，再按"哲学主张 → 格式骨架 → 校验规则 → 导出边界"四层拆开，每条主张都用仓库原文与实跑输出对齐。文中所有命令、输出与计数来自 2026-09-21 对 `main` 分支与 npm `0.4.0` 的一次实际执行，复核命令集中在文末，可逐条重跑。`lint` 与 `diff` 的正常结果只有 JSON 一种形态；下文按"级别 规则名 路径"排版的 finding 摘录，是把 JSON 里的字段重排成便于阅读的形式，不是终端原始字节。

## 一句话判断

DESIGN.md 想用一份 Markdown 文件同时做两件事：给智能体（Agent）读的设计散文，和给工具链消费的数值表。它的**散文层是真开放**——自定义小节、自定义词汇，规范不拦；它的**数值层其实很窄**——只有 5 个设计令牌（token）分组会被解析，其中进入导出产物的只有 4 组，其余顶层键在导出时静默丢弃。

把这两层混为一谈就会读错这个项目：`PHILOSOPHY.md` 说"格式靠使用者生长，不靠规范修订"，而仓库里那条叫 `token-like-ignored` 的规则，会指着它自己那个例句告警。

这个矛盾不是缺陷，是设计的接缝。本文要做的就是把它对准读者：什么该写进散文，什么必须写进 token，写了之后哪一层会丢。

## 项目坐标

| 项 | 值（2026-09-21 核对） |
|:---|:---|
| 仓库 | [google-labs-code/design.md](https://github.com/google-labs-code/design.md)，`main` 分支 |
| 首次提交 | 2026-04-10 的 `Initial commit`；同日并入 linter 与 `spec.md` |
| 提交规模 | `main` 上共 62 个提交，最近一次推送 2026-09-14 |
| 许可 | Apache-2.0（仓库有 `LICENSE`；npm 包体的 `package.json` 未声明 `license` 字段） |
| 语言与构建 | TypeScript，Bun workspaces 加 turbo 单仓 |
| npm 包 | `@google/design.md`，最新 `0.4.0`（2026-07-27 发布），首个版本 `0.1.0` 发布于 2026-04-21 |
| 运行门槛 | 运行时为 Node.js，版本下限 `>=18.0.0`（写在 `engines.node` 字段） |
| 关注度 | 28,017 stars、2,285 forks、44 个未关闭 issue |
| 规范主页 | 仓库在 GitHub 登记的 homepage：https://stitch.withgoogle.com/docs/design-md/specification |
| 文档体量 | `README.md` 364 行、`PHILOSOPHY.md` 110 行、`docs/spec.md` 377 行 |
| 附带样例 | `examples/` 目录下三套完整设计系统，linter 另有 9 个测试夹具 |

格式本身仍是 `alpha`：`docs/spec.md` 的生成头写着 `version: alpha`，README 的 `## Status` 也明确写了规范、取值结构与命令行工具三者都在活跃变更期。这条决定了后文所有"要不要现在上"的判断。

## 目录

- [一句话判断](#一句话判断)
- [项目坐标](#项目坐标)
- [系统地图：三条链路，不是一条](#系统地图三条链路不是一条)
- [问题拆分：散文、token、工具是三件事](#问题拆分散文token工具是三件事)
- [核心机制之一：PHILOSOPHY.md 的四条主张](#核心机制之一philosophymd-的四条主张)
- [核心机制之二：格式骨架只有两层](#核心机制之二格式骨架只有两层)
- [校验：11 条规则、真实严重级别与退出码](#校验11-条规则真实严重级别与退出码)
- [导出：五种格式与一条硬边界](#导出五种格式与一条硬边界)
- [文档与实现不一致的四处现场](#文档与实现不一致的四处现场)
- [程序化接口：把 linter 当编辑菜单](#程序化接口把-linter-当编辑菜单)
- [一次完整流转：给一套设计系统加动效](#一次完整流转给一套设计系统加动效)
- [命名上的选择：`.md` 的三重身份与 Windows 的 designmd](#命名上的选择md-的三重身份与-windows-的-designmd)
- [适用边界与替换方案](#适用边界与替换方案)
- [采用顺序](#采用顺序)
- [排查：按现象定位](#排查按现象定位)
- [自测清单](#自测清单)
- [下一步读哪份代码](#下一步读哪份代码)
- [参考与复核命令](#参考与复核命令)

## 系统地图：三条链路，不是一条

DESIGN.md 常被当成"一个 linter"，实际交付物是三条彼此独立、共享同一份 schema（结构模式）定义的链路。

| 链路 | 输入 | 输出 | 由谁驱动 |
|:-----|:-----|:-----|:---------|
| 规范链路 | `spec.mdx` 加 `spec-config.yaml` | `docs/spec.md`（生成物） | `bun run spec:gen` |
| 校验链路 | DESIGN.md 文本 | findings 列表与分级汇总 | 11 条规则、`lint` 子命令 |
| 导出链路 | 解析后的 token 模型 | Tailwind v3、v4、DTCG、CSS 变量 | 4 个 emitter、`export` 子命令 |

```text
仓库源文件   spec.mdx + spec-config.yaml ────────▶ docs/spec.md

DESIGN.md  ─┬─ parser ─▶ model ─▶ 11 rules ──────▶ lint findings
            │                        └────────────▶ diff（前后对比）
            └─ model ─▶ 4 emitters ───────────────▶ tailwind / dtcg / css-vars
```

三条链路共享的是同一批常量与规则描述符。这一点带出本文最重要的操作性结论：**规范文档、规则清单、导出能力都是源文件的产物或消费者，只有 `README.md` 里那几张表是手写的。** 手写表格与生成物之间的时间差，就是绝大多数"读到过期说法"的来源。

## 问题拆分：散文、token、工具是三件事

在 DESIGN.md 之前，把设计系统写进文本的尝试大致分三类：Style Dictionary 走"一份 token 转多平台产物"的流水线路线，W3C Design Tokens 社区组走"定义行业标准格式"的互操作路线，Salesforce Theo 走"单一来源加构建期转译"的工作流路线。三者共同点是**规范的中心是 token**。

DESIGN.md 把中心换成了散文，但换得不彻底，而且这是刻意的——仓库里三份文档对同一件事的措辞并不一致：

| 出处 | 原话 | 立场 |
|:-----|:-----|:-----|
| `PHILOSOPHY.md` | The prose is the most vital part of the specification. | 散文是规范主体 |
| `PHILOSOPHY.md` | The token values serve as context and are not rendering instructions. | token 只是上下文 |
| `docs/spec.md` | The tokens are the normative values; the prose provides context for how to apply them. | token 才是规范值 |
| `README.md` | Tokens give agents exact values. Prose tells them *why* those values exist and how to apply them. | 二者并列分工 |

这不是编辑事故，是视角差异：PHILOSOPHY 回答"生成质量从哪来"，规范性文档回答"机器该信谁"。两句可以同时成立——**意图靠散文传递，取值以 token 为准**。但代价很清楚：只写在散文里的东西没有规范值可继承，导出产物里也不会有它；只写在 token 里、没有散文解释的值，Agent 会用错地方。

于是"该写在哪一层"有了一条可执行的判据：**希望 Agent 在边角场景自行推断的，写进散文；希望出现在导出产物里的，写进 token。** 夹在中间最糟的写法，是把只有数值没有用途的 token 表塞满 front matter，然后在正文里一个字都不解释。

## 核心机制之一：PHILOSOPHY.md 的四条主张

`PHILOSOPHY.md` 只有 110 行，四条主张各占一节标题。常被概述成"三条原则"，其实是四条——第四条恰好最容易被忽略，也最影响采用决策。

### 主张一：散文是主体，token 不是渲染指令

> The prose is the most vital part of the specification.
> The token values serve as context and are not rendering instructions. Generally, we do not accept or recommend token requirements in the specification.

第三句常被省略，但它最硬：规范**不接收也不推荐**针对 token 的强制要求。配合开篇那句 "The prose is where the design lives. Everything else in the document exists to support it."，这一条的强度已经超过一般项目自述。

它落到写法上的要求很具体：`## Colors` 一节要说清每个颜色的**用途边界**，而不是复述色值。文档自带的例子就是照这个写法：

> **Vermilion** {colors.vermilion} is the single accent and appears only inside diagrams and chart annotations — never on typography, never on page numerals, never on metadata of any kind.

一句里给了正面用途加三条禁地，还用 `{colors.vermilion}` 引回 token。这种句子对生成质量的贡献，比再列十个色值都大。

### 主张二：一个具体参照胜过一串形容词

> A design that references "A 1970s graduate lecture handout in the tradition of an old and established university" evokes a complete world: the one color of ink, the generous margins, the serif set at a reading size, and the absence of decoration. That single sentence carries more useful information than a dozen metric values. It carries the reasoning behind the values.

紧接着是原文里的另一句对照：

> "Modern, clean, trustworthy, premium" evokes nothing specific. A model creates something in the center of what those words describe, creating an output that is typically generic. Adjectives describe a region. A specific reference describes a point.

最后一句才是落点：形容词描述的是一个区域的中心，也就是统计意义上最平庸的那个解；具体参照描述的是一个点。`## Overview` 里写"现代、简洁、可信、高端"，等于把生成结果推回分布中央。

README 给的例子是另一个方向：`Architectural Minimalism meets Journalistic Gravitas. The UI evokes a premium matte finish — a high-end broadsheet or contemporary gallery.` 三个名词短语各自锚定一类印刷物，一处形容词堆叠都没有。

### 主张三：负约束随参照对象免费继承

> A clear design reference carries its restrictions automatically. A model knows what a lecture handout is, and it knows what a lecture handout is not. It does not glow or use a gradient. You don't have to list these. Naming the object names them, the same way naming a dog tells the model that dogs don't meow.

"命名一个对象就命名了它的否定面"是整套哲学里最反直觉、也最有工程含义的一句。它的实用价值在于：显式穷举"不要渐变、不要阴影、不要暗色模式"这类否定清单，收益远低于把一个参照物说清。

但文档同时给这条设了边界，边界常被漏引：

> The negative constraints arrive for free when the reference is specific enough. An intentional list of "don'ts" is useful. A long rambling list is often a sign the description was too vague to carry them. A strong reference and an intentional list of do's and don'ts working together is the sweet spot.

即否定清单不是要删掉的东西，而是要**有意整理**的东西，它和强参照是叠加关系。文档随后给出的示例是 8 条 Don't 加 4 条 Do，每条都贴在参照物的边界上：不给标题页加 hero moment、不在大标题下配斜体导言（原文点名 "That is the Substack register"）、不给页码上色、不用加粗、不引入暗色模式与圆角。这些都不是泛泛的"保持极简"，而是在给一份讲义一条条描出边界。

### 主张四：格式靠使用者生长，不靠规范修订

这节的标题就是主张：The format grows through its users, not its spec.

> The spec defines the structural minimum that every DESIGN.md shares: a name, and a small set of categories (colors, typography, spacing, rounded, components) that are universal enough to standardize. Everything beyond that minimum is yours to define.

为了演示这一点，文档现写了一个规范里根本不存在的动效分组：

```yaml
motion:
  feedback: 120ms
  content: 250ms
  easing: 'cubic-bezier(0.2, 0, 0, 1)'
```

> The linter accepts these values and agents read the prose. No spec change was needed because the tokens themselves are context rather than instruction.

这段是自述里最需要校准的一处。**linter 确实不拒绝它**，这一点我实测通过；但"接受"不等于"无话可说"。把 `motion:` 原样放进一个真实文件的 front matter，`0.4.0` 会给出这样一条告警：

```text
warning  motion
"motion" looks like a design-token map but is not a recognized schema key
(colors, typography, spacing, rounded, components). It will be silently
ignored by export commands. Rename it to a supported key or move its
values under a recognized section.
```

规则名 `token-like-ignored`，级别 warning，不阻断合并，退出码仍是 0。判据是纯词法的，与键名无关：只要这个未知键的值（含向下递归一层）里出现十六进制色、带单位尺寸，或者出现 `fontFamily` 这类排版属性名，就判定"看起来是 token 表却不在 schema 里"。把 `colors:` 误写成 `colours:` 也会命中它。作为对照，同一份文件若只是多出一个 `## Motion` 散文小节，linter 一条告警都不发。

于是主张四的真实边界划出来了：**散文层的扩展完全免费，token 层的扩展要付一条告警，而导出链路根本不认它。** 这不是文档说谎，而是"Agent 读得到"与"工具链接得住"本来就是两件事——只是 `PHILOSOPHY.md` 把它们写在了一起。

## 核心机制之二：格式骨架只有两层

一个 DESIGN.md 由 YAML front matter 与 Markdown 正文两层组成，用的都是 `---` 与 `##` 这类最常见标记，没有自定义语法。

### 机器可读的那一层

front matter 一共 9 个键，4 个元信息加 5 个 token 分组（取自命令行工具子包 `packages/cli/src/linter/parser/spec.ts` 里的 `SCHEMA_KEYS`）：

| 键 | 必填 | 说明 |
|:---|:-----|:-----|
| `name` | 规范视为最小结构 | 设计系统名；linter 不检查它，缺了也不告警 |
| `version` | 否 | 字符串，当前写 `"alpha"` |
| `description` | 否 | 一句说明 |
| `omitted` | 否 | 声明"有意省略"的小节，把缺失提示改写成有理由的声明 |
| `colors` | 否 | 颜色 token 表 |
| `typography` | 否 | 排版 token 表 |
| `rounded` | 否 | 圆角尺度 |
| `spacing` | 否 | 间距尺度，允许无单位数字 |
| `components` | 否 | 组件属性表 |

`version` 是**可选**字段，不是固定值——README 与 spec 都写作 `optional, current: "alpha"`。把它当必填、或者以为它能做版本协商，都会读错这份 schema。

token 值只有四种形态：

| 类型 | 允许的形式 | 示例 |
|:-----|:-----------|:-----|
| Color | 任意 CSS 颜色：十六进制、颜色关键字、`rgb()`/`hsl()`/`hwb()`、`oklch()`/`oklab()`/`lab()`、`color-mix()` | `"#1A1C1E"`、`"oklch(62% 0.18 250)"` |
| Dimension | 数字加 `px`/`em`/`rem` | `48px`、`-0.02em` |
| Token Reference | `{分组.名称}`，指向已定义的原始值；`components` 内允许引用复合值 | `{colors.tertiary}`、`{typography.label-md}` |
| Typography | 对象，7 个属性：`fontFamily`、`fontSize`、`fontWeight`、`lineHeight`、`letterSpacing`、`fontFeature`、`fontVariation` | 见下方片段 |

颜色的支持面比多数同类工具宽，代价藏在对比度检查里。spec 写明所有颜色会被内部转换到 sRGB 再做 WCAG（网页内容无障碍指南）计算，原始格式只保留用于展示与导出。所以一个宽色域 `oklch()` 能否通过 `contrast-ratio`，取决于它转换后的结果。`lineHeight` 接受无单位数字，spec 直接推荐这种写法，因为倍数比绝对行高更适合响应式。`fontFeature` 与 `fontVariation` 分别映射到 `font-feature-settings` 与 `font-variation-settings`。

组件层有 8 个合法属性：`backgroundColor`、`textColor`、`typography`、`rounded`、`padding`、`size`、`height`、`width`。状态变体不嵌套，平铺成相关键名——`button-primary`、`button-primary-hover`、`button-primary-active`。spec 同时提醒组件规范仍在演化，鼓励各团队按领域补组件类型。

```yaml
components:
  button-primary:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.on-tertiary}"
    rounded: "{rounded.sm}"
    padding: 12px
  button-primary-hover:
    backgroundColor: "{colors.tertiary-container}"
```

模型层还有两个安全上限：token 嵌套深度 20、引用链深度 10。它们写在 `spec-config.yaml` 的 `limits` 段，由 2026-06-12 那次支持嵌套 token 声明的提交（`#103`）一并引入。另有一批同类约束是 2026-07-02 "bound token-validation cost on adversarial input"（`#121`）加的：行内值超过 64 字符就不做模式匹配、编辑距离比较前先按长度差剪枝。两者的动机是同一件事——这份文件任何人都能递进来，校验成本必须有上界。

### 人读的那一层

正文小节用 `##` 标题，顺序固定，可省略但不可乱序，共 8 节：

| # | 小节 | 认可的别名 |
|:--|:-----|:-----------|
| 1 | Overview | Brand & Style |
| 2 | Colors | |
| 3 | Typography | |
| 4 | Layout | Layout & Spacing |
| 5 | Elevation & Depth | Elevation |
| 6 | Shapes | |
| 7 | Components | |
| 8 | Do's and Don'ts | |

`## Overview` 的职责在 spec 里写得很具体：定义品牌个性、目标受众，以及界面该 "playful 还是 professional、dense 还是 spacious"——它是具体规则没覆盖时，Agent 用来兜底判断的那段上下文。

规范对"没见过的内容"整体宽容，但 README 与 spec 的清单不等长：spec 列了 6 种情形，README 只抄了 5 种，漏掉的是"未知间距值按字符串保留"这一条。以 spec 为准：

| 情形 | 规定行为 | 文档给的例子 |
|:-----|:---------|:-------------|
| 未知小节标题 | 保留，不报错 | `## Iconography` |
| 未知颜色 token 名 | 值合法即接受 | `surface-container-high: '#ede7dd'`（表面容器层级命名） |
| 未知排版 token 名 | 接受为合法排版 | `telemetry-data` |
| 未知间距值 | 接受，非法尺寸按字符串存留 | `grid-columns: '5'` |
| 未知组件属性 | 接受，并告警 | `borderColor` |
| 重复小节标题 | 报错，拒绝整个文件 | 两个 `## Colors` |

宽容姿态带来的前向兼容确实有效：一份带 `## Motion`、`## Iconography` 的文件能原样通过校验。但最后那一行需要单独看，它和实际行为不一致。

## 校验：11 条规则、真实严重级别与退出码

linter 是这个项目最有生产价值的部分，也是文档最容易被读错的部分。下面这张清单**不是从 README 抄的**，而是 `designmd spec --rules-only` 在 0.4.0 上的实际输出——这张表由规则描述符自动生成，因此不会过期。

| 规则 | 级别 | 检查内容 |
|:-----|:-----|:---------|
| `broken-ref` | error | 引用解析不到已定义 token；同时兼管未知组件子属性 |
| `missing-primary` | warning | 定义了颜色却没有 `primary` |
| `contrast-ratio` | warning | 组件的 `backgroundColor`/`textColor` 配对低于 4.5:1 |
| `orphaned-tokens` | warning | 颜色 token 未被任何组件引用 |
| `token-summary` | info | 汇总各组 token 数量 |
| `missing-sections` | info | `spacing`、`rounded` 在其他 token 存在时缺失 |
| `missing-typography` | warning | 定义了颜色却没有任何排版 token |
| `section-order` | warning | 小节顺序不符规范顺序 |
| `unknown-key` | warning | 顶层键像已知键的拼写错误 |
| `token-like-ignored` | warning | 顶层未知键的取值看起来是 token 表 |
| `omitted-rules` | info | 校验 `omitted` 声明本身是否有效 |

README 的表格写 "Each rule produces findings at a fixed severity level"，源码 `RuleFinding` 上写的却是 `Optional override of the descriptor's default severity`。**实际行为以后者为准**，两处可复现：

```text
# 组件里写了一个不在 8 个合法属性内的键
warning  broken-ref  components.button-primary.borderColor
'borderColor' is not a recognized component sub-token. Valid sub-tokens: …
```

它挂在 `broken-ref` 名下，级别却是 warning。`omitted-rules` 也一样：声明级别写着 info，实际会按情形发出三个不同的规则 ID——声明有效时 `declared-omission`（info），写了已经存在的分组时 `redundant-omission`（warning），写了不认识的节名时 `unknown-omission`（warning）。所以"一条规则一个固定级别"这个说法，在 11 条里有 2 条不成立。

`omitted` 这个键值得单看，因为它把"缺省"从一条疑问变成一条声明。一份故意不做圆角的设计系统会一直收到 `missing-sections`（info）；声明之后它被替换成 `declared-omission`（info），**finding 条数不变，变的是语义**——从"你少了 spacing"变成"你有意省略了 spacing"，而且可以带上理由：

```yaml
omitted:
  - spacing
  - section: rounded
    reason: "No rounded corners defined in brand book"
```

### 只有 error 拦得住合并

三条子命令的退出码语义不同，混用会让人以为 CI 生效了其实没有。以下每一格都实测过：

| 命令 | 退出 0 | 退出 1 | 退出 2 |
|:-----|:-------|:-------|:-------|
| `lint` | 无 error | 有 error | 输入文件读不到 |
| `export` | 导出成功（**不管源文件有没有告警**） | `--format` 非法或 emitter 出错 | 输入读不到 |
| `diff` | 无退化 | `after` 的 error 或 warning 变多 | 任一输入读不到 |

`export` 的退出码语义是 2026-07 一次修正后定下来的（"exit 0 on a successful export regardless of source lint findings"），意图很清楚：把关交给 `lint`，`export` 只负责产出。

更要小心的是**哪些情况根本不产生 error**。我实测的四例：

| 输入 | 实际结果 |
|:-----|:---------|
| front matter 里引用 `{colors.oops}` | `broken-ref`，error，退出 1 |
| YAML 语法写坏（流式序列没闭合） | 一条 warning 且不带规则名，`summary` 显示 0 error，退出 **0** |
| 同一份文件里出现两个 `## Colors` | **没有与重复标题有关的 finding**，退出 **0** |
| 顶层键写成 `colours:`（该文件无组件引用） | `unknown-key` 与 `token-like-ignored` 各一条 warning，退出 0 |

第三行直接推翻了文档说法。spec 与 README 都写着"重复小节标题 Error；拒绝文件"，而源码里的 `DUPLICATE_SECTION` 实际只用于**跨块的顶层 YAML 键重复**，即 front matter 与正文代码块之间的键名冲突。`##` 标题重复这条路径根本没有实现。第二行则属于文档根本没写：`spec.md` 与 `spec.mdx` 里都找不到关于 YAML 语法错误的处理约定，实跑结果是降级成一条不带规则名的 warning 继续跑。跨块键真重复时也一样——`Section 'colors' is defined in both frontmatter and code block 1.` 是 warning，退出码 0。

这决定了集成姿势：**把 `lint` 当守门员是有效的，但不能以为它覆盖了所有结构性错误。** 语法写坏与手误重复标题这两类它都放行。反过来，能产出 error 级 finding 的也不止 `broken-ref` 一条规则。模型层遇到非法色值同样给 error，例如 `'not-a-color' is not a valid color`，退出码 1，而这条 finding 并不带 `rule` 字段。

### 接进 CI

```yaml
name: Design System Lint
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npx @google/design.md lint DESIGN.md
```

Linux 上直接用 `design.md` 这个 bin 名没有问题（Windows 的情况见后文）。若希望把告警也交给 Agent 读，可以显式取 JSON：`npx @google/design.md lint --format json DESIGN.md`。

`lint` 与 `diff` 的 `--format` 帮助文本写着 "json or text"，但 `text` 目前没有对应实现：同一份输入下 `--format json`、`--format text` 与不带该参数的输出**逐字节相同**，都是 JSON。传一个更离谱的值（`--format yaml`）也不会报错，照常输出 JSON 退出 0。`export` 则会校验：非法取值返回 `{"error":"INVALID_FORMAT", …}` 并列出 5 个合法格式，退出码 1。

### 规则数量半年里变了三次

这条经验值得单独写，因为它决定了"该从哪里读规则"。

| 时间 | 变化 | 证据 |
|:-----|:-----|:-----|
| 2026-04-10 | linter 与 spec 同日进仓 | `feat: add design.md linter (#1)` |
| 2026-06-15 | 新增 `token-like-ignored`；`0.3.0` 发布 | `#105`、`release: 0.3.0` |
| 2026-07-01 | 新增 `css-vars` 导出格式 | `#109` |
| 2026-07-27 | 新增 `omitted` 键与其校验规则，README 的条数**从 nine 直接跳到 eleven**（一次补两行）；`0.4.0` 发布 | `#155`、`release: 0.4.0` |
| 2026-07-27，在 `#155` 之后 | 提交说明写着"改成 ten 并补 `token-like-ignored` 一行"，实际 diff 只把输出示例的 `info` 改成 `infos`、扩写了 diff 示例 | `#119` |

`#119` 是最能说明问题的一条。它的提交说明声称把条数改成 ten 并补了一行规则，可它落地时 `#155` 已经先把 nine 改成了 eleven，于是那条 diff 里根本没有规则表。`token-like-ignored` 早在 2026-06-15 就进了 linter，README 却直到 7 月还写着 nine——**表格与代码差了整整一个月，而且是靠外部贡献者提 PR 才对上的**。现在 main 上写的是 "eleven rules"，与 11 个描述符一致。

所以，**要规则清单就跑 `spec --rules-only`，别读 README**。这条命令的实现在 `commands/spec.ts` 里直接 `import { DEFAULT_RULE_DESCRIPTORS }`，表格是从规则对象本身生成的；README 那一张靠人记得改。

## 导出：五种格式与一条硬边界

`export` 的 `--format` 接受 5 个取值，README 的表格只列了 4 个——`css-vars` 是 2026-07-01 加的，表没跟着更新。`--help` 里五个都在：

| `--format` | 输出 | 用途 |
|:-----------|:-----|:-----|
| `json-tailwind` | JSON | Tailwind v3 的 `theme.extend` 对象 |
| `tailwind` | JSON | `json-tailwind` 的向后兼容别名 |
| `css-tailwind` | CSS | Tailwind v4 的 `@theme { … }` 块 |
| `dtcg` | JSON | W3C Design Tokens Format Module |
| `css-vars` | CSS | 裸 CSS 自定义属性，支持 `--prefix` |

拿仓库自带的 `examples/paws-and-paths/DESIGN.md` 实跑，得到的 `@theme` 块确实只用 Tailwind v4 自己的 8 个命名空间：

```text
--color-  --font-  --text-  --leading-
--tracking-  --font-weight-  --radius-  --spacing-
```

`css-vars` 加上前缀后是同一批变量换了名字：

```bash
npx @google/design.md export --format css-vars --prefix ds DESIGN.md
```

```css
:root {
  --ds-color-surface: #f9f9ff;
  --ds-color-primary: #855300;
  /* 该文件在 css-vars 下共展开 61 个自定义属性，这里只取两行 */
}
```

`dtcg` 的输出比"符合 W3C 格式"这句描述具体得多，值得看一眼实际形状：

```json
{
  "$schema": "https://www.designtokens.org/schemas/2025.10/format.json",
  "$description": "Paws & Paths",
  "color": {
    "$type": "color",
    "surface": {
      "$value": { "colorSpace": "srgb", "components": [0.976, 0.976, 1], "hex": "#f9f9ff" }
    }
  }
}
```

上面只截了 `color` 一组。真实顶层键是 `$schema`、`$description`、`color`、`spacing`、`rounded`、`typography` 六个——**没有 `components`**。分组名用单数 `color`，颜色值被拆成 `colorSpace` 加分量数组再加原始 `hex`，所以下游拿到的是已经过 sRGB 归一的结构，`hex` 字段留了退路。

### 硬边界：组件不进导出

`json-tailwind` 的实际输出结构是 `{ theme: { extend: { colors, fontFamily, fontSize, borderRadius, spacing } } }`——**组件（component）这一类属性完全不进导出**。

这不是遗漏。`examples/paws-and-paths/README.md` 在介绍配套 `tailwind.config.js` 时就把话说明白了：

> Component tokens are intentionally excluded — Tailwind's utility-first approach handles component styling through composition of these primitives.

于是"导出三条路径搞定一切"这个印象需要收紧成一句更准的话：**导出搬运的是原始值层（颜色、排版、圆角、间距），组件层与散文层不进任何导出格式。** 组件属性与散文的唯一消费者是 Agent 本身。

这也把 `token-like-ignored` 那条告警的意义讲清楚了。它担心的是一种很自然的误判：有人把只在 DESIGN.md 内部自洽的 token 组（比如动效）写进 front matter，以为它会随导出进入构建产物。它不会。

| 现有栈 | 推荐 `--format` | 接入方式 |
|:-------|:---------------|:---------|
| Tailwind v3（`tailwind.config.js`） | `json-tailwind` | `module.exports = require('./tailwind.theme.json').theme.extend` |
| Tailwind v4（CSS 里写 `@theme`） | `css-tailwind` | 把块拷进根样式 |
| 不吃 Tailwind 的普通前端 | `css-vars` | 直接引 CSS，用 `--prefix` 避让 |
| 多端与 Figma 生态 | `dtcg` | 交给支持 DTCG 的管道 |
| 只让 Agent 读 | 不必导出 | 直接把 DESIGN.md 放进仓库 |

最后一行是反直觉但常常正确的路径：Agent 场景下 `export` 一步都不需要做，因为散文只在 DESIGN.md 里，导出反而会把它丢掉。

## 文档与实现不一致的四处现场

把上面散落的对照集中一处，方便复核。这四处都是 0.4.0 上的实跑结果，不是推测：

**1. 程序化接口的 `summary` 键名。** README 的注释写 `{ errors, warnings, info }`，实际命令行工具与 `lint()` 返回的都是 `infos`。仓库在 `#119` 已经为这一点改过 README 的输出示例，但那段接口注释漏了，至今仍是旧的。

**2. lint 的 JSON 示例形状。** README 顶部那条示例 finding 是 `"textColor (#ffffff) on backgroundColor (#1A1C1E) has contrast ratio 15.42:1 — passes WCAG AA."`，级别 warning。而 `contrast-ratio` 只在**低于**阈值时发 finding；实跑一例：

```text
warning  contrast-ratio  components.button-ghost
textColor (#b8422e) on backgroundColor (#dccbff) has contrast ratio 3.64:1,
below WCAG AA minimum of 4.5:1.
```

15.42:1 那种通过情形不会出现在输出里。另外，规则层产出的每条 finding 都带 `rule` 字段，README 的示例里没有。但反过来也别把它当通则：解析层与模型层的 finding 恰恰**不带** `rule`，前文的非法色值与 YAML 降级都属这类。"有没有 `rule`"因此成了区分两类来源的可靠标志。

**3. 重复小节标题。** 见前文实测：spec 承诺拒绝文件，实现里没有这条检测。

**4. `motion` 示例与 `token-like-ignored`。** 见主张四：散文里写 `## Motion` 零告警，front matter 里写 `motion:` 一条 warning 并明示导出不认。

这四处里只有一处需要修代码（第 3 处），其余三处都是"读错了对象"：README 是给人看的简介，`docs/spec.md` 是生成的规范，`spec --rules-only` 是规则的事实来源。**要准确就往下游走一层。**

## 程序化接口：把 linter 当编辑菜单

`@google/design.md` 导出两个入口：根路径给 CLI，`./linter` 子路径给程序使用。后者实际导出的符号比 README 提到的 `lint` 多得多：`DEFAULT_RULES`（长度正好 11）、`runLinter`、`preEvaluate`、`fixSectionOrder`、四个 emitter，以及单条规则函数。但这里有个坑：11 条规则里有 10 条能单独取到，**`sectionOrder` 没有导出**，`omitted` 导出的是对象而不是函数。要单独复用这两条，只能从 `DEFAULT_RULES` 里按下标取，或者自己重实现。

`lint()` 返回的不只是 finding：

```js
import { lint } from '@google/design.md/linter';

const report = lint(readFileSync('DESIGN.md', 'utf8'));

report.findings;         // Finding[]：规则层的带 rule，解析层与模型层的不带
report.summary;          // { errors, warnings, infos }
report.designSystem;     // 解析完引用之后的设计系统模型
report.tailwindConfig;   // 直接算好的 Tailwind 主题
report.sections;         // 文档里出现的小节标题
report.documentSections; // 按标题切开的正文
```

`sections` 给回的是**原样的标题文本**，不做规范化，也不判断是否认识——`## Overview`、`## Layout`、`## Iconography` 会分别得到 `Overview`、`Layout`、`Iconography`。它有用是因为能一次拿到全部小节名（含自定义小节）来做分支判断，而不是因为它认得别名。`examples/paws-and-paths` 的正文标题恰好直接用了别名写法，所以取回来的名字看起来像规范名：

```text
['Brand & Style', 'Colors', 'Typography', 'Layout & Spacing',
 'Elevation & Depth', 'Shapes', 'Components']
```

自定义规则是最值得用起来的扩展点，但形状要注意。**`LintOptions.rules` 要的是 `LintRule`，也就是接收解析后的设计系统状态、返回 finding 数组的函数**（`(state) => Finding[]`），不是带 `run` 的描述符对象。另外模型里的 `components` 与组件的 `properties` 都是 `Map`，得按 `Map` 遍历。

```js
import { lint, DEFAULT_RULES } from '@google/design.md/linter';

// 仓库 tsconfig 为 strict；用 TypeScript 复写时给 state 加 DesignSystemState 标注
const noGradientRule = (state) => {
  const findings = [];
  for (const [name, comp] of state.components) {
    for (const [prop, value] of comp.properties) {
      if (String(value).includes('gradient')) {
        findings.push({
          severity: 'warning',
          path: `components.${name}.${prop}`,
          message: 'Gradient values are prohibited by house style.',
          rule: 'no-gradients',
        });
      }
    }
  }
  return findings;
};

const base = lint(content);                              // 默认 11 条
const wider = lint(content, { rules: [...DEFAULT_RULES, noGradientRule] });
```

拿一份最小探针文件跑一遍（3 个颜色加 1 组排版，其中一个组件的背景色是渐变，故缺 `spacing` 与 `rounded`），两次汇总的差值就是这条规则带来的：

```text
default :  {"errors":0,"warnings":0,"infos":3}
extended:  {"errors":0,"warnings":1,"infos":3}
  warning no-gradients components.hero-card.backgroundColor
  Gradient values are prohibited by house style.
```

`preEvaluate(state)` 接收同一份状态对象，把 finding 按严重级别分成 fixes、improvements、suggestions 三档。它的用途比 `lint` 更贴近 Agent 工作流：给模型的不是原始错误列表，而是一份"必须改、建议改、可以考虑"的菜单。目前 CLI 没有暴露自动修复，仓库里唯一的修复类函数是内部的 `fixSectionOrder`，只能调乱序的小节。

## 一次完整流转：给一套设计系统加动效

抽象机制说完了，用一次真实工作串一遍。目标是给 `paws-and-paths` 这套示例加一组动效令牌，并让它们进入构建产物。全程命令与输出都在本机跑过。

**第 1 步：确认起点干净。**

```bash
npx @google/design.md lint DESIGN.md
```

```json
{
  "findings": [
    { "severity": "info",
      "message": "Design system defines 47 colors, 8 typography scales, 6 rounding levels, 8 spacing tokens, 10 components.",
      "rule": "token-summary" }
  ],
  "summary": { "errors": 0, "warnings": 0, "infos": 1 }
}
```

**第 2 步：把动效写成散文小节。** 放在 `## Components` 之后，内容描述节奏而不是数值：

```markdown
## Motion

Transitions are quick and mechanical. Nothing bounces, nothing overshoots.
Nothing in the UI animates longer than 300ms.
```

再跑一次 lint：finding 数量不变，退出 0。**未知小节按规范被静默保留**，这一步什么都不用改。

**第 3 步：再补上数值，写成顶层 `motion:` 键。** lint 立刻多一条告警：

```text
summary {"errors":0,"warnings":1,"infos":1}
warning motion — "motion" looks like a design-token map …
It will be silently ignored by export commands.
```

退出码仍是 0，合并不受阻。真正的判断在第 4 步。

**第 4 步：确认下游到底拿不拿得到。**

```bash
npx @google/design.md export --format json-tailwind DESIGN.md | grep -c '120ms\|cubic-bezier'   # 0
npx @google/design.md export --format dtcg        DESIGN.md | grep -c 'cubic-bezier'            # 0
npx @google/design.md export --format css-vars    DESIGN.md | grep -c 'motion'                  # 0
```

三种格式全部为 0——动效值确实只活在 DESIGN.md 内部。到这一步才有决策依据：若动效由 Agent 直接生成内联样式或写进组件样式，停在散文层就够了；若要 `transition-duration: var(--motion-feedback)` 这类真实构建产物，动效值必须走另一条路（`css-vars` 手写、或放进 `spacing` 之类被识别的分组里借用）。

**第 5 步：改动现有令牌时，用 `diff` 卡退化。** 把 `primary` 从 `#855300` 调成 `#7A4C00`：

```json
{
  "tokens": { "colors": { "modified": ["primary"] },
              "components": { "modified": ["button-primary"] } },
  "findings": { "before": { "errors": 0, "warnings": 0, "infos": 1 },
                "after":  { "errors": 0, "warnings": 0, "infos": 1 },
                "delta":  { "errors": 0, "warnings": 0 } },
  "regression": false
}
```

引用它的组件同步出现在 `components.modified` 里，说明 diff 比对的是解析后的值。把 `button-primary` 的引用改成一个不存在的 token，`delta.errors` 变 1，回归标记 `regression` 变 `true`，退出码 1。

这次流转把三条链路的实际分工暴露完了：**散文负责意图，token 负责取值；校验主要在引用悬空与取值非法时说不；导出只搬运 `colors`、`typography`、`spacing`、`rounded` 四组，连 `components` 都不带上。**

## 命名上的选择：`.md` 的三重身份与 Windows 的 designmd

`design.md` 这个名字同时是仓库名、文件名与 npm 包名片段，四个标识符共用同一个词根：

```text
GitHub 仓库   google-labs-code/design.md
规范文件名    DESIGN.md
npm 包        @google/design.md
CLI bin       design.md 与 designmd（都指向 dist/index.js）
```

好处直接：URL 即规范入口，`npx @google/design.md lint` 读起来就是一句话，复制粘贴时不存在"到底指哪一个"的歧义。`.md` 后缀还顺带解决了分发问题——GitHub 直接渲染、任何编辑器直接打开、Agent 直接读，不需要插件。

代价则集中在 Windows。README 为此专门留了一节，原文是：

> On **Windows/PowerShell**, this direct form can produce no output (or open `DESIGN.md` in your Markdown editor) because the `.md` suffix in the `design.md` bin name collides with the Windows Markdown file association during command resolution. Run the dot-free `designmd` alias instead — point `npx` at the package with `-p`, then invoke `designmd`:

```bash
npx -p @google/design.md designmd lint DESIGN.md
```

`designmd` 这个无点别名是 2026 年 5 月一次修复加进去的（`fix(cli): add Windows-friendly designmd bin alias (#62)`），两个 bin 都指向同一个入口，跨平台行为一致。从 `package.json` 的脚本里调用时同样要用别名：

```jsonc
{
  "scripts": {
    "design:lint": "designmd lint DESIGN.md"
  }
}
```

带点号的 scope 在 PowerShell 里还有一层：`@` 在部分 shell 下有特殊含义，README 的建议是加引号，`npm install "@google/design.md"`。

如果装不到包，README 给的判断是：`ENOVERSIONS` 几乎总是 npm 没在查公共仓库，具体三种成因——`.npmrc` 里的自定义 `registry=`、企业镜像没同步这个包、`@google:registry` 配错。定位命令是 `npm config get registry`，正常应返回 `https://registry.npmjs.org/`；改好之后如果仍报错，用 `npm cache clean --force` 清掉缓存住的 404。

顺带纠正一个容易脱口而出的说法：带点号的 npm 包名**并非**没有先例。`node.extend`（2012 年上架）与 `dot`（2011 年）都在同一个注册表里活了很多年。`@google/design.md` 真正的特殊之处不在包名，而在 bin 名——npm 允许包名里带点，Windows 的命令解析却按文件扩展名行事，冲突是从这里来的。

## 适用边界与替换方案

DESIGN.md 的适用面比"任何前端项目"窄，它的收益全部来自两个前提：**有人（或 Agent）会读散文**，以及**你愿意为描述意图付出维护成本**。

适合的情形：

- Agent 反复生成界面代码，跨会话一致性是明确痛点。DESIGN.md 的价值恰好在散文层，而那一层只有 Agent 会消费。
- 设计与前端之间需要一份能 `git diff`、能走代码审查的规范载体。
- 下游已经在用 Tailwind 或 DTCG 生态，导出这一步是净收益。
- 团队愿意写 200 到 500 字的 `## Overview`，并且能给出具体参照物。

不必用的情形，以及替代选择：

| 情形 | 更合适的做法 | 原因 |
|:-----|:-------------|:-----|
| 单页活动站、一次性界面 | 直接写 Tailwind 配置 | 规范维护成本高于收益 |
| 设计系统真源在 Figma，Agent 不读规范 | Style Dictionary 加主题文件 | DESIGN.md 的散文层没有消费者 |
| 已有强约束体系（Material、Ant Design） | 引用上游规范 | 再造一层只会漂移 |
| 只需要跨工具搬运数值、不需要意图 | 直接用 DTCG `tokens.json` | DESIGN.md 的 token 子集是 DTCG 的子集 |
| 组件规格是核心诉求 | 再等几个版本 | 组件层不进导出，spec 自己也标注"仍在演化" |

组件这一层的成熟度要单独提醒：`docs/spec.md` 在 Components 一节直接放了提示 "The components specification is actively evolving"。若你的设计系统重心就在组件状态与尺寸规约，现在押上去赌注偏大。

## 采用顺序

如果决定要试，按这个顺序推进，每一步都有可验证的收口条件。

1. **先只写散文。** `name` 加一段 `## Overview` 加 `## Colors` 的用途说明，front matter 里只留必要数值。收口条件：`lint` 只有 info，退出 0；把 Overview 交给 Agent 生成一次页面，看风格是否稳定。这一步是唯一别人替代不了的工作。
2. **补 token，让引用闭合。** 加 `typography`、`spacing`、`rounded` 与 `components`，把散文里点到的值都变成可引用的 token。收口条件：`broken-ref` 零条。此时会出现 `orphaned-tokens` 告警，逐条判断是删掉还是被组件引用。
3. **接导出，并检查丢了什么。** 用 `json-tailwind` 或 `css-tailwind` 生成主题，把产物 diff 进构建。**明确接受组件与散文不进导出**这个事实，并决定这两层由谁消费。
4. **把 `lint` 挂上 PR。** 只让它对 error 说话，退出码 1 才阻断。这一步要顺手确认团队知道"语法写坏不会被拦"，否则会产生虚假安全感。
5. **稳定后再加自定义规则。** 组织级约束（按钮最小尺寸、禁用字体、禁止渐变）写成 `LintRule` 函数挂在 `DEFAULT_RULES` 之后。这些是纯函数，能直接进单测。
6. **给规范本身留退路。** 格式是 `alpha`，把 DESIGN.md 当作上游、导出产物当作下游生成物，不要反向手工维护生成物。

## 排查：按现象定位

下面按"看到什么"排，每条都对应本文里已经验证过的行为。

| 现象 | 先查什么 | 定位依据 |
|:-----|:---------|:---------|
| CI 绿了，但主题里没值 | 该分组是不是 4 个会进导出的键之一（`components` 也不算） | 未知顶层键被静默丢弃并带 `token-like-ignored`，组件层则按设计排除在 Tailwind 导出之外 |
| 明明写坏了 YAML，`lint` 却过了 | 看 `summary` 而不是退出码 | YAML 解析问题降级为 warning，不产生 error |
| 两个同名小节没被拦 | 这是当前实现，不是配置问题 | `DUPLICATE_SECTION` 只覆盖跨块的顶层 YAML 键 |
| `missing-sections` 一直出现 | 是不是真的有意省略 | 用 `omitted:` 声明，可附 `reason`；条数不会减少，规则名会变 |
| 颜色改了对比度却没过 | 转换到 sRGB 后的值 | 所有颜色先归一到 sRGB 再算 WCAG 比值 |
| Windows 上 `npx` 没输出 | 换 `designmd` 别名 | `.md` 后缀与 Markdown 文件关联冲突 |
| `ENOVERSIONS` | `npm config get registry` | 自定义镜像未同步该包 |
| 生成的界面仍是通用风格 | Overview 里有没有具体参照物 | 形容词只描述区域中心 |

## 自测清单

1. 一份 DESIGN.md 里，哪一层的内容不会被任何 `--format` 带到下游？（答：散文层与组件层；导出只搬运颜色、排版、间距、圆角四组。）
2. `lint` 在什么情况下退出 1？YAML 语法写坏会吗？（答：只有出现 error 级 finding 时；语法写坏降级为 warning，退出 0。）
3. 想把一组新的数值令牌纳入校验与导出，最少需要动几处？（答：加 schema 键要改解析器；只加散文小节零成本，但也不会进导出。）
4. `unknown-key` 为什么不把所有未知顶层键都告警？（答：schema 有意保持可扩展，只对与已知键编辑距离不超过 2 的键提示拼写错误；真正丢值的风险由 `token-like-ignored` 承担。）
5. 判断一份 Overview 写得够不够具体，用哪个反例最快？（答：把里面的形容词逐个划掉，如果划完什么都不剩，就还是"区域"而不是"点"。）
6. README 说每条规则级别固定，为什么实际不是？（答：`RuleFinding` 允许覆盖描述符默认级别，`broken-ref` 与 `omitted-rules` 各自跨两个级别。）

## 下一步读哪份代码

按目的选，不必顺序读完。

- 想判断"该写哪些内容"：`PHILOSOPHY.md`（110 行），四个主张各一节，重点在第四条的边界。
- 想核对字段的规范定义：`docs/spec.md`，注意它是生成物，改需求要动 `spec.mdx` 与 `spec-config.yaml`。
- 想知道规则到底怎么触发：`packages/cli/src/linter/linter/rules/`，一个规则一个文件，每个都配同名测试。
- 想知道导出丢了什么：`packages/cli/src/linter/tailwind/`、`dtcg/`、`css-vars/` 三个 emitter。
- 想看三份可直接抄的完整样本：`examples/` 下的 `paws-and-paths`、`atmospheric-glass`、`totality-festival`，每套都同时给了 DESIGN.md、Tailwind 配置与 DTCG 文件，三者差异本身就是最好的教材。
- 站内另一篇 [DESIGN.md：让 Coding Agents 理解视觉设计的格式规范](/posts/tech/design-md-visual-identity-coding-agents-guide/) 从 schema 与 CLI 用法切入，与本文互补：那篇讲怎么用，这篇讲它承诺到哪一步。

## 参考与复核命令

- 仓库：[google-labs-code/design.md](https://github.com/google-labs-code/design.md)（`main`，Apache-2.0）
- 哲学文档：[PHILOSOPHY.md](https://github.com/google-labs-code/design.md/blob/main/PHILOSOPHY.md)
- 生成的规范正文：[docs/spec.md](https://github.com/google-labs-code/design.md/blob/main/docs/spec.md)
- npm 包与发布历史：[@google/design.md](https://www.npmjs.com/package/@google/design.md)
- Stitch 侧的规范页：[stitch.withgoogle.com/docs/design-md/specification](https://stitch.withgoogle.com/docs/design-md/specification)
- W3C Design Tokens Format Module：[tr.designtokens.org/format](https://tr.designtokens.org/format/)

本文所有数字与输出都可以用下面几条命令复核，前提是 Node 不低于 18：

```bash
npm install @google/design.md          # 装到本地 node_modules
npx @google/design.md spec --rules-only --format json   # 规则清单的事实来源
npx @google/design.md export --help    # 五个 --format 取值都在这里
npx @google/design.md lint examples/paws-and-paths/DESIGN.md
npx @google/design.md diff examples/paws-and-paths/DESIGN.md examples/totality-festival/DESIGN.md
```

维护说明：本文的核对基线是 `main` 的 HEAD 提交 `9bf8eae`（2026-07-27 的 `release: 0.4.0`），GitHub 侧显示的最近推送时间是 2026-09-14。四个位置最容易随版本漂移，复核时优先看它们——规则条数（以 `spec --rules-only` 为准）、`export` 的格式数量（以 `--help` 为准）、重复小节的处置方式（源码里搜 `DUPLICATE_SECTION` 的适用范围），以及 `omitted` 键支持的节名列表（源码里搜 `validSections`）。格式仍处于 `alpha`，任何一条能力都可能在正式版收紧。
