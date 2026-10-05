---
title: "Archify 拆解：让 AI Agent 生成可验证架构图的 Skill"
slug: tt-a1i-archify-agent-skill-architecture-diagram-guide
github_repo: "tt-a1i/archify"
source_key: "gh:tt-a1i/archify"
date: 2026-07-11T02:50:00+08:00
lastmod: 2026-09-29T12:00:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Agent Skills", "Archify", "Mermaid", "AI 工具", "diagram"]
description: "按 Archify v3.0.1 拆解这个 73.9k star 的 agent skill：五种图类型、typed JSON IR 生成—校验—交付管线、bin/archify.mjs CLI、Architecture Delta 对比、更新检查的隐私边界，以及它与 Mermaid/Excalidraw 的真实关系（不是 Mermaid 主题，也不是画图编辑器）。"
---

# Archify 拆解：让 AI Agent 生成可验证架构图的 Skill

## 一句判断

Archify 常被介绍成"让 Claude 直接画架构图的 skill"。这个说法对，但只说对了一半：它是"skill 提示词 + 校验 CLI + 自包含 HTML 查看器"的组合，不只是一份提示词。自然语言进来，先被整理成一份带 schema 的 typed JSON IR，通过原子校验后才渲染成单个 HTML 交付；拿到图的人可以对节点溯源、沿路径回溯，配上深/浅双主题和多种导出方式带走。

它的自我定位值得先看清楚——README 原话：*it is not a general-purpose drawing editor or a Mermaid theme*。它既不是画布工具，也不是 Mermaid 的换皮主题，而是一套从"技术意图"到"可沟通产物"的完整管线。理解这一点，才不会拿它干本不属于它的活。

本文以 v3.0.1 为口径：安装、五种图类型、生成—校验—交付管线、`bin/archify.mjs` CLI、Architecture Delta、更新检查的隐私模型，最后给出适用边界与自测题。

## 项目坐标

以下数字为 2026-09-29 GitHub API 读数与仓库 README（`main` 分支）记载。

| 维度 | 数据 |
|------|------|
| 仓库 | [tt-a1i/archify](https://github.com/tt-a1i/archify) |
| Stars | **73,882**（2026-09-29 GitHub API 读数） |
| Forks | 4,977 |
| 主语言 | JavaScript（CLI 为 Node 脚本） |
| License | MIT |
| 稳定版 | **v3.0.1**（2026-09-28，见 CHANGELOG） |
| 建仓 | 2026-04-15 |
| 主页 | https://tt-a1i.github.io/archify/ |
| 形态 | Agent Skill + Node CLI + 生成式 HTML 查看器 |
| 兼容代理 | Cursor、Claude Code、Codex CLI、opencode（另有社区 Hermes / DeepSeek Harness 集成） |

README 记载：作者于 2026-09-01 公开榜单截图，称其登顶过 **GitHub Trending 全语言周榜第一**；并获得 QbitAI 的专题报道与开发者访谈。这一条源自作者发布的内容，可作为项目热度参考，不必当作第三方独立评测。

## 它解决什么问题

传统"AI 画架构图"的路径多半靠一段 prompt 让模型直接甩出一张 Mermaid 或一段 HTML。痛点不在"图能不能出来"，而在三点：

- **没有中间产物**：一次生成到最终图之间没有可复核、可改哪补哪的源，改一处等于重来；
- **不可验证**：模型说"这是你的系统架构"，但没有证据链，对错全凭肉眼；
- **交付碎片化**：图散在代码/画布里，导出、复制、分享各来一套流程。

Archify 把这三件事一次收口：**typed JSON IR 作源**（可复核可迭代），**原子校验后才交付**（不过校验不产出，失败给修复回执），**最终物是单个自包含 HTML**（双击即开、可交互、可导出，发给别人不依赖安装）。典型示例如下——直接从描述开始，无需仓库：

```text
Use Archify to draw: Browser -> API -> Redis cache -> PostgreSQL fallback.
```

或者让它读一个仓库生成"有源"的架构图：

```text
Analyze this repository, then use archify to create a high-level runtime
architecture diagram. Show 8–12 core components, one primary path,
external dependencies, and trust boundaries.
Put supporting detail in cards instead of adding more edges.
```

## 五种图类型

不只是架构图。v3.0.1 支持五类，各自适配的问题不同（下表取自 README）：

| 类型 | 最佳用途 | prompt 里该给的 |
|------|----------|-----------------|
| **Architecture** | 组件、服务、存储、信任边界 | 范围、核心组件、主路径 |
| **Workflow** | CI/CD、审批、工具调用、runbook | 参与者、顺序、分支、异常 |
| **Sequence** | API 调用、缓存回退、鉴权、异步链路 | 调用方、被调方、返回、时序 |
| **Data Flow** | 管道、血缘、PII、消费者 | 来源、转换、存储、边界 |
| **Lifecycle** | 状态、重试、等待、终态 | 状态、事件、重试与取消路径 |

架构图还带一个 `deployment-ownership` 可选剖面：当作者未声明归属、区域、私有库范围或具名跨越时，它**fail closed**——不会凭空推断，也不去探测真实基础设施。

不确定选哪种？官方提供图形化场景引导（guide.html），或直接用零依赖 CLI 帮我选：

```bash
node archify/bin/archify.mjs guide "Show an API request with Redis cache miss"
node archify/bin/archify.mjs guide "Map Kafka topics, consumer groups, replay, and DLQ" --json
```

## 输出契约：一个自包含的 HTML

交付物是**单文件自包含 HTML**：数据、交互、样式都在这一个文件里，离线双击即开。查看器原生支持：

- **主题切换**：深色 / 浅色一键切换；
- **交互检查**：按语义节点聚焦（`/`）、沿作者声明的上/下游追溯（focus 节点后 Upstream / Downstream）、探测一条有向路径（`R` / `PATH`）、角色两两对比（`L` / `LENS`）、雷达总览（`M` / `MAP`）、演示模式（`F`）；
- **共享位标识**：URL 可携带 `#focus=<id>`、`#focus=<id>&reach=upstream|downstream`、`#relation=<id>`、`#route=<source>~<target>`、`#lens=<kind>~<kind>`，稳定链接可直接恢复视图；
- **导出**：复制 PNG 到剪贴板、下载静态/动态格式；追溯一条路径后 `Export → Route Share Card` 可导出 1200×630 的分享卡（保留全图作上下文）；`Reach Share Card` 同理记录可达读数。

"可验证"不只是口号，README 的工程承诺里有两条直接对应：**truthful interaction**——聚焦与路径追溯复用作者声明的节点和关系，不发明拓扑、不声称运行时影响；**source evidence, only when requested**——仅当用户要求时，架构节点才标 `SRC n`，并打开锚定到**单个公开提交**的 Git 文件和行区间，普通图不带来源。

## 工作流：生成 — 校验 — 预览 — 交付 — 迭代

Archify 把一次出图拆成五步（Preview 可选），每步都有明确产物：

| 步骤 | 发生了什么 |
|------|-----------|
| **Generate** | 代理把自然语言描述整理成一份带 schema 的 **typed JSON IR**（可复现的源） |
| **Validate** | 内置校验器与布局规则检查源；失败处以机器可读 JSON 指出可修复项 |
| **Preview**（可选） | 仅回环的桌面会话监视一个 JSON，只刷新通过校验的版本，失败时保留上一个合格产物 |
| **Deliver** | 在同目录生成候选并复检，只有通过的产物才**原子替换**目标，可选 `--open` 打开该文件 |
| **Iterate** | 代理更新源，无关结构保持不变 |

对应的 CLI（仓库内 `archify/bin/archify.mjs`，先 `cd archify` 再调 `node bin/archify.mjs`）：

```bash
cd archify
node bin/archify.mjs doctor                                  # 环境自检
node bin/archify.mjs demo /tmp/archify-demo                  # 生成示例
node bin/archify.mjs guide "Show CI/CD checks, approval, deploy, and rollback"
node bin/archify.mjs validate workflow examples/agent-tool-call.workflow.json --quality showcase --json
node bin/archify.mjs preview workflow examples/agent-tool-call.workflow.json /tmp/workflow.html --quality showcase
node bin/archify.mjs deliver workflow examples/agent-tool-call.workflow.json /tmp/workflow.html --quality showcase --open --json
```

把前文的 cache miss 例子放进去走一遍：把 "Browser -> API -> Redis cache -> PostgreSQL fallback" 交给代理，它先生成一份 architecture 类型的 JSON IR（Generate）；校验器检查 schema、布局、HTML/SVG、路径与 label 间距，全部通过才放行（Validate）；同目录渲染候选并复检，原子替换目标文件（Deliver）；你在聊天里补一句 "Add authentication"，代理只改源 JSON 里受影响的部分，无关结构不动（Iterate）。改图因此变成改一份可复现的源，而不是重画一张图。

三处值得记住的边界：

- **失败给回执，不是堆栈**。`validate --json` / `deliver --json` 失败时输出一个 JSON 对象，内含稳定的规则码、针对的具体对象、测量证据，以及**仅受支持**的修复控制项（`diagnostics[].subject.supportedFixes`）。建议只采纳这些受支持修复，并在 Skill 规定的两轮修正内完成；人工视觉复核仍是独立一步。
- **preview 是显式的回环模式**：只监视一个 JSON、跑在随机 `127.0.0.1` 端口、失败时保留上一个已验证产物、`Ctrl-C` 停止、不向生成物注入任何额外运行时。测试或手动开 URL 用 `--no-open`。
- **CLI 零依赖**：`archify/package.json` 没有 `dependencies`，只有构建期才用到的 `devDependencies`，Node ≥18 即可直接跑。

这套设计落在 README 的工程师理念上：*layout judgment over generic auto-layout*——布局由代理判断层级/间距/路由/主次，共享的自动端点确定性地散开，而不是把箭头堆到同一个中点，很多"AI 画得乱"的问题正出在这里；*typed JSON IR* 让每个渲染后端都有可复现源；*truthful interaction* 保证交互复用的是作者拓扑而非自造；*portable by default* 让导出始终是全图、不含临时查看器状态。

### Architecture Delta：可复核的"改了什么"

面向设计评审/PR 评审，v3.0.1 提供**架构对比**：校验通过后的 Before / Delta / After 三张快照，配一份机器回执。选择某个作者化改动，或播放一次有限的、仅查看端的 Review——它不推断影响、风险或合并安全性。

```bash
node archify/bin/archify.mjs compare architecture base.json head.json architecture-delta.html --json
```

## 安装与更新检查

安装走 skills 生态：

```bash
# 全局安装
npx skills add tt-a1i/archify -g

# 显式、非交互的 Cursor 安装
npx -y skills add tt-a1i/archify --skill archify --agent cursor --global --copy --yes

# 不安装，临时试一次
npx skills use tt-a1i/archify@archify --agent codex
```

落到哪个目录取决于代理（README 表格）：Claude Code 是 `~/.claude/skills/` 或项目 `.claude/skills/`；Codex CLI 是 `~/.agents/skills/` 或 `.agents/skills/`；opencode 是 `~/.config/opencode/skills/`、`.opencode/skills/` 或 `.agents/skills/`；Claude.ai 与 Project Knowledge 则上传 `archify.zip`。另有两个社区自维护的 opt-in 集成（README 均声明非官方产品、无遥测）：Hermes Agent 用 `hermes skills install skills-sh/tt-a1i/archify/archify -y`；DeepSeek Harness 用 `dsh plugin --profile web add @tt-a1i/archify-dsh@0.1.0`。

值得单独说清的是**更新检查的隐私边界**：Archify 可能向固定清单发出 GET，**只**用于显示一个可选的更新提醒；它不下载也不安装更新。成功检查约每 24 小时（±20%）一次，活跃使用时失败会在 6 小时后再隔 24 小时重试。服务器只见普通 HTTP 元数据（IP 与时间），**收不到**版本、代理、项目数据、prompt、账号/设备 ID 或 ETag；是否更新、何时更新由你决定。v3.0.1 起提醒出现在每个任务的最终回复里，升级、或对某个版本选择暂缓（7 天）/忽略后不再重复；检查慢或离线都不会阻塞出图交付。`ARCHIFY_UPDATE_CHECK_DISABLED=1` 可彻底关掉网络请求与提醒写入。这条对"评估第三方 skill 是否值得接入"是关键信息。

## 与 Mermaid / Excalidraw 的真实关系

网上不少介绍把 Archify 说成"更好的 Mermaid"，这个说法要拆开看。README 对边界讲得很直接：**自动 Mermaid 解析、通用自动布局、托管分享、所见即所得编辑，都在"当前范围之外"**。它不是 Mermaid 主题，不负责把既有 Mermaid 代码美化；它从描述/仓库出发，产出的是自己的自包含 HTML。

| 维度 | Mermaid | Excalidraw / draw.io | Archify |
|------|---------|----------------------|---------|
| 交互方式 | DSL 代码 | 鼠标拖拽 | 自然语言（agent 代劳） |
| 中间源 | Mermaid 源码 | 画布文件 | typed JSON IR |
| 可验证性 | 无 | 无 | 校验回执 + 可选源码锚定 |
| 产出 | 需渲染器 | 文件/格式导出 | 单文件自包含 HTML |
| 定位 | 代码即图 | 人画图 | 给 agent 用的产物管线 |

一句话：Mermaid 是"用代码描述图"，Excalidraw 是"人手动画图"，Archify 是"让 agent 从描述出发、产出可验证且可直接分享的图"。三者更多是互补而非取代——已有 Mermaid 库想统一风格，或者需要人工精修画布，仍各有其位。

## 适用边界

**适合**：技术文档/README/Confluence 的示意图、设计评审与 PR 评审的"改了什么"对比、内部架构方案沟通、教学材料、需要"有源可考"的团队架构图。

**先放下**：

- 已有成熟的 Mermaid 工作流，只想换个出图风格——那不是 Archify 的主场景（它不做 Mermaid 解析）；
- 需要所见即所得地手动拖拽精修——用 Excalidraw / draw.io / Figma；
- 需要托管在线分享与多人实时协作——README 明说托管分享在范围之外；
- 极复杂的图（几十上百个节点）：它服务于"清晰传达技术意图"，不是无限画布的绘图编辑器。

## 常见问题与排查

| 现象/问题 | 说明 |
|-----------|------|
| 校验失败 | 看 `validate --json` 的稳定规则码 + `supportedFixes`，只采纳受支持修复，在 Skill 的两轮修正内完成 |
| 交付时想看预览又不想被打断 | 用 `preview`（回环模式），失败自动保留上一个合格产物；测试用 `--no-open` |
| 想完全离线 | 设 `ARCHIFY_UPDATE_CHECK_DISABLED=1`，关闭更新检查的网络与提醒写入 |
| 图要不要带源码证据 | 仅在需要时要求 `Evidence-backed`，节点会标 `SRC n` 并锚定单个公开提交；不需要时保持无源 |
| 语言本地化 | `meta.locale` 只本地化界面文案（页面标题、图例、状态/错误、无障碍标注），不碰作者内容；内置 `en`/`zh-CN`；其余语言（如 `es`）需 `meta.translations` 提供词条，缺词条的键回退英文并在 stderr 声明 |

## 自测题

**1. Archify 的中间产物是什么，为什么它不是直接把 HTML 甩给模型就完事？**

<details>
<summary>参考答案</summary>

中间产物是 **typed JSON IR**——一份带 schema、可复制、可复现的源。直接甩 HTML 的问题在于：改一处要重来、无法校验、无证据链。JSON IR 让"生成→校验→交付→迭代"都有抓手，代理改源而无关结构保持稳定。
</details>

**2. `validate` / `deliver` 失败时，推荐怎么处理？**

<details>
<summary>参考答案</summary>

读 `--json` 输出里的稳定规则码、所针对的对象与测量证据，只采纳 `supportedFixes` 列出的受支持修复，在 Skill 规定两轮修正内完成；人工视觉复核仍是独立一步。不要直接堆一个无结构的 Node 错误或盲目重试。
</details>

**3. 更新检查会偷偷上传我吗？**

<details>
<summary>参考答案</summary>

不会。它只对固定清单发 GET 用于显示可选提醒，不下载不安装；服务器只见普通 HTTP 元数据（IP、时间），收不到版本/代理/项目/prompt/账号/设备 ID/ETag。可 `ARCHIFY_UPDATE_CHECK_DISABLED=1` 关闭。
</details>

**4. Archify 能替代 Mermaid 吗？**

<details>
<summary>参考答案</summary>

不能直接替代。README 明确 Mermaid 自动解析在范围之外，它也不是 Mermaid 主题。已用 Mermaid 的存量工作流，需要的是风格统一或人工精修，那是另一类工具的事。
</details>

**5. 聚焦、路径追溯这些交互会不会造假拓扑？**

<details>
<summary>参考答案</summary>

设计约束是 "truthful interaction"：聚焦与路径追溯复用作者声明的节点和关系，不发明拓扑、不声称运行时影响；只有要求时可加源码锚定（`SRC n`）。校验也保证交付前 schema/布局/HTML/SVG/路径/label-to-route 全部通过。
</details>

## 资料口径

本文事实口径与版本锚点：

- 项目数据（stars/forks/语言/建仓日期/LICENSE）为 **2026-09-29 GitHub API 读数**；稳定版 `v3.0.1` 与发布日期（2026-09-28）来自 README 徽章与 CHANGELOG。
- 功能描述（五种图类型、五步管线、CLI 命令、`--json` 修复回执、Architecture Delta、更新检查隐私、范围外声明、source evidence、`meta.locale`）均来自 `main` 分支 README 与 CHANGELOG 原文，未做超出原文的推断；本文未在本地实际运行 CLI，所有命令与行为均为文档转述，使用前请自行复核。
- "GitHub Trending 全语言周榜第一""QbitAI 报道/访谈"为 README 转述作者发布内容，作为热度参考而非独立评测，未单独复核榜单快照。
- 使用前请以当时 main 分支为准；项目迭代较快，v3 的 API 细节可能在你读到时已变化。

## 参考资源

- 仓库：<https://github.com/tt-a1i/archify>
- 在线画廊（Proof Lab，11 个已检入场景）：<https://tt-a1i.github.io/archify/gallery.html>
- 场景引导：<https://tt-a1i.github.io/archify/guide.html>
- 完整生成/查看器契约：仓库 `archify/SKILL.md`
- Schema 参考：仓库 `archify/schemas/README.md`
- 变更记录：仓库 `CHANGELOG.md`
- 路线图：仓库 `ROADMAP.md`
- 作者动态：<https://x.com/t20000622yy>