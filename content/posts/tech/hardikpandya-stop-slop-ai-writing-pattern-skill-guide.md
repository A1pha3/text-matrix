---
title: "Stop Slop 项目导读：一份给 LLM 用的「去 AI 味」规则清单"
date: "2026-06-25T21:09:50+08:00"
slug: "hardikpandya-stop-slop-ai-writing-pattern-skill-guide"
description: "hardikpandya/stop-slop 是一份给 LLM 用的「去 AI 味」Skill，把 AI 写作套路整理成可机读规则。本文拆解它的 8 条主规则、4 类结构禁式与使用边界。"
draft: false
categories: ["技术笔记"]
tags: ["AI写作", "Prompt工程", "Claude", "LLM", "Skill"]
---

# Stop Slop 项目导读：一份给 LLM 用的「去 AI 味」规则清单

> **目标读者**：被 LLM 输出里那些套话、二元口号、机械排比烦到想做点什么的工程师或作者
> **前置知识**：知道 Claude / LLM 的 system prompt 是什么，用过 Claude Code、Claude Projects 或任何支持自定义指令的 LLM 工具
> **预计阅读时间**：8 分钟 | **难度**：⭐

---

## 一、核心判断

`hardikpandya/stop-slop` 不是模型，不是工具，也不是 Agent。它是**一份写给 LLM 看的 Skill**——把"AI 写出来的东西为什么总像 AI"这件事，整理成可机读的检查表。仓库本身极轻：4 个 Markdown 文件（`SKILL.md` + 3 个 `references/*.md`），MIT 协议，截至 2026-06-25 累计 12,372 Stars、859 Forks。这套 Skill 不让 LLM 写得更聪明，而是**教 LLM 别再犯同样的写作毛病**。

这套 Skill 的设计取舍很明确：

- 不做模型权重修改，只做 prompt 约束（因此任何兼容 system prompt 的客户端都能直接套用）
- 不试图覆盖所有文风问题，只瞄准"可识别的 AI 套路"（throat-clearing、二元对比、虚假主语、机械排比等）
- 不替代人类编辑，但能在大规模 LLM 输出场景里省下 80% 的"挑刺时间"

如果你受够了自己 LLM 输出里"在当今快节奏的时代""这不仅仅是 X，更是 Y"这种句式，这套规则会比一句"请写得更像人"管用得多——因为它把"像人"拆成了 8 条核心规则 + 5 维评分 + 一份"删除词清单"。

---

## 二、Skill 结构：4 个 Markdown 文件各管一摊

整个仓库的可执行部分只有 4 个文件：

```
stop-slop/
├── SKILL.md              # 核心规则（8 条主规则 + 11 项 quick checks + 5 维评分表）
├── references/
│   ├── phrases.md        # 词面禁词：throat-clearing、business jargon、adverbs、meta-commentary
│   ├── structures.md     # 结构禁式：binary contrasts、negative listing、dramatic fragmentation、false agency
│   └── examples.md       # before/after 对照示例
├── README.md             # 项目说明 + 接入方式
└── LICENSE               # MIT
```

`SKILL.md` 是核心入口，定下 8 条 Core Rules + 11 项 Quick Checks + 5 维评分。`phrases.md` 和 `structures.md` 是按需加载的细节字典：写完一句先扫 `phrases.md` 看有没有命中禁词，看一段节奏先扫 `structures.md` 看有没有落入套式。`examples.md` 提供 5 段 before/after 对照，把"为什么这样改"具体化。

这种"主入口 + 按需 reference"的分层是 Claude Skill 的标准模式：system prompt 不会被一次性撑爆，模型可以决定什么时候去翻 reference。

---

## 三、规则覆盖范围：8 条主规则能改掉什么

`SKILL.md` 列出的 8 条 Core Rules 大致可以归成 4 类问题：

**1. 词面清理：删 filler、删套话、删副词**

`phrases.md` 给出的禁词清单分 5 组：

- **Throat-clearing openers**：`"Here's the thing:"`、`"It turns out"`、`"Let me be clear"`、`"The real [X] is"` 这类"先清嗓再说话"的开场——直接删，让内容从第一句开始。
- **Emphasis crutches**：`"Full stop."`、`"Let that sink in."`、`"This matters because"`——空转的强调动作，没有任何信息量。
- **Business jargon**：`"navigate (challenges)" → handle`、`"unpack (analysis)" → explain`、`"lean into" → accept`、`"deep dive" → analysis`、`"circle back" → return to`。这一组特别针对 LLM 在企业语境里特别爱用、但实际上什么都没说的 11 个动词。
- **Adverbs**：`really`、`just`、`literally`、`genuinely`、`honestly`、`simply`、`actually` 这 16 个最常见的副词——按规则"全删，不留"。
- **Vague declaratives**：`"The reasons are structural"`、`"The implications are significant"`、`"The stakes are high"`——只说"重要"不说"什么"的话。

**2. 结构改造：避开二元对比和负面列表**

`structures.md` 把 6 类结构套路列成对照表：

- **Binary contrasts**：`"Not because X. Because Y."`、`"[X] isn't the problem. [Y] is."`、`"It's not this. It's that."`——这些"先否定再揭示"的句式本质上是 telegraphed reversal，规则是"直接说 Y，跳过 X"。
- **Negative listing**：`"Not a X... Not a Y... A Z."`——靠连续否定做的"戏剧性揭示"，读者其实不需要这个 runway。
- **Dramatic fragmentation**：`"[Noun]. That's it. That's the [thing]."`、`"X. And Y. And Z."`——把短句堆成"表演性深刻"，改写时直接合并成一句完整陈述。
- **Rhetorical setups**：`"What if [reframe]?"`、`"Here's what I mean:"`、`"Think about it:"`、`"And that's okay."`——这些是"先预告再揭示"的 scaffolding，直接说观点。
- **False agency**：把"complaint becomes a fix""the decision emerges""the market rewards"这种人称动词挂在无生命主语上。规则要求"点名执行人"，"the team fixed it" 而不是 "the complaint becomes a fix"。

**3. 句子级硬约束**

- 不用 Wh- 开头（What / When / Where / Which / Who / Why / How）
- 不用 em dash
- 不用被动语态
- 不用极端词（every / always / never / nobody / everybody）
- 段落不用"punchy one-liner"结尾——每段换一种收尾方式

**4. 5 维评分卡**

写完之后，按 Directness / Rhythm / Trust / Authenticity / Density 五项各打 1-10 分，总分 < 35/50 就重写。这套评分卡的设计思路是：与其让 LLM 写一次"看起来行"，不如让 LLM 自查五维后再交付。

---

## 四、5 段 before/after 看清"AI 味"长什么样

`examples.md` 给出 5 段对照，把规则从抽象落到具体：

| 原文 | 改后 | 改在哪里 |
|------|------|----------|
| "Here's the thing: building products is hard. Not because the technology is complex. Because people are complex. Let that sink in." | "Building products is hard. Technology is manageable. People aren't." | 删 throat-clearing + 二元对比 + emphasis crutch |
| "It turns out that most teams struggle with alignment. The uncomfortable truth is that nobody wants to admit they're confused. And that's okay." | "Teams struggle with alignment. Nobody admits confusion." | 删 hedging + throat-clearing + 许可式结尾 |
| "In today's fast-paced landscape, we need to lean into discomfort and navigate uncertainty with clarity. This matters because your competition isn't waiting." | "Move faster. Your competition is." | 删 business jargon + emphasis crutch |
| "Speed. Quality. Cost. You can only pick two. That's it. That's the tradeoff." | "Speed, quality, cost—pick two." | 删 dramatic fragmentation |
| "What if I told you that the best teams don't optimize for productivity? Here's what I mean: they optimize for learning. Think about it." | "The best teams optimize for learning, not productivity." | 删 rhetorical setup |

这 5 段对照把"AI 味"具体化到读者能直接对照自检的程度。

---

## 五、接入方式：4 条路径

`README.md` 列了 4 种接入方式：

- **Claude Code**：把整个文件夹作为 skill 添加（`.claude/skills/stop-slop/` 即可识别）
- **Claude Projects**：把 `SKILL.md` + 3 个 reference 上传到 project knowledge
- **Custom instructions**：从 `SKILL.md` 拷贝核心规则到任何 LLM 工具的 custom instructions
- **API 调用**：把 `SKILL.md` 放进 system prompt，`phrases.md` / `structures.md` 通过 tool use 按需加载

从工程角度看，前两条路径最省事；后两条适合已经在做 RAG 或 Agent pipeline、需要在 system prompt 级别强制约束的场景。

---

## 六、采用顺序与适用边界

**适合采用的场景**：

- 大量 LLM 生成内容需要"过一遍"的场景：博客草稿、文档初稿、营销文案、社交媒体内容
- 自己写完也总带 AI 味、想用一份规则清单作为"自检表"的作者
- Agent 系统中需要在 generation 后做一次"去味"步骤的 pipeline
- 想在团队里统一 LLM 写作风格基线（把 8 条 Core Rules 当作 style guide）

**谨慎采用的场景**：

- 需要保留 LLM 标志性格式的场景（例如某些营销文案的"对比 + 强调"是品牌识别的一部分）——直接套用会破坏品牌一致
- 学术论文或法律文书——这类内容对 hedging 词有合规需求，按 stop-slop 全删副词反而会损失必要的精确度
- 翻译任务：翻译要忠于原文措辞风格，把 stop-slop 直接套在翻译 system prompt 里会强制译员"二次创作"

**不适用的场景**：

- 想用它改模型权重或 RLHF（stop-slop 是 prompt 层面，不动模型）
- 想用它在生产环境做实时"反 AI 味检测"（规则都是 LLM-readable，没有提供 standalone 检测器 API）

**与现有工具的关系**：

- `bleu` / `perplexity` 等传统 NLP 指标不直接反映"AI 味"——停用词命中率可以近似，但不准确
- 一些 SaaS 提供"AI detector"功能，但 stop-slop 的设计目标不是"识别 AI 写的"，而是"让 LLM 少写出 AI 味的"
- 如果你已经在用 Anthropic 的 Claude with `style` 偏好，stop-slop 可以叠加上去作为更细的约束

---

## 七、总结：规则清单的工程价值

`hardikpandya/stop-slop` 的真正信号是：LLM 的"AI 味"问题不是靠换 prompt 措辞能解决的，而需要把"像不像人"拆成可机读的规则集。仓库用 4 个 Markdown 文件、约 500 行内容，给出了一份**经过分类、可按需加载、能直接套用 system prompt**的检查表——这件事在 LLM 应用层被严重低估了。

它的局限性也来自这个选择：规则是英文为主、中文场景下"throat-clearing"和"binary contrast"的具体形式会变化（中文的"那么问题来了""不仅如此""更重要的是"是另一套套路），需要自行补充或本地化。**当作英文写作的 baseline rule set 来用最稳**；中文场景建议把"删副词"和"删二元对比"这两条作为最稳的起点，再按需扩展。
