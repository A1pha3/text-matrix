---
title: "OpenSandbox：阿里巴巴开源的通用 AI 应用沙箱平台"
date: "2026-03-28T21:00:00+08:00"
slug: "alibaba-opensandbox-ai-sandbox-platform"
github_repo: "opensandbox-group/OpenSandbox"
source_key: "gh:opensandbox-group/OpenSandbox"
description: "深度解读 OpenSandbox（阿里巴巴开源，现由 opensandbox-group 维护）：通用 AI 应用沙箱平台，多语言 SDK、Docker/Kubernetes 运行时，1.1.0 新增 Firecracker 微虚拟机池 Fast Sandbox，覆盖编程 Agent、GUI Agent、代码执行、强化学习训练等场景。"
draft: false
categories: ["技术笔记"]
tags: ["沙箱", "Docker", "Kubernetes", "Firecracker"]
---

> **目标读者**：构建 AI 应用（编程 Agent、GUI Agent、代码执行、RL 训练）的开发者
> **核心问题**：如何为 AI 应用提供安全、可扩展的隔离执行环境？
> **难度**：⭐⭐⭐⭐（专家设计）
> **来源**：GitHub opensandbox-group/OpenSandbox（原 alibaba/OpenSandbox），访问于 2026-09-26

---

## 快速信息卡

| 指标 | 数值 |
|------|------|
| GitHub Stars | 15,513 |
| Forks | 1,428 |
| License | Apache-2.0 |
| 主要语言 | Python（约 38%）、Go（约 35%） |
| 最新版本 | release-1.1.0（2026-09-21，首个统一大版本） |
| 官方文档 | https://open-sandbox.ai/ |
| CNCF Landscape | 已收录（调度与编排类目） |

> 数据截至 2026-09-26，来自 GitHub API，以仓库实际状态为准。项目仓库已从 `alibaba/OpenSandbox` 迁移至 `opensandbox-group/OpenSandbox`，旧链接会自动跳转。

## 一句话判断

OpenSandbox 把"为 AI 应用提供隔离执行环境"做成了平台级产品：上层用多语言 SDK、CLI 和 MCP 屏蔽接入差异，下层用 Docker/Kubernetes 调度资源；1.1.0 又接入 Firecracker 微虚拟机池（Fast Sandbox），把沙箱创建变成对既有容量的恒定时间准入，官方给出的启动数字是约 80 毫秒。它解决的核心矛盾是：AI Agent 要执行任意代码、操作浏览器和桌面，又不能污染宿主环境或把数据带出边界。

## 学习目标

读完本文后你应当能够：

1. 说清 OpenSandbox 分层架构中每层的职责与可替换点
2. 说出内置沙箱环境（Code Interpreter、Chrome、Playwright、Desktop、VS Code）各自面向的任务
3. 描述一次代码执行如何穿过各层到达沙箱内的 `execd`，以及执行流量为何不走控制面
4. 在 Docker、Kubernetes 容器工作负载与 FastSandbox 微虚拟机池之间做出与场景匹配的选型决策
5. 判断自己的场景适不适合引入 OpenSandbox

## 目录

- [一、项目概览](#一项目概览)
- [二、技术架构](#二技术架构)
- [三、核心机制详解](#三核心机制详解)
- [四、任务流案例：一次代码执行如何穿过各层](#四任务流案例一次代码执行如何穿过各层)
- [五、快速开始](#五快速开始)
- [六、集成示例](#六集成示例)
- [七、与同类项目对比](#七与同类项目对比)
- [八、适用场景](#八适用场景)
- [九、Roadmap](#九roadmap)
- [十、采用建议](#十采用建议)
- [十一、常见问题排查](#十一常见问题排查)
- [十二、练习](#十二练习)
- [十三、自测题](#十三自测题)
- [十四、进阶路径](#十四进阶路径)
- [十五、总结](#十五总结)

## 总览地图

OpenSandbox 分五层，每层职责独立，可以单独替换：

| 层 | 职责 | 关键组件 | 可替换点 |
|---|---|---|---|
| 客户端层 | 给开发者用的入口 | Python / Java / Kotlin / JS / TS / C# / Go SDK + `osb` CLI + MCP 服务器 | 可扩展新语言 |
| 协议层 | 定义沙箱能做什么 | 生命周期、执行、诊断、出口策略的 OpenAPI 契约 | 规范在 `specs/` |
| 运行时层 | 管理沙箱生命周期 | `server`（FastAPI）+ Docker/Kubernetes 提供者 + FastSandbox 集成 | 可自托管 |
| 沙箱环境层 | 预置的执行镜像 | Code Interpreter / Chrome / Playwright / Desktop / VS Code | 镜像可自定义 |
| 隔离层 | 提供隔离边界 | gVisor / Kata / Firecracker 微虚拟机 | 按安全强度选择 |

阅读建议：先看"技术架构"理解各层边界，再看"任务流案例"理解一次代码执行的实际路径，最后按"采用建议"判断是否适合自己的场景。

---

## 一、项目概览

[OpenSandbox](https://github.com/opensandbox-group/OpenSandbox) 是阿里巴巴开源的通用 AI 应用沙箱平台，现由 `opensandbox-group` 组织维护（Java/Kotlin SDK 的 Maven groupId 仍是 `com.alibaba.opensandbox`，npm 包仍是 `@alibaba-group/opensandbox`，阿里背景有据可查）。它提供多语言 SDK、统一沙箱协议、Docker/Kubernetes 运行时，覆盖编程 Agent、GUI Agent、Agent 评估、AI 代码执行、强化学习训练等场景。

**核心数据（截至 2026-09-26，数据来自 GitHub API）：**

| 指标 | 数值 |
|------|------|
| GitHub Stars | 15,513 |
| Forks | 1,428 |
| License | Apache-2.0 |
| 最新版本 | release-1.1.0（2026-09-21） |
| 官方文档 | https://open-sandbox.ai/ |

> 时效说明：Stars 和 Forks 为访问时快照，可能已变化；版本号以仓库 release 页为准。

项目已进入 [CNCF Landscape](https://landscape.cncf.io/?item=orchestration-management--scheduling-orchestration--opensandbox) 的调度与编排类目，并通过 OpenSSF Best Practices 认证。

### 1.1 项目定位

> OpenSandbox is a general-purpose sandbox platform for AI applications.
> 通用 AI 应用沙箱平台

**支持场景：**

| 场景 | 说明 |
|------|------|
| **编程 Agent** | Claude Code、OpenAI Codex CLI 等 CLI Agent 在沙箱内运行 |
| **GUI Agent** | 浏览器自动化、桌面环境操作 |
| **Agent 评估** | 在受控沙箱中评估 Agent 能力（官方提供 Harbor 评估示例，一个试验一个沙箱） |
| **AI 代码执行** | 实现 Code Interpreter 功能 |
| **强化学习训练** | RL 训练任务在沙箱中运行 |

### 1.2 主要特色

| 特色 | 说明 |
|------|------|
| **多语言 SDK + CLI + MCP** | Python / Java / Kotlin / TypeScript / C#/.NET / Go 均已发布，另有 `osb` CLI 和 MCP 服务器 |
| **开放协议** | 生命周期与执行 API 以公开 OpenAPI 契约定义，自定义运行时可插接而无需改客户端 |
| **Docker/Kubernetes** | 本地运行 + 大规模分布式调度，同一套 SDK 调用 |
| **Fast Sandbox** | 1.1.0 新增：Firecracker 微虚拟机预热池，恒定时间准入，官方称约 80ms 启动；支持暂停/恢复 |
| **强隔离** | gVisor / Kata Containers / Firecracker 微虚拟机 |
| **网络安全策略** | Ingress 网关 + 沙箱级出口控制 + Credential Vault 凭证注入 |

---

## 二、技术架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│ OpenSandbox 架构                                            │
├─────────────────────────────────────────────────────────────┤
│ 客户端层（多语言）                                          │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│ │ Python   │ │ Java/    │ │ JS/TS    │ │ C#/.NET  │  …Go   │
│ │          │ │ Kotlin   │ │          │ │          │        │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
│         osb CLI  /  MCP 服务器                              │
├─────────────────────────────────────────────────────────────┤
│ 协议层（specs/）                                            │
│ 生命周期 API + 执行 API + 诊断 API + 出口策略 API           │
├─────────────────────────────────────────────────────────────┤
│ 运行时层（控制面 + 运行时后端）                              │
│ ┌─────────┐ ┌──────────────────────────────────────┐       │
│ │ server  │ │ 运行时后端：Docker / Kubernetes       │       │
│ │ FastAPI │ │ （BatchSandbox 或 agent-sandbox）     │       │
│ │         │ │ + FastSandbox 集成（微虚拟机池）      │       │
│ └─────────┘ └──────────────────────────────────────┘       │
├─────────────────────────────────────────────────────────────┤
│ 沙箱环境层（数据面）                                        │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│ │ Code     │ │ Chrome   │ │Playwright│ │ Desktop/ │        │
│ │Interpreter│ │ Browser │ │ 自动化    │ │ VS Code  │        │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
│          沙箱内守护进程：execd（命令/文件/代码）             │
├─────────────────────────────────────────────────────────────┤
│ 隔离层（Secure Container）                                  │
│ ┌──────────┐ ┌──────────┐ ┌──────────────┐                 │
│ │ gVisor   │ │ Kata     │ │ Firecracker  │                 │
│ │          │ │ Containers│ │ 微虚拟机     │                 │
│ └──────────┘ └──────────┘ └──────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 各层职责拆解

理解 OpenSandbox 的关键在于看清层与层之间的边界：客户端层只把请求发给协议定义的接口，不直接接触容器；协议层用 OpenAPI 规范定义接口，让多语言 SDK 保持一致行为；`server` 是控制面，负责认证、校验、持久化服务器侧记录，并把生命周期工作委托给运行时后端；沙箱环境层是数据面，提供预置镜像和沙箱内的 `execd` 守护进程；隔离层决定安全强度。

分层带来的实际收益：替换隔离运行时不需要改 SDK 代码；新增一种沙箱环境不需要动协议层；从 Docker 切到 Kubernetes 只影响运行时后端。官方架构文档把同一系统概括为六个面——客户端面、协议面、生命周期控制面、运行时后端、沙箱数据面、网络安全面——与本节的五层划分是对同一系统的不同粒度描述。

### 2.3 技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| SDK 语言 | Python/Java/Kotlin/JS/TS/C#/Go | 均已发布 |
| 服务端 | Python FastAPI | 沙箱生命周期控制面 |
| 沙箱内守护进程 | Go | `execd` 命令/文件/代码执行 |
| 容器 | Docker/Kubernetes | 运行时后端 |
| 微虚拟机 | Firecracker | FastSandbox 池 |
| 安全容器 | gVisor/Kata/Firecracker | 强隔离 |

仓库语言构成为 Python 约 38%、Go 约 35%（GitHub 语言统计，2026-09-26），前者主要来自 server 与 SDK，后者主要来自 `execd` 等沙箱内组件。

### 2.4 核心目录结构

```
OpenSandbox/
├── sdks/                # 多语言 SDK
│   ├── sandbox/         # Sandbox 基础 SDK
│   │   ├── python/      # Python SDK
│   │   ├── kotlin/      # Java/Kotlin SDK
│   │   ├── javascript/  # JS/TS SDK
│   │   ├── csharp/      # C#/.NET SDK
│   │   └── go/          # Go SDK
│   ├── code-interpreter/  # Code Interpreter SDK（python/javascript/csharp）
│   └── mcp/             # MCP 服务器
├── cli/                 # osb 命令行工具
├── specs/               # OpenAPI 规范（生命周期/执行/诊断/出口策略）
├── server/              # Python FastAPI 生命周期控制面
├── components/
│   ├── execd/           # 沙箱执行守护进程（命令/文件/代码）
│   ├── ingress/         # 入口流量网关
│   ├── egress/          # 出口网络控制
│   └── nodeagent/       # 节点侧代理
├── kubernetes/          # Kubernetes 部署
├── manifests/           # Helm charts 等部署清单
├── examples/            # 示例代码（claude-code、chrome、playwright、desktop、
│                        #   langgraph、rl-training、harbor-evaluation 等）
├── oseps/               # OpenSandbox 增强提案
├── docs/                # 架构文档（control-plane/data-plane/fast-sandbox/network）
└── tests/               # E2E 测试
```

注意：官方 Code Interpreter 镜像已迁移到独立仓库 [opensandbox-group/sandbox-images](https://github.com/opensandbox-group/sandbox-images)（原 `sandboxes/code-interpreter/` 目录已从主仓库移除），带可复现构建、自动化测试和独立发布。

---

## 三、核心机制详解

### 3.1 多语言 SDK、CLI 与 MCP

OpenSandbox 提供五种语言的 Sandbox SDK（Python、Java/Kotlin、JavaScript/TypeScript、C#/.NET、Go），外加 Code Interpreter SDK（Python、JavaScript、C#）。各语言 SDK 由公开 OpenAPI 契约约束，行为保持一致；生成代码负责常规请求响应，手写层负责流式输出、传输生命周期、错误映射这些语言特性相关的部分。

除 SDK 外，官方还提供两个入口：

- `osb` 命令行工具（`pip install opensandbox-cli`）：面向终端操作，覆盖沙箱生命周期、命令执行、文件操作、诊断查看与出口策略管理
- MCP 服务器（`pip install opensandbox-mcp`）：把沙箱创建、命令执行、文本文件操作暴露给 Claude Code、Cursor 等 MCP 客户端

为什么需要多语言 SDK？只提供 REST API 不够吗？因为不同语言的类型系统、异步模型、错误处理差异很大，直接调 REST 会让每个语言的用户都重复处理序列化和重试逻辑。SDK 把这些封装掉，各语言用户拿到的是符合本语言习惯的接口。

### 3.2 沙箱协议

协议面定义了四类公开 OpenAPI 契约（都在 `specs/` 下）：

**生命周期管理 API：**创建、列举、暂停、恢复、续期、删除沙箱，以及快照和模板管理。

**执行 API：**命令执行（支持流式输出与后台任务）、文件操作、PTY、代码解释器调用。

**诊断 API：**1.1.0 起稳定，按范围查询日志与事件（`logs:container|all`、`events:runtime|lifecycle|all`）。

**出口策略 API：**查看与修改沙箱的出口网络策略。

生命周期与执行分开定义，让控制面与数据面各自演进：生命周期操作频率低但必须可靠，执行操作频率高、允许失败重试，还能单独加流式输出。客户端应当依赖公开契约而不是具体实现，这也是自定义运行时能插接进来的前提。

### 3.3 沙箱运行时：三种部署形态

| 形态 | 适用场景 | 说明 |
|------|---------|------|
| **Docker** | 本地开发测试 | 单机快速启动 |
| **Kubernetes 容器工作负载** | 生产环境 | 大规模分布式调度，支持预热与池化 |
| **FastSandbox 微虚拟机池** | 高吞吐、短任务 | Firecracker 池，恒定时间准入，官方称约 80ms 启动 |

**Kubernetes 容器工作负载**通过工作负载提供者创建资源：默认由 OpenSandbox 自带的 BatchSandbox 控制器负责高吞吐与池化交付，也可切换为 `kubernetes-sigs/agent-sandbox` 提供者（1.1.0 起要求 agent-sandbox v1.0.0 的 `agents.x-k8s.io/v1beta1` API，属于破坏性变更）。

**FastSandbox** 是 1.1.0 的重头戏，值得单独展开（见 3.7 节）。

为什么池化和预热这么重要？因为创建一个沙箱要拉镜像、起容器、初始化运行时，冷启动可能要几秒到几十秒。AI Agent 的代码执行通常是高频短任务，每次都冷启动，用户体验会非常差。预热池把这部分延迟摊到空闲期，请求到来时做的是分配而不是创建。

### 3.4 沙箱环境

OpenSandbox 内置多种沙箱环境，每种环境是一个预置镜像：

| 环境 | 说明 | 典型用途 |
|------|------|---------|
| **Code Interpreter** | 代码执行沙箱 | Python、Java、Node.js、Go 运行时 + Jupyter 内核（Python/Java/TS/JS/Go/Bash） |
| **Chrome** | Chromium 沙箱 | VNC + DevTools，自动化与调试 |
| **Playwright** | Web 自动化 | 无头浏览器抓取与测试 |
| **Desktop** | 完整桌面环境 | VNC 远程桌面 |
| **VS Code** | 云端 IDE | code-server Web IDE |

预置这些环境的原因很直接：AI Agent 的需求高度集中在执行代码、操作浏览器和桌面三类任务上。镜像预装了运行时和依赖，启动即可用。运行时版本通过环境变量选择（`PYTHON_VERSION`、`JAVA_VERSION`、`NODE_VERSION`、`GO_VERSION`），需要别的工具链时可以基于官方镜像派生自定义镜像。

### 3.5 网络安全策略与凭证管理

**Ingress 网关（入口流量）：**统一入口管理，支持多种路由策略；端点解析有三种形态——直连地址、ingress 网关路由、server 代理。

**Egress 控制（出口流量）：**沙箱级出口控制，容器工作负载用 per-sandbox sidecar，FastSandbox 用共享的 Fastlet 出口配置，支持 DNS/nftables 策略。

**Credential Vault（凭证保险库）：**1.1.0 前后成型的特性——凭证在出口侧注入，真实密钥不进入沙箱工作负载，Agent 拿到的是受控的访问能力而不是密钥本身。

为什么出口控制和凭证管理重要？因为 Agent 执行的代码可能来自用户输入，也可能来自模型生成。如果沙箱能自由访问公网，恶意代码可以把宿主数据外传，或者攻击外部服务。出口白名单把攻击面收窄；Credential Vault 则解决另一个常见痛点——Agent 调外部 API 需要凭证，但把密钥放进沙箱等于把家底交给不可信代码。

### 3.6 强隔离机制

支持三种安全容器运行时，对应不同隔离强度：

| 运行时 | 隔离方式 | 适用场景 |
|--------|---------|---------|
| **gVisor** | 用户态内核拦截系统调用 | 中等安全要求，性能损失较小 |
| **Kata Containers** | 硬件虚拟化 | 高安全要求，VM 级隔离 |
| **Firecracker** | 轻量微虚拟机 | 高密度多租户，启动快 |

三种运行时是隔离与性能的不同取舍：gVisor 性能损失最小但隔离相对弱，Kata 隔离最强但开销更高，Firecracker 介于两者之间、专为高密度设计。选择取决于威胁模型——内部可信环境用 gVisor，公网多租户用 Firecracker，强合规场景用 Kata。配套的安全容器部署指南见 `docs/guides/secure-container.md`。

一个需要注意的细节：快照功能不支持 gVisor 运行时，创建 gVisor 沙箱的快照会被服务端以 `409 SNAPSHOT::UNSUPPORTED_RUNTIME` 拒绝。要依赖暂停/恢复的工作流应选 Firecracker 或容器运行时。

### 3.7 Fast Sandbox：微虚拟机池与恒定时间准入

FastSandbox 是理解 1.1.0 的关键。它的调度模型由三个概念组成：

- **SandboxPool**：容量与策略的单元。一个池固定运行时档案（容器档案或 Firecracker 档案）和资源形状，声明暖池容量（`capacity`）、Fastlet 模板、单 pod 沙箱密度上限（`maxSandboxesPerPod`）和预拉取镜像清单（`warmImages`）。
- **Fastlet**：预热好的 Kubernetes pod，一个 Fastlet 承载多个沙箱，每个沙箱占其中一个切片。
- **FastPath**：准入调度器。创建请求到来时，它在内存中对候选 Fastlet 排序（镜像缓存亲和优先，其次归一化负载，最后稳定哈希决胜），把沙箱原子地安置到选中的 Fastlet 上。

官方对这套机制的概括是：创建沙箱不再是新一轮调度，而是对既有容量的恒定时间准入。README 给出的数字是约 80ms 启动（来自官方文档，未附测试条件，实际数字因部署而异）。

两个设计细节保证了"快而不危险"：

1. **网络槽位先于运行时存在**。netns、veth、伪装规则在每个沙箱准入前就预置好，策略绑定随准入一起下发——沙箱在策略生效前不可达。
2. **Sandbox CR 先写完整再启动**。意图、初始策略、池引用先持久化，准入被任何故障打断都能靠调谐恢复，不会泄漏半个沙箱。

**暂停与恢复**：`Paused` 状态把运行时检查点写入 artifact store 并释放 Fastlet 容量；恢复时检查点可以在另一台 Fastlet 上还原，这也是路由在恢复后必须重新解析的原因。配合快照机制（1.1.0 新增可选的 PostgreSQL 存储与 SQLite 迁移命令），有状态沙箱工作流有了完整的落点。

---

## 四、任务流案例：一次代码执行如何穿过各层

跟踪一次"用户调用 Python SDK 执行 `2+2`"的完整流程。先说一个容易搞错的点：**创建沙箱走控制面，执行代码不走控制面**。官方架构文档明确，命令、文件、PTY 和代码执行请求绕过生命周期编排，客户端直连解析出的端点——单机是直连地址，Kubernetes 下可能是 pod 地址、server 代理或 ingress 网关路由。这样 server 就不会成为执行吞吐的瓶颈。

1. **创建（控制面）**：Python SDK 发出 `Sandbox.create(...)`，FastAPI server 认证、校验请求并持久化记录，交给运行时后端（Docker、Kubernetes 提供者或 FastSandbox）拉起容器或微虚拟机；命中预热池时直接分配
2. **端点解析（控制面返回）**：SDK 从生命周期 API 拿到沙箱的可达端点
3. **执行（数据面，直连）**：`interpreter.codes.run("2+2")` 按 `specs/` 中的执行契约序列化后直发沙箱内的 `execd`；`execd` 在 Code Interpreter 环境里起执行上下文，跑代码、捕获 stdout 和返回值
4. **隔离边界（始终生效）**：整个沙箱跑在 gVisor/Kata/Firecracker 之一的边界内，系统调用被拦截或虚拟化；挂了出口 sidecar 时，对外请求还要过出口策略

返回路径相反：`execd` 把结果按契约封装，SDK 反序列化为 `result` 对象，`result.result[0].text` 即 `4`。

这个流程的关键点是各层可独立替换：把 gVisor 换成 Firecracker，SDK 代码不变；把 Code Interpreter 镜像换成自定义工具链镜像，`server` 和 `execd` 也不用改。

---

## 五、快速开始

### 5.1 环境要求

| 工具 | 要求 |
|------|------|
| Docker | 必需（本地执行） |
| Python | 3.10+（运行示例和本地运行时） |

### 5.2 安装步骤

**1. 初始化配置：**

```bash
uvx opensandbox-server init-config ~/.sandbox.toml --example docker
```

**2. 启动 Sandbox Server：**

```bash
uvx opensandbox-server
# 显示帮助
uvx opensandbox-server -h
```

**3. 安装 Code Interpreter SDK：**

```bash
uv pip install opensandbox-code-interpreter
```

### 5.3 基本使用示例

```python
import asyncio
from datetime import timedelta

from code_interpreter import CodeInterpreter, SupportedLanguage
from opensandbox import Sandbox
from opensandbox.models import WriteEntry

async def main() -> None:
    # 1. 创建沙箱（官方 code-interpreter 镜像）
    sandbox = await Sandbox.create(
        "opensandbox/code-interpreter:v1.1.0",
        entrypoint=["/opt/code-interpreter/code-interpreter.sh"],
        env={"PYTHON_VERSION": "3.11"},
        timeout=timedelta(minutes=10),
    )

    async with sandbox:
        # 2. 执行 Shell 命令
        execution = await sandbox.commands.run("echo 'Hello OpenSandbox!'")
        print(execution.logs.stdout[0].text)
        # Hello OpenSandbox!

        # 3. 写文件
        await sandbox.files.write_files([
            WriteEntry(path="/tmp/hello.txt", data="Hello World", mode=644)
        ])

        # 4. 读文件
        content = await sandbox.files.read_file("/tmp/hello.txt")
        print(f"Content: {content}")
        # Content: Hello World

        # 5. 创建代码解释器
        interpreter = await CodeInterpreter.create(sandbox)

        # 6. 执行 Python 代码
        result = await interpreter.codes.run(
            """
            import sys
            print(sys.version)
            result = 2 + 2
            result
            """,
            language=SupportedLanguage.PYTHON,
        )
        print(result.result[0].text)   # 4
        print(result.logs.stdout[0].text)  # 3.11.x

        # 7. 清理沙箱
        await sandbox.kill()

if __name__ == "__main__":
    asyncio.run(main())
```

关于清理 API 的选择：`kill()` 停掉沙箱实例但保留服务器侧记录（之后还能 `connect()` 回去）；`destroy()` 适合"创建—使用—丢弃"的一次性流程，它先执行 `kill()` 再删除记录。用完即弃的场景选 `destroy()`，可能重连的场景选 `kill()`。

### 5.4 用 osb CLI 快速体验

不想写代码时，可以用官方命令行工具 `osb`：

```bash
uv tool install opensandbox-cli
osb config init
osb config set connection.domain localhost:8080
osb config set connection.protocol http
osb sandbox create --image python:3.12 --timeout 30m -o json
osb command run <sandbox-id> -o raw -- python -c "print(1 + 1)"
```

### 5.5 生产部署的两个硬要求

把这套东西放上生产前，先确认两件事：

- **API key**：配置了 API key 后，除健康检查和文档外的所有端点都要求 `OPEN-SANDBOX-API-KEY` 请求头；未配置 key 时，server 在非交互环境下会拒绝启动（除非显式确认不安全）。生产部署应当始终设置 key。
- **镜像完整性**：官方镜像发布到 Docker Hub、GHCR 和阿里云三个仓库，用 Cosign 无密钥签名并附带来源证明；生产环境按 digest 固定镜像，并按官方发布验证指南校验签名。

---

## 六、集成示例

### 6.1 编程 Agent 集成

OpenSandbox 为主流编程 Agent CLI 提供了官方示例，每个 CLI 都能跑在沙箱里：

| Agent | 说明 |
|-------|------|
| Claude Code | Anthropic CLI |
| Gemini CLI | Google CLI |
| OpenAI Codex CLI | OpenAI CLI |
| OpenCode | 开源 coding CLI |
| Qwen Code | 阿里通义 CLI |
| Kimi CLI | 月之暗面 CLI |

命令行之外，MCP 服务器（`pip install opensandbox-mcp`）把沙箱能力暴露给 Claude Code、Cursor 等 MCP 客户端：

```bash
pip install opensandbox-mcp
opensandbox-mcp --domain localhost:8080 --protocol http
```

### 6.2 其他值得看的示例

`examples/` 目录覆盖面比多数同类项目广，除 Agent 集成外还有：

- **LangGraph / Google ADK / DeerFlow**：Agent 框架集成，沙箱作为工具执行层
- **Harbor 评估**：在 OpenSandbox 上跑 Harbor Agent 评估，一个试验一个沙箱
- **持久卷**：Docker 命名卷、OSSFS、Kubernetes PVC 三种持久化模式
- **aio-sandbox**：All-in-One 沙箱配置
- **aks-kata**：AKS 上的 Kata 隔离部署
- **vscode / desktop / chrome / playwright**：远程开发与浏览器、桌面自动化

---

## 七、与同类项目对比

| 特性 | OpenSandbox | E2B | Docker API | Kata Containers |
|------|-------------|-----|------------|-----------------|
| **多语言 SDK** | ✅ Python/Java/Kotlin/TS/C#/Go | Python/JS | 无 | 无 |
| **CLI + MCP** | ✅ | ❌ | 无 | 无 |
| **Kubernetes 原生** | ✅ | 托管服务 | 需自己实现 | 有限 |
| **微虚拟机池** | ✅ FastSandbox（Firecracker） | ❌ | ❌ | 本身即 VM |
| **浏览器/桌面环境** | ✅ Chrome/Playwright/Desktop/VS Code | 有限 | ❌ | ❌ |
| **出口控制 + 凭证注入** | ✅ | 有限 | 需自己实现 | ❌ |
| **CNCF 收录** | ✅ | ❌ | ❌ | ✅ |

对比说明：E2B 是商业化的代码执行沙箱，托管服务开箱即用，但 self-host 能力和运行时形态不如 OpenSandbox 开放；Docker API 只提供容器原语，沙箱协议、预热池、出口策略都要自己封装；Kata Containers 只解决隔离层，不提供 SDK 和生命周期管理。OpenSandbox 的差异点在于把客户端、协议、控制面、运行时、环境、隔离打包成完整平台，并且全部可以自托管。

选型时还有一个维度值得掂量：E2B 换来的是不用运维，OpenSandbox 换来的是运行时自主权。团队有没有 Kubernetes 运维能力，往往比功能清单更能决定选哪个。

---

## 八、适用场景

| 场景 | 说明 |
|------|------|
| **AI 代码执行** | 云端 Code Interpreter |
| **编程 Agent** | Claude Code 等在沙箱中运行 |
| **浏览器自动化** | 网页抓取、UI 测试 |
| **桌面环境** | 远程 VNC 开发 |
| **Agent 评估** | 安全评估 Agent 能力（Harbor 集成） |
| **RL 训练** | 强化学习训练任务 |

---

## 九、Roadmap

> 状态整理自官方 [ROADMAP.md](https://github.com/opensandbox-group/OpenSandbox/blob/main/ROADMAP.md)，文件标注最后更新于 2026-04-28，以仓库实际进度为准。

### 9.1 沙箱运行时

| 功能 | 状态 | 说明 |
|------|------|------|
| 持久化卷 | 实现中 | OSEP-0003，Docker 命名卷与 Kubernetes PVC 已支持，收尾运行时缺口 |
| 本地轻量级沙箱 | 规划中 | 直接跑在 PC 上的 AI 工具沙箱 |
| 安全容器运行时 | 已实现，持续加固 | OSEP-0004，配套安全容器部署指南 |
| 根文件系统快照暂停/恢复 | 实现中 | OSEP-0008，支持有状态沙箱工作流 |
| 安全端点访问 | 已实现，持续加固 | OSEP-0011，保持 server、SDK、文档行为一致 |

### 9.2 SDK 与开发体验

| 功能 | 状态 | 说明 |
|------|------|------|
| SDK 规格对齐 | 持续进行 | Python、Go、Kotlin、JS/TS、C# 与公开规格保持一致 |
| 客户端侧沙箱池 | 已实现，持续完善 | OSEP-0005，预配置沙箱减少冷启动 |
| CLI 易用性 | 规划中 | 改善常用沙箱生命周期工作流 |
| 开发者控制台 | 可实现 | OSEP-0006，为用户和维护者提供更清晰的操作界面 |

### 9.3 可观测性、运维与治理

| 功能 | 状态 | 说明 |
|------|------|------|
| OpenTelemetry 指标与日志 | 实现中 | OSEP-0010，覆盖 execd、ingress、egress |
| Agent 沙箱内审计轨迹 | 规划中 | 记录命令、文件、网络等操作，待 OSEP 定义 |
| Kubernetes 部署 | 持续维护 | 自托管部署与 Helm charts（`manifests/charts/`） |
| 网络隔离指南 | 持续维护 | 安全默认值与实用隔离模式文档化 |

Roadmap 里有一节"Not Currently Planned"值得注意：在生命周期语义和 SDK 兼容性成熟之前不宣布 stable v1 API；没有 OSEP 和迁移路径不做破坏性变更。1.1.0 把版本号从 0.x 直接跳到 1.1.0（跳过 1.0.0，因为旧组件版本线已占用），配合签名 BOM 统一所有组件版本，可以看作朝这个方向迈出的一步。

---

## 十、采用建议

根据场景给出采用顺序：

1. **先试**：本地用 Docker 模式跑通"快速开始"示例或 `examples/claude-code`，验证沙箱能起来、代码能执行
2. **再选运行时形态**：短任务高吞吐选 FastSandbox 微虚拟机池；常规容器工作负载用 Kubernetes 提供者；本地开发用 Docker 模式
3. **再选隔离层**：内部可信环境用 gVisor（注意不支持快照），公网多租户用 Firecracker，强合规场景用 Kata
4. **最后自定义镜像**：预置环境不够用时，基于 [sandbox-images](https://github.com/opensandbox-group/sandbox-images) 的官方镜像派生，保持 entrypoint 协议不变

**适用边界：**
- 适合：需要执行任意代码、操作浏览器或桌面的 AI 应用；多租户代码执行平台；Agent 评估基准
- 不适合：纯 API 调用型 Agent（不需要沙箱）；对启动延迟极敏感且无法预热的实时交互场景；没有运维能力却要自托管的小团队（这种情况下托管服务可能更合适）

### 资源链接

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/opensandbox-group/OpenSandbox |
| 官网 | https://open-sandbox.ai/ |
| 架构文档 | https://github.com/opensandbox-group/OpenSandbox/tree/main/docs/architecture |
| 官方镜像仓库 | https://github.com/opensandbox-group/sandbox-images |
| 社区 | Discord（见 README）与钉钉技术群 |

---

## 十一、常见问题排查

实际跑 OpenSandbox 时容易踩的坑与排查路径：

**1. Sandbox Server 启动失败**

症状：`opensandbox-server` 命令报错、端口被占用，或因未配置 API key 拒绝启动。

排查步骤：
```bash
# 检查端口占用（默认 8080）
lsof -i :8080
# 检查配置文件
cat ~/.sandbox.toml
```

注意 1.x 的启动守卫：非交互环境下 server 未配置 API key 会拒绝启动，按提示显式确认不安全或配置 key。错误分类建议用响应里的错误码而不是错误消息——server 文档明确以错误码为准（例如代理失败返回 `502 BACKEND_CONNECTION_FAILED`）。

**2. 代码执行超时**

症状：SDK 调用 `interpreter.codes.run()` 长时间无响应。

可能原因：
- sandbox 镜像未正确拉取
- 出口隔离导致无法访问外部依赖
- 代码本身有死循环

排查步骤：
```python
# 创建时设置超时
sandbox = await Sandbox.create(..., timeout=timedelta(seconds=30))
# 检查 sandbox 状态
print(sandbox.status)
```

**3. 沙箱创建慢**

症状：Kubernetes 模式下创建 sandbox 需要几十秒。

原因：镜像拉取时间长，预热池未配置。

修复：配置预热与池化（容器工作负载配 BatchSandbox 池；短任务高吞吐场景直接评估 FastSandbox，`warmImages` 可预拉取镜像并保护其不被缓存逐出）。

**4. 出口控制导致依赖安装失败**

症状：在 Code Interpreter 里 `pip install` 失败，报网络错误。

原因：出口策略默认阻止沙箱访问公网。

修复：按官方出口策略配置放行 PyPI 镜像源域名；需要调外部 API 的场景优先考虑 Credential Vault 注入，而不是把密钥写进沙箱环境变量。

**5. 多语言 SDK 版本不匹配**

症状：SDK 调用报类型错误或协议不兼容。

原因：1.1.0 起所有组件统一版本发布，旧版 SDK 与新版 server 混搭可能出现协议偏差。

修复：升级到统一的 1.1.0 版本线（旧版组件 tag 命名空间已冻结），检查 `sdks/` 目录下对应 SDK 的 README。

---

## 十二、练习

### 练习一：本地跑通 OpenSandbox Docker 模式

1. 初始化配置：`uvx opensandbox-server init-config ~/.sandbox.toml --example docker`
2. 启动 server：`uvx opensandbox-server`
3. 安装 Code Interpreter SDK：`uv pip install opensandbox-code-interpreter`
4. 运行本文"快速开始"的基本使用示例，确认沙箱能创建、代码能执行
5. 记录：安装耗时、首次创建沙箱耗时、代码执行延迟

### 练习二：对比容器工作负载与预热池

1. 在 Docker 模式下跑通一个编程 Agent 示例（如 `examples/claude-code`）
2. 记录冷启动时间（从 `Sandbox.create` 到可执行命令）
3. 如果有 Kubernetes 测试环境，部署 `kubernetes/` 目录下的资源，配置池化
4. 对比冷启动时间差异，评估官方"约 80ms"的说法在你的硬件上意味着什么
5. 得出结论：你的场景适合哪种运行时形态？

### 练习三：用 osb CLI 完成一次沙箱生命周期

1. 安装 CLI：`uv tool install opensandbox-cli`
2. 初始化配置，指向本地启动的 server（`localhost:8080`）
3. 用 `osb sandbox create` 创建沙箱，记录创建耗时
4. 用 `osb command run` 执行命令并查看输出
5. 删除沙箱，记录完整生命周期的操作耗时

---

## 十三、自测题

用以下 5 题检验理解程度。答案折叠在每题下方。

**Q1**：OpenSandbox 的执行请求（命令、文件、代码）为什么绕过 `server` 直连沙箱端点？

> **答案**：生命周期操作走控制面（认证、校验、持久化、委托运行时后端），而执行是高频数据面流量。官方架构文档明确执行请求绕过生命周期编排、直连解析出的端点（直连地址、server 代理或 ingress 网关路由三种形态），这样 `server` 不会成为执行吞吐的瓶颈。

**Q2**：内置沙箱环境中，Chrome、Playwright、Desktop 分别面向什么任务？

> **答案**：Chrome 是带 VNC 和 DevTools 的 Chromium 沙箱，用于自动化与调试；Playwright 用于 Web 自动化测试与无头抓取；Desktop 提供带 VNC 的完整桌面环境，适合需要图形界面的操作。

**Q3**：FastSandbox 为什么能做到"恒定时间准入"？它的两个安全设计是什么？

> **答案**：沙箱被调度进预热好的 Fastlet 池，创建请求只做内存中的候选排序与原子安置，不触发新的镜像拉取和容器创建。两个安全设计：网络槽位（netns、veth、策略绑定）在运行时启动前预置好，沙箱在策略生效前不可达；Sandbox CR 先写完整再启动，准入被打断可由调谐恢复，不泄漏半个沙箱。

**Q4**：OpenSandbox 与 E2B 的主要差异是什么？

> **答案**：E2B 是商业托管代码执行沙箱，省运维但 self-host 能力和运行时形态开放度低；OpenSandbox 提供可自托管的完整平台（多语言 SDK、CLI、MCP、Kubernetes 原生、FastSandbox 微虚拟机池、出口控制与凭证注入），已进入 CNCF Landscape。选型关键看团队是否具备 Kubernetes 运维能力。

**Q5**：下面哪个场景不适合用 OpenSandbox？

> A. 需要执行任意代码的 AI 应用
> B. 对启动延迟极敏感且无法预热的实时交互场景
> C. 多租户代码执行平台
> D. Agent 评估基准

> **答案**：B。冷启动以秒计，预热池能把准入压到毫秒级，但前提是有可预热的负载模式；没有预热条件的极低延迟交互场景不合适。纯 API 调用型 Agent 和不需要隔离的内部工具同样没必要引入沙箱平台。

---

## 十四、进阶路径

读完本文后，按以下顺序深入：

1. **跑通最小示例**：按"快速开始"章节安装，用 Docker 模式跑通基本使用示例，确认环境正常。
2. **切换沙箱环境**：同一任务分别用 Code Interpreter、Chrome、Playwright 环境跑一遍，理解不同环境的适用场景。
3. **上 Kubernetes 模式**：在测试集群里部署 `kubernetes/` 目录下的资源，配置池化，记录冷启动时间与资源消耗。
4. **评估 FastSandbox**：读 `docs/architecture/fast-sandbox/` 下的调度、网络、检查点文档，理解 SandboxPool 与 FastPath 的取舍。
5. **自定义镜像**：基于 sandbox-images 的官方镜像派生，增加项目需要的依赖，保持 entrypoint 协议不变。
6. **读源码**：从 `server/` 目录开始，理解 FastAPI 控制面如何管理沙箱生命周期，再看 `components/execd/` 理解沙箱内的命令执行。
7. **读协议与 OSEP**：从 `specs/` 的 OpenAPI 契约入手，再看 `oseps/` 里的增强提案（OSEP-0005 客户端沙箱池、OSEP-0008 快照暂停/恢复、OSEP-0020 生命周期钩子），理解设计演进方向。
8. **贡献社区**：项目接受沙箱环境、文档改进和 bug fix 贡献，重大变更走 OSEP 流程。

---

## 十五、总结

OpenSandbox 把"为 AI Agent 提供隔离执行环境"做成了可交付的平台：多语言 SDK、CLI 和 MCP 屏蔽接入差异，公开协议让运行时可替换，Docker/Kubernetes 覆盖从本地实验到生产调度，gVisor、Kata、Firecracker 提供不同强度的隔离边界，1.1.0 又用 FastSandbox 把高频短任务的创建延迟压到毫秒量级。对要构建安全 AI 应用平台的团队来说，它把"环境隔离"这件基础设施的复杂度打包成了现成组件。

如果你已经有可用的沙箱方案，迁移前值得先确认两件事：你的负载模式能否吃满预热池这类高吞吐能力（吃不满，池的维护成本就是纯开销），以及出口白名单和凭证注入能否覆盖你依赖的下载源与外部 API。

---

## 资料口径说明

本文基于 OpenSandbox 官方仓库（[opensandbox-group/OpenSandbox](https://github.com/opensandbox-group/OpenSandbox)）公开文档整理，需要说明的边界：

1. **数据时效**：Stars、Forks、版本号为 2026-09-26 的 GitHub API 快照；OpenSandbox 处于活跃开发阶段（本文写作当日仍有提交），API 可能变化，请以[官方仓库](https://github.com/opensandbox-group/OpenSandbox)为准。
2. **性能数字**："约 80ms 启动"来自官方 README 对 FastSandbox 预热池的描述，未附测试条件，实际性能因硬件与部署而异；本文未做独立性能验证。
3. **安全容器选择**：gVisor/Kata/Firecracker 的隔离强度和性能开销因版本和配置而异，本文未提供具体性能对比数据，建议自行验证。
4. **仓库迁移**：项目组织已从 `alibaba/OpenSandbox` 迁至 `opensandbox-group/OpenSandbox`，官方 Code Interpreter 镜像迁至 `opensandbox-group/sandbox-images`；本文所有引用以新地址为准。
5. **CNCF Landscape 收录**：具体条目见 [CNCF Landscape 调度与编排类目](https://landscape.cncf.io/?item=orchestration-management--scheduling-orchestration--opensandbox)。
6. **判断边界**：本文对适用场景的判断基于其设计目标和技术特征，具体采用决策请结合业务场景评估。
7. **架构划分**：本文按官方 README 的 Features 归纳为客户端、协议、运行时、沙箱环境、隔离五层；官方架构文档另有"客户端面 / 协议面 / 生命周期控制面 / 运行时后端 / 沙箱数据面 / 网络安全面"的六面划分，两者是对同一系统的不同粒度描述。

---

**相关话题标签**

#OpenSandbox #沙箱 #AI平台 #Docker #Kubernetes #Firecracker #CNCF

**来源**

- GitHub：https://github.com/opensandbox-group/OpenSandbox
- 官方镜像：https://github.com/opensandbox-group/sandbox-images
- CNCF Landscape：https://landscape.cncf.io/
