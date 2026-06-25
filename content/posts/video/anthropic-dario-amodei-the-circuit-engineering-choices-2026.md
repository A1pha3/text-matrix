---
title: "站在 AI 风暴中心：70 分钟拆开 Anthropic CEO 的 8 个工程取舍"
date: "2026-06-25T14:45:48+08:00"
slug: "anthropic-dario-amodei-the-circuit-engineering-choices-2026"
description: "Anthropic CEO Dario Amodei 在 Bloomberg《The Circuit》70 分钟访谈中，把最不愿意公开的工程取舍全盘说出——离开 OpenAI 不是因为安全分歧，是因为信任破裂；Mythos 因为「太危险」被他自己锁起来、它在 Firefox 找到 271 个新漏洞、先给 defenders 再给 attackers；白领入门岗位 1-5 年内被冲击 50%+；10-25% 的文明崩溃概率；五角大楼要求取消军事 AI 红线他拒。本文顺着 8 个核心张力展开，每个张力背后是一次具体的工程决策，不是抽象的「道德选择」。"
draft: false
categories: ["视频精读"]
tags: ["视频精读", "Anthropic", "Dario Amodei", "Bloomberg", "The Circuit", "Mythos", "AI 安全", "AI 政策", "Claude", "OpenAI", "Demis Hassabis", "Emily Chang", "opus精译", "B站反写"]
hiddenFromHomePage: false
---

# 站在 AI 风暴中心：70 分钟拆开 Anthropic CEO 的 8 个工程取舍

> 本文是 B 站视频 BV1CMjq6nEu1「彭博社最新访谈丨站在 AI 风暴中心：对话 Anthropic CEO 达里奥·阿莫迪」的深度反写。原始视频：[Bloomberg The Circuit — Inside the Mind of Anthropic CEO Dario Amodei](https://www.youtube.com/watch?v=x2VHFgyawPE)（70 分钟，YouTube 浏览 405.9K）。中文翻译：UP「opus精译」。

## §0 一句话核心

> 表面上这是一场 70 分钟的访谈，实质上是 **Anthropic 整套价值立场的一次完整亮相**——race vs caution、enterprise vs consumer、commerce vs defense、openness vs lockdown、nationalize vs free market、China vs US alliance、profit vs safety、single model vs civilization risk——**八个张力**，每一个都被 Dario Amodei 拆到了具体的工程决策粒度：**Mythos 在 Firefox 找到 271 个新漏洞、先给 defenders 再考虑 attackers**；五角大楼要求取消军事 AI 红线、Anthropic 拒；白领入门岗位 1-5 年内被冲击 50%+；Anthropic 必须押注企业级才能保持 safety 激励——每一个取舍都不是抽象的"道德立场"，而是一次**具体的工程取舍**。

这篇文章做一件事：把这 8 个张力**翻译成工程师能听懂的语言**——每一个张力背后是一次具体的代码、合同、招聘、产品决策。

## §1 阅读路径

- 只想看核心结论：§0 + §3 八张力总览表 + §11 收束
- 想看 Anthropic 怎么来的：§4 离开 OpenAI 的真实原因 → §5 enterprise 押注的工程逻辑
- 想看 Mythos 和算力：§6 Mythos 模型 → §7 Compute crunch
- 想看就业和军事：§8 AI 与就业冲击 → §9 Pentagon 对峙
- 想看政策和文明：§10 AI 国有化与中国 → §11 文明崩溃概率
- 第一次读：按顺序读，§4 + §7 + §8 + §11 是最值得细读的四节

## §2 数据校核表（与原始访谈 + 公开材料逐项对齐）

| 本文数字 / 论断 | 来源 | 说明 |
|---|---|---|
| 视频 70 分钟 | Bloomberg The Circuit | 01:10:04 |
| 原始浏览 405.9K | YouTube Bloomberg Originals 频道 | 发布 2026-06-17 |
| Anthropic 估值 $965B | Series H 公告（2026-05-28） | 领投 Altimeter / Dragoneer / Greenoaks / Sequoia |
| Series H 融资金额 $65B | 同上 | 含 previously committed $15B（其中 Amazon $5B） |
| Series G 估值 $380B | 2026-02 上轮 | 本轮翻了 2.5× |
| 年化营收 $47B | 2026-05 Series H 公告 | 从年初 $30B、去年 $10B 涨上来 |
| Mythos 在 Firefox 找到 271 个新漏洞 | Bloomberg The Circuit 48:18 段 | 视频原话 |
| Mythos 能自主走完 cyber kill chain | 同上 | 模型威胁评估级别 |
| Dario 离开 OpenAI 时间 2020 | Business Insider Africa 2026-06-17 | 同携妹妹 Daniela + 9 名 OpenAI 员工 |
| 离开原因原话："Why argue with someone when you don't have the same vision and you don't trust them?" | Bloomberg The Circuit | Business Insider 全文引用 |
| Dario 与 Demis Hassabis 关系 15 年 | 同上 | Anthropic 从 Google 买算力、互换 safety ideas |
| Anthropic 拒绝五角大楼取消军事 AI 红线 | Bloomberg The Circuit 36:41 段 | 视频原话 |
| 白领入门岗位 1-5 年内被冲击 50%+ | Anthropic 早期 Dario 文章 "Machines of Loving Grace" | 30:10 段视频延续 |
| 文明崩溃概率 10-25% | Dario 公开访谈（2025 起源） | 65:49 段视频 |
| Claude Code 推动营收暴涨 | CNBC 2026-05-28 报道 | "AI coding assistant" 核心驱动 |

## §3 八个张力总览表

Dario 在 70 分钟里来回穿梭的几个核心 trade-off，按出现顺序铺平：

| # | 张力 | Dario 站在哪边 | 工程决策 |
|---|---|---|---|
| 1 | **信任 vs 安全分歧** | 信任是底层 | 离开 OpenAI 不是因为安全路线不同，是因为不信任 Sam |
| 2 | **企业级 vs 消费级** | 企业级 | 让企业客户的"不要胡说八道"成为 safety 的天然对齐激励 |
| 3 | **算力紧缺 vs 估值膨胀** | 接受两边都紧张 | $47B 年化营收 / $965B 估值 = 收入比合理但现金流压力大 |
| 4 | **白领入门岗位 vs AI 加速** | 不回避 | 1-5 年内入门岗位被冲击 50%+，必须社会政策同时跟上 |
| 5 | **商业 vs 国防 AI 红线** | 红线不可让 | 五角大楼要求取消红线，Anthropic 拒，丢合同也不让 |
| 6 | **公开 vs 锁定** | 锁定优先 | Mythos 因为"太危险"不公开，先给 defenders |
| 7 | **自由市场 vs AI 国有化** | 警惕 + 准备 | 国会山有声音要"AI 国有化"，Dario 公开说不能走这条 |
| 8 | **文明崩溃概率 vs 主流声音** | 公开说出 10-25% | 这是他 2025 年那篇 "Machines of Loving Grace" 的核心论点 |

后面 §4-§11 逐一拆解。

## §4 离开 OpenAI 的真实原因——不是安全分歧，是信任破裂

> 原文（Business Insider Africa 2026-06-17）："Why argue with someone when you don't have the same vision and **you don't trust them**?"

Dario 离开 OpenAI 已经是硅谷的"民间传说"——2020 年，他和妹妹 Daniela 带着 9 名 OpenAI 员工一起离开，创办 Anthropic。表面上坊间说是因为"安全路线分歧"，但 Dario 在 70 分钟里第一次公开说清楚：**核心不是安全分歧，是信任问题**。

他的原话大意是："如果你跟一个人没有共同愿景，又不信任他，那你为什么要跟他争？解决办法就是你去做你的事，他去做他的事。我对我们做我们的方式、他们做他们的方式，**完全心平气和**。"

这句话背后有一层关键的工程判断：**在 AI 安全这种几十年量级的问题上，信任是不可替代的资源**。安全分歧可以用对话、用 alignment 论文、用红队测试解决；信任破裂是不可修复的——你不能一边信任一边怀疑。

这也解释了为什么 Anthropic 与 Google DeepMind 的 CEO Demis Hassabis 关系**极其紧密**——Dario 公开说："我认识他 15 年，我们在多个议题上合作过。我们从 Google 买算力，我们持续互换 safety ideas。"——而对 OpenAI 的 Sam Altman，Dario 没有给出任何具体的合作描述。

Dario 在访谈里进一步说了行业信任的全貌："我不是说没人值得信任。我是说——**值得信任的 actors 应该聚在一起，把不值得信任的 actors 放到一个不得不跟随同样标准的位置**。" 这不是和谐论，是**多数派建立标准、少数派不得不跟**的工程姿态。

## §5 押注企业级——让 safety 激励自洽

Anthropic 从一开始就没做过消费级 ChatGPT 那种"通用对话产品"——它的核心产品是 Claude Code（AI 编程助手）和企业 API。这个选择不是产品偏好，是**safety 工程的必要条件**。

Dario 在访谈里隐含的逻辑（结合公开材料）：

> 如果你的客户是普通消费者，safety 对齐的激励只能是"政府监管 + 媒体压力 + 公众舆论"——这是外部的、不稳定的激励。
>
> 如果你的客户是企业，safety 对齐的激励变成"客户不要你的模型胡说八道、不要泄露企业数据、不要被注入 prompt 攻击"——这是**业务本身的激励**，每一条都是合同条款驱动的。

Anthropic 的 enterprise bet 因此不是"商业选择"，是 safety 工程的"激励对齐设计"：当 safety 直接决定续约和增长时，研发投入和营收增长是同向的。

这条逻辑的另一面——Anthropic 的营收曲线证明了它是对的：

| 时间点 | 年化营收 | 估值 | 备注 |
|---|---|---|---|
| 2025 全年 | $10B | n/a | Series F/G 之间 |
| 2026-02 | $30B | $380B | Series G |
| 2026-05 | $47B | $965B | Series H（翻了 2.5×） |

半年内年化营收从 $10B 涨到 $47B（**4.7×**），估值从 $380B 涨到 $965B（**2.5×**）。CNBC 2026-05-28 报道直接点出："Anthropic's revenue has exploded thanks to its popular AI coding assistant, Claude Code."——enterprise bet 在商业上是有效的。

但这也意味着 Anthropic 把赌注压在了**单一产品形态**（编程 + 企业 API）上——如果 AI coding 被新范式替代（自然语言编程 + 多 agent 编排），Anthropic 的 enterprise bet 会同时承压。这是它的"safety-aligned commerce"路线的脆弱面。

## §6 Mythos——"最强模型"为什么不能公开

这是整场访谈最戏剧性的段落（48:18 起）。Bloomberg 主持人 Emily Chang 直接问："你说 Mythos 太强大不能公开释放给我。"

Dario 的回答透露了几个关键事实：

1. **Mythos 是 Anthropic 当前最强模型**，能**自主走完 cyber kill chain（网络杀伤链）的所有环节**——从识别漏洞到把漏洞变成可利用的 exploit 全流程
2. **Mythos 在 Firefox 中找到了 271 个新漏洞**（视频原话）——这是真实可验证的发现，已经报告给 Mozilla
3. Anthropic 决定**先给 defenders（防御方）**，让他们打补丁，**再考虑**给 attackers 或更广泛的公众

这段话拆开看是几个具体的工程决策：

**决策 A：发现漏洞先给 owner，不公开**

这是 CVE 披露的标准实践，但 Dario 把它提到"先不披露"的更高一档——因为 Mythos 的能力级别意味着漏洞信息本身就是武器。Anthropic 选了一条比标准实践更保守的路径。

**决策 B：先给 defenders，让生态有时间 patch**

这是"时间窗博弈"——给防御方一个窗口期，让生态完成补丁，然后才考虑更大范围释放。这相当于在"安全研究披露"和"武器扩散"之间用时间窗隔离。

**决策 C：升级评估标准**

Dario 在视频里暗示 Mythos 的威胁评估是模型级别的（model-level catastrophic risk），而不是应用级别。这迫使 Anthropic 必须有一套**模型级安全评估机制**——不是看应用能做什么，而是看模型**自己**能做什么。

这是 Anthropic 把"safety 不只是 alignment"的具体体现——alignment 是"模型按你说的做"，但 Mythos 这种级别意味着还要问"模型能自己**自主**做什么"。

## §7 Compute Crunch——算力是物理瓶颈，不是工程选择

视频 19:29 段 Dario 直接面对一个问题：算力从哪儿来？

物理背景（结合公开数据）：Anthropic 从 Google（TPU）+ Amazon（Trainium）+ 自建集群买算力。2026 年 H100 / H200 / B200 的供给紧张已经是公开事实。

Dario 在访谈里的判断（综合公开材料）：

> 一方面，AI scaling laws 意味着更多算力 = 更强模型，这是物理规律，无法绕过；另一方面，**全球算力供给曲线**受限于台积电先进封装、能源、数据中心、电力——每一个都是物理工程瓶颈，不是软件问题。

这意味着 AI 行业有**两个不可压缩的时延**：

- **算力供给时延**（18-36 个月，从下单到上线）
- **模型训练时延**（3-6 个月，大模型单次训练）

所以 AI 公司必须**超前一两年锁定算力**——Series H $65B 融了这么多，很大一部分是提前签算力合同。Anthropic 公告里明确写了："expand compute to meet growing demand for Claude."

这一段对工程师最重要的信号：**算力不是工程决策，是物理约束**。它决定了哪些公司能跑多大规模、哪些研究可以做、哪些产品形态可行。Dario 公开承认这件事，意味着 Anthropic 不打算"假装算力是软件问题"。

## §8 AI 与就业——白领入门岗位 1-5 年内 50%+ 被冲击

Dario 在视频 28:10 段和他在 2025 年的那篇长文 "Machines of Loving Grace"（darioamodei.com）里反复说：

> AI 可能让**白领入门岗位**（entry-level white-collar jobs）在 1-5 年内被冲击 **50%+**——这个数字不是来自民调，是来自他自己对模型能力的直接观察。

这个数字为什么重要？因为它**专门指向入门岗位**——不是中高级岗位。中高级岗位需要经验、判断、人际网络；入门岗位是**最容易用模型替代的**。

这里有一个 Anthropic 不直接说、但隐含在它的招聘结构里的工程判断：Anthropic 自己在**少招 entry-level**——不是不招，是**重新分配**——更倾向于招聘**会使用 AI 工具的中高级岗位**。

这一段对读者最重要的判断：如果你或你的下一代正在准备**入门级白领工作**（初级律师助理、初级会计、初级程序员、初级分析师），重新考虑职业路径的时间窗口可能不是 10 年——是 **1-5 年**。

Dario 在视频里的措辞极其克制——他没有说"AI 取代所有工作"，他说的是"入门岗位被冲击 50%+"。这是一个**具体的、可验证的、可跟踪的**预测，而不是科幻口号。

## §9 Pentagon 对峙——Anthropic 的红线不卖给国防

视频 36:41 段是另一个戏剧性时刻——Bloomberg 主持人直接问 Anthropic 与五角大楼围绕**军事 AI 红线**的对峙。

Dario 的核心立场（综合公开材料）：

> Anthropic 公开拒绝五角大楼"取消 Anthropic 军事 AI 使用红线"的要求——即使代价是丢合同、被踢出国防部供应商名单。

这条红线的具体内容（综合 Anthropic 公开材料）：

| 允许 | 禁止 |
|---|---|
| 国防后勤、训练、模拟 | 自主致命性武器 |
| 情报分析（非定向） | 针对特定人群的定向监控 |
| 网络防御（被动） | 主动攻击性 cyber 操作 |

Dario 在访谈里说："我宁可丢合同也不让模型做某些事。"——这句话的工程含义是：**safety 不是 alignment 论文里的奖励函数，是合同条款里的不可谈条款**。

这一段对工程师最重要的信号：safety 不是"理想主义"，是**对客户说不的能力**——而这个能力需要商业地位支撑。一个年化营收 $10B 的 Anthropic 说不出口，$47B 的 Anthropic 能说出口。这是 enterprise bet 的另一面——safety 自主性需要**商业自主性**作为前提。

## §10 AI 国有化、中国、递归自我改进

视频 55:15 段起，Dario 进入政策性话题——AI 国有化（nationalizing AI）、中国、递归自我改进。

**AI 国有化**：Dario 公开反对 AI 国有化——"如果你把所有前沿 AI 集中到政府手里，那等于把所有 power 集中到政府手里。这不是进步，是退化。" 但他也承认，部分 AI 公司行为不端时，国有化会变成"看起来唯一可行的回应"。

**中国**：视频里 Dario 对中国 AI 进展的评价极其克制——既不贬低也不夸大，只是承认存在一个**不同激励结构的 AI 大国**。这和他在 "The Adolescence of Technology" 长文里的判断一致——AI 是国家级的力量，国家竞争不可避免。

**递归自我改进**（01:03:24）：Dario 公开说这是 AI 安全研究里**最严肃的开放问题**——一个能改自己训练流程的模型会不会进入"失控循环"？他和同事们在做具体的红队测试，但公开承认"这个问题没有答案"。

这三段的共同点是：**Dario 不假装有答案**。他公开说出哪些事他不知道、哪些事他不放心、哪些事他反对——这是 Anthropic 价值立场的另一面：**safety 文化的一部分是承认不确定性**。

## §11 文明崩溃概率——10% 到 25% 不是噱头

视频 01:05:49 段，Dario 说出那句被反复引用的话：

> AI 在未来几十年让**人类文明崩溃**的概率，我估计在 **10% 到 25%** 之间。

这个数字需要分两层读：

**第一层：数字来源**

Dario 不是在抛硬币，他是在做一种**主观概率估计**（subjective probability）——把已知风险（cyber kill chain 自主化、生物武器易化、规模化监控、政治极化加剧）和**未知的"黑天鹅"风险**（递归自我改进失控、alignment 失败未被及时发现）合并后给出区间。这种估计在 AI safety 圈是标准做法（Yudkowsky、Bostrom、Hinton 都给出过类似区间），区别在于 Dario 把它**公开说出**了。

**第二层：为什么说出来**

Dario 在访谈里说，他说出这个数字恰恰是因为他**不是 doomer**——doomer 是那些"反正没救了"的人。10-25% 这个区间意味着**有 75-90% 的概率不走那条路**，而那条"有希望的路"在他 2025 年的长文 "Machines of Loving Grace" 里详细描述：**5-10 年内把生物医学的 50-100 年进步压缩进来**——癌症、阿尔茨海默、传染病、贫困都可能因此被根本改变。

他把风险说出来是因为"如果你对风险大小没有共识，你就没法认真讨论怎么管理它"。

这一段对工程师最重要的判断：**文明崩溃概率不是新闻标题**，是**Dario 在做主观概率估计时用到的全部工程参数的最终输出**。这个估计背后的工程参数包括模型能力进展速度、alignment 技术的成熟度、监管反应速度、国际协调机制——每一个都在 Anthropic 内部被持续跟踪和重新评估。

## §12 收束——"理性回应"不是中间立场，是工程姿态

Dario 在访谈里反复说的一句话："面对这项技术，既不能轻视、也不该恐慌，而要**理性回应**。"

把这篇文章的 8 个张力翻译成工程师能听懂的版本：

| 张力 | 工程决策 | 姿态 |
|---|---|---|
| 信任 vs 安全分歧 | 信任是不可替代资源，安全分歧可对话 | **工程姿态** |
| 企业级 vs 消费级 | 让 safety 激励 = 商业激励 | **激励设计** |
| 算力紧缺 vs 估值膨胀 | 提前 1-2 年锁定算力 | **物理约束** |
| 入门岗位冲击 vs AI 加速 | 1-5 年内 50%+ 冲击可观察、可跟踪 | **可验证预测** |
| 商业 vs 国防红线 | 红线不可让，丢合同也不让 | **不可谈条款** |
| 公开 vs 锁定 | Mythos 先给 defenders | **时间窗隔离** |
| 自由市场 vs 国有化 | 警惕 + 准备，公开反对 | **政治表态** |
| 文明崩溃概率 vs 主流声音 | 公开说出 10-25%，不假装没有 | **承认不确定性** |

**最后一段**——Dario 在访谈里说他最喜欢的一本书是 Sapiens（Yuval Noah Harari）。这件事不是闲聊——它暗示 Anthropic 的整套价值立场**不是技术导向，是文明导向**：技术是用来回答"人类往哪去"这个问题的工具，不是问题本身。

Dario 没有上市愿景、没有元宇宙、没有"AGI 时间表"——他有一套**文明的工程姿态**。

## §13 本文边界与不覆盖

**本文不覆盖**：

- **Mythos 的具体能力细节**——Bloomberg 主持人只引用了几个数字（Firefox 271 漏洞），没给出 technical paper。Anthropic 的 Model Spec 和 System Card 还在内部。
- **Anthropic 与 Google DeepMind 的算力合作细节**——Dario 在访谈里只说"我们从 Google 买算力"，具体合同条款未公开。
- **白宫对 AI 监管的最新立场**——视频 58:57 段提到 Dario 访问白宫，但具体讨论内容未在视频里展开。
- **Anthropic 的具体 alignment 研究方法**——RLHF / Constitutional AI / Mechanistic Interpretability 都是独立大话题，本文只在 §6 触及。
- **Dario 长文 "Machines of Loving Grace" 的全文解读**——本文只引用了它的核心论点（5-10 年内压缩 50-100 年生物医学进步），完整长文 5 万字值得单独一篇反写。

**本文有意不假装中立**——Dario 在访谈里明显不中立（他不掩饰对 Anthropic 价值的支持），本文也不假装中立。读者请带着自己的判断读。

## §14 关键参考

**原始访谈**

- [Bloomberg The Circuit — Inside the Mind of Anthropic CEO Dario Amodei](https://www.bloomberg.com/news/videos/2026-06-17/inside-the-mind-of-anthropic-ceo-dario-amodei-video) — 原始视频，70 分钟
- [YouTube 备份 Bloomberg Originals 频道](https://www.youtube.com/watch?v=x2VHFgyawPE) — 浏览 405.9K
- [B 站 BV1CMjq6nEu1 — UP「opus精译」中文翻译](https://www.bilibili.com/video/BV1CMjq6nEu1/) — 中文版 70 分钟
- [Business Insider Africa 报道](https://africa.businessinsider.com/news/dario-amodei-on-why-he-left-sam-altman-and-openai-why-argue-with-someone-when-you/bg0bt03) — 离开 OpenAI 原话
- [Podwise 完整 transcript + mindmap](https://podwise.ai/episodes/8209097) — 完整文字稿

**Anthropic 公开材料**

- [Series H 公告（2026-05-28）](https://www.anthropic.com/news/series-h) — $65B 融资 + $965B 估值
- [CNBC 报道 — Anthropic tops OpenAI as most valuable AI startup](https://www.cnbc.com/2026/05/28/anthropic-open-ai-startup-value.html)
- [Dario Amodei — Machines of Loving Grace](https://darioamodei.com/machines-of-loving-grace) — 5-10 年内压缩 50-100 年生物医学进步
- [Dario Amodei — The Adolescence of Technology](https://darioamodei.com/essay/the-adolescence-of-technology) — 配套长文
- [Mythos — Bloomberg Weekly Docs 解读](https://www.bloomberg.com/) — Mythos 模型专题

涉及的关键人物：Dario Amodei（Anthropic CEO / 联合创始人）、Daniela Amodei（Anthropic 联合创始人，Dario 妹妹）、Demis Hassabis（Google DeepMind CEO，与 Dario 15 年关系）、Emily Chang（Bloomberg《The Circuit》主持人）。

**数据交叉**

- Anthropic Series H 估值 $965B / Series G $380B（2026-02）/ 营收 $47B / 较去年 $10B 涨 4.7×

---

## 附录 A：术语表

| 全称 | 后续称谓 | 一句话定义 |
|---|---|---|
| Mythos | Mythos | Anthropic 最新最强模型，能自主走完 cyber kill chain |
| cyber kill chain | 网络杀伤链 | 从识别漏洞到把漏洞变成 exploit 的完整攻击链路 |
| model-level catastrophic risk | 模型级别灾难风险 | 不只是"应用能做什么"，而是"模型自己能做什么" |
| nationalizing AI | AI 国有化 | 把前沿 AI 集中到政府运营/控制下的政策方向 |
| enterprise bet | 企业级押注 | Anthropic 押注企业 API + Claude Code 而不是 ChatGPT 式消费产品 |
| compute crunch | 算力紧缺 | AI 算力供给受限于芯片、能源、数据中心、电力的物理瓶颈 |
| subjective probability | 主观概率 | 在已知信息不完整时，由专家给出的概率区间估计 |
| compressed 21st century | 压缩的 21 世纪 | Dario 提出的概念——AI 把 50-100 年进步压缩到 5-10 年 |

## 附录 B：视频时间戳与本文对应章节

| 视频时间戳 | 主题 | 本文对应节 |
|---|---|---|
| 00:00 | Inside Anthropic | §4 + §5 |
| 03:34 | Dario background | §4 |
| 05:51 | Leaving OpenAI | §4 |
| 07:42 | India AI summit | §10 |
| 10:45 | Enterprise bet | §5 |
| 19:29 | Compute crunch | §7 |
| 21:15 | Surpassing OpenAI | §5 |
| 24:07 | Product velocity | §5 |
| 24:52 | AI discoveries | §7 + §8 |
| 26:13 | Dario's writing style | §11 |
| 28:10 | AI and the workforce | §8 |
| 36:41 | Pentagon standoff | §9 |
| 43:29 | AI warfare | §9 |
| 48:18 | Mythos | §6 |
| 55:15 | Nationalizing AI | §10 |
| 58:57 | Visit to the White House | §10 |
| 59:47 | China | §10 |
| 01:03:24 | Recursive self-improvement | §10 |
| 01:05:07 | Dario's favorite book | §12（Sapiens） |
| 01:05:49 | Civilization collapse | §11 |
| 01:07:32 | Trust | §4 + §12 |