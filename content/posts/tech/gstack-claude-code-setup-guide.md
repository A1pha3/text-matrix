---
title: "gstack：把 Claude Code 变成虚拟工程团队的 23 个专家技能"
date: "2026-05-14T20:32:00+08:00"
slug: "gstack-claude-code-virtual-engineering-team"
description: "gstack 是 Y Combinator 总裁 Garry Tan 开源的工具集，将 Claude Code 扩展为 23 个专科角色——CEO、设计师、工程经理、QA 负责人、安全官、发版工程师——全部通过斜杠命令调用。本文从设计理念、架构解析、技能速览、安装配置四个维度，系统解读这个 9.6 万星的项目。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "AI 编程", "gstack", "YC", "开发工具", "自动化测试"]
---

# gstack：把 Claude Code 变成虚拟工程团队的 23 个专家技能

2026 年 3 月，Andrej Karpathy 在 No Priors 播客里说了一句让整个科技圈震动的话：

> "I don't think I've typed like a line of code probably since December."

Y Combinator 总裁 Garry Tan 听到这句话之后，决定把自己用 AI 编程的完整方法论开源。他把这个工具集命名为 **gstack**——目前已在 GitHub 斩获 **96,218 Stars**，是近期最受关注的开源 AI 编程工具之一。

gstack 的核心思路并不复杂：把 Claude Code 从一个单点辅助工具，扩展成一个完整的虚拟工程团队。23 个专科角色，8 个强力工具，全部通过斜杠命令调用。安装 30 秒，即可启用。

本文从设计理念、架构解析、技能速览到安装配置，对这个项目做一次完整解读。

---

## 1. 背景与动机：一个人如何跑赢一支团队

Garry Tan 在 Y Combinator 工作期间，接触了数千家初创公司。他观察到的一个规律是：**一个全情投入的创始人，效率可以远超一支传统工程团队**。

他自己也在身体力行。2026 年过去的 60 天里，他在兼职运营 YC 的同时：上线了 3 个生产级服务、完成 40+ 功能更新、GitHub 年贡献数已达 1,237 次。同一个人、同样智力投入，2026 年的产出是 2013 年的 **240 倍**——前提是用了对的工具。

gstack 就是那套工具。

## 2. 核心设计理念

### 2.1 专科制衡，而非全知助手

大多数 AI 编程工具的思路是"一个更聪明的助手"——你说什么，它做什么。gstack 反其道而行：**强制专科化**。

当你运行 `/review`，Claude Code 扮演的是" Staff Engineer "角色，专门找那些通过 CI 但会在生产环境爆炸的 bug。当你运行 `/cso`，它扮演的是"首席安全官"，用 OWASP Top 10 + STRIDE 威胁模型审计代码。

每个技能的 system prompt 里嵌入了对应的专家思维框架，而不是通用对话。这不是提示词工程，是角色模拟。

### 2.2 流程即工作流，不是工具集合

gstack 不是 23 个独立工具，而是一个完整的开发流程：

```
Think → Plan → Build → Review → Test → Ship → Reflect
```

上游技能的输出，直接作为下游技能的输入。`/office-hours` 输出的设计文档，喂给 `/plan-ceo-review` 做战略评审；`/plan-eng-review` 输出的测试计划，由 `/qa` 接手执行。没有信息断层，没有交接损耗。

### 2.3 所有 AI 编程 agent 通用

gstack 不绑定 Claude Code。它通过 `./setup --host <name>` 支持 10 种 AI 编程 agent：

| Agent | 标志 | 安装路径 |
|-------|------|---------|
| OpenAI Codex CLI | `--host codex` | `~/.codex/skills/gstack-*/` |
| Cursor | `--host cursor` | `~/.cursor/skills/gstack-*/` |
| OpenCode | `--host opencode` | `~/.config/opencode/skills/gstack-*/` |
| Factory Droid | `--host factory` | `~/.factory/skills/gstack-*/` |
| Slate | `--host slate` | `~/.slate/skills/gstack-*/` |
| Kiro | `--host kiro` | `~/.kiro/skills/gstack-*/` |
| Hermes | `--host hermes` | `~/.hermes/skills/gstack-*/` |
| GBrain (mod) | `--host gbrain` | `~/.gbrain/skills/gstack-*/` |

接入新 agent 只需要一个 TypeScript 配置文件，零代码修改。

## 3. 架构解析

### 3.1 为什么用 Bun

gstack 的 CLI 和 Server 均采用 Bun 构建。选择 Bun 有四个原因：

**第一，编译为独立二进制文件。** `bun build --compile` 输出一个 ~58MB 的可执行文件，运行时不依赖 `node_modules`，不依赖 npx，不修改 PATH。这对于安装到 `~/.claude/skills/` 这种用户目录的工具来说，非常重要。

**第二，原生 SQLite 支持。** 浏览器 Cookie  decryption 需要直接读取 Chromium 的 SQLite 数据库。Bun 内置 `new Database()`，无需 `better-sqlite3`，无需 native addon 编译，没有跨平台编译的痛苦。

**第三，原生 TypeScript 开发。** 服务器代码以 `bun run server.ts` 运行，开发时无需编译步骤。

**第四，内置 HTTP 服务器。** `Bun.serve()` 简洁高效，足以支撑整个 CLI-Server 通信层，不需要 Express 或 Fastify。

### 3.2 守护进程模型

gstack 在后台运行一个长驻 Chromium 实例，CLI 通过 localhost HTTP 与其通信：

```
Claude Code (Tool call)
        ↓
CLI (编译后二进制，读取状态文件)
        ↓ HTTP POST /command
Server (Bun.serve)
        ↓ CDP
Chromium (headless，常驻 30 分钟空闲超时)
```

首次调用冷启动 ~3 秒；之后每次命令 ~100-200ms，因为浏览器已经就绪。

状态文件 `.gstack/browse.json` 记录当前服务器进程信息（PID、端口、认证 token）。CLI 通过这个文件定位服务器，如果服务器失活则自动重启。

### 3.3 双重监听器隧道架构（v1.6.0.0）

gstack 支持 `--client` 模式，即远程 AI agent 驱动本地浏览器。安全设计为**双监听器架构**：

- **本地监听器**（`127.0.0.1:LOCAL_PORT`）：完整功能，`/health`、`/cookie-picker`、`/inspector/*` 等，仅本地访问。
- **隧道监听器**（`127.0.0.1:TUNNEL_PORT`）：仅在 `/tunnel/start` 时绑定，提供受信任的 API 端点：`/connect`（配对）、`/command`（限定命令集）、`/sidebar-chat`。

ngrok 只转发隧道监听器的端口。这意味着：即使远程攻击者拿到了隧道 token，也无法访问本地监听器上的 `/health` 或 `/cookie-picker`。物理端口分离，比 HTTP Header 检查可靠得多。

### 3.4 安全模型

Cookie 是 gstack 处理的最敏感数据。安全设计分层：

1. **Keychain 访问需用户授权。** 首次导入 Cookie 时触发 macOS Keychain 对话框，用户必须手动点击"Allow"。
2. **解密在内存完成。** Cookie 值在内存中解密（PBKDF2 + AES-128-CBC），加载到 Playwright context 后直接使用，不落盘。
3. **数据库只读访问。** 复制 Chromium Cookie DB 到临时文件，读取后删除原临时文件，不触碰真实数据库。
4. **Bearer token 认证。** 每个 HTTP 请求（ mutation 类操作）必须携带 `Authorization: Bearer <token>`，否则返回 401。
5. **侧边栏 Agent 有 6 层防御。** 包括 L1-L3 内容安全过滤、L4 ML 分类器（TestSavantAI BERT-small ONNX，22MB 本地运行）、L5 canary token 检测等。

## 4. 核心技能详解

### 4.1 战略层（Think + Plan）

| 技能 | 角色 | 功能 |
|------|------|------|
| `/office-hours` | YC Office Hours | 6 个强制追问问题，重新定义产品边界，生成设计文档 |
| `/plan-ceo-review` | CEO/Founder | 战略评审，4 种模式（扩张/选择性扩张/保持范围/收缩），挑战产品方向 |
| `/plan-eng-review` | Engineering Manager | ASCII 数据流图、状态机、边界用例、安全顾虑，锁定技术架构 |
| `/plan-design-review` | Senior Designer | 每个设计维度 0-10 评分，解释满分标准，AI Slop 检测 |
| `/plan-devex-review` | Developer Experience Lead | 20-45 个强制追问，追踪开发者摩擦点 |

### 4.2 构建层（Build）

| 技能 | 角色 | 功能 |
|------|------|------|
| `/design-consultation` | Design Partner | 从零构建设计系统，调研竞品，生成逼真产品原型 |
| `/design-shotgun` | Design Explorer | 生成 4-6 个 AI 原型变体，在浏览器中打开比较板，迭代直到满意 |
| `/design-html` | Design Engineer | 将原型转化为可发布 HTML，30KB，零依赖，检测 React/Svelte/Vue |
| `/investigate` | Debugger | 系统性根因调试，"Iron Law"：没有调查就没有修复 |

### 4.3 评审层（Review + Test）

| 技能 | 角色 | 功能 |
|------|------|------|
| `/review` | Staff Engineer | 找通过 CI 但会在生产爆炸的 bug，自动修复显而易见的问题 |
| `/design-review` | Designer Who Codes | 设计审核 + 修复，原子提交，修复前/后截图对比 |
| `/qa` | QA Lead | 真实浏览器测试，找 bug 并用原子提交修复，生成回归测试用例 |
| `/qa-only` | QA Reporter | 与 `/qa` 相同方法论，但只报告，不改代码 |
| `/devex-review` | DX Tester | 真实开发者体验审核，计时 TTHW（Time To Hello World），截图错误 |

### 4.4 发版层（Ship + Reflect）

| 技能 | 角色 | 功能 |
|------|------|------|
| `/ship` | Release Engineer | 同步 main，运行测试，审计覆盖率，push，打开 PR |
| `/land-and-deploy` | Release Engineer | 合并 PR，等待 CI 和 deploy，验证生产环境健康状态 |
| `/canary` | SRE | 部署后监控循环，监控 console 错误、性能回退、页面失败 |
| `/benchmark` | Performance Engineer | 基准测试页面加载时间、Core Web Vitals，PR 间 before/after 对比 |
| `/document-release` | Technical Writer | 更新项目所有文档以匹配发版内容 |
| `/retro` | Engineering Manager | 团队感知周回顾，按人分解，shipping streaks，测试健康趋势 |

### 4.5 浏览器与安全

| 技能 | 角色 | 功能 |
|------|------|------|
| `/browse` | QA Engineer | 真实 Chromium 浏览器，~100ms/命令，元素通过 ARIA ref 系统定位 |
| `/connect-chrome` | Browser Setup | GStack Browser，配对已登录 Chrome 浏览器，共享 cookie |
| `/cso` | Chief Security Officer | OWASP Top 10 + STRIDE 威胁模型，17 个已知误报排除规则 |
| `/pair-agent` | Multi-Agent Coordinator | 与任意 AI agent 共享浏览器，每个 agent 独立标签页 |

## 5. Ref 系统：如何让 AI 精确定位页面元素

gstack 的 `$B` 命令组通过 Playwright 控制浏览器。每个页面元素通过 **ref** 系统定位（`@e1`、`@e2`、`@c1`），而不是 CSS selector 或 XPath。

工作原理：

1. Agent 运行 `$B snapshot -i`，Server 调用 Playwright 的 `page.accessibility.snapshot()`
2. 解析器遍历 ARIA 树，为每个可访问元素分配递增 ref（`@e1`、`@e2`……）
3. 每个 ref 存储对应的 Playwright Locator：`getByRole(role, { name }).nth(index)`
4. Agent 运行 `$B click @e3`，Server 解析 ref 到 Locator，执行 `.click()`

关键设计决策：**使用 ARIA accessibility tree，而非直接修改 DOM**。这样避免了三个问题：

- **CSP 限制**：生产网站通常阻止 DOM 修改脚本
- **React/Vue/Svelte 水合**：框架调和可能清除注入属性
- **Shadow DOM**：无法从外部访问 shadow root

Ref 还有 staleness 检测：SPA 导航可能改变 DOM 而不触发 `framenavigated` 事件。因此每次 `resolveRef()` 都会先执行 `count()` 检查——如果元素数为 0，立即报错"Ref stale"，而不是等待 Playwright 的 30 秒操作超时。

## 6. 安装与快速开始

### 6.1 环境要求

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- Git
- Bun v1.0+
- Node.js（仅 Windows）

### 6.2 单人安装（30 秒）

在 Claude Code 中粘贴以下命令，Claude 自动完成剩余安装：

```bash
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack && cd ~/.claude/skills/gstack && ./setup
```

安装后向 CLAUDE.md 添加 gstack 配置段，Claude 会自动加载技能路由规则。

### 6.3 团队模式（推荐）

在仓库中运行：

```bash
(cd ~/.claude/skills/gstack && ./setup --team) && ~/.claude/skills/gstack/bin/gstack-team-init required && git add .claude/ CLAUDE.md && git commit -m "require gstack for AI-assisted work"
```

团队成员无需手动安装，每次 Claude Code 启动时自动以 1 次/小时的频率静默检查更新。

### 6.4 最小工作流演示

```bash
# 第一步：产品定义
/office-hours
# → Claude 追问 6 个强制问题，重构产品方向，生成设计文档

# 第二步：战略评审
/plan-ceo-review
# → 读取设计文档，10 节评审，挑战 scope

# 第三步：技术锁定
/plan-eng-review
# → ASCII 数据流图，边界用例，安全评审

# 第四步：评审代码
/review
# → 自动修复 2 个问题，询问是否修复 1 个竞态条件

# 第五步：QA 测试
/qa https://staging.myapp.com
# → 打开真实浏览器，点击流程，找 bug 并修复

# 第六步：发版
/ship
# → 测试从 42 个增加到 51 个，打开 PR
```

全程 8 条命令，从"daily briefing app"到生产 PR。Claude 给出的产品定义可能超出你最初的想象——它重构了问题本身。

## 7. SKILL.md 模板系统

gstack 的每个技能文档（SKILL.md）由两部分组成：

- **人类编写的模板**（`SKILL.md.tmpl`）：包含工作流、技巧、示例
- **代码元数据自动填充**（`gen-skill-docs.ts`）：编译时将命令标志、参数引用注入模板

这意味着：代码里存在的命令，必然出现在文档里；代码里不存在的命令，文档里不会出现。CI 可以用 `gen:skill-docs --dry-run` + `git diff --exit-code` 检测文档与代码的漂移。

生成文档通过三层测试：

| 层级 | 内容 | 成本 | 速度 |
|------|------|------|------|
| 1 — 静态校验 | 解析每个 `$B` 命令，与注册表比对 | 免费 | <2s |
| 2 — E2E via `claude -p` | 真实 Claude session，运行每个技能 | ~$3.85 | ~20min |
| 3 — LLM-as-judge | Sonnet 评分文档质量 | ~$0.15 | ~30s |

层级 1 每次 `bun test` 都运行；层级 2 和 3 只在 `EVALS=1` 时触发。

## 8. 适用场景与边界

### gstack 适合：

- 初次使用 Claude Code，需要结构化工作流的开发者
- 技术创始人/CEO，想保持高代码质量的个人开发者
- Tech Lead / Staff Engineer，对每个 PR 做严格评审的团队
- 需要系统性安全审计和 QA 的项目

### gstack 不适合：

- 纯单行修改（`git commit -am"fix typo"` 这类场景不需要 gstack）
- 没有明确开发流程的临时探索
- 对浏览器自动化有复杂需求但无法运行 Chromium 的环境

### 当前限制：

- Cookie decryption 仅支持 macOS（使用 macOS Keychain）
- 缺少 Linux（GNOME Keyring/kwallet）和 Windows（DPAPI）支持
- 不支持 iframe 自动发现
- 多用户支持不在路线图上

## 9. 总结

gstack 解决的根本问题是：**AI 编程工具目前太像助手，太不像团队**。

当你让 AI 建一个功能，它会执行。但当你问"这个产品方向对吗""架构选型有没有风险""UI 设计有没有 AI 味道"——通用的 AI 编程工具无法给出结构性答案。

gstack 用 23 个专科角色，每个角色有自己独立的 system prompt 和工作方法论，加上强制执行流程（Think → Plan → Build → Review → Test → Ship → Reflect），让 Claude Code 的产出质量显著提升。

MIT 协议，免费开源，适合所有想在 AI 时代保持高产的开发者。

**仓库链接**：https://github.com/garrytan/gstack

**快速安装**：

```bash
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack && cd ~/.claude/skills/gstack && ./setup
```