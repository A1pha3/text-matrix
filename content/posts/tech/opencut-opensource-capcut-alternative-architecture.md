---
title: "OpenCut 深度拆解：6 万 Star 的开源 CapCut 替代品，正在用 TanStack + Elysia + Rust Core 重写一整个跨端视频编辑器"
slug: opencut-opensource-capcut-alternative-architecture
date: 2026-06-23T15:04:20+08:00
draft: false
categories: ["技术笔记"]
tags: ["视频编辑器", "CapCut", "TanStack Start", "Elysia", "Cloudflare", "开源项目", "WebAssembly", "Rust"]
description: "OpenCut 是定位为「开源 CapCut 替代品」的跨端视频编辑器，2025-06 立项一年内冲到 58,966 Star / 6,420 Fork。正在从 Web 单体重写为 TanStack Start + Elysia + Moon + Rust Core 的插件优先架构，预告 Editor API、MCP server、headless 自动化与桌面/移动端。本文从立项节奏、技术栈、rewrite 蓝图、当前可用状态四个层面拆解。"
---

## 核心判断

OpenCut 不是「又一个开源剪辑工具」，而是一份**对标 CapCut 商业版功能、开源后再补上插件和 AI 接入位**的产品级答卷。它在 2025-06-22 立项，不到一年累计 58,966 Star / 6,420 Fork（`opencut-classic` 旧版 77 Star，新版才是 6 万 Star 的本体）；License 走 MIT；语言以 TypeScript 为主、底层将要落到 Rust。当前主分支 `main` 已经清空，正在用 Moon monorepo + proto 工具链跑「TanStack Start（Web）+ Elysia on Cloudflare Workers（API）+ 待落地的 Rust core」的新骨架，而真正可用的还是 [opencut-classic](https://github.com/OpenCut-app/opencut-classic)（仓库已 archive）和 `opencut.app` 经典版。

仓库：`OpenCut-app/OpenCut`，MIT，TypeScript，2025-06-22 首发 commit，2026-06-21（两天前）还在 push 工具链改造（`replace turbo with moon`）；主作者 Maze Winther；6,200+ commits 量级在仓库里堆出来的是一个明显在「打地基」阶段的产品。

> 现场可玩：[opencut.app](https://opencut.app)（经典版）跑得动；[new.opencut.app](https://new.opencut.app) 是 rewrite 后的预览（curl 验证 HTTP/2 200，但目前只有「Hello world」首屏）。

## 系统地图：双 App + Moon + proto 工具链

仓库顶层结构非常克制——`.moon/workspace.yml` 写明只发现 `apps/*` 下的项目，明确预留 `crates/*` 入口给未来的 Rust crate。

```
OpenCut/
├── .moon/                 # Moon monorepo 配置
│   └── workspace.yml      # projects: ['apps/*']，未来加 'crates/*'
├── .prototools            # proto 锁版本：bun + moon
├── apps/
│   ├── web/               # @opencut/web — TanStack Start 前端
│   │   ├── src/
│   │   │   ├── routes/    # __root.tsx + index.tsx（TanStack Router file-based）
│   │   │   ├── components/ # shadcn/ui 风格组件库
│   │   │   ├── hooks/
│   │   │   ├── lib/
│   │   │   └── router.tsx
│   │   ├── wrangler.jsonc # Cloudflare Pages 部署
│   │   └── vite.config.ts
│   └── api/               # @opencut/api — Elysia on Cloudflare Workers
│       ├── src/
│       ├── wrangler.jsonc
│       └── package.json   # 唯一依赖：elysia
├── LICENSE                # MIT
├── README.md              # 明确说「OpenCut is being rewritten」
├── bunfig.toml
└── moon.yml
```

两个 app 各自管自己的 `package.json` 和 `wrangler.jsonc`——根目录**没有** `package.json`，README 里的 `bun install` 必须在 `apps/web` 或 `apps/api` 里跑。Moon 接管 tasks，proto 锁死 bun 和 moon 的版本，避免「我本地能跑你那边挂了」的工具链漂移。

### Web：TanStack Start + React 19 + Tailwind 4

`apps/web/package.json` 的依赖列表直接就是 2026 年 H1 的「现代全栈 React 应用旗舰组合」：

| 关键依赖 | 版本 | 角色 |
|---|---|---|
| `react` / `react-dom` | `^19.2.0` | React 19（Compiler 默认开启，Hooks 形态稳定） |
| `@tanstack/react-start` | `latest` | TanStack Start：基于 Vinxi/Nitro 的 SSR/SSG 框架 |
| `@tanstack/react-router` | `latest` | File-based 路由（`apps/web/src/routes/`） |
| `@tanstack/react-router-ssr-query` | `latest` | 路由级别的 SSR + Query 集成 |
| `@base-ui/react` / `radix-ui` | `^1.4.x` | 无样式 Headless 组件库（Base UI + Radix 双备） |
| `tailwindcss` | `^4.1.18` | Tailwind 4（CSS-first 配置，Vite 插件） |
| `@cloudflare/vite-plugin` | `^1.26.0` | Cloudflare Pages 一键部署 |
| `vite` | `^8.0.0` | Vite 8 |
| `wrangler` | `^4.70.0` | Cloudflare 部署 CLI |
| `zod` / `react-hook-form` | `^4.x` / `^7.x` | 表单 + 校验 |
| `shadcn` | `^4.7.0` | shadcn CLI（v4 是项目级 generator） |
| `recharts` / `embla-carousel-react` / `vaul` | 3.x / 8.x / 1.x | 图表 / 轮播 / Drawer |
| `vitest` | `^4.1.5` | 测试 |

UI 组件风格走 shadcn/ui 路线（`components.json` + `cn` 工具函数 + `class-variance-authority` + `tailwind-merge`），但**底层 primitive 同时引入 Base UI 和 Radix**——这在 shadcn 体系里比较罕见，暗示 rewrite 阶段还在权衡哪个 headless 库做长期依赖。TypeScript 6.0、React 19、TanStack Start latest、Vite 8——这是一个**敢用 latest tag 跑 CI**的团队。

### API：Elysia on Cloudflare Workers

`apps/api/package.json` 只有 3 个字段（不算 scripts）：

```json
{
  "name": "@opencut/api",
  "scripts": {
    "dev": "wrangler dev",
    "deploy": "wrangler deploy",
    "build": "wrangler deploy --dry-run"
  },
  "dependencies": { "elysia": "latest" },
  "devDependencies": {
    "@cloudflare/workers-types": "latest",
    "wrangler": "latest"
  }
}
```

Elysia 是 Bun-first 的 TypeScript Web 框架（设计类似 Hono/Express 但类型系统更严），编译到 Cloudflare Workers 跑。`wrangler dev` 启动本地 Workers 模拟器，`wrangler deploy` 直接发布到 Cloudflare——后端是**纯 Edge**，没有传统 Node 服务器。

整个 backend 唯一 runtime 依赖是 `elysia`——典型的「一框架扛所有路由 + middleware」的风格。

### 工具链：proto + Moon + bun

README 第一句就要求装 proto：

```sh
bash <(curl -fsSL https://moonrepo.dev/install/proto.sh)
proto use       # 按 .prototools 装 bun + moon
bun install
moon run web:dev  # localhost:5173
moon run api:dev  # localhost:8787
```

- **proto**（来自 moonrepo）锁住工具版本：`.prototools` 文件里钉死 bun 和 moon 的版本，多人协作时不会出现「我升了 bun 6.3，CI 跑挂」的问题。
- **Moon**：代替了之前的 Turbo（commit `chore(tooling): replace turbo with moon`），用来管 monorepo tasks 和依赖图。
- **bun**：runtime + package manager + script runner 三合一。

提交历史显示工具链迁移在 6-21 一次完成：

```
2026-06-21  chore(tooling): remove root package.json, let moon manage per-project
2026-06-21  chore(tooling): replace turbo with moon, add proto toolchain
2026-06-21  feat(api): add elysia server for cloudflare workers
2026-06-21  Merge branch 'rewrite'
```

`ci: update workflow for rewrite` 紧跟其后——CI 同步切到新结构。

## Rewrite 蓝图：五件「Coming Soon」

README 里有一节 Status 明确列出「正在重写」的五件事，这是 OpenCut 接下来 6-12 个月的产品路线图（**仓库自述**）：

1. **Editor API**——把视频编辑能力抽象成可编程 API，让脚本、自动化、第三方插件能直接操作时间轴
2. **First-class 第三方插件**（plugin-first 架构）—— 显式把插件从「hack 进去」变成「一等公民」
3. **Desktop / Mobile / Browser 三端一份代码（Rust core）**—— `.moon/workspace.yml` 预留 `crates/*` 入口就是为这一刻准备
4. **MCP server（for AI agents）**—— 让 Claude Code、Cursor、Cline 这类 agent 通过 MCP 直接调用 OpenCut 的编辑能力
5. **Headless mode（自动化 / 批量渲染）**—— 不开 UI 也能跑渲染管线

> 视野锚点：把 1 + 2 + 4 三件放一起看，OpenCut 的目标不只是一个剪辑工具，而是要成为「**视频编辑的 Linux 内核**」——Rust core 提供受控的、可编程的、可被 AI 调用的底层能力，UI 是众多壳之一。这与 Palmier Pro（MCP 反转的视频编辑器，Swift 6.2 / macOS 26 单端）走的是**完全不同的路径**——Palmier Pro 把 AI 拽进编辑器，OpenCut 把编辑器拽进 AI 生态。

`crates/*` 还没有任何文件，Rust core 还**没有动手**——所以路线图目前停留在「架构宣誓」阶段，落地代码得等。

## 当前阶段：能用什么 / 不能用什么

| 入口 | 状态 | 说明 |
|---|---|---|
| [opencut.app](https://opencut.app) | ✅ 可用 | **经典版**（Remotion + Next.js 时代）实跑 |
| [opencut-classic](https://github.com/OpenCut-app/opencut-classic) | 📦 Archived | 经典版仓库，77 Star，2026-05-17 最后 push，README 建议「今天要用就拿这个」 |
| [new.opencut.app](https://new.opencut.app) | 🟡 预览中 | rewrite 后的部署，目前只有「Hello world」首屏（commit `feat: add hello world to home page`，2026-05-27） |
| `OpenCut-app/OpenCut` main 分支 | 🔧 重构中 | 跑起来只能看到空壳首页，Editor 还没接进来 |
| Rust core / 桌面端 / 移动端 | ❌ 未开始 | `.moon/workspace.yml` 留了 `crates/*` 入口，但无任何文件 |
| MCP server / Plugin SDK | ❌ 未开始 | 只在 README 路线图里承诺 |
| 第三方贡献 | ⏸ 暂不接收 | README 明确：「We're not set up to take outside contributions yet」 |

**实操建议**：今天想真正用 OpenCut 剪片，就 clone `opencut-classic` 跑经典版；想跟 rewrite 进度、提 PR 或搭插件架构，等 README 把「not set up to take contributions」撤掉再说。

## 商业锚点：Sponsors 已经就位

README 的 Sponsors 一节放的是 **fal.ai**——「Generative image, video, and audio models all in one place」。这透露出 OpenCut 团队在「视频编辑 + 生成式 AI」这条线上的合作意图：编辑是 OpenCut 做，**生成素材**走 fal.ai 的 API（视频模型如 Kling、可灵、Veo、Runway Gen-4 这类）。换句话说，OpenCut 不打算自己训模型，而是把「编辑层」做到极致，「生成层」靠生态合作。

> 这种定位对个人创作者意义重大：开源剪辑工具少有能撑到「6 万 Star + 拿到 fal.ai 这种级别赞助」的——它意味着 OpenCut 有动力把**第三方生成模型**接进时间轴，而不是搞自己的闭源模型。

## 适合谁 / 不适合谁

**适合**

- 想跟一个「产品级开源剪辑项目」的 rewrite 进度，准备未来做插件或提 PR 的前端/全栈工程师
- 已经在用 CapCut、剪映、Premiere Rush 这类「轻量剪辑」工具，想找个**无水印 / 无云锁定**的开源替代品的创作者（用 classic 版即可）
- 关注 **MCP for AI agent 编辑**的实验者——OpenCut 是少数明确把 MCP 写进路线图的开源视频编辑器
- 想学「TanStack Start + Elysia + Cloudflare Pages/Workers + Moon monorepo」这套 2026 年现代 TS 全栈模板的开发者（rewrite 阶段的代码正好是从空到全的最佳参照）

**不适合**

- 想要「**今天**就用上**完整**开源视频编辑器」的人——classic 版能用但功能浅，new 版跑不起来任何剪辑
- 需要 Pro 级调色、多机位剪辑、复杂音频混音的工作流——OpenCut 不是 DaVinci Resolve / Kdenlive 的对手
- 移动端党——移动端在路线图里，但 `crates/*` 还是空目录
- 想立刻拿 PR 进来的贡献者——目前**不接受外部贡献**

## 一段决策建议

如果你在「找一个**长期有戏**的开源视频编辑器跟下去」，OpenCut 是 2026 年值得放进观察列表的少数项目之一——6 万 Star + fal.ai 赞助 + 明确把 MCP 和插件写进路线图，这些信号比「README 写得多好」更实在。但**今天就想剪片**就两件事：

1. 跑 `opencut-classic`（或者打开 [opencut.app](https://opencut.app)），先把基础剪辑流程验证一遍
2. clone `OpenCut-app/OpenCut`，按 README 装 proto → proto use → moon run web:dev，跑通**空壳首页**就算吃透了 rewrite 阶段的工程结构

至于 Rust core、Desktop/Mobile、Plugin SDK、MCP server——按团队的 push 节奏（Maze Winther 一个人两个月内把工具链 + 部署一次性切完），到 Q3 末应该能看到第一批能跑的东西。但在那之前，**不必在路线图上多花预期**。

## 关键事实速查

- **仓库**：[OpenCut-app/OpenCut](https://github.com/OpenCut-app/OpenCut)
- **经典版**：[OpenCut-app/opencut-classic](https://github.com/OpenCut-app/opencut-classic)（archived）
- **在线体验**：[opencut.app](https://opencut.app)（经典版） / [new.opencut.app](https://new.opencut.app)（rewrite 预览）
- **License**：MIT
- **首 commit**：2025-06-22
- **最新 push**：2026-06-21（2 天前，工具链迁移）
- **Star / Fork**：58,966 / 6,420（截至 2026-06-23）
- **主语言**：TypeScript（计划加 Rust）
- **前端栈**：TanStack Start + React 19 + Tailwind 4 + Vite 8
- **后端栈**：Elysia on Cloudflare Workers
- **Monorepo**：Moon（替代 Turbo）+ proto 工具链 + bun
- **赞助方**：fal.ai
- **作者**：Maze Winther（主导）
- **Open issues**：328（多数是重写期间的 roadmap / 讨论帖）
