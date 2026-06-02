---
title: "Claude Code 最佳实践大全：高热度 AI 编程指南解读"
date: "2026-03-28T20:00:00+08:00"
lastmod: 2026-04-03T23:33:16+08:00
slug: "claude-code-best-practice-guide"
aliases:
  - /posts/tech/claude-code-best-practice-guide/
description: "深度解读 shanraisshan/claude-code-best-practice 仓库，系统梳理 Claude Code 的核心概念、工作流组织方式、配置结构、扩展边界与团队落地建议。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "AI编程", "Anthropic", "最佳实践", "Agent工作流"]
---

# Claude Code 最佳实践大全：高热度 AI 编程指南解读

> **目标读者**：希望系统掌握 Claude Code 最佳实践、提升 AI 编程效率的开发者
> **前置知识**：了解 Claude Code 基础用法、有编程经验
> **预计阅读时间**：25 分钟 | **难度**：⭐⭐⭐

---

## 这篇文章在做什么

[Claude Code Best Practice](https://github.com/shanraisshan/claude-code-best-practice) 是 GitHub 上 Claude Code 实践资料最集中的仓库之一（31.4k Stars）。它不是官方手册，也不是入门教程——它真正解决的问题是：Claude Code 概念多、配置项杂、新特性更新快，开发者容易迷失在功能名词里。

这篇文章不会把仓库内容逐页翻译，而是按三条主线帮你建立判断框架：
1. **概念分层**：Subagents、Commands、Skills、Hooks、MCP、Plugins 各自管什么，什么时候用哪个
2. **配置地图**：`.claude/` 目录下的 settings、rules、memory、hooks 如何组织
3. **实战路径**：从个人配置到团队规范，先做什么、后做什么

如果你已经有 Claude Code 使用经验，但配置还散落在各处，这篇文章能帮你把零散操作收敛成一套可维护的工作方法。

### 概念地图

```
┌─────────────────────────────────────────────────────┐
│                    Claude Code                        │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  Subagents  │  │  Commands   │  │   Skills    │  │
│  │  (Agent)    │  │  (Command)  │  │  (Skill)    │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│        ↑               ↑               ↑            │
│    独立上下文      注入现有上下文    可配置、可预加载    │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   Hooks     │  │    MCP      │  │   Plugins   │  │
│  │  (钩子)      │  │  (协议)     │  │  (插件)      │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│   事件触发        外部工具连接      可分发的功能包      │
└─────────────────────────────────────────────────────┘
```

## 学习目标

完成本文后，你应该能够：

1. **说出这个仓库在 Claude Code 生态中的位置**：不是官方手册，也不是入门教程，而是方法地图
2. **区分六个关键概念的边界**：Subagents、Commands、Skills、Hooks、MCP、Plugins 各自管什么范围
3. **判断哪些特性适合现在就用**：区分稳定收益项、进阶组合项和时间敏感的新特性
4. **把知识迁移到自己的项目**：个人开发者和团队负责人分别从什么模块开始落地

---

## 目录

- [一、项目概览](#一项目概览)
- [二、核心概念体系](#二核心概念体系)
- [三、配置与个性化](#三配置与个性化)
- [四、新兴特性](#四新兴特性)
- [五、开发工作流对比](#五开发工作流对比)
- [六、编排工作流详解](#六编排工作流详解)
- [七、实战建议](#七实战建议)
- [八、常见问题](#八常见问题)
- [九、落地建议](#九落地建议)
- [十、自测清单](#十自测清单)
- [十一、实战练习](#十一实战练习)

---

## 一、项目概览

### 这个仓库里有什么

[Claude Code Best Practice](https://github.com/shanraisshan/claude-code-best-practice) 由开发者 **shanraisshan** 创建和维护，被 Boris Cherny（Anthropic 前员工、TypeScript 专家）在 X 上多次推荐，曾在 GitHub Trending 上获得 **#1 Repository Of The Day**。

**仓库规模**：

| 指标 | 数值 |
|------|------|
| GitHub Stars | 31.4k+ |
| Forks | 2.8k+ |
| Open Issues | 3 |
| 许可证 | MIT |

仓库内容覆盖这几个方向：

- **概念澄清**：Subagents、Commands、Skills、Hooks 等容易混淆的概念，分别说明各自的触发方式、上下文策略和适用场景
- **配置示例**：可以直接复用的 `.claude/` 配置文件，覆盖 settings、rules、agents、commands、skills、hooks 等目录
- **开发工作流**：对比 Superpowers、Spec Kit、BMAD-METHOD 等六套主流 AI 开发方法论，给出各自的核心理念和独特组件
- **新特性汇总**：梳理 Auto Mode、Channels、Agent Teams、GitHub Actions 等持续演进的 beta 能力

### 不适合做什么

这类仓库适合用来建立方法地图，但不适合把全部配置直接"整包复制"进项目。更稳妥的用法：

1. 先理解概念边界
2. 挑 1 到 2 个收益最高的模块做最小迁移
3. 根据项目实际情况决定要不要团队化、插件化

---

## 二、核心概念体系

Claude Code 的功能体系可以分为**三个层次**和**若干扩展模块**。

### 概念层次总览

```
┌─────────────────────────────────────────────────────┐
│                    Claude Code                        │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  Subagents  │  │  Commands   │  │   Skills    │  │
│  │  (Agent)    │  │  (Command)  │  │  (Skill)    │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│        ↑               ↑               ↑            │
│    独立上下文      注入现有上下文    可配置、可预加载    │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   Hooks     │  │    MCP      │  │   Plugins   │  │
│  │  (钩子)      │  │  (协议)     │  │  (插件)      │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│   事件触发        外部工具连接      可分发的功能包      │
└─────────────────────────────────────────────────────┘
```

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
| 调用方式 | 代码中调用 | `/command-name` |
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

### Hooks（钩子）

Hook 在智能体循环外部运行，由特定事件触发。事件发生时，可以执行脚本、发起 HTTP 请求、注入提示词或启动子代理。

**文件位置**：`.claude/hooks/`

**事件类型**：

| 事件 | 说明 |
|------|------|
| `pre-tool-use` | 工具使用前触发 |
| `post-tool-use` | 工具使用后触发 |
| `on-conversation-start` | 对话开始时触发 |
| `on-conversation-end` | 对话结束时触发 |

**使用示例**：

```javascript
// .claude/hooks/pre-tool-use.js
export const preToolUse = async (tool, args) => {
  console.log(`About to use tool: ${tool}`);
  return { tool, args };
};
```

### MCP Servers（模型上下文协议服务器）

MCP（Model Context Protocol）用于连接外部工具、数据库和 API，通过 `.mcp.json` 或 `.claude/settings.json` 配置。

**文件位置**：`.claude/settings.json` 或 `.mcp.json`

**典型用途**：
- 连接外部工具（GitHub、Slack 等）
- 连接数据库（PostgreSQL、MySQL 等）
- 调用外部 API（REST、GraphQL 等）

**配置示例**：

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

Plugin 把 Skills、Subagents、Hooks 和 MCP 服务器打包成一个可分发的单元，可以发布到插件市场供他人使用。

---

## 三、配置与个性化

### Settings（设置系统）

Claude Code 采用**分层配置系统**，支持多种配置级别。

**文件位置**：`.claude/settings.json`

**配置层级**（从高到低）：

1. 命令行标志（CLI Flags）
2. 项目级设置（`.claude/settings.json`）
3. 用户级设置（`~/.claude/settings.json`）
4. 系统级设置

**可配置项**：

| 配置项 | 说明 |
|--------|------|
| Permissions | 权限模式（允许/拒绝/自动） |
| Model Config | 模型配置（温度、最大令牌等） |
| Output Styles | 输出样式（简洁/详细/格式化） |
| Sandboxing | 沙箱模式 |
| Keybindings | 键盘快捷键 |
| Fast Mode | 快速模式 |

### Status Line（状态栏）

**概念**：Status Line 是**可自定义的状态栏**，显示上下文使用量、模型、成本和会话信息。

**显示信息**：

- 上下文使用量（Token 计数）
- 当前模型
- 本次会话成本
- 会话时长
- 并行任务数

### Memory（记忆系统）

Claude Code 的记忆系统通过**多个层面**实现持久上下文。

**记忆存储位置**：

| 位置 | 说明 | 优先级 |
|------|------|--------|
| `CLAUDE.md` | 项目根目录的指令文件 | 最高 |
| `.claude/rules/` | 规则文件夹 | 高 |
| `~/.claude/rules/` | 用户级规则 | 中 |
| `~/.claude/projects/<project>/memory/` | 项目级记忆 | 中 |

**@path 导入**：

```markdown
使用 @path/to/file 可以将任意文件内容导入上下文
```

**Rules（规则）**：

使用 `.claude/rules/` 组织规则文件，实现模块化管理。

---

## 四、新兴特性

### Auto Mode（自动模式）beta

**概念**：Auto Mode 是**后台安全分类器**，用 Claude 替代人工权限提示，自动判断操作是否安全。

**启动方式**：`--permission-mode auto`

**安全机制**：

- 阻止提示词注入（Prompt Injection）
- 阻止危险升级（Risky Escalations）
- 自动判断安全操作

**适用场景**：

- 信任的代码库
- 自动化工作流
- 快速原型开发

### Channels（通道）beta

**概念**：Channels 允许将**Telegram、Discord 或 Webhooks 的事件**推送到运行中的 Claude Code 会话。

**特点**：

- 你离开时 Claude 也能响应
- 支持远程触发任务
- 基于插件架构

### Code Review（代码审查）beta

**概念**：Code Review 是**多代理 PR 分析工具**，能捕捉 bug、安全漏洞和回归问题。

**特点**：

- 多代理并行分析
- 自动识别问题类型
- 与 GitHub 集成

### GitHub Actions

**概念**：在 CI/CD 流水线中**自动化 PR 审查、Issue 分类和代码生成**。

### Chrome（浏览器自动化）beta

**概念**：通过 Claude 在 Chrome 中**自动化浏览器操作**。

**功能**：

- 测试 Web 应用
- 调试控制台
- 自动填写表单
- 从页面提取数据

### Scheduled Tasks（定时任务）

| 命令 | 说明 | 运行位置 |
|------|------|----------|
| `/loop` | 本地循环执行（最长3天） | 本地机器 |
| `/schedule` | 云端定时执行（机器关闭也能运行） | Anthropic 云 |

### Agent Teams（代理团队）beta

**概念**：多个代理**在同一代码库上并行工作**，通过共享任务协调实现协作。

### Voice Dictation（语音输入）beta

**概念**：通过**按键说话**实现语音输入，支持 20 种语言。

**启动方式**：`/voice`

### Remote Control（远程控制）

**概念**：从**任何设备（手机、平板、浏览器）**继续本地会话。

**启动方式**：`/remote-control` 或 `/rc`

### Git Worktrees（Git 工作树）

**概念**：使用**隔离的 Git 分支进行并行开发**，每个代理获得独立的工作副本。

---

## 五、开发工作流对比

### 通用架构模式

所有主流工作流都遵循相同的架构：

```
Research → Plan → Execute → Review → Ship
```

### 六大工作流对比

| 工作流 | Stars | 核心理念 | 独特特性 |
|--------|-------|----------|----------|
| **Superpowers** | 118k | TDD-first | 铁律、整体计划审查 |
| **Everything Claude Code** | 111k | 本能评分 | AgentShield、多语言规则 |
| **Spec Kit** | 83k | 规范驱动 | 宪章模式、22+工具 |
| **gstack** | 52k | 角色人格 | 代码审查、并行冲刺 |
| **Get Shit Done** | 43k | 新鲜上下文 | 20万上下文、波执行 |
| **BMAD-METHOD** | 43k | 全周期 | 22+平台、代理人格 |

### Superpowers 详解（118k Stars）

**核心理念**：TDD-first（测试驱动开发优先）

**铁律（Iron Laws）**：

1. 先写测试，再写代码
2. 保持测试快速
3. 不提交未通过的测试

**工作流**：

1. 写计划 → 2. 审查计划 → 3. 写测试 → 4. 写代码 → 5. 重构 → 6. 审查

### Everything Claude Code 详解（111k Stars）

**核心理念**：本能评分（Instinct Scoring）

**核心组件**：

- `instinct scoring`：本能评分系统
- `AgentShield`：代理安全防护
- `multi-lang rules`：多语言规则

### Get Shit Done 详解（43k Stars）

**核心理念**：新鲜大上下文 + Wave Execution（波次执行）

**独特特性**：

- 200k Token 上下文
- Wave Execution（波次执行）
- XML Plans（XML 格式计划）

---

## 六、编排工作流详解

### Command → Agent → Skill 模式

Claude Code 的编排工作流遵循 **Command → Agent → Skill** 的层级模式：

```
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

### 一次代码审查如何流过系统

以 GitHub PR（Pull Request）审查为例，看 Commands、Subagents、Skills 和 Hooks 如何协同：

1. 用户在 Claude Code 中输入 `/review-pr #42`，触发 `review-pr` Command
2. Command 的提示词模板定义了审查步骤：拉取 diff → 安全检查 → 风格检查 → 生成报告
3. Command 启动三个 Subagent 并行工作：一个检查安全漏洞、一个检查代码风格、一个跑回归测试——每个子代理拥有独立上下文，互不干扰
4. 安全审查 Subagent 加载 `security-review` Skill，在隔离上下文中扫描代码
5. 每个 Subagent 使用工具前，Hook（`pre-tool-use`）记录操作日志
6. 三个 Subagent 完成后，主会话汇总结果，生成审查报告

这个流程展示了 Subagent 和 Skill 的典型区别：Subagent 提供隔离的执行环境，Skill 提供可复用的审查能力；同一个 Skill 可以被不同的 Subagent 加载使用。

### 如何自定义编排

1. **创建 Command**：在 `.claude/commands/` 中定义
2. **创建 Subagent**：在 `.claude/agents/` 中定义
3. **创建 Skill**：在 `.claude/skills/` 中定义
4. **组合使用**：通过 Command 调用 Subagent，Subagent 使用 Skill

---

## 七、实战建议

### 新手入门路径

**第一阶段（1-2天）**：

1. 安装 Claude Code，阅读官方文档
2. 尝试基本操作：读写文件、运行命令
3. 体验 `/voice` 语音输入
4. 体验 `/help` 获取帮助

**第二阶段（3-7天）**：

1. 配置 `.claude/settings.json`
2. 尝试 Subagents：创建简单子代理
3. 尝试 Commands：创建自定义命令
4. 体验 Hooks：添加简单的预工具钩子

**第三阶段（长期）**：

1. 构建个人 Skills 库
2. 配置 MCP Servers 连接常用工具
3. 探索 Agent Teams 并行开发
4. 研究适合自己的开发工作流

### 团队采用建议

**第一步：制定规范**

- 确定哪些操作需要人工审批
- 定义提交消息格式
- 制定 Code Review 流程

**第二步：配置共享**

- 在团队仓库中创建 `.claude/` 配置
- 使用 Rules 组织团队规范
- 共享常用的 Commands 和 Skills

**第三步：CI/CD 集成**

- 配置 GitHub Actions 自动审查
- 使用 Scheduled Tasks 自动化报告
- 建立质量门禁

### 安全最佳实践

| 场景 | 建议 |
|------|------|
| 公开仓库 | 使用 Auto Mode，定期审查 |
| 敏感代码 | 使用 Manual Mode，逐项审批 |
| 自动化任务 | 使用 Scheduled Tasks，记录日志 |
| 外部集成 | 使用 MCP，设置最小权限 |

### 性能优化

| 优化项 | 方法 |
|--------|------|
| 上下文管理 | 使用 Checkpointing（检查点）避免上下文溢出 |
| 并行执行 | 使用 Agent Teams 加速独立任务 |
| 成本控制 | 使用 Status Line 监控 Token 使用 |
| 长任务 | 使用 Ralph Wiggum Loop 自主迭代 |

---

## 八、常见问题

### Q1：这个仓库最适合当"教程"还是"模板库"？

它是方法与模板的结合体。如果只当模板库用，容易复制配置却不理解边界；如果只当教程读，会错过大量可直接迁移的资产。建议先读概念部分，再按需取用配置。

### Q2：我应该一开始就用上 Subagents、Hooks、Plugins 吗？

不建议。更合理的顺序：先固定项目上下文（CLAUDE.md、rules），再固定高频命令（Commands），然后引入最有收益的 Skills 或 Subagents。只有工作流已经稳定、需要团队复用时，再考虑打包和编排。

### Q3：为什么文章里没有把所有新特性都标成"立即可用"？

高热度仓库经常覆盖时间敏感能力，版本演进快。文档需要帮读者建立判断，而不是把每个热词都当成稳定能力推荐。beta 标记和演进速度本身也是判断素材。

### Q4：对于团队负责人，这个仓库最大的价值是什么？

不是"知道更多功能名词"，而是学会把个人经验沉淀为共享的 `.claude/` 资产。团队在上下文入口、命令入口、校验规则和分工上形成一致的工作流，比每个人各用各的配置更可靠。

---

## 九、落地建议

### 个人开发者：从哪里开始

**第一周**：先把项目上下文固定下来。在项目根目录创建 `CLAUDE.md`，描述项目结构、技术栈和编码规范。再在 `.claude/rules/` 里放几条规则——比如"提交前必须跑 lint"。这一步不需要理解任何高级概念，收益立竿见影。

**第二周**：挑一个高频操作做成 Command。比如 `/review` 命令用于代码审查，`/deploy` 命令用于部署。Commands 不需要独立上下文，学习成本最低。

**一个月内**：评估是否需要 Subagent 或 Skill。判断标准很简单——如果你发现自己反复对 Claude Code 描述同一段背景信息，就该把它写成 Skill；如果某个任务需要隔离运行且不影响主会话，就该用 Subagent。

### 团队负责人：从规范到资产

**第一步：统一上下文入口**。把 `CLAUDE.md` 和各语言规则放入团队仓库的 `.claude/` 目录。新成员克隆仓库后，Claude Code 自动加载团队的上下文规范，不需要口头传授。

**第二步：建立校验机制**。配置 Hooks（如 `pre-tool-use` 记录日志、`post-tool-use` 校验输出），让每次操作可追溯。如果有 CI 流水线，用 GitHub Actions 做 PR 自动审查。

**第三步：沉淀为可复用资产**。当多个项目需要同一套审查流程或部署脚本时，把它们打包成 Plugin，通过内部市场分发。这时才需要考虑 MCP 连接外部工具（如 Slack、Jira）和 Agent Teams 并行开发。

### 什么时候不要急着上

- **Agent Teams** 仍处于 beta，并行代理的协调成本不低。等团队单个代理的使用已经稳定，再引入多代理。
- **Channels 远程触发** 适合已有自动化体系的小团队。如果日常工作还在手动执行，先理顺本地工作流。
- **Plugins 打包分发** 适合跨项目复用场景。个人开发者或单项目团队暂时不需要。

### 相关资源

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/shanraisshan/claude-code-best-practice |
| Claude Code 文档 | https://code.claude.com/docs |
| 官方 Skills | https://github.com/anthropics/skills |

---

## 十、自测清单

用这份清单检验你对 Claude Code 核心概念的掌握程度。每项只有能用自己的话说清楚才算通过——只记得名词不算。

### 概念边界

- [ ] 能说清 Subagent 和 Command 在上下文策略上的根本区别
- [ ] 能举出一个该用 Skill 而非 Command 的典型场景
- [ ] 能解释 Hook 为什么运行在智能体循环外面，以及四个事件类型各适合干什么
- [ ] 能区分 MCP 和 Plugin：一个管连接、一个管分发

### 配置体系

- [ ] 知道 `.claude/` 下各子目录的职责（agents、commands、skills、hooks、rules）
- [ ] 能按优先级高低列出配置的四个层级
- [ ] 能说清 `CLAUDE.md`、`.claude/rules/` 和 `~/.claude/rules/` 三者的区别和覆盖关系

### 编排与工作流

- [ ] 能画出 Command → Agent → Skill 的调用链，并在链上标出上下文策略
- [ ] 能拆解一次 PR 审查流程中，哪些环节该用 Subagent 并行、哪些该顺序执行
- [ ] 读完六大工作流对比后，能判断自己的项目最接近哪一种，并说出理由

### 落地决策

- [ ] 能为一个真实项目写出 `CLAUDE.md` 的关键内容（不是模板填空）
- [ ] 知道团队配置共享的前三步顺序，以及每一步的验收标准
- [ ] 能对 Auto Mode、Agent Teams、Channels 分别做出"现在就用 / 观望 / 暂不需要"的判断

### 安全与性能

- [ ] 能说清 Auto Mode 和 Manual Mode 各自适合什么仓库类型
- [ ] 知道至少两种控制上下文溢出的方法，并了解各自的代价
- [ ] 能为公开仓库和内部敏感项目分别制定一套权限策略（不只是"设成 auto"）

---

## 十一、实战练习

以下三个练习按难度递进，覆盖从个人配置到编排设计的完整路径。每个练习都附带明确的验收标准——不是为了完成步骤，是为了达到效果。

### 练习 1：建立项目上下文（30 分钟）

**目标**：让 Claude Code 准确理解一个现有项目，不再依赖你口头补充背景信息。

**适用水平**：读过本文概念部分即可。

**步骤**：

1. 选一个你熟悉的真实项目（不要拿 Hello World）
2. 在项目根目录创建 `CLAUDE.md`，至少写入：项目一句话描述、技术栈、顶层目录结构说明、三条以上编码约定
3. 在 `.claude/rules/` 下创建 2–3 条规则文件，每条规则描述一个具体约束（如"接口变更需同步更新文档""提交前跑 lint"）
4. 启动 Claude Code 会话，问："这个项目是做什么的？用了什么技术栈？有哪些编码约定？"
5. 检查：Claude Code 的回答是否准确反映了 CLAUDE.md 和 rules 中描述的内容

**验收标准**：启动新会话（不加额外提示），Claude Code 能准确描述项目用途、技术栈和三条以上编码规范。如果你发现它漏了某条规则——规则文件里写得太模糊，重写，再来一轮。

**常见坑**：CLAUDE.md 写得像 README 的摘要——把"是什么"写得很全，但缺少"怎么做"的约束。Claude 需要的是后者。

---

### 练习 2：创建代码审查 Command 和安全审查 Subagent（45 分钟）

**目标**：实现一个 `/review` 命令，能调用独立子代理并行审查代码。

**适用水平**：已完成练习 1，或已经配置过项目上下文。

**步骤**：

1. 在 `.claude/commands/` 下创建 `review.md`，定义审查提示词：至少覆盖安全检查、代码风格、逻辑完整性三个维度
2. 在 `.claude/agents/` 下创建 `security-reviewer.md`，这是一个专门检查安全漏洞的 Subagent。给它独立的工具权限和审查清单
3. 在 Command 的提示词中指定：安全维度交给 `security-reviewer` Subagent 处理，其余维度由主会话完成
4. 找一段包含安全问题的代码（比如硬编码密钥、SQL 注入风险），用 `/review` 审查它
5. 观察：安全类问题是否来自 Subagent？风格和逻辑问题是否来自主会话？

**验收标准**：

- `/review` 能正确触发安全 Subagent
- 审查结果中，安全问题和其他问题的来源可区分（通过日志或输出结构）
- 如果有 Hooks 记录日志，能在日志中看到 Subagent 的工具调用记录

**常见坑**：Command 提示词写成了任务列表而不是编排指令。Command 的核心不是"要做什么"——是"怎么拆、分给谁"。

---

### 练习 3：设计一个从 PR 到部署的编排工作流（60 分钟）

**目标**：综合使用 Command、Subagent、Skill 和 Hook，设计一套可复用的 PR 审查与部署编排流程。

**适用水平**：已完成练习 2，或已经单独使用过 Command 和 Subagent。

**步骤**：

1. 画一张流程图，标记出从"收到 PR"到"通过审查并部署"的完整链路
2. 在链路上标注每一步使用哪种机制（Command 做入口调度、Subagent 做并行审查、Skill 提供可复用能力、Hook 做事件拦截）
3. 至少定义三个文件：
   - 一个入口 Command（如 `pr-pipeline.md`）
   - 一个 Subagent（如 `deploy-checker.md`，负责部署前校验）
   - 一个 Hook（如 `post-tool-use` 校验输出格式）
4. 选一个链路节点做实际验证：模拟一次 PR 提交，跑通从 Command 触发到 Subagent 完成审查的过程
5. 记录：哪些环节确实适合并行、哪些必须串行，以及你的判断依据

**验收标准**：

- 流程图中，并行节点和串行节点的区分有明确理由（不是"看起来可以并行"）
- 至少一个 Subagent 和 Hook 能在实际运行中协同工作
- 能说出这套流程不适合什么场景——不是万能答案

**没有标准答案**：不同项目对安全级别、部署频率、团队规模的要求不同，编排设计也会不同。重要的是你做出的取舍有依据，而不是抄了一个"最佳实践"。

---

*文档版本 1.4 | 更新日期：2026-06-02 | Stars: 31.4k*
