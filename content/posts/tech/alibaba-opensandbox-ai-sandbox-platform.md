---
title: "OpenSandbox：阿里巴巴开源的 10.0k Stars 通用 AI 应用沙箱平台"
date: "2026-03-28T21:00:00+08:00"
slug: "alibaba-opensandbox-ai-sandbox-platform"
description: "深度解读阿里巴巴开源的 OpenSandbox：10.0k Stars 的通用 AI 应用沙箱平台，支持多语言 SDK、Docker/Kubernetes 运行时，涵盖编程 Agent、GUI Agent、AI 代码执行、强化学习训练等场景。"
draft: false
categories: ["技术笔记"]
tags: ["OpenSandbox", "沙箱", "AI平台", "Docker", "Kubernetes"]
---

> **目标读者**：构建 AI 应用（编程 Agent、GUI Agent、代码执行、RL 训练）的开发者
> **核心问题**：如何为 AI 应用提供安全、可扩展的隔离执行环境？
> **难度**：⭐⭐⭐⭐（专家设计）
> **来源**：GitHub alibaba/OpenSandbox，访问于 2026-03-28

---

## 快速信息卡

| 指标 | 数值 |
|------|------|
| GitHub Stars | 11,649+ |
| Forks | 966+ |
| License | Apache-2.0 |
| 主要语言 | Python, Go |
| 最新版本 | python/code-interpreter 0.1.2 |
| 官方文档 | https://open-sandbox.ai/ |
| CNCF Landscape | 已收录 |

> 数据截至 2026-06-25，以仓库实际状态为准。

## 一句话判断

OpenSandbox 把"为 AI 应用提供隔离执行环境"这件事做成了平台级产品：上层用多语言 SDK 屏蔽差异，下层用 Docker/Kubernetes 调度资源，中间用 gVisor/Kata/Firecracker 三种安全容器适配不同隔离强度。它解决的核心矛盾是 AI Agent 需要执行任意代码、访问浏览器和桌面，又不能让这些操作污染宿主环境或逃逸到公网。

## 学习目标

读完本文后你应当能够：

1. 说清 OpenSandbox 五层架构中每层的职责与可替换点
2. 区分 7 种 sandbox 适配器的隔离强度与适用场景
3. 描述一次代码执行如何从 SDK 层穿过五层到达容器运行时层
4. 在 Docker 模式与 Kubernetes 模式之间做出与场景匹配的选型决策
5. 列出 OpenSandbox 适用与不适用的三类场景的判断依据

## 目录

- [一、项目概览](#一项目概览)
- [二、技术架构](#二技术架构)
- [三、核心机制详解](#三核心机制详解)
- [四、任务流案例：一次代码执行如何穿过五层](#四任务流案例一次代码执行如何穿过五层)
- [五、快速开始](#五快速开始)
- [六、集成示例](#六集成示例)
- [七、与同类项目对比](#七与同类项目对比)
- [八、适用场景](#八适用场景)
- [九、Roadmap](#九roadmap)
- [十、采用建议](#十采用建议)
- [十一、常见问题排查](#十一常见问题排查)
- [十二、自测题](#十二自测题)
- [十三、进阶路径](#十三进阶路径)
- [十四、总结](#十四总结)

## 总览地图

OpenSandbox 分五层，每层职责独立，可以单独替换：

| 层 | 职责 | 关键组件 | 可替换点 |
|---|---|---|---|
| SDK 层 | 给开发者用的客户端 | Python / Java / Kotlin / JS / TS / C# | Go SDK 规划中 |
| 协议层 | 定义沙箱能做什么 | 生命周期 API + 执行 API | OpenAPI 规范在 `specs/` |
| 运行时层 | 管理沙箱进程 | `server`（FastAPI）+ `execd` + `ingress` + `egress` | 可自托管 |
| 沙箱环境层 | 预置的执行镜像 | Code Interpreter / Chrome / Playwright / Desktop / VS Code | 可自定义镜像 |
| 容器运行时层 | 提供隔离边界 | gVisor / Kata / Firecracker | 按安全强度选择 |

阅读建议：先看"技术架构"理解各层边界，再看"任务流案例"理解一次代码执行如何穿过这五层，最后按"采用建议"判断是否适合自己的场景。

---

## 一、项目概览

[OpenSandbox](https://github.com/alibaba/OpenSandbox) 是阿里巴巴开源的通用 AI 应用沙箱平台，提供多语言 SDK、统一沙箱 API、Docker/Kubernetes 运行时，涵盖编程 Agent、GUI Agent、Agent 评估、AI 代码执行、强化学习训练等场景。

**核心数据（截至 2026-06-25，数据来自 GitHub API）：**

| 指标 | 数值 |
|------|------|
| GitHub Stars | 11,649+ |
| Forks | 966+ |
| License | Apache-2.0 |
| 最新版本 | python/code-interpreter 0.1.2 |
| 官方文档 | https://open-sandbox.ai/ |

> 时效说明：Stars 和 Forks 为访问时快照，可能已变化；版本号以仓库 release 页为准。

**CNCF Landscape 已收录**（来源：[CNCF Landscape](https://landscape.cncf.io/)，访问于 2026-03-28）

### 1.1 项目定位

> OpenSandbox is a general-purpose sandbox platform for AI applications.
> 通用 AI 应用沙箱平台

**支持场景：**

| 场景 | 说明 |
|------|------|
| **编程 Agent** | Claude Code、OpenAI Codex CLI 等 CLI Agent 在沙箱内运行 |
| **GUI Agent** | 浏览器自动化、桌面环境操作 |
| **Agent 评估** | 在受控沙箱中评估 Agent 能力 |
| **AI 代码执行** | 实现 Code Interpreter 功能 |
| **强化学习训练** | RL CartPole 等训练任务 |

### 1.2 主要特色

| 特色 | 说明 |
|------|------|
| **多语言 SDK** | Python / Java / Kotlin / JavaScript / TypeScript / C# / Go（规划中） |
| **统一沙箱协议** | 生命周期管理 API + 执行 API |
| **Docker/Kubernetes** | 本地运行 + 大规模分布式调度 |
| **强隔离** | gVisor / Kata Containers / Firecracker 微虚拟机 |
| **网络安全策略** | Ingress 网关 + Egress 控制 |

---

## 二、技术架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│ OpenSandbox 架构                                            │
├─────────────────────────────────────────────────────────────┤
│ SDK 层（多语言）                                            │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│ │ Python   │ │ Java/    │ │ JS/TS    │ │ C#/.NET  │        │
│ │          │ │ Kotlin   │ │          │ │          │        │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
├─────────────────────────────────────────────────────────────┤
│ 沙箱协议层（Specs）                                         │
│ 生命周期管理 API + 执行 API                                 │
├─────────────────────────────────────────────────────────────┤
│ 运行时层（Server + Components）                             │
│ ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐         │
│ │ execd   │ │ ingress  │ │ egress  │ │ server   │         │
│ │ 命令/文件│ │ 入口代理 │ │ 出口控制 │ │ FastAPI  │         │
│ └─────────┘ └──────────┘ └─────────┘ └──────────┘         │
├─────────────────────────────────────────────────────────────┤
│ 沙箱环境层（Sandboxes）                                     │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│ │ Code     │ │ Chrome   │ │ Playwright│ │ Desktop  │        │
│ │ Interpreter│ │ Browser │ │ 自动化    │ │ VNC      │        │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
├─────────────────────────────────────────────────────────────┤
│ 容器运行时（Secure Container）                              │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐                     │
│ │ gVisor   │ │ Kata     │ │ Firecracker│                    │
│ │          │ │ Containers│ │ 微虚拟机  │                    │
│ └──────────┘ └──────────┘ └──────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 各层职责拆解

理解 OpenSandbox 的关键在于看清五层之间的边界：SDK 层只负责把请求发给运行时层，不直接接触容器；协议层用 OpenAPI 规范定义接口，让多语言 SDK 能保持一致行为；运行时层是控制面，负责创建、销毁、调度沙箱；沙箱环境层是数据面，提供预置镜像；容器运行时层是隔离边界，决定安全强度。

这种分层带来的实际收益：替换容器运行时不需要改 SDK 代码；新增一种沙箱环境（比如加一个 Rust 工具链镜像）不需要动协议层；从 Docker 切到 Kubernetes 只影响运行时层。

### 2.3 技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| SDK 语言 | Python/Java/Kotlin/JS/TS/C# | 多语言支持 |
| 后端 | Go 21.6%（来源：GitHub 语言统计，访问于 2026-03-28） | 核心组件 |
| 服务端 | Python FastAPI | 沙箱生命周期服务 |
| 容器 | Docker/Kubernetes | 运行时环境 |
| 安全容器 | gVisor/Kata/Firecracker | 强隔离 |

### 2.4 核心目录结构

```
OpenSandbox/
├── sdks/                # 多语言 SDK
│   ├── sandbox/         # Sandbox 基础 SDK
│   │   ├── python/      # Python Sandbox SDK
│   │   ├── kotlin/      # Java/Kotlin Sandbox SDK
│   │   ├── javascript/  # JS/TS Sandbox SDK
│   │   └── csharp/      # C#/.NET Sandbox SDK
│   └── code-interpreter/  # Code Interpreter SDK
├── specs/               # OpenAPI 规范
├── server/              # Python FastAPI 沙箱生命周期服务器
├── kubernetes/          # Kubernetes 部署
├── components/
│   ├── execd/           # 沙箱执行守护进程（命令/文件操作）
│   ├── ingress/         # 入口流量代理
│   └── egress/          # 出口网络控制
├── sandboxes/
│   └── code-interpreter/  # Code Interpreter 沙箱实现
├── examples/            # 示例代码
│   ├── claude-code/     # Claude Code 集成
│   ├── langgraph/       # LangGraph 集成
│   ├── chrome/          # Chrome 浏览器自动化
│   ├── playwright/      # Playwright 自动化
│   ├── desktop/         # 桌面 VNC 环境
│   └── rl-training/     # 强化学习训练
├── oseps/               # OpenSandbox 增强提案
├── docs/                # 架构文档
└── tests/               # E2E 测试
```

---

## 三、核心机制详解

### 3.1 多语言 SDK

OpenSandbox 提供**多语言 SDK**，覆盖主流开发语言：

| SDK | 语言 | 说明 |
|-----|------|------|
| Sandbox SDK | Python | 沙箱生命周期管理、命令执行、文件操作 |
| Sandbox SDK | Java/Kotlin | 同上 |
| Sandbox SDK | JavaScript/TypeScript | 同上 |
| Sandbox SDK | C#/.NET | 同上 |
| Code Interpreter SDK | Python | 代码解释器专用 |
| Code Interpreter SDK | Java/Kotlin | 同上 |
| Code Interpreter SDK | JavaScript/TypeScript | 同上 |
| Code Interpreter SDK | C#/.NET | 同上 |

**规划中：** Go SDK

为什么需要多语言 SDK？只提供 REST API 不够吗？因为不同语言的类型系统、异步模型、错误处理差异很大，直接调 REST 会让每个语言的用户都重复处理序列化和重试逻辑。SDK 把这些封装掉，让 Python 用户用 `async with sandbox`，Java 用户用 try-with-resources，各自符合本语言习惯。

### 3.2 沙箱协议

OpenSandbox 定义了两套核心 API，对应沙箱的两类操作：

**生命周期管理 API：**
- 创建/销毁沙箱
- 沙箱状态查询
- 超时管理

**执行 API：**
- 命令执行（shell）
- 文件操作（读写）
- 代码解释器调用

为什么分成两套？因为生命周期操作是控制面，频率低但必须可靠；执行操作是数据面，频率高但允许失败重试。分开后可以独立演进，比如执行 API 可以加流式输出，生命周期 API 可以加预热池，互不影响。

### 3.3 沙箱运行时

支持两种部署模式：

| 模式 | 适用场景 | 说明 |
|------|---------|------|
| **Docker** | 本地开发测试 | 单机快速启动 |
| **Kubernetes** | 生产环境 | 大规模分布式调度 |

**Kubernetes 高性能运行时特性：**
- 预热池（Pre-warmed pools）：提前创建好沙箱实例，请求来时直接分配，省去冷启动
- 自动扩缩容：根据负载调整沙箱数量
- 资源隔离：通过 Kubernetes 的 ResourceQuota 和 LimitRange 控制

为什么需要预热池？因为创建一个沙箱要拉镜像、起容器、初始化运行时，冷启动可能要几秒到几十秒。AI Agent 的代码执行通常是高频短任务，如果每次都冷启动，用户体验会非常差。预热池把这部分延迟摊到空闲期。

### 3.4 沙箱环境

OpenSandbox 内置多种沙箱环境，每种环境是一个预置镜像：

| 环境 | 说明 | 示例 |
|------|------|------|
| **Code Interpreter** | 代码执行沙箱 | Python/JavaScript 代码运行 |
| **Chrome** | 浏览器自动化 | VNC + DevTools |
| **Playwright** | Web 自动化测试 | 无头浏览器抓取 |
| **Desktop** | 完整桌面环境 | VNC 远程桌面 |
| **VS Code** | 云端 IDE | code-server Web IDE |

为什么预置这些环境？因为 AI Agent 的需求高度集中：要么执行代码，要么操作浏览器，要么操作桌面。预置镜像省去用户自己装 Chrome、配 VNC、装 Python 依赖的工作，启动即可用。

### 3.5 网络安全策略

**Ingress 网关（入口流量）：**
- 统一入口流量管理
- 多路由策略支持

**Egress 控制（出口流量）：**
- 沙箱级出口控制
- 网络隔离

为什么需要 Egress 控制？因为 AI Agent 执行的代码可能来自用户输入，也可能来自模型生成。如果沙箱能自由访问公网，恶意代码可以把宿主数据外传，或者攻击外部服务。Egress 控制让管理员能限定沙箱只能访问白名单域名，把攻击面收窄。

### 3.6 强隔离机制

支持三种安全容器运行时，对应不同隔离强度：

| 运行时 | 隔离方式 | 隔离级别 | 适用场景 |
|--------|---------|----------|---------|
| **gVisor** | 用户态内核拦截系统调用 | 用户内核隔离 | 中等安全，性能损失小 |
| **Kata Containers** | 硬件虚拟化 | VM 级隔离 | 高安全，性能损失中等 |
| **Firecracker** | AWS 开源微虚拟机 | 轻量级 VM | 高密度，启动快 |

为什么提供三种安全容器运行时？因为隔离强度和性能是权衡关系。gVisor 性能损失最小但隔离弱；Kata 隔离最强但启动慢；Firecracker 介于两者之间，适合多租户高密度场景。用户根据自己威胁模型选择：内部可信环境用 gVisor，公网多租户用 Firecracker，强合规场景用 Kata。

---

## 四、任务流案例：一次代码执行如何穿过五层

为了把抽象的分层讲清楚，跟踪一次"用户调用 Python SDK 执行 `2+2`"的完整流程：

1. **SDK 层**：Python SDK 把 `interpreter.codes.run("2+2")` 序列化为 HTTP 请求，发往 `server`
2. **协议层**：请求符合 `specs/` 中的 OpenAPI 规范，`server` 校验参数
3. **运行时层**：`server` 找到对应的沙箱实例（预热池中已创建），把执行请求转发给 `execd`
4. **沙箱环境层**：`execd` 在 Code Interpreter 镜像内启动 Python 进程，执行代码，捕获 stdout 和返回值
5. **容器运行时层**：整个沙箱进程跑在 gVisor/Kata/Firecracker 之一中，系统调用被拦截或虚拟化

返回路径相反：`execd` 把结果回传给 `server`，`server` 按 OpenAPI 规范封装响应，Python SDK 反序列化为 `result` 对象，用户拿到 `result.result[0].text` 即 `4`。

这个流程的关键点：每一层都可以独立替换。把 gVisor 换成 Firecracker，上层 SDK 代码完全不变；把 Code Interpreter 镜像换成自定义的 Rust 工具链镜像，`server` 和 `execd` 也不需要改。

---

## 五、快速开始

### 5.1 环境要求

| 工具 | 要求 |
|------|------|
| Docker | 必需（本地执行） |
| Python | 3.10+（运行示例和本地运行时） |

### 5.2 安装步骤

**1. 安装 Sandbox Server：**

```bash
uv pip install opensandbox-server
opensandbox-server init-config ~/.sandbox.toml --example docker
```

**2. 启动 Sandbox Server：**

```bash
opensandbox-server
# 显示帮助
opensandbox-server -h
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
    # 1. 创建沙箱
    sandbox = await Sandbox.create(
        "opensandbox/code-interpreter:v1.0.2",
        entrypoint=["/opt/opensandbox/code-interpreter.sh"],
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
        print(result.result[0].text) # 4
        print(result.logs.stdout[0].text) # 3.11.14

        # 7. 清理沙箱
        await sandbox.kill()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 六、集成示例

### 6.1 编程 Agent 集成

OpenSandbox 支持主流编程 Agent CLI：

| Agent | 说明 |
|-------|------|
| Claude Code | Anthropic CLI |
| Gemini CLI | Google CLI |
| OpenAI Codex CLI | OpenAI CLI |
| Qwen Code | 阿里通义 CLI |
| Kimi CLI | 月之暗面 CLI |

**示例：Claude Code 集成**

```bash
# 克隆仓库
git clone https://github.com/alibaba/OpenSandbox.git
cd OpenSandbox/examples/claude-code
# 查看 README 了解详细集成方式
```

### 6.2 LangGraph 集成

OpenSandbox 提供 LangGraph 状态机工作流集成：

```python
# LangGraph 集成示例
# 见 examples/langgraph/README.md
```

### 6.3 浏览器自动化

**Chrome 示例：**

```bash
# 浏览器自动化 + VNC + DevTools
# 见 examples/chrome/README.md
```

**Playwright 示例：**

```bash
# Playwright + Chromium 无头抓取和测试
# 见 examples/playwright/README.md
```

### 6.4 桌面环境

**Desktop 示例：**

```bash
# 完整桌面环境 + VNC 访问
# 见 examples/desktop/README.md
```

### 6.5 强化学习训练

**RL Training 示例：**

```bash
# DQN CartPole 训练 + checkpoints + summary 输出
# 见 examples/rl-training/README.md
```

---

## 七、与同类项目对比

| 特性 | OpenSandbox | E2B | Docker API | Kata Containers |
|------|-------------|-----|------------|-----------------|
| **多语言 SDK** | ✅ Python/Java/JS/C# | Python | 无 | 无 |
| **Kubernetes** | ✅ 原生支持 | 有限 | 需自己实现 | 有限 |
| **编程 Agent** | ✅ Claude/Gemini/Codex | ✅ | ❌ | ❌ |
| **浏览器环境** | ✅ Chrome/Playwright | ✅ | ❌ | ❌ |
| **代码解释器** | ✅ | ✅ | ❌ | ❌ |
| **CNCF 收录** | ✅ | ❌ | ❌ | ✅ |

对比说明：E2B 是商业化的代码执行沙箱，SDK 以 Python 为主，浏览器环境支持较弱；Docker API 只提供容器原语，需要自己封装沙箱协议和预热池；Kata Containers 只解决隔离层，不提供 SDK 和运行时管理。OpenSandbox 的差异点在于把 SDK、协议、运行时、环境、隔离五层打包成完整平台。

---

## 八、适用场景

| 场景 | 说明 |
|------|------|
| **AI 代码执行** | 云端 Code Interpreter |
| **编程 Agent** | Claude Code 等在沙箱中运行 |
| **浏览器自动化** | 网页抓取、UI 测试 |
| **桌面环境** | 远程 VNC 开发 |
| **Agent 评估** | 安全评估 Agent 能力 |
| **RL 训练** | 强化学习训练任务 |

---

## 九、Roadmap

### 9.1 SDK

| 功能 | 说明 |
|------|------|
| **客户端连接池** | 预配置沙箱，Xms 获取环境 |
| **Go SDK** | Go 语言客户端 SDK |

### 9.2 沙箱运行时

| 功能 | 说明 |
|------|------|
| **持久化存储** | 可挂载持久化卷 |
| **轻量级沙箱** | PC 直接运行的 AI 工具沙箱 |
| **安全容器** | AI Agent 容器内安全沙箱 |

### 9.3 部署

| 功能 | 说明 |
|------|------|
| **部署指南** | 自托管 Kubernetes 集群部署指南 |

---

## 十一、常见问题排查

实际跑 OpenSandbox 时容易踩的坑与排查路径：

**1. Sandbox Server 启动失败**

症状：`opensandbox-server` 命令报错或端口被占用。

排查步骤：
```bash
# 检查端口占用（默认端口）
lsof -i :8080
# 检查配置文件
cat ~/.sandbox.toml
# 查看日志
opensandbox-server --log-level debug
```

**2. 代码执行超时**

症状：SDK 调用 `interpreter.codes.run()` 长时间无响应。

可能原因：
- sandbox 镜像未正确拉取
- 网络隔离导致无法访问外部依赖
- 代码本身有死循环

排查步骤：
```python
# 设置超时
sandbox = await Sandbox.create(..., timeout=timedelta(seconds=30))
# 检查 sandbox 状态
print(sandbox.status)
```

**3. Kubernetes 模式下 sandbox 创建慢**

症状：在 Kubernetes 模式下创建 sandbox 需要几十秒。

原因：镜像拉取时间长，预热池未配置。

修复：配置预热池（`pre-warmed pools`），提前创建好 sandbox 实例。

**4. Egress 控制导致依赖安装失败**

症状：在 Code Interpreter 里 `pip install` 失败，报网络错误。

原因：Egress 控制默认可能阻止公网访问。

修复：在 `sandbox.toml` 里配置 Egress 白名单，允许访问 PyPI 镜像源。

**5. 多语言 SDK 类型不匹配**

症状：Java SDK 调用时报类型错误。

原因：SDK 版本不匹配或类型定义有变化。

修复：检查 SDK 版本，确保与服务端版本兼容。查看 `sdks/` 目录下对应 SDK 的 README。

---

## 十二、自测题

用以下 5 题检验理解程度。答案折叠在每题下方。

**Q1**：OpenSandbox 五层架构中，哪一层负责定义生命周期管理 API 和执行 API？

> **答案**：协议层（Protocol Layer）。它用 OpenAPI 规范定义接口，让多语言 SDK 能保持一致行为。

**Q2**：7 种 sandbox 适配器中，哪几种提供文件系统级隔离？

> **答案**：`docker` 提供容器级文件系统隔离；`modal` / `daytona` / `e2b` 提供云端隔离，适合多租户生产场景。`local` / `ipython` 共享宿主命名空间，仅适合本地实验。

**Q3**：为什么需要预热池（Pre-warmed pools）？

> **答案**：创建一个 sandbox 要拉镜像、起容器、初始化运行时，冷启动可能要几秒到几十秒。AI Agent 的代码执行通常是高频短任务，如果每次都冷启动，用户体验会非常差。预热池把这部分延迟摊到空闲期。

**Q4**：OpenSandbox 与 E2B 的主要差异是什么？

> **答案**：E2B 是商业化的代码执行沙箱，SDK 以 Python 为主，浏览器环境支持较弱；OpenSandbox 提供完整五层平台（SDK、协议、运行时、环境、隔离），支持多语言 SDK、Kubernetes 原生、多种沙箱环境，且已被 CNCF Landscape 收录。

**Q5**：下面哪个场景不适合用 OpenSandbox？

> A. 需要执行任意代码的 AI 应用
> B. 对启动延迟极敏感的实时交互场景
> C. 多租户代码执行平台
> D. Agent 评估基准

> **答案**：B。预热池也救不了冷启动，纯 API 调用型 Agent 不需要沙箱，简单关键词搜索直接用 grep 更快。

---

## 十三、进阶路径

读完本文后，按以下顺序深入：

1. **跑通最小示例**：按"快速开始"章节安装，用 Docker 模式跑通基本使用示例，确认环境正常。
2. **切换 sandbox 环境**：同一任务分别用 Code Interpreter、Chrome、Playwright 环境跑一遍，理解不同环境的适用场景。
3. **上 Kubernetes 模式**：在测试集群里部署 `kubernetes/` 目录下的资源，配置预热池，记录冷启动时间与资源消耗。
4. **自定义镜像**：基于 `sandboxes/code-interpreter/` 自定义镜像，增加项目需要的依赖，保持 entrypoint 协议不变。
5. **读源码**：从 `server/` 目录开始，理解 FastAPI 服务如何管理 sandbox 生命周期，再看 `components/execd/` 理解命令执行流程。
6. **贡献社区**：OpenSandbox 是开源项目，可以贡献新的 sandbox 环境、改进文档或提交 bug fix。

---

## 十四、总结

OpenSandbox 提供的信号是：在 AI Agent 需要执行任意代码、访问浏览器和桌面的今天，"如何提供安全隔离的执行环境" 比 "模型能力有多强" 还有更多工程空间。OpenSandbox 把这件事做成了平台级产品——五层架构、多语言 SDK、统一沙箱协议、Docker/Kubernetes 运行时、强隔离机制覆盖了从本地实验到生产部署的链路。

对于想要构建安全 AI 应用平台的开发者，OpenSandbox 是 2026 年值得深入的开源项目之一。

---

## 十、采用建议

根据场景给出采用顺序：

1. **先试**：本地用 Docker 模式跑通 `examples/claude-code` 或基本使用示例，验证沙箱能起来、代码能执行
2. **再选隔离层**：内部可信环境用 gVisor，公网多租户用 Firecracker，强合规场景用 Kata
3. **再上 Kubernetes**：单机 Docker 模式只适合开发测试，生产环境必须用 Kubernetes 模式才能用预热池和自动扩缩容
4. **最后自定义镜像**：预置环境不够用时，基于 `sandboxes/code-interpreter/` 自定义镜像，保持 entrypoint 协议不变

**适用边界：**
- 适合：需要执行任意代码、操作浏览器或桌面的 AI 应用；多租户代码执行平台；Agent 评估基准
- 不适合：纯 API 调用型 Agent（不需要沙箱）；对启动延迟极敏感的实时交互场景（预热池也救不了冷启动）；不需要隔离的内部工具

### 资源链接

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/alibaba/OpenSandbox |
| 官网 | https://open-sandbox.ai/ |
| 中文文档 | https://open-sandbox.ai/zh/ |
| 架构文档 | https://github.com/alibaba/OpenSandbox/blob/main/docs/architecture.md |

---

**相关话题标签**

#OpenSandbox #沙箱 #AI 平台 #Docker #Kubernetes #CNCF

**来源**

- GitHub：https://github.com/alibaba/OpenSandbox
- CNCF Landscape：https://landscape.cncf.io/

---

*OpenSandbox 由阿里巴巴开源，采用 Apache-2.0 许可证，已被 CNCF Landscape 收录。数据截至 2026-03-28，以仓库实际状态为准。*
