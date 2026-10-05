---
title: "OpenViking：把 Agent 上下文做成一个可 ls 的数据库"
date: 2026-08-24T03:40:00+08:00
lastmod: 2026-10-02
slug: "openviking-context-database-viking-uri"
github_repo: "volcengine/OpenViking"
source_key: "gh:volcengine/OpenViking"
description: "火山引擎开源的 OpenViking 把记忆、知识库和技能统一挂载为 viking:// 虚拟文件系统，用目录级 L0/L1/L2 三层加载控制 token 开销，检索走意图分析加全局向量加可选 rerank。本文对照 v0.4.22 源码拆解其核心设计、基准数据与采用顺序。"
draft: false
categories: ["技术笔记"]
tags: ["OpenViking", "AI Agent", "上下文工程", "RAG", "Agent 记忆"]
---
# OpenViking：把 Agent 上下文做成一个可 ls 的数据库

## 核心判断

`volcengine/OpenViking` 是火山引擎开源的**上下文数据库（Context Database）**，官方现在的自我定位里多了个定语：self-evolving——记忆、知识库、技能不只是被存进去，还会随会话沉淀自动生长。它要解决的不是"再造一个向量库"，而是一个更具体的问题：AI Agent 的记忆、知识库和技能散落在各种黑盒存储里，Agent 自己不知道"它知道什么"，开发者也没法调试检索过程。

OpenViking 的答案是把这一切挂载成一个 `viking://` 虚拟文件系统——Agent 用 `ls`、`tree`、`find`、`grep` 浏览自己的上下文，用分层加载控制 token 开销。截至 2026 年 10 月初，该项目在 GitHub 上有约 3.9 万 star，最新版本 v0.4.22（2026-09-28），Python 实现，主项目 AGPLv3 协议。

## 问题：黑盒向量库的三个痛点

用传统 RAG 栈（向量库 + 检索 TopK）给 Agent 配记忆，常见三个问题：

1. **不可见**。检索发生在 embedding 空间里，Agent 拿到几段碎片，但不知道这些碎片从哪来、周围还有什么。结果对不对，全凭运气。
2. **token 失控**。要么塞摘要省 token 丢细节，要么整篇加载烧 token。没有"按需加深"的中间态。
3. **记忆被动**。会话结束，对话数据就沉没了——用户偏好、Agent 踩过的坑，都需要显式工程才能沉淀。

OpenViking 对这三点分别给出了机制化的回应。

## 系统地图

进入细节前先看东西怎么分。OpenViking 里所有上下文分三类，访问面和存储层则是另一条轴：

| 上下文类型 | 挂载路径 | 存什么 |
| --- | --- | --- |
| Resource | `viking://resources/` | 项目文档、代码库、网页等外部知识 |
| Memory | `viking://user/{user_id}/memories/` | 用户偏好、事实、Agent 经验，会话 commit 后自动抽取 |
| Skill | `viking://user/{user_id}/skills/` | 怎么做事的方法，整包索引、按任务召回 |

访问面是 HTTP Server（默认端口 1933）之上的三套客户端：CLI（`ov` 命令）、SDK（Python / Go / TypeScript）和 MCP 工具。存储分两层：RAGFS 存内容本体（含三层摘要），向量索引存 URI、向量、元数据和摘要文本，检索读索引，`read` 读本体。每条内容有唯一的 `viking://` URI，跨层引用都靠它。

## 设计一：viking:// 虚拟文件系统

三类上下文统一编址在 `viking://` 之下：

```text
viking://
├── resources/              # 资源：项目文档、代码库、网页
│   └── my_project/
│       ├── docs/
│       └── src/
└── user/
    └── {user_id}/
        ├── memories/       # 长期记忆（偏好、事实、经验）
        ├── resources/      # 用户私有资源
        ├── skills/         # 技能
        ├── peers/          # 稳定对话对象（Peer）的空间
        └── sessions/       # 会话：messages.jsonl + 归档历史
```

这个设计的直接收益是**确定性**：定位和操作上下文像开发者操作文件一样，路径就是身份。Agent 可以先 `tree` 一层看全貌，再钻进具体目录，而不是把全部赌注押在一次向量召回上。另一个不那么显眼的收益是**可编辑**：记忆和知识都是文件，你（或你的 Agent）能直接查看、修改、合并，而不用对着一个 embedding 库发呆。

## 设计二：L0/L1/L2 三层分级加载

分层加载的想法不稀奇，OpenViking 的做法有两个具体差异。

第一，**L0/L1 挂在目录上，不是每个文件一份**。官方文档（`docs/en/concepts/03-context-layers.md`）说得很直白：L0/L1 是目录级语义 sidecar，单个文件不生成自己的摘要层，文件摘要作为输入聚合进所属目录的 L1。落盘形态是目录里的两个隐藏文件——L0 存为 `.abstract.md`（默认上限 256 字符，`semantic.abstract_max_chars` 可调），L1 存为 `.overview.md`（默认 4000 字符）；L2 就是原始文件本身，没有统一上限。普通的 `ls` 不显示这两个 sidecar，直接 `read` 才能看到完整内容（含 YAML frontmatter 元数据）。

第二，**摘要是异步自底向上生成的**：文件摘要 → 叶子目录 L1 → 叶子目录 L0 → 逐级向上聚合，到命名空间边界为止。所以刚 `add-resource` 完立刻检索，结果可能不全——导入返回的是一个后台任务 ID，要轮询到完成。

这套机制还带了"新鲜度"账本：每个 sidecar 的 frontmatter 记录 `freshness`（直接子项总数、本次采样数、待处理变更数）。直接子项不超过 32 个（`semantic.overview_sample_limit`）的目录，子项变更立即触发上级刷新；更大的目录走确定性采样，变更先累计 `pending_child_changes`，占比达到 10%（`semantic.freshness_refresh_ratio`）才刷新。摘要因此是一份带明确覆盖声明的快照，而不是假装实时。

对 token 开销的控制由此变成结构性的：Agent 先读 256 字符的 L0 判断"这片区值不值得深入"，再读 L1 拿结构和导航，真正需要才加载 L2。`mkdir` 建目录时只有 L0（无描述就用目录名兜底），L0 和 L1 允许单独存在，读和向量重建只处理实际存在的层级。副作用是写入侧多了一笔模型调用成本——每个目录两层摘要都要 LLM 生成，后文的适用边界会回到这一点。

## 设计三：检索 = 意图分析 + 全局向量 + 可选 rerank

这里要修正一个直觉：既然是文件系统，检索是不是"向量定位目录、再逐层下钻浏览"？至少当前版本不是。官方检索文档明确写着：检索不做目录递归导航，文本查询可以直接命中 L0/L1/L2 任何一层的记录。目录在检索里的角色是**范围**，不是路径——查询可以被限定在某个项目子树或记忆子树里，而不是扫描整个平面向量池。

完整的检索管线是三段：

```text
Query → 意图分析（可选）→ 全局向量检索 → rerank（可选）→ 结果
```

入口有两个，分工不同：

- **`find`**：单条查询直接检索，不看会话上下文，走 QUICK 模式（召回 `limit` 条，无 rerank），延迟低，适合"查一下 OAuth 怎么配"这类简单问题。
- **`search`**：先过意图分析——LLM 读会话压缩摘要、最近 5 条消息和当前查询，产出 0 到 5 条带类型的子查询（`TypedQuery`：改写后的 query、上下文类型 MEMORY/RESOURCE/SKILL、意图、1–5 优先级）。闲聊问候会得到 0 条查询，直接跳过检索；复杂任务则可能同时查技能、资源和记忆三路。配置了 reranker 时自动升级 THINKING 模式：每条子查询召回 2 倍候选，rerank 单趟压回 `limit` 条。

"可观测"在这个版本体现为三件事：`search` 的返回里带着 `query_plan`（意图分析产出的子查询列表，你能看到模型把你的问题拆成了什么）；每条结果带 `level` 和 `score`，能看出命中的是摘要层还是原文层；目录作用域的解析由向量排序前的 TrieHI 索引完成——这是团队被 ICDE 接收的论文（arXiv:2606.16903）里形式化的部分。项目早期的目录优先队列、父到子分数传播、多轮收敛机制已被移除，现在的检索链路比"逐层下钻"的叙事更简单，也更接近标准向量检索的做法。

## 设计四：会话沉淀为记忆

会话 commit 拆成两阶段。第一阶段在请求内同步完成：路径锁下分配归档编号，把消息落成 `messages.jsonl` 写进 `viking://user/{user_id}/sessions/{session_id}/history/archive_NNN/`，进入持久队列后立即返回 task_id。第二阶段在后台异步跑：LLM 给这段历史生成 `.abstract.md` 和 `.overview.md`，然后按记忆策略抽取长期记忆写入用户空间，最后在归档目录里留下 `memory_diff.json` 和 `.done` 两个标记。

两点值得注意。一是**抽取有审计**：`memory_diff.json` 里新增、更新、删除分别记录，更新带修改前后内容，连"被校验或策略拦下的操作"都有记录（`skipped_operations` 带原因码），记忆不是黑盒写入，出问题能回看。二是**记忆有类型体系**：内置 profile、preferences、entities、events、identity、soul、cases、trajectories、experiences 九类，各映射到 memories 下的不同路径；其中 `experiences` 会启用完整的 Agent 进化管线并自动激活 cases 和 trajectories——这就是官方描述里 "self-evolving" 的机制来源。会话里涉及稳定 Peer（比如某个网页访客）时，相关记忆还可以落到对方的 peers 空间。

## 一次偏好如何变成跨会话记忆

把机制串起来看一条完整的流转。官方 README 建议的验证方式就是这个场景：

你在 Claude Code 里说"记住我偏好 tabs 缩进"，然后继续干活。此刻什么都没进长期记忆——消息先累积在当前会话里。会话 commit 时，第一阶段把消息归档，第二个阶段在后台跑摘要和抽取：这条偏好被写成 `viking://user/{user_id}/memories/preferences/` 下的一个文件，`memory_diff.json` 里多一条 add 记录。

几天后你开一个全新会话，问"我的代码风格偏好是什么"。Agent 端的集成把问题发给 OpenViking：若走 `search`，意图分析判定这是 MEMORY 类查询，产出子查询；全局向量检索在记忆子树范围内召回，`preferences/` 目录的 L0 摘要先参与匹配，命中后按需读出具体文件；结果以 URI 加摘要的形式注入会话。你得到答案，而这次的问答本身，又会在下一次 commit 时沉淀进去。

还有两个使用层面的细节。第一，记忆处理在后台异步进行，刚说完的偏好立刻去查查不到是正常的——这是设计行为，不是 bug。第二，接入 Agent 用的 key 有讲究：服务开了认证时，记忆读写要 user key，root key 不行。

## 效果：官方基准数字怎么读

项目在 0.3.22 版本给出了两组基准（复现脚本在仓库 `benchmark/` 目录；`benchmark/` 下还有 longmemeval、skillsbench、RAG、vectordb_perf 等更多评测，完整报告见官方博客，README 引用的主要是这两组）：

**长对话用户记忆（LoCoMo）**：测的是多轮长对话后，Agent 还能不能答对关于用户的事实。三个 Agent 集成（OpenClaw、Hermes、Claude Code）原生记忆准确率分别为 24.20%、33.38%、57.21%，接入 OpenViking 后全部提升到 80–83%；同时输入 token 下降 34.3–91.0%，查询延迟下降 58–66%。

**多轮 Agent 任务（tau2-bench）**：测的是客服型多轮任务的成功率。经验记忆让同一 LLM 在 Retail 场景 +6.87 个百分点、Airline 场景 +11.87 个百分点。

读这组数字先看三件事。LoCoMo 的提升主要反映**记忆管线本身**（抽取质量加分层加载的召回），基线越低的集成提升越猛——Claude Code 自带记忆不弱，所以只从 57.21% 到 80.32%；token 和延迟的下降则更多归功于"只注入摘要层而非全文"的加载策略，这部分换任何分层方案都可能复现。不能推出的：这些数字不等于你的业务问答准确率（LoCoMo 是英文长对话事实问答，域差很远）；tau2-bench 的增益来自经验记忆对特定客服流程的适配，换任务类型需要重测。另外这组数据来自项目方自测，VLM 用豆包 2.0 Pro，embedding 用 Doubao-embedding-vision-251215，模型栈偏自家生态，量级趋势可信，具体数字建议用自己的场景复测。

## 上手路径

先起服务，再接 Agent，两条路各自都有"让 Agent 自己干"和"手动"两种做法。

**起服务**需要 Python 3.10+ 和一个带 embedding 模型与 VLM 的模型供应商：

```bash
uv tool install openviking --upgrade && openviking-server init
openviking-server doctor    # 校验配置与连通性
openviking-server           # 前台启动，保持终端开着
```

`init` 交互式配置模型并写入 `~/.openviking/ov.conf`，支持 Volcengine、OpenAI、Codex OAuth、Kimi、GLM 和本地 Ollama（可自动检测并拉取模型）。不想管环境有两条捷径：README 顶部提供了 Railway 一键部署；火山引擎也托管了同版服务（OpenViking Service，前 50 个文件免费），服务端地址和 API key 在控制台拿。

**用 CLI 探一圈**。`ov` 命令随 Python 包附带——它实际是 Rust 原生二进制的极简包装（仓库 `crates/ov_cli`，Apache 2.0 单独授权，也可经 npm 包 `@openviking/cli` 或 cargo 独立安装）。导入资源是异步的，注意轮询任务状态：

```bash
ov status
ov add-resource https://github.com/volcengine/OpenViking
ov task status TASK_ID      # 重复执行直到 completed，再检索
ov tree viking://resources/volcengine -L 2
ov find "what is openviking"
ov grep "openviking" --uri viking://resources/volcengine/OpenViking/docs/en
```

**接 Agent**。官方安装脚本自动探测本机已有的编码 Agent 并注入记忆插件：

```bash
curl -fsSL https://openviking.ai/install | bash
```

脚本需要 macOS 或 Linux、Node.js 18+，无需 sudo；Windows 走桌面应用（Beta，另有配置集成、查看召回事件、同步本地记忆技能的功能）。具名集成覆盖 Claude Code、Codex、Cursor、TRAE（Hooks + MCP）、OpenClaw（作为上下文引擎内置）、Hermes（原生内置）、OpenCode、pi、DeerFlow、LangChain 等，也支持任意 MCP 客户端。装完重启 Agent，验证方式就是上一节那个偏好实验。

**再进一步**还有两个可选件：VikingBot（`pip install "openviking[bot]"` 后 `openviking-server --with-bot`，官方 Docker 镜像默认捆绑），它带来 `ov compile`——把导入的素材整理成 wiki、知识图谱或报告；以及三套官方 SDK（Python / Go / TypeScript）和 HTTP API，供自建集成。零安装的体验入口仍是 [OpenViking Studio](https://openviking.ai/studio) 在线演示，Web 版 Studio 也可自托管。

## 生产部署与许可证边界

开源版在生产上不缺关键件：支持多租户（Account / user / peer 三级隔离）、可选的资源 ACL 和认证（对外暴露前必须配），v0.4.22 又加了 Cluster / Account 两级运行时配置，改 VLM、embedding、向量后端不用改配置文件重启，向量后端同版新增了 openGauss DataVec 选项；Skill 检索也改成了整包索引、每个技能只返回一条最佳命中。

许可证要看清楚，它是**按组件分的**：主项目 AGPLv3（自部署无需激活码，但闭源商用有传染性约束）；`crates/ov_cli` 和 examples 是 Apache 2.0（examples 里的 Hermes 插件为 MIT）。闭源商用有两条官方出路：火山引擎的托管 SaaS（Personal / Enterprise 套餐，海外托管在计划中，将由 BytePlus 承载），或 Self-Managed 商业版（部署在自己的 VPC 或离线环境，license key 激活，含分布式部署与官方支持）。学术侧，核心能力有三篇论文背书：VikingMem 记忆管理（VLDB 2026）、目录感知检索（ICDE 2026）、VikingRAG（arXiv 投稿中），README 的 Research 一节给了链接。

## 适用与不适用

**适合**：长期运行的 Agent 需要跨会话记忆；知识库规模大到"一次检索塞不下上下文"；需要调试检索过程的团队。

**需要斟酌**：主项目 AGPLv3 对闭源商用有传染性约束（组件许可见上节）；L0/L1 摘要和记忆抽取都依赖 LLM，写入侧有持续的模型调用成本；检索不做目录递归下钻，如果你的场景真的需要"先浏览目录结构再人工深挖"，当前检索面给的是范围限定而非路径遍历；小规模场景（几十个文档的一次性问答）用不上这套机制，普通 RAG 反而更简单。

## 结论：按这个顺序试

OpenViking 的真正贡献不是某个算法，而是把"上下文工程"从流水线拼接提升到数据库范式：统一编址、分层加载、范围化检索、会话自动沉淀。即便不直接采用，viking:// 文件系统隐喻和目录级摘要设计也能回答"记忆系统到底该长什么样"。

要上手，建议的顺序是：先开 [OpenViking Studio](https://openviking.ai/studio) 转一圈建立直觉——浏览目录、跑两条语义查询，判断这套范式对不对你的胃口；对了，再自部署单机版接你常用的编码 Agent，跑一次上一节的偏好实验验证跨会话记忆；团队场景下一步是多租户加 ACL，同时评估写入侧的模型成本；闭源商用在这个节点再谈托管 SaaS 或商业版授权。给 Agent 做长时程记忆的团队可以现在就深入，把它和 [DeerFlow](../bytedance-deer-flow-long-horizon-superagent-guide/) 这类长时程 harness 配合使用是官方认可的组合（后者在 OpenViking 的 Partner Projects 名单里）；纯一次性问答场景不必跟进。
