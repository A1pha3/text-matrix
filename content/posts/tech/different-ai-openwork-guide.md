---
title: "OpenWork：让 AI Agent 的能力跨越工具边界的开源协作平台"
date: "2026-07-30T22:00:00+08:00"
draft: false
slug: "different-ai-openwork-guide"
description: "OpenWork 是一个开源的桌面端 AI 工作空间，基于 opencode 引擎构建。它把 Skills、MCP 连接、模型配置封装成可共享的能力层，通过一个远程 MCP 服务接入 Claude Code、Codex、Cursor 等任意 Agent——让团队能用同一套配置工作，而不被锁死在单一工具里。"
categories: ["技术笔记"]
tags: ["AI Agent", "MCP", "OpenWork", "opencode", "跨工具协作"]
---

## 本文导读

读完本文你将能够：

- 说清 OpenWork 到底解决了什么问题：不是「又一个 Claude Code」，而是把 Agent 能力层从具体工具里剥离出来
- 理解 OpenWork 的三层架构（桌面客户端 / 服务端 / Den 控制面）各自承担什么职责
- 区分 Skills、Plugins、MCP Connections 三个概念在 OpenWork 语境下的精确含义和适用场景
- 根据 team 规模和工具组合选出一条可行的接入路径
- 独立完成一次 OpenWork MCP 的接入和基础配置

适合读者：正在使用 Claude Code / Codex / Cursor 等 Agent 工具，感觉到「每个工具各配一遍太重复」的工程师、技术负责人或小团队 lead。

---

## 一、先给判断：OpenWork 不是「另一个 Claude Code」

如果你只用一个 Agent 工具，OpenWork 对你的价值有限。但只要你有以下任意一种情况，它就值得认真看一看：

1. **团队里有人用 Claude Code，有人用 Cursor，有人用 Codex**——各自配置 MCP、Skills、API Key，任何一项变更都要在 N 台机器上重复操作
2. **你有一套精心调好的 Skills 或 MCP 连接**，想打包分享给同事，但没有比「截图配置文件发 Slack」更好的办法
3. **你需要对团队使用的模型和工具做统一管控**——谁能用哪个模型、哪些 MCP 允许连接、桌面端版本策略，这些在纯本地工具里没有管理面

OpenWork 做的事情用一句话概括：**把 Agent 的「能力层」（Skills + MCP + 模型配置）从具体工具里抽出来，变成可共享、可管理、可分发的中间层。** 它不替代你的 Agent，而是给你的 Agent 装上一个共享背包。

这个项目目前 18.5k stars，TypeScript 写的，基于 opencode 引擎。支持 macOS、Windows、Linux 三个平台。

---

## 二、系统地图：三层架构 + 一个协议

OpenWork 的架构可以用三句话说完：

- **桌面客户端**（Electron + React）——用户面，你在这里和 Agent 对话
- **服务端**（openwork-server）——本地或远程运行，封装 opencode 引擎，管理 workspace 和 session
- **Den 控制面**（ee/ 目录下的 Cloud/Self-hosted 服务）——团队管理层，负责成员、权限、Marketplace、MCP 连接分发

三者之间的关系长这样：

```
┌──────────────────────────────────────────────────────┐
│  Claude Code  │  Codex  │  Cursor  │  桌面客户端      │
│               │         │          │  (Electron App) │
└───────────────┴─────────┴──────────┴────────┬─────────┘
                                              │
                    OpenWork MCP (Remote)      │
                    api.openworklabs.com/mcp   │
                                               │
              ┌────────────────────────────────┴────┐
              │        Den 控制面 (Cloud/Self-host) │
              │  - Members & RBAC                   │
              │  - Marketplace (Skills/Plugins)     │
              │  - MCP Connections (shared)         │
              │  - LLM Providers (managed)          │
              │  - Desktop Policies                 │
              └─────────────────────────────────────┘
                              │
                    ┌─────────┴──────────┐
                    │  openwork-server   │
                    │  (本地 or 远程)     │
                    │  wraps opencode    │
                    │  engine            │
                    └────────────────────┘
```

### 桌面客户端：不是必须的，但是体验最好的

桌面客户端用 Electron + React 构建，UI 组件基于 shadcn/ui（底层 Base UI），状态管理用 Zustand，数据层用 TanStack Query 和 Drizzle ORM。它本质上是一个面向 OpenWork server 的前端消费者。

但这里有个设计决策值得注意：**桌面客户端不是必须的**。你可以只用 OpenWork MCP——往 Claude Code 或 Cursor 里加一个远程 MCP 地址，你的 Agent 就能访问到团队共享的所有 Skills 和 MCP 连接。桌面客户端存在的意义是提供一个完整的工作空间体验（多 session 管理、artifact 展示、内嵌终端等），而不是强制锁入。

代码中可以看到，客户端通过 `@opencode-ai/sdk` 与服务端通信，所有 session、message、tool 调用都走标准 HTTP。`apps/app/src/app/lib/opencode.ts` 里定义了完整的 client 接口：

```typescript
type PromptAsyncParameters = {
  sessionID: string;
  directory?: string;
  messageID?: string;
  model?: { providerID: string; modelID: string };
  agent?: string;
  parts?: unknown[];
  reasoning_effort?: string;
};
```

### 服务端：opencode 引擎的封装层

`openwork-server` 是一个可以独立运行的 Node.js/Bun 服务。从 `apps/server/src/index.ts` 的导出可以看到它的定位非常清晰——一个可嵌入的服务：

```typescript
import { startEmbeddedServer } from "openwork-server";

const handle = await startEmbeddedServer({
  host: "127.0.0.1",
  port: 0,
  workspaces: ["/path/to/workspace"],
  token: clientToken,
  hostToken: hostToken,
  manageOpencode: true,
  opencodeBin: "/path/to/opencode",
});

console.log(`Server at ${handle.url}`);
handle.stop();
```

服务端自身依赖很少：`better-sqlite3` 做本地存储、`drizzle-orm` 做数据访问层、`zod` 做类型校验、`yaml` 和 `jsonc-parser` 解析配置。整体是轻量的，没有引入重量级框架。

服务端的核心职责包括：

- 管理 workspace（本地和远程）和 session 生命周期
- 封装 opencode 引擎的启动、停止和通信
- 处理 MCP 配置的增删改查（`apps/server/src/cloud-mcp-health.ts` 负责健康检查）
- 云同步：把 Den 控制面的 Skills、Plugins、MCP 连接同步到本地（`apps/server/src/desktop-cloud-sync.ts`）
- 审计日志（`apps/server/src/audit.ts`）
- 文件 session 和 artifact 管理

### Den 控制面：团队级别的能力分发

Den 是 OpenWork 的团队管理组件，代码在 `ee/` 目录下（Enterprise Edition）。它包含：

- **den-api**：后端 API 服务，处理成员、团队、权限、Marketplace、计费等
- **den-web**：管理界面，组织管理员在这里操作
- **den-gateway**：API 网关
- **inference**：推理代理，管理模型调用的路由和配额

Den 的核心价值在于「一次配置、全员可用」。举个例子：管理员在 Den 里创建一个 Notion 的 MCP 连接，配置好 OAuth 和访问范围，团队成员在各自的桌面客户端里就能直接使用——不需要各自去 Notion Developer Portal 注册应用、拿 client ID、配 redirect URL。

MCP 连接支持两种账户模式：

- **Individual accounts**（默认）：每个成员用自己的 OAuth 身份连接。适合 Notion、Linear 这种每个人都有自己权限范围的工具
- **One org account**：管理员连接一次，所有人的 Agent 都以这个身份操作。适合共享邮箱、团队 Slack bot 等场景

---

## 三、OpenWork MCP：两把钥匙开所有门

OpenWork MCP 是整个系统里最精巧的设计。它不试图把所有功能塞进一个臃肿的 MCP server，而是只暴露两个工具：

| 工具 | 作用 |
|------|------|
| `search_capabilities` | 搜索当前用户可用的 Skills、MCP 连接和插件 |
| `execute_capability` | 执行匹配到的能力 |

这个设计的好处在于：Agent 不需要预先知道你有哪些 Skills 或 MCP 连接。它先搜索，找到合适的，再执行。新增能力不需要改 Agent 的配置——在 Den 里发布一个新的 Marketplace 插件，所有通过 OpenWork MCP 连接的 Agent 立刻就能发现并使用。

### 接入任意 Agent

OpenWork MCP 是标准的远程 MCP server，URL 是：

```
https://api.openworklabs.com/mcp/agent
```

主流 Agent 的接入方式：

**Claude Code：**
```bash
claude mcp add --transport http openwork https://api.openworklabs.com/mcp/agent
```

**Codex：**
```bash
codex mcp add openwork --url https://api.openworklabs.com/mcp/agent
```

**OpenCode（opencode.json）：**
```json
{
  "mcp": {
    "openwork": {
      "type": "remote",
      "enabled": true,
      "url": "https://api.openworklabs.com/mcp/agent",
      "oauth": {}
    }
  }
}
```

**Cursor / VS Code / Windsurf / Zed / Gemini CLI / Claude Desktop**——文档里都有对应接入方式，本质上都是连同一个远程 MCP 地址。

接入后浏览器会弹出 OAuth 登录页面，选择你的 OpenWork 组织即可。这个流程设计得很顺手——把认证交给 OAuth，不搞自己的账号体系。

---

## 四、Skills、Plugins、MCP Connections：三个容易混淆的概念

在 OpenWork 语境里，这三个词有明确的不同含义。理解它们的边界是用好 OpenWork 的前提。

### Skill

Skill 是一段可复用的 Markdown 指令文件（`SKILL.md`），告诉 Agent 「在某个场景下应该怎么做」。它本质上就是 prompt engineering 的模块化封装。

比如你可以写一个 Skill：「当用户让你处理日期时，始终先用 `date` 命令获取当前时区时间，不要假设时区」。写一次，全团队可用。

Skill 可以从聊天中直接创建——在桌面客户端的对话里把一段做得不错的 prompt 保存为 Skill，它会同步到 Den，其他成员立刻能用。

### Plugin

Plugin 是一组 Skills 和/或远程 MCP 的打包集合，通过 Marketplace 分发。它对应的是「一套完整的工作流」。

比如一个「GitHub 工作流插件」可能包含：
- 3 个 Skills（PR 审查模板、commit message 规范、issue 分类逻辑）
- 1 个远程 MCP 连接（GitHub API）

Plugin 还支持导入 Anthropic 兼容格式——如果你有现成的 Claude plugin，可以直接导入到 OpenWork Marketplace。

### MCP Connection

MCP Connection 是一个由组织管理的 MCP 服务连接（Notion、Linear、Stripe、Sentry、Exa 等）。它处理的不是「怎么让 Agent 做事」，而是「让 Agent 能访问什么外部服务」。

每个 MCP Connection 的核心配置：

- 服务端 URL
- OAuth 模式（Individual / One org account）
- 访问范围（全组织 / 特定团队 / 特定人员）
- 可选预设（Notion、Linear、Stripe、Sentry、Exa、Context7）

三者关系简单概括：**Skill 是指令复用，Plugin 是工作流分发，MCP Connection 是服务连接共享。** 它们可以独立使用，也可以组合在一起。

---

## 五、架构决策点评：为什么这样设计

阅读完源码后，有几个设计决策值得拿出来讨论。

### 基于 opencode 而不是从零造引擎

OpenWork 没有自己实现 Agent loop，而是直接使用 opencode 引擎。这个决策降低了维护成本，也意味着 OpenWork 可以直接享受 opencode 生态的能力（新模型支持、工具调用优化等）。代价是对 opencode 有强依赖，版本升级需要紧跟上游。

代码里可以看到，客户端通过 `@opencode-ai/sdk/v2/client` 与服务端通信，session 管理和 message 流转全部走 opencode 协议。服务端的角色更像是一个 opencode 的封装层和增强层——它在不改变 opencode 核心行为的前提下，叠加了 workspace 管理、云同步、审计等功能。

### EE 目录：开源核心 + 商业化组件

项目采用了 Open Core 模式。核心的桌面客户端、服务端、OpenWork MCP 都是开源的（License 文件标注为 NOASSERTION，需进一步确认具体协议）。`ee/` 目录下的 Den 组件是商业版本，需要订阅 OpenWork Cloud 或购买 Enterprise 自部署许可。

这种分法比较干净——个人和小团队用开源部分就够了；需要团队共享和管控时才需要 Den。

### Electron + React 的选择

桌面端用 Electron 而不是 Tauri 或原生方案，在 2026 年看来是个务实的选择。opencode 本身是 Node.js 生态，Electron 可以直接复用 Node 的能力（`node-pty` 做终端模拟、`better-sqlite3` 做本地存储）。用 Tauri 的话需要 Rust 桥接层，增加复杂度但不带来决定性优势。

UI 用 shadcn/ui + Base UI 而不是 Material UI 或 Ant Design，符合开发者工具类产品的审美取向——克制、现代、不花哨。

### Computer Use 模块：原生 Swift 实现

`packages/handsfree` 里有一个原生 macOS Computer Use 实现，用 Swift 写的。它的设计很有想法：

- 通过 Accessibility API 做语义化快照（生成类似 `{e1}` 的紧凑引用）
- 严格后台模式：用 `CGEvent.postToPid` 向目标进程发事件，不动系统光标
- 渲染一个轻量级的第二光标 overlay 让用户看到 Agent 在操作哪里
- MCP 独立——核心运行时只暴露 `snapshot`、`click`、`typeText`、`pressKey` 等少量接口，`MCPServer` 只是一个 thin stdio wrapper

这个实现比直接用 Playwright 或 Puppeteer 更适合 macOS 原生应用的控制场景，因为它不需要浏览器作为中介。

---

## 六、从零开始：30 分钟接入 OpenWork

### 方式一：桌面客户端（推荐新手）

1. 到 [openworklabs.com/download](https://openworklabs.com/download) 下载对应平台的安装包
2. 打开后添加一个 workspace（选本地目录）
3. 在设置里连接你的 LLM Provider（Anthropic API Key 或 OpenAI Key）
4. 开始使用

### 方式二：给现有 Agent 加 OpenWork MCP

如果你已经在用 Claude Code 或 Cursor，只需要一行命令：

```bash
# Claude Code
claude mcp add --transport http openwork https://api.openworklabs.com/mcp/agent

# Codex  
codex mcp add openwork --url https://api.openworklabs.com/mcp/agent
```

浏览器会弹出让登录 OpenWork 账号并选择组织。完成后你的 Agent 就能搜索和执行团队共享的能力了。

### 方式三：一行 prompt 让 Agent 自己安装

OpenWork 提供了一个对 Agent 友好的引导：

```text
Install OpenWork on my computer, set up my first workspace, 
and open it ready to use. Follow the steps in 
https://openworklabs.com/start.md?v=hero
```

把这段贴到 Claude Code / Codex / ChatGPT 里，Agent 会自动完成安装、workspace 创建和启动。这个设计考虑到了非技术用户——他们不需要知道什么是 MCP 或终端命令。

### 本地开发

如果你想贡献代码或做深度定制：

```bash
git clone https://github.com/different-ai/openwork.git
cd openwork
pnpm install
pnpm dev
```

如果同时开多个 worktree 做开发：

```bash
pnpm dev:worktree
```

这个命令会自动设置独立的 dev profile、自动分配 CDP 端口和 Vite 端口，还会启用 mock keychain 避免频繁弹窗。开发者体验做得很细致。

---

## 七、团队落地：从个人到组织的路径

### 1-3 人小团队

不需要 Den。每个人各自用桌面客户端或 OpenWork MCP，Skills 通过 git 仓库共享，MCP 各自配置。这阶段 OpenWork 的价值主要是跨工具——只要有一个人的 Skills 写得好，其他人换个工具也能用。

### 5-20 人团队

建议开 OpenWork Cloud 订阅。核心操作：

1. 创建组织，邀请成员
2. 把高频使用的 MCP（Notion、Linear、GitHub 等）配置为 MCP Connections——选 Individual accounts 模式，每个人用自己的 OAuth 身份
3. 把团队约定（代码审查流程、文档模板、部署检查清单）封装成 Skills，发布到 Marketplace
4. 如果有团队共享的 API Key（如 Sentry 管理员），用 One org account 模式

这阶段 OpenWork 的价值是「配置一次、全员同步」。新人入职时只要连接 OpenWork MCP，所有能力立即可用。

### 20 人以上 / 企业

考虑自部署（Self-hosted）。OpenWork 支持部署在自己的 VPC 或 On-prem 环境：

- 通过 SSO（Microsoft Entra）做身份认证
- SCIM 自动化用户 provisioning
- Desktop Policies 控制桌面端行为（限制本地模型访问、指定可用版本）
- 审计日志满足合规需求
- 模型用量管控和配额分配

企业版本还支持 `connect-link` 包——一个基于 JWT 的安全连接协议，用于在 Den 和桌面端之间建立信任关系。`packages/connect-link/src/index.ts` 里的实现基于标准 JWT claims，包含 org 信息、品牌信息和 Den 地址。

---

## 八、和同类产品的对比

OpenWork 不是唯一解决「跨工具能力共享」问题的项目，但它的切入角度比较独特。

| 维度 | OpenWork | 直接用 MCP | Claude Code 共享配置 |
|------|----------|-----------|---------------------|
| 跨 Agent 工具 | ✅ 支持 Claude Code/Codex/Cursor/任意 MCP 客户端 | ✅ 但需各自配置 | ❌ 只限 Claude Code |
| 团队管理 | ✅ Den 控制面 | ❌ 无 | ❌ 无 |
| Skill 分发 | ✅ Marketplace | ❌ 手动 | 部分（CLAUDE.md） |
| MCP 共享 | ✅ 两种账户模式 | ❌ | ❌ |
| 模型管控 | ✅ LLM Provider 管理 | ❌ | ❌ |
| 开源 | ✅ Open Core | N/A | ❌ |
| 本地优先 | ✅ 桌面客户端可纯本地 | N/A | ✅ |
| 自部署 | ✅ Enterprise | N/A | ❌ |

核心差异：OpenWork 在「个人使用」和「团队共享」之间加了一个管理层（Den），而不是让每个 Agent 工具各自为政。

---

## 九、值得关注的细节

### 配置文件用 JSONC 而不是 JSON

opencode 的配置文件（`opencode.json`）用 JSONC 格式，支持注释和尾逗号。OpenWork 的 MCP 配置读写代码（`apps/app/src/app/mcp.ts`）用了 `jsonc-parser` 的 `applyEdits` 和 `modify` 来做结构化编辑，这意味着你可以在配置文件里写注释而不会被工具破坏。

### Sandbox 隔离

workspace 类型支持 local 和 remote 两种。remote workspace 可以跑在 Docker 或 microsandbox 里，实现执行环境隔离。从 `packages/types/src/workspace.ts` 的类型定义可以看到 sandbox backend 支持 `docker`、`microsandbox`、`container` 等多种后端。这意味着远程 Agent 执行可以在隔离容器里完成，不污染宿主环境——对安全敏感的团队来说这是个刚需。

### 国际化

OpenWork 有 i18n 支持——CI 里专门有 `ci-i18n.yml` 工作流检查翻译文件完整性。`TRANSLATIONS.md` 里列出了贡献翻译的流程。对于一个面向团队协作的工具来说，多语言支持不是锦上添花而是必需品。

### 开发体验的用心

从 AGENTS.md 可以看出这个团队的开发哲学很务实：

- **Demo-Driven Development**：先写 demo 脚本（voiceover），再写代码
- **fraimz 验证**：每个功能变更需要产出 frame-by-frame 的截图证据，证明端到端流程跑通了
- **最小 diff 原则**：`Use the smallest possible diff to make a change. Then think of how to make it smaller and do that again.`
- **禁止 `any`**：TypeScript 代码不允许用 `any` 和类型断言（除非 100% 必要）

这些约束反映在代码质量上——读起来是干净的、有约束的 TypeScript 代码。

---

## 十、局限性和注意事项

说了这么多好的方面，也需要指出当前版本的一些局限：

**Den 是商业产品。** 开源部分不包含团队管理功能。如果你的团队不想付费也不想自部署 EE 版本，那么只能在个人层面使用 OpenWork。

**文档尚不完善。** 从 docs.json 的结构来看，很多功能文档是近期才加入的。API 文档依赖 OpenAPI snapshot，深度文档还比较少。如果你需要做深度定制，要做好读源码的准备。

**opencode 依赖。** 服务端绑定 opencode 引擎，意味着 opencode 的限制会传导到 OpenWork。好在 opencode 本身也是开源的，但两个项目的版本耦合需要注意。

**远程 workspace 还是 Alpha。** Cloud 上的 Shared Workspace 功能目前标注为 Alpha，生产环境使用前需要评估稳定性。

**macOS Computer Use 需要 Swift 原生编译。** `packages/handsfree` 的原生模块需要 Swift 工具链支持，跨平台编译目前不覆盖这个模块。

---

## 总结

OpenWork 解决的是一个被长期忽视的问题：**Agent 工具的能力层应该可共享、可管理，而不应该被锁在单台机器、单个工具里。**

它不是要替代 Claude Code 或 Cursor，而是要做这些工具之间的「能力总线」。你在 Claude Code 里写好的 Skill，同事在 Cursor 里也能用；你在 Den 里配置的 Notion MCP 连接，新同事入职第一天就能访问。

如果你的团队正在被「每个工具各配一遍」的重复劳动困扰，OpenWork 值得一试。如果你的使用场景是纯个人的，那么先看看 OpenWork MCP 的两个工具是否对你的工作流有帮助——接入成本只有一行命令。

从工程角度看，这个项目的代码质量不错，架构决策合理（Open Core + opencode 引擎 + MCP 协议），开发流程严谨（fraimz 验证 + 最小 diff），文档和 CI 做得到位。18.5k stars 说明社区认可度已经起来了。接下来要看的是 Den 功能的成熟速度和生态（Marketplace 插件数量）的增长。

---

*项目地址：[github.com/different-ai/openwork](https://github.com/different-ai/openwork)*  
*官网：[openworklabs.com](https://openworklabs.com)*  
*文档：[openworklabs.com/docs](https://openworklabs.com/docs)*