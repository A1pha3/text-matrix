---
title: "Apache Maka：本地优先的 Agent 工作台，把每一次工具调用都记成可恢复的事实"
date: 2026-08-25T03:55:00+08:00
slug: "apache-maka-local-first-agent-workspace"
github_repo: "apache/maka"
source_key: "gh:apache/maka"
description: "Apache 孵化器项目 Maka 把 Agent 执行记录当作一等公民：模型消息、工具调用、权限决策与终止事件全部落为只追加日志，桌面端、CLI 与评测共用同一个 Runtime Host。本文拆解其架构、一次任务的完整流转与上手路径。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Apache", "开源", "架构"]
---

用 AI Agent 干活的人迟早会遇到同一组问题：会话记录只在 UI 里，上下文一截断历史就等于丢了；桌面端和命令行走的是两套运行时；评测环境和日常环境对不上。Apache 孵化器项目 [Maka](https://github.com/apache/maka) 把这些问题归结为一句话——记录本身就是事实源。它的做法是本地优先（local-first）：模型消息、工具调用、工具结果、权限决策、终止事件，全部写成一份只追加（append-only）日志，UI 和下一次模型调用都只是这份日志的视图。

下文按四条线走：先看项目全貌与两个前置认知，再拆核心设计与执行脊柱，然后用一个具体任务演示记录如何流过系统，最后给上手路径、排查要点与采用建议。

## 项目概览

| 项目 | 数据（2026-08-24 取自 GitHub） |
|------|------|
| 仓库 | apache/maka（Apache 孵化器项目，Incubating） |
| Stars / Forks | 2,822 / 304 |
| 语言 / 协议 | TypeScript / Apache 2.0 |
| 最新版本 | v0.1.11（2026-08-18），另有 CLI v0.1.0-beta.1 |
| 维护状态 | 最近提交 2026-08-24，高频迭代中 |
| 平台 | macOS Apple Silicon 为主；Windows 无签名预览；Linux 暂不支持 |

两个前置认知先讲清楚：

第一，**它还在孵化期**。README 明确说明：目前从仓库或包管理器发布的一切产物都不是 ASF 正式 release，未经孵化器 PMC 审查投票；数据格式、CLI 命令和实验能力都可能变。

第二，**本地优先是硬约束**。会话、设置、运行记录默认留在本机；模型自带——云 API、本地模型或兼容网关都行，Maka 不绑共享模型账号。API 密钥存在本地明文文件 `credential-vault.json`（仅 OS 账户可读），渲染进程永远看不到。

## 核心设计：四个"为什么"

Maka 的设计动机写在 README 的 "Why Maka" 一节，可以逐条读出来：

1. **你的机器，你的数据。** 会话与运行记录本地存储，模型连接由用户自带。
2. **记录被保留。** 模型消息、工具调用、工具结果、一轮如何结束，全部落盘。UI 和下一次模型调用是记录的视图，不是唯一副本。
3. **上下文缩短 ≠ 删历史。** Maka 可以在构造下一条 prompt 时省略旧的工具输出，但不丢弃已保存的证据——上下文窗口的取舍与证据留存是两件事。
4. **一个地方跑 Agent。** 桌面端、终端、评测全部经由同一个 Runtime Host。评测只拥有实验与分数，不另起一套执行环境。

第 3 条把两件常被混为一谈的事分开了：上下文窗口的取舍是 prompt 构造问题，证据留存是存储问题。多数 Agent 产品用"压缩上下文"顺手删掉记录，Maka 只在构造下一条 prompt 时省略旧的工具输出，已落盘的证据原样保留。

## 三个入口，一条脊柱

| 入口 | 适合 | 当前能力 |
|---|---|---|
| Desktop | 日常交互、文件与 Artifact 工作流、模型与权限配置 | Electron + React，流式会话、工具时间线、分支、搜索、恢复 |
| TUI / CLI | 在当前项目目录使用，或跑一次性非交互 Turn | `maka`、`maka run`，与桌面端共享工作区和模型连接 |
| Eval | 可复现的基准实验 | `maka eval run <spec> --out <dir>` |

后端脊柱可以画成一条链（取自仓库 ARCHITECTURE.md 的拓扑）：

```text
Desktop / TUI / CLI → Runtime Host → SessionManager → AgentRun
                                            ↓
                    Model + Tool Runtime → Runtime Event Log
                                            ↓
                         Context / Session / UI projections

Experiment → Cells → Attempts → Results
                    ↓
       Runtime Host executes Maka subjects
```

这条链里藏着两条需要分开看的执行路径。日常路径：桌面端、TUI、CLI 发起的任务经 Runtime Host 进 SessionManager，由 AgentRun 驱动模型与工具，事件写进 Runtime Event Log，Context / Session / UI 只是从日志做的投影。评测路径：实验展开成单元格后，Maka 被测体同样只通过 Runtime Host 执行，外部被测体走通用适配器。两条路径共用同一个执行内核，评测分数与日常体验之间的可比性才有依据。

### 内置工具与沙箱边界

内置工具是克制的六个：`Read`、`Write`、`Edit`、`Bash`、`Glob`、`Grep`；Computer Use 和目录 skills 是可选项，默认不开。越出沙箱边界的工具调用必须经过批准，运行可中止，失败会分类。执行记录持久化，支持崩溃恢复；中断 Turn 的续跑默认关闭，开启方式见后文排查与维护一节。

## 一次任务如何流过 Maka

脊柱链讲了模块怎么连，还要看一次真实任务怎么走。以 README 里的示例命令为例：

```sh
npm run cli:dev -- run "总结这个仓库并指出最大风险"
```

这条命令走完的路径是这样的：

1. CLI 把任务文本交给 Runtime Host，Runtime Host 创建 Session 与 AgentRun。
2. AgentRun 通过模型适配器调用你配置的模型。模型先请求工具：扫描目录用 `Glob`，搜索关键词用 `Grep`，读文件用 `Read`。这些工具都在沙箱边界内，直接执行。
3. 每一步的工具输出写进 Runtime Event Log。构造下一条 prompt 时，Context 投影会按上下文窗口取舍——省略旧的工具输出，但不删除日志里的证据。
4. 当模型发出越出沙箱边界的调用（比如 `Bash` 执行写操作），运行挂起等待批准；批准后继续，拒绝则记一条终止事件。
5. 任务结束后，这一轮从模型消息到终止事件的完整序列已经固化在 `runtime.sqlite` 里。会话在 UI 里显示为工具时间线；中断后打开 Safe resume，可以从日志重建上下文继续跑。

这就是"记录是事实源"的运行时含义：模型的每次思考、每个工具的输入输出、每次权限决策，先落盘再被消费，UI 与后续 prompt 都只是读日志的投影。

## 评测子系统：测的是什么

Maka 的评测不是给聊天客户端做对话打分，而是把"同一组任务在不同被测体上的表现"做成可复现实验。它有自己的建模：声明式多臂实验（multi-arm experiment）展开为"任务 × 重复 × 被测体"的单元格（cell），每个 cell 的尝试（attempt）不可变，支持定向基础设施替换与最早有效选择；结果内核记录分数、归一化用量、可归因成本、时长、状态与失败原因。

读评测结果前要先明确边界。它测的是：给定任务脚本，不同模型或不同配置在完成度和成本上的差异，且由于 Maka 被测体与日常使用跑在同一执行路径，分数反映的是真实运行行为而非专门适配的结果。它不能推出的是：生产环境下的稳定性与安全性——实验只覆盖任务脚本范围内的路径，权限决策、沙箱外的长尾行为都不在测度内。

## 上手路径

先说结论：**目前不建议下载预构建包**——README 原文是"在获得批准的 source release 之前，不推荐任何预构建下载"，请从源码构建运行。README 另外提供每日构建的 Desktop Nightly（从 main 构建、安装后自动更新），供开发者与测试者试用，但它同样不是 ASF release，不建议用于生产。

环境要求：Node.js 22.19+（CI 用 24）、npm（packageManager 为 npm 11）、Git、`ripgrep`（Grep 工具依赖）。桌面端只支持 Apple Silicon Mac。

```sh
git clone https://github.com/apache/maka.git
cd maka
npm ci
npm run dev        # 桌面端开发环境（HMR）
# 或 npm run dev:full  # 先构建全部 workspace 再起 Electron
```

首次启动没有内置模型账号：`Settings → Models` → 添加 API / 本地模型 / 支持的账户连接 → 测试并选默认模型 → 回工作区开任务。连接状态区分"已配置""可发送""实验性"三档，没接进 Runtime 的账户流程不会被伪装成可用模型。

命令行入口（源码方式）：

```sh
npm run build
npm run cli:dev                          # TUI
npm run cli:dev -- run "总结这个仓库并指出最大风险"   # 单次非交互 Turn
npm run cli:dev -- run --graph "实现两个独立切片并集成" # Graph 模式
```

`--graph` 的实现算子使用隔离的 Git worktree，因此要求源项目是干净的 Git 工作树。注意开发 CLI 用 `Maka Dev` profile，与发布版 `maka` 二进制的 `Maka` profile 不互通。

本地数据落在 Electron `userData` 下：

```text
<Electron userData>/workspaces/default/
  runtime.sqlite            # 运行状态与事件
  connection-catalog.json
  credential-vault.json     # 密钥明文本地文件
  settings.json
  artifacts/
```

## 仓库结构速览

```text
apps/desktop/          Electron 主进程 / preload / React 渲染
packages/core/         Session、Event、Permission、Connection 的纯契约
packages/storage/      SQLite 状态、配置与负载存储
packages/mcp/          与模型无关的 Model Context Protocol 客户端集成
packages/runtime/      AgentRun、模型适配、工具、上下文与恢复
packages/runtime-host/ 单一持有者 Runtime Host 的生命周期、协议与客户端引导
packages/eval/         实验 cell、attempt、结果与执行器/被测体适配
packages/computer-use/ Computer Use 后端选择、宿主生命周期与协议适配
packages/cli/          TUI 与非交互 CLI
packages/ui/           共享会话、Markdown、Artifact 与 UI 原语
```

契约（core）与实现（runtime/storage）分离，桌面与 CLI 共享同一套包——这是"三个入口一条脊柱"在代码层的体现。`runtime-host` 把执行内核收敛为单一持有者，`mcp`、`computer-use` 作为独立包接入，避免能力长进主进程里。

## 排查与维护

- **Safe resume 默认关闭**：中断 Turn 的续跑需要显式设置 `MAKA_RUNTIME_SAFE_BOUNDARY_RESUME=1`，之后才启用 Desktop Safe resume、CLI `/resume` 与启动自动续跑。注意这些调用会再次请求模型、消耗 token，不是纯本地操作。
- **升级注意**：旧版 JSONL 转写记录与 Electron `safeStorage` 凭据文件不会被导入。升级后的工作区可能显示空线程，相关凭据需要重新录入。
- **验证命令**：提交改动前跑 `npm run typecheck`、`npm test`、`npm run check:release`；单包可用 `npm --workspace @maka/runtime run test:dist` 等按需执行。
- **Graph 模式约束**：`--graph` 的实现算子使用隔离的 Git worktree，源项目必须是干净的 Git 工作树，否则任务会失败。

## 适用边界

- **适合**：重视会话证据与可审计性的重度 Agent 用户；需要评测与日常环境同路径的团队；数据不出本机的合规场景。
- **不适合**：Windows/Linux 为主的用户（前者是无签名预览、后者未支持）；期望开箱即用稳定 API 的集成方——版本号 0.1.x，格式还会变。
- **留意**：密钥是本地明文存储（有 OS 账户级隔离，但与系统钥匙串方案不同，敏感环境自行权衡）；IM bot 等能力仍是实验性。

## 延伸阅读

- 架构总览：仓库内 `ARCHITECTURE.md`（含系统地图、代码边界与六篇双语深潜）
- 中文文档：仓库内 `README.zh-CN.md`
- CLI 指南：`packages/cli/README.md`

回到开头的四类问题——会话只在 UI 里、上下文一断历史就丢、桌面与命令行两套运行时、评测与日常不一致。Maka 用一份只追加的执行日志同时作答，代价是尚在孵化期：格式会变、密钥是明文落盘、桌面端只认 Apple Silicon。看重可追溯性的用户，可以现在就从源码跑一次 `maka run`，看看单条 Turn 落盘成什么样子、断掉后如何恢复，这比看任何功能清单都更能判断它是否符合自己的工作方式；在 Windows/Linux 上工作、或需要稳定 API 的团队，等正式 source release 再评估也不迟。
