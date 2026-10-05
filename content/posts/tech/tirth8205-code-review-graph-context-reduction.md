---
title: "code-review-graph：把 Code Review 的上下文收缩成一张本地代码图"
date: 2026-07-20T03:02:36+08:00
lastmod: 2026-10-03
categories: ["技术笔记"]
tags: ["Code Review", "MCP", "tree-sitter", "AI 编程"]
description: "code-review-graph 是本地优先的代码智能图（CRG），用 Tree-sitter 把代码库解析成 nodes + edges 持久化到 SQLite，回答 AI Coding Agent 的'读哪些文件就够'问题。31.9K stars、六仓库基准中位数 63x token 削减、16 个平台一键接入，另有 GitHub Action 做 CI 里的风险评分 review。"
slug: tirth8205-code-review-graph-context-reduction
github_repo: "tirth8205/code-review-graph"
source_key: "gh:tirth8205/code-review-graph"

---

# code-review-graph：把 Code Review 的上下文收缩成一张本地代码图

## 一句话判断

code-review-graph（下称 CRG）解决的问题是 **"AI Coding Agent 在 review 时应该读哪些文件"**。它用 Tree-sitter 把代码库解析成 AST，再整理成 nodes（函数、类、导入）+ edges（调用、继承、测试覆盖）的图，持久化到仓库里的一个 SQLite 文件。文件一改，CRG 用图算出 blast radius（爆炸半径）——所有可能受影响的 callers、dependents 和测试——agent 只读这批文件，而不是在整库里翻。

这张图不止服务 review 工作流。社区检测、枢纽与桥、意外耦合、知识缺口那一组架构分析能力共用同一张图，在[姊妹篇](/posts/code-review-graph-ai-knowledge-graph/)里单独展开。

它的价值判断要放在两处看：headline 数字（六仓库基准中位数 63x 的 token 削减）建立在一个真实 agent 不会付的全库基线上，水分要挤；但 blast radius、callers-of-callers、tests-for 这类多跳结构查询，是 grep 和向量检索都给不了的，这部分才是它区别于 RAG 工具的立身之本。

## 系统地图

| 模块 | 责任 |
|------|------|
| Tree-sitter Parser | 把源码解析成 AST，主流语言覆盖，缺失语言可用 `languages.toml` 自定义 |
| Graph Builder | AST → nodes + edges（call / inherit / import / test coverage），另做社区检测（Leiden）与 FTS5 全文索引 |
| SQLite Store | 持久化到 `.code-review-graph/` 下单个文件，按 SHA-256 文件 hash 增量更新 |
| Blast Radius 分析 | 给定变更文件，沿图找出受影响的 callers / dependents / tests，输出风险评分 |
| MCP Server | 30 个工具加 5 个工作流模板，把图查询暴露给 agent；`serve --http` 默认绑 127.0.0.1:5555 |
| CLI | build / update / status / watch / detect-changes / dead-code / visualize / wiki 等人用命令面 |
| Watch Mode + Hooks | 编辑器 hook、git pre-commit hook、watch mode 触发增量更新；另有 `crg-daemon` 守护多仓库 |

## 关键机制拆解

### 1. Blast radius：改一个文件，牵出一片

README 对机制的描述是一句话："When a file changes, the graph traces every caller, dependent and test that could be affected." 具体到一次改动：改了 `login()`，图沿 CALLS 边找出所有调用它的函数，沿 IMPORT 边找出依赖所在模块的文件，再找出覆盖它的测试——三类的并集就是这次改动的 blast radius。

这个分析刻意偏保守：宁可多报一个可能受影响的文件，也不漏掉一个真被牵连的依赖。代价是大型依赖图里会有假阳性，官方的影响分析基准里 precision 只有 0.546（13 个评估 commit 的平均），换来的就是那栏 1.0 的 recall。

### 2. 增量更新：秒级维持

大型 repo 全量重建耗时会随规模增长，但日常开发不需要频繁全量重建。CRG 的更新路径是：hook 或 watch 触发 → diff 出变更文件 → 沿图的 import/call 边找受影响者 → 只重新解析 SHA-256 hash 变了的文件。官方实测口径：约 3,000 文件的 django 仓库，两文件编辑在 hook 路径上约 2.5 秒完成，其中约 1.4 秒是进程启动，空更新只花这点启动开销；同等规模仓库的冷构建约 40 秒。

解析失败也有明确行为：结果状态标 `partial`，摘要里点名失败文件，CLI 在 stderr 打 `Warning:`，这些文件保留上一轮的图数据，不至于一损俱损。

### 3. 多语言解析：清单比分类更准

CRG 支持的语言面以 README 清单为准：Python、JavaScript/TypeScript/TSX、Go、Rust、Java、C/C++、C#、Ruby、Kotlin、Swift、PHP、Scala、Solidity、Dart、Lua/Luau、Zig、Elixir、shell 脚本等三十余种，外加 Vue/Svelte 单文件组件、Jupyter 与 Databricks notebook（`.ipynb`）、Terraform（`.tf`）和 Ansible YAML。树里没有的语法可以不 fork 就地补：在 `.code-review-graph/languages.toml` 里把扩展名映射到 `tree_sitter_language_pack` 里的任意语法并声明四类节点类型，内置语言不可覆盖。

两个容易误读的边界：普通的 YAML 和 `.properties` 文件不当源码解析（只有 Ansible 和 Spring Boot 配置走特殊通道）；PHP 与 Java 项目在源码出现显式框架证据时，额外解析 Laravel 路由/Eloquent 与 Spring 依赖注入、WebFlux 路由这类框架语义边。

## 一次 review 怎么流过系统

以一次典型的功能分支改动为例：

1. 开发者改了三个文件。pre-commit hook（或 `crg-daemon` 的 watcher）触发增量更新，只重解析 hash 变化的文件，图维持最新。
2. 开发者跑 `code-review-graph detect-changes --brief`：命令查现有图，输出风险面板——diff 映射到受影响的函数、执行流和测试缺口——同时打出一个 Token Savings 面板，比如官方样例里的"全量上下文 12,921 tokens，图上下文 762 tokens，省下约 94%"。想先刷新再算就换 `update --brief`；加 `--verify` 会用 OpenAI 的 `cl100k_base` 分词器交叉核对估计值（官方在 222 个样本文件上校准的聚合偏差约 1%）。
3. agent 侧走 MCP：assistant 调 `detect_changes_tool` 拿风险评分，调 `get_impact_radius_tool` 拿 blast radius，然后只读这批文件。30 个工具里还有 `query_graph_tool`（callers/callees/tests/imports 查询）、`get_suggested_questions_tool`（从桥接节点和意外耦合生成的 review 问题）等；5 个工作流模板（review_changes、architecture_map、debug_issue、onboard_developer、pre_merge_check）把常见问法打包成了 prompt。
4. 如果走 CI 路线，GitHub Action 在 runner 上建图查询，每个 PR 发一条 sticky comment，列风险评分函数、受影响执行流和测试缺口，每次 push 原位更新；`fail-on-risk` 输入可以把它变成合并门禁。图在 CI 本地构建，源码不外发。

四条路径共享同一张图——这正是"本地优先"的含义：数据就是仓库里的一个 SQLite 文件，没有外部服务依赖，FAQ 明确写了零遥测。

## 63x 从哪来：把 benchmark 读准

CRG 的 token 基准测的是"整库语料 vs 图查询响应"：对每个仓库的 5 个样例问题（"how does authentication work" 这类），比较把全部源码塞给模型和只返回图查询结果（命中项加邻居边，约 2,200–3,900 tokens）的差距。2026-08-02 对 6 个仓库（fastapi、flask、gin、httpx、express 和 CRG 自身）13 个 commit 的 capture 结果：中位数约 63x，区间 34.6x–357.6x，最大值出自语料最大的 fastapi（约 95 万 tokens 语料压到 2,653）。

数字要配三个注脚读：

- **基线是上限，不是现实**。README 自己写明 "The whole-corpus baseline is an upper bound no real agent pays"——真实 agent 会 grep 标识符再读最匹配的几个文件。官方做了 `agent_baseline` 基准来测这个更真实的对照，但截至当前版本还没有发布正式 capture。所以 63x 该读作"结构化索引相对暴力全读的上限收益"，不是日常账单。
- **数字下滑是测量口径变化，不是产品退步**。上一个 capture（文章发表时的 README 口径）中位数约 82x，CRG 自身行写的是 208,821 tokens 压到约 2,495（93x）；新 capture 把它修成压到约 3,190（65.5x）。官方解释是节点 embedding 文本变得更丰富，graph_tokens 在每个仓库都升高了。一个会把自家 headline 从 93x 改成 65.5x 的项目，基准纪律在同类工具里少见。
- **两个基准答的是两个问题**。形式化的 `token_efficiency` 基准测"完整 review 上下文 JSON vs 仅变更文件内容"，小 commit 上比率会低于 1——响应里带的影响半径边和源码片段比单文件 diff 还贵。这不是 bug，是"图上下文的成本结构"本身。

影响分析基准也有同样的自省：recall 1.0 是循环上限——ground truth（变更文件加上有 call/import 边指向它们的文件）就来自预测器走的同一张图；更有说服力的 co-change 模式（按作者同一 commit 实际改动的文件打分）在 2026-08-02 capture 里每个 commit 都返回 0 个预测文件，官方直说"尚不可用，不予引用"。

## 定位与同类对比

按官方 FAQ 的口径：LSP 是编译器前端的符号级精度（泛型、重载、作用域感知），单语言单符号的精确引用该用它；CRG 是一张持久的跨语言结构图。RAG 类工具（如 claude-context）做相似度分块检索，CRG 的边是从 AST 解析出的结构关系，embeddings 只是可选的搜索辅助。grep 赢单跳查找，图赢多跳问题。与 Serena（LSP 符号工具集）、repomix（整库打包成单文件）的定位差异，官方在 docs/FAQ.md 里有逐项对比表，结论是 CRG 的生态位在"为 review 服务的持久结构图"。

生态数据（2026-10-03 读数）：GitHub 31,898★ / 2,919 forks，MIT 协议，纯 Python（要求 3.10+）；2026-02-26 建仓当天首发 PyPI 包（1.2.0），至今 37 个 release，最新 v2.3.9（2026-09-18）。README 有英、中、日、韩、印地五语版本。工程流程是 staging → testing → main 三级晋升，staging 测试通过后每日自动晋升到 testing，进 main 永远需要人动手，release 从 main 打 tag。

## 适用边界与采用顺序

官方 FAQ 给的规模判断比任何宣传都实用：

- **几百文件以下**：边际。agent 直接读就够了，结构元数据是这个小仓库还不回来的开销；琐碎的单文件改动上，review 响应携带的影响边和代码片段可能比 diff 本身还贵（形式基准在小 commit 上比率低于 1 的原因）。
- **几千文件以上、monorepo**：最强场景。fastapi 约 95 万 tokens 的语料没有任何 agent 能按问题通读，增量更新又能让图一直保持新鲜。
- **文件数只是维度之一**：一个 300 文件但每天 review 的仓库，比 3,000 文件偶尔碰一次的仓库更受益。

能力边界也要知道：执行流（entry point）检测目前主要对 Python 和 PHP/Laravel 模式可靠，整体 flow recall 约 33%，JavaScript 和 Go 需要改进；关键词搜索多数情况能把正确结果排到前列，但排名仍待打磨，Express 查询会因模块命名模式返回零命中。

采用顺序建议：先在 CI 里试 GitHub Action——一条 workflow 引用 `tirth8205/code-review-graph@v2.3.9` 就能在 PR 上拿到风险评分评论，团队零安装成本；确认 blast radius 的信噪比对你们的代码库值得，再让重度 agent 用户本地装 MCP（`pip install code-review-graph && code-review-graph install` 会探测已装工具并逐个写入配置，支持 codex、claude-code、cursor、windsurf、zed、continue、opencode、antigravity、gemini-cli、qwen、kiro、qoder、copilot、copilot-cli、codebuddy、hermes 十六个平台）。编辑器不支持 hook 的团队（Cursor、OpenCode）用 `crg-daemon` 在后台维持多仓库的图。语义搜索按需开启：本地 sentence-transformers 不出机器，配云 embeddings 时注意它会发送节点名、签名、docstring 摘要和文件路径——函数体不上传，但 stderr 会打出口警告直到显式设置 `CRG_ACCEPT_CLOUD_EMBEDDINGS=1`。

卸载同样有边界承诺（现行 README 措辞）："removes CRG-owned files and entries from a Git or SVN working tree and leaves other MCP servers, hooks, skills and JSONC comments alone"，共享配置文件原子替换，写失败原文件保持完整；`--dry-run` 预览、`--yes` 跳过确认、`--all-repos` 清理所有注册仓库、`--keep-data` 只拆集成保留图数据。

## 仓库地址

https://github.com/tirth8205/code-review-graph

## 阅读路径建议

1. `pip install code-review-graph && code-review-graph install`，接入最常用的 agent，或直接在 CI 里加 GitHub Action
2. `code-review-graph build` 建图后，改一个文件跑 `detect-changes --brief`，看 Token Savings 面板的真实数字
3. `code-review-graph status` 确认 Nodes/Edges/Files 非零；让 agent 问一个多跳问题（"这次改动影响了哪些调用方和测试"），对比它自己 grep 的答案
4. 读完 docs/FAQ.md 的对比表和 docs/REPRODUCING.md 的基准方法学，再决定是否全团队推广——基准可复现是官方明说的设计目标，值得亲自验一遍
