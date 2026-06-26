---
title: "Claude Code Plugins 官方插件生态完全指南"
date: "2026-05-23T03:05:00+08:00"
slug: "anthropics-claude-plugins-official-guide"
description: "claude-plugins-official是Anthropic官方维护的Claude Code插件市场与开发工具包，含35+官方插件与数百第三方插件，覆盖开发、数据库、安全、监控等场景。本文详解其架构、核心组件与开发工作流。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Claude插件", "MCP", "Agent SDK", "AI工作流", "Anthropic"]
---

# Claude Code Plugins 官方插件生态完全指南

## 核心判断

**claude-plugins-official** 是 Anthropic 官方维护的 Claude Code 插件市场与开发工具包，承担 Claude Code 扩展生态的中心枢纽角色。截至 2026 年 5 月 22 日，仓库积累 **24,497 Stars / 2,743 Forks**，包含 **35 个内部插件**（Anthropic 官方维护）和 **数百个第三方插件**，覆盖语言服务器、数据库连接、云平台集成、安全扫描、代码审查、开发工作流等工程场景。

本文回答四个问题：插件是什么、怎么安装使用、怎么开发、哪些场景值得用。

> **快速信息卡**
> - **Stars**: 31,137+
> - **Forks**: 3,399+
> - **License**: Apache-2.0
> - **语言**: Python
> - **最后更新**: 2026-06-26

**学习目标**：读完后你能回答——
- 插件系统的三层结构（plugins/、external_plugins/、marketplace.json 远程插件）分别是什么
- 怎么安装和使用一个插件
- 怎么开发一个自定义插件（plugin-dev 工具包的 7 个专项 skill）
- MCP 服务器的四种类型（stdio、SSE、HTTP、WebSocket）分别适用什么场景
- 插件安全策略的三项检查（has_broad_scope_hooks、has_undisclosed_telemetry、description_matches_behavior）分别防什么

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
- [自测题](#自测题)
- [进阶路径](#进阶路径)

---

## 系统地图

理解这个仓库，目录结构比 Stars 和 Forks 更重要：

```
claude-plugins-official/
├── .claude-plugin/
│   └── marketplace.json        ← 插件市场清单（所有插件的元数据）
├── plugins/                     ← Anthropic 官方维护的 35 个内部插件
│   ├── plugin-dev/              ← 插件开发工具包（含 7 个专项 skill）
│   ├── agent-sdk-dev/            ← Agent SDK 开发套件
│   ├── mcp-server-dev/           ← MCP 服务器开发指南
│   ├── clangd-lsp/               ← C/C++ 语言服务器
│   ├── code-review/             ← PR 代码审查
│   ├── feature-dev/             ← 特性开发工作流（含专用 Agent）
│   ├── security-guidance/        ← 安全提醒 Hook
│   └── ...（其他 30+内部插件）
├── external_plugins/             ← 第三方插件（经过质量审核）
│   ├── github/                  ← GitHub MCP 集成
│   ├── gitlab/                  ← GitLab MCP 集成
│   ├── playwright/              ← 浏览器自动化
│   ├── firebase/
│   ├── linear/
│   └── ...
└── .github/
    ├── policy/                  ← 插件安全策略（schema.json 定义审核标准）
    ├── workflows/               ← 自动化学件（插件 SHAs 校验、URL 检查等）
    └── scripts/                 ← 运维脚本
```

三类插件来源：

| 来源 | 说明 | 示例 |
|------|------|------|
| `plugins/` | Anthropic 官方维护，开源在当前仓库 | plugin-dev, code-review, clangd-lsp |
| `external_plugins/` | 第三方合作插件，经 Anthropic 审核后纳入 | github, gitlab, playwright, firebase |
| marketplace.json 远程插件 | 第三方插件，指向外部 Git 仓库 | aws-amplify, datadog, notion, slack |

---

## 插件能做什么

### 场景一：让 Claude Code 学会新工具

安装 GitHub 插件后，Claude Code 可以直接创建 Issue、管理 PR、搜索代码库，免去手动写 API 调用：

```bash
/plugin install github@claude-plugins-official
```

安装后，在对话中自然地说出"帮我看看这个仓库最近有哪些 PR"，Claude Code 会通过 GitHub MCP 服务器执行操作。

### 场景二：专业领域的深度能力

插件提供的是真实工具调用，直接操作对应服务：

- **数据库**：MongoDB、ClickHouse、CockroachDB、PlanetScale、Redis——直接写 SQL、查 schema、调优化建议
- **云平台**：AWS 全家桶、Azure、Google Cloud——跑 `aws iam` 命令，读文档，查定价
- **安全扫描**：Semgrep、Snyk、SonarQube、JFrog——在写代码的同时跑安全检查
- **代码审查**：内置 code-review 插件含多个专业 Agent，给出带置信度的审查结果

### 场景三：自定义开发工作流

`plugin-dev` 工具包提供了 7 个专项 skill，覆盖插件开发的全生命周期：

```
/plugin-dev:create-plugin   ← 端到端创建插件工作流（8 阶段）
hook-development            ← 事件驱动自动化（PreToolUse / PostToolUse / Stop 等）
mcp-integration             ← MCP 服务器接入（stdio / SSE / HTTP / WebSocket）
plugin-structure            ← 目录结构与 plugin.json 配置
plugin-settings             ← 插件配置管理（.local.md 模式）
command-development         ← 斜杠命令开发
agent-development           ← 自定义 Agent 创建
skill-development          ← Skill 编写规范
```

---

## 安装与使用

### 安装一个插件

```bash
/plugin install {plugin-name}@claude-plugins-official
```

或者在 Claude Code 内运行 `/plugin > Discover` 浏览插件市场。

**⚠️ 安全提示**：Anthropic 在 README 中明确说明，不对 MCP 服务器、文件或其他软件的安全性负责。安装第三方插件前，务必确认插件来源可信。

### 查看已安装的插件

```bash
/plugin list
```

### 插件的目录结构

每个插件遵循标准结构：

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json      # 插件元数据（必须）
├── .mcp.json            # MCP 服务器配置（可选）
├── commands/            # 斜杠命令（可选）
├── agents/              # 自定义 Agent（可选）
├── skills/              # Skill 定义（可选）
└── README.md            # 文档
```

`.claude-plugin/plugin.json` 是核心，定义插件的名称、版本、作者、类别和触发条件。

---

## 插件开发工具包详解

`plugin-dev` 是整个仓库里最值得深入看的插件之一。它用 **7 个专项 skill** 提供逐步展开的指导文档，覆盖插件开发的全生命周期。插件开发涉及目录结构、MCP 接入、Hook 事件、Agent 与 Skill 编写等多个维度，plugin-dev 把这些维度拆成独立 skill，让 Claude Code 在开发过程中按需加载对应指导，避免一次性塞入过多上下文。下面拆解 5 个关键 skill。

### hook-development

事件驱动自动化的核心。Hook 是 Claude Code 在关键节点插入的检查点，让插件能在工具执行前后做验证、追加上下文、阻止危险操作：

```bash
PreToolUse：工具执行前触发
PostToolUse：工具执行后触发
Stop：会话结束时触发
SessionStart / SessionEnd：会话生命周期
UserPromptSubmit：用户提交 prompt 时触发
PreCompact：上下文压缩前触发
Notification：通知事件
```

典型用途：安全检查（验证文件写入权限）、自动追加上下文（每次 `SessionStart` 加载项目信息）、阻止危险命令。

`${CLAUDE_PLUGIN_ROOT}` 是插件内引用自身路径的变量，保证插件在不同机器上可移植。

### mcp-integration

Model Context Protocol（MCP）服务器接入。不同场景需要不同的通信模式，因此提供四种服务器类型：

| 类型 | 适用场景 | 示例 |
|------|----------|------|
| `stdio` | 本地工具，调起子进程 | PostgreSQL、clangd |
| `SSE` | 托管服务，支持 OAuth | GitHub、GitLab（需认证） |
| `HTTP` | REST API 直连 | 各类 Web API |
| `WebSocket` | 实时双向通信 | 消息推送场景 |

选择依据：本地工具优先 stdio（进程间通信开销最低）；托管服务用 SSE（支持 OAuth 认证流）；REST API 用 HTTP；需要服务端主动推送的场景才用 WebSocket。

`.mcp.json` 配置示例（stdio 类型）：

```json
{
  "server-name": {
    "type": "stdio",
    "command": "the-langauge-server",
    "args": ["--stdio"]
  }
}
```

环境变量 `${CLAUDE_PLUGIN_ROOT}` 在 `.mcp.json` 中同样可用，用于构建可移植路径。

### plugin-structure

标准目录布局与 `plugin.json` 字段说明。最小插件只需要：

```
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

创建 Claude Code 的自定义 Agent。Agent 是带有 YAML frontmatter 的系统提示文件：

```yaml
---
name: my-agent
description: 何时触发这个 Agent
model: opus
color: "#ffeecc"
tools: [Read, Write, Bash]
---
[系统提示内容]
```

`description` 字段是触发关键——必须写得精准，让 Claude 在需要时能正确激活 Agent。官方建议用 `<example>` 块描述触发场景。

### skill-development

Skill 是 Claude Code 自动加载的上下文指南。标准结构：

```yaml
---
name: skill-name
description: 触发条件（描述何时应激活此 Skill）
version: "1.0.0"
---
SKILL 正文
```

遵循**逐步展开**原则：metadata → 核心 SKILL.md → 参考文献 → 示例 → 实用脚本。

---

## 插件安全策略

插件可以执行任意代码、访问文件系统、发起网络请求，因此需要审核机制防止恶意插件混入市场。仓库的 `.github/policy/schema.json` 定义了插件审核标准。提交到官方市场的插件必须通过以下检查：

| 检查项 | 说明 |
|--------|------|
| `passes` | 同时满足所有安全条件 |
| `has_broad_scope_hooks` | 是否有未做项目相关性过滤的宽范围 Hook |
| `has_undisclosed_telemetry` | 是否有未声明的外向网络调用 |
| `description_matches_behavior` | README 描述是否与实际行为一致 |

第三方插件在进入市场前，需要经过 Hook 作用域和隐式 Telemetry 的审查。`has_broad_scope_hooks` 防止插件监听全局事件窃取数据，`has_undisclosed_telemetry` 强制声明所有外向网络调用，`description_matches_behavior` 确保 README 与实际行为一致，避免伪装。

---

## 任务流示例：创建一个数据库插件

假设团队需要让 Claude Code 接入 PostgreSQL，完整流程如下：

**第一步**：问 plugin-dev "一个插件需要哪些组件"
 `plugin-structure` skill 返回标准目录结构

**第二步**：问 "怎么接入 PostgreSQL MCP 服务器"
 `mcp-integration` skill 给出 stdio 配置示例

**第三步**：运行 `/plugin-dev:create-plugin`，回答 8 阶段问卷
 自动生成目录结构和 `plugin.json`

**第四步**：测试 Hook 是否正常
 `hook-development` 提供 `validate-hook-schema.sh` 和 `test-hook.sh`

**第五步**：发布前验证
 仓库 GitHub Actions 自动跑 `validate-plugins.yml` 检查

这个流程把"查文档→搭骨架→接 MCP→测 Hook→过 CI"串成一条线，每一步对应一个 skill 或工具，避免在多个文档间来回跳转。

---

## 仓库现状与维护

- **创建时间**：2025 年 11 月 20 日
- **最后更新**：2026 年 5 月 22 日（活跃维护）
- **Stars**：24,497
- **主要语言**：Python（用于 GitHub Actions 脚本和自动化）
- **Open Issues**：690（社区活跃度高）
- **官方文档**：https://code.claude.com/docs/en/plugins

Anthropic 在官方文档站点上有更详细的插件开发指南，当前仓库是插件的源码和文档集合地。

> 仓库元数据截至 2026 年 5 月 22 日，后续会有变化。

---

## 适用边界

**适合用这个仓库的场景：**
- 想让 Claude Code 接入某个外部服务（查一下有没有对应插件）
- 想开发自己的 Claude Code 插件（`plugin-dev` 是官方入口）
- 想了解 Claude Code 扩展生态的能力范围

**不适合的场景：**
- 只需要 Claude Code 的基础对话能力（装插件是过度工程化）
- 想找一个通用 AI Agent 框架（这是 Claude Code 的专属扩展，无法用于其他 AI 工具）

---

## 采用建议

使用 Claude Code 的团队，按以下顺序探索：

1. **先用现成插件**：浏览 `/plugin > Discover`，找自己工作流中需要的工具。GitHub、GitLab、Playwright、AWS 这些插件开箱即用。
2. **再学插件开发**：当发现现成插件不够用，或有重复性工作流时，用 `plugin-dev` 工具包构建自己的插件。
3. **贡献社区**：如果你的插件有通用价值，通过 [plugin directory submission form](https://clau.de/plugin-directory-submission) 提交给官方市场。

从用插件到写插件，是降低工程团队日常重复劳动的有效路径。

---

## 常见问题

### Q1：插件安装后，为什么 slash commands 不出现？

**原因**：只装了命名 agent，没有装对应的 vertical plugin。

**解决**：命名 agent 打包了自己的 skills 副本，但 slash commands 定义在 `vertical-plugins/<vertical>/commands/` 下。如果想用 `/comps`、`/dcf` 这类命令，需要装对应的 vertical plugin。

### Q2：改了 skill 文件，但 agent 行为没变化？

**原因**：命名 agent 读的是 `agent-plugins/<slug>/skills/` 下的副本，不是 `vertical-plugins/<vertical>/skills/` 源文件。

**解决**：改完源文件后，运行 `python3 scripts/sync-agent-skills.py` 把更新推到所有打包了该 skill 的 agent。

### Q3：MCP 连接器配置了，但 AI 没有调用？

**原因**：Skills 层逻辑不变，但 Connector 需要在 `.mcp.json` 中正确配置，且 AI 需要根据上下文自动判断何时调用。

**解决**：检查 `.mcp.json` 配置是否正确，确认 MCP 服务器已启动，查看 AI 的推理过程了解为何没有调用。

### Q4：插件安全策略的三项检查分别防什么？

**A**：
- `has_broad_scope_hooks`：防止插件监听全局事件窃取数据
- `has_undisclosed_telemetry`：强制声明所有外向网络调用
- `description_matches_behavior`：确保 README 与实际行为一致，避免伪装

### Q5：开发一个 MCP 服务器时，工具的 description 字段应该怎么写？

**A**：说明工具的用途（实现细节交给代码）、列举典型的输入格式和输出示例、指明适用场景和禁忌场景。

---

## 自测题

1. **插件系统的三层结构（plugins/、external_plugins/、marketplace.json 远程插件）分别是什么？**  
   → plugins/ 是Anthropic官方维护的插件；external_plugins/ 是第三方合作插件（经审核）；marketplace.json 远程插件是第三方插件（指向外部Git仓库）

2. **MCP 服务器的四种类型（stdio、SSE、HTTP、WebSocket）分别适用什么场景？**  
   → stdio：本地工具，调起子进程（如PostgreSQL、clangd）；SSE：托管服务，支持OAuth（如GitHub、GitLab）；HTTP：REST API直连；WebSocket：实时双向通信（消息推送场景）

3. **插件安全策略的三项检查（has_broad_scope_hooks、has_undisclosed_telemetry、description_matches_behavior）分别防什么？**  
   → has_broad_scope_hooks：防止插件监听全局事件窃取数据；has_undisclosed_telemetry：强制声明所有外向网络调用；description_matches_behavior：确保README与实际行为一致，避免伪装）

4. **plugin-dev 工具包提供了哪7个专项skill？**  
   → hook-development、mcp-integration、plugin-structure、plugin-settings、command-development、agent-development、skill-development

5. **开发一个MCP服务器时，工具的 description 字段应该怎么写？**  
   → 说明工具的用途（实现细节交给代码）、列举典型的输入格式和输出示例、指明适用场景和禁忌场景）

---

## 进阶路径

### 阶段一：试用现成插件（1-2周）
- 浏览 `/plugin > Discover`，找自己工作流中需要的工具
- 安装GitHub、GitLab、Playwright、AWS等开箱即用插件
- 确认插件是否真的提升工作效率

### 阶段二：学习插件开发（2-4周）
- 当发现现成插件不够用，或有重复性工作流时，使用 `plugin-dev` 工具包
- 学习7个专项skill，掌握插件开发全生命周期
- 开发一个自定义插件，解决团队的具体问题

### 阶段三：贡献社区（1-3个月）
- 如果插件有通用价值，通过 [plugin directory submission form](https://claude.com/plugin-directory-submission) 提交给官方市场
- 学习插件安全策略，确保插件通过审核
- 参与社区讨论，了解其他开发者的需求

### 阶段四：构建插件生态（3个月+）
- 为团队构建插件体系，覆盖常用工作流
- 建立插件审核机制，确保安全性
- 分享插件开发经验，帮助更多人上手

