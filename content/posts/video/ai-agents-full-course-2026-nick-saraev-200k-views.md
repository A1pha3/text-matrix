---
title: "Nick Saraev 的 AI Agent 无代码大师班：三大平台、核心循环与提示词架构"
date: "2026-04-29T15:01:00+08:00"
slug: "ai-agents-full-course-2026-nick-saraev-200k-views"
description: "Nick Saraev《AI Agents Full Course 2026》（YouTube EsTrWCV0Ph4，494K 观看）据字幕重建：这是一门明确的无代码课——不写 Python，而是教你用 Codex / Claude Code / Antigravity 三大 agent 平台。核心是 Observe→Think→Act 的智能体循环与'完成的定义'、会自改的 agents.md、多智能体 MCP 编排与子智能体互审。开场用 5 个各带 Chrome 浏览器的 agent 跑真实获客 demo。"
draft: false
categories: ["视频精读"]
tags: ["AIAgent", "NickSaraev", "ClaudeCode", "Codex", "Antigravity", "MCP", "AgentSkills", "无代码"]
---

> **目标读者**：想用 AI agent 干实事的人——不限程序员，做自动化、运营、内容、编程都适用
> **这门课的判断**：这是一门**无代码**课。Nick Saraev 开场就说"你不需要任何编程经验，我自己也没有 CS 学位"。它教的不是写 Python，而是**用** Codex / Claude Code / Antigravity 三大 agent 平台，靠提示词架构把它们编排起来。
> **难度**：⭐⭐⭐ | **来源**：Nick Saraev《AI Agents Full Course 2026: Master Agentic AI》（YouTube，约 2 小时）

[YouTube 原片](https://www.youtube.com/watch?v=EsTrWCV0Ph4) ｜ 频道 [@nicksaraev](https://www.youtube.com/@nicksaraev) ｜ 时长约 2 小时 ｜ 494K 观看

---

## 视频信息卡

| 项目 | 内容 |
| ------ | ------ |
| 标题 | AI Agents Full Course 2026: Master Agentic AI (2 Hours) |
| 作者 | Nick Saraev（@nicksaraev；无代码 AI 自动化，Maker School 创始人） |
| 链接 | [youtube.com/watch?v=EsTrWCV0Ph4](https://www.youtube.com/watch?v=EsTrWCV0Ph4) |
| 观看 | 494K |
| 时长 | 约 2 小时 |
| 定位 | 平台无关的通用 agent 课（Codex / Claude Code / Antigravity） |

> **前置说明（据字幕重建，以及一处必须先讲的更正）**：本文据 YouTube 原片英文字幕逐段核对写成（yt-dlp 取字幕后清洗，约 1477 句）。
>
> 得先摆明：本站早期版本把这门课写成了一套 **Python / LangChain / CrewAI 编程课**（`ReActAgent`、`RAGAgent`、`SupervisorAgent` 一堆类），还配了编造的时间戳。核对字幕后确认——**视频里根本没有这些代码**。Nick 开场第一句就是"你不需要任何编程或计算机经验，我自己也没有 CS 学位"。这是一门**无代码**课，教你用三大 agent 平台，而不是手写 agent 框架。本文已据真实内容重建。

## 目录

本文较长（约 2 小时课程的整理），可用页面侧栏的目录（TOC）按章节跳转；只想抓骨架，看第一、三、五三节即可。

---

## 一、这门课到底在讲什么：无代码，且平台无关

先把定位钉死，因为最容易被讲反。Nick Saraev 开场就划了三条边界：

- **不需要编程**。"你不需要任何编程或已有的计算机经验……我自己也没有正规的计算机科学学位，我会的一切都是看免费资源学的。"
- **平台无关**。"这不只是讲 Codex、Claude Code 或 Antigravity，而是讲它们全部。"三个平台随便从哪个入手，终点一样。
- **讲别人没讲过的**。他自称"到目前为止我没在 YouTube 上看到有人讲我这门课里的大部分东西"，管这叫 "the sauce"（干货）。

他的底层判断很清醒，也是全片地基：**当前的 AI agent，单看智能未必比人强，一次做对的能力也比人差；它们真正的强项是并行**。同一个任务，你可以同时开很多个 agent 实例、各试各的路子，一遍遍地试，靠速度和数量堆出比人更好的结果。所以这门课的重点不是"把某个 agent 调得多聪明"，而是**怎么用提示词架构把多个 agent 编排起来**。

（他本人的背景也说明取向：教了 2000+ 人、用 AI agent 跑着一门年入 400 万美元的生意——是把 agent 用来干经济价值活的实战派，不是研究派。）

## 二、开场 demo：5 个各带浏览器的 agent 同时干活

课程一上来就甩了个"几个月前还会被当成天方夜谭"的 demo，把目标先摆出来。

场景是获客。他手上有一批会议来的 leads——有网站、LinkedIn、名字，**唯独缺邮箱**。搁一年前这批线索基本作废。现在，他让 Claude Code **同时开出一堆 Chrome 浏览器**，每个浏览器里一个子 agent，各自去一个网站，动态找到联系表单、填名字/邮箱、再写一段"模板但会随对象微调"的外联话术。这些 agent 之间还通过一个**共享聊天室**互通消息、分工。原本一个 agent 要干好几小时的活，一群 agent 并行几分钟铺完。

这个 demo 就是全片的"目标态"：**把工作拆散到多个浏览器实例、每个子 agent 一块独立工作区**。后面两小时讲的所有技巧，都是为了搭出这种编排。

---

---

## 三、核心：每个 agent 都在跑的三步循环

Nick 说，先别管平台，所有 agent 骨子里都在跑同一个循环，由三步组成——这是全片会反复回来的地基：

1. **观察（Observe）**：读进所有上下文——文件、之前的工具调用、系统提示、你给的 agents.md / claude.md / gemini.md、上一步的联网 research，乃至多模态数据（图像、音频）。
2. **思考（Think / Reason）**：基于全部上下文和你的高层目标，想"下一步做什么、怎么规划"。现在主流平台都有一个**可点开的推理步骤**——Nick 特别强调这点被很多人低估，因为它带来可解释性、可问责性和**可操控性**（你能中途看它在想什么、叫停、或者塞新资源进去）。
3. **行动（Act）**：调用工具、编辑文件、或者跑一条命令行（CLI）。

行动拿到结果后，把结果**喂回观察步**，循环再来一遍——每转一圈，上下文就更大一点。转个三四圈，模型会撞到一个 Nick 认为大多数人漏掉、"所以老是对 agent 失望"的东西——**完成的定义（definition of done）**：一组约束和技术规格，告诉模型"到此可以不用再循环了"。一旦满足，它就切到"任务完成"路线，吐一段格式化的最终回答。

Nick 反复敲一句话：这三步**每一步都能往死里优化**——观察能优化、思考能优化、行动也能优化，这门课就是教这个。

---

## 四、agent 不等于那个大模型

第二个地基判断：**agent ≠ LLM**。大模型只是里面的推理引擎，负责理解语言、做决策；但它就像两万年前一个手里攥着长矛的人——没有房子、火堆、社会分工、车这些"周边基础设施"，光有智能，能干的事很有限。

给 agent 装上"基础设施"，它才成其为 agent：

- **工具**：像人一样能读文件、跑代码、搜网页、调 API、改文件。
- **推理循环**：就是上一节那个 observe → think → act。
- **记忆**：agents.md / claude.md / gemini.md、对话历史、自动记忆文件、以及 skills。

所以"chatbot vs agent"的区别很干脆：chatbot 大致就是那个 LLM；agent 是 LLM **再加上**工具、推理循环和记忆。Nick 现场用 Codex 演示了一遍这个循环——让它研究"男性肌酸补充"，并给了个明确的完成定义："凑够 10+ 篇实证来源就返回一份结构化报告"。模型于是 观察 →（"用户要研究，我有联网工具"）思考 → 行动（搜索、汇编）→ 再观察，循环两三圈，58 秒后交出结构化证据报告。

---

## 五、三大平台：各自最擅长什么、最差什么

课程真正动手的部分，是带你注册并跑通三大 agent 平台，各自搭一个"给 Nick 做个人主页"的小 demo。Nick 反复强调一句克制的话：**这三家的智能差距其实很小（2%–5%），都在整个互联网上训练，能力差异更多是"谁训练得更晚"，而且每代都会重置——你完全可以只挑一个用**。但如果要区分，各有脾气：

| 平台（模型） | 归属 | 最擅长 | 短板 |
| ------ | ------ | ------ | ------ |
| **Codex**（GPT-5.4 系） | OpenAI | 后端编程、数学、测试驱动开发（给完成定义就自主跑到底）；生态和文档最全（最早入场） | 可解释性一般 |
| **Claude Code** | Anthropic | **推理最可解释**、最适合编排与 agentic 工作流（能实时看 / 叫停 / 操控）、质量稳定；像个"搭档" | 慢（除非 fast 模式，很烧额度）；前端 / 设计偏弱 |
| **Antigravity**（Gemini 3.1 Pro） | Google | **前端 / 设计最强**、多模态最强（能理解视频）、出字快 | 最不可解释、质量不稳定（"有些天直接拉胯"）；像"导弹"，指个目标就发射 |

Nick 的用法：要干净前端找 Gemini，要可控编排找 Claude，要后端 / 数学 / TDD 找 Codex。收费上他点了一句：Claude Code 要付费（约 $17–20/月），但他自己"在 agent 平台上拿到过 100–200 倍回报"，建议真想学就先付了、第一个月想办法把钱赚回来。

> 一句必须转述的话：他也承认在自己的 design-taste 技能加持下，Gemini 出的站最"性感"、GPT 出的偏"笨重"。但他一再强调别把这些 2%–5% 的差异太当真——"它们就是在整个互联网上训练的星系级大脑，差异更多来自训练时间的新旧"。

---

## 六、agents.md：会自我进化的系统提示词

这是 Nick 眼里"高投产比"的头号设计模式。每个平台都有一个会被**自动拼到每次对话最前面**的文件——Codex 叫 `agents.md`、Claude Code 叫 `claude.md`、Antigravity 叫 `gemini.md`（名字不同，机制一样）。

它真正的威力不在"静态模板一段提示词"，而在把它做成**会自改的元提示词**：让 agent 在你纠正它、或它犯错时，**自动把一条新规则追加到文件底部的"已学规则"区**。Nick 给的格式大致是这样（可直接塞进任何 agents/claude/gemini.md）：

```text
开始任何任务前先读完本文件；文件底部有一个会增长的"已学规则"区。
当用户纠正你、或你犯错时，立刻往"已学规则"区追加一条新规则，
按序号写成祈使句，格式：[类别] 永远/绝不 做 X，因为 Y。

── 已学规则 ──
1. 【前端】绝不默认深色模式，因为用户不喜欢。
```

现场的例子：他让 Antigravity 建个主页，结果给了个漂亮但**深色模式**的站；他说"别再搞深色模式了"，agent 没有只改这次，而是把"绝不做深色模式（用户偏好）"写进了 `gemini.md`。**下次再建站，这条规则已经在提示词最顶上，它再也不会犯**。规则越攒越多，agent 犯的"不合你偏好"的错就越来越少——第五次可能几乎归零。

层级也讲清了：最顶上是**全局** agents/claude/gemini.md（对所有项目生效，Claude 存在 `~/.claude/`），然后拼**本地项目**的 .md，再往下是 **skills**，最后才是你这次的行内提示词。好处是把一大堆上下文和功能**压进很少的 token**——这很关键，因为账单按 token 算，而且上下文越长、模型质量越容易掉。

---

## 七、Agent Skills：把工作流标准化成一段规程

Skill 是把大模型的"灵活 / 发散"收成"确定性直线"的办法——同一个任务每次都照同一套标准操作规程（SOP）来做。三家都支持（Codex skills、Gemini skills、Claude Code skills），规格几乎一样：一个带 `---` frontmatter 的文件，里头写 name、description，可选 tools / license / metadata。Nick 说他自己通常只写 name + description + 偶尔几个可用工具。

他拿 Anthropic 官方的 "algorithmic art"（算法艺术）skill 现场演示：把整个 skill.md 喂进模型、存成 skill 再 run，模型就照着规程生成了一批粒子算法艺术，还能实时调粒子数、噪声、湍流。要点是——**skill 让"同一件事每次都做得一样"**，并把一大段上下文折进很少的 token。

---

## 八、进阶：用提示词架构编排多个 agent

课程后半程是 Nick 说"YouTube 上没人讲过"的那部分——**都是用提示词编排多个 agent，不涉及写框架**。列一下他覆盖的技巧：

- **自改指令**（第六节已详述）：agent 改写自己的规则来减少犯错。
- **多智能体 MCP 编排**：把 Codex、Gemini、Claude 都**注册成 MCP 服务器**，在一个对话线程里同时调度多个 agent。
- **视频转动作（video-to-action）**：让 agent 从 YouTube 视频里学，而不只从纯文本学。
- **随机化多智能体共识**：用同一条提示词开出多个 agent，用它们结果的**统计离散度**来做创意发散和改进。
- **智能体聊天室**：给一群 agent 一个集中辩论的地方，互相怼着把答案质量顶上去。
- **子智能体互审回路**：让 agent **实时互相 review 对方的产出**，抓一个 agent 可能漏掉的问题。
- **提示词契约与反向提示**：约束输出格式、让模型反过来帮你补提示；收尾讲上下文管理与 token 定价优化。

这些合起来就是开场那个"5 个浏览器 agent 并行获客"demo 背后的东西：**单个 agent 没那么强，但把一群 agent 用提示词架构编排起来（分工、辩论、互审、共识），整体质量就上一个台阶**。

---

## 九、常见误读：这门课不是在教什么

本站早期版本据"内容地图"综合推理，把这门课写成了编程课，几处走样对着字幕更正：

- **误读一：这是一门 Python / LangChain / CrewAI 编程课**（写 `ReActAgent`、`AgentMemory`、`RAGAgent`、`SupervisorAgent` 等类）。全错。Nick 开场原话是"**你不需要任何编程**"，这是无代码课，教**用** Codex / Claude Code / Antigravity，不写 agent 框架代码。视频里没有这些 Python 类。
- **误读二：课程分"ReAct→Tool Use→Memory→Multi-Agent→生产部署"五部分，各有精确时间戳。** 这个大纲和时间戳是编的。真实主线是：无代码定位 + 开场 demo → observe/think/act 循环 → 三大平台对比 → self-modifying agents.md → skills → 一串"用提示词编排多 agent"的进阶技巧。
- **误读三：把"记忆"讲成短期 / 工作 / 长期 + 向量数据库 + 知识图谱。** 视频里的"记忆"就是 agents.md / claude.md / gemini.md、对话历史、自动记忆文件和 skills，不是向量库那一套。
- **误读四：Multi-Agent 讲的是 Supervisor / Crew 代码模式。** 视频讲的是 MCP 编排、智能体聊天室、子智能体互审、随机化共识——全是提示词层面的编排，不是 CrewAI 代码。

---

## 十、给不同读者的建议

**想用 agent 干活的非程序员**：这门课就是给你的。别被"agent"吓到——先挑一个平台（Nick 说随便挑，差距很小），把第三节那个 observe → think → act 循环记住，然后重点练一件事：给任务写清楚**完成的定义**。很多人对 agent 失望，排查下来往往就是没写清"做到什么算完"。

**做自动化 / 获客 / 运营的**：直接学第六节的 **self-modifying agents.md**——这是投产比最高的一招，让 agent 越用越懂你的偏好。再往上，开场那个"多浏览器并行"是靠把任务拆散 + 子 agent 各自工作区 + 共享聊天室实现的。

**程序员**：这门课的价值不在代码（它没代码），在**编排思路**——MCP 把多个 agent 注册成服务、子 agent 互审、随机化共识。把这些当提示词架构的模式库看。

**不适合谁**：想要现成 Python / LangChain agent 框架代码的人——这门课不给代码，给的是"怎么用现成平台把 agent 编排起来"的方法。

---

## 十一、资源与参考

- 视频原片：[Nick Saraev《AI Agents Full Course 2026》(YouTube EsTrWCV0Ph4)](https://www.youtube.com/watch?v=EsTrWCV0Ph4)
- 作者与社区：[Nick Saraev 个人站](https://nicksaraev.com/)（无代码 AI 自动化）／ [Maker School](https://www.skool.com/makerschool)
- 三大平台官方入口：OpenAI Codex、[Anthropic Claude Code](https://www.anthropic.com/)、Google Antigravity
- **进阶阅读**（站内相关）：[AI Agent 概念讲清楚（Jeff Su）]({{< relref "ai-agents-clearly-explained-jeff-su-4m-views.md" >}}) ／ [25 分钟从零到 Agent]({{< relref "zero-to-ai-agent-25-minutes-futurepedia-3m-views.md" >}})

---

## 十二、自测：你抓住这门课的真实定位了吗

1. 这门课要不要写代码？它教的是"写 agent 框架"还是"用 agent 平台"？（第一节）
2. observe → think → act 循环里，最多人漏掉、导致对 agent 失望的是哪一步？为什么它重要？（第三节）
3. 三大平台里，要干净前端、要可控编排、要后端 / TDD，各该找谁？（第五节）
4. self-modifying agents.md 为什么能让 agent 越用越少犯错？（第六节）

---

## 写作笔记（给后续读者）

- **信息来源**：YouTube 原片英文自动字幕（yt-dlp + chrome cookie 取字幕后清洗成约 1477 句，逐段核对）。所有引号内的话为字幕转译。

- **这一版（v2）做的最重要一件事，是把编造的编程课换回真实的无代码课**：删掉了视频里根本不存在的 Python / LangChain / CrewAI 代码（ReActAgent / WebSearchTool / AgentMemory / RAGAgent / SupervisorAgent / OptimizedAgent / MonitoredAgent）和编造的"五部分 + 时间戳"大纲；换成真实主线——无代码定位、5 浏览器 demo、observe/think/act 循环 + 完成的定义、三大平台（Codex / Claude Code / Antigravity）最擅长 / 最差、self-modifying agents.md、skills、MCP 编排 / 互审 / 共识等进阶技巧。

- **顺带落实的出处**：视频 = YouTube EsTrWCV0Ph4（494K 观看）；作者 Nick Saraev 是无代码 AI 自动化博主（@nicksaraev / Maker School），非程序员。

- **仍要知道的边界**：用的是自动字幕，个别专有名词 / 数字可能有听写误差（如 GPT 版本号"5.4"、Claude Code 价格"$17–20/月"按字幕如实转录）；进阶技巧一节按 Nick 的课程路线图概述，未逐一展开每个技巧的完整演示。

— 钳岳星君 2026-07-13（v2：据 YouTube 字幕重建 / 删除编造的 Python 编程课 / 还原无代码定位与三大平台 / 补 observe-think-act 循环与 self-modifying agents.md）
