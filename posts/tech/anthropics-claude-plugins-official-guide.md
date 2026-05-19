---
title: "Anthropic Claude Plugins 官方商店：从入门到精通的完整指南"
date: 2026-05-19T20:10:00+08:00
draft: false
tags:
  - Claude Code
  - MCP
  - AI编程
  - Anthropic
  - 插件系统
categories:
  - 技术指南
slug: anthropics-claude-plugins-official-guide
description: "全面解析 Anthropic 官方 Claude Code 插件目录，涵盖 35 个内部插件和 15 个第三方插件，深入讲解插件架构、Skill/Agent/Command 开发、MCP 集成，以及如何从零构建生产级插件。"
keywords:
  - Claude Code plugins
  - MCP server
  - Claude plugins official
  - claude-plugins-official
  - Anthropic plugin system
---

# Anthropic Claude Plugins 官方商店：从入门到精通的完整指南

> **今日趋势：** 🦞 1,244 stars | ⭐ 19,816 total stars | 🍴 2,489 forks
> **仓库：** [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official)

---

## 📊 项目概览

| 指标 | 数值 |
|------|------|
| **GitHub** | [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) |
| ** Stars** | ⭐ 19,816 |
| **今日新增** | 📈 +1,244 stars |
| **Forks** | 🍴 2,489 |
| **主语言** | Python |
| **创建时间** | 2025-11-20 |
| **维护方** | Anthropic |
| **官方文档** | [code.claude.com/docs/en/plugins](https://code.claude.com/docs/en/plugins) |

---

## 🎯 这个仓库是什么？

`claude-plugins-official` 是 **Anthropic 官方管理的 Claude Code 插件市场**。它不是一个普通的开源项目——它是 Claude Code 的官方插件分发平台，类似于 VS Code 的 Marketplace 或 npm 的官方注册表。

仓库分为两大板块：

```
claude-plugins-official/
├── plugins/           # 🤖 Anthropic 官方开发的内部插件（35个）
└── external_plugins/  # 🌍 第三方合作伙伴插件（15个）
```

### 内部插件（Internal Plugins）

由 Anthropic 团队开发和维护，覆盖开发全流程：

| 插件名称 | 功能定位 |
|----------|---------|
| `plugin-dev` | 插件开发工具包（核心推荐） |
| `skill-creator` | Skill 创建工作流 |
| `mcp-server-dev` | MCP Server 开发框架 |
| `agent-sdk-dev` | Agent SDK 开发工具 |
| `code-review` | 代码审查自动化 |
| `feature-dev` | 功能开发工作流 |
| `code-modernization` | 代码现代化改造 |
| `code-simplifier` | 代码简化工具 |
| `explanatory-output-style` | 输出风格指导 |
| `learning-output-style` | 学习风格输出 |
| `commit-commands` | 提交命令集 |
| `pr-review-toolkit` | PR 审查工具包 |
| `security-guidance` | 安全指南 |
| `session-report` | 会话报告生成 |
| `frontend-design` | 前端设计支持 |
| `math-olympiad` | 数学奥赛解题 |
| `playground` | 沙盒实验环境 |
| `clangd-lsp` / `pyright-lsp` / `gopls-lsp` 等 | 12 种 LSP 插件 |

### 外部插件（External Plugins）

第三方合作伙伴提供的高质量插件：

| 插件名称 | 集成服务 |
|----------|---------|
| `asana` | Asana 项目管理（SSE 连接） |
| `github` | GitHub Copilot MCP（HTTP + Bearer Token） |
| `gitlab` | GitLab 集成 |
| `linear` | Linear 项目跟踪 |
| `discord` | Discord 通知 |
| `telegram` | Telegram 消息推送 |
| `firebase` | Firebase 后端服务 |
| `terraform` | Terraform IaC |
| `playwright` | Playwright 浏览器自动化 |
| `greptile` | 代码搜索增强 |
| `context7` | 上下文管理 |
| `serena` | Serena 项目管理 |
| `laravel-boost` | Laravel 开发加速 |
| `imessage` | iMessage 集成 |

---

## 🏗️ 插件架构详解

### 标准插件结构

每个插件遵循统一的目录布局：

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json      # ✅ 必须：插件元数据清单
├── .mcp.json            # 可选：MCP Server 配置
├── commands/            # 可选：斜杠命令（Slash Commands）
├── agents/              # 可选：自主 Agent 定义
├── skills/              # 可选：Skill 定义
├── hooks/               # 可选：钩子脚本
└── README.md            # 可选：文档
```

### plugin.json 清单格式

```json
{
  "name": "plugin-dev",
  "description": "Plugin development toolkit with skills for creating agents, commands, hooks, MCP integrations, and comprehensive plugin structure guidance",
  "author": {
    "name": "Anthropic",
    "email": "support@anthropic.com"
  }
}
```

### MCP Server 配置（.mcp.json）

支持四种连接类型：

```json
// 类型1：stdio（本地进程，适合本地 MCP Server）
{
  "my-local-server": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
  }
}

// 类型2：SSE（Server-Sent Events，适合需要 OAuth 的远程服务）
{
  "asana": {
    "type": "sse",
    "url": "https://mcp.asana.com/sse"
  }
}

// 类型3：HTTP（REST API，适合 GitHub 等服务）
{
  "github": {
    "type": "http",
    "url": "https://api.githubcopilot.com/mcp/",
    "headers": {
      "Authorization": "Bearer ${GITHUB_PERSONAL_ACCESS_TOKEN}"
    }
  }
}

// 类型4：WebSocket（实时双向通信）
{
  "realtime-tools": {
    "type": "websocket",
    "url": "wss://realtime.example.com/ws"
  }
}
```

**环境变量扩展：** 支持 `${CLAUDE_PLUGIN_ROOT}`（插件根目录）和 `${USER_VAR}`（用户变量）。

---

## 📦 Skill 系统：插件的核心扩展机制

### 什么是 Skill？

Skill 是 Claude Code 的核心扩展单元，分为两种类型：

| 类型 | 触发方式 | 文件位置 |
|------|---------|---------|
| **Model-invoked Skill** | 任务上下文自动激活 | `skills/<name>/SKILL.md` |
| **User-invoked Skill** | 用户斜杠命令 `/skill-name` | `skills/<name>/SKILL.md` |

### Skill 文件格式

```yaml
---
name: hook-development
description: 当用户说 "create a hook"、"add a PreToolUse hook"、"validate tool use" 时激活
version: 1.0.0
---

# Hook Development Guide

## 核心概念

Hooks 允许你在 Claude Code 的关键事件点插入自定义逻辑...
```

### plugin-dev 的七大 Skill（核心重点）

`plugin-dev` 是整个仓库最重要的插件，它提供了开发任何插件所需的全部指导：

| Skill | 触发关键词 | 核心功能 |
|-------|-----------|---------|
| `hook-development` | create a hook, PreToolUse, validate | 事件驱动自动化、钩子脚本开发 |
| `mcp-integration` | add MCP server, .mcp.json | MCP Server 配置、OAuth/stdio/HTTP |
| `plugin-structure` | plugin structure, plugin.json | 插件目录布局、清单配置 |
| `plugin-settings` | plugin settings, .local.md | 插件配置、YAML 前端matter |
| `command-development` | slash command, arguments | 斜杠命令开发、前端matter参数 |
| `agent-development` | create agent, subagent | 自主 Agent 定义、YAML 前端matter |
| `skill-development` | create skill, SKILL.md | Skill 创建、渐进式披露原则 |

### 渐进式披露原则

每个 Skill 采用三层披露结构：

```
第一层（始终加载）：
  └── 元数据：简短描述 + 强触发短语

第二层（触发时加载）：
  └── SKILL.md：核心 API 参考（~1,500-2,000 词）

第三层（按需加载）：
  └── references/、examples/、scripts/
      └── 详细指南、工作示例、实用脚本
```

---

## 🔧 Agent 系统：自主执行单元

### Agent 文件格式

Agent 同样使用 YAML frontmatter + system prompt：

```yaml
---
name: plugin-creator
description: |
  当用户需要创建新插件时激活。示例：
  - "Create a plugin for database migrations"
  - "Build a plugin that integrates with Slack"
model: opus
color: "#FF6B35"
tools: [Read, Write, Exec, Grep, Glob]
---

你是插件创建专家。当用户请求创建新插件时：

1. 首先了解插件目的和需求
2. 规划组件结构（skills, commands, agents, hooks）
3. 使用 ${CLAUDE_PLUGIN_ROOT} 确保路径可移植
4. 逐个实现组件并验证
5. 生成完整 README 文档

遵循 plugin-dev 的最佳实践...
```

### 完整字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | ✅ | Agent 唯一名称 |
| `description` | ✅ | 触发描述，使用 `<example>` 块确保可靠触发 |
| `model` | ❌ | 可选 `opus`/`sonnet`/`haiku`，默认继承父级 |
| `color` | ❌ | UI 展示颜色（hex） |
| `tools` | ❌ | 允许使用的工具列表，默认全部 |
| `when` | ❌ | 触发条件描述 |

---

## 🪝 Hook 系统：事件驱动自动化

### 支持的 Hook 事件

| 事件 | 触发时机 | 典型用途 |
|------|---------|---------|
| `PreToolUse` | 工具执行前 | 输入验证、安全检查 |
| `PostToolUse` | 工具执行后 | 结果记录、后续触发 |
| `Stop` | 会话停止时 | 资源清理、连接关闭 |
| `SubagentStop` | 子 Agent 停止 | 结果聚合、状态同步 |
| `SessionStart` | 会话启动 | 上下文初始化 |
| `SessionEnd` | 会话结束 | 报告生成、清理 |
| `UserPromptSubmit` | 用户提交提示 | 内容预处理、过滤 |
| `PreCompact` | 压缩前 | 状态快照保存 |
| `Notification` | 通知触发 | 自定义通知处理 |

### Hook 脚本示例（PreToolUse）

```bash
#!/bin/bash
# plugins/my-plugin/hooks/validate-write.sh
# 验证文件写入操作的安全性

TOOL_NAME="$1"
INPUT_JSON="$2"

if [ "$TOOL_NAME" = "Write" ]; then
  FILE_PATH=$(echo "$INPUT_JSON" | jq -r '.file_path')
  
  # 检查是否尝试写入系统目录
  if echo "$FILE_PATH" | grep -q "^/etc\|^/usr/bin"; then
    echo '{"denied": true, "reason": "Cannot write to system directories"}'
    exit 1
  fi
fi

echo '{"allowed": true}'
exit 0
```

### 验证工具（来自 hook-development）

```bash
# 验证 hooks.json 结构
./validate-hook-schema.sh hooks/hooks.json

# 测试 Hook 执行
./test-hook.sh my-hook.sh test-input.json

# 代码风格检查
./hook-linter.sh my-hook.sh
```

---

## 🚀 快速入门：从安装到第一个插件

### 第一步：安装插件

在 Claude Code 中使用斜杠命令安装：

```bash
/plugin install plugin-dev@claude-plugins-official
```

或者通过菜单：`/plugin > Discover` 浏览插件市场

### 第二步：创建一个插件

使用 plugin-dev 提供的引导工作流：

```bash
/plugin-dev:create-plugin A plugin for managing database migrations
```

这会启动一个 8 阶段创建流程：

```
Discovery → Component Planning → Detailed Design →
Structure Creation → Component Implementation →
Validation → Testing → Documentation
```

### 第三步：理解最小插件结构

```bash
mkdir my-first-plugin
cd my-first-plugin
mkdir -p .claude-plugin

# 创建 plugin.json
cat > .claude-plugin/plugin.json << 'EOF'
{
  "name": "my-first-plugin",
  "description": "我的第一个 Claude Code 插件",
  "author": {
    "name": "Your Name",
    "email": "you@example.com"
  }
}
EOF

# 创建 README
cat > README.md << 'EOF'
# My First Plugin

一个简单的插件示例。

## 安装

/plugin install my-first-plugin@claude-plugins-official
EOF
```

### 第四步：添加一个 Skill

```bash
mkdir -p skills/hello-world
cat > skills/hello-world/SKILL.md << 'EOF'
---
name: hello-world
description: 当用户说 "hello" 或 "say hi" 时激活
version: 1.0.0
---

# Hello World Skill

这是一个简单的示例技能。

## 使用方法

当任务上下文包含 "hello" 相关的请求时，
此技能会自动激活并提供问候语生成能力。
EOF
```

### 第五步：添加一个命令

```bash
cat > skills/hello-command/SKILL.md << 'EOF'
---
name: hello-command
description: 生成问候语 /hello <name>
argument-hint: <名字>
allowed-tools: [Read]
---

# Hello Command

生成个性化的问候语。

## 用法

直接输入 `/hello <名字>` 即可生成问候语。
EOF
```

---

## 🔍 plugin-dev 深度解析

`plugin-dev` 是整个仓库的精华，它本身就是一个完整的插件开发框架。

### 七大技能详解

#### 1. hook-development（钩子开发）

**触发短语：** "create a hook", "add a PreToolUse hook", "validate tool use"

**核心能力：**
- Prompt-based hooks（推荐）：使用 LLM 做决策
- Command hooks：确定性验证逻辑
- 完整事件覆盖：PreToolUse、PostToolUse、Stop 等全部 9 种
- `${CLAUDE_PLUGIN_ROOT}` 可移植路径
- JSON Schema 输出格式

**资源统计：**
- Core SKILL.md：1,619 词
- 3 个示例钩子脚本
- 3 篇参考文档（patterns、migration、advanced）
- 3 个实用脚本（validate-hook-schema.sh、test-hook.sh、hook-linter.sh）

#### 2. mcp-integration（MCP 集成）

**触发短语：** "add MCP server", "integrate MCP", "configure .mcp.json"

**核心能力：**
- .mcp.json vs plugin.json 配置方式
- stdio/SSE/HTTP/WebSocket 四种服务器类型
- OAuth 认证模式
- MCP 工具在命令/Agent 中的使用
- 环境变量扩展（${CLAUDE_PLUGIN_ROOT}、用户变量）

**资源统计：**
- Core SKILL.md：1,666 词
- 3 个配置示例（stdio、SSE、HTTP）
- 3 篇参考文档（server-types ~3,200w、authentication ~2,800w、tool-usage ~2,600w）

#### 3. plugin-structure（插件结构）

**触发短语：** "plugin structure", "plugin.json manifest", "auto-discovery"

**核心能力：**
- 标准目录结构和自动发现机制
- plugin.json 清单格式和全部字段
- 组件组织（commands、agents、skills、hooks）
- ${CLAUDE_PLUGIN_ROOT} 全局使用
- 文件命名规范

**资源统计：**
- Core SKILL.md：1,619 词
- 3 个示例结构（minimal、standard、advanced）
- 2 篇参考文档（component-patterns、manifest-reference）

#### 4. plugin-settings（插件配置）

**触发短语：** "plugin settings", "store plugin configuration", ".local.md files"

**核心能力：**
- `.claude/plugin-name.local.md` 配置模式
- YAML frontmatter + markdown body 结构
- Bash 解析技术（sed、awk、grep）
- 临时激活钩子（flag 文件 + 快速退出）
- 真实案例：multi-agent-swarm 和 ralph-loop 插件

#### 5. command-development（命令开发）

**触发短语：** "create a slash command", "add a command", "command frontmatter"

**核心能力：**
- 斜杠命令格式和 markdown 结构
- YAML frontmatter 字段（description、argument-hint、allowed-tools）
- 动态参数和文件引用
- Bash 执行上下文
- 命令组织和命名空间

#### 6. agent-development（Agent 开发）

**触发短语：** "create an agent", "add an agent", "agent frontmatter"

**核心能力：**
- YAML frontmatter + system prompt 结构
- 全部前端字段（name、description、model、color、tools）
- `<example>` 块描述格式
- System prompt 设计模式（analysis、generation、validation、orchestration）
- AI 辅助 Agent 生成
- 完整生产级示例

#### 7. skill-development（Skill 开发）

**触发短语：** "create a skill", "add a skill", "write a new skill"

**核心能力：**
- SKILL.md YAML frontmatter 格式
- 渐进式披露原则（metadata → SKILL.md → resources）
- 强触发描述（具体短语）
- 写作风格（祈使句/不定式、第三人称）
- 资源组织（references/、examples/、scripts/）
- 基于 skill-creator 方法论

---

## 🔄 MCP Server 集成模式

### 场景 1：本地 stdio MCP Server

适用于本地工具和服务：

```json
{
  "filesystem": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "./workspace"]
  }
}
```

### 场景 2：远程 SSE MCP Server（OAuth）

适用于需要认证的第三方服务：

```json
{
  "asana": {
    "type": "sse",
    "url": "https://mcp.asana.com/sse"
  }
}
```

### 场景 3：HTTP REST API

适用于标准 REST API：

```json
{
  "github": {
    "type": "http",
    "url": "https://api.githubcopilot.com/mcp/",
    "headers": {
      "Authorization": "Bearer ${GITHUB_PERSONAL_ACCESS_TOKEN}"
    }
  }
}
```

---

## 📊 与同类项目对比

| 特性 | claude-plugins-official | VS Code Marketplace | npm |
|------|------------------------|---------------------|-----|
| **维护方** | Anthropic 官方 | Microsoft | npm team |
| **插件类型** | AI 助手扩展 | IDE 扩展 | Node.js 包 |
| **核心抽象** | Skill/Agent/Command/Hook | Extension | Package |
| **协议** | Claude Code 原生 + MCP | VS Code API | CommonJS |
| **认证** | OAuth/Bearer Token | 微软账号 | Token |
| **分发方式** | `/plugin install` | UI 安装 | CLI 安装 |

---

## 🎯 最佳实践

### ✅ 安全优先

```bash
# 1. 始终验证 Hook 输入
./validate-hook-schema.sh hooks/hooks.json

# 2. 使用环境变量存储凭证
# ❌ 错误：直接写死 token
# ✅ 正确：使用 ${GITHUB_TOKEN}

# 3. HTTPS/WSS 优先
# MCP Server 必须使用加密连接
```

### ✅ 可移植性

```bash
# ❌ 错误：硬编码绝对路径
/Users/name/project/

# ✅ 正确：使用环境变量
${CLAUDE_PLUGIN_ROOT}
./relative/path/
${HOME}/config/
```

### ✅ 测试验证

```bash
# 1. 本地测试插件
cc --plugin-dir /path/to/your-plugin

# 2. 验证配置
./validate-hook-schema.sh hooks/hooks.json
./validate-agent.sh agents/my-agent.yaml

# 3. Debug 模式
claude --debug
```

---

## 🚦 总结与学习路径

### 新手路线（Week 1）

```
1. 安装 plugin-dev：/plugin install plugin-dev@claude-plugins-official
2. 阅读 plugin-structure 理解插件架构
3. 阅读 command-development 创建第一个斜杠命令
4. 阅读 skill-development 创建第一个 Skill
```

### 进阶路线（Week 2-3）

```
1. 阅读 mcp-integration 集成外部服务
2. 阅读 hook-development 实现事件自动化
3. 阅读 agent-development 创建自主 Agent
4. 阅读 plugin-settings 实现配置管理
```

### 专家路线（Month 2+）

```
1. 深入研究 MCP Server 开发（mcp-server-dev）
2. 构建生产级插件并提交到外部插件市场
3. 贡献 plugin-dev 本身的改进
4. 探索多 Agent 协作模式
```

---

## 📚 官方资源

- **官方文档：** https://code.claude.com/docs/en/plugins
- **仓库地址：** https://github.com/anthropics/claude-plugins-official
- **插件提交：** https://clau.de/plugin-directory-submission
- **示例插件：** `/plugins/example-plugin` 在仓库中

---

> 🦞 **钳岳星君注：** Claude Code 的插件系统是目前 AI 编程助手领域最完善的扩展机制。相比 VS Code 的插件系统，它更注重 AI 原生能力的封装（Skill/Agent/Hook），而非简单的功能追加。如果你想深度定制 Claude Code 的行为，从 `plugin-dev` 入手是最快路径。