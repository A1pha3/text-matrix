---
title: "codebase-memory-mcp 架构拆解：用 C + tree-sitter 把代码库做成可查询的图"
date: "2026-06-18T15:05:00+08:00"
lastmod: "2026-09-19T11:40:00+08:00"
slug: "deusdata-codebase-memory-mcp-code-intelligence-guide"
github_repo: "DeusData/codebase-memory-mcp"
source_key: "gh:DeusData/codebase-memory-mcp"
description: "以 v0.11.0 为准拆解 codebase-memory-mcp：162 个 vendored tree-sitter grammar、自研 Hybrid LSP、RAM-first 索引管道、SQLite 图存储与 openCypher 读子集，并核对 README、论文 arXiv:2603.27277 与源码三处口径的差异。"
draft: false
categories: ["技术笔记"]
tags: ["MCP", "tree-sitter", "知识图谱", "AI 编程"]
---

## 先给判断：它省掉的不是 grep，而是"把相关文件读一遍"

`DeusData/codebase-memory-mcp` 把仓库解析成一张持久化的属性图，节点是函数、类、路由，边是调用、导入、继承，然后通过 MCP（Model Context Protocol，模型上下文协议）把这层结构暴露给编码智能体（agent）。它省掉的不是文本搜索，而是"为了回答一个结构问题而把相关文件全读一遍"的开销。

这篇的目标只有一个：给出一套判断同类代码情报工具的依据。要回答三件事——四层各自解决什么工程问题、一次问答实际流过哪些工具、论文里那三个数字能被读到哪一步。

结论先摆在这里。值得盯的地方不在速度，而在它把"用结构检索换回答质量"这笔交易做成了可复核的具体数字：论文表 6 里图谱方案 0.83 的回答质量，对应文件遍历基线 0.92，代价 7 个百分点，换来每问约 1,000 词元（token）对约 10,000 词元。速度是真的，退化也是真的，而 README 只写了前者。

## 目录

- [先给判断：它省掉的不是 grep，而是"把相关文件读一遍"](#先给判断它省掉的不是-grep而是把相关文件读一遍)
- [系统地图：四层里只有两层写在 README 里](#系统地图四层里只有两层写在-readme-里)
- [版本口径：这份 README 同时住着三套数字](#版本口径这份-readme-同时住着三套数字)
- [L1 解析层：162 个 grammar，和一层不挂 language server 的类型解析](#l1-解析层162-个-grammar和一层不挂-language-server-的类型解析)
  - [grammar 数量去数文件树，别数措辞](#grammar-数量去数文件树别数措辞)
  - [Hybrid LSP 是自己重写的，不是接别人的 language server](#hybrid-lsp-是自己重写的不是接别人的-language-server)
- [L2 索引管道：内存里建图，结束时落盘一次](#l2-索引管道内存里建图结束时落盘一次)
- [L3 存储与查询：13 个 label、两份边清单、一个会报错的 Cypher 子集](#l3-存储与查询13-个-label两份边清单一个会报错的-cypher-子集)
  - [边类型：README 的两张表互相缺项](#边类型readme-的两张表互相缺项)
  - [openCypher 读子集：默认 100,000 行上限](#opencypher-读子集默认-100000-行上限)
- [L4 工具面：注册表里 17 个，README 里 15 个，表格里 14 个](#l4-工具面注册表里-17-个readme-里-15-个表格里-14-个)
- [一次真实问答怎么穿过这四层](#一次真实问答怎么穿过这四层)
- [基准怎么读：83% 是低于基线的那个数字](#基准怎么读83-是低于基线的那个数字)
- [分发与安全的真实形状：49 个资产、一份 postinstall、两处互相矛盾的说法](#分发与安全的真实形状49-个资产一份-postinstall两处互相矛盾的说法)
- [最小配置示例](#最小配置示例)
- [按现象查：六个常见报错和它们的处置](#按现象查六个常见报错和它们的处置)
- [谁该现在就上，谁可以再等等](#谁该现在就上谁可以再等等)
- [五个自测题](#五个自测题)
  - [题 1：为什么说 Hybrid LSP 不等于"接一个 language server"](#题-1为什么说-hybrid-lsp-不等于接一个-language-server)
  - [题 2："83% answer quality"能不能作为"质量足够好"的证据](#题-283-answer-quality能不能作为质量足够好的证据)
  - [题 3：10× 词元和 120× 词元削减矛盾吗](#题-310-词元和-120-词元削减矛盾吗)
  - [题 4：想确认"这个函数真的没有调用者"，正确动作是什么](#题-4想确认这个函数真的没有调用者正确动作是什么)
  - [题 5：为什么说"单一静态二进制、没有脚本胶水"在 v0.11.0 已经不成立](#题-5为什么说单一静态二进制没有脚本胶水在-v0110-已经不成立)
- [练习：拿你自己的两个仓库跑一遍](#练习拿你自己的两个仓库跑一遍)
- [下一步读哪份源码](#下一步读哪份源码)
- [资料口径与复核方法](#资料口径与复核方法)
- [参考资料](#参考资料)

## 系统地图：四层里只有两层写在 README 里

项目的 `README.md` 只描述了两层：tree-sitter 语法解析和 Hybrid LSP 类型解析。要把一个压缩包就近 40 MB 的东西讲清楚，得按数据形态再切两刀。下面的四层是本文的阅读框架，不是项目的官方分层；每层右边给出的是 `src/` 下真实存在的目录。

```text
┌───────────────────────────────────────────────────────────────┐
│ L4 工具面   src/mcp（JSON-RPC 服务）+ src/cli（45 个客户端面） │
│             注册 17 个工具，按 --tool-profile 分档暴露         │
├───────────────────────────────────────────────────────────────┤
│ L3 存取     src/store（SQLite 图存储）+ src/cypher（解析执行） │
│             13 个节点 label · openCypher 读子集 · WAL 落盘     │
├───────────────────────────────────────────────────────────────┤
│ L2 索引     src/pipeline（多趟）+ src/discover + src/watcher   │
│             RAM-first · LZ4 · Aho-Corasick · 结束时单次 dump   │
├───────────────────────────────────────────────────────────────┤
│ L1 解析     internal/cbm（162 个 grammar + 抽取器）+ src/semantic │
│             语法层覆盖全部语言 · 类型层只覆盖 10 种            │
└───────────────────────────────────────────────────────────────┘
```

另有三个跨层的运行件：`src/daemon` 是每账户一个的协调守护进程，多个客户端会话共用它，监视器、共享索引任务和可选 UI 都挂在它身上；`src/foundation` 封装线程、文件系统、日志与内存；`src/ui` 是本地 HTTP 服务，加上经校验的 3D 前端资产包。

分层带来的第一个判断依据：**性能声明必须落到具体层上**。"亚毫秒查询"属于 L3，"3 分钟索引 Linux 内核"属于 L2，"162 种语言"属于 L1，"15 个工具"属于 L4。一句宣传语里混着四层的数字时，先拆开再评估。

## 版本口径：这份 README 同时住着三套数字

同一份 `README.md` 里，语言数量出现在四个位置，其中三个说 162，一个说 158。工具数量出现在四处，全都说 15，而 `src/mcp/mcp.c` 的 `TOOLS[]` 注册表有 17 项，README 自己的工具表格只列了 14 行。

这不是谁抄错了，而是一个高速迭代仓库在文档里留下的地质层：从 2026-02-24 建库到 2026-09-15，GitHub 上一共挂着 47 个 release，3 月单月发 22 个，7 月只发 2 个，最近一个是 9 月 15 日的 v0.11.0。把三个时间点的口径并排放：

| 口径 | 论文 v1（2026-03-28） | README @ v0.9.0 | README @ v0.11.0 | v0.11.0 实物 |
|------|----------------------|-----------------|------------------|--------------|
| 语言数 | 66 | 158 | 162（另一处仍写 158） | `internal/cbm/grammar_*.c` 计 162 个 |
| Hybrid LSP 语言 | — | 9 | 10（新增 Perl） | 表格 10 行 |
| MCP 工具 | 14 | 14 | 15 | `TOOLS[]` 17 项；README 表格 14 行 |
| 客户端面 | 自动检测 10 个 | 11 | 45（39 自动 + 6 条件） | 表格逐行列名 |
| 测试 | — | 徽标 5,604 passing | 徽标 6,768 / 正文 120 套 | — |
| 分发形态 | — | single static binary | 可执行文件 + 经验证的运行资产集 | 49 个 release 资产 |

三套数字带来的实操结论很直接：**任何被引用的计数都要带版本号和取证方式**。写"158 种语言"的文章不一定读错了，它可能读的是 2026 年 6 月的 v0.9.0；但读者拿它去对照今天的发布物就会失配。想固定口径，唯一可靠的做法是数实物——文件树、注册表数组、release 资产清单，这三样都比措辞稳定。

顺带一条：v0.9.0 的 README 里，客户端徽标写 11、架构图里那行管命令行工具安装的 `src/cli` 注释写 10。同一天的文档内部就已经不一致了。

## L1 解析层：162 个 grammar，和一层不挂 language server 的类型解析

### grammar 数量去数文件树，别数措辞

所有 grammar 以 vendored 方式编译进二进制，落地形态是 `internal/cbm/grammar_<语言>.c` 一组文件。在 v0.11.0 上数，正好 162 个，和 README 的"162 languages"以及架构注释一致；那处残留的"158 vendored tree-sitter grammars"是索引流水线一节的旧句。

把 grammar 编进二进制换来两件事：CI 和离线机器上不会出现"运行时下载失败"，以及分发物里没有可供篡改的下载源。代价是体积——`codebase-memory-mcp-darwin-arm64.tar.gz` 在 v0.11.0 是 39.21 MB，解压前就这么大。对只做文本搜索的工具来说这个体积很难接受，对"索引一次、反复查询"的工具来说是一次性成本。

覆盖度不等于质量。README 的 `Language Support` 一节承认这 162 种只有一部分经过基准测试：`docs/BENCHMARK.md`（v0.3.0，2026-03-01，Apple M3 Pro）按 12 类问题给每种语言打分，PASS 计 1.0、PARTIAL 计 0.5、FAIL 计 0.0，最后分成 Excellent（≥90%，17 种）、Good（75–89%，16 种）、Functional（<75%，2 种：OCaml 72%、Haskell 62%）。这份文档的方法论一节写"63 languages"，可它的汇总表只有 35 行、跨 34 个不同仓库，分档表的 17 + 16 + 2 也正好是 35；README 再把同一轮测试转述成"64 real open-source repositories"。三个数字互不相等，读这类覆盖度声明时先去找那张逐语言的表，别停在摘要行上。

### Hybrid LSP 是自己重写的，不是接别人的 language server

这一层最容易被误读的地方，是把 Hybrid LSP 理解成"去连一个现成的 language server"——它同时也是"团队要不要按语言装齐十种 server"这个决策的前提。

tree-sitter 只给你语法树。它能告诉你这里有个调用写着 `user.profile.display_name()`，不能告诉你它落到三个模块外的 `Profile.display_name`——导入、泛型、继承、标准库类型它都不追。

codebase-memory-mcp 的补法不是去连语言服务器，而是**用 C 重写一份类型解析算法**，README 的原话是"a lightweight C implementation of language type-resolution algorithms, structurally inspired by and compatible with major language servers"，点名对齐 tsserver / typescript-go、pyright、gopls、Roslyn、Eclipse JDT、rust-analyzer，并且明确写着"No language server process, no per-project setup, no API key"，直译过来是不需要 language server 进程、不需要逐项目设置、不需要应用程序接口（API）密钥。它每趟解析都跟 tree-sitter 一起跑，把 `CALLS` 细化成可判定的边，把无法唯一确定目标的调用降级为 `USAGE`。

有完整类型解析的 10 种语言（v0.11.0）：Python、TypeScript / JavaScript / JSX / TSX、PHP、C#、Go、C / C++、Java、Kotlin、Rust、Perl。其中 Python、PHP、C# 是 v0.7.0 加入，Go 与 C / C++ 在同一版被加强，Java、Kotlin、Rust 在 v0.8.0 加入。没有类型解析的语言不会报错，README 的说法是回落到文本解析，"so you always get some answer"——注意这句话的分寸：回落出来的边可能错，只是不会空。

Python 那一行的目标值可以直接引用：README 写"Target ~95% resolution on idiomatic code"。这是自报目标，不是测量结果。同一层在论文里的实测最低点是宏密集的 C，0.58——"95% 目标"和"0.58 实测"并排看，才是这层的真实边界。

## L2 索引管道：内存里建图，结束时落盘一次

README 的"极致速度"来自三个选择，值得逐个还原成"它省掉了什么"：

- **RAM-first**：整趟索引在内存里完成，读取用 LZ4 HC 压缩，图存储用内存 SQLite，最后一次性 dump 到磁盘，之后把内存交还操作系统。省掉的是索引过程中的随机写。
- **融合 Aho-Corasick**：多种模式匹配合成一趟扫描，代码在 `internal/cbm/ac.c`。省掉的是对同一文件反复跑多轮正则。
- **多趟流水线**：`src/pipeline` 按结构 → 定义 → 调用 → HTTP 链接 → 配置 → 测试的顺序推进，`src/discover` 负责文件发现（硬编码排除 → `.gitignore` 层级 → `.cbmignore`，符号链接一律跳过）。

已公开的耗时都标在 Apple M3 Pro 上：Linux 内核全量索引 3 分钟（28M LOC / 75K 文件 → 481 万节点、772 万边），fast 模式 1 分 12 秒（188 万节点），Django 约 6 秒（4.9 万节点、19.6 万边）；查询侧 Cypher 亚毫秒、正则名搜索 10 毫秒内、死代码检测约 150 毫秒、深度 5 的调用路径追踪 10 毫秒内。论文另给一条：靠 XXH3 内容哈希做增量重建，比全量重建快约四倍。

这一层有个容易被忽略的诚实设计，值得抄进任何索引类工具。索引结束后会比较"落盘的节点数"和"内存里提交的节点数"，比例低于 `CBM_DUMP_VERIFY_MIN_RATIO`（默认 0.5，且提交数 > 50）时，`index_repository` 返回 `status: "degraded"` 而不是照常报 `indexed`。也就是说它不把"悄悄掉了一半节点"当成成功。

内存预算不是无限的：默认按 `ram_fraction × 总内存` 推算，可用 `CBM_MEM_BUDGET_MB` 压低，`CBM_WORKERS` 限制并行度——容器里尤其要显式设，因为 `sysconf(_SC_NPROCESSORS_ONLN)` 看到的是宿主机核数而不是 cgroup 配额。README 没有给出不同仓库规模对应的内存实测值，想在自己的机器上判断，只能自己按 `docs/MEASURING_SAVINGS.md` 的路子测。

## L3 存储与查询：13 个 label、两份边清单、一个会报错的 Cypher 子集

图存在 SQLite 里，默认落在缓存根目录 `~/.cache/codebase-memory-mcp/` 下，开 WAL 模式，重启不丢；要重置就 `rm -rf` 这个目录。只读查询路径对坏库的处理写在 `src/mcp/mcp.c` 的注释里：报告问题、原样留着，不隔离也不重建，重建只发生在写入侧——这正是它敢给十个纯查询工具标 `readOnlyHint=true` 的依据。一个账户同一时刻只认一个规范 cache root，其他会话还活着时换根会被拒。

节点 label 在 README 的 `Graph Data Model` 一节列了 13 个：`Project`、`Package`、`Folder`、`File`、`Module`、`Class`、`Function`、`Method`、`Interface`、`Enum`、`Type`、`Route`、`Resource`。`Route` 和 `Resource` 是这套模型跟普通符号索引真正分开的地方：路由端点被当成一等实体，`Dockerfile`、Kubernetes manifest、Kustomize overlay 也被建成节点，overlay 用 `Module` 节点带 `IMPORTS` 边指向被引用资源。

### 边类型：README 的两张表互相缺项

`Graph Data Model` 一节枚举 19 种边；另一节"Edge types (selected)"列出 14 种，其中 6 种（`DATA_FLOWS`、`EMITS`、`INHERITS`、`LISTENS_ON`、`SEMANTICALLY_RELATED`、`SIMILAR_TO`）不在那 19 个里。再往 `src/pipeline` 的 `insert_edge` 字面量里看，还有 `DECORATES`、`GRPC_CALLS`、`GRAPHQL_CALLS`、`TRPC_CALLS`、`DEPENDS_ON`、`OVERRIDE`、`INFRA_MAPS` 等类型，README 两处都没写。

对读者的处置建议只有一条：**别从 README 抄边类型清单，跑 `get_graph_schema`**。README 给这个工具写的说明正是"Node/edge counts, relationship patterns, property definitions per label. Run this first."——每个节点 label 有多少、边有哪几种形状、属性怎么定义，它返回的是当前索引实际生成的那份，比任何一份文档都新。

### openCypher 读子集：默认 100,000 行上限

`query_graph` 实现的是 openCypher 的只读子集。支持 `MATCH` / `OPTIONAL MATCH` / 多 `MATCH`、`WHERE`、`WITH`（含 `WITH … WHERE`）、`RETURN`、`ORDER BY`、`SKIP`、`LIMIT`、`DISTINCT`、`UNWIND`、`UNION [ALL]`、`CASE`；模式侧支持带 label、label 交替 `(n:A|B)`、关系类型与方向、变长路径 `[*1..3]`、内联属性映射；聚合有 `count` / `sum` / `avg` / `min` / `max` / `collect`。写操作、`MERGE`（合并写入子句）、`CALL` 子句和参数化一律不支持。

这里有一个对写 agent 提示词很关键的取舍：子集外的语句不会静默返回空集，而是报明确的 `unsupported …` 错误。宁可让模型看见失败，也不要让它拿空结果去推断"没有调用者"。

一条真实的历史教训：`docs/BENCHMARK.md` 在 Linux 内核 `drivers/net/ethernet/intel/` 子集上测 properties 那一问时，`IS NOT NULL` 当时不支持，判 PARTIAL、用了 2/5 次重试才改写成功；今天的 README 已经把 `IS [NOT] NULL` 列进 `WHERE` 支持表。同一份查询在两个版本间从失败变成支持——这是"以 `--help` 和 `get_graph_schema` 为准"的又一个理由。

规模上限记一下：论文在 construct validity 里写明 `query_graph` 默认 100,000 行封顶，超大库里会低计。

## L4 工具面：注册表里 17 个，README 里 15 个，表格里 14 个

`src/mcp/mcp.c` 的 `TOOLS[]` 在 v0.11.0 注册 17 项，按用途分组：

| 组 | 工具 | 一句话 |
|----|------|--------|
| 索引 | `index_repository` `list_projects` `index_status` `delete_project` | 全量/增量入库与生命周期 |
| 结构检索 | `search_graph` `search_code` `get_code_snippet` `get_file_outline` | 前者按 label / 正则名 / 度数 / 文件范围过滤，后者是已索引文件内的 grep |
| 关系 | `trace_path` `query_graph` `get_graph_schema` `compare_graphs` `detect_changes` | BFS 调用追踪（深度 1–5，`trace_call_path` 是别名）、Cypher、模式自省、两图对比、git diff 映射到受影响符号与风险分级 |
| 全局视图 | `get_architecture` `check_index_coverage` `manage_adr` `ingest_traces` | 仓库概览、覆盖缺口、架构决策记录、运行时 trace 校验 |

三处计数分别是 17 / 15 / 14，差异都真实存在：`get_file_outline`、`compare_graphs`、`check_index_coverage` 三个进了注册表但没进 README 的工具表格。`ingest_traces` 的自述也值得注意——"Validate and count traces; graph edge creation is not implemented"，它只做校验和计数，不建边。

`--tool-profile` 决定实际可见面：`scout` 与 `analysis` 两份白名单在源码里分别有 8 项和 13 项，README 却写"seven"和"eleven"。这三档对应 install 生成的三种子代理，官方定义写得很克制：Scout 只给三到四次窄调用做正向的初步发现，并且明确"不做缺失、穷举影响或死代码这类断言"；Verify 是默认档，要求每个被引用的文件都有路径覆盖；Auditor 才在受限范围里查更宽的关系，并把仍未解决的限制显式写出来。这套分档本身就是判断依据——**"没搜到"和"确认不存在"是两个工具，别让 agent 用前者冒充后者。**

还有一条设计决定值得单独看：codebase-memory-mcp 内部不含大语言模型（LLM）。README 的解释是，别的代码图谱工具会内置一个模型把自然语言翻成图查询，那就要多一个 API key、多一份开销、多一个要配的模型；有了 MCP，你已经在对话的那个 agent 就是查询翻译器。这解释了为什么它敢说"零 API key"，也解释了为什么回答质量的上限同时受宿主模型约束——论文里那 0.83 就是在单一后端（Claude Opus 4.6）上测的。

## 一次真实问答怎么穿过这四层

工具名和参数对上之后，下一个问题是"一次问答的中间态长什么样"。项目自己留下了可核对的记录：`docs/BENCHMARK.md` 里 v0.3.0 对 Linux 内核 `drivers/net/ethernet/intel/` 子集做的 12 问，每一问都写了用的哪个工具、第几次尝试通过、返回多大。

被索引的对象是 387 个 C/H 文件，建出 19,993 个节点、67,305 条边，label 分布里 `Function` 11,546、`Class`（内核里的 struct）1,851、`Method` 1,803、宏 1,346、字段 1,095、社区 734、`Enum` 480、变量 461。

拿"谁调用了 `e1e_rphy`"这一问看数据怎么流：

1. 你对 agent 说这句话。agent 判断这是入边问题，调 `trace_path(function_name="e1e_rphy", direction="inbound", depth=5)`。
2. L3 的 `src/store` 走 SQL 递归 CTE 做 BFS，L4 把结果压成紧凑树。实测返回 67,600 字符，含 64 个直接调用者和若干深层链，1 次尝试即通过（表中标 1/5）。
3. 反方向那一问更有说服力：`i40e_probe` 出度 59，深度 5 的正向追踪返回 129,026 字符，没有超时。
4. agent 拿结构化结果用自然语言回你。图这边全程不请求模型，也不发网络包。

三个可迁移的观察。**第一，词元省在"不必读源码"上**：这 6.7 万字符是关系列表，不是文件正文；换成正向探索，agent 得把调用者所在的文件一篇篇读进来。**第二，紧凑树不是省字节的花招**：CLI 输出允许把重复路径前缀抽成一份 `<section>_refs` 目录，单元格写 `@0+handler.go` 再由调用方还原；README 说这条只在渲染后的表格至少小 15% 且 64 字节、同时词元形状代理也改善 1% 以上时才启用——它是算过账的。**第三，失败会显形**：同表里 properties 那一问当时判 PARTIAL（`IS NOT NULL` 不支持），第 2 次尝试改写才通过。一个会返回 PARTIAL 的工具比一个总是返回"看起来完整"结果的工具好审计。

至于跨会话，索引不是一次性的：`src/watcher` 用 git 轮询做增量同步，`auto_index`（默认关）打开后新项目在连接时自动索引，`auto_index_limit` 默认 50,000 文件。团队共享则走另一个机制——`.codebase-memory/graph.db.zst`，一个 zstd 压缩的图快照，官方口径 8–13:1，分 Best（`zstd -9` + 剥索引 + `VACUUM INTO`，显式 `index_repository` 时写）和 Fast（`zstd -3`，watcher 写）两档。这个文件每次索引都会被重写，git 会把每次重写存成一个完整新 blob，README 记了一个真实教训：某团队只对这一个路径提交，约 350 次提交后仓库涨到约 6 GB。要频繁移动它就得走 Git LFS，并接受 LFS 的存储计量和"队友没装 git-lfs 时会退化成一次全量重建"。

## 基准怎么读：83% 是低于基线的那个数字

论文 `arXiv:2603.27277`（2026-03-28 提交，5 位作者，分类 cs.SE / cs.AI / cs.PL）的表 6 是全部故事的原始出处；arXiv 页的 Comments 一栏写的是"10 pages, 5 authors, preprint"，期刊字段留空。实验设置：两个 agent 配置对照，一个带 codebase-memory 的 14 个工具，一个是常规文件读取加 grep 的 Explorer，同一批问题，两边都用 Claude Opus 4.6 作后端；打分由第一作者按人工检查代码得出的参考答案给连续 0–1 分，≥0.80 记 PASS、0.40–0.79 记 PARTIAL、<0.40 记 FAIL。

| 指标 | 图谱 agent | Explorer 基线 | 差值 |
|------|-----------|---------------|------|
| 质量分 | 0.83 | 0.92 | 90% of Explorer |
| 每问工具调用 | 2.3 | 4.8 | 少 2.1 倍 |
| 每问词元 | 约 1,000 | 约 10,000 | 少 10 倍 |
| 查询延迟 | <1 ms | 10–30 s | 快 >100 倍 |

先说测的是什么：31 种语言各配一个真实开源仓库，问题分 12 类。所以"31 个仓库"的单位不是 31 个独立样本，而是"语言 × 问题类"的网格；README 把它转述成"Evaluated across 31 real-world repositories"，模糊了这一点。

再说三个数字各自能撑到哪一步：

- **83% 对 92% 是一次退化，不是一次胜利。** 论文正文的说法是"achieves 90% of the Explorer Agent's quality score"。README 的引言只保留"83% answer quality"，读者很容易读成达到 83% 的可用水准。正确的读法是：这是一笔用质量换成本的交换，而 7 个百分点花在了哪类问题上，论文答了——需要整段源码上下文和穷举式模式匹配的问题，Explorer 仍占优；图谱在枢纽识别与调用者排名上于 19/31 种语言持平或更好。
- **"10 倍词元"是论文自己的约 1,000 对约 10,000，跟 README 的另一组数字不是一回事。** README 的 Performance 一节写"五次结构查询约 3,400 词元对约 412,000 词元"，并据此报"99.2% 削减 / 120x fewer tokens"。3,400 与 412,000 的比值是 121 倍，不是 10 倍。两组数字口径不同（每问均值对五次查询合计、不同基线），只能各自引用，不能互相换算。
- **"快 100 倍"带一个括号条件。** 表 6 那行的原文是">100 times faster (10/31)"，紧接着解释：这 10 问需要的是图刻意不存的行级代码。把括号去掉就成了无条件的百倍。

论文自己列的效度威胁都在这里落地了：单一模型后端，结论不保证跨模型或跨提示策略成立；打分来自第一作者而非盲评或独立人工或 LLM 裁判；分档阈值"chosen pragmatically"，换阈值会挪动分布；图只表达静态结构，运行时行为、反射和动态派发不在内；除嵌入向量（embedding）类检索增强生成（RAG）、ctags / LSP 和其他图系统之外的对比"remains future work"。也就是说，**目前没有任何一份已发表数据说它比 RAG 或 LSP 好**——它比较过的只有一件事：同一个模型，给图，或者给文件。

最差的样例比平均值有用：宏密集的 C，0.58 对 1.00。论文给的原因是宏在 tree-sitter 的 AST 里不存在。内核子集那份统计里宏确实被建成了 1,346 个节点，也就是定义进来了；分数丢在哪里，按论文的说法就是丢在宏展开之后才出现的那些调用上。

至于 README 反复强调的速度类数字（3 分钟索引内核等），目前只有项目自报，没有跨工具独立复现。更值得参考的是 `docs/EVALUATION_PLAN.md`：它给自己的定性是"plan, not a result set"，不含任何分数，要把论文的人工打分换成盲评的 LLM-as-a-Judge——随机 A/B 顺序、判官对 Graph 还是 Explorer 不知情、按答案引用量抽验至少 30% 的符号与路径、无法在源码里确认的断言把 Correctness 压到 0.5，并且直接写明同源模型当判官带着 10–25% 的自我偏好膨胀。一份计划愿意先把自家测量的偏置写进文档，比任何一句"性能卓越"都有信息量。

## 分发与安全的真实形状：49 个资产、一份 postinstall、两处互相矛盾的说法

代码情报工具的威胁模型特殊：它读你的全部源码，还写你的 agent 配置。项目在这块的动作比同类多，但"单一静态二进制、没有脚本胶水"这个说法在 v0.11.0 已经不成立，值得逐条摆清。

已核实的分发事实：v0.11.0 有 49 个 release 资产；除 tar.gz / zip 外还有 `.mcpb`（MCP Bundle）格式，darwin-amd64 的 `.mcpb` 与 `.tar.gz` 同为 39.73 MB；每个 release 带 `checksums.txt`（SHA-256），两个安装脚本在解包前都会校验。安装渠道除 GitHub 外还有 npm、PyPI、Homebrew、Scoop、Winget、Chocolatey、AUR 和 `go install`。

npm 那条渠道值得单独看，因为"没有 npm 依赖链可被供应链攻击"这句流行结论只对了一半。`codebase-memory-mcp@0.11.0` 的包体只有 4 个文件、34,800 字节、无 dependencies，`engines` 要 `node >= 18`——依赖链确实干净。但它声明了 `"postinstall": "node install.js"`，那个脚本 683 行，从 `https://github.com/DeusData/codebase-memory-mcp/releases/download/v<版本>/<archive>` 下载二进制，再拉同版本的 `checksums.txt` 逐个比对摘要，先落到同文件系统的私有暂存目录，再按文件原子改名。这是"安装期联网执行下载"的标准形态，防护做得算到位，但和"零下载"不是一回事。信任边界只是从 npm 依赖树移到了 npm 包自身的发布权限。

构建与验证链上，SECURITY.md 和 README 说法一致的部分有这些：

- SLSA Build Level 3 构建溯源，**作用域是 release 压缩包**，README 直接给了 `gh attestation verify` 的用法。
- Sigstore cosign 无密钥签名，SPDX 格式的 SBOM，每个 release 一份 `checksums.txt`。
- CodeQL 只要还有未处理告警就阻断发布。
- 每次构建跑 8 层安全审计：strace 监控网络外发、校验 `install.sh` / `install.ps1` 的输出路径与内容、23 个对抗性 JSON-RPC 载荷、核对 vendored 依赖摘要、在危险调用附近扫 `time()` / `sleep()` 找延迟激活模式。
- 对 MCP 工具处理器的文件读取次数做基线核对，多出预期读取即失败。
- 构建期跑本机杀毒扫描：Windows 用 Defender，Linux 与 macOS 用每日更新的 ClamAV，任一检出即构建失败。

VirusTotal 的策略比"每个 release 都被扫一遍"精细，也更值得读：每个发布产品从同一次链接输出派生三个行为等价的候选（未 strip、去调试符号、全 strip），发布前全部送扫；优先要求零恶意零可疑，唯一被容忍的结果是恰好一个以 `!ml` 结尾的 Microsoft 恶意标签，且必须披露；选中的那个候选在不改 SHA-256 的前提下打包；打包后连 `install.sh`、`install.ps1`、`LICENSE`、`THIRD_PARTY_NOTICES.md`、MCPB 的 `manifest.json` 和解压后的 UI 资产一起送扫，逐候选证据以 TSV 随 release 发布。README 与 SECURITY.md 在这里也对不上：前者说八个发布产品的 24 个候选，后者说 14 个交付容器。

关于那个 `!ml`：Microsoft Defender 会把 release 二进制判成 `Trojan:Script/Wacatac.B!ml`。SECURITY.md 的处理是三件事——说明 `!ml` 是启发式/机器学习分类而非特征码命中，给出实测"同一文件通常 62 个引擎里 61 个返回干净"，并且指出同一族检测也命中过 `gh`、llama.cpp、Godot 和微软自己的 Go 工具链，然后明确拒绝为绕过它而做混淆。企业内网上线前，这一条会真的咬人，先读它。

最需要留神的一处，是两份一手文档直接互斥。README 的 `Keeping Up to Date` 写着"cbm makes no network request of its own accord — it does not check for new versions in the background, and nothing phones home"；同一版本的 SECURITY.md 在 `Runtime Network Behavior` 写着 MCP `initialize` 之后会起一个后台更新检查线程，向 `https://api.github.com/repos/DeusData/codebase-memory-mcp/releases/latest` 请求 release 元数据，`curl --max-time 5` 限时，离线则忽略，且不发项目数据。README 的说法更强，SECURITY.md 说得更细；README 的环境变量表里也没有关掉这个检查的开关，`CBM_DOWNLOAD_URL` 只改下载源。要断网部署，就按 `api.github.com` 出向来审计，别按 README 那句话假设没有出站请求。

"100% 本地处理、代码不出机器"这句在两份文档里都成立——索引、查询、语义检索和 MCP 处理都在本地，不上报源码、仓库路径、图索引、查询内容或用量。它的反面同样值得记住：正因为不采遥测，维护者手上没有任何现场数据，所以 README 专门写了一套自采方法——`CBM_DIAGNOSTICS=1` 后由守护进程在私有临时目录写 `trajectory.ndjson`，每 5 秒一行 `rss` / `committed` / 峰值 / 缺页 / 文件描述符 / 查询数，退出后仍保留。报内存泄漏要附这个文件，它不含源码和查询文本。

## 最小配置示例

三条真实可运行的路径，都取自 v0.11.0 的 README 与 `docs/CONFIGURATION.md`。

一键安装（macOS / Linux），会顺带配置检测到的客户端：

```bash
curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash
```

只想手动配 Claude Code，不改任何 agent 的全局行为，加 `--skip-config`，或者自己写条目。用户级写 `~/.claude.json`，项目级写 `.mcp.json`：

```json
{
  "mcpServers": {
    "codebase-memory-mcp": {
      "command": "/path/to/codebase-memory-mcp",
      "args": []
    }
  }
}
```

验收：重启 agent 后执行 `/mcp`，能看到 `codebase-memory-mcp`。工具数量以 `/mcp` 报出来的那个为准，别拿本文或 README 的数字当预期——15 和 17 各自是某个口径下的真值。

不开 UI 时它默认不监听端口，需要时显式起：

```bash
codebase-memory-mcp --ui=true --port=9749
```

然后开 `http://localhost:9749`。UI 归共享守护进程所有，多个会话同时在线不会各起一个 HTTP 服务。想不经过 MCP 客户端就单独验证一把，用 CLI 模式（它不起守护进程、不注册会话、不留常驻进程）：

```bash
codebase-memory-mcp cli index_repository --repo-path /path/to/repo
codebase-memory-mcp cli list_projects
codebase-memory-mcp cli search_graph --project my-project --name-pattern '.*Handler.*' --label Function
codebase-memory-mcp cli trace_path --project my-project --function-name Search --direction both
codebase-memory-mcp cli query_graph --project my-project --query 'MATCH (f:Function) RETURN f.name LIMIT 5'
```

框架专有扩展名不用等上游支持，仓库根放 `.codebase-memory.json`（全局版在 `~/.config/codebase-memory-mcp/config.json`），只认一个键 `extra_extensions`，把扩展名映射到已支持的语言名，项目级覆盖全局级：

```json
{ "extra_extensions": { ".blade.php": "php", ".mjs": "javascript" } }
```

语言名大小写不敏感，取值必须在 README 列出的那份清单里；映射到未知语言名、或者扩展名没以 `.` 开头的条目会被跳过，并在 stderr 记一条告警，不会中断加载。默认日志级别下就能看到这条告警。

## 按现象查：六个常见报错和它们的处置

README 的 Troubleshooting 一节收进表里的，就是项目方认定为常见的六类故障。这里按现象把它们归并成两栏可读的形式：先分"根本没接上"还是"结果看着不对"，前者先试 `echo '{}' \| /path/to/binary` 能不能吐出 JSON，后者先看是不是没指定项目。处置全部照官方文档写，不加推测。

| 现象 | 先看哪里 | 处置 |
|------|----------|------|
| `/mcp` 里看不到服务 | `.mcp.json` 里的 `command` 是否为绝对路径 | 改绝对路径、重启 agent；用 `echo '{}' \| /path/to/binary` 验证可执行 |
| `index_repository` 失败 | 传的是相对路径 | 传绝对路径；被不信任的调用方驱动时设 `CBM_ALLOWED_ROOT`，越界的 `repo_path`（含符号链接与 `..` 解析后）会被拒 |
| `trace_path` 返回 0 结果 | 函数名没对上 | 先 `search_graph(name_pattern=".*PartialName.*")` 拿准确名字，注意 `trace_path` 深度只到 5 |
| 查询命中的是别的项目 | 多项目共库 | 每次调用带 `project="name"`，用 `list_projects` 看真实名字 |
| 装完找不到二进制 | PATH | `export PATH="$HOME/.local/bin:$PATH"` |
| UI 打不开 | 有没有传 `--ui=true` | 检查 `http://localhost:9749`；Nix 的 `default` 包不含 UI，只有 `codebase-memory-mcp-ui` 那个包能起 HTTP 服务 |

三条文档里散着、踩了很难查的：

- **改 `watcher_enabled` 之后不生效。** 它只在后台守护进程启动时读一次，改完要 `codebase-memory-mcp daemon stop`；只重连 MCP 客户端不会重启守护进程。`auto_watch` 才是每会话检查的那个。
- **换 `CBM_CACHE_DIR` 时报冲突。** 一个账户同时只认一个规范 cache root，有活跃会话时换新 root 会直接被拒，冲突记录落在 `${CBM_CACHE_DIR}/logs/daemon-conflicts.ndjson`。先关会话再换。
- **索引"成功"但节点少了。** 别把 `status: "degraded"` 当成 `indexed` 略过去，那是 `CBM_DUMP_VERIFY_MIN_RATIO` 的自检命中；同时跑 `check_index_coverage` 看被跳过和解析失败的文件。README 对这一档的定位很直白：干净的覆盖结果只表示"没有记录到缺口"，不表示完整。

Windows 上还有两条独立的：`.ps1` 从网上下载会带 Web 标记，要先 `Unblock-File`；SmartScreen 对未签名软件弹警告，处置是核对 `checksums.txt` 而不是直接"仍要运行"。

## 谁该现在就上，谁可以再等等

判断线划在"有没有结构类问题要反复问"，不划在仓库大小。

适合现在接：需要反复回答"谁调它、它调谁、改这处波及哪里"的中大型代码库；重构前要有据可依的场景（`detect_changes` 直接把 git diff 映射成受影响符号和爆炸半径，比人工全局搜索可审计）；多语言的单仓库（monorepo），尤其 Python / TypeScript / Go / Rust / C / C++ 这些有类型解析覆盖的；以及需要把跨服务端点当图实体来看的——HTTP 路由与调用点能按置信度配对，gRPC、GraphQL、tRPC 会被识别成端点，发布订阅通道走 `EMITS` / `LISTENS_ON` 两条边，再用 `ingest_traces` 拿运行时 trace 去校验 `HTTP_CALLS`。

可以再等：万行量级、grep 一次就能扫完的小仓库，索引和守护进程都是净开销；主要工作是找注释、TODO、日志串这类行级文本的，Explorer 那 0.92 就是这类任务的证据，`search_code` 和 grep 更合适；重度依赖宏的 C/C++ 和大量运行时拼装代码的，图里没有那些边；以及把"能跑 `query_graph`"当需求核心的，它的读子集不含 `MERGE` 与参数化，且默认 100,000 行封顶。

采用顺序，按依赖排：

1. 只在一台机器上装，用 `--skip-config` 或手写 `.mcp.json`，先别让它改任何 agent 的全局配置。
2. `index_repository` 一个中等仓库，跑 `get_graph_schema` 与 `list_projects`，把实际 label / 边类型和自己以为的对一遍。
3. 拿三个你已知答案的问题去问 `trace_path`、`query_graph`、`detect_changes`，答不对就先看 `check_index_coverage`，别先看模型。
4. 满意后再让 `install` 配全套客户端，并去每个客户端里核对它装了哪些 hooks 和子代理——它会写 skill、指令文件和生命周期钩子，Codex 侧还要在 `/hooks` 里复核信任哈希。
5. 团队共享走 `.codebase-memory/graph.db.zst`，先定提交节奏（发布节点或每夜任务），不要每次刷新都提交。

想进阶到"能自己判断这个工具值不值得改"，下一步是读代码而不是读文档。

## 五个自测题

### 题 1：为什么说 Hybrid LSP 不等于"接一个 language server"

<details>
<summary>参考答案</summary>

因为它不启动任何 language server 进程。README 写明它是用 C 重写的一份轻量类型解析算法，结构上对齐并兼容 tsserver / typescript-go、pyright、gopls、Roslyn、Eclipse JDT、rust-analyzer，直接编进二进制，"No language server process, no per-project setup, no API key"。它跟 tree-sitter 一起跑，把调用边细化，定不出唯一目标的降级成 `USAGE`。后果是：部署时不需要按语言装 server；但它是重新实现，覆盖度按语言分档，落到具体语言上要查那张 10 行的表。

</details>

### 题 2："83% answer quality"能不能作为"质量足够好"的证据

<details>
<summary>参考答案</summary>

不能。论文表 6 的原始数据是 0.83 对 0.92，正文写"achieves 90% of the Explorer Agent's quality score"——它是一次质量换成本的退化，且打分由第一作者按人工核对的参考答案在连续 0–1 尺度上完成，阈值自称"chosen pragmatically"，两边共用单一后端 Claude Opus 4.6。样本单位是 31 种语言各一个仓库、12 类问题。需要整段源码和穷举式匹配的问题 Explorer 仍占优，图谱只在枢纽识别与调用者排名上于 19/31 种语言持平或更好。

</details>

### 题 3：10× 词元和 120× 词元削减矛盾吗

<details>
<summary>参考答案</summary>

两者来自不同口径，不能互相换算。10× 是论文每问均值约 1,000 对约 10,000；120× 与"99.2% reduction"是 README 的实测记录：五次结构查询合计约 3,400 词元对文件遍历式检索约 412,000 词元，比值实际是 121 倍。把 3,400/412,000 当成论文那个 10× 的注脚，误差就是 12 倍。

</details>

### 题 4：想确认"这个函数真的没有调用者"，正确动作是什么

<details>
<summary>参考答案</summary>

三步。先 `trace_path(direction="inbound")`，返回空不代表不存在，先 `search_graph` 核对名字是否解析成功；再 `check_index_coverage` 看该文件是否被跳过或部分解析失败——README 明确说干净的覆盖结果只代表"没有记录到缺口"；最后按三档的分工核对结论级别：Scout 档官方就不允许提"缺失"，负向判断要落到 Auditor 档的受限范围里，并且把仍未解决的部分显式留着。直接把 `trace_path` 的空结果写成"没有调用者"，就是拿正向工具做否定证明。

</details>

### 题 5：为什么说"单一静态二进制、没有脚本胶水"在 v0.11.0 已经不成立

<details>
<summary>参考答案</summary>

v0.11.0 的 README 自己改了措辞：从 v0.9.0 的"single static binary"换成"native executable with a small verified runtime-asset set"。release 有 49 个资产，除 tar.gz / zip 还有 `.mcpb`；每个包里带 `install.sh` 或 `install.ps1`，`checksums.txt` 由两个安装脚本在解包前校验；npm 包体无依赖但声明 `postinstall`，那个 683 行脚本会从 GitHub Releases 下载固定版本的归档与摘要文件。真实收益不是"没有脚本"，而是脚本行为可审计：SLSA 溯源（作用域是 release 压缩包）、cosign、SBOM、CodeQL 阻断、8 层构建期审计，外加逐候选的 VirusTotal 与公开的 TSV 证据。

</details>

## 练习：拿你自己的两个仓库跑一遍

选一前一后两个仓库：一个 10k 文件以内、主要是一种语言；另一个多语言且带 Dockerfile 或 Kubernetes manifest。

1. 各索引一次，记下 `index_repository` 返回的节点数、边数和耗时；再跑 `get_graph_schema`，把实际 label 与本文的 13 个对比，看你这个仓库多出来的是哪几个（`Route`、`Resource` 通常在这里出现）。
2. 挑一个你答得出的结构问题（"谁调用 X""X 经过几层到入口"），分别在带工具和不带工具两种条件下问同一个 agent 各一次，记下词元与工具调用次数。这一步是在复现论文实验的形态，只不过换成你熟悉的代码——0.83 对 0.92 这个总体差值换不掉，但"你的问题落在图谱占优的那 19/31 里，还是在需要整段源码、基线占优的那 16/31 里"只能自己测。
3. 制造一次 PARTIAL：让 agent 用 `query_graph` 写一条含 `MERGE` 的语句，看它是不是明确报错而不是返回空集。这一步是在校准你对"失败会显形"这条设计属性的预期。

## 下一步读哪份源码

顺序按"能最快否证一个声明"排：

- `internal/cbm/cbm.h` 与 `internal/cbm/extract_*.c`：抽取层真正的产出。`extract_calls.c`、`extract_channels.c`、`extract_k8s.c`、`extract_type_refs.c` 这些文件名就是边类型的来源，比任何一份 README 更权威。
- `src/pipeline/`：`pass_semantic.c` 里能看到 `INHERITS` / `IMPLEMENTS` 的判定规则（目标是 `Interface` 就发 `IMPLEMENTS`，否则 `INHERITS`），以及多趟顺序。
- `src/mcp/mcp.c`：`TOOLS[]` 注册表与两份 profile 白名单。要核对工具数量，这是唯一的一手来源。
- `src/cypher/`：词法、解析、规划、执行。想判断"我的查询为什么被拒"，读这里比试错快。
- `docs/BENCHMARK.md` 与 `docs/EVALUATION_PLAN.md`：前者是已过时的具体测量，后者是尚未执行的计划。两份一起读，能看清这个项目的证据现在停在哪一步。
- `SECURITY.md`：先读 `Runtime Network Behavior` 和 `Antivirus False Positives`。要评估它，这两节比任何徽标都直接。

## 资料口径与复核方法

本文所有计数与引语在 2026-09-19 由下述来源核对，未采用二手转述：

- 源码与文档：用一条只要提交树、不取文件内容的浅克隆（`git clone --depth 1 --filter=blob:none --no-checkout`）拿到 `main` 的提交树，`git show HEAD:<path>` 按需取文件；`v0.11.0` 与 `v0.9.0` 两个标签下的 `README.md` / `SECURITY.md` / `src/mcp/mcp.c` 另从 `raw.githubusercontent.com` 单独取，避免把分支头当成发布物。grammar 数取自提交树里 `internal/cbm/grammar_*.c` 的计数（162），工具数取自 `TOOLS[]` 的字面量条目（17）。
- 论文：`arxiv.org/abs/2603.27277` 的摘要页与 PDF 正文，表 6、4.4 节社区采用数据、5.4 节效度威胁按原文转述。
- 发布物与包：GitHub Releases API 的 v0.11.0 资产清单（49 项及各自大小）、`registry.npmjs.org/codebase-memory-mcp` 的元数据与 tarball 内容（`package.json`、`install.js` 行数与下载 URL）。
- 仓库级事实：GitHub Repos API 在 2026-09-19 读到的 MIT 许可、主语言 C、43,775 星、3,561 复刻、创建时间 2026-02-24。

三处未能定案、显式保留为 unresolved：v0.11.0 源码 `TOOLS[]` 有 17 项而 README 四处写 15，本文两个数字都列而不取其一，读者以 `/mcp` 实测为准；`src/ui` 的"经外部验证的 3D-UI 资产包"具体包含哪些文件未逐个展开核对；`graph.db.zst` 的 8–13:1 压缩比与"某团队 6 GB"均为项目自述，无第三方复现。

失效条件：2026-02-24 到 2026-09-15 之间发了 47 个 release，而 `docs/BENCHMARK.md` 与论文描述的都是 2026 年 3 月的形态。本文的版本敏感结论（语言数、工具数、profile 白名单大小、客户端面数、分发形态）预计在下一次 minor 版本后即需重数一遍，重数方式就是上面那四条命令。

## 参考资料

- 项目仓库与 README、SECURITY.md、docs/ 目录：<https://github.com/DeusData/codebase-memory-mcp>
- 语言基准（v0.3.0，2026-03-01）：`docs/BENCHMARK.md`
- 评测计划（尚未产出结果）：`docs/EVALUATION_PLAN.md`
- 自建指标测量方法：`docs/MEASURING_SAVINGS.md`
- 配置与环境变量：`docs/CONFIGURATION.md`
- 论文《Codebase-Memory: Tree-Sitter-Based Knowledge Graphs for LLM Code Exploration via MCP》，arXiv:2603.27277，2026-03-28：<https://arxiv.org/abs/2603.27277>
- v0.11.0 发布页（49 个资产与逐候选扫描证据）：<https://github.com/DeusData/codebase-memory-mcp/releases/tag/v0.11.0>
