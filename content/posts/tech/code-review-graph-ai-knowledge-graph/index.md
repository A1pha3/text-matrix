---
title: "code-review-graph：用知识图谱把 AI 代码审查的 token 消耗砍到 1/65"
date: 2026-08-10T03:45:00+08:00
draft: true
categories: ["技术笔记"]
tags: ["code-review-graph", "mcp", "code-intelligence", "tree-sitter", "rag"]
description: "code-review-graph 用 Tree-sitter 将代码库解析为知识图谱，通过 blast-radius 分析和 MCP 协议为 AI 编程工具提供精准上下文，在 6 个真实开源项目的基准测试中实现了约 65 倍的 token 消耗缩减。"
github_repo: "tirth8205/code-review-graph"
source_key: "gh:tirth8205/code-review-graph"
---

## 核心问题：AI 代码审查的 token 浪费

当 AI 编程代理做代码审查时，它面临一个基本问题：为了理解一处改动的影响，需要读多少代码？最简单的做法是把整个仓库喂给模型——但这意味着每次审查都要消耗十几万 token。一个更聪明的代理会用 grep 搜索标识符、只读最相关的文件。但这仍然依赖启发式判断，容易漏掉跨模块的依赖链。

code-review-graph（[tirth8205/code-review-graph](https://github.com/tirth8205/code-review-graph)）的思路是：**预先把代码库解析成知识图谱**，审查时用图查询精确定位受影响的文件，只把这些文件喂给模型。在 6 个真实开源项目的基准测试中，这种方法将每个问题的 token 消耗从全量的数万 token 压缩到平均 2,000-3,500 token，中位缩减约 65 倍。

## 它怎么工作

### 管线：代码 → AST → 图 → 查询

整个系统分四层：

1. **解析层**：用 Tree-sitter 把源代码解析为 AST（抽象语法树），提取函数、类、导入、调用等结构化节点。
2. **图构建层**：将节点存为 SQLite 图数据库中的顶点，调用关系、继承关系、测试覆盖等存为边。
3. **变更追踪层**：文件改动时，通过图的调用边和导入边追踪所有可能受影响的节点——这是 blast-radius 分析。
4. **查询层**：通过 MCP（Model Context Protocol）协议暴露图查询接口，AI 代理在审查时调用获取精准上下文。

### Blast-radius 分析

这是核心机制。当一个文件发生变更时，code-review-graph 从图中该文件的节点出发，沿着调用边和导入边追踪所有调用方、依赖方和相关测试。这些文件构成了这次变更的"爆炸半径"（blast radius）——即可能受到影响、需要审查的文件集合。

AI 代理拿到的是这个精简集合，而不是整个仓库。以 Flask 仓库为例：全量代码 143,594 token，图查询返回 2,196 token，缩减 71 倍。

### 增量更新

首次构建约 10 秒（500 个文件的项目）。之后的更新是增量的：只重新解析 SHA-256 哈希发生变化的文件。在一个约 3,000 个文件的项目（Django）上，编辑两个文件的增量索引耗时约 2.5 秒，其中 1.4 秒是进程启动开销。

增量更新可以通过文件保存钩子或 watch 模式自动触发，无需手动操作。

## 安装与使用

### 安装

```bash
pip install code-review-graph          # 或 pipx install code-review-graph
code-review-graph install              # 自动检测并配置所有支持的 AI 工具
code-review-graph build                # 解析代码库构建图
```

`install` 命令自动检测你安装了哪些 AI 编程工具（Claude Code、Codex、Cursor、Windsurf、Zed、Continue、OpenCode、Gemini CLI、GitHub Copilot 等 15+ 种），为每个工具写入正确的 MCP 配置。

### 日常使用

安装并构建图后，在 AI 代理中直接提问：

```
Build the code review graph for this project
```

代理会通过 MCP 调用图查询工具，获取精准的审查上下文。

### GitHub Action

同样的分析可以跑在 CI 中。配置一个 composite GitHub Action，每个 PR 自动生成带风险评分的粘性评论：

```yaml
on:
  pull_request:

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: tirth8205/code-review-graph@v2.3.6
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

图在 CI runner 上本地构建和查询，源代码不发送到任何外部服务。可选的 `fail-on-risk` 输入将审查变为合并门控。

## 语言覆盖

支持的语言覆盖面很宽：Python、JavaScript/TypeScript/TSX、Go、Rust、Java、C/C++、C#、Ruby、Kotlin、Swift、PHP、Scala、Solidity、Dart、R、Lua、Shell、Elixir、Zig、PowerShell、Julia、Vue/Svelte SFC、Jupyter Notebook 等 30+ 种。

如果用的语言不在内置列表中，可以在项目根目录放一个 `.code-review-graph/languages.toml`，把文件扩展名映射到 Tree-sitter 语法和节点类型——不需要改代码或 fork。

PHP 项目额外获得 Composer PSR-4 导入解析、Blade 模板引用、以及 Laravel Route/Eloquent 的语义边。

## 基准测试

### Token 效率

在 6 个真实开源仓库上的测量（2026-08-02 重新捕获，代码固定在指定 SHA）：

| 仓库 | 全量 token | 图查询 token | 缩减倍数 |
|---|---:|---:|---:|
| fastapi | 948,793 | 2,653 | 375.6x |
| flask | 143,594 | 2,196 | 71.0x |
| code-review-graph | 208,821 | 3,190 | 68.1x |
| gin | 166,868 | 2,766 | 61.9x |
| httpx | 142,356 | 2,661 | 60.6x |
| express | 136,052 | 3,936 | 36.0x |

中位缩减约 65 倍。376 倍（fastapi）是最好情况而非典型值——仓库越大，全量基线越大，图的相对节省越多。

需要注意：全量基线是一个理论上限，真实代理不会真的读全部代码。但即使与"代理 grep 后读 top-3 文件"的基线相比，图查询仍有显著优势。

### 影响精度

blast-radius 的召回率（recall）在图推导模式下是 1.0——但这个数字是循环的：评分标准本身就用图的边来定义"地面真值"。更诚实的指标是 F1 分数：13 个评估提交的平均 F1 为 0.693，平均精确率 0.546。这意味着它倾向于过度预测（flag 太多而非太少），这是一个有意的权衡——漏掉一个被破坏的依赖比多看几个文件代价更高。

### 已知局限

- **小改动场景**：对于只改一个文件的 trivial 编辑，图的上下文元数据可能比直接读文件还多。
- **搜索质量**：MRR 0.35，关键词搜索在 top-4 内找到正确结果，但排序需要改进。
- **流程检测**：33% 的召回率，Python 和 PHP/Laravel 最好，JavaScript 和 Go 需要改进。
- **co-change 模式**：用 git 历史中的同提交共变文件做独立评分的机制还在修复中，暂不可用。

## 功能全景

除了核心的 blast-radius 分析和 MCP 集成，code-review-graph 还提供：

- **社区检测**：用 Leiden 算法聚类相关代码
- **Hub 和桥节点检测**：通过介数中心性找到架构瓶颈
- **意外耦合评分**：发现跨社区、跨语言的异常依赖
- **知识缺口分析**：识别孤立节点、未测试热点、薄弱社区
- **图快照对比**：比较不同时间点的图变化
- **多仓库注册表**：注册多个仓库，跨仓库搜索
- **可视化导出**：GraphML、Neo4j Cypher、Obsidian vault、SVG
- **语义搜索**：可选的向量嵌入（sentence-transformers、Gemini、MiniMax 或 OpenAI 兼容端点）

## 项目数据

| 指标 | 数值 |
|---|---|
| Stars | ~29,600 |
| Forks | ~2,710 |
| 主语言 | Python |
| 许可证 | MIT |
| 最新版本 | v2.3.7（2026-07-18） |
| Python 版本 | 3.10+ |
| 存储 | 本地 SQLite（`.code-review-graph/`） |

## 判断

code-review-graph 用一个经典的思路（预计算 + 精确查询）解决了 AI 代码审查的 token 效率问题。Tree-sitter + SQLite 是务实的技术选型——不依赖外部数据库或云服务，图数据完全本地化。MCP 协议的接入方式让它能适配几乎所有主流 AI 编程工具，而不是绑定到某一个。

它的局限同样清晰：F1 0.693 意味着有不少过度预测，对小改动场景不一定划算；流程检测和 co-change 评分还处于早期阶段。但作为一个"让 AI 代理少读废话、多读重点"的基础设施，它的方向和实现都是扎实的。对于在中大型代码库上使用 AI 代码审查的团队，token 节省带来的成本下降和审查质量提升是实打实的。
