---
title: "pbakaus/impeccable 拆解：当 Anthropic frontend-design 撞上 SaaS 模板同质化，46 条规则 + 23 个命令是怎么把 AI 拽回设计语言里的"
date: 2026-07-17T02:58:33+08:00
lastmod: 2026-07-17T02:58:33+08:00
draft: false
categories: ["技术笔记"]
tags: ["Impeccable", "Frontend Design", "AI Coding Agent", "Design System"]
description: "Impeccable 是 pbakaus 在 frontend-design 基础上扩展的设计语言 skill，47k+ stars，12 个 AI 编程工具通用，46 条 detector 规则 + 23 个命令 + live mode + hooks。"
weight: 1
slug: "pbakaus-impeccable-frontend-design-skill"
author: text-matrix
---

## 一句话判断

**Impeccable（[pbakaus/impeccable](https://github.com/pbakaus/impeccable)）是 Paul Bakaus 在 Anthropic frontend-design 基础上扩展的"AI 编程工具前端设计语言"skill，截至 2026-07 在 GitHub 上约 47k stars / 2.7k forks，Apache-2.0。** 它直接回应一个具体问题：**所有模型都在同一个 SaaS 模板集上训练，所以让 AI 写 UI 默认会得到 Inter + 紫蓝渐变 + cards-in-cards + 灰字配彩底 + 圆角图标块**。Impeccable 的解法不是又一个 prompt 模板，而是把工程化做到三层：

1. **46 条确定性 detector 规则**——无 LLM、无 API key，可在 CLI 和浏览器扩展里跑
2. **23 个 `/impeccable <command>` 命令**——和 AI 共享设计词汇
3. **provider-native hooks**——直接接进 Claude Code / Cursor / GitHub Copilot / Codex 的 hook manifest，把设计审查嵌入编辑流程本身

如果你正在做"AI 写出来的 UI 千篇一律"的工程治理，或者在多个 AI 编程工具之间维护一套设计系统，这篇文章值得完整读完。

---

## 系统地图

Impeccable 的真实结构不是"23 个命令的列表"，而是"安装 → 配置 → 命令 → 钩子 → live mode → 检测器"六层闭环：

```
┌──────────────────────────────────────────────────────────────────────┐
│  安装层 (Multi-provider installer)                                     │
│   npx impeccable install / update / link / detect                    │
│   5 种安装路径: CLI / Git Submodule / Plugin Marketplace / ZIP / 复制  │
│   12 个目标: Cursor / Claude Code / GitHub Copilot / Gemini CLI /    │
│            Codex / Grok Build / OpenCode / Pi / Kiro / Trae /        │
│            Rovo Dev / Qoder                                          │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────┐
│  配置层 (PRODUCT.md + DESIGN.md)                                        │
│   /impeccable init → 询问 brand vs product → 写入 design context       │
│   /impeccable document → 从现有代码反推 DESIGN.md                     │
│   共享工件: .impeccable/config.json + design.json + live/config.json  │
│            + critique/*.md (这些要进 git)                              │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────┐
│  命令层 (23 个共享命令)                                                 │
│   /impeccable craft / init / document / extract / shape /              │
│   critique / audit / polish / bolder / quieter / distill /            │
│   harden / onboard / animate / colorize / typeset / layout /          │
│   delight / overdrive / clarify / adapt / optimize / live             │
│   /impeccable pin <command> → 创建独立别名 (如 /audit)                 │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────┐
│  钩子层 (Provider-native hooks, 实时拦截)                                │
│   Claude Code:  .claude/settings.local.json → hook.mjs (after edit)   │
│   GitHub Copilot: .github/hooks/impeccable.json → hook.mjs (after)     │
│   Codex:        .codex/hooks.json → hook.mjs (after, 需 /hooks 批准)   │
│   Cursor:       .cursor/hooks.json → hook-before-edit.mjs (before)     │
│   拦截: 不影响不相关 hook, 损坏 manifest 立即中止, --force 备份替换    │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────┐
│  Live mode (浏览器内可视化迭代)                                          │
│   /impeccable live → 在浏览器里迭代组件变体                            │
│   共享工件: .impeccable/live/config.json                                │
│   临时工件: server.json / sessions/ / previews/ / annotations/ /       │
│            cache/ / *.png  (这些进 .gitignore)                         │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────┐
│  Detector 层 (46 条确定性规则 + LLM 评审)                                │
│   npx impeccable detect <path|url>                                     │
│   确定性规则无需 LLM 与 API key                                        │
│   /impeccable hooks → 共享 detector 配置                                │
│   调试: .impeccable/config.json hook.auditLog = path/to/log.ndjson    │
└──────────────────────────────────────────────────────────────────────┘
```

这张图最重要的一条路径：**"安装 → 配置 → 命令 / hooks → live mode → detector"** 是闭环的——`init` 写配置，`commands` 让 AI 按配置工作，`hooks` 在编辑时检测，`detect` 是命令式全量扫描，`live mode` 让迭代可视化。这条链路让 Impeccable 不只是"又一个 prompt 集"，而是一个**可装、可配、可钩、可检测、可迭代**的工程化设计治理系统。

---

## 边界与角色划分

把 Impeccable 拆成 5 组"不变项"，可以一次性回答它和 shadcn/ui / Tailwind / Material UI / Figma Tokens / Vercel v0 的差别：

| 维度 | Impeccable 的不变项 | 工程含义 |
|------|----------------------|---------|
| 形态 | Skill + 命令集，不是组件库 | 不强制引入组件库；不锁 UI 框架；不替代 shadcn/MUI |
| 检测 | 46 条确定性 detector 规则 | 不依赖 LLM 也能跑；可接入 CI；与 LLM-only critique 互补 |
| 工作单位 | `/impeccable <command>` 命令 | 共享设计词汇；不预设"prompt 应该长什么样" |
| 集成 | provider-native hooks | 直接嵌入 Claude Code / Cursor / Copilot / Codex 的工作流，不开新 UI |
| 输出 | DESIGN.md + design.json | 可读、可版本化、可评审；不是 hidden state |

要注意的几个边界：**Impeccable 不是设计系统**——它不提供 token / 组件库；**它不是 lint 工具**——它能做确定性 lint，但核心目标是"和 AI 共享设计语言"；**它不是 Figma 替代**——它的 design.json 是和 AI 沟通的中间格式，不是 Figma plugin。

---

## 关键机制

### 1. PRODUCT.md + DESIGN.md：把"设计语境"显式化

Impeccable 的第一步永远是 `/impeccable init`：

- 询问"是 brand 表面（marketing / landing / portfolio）还是 product 表面（app UI / dashboard / tool）"
- 写入 PRODUCT.md（产品 / 受众 / 品牌定位 / 声音）
- 可选写入 DESIGN.md（反 references / 颜色 / 字体 / 组件）

这两个文件是后续所有命令的"上下文"。`/impeccable document` 是反向版本——从已有项目代码反推 DESIGN.md，把"项目已经有的设计语言"显式化。

这条机制的工程含义：**设计决策不再藏在 AI 的 hidden context 里**，而是有可读、可审、可版本化的文件。

### 2. 23 个共享命令

23 个命令分成 3 组：

**元配置类**：

- `init` / `document` / `shape` —— 一次性 setup 或 plan
- `extract` —— 把可复用组件和 token 提到 design system

**评审与质检**：

- `audit` —— 技术质量检查（a11y / 性能 / 响应式）
- `critique` —— UX 设计评审（层级 / 清晰度 / 情感共鸣）
- `polish` —— 最终一遍设计系统对齐
- `harden` —— 错误处理 / i18n / 文本溢出 / 边界

**视觉调整**：

- `bolder` / `quieter` —— 放大 / 收敛设计强度
- `distill` —— 剥离到本质
- `animate` / `colorize` / `typeset` / `layout` —— 单一维度调整
- `delight` / `overdrive` —— 加入惊喜 / 技术炫技
- `clarify` —— UX 文案改进
- `adapt` —— 设备适配
- `optimize` —— 性能优化
- `craft` —— 完整 shape-then-build 流程

**Live 模式**：

- `live` —— 在浏览器里迭代元素变体

这套命令的精髓是**和 AI 共享一套设计词汇**——你说 `audit`，AI 知道要查 a11y / 性能 / 响应式；你说 `distill`，AI 知道要"剥离到本质"而不是"加东西"。这把"我和 AI 在谈设计"从模糊 prompt 变成精确动词。

### 3. 46 条确定性 detector 规则

这是 Impeccable 最工程化的部分。detector 是**确定性**的：

- 无需 LLM 调用
- 无需 API key
- 可以在 `npx impeccable detect src/` 或 `npx impeccable detect https://example.com`（Puppeteer）直接跑
- 在 Claude Code / Cursor / Copilot / Codex 的 hook 里也跑同一套

deterministic rules + LLM-only critique 是互补关系：

- 确定性规则回答"这段代码是不是用了 Inter 字体"
- LLM critique 回答"这个视觉层级是否清晰"

detector 配置通过 `.impeccable/config.json` 的 `detector` 段共享，`/impeccable hooks` 和 `npx impeccable detect` 都读这一份配置。

### 4. provider-native hooks：嵌入编辑流程

这是 Impeccable 和"23 个 prompt 命令"类工具的关键区别。每个 provider 的 hook 行为略有差异：

| Provider | Hook 文件 | 触发时机 | 行为 |
|---------|-----------|---------|------|
| Claude Code | `.claude/settings.local.json` | 编辑后 | 把发现写回 agent flow |
| GitHub Copilot | `.github/hooks/impeccable.json` | 编辑后 | 同上 |
| Codex | `.codex/hooks.json` | 编辑后 | 同上（需要 `/hooks` 手动批准） |
| Cursor | `.cursor/hooks.json` | 编辑前 | **拦截**坏写入，写不进去 |

Cursor 的"编辑前拦截"是最强形态——直接阻止坏设计落到文件里。Codex 的钩子需要用户在 `/hooks` 里批准一次（Codex 用 hook definition 做信任追踪，更新钩子定义可能要重新批准）。

**Installer 行为约束**：保留不相关 hook 条目；manifest 损坏立即中止；`--force` 备份损坏文件为 `.bak` 并替换。这条约束对"已有自定义 hook 的项目"很关键。

### 5. Live mode：浏览器内可视化迭代

`/impeccable live` 把 AI 写 UI 的工作流从"生成 → 看图 → 改 prompt"压缩成"浏览器内直接迭代变体"。共享工件 `.impeccable/live/config.json` 进 git，临时工件（server.json / sessions / previews / 截图）进 `.gitignore`。

这条机制的工程含义：**设计迭代不再需要反复 reload dev server**——AI 直接在浏览器里调组件、你看截图、给反馈。

### 6. 设计文件治理：哪些进 git 哪些不进

Impeccable 在 `.gitignore` 处理上做了细致的取舍。**共享工件进 git**：

- `.impeccable/config.json`（统一共享配置）
- `.impeccable/live/config.json`（live 模式框架 wiring）
- `.impeccable/design.json`（共享设计规格）
- `.impeccable/critique/*.md`（评审报告）

**临时工件进 .gitignore**：

- `.impeccable/config.local.json`（每开发者覆盖）
- `.impeccable/hook.cache.json` / `hook.pending.json`
- `.impeccable/*.png`（截图）
- `.impeccable/live/server.json` / `sessions/` / `previews/` / `annotations/` / `cache/` ...

这种"显式区分共享 / 临时"的设计让 monorepo 友好——patterns 是 unanchored 的，所以 `apps/web/.impeccable/` 这种嵌套项目结构不会被 anchored pattern 错过。

### 7. Codex / Gemini CLI / Cursor 的特殊步骤

README 明示了几个"必须手动做"的步骤，AI 装不了：

- **Codex**：装完后必须打开 `/hooks` 批准项目钩子
- **Gemini CLI**：必须 `npm i -g @google/gemini-cli@preview`，在 `/settings` 启用 Skills，再 `/skills list` 验证
- **Cursor**：必须切到 Nightly channel，启用 Agent Skills

这些"必须手动"是平台限制，不是 Impeccable 的缺陷；安装脚本会提示但不能代执行。

---

## 一个请求如何流过 Impeccable

下面以一个具体场景走一遍：在 Cursor 里 AI 写了一段 hero section，用户想让它既符合设计系统又不"AI 模板味"。

```
用户: "/impeccable audit the hero section"
        │
        ▼
Cursor 调起 /impeccable skill
        │
        ▼
Skill 读取 .impeccable/design.json + DESIGN.md
  - 知道品牌: brand 表面, voice "warm but precise", 颜色: #0A0A0A 主色
  - 字体: 不用 Inter, 不用 Arial
  - 反 references: 不要紫蓝渐变, 不要 cards-in-cards
        │
        ▼
audit 命令执行:
  Round 1: 读 hero section 当前代码
  Round 2: detector 规则扫描
    - "使用了 system-ui, fallback Inter"   ❌ (anti-pattern)
    - "primary button 用了 #6366F1"        ❌ (anti-pattern)
    - "headline 字号 32px, 副标题 16px"     ✓
  Round 3: LLM critique
    - "信息层级清楚, 但 CTA 与背景对比度偏低"
  Round 4: 输出 critique report → .impeccable/critique/hero-2026-07-17.md
        │
        ▼
Cursor hook (before-edit) 拦截:
  用户后续 AI 提议把 button color 改成 #6366F1 → hook 拒绝, 返回 detector 警告
        │
        ▼
用户: "/impeccable polish the hero"
        │
        ▼
polish 命令:
  - 用 design.json 的字体替代 Inter
  - 用 #0A0A0A 替代 #6366F1
  - 提高 CTA 对比度
  - 输出 diff → 用户 review → 接受
        │
        ▼
用户: "/impeccable live" 在浏览器里看 hero 变体
        │
        ▼
npx impeccable detect src/  (CI 步骤)
  - 全部 detector 通过 → 合并 PR
```

这个例子里关键看 4 件事：

1. **design.json 是 AI 的"设计系统手册"**——所有命令和 hook 都读这一份
2. **detector 是确定性的**——CI 可以跑，不用 LLM
3. **hook 在编辑时拦截**——Cursor 的 before-edit 模式是真正的"前置质量门"
4. **live mode 把迭代可视化**——浏览器内直接调，不开新工具

---

## 采用顺序与适用边界

### 推荐采用顺序

1. **`npx impeccable install`**——按提示选 provider / scope（项目 / 全局），不勾不需要的 provider
2. **`/impeccable init`**——先建立 PRODUCT.md + DESIGN.md，没有这一步命令没有"上下文"
3. **用 `/impeccable audit`** 跑一次现有代码——拿到第一份 critique 报告
4. **针对 critique 改几处**——验证命令是否真的理解你的 design.json
5. **启用 hook**——让 detector 在每次编辑时跑
6. **`/impeccable live`** 用于设计迭代——浏览器内可视化
7. **CI 集成 `npx impeccable detect`**——把设计治理做成强制门

### 适用边界

| 适合 | 不适合 |
|------|--------|
| 用 AI 编程工具（Cursor / Claude Code / Copilot / Codex）写 UI 的团队 | 不用 AI 编程工具的纯手写 UI 团队 |
| 有"AI 写出来的 UI 千篇一律"的具体痛感 | 还没有意识到"模型同质化"问题的项目 |
| 愿意维护 DESIGN.md / design.json 的团队 | 想要"全自动、不写配置"的工具 |
| 多 AI 编程工具并存（Cursor + Claude Code + Copilot 都要用） | 锁单一 provider 的场景（hooks 价值打折） |
| 设计系统需要持续治理（不是一次性 audit） | 一次性 audit 后就束之高阁 |
| 想要把设计审查嵌入开发流程 | 想要"专门的设计师 lint 工具" |

### 风险与未知项

- **需要手动完成的 provider 设置**：Codex 的 `/hooks` 批准、Cursor 的 Nightly channel + Agent Skills 启用、Gemini CLI 的 preview 版本——README 明示这些是平台限制，AI 装不了
- **detector 规则在演进**：46 条是 README 给的数字，规则集会增长；建议每月看一次 CHANGELOG 或 GitHub Releases
- **hook 拦截的边界**：Cursor 的 before-edit 模式会**直接拒绝写入**，其他 provider 是 after-edit 提示；如果团队不适应"被 hook 拒绝"，可能需要先关 hook 跑一遍 audit，再开 hook
- **monorepo 配置**：`.impeccable/` 可能落在 `apps/web/.impeccable/` 这种嵌套位置；`.gitignore` 用 unanchored patterns 是有意的，README 警告不要加 anchored patterns
- **已有自定义 hook 的项目**：installer 保留不相关条目，但 manifest 损坏会立即中止；`--force` 备份为 `.bak`，但仍需人审 `--force` 是否合适

---

## 一处延伸阅读

如果想继续深入：

- [pbakaus/impeccable 仓库](https://github.com/pbakaus/impeccable)——主仓库，README 的 "23 Commands" 表 + "Anti-Patterns" 段是快速了解设计语言的入口
- [impeccable.style 文档站](https://impeccable.style)——完整 hooks 文档 + 案例研究（Neo Mirai before/after）
- [npx impeccable CLI](https://www.npmjs.com/package/impeccable)——跟随 releases，star 包以便更新
- [Anthropic frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design)——Impeccable 的"前身"，理解它为什么"在 frontend-design 基础上扩展"必读
- [DEVELOP.md](docs/DEVELOP.md)——贡献者指南和构建说明
