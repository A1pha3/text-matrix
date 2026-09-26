---
title: "Claude Code 最佳实践大全：高热度 AI 编程指南解读"
date: "2026-03-28T20:00:00+08:00"
lastmod: 2026-09-22T10:30:00+08:00
slug: "claude-code-best-practice-guide"
github_repo: "shanraisshan/claude-code-best-practice"
source_key: "gh:shanraisshan/claude-code-best-practice"
aliases:
  - /posts/tech/claude-code-best-practice-guide/
description: "梳理 shanraisshan/claude-code-best-practice 仓库：Claude Code 的核心概念、配置结构、工作流组织方式、扩展边界与团队落地建议。数据与机制核对至 2026 年 9 月。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "AI 编程", "Anthropic", "最佳实践"]
---

# Claude Code 最佳实践大全：高热度 AI 编程指南解读

[Claude Code Best Practice](https://github.com/shanraisshan/claude-code-best-practice) 是 GitHub 上 Claude Code 实践资料最集中的仓库之一（66.2k Stars，2026 年 9 月数据）。仓库自我定位是 "from vibe coding to agentic engineering"——从随手对话式写代码，走向把 Claude Code 当作一个可编排的工程系统来用。它解决的是使用里的一个实际问题：概念多、配置项杂、新特性更新快，开发者容易在功能名词里绕晕。

下面按三条主线梳理这个仓库：概念分层（Subagents、Commands、Skills、Hooks、MCP、Plugins 各自管什么）、配置地图（settings 优先级与 CLAUDE.md 加载规则）、实战路径（从个人配置到团队规范）。文中数据与机制均已对照仓库 README 和 Claude Code 官方文档核实到 2026 年 9 月。

## 一、项目概览

### 这个仓库里有什么

[Claude Code Best Practice](https://github.com/shanraisshan/claude-code-best-practice) 由开发者 **shanraisshan** 创建和维护（2025 年 10 月建库，至今保持高频更新），被 Claude Code 创造者 Boris Cherny 在 X 上多次转发推荐，曾登上 GitHub Trending 日榜第一，也是 2026 年 3 月的月度 Trending 仓库。

**仓库规模**：66.2k+ Stars，6.5k+ Forks，MIT 许可证。

仓库内容覆盖这几个方向：

- **概念澄清**：Subagents、Commands、Skills、Hooks 等容易混淆的概念，分别说明各自的文件位置、配置字段和适用场景，每个概念都配了"Best Practice"和"Implemented"两份文档——前者讲原理，后者给可运行的实现
- **配置示例**：可以直接复用的 `.claude/` 配置文件，覆盖 settings、rules、agents、commands、skills、hooks 等目录
- **工作流对比**：对比 Superpowers、Spec Kit、BMAD-METHOD 等十余套主流 AI 开发方法论，并追踪各自的 Stars 与组件数量
- **Tips 合集**：83 条技巧，每条都标注来源——Boris Cherny、Anthropic 团队成员（Thariq、Cat Wu、Lydia Hallie）或社区开发者
- **新特性追踪**：Auto Mode、Agent Teams、Scheduled Tasks、Channels 等持续演进的 beta 能力，README 的 "Hot" 表几乎每周更新

仓库 README 里有一句使用建议值得先记住：**把它当课程读，而不是当工作流抄**。先理解 agents、commands、skills、hooks 这些原语，再组装自己的流程；仓库自带的 `/weather-orchestrator` 命令是一个完整的 Command → Agent → Skill 演示，适合作为第一个动手对象。

## 二、核心概念体系

Claude Code 的功能扩展围绕几个核心模块展开：Subagents、Commands、Skills、Hooks、MCP 和 Plugins。下面逐个说明各自管什么、放在哪里、什么时候用。

### Subagents（子代理）

Subagent 在全新隔离上下文中运行，拥有自己的提示词、工具白名单、模型和权限设置。定义文件是 `.claude/agents/<name>.md`，YAML frontmatter 声明配置——必填的只有 `name` 和 `description`，可选字段包括 `tools`（工具白名单）、`model`（默认 `inherit` 继承会话模型）、`maxTurns`（最大轮数）、`memory`（持久记忆范围：`user`/`project`/`local`）等十几个。

**与 Command 的关键区别**：Subagent 启动时创建独立的上下文，主会话只拿到它的最终报告，中间的文件读取、搜索、失败尝试都留在子代理自己的上下文里；Command 则直接把提示词注入当前上下文，所有操作共享同一个会话状态。

这也是 Anthropic 团队反复强调的用法：把"20 次文件读取 + 12 次搜索 + 3 条死路"这类脏活交给子代理，主上下文只留结论。

| 特性 | Subagent | Command |
|------|----------|---------|
| 上下文 | 全新隔离上下文 | 默认共享现有上下文 |
| 调用方式 | 主代理按需派生 | `/command-name` 手动调用 |
| 适用场景 | 复杂独立任务、上下文隔离 | 高频重复操作 |
| 结果回传 | 最终报告进入主会话 | 全程留在当前会话 |

### Commands（命令）

Command 是注入到当前上下文的提示词模板，用户通过 `/command-name` 主动调用，定义在 `.claude/commands/<name>.md`。

与 Subagent 相反，Command 默认共享当前上下文，适合快速执行单一操作。值得一提的是，Command 的 frontmatter 也支持 `context: fork` 字段——设置后整条命令会在隔离子代理中运行，主上下文只看最终结果。也就是说，"隔离还是共享"如今是一个可以逐命令选择的开关，不再是非此即彼的架构差异。

Boris Cherny 的建议是：每天要重复一次以上的"内循环"操作，都值得写成 Command 存进 `.claude/commands/` 并提交到 git——省掉重复输入提示词的成本，团队也能共用。

### Skills（技能）

Skill 是按需加载的知识与能力模块，Claude Code 会自动发现它。与 Command 相比，Skill 的两个特性值得单独说：

- **渐进式披露**：Skill 是文件夹而非单个文件，`SKILL.md` 之外还可以放 `references/`、`scripts/`、`examples/` 子目录，Claude 按需深入读取，避免一次性撑爆上下文
- **上下文分叉**：frontmatter 设置 `context: fork` 后，Skill 在子代理中运行，主上下文只收结果

**文件位置**：`.claude/skills/<name>/SKILL.md`

一个最小的 Skill 结构：

```markdown
---
name: security-review
description: 在隔离上下文中对代码做安全审查，适合 PR 合并前调用
---

# Security Review

按以下步骤审查传入的代码：……（正文描述指挥模型如何一步步执行）
```

`description` 是模型判断"何时该加载这个 Skill"的依据。Anthropic 工程师 Thariq 的原话是：description 是触发器，不是摘要——要写给模型看（"什么时候该触发我"），而不是写给人看的功能介绍。这一点和 Subagent 的 `description` 用法一致。

Claude Code 官方自带了 18 个内置 Skill（`/code-review`、`/debug`、`/verify` 等），官方维护的可安装 Skill 集合放在 [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills) 仓库中。

### Hooks（钩子）

Hook 在智能体循环的固定时点自动执行，是精准度最高的扩展机制。一个 Hook 可以是一条 shell 命令、一个 HTTP 端点、一次 MCP 工具调用、一段提示词，甚至一个子代理；最常用的是 shell 命令形式。

**配置位置**：`settings.json` 的 `hooks` 字段（脚本文件通常放在 `.claude/hooks/` 目录）。

工作方式：事件触发时，Claude Code 把事件上下文以 JSON 形式从 stdin 传给你的命令；脚本处理后用退出码或 stdout JSON 返回决定（放行、拒绝、附加上下文）。官方文档列了 30 多个事件，常用的有：

| 事件 | 触发时点 | 常见用途 |
|------|----------|----------|
| `PreToolUse` | 工具调用执行前，可拦截 | 拦截危险命令、记录操作日志 |
| `PostToolUse` | 工具调用成功后 | 自动格式化代码、校验输出 |
| `UserPromptSubmit` | 用户提交提示词时，模型处理前 | 注入额外上下文、关键词拦截 |
| `Stop` | 一轮响应结束时 | 提醒继续验证、通知外部系统 |

以官方文档的"拦截 `rm -rf`"为例，先在 `settings.json` 里声明：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/block-rm.sh"
          }
        ]
      }
    ]
  }
}
```

脚本从 stdin 读事件 JSON，命中危险命令时返回拒绝决定：

```bash
#!/bin/bash
# .claude/hooks/block-rm.sh（需 chmod +x，依赖 jq）
COMMAND=$(jq -r '.tool_input.command')

if echo "$COMMAND" | grep -q 'rm -rf'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "Destructive command blocked by hook"
    }
  }'
else
  exit 0  # 无决定，走正常权限流程
fi
```

同一个事件可以挂多个 Hook。Boris Cherny 的两个典型用法：用 `PostToolUse` 挂自动格式化——模型生成的代码已经够好，格式化补上最后 10%，避免 CI 挂掉；用 `Stop` 在每轮结束时提醒 Claude 继续验证自己的工作。

### MCP（模型上下文协议）

MCP 通过外部独立进程扩展 Claude Code 的能力边界——连接数据库、浏览器、第三方服务。与 Plugin 的分工是：MCP 解决"连接"问题，让 Claude 能调用外部工具；Plugin 解决"分发"问题，把配置和技能打包分享。

**配置位置**：项目根目录的 `.mcp.json`（可提交到仓库，团队共享），或用 `claude mcp add` 命令添加。JSON 里的键是 `mcpServers`：

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
    }
  }
}
```

远程服务用 HTTP 传输，例如 `claude mcp add --transport http notion https://mcp.notion.com/mcp`。注意生态变化较快：GitHub 的官方 MCP server 已独立为 [github/github-mcp-server](https://github.com/github/github-mcp-server) 仓库（33k+ Stars），早期随 `@modelcontextprotocol/server-github` 分发的版本已不再维护，选型时以各家官方仓库为准。

### Plugins（插件）

Plugin 是打包分发单元，把 Commands、Skills、MCP 配置、Hooks 等打包成一个模块，通过 `claude plugin install`（或会话内 `/plugin install`）从插件市场安装。适合团队把内部实践沉淀成可复用资产——Anthropic 维护着官方市场 `claude-plugins-official` 和社区市场 `claude-community`，企业也可以把市场放在私有仓库里。

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

把六个模块放进一张心智地图：`Hooks` 横切整个循环，在事件边界上做拦截与记录；`MCP` 与 `Plugins` 属于扩展层，一个管"连外部工具"，一个管"打包分发实践"；真正驱动对话推进的是 `Command → Subagent → Skill` 这条主线——仓库专门用一张编排图讲这个模式，`/weather-orchestrator` 就是它的可运行版本。

## 三、配置与个性化

### 设置文件的优先级

Claude Code 的配置要分清两个维度：**设置（settings）** 与 **上下文（context）**，二者合并规则不同，混在一起极易踩坑。

`settings.json` 按五级优先级合并，高优先级的同名键覆盖低优先级：

| 优先级 | 位置 | 谁在用 |
|--------|------|--------|
| 1 | `managed-settings.json`（企业管控） | 组织统一策略，普通设置无法覆盖 |
| 2 | `claude --settings` 启动参数 | 本次会话临时指定 |
| 3 | `.claude/settings.local.json` | 个人，不入库 |
| 4 | `.claude/settings.json` | 项目共享，随仓库分发 |
| 5 | `~/.claude/settings.json` | 开发者本机全局 |

一个容易忽略的细节：数组类设置（如 `permissions.allow`）不是覆盖，而是各层级**合并去重**——允许列表会累加。权限规则里 `deny` 拥有最高安全优先级，低优先级的 allow/ask 无法翻案。

**上下文（context）** 负责告诉模型"这个项目是什么"，按另一套规则加载：

1. **CLAUDE.md**：项目背景描述文件。加载规则见下一节
2. **`.claude/rules/*.md`**：规则文件，和 CLAUDE.md 一样自动进入每个会话；可在 frontmatter 里用 `paths` 声明文件匹配模式，让规则只在触碰相关文件时懒加载

> 常见误区：把 `CLAUDE.md` 和 `settings.json` 当作同一种优先级排序。实际上一个提供"项目背景"，一个提供"运行配置"，互不覆盖。另外，能用 settings 确定性配置的事（比如 `attribution.commit: ""` 关掉提交署名），就不要写进 CLAUDE.md 让模型"记住"——前者是机制保证，后者靠模型自觉。

### CLAUDE.md 的加载规则

CLAUDE.md 的目录行为有明确规则，写 monorepo 配置前必须搞清楚：

- **祖先启动加载**：启动时从当前目录向上遍历，路径上所有 CLAUDE.md 立即进入上下文——所以仓库根的公共规范永远在场
- **后代懒加载**：当前目录之下各子目录的 CLAUDE.md **不会**在启动时加载，只有当 Claude 读到该子目录的文件时才进入上下文
- **兄弟互不加载**：在 `frontend/` 工作时，`backend/CLAUDE.md` 不会出现
- **全局文件**：`~/.claude/CLAUDE.md` 对所有会话生效，适合放个人偏好；不想共享给团队的约定可以放 `CLAUDE.local.md` 并加入 `.gitignore`

这个设计让 monorepo 可以分层写规范：根目录放全仓通用的编码规范，各组件目录放框架专属约定，互不污染。Boris Cherny 建议单个 CLAUDE.md 控制在 200 行以内——超过之后模型开始忽略指令，这是社区反复踩过的坑。

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

好的 `CLAUDE.md` 只写"稳定不变"的信息——结构、技术栈、硬性规范。一个朴素的验收标准来自社区：任何开发者都能启动 Claude Code 说一句"跑测试"，而且第一次就能跑通；跑不通，说明 CLAUDE.md 缺了必要的构建、测试命令。一周一变的进度信息不该放这里，否则每次对话都在消耗上下文预算。

### 目录结构

```text
.claude/
├── agents/               # 子代理定义
├── commands/             # 命令模板
├── skills/               # 技能模块
├── hooks/                # 钩子脚本
├── rules/                # 规则文件
├── settings.json         # 项目共享设置
└── settings.local.json   # 个人本地设置（默认被 git 忽略）
```

## 四、开发工作流对比

README 追踪了十几套主流方法论，数据随仓库每周更新。先说结论：这些工作流名目不同，架构却收敛到同一个模式——**Research → Plan → Execute → Review → Ship**（研究 → 计划 → 执行 → 评审 → 发布）。差别主要在两个地方：计划产物是规格文档还是任务票，以及验收环节用 TDD 还是代码审查兜底。

截至 2026 年 9 月，主要工作流的规模与流程：

| 工作流 | Stars | 流程要点 |
|--------|-------|----------|
| [Superpowers](https://github.com/obra/superpowers) | 290k | 头脑风暴 → git worktree 隔离 → 写计划 → 子代理开发 → TDD → 代码审查 |
| [Matt Pocock Skills](https://github.com/mattpocock/skills) | 267k | 需求转规格 → 转任务票 → 实现 → TDD → 代码审查 |
| [Everything Claude Code](https://github.com/affaan-m/ECC) | 262k | 组件量最大：68 个子代理、94 个命令、292 个技能 |
| [Spec Kit](https://github.com/github/spec-kit) | 138k | GitHub 官方：宪法 → 规格 → 计划 → 任务 → 实现 |
| [gstack](https://github.com/garrytan/gstack) | 134k | 办公时间答疑 → 计划多角色评审 → 实现 → QA → 发布 → 复盘 |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec) | 70k | 变更提案 → 应用 → 验证 → 归档，规格与代码同步演进 |
| [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) | 53k | 创意 → PRD → 架构 → 规格 → 史诗与故事 → 构建 → 审查 → 回顾 |
| [Get Shit Done](https://github.com/gsd-build/get-shit-done) | 64.6k | 新项目 → 探索 → 规格 → 计划 → 分阶段执行 → 审查 → 发布 |

另有 [oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode)（39.3k，团队计划与执行）、[Compound Engineering](https://github.com/EveryInc/compound-engineering-plugin)（25.2k，复利式工程）、[HumanLayer](https://github.com/humanlayer/humanlayer)（11.6k，研究-计划-实现）等，模式大同小异。

这些流程全部由 Skills/Commands/Agents 组装而成，表格里的"组件数"就是各自的技能、命令、子代理文件数量——选定一套后，读它的 `.claude/` 目录比读文档更快。自主迭代类任务则有官方的 [Ralph Wiggum](https://github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum) 插件：让 Claude 在循环里反复执行-验证，直到验收条件通过。

## 五、编排工作流详解

### 一次代码审查如何流过系统

以 GitHub PR 审查为例，看 Commands、Subagents、Skills 和 Hooks 如何协同：

1. 用户输入 `/review-pr #42`，触发 `review-pr` Command
2. Command 的提示词模板定义了审查步骤：拉取 diff → 安全检查 → 风格检查 → 生成报告
3. Claude 按提示词派生三个 Subagent 并行工作：一个查安全漏洞、一个查代码风格、一个跑回归测试——每个子代理有独立上下文，互不干扰
4. 安全审查子代理加载 `security-review` Skill，在隔离上下文中扫描代码
5. 每个子代理调用工具前，`PreToolUse` Hook 记录操作日志
6. 三个子代理完成后，主会话汇总结果，生成审查报告

这个案例能看出 Subagent 和 Skill 的分工：Subagent 提供隔离的执行环境，Skill 提供可复用的审查能力；同一个 Skill 可以被不同子代理加载。仓库自带的 `/weather-orchestrator` 是同一模式的完整演示，可以直接运行观察。

### 如何自定义编排

1. **创建 Command**：在 `.claude/commands/` 中定义
2. **创建 Subagent**：在 `.claude/agents/` 中定义
3. **创建 Skill**：在 `.claude/skills/` 中定义
4. **组合使用**：Command 的提示词指挥模型派生 Subagent，Subagent 加载 Skill

## 六、实战建议

### 个人开发者：从哪里开始

**第一周**：先把项目上下文固定下来。在项目根目录创建 `CLAUDE.md`，描述项目结构、技术栈和编码规范，控制在 200 行内。再在 `.claude/rules/` 里放几条规则——比如"提交前必须跑 lint"。这一步不需要理解任何高级概念，做完马上能看到效果。

**第二周**：挑一个高频操作做成 Command，比如 `/review` 审代码、`/deploy` 部署。Commands 不需要独立上下文，学习成本最低。

**一个月内**：评估是否需要 Subagent 或 Skill。判断标准：反复对 Claude Code 描述同一段背景信息，就该写成 Skill；某个任务需要隔离运行且不污染主会话，就该用 Subagent。

### 团队负责人：从规范到资产

**第一步：统一上下文入口**。把 `CLAUDE.md` 和各语言规则放入团队仓库的 `.claude/` 目录。新成员克隆仓库后，Claude Code 自动加载团队的上下文规范，不需要口头传授。

**第二步：建立校验机制**。配置 Hooks（`PreToolUse` 记日志、`PostToolUse` 自动格式化），让每次操作可追溯；用 `permissions.deny` 挡住危险操作。如果有 CI 流水线，用 GitHub Actions 做 PR 自动审查。

**第三步：打包成可复用资产**。当多个项目需要同一套审查流程或部署脚本时，做成 Plugin 通过市场分发。这时才需要考虑 MCP 连接外部工具（如 Slack、Jira）和 Agent Teams 并行开发。

### 什么时候不要急着上

- **Agent Teams** 仍处于 beta，并行代理的协调成本不低。等团队单个代理的使用已经稳定，再引入多代理。
- **Channels 远程触发** 适合已有自动化体系的小团队。如果日常工作还在手动执行，先理顺本地工作流。
- **Plugins 打包分发** 适合跨项目复用场景。个人开发者或单项目团队暂时不需要。

### 安全与性能

| 场景 | 建议 |
|------|------|
| 日常开发想少点确认 | 用 Auto Mode（`--permission-mode auto` 或 `Shift+Tab` 切换）：模型分类器自动放行安全命令，遇到风险暂停询问；用它替代 `--dangerously-skip-permissions` |
| 敏感代码 | 保持默认手动确认，用 `/permissions` 写精确的 allow/deny 通配规则（如 `Bash(npm run *)`） |
| 自动化任务 | 用 `/loop` 或 `/schedule` 定时执行，保留日志 |
| 外部集成 | 走 MCP，企业可用 managed settings 统一管控可用的 server |

| 优化项 | 方法 |
|--------|------|
| 上下文管理 | `/context` 查看占用；`/compact` 带重点指示压缩；换任务时 `/clear` 清空 |
| 回滚与试错 | Checkpointing 自动跟踪文件编辑，`/rewind`（双击 Esc）回到出错前 |
| 并行执行 | Subagent 隔离脏活；独立任务多时再上 Agent Teams（beta） |
| 成本监控 | Status Line 常驻显示上下文水位；`/usage` 查额度 |
| 长任务 | `/goal` 设定完成条件让 Claude 跨轮次推进；自主迭代用 Ralph Wiggum 插件 |

### 相关资源

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/shanraisshan/claude-code-best-practice |
| Claude Code 文档 | https://code.claude.com/docs |
| 官方 Skills | https://github.com/anthropics/skills |
| GitHub 官方 MCP Server | https://github.com/github/github-mcp-server |

---

> 本文数据（Stars、工作流清单、特性状态）核对自仓库 README 与 Claude Code 官方文档，时点为 2026 年 9 月。该仓库每周更新，具体特性以官方文档为准。
