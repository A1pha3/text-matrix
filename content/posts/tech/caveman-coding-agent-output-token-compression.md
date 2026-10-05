---
title: "Caveman 拆解：Agent 省 Token，少说话是小头，少读字才是大头"
date: "2026-07-09T02:55:00+08:00"
lastmod: "2026-09-29T00:00:00+08:00"
slug: "caveman-coding-agent-output-token-compression"
github_repo: "JuliusBrussee/caveman"
source_key: "gh:JuliusBrussee/caveman"
description: "Caveman 靠『让 Agent 用穴居人语气说话』一周拿下 4000 星，随后把自己宣传的 65% 省 Token 数字撤了下来：JetBrains 独立测试显示纯 skill 只省 8.5% 输出。项目转向压输入侧的本地 proxy（54 项基准实测输入 -33.2%）。本文拆解它的证据链、三件套架构与净亏损边界。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "Token 优化"]
---

# Caveman 拆解：Agent 省 Token，少说话是小头，少读字才是大头

## 先给判断

2026 年 4 月的一个周五，Julius Brussee 把「让 coding agent 用穴居人语气说话」做成一份规则文件发上 GitHub，一周拿了 4000 星，7 月登顶 GitHub Trending，如今 10.8 万星（2026-09-29 GitHub API 查询）。梗是传播的壳，这个项目真正值得记的是两个工程判断：

1. **Agent 账单的大头在读，不在写。** JetBrains 用 86 个真实编码任务做配对 A/B，测出纯 skill 只省 8.5% 输出 token——项目方把这当作造 proxy 的理由，原话是「Their 8.5% is the number that made us build the proxy」。压输入的 proxy 随后把同一套测试的输入打下来 33.2%。
2. **省钱数字必须能被审查。** 项目把早期到处宣传的「省 65%」从 README 撤了下来，理由写在 `evals/README.md` 里：旧评测的对照臂设错了，把「回答简洁点」这句通用指令的效果算到了 skill 头上，数字因此虚高。

token 优化工具圈不缺号称省一半的 README，缺的是敢把自己最高的数字撤下来的。所以这篇文章拆三件事：65% 是怎么没的、三件套（skill / proxy / middleware）怎么分工、什么情况下装它反而多花钱。全部数字核验于 2026-09-29 的仓库 v2.7.0（主分支）与第三方原始出处。

## 项目速览：一张嘴，一台过滤器，一套 SDK

项目现在是三件套加一批周边工具，主仓库的主语言是 Go（proxy 引擎），外加 TypeScript / Python 的 SDK 与 middleware。关键事实：2026-04-04 创建，Hacker News 曾登顶（904 分、366 条评论），ThePrimeagen 的反应视频标题是「No way this actually works」，Adobe Research 的 CAVEWOMAN 论文把这种风格当成正式评测对象。License 是双轨的：skill 和 CLI 是 MIT，proxy 引擎等核心运行时是 BSL-1.1（详见文末 License 一节）。

| 组件 | 管什么 | 动的是哪侧账单 | 形态 | 许可 |
| --- | --- | --- | --- | --- |
| **skill** | agent 怎么**说** | 输出 token | 一份规则文件，30+ agent 可装 | MIT |
| **proxy** | agent 怎么**读** | 输入 token | 本地 Go 进程，夹在 agent 和 provider 之间 | CLI 为 MIT，运行时 BSL-1.1 |
| **middleware** | 你自己写的 app 怎么读 | 输入 token | TS / Python 包装器（alpha） | MIT 客户端 |

```
 你的 agent（Claude Code · Codex · Gemini · Aider · opencode · …）
      │  工具输出 · 日志 · JSON · diff · 搜索结果
      ▼
 ┌──────────────────────────────────────────────────┐
 │ caveman proxy（你的机器，你的密钥）                │
 │ detect() → json · log · code · diff · search · text│
 │ 原文 → 本地 SQLite，返回恢复句柄                    │
 └──────────────────────────────────────────────────┘
      │  更小的 prompt，同样的回答
      ▼
 你的 provider（Anthropic · OpenAI · Google · Bedrock · Vertex · Azure · OpenRouter）
```

skill 那一侧不经过任何进程：它就是装进 agent 的规则，让回答变短，代码、命令、路径、报错原文一字不动。proxy 这一侧才是真正动账单的地方——agent 一天到晚在重读日志、测试输出和半个仓库，这些字节在到达 provider 之前先被本地压缩，原文留在你磁盘上，随时可以取回。

## 65% 是怎么没的

这篇博客的旧版本也引用过那个 65%：README 曾挂出一张 10 个 prompt 的对照表，平均输出节省 65%。7 月之后再看仓库，benchmark 区写的是「No reviewed API benchmark result is published here yet」——表撤了，理由拆开看有三层。

**第一层：评测方法错了。** 旧 harness 的对照臂是「无系统提示」，拿 skill 去比裸模型。可「回答简洁点」这句话本身就值几十个百分点的输出削减，skill 的真实增量被这句通用指令掩盖了。`evals/README.md` 现在把话挑明：旧数字 inflated（虚高），正确的对照是 skill 对一句朴素的 `Answer concisely.`。

**第二层：官方主动认账。** `docs/HONEST-NUMBERS.md` 写着：早期的 stats 版本「applied a fixed 65% output ratio without a committed reviewed result」——一个没有可审查结果支撑的固定比例。现在 Claude Code 状态栏里的节省数字后缀也撤掉了。

**第三层：第三方先捅破的。** JetBrains 实验室的博客标题还留着梗——《Speaking to AI Agents like Cavemen Saves 65% of Tokens. We Test.》——但实测结果只有 8.5%（细节见下节）。项目方没有回避这个数，反而把它放进了 README 当 proxy 的出生证明。

同一套风格，换个对照臂，65% 变成 50%，再换到真实编码任务变成 8.5%。这不是项目变弱了，是尺子换准了。

## 现在的证据链：谁测的、测了什么、不能推出什么

| 谁测的 | 怎么测的 | 结果 |
| --- | --- | --- |
| 本仓库 eval | 10 个开发问题，skill 对 `Answer concisely.` 对照臂，claude-opus-4-6，快照提交进 git | 在简洁指令之上，输出 token 中位数再降 **50%**。只量长度，不量对错 |
| [JetBrains](https://blog.jetbrains.com/ai/2026/07/speak-to-ai-agents-like-cavemen-tosave-tokens/) | 86 个真实编码任务，配对 A/B，Claude Code 2.1.200，纯 skill（当时 proxy 还不存在） | 输出 token **-8.5%**，成本约 -10%，质量无可检出差异（sign test p = 0.82） |
| [Adobe Research（CAVEWOMAN，arXiv 2606.24083）](https://arxiv.org/abs/2606.24083) | 8 个模型 × 5 个数据集 × 5 个压缩等级，双通道协议 | 压输出使实际成本降 **1.4–2.4×**，最好情况 3×；压用户输入则净成本反升 |

把三个来源放在一起读，才能回答 benchmark 该回答的三个问题。

**测的是什么。** 本仓库那 50% 测的是「skill 相对一句简洁指令的净增量」——隔离的是规则文件本身的贡献；JetBrains 测的是 agentic coding 会话里的输出侧；CAVEWOMAN 是学术协议，同时压输入和输出两个通道，量准确率与实际成本。

**数字反映系统的哪部分。** 都在输出侧。对话式问答里可删的客套话多，砍得狠；agentic coding 会话的输出大头是代码和工具调用，skill 碰不到它们（这是设计而不是缺陷），所以只剩高个位数。8.5% 和 50% 不矛盾，是任务构成不同。

**不能推出什么。** 不能从 50% 推出「账单省一半」——输入侧一字未动，规则文件自己还要在每个请求里加约 1000 个估算输入 token；不能从 8.5% 推出「没用」——质量无损且免费，白捡；更不能从任何输出数字推出「整个 session 净省」——那取决于规则注入方式、缓存命中和计费模式，`HONEST-NUMBERS.md` 为此专门列了净亏损场景（本文末节）。

### proxy 的数字：输入侧 -33.2%

JetBrains 的结论——agent 的账单主要是读，不是写——直接催生了 proxy。它的基准是固定的 54 次 Claude Code 运行（6 个用例 × 3 次 × 两臂），记 provider 上报的输入 token，每个回答都对标准答案核验：

| 用例 | 直连 Claude Code | 经 caveman | 变化 |
| --- | ---: | ---: | ---: |
| CSV 离群值排查 | 165,823 | 74,484 | -55.1% |
| 日志大海捞针 | 148,807 | 74,068 | -50.2% |
| YAML 配置漂移 | 132,124 | 71,027 | -46.2% |
| 测试输出失败分析 | 150,377 | 108,514 | -27.8% |
| 部署 JSON 漂移 | 147,975 | 108,939 | -26.4% |
| Dashboard HTML 告警 | 140,687 | 154,641 | **+9.9%** |
| **合计** | **885,793** | **591,673** | **-33.2%** |

18/18 回答正确，按用例聚类的 95% 区间是 14.6%–48.5%。同一套测试里，竞品 Headroom 的包装省 6.7%、答错 3 题（它的 703,202 只覆盖自己答对的 15 次运行，6.7% 也只在那 15 次的基数上成立）。

那张红色的 HTML 行值得单独说。该用例没有匹配到压缩变换，caveman 只付了自己的开销、没赚回任何东西，维护者把行留在表里并写道：「The day I hide a red row is the day you should stop trusting the green ones.」——我藏起红行的那天，就是你们该不再相信绿行的那天。方法论细节与来源哈希在 `docs/WRAP-BENCHMARK.md`，但原始 harness 产物未随仓库发布，官方自己也标注这是 pinned report（固定快照报告），不是公众可复现的实验。

### Adobe 论文的另一半：压缩人的输入是双输

CAVEWOMAN 最有价值的结果不在输出侧，在对照侧：把**用户的 prompt** 压成电报体，净成本不降反升——五个基准均值约 1.15×，最差数据集 1.8×，强压缩下 2.7×，因为模型会用更长的回答补偿，同时准确率崩塌。

这解释了 caveman 的一条产品红线：skill 只改 agent 的嘴，从不重写你的 prompt。如果你在自己的应用里想压输入，那是 proxy 和 middleware 的活——它们压的是工具输出，不是人的话。

## 一次 debug 会话里的数据流

用「修一个 flaky 测试」把三件套串起来。

**skill 侧。** 你在 Claude Code 里装了 skill，同一个 bug 诊断，普通 agent 回答「Sure! I'd be happy to help you with that. The issue you're experiencing is likely caused by...」，装了 caveman 之后是规则文件里的标准示例：「Bug in auth middleware. Token expiry check use `<` not `<=`. Fix:」——冠词、客套话、对冲语没了，报错代码与修法一字未动。轮到执行删除数据这类不可逆操作时，Auto-Clarity 机制让它自动退出电报体、用完整句子复述风险，确认完再切回来。安全警告永远不压缩。

**proxy 侧。** 你用 `caveman claude` 启动 agent，本地代理夹在中间。agent 为了定位 flaky 用例，`--verbose` 跑出一万行测试输出；代理的 `detect()` 把它判成 log 类型，保留错误、堆栈、首尾行，丢掉 INFO 和进度噪音（这一类的目标节省是 85–95%），完整原文写进本地 SQLite，给 agent 返回一个恢复句柄。agent 觉得被剪掉的段落可疑，调 `caveman_retrieve` 把原文拿回来——压缩可逆是整套设计的前提，没有任何一处「回不去的」有损压缩。

engine 按载荷类型分的压缩器与目标节省：

| 检出类型 | 保留什么 | 目标节省 |
| --- | --- | ---: |
| `json` | 键、结构、error/message 子树，折叠重复数组 | 70–90% |
| `log` | 错误、堆栈、首尾行，丢 INFO 与进度噪音 | 85–95% |
| `code` | import、签名、类型，函数体省略但语法仍合法 | 40–70% |
| `diff` | 文件/hunk 头与变更行，重复上下文省略 | 60–80% |
| `search-result` | 首尾命中加诊断/安全命中 | 80–95% |
| `text` / HTML | 标题、开头结尾、重要小节 | 50–80% |

`contextwindow.Pack()` 还能把候选上下文按 BM25 相关度、时间新近度和错误信号装进 token 预算，返回时保持原有顺序。这套东西同时以五个 MCP 工具（`caveman_compress` / `caveman_retrieve` / `caveman_stats` / `caveman_toon_encode` / `caveman_toon_decode`）暴露给任何 MCP 宿主。

## skill 本体：六档风格与 tokenizer 经济学

`/caveman lite|full|ultra|wenyan-lite|wenyan-full|wenyan-ultra|off` 调档，默认 full，说 `stop caveman` 恢复正常。同一个问题（「为什么我的 React 组件在重渲染」）在六档下的样子：

| 档位 | 回答 |
| --- | --- |
| lite | Your component re-renders because you create a new object reference each render. Wrap it in `useMemo`. |
| full（默认） | New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`. |
| ultra | Inline obj prop, new ref, re-render. `useMemo`. |
| wenyan-lite | 組件頻重繪，以每繪新生對象參照故。以 useMemo 包之。 |
| wenyan-full | 每繪新生對象參照，故重繪；以 useMemo 包之則免。 |
| wenyan-ultra | 新參照則重繪。useMemo 包之。 |

wenyan 三档是真文言，不是「更短的中文」。规则文件对 wenyan-full 的定义是删掉 80–90% 的字符（注意是字符不是 token）、主语常省、之乃為其登场。这档存在的理由官方只写了一句：「because someone asked」。

规则文件里最有意思的是那些「不做什么」，每条背后都是 tokenizer 经济学：

- **禁止自造缩写**（cfg / impl / req / res / fn）：tokenizer 会把它们和全词切成一样多的子词，token 一个没省，读者还得解码。
- **禁止因果箭头**（→）：箭头自己占一个 token，什么都没省。
- **不为装 caveman 而加词**：压缩只在风格层，输出绝不增长；「when it not」比「when not」多一个 token，所以后者赢。
- **否定词绝不丢**：not / never / no / only / except 丢了会翻转语义，比省下的任何 token 都贵。数字与单位精确。
- **混入 ASD-STE100 简明技术英语**：一句一事、单句 20 词以内、主动语态、同一个东西永远用同一个词——caveman 负责删废话，STE 负责保歧义边界，两者冲突时清晰度赢。
- **语言跟随用户**：压缩的是风格不是语言，你用中文它就回中文；技术术语、代码、API 名、commit 类型关键词、报错原文永远逐字保留。

命令箱比「一个风格」大：`/caveman-commit`（一行 Conventional Commit）、`/caveman-review`（一行一条评审发现，如 `L42: 🔴 null deref. Guard it.`）、`/caveman-compress <file>`、`/caveman-stats`、`/caveman-help`；三个压缩版子代理（cavecrew-investigator / builder / reviewer）；六个工作模式（investigate-first、lean-build、surgical-patch、safe-refactor、migration、verify-and-stop）——这些不压文字，压的是「少写不需要的代码」；另有七个驱动 engine 和 proxy 的命令（`/caveman-setup`、`/caveman-learn`、`/caveman-optimize` 等）。

### `/caveman-compress`：把 memory 文件也压了

针对 CLAUDE.md 这类每个 session 都要重读的长期文件，`/caveman-compress` 压散文留结构，原标题、代码块、路径、URL 逐字校验保留，原文件自动备份。仓库里的 fixtures 基准：

| 文件 | 原 | 压 | 节省 |
| --- | ---: | ---: | ---: |
| claude-md-preferences.md | 706 | 285 | 59.6% |
| project-notes.md | 1145 | 535 | 53.3% |
| claude-md-project.md | 1122 | 636 | 43.3% |
| todo-list.md | 627 | 388 | 38.1% |
| mixed-with-code.md | 888 | 560 | 36.9% |
| **平均** | **898** | **481** | **46%** |

这些是输入侧收益，和输出风格无关，也是旧版文章里今天仍然站得住的那张表。

### pixel mode：让 skill 自己也省

skill 是 prompt 文本，每个请求都要重读一遍——caveman 对自己下手：`caveman convert` 把已装 skill 的正文渲染成 PNG 页面让模型当图读，在 caveman skill 自己身上从 1069 个估算 token 降到 415，砍 61%。转换有门槛：只有当图片版真的更便宜才写入，任何失败都保持原文件字节不变；`--revert` 随时逐字节还原。

## 安装与采用顺序

**第一步，skill（免费，MIT）。** 一行命令装进 30+ 个 agent，无需账号和 API key：

```bash
npx skills add JuliusBrussee/caveman -g
```

**第二步，proxy（压输入侧，真正动账单的一步）。** 本地安装 CLI 并包住你的 agent：

```bash
npm install -g @caveman-ai/cli && caveman setup --install
caveman claude    # 或 codex · gemini · aider · kilo · qwen · opencode · hermes · openclaw · pi
```

原生支持 10 个 agent（Claude Code、OpenAI Codex CLI、Gemini CLI、Aider、Kilo Code、Qwen Code、opencode、Hermes、OpenClaw、Pi），各自的配置文件保持不动，靠环境变量或临时配置生效；`caveman disable <agent>` 可整体撤销。整个团队共用可以跑一个容器放进自己的 VPC。Codex 是唯一的例外：它的运行时拒绝改写 shrink 钩子（openai/codex#18491），只走其余通道。

**第三步，先测量再相信。** 这是最值得抄的一步：

```bash
caveman learn             # 读本地数月的历史会话，把 token 去向按最差优先排序，每条给一个修法
caveman learn implement   # 把修法交给 Claude Code/Codex 逐个 diff 执行，没降每轮 token 的自动回滚
caveman trial -- claude   # 同一任务开/关 caveman 各跑一遍，trial report 出对比
```

官方把话说得很直白：这个 A/B 的排名高于 README 上的每一个数字。如果你的工作流里它输了，就关掉。

**给你自己写的 app：middleware（alpha）。** 在已有的 LLM 调用外包一层，请求前把大的工具结果换成短副本并递给模型一个 `caveman_retrieve` 工具，会话历史里始终保留原始字节。TypeScript 走 `@caveman-ai/middleware` + `@caveman-ai/sdk`，Python 走 `caveman-middleware` + `caveman-sdk`（3.13+），Vercel AI SDK、LangChain、OpenAI、Anthropic、LiteLLM、CrewAI 等有现成适配。不想改代码就把 SDK 的 baseURL 指向本地 proxy。两个注意点：runtime 留在 record 模式时只测量不压缩，客户端和服务端模式要都设；runtime 不可达时原始请求原样通过，除非显式开 strict 模式。

## 什么时候它会让你多花钱

`HONEST-NUMBERS.md` 开篇第一句是「Caveman save tokens sometimes. Caveman cost tokens sometimes.」——有时省，有时费。已知的净亏损场景：

- **简短的编码问答**（issue #145）：固定的规则注入开销可能超过输出削减，有用户实测净亏。
- **按请求计费的服务**（issue #506）：GitHub Copilot 按 premium requests 收费，答案再短也是同一次请求，一分省不下；其他按消息计费的服务同理。
- **计数器反向的个例**（issue #550）：一次 Cursor A/B 里，开 caveman 跑出 430 万 token、关掉只要 100 万，耗时还翻倍。这次运行无法复现，官方的结论也克制：规则重注入、重试、缓存与上下文核算完全可能吞掉输出节省。A/B 净亏就关。
- **压缩人的 prompt**：CAVEWOMAN 的双输结论（前文），caveman 自己不这么干，你也别指望拿它改写提示词省钱。

对应的经验法则也是官方原文：同一任务开关 caveman 各跑一遍，对比 provider 账单页的总额；同一任务账单变高，就为这个工作负载关掉它。

## License 与隐私

License 是双轨制，旧版文章只写「MIT」在今天已经不对：

- **MIT**：skill、Agent SDK 与初始化器、CLI、两个客户端 SDK、contracts、provider catalog、extension shell、cavemem 薄客户端。
- **BSL-1.1**（source-available，非 OSI 开源）：Engine、Proxy、Cache Engine、rewriter、Browse、MCP server、`shrink`、cavemem Go 核心、共享 Go 平台。自托管服务自己的一方流量免费（含生产），转售托管给第三方需要商业授权；每个版本在 2030-06-21 或发布满四年（取早者）自动转为 Apache-2.0。

隐私边界：skill 和 hooks 完全本地运行、从不上报；proxy 没有任何 Caveman 服务器在中途，Claude Pro/Max 登录原样透传给 Anthropic，所有被压缩的原文存在你机器上的 SQLite 里。CLI 默认发送匿名使用统计（命令名与 token 计数，不含 prompt、代码、路径），`caveman telemetry off` 或 `DO_NOT_TRACK=1` 一键关死。一个容易忽略的细节：受管模式（managed mode）下的 wrap 会把仓库的 owner/name 和当前分支名作为 `x-cave-tags` 头发给 Cloud 侧用于把花费关联到变更——分支名里如果带了人名，而你不想让它出去，就在 checkout 之外启动或用 `ANTHROPIC_CUSTOM_HEADERS` 自定义这个头。

顺带修正旧版文章的另一处：npm 包 `caveman-shrink` 还在，但已退居为独立的 stdin/stdout 工具，专压 MCP / OpenAI 风格的工具目录（`cat tools.json | caveman-shrink > tools.min.json`）；MCP 侧的主力变成了 proxy 暴露的五个 MCP 工具与 `@caveman-ai/middleware`。

## 结尾：这个项目真正值得带走的

1. **优化 agent 成本，先看读侧。** JetBrains 的核心发现是 agent 账单大头在读——日志、测试输出、diff、搜索结果，而说话风格只能动写侧。8.5%（输出）对 33.2%（输入）就是这条判断的数字版。先搞清你的 token 花在哪，再决定装什么。
2. **评测方法决定数字可信度。** 同一个 skill，对照臂从「裸模型」换成「一句简洁指令」，65% 变 50%，且 50% 只在长度上成立；换到真实编码任务，8.5%。以后看到任何「省 X%」，第一个问题该是「和什么比、谁测的、原始数据在哪」。
3. **敢撤数字的项目才值得长期信。** 红行留在表里、状态栏撤掉节省后缀、文档用一整页告诉你什么时候该把它关掉——这些动作比任何一个绿色百分比都更能预测这个项目后续数字的可靠度。

采用顺序：长期跑 Claude Code / Codex、会话里日志和测试输出占大头的工程师，从 `caveman learn` 开始，装 proxy，用 `caveman trial` 拿自己的数字；主要做短问答、或按请求计费的团队，装个 skill 无妨（免费、无损），proxy 可以等；给第三方做托管服务的，注意 BSL-1.1 的边界，那需要商业授权。

## 参考链接

- 仓库：<https://github.com/JuliusBrussee/caveman>（v2.7.0，2026-09-29 核验）
- 诚实账本：<https://github.com/JuliusBrussee/caveman/blob/main/docs/HONEST-NUMBERS.md>
- 评测方法与修正史：`evals/README.md`；proxy 基准：`docs/WRAP-BENCHMARK.md`
- JetBrains 实验室测试：<https://blog.jetbrains.com/ai/2026/07/speak-to-ai-agents-like-cavemen-tosave-tokens/>
- CAVEWOMAN（Adobe Research）：<https://arxiv.org/abs/2606.24083>
- Hacker News 讨论（#1，904 分）：<https://news.ycombinator.com/item?id=47647455>
- The New Stack 的泼冷水标题：<https://thenewstack.io/caveman-mode-token-savings/>
- npm：[@caveman-ai/cli](https://www.npmjs.com/package/@caveman-ai/cli) · [@caveman-ai/middleware](https://www.npmjs.com/package/@caveman-ai/middleware) · PyPI：`caveman-middleware`
- 相关研究：Brevity Constraints Reverse Performance Hierarchies in Language Models（<https://arxiv.org/abs/2604.00025>），与 CAVEWOMAN 的「过度压缩伤准确率」互为印证
