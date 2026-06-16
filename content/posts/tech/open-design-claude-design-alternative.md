---
title: "Open Design：开源版 Claude Design 本地优先设计系统"
date: "2026-04-28T19:31:21+08:00"
slug: "open-design-claude-design-alternative"
description: "Open Design 是一个本地优先的开源设计系统，可作为 Claude Design 的开源替代方案。它支持将现有代码助手（Claude Code、Codex、Cursor Agent 等）作为设计引擎，内置 19 个 Skills 和 71 套品牌级设计系统。"
draft: false
categories: ["技术笔记"]
tags: ["Open Design", "Claude Code", "Design System", "Local-First", "开源"]
---

## 项目概览

Open Design（简称 OD）是一个本地优先（Local-First）的开源设计系统，定位是 Anthropic Claude Design 的开源替代方案。该项目于 2026 年 4 月发布（与 Claude Design 同期），目前已获得 189 Stars 和 22 Forks，采用 Apache-2.0 开源许可证。

与 Claude Design 不同的是，Open Design 不捆绑独立的 AI 模型，而是将现有的代码助手（Claude Code、Codex CLI、Cursor Agent、Gemini CLI、OpenCode、Qwen Code）直接作为设计引擎。用户只需在本地安装任意一种代码助手，Open Design 就能通过 19 个可组合的 Skills 和 71 套品牌级设计系统来驱动设计工作流。

**能力项：**

| 项目 | 具体说明 |
|--------|----------|
| 内置 Skills | 19 个，覆盖原型、PPT、移动端、仪表盘、定价页、文档等场景 |
| 内置设计系统 | 71 套（包含 Linear、Stripe、Vercel、Airbnb、Tesla、Notion 等知名产品的设计语言） |
| 视觉方向 | 5 种风格方向（Editorial Monocle、Modern Minimal、Tech Utility、Brutalist、Soft Warm） |
| 设备框架 | iPhone 15 Pro、Pixel、iPad Pro、MacBook、Brower Chrome |
| 预览与导出 | 沙箱 iframe 预览，支持 HTML、PDF、PPTX、ZIP 格式导出 |

## Claude Design 的问题与 Open Design 的解法

Claude Design 走红很快，但限制也很快暴露：闭源、付费、仅限云端、锁定在 Anthropic 模型和 Skills 体系内。没有检出场、没有自托管、无法部署到 Vercel、也无法替换为自己偏好的代码助手。

Open Design 要解决的就是这个矛盾：保留 Claude Design 的核心理念（Artifact-First 心理模型、实时 Todo 计划流、沙箱 iframe 预览、五维自检），同时去掉这些锁定限制。

它的解法可以归纳为六条设计原则：

**1. 不捆绑 Agent，让现有的为你工作**

OD 的守护进程（Daemon）会在启动时扫描 PATH 环境变量，检测用户已安装的代码助手 CLI（claude、codex、cursor-agent、gemini、opencode、qwen）。检测到的第一个 CLI 即成为设计引擎，通过标准 I/O 通信。如果没有任何 CLI，OD 也会提供 Anthropic API 作为 BYOK（Bring Your Own Key）回退方案。

**2. Skills 是文件夹，不是插件**

遵循 Claude Code 的 SKILL.md 约定，每个 Skill 就是一个文件夹（包含 SKILL.md + assets/ + references/）。向 skills/ 目录添加一个新文件夹并重启守护进程，该 Skill 就会出现在选择器中。这与传统的插件系统不同——无需构建、无需注册表，只要文件存在就能被识别。

**3. 设计系统是 Markdown，不是 Theme JSON**

项目采用 VoltAgent/awesome-design-md 定义的 9 段式 DESIGN.md 规范（颜色、字体、排版、间距、布局、组件、动效、品牌、反模式）。每个 Artifact 输出时会读取当前激活的设计系统文件。切换系统后，下一次渲染就会使用新的设计令牌，设计系统天然具备可移植性。

**4. 交互式问答表单将 80% 的返工拦截在发生之前**

每一轮全新设计简报（Brief）都以一个 `question-form` 发现表单开始，而非直接生成代码。这个表单强制在生成设计之前先锁定：界面类型、目标受众、视觉基调、品牌上下文、规模和约束条件。30 秒的单选题比 30 分钟的来回返工要高效得多。

**5. 守护进程让 Agent 感觉像在本地工作，实际上它就是**

守护进程启动代码助手时，会将工作目录（cwd）设置为项目的 artifact 文件夹（`.od/projects/<id>/`）。Agent 拥有真正的 Read、Write、Bash、WebFetch 能力，可以读取 Skill 的 assets/template.html、grep 项目中的 CSS 变量、写入品牌规范文件，或者生成 PPTX/ZIP/PDF 文件。这些文件会在回合结束时出现在文件工作区，作为可下载的产物。

**6. Prompt Stack 就是产品**

发送时的组合不是简单的"系统提示 + 用户提示"，而是一个多层叠加的 Prompt Stack：

```
DISCOVERY 指令（第一轮表单、第二轮品牌分支、TodoWrite、五维自检）
+ 身份宪章（OFFICIAL_DESIGNER_PROMPT，抗 AI 垃圾检查，初级通过条件）
+ 激活的 DESIGN.md（71 个可用系统）
+ 激活的 SKILL.md（19 个可用 Skills）
+ 项目元数据（类型、保真度、演讲注释、动画、参考 ID）
+ Skill 侧文件（自动注入的预检：读取 assets/template.html + references/*.md）
+（Deck 类型且无 Skill 种子）DECK_FRAMEWORK_DIRECTIVE
```

每一层都是可编辑的文件。阅读 src/prompts/system.ts 和 src/prompts/discovery.ts 就能看到实际的合约内容。

## 架构与关键机制

Open Design 的技术架构分为三个主要层：浏览器前端、本地守护进程、代码助手 CLI。

**技术栈明细：**

| 层级 | 技术选型 |
|------|----------|
| 前端 | Vite 5 + React 18 + TypeScript |
| 守护进程 | Node.js 18+ · Express · SSE 流式推送 · better-sqlite3 |
| Agent 传输 | child_process.spawn + claude-stream-json 解析器（Claude Code）或行缓冲纯 stdout（其他 CLI） |
| 存储 | `.od/projects/<id>/` 下的纯文件 + `.od/db.sqlite`（SQLite） |
| 预览 | `srcdoc` 沙箱 iframe + per-Skill artifact 解析器 |
| 导出 | HTML（内联资源）· PDF（浏览器打印）· PPTX（Skill 定义）· ZIP（archiver） |

**本地存储结构（.od/）：**

```
.od/
├── app.sqlite                 ← 项目 · 对话 · 消息 · 打开的标签页
├── artifacts/                 ← "保存到磁盘" 的一次性渲染（带时间戳）
└── projects/<id>/             ← 按项目的临时目录，也是 Agent 的 cwd
```

首次运行 pnpm dev:all 时，守护进程会自动创建整个 .od/ 目录结构，无需手动运行 od init。

## 安装与最小示例

**环境要求：**

- Node.js 18+
- pnpm（或 npm）
- 至少一个代码助手 CLI（claude、codex、cursor-agent、gemini、opencode、qwen）之一

**安装步骤：**

```bash
git clone https://github.com/nexu-io/open-design.git
cd open-design
pnpm install         # 或 npm install
pnpm dev:all         # 启动守护进程 (:7456) + Vite (:5173)
open http://localhost:5173
```

首次启动时：

1. 守护进程检测 PATH 上有哪些 Agent CLI 并自动选择
2. 加载 19 个 Skills + 71 个设计系统
3. 弹出欢迎对话框，提示可粘贴 Anthropic API Key（仅在使用 BYOK 回退路径时才需要）
4. 自动在仓库根目录创建 .od/ 运行时文件夹（已加入 .gitignore，不会被提交）

**最小使用流程：**

1. 打开 http://localhost:5173
2. 选择一个 Skill（如 web-prototype）
3. 选择一个设计系统（如 Linear App）
4. 输入设计简报，如"帮我设计一个社交媒体动态流页面"
5. 等待问题表单弹出并回答（界面类型、受众、视觉基调等）
6. 观察 Todo 卡片实时流式更新
7. Artifact 在沙箱 iframe 中实时渲染
8. 点击"Save to disk"或下载为 HTML/PDF/ZIP

## 代码结构与模块拆解

**仓库结构一览：**

```
open-design/
├── daemon/                        ← Node.js 守护进程，唯一后端服务
│   ├── cli.js                     ← od bin 入口
│   ├── server.js                  ← /api/* 路由（项目、聊天、文件、导出）
│   ├── agents.js                  ← PATH 扫描器 + 每个 CLI 的 argv 构建器
│   ├── claude-stream.js           ← Claude Code stdout 的流式 JSON 解析器
│   ├── skills.js                  ← SKILL.md frontmatter 加载器
│   ├── design-systems.js          ← DESIGN.md 加载器 + 色板提取器
│   ├── lint-artifact.js           ← P0/P1 自检（Agent 输出）
│   ├── projects.js                ← 按项目的文件系统辅助函数
│   ├── db.js                      ← SQLite schema（项目/消息/模板/标签页）
│   └── frontmatter.js             ← 零依赖的 YAML 子集解析器
│
├── src/                           ← Vite + React + TS 前端
│   ├── App.tsx                    ← 路由、引导、设置
│   ├── components/                ← 27 个组件（chat、composer、picker、preview...）
│   ├── prompts/
│   │   ├── system.ts              ← composeSystemPrompt(base, skill, DS, metadata)
│   │   ├── official-system.ts     ← 身份宪章
│   │   ├── discovery.ts           ← 第一轮表单 + 第二轮品牌分支 + 五维自检
│   │   ├── directions.ts          ← 5 种视觉方向 × OKLch 色板 + 字体栈
│   │   └── deck-framework.ts      ← Deck 导航 / 计数器 / 打印样式表
│   ├── artifacts/
│   │   ├── parser.ts              ← 流式 artifact 标签提取器
│   │   └── question-form.ts       ← question-form JSON schema + 回放
│   └── runtime/
│       ├── srcdoc.ts              ← iframe 沙箱包装器
│       ├── markdown.tsx            ← 助手消息渲染器
│       └── exports.ts             ← HTML / PDF / ZIP 导出辅助函数
│
├── skills/                        ← 19 个 SKILL.md Skill 打包
│   ├── web-prototype/             ← 原型模式默认项
│   ├── saas-landing/              ← 营销页面（Hero / Features / Pricing / CTA）
│   ├── dashboard/                 ← 管理后台 / 分析仪表盘
│   ├── mobile-app/                ← 手机框架屏幕
│   ├── guizang-ppt/               ← 杂志风 Web PPT（默认 Deck 类型）
│   ├── pm-spec/                   ← PM 规格文档
│   └── ...（共 19 个）
│
├── design-systems/                ← 71 个 DESIGN.md 系统
│   ├── default/                   ← 中性现代风格（起始模板）
│   ├── linear-app/  vercel/  stripe/  airbnb/  notion/  ...
│   └── README.md                  ← 完整目录
│
├── assets/frames/                 ← 跨 Skill 共享的设备框架
│   ├── iphone-15-pro.html
│   ├── android-pixel.html
│   └── ...
│
└── .od/                           ← 运行时数据，gitignored，自动创建
```

**关键模块详解：**

**daemon/claude-stream.js** — 这是 OD 最关键的文件之一。Claude Code 的 stdout 输出的是流式 JSON（每行一个 JSON 对象），claude-stream.js 负责解析这些行并重建流式响应。其他 CLI（Codex、Gemini 等）使用纯 stdout，无需特殊解析。

**src/artifacts/parser.ts** — 负责从 Agent 输出中提取 artifact 标签。这是 OD 的核心机制：Agent 生成一个包含 HTML、CSS 和 JavaScript 的 artifact 片段，parser 提取后渲染到沙箱 iframe 中供实时预览。

**src/prompts/discovery.ts** — 这里定义了第一轮问答表单的 Prompt 模板和五维自检的评分逻辑。五维分别指：哲学（Philosophy）、层级（Hierarchy）、执行（Execution）、特异性（Specificity）和品牌契合度（Brand Fit）。

## 适用场景、优势与边界

**最适合的场景：**

- 需要快速生成设计原型（LP、仪表盘、移动端、PPT）的开发者
- 已习惯使用代码助手但缺乏设计能力的工程师
- 需要在团队中共享统一设计语言的小型工作室
- 想自托管设计工具但不想锁定在特定云服务的企业

**主要优势：**

1. **零锁定**：不依赖任何云服务，不绑定特定模型，不限制代码助手选择
2. **本地优先**：所有项目文件存储在本地 .od/ 目录，完全可控
3. **技能可扩展**：添加新 Skill 只需在 skills/ 下新建文件夹，无需构建
4. **设计系统可移植**：71 套现成设计系统可一键切换，满足不同品牌需求
5. **导出自由**：不锁定在任何封闭格式中，HTML/PDF/PPTX/ZIP 全部可用

**需要认识的边界：**

1. **桌面 Electron 应用缺失**：OpenCoworkAI/open-codesign（同类开源项目）是桌面 Electron 应用，适合喜欢原生体验的用户；OD 是 Web 应用，更适合浏览器环境
2. **无内置模型**：OD 不捆绑模型，完全依赖用户的代码助手 CLI 或 API Key
3. **设计系统同步需要手动运行脚本**：设计系统通过 scripts/sync-design-systems.mjs 从上游 VoltAgent/awesome-design-md 同步，非实时更新
4. **移动端预览依赖设备框架图片**：设备框架（iPhone、Pixel 等）是预渲染的 HTML 文件，不是真正的设备模拟

## 总结与延伸阅读

Open Design 不捆绑模型、不依赖云服务，却提供了接近 Claude Design 的体验。它的"本地优先 + 代码助手作为引擎 + Skill 驱动"设计思路，对需要在本地跑设计工具、又不想锁定云服务的团队有直接参考意义。

**延伸阅读：**

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/nexu-io/open-design |
| 官方文档（中文） | https://github.com/nexu-io/open-design/blob/main/README.zh-CN.md |
| 快速开始 | https://github.com/nexu-io/open-design/blob/main/QUICKSTART.md |
| VoltAgent/awesome-design-md | https://github.com/VoltAgent/awesome-design-md（71 套设计系统的上游） |

*原文地址：https://github.com/nexu-io/open-design*
