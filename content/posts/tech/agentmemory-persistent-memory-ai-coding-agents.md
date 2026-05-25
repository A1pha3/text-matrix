---
title: "agentmemory：一款基于真实评测基准的 AI 编码智能体持久化记忆引擎"
date: 2026-05-14T11:43:15+08:00
slug: "agentmemory-persistent-memory-ai-coding-agents"
description: "agentmemory 是为 AI 编码智能体设计的持久化记忆引擎，基于真实评测基准构建，支持 Claude Code、Cursor、Codex CLI 等 14+ 主流智能体，通过 12 个自动 Hook 实现零手动介入的记忆捕获，采用 BM25+向量+知识图谱混合检索，R@5 达 95.2%，每年 token 消耗降至约 170K（成本约 $10），且无需外部数据库依赖。本文详解其核心架构、检索机制与多智能体协同能力。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "agentmemory", "MCP", "记忆系统", "编码智能体"]
---

# agentmemory：一款基于真实评测基准的 AI 编码智能体持久化记忆引擎

## 项目概览

**agentmemory**（`rohitg00/agentmemory`）是当前 GitHub Trending 热榜项目，Star 数已达 **7,899**，Fork 675，主语言为 TypeScript。项目给自己的定位是"#1 Persistent memory for AI coding agents based on real-world benchmarks"——基于真实评测基准构建的 AI 编码智能体持久化记忆引擎。

核心解决一个具体问题：每次新会话开始，智能体都会忘记上一次做的事，你需要反复解释代码结构、偏好、已完成的工作。agentmemory 在后台静默运行，把智能体的每一次操作记录下来，压缩为可检索的记忆，下次会话开始时自动注入相关上下文——无需手动整理 MEMORY.md 或 CLAUDE.md。

项目内置于 [iii engine](https://github.com/iii-hq/iii) 之上，当前稳定版依赖 `iii-engine v0.11.2`，API 兼容 `iii-sdk ^0.11.0`。对外提供三种接入方式：MCP 服务器（51 个工具）、REST API（104 个端点）、iii 函数（供有 iii SDK 的语言直接调用）。

---

## 核心能力与技术创新

### 12 个自动 Hook，零手动介入

agentmemory 随 agent 生命周期自动挂载 12 个钩子（Hook），包括 `SessionStart`、`UserPromptSubmit`、`PreToolUse`、`PostToolUse`、`PreCompact`、`Stop` 等。智能体每次执行工具、提交提示或结束会话时，记忆引擎自动捕获并处理，无需开发者手动调用 `memory.add()`。

这与 mem0（需手动 `add()` 调用）和 Letta/MemGPT（靠 agent 自我编辑）形成鲜明对比——agentmemory 实现的是真正零干预的被动捕获。

### 三路混合检索（BM25 + Vector + Knowledge Graph）

检索层面采用三层融合：

- **BM25**（经典关键词检索）
- **向量检索**（支持 6 家提供商 + 本地 `all-MiniLM-L6-v2` 模型，完全免费无需 API Key）
- **知识图谱**（实体关系建模）

三种结果通过 **RRF（Reciprocal Rank Fusion）** 融合排序，取 top-K 输入上下文。项目在 ICLR 2025 的 **LongMemEval-S** 评测集（500 题）上达到 **R@5 = 95.2%**，对比 BM25-only 的 86.2% 有显著提升。对比竞品：mem0 R@5 = 68.5%，Letta = 83.2%。

### 四层记忆生命周期

agentmemory 的记忆不是静态存储，而是动态演化的四层结构：

1. **Raw Observation**——原始工具调用结果经 SHA-256 去重（5 分钟窗口）后存入
2. **隐私过滤**——自动剥离 secret、API Key 等敏感信息
3. **LLM 压缩**——将原始观测压缩为结构化事实（facts）、概念（concepts）和叙事（narrative）
4. **遗忘机制**——基于权重衰减和自动遗忘策略管理记忆过期

### 极低的 Token 消耗

| 方案 | 每年 Token 数 | 每年成本 |
|------|-------------|---------|
| 粘贴完整上下文 | 19.5M+ | 超出窗口，无法使用 |
| LLM 总结 | ~650K | ~$500 |
| **agentmemory** | **~170K** | **~$10** |
| agentmemory + 本地 Embedding | ~170K | **$0** |

本地 Embedding 使用 `all-MiniLM-L6-v2` 模型，完全免费，且模型在本地运行，数据不离开机器。

### 无外部数据库依赖

mem0 需要 Qdrant 或 pgvector，Letta 需要 Postgres + 向量数据库，而 agentmemory **仅依赖 SQLite + iii-engine**，无需额外部署任何外部存储服务，降低了使用门槛和运维成本。

---

## 支持的智能体生态

agentmemory 官方支持的智能体列表（持续扩展中）：

| 智能体 | 接入方式 |
|--------|---------|
| Claude Code | 12 Hook + MCP + Skills |
| OpenClaw | MCP + 插件 |
| Hermes | MCP + 6 Hook Memory Provider |
| Cursor | MCP Server |
| Codex CLI | MCP Server + Plugin（含 6 Hook + 4 Skills）|
| Claude Desktop | MCP Server |
| Cline / Roo Code / Kilo Code | MCP Server |
| Windsurf | MCP Server |
| Gemini CLI | MCP Server |
| OpenCode | MCP Server（`opencode.json` 配置）|
| Goose | MCP Server |
| Aider | REST API |
| pi | 插件目录拷贝 |

配置方式高度统一：对于大多数使用 `mcpServers` 形状的智能体，只需在配置文件中加入同一个 MCP 服务器块，无需改变任何其他设置。对于支持 Skill 的智能体（如 Claude Code、Codex CLI），还额外提供 `/recall`、`/remember`、`/session-history`、`/forget` 四个快捷技能。

---

## 快速上手

### 30 秒体验

```bash
# Terminal 1: 启动记忆服务器
npx @agentmemory/agentmemory

# Terminal 2: 加载示例数据并体验检索
npx @agentmemory/agentmemory demo
```

`demo` 命令会播发 3 个真实感会话（JWT 鉴权、N+1 查询修复、限流配置），然后用语义检索演示——搜索"数据库性能优化"能找到"N+1 查询修复"，这是关键词检索做不到的。实时查看记忆构建过程：打开 `http://localhost:3113`。

### Claude Code 接入（一行命令）

```
Install agentmemory: run `npx @agentmemory/agentmemory` in a separate terminal to start the memory server. Then run `/plugin marketplace add rohitg00/agentmemory` and `/plugin install agentmemory` — the plugin registers all 12 hooks, 4 skills, AND auto-wires the `@agentmemory/mcp` stdio server via its `.mcp.json`, so you get 51 MCP tools without any extra config step. Verify with `curl http://localhost:3111/agentmemory/health`. The real-time viewer is at http://localhost:3113.
```

### OpenClaw 接入

在 OpenClaw 的 MCP 配置文件中加入：

```json
{
  "mcpServers": {
    "agentmemory": {
      "command": "npx",
      "args": ["-y", "@agentmemory/mcp"],
      "env": {
        "AGENTMEMORY_URL": "http://localhost:3111"
      }
    }
  }
}
```

更深度的记忆槽（memory slot）集成：拷贝 `integrations/openclaw` 到 `~/.openclaw/extensions/agentmemory`，并在 `~/.openclaw/openclaw.json` 中启用 `plugins.slots.memory = "agentmemory"`。

### 导入已有会话

已有 Claude Code 的 JSONL 转录文件想要导入？：

```bash
npx @agentmemory/agentmemory import-jsonl ~/.claude/projects/-my-project/abc123.jsonl
```

导入后可在 Replay 功能中回放历史会话的时间线（支持 0.5× 到 4× 播放速度）。

### 从源码构建

```bash
git clone https://github.com/rohitg00/agentmemory.git && cd agentmemory
npm install && npm run build && npm start
```

会优先使用本地安装的 `iii`（如果 `iii` 已在 PATH 中），否则回退使用 Docker Compose 启动 `iiidev/iii:0.11.2`。

---

## 架构速览

```
PostToolUse hook 触发
  -> SHA-256 去重（5 分钟窗口）
  -> 隐私过滤器（剥离密钥、API Key）
  -> 存储原始观测
  -> LLM 压缩为结构化事实 + 概念 + 叙事
  -> 向量嵌入（6 家提供商 + 本地 all-MiniLM-L6-v2）
```

所有存储默认在本地的 SQLite 数据库，iii-engine 负责核心的记忆组织与检索逻辑。MCP 服务器（`@agentmemory/mcp`）与 REST API（`:3111`）共享同一后端，实时查看器（Viewer）监听 `:3113`。

---

## 多智能体协同机制

agentmemory 设计之初就考虑了多智能体共享记忆场景：

- **MCP + REST**——所有智能体通过标准 MCP 协议或 REST API 访问同一记忆服务器
- **Leases（租约）**——防止多个智能体同时修改同一记忆槽
- **Signals（信号）**——智能体间事件通知
- **Actions / Routines**——跨智能体的自动化流程编排

这意味着当你同时使用 Claude Code（写代码）和 Aider（代码审查）时，两者可以访问同一份关于项目架构的记忆，无需各自独立维护。

---

## 适用场景、优势与边界

### 适合的场景

- 多会话、长周期的 AI 辅助编码项目，代码库结构复杂、团队成员更替频繁
- 同时使用多个编码智能体的开发者，希望共享关于同一项目的上下文
- 需要在智能体会话之间保持偏好、一致性决策记录的项目
- 对数据隐私有要求（记忆本地存储，不走云端）的团队

### 优势

- **零手动介入**：12 个自动 Hook 自动捕获，无需改变工作流
- **评测驱动**：95.2% R@5 来自 ICLR 2025 真实评测集 LongMemEval-S，有可查证的 Benchmark
- **极低 Token 成本**：~170K tokens/年，约 $10（本地 Embedding 免费的场景下接近 $0）
- **无外部依赖**：SQLite + iii-engine，无需运维 Qdrant/Postgres 等外部数据库
- **跨智能体共享**：同一记忆服务器可为多个不同智能体提供记忆服务

### 边界与局限

- **Windows 支持较新**：当前 Windows 下的 `iii-engine` 安装需要手动下载预编译二进制，尚无 PowerShell 安装脚本或 scoop/winget 包
- **依赖特定 iii-engine 版本**：当前 agentmemory **锁定在 iii-engine v0.11.2**，`v0.11.6` 引入了新的沙箱模型尚未适配（参考 [iii-hq/iii releases v0.11.2](https://github.com/iii-hq/iii/releases/tag/iii%2Fv0.11.2)）
- **记忆质量依赖 LLM 压缩**：如果使用的 LLM 上下文窗口本身受限或压缩质量下降，记忆质量也会受影响
- **沙箱环境需额外配置**：在 Flatpak/Snap 等受限容器中使用时，需要设置 `AGENTMEMORY_FORCE_PROXY` 并指向可访问的 LAN 地址

---

## 总结与延伸阅读

agentmemory 解决的是 AI 编码智能体"每次会话从零开始"这个真实痛点。它不是一个简单的笔记插件，而是一套基于 iii engine 的完整记忆引擎——三层混合检索、四层记忆生命周期、零手动介入的自动捕获、跨智能体共享能力，加上在 ICLR 2025 真实评测集上的可查证 Benchmark，让它成为目前记忆类工具中数据最扎实的一个。

如果你同时使用多个编码智能体、或者厌烦了每次新会话都要重新解释项目结构，agentmemory 值得一试。项目目前仍在活跃维护中（最近更新于 2026-05-14），Star 数接近 8K，是一个正在上升期的高质量项目。

**相关资源：**

- 项目主页：https://agent-memory.dev
- GitHub：https://github.com/rohitg00/agentmemory
- iii engine（底层引擎）：https://github.com/iii-hq/iii
- Benchmark 详情：[benchmark/LONGMEMEVAL.md](https://github.com/rohitg00/agentmemory/blob/main/benchmark/LONGMEMEVAL.md)、[benchmark/COMPARISON.md](https://github.com/rohitg00/agentmemory/blob/main/benchmark/COMPARISON.md)
- npm 包：https://www.npmjs.com/package/@agentmemory/agentmemory