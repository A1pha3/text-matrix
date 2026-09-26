---
title: "Claude Code Plugins 官方插件生态完全指南"
date: "2026-05-23T03:05:00+08:00"
slug: "anthropics-claude-plugins-official-guide"
github_repo: "anthropics/claude-plugins-official"
source_key: "gh:anthropics/claude-plugins-official"
description: "claude-plugins-official 是 Anthropic 官方维护的 Claude Code 插件市场与开发工具包，含 39 个官方插件与 310 个市场条目，覆盖开发、数据库、安全、监控等场景。本文详解其架构、核心组件与开发工作流。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "MCP", "AI工作流", "Anthropic"]
---

# Claude Code Plugins 官方插件生态完全指南

claude-plugins-official 是 Anthropic 官方维护的 Claude Code 插件市场与开发工具包。它由三部分组成：`plugins/` 下是 Anthropic 亲手维护的 39 个官方插件，`external_plugins/` 收录 14 个经审核的第三方合作插件，`.claude-plugin/marketplace.json` 以 310 个条目把整个生态串起来——其中 258 个直接指向外部 Git 仓库。截至 2026 年 9 月 22 日，仓库累计 36,614 Stars、4,119 Forks，Apache-2.0 协议，仍在活跃维护。

对使用 Claude Code 的团队，这个仓库回答四个问题：插件是什么、怎么安装使用、怎么开发一个自己的插件、哪些场景值得用。

**读完本文你能回答**：

- 插件系统的三个来源（`plugins/`、`external_plugins/`、marketplace.json 远程条目）各自是什么
- 怎么安装和使用一个插件
- 怎么用 plugin-dev 工具包（7 个专项 skill + create-plugin 命令）开发自定义插件
- MCP 服务器的四种类型（stdio、SSE、HTTP、WebSocket）分别适用什么场景
- 插件安全策略的四项检查分别防什么

**目录**

- [系统地图](#系统地图)
- [插件能做什么](#插件能做什么)
- [安装与使用](#安装与使用)
- [插件开发工具包详解](#插件开发工具包详解)
- [插件安全策略](#插件安全策略)
- [任务流示例：创建一个数据库插件](#任务流示例创建一个数据库插件)
- [仓库现状与维护](#仓库现状与维护)
- [适用边界](#适用边界)
- [采用建议](#采用建议)
- [常见问题](#常见问题)
- [自测题](#自测题)
- [练习](#练习)
- [进阶路径](#进阶路径)
- [资料口径说明](#资料口径说明)

---

## 系统地图

理解这个仓库，目录结构比 Stars 和 Forks 更重要：

```text
claude-plugins-official/
├── .claude-plugin/
│   └── marketplace.json        ← 插件市场清单（310 个条目，含 renames 改名映射）
├── plugins/                     ← Anthropic 官方维护的 39 个内部插件
│   ├── plugin-dev/              ← 插件开发工具包（7 个专项 skill + create-plugin 命令）
│   ├── agent-sdk-dev/           ← Agent SDK 开发套件
│   ├── mcp-server-dev/          ← MCP 服务器开发指南
│   ├── clangd-lsp/              ← C/C++ 语言服务器
│   ├── code-review/             ← PR 代码审查
│   ├── feature-dev/             ← 特性开发工作流
│   ├── security-guidance/       ← 安全提醒 Hook
│   └── ...（其余 30 余个：各语言 LSP、skill-creator、hookify、example-plugin 等）
├── external_plugins/            ← 第三方合作插件（14 个，经审核纳入）
│   ├── github/                  ← GitHub MCP 集成
│   ├── gitlab/                  ← GitLab MCP 集成
│   ├── playwright/              ← 浏览器自动化
│   ├── firebase/
│   ├── linear/
│   └── ...（terraform、asana、discord、telegram、serena 等）
└── .github/
    ├── policy/                  ← 插件安全策略（schema.json 定义审核标准）
    ├── workflows/               ← 9 个自动化 workflow（插件校验、SHA 更新、URL 检查等）
    └── scripts/                 ← 运维脚本
```

三类插件来源的边界，一张表说清：

| 来源 | 说明 | 数量（2026-09-22） | 示例 |
|------|------|------|------|
| `plugins/` | Anthropic 官方维护，源码在当前仓库 | 39 | plugin-dev、code-review、clangd-lsp |
| `external_plugins/` | 第三方合作插件，经 Anthropic 审核后纳入 | 14 | github、gitlab、playwright、firebase |
| marketplace.json 远程条目 | 指向外部 Git 仓库，由 `bump-plugin-shas.yml` 定期更新锁定 SHA | 258 | aws-amplify、datadog、notion、slack |

区分这三类来源的意义在于：`plugins/` 里的代码你能直接审，出问题可以在仓库提 issue；远程条目的代码留在上游仓库，市场清单只锁定到某个 commit SHA——装之前值得去上游看一眼。

---

## 插件能做什么

### 场景一：让 Claude Code 学会新工具

安装 GitHub 插件后，Claude Code 可以直接创建 Issue、管理 PR、搜索代码库，不用手动写 API 调用：

```bash
/plugin install github@claude-plugins-official
```

安装后在对话里直接说"帮我看看这个仓库最近有哪些 PR"，Claude Code 会通过 GitHub MCP 服务器执行操作。

### 场景二：专业领域的深度能力

插件提供的是真实工具调用，直接操作对应服务：

- **数据库**：MongoDB、ClickHouse、CockroachDB、PlanetScale、Redis——写 SQL、查 schema、拿优化建议
- **云平台**：AWS 全家桶、Azure、Google Cloud——跑 `aws iam` 命令、读文档、查定价
- **安全扫描**：Semgrep、Snyk、SonarQube、JFrog——写代码的同时跑安全检查
- **代码审查**：内置 code-review 插件含多个专业 Agent，给出带置信度的审查结果

### 场景三：自定义开发工作流

`plugin-dev` 工具包提供 7 个专项 skill，覆盖插件开发的全生命周期：

```
plugin-structure            ← 目录结构与 plugin.json 配置
plugin-settings             ← 插件配置管理（.local.md 模式）
hook-development            ← 事件驱动自动化（PreToolUse / PostToolUse / Stop 等）
mcp-integration             ← MCP 服务器接入（stdio / SSE / HTTP / WebSocket）
command-development         ← 斜杠命令开发
agent-development           ← 自定义 Agent 创建
skill-development           ← Skill 编写规范
```

另有 `create-plugin` 斜杠命令，把七个 skill 按阶段串成端到端的创建流程，详见[任务流示例](#任务流示例创建一个数据库插件)。

---

## 安装与使用

### 安装一个插件

```bash
/plugin install {plugin-name}@claude-plugins-official
```

或者在 Claude Code 内运行 `/plugin > Discover` 浏览插件市场。

安装第三方插件前先确认来源可信。Anthropic 在 README 中明确声明：不对插件包含的 MCP 服务器、文件或其他软件的安全性负责，也无法验证它们会按预期工作——装之前看一眼插件主页和源码，这一步没人替你做。

### 插件的目录结构

每个插件遵循标准结构：

```text
plugin-name/
├── .claude-plugin/
│   └── plugin.json      # 插件元数据（必须）
├── .mcp.json            # MCP 服务器配置（可选）
├── commands/            # 斜杠命令（可选）
├── agents/              # 自定义 Agent（可选）
├── skills/              # Skill 定义（可选）
└── README.md            # 文档
```

`.claude-plugin/plugin.json` 是核心，定义插件的名称、版本、作者、类别等元数据。插件上架后 `name` 字段是不可变的 slug——用户已按这个名字安装，改掉会导致 `plugin-not-found` 错误；要改显示名用 `displayName`，确实要改 slug 就得在 marketplace.json 的 `renames` 映射里加一条，让老用户下次同步时自动迁移。

---

## 插件开发工具包详解

`plugin-dev` 是整个仓库里最值得深入看的插件。插件开发涉及目录结构、MCP 接入、Hook 事件、Agent 与 Skill 编写等多个维度，plugin-dev 把这些维度拆成 7 个独立 skill，让 Claude Code 在开发过程中按需加载对应指导，避免一次性塞入过多上下文。下面拆解 5 个关键 skill。

### hook-development

事件驱动自动化的核心。Hook 是 Claude Code 在关键节点插入的检查点，让插件能在工具执行前后做验证、追加上下文、阻止危险操作。支持 9 个事件：

```text
PreToolUse        工具执行前触发
PostToolUse       工具执行后触发
Stop              主会话结束时触发
SubagentStop      子代理结束时触发
SessionStart      会话启动时触发
SessionEnd        会话结束时触发
UserPromptSubmit  用户提交 prompt 时触发
PreCompact        上下文压缩前触发
Notification      通知事件
```

Hook 分两类，按需选择：**Prompt-Based Hook** 把 `$TOOL_INPUT` 交给模型做上下文感知判断，适合"这次写入是否合适"这类需要理解语义的校验，目前支持 Stop、SubagentStop、UserPromptSubmit、PreToolUse 四个事件；**Command Hook** 执行确定性脚本，适合快速校验、文件操作和接入外部工具。两类都通过 `${CLAUDE_PLUGIN_ROOT}` 变量引用插件自身路径，保证插件在不同机器上可移植。

skill 自带两个辅助脚本：`validate-hook-schema.sh` 校验 hooks.json 的结构与语法，`test-hook.sh` 在部署前用样例输入测试 Hook。

### mcp-integration

Model Context Protocol（MCP）服务器接入。不同场景需要不同的通信模式，因此提供四种服务器类型：

| 类型 | 适用场景 | 认证方式 | 示例 |
|------|----------|----------|------|
| `stdio` | 本地工具，调起子进程 | 环境变量 | PostgreSQL、clangd |
| `SSE` | 托管服务、云 API | OAuth | GitHub、GitLab |
| `HTTP` | REST API 直连 | Token | 各类 Web API |
| `WebSocket` | 实时双向通信 | 视服务而定 | 消息推送场景 |

选择依据：本地工具优先 stdio（进程间通信开销最低）；托管服务用 SSE（支持 OAuth 认证流）；REST API 用 HTTP；需要服务端主动推送的场景才用 WebSocket。

MCP 服务器有两种配置方法。推荐在插件根目录放独立的 `.mcp.json`：

```json
{
  "database-tools": {
    "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
    "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
    "env": {
      "DB_URL": "${DB_URL}"
    }
  }
}
```

也可以在 `plugin.json` 里内联 `mcpServers` 字段。插件少时两者差别不大，服务器多了之后独立文件的边界更清晰、更好维护。`${CLAUDE_PLUGIN_ROOT}` 在两种写法中都可用。

### plugin-structure

标准目录布局与 `plugin.json` 字段说明。最小插件只需要：

```text
my-plugin/
└── .claude-plugin/
    └── plugin.json
```

`plugin.json` 关键字段：

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "插件描述",
  "categories": ["development"],
  "skills": ["./skills/my-skill"]
}
```

### agent-development

创建 Claude Code 的自定义 Agent。Agent 是带 YAML frontmatter 的 Markdown 文件：

```yaml
---
name: my-agent
description: Use this agent when [触发条件]。Typical triggers include [场景 1], [场景 2], and [场景 3].
model: inherit
color: blue
tools: ["Read", "Write", "Grep"]
---
You are [agent 角色描述]...
```

`description` 是触发关键：官方要求在其中写明触发条件并附 2-4 个典型场景示例，长度以 200-1000 字符为宜——Claude 依据这段话判断何时激活 Agent，写得含糊就会漏触发或误触发。`name` 用小写字母、数字和连字符，3-50 个字符。正文部分则按"何时调用、核心职责、分析过程、输出格式"组织。

### skill-development

Skill 是 Claude Code 自动加载的上下文指南。frontmatter 只需 `name` 和 `description` 两个字段，其中 `description` 决定 Claude 何时使用这个 Skill，官方建议用第三人称写："This skill should be used when..."。

设计上遵循渐进展开（progressive disclosure）：元数据（name + description，约 100 词）常驻上下文；SKILL.md 正文控制在 1500-2000 词，按需加载；更长的参考文档和脚本放进 `references/` 与 `scripts/`，只在需要时读取。Skill 写得臃肿，代价是常驻上下文变大、触发变钝。

---

## 插件安全策略

插件可以执行任意代码、访问文件系统、发起网络请求，因此需要审核机制防止恶意插件混入市场。仓库的 `.github/policy/schema.json` 定义了插件审核标准，核心字段如下：

| 检查项 | 说明 |
|--------|------|
| `passes` | 同时满足所有安全条件才为 true |
| `has_broad_scope_hooks` | 是否存在未做项目相关性过滤的宽范围 Hook（UserPromptSubmit/PreToolUse/PostToolUse 无差别监听，或读取超出声明范围的用户数据） |
| `has_undisclosed_telemetry` | 是否有未声明的外向网络调用（向非 MCP 主机发数据且未在描述/README 中披露并提供退出选项） |
| `description_matches_behavior` | 只读 plugin.json 描述的用户，是否会对其 Hook、遥测、数据访问感到意外 |
| `may_make_external_network_calls` | 是否发起外部网络调用 |
| `may_download_additional_software` | 是否下载额外软件 |
| `hooks` | 逐条登记注册的 Hook：事件、路径、是否受控、是否联网 |
| `violations` | 具体违规文件与问题；不通过时必须引用证据 |

`has_broad_scope_hooks` 防止插件监听全局事件窃取数据，`has_undisclosed_telemetry` 强制披露所有外向网络调用，`description_matches_behavior` 确保 README 与实际行为一致——三条各守一个入口：事件入口、网络入口、认知入口。

审核之外还有自动化兜底。`.github/workflows/` 下共 9 个 workflow：`validate-plugins.yml` 校验插件合法性，`scan-plugins.yml` 跑安全扫描，`validate-frontmatter.yml` 与 `validate-licenses.yml` 检查元数据和许可证，`bump-plugin-shas.yml` 定期更新远程插件的锁定 SHA，`check-mcp-urls.yml` 检查 MCP URL 可达性，另有处理外部 PR 范围、回滚失败更新、关闭外部 PR 的三个 workflow。

---

## 任务流示例：创建一个数据库插件

假设团队需要让 Claude Code 接入 PostgreSQL，完整流程如下：

**第一步**：问 plugin-dev "一个插件需要哪些组件"——`plugin-structure` skill 返回标准目录结构。

**第二步**：问"怎么接入 PostgreSQL MCP 服务器"——`mcp-integration` skill 给出 stdio 配置示例。

**第三步**：运行 `/plugin-dev:create-plugin`，走完 8 个阶段的引导问卷（Discovery → Component Planning → Detailed Design → Structure Creation → Component Implementation → Validation → Testing → Documentation），自动生成目录结构和 `plugin.json`。

**第四步**：测试 Hook 是否正常——`hook-development` 提供 `validate-hook-schema.sh` 和 `test-hook.sh`。

**第五步**：发布前验证——仓库 GitHub Actions 自动跑 `validate-plugins.yml` 等检查。

每一步对应一个 skill 或脚本，不用在多份文档之间来回跳转。

---

## 仓库现状与维护

- **创建时间**：2025 年 11 月 20 日
- **最近推送**：2026 年 9 月 21 日（活跃维护）
- **Stars**：36,614（2026 年 5 月下旬约 24,500，四个月增长约 1.2 万）
- **Forks**：4,119
- **主要语言**：Python（用于 GitHub Actions 脚本和自动化）
- **Open Issues 与 PR**：合计 1,030（GitHub API 口径，含 PR）
- **官方文档**：https://code.claude.com/docs/en/plugins

Anthropic 在官方文档站点上有更详细的插件开发指南，当前仓库则是插件的源码和市场清单集合地。仓库元数据截至 2026 年 9 月 22 日，之后会继续变化。

---

## 适用边界

**适合用这个仓库的场景：**

- 想让 Claude Code 接入某个外部服务——先查一下有没有对应插件
- 想开发自己的 Claude Code 插件——`plugin-dev` 是官方入口
- 想了解 Claude Code 扩展生态的能力范围

**不适合的场景：**

- 只需要 Claude Code 的基础对话能力——装插件是过度工程化
- 想找一个通用 AI Agent 框架——这是 Claude Code 的专属扩展体系，插件格式无法直接用于其他 AI 工具

---

## 采用建议

使用 Claude Code 的团队，按以下顺序探索：

1. **先用现成插件**：浏览 `/plugin > Discover`，找自己工作流中需要的工具。GitHub、GitLab、Playwright、AWS 这些插件开箱即用。
2. **再学插件开发**：发现现成插件不够用、或某类重复劳动每周都出现时，用 `plugin-dev` 工具包构建自己的插件。
3. **贡献社区**：插件有通用价值的话，通过 [plugin directory submission form](https://clau.de/plugin-directory-submission) 提交给官方市场，过审后进入 `external_plugins/` 或远程条目。

---

## 常见问题

### Q1：插件改名后，用户安装失效怎么办？

`name` 是不可变 slug，改掉后老用户会收到 `plugin-not-found` 错误。改显示名用 `displayName`；确实需要改 slug，在 marketplace.json 顶层的 `renames` 映射中加一条 `"old-name": "new-name"`，插件加载器会在用户下次同步时自动迁移。

### Q2：上游仓库只有 SKILL.md，没有 plugin.json，能上架吗？

能。marketplace.json 条目可以声明 `strict: false` 并显式列出 `skills` 数组，把上游仓库的指定目录打包为 skill-bundle 插件。每个路径相对于 `source.path`，可以跨多个子目录挑选；每个 skill 以 `<plugin-name>:<skill-name>` 注册进 Claude Code。

### Q3：Hook 写完了，怎么在发布前验证？

分两步：先跑 `validate-hook-schema.sh hooks/hooks.json` 校验结构与语法，再用 `test-hook.sh` 喂样例输入做行为测试。两个脚本都在 hook-development skill 的 `scripts/` 下。

### Q4：第三方插件上架要过多少道检查？

以 `.github/policy/schema.json` 为准：`passes` 为 true 需同时满足无宽范围 Hook、无未披露遥测、描述与行为一致三项，外加外部网络调用、额外软件下载等字段的如实登记。提交入口是 [plugin directory submission form](https://clau.de/plugin-directory-submission)。

---

## 自测题

用以下 5 题检验理解程度。

**Q1**：插件系统的三个来源（`plugins/`、`external_plugins/`、marketplace.json 远程条目）分别是什么？

<details>
<summary>查看答案</summary>

`plugins/` 是 Anthropic 官方维护的插件（当前 39 个）；`external_plugins/` 是经审核纳入的第三方合作插件（当前 14 个）；marketplace.json 远程条目是指向外部 Git 仓库的插件（当前 258 个），由 CI 定期更新锁定 SHA。
</details>

**Q2**：MCP 服务器的四种类型分别适用什么场景？

<details>
<summary>查看答案</summary>

stdio：本地工具，调起子进程，认证走环境变量；SSE：托管服务与云 API，支持 OAuth；HTTP：REST API 直连，Token 认证；WebSocket：需要服务端主动推送的实时双向通信。
</details>

**Q3**：插件安全策略中，`passes` 为 true 需要同时满足哪三项核心检查？

<details>
<summary>查看答案</summary>

`has_broad_scope_hooks` 为 false（无未过滤的宽范围 Hook）、`has_undisclosed_telemetry` 为 false（无未披露的外向网络调用）、`description_matches_behavior` 为 true（描述与实际行为一致）。
</details>

**Q4**：plugin-dev 工具包提供了哪 7 个专项 skill？

<details>
<summary>查看答案</summary>

plugin-structure、plugin-settings、hook-development、mcp-integration、command-development、agent-development、skill-development。
</details>

**Q5**：上架后的插件想改名字，正确的做法是什么？

<details>
<summary>查看答案</summary>

`name` 是不可变 slug：改显示名用 `displayName`；确需改 slug，在 marketplace.json 的 `renames` 映射中登记 `"old-name": "new-name"`，让存量用户下次同步时自动迁移，否则会报 `plugin-not-found`。
</details>

---

## 练习

### 练习 1：安装并配置一个官方插件

选一个官方插件（如 `github` 或 `code-review`），完成以下任务：

1. 用 `/plugin install` 安装插件
2. 阅读插件的 `.claude-plugin/plugin.json`
3. 在对话中测试插件功能（如创建 Issue、审查 PR）
4. 观察插件如何调用 MCP 服务器

**目标**：掌握插件的安装和配置流程，理解插件与 MCP 服务器的关系。

### 练习 2：开发一个最小插件

参考 `plugin-dev` 的流程，做一个简单插件：

1. 选一个简单功能（如读取本地文件、调用外部 API）
2. 创建 `.claude-plugin/plugin.json`，按需添加 `commands/`、`skills/`
3. 用 `validate-hook-schema.sh` 与 `test-hook.sh` 验证（若含 Hook）
4. 本地安装并测试

**目标**：理解插件的内部结构，走通从创建到测试的最短路径。

### 练习 3：审读一个第三方插件的安全性

从 `external_plugins/` 或 marketplace.json 远程条目中选一个插件，对照 `.github/policy/schema.json` 的检查维度做一次审读：

1. 读插件的 `.mcp.json` 与 `plugin.json`，列出它注册的全部 Hook（对应 `hooks` 字段的登记格式）
2. 判断有没有无差别监听全局事件的 Hook（对应 `has_broad_scope_hooks`）
3. 追查代码中的外向网络调用，看是否在 README 中披露（对应 `has_undisclosed_telemetry`）
4. 对比 README 描述与实际行为，看用户只读描述会不会被误导（对应 `description_matches_behavior`）

**目标**：掌握官方审核的检查维度，能独立评估一个第三方插件是否值得信任。

---

## 进阶路径

**试用现成插件（1-2 周）**：浏览 `/plugin > Discover`，把工作流里最费时的两三个环节换成插件方案，同时确认它们确实省了时间——不能省时间的插件就卸掉。

**学习插件开发（2-4 周）**：通读 plugin-dev 的 7 个 skill，用 `create-plugin` 命令做一个解决团队具体问题的插件，发布前对照安全策略自查一遍。

**贡献社区（1-3 个月）**：插件有通用价值就提交给官方市场，学习安全策略确保过审；持续维护、响应 issue，是插件留在市场里的前提。

---

## 资料口径说明

本文事实口径如下，供读者复核：

1. **仓库数据**：Stars、Forks、条目数、插件数量等均于 2026 年 9 月 22 日通过 GitHub API 与仓库 main 分支核实，此后会继续变化，引用时建议以仓库实时数据为准。
2. **机制描述**：插件结构、安装命令、`renames` 机制、skill-bundle 写法以仓库 README（main 分支）为准；Hook 事件与两类 Hook、MCP 服务器类型、Agent/Skill 编写规范以 `plugins/plugin-dev` 下各 SKILL.md 为准；安全检查字段以 `.github/policy/schema.json` 为准；自动化流程以 `.github/workflows/` 下 9 个 workflow 文件为准。
3. **判断边界**：本文不评价各第三方插件的工程质量。`external_plugins/` 与远程条目仅代表通过了上架审核，具体插件的安全性与维护状态需在安装前自行确认——这也是 Anthropic 在 README 中免责声明的原因。
