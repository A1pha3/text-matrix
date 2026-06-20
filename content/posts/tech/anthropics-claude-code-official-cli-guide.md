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

Claude Code 是 Anthropic 官方推出的终端编程助手，基于 Claude Sonnet 模型工作。它是一个在终端里运行的独立 CLI 工具，不是 IDE 插件，也不是 Web 界面——打开终端，敲一行命令，就能让 AI 帮你读代码、改文件、跑测试、写提交信息。

相比在 IDE 里装插件，CLI 方式的好处是**不受编辑器限制**：Vim、Emacs、nano、ssh 远程服务器，只要终端能跑，就能用 Claude Code。

这篇文章覆盖从安装到精通的全部关键路径：安装配置、核心命令、自定义选项、Skill 扩展生态、MCP 协议集成，以及日常高频场景的操作指南。

## 学习目标

读完后你能：

- 在 macOS / Linux / WSL2 环境完成 Claude Code 的安装、API Key 配置和首次启动验证
- 用多轮对话完成读文件、改文件、跑测试、写提交信息四类高频操作，并理解每步的变更确认机制
- 通过 `CLAUDE.md` 和 `.claude.json` 给项目定制 AI 行为，区分全局配置与项目级覆盖的优先级
- 用 Skill 扩展机制把重复工作流固化成可复用命令，并能识别第三方 Skill 的安装路径
- 通过 MCP 协议把外部工具（文件系统、Git、数据库）接入 Claude Code，并理解工具注册后的调用方式

## 目录

- [一、项目定位与能力边界](#一项目定位与能力边界)
- [二、安装与首次启动](#二安装与首次启动)
- [三、核心用法](#三核心用法)
- [四、自定义与配置](#四自定义与配置)
- [五、Skill 扩展系统](#五skill-扩展系统)
- [六、MCP 协议集成](#六mcp-协议集成)
- [七、高频场景操作指南](#七高频场景操作指南)
- [八、常见问题与错误排查](#八常见问题与错误排查)
- [九、适用边界与决策建议](#九适用边界与决策建议)
- [十、自测题](#十自测题)
- [十一、进阶路径](#十一进阶路径)
- [十二、参考资源](#十二参考资源)

---

## 一、项目定位与能力边界

Claude Code 解决的是**在真实代码库里完成多步任务**的问题，不是"帮我想算法"这种单点问题。它把读文件、改文件、执行命令、Git 操作串成一条可观测的工作流，并在每一步保留变更记录，让人类可以中途审查、纠正或终止。

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

### 1. 系统要求

- macOS、Linux 或 Windows（通过 WSL2）
- Node.js 18+（用于运行 claude 命令）
- Anthropic API Key（支持 Claude API 的任意 key，包括兼容提供商）

### 2. 安装命令

通过 npm 全局安装：

```bash
npm install -g @anthropic-ai/claude-code
```

安装完成后验证：

```bash
claude --version
```

### 3. 配置 API Key

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

### 4. 使用兼容提供商

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

### 1. 启动与退出

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

### 2. 在项目里工作

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

### 3. CLAUDE.md：项目级行为定制

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

### 4. 多轮对话的典型工作流

```text
进入项目
$ cd ~/projects/my-app
$ claude

第一轮：描述任务
> 把登录页从用户名密码改成邮箱登录

Claude 会读文件、分析改动点、给你方案
你可以审查方案，然后确认或修改

第二轮：CLAUDE.md 里没覆盖的边界情况
> 对了，登录错误信息要区分"用户不存在"和"密码错误"
> 用户不存在返回"该邮箱未注册"，密码错误返回"密码不正确"

第三轮：执行和验证
> 运行一下看看有没有问题
```

---

## 四、自定义与配置

### 1. 全局配置文件

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

### 2. 项目级配置

在项目根目录放 `.claude.json`，可以覆盖全局配置：

```json
{
  "max_tokens": 16384,
  "temperature": 0.7
}
```

### 3. 模型选择

Claude Code 默认使用 `claude-sonnet-4`，也可以在配置里指定：

| 模型 | 适用场景 |
|------|----------|
| `claude-sonnet-4-20250514` | 日常编程任务（默认） |
| `claude-opus-4-20250514` | 复杂架构分析、超大代码库 |
| `claude-haiku-4-20250514` | 简单、快速的单轮任务 |

### 4. Permission System

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

权限分三类：`Read`（读文件）、`Edit`（改文件）、`Bash`（执行命令）。默认全部开启，按需收紧。`Bash` 类权限的破坏性远大于读写文件——`rm -rf`、`git push --force`、`curl | sh` 都可能造成不可逆后果，所以在生产项目里建议把 `Bash` 显式收紧到白名单命令。

---

## 五、Skill 扩展系统

Skill 是 Claude Code 的命令行扩展机制，用 `claude` 开头的一系列命令短语调用预定义的自动化工作流。

### 1. 内置 Skill

Claude Code 内置了若干常用 Skill，按 `claude` 前缀调用：

| Skill 命令 | 作用 |
|-----------|------|
| `claude /skills` | 列出当前可用的所有 Skill |
| `claude /skill install <name>` | 安装一个 Skill |
| `claude /skill list` | 查看已安装的 Skill |
| `claude /skill search <query>` | 在 Skill 市场搜索 |

> 注：上述命令格式以官方文档为准，不同版本可能存在差异。Claude Code 还在快速迭代，斜杠命令的具体名称和参数请以 [anthropics/claude-code](https://github.com/anthropics/claude-code) 仓库的最新 README 和 Changelog 为准。

### 2. 安装第三方 Skill

通过 `/plugin marketplace add` 安装：

```bash
claude
/plugin marketplace add owner/repo-name
/plugin install skill-name@version
```

> 注：`/plugin marketplace add` 与 `/plugin install` 是否在当前版本可用，以官方文档为准。社区也有手动克隆到 `~/.claude/skills/` 的安装方式，效果等价。

### 3. 常用 Skill 推荐

| Skill 名称 | 功能 |
|-----------|------|
| `claude-code-harness` | 给 Claude Code 加一套"写 Spec → 实施 → 验证 → Review → 打包证据"的交付流程 |
| `claude-code-skills` | 18 个官方 AI 技能，覆盖全栈开发常见场景 |

### 4. 自定义 Skill

Skill 说到底是一个包含 `instructions.md` 和可选配置文件的目录，安装后放在 `~/.claude/skills/` 下。

一个最小 Skill 的结构：

```text
my-skill/
├── instructions.md      # Skill 的行为指令
└── config.json          # 可选：配置项
```

`instructions.md` 在 Skill 被调用时作为系统级指令注入对话，告诉 AI 这个 Skill 做什么、按什么步骤做、产出什么格式。它的作用类似于 `CLAUDE.md`，但作用域限定在 Skill 调用期间。

---

## 六、MCP 协议集成

MCP（Model Context Protocol）是 Anthropic 提出的标准协议，用于让 AI 模型连接外部工具和数据源。Claude Code 原生支持 MCP。

### 1. MCP Server 是什么

一个 MCP Server 是一个独立的进程，通过标准协议暴露一组工具（tools）、资源（resources）和提示（prompts）给 Claude Code 使用。

常见的 MCP Server：

- **文件系统**：`mcp/filesystem`——直接操作本地文件
- **Git**：`mcp/git`——Git 操作
- **数据库**：`mcp/postgres`、`mcp/mysql`——数据库查询
- **浏览器自动化**：`mcp/browser`——网页抓取和控制

### 2. 在 Claude Code 里配置 MCP

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

配置完成后重启 Claude Code，MCP Server 会自动启动并注册工具。重启是必须的——MCP Server 是独立进程，Claude Code 启动时按配置拉起这些进程并建立通信通道，运行中的会话不会自动感知新增的 Server 配置。

### 3. 使用 MCP 工具

配置完成后，MCP Server 暴露的工具会直接出现在 Claude Code 的可用工具列表里，你可以在对话中直接调用：

```bash
claude
> 用 Git MCP 查看 main 分支最近 5 次提交
```

AI 会根据任务需要自动选择调用哪个 MCP 工具，用户不需要写特殊语法。

---

## 七、高频场景操作指南

### 1. 大型代码库快速上手

第一次进一个大项目，建议先花几分钟让 Claude 了解项目结构：

```bash
claude
> 读取项目的 README.md，了解这个项目是做什么的
> 查看 package.json 或 requirements.txt，了解依赖和技术栈
> 列出 src/ 或 lib/ 目录下的主要模块
```

然后问：

```text
> 这个项目的核心架构是怎样的？帮我梳理一下主要模块和它们的关系
```

### 2. Bug 修复工作流

```bash
claude
> Bug：在用户上传大于 10MB 的文件时没有报错，日志里也没有任何记录
> 先帮我看一下错误出现在哪个环节
```

Claude 会尝试定位问题，给出分析后，你可以确认方案再让它执行修复。

### 3. Code Review

```bash
claude
> Review 一下最近这次提交涉及的改动，重点关注测试覆盖率和潜在的边界情况
```

### 4. 生成测试

```bash
claude
> 为 src/utils/format.ts 里的所有函数补充单元测试，使用 Vitest 框架
```

### 5. 重构辅助

```bash
claude
> 把 src/components/ 下的所有 class 组件改成函数组件，并同步更新相关的 import
```

---

## 八、常见问题与错误排查

### 1. API 消耗如何控制

Claude Code 每次对话都会消耗 Token，主要来自：

- 项目文件内容的上下文注入
- 对话历史
- 模型输出的 completion

优化方式：

1. 在 `CLAUDE.md` 里明确说明哪些文件不需要关心，减少无关文件的读取
2. 使用 `.claudeignore` 文件（类似 `.gitignore`）排除不相关目录
3. 复杂任务分段做，不要在一个对话里塞太多逻辑

### 2. 网络请求失败

Claude Code 默认连 Anthropic 官方 API，如果遇到网络问题：

```bash
export ANTHROPIC_API_BASE="https://api.anthropic.com"  # 官方
# 或者换兼容提供商
export ANTHROPIC_API_BASE="https://openrouter.ai/api/v1"
```

### 3. 如何获取帮助

```bash
claude --help
```

或者在对话中：

```bash
> /help
```

### 4. 与 IDE 插件的分工

如果你的编辑器是 VS Code、JetBrains 系列，Anthropic 也提供了对应的 IDE 插件。IDE 插件的优势是深度集成（内联补全、悬停文档），Claude Code CLI 的优势是**跨编辑器、跨终端、适合远程服务器**。两者可以互补使用。

### 5. 常见错误与排查

| 错误现象 | 可能原因 | 排查方向 |
|---------|---------|---------|
| 启动报 `ANTHROPIC_API_KEY not set` | 环境变量未配置或未生效 | 检查 shell 配置文件（`~/.zshrc` / `~/.bashrc`）是否导出该变量，重启终端 |
| 命令执行被拒 `Permission denied` | 权限系统拦截 | 检查 `.claude.json` 的 `permissions.deny` 列表是否包含该操作 |
| 对话上下文丢失 | 单次会话超出 Token 上限 | 用 `/clear` 清理历史，或把任务拆成多个会话 |
| MCP Server 不生效 | 配置文件路径错误或 JSON 格式错误 | 用 `claude --help` 查看 MCP 诊断命令，确认 Server 是否注册成功 |
| 模型响应明显变慢 | 兼容提供商限流或网络抖动 | 切回官方 API 验证，或检查提供商状态页 |
| `CLAUDE.md` 没生效 | 文件不在项目根目录或命名错误 | 确认文件在 `git rev-parse --show-toplevel` 输出的目录下，文件名大小写正确 |

---

## 九、适用边界与决策建议

Claude Code 最适合以下场景：

- **日常 CLI 编程辅助**：终端常开，随时丢一个任务进去
- **跨编辑器场景**：不论用什么编辑器，统一的编程入口
- **远程服务器开发**：ssh 进去一样用 Claude Code
- **Skill 自动化**：把重复的工作流固化成 Skill，一键调用

不太适合的场景：

- 需要毫秒级响应的内联代码补全（用 IDE 插件更合适）
- 完全不想看代码就让 AI 全自动跑（Claude Code 设计上保留人类监督节点）
- 受限网络环境无法访问外部 API

### 采用顺序

1. **第一步：跑通安装和首次对话**。完成 `npm install -g @anthropic-ai/claude-code` 和 API Key 配置，在任意项目里启动 `claude`，让它读一个文件并回答一个问题。这一步只验证环境，环境不通后面所有调试都是白费。
2. **第二步：写 `CLAUDE.md`**。给主项目写一份项目级指令，把技术栈、目录规范、Git 提交格式告诉 Claude。这一步让后续每次对话都带着项目上下文，省去反复解释。
3. **第三步：跑通一个完整工作流**。挑一个真实任务（修 Bug、加测试、重构），让 Claude 走完"读文件 → 改文件 → 跑测试 → 写提交信息"全流程，确认每步的变更确认机制符合你的预期。
4. **第四步：按需引入 MCP**。当 Claude 自带的文件、Bash、Git 能力不够时（比如要查数据库），再引入对应的 MCP Server。不要一开始就堆 MCP，先确认基础工作流稳定。
5. **第五步：固化 Skill**。当你发现自己在重复给 Claude 同样的指令序列时，把它写成自定义 Skill，下次一行命令调用。Skill 的价值不在省一次输入，而在于把团队规范固化成 AI 行为。

---

## 十、自测题

1. Claude Code 的项目级配置文件和全局配置文件分别是什么？项目级配置如何覆盖全局配置？
2. `CLAUDE.md` 和 `.claude.json` 的作用有什么区别？分别在什么场景下使用？
3. Permission System 中 `Read` / `Edit` / `Bash` 三类权限分别控制什么？为什么生产项目里建议把 `Bash` 显式收紧？
4. MCP Server 注册的工具，在 Claude Code 里如何被调用？配置完成后为什么需要重启？
5. 自定义 Skill 的最小目录结构是什么？`instructions.md` 在 Skill 调用时起什么作用？

### 参考答案

<details>
<summary>第 1 题参考答案</summary>

全局配置文件是 `~/.claude.json`，项目级配置文件是项目根目录下的 `.claude.json`。Claude Code 启动时先加载全局配置，再加载项目级配置；同名键以项目级为准，因此项目级配置可以覆盖全局配置中的 `model`、`max_tokens`、`temperature` 等字段，但不会清空全局配置里项目级未指定的字段。
</details>

<details>
<summary>第 2 题参考答案</summary>

`CLAUDE.md` 是给 AI 看的项目上下文指令，用自然语言写技术栈、目录规范、Git 规范、注意事项，启动时作为系统级上下文注入每次对话，影响 AI 的决策和行为；`.claude.json` 是结构化的运行时配置，控制模型选择、Token 上限、权限、MCP Server 等可执行参数。前者管"AI 应该怎么做事"，后者管"AI 用什么工具和参数做事"。
</details>

<details>
<summary>第 3 题参考答案</summary>

`Read` 控制读文件、`Edit` 控制改文件、`Bash` 控制执行 shell 命令。生产项目里建议把 `Bash` 显式收紧是因为 shell 命令的破坏性远大于读写文件——`rm -rf`、`git push --force`、`curl | sh` 都可能造成不可逆后果。Permission System 的设计是把"读"和"写"分开，再把"写"里破坏性最强的 shell 执行单独管控，让用户能按风险等级收紧权限。常见做法是用 `permissions.deny` 把生产环境路径、密钥文件、`git push` 类操作显式禁掉。
</details>

<details>
<summary>第 4 题参考答案</summary>

MCP Server 注册的工具会出现在 Claude Code 的可用工具列表里，AI 在对话中根据任务需要自动调用，用户不需要写特殊语法。配置完成后需要重启是因为 MCP Server 是独立进程，Claude Code 启动时按配置拉起这些进程并建立通信通道，运行中的会话不会自动感知新增的 Server 配置。
</details>

<details>
<summary>第 5 题参考答案</summary>

最小目录结构是一个包含 `instructions.md` 的目录，可选 `config.json`：

```text
my-skill/
├── instructions.md      # Skill 的行为指令
└── config.json          # 可选：配置项
```

`instructions.md` 在 Skill 被调用时作为系统级指令注入对话，告诉 AI 这个 Skill 做什么、按什么步骤做、产出什么格式。它的作用类似于 `CLAUDE.md`，但作用域限定在 Skill 调用期间。
</details>

---

## 十一、进阶路径

- **写自定义 Skill 沉淀团队工作流**。把团队里反复出现的"读需求 → 改代码 → 跑测试 → 写提交"流程写成 Skill，统一产出格式和检查项。Skill 的价值不在省一次输入，而在于把团队规范固化成 AI 行为，新人入职后直接调用就能按规范产出。
- **用 MCP 接入内部工具链**。把内部 API 网关、监控平台、日志系统封装成 MCP Server，让 Claude Code 能直接查线上日志、调内部接口。这一步把 Claude Code 从"代码助手"扩展成"工程助手"，关键是给每个 MCP Server 配好权限边界，避免 AI 误操作线上资源。
- **搭权限分层配置**。在敏感项目里用 `.claude.json` 的 `permissions.deny` 把生产环境路径、密钥文件、`git push` 类操作显式禁掉，再让 `CLAUDE.md` 说明哪些操作必须人工确认。配置成本不高，但能避免 AI 误操作造成事故。
- **结合 CI 做 PR Review**。在 CI 里跑 Claude Code 对 PR 改动做自动 Review，把结果作为评论贴回 PR。关键是限定权限（只读 + 评论）和限定上下文（只看 diff 和相关文件），避免 AI 跑偏或越权改代码。
- **跟踪官方更新**。Claude Code 还在快速迭代，命令、Skill 机制、MCP 支持都可能变化。订阅 [anthropics/claude-code](https://github.com/anthropics/claude-code) 的 Release，遇到行为变化先查 Changelog，再决定是否升级。

---

## 十二、参考资源

- GitHub 仓库：[https://github.com/anthropics/claude-code](https://github.com/anthropics/claude-code)
- 官方文档：Anthropic 官网 Claude Code 页面
- Skill 市场：`/plugin marketplace` 命令访问（以官方文档为准）
- MCP 协议规范：[https://modelcontextprotocol.io](https://modelcontextprotocol.io)

---

*本文基于 GitHub 仓库 `anthropics/claude-code` 的公开信息编写。安装命令、配置项和 API 端点以官方最新版本为准。*
