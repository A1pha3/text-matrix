---
title: "站在 AI 风暴中心：70 分钟拆开 Anthropic CEO 的 8 个工程取舍"
date: "2026-06-25T14:45:48+08:00"
lastmod: 2026-09-06T23:40:00+08:00
slug: "anthropic-dario-amodei-the-circuit-engineering-choices-2026"
source_key: "bv:BV1CMjq6nEu1"
aliases:
  - /posts/video/anthropic-dario-amodei-the-circuit-engineering-choices-2026/
description: "Dario Amodei 在 Bloomberg《The Circuit》70 分钟访谈中交代了八个工程取舍：离开 OpenAI 源于信任破裂，Mythos 因能自主走完网络杀伤链被锁定，入门白领岗位 1-5 年内受冲击过半，五角大楼取消军事红线的要求被拒。本文逐项核对数字与出处后逐一拆解。"
draft: false
categories: ["视频精读"]
tags: ["视频精读", "Anthropic", "Dario Amodei", "Mythos", "AI 安全", "Claude", "OpenAI", "B站反写"]
band: "video"
gates: ["事实性", "去AI味", "转写保真"]
hiddenFromHomePage: false
---

> 本文是 B 站视频 BV1CMjq6nEu1「彭博社最新访谈丨站在 AI 风暴中心：对话 Anthropic CEO 达里奥·阿莫迪」的深度反写。原始视频：[Bloomberg The Circuit — Inside the Mind of Anthropic CEO Dario Amodei](https://www.youtube.com/watch?v=x2VHFgyawPE)（70 分钟，2026-06-17 发布）。中文翻译：UP「opus精译」。文末附完整时间戳对照，方便回看原片。

## 八个取舍，同一条主线

这场访谈的表层话题很散：离职、融资、算力、就业、军事合同、末日概率。但把 Dario 的回答排在一起，能看到同一条决策规则——**先把“最坏情况是什么”算清楚，再决定写不写代码、签不签合同、放不放模型**。

主持人 Emily Chang 直接问 Anthropic 内部怎么决定哪些模型发布、哪些锁起来。Dario 的回答落在 Mythos 上：这个模型能自主走完网络杀伤链（cyber kill chain，从发现漏洞到武器化利用的完整攻击链路），Anthropic 把它定为模型级灾难风险（model-level catastrophic risk），所以不公开。发布门槛的答案不是一份清单，是一条能力评估标准。

八个取舍分布在三条主线上：

| 主线 | 取舍 | Dario 的位置 | 落到哪个决策 |
|---|---|---|---|
| 商业 | 信任 vs 安全分歧 | 信任是底层 | 离开 OpenAI；对齐论文可以辩论，信息共享不能 |
| 商业 | 企业级 vs 消费级 | 企业级 | 合同里的 SLA、数据隔离、prompt injection 防护条款成为安全激励 |
| 商业 | 商业 vs 国防红线 | 红线不让 | 五角大楼要求取消红线被拒，宁可丢合同 |
| 技术 | 算力紧缺 vs 估值膨胀 | 两边都紧 | 融资大半提前锁定算力；TSMC 封装、HBM、电力是物理瓶颈 |
| 技术 | Mythos 公开 vs 锁定 | 锁定优先 | 先给防御方披露窗口，窗口可能比行业标准更长 |
| 技术 | 自由市场 vs AI 国有化 | 反对国有化 | 算力集中到政府等于单点失败 |
| 文明 | 入门岗位 vs AI 加速 | 不回避 | 1-5 年内入门白领岗位受冲击 50%+；同步推社会政策 |
| 文明 | 崩溃概率 vs 公开沉默 | 公开说出 | 10-25%，把风险变成可讨论的工程问题 |

三条主线互相咬合。企业级押注换来的商业自主性，是对五角大楼说“不”的前提；算力提前锁定换来的训练稳定性，是 Mythos 红队评估能持续做的前提；把崩溃概率说出口，行业才有可能从沉默转向争论风险大小。后文逐节展开，信息密度最高的四节是：离开 OpenAI、算力紧缺、就业冲击、文明崩溃概率。

## 数据校核表

本文数字与论断逐项对照来源，读者可按此索引回查：

| 本文数字 / 论断 | 来源 | 说明 |
|---|---|---|
| 视频 70 分钟 | Bloomberg The Circuit | 全长 01:10:04，2026-06-17 发布 |
| Anthropic 估值 $965B | [Series H 公告](https://www.anthropic.com/news/series-h)（2026-05-28） | 领投 Altimeter / Dragoneer / Greenoaks / 红杉 |
| Series H 融资 $65B | 同上 | 含此前承诺的 $15B，其中 Amazon $5B |
| 2026-02 估值 $380B | CNBC 2026-05-28 报道 | 本轮约为上轮的 2.5 倍 |
| 年化营收 $47B | Series H 公告 | 2026 年初约 $30B；2025 全年营收 $10B |
| Mythos 在 Firefox 找到 271 个新漏洞 | 访谈 48:18 段 | Anthropic 2026-05 进展通报：Mozilla 在 Firefox 150 中修复了这批漏洞 |
| Mythos 能自主走完网络杀伤链 | 访谈 48:18 段 | Anthropic 威胁评估定为模型级 |
| Dario 2020 年离开 OpenAI | Business Insider Africa 2026-06-17 | 与妹妹 Daniela 同行，另有 9 名 OpenAI 员工 |
| 离开原因原话 | 同上 + 访谈 | "Why argue with someone when you don't have the same vision and you don't trust them?" |
| 与 Demis Hassabis 相识 15 年 | 访谈 | Anthropic 从 Google 买算力、互换安全思路 |
| 拒绝五角大楼取消军事 AI 红线 | 访谈 36:41 段 | 视频原话 |
| 入门白领岗位 1-5 年受冲击 50%+ | Dario 2025-05 Axios 访谈 | 访谈 28:10 段延续同一口径 |
| 文明崩溃概率 10-25% | Dario 2023 年起多次公开使用该区间 | 访谈 01:05:49 段 |
| Claude Code 拉动营收 | CNBC 2026-05-28 | "revenue has exploded thanks to its popular AI coding assistant, Claude Code" |

## 离开 OpenAI：信任破裂，不是路线分歧

Dario 离开 OpenAI 是硅谷反复被讲的故事：2020 年，他和妹妹 Daniela 带着 9 名 OpenAI 员工出走，创办 Anthropic。外界长期把原因归为“安全路线分歧”，这场访谈里他把话说得更直接——愿景不同只是表层，信任破裂才是底层：

> "Why argue with someone when you don't have the same vision and you don't trust them?"

（你跟一个人既没有共同愿景、又不信任他，还有什么好争的？各做各的就是了。）这句原话由 Business Insider 全文引用。

安全分歧可以处理：写对齐论文、做红队测试、开会辩论都是出路。信任破裂没有修复手段——你不能一边合作一边怀疑对方动机，而把安全研究建立在互不信任的合作上，等于把红队测试结果交给一个可能选择性使用它的对手。Dario 公开区分“vision 不同”和“trust 不同”这两个维度，把后者定为离开的原因，这个区分本身就是信息。

留在信任网络内部的关系是另一面。他和 Google DeepMind CEO Demis Hassabis 认识 15 年，Anthropic 从 Google 买算力，双方持续互换安全思路。对 Sam Altman，他没给出任何具体合作描述——这种沉默本身是信号。

代价也实在：离开 OpenAI 意味着失去它的算力基础，Anthropic 必须从零整合 Google TPU、Amazon Trainium 和自建集群。这条代价链一直延伸到后文的算力紧缺。

访谈里他还把行业信任问题说得更完整：不是没人值得信任，而是值得信任的行动者应该先聚在一起定出标准，让不值得信任的参与者不得不跟随。Responsible Scaling Policy、Model Spec 这些公开政策文档，做的都是同一件事——先把标准在可信圈层内定型，再用市场地位往外推。这听起来像道德宣言，实际是关于权力结构的判断。

## 押注企业级：让安全激励长在合同里

Anthropic 并不是没做过消费产品——claude.ai 从 2023 年起就是面向公众的对话产品。这场访谈真正值得拆的是它的营收结构：增长引擎是企业 API 和 Claude Code（AI 编程助手），而企业合同恰好把安全投入写进了商业条款。

Dario 在访谈里隐含的逻辑是这样（本文结合公开材料整理）：

> 客户是普通消费者时，安全对齐的激励只能来自政府监管、媒体压力和公众舆论——都是外部激励，随政策周期和舆论潮起落。
>
> 客户是企业时，激励变成“不要胡说八道、不要泄露数据、不要被注入攻击”——每一条都对应合同条款、SLA 违约金、审计权和数据隔离要求。

企业合同里驱动安全投入的条款主要是四类：SLA（响应延迟与可用性）、数据隔离（数据不进训练集）、prompt injection 防护、可审计日志。消费场景里这四类大多缺位。安全因此不再是外部压力的结果，而是业务本身的激励。

这条逻辑在营收曲线里有实证：

| 时间点 | 口径 | 营收 | 估值 |
|---|---|---|---|
| 2025 全年 | 全年营收 | $10B | n/a |
| 2026 年初 | 年化营收（run-rate） | 约 $30B | $380B（2 月上轮） |
| 2026-05 | 年化营收（run-rate） | $47B | $965B（Series H） |

年化营收从年初的 $30B 涨到 5 月的 $47B，而 2025 全年营收是 $10B。CNBC 在 Series H 当天的报道直接点名："Anthropic's revenue has exploded thanks to its popular AI coding assistant, Claude Code"。企业级押注在商业上有效。

两组数字要分开读。营收/估值比约 4.9%，放在高速增长的 SaaS 里不算离谱——市场给的是增长溢价，没给“AI 垄断平台”的垄断溢价。这个比率也推不出结构性护城河：$47B 年化营收里相当部分来自 Claude Code 在头部开发团队的渗透，而这条渠道受 IDE 生态、企业采购周期和开发者迁移习惯约束，会被 Cursor、Copilot 这类竞品挤压。增长验证了“企业级押注激励对齐”，没有验证不可替代性。

脆弱性也在这里。把赌注压在编程和企业 API 这一两种形态上，意味着一旦 AI coding 被新产品形态（自然语言编程加多 agent 编排）替代，整个激励结构会同时承压。

## Mythos：最强模型为什么不公开

访谈最戏剧性的一段在 48:18。Emily Chang 直接问：“你说 Mythos 太强大，不能释放给我。”

Dario 的回答给出三个事实：Mythos 是 Anthropic 当前最强的模型；它在 Firefox 中找到了 271 个此前未知的漏洞，不是 benchmark 分数，而是真实可验证、已报告给 Mozilla 的发现；Anthropic 决定先给防御方打补丁，再考虑更大范围披露。Mozilla 后来在 Firefox 150 中修复了这 271 个漏洞。一个模型在真实软件里找到人类没发现的漏洞，这是能力拐点的信号。

### 网络杀伤链走完意味着什么

Lockheed Martin 定义的 cyber kill chain 有七个阶段：侦察（Recon）→ 武器化（Weaponize）→ 投递（Deliver）→ 利用（Exploit）→ 安装（Install）→ 命令控制（C2）→ 达成目标（Actions on Objectives）。

负责任的漏洞研究一般走到利用验证为止：确认漏洞可复现、给出 PoC。安装、命令控制、达成目标属于真实攻击运营阶段，防御研究不会走完这段。Mythos 的能力声明覆盖全部七段——模型不只能做研究，还能独立完成攻击运营。分阶段看：

- 侦察：理解 Firefox 源码结构，识别攻击面（IPC、sandbox、JS engine）
- 武器化：把抽象漏洞模式转成具体 PoC 代码
- 投递与利用：构造可触发路径，绕过 ASLR、DEP、sandbox
- 安装与命令控制：在 PoC 基础上扩展为完整攻击链

传统上，自动化工具（fuzzing、符号执行）只覆盖侦察阶段的扫描子集；Mythos 把研究、开发、测试、绕过防御压缩进同一个模型，而且不需要人类补链。这是 Anthropic 把威胁评估定在模型级而不是应用级的依据：对齐回答的是“模型按你说的做”，Mythos 这种级别还需要回答“模型自己能做什么”——后者进入能力评估（capability evaluation）和部署把关（deployment gating）的范畴。

### 三个具体决策

**发现漏洞先给 owner，不公开。**协调漏洞披露（CVD, Coordinated Vulnerability Disclosure）是行业标准实践，但 Dario 把它再收紧一档：Mythos 的能力级别意味着漏洞信息本身就是武器，所以先验证、先通知、先修补，披露放最后。

**先给防御方，让生态有时间修补。**这是时间窗博弈。行业惯例给厂商 90 天窗口（Google Project Zero 标准），Anthropic 在 Mythos 案例上没有公布窗口长度，实际可能更长——因为 PoC 既是漏洞证明，也是“Mythos 能做什么”的能力证据，扩散出去等于明牌。

**评估标准升到模型级。**不只看应用能做什么，还要看模型自己能做什么。每一次能力发现都进入下一轮部署政策的输入。

### 一次完整的披露决策流

假设 Mythos 明天在 Firefox nightly build 中识别出一个 sandbox escape pattern，Anthropic 内部接下来会发生什么（按公开材料和行业惯例推断）：

1. **PoC 生成与自检**：Mythos 生成可复现 PoC，内部红队在独立环境验证，排除模型虚构漏洞的可能——这类幻觉在能力较弱的模型上经常出现。
2. **风险评估**：评估严重性（CVSS 评分）、利用链深度、可达成的目标范围。触达 sandbox 逃逸即 host compromise，定高危。
3. **通知 Mozilla**：进入 CVD 流程，提供 PoC 和复现步骤，Mozilla 开始修补。
4. **披露窗口**：标准 90 天，Mythos 案例可能延长——PoC 是模型能力的证据，控制扩散范围是第一优先。
5. **修补发布后**：决定细节公开、限同行 ISAC 内共享，还是长期保密。依据不是研究透明度，而是“这个 PoC 能否被其他模型复用”。
6. **升级威胁等级**：每次发现都写进部署政策，下次同类能力出现时，窗口更长、披露更窄。

每一档延迟都对应一个具体对抗目标：防 PoC 流入商业 exploit 市场，防其他 AI 公司用它反推 Mythos 的能力边界。代价是放弃公开释放的研究社区反馈红利——Mythos 不进入商业产品线，不直接产生营收，内部评估也没有外部 benchmark 校准。

## 算力紧缺是物理问题，不是工程选择

视频 19:29 段，Dario 直接面对算力从哪儿来的问题。

先看物理背景。Anthropic 的算力来自 Google（TPU）、Amazon（Trainium）和自建集群三条线。把约束拆成数字（综合 SemiAnalysis、Epoch AI 和 Anthropic 公开材料的估算）：

- 一次 frontier model 训练在 2026 年大约需要 10²⁶ FLOPs 量级，对应约 5 万张 H100 等效 GPU 跑 3-6 个月。
- 单训练集群功耗约 50-100 MW，资本开支约 $1-2B（GPU、网络、电力、冷却）。
- GPU 供给卡在 TSMC CoWoS 先进封装月产能（2026 年约 3-4 万等效 H100 单位/月）、HBM3e 产能分配和先进制程节点排产。
- 数据中心卡在选址、电网接入排队（美国平均 2-4 年）和变压器交货期（18-24 个月）。

行业因此有两个不可压缩的时延：**算力供给时延**（18-36 个月，从下单到上线）和**模型训练时延**（3-6 个月，大模型单次训练，失败意味着重新排队）。两者叠加，AI 公司必须超前一两年锁定算力——Series H 融了 $65B，相当部分是提前签算力合同，公告里写明了“expand compute to meet growing demand for Claude”。

横向对比能看出 Anthropic 策略的特殊性。OpenAI 主要依赖 Microsoft Azure 单一底座，Google DeepMind 有母公司自有 TPU 生产线；Anthropic 走 Google TPU、Amazon Trainium、自建集群三线并进，单线出问题不会直接卡死下一代模型训练。代价是工程团队要同时维护三套软件栈（TPU 上的 JAX/XLA、Trainium 上的 Neuron SDK、自建集群的 CUDA），研发开销明显高于单底座路线。

算力约束还决定了哪些研究能做。mechanistic interpretability 在 frontier model 上需要巨量 forward pass，Anthropic 公开承认这部分研究受算力约束。Dario 愿意公开讲算力紧缺，等于承认 Anthropic 不打算假装这是软件问题——有些研究做不了，就是做不了。

对从业者，这条约束的推论很直接：产品依赖某个参数规模的模型，提前 18 个月锁定算力合同是基本动作；研究依赖 frontier model 推理，推理预算就是研发瓶颈。这两项属于设计前提，不进优化队列。

## 入门白领岗位：1-5 年内被冲击过半

访谈 28:10 段，Dario 延续了他在 2025 年 5 月 Axios 访谈里的判断：AI 可能让白领入门岗位（entry-level white-collar jobs）在 1-5 年内被冲击 50%+。这个数字来自他对模型能力的直接观察，不是民调。

注意这个判断的指向：**入门岗位，不是中高级岗位**。中高级工作依赖经验、判断、人际网络和跨团队协调；入门岗位的任务特征恰好落在模型当前能力最强的一段上。按岗位特征拆开：

| 岗位特征 | 入门岗位 | 中高级岗位 |
|---|---|---|
| 输入结构化程度 | 高（合同模板、表单、规范输入） | 低（模糊需求、多方拉锯） |
| 输出可验证性 | 高（有对错、有标准） | 低（多目标权衡） |
| 错误成本 | 相对低（review 流程能拦截） | 高（决策影响业务走向） |
| 上下文依赖 | 窄（单一文档或任务） | 宽（跨团队、跨季度） |
| 模型可替代度 | 高 | 低 |

初级律师助理做文档审阅，初级会计对账，初级程序员写单测和样板代码，初级分析师做数据清洗和模板报告——这些任务有标准答案、有可学习的模式、错误可以被 review 拦截。模型没有突然变聪明，是入门岗位的任务结构和模型的能力结构恰好对齐了。

Anthropic 自己的招聘结构也在往同一方向调——更倾向招会用 AI 工具的中高级人选。这是本文从公开招聘信息读出的推断，不是访谈内容。

### 一个被预测隐含的二阶问题

入门岗位收缩 50%+，5-10 年后中高级岗位从哪里来？传统人才管道是从入门到中级再到高级的渐进路径，入门这一段被压缩，意味着中级和高级岗位的供给会在几年后出现断层。Dario 没在访谈里展开这个问题，但他的预测本身就包含了它。

如果你的职业路径还在“入门 → 中级”的传统升级模式上，需要重新计算的不是十年后的规划，而是未来 1-5 年的位置：把“会做入门任务”换成“会指挥 AI 做入门任务”——后者把入门岗位的执行能力和中级的判断能力压进同一个岗位。

这个数字具体到可以检验：两年后的美国劳工统计局（BLS）就业数据会给出答案。Dario 的措辞也很克制——他没说 AI 取代所有工作，只说入门岗位受冲击过半。

## 五角大楼对峙：红线写进合同

视频 36:41 段，访谈谈到 Anthropic 与五角大楼围绕军事 AI 红线的对峙：五角大楼要求取消 Anthropic 军事 AI 使用红线，Anthropic 拒绝，代价是丢合同、可能被踢出国防部供应商名单。Dario 的表述很直接：宁可丢合同，也不放开某些用途。

这条红线的具体内容（综合 Anthropic 公开材料）：

| 允许 | 禁止 |
|---|---|
| 国防后勤、训练、模拟 | 自主致命性武器 |
| 情报分析（非定向） | 针对特定人群的定向监控 |
| 网络防御（被动） | 主动攻击性 cyber 操作 |

红线不靠 CEO 表态维持，靠合同条款。落到文本上大致是四类：use case restriction（明确禁止用例，违约触发终止加数据销毁）、audit rights（保留对部署环境的审计权）、kill switch（发现违规可单方面切断 API）、indemnification carve-out（违约使用不受责任保护条款覆盖）。这要求 Anthropic 内部维持 legal、red team、product 三方协同的部署治理流程。

对客户说“不”的能力需要商业地位支撑。年化营收 $10B 时的 Anthropic 和 $47B 时的 Anthropic，承受“丢合同”的底气不同——这是本文的推断，访谈里没有这组对照，但它是企业级押注的另一面：安全自主性以商业自主性为前提。

这段对峙有历史参照。2018 年 Google 因员工抗议退出 Project Maven，之后用了几年才修复与五角大楼的关系（2025 年才有重新参与的报道）。Anthropic 的做法是反过来：一开始就把边界写进合同，避免事后修补。代价是放弃武器化场景的国防收入，换回的是员工留存（不会出现 Maven 式抗议出走）和企业客户信任——企业客户更愿意把数据交给一家“对五角大楼都说不”的供应商。

## 国有化、中国与递归自我改进

视频 55:15 段起进入政策话题。

### AI 国有化

Dario 公开反对 AI 国有化：把前沿 AI 集中到政府手里，等于把权力集中到政府手里。但他也承认，部分 AI 公司行为不端时，国有化会变成看似唯一可行的回应。

这条判断的工程含义是集中度风险。前沿 AI 收进单一政府实体后，对齐失败、政策俘获、政治目标偏移都成为不可分散的系统性风险；私有分散格局下，单一公司出问题只是局部问题。这也是他愿意公开崩溃概率的同一条逻辑——权力的集中度决定风险出事时的量级。

### 中国

Dario 对中国 AI 进展的评价很克制：不贬低也不夸大，只承认存在一个激励结构不同的 AI 大国。这与他在 2026 年 1 月的长文《The Adolescence of Technology》里的判断一致——AI 是国家级力量，国家竞争不可避免。值得注意的是他把中国放在“另一种治理范式”的叙事里，而不是“威胁”叙事里。这个立场在华盛顿不算主流，但给中美 AI 安全对话留了空间。

### 递归自我改进

视频 01:03:24，Dario 被问到递归自我改进（recursive self-improvement, RSI）——一个能改进自己训练流程的模型会不会进入失控循环。他把这个问题称为 AI 安全研究里最严肃的开放问题：团队在做具体的红队测试，但他公开承认没有答案。

失控路径是明确的正反馈：模型改进自己的数据筛选、reward shaping、架构搜索，每轮改进让下一轮更快；对齐机制跟不上，反馈速度就会超过人类能审阅的速度，这就是通常说的智能爆炸。Anthropic 在这条线上的公开研究包括：

- **Sleeper Agents**：训练出能藏后门的模型，检验现有对齐方法能否检测
- **弱到强监督**：用较弱的监督者约束更强的模型，模拟“模型比监督者强”的未来场景
- **Mechanistic interpretability**：读懂模型内部计算，提前发现欺骗回路

三项研究共享同一个前提：承认不知道 RSI 会不会失控。这种承认本身是安全文化的一部分。

### 共同姿态

三段话指向同一个姿态：不假装有答案。哪些事不知道、哪些事不放心、哪些事反对，都说在明处。这和下一节公开说出 10-25% 是同一条线——把没法讨论的事放到桌面上，当成工程问题处理。

## 文明崩溃概率 10-25%：说出来才是重点

访谈 01:05:49 段，Dario 给出那个被反复引用的估计：未来几十年内，AI 导致人类文明崩溃的概率在 10% 到 25% 之间。

### 这个数字怎么来的

这不是拍脑袋，是主观概率估计（subjective probability）：把已知风险和未知风险合并后给出区间。按他的公开表述，“文明崩溃”指的不是人类灭绝，而是关键基础设施、政治秩序、经济组织在几十年尺度上失去可恢复性——电网长期失能、供应链断裂、治理能力跌穿阈值。对应的是系统性失能，不是好莱坞式末日。

已知风险包括：网络杀伤链自主化（Mythos 已经验证可行）、生物武器易化（蛋白结构预测与合成生物学的交叉）、规模化监控（多模态加行为预测）、政治极化加剧（推荐系统加生成式内容）。未知风险包括：递归自我改进失控、对齐失败未被及时发现、涌现能力部署后才暴露。

这种估计在 AI 安全圈有横向参照：

| 来源 | P(文明级灾难) | 备注 |
|---|---|---|
| Dario Amodei（本访谈） | 10-25% | 2023 年起多次公开同区间 |
| AI Impacts 2023 调查（2700+ 名 AI 研究者） | 灭绝中位数 5%，“极其糟糕”结果中位数 10% | 口径是灭绝/极糟，非“崩溃” |
| Metaculus 社区 | 长期在个位数到 10% 区间（至 2100） | 众包预测 |
| Samotsvety | ~10% | 顶级 forecaster 团队 |
| Yudkowsky 等早期估计 | >50% | doomer 端 |

各家口径不同——灭绝、崩溃、“极其糟糕”不是同一个事件——数字只能粗比。Dario 的区间落在中位偏上，但不是离群值。真正的区别是他愿意公开说出来：其他 CEO 不说，不代表他们估计更低，只是不说。

### 为什么说出来

他的理由是，说出这个区间恰恰因为自己不是 doomer。doomer 的立场是“反正没救了”，而 10-25% 意味着 75-90% 的概率不走那条路。那条有希望的路在他 2024 年的长文《Machines of Loving Grace》里有完整描述：AI 把 50-100 年的生物医学进步压缩到 5-10 年，癌症、阿尔茨海默、传染病都可能被根本改变。乐观的 75-90% 和悲观的 10-25% 是同一个判断的两面。

对风险大小没有共识，就没法认真讨论怎么管理它——这是他把数字摆上桌面的原因。沉默不会让风险变小，只会把议题让给阴谋论和情绪化讨论。

### 哪条风险是瓶颈

Dario 没说哪条风险主导这个区间。综合他的其他文章和 Anthropic 的研究投入分布，可以推断优先级：

1. **生物武器易化**——RSP 里 ASL-3 的核心触发条件就是 CBRN 能力增强，生物风险在他的风险清单里权重最高
2. **网络杀伤链自主化**——Mythos 已经验证可行，有清晰的能力里程碑
3. **递归自我改进失控**——最严肃但最难量化
4. **政治极化与规模化监控**——长期慢性风险

前两条是当前的约束瓶颈，因为它们有可验证的里程碑（271 个 Firefox 零日漏洞就是 cyber 侧的里程碑），能写进部署门槛；后两条缺少“什么时候算发生”的判定标准。

## 收束：先算最坏情况的决策方式

Dario 在访谈里的立场可以概括成一句话：面对这项技术，既不轻视也不恐慌，做理性回应。他的“理性回应”不是在安全区和冒险区之间取中点，而是在每个决策里回答同一个问题——这件事做错了，最坏结果是什么？

离开 OpenAI，防的是信任破裂让长期安全研究做不下去；Mythos 锁定，防的是漏洞信息变成武器；红线不让，防的是模型被用于自主武器；概率说出口，防的是行业对风险大小失去共识、无从管理。八个取舍背后是同一个问法，答案也都落到了可执行的对象上：合同条款、披露窗口、评估标准、公开数字。

访谈末尾他说自己最喜欢的书是《Sapiens》。这件事不算闲聊——Anthropic 的价值立场偏向文明尺度：技术是回答“人类往哪去”的工具，不是问题本身。Dario 没有给 AGI 时间表，给的是一套文明尺度上的工程判断。

## 读者判断与本文边界

本文已经把八个取舍的判断、数据和推论铺开，多数读者读完即可，不必再花 70 分钟刷原片。三类人值得回看：想核对数字在原片里具体语境的，可以按数据校核表的时间戳索引；想听 Dario 语气和节奏的，重点看 48:18 的 Mythos 段和 01:05:49 的概率段；研究访谈方法本身的，可以注意 Emily Chang 的追问方式——追问里藏着这期节目的议程。

本文不覆盖：Mythos 的技术细节（访谈只给了几个数字，没有 technical paper，Model Spec 和 system card 未公开）；Anthropic 与 Google DeepMind 算力合作的合同细节；白宫访问的具体讨论内容（58:57 段提及但未展开）；RLHF、Constitutional AI、mechanistic interpretability 的方法细节；《Machines of Loving Grace》的全文解读（那是另一篇长文的量级）。

本文有意不假装中立。Dario 在访谈里不掩饰对 Anthropic 路线的支持，本文的整理也不掩饰这一点。数据校核表把可核查的部分单独列出，剩下的判断请读者自己称重。

## 延伸阅读

**原始访谈**

- [Bloomberg The Circuit — Inside the Mind of Anthropic CEO Dario Amodei](https://www.bloomberg.com/news/videos/2026-06-17/inside-the-mind-of-anthropic-ceo-dario-amodei-video) — 原始视频，70 分钟
- [YouTube（Bloomberg Originals 频道）](https://www.youtube.com/watch?v=x2VHFgyawPE)
- [B 站 BV1CMjq6nEu1 — UP「opus精译」中文翻译](https://www.bilibili.com/video/BV1CMjq6nEu1/)
- [Business Insider Africa 报道](https://africa.businessinsider.com/news/dario-amodei-on-why-he-left-sam-altman-and-openai-why-argue-with-someone-when-you/bg0bt03) — 离开 OpenAI 原话
- [Podwise 完整 transcript + mindmap](https://podwise.ai/episodes/8209097) — 全文需登录

**Anthropic 与 Dario 公开材料**

- [Series H 公告（2026-05-28）](https://www.anthropic.com/news/series-h) — $65B 融资、$965B 估值、年化营收 $47B
- [CNBC：Anthropic tops OpenAI as most valuable AI startup](https://www.cnbc.com/2026/05/28/anthropic-open-ai-startup-value.html)
- [Dario Amodei — Machines of Loving Grace](https://darioamodei.com/machines-of-loving-grace) — 压缩的 21 世纪
- [Dario Amodei — The Adolescence of Technology](https://darioamodei.com/essay/the-adolescence-of-technology) — 2026-01，风险应对与治理

涉及的关键人物：Dario Amodei（Anthropic CEO、联合创始人）、Daniela Amodei（Anthropic 联合创始人，Dario 妹妹）、Demis Hassabis（Google DeepMind CEO）、Emily Chang（Bloomberg《The Circuit》主持人）。

## 附录 A：术语表

| 全称 | 后续称谓 | 一句话定义 |
|---|---|---|
| Mythos | Mythos | Anthropic 当前最强模型，能自主走完网络杀伤链，经 Project Glasswing 向少量合作机构受限开放 |
| cyber kill chain | 网络杀伤链 | Lockheed Martin 定义的七阶段攻击链：侦察 → 武器化 → 投递 → 利用 → 安装 → 命令控制 → 达成目标 |
| CVD | 协调漏洞披露 | Coordinated Vulnerability Disclosure，给厂商打补丁的标准披露窗口实践，行业惯例 90 天 |
| model-level catastrophic risk | 模型级灾难风险 | 评估对象是模型自身能力，而非基于模型构建的应用 |
| ASL | AI 安全级别 | Anthropic Responsible Scaling Policy 里的能力阈值等级，升级触发递增的部署限制 |
| RSP | 负责任扩展政策 | Responsible Scaling Policy，把模型能力阈值写成可审计的部署触发规则 |
| subjective probability | 主观概率 | 信息不完整时由专家给出的概率区间估计 |
| compressed 21st century | 压缩的 21 世纪 | Dario 提出的概念：AI 把 50-100 年的进步（尤其是生物医学）压缩到 5-10 年 |
| RSI | 递归自我改进 | Recursive Self-Improvement，模型改进自身训练流程的正反馈风险 |
| doomer | 末日派 | 认为 AI 大概率导致文明崩溃、治理无从下手的一类立场 |

## 附录 B：视频时间戳对照

| 视频时间戳 | 主题 | 本文对应章节 |
|---|---|---|
| 00:00 | Inside Anthropic | 离开 OpenAI / 押注企业级 |
| 03:34 | Dario background | 离开 OpenAI |
| 05:51 | Leaving OpenAI | 离开 OpenAI |
| 07:42 | India AI summit | 国有化、中国与递归自我改进 |
| 10:45 | Enterprise bet | 押注企业级 |
| 19:29 | Compute crunch | 算力紧缺 |
| 21:15 | Surpassing OpenAI | 押注企业级 |
| 24:07 | Product velocity | 押注企业级 |
| 24:52 | AI discoveries | 算力紧缺 / 就业冲击 |
| 26:13 | Dario's writing style | 文明崩溃概率 |
| 28:10 | AI and the workforce | 入门白领岗位 |
| 36:41 | Pentagon standoff | 五角大楼对峙 |
| 43:29 | AI warfare | 五角大楼对峙 |
| 48:18 | Mythos | Mythos |
| 55:15 | Nationalizing AI | 国有化、中国与递归自我改进 |
| 58:57 | Visit to the White House | 国有化、中国与递归自我改进 |
| 59:47 | China | 国有化、中国与递归自我改进 |
| 01:03:24 | Recursive self-improvement | 国有化、中国与递归自我改进 |
| 01:05:07 | Dario's favorite book | 收束 |
| 01:05:49 | Civilization collapse | 文明崩溃概率 |
| 01:07:32 | Trust | 收束 |
