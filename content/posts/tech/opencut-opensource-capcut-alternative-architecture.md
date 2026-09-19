---
title: "OpenCut 深度拆解：近 9 万 Star 的开源 CapCut 替代品，正在用 TanStack + Elysia + Rust Core 重写跨端视频编辑器"
slug: opencut-opensource-capcut-alternative-architecture
github_repo: "OpenCut-app/opencut-classic"
source_key: "gh:OpenCut-app/opencut-classic"
date: 2026-09-18T10:00:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["视频编辑器", "Cloudflare", "开源项目", "Rust"]
description: "OpenCut 是定位为「开源 CapCut 替代品」的跨端视频编辑器，2025-06 立项一年多累计 89,302 Star / 8,819 Fork。正在从 Web 单体重写为 TanStack Start + Elysia + Rust Core（GPUI 桌面端）的插件优先架构，路线图明确 Editor API、MCP server、Headless 模式、内置脚本 Tab 与桌面/移动端。本文基于 2026-09 仓库实况，从立项节奏、技术栈、重写进展、当前可用状态四层拆解。"
---

## 核心判断

OpenCut 不是「又一个开源剪辑工具」，而是一份**对标 CapCut 商业版功能、开源后再补上插件和 AI 接入位**的产品级答卷。它 2025-06-22 立项，一年多累计 **89,302 Star / 8,819 Fork**（`opencut-classic` 旧版 251 Star，新版才是 8.9 万 Star 的本体）；License 走 MIT；语言以 TypeScript 为主、Rust 正在落地。repo 顶层已出现 `Cargo.toml` / `Cargo.lock`，workspace 当前注册了 `apps/desktop`，并预留 `crates/*` 入口 —— Rust core 不是停留在纸面，而是已经跑起来的第一个原生端。

仓库：`OpenCut-app/OpenCut`，MIT，TypeScript（`language` 报告为 TypeScript），2025-06-22 首发 commit；当前 `pushed_at` 为 2026-08-10。主作者 Maze Winther。仓库从"一人打地基"走到了"三端同源、Rust 落地"的阶段。

> 现场可玩：[opencut.app](https://opencut.app)（经典版）跑得动；[new.opencut.app](https://new.opencut.app) 是 rewrite 后的预览入口，正式切换前一直承载新版。

## 系统地图：三 App + Cargo workspace + Moon/proto 工具链

仓库顶层结构克制而清晰，`.moon/workspace.yml` 只发现 `apps/*`，并明确预留 `crates/*` 给未来的 Rust crate：

```
OpenCut/
├── .moon/                 # Moon monorepo 配置
│   └── workspace.yml      # projects: ['apps/*']，预留 'crates/*'
├── .prototools            # proto 锁版本：bun + moon + rust
├── Cargo.toml             # workspace，members: ['apps/desktop']，预留 # 'crates/*'
├── Cargo.lock             # 已提交，锁定 Rust 依赖（含 gpui 0.2.2）
├── apps/
│   ├── web/               # @opencut/web — TanStack Start 前端
│   │   ├── src/
│   │   │   ├── routes/    # __root.tsx + index.tsx + editor.tsx（TanStack Router file-based）
│   │   │   ├── components/ # shadcn/ui 风格组件库
│   │   │   ├── hooks/  ├── lib/
│   │   │   └── router.tsx / routeTree.gen.ts
│   │   ├── wrangler.jsonc # Cloudflare Pages 部署
│   │   └── vite.config.ts
│   ├── api/               # @opencut/api — Elysia on Cloudflare Workers
│   │   ├── src/  ├── wrangler.jsonc
│   │   └── package.json   # 唯一依赖：elysia
│   └── desktop/           # @opencut/desktop — GPUI + Rust 桌面端
│       ├── Cargo.toml     # gpui 0.2.2
│       ├── src/           # main.rs / shell.rs / theme.rs / components / panels
│       └── README.md      # "Very early. Right now this is just a window."
├── changelog/             # 0.1.0 / 0.2.0 / 0.3.0（Editor foundation → Motion & effects → Masks & more）
├── LICENSE                # MIT
├── README.md              # 首行声明「OpenCut is being rewritten」
├── bunfig.toml
└── moon.yml
```

三个 app 各自管理自己的 `package.json`；根目录**没有** `package.json`，README 的命令都要在 `apps/web` 或 `apps/api` 里执行。Moon 接管 monorepo tasks，proto 锁死 bun、moon、rust 的版本，Cargo.lock 已提交 —— 从 Node 工具链到 Rust 工具链，团队都用「锁版本」来避免「我本地能跑、你那边挂了」的漂移。

### Web：TanStack Start + React 19 + Tailwind 4

`apps/web/package.json` 的依赖列表直接就是 2026 年 H1 的「现代全栈 React 应用旗舰组合」：

| 关键依赖 | 版本 | 角色 |
|---|---|---|
| `react` / `react-dom` | `^19.2.0` | React 19（Compiler 默认开启，Hooks 形态稳定） |
| `@tanstack/react-start` | `latest` | TanStack Start：基于 Vinxi/Nitro 的 SSR/SSG 框架 |
| `@tanstack/react-router` | `latest` | File-based 路由（`apps/web/src/routes/`） |
| `@tanstack/react-router-ssr-query` | `latest` | 路由级 SSR + Query 集成 |
| `@base-ui/react` / `radix-ui` | `^1.4.x` | 无样式 Headless 组件库（Base UI + Radix 双备） |
| `tailwindcss` / `@tailwindcss/vite` | `^4.1.18` | Tailwind 4（CSS-first 配置，Vite 插件） |
| `@cloudflare/vite-plugin` | `^1.26.0` | Cloudflare Pages 一键部署 |
| `vite` / `wrangler` | `^8.0.0` / `^4.70.0` | Vite 8 + Cloudflare 部署 CLI |
| `zod` / `react-hook-form` | `^4.x` / `^7.x` | 表单 + 校验 |
| `shadcn` | `^4.7.0` | shadcn CLI（v4 是项目级 generator） |
| `recharts` / `embla-carousel-react` / `vaul` | 3.x / 8.x / 1.x | 图表 / 轮播 / Drawer |
| `vitest` / `@testing-library/react` | `^4.1.5` / `^16.3.0` | 测试 |
| `lucide-react` / `@hugeicons/react` | 1.x / 1.x | 图标 |

UI 组件风格走 shadcn/ui 路线（`components.json` + `cn` + `class-variance-authority` + `tailwind-merge`），但**底层 primitive 同时引入 Base UI 和 Radix** —— 这在 shadcn 体系里比较罕见，说明 rewrite 阶段还没决定哪个 headless 库做长期依赖。TypeScript 6.0、React 19、TanStack latest、Vite 8 —— 这是一个**敢用 latest tag 跑 CI**的团队。值得注意：`routes/` 下除了 `index.tsx` 已出现 `editor.tsx`，重写的编辑器入口不再是"只有 hello world"。

### API：Elysia on Cloudflare Workers

`apps/api/package.json` 干净得惊人 —— 列完了整个后端，运行时依赖只有 `elysia`：

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

Elysia 是 Bun-first 的 TypeScript Web 框架（类型系统比 Hono/Express 更严），编译到 Cloudflare Workers 跑。`wrangler dev` 启动本地 Workers 模拟器，`wrangler deploy` 直接发布到 Cloudflare —— 后端是**纯 Edge**，没有传统 Node 服务器，一个框架扛所有路由 + middleware。

### Desktop：GPUI + Rust（重写的新信号）

`apps/desktop/` 是这次取证里最有信息量的一层。它是一个 **GPUI（`gpui 0.2.2`，Zed 的渲染框架）+ Rust** 的原生桌面应用，README 第一行就自我评估 **"Very early. Right now this is just a window that opens."**—— 当前阶段只开出一个窗口，但骨架已经成形：

- `src/main.rs` / `src/shell.rs` / `src/theme.rs` / `src/components/` / `src/panels/` —— 一个桌面应用的基本壳已就位
- 平台要求跨 macOS（Metal）/ Windows（Win32 + DirectWrite）/ Linux（Vulkan + Wayland/X11）
- `moon run desktop:dev / check / build` 对应 Rust 的 `cargo run / check / build --release`

把 Web 的 `routes/editor.tsx` 和 Desktop 的 GPUI 骨架放一起看：**"跨端一份代码"已经从路线图长进了代码**，只是进度还只在"窗口能打开"的早期。

### 工具链：proto + Moon + bun（+ rust)

README 第一句仍要求装 proto：

```sh
bash <(curl -fsSL https://moonrepo.dev/install/proto.sh)
proto use       # 按 .prototools 装 bun + moon + rust
bun install
moon run web:dev      # localhost:5173
moon run api:dev      # localhost:8787
moon run desktop:dev  # 见 apps/desktop/README.md（GPUI 首次编译较久）
```

- **proto**（来自 moonrepo）锁工具版本：`.prototools` 钉死 bun、moon，现在还加上 rust，多人协作不会出现「我升了 bun 6.3，CI 跑挂」。
- **Moon**：管理 monorepo tasks 和依赖图（此前从 Turbo 迁来）。
- **bun**：runtime + package manager + script runner 三合一。
- **Cargo workspace**：`resolver = "3"`、`edition = "2024"`，`members` 当前只有 `apps/desktop`，`# 'crates/*'` 注释保留 —— Rust 代码当前全部收在 desktop 应用内，尚未抽成独立 crates。

## Rewrite 蓝图：路线图已从 5 项扩到 6 项

README 的 Status 一节至今仍声明「**OpenCut is being rewritten from the ground up.**」，紧随其后列的"正在来的东西"在 2026-06 快照后多了一项（共 6 项，**仓库自述，加粗项为新增**）：

1. **Editor API**——把视频编辑能力抽象成可编程 API，让脚本、自动化、第三方插件能直接操作时间轴
2. **First-class 第三方插件**（plugin-first 架构）—— 显式把插件从「hack 进去」变成「一等公民」
3. **Desktop / Mobile / Browser 三端一份代码（Rust core）**—— `.moon/workspace.yml` 与 Cargo workspace 预留的入口，正是为此准备
4. **MCP server（for AI agents）**—— 让 Claude Code、Cursor、Cline 这类 agent 通过 MCP 直接调用 OpenCut 的编辑能力
5. **Headless mode（自动化 / 批量渲染）**—— 不开 UI 也能跑渲染管线
6. **A scripting tab directly in the editor（新增）**—— 编辑器里直接内嵌脚本 Tab，操作指向 Editor API

> 视野锚点：把 1 + 2 + 4 放一起看，OpenCut 的目标不是做一个剪辑工具，而是成为「**视频编辑的 Linux 内核**」——Rust core 提供受控、可编程、可被 AI 调用的底层能力，UI 只是众多壳之一。这与 Palmier Pro（MCP 反转的视频编辑器，Swift 6.2 / macOS 26 单端）走的是**完全不同的路径**——Palmier Pro 把 AI 拽进编辑器，OpenCut 把编辑器拽进 AI 生态。

## 当前阶段：能用什么 / 不能用什么

| 入口 | 状态 | 说明 |
|---|---|---|
| [opencut.app](https://opencut.app) | ✅ 可用 | **经典版**实跑 |
| [opencut-classic](https://github.com/OpenCut-app/opencut-classic) | 📦 Archived | 经典版仓库，251 Star（2026-09），README 仍建议"今天要用就拿这个" |
| [new.opencut.app](https://new.opencut.app) | 🟡 预览中 | rewrite 部署入口，正式切换前承载新版 |
| `OpenCut-app/OpenCut` main 分支 | 🔧 重构中 | `apps/web` 已有 `routes/editor.tsx`，不再只是中文 hello world 空壳 |
| `apps/desktop`（GPUI + Rust） | 🧪 早期 | README 自述"just a window that opens"，骨架已就位 |
| Rust core 抽成 `crates/*` | ⏳ 规划中 | workspace 留了入口，crates 尚未抽离 |
| MCP server / Plugin SDK | ❓ 未落地 | 在 README 路线图里承诺 |
| 第三方贡献 | ⏸ 暂不接收 | README 仍在：「We're not set up to take outside contributions yet」 |

**实操建议**：今天想真正用 OpenCut 剪片，就 clone `opencut-classic` 跑经典版；想跟 rewrite 进度、提 PR 或搭插件架构，等 README 把「not set up to take contributions」撤掉再说。

## 商业锚点：Sponsors 已经就位

README 的 Sponsors 一节放的仍是 **fal.ai**——「Generative image, video, and audio models all in one place」。这透露 OpenCut 团队在「视频编辑 + 生成式 AI」这条线上的合作意图**没有变**：编辑是 OpenCut 做，**生成素材**走 fal.ai 的 API（Kling、可灵、Veo、Runway Gen-4 这类）。OpenCut 不自己训模型，而是把「编辑层」做到极致，「生成层」靠生态合作。

> 这种定位对个人创作者意义重大：开源剪辑工具少有能撑到「8.9 万 Star + 拿到 fal.ai 这种级别赞助」的——它意味着 OpenCut 有动力把**第三方生成模型**接进时间轴，而不是搞自己的闭源模型。

## 适合谁 / 不适合谁

**适合**

- 想跟一个「产品级开源剪辑项目」的 rewrite 进度，关注插件 / MCP / Rust core 落地的全栈或 Rust 工程师
- 已经在用 CapCut、剪映、Premiere Rush 这类「轻量剪辑」工具，想找**无水印 / 无云锁定**开源替代品的创作者（用 classic 版即可）
- 关注 **MCP for AI agent 编辑**的实验者——OpenCut 是少数把 MCP 和脚本 Tab 都写进路线图的开源视频编辑器
- 想学「TanStack Start + Elysia + Cloudflare Pages/Workers + Moon monorepo + GPUI/Rust 三端同源」这套 2026 年现代 TS + Rust 混合模板的开发者——rewrite 代码正好是从空到全的最佳参照

**不适合**

- 想要「**今天**就用上**完整**开源视频编辑器」的人——classic 版能用但功能浅，new 版还不能投入剪辑
- 需要 Pro 级调色、多机位剪辑、复杂音频混音的工作流——OpenCut 不是 DaVinci Resolve / Kdenlive 的对手
- 移动端刚需者——桌面端才刚"开出一个窗口"，移动端在路线图里
- 想立刻拿 PR 进来的贡献者——目前**不接受外部贡献**

## 一段决策建议

如果你在找「一个**长期有戏**的开源视频编辑器跟下去」，OpenCut 是 2026 年值得放进观察列表的少数项目之一——8.9 万 Star、fal.ai 赞助、明确把 MCP / 插件 / 脚本 Tab 写进路线图，且 **Rust core 已落进仓库（GPUI 桌面端开了第一个窗口）**。这些是比「README 写得多好」更实在的信号。但**今天就想剪片**就记住：

1. 跑 `opencut-classic`（或打开 [opencut.app](https://opencut.app)），先把基础剪辑流程验证一遍
2. clone `OpenCut-app/OpenCut`，按 README 装 proto → `proto use` → `moon run web:dev`，再看一眼 `apps/web/src/routes/editor.tsx` 和 `apps/desktop/src/main.rs`——这两个文件就是 rewrite 阶段"工程结构长什么样"的缩影

至于真正把 Rust core 抽成 crates、Desktop/Mobile/Plugin SDK/MCP server——按团队一步步落地的节奏，桌面端"窗口"已经立起来了，接下来会往里填真实的渲染与编辑能力。在那之前，**不必在路线图上多做预期**，盯仓库推送即可。

## 关键事实速查

- **仓库**：[OpenCut-app/OpenCut](https://github.com/OpenCut-app/OpenCut)
- **经典版**：[OpenCut-app/opencut-classic](https://github.com/OpenCut-app/opencut-classic)（archived）
- **在线体验**：[opencut.app](https://opencut.app)（经典版） / [new.opencut.app](https://new.opencut.app)（rewrite 预览）
- **License**：MIT
- **首 commit**：2025-06-22
- **最新 push**：2026-08-10（latest `pushed_at`，commit `feat(desktop): add foundational GPUI primitives`，2026-08-01）
- **Star / Fork**：89,302 / 8,819（截至 2026-09，GitHub API `updated_at` 2026-09-13）
- **主语言**：TypeScript（Rust 已落地于 `apps/desktop`）
- **前端栈**：TanStack Start + React 19 + Tailwind 4 + Vite 8
- **后端栈**：Elysia on Cloudflare Workers
- **桌面端**：GPUI 0.2.2 + Rust（edition 2024），预留 `crates/*`
- **Monorepo**：Moon + proto（bun/moon/rust）+ bun，Cargo workspace
- **路线图**：Editor API / plugin-first / MCP server / Headless / 脚本 Tab / 三端同源
- **赞助方**：fal.ai
- **作者**：Maze Winther（主导）
- **Open issues**：378（多数是重写期间的 roadmap / 讨论帖）