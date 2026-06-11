---
title: "Hivemind：把团队 agent 经验自动沉淀为可复用技能的中枢"
date: "2026-06-11T15:00:21+08:00"
slug: "hivemind-activeloop-shared-agent-brain-architecture-guide"
description: "Hivemind 是 Activeloop 推出的跨多编程 Agent 的云端共享记忆与技能传播系统。本文解析其流水线、SKILL.md 编译与 LoCoMo benchmark 边界。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "OpenClaw", "共享记忆", "SKILL.md"]
---

> **目标读者**：同时在用 Claude Code、Cursor、Codex CLI、OpenClaw 等多个编程 Agent，并希望把"团队踩过的坑"沉淀成可复用资产的工程师 / 团队负责人。
> **核心问题**：Hivemind 跟 `CLAUDE.md` / `MEMORY.md` / `agentmemory` 这类「单 agent 记忆」方案到底有什么本质差异？它承诺的"技能自动传播"是不是又一个营销话术？
> **资料范围**：本文基于仓库 `main` 分支 README（v0.7.89）、`src/` 目录结构、`package.json` 依赖、docs 目录与 GitHub 仓库元数据；公开 benchmark（LoCoMo）数据来自 README 引用，**不**复现其内部评测环境。

---

## 阅读目标

读完后应该能回答四个问题：

- Hivemind 的定位是什么，适合什么场景，不适合什么场景。
- "Capture → Codify → Propagate" 流水线是怎么落地的。
- 跨 Claude Code / OpenClaw / Codex / Cursor / Hermes / pi 这六种 agent，集成机制分别是什么。
- README 上 LoCoMo 的 -25% cost / 1.7× tokens / 31% turns 数字应该怎么读，哪些可以采信。

## 1. 它要解决的不是「agent 失忆」，而是「团队经验不积累」

`CLAUDE.md`、`MEMORY.md`、`.cursorrules` 这类静态记忆文件解决的是"别让 agent 每次都从零解释项目"，agentmemory / mem0 / Letta 这一类本地记忆服务解决的是"agent 跨会话能记住上次做了什么"。但**真正卡团队生产力的，是第三层问题**：

> 周一你的 agent 帮你搞定了一个棘手的 ORM 迁移；
> 周三你同事的 agent 在另一个项目里又踩了同一个坑，从头排查。

Hivemind 把这一层叫做"团队级能力累积（capability compounding）"。它的核心主张是：

- **Capture（捕获）**：每个 agent 的 prompt、tool call、response 全部以 trace 形式落到云端 Deeplake 数据库。
- **Codify（编码）**：后台 worker 周期性扫描 trace，把出现 ≥ N 次的模式提炼为 `SKILL.md` 文件。
- **Propagate（传播）**：下一次任意 agent 启动时，相关 `SKILL.md` 自动注入上下文，团队里的所有人、所有 agent 共享同一份"经验池"。

可以先和现有方案做一次横向对照：

| 方案 | 记忆范围 | 沉淀物形态 | 跨 agent | 数据归属 |
| --- | --- | --- | --- | --- |
| 静态记忆文件 | 单项目 | 手工维护的 markdown | ❌ | 本地仓库 |
| agentmemory / mem0 / Letta | 单 agent | 自动 observation + 索引 | ❌ | 本地或自托管 |
| OpenClaw memory-core | 单 agent / 单机器 | 摘要 + 反思 | ❌ | 本地 |
| **Hivemind** | **团队 / 组织** | **trace + SKILL.md + 规则 + 目标** | ✅（Claude Code / OpenClaw / Codex / Cursor / Hermes / pi） | **Deeplake 云端或 BYOC** |

差异不在"能不能存信息"，而在**信息能不能在团队内被相关 agent 复用到下一次任务**。

## 2. 一张图看懂系统全貌

```mermaid
flowchart TB
    subgraph Agents[多 Agent 客户端]
        A1[Claude Code]
        A2[OpenClaw]
        A3[Codex CLI]
        A4[Cursor]
        A5[Hermes Agent]
        A6[pi]
    end

    subgraph Hooks[生命周期钩子]
        H1[sessionStart]
        H2[beforeSubmitPrompt]
        H3[postToolUse]
        H4[afterAgentResponse]
        H5[stop / sessionEnd]
    end

    subgraph CaptureLayer[Capture 层]
        C1[结构化 trace<br/>prompt / tool call / response]
        C2[~/.deeplake/memory/<br/>虚拟文件系统]
    end

    subgraph Engine[Deeplake 引擎]
        E1[memory 表<br/>summaries + 768d embedding]
        E2[sessions 表<br/>逐事件 trace]
        E3[hivemind_rules 表]
        E4[goal / kpi 表]
    end

    subgraph CodifyLayer[Codify 后台 worker]
        K1[每 N turn 触发<br/>SKILLIFY_EVERY_N_TURNS]
        K2[Haiku 决策器]
        K3[SKILL.md 写入]
        K4[Wiki 摘要生成]
    end

    subgraph Propagate[Propagate 注入]
        P1[SessionStart 注入 Rules 块]
        P2[查询时 hybrid 检索]
        P3[codebase graph 命中]
    end

    A1 --> H1 & H2 & H3 & H4 & H5
    A2 --> H1 & H2 & H3 & H4 & H5
    A3 --> H1 & H2 & H3 & H4 & H5
    A4 --> H1 & H2 & H3 & H4 & H5
    A5 --> H1 & H2 & H3 & H4 & H5
    A6 --> H1 & H2 & H3 & H4 & H5

    H1 & H2 & H3 & H4 & H5 --> C1
    C1 --> C2
    C1 --> E2
    C2 --> E1
    K1 --> K2 --> K3
    K3 --> C2
    K1 --> K4 --> E1
    H1 --> P1
    H2 --> P2
    P2 --> E1 & E2
    P3 --> E2
```

> ⚠️ 上面这张图是**作者基于 README 描述重组后的系统地图**，不是仓库里的现成架构图。原图请见 `docs/ARCHITECTURE.md`。

## 3. 仓库结构：18 个核心子模块各管一摊

`package.json` 里把 `hivemind` 命令打包成 `bundle/cli.js`，源码组织如下（v0.7.89，`main` 分支）：

| 目录 | 职责 |
| --- | --- |
| `src/cli/` | `hivemind` 命令行入口（install / login / status / skillify / rules / goal / context） |
| `src/commands/` | 各子命令实现 |
| `src/config.ts` / `src/user-config.ts` | 配置加载、环境变量解析 |
| `src/deeplake-api.ts` | 封装 Deeplake HTTP/SDK 调用 |
| `src/deeplake-schema.ts` | `memory` / `sessions` / `hivemind_rules` / `goal` / `kpi` 表 DDL |
| `src/embeddings/` | 可选本地 nomic-embed-text-v1.5 daemon（默认关） |
| `src/graph/` | codebase 图：files / symbols / imports / 实际访问边 |
| `src/hooks/` | 各 agent 的钩子 bundle 模板 |
| `src/mcp/` | 共享 MCP server（`~/.hivemind/mcp/server.js`） |
| `src/notifications/` | 启动时的 DATA NOTICE |
| `src/path-match.ts` | `~/.deeplake/memory/` 路径匹配 |
| `src/rules/` | 跨 agent 规则注入逻辑 |
| `src/shell/` | 交互式 Deeplake shell（`npm run shell`） |
| `src/skillify/` | 模式挖掘 + `SKILL.md` 编码 + `pull/unpull` 同步 |
| `src/utils/` | `sqlStr` / `sqlLike` / `sqlIdent` 等 SQL 转义 |
| `src/dashboard/` | Web 仪表盘 |
| `src/index-marker-store.ts` | BEGIN/END marker 块（如 pi 的 AGENTS.md 注入） |

外层还按 agent 维度分了独立的安装包：

```
claude-code/   # Claude Code marketplace plugin
openclaw/      # OpenClaw 原生 extension
codex/         # Codex hooks
cursor/        # Cursor hooks（1.7+）
hermes/        # Hermes Agent shell hooks + skill + MCP
pi/            # pi TypeScript extension + AGENTS.md marker
mcp/           # 共享 MCP server
```

`build` 脚本 `tsc && node esbuild.config.mjs` 会把这六份 bundle 一起编译到对应子目录。

## 4. Capture：每个 agent 都用自己最自然的钩子点接入

Hivemind 没有强行用一套钩子覆盖所有 agent，而是按各 agent 自身的扩展机制分别接：

| Agent | 集成机制 | 自动捕获 | 自动召回 |
| --- | --- | --- | --- |
| **Claude Code** | Marketplace plugin | ✅ | ✅ |
| **OpenClaw** | 原生 extension | ✅ | ✅ |
| **Codex** | `hooks.json` | ✅ | ✅ |
| **Cursor** | `hooks.json`（1.7+） | ✅ | ✅ |
| **Hermes Agent** | `config.yaml` shell hooks + skill + MCP server | ✅ | ✅ |
| **pi** | `pi.on(...)` 扩展 API + skill + AGENTS.md marker | ✅ | ✅ |

统一安装命令是：

```bash
npm install -g @deeplake/hivemind && hivemind install
```

安装器会扫描机器上所有支持的 assistant，**默认在每个 agent 的以下事件**上挂钩子（Cursor 1.7+ 的完整列表）：

- `sessionStart` — 注入团队 Rules 块
- `beforeSubmitPrompt` — 触发自动召回
- `postToolUse` — 上报 tool call 结果
- `afterAgentResponse` — 上报最终 response
- `stop` — 触发 skillify 后台 worker
- `sessionEnd` — 触发 wiki 摘要生成

**Codex 用户特别要注意**：首次启动会弹"Hooks need review"提示，**必须选 `2. Trust all and continue`**，否则钩子不会真正跑。

每个 agent 写入的数据维度都是统一的：

| 字段 | 含义 |
| --- | --- |
| `user_prompts` | 用户每条消息原文 |
| `tool_calls` | 工具名 + 完整 input |
| `tool_responses` | 工具完整 output |
| `assistant_responses` | agent 最终 response |
| `subagent_activity` | subagent 的 tool call / response |
| `codified_skills` | 从 trace 提炼出的 SKILL.md |

如果某次会话你不想被抓，置环境变量即可：

```bash
HIVEMIND_CAPTURE=false claude
HIVEMIND_DEBUG=1 claude   # 想看钩子日志
HIVEMIND_CAPTURE_ONLY_CLI=true  # 只抓 CLI 会话，跳过 SDK 派生会话
```

## 5. Codify：后台 worker 怎么"挖矿"出 SKILL.md

`HIVEMIND_SKILLIFY_EVERY_N_TURNS`（默认 20）控制挖掘频率。每到一轮：

1. 拉取最近 N 轮内"作用域"内的所有 trace（`me` vs `team`，由 `hivemind skillify scope` 切换）。
2. 调用 **Haiku**（README 显式提到）判断这些 trace 里有没有"值得保留的模式"。
3. 如果有，把模式提炼成 `SKILL.md`，写到 `<project>/.claude/skills/<name>/`。
4. 同时把 `SKILL.md` 同步到云端 Deeplake，供团队其他 agent `pull`。

`pull / unpull` 是显式的：

```bash
hivemind skillify pull    # 把队友的 skill 拉到本地
hivemind skillify unpull  # 撤回
```

Wiki 摘要是另一条 worker 链路，由 `hivemind_summaries` 在 `sessionEnd` 时触发。它**复用 host agent 自己的 CLI**（`claude -p` / `codex exec` / `pi --print`）来生成摘要，因此**不需要额外的 API key**。生成结果存到 `memory` 表里，附带 768 维 embedding（如果开了 embeddings daemon）。

## 6. Propagate：注入和召回两套机制

### 6.1 规则注入（同步路径）

`SessionStart` 时，agent 会拿到一段固定的注入块（README 原文）：

```text
=== HIVEMIND RULES (N active) ===
- <rule_id>: <text>
(X more, run 'hivemind rules list' to see all)

=== HIVEMIND HOW-TO ===
- Rules above are team principles. Treat any action that would violate one as a critical error and surface it to the user before proceeding.
- Run 'hivemind rules list' for the full inventory beyond what's shown here.
```

Codex **故意被排除**在这条规则注入之外——README 解释是"为了保持 TUI 干净"。

### 6.2 检索召回（异步路径）

每个 prompt 提交前，Hivemind 会做一次 hybrid 检索：

- **BM25 / lexical**：始终可用（默认）
- **Semantic**：依赖可选的本地 nomic-embed-text-v1.5 daemon，**默认关闭**（依赖 ~600 MB）

```bash
hivemind embeddings install   # 打开 semantic
hivemind install --with-embeddings  # 装的时候就打开
```

不开 embeddings 时，README 显式说"搜索会静默降级到 BM25/lexical-only"——不会出现"找不到"的报错，**只是召回质量下降**。这是一个重要的边界，写在选型时必须知道。

### 6.3 Codebase Graph

trace 还顺带喂出一个 codebase 图：文件 / 符号 / imports / 真实访问边。所以"我们在哪里处理 auth？"这样的查询，**不只匹配字面 "auth"，还会命中团队 agent 实际访问过的文件**。

## 7. 一个真实任务流：从踩坑到团队复用

假设一个 5 人团队，所有人装了 Hivemind，scope = team：

1. **周一 14:32** — 老王的 Claude Code 在 `repo-orders` 里处理 Drizzle ORM 迁移，trace 落进 `sessions` 表。
2. **周一 14:35** — 后台 worker 每 20 turn 触发一次，扫描到老王在 3 段 trace 里都用同一个 pattern：`drizzle-kit generate:pg --schema=public` 之后必须先 `set search_path`。
3. **周一 14:35** — worker 把这个 pattern 写进 `repo-orders/.claude/skills/drizzle-pg-migration/SKILL.md`，同时同步到云端。
4. **周一 14:40** — 小李的 Cursor 在另一个项目里要做同样的事，SessionStart 时 Hivemind 把团队级 Rules 注入，beforeSubmitPrompt 时 hybrid 检索命中老王上线的 SKILL.md。
5. **周一 14:41** — 小李的 Cursor 直接拿到"先 set search_path"的提示，**没有从零踩坑**。

这就是 Hivemind 跟 `agentmemory` 最大的体感差异：**你不需要主动去 pull，新的经验是"自己飘过来"的**。

## 8. LoCoMo benchmark 怎么读

README 给出的数字（100 QA pairs，Claude Haiku，`claude -p`）：

| 指标 | Baseline | Hivemind | 提升 |
| --- | --- | --- | --- |
| Cost / 100 QA | $8.94 | $6.65 | **-25%** |
| Tokens / question | 1,700 | 1,008 | **1.7× 减少** |
| Turns / question | 8.9 | 6.2 | **-31%** |

这些数字可以采信，但**有几个使用边界**要先看到：

1. **基线是什么**。README 写的是"running without shared memory"，也就是无任何 Hivemind 介入；和"裸用 Claude Code"的体感差距会比数字更小（Claude Code 自带 Skills 系统，跨项目经验也能复用一部分）。
2. **模型是 Haiku，不是 Opus/Sonnet**。README 没有说换成更强模型后绝对收益是否仍线性；如果团队主要用 Opus，要把"省下的 token"和"多花的 thinking cost"放一起算。
3. **LoCoMo 是长上下文记忆 benchmark**（arXiv:2402.17753），不是编程任务 benchmark。对真实编码工作流，"省下多少 token"是个**间接信号**，"少踩多少坑"才是直接信号——后者**公开数据里没有**。
4. **样本量是 100 QA**，CI 没说。开源 benchmark 复现时建议自己再跑 200+ 验证。

简言之：**这是一个"指标方向正确，但不是产品定论"的 benchmark**。

## 9. 数据归属与安全：BYOC + 三层防护

Hivemind 的安全姿态是"**默认云端，可选自带云**"：

| 控制项 | 说明 |
| --- | --- |
| 传输 | TLS 全程 |
| 存储 | AES-256 落盘 |
| 凭据 | 放在 Deep Lake 自己的 vault，Hivemind 永远拿不到原始 key |
| 隔离 | Org / workspace 边界在**存储层**就强制，不是只在 API 层 |
| 单次关停 | `HIVEMIND_CAPTURE=false` 关掉整个 capture |
| 销毁 | 删 workspace → 底层对象一并清掉 |

自带云（BYOC）支持矩阵：

| Provider | 状态 |
| --- | --- |
| Google Cloud Storage | 可用 |
| Azure Blob Storage | 可用 |
| Amazon S3 | contact us |
| S3-compatible on-prem | contact us |

代码层面的小细节也值得看一下——`src/utils` 里强制使用 `sqlStr` / `sqlLike` / `sqlIdent` 三个转义函数；虚拟文件系统只放行 ~70 个白名单 builtins，未知命令直接拒绝；credentials 强制 `0600`、config dir 强制 `0700`；登录走 device flow，**不把 token 写进环境变量**。

这些都是好习惯，但**仍然要清楚**：所有这些防护的前提是"你的 workspace 里的人是可信的"——README 自己写明：

> "All users in your Deeplake workspace can read this data. That's the design."

这跟 GitHub repo 内任意成员可读代码是同一类设计。**不要把敏感 token / 客户数据 / 合规审计要求直接喂进去**。

## 10. 与 OpenClaw memory-core 的关系

OpenClaw 用户尤其关心这一点。Hivemind 官方明确说：

> "Hivemind runs **alongside** OpenClaw's built-in `memory-core` plugin. It does **not** claim the memory slot, so `memory-core`'s dreaming cron (`"0 3 * * *"`) and other memory-slot-dependent jobs keep working."

也就是说：

- `memory-core` 还是负责**单 agent** 的 recall / promotion / dreaming。
- Hivemind 在它**上面**叠一层**团队级**的 trace 共享 + skill 编码 + 规则注入。
- 两者**共存不冲突**，但**两者的存储是分开的**（`memory-core` 在 OpenClaw 本地，Hivemind 在 Deeplake 云端）。

如果你已经搭好了 `memory-core`，Hivemind 不是替换，而是**向上扩**。

## 11. 适用边界与采用顺序

### 11.1 适合

- 团队 ≥ 3 人，且**多 agent 并用**（有人用 Claude Code，有人用 Cursor）。
- 痛点是"同一个坑踩第二次"或"新人 agent 启动成本高"。
- 能接受 trace 进云端（或愿意做 BYOC 配置）。
- 已经用了一个 agent 的 skills 系统，希望在**团队层**再扩一层。

### 11.2 不适合

- 单人 / 单项目 / 单 agent——这种情况下 agentmemory 或 `CLAUDE.md` 已足够。
- 强合规场景（金融 / 医疗 / 政府）下不愿把 trace 落云端、又没人力做 BYOC 接入的团队。
- 期望 Hivemind 自动解决"agent 写不出好代码"——它解决的是**经验复用**，不是能力本身。
- 团队尚未形成"多 agent 协作"工作流——此时加 Hivemind 是为时尚早。

### 11.3 建议的采用顺序

1. **最小试用**：`hivemind install` + 单人单 agent 跑一周，看 trace 写入和召回是否符合预期。
2. **开 embeddings**：确认降级路径 OK 后 `hivemind embeddings install`，看召回质量提升。
3. **scope 调到 team**：先在小范围（2-3 人）开启 `hivemind skillify scope team`，观察 SKILL.md 数量和质量。
4. **接 MCP**：Hermes / pi 接入共享 MCP server，统一工具面。
5. **BYOC 评估**：合规允许时，迁到 GCS / Azure，关闭 Hivemind Cloud 默认路径。

## 12. 一段话总结

Hivemind 是 Activeloop 在编程 agent 工具链上的一次"**从单兵到团队**"的升级尝试。它不像 `CLAUDE.md` 那样是手工规则文件，也不像 agentmemory 那样只服务单个 agent；它把"trace → skill → 注入"做成一条云端流水线，让团队任何 agent 都能从队友的踩坑历史里直接获益。**前提是你愿意把 trace 交到云端（或者花力气接 BYOC），并且团队已经够大、痛点已经够"重复"**。如果只满足前两条但缺后一条，先把 agentmemory / OpenClaw memory-core 用好更划算。

## 参考

- 仓库：<https://github.com/activeloopai/hivemind>
- README（v0.7.89）：`https://raw.githubusercontent.com/activeloopai/hivemind/main/README.md`
- 源码结构：`src/cli`、`src/commands`、`src/deeplake-api.ts`、`src/deeplake-schema.ts`、`src/skillify`、`src/mcp`、`src/embeddings`、`src/graph`、`src/rules`、`src/notifications`
- 安装包：`@deeplake/hivemind`（npm），Node ≥ 22.0.0
- Benchmark 引用：LoCoMo（Maharana et al., arXiv:2402.17753）
- 关键依赖：`deeplake ^0.3.30`、`@modelcontextprotocol/sdk ^1.29.0`、`@anthropic-ai/sdk ^0.97.1`、`zod ^4.3.6`
- 仓库元数据（2026-06-11 抓取）：953 stars / 53 forks / 36 open issues / TypeScript / Apache-2.0
