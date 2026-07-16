---
title: 'PostHog/posthog 架构拆解：一个 monorepo 如何承载 14 个产品 + 一个面向 agent 的产品操作系统'
date: 2026-07-17T02:57:12+08:00
lastmod: 2026-07-17T02:57:12+08:00
draft: false
categories: ["技术笔记"]
tags: ["PostHog", "产品分析", "Django", "React", "Monorepo", "AI Agent"]
description: "PostHog 是开源产品分析平台，35k+ stars，把产品分析 / Session Replay / Feature Flags / 实验 / 错误追踪 / 日志 / 数据仓库 / AI 可观测性 14 个产品收进一个 Django + React monorepo。本文拆解它的 products/ 垂直切片架构、MCP 与 agent skills 子生态，以及 self-hosting 与 self-driving mode 两条主线。"
weight: 1
slug: "posthog-posthog-open-source-product-platform-architecture"
author: text-matrix
---

## 一句话判断

**PostHog（[PostHog/posthog](https://github.com/PostHog/posthog)）不是一个"分析工具 + 几个周边产品"的拼盘，而是一个 35k+ stars 的产品操作系统（Product OS）**。它用一个 Django + React 的 monorepo 把 14 个产品（产品分析、Session Replay、Feature Flags、Experiments、错误追踪、日志、Survey、Data Warehouse、CDP、AI 可观测性、Workflows、Web Analytics、Self-driving、PostHog Code）按"垂直切片（vertical slice）"装进 `products/<product>/`，每个产品自带 backend / frontend / MCP / skills。整套系统的最新定位是"open source platform for building self-driving products"，并把"产品信号 → 派 agent → 写报告 + PR → 人在 Slack/Desktop/MCP 审核"做成默认工作流。

如果你在选型"一个开源、可自托管、能覆盖产品 + 工程 + AI 可观测性"的平台，这篇文章值得读完整。

---

## 系统地图

```
┌─────────────────────────────────────────────────────────────────────┐
│                          PostHog monorepo                            │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  products/<p>/                ← 14 个垂直切片产品                  │  │
│  │   ├─ backend/   Django app    models/queries/api/tasks/tests    │  │
│  │   ├─ frontend/  React         scenes/components/logics          │  │
│  │   ├─ mcp/       MCP tools     tools.yaml + UI app               │  │
│  │   ├─ skills/    Agent skills  面向 Claude Code / Cursor         │  │
│  │   └─ manifest.tsx             路由 / scenes / URL               │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐         │
│  │ ee/          │  │ services/    │  │ packages/            │         │
│  │ enterprise   │  │ llm-gateway  │  │ quill                │         │
│  │ features     │  │ mcp/         │  │ 共享 JS/TS 包        │         │
│  │ (迁出中)     │  │ oauth-proxy  │  │ (pnpm workspace)     │         │
│  │              │  │ stripe-app   │  │                      │         │
│  └──────────────┘  └──────────────┘  └──────────────────────┘         │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐         │
│  │ posthog/     │  │ common/      │  │ tools/ hogli         │         │
│  │ legacy       │  │ hogql_parser │  │ PyPI-publishable     │         │
│  │ monolith     │  │ 共享代码     │  │ developer CLI        │         │
│  │ (api/models/ │  │ (holding pen)│  │                      │         │
│  │  queries)    │  │              │  │                      │         │
│  └──────────────┘  └──────────────┘  └──────────────────────┘         │
│                                                                         │
│                              ↓ 部署                                    │
│   ┌────────────────────────────────────────────────────────────┐       │
│   │  PostHog Cloud US/EU (托管)   |   hobby deploy (自托管)      │       │
│   │  + LLM Gateway + MCP server   |   < 100k events/月          │       │
│   │  + Stripe / HubSpot / DW 接入 |   4GB RAM docker           │       │
│   └────────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
                          ▼
                Slack / Web / Desktop / MCP / Claude Code
                          ▼
            Self-driving mode: 信号 → Agent → 报告 + PR
```

这张图最重要的一条路径：**`products/<p>/{backend,frontend,mcp,skills}` 是 PostHog 的"垂直产品单元"**——每个产品自带 Django app + React scenes + MCP tool 定义 + agent skill，谁拥有谁负责。这是它和"一个大 Django 顶层包把 14 个 feature 塞一起"传统形态的本质区别。

---

## 边界与角色划分

PostHog 的代码边界可以按"谁拥有 / 谁共享 / 谁不允许"分四类：

| 层级 | 路径 | 所有权 | 跨产品访问 |
|------|------|--------|----------|
| 产品垂直切片 | `products/<p>/` | 单一产品独占 | 不互相 import |
| 跨产品共享包 | `packages/quill/` 等 | 全 monorepo 共享 | 任意 import |
| 独立服务 | `services/llm-gateway/`, `services/mcp/` | 不属于单一产品 | HTTP/gRPC |
| 共享底座 | `common/hogql_parser/` 等 | 临时中转 | 任意引用，但目标是收缩 |

不变项之外，**PostHog 明确不做**的事：

- ❌ **不**在 `products/<a>/` 里直接 import `products/<b>/` 的内部代码。代码评审会拦住，tach 工具静态扫描 import 边界。
- ❌ **不**把 enterprise 功能塞进 `ee/` 就结束。`ee/` 里的功能正在按垂直切片迁到 `products/` 下对应产品里（`ee/` 是"being migrated to products/"），迁完即弃用。
- ❌ **不**把 `common/` 当永久目的地。README 写得很明确：`common/` 是"holding pen, NOT a destination (goal: shrink it)"——共享代码在出现第二个产品依赖它时，必须升级到 `packages/<name>/`。

这三条"不做"恰好决定了 PostHog 的设计取舍——下面拆开看。

---

## 关键机制：14 个产品是怎么装进一个仓库的

### 1. 垂直切片：每个产品自带 backend / frontend / MCP / skills

`docs/internal/monorepo-layout.md` 把"垂直切片"写成了强制规则：

```text
products/<product>/
  backend/    Django app（models、logic、api/、presentation/、tasks/、tests/）
  frontend/   React（scenes、components、logics）
  manifest.tsx  路由、scenes、URL
  services/   可选：本产品部署的服务
  packages/   可选：本产品自有的库/CLI
  mcp/        可选：MCP tool 定义（tools.yaml）+ UI app
  skills/     可选：agent skills（多数产品已有）
```

一个产品的例子是 Feature Flags：它有自己的 `feature_flags/models.py`、`feature_flags/api/`、`feature_flags/frontend/scenes/`，但**不** import Experiments 的内部模块来用——如果需要共享模型，要么抽到 `packages/`、要么走 service-to-service HTTP。这条规则由两层执行：

- **tach**（Rust 写的 import 边界检查工具）跑在 CI 上，跨产品的 import 会直接 fail。
- **CODEOWNERS** 用 `products/<product>/**` 路径做 owner 分配，而不是 `<product>-*` 文件名前缀。

README 的措辞非常直接："A prefix doing a folder's job is the signal to nest."——文件名前缀做到文件夹能做的事了，就该嵌套。

### 2. pnpm workspace 与 package 命名的解耦

JS/TS 端的拓扑比较有意思：**包的位置不是访问控制**。`pnpm-workspace.yaml` 的 glob 是显式声明的（`products/*`、`packages/quill` 等），pnpm 按 `name` 解析，不按路径。所以这套规则：

- 包被单一产品拥有 → 默认放 `products/<p>/packages/<name>/`
- 被两个以上产品真正使用 → 升级到顶层 `packages/<name>/`（例：`packages/quill/`）
- 升级时机：**"Promote nested → root only when a second consumer actually depends on it — on real usage, not intent"**——等到第二个真实使用者出现再升级，不要按意图预先升级。

好处是路径调整几乎零成本：`packages/<name>/` → `products/<p>/packages/<name>/` 是一次 path rename，import 不需要改（因为 pnpm 按 name 解析）。

Python 和 Rust 不一样——它们 location 和 import name 直接绑定（一个顶层 Python 包甚至能 shadow 标准库模块，所以没有顶层 `platform/`），所以顶层目录规则不适用。

### 3. MCP 与 agent skills：产品自带"agent surface"

这是 PostHog 在 2026 年新长出来的关键能力。README 明确写：

> Most products are a Django app plus React scenes — and most already carry more: an `mcp/` directory of MCP tool definitions, often a `skills/` directory of agent skills. A product can own anything attributable to it, runtime and tooling alike.

具体落到能力上：

- **MCP**：`products/<p>/mcp/tools.yaml` 定义本产品的 MCP tools + 一个 UI app（多数产品都有）。PostHog 自己也跑一个 `services/mcp/` 服务。
- **Skills**：`products/<p>/skills/` 是面向 Claude Code / Cursor 的 agent skills——多数产品已有。
- **steering surface**：你可以从 Slack、Web、Desktop（PostHog Code）、或 Claude Code / Cursor 通过 MCP 接入整套产品。这一条是 self-driving mode 的物理基础。

这一层把 PostHog 从"被动分析平台"推到了"主动 agent 平台"——下面 self-driving mode 那一节会展开。

### 4. self-driving mode：信号 → agent → 报告 + PR

README 的产品定位第一句是"PostHog is the open source platform for **building self-driving products**"。"self-driving" 在这里不是自动驾驶车的比喻，而是：

> Turn signals in your product data (errors, rage clicks, failed queries, and more) into researched reports and pull requests you review and merge.

整条链路：

1. PostHog 在产品数据里检测信号（错误、rage clicks、失败 query、性能回退等）
2. agent 拿到信号，调本产品的 MCP tool 拉上下文（哪个用户 / 哪个会话 / 哪个 query）
3. agent 写研究报告 + 修复 PR
4. 人在 Slack / Desktop / MCP 里 review + merge

这意味着 PostHog 的产品能力已经从"展示数据"延伸到"对数据采取行动"。配合 `services/llm-gateway/`（LLM 代理）和 `services/mcp/`（MCP server），整个 agent surface 都是产品化的，不是文档里的一句"未来规划"。

### 5. AI observability 与 LLM Gateway

`services/llm-gateway/` 是 PostHog 自己的 LLM 代理服务。配合 `AI observability`（捕获 LLM 应用的 traces、generations、latency、cost），你可以在 PostHog 里看到自己产品里每个 LLM 调用的 token 成本与延迟分布。LLM Gateway 同时是 PostHog 自己用 self-driving mode 时的内部依赖。

---

## 任务流案例：从"产品里有 rage click"到"提一个 PR"

把上面的零件拼起来跑一次完整 self-driving 流程：

**Step 1：装 PostHog（自托管 hobby 部署，< 100k events/月）**

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/posthog/posthog/HEAD/bin/deploy-hobby)"
```

或直接用 PostHog Cloud US/EU（推荐，前 1M events / 5k recordings / 1M flag requests / 100k exceptions / 1500 survey responses 免费）。

**Step 2：接 SDK（前端）**

```html
<script>
  !function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.async=!0,p.src=s.api_host+"/static/array.js",(r=t.getElementByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=a:u=e._i=[],n=0;n<t.length;n++)g(u,t[n]);e._i=n,u._i=void 0,o=s.createElement("script");o.type="text/javascript",o.async=!0,o.src=s.api_host+"/decoy-route.js",r.parentNode.insertBefore(o,r)},e.__SV=1.2)}(document,window.posthog||[]);
  posthog.init('<project_api_key>', {api_host: 'https://us.i.posthog.com'})
</script>
```

**Step 3：接 MCP 到 Claude Code / Cursor**

在 Claude Code 里加 PostHog MCP（README 链的是 `posthog.com/mcp`）。这样 Claude Code / Cursor 拥有 `posthog_query` / `posthog_list_actions` 等 tool。

**Step 4：信号产生**

某个用户连续点 "Submit" 按钮 5 次没反应 → PostHog 抓到 rage click 事件 + 关联 session replay。

**Step 5：agent 介入**

你在 Slack 里给 PostHog 发："刚才那个 rage click 是什么导致的？能修吗？" → PostHog 的 agent：

1. 调 `posthog_query` 查这个 session 的 event 时间线
2. 调 `posthog_list_actions` 列出当时命中的 feature flags
3. 通过 MCP 读 session replay 的 DOM 快照
4. 在 `posthog/self-driving-review` 仓库写研究报告 + 修复 PR（按钮 disabled state 没在异步回调里恢复）
5. 飞书 / Slack 推一条 PR 链接给你 review

**Step 6：人在 review 后 merge**

这跟传统"人拉数据、写报告、提 PR、修代码"的两小时流程对比，agent 在 30 秒内交付。

---

## 与同类项目的横向对照

| 维度 | PostHog | Plausible | Mixpanel | Amplitude |
|---|---|---|---|---|
| 自托管 | ✅ hobby deploy | ✅ Docker | ❌ 闭源 SaaS | ❌ 闭源 SaaS |
| 产品数 | 14（含 flags / replay / errors / logs / DW） | 1（web analytics） | 3（analytics / experiments / session replay） | 4（analytics / session replay / experiments / CDP） |
| Session Replay | ✅ | ❌ | ✅ | ✅ |
| Feature Flags + Experiments | ✅ 内置 | ❌ | ✅ | ✅ |
| Error Tracking | ✅ | ❌ | ❌ | ❌ |
| LLM Gateway + AI observability | ✅ | ❌ | ❌ | 部分 |
| MCP server | ✅ 每个产品自带 | ❌ | ❌ | ❌ |
| Agent skills | ✅ Claude Code / Cursor | ❌ | ❌ | ❌ |
| Self-driving mode | ✅ 信号 → agent → PR | ❌ | ❌ | ❌ |
| 免费额度 | 1M events / 5k recordings / 1M flags / 100k exceptions / 1500 surveys | 每月按流量分阶 | 20M MTU 免费 | 10M events 免费 |

这张表想表达一件事：**PostHog 是少数同时把"产品分析 + 行为回放 + 实验 + 错误追踪 + LLM 可观测 + agent surface"塞进同一个开源仓库的平台**。它牺牲了"每个产品都做到行业第一深度"的指标，换来"全链路信号 → agent 行动"这一条别的平台都不具备的能力。

---

## 适用边界

**推荐使用**：

- 想用一个开源、可自托管、覆盖产品 + 工程 + AI 可观测性的统一平台
- 需要从产品信号（错误 / 行为 / 实验）一路追到 PR，不愿意在 5 个 SaaS 之间切窗口
- 已经在用 Claude Code / Cursor，希望把 PostHog 当 MCP server 接进来
- 想用 self-driving mode 把"高频、低风险"的修复自动化（如 rage click、失败 query、性能回退）
- 团队 < 100 人、单实例 100k events/月以内——hobby deploy 完全够用

**不推荐使用**：

- 你只需要一个简单的页面 PV / UV dashboard → Plausible 更轻量
- 数据量级在 1B events/月以上、需要专门的数据团队 → Mixpanel / Amplitude 的 SaaS 数据基础设施更成熟
- 强依赖 enterprise SSO / 私有化部署 / SOC2 → PostHog Cloud 已有 SOC2，但自托管的 enterprise SLA 是付费 add-on
- 不希望任何 agent / LLM 触达你的产品数据 → self-driving mode 是 opt-in，但 AI observability 默认开启；需要逐产品关闭
- 想找 PostHog 同款但完全 FOSS（无 ee/ 闭源 feature）→ 看 [posthog-foss](https://github.com/PostHog/posthog-foss)，它是 MIT-only 剥离版

---

## 决策建议

按团队现状选：

1. **初创团队、单一产品、想快速验证 PMF** → PostHog Cloud 免费层 + Feature Flags + 产品分析，self-driving mode 暂时关闭
2. **增长期团队、已有多个产品、要统一分析** → PostHog Cloud 付费层 + Session Replay + Experiments + Error Tracking
3. **工程效率团队、想用 agent 加速产品迭代** → 开 self-driving mode + 接 Claude Code / Cursor MCP + 给高频、低风险信号开自动 PR
4. **数据合规要求高、必须自托管** → hobby deploy（< 100k events/月）+ `services/` 独立服务 + 关闭 cloud-only 功能
5. **完全 FOSS 信仰** → 用 `posthog-foss` 而非 `posthog`，接受 feature 缩水
6. **大厂、亿级 events、需要专门数据团队** → 评估自建 + PostHog 作部分模块，不强求全套

---

## 阅读路径

按需读：

- **只想上手**：README + `posthog.com/docs/getting-started/install` + Cloud US/EU signup
- **想理解 monorepo 划分**：`docs/internal/monorepo-layout.md` + `products/README.md` + `products/architecture.md`
- **想看产品实现**：`products/<p>/backend/`（Django app）+ `products/<p>/frontend/scenes/`
- **想接 MCP / skills**：`posthog.com/mcp` + 任意产品的 `products/<p>/mcp/` + `products/<p>/skills/`
- **想看自托管部署**：`posthog.com/docs/self-host` + `bin/deploy-hobby` + `posthog.com/docs/self-host/troubleshooting`
- **想了解企业级 feature 分布**：看 `ee/LICENSE` 确认哪些产品有 enterprise tier

---

## 边界声明

本文基于 `PostHog/posthog` 仓库 README（2026-07-16 抓取）、`docs/internal/monorepo-layout.md`、`docs/internal/monorepo-layout.md` 描述的 products/ 架构、GitHub API 仓库元数据（35.7k stars、2.9k forks、Python 主语言、MIT + ee/ 混合 license）。仓库处于活跃迭代期，products/ 边界与 MCP / skills 列表可能在未来版本变化；self-driving mode 仍处于早期阶段，agent 的修复准确率与误报率官方未公开基准。具体能力请以仓库当时版本 + `posthog.com/changelog` 为准。

PostHog 是少数同时把"产品分析 / Session Replay / Feature Flags / Error Tracking / LLM observability / agent surface"塞进同一仓库的开源平台，长期路线与"5 个 SaaS 拼盘"的传统形态差异会持续扩大；如果你的工作流强依赖某个 SaaS 的深度能力，需要评估 PostHog 在该维度的功能完整度。
