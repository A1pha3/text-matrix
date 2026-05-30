---
title: "Anthropic Claude Code：官方AI编程CLI从入门到精通完全指南"
date: "2026-05-30T15:05:00+08:00"
slug: "anthropics-claude-code-official-cli-guide"
description: "Claude Code是Anthropic官方终端AI编程助手，基于Claude Sonnet工作，支持文件编辑、Git操作、多轮对话、Skill扩展和MCP协议，涵盖安装配置、核心用法和自定义选项。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Anthropic", "AI编程", "CLI", "MCP"]
---

# Anthropic Claude Code：官方 AI 编程 CLI 从入门到精通完全指南

Claude Code 是 Anthropic 官方推出的终端编程助手，基于 Claude Sonnet 模型工作。它不是 IDE 插件，不是 Web 界面，而是一个在终端里运行的独立 CLI 工具——打开终端，敲一行命令，就能让 AI 帮你读代码、改文件、跑测试、写提交信息。

相比在 IDE 里装插件，CLI 方式的好处是**不受编辑器限制**：Vim、Emacs、nano、ssh 远程服务器，只要终端能跑，就能用 Claude Code。

这篇文章覆盖从安装到精通的全部关键路径：安装配置、核心命令、自定义选项、Skill 扩展生态、MCP 协议集成，以及日常高频场景的操作指南。

---

## 一、项目定位与能力边界

Claude Code 解决的不是"帮我想算法"这种单点问题，而是**在真实代码库里完成多步任务**的问题。它把读文件、改文件、执行命令、Git 操作串成一条可观测的工作流，并在每一步保留变更记录，让人类可以中途审查、纠正或终止。

核心能力一览：

- **多轮对话式编程**：在终端里和 Claude 进行多轮对话，AI 记得上下文
- **文件读写与编辑**：读文件、改文件、创建文件，支持 glob 模式匹配
- **Bash 命令执行**：直接在终端里跑 shell 命令，看结果再决定下一步
- **Git 操作**：自动写提交信息、创建分支、查看 diff
- **Skill 扩展系统**：用 `claude` 开头的命令短语调用预定义的自动化工作流
- **MCP 协议集成**：通过 Model Context Protocol 连接外部工具和数据源
- **CLAUDE.md 项目级指令**：在项目根目录放 `CLAUDE.md`，给项目定制 AI 的行为

它的定位介于"单次问答"和"全自动驾驶"之间：AI 可以在你的监督下执行一系列操作，但每一步的变更会展示给你，确认后才真正落盘。

---

## 二、安装与首次启动

### 2.1 系统要求

- macOS、Linux 或 Windows（通过 WSL2）
- Node.js 18+（用于运行 claude 命令）
- Anthropic API Key（支持 Claude API 的任意 key，包括兼容提供商）

### 2.2 安装命令

通过 npm 全局安装：

```bash
npm install -g @anthropic-ai/claude-code
```

安装完成后验证：

```bash
claude --version
```

### 2.3 配置 API Key

Claude Code 支持多种环境变量配置方式。

**方式一：直接设置环境变量**

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

**方式二：通过配置文件**

在 `~/.claude.json`（全局）或项目根目录的 `.claude.json`（项目级）中配置：

```json
{
  "api_key": "sk-ant-api03-..."
}
```

**方式三：通过 `claude` 命令交互配置**

首次运行 `claude` 时，会引导你输入 API Key，并保存在 `~/.claude.json`。

### 2.4 使用兼容提供商

如果不想直接消耗 Anthropic API 额度，可以使用兼容提供商。需要设置 API Base URL 和对应的 Key：

```bash
export ANTHROPIC_API_KEY="your-provider-key"
export ANTHROPIC_API_BASE="https://openrouter.ai/api/v1"  # 或其他兼容端点
```

常见兼容提供商：

| 提供商 | API Base | 特点 |
|--------|----------|------|
| OpenRouter | `https://openrouter.ai/api/v1` | 大量免费模型 |
| NVIDIA NIM | `https://integrate.api.nvidia.com/v1` | 40 req/min 免费 |
| DeepSeek | `https://api.deepseek.com/v1` | 价格低 |
| 本地 Ollama | `http://localhost:11434/v1` | 完全免费，本地运行 |

---

## 三、核心用法

### 3.1 启动与退出

进入一个代码目录，直接启动：

```bash
cd ~/projects/my-app
claude
```

Claude Code 会启动一个交互式对话界面，底部有提示符等待你的输入。

退出方式：

```bash
/exit
```

或直接按 `Ctrl+C`。

### 3.2 在项目里工作

**读文件**

```bash
claude
> 读取 src/app.tsx 的内容
```

**改文件**

```bash
claude
> 在 src/app.tsx 里的 handleClick 函数后添加一个日志语句
```

**执行命令**

```bash
claude
> 运行 npm test 看看测试是否通过
```

**Git 操作**

```bash
claude
> 查看当前的 git diff
> 提交这次修改，提交信息写"更新用户认证逻辑"
> 创建一个新分支叫 feature/payment
```

### 3.3 CLAUDE.md：项目级行为定制

在项目根目录创建 `CLAUDE.md`，内容是给 Claude 的项目级上下文指令。例如：

```markdown
# CLAUDE.md

## 项目概述
这是一个使用 Next.js 14 + Tailwind CSS 构建的博客应用。

## 技术栈
- 框架：Next.js 14（App Router）
- 样式：Tailwind CSS
- 数据库：PostgreSQL + Prisma ORM

## 代码规范
- 组件放在 `src/components/` 目录
- API 路由放在 `src/app/api/` 目录
- 样式优先使用 Tailwind 工具类，特殊情况才写自定义 CSS
- 禁止在组件里直接写内联样式

## Git 规范
- 提交信息用中文，格式为"<类型>: <描述>"
- 类型包括：feat, fix, docs, style, refactor, test, chore
```

Claude Code 启动时会自动读取项目根目录的 `CLAUDE.md`，把它的内容作为系统级上下文注入每次对话。

### 3.4 多轮对话的典型工作流

```bash
# 进入项目
cd ~/projects/my-app
claude

# 第一轮：描述任务
> 把登录页从用户名密码改成邮箱登录

# Claude 会读文件、分析改动点、给你方案
# 你可以审查方案，然后确认或修改

# 第二轮：CLAUDE.md 里没覆盖的边界情况
> 对了，登录错误信息要区分"用户不存在"和"密码错误"
> 用户不存在返回"该邮箱未注册"，密码错误返回"密码不正确"

# 第三轮：执行和验证
> 运行一下看看有没有问题
```

---

## 四、自定义与配置

### 4.1 全局配置文件

`~/.claude.json` 控制 Claude Code 的全局行为：

```json
{
  "api_key": "sk-ant-api03-...",
  "model": "claude-sonnet-4-20250514",
  "max_tokens": 8192,
  "temperature": 1,
  "api_base": "https://api.anthropic.com"
}
```

### 4.2 项目级配置

在项目根目录放 `.claude.json`，可以覆盖全局配置：

```json
{
  "max_tokens": 16384,
  "temperature": 0.7
}
```

### 4.3 模型选择

Claude Code 默认使用 `claude-sonnet-4`，也可以在配置里指定：

| 模型 | 适用场景 |
|------|----------|
| `claude-sonnet-4-20250514` | 日常编程任务（默认） |
| `claude-opus-4-20250514` | 复杂架构分析、超大代码库 |
| `claude-haiku-4-20250514` | 简单、快速的单轮任务 |

### 4.4 Permission System

Claude Code 有内置的权限系统，控制 AI 可以执行哪些操作：

```json
{
  "permissions": {
    "allow": ["Read", "Edit", "Bash"],
    "deny": ["Bash:rm -rf /", "Edit:/etc/*"]
  }
}
```

也可以通过环境变量控制：

```bash
export CLAUDE_PERMISSIONS="read,edit,bash"
```

权限分三类：`Read`（读文件）、`Edit`（改文件）、`Bash`（执行命令）。默认全部开启，按需收紧。

---

## 五、Skill 扩展系统

Skill 是 Claude Code 的命令行扩展机制，用 `claude` 开头的一系列命令短语调用预定义的自动化工作流。

### 5.1 内置 Skill

Claude Code 内置了若干常用 Skill，按 `claude` 前缀调用：

| Skill 命令 | 作用 |
|-----------|------|
| `claude /skills` | 列出当前可用的所有 Skill |
| `claude /skill install <name>` | 安装一个 Skill |
| `claude /skill list` | 查看已安装的 Skill |
| `claude /skill search <query>` | 在 Skill 市场搜索 |

### 5.2 安装第三方 Skill

通过 `/plugin marketplace add` 安装：

```bash
claude
/plugin marketplace add owner/repo-name
/plugin install skill-name@version
```

### 5.3 常用 Skill 推荐

| Skill 名称 | 功能 |
|-----------|------|
| `claude-code-harness` | 给 Claude Code 加一套"写 Spec → 实施 → 验证 → Review → 打包证据"的交付流程 |
| `claude-code-skills` | 18 个官方 AI 技能，覆盖全栈开发常见场景 |

### 5.4 自定义 Skill

Skill 本质上是一个包含 `instructions.md` 和可选配置文件的目录，安装后放在 `~/.claude/skills/` 下。

一个最小 Skill 的结构：

```
my-skill/
├── instructions.md      # Skill 的行为指令
└── config.json          # 可选：配置项
```

---

## 六、MCP 协议集成

MCP（Model Context Protocol）是 Anthropic 提出的标准协议，用于让 AI 模型连接外部工具和数据源。Claude Code 原生支持 MCP。

### 6.1 MCP Server 是什么

一个 MCP Server 是一个独立的进程，通过标准协议暴露一组工具（tools）、资源（resources）和提示（prompts）给 Claude Code 使用。

常见的 MCP Server：

- **文件系统**：`mcp/filesystem`——直接操作本地文件
- **Git**：`mcp/git`——Git 操作
- **数据库**：`mcp/postgres`、`mcp/mysql`——数据库查询
- **浏览器自动化**：`mcp/browser`——网页抓取和控制

### 6.2 在 Claude Code 里配置 MCP

在 `~/.claude.json` 或项目级 `.claude.json` 中配置：

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"]
    },
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git"]
    }
  }
}
```

配置完成后重启 Claude Code，MCP Server 会自动启动并注册工具。

### 6.3 使用 MCP 工具

配置完成后，MCP Server 暴露的工具会直接出现在 Claude Code 的可用工具列表里，你可以在对话中直接调用：

```bash
claude
> 用 Git MCP 查看 main 分支最近 5 次提交
```

---

## 七、高频场景操作指南

### 7.1 大型代码库快速上手

第一次进一个大项目，建议先花几分钟让 Claude 了解项目结构：

```bash
claude
> 读取项目的 README.md，了解这个项目是做什么的
> 查看 package.json 或 requirements.txt，了解依赖和技术栈
> 列出 src/ 或 lib/ 目录下的主要模块
```

然后问：

```
> 这个项目的核心架构是怎样的？帮我梳理一下主要模块和它们的关系
```

### 7.2 Bug 修复工作流

```bash
claude
> Bug：在用户上传大于 10MB 的文件时没有报错，日志里也没有任何记录
> 先帮我看一下错误出现在哪个环节
```

Claude 会尝试定位问题，给出分析后，你可以确认方案再让它执行修复。

### 7.3 Code Review

```bash
claude
> Review 一下最近这次提交涉及的改动，重点关注测试覆盖率和潜在的边界情况
```

### 7.4 生成测试

```bash
claude
> 为 src/utils/format.ts 里的所有函数补充单元测试，使用 Vitest 框架
```

### 7.5 重构辅助

```bash
claude
> 把 src/components/ 下的所有 class 组件改成函数组件，并同步更新相关的 import
```

---

## 八、常见问题与边界

### 8.1 API 消耗如何控制

Claude Code 每次对话都会消耗 Token，主要来自：

- 项目文件内容的上下文注入
- 对话历史
- 模型输出的 completion

优化方式：

1. 在 `CLAUDE.md` 里明确说明哪些文件不需要关心，减少无关文件的读取
2. 使用 `.claudeignore` 文件（类似 `.gitignore`）排除不相关目录
3. 复杂任务分段做，不要在一个对话里塞太多逻辑

### 8.2 网络请求失败

Claude Code 默认连 Anthropic 官方 API，如果遇到网络问题：

```bash
export ANTHROPIC_API_BASE="https://api.anthropic.com"  # 官方
# 或者换兼容提供商
export ANTHROPIC_API_BASE="https://openrouter.ai/api/v1"
```

### 8.3 如何获取帮助

```bash
claude --help
```

或者在对话中：

```bash
> /help
```

### 8.4 与 IDE 插件的分工

如果你的编辑器是 VS Code、JetBrains 系列，Anthropic 也提供了对应的 IDE 插件。IDE 插件的优势是深度集成（内联补全、悬停文档），Claude Code CLI 的优势是**跨编辑器、跨终端、适合远程服务器**。两者可以互补使用。

---

## 九、适用边界与决策建议

Claude Code 最适合以下场景：

- **日常 CLI 编程辅助**：终端常开，随时丢一个任务进去
- **跨编辑器场景**：不论用什么编辑器，统一的编程入口
- **远程服务器开发**：ssh 进去一样用 Claude Code
- ** Skill 自动化**：把重复的工作流固化成 Skill，一键调用

不太适合的场景：

- 需要毫秒级响应的内联代码补全（用 IDE 插件更合适）
- 完全不想看代码就让 AI 全自动跑（Claude Code 设计上保留人类监督节点）
- 受限网络环境无法访问外部 API

**采用建议**：如果你在本地或远程服务器上做开发，Claude Code CLI 值得作为日常伴侣配置起来。先从安装和一个简单任务开始，熟悉后再逐步扩展到 Skill 和 MCP 集成。

---

## 十、参考资源

- GitHub 仓库：[https://github.com/anthropics/claude-code](https://github.com/anthropics/claude-code)
- 官方文档：Anthropic 官网 Claude Code 页面
- Skill 市场：`/plugin marketplace` 命令访问
- MCP 协议规范：[https://modelcontextprotocol.io](https://modelcontextprotocol.io)

---

*本文基于 GitHub 仓库 `anthropics/claude-code` 的公开信息编写。安装命令、配置项和 API 端点以官方最新版本为准。*