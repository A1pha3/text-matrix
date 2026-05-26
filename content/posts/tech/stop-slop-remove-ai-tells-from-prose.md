---
title: "stop-slop：给 AI 写作去味，让 Claude 写出更像人写的东西"
date: 2026-05-26T09:40:00+08:00
slug: "stop-slop-remove-ai-tells-from-prose"
description: "stop-slop 是一个让 AI 文字去掉\"AI腔\"的 skill 文件，通过禁止高频套话、修正机械句式、替换结构模板等手段，让 Claude 等大模型输出的文字更像人类写作，适合对文字质感有要求的技术写作者。"
draft: false
categories: ["技术笔记"]
tags: ["AI Writing", "Claude", "Prompt Engineering", "文字质量", "Skill"]
---

# stop-slop：给 AI 写作去味，让 Claude 写出更像人写的东西

**一句话判断：stop-slop 不是一个帮你写作的工具，而是一个教 AI 戒掉写作习惯的工具——把\"显然可以看出\"换成具体判断，把\"让我们深入探讨\"直接删掉。**

---

## 这个 skill 在解决什么问题

用 Claude 或 ChatGPT 写过技术文档的人大概都有一个感受：内容对了，但读起来哪里不对。

问题不在信息，在于文字本身带着一种"AI腔"：开头先说"让我们先来看"，结尾再来个"综上所述"，中间每隔几段就来一句"值得注意的是"。这些不传递信息的套话让文章听起来像是在背诵模板，而不是在交流。

stop-slop 就是针对这个问题的解决方案。它以 Anthropic Claude Code 的 skill 文件形式存在，核心思路是：**不是教 AI 怎么写，而是告诉 AI 哪些写法必须戒掉。**

---

## skill 结构

```
stop-slop/
├── SKILL.md              # 核心规则
├── references/
│   ├── phrases.md        # 禁止短语清单
│   ├── structures.md      # 禁止句式清单
│   └── examples.md        # 改写前后对比
└── README.md
```

结构很薄，核心内容全在 `SKILL.md` 的规则集里。`references/` 目录负责存放具体的黑名单——这些是 skill 运行时调用的规则库。

---

## 它检测什么

### 第一类：套话短语

throat-clearing openers、emphasis crutches、business jargon、adverbs、vague declaratives、meta-commentary。

这些是读者一眼就能认出来的"AI 味"信号词。具体词表见 `references/phrases.md`。

### 第二类：结构性模板

- binary contrasts（"不是 A 而是 B"式二段论）
- negative listings（"我们需要 X，我们还需要 Y"）
- dramatic fragmentation（故意拆分短句制造节奏感）
- rhetorical setups（自问自答式设问）
- passive voice（被动语态滥用）

### 第三类：句子级规则

- 禁止 Wh- 句式开头（What/Why/How/When 开头）
- 禁止 em dash（——）过度使用
- 禁止无意义的短句堆叠
- 必须用主动语态
- 禁止 lazy extremes（"完美的""无与伦比的"这类夸张词）

---

## 评分维度

skill 提供了一个 1-10 分的评分框架，维度如下：

| 维度 | 问题 |
|------|------|
| Directness | 内容是直接陈述还是在绕圈子 |
| Rhythm | 句子长短是否有变化，还是在打节拍 |
| Trust | 有没有在假设读者需要被告知显而易见的事 |
| Authenticity | 读起来像人写的还是像模型输出的 |
| Density | 有没有可删掉的废话 |

总分低于 35/50 的建议修改。

---

## 如何使用

### Claude Code

把 `stop-slop` 文件夹添加为 skill，直接在项目里调用。

### Claude Projects

上传 `SKILL.md` 和 `references/` 下的文件到项目知识库。

### 自定义指令

把 `SKILL.md` 里的核心规则复制到自己的 system prompt 里。

### API 调用

把 `SKILL.md` 全文放进 system prompt，references 文件按需挂载。

---

## 适合谁用

- 技术写作者：用 Claude 辅助写作，但希望最终文字质量接近手写
- 内容团队：想把 AI 生成的内容从"60 分"拉到"80 分"
- 文档工程师：需要产出发布级文字，不想让读者看出是 AI 写的

**不适合：**
- 法律、医学、学术论文等需要严格客观表述的文档
- 只需要快速草稿、不在乎文风的内部备忘

---

## 在趋势榜中的位置

stop-slop 登上了今天的 GitHub trending（4.4k Stars），说明市场对"AI 味去化"工具的需求在持续增长。

同类方向的项目还有 [taste-skill](https://github.com/Leonxlnx/taste-skill)（19.7k Stars），后者更侧重给 AI 编程工具注入品味，而 stop-slop 专注于文字写作场景。两者可以配合使用——taste-skill 解决代码输出质感，stop-slop 解决文档文字质感。

---

*skill 文件 MIT 协议，可以自由使用和改进。*