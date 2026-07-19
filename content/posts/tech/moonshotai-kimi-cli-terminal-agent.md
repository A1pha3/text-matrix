---
title: "Kimi CLI：MoonshotAI 给终端 Agent 的另一种答案，ACP + Shell Mode + MCP"
date: 2026-07-20T03:02:36+08:00
categories: ["技术笔记"]
tags: ["agent", "cli", "kimi", "acp", "mcp"]
description: "Kimi CLI 是 MoonshotAI 推出的终端 AI Agent，主打 Shell Mode（Ctrl-X 切到 shell）、ACP 协议接入 IDE、MCP 工具管理三大特性。它正在演进为 Kimi Code CLI，但所有现有安装与文档继续可用。"
---

# Kimi CLI：MoonshotAI 给终端 Agent 的另一种答案，ACP + Shell Mode + MCP

## 一句话判断

Kimi CLI 是 MoonshotAI 给中文开发者的"终端 AI Agent"——它的差异化不在模型，而在 **Shell Mode**（Ctrl-X 切到 shell 直接跑命令）和 **ACP（Agent Client Protocol，Agent 客户端协议）** 原生支持。这两点让它在"我既要 AI 帮我写代码，又要 AI 帮我跑命令"的场景里比同类工具更顺手。它正在演进为下一代 [Kimi Code CLI](https://github.com/MoonshotAI/kimi-code)，但 README 明确"this project will be gradually wound down; the docs and existing installations remain available"。

## 项目定位

- **仓库**：`MoonshotAI/kimi-cli`，Apache-2.0 协议，Python
- **GitHub Stars**：9.8K，Forks 1.2K（2026-07-16 数据）
- **PyPI**：[`kimi-cli`](https://pypi.org/project/kimi-cli/)
- **官方文档**：[moonshotai.github.io/kimi-cli](https://moonshotai.github.io/kimi-cli/zh/)（中英双语）
- **核心能力**：读 / 写代码、跑 shell、抓取网页、自主规划任务

## 系统地图

| 模块 | 责任 |
|------|------|
| Shell Mode | Ctrl-X 切换，让 Kimi CLI 临时充当 shell 直接执行命令 |
| ACP Adapter | 通过 Agent Client Protocol 把 Kimi CLI 暴露给 Zed / JetBrains 等 IDE |
| MCP Manager | `kimi mcp` 子命令组管理 MCP server |
| VS Code Extension | 配套的 [Kimi Code VS Code 扩展](https://marketplace.visualstudio.com/items?itemName=moonshot-ai.kimi-code) |
| Zsh Plugin | [zsh-kimi-cli](https://github.com/MoonshotAI/zsh-kimi-cli) 让 shell 拥有 agent 能力 |

## 关键机制拆解

### 1. Shell Mode：终端里的"两栖"工具

Kimi CLI 不是纯 agent 工具，它自带 shell 模式：

- 按 **Ctrl-X** 切换到 shell command mode
- 在这个 mode 里可以直接跑 `ls`、`cd`、`grep` 等命令
- 命令结果会自动喂回 agent 上下文
- 退出 shell mode 回到 agent 模式继续对话

这解决了"agent 工具和 shell 工具割裂"的痛点。在 Claude Code / Codex CLI 里，你想跑一个命令得退出 agent 上下文，丢掉了之前的会话状态。Kimi CLI 用一个热键切两栖，把"agent 编排"和"命令执行"放进同一个 UI。

> 注意：README 注明 `cd` 等 built-in shell 命令暂不支持。

### 2. ACP 原生支持

ACP（Agent Client Protocol）是 Zed / JetBrains 等 IDE 推出的"agent server 协议"，让 IDE 可以接入外部 agent 进程。Kimi CLI 是首批原生支持 ACP 的终端 agent：

```json
{
  "agent_servers": {
    "Kimi CLI": {
      "type": "custom",
      "command": "kimi",
      "args": ["acp"],
      "env": {}
    }
  }
}
```

把它配置到 Zed 或 JetBrains 后，IDE 的 agent 面板里就能创建 Kimi CLI threads，IDE 负责 UI，Kimi CLI 负责 agent runtime。和 Claude Code 的 IDE 集成（CLI 进程跑在 IDE 内部）相比，ACP 协议让 agent 进程和 IDE 解耦，更接近"agent 服务化"的方向。

### 3. MCP 工具管理

Kimi CLI 提供完整的 MCP 子命令组：

```bash
# 添加 streamable HTTP server
kimi mcp add --transport http context7 https://mcp.context7.com/mcp \
  --header "CONTEXT7_API_KEY: ctx7sk-your-key"

# 添加带 OAuth 认证的 server
kimi mcp add --transport http --auth oauth linear https://mcp.linear.app/mcp

# 添加 stdio server
kimi mcp add --transport stdio chrome-devtools -- npx chrome-devtools-mcp@latest

# 列出 / 移除 / 授权
kimi mcp list
kimi mcp remove chrome-devtools
kimi mcp auth linear
```

同时支持 `--mcp-config-file` ad-hoc 配置，让用户在脚本场景下临时接入 MCP 而不污染全局配置。MCP 三种 transport（stdio / http streamable / http + OAuth）的全覆盖说明 Kimi 团队把 MCP 当作一等公民来对待。

### 4. Zsh 插件

[zsh-kimi-cli](https://github.com/MoonshotAI/zsh-kimi-cli) 提供 zsh 集成——安装后 `~/.zshrc` 加 `plugins=(... kimi-cli)`，按 Ctrl-X 切到 agent mode。配合上面的 Shell Mode，Kimi CLI 在 zsh 用户手里的形态最完整：同一个 shell，按需切换 agent / command mode。

## 演进路线：Kimi Code CLI

README 顶部显著位置说明：

> Kimi CLI is evolving into Kimi Code CLI — the next-generation terminal AI agent from the same team. Installing Kimi Code CLI automatically migrates your configuration and sessions.

也就是说 Kimi CLI 是过渡形态，新功能会落在 [MoonshotAI/kimi-code](https://github.com/MoonshotAI/kimi-code)。但现有 `pip install kimi-cli` 仍然能用，文档继续维护。这意味着迁移到 Kimi Code CLI 是一行命令的事，但不必现在就强切。

## 适用人群

- **中文开发者**：原生中文文档 + 国内友好的网络访问
- **Zed / JetBrains 用户**：想用 ACP 接入国产 agent 的人
- **Zsh 重度用户**：把 agent 当 shell 扩展来用的人
- **需要 MCP 全 transport 的人**：stdio / http streamable / OAuth 三件套都覆盖

## 不适合谁

- **想要 GUI / IDE 内嵌原生 agent 的人**：Kimi CLI 是终端工具，VS Code 扩展只是 wrapper
- **需要长期支持 LTS 版本的人**：项目明确会"gradually wound down"，新功能迁移到 Kimi Code CLI
- **不愿意用国内 LLM 的人**：绑定 MoonshotAI 的 Kimi 模型，provider 不可切换

## 仓库地址

https://github.com/MoonshotAI/kimi-cli

## 阅读路径建议

1. `pip install kimi-cli` + `kimi login`，5 分钟起跑
2. 在 shell 里按 Ctrl-X 切到 shell mode，体验两栖切换
3. 加一个 MCP server（推荐 context7），看 MCP 工具怎么被 agent 编排
4. 读 docs/getting-started.md 的 ACP 配置节，把 Kimi CLI 接到 Zed 或 JetBrains