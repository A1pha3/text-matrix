---
title: "AI Website Cloner Template 架构拆解:把'克隆任意网站'拆成 5 阶段管道 + Spec 文件 + Worktree 并行 Builder"
date: 2026-06-22T20:58:00+08:00
slug: "jcodesmore-ai-website-cloner-template-agent-skill-architecture"
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "Next.js", "Agent Skill", "架构分析"]
description: "JCodesMore/ai-website-cloner-template 是一个让 Claude Code 等 AI 编码代理一键克隆任意网站到 Next.js 16 代码库的模板仓库,核心架构是 5 阶段管道 + Spec 文件作为契约 + Git Worktree 并行 Builder,3 个月拿到 17k+ stars。"
---

# AI Website Cloner Template 架构拆解:把"克隆任意网站"拆成 5 阶段管道 + Spec 文件 + Worktree 并行 Builder

## 核心判断

`JCodesMore/ai-website-cloner-template` 是一个 **GitHub 模板仓库**(`is_template: true`),给 Claude Code / Codex / Cursor 等 AI 编码代理装上一条 `/clone-website <url>` 技能(skill),让代理能一键把任意网站反向工程成可编译运行的 Next.js 16 + React 19 + Tailwind v4 + shadcn/ui 代码库。

它真正的工程价值**不在 Claude Code 本身**,而在这套机制:

1. **5 阶段管道**(Recon → Foundation → Spec → Parallel Build → Assembly)把"克隆一个网站"这件模糊任务拆成可检查、可中断、可重入的离散步骤;
2. **Spec 文件作为契约** —— 在浏览器里抓到的所有 CSS 数值、交互状态、资产路径**全部固化进 Markdown 文件**,builder 拿到的不再是"截图+一句话描述",而是包含 `getComputedStyle()` 结果的"组件施工图";
3. **Git Worktree 并行 Builder** —— 复杂 section 拆给多个 builder,每个跑在独立 worktree 分支,主 agent 最后合并,这把"一个 agent 干所有事"变成"工地总监 + 多个施工队"。

把模板当"克隆工具"会低估它;把它当 **"AI 编码代理如何把视觉任务做对"的工程范例** 才是项目作者真正的意图。仓库 README 顶部的核心原则 9 条里,有 5 条是关于"如何拆任务"和"如何传上下文",而不是关于"如何调 API"。

## 项目速览

| 维度 | 数据 |
| --- | --- |
| 仓库 | [`JCodesMore/ai-website-cloner-template`](https://github.com/JCodesMore/ai-website-cloner-template) |
| 类型 | GitHub 模板仓库(`is_template: true`,推荐 `Use this template`) |
| 主分支 | `master`(不是 `main`) |
| Stars / Forks | 17,434 / 2,721(2026-06-22 抓取) |
| 创建 / 最近 push | 2026-03-13 / 2026-06-01 |
| 许可证 | MIT |
| Topics | `ai`、`claude-code`、`claude`、`reverse-engineering`、`skills`、`website-clone` |
| 推荐运行环境 | Node.js 24+ + Claude Code(Opus 4.7 推荐) |

## 系统地图

仓库本身**不是网站**,它是一份给 AI 编码代理读的"开工指南" + 一份预搭好的脚手架:

```
JCodesMore/ai-website-cloner-template/         (GitHub 模板仓库,只读基准)
│
├── AGENTS.md                       ← 唯一信息源(Single Source of Truth)
├── CLAUDE.md / GEMINI.md / ...     ← sync-agent-rules.sh 自动生成的平台副本
│
├── .claude/
│   └── skills/
│       └── clone-website/
│           └── SKILL.md            ← /clone-website 技能定义(30312 字节)
│
├── src/                            ← Next.js 16 App Router 脚手架
│   ├── app/
│   ├── components/
│   ├── lib/utils.ts                ← shadcn cn() 工具
│   └── ...
│
├── docs/
│   ├── research/                   ← 抽取产出物(Spec 文件、行为记录、组件清单)
│   └── design-references/          ← 截图、视觉参考
│
├── scripts/
│   ├── sync-agent-rules.sh         ← 把 AGENTS.md 同步到 13 个平台
│   └── sync-skills.mjs             ← 把 .claude/skills/.../SKILL.md 同步到所有平台
│
├── package.json                    ← next 16.2.1 / react 19.2.4 / tailwindcss v4
└── Dockerfile / docker-compose.yml ← 容器化部署(默认 3000/3001)
```

两条关键不变量:

- **`AGENTS.md` 是 single source of truth**。其他 13 个平台的文件(`.cursor/rules`、`CLAUDE.md`、`GEMINI.md`、`.amazonq/...`、`.augment/...`、`.codex/...`、`.continue/...`、`.gemini/...`、`.opencode/...`、`.windsurfrules` 等)都由 `scripts/sync-agent-rules.sh` 自动从 `AGENTS.md` 重新生成。
- **`/clone-website` 技能的 SKILL.md 也是 single source of truth**。`scripts/sync-skills.mjs` 把它同步到所有支持平台的对应位置。

这意味着改一条平台特定指令**只需要改两个文件**:`AGENTS.md` 和 `.claude/skills/clone-website/SKILL.md`。

## 5 阶段管道

`/clone-website <url1> [<url2> ...]` 技能的 SKILL.md 把"克隆一个网站"拆成 5 个明确的阶段,**Phase 1 和 2 串行**(不能并行,因为下游依赖上游),**Phase 3、4、5 内部高度并行**。

### Phase 1:Reconnaissance(侦察)

> 这一阶段全部由主 agent 通过浏览器 MCP 完成(Chrome MCP / Playwright MCP / Browserbase MCP / Puppeteer MCP 之一)。

抓 4 类原料:

| 原料 | 输出位置 | 关键工具 |
| --- | --- | --- |
| **全页截图** | `docs/design-references/` | 桌面 1440px + 移动 390px 两个断点 |
| **全局抽取** | `docs/research/BEHAVIORS.md` | 字体、颜色、favicon、OG 图、平滑滚动库(Lenis / Locomotive) |
| **交互扫描** | `docs/research/BEHAVIORS.md` | 滚动扫描、点击扫描、悬停扫描、响应式扫描(3 断点) |
| **页面拓扑** | `docs/research/PAGE_TOPOLOGY.md` | 各 section 命名 + 视觉顺序 + 交互模型 |

**强制扫描**(Mandatory Interaction Sweep)是这一阶段最值钱的部分 —— README 里把它单独列为强制项,因为"很多交互在静态截图里看不出来":

- **滚动扫描**:滚动条慢速遍历,记录哪些 header 在滚动到阈值后变样、哪些元素用 `IntersectionObserver` 进入视口动画、哪些 tab 指示器是滚动驱动而非点击驱动。
- **点击扫描**:每个 button / tab / pill / card 都要点,记录切换后的内容与动画。
- **悬停扫描**:每个可悬停元素记录 hover 的 CSS 变化(不止颜色,还包括 transition 时长 + easing)。
- **响应式扫描**:1440px / 768px / 390px 三个断点都要测,记录布局在哪个断点切换列数 / 隐藏侧栏。

这一阶段产出的 `BEHAVIORS.md` 是后面写 Spec 文件的输入,**缺一项就少一项施工依据**。

### Phase 2:Foundation(地基)

> 串行。主 agent 自己干(不委托),因为它跨多个文件。

6 步顺序操作:

1. **更新字体** — 在 `src/app/layout.tsx` 用 `next/font/google` 或 `next/font/local` 配置目标网站实际用到的字体(每个 family、weight、style 都要齐)。
2. **更新 globals.css** — 把目标站点的颜色 token、间距值、关键帧动画、工具类、平滑滚动库集成写入 `:root` 和 `.dark`。
3. **创建 TypeScript 接口** — `src/types/` 下为观察到的内容结构定义类型(菜单项、卡片、轮播项等)。
4. **抽取 SVG 图标** — 把页面里所有内联 `<svg>` 元素去重后存为 `src/components/icons.tsx`,按视觉功能命名(`SearchIcon`、`ArrowRightIcon`、`LogoIcon`)。
5. **下载全局资产** — 写 `scripts/download-assets.mjs` 把所有图片 / 视频 / 二进制下载到 `public/`,保留有意义的目录结构。
6. **验证编译** — `npm run build` 必须通过,任何错误在这一阶段就修。

### Phase 3:Component Specs(组件施工图)

> 这一阶段是整个模板**最具方法论价值**的地方。

每个 section 在动笔之前,**先写一份 Spec 文件**到 `docs/research/components/`。Spec 不是随便一段描述,而是包含 9 个固定字段的 Markdown 文档,builder 拿到它**不需要再看浏览器**:

```
docs/research/components/
  ├── 01-hero-section.md
  ├── 02-features-grid.md
  ├── 03-pricing-table.md
  └── ...
```

每份 Spec 至少包含:

1. **目标截图 + 视觉参照**(从 `docs/design-references/` 引用)
2. **完整 DOM 结构**(section 内部所有 `<img>`、`<svg>`、`<a>`、`<button>`)
3. **每个元素的 `getComputedStyle()` 数值**(色、字号、间距、边框、阴影、过渡函数)
4. **资产本地路径**(图片 / 视频 / 字体已下载到 `public/` 的对应位置)
5. **真实文案内容**(用 `element.textContent` 抓,不要 placeholder)
6. **多状态文案**(tab 切换前 / 后、hover 状态、scroll 后状态)
7. **响应式断点行为**(在 1440 / 768 / 390 三个断点的布局变化)
8. **交互模型**(click-driven / scroll-driven / hover-driven / time-driven)
9. **Transition 参数**(duration、easing、动画属性、是否用 `animation-timeline`)

**这一阶段的硬约束**(SKILL.md 里明确写为 "Guiding Principles"):

> **Small Tasks, Perfect Results**:如果一个 builder prompt 超过 ~150 行 spec,这个 section 就太复杂,**必须**再拆。

> **Real Content, Real Assets**:这是 clone,不是 mockup。唯一允许生成内容的情形是"明显是 server-generated 且 per-session 唯一"的字段。

> **Completeness Beats Speed**:如果 builder 还要"猜"一个颜色 / 字号 / padding,说明你(主 agent)的抽取没做够。

### Phase 4:Parallel Build(并行建造)

> 主 agent 把 Spec 文件内容**直接内联**到每个 builder 的 prompt 里,builder 不需要再看浏览器。

每个 builder 在 **独立 git worktree 分支**里干活,典型流程:

```bash
# 主 agent 给某个 section 派 builder
git worktree add ../worktree-hero -b feat/hero  # 独立分支
# builder 在 ../worktree-hero 里只动自己负责的文件
# builder 完成后,主 agent 把分支 merge 回主分支
git merge feat/hero
```

**复杂度预算规则**(Complexity budget rule):

- 单个 section、纯静态(只有排版 + 文字 + 1-2 个按钮)→ 1 个 builder。
- 复杂 section(3 个以上 card 变体 + 不同 hover 状态)→ **每个 card 变体 + 一个 section wrapper 各 1 个 builder**。
- 交互复杂的 section(轮播 / tab / scroll-snap)→ 拆成"交互逻辑 builder"+"视觉呈现 builder"。
- 不确定时,**默认拆更细**。

主 agent 在 `AGENTS.md` 的"MOST IMPORTANT NOTES"里写了一条强约束:

> Always have each teammate work in their own worktree branch and merge everyone's work at the end, resolving any merge conflicts smartly since you are basically serving the orchestrator role and have full context to our goals.

也就是把"工头"的角色**显式建模** —— 主 agent 既不是工人也不是甩手掌柜,而是负责合并 worktree + 解决冲突的工地总监。

### Phase 5:Assembly & QA(组装 + 验收)

3 步收尾:

1. **合并 worktree** 到主分支,解决所有 merge conflict。
2. **拼接页面** —— 把各 section 串成完整 page,把 navigation、footer 等固定元素接到对应 section。
3. **视觉对比** — 用浏览器 MCP 截图新页面,**和原图做 diff**(像素级对比 + section 级别对比)。
4. **编译验证** — `npm run build` + `npx tsc --noEmit` 必须都通过。

任何一项不过,要么回退该 section 让 builder 重做,要么主 agent 自己补。

## 关键设计取舍

### 1. 为什么 Spec 文件是 Markdown 而不是 JSON?

因为 builder 是 Claude Code 之类的 LLM agent,Markdown 天然更适合 LLM 阅读,带截图引用、代码块、表格、emoji 标记都自然。JSON 适合机器解析,不适合"让 LLM 看一遍就开干"。

### 2. 为什么不直接让一个 agent 从头到尾做?

Claude Code 在长上下文里会**漂移**:颜色变淡、间距偏差、按钮圆角不一致。Spec 文件把"决策"固化下来,b builder 只看 spec,**主 agent 的注意力集中在拆任务,不消耗在像素细节**。这也是为什么 `~150 lines` 是复杂度上限 —— 超过这个长度,L builder 的输出就开始出现"近似但不精确"的退化。

### 3. 为什么不直接传截图给 builder?

截图是 1440x900 像素的栅格数据,builder 只能"看个大概",没法知道 `padding: 24px 32px` 还是 `padding: 28px 36px`,也没法知道 hover transition 是 200ms ease-out 还是 150ms ease-in。Spec 文件把**数值化、文本化的精确信息**固化,builder 拿到的信息密度比纯截图高一个数量级。

### 4. 为什么强制 worktree 隔离?

两个原因:

- **隔离 blast radius**:某个 builder 把代码改崩了,主分支不受影响,主 agent 可以单独回滚那个 section。
- **并行加速**:多个 worktree 可以同时跑 builder,不互相阻塞。Phase 4 在多 section 场景下是 N 倍加速。

### 5. 为什么把 AGENTS.md 当 single source of truth?

模板要支持 13 个 AI 编码平台(Claude Code、Codex CLI、OpenCode、GitHub Copilot、Cursor、Windsurf、Gemini CLI、Cline、Roo Code、Continue、Amazon Q、Augment Code、Aider)。如果每个平台的指令单独维护,**改一条规则要在 13 个文件同步修改**,很快就会漏。`sync-agent-rules.sh` 把"一次定义,多处生效"做实。

### 6. "Foundation 不可并行"的硬约束背后是什么?

字体、globals.css、TypeScript 类型、SVG 图标、资产目录是**所有 section 的依赖**。任何一个 section 的 builder 启动后,如果发现 `globals.css` 没准备好,要么停工、要么用错位的默认值。两难选择都导致返工。所以 Phase 2 必须串行做完、且 `npm run build` 通过。

## 关键机制:交互模型识别

SKILL.md 把"识别交互模型"列为单独一条强制原则,因为它是**最容易判断错、最难返工**的环节:

> A section with a sticky sidebar and scrolling content panels is fundamentally different from a tabbed interface where clicking switches content. Getting this wrong means a complete rewrite, not a CSS tweak.

判定流程:

1. **先别点**。先用浏览器 MCP 慢速滚动 section,观察元素是否随滚动变化。
2. 若变化 → **scroll-driven**。抓 `IntersectionObserver`、`scroll-snap`、`position: sticky`、`animation-timeline`。
3. 若无变化 → 才点击 / 悬停测试 click-driven / hover-driven。
4. 在 Spec 文件里**显式标注**:`INTERACTION MODEL: scroll-driven with IntersectionObserver` 或 `click-to-switch with opacity transition`。

## 适用边界

仓库 README 顶部写明 **Not Intended For**(明确禁止):

- **钓鱼或仿冒**(phishing / impersonation)
- **把别人的设计伪装成自己的**(passing off someone's design as your own)
- **违反目标网站 ToS**(部分网站明确禁止 scraping 或复制)

这三条意味着:这个工具**只适用于**以下三种合法场景(README 同节明确):

- **平台迁移** — 把自有 WordPress / Webflow / Squarespace 站点迁移到 Next.js。
- **丢失源码** — 网站还活着但仓库没了 / 开发者离职 / 技术栈过时。
- **学习** — 通过还原真实代码来研究生产级网站如何实现布局、动画、响应式。

## 适用人群

| 你是 | 这个模板对你的价值 |
| --- | --- |
| **前端工程师** 有一份想迁移到现代栈的老站 | 模板 + Claude Code 是迁移工程的 5x 加速器 |
| **AI 编码代理研究者** 想找"AI 做视觉任务"的范例 | 5 阶段管道 + Spec 契约是直接可借鉴的方法论 |
| **AI 编码代理技能作者** 想给 Claude Code 写自定义 skill | `.claude/skills/clone-website/SKILL.md` 30KB 是高质量样本(30312 字节,9 大原则,5 阶段) |
| **多 AI 平台工具作者** 想让一个 skill 跨平台生效 | `sync-agent-rules.sh` + `sync-skills.mjs` 是答案 |
| **希望"一键克隆任意网站"的小白** | 技术上能用,但需要先把 13 个 AI 代理之一 + Node 24 装好,门槛不低 |

## 这篇文章不覆盖什么

- 浏览器 MCP 的具体配置(Chrome MCP / Playwright MCP 怎么连、Playwright vs Puppeteer 选哪个) —— 那是另一个工程问题。
- Claude Code 的 sub-agent / worktree 命令细节 —— 用法层面的事,模板假设你已经会。
- 单个 section builder 写代码的具体模式(React Hooks 组织、shadcn 安装细节) —— 模板脚手架已搭好,builder 直接 `npx shadcn add` 即可。
- 对原网站 ToS 的合规判断 —— 取决于具体网站,需要使用者自行评估。

## 一句话总结

这个模板的本质,是把"克隆一个网站"从"一个 agent 看着截图猜样式",改造成"工地总监派多个施工队按施工图干活",而施工图(Spec 文件)在派活之前就已经把所有可量化的视觉细节固化下来 —— 它是 **AI 编码代理在视觉任务上"做对"的工程范式**,而不是单纯的"克隆工具"。