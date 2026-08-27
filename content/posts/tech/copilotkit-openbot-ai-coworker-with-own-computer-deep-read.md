---
title: "CopilotKit/OpenBot：当 AI agent 终于有了「自己的电脑」，治理网关才是真正的工程难题"
date: 2026-08-27T18:03:00+08:00
draft: false
tags: ["CopilotKit", "OpenBot", "AG-UI", "Agent Governance", "Browser Automation", "MCP", "CEL Policy", "Audit Trail", "AI Coworker"]
categories: ["技术笔记"]
description: "CopilotKit 在 2026-08 上线 OpenBot——一个让 AI agent 各拿一台独立浏览器+工作区+登录态、用统一网关治理所有 tool call、把审计日志写进 PostgreSQL 的开源 AI coworker 平台。本文深度解析：3.1k stars / MIT / 2026-08 发布 / 14 个子项目 / 0.2.0 之前的 alpha 版本。它的真正贡献不是「让 agent 拿浏览器」——这件事 Browser Use、Open Operator 早做过了——而是把「agent 能拿到工具」和「agent 值得被信任使用工具」之间那道工程鸿沟，用三层架构（target 解析 → CEL policy → audit row）填平。"
slug: copilotkit-openbot-ai-coworker-with-own-computer-deep-read
github_repo: "CopilotKit/OpenBot"
source_key: "gh:CopilotKit/OpenBot"
---

# CopilotKit/OpenBot：当 AI agent 终于有了「自己的电脑」，治理网关才是真正的工程难题

`CopilotKit/OpenBot` 是 2026-08-17 在 GitHub 上线的开源项目，2026-08-27 已积累 3097 stars / 377 forks / MIT / 22.6KB README + 15KB architecture 文档 + 111KB CHANGELOG，主语言 TypeScript。当前状态仍是 **Alpha**——README 顶部明确写着「early, expect rough edges」。

但工程结构非常扎实：14 个子项目（app / server / shared / supervisor / agent-computer / agent-bot / agent-langgraph / worker / charts / docker / docs / examples / spire / scripts）、Bun + Hono + React + Vite + Drizzle ORM + PostgreSQL（带 pgvector）技术栈、单条 `docker build` 命令把整个平台跑起来。

一句话定位：

> **Not "agent with a browser". A coworker with its own computer, behind one gateway that decides and records everything.** OpenBot 的核心创新不在于给 AI agent 一个浏览器——这件事 Browser Use、Open Operator、Anthropic Computer Use 早在 2024-2025 年就做过了。OpenBot 的真正贡献是**承认了一件事**：agent 能拿到工具 ≠ agent 值得被信任使用工具。它用三层架构（target 解析 → CEL 策略评估 → 审计行写入）把这两件事中间那道工程鸿沟填平，并把整条治理管线塞进 43KB 的 `gateway.ts` + 17KB 的 `sandbox.ts` 里。

读完 README + 7 份 docs（README/architecture/configuration/coworkers/deployment/development/releasing）+ 11 份核心源码（gateway/policy/sandbox/target/routes/snapshot-store/server/app/supervisor/agent-computer index）后，四条工程判断如下：

1. **AG-UI 协议的「框架无关」不是营销话术**——任何 AG-UI 端点都是 Bot，包括 LangGraph / Mastra / CrewAI / Pydantic AI / Google ADK 写的，治理跑在协议层而不是框架层。
2. **per-Bot 独立浏览器容器 + 治理网关**是 OpenBot 的真发明——「每 Bot 一台 Chromium + 自己的登录态 + 自己的 /workspace」，supervisor 按需启停，所有 tool call 走唯一网关。
3. **Fail-closed 语义**贯穿全栈——空策略允许 0 / 坏 deny 拒绝 / 坏 allow 不允许 / 私有地址默认拒绝 / 凭据加密后永不返回 API / 审计行 redact 凭据内容。
4. **人机协作的事件级审计**（`computer.help_requested` / `control_taken` / `control_released`）+ 「人在时 Bot 行动被拒绝而不是排队」——这种细节暴露了它是从真实企业场景长出来的。

下面分十节展开这四条。

---

## 一、问题域——「agent 能用工具」之后，下一道题是什么

2024 年的 AI agent 主流叙事是「让模型能操作浏览器」。Browser Use、Anthropic Computer Use、OpenAI Operator 都用同一套思路：让 LLM 看截图、决定点哪里、敲键盘。

这套思路有两个**没有解决但被忽略**的工程难题：

- **登录态怎么管**。你的 Gmail、你的银行后台、你的企业内部系统都需要登录。Agent 怎么登录？三种选择都不优雅：共享人类登录态（高危）、每次弹 2FA（破坏 agent 自主性）、给 agent 单独账号（成本 + 管理开销）。
- **怎么知道 agent 在干什么**。agent 操作浏览器时，人类看不到它在做什么，只能事后看日志。但事后日志不够——agent 可能已经在错误的页面上提交了表单、点错了删除按钮、误发了邮件。
- **agent 出错时谁负责**。LLM 幻觉 + 高风险操作（医疗、金融、运营）= 责任真空。

OpenBot 的回答是：**给每个 agent 一台自己的电脑 + 一个唯一的治理网关 + 一份不可篡改的审计日志**。这不是「让 agent 能用工具」的优化版，而是把 agent 从「一个 LLM 在你电脑里乱点」变成「一个经过审计、可以担责的同事」。

---

## 二、AG-UI 协议——为什么「框架无关」是 OpenBot 能成立的前提

OpenBot 建在 AG-UI（[ag-ui-protocol/ag-ui](https://github.com/ag-ui-protocol/ag-ui)）之上。这是它的第一性原理选择：治理跑在协议层而不是框架层。

协议层治理的好处用一句话说清楚：**今天用 LangGraph 写的 agent，明天换成 CrewAI，今天的所有治理规则、审计行、policy 仍然有效**。

`docs/architecture.md` 把这写成「Governance rides the protocol rather than the framework」——治理在协议层而不是框架层。后果是：

- Bot 是任何 AG-UI 端点（`remote-ag-ui` 模式）或纯 system prompt（`built-in` 模式）
- 端点校验用浏览器导航时同一套 target check（`AGENT_ENDPOINT_ALLOWED_HOSTS`）
- 授权 header 是 write-only 存的
- 私网地址默认拒绝（必须显式列白名单）

这套设计对 2026 年的 agent 生态是**结构性正确**的判断——单框架（Lanchain 一家独大 / LangGraph 自成体系）的时代过去了，跨框架互操作是必然趋势，而治理必须能跨框架。OpenBot 把治理做在协议层，等于一次性买断未来 5 年所有 agent 框架的入场券。

---

## 三、核心机制 1——per-Bot 独立浏览器容器：supervisor + agent-computer

OpenBot 真正的工程创新是「**每 Bot 一台电脑**」，由 supervisor 子项目编排。

`supervisor/src/docker.ts`（22KB）做的事：

1. 监听 server 的 ensure/stop/reset/list 调用
2. 每个 Bot 创建一个独立 Docker 容器，挂载独立 `/workspace` 卷，用独立 Chromium profile
3. 容器绑 127.0.0.1 + per-container `COMPUTER_TOKEN`（任何请求必须带 token）
4. 容器之间的网络严格隔离——数据库在另一个 `data` 网络，Bot 容器碰不到 PostgreSQL

`agent-computer/src/index.ts`（46KB）做的事：

- 跑一个 Chromium（带可选 sandbox / gVisor `COMPUTER_RUNTIME=runsc`）
- 暴露浏览器 snapshot、aria-snapshot（accessibility tree）、screencast（实时屏幕流）、file/workspace tools
- shell 命令继承 PATH + locale + proxy 变量，但**不继承部署环境的其他变量**（一个明确的最小环境面）
- proxy URL 自动剥离 userinfo（防止密码泄露）

人机协作的事件级审计写在 `agent-computer/src/control.ts`（9KB）：

```text
computer.help_requested    → agent 撞登录墙 / 2FA 时主动求助
computer.control_taken     → 人类接过控制
computer.control_released  → 人类交还控制
```

**关键安全语义**：当人类在控制浏览器时，Bot 的所有行动被「**拒绝**」而不是「排队」。这个细节非常重要——排队意味着 Bot 行动会以不可预测的顺序在人类操作后执行，拒绝意味着 Bot 在人类操作期间完全是 frozen 状态。

这套 per-Bot computer + event-level handoff 的设计，本质是把 Kubernetes pod 的隔离模型应用到 AI agent 领域——**每个 agent 是一个有自己计算环境、有自己身份、有自己审计的独立单元**。这是 OpenBot 区别于「让 agent 操作你电脑里那个浏览器」的根本差别。

---

## 四、核心机制 2——治理网关（43KB 的 gateway.ts + 25KB 的 audit.ts）

`server/src/computer/gateway.ts`（43KB，仓库最大单一文件之一）是 OpenBot 治理的核心。**任何**浏览器操作、文件操作、MCP 调用都必须经过它。gateway 的 5 步流水线（来自 docs/architecture.md）是它全部的设计哲学：

```text
1. resolve the target     → 从 server-held snapshot 或请求主体解析目标
2. evaluate policy        → 用当前 action policy 评估
3. write audit row        → 立刻写一行审计
4. call computer (if pass) → 通过才调计算机
5. write second audit row → forwarded action 失败再写一行
```

这套流水线三个关键设计：

### 4.1 Audit 写在 call 之前

文档原文：

> There is no path that acts without the record existing first.

这是 OpenBot 最核心的安全声明——**任何行动发生之前，审计行必须先存在**。换句话说，如果你看到一条 audit 行「action_permitted」，那一定有一次相应的真实行动；如果你看到一次真实行动，audit 里一定有一条对应的「action_permitted」+ 可能一条「action_failed」。这条不变量让审计行可以**作为 ground truth** 用于事后追责。

### 4.2 Fail-closed policy 引擎

`server/src/computer/policy.ts`（15KB）的语义直接抄文档：

```text
- A missing or empty policy permits nothing
- A broken deny rule denies
- A broken allow rule does not permit
- Shipped startup default is explicit: deny: [] and allow: ["true"]
- A malformed configured policy stops server startup
```

这是 fail-closed 的极致——任何「我不确定」的状态都拒绝行动。后果是 OpenBot 出厂默认拒所有行动，管理员必须**显式**配置 allow 规则才能放行。这条设计非常重要：它把「默认安全」作为系统基本不变量，而不是事后的合规配置。

policy 用 CEL（Common Expression Language）写，可以检查的字段列在 docs/architecture.md：

```text
tool.name | intent | bot.id | actor.id
page.url | page.host
element.ref | element.role | element.name | element.type
key
file.path | file.name | file.extension
mcp.server | mcp.tool | mcp.effect
```

这套字段覆盖了「agent 想要做什么 + 在哪个上下文 + 是哪个 Bot 哪个 actor + 目标是哪个 URL/元素/文件/MCP」全栈。比很多企业 IAM 系统还细。

### 4.3 Target check（12KB 的 target.ts）—— 私有地址默认拒绝

`server/src/computer/target.ts`（12KB）做的事听起来简单但很关键：浏览器要导航的 URL 必须经过 target check，**任何私有 IP 段默认拒绝**（除非 `AGENT_COMPUTER_ALLOW_PRIVATE_HOSTS=true`，但这条 `NODE_ENV=production` 直接拒启动）。

这是云上 agent 的头号安全漏洞——AWS / GCP metadata endpoint 是 `169.254.169.254`，agent 如果能访问就能拿到临时凭据；内网服务是 `10.0.0.0/8`、`192.168.0.0/16`、`127.0.0.0/8`。OpenBot 默认全部拒绝，强制管理员显式列白名单。

仓库注释里直接写：「cloud metadata addresses are refused under every configuration」。这是 OpenBot 设计哲学的缩影——**默认安全，把 enable 当作显式选择**。

---

## 五、核心机制 3——审计行（25KB 的 audit.ts）

`server/src/audit.ts`（25KB）是 OpenBot 的「黑匣子」。设计要点：

- **所有治理事件都写审计**：tool call、文件读写、登录、权限变更、agent endpoint 变更、policy 变更、控制权交接
- **凭据 redact**：secret 永远不写入 audit，只记录「请求了凭据，N 字符」
- **可读**：邮箱写在审计行（不止 user id），一年后回查的人也能读懂
- **可查询**：URL 参数 + Drizzle schema，审计有专门的 `/admin/audit` 页面 + 30 天 retention（`audit-retention.ts`）

`server/src/audit-retention.ts`（6KB）实现「30 天后审计自动清理」的合规策略——这在医疗、金融、GDPR 场景里是硬要求。

最关键的一点：审计行 schema 把 **「决策的规则」**也写进去（`/admin/audit` 上每条拒绝都标「规则 X」）。这意味着：

```text
事件 actor: user_42
事件 bot: bot_risk_analyst_v3
事件 tool: browser.navigate
事件 target: https://docs.google.com/document/d/X
事件 decision: refused
事件 rule: deny_policy_rule_3 ("deny *.google.com outside allowlist")
```

事后追责时，受害方可以精确知道「**谁、哪个 Bot、想做什么、在哪个目标、被哪条规则挡下来**」。这不是简单的日志，是**可读、可追责、可作为法律证据的治理轨迹**。

---

## 六、核心机制 4——凭据流与 secret 隔离

OpenBot 处理凭据的细节是它工程深度的另一个缩影：

- **录入端**：`/admin/credentials` 是 write-only 界面，存进数据库时用 `KEY_ENCRYPTION_KEY` 加密
- **使用端**：API **永远不返回明文凭据**——任何 GET 凭据的端点都返回密文或 redact 后的引用
- **审计端**：audit 行 redact 凭据内容，只记录「凭据被请求了，N 字符」
- **生命周期端**：`KEY_ENCRYPTION_KEY` 必须是 32 字节 base64，example key 在 `NODE_ENV=production` 下被拒启动

这一套对应到企业安全合规标准（PCI DSS、HIPAA、SOC 2）是直接可用的——OpenBot 在凭据流上的设计已经达到了企业 IAM 系统的水平，远超一般开源 agent 工具。

更细的：OAuth access / refresh token 用 Better Auth 自带加密，keyed on `BETTER_AUTH_SECRET`；SAML signing material 用 OpenBot 自己的 wrapper（因为 Better Auth 插件默认存明文 JSON）。这些细节是**真的做过企业集成的人**才会写出来的。

---

## 七、核心机制 5——人机协作 + 实时观测

OpenBot 把「人类监控 agent」当作一等公民设计：

- **实时屏幕**：Bot 看的页面通过 websocket 实时流给人类（`agent-computer/src/screencast.ts` 17KB）
- **Activity tab**：Bot 跑过的命令、读过的文件、退出码，按时间倒序，**最新在前**（这是产品细节，但很重要——人看 activity 时关心的是「最近发生了什么」）
- **文件查看只显示路径和大小**：绝不显示文件内容（agent 可能保存了用户给的机密）
- **控制权交接**：四步事件 `help_requested → control_taken → control_released`，审计行 + UI 状态机
- **人在时 Bot 拒绝**：人类控制期间 Bot 行动被拒绝而不是排队

这套「人在 loop」的工程实现，几乎是**目前开源 agent 工具里最完整的**——把 Lucid AI、Harvey、Cohere 等商业 agent 平台的人机协作机制用 MIT 协议开源出来了。

---

## 八、核心机制 6——Skills 缩窄 + 治理三维

OpenBot 的「让 agent 只看到该看到的工具」是另一个细节亮点（docs/architecture.md 的「Which tools a run is offered」一节）。

```text
- LLM 选对工具的能力：~10 个稳定，~30 个不可靠
- 连接两个 vendor 下午就过 10 个工具
- 一旦 Bot 持有太多工具，每次 run 只 offer 匹配 message 的 skills 声明的工具
```

实现：
1. 每条 message 进来，OpenBot 先问自己的 model：「这条 message 匹配哪些 skill？」
2. Bot 用这些 skill 声明的工具 + 所有 granted 但没 skill 声明的工具
3. **声明不等于授权**——声明 + 现有 grant 取交集，不可能通过 skill 越权

这套「narrow the offer, not the boundary」的设计哲学很值得展开：

- **缩窄 offer**（减少 LLM 看到的工具数）= 提高 LLM 选对工具的概率
- **不缩窄 boundary**（policy/audit/grant 仍然管全部行动）= 安全语义不变
- **失败开放**（无法 narrow 时给全工具）= 不因为 narrow 失败就 silently 降权

文档原文：

> This narrows the offer. It is not a boundary, and it never substitutes for one. The grant, the policy and the audit row decide what may happen; this decides only what the model can see. Every way it can fail — no skills declared, a model that cannot answer, a message that matches nothing, twelve tools or fewer — leaves the whole catalogue offered, because a narrowing that failed closed would remove capability an administrator granted, silently.

这是一段极有分量的设计哲学注释——**把「失败安全」和「失败有据」分开**：narrow 失败是 narrow 自己的事，不应该让 grant 已经给了的能力消失。

---

## 九、社区与生态——CopilotKit 的纵深

CopilotKit 不是从石头里蹦出来的——它是 [CopilotKit 商业平台](https://www.copilotkit.ai) 的开源核心层，配套托管的 CopilotKit Intelligence 项目（线程持久化、记忆、实时网关）。这意味着：

- **商业版本可用**：不想自建的用户可以付费用 CopilotKit Intelligence 的托管服务
- **开源核心可自托管**：完整代码 MIT，所有基础设施（PostgreSQL、Bots、Computers、Supervisor）都在 Docker Compose 里
- **AG-UI 生态绑定**：CopilotKit 是 AG-UI 协议的主要维护者，OpenBot 跑在 AG-UI 上等于绑定了 CopilotKit 的协议生态

**生态布局**：
- **三个 example 同事**：General Assistant / Knowledge / Risk Analyst（前者日常 / 第二者企业知识问答 / 第三者金融风控）
- **Tenant package**：`agents.yaml` / `channels.yaml` / `brand.yaml` / `knowledge.yaml` 五件套，企业部署时按这个模板改
- **MCP catalogue**：Google Drive + Notion 已经 ship，其他 vendor 必须经过 review
- **SaaS SPIRE**：compose 里预留了 SPIRE（零信任 workload identity）服务入口，未来可能支持零信任网络

**对照参考**：
- **vs Browser Use / Open Operator / Anthropic Computer Use**：它们都是「一个 LLM 看你浏览器」的工具，OpenBot 是「一个有治理的 AI coworker 平台」
- **vs LangChain / LlamaIndex / CrewAI**：它们都是 agent 框架，OpenBot 是 agent 运行时——框架不同层
- **vs Portia / Fixpoint / Skyfire**：合规 agent 平台也类似定位，但 OpenBot 是 MIT + 自托管 + 完整源码

---

## 十、采用顺序与边界——谁该先用，谁可以等等

### 10.1 该先上

**做企业 SaaS / 内部 agent 平台 / 需要合规审计的团队**：
- 已经有 LangGraph/CrewAI/Mastra 写的 agent 想加上治理层
- 需要让 agent 操作 Gmail / Notion / Google Drive / 内部系统，但又不敢直接给 LLM 登录态
- 需要 SOC 2 / HIPAA / GDPR 合规审计证据
- 接受 OpenBot 还 Alpha，「早期使用换深度参与」是值得的交易

**做 agent infra / 平台工程师**：
- OpenBot 的 gateway / policy / audit / supervisor 设计是**教学级**的工程——43KB 的 gateway.ts 配 17KB 的 sandbox.ts 配 15KB 的 policy.ts，比大多数商业平台的代码更清晰
- 这套架构可以借鉴到任何 agent runtime，不限于浏览器场景

**做 AG-UI 协议生态的开发者**：
- OpenBot 是 AG-UI 在治理层的 reference implementation
- 想让 AG-UI 有「合规 + 企业级」背书，OpenBot 是关键项目

### 10.2 可以等等

**只想要一个 Claude Computer Use 的开源替代**：
- Browser Use 比 OpenBot 轻得多，5 行代码就能跑起来
- 你不需要治理的时候，OpenBot 是 over-engineering

**只想要 MCP client / skill registry**：
- OpenBot 的 MCP 治理很好，但你不需要整套 stack
- 看它的 `server/src/plugins/` 子目录就够了

**只想要一个 agent 框架**：
- 你要的是 LangGraph / CrewAI，不是 OpenBot
- OpenBot 是运行时，框架选 LangGraph，两者不冲突

### 10.3 上手顺序

1. **跑通 `scripts/start.sh`**：`cp .env.example .env` → 填 `OPENAI_API_KEY` + `INTELLIGENCE_API_KEY` → `bash scripts/start.sh` → 打开 `http://localhost:3010`
2. **从 single user 模式开始**：`OPENBOT_SINGLE_USER=true` 不需要 OAuth，5 分钟进产品
3. **接 CopilotKit Intelligence**：`npx copilotkit login` → `project select` → 拿 `cpk-...` runtime key
4. **加 OAuth provider**：删掉 `OPENBOT_SINGLE_USER` → 配 Google / Microsoft / Okta / 自家 SAML → 配置 `INITIAL_ADMIN_EMAILS`
5. **加 coworker**：从 `/agents` 创建第一个 Bot，给一个 standing role
6. **配 policy**：从 `/admin/boundaries` 配 deny 规则 → 试一次浏览器 action 看 audit row 怎么写
7. **上生产**：`/admin/people` 管权限、`/admin/audit` 看决策、`/admin/credentials` 存加密凭据、`NODE_ENV=production` 强制 fail-closed

### 10.4 必看边界

- **Alpha 状态**：README 顶部明确写「early, expect rough edges」，**生产部署需要准备好降级到 Browser Use 的方案**
- **依赖 CopilotKit Intelligence**：threads 和 memory 在外部服务，免费层有限额，**自托管需要付 Intelligence 的部署成本**
- **agent-computer 必须绑 127.0.0.1**：暴露到 0.0.0.0 会让任何能访问 host:4100 的人都拿到 Bot 控制权（虽然有 COMPUTER_TOKEN 兜底，但这是 defense-in-depth，不是 sole control）
- **policy 表达式 CEL**：熟悉 CEL 需要学习成本，但这是 Google 维护 8+ 年的工业标准，长期看是合理选择
- **fail-closed 默认**：shipped 默认是 `deny: []` + `allow: ["true"]`——这意味着不配 policy 所有 action 都会被拒，**第一次配环境时容易踩坑**（误以为是 bug）

---

## 十一、回到系统层——OpenBot 真正贡献的是什么

把这件事拉到系统层看，OpenBot 真正的贡献不是「让 agent 有浏览器」——这件事 2024 年就做过了。**它的不可替代处是把「agent 能做」和「agent 值得被信任做」之间那道工程鸿沟，用三层架构（target 解析 → CEL policy → audit row）填平**，并把整套治理塞进 43KB 的 gateway.ts + 17KB 的 sandbox.ts + 15KB 的 policy.ts 里。

这套治理的价值可以用一句话量化：**把 agent 从「一个 LLM 在你电脑里乱点」变成「一个经过审计、可以担责的同事」**。这不是技术升级，是**身份升级**。

更深的层：OpenBot 的设计哲学里藏着一条**对 agent 行业最重要的元命题**——**「默认安全，把 enable 当作显式选择」**。这条哲学贯穿 target check（私网默认拒绝）、fail-closed policy（缺策略允许 0）、凭据 redact（secret 永不返回）、审计 redact（凭据写入前屏蔽）四个层面。

它不试图「让你方便地用 agent」，而是「**让你安心地用 agent**」。这是 2024-2025 年 OpenAI Operator、Anthropic Computer Use、Browser Use 都回避的真正难题，而 OpenBot 选择直面。

如果你正在做 agent infra、做企业 AI 平台、或者认真思考「agent 怎么进入生产」——**这个仓库值得花一个周末把它吃透**。43KB 的 gateway.ts + 17KB 的 sandbox.ts + 15KB 的 policy.ts + 22KB 的 supervisor/docker.ts + 46KB 的 agent-computer/index.ts，已经把 agent 治理的核心工程问题讲清楚了。

剩下的脚本和 docs 都是工程化的延伸。它的工程美学在于**「把所有不安全当作不变量默认」**——这条哲学是所有安全系统的共同根基，从 SELinux 到 OpenSSH，但 OpenBot 是第一个把它完整应用到 AI agent 领域的开源项目。

---

## 参考资料

- **代码仓库**：https://github.com/CopilotKit/OpenBot （MIT, 3097 stars, 2026-08-17 上线）
- **官方文档站**：https://www.copilotkit.ai/openbot
- **协议层**：[ag-ui-protocol/ag-ui](https://github.com/ag-ui-protocol/ag-ui) — Agent-to-User Interaction Protocol
- **CopilotKit 生态**：https://www.copilotkit.ai — 商业版（含托管的 CopilotKit Intelligence）
- **关键参考文**：
  - **docs/architecture.md**（15KB）— 7 服务 8 端口的运行时拓扑 + 治理三层 + policy 字段列表
  - **docs/configuration.md**（27KB）— 30+ 环境变量详解，是「从 single-user 到 production」的最完整路径
  - **docs/coworkers.md**（4.5KB）— agents.yaml / remote-ag-ui / built-in 两种 Bot 类型
  - **docs/deployment.md**（8KB）— 单镜像 vs docker-compose、min size、replicas 行为
  - **docs/development.md**（5KB）— `bun run test` / `bun run typecheck` / Drizzle schema 迁移
  - **docs/releasing.md**（5KB）— 版本号策略、CHANGELOG 规范
- **核心源码**：
  - `server/src/computer/gateway.ts`（43KB）— 治理核心：5 步流水线 + audit-first 不变量
  - `server/src/computer/policy.ts`（15KB）— CEL 表达式 + fail-closed 引擎
  - `server/src/computer/sandbox.ts`（17KB）— sandbox 工具集
  - `server/src/computer/target.ts`（12KB）— 私网地址默认拒绝 + cloud metadata 黑名单
  - `server/src/audit.ts`（25KB）— 审计行 schema + retention + redact
  - `agent-computer/src/index.ts`（46KB）— Chromium 编排 + screencast + workspace + shell
  - `supervisor/src/docker.ts`（22KB）— per-Bot 容器生命周期
- **同领域参考**：
  - [Browser-Use/browser-use](https://github.com/browser-use/browser-use) — 让 LLM 操作浏览器的轻量方案（OpenBot 的功能子集）
  - [ag-ui-protocol/ag-ui](https://github.com/ag-ui-protocol/ag-ui) — Agent-to-User Interaction Protocol
  - [portiaAI/portia-sdk-python](https://github.com/portiaAI/portia-sdk-python) — 同定位的合规 agent 平台（Python；repo 名以仓库实际情况为准）
  - [Skyvern-AI/skyvern](https://github.com/Skyvern-AI/skyvern) — 同定位的浏览器 agent 平台
  - [Significant-Gravitas/AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) — agent 框架经典参考（OpenBot 是 runtime，不是 framework）
- **安全标准参考**：
  - **PCI DSS**、**HIPAA**、**SOC 2** — OpenBot 的 audit / encrypt / redact 设计直接对应这些合规标准
  - **CEL（Common Expression Language）** — Google 维护 8+ 年的工业级表达式语言，K8s / Istio 同款
  - **SPIRE** — OpenBot compose 预留的零信任 workload identity 服务
  - **fail-closed vs fail-open** — OpenBot 全面 fail-closed 的设计哲学（与 OpenSSH / SELinux / AppArmor 同源）