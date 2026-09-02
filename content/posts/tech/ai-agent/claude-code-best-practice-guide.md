---
title: "Claude Code 最佳实践大全：高热度 AI 编程指南解读"
date: "2026-03-28T20:00:00+08:00"
lastmod: 2026-04-03T23:33:16+08:00
slug: "claude-code-best-practice-guide"
github_repo: "shanraisshan/claude-code-best-practice"
aliases:
  - /posts/tech/claude-code-best-practice-guide/
description: "梳理 shanraisshan/claude-code-best-practice 仓库：Claude Code 的核心概念、配置结构、工作流组织方式、扩展边界与团队落地建议。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "AI 编程", "Anthropic", "最佳实践"]
---

# Claude Code 最佳实践大全：高热度 AI 编程指南解读

[Claude Code Best Practice](https://github.com/shanraisshan/claude-code-best-practice) 是 GitHub 上 Claude Code 实践资料最集中的仓库之一（31.4k Stars）。它既不是官方手册，也不是入门教程，它解决的是 Claude Code 使用里的一个实际问题：概念多、配置项杂、新特性更新快，开发者容易在功能名词里绕晕。

下面按三条主线梳理这个仓库：概念分层（Subagents、Commands、Skills、Hooks、MCP、Plugins 各自管什么）、配置地图（`.claude/` 目录结构）、实战路径（从个人配置到团队规范）。

## 一、项目概览

### 这个仓库里有什么

[Claude Code Best Practice](https://github.com/shanraisshan/claude-code-best-practice) 由开发者 **shanraisshan** 创建和维护，被 Boris Cherny（Anthropic 前员工、TypeScript 专家）在 X 上多次推荐，曾在 GitHub Trending 上获得 **#1 Repository Of The Day**。

**仓库规模**：31.4k+ Stars，2.8k+ Forks，MIT 许可证。

仓库内容覆盖这几个方向：

- **概念澄清**：Subagents、Commands、Skills、Hooks 等容易混淆的概念，分别说明各自的触发方式、上下文策略和适用场景
- **配置示例**：可以直接复用的 `.claude/` 配置文件，覆盖 settings、rules、agents、commands、skills、hooks 等目录
- **开发工作流**：对比 Superpowers、Spec Kit、BMAD-METHOD 等六套主流 AI 开发方法论
- **新特性汇总**：梳理 Auto Mode、Channels、Agent Teams、GitHub Actions 等持续演进的 beta 能力

## 二、核心概念体系

Claude Code 的功能扩展围绕几个核心模块展开：Subagents、Commands、Skills、Hooks、MCP 和 Plugins。下面逐个说明各自管什么、放在哪里、什么时候用。

### Subagents（子代理）

Subagent 在全新隔离上下文中运行，拥有自己的工具、权限、模型、记忆和持久身份。

**文件位置**：`.claude/agents/<name>.md`

**与 Command 的关键区别**：Subagent 启动时会创建独立的上下文副本，主会话不会受到子代理操作的影响；Command 则直接把提示词注入当前上下文，所有操作共享同一个会话状态。

适用场景：
- 需要并行执行多个互不干扰的独立任务
- 需要在隔离环境中运行敏感操作
- 需要保持任务状态的独立性

### Commands（命令）

Command 是注入到当前上下文的提示词模板，用户通过 `/command-name` 主动调用。

**文件位置**：`.claude/commands/<name>.md`

与 Subagent 相反，Command 共享当前上下文，适合快速执行单一操作，不需要隔离状态。

| 特性 | Subagent | Command |
|------|----------|---------|
| 上下文 | 全新隔离上下文 | 共享现有上下文 |
| 调用方式 | 主代理按需唤起 | `/command-name` 手动调用 |
| 适用场景 | 复杂独立任务 | 简单工作流 |
| 状态隔离 | 完全隔离 | 共享状态 |

### Skills（技能）

Skill 是一个高度可配置的知识模块，Claude Code 会自动发现并加载它。与 Command 不同，Skill 支持上下文分叉（在主上下文副本中运行，互不影响）和渐进式披露（按需逐步提供信息，避免上下文溢出）。

**文件位置**：`.claude/skills/<name>/SKILL.md`

**关键属性**：
- 可配置（Configurable）：参数可自定义
- 可预加载（Preloadable）：可设置预加载行为
- 可自动发现（Auto-discoverable）：Claude Code 自动识别

Claude Code 官方维护了一系列预置 Skills，存放在 [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills) 仓库中。

一个 Skill 的最小结构是 `.claude/skills/<name>/SKILL.md`，顶部用 YAML frontmatter 声明元数据：

```markdown
---
name: security-review
description: 在隔离上下文中对代码做安全审查，适合 PR 合并前调用
---

# Security Review

按以下步骤审查传入的代码：……（正文描述指挥模型如何一步步执行）
```

`description` 是模型判断"何时该加载这个 Skill"的依据，要写成可判断的触发条件（"适合 PR 合并前调用"），而不是一句功能口号（"提供安全能力"）。

### Hooks（钩子）

Hook 在智能体循环外部运行，由特定事件触发。事件发生时，可以执行脚本、发起 HTTP 请求、注入提示词或启动子代理。

**文件位置**：`.claude/hooks/`

**事件类型**：

| 事件 | 说明 | 常见用途 |
|------|------|----------|
| `PreToolUse` | 工具使用前触发 | 拦截危险命令、记录操作日志 |
| `PostToolUse` | 工具使用后触发 | 校验工具输出、落盘审计 |
| `UserPromptSubmit` | 用户提交提示词时触发 | 注入额外上下文、做关键词拦截 |
| `Stop` | 一轮智能体循环结束时触发 | 汇总本轮 token 消耗、通知外部系统 |

> 说明：事件名以 PascalCase 或 kebab-case 书写均可，例如 `PreToolUse` 与 `pre-tool-use` 指同一事件；优先级 `PreToolUse` 高于 `PostToolUse`，同一个事件可挂多个 Hook，按在 `settings.json` 中的声明顺序依次执行。

**使用示例**：

```javascript
// .claude/hooks/pre_tool_use.js
// 导出的事件函数名必须与事件一致（PascalCase），参数为对象解构
export async function PreToolUse({ tool_name }) {
  console.error(`[pre-tool-use] ${tool_name}`);
  return {}; // 返回空对象表示不拦截，放行工具调用
}
```

### MCP（模型上下文协议）

MCP 通过外部独立进程的方式扩展 Claude Code 的能力。与 Plugin 的区别在于：MCP 解决的是"连接"问题——让 Claude Code 能调用外部工具；Plugin 解决的是"分发"问题——让配置和技能可以打包分享。

**配置位置**：`.claude/settings.json` 中的 `mcpServers` 字段

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
    }
  }
}
```

### Plugins（插件）

Plugin 是 Claude Code 的打包分发单元，把一组配置（Commands、Skills、MCP 配置、Rules 等）打包成一个模块，通过 `claude plugins install` 安装。适合团队内部共享实践。

### 概念之间的关系

```text
User invokes /command
        ↓
    Command loads
    (prompt template)
        ↓
    May spawn Agent
    (isolated context)
        ↓
    Agent uses Skill
    (reusable capability)
```

把六个模块放进一张心智地图会更清楚：`Hooks` 横切整个循环，在事件边界上做拦截与记录；`MCP` 与 `Plugins` 属于扩展层，一个管"连外部工具"，一个管"打包分发实践"；真正驱动对话推进的是 `Command → Subagent → Skill` 这条主线。

## 三、配置与个性化

### 配置文件层级

Claude Code 的配置要分清两个维度：**设置（settings）** 与 **上下文（context）**，二者的合并规则不同，混在一起极易踩坑。

**设置（settings.json）** 按优先级从高到低合并，高优先级的同名键覆盖低优先级：

1. **CLI 参数**：启动时通过 `--flag` 临时传入，优先级最高
2. **项目级** `./.claude/settings.json`：随仓库分发，团队共享
3. **用户级** `~/.claude/settings.json`：开发者本机偏好

**上下文（context）** 负责告诉模型"这个项目是什么"，按加载顺序拼接：

1. **CLAUDE.md**：项目根目录描述文件，写清结构、技术栈、编码规范；层级越深的子目录会先于父目录加载
2. **`./.claude/rules/*.md`**：规则文件，追加到 CLAUDE.md 之后，共同构成初始系统提示词

> 常见误区：把 `CLAUDE.md` 和 `settings.json` 当作同一种优先级排序。实际上一个提供"项目背景"，一个提供"运行配置"，互不覆盖。

### 一个 CLAUDE.md 示例

```markdown
# Project: my-service

技术栈：Python 3.12 + FastAPI + PostgreSQL

## 目录结构
- `app/`    业务逻辑
- `tests/`  单元测试

## 编码规范
- 单行不超过 100 字符
- 提交前必须运行 `uv run pytest`
- 修改 API 需同步更新 `openapi.yaml`

## 协作约定
需要把指定文件带进当前上下文时，直接用 @ 提及，例如："读取 @app/main.py 后开始重构"。
```

好的 `CLAUDE.md` 只写"稳定不变"的信息——结构、技术栈、硬性规范。那些一周一变的信息（某功能改到哪一步了）不该放这里，否则每次对话都在消耗宝贵的上下文预算。

### 目录结构

```text
.claude/
├── agents/          # 子代理定义
├── commands/        # 命令模板
├── hooks/           # 事件钩子
├── skills/          # 技能模块
├── rules/           # 规则文件
├── memory/          # 持久记忆
└── settings.json    # 全局设置
```

## 四、开发工作流对比

以下是六套主流 AI 开发方法论的简要对比：

| 工作流 | 核心理念 | 独特组件 |
|--------|----------|----------|
| Superpowers | 结构化提示词模板 | 多层提示词体系 |
| Spec Kit | 先写规格说明，再生成代码 | 规格驱动开发 |
| BMAD-METHOD | 分阶段执行（分析→设计→实现） | 渐进式交付 |
| Research → Plan → Execute → Review → Ship | 线性流水线 | 质量控制节点 |
| Ralph Wiggum Loop | 自主迭代 | 循环验证 |
| Spec Drift | 反模式识别 | 变更追踪 |

## 五、编排工作流详解

### 一次代码审查如何流过系统

以 GitHub PR 审查为例，看 Commands、Subagents、Skills 和 Hooks 如何协同：

1. 用户在 Claude Code 中输入 `/review-pr #42`，触发 `review-pr` Command
2. Command 的提示词模板定义了审查步骤：拉取 diff → 安全检查 → 风格检查 → 生成报告
3. Command 启动三个 Subagent 并行工作：一个检查安全漏洞、一个检查代码风格、一个跑回归测试——每个子代理拥有独立上下文，互不干扰
4. 安全审查 Subagent 加载 `security-review` Skill，在隔离上下文中扫描代码
5. 每个 Subagent 使用工具前，Hook（`pre-tool-use`）记录操作日志
6. 三个 Subagent 完成后，主会话汇总结果，生成审查报告

这里能看出 Subagent 和 Skill 的分工：Subagent 提供隔离的执行环境，Skill 提供可复用的审查能力；同一个 Skill 可以被不同的 Subagent 加载使用。

### 如何自定义编排

1. **创建 Command**：在 `.claude/commands/` 中定义
2. **创建 Subagent**：在 `.claude/agents/` 中定义
3. **创建 Skill**：在 `.claude/skills/` 中定义
4. **组合使用**：通过 Command 调用 Subagent，Subagent 使用 Skill

## 六、实战建议

### 个人开发者：从哪里开始

**第一周**：先把项目上下文固定下来。在项目根目录创建 `CLAUDE.md`，描述项目结构、技术栈和编码规范。再在 `.claude/rules/` 里放几条规则——比如"提交前必须跑 lint"。这一步不需要理解任何高级概念，做完马上能看到效果。

**第二周**：挑一个高频操作做成 Command。比如 `/review` 命令用于代码审查，`/deploy` 命令用于部署。Commands 不需要独立上下文，学习成本最低。

**一个月内**：评估是否需要 Subagent 或 Skill。判断标准：如果你发现自己反复对 Claude Code 描述同一段背景信息，就该把它写成 Skill；如果某个任务需要隔离运行且不影响主会话，就该用 Subagent。

### 团队负责人：从规范到资产

**第一步：统一上下文入口**。把 `CLAUDE.md` 和各语言规则放入团队仓库的 `.claude/` 目录。新成员克隆仓库后，Claude Code 自动加载团队的上下文规范，不需要口头传授。

**第二步：建立校验机制**。配置 Hooks（如 `pre-tool-use` 记录日志、`post-tool-use` 校验输出），让每次操作可追溯。如果有 CI 流水线，用 GitHub Actions 做 PR 自动审查。

**第三步：打包成可复用资产**。当多个项目需要同一套审查流程或部署脚本时，把它们做成 Plugin，通过内部市场分发。这时才需要考虑 MCP 连接外部工具（如 Slack、Jira）和 Agent Teams 并行开发。

### 什么时候不要急着上

- **Agent Teams** 仍处于 beta，并行代理的协调成本不低。等团队单个代理的使用已经稳定，再引入多代理。
- **Channels 远程触发** 适合已有自动化体系的小团队。如果日常工作还在手动执行，先理顺本地工作流。
- **Plugins 打包分发** 适合跨项目复用场景。个人开发者或单项目团队暂时不需要。

### 安全与性能

| 场景 | 建议 |
|------|------|
| 公开仓库 | 使用 Auto Mode，定期审查 |
| 敏感代码 | 使用 Manual Mode，逐项审批 |
| 自动化任务 | 使用 Scheduled Tasks，记录日志 |
| 外部集成 | 使用 MCP，设置最小权限 |

| 优化项 | 方法 |
|--------|------|
| 上下文管理 | 使用 Checkpointing 避免上下文溢出 |
| 并行执行 | 使用 Agent Teams 加速独立任务 |
| 成本控制 | 使用 Status Line 监控 Token 使用 |
| 长任务 | 使用 Ralph Wiggum Loop 自主迭代 |

### 相关资源

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/shanraisshan/claude-code-best-practice |
| Claude Code 文档 | https://code.claude.com/docs |
| 官方 Skills | https://github.com/anthropics/skills |