---
title: "ai-memory：给 AI 编码 Agent 的跨会话长期记忆"
date: 2026-08-21T03:26:00+08:00
slug: "ai-memory-agent-long-term-memory"
github_repo: "akitaonrails/ai-memory"
source_key: "gh:akitaonrails/ai-memory"
description: "ai-memory 用 Rust 实现一个基于 MCP 的长期记忆服务器，把 AI 编码 Agent 的会话观察编译成 Markdown 知识库，支持 Claude Code、Codex、Cursor 等十余种 CLI 的跨工具交接。本文解析其架构与上手路径。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "MCP", "长期记忆", "Rust"]
---
# ai-memory：给 AI 编码 Agent 的跨会话长期记忆

## 核心判断

ai-memory 解决的是 AI 编码工具一个真实而普遍的痛点：**会话一结束，上下文就丢了**。它用单个 Rust 二进制跑一个 MCP/HTTP 服务器，把各编码 Agent 生命周期钩子（lifecycle hook）上报的观察编译成一个 **git 版本化的 Markdown wiki**，让下一次会话、甚至不同厂商的 Agent（Claude Code → Codex → Cursor）都能在同一个目录里「接着上次的进度」。

它最本质的设计选择是 **compile-not-retrieve**：不做向量数据库即时检索，而是把零散观察编译成结构化页面，再通过 SQLite 的 FTS5、实体与图邻居检索。README 自己也明确把「Karpathy LLM Wiki」列为思想来源，把 agentmemory、basic-memory、cognee 等列为先例。

## 系统地图：一个二进制，一个数据目录

```
ai-memory（单个 Rust 二进制）
└── <data_dir>/
    ├── wiki/    # Markdown 源数据（真源），git 版本化
    ├── raw/     # 不可变的 sanitized 会话转录片段
    ├── db/      # SQLite 索引（FTS5 + 实体 + 向量）
    ├── models/  # 本地嵌入模型预留
    └── logs/    # 滚动日志
```

数据流是单向的：

```
各 Agent 生命周期钩子
    │  POST 观察（sanitized）
    ▼
MCP/HTTP 服务器
    │  单个 SQLite writer 串行写入
    ▼
编译成 Markdown 页面（wiki/）
    │
    ▼
检索：FTS5 + 实体 + 图邻居（可选向量 RRF）
    ▼
下一位 Agent 会话开头收到 bounded handoff
```

## 架构要点

### 1. 单一 writer 与「编译而非检索」

所有观察经钩子 POST 到服务器，由**单个 SQLite writer** 串行落盘，再编译成 Markdown 页面。坚持单一 writer，是把 SQLite 的写锁竞争挡在设计外：所有写入串行执行，读走一个可克隆的只读连接池，会话高并发也只需考虑读扩展。与「每次对话都全量检索向量库」的方案不同，它把记忆固化为结构化页面，靠 SQLite FTS5 全文检索、实体匹配与图邻居 RRF 混合召回（可选加向量 RRF），并对非全局检索做 bounded raw-observation fallback。

### 2. 生命周期捕获是零摩擦的

钩子采用 fire-and-forget 设计，只上报受限的、sanitized 的 prompt / 工具生命周期 / 会话边界观察。用户 prompt 与压缩后摘要最多保留 16 KiB；通知与工具摘录上限 2 KB，每条观察正文另有 16 KiB 持久后备。它**不是完整的原生转录**，这是刻意的取舍：捕获成本低，但保真度有限。

### 3. 按项目隔离是「构造上」保证的

每个项目落在 `<wiki_root>/<workspace_id>/<project_id>/…`，由稳定 UUID 定位。项目身份从 `$cwd` 推导：CLI 子命令会向上走到主 git 仓库根，让同一仓库的所有 worktree 共享一个项目身份；钩子路由默认用 `basename($cwd)`，也可 opt-in 仓库根规则。在任意祖先目录放一个 `.ai-memory.toml` 标记文件即可显式覆盖——适合多客户咨询、工作/个人分离、monorepo 或链接的 git worktree。同一页面路径可在两个项目并存而不冲突；重命名是改一列；清理是一次 `rm -rf`。

### 4. 跨 Agent 交接与 managed workstreams

「退出 Claude Code 中途换 Codex，几小时后在相同目录启动，下一位 Agent 在第一条 prompt 前看到 where you left off 区块」——这是它的招牌场景。进一步，`ai-memory run` 提供可选的 **managed workstreams**：对 Claude Code、Codex、OpenCode、Pi、Crush、Kimi Code、Command Code、Kiro CLI、OMP、Grok Build CLI、Antigravity CLI 等多套 harness 做透明的跨工具连续性（自动选 harness、原生 resume、参数透传、ledger 搜索）。直接启动（direct launch）的轻量路径不受影响。

### 5. 捕获豁免与后台自动完善：compile 的另一半

「编译」不是只在会话结束时跑一次。两条机制把 Karpathy 式 wiki 的「越用越新」补全：

- **捕获豁免有两档**。默认距最近标记文件（`.ai-memory.toml` 的 `[capture] ignore_paths`）最近的豁免策略，会在事件进入本地 spool / 服务器前，直接丢弃匹配的 file-tool 事件——敏感文件连轨迹都不落盘。更强的 `install-hooks --capture-mode allowlist` 则反转为**白名单**：一个仓库没有放置 marker，钩子就完全不产生任何生命周期事件。两者取舍相反：默认档是「漏掉 marker 只损失覆盖率」，白名单档是「漏掉 marker 只损失召回而保护机密」。后者的豁免只由原生 `ai-memory hook` 命令强制执行。配合既有按项目隔离，这是数据本地化诉求的第三道闸。
- **consolidation 与后台调度让记忆持续固化**。配置 `AI_MEMORY_LLM_PROVIDER` 后，会话结束时先生成一条**规则式**（不调 LLM）的 `sessions/<id>.md` 摘要；`memory_consolidate` 再把它重写成更持久的页面，或按 `concepts/`、`decisions/`、`gotchas/` 拆成多页并互加 wikilink。一个后台调度器在 hook 延迟之外遍历新完成会话，把审过的提议写进 pending-writes 审计、再默认自动合并回 wiki；管理员可设 `[auto_improve] require_approval = true` 改为人工审批，或直接关闭调度。每个 consolidation 与每个 session-end，`wiki/` 里都会落一次持久 git commit。**「编译」因此是增量维护，不是一次性快照。**

## 一次跨 CLI 交接：断点在哪，记忆如何跟上

把这套抽象落到一条真实工作线里，比单看机制图更接近使用时的判断：

```
① 搭环境：ai-memory run claude（Claude Code）
② 会话 1：修一个 flaky 集成测试
   PreToolUse/PostToolUse 钩子上报 sanitized 观察
   prompt 与压缩后摘要 ≤16 KiB，通知与工具摘录 ≤2 KB
   单个 SQLite writer 串行落盘，wiki/ 落一次 git commit
③ 退出：true SessionEnd → 规则式 sessions/<id>.md 摘要
   + 开一条 Handoff；若配了 LLM provider，
   memory_consolidate 展开成 concepts/decisions/gotchas 页
④ 半天后：同一目录 ai-memory run codex --yolo
   Codex 原生会话恢复 + 未消费 handoff 注入（包带版本化 origin marker）
   第一条 prompt 前读到 "where you left off"
   ——含结构、失败过的方案、待决问题，不用你重述架构
⑤ 提问：memory_query 走 FTS5 + 实体 + 图邻居 RRF
   编译结果 miss 时退回 bounded raw-observation 检索
```

几条值得留意的细节：第 ③ 步的摘要由规则生成，不消耗 token，也不会在无 LLM 配置时阻塞会话结束；第 ④ 步里不同 harness 的注入通道不一——Grok、Zero、Pool 不消费 `SessionStart` stdout，需经 MCP 的 `memory_handoff_accept` 取回手递；Codex 没有真正的 session-end 钩子，衔接交接依赖 managed 模式下 `ai-memory run codex` 的原生会话恢复。项目是否真能"无缝交接"，在第 ④ 步才见分晓。

## 支持矩阵（节选）

| 客户端 | 形态 | 说明 |
|--------|------|------|
| Claude Code | MCP + 生命周期钩子 | 支持会话感知隔离、可选的 `--capture-assistant` 双 opt-in |
| Codex | MCP + 生命周期钩子 | 无自动 true session-end 钩子，需手动 `ai-memory finalize-session` |
| Cursor | MCP + 生命周期钩子 | — |
| Gemini CLI | MCP + 生命周期钩子 | — |
| OpenClaw | MCP + 原生插件生命周期钩子 | — |
| VS Code Copilot | 仅 MCP | Copilot 尚无生命周期钩子 |
| Zed | 仅 MCP | 无 hooks / managed 支持 |
| Claude Desktop | 仅 MCP | 经 `mcp-remote` |
| Hermes Agent | 社区支持 | 社区维护插件，需自行审查 |

LLM 提供商支持 Anthropic、OpenAI、GitHub Copilot、Gemini、OpenCode Zen/Go 与 OIDC 设备认证；嵌入提供商支持 OpenAI、Voyage、Google Gemini 及 Ollama / LM Studio / vLLM 等无 key 的 OpenAI 兼容端点（需显式配置 `AI_MEMORY_EMBEDDING_BASE_URL` / `_MODEL` / `_DIM`）。

## 快速上手路径

1. 安装对应平台的 release 二进制（Linux amd64/arm64 Docker 镜像、macOS aarch64/x86_64 原生二进制、Windows WSL2 或原生 zip）。
2. 按目标 Agent 运行 MCP 配置安装（如 Claude Code 的 `install-mcp --session-aware`）+ 生命周期钩子安装。
3. 启动服务器（本机 loopback 可直接跑；多用户/非 loopback 场景按 `docs/deploy.md` 与 `docs/https-via-proxy.md` 配置 bearer token 与 TLS）。
4. 正常使用：会话结束自动编译；下一位 Agent 会话开头收到 handoff。
5. 需要向量检索时设置 `AI_MEMORY_EMBEDDING_PROVIDER`（嵌入可选，与 LLM 提供商相互独立）。

> 部分 harness（Codex、Antigravity、Kiro）没有真正的 true session-end 钩子，需要会话结束时手动 `ai-memory finalize-session` 才能生成最终摘要/交接。

## 检索与持久化边界

- **检索**：FTS-only 与 hybrid 路径在候选生成后应用同一 bounded page-authority 调整；嵌入改善相关性召回，但不决定哪条来源是 canonical。
- **持久化**：wiki 是普通 Markdown + git，可 `grep`、可在 Obsidian 打开、可用 `rsync` 备份。无向量数据库要维护、无 `write_note` 仪式、无手动上下文装载。
- **运行状态操作**（purge / rename / backup / restore / reset / reindex）：操作前务必读 `docs/lifecycle-ops.md` 的安全矩阵与每项目磁盘布局。

## 适用边界

**适合**：经常在多套 AI 编码 CLI 间切换、厌倦反复重述项目架构的开发团队；希望记忆以可 grep 的 Markdown + git 形式存在、而非黑盒向量库的用户；自托管、重视数据本地化的场景。

**需注意**：钩子捕获是 bounded 的（非完整转录），保真度上限明确；managed workstreams 是 opt-in，直接启动才是默认路径；不同 harness 的交接能力差异大（有的无 handoff 注入，只能经 MCP 恢复）；多用户场景的 `[slots] per_user` 是上下文注入隔离而非 RBAC。项目迭代极快（截至 2026-08-30 已到 v1.38.0），使用前留意 release 变更。

## 一句话总结

ai-memory 用「git 版本化的 Markdown wiki + SQLite 混合检索」这个极简内核，把跨 Agent、跨会话的记忆交接做成了一等能力——它是「Karpathy LLM Wiki 思路」在 Rust 生态里一个相当完整的工程化落地。
