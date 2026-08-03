---
title: "camelAI：把整个 AI 编码 Agent 塞进 Cloudflare Durable Object 的工程实践"
date: "2026-07-30T22:00:00+08:00"
draft: false
slug: "camelai-cloudflare-durable-object-ai-coding-platform"
github_repo: "qaml-ai/camelAI"
description: "camelAI（qaml-ai/camelAI）把 AI 编码 Agent 的整条执行链——聊天状态、Agent 循环、项目文件系统、Code Mode 工具、构建沙箱——全部压在 Cloudflare Workers + Durable Objects 上，不开 VM 也能跑生产级 Coding Agent。本文拆解 ChatThreadDO、WorkspaceFilesystemDO、Code Mode、Workers for Platforms 联邦这四层结构，给出三个真实任务流的端到端路径，并讨论它在自托管、模型灵活性和沙箱可信度上的边界。"
categories: ["技术笔记"]
tags: ["Cloudflare", "Durable Objects", "AI Agent", "camelAI", "Workers for Platforms", "架构分析"]
---

## 本文导读

读完本文你将能够：

- 说清 camelAI 想解决的问题：把 AI 编码 Agent 从「VM 上的长进程」拆解成「Cloudflare Workers 上的可序列化组件」
- 拆出它的四层结构：ChatThreadDO / WorkspaceFilesystemDO / Code Mode / 沙箱联邦，每一层负责什么、不负责什么
- 跟着三个具体任务走通整个系统：建项目并部署、运行一个 notebook 分析、把外部 Slack 数据接进应用
- 看清 Workers for Platforms 联邦里 dispatcher / app-usage-guard / discord-bridge / bedrock-provider 各承担什么职责
- 评估它在自托管、模型灵活性和沙箱可信度上的真实边界，知道什么时候该用、什么时候不该用

## 一、判断先行：camelAI 不是「又一个 Claude Code」

camelAI（仓库 [qaml-ai/camelAI](https://github.com/qaml-ai/camelAI)，公开域名 [camelai.com](https://camelai.com)）给出的答案不是「更好的 prompt 或更强的模型」，而是把整套 AI 编码平台拆成四个可在 Cloudflare Workers 上独立伸缩的层。这套拆法的关键事实有三条：

第一，每个聊天线程对应一个 `ChatThreadDO`。Agent 的循环、消息历史、运行态全在 Durable Object 里——而不是一台 VM。这件事直接消灭了「会话断了 Agent 进程没了」这个传统编码 Agent 最头疼的故障。

第二，Agent 写 JavaScript，不写 bash。Code Mode 把用户生成的 JS 包成独立 Worker 在 V8 isolate 里跑，凭证留在 isolate 外面。这是它和 Claude Code、Codex 这类以 shell 命令为底座的 Agent 在实现哲学上的分水岭。

第三，发布路径走 Cloudflare 自家的 Workers for Platforms。用户写完的应用不是「部署到 K8s」「部署到 VM」，是直接编译成 Worker Bundle 推到 dispatcher 命名空间，DNS 一指就到 `*.camelai.app`。

如果只把 camelAI 看作一个 AI 编码助手的开源实现，会低估它的工程价值。它的真正贡献，是给「在 Cloudflare 全家桶上能不能跑生产级 AI 平台」这个问题写了一整套工程答卷。

## 二、四层结构总览

下面这张图来自仓库 `README.md` 的架构章节，它不是装饰，而是这四层各自边界的官方描述：

```
React Router SSR + browser WebSocket
                  |
                  v
       Cloudflare main Worker
                  |
                  v
       ChatThreadDO（coding agent）
       自研 harness，基于 pi
                  |
       +----------+-----------+----------------+
       |          |           |                |
       v          v           v                v
Code Mode    WorkspaceFS    Cloudflare 沙箱     Workers for
Dynamic      DO             容器               Platforms
Worker /     SQLite +       构建 / 分析 /       dispatcher
V8 isolate   R2 文件        SQL                ->
                                                  Live app
```

四层之间的依赖关系是单向的：上层调用下层提供的 RPC，下层不知道上层存在。这种切法让每一层都能独立替换——比如换掉 Code Mode 不会影响文件系统，换掉 WorkspaceFS 不会影响沙箱。

### 2.1 ChatThreadDO：Agent 循环住在 Durable Object 里

`workers/main/src/chat-thread-do.ts` 整个文件 7848 行，是整个平台的心脏。它的关键设计有四点：

**继承自 Cloudflare 官方 `AIChatAgent`**（`@cloudflare/ai-chat`），而不是自己造流式传输。`AIChatAgent` 已经把 SQLite chunk 缓冲、断线重连、消息持久化做完了，camelAI 在这之上做的是把 Agent 循环接进去。仓库注释里写得很清楚：

> Extends AIChatAgent for its resumable-stream transport (SQLite chunk buffering + replay on reconnect) and, later, chatRecovery. The ai-chat message model is transport-internal only: pi_core_messages remains the canonical history and the Pi runtime owns the agent loop.

换句话说：传输层用 AIChatAgent，事实层用 pi 的 core messages。两层职责切清楚，AIChatAgent 那一层将来要换也能换。

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

**每个方法对状态的影响都在 DO 实例字段上可见**。`piSessionPromise`、`piSession`、`piActiveItemId`、`piAssistantText`、`streamingLeaseRefreshTimer` 这类字段按设计在源码里就暴露出来，目的是让 unit test 用 `Object.create(ChatThreadDO.prototype)` 这样的 fake seam 直接覆盖某一字段，而不用构造完整的 DO 实例。`workers/main/tests/` 下面有 18 个 `chat-thread-*.test.ts`，全是这种 seam 风格的测试。

### 2.2 WorkspaceFilesystemDO：SQLite + R2 双层文件系统

`workers/main/src/workspace-filesystem-do.ts` 是项目文件存储 DO，1860 行。它的存储分层是 Cloudflare 生态里典型的「小文件进 SQLite / 大文件进 R2」结构，关键代码片段：

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

每次 `js_exec` 调用都会编译出一份新 Worker，所以每次都是「干净的 V8 isolate」，没有跨调用的状态泄漏。

凭证隔离是这套设计的核心。模型能拿到的是 `env.PROJECTS`、`tools.deploy_project(...)`、`connections[alias]` 这样的平台和连接句柄，但拿不到 `connection.credentials` 本身。仓库里有专门的 `code-mode-integrations.ts`（589 行）维护连接发现和注入逻辑，避免把密钥塞到模型上下文里。

工具集规模可观：`code-mode-tools.ts` 4632 行，按类别分文件：

| 文件 | 工具类别 | 行数 |
| --- | --- | --- |
| `code-mode-runner.ts` | 执行器（sucrase + Worker 编译） | 1385 |
| `code-mode-tools.ts` | 主工具集 | 4632 |
| `code-mode-web-search.ts` | 网络搜索 / 抓取 | 1518 |
| `code-mode-integrations.ts` | 外部连接发现与注入 | 589 |
| `code-mode-custom-domains.ts` | 自定义域名 | 325 |
| `code-mode-deterministic-automations.ts` | 定时任务 | 235 |
| `code-mode-scheduled-prompts.ts` | 定时 prompt | 130 |

### 2.4 Cloudflare 沙箱联邦：只做 Linux 才能干的事

Agent 大部分时间住在 DO + V8 isolate 里，但有些活必须有真 Linux——npm install、构建、Jupyter notebook、SQL 查询。camelAI 把这些活显式收拢到三个 Sandbox 类，全部继承自官方 `@cloudflare/sandbox`：

```ts
import { Sandbox } from "@cloudflare/sandbox";

export class ProjectBuildSandbox extends Sandbox<Env> {}
export class AnalysisSandbox extends Sandbox<Env> {}
export class DbQuerySandbox extends Sandbox<Env> {}
```

三个沙箱各管一摊事：

| 沙箱 | 职责 | 触发工具 |
| --- | --- | --- |
| `ProjectBuildSandbox` | 每个 org 一份 warm 容器，专门跑 `npm install` / `vite build` 等需要 npm registry 出网的构建命令 | `tools.deploy_project`, `tools.add_dependency` |
| `AnalysisSandbox` | 每个 workspace 一份，跑 Jupyter notebook 与 `analysis_exec` shell | `tools.run_notebook`, `tools.analysis_exec` |
| `DbQuerySandbox` | 跑 SQL 查询与数据仓库导出；DATA_PROXY binding 在 worker 侧服务 | `tools.run_sql` 类操作 |

仓库 `AGENTS.md` 明确指出历史包袱已退出：

> The Go data-proxy (external `qaml-ai/project-runtime-service` `cmd/data-proxy`) is retired: SQL queries and warehouse exports now run in the `DbQuerySandbox` Cloudflare container.

这条信息很关键：之前的 `PROJECT_RUNTIME_HOST` VM 桥接已被替换，整个体系不再依赖外部 Go 服务，自托管时只需要 Cloudflare 单账户资源。

## 三、三个任务流走通整个系统

光看四层抽象还不够。下面是三个真实任务从用户输入到结果的端到端路径，每一步对应到上面的层级。

### 3.1 任务流 A：从空白工作区创建一个可部署的应用

1. **用户在浏览器发消息**：「帮我做一个待办清单应用，用 SQLite 存数据」。
2. **React Router 路由**（`src/routes/api/`）收到消息，转发到 main Worker 的 WebSocket 入口。
3. **WebSocket 命中** `ChatThreadDO` 实例（按 `threadId` 寻址）。Agent 循环开始——首次创建前必须 `read_skill({ skill: "developing-software" })`，这是 `pi-system-prompt.ts` 里的硬约束。
4. **Agent 调 `create_project`**：根据 system prompt 选择 `crud` 模板（默认），seed 出完整 React Router + Durable Object SQLite CRUD 脚手架。`create_project` 返回 project id 与 backend 标记 `do-r2`。
5. **Agent 改文件**：在 `js_exec` 里用 `await tools.add_shadcn_component(...)` 加按钮和列表组件，文件位置全部走 `location: "project"`。
6. **Agent 调 `deploy_project`**：这条调用会触发 `ProjectBuildSandbox` 拉镜像、`npm install`、`vite build`、把产物编译成 Worker Bundle 推到 dispatcher 命名空间。成功后返回 `live URL` 并自动 `set_preview`。
7. **用户在浏览器看到应用**：`*.camelai.app` 子域名指向 dispatcher Worker，dispatcher 把请求路由到对应的 user app worker bundle。

整个链路里，Agent 调的是平台工具，不是 bash。Sandbox 只承担 build 这一段，其余都在 DO 和 isolate 里完成。

### 3.2 任务流 B：跑一个数据探索 notebook 并发布为报告

1. **用户**：「读 `uploads/sales.csv`，做一个区域销售额的柱状图，然后发我链接。」
2. **Agent 调 `create_project`（template: `data-analysis`）**，seed 出 `analysis.ipynb`。
3. **Agent 调 `add_dependency`**：通常 pandas、altair 已预装，不需要额外加。
4. **Agent 调 `run_notebook`**：执行 `jupyter nbconvert --execute --inplace`，输出写回 project，验证 `validation.clean`，成功后自动 `set_preview` 打开 notebook。
5. **Agent 调 `deploy_project({ publish_intent: "user_requested" })`**：把执行完的 notebook 编译成静态报告 app 发布到 dispatcher。
6. **用户拿到链接**：报告 app 是只读静态站点，不需要持续服务。

注意 `publish_intent: "user_requested"` 是显式门槛——`data-analysis` 模板的 notebook 默认不发布，必须用户明确请求。这是为了避免 Agent 在用户没要求时自动公开报告。

### 3.3 任务流 C：把 Slack 数据接进应用

1. **用户在组织设置里连接 Slack**：OAuth 完成后，凭证存在 OrgDO 里（`workers/main/src/identity/`）。
2. **Agent 在 js_exec 里引用** `connections["slack"]`：拿到的是平台层句柄，不是原始 token。`code-mode-integrations.ts` 负责发现和注入。
3. **Agent 写业务代码**：

```js
const channels = await connections.slack.listChannels();
const messages = await connections.slack.listMessages({
  channel: channels[0].id,
  since: "2026-07-01",
});
return messages.map(m => ({ user: m.user, text: m.text }));
```

4. **Agent 把数据塞进 app**：通过 file tools 写到 project 文件，触发 `deploy_project`。

关键在于第 2 步：Agent 全程拿不到 `xoxb-` 开头的 Slack token。Token 留在 worker 侧，调用通过绑定方法路由。这就是 Code Mode 在安全模型上的核心承诺。

## 四、Workers for Platforms 联邦

camelAI 不只一个 Worker。`workers/` 下面有七个独立的 Worker：

| Worker | 职责 |
| --- | --- |
| `main/` | 主入口：WebSocket、API、MCP、admin、Stripe webhook |
| `dispatcher/` | Workers for Platforms dispatcher，路由已发布的 user app |
| `app-usage-guard/` | 账户级 Durable Object SQLite 用量监控，可逆隔离异常 app |
| `bedrock-provider/` | 自定义 AI Gateway provider，把 Anthropic 风格请求翻译到 Bedrock |
| `discord-bridge/` | Discord Gateway 长连接 + 控制 worker |
| `e2e-reports/` | 公开 viewer，托管 Playwright E2E 报告（`e2e-reports.camelai.dev`） |
| `eval-reports/` | 公开 viewer，托管 agent eval 结果（`evals.camelai.dev`） |

`app-usage-guard` 的设计文档在 `docs/deployed-app-usage-guard-design.md`，逻辑是「账户内任一 app 触发配额阈值就把整个账户的应用列入可逆隔离名单」。这避免了单个用户把整个 Cloudflare 账户的费用烧光。

`bedrock-provider` 是另一个工程上值得关注的小点：camelAI 不是 Bedrock 的客户端，而是在 Cloudflare AI Gateway 上注册了一个自定义 provider，把 Anthropic Messages API 风格的请求翻译到 Bedrock 调用。这意味着 BYOK 到 Bedrock 的用户不需要任何客户端代码改动。

## 五、API 路由的双轨制

`AGENTS.md` 里专门有一节写「API routing」，因为 camelAI 的 HTTP 入口有两套并行体系：

| 表面 | 位置 | 用途 |
| --- | --- | --- |
| React Router | `src/routes/api/` | Session cookie 用户 REST（工作区、计费 checkout、上传、聊天组） |
| Worker-native | `workers/main/src/routes/` | WebSocket、Stripe webhook、MCP、data-proxy、大部分 bearer admin REST |

`workers/main/src/index.ts` 在 React Router SSR 之前先抢走一部分路径（比如 `/api/admin/*`）。`AGENTS.md` 明确要求：

> When adding an API, match an existing neighbor; do not invent a third pattern.

这条规范不是因为风格洁癖，而是因为两套体系的中间件、错误处理、auth 方式都不同，混在一起会让 cookie 泄露到 bearer-only 的 admin 路由上。

## 六、边界与决策建议

这套架构的边界在哪里？四点最关键。

**第一，自托管用 docker-compose 而不是 Cloudflare 账户**。`SELF_HOSTING.md` 提供了完整 single-machine Docker Compose 目标：`bun run selfhost:init / doctor / up`。但要注意，自托管版**主动放弃**两个能力——outbound email 和密码邮箱验证；多节点 failover 也不支持。这是单容器目标的事实地基，不是 bug。

**第二，模型层是 BYOK 友好，但 harness 不替换**。底层模型可以从 Anthropic、OpenAI、OpenRouter、Bedrock、自定义端点选——camelAI 通过 Cloudflare AI Gateway + 自定义 Bedrock provider 把这条路径打通。但 Agent harness（任务拆分、工具调用、错误恢复、断线重连）是 camelAI 自家代码，模型层换不掉它。

**第三，沙箱可信度依赖 Cloudflare 平台**。`ProjectBuildSandbox` 在 `npm install` 阶段要访问 npm registry。这是平台能力，不是用户态能力。如果用户的工作区需要访问私有 npm registry，必须通过 `egress` 配置显式放行，不能假设「装包一定成功」。

**第四，不在沙箱里跑 bash**。这条路是显式选择——bash 工具被显式拒绝，所有 Agent 动作都走 JS 工具。这意味着如果用户的问题本质是「我有一个 bash 脚本需要执行」，camelAI 会要求把脚本用 `analysis_exec` 在 `AnalysisSandbox` 跑，或者重写成 Node 脚本在 Code Mode 跑。这是一个值得在选型时提前告诉用户的能力边界。

### 决策建议

| 场景 | 是否选 camelAI |
| --- | --- |
| 团队在 Cloudflare 生态上做产品，想给用户一个「在浏览器里写代码」的体验 | 是 |
| 想做自托管的 SaaS-like 编码 Agent，但运维资源有限 | 是，配合 docker-compose |
| 需要严格审计每一次工具调用的凭证使用 | 是，Code Mode 凭证隔离天然合规 |
| 工作流里深度依赖 bash 命令、复杂 shell 管道、pty 交互 | 谨慎，需评估 `analysis_exec` 是否够用 |
| 需要私有网络部署到客户机房，且要求 outbound email | 否，自托管明确不支持 |
| Agent 需要长时间后台运行（>30 分钟一气呵成） | 谨慎，需要查 Durable Object 唤醒预算与 wal 时长上限 |

## 七、推荐阅读路径

想动手搭一遍的读者，建议按这个顺序看代码：

1. `workers/main/src/chat-thread-do.ts` 的第 587 行 `export class ChatThreadDO extends AIChatAgent` 起——这是整个 Agent 循环的入口
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