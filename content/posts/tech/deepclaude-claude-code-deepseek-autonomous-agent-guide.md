---
title: "deepclaude: Claude Code 自主 Agent 循环遇上 DeepSeek V4 Pro"
date: "2026-05-06T11:41:17+08:00"
slug: "deepclaude-claude-code-deepseek-autonomous-agent-guide"
description: "deepclaude 是一个将 Claude Code 的自主 Agent 循环接入 DeepSeek V4 Pro、OpenRouter 等后端的开源工具，通过本地代理拦截 API 调用实现模型热切换，成本降至 Anthropic 原版的 1/17，同时保留完整的工具调用和文件编辑能力。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "DeepSeek", "AI Agent", "OpenRouter", "API 代理"]
---

# deepclaude: Claude Code 自主 Agent 循环遇上 DeepSeek V4 Pro

Claude Code 是目前最强的自主编程 Agent 之一，但每月 $200 的订阅费用加上用量上限，让很多个人开发者和小团队望而却步。**deepclaude** 这个项目做了件简单粗暴的事：把 Claude Code 的大脑换成 DeepSeek V4 Pro，身体保持不变——同一套交互体验，成本降到原来的 **1/17**。

项目地址：[aattaran/deepclaude](https://github.com/aattaran/deepclaude)，截至本文写作时已获得约 1,300+ Stars、60+ Forks，JavaScript 语言实现，MIT 许可证。

## 核心问题：Claude Code 为什么贵

Claude Code 本身是一个命令行工具，它的能力来自对 Anthropic API 的调用。Anthropic 的 Opus 模型输出 token 定价为 **$15/M**，而 Claude Code Max 订阅每月 $200 并有用量上限。

对比之下，DeepSeek V4 Pro 在 LiveCodeBench 上得分 **96.4%**，输出 token 定价仅为 **$0.87/M**。两者差了约 17 倍。

deepclaude 的思路不是重写 Claude Code，而是用本地代理接管 API 调用层，让 Claude Code 的 CLI 工具（文件读写、Bash 执行、Git 操作、子 Agent 启动等）继续正常工作，唯一变化的是模型提供商。

## 工作原理：代理拦截而非 fork

deepclaude 的核心是一个运行在 `localhost:3200` 的 HTTP 代理服务。它在 Claude Code 和各大 API 提供商之间充当中间人，架构如下：

```
Claude Code (终端)
    │
    ▼
localhost:3200 代理
    ├── /_proxy/mode  POST → 动态切换后端
    ├── /_proxy/status GET → 查询当前后端和运行时间
    ├── /_proxy/cost   GET → Token 用量和费用统计
    │
    ├── /v1/messages → 目标后端（DeepSeek / OpenRouter / Fireworks）
    └── 其他路径 → 直通 Anthropic（保持兼容性）
```

Claude Code 本身通过环境变量决定向哪里发请求：

| 环境变量 | 作用 |
|---|---|
| `ANTHROPIC_BASE_URL` | API 端点，默认为 `api.anthropic.com` |
| `ANTHROPIC_AUTH_TOKEN` | 后端 API Key |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | Opus 级别任务的模型名称 |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | Sonnet 级别任务的模型名称 |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | Haiku 级别（子 Agent）使用的模型 |
| `CLAUDE_CODE_SUBAGENT_MODEL` | 分裂出的子 Agent 所用模型 |

deepclaude 在启动时设置这些环境变量，指向本地代理；代理再根据当前选中的后端将请求转发到对应的 API 服务商。退出时恢复原始环境变量。

### 模型名重映射

不同后端对同一个模型有不同的命名方式，代理需要做一层翻译。例如 Claude Code 内部请求 `claude-opus-4-6` 时：

| 当前后端 | 实际发送到后端的模型名 |
|---|---|
| DeepSeek | `deepseek-v4-pro` |
| OpenRouter | `deepseek/deepseek-v4-pro` |
| Fireworks AI | `accounts/fireworks/models/deepseek-v4-pro` |

这段映射逻辑在 `proxy/model-proxy.js` 的 `MODEL_REMAP` 表中定义，切换后端时自动查表替换。

### Thinking Block 的处理

Anthropic 的模型支持 thinking block（思考块），但第三方后端可能会拒绝不认识的 thinking block（即使有签名）。代理在转发到非 Anthropic 后端前，会主动 `stripAllThinkingBlocks`，避免后端返回 400 错误。从非 Anthropic 后端切回 Anthropic 时，如果历史会话用过非 Anthropic 模型，同样会清除所有 thinking block，防止残留数据导致格式错误。

### SSE 流量的 Usage 修复

Claude Code 依赖响应中的 `usage` 字段计算 Token 消耗，但 DeepSeek/OpenRouter 在某些 SSE 事件（如 `message_start`、`message_delta`）中可能不包含 `usage` 字段，导致 Claude Code 端报 `"$.input_tokens" is undefined` 错误。代理实现了 `UsageNormalizer` 流处理器，在转发 SSE 时自动注入缺失的 usage 数据，保证 Claude Code 稳定运行。

## 支持的后端与定价

| 后端 | 启动参数 | 输入 $/M | 输出 $/M | 服务器 | 备注 |
|---|---|---|---|---|---|
| **DeepSeek**（默认） | `--backend ds` | $0.44 | $0.87 | 中国 | 自动上下文缓存（重复轮次降至 $0.004/M） |
| **OpenRouter** | `--backend or` | $0.44 | $0.87 | 美国 | 欧美地区延迟最低 |
| **Fireworks AI** | `--backend fw` | $1.74 | $3.48 | 美国 | 推理速度最快 |
| **Anthropic** | `--backend anthropic` | $3.00 | $15.00 | 美国 | 需要强推理时切回 |

**成本对比**（官方 README 数据）：

| 用量级别 | Anthropic Max | deepclaude (DeepSeek) | 节省 |
|---|---|---|---|
| 轻度（每月 10 天） | $200/月（封顶） | ~$20/月 | 90% |
| 重度（每月 25 天） | $200/月（封顶） | ~$50/月 | 75% |
| 含自动循环 | $200/月（封顶） | ~$80/月 | 60% |

DeepSeek 自带的上下文缓存机制使得 Agent 循环场景成本极低——首次请求后，系统提示词和文件上下文会被缓存，重复使用时降至 $0.004/M，相比未缓存的 $0.44/M 便宜约 110 倍。

## 安装与快速开始

### 前置要求

- Node.js 18+（代理服务依赖）
- Claude Code 已安装并登录（`claude auth login`）
- 对应后端的 API Key

### 第一步：获取 DeepSeek API Key

访问 [platform.deepseek.com](https://platform.deepseek.com)，注册账号并充值 $5，将 API Key 复制出来。

### 第二步：设置环境变量

**macOS / Linux：**

```bash
echo 'export DEEPSEEK_API_KEY="sk-your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**Windows (PowerShell)：**

```powershell
setx DEEPSEEK_API_KEY "sk-your-key-here"
```

### 第三步：安装 deepclaude

**macOS / Linux：**

```bash
chmod +x deepclaude.sh
sudo ln -s "$(pwd)/deepclaude.sh" /usr/local/bin/deepclaude
```

**Windows：**

```powershell
Copy-Item deepclaude.ps1 "$env:USERPROFILE\.local\bin\deepclaude.ps1"
# 或者将仓库目录加入 PATH
setx PATH "$env:PATH;C:\path\to\deepclaude"
```

### 第四步：启动

```bash
deepclaude                  # 使用 DeepSeek V4 Pro 启动 Claude Code
deepclaude --status         # 查看可用后端和 Key 配置状态
deepclaude --backend or     # 使用 OpenRouter（美国地区延迟最低）
deepclaude --backend fw     # 使用 Fireworks AI（推理最快）
deepclaude --cost           # 查看定价对比
deepclaude --benchmark      # 测试所有提供商的延迟
```

## 会话内后端热切换

deepclaude 支持在 Claude Code 运行过程中**不重启终端**直接切换后端，这是它区别于简单 API 替换脚本的亮点功能。

### 方式一：Slash 命令（推荐）

在 `~/.claude/commands/` 目录下创建三个命令文件：

**`deepseek.md`：**

```
Switch the model proxy to DeepSeek. Run this command silently and report the result:
curl -sX POST http://127.0.0.1:3200/_proxy/mode -d "backend=deepseek"
If successful, say: "Switched to DeepSeek."
```

**`anthropic.md`：**

```
Switch the model proxy back to Anthropic. Run this command silently and report the result:
curl -sX POST http://127.0.0.1:3200/_proxy/mode -d "backend=anthropic"
If successful, say: "Switched to Anthropic."
```

**`openrouter.md`：**

```
Switch the model proxy to OpenRouter. Run this command silently and report the result:
curl -sX POST http://127.0.0.1:3200/_proxy/mode -d "backend=openrouter"
If successful, say: "Switched to OpenRouter."
```

之后在 Claude Code 会话中直接输入 `/deepseek`、`/anthropic` 或 `/openrouter` 即可热切换模型。

### 方式二：CLI 参数

```bash
deepclaude --switch deepseek   # 或: ds, or, fw, anthropic
deepclaude -s anthropic
```

### 方式三：VS Code 快捷键

通过 VS Code 的 Tasks 和 keybindings 可以绑定键盘快捷键快速切换。

### 费用实时查询

```bash
curl -s http://127.0.0.1:3200/_proxy/cost
```

返回示例：

```json
{
  "backends": {
    "deepseek": {
      "input_tokens": 125000,
      "output_tokens": 45000,
      "requests": 12,
      "cost": 0.0941,
      "anthropic_equivalent": 1.05
    }
  },
  "total_cost": 0.0941,
  "anthropic_equivalent": 1.05,
  "savings": 0.9559
}
```

代理会持续追踪 Token 消耗，并计算相对于 Anthropic 定价的节省金额。

## Remote Control 模式

Claude Code 原生支持浏览器远程控制（`claude remote-control`），但该功能依赖 Anthropic 的 WebSocket 桥接服务 `wss://bridge.claudeusercontent.com`，无法直接替换。deepclaude 通过分离流量解决了这个问题：

```
claude remote-control
  ├── Bridge WebSocket → wss://bridge.claudeusercontent.com（Anthropic，必须）
  └── Model API 调用 → localhost:3200（代理，转发到 DeepSeek）
```

启动方式：

```bash
deepclaude --remote               # 浏览器远程控制 + DeepSeek
deepclaude --remote -b or         # 浏览器远程控制 + OpenRouter
deepclaude --remote -b anthropic  # 浏览器远程控制 + Anthropic（标准版）
```

使用 Remote Control 的前提条件：
- Claude Code 已完成 `claude auth login`
- 拥有 claude.ai 订阅（桥接服务是 Anthropic 基础设施）
- Node.js 18+（代理服务依赖）

## 已知限制

deepclaude 在 README 中明确标注了以下限制：

| 功能 | 状态 | 原因 |
|---|---|---|
| 文件读写、编辑 | ✅ 正常工作 | 不涉及模型能力 |
| Bash / PowerShell 执行 | ✅ 正常工作 | 不涉及模型能力 |
| Glob / Grep 搜索 | ✅ 正常工作 | 不涉及模型能力 |
| 多步自主工具循环 | ✅ 正常工作 | 核心功能保留 |
| 子 Agent 派生 | ✅ 正常工作 | 通过 `CLAUDE_CODE_SUBAGENT_MODEL` 配置 |
| Git 操作 | ✅ 正常工作 | 不涉及模型能力 |
| 项目初始化（`/init`） | ✅ 正常工作 | 不涉及模型能力 |
| Thinking 模式 | ✅ 默认启用 | 不涉及模型能力 |
| 图片 / 视觉输入 | ❌ 不支持 | DeepSeek 的 Anthropic 兼容端点不支持图片 |
| 并行工具调用 | ⚠️ 受限 | DeepSeek 支持最多 128 个工具/次，但 Claude Code 默认顺序发送 |
| MCP Server 工具 | ❌ 不支持 | 不通过兼容层传递 |
| Prompt Caching 节省 | ⚠️ 机制不同 | DeepSeek 有自己的缓存（自动），Anthropic 的 `cache_control` 参数被忽略 |

### 智能分工建议

根据项目 README 的经验总结：

- **日常任务（80% 的工作量）**：DeepSeek V4 Pro 与 Claude Opus 效果相当，可直接使用 deepclaude 默认配置。
- **复杂推理任务（20% 的工作量）**：切换到 `--backend anthropic`，处理完后再切回。

## 适用场景与优势

**适合使用 deepclaude 的场景：**
- 个人开发者日常编程、脚本编写、小工具开发
- 团队内部 CI/CD 流水线中的代码生成和修复
- 需要大量试错和迭代的探索性项目
- 预算有限的独立开发者或开源项目维护者

**不适合的场景：**
- 需要使用视觉能力（截图分析、UI 检查）的任务
- 需要调用 MCP Server 工具的任务
- 对推理质量要求极高、容不得任何差错的严肃生产代码审查（建议保留 Anthropic 作为备用）

## 与其他方案的对比

如果你的目标是"用更便宜的大模型跑 Agent 编码循环"，市面上的替代方案大概有两类：

**从零搭建 Agent 框架**（如 LangChain、AutoGPT）：需要自己处理工具调用、状态管理、错误重试，门槛高。deepclaude 的优势是直接利用 Claude Code 成熟的 Agent 实现，不需要重新造轮子。

**API 代理脚本**：最简单的方案是改环境变量直连 DeepSeek，但不支持会话内热切换、不处理模型名重映射、不修复 SSE usage 问题。deepclaude 在这层基础上做了完整的兼容性封装。

## 总结

deepclaude 是一个定位清晰、执行干净的工具。它没有重新发明轮子，而是精准地解决了"如何用更低的成本使用 Claude Code 的成熟 Agent 体验"这个问题。代理架构设计合理，支持多后端热切换，覆盖了主要的兼容性问题（模型重映射、thinking block 清理、usage 字段修复）。

对于每天都在用 Claude Code 写代码的开发者来说，如果日常 80% 的任务不需要 Opus 级别的推理能力，deepclaude 是一个可以直接上手的省钱方案。剩下的 20% 复杂任务，通过 `/anthropic` 切回去就好。

项目地址：[https://github.com/aattaran/deepclaude](https://github.com/aattaran/deepclaude)
