---
title: "Twenty：把 CRM 变成可发布代码的开源平台，用 SDK 定义 Object、工作流和 Agent"
date: "2026-05-29T09:06:54+08:00"
lastmod: "2026-09-28T10:00:00+08:00"
slug: "twenty-open-source-crm-sdk-agent-guide"
github_repo: "twentyhq/twenty"
source_key: "gh:twentyhq/twenty"
author: "钳岳"
canonical: "https://txtmix.com/posts/tech/twenty-open-source-crm-sdk-agent-guide/"
description: "Twenty 是开源 CRM，以「代码优先」为设计主轴——Object 定义、工作流配置和 AI Agent 全部用 TypeScript 代码描述，走 Git 工作流发布。本文拆解它的 App 平台、AI 能力、许可证结构与适用边界，数据核实至 2026 年 9 月底。"
draft: false
categories: ["技术笔记"]
tags: ["CRM", "开源", "TypeScript", "AI Agent", "NestJS", "PostgreSQL"]
---

# Twenty：把 CRM 变成可发布代码的开源平台

Twenty 给自己的定位写在 README 标题里：**The #1 Open-Source CRM**；GitHub 仓库描述则是 "The open alternative to Salesforce, designed for AI"。两句口号指向同一个判断：CRM 的扩展工作应该像写代码一样完成——定义数据模型、业务逻辑和 AI Agent 都用 TypeScript 描述，变更走 Git，发布走 CLI，可回滚、可评审。

这个定位在 2026 年有了更具体的含义。Twenty 的 App 开发工具链（`twenty-sdk` npm 包）于 2025 年 10 月首次发布，2026 年 4 月起进入 2.0 系列；官方文档在 Apps 概念页里的开场白是："Most CRMs give you a config panel. Twenty gives you a platform." 截至 2026 年 9 月 28 日，仓库有 57,578 stars、9,327 forks，主仓库 release 推进到 twenty/v2.41.0（2026-09-17），九月份连发 v2.39.0、v2.40.0、v2.41.0 三个 minor 版本，npm 上的 `twenty-sdk` 已到 2.43.0——发版节奏以周计，文档和 API 面貌月级漂移，本文数据均核实至 2026 年 9 月底。

## 先看地图：这套系统怎么分层

Twenty 容易被当成「一个长得像 Notion 的 CRM 界面」，实际它的重心在界面之下的平台层。按官方文档的口径，可以把系统拆成四层：

| 层 | 职责 | 关键事实 |
|------|------|---------|
| 核心 CRM | 客户、公司、商机等记录与视图，含日历/邮件同步 | 无代码配置对象、字段与视图（README 口径："the building blocks of a modern CRM"） |
| 工作流引擎 | 可视化自动化构建器 | 覆盖无代码自动化场景，与 AI 动作可组合 |
| App 平台 | 用 TypeScript 包扩展 CRM：数据模型、服务端逻辑、UI、AI 能力 | AST 分析发现实体，CLI 同步与发布，含 Marketplace |
| AI 层 | 聊天助手、工作流中的 AI 动作与自主 Agent | 仓库描述 "designed for AI"，Agent 能力标注 alpha |

技术栈（README Stack 节原文）：TypeScript 全栈，后端 NestJS + BullMQ，数据库 PostgreSQL，缓存 Redis，前端 React + Jotai + Linaria + Lingui，Monorepo 用 Nx 管理。商业路径是三档云订阅加自托管：Cloud Pro $9/人/月（按年付）、Organization $19/人/月（解锁 SSO 与更细的权限控制）、Enterprise 从 $50,000/年起（单租户隔离等），自托管开源核心免费（企业功能除外，见下文许可证一节）。

下面三节展开 App 平台与 AI 层——这是 Twenty 与其他开源 CRM 拉开差距的地方。

## App：CRM 扩展是 TypeScript 包

### 一个 App 里能放什么

官方文档把 App 定义为「用 `twenty-sdk` 声明实体的 TypeScript 包」。实体种类远不止数据模型，Concepts 页列了 16 种，常用的包括：

| 实体 | 作用 |
|------|------|
| Object / Field / Relation | 自定义记录类型、给现有对象加字段、双向关联 |
| Logic Function | 服务端 TypeScript 函数，支持 HTTP 路由、cron、数据库事件等多种触发器 |
| Skill / Agent | 可复用的 AI 指令、带自定义系统提示词的 AI 助手 |
| Front Component | 沙箱化的 React 组件，渲染进 Twenty 界面（侧板、小部件、命令菜单） |
| View / Navigation / Page Layout | 预配置列表视图、侧边栏入口、记录页布局 |
| Role | App 的权限集，约束它能读写哪些对象和字段 |
| Connection Provider | 代表用户访问第三方服务的 OAuth 凭据 |

声明方式是 `export default defineObject(...)` 这类函数调用。SDK 在构建期用 AST 分析找出所有声明——没有配置文件，没有注册样板代码，文件放哪个目录都行（目录结构只是约定）。构建产物是一份 manifest，完整描述这个 App 会往工作区添加什么。

### 开发循环：改代码，一秒后见界面

官方 Quick Start 把上手过程拆成三个阶段，前置条件是 Node.js 24.5+、Yarn 4（Corepack 启用）和 Docker：

```bash
npx create-twenty-app@latest my-twenty-app
```

脚手架会生成一个带 starter `application-config.ts`、默认角色、CI/CD 工作流和集成测试的 TypeScript 项目；如果本机 Docker 在运行，它还会顺带启动一个本地 Twenty 服务器——拉取 `twentycrm/twenty-app-dev` 镜像跑在 2020 端口，并自动用预置的演示工作区完成 CLI 认证。接着进入日常开发循环：

```bash
yarn twenty dev
```

这个命令监听 `src/` 目录，每次保存就重新构建并同步到服务器，官方口径是「改一个文件，几秒内界面生效」。这里的 `twenty` 命令来自 `twenty-sdk` npm 包（`npx twenty` 跑的就是它；旧的 `twenty-cli` 包已标记废弃并指向 twenty-sdk）。

要接 CI 或脚本，用一次性同步替代常驻监听：

```bash
yarn twenty plan    # 只构建并打印元数据变更，不落盘
yarn twenty apply   # 构建 + 同步，成功退出码 0，失败 1
```

`apply` 的文档明确写着适用场景包括 CI、pre-commit 钩子、AI agents 和脚本化工作流；破坏性变更（删除）默认要确认，`--force` 跳过。这两个命令是旧写法换的名字：`apply` 即原 `dev --once`，`plan` 即原 `dev --once --dry-run`，旧写法已标记废弃。

### 发布：私有部署与 Marketplace 双路径

```bash
npx twenty app:publish --private
```

README 里的这条命令是把构建产物以 tarball 形式部署到指定服务器——注意它只覆盖 `--private` 这条路径。发布文档给出的完整图景是两条路：

- **tarball 私有部署**：`app:publish --private` 上传到配置好的 remote（存在 `~/.twenty/config.json`），不进公开市场，其他工作区通过注册页的分享链接安装；
- **发布到 npm + Marketplace**：`app:publish`（不带 `--private`）把包发上 npm，再在 Twenty 里认领（claim），其他工作区就能从 Marketplace 目录发现并安装。

无论哪条路，发布都会创建一个 application registration——App 在实例上的身份，承载 marketplace 条目、OAuth 客户端和服务端状态。`universalIdentifier` 在实例内唯一，一个注册同一时刻最多属于一个工作区。这条规则把「安装 App」和「开发 App」拆成了两种权利：从 Marketplace 目录导入的 App 起始状态是「无主」，谁想改它的代码，得先用 GitHub 认领所有权；认不出主人时，同步会被拒绝。fork 别人的 App 时同理——要么换 `universalIdentifier`，要么让原属工作区转移注册。

## AI：产品层两条线，SDK 层三件套

### 产品里已经能用的 AI

按官方 User Guide（AI overview 页）的口径，目前有两块：

**AI 聊天助手**。能查询工作区里的任意记录、关系和指标，并且感知当前页面上下文——站在某家公司记录页提问「这家公司有什么商机在谈」，它知道「这家」指谁。

**工作流中的 AI**。可视化工作流构建器里可以加两类 AI 步骤：AI 动作（数据富化、记录分类、生成摘要）和自主 Agent（在工作流内执行多步任务），提示词完全自定义。官方给的用例包括自动分类流入线索、按会议纪要起草跟进邮件、按互动模式给商机打分。

权限上，AI Agent 受既有权限系统约束：在 Settings → Members → Roles 里配置它能访问哪些数据、对每个对象有什么读写权限。注意 AI 功能消耗工作区的 AI 积分（SDK 文档提到过「工作区 AI 积分中途耗尽」这种失败原因）。

### 用代码定义自己的 Skill 和 Agent

App 平台把 AI 能力开放成了三种实体，SDK 文档明确标注**目前处于 alpha**：

`defineSkill()` 定义可复用的指令文本（`content` 字段就是给 AI 看的操作说明）；`defineAgent()` 定义带系统提示词的 Agent，可选 `modelId` 覆盖默认模型，`responseFormat` 支持强制 JSON 输出——但 schema 是扁平的，属性类型只能是 `string`/`number`/`boolean`，不支持嵌套对象和数组。

`runAgent()` 让 Logic Function 驱动自家 Agent 运行。几个设计细节值得留意：

- 同步执行：`runAgent()` 等 Agent 跑完才返回，期间 Agent 自己会调工具读写记录；
- 传 `prompt` 或 `messages` 二选一，后者用于 Slack/Discord 这类多轮场景（1 到 100 条消息，`user` 消息可带附件，上限 10 个）；
- 默认以 App 自己的角色运行；传 `runAsWorkspaceMemberId` 可以代某位成员运行，此时权限收窄为该成员自己的角色，产出也记在成员名下——这个 token 不能指名任意成员，规则随调用方凭证类型变化；
- 官方专门警告了循环触发：在 `*.updated` 数据库事件触发器里调 `runAgent()`，而 Agent 又更新同一条记录，就会无限循环，要么用 `updatedFields` 把触发范围圈在 Agent 永远不写的字段上，要么先判断目标字段是否为空。

### 六种触发器把代码接进系统

Logic Function 是把上述一切串起来的执行单元。它有六种触发方式：HTTP 路由（`httpRouteTriggerSettings`）、服务器路由（`serverRouteTriggerSettings`，为第三方 webhook 把所有租户的事件都投递到同一个 URL 的场景设计）、数据库事件（`databaseEventTriggerSettings`，可用 `updatedFields` 过滤）、cron 定时（`cronTriggerSettings`），以及两种 AI 相关的：

- `toolTriggerSettings`——把函数暴露给 Twenty 的 AI 功能（聊天、MCP、function calling）发现和调用，入参用标准 JSON Schema 描述；
- `workflowActionTriggerSettings`——把函数注册为可视化工作流构建器里的一个步骤，用 Twenty 自己的 InputSchema，构建器据此渲染字段编辑器。

这两种触发器的 inputSchema 都可以省略，构建器会从处理函数源码推断。函数执行在服务端隔离的 Node.js 进程里，只能通过带类型的 API 客户端访问数据；客户端的访问令牌从 App 用 `defineApplicationRole()` 声明的角色派生，有真人触发时还会进一步收窄到触发者本人的权限。

## 一次任务怎么流过这套系统

官方 App 教程（Document Generator）恰好是一个完整样本：从 CRM 数据生成个性化文档。把它按执行顺序串起来，能看到各层如何配合：

1. **建模**：`defineObject` 声明 Document 和 Template 两个对象加一条关联——数据模型进工作区元数据，与内置对象同等待遇。
2. **服务端逻辑**：写一个 Logic Function 读模板、取记录、生成文档，同时挂 `toolTriggerSettings` 和 `workflowActionTriggerSettings`——同一个函数，既能在 AI 聊天里被调用，也能作为工作流步骤插入自动化流程，还能经 HTTP 路由触发后在网页上渲染结果。
3. **界面**：用 View 配置文档列表，加侧边栏导航和 Front Component——组件跑在 Web Worker 里，通过 Remote DOM 渲染原生 DOM 元素（官方明确说不是 iframe），与主页面用消息传递通信。
4. **Agent**：`defineAgent` 定义一个「文档助手」，挂上第 2 步的工具；用户在聊天里提出生成文档的请求，Agent 调用工具函数完成生成。
5. **发布**：`yarn twenty dev:build` 产出 manifest，`app:publish` 上 Marketplace，其他工作区一键安装。

这条链路里没有一步需要离开 TypeScript 工程上下文：对象、函数、界面、Agent 全部是仓库里可评审的源码，发布即部署，回滚靠 Git。

## 给编码代理的官方技能包

README 在 2026 年新增了一个板块：官方 Agent Skills，教编码代理完成 Twenty App 的全流程。`packages/twenty-agent-skills` 收录五个规范技能：

| 技能 | 用途 |
|------|------|
| `create-app` | 用 `create-twenty-app` 脚手架新 App |
| `develop-app` | 增改对象、字段、Logic Function、布局、前端组件、工作流 |
| `manage-app` | remote 管理、同步、构建、部署、日志、CI/CD 排障 |
| `publish-app` | README、Marketplace 元数据、图标截图等发布物料 |
| `use-twenty-mcp` | 可选：通过 MCP 连接工作区，把记录整理成可读 Markdown |

安装走 `skills` CLI（支持 Claude Code、Codex、Cursor、Pi 等 harness），源是仓库的 `agent-skills` 分支：

```bash
npx skills add https://github.com/twentyhq/twenty/tree/agent-skills --skill create-app
```

Codex 用户另有同名插件（`twenty`），内置公开的 `twenty-docs` MCP 服务器用于检索官方文档；访问工作区数据则要在自己的客户端里配工作区 MCP 端点，仓库提供 `setup-mcp.sh` 辅助脚本。SKILLS.md 还交代了仓库里另外几族技能的归属：`twenty-claude-skills` 面向工作区使用者，`.claude/skills` 只服务本仓库的贡献者——从裸仓库直接 `npx skills add twentyhq/twenty` 拉到的是后两者，建 App 要认准 `agent-skills` 分支。

这个技能包的存在本身是个信号：Twenty 把「用 AI 写 CRM 扩展」当成了官方支持的默认工作方式，文档里的 `apply` 命令甚至把 AI agents 列为一等公民的使用场景。

## 许可证与商业模式：双轨制怎么运作

Twenty 的许可结构比常见的「核心开源 + 企业版闭源」更细，README 附带的 LICENSE 声明分三层：

- **主体 AGPLv3**。修改 Twenty 本身对外提供网络服务，须按 AGPLv3（含第 13 条）开源修改内容。
- **企业双许可**。源码顶部带 `/* @license Enterprise */` 注释的文件走商业许可，典型是角色权限、SSO 这类企业功能——自托管这些能力需要商业授权。
- **MIT 例外**。`twenty-sdk`、`twenty-client-sdk`、`create-twenty-app`、`twenty-shared`、`twenty-ui` 组件库和 `packages/twenty-apps` 下的应用按 MIT 授权。

对评估「能不能拿它做商业项目」的团队，关键在一份附加条款（Twenty Application Exception，AGPLv3 第 7 条下的额外许可）：通过 Application Interfaces（HTTP API、webhook、manifest 格式、SDK）与 Twenty 交互、且不内嵌或修改 Twenty 源码的 Application，不受 AGPLv3 约束，**可以任意授权包括专有闭源**；用官方构建工具把 App 与仓库库文件打包也不产生传染。限制同样明确：这条豁免不覆盖 Twenty 本身的修改，也不授予商标权。

落到实操层面：给 Twenty 写的 App 是你的代码，闭源发售没有许可障碍；改 Twenty 平台本身再拿去提供 SaaS，才会触发 AGPL 的开源义务。这个结构把 copyleft 精确圈在了「改平台」这个真正的竞争面上。

## 自托管：成本与纪律

自托管走 Docker Compose，官方文档给的最低要求是 2GB 内存，低于这个数进程会崩。最快路径是一键脚本：

```bash
bash <(curl -sL https://raw.githubusercontent.com/twentyhq/twenty/main/packages/twenty-docker/scripts/install.sh)
```

两个纪律值得记下：装指定版本时 `VERSION` 必须写完整的 release tag（如 `v2.38.1`），`v2`、`latest` 这类别名不被接受；compose 配置从 `twenty/<version>` git tag 拉取，所以 v2.9.0 及更早的版本用不了这个脚本。环境变量全部声明在 `docker-compose.yml` 里，文档特别警告只改指南里提到的配置项。

## 适用边界：谁该上，谁先等

**适合认真评估的团队**：

- 工程团队自建 CRM，且扩展需求会持续演化——App 把扩展变成可评审、可回滚的代码资产，这是 Twenty 与配置型 CRM 的分水岭；
- 想在 CRM 里深度嵌入 AI 工作流的团队——`toolTriggerSettings` 加 `runAgent` 提供的是「业务函数直接成为 Agent 工具」的通路，在多数平台上这一步要在平台外另搭集成层；
- 对 vendor lock-in 敏感、但又想要 SaaS 级体验的团队——Cloud 三档定价透明（Pro $9 / Organization $19 / Enterprise $50k+/年），随时可以带着 App 代码迁去自托管。

**需要谨慎或再等等的场景**：

- 非技术团队主导的 CRM——App 开发、CLI、Git 工作流都默认使用者会写代码，纯业务团队拿它当 Salesforce 用会失望；
- 指望 Agent 能力立刻生产化的团队——`defineAgent`/`runAgent` 官方标注 alpha，`responseFormat` 的 schema 还不支持嵌套结构，投入前先在测试工作区验证；
- 需要 SAML/SSO 的自托管用户——这些能力在 `@license Enterprise` 文件里，自托管也要商业授权，预算谈不下来就只能选云的 Organization 档（$19/人/月）。

## 结尾判断

Twenty 证明了一件事：CRM 这类「配置型产品」和工程实践并不天然冲突，前提是把配置面整个搬进代码。它的 App 平台沿着这条路走得很完整——AST 发现实体、秒级同步、双路径发布、注册所有权模型，每个环节都有对应的 CLI 命令和数据模型；AI 层的产品能力尚在 alpha，但 SDK 已经把「业务函数变成 Agent 工具」的通路铺好，配合官方 Agent Skills，AI 写扩展这件事被当成了默认工作方式。

风险也同样具体：周级发版意味着 API 面貌持续变动，alpha 功能随时可能调整，企业功能与开源核心的边界由 `@license Enterprise` 注释划定并可能移动。把它用于生产的前提是接受这种节奏——锁定版本、把 App 代码放进自己的 CI、升级前跑 `yarn twenty plan` 看清元数据变更。做得到这些，它是目前把「CRM 即代码」走得最远的一个。

## 参考链接

- [Twenty 官网](https://twenty.com)
- [官方文档](https://docs.twenty.com)（文档索引：https://docs.twenty.com/llms.txt）
- [App 开发 Quick Start](https://docs.twenty.com/developers/extend/apps/getting-started/quick-start)
- [Apps 核心概念](https://docs.twenty.com/developers/extend/apps/getting-started/concepts)
- [Skills & Agents（SDK）](https://docs.twenty.com/developers/extend/apps/logic/skills-and-agents)
- [发布与 Marketplace](https://docs.twenty.com/developers/extend/apps/operations/publishing)
- [自托管 Docker Compose](https://docs.twenty.com/developers/self-host/capabilities/docker-compose)
- [GitHub 仓库](https://github.com/twentyhq/twenty)
