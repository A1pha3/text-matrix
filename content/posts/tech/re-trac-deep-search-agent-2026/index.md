---
title: "RE-TRAC：递归压缩每条轨迹，把深度搜索 agent 从「重复试错」改成「渐进学习」"
date: 2026-08-02T13:55:00+08:00
draft: false
slug: re-trac-deep-search-agent-2026
tags: ["arxiv", "agent", "deep-search", "test-time-scaling", "trajectory-compression", "sft", "icml-2026", "msra"]
categories: ["tech"]
description: "RE-TRAC 是微软亚洲研究院 + 6 所高校（东南大学 / 早稻田 / 清华 / 布朗 / 浙大）提出的深度搜索 agent 框架，让每轮探索留下一份结构化状态传给下一轮，把 ReAct 线性框架的「计划了却没走完」毛病治好。BrowseComp 上 o3 从 54.9% 推到 69.8%，o4-mini 从 25.7% 推到 46.8%，token 与工具调用随轮次单调下降。"
keywords: ["RE-TRAC", "deep search agent", "trajectory compression", "ReAct", "test-time scaling", "BrowseComp", "ICML 2026", "MSRA", "structured state"]
author: "钳岳"
canonical: "https://txtmix.com/posts/tech/re-trac-deep-search-agent-2026/"
---

> **本文素材**：arXiv `2602.02486`（PDF 18 页 / 836KB / 2026-02-02 提交 / 预印本 v1）。20 位作者：Jialiang Zhu、Gongrui Zhang、Xiaolong Ma、Lin Xu、Miaosen Zhang、Ruiqi Yang、Song Wang、Kai Qiu、Zhirong Wu、Qi Dai、Ruichun Ma、Bei Liu、Yifan Yang、Chong Luo、Zhengyuan Yang、Linjie Li、Lijuan Wang、Weizhu Chen、Xin Geng、Baining Guo。机构脚注：6 所高校（东南大学 / 早稻田 / 清华 / 布朗 / 浙大）+ Microsoft；带 † 标注的几位「this work was done during the internship at MSRA」。arXiv 内文未显式标注 ICML 录用，录用信息以会议公告为准。
>
> **本文目的**：把 RE-TRAC 的工程动机、状态结构、训练流程、关键数字如实讲清楚，**不做综述、不外推**。所有数字均对应 paper 的具体表格/图（Table 2-13 / Fig 2-6 / §4.1-4.4）。需要你自己复现时，对照 Table 7-8 的超参与 Fig 9-11 的 prompt。

---

## 一、Pass@8 远高于 Pass@1：模型不笨，探索没管理

深度搜索 agent（Deep Research Agent）正在成为 2026 年 AI 工程的主战场。它能自主开浏览器搜几千个网页、把碎片信息揉成报告——OpenAI 的 Deep Research、Google 的 Gemini Deep Research、Perplexity 的 Deep Research、xAI 的 Grok DeepSearch 都是这条线的产品级实现。

但它们都有一个工程上很扎眼的反直觉现象：**Pass@8 远高于 Pass@1**。

论文 Figure 2 把这件事画得很清楚：在 BrowseComp 上让同一个模型独立跑 8 次（采样温度 1.0），挑最对的那次当成上界。o3 模型 Pass@8 的上界约 81%，而 Pass@1 不到 60%。中间有 20 多个百分点的「本可以做到」没做到——这不是模型的智力上限问题，是**探索管理失败**的问题。

RE-TRAC 这篇论文的论点可以浓缩成一句话：

> **问题不是模型不会搜索，是同一个模型的多次独立尝试之间不互通信息。每条轨迹都在重复同一段已经走过的弯路——把多次独立试错改成渐进式学习，是 test-time scaling 的真正未开发空间。**

它做的事很朴素：每条轨迹跑完之后，把「我现在知道什么、还差什么、下一步该去哪」压成一个结构化状态，传给下一轮。下一轮不是从零开始，是从这个状态继续。

听起来像 KV-cache 优化？不像。它优化的是「**思考流程**」，不是计算复用。

---

## 二、失败的轨迹到底是怎么失败的：Appendix A 的 5 类行为标注

论文 §3 给出一组失败轨迹分析（详细 prompt 在 Appendix A 的 Figure 6），把失败模式分 5 类：

- **A**：模型给出了最终答案（或者问用户要更多信息），**但过程中规划过的分支没全部走完**。
- **B**：模型给出了最终答案（或者问用户要更多信息），**过程中规划过的分支全部走完了**——这是合格失败。
- **C**：模型碰到 context 长度上限，**在某个分支卡了很久，没切换**。
- **D**：模型碰到 context 长度上限，**仍在多个分支之间探索，直到撞墙**。
- **E**：以上都不是。

分析用的分类器是 GPT-5，让它对失败轨迹打标。

论文的核心观察：A、C、D 这三类占了绝大多数——**模型规划能力是有的，问题是它规划完会忘，或者它忘了切换，或者它撞墙就放弃**。B 类是少数的「想清楚了再死」。

这件事在你贴的摘要里被翻译成「83%-93% 的失败轨迹存在『计划了却没走完』」。**这个比例数字 paper 主体没给精确值**，附录也没有公开汇总（Figure 6 的 prompt 是分类 prompt，不是统计表）。我用「绝大多数」来描述是安全的；要更精确的数字需要你贴的版本——本文不擅自补。

RE-TRAC 解决的恰好是 A/C/D 三类共同的根：**轨迹结束时的状态没有结构化地传给下一轮**。

---

## 三、方法：每条轨迹被压成一个 5+3 块的状态

RE-TRAC 的核心机制是「**轨迹 → 结构化状态 → 下一轮的输入**」：

```
S_t ← Compress(τ_t, S_{t-1}; C)
```

其中 τ_t 是第 t 轮的 ReAct 轨迹，C 是固定的压缩规范，S_t 是下一轮的初始 user message。

### 3.1 Base 版本（给小模型 / SFT 用）：5 块

附录 C.3.1 给出两套 prompt。**给基础模型的版本固定 5 块**：

1. **Current Answer** — 目前为止最佳支撑的部分答案，或者 `None`（无结论证据）。
2. **Facts & Evidence Collected** — 这条轨迹发现的所有事实条目，带来源标注与验证状态。
3. **Analysis & Conclusions** — 从证据推导出的逻辑结论，**显式链接到事实**。
4. **Source Inventory & Verification Status** — 所有访问过的来源 + 当前验证状态。
5. **Uncertainties, Limitations, Gaps** — 未知变量、数据歧义、阻塞最终决策的失败模式。

这 5 块的工程含义是：**它把「我查到的事实」「我推出来的结论」「我还没解决的疑问」三件事显式分开**。ReAct 失败的最大根因之一就是这三件事在自然语言轨迹里混在一起，越往后越糊；RE-TRAC 用固定 schema 强制让模型自己先做这一步分类。

### 3.2 Full 版本（给 frontier LLM 用）：5 块 + 3 块 audit

给强模型（o3、GPT-5、DeepSeek-V3.2、GLM-4.7 等）用的版本**多加 3 块审计 facet**：

6. **Failed Attempts** — 已经放弃、走不通、或者到 rollout 末尾没进展的具体计划。
7. **Uncompleted Proposals** — 在工具输出里冒出来但没追的潜在线索（URL、实体、数据点、关键词）—— 因为 token 限制、焦点转移、或者模型自己的遗漏。
8. **Discarded Possibilities** — 候选答案或关键证据因为未经核实的假设、幻觉、逻辑跳跃被丢掉的东西。

这 3 块是 RE-TRAC 真正想塞进去的「反向价值」。ReAct 的惯性是「我得到了 X，所以我走 X」；RE-TRAC 强迫模型把**「我得到的 X，但没追的 Y、丢掉的 Z」也写下来**，下一轮读到的就不是「当前最好的答案」，而是「当前最好的答案 + 所有未走过的岔路」。

### 3.3 状态作为下一轮的输入

§4.2 给的状态注入方式很直接：状态被 **prepend** 到下一轮的 user message，紧跟在 system prompt 之后。这避免了 prompt 模板级别的复杂集成——任何 ReAct agent 都能接上。

论文同时强调一个微妙的设计：「**状态保留多个未解决候选**」——它不强制单一路径，避免探索塌缩。这跟 Best-of-N 的「最后选最优」逻辑正好相反：Best-of-N 把多条独立轨迹归约到一个答案，RE-TRAC 把多条轨迹融合到一个**候选清单**。

---

## 四、递归执行：frontier 模型直接当测试时扩展

§4.3 写得很朴素：

> Re-TRAC 作为一种免训练（training-free）的 prompt 策略，适用于推理阶段的前沿模型，无需微调。

执行流程：

1. 定义一个 deep research query，设定最大轮数 N（默认 8）。
2. 第一轮用标准 ReAct 跑出完整轨迹。
3. 用专门设计的 prompt（Fig 9 / Fig 10）压缩成结构化状态。
4. 把状态作为下一轮的初始 user message，紧跟在 system prompt 之后。
5. 模型再次跑 ReAct，依此类推，直到第 N 轮。
6. **最后一轮的答案就是最终输出**。

`RT@8` 这个记号就是这么来的——**第 8 轮的答案当成最终答案**。

### 4.1 测试时扩展的基线：四种投票方法

§5.2 把 RE-TRAC 跟四种 test-time scaling 方法放在一起比：

- **Pass@1** — 单次出答案，基线。
- **Re-TRAC (RT@n)** — 第 n 轮答案。
- **Majority Voting (MV@n)** — n 次独立解，**投票取最多的**。
- **Weighted Voting (WV@n)** — n 次独立解，**模型给每个解一个置信度，按置信度加权投票**。
- **Best-of-N (Best@n)** — n 次独立解，**取置信度最高的那一个**。

投票类方法的共同假设是「**n 次独立**」——每次都要从头跑，不复用历史。RE-TRAC 把这一点打破：每次复用历史，但保留分支多样性。

### 4.2 BrowseComp300 跑分（Table 3）：RE-TRAC 在所有模型上最优

BrowseComp 全集太大，作者从里面随机抽 300 题作为 BrowseComp300 子集（论文说子集表现与全集很接近）。Table 3 给出 5 个模型 × 4 种方法的对比：

| Model | Pass@1 | RT@8 | MV@8 | WV@8 | Best@8 |
|---|---|---|---|---|---|
| **o4-mini** | 25.7 | **46.8** | 34.0 | 46.7 | 43.3 |
| **o3** | 54.9 | **69.8** | 64.3 | 69.0 | 68.0 |
| **GPT-5-medium** | 48.3 | **66.6** | 61.7 | 64.7 | 54.0 |
| **DeepSeek-V3.2** | 45.3 | **60.8** | 55.7 | 57 | 55 |
| **GLM-4.7** | 37.7 | **60.7** | 41.7 | 48 | 42.3 |

几个能直接读出来的信号：

- **RT@8 在五个模型上全部胜出**——这是 paper 的最强主张。
- **GLM-4.7 在 MV@8 上几乎没涨**（37.7→41.7，+4 pp），而 RE-TRAC 把同一模型推到 60.7（+23 pp）。论文对此的解读是：GLM-4.7 的 self-judgment 能力跟 o3/GPT-5 有差距，所以投票类方法对它基本无效——但 RE-TRAC 不依赖 self-judgment，它依赖的是「把历史写下来」这件事。
- **o3 Pass@1=54.9、RT@8=69.8、Pass@8=81.7**——RT@8 已经接近 Pass@8 上界 81.7%（差了 12 pp）。剩下 12 pp 是 AP@N（accuracy prefix）的空间——意味着 RE-TRAC 内部 8 轮之间其实有不少正确答案出现，**如果换更好的选择策略还能再涨**。

### 4.3 效率证据（Figure 5）：token 与工具调用单调下降

投票类方法的天花板是**资源随 n 线性增长**——n 次独立解就是 n 倍 token。

RE-TRAC 不一样：因为状态把搜索空间逐步收窄，**token 与工具调用随轮次单调下降**。Figure 5 给出 5 个模型的对照（GLM-4.7 / DeepSeek-V3.2 / GPT-5-medium / o3 / o4-mini），每张图都是 token 用量（x 轴）vs 准确率（y 轴）的散点 + 趋势：

- 投票类（MV / WV / Best-of-N）的散点是「**往右平移**」——更多 token、差不多准确率。
- RE-TRAC 的散点是「**往左下方走**」——更少 token、更高准确率。

论文给出的工程结论：**RE-TRAC 用约一半的资源达到更好的性能**。

这件事的工程含义比看起来重。当下 deep research agent 的部署成本里，token + tool call 调用费占大头，RE-TRAC 把成本曲线从「线性增长」变成「先增后减」，对一个每晚跑几千次的产品来说，是直接省钱的。

---

## 五、SFT 训练小模型：把 GLM-4.7 的 RE-TRAC 轨迹蒸馏下来

§4.4 干了一件 RE-TRAC 工程里最聪明的事：**用 GLM-4.7 自己当老师，给小模型当师傅**。

### 5.1 数据合成：33k 问答对的 entity-tree 方法

合成数据跟 InfoAgent（Zhang et al., 2025）一样：抓 Wikipedia 实体当根节点，沿着相邻关系建树，每个根到叶的路径转成一个问题，再用 o3 把子问题做 fuzzification（提高难度）。

结果：**33k 个 QA pair**。

### 5.2 蒸馏 GLM-4.7 的 RE-TRAC 4 轮轨迹

让 GLM-4.7 用 RE-TRAC 框架跑 4 轮，每轮上下文独立，所以一道题的解轨迹可以摊成 4 个训练样本 → **132k 原始样本**。

过滤规则：

1. 含无效工具调用的样本丢掉；
2. turn 数少于 15 的样本丢掉（避免太短的轨迹）；
3. 无有效最终答案的样本丢掉。

过滤后剩 **104k 高质量样本**——用 SFT 训练 Qwen3-4B-Instruct 和 Tongyi-DeepResearch-30B-A3B。

SFT 超参（Appendix Table 7）：

| Setting | Value |
|---|---|
| number of samples | 104k |
| learning rate | 2e-5 |
| batch size | 512 |
| max length | 65536 |
| warmup ratio | 0.05 |
| learning rate scheduler | constant |
| weight decay | 0.1 |
| Adam β1 | 0.9 |
| Adam β2 | 0.95 |

这组超参值得记一下：**batch size 512 + max length 65536**——意味着训练用的硬件至少 8 张 80GB 显存的卡跑张量并行才撑得住，这不是个人 GPU 玩得起的训练。

### 5.3 SFT 出来的两个 RE-TRAC 模型

- **RE-TRAC-4B** —— base Qwen3-4B-Instruct
- **RE-TRAC-30B-A3B** —— base Tongyi-DeepResearch-30B-A3B（30B-A3B 是 MoE 架构，3B 激活）

---

## 六、五个 benchmark 全图（Table 2）：同尺寸全最优

论文在五个 deep research benchmark 上把 RE-TRAC-4B / 30B 跟所有可比模型对照（Table 2）：

- **BrowseComp**（Wei et al., 2025）— 浏览检索的 hard subset
- **BrowseComp-ZH**（Zhou et al., 2025）— 中文版
- **GAIA**（Mialon et al., 2023）— 通用 AI 助手 benchmark
- **XBench**（Chen et al., 2025b）— 真实职业任务
- **HLE**（Phan et al., 2025）— Humanity's Last Exam

按模型尺寸分四档：

### 6.1 闭源模型档（参考线）

| Model | BC | BC-ZH | GAIA | XBench | HLE |
|---|---|---|---|---|---|
| Claude-4.5-Sonnet | 24.1 | 42.4 | 71.2 | 66.0 | 32 |
| o3 | 49.7 | 58.1 | 70.5 | 66.7 | 24.9 |
| OpenAI DeepResearch | 51.5 | 42.9 | 67.4 | — | 26.6 |
| GPT-5-high | 54.9 | 63.0 | 76.7 | 77.9 | 42 |
| Gemini-3-pro | 37.8 | 51.6 | 74.8 | — | 38.3 |

### 6.2 大开源模型档（> 70B）

| Model | BC | BC-ZH | GAIA | XBench | HLE |
|---|---|---|---|---|---|
| Kimi-K2-Thinking-1T | 60.2 | 62.3 | — | — | 51.0 |
| DeepSeek-V3.2-Thinking-685B | 67.6 | 65.0 | — | — | 40.8 |
| GLM-4.7-358B | 52.0 | 66.6 | — | — | 42.8 |
| MiniMax-M2-229B | 44.0 | 48.5 | 75.7 | 72.0 | 31.8 |

### 6.3 中等开源档（15B~70B）

| Model | BC | BC-ZH | GAIA | XBench | HLE |
|---|---|---|---|---|---|
| Tongyi-DeepResearch-30B-A3B | 43.4 | 46.7 | 70.9 | 75.0 | 32.9 |
| IterResearch-30B-A3B | 37.3 | 45.2 | 72.8 | — | 28.8 |
| WebSailor-V2-30B-A3B (RL) | 35.3 | 44.1 | 74.1 | 73.7 | 30.6 |
| **RE-TRAC-30B-A3B (Ours)** | **53.0** | **57.3** | **78.2** | **83.0** | 31.5 |

### 6.4 紧凑开源档（< 15B）

| Model | BC | BC-ZH | GAIA | XBench | HLE |
|---|---|---|---|---|---|
| InfoAgent-14B | 15.3 | 29.2 | — | 40.4 | — |
| WebExplorer-8B | 15.7 | 32.0 | 50.0 | 53.7 | 17.3 |
| AgentCPM-Explore-4B | 25.0 | 29.0 | 63.9 | 70.0 | 19.1 |
| NestBrowse-4B | 22.4 | 28.4 | 68.9 | 74.0 | — |
| **RE-TRAC-4B (Ours)** | **30.0** | **36.1** | **70.4** | **76.6** | 22.2 |

### 6.5 三个能直接读出的结论

**① 同尺寸内全最优**：

- RE-TRAC-30B-A3B 在 BC / BC-ZH / GAIA / XBench 四个 benchmark 上比 Tongyi-DeepResearch-30B-A3B（之前最强的 30B 基线）涨 8-10 pp；HLE 涨 -1.4 pp（退步）。
- RE-TRAC-4B 在所有 < 15B 模型里全 benchmark 全最优。

**② 30B 反超 358B 与 685B**：

- RE-TRAC-30B-A3B 在 BC 上 53.0% > GLM-4.7-358B 52.0%。
- 论文 §5.1 明确写：**"the RE-TRAC framework is able to compensate for the lack of model intelligence by manually expanding its search space."**

**③ 30B 在 GAIA 上 78.2% 超所有闭源模型**：

- Claude-4.5-Sonnet 71.2 / o3 70.5 / OpenAI DeepResearch 67.4 / GPT-5-high 76.7 / Gemini-3-pro 74.8。
- 论文 §5.1 把这个结果解读成 **"small models equipped with the Re-TRAC framework can replace those expensive proprietary products, serving as advanced on-device search agents."**

这是 30B-A3B 的 MoE 架构（30B 总参、3B 激活）带来的额外红利——单卡可部署。

### 6.6 HLE 是 RE-TRAC 的弱项

Table 2 里 RE-TRAC-30B-A3B 在 HLE 上 31.5%，比 Tongyi-DeepResearch-30B-A3B 的 32.9% 还低 1.4 pp；RE-TRAC-4B 在 HLE 上 22.2%，虽然在 < 15B 档还是最优，但绝对值远低于 GPT-5-high 42 / Gemini-3-pro 38.3。

论文 §6 / §5.1 没正面解释这个现象。**HLE 的设计是「极难的、需要真知识的题」，跟 BrowseComp 的「检索 + 多步推理」不太一样**——可以推测：RE-TRAC 的核心机制是「管理多轮探索」，如果一道题用一轮就能答完，那 RE-TRAC 的状态就退化成「重写一遍题目」，没有增益反而有损。这是一个值得未来工作继续追的盲区。

---

## 七、Ablations：SFT / Free-use prompt / Summarizer 三组实验

### 7.1 SFT 的真实增益（Table 4）

Qwen3-4B-Instruct 没经过深度的 deep research 任务预训练，它的初始 RT@8 成绩极低：

| Model | BC | BC-ZH | GAIA | XBench | HLE |
|---|---|---|---|---|---|
| Qwen3-4B-Instruct (RT@8) | 2.7 | 6.9 | 24.4 | 45.0 | 7.0 |
| RE-TRAC-4B | 30.0 | 36.1 | 70.4 | 76.6 | 23.5 |

BrowseComp 从 2.7% 到 30.0%——**10 倍以上的增益**。这个数字本身就是 paper 最硬的工程证据：RE-TRAC 框架 + SFT 数据的组合拳，让一个本来不会做 deep research 的小模型变成能做的。

### 7.2 Free-use prompt（Table 5）：状态会不会让模型卡在旧路径

论文发现一个有趣的失败模式：**模型过度依赖总结、卡在前一轮的搜索路径上、不肯扩展**。他们加了一个 prompt 显式告诉模型「**自由使用总结，主动扩大搜索空间**」。

o3 在 BrowseComp300 上的 8 轮对照：

| Round | w/o free-use | w/ free-use |
|---|---|---|
| 1 | 56.1 | 56.1 |
| 2 | 61.2 (+5.1) | 63.0 (+7.0) |
| 3 | 64.0 (+2.8) | 65.7 (+2.7) |
| 4 | 66.4 (+2.4) | 67.0 (+1.3) |
| 5 | 66.8 (+0.4) | 69.3 (+2.3) |
| 6 | 68.2 (+1.4) | 70.0 (+0.7) |
| 7 | 68.5 (+0.3) | 71.0 (+1.0) |
| 8 | **68.9** (+0.4) | **71.7** (+0.7) |

每轮 free-use 版本都赢，8 轮累计 +2.8 pp（68.9 → 71.7）。这是 paper 里对「AI 容易被自己的总结骗到」的一个具体反制：**显式让 AI 怀疑总结、主动扩大搜索**。

### 7.3 Summarizer 替换（Table 6）：4B 的压缩能力是天花板

让 RE-TRAC-4B 用 GLM-4.7 当总结者（summarizer）：

| Model | Self | GLM-4.7 |
|---|---|---|
| RE-TRAC-4B | 30.0 | **38.5** |
| RE-TRAC-30B-A3B | 53.0 | 52.4 |

**RE-TRAC-4B 换 GLM-4.7 当总结者涨 8.5 pp（30.0 → 38.5）**；RE-TRAC-30B-A3B 换 GLM-4.7 没变化（53.0 → 52.4）。

论文对此的解读很老实：**4B 模型的压缩能力弱，它的搜索能力没有被充分发挥**；30B 模型的压缩能力已经够用。换更大的 summarizer 不会让它更好。

但这条结论的另一面是：RE-TRAC 的状态质量**直接绑定模型的压缩能力**。这条结论会被两种不同的解读带偏：

- 乐观：换更强的模型当 summarizer，能立刻让 4B 涨 8.5 pp。
- 悲观：**模型既能执行、又要总结**这件事是 RE-TRAC 框架的内在依赖，模型压缩能力不强的 agent 用 RE-TRAC 收益有限。

论文选择把这个留给 future work。这是个诚实的工程态度——但也是「RE-TRAC 不适合所有 agent」的提醒。

---

## 八、Round-by-round 微观：Table 9-13 给的 8 轮细节

附录 Table 9-13 给出 5 个模型在 BrowseComp300 上 8 轮的逐轮成绩，包括 Acc%、Pass@N、RT@N、AP@N、MV@N、WV@N、Best@N 共 7 个指标。挑两个最有信息量的看：

**o3（Table 10）**：

| Round | Acc% | Pass@N | RT@N | AP@N | MV@N | WV@N | Best@N |
|---|---|---|---|---|---|---|---|
| 1 | 56.7 | 56.7 | 56.7 | 56.7 | 56.7 | 56.7 | 56.7 |
| 4 | 54.7 | 75.0 | 67.1 | 67.4 | 60.0 | 66.7 | 64.0 |
| 8 | 54.7 | **81.7** | 69.8 | 71.1 | 64.3 | 70.0 | 68.0 |

o3 的 RT@8 是 69.8，但 Pass@8 是 81.7——**还有 11.9 pp 是被「最后一轮的答案不是最好的那个」吃掉的**。AP@8 = 71.1（8 轮里至少有一轮答对），跟 RT@8 = 69.8 几乎贴在一起，说明 o3 大部分时候最后一轮是它的最佳轮次。

**o4-mini（Table 9）**：

| Round | Acc% | Pass@N | RT@N | AP@N | MV@N | WV@N | Best@N |
|---|---|---|---|---|---|---|---|
| 1 | 26.7 | 26.7 | 26.7 | 26.7 | 26.7 | 26.7 | 26.7 |
| 8 | 26.4 | 57.3 | **46.8** | 47.8 | 30.3 | 44.7 | 43.7 |

o4-mini 的 Pass@8 = 57.3，RT@8 = 46.8，AP@8 = 47.8——**Pass@8 比 RT@8 高 10.5 pp**。这意味着 o4-mini 的 RT@8 离它的理论上限还远，**未来用更好的选择策略（不只看最后一轮）还能再涨**。

---

## 九、作者对 RE-TRAC 在 2026 年 deep research 谱系里的位置

论文 §6 给出三个方向的 future work：

1. **集成强化学习**——用 RL 进一步优化「经验生成过程」。
2. **跨更多 agentic 任务的扩展**——不限于 deep research。
3. **提升 summarizer 能力**——回应 §7.3 的发现。

作者自己承认的两个局限（§6 + §5.1 隐含）：

- **HLE 提升有限**：RE-TRAC 框架对「需要真知识 + 单轮推理」的题型不擅长（Table 2 数据反向证明）。
- **串行多轮的延迟代价**：论文没评测 8 轮 RE-TRAC 的端到端延迟，理由是 TTS 方法默认延迟不是核心指标——但生产部署里 8 × 单轮延迟是个真问题。

### 9.1 与你贴的「系列定位」的对照

你提到 RE-TRAC 与 ContextRot / AgentSwing / ACE / GAM 形成一个 deep research agent 演进谱系：

- **ContextRot** 诊断「为什么必须管理历史」
- **AgentSwing** 解决「单条轨迹内何时切换策略」
- **ACE** 解决「每个历史步骤以什么形态进上下文」
- **RE-TRAC** 在「**轮次之间**」做文章，把每轮探索压成状态传下去

**这些对照是论文 Related Work 里没明确列出的**——paper 自己的引用是 IterResearch（Chen et al., 2025a，Markovian state reconstruction）、Resum（Wu et al., 2025，context summarization）、MemAgent（Yu et al., 2025，multi-conv RL-based memory agent）、InfoAgent（Zhang et al., 2025）。你提到的几个名字是**外部视角的延伸定位**，不是论文本身的 Related Work。我把这个解读保留下来供对照，但作为严谨边界，**本文不擅自把那些 paper 跟 RE-TRAC 之间的细节关系讲死**。

### 9.2 RE-TRAC vs GAM：你贴的「有趣对照」值得展开

GAM（如果你指的是 General Agentic Memory 一类的近期工作）主张「**别提前压缩，把所有历史留在上下文里，让模型自己管理**」。这条路在大模型 context window 越来越大的今天显得合理。

RE-TRAC 反过来：**显式压缩 + 显式结构化**。

两种思路在「什么粒度管理历史」上有结构性差异：

- **GAM 路**：信任大模型的 in-context 学习能力，不压缩、不分块；成本随对话长度线性涨。
- **RE-TRAC 路**：把状态写死成 5+3 块，下一轮只看状态不看历史；成本随轮次先增后减，但引入「summarizer 能力依赖」的耦合。

**两个思路在工程上对应不同的部署形态**：

- GAM 适合 context window 大（> 400k）、summarizer 弱的场景；
- RE-TRAC 适合 context window 中等、summarizer 强（或者能 SFT 一个强 summarizer）的场景。

RE-TRAC 的 §7.3 ablation 给出了这个边界的硬证据：4B 模型的 summarizer 太弱，RE-TRAC 收益就小；30B 模型的 summarizer 够强，RE-TRAC 全胜。这跟 GAM 的「信任 in-context 能力」是相反方向的工程假设。

---

## 十、复现清单：Table 7 + Table 8 + Fig 9-11

如果你想自己复现 RE-TRAC，下面三组信息是关键：

**训练超参（Table 7）**：

```
number of samples: 104k
learning rate: 2e-5
batch size: 512
max length: 65536
warmup ratio: 0.05
scheduler: constant
weight decay: 0.1
Adam β1 / β2: 0.9 / 0.95
```

**推理超参（Table 8）**：

| Model | Context | Temperature | Top P | Reasoning |
|---|---|---|---|---|
| o4-mini | 200k | — | — | medium |
| o3 | 200k | — | — | medium |
| GPT-5 | 400k | — | — | medium |
| DeepSeek-V3.2 | 140k | 1.0 | 0.95 | enabled |
| GLM-4.7 | 128k | 1.0 | 0.95 | — |
| RE-TRAC-30B-A3B | 128k | 0.7 | 1.0 | — |
| RE-TRAC-4B | 128k | 0.7 | 0.8 | — |

**工具接口（Appendix C.1）**：

- `search(query)`：Google Search Web API，返回 5 条结果。Tongyi 模型可接受 list 参数做批量搜索。
- `visit(urls, goal)`：抓网页 → Trafilatura 抽正文 → GPT-4o-mini 摘要。Tongyi 用单数 `url`；GLM 用 `open(url, pattern)`，输出只有 summary。

**评估验证器（Appendix C.2）**：用 o4-mini 当 verifier，按 BrowseComp 的 prompt（Figure 8）判定最终答案对错。

---

## 十一、一句话总结

RE-TRAC 的工程贡献不在「提出新压缩算法」——它做的事朴素到接近「**让 ReAct 跑 8 次，每次把状态写下来传给下一次**」。它的工程贡献在**用一组结构化的状态 schema，强迫模型把『我知道的 / 我推出来的 / 我没追的』三件事显式分开**，让深度搜索从「独立的多次试错」变成「带记忆的渐进学习」。

这件事在 BrowseComp 上对 o3 兑现了 54.9 → 69.8（+14.9 pp）、对 o4-mini 兑现了 25.7 → 46.8（+21.1 pp）的 Pass@1 提升，token 与工具调用随轮次单调下降。**它的本质成本不是算法——是 prompt 的纪律**。

当你下次让 AI agent 跑一个长程任务时，记住一件事：它的 Pass@8 通常远高于 Pass@1。问题是它不分享。**RE-TRAC 想做的事，就是把这个「不分享」修掉——靠的不是更强的模型，是更清楚的笔记**。

---

## 附：来源核验

本文所有数字对应到论文具体位置（**paper 内文 + 附录**）：

- **§4.1 + Appendix C.3.1**：5+3 块状态结构定义
- **§4.2**：状态作为引导式搜索更新
- **§4.3 + Appendix C.3.3**：默认 8 轮、最大轮数 N
- **§4.4 + Appendix B**：33k QA → 132k raw → 104k 过滤
- **Table 2**：5 个 benchmark × 4 档尺寸
- **Table 3**：BrowseComp300 上 5 模型 × 4 方法
- **Table 4**：SFT 前后 4B 对比
- **Table 5**：o3 八轮 + free-use 提示效果（68.9 → 71.7）
- **Table 6**：4B 换 GLM-4.7 总结者（30.0 → 38.5）
- **Table 7-8**：训练与推理超参
- **Table 9-13**：5 个模型 8 轮逐轮数据
- **Figure 2**：Pass@K 曲线
- **Figure 5**：token / tool call 用量 vs 准确率
- **Figure 6**：Appendix A 失败分类 prompt
- **Figure 9-11**：状态 prompt 模板

需要自己核实时，去 arXiv `https://arxiv.org/abs/2602.02486` 看 v1 PDF（2026-02-02 提交版）。

---

**写在最后**：RE-TRAC 给 2026 年的 deep search agent 工程带来的不是新模型——是新方法论。**多轮独立是浪费，多轮递归是累积**。前者把同一条搜索路径跑 N 次，每次都是新的起点；后者把上一轮的状态作为下一轮的起点，每次都是上次的最优继续。

这件事的边界很清楚——HLE 退步、串行延迟未评测、summarizer 能力依赖。但它的核心主张——**用一个固定 schema 强迫模型做笔记**——是任何团队都能在周一早上动手试的事。下一个跑长程任务的 agent，给它加上这 5 块结构化笔记，你大概会看到跟你预期不一样的结果。

这件事的本质，跟 OpenSpace 给 skill 加质量层、跟 leader 给 AI 写任务书、跟 Khazix 一句话描述 RE-TRAC 都能成立——**AI 时代的工程护栏，越来越多长在「结构化的中间表示」上**。模型够强、prompt 够结构、状态够清楚，三件事一起做，工程就能往前挪一格。