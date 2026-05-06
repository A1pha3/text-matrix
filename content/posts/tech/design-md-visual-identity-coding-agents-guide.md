---
title: "DESIGN.md：让 Coding Agents 理解视觉设计的格式规范"
categories: ["技术笔记"]
tags: ["design.md", "design-system", "ai-agent", "google-labs-code", "design-token"]
date: "2026-04-30T11:30:00+08:00"
draft: false
---

# DESIGN.md：让 Coding Agents 理解视觉设计的格式规范

> **项目信息**：google-labs-code/design.md ⭐ 10,199 | Apache-2.0 | Created 2026-04-10
> **官方文档**：[stitch.withgoogle.com/docs/design-md/specification](https://stitch.withgoogle.com/docs/design-md/specification)
> **npm 包**：`@google/design.md`

---

## 一、背景与问题域

在 AI Coding Agent（如 Claude Code、Cursor、Copilot 等）飞速发展的今天，一个根本性的矛盾日益凸显：**设计系统与代码实现之间缺乏稳定的双向桥梁**。

传统工作流中，设计稿（Figma/Sketch）通过 design token 输出给开发同学，开发同学再将这些 token 落地为 CSS 变量或 Tailwind 配置。这个过程在人类协作中已经足够复杂，而当 AI Agent 介入时，问题变得更加棘手：

- AI Agent 生成的前端代码在色彩、间距、圆角上高度随机，缺乏一致性
- 不同 Agent、不同会话之间，视觉风格无法保持连贯
- 设计系统（Figma 变量库）与 Agent 的上下文理解之间存在巨大语义鸿沟

**DESIGN.md** 正是 Google Labs Code 团队给出的答案：一种**人类可读、机器可解析的设计系统描述格式**——将视觉设计从 Figma 的专有二进制中解放出来，以纯文本形式持久化地传达给 AI Agent。

---

## 二、核心概念：双层结构设计

DESIGN.md 文件的核心哲学体现在它的**双层结构**中：

```
┌─────────────────────────────────────┐
│  YAML Front Matter（机器可读层）      │  ← 设计 Token：精确数值
├─────────────────────────────────────┤
│  Markdown Body（人类可读层）          │  ← 设计理念：为什么选这些值
└─────────────────────────────────────┘
```

### 2.1 YAML Front Matter — 精确的设计 Token

```yaml
---
name: Heritage
colors:
  primary: "#1A1C1E"
  secondary: "#6C7278"
  tertiary: "#B8422E"
  neutral: "#F7F5F2"
typography:
  h1:
    fontFamily: Public Sans
    fontSize: 3rem
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: -0.02em
rounded:
  sm: 4px
  md: 8px
spacing:
  sm: 8px
  md: 16px
components:
  button-primary:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.on-tertiary}"
    rounded: "{rounded.sm}"
    padding: 12px
---
```

这是 AI Agent 直接消费的**规范性值（Normative Values）**——告诉 Agent 具体该用什么数值，而不是模糊的描述。

### 2.2 Markdown Body — 设计理念与上下文

```markdown
## Overview

Architectural Minimalism meets Journalistic Gravitas. The UI evokes a
premium matte finish — a high-end broadsheet or contemporary gallery.

## Colors

- **Primary (#1A1C1E):** Deep ink for headlines and core text.
- **Tertiary (#B8422E):** "Boston Clay" — the sole driver for interaction.
```

这部分解释了**为什么**选择这些值——品牌的个性、情感诉求、视觉隐喻。这是 Agent 在遇到未明确定义场景时做判断的指南。

> **关键原则**：Token 是规范，Prose 是上下文。两者缺一不可。

---

## 三、Token 类型系统

DESIGN.md 定义了以下几种核心 Token 类型：

| 类型 | 格式 | 示例 |
|:-----|:-----|:-----|
| **Color** | `#` + hex (sRGB) | `"#1A1C1E"` |
| **Dimension** | 数字 + 单位 (`px`, `em`, `rem`) | `48px`, `-0.02em` |
| **Token Reference** | `{path.to.token}` | `{colors.primary}` |
| **Typography** | 含 `fontFamily`, `fontSize`, `fontWeight` 等的对象 | 见下方 |

### Typography 完整结构

```yaml
typography:
  h1:
    fontFamily: Public Sans
    fontSize: 3rem
    fontWeight: 600
    lineHeight: 1.1        # 支持 24px / 1.6 等格式
    letterSpacing: -0.02em
    fontFeature: "tnum"   # OpenType 特性
    fontVariation: "wght 600"  # 可变字体轴
```

### Token Reference 引用机制

DESIGN.md 支持**跨 Token 引用**，使用 `{path.to.token}` 语法：

```yaml
components:
  button-primary:
    backgroundColor: "{colors.tertiary}"    # 引用 colors token
    textColor: "{colors.on-tertiary}"        # 引用 colors token
    rounded: "{rounded.sm}"                  # 引用 rounded token
    padding: 12px                            # 直接字面值
```

这使得 Token 之间可以建立**依赖关系图**，linter 可以检测**悬空引用（broken-ref）**——即引用了但从未定义过的 Token。

---

## 四、Section 规范：八段式结构

DESIGN.md 的 Markdown Body 必须遵循严格的 Section 顺序（使用 `##` 标题）：

| # | Section | 别名 |
|:--|:--------|:-----|
| 1 | Overview | Brand & Style |
| 2 | Colors | |
| 3 | Typography | |
| 4 | Layout | Layout & Spacing |
| 5 | Elevation & Depth | Elevation |
| 6 | Shapes | |
| 7 | Components | |
| 8 | Do's and Don'ts | |

**Section 顺序规则**：已存在的 Section 必须按此顺序排列；未使用的 Section 可以跳过；未知 Section（如 `## Iconography`）会被保留但不会报错。

---

## 五、组件 Token 规范

Components 部分定义了一组可复用的组件样式模板：

```yaml
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label-md}"
    rounded: "{rounded.md}"
    padding: 12px
    height: 48px
  button-primary-hover:
    backgroundColor: "{colors.primary-container}"
  glass-card-standard:
    backgroundColor: rgba(255, 255, 255, 0.1)
    textColor: "{colors.primary}"
    rounded: "{rounded.lg}"
    padding: "{spacing.glass-padding}"
```

**支持的组件属性**：

- `backgroundColor` — 背景色
- `textColor` — 文字色
- `typography` — 排版（引用 typography token）
- `rounded` — 圆角（引用 rounded token）
- `padding` — 内边距
- `size` / `height` / `width` — 尺寸

**变体表达**：hover、active、pressed 等状态通过**命名约定**表达——在同一组件名下加 `-hover`、`-active` 后缀。Agent 会自动识别并应用。

---

## 六、架构深度解析

### 6.1 整体架构

```
DESIGN.md 文件
     │
     ▼
┌─────────────┐
│   Parser    │  ← 解析 YAML frontmatter + Markdown body
│  Handler    │    (remark-frontmatter + yaml)
└──────┬──────┘
       ▼
┌─────────────┐
│   Model     │  ← 构建类型化 DesignSystemState
│  Handler    │    解析 token reference、类型校验
└──────┬──────┘
       ▼
┌─────────────┐
│   Linter    │  ← 执行 7 条规则
│   Runner    │    broken-ref / contrast / orphaned-tokens...
└──────┬──────┘
       ├───┬───────┬──────────┐
       ▼   ▼       ▼          ▼
   ┌────┐ ┌────┐ ┌────────┐ ┌────────────┐
   │Fixer│ │Tailwind│ │  DTCG   │ │   Spec    │
   │    │ │Emitter│ │Emitter  │ │ Generator │
   └────┘ └────┘ └────────┘ └────────────┘
```

### 6.2 Parser 层 (`parser/handler.ts`)

核心职责：提取 YAML 并构建文档结构。

```typescript
// 解析流程
const processor = unified()
  .use(remarkParse)
  .use(remarkFrontmatter, ['yaml']);

// 支持两种 YAML 嵌入方式：
// 1. frontmatter（--- yaml ---）
// 2. fenced code block（```yaml ... ```）
```

关键设计决策：
- **绝不抛异常**：所有错误都包装为 `ParserResult` 返回，`recoverable: true` 时可继续处理
- **支持多 Code Block**：允许分散在多个 ` ```yaml ` 代码块中的 YAML，最终合并
- **Source Map**：每个 token 的来源（文件行号、所属 block）都被追踪

### 6.3 Model 层 (`model/handler.ts`)

核心职责：解析 token reference，建立 token 依赖图，执行类型校验。

```typescript
// Token Reference 解析示例
// 输入: "{colors.primary}"
// 输出: 解析为对 colors.primary 这个 token 的引用
```

### 6.4 Linter 层 (`linter/runner.ts`)

执行 7 条静态规则，产生结构化 findings：

| 规则名 | 严重级别 | 检查内容 |
|:-------|:--------|:---------|
| `broken-ref` | **error** | Token 引用无法解析 |
| `missing-primary` | warning | 定义了颜色但没有 `primary` |
| `contrast-ratio` | warning | 组件前景/背景对比度低于 WCAG AA (4.5:1) |
| `orphaned-tokens` | warning | 定义了但从未被引用的 color token |
| `token-summary` | info | 各 section 的 token 数量统计 |
| `missing-sections` | info | 定义了 token 但缺少对应 section |
| `missing-typography` | warning | 定义了颜色但没有 typography |
| `section-order` | warning | Section 顺序不符合规范 |

### 6.5 Emitter 层 — 格式导出

DESIGN.md 的 Token 可以导出为其他流行格式：

**Tailwind CSS Theme Config：**

```bash
npx @google/design.md export --format tailwind DESIGN.md > tailwind.theme.json
```

导出的 Tailwind 配置结构：

```json
{
  "theme": {
    "extend": {
      "colors": { "primary": "#1A1C1E", ... },
      "fontFamily": { "h1": ["Public Sans", "sans-serif"] },
      "borderRadius": { "sm": "4px", "md": "8px" }
    }
  }
}
```

**DTCG (W3C Design Token Format)：**

```bash
npx @google/design.md export --format dtcg DESIGN.md > tokens.json
```

遵循 W3C Design Token Community Group 规范，实现设计系统跨工具互操作。

---

## 七、CLI 命令详解

### 7.1 `lint` — 验证 DESIGN.md

```bash
npx @google/design.md lint DESIGN.md
```

输出示例：

```json
{
  "findings": [
    {
      "severity": "warning",
      "path": "components.button-primary",
      "message": "textColor (#ffffff) on backgroundColor (#1A1C1E) has contrast ratio 15.42:1 — passes WCAG AA."
    }
  ],
  "summary": { "errors": 0, "warnings": 1, "info": 1 }
}
```

支持 stdin 输入：

```bash
cat DESIGN.md | npx @google/design.md lint -
```

### 7.2 `diff` — 版本间 Token 差异对比

```bash
npx @google/design.md diff DESIGN.md DESIGN-v2.md
```

输出示例：

```json
{
  "tokens": {
    "colors": { "added": ["accent"], "removed": [], "modified": ["tertiary"] },
    "typography": { "added": [], "removed": [], "modified": [] }
  },
  "regression": false
}
```

**regression 字段**：当 "after" 文件比 "before" 产生更多 errors/warnings 时为 `true`，CLI 退出码为 1。

### 7.3 `export` — 格式导出

```bash
npx @google/design.md export --format tailwind DESIGN.md > tailwind.theme.json
npx @google/design.md export --format dtcg DESIGN.md > tokens.json
```

### 7.4 `spec` — 规范输出

```bash
npx @google/design.md spec                    # 输出完整规范（Markdown）
npx @google/design.md spec --rules            # 附加 lint 规则表
npx @google/design.md spec --rules-only --format json  # 仅 JSON 规则
```

这个命令对于**将规范注入 Agent prompt**非常有用：

```
You are a frontend coding agent. Before generating UI, read the design system spec:
---
npx @google/design.md spec
---
```

---

## 八、编程 API

除了 CLI，`@google/design.md` 还提供完整的 TypeScript API：

```typescript
import { lint } from '@google/design.md/linter';

const report = lint(markdownString);

console.log(report.findings);        // Finding[]
console.log(report.summary);         // { errors, warnings, infos }
console.log(report.designSystem);    // Parsed DesignSystemState
console.log(report.tailwindConfig);  // Tailwind theme config
console.log(report.sections);       // ['Overview', 'Colors', 'Typography', ...]
```

**高级 API** — 逐层控制：

```typescript
import { runLinter, preEvaluate } from '@google/design.md/linter';
import { contrastRatio } from '@google/design.md/linter';

// 手动执行各阶段
const parsed = parser.execute({ content });
const modelResult = model.execute(parsed.data);
const lintResult = runLinter(modelResult.designSystem, customRules);

// 自定义对比度计算
const ratio = contrastRatio('#ffffff', '#000000'); // → 21:1
```

---

## 九、实战演示

### 9.1 从零创建一个 DESIGN.md

以 Google Stitch 的 Atmospheric Glass 示例为参考，这是一个天气 App 的 Glassmorphism 设计系统：

**Step 1：创建文件结构**

```bash
touch DESIGN.md
```

**Step 2：编写 Front Matter**

```yaml
---
name: Atmospheric Glass
colors:
  surface: "#0b1326"
  surface-container: "#171f33"
  on-surface: "#dae2fd"
  primary: "#ffffff"
  on-primary: "#2f3131"
  secondary: "#adc9eb"
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 84px
    fontWeight: "700"
    lineHeight: 90px
    letterSpacing: -0.04em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: "600"
    lineHeight: 40px
rounded:
  sm: 0.25rem
  lg: 1rem
  xl: 1.5rem
spacing:
  unit: 8px
  container-padding: 24px
components:
  glass-card-standard:
    backgroundColor: rgba(255, 255, 255, 0.1)
    textColor: "{colors.primary}"
    rounded: "{rounded.lg}"
    padding: "{spacing.glass-padding}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    height: 48px
    padding: 0 24px
---
```

**Step 3：编写 Prose Sections**

```markdown
## Brand & Style

This design system centers on a high-fidelity Glassmorphism aesthetic.
The UI relies on a "vibrant-minimalist" approach: the background provides
the energy through multi-colored abstract gradients, while the interface
elements act as frosted crystalline lenses.

## Colors

- **Primary Canvas:** A multi-stop linear gradient background featuring
  Deep Blue (#1E3A8A), Vivid Purple (#7E22CE), and Soft Pink (#DB2777).
- **Surface Alpha:** Component backgrounds are never solid. They range from
  `rgba(255, 255, 255, 0.1)` for secondary depth to `0.2` for primary.

## Elevation & Depth

- **Level 1 (Base):** Dynamic background gradient with a slight grain texture.
- **Level 2 (Standard Card):** `backdrop-filter: blur(20px)`,
  `background: rgba(255, 255, 255, 0.1)`.
- **Level 3 (Elevated/Modals):** `backdrop-filter: blur(40px)`,
  `background: rgba(255, 255, 255, 0.2)`.
```

**Step 4：Lint 验证**

```bash
npx @google/design.md lint DESIGN.md
```

### 9.2 集成到 Agent 工作流

**方式一：通过 Agent 配置文件（`.agents`）**

```
# .agents/AGENTS.md
When working on this project, read DESIGN.md first to understand the
visual identity. Use `npx @google/design.md lint` to validate any
changes to the design system.
```

**方式二：CI/CD 自动化**

```yaml
# .github/workflows/design-lint.yml
name: Design System Lint
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npx @google/design.md lint DESIGN.md
```

**方式三：注入 Agent System Prompt**

```typescript
// 在 Agent 配置中注入规范
const agentSystemPrompt = `
You are a frontend coding agent. Read the design system specification:
${await exec('npx @google/design.md spec')}
`;
```

---

## 十、开发扩展

### 10.1 发布自己的 DESIGN.md 规范包

将设计系统发布为 npm 包：

```json
// package.json
{
  "name": "@mycompany/design-system",
  "version": "1.0.0",
  "exports": {
    "./DESIGN.md": "./DESIGN.md"
  }
}
```

### 10.2 自定义 Lint 规则

```typescript
import { lint, DEFAULT_RULES, type LintRule } from '@google/design.md/linter';

const customRule: LintRule = {
  name: 'no-red-buttons',
  severity: 'warning',
  check: (state) => {
    const findings = [];
    const btn = state.components['button-primary'];
    if (btn?.backgroundColor === '{colors.error}') {
      findings.push({
        severity: 'warning',
        path: 'components.button-primary.backgroundColor',
        message: 'Avoid using error color for primary buttons.',
      });
    }
    return findings;
  },
};

const report = lint(content, {
  rules: [...DEFAULT_RULES, customRule],
});
```

### 10.3 扩展 Emitter（导出到其他格式）

参考现有的 Tailwind 和 DTCG Emitter 实现：

```typescript
// 新建 packages/cli/src/linter/css/handler.ts
export class CssEmitterHandler {
  execute(designSystem: DesignSystemState): CssOutput {
    return {
      ':root': {
        '--color-primary': designSystem.colors.primary,
        '--spacing-unit': designSystem.spacing.unit,
        // ...
      }
    };
  }
}
```

### 10.4 与 Figma Variables 集成

利用 DTCG 导出作为中间格式：

```bash
# Figma → DTCG tokens → DESIGN.md
figma variables export --format dtcg > tokens.json
# 使用转换脚本将 tokens.json → DESIGN.md frontmatter
```

---

## 十一、Consumer Behavior（消费者行为规范）

DESIGN.md 规范明确定义了 Consumer 遇到**未知内容**时的行为：

| 场景 | 行为 |
|:-----|:-----|
| 未知 section heading | 保留，不报错 |
| 未知 color token 名 | 接受（如果值合法） |
| 未知 typography token 名 | 接受为合法 typography |
| 未知 spacing 值 | 接受 |
| 未知 component property | 接受（带 warning） |
| 重复 section heading | **Error**：拒绝文件 |

这一设计确保了规范的**前向兼容**——未来的 token 类型和 section 不会导致现有 linter 报错。

---

## 十二、技术栈与依赖

- **Parser**：`unified` + `remark-frontmatter` + `yaml`
- **类型校验**：`zod`
- **构建**：`bun` + `TypeScript`
- **Monorepo**：`turbo`（pnpm-like 任务编排）
- **测试**：`bun test`

核心依赖极简（`yaml`、`zod`、`unified`），零重型依赖保证了 npm 包的轻量化。

---

## 十三、局限性与未来

- **当前版本**：`alpha`，格式和 API 仍在活跃演化中
- **组件规范**：仍在演进中，Components section 目前保持灵活性以容纳不同领域
- **语义色彩**：`on-primary`、`on-secondary` 等语义色彩 token 未在规范中明确定义（但 examples 中有使用）
- **Theme 变量**：尚不支持暗/亮主题切换的机制

---

## 总结

DESIGN.md 是 AI Coding Agent 时代的一个关键基础设施。它以极简的双层结构（YAML Token + Markdown Prose）解决了三个核心问题：

1. **精确性**：Token 提供无歧义的数值，消除 Agent 生成 UI 时的随机性
2. **持久性**：纯文本格式，不依赖 Figma/Sketch 等专有工具，可版本控制、可 Code Review
3. **互操作性**：DTCG/Tailwind 导出实现与现有工具链的双向桥接

无论你是**设计系统维护者**还是**AI Coding Agent 开发者**，DESIGN.md 都值得深入了解。它代表了 Google 对"AI 时代的设计工程化"这一命题的系统性思考。

> **延伸阅读**：
> - 官方 Spec：https://stitch.withgoogle.com/docs/design-md/specification
> - GitHub：https://github.com/google-labs-code/design.md
> - W3C Design Token Format：https://www.designtokens.org/
