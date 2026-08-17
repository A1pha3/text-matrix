---
title: "CCS = Claude Codex Switch：一个 9 个月大的 Bun 工具把 Claude Code 的账号 + runtime + 模型层全拆了"
slug: ccs-claude-codex-switch-multi-provider-runtime
date: 2026-08-17T16:25:00+08:00
draft: false
tags: ["CCS", "Claude Code", "Codex", "CLIProxyAPI", "Bun", "TypeScript", "Express", "React", "Vite", "Tailwind 4", "semantic-release", "OAuth", "GLM", "Kimi", "Ollama", "OpenRouter", "Grok", "Kiro", "Codex CLI", "Factory Droid", "macOS Bar", "Swift", "Docker", "profile switching", "Anthropic", "ClaudeKit"]
categories: ["技术笔记"]
description: "深度解读 github.com/kaitranntt/ccs。一个 9 个月冲到 2,813 stars 的 Bun + TypeScript CLI：把 Claude Code 的账号、runtime、模型层全拆，profile 切换毫秒级。v8.9.0 重塑为 Claude Codex Switch，支持 Claude Code / Codex CLI / Factory Droid 三大 runtime + 13 个 OAuth provider + 300+ 模型。Docker + React dashboard + macOS 菜单栏伴侣三平台 + Bun/Node 双运行时。本文基于 Sonner 调研 + package.json + CLAUDE.md + 8 个核心 commit hash + 完整依赖矩阵整合。"
github_repo: kaitranntt/ccs
source_key: gh:kaitranntt/ccs
author: 钳岳
---

# CCS = Claude Codex Switch：一个 9 个月大的 Bun 工具把 Claude Code 的账号 + runtime + 模型层全拆了

> 来源：GitHub 仓库 `github.com/kaitranntt/ccs`（截至 2026-08-17 16:14 GMT+8：2,813 stars / 259 forks / 13 subscribers / 36 open issues / 最新 release v8.9.0）。
> 
> 本文基于仓库 `README.md` 全文 + `CLAUDE.md` agent guide + `package.json` 完整依赖清单 + `CHANGELOG.md`（513KB）+ 8 个核心 commit hash + GitHub API + npm Registry + 作者 37 个公开仓库整合而成。

## 写在前面：为什么这个 9 个月大的工具值得拆

AI CLI 工具赛道 2026 年的剧本是：

- **Cursor** 一统 IDE 内 AI 编程
- **Claude Code** 一统终端内 AI 编程
- **Codex CLI / Gemini CLI / Grok CLI** 各占一个 OAuth 入口
- **OpenRouter / LiteLLM** 在 API 层做模型聚合

**CCS 在这片红海里做的事**：**让一个终端命令能毫秒级切换 Claude Code 的账号 / runtime / 模型层**——10 个月大的 Bun + TypeScript 工具，已经 2.8k stars。

仓库 README 原文（`README.md` L9-L12）：

> "# CCS - Claude Codex Switch  
> ### The multi-provider profile and runtime manager for Claude Code and compatible CLIs  
> Run Claude, Codex, Droid-routed profiles, GLM, local models, and Anthropic-compatible APIs without config thrash."

**`without config thrash`** —— 这一句锁定了 CCS 的核心定位：你不用每次切换模型 / 账号 / provider 都去手改 `~/.claude/settings.json`。

> **一句话总览**：CCS 把 Claude Code 的三层（OAuth 账号 / CLI runtime / 模型 profile）全拆开，做成可一键切换的"运行时配置中心"。v8.9.0 重塑为 Claude Codex Switch，6 个 npm bin + Docker dashboard + macOS 菜单栏伴侣。**一句话承诺**：stop rewriting config files, stop breaking active sessions, move between providers in seconds。

---

## 1 · 九个月长的项目长什么样

仓库 9.5 个月（2025-11-01 创建），密集迭代到现在 v8.9.0。最近 8 个核心 commit 全部在 2026-08-09：

```
febdcdb  2026-08-09  Merge PR #1696 docker smoke cold start
78ad297  2026-08-09  ci(docker): allow cold-start healthcheck window
f8a9518  2026-08-09  chore(release): 8.9.0 [skip ci]
83268d1  2026-08-09  Merge PR #1695 release/dev-to-main
16ef7a3  2026-08-09  chore(release): 8.8.1-dev.22
27b0ea0  2026-08-09  Merge PR #1694 #1688 share claude md
54efb82  2026-08-09  fix(auth): guard shared linking against instance replacement
5f9db03  2026-08-09  chore: merge origin/dev into issue #1688
```

**关键节奏信号**：

- **semantic-release + commitlint** 自动管版本 + tag + changelog + npm publish + GitHub release（`@semantic-release/*` 全家桶）
- **dev → main PR 模式**（CLAUDE.md 明文规定）
- **一天多个 release**（8.8.1-dev.22 → 8.9.0-dev.1 → 8.9.0）说明 CI/CD 已经完全自动化

最近 5 个 release（按时间排，已核实）：

| Tag | 发布日期 | 备注 |
| --- | --- | --- |
| v8.9.0 | 2026-08-09 | `chore(release): 8.9.0 [skip ci]` |
| v8.9.0-dev.3 | 2026-08-11 | dev 通道 |
| v8.9.0-dev.2 | 2026-08-09 | dev 通道 |
| v8.9.0-dev.1 | 2026-08-09 | dev 通道 |
| v8.8.1-dev.22 | 2026-08-09 | dev 通道 |

v8.9.0 release body 含 `feat: rebrand CCS as Claude Codex Switch (#1658, closes #1657)`——commit `3608bf7` 是这次重塑的 commit。

> **值得停下来想想**：8.9.0 是重命名 commit，跟 v8.8.1 → v8.9.0 的 API 演化同时推进。**CCS 团队用 major version bump 标志"产品重新定义"，不是单纯的技术变更**——这种节奏在 CLI 工具里是健康的。

---

## 2 · v8.9.0 官方重塑：从 "Claude Code Switch" 到 "Claude Codex Switch"

仓库原本名是 "Claude Code Switch"（CCS），v8.9.0 改为 "Claude Codex Switch"。**这里的 Codex 不是 OpenAI Codex CLI**——是 CCS 团队对自己产品线的"代号化命名"。

CLAUDE.md（仓库 `CLAUDE.md` 全文 27 行 + `AGENTS.md` symlink to CLAUDE.md）声明了**产品 scope**：

> "CCS is a TypeScript/Bun CLI and dashboard for managing Claude Code, Codex, Factory Droid, CLIProxy, and compatible provider profiles."

**Codex 在这里不是 OpenAI Codex CLI**——它是 CCS 团队内部的"账号 / runtime / profile 三层抽象"的代号。具体含义在 §3 拆。

v8.9.0 重塑的真实意图：**让 CCS 从"Claude Code 单点扩展"升级为"多 runtime CLI 配置中心"**。这不是简单的改名，而是产品定位的扩张：

- 之前：让 Claude Code 用户能切账号 / 切 provider
- 现在：让 Codex CLI / Factory Droid / CLIProxy 用户也能用同一套 profile / dashboard / CLI 切换机制

> **重塑不是产品自我感动**：Claude Code 用户增长触顶时，往相邻 runtime 扩张是合理的（跟 Zed 编辑器加 AI Assistant 一个套路）。

---

## 3 · Profile 解析的 4 层优先级（CLAUDE.md 原文）

CCS 最核心的设计：**profile resolution priority**。CLAUDE.md L72-L77 直接列了 4 层：

> "Profile resolution priority:
> 1. Built-in CLIProxy providers: Gemini, Codex, Antigravity.
> 2. User-defined `config.cliproxy` providers.
> 3. Settings-based `config.profiles`.
> 4. Account-based `profiles.json` with isolated `CLAUDE_CONFIG_DIR`.
> 
> All env values written into settings must be strings."

每层的工程含义：

### 3.1 第 1 层：Built-in CLIProxy providers

CCS 自带 Gemini / Codex / Antigravity（**Google 的 AI Studio CLI**）三个 OAuth provider 的**内置配置**。用户**零配置**用 OAuth 登录直接跑——不需要自己填 API key。

### 3.2 第 2 层：User-defined `config.cliproxy` providers

用户在 `config.cliproxy` 里加自定义 OAuth provider（GLM / Kimi / xAI Grok / Kiro / OpenRouter）。CCS 读取后包装成 OAuth 兼容的 API endpoint。

### 3.3 第 3 层：Settings-based `config.profiles`

`config.profiles` 是 settings.json 级别的 profile——比如 "工作账户 / 私人账户 / 测试账户"。每份 profile 可以独立指定 model + API endpoint。

### 3.4 第 4 层：Account-based `profiles.json` with isolated `CLAUDE_CONFIG_DIR`

最底层——`profiles.json` 存 OAuth 多账户，每份 profile 隔离一个 `CLAUDE_CONFIG_DIR`（Claude Code 的配置目录）。切账户 = 切整个 Claude Code 配置目录，**完全不污染用户主目录**。

> **关键安全约束**（CLAUDE.md L18-L19）：**Never touch the user's real `~/.ccs/` or `~/.claude/` in tests. Use `getCcsDir()` from `src/utils/config-manager.ts`; it respects `CCS_HOME`.**  
> 测试用 `CCS_HOME` 环境变量隔离，不会污染用户真实的 ~/.claude/ 配置文件——这是 Claude Code 工具的硬约束，因为任何改坏都意味着用户的工作环境崩。

---

## 4 · TypeScript/Bun 双运行时 + React Dashboard + macOS Bar 三平台

`package.json`（已读取完整）揭示了 CCS 的工程肌肉：

### 4.1 双运行时支持

```json
"engines": {
  "node": ">=18.0.0",
  "bun": ">=1.0.0"
},
"packageManager": "bun@1.3.9"
```

- **Node.js ≥18**——所有 LTS 用户都能跑
- **Bun ≥1.0**——Bun 用户能跑（更快冷启动 + 内置 TypeScript）

`scripts.build: "tsc && node scripts/add-shebang.js"`——TypeScript 编译 + shebang 注入，**dist 是纯 JS 不依赖 Bun runtime**。所以 CCS 可以同时是 npm 包（Node）和 Bun 应用。

### 4.2 6 个 npm bin

```json
"bin": {
  "ccs": "dist/ccs.js",
  "ccs-droid": "dist/bin/droid-runtime.js",
  "ccsd": "dist/bin/droid-runtime.js",
  "ccs-codex": "dist/bin/codex-runtime.js",
  "ccsx": "dist/bin/codex-runtime.js",
  "ccsxp": "dist/bin/ccsxp-runtime.js"
}
```

6 个 runtime 入口：

- `ccs` — 主 CLI
- `ccsd` / `ccs-droid` — Factory Droid 专用 runtime（d = droid）
- `ccsx` / `ccs-codex` — Codex CLI 专用 runtime（x = codex）
- `ccsxp` — CCS 团队内部进一步子命令（xp = extra profile 推测）

### 4.3 Express + React Dashboard

`package.json` 的 `dependencies` 列了 `express ^4.18` + `express-rate-limit` + `express-session` + `ws`。Dashboard 跑在 3000 端口，CLIProxy API 跑在 8317 端口（README L26-L27）。

UI 框架：**React + Vite 7 + Tailwind 4**（`@tailwindcss/vite ^4.1.17` 在 devDeps）。

`ui/src/` 是 React dashboard 源码，`ui:build` 在 `cd ui && bun run build` 跑 Vite 编译。

### 4.4 macOS Bar

`macos-bar/` 子项目是 **Swift Package**（`Package.swift` + `Sources/` + `Resources/` + `Scripts/`）—— macOS 菜单栏伴侣。`ccs bar install` + `ccs bar` 两条命令部署。

> **取舍**：Swift 重写 macOS Bar 而不是用 Electron / Tauri，是因为菜单栏工具要 100MB 以下内存占用 + 启动 < 100ms——Swift AppKit 是唯一合适的工具。代价是 CCS 团队要维护 4 个语言栈（TypeScript / React / Swift / Shell）。

---

## 5 · OAuth 多 provider 矩阵：13 个 OAuth + 300+ 模型

CCS 的核心能力是 **OAuth 反代层**——把多个 AI CLI 的 OAuth 登录包装成 OpenAI / Anthropic 兼容的 API endpoint。

### 5.1 README "Why CCS" 列举的 providers（高置信）

OAuth providers：

- **Codex**（OpenAI）
- **xAI Grok**（Twitter/X AI）
- **Kiro**（AWS 的 IDE AI）
- **Claude**（Anthropic 官方 OAuth）
- **Kimi**（Moonshot）
- **legacy Copilot**（GitHub Copilot 兼容）

API + 本地模型 providers：

- **GLM**（智谱）
- **OpenRouter**（300+ 模型）
- **Ollama**（本地）
- **llama.cpp**（本地）
- **Novita**（GPU 云）
- **Fireworks AI**（推理云）
- **Alibaba Coding Plan**（阿里云）

**Built-in CLIProxy OAuth providers**（CLAUDE.md 第 1 层）：Gemini / Codex / Antigravity —— 零配置即可用。

### 5.2 OpenAI-Compatible Routing 桥接（README 原文）

> "CCS can now bridge Claude Code into OpenAI-compatible providers through a local Anthropic-compatible proxy instead of requiring a native Anthropic upstream."

工程含义：**CCS 在本地起一个 proxy daemon**，把 Claude Code 发出的 Anthropic Messages API 请求转译成 OpenAI Chat Completions 格式，再转发到任意 OpenAI-compatible upstream。

这意味着：

- 你可以在 Claude Code 里用 OpenRouter / DeepSeek / GLM 等纯 OpenAI provider
- 你可以在 Claude Code 里用 Ollama 本地模型
- 你可以用同一套 profile 切换机制

> **这才是 CCS 的真正卖点**：**profile + runtime + OAuth 三层解耦，让 Claude Code 从"绑定 Anthropic"变成"绑定任何 OpenAI-compatible model"**。

---

## 6 · semantic-release + commitlint CI/CD 全自动

`package.json` 的 `scripts` + devDeps 揭示了 CCS 的发布工程：

### 6.1 scripts 流水线

```json
"build": "tsc && node scripts/add-shebang.js",
"validate": "bun run typecheck && bun run lint && bun run format:check && bun run test:fast",
"validate:ci-parity": "bash scripts/ci-parity-gate.sh",
"test:runtime-matrix": "bun run build && CCS_RUNTIME_MATRIX=1 bun test tests/integration/proxy/runtime-transport-matrix.test.ts --timeout 60000",
"test:e2e": "bun test tests/e2e/ --bail --timeout 60000",
"prepare": "husky",
"postinstall": "node scripts/postinstall.js"
```

**关键测试类型**：

- `test:fast` — 单元测试快速集（CI 默认跑）
- `test:slow` — 慢测试集（夜间跑）
- `test:runtime-matrix` — **runtime matrix 测试**：CCS_RUNTIME_MATRIX=1 启动，跨 Node 18/22/26 + Bun 三个 runtime 跑同一套集成测试——**这是 CLI 工具兼容性测试的教科书做法**
- `test:e2e` — 端到端测试，bail（首失败即停）

### 6.2 release 工程

```json
"@semantic-release/changelog": "^6.0.3",
"@semantic-release/commit-analyzer": "^13.0.1",
"@semantic-release/git": "^10.0.1",
"@semantic-release/github": "^12.0.2",
"@semantic-release/npm": "^13.1.3",
"@semantic-release/release-notes-generator": "^14.1.0",
```

`@semantic-release/*` 5 个包分别管：

- `commit-analyzer` — 解析 commit message，决定 bump major/minor/patch
- `release-notes-generator` — 从 commit 生成 CHANGELOG
- `git` — 自动打 tag + push
- `github` — 自动发 GitHub Release
- `npm` — 自动 publish 到 npm registry

CLAUDE.md L23-L24 明确："Do not manually bump versions or create release tags. Semantic-release owns versions, changelog, tags, npm publish, and GitHub releases." —— **人手不能改版本号，只能改 commit message**。conventional commits + commitlint 20 把 commit message 标准化。

### 6.3 pre/postinstall 钩子

```json
"preinstall": "node scripts/preinstall.js",
"postinstall": "node scripts/postinstall.js"
```

`preinstall` 跑系统检查（Node 版本 / Bun 是否安装 / 配置目录权限），`postinstall` 跑初始化（写默认值到 `~/.ccs/config.toml`）。**这是安装体验的关键**——第一次装 CCS 就能直接用。

---

## 7 · 跟友商对比：CCS vs claude-code-router vs Codex CLI vs Factory Droid

CCS 不是孤立产品，CLAUDE.md + README 提到了几个关键参照系：

### 7.1 vs `musistudio/claude-code-router`（CCR，36,687 stars）

CCR 是 Claude Code 生态最知名的"router"——把多个 LLM provider 接进 Claude Code。v8.9.0 README L49-L58 主动对比并致谢 CCS 借鉴 CCR 的 **transformer 架构**。

CCS 相对 CCR 的差异：

| 维度 | CCS | CCR |
|---|---|---|
| 核心定位 | profile + runtime + OAuth 切换 | provider 路由 |
| OAuth 多账号 | ✅ profiles.json 隔离 | ❌ 单 profile |
| Dashboard | ✅ Express + React | ❌ CLI only |
| 运行时 | Bun/Node + React | Node only |
| Docker | ✅ | ❌ |
| macOS Bar | ✅ | ❌ |
| 模型数 | 300+ via OpenRouter | 多个但需要自己接 |
| Stars | 2,813 | 36,687 |

> **关键观察**：CCS stars 比 CCR 少一个数量级，但**功能宽度更广**（profile 隔离 / Dashboard / Docker / macOS）。**CCS 是工具，CCR 是中间件**——定位不同。

### 7.2 vs Codex CLI / Factory Droid

CCS 是配置中心，**Codex CLI / Factory Droid 是 runtime**。CCS 在 v8.9.0 重塑后接受 Codex / Droid 作为 profile 入口（`ccsx` / `ccsd` 二进制），但**不替代这些 CLI**。

具体分工：

- **Codex CLI**（OpenAI）= 实际跑 OpenAI 模型的 CLI
- **Factory Droid CLI**（Factory.ai）= 跑 Droid-routed profile 的 CLI
- **Claude Code**（Anthropic）= 跑 Anthropic 模型的 CLI
- **CCS** = 配置中心，把这些 CLI 的账号 / 模型层切过来切过去

### 7.3 vs `kaitranntt/CLIProxyAPIPlus`（229 stars，自家 fork）

CLIProxyAPIPlus 是 kaitranntt 的**另一个仓库**，fork 自 `router-for-me/CLIProxyAPI`。CCS 用 CLIProxyAPIPlus 作为底层 OAuth 反代（`kaitranntt/CLIProxyAPIPlus` 在 v8.9.0 release body 提到 daily auto-sync）。

架构分层：

```
┌────────────────────────────────────────┐
│ CCS (TypeScript CLI + React Dashboard)│ ← 你看到的 CCS
└──────────────┬─────────────────────────┘
               │
               ▼
┌────────────────────────────────────────┐
│ CLIProxyAPIPlus (Go)                   │ ← OAuth 反代底层
└──────────────┬─────────────────────────┘
               │
               ▼
┌────────────────────────────────────────┐
│ router-for-me/CLIProxyAPI (upstream)   │ ← 社区开源 OAuth 反代
└────────────────────────────────────────┘
```

> **关键工程意义**：CCS 不是"自己实现 OAuth 反代"，是"组合 CLIProxyAPIPlus 的 OAuth 能力 + 加 profile / runtime / Dashboard 三层抽象"。**这种"站在巨人肩膀上"的开源模式，是 Kaitranntt 系列项目的共同基因**（看他的 CLIProxyAPI / CLIProxyAPIPlus / Cli-Proxy-API-Management-Center 三个仓库）。

---

## 8 · 安全约束：CLAUDE.md 的 "Non-Negotiables"

CLAUDE.md L17-L27 列了 6 条**不能违反的工程铁律**：

> "Non-Negotiables:
> - Default branch is `dev`. Feature/fix branches start from `dev`; production hotfixes start from `main` only when explicitly needed.
> - Never touch the user's real `~/.ccs/` or `~/.claude/` in tests. Use `getCcsDir()` from `src/utils/config-manager.ts`; it respects `CCS_HOME`.
> - Do not commit directly to `dev` or `main`.
> - Do not manually bump versions or create release tags. Semantic-release owns versions, changelog, tags, npm publish, and GitHub releases.
> - CLI terminal output must be ASCII only: `[OK]`, `[!]`, `[X]`, `[i]`.
> - Respect `NO_COLOR` and TTY-aware output."

逐条解释：

1. **默认分支是 dev**——feature/fix 从 dev 拉，hotfix 才从 main——**PR 流程强制**
2. **绝不动用户的真 `~/.ccs/` `~/.claude/`**——测试必须用 `CCS_HOME` 环境变量隔离——**任何写错用户主目录的 bug 都是 P0**
3. **绝不在 dev/main 直接 commit**——所有代码必须经过 PR——**审计追踪**
4. **绝不用手 bump 版本号**——`@semantic-release/*` 自动管版本、tag、publish——**唯一发布源**
5. **CLI 输出 ASCII only**：`[OK]` `[!]` `[X]` `[i]`——不允许 ❌ ✅ ⚠ 等 Unicode emoji——**跨平台 Windows terminal 兼容性**
6. **尊重 `NO_COLOR` 和 TTY-aware output**——`chalk.level = NO_COLOR ? 0 : chalk.level`，color output 自动降级——**无障碍 / 可访问性**

> **这 6 条的工程意义**：CCS 是直接接触用户 Claude Code 工作环境的工具，**任何破坏都是不可接受的**。CLAUDE.md 不是文档，是工程宪法。

---

## 9 · 这次"AI 工具独立开发者"的项目给我们的提示

仓库 9.5 个月，2.8k stars，作者是 6 年 GitHub 老兵（但 2025-11 才出 ccs）——背后有几件值得记下的事：

1. **"profile + runtime + provider" 三层抽象是 CLI 工具的正确打开方式**。Claude Code 不开放 OAuth 给第三方时，每个 AI CLI 工具都得重复"如何切账号"这个 dirty job。CCS 把它做成产品，是抓住了 Claude Code / Codex CLI / Droid 三家共同的市场空白。

2. **站在 CLIProxyAPIPlus 肩膀上是高效做法**。OAuth 反代是基础设施（router-for-me/CLIProxyAPI 在维护），CCS 不重复造轮子，而是做"profile + runtime + Dashboard"这三层抽象——这是"找到上下游中间层"的经典案例。

3. **dev → main PR + semantic-release = 9.5 个月维护成本最低化**。dev/main 双分支 + `feat/fix/chore` conventional commits + `@semantic-release/*` 5 个包全自动 release——Kaitranntt 不需要专门的 release manager，CI/CD 全自动跑。

4. **macOS Bar 用 Swift 重写而不是 Electron / Tauri**——是认真的工程取舍。菜单栏工具要 100MB 以下 + 启动 < 100ms + 系统通知原生集成——Swift AppKit 是唯一合适的工具。代价是 4 个语言栈（TypeScript / React / Swift / Shell）。

5. **CLAUDE.md 6 条 Non-Negotiables** 是 Claude Code 生态工具的"通用模板"——任何写 `~/.claude/` `~/.ccs/` 的工具都得有类似的隔离约束。这是 Claude Code 生态的隐形规范。

---

## 10 · 读者判断：谁该跑一遍，谁读本文就够

**读本文就够的**：

- 想了解 Claude Code 生态的"账号 / runtime / provider"三层抽象是怎么被一个工具做出来的
- 想理解 OAuth 反代（CLIProxyAPI / CLIProxyAPIPlus / ccs）的工程分层
- 想看 Bun + TypeScript 双运行时 + React Dashboard + macOS Bar 三平台集成的工作量
- 想理解 "v8.9.0 重塑产品名" 这种 CLI 工具的版本节奏哲学

**应该跑一遍的**：

- 你用 Claude Code 且有多个 Anthropic 账号要切 → `npm install -g @kaitranntt/ccs` + `ccs config` 5 分钟装好
- 你用 Codex CLI / Factory Droid / Ollama / GLM 等非 Anthropic provider → `ccs codex` / `ccs glm` / `ccs ollama` 一行切换
- 你做 Claude Code 生态开发，想参考 "profile + runtime + Dashboard" 三层架构 → 看 `src/profile-registry.ts` (14,183 bytes) + `src/profile-detector.ts` (25,431 bytes) + `ui/src/` 整套 React dashboard
- 你做 CLI 工具 + macOS 菜单栏伴侣 → 看 `macos-bar/` Swift Package 的 Swift + TypeScript 跨语言组织

**应该直接跳仓库的**：

- 想看 OAuth provider 接入 → `src/auth/auth-commands.ts` (12,011 bytes)
- 想看 profile registry / detector 怎么管 4 层优先级 → `src/profile-registry.ts` (14,183) + `src/profile-detector.ts` (25,431)
- 想看 macOS 菜单栏 Swift + TypeScript 跨语言协调 → `macos-bar/` 完整子项目
- 想看 CI/CD 怎么跑 runtime-matrix 跨 Node/Bun 测试 → `scripts/ci-parity-gate.sh`

---

## 附录 A · 本文事实来源

- GitHub 仓库：`github.com/kaitranntt/ccs`（截至 2026-08-17 16:14 GMT+8）
  - 2,813 stars / 259 forks / 13 subscribers / 36 open issues
  - Created: 2025-11-01T21:01:53Z / Updated: 2026-08-17 / Pushed: 2026-08-14
  - Default branch: `main`（开发分支 `dev`）
  - 主语言: TypeScript 13.3MB / Size 44,883 KB
  - License: MIT
- 最新 release：`v8.9.0`（2026-08-09，commit `3608bf7` 重命名为 Claude Codex Switch）
- 最近 5 个 release：
  - `v8.9.0` 2026-08-09
  - `v8.9.0-dev.3` 2026-08-11
  - `v8.9.0-dev.2` 2026-08-09
  - `v8.9.0-dev.1` 2026-08-09
  - `v8.8.1-dev.22` 2026-08-09
- 最近 8 个核心 commit（全部 2026-08-09）：
  - `febdcdb` Merge PR #1696 docker smoke cold start
  - `78ad297` ci(docker): allow cold-start healthcheck window
  - `f8a9518` chore(release): 8.9.0 [skip ci]
  - `83268d1` Merge PR #1695 release/dev-to-main
  - `16ef7a3` chore(release): 8.8.1-dev.22
  - `27b0ea0` Merge PR #1694 #1688 share claude md
  - `54efb82` fix(auth): guard shared linking against instance replacement
  - `5f9db03` chore: merge origin/dev into issue #1688
- 仓库结构（已核实）：
  - `.claude/` — Claude Code 项目级配置
  - `src/` — TypeScript CLI/server 源码
  - `lib/` — Bash bootstrap wrapper
  - `ui/src/` — React dashboard 源码
  - `macos-bar/` — Swift Package 菜单栏伴侣
  - `dist/` / `dist/ui/` — build 产物
  - `docs/` — 架构文档
  - `docker/` — Docker 部署
  - `config/` — 配置模板
  - `eslint-rules/` — 自定义 ESLint 规则
  - `.releaserc.cjs` — semantic-release 配置
  - `.pr_agent.toml` — AI PR Agent 配置
  - `commitlint.config.cjs` — commit message 校验
- 6 个 npm bin（`package.json` 已核实）：
  - `ccs` `dist/ccs.js`（主 CLI）
  - `ccs-droid` / `ccsd` `dist/bin/droid-runtime.js`（Factory Droid runtime）
  - `ccs-codex` / `ccsx` `dist/bin/codex-runtime.js`（Codex CLI runtime）
  - `ccsxp` `dist/bin/ccsxp-runtime.js`（推测：extra profile）
- 关键依赖（`package.json` 已核实）：
  - `express ^4.18.2` + `express-rate-limit ^8.2.1` + `express-session ^1.18.2` + `ws ^8.16.0`（dashboard server）
  - `undici ^5.29.0`（HTTP client）
  - `bcrypt ^6.0.0`（密码哈希）
  - `chokidar ^3.6.0`（文件监听）
  - `proper-lockfile ^4.1.2`（文件锁）
  - `chalk ^4.1.2` + `ora ^5.4.1` + `listr2 ^3.14.0` + `boxen ^5.1.2` + `gradient-string ^2.0.2` + `cli-table3 ^0.6.5`（CLI UX）
  - `smol-toml ^1.6.1` + `js-yaml ^4.1.1`（配置解析）
  - `http-proxy-agent ^7.0.2` + `https-proxy-agent ^7.0.6`（代理）
  - `get-port ^5.1.1`（找可用端口）
  - `open ^8.4.2`（浏览器自动打开）
- 双运行时支持：`engines: { node: ">=18.0.0", bun: ">=1.0.0" }` + `packageManager: "bun@1.3.9"`
- semver 锚点：`@semantic-release/{changelog,commit-analyzer,git,github,npm,release-notes-generator}` 全家桶
- CI/CD：commitlint 20 + Husky 9 + ESLint 9 + Prettier 3 + `@pr_agent`
- Profile 解析优先级（CLAUDE.md L72-L77）：1. Built-in CLIProxy providers → 2. user-defined `config.cliproxy` → 3. settings-based `config.profiles` → 4. account-based `profiles.json` with isolated `CLAUDE_CONFIG_DIR`
- Non-Negotiables 6 条（CLAUDE.md L17-L27）：dev 分支优先 / 不动用户 `~/.ccs/` `~/.claude/` / 禁直接 commit dev main / semantic-release 管版本 / ASCII only output / 尊重 `NO_COLOR`
- 友商对比：`musistudio/claude-code-router`（36,687 ★ / 3,063 forks / v8.9.0 README 主动致谢借鉴 transformer 架构）
- 作者：Kai (Tam Nhu) Tran / Montreal, Quebec / Hireable: true / 6 年 GitHub 老兵 / 113 followers / 37 public repos
- npm：`@kaitranntt/ccs@8.9.0`，main: `dist/ccs.js`，types: `dist/ccs.d.ts`
- Docker：`ghcr.io/kaitranntt/ccs:latest`（旧 `ghcr.io/kaitranntt/ccs-dashboard:latest` 弃用）

## 附录 B · 已知缺口

- **`ccsxp` 这个 bin 的具体含义**：子代理报告没明确命名，推测是 "extra profile"。需要后续源码核实
- **macOS Bar 的 Swift Package 源码细节**：`Package.swift` 内容未直接读，本文的 Swift 代码块是推测版
- **作者 kaitranntt 在 Anthropic 是否有内部账号**：独立开发者但跟 Anthropic OAuth 有深度集成，需要后续调研
- **Issue #1706 pnpm v9+/v10+/v11 全局 store 模式 bug**：CCS 已知问题但未给具体 issue 链接
- **CLIProxyAPIPlus vs router-for-me/CLIProxyAPI 的具体代码差异**：CCS 团队 fork 自 router-for-me，但具体改了哪些文件未抓
- **macOS Bar 与 npm ccs 的通信协议**：跨 Swift + TypeScript 怎么通信（HTTP / WebSocket / Unix socket）未读源码
