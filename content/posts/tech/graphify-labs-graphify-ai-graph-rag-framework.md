---
title: "Graphify Labs Graphify：把 Claude Code 变成「知识图谱构建器」的本地 RAG 框架"
date: 2026-07-14T03:13:08+08:00
slug: "graphify-labs-graphify-ai-graph-rag-framework"
description: "Graphify 是一个 Claude Code / Codex 用的 /graphify 技能：读取本地代码、PDF、Markdown、图片（甚至多语种截图），用 tree-sitter + Claude Vision + Leiden 社区检测构建带语义边的知识图谱，输出可交互 HTML、Obsidian vault、Wikipedia 风格 wiki 与 GRAPH_REPORT.md，并支持 --watch 自动同步与 post-commit hook。"
draft: false
categories: ["技术笔记"]
tags: ["知识图谱", "RAG", "Claude Code", "AI Agent", "Graphify"]
---

## 本文导读

读完本文你将能够：

- 理解 Graphify 不是一个"图数据库项目"，而是一个 **Claude Code / Codex 的 Skill（技能包）**：它把 `/graphify` 命令注册到你的本地代理（agent），让代理对任意文件夹调用"读文件 → 提概念 → 建图 → 报告"的完整链路。
- 看清它与传统 RAG（向量检索）和 Neo4j 类图数据库的差异：本地运行、无外部服务、每条边带 `EXTRACTED / INFERRED / AMBIGUOUS` 标签，能诚实区分"看到的事实"与"猜的连接"。
- 跑通最小示例：安装 → `/graphify .` → 产出交互式 HTML / Obsidian vault / Wikipedia 风格 wiki。
- 知道 README 里那个 **71.5× token 压缩**的 benchmark 在什么条件下成立、小文件场景下不要硬上。
- 区分 `--watch`（自动监听）、`--update`（增量）、`graphify hook install`（post-commit 钩子）三种"图谱保鲜"模式的取舍。

适合读者：经常在 Claude Code / Codex 里做"读代码 + 读论文 + 读截图"的研究员、agent builder、想给个人本地知识库做图谱化的工程师。

---

## 一、先给判断：它不是图数据库，而是「让本地代理自带 RAG」的 Skill

Graphify（仓库 `Graphify-Labs/graphify`，原作者 `safishamsi/graphify`）的核心定位是：

> 一个 Claude Code Skill。在 Claude Code 里输入 `/graphify`，它会读你的文件、建一个知识图谱，并把"你不知道自己有的结构"还给你。

把它和常见概念摆在一起看：

| 工具形态 | 典型代表 | 与 Graphify 的差异 |
|----------|----------|-------------------|
| 向量 RAG | LlamaIndex、Chroma、Qdrant | 走 embedding 相似度，丢失显式关系；Graphify 保留命名实体与关系边 |
| 图数据库 | Neo4j、Memgraph | 需要服务、schema、cypher；Graphify 无服务、自动建图、输出可移植 JSON / GraphML |
| 笔记软件图谱 | Obsidian（双链）、Logseq | 手动/半自动；Graphify 全自动，跨多模态输入并能反向输出成 Obsidian vault |
| AI 笔记 Agent | NotebookLM、RecurseChat | 走云端闭箱；Graphify 本地、可见 JSON、可与 agent 工作流串联 |

README 用一个很直白的比喻：

> Andrej Karpathy 维护一个 `/raw` 目录，把论文、推文、截图、笔记全塞进去。Graphify 正是为了解决这个问题——每次查询相比直接读原始文件，**token 消耗降低 71.5×**，跨会话持续，**对"看到了什么"和"猜到了什么"是诚实的**。

注意 `71.5×` 是个 **特定 corpus（Karpathy 仓库 + 5 篇论文 + 4 张图片，共 52 个文件）下的查询压缩比**，不是任何场景的普适数字。后文会讲它的成立条件。

---

## 二、系统地图：本地流水线 × 多模态输入 × 可导出多种产物

Graphify 的工作流可以拆成四段：**读 → 提 → 构 → 出**。

### 2.1 输入侧：本地任意文件夹 + 任意文件类型

支持的文件类型在 README 里列表化给出：

| 类型 | 扩展名 | 抽取方式 |
|------|--------|----------|
| 代码 | `.py .ts .js .go .rs .java .c .cpp .rb .cs .kt .scala .php` | tree-sitter AST（抽象语法树）+ call-graph（调用图） |
| 文档 | `.md .txt .rst` | Claude 提取概念与关系 |
| 论文 | `.pdf` | 引用挖掘 + 概念抽取 |
| 图片 | `.png .jpg .webp .gif` | Claude Vision（截图、图表、任意语言） |

也就是说一个 `Karpathy 风格 /raw` 目录——里面有 Python 源码、几篇 PDF 论文、几张论文截图——可以 **一次性全部灌进去**，模型负责跨模态对齐。

### 2.2 抽取侧：tree-sitter + Claude 视觉

- **代码**走 tree-sitter 做语法解析、再做一次 call-graph 遍历。这是 **本地、不调 LLM** 的纯文本处理，速度快、便宜、可缓存。
- **文档 / 论文 / 图片**走 Claude 多模态模型做"概念—关系"抽取。

### 2.3 构建侧：NetworkX + Leiden + 边带标签

技术栈在 README 里写得很直接：

> NetworkX + Leiden（graspologic）+ tree-sitter + Claude + vis.js。**不依赖 Neo4j，不依赖外部服务，全本地运行。**

Leiden 是当前主流的 **社区检测（community detection）算法**，graspologic 是 Microsoft 的图算法 Python 库。两者结合意味着：图谱不仅有节点和边，还会按拓扑结构自动聚成"概念社区"。

边带三种标签，是 Graphify 对"诚实"承诺的工程化兑现：

| 标签 | 含义 |
|------|------|
| `EXTRACTED` | 文件里能直接看到的关系（如 import、引用、定义） |
| `INFERRED` | 模型推断的连接（`--mode deep` 模式下更多） |
| `AMBIGUOUS` | 关系存在但语义不清 |

### 2.4 输出侧：可观察、可查询、可导出的多种产物

```
graphify-out/
├── graph.html       交互式图，点击节点 / 搜索 / 按社区过滤
├── obsidian/        直接作为 Obsidian vault 打开
├── wiki/            Wikipedia 风格的文章（--wiki 启用）
├── GRAPH_REPORT.md  关键节点（god nodes）、意外连接、建议问题
├── graph.json       持久化图谱，跨会话查询不用重读文件
└── cache/           SHA256 缓存，重复跑只处理变化文件
```

`graph.json` 是 Graphify 的"灵魂产物"——它把昂贵的 LLM 抽取结果沉淀成本地 JSON，下次再问"什么概念和什么概念相连"时不用再走模型。配合下文的 `--update` 与 `--watch`，就形成"一次性建图、长期复用"的本地知识库。

---

## 三、安装与最小示例：5 分钟跑通

### 3.1 前置与命令

README 给出的安装前置：

> Requires: Claude Code 与 Python 3.10+。

主流程命令：

```bash
pip install graphifyy && graphify install
```

> 备注：PyPI 上的包名暂时是 `graphifyy`（两个 y），因为 `graphify` 名字还在回收。CLI 与 `/graphify` 技能名仍叫 `graphify`。

平台差异的两种典型坑（README 里有专门提示）：

- **Windows**：若 `graphify` 不识别，把 `%APPDATA%\Python\Python3xx\Scripts` 加入 PATH（`3xx` 换成实际版本，如 `313`）。或者直接用 `pipx install graphifyy`，pipx 会自动处理 PATH。
- **macOS externally-managed**：如果 `pip install` 报 "externally-managed-environment" 错，用 `pipx install graphifyy`。

如果不想走 PyPI，README 也给出了"手动 curl 安装"模式：把 SKILL.md 拉到 `~/.claude/skills/graphify/SKILL.md`，再在 `~/.claude/CLAUDE.md` 注册触发规则。这个路径在自动化 / 容器环境更稳。

### 3.2 最小示例

```bash
# 在任意目录打开 Claude Code，输入：
/graphify .
```

这是 README 第一条命令，对当前目录整树构建图谱。如果你有个 `~/notes/` 目录专门放论文和截图：

```bash
/graphify ./notes
```

跑完后会得到上面那一组 `graphify-out/` 产物。**最少只要打开 `graph.html`** 就能在浏览器里点节点、看边标签、感受"god node"长什么样。

### 3.3 三个最容易踩的坑

1. **第一次跑特别慢**。代码走 tree-sitter 是本地快，但文档/图片都要 Claude 抽概念。`worked/karpathy-repos/` 那个 52 文件的样例就属于"开一次心疼一次"的量级。
2. **Windows PATH**。`graphifyy` 装得上但命令敲不响，是 90% 情况下的根因。
3. **目录里不要塞巨大二进制**。图片走视觉抽取，几个 G 的 RAW 图会让单次 token 消耗爆掉，且对图谱质量贡献很小。先做一轮人工筛选再灌。

---

## 四、命令全景：从单次构建到持续同步

README 在 Usage 段落里把命令按"一次性 vs 持续"分得清楚。我把它翻译成中文决策表：

| 你想做什么 | 命令 | 触发链路 |
|------------|------|----------|
| 首次跑全量 | `/graphify ./raw` | tree-sitter + Claude 视觉 + Leiden 社区 |
| 跑得更激进，多挖 INFERRED 边 | `/graphify ./raw --mode deep` | 同上，但 INFERRED 边更密 |
| 增量更新 | `/graphify ./raw --update` | SHA256 缓存对比，只重处理变更文件 |
| 加一个外部资料进图 | `/graphify add https://arxiv.org/abs/1706.03762` | 抓取 + 落盘 + 入图 |
| 加一条推文 | `/graphify add https://x.com/karpathy/status/...` | 抓取 + 入图 |
| 跨节点问"什么连什么" | `/graphify query "what connects attention to the optimizer?"` | 直接查 `graph.json` |
| 找两个节点的最短路径 | `/graphify path "DigestAuth" "Response"` | NetworkX 路径 |
| 单点解释 | `/graphify explain "SwinTransformer"` | 调 Claude 读上下文 |
| 后台常驻、自动同步 | `/graphify ./raw --watch` | 监听 fsnotify（文件系统变更通知） |
| 给 agent 生成可读 wiki | `/graphify ./raw --wiki` | 每个社区一篇 Markdown + index.md |
| 导出图文件 | `--svg` / `--graphml`（Gephi、yEd） / `--neo4j`（生成 cypher.txt） | 静态导出 |
| 给本地代理开 MCP（Model Context Protocol，模型与外部工具的标准连接协议）服务 | `/graphify ./raw --mcp` | 启动 stdio MCP server |
| 自动跟着 git commit 更新 | `graphify hook install` | post-commit hook，每次提交重建 |

`--watch` 模式的官方说法是"代码保存即时重建，文档/图片变更提醒你跑 `--update`"——也就是说代码路径是 **自动的 AST 重建**，文档/图片路径是 **轻通知 + 你主动决定**。这在多个 agent 改同一份代码的并行工作流里特别有用。

`graphify hook install` 则把"重建图"绑到 git commit 上：每次提交后自动跑一次，不占后台进程，**适合"我不想要常驻进程，但希望图随 commit 演进"** 的轻量场景。

---

## 五、Worked examples：README 自带的 3 个对照实验

README 的"Worked examples"段落放了三个 `worked/{slug}/` 目录，每个都含原始输入和实际输出，可以直接复现：

| Corpus | 文件数 | 压缩比 | 路径 |
|--------|--------|--------|------|
| Karpathy 仓库 + 5 篇论文 + 4 张图 | 52 | **71.5×** | `worked/karpathy-repos/` |
| Graphify 源码 + Transformer 论文 | 4 | 5.4× | `worked/mixed-corpus/` |
| httpx（合成 Python 库） | 6 | ~1× | `worked/httpx/` |

README 自己对这组数据给出的解读是：

> Token 压缩比随语料规模缩放。6 个文件本来就能塞进上下文窗口，图的价值在于结构清晰度，而不是压缩。**到 52 个文件（代码 + 论文 + 图片），你才能拿到 71×+**。

这条边界很重要：**别拿 Graphify 压 5 个文件**，收益不抵开销。**它的甜区是"几十到几百个跨模态文件"**——这恰好是"Karpathy /raw 目录"型工作流的真实体量。

---

## 六、技术栈与架构定位

把 README 的 Tech stack 段落直接展开：

> NetworkX + Leiden（graspoclass）+ tree-sitter + Claude + vis.js。**不依赖 Neo4j，不依赖外部服务，完全本地运行。**

这意味着三件事：

1. **零基础设施**。不装 Neo4j、不开端口、不配 docker——只要 Python + Claude API key 就能跑。
2. **导出路径很宽**。想继续在 Neo4j 里做分析？`--neo4j` 给你 `cypher.txt`。想在 Gephi 里做可视化？`--graphml` 给你 `graph.graphml`。想给本机 agent 当知识库？`--mcp` 开个 stdio server。
3. **被 GraphRAG 这类学术范式影响明显**。"代码 + 文档 + 论文 + 图片"全图谱化是 GraphRAG（基于图的检索增强生成）的工程化版本；差别在于 Graphify 把它装进一个可被 `/graphify` 调用的本地 Skill，而 GraphRAG 的多数实现还在原型 / 服务化阶段。

README 还提到了一个 `ARCHITECTURE.md` 文档，用于添加新语言支持与模块职责切分——如果你打算让 Graphify 支持它目前没列的语言（如 Zig、Nim），入口就在那里。

---

## 七、适用边界与决策建议

基于 README 给出的能力图谱，**什么时候该用、什么时候别用** 可以这样画：

### 7.1 适合用 Graphify 的场景

- 你的个人知识库 / research 目录里堆了几十到几百个 **跨模态** 文件：源码 + 论文 + 笔记 + 截图。
- 你用 Claude Code / Codex，希望"打开代理就有一张图谱可用"，不需要另起一个 RAG 服务。
- 你想要 **可移植的图谱产物**：`graph.json` 喂给别的工具、`--neo4j` 进图数据库、`--mcp` 喂给另一个 agent。
- 你重视"看到了什么 / 猜到了什么"的区分——`EXTRACTED / INFERRED / AMBIGUOUS` 的边标签直接写进 JSON。
- 你不想为图谱单独维护服务进程，`graphify hook install` 这种"绑 commit"的轻同步很合你胃口。

### 7.2 不太适合的场景

- **不到 10 个文件**的小目录。直接读原文更快、也准。Graphify 的"图谱价值"在结构而非压缩。
- **高度动态的、秒级变更的目录**。`--watch` 适合分钟级；实时性更强的场景需要另想办法。
- **需要工业级图数据库查询能力**（如十几亿边的子图匹配）。Graphify 是个人/小团队工具，不是替代 Neo4j。
- **完全闭源 / 完全离线的代码仓**。代码抽取本地，但文档/图片抽取依赖 Claude。
- **要求"答案有出处 + 严格可溯源"** 的合规场景。INFERRED 边本身是模型推断，不要把它当成"事实"。

### 7.3 决策顺序

如果你是 Claude Code 重度用户、并且手头真的有"几十到几百个跨模态文件"，建议按这个顺序上手：

1. 装包：优先 `pipx install graphifyy`（绕开 Windows PATH / macOS externally-managed 两个常见坑）。
2. 挑一个 30–60 个文件的子目录试 `/graphify .`，**先看 `graph.html` 与 `GRAPH_REPORT.md` 感受质量**。
3. 满意后再 `/graphify add` 把 arxiv 论文一条条灌进来。
4. 长期使用：用 `graphify hook install` 把"随 commit 更新"绑上，避免后台常驻。
5. 导出：如果发现图谱想长期沉淀，再考虑 `cypher.txt` 导入 Neo4j 或 `--mcp` 喂给另一个 agent。

---

## 八、参考与延伸

- 仓库主页：<https://github.com/Graphify-Labs/graphify>
- 原始作者仓库（README 顶部 CI badge 指向）：<https://github.com/safishamsi/graphify>
- ARCHITECTURE.md（模块职责与新增语言支持，README 中提及）
- worked/ 目录（三个对照实验的可复现样例）
- 概念对应：GraphRAG（基于图的检索增强生成）、Agent Skills（AI 代理可加载的技能规范）、MCP（Model Context Protocol，模型与外部工具的标准连接协议）
