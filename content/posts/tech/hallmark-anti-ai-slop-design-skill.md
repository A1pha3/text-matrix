---
title: "Hallmark：让 AI 生成的页面不再长得像 AI 生成的"
date: 2026-08-10T03:40:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["hallmark", "ai-design", "claude-code", "anti-slop", "frontend"]
description: "Hallmark 是一个面向 Claude Code、Cursor 和 Codex 的设计技能（skill），用 21 种宏观结构、21 套主题、57 道 slop-test 检测门和预发射六轴自评，系统性地阻止 AI 生成千篇一律的 UI 页面。本文拆解它的机制分层、设计流程与多样化规则。"
github_repo: "Nutlope/hallmark"
source_key: "gh:Nutlope/hallmark"
slug: "hallmark-anti-ai-slop-design-skill"
---

## AI 生成的页面为什么一眼就能认出来

用 LLM 生成前端页面时有一个普遍现象：不管你描述什么需求，产出的页面都有一种微妙的"AI 味"——居中 hero、渐变背景、三列卡片、rounded-2xl、indigo→purple 色板。这不是某个模型的缺陷，而是所有主流 LLM 在训练数据中见过太多同类模板后的统计回归——模型倾向于输出分布最密集的那个设计。

Hallmark（[Nutlope/hallmark](https://github.com/Nutlope/hallmark)）针对的就是这个问题。它的定位不是一个 UI 生成器，而是一个**设计技能（skill）**——一组规则和检测门，挂载到 Claude Code、Cursor 或 Codex 上，在代理生成 HTML/CSS 时执行约束。README 的副标题就是它的自我介绍：一套拒绝长得像 AI 生成的设计技能。

## 机制总览：三个可分离的层，四个动词

读 Hallmark 的规则集，先把三层东西分开。它们各自独立、各自有目录，混在一起看会以为 Hallmark 只是个"主题包"：

| 层 | 数量 | 管什么 | 举例 |
|---|---|---|---|
| 宏观结构（macrostructure） | 21 种 | 页面骨架：标题位置、分栏节奏、分隔线语言、按钮口吻 | Bento Grid、Long Document、Manifesto |
| 主题（theme） | 21 套 | 视觉皮肤：字体配对、色板、布局节奏 | Hum、Cobalt、Brutal、Riso |
| slop test | 57 道 + 六轴自评 | 验收：交付前逐条检查是否踩了 AI 设计的坏习惯 | 禁渐变文字、禁 hero 全居中 |

宏观结构和主题是两套独立的选择：同一个 Long Document 骨架可以穿 Newsprint 皮肤，也可以穿 Terminal 皮肤。换主题是换皮，换宏观结构是换骨——Hallmark 的多样性主张主要建立在骨架层。

操作端只有四个动词：

| 动词 | 作用 |
|---|---|
| *(默认)* | 构建新 UI。选宏观结构、套主题、跑 slop test，通过才交付 |
| `hallmark audit <target>` | 对已有代码逐条对照反模式评分，输出问题清单，不做修改 |
| `hallmark redesign <target>` | 扔掉结构，保留文案、信息架构和品牌，用不同的设计指纹重建 |
| `hallmark study <screenshot \| URL>` | 从你欣赏的设计中提取 DNA（宏观结构、字体配对、色彩锚点），可选生成可移植的 `design.md` |

## 核心机制

### 宏观结构：先选骨架，再写代码

`references/macrostructures.md` 开头第一条规则就是"选一个宏观结构，然后才开始写代码"。每种宏观结构是一个完整的指纹——标题放哪、正文怎么排、分隔线用细线还是色块、按钮是什么口吻、图片如何处理、进场动画是什么模式——打包成一个具名选择。

21 种里挑几种感受一下尺度：

- **Bento Grid**：大小不一的模块拼成不规则网格，节奏来自尺寸变化，不是等距卡片
- **Long Document**：读起来像备忘录或日志，连续散文加行内小标题，"页面是关于产品的文学"
- **Stat-Led**：hero 就是一个巨大的数字，后面所有内容都在支撑或限定它
- **Manifesto**：檄文式大字排版，先告诉读者该相信什么，再谈卖什么
- **Letter**：第一人称书信体，以"Dear friend,"开头，首屏没有按钮
- **Specimen**：左缘编号标签 + 巨型衬线字 + 不对称栏宽，字体厂气质

有一条针对性的禁令值得单独说：Specimen 曾经是默认兜底——模型一犹豫就滑向这种"编辑感"排版。现在规则明文写了 Specimen fall-through is banned：简报没有明确的编辑/字体厂气质时不许选它。这条禁令的由来，是作者清楚这套技能的用户主要是模型——模型一犹豫，就往这种排版上滑。

选择还受多样化规则约束：代码库里已有 `/* Hallmark · macrostructure: <name> · ... */` 戳记时，本次选择必须与最近三次构建都不同；简报模糊时先从前十种里选——按仓库的说法，这十种覆盖约 80% 的简报。

### 主题：21 套，按体裁分簇轮换

21 套具名主题各有完整的字体配对、色板和视觉语言：Specimen、Atelier、Brutal、Newsprint、Studio、Manifesto、Terminal、Midnight、Almanac、Garden、Riso、Sport、Bloom、Coral、Cobalt、Aurora、Editorial、Carnival、Lumen、Hum、Grid。

但 Hallmark 不让模型每次都面对全部 21 个选项。它先把简报归入四种体裁之一——atmospheric（氛围）、editorial（编辑）、modern-minimal（现代极简）、playful（俏皮）——每种体裁有自己的主题簇：

- atmospheric 在 Bloom / Midnight / Terminal / Aurora / Lumen 里轮换
- modern-minimal 在 Coral / Cobalt 里轮换
- playful 固定用 Hum
- editorial 走剩下的 13 套

簇内轮换还要对上一次构建在至少一个轴上不同——展示风格或强调色相。这样设计的原因写在规则里：每次都让用户选主题是摩擦，不是纪律。体裁归对了，主题自然落在一个小集合里。

### Custom：没有主题匹配时

当简报携带的创意意图没有任何目录主题能接住，Hallmark 切到 **Custom** 模式，分两档：调校（tuned）——为这个简报定制一套 OKLCH 色板加免费字体配对，仍搭在 Hallmark 的宏观结构上；完全定制（bespoke）——当简报的结构本身就是需求时，从第一性原理设计整页。无论哪档，57 道 slop test 一道不少。

这是一个安静的分支：普通简报永远不会触发它。协议在 [`references/custom-theme.md`](https://github.com/Nutlope/hallmark/blob/main/skills/hallmark/references/custom-theme.md)。

### 设计流程：从简报到交付的八步

SKILL.md 的默认流程有编号的八步（0 到 7），比"选结构、套主题、跑检测"的概括细得多：

**第 0 步，Pre-flight scan**。项目里已有代码时，先读再问。按顺序扫六个信号源：项目根目录的 `design.md`（若有，它是锁定的设计系统，优先级压过一切）、字体栈（`package.json` 里的 `next/font`、`@fontsource/*`，或 HTML 里的 Google Fonts 链接）、色板（`:root` 里的 OKLCH/HSL/hex 变量、`tailwind.config` 的 colors）、微交互动画立场（装了 framer-motion、gsap 这类动画库，就是 motion-on 项目）、间距标尺、框架。扫描结果以带文件行号的清单输出，明说"将保留什么、将引入什么"。仓库原话讲得很直白：践踏既有的色板或字体栈，是"用户留下这个技能"和"卸载它"之间的区别。

**第 1 步，Design-context gate**。向用户确认简报的关键信息。

**第 2 步，先选宏观结构**。写任何 CSS 之前，骨架先行。

**第 2.5 步，查项目记忆**。读 `.hallmark/log.json`——每次构建都会记录日期、宏观结构、主题、增强模式和简报。用最近 3-5 条约束本次选择：宏观结构不得与最近三次重复，主题与上次至少差一个轴，hero 增强原型不与上次相同。选之前还要用一行明文说出轮换判断，例如"最近 5 次：Bento Grid ×2、Long Document、Manifesto、Quote-Led——这次从 {Marquee Hero, Stat-Led, Workbench, Letter} 里选 Marquee Hero"。这个"说出来"的动作是规则里写明的问责线：在页面上选，而不是在脑子里选，技能才不会漂回 Bento-Grid-by-default。

**第 2.6 步，主题路由**。studied-DNA（study 动词提取的）、目录簇、Custom 三选一，按上面的体裁簇走。

**第 3 步，加载视觉规则集**。排版、色彩、间距、微交互的各 reference 文件按需读取。

**第 4 步，决定 hero 增强**。hero 类宏观结构（Marquee Hero、Stat-Led、Quote-Led、Letter、Photographic 等）可以在基础形态上叠一个增强原型（E1–E8，如 clipped-edge 切角、hand-built SVG 手绘图形）加一个修饰模式（HP1–HP4）。增强和修饰各最多一个。

**第 5-6 步，预览与构建**。先出一个预览块，再动手写。产物是自包含的 HTML + CSS，CSS 顶部盖戳记：宏观结构、主题、增强、六轴自评分。nav 和 footer 原型（N1a–N13 / Ft1–Ft8）也要与项目内历史构建不同——仓库称这是实践中被违反最多的一条规则。

**第 7 步，slop test**。交付前的最后一道门，下一节展开。

### slop test：57 道检测门 + 六轴自评

这是 Hallmark 的核心防线。交付前逐条过 57 道，每条的期望答案都是"否"。几个例子可以感受它的具体程度：

- 展示字体是 Inter、Roboto、Open Sans、Poppins、Lato 或系统默认字体（门 1）
- 任何紫→蓝渐变，包括 `background-clip: text` 的渐变标题；任何体裁都不允许渐变文字（门 2）
- hero `min-height: 100vh` 且 eyebrow、标题、导语、CTA 全部居中——自动不合格，最多保留两个居中元素（门 6）
- 纯 `#000` 或纯 `#fff` 作底色，modern-minimal 体裁例外（门 7）
- 页面结构与项目内上一次 Hallmark 构建相同（门 8）
- 用 `transition: all` 而不指明属性（门 10）；focus ring 淡入出现（门 15，键盘用户需要即时指示）；hover 提示延迟与 focus 不等（门 17，hover 延迟 800–1000 毫秒，focus 必须为 0）；自动轮播缺少悬停暂停（门 18，WCAG 2.2.2）
- 占位名写 "Jane Doe / John Smith"，或公司名用 Acme、Nexus、Seamless、Unleash 这类创业陈词滥调（门 19）
- CSS 顶部缺宏观结构戳记（门 20）

移动端是硬性底线：产出必须在 320 / 375 / 414 / 768 四个宽度下验证，禁横向滚动、禁两行可点击文字、图片网格轨道必须用 `minmax(0, 1fr)`。

检测门之前还有一道**预发射自评**（pre-emit self-critique）：在跑门之前，先按六个轴给计划产出的页面打 1–5 分——Philosophy（这页有没有立场）、Hierarchy（读者两秒内能否分清主次）、Execution（细节是否在规格内）、Specificity（它看起来像"这个简报"还是"任何人的一页"）、Restraint（没有不挣自己位置的东西了吗）、Variety（与项目内上次产出结构距离够不够）。任何一轴低于 3 分，先改再来。六轴分数写进 CSS 顶部戳记，如 `/* Hallmark · pre-emit critique: P5 H4 E5 S4 R5 V5 */`，后续构建可以查到并避开同样的弱点。

规则集里还有一条容易被忽略但立场很硬的纪律：honest copy。用户没提供的数字不许编——"+47% conversion"、"trusted by 50,000+ teams"、"10× faster"，一旦是编的，立刻就是 slop。同样的规矩管着见证语、客户 logo 和案例数量。对一个以"去 AI 味"为目标的技能来说，这条把问题从视觉层拉回了事实层：编造的社会证明本身就是最重的 AI 味。

## 一次构建的完整流转

把机制串起来。假设简报是"给一家酸面包烘焙工作室做落地页"：

第 0 步扫项目：没有 `design.md`，`package.json` 里没有字体依赖，也没有动画库——白纸项目，motion-cut。第 1 步的确认门：简报该交代的都交代了，直接放行。第 2 步选宏观结构：烘焙工作室的简报带手工感和俏皮劲，不选 Bento Grid，选 Marquee Hero——首屏一张大图就是整页，下方接菜单。第 2.5 步：没有 `log.json`，首次构建，无轮换约束，但本次会创建这个文件。第 2.6 步体裁路由：俏皮感简报归入 playful，主题固定走 Hum 这一套。第 4 步：hero 加一个 hand-built SVG 增强原型。第 5 步出预览，第 6 步构建、盖戳记、写 `log.json`。第 7 步：跑六轴自评，P5 H4 E5 S4 R5 V5，再过 57 道门——渐变？没有。全居中？eyebrow 偏轴。假数字？菜单价格都是用户给的。通过，交付。

同一个项目里下一次构建，`log.json` 会拦住所有与这次相同的选择。仓库演示页上的 12 个示例——酸面包 app、提取 API、唱片厂牌、AI 推理工具、茶单、蜂蜜农场、丝网印刷展、字体工作室、SaaS、旅行预订、摩洛哥时尚品牌、开发者基础设施——就是这么各长各的样子。

`study` 动词是另一个入口。给它一张截图或 URL，它提取的是结构 DNA 而不是像素：宏观结构、原型、字体配对、色彩锚点，先出一份诊断报告，指认"你看到的是什么结构、哪些反模式不该跟着抄"，再问是否用这套 DNA 重建你的内容。它有明确的拒绝清单——ThemeForest、Framer/Webflow 模板、Gumroad UI kit、Dribbble shots、Behance 展示厅这些付费模板来源一律拒收，像素克隆不是功能。URL 模式还能读到确切的字体名和色值；盲点也写在文档里：HTML 本身看不出视觉节奏，所以 URL 模式的诊断必须声明这一点。用户说 "lock the DNA" 时，它生成一份可移植的 `design.md`——此后这个项目里所有构建都服从它，多样化规则也随之反转：页面之间不再互异，而是共享同一套系统。这正是 `redesign` 动词做全站重塑时产出同一个文件的原因。

## 安装

```bash
npx skills add nutlope/hallmark
```

重新运行即可更新。或者手动复制 `SKILL.md` 和 `references/` 目录到：

- **Claude Code**：`~/.claude/skills/hallmark/`
- **Cursor**：`.cursor/rules/hallmark.mdc`（用 `SKILL.md` 正文，去掉 frontmatter）
- **Codex**：`~/.codex/skills/hallmark/`（个人）或 `.codex/skills/hallmark/`（项目级）

规则集主体在 [`skills/hallmark/SKILL.md`](https://github.com/Nutlope/hallmark/blob/main/skills/hallmark/SKILL.md)（67 KB，规则集的全部细节都在这一个文件里）和 [`references/`](https://github.com/Nutlope/hallmark/tree/main/skills/hallmark/references)（24 个参考文件和 4 个子目录：每种宏观结构、每套体裁、每个动词各有专属文件）。人类读者用的实例教程在 `docs/recipes.md`（八个完整简报）和 `docs/study-examples.md`（三个 DNA 提取实例）。

## 项目数据

| 指标 | 数值 |
|---|---|
| Stars | 28,945 |
| Forks | 1,488 |
| 主语言 | CSS |
| 许可证 | MIT |
| 制作方 | Together AI |
| 创建 / 最近推送 | 2026-04-27 / 2026-08-06 |
| 在线演示 | [usehallmark.com](https://www.usehallmark.com/) |

GitHub API 于 2026-09-21 验证。ROADMAP 上排着几个值得留意的方向：`hallmark variant`（同一简报并排出三个结构不同的版本——作者认为"AI 感"最大的来源是用户不知道第一版之外还有别的，所以接受了第一版）、品牌优先流程（从一段产品描述生成整套品牌并锁进 `design.md`）、以及把实时预览做成 MCP server，让生成和审计闭环。

## 适用边界

### 适合

- 用 AI 代理生成前端页面，苦于输出千篇一律
- 需要快速产出多种设计风格的原型，并且能在原型间保持不重样
- 想从已有设计中提取设计 DNA，锁成 `design.md` 复用到整个项目
- 团队有品牌规范但 AI 输出总不遵守——`design.md` 机制就是为这种场景准备的

### 不适合

- 后端、CLI、API 等非前端场景——Hallmark 只管视觉设计
- 需要像素级精确控制——它选结构和主题，不是手动调 CSS 的替代品
- 没有 AI 代理作为宿主——它是 skill，不是独立应用
- 复杂 Web 应用的仪表盘、管理后台——规则集主要覆盖落地页/hero 页，图表类页面在 ROADMAP 上还没有专属规则

## 判断

Hallmark 做对的事情，是把"不要这样设计"从一句模糊的建议，变成了一份 57 项、逐条可判"是/否"的验收清单，再配上一个让模型在交付前必须自评六轴的流程。它的多样性不靠随机——靠的是三层分离（骨架、皮肤、验收）加上项目记忆里的轮换约束，每次构建都被上一次构建排除掉一部分选项。Specimen 兜底禁令和 nav/footer 不重复规则尤其能说明问题：作者很清楚模型会往哪里滑，规则就修在哪里。

它的局限也实在：必须依附 AI 编程代理，本身不独立运行；规则集主要覆盖营销页和落地页，仪表盘类页面暂时只有 slop test 兜着。另一个隐含成本是规则集本身——67 KB 的 SKILL.md 加 24 个 reference 文件和 4 个子目录，每个构建都要走完八步流程，换来的是设计下限的显著抬升和速度的让渡。

ROADMAP 上 `hallmark variant` 的那句话其实是整个项目的题眼："AI 感"最大的来源，是用户不知道第一版之外还有别的，所以接受了第一版。Hallmark 现在做的一切——结构库、主题簇、检测门、自评——都是在替用户把"别的样子"造出来、筛出来。在这个方向上，它目前是最系统的尝试。
