---
title: "GitHub Copilot 代码审查：官方没有 PR Reviewer 应用，只有三条路径"
date: 2026-05-15T10:25:00+08:00
lastmod: "2026-10-03"
categories: ["技术笔记"]
tags: ["GitHub", "Copilot", "Code Review", "AI Agent", "SDK"]
draft: false
slug: github-copilot-pr-reviewer
github_repo: "github/copilot-sdk"
source_key: "gh:github/copilot-sdk"
description: "GitHub 没有一个叫 Copilot PR Reviewer 的官方应用。AI 审查 PR 的能力拆成三条路径：原生 Copilot code review（PR 页点 Request，通常 30 秒内回评）、Copilot CLI 的 /review 命令（本地改动预检）、Copilot SDK（六语言自建审查流）。本文按 2026-10-03 的官方文档与仓库读数，拆解每条路径的机制、成本与边界。"
---

想让 AI 审查你的 Pull Request，你会去搜 "Copilot PR Reviewer"——然后一无所获。GitHub 上没有叫这个名字的仓库或 Action（2026-10-03 实测搜索零命中）。如果你在别的教程里见过 `copilot-pr-reviewer-action` 这样的 Action 名、或 `.github/copilot-reviewer.yml` 这样的配置文件，它们在 [github/copilot-sdk](https://github.com/github/copilot-sdk) 仓库的全部 4,000 多个文件里逐个 grep 也都搜不到。这不是文档没写全，而是这个东西不存在。

GitHub 实际把 AI 代码审查拆成了三条路径，各管一段：**原生 Copilot code review** 是产品功能，直接在 PR 页面上请求，审查发生在 GitHub 的基础设施上；**Copilot CLI 的 `/review` 命令**管本地，在提交之前对未推送的改动快速过一遍；**Copilot SDK** 面向想把这些能力嵌进自己平台的团队，六种语言，自己写编排。官方从未说原生功能构建在 SDK 之上——它是 GitHub 自营的产品，SDK 只是同一家公司另开的通用集成入口。

本文事实核查基准：GitHub 官方文档与 copilot-sdk 仓库 2026-10-03 读数。

## 三条路径总览

| | 原生 Copilot code review | Copilot CLI `/review` | Copilot SDK 自建 |
|---|---|---|---|
| 形态 | GitHub 产品功能 | CLI 交互会话里的斜杠命令 | 六语言软件开发包 |
| 审什么 | 已推送的 Pull Request | 本地未提交的改动 | 你自己决定的任何输入 |
| 怎么触发 | PR 页 Reviewers 里点 Request，或分支规则集（ruleset）自动触发 | 会话里输入 `/review` | 代码里 `createSession` 发 prompt |
| 跑在哪 | GitHub 托管的 Actions runner 上 | 你的终端 | 你的应用进程旁起的 CLI 服务 |
| 结果 | PR 评论，带 High/Medium/Low 分级与修改建议 | 会话内文字反馈 | 你自己定义的输出 |
| 适合谁 | 所有付费 Copilot 计划的团队 | 提交前想先自检的开发者 | 需要定制审查流程、嵌入自有平台的团队 |

前两条路径零代码，第三条才是写代码的地方。多数团队真正需要的只有第一行。

## 原生 code review：一次审查如何流转

### 请求一次审查

在 GitHub.com 上打开一个 PR，右侧边栏 Reviewers 一栏，Copilot 旁边点 **Request**。官方文档给的预期是"通常少于 30 秒"出结果。评论回来后，每条评论带一个严重度标签——High、Medium 或 Low——用来排序先修哪个；能给出修复的地方直接以 suggested changes 形式呈现，点一下就能采纳提交。

有一个默认值需要记住：Copilot 的审查默认是 **Comment** 类型，不是 Approve 也不是 Request changes，也就是说默认情况下它不占用分支保护规则要求的必需审批名额。想让它的批准计入必需审批，要单独开启 Copilot approvals（下文细说）。

### 两个审查强度：Lite 与 Balanced

Copilot code review 支持两档审查强度。**Lite** 是标准审查，快速给出针对常见问题的反馈——官方的原话是 bug、安全漏洞和风格不一致。**Balanced** 是默认档，把 PR 路由到更高推理能力的模型，对复杂逻辑、安全敏感代码和跨服务改动做更长的分析。

成本上，官方估算一次 Lite 审查消耗价值 $0.05–1 美元的 AI credits，Balanced 一次 $0.25–5 美元，不含 GitHub Actions 分钟数；消耗一般随 PR 变大和自定义指令变多而上涨。这个估算的最大用途是给"该不该全仓库开 Balanced"定个量级：对日常小改动，Lite 的反馈速度和成本都合理；对碰钱、碰认证、碰多服务的 PR，Balanced 的差价买的是更长上下文里的推理。

强度解析有一套固定的优先级，请求时选的 > 这个 PR 上次用过的 > 发起者个人默认 > 仓库默认 > 组织默认 > GitHub 内置默认。也就是说个人可以在组织基线之上自主加严，但想在某个仓库"强制全员 Balanced"，得用仓库级默认。

### Agentic 能力：全仓上下文与一键转交

两档审查之上，还有两层自动开启的 agentic 能力。第一层是**全项目上下文收集**：审查不止看 diff，还会分析整个仓库来理解改动的语境，这直接决定"改了 A 函数签名，B 调用点会不会被点名"这类跨文件问题能不能被抓到。第二层是**把建议转交给 Copilot cloud agent**（public preview）：在审查评论上点 Fix with Copilot，云代理会在你的分支上另开一个带修复的新 PR。

这两层能力跑在 GitHub Actions 上——默认用标准 GitHub 托管 runner，可以换更大的 runner（分钟单价更高）或自托管 runner（不消耗 Actions 分钟数）。降级行为文档写得很清楚：Actions 不可用或相关 workflow 失败时，审查仍然会生成，只是没有这两层附加能力；如果你的组织禁用了 GitHub 托管 runner，审查会退化为更有限的形态。评价"这个功能可不可靠"时，这条依赖链比任何宣传数字都实在。

### 让审查更懂你的仓库

审查质量的上限往往不在模型，而在它对仓库约定的了解。GitHub 给了四个注入口，各管一层：

| 机制 | 存放位置 | 管什么 |
|---|---|---|
| 自定义指令 | `.github/copilot-instructions.md` | 全仓库、始终生效的 Copilot 专属规则 |
| 路径级指令 | `.github/instructions/*.instructions.md` | 只对匹配路径生效的规则 |
| AGENTS.md | 仓库根目录 | 跨 AI 工具共享的通用约定 |
| Agent 技能 | `.github/skills/` | 按需调用的任务型工作流 |

一个对验证很友好的细节：审查读取这些指令和技能时用的是 **head branch**（你改动的那个分支）而非 base branch。意味着你在同一个 PR 里改了 `.github/copilot-instructions.md`，这次审查就能按新规则来——先改规则、再看审查变化，一个 PR 就能完成闭环。

MCP 这层默认开着：**GitHub MCP server 和 Playwright MCP server 默认启用**，仓库里还可以配自己的 MCP server，把 issue 单号、事故记录、服务目录这类外部上下文直接拉进审查。仓库的 MCP 配置同时作用于 code review 和 Copilot cloud agent；只想让 cloud agent 用 MCP 的话，设置里有一项 "Allow Copilot to use MCP tools when reviewing pull requests"，默认启用，单独关掉即可。技能这层不需要手动调用——仓库里有 review 类技能（比如自定义的框架专项审查）时，Copilot 会在审查中自动采用相关的那些。

### 自动审查与治理

手动点 Request 之外，自动化有三层入口，按控制面从大到小：

- **仓库级**：Settings → Rules → Rulesets → 新建 branch ruleset，勾选 **Automatically request Copilot code review**。两个可选开关直接决定审查频率——**Review new pushes**（每次推送都重审；不勾则一个 PR 只审一次）和 **Review draft pull requests**（草稿阶段就审，赶在人审之前把低级问题清掉）。
- **组织级**：组织策略里可以对部分或全部仓库开启自动审查，也可以统一下发默认审查强度。
- **用户级**：Copilot Pro、Pro+、Max 订阅者和 Business/Enterprise 许可持有者可以给自己创建的 PR 开自动审查（托管账号除外）。

仓库 ruleset 和用户个人设置是两套并行配置，官方明说不互相继承、也不互相覆盖——任一边启用即触发自动审查，但一个 PR 只会收到一条审查，不会两边各发一条。这个设计值得留意：意味着"仓库没配自动审查"不等于"没人开了自动审查"，排查审查来源时要两边都看。

**Copilot approvals** 是治理层的最后一块（public preview，默认对所有组织禁用）。企业策略有三个档位：让组织自行决定、仅对选定组织启用、全局禁用。开启后，Copilot 可以提交满足 required-approval 规则的 Approve 审查，效力与同事的批准相同；新提交推上来之后批准自动撤销，需要重新请求审查。要不要让 AI 的批准计入合并门槛，是个纯治理决策——默认关闭这个状态本身就说明了 GitHub 对它的态度。

还有一条容易忽略的路径：组织成员**没有 Copilot 许可证**也能用 GitHub.com 上的 code review。前提是组织在 Business 或 Enterprise 计划上，由企业管理员依次启用两条策略（AI credits 付费使用 + 允许无许可证成员使用 code review），且只对显式启用的组织内仓库生效。对"只想给少数外包协作者开审查能力"的场景，这比买整份许可证便宜。

### 两个硬边界

**模型不可换。**官方文档原话是 "Model switching is not supported"——code review 是一个精心调校过的专有产品，混用模型、提示词与系统行为来保证一致性，换模型大概率牺牲可靠性。组织设置页的 Models 配置只管 Copilot Chat，管不到它；它甚至可能使用你在 Models 页里没启用的模型。想要"用自己选的模型做审查"，这条路径给不了，能走的是第三条路径自建。

**部分文件不审。**依赖管理文件（`package.json`、`Gemfile.lock` 这类）、日志文件、SVG 文件被排除在审查之外。排除依赖清单合理——那些文件本就不该人审——但意味着 lock 文件里偶尔混入的可疑依赖变更不会被它抓到，供应链审查仍需要专门的工具。

## CLI 本地预检：/review

提交之前想要一遍快速反馈，可以不开 PR，直接在 Copilot CLI 的交互会话里输入 `/review`。命令后面可以跟提示词、路径或文件模式来收窄审查范围。Copilot 分析改动时如果需要执行命令（比如看 diff、验证文件），会先征求你的批准。反馈直接落在会话里，改完可以再跑。

Copilot CLI 的安装是 `brew install copilot-cli` 或 `npm install -g @github/copilot`。注意包名是 `@github/copilot`——网上常见的 `@github/copilot-cli` 是一个不存在的包名，照抄会直接 404。

这条路径的定位是**提交前的本地自检**，审查对象是你工作区里的改动，不是 PR。它和原生 code review 是流水线上的两道工序，互相替代不了。

## SDK 自建：当产品功能不够用时

前三条路径覆盖不了的场景——把审查嵌进内部 DevOps 平台、输出到自有的报告系统、对特定代码库类别做完全定制的审查逻辑——才是 [github/copilot-sdk](https://github.com/github/copilot-sdk) 的地盘。仓库 2026-10-03 读数：10,539 Stars、1,472 Forks，MIT 许可，TypeScript 为主要语言，2026-01-14 建仓，最新 release v1.0.16（2026-09-30）；FAQ 明确它已 general available 并遵循语义化版本。

六种语言的 SDK 共享同一个架构：你的应用 → SDK 客户端 → JSON-RPC → 以服务器模式运行的 Copilot CLI。SDK 负责管理 CLI 进程的生命周期，Node.js、Python、.NET 三个版本自动捆绑 CLI 运行时，Go、Java、Rust 需要自行保证 `copilot` 在 PATH 里。运行时要求：Node.js ^20.19.0 或 ≥22.12.0，Python 3.11+。

用官方 getting-started 里的原版示例看最小用例有多小——TypeScript 五行：

```typescript
import { CopilotClient } from "@github/copilot-sdk";

const client = new CopilotClient();
const session = await client.createSession({ model: "auto" });

const response = await session.sendAndWait({ prompt: "What is 2 + 2?" });
console.log(response?.data.content);
```

Python 版：

```python
import asyncio
from copilot import CopilotClient
from copilot.session import PermissionHandler

async def main():
    client = CopilotClient()
    await client.start()

    session = await client.create_session(on_permission_request=PermissionHandler.approve_all, model="auto")
    response = await session.send_and_wait("What is 2 + 2?")
    print(response.data.content)

    await client.stop()

asyncio.run(main())
```

基于这套 API 搭一个自己的审查 agent，思路是把系统提示词换成审查角色、把 diff 作为输入喂给会话、把输出解析成你自己的报告格式——SDK 提供会话管理、工具调用、权限钩子和 MCP 扩展点，审查逻辑本身完全归你写。

两个采用前提要说在前面。第一，**需要 Copilot 订阅**（有免费档，限量），除非走 BYOK——用 OpenAI、Microsoft Foundry 或 Anthropic 的 API key 直连模型，此时不需要 GitHub 认证，但仅支持 key 认证，不支持 Entra ID、托管身份或第三方 IdP。第二，计费与 Copilot CLI 同模型，按 prompt 计入用量额度。

## 任务流案例：一个 PR 走完全部三道工序

以一个真实场景把三条路径串起来：开发者修一个 API 参数校验的 bug。

1. **本地预检（CLI）**。改完代码，在 Copilot CLI 会话里跑 `/review src/api`，收窄到改动目录。反馈指出边界条件没覆盖——顺手补上测试再提交，最便宜的一轮拦截已经发生。
2. **自动审查（原生）**。push 开 PR。仓库的 branch ruleset 开了 Automatically request Copilot code review 和 Review draft pull requests，所以草稿状态就会收到一轮审查：一条 High 的评论指出校验逻辑在某类输入下仍然可绕过，附 suggested change；两条 Medium/Low 提到命名与测试覆盖。
3. **修复闭环（原生 + cloud agent）**。High 那条建议合理，点 Apply 采纳；Medium 那条改动面较大，点 Fix with Copilot 转给 cloud agent，它在分支上另开一个带修复的 PR 供复核。
4. **人审合入**。修复推送后，此前若开启过 Copilot approvals，其批准已随新提交自动撤销；人类 reviewer 复核后合入。整个流程里 AI 承担了第一遍扫描，人守最终判断。

## 采用建议

按成本从低到高排一个上手顺序：

1. **先开原生功能**。它不需要任何部署——组织策略里确认 Copilot code review 已启用，PR 页点一次 Request 就能看到质量。觉得反馈太浅再把默认强度升到 Balanced。
2. **高频仓库上自动化**。对改动频繁、质量要求高的仓库配 ruleset 自动审查；同时把团队约定写进 `.github/copilot-instructions.md`，这通常是提升审查质量性价比最高的一步。
3. **有平台化诉求才动 SDK**。内部 DevOps 平台想统一展示审查结果、或需要完全定制的审查逻辑时再写代码。它的维护成本是长期的——SDK 版本、CLI 捆绑策略、权限钩子都要跟着上游走。

三类团队可以缓一缓：需要指定审查模型或私有化部署的（原生是云服务且模型不可换，SDK 的 BYOK 只支持 key 认证）；依赖 lock 文件变更做安全把关的（这些文件被排除在审查外）；以及把合规结论寄托在 AI 审查上的金融医疗类项目——High/Medium/Low 是优先级提示，不是合规结论，监管口径的复核仍然要人来做。

成本预期也给一个量级：按官方估算，每个 PR 花费 $0.05–5 美元等值 AI credits（强度决定档位），外加跑 agentic 能力的 Actions 分钟数。用量可以在组织的 Actions 指标里按 `copilot-pull-request-reviewer` workflow 过滤查看，计费报告里对应的 workflow_path 是 `dynamic/agents/copilot-pull-request-reviewer`。

## 结语

GitHub 把 AI 代码审查做成产品功能而不是独立应用，这个决定对使用方的含义很具体：接入成本从"一个集成工程"降到了"一次开关配置"，而迁移成本也随之消失——没有第三方 reviewer 应用的账号、webhook 和令牌要管。真正需要写代码的部分被推到了两端：仓库约定用指令、技能和 MCP 表达，深度定制用 SDK 实现。对多数团队，第一步是花三十秒点一次 Request，看看它在你自己的代码上说什么，再决定往下走多深。

**相关资源：**

- [About GitHub Copilot code review](https://docs.github.com/en/copilot/concepts/agents/code-review) — 功能概念文档（可用范围、agentic 能力、计费估算）
- [Using GitHub Copilot code review](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/use-code-review) — 请求审查与自动化配置的操作文档
- [Configuring code review by GitHub Copilot](https://docs.github.com/en/copilot/how-tos/copilot-on-github/set-up-copilot/configure-code-review) — ruleset 自动审查配置步骤
- [github/copilot-sdk](https://github.com/github/copilot-sdk) — 六语言 SDK 与 Getting Started 教程
- [Copilot CLI agentic code review](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/agentic-code-review) — `/review` 命令用法
- [github/awesome-copilot](https://github.com/github/awesome-copilot) — 社区维护的指令、Agent 与技能集合（截至 2026-10-03 约 3.96 万 Stars），含 `postgresql-code-review`、`mcp-implementation-security-review` 等审查类技能
