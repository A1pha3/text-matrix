---
title: "blader/humanizer 项目导读：把「去 AI 味」从一句玄学 prompt 变成一份 374 行的规则文件"
slug: blader-humanizer-anti-ai-writing-skill
github_repo: "blader/humanizer"
source_key: "gh:blader/humanizer"
date: 2026-09-01T14:50:00+08:00
lastmod: 2026-09-18T10:30:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["AI 写作", "Skill", "去 AI 味", "Agent", "Claude Code"]
description: "Humanizer 是一个 47.6k stars 的 agent skill，把维基百科『AI 写作迹象』整理成 25 条规则，让任何 agent 能把 AI 味文本改成人的写法而不改事实。本文基于 v3.0.0 解读它的规则结构、四步工作流、事实红线与自我校验脚本。"
---

# blader/humanizer 项目导读：把「去 AI 味」从一句玄学 prompt 变成一份 374 行的规则文件

## 核心判断

多数人「去 AI 味」的做法，是给模型一句「写得更自然一点」，把判断权交给模型自己。Humanizer 走了另一条路：把「不像 AI」拆成 25 条可以逐条指认的规则，做成一份 374 行的 Markdown 文件，让任何 agent 照着规则改写，同时保证不增减一个事实。

这份规则文件不是作者拍脑袋写的。它的源头是维基百科的「Signs of AI writing」手册——由 WikiProject AI Cleanup（清理 AI 生成内容的维基专项组）维护，每个信号都配了维基百科条目里的真实病例。Humanizer 做的事，是把一部描述性手册压缩成一套可执行、可校验的改写流程。

项目在 2026 年 1 月 18 日建仓，8 个月拿到 47.6k stars。中间经历了一次大重构：规则一度膨胀到 35 条，2026 年 9 月的 v3.0.0 又合并回 25 条，并按「犯错强度」重新排序。这个反复本身就是信息——AI 味的信号库需要跟着模型和语料持续维护，不是一个写完就封版的清单。

## 项目坐标

| 维度 | 数据 |
|------|------|
| 仓库 | blader/humanizer |
| Stars | 47,598（截至 2026-09-18，GitHub API） |
| 建仓时间 | 2026-01-18 |
| 最近推送 | 2026-09-06 |
| 仓库大小 | 205 KB |
| GitHub 语言标签 | Python |
| 产品本体 | 一份 374 行的 `SKILL.md`（v3.0.0） |
| License | MIT |
| 规则数 | 25 条，分 5 组 |
| 规则来源 | Wikipedia: Signs of AI writing |
| 适配 | Claude Code / Cursor / Codex 等任何支持 skill 的 agent |
| Homepage | skills.sh/blader/humanizer（分发与安装量统计页） |

语言标签是 Python，但产品本体是纯 Markdown。Python 的来源是 `scripts/validate-package.py`——一个 87 行的自校验脚本，稍后展开。整个仓库的组织方式是：prompt 是产品，脚本是测试，README 兼任文档和发布说明。

## 问题拆分：AI 味到底是什么

### 根源是回归均值

维基手册给的解释很直接：LLM 用统计算法猜下一个词，输出自然趋向「统计上最可能、适用范围最广」的结果。名人语料里满是正面、重要的措辞，模型就倾向于丢掉具体、罕见、有棱角的事实，换成通用、正面、听起来很重要的描述。

手册里有个比喻值得整段抄下来：

> 就像对着画像越喊越大声「这是个重要人物」，画像却从锐利的照片糊成一幅模糊的草图。主角越来越不具体，同时越来越夸张。

AI 味的本质就这一句话：细节消失，重要性膨胀。后面 25 条规则，都是这个默认倾向在不同位置的表现。

### 检测为什么靠不住

维基手册引用的几项研究，把「凭感觉判断」这条路堵得差不多了：

- 2025 年一项发表在 Advances in Simulation 的研究显示，人类区分 LLM 文本和人写文本的能力不比随机猜测好。
- 同年另一项基于德语学位论文的研究，人类对 AI 文本的识别率 57%，对人类文本 64%。
- 2025 年的一项预印本研究显示，重度 LLM 用户判断一篇文章是否 AI 生成的准确率约 90%——按这个比例，标记 10 页就带着 1 个误伤；轻度用户的成绩只比随机略好。
- GPTZero 这类自动检测工具好于随机，但错误率不可忽略，且文本改写、排版调整或换用训练时没见过的模型都可能让检测失效。

人和工具都看不准，所以规则化才有价值：感觉不可靠，那就列清单。维基手册自己也强调，这些信号只是「可能有问题的迹象」，不是判决书——清单描述现象，不替代判断。

## 核心机制：25 条规则、四步工作流、一条红线

### 25 条规则，按强度排序

v3.0.0 把规则分成 5 组，编号按信号强度和出现频率从高到低排。前 5 条（#1-#5）单独出现一次就值得动手改；标了 weak alone 的（破折号、限定词堆叠、连字符对、被动语态、花引号）需要同一段落里多个信号同时出现才动手，因为认真的作者也可能故意这么写。

| 组 | 编号 | 管什么 | 例子 |
|------|------|--------|------|
| A. 摆架势代替陈述 | #1-5 | 「不是X而是Y」、金句式收尾、伪深刻格言、绕圈开场、回应没人提的反对 | "It's not just X, it's Y" → 直接说观点 |
| B. 节奏模板化 | #6-11 | 强行三连排比、句子开头重复、破折号滥用、限定词堆叠、连字符对、被动语态 | "innovation, inspiration, and insights" → 该几项写几项 |
| C. 夸大与借势 | #12-18 | AI 高频词、重要性膨胀、模糊关联、浅层 -ing 尾巴、广告腔、借专家之名、回避 is/are | "nestled within the breathtaking region" → 直接说这是什么 |
| D. 格式模板化 | #19-21 | 装饰性加粗、标题大写和 emoji、花引号 | "**OKRs**, **KPIs**" → 去掉加粗 |
| E. 聊天与草稿残留 | #22-25 | 客套话、知识截止声明、标题在首句复读、写「上一版」 | "I hope this helps!" → 删掉 |

每条规则都配 before/after 对照。这是规则能被执行的关键：不是告诫「别写套话」，而是具体到「`serves as` 换成 `is`」。

排序本身是个设计判断。README 里写明编号按「强度和频率」排——「不是X而是Y」排第 1，因为它是 AI 文本里最普遍、最暴露出处的信号，每条规则得到的篇幅也按这个优先级分配。

### 四步工作流

SKILL.md 的流程是四步：

1. **标记信号。** 通读全文，从最强信号标起。段落形状也要看——跨两句的对比、每节结尾都收同一句金句，和句级信号是同一回事。
2. **起草重写。** 保留全部有依据的论断；可以合并段落、调整结构，但信息不能丢。缺细节就问，或者换个更简单的写法。
3. **检查草稿。** 读出声，问两个问题：哪里还像 AI？有没有新增或丢掉任何事实、名字、数字、日期、引语、引用？SKILL.md 还点名了五个重写后最容易存活的信号：对比句、收尾金句、破折号、三连排比、加粗标签，要求逐一复查。
4. **写终稿。** 围绕段落主旨自然地重说一遍，而不是对标记短语逐个打补丁。句子长短要有变化。

第一步就不把原文结构当金科玉律——「可以合并段落、拆分句子、重组顺序」写进了规则文本。这是它和一般润色 prompt 的另一个区别：润色只改措辞，Humanizer 允许动结构。

### 一条红线：不编造事实

SKILL.md 的措辞很硬：不得加入来源或用户没有提供的名字、数字、日期、引语、引用。句子缺一个必要细节，就开口问，或者换个写法。唯一豁免是虚构创作——虚构里编细节本来就是任务。

README 里的里斯本游记示例专门演示了这条红线的合法形态：作者附了便条（去年十月去的、酒店在阿尔法玛、蛋挞在 Graça 的一家小店吃的），改写稿才能用这些细节。没有便条，就该问，而不是编。红线管的不是「模糊化」，是「细节必须有出处」。

### 声音匹配与输出模式

给它 2-3 段作者自己写的文字，它会先分析句子长度、用词、标点、开头和转场习惯，再按这个节奏改写。写作样本的优先级高于默认规则：默认规则限制破折号，但样本爱用破折号，就按原频率保留。没有样本时，按文本类型定声音——博客、随笔、个人写作保留作者的观点、犹豫和幽默；参考、技术、法律文本保持中性平实。

输出分三种模式。粘贴文本（默认）返回三样东西：第一版重写、残留问题的简短清单、终稿。指定文件时只改正文，代码块、行内代码、命令、路径、YAML 元数据和链接目标原样不动。被其他任务嵌入调用时只返回终稿。

还有一个容易忽略的边界（When not to act）：引语、标题、专有名词、正在讨论某短语的段落，里面的信号不动；信件的称呼和落款比聊天机器人早得多；2022 年 11 月 30 日之前写的文本直接不算 AI 写。

### 自校验脚本

`validate-package.py`（87 行，无外部依赖）盯着几件事：SKILL.md 必须以 YAML 元数据开头，且顶层不得出现 `version`、`compatibility`、`allowed-tools` 这类未被支持的字段；版本号在 SKILL.md、README 和插件清单三处必须一致；规则编号从 1 连续排到 25，不许有缺口；README 的规则表编号必须与 SKILL.md 一一对应；SKILL.md 不得超过 400 行；仓库根目录只允许一份常规 SKILL.md（不能是符号链接）。

一个以 prompt 为产品的仓库，用一个测试脚本保证 prompt 的可维护性——版本、编号、篇幅都有硬约束。这是「规则文件当软件工程做」最直白的证据。

## 版本演进：35 条合并成 25 条，删掉的两条更有信息量

changelog 完整记录了这个项目的维护轨迹：2.0.0 从维基手册重写；2.4.0 加声音匹配；2.9.0 确立「不编造事实」红线；2.10.0 规则膨胀到 35 条；2.11.x 全文改写为 Plain Language；2026 年 9 月的 3.0.0 合并回 25 条。

3.0.0 的合并逻辑有两层。第一层是去重：工作流文本此前散在五处，破折号规则写了两遍，这次各归一处。第二层更有意思——删掉了「假 X 到 Y 范围」和「同义词轮换」两条，因为维基手册现在把它们列为人类写作习惯或历史现象。上游语料修正了判断，下游规则跟着撤销，并新增了「模糊关联」这条维基新收录的信号。

这段演进回答了一个问题：规则库会不会过时？会，而且这个项目把「跟着上游更新」当成了常规维护。词表也在换血——维基手册记录了 `delve` 这个词从 2023-2024 年被 ChatGPT 滥用、2024 年后期回落、2025 年骤降的完整曲线。AI 味是移动的靶子，信号库需要版本号。

## 任务流案例：一段里斯本游记穿过整套机制

用 README 的完整示例串一遍。输入是典型的 AI 味游记：

> I recently spent five unforgettable days in Lisbon, and let me tell you — this city completely stole my heart... Nestled along the banks of the Tagus River, Lisbon stands as a vibrant testament to Portugal's enduring spirit... And the food? Simply divine... If you're dreaming of your next getaway, this is one destination that promises memories to last a lifetime. ✨

各条规则在其中的落点：

- **#16 广告腔 / #12 AI 高频词**：`Nestled along the banks`、`vibrant testament` 属于推销式语言和高频词，删夸张，留事实。
- **#8 破折号**：全文破折号拆成逗号或句号（这条标了 weak alone，这里是配合其他信号一起改的）。
- **#1 「不是X而是Y」+ #2 收尾金句**：原文结尾 "Lisbon isn't just a place to visit — it's a place to fall in love with, again and again" 是教科书式的对比句加金句收尾，整体重写。
- **#13 重要性膨胀**：`unforgettable`、`Simply divine`、`a moment I will never forget` 这类拔高词被降级成具体陈述。
- **#20 emoji**：结尾的 ✨ 属于装饰性符号，删除。

输出（节选）：

> I spent five days in Lisbon last October and still have mixed feelings about it. Beautiful, yes. Also harder on the knees than anyone warned me.
>
> The hills are the whole story and somehow never make the brochures. My hotel was up in Alfama...

两版对比，信息基本全保住了：五天、电车、蛋挞、山丘、阿尔法玛都在。变的是情绪——从浮夸的惊艳变成诚实的五味杂陈。「十月」「阿尔法玛」这些细节来自作者的便条，正好演示了红线：细节必须有出处。结尾落回「春天再去、换双好鞋」这样的具体计划，而不是一句总结陈词。

## 数据解读：47.6k stars 说明什么，不能推出什么

GitHub stars 测的是关注度，不是效果。它反映多少人觉得这个项目值得收藏，不反映用过的用户里有多少真把 AI 味去掉了。

47.6k 放在 2026 年看，更多说明生态：技能分发渠道（skills.sh 安装量、Claude Code 插件化）成熟了，「装一个 skill 就能改文风」这个模式被接受了；同时 AI 生成内容泛滥，让「看起来不像 AI」成了内容生产者的刚需；Humanizer 还占着「以维基手册为源」的背书——规则有出处。

不能从这个数字推出的东西同样值得列出来：

- **不能推出它能骗过检测器。** 它引用的研究本身就说明检测工具错误率不可忽略，项目也从不承诺「过检」，3.0.0 甚至从包文件里删掉了 `ai-detection` 关键词。
- **不能推出 25 条规则完备。** SKILL.md 里每条规则都写了误伤提醒（false positives），维基母版也声明这是描述性清单。3.0.0 删掉两条规则的动作就是提醒：清单本身也在被证伪和修正。
- **不能推出它适合中文。** 25 条规则绝大多数是英文特征——`Additionally`、`landscape`、title case、花引号、em dash。中文的 AI 味是另一套信号（「值得注意的是」「综上所述」「赋能」「闭环」），需要另一份信号库。Humanizer 解决的是英文语境的工程问题。

## 采用建议与适用边界

谁该先用：英文内容创作者（博客、newsletter、产品文案），要把 AI 初稿改成自己的声音；用 agent 写文档的团队，让交付前的文档先过一遍它；研究「写作审美工程化」的人——374 行 SKILL.md 同时是产品、文档和教学材料。

谁可以等等：纯中文写作场景，直接套用会失灵；想「过 AI 检测」的，它的设计目标恰恰相反——要诚实和自然，不追求伪装。

落地顺序：

1. 最轻量：`npx skills add blader/humanizer --global`，在任意 agent 里用 `/humanizer` 改一段文本。
2. Claude Code 2.1.142 及以上版本可以走插件通道：先 `/plugin marketplace add blader/humanizer`，再 `/plugin install humanizer@humanizer`，自带更新。
3. 日常使用：把「粘贴文本」换成「指定文件」，让它只改正文、不碰代码块和 frontmatter。
4. 进阶：给它 2-3 段自己的旧文做声音样本，改写会跟着你的节奏走。
5. 再往深一步：读它的 `validate-package.py`。87 行脚本怎么给一份 prompt 文件做回归测试，这个问题在多数「prompt 工程」讨论里没人碰。

## 结尾判断

Humanizer 的价值不在那 25 条规则本身——有经验的编辑本来就在做类似的事。它的价值在于把「写作审美可以降维成清单、清单可以被脚本校验」这件事完整演示了一遍：规则有上游出处，版本有 changelog，编号有连续性检查，篇幅有硬上限，上游语料修正时下游跟着撤销过时的规则。

对想让自己的文字「不那么 AI」的人，这个仓库给出的可复用做法是：先把你认为的 AI 味信号一条条列出来，写清每条的 before/after 和误伤条件，再谈自动化。信号会过时，维护机制比某一份清单更耐用。

---

## 参考来源

- [blader/humanizer GitHub 仓库](https://github.com/blader/humanizer)（本文数据截至 2026-09-18，基于 v3.0.0）
- [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- [WikiProject AI Cleanup](https://en.wikipedia.org/wiki/Wikipedia:WikiProject_AI_Cleanup)
