---
title: "Riley Brown 用 Codex 跑 150 万粉内容生意：把反复干的活变成 Skill，才是单人创业的护城河"
date: 2026-08-19T20:30:00+08:00
lastmod: 2026-09-24T00:00:00+08:00
slug: riley-brown-codex-content-business-1-5m
categories: ["视频精读"]
tags: ["Riley Brown", "Codex", "AI Agent", "Skills", "内容创业", "工作流"]
description: "Peter Yang 主持的 41 分钟访谈。Riley Brown 现场演示一个 150 万跨平台粉丝的内容创业者怎么用 Codex 加自建 Skill 链跑内容生意：本地存储、computer use、Remotion 插件、图片抓取、YouTube 研究、开场钩子大纲、Excalidraw 图解、缩略图生成。方法论核心：质量重于批量、按结果迭代 Skill、链式提示、不离开 Codex。"

author: 钳岳
---

> 来源：YouTube 视频 `https://www.youtube.com/watch?v=N34zz1-RSGw` —— Peter Yang 主持的《How I Run My 1.5M+ Follower Content Business With Codex | Riley Brown》，发布于 Peter Yang 频道（`@PeterYangYT`，频道简介：「Practical AI tutorials and expert interviews for busy people」），时长 **41:47**。本文依据视频逐字稿撰写，引号内均为 Riley 或 Peter Yang 的原话。

## 写在前面：为什么这一期值得拆

大多数讲「AI 怎么用在内容创业」的访谈都停在工具罗列层面——「我用 ChatGPT 写文案、用 Midjourney 出图、用 Descript 剪视频」。这一期不是。Riley Brown 把对话推到了第二层：他不是来介绍 Codex 是什么的，是来展示**当一个内容创业者把 Codex 当操作系统之后，单人团队的工作流该长什么样**。

整期最值得记住的一句是：

> "I want multiple tabs to open up in the background, of relevant things that might be useful. Like Codex would be like, 'Hey, by the way, I opened up this link, you may want to in this one specific line, you should do this.'"（我要 Codex 在后台把可能相关的链接全打开——"顺便说一句我开了这个链接，你这段话里可能可以用上"。）

这背后是 Peter Yang 一开场就点出的「创作-分发-流程」三层结构——YouTube 是创作枢纽，Instagram、TikTok、X 各自做平台原生内容，剪辑最近才开始接触 AI——以及 Riley 在每一层上铺开的 Skill 链。Skill 在这里的含义是：把一套反复使用的做法沉淀成可复用的指令文件，让智能体每次都按同一套规范执行。

**阅读目标**：读完这篇，你应该能回答三件事——Riley Brown 怎么把 Codex 当操作系统跑一个 150 万粉丝的内容生意；哪些反复干的活值得沉淀成 Skill、怎么按结果迭代；这套打法的适用边界在哪里。

**目录**

1. Codex 不是 ChatGPT：本地存储与 computer use
2. Remotion 插件与图片抓取 Skill：把素材准备交给智能体
3. YouTube Researcher 与钩子大纲：把「模仿爆款」做成 Skill
4. Excalidraw 与 Wispr Flow：把「讲清楚一件事」做成 Skill
5. Paper 加 Codex：缩略图工作流的工程化
6. 链式提示与按结果迭代：让 AI 自己长出新 Skill
7. 横向对比：Riley 在智能体玩法谱系里的位置
8. 七条可落地建议与三个常见误区
9. 值得追问的工程问题与读完自测
10. 引用、参考与下一步

## 一、Codex 不是 ChatGPT：本地存储与 computer use

Riley 上场先把 Codex 跟 ChatGPT 的工程性区别讲清楚。很多人用 Codex 用了很久，都没意识到这一点：

> "Normally when you come to Codex, it looks like this, right? It looks like ChatGPT. But when you go to ChatGPT, everything that you upload to it, if you were to upload an image, many people have done that, uploaded images or PDFs etc, all of that's stored in the cloud. When you use Codex, all of it's stored locally. And so Codex, just like Claude Code, can fully control your computer, and in fact it has a computer use skill built into the platform."

从这段原话里能读出三个底层事实。

第一，**本地存储不是隐私偏好，是 computer use 能落地的前提**。computer use 指模型直接操作电脑的能力。如果上传的文件留在云端、本地 Codex 看不到，它就不可能调用 Finder、编辑器、浏览器这些本地工具来协作。本地存储是基础设施，不是锦上添花的功能。

第二，computer use 在 Codex 里是内置能力，不是后期外挂的插件。Riley 现场调用 Remotion 插件、SerpAPI、本地文件，整套动作都靠 computer use 在后台调度。

第三，这跟 Claude Code 在架构上同源——两家都在赌同一个方向：**LLM（大语言模型）是新运行时，不是新聊天窗口**。Riley 没有做两家对比，但他默认了 Codex 和 Claude Code 走的是同一条路。

对工程读者的启示是：评估智能体平台时，「是否本地存储」比「上下文窗口多大」更基础。前者决定能不能做 computer use，后者只决定能不能聊得更长。

## 二、Remotion 插件与图片抓取 Skill：把素材准备交给智能体

Riley 演示视频开场动画时给出的流程，核心思路是从互联网拉取素材，是整期演示里工程含量最高的一段：

```text
@remotion  →  Skill: Remotion best practices（自带 creator brand 色系）
internet image puller  →  SerpAPI → Google Images  →  自动按 video transcript 找对应 logo
最终输出 → 1 张 Canva-可裁剪 graphic
```

两件事值得拆开讲。

### 2.1 Remotion best practices 这个 Skill 是怎么来的

「`Remotion best practices`」不是 OpenAI 官方插件，是 Riley 把 Codex 用了一阵以后自己攒出来的：他在 Codex 设置里手写一份「creator brand」规范（配色、字体、动效节奏），让 Codex 记住，下次调用 `@remotion` 时自动套用。

这背后是 AI 工程里被反复验证的一个范式：**LLM 的行为本质上是 prompt（提示词）加 context（上下文）的组合**。把「我想要 Riley 那种开场动画」拆成一份 Remotion best practices 的 Markdown 规范文档，比让模型每次从零学起更省 token（词元）、更稳、也更可调试。

### 2.2 Internet Image Puller 用 SerpAPI 解决「素材找不到」

SerpAPI 是一款搜索结果 API（应用程序接口），Riley 用它做图片检索。他在演示里直接说：

> "I have a skill, I actually, I think it's called, um, image pull, internet image puller. There it is. So this internet image puller is one where it'll go off, it'll actually use something called the SerpAPI. Um, and so it uses Google Images within the SerpAPI, and it will actually find the relevant logos related to whatever video it is."

链条是这样的：

1. Riley 把要做 B-roll（补充镜头）的 video transcript（视频文字稿）喂给 Codex
2. Codex 调 internet image puller
3. Skill 调 SerpAPI 的 Google Images 端点
4. 按文字稿关键词拉对应的 logo
5. 拉到的 logo 直接进 Remotion 模板

「找 logo」这件事，过去是手动 Google、截图、拖进 Figma；现在压缩成说一句话。Riley 还演示了链式提示（chain prompting）：一句话里同时说「pull the relevant logos and then make a graphic for this」，让两个 Skill 串着跑。

## 三、YouTube Researcher 与钩子大纲：把「模仿爆款」做成 Skill

Riley 讲他的 hook（开场钩子）生成工作流时，提到两个核心 Skill：

```text
YouTube researcher  →  Supadata API → 1 秒拉全 transcript
hook outline        →  按某个爆款视频的 intro 结构 → 生成新视频 hook
```

### 3.1 Supadata 与 yt-dlp 的工程对比

> "I've been using yt-dlp, but you're saying that this other thing can just pull the transcript in one second?" ——Peter Yang
>
> "Yeah, I mean it's just like a quick API call, like yt-dlp, if I'm not mistaken, it'll download the full video and then pull the transcript, that is super data-intensive. And, yeah, Supadata will just, you know, you can say spin up sub-agents, that's one thing you can do with Codex, and they have a really cool UI. You can just ask it to use sub-agents, and it'll split off into like six agents, and it will scrape it all in like 30 seconds."

同一件事，两条技术路线。yt-dlp 是本地下载加解析，要把完整视频拉下来再提文字稿，对带宽、磁盘、CPU 都很贵；Supadata 是远端 API，调用一次直出文字稿。Codex 的子智能体（sub-agent）界面还能把「拉 6 个频道的文字稿」拆成 6 个并发 agent，30 秒扫完整个频道。

顺着这个对比得出的判断是：当同一条链路既有「本地重资源版本」又有「远端 API 版本」时，优先选后者。前者把重活压在自己机器上，后者压给 SaaS（软件即服务）平台——更便宜、更可扩展、更省 token。

### 3.2 Hook Outline：把「模仿爆款」做成可复用结构

Riley 的 hook 工作流分三步：

1. 找到一个「好 hook 的爆款视频」（这次是 Alex Hormozi）
2. 调 hook outline，让 Codex 把这个视频的 hook 结构抽出来
3. 把自己的新视频想法喂进去，让 Codex 按这个结构写新 hook

为什么值得这么做？因为开场几乎决定整支视频的去留。Riley 自己说「the intro is the most important part, and then the rest of the video is kind of free flowing」——开场之外的部分可以自由发挥。对内容创业来说，**最值得抽象、最值得做成 Skill 的，恰好是开场这一段**。

### 3.3 GPT、Claude 与 GLM 5.2 在同一任务上的分歧

Riley 在演示时点出了一个对工程读者很关键的差异：

> "One thing that's really annoying about Codex, and one of the reasons why I've been moving off of it, is because the GPT models won't pull the transcript. You can see here that it summarized his intro, and the reason it did that is because of copyright infringement. Um, it didn't want to, because it doesn't, yeah, it doesn't. But Claude's models will do it without thinking. So that's why I've been using Claude for this use case. Yeah, interesting, um, that's funny that Claude is actually more open than GPT, it's the other way around. So, it's task dependent. Um, the open models don't care either, like GLM 5.2 will do it any time."

三个事实：GPT 在 Codex 上拒绝整段复述文字稿，Riley 推测是版权过滤；Claude 不受影响，直接复述；GLM 5.2 也照做，Riley 把它归进「open models don't care either」。

这条观察的价值在于：**同一个任务在不同模型上的实际行为可能天差地别**——这不是提示词工程问题，是模型策略问题。当某个 Skill 必须靠模型「不拒绝」才能跑通时，选哪个模型本身就是工程决策的一部分。

## 四、Excalidraw 与 Wispr Flow：把「讲清楚一件事」做成 Skill

Riley 演示了他怎么用 Wispr Flow 加 Excalidraw 录视频：戴上 AirPods Max，开着 Wispr Flow 走 10 分钟，口述大纲，Codex 把口述直接转成 Excalidraw 风格的图解（9 张分镜）。

```text
Wispr Flow 口述
   ↓
"我要做 Codex 视频，我想讲 9 张分镜：xxx、xxx、xxx"
   ↓
Excalidraw diagrams skill（自带 Riley 风格 sections）
   ↓
80% 可用 diagram → Riley 自己改 20–30 分钟
```

这条工作流解决的是内容创业者最难的一件事：把脑子里的想法结构化。Riley 没用 Todoist，也没用 Notion 模板，而是让 Wispr Flow 把脑子直接倒出来，再让 Codex 把倒出来的东西转成可视结构。这条链省的不是时间，是「脑子里想清楚」和「写清楚」之间的那道翻译税。

## 五、Paper 加 Codex：缩略图工作流的工程化

这是整期在「AI 视觉加 AI 编排」上含量最高的一段。Riley 用 Codex 把缩略图（thumbnail）里的 Alex Hormozi 头像换成自己的脸，工程链路如下：

```text
1. Codex 调 Paper API（AI-native Figma）
2. Codex 调 Alex Hormozi / Dan Martell YouTube 频道
3. 拉最火的 N 个 thumbnail → 直接放到 Paper board
4. Riley 复制其中一个 → 粘贴到自己的 Paper page
5. Codex 调 Paper 内置的图像生成 → "把戴胡子的人替换成不戴胡子的人"
6. Codex 连续生成 7 个版本 → Riley 选最好的
```

Riley 在这里反复强调一个观点：

> "Paper is an AI-native Figma, and when I say AI-native I mean that it is an application built for AI first, they basically took a lot of the good stuff about Figma and made it really easy to connect to any tool."

「AI 原生（AI-native）」和「AI 友好（AI-friendly）」是两个不同的设计立场：后者保留旧交互，往上加 AI 插件；前者从第一天起就假定 AI 是主要用户。Paper 把画板设计成可以由智能体写入，而不是只能由人拖拽——这是 Riley 能用 Codex 自动化整条缩略图流程的根本原因。

这个区分放到工程选型里同样成立：「AI 原生还是 AI 友好」比界面好不好看更根本。前者可自动化，后者只能当聊天框用。

## 六、链式提示与按结果迭代：让 AI 自己长出新 Skill

访谈的最后，Riley 讲了他持续维护 Skill 的方法论：

> "Do you look at the skill files manually, no, you just look at the output, right?"
>
> "No, I've never looked at a skill file once, like, it's test-based, it's like, ask AI to do a thing, use a skill, if it does properly, great. If it doesn't, you tell the AI, 'Hey, you didn't do a good job,' and then, 'please change the skill so that you don't do that again.' Then you want to go to a new chat, so the context is cleared, so you can test it again. Test the agent in a new chat, see if it does it successfully. If it does it successfully, great, right, and once it does it incorrectly, you update the skill, right. That is the way better way to do it than to manually edit the skill."

这套「按结果迭代（outcome-based）」的打法有三条要点。

其一，Riley 从来不打开 Skill 文件看，只看输出结果来判断「这个 Skill 行不行」。

其二，迭代方式是对话式的：AI 用 Skill 做一件事，做得好就通过；做不好就告诉它「你没做好，去改 Skill，别再犯」。改完之后**必须开新对话再测**——旧对话的上下文会污染测试结果，你分不清是 Skill 改好了还是上下文在兜底。

其三，他明确反对手写、手改 Skill 文件的流派。理由是那等于在为某一个模型版本优化提示词，模型一升级就全部失效。这跟传统提示词工程的立场正好相反——传统派把提示词当工程资产，要 review、要 diff、要版本管理；Riley 派认为 Skill 由结果驱动，模型一变就该让 AI 重新生成。这不是审美分歧，是模型升级频率与文档维护频率之间的工程取舍。

最后他补了一个重要边界：

> "This is for my creative workflows, right, they're very low risk. You know, if we were doing some mission-critical thing, which we actually do, like when we're dealing with clients, or when it has to do with anything that has to do with payments or sensitive documents, yes, we'll go in and analyze the skills."

低风险与高风险的工作流要用两套方法：内容创作丢了再发，可以放开让 AI 自己迭代；客户合同、付款、敏感文档相关的流程，他自己也会回去人工分析 Skill 文件。

## 七、横向对比：Riley 在智能体玩法谱系里的位置

把 Riley 的工作流和此前拆过的几个智能体玩家放在一起看：

| 玩家 | 工作流哲学 | Skill 策略 | 对模型升级的态度 |
| --- | --- | --- | --- |
| Riley Brown（本期） | Codex 当操作系统，智能体在上面跑 | 按结果迭代，AI 自己维护 | 「模型变了让 AI 重写 Skill」 |
| prime-agent（8-15） | persistent Python REPL 当 control plane | 小步 evidence-backed 更新 + rollback | harness 持久，模型可换 |
| Pi（8-17） | 代码即真相 / bash 够用 | 系统最小化（4 个内置工具 + 不足 1000 token 系统提示） | 拒绝整套 MCP 生态 |
| Claude Code / OpenAI Codex | LLM 是新运行时 | computer use + 插件体系 | 不强调 |
| LangGraph / Dify / n8n | workflow 编排，可视化 | 显式节点-边图 | 不强调 |

Riley 这一期跟 prime-agent 在「运行环境持久、模型可换」上同源，跟 Pi 在「拒绝复杂度堆叠」上同源，跟传统 workflow 工具完全反向——他不画流程图，他让 AI 自己长出 Skill。

## 八、七条可落地建议与三个常见误区

以下七条全部从本期 Riley 的工作流里直接抽出，不是抽象建议：

1. **先列清单再动手**：把你每个反复做的动作列出来（拉素材、做图解、写钩子、生成缩略图、跨平台分发），按「是否每周至少做 3 次」筛选——只有这种才值得做成 Skill。
2. **Skill 用按结果迭代的方式养**：不要手写提示词，让 Codex 自己迭代。每次改完开新对话测试，避免上下文污染。
3. **按任务选模型**：GPT、Claude、GLM 5.2 在「是否拒绝复述文字稿」这类策略上行为天差地别，别一锅烩。
4. **个人品牌规范先积累再沉淀**：像 Remotion best practices 这种 Skill，先用 Codex 干两三个月，再决定哪些规范值得固化。
5. **口述转图解是最快路径**：Wispr Flow 加 Codex 加 Excalidraw，把脑子里的模糊结构直接变现，是单人内容创业的核心武器。
6. **优先选 AI 原生工具**：Paper 优于 Figma 这类 AI 友好工具——前者的画板能由智能体写入，后者只能由人拖。
7. **质量重于批量（quality > batching）**：Riley 反复强调，批量生产长期会让内容失去灵魂，单条视频的质量沉淀比日更数量重要。

落地时最容易踩的坑有三个，都来自 Riley 本期的明确提醒：

1. **手写或手改 Skill 文件**。这是在为某个模型版本优化提示词，模型一升级就失效。排查方法：看自己是否经常打开 Skill 文件改字句，是就该换成按结果迭代。
2. **在旧对话里测试改过的 Skill**。旧上下文会污染测试结果，改完必须开新对话再测，这是 Riley 流程里的固定动作。
3. **高风险流程照搬按结果迭代**。客户、付款、敏感文档相关的流程，Riley 自己也会回去人工分析 Skill 文件；内容创作低风险可以放开，别的场景不能照搬。

## 九、值得追问的工程问题与读完自测

这期没有展开、但值得追问的事有三件：

1. **「不离开 Codex」的边界**：Riley 强调他不爱切换窗口，所以所有事都发生在 Codex 里。这种「单一应用全包」架构的代价是什么？Codex 自己挂了怎么办？智能体状态怎么跨设备同步？
2. **按结果维护的可观测性**：Riley 不读 Skill 文件，那出了问题怎么定位？某个钩子突然变差，是哪个 Skill 改坏的？
3. **个人自动化农场的可靠性**：Riley 提到「I have Codex running on my little Mac mini, I have some automations there」——这种个人级自动化和云端智能体服务在可靠性上的差距，值得单独写一篇。

### 读完自测

1. 你能列出自己每周至少做 3 次的重复动作，并判断哪些值得做成 Skill 吗？
2. 你能说出按结果迭代为什么必须开新对话测试吗？
3. 你能分清哪些任务该交给 Claude、GLM 5.2，哪些交给 GPT 吗？

## 十、引用、参考与下一步

### 数据来源

- 视频：`https://www.youtube.com/watch?v=N34zz1-RSGw`
- 频道：`@PeterYangYT`（Peter Yang），频道简介「Practical AI tutorials and expert interviews for busy people」
- 嘉宾：`@RileyBrownAI`（Riley Brown），150 万+ 跨平台粉丝，Agent Native 创始人，早年 vibe coding 产品 Vibecode 作者
- 逐字稿：从视频逐字稿提取，逐句校核，全文与 41:47 视频原话对齐

### 提到的工具一览

- **Codex / ChatGPT**（OpenAI）——本地存储 + computer use + 插件体系
- **Claude / Claude Code**（Anthropic）——复述文字稿的策略更开放
- **GLM 5.2**（智谱）——「open models don't care either」
- **Remotion**（基于 React 的视频框架）——`@remotion` Skill 自带 creator brand
- **SerpAPI / Google Images**——internet image puller 的后端
- **Supadata**——一秒拉全文字稿的远端 API
- **Excalidraw**——白板图解工具，Codex 渲染成 Riley 自定义 sections 风格
- **Wispr Flow**——语音转写，Riley 走 10 分钟直接倒出想法
- **Paper**——AI 原生的 Figma，画板可由 AI 写入
- **Typefully**——Twitter 草稿队列
- **Notion**——视频数据库，Codex 写入加读出链接
- **Vibecode**（Riley 早期 vibe coding 产品）——用 Claude Code 以自然语言生成应用；现任职创业公司 Agent Native

### 关联阅读与下一步

- 本系列此前拆解：prime-agent（`/posts/prime-intellect-prime-agent/`）、Pi（`/posts/video-reading/pi-coding-agent-code-as-truth-no-mcp/`）
- 下一期建议拆：Peter Yang 自己的 Codex 玩法，以及 Claude 智能体在 Slack 里的编排哲学

### 说明

本文与逐字稿逐一对照，原话均以引号标出；如有错漏，以原视频为准。截稿于 2026-08-19 20:30 GMT+8，文中数据点全部从 41:47 逐字稿提取；第三方工具的版本与功能随上游更新可能漂移。
