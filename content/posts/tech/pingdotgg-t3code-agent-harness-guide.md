---
title: "T3 Code：Theo 的 Agent 控制台，远程驾驭 Claude Code 与 Codex"
date: 2026-08-01T02:54:21+08:00
categories: ["技术笔记"]
tags: ["T3 Code", "Agent", "Claude Code", "Codex", "Cursor", "远程开发"]
description: "T3 Code 是 Theo（pingdotgg）开源的多端 agent 控制面，用 Effect RPC 把 Claude Code、Codex、Cursor、Grok Build、OpenCode 统一接到手机、浏览器和桌面，支持局域网、Tailscale、中继隧道与 SSH 四种远程方式。"
slug: pingdotgg-t3code-agent-harness-guide
github_repo: "pingdotgg/t3code"
---

# T3 Code：Theo 的 Agent 控制台，远程驾驭 Claude Code 与 Codex

AI 编程 agent（智能体）有个共同的物理约束：它们跑在你电脑的终端里，你就得坐在终端前。Claude Code 在跑一个跨文件重构时，你出去吃顿饭，回来发现它停在某个审批点等你——这半个小时本来可以不用坐在屏幕前。T3 Code 拆掉的正是这条绑定：agent 的进程仍在你的机器上，操控面搬到手机、浏览器和桌面，你在哪儿，控制台就在哪儿。

这个判断值得先说清楚：T3 Code 是壳，不是 agent。它不跑模型、不做代码生成，管理的是你已安装并认证的 agent 进程——把「坐在终端前」变成「躺在沙发上，偶尔低头看一眼」。评估它的时候，标准应该是「壳做得好不好」，而不是「它能不能写代码」。

## 目录

**理解篇**

- [一、它解决的是什么](#一它解决的是什么)
- [二、系统地图](#二系统地图)
- [三、核心机制](#三核心机制)
- [四、远程访问：四种连接目标](#四远程访问四种连接目标)
- [五、示例：一次 bug 修复如何流过系统](#五示例一次-bug-修复如何流过系统)

**实践篇**

- [六、与同类工具的对比](#六与同类工具的对比)
- [七、快速上手](#七快速上手)
- [八、常见问题 FAQ](#八常见问题-faq)
- [九、适用边界](#九适用边界)
- [十、采用建议](#十采用建议)

**学习篇**

- [十一、学习目标](#十一学习目标)
- [十二、自测题](#十二自测题)
- [十三、进阶方向](#十三进阶方向)
- [十四、参考资料](#十四参考资料)

## 一、它解决的是什么

T3 Code 的 README 把自己定位为 agent harness control surface——控制面，不是编辑器。它受 Codex 桌面应用、Conductor、Claude Desktop 等产品启发，但选了另一条路：把 agent 的操控从终端解放出来，同时保证所有执行仍发生在你自己的机器上。

| 维度 | 数据 |
|------|------|
| 仓库 | pingdotgg/t3code |
| Stars | 15,000+（2026-07） |
| 语言 | TypeScript（Effect 生态） |
| 许可证 | MIT |
| 作者 | Theo Browne（pingdotgg） |

项目 2026 年 2 月创建，半年出头冲到 15k stars，commit（提交）数 2,200+。增长快的一部分原因当然来自 Theo 的号召力，但仓库本身的做法——MIT、零遥测、自带各平台安装包、`npx t3@latest` 免安装体验——也是它被反复转发的理由。

## 二、系统地图

T3 Code 的架构可以压缩成一张图：客户端通过一条加密的 WebSocket 连到服务端，服务端通过驱动适配器指挥各个 agent CLI（命令行工具）。远程与否只体现在连接方式上，运行时本身从不拆分。

```mermaid
graph TB
    C[客户端<br/>Web/移动/桌面] -->|Effect RPC /ws| S[apps/server<br/>事件溯源编排]
    S -->|驱动适配| A[Agent CLI<br/>Codex/Claude/Cursor/Grok/OpenCode]
```

四个层次各管一件事：

| 层 | 职责 | 关键组件 |
|------|------|----------|
| 客户端层 | 连接管理、认证、RPC、Atom 状态 | packages/client-runtime |
| 服务编排层 | 事件溯源、投影、检查点、终端、文件系统 | OrchestrationEngine、DrainableWorker |
| Provider 层 | 驱动注册与适配 | 5 个内置 driver + adapter（适配器模式） |
| Agent 运行时 | 实际执行编码任务 | Codex / Claude / Cursor / Grok / OpenCode |

值得注意的分层原则：客户端只负责连接和渲染，所有 provider 进程、终端、git 操作、文件读取都发生在服务端。手机上的 App 再轻巧，也只是服务端状态的投影。

## 三、核心机制

### 3.1 编排：事件溯源，而不是轮询

T3 Code 的服务端不直接改应用状态。客户端派发类型化命令，编排引擎把命令变成持久化事件，再由投影器推导出读模型——这是标准的 event sourcing 结构，但落地得很彻底。

`OrchestrationEngine` 内部是一条单 worker 的命令队列，命令处理完全有序：先查持久化收据保证重试幂等，再用纯函数 `decider` 从「命令 + 当前状态」产出事件，最后在同一个 SQL 事务里追加事件、更新内存读模型、写回投影表、记录收据。因为持久化和投影共享一个事务，读模型永远不可能和事件日志不一致。

命令和事件在契约层有明确的命名边界。客户端可以派发 `thread.create`、`thread.turn.start`、`thread.approval.respond` 这类命令；而 `thread.message.assistant.delta`、`thread.turn.diff.complete` 这类事件只能由服务端 reactor 产出，客户端永远造不出来。turn 的结束也由投影器判定——session 离开 running 状态的那一刻，而不是检查点收尾的时刻。

为什么要这么大动干戈？因为 agent 会话天然是长时、异步、跨设备的。轮询 git 状态或定时器猜进度，一旦服务端重启或网络抖动，状态就对不上了。事件溯源让「发生了什么」成为唯一事实来源，任何客户端重连后都能从日志重建视图。

### 3.2 队列：DrainableWorker 与确定性等待

长时间运行的后续工作（provider 事件归一化、命令反应、检查点处理）跑在基于队列的工作器里。`DrainableWorker` 把事务性队列和事务性的未完成计数配对：入队即原子递增，处理完成必递减，`drain` 一直重试到计数归零。

这个设计最大的受益者是测试。异步里程碑不再靠「sleep 一会儿再断言」，而是等待「队列空且当前项完成」这个确定点。三个核心工作器（`ProviderRuntimeIngestion`、`ProviderCommandReactor`、`CheckpointReactor`）都暴露 `drain` 接口，测试代码可以精确地停在任意异步边界上。

`ProviderRuntimeIngestion` 里还有一个容易被忽略的取舍：assistant 文本默认走 buffered 交付，不逐字流式推送。缓冲上限是 24,000 字符，一旦某次追加会越过这个值，就把整段累积文本作为单个 delta 吐出去。客户端收到的是完整的、可读的块，代价是长回复会有一瞬间的停顿。对远程控制场景，手机上出现一段完整文字，比逐字蹦字更实用——这是把「流式体验」让位给「信息完整性」的明确决定。

### 3.3 Provider：五套驱动，一个抽象

服务端内置五个驱动：Codex、Claude、Cursor、Grok、OpenCode。每个驱动声明自己的类型、配置 schema（模式），并创建适配器；两个注册表把「配置的实例」和「活的进程」分开管理，`ProviderService` 路由会话和 turn 操作时根本不知道背后是哪个 agent。

加一个新 agent 的成本被压得很低：写一个 driver 加一个 adapter，注册进 `BUILT_IN_DRIVERS`，编排层、契约层、客户端一行都不用改。你本机装了什么 agent，T3 Code 就能驱动什么。

### 3.4 检查点：每一次 turn 都有快照

每个 turn 都被工作区检查点括起来，diff 和回滚因此是精确的。`CheckpointStore` 通过 VCS 驱动把状态存成隐藏的 Git ref——`VcsCheckpointOps` 是存储契约，Git 是当前唯一实现。`CheckpointReactor` 协调基线捕获、turn 完成捕获、diff 投影，以及工作区和 provider 会话的双重回滚。你在手机上看到的每一处 diff，背后都是一次真实的 Git 快照对比，不是模拟出来的「变更摘要」。

## 四、远程访问：四种连接目标

T3 Code 的远程模型一句话就能说清：远程是连接层的属性，不是运行时的拆分。客户端永远只认「一条到某个 T3 server 的 WebSocket」，至于这条 WebSocket 是怎么建立的，有四种目标：

| 目标类型 | 用途 |
|----------|------|
| 本地主连接 | 桌面应用或 CLI 管理的本机服务端 |
| Bearer 配对 | 手动配对任意直连 HTTP/WebSocket 端点 |
| Relay 中继 | `t3 connect` 托管隧道，穿透 NAT（网络地址转换） |
| SSH | 桌面应用托管 SSH 远程环境 |

局域网直连是最简单的方式，手机和服务器在同一个子网即可。服务器在 NAT 后面或要跨公网访问时，走 Relay 中继隧道——注意中继 Worker 只交换凭据和托管端点，应用流量走的是 Cloudflare 隧道主机名，不经过中继本身。Tailscale 用户可以直接用 `--tailscale` 把服务发布到 tailnet 的 HTTPS 地址。桌面应用还能通过 SSH 在远程机器上启动或复用 T3 server，再把端口转发回来。

配对流程设计得比传统 token（令牌）登录干净：`t3 serve`（或对运行中的服务器执行 `t3 pair`）签发一次性配对 token，远程设备用它交换会话，之后访问全部基于会话，不需要长期秘密。WebSocket 的认证票据独立签发，默认五分钟过期，且每个 RPC 方法还各自校验权限范围——拿到一条合法连接不代表能调所有方法。会话管理单独交给 `t3 auth`：签发额外凭据、查看活跃会话、吊销不再信任的配对，都在这一条命令下完成。

客户端和远程服务器版本不一致时，连接层不会静默失败：环境描述符携带运行中的服务器版本，UI 据此显示对应的同步操作，服务端也支持更新回滚。远程环境在客户端升级期间保持在线，断线重连由连接管理器统一处理，和普通网络抖动走同一条恢复路径。

## 五、示例：一次 bug 修复如何流过系统

用这个最常见的场景做示例：你在手机上看到 CI 报了一个 TypeScript 类型错误，想远程让 agent 修掉。

1. 手机打开 T3 Code App，选 Claude Code 作为 provider
2. 输入指令：「修复 src/utils/parser.ts 第 42 行的类型错误，错误信息是 …」
3. 客户端经 WebSocket 发出 `thread.turn.start` 命令，RPC 层完成鉴权
4. 引擎持久化该事件，`ProviderCommandReactor` 据此派发 provider 调用
5. Claude Code 在服务器上读取文件、分析类型、生成修改、写回磁盘

到这里，agent 在服务器上干它的活，手机可以锁屏。异步里程碑由服务端队列推进，与设备是否在线无关：

6. `ProviderRuntimeIngestion` 消费 Claude Code 的事件流，归一化为编排命令
7. 遇到需要授权的操作，agent 停在审批点，手机收到 `thread.approval.respond` 请求，你点一下批准
8. `CheckpointReactor` 捕获 turn 完成时的快照，投影出 diff
9. 服务端通过订阅推送把进度和 diff 实时同步到手机
10. 你审阅 diff，点一键 PR，分支和变更日志自动就位

整个过程里，手机上流动的只有指令和状态；代码执行、git 操作、文件变更全部发生在服务器上。

## 六、与同类工具的对比

agent 远程控制和编排不是 T3 Code 独有。拿它跟几个常被一起提起的工具比，差异立刻清晰：

| 特性 | T3 Code | Parallel Code | Superset |
|------|---------|---------------|----------|
| 多 agent | Codex/Claude/Cursor/Grok/OpenCode | 通用 | 通用 |
| 远程控制 | ✅ 移动/Web/桌面 | ❌ 仅桌面 | ❌ 仅桌面 |
| 线程→Git 分支 | ✅ | ✅ | ✅ |
| 一键 PR | ✅ 自动变更日志 | ❌ | ❌ |
| 许可证 | MIT | 不开源 | Elastic 2.0（source-available） |

T3 Code 的差异化优势是远程控制和多 agent 统一入口。Superset 走的是「编辑器形态 + 十路并行」路线，Parallel Code 强调每个 agent 独立 workspace。想离开电脑操作 agent，T3 Code 目前是最直接的选择；如果你的痛点是一次跑十个 agent，Superset 的方向可能更接近你的需求。

## 七、快速上手

```bash
# 最简方式，需 Node.js 22.16+ / 23.11+ / 24.10+
npx t3@latest

# 完整 CLI 参考
npx t3@latest --help
```

**前置条件**：至少安装并认证一个 agent——`claude auth login`、`codex login`、`agent login`（Cursor）、`grok login` 或 `opencode auth login`，确认它在终端能正常跑。T3 Code 不产生 agent 能力，它只接管你已有的。

桌面安装走各平台包管理器：Windows 用 `winget install T3Tools.T3Code`，macOS 用 `brew install --cask t3-code`，Arch 用 `yay -S t3code-bin`。远程访问的完整配置见 [remote-access.md](https://github.com/pingdotgg/t3code/blob/main/docs/user/remote-access.md)。

## 八、常见问题 FAQ

**Agent 列表为空或显示未认证**
确认 agent 已在本机安装并完成认证。依次运行 `claude auth login`、`codex login` 等命令，成功后重启服务端刷新状态。

**手机无法连接到服务器**
先确认手机和服务器在同一网络，或已配置 Tailscale。在服务器上运行 `npx t3 pair` 生成二维码扫描配对，不要手输 IP。`--tailscale` 选项要求 Tailscale 已登录并运行。服务器在 NAT 后面时改用 `t3 connect` 中继隧道。

**WebSocket 频繁断连**
T3 Code 的实时通道依赖 WebSocket，弱网可能断连。优先在稳定网络下使用，或换 SSH 隧道。Linux 上以 systemd 服务运行时，用 `journalctl -u t3code` 查日志。

**如何更新 T3 Code**
`npx t3@latest` 每次运行自动拉最新版；桌面 App 在 GitHub Releases 下载新版，macOS 可 `brew upgrade t3-code`。注意客户端和远程服务器版本不一致时，界面会提示同步操作，更新前先结束进行中的任务——服务端会短暂重启。

## 九、适用边界

**适合**：

- 已在用 Claude Code / Codex / Cursor 的开发者，想把监控从终端挪到手机
- 需要跨设备接管编码 agent 的场景（公司机器跑任务，回家继续盯）
- 同时用多个 agent 后端、想要一个统一入口的人
- 想要线程自动分支 + 一键 PR 的开发者

**不适合**：

- 没有 agent 订阅的用户——T3 Code 本身不产生任何智能
- 需要深度定制或大功能贡献的团队——README 明确「mostly not accepting contributions yet」，目前只收小修复
- 对 Electron 体积和内存敏感的场景
- 弱网下对连接稳定性有苛刻要求的场景（需自行验证）

## 十、采用建议

个人开发者如果已经在用 Claude Code 或 Codex，从 `npx t3@latest` 开始，花十分钟验证远程流程是否通顺。如果只在本地用终端，T3 Code 的价值有限——它的溢价在「离开电脑」这个动作上。

小团队有人专门负责 agent 机器的话，远程控制和 Git 工作流自动化能省掉「谁在哪个 agent 上跑了什么」的沟通损耗。但项目不收大贡献，遇到特定 bug 别指望能快速修掉，要有自己绕路的准备。

正在评估 agent 编排方案的话，同时看 T3 Code 和 Superset：前者强在远程和多 agent 统一入口，后者强在并行规模和编辑器形态。两者解决的不是同一个维度的问题。

## 十一、学习目标

读完这篇文章，你应该能回答四个问题：T3 Code 在架构上如何实现「远程是连接层属性」；事件溯源为什么比轮询更适合 agent 会话；五个内置驱动如何做到增删 agent 不动编排层；四种连接目标分别在什么网络条件下使用。能复述「客户端不执行任何 agent 工作」这条边界，说明理解到位了。

## 十二、自测题

1. 为什么 T3 Code 坚持把 provider 进程、git 操作、文件读取全部放在服务端，而不是客户端？
2. 事件溯源中，`decider` 为什么要保持纯函数、无副作用？
3. 手机锁屏后 agent 为什么还能继续执行？服务端靠什么机制保证这一点？
4. Relay 中继和传统反向代理有什么区别？流量最终走哪条路？

答案都在正文的机制段落里，答不上来的小节回去重读对应章节。

## 十三、进阶方向

- 读 [架构文档](https://github.com/pingdotgg/t3code/blob/main/docs/internals/overview.md)，关注 `OrchestrationEngine` 的命令/事件循环和 `DrainableWorker` 的队列语义
- 读 [providers.md](https://github.com/pingdotgg/t3code/blob/main/docs/internals/providers.md)，理解 driver + adapter 的分工，试着自己为某个 CLI agent 写一个最小驱动
- 动手搭一条 SSH 远程环境，观察配对票据的签发与 WebSocket 的鉴权流程，把「连接层 vs 运行时」的抽象亲手验证一遍

## 十四、参考资料

- 仓库：[github.com/pingdotgg/t3code](https://github.com/pingdotgg/t3code)
- 架构总览：[docs/internals/overview.md](https://github.com/pingdotgg/t3code/blob/main/docs/internals/overview.md)
- Provider 机制：[docs/internals/providers.md](https://github.com/pingdotgg/t3code/blob/main/docs/internals/providers.md)
- 远程架构：[docs/internals/remote.md](https://github.com/pingdotgg/t3code/blob/main/docs/internals/remote.md)
- 远程访问指南：[docs/user/remote-access.md](https://github.com/pingdotgg/t3code/blob/main/docs/user/remote-access.md)
- Web App：[app.t3.codes](https://app.t3.codes)
