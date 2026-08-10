---
title: "Code-Graph-RAG：用知识图谱给整个 monorepo 建索引，再用自然语言查代码"
date: 2026-08-11T03:22:16+08:00
slug: "code-graph-rag-monorepo-knowledge-graph"
github_repo: "vitali87/code-graph-rag"
source_key: "gh:vitali87/code-graph-rag"
description: "Code-Graph-RAG 用 Tree-sitter 解析多语言代码库，将函数、类、模块及其调用关系导入 Memgraph 知识图谱，再通过自然语言生成 Cypher 查询实现代码检索、编辑和死代码分析。"
draft: true
categories: ["技术笔记"]
tags: ["RAG", "知识图谱", "代码分析", "Tree-sitter", "Memgraph"]
---

## 核心判断

传统代码搜索靠关键词或正则，理解代码靠读文件。Code-Graph-RAG 提供了第三条路：**把代码库的结构信息（谁调用了谁、谁定义了什么、谁依赖了哪个模块）提取成知识图谱，然后让 AI 用自然语言查询这张图**。

它不是在嵌入向量里找相似文本，而是在图数据库里走边——从入口点沿调用边出发，能找到所有可达但从未被调用的死代码；沿 `FLOWS_TO` 数据流边追踪，能看到一个变量从赋值到 I/O 输出的完整路径。

## 系统地图

Code-Graph-RAG 由两个子系统组成：

```
源代码 → Tree-sitter 解析器 → AST 分析 → Memgraph 知识图谱
                                                    |
用户查询 → AI 模型 (Cypher 生成) → Cypher 查询 → 图查询结果 → 响应
```

**解析器侧**：用 Tree-sitter 对每种语言生成 AST，从 AST 中提取函数、类、方法、模块节点，以及它们之间的调用、引用、导入关系边。所有节点和边统一写入 Memgraph，使用同一套语言无关的图 schema。

**RAG 侧**：用户输入自然语言问题，AI 模型将其转写为 Cypher 查询，在 Memgraph 上执行，返回匹配的代码片段和结构关系。

### 图 schema 要点

图中的节点类型包括 `Function`、`Class`、`Method`、`Module`，边类型包括 `CALLS`（调用）、`REFERENCES`（引用）、`IMPORTS`（导入）、`CONTAINS`（包含）、`FLOWS_TO`（数据流）和 `DEFINED_IN`（定义于）。2026 年新增的数据流追踪边 `FLOWS_TO` 覆盖 C#、Java、C、Go 四种语言，沿赋值、函数调用和 I/O 输出追踪值的传播路径。

### 支持语言

完全支持 13 种：Python、TypeScript、TSX、JavaScript、Rust、Go、Java、C、C++、C#、PHP、Lua、Dart。Scala 开发中。Ruby 通过可插拔的 ast-grep 层提供结构支持（模块、函数、类、导入）。

ast-grep 层是一个值得注意的设计：添加一门新语言只需写一个 YAML 模式文件，就能从 AST 匹配中生成对应节点和边，不需要手写解析器。这把"支持新语言"的成本从"写一个 Tree-sitter grammar 适配器"降到了"写一个 YAML 文件"。

## 一个查询如何流过系统

以"找出 `processPayment` 函数调用的所有函数，以及它们的定义位置"为例：

1. **图构建**（预先完成）：`cgr start --repo-path ./my-repo --update-graph` 触发 Tree-sitter 解析整个仓库，在 Memgraph 中创建 `Function:processPayment` 节点和对应的 `CALLS` 边。
2. **用户输入**：在 CLI 中输入"show me all functions called by processPayment and where they are defined"。
3. **Cypher 生成**：AI 模型将自然语言转写为 Cypher 查询——`MATCH (f:Function {name: 'processPayment'})-[:CALLS]->(called:Function) RETURN called.name, called.file, called.line`。
4. **图查询**：Cypher 在 Memgraph 上执行，返回被调用函数名、所在文件、行号。
5. **代码检索**：按返回的文件和行号从源码中提取实际代码片段，呈现给用户。

整个过程的关键区别：传统文本搜索会漏掉间接调用（A 调 B，B 调 C，搜索"A"不会找到 C），而图查询可以递归走边。

## 核心能力

| 能力 | 说明 |
|------|------|
| 自然语言查询 | 用自然语言提问，AI 生成 Cypher，返回结构化结果 |
| 代码编辑 | 通过 Agent 用 AST 级别的补丁修改代码，修改前有 diff 预览 |
| 死代码检测 | 从入口点出发沿调用边遍历，不可达的函数即为死代码 |
| 代码优化 | 按语言最佳实践或自定义编码规范评估代码质量 |
| 结构化搜索替换 | 用 ast-grep 的 AST 模式匹配和重写代码，不依赖文本正则 |
| 实时更新 | 代码变更后增量更新图，不必全量重建 |
| MCP Server | 作为 MCP 服务器运行，Claude Code 等 MCP 客户端可直接查询和编辑 |

## 安装与快速开始

```bash
# 安装（推荐 uv）
uv tool install "code-graph-rag[treesitter-full,semantic]"

# 或用 pipx
pipx install "code-graph-rag[treesitter-full,semantic]"
```

前置依赖：Docker（运行 Memgraph）、cmake、ripgrep。

```bash
# 启动 Memgraph + Qdrant（内置 Docker Compose）
cgr daemon up

# 解析仓库到图中
cgr start --repo-path /path/to/repo --update-graph

# 进入交互查询
cgr start --repo-path /path/to/repo
```

多个仓库可以依次索引到同一张共享图中。`--clean` 参数会清空所有项目（会确认），不是只清当前项目。

## 适用边界

**适合**：

- 接手大型 monorepo，需要快速理解代码结构和依赖关系
- 技术债清理：系统性地找出死代码、循环依赖、孤儿模块
- 多语言混合代码库的跨语言代码检索
- 作为 IDE 插件或 MCP 服务器的代码知识后端

**不适合**：

- 小型项目（几百文件以内），grep 和 IDE 跳转足够快
- 需要 100% 精度的场景（Tree-sitter 解析是语法级的，不做语义分析）
- 实时性要求极高的场景（图构建需要时间，增量更新有延迟）
- 需要分析二进制文件或编译产物中代码的场景

项目 MIT 协议，当前版本 v0.0.589（2026-08-10），3.5K Stars，Python 为主语言，更新频率极高（连续三天三个版本）。需要注意的是 GitHub 账号一度被暂停（README 中有相关注释），stars/forks 徽章暂时不可用。
