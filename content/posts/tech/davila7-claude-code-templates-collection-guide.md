---
title: 'davila7/claude-code-templates 项目导读：一个 29k stars 的 Claude Code "组件仓库 + 仪表盘 + CLI" 三件套是怎么搭起来的'
date: 2026-07-17T02:57:12+08:00
lastmod: 2026-07-17T02:57:12+08:00
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "MCP", "AI Agent", "开源模板", "Node.js CLI", "Skills"]
description: "Claude Code Templates 是 davila7 维护的开源 Claude Code 组件集合（agents / commands / hooks / MCPs / settings / skills），29.5k stars，配套 npm CLI + Astro 仪表盘 + Cloudflare Workers 后端。本文拆解它的三件套架构、组件分类、6 条 CLI 子命令、以及 aitmpl.com 仪表盘与 components.json 索引。"
weight: 1
slug: "davila7-claude-code-templates-collection-guide"
author: text-matrix
---

## 一句话判断

**Claude Code Templates（[davila7/claude-code-templates](https://github.com/davila7/claude-code-templates)）是一个 29.5k stars 的 Claude Code 组件仓库 + CLI + 仪表盘"三件套"**，作者 Daniel Avila。它把 Claude Code 周边生态（agents、slash commands、hooks、MCP integrations、settings、skills）做成可发现、可一键安装的开源组件库，通过 `npx claude-code-templates@latest` 一行命令就能给本地 Claude Code 装上 development-team/frontend-developer 这种 specialist agent、`/generate-tests` 这种 slash command、GitHub / PostgreSQL / Stripe MCP server、以及 Bright Data 这种第三方数据 MCP。同时维护 [aitmpl.com](https://aitmpl.com) 仪表盘与 `docs/components.json` 索引，覆盖"浏览 → 试用 → 安装 → 监控"完整闭环。

如果你在选型"Claude Code 怎么从空白起步 / 怎么给团队统一一套组件 / 怎么让非工程师也能挑模板"，这篇文章值得读完整。

---

## 系统地图

```
┌────────────────────────────────────────────────────────────────────────┐
│                  Claude Code Templates (3-piece architecture)            │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  cli-tool/    Node.js CLI (npm package)                            │ │
│  │    ├─ src/              commands / analytics-ui / dashboard wiring │ │
│  │    ├─ bin/              可执行入口                                  │ │
│  │    ├─ templates/        组件模板源（按 type 分目录）                │ │
│  │    ├─ components/       Claude Code 组件定义                        │ │
│  │    ├─ docs_to_claude/   把外部文档转成 Claude 可读的 SKILL.md       │ │
│  │    ├─ tests/            Jest 套件                                  │ │
│  │    └─ SKILLS_DASHBOARD.md                                            │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  dashboard/    Astro site (Cloudflare Pages 部署)                  │ │
│  │    ├─ 列出 100+ 组件，按 type 筛选                                   │ │
│  │    ├─ 一键安装按钮 → 调 CLI                                          │ │
│  │    └─ 跳到 aitmpl.com / app.aitmpl.com                              │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  cloudflare-workers/   后端服务                                     │ │
│  │    ├─ analytics 接收                                                       │ │
│  │    ├─ cron 任务                                                          │ │
│  │    └─ 监控上报                                                          │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  docs/components.json    组件索引（python 脚本生成）               │ │
│  │    ├─ scripts/generate_components_json.py                              │ │
│  │    └─ 仪表盘 + npm 包共用                                              │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  组件类型（6 类）                                                    │ │
│  │    ├─ 🤖 Agents       security-auditor / react-perf-optimizer ...    │ │
│  │    ├─ ⚡ Commands     /generate-tests / /optimize-bundle ...          │ │
│  │    ├─ 🔌 MCPs         github / postgresql / stripe / aws / openai     │ │
│  │    ├─ ⚙️ Settings     timeouts / memory / output-style                │ │
│  │    ├─ 🪝 Hooks        pre-commit-validation / post-completion         │ │
│  │    └─ 🎨 Skills       pdf-processing / excel-automation / workflows   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
                          ▼
            用户本地 Claude Code (~/.claude/)
                          ▼
        Agents / Commands / MCPs / Skills 装到 .claude/
```

这张图最重要的一条路径：**`cli-tool/templates/` 是组件源、`docs/components.json` 是索引、`dashboard/` + `cloudflare-workers/` 是发现层、`cli-tool/src/` 把三者缝起来**。发布走 `npm version` + `npm publish`，部署走 `wrangler pages deploy`（仪表盘）+ GitHub Actions on push to main（自动）。

---

## 边界与角色划分

Claude Code Templates 的工程边界可以按"角色 + 数据流"分四组：

| 角色 | 谁负责 | 谁不允许 | 关键文件 |
|---|---|---|---|
| 组件源 | `cli-tool/templates/` 与 `cli-tool/components/` | 直接改 dashboard | `templates/<type>/` |
| 索引生成 | `scripts/generate_components_json.py` | 跳过 CI 直接改 json | `docs/components.json` |
| 仪表盘 UI | `dashboard/`（Astro） | 调本地 CLI | `dashboard/src/` |
| 后端服务 | `cloudflare-workers/` | 暴露给公网的 worker | 各 worker 目录 |

不变项之外，**Claude Code Templates 明确不做**的事：

- ❌ **不**写 API key / token / project ID 到任何代码文件。`CLAUDE.md` 把这条列为 CRITICAL：所有密钥走 `.env` 或 Cloudflare `wrangler secret put`。Reviewer 看到 hardcoded secret 直接拒。
- ❌ **不**用 Vercel 部署。`CLAUDE.md` 写"Manual deploy uses `wrangler pages deploy`, not Vercel"——部署走 Cloudflare Pages。
- ❌ **不**单独维护 enterprise fork。Components 是 MIT，第三方 component（如 K-Dense-AI 的 139 个 scientific skills）按原 license 引入并标注来源。
- ❌ **不**和官方 Claude Code CLI 捆绑。Claude Code Templates 是补充工具，安装后落到 `~/.claude/` 而不是替代 Claude Code。

这四条"不做"恰好决定了 Claude Code Templates 的设计取舍——下面拆开看。

---

## 关键机制：三件套架构是怎么拼起来的

### 1. CLI 的 6 个安装维度

README 把 CLI 设计成 6 维度的"组件安装器"：

```bash
# 一行装全套
npx claude-code-templates@latest \
  --agent development-team/frontend-developer \
  --command testing/generate-tests \
  --mcp development/github-integration \
  --yes

# 交互式浏览
npx claude-code-templates@latest

# 单独装一种
npx claude-code-templates@latest --agent development-tools/code-reviewer --yes
npx claude-code-templates@latest --command performance/optimize-bundle --yes
npx claude-code-templates@latest --setting performance/mcp-timeouts --yes
npx claude-code-templates@latest --hook git/pre-commit-validation --yes
npx claude-code-templates@latest --mcp database/postgresql-integration --yes
```

每个组件类型对应 `cli-tool/templates/<type>/<category>/<name>.md`（或类似命名），CLI 通过 `docs/components.json` 索引找到目标文件，复制到用户 `~/.claude/<对应子目录>/`。

### 2. 三件套工具：Bundled tool 不止装组件

除了"装组件"，CLI 还提供 5 个 bundled tool：

```bash
npx claude-code-templates@latest --analytics       # Claude Code Analytics（实时 session 状态 + 性能）
npx claude-code-templates@latest --chats           # Conversation Monitor（移动端 UI）
npx claude-code-templates@latest --chats --tunnel  # 通过 Cloudflare Tunnel 远程访问
npx claude-code-templates@latest --health-check    # 安装健康度诊断
npx claude-code-templates@latest --plugins         # Plugin Dashboard（市场 / 已装 / 权限）
```

`--analytics` 和 `--chats` 是给非工程师用的——他们不需要懂 agent / MCP 概念，但能"看 AI 在做什么"。这是 README 反复强调"comprehensive collection"+"Interactive web interface"的工程化落地。

### 3. 仪表盘 + 索引：aitmpl.com / app.aitmpl.com

仪表盘 + 后端是两个 Cloudflare Pages 站点：

```bash
# Dashboard 构建 + 部署
cd dashboard && npm run build
npm run deploy  # wrangler pages deploy www + app.aitmpl.com
```

索引由 `scripts/generate_components_json.py` 维护（README 写得很直接：`# Component catalog` → `python scripts/generate_components_json.py  # Update docs/components.json`）。`components.json` 同时被仪表盘和 npm 包读取，保证两边一致。

部署自动化：`CLAUDE.md` 写"Deploys to production happen automatically via GitHub Actions on push to `main` (changes in `dashboard/**`)"。其他目录（`cli-tool/`、`cloudflare-workers/`）的改动需要手动部署。

### 4. 安全规则：NEVER hardcode secrets

`CLAUDE.md` 用一整个章节强调密钥安全，这是少数公开把"anti-pattern"写进 README 的项目：

```javascript
// ❌ WRONG
const API_KEY = "AIzaSy...";

// ✅ CORRECT
const API_KEY = process.env.GOOGLE_API_KEY;
```

适用对象包括 Cloudflare account/project ID、Supabase URL、Discord ID、database connection string。如果不小心 commit 了 secret，"Revoke the key IMMEDIATELY" + 走仓库清理流程。这条规则的工程含义是：所有 component 模板在引入第三方 MCP 时，必须让用户自己填 key，模板里只放 placeholder。

### 5. 第三方组件归因

README 的 Attribution 一节列出引入来源：

- **K-Dense-AI/claude-scientific-skills**（MIT，139 个 scientific skills，涵盖 biology / chemistry / medicine / computational research）

第三方组件按原 license 引入并标注，目的是"让 Claude Code 在科研 / 学术场景下也有现成 agent 可用"。这条规则的工程含义是：Claude Code Templates 的组件不是自产，而是社区聚合——这与 npm registry 的角色一致。

### 6. Bright Data 赞助 + Web Skills

README 顶部一整段 Bright Data 赞助（独立段落，不是隐藏），配套一键安装命令：

```bash
npx claude-code-templates@latest --skill web-data/search,web-data/scrape,web-data/data-feeds,web-data/bright-data-mcp,web-data/bright-data-best-practices,development/brightdata-local-search --mcp web-data/brightdata --yes
```

`web-data/search` / `web-data/scrape` / `web-data/data-feeds` 是 Bright Data 的 Skills，`web-data/brightdata` 是 MCP server。赞助模式不是简单的 logo 露出，而是 "Claude Code → Bright Data live web" 端到端能力的官方集成。README 在醒目位置标注这条的目的是：让用户清楚这些组件不是 Claude Code Templates 自产，而是第三方 MCP 提供方。

---

## 任务流案例：给一个新项目配 Claude Code 全套

**Step 1：装一个完整 dev stack**

```bash
cd my-new-project
npx claude-code-templates@latest \
  --agent development-team/frontend-developer \
  --command testing/generate-tests \
  --mcp development/github-integration \
  --yes
```

CLI 把 frontend-developer agent 写到 `~/.claude/agents/`、`/generate-tests` slash command 写到 `~/.claude/commands/`、GitHub MCP 写到 `~/.claude/.mcp.json`。

**Step 2：开 Claude Code**

```bash
claude
```

在 Claude Code 里 `/agents` 可以看到新装的 frontend-developer agent，`/generate-tests` 可以直接调用，GitHub MCP server 让 Claude Code 能直接调 GitHub API。

**Step 3：装 Bright Data 接入 live web**

```bash
npx claude-code-templates@latest \
  --skill web-data/search,web-data/scrape \
  --mcp web-data/brightdata \
  --yes
```

Claude Code 现在能用 live web search + scrape + structured data feeds。

**Step 4：加 health check**

```bash
npx claude-code-templates@latest --health-check
```

CLI 输出 diagnostics（哪个 agent 装好了、哪个 MCP 缺 env var、哪个 hook 没生效）。

**Step 5：用 analytics 看实时状态**

```bash
npx claude-code-templates@latest --analytics
npx claude-code-templates@latest --chats --tunnel
```

第二个命令通过 Cloudflare Tunnel 把 Claude Code 对话暴露到公网，手机可以看。

---

## 与同类项目的横向对照

| 维度 | Claude Code Templates | awesome-claude-code（社区列表） | Anthropic 官方 examples |
|---|---|---|---|
| 形态 | 组件仓库 + CLI + 仪表盘 | Markdown 列表 | 文档示例 |
| 安装 | `npx` 一行装组件 | 手动复制粘贴 | 手动复制粘贴 |
| 索引 | `docs/components.json` + dashboard | 无 | 无 |
| 组件数 | 100+（agents/commands/mcps/hooks/settings/skills） | 50-200（awesome 列表） | 10-20 |
| 第三方 MCP | ✅ Bright Data 等 | ❌ 仅链接 | ❌ |
| 跨平台 CLI | ✅ npm package | ❌ | ❌ |
| Cloud 仪表盘 | ✅ aitmpl.com + app.aitmpl.com | ❌ | ❌ |
| 健康度检测 | ✅ `--health-check` | ❌ | ❌ |
| Analytics | ✅ `--analytics` | ❌ | ❌ |
| 远程对话监控 | ✅ `--chats --tunnel` | ❌ | ❌ |
| License | MIT | n/a（文档） | n/a |
| Stars | 29.5k | n/a | n/a |

这张表想表达一件事：**Claude Code Templates 是少数同时把"组件源 + 索引生成 + 安装 CLI + 浏览仪表盘 + 健康度诊断 + 实时分析"六件事塞进同一个 npm 包的开源项目**。它牺牲了"每个组件都自己写"的纯净度，换来"100+ 社区组件 + 一行命令装好"的实战体验。

---

## 适用边界

**推荐使用**：

- 刚开始用 Claude Code，不想从零写 agent / command / MCP
- 团队内需要统一一套 Claude Code 配置（新人 onboarding 一行命令搞定）
- 想给非工程师配 Claude Code（dashboard + health-check + analytics 是给 PM / 设计师 / 运维用的）
- 想集成 Bright Data 这类第三方 live web MCP（一条命令装完）
- 想要 Mobile UI 看 Claude Code 对话（`--chats --tunnel`）
- 想要"我装了 50 个 component 但不知道哪个坏了"的诊断工具

**不推荐使用**：

- 已经有定制化 Claude Code 配置（自己写的 agent 模板比 Claude Code Templates 里的更贴团队）→ 切换收益评估
- 不想装 npm 全局依赖 / 受限于 `npx` 启动速度 → 直接 fork `cli-tool/templates/` 手动挑组件
- 公司内部有 proxy / 严格出站规则 → CLI 要拉 Bright Data MCP 等第三方包，可能被拦
- 团队对第三方组件有严格 license 审计 → 必须逐个检查 K-Dense-AI 等组件的 license
- 不喜欢"组件市场"模式、希望每个 MCP 都有官方维护方 → 期待管理成本（社区组件可能 stale）

---

## 决策建议

按团队现状选：

1. **个人 / 小团队、刚开始用 Claude Code** → 直接 `npx claude-code-templates@latest --agent ... --mcp ... --yes`，几行命令装好
2. **中型团队、需要统一 Claude Code 配置** → fork 仓库，把内部组件也按相同 `templates/<type>/<category>/<name>.md` 命名约定提交，配 `health-check` 做 onboarding 验证
3. **非工程师团队（PM / 设计师 / 运维）** → 走 `dashboard.aitmpl.com` + `--analytics` + `--chats --tunnel`，不需要懂 CLI
4. **AI 重度用户、想监控 Claude Code 行为** → `--analytics` 是少数能看"agent 调 MCP 频次 / tool call 时延"的工具
5. **完全 FOSS 信仰、担心 Bright Data 等闭源依赖** → fork + 删除 `web-data/bright*` 相关 component
6. **要审计每个 component 的来源** → 看 `cli-tool/components/` 的 metadata（README 写明第三方归因）

---

## 阅读路径

按需读：

- **只想上手**：README 顶部 `Quick Installation` + `npx claude-code-templates@latest --help`
- **想理解 CLI 实现**：`cli-tool/src/` + `cli-tool/templates/` 目录结构 + `cli-tool/SKILLS_DASHBOARD.md`
- **想看仪表盘**：`dashboard/` + `aitmpl.com` 部署流程
- **想看后端 worker**：`cloudflare-workers/` 各 worker 目录
- **想看安全规则**：`CLAUDE.md` 的 `Security Guidelines` 一节
- **想贡献组件**：`CONTRIBUTING.md` + `CODE_OF_CONDUCT.md` + `templates/` 现有命名约定
- **想看归因**：README 底部 `Attribution`（K-Dense-AI 等）

---

## 边界声明

本文基于 `davila7/claude-code-templates` 仓库 README（2026-07-16 抓取）、`CLAUDE.md`（开发指南）、GitHub API 仓库元数据（29.5k stars、3.2k forks、Python 主语言、MIT license）、`cli-tool/` + `dashboard/` + `cloudflare-workers/` 目录结构。仓库处于活跃迭代期，组件列表（agents / commands / MCPs / hooks / settings / skills）持续增长；Bright Data 等赞助商集成可能随协议变更调整。具体组件列表以 `docs/components.json` 与 [aitmpl.com](https://aitmpl.com) 为准。

Claude Code Templates 是少数同时把"组件源 + CLI + 仪表盘 + 后端 + 分析 + 远程监控"塞进同一仓库的开源项目；如果你的工作流强依赖某个 MCP 的特定版本，需要关注组件升级时是否同步更新。
