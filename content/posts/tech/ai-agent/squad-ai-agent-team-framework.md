---
title: "Squad：把 GitHub Copilot 变成一支 AI 开发团队"
slug: "squad-ai-agent-team-framework"
github_repo: "bradygaster/squad"
source_key: "gh:bradygaster/squad"
author: "钳岳"
canonical: "https://txtmix.com/posts/tech/ai-agent/squad-ai-agent-team-framework/"
aliases:
  - /posts/tech/squad-ai-agent-team-framework/
date: "2026-03-31T12:50:00+08:00"
lastmod: "2026-09-26T12:00:00+08:00"
categories: ["技术笔记"]
tags: ["AI智能体", "GitHub Copilot", "多智能体"]
description: "Squad 把 GitHub Copilot 扩展成一支 human-led 的 AI 开发团队：成员有名字有章程，决策和偏好作为文件写回仓库，跨会话、跨机器可读。本文拆解它的多智能体分工、文件持久化与治理机制，并给出上手路径与适用边界。"
---

# Squad：把 GitHub Copilot 变成一支 AI 开发团队

Squad 不是把 Copilot 拆成几个聊天窗口，而是让一支分工明确的小队住进你的仓库。前端、后端、测试、组长各配一个独立智能体，成员名字取自一套主题化的"演员表"，决策和偏好作为文件写回仓库，跨会话、跨机器都能读到。项目定位里反复强调 human-led：人定方向、人做审查、人担最终责任，Squad 负责协调、重复劳动和并行执行。一句话概括它的主张：**让"团队"本身变成可以被版本管理的代码。**

本文基于官方仓库与文档站梳理，以 2026 年 9 月下旬的 dev 分支与 npm 0.13.1 版为口径，只讲真实存在的能力。

---

## 它解决什么问题

用 Copilot Chat 做大项目，三个问题会反复出现。

- **上下文装不下整个项目**：每次都只能看到当前文件附近的内容，跨文件的设计意图要反复提醒。
- **决策会丢**：上一轮定下的取舍，关掉 IDE 就没了，下次重新对齐。
- **只有一个角色视角**：任务横跨前端、后端和测试时，你得手动切来切去。

Squad 用两条机制回应：**多智能体分工**，把专业角色拆成独立智能体，各自有章程、有记忆；**基于文件系统的持久化**，把团队配置、路由规则、决策和工作历史全部落地到仓库的 `.squad/` 目录。下次打开项目，团队状态和之前的决定都在，不需要重新初始化。

先给一张地图，后面逐个展开：

| 组件 | 落在哪个文件 | 干什么 |
| --- | --- | --- |
| Coordinator（协调器） | `.github/agents/squad.agent.md` | 读请求、查路由、并行派活，是唯一的调度入口 |
| Lead | `.squad/agents/{name}/charter.md` | 拆需求、定接口、代码评审 |
| Backend / Frontend / Tester 等专员 | 同上，各一份章程 | 在自己的上下文里干活，写回学到的约定 |
| Scribe | 合并写入 `.squad/decisions.md` | 静默记录员，汇总所有成员的决策 |
| Ralph | 轮询 issue 与状态 | 哨兵，盯住仓库里的工作信号，按需提醒 |
| 团队状态 | `.squad/` 整个目录 | 花名册、路由规则、决策、历史，全部随 git 走 |

---

## 核心机制

### 一支有角色的队伍

第一次在仓库里跑 Squad 时，它走四步：扫描仓库（语言、目录结构、测试框架、依赖），提出一份 3–7 人的花名册，等你确认或增删，然后把成员写进 `.squad/`。默认构成里 **Lead**（拆解、评审、解阻塞）和 **Scribe**（静默记录决策）永远在；**Tester** 只在检测到测试设施时出现，**Frontend** 对应 React/Vue/Svelte/Angular，**Backend** 对应 API 路由或数据库代码，仓库有 README 或 docs/ 还会配一个写文档的 **DevRel**。

角色定义不需要从零生成。Squad 内置了一组基础角色，官方口径 20 个，覆盖软件研发（架构、前后端、测试、安全、数据、AI 工程师）与业务运营（产品、项目管理、市场、法务），用 `squad roles` 可以列出全部。选定角色后再按你的项目细化章程。

成员名字是最有辨识度的设计：来自一套主题化的"演员表"（casting）。官方示例里的 Keaton、McManus、Fenster 出自电影《非常嫌疑犯》，文档站演示用的 Flight、CAPCOM、FIDO 则是阿波罗任务控制的呼号。`.squad/casting/` 下有三个 JSON 维护这套体系——policy 是配置，registry 是已占用名字的注册表，history 记录每个"宇宙"的使用情况。名字跨会话持久，clone 仓库的人拿到同一批成员。

每个成员在独立的子进程上下文里运行，开工前读两样东西：全局的 `.squad/decisions.md` 和自己的 `agents/{name}/history.md`；收工后把学到的约定写回去。成员之间不共享对话，协调由 coordinator 统一做。这跟"戴着不同帽子切换"的聊天机器人是两回事。

花名册上还可以有真人。说一句"Add Sarah as design reviewer"，Sarah 就带着 👤 Human 徽章进名单——她没有章程和历史，不会被派活，但路由到她时 Squad 会暂停并提醒你去找她，事情办完你再回报结果。设计签核、安全审查这类必须人来做的决定，就有了明确的落点。

### 团队的所有状态都是仓库里的文件

装好 CLI 后跑一次 `squad init`，官方口径下它创建两样东西：`.github/agents/squad.agent.md`（coordinator 的智能体定义，Copilot 靠它认出 Squad）和 `.squad/`（团队状态目录）：

```text
.squad/
├── team.md              花名册：谁在队里、负责什么
├── routing.md           路由规则：哪类活归谁
├── decisions.md         共享记忆：全体决策（含人类批准状态）
├── decisions/inbox/     成员投递决策的收件箱，Scribe 负责合并
├── ceremonies.md        仪式 / 协作约定
├── casting/             演员表：policy、registry、history
├── agents/{name}/       charter.md 章程 + history.md 项目记忆
├── skills/              从工作中沉淀的可复用知识
├── log/                 会话历史（可搜索）
└── orchestration-log/   协调器派活了什么、结果如何
```

把整个目录提交进 git：

```bash
git add .squad/ .github/ .gitattributes
git commit -m "Add Squad team"
```

任何人 clone 这个仓库，得到的就不只是代码，还有这支团队的全部积累——花名册、章程、路由规则、决策、历史。团队记忆变得能 diff、能 review、能随分支演进。这是"团队即代码"的含义。

顺带一提目录名的演变：项目早期用过 `.ai-team/`，npm 分发迁移时（0.8.x 时期）统一改成了 `.squad/`，如今 `squad upgrade --migrate-directory` 还专门负责帮老项目改名。网上若见到 `.ai-team/` 的旧教程，路径全部要换。

### 说"Team"，就并行发散

给整个团队下任务时，用 **"Team"** 开头触发并行 fan-out；点名某个成员，任务就只交给那个人。协调器按三级策略路由：你点名的优先，其次匹配 `.squad/routing.md` 里的路径规则（比如 `src/api/**` 归 Backend），再不行按技能匹配，都没命中就由 Lead 分诊。GitHub issue 上的 `squad:{member}` 标签可以直接把工作派给对应成员。

努力程度也是分档的，官方给的四档响应模式：

| 模式 | 官方量级 | 何时触发 |
| --- | --- | --- |
| Direct | 约 2–3 秒 | 状态查询、事实性问题，协调器直接答，不派成员 |
| Lightweight | 约 8–12 秒 | 改错字类小活，单个成员、精简提示词 |
| Standard | 约 25–35 秒 | 常规任务，完整加载章程、历史与决策 |
| Full | 约 40–60 秒 | "Team, ..." 开头的复杂任务，多成员并行，可能触发设计评审 |

以"修一个超阈值发告警的成本监控功能"为例：说"Team, 实现成本告警"，Lead 评审需求、定接口，Backend 搭 AWS Cost Explorer 客户端，Frontend 写 Slack 通知模块，Tester 按需求补测试，Scribe 记录全程。五个窗口并行，而不是一个助手逐个切。收工后留下两条面包屑：`decisions.md` 里是每个成员做过的决定，`orchestration-log/` 里是派活与结果的全记录，你回来时可以带着完整上下文审查。

### 决策会自校准，治理写死在框架里

每个成员开工前都会读一遍 `decisions.md`，所以决策积累得越多，团队在约定上越自动对齐。成员产出的决策先进 `decisions/inbox/`，由 Scribe 合并进主文件——随口立下的偏好也会被固化，比如你说了句"以后都用结构化日志"，之后每个成员都会遵守，不用反复叮嘱。

比记录更进一步的是约束。Squad 把几条治理规则做进了框架，官方文档的表述是"用代码执行，而不是提示词里的建议"：

- **文件写入护栏**：成员改不了分配范围之外的文件；
- **PII 清洗**：敏感个人信息进记忆和日志前被剥离（另有 `squad scrub-emails` 命令可手动清理）；
- **评审锁定**：Reviewer 拒绝某次提交后，原作者被锁出该任务，不许自我翻案——防止无休止的修改重试循环，锁定期跨会话持久，明确说"Unlock 某某 for issue #42"才解除；所有合格成员都被锁死时，协调器升级给你裁决；
- **升级点**：悬而未决的决策会浮给指定的人类负责人，不会默默滑过去。

还有两类"仪式"（ceremony）会在关键时刻自动触发：多成员改同一片共享系统时开设计评审，构建失败、测试失败或评审被拒后开复盘，结论写进决策库。也可以随时手动点名开一场。

---

## 上手：十分钟跑起来

前置条件：一个 Git 仓库；**GitHub Copilot CLI**（负责运行团队，单独安装）；**GitHub CLI** 只在要用 issue、PR、项目板和值守循环时才需要。通过 npm 安装要求 Node.js 22.5+；不想依赖 Node 的话，Homebrew、WinGet 或官方安装脚本都自带运行时。

```bash
# 1. 安装 CLI（或 brew install --cask bradygaster/squad/squad）
npm install -g @bradygaster/squad-cli

# 2. 在仓库根目录初始化团队
cd ~/projects/my-app
squad init

# 3. 登录 GitHub，够到 issue / PR 的联动
gh auth login

# 4. 体检
squad doctor
```

想在一步内得到一支配好的队伍，用 `squad init --preset default`；不带参数的 `squad init` 会走完扫描—提议—确认的完整流程。

然后在命令行用 Copilot 拉起 Squad：

```bash
copilot --agent squad --yolo
```

`--yolo` 让 Copilot 不再对每次工具调用逐个弹确认。Squad 一个会话会做大量工具调用，不加这个选项会被审批提示打断。VS Code 里则打开 Copilot Chat，在智能体列表里选 Squad——CLI 和 VS Code 读的是同一份 `.squad/`，成员、决策、记忆完全共享。

接着描述你要做什么，比如"用 Go 写一个监控 AWS 费用的 CLI，超阈值发 Slack 告警"。Squad 会先拼出一支队伍念给你听，你确认或微调角色后，成员就开工了。

---

## 这半年长出了什么

这篇文字初稿写在 2026 年 3 月，当时 Squad 发布刚两个月、版本 0.8.x。到 9 月的 0.13.1，项目从"仓库里的多智能体框架"长出了几条新枝，选三个影响使用方式的：

**Ralph 值守模式。** `squad watch` 让 Ralph 持续轮询仓库 issue：默认每 10 分钟一轮，加 `--execute` 会把可执行的 issue 直接派给 Copilot 智能体处理，处理不了按四级策略恢复（重置熔断、重验凭证、拉取状态、暂停 30 分钟等人）。支持 `--overnight-start 18:00 --overnight-end 08:00` 设定夜间窗口，状态可以落到 git-notes 或孤儿分支上重启不丢。想造一个"睡觉时仓库自己往前走"的循环，这是入口。

**GitHub Agentic Workflows 集成。** 0.12.0 起，Squad 可以作为可复用工作流装进任意仓库，团队成员在 issue 评论里用斜杠命令指挥：`/squad` 从仓库分析直接选角组队，`/squad implement` 派发 issue，`/squad retro` 跑复盘。配套的自动改进 worker（squad-improvement-worker）设计得相当克制：自动实现默认关闭，产出一律是草稿，合并必须经人审。

**SDK 与 .NET 预览。** 不喜欢 markdown 定义团队的话，`squad.config.ts` 里用类型化的 builder 函数定义成员，`squad build` 生成全部文件（官方标注实验性，生产团队仍建议 markdown 优先）。`@bradygaster/squad-sdk` 提供程序化编排接口；.NET 那边有 `Squad.Agents.AI` 预览包，能把一支 Squad 作为 Microsoft Agent Framework 的 agent 注册进 DI 容器。

安装渠道也从 npm 一家扩到了 Homebrew、WinGet、独立安装脚本和直接下载归档，另有 preview / insider 两个尝鲜通道。CLI 命令从 15 个涨到 17 个，`squad shell` 交互式终端已废弃，日常入口统一收敛到 `copilot --agent squad`。

---

## 值得记住的三个行为特征

- **第一次最慢**：成员还没有历史。跑过两三次之后，它们会记住你的目录结构、命名习惯，不再重复提问。
- **成员会自己成长**：每个智能体把学到的约定追加进自己的 `history.md`，这是只追加、跨会话的私人记忆；一两周后对新任务的熟悉度接近老成员。退休成员进 `.squad/agents/_alumni/`，章程封存备查。
- **团队随代码走**：`git clone` 一个带 `.squad/` 的仓库，就完整带走了这支队伍；它也能进 CI、进 gh-aw 工作流被反复调用。

---

## 边界与注意

- **Alpha 预览**：官方在 README 顶部持续标注实验状态，API 与 CLI 命令可能随版本变化，破坏性变更记在 CHANGELOG。别在依赖其具体接口的自动化上锁得太死。
- **依赖 Copilot**：Squad 本体 MIT 许可、免费，但团队的日常运行依赖 GitHub Copilot（CLI 或编辑器里的 Copilot 订阅）；把 issue 派给 @copilot coding agent 后台干活，则按 coding agent 自身的订阅与计费规则来。
- **放开 `--yolo` 要审慎**：跳过逐次审批，等于把信任模型整体上移。Squad 的治理护栏（写入围栏、评审锁定）能兜住一部分风险，但建议先在隔离或分支环境里跑，对敏感操作保持人工把关。
- **离线能力有限**：读已落盘的团队文件、看决策日志可以离线；真正让成员跑起来、同步 issue，都依赖 Copilot 联网。
- **适合的阶段**：中小型项目验证与尝鲜很合适；对稳定性要求极高的核心系统，可先观察它的发布节奏（好在每版 CHANGELOG 记录得很细）。

---

## 什么时候该用它

- 项目大到单次 Chat 上下文装不下，需要按角色拆工作区。
- 项目周期长、需要团队持续记住决策，减少反复对齐的成本。
- 多技术栈项目，希望 AI 也按前端 / 后端 / 测试的边界分工。
- 想要"issue 进、PR 出"的半自动流水线，又不放心全自动——Ralph 值守加人工评审门是个折中点。

如果项目还在原型阶段、代码量不大，或者你一个人做且不需要角色分工，直接用 Copilot Chat 反而更轻。Squad 的价值在项目复杂度和团队规模上来之后才体现。

---

## 常见问题

**Squad 和 Copilot Chat 有什么区别？**

Chat 是单一角色、无跨会话记忆；Squad 是多角色分工，团队状态和决策通过 `.squad/` 文件持久化，能跨会话保留。

**要不要额外付费？**

Squad 本身免费开源（MIT）。运行团队需要 GitHub Copilot 订阅（Copilot CLI 或编辑器内 Copilot 均可）；只有用到 @copilot coding agent 后台处理 issue 时，才涉及该项功能对应的订阅档位。

**团队知识安全吗？**

默认存在仓库内、随代码走。框架内置 PII 清洗和写入围栏，但含敏感信息的文件仍应注意——不想提交的可以加进 `.gitignore`，公开仓库更要谨慎。

**能离线用吗？**

读取本地团队文件、查看决策日志可以离线；运行成员、同步 issue 需要网络。

**支持哪些入口？**

官方兼容矩阵覆盖四类界面：Copilot CLI（`copilot --agent squad`，日常推荐的完整功能入口）、VS Code（Copilot Chat 里选 Squad）、JetBrains（通过 Copilot 插件）、GitHub.com（@copilot coding agent 按 issue 标签后台干活）。Squad CLI 本身负责安装、体检、值守等运维动作，另有 SDK 供程序化集成。

---

## 结语

Squad 把"团队记忆"变成了可版本管理的源码，又把治理规则从提示词挪进了框架代码——这是它与普通对话式 AI 助手的两个根本区别。它还处在早期，但从选角、章程、决策合并到评审锁定，这套机制已经能支撑真实的日常工作流。当 AI 开发不再是一个对话框，而是一支住进仓库、跨会话持续工作的队伍，值得花十分钟让它在你自己的仓库里跑一次。

**资源**

- GitHub 仓库：https://github.com/bradygaster/squad
- 官方文档：https://bradygaster.github.io/squad/
- 讨论区：https://github.com/bradygaster/squad/discussions

---

*项目状态：Alpha 预览，MIT 许可。作者 Brady Gaster 为微软 CoreAI 部门 PM Architect。本文以 2026-09-25 的仓库 dev 分支与 npm 0.13.1 版为口径核对，文档信息随时间演进，以官方 CHANGELOG 为准。*
