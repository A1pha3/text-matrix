---
title: "HTML 的不讲道理：AI 时代文档的新范式"
date: "2026-05-09T17:30:37+08:00"
slug: "unreasonable-effectiveness-of-html"
description: "深入解析 thariq 的 HTML effectiveness 项目：20 个自包含 HTML 文件如何替代 Markdown 完成代码审查、动画调参、设计系统、交互原型等 Markdown 难以胜任的工作。探讨 AI 生成富媒体文档的设计哲学。"
draft: false
categories: ["技术笔记"]
tags: ["HTML", "AI编码助手", "ClaudeCode", "文档设计", "交互原型"]
---
# HTML 的不讲道理：AI 时代文档的新范式

> **目标读者**：使用 AI 编码助手（Coding Agent）的开发者、AI 应用架构师、文档工程师
> **前置知识**：用过 Claude Code / Copilot 等 AI 编码工具，了解 Markdown 文档的局限性
> **核心问题**：当 AI 可以直接生成可交互的 HTML 而非静态 Markdown 时，我们能用 HTML 做什么 Markdown 做不了的事？

---

## 1. 从"写 Markdown"到"生成 HTML"

如果你用 AI 编码助手写过代码，大概有过这个经历：让 AI 写一份技术文档，它噼里啪啦吐出一篇很长的 Markdown，格式工整、条理清晰——然后你打开一看，发现：

- 代码块里没有语法高亮，但勉强能看
- 图表只能用 ASCII art 或外链图片凑合
- 表格稍微复杂一点就乱成一团
- 想在手机上看？排版完全崩了

这就是 Markdown 的天花板。Markdown 生来是为"写网页"设计的，但它真正的输出格式只是纯文本加一些符号装饰。**Markdown 能描述结构，但不能定义体验**。

而 AI 编码助手（Claude Code、opencode、Pi 等）本质上是一个能读写文件的智能体。当你可以让它生成一个 `.html` 文件，而不是 `.md` 文件时，可能性就打开了——因为 HTML 是**真正的 UI 媒介**，不是文字的替身。

thariq 的这个项目就是这样一种实验的集结：**20 个自包含的 `.html` 文件，每个都是 AI 替代"一篇文档"的答案**。

---

## 2. 为什么 HTML 能做到 Markdown 做不到的事

### 2.1 空间信息：Markdown 扁平，HTML 立体

代码审查（Code Review）是最典型的例子。当 AI 给你一段 diff，Markdown 的做法是把增减行用符号标出来：

```markdown
- old line
+ new line
```

扁平。死板。视觉信息全部丢失。

看看 `03-code-review-pr.html` 里的 PR 审查页面是怎么做的：

- 左侧是完整的 diff 渲染，有语法高亮
- 右侧边栏标注着每个文件的**风险等级**（safe / needs attention）
- 每个文件还有**跳转链接**，点击直达需要重点看的部分
- 文件列表配有变更行数统计（`+142 / −38`）

diff 本质上是**空间信息**——变更在哪里、关联多少行、周围是什么上下文。这些信息在 Markdown 里要么丢失，要么被压成一维的文本流。HTML 让这些空间关系直接可视化。

### 2.2 交互性：动画和交互是"感受"出来的，不是"描述"出来的

原型设计（Prototyping）是第二个关键场景。

`07-prototype-animation.html` 是一个过渡动画的沙盒：把一个动画的所有参数（duration、easing curve）做成滑块，你直接拖动调节，实时预览效果。

```html
<!-- 核心交互：实时调节 CSS 参数 -->
<input type="range" id="duration" min="0.1" max="2" step="0.1" value="0.3">
<input type="range" id="easing" min="0" max="1" step="0.01" value="0.5">
```

你没法用 Markdown 描述这件事——"请感受一下 300ms ease-out 和 500ms ease-in-out 的区别"。但一个滑块 + 实时预览，五秒钟就能感受到。这是**物理直觉**，不是文字理解。

`08-prototype-interaction.html` 更进一步：四个真实可点击的屏幕页面串联在一起，形成一个可交互的流程图。你不需要打开 Figma，原型就在浏览器里。

### 2.3 真实媒介：SVG 是真正的矢量绘图工具

`10-svg-illustrations.html` 展示了为什么 HTML 的 `<svg>` 比 Markdown 图片链接强一百倍。

每张 SVG 图是**内联的**——你可以直接复制其中一段，粘贴到 Figma、Sketch 或代码里。每一根线条、每一个节点都可以手动微调。AI 不再只是输出一个"图片链接"，而是给了一个**可编辑的矢量资产**。

更重要的是，这些 SVG 是和上下文一起生成的——比如"为后台任务文档画三个 header 插图"。AI 知道这套图的风格、色板、用途，它不是一个孤立的资源，而是一套系统内的视觉语言。

### 2.4 可导航的信息架构

长文档（Research、Reports）是 Markdown 的舒适区，但 HTML 可以做得更好。

`14-research-feature-explainer.html` 是一个关于 Rate Limiting（限流）的技术解释页面。Markdown 版本的 FAQ 可能长这样：

```markdown
## FAQ

**Q: 超出限制怎么办？**  
A: 返回 429 状态码。

**Q: 恢复窗口是多久？**  
A: 60 秒后重置。
```

HTML 版本怎么做？每个 FAQ 条目是一个**可折叠的 section**，点击展开，关闭收起。但更重要的是：页面顶部有 TL;DR 摘要框、请求路径的分步骤图（每步都有标注和跳转链接）、配置示例的 tab 切换——这些元素让一篇技术文档变成了一个**可操作的工具**，而不是一个需要阅读理解的文本。

`15-research-concept-explainer.html` 是最直观的一个例子：**Consistent Hashing（一致性哈希）的交互式讲解**。

核心是一个实时可操作的环形图：
- 4 个节点分布在环上
- 可以增加节点或删除节点
- 每次操作后，环形图实时更新，显示哪些 key 发生了迁移
- 彩色弧段显示每个节点的所有权范围

用 Markdown 写"一致性哈希"能写到天荒地老，但这个交互式演示五分钟就能让人理解 K/N 的核心洞察。这就是**媒介的力量**。

---

## 3. 20 个用例的场景分类

这 20 个 HTML 文件不是随机生成的。它们被组织成 8 个场景类别，每个类别都指向一类 Markdown 写不好的工作：

| 类别 | 文件数 | Markdown 的痛点 | HTML 的解法 |
|------|--------|----------------|-------------|
| **Exploration & Planning**（探索与计划） | 3 | 多个方案并列难以对比 | 并排展示，可视化选择 |
| **Code Review**（代码审查） | 3 | Diff 扁平，缺少上下文 | Annotated diff，风险标注 |
| **Design**（设计） | 2 | 设计稿只能截图或链接 | Tokens 成为可复制 swatches |
| **Prototyping**（原型） | 2 | 动画和交互无法描述 | 滑块调节，实时预览 |
| **Diagrams**（图表） | 2 | 图表是静态图片，无法编辑 | Inline SVG，可复制可微调 |
| **Decks**（演示） | 1 | 需要 Keynote/PowerPoint | 纯 HTML 幻灯片，键盘导航 |
| **Research & Learning**（研究与学习） | 2 | 长文导航困难 | 可折叠章节，Tab 切换 |
| **Reports**（报告） | 2 | 周报/月报格式单调 | 时间轴、小图表、彩色状态 |
| **Custom Editors**（自定义编辑器） | 3 | 调试日志需另开工具 | 嵌入式 Triage Board、Feature Flag 面板 |

Custom Editors 特别有意思——`18-editor-triage-board.html` 是一个任务分诊面板，`19-editor-feature-flags.html` 是 Feature Flag 管理界面，`20-editor-prompt-tuner.html` 是一个 Prompt 调参工具。**AI 生成的不是文档，而是一个可以工作的工具**。这已经超出了"文档"的范围，进入了"直接产出生产力"的领域。

---

## 4. 为什么 AI 生成 HTML 的质量能超出预期

看这些例子的时候，你可能会想：AI 不是经常写出乱七八糟的 HTML 吗？CSS 命名混乱、布局一塌糊涂、样式互相覆盖——为什么这些例子看起来像是有设计师参与过的？

thariq 在项目说明里给出了一个关键线索：**"Twenty self-contained .html files an agent produced instead of a wall of markdown"**——AI 生成的是文件，不是文本片段。当 AI 生成一个完整的 `.html` 文件时，它需要考虑：

1. **内联 CSS**：文件是自包含的，所以样式必须和结构一起设计，没有外部 stylesheet 可以依赖，这让 AI 必须从头规划整个视觉系统
2. **真实交互**：滑块、表单、折叠面板需要实际的 JS 逻辑，AI 不能写"点击展开（此处为示意）"这种占位符
3. **可运行的约束**：生成的 HTML 必须能在浏览器里直接打开并正常工作，这意味着 AI 的输出质量有了一个硬性的验证标准——跑不起来就是跑不起来

Markdown 的问题是：它可以被生成得很流畅，但验证成本几乎为零。AI 可以吐出一篇格式工整但实际运行会出问题的代码，只要在 Markdown 里看起来合理就行。**HTML 逼着 AI 对自己的输出负责**。

---

## 5. 文档的渐进式披露（Progressive Disclosure）

这 20 个 HTML 文件的另一个共同设计哲学是**渐进式披露（Progressive Disclosure）**——不要在一开始就展示所有信息，只在用户需要时提供。

传统的 Markdown 文档像一个无限滚动的线性文本：开头写 TL;DR，然后背景、然后原理、然后 API 参考、然后 FAQ——不管你处于什么阶段，所有内容都摊在眼前。

HTML 的方案是什么？以 `14-research-feature-explainer.html` 为例：

- **顶部**：TL;DR 摘要框，一句话说明 Rate Limiting 的核心机制
- **中层**：可折叠的请求路径步骤，每步展开可以看到具体的代码路径和耗时
- **底部**：Tab 切换的配置示例，FAQ 可折叠

读者可以从 TL;DR 开始快速理解全貌，也可以深入任何一个细节，而不需要在大量文字里找线索。这是一种**主动导航的信息架构**，而非被动的线性阅读。

---

## 6. AI-Code Agent 友好（AI-Agent Friendly）

每个生成的 HTML 项目都包含 `CLAUDE.md` 和 `AGENTS.md` 文件，这是 AI 编码助手的入口文档。它们遵循 **Progressive Disclosure** 原则：简洁的项目概览放在根目录，详细文档通过链接深入——而不是把整个项目的所有细节堆在一个巨大的 README 里。

对于 AI 编码助手来说，这意味着：
- **首次接触**：AI 不需要读 10 分钟文档才能开始工作，概览直接给出关键路径
- **需要细节时**：有具体的文档链接可以跳转，AI 可以按需获取信息
- **上下文污染**：大量低频细节不会污染 AI 的上下文窗口（context window）

这种设计思路本身也值得借鉴——不只是给人类写文档要讲究渐进式披露，给 AI 写文档同样需要。

---

## 7. 这个项目的核心洞察

回过头来看，thariq 的这个实验指向了一个更根本的问题：

> **文档的目的是传递信息，而信息的载体应该匹配信息的性质。**

代码审查是空间信息 → 需要可视化 diff  
动画调参是感受型信息 → 需要实时交互  
设计系统是视觉语言 → 需要可复制的 token  
一致性哈希是过程性理解 → 需要可操作的环形图  

Markdown 是一种**通用介质**，它擅长表达文本结构，但所有类型的信息都被压缩成同一种格式。当你允许 AI 生成专门的格式（HTML、SVG、交互式组件），信息密度可以大幅提升。

这不是说 Markdown 会被淘汰——文字描述、长篇教程、API 文档仍然最适合 Markdown。但对于特定类型的工作，HTML（以及更广泛的富媒体格式）提供了 Markdown 给不了的东西。

**AI 编码助手打开了一个新的设计空间**：不再只是"让 AI 帮我写更好的 Markdown"，而是"让 AI 生成最适合这个任务的格式"。这个项目就是这个新空间的早期演示。

---

## 参考资料

- [The unreasonable effectiveness of HTML — examples](https://thariqs.github.io/html-effectiveness)
- 项目 GitHub（完整 20 个 HTML 文件可在浏览器直接打开体验）

---

**文档信息**
难度：⭐⭐⭐⭐ | 类型：技术笔记 | 更新日期：2026-05-09 | 预计阅读时间：20 分钟
