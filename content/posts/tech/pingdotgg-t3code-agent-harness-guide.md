---
title: "T3 Code：Theo 的 Agent 控制台，远程驾驭 Claude Code 与 Codex"
date: "2026-08-01T02:54:21+08:00"
slug: pingdotgg-t3code-agent-harness-guide
github_repo: "pingdotgg/t3code"
description: "T3 Code 是 Theo（pingdotgg）开源的多端 agent 控制面，用 Effect RPC 把 Claude Code、Codex、Cursor、Grok Build、OpenCode 统一接到手机、浏览器和桌面，支持局域网、Tailscale、中继隧道与 SSH 四种远程方式。"
categories: ["技术笔记"]
tags: ["T3 Code", "Agent", "Claude Code", "Codex", "Cursor", "远程开发"]
---

# T3 Code：Theo 的 Agent 控制台，远程驾驭 Claude Code 与 Codex

AI 编程 agent（智能体）都有一个逃不掉的约束：它们跑在你电脑的终端里，你就得坐在终端前。Claude Code 在跑一个跨文件重构时，你出去吃顿饭，回来发现它停在某个审批点等你——这半小时本可以不用守在屏幕前。T3 Code 拆掉的正是这个约束：agent 的进程仍在你的机器上，操控面搬到手机、浏览器和桌面，你在哪儿，控制台就在哪儿。

先把判断亮出来：T3 Code 是壳，不是 agent。它不跑模型、不做代码生成，管理的是你已安装并认证的 agent 进程——把「坐在终端前」变成「躺在沙发上，偶尔低头看一眼」。评估它，标准是这层壳顺不顺手，代码能力不归它管。

README 里有一句它自己的回答，比任何介绍都诚实。被问「你到底在卖什么」时，它写的是「Nothing」——他们做 T3 Code，是因为想要最好用的 agent 开发体验，而 Codex 桌面应用、Conductor、Claude Desktop、Cursor Glass 这些现成方案都没到他们的标准。它想做到性能好、能远程、真正开放，并明说「万一走错了方向，你会拿到 fork 和构建自己编辑器所需的一切」。这句「真正开放」不是口号，仓库 MIT、不上传遥测、自带安装包，都是它的兑现。

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

T3 Code 的 README 把自己定位为 agent harness control surface——控制面。它受 Codex 桌面应用、Conductor、Claude Desktop、Cursor Glass 等产品启发，但选了另一条路：把 agent 的操控从终端解放出来，同时保证所有执行仍发生在你自己的机器上。

| 维度 | 数据 |
|------|------|
| 仓库 | pingdotgg/t3code |
| Stars | 16,000+（2026-08） |
| Forks | 3,600+ |
| 语言 | TypeScript（Effect 生态） |
| 许可证 | MIT |
| 作者 | Theo Browne（pingdotgg） |

项目 2026 年 2 月 8 日创建，半年出头冲到 16k stars，commit（提交）数 2,200+。增长快，一部分靠 Theo 的号召力，但仓库本身的做法——MIT、不上传遥测、自带各平台安装包、`npx t3@latest` 免安装体验——同样经得起传播。开 issue 数超过 1,000。

## 二、系统地图

T3 Code 的架构可以压缩成一张图：客户端通过一条 WebSocket 连到服务端，服务端通过驱动适配器指挥各个 agent CLI（命令行工具）。这张图里没有「远程模式」和「本地模式」之分——客户端在哪，不影响服务端怎么跑。

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

分层原则很干脆：客户端只负责连接和渲染，所有 provider 进程、终端、git 操作、文件读取都发生在服务端。手机上的 App 再轻巧，也只是服务端状态的投影。

客户端和服务端之间的契约，是 Effect RPC 组，不是自造的推送协议。`rpc.ts` 声明 `WS_METHODS` 并组装 `WsRpcGroup`，每个成员要么是 unary（单次调用）要么是服务端流（`stream: true`）。`orchestration.subscribeThread`、`orchestration.subscribeShell`、`subscribeServerConfig`、`terminal.attach` 这些流式成员，取代了原来那种广播推送总线：客户端只订阅自己需要的，服务端只在对应订阅上推送。想实时看某条线程的 diff，就订阅它；不想看 shell，就不订阅。

## 三、核心机制

### 3.1 编排：事件溯源，不靠轮询

T3 Code 的服务端不直接改应用状态。客户端派发类型化命令，编排引擎把命令变成持久化事件，再由投影器推导出读模型——标准的 event sourcing 结构。命令的入口是唯一一个 RPC 方法 `orchestration.dispatchCommand`，客户端永远不会直接调某个 provider。

`OrchestrationEngine` 内部是一条单 worker 的命令队列，命令处理完全有序：先查持久化收据保证重试幂等，再用纯函数 `decider` 从「命令 + 当前状态」产出事件，最后在同一个 SQL 事务里追加事件、更新内存读模型、写回投影表、记录收据。因为持久化和投影共享一个事务，读模型永远不可能和事件日志不一致。派发失败时，引擎会重读起始序列之后的事件对账，而不是把状态交给猜测。`decider` 保持纯函数不是洁癖——事件要能重放，重放要能得出同样结果，任何副作用（写文件、发请求、读时钟）都会让重放失真。

命令和事件在契约层有明确的命名边界。客户端可以派发 `thread.create`、`thread.turn.start`、`thread.approval.respond` 这类命令；而 `thread.message.assistant.delta`、`thread.turn.diff.complete` 这类事件只能由服务端 reactor 产出，客户端造不出来。turn 何时结束也由投影器判定——session 离开 running 状态的那一刻，而不是检查点收尾的时刻。

为什么绕这么大一圈？因为 agent 会话天然是长时、异步、跨设备的。轮询 git 状态或定时器猜进度，一旦服务端重启或网络抖动，状态就对不上了。事件溯源让「发生了什么」成为唯一事实来源，任何客户端重连后都能从日志重建视图。

### 3.2 队列：DrainableWorker 与确定性等待

长时间运行的后续工作（provider 事件归一化、命令反应、检查点处理）跑在基于队列的工作器里。`DrainableWorker` 把事务性队列和事务性的未完成计数配对：入队即原子递增，处理完成必递减，`drain` 一直重试到计数归零。

这个设计最直接的受益者是测试。异步里程碑不再靠「sleep 一会儿再断言」，而是等待「队列空且当前项完成」这个确定点。三个核心工作器（`ProviderRuntimeIngestion`、`ProviderCommandReactor`、`CheckpointReactor`）都暴露 `drain` 接口，测试代码可以精确地停在任意异步边界上。

`ProviderRuntimeIngestion` 里还有一个容易被忽略的取舍：assistant 文本默认走 buffered 交付，不逐字流式推送。缓冲上限是 24,000 字符，一旦某次追加会越过这个值，就把整段累积文本作为单个 delta 吐出去。缓冲并非死等到 turn 结束才清空——在交互边界（审批请求弹出、需要用户输入）时也会整体冲刷。客户端收到的是完整的、可读的块，代价是长回复会有一瞬间的停顿。对远程控制场景，手机上出现一段完整文字，比逐字蹦字更实用——取舍而已。

### 3.3 Provider：五套驱动，一个抽象

服务端内置五个驱动：Codex、Claude、Cursor、Grok、OpenCode。每个驱动声明自己的类型、配置 schema（模式），并创建适配器；两个注册表把「配置的实例」和「活的进程」分开管理——`ProviderInstanceRegistry` 管实例，`ProviderAdapterRegistry` 把实例解析成活的适配器，`ProviderService` 路由会话和 turn 操作时根本不知道背后是哪个 agent。

客户端面向 provider 的命令也走同一个抽象：`thread.turn.start`、`thread.turn.interrupt`、`thread.approval.respond`、`thread.user-input.respond`、`thread.checkpoint.revert`、`thread.session.stop`，外加两个模式设定 `thread.runtime-mode.set`、`thread.interaction-mode.set`。调用方只认线程，不认 agent。

加一个新 agent 的成本被压得很低：写一个 driver 加一个 adapter，注册进 `BUILT_IN_DRIVERS`，编排层、契约层、客户端一行都不用改。你本机装了什么 agent，T3 Code 就能驱动什么。

### 3.4 检查点：每一次 turn 都有快照

每个 turn 都被工作区检查点括起来，diff 和回滚因此是精确的。`CheckpointStore` 通过 VCS 驱动把状态存成隐藏的 Git ref——`VcsCheckpointOps` 是存储契约，Git 是当前唯一实现。`CheckpointReactor` 协调基线捕获、turn 完成捕获、diff 投影，以及工作区和 provider 会话的双重回滚；`CheckpointDiffQuery` 负责回答单次 turn 或整条线程的 diff 请求。你在手机上看到的每一处 diff，背后都是一次真实的 Git 快照对比。

## 四、远程访问：四种连接目标

T3 Code 的远程模型一句话就能说清：远程只存在于连接层，运行时从不拆分。客户端永远只认「一条到某个 T3 server 的 WebSocket」，至于这条 WebSocket 是怎么建立的，有四种目标。容易误判的是 Tailscale：它不是第五种目标类型，只是走普通 bearer 配对路径接入的端点提供者，接不接都不改核心模型。

| 目标类型 | 用途 |
|----------|------|
| 本地主连接 | 桌面应用或 CLI 管理的本机服务端 |
| Bearer 配对 | 手动配对任意直连 HTTP/WebSocket 端点 |
| Relay 中继 | `t3 connect` 托管隧道，穿透 NAT（网络地址转换） |
| SSH | 桌面应用托管 SSH 远程环境 |

局域网直连是最简单的方式，手机和服务器在同一个子网即可。服务器在 NAT 后面或要跨公网访问时，走 Relay 中继隧道——注意中继 Worker 只交换凭据和托管端点，应用流量走的是 Cloudflare 隧道主机名，不经过中继本身。Tailscale 用户可以直接用 `npx t3 pair --tailscale` 把服务发布到 tailnet 的 HTTPS 地址，那个映射会一直保留到你手动关掉 `tailscale serve --https=443 off`。桌面应用还能通过 SSH 在远程机器上启动或复用 T3 server，再把端口转发回来。

配对流程设计得比传统 token（令牌）登录干净：`t3 serve`（或对运行中的服务器执行 `t3 pair`）签发一次性配对 token，远程设备用它交换会话，之后访问全部基于会话，不需要长期秘密。桌面应用里还能用「Create Link」生成一个配对链接，直接分享给另一台设备。WebSocket 的认证票据独立签发，默认五分钟过期，且每个 RPC 方法还各自校验权限范围——拿到一条合法连接不代表能调所有方法。会话管理单独交给 `t3 auth`：签发额外凭据、查看活跃会话、吊销不再信任的配对，都在这一条命令下完成。

托管配对（app.t3.codes）只是个客户端便利，不是中继。它不代理 HTTP 或 WebSocket 流量，浏览器直接连你给的后端地址，配对 token 放在 URL hash 里，连托管页都看不到。前提是后端必须能被浏览器直接访问——HTTPS 页面只能连 HTTPS/WSS 后端，纯 HTTP 的局域网地址还得走桌面或 CLI 的直连配对。

客户端和服务端版本不一致时，连接层不会静默失败：环境描述符携带运行中的服务端版本，UI 据此显示对应的同步操作，服务端也支持更新回滚。远程环境在客户端升级期间保持在线，断线重连由连接管理器统一处理，和普通网络抖动走同一条恢复路径。

## 五、示例：一次 bug 修复如何流过系统

最常见的场景：你在手机上看到 CI 报了一个 TypeScript 类型错误，想远程让 agent 修掉。

1. 手机打开 T3 Code App，选 Claude Code 作为 provider
2. 输入指令：「修复 src/utils/parser.ts 第 42 行的类型错误，错误信息是 …」
3. 客户端经 WebSocket 发出 `orchestration.dispatchCommand`，携带 `thread.turn.start` 命令，RPC 层完成鉴权
4. 引擎持久化该事件，`ProviderCommandReactor` 据此派发 provider 调用
5. Claude Code 在服务器上读取文件、分析类型、生成修改、写回磁盘

到这里，agent 在服务器上继续跑，手机可以锁屏。异步里程碑由服务端队列推进，与设备是否在线无关：

6. `ProviderRuntimeIngestion` 消费 Claude Code 的事件流，归一化为编排命令
7. 遇到需要授权的操作，agent 停在审批点，手机弹出审批请求，你点一下批准，客户端据此派发 `thread.approval.respond` 命令
8. `CheckpointReactor` 捕获 turn 完成时的快照，`CheckpointDiffQuery` 投影出 diff
9. 服务端通过 `orchestration.subscribeThread` 订阅推送把进度和 diff 实时同步到手机
10. 你审阅 diff，点一键 PR，分支和变更日志自动就位

整个过程里，手机上流动的只有指令和状态；代码执行、git 操作、文件变更全部发生在服务器上。

## 六、与同类工具的对比

agent 远程控制和编排不是 T3 Code 独有。拿它跟几个常被一起提起的工具摆在一起看（以下对 Parallel Code、Superset 的描述按其公开产品信息归纳，细节可能随版本变化）：

| 特性 | T3 Code | Parallel Code | Superset |
|------|---------|---------------|----------|
| 多 agent | Codex/Claude/Cursor/Grok/OpenCode | 通用 | 通用 |
| 远程控制 | ✅ 移动/Web/桌面 | ❌ 仅桌面 | ❌ 仅桌面 |
| 线程→Git worktree | ✅ | 独立 workspace | 未披露 |
| 一键 PR | ✅ 自动变更日志 | 未披露 | 未披露 |
| 许可证 | MIT | 不开源 | Elastic 2.0（source-available） |

T3 Code 的取舍很清晰：远程控制和多 agent 统一入口。Superset 走的是「编辑器形态 + 十路并行」路线，Parallel Code 强调每个 agent 独立 workspace。想离开电脑操作 agent，T3 Code 目前是最直接的选择；如果一次要跑十个 agent，Superset 的方向可能更接近你的需求。

它和 Cursor、Copilot 也不是一类东西。Cursor 是 AI 优先的编辑器，Copilot 是 IDE（集成开发环境）里的插件，都长在编辑生态内；T3 Code 站在 IDE 之外，管理的是完整的 agent 会话——它不依赖你用哪个编辑器，你甚至可以没有编辑器，只有终端。两者可以共存，不构成替代关系。

## 七、快速上手

```bash
# 最简方式，需 Node.js 22.16+ / 23.11+ / 24.10+
npx t3@latest

# 完整 CLI 参考
npx t3@latest --help
```

**前置条件**：至少安装并认证一个 agent——`claude auth login`、`codex login`、`agent login`（Cursor）、`grok login` 或 `opencode auth login`，确认它在终端能正常跑。T3 Code 不产生 agent 能力，它只驱动你已经有的。

桌面安装走各平台包管理器：Windows 用 `winget install T3Tools.T3Code`，macOS 用 `brew install --cask t3-code`，Arch 用 `yay -S t3code-bin`。远程访问的完整配置见 [remote-access.md](https://github.com/pingdotgg/t3code/blob/main/docs/user/remote-access.md)。

## 八、常见问题 FAQ

**Agent 列表为空或显示未认证**
确认 agent 已在本机安装并完成认证。依次运行 `claude auth login`、`codex login` 等命令，成功后重启服务端刷新状态。

**手机无法连接到服务器**
先确认手机和服务器在同一网络，或已配置 Tailscale。在服务器上运行 `npx t3 pair` 生成二维码扫描配对，不要手输 IP。`--tailscale` 选项要求 Tailscale 已登录并运行，发布后想关掉映射就执行 `tailscale serve --https=443 off`。服务器在 NAT 后面时改用 `t3 connect` 中继隧道。桌面 App 用户也可以走 Settings → Connections 的图形化配对流程，或直接用 Create Link 生成配对链接。

**WebSocket 频繁断连**
T3 Code 的实时通道依赖 WebSocket，弱网可能断连。优先在稳定网络下使用，或换 SSH 隧道。Linux 上以 systemd 后台服务运行时，用 `npx t3@latest service status` 检查服务状态，`npx t3@latest service update` 修复。

**如何更新 T3 Code**
`npx t3@latest` 每次运行自动拉最新版；桌面 App 在 GitHub Releases 下载新版，macOS 可 `brew upgrade t3-code`。注意客户端和服务端版本不一致时，界面会提示同步操作，更新前先结束进行中的任务——服务端会短暂重启。

**T3 Code 免费吗**
开源免费，MIT 许可证。费用只来自你已有的 agent 订阅——Claude Code、Codex 等各自的账单，T3 Code 本身不额外收费。

**数据会经过第三方服务器吗**
不会。agent 进程、文件、git 操作都发生在你自己的机器上，客户端只传输指令和状态。项目唯一的遥测是本地资源监控——一个独立的 Rust 监控进程采样 CPU 和内存，历史只在诊断时汇总，不落盘、不上传，也不是行为追踪。即使走托管配对（app.t3.codes），浏览器也是直连你的后端，配对 token 放在 URL hash（哈希）里，不经托管页转手。

**如何反馈问题**
GitHub Issues 提交 bug（不保证修复速度），Discord 社区讨论。项目明确「mostly not accepting contributions yet」，小修复可能被考虑，大功能不要抱期待。

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

个人开发者如果已经在用 Claude Code 或 Codex，从 `npx t3@latest` 开始，花十分钟验证远程流程是否通顺。如果只在本地用终端，T3 Code 的价值有限——它的溢价全在「离开电脑」这个动作上。

小团队有人专门负责 agent 机器的话，远程控制和 Git 工作流自动化能省掉「谁在哪个 agent 上跑了什么」的沟通损耗。但项目不收大贡献，遇到特定 bug 别指望能快速修掉，要有自己绕路的准备。

正在评估 agent 编排方案的话，同时看 T3 Code 和 Superset：前者强在远程和多 agent 统一入口，后者强在并行规模和编辑器形态。两者解决的不是同一个维度的问题。

## 十一、学习目标

读完这篇文章，四个问题应该能回答：T3 Code 在架构上如何实现「远程只存在于连接层」；事件溯源为什么比轮询更适合 agent 会话；五个内置驱动如何做到增删 agent 不动编排层；四种连接目标分别在什么网络条件下使用。能复述「客户端不执行任何 agent 工作」这条边界，说明理解到位了。

## 十二、自测题

1. 为什么 T3 Code 把 provider 进程、git 操作、文件读取全部放在服务端，而不是客户端？
2. 事件溯源中，`decider` 为什么要保持纯函数、无副作用？
3. 手机锁屏后 agent 为什么还能继续执行？服务端靠什么机制保证这一点？
4. Relay 中继和传统反向代理有什么区别？流量最终走哪条路？
5. 为什么说 Tailscale 不是第五种连接目标？它接入的路径是什么？

答案都在正文的机制段落里，答不上来的小节回去重读对应章节。

## 十三、进阶方向

- 读 [架构文档](https://github.com/pingdotgg/t3code/blob/main/docs/internals/overview.md)，关注 `OrchestrationEngine` 的命令/事件循环和 `DrainableWorker` 的队列语义
- 读 [providers.md](https://github.com/pingdotgg/t3code/blob/main/docs/internals/providers.md)，理解 driver + adapter 的分工，试着自己为某个 CLI agent 写一个最小驱动
- 动手搭一条 SSH 远程环境，观察配对票据的签发与 WebSocket 的鉴权流程，把「连接层 vs 运行时」的抽象亲手验证一遍
- 读 [remote.md](https://github.com/pingdotgg/t3code/blob/main/docs/internals/remote.md)，对照四种目标类型和端点提供者模型，理解「访问方式」和「启动方式」为什么是两个独立概念

## 十四、参考资料

- 仓库：[github.com/pingdotgg/t3code](https://github.com/pingdotgg/t3code)
- 架构总览：[docs/internals/overview.md](https://github.com/pingdotgg/t3code/blob/main/docs/internals/overview.md)
- Provider 机制：[docs/internals/providers.md](https://github.com/pingdotgg/t3code/blob/main/docs/internals/providers.md)
- 远程架构：[docs/internals/remote.md](https://github.com/pingdotgg/t3code/blob/main/docs/internals/remote.md)
- 远程访问指南：[docs/user/remote-access.md](https://github.com/pingdotgg/t3code/blob/main/docs/user/remote-access.md)
- 资源遥测：[docs/internals/resource-telemetry.md](https://github.com/pingdotgg/t3code/blob/main/docs/internals/resource-telemetry.md)
- Web App：[app.t3.codes](https://app.t3.codes)