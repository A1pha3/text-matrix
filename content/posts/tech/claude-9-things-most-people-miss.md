---
date: '2026-09-12T21:32:00+08:00'
draft: false
title: "Claude 的 9 件事：大多数人浪费的，是把 AI 助手当成了 AI 角色"
slug: "claude-9-things-most-people-miss"
description: "翻译反写 @anatolikopadze 推文长 thread《9 things most people don't use Claude for》——把 9 条建议还原为一个底层问题：大多数用户把 Claude 锁死在「AI 助手模式」里，没切换到「AI 角色模式」，也没把 Claude 的 4 个能力扩展用到尽头"
categories: ["技术笔记"]
tags: ["Claude", "AI", "翻译反写", "提示工程", "LLM"]
---

# Claude 的 9 件事：大多数人浪费的，是把 AI 助手当成了 AI 角色

> 本文是第 15 篇「x.com KOL 推文翻译反写」系列。原文是 [@anatolikopadze](https://x.com/anatolikopadze) 的长 thread《9 things most people don't use Claude for》。原推的聪明之处不在技巧清单本身，而在于把 9 件事绑回同一个底层问题。

## 一、为什么这条推值得翻译反写

原 thread 的结构很工整：1 张大图、9 个编号、每个 3-5 句话的硬建议。这是 KOL 推文最常见的格式——注意力经济下的最优信息组织方式：编号让人有「我能在 5 分钟内看完」的安全感，每条短小独立便于截图转发。

但如果你按这个格式读过去，你会得到 9 个独立的 tip，每个都「听起来很有道理」。你会收藏起来，3 天后忘记，3 周后偶尔想起一个来试一下。**问题不在于你不努力，而在于这 9 件事是同一件事的 9 个面**——把它们当 9 件事用，永远用不到位。

原推没有说出来的那件事是：**大多数人把 Claude 锁死在「AI 助手模式」里——一个被动响应、给建议、避免冲突的对话伙伴**。9 个技巧里，4 个是「Claude 本来就有，但你没让它做」（能力扩展），5 个是「给 Claude 一个角色，它会完全切换身份」（角色扮演）。两组都要求你**主动打破默认模式**。

我会在本文做两件事：保留原推 9 条的原始表述和金句（翻译到中文语境），然后把它们重组成「2 组 + 1 个底层逻辑」。文末给你三句话的操作顺序——读完就能用上 1 个能力扩展 + 1 个角色扮演。

## 二、第一性原理：AI 助手模式 vs AI 角色模式

先讲清楚一个区分——这是原推 9 个技巧的真正轴。

**AI 助手模式**（assistant mode）是大多数人对 LLM（大语言模型）的默认心智模型：你问，我答；你说需求，我给方案。Claude 在这种模式下是一个「最懂礼貌的实习生」——听话、给建议、避免冲突、给五点 bullet point 安慰你。这种模式对付明确任务、提效、查资料是有效的，但它有一个**结构性的盲点**：当问题本身是模糊的、矛盾的、需要外部视角的，助手模式只会让 Claude 顺着你说。

**AI 角色模式**（role mode）是把 Claude 放进一个具体的专业身份里：你不是在和一个 AI 聊天，而是在和一个**有专业立场的人**对话。`CBT` 治疗师、压力测试官、私教、谈判对手、唱反调的——这些角色都有自己的「拒绝清单」和「追问纪律」，不会顺着你说，也不会给出泛泛的「建议」。

两者最大的差异是**反作用力**。助手模式几乎没有反作用力——你说啥它都同意；角色模式自带反作用力——它会问到你难受、反驳到你沉默、把你的假设拆到你说不出话来。

**大多数用户浪费的不是 Claude 的 token，是 90% 的杠杆**。原推 9 件事里，A 组（4 个能力扩展）解决「我连 Claude 有什么都不知道」的问题，B 组（5 个角色扮演）解决「我让 Claude 做了什么」的问题。前者是技术杠杆，后者是认知杠杆。两者叠加，才是把 Claude 从「聊天玩具」推到「思考伙伴」的临界点。

## 三、A 组：4 个能力扩展（Claude 本来能做，大多数人没让它做）

这一组的特点是：Claude 默认就能做这些事，但 80% 的用户根本没意识到它的存在，或者用过一两次就再没打开。

### 1. Long-form writing：长写、短写、专业、随意、文档、邮件，全都行

> 原文：「Most people treat Claude like a chatbot. They ask a question, get an answer, copy-paste it somewhere. They never explore the writing side.」

大多数用户把 Claude 当成一个搜索框：问问题，拿答案，复制走人。**他们没把 Claude 当成写作工具用**。这可能是因为早期 LLM 的写作确实弱——但 Claude 3.5/4 这一代已经可以模仿任何风格、长度、格式。

原推给了一个非常具体的最小可执行实验：找一份你最近写的文档，让 Claude 用三种不同风格重写，对比原稿。**这个实验的价值不在于得到一个「更好」的重写，而在于让你意识到：你以为自己的写作风格是单一的，其实你只会一种风格——而「风格」本身是一个可以多维度调用的工具。**

写作这件事的杠杆点不在于 Claude 写得「更好」，而在于它能写「你平时不写的那一种」。比如你平时写邮件都很简略、对方经常误解你的意思——那就让 Claude 写一封更正式但保留你核心论点的版本给你参考。比如你写技术文档太学究气——就让 Claude 写一版「外行能看懂」的你。这不是替代你的写作，是**让你看见自己写作的形状**。

### 2. Artifacts：聊天窗口里能跑的应用

> 原文：「Many people think Claude can only produce text. It can't build anything real. That's wrong. Artifacts are when Claude builds something that actually works inside the chat.」

这是 Claude 在 2024 年最被低估的功能之一。Artifacts（工件/制品）允许 Claude 在聊天侧栏里直接生成可交互的产品：计算器、习惯追踪器、图表仪表盘、SVG 图形、Mermaid 流程图，**不是要你复制代码出去运行，而是直接打开就用**——原推的金句是「Without leaving the conversation」（不用离开对话窗口）。免费计划就可以用。

**这个能力改变了 Claude 的工作流分类**。从「生成文本」变成「生成可验证的制品」。这意味着 Claude 不再是「问—答」这种线性流，而是可以做出让你**点击、滑动、输入数据看结果**的东西。

原推举的例子值得复刻：calculator、habit tracker、game、dashboard with charts。每一个都是「本来需要打开 Excel / Figma / 某个网页工具做 30 分钟的事，现在在聊天里 30 秒搞定」。**当你意识到「可点可滑」这件事的存在，Claude 突然从一个写邮件的助手变成一个能交原型的人**。

我自己的用法是：用 Artifacts 写「可视化决策辅助工具」——比如做一个「这次架构方案换 vs 不换的 ROI 模拟器」，数据是我口述的，交互是 Claude 生成的。30 秒出来一个能拖动的图，比写三段文字论述说服力强 10 倍。

### 3. Adaptive Thinking（Extended Thinking）：看见 Claude 思考的全过程

> 原文：「Most Claude users have never turned this on. Extended Thinking is a mode where Claude reasons through a problem step by step before giving you an answer - and you can watch the entire process.」

Extended Thinking（扩展思考）是 Claude 的「显示中间过程」开关。打开后，Claude 在给最终答案之前会先把推理过程摊开给你看——不是最终答案的「解释」，是真正从问题分析到方案推演的**完整思考链**。

大多数用户根本没开过这个开关。它的场景边界很清晰：

- 简单事实查询、闲聊、改写邮件——**不需要**。开了只会拖慢。
- 复杂决策、战略分析、多步推理、需要 Claude 真的「想」而不是「猜下一个 token」——**必须开**。

**原推的核心洞见是：你以为 Claude 给你的「答案」就是思考的结果，其实它只是思考的最后一个字**。当你打开 Extended Thinking，你会看到 Claude 在得出结论之前走了哪些弯路、考虑过哪些备选、最后为什么放弃某条路径——**这些过程信息比最终答案更值钱**，因为它让你能判断「这个结论的证据链是什么」「我能反驳哪一步」。

实际使用中我建议这样：遇到重要决策时，同时跑两遍——一遍普通模式拿「直觉答案」，一遍 Extended Thinking 拿「推理过程」。两份输出对照读，你会发现 Claude 自己在「最后定型答案」时砍掉了多少**不确定性**。这些被砍掉的不确定性，往往是你做决策时最该知道的事。

### 4. Memory：让 Claude 跨会话记得你

> 原文：「With Memory on, Claude builds a profile of you over time. Your job, your projects, how you like to communicate, what you're currently working on. Start a completely new chat and it already knows the context.」

Memory 是 Claude 的「用户档案」开关。打开后，Claude 会在每次对话中持续学习你是谁、做什么、怎么交流、在忙什么。下次新开一个聊天窗口，**Claude 已经知道上下文**，你不用再自我介绍。

这个功能默认是关闭的。大多数用户根本不知道它存在——或者知道，但「觉得有点怕」（让 AI 记住自己多了一点 surveillance 感）。原推的判断是：关着它，等于你**主动放弃了 Claude 最有杠杆的能力之一**。

打开 Memory 之后会立刻发生三件事：

- 你新开一个窗口问「上次那个项目怎么做的」，Claude 知道你在说哪个。
- 你换了一种语言或口吻，Claude 会跟着调（因为它记得你之前偏好哪种）。
- 你换设备、换平台，只要登录同一个账号，Memory 是跟随账号的。

**这个能力的天花板取决于你告诉 Claude 多少**。Memory 不是被动记录的日志，是主动维护的档案——你可以在任意对话里说「记住：我接下来三个月在做 X 项目的 Y 部分，沟通风格偏好 Z」，Claude 会把这条写进 Memory。Memory + Artifacts + Extended Thinking 三个同时打开，Claude 实际上变成了一个**认识你、记得你、能跑东西给你看、还会思考过程**的协作伙伴。

## 四、B 组：5 个角色扮演（给 Claude 一个 role prompt，它会完全切换身份）

A 组解决「Claude 有什么能力」的认知问题，B 组解决「Claude 在扮演什么角色」的身份问题。**后者是杠杆更大的那一组**——因为 A 组只是让 Claude 做它本来就能做的事，B 组是让 Claude 用**你不熟悉的视角**看你的问题。

原推的潜台词：**给 Claude 一个 role prompt，它会完全切换身份**——它会改变「它怎么问你、它会反驳什么、它会拒绝什么」的默认行为。复制下面任意一段到新聊天窗口的开头，效果立竿见影。

### 5. Personal psychologist：把它变成一个问你问题的治疗师

> 原文：「Most people use Claude as a validation machine. They describe a problem. Claude says that sounds hard and offers five bullet points of advice. That's not how good therapy works.」

**助手模式的最大失败模式就是「验证机器」**。你描述一个问题，Claude 说「那听起来很难」，给五点建议，你感觉被听见了，但问题还在原地。

原推给的 prompt 把 Claude 切到 **CBT（认知行为疗法）治疗师** 模式：它不再给建议，**它问你问题**——你焦虑什么、你担心的是什么最坏的结果、你的证据是什么、你的反例是什么。这种模式对**反复纠结的决定、说不清的焦虑、需要外部视角**的场景极其有效。

**为什么 CBT 模式有效**？因为 CBT 的核心不是「给你答案」，是「教你检查自己的思考过程」——你把一个模模糊糊的困扰说出来，治疗师会一直问「具体是什么」「什么时候开始的」「你说的是事实还是解读」「你怎么知道这是真的」，几次下来你自己就看清了。Claude 切到 CBT 角色后能复现这个过程，**因为角色身份会改变它的提问纪律**——它会克制住「给建议」的冲动。

实用操作：原推给了 prompt 文本（具体内容在原推文中），复制到新窗口开头，**接下来你只负责回答问题，不负责给方案**。10-15 个问答之后，你会拿到一个你自己想清楚的方案——而不是 Claude 帮你想清楚的方案。两者的稳定性完全不一样。

### 6. The hard mentor：把它变成一个拒绝你舒服的导师

> 原文：「By default Claude agrees with you. It adds to your ideas, supports your reasoning, finds the positives. This is almost always the wrong thing.」

这是 9 条里**最被低估的一条**。Claude 默认的「同意 + 找亮点 + 加补充」行为模式是 RLHF（人类反馈强化学习）训练出来的——它被训练成「最有帮助」的样子，但「最有帮助」≠「对你最好」。

原推的金句要原样保留：**「It's uncomfortable. That's why it works.」**（这让你不舒服。所以它才有用。）

把 Claude 切到「压力测试官」模式后，它会做三件事：找你的弱假设（哪些前提你没说但隐含假设了）、找你漏掉的视角、找你的方案在什么位置会崩——**具体到什么位置**，不是泛泛的「可能有问题」。

**这种模式对所有「我已经在内部做完了决定、想找人确认」的场景是救命的**。你以为你在「确认」，其实你是在找同意；hard mentor 不给你同意，它给你的是「你做这个决定前应该看的三件事」。

原推的 prompt 文本我建议读完原推后**复制粘贴**——它把 Claude 的「agree with user」默认行为直接关掉，换上「stress-test user plan」的行为。这不是 prompt engineering 的修辞，是**行为身份的切换**——prompt 一改，Claude 问问题的方式、它拒绝什么、它绝不让你滑过什么，全都跟着改。

### 7. Personal trainer：把你的真实数据交给它

> 原文：「Generic fitness advice is everywhere. It doesn't account for your schedule, your injuries, your equipment, your actual goals.」

这一条的核心是：**角色 + 你的真实数据 = 个性化方案**。Claude 切到「私教」角色后，关键不是它懂多少健身知识——是它**记住了你的具体数据**（训练频率、伤病史、可用器材、目标时间线、当前 PR），并**在每次你汇报进展时动态调整**。

这个机制可以推广到任何「专业知识 + 个体差异大」的场景：营养、写作练习、语言学习、谈判训练、代码 review。**角色给你专业框架，你的具体数据给 Claude 让它能个性化**。这两者缺一不可——只给数据不给角色，Claude 给你的是「通用建议」；只给角色不给数据，Claude 给你的是「教科书」。

**实操建议**：开新窗口，切到「私教」角色，**第一轮**就把你的真实情况全交代清楚（不要「我经常跑步」这种泛泛的话，要「我每周三和周六各跑 5 公里，膝盖有旧伤」这种带边界条件的）。**之后每次训练完回到这个窗口汇报**，Claude 会基于历史数据调整下周计划——这就从「搜索引擎」变成「持续跟进的合作者」了。

### 8. Practice a difficult conversation：让它扮演对面那个人

> 原文：「Most people walk into hard conversations unprepared. They know what they want to say but not what the other person will actually say back.」

**谈判、绩效对话、拒绝、要求加薪、说服老板**——这些场景的核心不是你怎么说，而是对方怎么回。你能准备的只有自己一半的话，对面那一半你不确定。

Claude 切到「对面那个人」角色后，你说什么它就**按那个人的身份回应**——如果对面那个老板是抠门的，Claude 就会用抠门老板的方式回；如果你对面那个同事是情绪化的，Claude 就会用情绪化同事的方式回。**它扮演的不是「一般人」，是「你具体要面对的那个人」**。

原推的洞察值得展开：练习几次之后，**真实对话变容易了**。原因不是「你练习了措辞」，是「你见过对方所有可能的反应路径，你不再 surprise」。**这是认知卸载的一种形式**——把「可能的意外反应」从未来的真实场景卸载到现在的低成本模拟里。

实操：把对面那个人的具体画像告诉 Claude（职级、性格、过往决策偏好、可能的底线），然后开始对话。**让 Claude 拒绝给你想要的结果**——如果你几句就说服了它，说明你的 prompt 没把对方设定得够强，**重设对方的拒绝条件**，再来一遍。

### 9. Devil's advocate：决定做完之前，让它打穿这个决定

> 原文：「You've made up your mind. You've already thought through the objections. You're convinced. That's exactly the moment to have Claude attack the decision.」

这是 9 条里**最锋利的一条**。原推的金句要原样保留：**「Five minutes now. Before you commit. Not after.」**（现在就花 5 分钟。在你 commit 之前。不是之后。）

**这是 hard mentor 的升级版**——hard mentor 是「你拿方案来我给你压力测试」，devil's advocate 是「你拿决定来我**专门攻击这个决定**」。它的功能是把「我已经想清楚了」这个心理状态拆开——**你可能想清楚了 70%，剩下的 30% 是你不愿看的**。

为什么这个时机最关键？因为在 commit 之前，**你还有时间**。一旦 commit 了，5 分钟的反对意见就是事后诸葛亮。devils-advocate 模式强制你在「心理能量最高、决策成本最低」的那个时间点做这件你不想做的事。

实操：把决定写下来——一句话能说清的决定。然后把这段文字粘到新窗口的 devil's-advocate prompt 后面，让 Claude 攻击。**重点不是「Claude 说了什么」，是「它说的有没有我没看到的角度」**。如果全是你已经想过的，说明你想得够深，可以 commit；如果你卡在某一条上答不上来，**这正是你应该在 commit 前重新想一遍的那条**。

## 五、Meta 视角：为什么 KOL 推文都是「数字 + 短标题」格式

写到这里应该停下来聊一件事：**为什么原推要做成 9 条而不是 1 条**？这是一个关于「信息格式如何在注意力经济中生存」的问题。

**「9 个独立 tip + 一张大图」是 KOL 推文的最优解**，原因有三：

1. **可分割传播**：9 条里任何一条都能被单独截图转发，**每一张图都是一条独立的 hook**。一条长推文只能被转发一次，9 个 tip 能被转发 9 次。
2. **降低承诺成本**：「看 5 分钟」远比「看 1 篇 30 分钟的文章」容易 commit。读者更容易点开，**KOL 更可能获得浏览**。
3. **制造完成感**：编号 + 短标题给人「我系统地学到了 9 件事」的感觉，**这是一种格式上的多巴胺**——即使你只认真看了 3 条，潜意识里你觉得自己「学完了」。

但代价是**信息密度被格式压缩**。9 条独立 tip 没有揭示它们之间的依赖关系——能力扩展组（A 组）的 4 条是「Claude 有什么」，角色扮演组（B 组）的 5 条是「Claude 在扮演什么」，**两组背后的轴是「我有没有切换出 AI 助手默认模式」**。原推没有把这个轴抽出来——这正是翻译反写应该做的事。

**翻译反写的目的不是「把英文翻成中文」**。是「**把作者已经知道但没说出来的底层逻辑，替作者说一遍**」。原作者 @anatolikopadze 显然知道 9 条是 2 组（原推里他用了「Give Claude a role」这一节作为分隔），但他没有在推文里写「**这两组的区别是什么**」——因为推文格式不允许。5000 字的翻译反写博客允许。

## 六、给自己的三句话（立刻能用的 1 + 1 顺序）

如果你读完只做一件事，那应该是：

1. **今天打开一个新窗口，把原推里 5 个 role prompt 任选一个贴进去**（推荐 hard mentor 或 personal psychologist，因为它们对任何人都立即有效）。先随便问 5 个问题，感受一下角色切完之后 Claude 的提问纪律变化。
2. **同一周内，挑一件你最近做过的事（比如写过的邮件、做过的方案）**——用 Artifacts 让 Claude 做一个可视化版本（dashboard、决策树、对比表），你亲手点开它、用它一次。**Artifacts 的价值在「点」不在「看」**。

不需要 9 件全做。**做对 1 件 + 1 件，A 组的杠杆和 B 组的杠杆就开始复合**。剩下的 7 件会自然跟上——因为你已经看见了「Claude 是什么」和「Claude 能扮演什么」这两条边，剩下的是填空题。

最后一句：**你过去一年用 Claude 的方式，浪费的不是 90% 的 token，是 90% 的杠杆**。token 可以用钱买，杠杆不行。

---

## 七、常见问题与排查

读完到这里，你大概率会想试 1-2 个角色。**但你可能撞上几堵墙**——这些墙不是 Claude 的问题，是你切换模式时一定会撞的，提前说破省得你放弃。

**Q1：开了 Memory，但新窗口的 Claude 好像「不记得我」。**
Memory 是跟随账号的，但新窗口的「开头」需要你给一个触发点。试着在窗口开头写「我最近在做 X，背景是 Y」——Memory 里的档案会和这段触发文字一起被召回。如果你没写触发，Claude 会保守地不主动用 Memory，避免误判。

**Q2：打开了 Extended Thinking，答案变慢了但没看出来「想」了什么。**
注意：Extended Thinking 输出的「思考过程」是折叠的，**你需要点开才能看见**。在 Claude.ai 网页版，思考块在「Thought for Xs」的折叠区域。如果你只看到最终答案往下走，说明你跳过了一个重要的证据链。

**Q3：role prompt 贴进去，Claude 还是不进入角色。**
两个常见原因。**第一是 prompt 被淹没了**——你在 role prompt 后面又写了长长的问题描述，Claude 的注意力被后面的内容吸走。修法：role prompt 和你的问题之间留一行空行，或者用「以下是规则：...」这样的强分隔标记。**第二是问题太具体了**——role prompt 设的是「硬导师」，但你问的是「帮我润色这句话」，Claude 会用普通助手模式处理润色任务。修法：先用 role prompt 问一个符合角色场景的问题（「我要做这个决定，请挑刺」），等角色立住，再切入你的具体任务。

**Q4：Artifacts 点了没反应。**
Artifacts 在 Claude.ai 网页版和 iOS/Android 客户端支持，**纯 API 调用没有 Artifacts**——API 用户需要用 `tool_use` 自己做。检查你登录的是 Claude.ai 还是某个第三方包装。

**Q5：所有 9 个都试了一遍，感觉没质变。**
这是最关键的一个问题。**9 个 tip 的价值不是「9 个都用上」，是「在 1 个具体场景里把 A 组和 B 组都开起来」**。比如你下周要做一个重要决策——同时打开 Memory（让 Claude 知道你的背景）、Artifacts（让 Claude 做出可视化决策树）、role = devil's advocate（让 Claude 攻击你的决定）、Extended Thinking（让 Claude 摊开推理）。**4 个杠杆叠在同一个决策上，质变会发生**。零散地用任何一个，杠杆都是 1.2 倍；叠起来才是 5-10 倍。

---

## 附：原文出处

- 原 thread：[@anatolikopadze on X](https://x.com/anatolikopadze/status/2057813254617858078)
- 同系列：先看 [9arm-skills：让 AI 编程助手按流程干活的合约式 Skills](https://txtmix.com/posts/tech/9arm-skills-claude-code-agent-skills-guide/)，再看本篇，体系更连贯
- Claude 官方文档：[docs.claude.com](https://docs.claude.com/)——Memory / Artifacts / Extended Thinking 三个功能的权威来源

> 本文是「x.com KOL 推文翻译反写」系列的第 15 篇。系列目的：把 KOL 推文的「9 件事」「5 步法」「3 个技巧」格式，还原为底层结构 + 操作顺序。所有文章首发于 [txtmix.com](https://txtmix.com/)。
