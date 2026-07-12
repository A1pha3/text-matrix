---
title: "Hallmark 项目导读：用反 AI 味规则让 Claude Code、Cursor、Codex 生成不一致的网页"
slug: nutlope-hallmark-anti-ai-slop-design-skill
date: 2026-07-13T03:03:14+08:00
lastmod: 2026-07-13T03:03:14+08:00
draft: false
categories: ["技术笔记"]
tags: ["AI", "设计", "Claude Code", "skill", "前端"]
description: "Hallmark 是 Together AI 出品的反 AI 同质化设计 skill（Claude Code / Cursor / Codex 通用）。本文解读其规则集结构与 4 动词。"
---

# Hallmark 项目导读：用反 AI 味规则让 Claude Code、Cursor、Codex 生成不一致的网页

## 核心判断

Hallmark 解决的不是"让 AI 设计出好看的网页"的问题，而是"让 AI 设计出**不被一眼识破为 AI 设计**的网页"的问题。它的做法是**给 AI 写一套反 on-distribution（反默认分布）的设计规则集**——20 个主题、57 条 slop-test 闸门、Custom 分支的元规则——配合四个动词接口（默认创建、`audit`、`redesign`、`study`），把"如何让 AI 别生成千篇一律的渐变粉紫 + glassmorphism + 过度圆角"这件事变成可安装的 skill。从这个角度看它的规则结构，能立刻明白它和普通 AI 设计 prompt 之间的边界。

## 项目坐标

| 维度 | 数据 |
|------|------|
| 仓库 | Nutlope/hallmark |
| Stars | 约 4.1k（截至 2026-07）|
| 主语言 | CSS（核心）+ Markdown（规则 + 文档）|
| License | MIT |
| 引擎适配 | Claude Code / Cursor / Codex（同一份 skill） |
| 出品方 | Together AI |
| 演示站 | usehallmark.com（含 20 个主题示例 + Custom 分支示例） |

> Hallmark 不是新做的"前端库"，也不是"设计 token 系统"，它本质是**一份带主题规则的 SKILL.md 套件**，可以装进 Claude Code 的 skill 目录、Cursor 的 rule 文件、Codex 的 skill 目录，复用同一组规则。它的实际"产物"是 demo 站里那些手工 + AI 协作生成的网页。

## 范式：把反 AI 味做成可复用的规则集

### AI 同质化是怎么发生的

当前 LLM（不管是 GPT、Claude、Gemini 还是开源）在"帮我设计一个 SaaS 主页" 这种 prompt 上，几乎完全收敛到同一组视觉范式：

- 渐变粉紫色 / 深空蓝玻璃拟物
- 过大的圆角 + 内阴影
- 大字 hero + 居中 CTA + 三栏 features
- blob shape / mesh gradient / aurora 背景
- emoji 当 icon
- "Empower / Seamlessly / Unlock / Elevate" 这种动词堆叠

这不是巧合。训练数据里网页设计案例大部分是 Bootstrap、Tailwind UI、shadcn 风格的产物 + 大量 SaaS 落地页模板，导致模型在生成新页面时拉到的"最近的模板"高度集中。要让输出偏离这个分布，需要的不是更强的模型，而是**显式告诉模型不要拉那一类模板**——这正是 Hallmark 的规则集。

### Hallmark 的 4 个动词

| 动词 | 触发条件 | 行为 |
|------|----------|------|
| **(default)** | 你直接说"做一个 X 网站" | skill 自动选主题 + macrostructure（宏观结构）、应用规则集、过 slop-test 闸门才交付 |
| `hallmark audit <target>` | 想检查已有代码 | 出 punch list（反模式清单），不修改代码 |
| `hallmark redesign <target>` | 想保留内容但换风格 | 复用原有 copy + IA + 品牌，重建不同的 macrostructure + theme |
| `hallmark study <screenshot | URL>` | 想从一个"你喜欢的设计"反向抽取风格 | 抽取 DNA（macrostructure、type-pairing、colour anchor），**主动拒绝像素级克隆与付费模板**，可选输出一个可携带的 `design.md` 让别的 AI 工具接手 |

四个动词的边界很清晰：**默认动词负责"创造"，audit 负责"测量"，redesign 负责"复用"，study 负责"传递"**。这种动词切分方式对应"create / inspect / modify / analyze"的认知四象限，对终端用户的提示工程门槛很低。

## 系统地图：20 个主题 + 57 条 slop-test + Custom 分支

| 层 | 位置 | 数量 | 作用 |
|----|------|------|------|
| 主入口 | `skills/hallmark/SKILL.md` | 1 套 | 主体规则：什么时候选什么主题，怎么过 slop-test |
| 主题清单 | `skills/hallmark/references/*.md` | 20 个 | Hum / Cobalt / Carnival / Lumen / Garden / Riso / Custom 等 |
| 闸门 | 内嵌在主规则 | 57 条 | "不能出现的视觉/排版/词汇" 反模式清单 |
| 自检段 | 主规则内 | 1 段 | pre-emit self-critique（出发前最后一遍自评） |
| Custom 协议 | `skills/hallmark/references/custom-theme.md` | 1 个 | 创意 brief 的兜底分支 |
| 样例网站 | `site/_tests/`（20+ 个） | 20+ | 演示站原始 HTML + CSS，每个 HTML 文件顶部 stamp macrostructure |
| 文档 | `docs/recipes.md` + `docs/study-examples.md` | 2 份 | 工作流范例 + study 动词示例 |

> 这种"主题 / 闸门 / 协议 / 样例"四件套是经典的设计系统结构——参考 Material Design、Polaris、Lightning 的目录切法。Hallmark 的特别之处是面向 LLM（不是人）维护：每条规则同时面对"我要让模型遵守"和"我要让人读懂为什么"两个目标。

### 20 个主题 vs Catalog / Custom / Vanilla

- **Catalog 主题**（Hum / Cobalt / Carnival / Lumen / Garden / Riso 等 20 个）：每个对应一个明确的视觉指纹（Carnival = 马戏团彩旗、Riso = 丝网印刷错位、Garden = 园艺广告印刷品、Lumen = 学术 …）。
- **Custom 分支**：当 brief 携带主题覆盖不到的"创意意图"（如"做一张夜车卧铺票"），进入 Custom，从 palette + type + layout 重新构造，不套 catalog。Custom 仍需要过 57 条 slop-test。
- **Vanilla 主题**：当 brief 没有创意意图时（比如 demo 里某些"普通 SaaS 落地页"），vanilla 主题保证规则被遵守而不强加风格——目录的 Custom 段明确说"It stays a quiet branch; vanilla briefs never see it"。

> 这条分支协议是 Hallmark 区别于"AI 设计 prompt 集合"的关键：不是所有 brief 都应该走 Custom（Custom 是为了"超出目录的创意意图"），但 vanilla 也不能偷懒直接给"AI 默认分布"，vanilla 必须仍然过 slop-test。

### Slop-test 57 条闸门（工作机制）

slop-test 在 README 里被描述为"fifty-seven slop-test gates plus a pre-emit self-critique"。仓库没公开全部 57 条（多为反模式判别 + 模式是否落在 20 个 catalog 指纹外的检测），可以推断的几类：

| 反模式类别 | 例子 | 拒绝动作 |
|------------|------|----------|
| 色板 | 渐变粉紫、深空蓝、过度使用 `#6366f1` 等"AI 蓝" | 替换为对应主题的指纹色 |
| 圆角 | 全部 `border-radius: 24px+` | 主题约束内做差异化圆角 |
| 字体 | 仅 Inter / Geist / system-ui | 强制要求 type-pairing（如 Riso 用 serif + monospace） |
| 词汇 | Empower / Seamlessly / Unlock 动词堆 | 替换为可感知的具体名词 |
| 布局 | 中线居中 + 三栏 features + 顶部大 hero | 强制 macrostructure 偏移 |
| 装饰 | blob / mesh gradient / aurora / glow 渐变 | 不出现在 Hallmark 输出 |
| icon | 纯 emoji 替代 icon | 用主题对应的几何 / 文字 icon |
| 复用 | 直接抄 shadcn / Tailwind UI / Vercel 模板 | 拒绝 |
| 像素克隆 | study 模式下像素级复刻另一份设计 | 拒绝，只抽 DNA |

> slop-test 闸门是规则集而非 ML 模型——意味着它们可读、可改、可补。维护者（Hallmark 团队）可以加入新的反模式，不需要重新训练。

## 任务流案例：hallmark 默认动词从 brief 到成品

```
用户 prompt
"做一个茶馆的菜单网页"
        │
        ▼
┌──────────────────────────────────────┐
│ Claude Code / Cursor / Codex          │
│ 已加载 hallmark skill（SKILL.md）     │
└──────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────┐
│ Step 1: 解析 brief                    │
│ - "茶馆" → 哪个 catalog 主题匹配？      │
│   → 命中 Hum（面包房、手作坊类）或      │
│     Garden（园艺农产）或 Custom          │
└──────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────┐
│ Step 2: 选主题 + macrostructure       │
│ - Hum 主题 = 手作、印刷感、暖色           │
│ - macrostructure = e.g. "menus-as-     │
│   broadsheet"                          │
└──────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────┐
│ Step 3: 应用主题规则集                 │
│ - type-pairing: serif body + slab     │
│   headline                             │
│ - colour anchor: warm earth tones    │
│ - 拒绝 glassmorphism / gradient       │
└──────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────┐
│ Step 4: 写 HTML + CSS                  │
│ - 自包含文件（HTML 内嵌 CSS）           │
│ - CSS 注释里 stamp macrostructure     │
└──────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────┐
│ Step 5: 跑 slop-test 57 闸门          │
│ - 检查无渐变、无 emoji icon、          │
│   无 Empower动词堆                    │
│ - 不通过则重写或换主题                  │
└──────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────┐
│ Step 6: Pre-emit self-critique        │
│ - 模型自评："这份设计有没有看起来像    │
│   AI 默认产物？"                       │
│ - 不通过则重新进入 Step 3              │
└──────────────────────────────────────┘
        │
        ▼
自包含 HTML + CSS 交付
（macrostructure stamp 写在 CSS 注释里）
```

> 这个流程的核心不是"让 AI 更强"，而是"在 AI 已经够强的基础上，把决策权从模型的训练分布拿出来，交给人工规则"。一旦规则集覆盖完整，AI 设计就从"开盲盒"变成"按协议生成"。

## 关键设计取舍

### 1. 跨引擎一致（Claude Code / Cursor / Codex）

`SKILL.md` 顶部明确：**同一份 SKILL.md + references 在三个 IDE / CLI 引擎里通用**。这不是技术魔法——每个引擎都有"读 SKILL.md / rules 目录"的约定，Hallmark 利用它们的共同子集：

```bash
npx skills add nutlope/hallmark
```

或者手动复制：

```
Claude Code:  ~/.claude/skills/hallmark/
Cursor:       .cursor/rules/hallmark.mdc     ← 取 SKILL.md 正文，去掉 frontmatter
Codex:        ~/.codex/skills/hallmark/        ← 个人
              .codex/skills/hallmark/        ← 项目范围
```

> 这条设计的杠杆极大：开发者不需要为每个引擎学一套 prompt 习惯。但代价是对引擎版本敏感——某天 Claude Code 改了 skill 加载语义，Hallmark 必须更新一次。

### 2. Custom 分支作为"意图兜底"

大多数 AI 设计 prompt 在"用户创意意图超出已有模板"时会硬套一个最相似的 catalog 模板，结果是"既不像已有模板的标杆，又不像用户想要的"。Hallmark 的 Custom 分支是显式的兜底：**当前目录主题覆盖不到时，从零构造一个全新 palette + type + layout，但仍跑 slop-test**。

Custom 不是默认分支——它只在 brief 表达出明显超出 catalog 的创意意图时才触发。这意味着普通 SaaS 落地页 brief 永远不会进 Custom，避免"创意型狂野设计"侵入稳定输出区。

### 3. study 动词的"反像素克隆"

```bash
hallmark study https://stripe.com
```

这一动词是从第三方设计抽取 DNA（macrostructure、type-pairing、colour anchor）然后改写。Hallmark **主动拒绝两件事**：

- **像素级克隆**：把 stripe.com 的色号、字号直接抄过来。
- **付费模板克隆**：把付费 UI kit（Tailwind UI Pro、shadcn Pro）拆皮后输出——这有法律 / 协议风险。

study 还能输出一个可便携的 `design.md`，让别的 AI 工具接手继续设计。这条接口的存在让 Hallmark 在大型工作流里能当"设计 DNA 提取器"用，不只是"成品生成器"。

### 4. 自包含 HTML + CSS（不绑定框架）

`site/_tests/` 下的 20+ 演示样例都是**单个 HTML 文件 + 内嵌 CSS**——不依赖 React、Vue、Tailwind、Webpack 任何工具链。打开即可在浏览器看，复制即可上线（最多调整 image / font 来源）。这种"零依赖产物"的代价是不方便做大型交互工程，但对"快速产出一个能上线的展示页"是最低门槛。

### 5. CSS 注释 stamp macrostructure

每个 demo HTML 的 CSS 注释行里写明这条产物用的是哪个 macrostructure（结构风格）+ theme：

```css
/* macrostructure: menu-as-broadsheet | theme: Hum | brief: tea-menu */
```

这种 stamping 让代码可以被审计、可被复刻、可被加入 Custom 分支的 training 参考。从工程治理角度看，比 Git LFS 一些 metadata JSON 轻得多。

## 与其他 AI 设计工具的边界

| 工具 | 主形态 | 与 Hallmark 的关系 |
|------|--------|-------------------|
| Hallmark | skill + 规则集 | 强制执行反 AI 味 |
| v0.dev | Vercel 出品的 AI 生成 React/Tailwind UI | 不限制输出风格，会"AI 默认分布"漂移 |
| Galileo AI | AI 设计 + Figma 集成 | 偏视觉，自然走默认分布 |
| Figma AI / Figma Make | Figma 内 AI | 在 Figma 工作流内，目标成果是 Figma frame |
| Relume / Durable | AI 落地页 | 营销导向，default 渐变 + 大 hero |
| Midjourney / DALL-E | 图像生成 | 不做网页 layout，做插画 / 海报 |
| agent-skills 集合 | 通用的 skill 协议 | 上游协议；Hallmark 是该协议的"设计 skill" 实例 |

> 区别核心：**Hallmark 是规则集，其他大部分 AI 设计工具是模型驱动**。规则集的稳定性远高于模型，且规则集可以被开发者编写、审阅、扩展。

## 与"自定义 Claude Code skill"的边界

Claude Code 已经支持任意 skill 目录，开发者完全可以自己写一份 "anti-slop-design.md" 放进 `~/.claude/skills/`。但 Hallmark 提供的"集中维护 + 持续更新 + 20 个主题 + 57 条闸门 + Custom 分支 + 演示站 + study 动词"是个人写一份难以触达的规模感。从投资回报看：

- **用 Hallmark**——如果你需要"AI 别给我千篇一律的设计"，且接受 skill 套用宏观规则。
- **自己写**——如果你的设计语言非常特化（比如"只能做朝鲜文旅游门户"），Hallmark 的目录无法直接套。
- **结合**——把 Hallmark 当作规则集基线，再覆盖一层自家品牌规则（颜色、字体、icon 库）。

## 适用场景

### 适合

- **快速做宣传/营销落地页**——茶馆、唱片厂牌、AI 工具、SaaS、旅行预订等 demo 站里都有覆盖。
- **AI 工具类应用的 hero / examples**——上文 12 张图都是 AI 工具的产物（Cinder、NAJM、Hyperlane、Tally 等）。
- **设计师想要 audit 已有页面**——audit 动词直接产 punch list。
- **学习反 AI 味设计**——57 条 slop-test 是公开的反模式教材。

### 不适合

- **复杂企业级后台**——Hallmark 偏向 landing / showcase，没承诺 dashboard / 数据表格的视觉规则。
- **强交互应用**——自包含 HTML + CSS 不绑定 React / state。
- **需要严格符合 WCAG / RTL / 印地语排版**的合规场景——Hallmark 没承诺这些。
- **印刷品**（海报、画册）——样例都是屏幕尺寸。

## 安装与上手

```bash
# 一键装到当前工程（Claude Code 推荐）
npx skills add nutlope/hallmark

# 手动复制（任意引擎通用）
git clone https://github.com/Nutlope/hallmark
cp -r hallmark/skills/hallmark ~/.claude/skills/

# Cursor：把 SKILL.md 内容（去掉 frontmatter）写入
# .cursor/rules/hallmark.mdc

# Codex：放到 ~/.codex/skills/hallmark/

# 看 20 个主题 demo（无需安装）
open https://www.usehallmark.com
```

装完之后：

- 在 Claude Code 直接说 "用 hallmark 做 X 网站"。
- 说 "hallmark audit 当前 index.html" 拿反模式清单。
- 把别的网站 URL 用 "hallmark study <URL>" 抽 DNA。

## 阅读路径建议

1. **先看 usehallmark.com 的 12 个截图**——30 秒内能感受到"非 AI 默认"是什么样。
2. **下载 SKILL.md + references 目录**——这才是产品的实质，仓库其他都是辅助。
3. **读 docs/recipes.md + docs/study-examples.md**——典型 prompt 例子比规则文字更快上手。
4. **跑一次 audit 动词**——拿一份自己的已有页面过 audit，对照 punch list 看 57 条 slop-test 是怎么落地的。
5. **改一条 slop-test**——按你的品牌加一条反模式，体验维护自定义规则的成本曲线。

## 参考资源

- 主仓库：`https://github.com/Nutlope/hallmark`
- 演示站（20+ 主题示例）：`https://www.usehallmark.com`
- SKILL.md 主规则：`https://github.com/Nutlope/hallmark/blob/main/skills/hallmark/SKILL.md`
- Custom 分支协议：`https://github.com/Nutlope/hallmark/blob/main/skills/hallmark/references/custom-theme.md`
- 工作流范例：`https://github.com/Nutlope/hallmark/blob/main/docs/recipes.md`
- study 动词示例：`https://github.com/Nutlope/hallmark/blob/main/docs/study-examples.md`
- 安装命令：`npx skills add nutlope/hallmark`
- 出品方 Together AI：`https://www.together.ai/`
- 仓库 author Nutlope 个人博客：`https://nutlope.com`
