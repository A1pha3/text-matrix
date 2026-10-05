---
title: "linkedin-skills：12 个先出草稿、等人批准的 Claude Code 技能，把 LinkedIn 经营拆成内容工程"
date: 2026-09-23T04:30:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Agent Skills", "LinkedIn", "开源项目"]
description: "sergebulaev/linkedin-skills 是一套 MIT 协议的 Claude Code / Codex 技能包：写帖、评帖、回复、去 AI 味、逆向爆款钩子、七日内容规划等 12 个技能，共享一条读写管道，全部走先草稿后审批的流程。本文拆解其技能映射、写作规范、读/写/图三层可选依赖与适用边界。"
github_repo: "sergebulaev/linkedin-skills"
source_key: "gh:sergebulaev/linkedin-skills"
slug: linkedin-skills-claude-code-approval-flow
---

## 核心判断

"用 AI 写 LinkedIn"的工具不少，通病也一致：要么发布即失控，agent 直接把内容推出去，人没有审阅机会；要么产出一眼 AI 味，发得越多，账号越贬值。linkedin-skills（[sergebulaev/linkedin-skills](https://github.com/sergebulaev/linkedin-skills)）把这两个问题当工程问题来解：**每个技能默认只出草稿，发布前必须等用户说 yes**（README 的说法是 "wait for your approval before anything gets published"）；同时内置一套明确反对 AI 腔的写作规范——并且诚实标注"不承诺骗过 AI 检测器，没有任何编辑能可靠做到"（"Does not promise to beat detectors (no edit reliably does)"）。

这是 Creative Content Crafts（[cccrafts.ai](https://cccrafts.ai)）开源的 LinkedIn 营销技能包：12 个 Claude Code / Codex 技能加一条所有技能共享的读写管道，MIT 协议，覆盖写帖、评帖、回复、逆向爆款钩子、七日内容规划、团队账号运营。截至 2026-10-03，仓库 3,974 stars、666 forks，最新版 v1.1.15（2026-09-29）；同一团队维护着 X、Instagram、YouTube、TikTok、Threads、Facebook 六个姊妹技能包，共享同一套声音引擎和审批流。用自然语言唤起，不用写代码。

## 12 个技能怎么组织

| 技能 | 类别 | 做什么 |
|------|------|--------|
| **Post Writer** | 写 | 从 20 个 2026 年钩子公式（排比、悬念缺口、情绪冷开场等）中按互动目标选型起草，可附创始人角度库 |
| **Humanizer** | 写 | 按段落评分 AI 词汇密度，处理 reveal bridge、碎句堆叠、表演式真诚；不承诺骗过检测器 |
| **Post Audit** | 写 | 发布前按 2026 算法启发式和 AI 检测模式检查草稿 |
| **Repurposer** | 写 | 把推文、视频、博客改写成原生 LinkedIn 帖：折叠线之上重做钩子、扩到 900–1,300 字符、链接移到首条评论 |
| **Comment Drafter** | 互动 | 给任意帖子 URL 起草评论，也可带评语转发 |
| **Reply Handler** | 互动 | 起草回复并正确处理两层评论扁平化；给一个帖子 URL 可扫完整个评论串批量起草 |
| **Hook Extractor** | 互动 | 逆向爆款帖的钩子公式，返回可填空的模板 |
| **Engagement Monitor** | 运营 | 对外拉点赞者/评论者按 ICP 匹配度分档；对内盯自己评论有没有换来作者回复 |
| **Content Planner** | 运营 | 七日内容计划：每日主题、格式、钩子、发布时间、评论目标 |
| **Profile Optimizer** | 运营 | 按 2026 转化模式重写 headline、About、Featured、Experience |
| **Employee Advocacy** | 运营 | 团队 LinkedIn 计划：14 天启动、发布节奏、品牌治理、ROI 追踪 |
| **Interviewer** | 基建 | 采访你并把回答存进 Story Bank（角色、带真实数字的凭据、转折点、伤疤、立场）；唯一零发帖历史也能用的技能 |

README 说"12 个技能加一条读写管道"，落到仓库里是 `skills/` 下 12 个目录，外加根目录一个 `linkedin-marketing` 元技能负责整体路由。表格和目录有两处对不上，而对上这两处，才算读懂这个项目的组织方式：

**Post Audit 没有独立目录。** 它是 Humanizer 的子技能（`skills/linkedin-humanizer/sub-skills/post-audit.md`），改写和审计本来就是同一段文字的正反面——审计发现的问题，改写负责修掉。

**Engagement Monitor 对应两个目录。** `linkedin-engager-analytics` 向外看人：拉任意帖子的点赞者和评论者，按 ICP 匹配度分四档（peer / aspirational / prospect / other），产出跟进名单；`linkedin-thread-monitor` 向内看线程：追踪自己的评论是否换来作者回复，按热度分四档——hot（6 小时内，90 分钟内跟回效果最好）、warm（6–24 小时，作者回复最集中的窗口）、cool（24–72 小时）、dormant（超 72 小时，改走私信）。README 把两半合成一行，因为它们是同一次互动运营的内外两面。

所谓的"一条读写管道"，是 `lib/` 下那层薄客户机：`url_parser.py` 解析 LinkedIn 的三种 URN 格式，`apify_client.py` 负责读，`publora_client.py` 负责写，`pixfaro_client.py` 负责配图，`approval.py` 负责审批卡。12 个技能共享这一层，技能本身只是 7,000 行指令——evals 脚本的自述原话是：这个包的本体不是代码，是"agent 要遵循的 7,000 行指令"。

## 写作规范是这个包的灵魂

多数同类项目把功夫花在"写得像人"，这个包把功夫花在"定义什么是不像人"。根 SKILL.md 的 Voice rules 有 10 条，全部技能强制继承，几条关键的：

- em dash（—）每 100 词最多 1 个——"这个符号在 2026 年已经不再是 AI 标志，密度才是"；
- 专有名词一律大写，"小写显得不尊重"；
- 禁用 AI 高频词：leverage、fundamentally、streamline、harness、delve、unlock、foster；
- 具体数字胜过形容词——"47%" 胜过 "significant savings"；
- 帖子 900–1,300 字符、评论 200–350 字符；
- **钩子必须活在前 210 个字符里**——移动端折叠线（"… see more"）之前，这是注意力真正投票的地方。

支撑 Post Writer 的是 `references/hook-formulas.md` 里的 20 个钩子公式（F1–F20），从平台风险排比（F1）、品类讣告（F2）、年度转折（F3），到面向创始人层的 4 个结构性公式：受控 A/B 轶事（F17）、伪二分消解（F18）、轶事对接证据（F19）、分岔曲线收尾（F20）。创始人是这个包的一等公民：`founder-topics.md` 提供了 10 个填空式角度模板（重新为品类定价、audience of one、稀缺机会的算术等），优化目标从曝光换成"少数高价值读者的信任"。

Interviewer 和 Story Bank 解决的是另一个冷启动问题：所有技能起草时都不再中途追问数字，因为素材已经躺在共享的 Story Bank 里。这也是 12 个技能里唯一不依赖发帖历史的——它要的是你的职业经历，不是你的帖子存档。

## 三层可选依赖：读、写、图

技能包本身零配置可用——所有需要外部数据的环节都会降级成"请你把文本粘过来"。三个可选服务各自补一层能力：

**Apify（读数据）**。Comment Drafter、Reply Handler、Hook Extractor、Engagement Monitor 可以借它自动读取帖子正文、评论串、互动者名单。四个无 cookie 的采集 actor 按量计费（$1–5 每 1,000 条结果），免费额度每月 $5；README 估算典型用法——日评论运营加每周一次互动者分析——每月不到 $2。没配 token 时自动降级为手动粘贴，功能不缺，只是费手。

**Publora（发布）**。默认模式是起草后自己复制粘贴；接上 Publora 的发布 API（免费层每月 15 帖），agent 才能直接发布。它替你处理了 LinkedIn 的三种 URL 格式、反应类型错位（用 PRAISE 而不是 CELEBRATE）、评论串扁平化 bug 这些平台暗坑。接入方式两种：claude.ai / Claude Code 用 connector（授权一次，无密钥落盘），其他环境用 API key 写进 `.env`——README 明确说两种方式并列、无主次。一个已知的坑值得提前知道：connector 不走 `.env`，所以 `scripts/check_config.py` 和 `selftest.py` 看不见它，它们报"manual"不代表发布没在工作。

**Pixfaro（配图）**。Post Writer 可以为草稿生成配图（feed 图、轮播页、钩子金句卡）。无 key 时降级为只出图像 prompt，自己拿去生成，流程不断。它是个多模型图像 API 的单一入口（$0.004/张起），卖点是把账号名、品牌色、logo 做像素级叠加，便宜的基础模型也能渲染出清晰文字的金句卡。

三层的健康状态一条命令可见：`python3 scripts/selftest.py` 分别报告 Apify、Publora、Pixfaro 各自是否就绪，缺什么点名什么，而不是给一个笼统的红叉。附带一层提示礼仪：缺哪层只在对话第一句说一次，之后不再重复推销。

有一层利益关联需要点破：README 的 License 节写着 "MIT. Powered by Publora"，Pixfaro 的注册链接也带推荐码。发布与配图两层依赖与作者是商业关联的，不影响读侧和草稿侧的可用性，但接入前应把这点计入。

## 审批门控的真身：约定，而非强制

"先出草稿再等人批准"是这个包最大的卖点，实现却值得看清楚。`lib/approval.py` 的文档字符串自己说明白了：这是一个**约定层，不是运行时强制**（"a thin conventions layer, not runtime enforcement"）——`render_approval_card` 规定了审批卡的标准格式（动作类型、完整预览、目标 URL、字符数，加一句 "reply YES to post or suggest edits"），技能被要求渲染这张卡然后停下等回复。

也就是说，门控的可靠性建立在 SKILL.md 指令的遵循度上，而不是代码层的硬拦截。对 Claude Code / Codex 这类对系统提示词遵循良好的 agent，这个设计是合理的轻量解；但它意味着门控不是安全边界——真正的硬约束只有一条：不配 Publora，就物理上发不出去。

配套的安全设计在另一个方向上：五个读侧技能会读到别人写的 LinkedIn 文本，而同一个会话又能以你的身份发布——这是典型的注入攻击面。项目的规则是：读回来的内容**是数据，不是指令**，不能指挥 agent、不能改动草稿、不能代替用户批准。

## 质量基建：tests 管管道，evals 管行为

这个包对"怎么验证一个 prompt 工程产品"给出了自己的答案，值得单独一提。`tests/` 用传统单测检查管道和文档格式；而 `evals/run_evals.py` 处理真正的问题——这个包的本体是 7,000 行 agent 要遵循的指令，单测测不了"agent 拿着它是否真的按说的做"。evals 的做法是拿 fixture 跑 agent、给输出打分，评分器刻意做成确定性的窄断言：嵌套回复的 `parentComment` 指对没有、脱敏后的草稿保住用户真实数字没有。自述的理由很清醒："需要品味的评分器，是一个会漂移的评分器。"每个用例一次模型调用。

## 一次周二的发布流程

把机制串成一条线。假设一个 B2B 创始人已经用 Interviewer 建好了 Story Bank：

1. **周一**，让 Content Planner 出七日计划。计划按"信念 / 构建公开 / 算术 / 证据"四类支柱排布每日主题、钩子和发布时间——周二 8:00 AM ET 是算法启发式给美国 B2B 受众的推荐窗口。
2. **周二早上**，让 Post Writer 写帖。它从 Story Bank 取真实数字，选 F7「反常精确的账本」公式起草（用 $14,287 这类怪异精确的数字替代整数），附一张 Pixfaro 金句卡；然后渲染审批卡停下——预览、字符数、目标账号，等你回复。
3. **你改两处，回 "post"。** agent 才调用 Publora 发布。没接 Publora 就到此为止：草稿加配图 prompt 都在，自己粘贴。
4. **周三**，thread-monitor 扫过去 72 小时的评论，发现一位作者在你评论的第二天回复了——正落在 warm 窗口（发出后 6–24 小时；作者回复的时点分布里这一档占 25%，质量最高，0–6 小时占七成）。它把线程路由给 Reply Handler 批量起草跟评，你审完放行。
5. **周四**，engager-analytics 拉那篇帖的点赞评论者，按 ICP 分档产出名单：3 个 peer（可回关）、1 个 prospect（值得约聊）、若干 aspirational（持续互动）。

全程只有两次人为放行，其余环节都在草稿和读取层打转——这就是"审批流"在真实节奏里的样子。

## 安装：七条路径

跨 agent 通用的入口是 skills CLI：

```bash
npx skills add sergebulaev/linkedin-skills
```

Claude Code（CLI / VS Code / JetBrains）走插件市场，注意是**两步**，少了第二步装不上：

```text
/plugin marketplace add sergebulaev/linkedin-skills
/plugin install linkedin-skills@linkedin-skills
```

其余路径按你的入口选：Codex CLI 用 `codex plugin marketplace add sergebulaev/linkedin-skills` 加 `codex plugin add linkedin-skills@linkedin-skills`；claude.ai 网页和 Claude Desktop 在 Customize → Plugins 里"从仓库添加市场"后粘贴仓库名（需要付费计划并开启代码执行）；Hermes Agent（Nous Research，遵循 agentskills.io 开放标准）把仓库 clone 进 `~/.hermes/skills/linkedin-skills`，从 OpenClaw 迁移可用 `hermes claw migrate`；OpenClaw 用户按 README 把仓库 clone 进工作目录、在系统提示词里指路即可。或者最简单：clone 下来直接当工作目录打开，`.claude/skills/` 的符号链接镜像让 Claude Code 自动发现全部 12 个技能。

装好后直接说话："帮我写一条关于 X 的 LinkedIn 帖子"，对应技能自动激活。

## 适用边界

- **英文生态构建**：钩子公式、词汇密度评分、发布时间窗口全部按英文 LinkedIn 和欧美时区设计，中文内容效果官方未验证，需自行测试；
- **发布侧依赖第三方**：LinkedIn 没有开放的发帖 API，自动发布绕不开 Publora 这样的中间层；介意第三方依赖就停在"草稿 + 手动粘贴"，功能主体不受影响——社区技能 linkedin-outreach 的说明也印证了这个边界：LinkedIn 连邀请和私信 API 都没有，连接请求只能草稿后人肉发送；
- **算法启发式不是官方口径**：Post Audit 依据的 `algorithm-heuristics.md` 自己标注"reported; not officially confirmed"——保存互动权重 5 倍于点赞、头 60–90 分钟窗口决定八成触达这类数字是逆向与社区观察，拿来当检查清单可以，当平台承诺不行；
- **审批门控是约定不是硬墙**：真正的硬开关只有"不配 Publora 就发不出去"，对门控有硬性要求的团队要自己加代码层拦截。

## 结尾判断

这个包真正值得看的不是"AI 帮你发帖"，而是它把内容经营的隐性知识显式化的程度：钩子公式可数、AI 味特征可评分、发布时机可查表、素材沉淀有固定格式、审批有标准卡片。哪怕你不用 Claude Code，`references/` 目录下的钩子公式表和算法启发式清单也值得单独抄走。

采用顺序上，已经用 Claude Code 且需要持续产出 LinkedIn 内容的创业者和运营者可以直接上手：先 clone 进工作目录零配置用起来（Interviewer 起步建 Story Bank），跑顺了再决定是否接 Apify 和 Publora。只想要写作规范和公式库的研究者，读仓库即可，不必安装。做中文内容或对发布链路有合规硬要求的团队，这个包目前帮不上太多——前者等生态验证，后者需要的是自己可控的发布层。
