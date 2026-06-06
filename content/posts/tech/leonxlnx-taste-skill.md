+++
date = '2026-05-16T23:46:24+08:00'
draft = false
title = 'Taste-Skill：AI 前端反 slop 框架'
slug = 'leonxlnx-taste-skill-anti-slop'
description = 'Taste-Skill 通过结构化的 SKILL.md 规范对抗 LLM 前端生成的 slop 问题，基于控制实验数据系统分析 LazyBench 现象、根因和修复体系，覆盖 12 个细分技能。'
categories = ['技术笔记']
tags = ['AI', '前端', '设计', '开源']
+++

# Taste-Skill：AI 前端反 slop 框架

> 如果你用 AI 生成过前端界面，大概率见过这些画面：紫色渐变按钮、居中的 Hero、Inter 字体、`h-screen` 撑满的页面、用 emoji 替代图标——这不是你要求的，但 AI 总能加上。这类产物被社区称为 **slop**。Taste-Skill 就是为了解决这个问题而诞生的。

**GitHub**: [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill)
**官网**: [tasteskill.dev](https://tasteskill.dev)

---

## 1. 背景：为什么 AI 生成的前端总是「油腻」？

Taste-Skill 的作者（[@lexnlin](https://x.com/lexnlin) / [@blueemi99](https://x.com/blueemi99)）在项目 research 目录下做了大量深入研究，系统性地分析了 LLM 输出「垃圾内容」的根因。这不是主观审美问题，而是有明确实验数据支撑的行为模式。

### 1.1 LLM「懒惰」（Lazy Output）的根因

**认知捷径（cognitive shortcuts）**：当模型感知到任务「简单」或上下文「过长」时，会主动减少内部计算量，用表面层总结替代完整多步推理。这不是记忆退化或上下文衰减——模型**知道**完整的答案，但**选择**不输出。2024 年底的实验（LazyBench）已证实这一点。

**训练数据偏差（RLHF + Compute）**：强化学习阶段，人类标注者隐式地奖励「简洁」输出（阅读体验好、看起来完整），惩罚「冗长」输出（看起来啰嗦、可能包含错误）。模型学会了一个不等式：**短输出 = 低风险 = 奖励**。

**季节性行为异常**：2023 年 12 月 ChatGPT 平均输出长度显著下降，因为训练数据中国际员工的产出本身就偏少。模型把这个模式内化了——即使在 5 月，在 prompt 中加一句「现在是 12 月」，输出长度又会上升。

**错误规避驱动截断**：长输出=更多错误表面积=更多幻觉风险=负面反馈。截断成为降低风险的理性选择。

### 1.2 前端设计的「AI 典型病」

| 病症 | 描述 |
|:---|:---|
| **AI Purple** | 紫色/蓝色霓虹渐变、按钮发光效果 |
| **居中偏执** | Hero/H1 全部居中，不管上下文 |
| **Emotion Emoji** | 代码和 UI 中大量 emoji 替代专业图标 |
| **Card 滥用** | 任何内容都用卡片容器，导致层级混乱 |
| **h-screen 灾难** | 用 `h-screen` 做全屏 Hero，移动端灾难性跳动 |
| **Inter 字体病** | 不分场景默认 Inter，缺乏个性 |
| **不完整状态** | 只有成功状态，没有 Loading/Empty/Error |

这些不是偶发现象，而是大模型在统计规律中学到的「最安全、最常见、最少被投诉」的模式集合。

---

## 2. 核心概念：从「模型调参」到「行为规范」

### 2.1 SKILL.md 体系——Agent 的即插即用模块

Taste-Skill 没有发明新协议，而是复用了 [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills) 的标准格式。每个 Skill 就是一个包含 `SKILL.md` 的文件夹，通过 `npx skills add` 安装。

```
skills/
├── taste-skill/         → design-taste-frontend
├── gpt-tasteskill/      → gpt-taste
├── image-to-code-skill/ → image-to-code
├── soft-skill/          → high-end-visual-design
├── minimalist-skill/    → minimalist-ui
├── brutalist-skill/      → industrial-brutalist-ui
└── ...
```

安装方式：
```bash
# 全部安装
npx skills add https://github.com/Leonxlnx/taste-skill

# 按名称安装单个
npx skills add https://github.com/Leonxlnx/taste-skill --skill "design-taste-frontend"
```

### 2.2 三维配置系统（DESIGN_VARIANCE / MOTION_INTENSITY / VISUAL_DENSITY）

每个 Skill 的顶部有一段 YAML frontmatter，其中三行数字定义了 AI 生成界面的「性格」：

| 参数 | 范围 | 含义 |
|:---|:---|:---|
| `DESIGN_VARIANCE` | 1-10 | 布局实验度（1=完美对称，10=艺术化混乱） |
| `MOTION_INTENSITY` | 1-10 | 动画深度（1=静止，10=电影级/魔法物理） |
| `VISUAL_DENSITY` | 1-10 | 单屏信息密度（1=艺术馆级留白，10=驾驶舱级密集） |

默认值 **8/6/4**（高变化度 + 中等动效 + 适中的视觉密度），用户可以通过对话中直接指定数值来覆盖，比如「把这个页面改成 `MOTION_INTENSITY=2`、`VISUAL_DENSITY=2`」。

### 2.3 懒惰 remediation（对抗策略）的四层体系

项目 research 目录包含了完整的研究体系：

| 层级 | 文件 | 作用 |
|:---|:---|:---|
| **根因分析** | `root-causes/` | cognitive-shortcuts、output-limits、rlhf-and-compute、training-data-bias |
| **实验数据** | `findings/empirical-results.md` | 2025年对照实验：多部分指令服从仅 34%-80%、加「深呼吸」指令让准确率从34%到80% |
| **对抗策略** | `remediation/` | 架构模式、参数调优、提示工程、参考提示词 |
| **技能规范** | `skills/*.md` | 将研究结论产品化为 AI 可执行的规则 |

---

## 3. 架构解析：SKILL.md 内部结构

### 3.1 设计工程指令（Design Engineering Directives）

以 `taste-skill/SKILL.md` 为例，这是最核心的 Skill。内容组织成 7 个 SECTION：

**Section 1: ACTIVE BASELINE CONFIGURATION**
定义三围参数的默认值，AI 必须遵守，除非用户明确覆盖。

**Section 2: DEFAULT ARCHITECTURE & CONVENTIONS**
结构规范，包含大量强制规则：
- 导入第三方库前必须检查 `package.json`，缺失则输出安装命令
- 默认 React/Next.js，使用 Server Components
- 状态管理：局部用 `useState`/`useReducer`，全局仅用于避免 prop-drilling
- 样式策略：90% 用 Tailwind CSS，并检查版本（T3 vs T4 语法不兼容）
- **emoji 禁令**：代码、markup、文字内容、alt 文本中严禁 emoji，必须用 Phosphor/Radix 图标或 SVG 原语替代

**Section 3: DESIGN ENGINEERING DIRECTIVES（核心）**
通过规则对抗 LLM 的设计偏见：

- **Rule 1: 确定性字体排版**
  - 标题：`text-4xl md:text-6xl tracking-tighter leading-none`
  - 字体选择：禁止默认 Inter，强制使用 Geist、Outfit、Cabinet Grotesk 或 Satoshi
  - 仪表盘/软件 UI 禁用衬线字体

- **Rule 2: 色彩校准**
  - 最多 1 个强调色，饱和度 < 80%
  - **AI Purple 禁令**：紫色/蓝色霓虹渐变严格禁止
  - 基调：Zinc/Slate 中性色 + 高对比度单一强调色（Emerald/Electric Blue/Deep Rose）

- **Rule 3: 布局多元化（对抗居中偏执）**
  - 当 `DESIGN_VARIANCE > 4`，居中 Hero/H1 严格禁止
  - 强制使用 Split Screen（50/50）、左文字右素材或 Asymmetric White-space

- **Rule 4: 材质感、阴影与反卡片滥用**
  - `VISUAL_DENSITY > 7` 时，通用卡片容器严格禁止
  - 用 `border-t`、`divide-y` 或负空间做逻辑分组
  - 只有需要 elevation（z-index）时才用卡片

- **Rule 5: 交互状态全覆盖**
  - Loading: 骨架屏（匹配布局尺寸，不用通用旋转器）
  - Empty: 精心设计的空状态引导用户填充
  - Error: 内联错误提示
  - `:active`: `-translate-y-[1px]` 或 `scale-[0.98]` 模拟物理按压反馈

- **Rule 6: 数据与表单模式**
  - Label 在 Input 上方，Helper text 可选，Error text 在 Input 下方

**Section 4-7（Motion / Liquid Glass / Advanced Typography）**：高阶视觉动效规范，包含 GSAP 集成方向、滚动动画、视差效果等。

### 3.2 技能分支体系

| Skill | Install name | 场景 |
|:---|:---|:---|
| `taste-skill` | `design-taste-frontend` | 通用默认，安全的全方位选择 |
| `gpt-tasteskill` | `gpt-taste` | GPT/Codex 专用，更严格的布局变化度和 GSAP 方向 |
| `image-to-code-skill` | `image-to-code` | 图像优先流程：生成参考图→分析→代码实现 |
| `redesign-skill` | `redesign-existing-projects` | 现有项目：先审计 UI，再修复布局/间距/层级 |
| `soft-skill` | `high-end-visual-design` | 高端精致 UI，低对比度、留白充足、春弹簧动画 |
| `minimalist-skill` | `minimalist-ui` | 编辑器风（Notion/Linear 风格），克制配色、清晰结构 |
| `brutalist-skill` | `industrial-brutalist-ui` | ⚠️ BETA 瑞士印刷风、硬机械语言、实验性布局 |
| `output-skill` | `full-output-enforcement` | 防止模型半途而废，强制完整输出 |
| `stitch-skill` | `stitch-design-taste` | Google Stitch 兼容规则，支持可选 `DESIGN.md` 导出 |

---

## 4. 工程亮点：从研究到生产的闭环

### 4.1 科学的研发流程

项目最令人印象深刻的地方不是代码本身，而是背后的研究深度。每个技能规范都基于：

- **2025 年控制实验数据**：多部分指令完成率仅 34%-80%，LLM 截断是**主动选择**而非能力不足
- **微软研究院提示刺激效果表**：加入「深呼吸」让逻辑准确率从 34% 提升到 80%，加入「200美元小费」让质量提升 45%
- **LazyBench 发现**：模型在感知任务「简单」或上下文「过长」时主动减少计算量
- **根因分类体系**：cognitive-shortcuts、output-limits、rlhf-and-compute、training-data-bias 四个维度

这意味着 Taste-Skill 的每条规则都有实验依据，不是「我觉得好看」的主观审美。

### 4.2 与主流 Agent 生态的集成

Taste-Skill 明确支持三大主流 Agent：

| Agent | 集成方式 |
|:---|:---|
| **Claude Code** | 直接复制 SKILL.md 到项目或粘贴到对话 |
| **OpenAI Codex** | 配合 `gpt-taste` 更严格的布局/GSAP 规则 |
| **Cursor** | 同上 |

图像生成类 Skill（`imagegen-frontend-web`、`brandkit` 等）则针对 ChatGPT Images 设计，输出参考图后交给编码 Agent 实现。

### 4.3 Skill 分工设计哲学

不是一个大而全的 Skill，而是多个专注单一职责的小 Skill：

> *Each skill does one job; you do not need all of them at once.*

这避免了单一大 Skill 上下文膨胀问题，也符合 MCP 协议的设计理念。每个 Skill 平均 ~200-400 行 MD，内容量控制在单次上下文可完全消费的范围内。

---

## 5. 竞争格局

| 方案 | 定位 | 优势 | 不足 |
|:---|:---|:---|:---|
| **Taste-Skill** | AI 前端品位规范 | 17k Stars，研究驱动，完整技能矩阵 | 仅限 SKILL.md 格式，需手动管理 |
| **Vercel AI SDK** | AI 应用开发框架 | 完整的数据流、streaming、工具调用 | 不涉及 UI 输出规范 |
| **shadcn/ui** | 组件库 | 高质量可定制组件 | 需要人工选择和组装 |
| **TailwindUI** | 官方设计系统 | 精美的生产级组件 | 授权费用，非 AI 原生 |
| **Magic UI** | 开源动画组件 | 免授权，可复制粘贴 | 偏向组件库，非行为规范 |

**Taste-Skill 是目前唯一一个系统性地解决「AI 前端油腻」问题的开源项目**，且研究深度（17k Stars 社区验证）远超其他方案。

---

## 6. 实战示例

### 6.1 基础使用

```bash
# 安装全部技能
npx skills add https://github.com/Leonxlnx/taste-skill

# 在 Claude Code/Cursor 中激活
# → 直接粘贴 SKILL.md 内容，或让 agent 自动发现

# 用户：做一个落地页
# Agent（激活 taste-skill 后）:
# → 自动用 Satoshi + Geist 字体
# → 禁用紫色渐变，用 Zinc/Emerald 色调
# → Split Screen 布局而非居中 Hero
# → 生成骨架屏 Loading + 完整 Empty/Error 状态
```

### 6.2 调整设计参数

```
用户：把这个页面改成高密度仪表盘风格
Agent：设置 VISUAL_DENSITY=8，DESIGN_VARIANCE=6
→ 卡片容器被 border-t 分组替代
→ 使用 grid 而非 flex 百分比计算
→ 数据指标呼吸感更强但信息密集
```

---

## 7. 局限性

1. **依赖 Agent 自觉遵守**：SKILL.md 是规范而非强制，Agent 可以忽略（虽然概率较低）
2. **技能版本管理**：更新 Skill 后需要重新安装，Agent 不会自动同步最新版本
3. **仅覆盖前端**：不涉及后端 API 设计、数据建模等后端领域
4. **Brutalist Skill 仍在 BETA**：`industrial-brutalist-ui` 为实验阶段
5. **学习曲线**：需要理解三围参数的含义才能有效调整

---

## 8. 总结

Taste-Skill 的核心洞察是：**AI 前端「油腻」不是审美问题，而是行为问题**。解决这个问题不能靠调模型参数，而是要在 prompt 层给出可操作的、经过实验验证的行为规范。

研究驱动的技能体系 + 细粒度的职责分工 + 完整的 remediation 层级，使其成为目前最系统的 AI 前端品位提升方案。随着 17k Stars 的社区积累和持续的版本迭代（2026-05-06 最新更新），Taste-Skill 有望成为 AI 编码 Agent 的标准配置。

**官网**: [tasteskill.dev](https://tasteskill.dev)
**GitHub**: [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill)
**赞助**: [GitHub Sponsors](https://github.com/sponsors/Leonxlnx)