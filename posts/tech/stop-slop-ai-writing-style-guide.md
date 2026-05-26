---
title: "stop-slop：一个专门消除AI写作腔的Skill文件"
date: "2026-05-25T23:05:00+08:00"
slug: "stop-slop-ai-writing-style-guide"
description: "stop-slop 是一个开源 Skill，通过禁用特定短语、结构模板和句式规则来去除AI生成文本中的「AI腔」（AI tells）。作者为 Hardik Pandya，采用 MIT 许可证。本文深入解析其设计逻辑与使用方法。"
draft: false
categories: ["技术笔记"]
tags: ["AI写作", "提示工程", "Claude", "自然语言处理", "写作风格"]
---

## 什么是 stop-slop

AI 生成的内容有个问题：太像 AI 说的。短语固定、节奏均匀、结构对称，一眼就能认出来。stop-slop 干的就是这件事——把这个识别模式提取成规则，让模型学会主动去掉这些痕迹。

项目主页在 [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop)，以 Skill 文件形式提供，可直接接入 Claude Code、Claude Projects 或任意 LLM API 的 system prompt。

```plaintext
stop-slop/
├── SKILL.md              # 核心指令
├── references/
│   ├── phrases.md        # 禁用短语清单
│   ├── structures.md     # 禁用结构模式
│   └── examples.md       # 改写前后对照
├── README.md
└── LICENSE               # MIT
```

核心思路是把「AI腔」分成三个层次逐层清除：**词面**（特定短语）→ **句式**（结构模板）→ **节奏**（段落层面的固定套路）。

---

## 禁用短语：别再这么说了

phrases.md 列出了五类需要从文本中剔除的短语。

### 开头语（Throat-clearing openers）

这类短语出现在句首，没有任何信息量，只是为了「引出正题」。典型代表：

- "It's important to note that..."
- "It's worth noting that..."
- "It's worth mentioning that..."
- "It's interesting to note..."

中文对应的磨叽开场同样在禁用范围内：「值得注意的是……」「需要指出的是……」「值得注意的是……」。

### 强调词（Emphasis crutches）

用来强调某事重要、紧急或无可辩驳，但实际没有提供任何新信息的词：

- "very", "really", "quite", "basically", "actually"
- "definitely", "certainly", "absolutely"

这些词的真实功能是给不确定的内容壮胆。删掉之后，句子反而更有力。

### 商业术语（Business speak）

办公室里常见的黑话，在技术文档中格外刺眼：

- "leverage", "synergy", "holistic", "robust", "scalable"
- "game-changer", "paradigm shift", "cutting-edge"

### 副词（Adverbs）

这是一个激进的立场：stop-slop 认为大多数副词都是可以删除的冗余修饰。`-ly` 结尾的词几乎全部在列。理由很简单——主动语态的动词远比副词+动词的组合更有力度。

### 模糊陈述（Vague declaratives）

听起来斩钉截铁、实际上什么都没说的句子：

- "The results speak for themselves."
- "It's safe to say..."
- "It's clear that..."
- "As you can see..."

### 元评论（Meta-commentary）

作者跳出来解释自己在做什么，而不是直接做：

- "In this section, we will explore..."
- "To summarize..."
- "As mentioned earlier..."

---

## 结构陈词滥调：别再这么搭了

structures.md 针对的是比单词更高一层的组织模式。这些模式单独看都没问题，但在 AI 文本中扎堆出现就成了暴露信号。

### 二元对比（Binary contrasts）

「不是 A 就是 B」「X 和 Y 本质上不同」这类强制对立。看多了就腻：

> "Unlike traditional approaches, our method..."

这种「vs 句式」在 AI 文本里密集出现，是因为模型倾向于用对立来制造戏剧感。

### 负面列表（Negative listings）

「我们不做什么、不会什么、不是什么」。列表本身没问题，但 AI 喜欢在列表前加一段宏大叙事，然后用负面清单收尾，形成一种「高开低走」的结构。

### 戏剧性碎片化（Dramatic fragmentation）

短句堆叠制造节奏感。单独看很有力，但 AI 文本里高频出现就成了模板：

> "The data was clear. The results were undeniable. Action was necessary."

### 修辞设置（Rhetorical setups）

先铺垫，再给出结论。铺垫越来越长，结论越来越短。AI 文本里常见的是用一个超长的背景句引出一个理所当然的结论。

### 虚假代理（False agency）

把明明是模型生成的内容伪装成某个角色的声音：

> "According to our analysis..."

其实并没有「我们的分析」，这只是模型在模拟一个不存在的权威来源。

### 被动语态（Passive voice）

要求用主动语态替代。不只是因为被动语态「不好」，而是因为 AI 文本中被动语态出现频率异常高，是识别信号之一。

---

## 句级规则：逐条卡死

SKILL.md 给出了一些精确到标点的规则，无法靠正则简单替换，需要在写作层面遵守。

| 规则 | 说明 |
|------|------|
| 禁止 Wh- 开头 | 不要用 "What...", "Why...", "How..." 开头。它们天然具有「引入下文」的结构，AI 喜欢用来做转场。 |
| 禁止 em dash (—) | AI 文本中 em dash 的使用频率远高于人类写作。禁用可以有效打散节奏。 |
| 禁止短促碎片化 | 不要连续用三个以下单词的短句。碎片化本身不是问题，但连续出现就成了信号。 |
| 禁止 lazy extremes | 「最糟糕的」「最理想的」「绝对」这类词。用具体的数字和条件替代。 |
| 强制主动语态 | 所有句子尽量用主动语态。被动语态只在真正必要时使用。 |

这些规则里，em dash 最有意思——它本身没问题，但「AI 用了大量 em dash」这件事是个统计事实。禁止它不是否定这个标点，而是对统计异常的响应。

---

## 五维评分：给文本打分

stop-slop 提供了一套评分机制，从五个维度评估文本的「人味儿」：

| 维度 | 评估问题 |
|------|------|
| Directness（直接性） | 是陈述句还是宣布句？ |
| Rhythm（节奏） | 句长是否多样？ |
| Trust（信任感） | 是否尊重读者智商？ |
| Authenticity（真实感） | 听起来像人写的吗？ |
| Density（密度） | 有没有可以删掉的内容？ |

每个维度 1-10 分，满分 50。**总分低于 35 的文本需要修改。**

这个评分体系的逻辑和 AI 检测工具不同——它不是判断「这段文字是不是 AI 写的」，而是判断「这段文字读起来像不像人写的」。两者的区别在于：前者可以被对抗，后者更接近真实的写作质量。

---

## 使用方式：怎么接入

stop-slop 作为 Skill 文件，有以下几种接入方式：

**Claude Code**

把整个文件夹作为 skill 目录加入即可。Claude Code 会自动读取 SKILL.md 和 references 目录。

**Claude Projects**

上传 SKILL.md 和 references 下的三个文件到项目知识库中。模型会在需要时按需加载。

**自定义指令（Custom instructions）**

将 SKILL.md 中的核心规则复制到 system prompt 中，适合在 API 调用场景使用。references 文件则按需引用。

**API system prompt**

直接把 SKILL.md 内容放进 system prompt，配合 references 文件做按需加载。这是让任意 LLM 都获得这套规则的最简方式。

---

## 效果示例

以下是从 examples.md 中提取的对照案例。原文左侧为「AI腔」版本，右侧为通过 stop-slop 改写的版本。

**禁用短语：**

> 原文：It is worth noting that this approach is very robust and scalable.
> 改写：This approach is robust and scalable.

> 原文：In conclusion, we can definitely say that the results are very promising.
> 改写：The results are promising.

**禁用结构：**

> 原文：Unlike traditional systems, our solution doesn't suffer from latency issues. It doesn't require complex configuration. And it certainly doesn't break in production.
> 改写：Our solution has low latency, needs no complex configuration, and runs reliably in production.

**句级改写：**

> 原文：What this means for you is that you can now deploy faster.
> 改写：You can deploy faster.

> 原文：The data was compelling. The team was convinced. The launch proceeded.
> 改写：The compelling data convinced the team to proceed with the launch.

---

## 限制与边界

stop-slop 是一套规则，不是一套理论。它的有效性建立在「AI 文本中这些模式出现频率更高」这个统计事实之上。如果你写的内容确实需要这些结构（比如学术论文的特定格式要求），按规则硬删就会损害表达的准确性。

使用时应该把它当作**修改的起点而非终点**。评分低了改，改完再评，直到既去掉 AI 腔、又保留必要信息。

这套规则的另一个局限在于它是面向英文的。中文的 AI 腔检测需要单独建模，短语、结构、句式的对应关系并不能直接映射。这个问题目前没有现成的解决方案。

---

## 总结

stop-slop 的价值在于它把「AI 腔」这个模糊的感知拆解成了可以操作的检查清单。从禁用短语、禁用结构、句级规则到五维评分，一层层把「听起来像模型写的」还原成「听起来像人写的」。

MIT 许可证意味着可以自由使用、修改和分发。如果你需要产出更自然的 AI 生成文本，或者在调试 prompt 时想让输出更「有人味儿」，这个 Skill 值得加入你的工具链。

GitHub 地址：[hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop)
作者：[Hardik Pandya](https://hvpandya.com)