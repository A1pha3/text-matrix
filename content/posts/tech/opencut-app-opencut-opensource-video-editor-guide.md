---
title: "OpenCut：开源 CapCut 替代品的双仓库真相与重写路线图"
date: 2026-06-26T18:19:00+08:00
slug: "opencut-app-opencut-opensource-video-editor-guide"
description: "OpenCut 是 GitHub 上最火的 CapCut 开源替代品（近 6 万 Star），但当前仓库仍处于重写脚手架阶段，真正的产品仍跑在已归档的 classic 版本。本文拆解两个仓库的关系、Rust 引擎 + 插件 + MCP + Headless 的重写路线图，以及如何选型。"
draft: false
categories: ["技术笔记"]
tags: ["OpenCut", "视频编辑器", "CapCut 替代品", "Rust 引擎", "MCP"]
---

## 先给一个核心判断

`OpenCut-app/OpenCut` 当前是一个**几乎空壳的重写仓库**：`apps/web/src/routes/index.tsx` 只有一行 `<p>hello world!</p>`，`apps/web/src/hooks` 只有 `use-mobile.ts`，`apps/web/src/lib` 只有 shadcn 的 `utils.ts`。但它顶着近 6 万 GitHub Stars、6.5K Forks，是「开源 CapCut 替代品」这个赛道里关注度最高的项目。

真相是：**生产可用的 OpenCut 现在跑在另一个仓库 `opencut-app/opencut-classic` 上**，并部署在 `opencut.app`（Next.js + WASM/Rust 合成器 + Docker 自托管）。`OpenCut-app/OpenCut` 仓库本身在 2026-05-27 的 commit `chore: replace codebase with rewrite` 中被整体替换成重写脚手架，README 直接告诉你「`opencut.app` 仍在运行 classic 版本；重写完成前先去 `opencut-classic`」。等到重写就绪，`new.opencut.app` 会接替 `opencut.app`，classic 退到 `old.opencut.app`。

要正确评估这个项目，必须把「两个仓库」和「重写路线图」拆开看。

## 仓库身份卡

| 项 | 数据 |
|---|---|
| 当前仓库 | `OpenCut-app/OpenCut`（默认 GitHub 链接） |
| 上线仓库 | `opencut-app/opencut-classic`（已 archive，README 标记「Legacy」） |
| 当前域名 | `opencut.app`（classic）、`new.opencut.app`（rewrite beta） |
| Stars | 59,964（2026-06-26 抓取） |
| Forks | 6,505 |
| Watchers | 59,964 |
| Open Issues | 329 |
| 主语言 | TypeScript 212,960 行 + CSS 4,631 行（重写仓库；classic 仓库另有 Rust + WASM） |
| 许可证 | MIT |
| 描述 | "The open-source CapCut alternative" |
| Topics | `editor`、`oss`、`videoeditor` |
| 主要赞助 | fal.ai、Vercel（OSS 计划） |
| 维护者 | Maze Winther（个人为主要 contributor，2025-06-22 创立组织） |
| Discord | `zmR9N35cjK`（服务器 ID `1386309140057690133`） |

> ⚠️ **数据时效**：上述 Star/Fork 数随时间变化，但两个仓库的分工关系是 README 里写死的——classic 仓库的 README 第一行就声明「This is the original OpenCut codebase. It's archived and no longer maintained. The rewrite is happening at `opencut-app/opencut`.」

## 两个仓库的关系图

```text
        ┌────────────────────────────────────────────┐
        │  opencut.app （生产域名，仍是 classic 版）  │
        │  Next.js 14 + Docker 自托管 + WASM 前端    │
        └──────────────────┬─────────────────────────┘
                           │
                           ▼
        ┌────────────────────────────────────────────┐
        │  opencut-app/opencut-classic （归档仓库）   │
        │  - apps/web/         Next.js 应用          │
        │  - apps/desktop/     GPUI 桌面端（WIP）     │
        │  - rust/             Rust core（合成器、   │
        │                      效果、蒙版、WASM 绑定）│
        └──────────────────┬─────────────────────────┘
                           │ 2026-05-27 「replace codebase
                           │ with rewrite」整体替换
                           ▼
        ┌────────────────────────────────────────────┐
        │  OpenCut-app/OpenCut （当前仓库，重写中）   │
        │  - apps/web/         TanStack Start +      │
        │                      React 19 + shadcn      │
        │  - apps/api/         Elysia + Cloudflare    │
        │                      Workers（API stub）    │
        │  - rust/ 还没建      （待落地）             │
        └──────────────────┬─────────────────────────┘
                           │
                           ▼
        ┌────────────────────────────────────────────┐
        │  new.opencut.app （重写预览域名）          │
        │  暂时只是 hello world! 占位页              │
        └────────────────────────────────────────────┘
```

经典版的 README 三句话把定位说得很清楚：

> - **Privacy**: Your videos stay on your device
> - **Free features**: Most basic CapCut features are now paywalled
> - **Simple**: People want editors that are easy to use - CapCut proved that

这就是 OpenCut 的价值主张——**本地优先、免费、不臃肿**。剩下要回答的问题就是：重写打算怎么实现这套承诺。

## 重写路线图（来自 #811 Tracking Issue）

官方在 issue #811「Tracking: OpenCut rewrite」里把重写拆成 6 个目标。架构师只画了两个 Mermaid 图就把「engine 与 UI 分离」的核心思想说完了：

```text
flowchart TD
    Web --> Core
    Desktop --> Core
    Android --> Core
    iOS --> Core
    Core["Rust core (engine)"]
```

```text
flowchart TD
    MCP --> Core
    Headless --> Core
    Scripting --> Core
    Core["Rust core (engine)"]
```

**关键判断**：所有 UI 入口（Web、桌面、Android、iOS）和所有自动化入口（MCP server、Headless、Scripting tab）都共用同一个 Rust core。这与 classic 的「TypeScript + WASM 调用 Rust 子集」是同一思路，但 classic 里 Rust 是被动调用的子模块，重写要把它升格为唯一的「engine」。

### 6 个具体目标

1. **Editor API** —— 一套稳定 API，让第三方能在引擎之上建自定义 UI。
2. **Plugin system** —— 一等公民的三方插件机制，编辑器默认保持轻量，**插件决定你自己的编辑器装什么**。FAQ 里直接写明：「The opposite. Plugins let us keep the editor light by default.」。
3. **Desktop / Mobile / Browser from one codebase** —— 同一份代码跑桌面、移动、浏览器，依赖 Rust core 抹平平台差异。
4. **MCP server** —— 让 AI agent（如 Claude Code）通过 MCP 操作编辑器。classic 版已经在 PR #752「feat: MCP server, UI fixes, and CLAUDE.md」做过一版实验：9 个工具（`get_timeline`、`split`、`remove_range`、`trim`、`undo`、`redo`、`seek`、`play`、`pause`），通过 WebSocket bridge 接到 Claude Code。
5. **Headless mode** —— CLI + 批渲染 + CI 流水线。
6. **Scripting tab** —— 编辑器内置脚本运行入口。

附加收益（同一个 issue 列出）：渲染管线更稳定更快、自动字幕修一组 bug、元素可分组、转场和滤镜、新效果库、键盘优先模式（opt-in）、UI 视觉翻新。

## 当前代码实际状态

写文章前有必要澄清「现在到底能跑什么」：

| 文件 | 状态 |
|---|---|
| `apps/web/src/routes/index.tsx` | `<p>hello world!</p>` |
| `apps/web/src/routes/__root.tsx` | 只有 `TooltipProvider` 包裹 + TanStack Router devtools |
| `apps/web/src/components/ui/*` | shadcn 全套 50+ 原子组件（button、dialog、command、resizable、sidebar 等），但**未拼装成任何编辑器 UI** |
| `apps/web/src/hooks/` | 仅 `use-mobile.ts` |
| `apps/web/src/lib/` | 仅 `utils.ts`（`cn()` helper） |
| `apps/api/src/index.ts` | Elysia + Cloudflare Worker adapter，3 个 endpoint：`GET /`（ok）、`GET /health`（带时间戳）、`POST /echo`（zod 校验） |
| `apps/web/wrangler.jsonc` | 已绑 `new.opencut.app`（custom_domain），`main: @tanstack/react-start/server-entry` |
| `apps/api/wrangler.jsonc` | `opencut-api`，`compatibility_date: 2025-06-01` |
| `rust/` | **不存在**（仅 `.moon/toolchains.yml` 启用了 `rust: {}` 占位，等第一个 Cargo.toml 出现时自动接管） |
| `docs/` | **不存在**（issue #811 FAQ 里说「We're still writing the architecture docs. Once those are out, you'll be able to contribute with a clear direction.」） |

**结论**：仓库现在的角色是「脚手架 + 愿景声明」。所有 Rust 引擎代码、UI 业务逻辑、插件加载器、MCP 实现都还是空的。如果你现在 clone 下来想「用上 OpenCut」，你拿到的是 hello world 占位页面 + 一个会响 `/health` 的 Cloudflare Worker。

## 工程栈与部署拓扑

重写阶段的工具链经过仔细选型，每一个选择都能从仓库里看到依据：

### 工具链层（monorepo + 版本管理）

```yaml
# .prototools
moon = "2.3.3"
bun  = "1.3.11"
```

```yaml
# .moon/toolchains.yml
javascript: {}
bun:
  version: '1.3.11'
  installDependencies: true
rust: {}  # 占位，等 Cargo.toml 出现自动接管
```

```yaml
# .moon/workspace.yml
projects: ['apps/*']
```

```toml
# bunfig.toml
[install]
minimumReleaseAge = 604800  # 7 天最小发布间隔，挡掉 npm 上当天发布的可疑包
```

四个文件的组合意图很清晰：
- **proto** 钉死 moon + bun 版本号，本地与 CI 看到完全一致的工具链。
- **moon** 做任务编排、依赖缓存、CI 矩阵（`.github/workflows/bun-ci.yml` 里 `moon ci` 是单一入口）。
- **bun** 是包管理与运行时，1.3.11 在 2026 上半年是较新版本。
- **`minimumReleaseAge = 604800`** 是显式安全策略——不要当天发版的依赖。

### CI 矩阵

```yaml
# .github/workflows/bun-ci.yml
on:
  push:
    branches: [main]
    paths-ignore: ["*.md"]
  pull_request:
    branches: [main]
    paths-ignore: ["*.md"]

jobs:
  ci:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
```

只跑 `moon ci`，三平台矩阵。`paths-ignore: ["*.md"]` 让纯文档 PR 不浪费 CI 时间。

### Web 前端栈（`apps/web/package.json`）

- **框架**：React 19.2 + TanStack Start + TanStack Router（file router，`.cta.json` 里 `mode: "file-router"`）+ Vite 8
- **样式**：Tailwind 4（`@tailwindcss/vite`）+ shadcn（`base-mira` 风格）+ `hugeicons` 图标
- **表单 / 数据**：`react-hook-form`、`@hookform/resolvers`、`zod`、`recharts 3.8`
- **运行时**：部署到 Cloudflare Workers（`@cloudflare/vite-plugin`），域名 `new.opencut.app`
- **基建组件**：`@base-ui/react`、`radix-ui`、`vaul`、`cmdk`、`embla-carousel-react`、`sonner`、`@tanstack/react-devtools`

Vite 配置同时挂了 5 个插件：

```ts
plugins: [
  devtools(),
  cloudflare({ viteEnvironment: { name: 'ssr' } }),
  tailwindcss(),
  tanstackStart(),
  viteReact(),
]
```

### API 后端栈（`apps/api`）

```ts
// apps/api/src/index.ts
import { Elysia, t } from "elysia";
import { CloudflareAdapter } from "elysia/adapter/cloudflare-worker";

export default new Elysia({ adapter: CloudflareAdapter })
  .get("/", () => ({ status: "ok" }))
  .get("/health", () => ({ healthy: true, timestamp: new Date().toISOString() }))
  .post("/echo", ({ body }) => body, {
    body: t.Object({ message: t.String() }),
  })
  .compile();
```

- **框架**：Elysia（Bun 生态里对标 Hono / Fastify 的 TypeScript 框架）
- **部署**：Cloudflare Workers，`compatibility_date: 2025-06-01`，末尾 `.compile()` 触发 AoT 编译（Cloudflare adapter 要求）
- **当前功能**：健康检查 + 回声接口。是个完整可部署的 hello API，但不是真正的 Editor API。

### Classic 栈（`opencut-app/opencut-classic`）

虽然不在当前仓库里，但理解 OpenCut 不能绕过：

- **前端**：Next.js（页面路由）
- **后端**：Docker Compose 起 Postgres + Redis + 自托管 serverless-redis-http
- **核心**：`rust/` 子模块，GPU 合成器、效果、蒙版、WASM 绑定——「We're actively migrating business logic here from TypeScript」
- **桌面**：`apps/desktop/` 用 GPUI（Zed 编辑器同款 Rust GUI 框架），状态：进行中
- **本地 WASM 开发流程**：`bun run build:wasm` → `bun link` → `bun link opencut-wasm` → `bun dev:wasm` 监听 rebuild
- **自托管**：`docker compose up -d` 一键全套（含生产构建），端口 3100

## 现在到底能用什么？

四个层级的可选项，按时间轴排列：

### 1. 现在就用 —— opencut.app（classic 版）

如果你的目标是「立刻找到一个不付费、无水印、视频留在本地的 CapCut 替代品」，**直接访问 [opencut.app](https://opencut.app)，那是 classic 版本，仍然可以正常使用**。Vercel 边缘缓存，HTTP 200，主页 SSR 走 Next.js。

如果想自托管：

```bash
git clone https://github.com/opencut-app/opencut-classic
cd opencut-classic
cp apps/web/.env.example apps/web/.env.local
docker compose up -d db redis serverless-redis-http
bun install
bun dev:web
# http://localhost:3000
```

或者跳过 Docker（不用 DB / Redis 时）：

```bash
bun install
bun dev:web
```

完整生产构建（端口 3100）：

```bash
docker compose up -d
```

### 2. 观望重写 —— new.opencut.app

`new.opencut.app` 当前返回 200，但内容只是 hello world 占位。它的存在意义是验证部署管线（TanStack Start + Cloudflare Workers + custom domain）跑通。等真正的 UI 组件落地，它会从 hello world 变成可点击的编辑器。

### 3. 跑通本地重写脚手架

```bash
# 全局装 proto
bash <(curl -fsSL https://moonrepo.dev/install/proto.sh)

# 进仓库
git clone https://github.com/OpenCut-app/OpenCut
cd OpenCut

# proto 自动按 .prototools 装 moon + bun
proto use
bun install

# 起 web
moon run web:dev   # localhost:5173

# 起 api
moon run api:dev   # localhost:8787
```

注意两个 dev server 都会跑起来，但 web 端只显示 hello world，api 端能 curl `/health` 拿时间戳。

### 4. 等待里程碑

issue #811 是官方 tracking issue，6 个里程碑目前一个都还没打勾。最近 commit（`ci: update workflow for rewrite`、`Merge branch 'rewrite'`）还在脚手架阶段。等以下任一信号出现，意味着重写进入实质阶段：

- `rust/` 目录首次提交 Cargo.toml（Rust core 真正启动）
- `docs/architecture.*` 文档出现（FAQ 说「Once those are out, you'll be able to contribute with a clear direction」）
- 第一个端到端 UI 组件（非 shadcn 模板）出现在 `apps/web/src/components/` 下业务目录里
- MCP server、Plugin loader、Headless CLI 任一模块的代码提交

## 适合谁 / 不适合谁

### 适合

- **寻找 CapCut 替代品的视频创作者**：classic 版可以立刻用，本地优先、免费、无水印。
- **做 Rust + WASM + GPU 合成器的研究 / 二次开发者**：classic 仓库 `rust/` 已经是可独立研究的子项目（GPU compositor、effect、mask 子系统）。
- **AI agent 工程化方向探索者**：issue #778（Headless Rendering SDK）、#827（Headless Mode for agents）、PR #752（MCP server）这三件事构成了「用 Claude Code 编辑视频」的早期路线图，可以追踪 OpenCut 的实装进度作为业内信号。
- **多端编辑器架构学习者**：engine / UI 分离、单一 Rust core 跑 Web + 桌面 + 移动的拓扑在编辑器赛道不常见，值得跟着重写进度读。

### 不适合

- **期望现在就在 OpenCut-app/OpenCut 仓库找到可用编辑器的开发者**——它现在只是脚手架。
- **想立刻通过 MCP 让 AI agent 剪辑视频的人**——经典版的 PR #752 给了原型但未发布到 main，重写版本还没实装。
- **对插件生态有强需求的团队**——plugin loader 没写完之前别赌。
- **寻求成熟商业级支持的开源软件**——OpenCut 的开发节奏由 Maze Winther 主导，目前没有公开 roadmap timeline（issue #811 FAQ 最后一条「Is there a timeline on when it's coming out?」没有回答）。

## 几个值得追的「状态信号」

后续如果要持续观察这个项目，可以关注这几个低噪音信号：

1. **`OpenCut-app/OpenCut` 的 `rust/` 目录何时首次出现**——这是 engine 启动的物理标志。
2. **`new.opencut.app` 何时不再显示 hello world**——UI 组件首次接入的标志。
3. **issue #811 何时转为 closed**——重写里程碑打完的时刻。
4. **classic 仓库 `opencut-app/opencut-classic` 何时被标 `Archived` 而非仅 README 标记**——切换域名准备就绪的信号。
5. **Discord `#beta-testing` 频道**（隐藏在 `discord.gg/zmR9N35cjK` 内）——官方说「Sneak peeks and early builds of the desktop/mobile app go to the Discord first」，所有桌面/移动端的早期构建都先在 Discord 释出，不走 GitHub Releases。
6. **`docs/anomaly-decisions/` 类似的设计文档**——FAQ 说「We're still writing the architecture docs」是开放贡献的前置条件。

## 一个常被忽略的小细节

`bunfig.toml` 里的 `minimumReleaseAge = 604800`（7 天）很少出现在同类项目里。它表示所有 npm 依赖必须发版满 7 天才能被安装。这是一个**显式的供应链风险策略**，挡掉 npm 上当天发版就被供应链攻击接管的包。对于一个「6 万 Star 的开源视频编辑器」来说，把这条作为仓库级别的硬约束写入 bunfig，而不是留给各自 package.json 的 `pnpm.onlyBuiltDependencies`，说明团队把安全门控当成 monorepo 级别的关注点。这个细节在 PR review 时也适用：任何新加的依赖若违反 7 天窗口，CI 应能立刻 fail。

## 参考链接

- 主仓库：<https://github.com/OpenCut-app/OpenCut>
- 归档的 classic 仓库：<https://github.com/opencut-app/opencut-classic>
- 重写路线图 tracking issue：<https://github.com/OpenCut-app/OpenCut/issues/811>
- 早期 MCP 实验 PR：<https://github.com/OpenCut-app/OpenCut/pull/752>
- Headless Rendering SDK 提案：<https://github.com/OpenCut-app/OpenCut/issues/778>
- 生产域名（classic）：<https://opencut.app>
- 重写预览域名：<https://new.opencut.app>
- Discord：<https://discord.gg/zmR9N35cjK>
- 工具链说明：<https://moonrepo.dev/proto>

---

写这篇文章时仓库状态：59,964 Stars、329 Open Issues、classic 仓库仍在生产、rewrite 仓库处于 monorepo 脚手架阶段（hello world 占位 + Elysia API stub）。所有结论以仓库 README 与 #811 issue 的官方叙述为准。