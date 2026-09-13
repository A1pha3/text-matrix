---
title: "Anthropic Claude Code：官方 AI 编程 CLI 从入门到精通完全指南"
date: "2026-05-30T15:05:00+08:00"
slug: "anthropics-claude-code_official_cli_guide"
github_repo: "anthropics/claude-code"
source_key: "gh:anthropics/claude-code"
description: "Claude Code 是 Anthropic 官方终端 AI 编程助手，默认模型随账户类型而定（Pro 与 Team Standard 为 Sonnet，Max、Enterprise 与 API 为 Opus），支持文件编辑、Git 操作、多轮对话、Skill 扩展和 MCP 协议，涵盖安装配置、核心用法和自定义选项。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Anthropic", "AI 编程", "CLI", "MCP"]
---

# Anthropic Claude Code：官方 AI 编程 CLI 从入门到精通完全指南

Claude Code 是 Anthropic 官方推出的终端编程助手，默认模型随账户类型而定：Pro 与 Team Standard 订阅默认 Sonnet，Max、Team Premium、Enterprise 和 API 账户默认 Opus，会话中用 `/model` 随时切换。它是一个在终端里运行的独立 CLI 工具，覆盖 IDE 插件和 Web 界面之外的第三条路径——打开终端，敲一行命令，让 AI 帮你读代码、改文件、跑测试、写提交信息。

CLI 方式相比 IDE 插件的核心差异在**入口位置**：Vim、Emacs、nano、ssh 远程服务器，只要终端能跑，就能用 Claude Code。代价是交互全部通过对话驱动——没有图形化的 diff 面板和补全弹窗，文件引用靠 `@` 路径，多步任务靠多轮对话推进。

下面按从安装到精通的顺序展开：安装配置、核心命令、自定义选项、Skill 扩展系统、MCP 协议集成，以及日常高频场景的操作指南。

> **快速信息卡**（GitHub 指标为 2026 年 9 月快照，以仓库实时数据为准）
> - **Stars**: 约 14.5 万
> - **License**: 非标准开源许可（GitHub 未识别为 OSI 认证许可证，以仓库 LICENSE 为准）
> - **语言**: 仓库文件统计 Python 占比过半、TypeScript 次之；产品本体是编译后的独立可执行文件，运行不依赖解释器
> - **默认模型**: Pro 与 Team Standard 默认 Sonnet，Max、Team Premium、Enterprise 与 API 默认 Opus，`/model` 可切换

## 学习目标

读完后你能：

- 在 macOS / Linux / Windows（原生或 WSL2）环境完成 Claude Code 的安装、账户配置和首次启动验证
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
| **`CLAUDE.md`** | 项目上下文、代码规范、Git 规范（自然语言） | 项目根目录 `CLAUDE.md`，另有用户级与个人项目级位置 | 启动时作为系统级上下文注入每次对话 |
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
- **Skill 扩展系统**：用 `/` 斜杠命令调用预定义的自动化工作流，AI 也会按描述自行调用
- **MCP 协议集成**：通过 Model Context Protocol 连接外部工具和数据源
- **CLAUDE.md 项目级指令**：在项目根目录放 `CLAUDE.md`，给项目定制 AI 的行为

每一步的变更会展示给你，确认后才真正落盘。这种"半自动 + 监督节点"的设计，让 AI 能处理多步任务，同时保留人类介入的能力。

---

## 二、安装与首次启动

### 1. 系统要求

- macOS 13.0+、Ubuntu 20.04+ / Debian 10+ / Alpine 3.19+，或 Windows 10 1809+（Windows Server 2019+ 起支持原生 PowerShell 与 CMD，WSL2 同样可用）
- 内存 4 GB 以上，x64 或 ARM64 处理器，需要网络连接
- Node.js 22+（仅 npm 安装方式需要，v2.1.198 起；原生安装不依赖 Node.js）
- Anthropic 账户（Pro / Max / Team / Enterprise 订阅或 Anthropic API Key；免费版 Claude.ai 账户不含 Claude Code 访问权限）

### 2. 安装命令

官方推荐原生安装方式：macOS / Linux / WSL 用 curl 安装脚本，Windows 用 PowerShell、CMD 或 WinGet。Homebrew 走 cask 通道；npm 方式已不再是官方首选，但作为 fallback 仍然可用。

```bash
# macOS / Linux / WSL（原生安装，不需要 Node.js）
curl -fsSL https://claude.ai/install.sh | bash
```

```powershell
# Windows PowerShell
irm https://claude.ai/install.ps1 | iex
```

```batch
# Windows CMD
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

```bash
# macOS / Linux（Homebrew）
brew install --cask claude-code

# Windows（WinGet）
winget install Anthropic.ClaudeCode
```

原生安装支持指定版本或更新通道，例如 `curl -fsSL https://claude.ai/install.sh | bash -s stable`；已安装的机器用 `claude update` 升级。

npm 方式（旧方式，v2.1.198 起需要 Node.js 22+，不要加 `sudo`）：

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

首次运行 `claude` 时，会自动打开浏览器完成 OAuth 登录。Pro / Max 订阅账户登录后可直接使用，凭证保存在本机（macOS 存 Keychain，Linux / Windows 存 `~/.claude/.credentials.json`）。

**方式二：使用 Anthropic API Key**

在 shell 配置（`~/.zshrc` / `~/.bashrc`）中导出环境变量：

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

设置了 `ANTHROPIC_API_KEY` 后，首次运行不再打开浏览器，而是提示你确认一次这个 Key。两种方式都存在时，**环境变量优先于登录态**——官方凭据选择顺序是：云服务商凭据 → `ANTHROPIC_AUTH_TOKEN` → `ANTHROPIC_API_KEY` → `apiKeyHelper` 脚本 → OAuth 登录凭证。API Key 也可以写在 `~/.claude/settings.json` 的 `env` 字段里，但环境变量更直观，也不容易误提交。

### 4. 使用兼容提供商

官方直接支持的第三方托管平台是 Amazon Bedrock、Google Cloud 的 Agent Platform 和 Microsoft Foundry，通过各自的环境变量（如 `CLAUDE_CODE_USE_BEDROCK`）接入。此外，社区常用 `ANTHROPIC_BASE_URL` 把请求指向兼容 Anthropic API 格式的端点——这条路不是官方支持路径，模型映射和行为兼容性由提供商保证：

```bash
export ANTHROPIC_API_KEY="your-provider-key"
export ANTHROPIC_BASE_URL="https://openrouter.ai/api/v1"  # 或其他兼容端点
```

常见兼容端点（限流政策和价格随时可能调整，以各提供商官网为准）：

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

键盘操作上：`Ctrl+C` 中断正在运行的操作；没有操作在跑时，第一次按清空输入框，第二次按退出。`Ctrl+D` 也可以退出会话。输入多行内容用 `\` 接回车，或 `Ctrl+J` 换行；输入 `!` 前缀直接执行 shell 命令，`@` 前缀引用文件路径。

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

Claude Code 启动时会自动读取 `CLAUDE.md`，把它的内容作为系统级上下文注入每次对话。文件可以放在这些位置：

| 位置 | 作用范围 | 加载时机 |
|------|---------|---------|
| `./CLAUDE.md` 或 `./.claude/CLAUDE.md` | 团队共享，随仓库提交 | 每次会话启动时 |
| `./CLAUDE.local.md` | 个人项目级，加入 gitignore | 启动时，排在 `CLAUDE.md` 之后 |
| `~/.claude/CLAUDE.md` | 个人全局，所有项目生效 | 每次会话启动时 |
| 子目录中的 `CLAUDE.md` | 该子目录的局部说明 | Claude 读到该目录文件时按需加载 |

几个配套机制：所有位置的文件是**拼接**而不是覆盖；`CLAUDE.md` 里可以用 `@path/to/file` 导入其他文件，最多递归四层——导入的内容同样占用上下文，拆文件只利于组织，不省 Token。新项目可以直接跑 `/init`，Claude 会分析代码库并生成初始 `CLAUDE.md`；`/memory` 列出并打开所有记忆文件编辑。

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
| 企业托管 | `managed-settings.json`（系统目录或 MDM 下发） | 机器上所有用户，开发者不可覆盖 | 不适用 |
| 命令行 | `--settings` 指定配置文件；`--model`、`--permission-mode` 等覆盖单项 | 当前会话 | 不适用 |
| 项目个人级 | `.claude/settings.local.json` | 你自己，当前项目 | 否（不要提交到 git） |
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

Claude Code 用模型别名指代"当前推荐版本"：`sonnet`（日常编码）、`opus`（复杂推理）、`haiku`（最快最轻量），别名会随时间指向更新的版本——2026 年 9 月时 `opus` 解析到 Opus 5、`sonnet` 解析到 Sonnet 5。还有几个特殊别名：`opusplan` 计划阶段用 Opus、执行阶段切 Sonnet；`best` 在 Fable 可用时优先用它。也可以用完整模型名锁定具体版本，例如 `claude-opus-5`、`claude-sonnet-5`（Anthropic 迭代较快，最新可用版本与定价以官方 [models overview](https://platform.claude.com/docs/en/about-claude/models/overview) 为准）。

默认模型按账户类型解析：**Max、Team Premium、Enterprise 和 API 账户默认 Opus，Pro 和 Team Standard 默认 Sonnet**；管理员设置过组织默认模型时以组织设置为准。

切换方式按优先级从高到低：

| 方式 | 写法 | 作用范围 |
|------|------|---------|
| 会话内切换 | 对话中输入 `/model sonnet` | 当前会话 |
| 启动时指定 | `claude --model opus` | 当前会话 |
| 环境变量 | `export ANTHROPIC_MODEL="opus"` | 新启动的会话 |
| 配置文件 | `settings.json` 的 `model` 字段 | 新启动的会话 |

`/model` 不接参数会打开模型选择器：按 `Enter` 切换并保存为新会话的默认值（写入用户级设置的 `model` 字段），按 `s` 则只对当前会话生效。

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

三个列表按 **deny → ask → allow** 的顺序求值，第一个命中的规则生效：宽泛的 `deny` 不能被更具体的 `allow` 打破，任何层级的 `deny` 也不能被更低层级解除。规则语法上，`Bash(npm run build)` 只精确匹配这一条命令，`Bash(npm run *)` 匹配任意后缀，`:*` 写法等价于尾部的 ` *`（`Bash(ls:*)` 与 `Bash(ls *)` 相同）；`&&`、`;`、`|` 拼接的复合命令要求每个子命令分别命中规则，`timeout`、`nice` 这类包装器会被剥掉再匹配。

除了列表，还有六种权限模式（`permissions.defaultMode`）决定"没被任何规则覆盖的操作"如何处理：

| 模式 | 行为 | 适用场景 |
|------|------|---------|
| `default` | 每类工具首次使用时提示（别名 `manual`） | 默认，陌生代码库 |
| `acceptEdits` | 文件编辑和常见文件系统命令（`mkdir`、`touch`、`mv`、`cp`）免确认，限工作目录内；Bash 仍询问 | 日常开发 |
| `plan` | 只读探索：读文件、跑只读命令，不改源文件 | 方案评审、陌生代码考察 |
| `auto` | 自动批准工具调用，后台安全检查校验操作与请求是否一致 | 熟悉项目里的自动化 |
| `dontAsk` | 本应提示的操作直接拒绝，预批准的仍可运行 | 受限自动化 |
| `bypassPermissions` | 跳过权限提示，包括对受保护路径的提示 | 仅限容器 / VM 等隔离环境 |

模式可以在会话中按 `Shift+Tab` 循环切换，也可以用 `--permission-mode` 参数在启动时指定。`Bash` 类权限的破坏性远大于读写文件——`rm -rf`、`git push --force`、`curl | sh` 都可能造成不可逆后果，所以在生产项目里建议把 `Bash` 显式收紧到白名单命令。

---

## 五、Skill 扩展系统

Skill 是 Claude Code 的可复用指令包：一个带 `SKILL.md` 的目录，用 `/skill-name` 调用。自定义斜杠命令已并入这套体系——`.claude/commands/deploy.md` 和 `.claude/skills/deploy/SKILL.md` 都会生成 `/deploy`，旧的 commands 文件继续兼容。Claude 也会根据 SKILL.md 里的描述，在任务匹配时自动调用。

### 1. 为什么需要 Skill

`CLAUDE.md` 已经能给项目注入上下文指令，为什么还要 Skill？两者的作用域不同：`CLAUDE.md` 是常驻上下文，每次对话都加载，适合放项目规范这类始终生效的内容；Skill 是按需调用的指令包，只在被调用时才注入，适合放"偶尔执行但步骤固定"的工作流，比如"生成 PR 描述"、"按团队模板写 Commit Message"。把所有指令都塞进 `CLAUDE.md` 会让上下文膨胀、消耗 Token，Skill 解决的就是分场景加载的问题。

### 2. 内置命令与捆绑 Skill

Claude Code 自带两类命令：内置命令是写死在 CLI 里的固定功能，如 `/help`、`/clear`、`/compact`、`/model`、`/permissions`、`/mcp`、`/init`、`/context`、`/rewind`，不可删除；捆绑 Skill 是官方附带的提示词包，如 `/doctor`（别名 `/checkup`，诊断安装与健康状态）、`/code-review`（别名 `/review`，审查当前 diff 或指定 PR）、`/batch`、`/debug`、`/loop`、`/claude-api`，以及配套使用的 `/run` 和 `/verify`。捆绑 Skill 的行为随版本调整，可用 `/help` 查看当前版本支持哪些，也可以用 `disableBundledSkills` 设置整体关闭。

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

### 4. 值得关注的 Skill 仓库

| 仓库 | 说明 |
|------|------|
| `anthropics/skills` | Anthropic 官方 Skill 集合，覆盖文档处理、开发流程等场景 |
| `claude-code-harness` | 第三方交付流程 Skill："写 Spec → 实施 → 验证 → Review → 打包证据" |

> 注：第三方 Skill 的具体能力、维护状态和兼容性请到对应仓库确认，本表仅作入口参考。

### 5. 自定义 Skill

一个 Skill 是包含 `SKILL.md` 的目录。`SKILL.md` 的 frontmatter 里声明元数据，正文写工作流指令；目录里还可以放参考文档、模板、脚本等辅助文件，按需加载。frontmatter 的常用字段：`description`（告诉 Claude 何时用这个 Skill，也是自动调用的依据）、`when_to_use`、`argument-hint`（参数提示）、`disable-model-invocation`（禁止 AI 自动调用，只允许手动触发）、`allowed-tools`（限定 Skill 内可用的工具）。命令名默认来自目录名。官方建议 `SKILL.md` 控制在 500 行以内，大段参考资料拆到辅助文件里。

一个最小 Skill 的结构：

```text
my-skill/
├── SKILL.md        # 必需：frontmatter（description 等）+ 工作流指令
└── reference.md    # 可选：被 SKILL.md 链接引用的辅助资料
```

`SKILL.md` 在 Skill 被调用时作为系统级指令注入对话，告诉 AI 这个 Skill 做什么、按什么步骤做、产出什么格式。它的作用类似于 `CLAUDE.md`，但作用域限定在 Skill 调用期间。写好后不用重启：Claude Code 会监听 skills 目录的变化，`SKILL.md` 的新增、修改、删除都即时生效，没有专门的 reload 命令；会话里用 `/skills` 可以查看和开关各 Skill 的可见性。

---

## 六、MCP 协议集成

MCP（Model Context Protocol）是 Anthropic 提出的标准协议，用于让 AI 模型连接外部工具和数据源。Claude Code 原生支持 MCP。

### 1. 为什么需要 MCP

Claude Code 自带文件读写、Bash、Git 三类基础能力，但遇到"查数据库"、"读线上日志"、"调内部 API"这类需求时，自带能力不够用。MCP 解决的就是这个扩展问题：把外部工具封装成标准化的 Server，Claude Code 通过统一协议调用，用户不用为每个工具单独写适配代码。MCP 在这里扮演"插件接口层"的角色，把工具接入和工具使用解耦——工具方按协议实现 Server，Claude Code 按协议调用，两边互不耦合。

### 2. MCP Server 是什么

一个 MCP Server 是一个独立的进程，通过标准协议暴露一组工具（tools）、资源（resources）和提示（prompts）给 Claude Code 使用。

常见的 MCP Server：

- **文件系统**：`@modelcontextprotocol/server-filesystem`——受限访问的本地文件操作（官方参考实现，npm 包）
- **Git**：`mcp-server-git`——读取、搜索、操作 Git 仓库（官方参考实现，PyPI 包，`uvx mcp-server-git` 运行）
- **记忆 / 推理 / 抓取 / 时区**：`server-memory`、`server-sequential-thinking`、`server-fetch`、`server-time`——同属官方参考实现
- **数据库与 SaaS**：PostgreSQL 等早期官方参考实现已移入归档仓库（servers-archived），生产环境建议用数据库厂商或内部平台维护的实现；Stripe、Notion 等 SaaS 提供官方远程 MCP 端点，直接以 HTTP 方式接入

### 3. 在 Claude Code 里配置 MCP

推荐用 `claude mcp add` 命令添加，按 `--scope` 决定写入位置：

```bash
# 项目作用域：写入项目根目录 .mcp.json（团队共享，随仓库提交）
claude mcp add --scope project filesystem -- npx -y @modelcontextprotocol/server-filesystem /path/to/allowed/dir

# 本地作用域（默认）：只对当前项目生效，写进 ~/.claude.json，个人私有
claude mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem /path/to/allowed/dir

# 用户作用域：所有项目可用
claude mcp add --scope user my-db -- npx -y mcp-server-postgres
```

远程 Server 走 HTTP 传输（官方推荐的远程方式）：

```bash
claude mcp add --transport http stripe https://mcp.stripe.com/mcp
```

项目共享的 `.mcp.json` 内容结构如下（团队克隆仓库即可复用）：

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"]
    },
    "stripe": {
      "type": "http",
      "url": "https://mcp.stripe.com/mcp"
    }
  }
}
```

`.mcp.json` 支持 `${VAR}` 和 `${VAR:-default}` 环境变量展开，密钥不必写进提交到仓库的文件。注意 `claude mcp add` 里的 `--` 分隔符：它之后的内容原样传给 Server 进程，没有它，Server 自己的 flag（比如 `--port`）会被 Claude Code 误解析。

配置完成后，新会话启动时 MCP Server 会自动拉起并注册工具；运行中的会话不会自动感知新增的 Server，需要重启或输入 `/mcp reconnect <server-name>`。用 `/mcp` 可以查看每个 Server 的连接状态（connected / failed / disabled 等），还能触发 OAuth 认证、临时禁用某个 Server。

### 4. 使用 MCP 工具

配置完成后，MCP Server 暴露的工具会直接出现在 Claude Code 的可用工具列表里，你可以在对话中直接调用：

```text
> 用 Git MCP 查看 main 分支最近 5 次提交
```

AI 会根据任务需要自动选择调用哪个 MCP 工具，用户不需要写特殊语法。

---

## 七、任务流案例：一个 Bug 修复如何流过系统

前面分别讲了 CLI 本体、`settings.json`、`CLAUDE.md` 和 Skill / MCP 扩展层四条机制。它们在实际任务里如何协作？下面用一个真实的 Bug 修复场景串起来。

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

如果 Bug 在线上复现但本地难复现，可以给数据库或日志平台配一个 MCP Server，让 AI 直接查线上数据：

```text
> 用 postgres MCP 查最近 24 小时 upload 相关的错误日志
```

AI 调用 MCP 注册的工具执行查询，把结果带回对话。

这个案例里，四条机制各司其职：CLI 本体是入口，`settings.json` 提供模型和权限配置（Permission System 在每步变更前拦截确认），`CLAUDE.md` 提供 Git 规范和项目上下文，MCP 在自带能力不够时接入外部数据源。遇到新任务时，判断"这一步该用哪个机制"就能据此定位。

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

也可以直接跑 `/init`，让 Claude 分析代码库并生成初始 `CLAUDE.md`，后续每次会话都自动带上这些项目上下文。

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

当前版本内置了 `/code-review`（别名 `/review`）捆绑 Skill，可以直接审查当前 diff 或指定 PR。

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

动手前建议先按 `Shift+Tab` 切到 `plan` 模式，让 Claude 只做只读分析、给出重构方案，确认范围没有扩大再放行编辑。

---

## 九、常见问题与错误排查

### 1. API 消耗如何控制

Claude Code 每次对话都会消耗 Token，主要来自：

- 项目文件内容的上下文注入
- 对话历史
- 模型输出的 completion

官方没有 `.claudeignore` 这样的忽略文件机制（写了也不会生效），控制消耗靠这些手段：

1. 在 `CLAUDE.md` 里明确说明哪些文件不需要关心，减少无关文件的读取
2. 用 `/context` 查看当前上下文占用，用 `/compact` 压缩对话历史（可附加总结重点），任务切换时用 `/clear` 开新会话
3. 复杂任务分段做，不要在一个对话里塞太多逻辑
4. 用 `permissions.deny` 挡住 `.env` 等敏感文件——主要目的是安全，顺带避免这些内容进入上下文

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

安装或行为异常时，`/doctor` 会做健康诊断；版本问题用 `claude update` 升级后再试。

### 4. 与 IDE 插件的分工

如果你的编辑器是 VS Code、JetBrains 系列，Anthropic 提供了对应的 IDE 扩展：diff 在编辑器面板里展示、选中的代码自动共享为上下文、诊断信息同步给 Claude。注意 Anthropic 没有做内联代码补全——边打字边补全是 Copilot、Cursor 这类工具的领域。Claude Code CLI 的优势是**跨编辑器、跨终端、适合远程服务器**，还能进 CI 脚本。两者可以互补使用：日常补全交给 IDE 工具，多步重构、跨文件改动、远程服务器开发用 CLI。

### 5. 常见错误与排查

| 错误现象 | 可能原因 | 排查方向 |
|---------|---------|---------|
| 认证失败或要求重复登录 | 环境变量与登录态冲突 | 检查 shell 配置文件（`~/.zshrc` / `~/.bashrc`）里的 `ANTHROPIC_API_KEY` 是否过期，重启终端；会话内用 `/login` 重新登录 |
| 命令执行被拒 `Permission denied` | 权限系统拦截 | 检查 `settings.json` 的 `permissions.deny` 列表是否包含该操作，或用 `/permissions` 调整模式 |
| 对话上下文丢失 | 单次会话超出上下文窗口 | 用 `/compact` 压缩历史，或把任务拆成多个会话 |
| MCP Server 不生效 | 配置错误或进程启动失败 | 在对话中运行 `/mcp` 查看连接状态，或用 `claude mcp list` 确认注册信息 |
| 模型响应明显变慢 | 兼容提供商限流或网络抖动 | 切回官方 API 验证，或检查提供商状态页 |
| `CLAUDE.md` 没生效 | 文件不在项目根目录或命名错误 | 确认文件在 `git rev-parse --show-toplevel` 输出的目录下，文件名大小写正确；用 `/context` 查看实际加载了哪些记忆文件 |
| 行为与文档描述不符 | 本地版本过旧 | 运行 `/doctor` 诊断，用 `claude update` 升级后对照官方 Changelog |

---

## 十、适用边界与决策建议

Claude Code 最适合以下场景：

- **日常 CLI 编程辅助**：终端常开，随时丢一个任务进去
- **跨编辑器场景**：不论用什么编辑器，统一的编程入口
- **远程服务器开发**：ssh 进去一样用 Claude Code
- **Skill 自动化**：把重复的工作流固化成 Skill，一键调用

不太适合的场景：

- 需要毫秒级响应的内联代码补全（用 Copilot、Cursor 这类 IDE 工具更合适）
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

`Read` 控制读文件、`Edit` 控制改文件、`Bash` 控制执行 shell 命令。生产项目里建议把 `Bash` 显式收紧是因为 shell 命令的破坏性远大于读写文件——`rm -rf`、`git push --force`、`curl | sh` 都可能造成不可逆后果。求值顺序是 deny → ask → allow，第一个命中的规则生效，所以宽泛的 `deny` 无法被更具体的 `allow` 打破。常见做法是用 `permissions.deny` 把生产环境路径、密钥文件、`git push` 类操作显式禁掉。
</details>

<details>
<summary>第 4 题参考答案</summary>

MCP Server 注册的工具会出现在 Claude Code 的可用工具列表里，AI 在对话中根据任务需要自动调用，用户不需要写特殊语法。配置完成后需要重启是因为 MCP Server 是独立进程，Claude Code 启动时按配置拉起这些进程并建立通信通道，运行中的会话不会自动感知新增的 Server 配置——急用时也可以用 `/mcp reconnect <server-name>` 重连。
</details>

<details>
<summary>第 5 题参考答案</summary>

最小目录结构是一个包含 `SKILL.md` 的目录，可选参考文档等辅助文件：

```text
my-skill/
├── SKILL.md        # 必需：frontmatter（description 等）+ 工作流指令
└── reference.md    # 可选：被 SKILL.md 链接引用的辅助资料
```

`SKILL.md` 在 Skill 被调用时作为系统级指令注入对话，告诉 AI 这个 Skill 做什么、按什么步骤做、产出什么格式。它的作用类似于 `CLAUDE.md`，但作用域限定在 Skill 调用期间。skills 目录有实时变更监听，文件保存后即生效，不需要重启会话。
</details>

---

## 十二、进阶路径

- **写自定义 Skill 沉淀团队工作流**。把团队里反复出现的"读需求 → 改代码 → 跑测试 → 写提交"流程写成 Skill，统一产出格式和检查项。新人入职后直接调用，产出的格式和检查项跟老成员一致。
- **用 MCP 接入内部工具链**。把内部 API 网关、监控平台、日志系统封装成 MCP Server，让 Claude Code 能直接查线上日志、调内部接口。这一步让 Claude Code 从代码助手扩展到工程助手，重点是为每个 MCP Server 配好权限边界，避免 AI 误操作线上资源。
- **搭权限分层配置**。在敏感项目里用 `.claude/settings.json` 的 `permissions.deny` 把生产环境路径、密钥文件、`git push` 类操作显式禁掉，再让 `CLAUDE.md` 说明哪些操作必须人工确认。配置成本不高，但能避免 AI 误操作造成事故。
- **结合 CI 做 PR Review**。在 CI 里跑 Claude Code 对 PR 改动做自动 Review，把结果作为评论贴回 PR。这一步要限定权限（只读 + 评论）和限定上下文（只看 diff 和相关文件），避免 AI 跑偏或越权改代码；CI 环境的长期凭证可以用 `claude setup-token` 生成一年期 OAuth token。
- **跟踪官方更新**。Claude Code 还在快速迭代，命令、Skill 机制、MCP 支持都可能变化。订阅 [anthropics/claude-code](https://github.com/anthropics/claude-code) 的 Release，遇到行为变化先查 Changelog，再决定是否升级。

---

## 十三、参考资源

- GitHub 仓库：[https://github.com/anthropics/claude-code](https://github.com/anthropics/claude-code)
- 官方文档：[https://code.claude.com/docs](https://code.claude.com/docs)（setup / settings / permissions / memory / skills / mcp 分册）
- 官方 Skill 集合：[https://github.com/anthropics/skills](https://github.com/anthropics/skills)
- MCP 协议规范：[https://modelcontextprotocol.io](https://modelcontextprotocol.io)；官方参考实现：[https://github.com/modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)

---

*本文基于 GitHub 仓库 `anthropics/claude-code` 的公开信息编写，初稿于 2026 年 5 月，2026 年 9 月对照官方文档与仓库数据核实更新。安装命令、配置项、模型版本号和 API 端点以官方最新版本为准；第三方 Skill 和 MCP Server 的能力与维护状态请到对应仓库确认。*
