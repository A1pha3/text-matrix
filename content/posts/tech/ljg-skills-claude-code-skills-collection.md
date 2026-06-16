---
title: "ljg-skills：李继刚的 Claude Code 技能集，19把刀锻造认知流水线"
date: "2026-05-14T16:20:00+08:00"
slug: "ljg-skills-claude-code-skills-collection"
description: "深入解析 lijigang/ljg-skills：一个包含19个 Claude Code 技能的个人工具箱，涵盖论文阅读、内容铸卡、写作引擎、概念解剖、投资分析等场景。剖析每个技能的定位、使用方式和串联逻辑，理解如何用 AI 工具锻造认知流水线。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "AI工具", "技能集", "工作流", "认知科学", "写作", "论文阅读"]
---

# ljg-skills：李继刚的 Claude Code 技能集，19 把刀锻造认知流水线

> **项目信息**：https://github.com/lijigang/ljg-skills | ⭐ 4,971 | TypeScript/HTML | Claude Code Skills

---

## 一、项目定位与设计思路

ljg-skills 是一个**个人工具箱**，作者李继刚为 Claude Code 打造了一套完整的技能体系。这个项目解决的是一个具体问题：**AI 对话是一次性的，但认知工作需要积累和复用**。

大多数人和 AI 对话后，产出物是一次性的——对话结束，AI 的"记忆"消失，下次重新开始。ljg-skills 的思路是把**可复用的认知工作流程封装成技能**，让 AI 在每次对话中都能调用经过深思熟虑的专用工具，而不是每次都从零开始摸索。

项目结构分两层：
- **技能（Skill）**：单个专用工具，解决一类认知任务
- **工作流（Workflow）**：多个技能串联，执行完整的高阶任务

安装方式极其简单（一行 npx 命令），支持 org-mode 和 Markdown 两种格式，分别面向 Emacs/Denote 用户和 Obsidian/VSCode 用户。

---

## 二、技能全景图

### 2.1 技能分类

| 类别 | 技能 | 一句话定位 |
|------|------|-----------|
| **阅读** | ljg-paper, ljg-paper-river, ljg-read | 论文 → 可用认知 |
| **写作** | ljg-writes, ljg-plain, ljg-qa | 观点 → 深度文章 |
| **卡片** | ljg-card | 内容 → PNG 视觉卡片 |
| **解剖** | ljg-learn, ljg-think, ljg-rank | 概念 → 顿悟 |
| **分析** | ljg-invest, ljg-relationship | 对象 → 判断 |
| **表达** | ljg-present, ljg-roundtable | 大纲 → 演讲/讨论 |
| **辅助** | ljg-word, ljg-travel, ljg-skill-map | 单词/旅行/技能盘点 |
| **工程** | ljg-push | 本地技能 → GitHub 同步 |

### 2.2 技能详解

#### ljg-card — 内容铸卡（视觉化）

将任意内容（URL / 文本 / 文件）转换为 PNG 视觉卡片。七种模具：

| 模具 | 尺寸 | 场景 |
|------|------|------|
| `-l`（默认） | 1080 x auto | 长图阅读卡 |
| `-i` | 1080 x auto | 信息图 |
| `-m` | 1080 x 1440 | 多卡（自动切分） |
| `-v` | 1080 x auto | 编辑式视觉笔记（问题→失败→转折→顿悟→命名） |
| `-c` | 1080 x auto | 日式黑白漫画风格 |
| `-w` | 1080 x auto | 白板马克笔风格 |
| `-b` | 1080 x 1440 | 碑刻大字（小红书附件风格） |

**设计哲学**：反 AI 生成痕迹。禁 Inter 字体、禁纯黑、禁三等分卡片、禁居中 Hero、禁 AI 文案腔。

#### ljg-paper — 论文阅读

为非学术人士提取论文核心想法，重理解不重批判。

**目标**：让一个不懂这个领域的聪明人读完笔记，能复述：
1. 论文在解决什么问题（具体到一个例子）
2. 作者用什么招数解的（机制 + 设计选择的理由）
3. 核心发现是什么（包括最反直觉的副发现）
4. 读者能带走什么洞见

**title 写作约束**（精髓）：
- 6-15 字，中文母语凝练
- 动词为骨，名词具体
- 自带张力：反直觉 / 对仗并置 / 转折反讽
- 不出现英文术语（RL / HR / Agent / token 等都不行）

**正例对照**：

| 论文核心 | ✗ 翻译腔 | ✓ 中文凝练 |
|----------|---------|-----------|
| 奖励信号把模型锁在已会轨迹里 | 奖励信号会把模型锁死在已会的轨迹里 | 学会，反成枷锁 |
| 只用错样本做 RL，反思能力自己长出来 | 只用错样本做 RL，反思能力自己长出来 | 错处长出反省 |
| 多智能体缺的是组织协调而非个体智能 | Multi-agent 缺的不是聪明，是 HR | 多智不如善织 |
| 老师与学生看待问题角度不同导致教学失败 | 老师比学生高分还教不会 | 高分难为师 |

#### ljg-paper-river — 论文溯源

倒读法，递归挖前序论文（最多 5 层）+ 最新进展，从源头讲述问题演化史。

不是顺着读（从摘要到方法到结论），而是倒着读（这篇论文引用了谁的工作？那个工作又引用了谁？）。最终呈现的是一条问题演化的历史脉络。

#### ljg-learn — 概念解剖

从八个方向切开一个概念：
1. **历史**：最早从哪冒出来 → 怎么变的 → 哪一步拐成了今天的意思
2. **辩证**：它的反面是什么 → 正反碰撞后的更高理解
3. **现象**：扔掉所有预设，回到事情本身，用日常场景还原
4. **语言**：拆字源（中/英/希腊/拉丁）→ 相邻概念的语义网
5. **形式**：写一个公式或形式化表达 → 公式在哪里失效
6. **存在**：这个概念改变了人怎么活着
7. **美感**：它美在哪？用一个具体意象呈现
8. **元反思**：我们在用什么隐喻理解它？这个隐喻挡住了什么？

最终压缩成一句顿悟。

#### ljg-writes — 写作引擎

像手术刀剖开一个观点，一层层剥到底。1000-1500 字。

**核心约束**：
- 心里放一个具体的人，写给他，不写给「读者们」
- 先亮自己的弯路，再给方向——说服力来自你先错过
- 不确定就说不确定。「大概 70%」比「可能」诚实
- 不借势：不用群体代言（「程序员都知道」），不编造经历
- *不自标深度*：禁用「再深入一层」「最深的一层是」

**三刀写作法**：
1. **切第一刀**：问它底下是什么？切出一个读者没看见的层
2. **切第二刀**：刚剖出的那层，再往下一层（不重复第一刀）
3. **切到底**：直到切不动，诚实说「不确定」也是一种底

#### ljg-plain — 白话引擎

把任何内容改写到聪明的十二岁小孩也能懂。

#### ljg-invest — 投资分析

核心判断：项目是否是一台「秩序创造机器」。

#### ljg-qa — 信息提问机

把文章/论文/书的核心观点抽成 Q-A 链。Q 切要害，A 四段（结论 / 形式化 / 步骤 / 边界）。

#### ljg-think — 追本之箭

给一个观点或现象，纵向深钻到不可再分的本质。

#### ljg-rank — 降秩引擎

给一个领域，找出背后不可再少的独立生成器。

#### ljg-relationship — 关系分析

五层结构诊断 + 精神分析，通过对话引导帮用户"看见"关系真实结构。

#### ljg-roundtable — 圆桌讨论

求真导向的结构化多人辩证对话，每轮生成 ASCII 思考框架图。

#### ljg-present — 演讲铸造器

基于 orgmode outline 层级 1:1 视觉化呈现——色块大字、ultra-bold 错位。

**核心哲学**：Outline 是真理，Skill 是渲染器。不改内容，只改呈现。

三档主题色：black / red / yellow（默认 black 或按 filetags 推断）。可用 -r / -b / -y 覆盖。

视觉语言参考 Felipe Franco / BIG STUDIOS 的 manifesto 美学：
- 整篇一个主题色
- left-aligned 舞台美学
- 超大字 ultra-bold（单字 70vmin、长句 11vmin）
- 多行错位（按 outline 嵌套深度）

#### ljg-read — 伴读

陪你读任何文本，英文三层翻译（信达雅）+ 结构标注 + 深度提问 + 跨领域旁逸。

#### ljg-word — 单词精通

深度拆解一个英语单词的核心语义和顿悟时刻。

#### ljg-travel — 旅行研究

输入城市名，生成深度文化研究文档（org-mode）+ 便携卡片（PNG）。

#### ljg-skill-map — 技能地图

扫描所有已安装技能，渲染可视化总览。

#### ljg-push — 推送引擎

把本地 `~/.claude/skills/ljg-*` 一键同步到 GitHub（master + md 双分支）。

---

## 三、工作流：技能串联

| 工作流 | 技能链 | 说明 |
|--------|--------|------|
| **ljg-paper-flow** | ljg-paper → ljg-card -c | 读论文 + 做漫画卡片一气呵成 |
| **ljg-word-flow** | ljg-word → ljg-card -i | 单词深度分析 + 信息图卡片一气呵成 |

---

## 四、安装与使用

### 4.1 一键安装

```bash
# 安装全部技能（全局，org-mode 格式）
npx skills add lijigang/ljg-skills -g --all

# 安装全部技能（Markdown 格式）
npx skills add lijigang/ljg-skills#md -g --all

# 安装单个技能
npx skills add lijigang/ljg-skills -g --skill ljg-card

# 查看仓库中有哪些技能
npx skills add lijigang/ljg-skills -l
```

### 4.2 替代方式：git clone

```bash
# org-mode 版本
git clone https://github.com/lijigang/ljg-skills.git ~/.claude/plugins/ljg-skills

# Markdown 版本
git clone -b md https://github.com/lijigang/ljg-skills.git ~/.claude/plugins/ljg-skills
```

### 4.3 ljg-card 依赖

```bash
cd ~/.claude/skills/ljg-card && npm install && npx playwright install chromium
```

---

## 五、设计哲学总结

### 5.1 核心原则

1. **工具即认知**：用 AI 重新设计认知工作的流程，而非加速已有流程
2. **专门优于通用**：每个技能只解决一类问题，但解决得很深
3. **积累优于一次性**：技能封装了工作流程，可以在多次对话中复用
4. **输出物优先**：最终产出是可见的（PNG / 文章 / 卡片），不是对话记录

### 5.2 与传统工具的区别

| 维度 | 传统工具 | ljg-skills |
|------|----------|-----------|
| 论文阅读 | 手动整理笔记 | ljg-paper → 结构化认知卡片 |
| 内容可视化 | 手动设计 + 截图 | ljg-card → PNG 一键输出 |
| 概念理解 | 碎片化搜索 | ljg-learn → 八维解剖 |
| 写作 | 空白文档从零写 | ljg-writes → 手术刀分层 |
| 演讲准备 | PowerPoint 从零做 | ljg-present → Outline 1:1 渲染 |

---

## 六、相关链接

- GitHub：https://github.com/lijigang/ljg-skills
- Claude Code 文档：https://docs.anthropic.com/en/docs/claude-code
- Skills CLI：https://github.com/vercel-labs/skills