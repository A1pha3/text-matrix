---
title: "camelAI：把整个 AI 编码 Agent 塞进 Cloudflare Durable Object 的工程实践"
date: "2026-07-30T22:00:00+08:00"
draft: false
slug: "camelai-cloudflare-durable-object-ai-coding-platform"
github_repo: "qaml-ai/camelAI"
source_key: "gh:qaml-ai/camelAI"
description: "camelAI（qaml-ai/camelAI）把 AI 编码 Agent 的整条执行链——聊天状态、Agent 循环、项目文件系统、Code Mode 工具、构建沙箱——全部压在 Cloudflare Workers + Durable Objects 上，不开 VM 也能跑生产级 Coding Agent。本文拆解 ChatThreadDO、WorkspaceFilesystemDO、Code Mode、Workers for Platforms 联邦这四层结构，给出三个真实任务流的端到端路径，并讨论它在自托管、模型灵活性和沙箱可信度上的边界。"
categories: ["技术笔记"]
tags: ["Cloudflare", "Durable Objects", "AI Agent", "camelAI", "Workers for Platforms", "架构分析"]
lastmod: "2026-10-04"
---

## 本文导读

读完本文你将能够：

- 说清 camelAI 想解决的问题：把 AI 编码 Agent 从「VM 上的长进程」拆解成「Cloudflare Workers 上的可序列化组件」
- 拆出它的四层结构：ChatThreadDO / WorkspaceFilesystemDO / Code Mode / 沙箱联邦，每一层负责什么、不负责什么
- 跟着三个具体任务走通整个系统：建项目并部署、运行一个 notebook 分析、把外部数据库数据接进应用
- 看清八个 Worker 组成的联邦里 dispatcher / app-usage-guard / discord-bridge / user-logs-tail 各承担什么职责
- 评估它在自托管、模型灵活性和沙箱可信度上的真实边界，知道什么时候该用、什么时候不该用

一个时点声明：本文的源码分析锚定 2026-07-30 发表当日的主干（commit `7e259795`），行数、文件名和引语都对这个时点负责。这个仓库迭代极快——2026-10-04 复核时，两个多月里主干已合入 150 多个 PR，ChatThreadDO 所在文件从 7,863 行瘦身到 316 行，Bedrock 网关从独立 Worker 并入主 Worker。第九节给了完整的漂移清单；文中所有 era 时点结论都以「发表时」标记。

## 一、判断先行：camelAI 不是「又一个 Claude Code」

camelAI（仓库 [qaml-ai/camelAI](https://github.com/qaml-ai/camelAI)，公开域名 [camelai.com](https://camelai.com)）给出的答案不是「更好的 prompt 或更强的模型」，而是把整套 AI 编码平台拆成四个可在 Cloudflare Workers 上独立伸缩的层。这套拆法的关键事实有三条：

第一，每个聊天线程对应一个 `ChatThreadDO`。Agent 的循环、消息历史、运行态全在 Durable Object 里——而不是一台 VM。这件事直接消灭了「会话断了 Agent 进程没了」这个传统编码 Agent 最头疼的故障。

第二，Agent 写 JavaScript，不写 bash。Code Mode 把用户生成的 JS 包成独立 Worker 在 V8 isolate 里跑，凭证留在 isolate 外面。这是它和 Claude Code、Codex 这类以 shell 命令为底座的 Agent 在实现哲学上的分水岭。

第三，发布路径走 Cloudflare 自家的 Workers for Platforms。用户写完的应用不是「部署到 K8s」「部署到 VM」，是直接编译成 Worker Bundle 推到 dispatcher 命名空间，DNS 一指就到 `*.camelai.app`。

如果只把 camelAI 看作一个 AI 编码助手的开源实现，会低估它的工程价值。它的真正贡献，是给「在 Cloudflare 全家桶上能不能跑生产级 AI 平台」这个问题写了一整套工程答卷。

## 二、四层结构总览

先看地图。下面这张图转录自发表时仓库 `README.md` 的架构章节，注意它其实画了两条线：ChatThreadDO 下面分出的三个执行面（Code Mode、文件系统、沙箱容器），以及 `deploy_project` 单独走的发布线（构建沙箱 → Workers for Platforms → Dispatcher → 线上应用）：

```text
React Router SSR + browser WebSocket
                  |
                  v
       Cloudflare main Worker
                  |
                  v
       ChatThreadDO (coding agent)
       custom harness built on pi
                  |
       +----------+-----------+----------------+
       |                      |                |
       v                      v                v
Code Mode dynamic     WorkspaceFilesystemDO   Short-lived Cloudflare
Worker / V8 isolate     SQLite + R2 files      sandbox containers
JavaScript tools,       Artifacts history      build / notebook / SQL
data connections

deploy_project: project files -> build sandbox -> Workers for Platforms
                                                   |
                                                   v
                                        Dispatcher Worker -> live app
```

层与层之间的依赖是单向的：上层调用下层提供的 RPC，下层不知道上层存在。这种切法让每一层都能独立替换——换掉 Code Mode 不影响文件系统，换掉 WorkspaceFS 不影响沙箱。

### 2.1 ChatThreadDO：Agent 循环住在 Durable Object 里

发表时 `workers/main/src/chat-thread-do.ts` 整个文件 7,863 行，是整个平台的心脏。它的关键设计有四点：

**继承自 Cloudflare 官方 `AIChatAgent`**（`@cloudflare/ai-chat`），而不是自己造流式传输。`AIChatAgent` 已经把 SQLite chunk 缓冲、断线重连、消息持久化做完了，camelAI 在这之上做的是把 Agent 循环接进去。仓库注释里写得很清楚：

> Extends AIChatAgent for its resumable-stream transport (SQLite chunk buffering + replay on reconnect) and, later, chatRecovery. The ai-chat message model is transport-internal only: pi_core_messages remains the canonical history and the Pi runtime owns the agent loop.

分工由此明确：传输层用 AIChatAgent，事实层用 pi 的 core messages。两层职责切清楚，AIChatAgent 那一层将来要换也能换。

**Agent 循环用 pi 的底层库自建**。它从 `@earendil-works/pi-agent-core` 拿 `Agent as PiCoreAgent`，从 `@earendil-works/pi-ai` 拿 `Model` 抽象。注释里有句直接表态：

> The agent is camelAI's own harness, built from pi's lower-level agent loop and state-management libraries. It is not Claude Code or Codex.

Anthropic、OpenAI、OpenRouter、Bedrock、自定义端点都可以提供底层模型，但它们都不提供 Agent harness——harness 是 camelAI 自己写的。

**调用面是 callable + WebSocket**。`ChatThreadDO` 把 `sendMessage`、`requestStop`、`answerQuestion`、`getOlderUiMessages` 等方法标成 Cloudflare Agents SDK 的 `callable()`，前端通过 WebSocket 直接调 DO 实例的这些方法，不需要单独的 REST API。代码里的注册片段：

```ts
callable()(this.prototype.requestStop, context);
callable()(this.prototype.setPreviewTabsState, context);
callable()(this.prototype.answerQuestion, context);
callable()(this.prototype.submitConnectionSetupResponse, context);
callable()(this.prototype.refreshModel, context);
callable()(this.prototype.sendMessage, context);
callable()(this.prototype.getOlderUiMessages, context);
```

**每个方法对状态的影响都在 DO 实例字段上可见**。`piSessionPromise`、`piSession`、`piActiveItemId`、`piAssistantText`、`streamingLeaseRefreshTimer` 这类字段按设计在源码里就暴露出来，目的是让 unit test 用 `Object.create(ChatThreadDO.prototype)` 这样的 fake seam 直接覆盖某一字段，而不用构造完整的 DO 实例。`workers/main/tests/` 下面有 17 个 `chat-thread-*.test.ts`，全是这种 seam 风格的测试。

### 2.2 WorkspaceFilesystemDO：SQLite + R2 双层文件系统

`workers/main/src/workspace-filesystem-do.ts` 是项目文件存储 DO，发表时 1,860 行。它的存储分层是 Cloudflare 生态里典型的「小文件进 SQLite / 大文件进 R2」结构，关键代码片段：

```ts
import { DurableObject } from "cloudflare:workers";
import { Workspace, type FileInfo } from "@cloudflare/shell";

const WORKSPACE_STORE_NAMESPACE = "default";
const WORKSPACE_STORE_TABLE = `cf_workspace_${WORKSPACE_STORE_NAMESPACE}`;
```

底层用的是 `@cloudflare/shell` 的 `Workspace` 库。注释里把它和 R2 的对应关系钉死：

> The @cloudflare/shell Workspace store (v0.3.7) namespaces its SQLite table and R2 object keys. We construct it with no `namespace`, so it defaults to "default": rows live in `cf_workspace_default` and each spilled file's R2 key is `${r2Prefix}/default${normalizedPath}` (see Workspace.r2Key).

也就是说，文件大小过阈值（`DEFAULT_INLINE_THRESHOLD = 1_500_000` 字节）就 spill 到 R2，路径前缀由 `@cloudflare/shell` 的 `r2Key` 公式决定。任何对该库 namespace 默认值或 `r2Key` 公式的升级，都得同步改 `adoptR2FileInto` 这条迁移路径——这是仓库显式标注的脆弱点。

文件版本历史则走 Cloudflare Artifacts（在 `WorkspaceFilesystemEnv.ARTIFACTS` 里以 binding 形式注入），不是自己造 git。每次 `deploy_project` 之前系统会拿到一个 `list_commits()` 返回的快照 ID，用于 `revert_project`。

### 2.3 Code Mode：AI 写 JavaScript，凭证留在沙箱外

Code Mode 是 camelAI 最具特色的设计。它的核心论点是：让 Agent 写 bash 命令存在「每个工具都要重新解析参数、shell 转义、错误处理分散」三个痛点；改写成 JS 后，这些问题一次性解决。

执行器在 `workers/main/src/code-mode-runner.ts`。关键步骤：

```ts
import { transform as sucraseTransform } from "sucrase";

const TS_STRIP_PREFIX = "async function __camelTypeStrip__() {\n";
const TS_STRIP_SUFFIX = "\n}";

export function stripTypeScriptFromUserCode(userCode: string): string {
  // 把用户代码包成 async function，再用 sucrase 剥 TS
  // sucrase 失败则原样返回，保证 JS 行为不回归
}
```

它支持 TypeScript：模型写带类型的 JS 代码，由 sucrase 在执行前剥成 JS。失败 fallback 到原文，确保「普通 JS 永远能跑」。

执行容器不是真 Worker，而是动态 import 出来的 Worker entrypoint。模板里写得很清楚：

```ts
const workerPrefixTemplate = String.raw`
import { WorkerEntrypoint } from "cloudflare:workers";
const USER_CODE_START_LINE = __USER_CODE_START_LINE__;
const USER_CODE_END_LINE = __USER_CODE_END_LINE__;
const store = new Map();
function stringifyOutput(value) { /* ... */ }
...
`;
```

每次 `js_exec` 调用都会拼接一份新的 Worker 模板再编译，对应 README 的原话「Code Mode runs that JavaScript in fresh V8 isolates」——每次都是干净的 V8 isolate，没有跨调用的状态泄漏。

凭证隔离是这套设计的核心。模型能拿到的是 `env.PROJECTS`、`tools.deploy_project(...)`、`connections[alias]` 这样的平台和连接句柄，但拿不到 `connection.credentials` 本身。仓库里有专门的 `code-mode-integrations.ts`（589 行）维护连接发现和注入逻辑，避免把密钥塞到模型上下文里。

工具集规模可观，`code-mode-tools.ts` 发表时 4,632 行，按类别分文件：

| 文件 | 工具类别 | 行数 |
| --- | --- | --- |
| `code-mode-runner.ts` | 执行器（sucrase + Worker 编译） | 1,385 |
| `code-mode-tools.ts` | 主工具集 | 4,632 |
| `code-mode-web-search.ts` | 网络搜索 / 抓取 | 1,518 |
| `code-mode-integrations.ts` | 外部连接发现与注入 | 589 |
| `code-mode-custom-domains.ts` | 自定义域名 | 325 |
| `code-mode-deterministic-automations.ts` | 定时任务 | 235 |
| `code-mode-scheduled-prompts.ts` | 定时 prompt | 130 |

### 2.4 Cloudflare 沙箱联邦：只做 Linux 才能干的事

Agent 大部分时间住在 DO + V8 isolate 里，但有些活必须有真 Linux——npm install、构建、Jupyter notebook、SQL 查询。发表时这些活由四个继承自官方 `@cloudflare/sandbox` 的沙箱类承接：

```ts
import { Sandbox } from "@cloudflare/sandbox";

export class ProjectBuildSandbox extends Sandbox<Env> {}
export class AnalysisSandbox extends Sandbox<Env> { /* 连接 RPC、会话管理 */ }
export class DbQuerySandbox extends Sandbox<Env> { /* 静态 IP 出口、SSRF 防护 */ }
export class EvalSandbox extends Sandbox<Env> {}
```

四个沙箱各管一摊事：

| 沙箱 | 职责 | 网络姿态 |
| --- | --- | --- |
| `ProjectBuildSandbox` | 每个 org 一份 warm 容器，专门跑 `npm install` / `vite build` 等需要 npm registry 出网的构建命令；只执行平台下发的固定命令 | 需要出网（装包），与数据面隔离 |
| `AnalysisSandbox` | 每个 workspace 一份 warm 容器，跑 Jupyter notebook、临时 Python 和 DuckDB 跨源归减，按会话隔离 | `enableInternet = false`，出口白名单只有 PyPI 两个域名 |
| `DbQuerySandbox` | 跑 SQL 查询与数据仓库导出（Parquet 写回 R2） | 开网（要解析客户数据库主机名），但数据库流量走 static-IP 中继，双侧 SSRF 防护 |
| `EvalSandbox` | 承载 agent evals 的容器基建 | —— |

Analysis 和 DbQuery 这两个数据面沙箱的网络设计值得单独看，源码注释写得很坦白：

**AnalysisSandbox 是「关互联网 + 白名单」，而不是「密封盒子」**。出口白名单只放 PyPI（`pypi.org`、`files.pythonhosted.org`，让 `uv` 能装预装栈之外的包），再加一个拦截主机 `connections.internal`——容器里的 notebook 代码 POST 到这个主机时，请求根本不离开 Cloudflare，由沙箱出口层转交 Worker 侧注册的 `connectionsRpc` 处理器执行，workspace/org 作用域由 DO 侧附加，容器代码伪造不了。注释里有一句关键承诺：「no token or credential ever enters the container」。数据输入走只读 R2 挂载（连接导出和工作区上传），同样不经过互联网。这个容器还吸收了更早的 `WarehouseSandbox`——源码自述「the successor to (and absorption of) WarehouseSandbox」，DuckDB 归减原来就是封闭仓库的全部工作。

**DbQuerySandbox 保留开网，用出口中继保住固定 IP**。很多客户数据库有 IP 白名单，容器必须以固定 IP 出去：数据库流量经 `cloudflared access tcp` → Cloudflare Tunnel → gost 中继（Terraform 管理，在 `infra/db-egress-relay/`，是整个体系退役 VM 潮后唯一保留的 VM），不配中继则直连。两种模式下 runner 都做 SSRF 防护，gost 在 VM 侧再验一遍同一份黑名单。导出走无凭证的 R2 挂载——S3 密钥不进容器，warehouse 前缀以读写挂载，导出结果直接写 Parquet。

仓库 `AGENTS.md` 明确指出历史包袱已退出：

> The Go data-proxy (external `qaml-ai/project-runtime-service` `cmd/data-proxy`) is retired: SQL queries and warehouse exports now run in the `DbQuerySandbox` Cloudflare container.

原文还有后半句：配套的 `SANDBOX_HOST` VPC binding 一并删除，「Do not reintroduce either」。之前的 Azure `project-runtime-service` VM 和 `PROJECT_RUNTIME_HOST` 桥接也已移除，剩下的唯一 VM 就是上面那个数据库出口中继。也就是说，主平台不再依赖外部服务，只在数据库出网这一处保留一台静态 IP 中继机。

## 三、三个任务流走通整个系统

光看四层抽象还不够。下面是三个真实任务从用户输入到结果的端到端路径，每一步对应到上面的层级。

### 3.1 任务流 A：从空白工作区创建一个可部署的应用

1. **用户在浏览器发消息**：「帮我做一个待办清单应用，用 SQLite 存数据」。浏览器与 main Worker 之间是一条 WebSocket 长连接（发表时的架构图如此标注；2026-10 复核时已改为 HTTP/SSE）。
2. **WebSocket 命中** `ChatThreadDO` 实例（按 `threadId` 寻址）。Agent 循环开始——首次创建前必须 `read_skill({ skill: "developing-software" })`，这是 `pi-system-prompt.ts` 里的硬约束。
3. **Agent 调 `create_project`**：根据 system prompt 选择 `crud` 模板（默认），seed 出完整 React Router + Durable Object SQLite CRUD 脚手架。`create_project` 返回 project id 与 backend 标记 `do-r2`。模板一共六种：`crud`（默认）、`vanilla`（零依赖纯前端）、`ai-chat`、`integration-dashboard`、`data-dashboard`、`data-analysis`（notebook 报告）。
4. **Agent 改文件**：在 `js_exec` 里用 `await tools.add_shadcn_component(...)` 加按钮和列表组件，文件位置全部走 `location: "project"`。
5. **Agent 调 `deploy_project`**：这条调用会触发 `ProjectBuildSandbox` 拉镜像、装依赖、构建，再把产物收集成 Worker Bundle 推到 dispatcher 命名空间。成功后返回 live URL 并自动打开预览——AGENTS.md 原话「no manual `set_preview` is needed」（工具仍在，用于显式切换预览）。
6. **用户在浏览器看到应用**：`*.camelai.app` 子域名指向 dispatcher Worker，dispatcher 把请求路由到对应的 user app worker bundle。

整个链路里，Agent 调的是平台工具，不是 bash。Sandbox 只承担 build 这一段，其余都在 DO 和 isolate 里完成。

### 3.2 任务流 B：跑一个数据探索 notebook 并发布为报告

1. **用户**：「读 `uploads/sales.csv`，做一个区域销售额的柱状图，然后发我链接。」
2. **Agent 调 `create_project`（template: `data-analysis`）**，seed 出 `analysis.ipynb`。
3. **Agent 检查依赖**：通常什么都不用装——pandas、numpy、polars、duckdb、altair、plotly、matplotlib、scikit-learn 等 Python 数据栈在分析容器里预装，需要额外包时走 `add_python_dependency`。
4. **Agent 调 `run_notebook`**：执行 `jupyter nbconvert --execute --inplace`，输出写回 project，验证 `validation.clean`，成功后自动 `set_preview` 打开 notebook。
5. **Agent 调 `deploy_project({ publish_intent: "user_requested" })`**：把执行完的 notebook 编译成静态报告 app 发布到 dispatcher。
6. **用户拿到链接**：报告 app 是只读静态站点，不需要持续服务。

注意 `publish_intent: "user_requested"` 是显式门槛——`data-analysis` 模板的 notebook 默认不发布，必须用户明确请求。这是为了避免 Agent 在用户没要求时自动公开报告。

### 3.3 任务流 C：把 ClickHouse 数据接进应用

1. **用户在工作区连接 ClickHouse**：填好主机和凭证后，凭证经 `INTEGRATION_SECRET_KEY` 加密成 `credentials_encrypted` 存进组织 DO（`workers/main/src/identity/` 下的 `OrgDO`），界面只显示「已连接」，不回显密钥。
2. **Agent 在 js_exec 里先发现连接**：连接不是普通变量，而是一个冻结的 runtime 门面，官方示例代码是：

```js
const entry = await env.CONNECTIONS.find("clickhouse");
return await connections[entry.alias].query({ query: "SELECT 1 AS ok" });
```

   `env.CONNECTIONS` 这个门面还带 `list` / `get` / `methods`（方法目录）/ `verify`（健康检查）/ `test`（冒烟测试）/ `invoke` 等辅助入口。Agent 拿到的是按别名索引的句柄，不是连接串。

3. **Agent 写业务代码**：用 `connections[alias].query(...)` 跑查询、把结果交给前端组件，或经连接的 `export` 方法落成 R2 导出再挂载读取。
4. **Agent 把数据塞进 app**：通过 file tools 写到 project 文件，触发 `deploy_project`。

关键在第 2 步：Agent 全程接触不到解密后的凭证。解密只发生在 Worker 侧的连接运行时里（`connections-runtime.ts`），查询请求由平台代转——分析沙箱里的 notebook 更彻底，连它的数据库访问都走 `connections.internal` 拦截主机，凭证从来不过容器边界。README 对这套模型的定位是「Credentials remain outside the execution sandbox」。

顺带纠正一个容易混淆的点：Slack（还有 Telegram、Discord、email）在 camelAI 里不是这种数据连接，而是**聊天渠道**——把 agent 接进 Slack 工作区，让你在频道里直接和它对话，事件经 `slack-events-queue.ts` 排队处理。发表时 hosted 数据连接适配器覆盖的是 ClickHouse、Postgres、BigQuery、Snowflake、MongoDB、Airtable、Shopify、Twilio、Zendesk 这类数据与业务服务，Slack 不在其列。

## 四、Workers for Platforms 联邦

camelAI 不只一个 Worker。发表时 `workers/` 下面有八个独立的 Worker：

| Worker | 职责 |
| --- | --- |
| `main/` | 主入口：WebSocket、API、MCP、admin、Stripe webhook |
| `dispatcher/` | Workers for Platforms dispatcher，路由已发布的 user app |
| `app-usage-guard/` | 账户级 Durable Object SQLite 用量监控，可逆隔离异常 app |
| `bedrock-provider/` | 自定义 AI Gateway provider，把 Anthropic 风格请求翻译到 Bedrock |
| `discord-bridge/` | Discord Gateway 长连接（`DiscordGatewayDO`）+ 控制 DO |
| `user-logs-tail/` | 抓取已发布 app 的 tail 日志事件，转发给主 Worker 里的 `WorkerLogsDO` 持久化 |
| `e2e-reports/` | 公开 viewer，从 R2 托管 Playwright E2E 报告（`e2e-reports.camelai.dev`） |
| `eval-reports/` | agent evals 的只读结果存储 + viewer（`evals.camelai.dev`） |

`app-usage-guard` 值得展开，它是联邦里唯一会「主动动手」的成员。这个 Worker 每 5 分钟查询账户级的 Workers Observability 数据，统计各 app 对 Durable Object SQLite 的读写量；生产与 staging 都已承诺 `enforce` 模式。触发隔离时它不是删数据，而是把该 app 在 dispatcher 里的部署脚本替换成一个生成的 quarantine Worker——这个替身的 `alarm()` 处理器全是空操作，应用从此不再干活，但 DO 命名空间和用户数据原样保留。用户重新部署一次即可解除隔离，并进入 1 小时观察期。设计上还有一条硬要求：dispatcher 注册表的更新是 best-effort，所以隔离决定以 D1 里的权威状态为准，KV 故障不能阻止隔离生效。staging 的隔离演练记录显示，一个每秒自触发的 SQLite 告警计数器在隔离前后都停在 117，哨兵行状态为 `preserved`。机制整体是账户级的用量雷达 + 按 app 粒度的可逆熔断，防的是单个 app 把整个 Cloudflare 账户的费用烧穿。

`bedrock-provider` 是另一个工程上值得关注的小点：camelAI 不是 Bedrock 的客户端，而是在 Cloudflare AI Gateway 上注册了一个自定义 provider（README 仓库结构表的原文是「Anthropic-to-Bedrock AI Gateway provider」），把 Anthropic Messages API 风格的请求翻译到 Bedrock 调用，内置一份带价格与上下文窗口的模型目录。这意味着 BYOK 到 Bedrock 的用户不需要任何客户端代码改动。

## 五、API 路由的双轨制

`AGENTS.md` 里专门有一节写「API routing」，因为 camelAI 的 HTTP 入口有两套并行体系：

| 表面 | 位置 | 用途 |
| --- | --- | --- |
| React Router | `src/routes/api/` | Session cookie 用户 REST（工作区、计费 checkout、上传、聊天组） |
| Worker-native | `workers/main/src/routes/` | WebSocket、Stripe webhook、MCP、data-proxy、大部分 bearer admin REST |

`workers/main/src/index.ts` 在 React Router SSR 之前先抢走一部分路径（比如 `/api/admin/*`）。`AGENTS.md` 明确要求：

> When adding an API, match an existing neighbor; do not invent a third pattern.

这条规范不是因为风格洁癖：两套体系的中间件、错误处理、auth 方式都不同，混写大概率第一个踩中的就是 auth——cookie 会话语义混进 bearer-only 的 admin 路由。

## 六、边界与决策建议

这套架构的边界在哪里？四点最关键。

**第一，自托管用 docker-compose 而不是 Cloudflare 账户**。`SELF_HOSTING.md` 提供了完整 single-machine Docker Compose 目标：`bun run selfhost:init / doctor / up`。但要注意，自托管版**主动放弃**三个能力——outbound email、密码邮箱验证和多节点 failover。README 的原话是「Outbound email and password-email verification are intentionally unavailable, as is multi-node failover」。密码注册会被直接拒绝（验证邮件发不出去），验证邮件重发和邮件工单表单返回显式的不可用错误；组织邀请仍会创建，但管理员得自己把邀请链接通过别的渠道发给对方；agent 的 `send_email` 工具从发现列表里消失并在服务端拒绝。认证走捆绑的 Pomerium（`SELFHOST_AUTH_MODE=bundled-pomerium`，Caddy 做前门，Pomerium 只绑 127.0.0.1），也可以换 `external-pomerium` 或 `cloudflare-access` 接企业已有的代理。这些是单容器目标的事实地基，不是 bug。

**第二，模型层是 BYOK 友好，但 harness 不替换**。底层模型可以从 Anthropic、OpenAI、OpenRouter、Bedrock、自定义端点选——发表时 Bedrock 路径经 Cloudflare AI Gateway 的自定义 provider 打通。但 Agent harness（任务拆分、工具调用、错误恢复、断线重连）是 camelAI 自家代码，模型层换不掉它。

**第三，出网是按沙箱分级的平台决策，不是用户可配项**。构建容器需要 npm registry 出网、分析容器只放行 PyPI、查询容器走静态 IP 中继——这套 posture 是平台在代码里定死的（见 2.4 节），用户侧没有「放行某个域名」的配置面。如果你的工作流依赖一个私有 npm registry 或 PyPI 之外的内网源，发表时的代码路径里没有给用户留开关，选型前要先想清楚。

**第四，不提供 bash 工具**。AGENTS.md 原话「There is no shell/`bash` tool」——不是限制 bash 的权限，是这个工具根本不存在，所有 Agent 动作都走 JS 工具。如果用户的问题本质是「我有一个 bash 脚本需要执行」，camelAI 会要求把脚本用 `analysis_exec` 在 `AnalysisSandbox` 跑，或者重写成 Node 脚本在 Code Mode 跑。这是一个值得在选型时提前告诉用户的能力边界。

### 决策建议

| 场景 | 是否选 camelAI |
| --- | --- |
| 团队在 Cloudflare 生态上做产品，想给用户一个「在浏览器里写代码」的体验 | 是 |
| 想做自托管的 SaaS-like 编码 Agent，但运维资源有限 | 是，配合 docker-compose；接受无邮件、单机 |
| 需要严格审计每一次工具调用的凭证使用 | 是，Code Mode 凭证隔离天然合规 |
| 工作流里深度依赖 bash 命令、复杂 shell 管道、pty 交互 | 谨慎，需评估 `analysis_exec` 是否够用 |
| 需要私有网络部署到客户机房，且要求 outbound email | 否，自托管明确不支持 |
| Agent 需要长时间无人值守连续跑大任务 | 谨慎，先评估单次请求的时长预算与容器生命周期 |

## 七、推荐阅读路径

想动手搭一遍的读者，建议按这个顺序看代码：

1. `workers/main/src/chat-thread-do.ts` 的第 586 行 `export class ChatThreadDO extends AIChatAgent` 起——这是整个 Agent 循环的入口
2. `workers/main/src/chat-thread/pi-tools.ts`——工具定义怎么挂在 Pi 上
3. `workers/main/src/workspace-filesystem-do.ts`——双层文件系统怎么落地
4. `workers/main/src/code-mode-runner.ts` 的 `codeModeWorkerModule`——动态 Worker 编译原理
5. `workers/main/src/code-mode-tools.ts` 的 `create_project / deploy_project`——平台工具的标准实现

跑得通再考虑怎么改。`bun run dev:local-auth` 是最快的本地入口（`http://localhost:3001`），它会 seed 一个 `Local Dev` 用户、组织和工作区，省掉 OAuth 整套流程。

## 八、小结

camelAI 用四层结构回答了一个具体工程问题：能不能把整套 AI 编码平台塞进 Cloudflare Workers 全家桶，不开 VM 也能跑生产。答案是可以，但代价是：

- Agent 写 JS 不写 bash，需要重新训练用户和模型的使用习惯
- 沙箱只承担真 Linux 任务，其余全在 DO 和 isolate 里完成，工具边界要切清楚
- 发布路径绑死在 Workers for Platforms 上，不能跨云分发

这些边界不是设计妥协，是架构本身划出来的。选型时先确认「我愿不愿意让 Agent 写 JS」，再确认「我的负载能不能跑在 Cloudflare 上」，最后确认「我的发布目标是不是 Worker Bundle」。三个都满足，camelAI 是个少见的同时具备「工程透明度」「凭证隔离」「自托管路径」的选项。

## 九、发表之后：这条主线走到哪了

本文正文锚定发表当日的主干。2026-10-04 复核时，主干又合入了 150 多个 PR，有几处变化直接影响上文的结构描述，列在这里供读者对照：

| 上文（2026-07-30，commit `7e259795`） | 现状（2026-10-04，commit `3825a9a6`） |
| --- | --- |
| `chat-thread-do.ts` 7,863 行单文件（另有 `chat-thread/` 目录放 Pi 工具、流重试等 21 个辅助文件） | 主文件瘦身到 316 行；运行时逻辑重组进 `agent-runtime/` 目录（线程 fork、运行时 API、模型路由、转录等 18 个模块），`chat-thread/` 只剩 2 个文件 |
| 浏览器经 WebSocket 连 ChatThreadDO | README 架构图改为 `browser HTTP/SSE` |
| `bedrock-provider/` 独立 Worker（AI Gateway 自定义 provider） | Worker 已移除，Bedrock 适配并入主 Worker（`bedrock-pi-*.ts` 一组文件，直连 `bedrock-mantle.<region>.api.aws` 的 Anthropic 兼容端点）；`workers/` 目录从八个变七个 |
| 四个 `extends Sandbox` 的容器类 | 容器管理重构为 `analysis-container.ts` / `project-build-container.ts` / `db-query-container.ts` 加一套 sizing/placement/mounts 模块，不再整类继承 `Sandbox` |
| `code-mode-runner.ts`（1,385 行）、`code-mode-web-search.ts`（1,518 行） | 两个文件拆除：执行器并入 `code-mode-tools.ts`（已长到 5,388 行）；`web_fetch` / `web_search` 仍在工具面上 |

两条没有变的线值得点名：pi 之上的自研 harness 定位没动（现行 README 原话仍是一句「It is not Claude Code or Codex」），四层职责的划分也原样保留——变的主要是文件怎么组织、Bedrock 走哪个入口。另外自托管线在按自己的节奏发版，最新为 `selfhost-v0.1.18`（2026-08-27）。

想跟进最新演进，有两个一手入口：仓库 [AGENTS.md](https://github.com/qaml-ai/camelAI/blob/main/AGENTS.md)（作者维护的结构地图，本文多处引语即出于此），以及官方博客那篇 [Our coding agent runs in a Cloudflare Durable Object, not a VM](https://camelai.com/blog/our-coding-agent-runs-in-a-cloudflare-durable-object-not-a-vm)——设计取舍的来龙去脉，作者自己写得比任何解读都细。