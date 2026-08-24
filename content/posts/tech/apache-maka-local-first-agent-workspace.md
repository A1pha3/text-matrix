---
title: "Apache Maka：本地优先的 Agent 工作台，把每一次工具调用都记成可恢复的事实"
date: 2026-08-25T03:55:00+08:00
slug: "apache-maka-local-first-agent-workspace"
github_repo: "apache/maka"
source_key: "gh:apache/maka"
description: "Apache 孵化器项目 Maka 是一个本地优先的 AI Agent 工作台：模型消息、工具调用、权限决策与终止事件全部落为只追加日志，桌面端、CLI 与评测共用同一个 Runtime Host。本文拆解其架构与上手路径。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Apache", "开源", "架构"]
---

用 AI Agent 干活的人迟早会遇到同一组问题：会话记录只在 UI 里、上下文一截断历史就等于丢了、桌面端和命令行走的是两套运行时、评测环境和日常环境对不上。Apache 孵化器项目 [Maka](https://github.com/apache/maka) 把这些问题归结为一句话——"记录本身就是事实源"，然后给出了一个本地优先（local-first）的工程答案：模型消息、工具调用、工具结果、权限决策、终止事件，全部写成一份只追加（append-only）日志，UI 和下一次模型调用都只是这份日志的视图。

## 项目概览

| 项目 | 数据（2026-08-24 取自 GitHub） |
|------|------|
| 仓库 | apache/maka（Apache 孵化器项目，Incubating） |
| Stars / Forks | 2,822 / 304 |
| 语言 / 协议 | TypeScript / Apache 2.0 |
| 最新版本 | v0.1.11（2026-08-18），另有 CLI v0.1.0-beta.1 |
| 维护状态 | 最近提交 2026-08-24，高频迭代中 |
| 平台 | macOS Apple Silicon 为主；Windows 无签名预览；Linux 暂不支持 |

两个前置认知要先立住：

第一，**它还在孵化期**。README 明确说明：目前从仓库或包管理器发布的一切产物都不是 ASF 正式 release，未经孵化器 PMC 审查投票；数据格式、CLI 命令和实验能力都可能变。

第二，**本地优先是硬约束**。会话、设置、运行记录默认留在本机；模型自带——云 API、本地模型或兼容网关都行，Maka 不绑共享模型账号。API 密钥存在本地明文文件 `credential-vault.json`（仅 OS 账户可读），渲染进程永远看不到。

## 核心设计：四个"为什么"

Maka 的设计动机可以从 README 的 "Why Maka" 一节读出，值得逐条看：

1. **你的机器，你的数据。** 会话与运行记录本地存储，模型连接由用户自带。
2. **记录被保留。** 模型消息、工具调用、工具结果、一轮如何结束，全部落盘。UI 和下一次模型调用是记录的视图，不是唯一副本。
3. **上下文缩短 ≠ 删历史。** Maka 可以在构造下一条 prompt 时省略旧的工具输出，但不丢弃已保存的证据——上下文窗口的取舍与证据留存是两件事。
4. **一个地方跑 Agent。** 桌面端、终端、评测全部经由同一个 Runtime Host。评测只拥有实验与分数，不另起一套执行环境。

第 3 条是全文最有品味的设计判断：大多数 Agent 产品把"上下文压缩"实现成"删记录"，Maka 把两者解耦了。

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

关键点在最后一段：评测里的 Maka 被测体也只通过 Runtime Host 执行，外部被测体走通用适配器。评测与日常使用跑在同一个执行路径上，"评测分数"和"实际体验"才可比。

内置工具是克制的六个：`Read`、`Write`、`Edit`、`Bash`、`Glob`、`Grep`；Computer Use 和目录 skills 是可选项，默认不开。越出沙箱边界的工具调用必须经过批准，运行可中止，失败会分类。执行记录持久化，支持崩溃恢复与中断 Turn 的可选续跑。

评测子系统有自己的建模：声明式多臂实验展开为"任务 × 重复 × 被测体"单元格（cell），每个 cell 的尝试（attempt）不可变，支持定向基础设施替换与最早有效选择；结果内核记录分数、归一化用量、可归因成本、时长、状态与失败原因。

## 上手路径

先说结论：**目前不建议下载预构建包**——README 原文是"在获得批准的 source release 之前，不推荐任何预构建下载"，请从源码构建运行。

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
apps/desktop/       Electron 主进程 / preload / React 渲染
packages/core/      Session、Event、Permission、Connection 的纯契约
packages/storage/   SQLite 状态、配置与负载存储
packages/runtime/   AgentRun、模型适配、工具、上下文与恢复
packages/eval/      实验 cell、attempt、结果与执行器/被测体适配
packages/cli/       TUI 与非交互 CLI
packages/ui/        共享会话、Markdown、Artifact 与 UI 原语
```

契约（core）与实现（runtime/storage）分离，桌面与 CLI 共享同一套包——这是"三个入口一条脊柱"在代码层的体现。

## 适用边界

- **适合**：重视会话证据与可审计性的重度 Agent 用户；需要评测与日常环境同路径的团队；数据不出本机的合规场景。
- **不适合**：Windows/Linux 为主的用户（前者是无签名预览、后者未支持）；期望开箱即用稳定 API 的集成方——版本号 0.1.x，格式还会变。
- **留意**：密钥是本地明文存储（有 OS 账户级隔离，但与系统钥匙串方案不同，敏感环境自行权衡）；IM bot 等能力仍是实验性。

## 延伸阅读

- 架构总览：仓库内 `ARCHITECTURE.md`（含系统地图、代码边界与六篇双语深潜）
- 中文文档：仓库内 `README.zh-CN.md`
- CLI 指南：`packages/cli/README.md`

一句话总结：Maka 不是又一个 Agent 聊天客户端，而是把"Agent 执行记录"当作一等公民来设计的本地工作台——如果你在乎的是每次工具调用都可追溯、可恢复、可评测，它值得在孵化期就放进观察列表。
