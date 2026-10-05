---
title: 'davila7/claude-code-templates 项目导读：README 两个多月一字未动，组件索引从 1,810 涨到 1,907 —— "组件库 + CLI + 仪表盘"三件套的真实规模'
date: 2026-07-17T02:57:12+08:00
lastmod: 2026-10-05T00:00:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "MCP", "AI Agent", "Skills"]
description: "Claude Code Templates 是 davila7 维护的 Claude Code 组件集合：九类组件（agents / commands / mcps / settings / hooks / skills / loops / mods / sandbox）加 14 个项目模板，官方索引 components.json 收录 1,907 条，配套 npm CLI + Astro 仪表盘 + 五个 Cloudflare Workers。本文拆解三件套架构、README 与索引的三层口径差、CLI 的三十多个 flag、以及 cli-rust 重写与 K-Dense 上游改名这些 README 没写的部分。"
slug: "davila7-claude-code-templates-collection-guide"
github_repo: "davila7/claude-code-templates"
source_key: "gh:davila7/claude-code-templates"
author: text-matrix
---

## 一句话判断

**Claude Code Templates（[davila7/claude-code-templates](https://github.com/davila7/claude-code-templates)，2026-10-05 读数 32,375 stars / 3,703 forks，MIT）是一个 Claude Code 组件仓库 + CLI + 仪表盘的"三件套"**，作者 Daniel Avila。它把 Claude Code 周边生态做成可发现、可一键安装的组件库：422 个 agent、288 条 slash command、105 个 MCP 集成、890 个 skill，外加 loops（自治工作流）、mods（函数钩子插件）、sandbox（沙箱模板）三类新组件，通过 `npx claude-code-templates@latest` 一行命令装进本地 Claude Code。

这个项目最值得注意的一点是**文档与实物的距离**：README 顶部写着"explore and install 100+ agents, commands, settings, hooks, and MCPs"，而官方自己的组件索引 `docs/components.json` 在本文发文时（2026-07-16）已收录 1,810 条组件（另有 14 个项目模板），如今是 1,907 条。README 两个多月一字未动，组件目录、CLI flag、核心依赖的上游都在变。把它当成"组件市场的橱窗"会低估它，把它当成"README 描述的那个小工具"则会误判它。

如果你在选型"Claude Code 怎么从空白起步 / 怎么给团队统一一套组件 / 怎么让非工程师也能看住 AI 在做什么"，这篇文章值得读完整。

---

## 系统地图

```
┌──────────────────────────────────────────────────────────────────────────┐
│                Claude Code Templates（三件套 + 两个配套件）                 │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  cli-tool/    Node.js CLI（npm 包 claude-code-templates）           │ │
│  │    ├─ bin/create-claude-config.js   30+ 个 flag 的唯一入口           │ │
│  │    ├─ src/                          安装 / 仪表盘 / 健康检查实现      │ │
│  │    ├─ components/                   九类组件源（索引的主数据源）      │ │
│  │    ├─ templates/                    14 个语言项目脚手架              │ │
│  │    │                                 (common/go/python/rust/...)    │ │
│  │    ├─ docs_to_claude/               外部文档转 SKILL.md              │ │
│  │    └─ tests/                        Jest 套件                        │ │
│  ├────────────────────────────────────────────────────────────────────┤ │
│  │  cli-rust/    核心安装逻辑的 Rust 重写（v0.1.0 preview，独立分发）    │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌────────────────────────────┐  ┌───────────────────────────────────┐ │
│  │  dashboard/  Astro 站点     │  │  cloudflare-workers/  五个 Worker │ │
│  │    aitmpl.com +             │  │    crons        定时调度器        │ │
│  │    app.aitmpl.com           │  │    docs-monitor 文档变更监控      │ │
│  │    Cloudflare Pages 部署    │  │    pulse        每周 Telegram 周报│ │
│  │                             │  │    newsletter   通讯              │ │
│  │                             │  │    daily-health-report 每日报告  │ │
│  └────────────────────────────┘  └───────────────────────────────────┘ │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  docs/components.json   官方组件索引（generate_components_json.py） │ │
│  │    仪表盘与 npm 包共同读取；2026-10-05 实测 1,907 条                 │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
                          ▼
            用户本地 Claude Code
                          ▼
   agents/commands/settings/hooks/skills 装到 ~/.claude/ 对应子目录
   MCP 深合并进当前项目根的 .mcp.json
   项目模板从 templates/ 生成整个目录
```

这张图最重要的一条路径：**`cli-tool/components/` 是组件源、`docs/components.json` 是索引、`dashboard/` 与 `cloudflare-workers/` 是发现与监控层、`cli-tool/src/` 把三者缝起来**。注意 `cli-tool/templates/` 不在这一条链上——它放的是按编程语言组织的项目脚手架（React、Django、FastAPI 等 14 个），和组件安装是两个独立功能。

---

## 组件到底有多少：三层口径

这个项目的"组件数"有三个官方口径，差距很大，直接引用哪个数字会得出完全不同的结论：

| 口径 | 位置 | 说法 | 实际情况 |
|---|---|---|---|
| README | "Browse All Templates" 一节 | "100+ agents, commands, settings, hooks, and MCPs" | 严重过时，且只覆盖六类 |
| CLAUDE.md | Component Types 一节 | "Agents (600+)" 等概数 | 方向都偏了：agents 实际 422 条 |
| components.json | `docs/components.json` | 机器生成的精确索引 | **1,907 条**（2026-10-05 实测） |

精确索引按类型拆开是这样：

| 类型 | 条数 | 是什么 |
|---|---|---|
| agents | 422 | 领域专家代理（security-auditor、react-perf-optimizer…） |
| skills | 890 | 渐进式披露的技能包（含 scientific 分类 136 个目录） |
| commands | 288 | 自定义斜杠命令 |
| mcps | 105 | 外部服务集成（GitHub、PostgreSQL、Stripe…） |
| settings | 72 | Claude Code 配置（超时、记忆、输出风格） |
| hooks | 62 | 自动化触发器 |
| mods | 39 | 函数钩子插件（含 2048、doom、chess 等游戏 mod） |
| loops | 18 | 自治工作流（ticket-to-pr-loop、overnight-pr-routine-loop…） |
| sandbox | 11 | 沙箱模板（物理上三种 provider：cloudflare / docker / e2b） |
| templates | 14 | 语言项目脚手架（angular/django/fastapi/react…） |

本文发文时点（2026-07-16 的 commit 1a9cc7da）这份索引是 1,810 条（同样不含项目模板）：当时已有 loops 和 sandbox，还没有 mods——mods 类是 2026-09-16 才出现的。80 天涨了 97 条，增速不算惊人，但分布很有倾向性：agents 从 421 到 422 几乎停滞，skills 从 860 涨到 890，mods 从零到 39。

**读这份表的建议**：以 `docs/components.json` 为准（[aitmpl.com](https://aitmpl.com) 仪表盘就是它的渲染层），README 的"100+"和 CLAUDE.md 的概数都不要引用。索引由 `scripts/generate_components_json.py` 从组件目录生成，仪表盘和 npm 包读的是同一份文件，所以它是这个项目里唯一"生成即事实"的数字。

---

## 边界与角色划分

Claude Code Templates 的工程边界可以按"角色 + 数据流"分四组：

| 角色 | 谁负责 | 谁不允许 | 关键文件 |
|---|---|---|---|
| 组件源 | `cli-tool/components/` | 直接改 dashboard | `components/<type>/` |
| 项目脚手架 | `cli-tool/templates/` | 混入组件 | `templates/<lang>/` |
| 索引生成 | `scripts/generate_components_json.py` | 跳过脚本手改 json | `docs/components.json` |
| 仪表盘 UI | `dashboard/`（Astro） | 调本地 CLI | `dashboard/src/` |
| 自动化 | `cloudflare-workers/` 五个 Worker | 暴露给公网的 worker | 各 worker 目录 |

不变项之外，**它明确不做**的事（均出自 `CLAUDE.md` 原文）：

- ❌ **不**写 API key / token / project ID 到任何代码文件。`CLAUDE.md` 把这条列为 CRITICAL：所有密钥走 `.env` 或 Cloudflare `wrangler secret put`，手滑 commit 了就 "Revoke the key IMMEDIATELY"。
- ❌ **不**用 Vercel 部署 dashboard。`CLAUDE.md` 写"Manual deploy uses `wrangler pages deploy`, not Vercel"。这条是 2026-07 刚成立的：同文件另一处写着 "The Vercel collector was removed (2026-07) since the dashboard no longer deploys to Vercel"——本文发文时点恰好是迁移刚完成，仓库里那个只为 `/components.json` 配 CORS 头的 `vercel.json` 是旧时代的残留，如今已从仓库根删除。
- ❌ **不**单独维护 enterprise fork。组件是 MIT，第三方组件按原 license 引入并在 Attribution 一节标注来源。
- ❌ **不**和官方 Claude Code CLI 捆绑。它是补充工具，安装产物落到 `~/.claude/` 与项目目录，不替代 Claude Code 本体。

---

## 关键机制

### 1. CLI：README 只讲六个维度，flag 有三十多个

README 把 CLI 讲成六类组件的安装器，这部分属实，且命令至今逐字可用：

```bash
# 一行装全套
npx claude-code-templates@latest \
  --agent development-team/frontend-developer \
  --command testing/generate-tests \
  --mcp development/github-integration \
  --yes

# 交互式浏览
npx claude-code-templates@latest

# 单独装一种（README 原版示例）
npx claude-code-templates@latest --agent development-tools/code-reviewer --yes
npx claude-code-templates@latest --command performance/optimize-bundle --yes
npx claude-code-templates@latest --setting performance/mcp-timeouts --yes
npx claude-code-templates@latest --hook git/pre-commit-validation --yes
npx claude-code-templates@latest --mcp database/postgresql-integration --yes
```

但安装 flag 现在是**八类**：上面六个之外还有 `--skill` 和 `--loop`、`--mod`。后两个是 README 完全没提的新维度：

- `--loop` 装一个自治工作流，**并把该 loop 引用的其他组件连带装上**（flag 自述 "install specific loop component and its referenced components"）。每个 loop 是"目标 + 执行间隔 + 停止条件"的组合，比如 `ticket-to-pr-loop`、`overnight-pr-routine-loop`。
- `--mod`（别名 `--function-hook`）装一个 Claude Mod：把整个插件目录递归写进 `.claude/skills/{name}/`，由 Claude Code 作为本地插件加载。这依赖 Claude Code 的 function-hooks 机制——**2.1.287 起默认开启**，2.1.259–2.1.286 需要设 `CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1`。mods 索引里除了 `admin-capability-lockdown` 这类管理工具，还有 2048、doom、flappy 一批用引擎事件写的小游戏。

入口文件 `bin/create-claude-config.js` 里实测有 30 多个 flag，README 只宣传了其中一小部分。值得知道的还有：

| flag | 作用 |
|---|---|
| `--dry-run` | 只显示将要复制什么，不实际写盘——批量安装前建议先跑一遍 |
| `--sandbox <provider>` | 在隔离沙箱里执行 Claude Code，支持 e2b（配套 `--e2b-api-key`） |
| `--prompt <prompt>` | 安装完成后直接把 prompt 丢给 Claude Code 执行 |
| `--workflow` | 配合安装 flag，按 `#hash` 或 base64 编码的 YAML 复原一套安装组合 |
| `--studio` | Claude Code Studio 界面（本地与云执行） |
| `--teams` | 多 agent 协作会话的回看面板 |
| `--agents` / `--skills-manager` / `--2025` | agents 面板 / 技能管理面板 / 2025 年度使用回顾 |
| `--command-stats` / `--hook-stats` / `--mcp-stats` | 分析已有的命令、钩子、MCP 配置并给优化建议 |
| `--create-agent` / `--list-agents` / `--remove-agent` / `--update-agent` | 全局 agent（跨项目可用）的增删改查 |
| `--clone-session <url>` | 从 URL 下载并导入一份共享的 Claude Code 会话 |

### 2. README 宣传的四个工具

README 的 "Additional Tools" 一节给了四个，flag 均已核实存在：

```bash
npx claude-code-templates@latest --analytics       # 实时会话状态与性能指标
npx claude-code-templates@latest --chats           # 移动端优先的对话查看界面
npx claude-code-templates@latest --chats --tunnel  # 经 Cloudflare Tunnel 安全远程访问
npx claude-code-templates@latest --health-check    # 安装健康度诊断
npx claude-code-templates@latest --plugins         # 插件市场/已装/权限面板
```

`--analytics` 与 `--chats` 是给非工程师用的——他们不需要懂 agent、MCP 这些概念，但能看见 AI 在做什么。`--tunnel` 的官方措辞是 "Secure remote access via Cloudflare Tunnel"，本质是把本地界面通过隧道暴露出去方便手机查看；在公司网络里用之前，值得先想想这条隧道的出口策略。

### 3. 索引：一份 JSON 喂两端

`docs/components.json` 由 `scripts/generate_components_json.py` 生成（`CLAUDE.md` 原话："Update docs/components.json"），消费方有两个：

- **仪表盘**：aitmpl.com 的浏览、筛选、一键安装按钮，全是这份 JSON 的渲染；
- **npm 包**：CLI 安装组件时优先读包内自带的 `docs/components.json`（`cli-tool/src/index.js` 里写明 "First try to use local components.json file which has all agents cached"），按索引里的 `path` 字段回 GitHub raw 拉组件文件。

部署侧，dashboard 的生产部署由 GitHub Actions 在 push 到 `main`（`dashboard/**` 路径）时自动完成；其他目录的改动需要手动部署。发布走 `npm version` + `npm publish`，当前 latest 是 1.29.6（2026-09-17），npm 上共 158 个版本。

### 4. cli-rust：安装核心的 Rust 重写

`cli-rust/` 在本文发文时点就已存在，README 至今没提它。它的自述很克制：**只重写六类组件的安装逻辑**（agents、commands、mcps、settings、hooks、skills），并保证与 Node.js CLI "byte-for-byte parity"（逐字节一致）；仪表盘、沙箱、健康检查、交互式安装等其余功能继续委派给 Node CLI。

分发刻意与 npm 包隔离：以 `cli-rust-v*` tag 从 GitHub Releases 发独立二进制（v0.1.0 preview），提供 shell 脚本、`cargo binstall --git`、源码编译三条通道，现有 `npx` 体验完全不受影响。对读者而言，短期不用改变使用方式；它真正的意义是给"装组件"这个最高频路径准备一个无 Node 依赖的快路径。

### 5. 安全规则与遥测

`CLAUDE.md` 用一整节强调密钥安全，这在开源项目里不多见：

```javascript
// ❌ WRONG
const API_KEY = "AIzaSy...";

// ✅ CORRECT
const API_KEY = process.env.GOOGLE_API_KEY;
```

适用对象包括 Cloudflare account/project ID、Supabase URL、Discord ID、数据库连接串。对组件消费者的含义是：所有第三方 MCP 模板里只放 placeholder，key 由用户自己填。

另一件 README 没写、但装组件的人应该知道的事：CLI 带**公开遥测**。`cli-tool/src/tracking-service.js` 的 `shouldEnableTracking()` 表明安装事件默认上报，三个开关任一即可关闭——设 `CCT_NO_TRACKING=true`、`CCT_NO_ANALYTICS=true`，或处于 `CI=true` 环境（CI 里自动关闭）。在意安装行为外泄的团队，把这个环境变量写进镜像构建脚本一行就能关掉。

### 6. 第三方归因与 K-Dense 上游改名

README 的 Attribution 一节列出组件来源：K-Dense-AI 的科学技能包（MIT，"139 scientific skills"）、anthropics/skills 官方技能 21 个、obra/superpowers 14 个工作流技能、wshobson/agents 48 个 agent 等，各自保留原 license。仓库内 `components/skills/scientific/` 分类下实测有 136 个技能目录。

一个值得注意的漂移：**K-Dense-AI 上游已把 `claude-scientific-skills` 改名为 `scientific-agent-skills`**（GitHub 301 重定向可证），新版自述 "177 ready-to-use validated skills"，star 数已达 47,589。而 claude-code-templates 的 README 因为两个多月未更新，仍写着旧名和旧数字 139。组件本身还能装、还能用，但去做第三方 license 审计时，请按新仓库名去找源头。

### 7. Bright Data 赞助

README 顶部一整段 Bright Data 赞助（明面位置，不是隐藏角标），配套一键安装：

```bash
npx claude-code-templates@latest --skill web-data/search,web-data/scrape,web-data/data-feeds,web-data/bright-data-mcp,web-data/bright-data-best-practices,development/brightdata-local-search --mcp web-data/brightdata --yes
```

赞助形态是能力集成而非 logo 露出：web search、scraping、结构化数据源三类 skill 加一个 MCP server，把 Claude Code 接到实时网络数据上。这些组件不是项目自产，是第三方 MCP 提供方——README 在最显眼的位置放这段，反而帮你把"哪些组件有商业背景"标清楚了。

---

## 任务流案例：给一个新项目配 Claude Code 全套

**Step 1：先看后装**

```bash
cd my-new-project
npx claude-code-templates@latest \
  --agent development-team/frontend-developer \
  --command testing/generate-tests \
  --mcp development/github-integration \
  --dry-run
```

`--dry-run` 会列出将要写入的每个文件，确认没有意外覆盖后去掉它重新执行。安装完成后：agent 落在 `~/.claude/agents/`，slash command 落在 `~/.claude/commands/`，**GitHub MCP 深合并进当前项目根目录的 `.mcp.json`**——注意 MCP 是项目级配置，不是用户级；重复安装同一个项目时 CLI 会读取已有的 `.mcp.json` 做合并，不会覆盖你手写的 server 条目。

**Step 2：开 Claude Code 验证**

```bash
claude
```

`/agents` 里能看到新装的 frontend-developer，`/generate-tests` 可以直接调用，`.mcp.json` 里的 GitHub MCP server 让 Claude Code 具备调 GitHub API 的能力。

**Step 3：接实时网络数据（可选）**

```bash
npx claude-code-templates@latest \
  --skill web-data/search,web-data/scrape \
  --mcp web-data/brightdata \
  --yes
```

**Step 4：跑一次健康检查**

```bash
npx claude-code-templates@latest --health-check
```

它会检查各组件安装状态，包括当前目录 `.mcp.json` 的 JSON 语法与 server 配置是否有效——排查"装了但没生效"时先跑它。

**Step 5：非工程师盯盘（可选）**

```bash
npx claude-code-templates@latest --analytics
npx claude-code-templates@latest --chats --tunnel
```

第二条会经 Cloudflare Tunnel 把对话界面暴露到公网供手机查看；离开家庭网络环境前记得关掉。

---

## 与同类项目的横向对照

| 维度 | Claude Code Templates | awesome-claude-code（社区清单） | Anthropic 官方示例 |
|---|---|---|---|
| 形态 | 组件库 + CLI + 仪表盘 + Workers | Markdown 链接清单 | 文档示例 |
| 安装 | `npx` 一行装组件 | 手动复制粘贴 | 手动复制粘贴 |
| 索引 | `docs/components.json`（1,907 条）+ aitmpl.com | 无 | 无 |
| 组件规模口径 | 索引精确计数 | 未宣称总数（cct 从中引入过 21 条命令） | 不适用 |
| 第三方商业 MCP | ✅ Bright Data 明示赞助 | 仅链接 | ❌ |
| 监控/面板 | `--analytics`、`--chats`、`--plugins` 等 | ❌ | ❌ |
| License | MIT | CC0 1.0（cct Attribution 标注） | 各示例自定 |

这张表想说明的分工是：awesome 清单解决"有什么"，官方示例解决"怎么写"，而 Claude Code Templates 试图把"发现 → 试用 → 安装 → 监控"整条链收进一个 `npx` 命令。代价也明确：组件质量靠 Attribution 与 review 流程兜底而非官方背书，README 与索引长期不同步，赞助商组件与社区组件混在同一个命名空间里。

---

## 适用边界

**推荐使用**：

- 刚开始用 Claude Code，不想从零写 agent / command / MCP——先用 `--dry-run` 看清单再装
- 团队需要统一一套 Claude Code 配置，新人 onboarding 想一条命令搞定
- 想让非工程师（PM / 设计师 / 运维）能看住 AI 在做什么——dashboard、`--analytics`、`--chats` 都是为这个场景准备的
- 想要"装了几十个组件但不知道哪个坏了"的诊断工具——`--health-check`
- 想要自治工作流（loops）或函数钩子插件（mods）这类新形态组件的现成例子

**不推荐 / 谨慎使用**：

- 已有深度定制配置的团队——切换收益要自己算，索引里 1,907 条组件多数你用不上
- 严格出站策略的公司网络——CLI 要从 GitHub raw 拉组件，`--tunnel` 会开公网出口
- 对第三方组件有 license 审计要求——K-Dense 等来源要按**改名后的新仓库**核对，README Attribution 已滞后
- 不愿暴露安装遥测的环境——默认上报，需显式设 `CCT_NO_TRACKING=true`
- 需要 MCP 装在用户级而非项目级的工作流——MCP 永远写进当前项目根的 `.mcp.json`，没有用户级安装路径

**决策建议**，按团队现状选：

1. **个人 / 小团队起步**：`npx claude-code-templates@latest` 交互式浏览，或按上面任务流的 `--dry-run` → 安装 → `--health-check` 三步走。
2. **中型团队统一配置**：fork 仓库，内部组件按 `components/<type>/<category>/<name>` 的现有约定提交（注意不是 `templates/`——那里只放项目脚手架），配 `--health-check` 做 onboarding 验证。
3. **非工程师团队**：直接用 aitmpl.com 挑组件 + `--analytics` / `--chats` 盯盘，绕开 CLI。
4. **AI 重度用户**：`--command-stats` / `--hook-stats` / `--mcp-stats` 三个分析器适合装了很多组件后的清理阶段；`--clone-session` 可以导入别人的会话做参考。
5. **完全 FOSS 立场**：fork 后删掉 `web-data/bright*` 相关组件即可，其余部分不依赖赞助商。
6. **合规敏感团队**：镜像构建脚本里加 `CCT_NO_TRACKING=true`，并把 Attribution 里的第三方仓库逐个按当前地址重验。

---

## 边界声明

本文以两个时点为锚：发文时点 2026-07-16（commit `1a9cc7da`，README 190 行、组件索引 1,810 条）与复核时点 2026-10-05（README 逐字未变、组件索引 1,907 条、32,375 stars / 3,703 forks / MIT / npm latest 1.29.6）。核查面包括：GitHub API 仓库元数据、era 与现行 README 逐字 diff、`CLAUDE.md` 安全与部署段、`docs/components.json` 索引逐类计数、`cli-tool/` 目录结构与 `src/index.js`、`src/file-operations.js`、`src/tracking-service.js` 源码、`cli-rust/README.md`、`cloudflare-workers/` 五个 worker 的 README，以及 aitmpl.com / app.aitmpl.com / docs.aitmpl.com 的可访问性验证。仓库处于活跃迭代期（最近一次 push 为 2026-10-04），组件计数与 flag 面会继续变化；具体以 `docs/components.json` 与 [aitmpl.com](https://aitmpl.com) 为准。

回到系统层：这个项目真正持续提供价值的不是那 1,907 条组件本身——组件会过时、会改名、会有 license 变动——而是**"索引生成脚本 + 安装 CLI + 仪表盘"这条流水线**。README 的滞后反而说明了这点：文档停更的这两个多月里，流水线照常运转，索引照常增长。依赖它的时候，盯索引和源码，别盯 README。
