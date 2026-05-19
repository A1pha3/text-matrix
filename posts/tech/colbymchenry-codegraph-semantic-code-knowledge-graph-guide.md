---
title: "CodeGraph：为 Claude Code 打造的语义代码知识图谱"
date: 2026-05-17T03:05:00+08:00
slug: "codegraph-semantic-code-knowledge-graph-claude-code"
description: "CodeGraph 是一个预索引代码知识图谱，专为 Claude Code 设计，通过 SQLite 图数据库将代码符号关系、调用图和结构信息存储在本地，显著减少工具调用次数和探索时间，支持19+编程语言和13种Web框架。"
draft: false
categories: ["技术笔记"]
tags: ["CodeGraph", "Claude Code", "MCP", "代码知识图谱", "SQLite", "Tree-sitter"]
---

# CodeGraph：为 Claude Code 打造的语义代码知识图谱

[CodeGraph](https://github.com/colbymchenry/codegraph) 是一个预索引代码知识图谱（Pre-indexed code knowledge graph），专为 Claude Code 智能体设计。项目通过将代码结构和符号关系预先索引到本地 SQLite 数据库，让 Claude Code 的 Explore Agent 无需反复扫描文件即可获取代码上下文，从而实现「更少 token、更少工具调用、100% 本地运行」的体验。

## 1. 项目概览

CodeGraph 解决的核心问题是大型代码库中 Claude Code 工具调用成本过高。当 Claude Code 需要探索一个陌生代码库时，它会派生出多个 Explore Agent 并行扫描文件，每次 `grep`、`glob`、`Read` 操作都会消耗 token 并产生工具调用延迟。CodeGraph 通过预建知识图谱，将这一成本从平均 40+ 降至 3 次左右。

**核心数据：**
- Stars：未公开（README 未标注，需以实际 GitHub 页面为准）
- 语言：TypeScript / JavaScript（CLI + MCP server），SQLite 存储
- License：MIT
- 官方安装命令：`npx @colbymchenry/codegraph`

## 2. 为什么需要 CodeGraph

### Claude Code 的工具调用瓶颈

在未使用 CodeGraph 的情况下，Claude Code 探索 VS Code 规模的代码库需要 52 次工具调用、耗时 1 分 37 秒。使用 CodeGraph 后，同一任务仅需 3 次调用、17 秒——**减少 94% 工具调用、加快 82% 探索速度**。

这一效果来自官方在 6 个真实代码库上的基准测试（VS Code、Excalidraw、Claude Code 自身、Java、Alamofire、Swift Compiler），平均结果为 **92% 更少工具调用、71% 更快完成**。

### CodeGraph 的解决思路

不是让 Claude Code 少做事，而是让每次工具调用返回更多信息量。传统 Explore Agent 一次 `grep` 只能返回匹配行；CodeGraph 一次工具调用可以返回：

- 符号的所有定义位置
- 该符号调用的所有下游符号（callees）
- 所有调用该符号的上游位置（callers）
- 包含该符号的代码片段
- 该符号的影响半径分析

## 3. 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Claude Code                               │
│                                                                  │
│  "Implement user authentication"                                 │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐      ┌─────────────────┐                   │
│  │  Explore Agent  │ ──── │  Explore Agent  │                   │
│  └────────┬────────┘      └────────┬────────┘                   │
└───────────┼────────────────────────┼─────────────────────────────┘
            │                        │
            ▼                        ▼
┌───────────────────────────────────────────────────────────────────┐
│                     CodeGraph MCP Server                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │   Search    │  │   Callers   │  │   Context   │               │
│  │  "auth"     │  │  "login()"  │  │  for task   │               │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘               │
│         │                │                │                       │
│         └────────────────┼────────────────┘                       │
│                          ▼                                        │
│              ┌───────────────────────┐                            │
│              │   SQLite Graph DB     │                            │
│              │   • symbols           │                            │
│              │   • edges             │                            │
│              │   • FTS5 index        │                            │
│              └───────────────────────┘                            │
└───────────────────────────────────────────────────────────────────┘
```

### 索引流程

** Extraction（提取）** — tree-sitter 将源代码解析为 AST，语言特定查询从中提取节点（函数、类、方法）和边（调用、导入、继承、实现关系）。

**Storage（存储）** — 所有数据写入本地 `.codegraph/codegraph.db` SQLite 数据库，带 FTS5 全文索引。

**Resolution（解析）** — 提取后进行引用解析：函数调用→定义、导入→源文件、类继承关系，以及框架特定模式（如 Django `path()`、Flask `@app.route`）。

**Auto-Sync（自动同步）** — MCP server 通过操作系统原生文件事件（FSEvents/inotify/ReadDirectoryChangesW）监听项目变更，变更经过 2 秒静默窗口去抖、过滤为仅源代码文件后增量同步。零配置，图谱始终保持最新。

## 4. 核心功能与 MCP Tools

CodeGraph 作为 MCP Server 暴露以下工具供 Claude Code 调用：

| 工具 | 用途 |
|------|------|
| `codegraph_search` | 按名称在整个代码库中搜索符号 |
| `codegraph_context` | 为任务构建相关代码上下文 |
| `codegraph_callers` | 查找哪些代码调用了指定函数 |
| `codegraph_callees` | 查找指定函数调用了哪些其他函数 |
| `codegraph_impact` | 分析更改某符号会影响到哪些代码 |
| `codegraph_node` | 获取特定符号的详细信息（含源码） |
| `codegraph_files` | 获取已索引的文件结构（快于文件系统扫描） |
| `codegraph_status` | 检查索引健康状况和统计信息 |

`codegraph_context` 是其中最有价值的工具——它接受一个自然语言任务描述，自动推断需要哪些代码节点和边，构建适合该任务的上下文窗口，返回格式化的 Markdown 代码片段。

## 5. 支持的语言与框架

### 支持的语言（19+）

TypeScript/JavaScript、Python、Go、Rust、Java、C#、PHP、Ruby、C、C++、Swift、Kotlin、Dart、Svelte（含 Svelte 5 Runes 和 SvelteKit 路由）、Vue（含 script-setup 和 Nuxt 路由）、Liquid、Pascal/Delphi。

### 框架感知路由（13 种框架）

CodeGraph 能识别 Web 框架路由文件并将 URL 模式链接到对应处理器：

| 框架 | 识别的模式 |
|------|----------|
| Django | `path()`、`re_path()`、`url()` in `urls.py` |
| Flask | `@app.route`、`blueprint` 路由 |
| FastAPI | `@app.get` 等标准方法 |
| Express | `app.get`、带中间件链的 router |
| Laravel | `Route::get`、`Route::resource`、`Controller@action` |
| Rails | `get '/x', to: 'users#index'` |
| Spring | `@GetMapping`、`@PostMapping`、`@RequestMapping` |
| Gin / chi / gorilla / mux | `r.GET()`、`router.HandleFunc()` |
| Axum / actix / Rocket | `.route()` |
| ASP.NET | `[HttpGet("/x")]` 属性 |
| Vapor | `app.get()` |
| React Router / SvelteKit | Route 组件节点 |

## 6. 安装与快速开始

### 自动安装（推荐）

```bash
npx @colbymchenry/codegraph
```

交互式安装程序会自动完成：

1. 全局安装 `codegraph`（MCP server 需要）
2. 在 `~/.claude.json` 中配置 MCP server
3. 为 CodeGraph tools 设置自动允许权限
4. 添加全局指令到 `~/.claude/CLAUDE.md`
5. 可选：初始化当前项目

### 初始化项目

```bash
cd your-project
codegraph init -i   # 初始化并建立索引
```

之后 Claude Code 检测到 `.codegraph/` 目录存在时，会自动使用 CodeGraph 工具替代 Explore Agent。

### 手动安装

```bash
npm install -g @colbymchenry/codegraph
codegraph init /path/to/project
codegraph serve --mcp
# 将 MCP server URL 配置到 ~/.claude.json
```

### CLI 参考

| 命令 | 用途 |
|------|------|
| `codegraph` | 运行交互式安装程序 |
| `codegraph install` | 显式运行安装程序 |
| `codegraph init [path]` | 在项目中初始化（加 `--index` 同时索引） |
| `codegraph index [path]` | 完整索引（加 `--force` 重新索引） |
| `codegraph sync [path]` | 增量更新 |
| `codegraph status [path]` | 显示统计信息 |
| `codegraph query <search>` | 搜索符号 |
| `codegraph files [path]` | 显示文件结构 |
| `codegraph context <task>` | 为 AI 任务构建上下文 |
| `codegraph affected [files...]` | 追踪受变更影响的测试文件 |
| `codegraph serve --mcp` | 启动 MCP server |

`codegraph affected` 可接收 `git diff --name-only` 输出，实现精准的影响域分析用于 CI：

```bash
#!/usr/bin/env bash
AFFECTED=$(git diff --name-only HEAD | codegraph affected --stdin --quiet)
if [ -n "$AFFECTED" ]; then
  npx vitest run $AFFECTED
fi
```

## 7. 库级别使用

CodeGraph 也可作为 Node.js 库直接使用：

```javascript
import CodeGraph from '@colbymchenry/codegraph';

const cg = await CodeGraph.init('/path/to/project');
// 或：const cg = await CodeGraph.open('/path/to/project');

await cg.indexAll({
  onProgress: (p) => console.log(`${p.phase}: ${p.current}/${p.total}`)
});

const results = cg.searchNodes('UserService');
const callers = cg.getCallers(results[0].node.id);
const context = await cg.buildContext('fix login bug', {
  maxNodes: 20,
  includeCode: true,
  format: 'markdown'
});
const impact = cg.getImpactRadius(results[0].node.id, 2);

cg.watch();   // 监听文件变更并自动同步
cg.unwatch(); // 停止监听
cg.close();
```

## 8. 配置项

`.codegraph/config.json` 控制索引行为：

```json
{
  "version": 1,
  "languages": [],
  "exclude": ["node_modules/**", "dist/**", "build/**", "*.min.js"],
  "frameworks": [],
  "maxFileSize": 1048576,
  "extractDocstrings": true,
  "trackCallSites": true
}
```

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `languages` | 要索引的语言（空则自动检测） | `[]` |
| `exclude` | 忽略的 glob 模式 | `["node_modules/**", ...]` |
| `frameworks` | 框架提示 | `[]` |
| `maxFileSize` | 跳过大于此大小的文件（字节） | 1048576（1MB） |
| `extractDocstrings` | 从代码提取文档字符串 | `true` |
| `trackCallSites` | 追踪调用位置 | `true` |

## 9. 常见问题

### "CodeGraph not initialized"

在项目目录下先运行 `codegraph init`。

### 索引慢 / WASM fallback

如果 `codegraph status` 显示 `Backend: wasm`，说明 `better-sqlite3` 原生模块未安装成功，系统回退到 WASM SQLite（慢 5-10 倍）。

修复方法：

```bash
# macOS
xcode-select --install

# Linux (Debian/Ubuntu)
sudo apt install build-essential python3 make

# 重新构建
npm rebuild better-sqlite3
```

修复后 `codegraph status` 应显示 `Backend: native`。

### MCP server 无法连接

确认项目已初始化并建立索引，验证 MCP 配置中的路径正确，命令行执行 `codegraph serve --mcp` 确认正常。

## 10. 总结

CodeGraph 针对的是 Claude Code 在大型代码库中的工具调用成本问题，通过预索引的代码知识图谱将每次工具调用的信息量提升一到两个数量级。其核心优势在于：

- **零外部依赖**：纯本地 SQLite，无 API key，无网络请求
- **增量自动同步**：FSEvents/inotify 驱动，索引始终保持新鲜
- **框架感知**：不只是符号，还理解 URL 路由到处理器的映射关系
- **19+ 语言覆盖**：从 TypeScript 到 Pascal，主流语言均支持

如果你经常在大型代码库中使用 Claude Code，CodeGraph 是一个值得一试的效率工具——它不改变 Claude Code 的行为，只让每一次工具调用更有效。