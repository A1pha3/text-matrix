---
title: "Claude How To：Claude Code 精通学习指南"
date: "2026-04-01T13:00:00+08:00"
lastmod: "2026-09-22T10:00:00+08:00"
slug: "claude-howto-master-guide"
github_repo: "luongnv89/claude-howto"
source_key: "gh:luongnv89/claude-howto"
aliases:
  - /posts/tech/claude-howto-master-guide/
  - /posts/tech/ai-agent/claude-howto-master-claude-code-guide/
categories: ["技术笔记"]
tags: ["Claude Code", "AI 编程", "Skills", "Hooks", "MCP"]
description: "Claude How To 是 4.1 万 Stars 的 Claude Code 学习指南，按 10 个模块、11-13 小时路径带你在周末入门到进阶。本文以 v2.1.278 为口径拆解其模块结构、可复制的生产级模板与组合工作流，全部示例对照仓库源文件核实。"
---

# Claude How To：Claude Code 精通学习指南

> 预计阅读时间：30 分钟 | 难度：⭐⭐⭐⭐

装好 Claude Code、跑过几个提示词之后，大多数人卡在同一个地方：知道斜杠命令、Hooks、MCP 这些功能存在，却不知道怎么把它们串成一个真正省时间的工作流。官方文档把每个功能讲清楚了，但"先学哪个、怎么组合"要自己摸索。

[luongnv89/claude-howto](https://github.com/luongnv89/claude-howto) 就是冲着这个缺口来的。它是一个结构化、可视化、以实例驱动的 Claude Code 学习指南：10 个教程模块、带时间估计的进阶路线、可以直接复制进项目的生产级模板，还有一个内置自测来帮你定位水平。仓库口号是"一个周末精通 Claude Code"，官方定位是与文档互补——用它学习，用文档查细节。

本文以指南 v2.1.278（2026 年 9 月，对齐 Claude Code 2.1.278）为口径，数据时点 2026-09-22。

## 学习目标

读完本文，你会清楚三件事：

- Claude Code 十个核心功能模块各自解决什么问题，学习的先后顺序怎么排；
- 这份指南提供了哪些可以直接复制进项目的模板，它们长什么样；
- 怎么把斜杠命令、Memory、Subagents、Hooks、MCP 组合成代码评审、文档生成、部署自动化这三类真实工作流。

---

## 一、项目概述

### 1.1 项目定位

作者 luongnv89 在 README 里把痛点讲得很直白：官方文档描述功能但不展示组合；没有明确的学习路径，你不知道该先学 MCP 还是先学 Hooks；示例太基础，一个"hello world"斜杠命令帮不了你搭建带安全扫描的代码评审流水线。指南的应对方式是按学习顺序重组全部功能，每个模块配 Mermaid 图讲解内部机制，再给一套复制即用的配置。

除了 GitHub 仓库，项目还有[配套官网](http://luongnv.com/claude-howto/)，README 有英语、越南语、中文、乌克兰语、日语五个语言版本（中文版在 `zh/` 目录）。

### 1.2 关键数据

| 指标 | 数值 |
|------|------|
| **GitHub Stars** | 41,620 |
| **GitHub Forks** | 5,111 |
| **Commits** | 248 |
| **贡献者** | 24 |
| **指南版本** | v2.1.278（2026 年 9 月，对齐 Claude Code 2.1.278） |
| **最新提交** | 2026 年 9 月 19 日 |
| **协议** | MIT |

仓库 2025 年 11 月创建，当前 4.16 万 Stars，README 徽章显示曾登 GitHub Trending 第一。维护节奏跟 Claude Code 版本走：每个 Claude Code 版本发布后同步更新内容，README 标注"Last Updated: September 19, 2026"。教学素材类仓库能做到这个更新强度的不多。

### 1.3 与官方文档的分工

| 维度 | 官方文档 | Claude How To |
|------|----------|---------------|
| **格式** | 参考文档 | 可视化教程 + Mermaid 图表 |
| **深度** | 功能描述 | 内部机制讲解 |
| **示例** | 基础片段 | 生产级模板直接可用 |
| **结构** | 按功能组织 | 渐进式学习路径 |
| **入门** | 自主探索 | 带时间估计的引导路线图 |
| **自测** | 无 | 交互式测验定位知识缺口 |

这张表出自 README 原文的对比节。值得补一句作者没说的：仓库里每个模板与示例文件末尾都统一标注对应的官方文档链接、核对用的 Claude Code 版本号和兼容模型清单，内容更新时对着官方 changelog 逐项核对——所以它更像官方文档的"导学层"，不是替代品。

### 1.4 学习路径概览

| 阶段 | 时长 | 起点 |
|------|------|------|
| **初学者** | ~2.5 小时 | Slash Commands |
| **中级** | ~3.5 小时 | Skills |
| **高级** | ~5 小时 | Advanced Features |

全部走完约 11-13 小时。不确定自己水平的，在 Claude Code 里跑 `/self-assessment`，它会按你答不上来的题推荐起点；每学完一个模块，用 `/lesson-quiz [主题]` 做小测查漏。

---

## 二、十大模块详解

### 2.1 模块总览

| 学习顺序 | 模块 | 目录 | 难度 | 时长 |
|------|------|------|------|------|
| 1 | Slash Commands | `01-slash-commands/` | 初学者 | 30 分钟 |
| 2 | Memory | `02-memory/` | 初学者+ | 45 分钟 |
| 3 | Checkpoints | `08-checkpoints/` | 中级 | 45 分钟 |
| 4 | CLI Basics | `10-cli/` | 初学者+ | 30 分钟 |
| 5 | Skills | `03-skills/` | 中级 | 1 小时 |
| 6 | Hooks | `06-hooks/` | 中级 | 1 小时 |
| 7 | MCP | `05-mcp/` | 中级+ | 1 小时 |
| 8 | Subagents | `04-subagents/` | 中级+ | 1.5 小时 |
| 9 | Advanced Features | `09-advanced-features/` | 高级 | 2-3 小时 |
| 10 | Plugins | `07-plugins/` | 高级 | 2 小时 |

注意"学习顺序"和"目录编号"不一致：目录按功能族编号（01 斜杠命令、02 记忆……07 插件），学习路径表是按依赖关系重排的——比如 Checkpoints 的目录是 `08-checkpoints/`，但因为它只依赖基础概念，被提到第 3 位学。下文按学习顺序展开。

### 2.2 Slash Commands（斜杠命令）

斜杠命令是把一段写好的提示词存成 Markdown 文件，用 `/` 前缀触发。指南提供 8 个现成命令：

| 命令 | 文件 | 用途 |
|------|------|------|
| `/optimize` | `optimize.md` | 性能问题分析与优化建议 |
| `/pr` | `pr.md` | Pull Request 准备 |
| `/generate-api-docs` | `generate-api-docs.md` | API 文档生成 |
| `/commit` | `commit.md` | 规范化提交信息 |
| `/doc-refactor` | `doc-refactor.md` | 文档重构 |
| `/push-all` | `push-all.md` | 批量推送 |
| `/setup-ci-cd` | `setup-ci-cd.md` | CI/CD 配置 |
| `/unit-test-expand` | `unit-test-expand.md` | 单元测试补全 |

命令文件的格式很简单，frontmatter 一行 `description`，正文就是给 Claude 的指令。`optimize.md` 的正文是按优先级排列的五类检查——性能瓶颈（O(n²) 操作、低效循环）、内存泄漏、算法改进、缓存机会、并发问题——并规定输出格式必须包含严重度（Critical/High/Medium/Low）、代码位置、解释和带代码示例的修复建议。

安装就是把文件复制到项目的 `.claude/commands/` 目录，会话里输入 `/optimize` 即可。自定义一个新命令也一样：写个 Markdown，说明你要 Claude 做什么。

### 2.3 Memory（记忆）

Memory 解决的是"每次会话都要重新交代背景"的问题，本质是三层 CLAUDE.md 文件，Claude 启动时自动加载：

| 层级 | 模板文件 | 安装位置 | 用途 |
|------|----------|----------|------|
| 项目级 | `project-CLAUDE.md` | 项目根目录 `CLAUDE.md` | 团队共享规范，进版本控制 |
| 目录级 | `directory-api-CLAUDE.md` | 如 `src/api/CLAUDE.md` | 只对该目录生效的规则 |
| 个人级 | `personal-CLAUDE.md` | `~/.claude/CLAUDE.md` | 个人偏好，不进仓库 |

指南的 `project-CLAUDE.md` 模板以一个电商项目为背景，把该写进去的东西列全了：技术栈、命名规范（文件 kebab-case、类 PascalCase、常量 UPPER_SNAKE_CASE）、Git 工作流（分支命名、conventional commits、合并前必须过 CI 加一人 approve）、测试要求、API 规范、常用命令表、团队成员和已知问题。有两个细节值得抄进自己的模板：一是用 `@docs/architecture.md` 这样的导入语法挂接架构文档，避免把长文档全文塞进 CLAUDE.md；二是"Known Issues & Workarounds"一节——把"连接池高峰期限 20，绕法是排队"这类坑写成条目，Claude 生成代码时会主动避开。

### 2.4 Checkpoints（检查点与回退）

Checkpoints 让你大胆实验：每次改动前有快照，改砸了一键回退。这个模块最反直觉的一点是**没有保存命令**——Claude Code 在你每次输入提示词时自动创建检查点，需要回退时按两次 Esc 或输入 `/rewind`，然后从五个选项里选：

1. Restore code and conversation（代码和对话都回退）
2. Restore conversation（只回退对话）
3. Restore code（只回退代码）
4. Summarize from here（从当前点总结）
5. Never mind（取消）

"只回退代码"和"只回退对话"分开设计是聪明的：改代码前想换个思路重问，回对话；对话有价值但代码跑偏了，回代码。指南建议的用法包括同一检查点出发对比两种实现、重构前留档、A/B 两套设计方案。

### 2.5 CLI Basics（命令行基础）

Claude Code 不只是交互式 REPL，`10-cli/` 模块把命令行用法整理成脚本友好的参考：

```bash
# 交互模式
claude "explain this project"

# Print 模式（非交互，跑完退出）
claude -p "review this code"

# 管道输入
cat error.log | claude -p "explain this error"

# JSON 输出，供脚本解析
claude -p --output-format json "list functions"

# 恢复指定会话
claude -r "feature-auth" "continue implementation"
```

`-p` 加管道和 JSON 输出是 CI/CD 集成的基础：让 Claude 在流水线里跑测试、生成报告、解析结构化结果，都不需要人坐在终端前。

### 2.6 Skills（技能）

Skills 是带脚本和参考资料的自动调用能力包。与斜杠命令的区别在触发方式：命令要你手动输入，Skill 由 Claude 根据 description 自动判断调用。指南提供 6 个技能：

| 技能 | 内容 | 结构亮点 |
|------|------|----------|
| `code-review-specialist` | 安全/性能/质量/可维护性四维评审 | 配 `scripts/` 复杂度分析脚本 + `templates/` 评审清单 |
| `refactor` | 重构决策与执行 | 带 `references/` 代码坏味手册与重构目录，`scripts/` 坏味检测 |
| `doc-generator` | API 文档生成 | 配 `generate-docs.py` 生成脚本 |
| `blog-draft` | 博客草稿写作 | 大纲与草稿两套模板 |
| `brand-voice` | 品牌语调一致性检查 | 配语调示例库 |
| `claude-md` | 帮你给项目写 CLAUDE.md | 元技能：用 Claude 配置 Claude |

SKILL.md 的格式比大多数人想象的简单，`code-review-specialist` 的开头是这样的：

```markdown
---
name: code-review-specialist
description: Comprehensive code review with security, performance, and quality analysis. Use when users ask to review code, analyze code quality, evaluate pull requests, or mention code review, security analysis, or performance optimization.
---

# Code Review Skill

This skill provides comprehensive code review capabilities focusing on:

1. **Security Analysis**
   - Authentication/authorization issues
   - ...
```

触发逻辑全写在 description 里——"Use when users ask to review code..."，Claude 拿这段话判断什么时候加载这个技能。正文列能力清单，并告诉 Claude 执行时读取哪些参考文件。写自定义 Skill 的要点也在这：description 要写清"什么情况下用我"，而不是功能介绍。

### 2.7 Hooks（生命周期钩子）

Hooks 是 Claude Code 的事件驱动自动化：特定事件发生时自动执行 shell 命令。指南的 `06-hooks/` 提供 11 个现成脚本，从代码格式化到安全扫描：

| 脚本 | 挂载事件 | 用途 |
|------|----------|------|
| `format-code.sh` | 写文件后 | 自动格式化代码 |
| `security-scan.sh` | 写文件后 | 扫描安全问题 |
| `pre-commit.sh` | 提交前 | 提交前跑测试 |
| `log-bash.sh` | Bash 调用后 | 记录所有命令 |
| `validate-prompt.sh` | 提示词提交时 | 校验用户输入 |
| `notify-team.sh` | 会话结束 | Slack 通知 |
| `context-tracker.py` | 定期 | 上下文用量追踪 |
| `dependency-check.sh` / `pre-tool-check.sh` / `session-end.sh` | 相应事件 | 依赖检查 / 工具前置检查 / 会话清理 |

挂载靠 `settings.json` 配置。以"写文件后自动格式化加安全扫描"为例：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/format-and-lint.sh" }
        ]
      }
    ]
  }
}
```

指南按 Claude Code 官方文档整理了完整的 Hook 体系：5 种类型（`command`、`http`、`prompt`、`mcp_tool`、`agent`，决定钩子怎么跑）、33 个事件分 4 类（Tool 类 6 个、Session 类 7 个、Task 类 6 个、Lifecycle 类 14 个，决定什么时候跑）。Hook 事件覆盖面是 Claude Code 自动化能力的上限——从 `PreToolUse` 拦截危险命令到 `SessionStart` 注入环境信息，基本上"每次 Claude 做某事之前/之后"都可编程。

### 2.8 MCP（Model Context Protocol）

MCP 让 Claude Code 访问外部工具和数据源。指南提供 4 个现成配置：`github-mcp.json`（GitHub 集成）、`database-mcp.json`（数据库查询）、`filesystem-mcp.json`（文件操作）、`multi-mcp.json`（多服务器组合）。GitHub 的配置长这样：

```json
{
  "mcpServers": {
    "github": {
      "type": "stdio",
      "command": "npx",
      "args": ["@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

两种安装方式：手动把配置放进项目 `.mcp.json`（进版本控制，全团队共享），或用 CLI 命令添加到个人配置：

```bash
export GITHUB_TOKEN="your_token"
claude mcp add github -- npx -y @modelcontextprotocol/server-github
```

配置完成后 MCP 工具自动对 Claude 可用——代码评审工作流里"从 GitHub 拉 PR"这一步，靠的就是它。

### 2.9 Subagents（子代理）

Subagents 是有独立上下文窗口的专职助手：主代理把任务委托出去，子代理用自己的提示词和工具白名单干活，做完只返回结果。指南提供 9 个现成定义，安装到项目的 `.claude/agents/` 目录：

| 子代理 | 职责 |
|--------|------|
| `code-reviewer` | 代码质量与安全评审 |
| `clean-code-reviewer` | 整洁度专项检查 |
| `secure-reviewer` | 安全评审（只读，禁止修改） |
| `test-engineer` | 测试策略与覆盖率 |
| `debugger` | Bug 定位与修复 |
| `documentation-writer` | 技术文档 |
| `implementation-agent` | 完整功能实现 |
| `performance-optimizer` | 性能优化 |
| `data-scientist` | 数据分析 |

子代理定义也是 Markdown 文件，frontmatter 四个字段——`name`、`description`、`tools`（工具白名单）、`model`：

```markdown
---
name: code-reviewer
description: Expert code review specialist. Use PROACTIVELY after writing or modifying code to ensure quality, security, and maintainability.
tools: Read, Grep, Glob, Bash
model: inherit
---

# Code Reviewer Agent

You are a senior code reviewer ensuring high standards of code quality and security.

When invoked:
1. Run git diff to see recent changes
2. Focus on modified files
3. Begin review immediately

## Review Priorities (in order)

1. **Security Issues** - Authentication, authorization, data exposure
2. **Performance Problems** - O(n^2) operations, memory leaks, inefficient queries
...
```

两个值得学的细节：`description` 里写"Use PROACTIVELY after writing or modifying code"是在告诉主代理主动委托的时机；`tools` 白名单里只给 Read/Grep/Glob/Bash，评审代理物理上做不了修改——权限最小化不靠提示词约束，靠工具配置。

### 2.10 Advanced Features（高级功能）

这个模块体量最大（模块 README 超过 11 万字节），覆盖六块：

- **Planning Mode**：写代码前先产出详细实现计划，适合多文件改动；
- **Extended Thinking**：复杂问题的深度推理，`Alt+T`（macOS `Option+T`）切换；
- **Background Tasks**：长任务后台跑，不阻塞会话；
- **Permission Modes**：六档权限——`manual`（原名 `default`，每步确认）、`acceptEdits`（自动接受编辑）、`plan`（只读规划）、`auto`（自动模式，带后台安全分类器）、`dontAsk`、`bypassPermissions`；
- **Headless Mode**：`claude -p` 无头运行，CI/CD 集成的正式用法；
- **Session Management**：`/resume`、`/rename`、`/fork`、`/branch` 管理会话，`claude -c` 继续上次会话，`claude -r` 恢复指定会话。

模块自带的 `config-examples.json` 很实用——11 个场景的完整 `settings.json` 配置，从开发环境到安全审计，下一节展开。

### 2.11 Plugins（插件）

Plugins 是把命令、子代理、Hooks、MCP 打包分发的方式。指南提供 3 个完整插件：

| 插件 | 内容 |
|------|------|
| `pr-review` | 3 个子代理（性能分析/安全评审/测试检查）+ 3 个命令 + 预评审 Hook + GitHub MCP 配置 |
| `devops-automation` | 3 个子代理（告警分析/部署专员/事故指挥）+ 4 个命令 + 部署前后 Hook + Kubernetes MCP 配置 |
| `documentation` | 3 个子代理 + 4 个文档命令 + MCP 配置 + 文档模板 |

插件结构有一个元数据文件加若干功能目录，`pr-review` 的 `plugin.json` 一共六行：

```json
{
  "name": "pr-review",
  "version": "1.0.0",
  "description": "Complete PR review workflow with security, testing, and docs",
  "author": {
    "name": "Anthropic"
  },
  "license": "MIT"
}
```

安装一条命令：`/plugin install pr-review`。想给团队沉淀一套标准化工作流时，插件是比"每人复制一堆文件"干净得多的载体。

---

## 三、组合成工作流：三个官方案例

单看每个模块都是零件，指南真正的卖点是组合。README 给了三个端到端案例：

**自动代码评审**（Slash Commands + Subagents + Memory + MCP）：输入 `/review-pr` 后，Claude 先加载项目记忆里的编码规范，通过 GitHub MCP 拉取 PR，把评审委托给 `code-reviewer` 子代理、测试检查委托给 `test-engineer` 子代理，最后汇总两路结果输出综合评审。

**自动文档生成**（Skills + Subagents + Memory）：你说"给 auth 模块生成 API 文档"，Claude 加载项目记忆中的文档标准，识别出这是文档生成请求后自动调用 `doc-generator` 技能，再把具体写作委托给 `api-documenter` 子代理，产出带示例的完整文档。

**DevOps 部署**（Plugins + MCP + Hooks）：输入 `/deploy production`，pre-deploy Hook 先验证环境，`deployment-specialist` 子代理经 Kubernetes MCP 执行部署，post-deploy Hook 做健康检查，全程不需要人盯着。

三个案例的共同结构值得注意：Memory 定规范，MCP 连外部系统，Subagents 干专职活，Hooks 守边界——每个零件都在自己最擅长的位置。

---

## 四、settings.json 配置速查

`09-advanced-features/config-examples.json` 提供 11 个场景的完整配置。挑三个最有代表性的：

**日常开发**——自动接受编辑，命令白名单放行，写文件后自动格式化：

```json
{
  "model": "claude-sonnet-5",
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": ["Bash(npm run *)", "Bash(git diff:*)", "Bash(git status:*)"]
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/format-and-lint.sh" }
        ]
      }
    ]
  }
}
```

**生产运维**——每步确认，硬禁危险命令，提交前置检查，开文件检查点：

```json
{
  "model": "claude-opus-5",
  "permissions": {
    "defaultMode": "manual",
    "deny": ["Bash(git push --force*)", "Bash(rm -rf*)"]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/pre-commit.sh" }
        ]
      }
    ]
  },
  "fileCheckpointingEnabled": true
}
```

**安全审计**——plan 只读模式拉满推理投入，读文件后自动扫安全：

```json
{
  "model": "claude-opus-5",
  "permissions": {
    "defaultMode": "plan"
  },
  "env": {
    "CLAUDE_CODE_EFFORT_LEVEL": "max"
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          { "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/security-scan.sh" }
        ]
      }
    ]
  }
}
```

对照着看规律很清楚：权限用 `allow`/`deny` 规则列表控制，行为靠挂在不同事件上的 Hook 调整，`defaultMode` 决定人机分工的松紧。其余 8 个场景（学习模式、CI/CD、结对编程、大型重构、自主开发 + 沙箱等）都在同一个文件里，按需取用。

---

## 五、快速开始

15 分钟体验核心功能：

```bash
# 1. 克隆指南
git clone https://github.com/luongnv89/claude-howto.git
cd claude-howto

# 2. 复制第一个斜杠命令
mkdir -p /path/to/your-project/.claude/commands
cp 01-slash-commands/optimize.md /path/to/your-project/.claude/commands/

# 3. 在 Claude Code 里输入 /optimize 试试

# 4. 配置项目记忆
cp 02-memory/project-CLAUDE.md /path/to/your-project/CLAUDE.md

# 5. 安装一个技能
cp -r 03-skills/code-review-specialist ~/.claude/skills/
```

一小时的进阶配置：批量安装全部斜杠命令（`cp 01-slash-commands/*.md .claude/commands/`）、套用项目记忆模板、装上 `code-review-specialist` 技能，然后按学习路径把 Hooks、Subagents、MCP、Plugins 逐个补齐。

两个安装前的注意事项，来自 README：Claude Code 自 v2.1.113 起改为原生二进制分发（`npm install -g @anthropic-ai/claude-code` 仍然可用，原生二进制会作为可选依赖在首次运行时下载）；自 v2.1.116 起下载源固定为 `https://downloads.claude.ai/claude-code-releases`，企业内网代理需要把这个域名加进白名单。

---

## 六、离线阅读与工程化质量

这个仓库对自己也挺严格：

- **EPUB 离线版**：`uv run scripts/build_epub.py` 一键生成包含全部内容和渲染后 Mermaid 图的电子书；
- **测试基建**：Python 单元测试（pytest，覆盖 3.10-3.12）+ Ruff lint + Bandit 安全扫描 + mypy 类型检查 + Codecov 覆盖率，每次 push 自动跑；
- **多语言**：英/越/中/乌/日五语版本，`zh/` 目录是完整中文翻译；
- **延伸资源**：README 推荐了 Claude Code 创造者 Boris Cherny 的工作流推文（并行子代理、共享 CLAUDE.md、Plan 模式、验证钩子）和作者自己的 Medium 博客。

一个教学仓库配上完整的 CI 和多语言翻译，维护者在认真做长期项目，不是蹭一波热度。

---

## 相关链接

- 🌐 仓库：https://github.com/luongnv89/claude-howto
- 🏠 配套官网：http://luongnv.com/claude-howto/
- 📖 学习路径：https://github.com/luongnv89/claude-howto/blob/main/LEARNING-ROADMAP.md
- 📚 功能目录：https://github.com/luongnv89/claude-howto/blob/main/CATALOG.md
- 🧪 快速参考：https://github.com/luongnv89/claude-howto/blob/main/QUICK_REFERENCE.md
- 🗂️ 全站索引：https://github.com/luongnv89/claude-howto/blob/main/INDEX.md
- ✍️ 作者博客：https://medium.com/@luongnv89

---

## 参考来源与口径说明

- 本文数据（Stars 41,620、Forks 5,111、Commits 248、贡献者 24）来自 GitHub API，2026-09-22 读数；指南版本口径 v2.1.278 取自仓库 README 徽章与 FAQ（2026 年 9 月，对齐 Claude Code 2.1.278），GitHub Releases 列表最新 tag 为 v2.1.160（2026-06-02 发布），两套版本号口径不同，正文取 README 口径。
- 十个模块的学习顺序、各档时长与目录对应关系，对照 README "Not Sure Where to Start?" 节的学习路径表；"学习顺序与目录编号不一致"是该表原文呈现方式（Checkpoints 的目录为 `08-checkpoints/`，学习顺序为第 3）。
- 文中全部配置与代码示例逐文件对照仓库源文件：斜杠命令对照 `01-slash-commands/optimize.md`，记忆模板对照 `02-memory/project-CLAUDE.md`，技能格式对照 `03-skills/code-review-specialist/SKILL.md`，子代理格式对照 `04-subagents/code-reviewer.md`，MCP 配置对照 `05-mcp/github-mcp.json`，Hook 配置与事件清单对照 `06-hooks/README.md`，插件结构对照 `07-plugins/pr-review/`，场景配置对照 `09-advanced-features/config-examples.json`（development / production / security_audit 三例均为原文节选）。
- Hooks 的"5 种类型、33 个事件分 4 类"计数对照 `06-hooks/README.md`（2026-09-22 版本）；技能 6 个、子代理 9 个、Hook 脚本 11 个按仓库目录实数，均多于 README 概览列出的条目数。
- Claude Code 安装方式变更（v2.1.113 原生二进制、v2.1.116 下载源）转述自 README "Get Started in 15 Minutes" 节的安装注记。
- 各模块 README 均标注官方文档出处与核对用的 Claude Code 版本号；工作流三案例为 README "Example Workflows" 节原文归纳。

---

*🦞 每日 08:00 自动更新*
