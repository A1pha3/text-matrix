---
title: "CodeGraph：为 Claude Code 打造的本地代码知识图谱"
date: 2026-05-16T19:45:00+08:00
slug: "codegraph-claude-code-knowledge-graph"
description: "CodeGraph 是一个为 Claude Code 设计的本地代码知识图谱工具，通过 tree-sitter 解析构建符号关系图并存储在 SQLite 中。在基准测试中，集成 CodeGraph 后 Claude Code 的 Explore 智能体平均减少 92% 的工具调用次数，速度提升 71%。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "代码知识图谱", "MCP", "tree-sitter", "TypeScript"]
---

## 项目概览

**CodeGraph** 由 [colbymchenry](https://github.com/colbymchenry) 开发，是一个面向 Claude Code 的本地代码知识图谱工具。截至 2026 年 5 月，项目在 GitHub 上拥有约 **2,089** 颗 Stars，仓库语言为 TypeScript，采用 MIT 许可证。

它的核心价值主张：**用预索引的知识图谱替代 Claude Code 的 Explore 智能体对代码库的扫描式探索，大幅减少工具调用次数和 token 消耗。**

---

## 核心问题

当 Claude Code 面对「解释这个代码库中的 X 系统是如何工作的」这类探索性任务时，它会启动 Explore 智能体，通过 `grep`、`find`、`Read` 等工具反复扫描文件来理解代码结构。这个过程消耗大量 token 和时间，因为每次工具调用都涉及文件读取和上下文切换。

**CodeGraph 的解法：** 在开发者初始化项目时，提前用 tree-sitter 解析整个代码库，构建符号关系图（函数→被谁调用、类→继承关系、模块→导入依赖），存入本地 SQLite 数据库。Claude Code 运行时通过 MCP（Model Context Protocol）协议查询这个图谱，一次工具调用就能获得完整上下文。

---

## 工作原理

### 三层架构

1. **提取层（Extraction）**：使用 tree-sitter 将源码解析为 AST，通过语言特定查询提取节点（函数、类、方法）和边（调用、导入、继承）
2. **存储层（Storage）**：所有数据存入本地 SQLite 数据库（`.codegraph/codegraph.db`），支持 FTS5 全文搜索
3. **服务层（Resolution）**：解析完成后解析引用——函数调用→定义、导入→源文件、类继承关系；同时通过框架识别补充路由→处理器等额外关联

### 增量同步

MCP 服务器使用操作系统原生文件事件（FSEvents/inotify/ReadDirectoryChangesW）监听项目变化，2 秒安静窗口后触发增量同步，图谱始终保持最新，无需任何配置。

### MCP 工具接口

当作为 MCP 服务器运行时，CodeGraph 向 Claude Code 暴露以下工具：

| 工具 | 用途 |
|------|------|
| `codegraph_search` | 按名称搜索符号 |
| `codegraph_context` | 为任务构建相关代码上下文 |
| `codegraph_callers` | 查找某函数的调用方 |
| `codegraph_callees` | 查找某函数调用的其他函数 |
| `codegraph_impact` | 分析更改某符号的影响范围 |
| `codegraph_node` | 获取单个符号详情（含源码） |
| `codegraph_files` | 获取索引的文件结构（快于文件系统扫描） |
| `codegraph_status` | 检查索引健康状态 |

---

## 基准测试结果

作者在 6 个真实代码库上进行了对比测试（使用 Claude Opus 4.6 + Claude Code v2.1.91）：

| 代码库 | 语言 | CodeGraph | 不用 CodeGraph | 提升幅度 |
|--------|------|-----------|----------------|----------|
| VS Code | TypeScript | 3 调用，17s | 52 调用，1m 37s | **94% 减少，82% 加速** |
| Excalidraw | TypeScript | 3 调用，29s | 47 调用，1m 45s | **94% 减少，72% 加速** |
| Alamofire | Swift | 3 调用，22s | 32 调用，1m 39s | **91% 减少，78% 加速** |
| Swift Compiler | Swift/C++ | 6 调用，35s | 37 调用，2m 8s | **84% 减少，73% 加速** |

关键发现：

- **零文件读取**：使用 CodeGraph 时，智能体从未回落到文件读取，信任 `codegraph_explore` 的结果
- **跨语言查询有效**：Python+Rust 混合代码库中，图谱遍历找到了跨语言边界的关系
- **大型代码库**：Swift Compiler（25,874 文件，272,898 节点）在 4 分钟内完成索引，复杂跨切面问题用 6 次 explore 调用 + 零文件读取在 35 秒内答完

---

## 支持的语言与框架

### 支持的语言（19+）

TypeScript、JavaScript、Python、Go、Rust、Java、C#、PHP、Ruby、C、C++、Swift、Kotlin、Dart、Svelte（支持 Svelte 5 runes）、Vue（支持 Nuxt 路由）、Scala、Dart、Pascal/Delphi、Liquid

### 框架感知路由

CodeGraph 识别主流 Web 框架的路由文件，将 URL 模式与处理器关联：

Django (`path()`、`re_path()`)、Flask（`@app.route`）、FastAPI（`@app.get` 等）、Express（`app.get` 等）、Laravel（`Route::get()` 等）、Rails（`get '/x', to:` 语法）、Spring（`@GetMapping` 等）、Gin/chi/gorilla/mux、Axum/actix/Rocket、ASP.NET（`[HttpGet]` 属性）、Vapor、React Router / SvelteKit

---

## 安装与使用

### 快速安装

```bash
npx @colbymchenry/codegraph
```

交互式安装器会自动：安装 `codegraph` 全局包、配置 MCP 服务器到 `~/.claude.json`、设置 CodeGraph 工具的自动允许权限、在 `~/.claude/CLAUDE.md` 中添加全局指令。

### 初始化项目

```bash
cd your-project
codegraph init -i
```

之后 Claude Code 遇到带有 `.codegraph/` 目录的项目时，会自动使用 CodeGraph 工具。

### 手动配置（非交互安装）

```bash
npm install -g @colbymchenry/codegraph
```

然后在 `~/.claude.json` 中添加 MCP 服务器配置：

```json
{
  "mcpServers": {
    "codegraph": {
      "type": "stdio",
      "command": "codegraph",
      "args": ["serve", "--mcp"]
    }
  }
}
```

---

## 重要设计理念：子代理隔离

README 中特别强调了一条使用规范：

> **永远不要在主会话中直接调用 `codegraph_explore` 或 `codegraph_context`**——它们返回大量源码，会迅速填满主会话上下文。探索类问题应该**spawn 一个 Explore 子智能体**来处理。

主会话只应该直接使用轻量级工具：`codegraph_search`、`codegraph_callers`、`codegraph_callees`、`codegraph_impact`、`codegraph_node`。这样保持了主会话的精简，同时让 CodeGraph 的图谱能力通过子智能体发挥出来。

---

## 适用场景

- 中大型代码库的代码理解任务（Claude Code 探索性提问）
- 跨文件/跨模块的影响分析（改一个函数前想知道影响范围）
- 调用链追溯（某方法被哪些地方调用，调用深度如何）
- 路由→处理器的关联查询（Web 框架场景）

**不适合场景：**

- 尚未初始化 CodeGraph 的项目（需要先 `codegraph init`）
- 需要实时修改代码并立即生效的场景（图谱有 2 秒同步延迟）

---

## 总结

CodeGraph 解决了一个很实在的问题：Claude Code 的 Explore 智能体每次探索都需要重新扫描文件，效率低下。通过在项目初始化时构建好代码知识图谱，后续探索直接查询图谱而不是扫描文件系统，工具调用次数和 token 消耗大幅下降。

它完全本地化、无需 API key、支持 19+ 语言和 13 种 Web 框架路由感知，设计理念也很合理——子代理隔离避免污染主会话上下文。对于使用 Claude Code 进行代码理解和修改的开发者来说，CodeGraph 是一个值得一试的效率工具。

**仓库链接：** https://github.com/colbymchenry/codegraph