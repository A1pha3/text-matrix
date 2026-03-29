---
title: "AI Agent 的道与术：工程师如何重构工作方式"
date: 2026-03-29T08:00:00+08:00
slug: "ai-agent-engineer-workflow"
description: "深入解读 onevcat/2026-let-s-vision 演讲项目，探讨 AI Agent 时代工程师如何重构工作方式，涵盖人机协作的道与术、Slidev 制作流程、AI 驱动制作工作流等核心实践。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Slidev", "工程师", "工作方式", "AI协作"]
---

# AI Agent 的道与术：工程师如何重构工作方式

> 一文读懂 onevcat/2026-let-s-vision 演讲项目

**学习目标**

学完本文后，你将掌握：
- 理解 AI Agent 时代工程师工作方式的核心转变
- 了解人机协作的"道"与"术"之分
- 掌握如何用 AI 工具（Claude Code、Slidev）高效制作技术演讲
- 学会建立"页面→演讲备注→观点来源"的追踪映射
- 能够复现这套基于 Agent 的 Slide 制作工作流

---

## 一、项目概述

### 1.1 是什么

[onevcat/2026-let-s-vision](https://github.com/onevcat/2026-let-s-vision) 是 Let's Vision 26 上海分享的演讲稿仓库，主题为"**AI Agent 时代下，工程师如何重构工作方式**"。

作者 onevcat（Wei Wang）是知名iOS/Android开发者和开源贡献者（拥有多个知名开源项目如 Kingfisher）。

### 1.2 核心价值

这个仓库的特殊之处在于**它不仅仅是一个演讲幻灯片，更是一个完整的 AI 协作实验记录**。

| 组成部分 | 说明 |
|-----------|------|
| Slidev 源码 | 完整的演讲幻灯片源代码 |
| 原始研究材料 |观点池、早期结构规划、引用与依据、完整讲稿笔记 |
| AI 协作 trace | 与 AI 协作的完整对话记录 |
| 设计迭代记录 | 多轮设计批评与修正决策 |
| 自动化工具 | 提取 speaker notes、生成索引的脚本 |

### 1.3 在线资源

- **PDF 版本**：[2026-vision.pdf](https://github.com/onevcat/2026-vision/releases/download/release/2026-vision.pdf)
- **在线浏览**：[let-s-vision-2026.onev.cat](https://let-s-vision-2026.onev.cat/)

---

## 二、核心概念：道与术

### 2.1 什么是"道"

"道"是**原理和思想**，回答"为什么"的问题。在 AI Agent 时代：

- **约束（Constraints）**：在 AI 时代，约束条件发生了什么变化？哪些边界依然有效？
- **协作（Collaboration）**：人与 AI Agent 如何分工？各自擅长什么？
- **落地（Implementation）**：如何在工程团队中真正实践这些方法？

### 2.2 什么是"术"

"术"是**具体的执行方法和工具**：

- 如何用 AI 辅助写代码？
- 如何用 AI 辅助做演讲？
- 如何建立高效的 AI 工作流？
- 如何迭代 AI 生成的内容？

### 2.3 道与术的关系

> 光有"术"没有"道"，是瞎干；光有"道"没有"术"，是空谈。

本文的核心观点：**在 AI Agent 时代，工程师需要同时掌握"道"与"术"，才能真正重构工作方式**。

---

## 三、仓库结构详解

### 3.1 目录概览

```
2026-let-s-vision/
├── .agents/skills/          # Agent 相关技能
├── .baoyu-skills/           # 宝玉文章插图技能
│   └── baoyu-article-illustrator/
├── .claude/skills/          # Claude 专用技能
├── components/               # React 组件
├── design-fix/              # 设计迭代记录
│   └── critique-report.md   # 设计批评报告
├── output/prompts/          # 输出提示词
├── public/                  # 静态资源
├── resources/               # 研究材料
│   ├── points.md            # 观点池
│   ├── slide-overview.md    # 早期结构规划
│   ├── references.md        # 引用与依据
│   └── 2026-03-shanghai-ai-agent-talk-notes.md  # 完整讲稿笔记
├── scripts/                 # 工具脚本
│   ├── extract-notes.py     # 提取 speaker notes
│   └── slide-index.sh       # 生成页码索引
├── skills/                  # 通用技能
├── CLAUDE.md               # Claude 配置
├── slides.md               # Slide 内容
└── package.json            # 依赖配置
```

### 3.2 核心文件解析

#### `resources/` — 研究的起点

| 文件 | 内容 |
|------|------|
| `points.md` | 观点池，收集了所有可能被纳入演讲的观点 |
| `slide-overview.md` | 早期结构规划，确定演讲的整体框架 |
| `references.md` | 所有引用和依据，确保内容有据可查 |
| `2026-03-shanghai-ai-agent-talk-notes.md` | 完整的讲稿笔记 |

这些文件展示了**一个演讲是如何从零开始构建的**，每个观点都经过了筛选和排列。

#### `design-fix/` — 迭代的痕迹

设计迭代是演讲制作中最容易被忽视但最重要的部分。

`critique-report.md` 记录了**从反模式识别到色彩语义、信息密度、页面差异化等问题的逐轮收敛过程**。

阅读这个文件，你可以学到：
- 如何接受批评并转化为改进行动
- 设计如何在迭代中逐步完善
- 哪些设计决策是最关键的

#### `scripts/` — 工具的力量

| 脚本 | 功能 |
|------|------|
| `extract-notes.py` | 从 slides.md 提取每页 speaker notes、click 结构和页级元数据（JSON） |
| `slide-index.sh` | 生成页码/行号范围/layout/title 的快速索引，便于定位与审校 |

### 3.3 技术栈

| 技术 | 用途 |
|------|------|
| **Slidev** | 幻灯片框架，基于 Vue 3 |
| **Python** | 脚本编写，占 71.5% |
| **Vue** | 组件开发，占 24.6% |
| **Shell** | 构建脚本，占 2.1% |
| **JavaScript/TypeScript** | 少量配置 |

---

## 四、AI 驱动制作流程

### 4.1 工作流概览

这个演讲采用了**"人设方向 + AI 辅助迭代"**的工作流：

```
想法 → AI 辅助内容重写 → AI 辅助结构重排 → 视觉风格收敛 → 多轮审阅修正
```

### 4.2 每一步详解

#### 第一步：内容重写

将原始想法用 AI 辅助扩展成完整的段落或演讲稿。AI 可以帮助：
- 扩展粗糙的想法为完整的论述
- 提供多个角度的论证
- 补充具体的例子和类比

#### 第二步：结构重排

将内容打散，按照逻辑重新组织。AI 可以帮助：
- 识别内容之间的逻辑关系
- 建议更好的组织方式
- 找出遗漏的重要观点

#### 第三步：视觉风格收敛

确定整体视觉风格，包括：
- 色彩方案
- 排版规范
- 图表样式
- 动画效果

#### 第四步：多轮审阅修正

通过多轮"批评→修改"循环，让内容越来越完善。每一轮都会有新的发现和改进口。

### 4.3 给 Agent 的直接可用提示词

仓库提供了一个可以直接喂给 Agent 的提示词，让 AI 帮你快速了解所有细节：

```
请你完整研究这个 repo（https://github.com/onevcat/2026-vision），并输出一份结构化分析报告。要求：
1) 提炼这套演讲的核心思想：主问题、核心结论、"道"与"术"、可观察和落地的启发
2) 对比 slides 最终内容与仓库中的"未完全发布内容"：resources/、design-fix/ 中的关键取舍
3) 基于 scripts/ 工具给出可复现的方法：如何提取 speaker notes、如何建立追踪映射
4) repo 中有哪些 skill，它们能使用在我自己的项目或者智能体中么？
5) 最后给出一份"观众扩展阅读路径"（按 30 分钟 / 2 小时 / 半天三个时间预算）
```

---

## 五、实战：本地构建

### 5.1 环境准备

```bash
# 克隆仓库
git clone https://github.com/onevcat/2026-let-s-vision.git
cd 2026-let-s-vision

# 安装依赖
pnpm install
```

### 5.2 常用命令

```bash
# 开发模式（热重载）
pnpm dev

# 构建生产版本
pnpm build

# 导出为 PNG 图片
pnpm export:png

# 导出为 PDF
pnpm export
```

### 5.3 提取 Speaker Notes

如果你想研究这个演讲的完整讲稿，可以使用：

```bash
# 提取所有 speaker notes
python scripts/extract-notes.py
```

这会生成一个 JSON 文件，包含每页的：
- Speaker notes 内容
- Click 结构
- 页级元数据

### 5.4 生成索引

```bash
# 生成快速索引
bash scripts/slide-index.sh
```

生成的内容包含：
- 页码
- 行号范围
- Layout 信息
- Title

---

## 六、扩展阅读路径

### 6.1 30 分钟速览

适合时间紧迫的读者：

1. 阅读 README 的核心介绍
2. 浏览 slides.md 的前 10 页
3. 阅读 critique-report.md 的摘要部分

### 6.2 2 小时深度阅读

适合想要系统学习的读者：

1. 完整阅读 PDF 版本演讲稿
2. 研究 resources/ 中的观点池和结构规划
3. 阅读 design-fix/ 中的关键设计决策
4. 实践本地构建命令

### 6.3 半天深入研究

适合想要完全复现这套方法的读者：

1. 完成 2 小时路径的所有内容
2. 深入研究 scripts/ 中的工具实现
3. 阅读完整的 AI 协作 trace
4. 尝试用自己的主题复现这个工作流
5. 研究 skills/ 中的各种技能，看是否能应用到自己项目

---

## 七、关键启发

### 7.1 对工程师的启发

1. **AI 是工具，不是替代者**：最有价值的不是 AI 本身，而是知道如何使用 AI 的人
2. **迭代优于完美**：不要追求一次到位，通过多轮迭代可以接近完美
3. **记录过程很重要**：保留 AI 协作的 trace，有助于复盘和学习
4. **工具需要配套**：单独的工具有限，但工具链可以释放巨大生产力

### 7.2 对团队的启发

1. **建立共享的 AI 工作流**：团队成员可以复用彼此的 AI 协作经验
2. **批评与自我批评并行**：design-fix/ 的思路可以应用于代码审查
3. **工具自动化**：重复性工作应该被脚本化

### 7.3 对个人品牌的启发

onevcat 通过这个项目展示了：
- 如何用 AI 工具提升个人生产力
- 如何将工作过程转化为可分享的内容
- 如何建立自己在某个领域的专业影响力

---

## 八、常见问题

### Q: 这个项目适合完全没有 AI 经验的工程师吗？

A: **可以**，但建议先了解基本的 AI 工具使用方法（如 Claude Code、ChatGPT 等）。对 AI 有基本认知后，再来学习这套方法论会事半功倍。

### Q: 必须使用 Slidev 吗？

A: 不是的。Slidev 是这个项目选择的工具，但核心的工作流（内容→结构→视觉→迭代）适用于任何演示文稿工具。

### Q: 如何将这些方法应用到我的工作中？

A: 建议从最小可行的方法开始：
1. 先用 AI 辅助写一个小的技术文档
2. 用这个项目的提示词让 AI 帮你分析你的工作内容
3. 逐步建立自己的 AI 工作流

### Q: 如何获取更多关于 onevcat 的信息？

A: 可以关注他的 GitHub 主页和社交媒体，他经常分享关于 AI 工具使用的经验和技巧。

---

## 九、总结

onevcat/2026-let-s-vision 不仅仅是一个技术演讲，更是一个**完整的 AI 协作实验**。

通过这个项目，你可以学到：

- **"道"的层面**：AI Agent 时代工程师应该如何思考和工作
- **"术"的层面**：如何用具体的工具和方法实现这些想法
- **"器"的层面**：如何选择和组合工具来提升生产力

**核心 takeaway**：在 AI 时代，最重要的能力不是"会用 AI"，而是"知道在哪里用 AI"以及"如何与 AI 协作"。

---

## 十、资源链接

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/onevcat/2026-let-s-vision |
| PDF 版本 | https://github.com/onevcat/2026-vision/releases/download/release/2026-vision.pdf |
| 在线浏览 | https://let-s-vision-2026.onev.cat/ |
| 作者 GitHub | https://github.com/onevcat |
| Slidev 官网 | https://sli.dev/ |
