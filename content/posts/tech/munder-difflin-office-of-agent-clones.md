---
title: "Munder Difflin：把你已付费的终端 Agent CLI 编成一间会自我协调的办公室"
date: 2026-08-27T03:40:00+08:00
slug: "munder-difflin-office-of-agent-clones"
github_repo: "chaitanyagiri/munder-difflin"
source_key: "gh:chaitanyagiri/munder-difflin"
description: "Munder Difflin 是一个本地多智能体 harness，把 Claude Code、Codex、Grok 等终端 Agent CLI 包装成有记忆、有邮箱、有工位的克隆员工，由一个 GOD 编排者调度。本文拆解它的 hive 协作层设计与消息协议。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "多智能体协作", "Harness", "Claude Code", "本地部署"]
---

> **先给判断**：Munder Difflin 不是又一个新的 Agent 框架——它一个字节都不替换你已有的 Agent 运行时。它的全部工作是在 `claude`、`codex`、`grok` 这些终端 CLI 外面包一层"办公室"：每个 CLI 进程是一个有长期记忆和邮箱的员工，一个叫 Michael 的 GOD 编排者负责分活、仲裁、升级上报，而你只跟 Michael 说话。理解它的钥匙是仓库里的 `HIVE.md`：一份把经典多智能体模式（黑板、信息素、actor 邮箱、supervisor）钉在"纯文件 + 单提交者 git"上的设计契约。

## 1. 它解决什么问题

2026 年的普遍处境是：你同时订阅了 Claude、Codex、Gemini，每个都有 CLI，每个都在自己的终端窗口里孤独地干活。开三个窗口手动复制粘贴上下文，是人肉当路由器。

Munder Difflin（名字致敬《办公室》里的纸业公司 Dunder Mifflin）的答案是：**不做新模型、不做新 Agent 运行时，只做协调层**。每个你已付费的 CLI 订阅，在它的小时额度内变成"你的克隆"——它们互相发消息、共享记忆、自己认领任务，你在旁边看虚拟办公室里化身走来走去。

这个定位决定了它的几个硬约束：

- **免费开源**（README 标注 MIT，GitHub license 字段显示为自定义 Other），Electron + React + TypeScript 桌面应用，macOS / Windows / Linux 三平台；
- **BYOK**：每个 provider 的 key 自己带，另支持 Ollama / LM Studio / vLLM 本地模型；
- **本地优先**：hive 数据全部是你机器上的一个 git 仓库，没有云端依赖。

## 2. 系统地图：一条从人到 GOD 到员工的命令链

整个系统只有四个角色，职责边界非常干净：

| 角色 | 是什么 | 干什么 |
|------|--------|--------|
| 你 | 人 | 只跟 Michael 说话，批处理 escalated 的关键事项 |
| GOD agent（Michael） | 一个特权编排进程 | 读所有请求、路由任务、仲裁冲突；常规请求自己消化，只有花钱 / 破坏性操作 / 范围变更才上报 |
| Agent 员工 | 真实的 CLI 进程（claude / agy / codex / grok / kimi / qwen / opencode / crush / pi / copilot / 自定义） | 干活，读写自己的记忆，收发消息 |
| hive | 本地 git 仓库里的纯文件层 | 记忆、邮箱、黑板、任务账本、事件日志 |

渲染层是 Pixi.js 的 2D 办公室楼层——化身走到工位表示在工作，信封在办公桌之间飞表示消息在传递。这不是装饰：它把"多 Agent 系统最难的可观测性"做成了肉眼可见的状态机。每个终端都是 `node-pty` 里跑的真实 PTY 进程，用 xterm.js 逐字节渲染，你随时可以打字插进去。

## 3. hive 协作层：设计文档里最值钱的部分

`HIVE.md` 开篇就承认它"缝合"了五个经典模式，并且逐一给了对应关系——这种诚实本身就是好工程的味道：

| 用户要的行为 | 模式名 |
|--------------|--------|
| Agent 出生时拿到记忆文件、自己读写 | Agent 长期记忆（MemGPT / Letta 式） |
| 往另一个 Agent 的文件里写需求 | 信息素（Stigmergy，靠修改共享环境协调） |
| 多个 Agent 共同编辑一份计划 | 黑板架构（Hearsay-II） |
| "每完成一个任务就检查收件箱" | 邮箱 / Actor 模型 |
| 一个"神"替大家澄清和分活 | Orchestrator / Supervisor |

作者还点出最近的学术近亲是斯坦福的 Generative Agents（Park et al., 2023）——同样是有记忆流、检索、反思和规划的 2D 化身。差异在于：Generative Agents 是社会模拟研究，Munder Difflin 把同一套结构压到"真实的 CLI 进程 + 真实的工程任务"上。

### 3.1 五条锁定的设计决策

`HIVE.md` 的 "Locked design decisions" 一节值得逐条读，因为每条都是踩过坑之后的反直觉选择：

**1. git 只做协调与审计，且只有一个提交者。** hive 的一切都是文件，但 Agent 从不调用 git——只有 Electron 主进程提交。这是为了避免多进程并发下的 `.git/index.lock` 损坏，作者还引了 GitHub Desktop 的提交队列和 lazygit 的重试退避作为参照。

**2. 单写者原则。** 每个 Agent 只写自己 `agents/<id>/` 目录下的文件。跨 Agent 递送由主进程的 router 完成：从发送者的 `outbox/` 搬进接收者的 `inbox/`。任何文件都不会被两个进程同时写。

**3. 自主优先，人机协作原生。** 常规请求（澄清、要数据、微调计划）GOD 自己解决，系统保持全自动运转；只有关键事项才升级给人——而且没有独立的审批队列，升级就发生在 Michael 自己的 Claude Code 会话里，工具权限提示本身就是 HITL 闸门，还能通过 `/remote-control` 从手机上批。

**4. 记忆 markdown 优先。** 每个 Agent 一个 `memory.md`，外加共享黑板；关键词检索不够时才上 SQLite FTS 索引。作者明确拒绝了 Letta / Mem0 / Zep 这类重型向量记忆层，理由是 5–15 个 Agent 的规模用不上，而且它们想吞掉 Agent 运行时——而这里的运行时是 `claude` CLI 本身。

**5. 自主循环 = Stop hook。** Agent 干完活由 `Stop` hook 返回 `{"decision":"block","reason":…}` 逼它继续处理收件箱，用 `stop_hook_active` 防无限循环。

### 3.2 磁盘布局：一个可以直接读的协作协议

hive 目录本身就是文档：

```
hive/
  PROTOCOL.md            # Agent 侧契约：怎么记忆、怎么发消息
  registry.json          # 花名册：每个 Agent 的角色、能力、状态、工位
  board.md               # 共享黑板 / 共同编辑的计划
  tasks.json             # 任务账本（id、负责人、规格、状态、结果引用）
  log.jsonl              # 只追加的事件流（驱动 UI 活动流）
  agents/<agentId>/
    identity.md          # 我是谁、我的角色和能力（启动时读）
    memory.md            # 我的长期记忆（启动时读，学到东西就追加）
    inbox/               # 递送给我的消息，一消息一 JSON 文件
    inbox/.done/         # 已处理消息留档审计
    outbox/              # 我想发的消息，router 来取
    cursor.json          # { lastProcessed: <msgid> }，防重复处理
```

三条让它健壮的细节：消息一律"临时文件 + 原子 `rename`"写入，绝不做共同编辑的共享邮箱文件；`log.jsonl` 只追加，消费者自己管游标；`board.md` 是唯一真正共编的文件，所以它必须经过 GOD（唯一抄写员）落笔。

### 3.3 消息模式：FIPA 的减法

消息 schema 借了 FIPA-ACL / KQML 唯一有用的概念——**speech act（言语行为）**——然后扔掉 LISP 语法，只留七个语义字段。这个取舍和整个仓库的气质一致：不发明协议，只取被四十年多智能体研究验证过的最小内核。

## 4. 控制与安全：把"驯服 Agent"做成阶梯

多 Agent 系统真正的风险不是不够聪明，而是失控时的破坏半径。Munder Difflin 给了一套完整的约束装置：

- **人工闸门**：花费、范围、破坏性操作升级到你；
- **熔断器**：对循环、错误风暴、超预算的 Agent 执行"转向 → 约束 → 停止"三级阶梯；
- **预算与遥测**：每 Agent token 预算、从会话记录算真实成本、持久账本、OTel spans、工具调用瀑布图；
- **可选 git worktree 隔离**：并行 Agent 各用各的工作树，永不撞分支。

外围还有 Slack / webhook 入口（Michael 可以起临时工人、线程内回复、用完销毁）、`munderdifflin://hire` 分享链接的"招聘"、以及 227 个可浏览安装的 skills 目录。

## 5. 上手与适用边界

当前状态是 **working prototype**（v0.4.5），三平台桌面应用。前置依赖会由一个 Settings 页面体检（uv、git、Node、MemPalace、各 Agent CLI），缺什么可以让 Michael 装什么。本地模型用户有专门的 open models 和 Mac Mini 部署指南。

**适合你，如果**：你已有多个 Agent CLI 订阅、想榨干它们的小时额度；你想研究"纯文件 + 单提交者 git"这种极简多智能体协调层怎么设计；你想给团队搭一个可视化的 Agent 车间。

**不适合你，如果**：你只有一个 Agent 订阅（协调层的价值无从发挥）；你要的是云端多租户 Agent 平台（它是单机桌面应用）；你期望生产级稳定——它自己标着 prototype，star 数 4.8k 说明关注度高，但成熟度要按原型看待。

一个值得留意的信号：仓库 2026 年 5 月底创建，8 月下旬仍在高频提交，README / HIVE.md / SPEC.md / DESIGN.md 四份文档分工清晰——这是一个把"设计先行"当真的项目，`HIVE.md` 本身就值得做多智能体系统的人精读。

## 6. 结论

Munder Difflin 的品味在于克制：不造运行时、不造记忆框架、不造协议，只造一间办公室。五个经典 MAS 模式被压缩成"markdown 记忆 + 原子文件邮箱 + 单提交者 git"这套任何后端工程师半小时就能读懂的机制。如果你正在为"多个 Agent CLI 各自为战"烦恼，或者想在本地复现 Generative Agents 式的结构但干的是真活——把它当试验台装一个，重点读 `HIVE.md`。

> 仓库：<https://github.com/chaitanyagiri/munder-difflin>（4.8k stars，JavaScript/Electron，v0.4.5，2026-08-26 仍在提交）
