---
title: "Vercel Open Agents：在 Vercel 上自托管云端编码 Agent——三层架构、GitHub 集成与部署实践"
date: "2026-04-16T02:00:00+08:00"
slug: "vercel-open-agents-cloud-agent-template"
github_repo: "vercel-labs/open-agents"
source_key: "gh:vercel-labs/open-agents"
description: "Open Agents 是 Vercel Labs 开源的参考模板，用来在 Vercel 上构建和运行后台编码 Agent。它用三层架构（Web / Agent Workflow / Sandbox）把界面、Agent 逻辑和执行环境拆开，Agent 运行在沙箱之外，通过工具文件读写、搜索、Shell 与沙箱交互。本文讲清设计要点、部署流程、GitHub 集成与定制方向。"
draft: false
categories: ["技术笔记"]
tags: ["Vercel", "AI Agent", "TypeScript", "Workflow"]
---

# Vercel Open Agents：在 Vercel 上自托管云端编码 Agent

Open Agents 是 Vercel Labs 发布的一个开源参考应用，用来在 Vercel 上构建并运行**后台编码 Agent**。它把「从一个自然语言需求到一份代码改动」的完整链路打包好：Web 界面、Agent 运行时、沙箱编排、GitHub 集成，全部到位。部署之后，你给 Agent 下达任务，它就能在云端克隆仓库、改文件、跑命令、提交并推送，整个过程不需要你的电脑保持在线。

官方对它的定位很明确：**这是一个拿来 Fork 再改造的模板，不是一个开箱即用的黑盒**。这也是它和 Devin、Bolt 这类托管平台最本质的区别。

> 以下内容依据仓库 README（写作时的主分支）整理。项目迭代很快，具体参数请以官方文档和 `apps/web/.env.example` 为准。

---

## 一、先想清楚：Agent 为什么要跑在沙箱外面

在讲三层结构之前，值得先理解项目最重要的一个设计取舍。

Open Agents 的沙箱是一个隔离的 VM，里面有文件系统、Shell、Git、开发服务器和预览端口；Agent 却**不在这台 VM 里运行**。它跑在沙箱之外，通过一组工具（读文件、改文件、搜索、执行 Shell 命令）去操作沙箱。

> Agent does not run inside the VM. It runs outside the sandbox and interacts with it through tools.

这个「Agent 与沙箱分离」是整个项目的核心主张，换来四个实际收益：

- **执行生命周期解耦**。Agent 是一个可持久化的工作流，不依赖某一次 HTTP 请求的存活时间，一个任务可以跨多个持久化步骤连续执行。
- **沙箱独立休眠与恢复**。沙箱闲置可以休眠，需要时再基于快照恢复，Agent 不用跟着沙箱一起进退。
- **两边可以独立演进**。模型/供应商的选择、沙箱的实现方式，互不绑架，可以各自替换升级。
- **VM 保持纯粹**。沙箱只做一个干净的执行环境，不会因为塞进了控制逻辑而膨胀成「控制平面」。

对比一下传统做法：如果 Agent 跑在 VM 内部，它的命运就和 VM 绑定，请求一断 Agent 就退，VM 也无法独立休眠，耦合太深。Open Agents 把这条耦合线剪断了。

---

## 二、三层架构一览

```
Web ──────────────► Agent Workflow ──────────────► Sandbox VM
   (界面 / 登录       (后台持久化工作流              (执行环境：
     / 会话 / 流式UI   + 工具集)                     文件系统 / Shell / Git)
```

| 层 | 载体 | 职责 |
|------|------|------|
| **Web** | `apps/web`（Next.js） | 登录、会话、聊天界面、流式输出 |
| **Agent Workflow** | Vercel 上的 durable workflow | Agent 逻辑、多步执行、取消、工具调度 |
| **Sandbox** | Vercel Sandbox VM | 文件系统、Shell、Git、开发服务器、预览端口 |

消息进来时，Chat 请求会启动一个 workflow 运行，而不是在请求内联执行 Agent。这件事的意义在于：Agent 的每一步决策都会作为持久化的 workflow 步骤被保存下来，中途失败可以断点续跑；活跃的运行还能通过重连到已有 workflow 的流来恢复进度。

---

## 三、当前具备的能力

- **对话式编码 Agent**：提供 file、search、shell、task、skill、web 六类工具，从读改文件到执行命令再到联网取信息，一条链走通。
- **持久化多步执行**：基于 Vercel Workflow SDK，支持流式输出和取消。
- **隔离沙箱**：每次会话有独立 VM，基于快照恢复；暴露 `3000 / 5173 / 4321 / 8000` 四个端口，可跑开发服务器查看效果，闲置自动休眠，也可以指定一个基础快照作为全新沙箱起点。
- **仓库克隆与分支操作**：Agent 在沙箱内克隆仓库、切分支、干活。
- **可选的自动 commit / push / PR**：一次成功后自动提交、推送、建 PR。注意这是按偏好的功能，不是默认全开。
- **会话只读分享**：生成只读链接，对方能看完整对话和改动，但不能继续操作。
- **语音输入（可选）**：接入 ElevenLabs 转录，懒得打字可以说话。

---

## 四、动手部署：从 Fork 到跑起来

官方推荐在 Vercel 上一键部署，流程如下。用部署按钮时，Neon Postgres 会被自动开通。

1. **Fork 仓库**：`https://github.com/vercel-labs/open-agents`。
2. **导入 Vercel**：把 Fork 的仓库导入 Vercel 项目。
3. **生成会话签名密钥**：

   ```bash
   openssl rand -base64 32   # 用作 BETTER_AUTH_SECRET
   ```

4. **设置最小环境变量**，先让应用能启动：

   ```env
   POSTGRES_URL=
   BETTER_AUTH_SECRET=
   ```

5. **先部署一次**，拿到一个稳定的生产域名，后面配置 OAuth 的回调地址要用它。
6. **创建 Vercel OAuth App**，回调地址填：

   ```
   https://YOUR_DOMAIN/api/auth/callback/vercel
   ```

   然后补上并重新部署：

   ```env
   NEXT_PUBLIC_VERCEL_APP_CLIENT_ID=
   VERCEL_APP_CLIENT_SECRET=
   ```

7. **配置 GitHub（想要完整的编码 Agent 流程时再做）**。创建一个 GitHub App，配置：

   - Homepage URL：`https://YOUR_DOMAIN`
   - Callback URL：`https://YOUR_DOMAIN/api/auth/callback/github`
   - Setup URL：`https://YOUR_DOMAIN/api/github/app/callback`

   再把相关变量补上并重新部署（`GITHUB_APP_PRIVATE_KEY` 可以是带转义换行的 PEM 原文，也可以是 base64 编码的 PEM）。

8. **可选增强**：加 Redis/KV、设 `OPEN_AGENTS_RESOURCE_PROFILE=hobby` 使用 Hobby 兼容的资源默认值、填生产域名，或指定自己的沙箱基础快照。

### 授权方式的一点说明

登录认证由 **Better Auth** 负责，Vercel 和 GitHub 作为社交登录提供方，所有认证路由都由 `/api/auth/[...all]` 通配处理。GitHub 方面你**不需要另外再建一个 GitHub OAuth App**：Open Agents 直接复用 GitHub App 的 OAuth 凭据作为 Better Auth 的社交登录，同时用它颁发安装令牌来做仓库级访问。如果你的 GitHub App 是公开的，组织级安装也能顺畅工作。

---

## 五、本地开发

本地直接用 pnpm（与官方命令保持一致）：

```bash
# 1. 启用 corepack 并安装依赖
corepack enable
pnpm install

# 2. 生成本地环境文件
cp apps/web/.env.example apps/web/.env

# 3. 填好 apps/web/.env 里的必填项
# 4. 启动
pnpm web
```

如果你已经关联了 Vercel 项目，也可以用 `vc env pull` 直接把远程环境变量拉到本地。

**常用开发命令**：

```bash
pnpm web                    # 启动开发服务器
pnpm check                  # lint + 格式检查
pnpm fix                    # lint + 格式修复
pnpm typecheck              # 全包类型检查
pnpm run ci                 # 完整 CI：check + typecheck + 测试 + 迁移检查
pnpm sandbox:snapshot-base  # 刷新沙箱基础快照
```

---

## 六、环境变量速查

完整的清单在 `apps/web/.env.example`，README 给出的分类如下。核心原则是：**先能启动，再看登录，再看 GitHub**，三个层次递进，不要在第一步就堆满所有配置。

### 最小运行时（应用能启动）

```env
POSTGRES_URL=
BETTER_AUTH_SECRET=
```

### 支持登录（Vercel OAuth）

```env
NEXT_PUBLIC_VERCEL_APP_CLIENT_ID=
VERCEL_APP_CLIENT_SECRET=
```

### 支持 GitHub 仓库访问 / 推送 / PR

```env
NEXT_PUBLIC_GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_APP_ID=
GITHUB_APP_PRIVATE_KEY=
NEXT_PUBLIC_GITHUB_APP_SLUG=
GITHUB_WEBHOOK_SECRET=
```

### 可选

```env
REDIS_URL=                                # Skills 元数据缓存，不配则退回内存
KV_URL=                                   # 同上，Upstash
OPEN_AGENTS_RESOURCE_PROFILE=             # 设为 hobby 用 Hobby 兼容资源默认值
VERCEL_PROJECT_PRODUCTION_URL=             # 生产域名（元数据与回调）
NEXT_PUBLIC_VERCEL_PROJECT_PRODUCTION_URL=
VERCEL_SANDBOX_BASE_SNAPSHOT_ID=          # 全新沙箱的基础快照
ELEVENLABS_API_KEY=                       # 语音转录
```

> 提示：部分转发国外教程里出现过的 `JWE_SECRET` / `ENCRYPTION_KEY` 是更早期版本的变量名，当前项目已改用 Better Auth（`BETTER_AUTH_SECRET`）。以仓库现版本的 `.env.example` 为准。

---

## 七、仓库结构解析

```text
apps/web         Next.js 应用：Web 界面、workflow、认证、聊天 UI
packages/agent   Agent 实现：工具、子代理、技能
packages/sandbox 沙箱抽象：Vercel Sandbox 集成
packages/shared  共享工具库
```

其中 `packages/agent` 是你定制 Agent 的核心区域，`tools/`、`subagents/`、`skills/` 三个目录分别对应工具、子代理和可复用技能。`packages/sandbox` 关心的是「沙箱如何抽象、如何对接 Vercel Sandbox」这类问题。

---

## 八、几种常见方案对比

Open Agents 的价值在于「自托管 + 可改造」。把它和两款典型方案放在一起看会更容易把握它的位置：

| 维度 | Open Agents | 托管式 Agent 平台（如 Devin） | 本地 CLI Agent（如 Claude Code） |
|------|-------------|-------------------------------|----------------------------------|
| 运行位置 | 云端（Vercel） | 云端，厂商托管 | 本地机器 |
| 是否可改 | 开源可 Fork 改源码 | 封闭平台 | 脚本可按需编排 |
| 需要电脑在线 | 否 | 否 | 是，电脑需开机 |
| 上手成本 | 需自己部署与配置 | 无需部署 | 低，装一个 CLI |
| 适用场景 | 团队要掌控整个流水线 | 快速用现成服务 | 个人单机任务 |

三者的关系不是互斥，而是「自找麻烦的程度 / 掌控程度」不同。Open Agents 站在掌控那一端。

---

## 九、定制方向

既然是参考模板，定制就是它的本职。几个典型改法：

- **改 Agent 行为**：动 `packages/agent/src/` 下的 `tools/`、`subagents/`、`skills/`，增删工具、调整子代理或技能集。
- **换模型/供应商**：Open Agents 兼容 OpenAI 风格接口，可接 GPT 系列、Anthropic 的 Claude，也能通过兼容接口连本地模型。具体以当前实现为准。
- **改 Web UI**：动 `apps/web/src/` 下的组件与认证逻辑。
- **改沙箱行为**：动 `packages/sandbox/src/`，调整端口暴露、快照策略。

---

## 十、结束语

Open Agents 本质上是 Vercel 给你的一份「云端编码 Agent 的参考答卷」，把登录、持久化工作流、隔离沙箱、GitHub 集成这些容易踩坑的环节先做对了，把源码交到你手里。它适合的用法是走通一层，再看一层，按自己的业务去 Fork 改造，而不是当黑盒直接上线。

对想要掌控 Agent 基础设施、又不想从零硬造的团队来说，这是一种务实的选择。

---

## 参考资源

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/vercel-labs/open-agents |
| 在线演示 | https://open-agents.dev |
| Vercel 模板页 | https://vercel.com/templates/next.js/open-agents |

---

> 用途说明：本文是技术笔记，面向对云端 Agent 部署感兴趣的开发者和架构师。写作时点信息来自仓库主分支 README，随着项目快速迭代，请以官方最新文档为准。