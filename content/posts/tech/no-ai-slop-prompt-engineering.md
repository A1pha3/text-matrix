---
title: "no-ai-slop 源码拆解：一套用 20 多条反模式规则消灭 AI 味的编辑器提示词"
date: "2026-09-13T03:35:00+08:00"
draft: false
description: "petergyang/no-ai-slop 是一个 8.6k star 的 Python 仓库，本质是一份结构化编辑提示词：20 多条 AI 味反模式、三层词表、双职责工作流和自检 eval。本文拆解它的规则设计与工程取舍。"
categories: ["技术笔记"]
tags: ["AI写作", "prompt工程", "LLM", "开源项目"]
github_repo: "petergyang/no-ai-slop"
source_key: "gh:petergyang/no-ai-slop"
slug : no-ai-slop-prompt-engineering
---

## 先给判断

`petergyang/no-ai-slop` 的价值不在代码——仓库的 Python 部分只有一个插件打包脚本——而在 `skills/no-ai-slop/SKILL.md` 这份不到两百行的提示词。它把「这段文字有 AI 味」这个模糊感受，翻译成了 20 多条可以逐条指认的反模式规则，再配上词表、工作流和自检清单，做成一个能被 ChatGPT、Claude Code、Codex 等编码代理直接安装的 skill。

更准确地说，它是一个**用代码工程方法管理的编辑规范**：反模式像 lint 规则一样逐条登记，词表分三档（禁用、常空副词、常空短语），编辑输出要求附「What changed」变更说明，甚至自带一个 `eval.md` 让模型对自己的产出跑检查。对于任何想系统治理 AI 生成文本风格的人，这套规则库本身就值得抄走。

## 项目概览

| 项目 | 数据（2026-09-13 取自 `gh repo view`） |
|------|------|
| 仓库 | `petergyang/no-ai-slop` |
| 描述 | Removes 20+ patterns of AI slop from any piece of writing |
| Stars / Forks | 8,610 / 647 |
| 主语言 | Python（实际仅插件打包脚本） |
| License | MIT |
| 创建时间 | 2026-07-07 |
| 最近提交 | 2026-09-02（活跃维护） |

作者 Peter Yang 是创作者经济（creator economy）领域的博主，这个 skill 是他付费课程体系 Behind the Craft 的免费引流部分，同时也是 ChatGPT 官方插件市场上的插件。安装方式两条路：

```text
Install the /no-ai-slop skill globally from https://github.com/petergyang/no-ai-slop
```

```sh
npx skills add petergyang/no-ai-slop --skill no-ai-slop --global --yes
```

第一条粘贴给任意编码代理即可，第二条走标准 skill 分发工具。装完后 `/no-ai-slop (你的文稿)` 触发编辑，`/no-ai-slop is this slop? (你的文稿)` 触发检测。

## 系统地图：三层结构

整个 skill 的知识全部装在一个目录里，职责切分如下：

```
skills/no-ai-slop/
├── SKILL.md    # 核心规则：角色设定 + 双职责 + 编辑原则 + 词表 + 反模式 + 工作流
└── eval.md     # 自检清单：编辑完成后模型对照检查
.codex-plugin/plugin.json  # ChatGPT / Codex 插件元数据
scripts/build_plugin.py    # 打包与校验插件
```

规则的层次从抽象到具体是三层：

1. **编辑原则**（Editing principles）——约 18 条，定义「怎么改」：保留作者声音、最小有效修改、主动语态、具体优先于抽象。这一层不针对 AI 味，是通用的人类编辑守则。
2. **词表**（Words to cut）——直接点名要消灭的词。禁用词一刀切：delve、leverage、robust、paradigm shift、tapestry 等 26 个；常空副词和常空短语则给了保留条件——当它们承载真实的不确定性或作者口吻节奏时可以留。
3. **反模式**（Patterns to cut）——20 多条结构级规则，每条带例子和改法，是整个 skill 的核心资产。

一个值得注意的工程细节：词表不是无差别封杀。禁用词 outright banned，副词和短语是「often-empty」——切掉不加东西的，保留有功能的。这个分档比一刀切的黑名单更像一个有经验的编辑会做的事。

## 核心资产：反模式规则逐类拆解

20 多条反模式可以归成四组，每组解决一类 AI 味的成因。

**第一组：假装有洞见。** 包括二元对比（「It's not X. It's Y.」）、清嗓子开场（「Here's the thing」）、伪洞察铺垫（「What nobody tells you」）、冒号揭示（「The best part: it learns.」）。这四条的共性是用句式制造戏剧感来代替实际内容，修法一律是删掉结构、让论点裸奔——「The part everyone misses: distribution is the real moat」改成「Distribution is the moat」，信息没少，表演没了。

**第二组：假装做了分析。** 包括尾随 `-ing` 从句的浅层分析（「highlighting the team's commitment to innovation」）、重要性吹捧（「marks a pivotal moment」）、黄鼠狼归因（「experts agree」「studies show」）。规则的处理方式体现了证据观：要么给出可指认的来源，要么删掉论断——skill 明确禁止模型替用户编造来源，没有来源就问。

**第三组：节奏与结构的机械感。** 同义词轮换（agent / assistant / tool 其实指同一个东西）、否定列举（「Not a X. Not a Y. A Z.」）、戏剧化断句（「That's it. That's the whole thing.」）、机器人节奏（每段同样的句式形状）。这组规则针对的是 AI 文本统计意义上的平滑性——模型倾向于避免重复、均匀输出，而人类写作恰恰靠重复和长短不齐来传意。

**第四组：结尾的套路。** 假深沉收尾（「The future isn't coming. It's already here.」）的处理规则写得很硬：不要改写成更好的比喻，不要保留节奏，直接删掉，然后落在正文里最清晰的那个具体句子上。总结复述式结尾（「In conclusion」）同理——读者刚刚读完，不需要再听一遍。

此外还有一条针对格式化 AI 味的规则：标题里的 emoji、句中加粗强调、两句话就套一个小标题，都算 formatting slop。以及破折号规则——不作为默认节奏拐杖，短文一条不用，长文至多一两条。

## 双职责设计：编辑与检测分离

SKILL.md 开头就声明了两个互斥职责，这是整个工作流里最值得借鉴的设计。

**编辑模式**（默认）做最小有效修改，返回修改稿加一段「What changed」。**检测模式**只输出发现：逐条指认命中的反模式、引用原文、给几个字的修法建议，明确不做三件事——不重写、不打分、不猜测文本是否由 AI 写成。

「不猜测是否 AI 写的」这一条写得很清醒：AI 检测器只能猜，而具名反模式是用户可以逐条核对的证据。检测模式输出的是可验证的事实清单，不是概率判断。这个边界划分让 skill 避开了 AI 检测这个出了名不可靠的赛道，只做自己能负责的事。

工作流末尾还有一道自检：编辑完成后模型要对照 `eval.md` 检查自己的产出，有检查失败就修了再跑。这是把「测试」概念引进提示词工程的少见做法。

## 一个编辑任务的完整流转

以一段典型的 AI 味文稿为例，走一遍流程：

输入（检测模式 `/no-ai-slop is this slop?`）：

> Here's the thing about modern CI: it's not just about speed. It's about trust. The pipeline validates every commit, underscoring the team's commitment to quality. That's it. That's the whole thing.

预期输出会指认四条命中：清嗓子开场（Here's the thing）、二元对比（not just X. It's Y）、浅层分析（underscoring 从句）、戏剧化断句（That's it. That's the whole thing）。每条引用原文，各给几个字的修法。

编辑模式（`/no-ai-slop`）下的最小改写方向：

> Modern CI is about trust: the pipeline validates every commit, so broken code can't reach production unnoticed.

开场删了，二元对比拆成直接陈述，`-ing` 从句换成「so + 具体后果」，断句戏删掉。信息量没有损失，句子从表演变成了陈述。

## 设计取舍

**最小有效修改优先于全面润色。** 规则反复强调：有人味但粗糙的初稿，改完之后还应该听起来是同一个人。这直接对抗了 LLM 编辑最常见的副作用——把所有段落磨得一样整齐，个人词汇、节奏、跑题全部被抹平。为此规则甚至保留了「I think」「maybe」「to be honest」这类词的合法性，只要它们表达真实的不确定或作者口吻。

**规则可指认优先于风格判断。** 每条反模式都带例句和改法，检测输出要求引用原文。这让 skill 的行为可审计——用户能核实每一条改动是否有据，而不是接受一个黑箱的「润色」。

**保留作者事实边界。** 不发明论断、例子、数据或观点；不清楚就问。配合黄鼠狼归因规则，整个 skill 对事实的态度是收缩而不是扩张。

## 适用边界

这个 skill 的定位是**英文文风编辑器**。反模式规则和词表全部从英文语料提炼，直接用于中文文本效果会打折——中文的 AI 味有自己的一套高频症状（「值得注意的是」「赋能」「不难发现」、排比堆叠、四字格滥用），需要另建词表。

它也不检测事实错误。黄鼠狼归因规则只要求「给出来源或删掉」，不会替你核实来源本身是否可靠。事实核查是另一个问题域。

第三，它解决的是「已经写出来的稿子」，不解决「如何一开始就少生成 AI 味」——那需要改的是生成侧的提示词，而不是编辑侧。

## 什么时候值得用

如果你的工作流里有「AI 起草或润色 + 人工终审」的环节，这个 skill 适合放在人工终审之前做第一道筛。它的规则库也可以直接当中文版同类工具的设计参考：把 20 多条反模式翻译成本地语料的对应症状，配上同样的「检测只指认不判断、编辑只做最小修改」双职责边界，就是一个中文 no-slop skill 的骨架。

仓库本身适合通读 `skills/no-ai-slop/SKILL.md` 全文——它同时是一份规则库和一个高水准的提示词范例，两个身份都值得学。
