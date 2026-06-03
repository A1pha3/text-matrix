---
title: "Datawhale/easy-vibe：一套把想法落成产品的 Vibe Coding 开源课程"
date: "2026-05-10T16:55:00+08:00"
slug: "datawhale-easy-vibe-vibe-coding-course-guide"
description: "easy-vibe 是 DatawhaleChina 维护的 Vibe Coding 开源课程，围绕从想法、原型、全栈上线到工程化 AI 协作，构建出一条 3 + 1 的学习路径。本文结合 README、中文 README 与 llms.txt，梳理它真正适合谁、每个阶段解决什么问题，以及为什么它不只是一个教程仓库。"
summary: "这篇文章基于 easy-vibe 的 README、中文 README 和 llms.txt，重新梳理这套课程的 3 + 1 学习结构、适用人群、代表内容、OpenClaw 与 llms.txt 的位置，以及它为什么比普通的 AI 编程入门教程更完整。"
draft: false
categories: ["技术笔记"]
tags: ["Vibe Coding", "Datawhale", "AI Agent", "OpenClaw", "Claude Code", "教程指南"]
---

<!-- markdownlint-disable-file MD003 MD041 -->

## 读完你会

- 用一句话讲清楚 easy-vibe 的 3+1 课程结构，以及每个阶段在解决什么问题。
- 根据自己当前的背景，找到最适合的课程入口（Stage 1、Stage 2、Stage 3 或附录知识库）。
- 举出一个从想法到原型的真实学习路径，说明课程在不同阶段提供了什么支持。
- 判断 easy-vibe 和 hello-claw 分别适合什么场景，避免走错入口。

## 项目概览

如果把 easy-vibe 只看成一个“AI 编程入门仓库”，很容易低估它。它真正做的，不是把一堆提示词、工具截图和零散 Demo 堆在一起，而是把“想法出现”“原型落地”“产品上线”“工程化协作”连成一条连续路径。对零基础读者来说，它降低的是第一步的心理门槛；对已经会写代码的人来说，它补的是 AI 协作开发的方法和完整交付链路。

以下内容基于 easy-vibe 的 README、中文 README 和仓库根目录 llms.txt 整理，统计口径截至 2026 年 5 月 10 日。

| 项目 | 信息 |
| ------ | ------ |
| 仓库 | [datawhalechina/easy-vibe](https://github.com/datawhalechina/easy-vibe) |
| 官网 | [datawhalechina.github.io/easy-vibe](https://datawhalechina.github.io/easy-vibe/) |
| GitHub Stars | 8,818 |
| License | CC BY-NC-SA 4.0 |
| 多语言文档 | 10 种语言 |
| 核心口号 | If you can talk, you can build apps. / 会说话就会做应用。 |

官方 README 已提供简体中文、繁體中文、English、日本語、한국어、Español、Français、Deutsch、العربية 和 Tiếng Việt 十种语言入口。对一个面向全球新手的开源课程来说，这不是锦上添花，而是课程真正能扩散出去的基础设施。

easy-vibe 由 DatawhaleChina 社区维护。它的目标不是把你训练成某门语言的"语法题选手"，而是让你学会如何和 AI 一起把一个想法做成产品。这直接决定了课程的组织方式：先做出东西，再在需要的时候理解原理，而不是先把所有基础知识压给你。

easy-vibe 内部有三层结构：纵向的能力阶梯（Stage 1 → Stage 2 → Stage 3）按原型到工程化的难度递进；横向的知识补给（附录知识库）在你卡住时提供原理兜底；再加上 llms.txt 这条给 AI Agent 的导航层。三者共同构成一套同时服务人和 Agent 的学习基础设施。

## 它真正解决的，不是"怎么学语法"

传统编程入门路线常见的断点有三个。第一，很多人刚开始学时并不知道该做什么，于是长期停留在语法和小练习里。第二，能让 AI 生成一个页面的人很多，但能把页面变成完整产品的人不多。第三，已经有经验的开发者知道 AI 能提速，却未必知道怎样把 AI 纳入真实的工程流程。

easy-vibe 恰好对着这三个断点展开。

它把 Vibe Coding 解释成一种新的协作方式：人负责表达目标、筛选方向、判断取舍，AI 负责把想法快速变成看得见、点得动、能继续迭代的产物。这门课并不是在承诺"以后不需要懂技术了"，而是在教你怎样把技术理解和 AI 的执行能力接起来。

## 课程结构：不是资料堆，而是一条 3 + 1 路线

easy-vibe 在 README 和 llms.txt 里都把自己的结构定义得很清楚：它不是四堆互不相关的内容，而是一个 3 + 1 的体系。三个阶段对应不同能力层级，外加一个随取随用的附录知识库。

| 模块 | 目标 | 代表内容 | 你最终拿到什么 |
| ------ | ------ | ------ | ------ |
| Stage 1：新手入门与产品原型 | 建立 AI 编程直觉，先做出第一个可交互作品 | 学习地图、AI IDE、找点子、做原型、集成 AI 能力、完整项目实战 | 一个能展示、能讨论、能继续迭代的原型 |
| Stage 2：初中级开发 | 把原型变成可上线的产品 | UI 设计、组件库、Git、Supabase、API、部署、Stripe、Dify、两套大作业 | 一个具备登录、数据库、计费和部署能力的全栈应用 |
| Stage 3：高级开发 | 进入工程化的 AI 协作和跨平台开发 | Claude Code、MCP、Skills、Agent Teams、Spec Coding、PWA、Electron、移动端、VS Code 扩展 | 更接近生产环境的多平台项目与 AI 开发工作流 |
| 附录知识库 | 随查随用，补足原理和背景知识 | 9 大知识领域、80+ 交互式专题 | 在遇到陌生概念时，能快速补齐上下文 |

这条路线的好处是，它允许不同背景的人从不同入口进入。零基础不必硬啃后端和部署；有经验的开发者也不需要先回头看完所有入门章节，才能进入对自己真正有用的部分。

拿一个具体场景来说：假设你是一个产品经理，手里有一个"帮自由职业者自动生成发票"的想法。你不会写代码，但有这个领域的用户洞察。你的路径会是：Stage 1 的"寻找好想法"帮你把这个念头打磨成可验证的需求假设 → "动手做出原型"让你用 AI 生成第一个可点击的界面 → 附录里的 Double Diamond 和 The Mom Test 帮你在找人试用之前校准方向。验证通过后，Stage 2 的 SaaS 大作业教你接入 Supabase 做数据库、Stripe 做收款，把原型变成能收钱的产品。整个过程里，你不需要先学完任何一门编程语言，每一步该补什么原理，附录知识库就在那里等着。

这条路径在 Vibe Stories 里多个真实案例中都能找到对应——不是只有开发者能从这套内容里获益。

## Stage 1 为什么是 easy-vibe 的核心

很多“面向零基础”的 AI 编程教程，真正的问题不是内容少，而是默认读者已经知道什么算一个好需求、什么算一个可演示的原型、什么算可验证的用户反馈。easy-vibe 的 Stage 1 处理得更完整。

这一阶段的主线包括 [学习地图](https://datawhalechina.github.io/easy-vibe/zh-cn/stage-1/learning-map/)、[AI 时代，会说话就会编程](https://datawhalechina.github.io/easy-vibe/zh-cn/stage-1/ai-capabilities-through-games/)、[认识 AI IDE 工具](https://datawhalechina.github.io/easy-vibe/zh-cn/stage-1/introduction-to-ai-ide/)、[寻找好想法](https://datawhalechina.github.io/easy-vibe/zh-cn/stage-1/finding-great-idea/)、[动手做出原型](https://datawhalechina.github.io/easy-vibe/zh-cn/stage-1/building-prototype/) 和 [完整项目实战](https://datawhalechina.github.io/easy-vibe/zh-cn/stage-1/complete-project-practice/)。

课程先让你体验 AI 编程是什么，再让你理解怎样找到值得做的题目，接着才进入原型、功能、反馈和迭代。对新手来说，这比一上来讲框架、语法、工程目录更有效，因为真正的阻塞点往往不是"不会写"，而是"不知道做什么"和"不知道怎么判断自己做得对不对"。

2026 年 3 月新增的“用户研究与需求验证”附录也很关键。像 [Double Diamond](https://datawhalechina.github.io/easy-vibe/zh-cn/stage-1/appendix-double-diamond/)、[Jobs to Be Done](https://datawhalechina.github.io/easy-vibe/zh-cn/stage-1/appendix-jobs-to-be-done/) 和 [The Mom Test](https://datawhalechina.github.io/easy-vibe/zh-cn/stage-1/appendix-mom-test/) 这些内容，补的不是“怎么让 AI 回答得更好”，而是“怎么避免从一开始就在做错的东西”。这是 easy-vibe 和很多提示词教程最大的差别之一。

## Stage 2 把“能做 Demo”推进到“能上线、能收费、能维护”

Stage 2 是这套课程最实用、也最容易被低估的一部分。它并没有停在“再做几个页面”上，而是把一个真实产品上线所需的链路串了起来。

这一阶段一边讲前端表现力，一边补全产品交付链。你会看到 UI 设计、Design to Code、现代组件库和多产品界面规则，也会看到 Git、数据库、API 设计、云端部署、终端优先的 AI Coding 工具，以及收费系统接入。课程的重点已经从“AI 能帮我生成什么”转到“我怎么把这些结果接成一个完整系统”。

这里最值得看的，是两个大作业。一个是 [第一个 SaaS 全栈应用：AI 文案生成网站](https://datawhalechina.github.io/easy-vibe/zh-cn/stage-2/assignments/copywriting-platform-supabase/)，它把登录、生成、数据库、计费和后台管理串成了一个完整闭环；另一个是在线考试与管理系统，适合想看更复杂业务流的读者。很多教程的问题在于案例做完就结束了，而 easy-vibe 的 Stage 2 已经明显朝“可以继续扩展成真实项目”的方向走。

## Stage 3 真正进入工程化 AI 开发

如果说 Stage 1 教的是“怎么开始”，Stage 2 教的是“怎么把东西做完整”，那么 Stage 3 处理的就是“怎么把 AI 真正纳入开发流程”。

这一阶段的核心已经不再是简单的提示词，而是围绕 Claude Code 展开的工程化能力，包括安装与基础用法、MCP、Skills、Long-Running Tasks、Agent Teams、Spec Coding、工作流最佳实践、移动端远程开发，以及 Claude Agent SDK。它讨论的问题不再是“AI 会不会写代码”，而是“AI 在复杂任务里怎样稳定地持续工作”。

这背后其实是工程方法的变化：怎样组织上下文，怎样把任务切小，怎样用规格先行减少返工，怎样在多 Agent 协作下控制质量，怎样让 AI 不只会补几段代码，而是能参与长期任务。对于已经在用 Claude Code、Cursor 或类似工具的人，这一部分更像一套系统化工作方法，而不只是工具功能介绍。

同一阶段的跨平台章节也很完整，覆盖微信小程序、Android、iOS、PWA、浏览器扩展、Electron、VS Code 扩展和 Qt 工业应用。这说明 easy-vibe 的目标并不是把读者留在单一的 Web 页面，而是让人理解 AI 辅助开发可以延伸到不同交付平台。

## 附录知识库不是补丁，而是这套课程的底盘

easy-vibe 的附录知识库目前覆盖 9 大知识领域、80+ 交互式专题。这个部分很容易被忽略，因为它不像 Stage 1 到 Stage 3 那样有一条清晰主线，但它其实承担了非常重要的作用：把新手和进阶读者都会卡住的原理问题，做成可以按需查阅的可视化材料。

你不需要在一开始就把 Git、终端、RAG、Diffusion、前端基础、后端概念全部学完，才允许自己开始做项目。遇到问题时再回到附录补上下文，更符合真实学习节奏。对很多人来说，这种"边做边补"的组织方式，比传统课程更接近实际工作。

## llms.txt 和 Hello Claw 在整个生态里的位置

OpenClaw 是 easy-vibe 友好的外部生态之一，但不是这门课的唯一核心。

2026 年 3 月，easy-vibe 在仓库根目录新增了 [llms.txt](https://raw.githubusercontent.com/datawhalechina/easy-vibe/main/llms.txt)。这个文件不是普通宣传文案，而是专门写给 AI Agent 的导航说明，里面直接定义了 3 + 1 的课程架构、各阶段关键词和路径建议。当你用 OpenClaw、Claude Code、Cursor、Trae 或其他支持仓库上下文的 Agent 时，AI 不必把整个仓库盲目扫一遍，而是可以先读这份导航，再去更准确的章节里回答问题。

easy-vibe 在这里不只是“人类可读的教程”，也是“Agent 可导航的教程”。对 AI 时代的文档设计来说，这个点很有代表性。

至于 [hello-claw](https://github.com/datawhalechina/hello-claw)，它更像 DatawhaleChina 围绕 OpenClaw 提供的配套课程，适合想把命令行 AI 助手真正搭起来的人。如果你的目标是学会用 AI 做产品，easy-vibe 已经足够；如果你的目标是继续深入到 AI Agent 工具链，hello-claw 才是自然的下一站。

## Vibe Stories 为什么重要

很多开源教程会展示成品，却很少展示“不同背景的人是怎样把这些内容真正用起来的”。easy-vibe 的 [Vibe Stories](https://datawhalechina.github.io/easy-vibe/zh-cn/vibe-stories/story-1.html) 板块补上了这一点。

目前公开的真实案例包括乡村小学老师、大学生、高中信息技术老师和货车司机。这个板块的价值，不只是“故事励志”，而是它把课程的可迁移性展示出来了：不是只有开发者能从这套内容里获益，不同职业、不同技术基础的人都可能用它做出能解决现实问题的东西。对一门主打零门槛和低心理负担的课程来说，这类证据比口号更有说服力。

## 这套教程适合谁，也不太适合谁

如果你属于下面几类人，easy-vibe 很值得投入时间：

- 零基础，但已经有一个明确的小产品想法。
- 产品经理、创业者，想把 MVP 更快做出来。
- 学生或初级开发者，想补齐从原型到上线的完整链路。
- 已经在用 AI 编码工具，但想把工作流做得更工程化的开发者。

如果你想要的是另一类内容，预期就要调整：

- 想系统刷完一门编程语言语法，easy-vibe 不是那种教材。
- 想一次性补完计算机基础、网络、数据库、算法再开始动手，这套课的节奏会显得太“先做后学”。
- 想直接复制现成产品而不理解需求、交互、部署和反馈循环，课程能帮到的也有限。

easy-vibe 最适合那些愿意在做项目的过程中学习，而不是等"全懂了再开始"的人。

## 开始前先回答三个问题

在决定从哪一段开始之前，先问自己三件事。

1. 你现在最缺的是第一份正反馈、一个完整全栈闭环，还是工程化工作流？
2. 你要做的是练习项目，还是准备真的上线并接受用户反馈？
3. 你是否愿意边做边补原理，而不是等全部学完再动手？

官方首页其实已经把入口做成了五种非常直白的选择：我想先试试、我有个想法要实现、我想系统学习、我想构建 AI Agent、我想查资料。这个设计本身就很能说明 easy-vibe 的思路，它不是要求所有人走同一条路，而是先帮你找到当前最合适的入口。

如果你只想先试试 AI 编程是什么感觉，先看 [学习地图](https://datawhalechina.github.io/easy-vibe/zh-cn/stage-1/learning-map/) 和 [AI 时代，会说话就会编程](https://datawhalechina.github.io/easy-vibe/zh-cn/stage-1/ai-capabilities-through-games/)。如果你已经有产品想法，优先走 Stage 1 里的“找点子”“做原型”“完整项目实战”，再进入 Stage 2 的数据库、部署和支付。已经有开发经验的人，可以从 Stage 2 或 [Stage 3](https://datawhalechina.github.io/easy-vibe/zh-cn/stage-3/) 直接开始；如果你关心的是 AI Agent，本体课程之外再接上 hello-claw 会更高效。

## 常见问题 (FAQ)

**Q1: easy-vibe 和传统学编程的课程到底有什么不同？**

传统课程通常按语言语法、数据结构、算法的顺序推进，目标是把你训练成能独立写代码的开发者。easy-vibe 走的是另一条路：它围绕“把想法做成产品”组织内容，先让你用 AI 做出东西获得正反馈，再在需要时回到附录补原理。它不是语法教材的替代品，而是 AI 协作开发的完整路径。

**Q2: 我完全不会写代码，真的能跟上吗？**

能。easy-vibe 的 Stage 1 就是为零基础设计的，它不会假设你已经知道什么是 Git、API 或数据库。你需要准备的是：一个你想做的产品想法、一台能跑 AI IDE（如 Cursor、Trae）的电脑，以及愿意边做边学的耐心。课程里乡村小学老师、货车司机等真实案例（见 Vibe Stories）说明，技术背景不是硬门槛。

**Q3: 学完整个课程大概需要多长时间？**

这取决于你的背景和目标。如果只走 Stage 1 做出一个原型，投入 2-4 周即可。如果走 Stage 1 + Stage 2 做出可上线的全栈应用，一般需要 1-2 个月。Stage 3 的工程化内容更偏工作流优化，可以按需选看。附录知识库不需要通读，在做项目遇到具体问题时查阅即可。

**Q4: easy-vibe 和 hello-claw 是什么关系？我需要两个都学吗？**

hello-claw 是 DatawhaleChina 另一套围绕 OpenClaw（命令行 AI 助手）的配套课程，定位在 AI Agent 工具链的搭建。如果你只是想学会用 AI 做产品，easy-vibe 就够了。如果你想深入配置自己的命令行 AI 助手、理解 Agent 底层机制，再去看 hello-claw。两者互补，但 easy-vibe 是更普适的入口。

**Q5: 学完 easy-vibe 之后，下一步可以往哪个方向走？**

三个方向：一是用学到的能力把你的产品想法真正做出来并上线，这是最直接的验证；二是进入 hello-claw 深入了解 AI Agent 工具链；三是带着课程里积累的项目经验去学习更系统的工程基础（如数据库设计、系统架构），这时你已经有具体的痛点和上下文，学起来会比零基础直接啃书更高效。

## 自测

1. easy-vibe 的 Stage 2 主要解决什么问题？列举 Stage 2 涉及的两项关键技术。
2. llms.txt 在 easy-vibe 中起什么作用？它是写给谁看的？
3. 一个零基础但有明确产品想法的人，推荐按什么顺序学习 easy-vibe 的各个模块？
4. easy-vibe 不适合哪两类学习者？分别说明原因。

## 总结

easy-vibe 值得看的地方，不是它把“Vibe Coding”这个词说得多热闹，而是它把这件事拆成了可以学习、可以跟做、可以迁移的一条路径。Stage 1 解决起步和产品感，Stage 2 解决上线和变现，Stage 3 解决工程化协作，附录知识库负责在你卡住时补齐原理背景。再加上 llms.txt 这种面向 AI Agent 的导航设计，它已经不只是传统意义上的教程仓库，而是一套同时服务人和 Agent 的学习基础设施。

如果你关心的不是“AI 能不能帮我写几行代码”，而是“我怎样更稳定地把一个想法做成产品”，easy-vibe 的确值得花时间系统看一遍。
