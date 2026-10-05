---
title: "InkOS 解析：AI Agent 如何接管一部小说的全生命周期"
date: "2026-05-30T13:30:00+08:00"
lastmod: "2026-09-29T00:00:00+08:00"
slug: "inkos-ai-novel-writing-agent"
github_repo: "Narcooo/inkos"
source_key: "gh:Narcooo/inkos"
description: "Narcooo/inkos 是一个开源长篇小说写作 AI Agent 系统，用十个专业 Agent、37 维度连续性审计、Zod 校验的结构化状态和 SQLite 检索记忆，把长篇写作中的上下文膨胀、状态漂移、AI 味三个问题做成可观察的工程环节。本文以 v1.8.0 为口径拆解其管线设计与适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "多Agent协作", "创意写作"]
---

# InkOS 解析：AI Agent 如何接管一部小说的全生命周期

写长篇时，AI 写作工具普遍栽在三件事上：上下文越塞越满，模型开始"遗忘"前文；角色身上凭空多出一件两章前已经丢掉的武器；行文里高频词和总结腔越积越多。InkOS（[Narcooo/inkos](https://github.com/Narcooo/inkos)）的思路是把这三个问题从"祈祷模型自己撑住"改成工程环节：写作前先编译输入，状态写进带 schema 校验的 JSON，每一章草稿交给一个专门的审计 Agent 对照 37 个维度检查。

它把一章的生产拆给十个各管一段的 Agent，用文件系统做解耦——这也是它和"一个大 Prompt 写完全文"方案最本质的区别。本文以 v1.8.0（2026-08-17 发布，当前最新稳定版）为口径，核实于 2026-09-29；文中引用的项目方自测数据单独注明了出处时点。

## 快速信息卡

| 项目 | 信息 |
|------|------|
| **GitHub** | [Narcooo/inkos](https://github.com/Narcooo/inkos) |
| **Stars** | 10,086（2026-09-29 读数） |
| **Forks** | 1,848 |
| **许可证** | AGPL-3.0 |
| **主要语言** | TypeScript |
| **运行时** | Node.js 22+ |
| **最新稳定版** | v1.8.0（2026-08-17） |
| **安装** | `npm i -g @actalk/inkos` |

## 系统地图：一条管线和十个角色

每一章默认按"规划 → 编排 → 写作 → 审计 → 必要修订 → 状态同步"运行。十个 Agent 的分工：

| Agent | 职责 |
|-------|------|
| **雷达 Radar** | 扫描平台趋势和读者偏好，指导故事方向（可插拔，可跳过） |
| **规划师 Planner** | 读取作者意图、当前焦点和记忆检索结果，产出本章意图（must-keep / must-avoid） |
| **编排师 Composer** | 从结构化状态、控制文档和材料中按任务选择上下文，记录保护层级、检索和语义压缩 trace |
| **建筑师 Architect** | 建书、导入或番外初始化时生成基础设定：故事框架、规则、角色与长期控制文件 |
| **写手 Writer** | 基于编排后的精简上下文生成正文（字数治理 + 对话引导） |
| **观察者 Observer** | 从正文中过度提取 9 类事实（角色、位置、资源、关系、情感、信息、伏笔、时间、物理状态） |
| **反射器 Reflector** | 输出 JSON delta（而非全量 markdown），由代码层做 Zod schema 校验后 immutable 写入 |
| **归一化器 Normalizer** | 仅在正文明显偏离硬性字数区间（hard range）时单 pass 压缩/扩展 |
| **连续性审计员 Auditor** | 对照结构化状态、控制文档和章节上下文验证草稿，执行连续性与质量检查 |
| **修订者 Reviser** | 修复审计发现的关键问题；默认最多自动修订一次，可通过 `writing.reviewRetries` 调整，其他问题标记给人工审核 |

架构上有两点值得先说清。第一，Agent 之间不共享内存状态，一切通过文件传递：正文、状态、意图、上下文都落在 `story/` 目录下，单个 Agent 出错不会污染其他环节的产物。第二，管线里没有"审稿通过就万事大吉"的状态——审计产出的是带证据的 observation（结构化的审查记录），修订是显式动作，仍未解决的问题保留在结果里交给人工。这个设计取向贯穿全项目。

Radar 是可选环节，不在每一章的必经路径上；Architect 只在建书和导入时跑一次。所以日常每一章实际经过的是 Planner 到 Reviser 这条链。

## 一次 `write next` 里发生了什么

把抽象机制落到一个具体命令上。执行 `inkos write next 吞天魔帝` 后：

1. **Planner** 读 `story/author_intent.md`（这本书长期想成为什么）和 `story/current_focus.md`（最近 1-3 章要把注意力拉回哪里），结合记忆检索结果，生成 `story/runtime/chapter-XXXX.intent.md`——本章的 must-keep、must-avoid 和冲突处理建议。
2. **Composer** 从结构化状态、控制文档和材料库中按本章任务挑选上下文，落盘三个文件：`context.json`（实际选入了什么）、`rule-stack.yaml`（本章规则的优先级层和覆盖关系）、`trace.json`（输入编译轨迹，供调试）。上下文按 protected / compressible 分层——哪些必须原样保留、哪些允许语义压缩——避免长书越写越塞。
3. **Writer** 基于精简上下文写正文。`--words` 指定的是目标字数，系统推导一个允许区间；中文按 `zh_chars` 计数，英文按 `en_words`。超出区间最多追加一次纠偏归一化（压缩或补足），不会硬截断；一次纠偏后仍超出 hard range 的章节照常保存，在结果和章节索引里留下长度 warning。
4. **Auditor** 对照结构化状态、控制文档和本章上下文，从 37 个维度检查草稿：角色记忆、物资连续性、伏笔回收、大纲偏离、叙事节奏、情感弧线等。
5. 审计发现问题就进入"修订 → 再审计"，默认最多一轮（`inkos config set writing.reviewRetries 3` 可调高）。仍未解决的问题保留在结果和状态里，标记给人工或后续命令。
6. **Observer** 从定稿正文提取 9 类事实，**Reflector** 把它们变成 JSON delta，经 `applyRuntimeStateDelta` 做 immutable 更新、`validateRuntimeState` 做结构校验后写入 `story/state/*.json`，再投影成人类可读的 Markdown。

六个步骤里，模型只负责理解、提议和生成；确认、校验、落盘全部由宿主代码完成。完成态只来自真实文件和工具结果，不采信模型的口头声明。

## 输入治理：控制面与运行时产物

多数同类工具把创作简报、大纲、书级规则和当前指令混在一个 Prompt 里。InkOS 把控制信息拆成多层可独立编辑的文件：

| 文件 | 用途 | 谁写 |
|------|------|------|
| `story/author_intent.md` | 这本书长期想成为什么 | 人类作者 |
| `story/current_focus.md` | 最近 1-3 章要把注意力拉回哪里 | 人类作者 |
| `story/runtime/chapter-XXXX.intent.md` | 本章目标、保留项、避免项、冲突处理 | Planner |
| `story/runtime/chapter-XXXX.context.json` | 本章实际选入的上下文 | Composer |
| `story/runtime/chapter-XXXX.rule-stack.yaml` | 本章优先级层和覆盖关系 | Composer |
| `story/runtime/chapter-XXXX.trace.json` | 本章输入编译轨迹 | Composer |

这套控制面在 `inkos.json` 里对应 `inputGovernanceMode` 配置：默认值 `v2`，即上面这条"先编译、再写作"的链路；`legacy` 作为显式回退保留，对应旧的 Prompt 拼装路径。注意 v2 指的是输入治理模式的代号，不是项目版本号。

规则体系分三层：写手内置约 25 条通用创作规则（人物塑造、叙事技法、逻辑自洽、语言约束、去 AI 味）；每个题材有专属规则（禁忌、语言约束、节奏、审计维度）；每本书还有独立的 `book_rules.md`（主角人设、数值上限、自定义禁令）和 `story_bible.md`（世界观设定）。建书时传 `inkos book create --brief my-ideas.md`，Architect 基于简报生成这些设定，而不是凭空发挥。

## 去 AI 味做在两个环节

InkOS 的去 AI 味不是事后过滤，而是嵌在写作链路里：

- **源头抑制**：去 AI 味规则内置于写手 Agent 的 prompt 层——词汇疲劳词表、禁用句式、文风指纹注入，从生成源头减少 AI 痕迹。配合 `inkos style analyze` 提取参考文本的统计指纹（句长分布、词频特征、节奏模式），`inkos style import` 注入指定书籍后，后续章节自动沿用该风格，修订者也会用风格标准做审计。
- **显式改写**：`revise --mode anti-detect` 对已有章节做专门的反检测改写，不重新生成内容。
- **量化检查**：`inkos detect` 做 AIGC 检测（支持 `--all` 全部章节、`--stats` 统计）；审计里的 AI 痕迹检测维度会标出高频词、句式单调、过度总结等可修订位置，检测结果反馈给 Reviser 决定是否需要更多轮修订。

三者的分工是：源头少产生，存量可定向修复，结果可度量。

## 连续性审计与真相文件

审计员对照的基准是三层记忆，权威和投影分得很清楚：

| 层 | 用途 |
|----|------|
| `story/state/*.json` | 权威结构化状态：当前状态、伏笔、章节摘要等，写入前过 Zod schema 校验 |
| `story/*.md` | 人类可读投影，可直接阅读和修改 |
| `story/memory.db` | Node 22+ 自动启用的 SQLite 时序记忆库，用于相关事实、伏笔和摘要检索 |

Markdown 投影在 v1.4.x 文档里枚举过完整清单，共 7 个文件（当前 README 列举了其中 4 个）：

| 文件 | 用途 |
|------|------|
| `current_state.md` | 世界状态：角色位置、关系网络、已知信息、情感弧线（必需） |
| `pending_hooks.md` | 未闭合伏笔：铺垫、对读者的承诺、未解决冲突（必需） |
| `chapter_summaries.md` | 各章摘要：出场人物、关键事件、状态变化、伏笔动态 |
| `particle_ledger.md` | 资源账本：物品、金钱、物资数量及衰减追踪（无数值体系的题材可没有它） |
| `subplot_board.md` | 支线进度板：A/B/C 线状态、停滞检测 |
| `emotional_arcs.md` | 情感弧线：按角色追踪情绪变化和成长 |
| `character_matrix.md` | 角色交互矩阵：相遇记录、信息边界 |

"必需/可选"来自源码：`state/manager.ts` 里 `current_state.md` 和 `pending_hooks.md` 在必需清单里，`particle_ledger.md` 注释明确写着无数值体系（`numericalSystem=false`）的题材可以没有。审计员就是拿这些状态对照草稿——角色"记起"了从未亲眼见过的事，或拿出了两章前已经丢失的武器，都会被捕捉。

状态写入的可靠性是硬约束：伏笔系统的 `lastAdvancedChapter` 必须是整数，`status` 只能取 open / progressing / deferred / resolved 四值。LLM 输出的 JSON delta 在写入前经过 immutable 更新加结构校验，坏数据直接拒绝，不会滚雪球。

这套结构化状态是从 v0.6.0（2026-03-26）开始引入的：权威来源从 Markdown 迁到 `story/state/*.json`，Settler（状态结算环节）不再输出完整 Markdown，改输出 JSON delta。旧书首次运行时自动迁移，Markdown 保留为投影。

## SQLite 时序记忆：给检索设上限

长篇写到几十万字后，把所有历史塞进上下文既贵又容易淹没近期细节。Node 22+ 环境下，InkOS 自动启用 `story/memory.db`，按相关性检索历史事实、伏笔和章节摘要，而不是全量注入。

v1.8.0 把检索统一成一套本地投影：故事记忆、材料库和 Skill 参考资料共用 SQLite FTS5 / BM25 检索，原始文件仍是权威来源，索引可重建，检索结果保留来源与位置。这套设计的边界也要说清：记忆库是可重建的检索投影，不作为故事事实的权威——删掉它不丢事实，重建即可。

## 四种使用模式

v1.8.0 提供 Studio Chat、TUI、CLI 三种交互形态，底层按四种使用模式组织，共享同一组原子操作：

**完整管线（一键式）**：`inkos write next 吞天魔帝`，走 plan → compose → write → 审计 → 按配置修订的完整链路，`--count 5` 连写五章。适合已经建好书、配好模型、想让它自动跑下去的场景。

**原子命令（可组合）**：`inkos plan chapter`、`inkos compose chapter`、`inkos draft`、`inkos audit`、`inkos revise` 各自独立执行单一操作，全部支持 `--json`。`plan` 调用 LLM 生成章节意图；`compose` 只编译本地文档和状态，不要求在线 LLM，可以在配好 API Key 之前先检查输入治理的结果。外部 AI Agent 可以通过 `exec` 调这组命令做脚本编排。

**自然语言 Agent 模式**：`inkos agent "帮我写一本都市修仙，主角是个程序员"`。v1.4.x 时代这一模式暴露固定的 18 个工具（write_draft、plan_chapter、scan_market、create_book 等）；v1.8.0 重构后改为按场景收窄的 action 面——建书、短篇、同人、Play、剧本、分镜、翻译、封面等能力按当前会话类型开放，完成态同样只来自工具结果和落盘文件。

**Studio Play 模式**：v1.5.0 新增的开放世界与分支互动，不要求先建书，用自然语言定义世界契约（时间怎么推进、物品和证据怎么影响故事），系统生成可继续玩的世界并把每回合状态写回本地。

对外部 Agent 的接入有专门入口：`inkos interact --json --message "..."` 与 TUI 走同一执行内核；InkOS 也发布成了 OpenClaw Skill（`clawhub install inkos`），Claude Code 等兼容 Agent 可直接调用。`inkos up` 启动守护进程后台连写，通知推送支持 Telegram、飞书、企业微信和带 HMAC-SHA256 签名的 Webhook。

## 从小说工具到故事创作系统：八个月的演进

InkOS 的定位在这大半年里动过一次，看版本线比看宣传语准确：

| 版本 | 时间 | 关键变化 |
|------|------|----------|
| v0.4.6 | 2026-03-17 | 仓库最早的公开版本 |
| v0.6.0 | 2026-03-26 | 状态结构化：权威来源迁到 `story/state/*.json`，Zod 校验 |
| v1.0.0 | 2026-03-30 | 首个正式版 |
| v1.4.1 | 2026-05-18 | 5 月底文档的基线版本：原子命令、Studio、Short 短篇包、显式 18 工具的 Agent 模式已就绪（下文自测数据出自这一时期） |
| v1.5.0 | 2026-06-10 | InkOS Play 开放世界与分支互动；Studio 入口重做；审计维度 33 → 37 |
| v1.6.0 | 2026-07-01 | 互动影游；引入标准 `SKILL.md` 能力包 |
| v1.7.0 | 2026-07-11 | 完整翻译工作台；剧情多线推演（`inkos forecast`）；`inkos auto` 与通知 |
| v1.8.0 | 2026-08-17 | 统一 pi-agent harness（智能体运行时框架）；15 个内置 Skills；统一 FTS5/BM25 本地检索；安全章节工作区 |

两条对读者有实际影响的演进。一是定位：项目标题从"自动化小说写作 AI Agent"改成了"创作智能体系统"，长短篇小说之外，剧本、分镜、互动影游、开放世界和长文翻译都进了同一个工作台——但本文聚焦的长篇管线仍是其中最完整的主线。二是底座：v1.8.0 把 Studio Chat、TUI、`inkos interact` 和生产 worker 收敛到同一套 pi-agent 工具循环（构建在 Mario Zechner 的 [pi](https://github.com/badlogic/pi-mono) 之上，即 `@mariozechner/pi-ai` 与 `pi-agent-core`），既有的长篇管线降为可直接调用、可中断、可观测的确定性能力。

master 分支当前是 2.0 开发版：内置 Skills 扩到 19 个，去 AI 味从词表方案改为可替换的 `inkos-story-deslop` Skill 语义方法。本文机制描述以 v1.8.0 为准，读者动手前建议对照自己安装的版本。

## 项目方自测数据怎么读

项目方在 2026 年 5 月底的 README（v1.4.x 时代）公布过一组全自动生产数据——用 InkOS 跑玄幻题材的《吞天魔帝》（也就是 README 各处命令示例里用的那本书）：

| 指标 | 数据 |
|------|------|
| 已完成章节 | 31 章 |
| 总字数 | 452,191 字 |
| 平均章字数 | ~14,500 字 |
| 审计通过率 | 100% |
| 资源追踪项 | 48 个 |
| 活跃伏笔 | 20 条 |
| 已回收伏笔 | 10 条 |

怎么读这组数字：它测的是管线在长篇连载下的吞吐和状态管理规模——31 章、45 万字还能保持 48 个资源项和 20 条伏笔的账目连续，说明结构化状态和检索记忆确实在工作，这正是同类工具最容易崩的地方。它不能推出的同样明确：这是项目方自报的单样本数据，不是独立复现的 benchmark；正文质量、模型贡献占比、不同模型下的表现，都不在这组数字的覆盖范围内；现行 README 已撤下这一节，数据停留在 v1.4.x 时代。

"审计通过率 100%"尤其容易误读。按 Reviser 的机制，它不代表 31 章没有任何问题——默认管线只修关键问题，其他问题标记给人工审核。这个数字能说明的最多是"没有未处理的关键问题"，与文本质量的距离很远。`inkos analytics` 至今仍把审计通过率作为常规统计项，读自己的数据时建议保留这层怀疑。

## 适用边界与上手路径

**适合用的场景**：

- 有明确创作方向、写长篇连载的作者，尤其是需要状态管理（多线剧情、资源、伏笔账目）的网文题材
- 想把创作流程拆成可观察、可干预环节的团队：每章的意图、上下文、审计结果都是落盘文件，可以审查和回放
- 研究 Agent 管线设计的开发者：结构化状态、输入治理、审计闭环都是完整可读的实现

**可以等等的场景**：

- 纯创意探索阶段。InkOS 的强项是执行已知意图：`author_intent.md` 和 `current_focus.md` 得你自己写，它擅长"把你想好的事情写好"，不擅长"帮你想好"
- 一次性短文。建书、配模型、理解文件结构的初始化成本对单次任务偏高；真要快速出短篇，走 `inkos short run` 交付包更直接

**上手五步**（命令均按 v1.8.0 README 核对）：

```bash
npm i -g @actalk/inkos        # 需要 Node.js 22+
inkos init my-novel           # 初始化项目
cd my-novel && inkos          # 启动 Studio，在「模型配置」里填服务和 API Key
inkos book create --title "书名" --genre xuanhuan   # 创建第一本书
inkos write next 书名         # 跑完整管线写第一章
```

配好模型后，`inkos doctor` 能诊断配置来源和 API 连通性。模型侧支持 Google Gemini、Moonshot、MiniMax、智谱、百炼、DeepSeek、OpenRouter、Ollama 等服务和任意 OpenAI 兼容端点；`inkos config set-model` 可以给不同 Agent 配不同模型——README 给的参考组合是写手用创意强的模型、审计用便宜快速的模型、雷达用本地零成本模型。

一个商用前必须核对的点：许可证是 AGPL-3.0，对网络服务场景的传染性比 MIT/Apache 强得多，把 InkOS 集成进自己对外提供的产品前，建议先评估合规义务。

## 结语

InkOS 值得研究的不是"AI 能写小说"，而是它怎么把"写作"这个通常靠直觉的活动拆成可以逐环节审查的工程流程：输入先编译再进模型，状态用带 schema 校验的 JSON 做权威，审计产出带证据的 observation 而不是一个通过与否的印章。上下文膨胀、状态漂移、AI 味这三个问题的解法分别落在检索投影、结构化状态和双层去 AI 味上，环环有对应。

它也确实有代价：概念多（十个角色、七类投影文件、多层控制面），初始化和配置有学习成本，AGPL 许可证对商用不友好。在开源小说写作项目里，把管线拆到这个颗粒度并配齐审计与状态校验的还不算多——如果你的痛点恰好是长篇连载中的状态管理，它值得认真跑一次；如果你要的只是快速生成一段文字，更轻量的方案到处都是。

## 参考链接

- [Narcooo/inkos 仓库](https://github.com/Narcooo/inkos)（AGPL-3.0，TypeScript）
- [Releases 发布线](https://github.com/Narcooo/inkos/releases)（v0.4.6 → v1.8.0，本文版本时间线的出处）
- [npm 包 @actalk/inkos](https://www.npmjs.com/package/@actalk/inkos)
- [pi-mono（InkOS 的 agent 运行时底座）](https://github.com/badlogic/pi-mono)
- [ClawHub Skill 页](https://clawhub.ai/narcooo/inkos)（OpenClaw / Claude Code 调用入口）
