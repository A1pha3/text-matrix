---
title: "Stitch Skills：给 Google Stitch 装的 16 个 Agent 技能，以及一套「接力棒」式的自主建站循环"
date: "2026-11-20T01:27:19+08:00"
slug: "google-labs-code-stitch-skills-agent-skill-plugins"
description: "Stitch Skills 是 Google Labs 为 Stitch MCP 写的 16 个 Agent 技能，分成 design、build、utilities 三个插件。本文拆解它的三插件分层、技能标准目录结构、code-to-design 的三段编排，以及用 .stitch/next-prompt.md 传接力的自主建站循环，并给出跨 harness 安装的兼容清单。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "设计系统", "Google Stitch", "Agent Skills", "前端"]
github_repo: "google-labs-code/stitch-skills"
source_key: "gh:google-labs-code/stitch-skills"
---

## 核心判断

Google Stitch 是个在线的 AI 界面设计工具，它自己能生成和编辑屏幕。但「生成屏幕」和「做一个产品」之间隔着很长的路：设计系统要一致、代码要能跑、多页要串起来、生成的东西得验收。

Stitch Skills 补的就是这段路 —— **16 个 Agent 技能**，让编码 agent 能驱动 Stitch，把「生成一张图」变成「迭代一个站点」。

它的设计里有三处值得单独讲：

**一、技能是插件，不是散装脚本。** 三个插件（`stitch-design`、`stitch-build`、`stitch-utilities`）各自成组，可以按需只装一个。README 特别提醒技能之间**常有相互依赖**，选择性安装时要把依赖一起带上。

**二、`code-to-design` 是一条三段编排链**，而不是一个动作。它强制串联「抽取静态 HTML → 抽取设计系统 → 上传」，而且 skill 描述里写死了「**即使只是简单的『保存』操作也必须用这个技能**，因为这是确保设计系统被提取、资产被正确链接的唯一方式」。

**三、`stitch-loop` 用一个文件当接力棒。** `.stitch/next-prompt.md` 作为迭代之间的中继，agent 读它 → 生成页面 → 集成进站点 → 写下一轮任务给下一棒。这让**多轮自主建站**成为可能，而不需要一个 orchestrator 常驻。

需要说清楚的定位边界：**它依赖 Stitch MCP 服务**，Stitch 本身是 Google 的托管服务（labs.google.com/stitch）。这套技能是客户端侧的编排层，不是 Stitch 的替代实现。而且仓库自己声明：**这不是 Google 官方支持的产品**，也**不符合 Google 开源软件漏洞赏金计划**的资格。

截至 2026 年 11 月 20 日，这个仓库有 10632 stars、1381 forks，TypeScript 为主，Apache-2.0 许可，2026 年 1 月创建，11 月 18 日仍有提交（合并了一个补充 `site-md` 技能文档的 PR）。

## 三插件分层

| 插件 | 技能数 | 职责 |
|---|---|---|
| `stitch-design` | 6 | 在 Stitch 里创建、管理、优化设计 |
| `stitch-build` | 5 | 从 Stitch 设计生成代码、框架集成、动效资产 |
| `stitch-utilities` | 5 | 提示增强、设计规范生成、标准执行 |

### design：设计侧六个

| 技能 | 做什么 |
|---|---|
| `code-to-design` | 前端代码（React、Vue 等）转 Stitch 设计：HTML 抽取 + 设计系统 + 上传 |
| `generate-design` | 从文本或图片生成新屏幕、编辑已有屏幕、创建设计变体 |
| `manage-design-system` | 管理 Stitch 里的设计系统 —— 上传 DESIGN.md 并把主题应用到屏幕 |
| `extract-design-md` | 直接从前端源码里抽出一份完整的 DESIGN.md |
| `extract-static-html` | 从运行中的 web app 抽取自包含静态 HTML，内联 CSS 和图片 |
| `upload-to-stitch` | 把本地资产（图片、模型、HTML）上传到 Stitch 项目 |

### build：代码侧五个

| 技能 | 做什么 |
|---|---|
| `react-components` | Stitch 屏幕 → React 组件系统，带自动化校验和设计令牌一致性 |
| `react-native` | Stitch HTML 设计 → 生产可用的 React Native 组件，含 StyleSheet 和平台相关代码 |
| `remotion` | 从 Stitch 项目生成演示视频，用 Remotion 做平滑转场和缩放 |
| `shadcn-ui` | 集成和构建 shadcn/ui 组件的专家指引 |
| `react-vite-dashboard` | Stitch 屏幕 → React + Vite 面板，用 TanStack Query、DESIGN.md 令牌和 Web3 读模式 |

### utilities：五个辅助

| 技能 | 做什么 |
|---|---|
| `design-md` | 分析 Stitch 项目，用语义语言生成完整 DESIGN.md |
| `enhance-prompt` | 把模糊的 UI 想法变成打磨过的 Stitch 优化提示 |
| `site-md` | 分析项目描述或站点需求，综合出项目宪法（SITE.md），供 Stitch Build Loop 使用 |
| `stitch-loop` | 从单个提示生成完整多页网站，带自动化校验 |
| `taste-design` | 生成强制「高级、反通用」UI 标准的 DESIGN.md |

## 技能标准目录结构

所有技能遵循同一个结构，这是整个仓库最值得学的一点：

```text
skills/<skill-name>/
├── SKILL.md           — agent 的「任务控制中心」
├── scripts/           — 可执行执行器（校验与网络）
├── resources/         — 知识库（检查清单与风格指南）
└── examples/          — 「黄金标准」语法有效参考
```

README 把它类比成「Mission Control」。这个四段式分工的含义是：**SKILL.md 负责编排，scripts 负责干活，resources 负责查，examples 负责对齐**。

一个具体的例子是 `generate-design`。它的 SKILL.md 里有一段「提示增强流水线」，规定**在调用任何 Stitch 生成或编辑工具之前，你 MUST 增强用户的提示**。第一步是分析上下文：

- **项目**：用 `list_projects` 找对的 `projectId`，没有就 `create_project` 建一个。
- **设计系统**：用 `list_design_systems` 查项目上有没有设计系统。**如果有，颜色、字体、圆角这些设计令牌已经在项目级别生效了 —— 生成提示里不要再包含任何颜色、字体或主题指令。** 如果没有，先委派给 `manage-design-system` 技能。

第二条是「已经有就别再说」的规则。这类约束看起来琐碎，但它是**防止设计令牌被提示词覆盖**的关键 —— 在 LLM 生成链路里，多说一句「按钮用蓝色」就可能把整个设计系统的色彩覆盖掉。

## 机制：三段编排与强制路径

`code-to-design` 的结构是「这个技能编排另外三个技能」：

1. **`extract-static-html`**：从构建产物或运行中的 dev server（Vite dev server、Angular CLI 的 `ng serve`）抽出一个自包含的 HTML 文件。
2. **`extract-design-md`**：分析源码（包括 Angular 的 `angular.json`、外部 `.html` 模板、主题文件和组件）生成设计系统 DESIGN.md。
3. **`upload-to-stitch`**：把 HTML 和设计系统上传到 Stitch 项目。

skill 的描述里那句「即使只是简单的『保存』操作也必须用这个技能」是重点 —— 它把**绕过完整路径**这件事直接堵死了。原因也说得清楚：这是确保设计系统被提取、资产被正确链接的唯一方式。

这不是多余的严格。如果只上传 HTML 而不抽设计系统，Stitch 项目里就没有令牌，后续生成的屏幕会跟你的代码长得不一样 —— 那个「迁移」就只迁了一半。

## 机制：接力棒循环

`stitch-loop` 是最有意思的一个技能。它把自己定义为一个**参与迭代式建站循环的自主前端构建器**。

循环的每一轮：

1. 从接力文件读取当前任务 —— `.stitch/next-prompt.md`
2. 用 Stitch MCP 工具生成一个页面
3. 把页面集成进站点结构
4. **把下一轮任务写回接力文件**

接力文件长这样：

```markdown
---
```

前置条件：

- **必需**：Stitch MCP 服务访问权限、一个 Stitch 项目、`.stitch/DESIGN.md`（没有就用 `design-md` 技能生成）、`.stitch/SITE.md`（记录站点愿景和路线图）
- **可选**：Chrome DevTools MCP 服务 —— 提供生成页面的视觉验证能力

这个设计的妙处在于**状态落在文件系统里，而不是某个 orchestrator 的内存里**。接力文件是纯文本，可以被人打开、编辑、提交进 git，也可以被另一个 harness 接棒。换句话说，**它把「多轮自主循环」变成了可交接的工作流**。

`site-md` 技能的存在就是为了喂这个循环 —— 它「分析项目简报或站点需求，综合出项目宪法（SITE.md），供 Stitch Build Loop 使用」。

## taste-design：把「反通用」写成规则

`taste-design` 技能直译过来是「品味设计」。它的描述很有性格：

> 生成 agent 友好的 DESIGN.md 文件，强制执行高级、反通用的 UI 标准 —— 严格排版、经过校准的色彩、非对称布局、持续微动效、硬件加速的性能。

它生成的 DESIGN.md 编码七类内容：视觉氛围、色彩校准、排版架构、组件行为、布局原则、动效哲学、**反模式清单**（明确列出被禁的 AI 设计陈词滥调）。

最后一条最关键。**「不要用渐变紫 + 圆角卡片 + 玻璃拟态」需要写成禁令，而不是指望模型不这么干。** 因为这些恰恰是模型最想用的 —— 它们在训练数据里出现频率最高。

## 安装矩阵

这是这个仓库最实用的一块内容 —— **同一套技能要跨 5 个以上 harness 安装，每个 harness 的机制都不一样**。

### Codex：marketplace + sparse checkout

```bash
codex plugin marketplace add google-labs-code/stitch-skills --ref main \
  --sparse .agents/plugins \
  --sparse plugins/stitch-design \
  --sparse plugins/stitch-build \
  --sparse plugins/stitch-utilities
```

`--sparse` 是可选的，用来只 checkout 列出的路径加快克隆。也可以走 Codex UI：Settings → Plugin Marketplaces → Add，填 Source、Git ref、Sparse paths。

注册后可以任意组合安装三个插件。

### Claude Code 与 Cursor：npx plugins

```bash
# Claude Code —— 装到当前项目
npx plugins add google-labs-code/stitch-skills --scope project --target claude-code

# Cursor —— 装到当前工作区
npx plugins add google-labs-code/stitch-skills --scope workspace --target cursor
```

### OpenCode：要手动

OpenCode **不使用** `npx plugins` / `npx skills`，也不认 Codex/Claude 的 marketplace 布局。所以要手动两步：

**Skills** —— 把需要的技能文件夹复制到可发现的路径：

```bash
mkdir -p .opencode/skills
cp -R plugins/stitch-design/skills/generate-design .opencode/skills/generate-design
# 对 plugins/*/skills/ 下的其它技能重复
```

OpenCode 也会读 `.claude/skills/` 和 `.agents/skills/`。

**这里有个命名坑**：OpenCode 要求 skill 的 `name` frontmatter 是小写 kebab-case，且**必须和目录名一致**。用 `stitch::…` 这类带命名空间的 skill 名（或任何非 kebab 形式）需要先改名才能被 OpenCode 加载。多余的 frontmatter（比如 `allowed-tools`）会被忽略。

**Stitch MCP** —— 在项目 `opencode.json` 或 `~/.config/opencode/opencode.json` 里加远程 MCP：

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "stitch": {
      "type": "remote",
      "url": "YOUR_STITCH_MCP_URL",
      "enabled": true
    }
  }
}
```

还有一个更隐蔽的坑：**技能指令里提到的工具名在不同 harness 里不一样** —— OpenCode 用 `webfetch` / `bash`，不是 `web_fetch` / `run_command`。适配到 OpenCode 时要优先用 OpenCode 的工具名。

### 选择性安装

```bash
npx skills add google-labs-code/stitch-skills
```

README 有个 IMPORTANT 提醒：**Stitch Design 技能之间常有相互依赖**。如果选择性安装，确保把必要的依赖一起装上。

## 前置条件

所有技能都要求 **Stitch MCP 服务已配置并运行**。README 明确：先按 Stitch MCP Setup Instructions 注册服务并配好环境变量和凭据。

还有一个文档导航的坑，README 专门提了：

> 如果 `stitch.withgoogle.com/docs` 下的链接跳转不正确，在同一 host 下打开目标路径（比如 `https://stitch.withgoogle.com/docs/learn/device-types/`）。

## 边界

- **依赖托管服务**。Stitch 本身是 Google 的在线产品（labs.google.com/stitch），这套技能是客户端编排层。没有 Stitch 就没有这套技能。
- **不是 Google 官方支持的产品**，且明确不符合 Google OSS 漏洞赏金计划资格。
- **技能质量不均**。16 个技能里 `generate-design`、`code-to-design`、`stitch-loop` 有详细的 SKILL.md 和脚本，而一些工具类技能（比如 `shadcn-ui`）更像是「专家指引」而不是自动化流程。**装之前自己看一眼你要用的那个技能有多厚。**
- **`enhance-prompt` 和 `taste-design` 是主观的**。它们把某种审美偏好写成了规则 —— 如果那不是你要的风格，`taste-design` 生成的 DESIGN.md 会主动把你的界面推向另一个方向。
- **OpenCode 支持是最弱的**。命名规则和工具名都要手工适配，而且 README 自己在 OpenCode 段落里承认了这点。
- **`react-vite-dashboard` 技能内置了 Web3 读模式**，这是个很窄的垂直场景，不是通用面板模板。

## 采用顺序

1. **先配 Stitch MCP**，按官方 setup 文档走完，确认 agent 能调 `list_projects`。这一步不通，后面全部免谈。
2. **只装 `stitch-design` 一个插件**，把 `generate-design` 和 `manage-design-system` 用熟。这两个覆盖了「生成 + 保持一致」的主线。
3. **然后装 `stitch-utilities`**，用 `design-md` 给你的项目生成一份 DESIGN.md。**这一步是所有后续一致性的地基** —— 有了它，`generate-design` 会自动少说很多话（因为令牌已在项目级生效）。
4. **再考虑 `stitch-build`**，从 `react-components` 开始。
5. **`stitch-loop` 放到最后** —— 它需要 DESIGN.md 和 SITE.md 两个前置文件，而且是最自动化的一个。
6. **接 Chrome DevTools MCP**（可选）。`stitch-loop` 的视觉验证能力依赖它。

## 排查：按现象定位

| 现象 | 先查这里 |
|---|---|
| OpenCode 加载不了技能 | skill 的 `name` 必须是小写 kebab-case 且与目录名一致；`stitch::` 形式的要先改名 |
| OpenCode 里工具名对不上 | 技能里写的是 `web_fetch` / `run_command`，OpenCode 用 `webfetch` / `bash` |
| 生成的界面跟已有页面风格不一致 | 项目上没有设计系统 → 先跑 `manage-design-system`；另外确认 `generate-design` 的提示里没有多余的色彩/字体指令 |
| 生成的屏幕覆盖了设计令牌 | 检查生成提示里是否混入了具体颜色/字体指令 —— 令牌已在项目级生效时不应再提 |
| 迁移代码到 Stitch 后只有一半 | 不能直接调 `upload-to-stitch`，必须走 `code-to-design` 三段链（HTML + 设计系统 + 资产） |
| 多轮建站循环中断 | 检查 `.stitch/next-prompt.md` 是否被写坏；`.stitch/DESIGN.md` 和 `.stitch/SITE.md` 是否存在 |
| MCP 工具名报错 | 工具名带前缀（`list_projects`、`generate_screen_from_text`、`edit_screens`），看 skill 里的说明 |
| 文档链接跳转不对 | 在同 host 下打开目标路径，如 `https://stitch.withgoogle.com/docs/learn/device-types/` |
| 装完发现缺技能 | 技能之间有相互依赖，选择性安装时要带上依赖项 |

## 参考

- 仓库：<https://github.com/google-labs-code/stitch-skills>
- Stitch MCP 配置：<https://stitch.withgoogle.com/docs/mcp/setup/>
- Agent Skills 开放标准：<https://agentskills.io>
- 本仓库其它相关文章：DESIGN.md 格式规范（`google-labs-code/design.md`）—— 讲的是规范本身的格式与校验，与本文的插件架构与循环机制是两件事
