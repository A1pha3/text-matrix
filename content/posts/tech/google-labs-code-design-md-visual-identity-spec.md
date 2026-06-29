---
title: "DESIGN.md 哲学与采用路径：Google Labs 给 Coding Agent 的设计简报范式"
date: "2026-06-26T18:01:00+08:00"
slug: "google-labs-code-design-md-visual-identity-spec"
description: "Google Labs 开源的 DESIGN.md 不只是一个 token 文件格式，它把「Prose 优先」「具体参考 > 形容词列表」「负约束自动从参考对象继承」三条设计哲学编进了规范里。本文拆解 PHILOSOPHY.md 的核心洞察、9 条 lint 规则作为生产契约的意义、Tailwind v3/v4 + W3C DTCG 互操作路径，以及 `.md` 仓库命名的工程意图。"
draft: false
categories: ["技术笔记"]
tags: ["DESIGN.md", "Google Labs", "设计系统", "AI Agent", "Design Tokens"]
---

# DESIGN.md 哲学与采用路径：Google Labs 给 Coding Agent 的设计简报范式

## 学习目标

读完本文后，你应当能够：

- 说出 DESIGN.md 与「普通设计 token 文件」的本质区别——它把**散文（prose）作为规范的中心**，token 只是参考上下文
- 解释 PHILOSOPHY.md 提出的三条设计原则（Prose 优先、具体参考胜过形容词列表、负约束从参考对象自动继承）为什么比「列规范」更适合生成式 Agent
- 把 9 条 lint 规则看作一份"机器可读的生产合同"，知道 `broken-ref` / `contrast-ratio` / `unknown-key` 这几条对应什么样的真实事故
- 在 Tailwind v3 配置、Tailwind v4 主题、W3C DTCG 三种下游格式中，根据团队现状选择合适的 export 路径
- 解释仓库名 `design.md` 与文件名 `DESIGN.md`、npm 包名 `@google/design.md` 三者为何是同一个标识符
- 判断自己的项目是否值得引入 DESIGN.md，什么规模以下不必上

阅读建议：本文和站内另一篇 [DESIGN.md：让 Coding Agents 理解视觉设计的格式规范](/posts/tech/design-md-visual-identity-coding-agents-guide/) 是姐妹篇，那篇从 schema 与架构切入，本篇从哲学、命名、采用路径切入。先读哪一篇取决于你想先了解"怎么用"还是"为什么这样设计"。

## 核心判断

如果只用一句话概括 DESIGN.md 和"把 token 写到 YAML 文件"的区别，那就是：

> **DESIGN.md 把「Prose 是规范中心」这件事直接写进了格式要求里。** Token 不再是渲染指令，而是给 Prose 描述做参考的上下文；Agent 先读散文理解设计意图，再回到 token 取精确数值。

这个判断来自 Google Labs 团队在仓库根目录写的 [PHILOSOPHY.md](https://github.com/google-labs-code/design.md/blob/main/PHILOSOPHY.md)，里面有一段几乎是把整个项目定调的话：

> **The quality of a generated design is determined less by the precision of its values than by how clearly the intent is described.**
> 决定生成质量的不是 token 的精度，而是设计意图被描述得有多清楚。

读到这句话之后，再看 README 里那张把 "Architectural Minimalism meets Journalistic Gravitas" 写在 `## Overview` 下面的 Heritage 示例，意义就完全不同了：那段散文不是装饰、不是 docstring，它是规范的"主菜"。

仓库 [github.com/google-labs-code/design.md](https://github.com/google-labs-code/design.md) 在 2026-04-10 首次提交，到 2026-06-26 已积累 20,274 stars、1,683 forks、Apache-2.0 协议，npm 包名是 `@google/design.md`。它不是单纯的格式玩具——Google Labs 的产品 [Stitch.withgoogle.com](https://stitch.withgoogle.com/docs/design-md/specification) 把这一规范作为设计→代码流程的中间表示。理解这个上下文，再看 9 条 lint 规则与 export pipeline，就能看出 Google 想推的是一条完整链路，不只是一个 lint 工具。

## 目录

- [学习目标](#学习目标)
- [核心判断](#核心判断)
- [一、为什么不是"又一个 token 文件"](#一为什么不是又一个-token-文件)
- [二、PHILOSOPHY.md 三条原则](#二philosophymd-三条原则)
- [三、格式骨架：把 Prose 摆上桌](#三格式骨架把-prose-摆上桌)
- [四、9 条 Lint 规则：把规范变成生产合同](#四9-条-lint-规则把规范变成生产合同)
- [五、Export 三条路径：把 DESIGN.md 送进现有栈](#五export-三条路径把-designmd-送进现有栈)
- [六、`.md` 三重身份：一个标识符的工程意图](#六md-三重身份一个标识符的工程意图)
- [七、Windows 上的 `designmd` shim：被 `.md` 绑架的命令名](#七windows-上的-designmd-shim被-md-绑架的命令名)
- [八、采用路径与适用边界](#八采用路径与适用边界)
- [九、自检清单](#九自检清单)
- [总结](#总结)

---

## 一、为什么不是"又一个 token 文件"

在 DESIGN.md 之前，把设计系统塞进文本格式已经有不少尝试：

- **Style Dictionary**（Amazon 开源）：把 token 转成多平台 JSON / CSS / iOS / Android，思路是"pipeline"。
- **W3C Design Tokens Community Group（DTCG）**：制定 `tokens.json` 行业标准，思路是"互操作"。
- **Salesforce Theo**：单一 JSON token + gulp 转译，思路是"工作流自动化"。

DESIGN.md 的差异在于它**没有把 token 当成规范的中心**。它给 YAML front matter 和 Markdown body 同等地位，但两者的职责完全不一样：

| 层级 | 职责 | Agent 怎么用 |
|:-----|:-----|:-------------|
| YAML Front Matter | 给出**精确数值**（色值、字号、间距、圆角、组件属性） | 解析为 token map，遇到精确匹配直接采用 |
| Markdown Body | 解释**为什么**这样选，以及**什么时候用** | 解析为自由文本，遇到 token 没覆盖的边角场景，按散文描述推断 |

这种双层结构不是 DESIGN.md 的发明——很多项目的 README 都有"用法说明 + 配置示例"——但它是少数**把这种结构形式化进规范**的：哪一段必须是 YAML、哪一段必须是 Markdown、Section 顺序、哪些字段是机器可解析的、哪些字段是给 Agent 看的，全部明确。

更深的一层：DESIGN.md 团队在 PHILOSOPHY.md 里说，token 的值只是 context，**不是 rendering instruction**。这条立场是反直觉的——大多数 token 工具都把"精确渲染"当作卖点。DESIGN.md 反而说：你拿 `#1A1C1E` 给 Agent，它不会知道这个色值该用在哪儿；你写"Deep ink for headlines and core text"，Agent 才知道这是"标题用墨色"。Token 提供锚点，散文提供语义，二者缺一不可。

## 二、PHILOSOPHY.md 三条原则

PHILOSOPHY.md 总共不到 200 行，但密度极高。我把它浓缩成三条可以直接在评审会上引用的原则。

### 原则 1：Prose 是规范中心，token 是上下文

原文摘录：

> The prose is the most vital part of the specification.
> The token values serve as context and are not rendering instructions.

推论：**在 DESIGN.md 里，散文不能写得像"文档"**，而要写得像"设计简报"。Heritage 示例的 `## Overview` 段只有一句"Architectural Minimalism meets Journalistic Gravitas. The UI evokes a premium matte finish — a high-end broadsheet or contemporary gallery."，没有一句废话，但每个词都在为 Agent 锚定一个具体的视觉世界。

如果你的 `## Overview` 写的是"现代、简洁、可信、专业"，那就违反了这条原则——那只是四个形容词。

### 原则 2：具体参考胜过形容词列表

原文摘录：

> A 1970s graduate lecture handout in the tradition of an old and established university evokes a complete world: the one color of ink, the generous margins, the serif set at a reading size, and the absence of decoration.
> That single sentence carries more useful information than a dozen metric values.

对比：

> "Modern, clean, trustworthy, premium" evokes nothing specific. A model creates something in the center of what those words describe, creating an output that is typically generic.

这条原则直接告诉 Agent 怎么写 Overview：不要列举形容词，找一个**真实存在的、读者熟悉的、有视觉风格的对象**，然后说"像那个"。Lecture handout、broadsheet、gallery、subway signage、children's book、technical manual——任选一个，都比 "modern + clean" 信息密度高出一个数量级。

### 原则 3：负约束从参考对象自动继承

原文摘录：

> A clear design reference carries its restrictions automatically. A model knows what a lecture handout is, and it knows what a lecture handout is not. It does not glow or use a gradient.

这一条是设计哲学里最反直觉的部分。常规做法是显式写"不要渐变、不要阴影、不要暗色模式"——但 PHILOSOPHY 团队说，**只要你把参考对象说清楚，负约束是免费送的**。Lecture handout 不会发光、Substack 不会有杂志式封面、Pixar 字体不会出现在严肃报告里——这些"不要"都不需要写。

当然后面紧跟一条补丁："The negative constraints arrive for free when the reference is specific enough. An intentional list of do's and don'ts is useful. A long rambling list is often a sign the description was too vague to carry them."——即**有意整理的 Do's and Don'ts 仍然是有用的**，但它应该是参考对象的"小词典"，而不是"兜底全列"。

PHILOSOPHY.md 给出的 Do's and Don'ts 示例非常具体：不要给标题页加 hero moment、不要再加一个 italic standfirst、不要再加 corner ornaments——每一条都是在把"lecture handout"这个参考对象的边界一条条描清，而不是泛泛说"保持极简"。

把这三条原则合起来看，DESIGN.md 的设计哲学就清楚了：

- **散文是中心**——不要把所有规范都塞进 token 表
- **参考是锚点**——找一个具体事物比列形容词有用
- **负约束是副产品**——参考对象自带否定列表

## 三、格式骨架：把 Prose 摆上桌

有了哲学再看格式骨架就顺了。DESIGN.md 文件只有两层。

### 3.1 YAML Front Matter

YAML 给出机器可解析的精确数值，结构是固定的几类：

```yaml
---
name: Heritage
version: "alpha"          # 当前固定为 "alpha"
description: "..."        # 可选
colors:
  primary: "#1A1C1E"
  tertiary: "#B8422E"
typography:
  h1:
    fontFamily: Public Sans
    fontSize: 3rem
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: -0.02em
rounded:
  sm: 4px
  md: 8px
spacing:
  sm: 8px
  md: 16px
components:
  button-primary:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.on-tertiary}"
    rounded: "{rounded.sm}"
    padding: 12px
  button-primary-hover:
    backgroundColor: "{colors.tertiary-container}"
---
```

四种 token 类型：

| 类型 | 格式 | 示例 |
|:-----|:-----|:-----|
| Color | 任意 CSS 颜色 | `"#1A1C1E"`, `"oklch(62% 0.18 250)"` |
| Dimension | 数字 + 单位 | `48px`, `-0.02em` |
| Token Reference | `{path.to.token}` | `{colors.primary}` |
| Typography | 对象（见下） | `fontFamily` + `fontSize` + `fontWeight` + `lineHeight` + `letterSpacing` + `fontFeature` + `fontVariation` |

Token Reference 是 DESIGN.md 一个值得专门讲的小设计：`{colors.tertiary}` 这种语法让一个 token 引用另一个 token，构建依赖图。Linter 能检测"悬空引用"——写了 `{colors.oops}` 但 colors 里没有 `oops`，会直接 `error` 拦下。Component 嵌套 token 也是这个机制。

### 3.2 Markdown Body

散文部分用 `##` 标题分 Section，顺序固定（允许省略，但出现的必须按这个顺序）：

| # | Section | 别名 |
|:--|:--------|:-----|
| 1 | Overview | Brand & Style |
| 2 | Colors | |
| 3 | Typography | |
| 4 | Layout | Layout & Spacing |
| 5 | Elevation & Depth | Elevation |
| 6 | Shapes | |
| 7 | Components | |
| 8 | Do's and Don'ts | |

Section 顺序本身是规范的一部分——Linter 有 `section-order` 规则专门检查这件事。Agent 在生成 UI 时按固定顺序读 Section，跨项目的一致性能大幅提升。

"Consumer Behavior for Unknown Content" 这条小规则容易被忽略，但它直接回答了一个关键问题："Agent 读到规范没覆盖的内容时，应该怎么办？"

| 情况 | 行为 |
|:-----|:-----|
| 未知 Section 标题 | 保留，不报错 |
| 未知 color token 名 | 只要值合法就接受 |
| 未知 typography token 名 | 接受为合法 typography |
| 未知 component property | 接受 + warning |
| 重复 Section 标题 | 报错，拒绝文件 |

最后一行尤其重要——重复 Section 是**唯一**会让 Linter 拒绝整个文件的情况。其他情况都是宽松处理，这是设计者明确选择的"前向兼容"姿态：让规范保持开放，让用户项目得以渐进扩展。

## 四、9 条 Lint 规则：把规范变成生产合同

DESIGN.md 最有生产价值的一块不是格式，是 9 条 Lint 规则。每条规则在固定严重级别产出 finding，结构化 JSON 输出让 Agent 可以直接消费：

| Rule | Severity | 检查 |
|:-----|:---------|:-----|
| `broken-ref` | error | Token 引用（如 `{colors.primary}`）未解析到任何已定义 token |
| `missing-primary` | warning | 定义了 color 但没有 `primary`——Agent 会自动生成一个 |
| `contrast-ratio` | warning | Component 的 `backgroundColor`/`textColor` 对低于 WCAG AA（4.5:1） |
| `orphaned-tokens` | warning | 颜色 token 定义了但没有任何 component 引用 |
| `token-summary` | info | 统计每个 section 多少 token |
| `missing-sections` | info | 其他 token 存在时，optional section（spacing / rounded）缺失 |
| `missing-typography` | warning | 定义了 color 但没定义 typography——Agent 会用默认字体 |
| `section-order` | warning | Section 出现顺序不符 |
| `unknown-key` | warning | 顶层 YAML key 像是已知 schema key 的拼写错误（如 `colours:` → `colors:`） |

把规则表当成"生产合同"来读，里面藏着几个有意思的工程选择：

1. **`broken-ref` 唯一是 error**。其他都是 warning。意思很直接：唯一会让 Lint 拒绝合并的，是"token 引用悬空"——这是 Agent 必出错的事。其他都允许通过，但给出建议。
2. **`contrast-ratio` 默认阈值是 WCAG AA 4.5:1**，不是 AAA 7:1。这是设计者在"严格可访问性"和"现实设计系统多样性"之间做的取舍。
3. **`orphaned-tokens` 是 warning 不是 error**。意思是"你定义了但没被任何 component 用的颜色"会被标出来，但不会拒绝——很多 token 是"future-proof"用，规则理解这一点。
4. **`unknown-key` 只对看起来像已知 key 拼错的告警**，自定义扩展 key 静默。这条避免了"严格 linter 把未来扩展打回去"的常见错误。
5. **存在 `missing-primary` 和 `missing-typography` 这种"提示规则"**——它们不报错，但告诉 Agent："如果你看到这种不完整规范，你会按默认行为补全"。这是把 Agent 退化路径写进了规范。

把 Linter 当 Agent 守门员来用，可以这样集成到 CI：

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

`lint` 命令 exit code 在有 error 时为 1，因此 `npx @google/design.md lint DESIGN.md` 自然成为 PR 阻塞点。

Linter 也作为库暴露：

```typescript
import { lint, DEFAULT_RULES } from '@google/design.md/linter';

const report = lint(content);                       // 用默认 9 条规则
// report.findings: Finding[]
// report.summary:  { errors, warnings, info }
// report.designSystem: 解析后的 DesignSystemState

// 也可以扩展自定义规则
const noGradientRule = {
  name: 'no-gradients',
  severity: 'warning',
  check: (state) => {
    const findings = [];
    for (const [name, comp] of Object.entries(state.components)) {
      if (comp.backgroundColor?.includes('gradient')) {
        findings.push({
          severity: 'warning',
          path: `components.${name}.backgroundColor`,
          message: 'Gradient backgrounds are prohibited. Use solid colors.',
        });
      }
    }
    return findings;
  },
};

const customReport = lint(content, {
  rules: [...DEFAULT_RULES, noGradientRule],
});
```

这条扩展点让每个团队可以在 9 条基础上加自家规则——比如"禁止渐变"、"禁止使用某个字体"、"按钮高度必须 ≥ 40px"——Linter 充当"组织级设计守门员"。

## 五、Export 三条路径：把 DESIGN.md 送进现有栈

格式规范的真正考验是"和现有工具链接得上吗"。DESIGN.md 的答案是 `export` 子命令，覆盖三种常见下游：

```bash
# 1. Tailwind v3 — 传统 JSON 配置
npx @google/design.md export --format json-tailwind DESIGN.md > tailwind.theme.json
# （--format tailwind 是 json-tailwind 的别名，向后兼容）

# 2. Tailwind v4 — 新的 CSS 主题块
npx @google/design.md export --format css-tailwind DESIGN.md > theme.css

# 3. W3C Design Tokens Format Module
npx @google/design.md export --format dtcg DESIGN.md > tokens.json
```

三条路径对应三种团队现实：

| 现有栈 | 推荐 export | 落地方式 |
|:-------|:------------|:---------|
| Tailwind v3 项目（`tailwind.config.js`） | `json-tailwind` | 导出后 `module.exports = require('./tailwind.theme.json').theme.extend` |
| Tailwind v4 项目（`@theme` in CSS） | `css-tailwind` | 把 `@theme { ... }` 块拷进根 CSS |
| 多端 Figma / iOS / Android 同步 | `dtcg` | 配合 Style Dictionary 等消费 DTCG JSON |
| Agent 直接消费 | 不必 export | 让 Agent 直接读 DESIGN.md |

注意第三种是反直觉但正确的路径：很多 Agent 场景下，**根本不需要 export**。Agent 直接读 DESIGN.md 的 YAML + 散文，比解析 `tailwind.config.js` 拿到更多信息（散文段只在 DESIGN.md 里）。

`export` 输出的 Tailwind v4 CSS 块用 Tailwind v4 自己的命名空间：

```css
@theme {
  --color-*: ...;       /* 颜色 token 映射到 --color-* */
  --font-*: ...;        /* 字体 */
  --text-*: ...;        /* 字号 */
  --leading-*: ...;     /* 行高 */
  --tracking-*: ...;    /* 字距 */
  --font-weight-*: ...; /* 字重 */
  --radius-*: ...;      /* 圆角 */
  --spacing-*: ...;     /* 间距 */
}
```

这意味着 v4 用户的 `bg-primary` / `text-h1` / `rounded-md` / `p-md` 可以直接用，不用再写自定义 className。

`dtcg` 输出符合 [W3C Design Tokens Format Module](https://tr.designtokens.org/format/)——`$type` / `$value` 风格——可以接入 Style Dictionary、Tokens Studio for Figma 等生态。Style Dictionary 的现有用户可以把 DESIGN.md 当作"上游 source"。

最后一条命令是 `spec`：

```bash
npx @google/design.md spec                  # 输出 spec markdown
npx @google/design.md spec --rules          # 末尾追加当前 9 条 lint 规则
npx @google/design.md spec --rules-only --format json
```

`spec` 设计的本意是**注入到 Agent prompt**：你在 system prompt 里放"读取项目根目录的 DESIGN.md，再执行 `npx @google/design.md spec` 拿到 spec 全文当作额外上下文"。这一点和 Stitch.withgoogle.com 的产品形态高度吻合。

## 六、`.md` 三重身份：一个标识符的工程意图

DESIGN.md 仓库命名有一个常被忽略的细节：`design.md` 这个名字**同时是 GitHub 仓库名、文件名、npm 包名的一部分**，三者共用同一个标识符。

```text
GitHub 仓库：  github.com/google-labs-code/design.md
文件名：      DESIGN.md   （项目根目录）
npm 包：      @google/design.md
CLI 入口：    designmd  （Windows 兼容 shim，详见下节）
品牌名：      DESIGN.md
```

这个"重名"不是巧合，是工程选择。代价和收益都很明确：

- **代价 1：Windows 命令名冲突**——见下节 `designmd` shim。
- **代价 2：搜索/GitHub SEO**——`design.md` 这种短词在 GitHub 全局搜几乎搜不到，团队需要靠完整 owner 路径定位。
- **代价 3：和现有项目命名规范冲突**——`@google/design.md` 名字里带点号，npm 历史上没有这种先例。

收益同样清晰：

- **URL 即规范**：`github.com/google-labs-code/design.md` 直接就是 spec 仓库的入口，没有 "spec" / "docs" 之类的二级路径。
- **包名即品牌**：`npm install @google/design.md` 之后 `npx @google/design.md lint` 看上去就很自然。
- **跨平台一致**：仓库名 = 文件名 = 包名根，复制 README 提到 DESIGN.md 时不用解释是哪一个。

更妙的是 **.md 这个扩展名本身的语义**——它是个 Markdown 文件，所有 GitHub 渲染、所有编辑器、所有 Agent 都能直接读。如果仓库叫 `design-system-spec`、文件名叫 `design-spec.md`，反而要解释一次"哪个是规范的入口"。

读 PHILOSOPHY.md 的时候你也能感受到这条选择：项目以 .md 后缀出现，意思是"这是一个用 Markdown 描述的设计规范"——**这个描述本身才是产品的全部**。CLI 工具 `@google/design.md` 只是这个 spec 的"配套工具"，而不是反过来。

## 七、Windows 上的 `designmd` shim：被 `.md` 绑架的命令名

`.md` 既是品牌名也是 npm bin 名，会撞上一个 Windows 特有的问题：Windows 的命令解析把 `.md` 视作 Markdown 文件关联名，PowerShell 在某些情况下会**优先打开 Markdown 编辑器**而不是执行 bin。

DESIGN.md 仓库的 README 里有专门一节解释这件事：

> On **Windows/PowerShell**, this direct form can produce no output (or open `DESIGN.md` in your Markdown editor) because the `.md` suffix in the `design.md` bin name collides with the Windows Markdown file association during command resolution. Run the dot-free `designmd` alias instead — point `npx` at the package with `-p`, then invoke `designmd`:
>
> ```bash
> npx -p @google/design.md designmd lint DESIGN.md
> ```

`designmd` 是同一个入口点的 shim，跨平台行为一致。`package.json` scripts 里同样要用 alias：

```jsonc
{
  "scripts": {
    "design:lint": "designmd lint DESIGN.md"
  }
}
```

在 macOS / Linux 上 `npx @google/design.md lint DESIGN.md` 一切正常，Windows 上要先切换到 `designmd`。这是一个典型的"文件名后缀绑架命令名"问题——值得所有做工具链的人在 README 里写一段"Windows tip"。

另一个 Windows 坑：`@google/design.md` 这种带点号的 scope，在某些 PowerShell 配置下 `npm install` 会把 `@` 当特殊字符。解决方案是加引号：

```bash
npm install "@google/design.md"
```

如果遇到 `npm error ENOVERSIONS`（"No versions available for @google/design.md"），按 README 的诊断流程先看 `npm config get registry`——99% 是 `.npmrc` 里的 corporate mirror 没有同步这个包。

## 八、采用路径与适用边界

不是所有项目都该上 DESIGN.md。把它当"必选规范"会拖慢小项目；把它当"先评估再决定"则价值最大。

### 8.1 适合采用的场景

- **AI Coding Agent 频繁生成 UI**——Claude Code、Cursor、Copilot 生成前端代码，DESIGN.md 让 Agent 有持久上下文。
- **多 Agent / 多设计师协作**——每个贡献者用同一份 DESIGN.md，AI 生成产物跨人一致。
- **设计系统需要版本管理**——DESIGN.md 是纯文本，可 git diff、可 code review、可回溯。
- **下游要用 Tailwind / DTCG 多端**——export pipeline 一行命令出三套产物。

### 8.2 不必采用的场景

- **页面数 < 5、视觉复杂度低**——单页营销站、一次性活动页，开 DESIGN.md 的维护成本高于收益。
- **设计系统完全在 Figma 里、Agent 不直接读规范**——这种情况下 Style Dictionary + Tailwind 主题已够，DESIGN.md 加一层。
- **组件总数 < 20**——PHILOSOPHY 的"prose 优先"在组件少时收益不明显，散文和组件表信息密度接近。
- **已有强约束的设计系统**（如 Material Design / Ant Design）——直接用上游规范，不要再造一层。

### 8.3 渐进采用建议

如果决定要上，建议按这个顺序：

1. **第 1 周：写一个最小 DESIGN.md**——只放 `name` + `colors` + `typography` + 一段 `## Overview`。跑 `npx @google/design.md lint` 让 Linter 当 reviewer。
2. **第 2 周：接 Tailwind export**——`json-tailwind` 或 `css-tailwind`，让现有项目用上规范。
3. **第 3 周：把 `## Do's and Don'ts` 写出来**——这时候 Linter 的 `unknown-key` 不会卡，但写作本身会暴露设计冲突。
4. **第 4 周：接 CI 阻断**——`npx @google/design.md lint DESIGN.md` 放到 PR check，error 直接拒绝合并。
5. **稳定后：加自定义 lint 规则**——比如"按钮最小高度 40px"、"字体禁用列表"，把组织级设计守门员职责挂到 Linter。

## 九、自检清单

把这份清单当作"该不该引入 DESIGN.md"的最后决策表：

- [ ] 项目至少有一个 Coding Agent（Claude Code / Cursor / Copilot）会生成 UI 代码
- [ ] 组件数量 ≥ 20，或者有 5+ 个组件会被多个页面复用
- [ ] 设计系统需要跨人 / 跨 Agent 一致（多人协作或多会话 Agent）
- [ ] 团队愿意写"设计简报"风格的散文（至少 200-500 字 Overview + 各 Section 解释）
- [ ] 下游至少一个 Tailwind v3 / v4 / DTCG 消费方
- [ ] CI 流程允许引入新的阻断 check
- [ ] 团队接受 `alpha` 版本的不稳定性（`@google/design.md` 当前是 alpha，规范可能演化）

如果 7 条命中 5 条以上，DESIGN.md 值得一试。命中 3 条以下，建议先观察 3 个月看上游 API 是否稳定。

## 总结

DESIGN.md 不是一个"标准 token 文件格式"，而是一份**给 Coding Agent 的设计简报规范**。它的设计哲学核心是三条：

1. **Prose 是中心**——token 是给散文做参考的上下文，不是渲染指令
2. **具体参考胜过形容词**——找一个真实存在的、有视觉风格的对象
3. **负约束从参考对象自动继承**——不要"穷举不要"，把参考说清楚

9 条 Lint 规则 + 自定义扩展点让规范可以**当作生产合同**，Tailwind v3/v4 + W3C DTCG 三条 export 路径让规范**接得上现有栈**，`.md` 三重身份和 `designmd` Windows shim 让规范**全平台可用**。

如果你的项目要让 Coding Agent 生成视觉一致的前端 UI，DESIGN.md 是当前最值得评估的方案之一——前提是你愿意写散文，而不只是写 token 表。

---

> **延伸阅读**：
> - 仓库：[github.com/google-labs-code/design.md](https://github.com/google-labs-code/design.md)
> - 官方 Spec：[stitch.withgoogle.com/docs/design-md/specification](https://stitch.withgoogle.com/docs/design-md/specification)
> - 哲学文档：[PHILOSOPHY.md](https://github.com/google-labs-code/design.md/blob/main/PHILOSOPHY.md)
> - W3C Design Tokens：[designtokens.org](https://www.designtokens.org/)
> - 姐妹篇：[DESIGN.md：让 Coding Agents 理解视觉设计的格式规范](/posts/tech/design-md-visual-identity-coding-agents-guide/)
