---
title: "awesome-generative-ai-guide 导读：一份可以当课表的 GenAI 资源中心"
date: "2026-08-30T10:00:00+08:00"
slug: "awesome-generative-ai-guide-resource-hub"
github_repo: "aishwaryanr/awesome-generative-ai-guide"
description: "aishwaryanr/awesome-generative-ai-guide 在 2026 年 7 月重构为旅程导航：Use AI / Build AI / Understand AI 三条路径配 101/201/301 三档，另有角色化面试中心、90+ 免费课清单与月度论文榜。本文拆解它的新结构、适合人群与使用边界。"
draft: false
categories: ["技术笔记"]
tags: ["GenAI", "LLM", "课程"]
---

# awesome-generative-ai-guide 导读：一份可以当课表的 GenAI 资源中心

[aishwaryanr/awesome-generative-ai-guide](https://github.com/aishwaryanr/awesome-generative-ai-guide) 是 GitHub 上星标接近 3 万的 GenAI 资源仓库。它跟常见的 `awesome-xxx` 链接清单不一样：不满足于把一堆链接按分类排好，而是同时维护着课程、面试题、论文榜和路线图。2026 年 7 月它做了一次大重构，把内容从「按资源类型堆放」改成「按你要做什么进门」。这篇文章讲清楚重构后的结构、它适合谁、以及怎么用。

## 快速信息卡

| 项目 | 信息 |
|------|------|
| **仓库地址** | [aishwaryanr/awesome-generative-ai-guide](https://github.com/aishwaryanr/awesome-generative-ai-guide) |
| **Stars** | ≈29k（截至 2026-08） |
| **Forks** | ≈6k（截至 2026-08） |
| **许可证** | MIT |
| **维护者** | Aishwarya Naresh Reganti（LevelUp Labs 团队） |
| **最近更新** | 2026-08（重构后仍在持续刷新） |

## 一条主线：按「你要做什么」进门

仓库 README 的第一屏不是目录，而是一个选择：

- 🧑‍💻 **我想在工作中用 AI** → `journeys/use.md`
- 🏗️ **我想构建 AI 系统** → `journeys/build.md`
- 🔬 **我想读懂研究** → `journeys/understand.md`
- 💬 **我在准备面试** → `interview_prep/README.md`
- 📚 **我只想翻翻免费课** → `courses.md`
- 📺 **我更喜欢看视频** → `youtube/README.md`

这就是 2026 年 7 月重构的核心：不再问「这份资源属于哪个分类」，而是问「你是谁、想走到哪」。每条旅程内部再按深度分三档——101 入门、201 进阶、301 高级——并配一张「旅程 × 档位」矩阵。

| 旅程 | 101 入门 | 201 进阶 | 301 高级 |
|------|---------|---------|---------|
| **Use AI** | LLM 是什么、提示词基础、用好对话工具 | 高阶提示、连接工具、工作中的 Agent | 个人自动化、多步 Agent 工作流 |
| **Build AI** | 够用的 LLM 原理、应用技术栈、第一个 LLM 应用 | RAG、Agent、评测、微调、护栏 | LLMOps、生产规模、系统设计 |
| **Understand AI** | Transformer、关键论文、怎么读论文 | 推理、Agent、RAG、评测等活跃方向 | 月度论文榜、研究活表、State of AI |

README 里写得很直白：**Build AI 是旗舰旅程，也是最深的一条。** 之前那张「90+ 门免费课」长清单，已经按档位和主题重新编排进这张矩阵。想按主题直跳，还有九张主题页：LLM 基础、提示与上下文、RAG、微调、Agent、评测与可观测、多模态、生产与 LLMOps、安全与护栏。

## 仓库结构（2026-07 重构后）

```text
awesome-generative-ai-guide/
├── journeys/                          # 三条主旅程
│   ├── use.md                         # Use AI：在工作中用 AI
│   ├── build.md                       # Build AI：构建 AI 系统（旗舰，最深）
│   └── understand.md                  # Understand AI：读懂研究
├── topics/                            # 按主题聚合的索引（9 张）
│   ├── foundations.md  ├── prompting.md  ├── rag.md
│   ├── fine-tuning.md  ├── agents.md    ├── evaluation.md
│   ├── multimodal.md  ├── production.md └── safety-security.md
├── free_courses/                      # LevelUp Labs 原创免费课
│   ├── ai_evals_for_everyone/         # 10 章，认证
│   ├── openclaw_mastery_for_everyone/ # 10 天，认证
│   ├── agentic_ai_crash_course/       # 10 部分：Agent / 工具 / RAG / MCP
│   ├── generative_ai_genius/          # 无数学的入门
│   └── Applied_LLMs_Mastery_2024/     # 11 周基础课（已归档 2024 版）
├── courses.md                         # 90+ 门免费课，按主题排列
├── interview_prep/                    # 角色化面试中心
│   ├── README.md
│   ├── 60_gen_ai_questions.md         # 所有人先过的共用题库
│   └── roles/
│       ├── ai-engineer/
│       ├── ai-product-manager/
│       ├── forward-deployed-engineer/
│       └── ai-strategist/
├── research_updates/                  # 研究更新
│   ├── 2024_papers/ 2025_papers/ 2026_papers/   # 月度论文榜按年份归档
│   ├── state_of_ai_2025_report/       # 年度报告
│   ├── rag_research_table.md          # 活表：RAG
│   ├── ai_evaluation_2025_table.md    # 活表：AI 评测
│   ├── agentic_search_retrieval_table.md  # 活表：Agentic 搜索与检索
│   └── survey_papers.md               # 综述论文
├── resources/                         # 工具清单、术语表、外部资源
│   ├── our_favourite_ai_tools.md
│   └── llm_lingo/                     # 6 部分术语表
├── youtube/                           # 视频转写与配套资料
├── LICENSE.md                         # MIT
└── README.md                          # 入口：旅程矩阵 + 主题索引
```

## 五类资源，各自解决什么问题

重构之后，仓库里的资源大致归成五类，更新频率和用途各不相同。

| 资源 | 更新频率 | 主要载体 | 解决的问题 | 不解决的问题 |
| --- | --- | --- | --- | --- |
| 旅程 + 主题页 | 随内容持续更新 | `journeys/`、`topics/` | 按目标给出一条分档路径 | 只是导航骨架，内容仍落在课程与论文里 |
| LevelUp Labs 原创课 | 发布后归档 | `free_courses/` | 免费系统课程，两门带证书 | 除认证课外不发证书；Applied LLMs 停在 2024 版 |
| 90+ 外部免费课 | 低频 | `courses.md` | 全网免费课按主题汇总 | 第三方链接可能失效 |
| 面试中心 | 低频 | `interview_prep/` | 按角色端到端准备 | 系统设计题还在规划中 |
| 研究更新 | 月度 + 活表持续维护 | `research_updates/` | 论文榜、专题活表、年度报告 | 只给线索，不给论文精读 |

## 适合谁用

- **零基础想入门 LLM 的开发者**：从 `journeys/build.md` 的 101 段进，配套 `topics/foundations.md` 和 `topics/prompting.md` 补细节。
- **不想付 Coursera / DeepLearning.AI 学费的系统学习者**：LevelUp Labs 五门原创课全免费，AI Evals for Everyone 和 OpenClaw Mastery for Everyone 还带证书，可挂 LinkedIn。
- **准备 GenAI 岗位面试的人**：面试中心按角色拆好（AI Engineer、AI Product Manager、Forward-Deployed Engineer、AI Strategist），先过 60 道共用题再进角色文件夹。
- **想跟研究节奏的人**：月度论文榜 + 四张专题活表，替代手动刷 arXiv。
- **团队内训负责人**：直接 fork，按旅程矩阵重排内部材料。

## 任务流案例：两周从零入门 RAG

假设你是一个有后端经验、但没碰过 RAG 的工程师，想用两周时间搭出一个能跑的 RAG demo。重构后的仓库给你一条清晰的串联路径。

**第 1–2 天：先看地图，不急着动手。** 打开 `journeys/build.md`，找到 101 段里关于 RAG 的部分，再点进 `topics/rag.md` 主题页。主题页会把这条路上所有相关资源聚在一起，你不需要自己在课程、论文、代码之间来回翻。读完你应该能说出 RAG 的四个环节——检索、嵌入、重排、生成——各是什么，但还没写代码。

**第 3–7 天：课程补原理，代码跑通。** RAG 细节在两条线上都有：`free_courses/Applied_LLMs_Mastery_2024/` 的第 4 周（RAG）和第 5 周（LLM 应用工具）讲得最系统，虽然课程已归档为 2024 版，但 RAG 基础流程不过时；`free_courses/agentic_ai_crash_course/` 里也有 RAG 与工具相关章节，更新一些。课程配套的 Notion 页和 GitHub 代码同步存在，Notion 读原理、仓库跑代码。

**第 8–10 天：面试题查漏。** 进 `interview_prep/roles/ai-engineer/`，先做 `interview_prep/60_gen_ai_questions.md` 里 RAG 相关的题（召回评估、chunk 策略、上下文窗口）。能答出来的跳过，答不出来的回主题页补。面试中心的题带答案，适合当自测工具。

**第 11–14 天：论文榜补趋势。** 打开 `research_updates/2026_papers/` 看最近几个月的论文，再翻 `research_updates/rag_research_table.md` 活表，挑 3–5 篇读 abstract 和 intro。课程是 2024 年的，论文活表能补上 long-context 对 RAG 的冲击、Agentic RAG 这类新方向。

这条路径的顺序是：地图 → 原理 → 查漏 → 趋势。换学习目标时顺序不变，只替换对应的旅程和主题页。

## 进阶路径

**从论文榜到论文精读**：论文榜只给标题和摘要，深度阅读要回到 arXiv 原文。从 `2026_papers/` 挑 3 篇，按「动机 → 方法 → 实验 → 局限」四段拆解，每篇写一页笔记。

**从面试题到系统设计**：面试中心明确标注「系统设计题在后续建设阶段」，这道短板要自己补。可以自己设计一个「百万级文档的 RAG 系统」，画出检索、嵌入、重排、生成四环的选型与延迟成本估算，再对照公开工程博客查漏。

**从免费课到付费直播课**：免费课跟完还想要项目制训练的话，Aishwarya 与 Kiriti 在 Maven 上开直播小班课（AI System Design、Advanced AI Evals），累计 3000+ 学员。这是原创课之外的付费选项，按需选择。

## 适用边界

**适合**：想用一份仓库当 GenAI 学习中枢的人；预算为零、能投入 5–10 周的初学者；要准备 GenAI 岗位面试的求职者。

**不适合**：想读最前沿架构细节的资深研究员——它偏应用与入门；也替代不了真实的项目经验和系统设计训练。

几个注意点：

- 原创课里 Applied LLMs Mastery 是 2024 年版，已标注归档，工具链部分（LangChain 版本、API 调用）要以官方当前文档为准。
- `courses.md` 的 90+ 门外部课链接来自社区，个别可能失效。
- 面试中心的系统设计题尚未上线，深度面试需另找材料。
- 免费课免费，但 Maven 直播小班课和部分外部课程收费，看清楚再点。

## 常见问题

**为什么有 journeys / topics 一堆目录？**
2026 年 7 月仓库从「按资源类型堆放」重构为「按目标导航」。journeys 回答「你是谁、想走到哪」，topics 回答「我想直接看某个主题」。骨架变复杂，但入口反而变少——README 第一屏就是选择。

**Applied LLMs Mastery 是 2024 年的，还值得跟吗？**
原理部分（Transformer、注意力、RAG 基础流程、Eval 方法论）仍然有效，仓库也把它标注为「归档 2024 版」。工具链部分以官方当前文档为准。想要更新的内容，优先看 Agentic AI Crash Course 和 AI Evals for Everyone。

**免费课真的免费？证书是怎么回事？**
LevelUp Labs 原创课免费，AI Evals for Everyone 和 OpenClaw Mastery for Everyone 通过后发证书，可挂 LinkedIn。Maven 上的直播小班课收费。外部课链接免费，但由第三方托管，规则以对方为准。

**面试中心只有 AI Engineer 吗？**
目前四个角色：AI Engineer、AI Product Manager、Forward-Deployed Engineer、AI Strategist。所有人都先共用 60 道题，再进自己的角色文件夹。

**fork 做内训，许可证有坑吗？**
仓库本身是 MIT，可以 fork 和修改。但 `courses.md` 里链接的第三方课程与资源版权不在 MIT 范围内，需要单独确认。

**论文榜是不是停更了？**
没有，只是换了地方：月度论文榜从 README 挪进 `research_updates/`，按年份分文件夹（2024/2025/2026），另外还有 RAG、AI 评测、Agentic 搜索与检索三张活表在持续维护。看最新的去那里，README 只留入口。

## 采用顺序

按投入时间分四档：

- **入门档（1–2 周）**：`journeys/build.md` 101 段 + 一张相关主题页，最后用 60 道题自查。
- **系统档（5–10 周）**：挑一门原创课按周/章跟完，配套代码跑通，期间每月扫一次论文榜。
- **面试档（2–4 周）**：进自己岗位的角色文件夹端到端走一遍，先过共用题。
- **团队档**：fork 后按旅程矩阵重排内部材料，替换成自己的技术栈与案例，注意第三方资源许可证。

仓库的强项是路径清晰：旅程给方向，主题页给聚合，课程给系统知识，面试中心给自查，研究更新给趋势。弱项是时效与深度——课程定格在发布时的技术栈，深度阅读仍要回到 arXiv 原文和官方文档。
