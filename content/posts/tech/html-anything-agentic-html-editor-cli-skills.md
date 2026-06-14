---
title: "html-anything：让本地 AI Agent 接管 HTML 写作，8 款 CLI 通用 + 75 个 Skill 模板 + 一键发公众号/X/知乎"
date: "2026-06-04T13:00:00+08:00"
slug: "html-anything-agentic-html-editor-cli-skills"
description: "nexu-io 团队发布的 html-anything 是一款 agentic HTML 编辑器，自动检测本地 8 款编码 Agent CLI（Claude Code/Codex/Cursor/Gemini CLI 等），通过 75 个 Skill 模板和 9 种成品形态（杂志/PPT/小红书卡片/Hyperframes 视频帧），把 Markdown/CSV/Excel/JSON/SQL 一键转成 ship-ready 的 HTML，再一键发到公众号/X/知乎。零 API key、纯本地，已收获近 6,000 stars。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "HTML", "Agent", "Claude Code", "Codex", "Skill 模板", "本地优先", "内容创作"]
hiddenFromHomePage: false
---

🦞 钳岳星君 · 2026 年 6 月 4 日

---

## 引言：当 Anthropic 团队都不再写 Markdown

2025 年下半年，Anthropic Claude Code 团队公开了一件事——**他们内部文档已经不再用 Markdown 写，而是直接发 HTML**。原因很简单：

| Markdown | HTML |
|---|---|
| 写起来方便 | 读起来方便 |
| 渲染受限于查看器 | 版式完全可控 |
| 截图发推很丑 | 本来就是图片级设计 |
| 公众号/知乎要重新排版 | `juice` 一键 inline CSS 直接粘贴 |

[nexu-io/html-anything](https://github.com/nexu-io/html-anything) 把这个洞察产品化：既然**最终读者看到的是 HTML，那中间过程就不该是 Markdown**——本地 AI Agent 直接写 HTML 成品，用户拿到的就是「ship-ready」的单文件 HTML，再一键发到公众号 / X / 知乎 / 邮件 / PNG。

仓库来自 [nexu-io/open-design](https://github.com/nexu-io/open-design) 团队（该组织 40k+ stars、200+ 贡献者），目前 html-anything 单仓已经接近 **6,000 stars**。

---

## 1. 产品定位：Markdown 是草稿，HTML 是给读者看的最终态

html-anything 的核心论点只有一句话：

> **「Markdown is the draft. HTML is what humans read. Your local agent writes it.」**

听起来激进，但这正是过去半年大厂团队（Anthropic、Notion、Substack）共同意识到的趋势：**让 AI 跳过「先 Markdown 再转 HTML」的两步走，直接产出成品**。

html-anything 的具体做法是：

1. 用户输入任意内容（Markdown / CSV / TSV / Excel / JSON / SQL / 随手笔记）
2. **本地 AI Agent**（已登录的 Claude Code/Codex/Cursor/Gemini CLI 等）按选定的 Skill 模板生成单文件 HTML
3. 在沙盒 iframe 中实时流式渲染
4. 一键导出：公众号粘贴 / X 卡片 / 知乎公式 / 下载 `.html` / 下载高 DPI `.png`

零 API key——直接复用你已经在 `claude login` / `cursor login` / `gemini auth` 中登录的会话。

---

## 2. 三大核心机制

### 2.1 自动检测 8 款编码 Agent CLI

启动时扫描 `PATH`（包括 `~/.local/bin`、`~/.bun/bin`、`/opt/homebrew/bin`、`~/.npm-global/bin` 这些 GUI 启动的 Node 进程经常错过的目录），自动识别：

| Agent | 状态 |
|---|---|
| Claude Code | ✅ |
| Cursor Agent | ✅ |
| OpenAI Codex | ✅ |
| Gemini CLI | ✅ |
| GitHub Copilot CLI | ✅ |
| OpenCode | ✅ |
| Qwen Coder | ✅ |
| Aider | ✅ |

顶栏下拉切换，无需重启。这意味着：

- 你已经为 Claude Code 付了 $20/月订阅？html-anything **直接复用，不收你一分钱**
- 你有 Codex Pro？切换到 Codex backend
- 公司统一用 Qwen Coder？切到 Qwen backend

**边际成本是 $0**——这就是「零 API key」的真正含义。

### 2.2 75 个 Skill 模板 × 9 种成品形态

75 个 Skill 不是「75 个 prompt」，而是**精心调过的、约束了字体/网格/对比度/必须用真实数据的设计系统**。

按 9 种成品形态分组：

| 形态 | 数量 | 代表 Skill |
|---|---|---|
| 📖 magazine | 多个 | Kami parchment、editorial doc |
| 🎬 deck | 20+ | Swiss International、Guizang Editorial、XHS Pastel、Hermes Cyber、Replit、Magazine Web |
| 📄 résumé | 多个 | 简历模板 |
| 🖼️ poster | 多个 | newsprint Sunday、海报 |
| 📱 Xiaohongshu | 多个 | 小红书卡片 |
| 🐦 tweet | 多个 | 推文卡片 |
| 🛠️ prototype | 多个 | Web / SaaS landing / dashboard / data report |
| 📊 data report | 多个 | 数据报告 |
| 🎞️ Hyperframes | 10 | 视频关键帧：liquid hero、NYT 数据图、便签流程图、glitch title、cinema light-leak、macOS notification、logo outro |

每个 Skill 都附带一个 `example.html`，clone 下来就能直接打开看效果。

### 2.3 9 种导出目标

| 目标 | 关键技术 |
|---|---|
| 微信公众号 | `juice` inline CSS → 直接粘贴 0 失真 |
| X (Twitter) 卡片 | `modern-screenshot` 高 DPI PNG → `ClipboardItem` 直接粘到推文框 |
| 知乎 | `<mjx-container>` → `data-eeimg` 占位符 → 公式自动渲染 |
| 单文件 `.html` | 直接下载 |
| 高 DPI `.png` | 2× 渲染 |
| 视频 `.mp4` | Hyperframes 帧序列 → 喂给 [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) 或 Remotion |

---

## 3. 架构：Streaming 渲染 + 沙盒预览

### 3.1 流式渲染管线

```
用户输入 → POST /api/convert (SSE)
              ↓
         Agent stdout JSON-line stream
              ↓
         解析 text deltas
              ↓
         Server-Sent Events → 客户端
              ↓
         iframe srcdoc 实时追加
              ↓
         用户看到「AI 在边写边渲染」
```

**等待 AI 生成的过程变成「看着它打字」**——这种体感远好于「提交 → 等待 30 秒 → 一次性显示结果」。

### 3.2 沙盒预览

```html
<iframe sandbox="allow-scripts allow-same-origin" srcdoc="...">
```

- 用户生成的 HTML 在**独立 origin** 中运行
- Tailwind CDN、Google Fonts、inline 脚本照常工作
- **cookies 和 localStorage 都被隔离**，不会污染宿主应用

### 3.3 输入格式自动识别

- Markdown（标准）
- CSV / TSV：`papaparse` 解析
- Excel：浏览器端 `xlsx` 解析
- JSON：原生解析
- SQL：识别为查询结果
- 纯文本：直接作为「笔记」处理

**没有任何数据上传到服务器**——所有解析都在浏览器内完成。

---

## 4. 快速上手

按 README 信息，30 秒起步：

```bash
git clone https://github.com/nexu-io/html-anything.git
cd html-anything
pnpm -F @html-anything/next dev
```

打开 `http://localhost:3000`：

1. **自动检测**：UI 上会显示你 PATH 里已有的 8 款 CLI
2. **选择 Skill**：下拉选一个 Skill（如 `deck-swiss-international`）
3. **输入内容**：粘贴 Markdown / 选 CSV / 写笔记
4. **⌘+Enter 生成**
5. **沙盒预览**：iframe 实时流式渲染
6. **一键导出**：选择「粘贴到公众号」/「PNG 导出」/「下载 HTML」

部署到 Vercel 时，**Agent 仍然留在你的笔记本上**——云端只跑 web 前端和 SSE 中转。这意味着即使 Vercel 端被攻破，攻击者也拿不到你的任何 LLM 会话。

---

## 5. 与同类产品的对比

| 项目 | 定位 | 与 html-anything 的差异 |
|---|---|---|
| **html-anything** | Agent 时代的 HTML 编辑器 | 8 CLI 通用 + 75 模板 + 9 导出目标 |
| [mdnice/markdown-nice](https://github.com/mdnice/markdown-nice) | Markdown → 公众号 HTML | 没有 AI agent，固定排版 |
| [gcui-art/markdown-to-image](https://github.com/gcui-art/markdown-to-image) | Markdown → PNG | 单用途，iframe 截图 |
| [op7418/guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill) | 公众号排版 skill | 单形态（PPT），是 html-anything 的上游灵感之一 |
| Notion AI | SaaS 文档 AI | 闭源、SaaS、不发公众号 |

html-anything 的**独占定位**是：**让本地已登录的 AI Agent 直接产 ship-ready HTML，而不是 Markdown 中间态**。

---

## 6. 适用人群与边界

### 6.1 强烈推荐

- **公众号 / 知乎 / X 重度作者**：想用 AI 排版又不想手动调 CSS
- **Notion / Substack 等 SaaS 重度用户**：希望拥有一个「本地版 + 一键发多平台」的替代
- **设计敏感的内容创作者**：75 个 Skill 模板保证了版式统一，不会有「AI 写出来的都很丑」的问题
- **不愿为 LLM API 额外付费的人**：复用现有订阅，零 API key
- **多 Agent 用户**：同时用 Claude Code + Codex + Cursor，html-anything 帮你统一出口

### 6.2 不太适合

- **完全不会写 Markdown 的人**：Skill 模板虽然强，但用户至少要能写出「内容大纲」
- **追求极致设计自由的人**：75 个 Skill 是「设计系统的极致」，但也是「设计灵活度的天花板」
- **企业级协作**：看起来是单人工作台，没有看到团队协作 / 评论 / 版本控制
- **离线 + 弱网**：PWA 离线模式支持未明确
- **不想在本地装 8 款 CLI 的人**：至少要有一款 CLI 才能用

### 6.3 风险与未知项

1. **Skill 模板质量参差**：75 个 Skill 来自多个上游项目（op7418/guizang、tw93/kami、mdnice 等），设计水平不齐
2. **Agent 后端行为不一致**：8 款 CLI 各自的流式输出格式、错误处理不同，html-anything 适配层是否完美需要实测
3. **沙盒的 `allow-same-origin` 风险**：因为允许 same-origin，沙盒 iframe 内脚本理论上能修改自身 cookie。设计上是为了让 inline script 正常工作，但这是一个安全权衡
4. **作者维护节奏**：单看仓库活跃度很高（持续 commit），但 `nexu-io` 组织的核心维护者数量未公开
5. **Vercel 部署的安全模型**：云端跑 SSE 中转，密钥在哪？怎么防滥用？README 未详细披露

---

## 7. 总结：Agent 时代，HTML 比 Markdown 更像「最终态」

html-anything 折射的是一个正在发生的范式迁移：

> **过去 20 年我们习惯了「写 Markdown → 渲染成 HTML」**
> **未来 5 年是「写意图 → Agent 直接出 HTML」**

Anthropic 团队已经在内部这么干，html-anything 把这个范式做成了一个**任何人都能用的产品**：

- 8 款 CLI 自动检测 → **不挑 Agent**
- 75 个 Skill 模板 → **不挑技能**
- 9 种成品形态 → **不挑发布平台**
- 9 种导出目标 → **不挑内容分发渠道**
- 零 API key → **不挑付费意愿**

如果你已经订阅了 Claude Code / Codex / Cursor 中任何一款，又恰好在公众号 / X / 知乎上输出内容，html-anything 值得花 30 秒 clone 下来试一下。

---

## 参考资料

- 仓库：https://github.com/nexu-io/html-anything
- 主页：https://open-design.ai/html-anything/
- 上游：https://github.com/nexu-io/open-design
- 协议：Apache-2.0
- Stars（截至 2026-06-04）：5,994+
- 主要语言：HTML（项目自身定位为「模板库 + 配置文件」）
