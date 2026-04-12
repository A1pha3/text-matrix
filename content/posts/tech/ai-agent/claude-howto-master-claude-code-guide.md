---
title: "Claude How To：从入门到精通 Claude Code 终极指南"
date: 2026-03-30T23:45:00+08:00
lastmod: 2026-04-03T23:24:59+08:00
slug: claude-howto-master-claude-code-guide
aliases:
  - /posts/tech/claude-howto-master-claude-code-guide/
categories: ["技术笔记"]
tags: ["Claude Code", "AI 编程", "Skills", "MCP", "Subagents", "Hooks", "Plugins"]
description: "基于 2026 年 3 月仓库状态，对 Claude How To 做一次系统化中文导读。本文讲清 Claude Code 的学习顺序、安装路径、功能边界、常见误区与实战工作流。"
---

# Claude How To：从入门到精通 Claude Code 终极指南

> 预计阅读时间：45分钟 | 难度：⭐⭐⭐⭐

---

> 目标读者：已经在用或准备系统使用 Claude Code 的开发者、团队技术负责人、AI 工作流设计者
> 前置知识：命令行基础、Git 基础、理解 LLM 工具调用的基本概念
> 版本基线：本文依据 2026-03-31 的仓库状态整理；Stars / Forks 等实时指标会继续变化，请以仓库页面为准。

## 学习目标

读完本文后，你应该能够：

1. **说清 Claude How To 的定位**：知道它和官方 Claude Code 文档分别解决什么问题。
2. **理解学习顺序与装配顺序的区别**：知道为什么“先学什么”不等于“先装什么”。
3. **分辨关键能力边界**：能解释 Slash Commands、Memory、Skills、Subagents、Hooks、MCP、Plugins、Checkpoints 的职责差异。
4. **按真实项目落地**：知道如何把个人经验沉淀为团队可复用的工作流资产。
5. **规避常见事实错误**：避免把目录、事件、配置路径和能力边界写错。

## 先看结论

如果你只想记住一句话：Claude How To 的价值，不在于“把 Claude Code 的功能列一遍”，而在于它把 Slash Commands（斜杠命令）、Memory（记忆）、Skills（技能）、Subagents（子代理）、MCP、Hooks（钩子）、Plugins（插件）、Checkpoints（检查点）和 CLI（命令行接口）串成了一条真正可落地的学习与交付路径。

它最适合三类人：

- 已经装了 Claude Code，但还停留在“聊天式使用”的个人开发者
- 想把团队规范沉淀到 `CLAUDE.md`、Skills、Subagents 里的技术负责人
- 准备把 AI 编程从“偶尔试试”升级为“稳定工作流”的重度用户

它不太适合两类人：

- 只想找一页命令清单，不打算理解工作流组合的人
- 完全不准备配置持久上下文、自动化和外部工具的人

如果你现在只有 15 分钟，请先做四件事：

1. 克隆仓库并读一遍 `README.md`。
2. 复制一个 Slash Command 到项目里。
3. 创建项目级 `CLAUDE.md`。
4. 安装一个现成 Skill，并实际运行一次。

## 一、Claude How To 到底是什么

Claude How To 是仓库 [luongnv89/claude-howto](https://github.com/luongnv89/claude-howto)。它不是 Anthropic 官方文档的替代品，而是一套“怎么把功能组合成工作流”的教程系统。

官方文档更像 Reference（参考手册）：告诉你某个能力存在、参数是什么、限制在哪里。Claude How To 更像 Workflow Guide（工作流指南）：告诉你应该先学什么、不同能力怎么配合、哪些配置可以直接拷走用。

这也是它和普通“功能清单型教程”最大的区别：它强调的不只是“会用”，而是“能组合、能复用、能迁移到真实项目里”。

## 二、已核实的项目概况

| 项目 | 信息 |
| ---- | ---- |
| 仓库 | [luongnv89/claude-howto](https://github.com/luongnv89/claude-howto) |
| 仓库定位 | 面向 Claude Code 的可视化、示例驱动、工作流导向教程 |
| 最新发布 | v2.2.0 |
| 兼容版本 | Claude Code 2.1+ |
| 兼容模型 | Claude Sonnet 4.6、Claude Opus 4.6、Claude Haiku 4.5 |
| 仓库结构 | 10 个主模块，外加 `CATALOG.md`、`LEARNING-ROADMAP.md`、`QUICK_REFERENCE.md`、`INDEX.md` 等总览文档 |
| 实时热度 | 截至 2026-04-03，约 17.5k Stars、2.1k Forks |
| 维护状态 | 活跃维护，文档持续随 Claude Code 版本同步 |

这里有一个值得注意的细节：README 中使用了 “Trusted by 5,900+ Developers” 这样的宣传文案，但 GitHub 页面实时显示的 Stars 已更高。写这类文章时，最好把“README 文案”与“仓库实时指标”分开写，避免把营销文案误当成实时数据。

此外，这个仓库不只有 README：

- `LEARNING-ROADMAP.md` 负责学习顺序
- `CATALOG.md` 负责功能矩阵和安装优先级
- `QUICK_REFERENCE.md` 负责速查
- `INDEX.md` 负责完整索引

如果你不是按教程顺序学习，而是按“我现在缺什么能力”来检索，这四份总览文档的价值非常高。

## 适用场景：什么时候优先读这篇

### 场景一：你已经在用 Claude Code，但一直停留在“聊天式使用”

如果你会提问、会让 Claude 改几个文件，却还没有形成稳定命令、项目记忆、外部工具接入和自动化守卫，这篇文章最适合作为从“能用”到“会组织工作流”的过渡。

### 场景二：你负责团队规范，希望把经验沉淀成可执行资产

当团队总在重复解释目录结构、提交规范、审查流程和工具边界时，这篇文章能帮助你把这些经验落到 `CLAUDE.md`、Slash Commands、Skills、Subagents 和 Hooks 上。

### 场景三：你想看的是系统方法，而不只是命令清单

如果你的目标是理解这些能力如何组合，这篇文章比单独查某个命令更有价值；反过来，如果你只想确认某个参数怎么写，官方参考文档通常更直接。

### 它提供的不是“信息”，而是“现成产物”

| 你能拿到什么 | 为什么有用 |
| ---- | ---- |
| Slash Commands 示例 | 把高频提示词变成稳定入口 |
| `CLAUDE.md` 模板 | 让 Claude Code 记住项目结构、规范与偏好 |
| Skills 示例 | 把重复任务封装为可自动触发的能力 |
| Subagents 示例 | 把复杂任务拆给不同专长的子代理 |
| MCP 配置示例 | 让 Claude Code 连接 GitHub、数据库、文件系统等外部能力 |
| Hooks 示例 | 在关键事件上自动做校验、记录、通知 |
| Plugins 示例 | 把 commands、agents、skills、hooks、MCP 打成可共享的完整方案 |

如果你经常离线阅读长文档，这个仓库还支持生成 EPUB 电子书：

```bash
uv run scripts/build_epub.py
```

## 三、先搞清作用域，再谈安装

很多人第一次看 Claude How To，会直接把所有文件都复制到一个项目里。这样做通常不是最快路径。先搞清“项目级”和“用户级”的边界，效率会高很多。

| 作用域 | 典型路径 | 适合放什么 |
| ---- | ---- | ---- |
| 项目级 | `.claude/commands/`、`.claude/agents/`、`.claude/skills/`、`.claude/settings.json`、`.mcp.json`、`CLAUDE.md` | 团队共享规则、项目专用命令、项目专用技能 |
| 用户级 | `~/.claude/commands/`、`~/.claude/agents/`、`~/.claude/skills/`、`~/.claude/hooks/`、`~/.claude/settings.json`、`~/.claude/CLAUDE.md` | 跨项目个人偏好、私有习惯、通用自动化 |

经验上，推荐这样理解：

- 想让团队都能用到的东西，尽量放项目级并纳入版本控制。
- 只属于你个人的偏好与自动化，放用户级。
- Hooks 脚本通常更适合用户级；但 Hook 配置既可以放用户级，也可以放项目级 settings。
- MCP 配置不要随手写成 `.claude/mcp.json`。当前文档体系更推荐项目级 `.mcp.json`，或者通过 CLI 直接 `claude mcp add ...`。

## 四、15 分钟上手：最短可行路径

如果你只想验证“这个仓库到底值不值得学”，按下面的最短路径来就够了。

```bash
# 1. 克隆仓库
git clone https://github.com/luongnv89/claude-howto.git
cd claude-howto

# 2. 复制第一个 Slash Command 到你的项目
mkdir -p /path/to/your-project/.claude/commands
cp 01-slash-commands/optimize.md /path/to/your-project/.claude/commands/

# 3. 设置项目级 Memory
cp 02-memory/project-CLAUDE.md /path/to/your-project/CLAUDE.md

# 4. 安装一个 Skill
cp -r 03-skills/code-review ~/.claude/skills/
```

然后进入你的项目并启动 Claude Code，直接试：

```bash
cd /path/to/your-project
claude
# 在 Claude Code 中输入：
/optimize
```

这套路径的意义，不是让你“装了三个功能”，而是让你同时感受到三种完全不同的价值：

- Slash Commands 解决的是“入口标准化”。
- Memory 解决的是“上下文稳定”。
- Skills 解决的是“能力自动化”。

### 如果你愿意再多花 45 分钟

下面这组配置，会让你从“能用”升级到“开始有工作流意识”。

```bash
# 项目级 Slash Commands
cp 01-slash-commands/*.md /path/to/your-project/.claude/commands/

# 项目级 Memory
cp 02-memory/project-CLAUDE.md /path/to/your-project/CLAUDE.md

# 项目级 Subagents
mkdir -p /path/to/your-project/.claude/agents
cp 04-subagents/*.md /path/to/your-project/.claude/agents/

# GitHub MCP
export GITHUB_TOKEN="your_token"
claude mcp add github -- npx -y @modelcontextprotocol/server-github
```

做到这一步，你已经可以开始拼出最有价值的一类场景：项目上下文 + 自定义命令 + 子代理分工 + GitHub 外部数据。

## 五、学习顺序和装配顺序不是一回事

Claude How To 做得很好的一个地方，是它同时给出了“学习顺序”和“安装优先级”。这两者不要混为一谈。

| 视角 | 推荐顺序 | 为什么 |
| ---- | ---- | ---- |
| 学习顺序 | Slash Commands → Memory → Checkpoints → CLI → Skills → Hooks → MCP → Subagents → Advanced Features → Plugins | 这是认知递进路径，先理解单点能力，再理解组合能力 |
| 装配顺序 | Memory → Slash Commands → Subagents → Hooks → MCP → Skills → Plugins | 这是工程回报路径，优先装那些最能立刻提高产出的组件 |

这也是我认为这类指南是否“高级”的分水岭。低水平教程只会告诉你“有哪些功能”；高水平教程会告诉你“先学什么”和“先装什么”其实不是一回事。

### 按当前水平选入口

| 你的现状 | 先看哪块 | 预计投入 |
| ---- | ---- | ---- |
| 刚会在 Claude Code 里聊天 | Slash Commands + Memory | 约 2.5 小时 |
| 已经会用 `CLAUDE.md` 和自定义命令 | Skills + Hooks + Checkpoints | 约 3.5 小时 |
| 已开始接外部工具和多代理协作 | MCP + Subagents + Advanced Features + Plugins | 约 5 小时 |

### 10 个模块的正确打开方式

| 顺序 | 模块 | 你真正要学会的东西 | 最直接的产出 |
| ---- | ---- | ---- | ---- |
| 1 | Slash Commands | 把重复提示词做成统一入口 | `/optimize`、`/pr` 这类稳定命令 |
| 2 | Memory | 让 Claude Code 读懂你的项目和团队规则 | 项目级 `CLAUDE.md` |
| 3 | Checkpoints | 在高风险操作中安全回退 | `/rewind` 的使用习惯 |
| 4 | CLI | 把 Claude Code 接进终端、脚本和 CI | `claude -p ...` 这类自动化入口 |
| 5 | Skills | 把“领域知识 + 操作规则”封装成可复用能力 | 项目 Skill 或个人 Skill |
| 6 | Hooks | 让校验、记录、通知自动发生 | 写入前格式化、敏感操作校验、日志记录 |
| 7 | MCP | 给 Claude 接上 GitHub、数据库、浏览器等外部世界 | GitHub 审查、数据库查询、自动化浏览 |
| 8 | Subagents | 把复杂任务拆成多角色协作 | 代码审查、测试、文档并行处理 |
| 9 | Advanced Features | 学会规划模式、深度思考、后台任务等高级能力 | 长任务的可控执行 |
| 10 | Plugins | 把多项能力打包成可分发方案 | 团队级工作流套件 |

## 六、最容易混淆的功能边界

真正把 Claude Code 用顺手的人，往往不是“知道很多命令”的人，而是“知道什么时候用哪种扩展机制”的人。

| 功能 | 它解决什么问题 | 什么时候优先用 | 常见误解 |
| ---- | ---- | ---- | ---- |
| Slash Commands（斜杠命令） | 给高频任务一个稳定入口 | 你反复输入相似提示词时 | 它不是知识库，也不会自动长期记忆 |
| Memory（记忆） | 持久保存项目背景和规则 | 需要长期稳定上下文时 | 它不是 README 的替代品，而是面向 Claude 的规则层 |
| Skills（技能） | 把某类任务的专业处理方式自动化 | 任务模式重复、判断逻辑相对稳定时 | 它不是“更高级的 Slash Command” |
| Subagents（子代理） | 把任务拆分给不同专长的代理 | 问题复杂、需要并行或隔离上下文时 | 它不是 Skill 的别名，两者解决的问题不同 |
| MCP | 接入外部工具和实时数据 | 需要 GitHub、数据库、浏览器、API 时 | 它不是提示工程，而是外部能力接入层 |
| Hooks（钩子） | 在事件发生时自动执行动作 | 需要校验、审计、通知、强制流程时 | 它不是“写在系统提示里的规则” |
| Plugins（插件） | 把 commands、agents、skills、hooks、MCP 打包分发 | 团队共享、标准化安装、统一维护时 | 它不是“命令合集”，而是完整解决方案 |
| Checkpoints（检查点） | 安全试错与回退 | 重构、批量修改、探索多方案时 | 它不依赖你手写备份脚本 |
| CLI | 把 Claude Code 接入脚本和流水线 | 自动化、批处理、CI/CD 时 | 它不只是交互式聊天的另一种外壳 |

把这些边界想清楚之后，你会更容易明白一个关键判断：

> 先用 Slash Commands 统一入口，再用 Memory 稳定上下文，用 Subagents 拆复杂任务，用 MCP 接外部世界，用 Hooks 固化流程，最后再用 Plugins 打包分发。

## 七、这套体系为什么比“会几个命令”更强

Claude How To 的真正上限，不在单个模块，而在组合能力。

```mermaid
graph LR
    A["用户请求 / Slash Command"] --> B["Memory 载入项目上下文"]
    B --> C["主代理制定任务"]
    C --> D["Subagents 并行分工"]
    D --> E["MCP 访问 GitHub / DB / Browser"]
    E --> F["Hooks 触发校验、记录、通知"]
    F --> G["输出结果 / Checkpoints 回退"]
```

上图看起来简单，但它解释了 Claude Code 工作流的核心：不是“让模型更聪明”，而是“让系统更稳定”。

### 1. 自动化代码审查

最有现实价值的起手式通常是：

- Slash Command 负责触发 `/review-pr`
- Memory 提供编码规范、目录说明、测试要求
- Subagents 分别负责安全、性能、测试覆盖率
- MCP 读取 GitHub PR 数据
- Hooks 负责审查前校验或审查后记录

这类工作流最适合团队落地，因为它直接对应 PR 质量、代码一致性和审查成本。

### 2. 团队知识沉淀

当你发现团队总在重复讲同一套规范时，最好的办法不是多开几次分享会，而是把规则写进：

- `CLAUDE.md`
- 项目级 Skills
- 项目级 Slash Commands
- 必要时再封装为 Plugin

这样做的价值在于：规范不再停留在 Wiki 里，而是变成真正会被 Claude Code 执行的系统配置。

### 3. 长任务与高风险改动

当任务涉及大规模重构、长链路改动或多种方案试验时，Checkpoints、Planning Mode、Background Tasks 这些能力才真正开始体现价值。

很多“AI 写代码不可靠”的抱怨，本质上不是模型不行，而是使用者没有建立：

- 可回退点
- 任务分解
- 外部验证
- 自动化守卫

Claude How To 恰好就在补这一层。

## 八、文中最容易写错的 6 个点

原始版本里，最值得修正的不是文风，而是这些事实和边界问题。

### 1. 不要在正文重复写 H1

Hugo 站点已经在 frontmatter 里给了 `title`，正文再写一遍 `#` 标题，会触发典型的 Markdown 结构问题，也让页面层级重复。

### 2. Hooks 不是几个“随口起名”的事件

当前资料里，Hooks 明确分为 4 大类、25 个事件，例如 `PreToolUse`、`PostToolUse`、`SessionStart`、`SubagentStart`、`TaskCompleted`、`ConfigChange` 等。不要把它写成一组自定义的小写事件名，否则读者按文中配置会直接对不上。

### 3. Checkpoints 的重点是“自动快照 + 回退”，不是“手动存档命令”

当前文档强调的操作方式是：

- 每次用户提示后会自动创建检查点
- 通过 `Esc` 连按两次或 `/rewind` 回退
- 可选择恢复代码、恢复对话，或只做摘要

如果把它讲成“先执行某个自定义 checkpoint create 命令”，就会把读者带偏。

### 4. MCP 的项目级配置重点是 `.mcp.json`

把 MCP 简化为“把配置丢到 `.claude/mcp.json`”不够准确。当前更稳妥的写法是：

- 项目级用 `.mcp.json`
- 用户级用 `~/.claude.json`
- 或直接通过 `claude mcp add ...` 配置

### 5. Skill 结构不是固定目录模板

Skill 的核心是 `SKILL.md`，其余目录可能包含 `scripts/`、`templates/` 或其他辅助文件，但不是所有 Skill 都必须有 `commands/`、`agents/`、`rules/`、`tools/` 这整套固定骨架。

### 6. Plugin 不是“命令打包版”

Plugin 的定位更高，它通常包含：

- `.claude-plugin/plugin.json`
- `commands/`
- `agents/`
- `skills/`
- `hooks/`
- `.mcp.json`
- `settings.json`
- `scripts/`

如果只把 Plugin 理解成“多个 Slash Commands 的合集”，读者会低估它的工程价值。

另外，Plugin 内的 Subagents 还有明确的安全限制，不能借 frontmatter 去定义 `hooks`、`mcpServers` 或 `permissionMode`。这说明 Plugin 的设计目标不是无限扩权，而是受控打包。

## 九、推荐给中文开发者的实践策略

如果你的目标不是“了解 Claude Code 有哪些功能”，而是“让团队真的用起来”，我更推荐下面这条路线。

### 阶段 1：先拿到稳定收益

先做三件事：

- 给项目写一份 `CLAUDE.md`
- 复制 2 到 3 个最常用的 Slash Commands
- 安装 1 个最符合当前任务的 Skill 或 Subagent

这一步的目标是减少重复解释和重复提示词。

### 阶段 2：让流程开始自动化

当团队开始稳定使用后，再加：

- GitHub MCP
- 基础 Hooks
- 1 到 2 个项目级 Subagents

这一步的目标是让审查、校验、上下文加载开始“自动发生”。

### 阶段 3：再做团队级打包

只有当团队已经验证过这套工作流有持续价值时，再把它封装成 Plugin。不要一开始就追求“大而全”的插件化，那会让维护成本先于收益到来。

## 十、常见故障排查

| 问题 | 常见原因 | 优先排查什么 |
| ---- | ---- | ---- |
| 命令不生效 | 文件路径不对、文件名不对、语法有问题 | 先看 `.claude/commands/` 是否存在，再看 frontmatter 是否正确 |
| Skill 没有被触发 | 触发描述不清、放错目录、任务不匹配 | 先看 `SKILL.md` 是否在正确路径，再看描述是否足够明确 |
| Subagent 不委派 | 任务不够复杂、描述不聚焦、权限不合适 | 先查 agent 描述，再确认当前任务是否值得拆分 |
| MCP 连不上 | 环境变量缺失、服务未安装、网络或权限问题 | 先看 token，再看 `claude mcp add` 是否成功 |
| Hooks 不执行 | 脚本无执行权限、settings 未配置、事件名写错 | 先 `chmod +x`，再检查 `settings.json` 和事件名 |
| Plugin 装了但组件不加载 | `plugin.json` 路径错误、组件路径不一致、版本兼容性问题 | 先检查 `.claude-plugin/plugin.json` 和目录结构，再尝试 `/reload-plugins` |

如果你是团队内第一次推广 Claude Code，建议把这些排错项单独整理成内部 Runbook。这样出问题时，不会回到“谁会配、谁来救火”的人肉依赖模式。

## 十一、练习与自测

一篇顶级教程不能只有“知识点”，还要能让读者验证自己是否真的会了。下面这组练习，能快速判断你是否已经从“看懂”进入“会用”。

### 基础练习

1. 在一个真实项目里创建 `CLAUDE.md`，写入技术栈、目录结构、测试与提交规范。
2. 安装一个 Slash Command，并让它在实际任务里跑通一次。
3. 运行 `/self-assessment`，确认自己目前处在 Beginner、Intermediate 还是 Advanced。

### 进阶练习

1. 增加一个项目级 Subagent，用于代码审查或文档生成。
2. 配置 GitHub MCP，让 Claude Code 能获取 PR 或仓库信息。
3. 完成一个 `Hooks + Memory + Subagents` 组合工作流。

### 专家练习

1. 把一套真实团队流程封装成 Plugin。
2. 为 Plugin 补齐安装说明、目录结构、权限边界和排错说明。
3. 在团队中做一次最小规模试点，而不是只在个人环境里演示。

### 自测清单

- 我能解释 Slash Commands、Skills、Subagents、Plugins 的区别吗？
- 我知道哪些配置应该放项目级，哪些应该放用户级吗？
- 我知道 MCP 的项目级入口是 `.mcp.json`，也会用 `claude mcp add` 吗？
- 我知道检查点的核心操作是 `/rewind` 或 `Esc` 连按两次吗？
- 我能说清一个高质量 Claude Code 工作流，为什么必须同时包含“上下文、分工、外部数据、验证”这四层吗？

如果这 5 个问题里有 2 个以上答不稳，不建议直接跳到 Plugins 或复杂自动化，先把前 4 个模块练扎实。

## FAQ

### Q1：这篇文章和官方 Claude Code 文档分别该怎么看？

**答：** 官方文档更像参考手册，负责说明能力、参数、限制和正式接口；这篇文章更像工作流导图，重点在于告诉你这些能力应该如何组合、先学什么、先装什么、先验证什么。

### Q2：如果我只是个人开发者，还需要关心 Plugins 吗？

**答：** 不需要一开始就关心。对个人开发者来说，通常优先级是 `CLAUDE.md`、2 到 3 个高频 Slash Commands，以及 1 个到 2 个最能提高产出的 Skills 或 Subagents。只有当工作流稳定、需要跨团队复用时，再考虑 Plugin 化。

### Q3：为什么本文反复强调“学习顺序”和“装配顺序”不同？

**答：** 因为很多人理解了功能，却没有拿到即时收益；也有人快速复制了一堆配置，却并不知道自己为什么这样配。把两者拆开，才能同时兼顾认知递进和工程回报。

### Q4：最常见的落地错误是什么？

**答：** 通常不是“不会写命令”，而是过早追求大而全：一上来就装满 MCP、Hooks、Plugins、Subagents，却没有一条工作流真正稳定跑通。更稳妥的路径是先把高频任务固化，再逐步扩展。

## 十二、结论：怎么把这份指南真正用起来

Claude How To 的价值，不在于它“资料很多”，而在于它把 Claude Code 从单点功能，提升成了可复用、可协作、可打包的工作流系统。

如果你是个人开发者，最值得先做的是：

1. 用 `CLAUDE.md` 固定项目上下文。
2. 用 Slash Commands 固定高频入口。
3. 用 1 个 Skill 或 1 个 Subagent 处理最重复的任务。

如果你是团队负责人，最值得先做的是：

1. 先验证一条工作流，而不是先设计一整套平台。
2. 先把规范写成 Claude 能执行的文件，而不是只写在文档平台里。
3. 只有在工作流稳定后，再升级到 Plugin 级打包与分发。

一句话收尾：官方文档负责告诉你“有什么”，Claude How To 负责教你“怎么把这些东西真正连起来”。

## 参考链接

- [仓库主页](https://github.com/luongnv89/claude-howto)
- [学习路线图](https://github.com/luongnv89/claude-howto/blob/main/LEARNING-ROADMAP.md)
- [功能总览](https://github.com/luongnv89/claude-howto/blob/main/CATALOG.md)
- [速查卡](https://github.com/luongnv89/claude-howto/blob/main/QUICK_REFERENCE.md)
- [官方 Claude Code 文档](https://code.claude.com/docs/en/overview)
- [官方 Plugins 文档](https://code.claude.com/docs/en/plugins)
