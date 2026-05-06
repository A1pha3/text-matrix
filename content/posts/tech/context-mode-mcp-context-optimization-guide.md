---
title: "Context Mode：解决AI编程Agent上下文危机的MCP服务器"
date: "2026-04-12T18:02:00+08:00"
slug: context-mode-mcp-context-optimization-guide
description: "7.1k Stars的Context Mode，通过沙箱执行将315KB上下文压缩至5.4KB，节省98%。支持12大平台：Claude Code/Gemini CLI/Cursor/OpenCode等。FTS5+BM25知识库实现会话连续性。"
draft: false
categories: ["技术笔记"]
tags: ["MCP", "上下文优化", "Claude Code", "Cursor", "FTS5", "知识库"]
---

# Context Mode：解决AI编程Agent上下文危机的MCP服务器

## 📋 学习目标

- 理解Context Mode解决的核心问题——AI编程工具的上下文窗口危机
- 掌握6个核心工具的工作原理和使用场景
- 理解FTS5+BM25知识库如何实现会话连续性
- 学会在不同平台（Claude Code/Gemini/Cursor等）上安装和配置Context Mode
- 掌握Think in Code范式——让AI写代码计算，而非读取数据

---

## 📖 项目概述

### 什么是Context Mode

**Context Mode**是一个MCP服务器，专门解决AI编程工具的**上下文窗口危机**。

核心洞察：
> 每一次MCP工具调用都会向上下文窗口倾倒原始数据。一个Playwright快照消耗56KB。30分钟后，40%的上下文空间消失了。当Agent压缩对话时，它会忘记正在编辑的文件、进行中的任务、上一次的要求。

### 三大核心能力

| 能力 | 说明 | 效果 |
|------|------|------|
| **Context Saving** | 沙箱工具保持原始数据不入上下文 | 315KB → 5.4KB，**节省98%** |
| **Session Continuity** | SQLite FTS5知识库追踪文件编辑、任务、错误 | 对话压缩后完美恢复 |
| **Think in Code** | LLM生成计算脚本，而非读取数据 | 100倍上下文节省 |

### 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | **7.1k** |
| Forks | 483 |
| Watch | 48 |
| 贡献者 | 34人 |
| 最新版本 | v1.0.75 (2026-04-06) |
| 许可证 | Elastic License 2.0 (ELv2) |
| 语言 | TypeScript 49.4%, JavaScript 46.1% |

---

## 🛠️ 6个核心工具

### 工具一览

| 工具 | 功能 | 上下文节省 |
|------|------|----------|
| `ctx_batch_execute` | 一次调用执行多条命令+搜索 | 986KB → 62KB |
| `ctx_execute` | 在11种语言中运行代码，仅stdout进入上下文 | 56KB → 299B |
| `ctx_execute_file` | 在沙箱中处理文件，原始内容永不离开 | 45KB → 155B |
| `ctx_index` | 将markdown分块存入FTS5，BM25排序 | 60KB → 40B |
| `ctx_search` | 多查询一次调用搜索索引内容 | 按需检索 |
| `ctx_fetch_and_index` | 获取URL，转换HTML为markdown，分块索引 | 60KB → 40B |

### 实用命令

| 命令 | 功能 |
|------|------|
| `ctx_stats` | 显示上下文节省、调用次数、会话统计 |
| `ctx_doctor` | 诊断安装：运行时、钩子、FTS5、版本 |
| `ctx_upgrade` | 从GitHub升级，重建，重配钩子 |
| `ctx_purge` | 永久删除知识库中的所有索引内容 |

---

## 🏗️ 沙箱执行原理

### 工作流程

```
用户请求
    ↓
ctx_execute 调用
    ↓
隔离子进程启动（独立进程边界）
    ↓
脚本在沙箱中运行
    ↓
仅 stdout 进入上下文
    ↓
原始数据（日志、API响应、快照）永不离开沙箱
```

### 支持的运行时

**11种语言运行时**：JavaScript, TypeScript, Python, Shell, Ruby, Go, Rust, PHP, Perl, R, Elixir

**Bun自动检测**：JS/TS执行速度提升3-5倍

### 智能过滤

当输出超过5KB且提供了`intent`时：
1. 将完整输出索引到知识库
2. 搜索与intent匹配的部分
3. 仅返回相关匹配+可搜索词汇

---

## 📚 知识库工作原理

### SQLite FTS5架构

```
ctx_index 工具
    ↓
按标题分块markdown（代码块保持完整）
    ↓
存储到 SQLite FTS5 表
    ↓
BM25排序算法评分
```

### 检索策略： Reciprocal Rank Fusion (RRF)

两种并行策略融合：

| 策略 | 说明 |
|------|------|
| **Porter词干** | FTS5 MATCH + porter分词器。"caching"匹配"cached", "caches", "cach" |
| **Trigram子串** | FTS5 trigram分词器。"useEff"找到"useEffect" |

### 高级特性

| 特性 | 说明 |
|------|------|
| **Proximity Reranking** | 查询词越近的结果排名越高 |
| **Fuzzy Correction** | Levenshtein距离纠错。"kuberntes" → "kubernetes" |
| **Smart Snippets** | 智能提取而非截断 |
| **TTL Cache** | 24小时TTL，14天清理 |

---

## 🔄 会话连续性

### 四大钩子协同

| 钩子 | 功能 | Claude Code | Gemini CLI | VS Code Copilot | Cursor | OpenCode | OpenClaw |
|------|------|------------|-----------|-----------------|--------|-----------|----------|
| **PreToolUse** | 工具执行前强制沙箱路由 | ✅ | ✅ | ✅ | ✅ | Plugin | ✅ |
| **PostToolUse** | 每次工具调用后捕获事件 | ✅ | ✅ | ✅ | Plugin | Plugin | ✅ |
| **PreCompact** | 对话压缩前建立快照 | ✅ | ✅ | ✅ | Plugin | Plugin | - |
| **SessionStart** | 压缩或恢复后恢复状态 | ✅ | ✅ | ✅ | - | - | Plugin |

### 不同平台的会话完整性

| 平台 | 完整性 |
|------|---------|
| Claude Code | **完整** |
| Gemini CLI | 高 |
| VS Code Copilot | 高 |
| OpenCode | 高（缺SessionStart） |
| Cursor | 部分（缺SessionStart） |
| Codex CLI | 等待上游钩子分发 |

---

## 💾 性能基准测试

### 典型场景压缩效果

| 场景 | 原始大小 | 压缩后 | 节省率 |
|------|----------|--------|--------|
| Playwright快照 | 56.2 KB | 299 B | **99%** |
| 20个GitHub Issues | 58.9 KB | 1.1 KB | **98%** |
| 500条访问日志 | 45.1 KB | 155 B | **100%** |
| Context7 React文档 | 5.9 KB | 261 B | **96%** |
| 分析CSV (500行) | 85.5 KB | 222 B | **100%** |
| Git日志 (153次提交) | 11.6 KB | 107 B | **99%** |
| 子Agent研究 | 986 KB | 62 KB | **94%** |

### 全会话效果

> 315KB原始输出 → 5.4KB。会话时间从~30分钟延长到~3小时。

---

## 📦 安装配置

### Claude Code（推荐，自动）

```bash
# 前置要求：Claude Code v1.0.33+
claude --version

# 如果 /plugin 不识别，先更新
brew upgrade claude-code
# 或
npm update -g @anthropic-ai/claude-code

# 安装
/plugin marketplace add mksglu/context-mode
/plugin install context-mode@context-mode

# 重启Claude Code（或运行 /reload-plugins）

# 验证
/context-mode:ctx-doctor
```

### 其他平台

| 平台 | 安装方式 |
|------|----------|
| **Gemini CLI** | 配置文件，钩子内置 |
| **VS Code Copilot** | 钩子+SessionStart |
| **Cursor** | 钩子+停止支持 |
| **OpenCode** | TypeScript插件+钩子 |
| **KiloCode** | TypeScript插件+钩子 |
| **OpenClaw/Pi Agent** | 原生网关插件 |
| **Codex CLI** | MCP+钩子（等待上游分发） |
| **Antigravity** | MCP仅限，无钩子 |
| **Kiro** | 钩子+转向文件 |
| **Zed** | MCP仅限，无钩子 |

---

## 🎯 Think in Code范式

### 核心理念

> **LLM应该编程分析，而不是计算数据。**

与其将50个文件读入上下文来计数函数，不如让Agent写一个脚本来计数并`console.log()`结果。

### 对比示例

❌ **传统方式（浪费上下文）**：
```
读取50个文件 → 数函数 → 返回结果
上下文消耗：50 × 10KB = 500KB
```

✅ **Think in Code（节省98%）**：
```
生成并运行计数脚本 → 仅返回结果
上下文消耗：脚本 + 结果 = 0.3KB
```

---

## 🔒 安全与隐私

### 安全模型

Context Mode在你已有的权限规则基础上执行——并将其扩展到MCP沙箱。

**配置示例**：
```json
{
  "permissions": {
    "deny": [
      "Bash(sudo *)",
      "Bash(rm -rf /*)",
      "Read(.env)",
      "Read(**/.env*)"
    ],
    "allow": [
      "Bash(git:*)",
      "Bash(npm:*)"
    ]
  }
  }
}
```

### 隐私承诺

- **数据不离本地**：无遥测、无云同步、无使用追踪
- **SQLite数据库**：存储在你的home目录
- **会话结束即销毁**：无持久化数据

---

## 📊 路由强制执行

### 钩子 vs 指令文件

| 方式 | 效果 |
|------|------|
| **钩子（Hooks）** | 程序化拦截，可阻止危险命令，~98%节省 |
| **指令文件** | 指导模型，无法阻止任何操作，~60%节省 |

**结论**：在支持钩子的平台上，始终启用钩子。

---

## 🚀 实用示例

### 示例1：深度仓库研究（5次调用，62KB上下文）

```bash
Research https://github.com/modelcontextprotocol/servers — architecture, tech stack, top contributors, open issues, and recent activity. Then run /context-mode:ctx-stats.
```

### 示例2：Git历史分析（1次调用，5.6KB上下文）

```bash
Clone https://github.com/facebook/react and analyze the last 500 commits: top contributors, commit frequency by month, and most changed files. Then run /context-mode:ctx-stats.
```

### 示例3：会话连续性（压缩恢复）

```bash
# 开始多步骤任务
"Create a REST API with Express — add routes, tests, and error handling."

# 20+次工具调用后
ctx stats  # 查看会话事件数

# 当上下文压缩时
# 模型从上次提示继续，任务、文件、决策完整保留
```

---

## 🌟 生态兼容

| 平台 | MCP Server | PreToolUse | PostToolUse | SessionStart | PreCompact |
|------|------------|------------|-------------|--------------|------------|
| Claude Code | ✅ | ✅ | ✅ | ✅ | ✅ |
| Gemini CLI | ✅ | ✅ | ✅ | ✅ | ✅ |
| VS Code Copilot | ✅ | ✅ | ✅ | ✅ | ✅ |
| Cursor | ✅ | ✅ | ✅ | ❌ | Plugin |
| OpenCode | ✅ | Plugin | Plugin | ❌ | Plugin |
| OpenClaw | ✅ | ✅ | ✅ | Plugin | - |
| Codex CLI | ✅ | ✅ | ✅ | ✅ | - |
| Antigravity | ✅ | ❌ | ❌ | ❌ | ❌ |
| Kiro | ✅ | ✅ | ✅ | ❌ | ❌ |
| Zed | ✅ | ❌ | ❌ | ❌ | ❌ |
| Pi Coding Agent | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## ✅ 总结

Context Mode是**AI编程工具的上下文危机解决方案**：

1. **98%上下文节省**：沙箱执行让原始数据永不进入上下文
2. **会话连续性**：对话压缩后完美恢复，无需重复
3. **Think in Code**：让AI写代码计算，而非浪费上下文读取
4. **12平台支持**：覆盖主流AI编程工具
5. **安全隐私**：本地处理，无遥测无追踪
6. **开源可用**：ELv2许可证，源码可用

🦞
