---
title: "Claude Plugins Official：Anthropic 把关的插件分发入口"
date: 2026-05-20T09:09:49+08:00
slug: "claude-plugins-official-anthropic-plugin-directory"
github_repo: "anthropics/claude-plugins-official"
source_key: "gh:anthropics/claude-plugins-official"
description: "拆解 anthropics/claude-plugins-official：Anthropic 官方维护的 Claude Code 插件目录。从 marketplace.json 清单、插件条目解析、plugin.json 扩展点、命名空间与不可变名称、skill-bundle 五个机制入手，串起一个第三方插件从提交审核到安装升级的完整生命周期，并给出安全信任边界与采用建议。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Anthropic", "插件系统", "MCP", "AI 工具"]
---

# Claude Plugins Official：Anthropic 把关的插件分发入口

## 学习目标

读完这篇，你将能：

- 说清这个仓库不是"又一个插件商店"，而是一套"分发协议 + 审核闸门 + 安装升级机制"。
- 区分 `marketplace.json` 与 `plugin.json` 各自管什么，看懂一个插件条目如何被解析。
- 解释插件条目的四种 `source` 来源，以及版本如何被固定。
- 说明 `name` 为什么不可变、改名为什么会触发 `plugin-not-found`。
- 判断一个第三方插件值不值得装，以及官方审核到底覆盖了哪一层。

## 目录

- [§1 先给判断](#1-先给判断)
- [§2 系统地图：三个文件的职责](#2-系统地图三个文件的职责)
- [§3 它解决的不是"缺插件"的问题](#3-它解决的不是缺插件的问题)
- [§4 机制一：marketplace.json 是目录的目录](#4-机制一marketplacejson-是目录的目录)
- [§5 机制二：一个插件条目如何被解析](#5-机制二一个插件条目如何被解析)
- [§6 机制三：plugin.json 与插件扩展点](#6-机制三pluginjson-与插件扩展点)
- [§7 机制四：命名空间与不可变名称](#7-机制四命名空间与不可变名称)
- [§8 机制五：skill-bundle 与 strict 模式](#8-机制五skill-bundle-与-strict-模式)
- [§9 任务流：一个第三方插件的一生](#9-任务流一个第三方插件的一生)
- [§10 生态观察：内部与外部，看几个真实插件](#10-生态观察内部与外部看几个真实插件)
- [§11 安全：官方审核的边界在哪](#11-安全官方审核的边界在哪)
- [§12 验证与限制：诚实披露](#12-验证与限制诚实披露)
- [§13 采用顺序与适用边界](#13-采用顺序与适用边界)
- [§14 自测题](#14-自测题)
- [§15 常见问题](#15-常见问题)
- [§16 术语对照](#16-术语对照)
- [§17 结尾判断](#17-结尾判断)
- [§18 参考与延伸阅读](#18-参考与延伸阅读)

## 信息来源约定

本文事实来自三类来源，写作时均已核验：

- **（仓库证据）**：`anthropics/claude-plugins-official` 的 README、`.claude-plugin/marketplace.json`、`plugins/example-plugin` 下的真实文件、`/plugins` 与 `/external_plugins` 目录列表。Stars 数据取 GitHub API 返回值（2026-08-28 更新，35000），仓库创建于 2025-11-20，协议 Apache-2.0。
- **（官方文档）**：`code.claude.com/docs/en/plugins` 与 `plugin-marketplaces` 的插件开发、扩展点、marketplace schema 说明。
- **（作者推断）**：基于上述证据的工程判断，文中已单独标注。

## §1 先给判断

把它理解成"又一个插件商店"，会错过这个仓库真正想解决的问题。

Claude Code 在很长一段时间里靠复制 `.claude/` 目录来分享配置。这个仓库把这条路改成了一台正经的分发机器：一个 `marketplace.json` 清单描述"有哪些插件、从哪拉、钉在哪个版本"，Claude Code 装完后把插件写进本地缓存，按命名空间注册，之后可以自动升级。仓库本身只是这台机器的目录壳，真正的机制都在清单和插件目录结构里。

第二个判断关于信任：Anthropic 没有能力、也没有声称有能力审查每个插件内部的行为。它把关的是"什么东西能进这个目录"，而不是"进目录的东西一定安全"。这一点 README 写在最前面，后面 §11 会展开。

## §2 系统地图：三个文件的职责

在进细节之前，先分清这个仓库里几类文件各自管什么。

```mermaid
graph TD
    A[claude-plugins-official 仓库] --> B[.claude-plugin/marketplace.json<br/>插件目录的目录]
    A --> C[/plugins<br/>Anthropic 内部插件]
    A --> D[/external_plugins<br/>第三方插件副本]
    B --> E[plugins[] 条目<br/>name + source + category]
    E --> F[相对路径 ./plugins/...<br/>仓库内直接引用]
    E --> G[git-subdir / url / github<br/>指向各厂商仓库]
    E --> H[npm]
    B --> I[renames 映射<br/>旧名自动迁移]
    F --> J[~/.claude/plugins/cache<br/>本地版本化缓存]
    G --> J
    J --> K[Claude Code 按 name 注册<br/>/插件名:技能名]
```

职责对照表：

| 文件 | 位置 | 管什么 | 由谁维护 |
| --- | --- | --- | --- |
| `marketplace.json` | 仓库 `.claude-plugin/` 下 | 收录哪些插件、从哪拉、钉在哪个版本、旧名迁移 | 目录维护者 |
| `plugin.json` | 每个插件的 `.claude-plugin/` 下 | 单个插件的身份：名称、描述、版本、作者 | 插件作者 |
| `.mcp.json` | 每个插件的根目录 | 插件捆绑的 MCP 服务器 | 插件作者 |
| `.lsp.json` / `monitors.json` / `settings.json` | 插件根目录 | LSP 服务器、后台监控、默认设置 | 插件作者 |

一句话分界：`marketplace.json` 管"目录"，`plugin.json` 管"单个插件"，其余文件管"这个插件扩展了什么"。

## §3 它解决的不是"缺插件"的问题

Claude Code 早在有这个目录之前就能装插件，方法是把 `.claude/` 目录拷给别人。这个仓库解决的其实是三个更上游的问题：

1. **分发与版本**。拷贝目录没有版本概念，升级只能靠重新拷。插件机制让每个插件带 `version`（或退而用 git commit SHA），用户升级时只拉变化的部分。
2. **发现与信任**。网上搜到的插件质量参差，安全无法保证。目录替用户做了第一层筛选，README 同时把"使用前请信任插件"的免责声明顶在最前面。
3. **命名冲突**。独立配置里所有人写 `/hello`，装两个就撞。插件强制用 `<插件名>:<技能名>` 命名空间，冲突被结构性地消灭。

理解这三件事，后面看机制才有坐标。

## §4 机制一：marketplace.json 是目录的目录

目录本身也是一个标准插件市场，清单文件在 `.claude-plugin/marketplace.json`（仓库证据）。文件头声明了 schema 和归属：

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "claude-plugins-official",
  "description": "Directory of popular Claude Code extensions including development tools, productivity plugins, and MCP integrations",
  "owner": {
    "name": "Anthropic",
    "email": "support@anthropic.com"
  },
  "renames": { ... },
  "plugins": [ ... ]
}
```

顶层只有五件事：`$schema`、`name`、`description`、`owner`、`renames`，剩下的全部是 `plugins` 数组。`renames` 是旧插件名的迁移表，§7 专门讲。

值得注意的一点：`name` 是公开标识。用户安装时的命令是 `/plugin install {插件名}@claude-plugins-official`，这里的 `{插件名}` 必须和 `plugins` 数组里的 `name` 完全一致，否则直接报 `plugin-not-found`。所以"目录里叫什么"是用户能感知的公开契约，改名的代价被刻意抬高。

## §5 机制二：一个插件条目如何被解析

`plugins` 数组里每个条目描述一个插件，核心是三个字段：`name`（公开标识）、`category`（分类）、`source`（从哪拉）。`source` 有四种形态（仓库证据 + 官方文档）：

| source 类型 | 字段 | 说明 | 真实例子 |
| --- | --- | --- | --- |
| 相对路径 | `"./plugins/..."` | 目录仓库内的插件，路径相对仓库根 | `agent-sdk-dev`（Anthropic 内部） |
| `url` | `url`, `sha?` | 整个 git 仓库 | `agentforce-adlc`（Salesforce，钉了 sha） |
| `git-subdir` | `url`, `path`, `ref?`, `sha?` | 大仓库里的子目录，用稀疏克隆只拉该目录 | `42crunch-api-security-testing`（钉了 v1.5.5 + sha） |
| `npm` | `package`, `version?` | 从 npm 安装 | 目录当前未大量使用 |

以 42Crunch 的真实条目为例：

```json
{
  "name": "42crunch-api-security-testing",
  "author": { "name": "42Crunch" },
  "category": "security",
  "source": {
    "source": "git-subdir",
    "url": "https://github.com/42Crunch-AI/claude-plugins.git",
    "path": "plugins/api-security-testing",
    "ref": "v1.5.5",
    "sha": "30287f5e3f122a646d1ac5ca3ab96e130c52a3ad"
  },
  "homepage": "https://42crunch.com"
}
```

这里藏着设计取舍：**`ref` 和 `sha` 是两档钉版本的方式**。`ref` 跟 tag 或分支，`sha` 钉到不可变的具体 commit。第三方插件进目录时带上 `sha`，意味着"目录收录的是这个仓库在这个 commit 的样子"，而不是"这个仓库最新是什么就装什么"。安装后插件被克隆进本地版本化缓存 `~/.claude/plugins/cache`，后续升级由版本解析决定。

另一个容易混的点：**marketplace 源和插件源是两回事**。`/plugin marketplace add` 拉的是 `marketplace.json` 这个清单本身（只支持 `ref`）；清单里每个插件条目自己的 `source` 决定插件从哪个仓库拉（支持 `ref` 和 `sha`，独立钉版本）。目录维护方与插件厂商的仓库可以完全无关，各自钉各自的版本。

## §6 机制三：plugin.json 与插件扩展点

每个插件在自己的 `.claude-plugin/plugin.json` 里声明身份。仓库里的 `example-plugin` 是标准参考（仓库证据）：

```json
{
  "name": "example-plugin",
  "description": "A comprehensive example plugin demonstrating all Claude Code extension options including commands, agents, skills, hooks, and MCP servers",
  "author": {
    "name": "Anthropic",
    "email": "support@anthropic.com"
  }
}
```

`plugin.json` 的字段（官方文档）：

- `name`：唯一标识，同时是技能命名空间（`/example-plugin:技能名`）。
- `description`：插件管理器里展示的说明。
- `version`：可选。缺省时若插件走 git 分发，用 commit SHA 当版本，每次 commit 都算新版本；显式设置后，只有版本号变化用户才收到更新。
- `author`：可选，作者署名。

**一个容易踩的坑**：只有 `plugin.json` 放在 `.claude-plugin/` 里。`commands/`、`agents/`、`skills/`、`hooks/` 必须放在插件根目录，放进 `.claude-plugin/` 里不会被加载（官方文档明确写了这是 common mistake）。

插件能扩展的东西远比"一个技能"多（官方文档完整扩展点）：

| 目录/文件 | 用途 |
| --- | --- |
| `skills/<名称>/SKILL.md` | Agent Skill，模型按任务上下文自动调用 |
| `commands/` | 扁平的 Markdown 斜杠命令（旧格式，新插件用 `skills/`） |
| `agents/` | 自定义智能体定义 |
| `hooks/`（`hooks.json`） | 事件处理钩子 |
| `.mcp.json` | 捆绑的 MCP 服务器 |
| `.lsp.json` | 语言服务器（代码智能） |
| `monitors/`（`monitors.json`） | 后台监控，逐行把 stdout 推给 Claude |
| `bin/` | 插件启用期间加入 Bash 工具 PATH 的可执行文件 |
| `settings.json` | 插件启用时应用的默认设置（目前支持 `agent` 与 `subagentStatusLine`） |

一个真实命令文件长这样（`example-plugin/commands/example-command.md`，仓库证据）：

```markdown
---
description: An example slash command that demonstrates command frontmatter options
argument-hint: <required-arg> [optional-arg]
allowed-tools: [Read, Glob, Grep, Bash]
---
```

frontmatter 支持 `description`、`argument-hint`、`allowed-tools`（预授权工具，减少权限弹窗）、`model`（覆盖模型）。`example-plugin` 的 `.mcp.json` 也很简单（仓库证据）：

```json
{
  "example-server": {
    "type": "http",
    "url": "https://mcp.example.com/api"
  }
}
```

插件还可以发 `.lsp.json`、`monitors.json`、`settings.json`（官方文档示例）：

```json
{
  "go": {
    "command": "gopls",
    "args": ["serve"],
    "extensionToLanguage": { ".go": "go" }
  }
}
```

```json
[
  {
    "name": "error-log",
    "command": "tail -F ./logs/error.log",
    "description": "Application error log"
  }
]
```

```json
{
  "agent": "security-reviewer"
}
```

把这几张图拼起来，插件的本质是"一组按约定摆放的文件 + 一份清单声明"，Claude Code 在启用时按约定把它们挂到对应扩展点。

## §7 机制四：命名空间与不可变名称

插件和独立配置最直观的区别在命令名。独立配置里 `skills/hello/SKILL.md` 是 `/hello`；插件里同名技能是 `/my-plugin:hello`。命名空间前缀来自 `plugin.json` 的 `name`，这个前缀同时消灭了不同插件间的名字冲突。

**`name` 是不可变 slug**（仓库 README 原文强调）。用户装插件用的是这个名字，改掉它，已安装用户下次同步就报 `plugin-not-found`。目录因此给了两条纪律：

1. 想改 UI 上的展示名，用 `displayName` 字段，不动 `name`（该字段由较新的 Claude Code 版本支持）。
2. 实在要改 `name`，在 `marketplace.json` 顶层 `renames` 表里加一条迁移映射，Claude Code 下次同步自动把旧名重写到新名。

真实的 `renames` 表（仓库证据，节选）：

```json
"renames": {
  "adlc": "agentforce-adlc",
  "vals": "valtown",
  "qodo-skills": "qodo",
  "azure-skills": "azure",
  "sonarqube-agent-plugins": "sonarqube"
}
```

注意这些旧名大多带 `-skills` 或 `-plugins` 后缀，说明早期命名不统一，后来靠 `renames` 收拢——这条机制是目录演进过程中沉淀出来的，不是一开始就设计好的。

## §8 机制五：skill-bundle 与 strict 模式

目录里有一类特殊的插件：上游仓库只发 `SKILL.md`，没有 `.claude-plugin/plugin.json` 清单。对这类仓库，市场条目可以用 `strict: false` 直接声明技能（仓库 README 原文）。

```json
{
  "name": "example-bundle",
  "description": "Brief description of the bundled skills.",
  "author": { "name": "Author Name" },
  "category": "development",
  "source": {
    "source": "git-subdir",
    "url": "https://github.com/example-org/sdk.git",
    "path": "packages/agent-skills",
    "ref": "main",
    "sha": "<commit sha>"
  },
  "strict": false,
  "skills": ["./skill-a", "./skill-b", "./skill-c"],
  "homepage": "https://github.com/example-org/sdk"
}
```

两个要点：

- `strict: false` 表示"组件定义不由 plugin.json 说了算"，改由市场条目显式声明 `skills` 数组。
- `skills` 数组里的路径相对 `source.path`，指向包含 `SKILL.md` 的目录；每个技能注册为 `<插件名>:<技能名>`。路径可以下沉多层，从大仓库里挑出想要的子集。

目录里的真实例子是 `amd-skills`（仓库证据）：AMD 的 skills 仓库没有 plugin.json，市场条目用 `strict: false` 显式列出 `local-ai-use`、`serving-llms-on-instinct` 等四个技能目录。

## §9 任务流：一个第三方插件的一生

把前面五个机制串成一个完整流程，以 42Crunch 的 API 安全插件为例：

1. **提交**。厂商填插件目录提交表单（`clau.de/plugin-directory-submission`），说明插件用途、仓库位置、要收录的版本。
2. **审核入库**。通过后，维护者把插件条目写进 `marketplace.json` 的 `plugins` 数组，`source` 钉到具体 commit。
3. **用户发现**。在 Claude Code 里执行 `/plugin > Discover` 浏览，或直接 `/plugin install 42crunch-api-security-testing@claude-plugins-official`。
4. **解析与拉取**。Claude Code 读 `marketplace.json`，按 `source` 稀疏克隆 42Crunch 仓库的 `plugins/api-security-testing` 子目录到 `~/.claude/plugins/cache`，记录 `sha` 作为版本锚点。
5. **注册**。按 `plugin.json` 的 `name` 建立命名空间，插件里的命令、技能、MCP 服务器挂到对应扩展点；捆绑的 MCP server 首次使用时触发权限申请。
6. **升级**。下次同步时对比缓存里的 `sha`/`version` 与市场条目声明，变了才拉新。

开发侧对应的工具链：本地开发用 `claude --plugin-dir ./my-plugin` 直接加载（支持 zip），改动后 `/reload-plugins` 热重载，`claude plugin init` 能脚手架出一个 `~/.claude/skills/` 下的插件。这套"清单 → 拉取 → 缓存 → 注册 → 升级"的链路，和 npm、Homebrew 是同一类设计。

## §10 生态观察：内部与外部，看几个真实插件

截至本文写作时（2026-08 核验），`/plugins` 目录下可见 18 个 Anthropic 内部插件，覆盖代码评审、现代化改造、安全、前端设计、各语言 LSP（clangd / gopls / csharp / jdtls）等；`/external_plugins` 目录存放部分第三方插件副本（当前可见 15 个，如 `asana`、`context7`、`discord`），其余第三方插件通过 `marketplace.json` 的 URL / `git-subdir` 源直接指向厂商仓库。

看几个有代表性的条目：

- `42crunch-api-security-testing`（security）：审计 OpenAPI 规格、按 OWASP API Security 风险（含 BOLA / BFLA）扫描，走 audit → scan → remediate → validate 循环。
- `adobe-for-creativity`（design）：背景移除、矢量化、专业修图等创意工具。
- `airtable`（productivity）：捆绑 Airtable 官方 MCP server，让 Claude 直接操作表格数据。
- `atlassian`（productivity）：接 Jira 和 Confluence，搜问题、建 issue、读文档。
- `agentforce-adlc`（development）：Salesforce 的 Agent 开发生命周期，编排 `.agent` 文件。
- `amd-skills`（development）：前面说过的 skill-bundle 例子。

条目的 `category` 字段把插件分成 security、design、development、productivity、database、monitoring 等类别，`/plugin > Discover` 的浏览体验就是按这些字段组织的。

## §11 安全：官方审核的边界在哪

README 开头的警告值得逐句读（仓库证据，原文大意）：

> 在安装、更新或使用任何插件之前，确保你信任它。Anthropic 不控制插件里包含的 MCP 服务器、文件或其他软件，也无法验证它们会按预期工作、不会改变。

这句话划出了信任模型：

- **Anthropic 控制的**：什么能进目录、每个条目的来源钉在哪个版本、`renames` 迁移是否安全。这一层解决"发现环节"的风险——你不用从犄角旮旯搜插件。
- **Anthropic 不控制的**：插件内部实际执行什么。一个插件能挂 MCP server（可能访问文件系统、网络）、`bin/` 会把可执行文件塞进 Bash PATH、hooks 会在事件发生时跑代码。这些都在 Anthropic 的能力范围之外。

所以官方目录降低的是**发现环节**的风险，不是**运行环节**的风险。运行环节的防线是 Claude Code 的权限机制：MCP server 首次使用时的权限申请、`allowed-tools` 预授权、以及你自己安装前读一遍插件的 `plugin.json` 和源码。

## §12 验证与限制：诚实披露

- **Stars 增长很快，但不等于插件质量**。仓库 2026-08 时约 35k stars。这个数字反映的是"Claude Code 生态热度"，不是目录内插件的平均水平。
- **收录标准是黑盒**。提交表单 + 审核流程存在，但细则不公开。哪些插件能进、为什么有些没进，读者无从验证。
- **外部插件版本由厂商控制**。Anthropic 只钉来源 commit，插件内容更新节奏、是否引入破坏性变更，都由厂商决定。
- **缺 `version` 的插件更新很频繁**。按 §6 的规则，走 git 分发且不写 `version` 时，每个 commit 都是新版本，升级可能比预期勤。
- **`renames` 只解决"名称变更"的兼容**。旧插件内部结构变化导致的配置失效，目录并不兜底。
- **本文事实有明确的时间戳**。目录与插件数量会持续变化，读到的结构以写作时（2026-08 核验）为准。

## §13 采用顺序与适用边界

### 13.1 谁先上

- 已经在用 Claude Code、常手动复制 `.claude/` 目录给同事的人，先装目录里的 Anthropic 内部插件（代码评审、LSP、安全），体验"装完即用 + 自动升级"。
- 团队内部要共享技能/智能体/钩子的，尽早把配置改造成插件结构，并建自己的私有 marketplace（官方文档支持私有仓库分发）。

### 13.2 谁可以等等

- 只用 Claude Code 做一次性代码问答、不长期维护扩展的，插件目录带来的收益有限。
- 对第三方代码安全零容忍、又不愿意安装前逐行读源码的环境，官方目录并不能解决你的问题，该上的是更严格的进程隔离手段。

### 13.3 采用顺序建议

1. `/plugin > Discover` 先看 Anthropic 内部插件，装一两个跑通。
2. 需要第三方能力时，优先选 `category` 匹配、有明确 `homepage` 和 `source` 钉版本的条目。
3. 生产团队：把内部共享能力做成插件，建私有 marketplace，版本用显式 `version` 而不是裸 commit SHA。
4. 想贡献的开发者：对照 `plugins/example-plugin` 写第一个插件，本地用 `--plugin-dir` 测通，再走提交表单。

## §14 自测题

1. `marketplace.json` 和 `plugin.json` 分别管什么？一个插件条目的 `source` 字段有哪几种形态？
2. 为什么插件的 `name` 不能随便改？想改 UI 展示名和真要改名字各走哪条路？
3. 一个上游仓库只有 `SKILL.md`、没有 `plugin.json`，目录怎么收录它？
4. 官方审核覆盖了哪一层风险？哪一层风险仍然需要用户自己承担？
5. 什么情况下你不会用这个目录，而是自己建 marketplace 或继续用独立配置？

<details>
<summary>参考答案</summary>

1. `marketplace.json` 管目录：收录哪些插件、从哪拉、钉在哪个版本、旧名迁移；`plugin.json` 管单个插件的身份（名称、描述、版本、作者）。`source` 有相对路径、`url`、`git-subdir`、`npm` 四种。
2. `name` 是不可变 slug，改了会导致已安装用户 `plugin-not-found`。改 UI 展示名用 `displayName`；真要改名，在 `marketplace.json` 的 `renames` 表加迁移映射。
3. 用 `strict: false` + 显式 `skills` 数组声明技能路径，每个技能注册为 `<插件名>:<技能名>`。
4. 覆盖"发现环节"：什么能进目录、来源钉在哪个版本。不覆盖"运行环节"：插件内部行为，需要用户安装前信任、安装时看权限申请。
5. 团队共享且要版本管理、私有分发时，建自己的 marketplace；单项目个人配置，继续用 `.claude/` 独立配置即可。

</details>

## §15 常见问题

**Q1：`/plugin install xxx@claude-plugins-official` 报 `plugin-not-found` 怎么办？**

检查名字是否和 `marketplace.json` 里 `plugins` 数组的 `name` 完全一致（大小写、连字符都要对）。这个名字可能是 `renames` 迁移过的旧名，也可能写成了 `displayName`。不确定就进 `/plugin > Discover` 直接浏览。

**Q2：外部插件和内部插件有什么区别？**

内部插件（`/plugins`）由 Anthropic 团队开发和维护；外部插件（`/external_plugins` 及市场条目指向的厂商仓库）来自合作伙伴和社区，经审核收录。对用户来说安装方式相同，责任主体不同。

**Q3：装第三方插件前要看什么？**

先读 `plugin.json` 声明了什么扩展点（技能、命令、agents、hooks、MCP server），再看 `.mcp.json` 连了哪些外部服务、`bin/` 会往 PATH 塞什么。MCP server 首次使用会弹权限申请，别直接全部批准。

**Q4：插件可以访问我哪些数据？**

取决于它声明和获得授权的能力。带 MCP server 的插件可能访问文件系统、网络；`bin/` 里的可执行文件会进入 Bash 工具 PATH；hooks 会在事件触发时执行代码。范围由权限机制控制，但安装前自行审查仍然必要。

**Q5：怎么开发自己的插件并提交？**

对照 `plugins/example-plugin` 的参考实现，本地用 `claude --plugin-dir ./my-plugin` 测试，改动后 `/reload-plugins` 热重载。要进入目录，走插件目录提交表单（`clau.de/plugin-directory-submission`）等待审核。

**Q6：为什么不把 `.claude-plugin/plugin.json` 和 `commands/` 放一起？**

`commands/`、`agents/`、`skills/`、`hooks/` 必须在插件根目录，`.claude-plugin/` 里只放 `plugin.json`。放错了不会被加载，这是官方文档明确列出的常见错误。

## §16 术语对照

| 中文 | 英文 | 含义 |
| --- | --- | --- |
| 插件市场清单 | Marketplace manifest | `marketplace.json`，描述目录收录什么插件 |
| 插件清单 | Plugin manifest | `plugin.json`，描述单个插件的身份 |
| 命名空间 | Namespace | 插件名给技能加的前缀，如 `/my-plugin:hello` |
| 不可变名称 | Immutable name | 插件 `name` 不可改，改了破坏安装 |
| 技能包 | Skill-bundle | `strict: false` 时直接声明技能数组的收录方式 |
| 严格模式 | Strict mode | 默认行为，`plugin.json` 是组件定义的权威 |
| 稀疏克隆 | Sparse clone | `git-subdir` 只拉子目录，省带宽 |
| 版本固定 | Version pinning | 用 `ref`（tag/分支）或 `sha`（commit）钉版本 |
| 后台监控 | Background monitors | `monitors.json` 定义，把 stdout 逐行推给 Claude |
| 钩子 | Hooks | `hooks.json` 定义的事件处理 |
| 语言服务器 | LSP | `lsp.json` 声明，提供代码智能 |

## §17 结尾判断

这个仓库真正的价值不在那几十个插件，而在它把 Claude Code 的扩展从"复制目录"升级成了"带版本、可发现、可升级的分发"。

对普通用户，它是降低发现风险的入口；对团队，它是分发内部能力的模板；对 Anthropic，它是把插件生态的入口握在自己手里的闸门。理解这一点，再回看 `marketplace.json` 的每个字段、`renames` 的每个条目，都是在看这台分发机器是怎么被设计、又被生态的反馈一点点修正的。

## §18 参考与延伸阅读

- [anthropics/claude-plugins-official 仓库](https://github.com/anthropics/claude-plugins-official)
- [Claude Code 插件开发文档](https://code.claude.com/docs/en/plugins)
- [插件市场分发文档](https://code.claude.com/docs/en/plugin-marketplaces)
- [插件完整参考（Plugins reference）](https://code.claude.com/docs/en/plugins-reference)
- [发现与安装插件](https://code.claude.com/docs/en/discover-plugins)

---

*本文事实基于 `anthropics/claude-plugins-official` 仓库（README、`.claude-plugin/marketplace.json`、`plugins/example-plugin` 及目录列表）与 `code.claude.com` 官方文档核验。Stars 数据为 GitHub API 2026-08-28 返回值；目录与插件数量随生态持续变化，以写作时核验结果为准。涉及提交审核细则、收录标准等未公开部分，已在文中标注为无法验证。*
