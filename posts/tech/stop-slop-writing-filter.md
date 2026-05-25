---
title: "Stop Slop：给 AI 写作去除"AI味"的技能文件"
date: "2026-05-25T20:08:27+08:00"
slug: "stop-slop-remove-ai-writing-patterns"
description: "Stop Slop 是一个开源技能文件，帮助 LLMs 识别并移除 AI 写作中的常见模式——包括废话开头、强调癖、呆板结构等。本文解析其检测机制和用法。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "写作", "Prompt", "LLM", "去AI味"]
---

# Stop Slop：给 AI 写作去除"AI味"的技能文件

Stop Slop 是一个专门针对 AI 写作风格的技能文件（Skill File），由 Hardik Pandya 开发。其核心功能是教会大语言模型识别并移除 prose（散文/正文）中的 AI 特征——那些让文字读起来"太像 AI 写的"的模式和结构。

项目目前获得 4,153 颗 Stars，License 为 MIT，可以免费使用。

## 核心问题

AI 生成的文字有一种可辨识的质感：开头总是"当然""当然，这里有一个…"；结构上喜欢"首先…其次…最后…"的排比；充满"重要的是""值得注意的是"这类元话语；充斥着加强语气的副词和极端表述。

Stop Slop 认为这些问题是可以被系统性地识别和修复的。

## 检测维度

项目从三个层面检测 AI 写作模式：

### 短语层面（Banned Phrases）

AI 喜欢用的废话开头和加强语气词，包括：

- 废话开场白（Throat-clearing openers）
- 强调癖（Emphasis crutches）——"非常重要的""极其关键的"
- 商业黑话（Business jargon）
- 所有副词（Adverbs）
- 模糊声明（Vague declaratives）
- 元评论（Meta-commentary）——"值得注意的是""值得注意的是"

完整列表在 `references/phrases.md` 中维护。

### 结构层面（Structural Clichés）

AI 偏好的固定句式和结构：

- 二元对比（Binary contrasts）——"不是 A 而是 B"
- 负面列表（Negative listings）——"不是 X，不是 Y，而是 Z"
- 戏剧性碎句（Dramatic fragmentation）
- 修辞铺垫（Rhetorical setups）
- 虚假主动性（False agency）
- 被动语态滥用
- 长叙述距离感（Narrator-from-a-distance voice）

完整列表在 `references/structures.md` 中维护。

### 句法层面（Sentence-level Rules）

- 禁止 Wh- 疑问句开头（Who、What、When 等）
- 禁止使用 em dash（——）
- 禁止短促碎句
- 禁止极端化表述（"从来没有""绝对""完美的"）
- 必须使用主动语态

## 评分体系

Stop Slop 提供一套 1-10 分的评分维度，帮助判断文字是否需要重写：

| 维度 | 评估问题 |
|------|----------|
| 直接性（Directness） | 是陈述句/宣告句，还是铺垫句？ |
| 节奏（Rhythm） | 句式多变，还是像节拍器一样机械？ |
| 信任（Trust） | 是否尊重读者智商？ |
| 真实性（Authenticity） | 读起来像人写的吗？ |
| 密度（Density） | 有没有可以删掉的内容？ |

总分 50 分，低于 35 分建议重写。

## 使用方式

**Claude Code 用户：** 直接将整个文件夹作为 skill 添加到项目中。

**Claude Projects 用户：** 将 `SKILL.md` 和 reference 文件上传到项目知识库。

**自定义指令：** 从 `SKILL.md` 中复制核心规则，粘贴到自己的 system prompt 中。

**API 调用：** 在请求时将 `SKILL.md` 内容包含在 system prompt 中，reference 文件按需加载。

## 项目结构

```
stop-slop/
├── SKILL.md              # 核心指令
├── references/
│   ├── phrases.md        # 需要移除的短语列表
│   ├── structures.md      # 需要避免的结构模式
│   └── examples.md       # 改写前后示例
├── README.md
└── LICENSE
```

## 典型改写示例

AI 原文：

> 当然，让我们深入探讨一下这个非常重要的话题。首先，我们需要明确……其次，我们还应该注意到……最后，综上所述，我们可以得出结论——

改写后：

> 这个话题值得认真讨论。先说清楚前提，再说具体做法，结论自己会浮出来。

## 局限性

Stop Slop 是一个基于规则的检测系统，对抗的是 AI 写作的统计特征，不是真正的语义质量提升。如果原始内容本身信息量不足，去 AI 味后的文字会更明显地暴露这一点——问题不在风格，在内容。

---

*本文档基于 GitHub 仓库 2026 年 5 月最新信息编写，Stars：4,153，License：MIT。*