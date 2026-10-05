---
title: "CopilotKit/OpenBot：当 AI agent 终于有了「自己的电脑」，治理网关才是真正的工程难题"
date: 2026-08-27T18:03:00+08:00
lastmod: 2026-10-05T00:00:00+08:00
draft: false
tags: ["CopilotKit", "OpenBot", "AG-UI", "Agent Governance", "Browser Automation", "MCP", "CEL Policy", "Audit Trail", "AI Coworker"]
categories: ["技术笔记"]
description: "CopilotKit 在 2026-08 上线 OpenBot——让 AI agent 各拿一台独立浏览器+工作区+登录态，用统一网关治理所有 tool call，把审计日志写进 PostgreSQL。本文按 2026-10-05 的 v0.1.0 复核：6k stars / MIT / 30 个子项目 / 12 个框架适配器。它真正解决的不是「让 agent 拿浏览器」，而是「agent 能拿到工具」与「agent 值得被信任使用工具」之间的工程鸿沟——用 target 解析 → CEL 策略 → 审计行三层填平。"
slug: copilotkit-openbot-ai-coworker-with-own-computer-deep-read
github_repo: "CopilotKit/OpenBot"
source_key: "gh:CopilotKit/OpenBot"
---

# CopilotKit/OpenBot：当 AI agent 终于有了「自己的电脑」，治理网关才是真正的工程难题

`CopilotKit/OpenBot` 2026-08-17 在 GitHub 上线，本文写作时（2026-08-27）它有 3,097 stars / 377 forks、最新 release 是 08-22 的 v0.0.4（package.json 同步在 0.0.4）；到 2026-10-05 复核，读数涨到 6,030 stars / 807 forks，五个周里连发 12 个版本（0.0.5 → 0.0.15 → v0.1.0，2026-10-03），仓库从 621 个文件扩到 1,643 个。README 的状态徽章仍是 **Alpha**——「early, expect rough edges」的警告原样挂着。

五个周前的 OpenBot 和现在的 OpenBot 不是同一个东西。但它真正的立身之本没变：**承认 agent 能拿到工具 ≠ agent 值得被信任使用工具**，并用三层架构（target 解析 → CEL 策略评估 → 审计行写入）把这两件事之间的工程鸿沟填平。这句话反过来说更清楚——给 agent 一个浏览器这件事，Browser Use、Open Operator、Anthropic Computer Use 在 2024-2025 年就做完了；在每一次动作发生前先裁决、先留痕，没人做到 OpenBot 这个深度。

工程骨架也是那时候打好的：Bun + Hono + React + Vite + Drizzle ORM + PostgreSQL（pgvector 镜像 pg17）技术栈，写作时 14 个子项目，现在 30 个目录——多出来的 12 个是 `agent-<framework>` 框架适配器（Google ADK、AG2、Agno、Claude SDK、CrewAI、LangGraph AG-UI、Langroid、LlamaIndex、Mastra、Microsoft Agent Framework、Pydantic AI、Strands），另有 desktop 桌面壳和 mobile（Expo）两个新端。

一句话定位，用现行 README 自己的话：

> **The AI assistant your company can actually own.** Same shape as ChatGPT, Claude or Grok, with one difference that matters: it runs on your infrastructure and you can change anything about it. Any agent stack, through AG-UI.

五个周里 README 还多了一段新的定位声明，值得抄给所有做开源 agent 平台的人：

> **A template, not a product.** OpenBot is meant to be cloned and made your own. There is no hosted version to sign up for, and nothing here is published as a package to depend on: every workspace in this repository is private.

通读双时点的 README、7+4 份 docs、310KB 的 CHANGELOG 和核心源码之后，五条工程判断如下：

1. **AG-UI 协议的「框架无关」不是营销话术**。README 原话是「the governance rides the protocol rather than the framework」——治理跑在协议层而不是框架层，今天用 LangGraph 写的 agent，明天换成 CrewAI，治理规则、审计行、policy 全部原样有效。五个周后仓库里多出 12 个框架适配器目录和一条 compose 里的 `agent-harness` 服务（端口 4202），等于官方自己兑现了这个承诺。
2. **per-Bot 独立浏览器容器 + 治理网关**是 OpenBot 的真发明——每 Bot 一台 Chromium + 自己的登录态 + 自己的 `/workspace`，supervisor 按需启停，所有 tool call 走唯一网关。
3. **Fail-closed 语义**贯穿全栈——策略缺失或为空时允许零动作、坏 deny 规则按拒绝处理、坏 allow 规则不给许可、私有地址默认拒绝、凭据加密后永不返回 API、审计行 redact 凭据内容。注意这说的是「策略引擎遇到缺损时的行为」；出厂自带的默认策略本身是显式的全放行（下文详述），这是很多解读文会读反的地方。
4. **人机协作的事件级审计**（`computer.help_requested` / `control_taken` / `control_released`，v0.1.0 起多了 `help_cancelled`）+「人在时 Bot 行动被拒绝而不是排队」——这种细节暴露了它是从真实企业场景长出来的。
5. **五个周的方向盘转向**：从「一个治理严格的平台」转向「一个让你克隆改造的模板」——example coworker 从 3 个变 13 个、发布镜像上 ghcr.io、桌面壳可一键安装、加上了 Routines 定时任务和 Automatic Learning 循环。治理内核原封未动，产品外壳全面提速。

下面分十一节展开，最后附这五个周的版本变迁清单。

---

## 一、问题域——「agent 能用工具」之后，下一道题是什么

2024 年的 AI agent 主流叙事是「让模型能操作浏览器」。Browser Use、Anthropic Computer Use、OpenAI Operator 用的是同一套思路：让 LLM 看截图、决定点哪里、敲键盘。

这套思路留下三个没有解决的工程难题：

- **登录态怎么管**。Gmail、银行后台、企业内部系统都需要登录。共享人类登录态高危，每次弹 2FA 破坏自主性，给 agent 单独账号则有成本和管理开销。
- **怎么知道 agent 在干什么**。人类看不到操作过程，只能事后看日志。但事后日志不够——agent 可能已经在错误的页面上提交了表单、点错了删除按钮。
- **agent 出错时谁负责**。LLM 幻觉 + 高风险操作（医疗、金融、运营）= 责任真空。

OpenBot 的回答：**给每个 agent 一台自己的电脑 + 一个唯一的治理网关 + 一份不可篡改的审计日志**。它把 agent 从「一个 LLM 在你电脑里乱点」变成「一个经过审计、可以担责的同事」。

---

## 二、AG-UI 协议——为什么「框架无关」是 OpenBot 能成立的前提

OpenBot 建在 AG-UI（[ag-ui-protocol/ag-ui](https://github.com/ag-ui-protocol/ag-ui)）之上。README 原话：

> A Bot is any endpoint speaking AG-UI, the open protocol for agent-to-user interaction, so OpenBot is not tied to a framework and neither are you. Agents built with LangGraph, Mastra, CrewAI, Pydantic AI, Google ADK or written by hand all arrive the same way, and the governance rides the protocol rather than the framework.

协议层治理的好处用一句话说清：**今天用 LangGraph 写的 agent，明天换成 CrewAI，所有治理规则、审计行、policy 仍然有效**。

`docs/architecture.md` 把 Bot 定义为两种类型：`built-in`（纯 system prompt）或 `remote-ag-ui`（任意 AG-UI 端点）。端点不是随便填的：

- 端点校验用浏览器导航时同一套 target check，注册时验一次，端点返回的**每一次重定向**再验一次
- 授权 header 是 write-only 存的
- 私网地址默认拒绝，必须显式列进 `AGENT_ENDPOINT_ALLOWED_HOSTS`（精确匹配，host 带端口则钉死端口；写成 URL 或带 `*` 会直接拒绝启动）

这套设计对 2026 年的 agent 生态是结构性正确的判断——单框架独大的时代过去了，跨框架互操作是趋势，而治理必须能跨框架。五个周后 12 个框架适配器目录落地，验证了这个判断。

---

## 三、核心机制 1——per-Bot 独立浏览器容器：supervisor + agent-computer

OpenBot 真正的工程创新是「**每 Bot 一台电脑**」，由 supervisor 子项目编排。

`supervisor/src/docker.ts`（写作时 22KB，现 27KB）只暴露四个操作：ensure、stop、reset、list。每个 Bot 一个独立 Docker 容器，挂独立 `/workspace` 卷、独立 Chromium profile；容器绑 127.0.0.1 + per-container `COMPUTER_TOKEN`（任何请求必须带 token）；Bot 容器与 PostgreSQL 分处不同 Docker 网络，互相摸不到。它握着 Docker socket，所以 compose 把它钉在 `127.0.0.1:4500`（容器内 4300）。想再进一步，设 `COMPUTER_RUNTIME=runsc` 可以把计算机跑在 gVisor 沙箱里。

`agent-computer/src/index.ts`（写作时 46KB，现 65KB）负责：

- 跑一个 Chromium（Playwright 1.62 驱动），暴露浏览器 snapshot、aria-snapshot（accessibility tree）、screencast（实时屏幕流）、file/workspace 工具
- shell 命令继承 PATH + locale + proxy 变量，**不继承部署环境的其他变量**——一个明确的最小环境面
- proxy URL 自动剥离 userinfo（防止密码泄漏进容器）

**出口网络是这套隔离的另一半，写作时的文章漏了它**：每个 Bot 的浏览器出口走 per-Bot egress 代理，配置放在仓库根的 `egress.env`（不是装着部署密钥的 `.env`），`EGRESS_PROXY_DEFAULT` 兜底、`EGRESS_PROXY_<BOT_ID>` 按 Bot 覆写。没配这个文件时浏览器直连出网。

v0.1.0 把出口治理又拧紧了一格：**Bot 的计算机在服务器推送网络策略之前拒绝一切网络**。CHANGELOG 原话承认了旧行为的代价——「A computer used to allow every connection until the server had pushed its Bot's network policy, which left up to 30 seconds of unfiltered access after every wake」。脱离 API server 单跑计算机的老场景可以设 `EGRESS_POLICY_REQUIRED=0` 退回。同一版还修掉一个安全隐患：形如 `10.0.0.5/` 的坏 IP 段过去会被读成 `/0` 放行全部 IPv4，现在包含坏段的整份策略被拒绝，其下的 Bot 回落到一张空 allowlist——在管理员于 Admin → Enterprise 修正之前什么都访问不了。

人机协作的控制权状态机在 `agent-computer/src/control.ts`（写作时 9KB，现 12KB）：它管 `ControlState` 与动作屏障（action barrier）。而**事件级审计的写入发生在 server 侧**——事件常量收在 `server/src/audit.ts`，由 `server/src/computer/gateway.ts` 的 `writeControlEvent` 落库。两处合起来才是完整链路：

```text
computer.help_requested    → agent 撞登录墙 / 2FA 时主动求助（v0.1.0 起可取消：help_cancelled）
computer.control_taken     → 人类接过控制
computer.control_released  → 人类交还控制
```

**关键安全语义**：人类控制浏览器期间，Bot 的所有行动被「**拒绝**」而不是「排队」。排队意味着 Bot 动作会以不可预测的顺序跟在人类操作后面执行；拒绝意味着人类操作期间 Bot 完全冻结。v0.1.0 补了另一半：没挂浏览器的 run 遇到人类接管时**暂停等待交接**，而不是错误退出。

这套 per-Bot computer + event-level handoff 的设计，本质是把 Kubernetes pod 的隔离模型搬到 agent 领域——每个 agent 是一个有自己计算环境、自己身份、自己审计的独立单元。

---

## 四、核心机制 2——治理网关（gateway.ts，写作时 43KB，现 56KB）

`server/src/computer/gateway.ts` 是仓库最大的单一源文件之一，也是 OpenBot 治理的核心。**任何**浏览器操作、文件操作、MCP 调用都必须经过它。README 对它的定义只有一句：

> The gateway is the only way in: it resolves the target from a server-held snapshot, evaluates the policy, writes the audit row, and only then calls the computer. There is no path that acts without the record existing first.

`docs/architecture.md` 把它展开成五步流水线：

```text
1. resolve the target      → 从 server 持有的快照或请求主体解析目标
2. evaluate policy         → 用当前 action policy 评估
3. write audit row         → 先为这个决定写一行审计
4. call computer (if pass) → 决定放行才调计算机
5. write second audit row  → 放行的动作执行失败再补一行
```

三个关键设计：

### 4.1 Audit 写在 call 之前

「任何行动发生之前，审计行必须先存在」是 OpenBot 最核心的安全声明。看到一条 `action_permitted` 的审计行，就一定有过一次真实行动；看到一次真实行动，审计里一定有对应记录。这条不变量让审计行可以当作事后追责的 ground truth。

### 4.2 Fail-closed 引擎，和一个容易被读反的默认值

`server/src/computer/policy.ts`（写作时 15KB，现 19KB）的语义抄自 `docs/architecture.md` 原文：

```text
Deny rules are evaluated before allow rules. The policy engine fails closed:
a missing or empty policy permits nothing, a broken deny rule denies, and a
broken allow rule does not permit. OpenBot's shipped startup default is
explicit: deny: [] and allow: ["true"], unless AGENT_COMPUTER_POLICY or a
saved administrator policy replaces it. A malformed configured policy stops
server startup.
```

逐句拆开：

- **deny 先于 allow** 评估
- **策略缺失或为空** → 什么都不允许
- **坏 deny 规则** → 按拒绝算；**坏 allow 规则** → 不给许可——凡「我不确定」一律不放行
- **出厂默认**是显式的 `deny: []` + `allow: ["true"]`——deny 空、allow 是恒真表达式，**合起来等于默认放行一切**
- **格式损坏的策略** → 服务器拒绝启动

这里是最容易读反的地方：fail-closed 说的是「引擎遇到缺损配置时的行为」，而出厂默认是一个**故意写出来的全放行策略**——开箱即可用，本地体验优先；管理员一旦开始写自己的规则，从一张空表起步就是全拒绝，收紧哪些动作是显式决定。两种行为各管一段，不矛盾。

policy 用 CEL（Common Expression Language）写，配大小写不敏感的 `contains()` 和 `matches()`。规则能检查的字段，写作时是 10 类，现在扩到 12 类：

```text
tool.name | intent | bot.id | actor.id
page.url | page.host
element.ref | element.role | element.name | element.type
key
command                                        ← v0.1.0 新增
file.path | file.name | file.extension
mcp.server | mcp.tool | mcp.effect
initiator.kind | initiator.id                  ← v0.1.0 新增
```

`initiator` 是五周里最有分量的新增：它回答「这个 run 是谁发起的」，枚举 `person` / `deployment` / `routine` / `handoff`。文档特意点明 `actor.id` 在定时 run 里取的是 routine 的属主，所以 `initiator.*` 是**唯一能区分「无人值守的定时任务」和「有人正在打字」的字段**——一条规则可以拒绝定时 routine 做的事，同时放行人类亲自发起的同一件事。

### 4.3 Target check（target.ts，12KB，五个周零改动）——私有地址默认拒绝

浏览器要导航的 URL 必须过 target check，**任何私有 IP 段默认拒绝**（`AGENT_COMPUTER_ALLOW_PRIVATE_HOSTS=true` 可放行，但 `NODE_ENV=production` 下设了它直接拒启动）。

这是云上 agent 的头号安全漏洞——AWS / GCP 的 metadata endpoint 是 `169.254.169.254`，agent 摸到它就能拿到临时凭据；内网服务在 `10.0.0.0/8`、`192.168.0.0/16`、`127.0.0.0/8`。OpenBot 默认全部拒绝，强制管理员显式列白名单。`docs/architecture.md` 的安全边界清单里写着「cloud metadata addresses are refused under every configuration」——云元数据地址在任何配置下都拒，没有例外口子。

「默认安全，把 enable 当作显式选择」——target check、egress 策略、v0.1.0 对坏 IP 段的处置，三处都是同一个哲学。

---

## 五、核心机制 3——审计行（audit.ts，写作时 22.5KB，现 42KB，五个周翻了近一倍）

`server/src/audit.ts` 是 OpenBot 的「黑匣子」。它的体量本身就是信息——这五个周里审计覆盖面一直在扩。

**记什么**：每一次 tool call、每一次点击/按键/滚动、每一次文件读写、登录、权限变更、agent endpoint 变更、policy 变更、凭据请求、控制权交接。v0.1.0 的清单里连「一个人把自己的账号连到某个 MCP server」（`mcp.account_connected`）和对应的断开（`mcp.account_disconnected`）都各有专属行——后者的 `vendorRevocationRequested` 字段甚至记录了「是否已向厂商请求撤销授权」这个细节。

**怎么记**：事件分四类写——`computer.action_allowed` / `action_refused` / `action_failed` / `action_stopped`。源码注释里有一句值得所有做审计系统的人读三遍的话：

> a trail that records only what was permitted cannot answer whether the Bot tried.

只记放行的轨迹回答不了「Bot 到底试过什么」。拒绝要记，放行后执行失败要记，被人类按 Stop 中断的也要单独记——因为「把 Stop 算进失败率的报表会把一次人为改变主意报成一次系统故障」。

**行的形状**：`audit_events` 表的列是 `actorUserId`（有意不做外键——轨迹 append-only，任何级联更新都是触发器要拒绝的）、`eventType`、`targetType`/`targetId`、`payload`（jsonb）、时间戳。Bot 信息、命中的规则、具体目标都在 payload 里；`/admin/audit` 页面把每次拒绝连同**命名的那条规则**一起展示（架构图的原话是「or refuses and names the rule」）。事后追责时，你能精确知道谁、哪个 Bot、想对哪个目标做什么、被哪条规则挡下来。

**删不删**：`audit-retention.ts` 这个文件名容易让人以为它负责「到期自动清理」，实际行为恰好更克制。文件头部的注释先把问题摆上台面：审计表会在真实使用的几周内长成部署里最大的表，而产品过去「什么都不删」，企业买家问起保留政策时，诚实的回答只能是「我们永远保留一切，且你无法表达别的选项」。它的解法是：

- **默认不删**。`AUDIT_RETENTION_DAYS` 不设就永久保留——「因为默认值说删就删掉别人的审计轨迹，是两种失败里更糟的那种」
- **显式配置才删**，按天数为窗口批量清扫（单批 5,000 行，Postgres advisory lock 保证多副本只跑一个清扫者）
- **表严格 append-only**：数据库层拒绝一切 delete——除非事务显式声明了 retention 窗口；窗口内的行也照样拒绝删除；UPDATE 在任何条件下都不可能。「我们删掉了关于那次事故的行」在这套机制下无法发生

顺带修正「窗口不是记录」这个容易忽略的边界：`/channel` 里的 Activity 面板（Bot 跑过的命令、输出、退出码，文件读写清单，最新在前）**只存在于浏览器里，刷新即失**。文档原话是「It is a window rather than a record; the record is the audit trail」——调查者要读的是服务端那份跨重启存活的审计轨迹，不是这个窗口。

---

## 六、核心机制 4——凭据流与 secret 隔离

OpenBot 处理凭据的细节是它工程深度的另一个缩影：

- **录入端**：`/admin/credentials` 是 write-only 界面，存库时用 `KEY_ENCRYPTION_KEY` 加密
- **使用端**：API 永不返回明文凭据
- **审计端**：审计行 redact 凭据内容，只记「请求了凭据、N 字符」
- **生命周期端**：`KEY_ENCRYPTION_KEY` 必须是 base64 编码的 32 字节值，公开的 example key 在 `NODE_ENV=production` 下直接拒启动

这一套对应企业安全合规审查（PCI DSS、HIPAA、SOC 2）是直接可用的。

更细的两条：OAuth access / refresh token 用 Better Auth 自带加密，keyed on `BETTER_AUTH_SECRET`；SAML signing material 走 OpenBot 自己的 wrapper 加密——因为 Better Auth 的 SSO 插件默认把这部分存成明文 JSON。后一条是「真的做过企业集成的人」才会写出来的代码。

---

## 七、核心机制 5——人机协作 + 实时观测

OpenBot 把「人类监控 agent」当作一等公民设计：

- **实时屏幕**：Bot 看的页面经 websocket 实时转给人类，走和其他路由同一个权限问题（`screencast.ts`，写作时 6.9KB，现 9KB）
- **Activity tab**：Bot 跑过的命令、输出、退出码、文件读写，按时间倒序最新在前；但记住第五节说的——它是窗口不是记录
- **文件查看只显示路径和大小**：绝不回显内容，因为 agent 可能存了用户托付的机密；写文件的路由同样拒绝回显
- **控制权交接**：`help_requested → control_taken → control_released` 三事件（v0.1.0 加了 `help_cancelled`），审计行 + UI 状态机各一份
- **人在时 Bot 拒绝**：人类控制期间 Bot 行动被拒绝而不是排队；无浏览器挂载的 run 则暂停等待

---

## 八、核心机制 6——Skills 缩窄 + 治理三维

「让 agent 只看到该看到的工具」是另一个细节亮点（`docs/architecture.md` 的「Which tools a run is offered」一节——这段五个周零改动，原文引用仍然逐字成立）：

```text
- 模型选对工具的能力：~10 个稳定，~30 个不可靠
- 连接两个 vendor，第一个下午就会越过 10 个工具这条线
- Bot 持有太多工具时，每次 run 只 offer 匹配 message 的 skills 所声明的工具
```

实现路径：

1. 每条 message 进来，部署先问自己的 model：「这条 message 匹配哪些 skill？」
2. Bot 拿到这些 skill 声明的工具 + 所有 granted 但没有 skill 认领的工具
3. **声明不等于授权**——offer 永远与已有 grant 取交集，写 skill 不可能让任何人多拿到一个工具

这套「narrow the offer, not the boundary」的设计哲学，官方的完整表述是：

> This narrows the offer. It is not a boundary, and it never substitutes for one. The grant, the policy and the audit row decide what may happen; this decides only what the model can see. Every way it can fail — no skills declared, a model that cannot answer, a message that matches nothing, twelve tools or fewer — leaves the whole catalogue offered, because a narrowing that failed closed would remove capability an administrator granted, silently.

缩窄的是 offer（模型看到的），不是 boundary（policy/audit/grant 管的）。缩窄失败时回退到全目录——因为「失败即关闭的缩窄会悄悄拿走管理员明确授予的能力」。把「失败安全」和「失败有据」分开，这段注释是最好的教材。

五个周后这个机制长出了新枝：随包发布的 `skill-creator` skill 被授予后，Bot 可以**在对话里和你一起写出一个新 skill**，且只有你按下卡片上的按钮才会保存——「在对话里制造能力，但落盘要过人手」。v0.1.0 还补了配套的收紧：卸载 skill 时它的 grants 一并撤销。

---

## 九、社区与生态——CopilotKit 的纵深，与「模板化」转向

CopilotKit 不是从石头里蹦出来的：OpenBot 背靠 [CopilotKit 商业平台](https://www.copilotkit.ai)，配套托管的 CopilotKit Intelligence（线程持久化、记忆、实时网关、Learning 容器）。

- **托管或自托管都行**：Intelligence 有免费 Developer plan；不想用云的，v0.1.0 起官方支持在**一台 Mac 的 Docker 里本地跑 Intelligence**（30 天 license，`npx copilotkit@latest local renew` 可反复续期，官方明说这是预览、不是生产安装）
- **AG-UI 生态绑定**：CopilotKit 是 AG-UI 协议的主要维护者，OpenBot 跑在 AG-UI 上等于绑定了这个协议生态

**生态布局，按 2026-10-05 口径**：

- **13 个 example 同事**：写作时是 3 个（General Assistant 日常 / Knowledge 企业知识 / Risk Analyst 风控，第三个现在改为经端点触达）；v0.0.14 起新增 10 个单文件同事放在 `examples/fintech/agents/`，每个只做一件事——按政策原文核报销单、把会议纪要拆成跟进项、从已发布内容起草 release notes、工单分诊、按员工手册答新人提问、写研究简报（并写明没找到什么）、整理面试纪要、on-call 交接、续约前汇总已知信息、把客户反馈聚成可引用的主题
- **Tenant package**：`examples/fintech/` 下 6 份 yaml——`agents.yaml` / `channels.yaml` / `brand.yaml` / `knowledge.yaml` / `model.yaml` / `skills.yaml`，v0.1.0 起每个同事还可以拆成 `agents/` 目录下的单文件
- **MCP catalogue**：写作时 Google Drive + Notion 已 ship；现在加上了 Parallel Search（公开网检索与抽取），并经 Composio 代理了几百个应用——catalogue 只收部署方愿意背书的 vendor，自定义 server 过 URL 检查，未知工具一律按写操作对待
- **Routines**（0.0.5 引入，0.1.0 成型）：让 Bot 按计划做事，以发起人的身份在发起的频道里跑。15 分钟下限 + 20 个启用上限防止一句话排出让人生畏的计划表，连续失败 10 次自动停——「与其永远烧模型钱不如停下来」。需要 worker 进程，`scripts/start.sh` 会带起来
- **Automatic Learning**（0.1.0 新增，默认开启）：Bot 把完成的会话贡献给 Intelligence 的 Learning 容器，换回它发布的 skill——部署方在 Intelligence 侧审证据、批修订，OpenBot 侧只管映射和投递
- **Bot 间协作**（0.0.5 引入）：一个 Bot 可以把活转交给另一个 Bot，没有 Bot 能接时找人
- **SPIRE**：compose 里预留的零信任 workload identity 服务入口（spire-init / spire-server / spire-agent 三件），未见官方文档展开，当作预留位看

**发布形态也变了**：v0.1.0 起镜像发布在 `ghcr.io/copilotkit/openbot`——

```sh
docker run -p 3001:3001 --env-file .env \
  -e EMBEDDED_POSTGRES=on -v openbot-data:/var/lib/postgresql \
  ghcr.io/copilotkit/openbot:latest
```

不用 clone、不用 build，应用也挂在 3001（clone 方式是 3001 + 3010 两个端口）。README 新增的「A template, not a product」声明就是这个转向的官方注脚：它不想做你注册使用的 SaaS，它想被你克隆后变成你自己的产品。

**对照参考**：

- **vs Browser Use / Open Operator / Anthropic Computer Use**：它们解决「一个 LLM 看你的浏览器」，OpenBot 是「一个有治理的 AI coworker 平台」
- **vs LangChain / LlamaIndex / CrewAI**：它们是 agent 框架，OpenBot 是运行时——不同层，可以组合（12 个适配器目录就是证明）
- **vs Portia / Skyvern 等合规或浏览器 agent 平台**：定位有重叠，OpenBot 的差异点是 MIT + 自托管 + 完整源码 + 每动作裁决的治理粒度

---

## 十、采用顺序与边界——谁该先用，谁可以等等

### 10.1 该先上

**做企业 SaaS / 内部 agent 平台 / 需要合规审计的团队**：

- 已经有 LangGraph/CrewAI/Mastra 写的 agent，想加治理层
- 要让 agent 操作 Gmail / Notion / Google Drive / 内部系统，但不敢把登录态直接交给 LLM
- 需要 SOC 2 / HIPAA / GDPR 式的审计证据链
- 接受它还是 Alpha，「早期使用换深度参与」是笔划算的交易

**做 agent infra / 平台工程师**：

- gateway / policy / audit / supervisor 的实现是教学级的——五步流水线、fail-closed 引擎、append-only 审计，每个模块都小到能一个下午读完
- 这套架构可以借鉴到任何 agent runtime，不限于浏览器场景

**做 AG-UI 协议生态的开发者**：OpenBot 是 AG-UI 在治理层的 reference 级实现。

### 10.2 可以等等

**只想要一个 Computer Use 的开源替代**：Browser Use 轻得多，不需要治理时上 OpenBot 是过度工程。

**只想要 MCP client / skill registry**：看 `server/src/plugins/` 子目录就够了，不必搬整套 stack。

**只想要一个 agent 框架**：那你要的是 LangGraph / CrewAI，不是 OpenBot。两者不冲突。

### 10.3 上手顺序（2026-10-05 口径）

1. **跑通全栈**：`cp .env.example .env && bun install` → `bash scripts/start.sh` → 打开 `http://localhost:3010`。启动脚本拉起 Docker 服务、跑迁移、起 API（3001）、起 routine worker、起应用（3010），健康检查全过才打印下一步；`scripts/stop.sh` 收摊，`--keep-computers` 保留 Bot 计算机，数据都在卷里不会丢
2. **接 Intelligence**：`npx --yes copilotkit@latest login` → `project select` → `bun scripts/setup-learning.ts`——新 helper 会配好 runtime key、建（或复用）`openbot` Learning 容器并把两者写进 `.env`。managed Intelligence 不再需要单独的 license token；只想要 key-only 老接法的，容器也可以事后在 Admin → Automatic Learning 里指派
3. **填剩下的必填项**：`OPENAI_API_KEY`，以及 `openssl rand -base64 32` 生成自己的 `KEY_ENCRYPTION_KEY`（example key 仅限本地）
4. **加 OAuth provider**：配 Google / Microsoft / Okta / 自家 SAML；`INITIAL_ADMIN_EMAILS` 授予第一批管理员，之后 `/admin/people` 可提升他人——但写在这个变量里的地址是下限，无法从界面降级或移除
5. **加 coworker**：从 `/agents` 建第一个 Bot，给一个 standing role；或者在 `examples/fintech/agents/` 挑一个现成的单文件同事改
6. **配 policy**：从 `/admin/boundaries` 写 deny 规则 → 跑一次浏览器动作 → 去 `/admin/audit` 看审计行怎么落、拒绝如何命名规则
7. **上生产**：`/admin/people` 管权限、`/admin/credentials` 存加密凭据、`NODE_ENV=production` 启用强制项（拒 example key、拒私网放行开关）；过一遍 0.1.0 的升级清单——Automatic Learning 默认开启（不需要就显式关）、egress 策略变为推送前拒绝、10 个数据库迁移（0042–0051）

### 10.4 必看边界

- **Alpha 状态**：README 徽章和粗体警告都还在，生产部署请备好降级路径
- **出厂默认是全放行，收紧靠你**：`deny: []` + `allow: ["true"]` 开箱即用；开始写 policy 后，空表起步就是全拒绝——从默认放行收紧到你的规则，这个过程的方向别搞反
- **依赖 Intelligence**：threads 和 memory 在外部服务（托管或本地 Docker）。Automatic Learning 0.1.0 起默认开启，不想要就显式保存关闭设置
- **agent-computer 绑 127.0.0.1**：compose 只把它暴露在 `127.0.0.1:4100`，健康检查路由除外的一切请求都要 `COMPUTER_TOKEN`。别把它发布到 0.0.0.0——token 是纵深防御的一层，不是唯一防线
- **egress 三件套**：per-Bot 代理（`egress.env`）、推送前拒绝（0.1.0）、坏 IP 段整份拒绝——把 Bot 的出口当正式网络边界来配
- **policy 表达式 CEL**：有学习成本，但这是 Google 维护多年、K8s/Istio 同款的工业标准，长期看是合理选择

---

## 十一、回到系统层——OpenBot 真正贡献的是什么

把这件事拉到系统层看，OpenBot 的贡献不是「让 agent 有浏览器」——这件事 2024 年就做过了。它把「agent 能做」和「agent 值得被信任做」之间的鸿沟，用三层架构（target 解析 → CEL policy → audit row）填平了。

这套治理的价值可以用一句话说清：**把 agent 从「一个 LLM 在你电脑里乱点」变成「一个经过审计、可以担责的同事」**。这不是技术升级，是身份升级。

底下压着一条元命题：**默认安全，把 enable 当作显式选择**。它贯穿四处——target check（私网默认拒绝、云元数据无例外）、策略引擎（缺损即拒绝）、审计（append-only，删除需要显式声明且留痕机制守门）、egress（0.1.0 起策略推送前一根网线都不通）。v0.1.0 修坏 IP 段的方式是「整份策略拒绝、Bot 回落空 allowlist」，宁可用不了也不悄悄放行——这个取舍就是这条哲学的样子。

五个周从 0.0.4 到 0.1.0，OpenBot 在外壳上做尽了减法（一键 docker run、桌面壳、对话里建同事），在治理内核上做尽了加法（initiator 字段、egress 收紧、审计扩容、Learning 循环也默认带审计语义）。一个想被克隆的模板，把「值得被信任」做成了出厂配置——这个组合在开源 agent 项目里还找不到第二个。

## 附：从 0.0.4 到 v0.1.0——五个周的变迁清单

| 版本（日期） | 主要变化 |
| --- | --- |
| 0.0.5–0.0.7（08-28–09-04） | Bot 间转交与找人、Routines 雏形、Kubernetes 部署文档；发布全部服务镜像；对话中写 skill、建同事（起步零权限）、standing instructions |
| 0.0.8–0.0.10（9 月上中旬） | 桌面壳（安装 OpenBot 然后成为它）；消息带附件；桌面 setup 直接装容器引擎；生成式界面（表格/表单）；审计 redact 与 fail-open 修缺陷系列 |
| 0.0.11–0.0.12（9 月中旬） | 策略规则可询问 run 发起者（initiator 前身）；Composio 代理几百应用；skill 卸载撤 grants；Bot shell 读不到邻近进程的部署密钥 |
| 0.0.13–0.0.14（9 月中下旬） | Google Drive 共享盘；组织级登录权威；+10 个单文件 example 同事；ADK/Langroid 等适配器可用 |
| 0.0.15（9-22） | 模型 provider 自带登录可顶 API key；钉死 Bun 版本才可启动 |
| **v0.1.0（10-03）** | Automatic Learning 默认开；egress 推送前拒绝+坏 IP 段整份拒；`command`/`initiator.*` 入 CEL；`help_cancelled` 事件；Helm chart 全量（Slack/Teams/短信/push/SCIM/inbound email/OpenTelemetry）；自托管帮助条幅（付费 plan 不显示）；10 个迁移 |

## 参考资料

- **代码仓库**：https://github.com/CopilotKit/OpenBot （MIT；2026-10-05 读数 6,030 stars / 807 forks；2026-08-17 上线）
- **官方文档站**：https://www.copilotkit.ai/openbot
- **协议层**：[ag-ui-protocol/ag-ui](https://github.com/ag-ui-protocol/ag-ui) — Agent-to-User Interaction Protocol
- **CopilotKit 生态**：https://www.copilotkit.ai — 商业版（含托管与本地 Docker 两种 Intelligence）
- **docs（11 份）**：architecture（30KB，双时点核对主力）/ configuration / coworkers / deployment / development / releasing / automatic-learning / parallel-research / routines / windows-signing / README
- **核心源码**：
  - `server/src/computer/gateway.ts`（56KB）— 治理核心：五步流水线 + audit-first 不变量 + 控制事件写入
  - `server/src/computer/policy.ts`（19KB）— CEL 表达式 + fail-closed 引擎
  - `server/src/computer/sandbox.ts`（26KB）— sandbox 工具集
  - `server/src/computer/target.ts`（12KB，五周零改动）— 私网默认拒绝 + 云元数据黑名单
  - `server/src/audit.ts`（42KB）— 审计事件类型全集 + redact
  - `server/src/audit-retention.ts`（7KB）— opt-in 保留窗口 + append-only 守门
  - `agent-computer/src/index.ts`（65KB）— Chromium 编排 + screencast + workspace + shell
  - `agent-computer/src/control.ts`（12KB）— 控制权状态机与动作屏障
  - `supervisor/src/docker.ts`（27KB）— per-Bot 容器生命周期
- **同领域参考**：
  - [Browser-Use/browser-use](https://github.com/browser-use/browser-use) — 轻量浏览器操作（OpenBot 的功能子集）
  - [Skyvern-AI/skyvern](https://github.com/Skyvern-AI/skyvern) — 浏览器 agent 平台
  - [portiaAI/portia-sdk-python](https://github.com/portiaAI/portia-sdk-python) — 合规 agent 定位（Python）
  - [Significant-Gravitas/AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) — agent 框架经典参考（OpenBot 是 runtime，不是 framework）
- **安全标准参考**：PCI DSS / HIPAA / SOC 2（audit-encrypt-redact 设计的对应面）；CEL（K8s/Istio 同款表达式语言）；SPIRE（compose 预留的零信任 workload identity）
