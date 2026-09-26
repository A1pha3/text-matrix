---
title: "InsForge：给 AI 编码代理的全栈后端平台"
date: "2026-05-06T20:05:34+08:00"
slug: "insforge-ai-backend-platform-guide"
github_repo: "InsForge/InsForge"
source_key: "gh:InsForge/InsForge"
description: "InsForge 是一个面向 agentic coding 的开源后端平台：十个后端产品共用同一套 REST、JWT 与 MCP 接口，AI 编码代理通过 MCP 服务器和 CLI 建表、跑迁移、部署函数、读日志，人只负责定义意图和审查结果。"
draft: false
categories: ["技术笔记"]
tags: ["AI 编程", "MCP", "Docker", "开源", "后端"]
lastmod: "2026-09-26T22:14:00+08:00"
---

后端平台不缺新面孔，缺的是为 AI 编码代理设计的操作界面。InsForge（Apache-2.0，2025 年 7 月创建，截至 2026 年 9 月 26 日 13,022 stars）把默认操作者设为代理而不是人：数据库、认证、存储、实时通道、边缘函数、模型网关等十个产品共用同一套 REST 接口、同一套 JWT 鉴权，再通过一个 MCP 服务器和一套 CLI 暴露成代理可直接调用的工具与命令。人定义意图、审查结果；建表、迁移、部署、排障由代理在终端里完成。官方对比页对这种角色转变的表述是：传统平台上你"实现并执行"，用 InsForge 你"定义意图并审查"。

这个定位决定了它和 Supabase、Firebase 的根本差异不在产品清单，而在每个产品同时暴露两个操作面——给人用的仪表盘，给机器用的 MCP 与 CLI。下文先看系统全貌，再拆 MCP 工具面与 CLI 工作流，最后给自托管与云上两条路径的采用建议。

## 系统地图：十个产品与两条通道

官方文档把产品线归纳为十个，共用"同一套 REST、同一套 JWT、同一个 MCP 服务器、同一组 SDK"：

| 产品 | 职责 |
|------|------|
| Database | 托管 Postgres，支持迁移、后端分支、pgvector、S3 备份；每张表自动生成类型化 REST 与 SDK 接口 |
| Authentication | 邮箱密码、免密、OAuth、移动端登录；JWT 会话、行级安全（RLS），也可作为 OAuth 服务器 |
| Storage | S3 兼容对象存储，签名 URL、行级策略，可配 rclone、AWS CLI、Terraform |
| Realtime | 单条 WebSocket 推送数据库变更、广播与 presence，订阅和发布都过 RLS 检查 |
| Edge Functions | Deno 运行的无服务器 TypeScript，支持定时任务和数据库触发链式调用 |
| Model Gateway | OpenRouter 路由的 OpenAI 兼容接口，平台托管密钥、按项目计量与限额 |
| Sites | 前端构建与托管，自动关联后端项目 |
| Messaging | 事务性邮件，SMS 与推送在路线图上 |
| Payments | Stripe 结账、订阅与客户门户流程 |
| Compute | 长时运行容器，跑队列 worker、推理循环、WebSocket 服务这类负载（官方仍标 private preview） |

代理操作这些产品的通道有两条：

- **MCP 服务器**（自托管与云都可用）：云端托管地址 `https://mcp.insforge.dev/mcp`，HTTP 传输；自托管实例在仪表盘按引导接入。
- **CLI + Skills**（仅云）：`@insforge/cli` 命令行加配套代理技能，从终端直接驱动，不要求编辑器支持 MCP。

自托管栈由四个容器组成，`docker compose up -d` 即可拉起：

```text
AI 编码代理（Cursor、Claude Code、Codex…）
   │  MCP：https://mcp.insforge.dev/mcp
   ▼
InsForge 应用容器（仪表盘 + API，默认端口 7130）
   ├─ PostgREST v12.2.12：把 Postgres 15 的每张表暴露成 REST
   ├─ Deno 2.0.6：边缘函数运行时
   ├─ Storage：默认本地文件系统，可加 MinIO/RustFS 或自备 S3
   └─ Realtime：应用内 WebSocket（数据库变更/广播/presence）
```

端口有分工：7130 是仪表盘与 API，7131 是 auth 端口且只绑定 127.0.0.1。用户侧不需要装 Node.js——应用镜像内置 Node 20，另外三个组件（Postgres、PostgREST、Deno）都是现成镜像。

## MCP 工具面：代理能看到什么、能改什么

MCP 服务器对代理暴露 16 个工具，按产品分五区：

| 区 | 工具 | 用途 |
|----|------|------|
| Database | `get-table-schema`、`run-raw-sql`、`bulk-upsert` | 读表结构、执行受限裸 SQL、批量写入 |
| Storage | `create-bucket`、`list-buckets`、`delete-bucket` | 管理存储桶 |
| Functions | `create-function`、`get-function`、`update-function`、`delete-function` | 管理 Deno 边缘函数 |
| Deployment | `create-deployment`、`start-deployment`、`get-container-logs` | 部署应用、读容器日志 |
| Setup & docs | `fetch-docs`、`get-anon-key`、`get-backend-metadata` | 拉取文档、生成匿名密钥、索引后端元数据 |

权限上有一条硬边界：裸 SQL 走与 REST API 相同的严格模式端点，要求 admin 密钥，系统表和 `auth.users` 被阻断。也就是说代理拿到的是有约束的写权限，不是裸管理员。

支持哪些代理，官方用代理目录（insforge.dev/agents）维护，文档里给出分步配置的有 Cursor、Claude Code、GitHub Copilot、Codex、Windsurf、Google Antigravity、Kiro、Cline、Trae 等。连接是否成功，验证方式是给代理发一句固定提示词：

```text
I'm using InsForge as my backend platform, call InsForge MCP's fetch-docs tool to learn about InsForge instructions.
```

代理拉到文档后就知道怎么用其余工具——把产品说明书做成代理调用的第一个工具，是这类平台里一个务实的设计。

## Agent-native 四原语：CLI、配置即代码、分支、诊断

MCP 解决编辑器里的代理，CLI 解决任何终端里的代理。官方把这套机制称为 agent-native 原语，共四件：

**CLI harness**。用 `npx @insforge/cli` 调用，官方明确不建议全局安装，让代理始终用项目锁定版本。每个命令都支持 `--json` 输出结构化结果，`--yes` 跳过交互确认。命令面分七个区：登录与上下文、项目管理、schema 迁移、配置、分支、构建类操作（函数/存储/部署/密钥/定时任务/模型）、诊断。npm 包 `@insforge/cli` 当前 0.2.8，engines 要求 Node ≥ 18。

**Config as code**。认证、SMTP、存储、保留策略、部署设置写在项目的 `insforge.toml` 里，`config plan` 预览差异、`config apply` 应用、`config export` 导出。项目配置进版本库，走 PR 评审而不是表单。

**Branching**。把整个后端克隆成隔离分支去试危险变更，验证后 merge，或者 reset 直接丢弃。数据库 schema 变更本身就是仓库里的迁移文件，和 `insforge.toml` 一样可评审、可回滚。

**Diagnostics**。`diagnose` 拉取 advisor 安全发现、数据库健康、指标与错误日志；`diagnose --ai "问题描述"` 让模型解读这些数据并给出修复方向。官方举的例子是代理自己发现"RLS 策略过宽"并自行修复，不需要人记得去检查。

另外每个项目内置四个保留密钥：`ANON_KEY`（公开客户端键）、`API_KEY`（admin 密钥，`ik_` 前缀）、`JWT_SECRET`、`INSFORGE_BASE_URL`，都可用 `secrets` 子命令读取和轮换，轮换支持宽限期。

### 任务流案例：加一张订单表

四件原语串起来就是官方给的标准代理回路。假设代理接到需求"给应用加订单表"：

```bash
# 1. 读当前后端状态
npx @insforge/cli --json metadata

# 2. 建隔离分支，写迁移并应用
npx @insforge/cli branch create add-orders
npx @insforge/cli db migrations new add-orders-table
npx @insforge/cli db migrations up --all

# 3. 诊断验证，必要时让模型解读输出
npx @insforge/cli diagnose --json
npx @insforge/cli diagnose --ai "why are auth requests failing after the last migration?"

# 4. 验证通过后合回主分支
npx @insforge/cli branch merge add-orders
```

整个流程没有一步需要打开仪表盘：元数据、迁移状态、诊断结果都是结构化输出，变更以迁移文件和配置文件的形式存在，可提交、可评审。这和"AI 生成一段 SQL、你自己粘贴执行"是两回事——代理操作的是真实后端，读回的也是真实状态。

## 从七产品到十产品：半年三次扩张

本文初版写于 2026 年 5 月。半年过去，项目的口径换了三轮，对照着看更能看出走向：

**产品面扩张。** 5 月的 README 列七个产品（认证、数据库、存储、模型网关、边缘函数、Compute、站点部署）；现在文档列十个，新增 Realtime、Messaging、Payments，另有 Analytics（接 PostHog）、Web Scraper（接 Apify）等集成专题。方向很清楚：从"给代理的后端原语"长成"代理能搭完整应用的全家桶"。

**措辞收敛。** 5 月的 README 用"语义层（semantic layer）"描述自己的架构位置，以 Fetch/Configure/Inspect 三个动词概括代理的操作；现行 README 不再提语义层，改为两条具体的通道（MCP 服务器、CLI + Skills）和两个动作（读后端上下文与状态、配置后端原语）。

**安装简化。** 5 月的自托管要手动 clone 仓库、复制 `.env` 模板、自己生成密钥；现在一条 setup.sh 命令完成初始化并自动生成全套密钥（见下节）。云路径注册后 `npx @insforge/cli link` 即可连上约 3 秒就绪的项目。当前版本 v2.3.2（2026-09-08 发布）。

## 快速开始

### 云路径（官方推荐）

在 insforge.dev 注册并创建项目，后端约 3 秒就绪，从浏览器地址栏复制 Project ID，然后在你的应用目录里执行：

```bash
npx @insforge/cli link --project-id <your-project-id>
```

最后给代理发验证提示词：

```text
I'm using InsForge as my backend platform. Read the current directory, make sure InsForge skills are installed, and use InsForge CLI for backend tasks.
```

### 自托管（Docker Compose）

```bash
# 初始化：拉取部署文件并生成密钥
curl -fsSL https://raw.githubusercontent.com/InsForge/InsForge/main/deploy/setup.sh | sh -s ~/insforge

cd ~/insforge
$EDITOR .env          # 按需设置 API_BASE_URL（浏览器访问用的地址）
docker compose up -d

# 打开 http://localhost:7130，按引导把 MCP 服务器接到你的代理
```

setup.sh 做两件事：拉取部署文件；生成 `JWT_SECRET`、`ENCRYPTION_KEY`、`POSTGRES_PASSWORD`、`ROOT_ADMIN_PASSWORD` 和两个访问密钥，写进 `~/insforge/.env`（权限 600）。重复执行只补缺，不覆盖你改过的值。

三个容易踩的坑：

- **不要跳过 setup.sh 直接 compose up**。compose 文件里的密钥带占位默认值，直接启动等于拿公开默认密钥跑服务。
- **多实例要改 `COMPOSE_PROJECT_NAME`**。两个目录共用默认项目名会共享同一组容器；每个实例再配一套端口变量（`POSTGRES_PORT`、`POSTGREST_PORT`、`APP_PORT`、`AUTH_PORT`、`DENO_PORT`）。
- **存储后端默认是本地文件系统**。要 S3 语义需在 `COMPOSE_FILE` 追加 MinIO 或 RustFS 的 overlay，或者直接配自备 S3 端点（AWS S3、R2、Wasabi、腾讯云 COS、阿里云 OSS 等）；配好后 `/storage/v1/s3` 网关对 aws CLI、rclone 和各语言 AWS SDK 开放。

不想装 Docker，Railway、Zeabur、Sealos、RepoCloud、ZopDay 五个平台有一键部署模板。

## 商业化与成本

云服务三档：

| | Free | Pro | Enterprise |
|---|---|---|---|
| 价格 | $0 | $25/月 | 定制 |
| 月活用户 | 5 万 | 10 万 | 定制 |
| 数据库 | 500 MB | 8 GB | 定制 |
| 流量 | 5 GB | 250 GB | 定制 |
| 文件存储 | 1 GB | 100 GB | 定制 |
| 模型额度 | $1 | $10/月 | 定制 |
| 边缘函数调用 | 10 万次 | 10 万次，超出按量 | 定制 |
| Compute | 120 小时/月（默认规格） | 按量计费，含 $10 抵扣 | 按量计费 |

Pro 超出包含量后按量计费，Free 项目闲置一周会被暂停。`npx @insforge/cli usage` 可查当前周期的用量明细。自托管则完全免费，只承担自己的基础设施成本；Compute 在自托管下默认跑在本机 Docker（挂载 docker.sock），也可配 Fly.io 用你自己的账户（`FLY_API_TOKEN` + `FLY_ORG`）。

## 适用边界与采用建议

先说不适合的场景：

- **Compute 没有持久卷**。镜像、环境变量或端口一变，容器即重建、内部写入即丢失，持久数据必须放 Postgres 或 Storage；需要挂盘的负载现在满足不了。
- **Compute 仍标 private preview**，生产依赖前留意。
- **代理拿到的是真实写权限**。严格模式 SQL 挡住了系统表，但 admin 密钥本身的管理在你自己手上，给代理的密钥要按项目隔离。
- 不使用 AI 编码代理、后端由人工维护的团队，它相对 Supabase 这类成熟方案没有优势。

最顺的路径是用 AI 编码代理做全栈原型和中小应用的团队：云免费档零成本起步，CLI 与 MCP 的代理工作流是现成的，Stripe 支付和模型网关省掉两块最常见的集成工作。数据必须留在自己机房的环境走自托管四容器，把代理指向自托管实例的 MCP 端点即可。

对比 Supabase、Firebase 时注意官方 alternatives 页自带立场，但两个事实点站得住：Payments 内置 Stripe 集成（Supabase 需要自己在应用代码里接），Firebase 不支持自托管（InsForge 四容器 compose 即起）。数据库选型上两者同为 Postgres 系，迁移成本主要在 SDK 与 RLS 约定，不在数据模型。

## 结语

InsForge 的赌注是后端的操作界面会从仪表盘迁到代理的终端。实现上没有黑魔法——Postgres、PostgREST、Deno 都是成熟组件，价值在于把十个产品收拢成一套统一的 MCP 工具面和一条全程 `--json` 的 CLI 通路，再用分支、配置即代码、诊断三件事把代理的写权限管出工程化的样子。值不值得跟，看你的团队里 AI 编码代理承担的编码比例：比例越高，这个"代理当后端工程师"的平台越接近刚需。

**官网**：<https://insforge.dev>
**官方文档**：<https://docs.insforge.dev>
**代理目录**：<https://insforge.dev/agents>
**仓库**：<https://github.com/InsForge/InsForge>

---

数据口径：stars、版本、产品清单、定价核对自 GitHub 仓库 InsForge/InsForge（main 分支与 v2.3.2）及仓库内 docs/ 目录，时点 2026-09-26。项目迭代快，采用前以官方文档为准。
