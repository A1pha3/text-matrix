---
title: "GBrain：Garry Tan 给自己的 AI agent 造了一个带出处的记忆层"
date: "2026-04-11T23:01:28+08:00"
lastmod: 2026-09-30
slug: gbrain-ai-agent-workflow-automation-platform
github_repo: "garrytan/gbrain"
source_key: "gh:garrytan/gbrain"
description: "GBrain（garrytan/gbrain）不是又一个 Agent 框架，而是给现有 agent 补上记忆层：显式事实带出处、可更正可撤回、跨 agent 共享，靠 PGLite/Postgres + 混合检索 + 夜间富化循环运转。本文拆解其架构、协议与成本，并给出采用建议。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "记忆系统", "MCP", "开源", "Garry Tan"]
---

Y Combinator 总裁兼 CEO Garry Tan 开源的 [garrytan/gbrain](https://github.com/garrytan/gbrain)，名字容易被误读成又一个 Agent 框架。它解决的是另一件事：**让已经在用的 AI agent 拥有一个自己掌控、能积累、能查询的记忆层**。Garry Tan 用它做自己 OpenClaw 和 Hermes 部署的生产记忆库，README 自述规模已到 155,795 页、24,589 个联系人、5,340 家公司，由 66 个 cron 任务自动维护。

它和 ChatGPT Memory 那类托管记忆的区别在三个约束上：存的是**显式事实并带出处**，不是聊天摘要；支持**更正和撤回**，错了能修；**跨 agent 共享**，Claude Code、Codex、Grok Bot 读的是同一个库。数据落在你自己的 Postgres 里，密钥是你自己的。

写作时数据：30,448 Stars / 4,570 Forks / MIT 协议 / v0.60.11.0（2026-09-30 实测，GitHub API）。仓库 2026 年 4 月 5 日创建，发版节奏很快，9 月 29 日一天就发了 4 个版本。

## 它要解决的两个真实问题

GBrain 源自 Garry Tan 的个人 agent 项目 OpenClaw。最初的记忆就是一堆 Markdown 文件，搜索靠 ripgrep。项目的[起源文档](https://github.com/garrytan/gbrain/blob/master/docs/ethos/ORIGIN.md)承认这很快撞上两个问题：

1. **跨会话遗忘**。每个新对话都在重新问基础问题，上周介绍过的人、周二做的决定，到周四就没了。记忆文件存在，agent 却用不上。
2. **重复劳动**。同一个公司的两条消息变成两个联系人页面，三次会面变成三条互不关联的时间线。信噪比实时衰减。

GBrain 的解法不是某个大发明，而是一叠小改造的叠加：查询先查自己的 brain 再调外部 API；每次写页面自动提取图链接；关系用带类型的边存，"谁在 Acme 工作"这种问题才有确定答案；向量检索之上叠关键词和重排序；夜间 cron 去重、修引用、找矛盾。贡献全在"一起做齐"这件事上，底座是跑在 WASM 里的 Postgres + pgvector，不需要单独的数据库服务器。

## 系统地图：四组概念先分清

GBrain 的文档密度很高，动手前先分清四组容易混淆的概念：

| 维度 | 两边各是什么 | 怎么选 |
|------|-------------|--------|
| 存储引擎 | PGLite（Postgres 17 编译成 WASM，零配置）vs Postgres + pgvector（Supabase 或自托管） | 个人用、5 万页以内默认 PGLite；共享或大规模用 Postgres |
| 访问入口 | CLI（`gbrain <命令>`）vs MCP 服务器（`gbrain serve`） | 人自己操作走 CLI；给 agent 用走 MCP |
| 查询方式 | `gbrain search`（返回排序页面）vs `gbrain think`（返回合成答案） | 要原始材料用 search；要结论和出处用 think |
| 组织单位 | brain（一个数据库）vs source（brain 里的一个仓库） | 一个 brain 可装 wiki、笔记、文章等多个 source |

最后一条展开说：agent 按目录写页面时，路由规则放在 `.gbrain-source` 点文件里，按 6 层优先级链解析。这意味着你可以把公司 wiki、个人笔记、项目文档装进同一个 brain，各自保持独立的授权和路由。

架构上还有一个关键设计：**contract-first 的 BrainEngine 接口**（`src/core/engine.ts`，140+ 方法），CLI 和 MCP 服务器都从这个接口生成。所以 README 里每个 CLI 命令，agent 通过 MCP 都能调到等价操作，两边不会漂移。

## 记忆怎么存：带出处的事实，不是聊天记录

GBrain 存储的基本单位是**页面**（Markdown 文件）加**显式事实**。你说"记住这个：我们选了 Stripe 而不是 Adyen"，它存下这句话并记录出处（哪次对话、哪份文档）。每条事实可以更正、可以撤回，撤回后不会在检索里继续冒出来。

这套设计的系统记录是 Markdown 仓库：git 里删掉一个文件，数据库里对应软删除。但数据库里还有机器生成的页面、未解析事实和修订历史，这些不在 git 里——官方在[系统记录契约](https://github.com/garrytan/gbrain/blob/master/docs/architecture/system-of-record.md)里明确说 Markdown 导出不等于完整备份，要备份得另做数据库备份。

页面类型由 **schema pack** 决定。默认包 `gbrain-base-v2` 定义 15 种类型：person、company、deal、email、slack、project、tweet 等，14 个规范类型加 1 个兜底的 note。不合身可以自建：`gbrain schema detect` 聚类你的实际目录结构，`gbrain schema suggest` 用 LLM 细化，`gbrain schema review-candidates --apply` 人工把关后启用。类型不是标签摆设——`whoknows` 专家路由只认声明了 `expert_routing: true` 的类型，事实抽取只跑在 `extractable: true` 的类型上。

## 记忆怎么取：search 给材料，think 给答案

```bash
# 原始检索：按混合得分返回页面，不生成答案
gbrain search "who's working on AI agents at portfolio companies?"

# brain 层：合成带引用的答案，外加缺口分析
gbrain think "who's working on AI agents at portfolio companies?"
```

`search` 的排序是五种信号叠加：向量、关键词、RRF、来源层级加权、重排序器。新装默认用 Voyage 的 `voyage-4` 嵌入（1024 维）加 `rerank-2.5` 重排序，也可以换 OpenAI、Gemini、Ollama 本地模型等 13 家嵌入供应商，或用 llama.cpp 跑 Qwen3-Reranker 做全本地方案。

真正值得花时间的是 `think`。它跑同样的检索，然后把结果合成一篇**带页面级引用的答案**，末尾附一份缺口分析：哪些页面已经过时、哪些说法没有出处、哪些页面互相矛盾、哪里还有空洞。README 原话是"The gap analysis is the part that changes how you use the brain"——你知道了脑子哪里空着，才知道该往哪里补。

成本边界要分清：keyless 模式（不配任何 API key）下关键词检索照常工作，但语义检索、重排序会把文本发给配置的供应商并计费，`think` 需要单独配置对话模型。

## 图谱层：模式匹配抽边，数字要会读

GBrain 的知识图谱走的是便宜路线：可信的本地页面写入时，用**纯模式匹配**（不调 LLM）从 `[[people/alice-example]]` 这类引用里抽出带类型的边。远程写入不内联抽边——stdio 连接靠启动和空闲时扫描补，HTTP 连接需要显式维护或授权的 `add_link` 调用。官方反复强调：抽出来的边是待核查的证据，不是关系为真的证明。

效果有基准数字。在 BrainBench 关系类问题上，图适配器拿到 P@5 0.3421 / R@5 0.9791，纯混合检索是 0.1917 / 0.6874（[2026-09-09 刷新](https://github.com/garrytan/gbrain-evals/blob/main/docs/benchmarks/2026-09-09-retrieval-refresh.md)）。读这组数字要注意三点：它测的是"问关系类问题时图检索对混合检索的增益"，不是全任务普遍提升；增益主要来自召回率近乎翻倍（图边把相关页面直接带回来了）；它衡量的是整套系统在特定基准上的表现，换成你的数据分布不能直接外推。

## 后台循环：白天记录，夜里做账

GBrain 的日常运转是一个六环节循环，README 给的图示是：

```text
signal → search → respond → write → auto-link → sync
```

信号检测器（需要显式开启）从对话里捕捉可以长期留存的实质想法和实体提及；每次回答前先查 brain 再调外部 API；写回页面时自动连图；cron 负责同步。

真正的差异在夜间。官方叫 dream cycle，cron 跑起来做五类事：给联系人页面去重、修引用、给信息打显著度分、找页面间矛盾、准备第二天的任务清单。这个设计把"记忆维护"从 agent 对话里挪走了——对话窗口宝贵，整理账目这种活交给后台。在 OpenClaw 或 Hermes 这类常驻平台上，这个循环 24 小时不停，这正是 README 那组大规模数字的来源。

## 协议与接入：把记忆当成一根网线来卖

GBrain 最有意思的工程决策是定义了一份**记忆协议**。[MEMORY_VERBS v1](https://github.com/garrytan/gbrain/blob/master/docs/protocol/MEMORY_VERBS_v1.md) 把全部记忆操作收敛成七个动词：`recall`、`remember`、`entity`、`synthesize`、`forget`、`context_pack`、`delta`。协议版本 1 的字段名和语义**永久冻结**，只允许向后兼容地加可选字段——文档原话是"让每个 harness 依赖它的方式，像每个 Postgres 客户端依赖线缆协议一样"。还配了 `gbrain protocol conformance` 命令验证任何端点是否符合协议。这等于把记忆层做成了公共接口：其他记忆服务器实现同样七个动词，就能接入同一个生态。

接入面做得很全。MCP 工具目录（自动生成、有新鲜度守护）列出 **133 个工具、23 个分区**，默认 starter surface 约 38 个操作，`gbrain serve --surface verbs` 则只暴露七个动词。已验证的客户端覆盖 Claude Code、Codex、Cursor、Windsurf、OpenClaw、Hermes、Grok Bot、Muse、opencode、ChatGPT、Perplexity 等（各自有专门指南）。

远程访问是另一条主线。`gbrain mcp expose` 把 HTTP 服务器发布到你的 Tailscale 网络，自动装 launchd/systemd 用户服务，加 `--funnel` 可以开放公网给云上 agent 用。HTTP 服务器带 OAuth 2.1、动态客户端注册和限流，权限按 `read` / `write` / `admin` / `agent` 四种 scope 划分。给整个团队用的话，`gbrain agent register` 能为每个 agent 铸造带 scope 的 OAuth 客户端和 30 天 token。官方对共享边界的说明很直白：远程客户端被 source 授权和可见性过滤器约束，但能碰到本地文件和数据库凭据的调用方是另一层信任边界——授权测试覆盖的是具体路径，不是"零泄漏"保证。

## 安装与成本

```bash
bun install -g github:garrytan/gbrain
gbrain init --pglite --no-embedding   # keyless 本地 brain，无 Docker
gbrain doctor                          # 体检
```

要求 Bun 1.3.11 以上。**注意：GBrain 不通过 npm 分发**，npm 上同名的 `gbrain` 包是无关项目，装了会遮蔽真正的命令；README 专门警告了这件事，`gbrain doctor` 能检测并给出修复命令。PyPI 上也没有同名 Python 包。

最小接入只需两步——初始化本地 brain，然后把它挂给你的编程 agent：

```bash
gbrain init --pglite --no-embedding
claude mcp add gbrain -- gbrain serve --surface verbs   # 或 codex mcp add
```

成本分三档。keyless 本地记忆不花钱，用的是你已有的 harness 订阅；接上嵌入和重排序后按供应商计费；完整的 OpenClaw/Hermes 常驻部署（README 称之为"as intended"的用法）需要一台 8GB+ 内存的服务器加随用量增长的 API 开销，官方明说这远超一个聊天订阅。另有三个官方教程给了预估：个人 agent 全栈搭建约 2 小时，公司 brain（10–50 人团队）约 90 分钟，`gbrain skillopt` 技能优化一轮约 20 分钟、约 1 美元 API 费。

## 任务流案例：准备明早和 Alice 的会面

README 里的例子最能说明 search 和 think 的差别。你明天要见 Alice，想让 agent 帮你准备。

用传统个人知识工具，你得到的是五条搜索结果：Alice 的主页、三份会面记录、一条定价笔记——每条都要自己点开读。用 GBrain，你问"见 Alice 之前我需要知道什么"，`think` 返回的是这样的答案：

> Alice 在 Acme（一家 B 轮金融科技公司）管工程。你们上次交流是 4 月 22 日，谈了一次定价。有三件事还开着：她欠你新定价层的安全评审（截止 5 月 1 日，之后没有更新）；你答应给 500 席位层报价（4 月 25 日发出，尚未回复）；她提到在招 CISO，你说要介绍人脉。
>
> 提醒：brain 里关于 Alice 和 Acme 的信息已经六周没有更新了。她可能通过邮件或 Slack 回复过——这些渠道 brain 看不到。见面前值得先跟她确认。

注意最后那段。它不是检索结果的一部分，是缺口分析：brain 知道自己**不知道**什么。这个例子在 README 里完整可查，官方将其总结为一句话："Search finds the pages. The brain reads them for you and writes the answer."

配套机制在这个案例里各就各位：会面纪要由信号捕捉或邮件集成（Gmail/Calendar/Contacts 原生同步，也有 Twilio + OpenAI Realtime 的电话转 brain 页面方案）进入 brain；夜间 dream cycle 已经把 Alice 的多次会面合并成一条时间线、修好了引用；白天你用自然语言提问，agent 路由到 `synthesize`，答案带着每条事实的出处页面。

## 采用建议

**适合现在就上的：**

- 已经重度使用某个编程或个人 agent（Claude Code、Codex、OpenClaw 等），苦于它记不住跨会话的事——keyless 路径两分钟接入，不装任何额外服务。
- 在跑 OpenClaw 或 Hermes 这类常驻 agent，想要完整的采集-富化循环——这是 GBrain 的设计目标场景，代价是服务器和 API 开销。
- 想给 10–50 人团队建联邦式机构记忆、且愿意自己管 Postgres 的团队——company brain 教程走完约 90 分钟。

**可以再等等的：**

- 想要一个纯托管、零运维记忆服务的团队——GBrain 是自托管软件，数据库、密钥、升级（大版本升级可能要重建索引）都得自己管。
- 期望"多 Agent 编排框架"的人——它不管 agent 之间怎么分工，只管记忆这一层。
- 对检索质量有极致要求又不愿跑外部嵌入 API 的场景——全本地方案（Ollama/llama.cpp）可行，但效果要自己评测，官方的基准数字用的是 Voyage。

**起步顺序：** 先 `gbrain init --pglite --no-embedding` 加 `--surface verbs` 挂到现有 agent，验证一轮 remember/recall/更正/撤回；再导入你的笔记目录（`gbrain import`）看关键词检索够不够用；最后才考虑开语义检索、接邮箱日历、上 dream cycle 这些花钱花机器的环节。官方文档专门提醒：默认情况下 agent 存的记忆是 brain 级可见的，私密事实记得传 `visibility: "private"`。

## 相关资源

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/garrytan/gbrain |
| 安装文档 | https://github.com/garrytan/gbrain/blob/master/docs/INSTALL.md |
| 记忆协议 v1 | https://github.com/garrytan/gbrain/blob/master/docs/protocol/MEMORY_VERBS_v1.md |
| 个人 agent 教程 | https://github.com/garrytan/gbrain/blob/master/docs/tutorials/personal-brain.md |
| 公司 brain 教程 | https://github.com/garrytan/gbrain/blob/master/docs/tutorials/company-brain.md |
| 评测仓库 | https://github.com/garrytan/gbrain-evals |
| 起源故事 | https://github.com/garrytan/gbrain/blob/master/docs/ethos/ORIGIN.md |

---

_🦞 本文由钳岳星君撰写，基于 gbrain v0.60.11.0_
