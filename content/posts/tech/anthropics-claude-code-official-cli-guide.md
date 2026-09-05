---
title: "Anthropic Claude Code：官方AI编程CLI从入门到精通完全指南"
date: "2026-05-30T15:05:00+08:00"
slug: "anthropics-claude-code_official_cli_guide"
github_repo: "anthropics/claude-code"
description: "Claude Code是Anthropic官方终端AI编程助手，默认模型随账户类型而定（Pro/API账户为Sonnet，Max账户为Opus），支持文件编辑、Git操作、多轮对话、Skill扩展和MCP协议，涵盖安装配置、核心用法和自定义选项。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Anthropic", "AI 编程", "CLI", "MCP"]
---

# Anthropic Claude Code：官方 AI 编程 CLI 从入门到精通完全指南

Claude Code 是 Anthropic 官方推出的终端编程助手，默认基于 Claude Sonnet 模型工作，可在配置中切换到 Opus 或 Haiku。它是一个在终端里运行的独立 CLI 工具，覆盖 IDE 插件和 Web 界面之外的第三条路径——打开终端，敲一行命令，让 AI 帮你读代码、改文件、跑测试、写提交信息。

CLI 方式相比 IDE 插件的核心差异在**入口位置**：Vim、Emacs、nano、ssh 远程服务器，只要终端能跑，就能用 Claude Code。代价是没有内联补全和悬停文档这类深度集成能力，需要靠多轮对话驱动。

下面按从安装到精通的顺序展开：安装配置、核心命令、自定义选项、Skill 扩展系统、MCP 协议集成，以及日常高频场景的操作指南。

> **快速信息卡**（GitHub 指标持续变化，以仓库实时数据为准）
> - **Stars**: 约 14 万
> - **License**: 非标准开源许可（GitHub 未识别为 OSI 认证许可证，以仓库 LICENSE 为准）
> - **语言**: Python 为主（GitHub 语言统计；早期版本为 TypeScript）
> - **默认模型**: Sonnet（Pro / API 账户）或 Opus（Max 账户），可在对话中用 `/model` 切换

## 学习目标

读完后你能：

- 在 macOS / Linux / WSL2 环境完成 Claude Code 的安装、API Key 配置和首次启动验证
- 用多轮对话完成读文件、改文件、跑测试、写提交信息四类高频操作，并理解每步的变更确认机制
- 通过 `CLAUDE.md` 和 `settings.json` 给项目定制 AI 行为，区分各层配置的优先级与合并规则
- 用 Skill 扩展机制把重复工作流固化成可复用命令，并能识别第三方 Skill 的安装路径
- 通过 MCP 协议把外部工具（文件系统、Git、数据库）接入 Claude Code，并理解工具注册后的调用方式

## 系统总览：四条独立机制

Claude Code 的能力由四条相对独立的机制叠加而成，先理清边界，后面章节才不会混淆：

| 机制 | 控制什么 | 配置位置 | 谁来读 |
|------|---------|---------|--------|
| **CLI 本体** | 启动、对话、文件读写、Bash、Git | 命令行参数 | 用户 |
| **`settings.json`** | 模型、权限规则、环境变量、MCP Server 注册 | `~/.claude/settings.json`（用户级）、`.claude/settings.json`（项目级，随仓库共享）、`.claude/settings.local.json`（项目个人级，不入库） | Claude Code 启动时按优先级合并加载 |
| **`CLAUDE.md`** | 项目上下文、代码规范、Git 规范（自然语言） | 项目根目录 `CLAUDE.md` | 启动时作为系统级上下文注入每次对话 |
| **Skill / MCP** | 可复用工作流 / 外部工具接入 | `~/.claude/skills/`、`.claude/skills/`（Skill）；`claude mcp add` 写入 `.mcp.json` 或 `~/.claude.json`（MCP） | Skill 在调用时注入；MCP 在启动时拉起进程 |

四条机制的作用域不同：CLI 本体是运行时入口，`settings.json` 管可执行参数，`CLAUDE.md` 管 AI 的行为偏好，Skill 和 MCP 是扩展层。理解这个分工后，"该改哪个文件"就不再混淆。需要注意：`~/.claude.json` 是另一个文件，存的是会话历史和应用状态，不是用来配置模型或权限的。

## 目录

- [一、项目定位与能力边界](#一项目定位与能力边界)
- [二、安装与首次启动](#二安装与首次启动)
- [三、核心用法](#三核心用法)
- [四、自定义与配置](#四自定义与配置)
- [五、Skill 扩展系统](#五skill-扩展系统)
- [六、MCP 协议集成](#六mcp-协议集成)
- [七、任务流案例：一个 Bug 修复如何流过系统](#七任务流案例一个-bug-修复如何流过系统)
- [八、高频场景操作指南](#八高频场景操作指南)
- [九、常见问题与错误排查](#九常见问题与错误排查)
- [十、适用边界与决策建议](#十适用边界与决策建议)
- [十一、自测题](#十一自测题)
- [十二、进阶路径](#十二进阶路径)
- [十三、参考资源](#十三参考资源)

---

## 一、项目定位与能力边界

Claude Code 解决的核心问题是**在真实代码库里完成多步任务**。单次问答型 AI 助手（如 ChatGPT 网页版）只能给你代码片段，你自己复制粘贴；全自动 Agent 型工具（如 AutoGPT）放手让 AI 跑，人类难以介入。Claude Code 走中间路线：AI 主动读文件、改文件、执行命令、做 Git 操作，每一步都把变更展示给人类，确认后才落盘。

它提供的能力包括：

- **多轮对话式编程**：在终端里和 Claude 进行多轮对话，AI 记得上下文
- **文件读写与编辑**：读文件、改文件、创建文件，支持 glob 模式匹配
- **Bash 命令执行**：直接在终端里跑 shell 命令，看结果再决定下一步
- **Git 操作**：自动写提交信息、创建分支、查看 diff
- **Skill 扩展系统**：用 `claude` 开头的命令短语调用预定义的自动化工作流
- **MCP 协议集成**：通过 Model Context Protocol 连接外部工具和数据源
- **CLAUDE.md 项目级指令**：在项目根目录放 `CLAUDE.md`，给项目定制 AI 的行为

每一步的变更会展示给你，确认后才真正落盘。这种"半自动 + 监督节点"的设计，让 AI 能处理多步任务，同时保留人类介入的能力。

---

## 二、安装与首次启动

### 1. 系统要求

- macOS 13+、Linux（Ubuntu 20.04+ / Debian 10+ 等）或 Windows 10 1809+（推荐 WSL2）
- 内存 4 GB 以上
- Node.js 18+（仅使用 npm 安装方式时需要；原生安装不依赖 Node.js）
- Anthropic 账户（Claude Pro / Max 订阅或 Anthropic API Key）

### 2. 安装命令

官方推荐原生安装方式：macOS / Linux / WSL 用 curl 安装脚本，Windows 用 PowerShell。Homebrew 也可用；npm 方式已不再是官方首选（官方文档标记为 deprecated），但作为 fallback 仍然可用。

```bash
# macOS / Linux / WSL（原生安装，不需要 Node.js）
curl -fsSL https://claude.ai/install.sh | bash

# Windows PowerShell
irm https://claude.ai/install.ps1 | iex

# macOS / Linux（Homebrew）
brew install claude-code
```

npm 方式（旧方式，需要 Node.js 18+）：

```bash
npm install -g @anthropic-ai/claude-code
```

安装完成后验证：

```bash
claude --version
```

### 3. 配置账户

Claude Code 的身份认证有两种方式，任选其一：

**方式一：订阅账户登录（推荐，无需管理 API Key）**

首次运行 `claude` 时，会自动打开浏览器完成 OAuth 登录。Pro / Max 订阅账户登录后可直接使用，凭证由 Claude Code 安全保存。

**方式二：使用 Anthropic API Key**

在 shell 配置（`~/.zshrc` / `~/.bashrc`）中导出环境变量：

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

两种方式都存在时，登录态优先于环境变量。API Key 也可以写在 `~/.claude/settings.json` 的 `env` 字段里，但环境变量更直观，也不容易误提交。

### 4. 使用兼容提供商

如果不想直接消耗 Anthropic API 额度，可以使用兼容提供商。需要设置 API Base URL 和对应的 Key：

```bash
export ANTHROPIC_API_KEY="your-provider-key"
export ANTHROPIC_BASE_URL="https://openrouter.ai/api/v1"  # 或其他兼容端点
```

常见兼容提供商（限流政策和价格随时可能调整，以各提供商官网为准）：

| 提供商 | API Base | 特点 |
|--------|----------|------|
| OpenRouter | `https://openrouter.ai/api/v1` | 聚合多家模型，部分模型有免费额度 |
| NVIDIA NIM | `https://integrate.api.nvidia.com/v1` | 部分模型提供免费试用配额 |
| DeepSeek | `https://api.deepseek.com/v1` | 价格相对较低 |
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

### 1. 配置文件的位置与优先级

Claude Code 的配置分散在几个 `settings.json` 文件里，按优先级从高到低合并加载：

| 层级 | 文件 | 作用范围 | 是否入库 |
|------|------|---------|---------|
| 企业托管 | `/etc/claude-code/managed-settings.json`（Linux）等系统路径 | 机器上所有用户，开发者不可覆盖 | 不适用 |
| 命令行参数 | `--model`、`--permission-mode` 等 | 当前会话 | 不适用 |
| 项目个人级 | `.claude/settings.local.json` | 你自己，当前项目 | 否（自动加入 gitignore） |
| 项目共享级 | `.claude/settings.json` | 团队所有人 | 是 |
| 用户级 | `~/.claude/settings.json` | 你自己，所有项目 | 否 |

规则不是简单"高层文件整体覆盖低层"：`allow`、`deny` 列表会跨层合并，且任何一层的 `deny` 都不能被更低层的 `allow` 解除。另一个常见文件 `~/.claude.json` 存的是会话历史和应用状态，不要用它来配置模型或权限。

### 2. 全局与项目级配置示例

用户级 `~/.claude/settings.json`：

```json
{
  "model": "sonnet",
  "permissions": {
    "allow": ["Read", "Glob", "Grep"],
    "ask": ["Bash(git push *)"],
    "deny": ["Read(./.env)", "Bash(rm -rf *)"]
  }
}
```

项目级 `.claude/settings.json` 可以按团队规范覆盖模型和权限，比如把默认模型定为 `opus`。`permissions` 列表跨层合并，所以项目级只需写自己要新增或收紧的规则，不必复制用户级的全部内容。

### 3. 模型选择

Claude Code 用模型别名指代"当前推荐版本"：`sonnet`（日常编码，Pro / API 账户默认）、`opus`（复杂推理）、`haiku`（最快最轻量），别名会随时间指向更新的版本。也可以用完整模型名锁定具体版本，例如 `claude-opus-4-6`、`claude-sonnet-4-6`、`claude-haiku-4-5`（示例基于 2026 年中官方模型概览；Anthropic 迭代较快，最新可用版本与定价以官方 [models overview](https://platform.claude.com/docs/en/about-claude/models/overview) 为准）。

切换模型有四种方式，按优先级从高到低：

| 方式 | 写法 | 作用范围 |
|------|------|---------|
| 会话内切换 | 对话中输入 `/model sonnet` | 当前会话 |
| 启动时指定 | `claude --model opus` | 当前会话 |
| 环境变量 | `export ANTHROPIC_MODEL="opus"` | 新启动的会话 |
| 配置文件 | `settings.json` 的 `model` 字段 | 新启动的会话 |

Max 订阅账户的默认模型是 Opus，Pro / API 账户默认是 Sonnet；`/model` 不接参数可以查看当前模型并列出可选列表。

### 4. Permission System

Claude Code 有内置的权限系统，控制 AI 可以执行哪些操作。规则写在 `settings.json` 的 `permissions` 字段里，用"工具名（参数模式）"语法，支持通配符：

```json
{
  "permissions": {
    "allow": ["Read", "Bash(npm test *)"],
    "ask": ["Edit(.env*)"],
    "deny": ["Bash(rm -rf *)", "Bash(git push --force *)"]
  }
}
```

三个列表的语义：`allow` 静默放行、`ask` 每次询问、`deny` 直接拒绝（即使被 allow 也不执行）。命令匹配时可以用 glob 通配，例如 `Bash(git *)` 放行所有 `git` 开头的命令，`Edit(src/**)` 限定 `src` 目录下的文件。

除了列表，还有四种权限模式（`permissions.defaultMode`）决定"没被任何规则覆盖的操作"如何处理：

| 模式 | 行为 | 适用场景 |
|------|------|---------|
| `default` | 每次操作都询问 | 默认，陌生代码库 |
| `acceptEdits` | 文件编辑免确认，Bash 仍询问 | 日常开发 |
| `dontAsk` | 不在 allow 列表的操作直接拒绝 | 受限自动化 |
| `bypassPermissions` | 跳过所有确认 | 仅限隔离的 CI 环境 |

模式可以在会话中按 `Shift+Tab` 循环切换，也可以用 `--permission-mode` 参数在启动时指定。`Bash` 类权限的破坏性远大于读写文件——`rm -rf`、`git push --force`、`curl | sh` 都可能造成不可逆后果，所以在生产项目里建议把 `Bash` 显式收紧到白名单命令。

---

## 五、Skill 扩展系统

Skill 是 Claude Code 的可复用指令包：一个带 `SKILL.md` 的目录。2026 年起，Skill 与自定义斜杠命令统一成同一套机制，用 `/skill-name` 调用；Claude 也会根据描述在合适的时候自动调用。

### 1. 为什么需要 Skill

`CLAUDE.md` 已经能给项目注入上下文指令，为什么还要 Skill？两者的作用域不同：`CLAUDE.md` 是常驻上下文，每次对话都加载，适合放项目规范这类始终生效的内容；Skill 是按需调用的指令包，只在被调用时才注入，适合放"偶尔执行但步骤固定"的工作流，比如"生成 PR 描述"、"按团队模板写 Commit Message"。把所有指令都塞进 `CLAUDE.md` 会让上下文膨胀、消耗 Token，Skill 解决的是这个分场景加载的问题。

### 2. 内置命令与捆绑 Skill

Claude Code 自带两类命令：内置命令是写死在 CLI 里的固定功能（如 `/help`、`/clear`、`/compact`、`/model`、`/permissions`、`/mcp`），不可删除；捆绑 Skill 是官方附带的提示词包（如 `/code-review`、`/simplify`、`/batch`、`/debug`、`/loop`），行为随版本调整，可用 `/help` 查看当前版本支持哪些。

### 3. 安装第三方 Skill

通过插件市场安装（Anthropic 官方插件系统）：

```text
/plugin marketplace add owner/repo-name
/plugin install plugin-name@version
```

也可以把 Skill 目录手动放到对应位置，效果等价：

- `~/.claude/skills/<name>/SKILL.md` —— 个人使用，所有项目可用
- `.claude/skills/<name>/SKILL.md` —— 项目共享，随仓库分发

> 注：`/plugin` 系列命令的具体名称和参数以官方文档为准，Claude Code 迭代较快。

### 4. 常用 Skill 推荐

| Skill 名称 | 功能 |
|-----------|------|
| `claude-code-harness` | 给 Claude Code 加一套"写 Spec → 实施 → 验证 → Review → 打包证据"的交付流程 |
| `claude-code-skills` | 官方 AI 技能集合，覆盖全栈开发常见场景 |

> 注：第三方 Skill 的具体能力、维护状态和兼容性请到对应仓库确认，本表仅作入口参考。

### 5. 自定义 Skill

一个 Skill 是包含 `SKILL.md` 的目录。`SKILL.md` 的 frontmatter 里声明 `name` 和 `description`，正文写工作流指令；目录里还可以放参考文档、模板、脚本等辅助文件，按需加载。

一个最小 Skill 的结构：

```text
my-skill/
├── SKILL.md        # 必需：frontmatter（name、description）+ 工作流指令
└── reference.md    # 可选：被 SKILL.md 链接引用的辅助资料
```

`SKILL.md` 在 Skill 被调用时作为系统级指令注入对话，告诉 AI 这个 Skill 做什么、按什么步骤做、产出什么格式。它的作用类似于 `CLAUDE.md`，但作用域限定在 Skill 调用期间。写好后在会话里输入 `/reload-skills` 即可让新 Skill 生效。

---

## 六、MCP 协议集成

MCP（Model Context Protocol）是 Anthropic 提出的标准协议，用于让 AI 模型连接外部工具和数据源。Claude Code 原生支持 MCP。

### 1. 为什么需要 MCP

Claude Code 自带文件读写、Bash、Git 三类基础能力，但遇到"查数据库"、"读线上日志"、"调内部 API"这类需求时，自带能力不够用。MCP 解决的就是这个扩展问题：把外部工具封装成标准化的 Server，Claude Code 通过统一协议调用，用户不用为每个工具单独写适配代码。MCP 在这里扮演"插件接口层"的角色，把工具接入和工具使用解耦——工具方按协议实现 Server，Claude Code 按协议调用，两边互不耦合。

### 2. MCP Server 是什么

一个 MCP Server 是一个独立的进程，通过标准协议暴露一组工具（tools）、资源（resources）和提示（prompts）给 Claude Code 使用。

常见的 MCP Server：

- **文件系统**：`mcp/filesystem`——直接操作本地文件
- **Git**：`mcp/git`——Git 操作
- **数据库**：`mcp/postgres`、`mcp/mysql`——数据库查询
- **浏览器自动化**：`mcp/browser`——网页抓取和控制

### 3. 在 Claude Code 里配置 MCP

推荐用 `claude mcp add` 命令添加，按 `--scope` 决定写入位置：

```bash
# 项目作用域：写入项目根目录 .mcp.json（团队共享，随仓库提交）
claude mcp add --scope project filesystem -- npx -y @modelcontextprotocol/server-filesystem /path/to/allowed/dir

# 本地作用域（默认）：只对当前项目生效，写进 ~/.claude.json，个人私有
claude mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem /path/to/allowed/dir

# 用户作用域：所有项目可用
claude mcp add --scope user my-db -- npx -y @modelcontextprotocol/server-postgres
```

项目共享的 `.mcp.json` 内容结构如下（团队克隆仓库即可复用）：

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

配置完成后，新会话启动时 MCP Server 会自动拉起并注册工具；运行中的会话不会自动感知新增的 Server，需要重启或输入 `/mcp reconnect <server-name>`。用 `/mcp` 可以查看每个 Server 的连接状态（connected / failed / disabled 等）。

### 4. 使用 MCP 工具

配置完成后，MCP Server 暴露的工具会直接出现在 Claude Code 的可用工具列表里，你可以在对话中直接调用：

```text
> 用 Git MCP 查看 main 分支最近 5 次提交
```

AI 会根据任务需要自动选择调用哪个 MCP 工具，用户不需要写特殊语法。

---

## 七、任务流案例：一个 Bug 修复如何流过系统

前面分别讲了 CLI 本体、`settings.json`、`CLAUDE.md`、Skill、MCP 五条机制。这五条机制在实际任务里如何协作？下面用一个真实的 Bug 修复场景串起来。

**任务**：用户上传大于 10MB 的文件时没有报错，日志里也没有记录，需要定位并修复。

**第一步：进入项目，加载上下文**

```bash
$ cd ~/projects/upload-service
$ claude
```

Claude Code 启动时按顺序做三件事：加载 `~/.claude/settings.json` 和项目级 `.claude/settings.json` 拿到模型、权限等配置（按优先级合并），读取 `CLAUDE.md` 把项目技术栈和代码规范注入系统上下文。此时 AI 已经知道这是个 Next.js + PostgreSQL 项目，文件上传走 `src/app/api/upload/route.ts`。

**第二步：描述任务，AI 主动读文件**

```text
> Bug：用户上传大于 10MB 的文件时没有报错，日志里也没有任何记录
> 先帮我看一下错误出现在哪个环节
```

AI 调用 `Read` 工具读 `src/app/api/upload/route.ts`，发现文件大小校验逻辑写在了 `try` 块外，校验失败时直接 `return`，没进日志中间件。AI 给出分析后停下来等你确认。

**第三步：确认方案，AI 改文件**

```text
> 把校验逻辑移到 try 块里，校验失败时调用 logger.warn 记录
```

AI 调用 `Edit` 工具改文件，把 diff 展示给你。你确认后变更落盘。这一步的"确认"机制就是 Permission System 在起作用——`Edit` 权限默认开启但每次都展示 diff，让你能在落盘前拦截。

**第四步：跑测试验证**

```text
> 运行 npm test 看看有没有问题
```

AI 调用 `Bash` 工具执行 `npm test`。如果测试失败，AI 会读测试输出、定位失败用例、再次改文件，循环直到测试通过。

**第五步：写提交信息**

```text
> 提交这次修改，按 CLAUDE.md 里的 Git 规范写提交信息
```

AI 读 `CLAUDE.md` 里的 Git 规范（中文、`<类型>: <描述>` 格式），生成 `fix: 修复大文件上传校验失败时无日志记录的问题`，调用 `Bash` 执行 `git commit`。

**第六步（可选）：用 MCP 查线上日志**

如果 Bug 在线上复现但本地难复现，可以配置 `mcp/postgres` 或内部日志平台的 MCP Server，让 AI 直接查线上日志：

```text
> 用 postgres MCP 查最近 24 小时 upload 相关的错误日志
```

AI 调用 MCP 注册的工具执行查询，把结果带回对话。

这个案例里，五条机制各司其职：CLI 本体是入口，`settings.json` 提供模型和权限配置，`CLAUDE.md` 提供 Git 规范和项目上下文，Permission System 在每步变更前拦截确认，MCP 在自带能力不够时接入外部数据源。遇到新任务时，判断"这一步该用哪个机制"就能据此定位。

---

## 八、高频场景操作指南

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

Claude 会尝试定位问题，给出分析后，你可以确认方案再让它执行修复。完整的任务流参考[第七章](#七任务流案例一个-bug-修复如何流过系统)。

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

## 九、常见问题与错误排查

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
export ANTHROPIC_BASE_URL="https://api.anthropic.com"  # 官方
# 或者换兼容提供商
export ANTHROPIC_BASE_URL="https://openrouter.ai/api/v1"
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

如果你的编辑器是 VS Code、JetBrains 系列，Anthropic 也提供了对应的 IDE 插件。IDE 插件的优势是深度集成（内联补全、悬停文档），Claude Code CLI 的优势是**跨编辑器、跨终端、适合远程服务器**。两者可以互补使用：日常写代码用 IDE 插件拿补全，多步重构、跨文件改动、远程服务器开发用 CLI。

### 5. 常见错误与排查

| 错误现象 | 可能原因 | 排查方向 |
|---------|---------|---------|
| 启动报 `ANTHROPIC_API_KEY not set` | 环境变量未配置或未生效 | 检查 shell 配置文件（`~/.zshrc` / `~/.bashrc`）是否导出该变量，重启终端 |
| 命令执行被拒 `Permission denied` | 权限系统拦截 | 检查 `settings.json` 的 `permissions.deny` 列表是否包含该操作，或用 `/permissions` 调整模式 |
| 对话上下文丢失 | 单次会话超出上下文窗口 | 用 `/compact` 压缩历史，或把任务拆成多个会话 |
| MCP Server 不生效 | 配置错误或进程启动失败 | 在对话中运行 `/mcp` 查看连接状态，或用 `claude mcp list` 确认注册信息 |
| 模型响应明显变慢 | 兼容提供商限流或网络抖动 | 切回官方 API 验证，或检查提供商状态页 |
| `CLAUDE.md` 没生效 | 文件不在项目根目录或命名错误 | 确认文件在 `git rev-parse --show-toplevel` 输出的目录下，文件名大小写正确 |

---

## 十、适用边界与决策建议

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

1. **第一步：跑通安装和首次对话**。用原生安装脚本装好 `claude`，完成账户登录或 API Key 配置，在任意项目里启动 `claude`，让它读一个文件并回答一个问题。这一步只验证环境，环境不通后面所有调试都是白费。
2. **第二步：写 `CLAUDE.md`**。给主项目写一份项目级指令，把技术栈、目录规范、Git 提交格式告诉 Claude。这一步让后续每次对话都带着项目上下文，省去反复解释。
3. **第三步：跑通一个完整工作流**。挑一个真实任务（修 Bug、加测试、重构），让 Claude 走完"读文件 → 改文件 → 跑测试 → 写提交信息"全流程，确认每步的变更确认机制符合你的预期。
4. **第四步：按需引入 MCP**。当 Claude 自带的文件、Bash、Git 能力不够时（比如要查数据库），再引入对应的 MCP Server。不要一开始就堆 MCP，先确认基础工作流稳定。
5. **第五步：固化 Skill**。当你发现自己在重复给 Claude 同样的指令序列时，把它写成自定义 Skill，下次一行命令调用。Skill 把团队规范固化成 AI 行为，比省一次输入更有价值。

---

## 十一、自测题

1. Claude Code 的项目级配置文件和全局配置文件分别是什么？项目级配置如何覆盖全局配置？
2. `CLAUDE.md` 和 `settings.json` 的作用有什么区别？分别在什么场景下使用？
3. Permission System 中 `Read` / `Edit` / `Bash` 三类权限分别控制什么？为什么生产项目里建议把 `Bash` 显式收紧？
4. MCP Server 注册的工具，在 Claude Code 里如何被调用？配置完成后为什么需要重启？
5. 自定义 Skill 的最小目录结构是什么？`SKILL.md` 在 Skill 调用时起什么作用？

### 参考答案

<details>
<summary>第 1 题参考答案</summary>

全局配置文件是 `~/.claude/settings.json`（用户级），项目级配置文件是项目根目录下的 `.claude/settings.json`（随仓库共享）。Claude Code 启动时按层级合并加载；同名键以更高层级为准，因此项目级配置可以覆盖用户级配置中的 `model`、`permissions` 等字段，但不会清空用户级配置里项目级未指定的字段。容易混淆的 `~/.claude.json` 只是会话历史和应用状态，不用来配置模型或权限。
</details>

<details>
<summary>第 2 题参考答案</summary>

`CLAUDE.md` 是给 AI 看的项目上下文指令，用自然语言写技术栈、目录规范、Git 规范、注意事项，启动时作为系统级上下文注入每次对话，影响 AI 的决策和行为；`settings.json` 是结构化的运行时配置，控制模型选择、权限规则、环境变量、MCP Server 等可执行参数。前者管"AI 应该怎么做事"，后者管"AI 用什么工具和参数做事"。容易混淆的 `~/.claude.json` 只是会话历史和应用状态，不要用来配置模型或权限。
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

最小目录结构是一个包含 `SKILL.md` 的目录，可选参考文档等辅助文件：

```text
my-skill/
├── SKILL.md        # 必需：frontmatter（name、description）+ 工作流指令
└── reference.md    # 可选：被 SKILL.md 链接引用的辅助资料
```

`SKILL.md` 在 Skill 被调用时作为系统级指令注入对话，告诉 AI 这个 Skill 做什么、按什么步骤做、产出什么格式。它的作用类似于 `CLAUDE.md`，但作用域限定在 Skill 调用期间。
</details>

---

## 十二、进阶路径

- **写自定义 Skill 沉淀团队工作流**。把团队里反复出现的"读需求 → 改代码 → 跑测试 → 写提交"流程写成 Skill，统一产出格式和检查项。Skill 把团队规范固化成 AI 行为，新人入职后直接调用就能按规范产出。
- **用 MCP 接入内部工具链**。把内部 API 网关、监控平台、日志系统封装成 MCP Server，让 Claude Code 能直接查线上日志、调内部接口。这一步让 Claude Code 从代码助手扩展到工程助手，重点是为每个 MCP Server 配好权限边界，避免 AI 误操作线上资源。
- **搭权限分层配置**。在敏感项目里用 `.claude/settings.json` 的 `permissions.deny` 把生产环境路径、密钥文件、`git push` 类操作显式禁掉，再让 `CLAUDE.md` 说明哪些操作必须人工确认。配置成本不高，但能避免 AI 误操作造成事故。
- **结合 CI 做 PR Review**。在 CI 里跑 Claude Code 对 PR 改动做自动 Review，把结果作为评论贴回 PR。这一步要限定权限（只读 + 评论）和限定上下文（只看 diff 和相关文件），避免 AI 跑偏或越权改代码。
- **跟踪官方更新**。Claude Code 还在快速迭代，命令、Skill 机制、MCP 支持都可能变化。订阅 [anthropics/claude-code](https://github.com/anthropics/claude-code) 的 Release，遇到行为变化先查 Changelog，再决定是否升级。

---

## 十三、参考资源

- GitHub 仓库：[https://github.com/anthropics/claude-code](https://github.com/anthropics/claude-code)
- 官方文档：Anthropic 官网 Claude Code 页面
- Skill 市场：`/plugin marketplace` 命令访问（以官方文档为准）
- MCP 协议规范：[https://modelcontextprotocol.io](https://modelcontextprotocol.io)

---

*本文基于 GitHub 仓库 `anthropics/claude-code` 的公开信息编写，撰写时间为 2026 年 5 月。安装命令、配置项、模型版本号和 API 端点以官方最新版本为准；第三方 Skill 和 MCP Server 的能力与维护状态请到对应仓库确认。*

