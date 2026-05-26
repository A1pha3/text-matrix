+++
date = '2026-05-26T16:16:40+08:00'
draft = false
title = 'Taste Skill：给AI的前端注入「审美品味」，告别千篇一律的slop UI'
+++

# Taste Skill：给AI的前端注入「审美品味」，告别千篇一律的slop UI

## 概述

**Taste Skill** 是 Leonxlnx 开源的「AI前端反slop」工具集，通过一系列 Agent Skills 引导 AI 编程工具（Claude Code、Codex、Cursor 等）生成具有设计品味的前端界面，而不是流水线式的 boilerplate 产物。

GitHub: [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) ⭐ 20,015 | License: MIT

---

## 背景痛点

当 AI 帮你写前端代码时，常见的输出是：

- 居中的 sans-serif 文字
- 渐变按钮配 shadow
- 大量冗余 padding，千篇一律的卡片网格
- 毫无个性的「AI味」界面

这不是代码能力的问题，而是 **prompt 缺乏设计意图的传递机制**。Taste Skill 的出现就是为了解决这个问题——让 AI 不只是「能跑」，而是「好看」。

---

## 核心功能

### 1. 一套 Skills，多种风格覆盖

通过 `npx skills add` 安装，即可在 Claude Code / Codex / Cursor 中调用：

| Skill | 安装名 | 用途 |
|---|---|---|
| **taste-skill** (v2) | `design-taste-frontend` | 默认推荐，v2 实验版，含 VARIANCE / MOTION / DENSITY 三档可调节参数 |
| **taste-skill-v1** | `design-taste-frontend-v1` | 保守 v1，行为稳定，用于已依赖 v1 行为的项目 |
| **gpt-taste** | `gpt-taste` | 更严格的 GPT/Codex 规则，加强布局差异化和 GSAP 动画指导 |
| **image-to-code-skill** | `image-to-code` | 图生代码流水线：先生成参考图 → 分析设计语言 → 实现前端 |
| **redesign-skill** | `redesign-existing-projects` | 对已有项目进行 UI 审计后修复 |
| **soft-skill** | `high-end-visual-design` | 高端柔和风格：低对比度、大留白、Spring 动效 |
| **minimalist-skill** | `minimalist-ui` | Notion/Linear 风的编辑产品 UI |
| **brutalist-skill** | `industrial-brutalist-ui` | 瑞士印刷风格的硬核机械语言 |
| **output-skill** | `full-output-enforcement` | 强制完整输出，防止 AI 输出半成品 + 注释占位符 |

### 2. 三档可调节参数（v2 新增）

Taste Skill 的核心通过三个数字刻度控制输出风格：

- **DESIGN_VARIANCE** (1-10)：布局实验度
  - 低 → 居中、干净、经典
  - 高 → 非对称、现代、打破网格

- **MOTION_INTENSITY** (1-10)：动效深度
  - 低 → 悬停反馈
  - 高 → 滚动视差、磁吸效果、GSAP 骨架代码

- **VISUAL_DENSITY** (1-10)：单位视口信息密度
  - 低 → 留白充裕、呼吸感强
  - 高 → 数据密集型仪表盘

### 3. 图像生成技能（配合 ChatGPT Images 等）

| Skill | 安装名 | 用途 |
|---|---|---|
| **imagegen-frontend-web** | `imagegen-frontend-web` | 网站 Landing Page 含 hero、多分区排版、品牌级字体间距 |
| **imagegen-frontend-mobile** | `imagegen-frontend-mobile` | iOS/Android 移动端界面设计含 mockup |
| **brandkit** | `brandkit` | 品牌识别板：Logo 方向、色彩体系、字体系统 |

生成参考图后可直接喂给 Codex / Cursor / Claude Code 实现。

### 4. Google Stitch 兼容

`stitch-skill` 可导出标准 `DESIGN.md` 格式，无缝对接 Google Stitch 工作流。

---

## 安装使用

### 安装全部 skills

```bash
npx skills add https://github.com/Leonxlnx/taste-skill
```

### 安装单个 skill

```bash
npx skills add https://github.com/Leonxlnx/taste-skill --skill "design-taste-frontend"
```

也可以直接复制 `SKILL.md` 内容粘贴到 ChatGPT / Codex 对话中。

---

## 典型工作流：Image-to-Code

1. 在支持图像生成的 AI（ChatGPT Images / Codex image mode）中加载 `imagegen-frontend-web` skill
2. 生成 Landing Page 参考图（hero、multi-section、强字体层级）
3. 将图像发给 Codex / Cursor / Claude Code，同时加载 `image-to-code-skill`
4. AI 分析设计语言后直接实现完整前端

---

## 与 stop-slop 的区别

| 工具 | 定位 | 作用于 |
|---|---|---|
| **stop-slop** | Prompt skill 文本规则 | 去除 AI 文本输出的陈词滥调（hallmark 等） |
| **Taste Skill** | 前端设计指导框架 | 提升 AI 生成代码的视觉设计质量 |

两者互补——stop-slop 治理文字，Taste Skill 治理界面。

---

## 技术细节

- **语言**：Shell（Skill 文件为 Markdown，含 YAML frontmatter 元数据）
- **安装方式**：`npx skills add`（基于 Vercel Agent Skills 规范）
- **兼容性**：框架无关，React / Vue / Svelte 均可使用
- **License**：MIT，2026 年
- **官网**：https://tasteskill.dev

---

## 总结

Taste Skill 是目前 AI 前端开发工作流中设计质量控制最完整的开源方案。20K+ Stars 的社区认可证明了 AI 生成界面「不只是能跑」这个需求的真实存在。

**适合人群：**
- 使用 Claude Code / Codex / Cursor 做前端开发的工程师
- 希望 AI 生成的作品有一定设计感的独立开发者
- 追求「vibe coding」而非「boilerplate coding」的团队

**安装即用**，建议从 `design-taste-frontend`（v2 默认）开始体验。