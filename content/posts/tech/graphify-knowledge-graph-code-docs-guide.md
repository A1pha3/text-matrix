+++
date = '2026-04-30T11:30:00+08:00'
draft = false
title = 'Graphify：将任意文件夹转化为可查询的知识图谱'
slug = 'graphify-knowledge-graph-code-docs-guide'
description = 'Graphify 是一个 Python 本地运行的 AI 编码助手技能，能将代码、文档、PDF、图片甚至视频转化为可查询的知识图谱，无需 Neo4j、无需服务器。'
categories = ['技术笔记']
tags = ['AI', '知识图谱', 'Python', '开源']
+++

# Graphify：将任意文件夹转化为可查询的知识图谱

> Graphify 是一个由 Python 驱动、本地运行的 AI 编码助手技能，能将代码、文档、PDF、图片甚至视频转化为可查询的知识图谱。MIT 许可证、Python 3.10+ 即可运行，无需 Neo4j、无需服务器。在 Karpathy 的混合语料（52 个文件）测试中，每个查询的 token 消耗比直接读取原始文件降低 **71.5 倍**。

<!--more-->

## 目录

- [1. 背景与核心价值](#1-背景与核心价值)
- [2. 核心概念解析](#2-核心概念解析)
- [3. 技术原理：六阶段处理管线](#3-技术原理六阶段处理管线)
- [4. 多模态文件处理：代码、文档、图片、视频](#4-多模态文件处理代码文档图片视频)
- [5. 系统架构与模块设计](#5-系统架构与模块设计)
- [6. 安装与配置](#6-安装与配置)
- [7. 实战演示](#7-实战演示)
- [8. 开发扩展与 API](#8-开发扩展与-api)
- [9. 常见问题与故障排除](#9-常见问题与故障排除)
- [10. 总结与未来展望](#10-总结与未来展望)

---

## 1. 背景与核心价值

### 1.1 为什么需要 Graphify

在日常开发中，知识散落在各处：代码文件、README 文档、学术论文、架构图、会议截图、项目笔记。当你想问"Attention 机制和优化器之间有什么联系？"时，你需要通读所有相关文件才能找到答案——这个过程既缓慢又低效。

Graphify 的诞生就是为了解决这个问题。它的灵感来自 Andrej Karpathy 的工作方式：他在一个 `/raw` 文件夹中存放论文、推文截图和笔记。Graphify 是对这一工作流的系统性回答——通过构建**可查询的知识图谱**，让 AI 能够在索引后的结构化知识中快速找到跨文件的隐含联系。

### 1.2 核心价值主张

| 维度 | 传统方式（读原始文件） | Graphify 方式（图谱查询） |
|------|----------------------|--------------------------|
| Token 消耗 | O(n) 随语料线性增长 | **71.5 倍**压缩（52 文件测试） |
| 跨域关联 | 需要人工建立连接 | 自动发现代码-论文、代码-图片关联 |
| 查询能力 | 只能关键词搜索 | 自然语言提问 + 图路径查询 |
| 增量更新 | 全量重新读取 | SHA256 缓存，只重处理变化文件 |
| 持久化 | 每次会话重读 | graph.json 跨会话保留 |

### 1.3 项目概览

```
仓库：      safishamsi/graphify
Stars：    38,379（截至 2026-04-30）
创建时间：  2026-04-03
许可证：    MIT
语言：      Python
版本：      0.5.5
PyPI：      graphifyy（graphify 名称正在认领中）
主页：      https://graphifylabs.ai/
默认分支：  v5
```

支持的主流 AI 编码助手：

- **Claude Code**（核心平台）、Claude Desktop
- **GitHub Copilot CLI**、**OpenCode**、**Cursor**、**Gemini CLI**
- **Aider**、**OpenClaw**、**Factory Droid**、**Trae**、**Kiro**、**VS Code Copilot Chat**

---

## 2. 核心概念解析

### 2.1 知识图谱的基本结构

Graphify 构建的知识图谱以**节点（Node）** 和**边（Edge）** 为基本元素：

```json
// 节点结构
{
  "id": "unique_string",          // 全局唯一标识符
  "label": "human name",         // 人类可读的节点名称
  "source_file": "path/to/file", // 来源文件路径
  "source_location": "L42"        // 源代码行号（可选）
}

// 边结构
{
  "source": "node_id_a",
  "target": "node_id_b",
  "relation": "calls|imports|uses|...",  // 关系类型
  "confidence": "EXTRACTED|INFERRED|AMBIGUOUS"  // 置信度
}
```

### 2.2 三种置信度标签

理解 Graphify 的置信度体系是正确使用工具的关键：

| 标签 | 含义 | 典型来源 |
|------|------|---------|
| `EXTRACTED` | 关系在源码中**明确陈述** | import 语句、函数调用、显式引用 |
| `INFERRED` | 关系是**合理推断** | 调用图二遍分析、共现场景推断 |
| `AMBIGUOUS` | 关系**不确定**，需人工复核 | LLM 生成的低置信度关联 |

这种标注体系让用户始终清楚哪些是"事实"、哪些是"猜测"——这在代码-论文混合图谱中尤为重要。

### 2.3 社区检测与 God Nodes

Graphify 使用 **Leiden 算法**（via graspologic）对图谱进行社区检测（Community Detection）。其核心输出包括：

- **God Nodes（神节点）**：度数最高的概念节点——所有其他节点都通过它相连。例如在机器学习语料中，`Tensor`、`Layer`、`Forward` 往往会成为 God Nodes，它们是整个知识网络的中枢。
- **Surprising Connections**：跨域关联（代码↔论文边权重高于代码↔代码），每个连接附带自然语言解释。
- **Suggested Questions**：图谱"专属问题"——那些只有通过图结构才能回答的问题。

### 2.4 图谱输出格式

```
graphify-out/
├── graph.html       # 交互式可视化（vis.js，点击节点、搜索、按社区过滤）
├── obsidian/        # Obsidian 知识库 Vault，可直接导入 Obsidian
├── wiki/            # Wikipedia 风格的 Markdown 文章（供 AI agent 导航）
├── graph.json       # 持久化图谱文件，跨会话查询
├── GRAPH_REPORT.md  # 报告：God Nodes、跨域连接、建议问题
└── cache/           # SHA256 缓存——只重处理变化的文件
    ├── ast/         # 代码 AST 缓存
    └── semantic/    # LLM 语义提取缓存
```

---

## 3. 技术原理：六阶段处理管线

Graphify 的处理流程由六个独立阶段组成，每阶段职责单一，通过 Python dict 和 NetworkX 图对象传递数据，无共享状态，无外部副作用：

```
detect()  →  extract()  →  build_graph()  →  cluster()  →  analyze()  →  report()  →  export()
```

### 3.1 阶段一：detect — 文件发现

`detect.py` 的 `collect_files(root)` 函数负责扫描目标目录，返回过滤后的文件路径列表。过滤规则基于文件扩展名分组：

| 文件类型 | 扩展名 |
|---------|--------|
| 代码 | `.py .ts .js .go .rs .java .c .cpp .rb .cs .kt .scala .php .swift .lua .zig .ps1 .ex .m .jl .v` |
| 文档 | `.md .txt .rst .mdx .html` |
| 图片 | `.png .jpg .webp .gif` |
| PDF | `.pdf`（需 `graphifyy[pdf]`） |

实现要点：`detect.py` 中定义了 `CODE_EXTENSIONS`、`DOC_EXTENSIONS` 等常量，`collect_files()` 根据这些常量过滤文件，隐蔽地忽略 `node_modules`、`__pycache__`、`.git` 等无关目录。

### 3.2 阶段二：extract — 多模态内容提取

`extract.py` 是整个管线中最复杂的模块，它为不同文件类型调用不同的提取器：

**代码文件（基于 tree-sitter AST）**

```python
# 伪代码展示 extract() 的分发逻辑
def extract(path: Path) -> dict:
    suffix = path.suffix.lower()
    if suffix in CODE_EXTENSIONS:
        return extract_code_ast(path)   # tree-sitter 解析
    elif suffix in DOC_EXTENSIONS:
        return extract_semantic(path)    # LLM 概念提取
    elif suffix in IMAGE_EXTENSIONS:
        return extract_vision(path)     # Claude Vision 多语言图片理解
    elif suffix == ".pdf":
        return extract_pdf(path)        # PDF 文字提取 + LLM 语义
    ...
```

**代码提取的 two-pass 策略：**

1. **Pass 1（AST 解析）**：使用 tree-sitter 解析代码 AST，提取函数、类、变量、import/export 语句，生成节点和 `EXTRACTED` 置信度的边。
2. **Pass 2（调用图推断）**：基于 Pass 1 的结果进行跨函数/跨文件调用关系推断，生成 `INFERRED` 置信度的边。对于 Python、Java、Go、Rust 等语言，还支持**跨文件调用解析**——未解析的调用目标会保存为 `raw_calls`，在全局标签映射完成后进行统一解析。

**文档文件（基于 LLM 语义）**

对于 Markdown、纯文本等文档文件，Graphify 调用 LLM（默认 Claude）进行概念和关系的语义提取：

```
输入：README.md 文本内容
输出：{"nodes": [...], "edges": [...]}  # LLM 从文本中提取概念节点和关系边
```

**图片文件（基于 Claude Vision）**

Graphify 通过 Claude Vision API 处理图片，支持：
- 截图、架构图、流程图
- 其他语言的图片（中文、日文等文档照片）
- 白板照片、手绘示意图

**PDF 文件（可选依赖）**

需安装 `graphifyy[pdf]`，使用 `pypdf` + `html2text` 提取文本，再走 LLM 语义提取管线。

### 3.3 阶段三：build_graph — 图谱构建

`build.py` 的 `build_graph(extractions)` 接收所有提取结果（节点列表 + 边列表），构建 NetworkX 无向图对象：

```python
import networkx as nx

def build_graph(extractions: list[dict]) -> nx.Graph:
    G = nx.Graph()
    for extraction in extractions:
        for node in extraction["nodes"]:
            G.add_node(node["id"], **node)
        for edge in extraction["edges"]:
            G.add_edge(edge["source"], edge["target"], **edge)
    return G
```

去重逻辑通过 `deduplicate_by_label()` 合并同标签节点，跨文件节点 ID 碰撞通过文件路径前缀规范化解决。

### 3.4 阶段四：cluster — 社区检测

`cluster.py` 使用 Leiden 算法（via graspologic）对图谱进行社区检测，为每个节点标注 `community` 属性：

```python
# 伪代码
def cluster(G: nx.Graph) -> nx.Graph:
    from graspologic.algorithms import cluster as leiden_cluster
    partition = leiden_cluster(G, algorithm="leiden")
    for node, community_id in partition.items():
        G.nodes[node]["community"] = community_id
    return G
```

Leiden 算法相比 Louvain 具有更严格的理论保证，能产生更紧密、更少碎片化的社区结构。

### 3.5 阶段五：analyze — 图谱分析

`analyze.py` 在社区检测后的图上计算高级语义：

```python
def analyze(G: nx.Graph) -> dict:
    return {
        "god_nodes": god_nodes(G, top_n=10),           # 度数最高的中枢节点
        "surprises": surprising_connections(G),       # 跨域惊奇连接
        "questions": suggested_questions(G),           # 建议提问
        "stats": {
            "total_files": ..., "total_nodes": ...,   # 统计摘要
            "edge_distribution": ...
        }
    }
```

**God Nodes 计算**：按节点度数（连接数）排序，取 Top N。度数高意味着该概念与多个其他概念相连，是跨领域知识的中介。

**Surprising Connections**：边按复合权重排序，代码-论文边权重高于代码-代码边。每个结果附带自然语言解释"Why this matters"。

### 3.6 阶段六：report + export — 报告与导出

`report.py` 渲染 GRAPH_REPORT.md，`export.py` 负责多格式导出：

| 格式 | 说明 | 适用场景 |
|------|------|---------|
| `graph.json` | 完整图谱（节点 + 边 + 属性） | 跨会话持久化、MCP 服务 |
| `graph.html` | vis.js 交互式可视化 | 浏览器探索、演示 |
| `obsidian/` | Obsidian Vault | Obsidian 用户、链接笔记 |
| `wiki/` | Wikipedia 风格 Markdown | AI Agent 自动导航 |
| `graph.svg` | 静态矢量图（需 `graphifyy[svg]`） | 文档嵌入 |
| `graph.graphml` | GraphML 格式 | Gephi、yEd 等专业图工具 |
| `cypher.txt` | Neo4j Cypher 语句 | Neo4j 知识库导入 |
| MCP stdio | MCP 协议服务 | 与支持 MCP 的 AI 工具集成 |

---

## 4. 多模态文件处理：代码、文档、图片、视频

### 4.1 代码解析：tree-sitter AST + 调用图推断

Graphify 的代码解析是业界最完整的方案之一，当前支持 **21 种编程语言**：

```
Python、TypeScript/JavaScript、Go、Rust、Java、C、C++、
Ruby、C#、Kotlin、Scala、PHP、Swift、Lua、Zig、
PowerShell、Elixir、Objective-C、Julia、Verilog
```

每种语言的解析器均为 tree-sitter 的独立 npm 包，在 `pyproject.toml` 中声明为依赖：

```toml
[project.optional-dependencies]
leiden = ["graspologic; python_version < '3.13'"]
```

**添加新语言提取器的标准流程**（详见 ARCHITECTURE.md）：

1. 在 `extract.py` 添加 `extract_<lang>(path: Path) -> dict` 函数
2. 在 `extract()` 的分发表和 `collect_files()` 中注册文件后缀
3. 在 `detect.py` 的 `CODE_EXTENSIONS` 和 `watch.py` 的 `_WATCHED_EXTENSIONS` 中添加后缀
4. 在 `pyproject.toml` 添加 tree-sitter 语言包依赖
5. 在 `tests/fixtures/` 添加测试 fixture，在 `tests/test_languages.py` 添加测试

**TypeScript `@/` 路径别名解析**（v0.5.1+）：通过读取项目中的 `tsconfig.json` 解析 `@/` 别名，将其映射为实际文件路径，确保跨模块调用边准确生成。

**Go 包限定调用保留**（v0.5.5+）：`pkg.Func()` 形式的 Go 包限定调用不再被错误地剥离为裸函数名，避免跨文件调用解析错误。

### 4.2 文档处理：语义提取管线

支持的文档格式：

- **Markdown**（`.md`）、**reStructuredText**（`.rst`）、**纯文本**（`.txt`）
- **HTML**（`.html`，v0.4.23+）
- **MDX**（`.mdx`，v0.4.22+）

文档提取不走 AST，而是通过 LLM 的语义理解能力，从文本中提取"概念节点"和"语义关系边"。例如，一篇关于 Transformer 的博客会被解析为：

```
节点：Attention、Multi-Head、Scaled Dot-Product、Positional Encoding、Feed-Forward
边：(Attention → Multi-Head, "is_component_of")、
    (Scaled Dot-Product → Attention, "used_by")
置信度：全部 INFERRED（从文本推断，非显式声明）
```

### 4.3 图片处理：多语言视觉理解

Graphify 的图片处理完全依赖 Claude Vision API，**不进行 OCR**（这是关键区别——它做的是视觉语义理解，不是文字识别）。支持的图片类型：

- **截图**：代码截图、错误信息截图、UI 界面截图
- **架构图 / 流程图**：Mermaid、draw.io、PlantUML 等工具导出的图片
- **手绘草图**：白板照片、笔记本手绘
- **其他语言文档**：中文技术文档图片、日文论文截图等

提取结果与文档处理类似：节点是图片中识别的概念，边界是概念之间的关系。Claude Vision 能理解图片的语义内容并将其结构化。

### 4.4 PDF 论文处理

需安装可选依赖：

```bash
pip install 'graphifyy[pdf]'   # 提供 pypdf + html2text
```

处理流程：

1. `pypdf` 提取 PDF 文本内容
2. `html2text` 处理排版（保留层次结构）
3. LLM 语义提取：概念节点 + 引文关系 + 方法关联
4. 论文特有：引文网络（Paper A → Paper B，"cites"关系）

### 4.5 视频与音频处理（可选）

```bash
pip install 'graphifyy[video]'  # 提供 faster-whisper + yt-dlp
```

处理 YouTube 视频或其他视频文件中的字幕/语音内容，将其转化为可图谱化的文本。

---

## 5. 系统架构与模块设计

### 5.1 整体架构

Graphify 采用**管线架构**（Pipeline Architecture），各阶段职责单一，通过 Python dict 和 NetworkX 图对象传递数据：

```
用户输入（文件夹/URL）
         │
         ▼
┌──────────────────────────────────────────────┐
│  CLI / Skill 入口（__main__.py / skill.md）   │
└─────────────────┬────────────────────────────┘
                  │
         ┌────────▼────────┐
         │   detect.py      │  ← 文件发现
         │ collect_files()   │
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │   cache.py      │  ← SHA256 缓存层（增量更新）
         │ check_semantic_  │
         │ cache()          │
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │   extract.py    │  ← 多模态内容提取
         │ extract()       │  （tree-sitter / LLM / Vision）
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │   build.py      │  ← NetworkX 图构建
         │ build_graph()   │
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │  cluster.py     │  ← Leiden 社区检测
         │ cluster()       │  （graspologic）
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │  analyze.py     │  ← God Nodes / 惊奇连接
         │ analyze()       │
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │  report.py     │  ← GRAPH_REPORT.md 生成
         │ render_report()│
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │  export.py      │  ← 多格式导出
         │ export()        │  （JSON / HTML / Obsidian / Wiki）
         └─────────────────┘
```

### 5.2 核心模块职责表

| 模块 | 核心函数 | 输入 → 输出 | 依赖 |
|------|---------|-----------|------|
| `detect.py` | `collect_files(root)` | 目录路径 → `[Path]` 过滤列表 | 标准库 |
| `cache.py` | `check/save_semantic_cache` | 文件列表 → (已缓存, 未缓存) 分组 | hashlib |
| `extract.py` | `extract(path)` | 文件路径 → `{nodes, edges}` | tree-sitter、LLM API |
| `build.py` | `build_graph(extractions)` | 提取结果列表 → `nx.Graph` | networkx |
| `cluster.py` | `cluster(G)` | 图 → 附有 community 属性的图 | graspologic |
| `analyze.py` | `analyze(G)` | 图 → 分析字典 | networkx |
| `report.py` | `render_report(G, analysis)` | 图+分析 → Markdown 报告 | Jinja2 |
| `export.py` | `export(G, out_dir, ...)` | 图 → 多格式文件 | networkx、Jinja2 |
| `ingest.py` | `ingest(url, ...)` | URL → 下载保存到 corpus | requests |
| `security.py` | `validate_*()` | URL/路径/标签 → 验证或抛异常 | urllib、tldextract |
| `validate.py` | `validate_extraction(data)` | 提取字典 → 校验或抛异常 | jsonschema |
| `serve.py` | `start_server(graph_path)` | 图文件路径 → MCP stdio 服务器 | sse-starlette |
| `watch.py` | `watch(root, flag_path)` | 目录 → 变化时写标志文件 | watchdog |

### 5.3 增量更新机制

Graphify 的增量更新通过 **SHA256 缓存**实现，这是其高效性的关键：

```
cache/
├── ast/        # 代码 AST 缓存（文件内容哈希）
└── semantic/  # LLM 语义提取缓存（内容哈希）
```

- `--update` 时：计算文件内容 SHA256，与缓存对比，只重处理变化的文件
- `--watch` 时：后台监控目录，代码文件保存触发即时 AST 重建；文档/图片变化通知用户手动 `--update`
- **Git Hook 模式**（`graphify hook install`）：每次 `git commit` 后自动触发增量图谱重建，无后台进程依赖

### 5.4 安全机制

`security.py` 是 Graphify 的安全护城河，所有外部输入必须通过它：

| 验证函数 | 防护目标 |
|---------|---------|
| `validate_url()` | 只允许 http/https，阻止 `file://` SSRF |
| `safe_fetch()` | 请求体大小上限 + 超时控制 |
| `_NoFileRedirectHandler` | 阻止 DNS 重绑定绕过 |
| `validate_graph_path()` | 确保图文件路径在 `graphify-out/` 内 |
| `sanitize_label()` | 去除控制字符、最大 256 字符、HTML 转义 |

> v0.5.4 修复：SSRF DNS 重绑定漏洞——`safe_fetch` 在整个请求期间 patch `socket.getaddrinfo`，彻底封堵 DNS rebinding 攻击。

---

## 6. 安装与配置

### 6.1 系统要求

- **Python**: 3.10+（支持 Python 3.14+，v0.5.5+ 已移除上限约束）
- **AI 模型**: Claude Code（默认）、Kimi K2.6（可选，v0.5.5+）
- **操作系统**: macOS、Linux、Windows（PowerShell）

### 6.2 标准安装（推荐）

```bash
# 安装 PyPI 包
pip install graphifyy && graphify install

# 验证安装
graphify --version
```

> 注意：PyPI 包名临时为 `graphifyy`，因为 `graphify` 名称正在与 PyPI 官方协商认进程中。CLI 命令和 Skill 命令仍然是 `graphify`。

### 6.3 手动安装（curl，适用于所有平台）

```bash
# 创建技能目录
mkdir -p ~/.claude/skills/graphify

# 下载 Skill 文件
curl -fsSL https://raw.githubusercontent.com/safishamsi/graphify/v1/skills/graphify/skill.md \
  > ~/.claude/skills/graphify/SKILL.md
```

然后在 `~/.claude/CLAUDE.md` 中添加：

```markdown
- **graphify** (`~/.claude/skills/graphify/SKILL.md`) - any input to knowledge graph.
  Trigger: `/graphify`
When the user types `/graphify`, invoke the Skill tool with `skill: "graphify"` before doing anything else.
```

### 6.4 uv 方式安装（无需 pip）

```bash
uv tool install graphifyy
# 或无需安装直接运行：
uvx graphifyy install
```

### 6.5 可选依赖安装

```bash
# 完整功能（所有可选依赖）
pip install 'graphifyy[all]'

# 按需拆分安装
pip install 'graphifyy[mcp]'          # MCP 服务器支持
pip install 'graphifyy[neo4j]'        # Neo4j 导出
pip install 'graphifyy[pdf]'          # PDF 处理
pip install 'graphifyy[watch]'        # 文件监控
pip install 'graphifyy[svg]'          # SVG 导出
pip install 'graphifyy[leiden]'       # Leiden 社区检测（Python < 3.13）
pip install 'graphifyy[office]'      # Word/Excel 处理
pip install 'graphifyy[video]'        # 视频/音频处理
pip install 'graphifyy[kimi]'         # Kimi K2.6 后端
```

### 6.6 Windows 特殊说明

Windows 用户安装后需确保 `Scripts` 目录在 PATH 中：

```powershell
# pip 安装时注意 Python 安装路径
# 典型路径：%APPDATA%\Python\PythonXY\Scripts
# 也可使用 pipx：
pipx ensurepath
```

---

## 7. 实战演示

### 7.1 基础使用：构建当前目录的知识图谱

```bash
# 进入任意项目目录
cd ~/projects/my-awesome-ai/

# 在 Claude Code 中输入：
/graphify .

# 或命令行直接运行：
graphify .
```

Graphify 会自动扫描目录，识别文件类型，提取内容，构建图谱。处理完成后输出：

```
graphify-out/
├── graph.html       # 打开浏览器访问交互式图谱
├── obsidian/        # 可导入 Obsidian
├── graph.json       # 持久化图谱
└── GRAPH_REPORT.md  # 报告摘要
```

### 7.2 指定目录与深度模式

```bash
# 针对特定文件夹
/graphify ./raw

# 深度提取模式（更激进的 INFERRED 边提取）
/graphify ./raw --mode deep

# 构建 Agent 可爬取的 Wiki
/graphify ./raw --wiki
```

### 7.3 增量更新

```bash
# 只重处理变化的文件，合并到现有图谱
/graphify ./raw --update
```

### 7.4 图谱查询

```bash
# 自然语言提问
graphify query "what connects attention to the optimizer?"

# 路径查询：找出两个节点之间的路径
graphify path "DigestAuth" "Response"

# 节点解释
graphify explain "SwinTransformer"
```

### 7.5 添加外部资料

```bash
# 添加 ArXiv 论文
graphify add https://arxiv.org/abs/1706.03762

# 添加 Twitter 推文
graphify add https://x.com/karpathy/status/1234567890
```

### 7.6 监听文件变化

```bash
# 后台监控，文件变化自动重建图谱
# 代码保存 → 即时 AST 重建（无需 LLM）
# 文档/图片变化 → 通知手动 --update
/graphify ./raw --watch
```

### 7.7 Git Hook 自动构建

```bash
# 安装 post-commit hook
graphify hook install

# 每次 git commit 后自动触发增量图谱重建
# 无需后台进程，支持 Husky 等工具配置的 hooksPath
```

### 7.8 多格式导出

```bash
# SVG 矢量图（需 [svg] 依赖）
/graphify ./raw --svg

# GraphML（用于 Gephi、yEd）
/graphify ./raw --graphml

# Neo4j Cypher（导入 Neo4j）
/graphify ./raw --neo4j

# MCP 服务（支持 MCP 的 AI 工具直接连接）
/graphify ./raw --mcp
```

### 7.9 跨仓库图谱合并

```bash
# 克隆并图谱化任意公开仓库
graphify clone https://github.com/facebookresearch/llama

# 合并多个 graph.json 为跨仓库大图谱
graphify merge-graphs graphify-out-1/graph.json graphify-out-2/graph.json
```

### 7.10 Token 基准测试

每次运行后 Graphify 会自动打印 token 消耗基准。在 Karpathy repos + 5 篇论文 + 4 张图片（共 52 个文件）的混合语料上：

| 查询方式 | Token 消耗 | 压缩比 |
|---------|-----------|--------|
| 读原始文件 | ~1,200,000 tokens | 1x |
| Graphify 图谱查询 | ~16,800 tokens | **71.5x** |

---

## 8. 开发扩展与 API

### 8.1 作为 Python 库使用

Graphify 的所有管线阶段都可以通过 Python API 调用：

```python
from graphify import detect, extract, build, cluster, analyze, export

# 1. 发现文件
files = detect.collect_files("./my-project")

# 2. 提取内容（可并行的最佳位置）
extractions = [extract.extract(f) for f in files]

# 3. 构建图谱
G = build.build_graph(extractions)

# 4. 社区检测
G = cluster.cluster(G)

# 5. 分析
analysis = analyze.analyze(G)

# 6. 导出
export.to_json(G, "graphify-out/graph.json")
export.to_html(G, "graphify-out/graph.html")
export.to_obsidian(G, "graphify-out/obsidian/")
```

### 8.2 MCP 服务器

Graphify 提供 MCP（Model Context Protocol）stdio 服务器，可与支持 MCP 的 AI 工具集成：

```bash
# 启动 MCP 服务器
graphify serve graphify-out/graph.json

# 或通过 --mcp 标志
graphify --mcp ./graphify-out/graph.json
```

MCP 服务器暴露的能力：
- 图谱查询（自然语言）
- 路径查找
- 节点解释
- 图结构统计

### 8.3 自定义 LLM 后端（Kimi K2.6）

v0.5.5+ 支持 Kimi K2.6 作为语义提取后端：

```bash
pip install 'graphifyy[kimi]'
export MOONSHOT_API_KEY="your-kimi-api-key"
```

Kimi K2.6 在关系提取丰富度上比 Claude 高 3-6 倍，成本约为 1/3。需要设置 `KIMI_BASE_URL` 和 `KIMI_MODEL` 环境变量来自定义端点。

### 8.4 插件 Skill 机制

Graphify 提供了多个平台的 Skill 文件：

| 平台 | 文件 | 安装命令 |
|------|------|---------|
| Claude Code | `skill.md` | `graphify install` |
| Codex | `skill-codex.md` | `graphify codex install` |
| OpenCode | `skill-opencode.md` | `graphify opencode install` |
| Aider | `skill-aider.md` | — |
| Copilot | `skill-copilot.md` | `graphify vscode install` |
| OpenClaw | `skill-claw.md` | — |
| Droid | `skill-droid.md` | — |
| Trae | `skill-trae.md` | — |
| Kiro | `skill-kiro.md` | — |
| VS Code | `skill-vscode.md` | `graphify vscode install` |
| Windows | `skill-windows.md` | — |

每个 Skill 文件都是一个独立的提示词模板，定义了如何将 Graphify 的输出格式化为对应平台可消费的上下文。

### 8.5 添加新语言提取器

标准流程（见 ARCHITECTURE.md）：

```python
# 1. 在 extract.py 添加提取函数
def extract_zig(path: Path) -> dict:
    from tree_sitter_zig import parser
    # AST 解析 → 节点和边
    # 调用图二遍分析 → INFERRED edges
    return {"nodes": [...], "edges": [...]}

# 2. 在 extract.py 分发表中注册
EXTRACTORS = {
    ".py": extract_python,
    ".zig": extract_zig,  # 新增
    ...
}

# 3. 在 detect.py 的 CODE_EXTENSIONS 添加
CODE_EXTENSIONS = {".py", ".zig", ...}

# 4. 在 pyproject.toml 添加依赖
dependencies = ["tree-sitter-zig"]

# 5. 在 watch.py 的 _WATCHED_EXTENSIONS 添加
# 6. 添加测试 fixture
```

---

## 9. 常见问题与故障排除

### 9.1 安装问题

**Q: `graphify: command not found`**
- 确保 pip 安装目录在 PATH 中（Linux/macOS: `~/.local/bin`）
- Windows: 检查 `%APPDATA%\Python\PythonXY\Scripts`
- 或使用 `python -m graphify` 代替

**Q: Skill 版本过期警告**
- 运行 `graphify install` 刷新所有平台的 skill 文件（v0.4.23+ 支持跨平台同步刷新）

### 9.2 处理问题

**Q: 某文件类型被静默跳过**
- 检查文件扩展名是否在支持列表中（参考第 4 节）
- `.mjs`、`.ejs`、`.mdx` 支持分别从 v0.4.16、v0.4.15、v0.4.22 开始

**Q: 跨文件调用边丢失**
- 确保文件扩展名在代码支持列表中
- 检查是否触发了 phantom god nodes 问题（v0.5.5 已修复）
- 对于 Go，检查包限定调用格式（`pkg.Func()`）

**Q: 图片/文档提取结果为空**
- 确认 API Key 配置正确（`ANTHROPIC_API_KEY` 或 `MOONSHOT_API_KEY`）
- 检查网络连接

### 9.3 图谱质量问题

**Q: God Nodes 都是无意义的通用词**
- 使用 `--mode deep` 进行更激进的过滤
- 或在 GRAPH_REPORT.md 中使用 `AMBIGUOUS` 标记手动复核

**Q: 节点 ID 碰撞（同文件名不同目录）**
- v0.5.1+ 已修复，节点 ID 现在包含相对路径前缀
- 旧图谱需删除 `graphify-out/` 后重新构建

### 9.4 安全问题

**Q: `safe_fetch` 报 SSRF 错误**
- 确保 URL 是 http/https（不接受 file://）
- v0.5.4+ 已彻底修复 DNS rebinding 问题

---

## 10. 总结与未来展望

### 10.1 技术亮点回顾

Graphify 之所以在发布 27 天内获得 38,379 Stars，源于几个核心创新：

1. **多模态统一抽象**：将代码（AST）、文档（LLM 语义）、图片（Vision）统一为节点-边图结构，消除了不同数据源之间的壁垒。
2. **两-pass 提取策略**：先提取显式关系（EXTRACTED），再推断隐含关系（INFERRED），置信度标注让用户始终掌握信息的确定性。
3. **Leiden 社区检测**：在开放词汇（LLM 提取）图谱上使用严格的社区检测算法，发现知识的中枢和跨域连接。
4. **本地优先 + 增量更新**：无需服务器，SHA256 缓存实现秒级增量更新，Git Hook 模式实现零摩擦的自动化。
5. **多格式导出生态**：Obsidian、Wiki、GraphML、Neo4j、MCP——图谱输出可无缝嵌入现有工作流。

### 10.2 适用场景

- **个人知识管理**：将笔记、论文、代码、图片统一为可查询的知识网络
- **代码库探索**：大型项目（数百个文件）的结构化理解，发现隐藏的依赖关系
- **论文阅读助手**：将多篇相关论文转化为引文网络，找到跨论文的概念关联
- **AI Agent 记忆层**：为 AI Coding Assistant 提供持久化的项目上下文
- **团队知识沉淀**：将文档、图片、手绘草图整合为共享知识图谱
- **GraphRAG**：作为检索增强生成的图谱层，提升 RAG 的召回质量

### 10.3 与传统 RAG 的对比

| 维度 | 传统 RAG | Graphify（图谱 RAG） |
|------|---------|---------------------|
| 索引单元 | Chunk（文本片段） | Node（概念单元） |
| 关系建模 | 无 | EXTRACTED / INFERRED / AMBIGUOUS 三级 |
| 跨域关联 | 弱（依赖关键词重叠） | 强（图结构天然捕获跨域关系） |
| 查询类型 | 关键词/语义相似 | 自然语言 + 路径查询 + 解释生成 |
| 增量更新 | 通常需全量重建 | SHA256 缓存，增量秒级 |
| 可视化 | 无 | 交互式 HTML + Obsidian + Wiki |

### 10.4 生态定位与竞品对比

Graphify 处于 **AI Coding Assistant Skill** 与 **GraphRAG** 的交叉点。类似的工具包括：

- **Nickel**：本地知识库，但不支持代码 AST 解析
- **D介**：传统文档问答，不做知识图谱
- **Obsidian + Dataview**：本地笔记图谱，但无代码理解能力
- **Neo4j + LLM**：完整的图数据库方案，但需要自行搭建 pipeline

Graphify 的差异化在于：**开箱即用的 skill 形态 + tree-sitter 多语言 AST 解析 + LLM 语义提取 + Leiden 社区检测**，四者合一，零配置即可在任意文件夹上构建知识图谱。

### 10.5 社区资源

- **官网**: https://graphifylabs.ai/
- **GitHub**: https://github.com/safishamsi/graphify
- **完整变更日志**: [GitHub Releases](https://github.com/safishamsi/graphify/releases)
- **工作示例**: [`worked/`](https://github.com/safishamsi/graphify/tree/main/worked) 目录提供了 Karpathy repos + 论文 + 图片的完整测试语料及输出结果

### 10.6 结语

Graphify 用 27 天突破 38,379 Stars，折射出一个清晰的需求：**在 AI 时代，我们需要的不是更多的文件，而是更少但更结构化的知识**。当代码、文档、图片、论文都可以被统一抽象为"概念节点"和"关系边"，AI 的查询能力才能真正释放。

更重要的是，Graphify 诚实地区分了"提取"（EXTRACTED）和"推断"（INFERRED）——这种不确定性标注本身就是 AI 辅助人类认知的正确范式。知识图谱不是真理的终点，而是探索的起点。