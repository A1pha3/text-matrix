---
title: "stop-slop：把 AI 写作从套话和模板句里拽出来的 skill"
date: "2026-05-26T09:40:00+08:00"
slug: "stop-slop-remove-ai-tells-from-prose"
description: "stop-slop 是 Hardik Pandya 开源的写作 skill，它把 AI 常见套话、模板句和假动作拆成可执行规则，适合清理英文技术写作里的 AI 味。"
draft: false
categories: ["技术笔记"]
tags: ["AI Writing", "Claude Code", "Prompt Engineering", "Agent Skills", "Editing"]
---

stop-slop 把“AI 味”拆成了一套能执行的编辑检查表：先删词，再拆结构，再把句子的施动者找回来，最后给文章打分。它处理的是成稿阶段。对经常用 Claude、ChatGPT 或其他 LLM 写英文技术文章的人，这比一句“写得自然一点”更容易落实到具体修改动作。

截至 2026 年 5 月 28 日，[hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop) 在 GitHub 上已有 6.1k Stars、446 Forks、3 位贡献者，协议为 MIT。仓库没有 Release，也没有 Package；它的主体是一套 skill 文件和参考规则库，而不是一个 CLI 工具或浏览器插件。

| 项目 | 信息 |
| ---- | ---- |
| 仓库 | [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop) |
| 作者 | [Hardik Pandya](https://hvpandya.com/) |
| 核心定位 | A skill for removing AI tells from prose |
| 协议 | MIT |
| 最近维护信号 | 近两个月仍在补规则，近期提交新增 false agency 检查 |

> 延伸阅读：如果你关心的是界面层的 slop，而不是 prose 层的 slop，可以继续读 [Taste Skill：给 AI 的前端注入「审美品味」，告别千篇一律的 slop UI]({{< relref "leonxlnx-taste-skill-anti-slop-frontend-framework.md" >}})。

## 它解决的写作问题

AI 生成的技术 prose 经常出现一种熟悉的写法：开头先铺垫“让我们看看”，中间反复“值得注意的是”，结尾再收一句“综上所述”。这些句子不传递新信息，只是在模仿“像文章”的样子。

stop-slop 不要求模型抽象地“更像人类”，它把毛病拆成一组可以检查、可以改写、可以维护的规则。这个仓库没有把所有内容都塞进一个 `SKILL.md`，而是拆成三层：

- `SKILL.md` 只放长期稳定的原则，比如 Quick Checks、主动语态、5 维评分。
- `references/phrases.md` 和 `references/structures.md` 负责收录会扩展的禁词和结构模式。
- `references/examples.md` 放改写前后的对照，告诉模型“改完以后应该长什么样”。

这套拆法直接降低了维护成本。最近新增 false agency 规则时，维护者只需要补 references，不必重写主 skill。站在 prompt engineering 的角度看，这比把所有例子都塞进一段越来越长的 system prompt 更稳。

## 仓库里最有价值的四组规则

### 套话会延迟表达

`references/phrases.md` 收的第一类内容，是各种开头先摆姿态的句子。比如“先说清楚一件事”“真正的问题是”“这里值得注意的是”这一类表达。stop-slop 的处理办法很直接：删掉宣布动作，只保留信息本身。

这套处理方式很硬。仓库甚至把 adverb 也整体视为风险源，要求能删就删。你未必要接受它的全部审美，但它确实把“废话”从抽象感觉变成了具体对象。

### 很多 AI 句子的问题出在句型

`references/structures.md` 比短语表更有意思。它针对的不是某个词，而是一整套“先吊一下读者，再揭晓答案”的模板。最典型的是 binary contrast，也就是“不是 X，而是 Y”这一类转折句。stop-slop 对这类句式的态度很明确：直接把 Y 说出来，句子通常会更干净。

同一个文件还列了 negative listing、dramatic fragmentation、rhetorical setup 等模式。把这些条目放在一起看，你会发现 stop-slop 真正整理的是 LLM 常见的“文章骨架”，不只是几个高频短语。

### false agency 抓得很准

仓库最近一次显眼的更新，是把 false agency 补进结构规则里。它指的是让没有行动能力的对象去执行人类动作。比如“数据告诉我们留存率下滑了”，这句话省掉了真正的观察者。更具体的写法会是“我们的留存分析显示用户流失加快了”，或者直接写“用户在第 7 天流失得更快”。句子一改，谁在观察、观察到了什么，也就一起落了地。

这是 stop-slop 最像编辑的地方。它会逼你把“谁做了什么”讲清楚。只要你写技术文章、产品分析或团队复盘，这条规则都很有用，因为它直接关系到责任、动作和判断是否落在具体对象上。

### 节奏也会暴露 AI

除了词和结构，仓库还专门管节奏。规则包括不用 em dash，不用连续的三项排比，不要每段都用 punch line 收尾，也不要把句子拆成一截一截装出重量感。

单独看某一句，这类节奏问题未必显眼；连续出现三四段以后，固定拍子就出来了。stop-slop 把这种节拍感也列进了检查项，作者或模型可以一条条对照着改。

## 一次 stop-slop 工作流是怎么跑的

这个项目不会自动改稿。仓库里没有 parser、lint 命令或 IDE 插件。它依赖的是模型在写作或改稿阶段主动执行这些规则。因此，stop-slop 更像一条清稿流程：

1. 先写出能表达事实的初稿。
2. 按 `SKILL.md` 里的 Quick Checks 扫一遍，把副词、被动语态、Wh- 开头句、em dash、meta-joiners 先清掉。
3. 回到 `phrases.md` 和 `structures.md`，处理那些不一定错、但一看就像模型模板的句子。
4. 参考 `examples.md` 的 before/after，对照检查改写后是不是更直接，而不只是更短。
5. 最后按 Directness、Rhythm、Trust、Authenticity、Density 五个维度打分。README 给的门槛是 35/50，低于这个分数就继续改。

最关键的地方在于，stop-slop 没把“自然”当成主观感觉，而是给了一个可复盘的闭环。你可以不同意它的某条规则，但这种“规则 + 对照 + 打分”的组织方式，确实比一句“去掉 AI 味”更好执行。

## 从 prompt engineering 角度看，stop-slop 最值得学的是什么

如果你经常给 Agent 写 system prompt，这个仓库最值得抄的不是具体词表，而是组织方式。

`SKILL.md` 负责立规矩，`references/` 负责举例和扩表，主提示因此可以保持稳定。Quick Checks 是最小检查集，评分表是交付前门槛，`examples.md` 承担 few-shot 对齐的作用。三者合在一起，就是一条完整的编辑回路。

这也解释了为什么 false agency 这样的新规则可以持续补进去。项目没有停在“一份漂亮 prompt”这一步，而是在把新的坏习惯逐步归档成可维护的知识库。

## 怎么接入，谁最适合用

README 给了四条接入路径：

- Claude Code：把整个文件夹作为 skill 加进去。
- Claude Projects：上传 `SKILL.md` 和 `references/` 到项目知识库。
- Custom instructions：把核心规则抄进 system prompt。
- API：在 system prompt 中放入 `SKILL.md`，需要时再挂载 reference 文件。

如果你的主要工作流，是让 LLM 起草英文技术文章、项目说明或博客草稿，再由人做最后定稿，这套规则可以直接插进现有流程。它最适合的场景也很明确：事实差不多已经对了，成稿还是带着明显的模型腔。

## 这套规则的边界也很清楚

先说最重要的一点：它目前主要服务英文写作。`phrases.md`、`structures.md` 和示例几乎全是英文语料，因此中文写作更适合借鉴思路，不能逐条照搬黑名单。

第二，stop-slop 带有很强的文风立场。比如“尽量清除所有副词”“不要用 em dash”“优先用主动语态”。这套立场拿来清理 AI 生成的技术 prose 很有效，但它不是所有文体都该遵守的统一法则。法律文本、学术论文，或者需要刻意保留作者声线的文章，都不适合机械套用。

第三，它处理的是文字成稿的质感问题。原文如果判断空泛、证据不足、结构失衡，stop-slop 只能把空话说得更干净，不能替你补研究。

## 最后判断

stop-slop 的接入成本很低。没有 CLI 要安装，也没有新语言要学。把 `SKILL.md` 和 `references/` 放进 Claude Projects、Claude Code 或自己的 system prompt，就能开始用。

这套方案的前提也很清楚：模型得愿意执行这些规则，人还得做最后把关。它没有承诺“一次成稿就像人写的”，它提供的是另一条更现实的路径：模型先起草，规则再清稿，最后由人决定什么该保留。