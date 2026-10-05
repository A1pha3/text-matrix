---
title: "Cloudflare OS：当每个用户都跑一份自己的软件，SaaS 的地基开始松动"
description: "Cloudflare OS 是 Cloudflare 内部日常使用后开源的 AI 生产力环境：每个文档是一个私有沙箱里的应用（Gadget），能力型安全层（Gatekeeper）管住 Agent 与外部世界的一切往来。本文拆解它的私有实例模型、能力安全与异步审批设计，以及与 SaaS 架构的根本分歧。"
date: 2026-10-06T03:25:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Cloudflare OS", "Cloudflare Workers", "AI Agent", "能力安全", "架构"]
github_repo: "cloudflare/cloudflare-os"
source_key: "gh:cloudflare/cloudflare-os"
slug : cloudflare-os-gadget-capability-security
---

## 核心判断

绝大多数「AI 工作台」产品的共同点是：一个更强的聊天框，加上一堆连接器。Cloudflare OS 不是。它由 Cloudflare 内部孵化——README 称从工程师到销售的大量员工每天在用它工作——2026 年 8 月开源的 v2 是一次完全重写。约 1.1 万 stars，最近提交在 2026 年 10 月，处于官方明示的「early access，rough edges 很多」阶段。

它真正值得读的地方是一个架构主张：**AI 时代，中心化 SaaS 的经济与安全模型开始不成立，替代品是「每个用户跑一份自己的、AI 写的、沙箱里的小应用」**。这不是口号——仓库里有一套完整的技术栈在支撑这个主张，而且由 Workers 运行时团队亲自构建，用上了为它专门加进运行时的特性（Dynamic Workers、Facets）。对平台工程师来说，这份源码本身就是 Workers 前沿用法的官方示范。

## 系统地图

Cloudflare OS 的三个支柱，README 给得很清楚：

1. **Agent 聊天 UI**：预载公司知识的通用 Agent，干活的方式是写代码并立即执行（Code Mode）；
2. **Gadget 沙箱应用**：让 Agent 构建小型个人应用并安全分享；
3. **Gatekeepers**：一层能力型安全框架，管住 Agent 和应用能碰什么。

用一个操作系统类比串起来（README 原表）：

| 传统 OS | Cloudflare OS |
|---------|---------------|
| 内核 | `packages/workshop-backend` |
| 设备驱动 | `packages/gatekeeper-*` |
| shell | `packages/workshop-frontend` |
| 进程 | Gadget（应用实例） |
| 可执行文件 | Blueprint（应用模板） |
| ACL | 共享权限 |
| ？ | Agent |

Agent 是传统 OS 没有的那一行——它既不是用户，也不能当成用户对待。这个类比不是营销修辞：workshop-backend 确实在做内核的事（隔离、调度、访问控制），Gatekeepers 确实在做驱动的事（把外部服务包装成受控接口）。而 Agent 是传统操作系统的缺失件：**必须对一个人类用户负责，同时拥有自己的受限权限**。

## Gadget：每个用户一份软件实例

在 Cloudflare OS 里创建一份幻灯片，系统不是调用某个云端 SaaS，而是**为你的这次使用私有地起一个幻灯片应用实例**——一个 Gadget。实例间的隔离是运行时级别的：每个 Gadget 跑在一个 Dynamic Worker Facet 里（Workers 的新特性），默认断网，只能通过显式声明的 Workers Bindings 访问指定外部资源。

这个模型直接换来两条性质：

1. **幻灯片应用不可能有泄露你的数据的漏洞**——因为别人根本不跑你的那份实例，沙箱控制着一切访问；
2. **你可以放心改它**。缺个功能？让 Agent 加。因为第 1 条，改代码是安全的。

第 2 条是整个设计的重心。中心化 SaaS 时代，改软件要给开发者提 feature request；Gadget 模型下，**最终用户用 AI 解决自己的问题**。分享时你分享的不是运行中的服务，而是 Blueprint——整套应用代码，对方拿到的是自己的副本。这更像手机 App 的分发模型，而不是 SaaS。

协作同样内置：每个 Gadget 由一个 Durable Object 支撑，实时多人协作是 Durable Object 的舒适区，README 说编码 Agent 默认就会实现实时协作，无需专门要求。

## Gatekeepers：能力安全与异步审批

Gatekeeper 被描述为「加强版 MCP server」，每个外部服务（GitHub、Google、Notion、Slack、Supabase、Home Assistant……仓库里已有十余个）对应一个 Gatekeeper Worker，职责：

- 把服务的原生 API 包装成干净的 Cap'n Web RPC 接口；
- 处理 OAuth 授权；
- 把访问收窄到用户真正想给的那一个资源（capability，能力，而非宽泛的角色）；
- 记录 Agent/应用的每个动作；
- 有副作用的动作，给人类批准或拒绝的机会。

最值得单独讲的是最后一条的**异步审批**设计。传统 human-in-the-loop 是同步的：Agent 想做有副作用的动作就得停下等你点批准——你去倒杯咖啡回来，发现 Agent 在第一步就卡住了。结果就是人们干脆开 `--dangerously-skip-permissions`。

Gatekeepers 的解法：审批触发时**本地模拟动作结果**，告诉 Agent「完成了」，Agent 继续排队后续动作；如果 Agent 回读结果，就喂给它模拟数据。等你回来，可以批量或逐条批准/拒绝，届时真实动作才落盘。这把审批从 Agent 的关键路径上摘掉了，同时没有放弃人类的最终控制权。对任何做 Agent 编排的人来说，这一段都是可直接借鉴的设计。

能力模型的另一面是**默认无访问**：即使平台配置了外部账号，Agent 和 Gadget 也拿不到任何东西——必须由用户逐个「引见」（introduction，粘贴链接或从 UI 选择）资源给某个 Agent，Agent 也可以主动请求引见。这与多数 Agent 框架「配置一次 MCP server、此后 ambient 全量可用」形成鲜明对照。

## 上手路径

```bash
# 本地快速体验（需 pnpm）
git clone https://github.com/cloudflare/cloudflare-os
cd cloudflare-os
pnpm run-local
# 打开 http://localhost:8787 —— 全栈跑在 wrangler/workerd 上
```

试着输入：「给我的客户会议做一份幻灯片」「做一个协作白板」「做一个井字棋，我先手」。部署到自己 Cloudflare 账户走 [os.cloudflare.app/deploy](https://os.cloudflare.app/deploy)；带定制 Gatekeeper 的正式部署用官方 starter 仓库 [cloudflare/cloudflare-os-starter](https://github.com/cloudflare/cloudflare-os-starter)。自托管路线基于开源的 workerd（文档与工具链仍在完善中，README 标注 COMING SOON）。

Gatekeeper 对接第三方服务需要各自配置 OAuth 凭据——README 坦承这步对非开发者不友好，每个 `packages/gatekeeper-*` 下有单独说明。

## 适用边界与风险

- **early access**：v2 重写后官方自认能力已强但粗糙边多，直接给非技术员工当日常生产力环境需要勇气与灰度；
- **不接受外部功能贡献**：官方明说 AI 让写代码变容易、审查变贵，只收小的、可平凡验证的修复 PR——用「抄作业」心态读它，而非「共建」心态；
- LLM 可自选供应商（基于 pi-agent-core 统一多模型接口），但 Gatekeeper 的 OAuth 配置成本是真实存在的运维负担；
- 深度绑定 Workers 运行时特性（Durable Objects、Dynamic Workers、Facets 部分 是为 OS 专门加的），脱离 Cloudflare 生态自托管要等 workerd 路线成熟。

## 结语

Cloudflare OS 的可读性远超一个「内部工具开源」：它把三个正在发生的技术趋势——Code Mode Agent、运行时级沙箱、能力安全——压进了一个自洽的产品形态，并押注了一个激进但逻辑自洽的判断：**当每个用户都能让 AI 改自己的软件，中心化 SaaS 就不再是默认答案**。无论这个赌注对不对，Gatekeepers 的异步审批与默认无访问设计，已经值得进任何一份 Agent 安全设计的参考清单。

仓库：[cloudflare/cloudflare-os](https://github.com/cloudflare/cloudflare-os)。
