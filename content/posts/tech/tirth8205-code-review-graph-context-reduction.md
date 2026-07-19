---
title: "code-review-graph：本地优先的代码智能图，把 Code Review 的 token 砍到 1/93"
date: 2026-07-20T03:02:36+08:00
categories: ["技术笔记"]
tags: ["code-review", "mcp", "graphrag", "tree-sitter", "ai-coding"]
description: "code-review-graph 是本地优先的代码智能图（CRG），用 Tree-sitter 把代码库解析成 nodes + edges 持久化到 SQLite，回答 AI Coding Agent 的'读哪些文件就够'问题。21K stars、自家仓库 token 削减 93x、支持 9+ 种主流 coding agent。"
---

# code-review-graph：本地优先的代码智能图，把 Code Review 的 token 砍到 1/93

## 一句话判断

code-review-graph（CRG）解决的核心问题是 **"AI Coding Agent 在 review 时应该读哪些文件"**——它用 Tree-sitter 把代码库解析成 AST（Abstract Syntax Tree，抽象语法树），再转成 nodes（函数 / 类 / 导入）+ edges（调用 / 继承 / 测试覆盖）的图，持久化到 SQLite。改一个文件时 CRG 用图算出 blast radius（爆炸半径），Agent 只读真正受影响的 ~15 个文件，而不是整个 repo。在自家 27.7 万文件的仓库里，token 从 208K 降到 ~2.5K——**93x 削减**。

## 项目定位

- **仓库**：`tirth8205/code-review-graph`，MIT 协议，Python
- **GitHub Stars**：20.9K，Forks 2.2K（2026-07-18 数据）
- **状态**：开源、本地优先（local-first）
- **支持 Agent**：Codex、Claude Code、CodeBuddy Code、Cursor、Windsurf、Zed、Continue、OpenCode、Antigravity、Gemini CLI、Qwen、Qoder、Kiro、GitHub Copilot、GitHub Copilot CLI（README 列出 15 个）
- **核心依赖**：Tree-sitter（AST 解析）、SQLite（持久化）、FastMCP ≥ 3.2.4（MCP server）

## 系统地图

| 模块 | 责任 |
|------|------|
| Tree-sitter Parser | 把源码解析成 AST（多语言支持） |
| Graph Builder | AST → nodes + edges（call / inherit / import / test coverage） |
| SQLite Store | 持久化图数据，支持 SHA-256 文件 hash 增量更新 |
| Blast Radius Engine | 给定变更文件，查询图算出所有受影响的 callers / dependents / tests |
| MCP Server | 把 blast radius 暴露成 MCP 工具供 agent 调用 |
| Watch Mode + Hooks | 文件保存 / git commit 时增量更新图 |

## 关键机制拆解

### 1. 为什么需要 CRG

AI Coding Agent 在 review / 修改代码时的默认行为是"读所有相关文件"——这在小型项目没问题，在大型 monorepo 里就是**灾难**。一个 27K 文件的 monorepo，单次 review 可能让 agent 读 200K tokens，Claude / GPT 调用成本爆炸且延迟翻倍。

CRG 的解法是**预先建立仓库的"知识图谱"**：

- Tree-sitter 解析所有源码，提取 function / class / import / call 关系
- 落到 SQLite
- 文件改动时通过图查询 blast radius
- Agent 只读 blast radius 内的文件

### 2. Blast Radius 分析

README 给的核心机制：

> When a file changes, the graph traces every caller, dependent, and test that could be affected. This is the "blast radius" of the change. Your AI reads only these files instead of scanning the whole project.

举个例子：改了 `login()` 函数

- 通过图找到所有调用 `login()` 的函数（callers）
- 通过图找到所有 import login 模块的文件（dependents）
- 通过图找到所有覆盖 login 的测试（test coverage）
- 这三类合并就是 blast radius

Agent 只需要读 blast radius 内的 ~15 个文件，而不是整个 repo 的 27K 文件。

### 3. 增量更新 < 2 秒

大型 repo 全量重建图可能需要 10+ 分钟，但日常开发不会频繁全量改。CRG 用 SHA-256 文件 hash 做增量：

- 文件保存或 commit 时触发 watch mode / hook
- diff changed files
- 通过 hash 找到 dependent 文件
- 只重 parse 改动的文件

> A 2,900-file project re-indexes in under 2 seconds.

2 秒的延迟让 watch mode + agent hook 的"边写代码边更新图"模式可行。

### 4. 93x Token 削减（自测数据）

README 引用自家仓库的实测：

> code-review-graph repo: 208,821 source tokens funnel down to ~2,495 token graph responses — **93x fewer tokens per question**

93x 是从 208K token 的"全量读"到 2.5K token 的"图查询响应"的对比。节省的不是 query 本身的 token，而是 agent **避免读不相关文件**的 token。

### 5. 多语言支持

CRG 通过 Tree-sitter 支持 Web（JavaScript / TypeScript / Vue / Svelte）、Backend（Python / Java / Go / Rust）、Systems（C / C++ / Zig）、Mobile（Swift / Kotlin）、Scripting（Ruby / Lua / Bash）、Config（YAML / TOML / JSON），还支持 Jupyter / Databricks notebook。覆盖面足够中型 monorepo 使用。

### 6. 跨平台 agent 接入

CRG 通过 MCP server 暴露能力，安装命令对每个 agent 都做了适配：

```bash
code-review-graph install --platform claude-code
code-review-graph install --platform cursor
code-review-graph install --platform codex
# ... 15 个平台
```

安装后 AI assistant 只需要问 "Build the code review graph for this project"，CRG 会自动建图 + 暴露 MCP tools。

## 关键代码入口

CRG 的扩展点非常清晰：

- **新语言支持**：编辑 `code_review_graph/parser.py`，加 `EXTENSION_TO_LANGUAGE` + `_CLASS_TYPES` / `_FUNCTION_TYPES` / `_IMPORT_TYPES` / `_CALL_TYPES` 映射
- **新平台支持**：CRG 的 install 子命令系统已经覆盖 15 个平台，新增平台按相同模式添加
- **卸载**：`code-review-graph uninstall --dry-run` 预览 + `--yes` 跳过 prompt + `--all-repos` 清理所有仓库注册

CRG 明确说"removes only CRG-owned files and entries; unrelated MCP servers, hooks, skills, and JSONC comments remain untouched"——卸载的边界控制做得干净，对企业用户友好。

## 适用人群

- **大型 monorepo 维护者**：27K+ 文件项目，AI agent 读全量 token 成本爆炸的人
- **AI Coding Agent 重度用户**：每天用 Claude Code / Cursor / Codex 跑 review 的人
- **企业团队**：代码库 > 10K 文件，需要本地优先（数据不出仓库）的人
- **追求 token 节省的人**：93x 削减意味着 review 成本降一个数量级

## 不适合谁

- **小型项目（< 500 文件）**：全量读 200K token 也不贵，CRG 的复杂度不划算
- **单文件开发的人**：没有 blast radius 概念，CRG 优势无法发挥
- **不愿装 MCP server 的人**：CRG 默认通过 MCP 暴露，CLI 模式覆盖功能较少
- **企业用户不愿本地存图数据的人**：CRG 是 local-first，不提供云端托管

## 仓库地址

https://github.com/tirth8205/code-review-graph

## 阅读路径建议

1. `pip install code-review-graph && code-review-graph install`，接入你最常用的 agent
2. 让 agent "Build the code review graph for this project"，观察首次建图耗时
3. 改一个文件，触发 watch mode，看增量更新是否 < 2 秒
4. 让 agent "review this change with minimal blast radius"，对比启用 CRG 前后的 token 消耗