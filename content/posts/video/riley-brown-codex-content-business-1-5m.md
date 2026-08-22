---
title: "Riley Brown 用 Codex 跑 1.5M+ 粉丝内容生意：把每个反复干的活变成 Skill，是单人内容创业的真护城河"
date: 2026-08-19T20:30:00+08:00
lastmod: 2026-08-22T00:00:00+08:00
slug: riley-brown-codex-content-business-1-5m
categories: ["视频精读"]
tags: ["Riley Brown", "Codex", "Peter Yang", "AI Agent", "Skills", "Content Creator", "Vibecode", "Chorus", "Excalidraw", "Paper", "Remotion", "Wispr Flow", "Supadata", "SerpAPI", "Typefully", "Notion", "Claude", "GPT", "GLM 5.2", "Vibecoding", "Short Form", "Long Form"]
description: "Peter Yang 主持的 41 分钟长访谈。Riley Brown 现场演示一个 1.5M+ 跨平台粉丝的内容创业者怎么用 Codex + 自建 Skill 链跑内容生意：本地存储、computer use、Remotion 插件、internet image puller、YouTube researcher、hook outline、Excalidraw diagrams、YouTube thumbnail、Paper、Typefully、Notion。重点提炼：quality > batching、outcome-based 测试 Skill、Chain prompting、不离开 Codex 这条核心工作流哲学。"

author: 钳岳
---

# Riley Brown 用 Codex 跑 1.5M+ 粉丝内容生意：把每个反复干的活变成 Skill，是单人内容创业的真护城河

> 来源：YouTube 视频 `https://www.youtube.com/watch?v=N34zz1-RSGw` ——Peter Yang 主持的《How I Run My 1.5M+ Follower Content Business With Codex | Riley Brown》，发布于 Peter Yang 频道（`@PeterYangYT`，频道描述：「Practical AI tutorials and expert interviews for busy people」），时长 **41:47**。本文依据视频逐字稿撰写，全文与视频原话逐句对齐，引号内均为原话。

## 写在前面：为什么这一期值得拆

大多数讲「AI 怎么用在内容创业」的访谈都停在工具罗列层面——「我用 ChatGPT 写文案、用 Midjourney 出图、用 Descript 剪视频」。这一期不是。Riley Brown 把对话推到了**第二层抽象**：他不是来介绍 Codex 是什么的，是来展示「**当一个内容创业者把 Codex 当操作系统以后，单人团队的工作流应该长什么样**」。

如果只读一句话就够了，我选这一句：

> "I want multiple tabs to open up in the background, of relevant things that might be useful. Like Codex would be like, 'Hey, by the way, I opened up this link, you may want to in this one specific line, you should do this.'"（我要 Codex 在后台把可能相关的链接全打开——"顺便说一句我开了这个链接，你这段话里可能可以用上"。）

这背后是 Peter Yang 一开始就点出的「创作-分发-流程」三层模型——**YouTube 是创作枢纽，Instagram / TikTok / X 各自做 native 内容，剪辑最近才开始接触 AI**——以及 Riley 在每层上铺开的具体 Skill 链。下面我把整期内容按主题拆成 6 段，每段直接落到「为什么这样做 / 这样做换来了什么」。

**阅读目标**：读完这篇，你应该能回答三件事——Riley Brown 怎么把 Codex 当操作系统跑一个 1.5M+ 粉丝的内容生意；哪些反复干的活值得沉淀成 Skill、怎么用 outcome-based 方式迭代；这套打法的适用边界在哪里。

**目录**

1. Codex 不是 ChatGPT：本地存储与 computer use 的底层差异
2. Remotion 插件与 Internet Image Puller：素材准备交给 Skill
3. YouTube Researcher 与开场钩子大纲：把「模仿爆款」做成 Skill
4. Excalidraw + Wispr Flow：把「讲清楚一件事」做成 Skill
5. Paper + Codex：缩略图工作流的工程化
6. Chain prompting + outcome-based 调试：让 AI 自己长出新 Skill
7. 横向对比：Riley 与其他智能体玩法的位置
8. 7 条可落地建议、读完自测与待追问的问题

## 一、Codex 不是 ChatGPT：本地存储 + computer use 是底层差异

Riley 上场先把 Codex 跟 ChatGPT 的工程性区别讲清楚——这一段值得单独拎出来**，**因为很多人用 Codex 用了很久都没意识到这一点：

> "Normally when you come to Codex, it looks like this, right? It looks like ChatGPT. But when you go to ChatGPT, everything that you upload to it, if you were to upload an image, many people have done that, uploaded images or PDFs etc, all of that's stored in the cloud. When you use Codex, all of it's stored locally. And so Codex, just like Claude Code, can fully control your computer, and in fact it has a computer use skill built into the platform."

三个底层事实：

1. **本地存储 ≠ 隐私优先选择**——是「computer use 能落地的前提」。如果上传的文件留在云端、本地 Codex 看不到，那 Codex 就不可能用 Finder / 编辑器 / 浏览器这些本地工具协作。本地存储是基础设施，不是 feature。
2. **Computer use 已经是内置 Skill**——不是后期接的 plugin，是 Codex 平台默认能力。Riley 在视频里直接调 Remotion 插件、SerpAPI、本地文件——这套动作全靠 computer use 在后台调度。
3. **这跟 Claude Code 在架构上同源**——两家都在赌「LLM（大语言模型）是新的 runtime，不是新的 chatbot」。Riley 没有做两家对比，但他隐含承认 Codex / Claude Code 走的是同一条路。

这一段对工程读者的启示是：**评估 agent（智能体）平台时，「是否本地存储」比「上下文窗口多大」更基础**。前者决定能不能做 computer use，后者只决定能不能聊得更长。

## 二、Remotion 插件 + Internet Image Puller：把素材准备从「找人做」改成「问 Skill」

Riley 演示视频开场动画时给出的流程，核心思路是 pull（拉取）互联网素材，是我整期看到的**最有工程含量**的一段：

```text
@remotion  →  Skill: Remotion best practices（自带 creator brand 色系）
internet image puller  →  SerpAPI → Google Images  →  自动按 video transcript 找对应 logo
最终输出 → 1 张 Canva-可裁剪 graphic
```

两件事值得拆开：

### 2.1 Remotion best practices 这个 Skill 是怎么诞生的

Riley 自己说：「`Remotion best practices`」这个 Skill 是他把 Codex 用了一阵以后**自己攒出来的**。它不是 OpenAI 官方插件，是 Riley 在 Codex 设置里**手写一份「creator brand」规范**（配色、字体、动效节奏），然后让 Codex 记住——下次调用 `@remotion` 时自动套用。

这背后是一个在 AI 工程里被反复验证的范式：**LLM 的「行为」本质上是 prompt（提示词）+ context 的组合**。把「我想要 Riley 那种开场动画」拆成一段 Remotion best practices 的 Markdown 规范文档，比让模型每次重新从零学起更省 token（词元）、更稳、更可调试。

### 2.2 Internet Image Puller 用 SerpAPI 解决了「素材找不到」问题

SerpAPI 是一款搜索结果 API（应用程序接口），Riley 用它做图片检索。他在演示里直接说：「I have a skill, I actually, I think it's called, um, image pull, internet image puller. There it is. So this internet image puller is one where it'll go off, it'll actually use something called the SerpAPI. Um, and so it uses Google Images within the SerpAPI, and it will actually find the relevant logos related to whatever video it is.」

链条是：

1. Riley 把要做 B-roll 的 video transcript 喂给 Codex
2. Codex 调 internet image puller
3. Skill 调 SerpAPI 的 Google Images endpoint
4. 按 transcript 关键词拉对应的 logo
5. 拉到的 logo 直接进 Remotion 模板

这等于**把「找 logo」这件事从「我得手动 Google → 截图 → 拖进 Figma」压缩成「我说一句话」**。Riley 进一步演示 chain prompting——可以同时说「pull the relevant logos and then make a graphic for this」让两个 Skill 串起来。

## 三、YouTube Researcher + Hook（钩子）Outline：用 Supadata 把「模仿爆款」做成 Skill

Riley 在讲他的 hook（钩子，视频开场钩子）生成工作流时提到了**两个核心 Skill**：

```text
YouTube researcher  →  Supadata API → 1 秒拉全 transcript
hook outline        →  按某个爆款视频的 intro 结构 → 生成新视频 hook
```

### 3.1 Supadata vs yt-dlp 的工程对比

> "I've been using yt-dlp, but you're saying that this other thing can just pull the transcript in one second?" ——Peter Yang
>
> "Yeah, I mean it's just like a quick API call, like yt-dlp, if I'm not mistaken, it'll download the full video and then pull the transcript, that is super data-intensive. And, yeah, Supadata will just, you know, you can say spin up sub-agents, that's one thing you can do with Codex, and they have a really cool UI. You can just ask it to use sub-agents, and it'll split off into like six agents, and it will scrape it all in like 30 seconds."

三个层次的事实：

1. **yt-dlp 是本地下载 + 解析**：要把完整视频拉下来再解析，对带宽、磁盘、CPU 都很贵。
2. **Supadata 是远端 API**：直出 transcript，调用一次就能拿到整段文字。
3. **Codex 的 sub-agent UI**：能把「拉 6 个频道的 transcript」拆成 6 个并发 agent，30 秒扫完整个频道。

**这一段对工程读者的启示是：当某个工程链路有「本地重资源版本」和「远端 API 版本」时，永远优先选远端 API 版本**。前者把重活压在自己机器上，后者把重活压给 SaaS（软件即服务）平台——后者永远更便宜、更可扩展、更省 token。

### 3.2 Hook Outline：把「模仿爆款」做成可复用结构

Riley 的 hook 工作流是：

1. 找到一个「好 hook 的爆款视频」（这次是 Alex Hormozi）
2. 调 hook outline → 让 Codex 把这个视频的 hook 结构抽出来
3. 把自己的新视频想法喂进去 → 让 Codex 按这个结构写新 hook

为什么这样做？因为「**前 30 秒决定 70% 的留存**」——Riley 自己说「the intro is the most important part, and then the rest of the video is kind of free flowing」。这意味着对内容创业来说，**最值得抽象、最值得做成 Skill 的，恰好是 intro 这一段**。其他段反而应该自由流动。

### 3.3 GPT vs Claude vs GLM 5.2 的工程分歧

Riley 在演示时点出了一个**对工程读者很关键的差异**：

> "One thing that's really annoying about Codex, and one of the reasons why I've been moving off of it, is because the GPT models won't pull the transcript. You can see here that it summarized his intro, and the reason it did that is because of copyright infringement. Um, it didn't want to, because it doesn't, yeah, it doesn't. But Claude's models will do it without thinking. So that's why I've been using Claude for this use case. Yeah, interesting, um, that's funny that Claude is actually more open than GPT, it's the other way around. So, it's task dependent. Um, the open models don't care either, like GLM 5.2 will do it any time."

三个工程事实：

1. **GPT 在 Codex 上拒绝整段 transcript 复述**——Riley 推测是版权过滤。
2. **Claude 不 care**——直接复述。
3. **GLM 5.2 也复述**——Riley 把它归类为「open models don't care either」。

这条工程观察很重要：**同一个任务在不同 model 上的实际行为可能天差地别**——这不是 prompt 工程问题，是 model policy 问题。Riley 隐含承认：**当某个 Skill 必须靠 model 「不拒绝」才能跑通时，model 选择本身是工程决策的一部分**。

## 四、Excalidraw Diagrams + Wispr Flow：把「讲清楚一件事」做成一个 Skill

Riley 演示了**他怎么用 Wispr Flow + Excalidraw 录视频**：戴上 AirPods Max 开 Wispr Flow 走 10 分钟、口述大纲，Codex 把口述直接转成 Excalidraw 风格的 diagram（9 张分镜）。

```text
Wispr Flow 口述
   ↓
"我要做 Codex 视频，我想讲 9 张分镜：xxx、xxx、xxx"
   ↓
Excalidraw diagrams skill（自带 Riley 风格 sections）
   ↓
80% 可用 diagram → Riley 自己改 20–30 分钟
```

这条工作流解决的是「**内容创业者最难的一件事**」——把脑里的想法结构化。Riley 没用 Todoist 没用 Notion template，而是**让 Wispr Flow 把脑子直接 dump 出来，让 Codex 把 dump 转成可视结构**。这条链省的不是时间，是「脑子里想清楚再写清楚」之间的那道翻译税。

## 五、Paper + Codex 替换 Alex Hormozi 头像：thumbnail 工作流的工程化

这一段是整期最有「**AI 视觉 + AI 编排**」含量的一段。Riley 用 Codex 替换 thumbnail 里的 Alex Hormozi 头像变成自己的脸，工程链路示例如下：

```text
1. Codex 调 Paper API（AI-native Figma）
2. Codex 调 Alex Hormozi / Dan Martell YouTube 频道
3. 拉最火的 N 个 thumbnail → 直接放到 Paper board
4. Riley 复制其中一个 → 粘贴到自己的 Paper page
5. Codex 调 Paper 内置的图像生成 → "把戴胡子的人替换成不戴胡子的人"
6. Codex spam 生成 7 个版本 → Riley 选最好的
```

Riley 在这里反复强调一个工程观点：

> "Paper is an AI-native Figma, and when I say AI-native I mean that it is an application built for AI first, they basically took a lot of the good stuff about Figma and made it really easy to connect to any tool."

**「AI-native」 vs 「AI-friendly」 的区别**：AI-friendly 是「保留旧 UX，加 AI 插件」；AI-native 是「从第一天起就假设 AI 是主用户」。Paper 把 board 设计成「**可以由 agent 写入**」，而不是「**只能由人拖拽**」——这是 Riley 能用 Codex 自动化 thumbnail 流程的根本原因。

这条对工程读者的启示是：**评估一个新工具时，「AI-native vs AI-friendly」是一个比 surface-level UX 更根本的维度**。前者可自动化，后者只能当 chatbot 用。

## 六、Chain prompting + outcome-based Skill 调试：让 AI 自己长出新 Skill

Riley 在最后讲了一段**关于怎么持续做 Skill 的方法论**：

> "Do you look at the skill files manually, no, you just look at the output, right?"
>
> "No, I've never looked at a skill file once, like, it's test-based, it's like, ask AI to do a thing, use a skill, if it does properly, great. If it doesn't, you tell the AI, 'Hey, you didn't do a good job,' and then, 'please change the skill so that you don't do that again.' Then you want to go to a new chat, so the context is cleared, so you can test it again. Test the agent in a new chat, see if it does it successfully. If it does it successfully, great, right, and once it does it incorrectly, you update the skill, right. That is the way better way to do it than to manually edit the skill."

三个工程观点：

1. **Never look at skill files manually**——Riley 自己从来没打开过 skill 文件。他只看 output 决定「这个 Skill 行不行」。
2. **Outcome-based testing**——「如果你让 AI 用 Skill 做一件事，做得好就行；做得不好就告诉 AI 改 Skill」。改完 Skill **必须开新 chat**——因为旧 chat 的 context 会污染测试结果。
3. **Don't manually edit skill files**——Riley 明确反对「手写 Skill 文件」流派，他觉得那是「**为某个 model 优化 prompt，但 model 一升级就全失效**」。

这跟传统 prompt engineering 立场相反——传统派说「prompt 是工程资产，要 review、要 diff、要版本管理」；Riley 派说「**skill 是 outcome 驱动的，model 一变 skill 就该自动重生成**」。这不是工程审美分歧，是**模型升级频率 vs 文档维护频率的工程取舍**。

最后 Riley 补了一句关键 caveat：

> "This is for my creative workflows, right, they're very low risk. You know, if we were doing some mission-critical thing, which we actually do, like when we're dealing with clients, or when it has to do with anything that has to do with payments or sensitive documents, yes, we'll go in and analyze the skills."

「**低风险 vs 高风险 workflow 用不同方法**」——内容创业无所谓，丢了再发；但客户合同、付款、敏感文档要走人工 review。

## 七、横向对比：Riley vs 我以前拆过的几个 AI Coding Agent 玩家

| 玩家 | 工作流哲学 | Skill 策略 | 对 model 升级的态度 |
| --- | --- | --- | --- |
| Riley Brown（本期） | Codex 当 OS，agent 在 OS 上跑 | outcome-based，AI 自己维护 | 「model 变了我让 AI 重写 skill」 |
| prime-agent（8-15） | persistent Python REPL 当 control plane | 小步 evidence-backed 更新 + rollback | harness 持久，model 可换 |
| Pi（8-17） | 代码即真相 / bash 够用 | 系统最小化（4 个内置工具 + < 1000 token system prompt） | 拒绝整套 MCP 生态 |
| Claude Code / OpenAI Codex | LLM 是新 runtime | computer use + plugin 体系 | 不强调 |
| LangGraph / Dify / n8n | workflow 编排，可视化 | 显式 node（节点）-edge 图 | 不强调 |

Riley 这一期跟 prime-agent 在「harness 持久、model 可换」上同源；跟 Pi 在「反对 complexity 堆叠」上同源；跟传统 workflow 工具完全反向——他不画 workflow 图，他让 AI 自己长出 Skill。

## 八、给内容创业者的 7 条可立即落地的建议

不是抽象建议，全部从本期 Riley 的工作流里**直接抽出**：

1. **第一件事**：把你每个反复做的「动作」列出来（拉素材、做 diagram、写 hook、生成 thumbnail、跨平台分发），按「是否每周至少做 3 次」筛——只有这种才值得做成 Skill。
2. **Skill 写法**：不要手写 prompt，让 Codex 自己用 `outcome-based` 方式迭代。开新 chat 测试，避免 context 污染。
3. **Model 选择**：GPT / Claude / GLM 5.2 在「是否会拒绝复述 transcript」这类 policy 上行为天差地别，按任务选 model，不要一锅烩。
4. **Remotion best practices 这种「个人 brand 规范」Skill**：先积累，再做成 Skill。先用 Codex 干两三个月，再决定哪些规范值得沉淀。
5. **Wispr Flow + Codex + Excalidraw**：口述 → diagram 是把「脑子里的模糊结构」变现的最快路径，单人内容创业的核心武器。
6. **Paper 这种 AI-native 工具**优先于 Figma 这种 AI-friendly 工具——前者能由 agent 写入，后者只能由人拖。
7. **「quality > batching」**：Riley 反复强调——batching 长期会让内容变 soulless，单条视频质量沉淀比日更数量重要。

**常见执行错误与排查**：按这套打法落地时，三个最容易踩的坑，都来自本期视频里 Riley 的明确提醒：

1. **手写 / 手改 Skill 文件**。Riley 明确反对，理由是这是在为某个模型优化 prompt，模型一升级就失效；排查方式：看自己是否经常打开 skill 文件改字句，是就该换成 outcome-based 迭代。
2. **在旧 chat 里测试改过的 Skill**。旧上下文会污染测试结果，改完 Skill 必须开新 chat 再测——这是 Riley 流程里的固定动作。
3. **高风险流程也照搬 outcome-based**。客户、付款、敏感文档相关的 workflow，Riley 自己也会回去人工分析 skill 文件；内容创作低风险可以放开，别的场景不能照搬。

## 九、几个值得追问的工程问题

这期 Riley 没有展开但值得追问的事：

1. **「不离开 Codex」的工程边界**：Riley 强调他不爱切换 tab，所以 everything happens in Codex。**但这种「单一 app 全包」架构的代价是什么**？比如 Codex 自己挂了怎么办？比如 agent 状态怎么跨设备同步？
2. **「outcome-based skill 维护」的 debug 可观测性**：Riley 不读 skill 文件，那出问题怎么 trace？比如某个 hook 突然变得很烂，是哪个 skill 改坏了？
3. **「Mac mini 跑 Codex 自动化」的工程含义**：Riley 提到「I have Codex running on my little Mac mini, I have some automations there」——这种「个人自动化 farm」的可靠性 vs Claude agents in cloud 的对比，值得单独写一篇。

**读完自测**：三个问题检验这套方法你是否真的接住了。

1. 你能列出自己每周至少做 3 次的重复动作，并判断哪些值得做成 Skill 吗？
2. 你能说出 outcome-based 迭代为什么必须开新 chat 测试吗？
3. 你能分清哪些任务该交给 Claude / GLM 5.2、哪些交给 GPT 吗？

## 十、引用、参考与下一步

### 数据来源
- 视频：`https://www.youtube.com/watch?v=N34zz1-RSGw`
- 频道：`@PeterYangYT`（Peter Yang），频道描述「Practical AI tutorials and expert interviews for busy people」
- 嘉宾：`@RileyBrownAI`（Riley Brown），1.5M+ 跨平台粉丝；公司 Chorus（agent orchestration），前作 Vibecode
- 逐字稿：从视频逐字稿提取，笔者逐句校核，全文 41:47 与视频原话对齐

### 提到的工具一览

- **Codex / ChatGPT**（OpenAI）—— local-first + computer use + plugin 体系
- **Claude / Claude Code**（Anthropic）—— transcript 复述 policy 更开放
- **GLM 5.2**（智谱）——「open models don't care either」
- **Remotion**（React-based 视频框架）—— `@remotion` Skill 自带 creator brand
- **SerpAPI / Google Images**—— internet image puller 后端
- **Supadata**—— 1 秒拉 transcript 的远端 API
- **Excalidraw**—— 白板 diagram，Codex 渲染成 Riley 自定义 sections 风格
- **Wispr Flow**—— 语音转写，Riley 走 10 分钟直接 dump 想法
- **Paper**—— AI-native Figma，AI-first board
- **Typefully**—— Twitter 草稿队列
- **Notion**—— 视频数据库，Codex 写入 + 读出 link
- **Chorus / Vibecode**（Riley 自己产品）—— Claude agents / 任何 model 编排

### 后续工作
- 下一期建议拆：Peter Yang 自己的 Codex 玩法 + Claude agent 在 Slack 里的编排哲学
- 关联阅读：prime-agent 反写（`/posts/prime-intellect-prime-agent/`）、Pi 反写（`/posts/video-reading/pi-coding-agent-code-as-truth-no-mcp/`）

### 反馈
- 这篇如果哪里写错了 / 漏了某段，请直接告诉我——本文与逐字稿 1:1 对照，原话均标引号。

---

> 截稿日 2026-08-19 20:30 GMT+8。数据点全部从 41:47 逐字稿提取，引号内为 Riley / Yang 原话；文中第三方工具版本与功能随上游更新可能漂移。