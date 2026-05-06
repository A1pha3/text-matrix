---
title: "Context Mode：解决 AI 编程 Agent 的另一半上下文问题"
date: "2026-05-05T20:18:00+08:00"
slug: "context-mode-mcp-server-llm-context-optimization-guide"
description: "Context Mode 是一个 MCP Server，解决 AI 编程 Agent 的上下文窗口污染问题：工具输出占满 context、对话压缩后记忆丢失、输出冗长浪费 token。通过沙箱隔离+SQLite+FTS5+输出压缩四合一，实现 98% 工具数据 reduction 和 65-75% 输出 token 压缩。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Context Mode", "MCP", "上下文优化", "AI编程", "LLM"]
---

# Context Mode：解决 AI 编程 Agent 的另一半上下文问题

Context Mode 解决的是 AI 编程 Agent 场景里被长期忽视的另一半问题：当你在用 Claude Code、Cursor 或 Gemini CLI 时，每次 MCP 工具调用都在往 context window 里塞原始数据——一个 Playwright 快照 56 KB，20 个 GitHub issues 59 KB，一个 access log 45 KB。30 分钟后，40% 的 context 被这些数据吃掉，而当 agent 压缩对话腾空间时，它忘了正在改哪个文件、有哪些任务在进行、你最后要求了什么。

项目 GitHub：[mksglu/context-mode](https://github.com/mksglu/context-mode)，Stars 12,712，MIT License，2026-05-05 刚推送更新，HN 前帖 570+ points。

## 1. 问题分析：上下文窗口的四重浪费

Context Mode 的 README 将问题拆成了四个维度：

| 问题 | 现象 | 影响 |
|------|------|------|
| **工具数据污染** | 每次 MCP 调用把原始数据塞进 context | 56 KB Playwright 快照，20 GitHub issues 59 KB |
| **会话连续性丢失** | 对话压缩（compact）后丢失工作状态 | 不知道改到哪了、任务还剩什么、上次要求了什么 |
| **计算浪费** | 把 LLM 当数据处理器而不是代码生成器 | 读 50 个文件来数函数，开销巨大 |
| **输出膨胀** | 模型输出大量填充词、客套话、冗长解释 | 从两侧浪费 context |

## 2. 解决方案：四合一架构

### 2.1 Context Saving — 沙箱工具

原始方案：每次工具调用返回的数据直接进 context。Context Mode 的做法是：工具数据进沙箱，context 里只留压缩后的摘要。

效果：315 KB 工具数据变成 5.4 KB， reduction 98%。

具体实现是通过 6 个沙箱工具：

- `ctx_batch_execute`：批量执行脚本
- `ctx_execute`：执行单条分析脚本
- `ctx_execute_file`：执行文件中的脚本
- `ctx_index`：将内容编入索引
- `ctx_search`：搜索已索引内容
- `ctx_fetch_and_index`：抓取并索引

### 2.2 Session Continuity — SQLite + FTS5

当对话压缩时，Context Mode 不把数据倒回 context，而是将事件（文件编辑、git 操作、任务、错误、用户决策）记录到 SQLite。当需要恢复时，通过 FTS5（BM25 搜索）只取相关的内容。

机制：

- 使用 `--continue` 参数：之前 session 的数据从 SQLite 恢复
- 不使用 `--continue`：session 结束时数据立即清除，不残留

### 2.3 Think in Code — 脚本优先范式

Context Mode 强制转换了一个范式：**不要读数据，让代码去处理数据**。

传统模式（47 个 Read()）：读取 50 个文件进 context 来数函数 → 700 KB context 消耗。

Context Mode 模式：

```js
ctx_execute("javascript", `
  const files = fs.readdirSync('src').filter(f => f.endsWith('.ts'));
  files.forEach(f => console.log(f + ': ' + fs.readFileSync('src/'+f,'utf8').split('\n').length + ' lines'));
`);
```

→ 只消耗 3.6 KB context，一次脚本替换十次工具调用，节省 100 倍 context。

这个范式在全部 14 个支持的平台上强制执行，包括 Claude Code（插件形式）、Gemini CLI、Cursor、Cline 等。

### 2.4 Output Compression — 输出压缩

模型输出变得像"穴居人说话"：技术精确、惜字如金、无填充词、无客套话、无冗余解释。

规则示例：

- 删除冠词、填充词（just/really/basically）
- 删除客套话和犹豫表达
- 删除过度保守措辞
- 短语优先：**[thing] [action] [reason] [next step]**
- 自动展开保留给：安全警告、不可逆操作、用户可能困惑的场景

效果：约 65-75% 输出 token reduction，同时保持技术准确性。

例外自动展开：安全警告、不可逆操作、用户困惑场景——这些情况模型会正常展开说明。

## 3. 支持平台（14 个，含自动路由强制执行）

以下平台支持 hook 自动路由强制执行（plugin 方式或配置文件方式）：

- **Claude Code**：完整插件市场集成，自动 Hook 注册（PreToolUse、PostToolUse、PreCompact、SessionStart）+ 11 个 MCP 工具 + 5 个 slash 命令（ctx-stats、ctx-doctor、ctx-upgrade、ctx-purge、ctx-insight）
- **Gemini CLI**：配置文件方式，Node.js 18+
- **Cursor**：Cursor 有专门的 MCP 配置方式
- **Cline**：自动 hook 注册
- **Roo**：自动 hook 注册
- **Zed**：需要手动复制路由文件
- **VSCode（Cline）**：通过 package.json 配置

## 4. Claude Code 安装详解

Context Mode 的核心用户群是 Claude Code 开发者，安装过程如下：

### 前置条件

- Claude Code v1.0.33+（`claude --version` 确认版本）
- 老版本执行 `brew upgrade claude-code` 或 `npm update -g @anthropic-ai/claude-code` 升级

### 安装命令

```bash
/plugin marketplace add mksglu/context-mode
/plugin install context-mode@context-mode
```

重启 Claude Code（或执行 `/reload-plugins`）。

### 验证

```
/context-mode:ctx-doctor
```

Doctor 命令验证：runtime 环境、hooks 注册、FTS5 数据库、插件注册、版本号。所有检查项应显示 `[x]`。

### 可选状态栏

插件 manifest 无法声明状态栏，需手动编辑 `~/.claude/settings.json`：

```json
{
  "statusLine": {
    "type": "command",
    "command": "context-mode statusline"
  }
}
```

重启后，状态栏显示：`$ saved this session · $ saved across sessions · % efficient`，实时看到节省积累。

## 5. 性能数据

官方数据：

- **工具数据 reduction**：315 KB → 5.4 KB（98%）
- **输出 token reduction**：~65-75%（实测）
- **启动效果**：30 分钟会话后，原来 40% 的 context 被工具数据污染，使用后趋近零

90 天使用数据（从 ctx-insight 获取）：90 个指标、37 种洞察模式、4 个复合评分（生产力、质量、委托度、上下文健康）覆盖 23 个事件类别。

## 6. 与传统 RAG 的区别

| 维度 | Context Mode | 传统 RAG |
|------|-------------|----------|
| 触发时机 | 工具输出时即时拦截，不进入 context | 检索阶段 |
| 数据结构 | SQLite 事件日志 + FTS5 | 向量数据库 |
| 恢复方式 | BM25 检索，只取相关事件 | 全量向量相似度 |
| 输出压缩 | 逐次模型输出压缩 | 无 |
| 适用场景 | 编程 Agent 上下文管理 | 文档问答、知识库 |

## 7. 适用场景

- 长时间运行的复杂项目（数小时乃至数天的会话）
- 需要频繁切换上下文的大型重构任务
- 使用 Claude Code 处理大型代码库的开发者
- 关注 token 成本和 API 用量的团队

## 8. 局限性与注意事项

1. **仅支持特定平台**：不是所有 AI 编程工具都支持，列表在 README 中
2. **Session Start Hook 必须在 Claude Code v1.0.33+**：老版本不支持
3. **`--continue` 行为是双刃剑**：继续时恢复上次的记忆，同时也恢复未解决的问题状态
4. **脚本优先范式需要思维转换**：习惯直接读文件的开发者可能需要适应
5. **输出压缩牺牲可读性**：团队协作场景可能需要调整压缩策略

## 9. 总结

Context Mode 解决了 AI 编程 Agent 中一个被长期忽视但影响巨大的问题：上下文窗口被工具输出污染。通过四合一方案（沙箱隔离+事件日志+脚本优先+输出压缩），它在不影响工作质量的前提下实现了 98% 工具数据 reduction 和 65-75% 输出 token 压缩。

对于长时间重度使用 Claude Code 的开发者来说，Context Mode 是目前最完整的上下文优化方案，值得安装体验。

---

**项目信息**

- GitHub：[mksglu/context-mode](https://github.com/mksglu/context-mode)
- Stars：12,712
- 语言：TypeScript
- License：ELv2（Elastic License v2）
- 推送时间：2026-05-05
- HN 讨论：[news.ycombinator.com/item?id=47193064](https://news.ycombinator.com/item?id=47193064)（570+ points）
- Discord：[discord.gg/DCN9jUgN5v](https://discord.gg/DCN9jUgN5v)