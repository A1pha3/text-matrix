---
title: "Open-Inspect 源码剖析：后台 AI 编码代理如何跑起来"
date: 2026-07-13T03:01:47+08:00
categories: ["技术笔记"]
tags: ["AI-Agent", "Cloudflare", "TypeScript", "后台任务", "Sandbox"]
description: "Open-Inspect 是 Ramp 后台 AI 代理开源版。控制面用 Cloudflare+DO 承载会话,数据面用 Modal 等沙箱跑 OpenCode,GitHub App 短期令牌做凭证。"
slug: colemurray-background-agents-async-agent-framework---

# Open-Inspect 源码剖析：后台 AI 编码代理如何跑起来

> 仓库：`ColeMurray/background-agents`（[GitHub](https://github.com/ColeMurray/background-agents)），截至 2026-07-13 公开数据 2 212 stars、341 forks，主语言 TypeScript，协议 MIT。最近一次 push 2026-07-12。

## 一、什么是 Open-Inspect

Open-Inspect 是 Ramp 在 2024 年公开的内部工具 [Inspect](https://builders.ramp.com/post/why-we-built-our-background-agent) 的开源版本，由 ColeMurray 主导重写。它解决的是一类很具体的工程问题：让 AI 编码代理在后台长期运行，能从多个入口（Web UI、Slack、GitHub PR、Linear issue、Webhook）发起，能跑完整开发环境（Node.js、Python、git、浏览器、VS Code Server），能多人协作，最后还能以 PR 形式产出可评审的代码。

它的定位与一般"AI CLI 工具"显著不同：

- 不是一次性命令行 AI（Claude Code / Codex CLI 那样你盯着终端问一句答一句）。
- 不是 IDE 内的 Copilot 风格补全。
- 是 **后台运行的、长期存活的、跨团队的 AI 编码代理**——它有自己的会话状态、有自己的运行环境、有自己的事件流，能在你不看屏幕的时候把活干完。

## 二、整体架构：控制面与数据面

Open-Inspect 的架构清晰分成两层：

```
                                    ┌──────────────────┐
                                    │     Clients      │
                                    │ ┌──────────────┐ │
                                    │ │  Web / Slack │ │
                                    │ │ GitHub / Lin.│ │
                                    │ │   Webhooks   │ │
                                    │ └──────────────┘ │
                                    └────────┬─────────┘
                                             │
                                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                     Control Plane (Cloudflare)                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                   Durable Objects (per session)              │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───────────────┐    │  │
│  │  │ SQLite  │  │WebSocket│  │  Event  │  │   GitHub      │    │  │
│  │  │   DB    │  │   Hub   │  │ Stream  │  │ Integration   │    │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └───────────────┘    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              D1 Database (repo-scoped secrets)               │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬───────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                 Data Plane (Sandbox Backend)                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     Session Sandbox                          │  │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐                 │  │
│  │  │ Supervisor│──│  OpenCode │──│   Bridge  │─────────────────┼──┼──▶ Control Plane
│  │  └───────────┘  └───────────┘  └───────────┘                 │  │
│  │                      │                                       │  │
│  │              Full Dev Environment                            │  │
│  │      (Node.js, Python, git, agent-browser)                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

**控制面（Control Plane）** 在 Cloudflare 上跑：Workers 处理请求路由、Durable Objects 维护每个会话的状态、WebSocket Hub 推送实时事件流、D1 数据库存储 repo 粒度的密钥。**数据面（Data Plane）** 是真正的开发环境沙箱，由 Modal / Daytona / Vercel Sandbox / OpenComputer 等多家 sandbox 提供方之一承载。沙箱内运行 OpenCode 编码代理 + Supervisor + Bridge 进程。

这种"控制面与数据面解耦"的架构带来的好处：

- **横向扩展**：沙箱可以独立扩缩，会话状态不丢失。
- **多沙箱后端可插拔**：可以根据合规、成本、地域选择不同的 sandbox 提供方。
- **客户端轻量化**：所有客户端只与控制面交互，控制面再用 WebSocket / HTTP 与沙箱通信。

## 三、关键子系统

### 3.1 Durable Objects：会话即对象

Cloudflare Durable Objects 是 Cloudflare Workers 上的"有状态对象"，每个对象对应一份 SQLite 数据库、有自己的 CPU 时分、有自己的 WebSocket 连接。Open-Inspect 把"会话"映射成 Durable Object：每个会话都有自己的 SQLite（消息、文件操作记录、状态）、WebSocket Hub（把流式输出推给客户端）、事件流（自动化、webhook 触发）、GitHub 集成（PR 创建、commit 推送）。

会话对象是 Open-Inspect 的"心智单元"——所有客户端（Web、Slack、GitHub、Linear、Webhook）都和它交互，所有自动化都基于它的事件流触发。

### 3.2 D1：仓库粒度的密钥存储

D1 是 Cloudflare 的 serverless SQLite 数据库。Open-Inspect 用它存放 per-repo 的 secrets，避免 secrets 漂到沙箱配置里。注入到沙箱时，沙箱通过加密通道从控制面拉到本地环境变量，scope 控制在 global / per-repo / per-environment 三档。

### 3.3 Sandbox Runtime

沙箱是会话运行的真实环境。Open-Inspect 在沙箱里跑的是 OpenCode（一款与 Claude / OpenAI 等多模型兼容的编码代理运行时）。Supervisor 进程负责会话生命周期管理（启动、暂停、恢复、终止），Bridge 进程负责和 Control Plane 通信（发日志、回消息、上报状态）。

沙箱支持的可选 backend：

- **Modal**：云端 sandbox 基础设施
- **Daytona**：云端开发 sandbox
- **Vercel Sandbox**：Vercel 的 serverless 沙箱
- **OpenComputer**：专用模板沙箱

多种 backend 通过统一的沙箱接口抽象，运维团队可以根据成本、合规、地域选配。

### 3.4 仓库生命周期脚本

Open-Inspect 支持在仓库内放两个可选的启动脚本：

```bash
# .openinspect/setup.sh - 装依赖（镜像构建 / 新会话时跑）
#!/bin/bash
npm install
pip install -r requirements.txt
```

```bash
# .openinspect/start.sh - 启动运行时服务（每次会话启动都跑）
#!/bin/bash
docker compose up -d postgres redis
```

- `setup.sh`：在 image build 和 fresh session 模式跑；在 prebuilt-image 和 snapshot-restore 模式跳过
- `start.sh`：在 fresh / prebuilt-image / snapshot-restore 模式都跑
- 默认超时：`SETUP_TIMEOUT_SECONDS=300`、`START_TIMEOUT_SECONDS=120`
- 两个脚本会收到 `OPENINSPECT_BOOT_MODE` 环境变量（`build`、`fresh`、`repo_image`、`snapshot_restore`）
- `start.sh` 失败是严格的——会让整个会话启动失败
- 钩子里的 git 操作可以通过控制面代理鉴权到其他私有仓库

这套机制让团队可以把"启动开发环境的全套动作"沉淀进仓库本身，Open-Inspect 负责调度，而不是每个新人都要手动跑一遍。

## 四、快速启动机制

后台代理最大的体验问题是"每次发起任务都要等环境"。Open-Inspect 用三层缓存解决这个问题：

**文件系统快照**：每次提示词结束后保存沙箱状态，后续会话从快照恢复而不是重新 clone。

**预构建镜像**：可以为每个仓库（Settings > Images）或环境（Settings > Environments）开关预构建镜像。镜像每 30 分钟重建一次，包含最新 commit 与依赖。

**主动预热**：你刚开始打字、沙箱就已经开始启动了。`first-prompt latency` 因此可以做到接近零感知。

## 五、多模型支持

Open-Inspect 支持多种 AI 模型，按 README 列出的清单：

| Provider | 模型 |
|---------|------|
| Anthropic | Claude Haiku 4.5, Sonnet 4.5/4.6, Opus 4.5/4.6/4.7/4.8, Fable 5 |
| OpenAI | GPT 5.4, GPT 5.5, 5.3 Codex, 5.3 Codex Spark |
| OpenCode Zen | Kimi K2.5/K2.6, MiniMax M2.5, Qwen3.7 Max, GLM 5/5.1（opt-in） |
| Z.AI Coding Plan | GLM 5.2（opt-in） |

每个会话都可以选模型，并能配 reasoning effort 控制。OpenAI 模型支持通过 OAuth 接你的 ChatGPT 订阅，不需要额外 API key。

## 六、客户端集成

Open-Inspect 不只是一个 Web UI，它还提供多个客户端集成入口：

- **Web UI**：完整的会话管理 + 实时流 + 模型/推理强度选择器 + 终端面板 + 多人在场指示
- **Slack Bot**：@ 提及或 DM 启动会话，回帖 thread 携带结果；每个用户的模型与分支偏好可在 App Home 配
- **GitHub Bot**：PR 打开时自动 review，或对 PR 评论里的 @mention 做响应；可按仓库配置
- **Linear Bot**：在 issue 上 mention 或指派代理启动编码会话，把进度活动 post 回 issue，并链接产出的 PR
- **Webhooks**：通过认证 HTTP POST 从任何外部系统触发会话

这种"多入口"对应的是后台代理的真实使用场景：开发者可能从 Linear 上的某个工单触发、从 Sentry 报警触发、从 Slack 上的对话触发、从 CI 失败触发——而不是每次都打开 Web UI。

## 七、自动化

自动化（Automation）是 Open-Inspect 的"无人值守"模式：

- **Cron schedules**：时/日/周/月或自定义 5 字段 cron，带时区
- **Sentry alerts**：新错误 / 回归 / 关键指标告警自动 triage
- **Inbound webhooks**：用 JSONPath 条件过滤决定哪些 payload 触发会话
- **多仓库 fan-out**：一个定时自动化可以跨最多 10 个仓库，每个仓库开独立会话和 PR
- 连续 3 次失败自动暂停；手动触发按钮；完整运行历史

可以把自动化理解为："每次 cron 触发都跑一个新会话；每次 webhook 都对应一个新任务；不需要人看着"。

## 八、子任务并行

Open-Inspect 的代理可以 spawn 出多个并行子任务：

```typescript
// 在代理运行时调用
spawnTask({
  repo: 'org/submodule',
  prompt: '...',
  branch: 'feature-x',
});
```

- 父任务继续工作，子任务在独立沙箱、独立分支并行跑
- 用 `get-task-status`、`cancel-task` 协调
- 有 depth limit 和 per-repo guardrails

这让一个"重构整套 monorepo"的任务可以分解成"重构每个子模块"的并行子任务，父任务在收集子任务结果后做整合 PR。

## 九、沙箱环境

每个会话沙箱预装了：

- **Node.js 22**
- **Python 3.12**
- **Bun**
- **git**
- **GitHub CLI**
- **build-essential**

还提供：

- **agent-browser CLI**：无头 Chromium，支持截图、视觉 diff、UI 验证
- **code-server**：可选的浏览器版 VS Code，连接到会话工作区
- **Web terminal**：ttyd 驱动的终端，从会话 UI 访问
- **端口隧道**：最多暴露 10 个开发服务器端口，通过加密隧道；URL 在 `.tunnels.env` 里，`.openinspect/start.sh` 跑前可用

密钥存储 AES-256-GCM 加密，按 global / per-repo / per-environment 三档 scope，spawn 时作为环境变量注入。支持 `.env` 批量粘贴导入。

## 十、Commit Attribution 与 PR 创建

Open-Inspect 强制让 commit 归属于发提示词的真实用户，而不是 bot 账号：

```typescript
// Configure git identity per prompt
await configureGitIdentity({
  name: author.scmName,
  email: author.scmEmail,
});
```

PR 创建路径按登录方式分两支：

- **GitHub OAuth 登录**：用用户的 OAuth token 创建 PR，能正确归属用户，且只能对用户有写权限的仓库开 PR。
- **其他登录方式（Google 等）**：用户的 SCM token 不存在，PR 走共享 GitHub App bot 账号。

这是 Open-Inspect 信任模型的关键部分——读 README 就能看到：所有用户共享同一个 GitHub App 凭证，所有用户对所有共享仓库都有访问权。

## 十一、安全模型与单租户约束

Open-Inspect 明确**只支持单租户部署**——所有用户都是同一组织、同一信任域的成员，能访问相同仓库。原因是它使用共享的 GitHub App 安装完成 git 操作（clone、fetch、push），控制面在 server-side 签发短期 installation token，再通过 git credential helper 按需代理给沙箱。

这意味着：

- 所有用户共享同一组 GitHub App 凭证。GitHub App 必须装在组织仓库上，任何用户都能访问 App 有权限的仓库。
- 不做 per-user 仓库访问校验。
- 对于 GitHub 登录的用户，PR 用他们的 OAuth token 创建；对于其他登录方式，回落到共享 GitHub App bot。

这种设计的来源是 Ramp Inspect 本身是给内部员工用的。多租户场景需要：

- 每个租户独立的 GitHub App 安装
- 在会话创建时做访问校验
- 数据模型层做租户隔离

部署建议（README 给出）：

1. 部署在组织 SSO / VPN 之后
2. GitHub App 仅安装在目标仓库
3. 限制登录：配置允许的 GitHub 用户、邮箱域名、活跃的 GitHub 组织成员（`ALLOWED_GITHUB_ORGS`）
4. GitHub App 安装时只勾选特定仓库，不要"All repositories"

## 十二、token 架构一览

| Token 类型 | 用途 | 作用域 |
|-----------|------|--------|
| GitHub App Token | 代理 git clone/fetch/push | 所有 App 安装的仓库 |
| User OAuth Token | 创建 PR、获取用户信息 | 用户有权限的仓库 |
| Sandbox Auth Token | 沙箱到控制面的会话调用 | 单会话 |
| WebSocket Token | 实时会话认证 | 单会话 |

## 十三、源码读法建议

Open-Inspect 是一个 monorepo，`packages/` 下分多个包：

| Package | 描述 |
|---------|------|
| `control-plane` | Cloudflare Workers + Durable Objects |
| `web` | Next.js Web 客户端 |
| `sandbox-runtime` | 沙箱内共享的代理运行时 |
| `modal-infra` | Modal sandbox 基础设施 |
| `daytona-infra` | Daytona snapshot 基础设施 |
| `opencomputer-infra` | OpenComputer 模板基础设施 |
| `slack-bot` | Slack 集成（消息起会话） |
| `github-bot` | GitHub 集成（自动 review、@mention） |
| `linear-bot` | Linear 集成（issue → 编码会话） |
| `shared` | 共享类型与工具 |

读源码建议的顺序：

1. **`packages/control-plane/`**：先理解 Durable Objects 上的会话对象模型（SQLite schema、状态机、WebSocket Hub）
2. **`packages/sandbox-runtime/`**：看 Supervisor + Bridge 怎么和控制面通信
3. **`packages/web/`**：Next.js 客户端怎么订阅 WebSocket 接收流式输出
4. **`packages/modal-infra/`**（或其他 `*-infra`）：看 sandbox 怎么被实例化、怎么挂载 lifecycle script
5. **`packages/slack-bot/`**：用一个最简单的集成看多入口如何复用控制面

## 十四、与 Claude Code / Devin / Codex 的差异

- **相对 Claude Code CLI**：Claude Code 是个人终端工具，按提示词交互；Open-Inspect 是后台常驻代理，从多个入口触发，能跨会话保留状态。
- **相对 Devin**：Devin 是 Cognition Labs 的商业产品，定位接近；Open-Inspect 是开源版本，单租户、自托管、可扩展。
- **相对 Codex CLI / Codex Web**：Codex 是 OpenAI 的 CLI 与 Web 端产品；Open-Inspect 模型无关，能切换 Anthropic / OpenAI / OpenCode Zen / Z.AI 等。
- **相对 Cursor Background Agent**：Cursor 是 IDE 商业产品，Open-Inspect 是平台开源，可独立部署到自有 Cloudflare / Modal / Daytona。

## 十五、采用建议

适合：

- 想自建"团队级后台 AI 编码代理"的工程团队
- 已有 GitHub App、Webhook、Slack / Linear 工作流，想把 AI 代理嵌进现有流程
- 需要多入口、多模型、长期会话状态、可观测性的组织
- 对数据驻留有要求（能部署在自有 Cloudflare + 自选 sandbox 后端）

不适合：

- 个人独立开发者：复杂度太高，单人用 Claude Code CLI / Codex CLI 足矣
- 多租户 SaaS：Open-Inspect 明确不支持，需要先做租户隔离改造
- 无 GitHub / Slack / Linear 的团队：入口价值大减
- 对完整审计 / SOC2 / 严格权限管理有要求的场景：单租户共享 GitHub App 不满足

## 十六、上手步骤

按 README 给出的文档路径：

1. **`docs/SETUP_GUIDE.md`**：本地开发 + 贡献者 + 部署三种路径
2. **`docs/GETTING_STARTED.md`**：部署说明
3. **`docs/HOW_IT_WORKS.md`**：架构与核心概念
4. **`docs/AUTOMATIONS.md`**：定时任务与告警触发
5. **`docs/AVAILABLE_MODELS.md` / `docs/OPENAI_MODELS.md`**：模型选择与 OpenAI OAuth 设置

如果只是想本地跑通贡献者流程，建议：

```bash
git clone https://github.com/ColeMurray/background-agents
cd background-agents
pnpm install
pnpm dev
```

然后访问 `http://localhost:3000`（Next.js Web 客户端），用 GitHub OAuth 登录，开一个新会话验证链路通畅。

## 十七、小结

Open-Inspect 把"后台 AI 编码代理"从一种商业产品范式变成可自托管的开源参考实现。它的核心贡献是把会话状态、运行沙箱、客户端入口、自动化触发这几条原本互相纠缠的线，用 Cloudflare Workers + Durable Objects + 任意 sandbox backend 的组合清晰拆开。同时它也明确了边界：单租户、共享 GitHub App、可观察、可扩展，但不做多租户隔离。

对于希望把 AI 编码代理作为"组织基础设施"来构建的团队，Open-Inspect 是当前最完整的开源参考之一；对于个人开发者，它的复杂度远超 Claude Code CLI 直接使用，建议只在团队场景下评估采用。