---
title: "Hallmark 深读：Custom 分支协议、DNA 提取与跨 AI 工具的设计传递"
slug: nutlope-hallmark-invisible-watermark-2026
github_repo: "Nutlope/hallmark"
date: 2026-08-05T22:35:00+08:00
lastmod: 2026-08-05T22:35:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["设计系统", "Skill", "Claude Code", "Cursor", "Codex", "DNA 提取"]
description: "从 Custom 分支协议、DNA 三层提取、design.md 跨工具传递三个角度深读 Hallmark——Together AI 出品的设计 skill 如何用元规则和便携设计系统打破 AI 生成网页的同质化。"
authors: ["钳岳"]
---

# Hallmark 深读：Custom 分支协议、DNA 提取与跨 AI 工具的设计传递

## 为什么再读一次 Hallmark

Hallmark 是 Together AI 出品的设计 skill，安装在 Claude Code、Cursor、Codex 三大 AI 编程助手中，核心使命是让 AI 生成的网页「看起来像人做的，不像 AI 吐的」。关于它的 4 动词接口（默认创建 / `audit` / `redesign` / `study`）、57 条 slop-test 闸门、20 个 catalog 主题的基本架构，已有前文覆盖。

本文不再重复这些内容。我们从三个更深的切口切入：**Custom 分支如何用元规则实现「有约束的自由」**、**`study` 动词的 DNA 提取如何将设计拆解为可迁移的三层结构**、以及 **`design.md` 便携设计系统如何让一份设计在 Claude Code / Cursor / Codex 之间无缝传递**。这三个机制共同回答了一个前文未展开的问题：当 AI 编程助手从「单工具」走向「多工具协作」时，设计系统怎么跟着走。

## 项目坐标速查

| 维度 | 数据 |
|------|------|
| 仓库 | Nutlope/hallmark |
| License | MIT |
| 出品方 | Together AI |
| 演示站 | usehallmark.com（含 12 个 catalog 主题示例 + Custom 分支示例） |
| 安装 | `npx skills add nutlope/hallmark` |
| 引擎适配 | Claude Code (`~/.claude/skills/hallmark/`) / Cursor (`.cursor/rules/hallmark.mdc`) / Codex (`~/.codex/skills/hallmark/`) |

## 切口一：Custom 分支——有约束的从零设计

### 问题：catalog 主题不够用怎么办

Hallmark 默认走 catalog 路线：20 个命名主题（Specimen、Midnight、Brutal、Garden、Atelier、Newsprint、Terminal、Manifesto、Almanac、Sport、Studio、Riso、Bloom、Coral、Cobalt、Aurora、Editorial、Carnival、Lumen、Hum），每个主题是一组固定的 paper-band + display-style + accent-hue 组合。配合 diversification 规则（连续两次输出必须在三个轴中至少一轴不同），catalog 已经能产出结构多样的页面。

但 catalog 有天花板。当一个 brief 带有强烈的品牌意图——比如用户说「用我们的赤陶色」或者描述了一个 catalog 里没有任何主题能承载的多属性美学（「苔藓、地衣、柔粉、草本」）——catalog 的任何选择都会是妥协。这时 Hallmark 需要从 catalog 切换到 Custom 分支。

### Custom 分支的触发：信号检测，不是用户手动选

Custom 不是用户在每次 prompt 中需要主动声明 `--theme custom` 的选项。Hallmark 在 Step 1 的 Design-context gate 中内建了**信号检测**机制，自动判断 brief 是否需要走 Custom 路线。根据 `custom-theme.md` 协议，五个触发信号如下：

1. **显式请求**——用户说出 "custom theme"、"tailored to our brand"、"make it ours"、"something unique" 等关键词
2. **命名品牌色**——用户给出具体的锚定色（hex / OKLCH / 品牌名），如「use our terracotta」、「品牌红是 #c0392b」
3. **多属性美学描述**——三个以上 vibe 词指向一个 catalog 无法承载的特定感觉，如「苔藓、地衣、柔粉、草本」或「深夜、霓虹、粗野主义熟食店」。但单个形容词（「温暖的」、「技术的」）不算信号——那是 tone，catalog 已经覆盖
4. **品牌情绪参考附件**——用户附带色板、moodboard、Pantone 色卡（注意：如果附带的是页面截图，则路由到 `study` 而非 Custom）
5. **独特的结构愿景**——brief 命名了一个结构或构图，而不只是配色或情绪：「no theme / from scratch / fully bespoke / art-direct it」，或者一个 catalog 宏结构库中没有对应条目的页面形状（滚动拼贴诗、车票形页面、交互式元素周期表）

如果以上五个信号都没有触发，Hallmark **不提 Custom 的存在**，静默走 catalog。这是一个刻意的 UX 决策：大多数 brief 不需要 Custom，在不需要时提及它只会增加摩擦。

### Custom 的两层深度：Tuned 与 Bespoke

Custom 不是一个开关，而是一个光谱。`custom-theme.md` 定义了两个深度：

**Tuned（调校级）**：保留 Hallmark 的宏结构、组件原型、页面骨架，只为这一个 brief 重新构造 OKLCH 调色板 + 免费字体配对。自由的只是「组合」——颜色和字体的搭配是独一无二的，但页面结构仍来自 Hallmark 的宏结构库。这是 Custom 的浅水区，也是大多数 Custom brief 的落点。

**Bespoke（定制级）**：当 brief 的结构本身就是诉求时，Custom 进入深水区。不只是调色板和字体，页面的**结构和构图也从第一性原则设计**——丢弃 catalog 的宏结构、丢弃 genre 路由、丢弃固定的原型目录。唯一的约束是 slop-test 闸门（详见下文）。`custom-theme.md` 的原文说得很清楚：

> *"It drops the named-theme tokens, the genre cluster routing, the fixed macrostructure + archetype catalog... It keeps every universal slop-test gate — the guarantee that survives the freedom."*

两层深度的工程含义不同：Tuned 是「换皮」，Bespoke 是「换骨」。两者的对比如下：

| 维度 | Tuned（调校级） | Bespoke（定制级） |
|------|-----------------|-------------------|
| 自由范围 | 调色板 + 字体配对（组合唯一） | 调色板 + 字体 + **页面结构**（从第一性原则设计） |
| 宏结构 | 保留 Hallmark 的 21 个命名宏结构 | 丢弃——为 brief 重新构图 |
| Genre 路由 | 保留（editorial / atmospheric / modern-minimal / playful） | 丢弃——不做 genre 默认 |
| 组件原型 | 保留（N1a–N13 导航 / Ft1–Ft8 页脚 / H1–H6 Hero） | 丢弃——鼓励 novel hero / nav / section |
| Diversification 轮换 | 参与（与 catalog 和其他 Custom 按三轴规则轮换） | 豁免（one-off，不参与轮换，但不克隆最近的 bespoke run） |
| Slop-test 闸门 | **全部生效** | **全部生效** |
| 典型 brief | 「用我们的赤陶色 + 手工编辑风」 | 「从零设计一张车票形页面」 |

两者的共同点：同一条入口（Custom 分支）、同一次确认（一个跟进问题）、同一套闸门（57 条 slop-test）、同一个 stamp 格式（记录 route / structure / idea / axes / gates）。

### 兜底保护：vanilla briefs never see it

Custom 分支的一个关键设计是**静默隔离**。README 的 Custom 章节有一句话值得展开：

> *"It stays a quiet branch; vanilla briefs never see it."*

这不是一句宣传语，而是对 Custom 滥用的工程级防护。具体实现包含三层：

**第一层：信号门槛**。单个形容词不触发 Custom，必须满足上述五个信号之一。这过滤了绝大多数「其实 catalog 就够了」的 brief。

**第二层：一次确认**。即使信号触发，Hallmark 也只问一个跟进问题：「这个 brief 似乎 Custom 比 catalog 更合适。要我构造一个 Custom OKLCH 调色板 + 免费字体配对，还是继续走 catalog？」用户沉默 → 走 catalog。Default 永远是 catalog。

**第三层：palette 构造的规则约束**。Custom 并非「自由发挥」。`custom-theme.md` 的 § B 定义了严格的 palette 构造流程：锚定色优先（OKLCH 色彩空间，chroma 钳制在 0.12–0.20），paper 色必须向锚定色微染（chroma 0.005–0.020），ink 色根据 paper 亮度决定方向，所有灰阶以 6–10% L 步阶排布。这些规则来自 `color.md`，Custom 不能绕过。

三层保护的结果是：Custom 既给了「catalog 不够用时的自由」，又通过规则约束确保这份自由不会滑向新的 AI 同质化（比如每次 Custom 都生成赤陶色 + Fraunces 斜体）。

### Custom 仍走全部 57 条 slop-test 闸门

这是 Custom 分支最重要的工程约束。README 原文：

> *"Same 57 slop-test gates, no template underneath."*

57 条 slop-test 闸门是 Hallmark 不可协商的约束层，覆盖纯白禁令（Gate 7）、零色度中性灰禁令（Gate 22）、accent 占比 ≤5%（Gate 23）、斜体标题禁令（Gate 38a）、虚构指标禁令（Gate 46）、重绘 UI chrome 禁令（Gate 47）、mid-render token 即兴禁令（Gate 48）等。Custom——不管是 Tuned 还是 Bespoke——**每一条闸门照跑不误**。

这意味着 Custom 的自由度体现在「选什么颜色、配什么字体、页面什么结构」，而不是「要不要遵守反 AI 味的规则」。规则是地板，Custom 在地板之上自由设计，但不能穿透地板。

### 元规则：规则之上还有规则

Custom 分支揭示了一个有趣的设计哲学：**元规则（meta-rules）**。Hallmark 不只有「禁止做什么」的低阶规则（57 条闸门），还有「什么时候允许打破常规」的高阶规则：

- catalog 主题不匹配时，允许走 Custom——但触发条件由元规则定义
- Custom 的 Bespoke 深度允许丢弃宏结构——但 slop-test 闸门由元规则保护
- diversification 规则在 Custom 之间同样生效——连续两次 Custom 必须在至少一个轴上不同

这不是简单的「规则叠加规则」，而是一个**分层规则系统**：底层是不可协商的闸门（slop-test），中层是可组合的主题系统（catalog + Custom），高层是调度规则（何时用 catalog、何时用 Custom、Custom 之间如何多样化）。这种分层设计让 Hallmark 在「严格」和「灵活」之间找到了一个精确的平衡点。

### 实操：如何判断你的 brief 是否需要走 Custom

如果你正在使用 Hallmark，可以用以下决策树快速判断：

1. brief 是否包含 3 个以上指向特定感觉的 vibe 词？（如「苔藓、地衣、柔粉、草本」）→ **是 → Custom（Tuned）**
2. brief 是否命名了一个具体的品牌色？（hex / OKLCH / 品牌色名）→ **是 → Custom（Tuned）**
3. brief 是否明确说「from scratch / fully bespoke / art-direct it」或描述了一个 catalog 无法承载的页面形状？→ **是 → Custom（Bespoke）**
4. brief 是否只有 1-2 个普通形容词？（如「温暖的」「技术的」）→ **否 → Catalog（静默走）**
5. 以上都不触发 → **Catalog（默认）**

这个决策树对应的就是 Hallmark Step 1 的信号检测逻辑。大多数 brief 会落在第 4-5 条——catalog。

## 切口二：DNA 提取——`study` 动词的三层结构拆解

### study 做什么

`hallmark study <screenshot | URL>` 是四个动词中最特殊的一个：它不产出页面，而是**提取设计 DNA**。README 的描述：

> *"Extract the DNA from a design you admire: macrostructure, type-pairing, colour anchor. Refuses pixel-clones and paid templates. Optionally emits a portable `design.md` for handoff to other AI tools."*

DNA 这个比喻精确且有用。`study` 提取的不是像素级的「这个按钮是什么颜色、这个标题是多少字号」，而是结构级的「这个页面用的是 Marquee Hero 宏结构 + 斜体编辑衬线 display + 中性 grotesque body + 去饱和森林绿锚定色 + 发丝级分割线 + 一次编排式入场动画」。前者是外观复制，后者是骨架理解。

### 三层 DNA 提取

根据 `study.md` 协议，DNA 提取按严格的五步协议执行。其中前三步对应 DNA 的三个结构层：

**第一层：Macrostructure（宏结构）**。`study` 将目标页面匹配到 Hallmark 的 21 个命名宏结构中最接近的一个（或两个相邻的）。宏结构是一个完整的页面形状——标题位置、主体构成、分割线语言、按钮语气、图片处理方式、入场动画——打包为一个命名选择。提取宏结构的意义在于：它决定了页面的节奏感，而不是视觉细节。

**第二层：Type-pairing（字体配对）**。`study` 读取字体的**角色**而非字体名（图像模式下不猜字体名，只记「斜体编辑衬线 display + 中性 grotesque body」）。URL 模式下可以从 CSS 中读取确切字体声明。字体配对层的提取结果是「display 角色 + body 角色 + 可选 label 角色」的组合，这决定了页面的文字气质。

**第三层：Colour anchor（色彩锚定）**。`study` 提取三个色彩维度：paper 亮度带（dark / mid / light）、paper 色相偏移（暖 / 冷 / 中性 / 彩色）、accent 色相带和占地比例。色彩锚定层的提取结果是「一个亮度带 + 一个色相方向 + 一个 accent 色相 + accent 占比」，这决定了页面的情绪温度。

三层加在一起，就是一段完整的 DNA 描述。`study.md` 的说法：

> *"A designer who likes a reference site does not photocopy it. They look at it long enough to say 'ah — that's a Marquee Hero with a single column body, italic-editorial display paired with monospace labels, anchored on a desaturated forest green at maybe 3% footprint, with hairline rules and one orchestrated entrance.' Then they go build something different with the same skeleton."*

### 拒绝像素克隆：prompt guard + 强制抽象

`study` 的一个核心原则是**拒绝像素克隆**。这不是通过机器学习检测实现的，而是通过两层 prompt guard：

**第一层：拒绝列表**。`study.md` 维护了一个自动拒绝域名列表，覆盖付费模板市场（ThemeForest、TemplateMonster、Framer Templates、Webflow Templates、Gumroad 模板）和设计师展示平台（Dribbble、Behance）。URL 模式下，匹配到这些域名直接拒绝，不发起 WebFetch。

**第二层：强制抽象**。即使源页面通过了拒绝检查，`study` 的五步协议本身就在做抽象——它不记录「按钮圆角 8px、背景色 #F5F5F0」，而是记录「paper 是暖色调 near-white、accent 是 chromatic-green 约 145°」。从像素到结构层抽象的过程，本身就是一种反像素克隆的保护。

此外，`study` 对「锁定 DNA」（emit design.md）有比「诊断」（diagnosis only）更严格的拒绝层。URL 模式下提取 DNA 到 design.md 需要用户声明来源是自己作品或自己品牌的公共参考，第三方的 URL 会被拒绝。这是一个不对称设计：诊断可以宽松（看一眼学结构），但锁定 DNA 要严格（不能把别人的设计系统偷走）。

### 图像模式 vs URL 模式的信息差

`study` 接受两种输入：截图（图像模式）和 URL（URL 模式）。两者的 DNA 提取协议相同，但信息精度有系统性差异：

| 维度 | 图像模式 | URL 模式 |
|------|---------|---------|
| Surface（色彩） | 估算色带和占比 | 从 CSS custom properties 读取确切 OKLCH / hex 值 |
| Type（字体） | 只记角色（「中性 grotesque body」），不猜字体名 | 角色加确切字体名（从 `@font-face`、Google Fonts link、`next/font` 读取） |
| Structure（结构） | 从可见区域推断 | 从真实 DOM（`<nav>`、`<section>`、`<main>`、`<footer>`）推断 |
| Motion（动效） | 静态截图不可见，默认假设 | 从 `<script src>` 和 CSS `@keyframes` / `transition` 读取 |
| Rhythm（节奏） | 可直接从视觉 gestalt 观察 | **不可观察**——HTML 无法告诉你密度和不对称感 |

两者的信息差形成互补关系：URL 模式在色彩、字体、结构、动效上更精确，但在节奏感上是盲区；图像模式精度较低，但能捕捉到页面整体的 gestalt。`study.md` 在 URL 模式的诊断报告中会明确标注这一盲点：

> *"I read this from the page's HTML, not a screenshot — I can name the macrostructure, the type, the colour, and the motion, but I can't tell you whether the rhythm reads generous or templated."*

这是一个诚实的设计：不掩盖工具的局限性，而是把局限性暴露给用户，让用户决定是否需要补充一张截图。

## 切口三：design.md——跨 AI 工具的设计传递格式

### 为什么用 Markdown 而不是 JSON/YAML

Hallmark 的 `design.md` 是一个可选的便携设计系统文件，由用户显式请求（说 "lock the system" 或 "give me a design.md"），写入项目根目录。后续 Hallmark 运行时优先读取这个文件，将其作为项目的锁定设计系统。

格式选择上，`design.md` 用 Markdown 而非 JSON/YAML，这个决策背后有明确的工程哲学：

**Markdown 是给 AI 读的，也是给人读的**。`design.md` 的目标读者不是解析器，而是 AI 编程助手和人类开发者。AI 读 Markdown 是自然能力（训练数据中大量 Markdown），人读 Markdown 不需要任何工具。JSON/YAML 需要工具才能人类可读，且对于「设计系统」这种需要叙述性上下文（为什么选这个 genre、motion stance 是什么意思）的内容，结构化格式反而不如 Markdown 表达力强。

**Markdown 内嵌代码块可以携带 CSS**。`design.md` 的核心是一个 `tokens.css` 代码块，包含完整的 OKLCH 调色板变量声明。CSS 自定义属性（`var(--color-accent)`）本身就是设计 token 的载体，直接嵌在 Markdown 代码块中，AI 工具可以直接提取并使用，人类也能直接复制到项目中。

### design.md 的结构

根据 `design-md.md` 协议，一个完整的 `design.md` 目标约 45 行，包含以下区块：

- **System**：genre、宏结构、主题路由、三轴值——一段话定位设计方向
- **Tokens**：`:root` CSS 代码块，包含 `--color-*` / `--font-*` / `--space-*` / `--ease-*` / `--dur-*` / `--radius-*` 全部命名 token——设计系统的执行层
- **CTA voice**：主按钮和次按钮的填充、圆角、padding 规则——交互元素的语气
- **Motion stance**：动效策略（silent / 1-2 reveal primitives / motion-cut）加 reduced-motion 回退——动效的约束
- **Exports**：指向项目中 `tokens.css` 的路径，以及扩展到 Tailwind v4 `@theme`、DTCG `tokens.json`、shadcn/ui CSS 变量的指令——跨格式兼容

这个结构的关键特点是**渐进式信息密度**：System 是一句话的摘要，Tokens 是可直接粘贴的 CSS，CTA voice 和 Motion stance 是补充规则。AI 工具可以根据需要读取不同深度的信息——快速扫描只看 System，精确实现看 Tokens。

### 两条产出路径

`design.md` 有两条产出路径，每条的信号源和严格度不同：

**路径一：Default verb → lock the system**。用户在 default verb 的构建-迭代流程中，对当前结果满意后说 "lock the system"。`design.md` 的 token 来自当前构建的内存状态，没有拒绝层（用户拥有自己迭代出来的构建），不包含 Provenance 区块。

**路径二：Study verb → lock the DNA**。用户在 `study` 诊断成功后说 "lock the DNA" 或 "give me a design.md"。`design.md` 的 token 来自提取的 DNA——URL 模式下精确来自 CSS，图像模式下来自估算的色带。这条路径有更严格的拒绝层（前文提到的 URL-mode attestation），且必须包含 Provenance 区块（记录来源、模式、日期、attestation 回答、置信度笔记）和 Notes 区块（携带「不应搬运的反模式列表」）。

两条路径产出的文件格式完全一致，后续 Hallmark 运行不区分来源。这意味着一个通过 `study` 从某品牌参考站提取 DNA 并锁定的 `design.md`，和一个通过 default verb 迭代锁定的 `design.md`，在后续使用中享有同等地位。

### 跨 AI 工具传递的范式意义

`design.md` 的真正价值不在于它是一个设计系统文件——这样的文件格式有很多（Style Dictionary、DTCG tokens.json、Tailwind config）。它的价值在于**它是第一个为 AI 编程助手之间的互操作设计的便携设计系统格式**。

考虑这个工作流：

1. 在 Claude Code 中用 `hallmark default` 设计一个落地页，迭代到满意
2. 说 "lock the system" → 生成 `design.md`
3. 打开 Cursor，导入同一个项目——Cursor 读到 `design.md`，知道当前项目的设计系统
4. 在 Cursor 中用 `hallmark redesign` 修改某个组件——Hallmark 的 pre-flight scan 第一步就是检测 `design.md`，存在则 defer to it
5. 切到 Codex 做另一个页面——同样的 `design.md` 被读取，设计系统保持一致

这个流程的关键在于：`design.md` 不是某个 AI 工具的私有格式，而是 Hallmark skill 在三大工具之间共享的**公共契约**。skill 层面的互操作（同一个 skill 安装在三个工具中）加上数据层面的互操作（同一个 `design.md` 在三个工具间传递），构成了一个跨 AI 工具的设计系统传递范式。

## CSS 注释中的 macrostructure 印章

最后展开一个容易被忽略但设计精巧的细节。README 提到：

> *"Each page is self-contained HTML + CSS, stamped with its macrostructure in the CSS comment."*

Hallmark 在每个生成页面的 CSS 顶部强制写入一个结构化注释块。这个「印章」（stamp）不是装饰，而是承载了三重功能：

**功能一：diversification 的依据**。Hallmark 的 diversification 规则要求连续两次输出不能共用同一个宏结构。规则的前提是「知道上一次用了什么」——信息就来自 stamp。Step 2.5 的 `.hallmark/log.json` 记录了历史选择，stamp 是嵌入在产出物中的冗余备份。

**功能二：audit 的读入入口**。`hallmark audit <target>` 读取目标代码时，首先扫描 CSS 顶部的 stamp，从中获取宏结构名、主题名、三轴值、context 来源（用户提供还是推断）。这让 audit 不需要重新分析整个页面就能定位到「这个页面用了 Hallmark 的什么配置」。

**功能三：人类可读的 metadata trail**。stamp 的格式是一个多行 CSS 注释，包含 macrostructure 名、hero 原型和参数、主题路由和 vibe、paper 和 accent 的 OKLCH 值、display 和 body 字体名、三轴值、是否来自 study、context 类型、版本号。对于人类开发者来说，打开一个 CSS 文件就能看到这段 metadata，比翻找某个 `.hallmark/` 目录下的 JSON 文件直观得多。

Custom（Tuned 级）的 stamp 示例：

```css
/* Hallmark · macrostructure: Long Document · H5 hero knobs: salutation=time-stamp, body=2 paragraphs, signoff=initials
 * theme: custom · vibe: "archival warmth, hand-set, no varnish" · paper: oklch(94% 0.020 65) · accent: oklch(58% 0.16 35)
 * display: Fraunces italic · body: Source Serif 4 · axes: light / italic-serif / chromatic-terracotta
 * studied: no · context: explicit · v0.8.0
 */
```

Custom（Bespoke 级）的 stamp 额外包含 structure 和 idea 字段：

```css
/* Hallmark · route: custom (bespoke) · structure: <one-line shape> · idea: "<central move>"
 * paper: oklch(...) · accent: oklch(...) · display: <font> · body: <font>
 * axes: <paper-band> / <display-style> / <accent-hue> · gates: all-pass · studied: no
 */
```

在文件内部留 metadata 的做法让人想到 git 的 blame 信息——不是外部系统的附加层，而是嵌入在产出物自身中的溯源记录。对于 Figma / Sketch 等设计工具来说，这种「文件即文档」的哲学提供了启发：设计产出物可以同时是审美对象和信息载体。

## 三个切口的交汇点

Custom 分支协议、DNA 三层提取、design.md 跨工具传递——这三个机制看似独立，实际共享一个设计理念：**把设计系统的约束从「写死在某个工具里」变成「可在工具之间流动的结构化知识」**。

Custom 分支确保了约束的弹 性——当 catalog 主题不够用时，规则系统允许「有约束地从零设计」，而不是要么强制用 catalog 要么完全放开。DNA 提取确保了知识的可迁移性——任何设计都可以被拆解为三层 DNA，从一个工具搬到另一个工具。design.md 确保了系统的一致性——锁定的设计系统成为项目级真理源，所有后续 Hallmark 运行 defer to it。

这三个机制加在一起，让 Hallmark 不只是一个「让 AI 生成更好看网页的 skill」，而是一个**跨 AI 工具的设计系统基础设施**。当 AI 编程助手从「单工具」走向「多工具协作」的时代，设计系统怎么跟着走——Hallmark 给了一个值得认真讨论的答案。

> **声明**：本文基于 Hallmark 仓库 README.md 和 skills/hallmark/ 目录下的 `custom-theme.md`、`study.md`、`design-md.md`、`SKILL.md` 等公开文件撰写。Custom 分支的触发机制、DNA 提取的五步协议、design.md 的格式规范均有一手源码佐证。具体的 palette 构造算法（OKLCH chroma 钳制范围、paper 微染规则）来自 `color.md` 和 `custom-theme.md` 的公开规则，实际执行效果需以 `npx skills add nutlope/hallmark` 安装后的运行为准。
