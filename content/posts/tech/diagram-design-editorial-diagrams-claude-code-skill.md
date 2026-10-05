---
title: "diagram-design：给 Agent 的编辑级图表技能，41 种自包含 HTML/SVG"
date: 2026-08-17T03:28:00+08:00
slug: "diagram-design-editorial-diagrams-claude-code-skill"
github_repo: "cathrynlavery/diagram-design"
source_key: "gh:cathrynlavery/diagram-design"
description: "diagram-design 是一个面向 Claude Code、Codex、Copilot 等 Agent 宿主的图表技能：41 种编辑级图表类型，自包含 HTML+SVG 输出，60 秒抓取网站品牌色，还能把旧 draw.io/Mermaid 图重绘成编辑风。本文梳理其设计取舍与安装方式。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "图表", "Agent Skill", "可视化", "开源"]
---

让 AI 画一张架构图，大概率会得到一堆圆角矩形加阴影的"Mermaid 风"产物——能用，但放在正经的技术文章里一眼廉价。cathrynlavery/diagram-design（42.7k stars，2.7k forks，MIT）就是为了解决这个问题而生的 Agent 技能（skill）：41 种编辑级（editorial）图表类型，输出自包含的 HTML + SVG，无阴影、无渐变堆砌、无"Mermaid-slop"。项目创建于 2026 年 4 月，半年间类型数已扩到 41 种，支持宿主也从 Claude Code 扩到 Codex、GitHub Copilot、Factory Droid、Pi 等。

## 它解决什么问题

作者 Cathryn Lavery 是实体品牌 BestSelf.co 的创始人，同时在 [littlemight.com](https://littlemight.com) 写技术内容。她在 README 里讲了动机：每次需要配图——架构草图、流程图、优先级金字塔——问 Claude 得到的结果都和整站视觉风格格格不入，要么去 Figma 里磨 30 分钟，要么干脆放弃配图。于是她把这个能力做成了一个 Agent 技能，让 AI 直接产出符合编辑标准的图表。

README 里那条设计原则点明了品味来源："The highest-quality move is usually deletion"（最高质量的操作通常是删除）——每个节点都要挣得自己的位置，强调色只留给读者应该最先看的 1-2 个元素，目标信息密度是 4/10。

## 四个能力域

半年迭代之后，这个技能已经不止"生成好看的图"。它的功能分四个域，后面逐一展开：

| 能力域 | 做什么 | 典型入口 |
| ------ | ------ | -------- |
| 静态图表 | 41 种类型 × 3 种风格变体，自包含 HTML+SVG | 自然语言让 Agent 画 |
| 旧图重绘 | draw.io / Mermaid / Excalidraw 源文件 → 编辑风 | `/diagram-design:import-*` 命令 |
| 品牌匹配 | 抓取网站提取颜色字体，写入 style-guide | "onboard diagram-design to https://yoursite.com" |
| 导出与动效 | SVG/PNG 导出；可选的有序讲解动效 | `/diagram-design:export-diagram` |

## 41 种类型，两个增长维度

每种类型都有三种静态变体：极简浅色、极简深色、完整编辑风。输出是纯自包含 HTML + SVG——静态输出没有构建步骤、没有 JavaScript、没有外部图片依赖，浏览器双击直接打开。

版本线能看出这个项目的推进节奏：2.0 加入 Loop 飞轮（带共享内存枢纽的环形结构）；2.3 引入语义系统模式（Semantic Patterns）和可选动效；2.5.10 一次加了十种布局语法——Sankey、鱼骨图、Wardley map、看板、用户旅程、部署图、依赖图、UML 类图、故事地图、数据库 schema；此后又补了极坐标、瀑布图、热力图等，到 2.6.41 共 41 种。

2.3 的语义模式容易被误读成"又一个分类体系"，它其实是给类型数量踩的刹车。思路是把行为描述和布局分离：扇入队列、策略追踪、信任边界这类"行为"，复用最接近的现有布局类型表达，不为每种行为新增一种图。仓库的 ADR 里专门记录了这条决定（patterns never add types）。目前有 9 种路由模式，每种定义了自己的触发条件、原语、预算和反模式。要区分的是：语义维度不膨胀，布局维度仍在按路线图扩张——2.5.10 的十种新类型长的是后一个维度，两者不矛盾。

一个对使用者很实际的细节是渐进披露：Agent 启动时只知道技能名字和一句话描述，接到"画个流程图"的请求才加载 SKILL.md 和 `type-flowchart.md` 这一个类型参考。类型再怎么加，每次请求的上下文开销不变。

## 60 秒品牌匹配

这个项目最聪明的一步是 onboarding 流程。你对 Agent 说"onboard diagram-design to https://yoursite.com"，它会：

1. 抓取你的首页
2. 提取主色调和字体栈
3. 映射到语义角色：paper（背景）、ink（正文）、muted（次要）、accent（强调）、link
4. 给出 diff 提案，确认后写入 `references/style-guide.md`

之后每张图都用你的颜色。网站的背景色变成图纸底色，CTA 按钮色变成焦点强调色，正文字体变成节点标签字体。写 token 之前还会自动做 WCAG AA 对比度校验——如果你的品牌色在 9-12px 的图表字号下对比度不达标，它会提议调整值并解释原因。品牌匹配还会产出一份"保真回执"：采样 URL、颜色角色、字体族与字重、字体源 URL 及回退方案。

开箱未 onboard 时，图用默认的 jet-black + atomic-tangerine 配色，直接截图也不丢人。技能还有一个 first-run gate：新项目第一次出图时，如果 style-guide 还是默认皮肤，它会先停下来问你要不要跑 onboarding——默认外观不会悄悄混进品牌项目里。服务多个客户的话，可以把品牌存成命名 profile（`~/.diagram-design/profiles/`），在项目里放一个 `.diagram-design` 标记文件指定用哪套，多项目并行互不覆盖。

## 旧图重画：draw.io / Mermaid / Excalidraw

存量图是比新图更现实的痛点：团队里躺着几百张 draw.io 和 Mermaid 图，风格各异。这个技能的导入重绘思路是——内容不动，设计系统换掉。三种来源都支持：draw.io 的 `.drawio`/`.drawio.xml`/`.drawio.png`/`.drawio.svg`（包括编辑器里看起来像 base64 乱码的压缩 payload）、Mermaid 的 `.mmd` 文件和 Markdown 里的围栏代码块、Excalidraw 的场景文件（仅解析文本，不做渲染）。

重绘由四个拨盘控制输出：

| 拨盘 | 选项 | 控制什么 |
| ------ | ------ | -------- |
| format | html / svg / png / html+png | 交付物形态：SVG 给 Figma，PNG 给幻灯片 |
| size | 10 档（doc-inline 到 print-a3 等） | viewBox 和字号阶梯——投屏幻灯片用 16px 节点名，不是 12px |
| detail | faithful ≤24 节点 / balanced ≤12 / simplified ≤7 | 留多少源内容，按固定降级阶梯裁：装饰 → 重复 → 叶子簇 → 基础设施 |
| audience | engineer / mixed / executive | 只改措辞不改数量：`Auth Service / JWT · RS256 · :8443` → `Sign-in` |

README 给了一个真实案例：一张 12 节点的 draw.io 文件按 balanced 档重绘成博客配图——源文件里六种粉彩填充色归成一个强调色，手工拖拽的坐标变成 4px 网格对齐。每次导入以一份"fidelity ledger"（保真台账）收尾，明说了合并了什么、折叠了什么、丢了什么：比如某个未连线的便签被丢弃，请求主链路完整保留。你比谁都熟悉源文件，台账让你能一眼核对。

## "编辑级"是门禁，不是形容词

设计系统本身值得单独一提：全图一个强调色、每图 1-2 个焦点元素；三种字体——Instrument Serif 做标题和斜体标注、Geist 做节点名、Geist Mono 做端口和 URL 这类技术子标签；1px 发丝边框，无阴影，圆角不超过 10px；所有坐标、宽度和间距都能被 4 整除。作者对 4px 网格的注释是"不可妥协，正是它让图不显得 AI 生成"（it's what keeps the diagrams from feeling AI-generated）。

支撑这套品味的是一组机检门禁，都在 CI 里跑：`lint-render.py` 用无头 Chromium 按"实际画出的像素"检测裁剪——理由是 `getBoundingClientRect()` 不知道描边宽度和 `clip-path`，几何测量既漏报也误报；`verify-treemap.py` 检查矩形树图的面积占比和图内印刷的数值一致——树图的全部主张就是"面积即编码"；`verify-waterfall.py` 检查瀑布图的累计值守恒。CI 不用 golden images，浏览器网络在解析器层切断，靠 Playwright 锁版本保证像素可比。用户装完技能也能在自己生成的图上跑 `self_check.py` 自检。

编辑级（editorial）在这里不是审美口号，是一组写成了断言的规则。这也是它和无参数的"帮我画好看点"提示词之间的本质差距。

## 安装

**Claude Code**（插件市场方式）：

```text
/plugin marketplace add cathrynlavery/diagram-design
/plugin install diagram-design@diagram-design
```

装完记得在 `/plugin` → Marketplaces 里打开 auto-update（Claude Code 对第三方市场默认关闭自动更新）。

**Codex**：

```bash
codex plugin marketplace add cathrynlavery/diagram-design
codex plugin add diagram-design@diagram-design
```

**Pi**：

```bash
pi install https://github.com/cathrynlavery/diagram-design
```

另有 GitHub Copilot、Factory Droid、Kiro、OpenCode 和组织版 Claude Cowork 的安装方式，README 各有对应命令。想深度定制样式指南的，可以 clone 后用 editable install（符号链接 `skills/diagram-design/` 到 `~/.claude/skills/`），避免包更新覆盖你的定制。

## 适用边界

适合：用 Claude Code / Codex / Pi 写技术内容，需要频繁配图且对视觉品质有要求的作者；团队需要统一风格的架构图、流程图产出；手头有存量 draw.io/Mermaid 图想批量换风格。

不适合：需要交互式探索的 BI 类图表——这是编辑配图工具，不是数据分析工具（导出 PNG/SVG 也只含图本身，不含编辑卡片）；推文用的 unicode 小图、清单、前后对比这类内容，作者自己的建议是一张表格或一段话更好——画图前先问：读者从这张图学到的东西，是否多过一段写好的文字？动效方面，静态输出是默认，可选动效面向有序讲解场景，提供 reveal/step/loop 模式并尊重系统的减少动效设置。

## 小结

diagram-design 抓住了 Agent 时代一个新出现的缝隙：AI 能生成图表，但生成"好看且符合品牌"的图表需要把设计知识显式化。它把图表类型、配色语义、对比度规则、几何守恒全部固化成技能文件和 CI 门禁，让 AI 每次产出都落在编辑标准线以上。半年 42.7k stars 说明这个痛点真实存在。

如果要上手，建议的顺序是：装好插件后先跑一次 onboarding 把品牌色配进去，随手画一张架构图感受输出基线；然后把库里最碍眼的两三张 Mermaid/draw.io 旧图重绘一遍，用 fidelity ledger 核对内容有没有丢；最后有幻灯片需求时再试 export 的 PNG 导出。写作重、数据看板重的团队前者收益最大，后者这个工具本来也不接这个活。

- 仓库：https://github.com/cathrynlavery/diagram-design
- 图库预览：https://cathrynlavery.github.io/diagram-design/
