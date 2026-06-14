---
title: "oh-my-pi：集成IDE的终端AI Coding Agent"
date: "2026-05-20T20:00:00+08:00"
slug: "oh-my-pi-integrated-ide-coding-agent"
description: "oh-my-pi是一个用TypeScript/Rust编写的终端AI Coding Agent，将IDE完整集成到Agent中。支持hashline编辑、LSP、DAP调试、40+模型、内置浏览器和子Agent，源自Mario Zechner的开源项目Pi。开源4个月斩获5187 Stars。本文详解其核心特性、架构设计和快速上手。"
draft: false
categories: ["技术笔记"]
tags: ["AI Coding", "Terminal", "LSP", "Debugger", "TypeScript", "Rust"]
---

## 项目概览

[oh-my-pi](https://github.com/can1357/oh-my-pi)（简称 omp）是终端 AI Coding Agent 领域的强力竞争者，将 IDE 完整能力直接接入 Agent。与其他 Agent 不同，它不是简单包装 bash，而是**内嵌了真实的编程工具链**：LSP 代码补全、真实调试器（DAP）、多语言执行内核。

**核心数据：**
- GitHub Stars：5,187（今日增长显著，开源仅 4 个月）
- 语言：TypeScript + Rust（~27k 行 Rust 核心）
- 运行时：Bun（推荐）、Node.js
- 平台：macOS · Linux · Windows
- 开源协议：MIT
- 官网：https://omp.sh

**为什么值得写：**
- Hashline 编辑让 AI 修改第一次就成功，减少 token 消耗（Grok 4 Fast 节省 61%输出 token）
- 内置真实调试器（DAP），支持 lldb/dlv/debugpy
- 子 Agent 系统支持任务并行和类型化结果返回
- 继承 Cursor MDC、Cline rules、Copilot AGENTS.md 等 8 种格式，零迁移成本

---

## 核心特性详解

### 01 · Hashline 编辑：第一次就做对

传统的 diff 编辑依赖行号/行内容作为锚点，模型容易找错位置导致编辑失败。omp 使用**内容哈希锚点**定位编辑位置，模型只描述"改哪里"而不重复"写什么"，token 消耗大幅降低。

```bash
# 模型输出
edit "formatBytes" in src/utils.ts
# omp内部转换为hashline patch，精确匹配内容位置
```

**效果：** Grok 4 Fast 相同工作节省 61%输出 token；编辑一次通过率大幅提升。

### 02 · LSP 完整集成：IDE 知道什么，Agent 就知道什么

通过 `workspace/willRenameFiles`，重命名操作自动更新所有引用（重导出 barrel 文件、别名导入）。Agent 调用的是 IDE 的 LSP 服务，不是自己的模拟。

```bash
# LSP rename示例
LSP rename formatBytes → formatFileSize
# 自动更新 format.ts、report.ts、cli.ts 中的所有引用
```

### 03 · 真实调试器支持

omp 通过 DAP（Debug Adapter Protocol）驱动真实的调试器：
- **lldb**：C/C++/Rust 原生二进制调试
- **dlv**：Go 服务 goroutine 栈追踪
- **debugpy**：暂停 Python 进程、inspect 变量、evaluate 表达式

大多数 Agent 还在用 print 调试，omp 已经可以直接 attach 到进程。

### 04 · 时间旅行式流规则（TTSR）

规则文件平时静默，模型偏离预期时触发：正则匹配中止输出、注入规则到 system reminder、从同一点重试。注入在 context 压缩后依然存活，修复持久有效。

```
# 模型即将写 Box::leak
→ 规则触发："Don't reach for Box::leak in production"
→ 模型改用 Arc<str>，询问用户确认
```

### 05 · 子 Agent 并行任务

`task` 将工作分配给隔离的 worker，每个 worker 拥有独立工具表面，最终 yield 是 schema 校验的对象，父 Agent 直接读取字段，无需解析 prose。

```
task {
  agents: ["ComponentsExports", "RoutesExports"],
  constraints: "IRC DM between peers"
}
→ 子Agent并发执行
→ 结果: { exports: [...], coordination_note: "..." }
```

### 06 · 浏览器与 Electron 应用控制

Stealth 模式默认开启，页面看到正常用户而非 headless bot。同一个 API 驱动任意 Electron 应用（Slack、Notion、Figma）。

### 07 · 跨格式继承

omp 直接读取 8 种已存在的 Agent 规则格式，无需转换：
- Cursor MDC
- Cline `.clinerules`
- Codex `AGENTS.md`
- Copilot `applyTo`
- 等

### 08 · 原子提交与冲突解决

`omp commit` 通过 `git-overview`、`git-file-diff`、`git-hunk` 读取工作树，将无关变更拆分为原子提交，循环依赖在写入前拒绝。合并冲突每个对应一个 URL，写 `@theirs` / `@ours` / `@base` 到 `conflict://N` 即可解决。

---

## 快速开始

### 安装（macOS / Linux）

```bash
curl -fsSL https://omp.sh/install | sh
```

### Bun（推荐）

```bash
bun install -g @oh-my-pi/pi-coding-agent
```

### Windows

```powershell
irm https://omp.sh/install.ps1 | iex
```

### mise 版本管理

```bash
mise use -g github:can1357/oh-my-pi
```

---

## 内置工具一览（32 个）

**文件与搜索：**
| 工具 | 说明 |
|------|------|
| `read` | 文件、目录、归档、SQLite、PDF、笔记本、URL、内部 scheme |
| `write` | 创建/覆盖文件、归档条目、SQLite 行 |
| `edit` | hashline 补丁，含内容哈希锚点和陈旧锚点恢复 |
| `ast_edit` | 结构重写，预览后应用（via ast-grep） |
| `ast_grep` | 50+ tree-sitter 语法的结构代码查询 |
| `search` | 文件/glob/内部 URL 的正则搜索 |
| `find` | glob 路径查找 |

**运行时：**
| 工具 | 说明 |
|------|------|
| `bash` | workspace shell，支持可选 PTY 和后台任务调度 |
| `eval` | 持久 Python 和 JavaScript 单元格，共享 prelude 和工具重入 |

**内部 scheme（透明解析）：**
| scheme | 说明 |
|--------|------|
| `pr://` | 读取 PR 信息 |
| `issue://` | 读取 Issue |
| `agent://` | 子 Agent 结果 |
| `skill://` | 技能文档 |
| `rule://` | 规则文件 |
| `conflict://N` | 合并冲突解决 |

---

## 模型性能对比

omp 的编辑格式针对不同模型做了优化调整：

| 模型 | 效果 |
|------|------|
| Grok Code Fast 1 | 编辑通过率从 6.7%→68.3%（格式优化） |
| Gemini 3 Flash | 超过 str_replace 格式，超越 Google 自己的最佳尝试 |
| Grok 4 Fast | 输出 token 减少 61%（hashline 去除了 retry 循环） |
| MiniMax | 通过率提升 2.1 倍（同权重、同 prompt） |

---

## ACP：编辑器驱动的 Agent

在 Zed 编辑器中运行 omp，获得与终端相同的 Agent 体验：读取你实际查看的 buffer，通过编辑器 save 路径写入，在编辑器 terminal 中 spawn shell。危险工具暂停等待确认，一次回答即可。无桥接层、无插件、无需要同步的第二大脑。

---

## 适用场景

- 需要高精度编辑（hashline 确保第一次成功）
- 跨平台开发（macOS/Linux/Windows 同一二进制）
- 需要真实调试能力（lldb/dlv/debugpy）
- 已有 Cursor/Cline/Codex 规则，想平滑迁移
- 子 Agent 并行处理复杂任务

---

## 总结

oh-my-pi 将终端 AI Coding Agent 提升到新高度：不是简单调用 bash，而是**将 IDE 完整集成**，让 Agent 真正理解代码结构。Rust 核心（约 27k 行）保证了性能，TypeScript 生态保证了可扩展性。

**关键价值：**
- Hashline 编辑让 AI 第一次就做对，节省 token 提高效率
- LSP + DAP 完整集成，真实调试能力而非 print 大法
- 子 Agent 并行 + 类型化结果，复杂任务分解简单
- 8 种格式继承，零迁移成本

**参考链接：**
- GitHub：https://github.com/can1357/oh-my-pi
- 官网：https://omp.sh
- 安装脚本：https://omp.sh/install