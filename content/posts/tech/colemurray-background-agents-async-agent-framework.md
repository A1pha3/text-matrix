---
github_repo: "ColeMurray/background-agents"
source_key: "gh:ColeMurray/background-agents"
title: "Open-Inspect 源码剖析：后台 AI 编码代理，从能跑到能管"
date: 2026-07-13T03:01:47+08:00
lastmod: 2026-10-04
categories: ["技术笔记"]
tags: ["AI Agent", "Cloudflare", "TypeScript"]
description: "Open-Inspect 是受 Ramp Inspect 启发的开源后台编码代理平台。本文按 2026-10-04 的 main 分支复核：双 harness 运行时、七个 provider 六十五个模型、团队级访问控制与审计，以及没变的单租户边界。"
slug: colemurray-background-agents-async-agent-framework
---
# Open-Inspect 源码剖析：后台 AI 编码代理，从能跑到能管

> 仓库：`ColeMurray/background-agents`（[GitHub](https://github.com/ColeMurray/background-agents)）。本文发表时（2026-07-13）读数 2,212 stars、341 forks；复核时（2026-10-04）3,314 stars、478 forks，主语言 TypeScript，协议 MIT，当天仍有提交。仓库不打版本 tag、不发布 release，所有能力都以 main 分支交付——文中机制描述均以 2026-10-04 的 main 为准，与发文时的差异单独标出。

## 一、先说这三个半月变了什么

本文初版发表时，Open-Inspect 的卖点是"后台代理怎么跑起来"：会话进 Durable Object、代码进沙箱、产出是 PR。10 月复核 main 分支，答案多了一层——跑起来之后，谁有权碰它。

两条主线的变化最大。其一是运行时从"只跑 OpenCode"变成 harness（代理运行时）抽象：沙箱里多了一个 Claude Agent harness，跑 Anthropic 的 Claude Agent SDK，可以接 Claude 订阅而不是 API key，会话创建时二选一并终身固定。其二是安全模型从"共享凭证、互信到底"长出了团队级访问控制：四个工作区角色、会话三档可见性、审计日志，README 还专门加了一句"Teams add internal access controls, not tenant isolation"——单租户定位没变，"内部谁都能碰一切"的默认假设变了。

模型目录从四个 provider 扩到七个、六十五个模型 ID；子任务工具整体改名；Node.js 从 22 升到 24。下文按现在的形态讲，变化处标注发文时的样子。

## 二、它是什么

Open-Inspect 是受 Ramp 内部工具 Inspect 启发的开源重写。Ramp 在 2026 年 1 月 12 日发了篇博客讲他们怎么给非工程岗位的员工配一个"什么都验证得了"的编码代理（[Why We Built Our Own Background Agent](https://builders.ramp.com/post/why-we-built-our-background-agent)）；仓库 main 分支的 `docs/ramp-inspect-agent.md` 收录了这篇的摘录。Cole Murray 于 2026 年 1 月 25 日建仓重写——所以它是社区实现，不是 Ramp 的官方开源，README 自己的措辞是 "inspired by"。

它解决的问题很具体：让 AI 编码代理在后台长期运行，从 Web UI、Slack、GitHub PR、Linear issue、Webhook 任意入口发起，跑在带完整开发环境的沙箱里，支持多人实时协作，最后以 PR 形式交付可归属到真实用户的代码。它不是你盯着终端用的 CLI，也不是 IDE 里的补全——它有自己的会话状态、运行环境和事件流，在你关掉屏幕后继续干活。

## 三、整体架构：控制面与数据面

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
│  │  ┌───────────┐  ┌────────────┐  ┌───────────┐                │  │
│  │  │ Supervisor│──│  Harness   │──│   Bridge  │────────────────┼──┼──▶ Control Plane
│  │  └───────────┘  │ (OpenCode  │  └───────────┘                │  │
│  │                 │  or Claude)│                                │  │
│  │                 └────────────┘                                │  │
│  │                      │                                        │  │
│  │              Full Dev Environment                             │  │
│  │      (Node.js, Python, git, agent-browser)                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

**控制面**跑在 Cloudflare 上：Workers 处理请求路由，Durable Objects 维护每个会话的状态，WebSocket Hub 推流式事件，D1 存仓库粒度的密钥和审计事件。**数据面**是真正的开发环境沙箱，由五家 sandbox 后端之一承载（Modal、Daytona、Vercel Sandbox、OpenComputer、E2B——发文时是四家，E2B 是后来加的）。沙箱内三个进程：Supervisor 管会话生命周期，Bridge 跟控制面通信（每 30 秒一次心跳，上报启动阶段），中间就是代理运行时本体。

这么拆的好处没变：沙箱可以独立扩缩而会话状态不丢；五家后端走统一接口，按成本、合规、地域选配；所有客户端只跟控制面说话。

## 四、关键子系统

### 4.1 Durable Object：一个会话一个对象

每个会话映射成一个 Durable Object，自带 SQLite（消息、文件操作记录、状态）、WebSocket Hub 和事件流。所有客户端入口和所有自动化触发都汇聚到这个对象上——它是系统的心智单元。会话表里有 `harness` 字段，取值 `'opencode'` 或 `'claude'`，创建时写入、之后不可改（源码注释原话 "fixed at create"，与 base branch 同一待遇）。

### 4.2 D1：密钥与审计

D1 存 per-repo 的密钥，AES-256-GCM 加密，按 global / per-repo / per-environment 三档 scope，会话启动时作为环境变量注入，支持 `.env` 批量粘贴导入。审计日志也落在这：`authorization_audit_events` 表，官方文档明说审计写入是 best effort，不作合规级保证。

### 4.3 沙箱运行时：双 harness

沙箱内真正跑模型对话的是 harness。**OpenCode** 是内置默认，能跑目录里全部模型，Anthropic 模型在它上面只认 `ANTHROPIC_API_KEY`。**Claude Agent** 是第二选择，在沙箱里跑 Claude Agent SDK，只跑 Anthropic 模型，认证可以用 API key，也可以用控制面代持的 Claude 订阅账号——用户从不在沙箱里登录，凭证始终在平台手里。它还原生读仓库的 `CLAUDE.md`。这套双引擎结构落在 `packages/sandbox-runtime/src/sandbox_runtime/harness/` 下：`opencode.py` 和 `claude.py` 各自实现，`claude_stager.py` 负责把 SDK 暂存进沙箱。

启动顺序是固定的八阶段：建沙箱 → Bridge 起连（`starting`）→ git clone（`sync`）→ setup 脚本（`setup`）→ start 脚本（`start`）→ 安装 Managed Skills（`skills`）→ 代理启动（`harness`）→ 就绪（`ready`）。判定就绪的是运行时自己的 `ready` 事件，不是连接建立。启动期间的提示词会排队等就绪。

### 4.4 仓库生命周期脚本

仓库可以在 `.openinspect/` 下放两个可选脚本：

```bash
# .openinspect/setup.sh - 装依赖（镜像构建 / 全新会话时跑）
#!/bin/bash
npm install
pip install -r requirements.txt
```

```bash
# .openinspect/start.sh - 启动运行时服务（每次会话启动都跑）
#!/bin/bash
docker compose up -d postgres redis
```

两条铁律：`setup.sh` 在全新会话里失败只算警告、boot 继续，在镜像构建模式里失败则是致命的；`start.sh` 只要存在且失败，整个会话启动就失败。两个脚本都收到 `OPENINSPECT_BOOT_MODE` 环境变量（`build`、`fresh`、`repo_image`、`snapshot_restore` 四档），钩子里的 git 操作可以借共享凭证访问同 SCM 主机上的其他私有仓库。

发文时这对脚本有各自的超时常量（`SETUP_TIMEOUT_SECONDS=300`、`START_TIMEOUT_SECONDS=120`）；现行设计去掉了 hook 专属超时，改用一个总预算：`SANDBOX_BOOT_TIMEOUT_MS`，默认 30 分钟，按整个会话启动流程计量，脚本自己想卡截止时间就自己加。脚本进度会实时上报到会话界面，但 stdout 和 stderr 会被丢弃、不收集不展示——镜像构建连进度都不报，因为它没有可挂的会话。

## 五、快速启动：三层缓存

后台代理最伤体验的是"每次发任务都等环境"。三层缓存在发文时就有了，至今没变：

- **文件系统快照**：每次提示词结束后保存沙箱状态，后续会话直接恢复，不重新 clone。
- **预构建镜像**：按仓库（Settings > Images）或环境（Settings > Environments）开关，每 30 分钟重建一次，带上最新 commit 和依赖。
- **主动预热**：你刚开始打字、还没按回车，沙箱就开始启动了。

首条提示词的等待时间因此可以压到接近无感。

## 六、多模型支持：三个月从 24 款到 65 款

`docs/AVAILABLE_MODELS.md` 是当前清单的权威出处（2026-10-04 读数）：

| Provider | 模型数 | 默认状态 | 认证方式 |
|---------|------|---------|---------|
| Anthropic | 13（Haiku 4.5，Sonnet 4.5–5.5，Opus 4.5–5.5，Fable 5/5.1） | 启用 | API key；订阅仅限 Claude Agent harness |
| OpenAI | 9（GPT 5.4/5.5、5.6 Sol/Terra/Luna、GPT-6 Astra/Sol/Luna、6.1 Sol） | 启用 | API key 或 ChatGPT 订阅 OAuth |
| xAI / SuperGrok | 4（Grok 4.5–4.7、Grok Build 0.1） | opt-in | `XAI_API_KEY` 或 SuperGrok 订阅 OAuth |
| OpenCode Zen | 8（Kimi、MiniMax、Qwen、GLM 等） | opt-in | `OPENCODE_API_KEY`，按 token 计费 |
| OpenCode Go | 27（同上再加 DeepSeek、MiMo、混元、LongCat 等） | opt-in | 同一 `OPENCODE_API_KEY`，包月配额 |
| Z.AI Coding Plan | 2（GLM 5.2/5.3） | opt-in | `ZHIPU_API_KEY` |
| DeepSeek | 2（V4 Flash/Pro） | opt-in | `DEEPSEEK_API_KEY` |

发文时的清单是 24 款（`docs/AVAILABLE_MODELS.md` 口径，含初版文章没提的 DeepSeek 两款）；xAI 和 OpenCode Go 通道是这三个月新增的，Anthropic、OpenAI 和 OpenCode Zen 的目录也都各扩了一圈。

几个值得知道的细节。**harness 决定模型面**：Claude Agent harness 只跑 Anthropic 模型，其余全部只在 OpenCode 上跑；会话内临时切一个当前 harness 跑不了的模型会被直接拒绝，而不是静默换掉。**订阅会计入通道**：Claude 订阅账号只对 Claude Agent 会话生效，Slack、GitHub 发起的会话固定跑 OpenCode、只认 API key，所以设置默认订阅账号不会弄坏用不了它的会话；Linear 集成有全局和每仓库的 harness 设置（默认 OpenCode）。**Go 通道有滚动限额**：包月制，5 小时窗口用 20% 月额、一周用 50%、一月用 100%，无人值守会话钉在 Go 模型上可能中途耗尽配额而失败，官方文档建议无人值守场景别用 Go 模型。**同一模型多个入口**：`glm-5.2` 同时存在于 Zen、Go、Z.AI 三处，`grok-4.6` 在 xAI 和 Go 两处——同一个模型、三种记账，选哪个入口是在选账单。文档还记录了一处诚实处理：Go 官方列 28 个模型，其中 `minimax-m2.5` 在仓库钉住的 OpenCode 版本里解析不了，Open-Inspect 干脆不提供这个选项，而不是给你一个点了就报错的条目。

每个会话都可以选模型并配 reasoning effort（推理强度），各模型的档位和默认值都写在清单表里。

## 七、客户端集成

- **Web UI**：完整会话管理、实时流、模型/推理强度选择器、终端面板、多人在场指示。
- **Slack Bot**：@ 提及或 DM 启动会话，回帖进 thread；提示词可以带 PNG、JPEG、WebP、GIF 附件（发文时不支持）；每个用户的模型与分支偏好在 App Home 配。
- **GitHub Bot**：PR 打开时自动 review，或响应 PR 评论里的 @mention，按仓库配置。
- **Linear Bot**：issue 上 mention 或指派代理启动会话，进度活动回帖到 issue 并链接产出的 PR。
- **Webhooks**：认证 HTTP POST 从任意外部系统触发会话。

代理这边还有一个容易被漏掉的工具：`slack-notify`，让 agent 在会话过程中主动往 Slack 发通知。它不是裸调用——目标频道受会话可见性和 team 归属约束，未配置通知功能、仓库禁用、会话无权发到该频道等五类拒绝原因各有明确的提示语，源码里连"不要未经用户允许换个频道重试"这样的行为指引都写给了模型。

多入口对应的是真实触发场景：从 Linear 工单、Sentry 告警、Slack 对话、CI 失败发起，而不是每次都打开 Web UI。

## 八、自动化

自动化是无人值守模式，发文时的五类触发器全部保留，新增一类：

- **Cron schedules**：时/日/周/月或自定义 5 字段 cron，带时区。
- **Sentry alerts**：新错误、回归、关键指标告警自动 triage。
- **GitHub workflow runs**（新增）：GitHub Actions 工作流跑完时启动会话，可按 workflow 名和 conclusion（成功/失败）过滤。
- **Inbound webhooks**：JSONPath 条件过滤决定哪些 payload 触发会话。
- **多仓库 fan-out**：一个定时自动化最多跨 10 个仓库，每个仓库开独立会话和 PR。
- 连续 3 次失败自动暂停；有手动触发按钮和完整运行历史。

把它理解成"每次触发都开一个新会话，不需要人看着"就够了。自动化本身的访问控制也进了这套体系：自动化有归属（个人或团队），成员被停用后其自动化的处理规则写在 AUTH 文档里。

## 九、子会话：改名与补课

发文时这套机制叫 Sub-Task Spawning，工具名是 `spawn-task`、`get-task-status`、`cancel-task`。现行改名 Child Sessions，工具面扩成四个：`spawn-child` 建独立沙箱、独立分支的子会话并立即返回；`send-child-prompt` 往一个已存在的直接子会话排队追加指令；`get-child-status` 和 `cancel-child` 负责查询与取消。父会话继续干活，子会话并行跑；有深度上限和按仓库的护栏（源码里会话表带 `spawn_depth` 字段，树遍历另有硬顶防失控）。子会话继承父会话的 harness。顺带更正初版的一个错误：初版写过一个 `spawnTask({repo, prompt, branch})` 的 TypeScript 调用示例，仓库里从来没有这个函数——这些是 agent 在会话内调用的工具，名字是上面的连字符形式，README 从发布起就是这么写的。

一个"重构整个 monorepo"的任务因此可以拆成每模块一个子会话并行跑，父会话收结果做整合 PR。

## 十、沙箱环境

每个会话沙箱预装 Node.js 24（发文时是 22）、Python 3.12、Bun、git、GitHub CLI、build-essential。另有：

- **agent-browser CLI**：无头 Chromium，支持截图、视觉 diff、UI 验证。
- **code-server**：可选的浏览器版 VS Code，连到会话工作区。
- **Web terminal**：ttyd 驱动，从会话 UI 访问。
- **端口隧道**：最多暴露 10 个开发服务器端口，走加密隧道；URL 写在沙箱内 `/workspace/.tunnels.env`，`.openinspect/start.sh` 执行前就可用。

## 十一、Commit 归属与 PR 创建

commit 强制归属到发提示词的真实用户而不是 bot 账号，这段代码从发文到现在一字未动：

```typescript
// Configure git identity per prompt
await configureGitIdentity({
  name: author.scmName,
  email: author.scmEmail,
});
```

PR 创建路径分两支：GitHub 登录的用户用他自己的 OAuth token 建 PR，归属正确、且只能对有写权限的仓库开；其他登录方式（如 Google）的用户没有 SCM token，PR 落到共享 GitHub App bot 名下。AUTH 文档把这条边界写得更细：沙箱的 git 凭证只覆盖该会话持久化的仓库（team 归属的会话再叠加当前 team 的授权），镜像构建拿到的是另一枚范围更窄的 `VCS_CLONE_TOKEN`。

## 十二、安全模型：单租户没变，内部控制长了牙

单租户定位从发文到现在没变过：所有用户都是同一组织的可信成员，共享一套 GitHub App 安装，系统在创建会话前不会去比对用户个人的 GitHub 仓库权限。要做多租户，官方列的三件事也还是那三件：每租户独立的 App 安装、会话创建时做访问校验、数据模型层做租户隔离。

变的是"可信成员"内部怎么管。这套东西发文时完全没有，现在占掉了 AUTH 文档的大半篇幅：

- **四个工作区角色**：Owner、Administrator、Member、Viewer，十七项能力逐项列表——比如只有 Owner/Administrator 能动共享设置、集成和密钥，Viewer 只读，转移工作区所有权是 Owner 独占动作。
- **团队（Teams）**：可选。有成员和 lead、开放或邀请制、默认可见性；建团队不会移动已有的会话，会话归属（个人或某团队）一经创建即固定，不能在团队之间或与工作区之间转移。
- **会话三档可见性**：`workspace`（全体可读）、`team`（成员加 Owner/Administrator）、`private`（仅所有者和显式协作者）。`team` 档的读边界要开 `TEAMS_ENFORCEMENT=on` 才生效，部署默认是 `shadow` 模式——只记录"如果开了会拦掉什么"，不影响实际访问，方便先观察再收紧。
- **private 在所有模式下强制**。Owner 有一条"破窗读取"路径：按 ID 读、被审计、不出现在任何列表里，且不给提示词和沙箱权限，除非把自己加为协作者；Administrator 没有破窗权；无人格的 bot 服务读不了 private 会话。
- **team 归属会话的所有非读操作都要求当前是团队成员**——包括所有者本人、团队 lead、Owner 和 Administrator。开了 enforcement 后删除会话还需要 `sessions.delete` 权限加上所有者/lead/管理员身份。协作者是一种会话级授权而非角色：team 会话的协作者必须是当前团队成员，退队即失访问。

还有两条边界值得部署者背下来。其一，凭证按需签发但会缓存在沙箱磁盘上——快照可能把凭证一起存下来，而收回授权不会立即吊销已发出的 token，它们活到过期为止。其二，GitLab 凭证是部署级 PAT 而不是每会话一枚，共享面比 GitHub 侧更宽。

部署建议四条与发文时相同：部署在组织 SSO/VPN 之后；GitHub App 只装到目标仓库；配置允许登录的用户、邮箱域名或 GitHub 组织成员（`ALLOWED_GITHUB_ORGS`）；装 App 时勾选具体仓库而不是 "All repositories"。

## 十三、源码读法

monorepo，`packages/` 下现在有 14 个目录——README 的包表只列了 11 个，`vercel-infra`、`sandbox-images`（沙箱镜像构建，`toolchain.json` 钉住 OpenCode 版本）和 `docs`（Next.js 文档站）没进表，以目录为准：

| Package | 描述 |
|---------|------|
| `control-plane` | Cloudflare Workers + Durable Objects |
| `web` | Next.js Web 客户端 |
| `sandbox-runtime` | 沙箱内共享的代理运行时（Python，双 harness 在 `harness/` 下） |
| `modal-infra` | Modal sandbox 基础设施 |
| `daytona-infra` | Daytona snapshot 基础设施 |
| `vercel-infra` | Vercel Sandbox 基础设施 |
| `e2b-infra` | E2B 沙箱模板基础设施 |
| `opencomputer-infra` | OpenComputer 模板基础设施 |
| `sandbox-images` | 沙箱镜像构建（工具链钉版） |
| `slack-bot` | Slack 集成 |
| `github-bot` | GitHub 集成（自动 review、@mention） |
| `linear-bot` | Linear 集成（issue → 编码会话） |
| `shared` | 共享类型与工具 |
| `docs` | 文档站 |

建议顺序：先读 `control-plane` 的会话对象模型（SQLite schema、状态机、WebSocket Hub），再读 `sandbox-runtime` 的 Supervisor + Bridge + harness 通信，然后 `web` 看客户端怎么订阅流式事件，`modal-infra` 或其他 `*-infra` 看沙箱怎么实例化、怎么挂生命周期脚本。发文时列的 10 个包都还在，没搬过位置。

## 十四、与 Claude Code / Devin / Codex 的差异

- **相对 Claude Code CLI**：Claude Code 是个人终端工具，交互式问答；Open-Inspect 是后台常驻平台，多入口触发、跨会话保留状态、面向团队。有意思的是它反过来集成了 Claude——通过 Claude Agent harness 跑 Claude Agent SDK。
- **相对 Devin**：Devin 是 Cognition 的商业托管产品，定位最接近；Open-Inspect 开源、单租户、自托管、五家沙箱后端可选。
- **相对 Codex CLI / Codex Web**：Codex 是 OpenAI 的单家产品；Open-Inspect 模型无关，七家 provider 可切。
- **相对 Cursor Background Agent**：Cursor 是 IDE 厂商的托管后台代理；Open-Inspect 平台开源，能部署到自己的 Cloudflare 账号和自选沙箱。

## 十五、采用建议

适合：想自建团队级后台编码代理、且有能力维护它的工程团队；已有 GitHub App、Webhook、Slack / Linear 工作流想把代理嵌进去的组织；对数据驻留有要求、想部署在自有 Cloudflare 加自选沙箱的团队。

不适合，或者先别急：个人开发者——复杂度远超一个 CLI 的收益；需要多租户 SaaS 化的场景——明确不支持，租户隔离要自己造；没有 GitHub / Slack / Linear 的团队——入口价值大减。

两个决策相关的现状。第一，项目不打 tag 不发 release，所有更新直接进 main，采用它意味着接受一条快速移动的分支（发文到复核三个半月，模型目录、安全模型、工具名都动过）。钉 commit 部署、订阅仓库通知，是跟上它的最低配置。第二，关于审计与合规：现在的审计日志和 shadow 模式给了内部治理相当的工具，但官方明说审计写入是 best effort，共享 GitHub App 的单租户边界也没有变——把它当"带访问控制的内部基础设施"评估是准确的，当"满足外部合规的托管平台"评估不是。

## 十六、上手路径

发文时初版给的"clone 后 `pnpm dev`"是错的——仓库从建库起就用 npm，根 `package.json` 里也从来没有过 `dev` 脚本。真实路径在 `docs/SETUP_GUIDE.md`，按目标分三条：Path A 本地跑 Web UI（连已部署的后端，约 10–20 分钟）、Path B 本地贡献代码（lint/typecheck/test，约 15–30 分钟）、Path C 部署完整自有栈（约 1–3 小时，走 `docs/GETTING_STARTED.md` 的十步，从建 GitHub App、配 Terraform 到引导工作区 Owner 和创建第一个团队）。

本地开发的最短启动序列（Path A，需要已有控制面）：

```bash
git clone https://github.com/ColeMurray/background-agents
cd background-agents
bash .openinspect/setup.sh          # 装依赖、构建 shared、装 git hooks
cp packages/web/.env.example packages/web/.env.local
# 编辑 .env.local：填 GITHUB_CLIENT_ID/SECRET（必填）、
# NEXTAUTH_URL、CONTROL_PLANE_URL、INTERNAL_CALLBACK_SECRET 等
npm run dev -w @open-inspect/web
```

打开 `http://localhost:3000` 用 GitHub 登录。OAuth 回调 URL 必须精确配置为 `http://localhost:3000/api/auth/callback/github`，差一个字符登录就会失败。验证链路：开一个会话、发一条提示词、确认事件流实时刷出来。想完整自托管，直接从 GETTING_STARTED 的 Step 1 走起，Cloudflare、Modal 的凭证和 Terraform 是前置。

`docs/` 下还有几份发文时不存在的文档值得按需读：`AUTH.md`（访问控制与凭证边界的权威出处）、`CLAUDE_AGENT.md`（订阅接入与 harness 选择）、`MANAGED_SKILLS.md`（可复用技能：按会话/仓库/环境分配、个人配置档、钉住修订版）、`MEMORY.md`（跨会话持久记忆：无向量库，事实目录加词法检索，代理写入要经所有者或维护者审批——README 甚至没宣传这个功能）、`GROK_MODELS.md`。

## 十七、小结

Open-Inspect 把"后台 AI 编码代理"从商业产品范式变成可自托管的开源参考实现，这三个月又补上了两块团队落地必需的板：运行时不锁死一家（OpenCode 与 Claude Agent 双 harness，订阅与 API key 分通道记账），内部治理有了角色、可见性、审计三件套。边界也划得清楚：单租户、共享 App 凭证、审计尽力而为、无版本发布。

对想把 AI 编码代理当组织基础设施建的团队，它是当前最完整的开源参考之一——前提是你接受跟一条快速移动的 main 分支。个人开发者继续用 Claude Code 或 Codex CLI 就好。
