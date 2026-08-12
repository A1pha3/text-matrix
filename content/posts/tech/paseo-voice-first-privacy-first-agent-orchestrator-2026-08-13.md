---
title: "Paseo 深度解读：voice-first + privacy-first + mobile-first 的 agent 编排器，它跟 Orca 的差异不在功能列表，在产品哲学"
date: 2026-08-13T00:25:00+08:00
draft: false
tags: ["AI Agent", "开源项目深拆", "Mobile", "Voice", "Privacy", "Self-hosted", "Expo", "Coding Agent"]
categories: ["技术笔记"]
description: "getpaseo/paseo（paseo.sh）是 2026 年 8 月 GitHub 新上的 agent 编排器，跟 Orca 同赛道但产品哲学完全不同——零 telemetry / 零 tracking / 零 forced login / AGPL-3.0 / E2E encrypted relay / voice control / TypeScript SDK / Skills（handoff/advisor/committee）。它不实现 agent，它把 Claude Code / Codex / Copilot / OpenCode / Pi 五个 agent 装进同一个 daemon，从手机 / 桌面 / CLI / web 四端操控。本文拆它的架构（daemon + WebSocket + relay + provider adapter）、它的 agent lifecycle 状态机、它的 Skills 系统，以及它在 Orca / oh-my-pi / pi-mono 赛道里的差异化定位。"
slug: "paseo-voice-first-privacy-first-agent-orchestrator"
band: "review"
gates: ["事实性", "去AI味", "观点依据"]
github_repo: "getpaseo/paseo"
---

## 这篇文章在回答什么

`getpaseo/paseo`（品牌名 paseo.sh）的 README 第一句话：

> One interface for Claude Code, Codex, Copilot, OpenCode, and Pi agents.
> Run agents in parallel on your own machines. Ship from your phone or your desk.

把它和刚写过的 Orca 放在一起看，赛道几乎一样——「多 agent 编排器」。但产品哲学完全不同。差异不在功能列表，在三个选择上：

1. **隐私优先于功能**——Paseo 零 telemetry / 零 tracking / 零 forced login / AGPL-3.0。Orca 有 telemetry（可 opt out）。Paseo 把隐私做成第一卖点，不是可选项。
2. **语音优先于键盘**——Paseo 有 voice control（dictate tasks / talk through problems）。Orca 没有。Paseo 把"对着手机说一句话让 agent 干活"做成一等公民。
3. **Skills 优先于 worktree**——Paseo 有三个内置 Skills：`/paseo-handoff`（plan with Claude → handoff to Codex）、`/paseo-advisor`（second opinion）、`/paseo-committee`（root cause analysis with two contrasting agents）。Orca 把 worktree 编排做成一等公民。Paseo 把 **agent 间协作** 做成一等公民。

这篇文章做三件事：

1. 拆 Paseo **的架构**——daemon + WebSocket + relay + provider adapter，10 个 packages 各做什么
2. 拆 Paseo **的产品哲学**——隐私 / 语音 / Skills 三条差异化线各自付出的工程代价
3. 把 Paseo 放到赛道——跟 Orca / oh-my-pi / pi-mono 的关系是互补还是替代

## 一、架构：daemon 是心脏，WebSocket 是动脉

Paseo 是 client-server 架构。`docs/architecture.md` 开篇给了一张系统图：

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Mobile App │    │     CLI     │    │ Desktop App │
│   (Expo)    │    │ (Commander) │    │ (Electron)  │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       │   WebSocket      │   WebSocket      │
       │  (direct or      │  (direct)        │
       │   via relay)     │                  │
       └──────────┬───────┴──────────────────┘
                  │
           ┌──────▼──────┐
           │   Daemon    │
           │  (Node.js)  │
           └──────┬──────┘
                  │
     ┌────────────┼────────────┬────────────┬────────────┐
     │            │            │            │            │
┌────▼─────┐ ┌───▼────┐ ┌──────▼─────┐ ┌────▼─────┐ ┌────▼────┐
│ Claude   │ │ Codex  │ │  Copilot   │ │ OpenCode │ │   Pi    │
│ Agent    │ │ Agent  │ │    ACP     │ │  Agent   │ │ Agent   │
│ SDK      │ │ Server │ │            │ │          │ │         │
└──────────┘ └────────┘ └────────────┘ └──────────┘ └─────────┘
```

四个客户端（Mobile / CLI / Desktop / Web）通过 WebSocket 连一个 daemon，daemon 管理五个 agent provider 进程。

### 1.1 daemon 做什么

`packages/server` 是 Paseo 的心脏。一个 Node.js 进程，职责清单来自 `docs/architecture.md`：

- 监听 WebSocket 连接
- 管理 agent 生命周期（create / run / stop / resume / archive）
- 实时流式输出 agent timeline
- 通过 transport-neutral tool catalog 提供 agent-to-agent 工具（MCP 是其中一个 adapter）
- 可选连接 relay 做远程访问
- 可选在同一个 HTTP server 上 serve web client

关键模块：

| 模块 | 职责 |
|---|---|
| `server/bootstrap.ts` | daemon 初始化：HTTP / WS server / agent manager / storage / relay |
| `server/websocket-server.ts` | WebSocket 连接管理 / hello 握手 / binary frame 路由 |
| `server/session.ts` | 每 client session 状态 / timeline 订阅 / terminal 操作 |
| `server/agent/agent-manager.ts` | agent 生命周期状态机 / timeline 跟踪 / subscriber 管理 |
| `server/agent/agent-storage.ts` | 文件 JSON 持久化到 `$PASEO_HOME/agents/` |
| `server/agent/tools/` | transport-neutral tool catalog |
| `server/agent/mcp-server.ts` | MCP adapter（把 Paseo tool catalog 注册到 MCP SDK） |
| `server/agent/providers/` | provider adapter |
| `server/relay-transport.ts` | 出站 relay 连接 + E2E 加密 |
| `server/schedule/` | cron 定时 agent |

**注意一个设计决策**：Paseo tools 不是 MCP tools——它们住在 `packages/server/src/server/agent/tools/` 的共享 tool catalog 里，MCP 只是 fallback adapter。支持 native tools 的 provider（`supportsNativePaseoTools: true`）直接消费 `launchContext.paseoTools`，不走 MCP 中转。这意味着 **Paseo 的 tool 层是 provider-agnostic 的**——同一套工具定义可以注入到任何 provider。

### 1.2 5 个 provider adapter

`docs/providers.md` 详细描述了两种集成模式：

**ACP（Agent Client Protocol）模式**——推荐路径。继承 `ACPAgentClient`，处理进程 spawning / stdio transport / session lifecycle / streaming / permissions / model discovery。目前 Copilot 用这个模式（`copilot-acp-agent.ts`）。

**Direct 模式**——直接实现 `AgentClient` + `AgentSession` 接口。已有实现：Claude / Codex / OpenCode / Pi / oh-my-pi（omp）/ mock（dev only）。

每个 provider 有自己的 `providerOptions`——Paseo 验证它用 provider 自己的 strict schema。比如 Codex 接受 `approval_policy` / `sandbox_mode` / `web_search` / `features.multi_agent_v2`；Claude 接受 `allowedTools` / `disallowedTools` / `sandbox` / `settings`；OpenCode 接受 `permission`。

这意味着 **Paseo 不试图统一 provider 的能力面**——它让每个 provider 保留自己的原生配置选项，只在外层做编排。这跟 Orca 的"30+ adapter 统一成同一套内部接口"策略不同——Paseo 的策略是 **"5 个 adapter 各保留原生语义，编排层透明传递"**。

### 1.3 protocol / client / app / cli / relay 五个 packages

| Package | 职责 |
|---|---|
| `packages/protocol` | WebSocket 消息 schema / binary frame codec / timeline 类型 / provider config schema——所有 shared 类型在这里 |
| `packages/client` | 低层 daemon WebSocket driver + 高层 `PaseoClient` facade——SDK facade |
| `packages/app` | Expo 客户端（iOS / Android / web）——React Native + Expo Router |
| `packages/cli` | Commander.js CLI——Docker 风格命令（`paseo run/ls/attach/send/wait`） |
| `packages/relay` | E2E encrypted relay transport——daemon 和 client 共享 |

**`packages/protocol` 是零依赖的**——server / app / cli / client 都依赖它，它不依赖任何一个。这是经典的 **shared kernel 模式**——把所有跨端共享的类型放在一个独立包里，避免循环依赖。

`packages/client` 有一个双面 API 设计：低层 `@getpaseo/client/internal/daemon-client` 给 app / cli 用（迁移期），高层 `@getpaseo/client` 给 SDK 用户用。这意味着 **Paseo 的 SDK 不是事后抽取——它是 daemon client 的天然 facade**。

## 二、Agent lifecycle：从 initializing 到 closed

`docs/agent-lifecycle.md` 给了完整的状态机：

```
initializing → idle → running → idle (or error → closed)
                 ↑        │
                 └────────┘  (agent completes a turn, awaits next prompt)
```

每个 live agent 在 `AgentManager` 里带一个 `lastStatus`：`initializing` / `idle` / `running` / `error`。`closed` 是持久化的、可恢复的状态——agent record 存在但没有 live provider runtime。

### 2.1 Runtime residency：idle 不等于 closed

这是 Paseo lifecycle 里最有判断力的一条设计——**idle agent 保持 resident**。

> Idle agents remain resident indefinitely. Runtime closure happens only through an explicit lifecycle action such as archive, replacement, reload, workspace teardown, or daemon shutdown.

也就是说，agent 跑完一轮后停在 `idle` 状态，**它的 provider 进程、订阅、background work 全部保留**——直到显式关闭。这意味着 agent 可以在下一轮 prompt 时**立刻响应**，不需要重启 provider。

但这条设计有一个真实的风险——provider 进程可能在 idle 期间**静默死掉**：

> A provider runtime can still die on its own — crash, OOM kill, host suspend. Work the agent parked inside that process dies with it: Claude Code's background Bash shells, Monitor watches, and workflows all live in the CLI process, and the completion notification that would have woken the agent never arrives.

Paseo 的应对是：**runtime 死亡时报一个 turn failure，让 agent 进入 `error` 状态**——而不是假装 agent 还 healthy。这是一个诚实的工程取舍——**承认你无法检测所有死亡模式，但保证你能报告你观察到的**。

### 2.2 Cancellation 的 split-brain 防御

Cancellation 那一段有一个非常细致的工程设计：

> Cancellation changes lifecycle state only after the provider acknowledges the interrupt or emits a terminal turn event. If the interrupt is rejected or times out, the agent remains `running` with its active foreground turn intact.
>
> Synthesizing a local cancellation without provider acknowledgment creates a split-brain session: Paseo accepts a new prompt while the provider still owns the previous foreground turn.

**Split-brain**——Paseo 不允许"本地以为 cancelled 但 provider 还在跑"的状态。这跟前面写过的 pi-mono / oh-my-pi 的 abort 设计一致（abort 必须等 provider 确认），但 Paseo 把它放在 **agent lifecycle state machine** 层面——不只是 signal 传递，是状态转换的前置条件。

### 2.3 Parent / Child / Detached

Agent 可以通过 `create_agent` MCP tool 创建子 agent。子 agent 的关系：

- **Subagent**——属于创建者，出现在创建者的 subagent track 里，随创建者一起 archive
- **Detached agent**——通过显式 detach 操作独立，不再出现在 former parent 的 track 里

Detach 是**纯关系操作**——它只删 `paseo.parent-agent-id` label，不停 / 不 archive / 不移动 / 不重启 agent。Agent 保持当前 `cwd` 和 `workspaceId`，离开 parent 的 track，以后行为像一个 root agent。

这个设计解决了一个具体问题：**agent 间的关系是 metadata，不是 runtime 状态**。关系变了，runtime 不需要变。

## 三、隐私优先：零 telemetry 的工程含义

Paseo 的 privacy-first 不是 marketing 词——它落在三个具体工程决策上。

### 3.1 零 telemetry / 零 tracking / 零 forced login

README 明确写了：

> **Privacy-first:** Paseo doesn't have any telemetry, tracking, or forced log-ins.

`docs/product.md` 的 Core philosophy 那一节把"Respectful"列为设计原则：

> **Respectful** — No telemetry, no forced cloud, no forced accounts

这跟 Orca 形成鲜明对比——Orca 的 README 有 `Privacy & telemetry docs` 链接说明收集什么匿名使用数据、怎么 opt out。Paseo 的选择是**完全不收集**。

工程含义是什么？**没有 telemetry 意味着不能靠数据驱动决策**。Paseo 团队不知道用户最常用哪个 provider、哪个 feature crash 最多、哪个路径转化率最高。他们只能靠 GitHub issues / Discord / Reddit 做定性反馈。

这是一个**产品速度 vs 用户信任**的交换。Paseo 选了信任——对 self-hosted / privacy-conscious 开发者来说，这是决定性的卖点。

### 3.2 AGPL-3.0

Paseo 的 license 是 AGPL-3.0——不是 MIT 也不是 Apache-2.0。AGPL 的关键条款是**网络使用也触发 copyleft**——如果你修改 Paseo 并通过网络提供服务，你必须开源你的修改。

Orca 是 MIT。oh-my-pi 是 MIT。pi-mono 是 MIT。**Paseo 是这个赛道里唯一一个 AGPL 的主要项目**。

这是一个非常明确的信号——**Paseo 不希望被云厂商 fork 后闭源 SaaS 化**。AGPL 保护开源项目的商业护城河，代价是**企业采用阻力更大**（很多公司法务禁用 AGPL）。

### 3.3 E2E encrypted relay

`packages/relay` 是 E2E 加密的 relay bridge，用 Elixir 写（`getpaseo/paseo-relay`）。relay 连接 daemon 和 remote client，**relay server 看不到内容**——加密在客户端完成。

`SECURITY.md` 描述了 relay threat model：

- Relay 是可信传输层，但不可信内容层——relay 看到加密流量，看不到明文
- DNS rebinding 防御——daemon 验证 Host header
- Agent auth——每个 agent 有独立 auth token

E2E relay 的工程含义：**Paseo 可以在不开端口的情况下远程访问**——手机通过 relay 连 daemon，daemon 不需要暴露公网 IP。这跟 Tailscale / WireGuard 的模式类似，但 Paseo 把它做进了产品里——不需要额外装 VPN。

## 四、语音优先：voice control 的产品逻辑

README 的 features 列表里，voice control 排第三（Self-hosted / Multi-provider / **Voice control** / Cross-device / Privacy-first）：

> **Voice control:** Dictate tasks or talk through problems in voice mode. Hands-free when you need it.

`packages/app/src/` 有 voice 相关代码，`packages/expo-two-way-audio` 是一个独立的 Expo module——iOS / Android 双向音频。这意味着 **Paseo 的语音不是简单的 speech-to-text**——它是**实时双向语音**（你说话，agent 听到；agent 说话，你听到）。

为什么 voice control 是 Paseo 的差异化？把它放到 mobile-first 的场景里看——**手机上打字不方便，但说话很方便**。开发者从手机上给 agent 发 prompt，最快的路径不是打开键盘打字，而是**按住按钮说一句话**。

这跟 Orca 的 mobile companion 形成对比——Orca 的 mobile 是**监控 + steering**（看 agent 状态、发 follow-up），Paseo 的 mobile 是**voice-first interaction**（用嘴跟 agent 对话）。

Voice 的工程代价是显白的——`packages/expo-two-way-audio` 有原生 iOS / Android 代码、需要处理麦克风权限、音频编码、网络延迟、回声消除。这是一个**独立的工程投入**，不是所有 agent 编排器都愿意做的。

## 五、Skills：agent 间协作的产品化

Paseo 的 Skills 系统是它最有判断力的差异化——README 给了三个内置 Skills：

> ```bash
> npx skills add getpaseo/paseo
> ```
>
> - `/paseo-handoff` — hand off work between agents. I use this to plan with Claude and then handoff to Codex to implement.
> - `/paseo-advisor` — spin up a single agent as an advisor for a second opinion, without delegating the work itself.
> - `/paseo-committee` — form a committee of two contrasting agents to step back, do root cause analysis, and produce a plan.

这三个 Skills 把 **agent 间协作模式** 做成了产品级 abstraction：

### 5.1 /paseo-handoff：plan → implement 分工

Plan with Claude → handoff to Codex。Claude 负责"想清楚"（拆任务 / 定接口 / 写 spec），Codex 负责"做出来"（写代码 / 跑测试 / 修 bug）。

这个模式对应了一个真实的工程实践——**senior engineer 设计 + junior engineer 执行**。Paseo 把它映射成 **Claude（擅长推理）+ Codex（擅长实现）** 的分工。

### 5.2 /paseo-advisor：second opinion

启动一个 advisor agent 做"第二意见"——不 delegating 工作，只做 review。主 agent 继续干活，advisor 在旁边看。

这跟 oh-my-pi 的 **advisor 角色**（特性 #06）是同一个模式——两个项目独立实现了同一种协作抽象。

### 5.3 /paseo-committee：root cause analysis

两个"对比性" agent 组成委员会——step back、做根因分析、产出计划。这是一个**多模型辩论**的产品化——让两个不同视角的 agent 对同一个问题给出不同分析。

committee 模式的价值在于**对抗单一模型的 confirmation bias**——一个 agent 可能沿着错误路径越走越远，两个不同视角的 agent 更容易在早期发现分歧。

### 5.4 Skills 系统的工程含义

Skills 是 `npx skills add getpaseo/paseo` 安装的——这意味着它走的是 **skills 生态协议**（`skills` CLI），不是 Paseo 私有格式。任何支持 skills 协议的 agent 都能用。

这跟 oh-my-pi 的 Skills（`learn` / `manage_skill`）不同——oh-my-pi 的 skills 是**agent 自己写的**（agent 从经验中学习、自动创建 skill），Paseo 的 skills 是**人写的**（开发者预定义协作模式）。

两种模式的差异：oh-my-pi 的 skill 是**agent 级**的（让 agent 变更聪明），Paseo 的 skill 是**orchestrator 级**的（让多 agent 协作更高效）。

## 六、TypeScript SDK：把 daemon 变成可编程平台

Paseo 有一个 `@getpaseo/client` TypeScript SDK——README 给了示例：

```ts
import { createPaseoClient } from "@getpaseo/client";

const client = createPaseoClient({ url: "ws://127.0.0.1:6767/ws" });
await client.connect();

const agent = await client.agents.create({
  config: { provider: "codex/gpt-5.5" },
  cwd: "/Users/me/dev/storefront",
  prompt: "Review the current diff and name the riskiest change.",
});

const result = await agent.waitForFinish();
console.log(result.lastMessage);

await client.close();
```

这是 Orca 没有的——Orca 的 4 入口（TUI / one-shot / SDK / RPC / ACP）虽然有 SDK，但不是 TypeScript first-class。Paseo 的 SDK 是 **TypeScript 原生**，走 WebSocket 连 daemon。

SDK 的存在意味着 **Paseo daemon 是一个可编程平台**——第三方可以构建 dashboard、issue 集成、CI pipeline、orchestration service，所有这些都通过同一个 SDK 接入。

README 的 Related projects 那一节已有证据：

- `getpaseo/paseo-relay`（Elixir relay，独立 repo）
- `paseo-skins`（社区主题 + 主题加载器 + Agent Skill）
- `paseo-vscode`（VS Code 扩展）

三个相关项目都是社区贡献——SDK 让社区生态成为可能。

## 七、Docker：daemon + web UI in a container

README 给了 Docker 一键启动：

```bash
docker run -d --name paseo \
  -p 6767:6767 \
  -e PASEO_PASSWORD=change-me \
  -v "$PWD/paseo-home:/home/paseo" \
  -v "$PWD:/workspace" \
  ghcr.io/getpaseo/paseo:latest
```

这意味着 **Paseo 可以跑在 headless server 上**——不需要 desktop / mobile app，通过 web UI 访问。对 CI / 远程开发 / 企业内网场景，Docker 是必需品。

Orca 也有 headless Linux server 支持（`docs/reference/headless-linux-server.md`），但 Paseo 的 Docker 化更彻底——一个命令拉起 daemon + web UI，`localhost:6767` 直接用。

## 八、Paseo vs Orca：同赛道，不同哲学

把 Paseo 和 Orca 放在一起，差异不在功能列表，在**产品哲学**：

| 维度 | Orca | Paseo |
|---|---|---|
| **产品起点** | Desktop IDE（Electron） | Mobile app（Expo） |
| **Agent 数** | 30+ | 5 |
| **隐私** | 有 telemetry（可 opt out） | 零 telemetry |
| **License** | MIT | AGPL-3.0 |
| **语音** | 无 | Voice control（双向音频） |
| **Skills** | 无 | 3 个内置（handoff / advisor / committee） |
| **Worktree** | 一等公民 | 支持，但不是焦点 |
| **SDK** | 无 TypeScript first-class | `@getpaseo/client` |
| **Relay** | 自有 | Elixir 独立 repo，E2E encrypted |
| **Docker** | headless Linux server | 一键 Docker |
| **Annotate diff** | 一等公民 | 无 |
| **GitHub / Linear** | 原生集成 | 无 |
| **社区生态** | 无 | relay / skins / vscode 三方 |

哲学差异一句话总结：

- **Orca 是 "IDE for agents"**——把 agent 装进 IDE，开发者用 IDE 的方式指挥 agent
- **Paseo 是 "remote control for agents"**——把 agent 留在 daemon 里，开发者用手机 / 桌面 / CLI / web 从外面操控 agent

两种哲学不是替代关系——**它们适合不同场景**：

| 场景 | 选 Orca | 选 Paseo |
|---|---|---|
| 桌面深度开发 | ✅ | |
| 手机随时介入 | ✅ | ✅ |
| 语音指挥 agent | | ✅ |
| Self-hosted / 离线 | | ✅ |
| 多 agent fan-out + compare | ✅ | |
| Agent 间协作（handoff / committee） | | ✅ |
| 企业 IT / 合规 | | ✅（AGPL + 零遥测） |
| CI / headless server | ✅ | ✅ |

## 九、Paseo 在 pi 生态的位置

把 Paseo 放到更大的 agent 生态里——它和 pi-mono / nano-pi / pi-book / oh-my-pi 的关系：

| 项目 | 定位 | 与 Paseo 的关系 |
|---|---|---|
| pi-mono | agent loop 作为库 | Paseo 的 provider adapter 之一（Pi agent） |
| nano-pi | 600 行教学版 | 无直接关系 |
| pi-book | pi-agent-core 中文架构书 | 无直接关系 |
| oh-my-pi | pi-mono 工程级 hyper-fork | **Paseo 的 provider adapter 之一**（omp agent） |

Paseo 支持 5 个 provider：Claude Code / Codex / Copilot / OpenCode / Pi。其中 **Pi 和 oh-my-pi（omp）都是 Paseo 的 provider adapter**——Paseo 可以把 oh-my-pi 作为一个 agent 运行。

这意味着 **Paseo 和 oh-my-pi 不是竞争关系**——Paseo 是 oh-my-pi 的**容器**。你可以在 Paseo 里同时跑 oh-my-pi 和 Claude Code，用 `/paseo-handoff` 在两者间分工。

## 十、落地路径

按代价从小到大排：

**1. Docker 一键启动。** `docker run -d --name paseo -p 6767:6767 -e PASEO_PASSWORD=change-me -v "$PWD/paseo-home:/home/paseo" -v "$PWD:/workspace" ghcr.io/getpaseo/paseo:latest`。打开 `localhost:6767`，装一个 agent CLI（Claude Code / Codex / Copilot / OpenCode / Pi），开始跑。

**2. CLI 快速上手。** `npm install -g @getpaseo/cli && paseo`。daemon 启动后用 `paseo run --provider claude/opus-4.6 "implement user authentication"` 直接派活。`paseo ls` 看跑着的 agent，`paseo attach abc123` 看实时输出。

**3. 手机配对。** 桌面 app 打开 Settings → Pair Device，手机扫二维码配对。走 E2E relay（自动加密），或 Tailscale / 直连 TCP。

**4. 装 Skills。** `npx skills add getpaseo/paseo`，在任何 agent 对话里用 `/paseo-handoff` / `/paseo-advisor` / `/paseo-committee`。

**5. TypeScript SDK 编排。** `npm install @getpaseo/client`，写自己的 issue 集成 / dashboard / CI pipeline。

**6. Fork + 加 provider。** `docs/providers.md` 给了 ACP / Direct 两种模式的完整指南。ACP 推荐（继承 `ACPAgentClient`），Direct 需要实现 `AgentClient` + `AgentSession`。

## 十一、一章小结

Paseo 不是又一个 Orca。它是 **voice-first + privacy-first + mobile-first 的 agent 编排器**。

三件事连起来：

1. **架构**——daemon + WebSocket + relay + 5 provider adapter，10 个 packages 分工清晰，protocol 是零依赖 shared kernel。
2. **哲学**——零 telemetry / AGPL-3.0 / E2E relay / voice control / Skills，每一条都付出工程代价，换来 privacy-conscious 开发者群体的信任。
3. **位置**——Paseo 和 Orca 同赛道不同哲学（"remote control" vs "IDE"）；和 oh-my-pi 互补（oh-my-pi 是 Paseo 的 provider 之一）。

一句话版本：**Orca 把 agent 装进 IDE，Paseo 把 agent 留在 daemon 里——你用手机 / 桌面 / CLI / 语音从外面操控。前者像 VS Code，后者像 Home Assistant**。

## 为什么不去

> **为什么 Paseo 只支持 5 个 agent 而不是像 Orca 那样支持 30+？** 因为每加一个 provider 就要实现一个 adapter——ACP 模式还好（继承基类），Direct 模式要从头实现 `AgentClient` + `AgentSession`。5 个是当前能做扎实的上限。Orca 的 30+ adapter 是工程投入的规模优势（团队更大、节奏更快），Paseo 选了**少而深**——每个 provider 的原生配置选项都保留、schema 严格验证、provider 特有的 capability 有 feature gate。**5 个做得好比赛跑 30 个**。
>
> **为什么 Paseo 选 AGPL-3.0 而不是 MIT？** 因为 AGPL 保护 Paseo 不被云厂商 fork 后闭源 SaaS 化。AGPL 的网络使用条款让任何修改后提供网络服务的衍生品必须开源。代价是企业采用阻力更大——很多公司法务禁用 AGPL。Paseo 选了**保护开源护城河 > 最大化企业采用**。这跟 pi-mono / oh-my-pi / Orca 的 MIT 路线完全不同——后者选了**最大化传播 > 保护商业护城河**。
>
> **为什么 Paseo 的 Skills 不是 agent 自动生成的？** 因为 Paseo 的 Skills 是 **orchestrator 级**的（让多 agent 协作），不是 **agent 级**的（让单个 agent 变更聪明）。Orchestrator 级 skill 需要的是**人对协作模式的理解**（plan → implement / second opinion / committee），不是 agent 从经验中学习的自动沉淀。oh-my-pi 的 `learn` / `manage_skill` 是后者——让 agent 自己写 skill。两种模式服务的场景不同：Paseo 的 skill 是**产品级预设**，oh-my-pi 的 skill 是**agent 级学习**。两者可以共存——Paseo 的 `/paseo-handoff` 可以让一个有 learn 能力的 agent 跑完后再把经验沉淀回来。
