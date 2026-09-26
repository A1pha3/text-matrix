---
title: "Langfuse 的真正赌注：一张不做 join 的 observation 表"
date: "2026-05-29T12:45:00+08:00"
lastmod: "2026-09-20T00:00:00+08:00"
slug: "langfuse-llm-engineering-platform"
github_repo: "langfuse/langfuse"
source_key: "gh:langfuse/langfuse"
description: "把 Langfuse 写成「观测 + 提示词 + 评估 + 数据集四合一」不算错，但它解释不了 ClickHouse 为什么在 2026 年 1 月收购这个项目。本文按 2026-09-20 核实的仓库与官方文档，从 v4 的 observations-first 数据模型出发拆解它的架构，并纠正三处流传较广的误读：prompt 缓存被当成响应缓存、A/B 分流被当成平台自带能力、以及「Langfuse 是同类里唯一能自托管的开源选项」。"
draft: false
categories: ["技术笔记"]
tags: ["可观测性", "Langfuse", "ClickHouse", "OpenTelemetry", "AI工程", "开源项目解读"]
---

多数关于 Langfuse 的介绍停在同一句话上：观测、提示词管理、评估、数据集四合一。这句话不假，但它解释不了两件事——ClickHouse 为什么在 2026 年 1 月把这个项目收进公司，以及 v4 为什么要逼所有存量项目做一次迁移。

能解释这两件事的是存储层的一个决定：把查询的基本单位从「一次请求」换成「一个执行步骤」，并让每个步骤在写入时就把所属请求的属性复制到自己那一行。读路径因此不再 join、不再去重。Langfuse 官方对这个模型的措辞是 observations-first，它同时解释了 v4 的速度、SDK（软件开发包）的版本门槛，以及被收购之后两家公司在数据密集场景上的互补。

按这个判断，下面会依次回答：数据模型到底是什么形状、v4 改写了什么、那些性能数字该怎么读、四条产品主线各自的边界在哪、以及一个真实请求会怎样流过整个系统。

顺手纠正三处流传较广的误读：提示词（prompt）缓存被解释成了响应缓存、A/B 分流被当成了平台自带的能力、以及「同类里只有 Langfuse 开源且可自托管」。

## 目录

- [1. 仓库现状与本文口径](#1-仓库现状与本文口径)
- [2. 系统地图：四条主线加一个存储层](#2-系统地图四条主线加一个存储层)
- [3. 数据模型：一行就是一个执行步骤](#3-数据模型一行就是一个执行步骤)
- [4. v4 改写了什么：去掉读时 join](#4-v4-改写了什么去掉读时-join)
- [5. 怎么读 v4 的性能数字](#5-怎么读-v4-的性能数字)
- [6. 读路径的另一半：Observations API v2 与 Metrics API v2](#6-读路径的另一半observations-api-v2-与-metrics-api-v2)
- [7. 提示词管理：缓存的是取 prompt 这一步](#7-提示词管理缓存的是取-prompt-这一步)
- [8. 评估：三种分数类型，评估器挂在 observation 上](#8-评估三种分数类型评估器挂在-observation-上)
- [9. 数据集与实验：实验离不开数据集](#9-数据集与实验实验离不开数据集)
- [10. 一次请求如何流过整个系统](#10-一次请求如何流过整个系统)
- [11. 部署形态：两个容器加四种存储](#11-部署形态两个容器加四种存储)
- [12. 数据出口：Blob Storage 导出与它的地雷](#12-数据出口blob-storage-导出与它的地雷)
- [13. 横向对比：Phoenix 与 LangSmith 的真实差异](#13-横向对比phoenix-与-langsmith-的真实差异)
- [14. 什么时候不该用](#14-什么时候不该用)
- [15. 采用顺序：谁先上、谁再等](#15-采用顺序谁先上谁再等)
- [16. 按症状排查](#16-按症状排查)
- [17. 五个自测题](#17-五个自测题)
- [18. 下一步读什么](#18-下一步读什么)
- [19. 维护指引：本文断言的失效条件](#19-维护指引本文断言的失效条件)
- [参考来源](#参考来源)

## 1. 仓库现状与本文口径

本文所有陈述的核实时间是 2026-09-19 至 09-20，来源只有三类：GitHub 的 API（应用程序接口）与仓库内文件、langfuse.com 的文档与 changelog、以及我自己跑的命令。每个数都标了口径，凡口径不明的地方都直接写「没有公开口径」。

| 项 | 当前值 | 口径 |
| --- | --- | --- |
| Stars / Forks | 34,811 / 3,808 | GitHub API，2026-09-19 |
| 贡献者 | 约 208 | `contributors?per_page=1&anon=true` 的分页末页页号 |
| 最新版本 | v4.38.0（2026-09-17） | GitHub Releases；同期 v3.225.8 仍在发版 |
| 仓库建立 | 2023-05-18 | API `created_at` |
| 许可证 | 开源核心 + 商业外围 | 见下 |
| 归属 | ClickHouse 旗下 | 见下 |

两个容易写错的点。

**许可证不是「MIT」一句话。** 仓库根 `LICENSE` 的版权行是 `Copyright (c) 2023-2026 ClickHouse, Inc.`，正文写明 `ee/`、`web/src/ee/`、`worker/src/ee/` 三个目录下的内容适用 `ee/LICENSE`，其余才是 MIT Expat。而 `ee/LICENSE` 开头自己就说："Langfuse is an open core project. Langfuse's core is permissively licensed (MIT license)."。所以准确说法是 open core：核心 MIT，企业特性目录另受一份 Enterprise License 约束。README 上挂的 MIT badge 只对核心成立。

**它已经不是独立创业公司。** 官方博客 `/blog/joining-clickhouse`（frontmatter 日期 2026-01-16，作者 Clemens、Marc、Max）第一句是 "ClickHouse has acquired Langfuse."，同一篇承诺 "Langfuse stays open source and self-hostable. There are no planned changes to licensing."。README 里的表述更省事："since January 2026 we're part of ClickHouse"。官网页脚现在写的是 "by ClickHouse"。

至于更早的融资：2023-11-07 官方博客宣布 400 万美元种子轮，投资方是 Lightspeed Venture Partners、La Famiglia 和 Y Combinator，YC 公司是 W23 批次（README badge 与 yc.com 公司页一致，公司状态标 Acquired）。有些中文文章把它写成 W24，也有文章把 ClickHouse 的法人写成 "Finto Technologies"——后者是把主语安反了，`langfuse.com/imprint` 页脚是 "© 2022–2026 Langfuse GmbH / Finto Technologies Inc."，Finto 是 Langfuse 自己的法人名，ClickHouse 的主体叫 ClickHouse, Inc.。

## 2. 系统地图：四条主线加一个存储层

Langfuse 的产品面是四条主线，但它们不并列：前三条往存储层写数据，第四条从存储层读数据。

```text
  写入侧                            读取侧
┌──────────────────────────────┐   ┌─────────────────────────────────┐
│ 1 观测 Observability         │   │ 查询：一张 observations 表      │
│   OTel / SDK 上报步骤        │──▶│   每行含自身数据 + trace 副本   │
├──────────────────────────────┤   ├─────────────────────────────────┤
│ 2 提示词 Prompt Mgmt         │   │ 聚合：Metrics API v2            │
│   版本、标签、playground     │──▶│   cost / token / 延迟 / 分数    │
├──────────────────────────────┤   ├─────────────────────────────────┤
│ 3 评估 Evaluation            │   │ 出口：Blob Storage 导出         │
│   分数、评估器、人工反馈     │──▶│   Parquet / CSV / JSON / JSONL  │
├──────────────────────────────┤   └─────────────────────────────────┘
│ 4 数据集 Dataset/Experiment  │     存储：Postgres 事务、ClickHouse 读数、
│   版本化测试集与受控实验     │     Redis/Valkey 队列、S3 兼容存原始事件
└──────────────────────────────┘
```

四条主线的职责边界，按官方文档的措辞整理：

| 主线 | 它负责的对象 | 一句话边界 |
| --- | --- | --- |
| 观测 | trace、observation、session | 只记录发生了什么，不判断好坏 |
| 提示词 | prompt 版本、label、config | 只管文案与参数的版本和读取延迟，不管模型响应 |
| 评估 | score、evaluator、score config | 把「好坏」变成可聚合的字段，挂到 observation 或 experiment 上 |
| 数据集 | dataset、dataset item、experiment run | 提供可复现的受控输入，是实验的轴 |

把它当「四件单品的集合」来评估会得出错误的结论：Langfuse 的取舍全在把这四件事塞进同一张可读宽表里。下面的拆解围绕这条主线。

## 3. 数据模型：一行就是一个执行步骤

官方 `docs/observability/data-model` 把概念定成三个，顺序是 observations、traces、sessions，而不是很多介绍里的「trace 为主、observation 为从」。

- **observation**：应用的一个执行步骤，大语言模型（LLM）调用、工具调用、检索步骤都算。可以嵌套以反映应用结构。文档特意补了一句：Langfuse 把 span 叫作 observation，同时 span 本身也是一种 observation 类型。
- **trace**：一次请求或操作，比如「用户提问到最终回答」这一整段。定义上就是「共享同一个 `trace_id` 的所有 observation 的逻辑分组」。
- **session**：可选，把属于同一次用户交互的多条 trace 归到一起，典型场景是多轮对话。官方建议多轮对话或有状态工作流才用。

真正决定后续一切的是文档里这句："Conceptually, Langfuse stores one observations table, and each row holds the observation-level data plus a copy of the trace-level attributes." 也就是说 `user_id`、`session_id`、`tags`、`metadata` 这些 trace 级属性由 SDK 在上报前自动复制进每一行 observation。表长这样（照官方文档的示例改写）：

| 行 | 类型 | 名称 | 延迟 | trace_id | trace 名 | user_id | session_id |
| --- | --- | --- | --- | --- | --- | --- | --- |
| obs-1 | span | handle-chat | 3.1 s | abc123 | chat-request | u-42 | s-7 |
| obs-2 | span | retrieval | 0.4 s | abc123 | chat-request | u-42 | s-7 |
| obs-3 | generation | llm-call | 2.6 s | abc123 | chat-request | u-42 | s-7 |
| obs-4 | span | build-report | 1.2 s | def789 | export-report | u-17 | s-9 |

类型字段目前官方列了 event、span、generation、agent（智能体）、tool、chain、retriever 等，各自有明确语义：event 记离散事件，span 记一段耗时，generation 额外带提示词、词元（token）用量和成本，retriever 特指「只查不改状态」的那一步。做成本与延迟归因时，选错类型等于把自己最关心的那一层过滤掉。

还有两个容易忽略的字段级机制。其一是**环境**：`environment` 用来隔开 production、staging、development，配合 tags、releases 一起构成过滤维度。其二是**客户端采样**：`LANGFUSE_SAMPLE_RATE`（或 SDK 构造参数 `sample_rate`）取值 0 到 1，默认 1 表示全采；设成 0.2 就是只上报 20% 的 trace。文档明说采样在客户端完成——这决定了它是成本阀，而不是服务端的保护措施。

## 4. v4 改写了什么：去掉读时 join

v4 于 2026-07-29 打出 `v4.0.0` tag，官方 changelog 在 2026-08-17 宣布 "Langfuse v4 is live on Langfuse Cloud and generally available for self-hosted deployments"。它带的新能力是一串：Monitors（成本/质量/延迟阈值，通过 Slack、webhook 或 GitHub Actions 通知）、Code evaluators、Filter search bar、Full-text search、Pulse、Langfuse Assistant、Observations API v2、Metrics API v2。

但版本名下的实质变化只有一句：v4 是 observations-first。changelog 的 "Technical background" 一节把旧路径讲得很清楚，值得逐步对照。

```text
旧（v3 及更早）
  旧 SDK 对 trace 和 observation 的更新分别写入两张表
        ↓ 查询时
  ClickHouse 先 join 两张表，再对同一实体的多次更新去重
        ↓
  规模一大就慢

新（v4）
  SDK 在上报前把 user_id、session_id 等 trace 级属性塞进每条 observation
        ↓ 写入
  一条已完成的 observation 只写一次，进一张反规范化的 append-only 表
        ↓ 查询
  既不需要 join，也不需要去重
```

这条改写带来三个直接后果，都能在官方页面上找到对应说明。

第一，**SDK 版本成了架构门槛**。文档点名：Python SDK 4.7.0 起、JS/TS SDK 5.4.0 起才会在上报前补齐 trace 级属性。低于这两个版本，数据仍按旧路径进表。升级 FAQ 里还有一句代价说明值得抄下来："Deprecated SDKs can delay data by up to 15 minutes."——旧 SDK 的延迟不是几毫秒，而是分钟级，因为它走的是即将下线的摄入通道。

第二，**trace 级属性从「一份」变成「每行一份」**。文档的措辞是 each row holds a copy，这是明确的冗余换速度取舍。它换来的是查询与聚合不用 join，代价是同一属性在成千上万行里重复存在。changelog 进一步说，append-only 与数据不可变给未来留了物化视图的空间——也就是说这一版先把读路径做窄，把优化余地留给下一步。

第三，**存量项目必须动**。Langfuse Cloud 在 2026-11-16 起只跑 v4，v3 端点与特性一并下线；官方说新项目和新建的 managed 项目无需迁移，存量项目要自己看 Migration Assistant 与迁移状态页。自托管不绑定这个日期，但 v3 的安全补丁只到 2027 年 1 月。要做的动作里最容易被漏掉的是四条：把 trace 级评估器改成 observation 目标、把 legacy-dataset 评估器改成 experiment 目标、把 Blob Storage 导出切到 enriched observations、把 PostHog 与 Mixpanel 的同步也切过去。

## 5. 怎么读 v4 的性能数字

Langfuse 站内 banner 当前写的是 "Langfuse v4 is here: real-time, up to 165× faster"，点进去指向 2026-08-17 那篇 v4 changelog。但那篇正文里没有 165×，它给的是另外两个说法：大结果集的首屏表格加载「从秒级降到毫秒级」，以及大项目在较长时间范围上的看板「at least 10x faster」。

这三组数各自能支撑到哪一步：

| 说法 | 测的对象 | 能推出 | 推不出 |
| --- | --- | --- | --- |
| up to 165× faster | 官方未在这一页给出口径 | 官方认为某个最好情况下差距在这个量级 | 任何日常查询会快 165 倍 |
| 首屏表格加载 秒 → 毫秒 | 大结果集首次列表加载 | 列表首屏的等待时间 | 导出全量、跑聚合的时间 |
| 看板至少 10× | 大项目、较长时间范围的仪表盘（dashboard） | 读放大明显的那类查询变快 | 小项目、短窗口的体感；写入吞吐 |

按第 4 节的机制回读这些数，它们指向的是同一件事：省掉的是读时的 join 与去重，所以受益最大的是「扫很多行、跨很长时间」的查询；本来行数就少的查询不会有同样体感。要拿自己的数据验证，唯一可靠的做法是在同一 project 上分别用 v3 与 v4 跑同一条 dashboard 查询，别的都是转述。

## 6. 读路径的另一半：Observations API v2 与 Metrics API v2

这两个 API 是 v4 新能力里对系统集成方影响最大的部分，`docs/api-and-data-platform/features/observations-api` 给了具体约束。

- **游标分页替代 offset**。首次请求带 `limit`，默认 50、上限 1,000；官方特意标了「v1 上限是 100」。还有下一页时响应 `meta` 里给 `cursor`，下一次请求把它塞回 `cursor` 参数。
- **只取需要的列**。文档的措辞是 "cursor-based pagination and selective field retrieval so you only fetch the columns you need"。观测行里 input/output 可以非常大，按需取列才是省传输的地方。
- **`parseIoAsJson` 已弃用**：不传或传 `false`，传 `true` 直接返回 400。
- **分数读取换到了 v3**：Python SDK 4.8.1 起的 `api.scores_v3`、JS/TS SDK 5.5.0 起的 `api.scoresV3`，`api.scores` 的 v2 读取路径标记为弃用。
- **v1 资源整体挪到 `api.legacy.*` 下**（Python 是 `*_v1`，JS/TS 是 `*V1`）。
- **可用性不对称**：两个 v2 API 只在 Langfuse Cloud 和自托管 v4 上提供；自托管 v3 得继续用 v1 Observations API。
- Metrics API v2 负责聚合 cost、token、调用量、延迟和分数——也就是把原来只能在 UI 上看的图变成可编程的读数口。

这里有一个容易被当成缺陷的行为：新写入的数据不是即时可见。文档提到需要在 OTLP exporter 上设置某个 header，才能看到准实时（near real time）的新数据。默认口径是批处理，做实时看板时要按这个前提设计刷新频率。

## 7. 提示词管理：缓存的是取 prompt 这一步

这是流传最广的一处误读。不少文章把 README 里那句 "Thanks to strong caching on server and client side, you can iterate on prompts without adding latency to your application." 解释成「相同 prompt 与参数的请求会命中响应缓存，不消耗 token」。这个解释不成立。

`docs/prompt-management/features/caching` 的标题就是 Caching of Prompts in Client SDKs，第一句写得很直白："Langfuse prompts are cached client-side in the SDKs, so there's no latency impact after the first use and no availability risk."缓存的是**提示词定义**的读取路径，和模型响应无关。它的链路是这样：

```text
SDK 本地缓存命中且未过期   → 直接返回，零网络请求
命中但 TTL 过期            → 先返回旧值，后台重新校验（保证可用性）
未命中（如进程刚启动）     → 调 Langfuse API
  └ API 侧用 Redis 缓存 prompt；Redis 不可用则回落数据库
可选：启动时 pre-fetch 预热
可选：本地空 + API 不可用时用 fallback prompt 兜底
```

文档对兜底的判断也很实在：pre-fetch 通常不必要，服务启动后第一次使用的少量延迟一般可以接受；fallback 更是少用，因为 prompts API 本身可用性盯得很紧。

这条澄清的实务含义是：把 prompt 缓存当成省钱手段是错的，它省的是每次请求前多出来的一次 HTTP 往返；要控成本得去看 generation 的 token 与成本字段，以及第 3 节说的采样率。

其余能力按文档口径：prompt 支持版本控制与 label，UI、SDK、API 都能创建和编辑变体；playground 用于交互调试；prompt 可以关联到 trace；还有 prompt composability、message placeholders、folders、webhooks 与 GitHub 集成。

**A/B 与灰度是另一处需要收窄的说法。** `docs/prompt-management/features/a-b-testing` 的实现方式不是平台按百分比切流量，而是：给两个版本打上不同 label（文档例子是 `prod-a` 与 `prod-b`），然后**由你的应用**在取 prompt 时随机交替使用——文档示例代码里直接 `import random`。Langfuse 负责的是让你能把两个 label 的流量分别关联到 trace 上、事后对比。官方也承认这条路子同样适用于 canary deployment（金丝雀部署），前提是分流逻辑你自己在应用侧写。所以「灰度 10%」这种能力，准确说法是「平台提供 label 与对比，分流比例由你实现」。

## 8. 评估：三种分数类型，评估器挂在 observation 上

`docs/evaluation/evaluation-methods/llm-as-a-judge` 对分数类型的表述是："In Langfuse, that score can be numeric, categorical, or boolean." 三种，不是四种。数值用于 0 到 1 这类连续判断；分类用于 `correct`、`partially_correct`、`incorrect` 这种显式标签；布尔用于二元裁决，文档给的例子是「用户是否不同意助手」「请求是否超出范围」「回答是否违反策略」。开放性文本反馈在 Langfuse 里走 comments 与人工标注路径，不是 LLM-as-a-Judge 的一种分数类型。外面还常见另一类注记，把三种类型分别挂到 v2.4.8、v2.3.6、v2.4.7 这些小版本号上；现行文档与 changelog 里找不到对应条目，不必照抄。

评估器挂在什么对象上，文档也换了口径。它现在按数据性质分流：

| 要评什么 | 挂在哪 | 官方态度 |
| --- | --- | --- |
| 线上真实流量 | observation（单个 LLM 调用、检索、工具调用） | 推荐 |
| 受控测试 | experiment（配合 dataset） | 推荐 |
| 整条 trace | trace-level evaluator | 已弃用，迁移指引要求改成 observation 目标 |

这个转向和第 3、4 节是同一件事的另一面：既然存储单位变成了步骤，评估也应按步骤打分。于是一个 agent 链路里，意图分类那一步的质量、检索相关性、最终生成质量是三条互不相加的独立信号，能定位到环节而不是给一个笼统总分。围绕评估器本身的治理能力在 2026-06 到 08 陆续补齐：evaluator 规则可复用、模板库、评估器版本可回滚、稳定的 evaluator API，以及通过 MCP 配置评估器（2026-06-10 changelog）。

Code evaluators 是 v4 的一揽子新能力之一，语义很具体：对线上 observation 与 experiment 跑确定性的 Python 或 TypeScript 检查，适合格式、字段、长度、模式（Schema）这类不该交给模型判断的验收。外面把它挂到「v0.19 Launch Week 5 新增」上的说法同样对不上——v0.19 属 2023 年的版本序列，而这项能力是随 v4 进入新能力清单的。

分数之外还有两条入口：UI 上直接打分与写评论（scores via UI、comments）、终端用户反馈（user feedback）、以及对结果做人工更正（corrections）。这几条构成「人工投入最少 → 最多」的梯度，但官方并没有把它们排成一个五级矩阵，写的时候不必凑数。

## 9. 数据集与实验：实验离不开数据集

数据集这一侧，`docs/evaluation/experiments/datasets` 的版本化描述可以直接引用：每一次对 item 的 add、update、delete 或 archive 都会产生一个新的 dataset version，版本按时间戳追踪；GET 类接口默认返回查询时刻的最新版，要取历史状态就在 `version` 参数里传时间戳；`langfuse.get_dataset(name="...", version=version_timestamp)` 就是这个用法。文档还划了一条边界：版本化只作用于 dataset items，schema 变更不会生成新版本。

这解决的是评测里最脏的一类问题：分数掉了，分不清是模型退步还是测试集被悄悄改过。有了按时间戳取版本的能力，「当时测了什么」才是可复现的。

实验这一侧，流传较广的说法是「Experiments 已独立为一级概念，可以脱离数据集运行」。现行文档不支持这个说法。`docs/evaluation/experiments/data-model` 列出的创建路径只有三条：SDK 的 Experiment runner、UI（入口就在 dataset 页面上）、以及直接走 OpenTelemetry 摄入，并且明确写着 "There is no public REST endpoint for creating new experiment runs; the legacy POST /api/public/dataset-run-items path is deprecated."。`experiments-via-sdk` 的定义也是「把应用或 prompt 循环跑过一个 dataset」。

真正的自由度不在「要不要数据集」，而在数据集放哪儿：文档说可以用 Langfuse 托管的数据集，也可以用**本地数据集**作为实验基础。也就是说快速冒烟不必先把测试数据上传，但「有一批带 input 与 expected output 的样本」这个前提不会消失。想不建数据集就并排比较两个 prompt 版本，对应的功能是 playground，不是 experiments。

数据结构上有两个细节值得记：`DatasetItem` 按 id 做 upsert，同一 project 内 id 必须唯一且不能跨数据集复用；每条 item 可以带 `sourceTraceId` 与 `sourceObservationId`，这就是从线上 badcase 反查回原始请求的链路。`status` 只有 ACTIVE 与 ARCHIVED 两态——注意 archive 也算一次版本变更。另外 Dataset 对象上有 `remoteExperimentUrl` 与 `remoteExperimentPayload` 两个字段，用于把实验触发到外部执行环境，v4 的发布说明还补了远程实验运行时的鉴权头。

持续集成/持续部署（CI/CD）这条路官方给的工作流是四步：建数据集 → 用 Python 或 JS/TS SDK 写实验跑过数据集 → 加评估器打分 → 分数越过阈值时抛 `RegressionError`。回退检查因此变成流水线里一个可捕获的异常，而不是靠人盯 dashboard。

## 10. 一次请求如何流过整个系统

把前面几节串成一条链。场景：一个客服 agent，用户问「我上周的订单为什么还没到」。

1. 应用侧收到请求，SDK（Python ≥4.7.0 / JS/TS ≥5.4.0）建立 trace 上下文，把 `user_id`、`session_id`、`environment=production`、`tags=["support"]` 带上。若设了 `LANGFUSE_SAMPLE_RATE`，此刻决定是否上报。
2. 意图分类那一步上报为 `span`；查订单接口上报为 `tool`；向量检索上报为 `retriever`；最终话术生成上报为 `generation`，带 prompt、token 用量与成本。SDK 在发出前把第 1 步的 trace 级属性复制进这四条 observation。
3. 写入路径：事件先进队列（Redis/Valkey），Worker 容器异步处理，observation 一次性落进 ClickHouse 的 observations 表，原始事件与多模态内容落 S3 兼容对象存储，事务性数据在 Postgres。
4. 因为四条 observation 各自携带 `user_id`，「按用户聚合本月成本」是一次扫描加聚合，没有 join。
5. 一个布尔评估器盯在意图分类那一步上，判断「这次是否属于超出范围请求」；一个数值评估器盯在 `generation` 上判 helpfulness；一个 code evaluator 检查最终话术里有没有按规定带上订单号。三个分数分别落在三个 observation 上，互不相加。
6. Monitor 发现 helpfulness 在最近一小时的滑动均值低于阈值，通过 Slack 告警——通知里带着能直接跳过去的 filter search bar 链接。
7. 值班的人点开最差那条 `generation`，把它连同来源 `observation` 一键加进数据集；这个动作让数据集产生一个新 version。
8. 提示词作者改出新版本，打 label `prod-b`。发布前用 SDK 在同一数据集的历史时间戳上跑一次 experiment，与旧结果对比，CI 里越界即抛 `RegressionError`。
9. 上线时由应用侧按 `prod-a` / `prod-b` 随机分流，两条路的成本、延迟与分数在同一张表里可比。
10. 一周后要把这批数据搬进数仓：Blob Storage 导出按 hourly 跑，只选需要字段组，格式选 Parquet。

这条链里，第 3 到第 5 步是 Langfuse 自己承担的部分，第 8、9 步的分流与回归判定仍是应用代码。把这条边界看清楚，比记住它有几个功能有用。

## 11. 部署形态：两个容器加四种存储

官方自托管页面的架构叙述很短：Langfuse 由两个应用容器、若干存储组件、外加一个可选的 LLM API/Gateway（网关）组成。

| 组件 | 职责（官方措辞） | 选型含义 |
| --- | --- | --- |
| Langfuse Web | 提供 UI 与 API | 无状态，可横向复制 |
| Langfuse Worker | 异步处理事件 | 摄入吞吐主要看它 |
| Postgres | 事务性主库 | 项目、用户、配置这类数据 |
| ClickHouse | 存 traces、observations、scores 的 OLAP 库 | 读放大的来源，也是 v4 改造的落点 |
| Redis / Valkey | 队列与缓存 | 挂了会同时影响摄入与 prompt 读取延迟 |
| S3 兼容对象存储 | 存原始事件、多模态输入、批量导出等 | 多模态用得越多，这里越大 |

部署方式按官方给的层级是：本机 `docker compose` 起一套（文档口径是 5 分钟）→ 单机 VM 上的 `docker compose` → 生产首选 Kubernetes + Helm → 以及 AWS、Azure、GCP 的 Terraform 模板。页面同时强调 Langfuse 只依赖开源组件，可以本机、云上或本地机房部署。

这里有个判断值得写下来：v4 之后自托管的运维重心会明显偏向 ClickHouse。第 4 节的所有收益都建立在那张宽表上，而第 12 节会看到连导出格式都和 ClickHouse 版本有关（Parquet 需要 25.11 起才完整）。原本只想「装个观测工具」的团队，实际上是在多运维一个 OLAP 集群——「可以共用已有的 ClickHouse」这句省事话掩盖的正是这块复杂度。

## 12. 数据出口：Blob Storage 导出与它的地雷

`docs/api-and-data-platform/features/export-to-blob-storage` 的行为参数很具体，而流传的描述里有真有假，值得整段核对。

- 目标：Amazon S3、S3 兼容存储、Azure Blob Storage。**GCS 是通过 S3 兼容路径接的**——endpoint 填 `https://storage.googleapis.com`，鉴权用 HMAC 密钥对，而不是 service account（服务账号）。
- 格式：Parquet（默认）、CSV、JSON、JSONL。文本格式可选 gzip；Parquet 用它自己的编码与压缩。「导出支持 gzip」这句常被补成「所有格式都能压」，实际默认那个 Parquet 反而不吃这个开关。
- 频率：每 20 分钟、每小时、每天、每周。字段组（field groups）可配，所以「只导 trace_id、时间、模型、成本、延迟，不导完整 prompt」是成立的。
- 可用性按档分级：Cloud 上 Pro 不可用、Teams 需加购、Enterprise 可用；**自托管可用**。这一条直接推翻了「数据主权只能靠企业版」的想当然。
- 保存前可以用 Validate 检查 Langfuse 能否访问桶与凭证。

两个雷：其一，Parquet 的 observation 文件里没有 `input_price`、`output_price`、`total_price` 这三列，要用 `cost_details` 和 `total_cost`——照旧列名建表会在下游报缺字段。其二，自托管 ClickHouse 低于 25.11 时，不完整的 Parquet 输出可能不被上报，官方建议要么升级 ClickHouse，要么改用 CSV/JSON/JSONL。这类「格式与数据库版本绑定」的约束，正是把它自托管时最该提前排的地方。

## 13. 横向对比：Phoenix 与 LangSmith 的真实差异

把 Phoenix 与 LangSmith 标成「不开源、不能自托管」，再据此得出「Langfuse 是唯一开源选项」——这条常见论证的两级都不成立。

- Arize Phoenix（`Arize-ai/phoenix`，2026-09 约 11,540 stars）用 **Elastic License 2.0**：源码公开、可自由使用，但不是 OSI 认可的开源许可证。自托管则是官方明确支持的，arize.com 的 self-hosting 页原话是 "Phoenix is free to self-host with no feature limitations."，部署指引给了 Docker、Helm 等多条路。它的存储是 SQLite（默认）或 PostgreSQL，仓库里找不到 ClickHouse。
- LangSmith 平台本身闭源（`langchain-ai/langsmith-sdk` 是 MIT，但那只是客户端 SDK）。但「不能自托管」是错的：官方架构文档写的是 "Self-hosted LangSmith is an add-on to the Enterprise plan"，pricing 页 Enterprise 档带 self-hosted 与 hybrid 两种选项。更关键的是，它的存储栈里就有 ClickHouse——架构文档列的是 ClickHouse（traces 与 feedback 数据）、PostgreSQL（运营数据）、Redis。所以「只有 Langfuse 用 ClickHouse」同样不成立。

去掉这些稻草人之后，真实差异大致是这样：

| 维度 | Langfuse | Phoenix | LangSmith |
| --- | --- | --- | --- |
| 许可证口径 | 核心 MIT + `ee/` 企业许可（open core） | Elastic License 2.0（源码可得） | 平台闭源，SDK 为 MIT |
| 自托管 | 免费，Docker/Helm/Terraform；部分能力仅 Enterprise 档 | 免费，官方称无功能限制 | 仅 Enterprise 附加项 |
| OLAP 存储 | ClickHouse | PostgreSQL / SQLite | 含 ClickHouse、PostgreSQL、Redis |
| 与框架的关系 | 框架中立，OTel 为入口 | 开源工具链，非某框架附属 | 与 LangChain 生态最紧 |
| 主要定位 | 观测 + 提示词 + 评估 + 数据集同栈 | 评测与实验、本地起步快 | LangChain/LangGraph 全周期 |

「YC 背景」「50+ 集成」这类条目不该出现在对比表里——它们不构成技术决策依据。集成面当前更实的口径是：langfuse.com 的集成目录按框架、模型供应商、网关、开发者工具、无代码平台、分析工具等分组，sitemap 里 `/integrations/` 下的页面共 134 条（框架 42、模型供应商 30），其中 OpenTelemetry 自身占了两条子页，所以它是页面数，不是去重后的集成条数。真正决定要不要选它的，从来不是这里有多少行。

## 14. 什么时候不该用

判断条件按可验证的边界给，不按「规模大小」这种模糊词给。

**不必现在装**：单轮调用、没有多步链路、也不打算做版本化评测的原型。这种情况下你能从平台得到的只有一份请求日志，而第 11 节那套四件存储的运维成本一分都不会少。此时用 OTel 把日志打到任意后端更划算，反正 Langfuse 的摄入本来就是 OTLP。

**换了更合适**：团队已经在 LangGraph 上做完整个链路编排，且不打算离开它，那么 LangSmith 的原生追踪与 Langfuse 需要额外接 callback 相比，摩擦确实更低。反过来，只要有多框架并存或明确要防锁定，框架中立这条就值得为它付迁移成本。

**别指望它做到的**：把 prompt 缓存当成本阀（第 7 节）；把平台当灰度分流器（同节）；把「up to 165×」当自己环境的预期值（第 5 节）；以及把自托管当成一个单容器应用（第 11 节）。

## 15. 采用顺序：谁先上、谁再等

给一个按代价从低到高排序的接入顺序，每一步都能单独验收。

1. 先只接 OpenTelemetry 摄入，不写任何 Langfuse 专有代码。验收：能在 UI 里看到一条多步 trace，且每条 observation 都带上了 `user_id` 与 `environment`。
2. 确认 SDK 版本过第 4 节那条线（Python 4.7.0 / JS/TS 5.4.0）。验收：升级 FAQ 里的迁移状态页不报旧摄入通道。
3. 加**一个**布尔或数值评估器，盯在你最贵或最关键的那一步上，不要一上来全链路铺开。验收：分数能出现在 observations 列表的过滤结果里。
4. 从真实 badcase 攒一个 20 到 50 条的数据集，用 `version` 参数固定一次基线实验。验收：同一时间戳两次取到的条数一致。
5. 把基线实验搬进 CI，越界抛 `RegressionError`。验收：一次故意的 prompt 退化能让流水线红。
6. 最后才上 Monitors 和 Blob Storage 导出。自托管的话，先把 ClickHouse 升到 25.11 以上再配 Parquet 导出。

谁可以等：还没有面向真实用户的 LLM 功能、或团队里没有人负责看板的，第 3 步之后就可以停。谁该先上：多框架并存、有数据主权要求、或者已经开始为 prompt 改动争吵的团队——这三类团队正撞在 Langfuse 覆盖最实的那几段摩擦上。

## 16. 按症状排查

以下每条都对应官方文档或 FAQ 里已写明的成因，未收录未验证的社区说法。

| 症状 | 先查什么 | 依据 |
| --- | --- | --- |
| 数据没出现或晚十几分钟 | SDK 是否低于 4.7.0 / 5.4.0；官方明说旧通道可延迟至多 15 分钟 | v4 升级 FAQ |
| v4 升级后实验在 UI 里看不到，但 trace 和数据集条目都在 | JS/TS SDK ≥5.0.0 且还在手工调 `item.link()`；v4 靠 observation 上的 `langfuse.experiment.*` 属性把 run 关联到 trace，应改用 Experiment runner | `faq/all/experiment-runs-not-visible-v4` |
| 自托管调不到 Observations API v2 | 该 API 只在 v4（含 Cloud）提供，自托管 v3 用 v1 | observations-api 页 |
| 导出请求返 400 | 传了已弃用的 `parseIoAsJson=true` | observations-api 页 |
| Parquet 导出缺列或不完整 | 一是三列价格字段不存在，要用 `cost_details`/`total_cost`；二是 ClickHouse 低于 25.11 | blob 导出页 |
| GCS 配不上 | 要走 S3 兼容 endpoint + HMAC 密钥对，不是 service account | blob 导出页 |
| 分数类型里没有文本 | LLM-as-a-Judge 只有 numeric / categorical / boolean，开放性反馈走 comments | llm-as-a-judge 页 |
| 取到的数据集和上周不一样 | 没传 `version` 时间戳，GET 默认返回查询时刻最新版 | datasets 页 |
| 首次取 prompt 比预期慢 | 缓存是 SDK 本地 + 服务端 Redis，冷启动未预热属正常；只有同一份 prompt 定义的读取变快 | caching 页 |
| 只有部分 trace 上报 | `LANGFUSE_SAMPLE_RATE` 不是 1 | sampling 页 |

## 17. 五个自测题

1. 为什么说 v4 是 observations-first？它在写入和读取两侧各改变了什么，代价是什么？
2. Python SDK 4.6.x 接进 v4 项目，数据能写进去吗？会碰上什么具体问题？
3. 一个 prompt 缓存在 Langfuse 里到底缓存了什么？为什么不省钱？
4. 想把新版本 prompt 先放给 5% 用户，Langfuse 提供的是哪两件事，你自己要写哪一件？
5. 分数从 0.82 掉到 0.71，怎么用 Langfuse 的机制分辨是模型变了还是测试集变了？

## 18. 下一步读什么

按顺序读比按目录跳读快：

1. `docs/observability/data-model` —— 一张表加一份行例，全篇的地基。
2. `changelog/2026-08-17-langfuse-v4` —— Technical background 那一节是本文第 4 节的原始出处。
3. `faq/all/upgrade-to-langfuse-v4` —— 四条迁移动作；自托管也要读，因为它写清了哪些通道会下线。
4. `docs/api-and-data-platform/features/observations-api` —— 写集成前读完分页与字段选择部分。
5. `docs/evaluation/experiments/datasets` 与 `docs/evaluation/experiments/data-model` —— 两条一起读，「版本化只到 item 层」与「实验必须有数据集」都在里面。
6. `self-hosting/deployment/infrastructure/clickhouse` 与 `blobstorage` —— 决定自托管失败率的两个组件。
7. `blog/joining-clickhouse` —— 只有两页长，但能解释为什么一个应用层项目会被基础设施公司买走。

## 19. 维护指引：本文断言的失效条件

下表列出本文里哪些断言依赖当前版本、以及什么事件会让它失效。改版本时只改表格内那几处就能保持全文自洽。

| 位置 | 断言 | 失效触发 |
| --- | --- | --- |
| 第 1 节 | 34,811 stars / 3,808 forks / 约 208 贡献者 / v4.38.0 | 任一项随时间变化；重取只需 GitHub API，口径已写定 |
| 第 1 节 | 核心 MIT、`ee/` 企业许可、版权归 ClickHouse, Inc. | `LICENSE` 或 `ee/LICENSE` 一旦改动需重写本段 |
| 第 1 节 | 2026-01-16 被 ClickHouse 收购；W23 批次；2023-11-07 种子轮 | 历史事实，不失效；但引用页 URL 若重组需更新 |
| 第 3 节 | observation 类型列表 | 新增类型（如后续 agent 相关）需补 |
| 第 3 节 | 采样默认 1、范围 0–1 | 环境变量改名需重查 |
| 第 4 节 | SDK 4.7.0 / 5.4.0 门槛 | 新版本 SDK 下可提升门槛 |
| 第 4 节 | Cloud 2026-11-16 转 v4-only、v3 补到 2027-01 | 日期一过整段变既成事实 |
| 第 5 节 | 三组性能数字的口径 | 官方一旦公布 165× 的测量方法，本表需重写 |
| 第 6 节 | v2 API 仅 Cloud 与自托管 v4；limit 上限 1,000 | 自托管 v3 下线后可删该句 |
| 第 7 节 | 缓存与 A/B 的真实语义 | 平台若内置分流需重写本节 |
| 第 8 节 | 分数三类型；trace 级评估器已弃用 | 弃用通道下线后改写 |
| 第 9 节 | 实验无公共创建端点；本地数据集可行 | v4 之后的 Experiments API 扩展需重核 |
| 第 12 节 | Blob 导出的格式、频率、分档、ClickHouse 25.11 | 分档调整是最高频变动 |
| 第 13 节 | Phoenix 11,540 stars 与 ELv2、LangSmith 自托管仅 Enterprise | 竞品定价与许可证变动需重查 |

## 参考来源

- 仓库与元数据：<https://github.com/langfuse/langfuse>（`main`，GitHub API 2026-09-19）
- 许可证：`LICENSE`（MIT Expat + `ee/` 例外）、`ee/LICENSE`（open core 声明）
- README：YC W23 badge、"since January 2026 we're part of ClickHouse"、各能力条目
- 收购公告：<https://langfuse.com/blog/joining-clickhouse>（2026-01-16）
- 种子轮：<https://langfuse.com/blog/announcing-our-seed-round>（2023-11-07）
- YC 公司页：<https://www.ycombinator.com/companies/langfuse>（W23，状态 Acquired）
- 数据模型：<https://langfuse.com/docs/observability/data-model>
- v4 发布：<https://langfuse.com/changelog/2026-08-17-langfuse-v4> 与 GitHub Release `v4.0.0`（2026-07-29）
- v4 升级与已知问题：<https://langfuse.com/faq/all/upgrade-to-langfuse-v4>、<https://langfuse.com/faq/all/experiment-runs-not-visible-v4>
- 读路径：<https://langfuse.com/docs/api-and-data-platform/features/observations-api>、<https://langfuse.com/docs/metrics/features/metrics-api>
- 提示词：<https://langfuse.com/docs/prompt-management/features/caching>、<https://langfuse.com/docs/prompt-management/features/a-b-testing>
- 评估：<https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge>、<https://langfuse.com/docs/evaluation/evaluation-methods/code-evaluators>
- 数据集与实验：<https://langfuse.com/docs/evaluation/experiments/datasets>、<https://langfuse.com/docs/evaluation/experiments/data-model>、<https://langfuse.com/docs/evaluation/experiments/experiments-ci-cd>
- 自托管：<https://langfuse.com/self-hosting>、<https://langfuse.com/self-hosting/deployment/infrastructure/clickhouse>、<https://langfuse.com/self-hosting/deployment/infrastructure/blobstorage>
- 数据出口：<https://langfuse.com/docs/api-and-data-platform/features/export-to-blob-storage>
- 竞品：<https://github.com/Arize-ai/phoenix>（LICENSE 为 Elastic License 2.0）、<https://arize.com/docs/phoenix/self-hosting>、<https://docs.langchain.com/langsmith/architectural-overview>
