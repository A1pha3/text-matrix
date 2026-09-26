---
title: "FDE 浪潮：OpenAI 部署公司、PE 资本与 AI 落地的组织深处"
date: "2026-06-23T00:45:00+08:00"
lastmod: "2026-09-24T00:00:00+08:00"
slug: "openai-deployco-fde-palantir-2026"
source_key: "bv:BV1jxLd6oEGR"
description: "2026 年 5 月，三大 AI 巨头同步押注同一件事：把 AI 从 demo 推进企业组织深处。拆解 FDE（前线部署工程师）的 Palantir 军方渊源、四项工作方法、AI 原生组织的五层嵌入，以及为什么这次是模型公司+PE，不是模型公司+咨询。"

draft: false
categories: ["视频精读"]
tags: ["OpenAI", "Anthropic", "Palantir", "FDE", "硅谷101"]
hiddenFromHomePage: false
---

> **阅读目标**：一次看懂 2026 年 5 月三大 AI 巨头同步押注部署公司这件事——FDE 是什么、为什么起源于 Palantir 的军方项目、为什么这轮是「模型公司+PE」而非「+咨询」、AI 原生组织要嵌入哪 5 层，以及发布之后三个月牌桌怎么变大。各节标题即目录，可按需跳读。

## 这篇文章回答什么

- 为什么 OpenAI、Anthropic、谷歌云**同步**成立部署公司或组建 FDE 团队
- FDE 和传统软件工程师、外包实施、咨询顾问的关键区别在哪
- 从 Palantir 到 OpenAI/Anthropic，FDE 哪套工作方法没变过
- 为什么是「模型公司+PE」而不是「模型公司+咨询」
- AI 原生组织需要嵌入哪 5 层
- 为什么「内部 FDE」是 +AI 企业的新关键人才
- SaaS 的生存威胁与转型机会
- 5 月之后的三个新玩家：微软、亚马逊，和 Anthropic 那家叫 Ode 的合资公司

---

## 写在前面

2026 年 5 月 4 日，Anthropic 宣布与黑石集团（Blackstone）、Hellman & Friedman、高盛共同成立一家估值 15 亿美元（$1.5B）的 AI 原生企业服务公司。几个小时前，Bloomberg 刚曝光 OpenAI 的同类动作：一家内部代号 DeployCo 的部署公司（The Deployment Company），19 家机构合计注资超过 40 亿美元，投后估值 100 亿美元。一周后的 5 月 11 日，OpenAI 正式官宣 Deployment Company，同步宣布收购英国咨询公司 Tomoro；贝恩咨询（Bain & Company）同日宣布投资并与其合作。

把这条新闻和硅谷 101 播客《OpenAI 联手 PE 砸下 40 亿美元，聊聊硅谷最火新职位 FDE》（BV1jxLd6oEGR，51 分 30 秒）对照起来读，会发现 5 月初发生的事情不是几家 AI 公司不约而同做了相似的事，而是同一个判断被三家公司同时押注：AI 的下一战场正在从模型转向组织深处。负责把 AI 推进组织深处的人，就是硅谷 2026 年最炙手可热的工种——Forward Deployed Engineer（前线部署工程师，FDE）。

本文以这期播客为骨架，叠加 TechCrunch、CNBC、WSJ、Bloomberg、OpenAI 与 Anthropic 官方公告等 5 月报道，未尽研究 2026-05-18 长文《从 Palantir 到 FDE 热潮》，以及各家后续动态，把 FDE 浪潮从历史起源、组织方法、资金结构、真实战场四个角度串起来，并补记发布之后三个月的新进展。

B 站页面未提供可稳定引用的完整字幕，本文不逐句转录，而是把播客内容还原成文。所有时间、金额、公司名都来自公开报道，来源见文末；无来源的细节一律不写。

---

## 一、先看地图：FDE 不是「实施工程师」改名

要理解 FDE 为什么在 2026 年突然成为硅谷最热的新职位，先把它和几个看似相近的工种切分开。

**传统软件工程师**的目标是为许多客户开发一个能力：写通用库、通用平台、通用 API，希望一份代码服务尽可能多的客户。

**实施工程师/部署顾问**是传统 SaaS 公司的角色：按产品手册帮客户上线、配置权限、导入数据。产出是「客户能用了」。

**管理咨询顾问**（麦肯锡、BCG、贝恩）给客户提供分析和建议，不写代码也不部署系统，交付的是幻灯片和口头结论，客户自己决定怎么执行。

**FDE 是什么？** Palantir 给出的定义：为一个客户启用许多能力。FDE 直接嵌入客户现场，和客户的运营团队、工程师、数据团队坐在同一间办公室，用公司现有的平台、工具和模型，为客户特定场景构建定制化解决方案。

这种工作形态是 Palantir 在 2000 年代中期服务美国军方和情报部门时打磨出来的。那些客户的问题涉及最敏感的数据、最复杂的流程、最模糊的需求，FDE 团队要解决的正是「客户自己说不清楚自己要什么」。

FDE 的工作方法有 4 个核心：

1. **从具体决策出发，而不是从数据表出发**。Palantir 内部称之为 Ontology（本体）建模——它要回答的不是「有哪些数据」，而是「这个组织如何做决定，决策依赖哪些事实、规则和动作」。
2. **把组织建模为对象、关系和动作**。Ontology 把数据整合成对象和连接，让运营复杂性既能被人类理解，也能被 AI 理解。
3. **把 AI 接入业务闭环**。Palantir 的 AIP（AI Platform）把生成式 AI、运营数据、业务规则、权限、应用开发、安全治理放在同一平台。
4. **现场工程师嵌入客户现场**。FDE 不是远程支持，而是驻场——和客户团队一起吃饭、一起开会、一起写代码、一起加班。

一套 Ontology 建模示意：

```text
对象(Object):  订单 · 客户 · 库存 · 审批人
关系(Link):    订单 ──属于──▶ 客户 ；订单 ──扣减──▶ 库存
动作(Action):  批准订单 / 触发补货 / 冻结账户（每个动作带权限 + 业务规则）
决策闭环:      事实(运营数据) → 规则 → 动作 → 反馈；人和 AI 读同一套模型
```

四个角色放在一张表里，区别一目了然：

| 角色 | 目标 | 交付物 | 是否驻场 | 服务的客户 |
| --- | --- | --- | --- | --- |
| 传统软件工程师 | 为多个客户做一个能力 | 通用库 / 平台 / API | 否 | 许多 |
| 实施工程师 | 按产品手册让一个客户上线 | 配置完成的系统 | 否 | 一个 |
| 咨询顾问 | 给出分析和建议 | 幻灯片 / 口头结论 | 否 | 一个 |
| FDE | 为一个客户启用许多能力 | 现场构建的定制方案 | 是 | 一个 |

FDE 和「AI 工程师」「实施顾问」都不重叠：它把工程化交付能力直接搬进客户组织，是一支现场作战单位。

---

## 二、2026 年 5 月：三大 AI 巨头同步押注同一件事

把 5 月初三家公司各自的动作展开看，这不是单一事件，而是同一个判断的三种表达。

### OpenAI：The Deployment Company（DeployCo）

- **2026-05-04**：Bloomberg 报道 OpenAI 正在组建 The Deployment Company，19 家机构投资、投后估值 100 亿美元。TPG 领投，Advent、Bain Capital、Brookfield 联合领投；高盛、软银、华平（Warburg Pincus）、西班牙对外银行（BBVA）、贝恩咨询、凯捷（Capgemini）、麦肯锡等也在投资人名单里。OpenAI 对该公司控股。
- **2026-05-11**：OpenAI 官宣 Deployment Company，同步宣布收购爱丁堡 AI 咨询公司 Tomoro——客户包括 Tesco、维珍航空、Supercell，约 150 名 FDE 和部署专家随交易转入（交易尚待监管批准）。贝恩咨询同日宣布投资并合作，7 月又成为 OpenAI 精英合作伙伴。
- **业务目标**：在客户内部识别高价值 AI 场景，重构关键工作流，把 AI 嵌入客户组织深处。工程打法参考了 Palantir：先诊断，再挑几个高优先级工作流做深。
- **已有样板**：BBVA 作为创始合作伙伴，内部 rollout 覆盖 25 个国家的 12 万名员工。

### Anthropic：15 亿美元的 AI 原生企业服务 JV

- **2026-05-04**：Anthropic 与黑石、Hellman & Friedman、高盛联合成立合资公司，估值 15 亿美元；Anthropic、黑石、H&F 各承诺出资 3 亿美元，Apollo、General Atlantic、GIC、Leonard Green、红杉等参与。目标客群是各行各业的中型企业，把 Claude 推进其核心运营环节。
- **FDE 招聘**：Anthropic 公开招募 FDE、Applied AI 一类岗位，把 Claude 的能力交付进企业生产环境，并把现场沉淀的可重复部署模式回馈给产品和工程团队（The New Stack 2026-05-28 对两家 FDE 团队扩张有专题报道）。
- **关键信号**：这家 JV 的金融资本阵容（黑石、H&F、高盛）与 Anthropic 在金融行业的客户优势相匹配——Claude 在编程、推理、金融分析等场景的表现是其切入点。

### 谷歌云：招募数百名 FDE

- **2026-05-13**：多家媒体报道，谷歌云在 OpenAI 和 Anthropic 之后计划招募数百名 Forward Deployed Engineer，帮企业把 Gemini、Vertex AI、Agent Development Kit（ADK）等产品推进生产现场，弥合前沿模型与客户真实环境之间的差距——集成复杂性、数据就绪、状态管理都是日常。谷歌高管把 FDE 称为当下科技行业最抢手的工作。

### 为什么三巨头同时动手？

5 月初不是巧合。三家公司同时看到了同一件事：模型能力已经够强，但企业用不起来。

模型评测分数在涨，公开 benchmark 上的能力越来越强。但企业里的真实工作流——ERP、CRM、MES、交易系统、风控系统、工单系统、审批流程、权限体系、审计与合规——这些数据和流程 AI 还摸不到。要摸到，必须有人驻场。这就是 FDE 成为硅谷最热新职位的根本原因。

> 模型评测涨得再快，也到不了客户的风控系统里。这一段路，得靠驻场的人走完。

---

## 三、为什么是 PE，而不是传统咨询公司？

这是本期播客里对咨询行业冲击最大的一个问题，也最容易被一带而过。

Oliver 是这期播客的另一位嘉宾——Invisible Technologies 企业业务 VP、前麦肯锡咨询师。他从私募和咨询行业的视角拆解了模型公司为何绕开传统咨询、直接与 PE 合作。三个原因。

其一，PE 手里有现成的企业客户名单。黑石、H&F、高盛这类机构手里有几十到几百家被投企业，DeployCo 的 19 家投资机构的被投企业加总超过 2000 家——这些都是天然的 AI 落地客户。传统咨询公司也有客户名单，但项目制交付是「建议+PPT」，无法把工程团队长期驻进客户内部。

其二，PE 的核心利益是被投企业价值提升，与 FDE 长期驻场天然对齐。模型公司派 FDE 驻场 6-18 个月，帮被投企业把 AI 嵌进工作流，最终结果是企业效率提升、估值上涨——PE 拿到回报，模型公司拿到深度合作。咨询公司的项目制收费相反：从短期项目中收费，没有动力做长期驻场。

其三，PE 有资本和风险共担的能力。Anthropic 的 15 亿美元 JV 由黑石、H&F、高盛共同出资共担风险，DeployCo 则由 19 家机构出了 40 多亿美元。这种资本结构让 FDE 团队不必背短期 ROI 指标，可以专注做长周期的嵌入工作。

对传统咨询公司来说，这轮浪潮是结构性威胁：麦肯锡、BCG 这类「卖建议」的公司，正面对「卖驻场工程师」的新模式。不过故事还有另一面——麦肯锡、贝恩咨询、凯捷都出现在 DeployCo 的投资人名单里，贝恩咨询还与 DeployCo 达成正式合作。传统咨询不是被排除在牌局外，而是被迫换一种方式入局：从卖项目，变成当股东。贝恩咨询主动押注 PE 行业、与 OpenAI DeployCo 绑定，可能是咨询行业里最清醒的一次转身。

---

## 四、Palantir 的方法论：三件事不会变

Palantir 二十年 FDE 经验，可以浓缩成一句话：FDE 卖的不是「服务」，是一支能驻场、能解决具体问题的工程力量。这件事在 AI 时代不会变，在 Palantir 之前的咨询时代也不会变。留下来的方法论有三条。

### 1. 现场工程是核心商业模式

过去 20 年的企业软件史是「标准化产品+远程销售」的历史。SaaS 公司的目标是做出一款好用、易扩展、可远程配置的产品，最大限度减少人工服务。

Palantir 走的是反方向：复杂组织的客户，必须有工程师驻场才能交付。客户买的不是一套软件，而是一支能解决自己具体问题的工程队伍。

AI 时代这件事变得更突出——模型再强，也需要驻场工程师帮客户把模型嵌进 ERP、CRM、MES、风控、权限、合规系统。OpenAI、Anthropic、谷歌云成立部署公司或组建 FDE 团队，本质上是把 Palantir 这个 20 年前的判断重做一遍。

### 2. 客户现场反哺产品研发

Palantir 的 FDE 不只交付项目，还把现场形成的解决方案沉淀回平台：在某客户现场发现新问题，解决之后写进 Foundry，下一个客户直接复用。

从 Palantir 到新一代 AI 公司，FDE 岗位的公开描述里都能看到同一类职责：在现场识别可重复的部署模式，把经验回馈给产品和工程团队。这句话的实质，是让现场工程成为产品研发的延伸——既不是「销售反馈」，也不是「客户成功」，而是把一部分产品开发权放到客户现场。

### 3. 重塑 AI 公司的组织边界

OpenAI 原本更像模型公司，现在多了「模型公司+部署公司」两重身份。Anthropic 原本是模型 API 提供方，现在往「模型+MCP+子智能体+技能+部署伙伴」扩展。谷歌云原本是云服务公司，现在把 Gemini、Vertex AI、ADK 通过 FDE 推进客户现场。

三家公司的组织边界都在扩张——模型公司正在变成带部署能力的组织工程公司。

这与传统软件公司的边界扩张方向相反。Salesforce 是先做出 SaaS 产品，再通过 AppExchange 扩展到更多应用场景；今天的 AI 公司则是通过派驻工程师来扩展边界。

---

## 五、AI 原生组织的 5 层嵌入

如果「AI 落地的真正战场是组织深处」是结论，那「组织深处」具体指什么？

未尽研究 2026-05-18 的长文给出了一个清晰的分层——AI 原生组织需要至少嵌入 5 层：

| 层 | 内容 | 解决的问题 |
| --- | --- | --- |
| 1. **数据层** | AI 能访问企业内部可信数据 | 不仅是公开互联网知识 |
| 2. **语义层** | AI 知道什么是订单、客户、设备、合同、头寸、敞口、供应商、任务、风险 | 业务对象的精确定义 |
| 3. **流程层** | AI 知道一个任务从发起到审批、执行、复核、留痕的完整流程 | 任务的全生命周期 |
| 4. **动作层** | AI 不能只建议，还要能在权限允许下创建工单、修改记录、提交申请、触发流程 | AI 的动手能力 |
| 5. **治理层** | AI 的每一次读取、判断、建议和动作都要有权限、审计、回滚、人工接管和责任边界 | AI 的可审计性 |

5 层中最难的是**语义层**和**动作层**。

语义层的难点在于：行业知识是软件公司的护城河。金融软件公司知道什么是「头寸」「保证金」「异常交易」「反洗钱」，医疗软件公司知道什么是「诊断组」「病历」「处方」「医保编码」。通用 AI 模型不知道这些，必须有人把行业知识编码给 AI。

动作层的难点在权限治理。AI 不能随意创建工单或修改记录，必须有严格的权限——什么用户或智能体在什么条件下可以执行什么动作。Palantir 的 Ontology 在设计之初就把「行动」作为一等公民，把权限作为控制平面的一部分。

这 5 层不是技术问题，而是组织工程问题——通常要 FDE 团队驻场 6-18 个月才能完成。

### 一次采购审批怎样穿过 5 层

把分层落到一件具体的事上，选采购审批——企业里最常见、也最容易被 AI 改造的流程。

- **数据层**：AI 要读到采购单、预算、供应商、历史成交价，这些散在 ERP 和财务系统里，驻场团队先把它们接成 AI 可访问的数据源。
- **语义层**：模型要认得「采购单」不是一段文字，而是绑着预算科目、供应商和审批人的对象；还得知道「预算科目」和「部门」不是一回事。
- **流程层**：一笔单子从发起 → 部门审批 → 财务复核 → 留痕归档，每一步的触发条件和负责人，AI 都要能复述。
- **动作层**：流程层跑通后，AI 才有资格在权限内代填表单、发起审批、比对价格，而不是只吐出一段建议。
- **治理层**：每个动作都带权限、审计日志和回滚点，审批人随时能接管，出问题能定位到具体是哪一次调用。

前两层是「看懂数据」，中间两层是「跑通流程」，最后一层是「保证可追责」。缺了动作层，AI 只是高级搜索；缺了治理层，AI 不敢真正动手。

---

## 六、Anthropic 内部的 5 类组织变化

Anthropic 把自己的 FDE 实践写进了招聘描述，内部组织变化也能从这些公开材料里反推出来。五条变化，指向 AI 公司的未来形态。

**研究-产品距离缩短。** 模型能力要快速转化为 Claude Code、Claude for Work、Skills、MCP 这样的产品工具链。研究员的产出不再只是论文和模型权重，而是直接成为产品功能。

**产品-客户现场距离缩短。** FDE 进驻客户现场后，客户的真实问题会反向定义产品路线：哪些 MCP 服务器最常用？哪些子智能体最稳定？哪些技能最容易复用？答案都在现场。

**工程师工作方式智能体化。** 如果 Anthropic 内部广泛使用 Claude Code 和智能体工作流，组织会从「人写代码」转向「人设计目标、规范、评估、审查、合并结果」。更多人做架构、任务拆解、评估、代码审查、产品判断；更少人做重复性实现。

**安全-产品深度耦合。** 智能体一旦进入客户生产系统，就涉及工具调用、权限、数据访问和动作执行。安全必须从「原则」变成「产品机制」——权限边界、可解释日志、评测、沙箱、人在环中。

**企业销售从卖席位转向卖工作流转型。** 客户买的不只是 Claude 的访问权，而是希望 Claude 改造客服、研发、法务、金融分析、运营等流程。这是从 SaaS 席位订阅向流程转型服务的迁移。

这五条放在一起，指向同一件事：AI 公司不再只做模型，而是帮客户把模型变成组织能力。

---

## 七、对 +AI 企业的启示：内部 FDE 是新关键人才

FDE 浪潮对模型公司的影响是清晰的——组建或收购 FDE 团队。但它对采纳 AI 的企业影响同样深远。

传统企业的 AI 转化过程通常是：IT 部门评估工具 → 采购 → 培训员工使用 → 期望看到效率提升。这个流程有个根本问题：员工用上了 AI 工具，但组织的流程、权限、数据结构没变。结果是 AI 被用成高级版搜索引擎，组织的实际工作流纹丝不动。

真正的 AI 转型需要内部出现一批「内部 FDE」——既懂业务流程，又懂数据和 AI，能把模型能力持续装进组织工作流。这种角色和传统企业的数据科学家、AI 工程师、数字化转型经理都不一样：

- 数据科学家专注模型和算法，不懂业务流程
- AI 工程师专注工具和框架，不懂业务语义
- 数字化转型经理专注流程和变革管理，不懂工程实现
- **内部 FDE 需要同时懂三件事**：业务流程 + 数据/AI 工程 + 变革管理

这个角色的人才市场几乎不存在——要么企业内部花 2-3 年培养，要么从外部 FDE 团队招聘。未来 +AI 企业的竞争力之一，不在于用了哪个模型，而在于组织吸收 AI 的速度和深度。

---

## 八、SaaS 的生存威胁与转型机会

大量 SaaS 和垂直软件公司正处在 AI+ 与 +AI 之间：既不是底层模型公司，也不是最终行业客户，而是行业流程和软件入口的拥有者。

智能体带来的生存威胁有三类。一是**界面被 AI 绕过**——如果用户未来通过 ChatGPT、Claude、Gemini 直接发出自然语言命令，传统软件的 UI 价值会下降，很多只有表单、菜单和报表的 SaaS 可能被通用智能体压成后台工具。二是**工作流被平台吸收**——OpenAI、Anthropic、Google、Microsoft 一旦掌握企业智能体入口，许多轻量 SaaS 功能可能变成模型或平台的内置能力。三是**差异化消失**——只给旧产品加一个聊天框，很容易被更强的模型、更便宜的 API、更深的平台集成取代。

但它们也有三样固有优势。**行业语义**：金融软件公司知道什么是交易、头寸、保证金、敞口、异常交易、反洗钱，医疗、制造、能源、法律软件公司也各自掌握行业对象和流程——这些是通用模型没有的，但可以被 FDE 编码进 Ontology。**客户系统入口**：很多行业软件已经部署在客户核心业务系统里，比通用 AI 公司更接近真实工作流。**信任和合规经验**：金融、医疗、能源、政务行业不会轻易让通用 AI 智能体进入核心系统，垂直软件公司若能把 AI 安全地嵌进已有系统，优势明显。

所以它们的机会，是从软件供应商升级为行业 AI 操作系统。

成功样本里，**Salesforce 是最典型的 SaaS 转型案例**。2025 年 12 月 3 日的 FY2026 三季报显示：

- Agentforce 与 Data 360 的年化经常性收入（ARR）接近 14 亿美元，同比增长 114%
- Agentforce 单品 ARR 突破 5 亿美元，同比增长 330%
- 累计签下超过 18,500 笔 Agentforce 交易，其中付费交易超过 9,500 笔，付费交易环比增长 50%

它的逻辑不是给 CRM 加个聊天框，而是把客户数据、销售、客服、营销和工作流整体重构为 Agentic Enterprise。

**ServiceNow 是另一个样本**。它本来就是企业工作流平台，现在把 AI 智能体嵌进 IT、HR、客服、财务、供应链等流程，2026 年 5 月又发布了面向全企业的「AI 员工」（AI workforce）产品概念。平台型 SaaS 的转身路径是：自己先变成 AI 智能体的运行环境。

两个案例的共同点：成功的软件公司不是被 AI 替代，而是把自己变成 AI 智能体的运行环境。FDE 浪潮对 SaaS 行业的真正含义也在这里——能承接 AI 智能体的 SaaS，会取代不能承接的 SaaS。

---

## 九、发布之后：牌桌迅速变大

本文发布（2026 年 6 月下旬）后的三个月，格局演化的速度超过了播客里的判断。几件值得补记的事，全部有公开报道可查：

- **Anthropic 的 JV 有了名字和第一笔收购。** 5 月 21 日，这家合资公司宣布收购 AI 公司 Fractional AI；7 月 15 日，公司以 **Ode** 之名正式亮相。
- **微软亲自下场。** 7 月 2 日，TechCrunch 报道微软成立自己的 AI 部署公司，承诺投入 25 亿美元。
- **亚马逊跟进。** 6 月 30 日，TechCrunch 报道亚马逊组建预算 10 亿美元的 FDE 组织，跟随 OpenAI 和 Anthropic 的打法。
- **DeployCo 继续扩张。** 7 月 8 日，Axios 独家报道 DeployCo 拟收购 Northslope；8 月 25 日，市场研究集团 NIQ 宣布与 DeployCo 合作。
- **FDE 成为人才军备竞赛。** Forbes 5 月底称这是「企业级最昂贵岗位」的豪赌；TechCrunch 7 月底的报道直接把 FDE 称作「AI 行业最新的人才执念」。

三家公司变成六家以上，FDE 从一个职位变成一场军备竞赛。播客里那句「AI 的下一战场在组织深处」，三个月后已经是所有巨头的共识。

---

## 十、结语

把 2026 年 5 月初 OpenAI Deployment Company、Anthropic JV、谷歌云 FDE 招聘的同步动作，Palantir 二十年的 FDE 经验，和之后三个月的新进展放在一起，三个结论可以同时成立。

**FDE 不是新职位。** Palantir 在 2000 年代中期就把它打磨成型，核心是「为一个客户启用许多能力的现场工程师」。今天的大动作，本质上是把 FDE 模式从服务军方/情报部门复制到服务企业 AI 落地，并且第一次配上了大额资本。

**FDE 变成硅谷最热职位，是因为 AI 的下一公里不在模型，而在组织深处。** 模型能力已经够强，但企业用不起来——必须有人驻场，把 AI 嵌进 ERP、CRM、MES、风控、权限、合规系统。

**这轮的资金搭档是 PE，不是咨询公司。** 黑石、H&F、高盛、TPG、Brookfield 这类机构手里有真实的被投企业名单，资本和风险共担能力强，与 FDE 长期驻场的目标天然对齐。传统咨询公司面临结构性威胁，但麦肯锡、贝恩、凯捷用入股的方式留在了牌桌上——交付形态的竞争才刚刚开始。

最后一句话：模型决定 AI 能走多远，组织决定 AI 能走多深，FDE 就是让 AI 走深的那批人。

---

## 读者判断：谁该听原播客

**读本文就够的**：

- 想搞清 FDE 是什么、和「实施工程师 / 咨询顾问 / 传统软件工程师」差在哪，以及 2026 年 5 月三巨头为什么同步押注部署公司。播客里的定义、方法、资金结构和案例，本文都已展开。
- 没时间听 51 分 30 秒，只要结论、可引用的数字和出处。

**建议听原播客的**：

- 想听两位嘉宾（Jove、Oliver）的现场语气和临场举例。本文还原的是观点和结构，口语里的即兴细节、问答来回是文字替代不了的。
- 想核对某句话的原始表述。B 站页面未提供可稳定引用的完整字幕，本文不逐句转写、未标注时间戳；要精确定位某段，可凭 51 分 30 秒的总时长和各节内容顺序大致回看。

**视频信息**：硅谷 101《OpenAI 联手 PE 砸下 40 亿美元，聊聊硅谷最火新职位 FDE》，BV1jxLd6oEGR，51 分 30 秒，2026 年 6 月 18 日发布。

---

## 常见误读

下面几条最容易搞错：

- **「FDE 就是实施工程师改了个名」**——不对。实施工程师是「为一个客户按手册上线一个产品」，FDE 是「为一个客户启用许多能力」，用平台+模型现场构建定制方案；本质区别是通用产品交付 vs 现场能力构建。
- **「这轮找 PE 是因为缺钱」**——不对。找 PE 而不是咨询公司，核心是 PE 手里有现成的被投企业客户名单，利益与长期驻场提升企业价值天然对齐，还能风险共担。钱只是其一。
- **「模型够强了，FDE 是过渡角色」**——恰恰相反。模型越强，越暴露出企业数据和流程 AI 摸不到这个瓶颈。把 AI 嵌进 5 层组织的活，短期内只有驻场的人能干。
- **「咨询公司要被消灭了」**——目前看到的不是消灭，是收编：麦肯锡、贝恩咨询、凯捷都是 DeployCo 的投资人，贝恩咨询还成了 OpenAI 精英合作伙伴。被重写的是交付形态，不是这些公司本身。

## 自测清单

- [ ] 说得清 FDE 和「实施工程师 / 咨询顾问 / 传统软件工程师」四者的关键区别吗？
- [ ] 讲得出为什么这轮是「模型公司 + PE」而不是「模型公司 + 咨询公司」的三个原因？
- [ ] 列得出 AI 原生组织要嵌入的 5 层，以及为什么语义层和动作层最难？
- [ ] 说得出 Palantir 的 Ontology 为什么把「动作」和「权限」当一等公民？

## 下一步

想把这套框架用起来，可以对照 Palantir 的 Ontology / AIP 公开文档，把自己业务里的「对象—关系—动作」画出来；再对照文末 Anthropic、谷歌云的 FDE 招聘报道，看真实岗位到底要什么能力。

---

## 引用与参考资料

**核心视频源**：

- 硅谷 101《OpenAI 联手 PE 砸下 40 亿美元，聊聊硅谷最火新职位 FDE》BV1jxLd6oEGR，2026-06-18 发布，时长 51 分 30 秒
- 主持：Yiwen（硅谷 101 特约研究员）；嘉宾：Jove（Cresta FDE 团队负责人）、Oliver（Invisible Technologies 企业业务 VP、前麦肯锡咨询师）
- 视频原址：<https://www.bilibili.com/video/BV1jxLd6oEGR>

**5 月初三大事件**：

- Anthropic 官方 2026-05-04《Building a new enterprise AI services company with Blackstone, H&F, and Goldman Sachs》
- OpenAI 官方 2026-05-11《OpenAI launches the OpenAI Deployment Company to help businesses build around intelligence》
- TechCrunch 2026-05-04《Anthropic and OpenAI are both launching joint ventures for enterprise AI services》：<https://techcrunch.com/2026/05/04/anthropic-and-openai-are-both-launching-joint-ventures-for-enterprise-ai-services/>
- CNBC 2026-05-04《Anthropic teams with Goldman, Blackstone and others on $1.5 billion AI venture targeting PE-owned firms》
- Forbes 2026-03-12《Anthropic In Talks With Blackstone And Hellman & Friedman To Launch AI Joint Venture》
- WSJ 2026-05-04《Anthropic Unveils $1.5 Billion Joint Venture With Wall Street Firms》
- The Next Web 2026-05-04《OpenAI closes The Deployment Company, a $10bn enterprise AI bet on private equity》
- Reuters 2026-05-11《OpenAI creates new unit with $4 billion investment to aid corporate AI push》
- Bloomberg 2026-05-11《OpenAI to Buy Consulting Firm for JV With Private Equity》
- The Information 2026-05-11《OpenAI Launches $10 Billion Private-Equity Joint Venture, Acquires Consultancy》
- Business Insider 2026-05-11《What smart people are saying about OpenAI's new $10 billion company to help businesses deploy AI》
- Bain & Company（PRNewswire）2026-05-11《Bain & Company invests in the OpenAI Deployment Company, a new venture to deploy AI at enterprise scale》
- The Decoder 2026-05-11《OpenAI's DeployCo subsidiary adopts Palantir's playbook, building a moat from workflows no lab can simulate》（19 家投资人名单、Tomoro 客户与 150 人规模、BBVA 部署数据、FDE 源起 Palantir 2000 年代中期）

**谷歌云 FDE**：

- India Today 2026-05-13《After OpenAI and Anthropic, Google plans to hire hundreds of Forward Deployed Engineers for AI》
- Fast Company 2026-05-13《Google, Box CEOs call this the "most in-demand" job in tech》

**国内综合报道**：

- 未尽研究 2026-05-18《从 Palantir 到 FDE 热潮，AI 如何真正进入企业组织》：<https://new.qq.com/rain/a/20260518A0004300>（AI 原生组织五层嵌入框架出处）

**SaaS 转型案例**：

- Salesforce 新闻稿 2025-12-03《Salesforce Delivers Record Third Quarter Fiscal 2026 Results Driven by Agentforce & Data 360》（Agentforce 与 Data 360 ARR 接近 14 亿美元、+114%；Agentforce ARR 破 5 亿美元、+330%；18,500 笔交易、9,500+ 付费）
- Fortune 2026-05-05《ServiceNow just unveiled an AI workforce that can run your entire company》

**发布后进展（2026-06 至 2026-09）**：

- Business Wire 2026-05-21《AI-Native Firm Backed by Anthropic, Blackstone, H&F Acquires Fractional AI》
- TechCrunch 2026-06-30《Amazon launches new $1 billion FDE org, following OpenAI and Anthropic》
- TechCrunch 2026-07-02《Microsoft launches its own AI deployment company with $2.5 billion commitment》：<https://techcrunch.com/2026/07/02/microsoft-launches-its-own-ai-deployment-company-with-2-5-billion-commitment/>
- Axios 2026-07-08《Exclusive: OpenAI deployment arm to acquire Northslope》
- PE Hub 2026-07-15《Ode with Anthropic launches as PE firms team up with AI specialists》
- PRNewswire 2026-07-20《Bain & Company named an OpenAI Elite Partner》
- NIQ 2026-08-25《NIQ and The OpenAI Deployment Company Collaborate to Bring Consumer Intelligence into Enterprise Workflows》
- Forbes 2026-05-28《AI Giants Bet Billions On The Most Expensive Job In Enterprise》；TechCrunch 2026-07-30《Forward-deployed engineers are the AI industry's latest talent obsession》

**说明**：本文不外推任何未公开数据。所有时间、金额、公司名、人事变动均来自上述公开报道；未标注链接的条目可按「媒体名 + 日期 + 标题」检索原文。OpenAI 出资额与注册地等未见权威报道的细节，本文不作陈述。
