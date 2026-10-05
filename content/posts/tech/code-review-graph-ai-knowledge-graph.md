---
title: "code-review-graph：一张本地代码图，既过滤 AI 的上下文，也透视架构"
date: 2026-08-10T03:45:00+08:00
lastmod: 2026-10-03
draft: false
categories: ["技术笔记"]
tags: ["code-review-graph", "知识图谱", "架构分析", "mcp", "tree-sitter"]
description: "code-review-graph 用 Tree-sitter 把代码库解析成持久的本地知识图谱：六仓库基准中位约 63 倍的 token 缩减之外，Leiden 社区检测、介数中心性、意外耦合评分和知识缺口分析让它同时是一台架构透视镜。"
github_repo: "tirth8205/code-review-graph"
source_key: "gh:tirth8205/code-review-graph"
slug: "code-review-graph-ai-knowledge-graph"
---

[code-review-graph](https://github.com/tirth8205/code-review-graph)（下称 CRG）把"理解一个代码库"从每次 AI 会话里的临时开销，变成一份存在仓库里的持久资产：Tree-sitter 解析出函数、类、导入、调用点和继承关系，连同测试覆盖一起存进一个 SQLite 文件。这份资产有两种用法。第一种你已经猜到——审查时算出变更的爆炸半径，只让 agent 读受影响的文件，六仓库基准中位约 63 倍的 token 缩减就来自这条路（工作流细节见[姊妹篇](/posts/tech/tirth8205-code-review-graph-context-reduction/)，本文不重复）。第二种用得少得多，也更可惜：把图本身当作架构分析工具，回答"这个系统的社区结构长什么样、哪里是瓶颈、哪些依赖出乎意料、哪里没有测试"。

第二种用法不需要换任何工具。同一张图、同一个 MCP（Model Context Protocol，AI 工具接外部能力的标准协议）server，30 个工具里有一整组是给架构分析准备的——本文就把这半边讲清楚。

## 这张图里有什么

CRG 的解析器提取六类结构：函数、类、导入、调用点、继承和测试。它们组成图的顶点，调用、继承、导入和"哪些测试覆盖哪些代码"组成边。每个文件记 SHA-256 哈希，改动时只重新解析哈希变化的文件——增量更新让图能长期保持新鲜，这是"持久资产"成立的前提。

六个基准仓库的图规模（2026-08-02 在固定 SHA 上的净室构建）：

| 仓库 | 节点 | 边 | 嵌入向量 |
|---|---:|---:|---:|
| fastapi | 6,287 | 32,036 | 5,159 |
| express | 1,990 | 19,492 | 1,849 |
| gin | 1,589 | 17,237 | 1,491 |
| code-review-graph | 1,446 | 9,094 | 1,354 |
| flask | 1,415 | 8,259 | 1,329 |
| httpx | 1,263 | 8,236 | 1,193 |

fastapi 一个中等规模项目就有六千多节点、三万多边，而这个体量的图完整存在一个本地 SQLite 文件里，构建一次约 40 秒（约 3,000 文件的仓库，实测口径），之后由 hook 或 watch 模式增量维持。嵌入向量数低于节点数不是丢了——File 节点不参与嵌入。

边还有置信度标注，分 EXTRACTED（从 AST 直接提取）和 INFERRED（推断）两级，各带浮点分数。这让下游查询可以区分"确定的事实"和"图猜的关系"，做架构决策时知道哪些结论可以硬引。

## 四层图分析：从聚类到缺口

功能表里那组架构分析能力，实际是四个层次递进的问题。

### 第一层：代码的社区结构

Leiden 算法把图聚成"社区"——高内聚的模块簇。两个工程细节让它对大仓库可用：分辨率随图规模自动缩放，占比超过 25% 的社区会递归再拆，避免"一半代码算一个社区"的无效结果。聚类结果直接产出一份架构总览（`get_architecture_overview_tool` 或 CLI 对应命令），按社区画模块地图，并附耦合警告。社区检测依赖可选的 `[communities]` extra（igraph）。

社区结构还派生出两种产物：`code-review-graph wiki` 从社区结构生成 Markdown wiki，给新成员一份按真实代码组织、而不是按目录约定组织的入门材料；`visualize` 起一个 D3.js 力导向图，节点大小按连接数缩放，社区图例可以开关，浏览器里直接翻。

### 第二层：枢纽与桥

介数中心性找出桥接节点——被最多路径穿过的"咽喉"；连接数排名找出枢纽。这两类节点是架构上最贵的位置：改一处牵一片，也是最该写测试、最该做代码评审的地方。对应 `get_hub_nodes_tool` 和 `get_bridge_nodes_tool`。

### 第三层：意外耦合

意外耦合评分专门找三类异常边：跨社区的依赖（两个本应独立的模块互相引用）、跨语言的依赖（比如 Python 直接摸到前端模块）、外围直连枢纽的依赖（本该经过中间层的调用）。这是四层里最能直接转化成重构任务的一层——`get_surprising_connections_tool` 返回的每条边，基本都对应一次"这俩为什么认识"的追问。

### 第四层：知识缺口

前三层说代码什么样，这一层说代码哪里虚：孤立节点（谁都不引用也不引用谁的代码）、未测试热点（被大量依赖却没有测试覆盖）、薄弱社区（内部联系松散的模块）。`get_knowledge_gaps_tool` 输出这三类，`get_suggested_questions_tool` 再把枢纽、桥和意外耦合成 review 问题——这类问题让 AI 审查从"检查这个 diff"升级到"检查这个系统的薄弱处"。

## 一次架构评审怎么跑

把四层能力串成一次真实工作。假设接手一个陌生仓库，或者每季度做一次架构健康检查：

```bash
code-review-graph build      # 首次建图，之后 hook/watch 增量维持
code-review-graph wiki       # 社区结构生成 wiki，先建立全局认知
code-review-graph dead-code  # 无调用方也无测试的函数和类
```

然后在 MCP 会话里让 agent 走一圈：`architecture_map` prompt 拿架构总览和耦合警告；`get_bridge_nodes_tool` 和 `get_surprising_connections_tool` 找瓶颈和异常依赖；`get_knowledge_gaps_tool` 列出未测试热点；最后 `get_suggested_questions_tool` 把发现转成具体的评审问题。产出想归档，`visualize --format obsidian` 导出成 Obsidian vault，图、笔记和反向链接都在本地。

这趟流程的每一步都是本地计算。图数据不离开你的机器，项目 FAQ 明确写了零遥测。

## 语义搜索：图的检索层

图查询解决"结构已知"的问题——调用谁、影响谁；语义搜索解决"结构未知"的入口问题——"处理认证的代码在哪"。两者在 CRG 里是组合关系：FTS5 全文索引做关键词与向量的混合检索，向量部分可选，五种 provider：

| Provider | 安装 | 默认模型 |
|---|---|---|
| sentence-transformers（本地） | `[embeddings]` extra | `all-MiniLM-L6-v2` |
| Google Gemini | `[google-embeddings]` extra | 需 `GOOGLE_API_KEY` |
| MiniMax | 设 `MINIMAX_API_KEY` | — |
| Voyage AI | 免额外安装，设 `VOYAGE_API_KEY` | `voyage-code-3` |
| OpenAI 兼容端点 | 免额外安装 | — |

OpenAI 兼容一路覆盖 OpenAI、Azure、自托管网关（new-api、LiteLLM、vLLM、LocalAI）以及 OpenAI 模式下的 Ollama，配 `CRG_OPENAI_BASE_URL` 即可接本地模型。Voyage 那一路默认 `voyage-code-3`、1024 维，是五家里唯一为代码专门调过的默认嵌入模型。

选云嵌入之前要知道数据边界，README 写得很具体：上传的是标识符、签名、结构上下文和首段 docstring 的有界摘要——函数体不上传。但云服务商收到的毕竟是源代码衍生文本，首次调用会触发 stderr 警告，直到显式设置 `CRG_ACCEPT_CLOUD_EMBEDDINGS=1`；端点指向 localhost（`127.0.0.1`、`localhost`、`0.0.0.0`、`::1`）时警告自动跳过。这个设计把"数据去哪了"的决定权留在用户手里，而不是藏在文档第 N 节。

嵌入模型的选择纪律值得抄录：别用 `-preview`、`-beta`、`-exp` 后缀的模型建索引——预览模型可能改权重——嵌入维度一变就得全量重嵌——也可能被直接撤回。官方推荐 GA 版本：OpenAI 的 `text-embedding-3-small`/`-large`、自托管 vLLM 或 LocalAI 上的 `Qwen/Qwen3-Embedding-8B`、原生 Gemini 的 `gemini-embedding-001`。

两个维护细节：常规构建不刷新嵌入，要刷新得显式传 `--embedding-provider` 和 `--embedding-model`；文档提取功能加入之前建的旧图，需要先做一次全量 `build` 再重嵌。

搜索排名仍是短板——官方 Limitations 承认关键词搜索多数情况能把正确结果排到前列，但排序待改进，Express 仓库的查询会因模块命名模式返回零命中。检索层的定位是"入口辅助"，不是图的立身之本。

## 基准数字：读法比数字重要

token 效率基准（2026-08-02 capture，全部固定 SHA）：

| 仓库 | 全量 token | 图查询 token | 缩减 |
|---|---:|---:|---:|
| fastapi | 948,793 | 2,653 | 357.6x |
| flask | 143,594 | 2,196 | 65.4x |
| code-review-graph | 208,821 | 3,190 | 65.5x |
| gin | 166,868 | 2,766 | 60.3x |
| httpx | 142,356 | 2,661 | 53.5x |
| express | 136,052 | 3,936 | 34.6x |

中位约 63x。三个读数前提：全量基线是理论上限，真实 agent 会先 grep 再读最匹配的几个文件，官方的 `agent_baseline` 基准已实现但尚未发布正式捕获；357.6x 出自语料最大的 fastapi，是最好情况不是典型值；这组数字比上一轮 capture 低，原因是节点嵌入文本变丰富后 graph_tokens 在每个仓库都升高——一个会把自家 headline 数字主动改小的项目，基准纪律本身就是稀缺品质。数字的完整解读（包括影响精度 F1 0.693 的含义和 co-change 模式为何暂不可用）在[姊妹篇](/posts/tech/tirth8205-code-review-graph-context-reduction/)里有逐项拆解。

对本篇的主题，benchmark 只说明一件事：图查询响应被刻意控制在 2,000–4,000 token 量级，所以"顺手问一句架构问题"的成本低到可以随时发生——架构分析不需要专门立项，它可以是日常工作流里的一条命令。

## 值得学的工程纪律

抛开功能，CRG 的几条工程实践在同类工具里少见：

**可复现性**。所有基准数字来自评测运行器：每个配置钉住上游 SHA，Leiden 聚类固定种子（`CRG_LEIDEN_SEED=42`），嵌入在 CPU 上确定性生成——两台机器跑出同一组数字。另有每周一次的 report-only 定时评测跑最小配置，防数字悄悄漂移。

**部分失败不扩散**。解析失败时结果状态标 `partial`，摘要点名失败文件，CLI 在 stderr 打警告，失败文件保留上一轮的图数据。一次解析事故不会毁掉整张图。

**两步式重构**。`refactor_tool` 只做预览（重命名预览、框架感知的死代码检测、基于社区结构的建议），`apply_refactor_tool` 只应用"已经预览过"的重构。预览和执行分离，agent 就没有单步改坏代码的通道。

**发布流程**。默认分支是 `staging`，PR 打向 staging；staging 测试通过后每天自动晋升到 `testing`，进 `main` 永远需要人工，release 从 `main` 打 tag。项目 2026-02-26 建仓，七个多月打出 37 个 release，最新 v2.3.9（2026-09-18）——节奏不见拖沓。

## 边界与采用

图规模三档（官方 FAQ 口径）：几百文件以下属于边际——agent 直接读就够，结构元数据是这个体量还不会回本的开销；几千文件以上和 monorepo 是最强场景——没有 agent 能按问题通读约 95 万 token 的 fastapi 语料；文件数只是维度之一，每天有人审查的 300 文件仓库，比偶尔才碰的 3,000 文件仓库更受益。

CRG 的调用解析是 AST 级启发式，不是编译器级精度——需要泛型、重载、作用域感知的符号级引用，LSP 仍是更准的工具。执行流检测目前对 Python 和 PHP/Laravel 模式最可靠，整体 flow recall 约 33%，JavaScript 和 Go 待改进。把图分析当"架构讨论的起点"很合适，当"架构决策的唯一依据"则会超出来访精度。

采用顺序上，本篇的架构用法和姊妹篇的审查用法共享同一张图，边际成本为零：先用 GitHub Action（`tirth8205/code-review-graph@v2.3.9`，一条 workflow 引用，PR 上自动获得带风险评分的评论）验证图的信噪比；值得长期用，再 `pip install code-review-graph && code-review-graph install` 一键接入——install 探测本机已装的 AI 工具并逐个写配置，支持 Codex、Claude Code、Cursor、Windsurf、Zed、Continue、OpenCode、Antigravity、Gemini CLI、Qwen、Kiro、Qoder、GitHub Copilot、Copilot CLI、CodeBuddy、Hermes 十六个平台；编辑器不支持 hook 的（Cursor、OpenCode），`crg-daemon` 会在后台以子进程方式维持多仓库的图，每 30 秒健康检查。架构评审那套查询，从第一天起就免费附赠。

项目数据（2026-10-03 读数）：GitHub 31,898★ / 2,918 forks，MIT 协议，纯 Python（3.10+），存储是 `.code-review-graph/` 下的单个 SQLite 文件，官网 [code-review-graph.com](https://code-review-graph.com)。

## 仓库地址

https://github.com/tirth8205/code-review-graph
