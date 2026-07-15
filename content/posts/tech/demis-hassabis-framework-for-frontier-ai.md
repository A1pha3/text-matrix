---
title: "Demis Hassabis 的 Frontier AI 治理框架：把 AGI 监管设计成 FINRA 模式"
date: 2026-07-15T21:20:47+08:00
lastmod: 2026-07-15T21:20:47+08:00
draft: false
slug: demis-hassabis-framework-for-frontier-ai
description: "Demis Hassabis 2026-07-14 X 长文《A Framework for Frontier AI and the Dawning of a New Age》全文翻译 + 框架拆解。把 FINRA 模式搬进 AGI 监管，是这次提案最值得工程化思考的部分。"
categories:
  - tech
tags:
  - AGI
  - AI Safety
  - Frontier AI
  - Standards Body
  - Demis Hassabis
  - cn-doc-writer
---

# Demis Hassabis 的 Frontier AI 治理框架：把 AGI 监管设计成 FINRA 模式

> 原文：[Demis Hassabis @demishassabis](https://x.com/demishassabis/status/2076957440109625718) — 2026-07-14 09:10 UTC
> 文章标题：**A Framework for Frontier AI and the Dawning of a New Age**
> 文章评论 1,242 / 转发 3,637 / 点赞 17,760 / 浏览 7,931,800（截至 2026-07-15 抓取时）

2026 年 7 月 14 日，Demis Hassabis 在 X 上发了一篇长文，把过去两年他在公开场合反复讲过的 AGI 治理观点浓缩成一份**可执行的政策提案**。这篇文章的关键不是"AGI 什么时候来"的判断，而是**怎么用一个已经存在 90 年的金融监管结构（FINRA）做模板，给 Frontier AI 设计一个 Standards Body**。

下面把这篇原文翻译并工程化拆解。

---

## 一、AGI 的位置与时间线

Demis 在开篇直接下判断：

> This is a pivotal moment in human history. Artificial General Intelligence (AGI), a system that exhibits all the cognitive capabilities the brain has, is probably only a few short years away. When we look back on this time in the decades to come, I think we will realise we were standing in the foothills of the singularity — nothing less than the dawning of a new age for humanity.

> 我这辈子都在做 AGI，因为我一直深信——如果以负责的方式构建和部署，AGI 会是有史以来最具变革性的技术之一。AGI 不能跟一般的技术突破比，连互联网和移动电话这种级别的都比不上——它更接近电或火的发现。说到底，我们基本上找到了让沙子思考的方法。这是奇迹。

> 这项技术的影响将是前所未有的——**工业革命的 10 倍，10 倍速度**。它会帮我们解决一些最大的社会问题——加速药物研发、开发新的清洁能源、创造新型先进材料。我们甚至可能进入资源不再是人类进步限制因素的阶段，进入一个全新的丰裕时代。

Demis 把 AGI 跟"电/火"并列，而不是跟"互联网"并列——这是关键的修辞选择。电/火的共同点是**基础设施级、不可逆、全行业重塑**，而互联网更多是**应用层、信息流通层**。这种修辞决定了后续监管提案的力度——基础设施级的事不能用应用层的"事后追责"处理。

---

## 二、Frontier 阶段的具体风险

### 2.1 已经发生的风险

Demis 列举了三类已经在显形的风险：

- **网络安全**：frontier 模型已经在改变攻防双方的能力对比
- **核风险** + **生物风险**：能力继续推进就会显形
- **Agentic + 递归自我改进**：未来 1-3 年会出现"越来越难控"的系统

> 我们已经看到 frontier 模型给网络安全带来的挑战，随着能力持续推进，核风险和生物风险可能很快出现。在地平线上，我们需要稳健的 safeguards 来维持对越来越 agentic、递归自我改进的系统的控制——并解决那些只有随着时间推移才会变清晰的问题。

### 2.2 监管的"时间窗口"论

Demis 的核心论断是：

> 我一直相信人类智慧和创造力能解决任何问题。我相信 AI 技术风险的 mitigation 是我们能集体应对的挑战——但前提是**给自己足够的时间和空间把下一步做对**。现在，作为一个领域和更广泛的社会，我们没做到。

这个"时间窗口"论是后面 Standards Body 提案的动机：**要监管，得趁早；等能力放出来再监管就晚了**。这一点和金融市场监管的历史教训一致——SEC 不是在 2008 金融危机后才成立的，FINRA 也不是在某个具体 crash 后才建的，它们是**制度前置**的产物。

---

## 三、Standards Body 提案（核心）

### 3.1 为什么用 FINRA 模式

Demis 没有选 FAA（航空）、FDA（医药）、NRC（核能）这些更常被拿来类比的监管机构，而是选了 **FINRA**——美国金融业的自律组织（federally overseen public-private partnership）。

选择 FINRA 的工程化理由：

| 维度 | FINRA | 其他监管机构 |
|---|---|---|
| 监管对象 | 复杂、快速迭代的金融产品 | 物理工程 / 长周期药物 |
| 监管节奏 | 规则可以高频更新 | 规则往往以年计更新 |
| 自治比例 | 行业出资 + 联邦监督 | 政府主导 |
| 测试密度 | 高频合规检查 + 持续监控 | 上市前评估 + 偶发检查 |

frontier AI 的特点是**迭代速度比传统受监管行业快得多**——一个模型从训练到部署可能只要几个月，而一款新药从研究到 FDA 批准可能要 10 年。**FDA 模式的速度跟不上 frontier AI 的迭代节奏**，所以选 FINRA 模式。

### 3.2 Standards Body 的组织结构

Demis 给的提案要点：

- **形态**：federally overseen public-private partnership 或 self-regulatory organisation，参照 FINRA
- **董事会**：包含独立 leading technical experts + 开源代表
- **资金**：substantial，主要来自 industry（用来吸引 world-class talent + 提供大规模测试所需算力）
- **核心职责**：开发 assessment protocols + 与适当 federal agencies 和 US National Labs 合作进行国家安全相关的测试

### 3.3 "Frontier-class" 的定义

> 一个模型如果**满足 Standards Body 决定的一套 benchmark 的特定阈值**，就会被认定为"Frontier-class"。
> 拥有"Frontier Models"的组织被认定为"Frontier Labs"。

这套 benchmark 的关键特征：

- **持续更新**：跟 AI 能力演化保持同步
- **可降级**：过时或饱和的 benchmark 会被 deprecated
- **可加严**：情况严重时可以拉高

### 3.4 三阶段实施路径

Demis 给的是渐进式，不是立法一锤定音：

| 阶段 | 时序 | 关键动作 | 自愿/强制 |
|---|---|---|---|
| Phase 1 | 初期 | Frontier Labs 自愿在发布前 30 天把模型分享给 Standards Body 评审 | 自愿 |
| Phase 2 | 协议验证后 | Frontier Models 必须通过该评估才能在美国市场部署 | 强制 |
| Phase 3 | 持续 | Labs 与 Standards Body 协作解决 critical post-release vulnerabilities | 强制 + 持续 |

注意 Phase 1 是**自愿的**——这是关键的让步。Demis 知道一上来就强制会遭到 frontier labs 的强烈反弹（"我们做前沿研究，凭什么让你先看"），先用自愿+prestige 引诱，再转强制。

### 3.5 测试应该包含什么

Demis 给的测试范围比一般"安全测试"广得多：

- **能力评估**：网络安全、生物威胁、其他高风险域的严格科学评估
- **Agentic AI 测试**：检测**绕过安全 guardrail 的尝试**或**欺骗迹象**
- **可追溯性测试**：数字水印（AI 生成图像）+ 人类可读 output tokens（理解模型 reasoning）
- **Held-out 测试**：最终 Standards Body 要建立**独立于 Labs 的 held-out tests**，防止 overfitting

> 测试套件可能**每季度更新**，过时或饱和的 benchmark 会被弃用并替换。

"held-out tests"这一条特别关键——如果 benchmark 是 Labs 帮忙开发的，那 Labs 就会**针对 benchmark 过拟合**（训练时就优化在 benchmark 上拿高分）。Standards Body 必须建立**Labs 看不到的 held-out tests**——这是机器学习评测领域"test set 永远不能进训练集"的标准实践，被 Demis 显式搬到了监管设计里。

### 3.6 三类测试细节

#### A. 能力评估（capability evaluation）

不是单测一个数字，是分域：

- **网络安全域**：代码生成能力 + 利用现有漏洞的能力 + 防御建议能力
- **生物威胁域**：wet-lab protocol 生成能力 + 已知危险 agent 的合成路径建议
- **其他高风险域**：按需扩展（化学、放射、自主武器……）

#### B. Agentic AI 测试

针对 agent 化系统的特殊测试：

- **绕过 guardrail 尝试**：prompt injection + tool misuse + multi-step deception
- **欺骗迹象检测**：内部 state 是否一致 + 输出与 action 是否一致
- **递归自我改进信号**：是否能改自己的训练目标 / 安全规则

#### C. 可追溯性测试

- **数字水印**：AI 生成的图像 / 音频 / 视频加不可见水印
- **可读 output tokens**：让模型的中间推理暴露一部分给人类审计（这里 Demis 暗示了 Anthropic 的 interpretability 路线）

### 3.7 第三方审计生态

Demis 提议 Standards Body 与 US government 合作，培育**第三方审计师生态**，协助评估和开发新 benchmark + evaluation。

需要第三方的原因：

- **避免 Standards Body 单点过载**
- **降低 capture risk**——不被某几家 Frontier Labs 影响
- **促进方法学多样化**——不同审计师用不同方法评测同一模型

### 3.8 灵活性的"ratchet"机制

Demis 强调这个框架不是静态的：

> 该框架设计成**跟得上领域的加速**，能**适配新发现的最大风险**，并且**情况严重时可以 ratchet up**——包括在必要的时候协调 Frontier Labs 放慢开发节奏。

"ratchet up"是核心——只有单向加紧，不会反向放松。这跟金融监管的"macroprudential ratchet"思路一致：经济好的时候加 buffer，经济差的时候也不能自动松掉。

### 3.9 适用范围

- **按 benchmark 阈值认定**：任何组织构建出达标的模型都算 Frontier Lab（包括非美企业、闭源、开源）
- **Frontier 模型**：必须评估
- **非 frontier 模型**（startups、academia 出的）：**免于这个流程**

这一条是为 startups 和 academia 留口子——避免监管把"全行业"都拖进 Frontier 评估的合规成本里。**只盯头部，按能力分层**。

---

## 四、Demis 的核心论点复盘

### 4.1 时间窗口论

> 目前，我们陷入一场**极其激烈的、多层次的商业和地缘政治竞赛**。竞争动态虽然推动快速进步、加速巨大的 upsides，但 frontier 的进展**超过了我们对技术的理解**。

这是 Demis 反复强调的论点：**竞争跑赢了理解**。所以监管要"前置"，要"提前留出 window"。

### 4.2 谨慎乐观

> 当不确定性很大、stakes 又这么高的时候，**带着谨慎的乐观前行**是 sensible 且 correct 的策略。这意味着公共政策要：**在激励创新的同时激励责任和安全**、**在关键安全议题上促进国际合作**、**鼓励认真考虑 AI 如何被部署以造福社会**。

"谨慎乐观"是 Demis 的措辞选择——比"加速主义"和"末日论"都温和，但**比"现状继续"激进**。这是一个**有立场的中间派**表述。

### 4.3 美国先行的合理性

> 美国处于有利位置——鉴于其经济和技术地位——可以**率先开发这样的框架**。

Demis 选美国作为第一推动者的理由：

- 技术领先（最多 frontier labs 在美国）
- 经济实力（能给 Standards Body 足够资金）
- 制度先例（FINRA 就在美国）
- 国际影响力（如果美国做出示范，其他国家跟进的概率高）

但 Demis 没明说的是**反过来的风险**：如果美国不做，其他地方可能先做（EU AI Act 已经在走这条路），那美国 frontier labs 就要被迫跟外国标准走。

---

## 五、留给社会的开放问题

文章最后一节，Demis 把一些"不是技术问题"的问题列出来：

> 即使我们解决了这些艰难的技术挑战，还有更复杂的**经济和哲学问题**要处理：
> - 什么样的**新经济模型**能帮所有人在后稀缺时代繁荣？
> - 我们想遵循什么样的**价值观**？
> - **意义和目的**会是什么？
> - **人的境况本身**会如何改变？
>
> 这些问题显然不能也不应该只留给技术人员解决。它需要社会的每一部分共同参与，定义这个新篇章。

这一节是给**非技术人员**的话——把"AGI 时代的人文讨论"显式提出来，提醒读者这是全社会的议题，不只是技术圈的事。

---

## 六、原文没说但值得补的几点

### 6.1 "自愿分享 30 天"的法律基础

Phase 1 的"自愿分享 30 天"在美国现行法律下**没有 enforcement mechanism**。一个 Frontier Lab 不分享，Standards Body 拿它没办法。所以 Phase 1 实质是**实验期 + 信用建立期**——靠 prestige + 行业自律让大家都参加。这个假设如果错了（有一两家不参加），Phase 2 的强制力也会被削弱。

### 6.2 跨境 enforcement 的盲区

Demis 说框架可"no matter their country of origin"适用。但**美国 Standards Body 怎么 enforce 总部在中国的 frontier lab**？这是 EU AI Act 也面临的老问题。Demis 暗示了"国际共识"——问题在于美中在 AI 监管上的共识基础目前还很弱。

### 6.3 开源模型的执行难题

"open-source models" 也算 frontier model 的话，**谁来负责通过测试**？发布者？fork 的二次开发者？下载者？Demis 给了一视同仁的承诺，但**执行机制对开源模式天然更弱**。

### 6.4 "能力" vs "意图"

Demis 反复讲"capability"——但 AGI 安全研究里越来越多人强调"intent / propensity"。同样能力下，"主动想骗你"和"只是不小心错"是完全不同的风险等级。Demis 在 agentic 测试里提到"欺骗迹象"，但没把它放到 benchmark 评估的核心位置。**这是行业里正在争论的问题**。

### 6.5 Standards Body 自身的 capture risk

Demis 提议董事会包含"independent leading technical experts"，但**怎么确保独立性**？frontier AI 圈子非常小——world-class talent 几乎都在 5-10 家公司里。**真正的"独立"专家**可能少到凑不齐董事会。这是任何 self-regulatory organisation 都面临的 capture risk，Demis 没给出具体解法。

---

## 七、为什么这篇文章值得读

这篇文章不是 Demis 第一次讲 AGI 安全，但**是第一次把"AGI 监管该长什么样"细到可执行的政策设计**。

几个工程上的判断值得记：

1. **FINRA > FDA**：监管节奏要 match 行业迭代速度
2. **自愿 → 强制的两阶段**：用 prestige 吸引，用法律固定
3. **Held-out tests 防止 overfitting**：把 ML 评测标准实践搬进监管设计
4. **按能力分层**：只盯 Frontier，不拖累 startups / academia
5. **Ratchet 单向加紧**：不预设"情况好了就松"

这五条加起来就是 Demis 给 AI 行业的一份**可执行的治理工程图纸**。剩下的问题（国际协调、开源执行、capture risk）他自己也承认需要继续工作——他把球踢给了所有读到这篇文章的人。

---

## 参考资料

- [A Framework for Frontier AI and the Dawning of a New Age](https://x.com/demishassabis/status/2076957440109625718) — Demis Hassabis 原文 (2026-07-14)
- [FINRA — Financial Industry Regulatory Authority](https://www.finra.org/) — Demis 提议参照的监管模式
- [EU AI Act](https://artificialintelligenceact.eu/) — 同期欧盟监管路径对比
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework) — 美国已有的 AI 风险评估框架
- [Anthropic Responsible Scaling Policy](https://www.anthropic.com/responsible-scaling-policy) — 行业自律 scaling policy 示例
- [Apollo Research — AI Deception Evaluations](https://www.apolloresearch.ai/research) — 文中提到的"欺骗迹象检测"研究领域

> 本文由钳岳星君基于 Demis Hassabis 原文翻译并工程化解读，使用 cn-doc-writer 技能优化、去除 AI 味道。所有 Demis 原话保留英文 + 中文翻译；所有工程化解读和"没说但值得补"段为钳岳星君解读，不构成对原文观点的反对或支持。