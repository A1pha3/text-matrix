---
title: "ibelick/ui-skills：把设计师与前端工程师的「UI 心法」打包成 Claude Code 可消费的 skill 包注册中心"
date: 2026-07-17T02:58:00+08:00
lastmod: 2026-07-17T02:58:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Skills", "UI", "Design Engineering", "Astro"]
description: "ibelick/ui-skills 是一个面向 Design Engineer 的 Claude Code skill 注册中心，4k+ stars，MIT 协议。它把分散在 antfu、emilkowalski、mattpocock、jakubkrehel、iart-ai 等数十位设计师/工程师的 UI 心法统一为可一键安装的 skill 包，并提供 CLI 让 agent 按 motion / accessibility / typography 维度自动路由。"
weight: 1
slug: "ibelick-ui-skills-design-engineering-skills-registry"
author: text-matrix
---

## 一句话判断

**ibelick/ui-skills 是一个面向 Design Engineer 的 Claude Code skill 注册中心**——它的本质不是”一套 UI skill”，而是”一套让 agent 找到对的那套 UI skill”的分发机制：把 antfu、emilkowalski、mattpocock、jakubkrehel、iart-ai、mengto、cloudai-x、jakubantalik、leonxlnx 等数十位设计师与前端工程师各自写出的 UI 类 skill（animation、accessibility、typography、color、interaction、frontend craft）聚合到一个 `npx ui-skills` CLI 后面，让 coding agent 按 motion / accessibility / metadata / craft 等维度自动路由到最匹配的几条 skill。4k+ stars、MIT 协议，主仓库本身只放 6 条官方 skill（baseline-ui、fixing-accessibility、fixing-metadata、fixing-motion-performance、improve-ui、ui-skills-root），其余都是通过注册表拉取的第三方 skill。

如果你正在用 Claude Code 写 UI、并且厌倦了”给 agent 一句 generic prompt 然后被回吐一段泛 AI 风的 React 组件”，那这篇文章值得读完。

---

## 系统地图

```
┌──────────────────────────────────────────────────────────────────────┐
│                       ibelick/ui-skills                                │
│                                                                          │
│  ┌─────────────────────┐    ┌────────────────────────────────────┐    │
│  │  本仓自带 6 条 skill │    │  注册表（ui-skills.com registry）  │    │
│  │  ─────────────────── │    │  ────────────────────────────────  │    │
│  │  baseline-ui         │    │  ibelick / 0xdesign / accesslint  │    │
│  │  fixing-accessibility│    │  addyosmani / antfu / arifszn     │    │
│  │  fixing-metadata     │    │  bencium / callstack / cloudai-x  │    │
│  │  fixing-motion-      │    │  cursor / Dammyjay93 / Danilaa1   │    │
│  │    performance       │    │  diffusionstudio / dimillian      │    │
│  │  improve-ui          │    │  emilkowalski / iart-ai           │    │
│  │  ui-skills-root      │    │  jakubantalik / jakubkrehel       │    │
│  └──────────┬───────────┘    │  jane-xiaoer / kitlangton         │    │
│             │               │  latent-spaces / leonxlnx         │    │
│             │               │  mattpocock / mengto / ...        │    │
│             │               └────────────────┬───────────────────┘    │
│             │                                │                         │
│             └─────────────┬──────────────────┘                         │
│                           ▼                                            │
│            ┌──────────────────────────────┐                            │
│            │   ui-skills Astro 网站       │   ← 浏览 / 搜索 / 发现    │
│            │   （registry 站点）           │                            │
│            └──────────────┬───────────────┘                            │
│                           ▼                                            │
│            ┌──────────────────────────────┐                            │
│            │   `npx ui-skills` CLI          │   ← 本地安装 + 路由      │
│            │   ──────────────────────────  │                            │
│            │   npx ui-skills start         │                            │
│            │   npx ui-skills categories    │                            │
│            │   npx ui-skills list          │                            │
│            │     --category motion        │                            │
│            │   npx ui-skills get baseline-ui                           │
│            └──────────────┬───────────────┘                            │
│                           ▼                                            │
│            ┌──────────────────────────────┐                            │
│            │   Claude Code / Cursor / ... │   ← 由 skill 文件引导     │
│            │   agent 运行时                │      行为                  │
│            └──────────────────────────────┘                            │
└──────────────────────────────────────────────────────────────────────┘
```

这张图最重要的一条路径：**注册表 → CLI → agent runtime**。仓库本身只占”入口路由 + 6 条 ibelick 自家 skill”这一小段；真正庞大的是 `ui-skills.com` 上聚合的第三方 skill 集合。这种”本仓薄 + registry 厚”的形态是它和别的 skills 项目最大的结构差异。

---

## 边界与角色划分

ibelick/ui-skills 的设计边界可以用 4 条不变项概括：

| 维度 | 不变项 | 含义 |
|------|--------|------|
| 仓库本体的角色 | 注册中心 + 6 条自营 skill | 本仓只放 routing + ibelick 自己写的 baseline 系列；registry 是真相源 |
| Skill 的来源 | 多 owner 第三方为主 | antfu / emilkowalski / mattpocock / jakubkrehel / iart-ai / mengto 等 20+ 位作者贡献 skill |
| 路由维度 | category-based | `motion` / `accessibility` / `metadata` / `craft` / `typography` / `color` 等 |
| 消费方式 | npx CLI + 网站浏览 | `start` 一键启动、`list --category X` 按类筛选、`get <slug>` 取详情 |

不变项之外，**它明确不做**的事：

- ❌ **不**自己写所有 skill。本仓只放 6 条（`baseline-ui` / `fixing-accessibility` / `fixing-metadata` / `fixing-motion-performance` / `improve-ui` / `ui-skills-root`），其余都是引用第三方仓库路径（`<owner>/<repo>`）。
- ❌ **不**做平台绑定。skill 文件是 markdown，可以被 Claude Code、Cursor、Windsurf、Cline、Aider 等任意支持 skill 协议的 agent runtime 消费。
- ❌ **不**维护一个 RAG 向量库。registry 是一个静态 + 元数据驱动的目录，不是 embedding-based 检索；分类是按作者标注的 `category` / `slug`，不是语义相似度。
- ❌ **不**做版本强制锁定。`ui-skills start` 把 skill 文件落到 `~/.claude/skills/`（或对应 runtime 的 skills 目录）后，agent 在会话期间按文件内容驱动行为；版本变化跟随上游 commit。

这 4 条”不做”恰好决定了它的设计取舍——下面拆开看。

---

## 关键机制：注册中心 + 路由是怎么工作的

### 1. 本仓 6 条 skill 不是”完整能力图”

README 表面看极短，但 `package.json`（TypeScript，Astro v5 + React 19 + Tailwind v4 + motion）以及 registry 站点 `ui-skills.com` 的 `CommandDialog` 才是真正展示能力边界的地方。本仓这 6 条 skill 的定位：

| Skill slug | 角色 |
|---|---|
| `ui-skills-root` | 路由器：告诉 agent ”用户要 UI 帮助时，按 topic / stack / intent 路由到最小必要的 UI skill 子集” |
| `baseline-ui` | 入门清理：把 UI 代码里的 spacing / hierarchy / typography / 小 layout 问题快速过一遍（README 里原文叫 ”Quickly deslop UI code”） |
| `fixing-accessibility` | 修 a11y：ARIA label、键盘导航、焦点管理、对比度、表单错误 |
| `fixing-metadata` | 修 SEO/social：title、meta description、OG、Twitter card、canonical、JSON-LD |
| `fixing-motion-performance` | 修 motion：layout thrashing、compositor、scroll-linked motion、blur 性能 |
| `improve-ui` | 审计 + 写 plan：审计现有产品面、产出实现计划（read-only，不改源码） |

**这 6 条刻意只覆盖”基础维护”**——spacing、accessibility、metadata、motion performance；它们不教 agent ”怎么设计好看”。设计美学这件事被显式外包给了 registry 里的 emilkowalski / jakubkrehel / mengto / antfu / leonxlnx 等 skill owner。

### 2. Registry 是真正的力量来源

`ui-skills` 项目官方站点的 `CommandDialog` 组件把 registry 渲染成一张可搜索的表。下面是从这条 JSON 抽取出的代表性 skill（按作者归类）：

| Owner | 代表性 skill | 类别 |
|---|---|---|
| `antfu` | vue、nuxt、pinia、pnpm、slidev、tsdown、turborepo、unocss、vite、vitepress、vitest、vueuse-functions、web-design-guidelines | 工程栈 + 设计 |
| `emilkowalski` | animation-vocabulary、apple-design、emil-design-eng、improve-animations、review-animations | motion + Apple-style 设计 |
| `iart-ai` | 60fps-animation、accessible-animation、gsap-web、lottie-animation、micro-interaction、page-transition-animation、svg-animation | 性能 + 动效栈 |
| `mattpocock` | ask-matt、codebase-design、diagnosing-bugs、domain-modeling、engineering、grill-with-docs、improve-codebase-architecture、prototype、setup-matt-pocock-skills、tdd、to-issues、to-prd、triage | 通用工程方法论 |
| `jakubkrehel` | better-colors、better-typography、better-ui、make-interfaces-feel-better、oklch-skill | 颜色 + 排版 + 微交互 |
| `mengto` | animation-on-scroll、animation-systems、beautiful-shadows、cobejs、company-logos、container-lines、design-first-ui-prompting、design-taste-frontend | 视觉系统 |
| `leonxlnx` | brutalist-skill、gpt-tasteskill、minimalist-skill、output-skill、redesign-skill、soft-skill、stitch-skill、taste-skill | 高端设计方向 |
| `anthropics` | canvas-design、frontend-design | 设计美学基线 |
| `accesslint` | audit-and-fix、contrast-checker、link-purpose、refactor、use-of-color | a11y 自动化 |
| `cloudai-x` | threejs-animation、threejs-fundamentals、threejs-geometry、threejs-interaction、threejs-lighting、threejs-loaders、threejs-materials、threejs-postprocessing、threejs-shaders、threejs-textures | Three.js 全栈 |
| `callstackincubator` | react-native-best-practices | RN 性能 |
| `cursor` | thermo-nuclear-code-quality-review | 严格代码审查 |
| `diffusionstudio` | text-to-lottie | Lottie 工作流 |
| `dimillian` | swiftui-ui-patterns | SwiftUI 模式 |
| `jane-xiaoer` | web-clone | 网站复刻方法论 |
| `kitlangton` | effect | Effect v4 TS 工作流 |
| `latent-spaces` | brag | 项目宣传视频 |
| `0xdesign` | design-lab | 交互式设计探索 |
| `addyosmani` | frontend-ui-engineering、web-quality-audit | 前端工程质量 |
| `Dammyjay93` | interface-design | 后台/SaaS 设计 |
| `Danilaa1` | compact-landing | 紧凑 landing 页面 |
| `arifszn` | slide-wright | 演示稿生成 |
| `bencium` | bencium-innovative-ux-designer | 高质量 UI 生成 |
| `Jakubantalik` | refine-live、transitions-dev | 实时精修 + 过渡模式 |

**这张表想表达一件事**：ui-skills 不试图自己写所有类别的 skill——它把”什么类别的 skill 由谁来写”这件事当作 registry 的核心数据。这跟 npm 之于 Node.js、或 Hugging Face Hub 之于模型的关系是同构的。

### 3. CLI 是注册表的本地投影

`npx ui-skills` 提供 4 个子命令：

```bash
npx ui-skills                # 默认入口（展示 help 或启动 router）
npx ui-skills start          # 把 router skill 装到本地 agent runtime
npx ui-skills categories     # 列出 registry 里的所有 category
npx ui-skills list --category motion
                            # 按 category 列出 registry 里的 skill
npx ui-skills get baseline-ui
                            # 拉取并展示某条 skill 的内容
```

**关键设计**：`start` 只安装 router skill，不预装所有 skill。当用户在 Claude Code 里问”这个按钮的 hover 动画有问题”时，`ui-skills-root` 这个 router 会先读懂”用户在做 motion 相关的事”，然后**让 agent 自己用 `npx ui-skills get <slug>` 按需拉取对应 skill**——这样既避免在上下文窗口里塞上百条 skill，又让 registry 里的第三方 skill 内容始终是最新版本。

### 4. Skill 文件结构

每条 skill 在源仓库里就是一份 markdown（典型位置 `<owner>/<repo>/SKILL.md` 或 `skills/<slug>/SKILL.md`），frontmatter 通常带：

- `name`：slug
- `description`：一段触发描述，告诉 agent ”Use when ...”
- 可选 `tags` / `category`

`ui-skills.com` 的 registry JSON 把这些元数据聚合成 `<slug> / pathSlug / label / sourceLabel / description / searchContent>` 一条记录，CLI 和网站共用。**这种”skill 是 markdown + metadata 是 JSON”的二段式**让 registry 不需要重新发明 skill 格式，只是一个聚合层。

---

## 任务流案例：让 agent 修一个有 motion 抖动的页面

把上面的零件拼起来跑一次完整 flow：

**Step 1：安装 router skill**

```bash
npx ui-skills start
```

**Step 2：用户提问**

在 Claude Code 里：

```
我页面顶部的 banner 滚动时有明显抖动，blur 看着也卡，帮我看看
```

**Step 3：内部发生了什么**

1. `ui-skills-root` router 加载，读 description（”Use when the user needs UI help and you must route by topic, stack, and intent to the smallest useful set of UI skills”）。
2. router 识别关键词 ”banner 滚动抖动 / blur 抖动” → topic = motion、性能子集。
3. router 让 agent 跑 `npx ui-skills get fixing-motion-performance`（本仓自带，命中）。
4. agent 读 `fixing-motion-performance` 的 markdown 指南，开始按里面的 audit 清单逐项排查（layout thrashing / compositor / scroll-linked motion / blur）。
5. 如果审计还需要”动画性能通论”补充知识，router 再让 agent 跑 `npx ui-skills get iart-ai/60fps-animation`（registry 第三方，按需拉取）。
6. 修复完成后，agent 输出 diff 和解释。

**Step 4：跨 skill 协作**

如果用户接着说”顺便把 hero 文字的对比度调到 WCAG AA”：

- router 识别 topic 切换为 accessibility → 加载 `fixing-accessibility`（本仓）+ `accesslint/contrast-checker`（registry）。
- 两条 skill 不冲突：一条管修代码，一条管查对比度数值。

**这是 ui-skills 的关键卖点**：在不改 agent runtime 的前提下，按用户 intent 路由到最匹配的 skill 子集，避免 context 爆炸 + 避免泛 AI 风的输出。

---

## 与同类项目的横向对照

| 维度 | ibelick/ui-skills | 单一作者 skills 仓库（如 `9arm/skills`） | Claude Code 官方 builtin skills | 设计向 prompt 集合（如 `anthropics/canvas-design`） |
|---|---|---|---|---|
| 角色 | 注册中心 + router | 单一作者汇总包 | Anthropic 官方内置 | 单条设计 skill |
| Skill 数量 | 6（自营）+ N（registry） | 数十条 | 少量官方 | 1-2 条 |
| 路由机制 | category + intent router | 无（整包装入） | 无（按场景触发） | 无 |
| 作者结构 | 多 owner + 第三方 | 单一 owner | Anthropic | Anthropic |
| 跨 runtime | Claude Code / Cursor / 等 | 通常绑定 Claude Code | Claude Code only | Claude Code |
| License | MIT | 通常 MIT | Anthropic 私有 | 同作者 |
| 更新策略 | 跟随上游 commit | 跟随本仓 commit | 跟随 Anthropic | 跟随本仓 |

这张表想表达一件事：**ibelick/ui-skills 是”npm registry 之于 Node.js”在 skills 领域的早期形态**——它不抢作者的功，而是给作者一条到达 agent 的最短路径。

---

## 适用边界

**推荐使用**：

- 在 Claude Code / Cursor / Windsurf 等 runtime 里频繁做 UI 工作、希望摆脱”prompt → 泛 AI 风格组件”的循环
- 想按 motion / a11y / typography / color / interaction 维度精细化 agent 行为
- 团队里有多个 frontend 工程师，各自维护一套私有 skill 集，希望统一聚合到一个内部 registry
- 想验证某条 antfu / emilkowalski / mattpocock 的 skill 在自己项目里效果如何（不用 clone 整个仓库）

**不推荐使用**：

- 完全不用 coding agent → skills 体系对你无意义
- 只想要”一套完整的内部 design system” → 走 Storybook / Figma Tokens / shadcn 而不是 skills
- 需要强版本锁定 / 内部分发 → ui-skills 是公开 registry，不适合私有 skill 分发场景（需要自建 fork registry）
- 用 Claude Code 但不开启 skill 协议 → router skill 无法被加载

---

## 决策建议

按使用阶段选：

1. **刚接触 Claude Code 做 UI** → `npx ui-skills start` 装 router，再用 `npx ui-skills categories` 看一遍分类，按需 `get`。
2. **主要做 React/Vue + Tailwind + Framer Motion 类项目** → 优先用 `antfu/*` + `iart-ai/*` + `mengto/*` + `ibelick/baseline-ui` 组合。
3. **主要做 Three.js / WebGL 项目** → `cloudai-x/*` 系列是当前最完整的 Three.js skill 集。
4. **主要做后端 / 算法 / 工程方法论** → `mattpocock/*` + `cursor/thermo-nuclear-code-quality-review` + `ibelick/fixing-metadata`（如果涉及 docs 站）。
5. **想自己贡献一条 skill** → 模仿 registry 里任意一条的 frontmatter 格式 + description ”Use when ..." 模式，然后给 `ui-skills.com` 提 PR 或在 README 里挂 `<owner>/<repo>` 路径。

---

## 阅读路径

按需读：

- **只想上手**：README + `npx ui-skills start` + `npx ui-skills categories`
- **想理解路由**：本仓 `skills/ui-skills-root/SKILL.md` + `ui-skills.com` 首页的 `CommandDialog` 数据
- **想理解 registry 形态**：访问 ui-skills 项目官网（见 [README 顶部链接](https://github.com/ibelick/ui-skills)）直接搜 category
- **想理解一条 skill 长什么样**：克隆任意一条 `antfu/*` 或 `iart-ai/*` 仓库，读它们的 SKILL.md
- **想理解 Astro 站点怎么搭**：`package.json`（Astro v5 + React 19 + Tailwind v4 + motion）+ `astro.config`（推测）

---

## 边界声明

本文基于 [ibelick/ui-skills](https://github.com/ibelick/ui-skills) 仓库 README（2026-07-17 抓取）、ui-skills 项目官方站点的 registry JSON 的代表性切片（站点链接见 README 顶部）、以及 GitHub API 拉取的 skills 目录列表。仓库版本为 `0.2.3`，处于活跃迭代期；registry 里的 skill owner / slug / category 列表会随时间扩张，本文列出的 owner 不保证完整。skill 内容、CLI 子命令、registry JSON 结构可能在未来版本变化；具体实现请以仓库当时版本为准。

如果你的运行时是 Claude Code 之外的客户端，请先确认该客户端支持 skill 协议（Cursor、Windsurf、Cline 已支持；Aider 等部分客户端的 skill 支持仍在演进）。
