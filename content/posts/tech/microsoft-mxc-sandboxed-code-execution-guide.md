---
title: "Microsoft MXC：跨平台策略驱动沙箱执行容器，AI Agent 安全运行的新底座"
date: 2026-06-07T09:30:00+08:00
slug: "microsoft-mxc-sandboxed-code-execution-guide"
description: "Microsoft MXC 是微软开源的跨平台沙箱代码执行系统，统一封装 Windows Sandbox、AppContainer、LXC、Bubblewrap、Seatbelt、MicroVM 等十余种底层隔离后端，对外提供 JSON 配置和 TypeScript SDK。本文解读其分层隔离思路、Schema 设计、状态生命周期 API 与早期预览阶段的明确边界。"
draft: false
categories: ["技术笔记"]
tags: ["沙箱", "AI Agent", "代码执行", "微软", "安全隔离"]
---

# Microsoft MXC：跨平台策略驱动沙箱执行容器

> **目标读者**：负责在生产环境运行不可信代码、模型生成代码或第三方工具的 AI 平台 / DevOps / 安全工程同学
> **核心问题**：当 Agent 框架、CI 系统或 IDE 插件需要在不同操作系统上隔离执行任意代码时，Windows Sandbox、Linux Bubblewrap / LXC、macOS Seatbelt 这些底层机制如何用一套统一的策略和 API 表达？
> **难度**：⭐⭐⭐（进阶）
> **预计阅读时间**：12 分钟

---

## 学习目标

通过本文，你将掌握以下核心能力：

- 理解 MXC 的分层隔离思路和跨平台抽象设计
- 掌握 MXC 的 Schema 双轨机制（稳定版 vs 实验版）
- 学会使用 TypeScript SDK 执行沙箱代码
- 理解 MXC 的状态生命周期 API（provision → start → exec → stop → deprovision）
- 识别 MXC 当前的安全边界和适用场景
- 能够判断 MXC 是否适合你的 Agent/CI/IDE 项目

## 目录

1. [为什么 MXC 值得看](#一为什么-mxc-值得看)
2. [核心判断](#二核心判断)
3. [系统地图：MXC 的三层结构](#三系统地图mxc-的三层结构)
4. [平台支持矩阵](#四平台支持矩阵来自-readme-实测)
5. [任务流案例：跑一段「AI 生成的 Python」到底发生了什么](#五任务流案例跑一段ai-生成的-python到底发生了什么)
6. [Schema 版本与「稳定/实验」双轨](#六schema-版本与稳定实验双轨)
7. [显式风险：微软自己说的「不是安全边界」](#七显式风险微软自己说的不是安全边界)
8. [谁应该关注，谁可以先观望](#八谁应该关注谁可以先观望)
9. [阅读路径建议](#九阅读路径建议)

---

## 一、为什么 MXC 值得看

过去两年 AI Agent 的爆发，把「让大模型自己跑代码」从一个 Demo 推到了生产链路。Claude Code、Codex CLI、各种 Coding Agent 在用户机器上自动 `npm install`、执行 shell 命令、改写文件系统——这背后每一行 `child_process.spawn` 都在隐式承担一个沙箱责任。

而「沙箱」这件事，长期被切割成三个互不兼容的世界：

- **Windows** 有 AppContainer、Base Process Container、Windows Sandbox、WSL Distros，权限边界在 SID、Capability、Token 上
- **Linux** 有 Bubblewrap、Landlock、nsproxy、LXC、Firecracker，边界在 namespace、cgroup、seccomp
- **macOS** 长期被 Seatbelt（sandbox-exec）主导，规则用 Scheme 表达，和 Linux 几乎不通用

结果就是：跨平台 Agent 框架写一段「跑用户代码」就要写三套适配，policy 描述也三套。**Microsoft MXC（Microsoft eXecution Container）想做的事情就是把这三套机制收成一套 JSON 配置和一套 TypeScript SDK**。

> 重要前提：MXC 目前是「early preview」阶段，微软在 README 顶部用 `> [!WARNING]` 明确写了 **当前任何 MXC profile 都不应被视为安全边界（security boundary）**，下游策略存在已知过度宽松的问题。这一点先记住，后面会专门讲。

---

## 二、核心判断

| 维度 | 结论 |
|------|------|
| **形态** | 跨 OS 的「沙箱执行层中间件」，不是 Agent 框架本身 |
| **核心抽象** | JSON Schema（`mxc-config`） + 多 Backend 适配 + 状态生命周期 API |
| **目标场景** | Agent / Coding CLI / IDE 插件 / CI 沙箱执行 |
| **当前状态** | 早期预览，Schema 处于 `0.6.0-alpha`（稳定）与 `0.7.0-dev`（实验）双轨 |
| **值得立刻接入** | 想统一 Windows / Linux / macOS 三端沙箱的 Agent 平台 |
| **不建议立刻接入** | 把 MXC 当作可信安全边界、用于生产环境对抗恶意对手 |

一句话：**MXC 是一块「Agent 安全的地基」候选者，不是成品。** 它的设计价值在于分层抽象和跨平台一致性，而不是当前 policy 的强度。

---

## 三、系统地图：MXC 的三层结构

MXC 自下而上可以拆成三层，对应到仓库的目录布局非常清晰：

```text
┌─────────────────────────────────────────────────────────────┐
│  Layer 3：策略与 API 层                                       │
│  - schemas/        JSON Schema（0.5/0.6 稳定 + 0.7 dev）     │
│  - sdk/            @microsoft/mxc-sdk（TS，一键 + 状态生命周期）│
│  - docs/sandbox-policy/v1   策略规范                           │
├─────────────────────────────────────────────────────────────┤
│  Layer 2：原生执行层                                           │
│  - src/   Rust workspace，编译出 wxc-exec (Windows) /         │
│           lxc-exec (Linux) / mxc-exec-mac (macOS)            │
│  - 统一 CLI 入口：<binary> config.json                       │
├─────────────────────────────────────────────────────────────┤
│  Layer 1：OS 原生隔离后端（按平台可选）                          │
│  Windows  : processcontainer / windows_sandbox / wslc /      │
│             microvm / hyperlight / isolation_session        │
│  Linux    : bubblewrap / lxc / microvm / hyperlight         │
│  macOS    : seatbelt                                         │
└─────────────────────────────────────────────────────────────┘
```

最关键的设计取舍是 **「策略统一、后端可换」**：

- 业务侧只写一份 `mxc-config` JSON（或通过 SDK 的 `createConfigFromPolicy` 生成）
- 原生 binary 根据 `host.platform` 字段派发到对应后端
- 想从 `bubblewrap` 升级到 `microvm`？改一行配置，不用动业务代码

这一层抽象对 Agent 平台尤其重要——同一份「允许读 `~/.cache/...`、禁止联网、超时 30s」的策略，可以同时在用户的 macOS、本地 Linux 容器和 Windows CI runner 上生效。

---

## 四、平台支持矩阵（来自 README 实测）

下表是 README 章节「Platforms」里给出的官方支持矩阵，可以直接当作选型参考：

| 平台 | 默认后端 | 其他可选后端 | 构建要求 |
|------|---------|-------------|---------|
| **Windows 11 24H2+**（已在 25H2 验证） | `processcontainer` | `windows_sandbox` / `wslc` / `microvm` / `hyperlight` / `isolation_session` | `processcontainer`: 26100（24H2）<br>`isolation_session`: 26300.8553（Insider Preview） |
| **Linux x64 / ARM64** | `bubblewrap` | `lxc` / `microvm` / `hyperlight` | Linux 需 `bwrap`（默认）或 `lxc` 工具集 |
| **macOS ARM64 / x64**（Schema `0.6.0-alpha`+） | `seatbelt` | — | — |

几个细节很值得关注：

1. **稳定 / 实验分层明确**：稳定 one-shot 后端（`processcontainer` / `bubblewrap` / `lxc`）不需要开 experimental；其余后端需要在 `SandboxSpawnOptions.experimental = true` 或 CLI 加 `--experimental`。
2. **macOS 早期很受限**：在 `0.6.0-alpha` 之前，macOS 的 schema 还不完整；目前 Network Policy 在 macOS 上**不支持 Proxy**，Windows 上 Network Policy 还在补全。
3. **微 VM 选项**：Linux 上有 `microvm`（基于 NanVix）和 `hyperlight` 两种 micro-VM 路线，给了对启动延迟和隔离强度有不同取舍的团队。

---

## 五、任务流案例：跑一段「AI 生成的 Python」到底发生了什么

光看抽象容易飘，下面用 README 给出的 SDK 例子把一个完整请求流走一遍。假设你的 Agent 收到一段模型生成的 Python 代码，要在用户机器上跑：

```typescript
import {
  spawnSandboxFromConfig, createConfigFromPolicy,
  getAvailableToolsPolicy, getTemporaryFilesPolicy,
  getPlatformSupport,
} from '@microsoft/mxc-sdk';

// 1. 平台能力探测
if (!getPlatformSupport().isSupported) {
  throw new Error('MXC not available on this host');
}

// 2. 组合策略：可用工具只读 + 临时目录可写
const tools = getAvailableToolsPolicy(process.env);
const temp  = getTemporaryFilesPolicy();

const config = createConfigFromPolicy({
  version: '0.6.0-alpha',
  filesystem: {
    readonlyPaths:  tools.readonlyPaths,
    readwritePaths: temp.readwritePaths,
  },
  network: { allowOutbound: false },
  timeoutMs: 30_000,
});

// 3. 把模型生成的命令挂到配置上
config.process!.commandLine = 'python -c "print(\'hello from sandbox\')"';

// 4. 启动沙箱子进程
const child = spawnSandboxFromConfig(config, { usePty: false });
child.stdout!.on('data', (d) => process.stdout.write(d));
child.on('close', (code) => console.log('exit:', code));
```

执行时这条请求流穿过的就是上面那张三层地图：

```text
SDK 入口
  └─ 序列化为 mxc-config JSON
       └─ 原生 binary 接收（macOS 上是 mxc-exec-mac）
            └─ 派发到 seatbelt 后端
                 └─ Seatbelt Scheme 注入 sandbox-exec
                      └─ 实际执行 python -c ...
                           └─ stdout/stderr 默认直通到 child
```

如果要做「Agent 工具调用需要长连接」这种场景，MXC 还提供状态生命周期 API：

```typescript
import {
  provisionSandbox, startSandbox, execInSandboxAsync,
  stopSandbox, deprovisionSandbox,
} from '@microsoft/mxc-sdk';
```

走 `provision → start → exec → stop → deprovision` 五个阶段，避免每次都从零拉起 sandbox。

---

## 六、Schema 版本与「稳定/实验」双轨

MXC 在仓库里同时维护两套 Schema，这是工程上很务实的设计：

| Schema 版本 | 状态 | 文件 |
|-------------|------|------|
| `0.5.0-alpha` | 稳定（已归档） | `schemas/stable/mxc-config.schema.0.5.0-alpha.json` |
| `0.6.0-alpha` | 稳定（当前推荐） | `schemas/stable/mxc-config.schema.0.6.0-alpha.json` |
| `0.7.0-dev` | 实验（包含 experimental 后端 + 状态生命周期） | `schemas/dev/mxc-config.schema.0.7.0-dev.json` |

经验法则：**新代码选 `0.6.0-alpha`**；要试状态生命周期或实验后端再上 `0.7.0-dev`，并在调用时显式声明 `experimental: true`。版本演进规则写在 `docs/versioning.md`。

---

## 七、显式风险：微软自己说的「不是安全边界」

这一节是整篇文章最重要的「边界声明」，直接引用 README 顶部那段 WARNING：

> This repository contains an early preview of code published to enable early integration and feedback... There are known cases where the current policies generated by the MXC SDK in this repository are overly permissive and will be addressed before this is made more generally available. Security researcher partnership while MXC matures is welcome, however **no MXC profiles should be treated as security boundaries currently**.

翻译成对工程同学的判断：

1. **不要把 MXC 直接当作生产级沙箱来对抗主动恶意对手**——它是「执行层」不是「防护层」。
2. **策略模板可能过宽**——`getAvailableToolsPolicy` 给出的默认允许列表里，可能涵盖比你预期更多的系统工具路径，使用前需要自己收紧。
3. **Windows 的 sandbox policy v1 还在迭代**——`docs/sandbox-policy/v1/policy.md` 是当前规范，后续大概率会升 v2。
4. **跨平台策略有缺口**——Network Policy 在 macOS 上不支持 Proxy；Windows 上 Outbound 过滤还在补。设计「在 Windows 上能拦，macOS 上拦不到」的能力时，要假设 macOS 是兜底弱项。
5. **实验后端可能有兼容变化**——`microvm` / `hyperlight` / `isolation_session` 都在快速演进，不要把它们的稳定性当作 SLA。

对应的策略：把 MXC 接到 Agent 框架里时，**自己再叠一层审计 / 速率限制 / 资源限额**，把 MXC 当作「执行沙箱」而非「安全防线」。

---

## 八、谁应该关注，谁可以先观望

**值得现在评估的团队：**

- 跨平台 AI Agent 框架作者：希望一次策略配置在 Win/macOS/Linux 都生效
- IDE / 编程助手后端：需要在用户本地跑模型生成代码，又不想维护三套隔离实现
- CI / 沙箱服务：要把任意 PR / 工具调用放到有边界的执行环境
- 安全工程：希望参与 `sandbox-policy/v1` 的早期规范反馈（微软明确欢迎）

**可以先观望的团队：**

- 只要在 Linux 跑模型代码：直接用 `bubblewrap` + Landlock 就够了
- macOS 单平台：Seatbelt 单独用更轻
- 生产对抗强恶意对手：等微软给出 GA 标签 + 第三方审计再说

---

## 九、阅读路径建议

如果你想最短时间把 MXC 摸透，按这个顺序看仓库：

1. **README**——平台矩阵 + 警告段
2. **`docs/schema.md`**——理解 `mxc-config` JSON 的全部字段
3. **`docs/sandbox-policy/v1/policy.md`**——策略规范，对应到 SDK 的 `createConfigFromPolicy`
4. **`sdk/README.md`**——TypeScript API 细节和 one-shot / state-aware 两种调用模式
5. **挑一个 backend 文档**：`docs/bwrap-support/` 或 `docs/macos-support/` 等，看真实后端如何接收 JSON

MXC 的最大价值在于「把跨平台沙箱这件事拉到统一的策略面」。对 Agent 平台来说，它不是「要不要用」的问题，而是「等它 GA 之后要不要第一时间替换现有自研适配」的问题。

---

## 自测题

1. **MXC 的核心抽象是什么？**
   <details>
   <summary>查看答案</summary>
   答案：JSON Schema（mxc-config）+ 多 Backend 适配 + 状态生命周期 API。业务侧只写一份配置，原生 binary 根据平台派发到对应后端。
   </details>

2. **MXC 目前是否可以作为生产级安全边界使用？**
   <details>
   <summary>查看答案</summary>
   答案：不可以。微软在 README 顶部明确写了 WARNING：当前任何 MXC profile 都不应被视为安全边界，下游策略存在已知过度宽松的问题。
   </details>

3. **如果想从 `bubblewrap` 升级到 `microvm`，需要修改业务代码吗？**
   <details>
   <summary>查看答案</summary>
   答案：不需要。只需修改一行配置（改 backend 字段），不用动业务代码。这是 MXC「策略统一、后端可换」设计的核心价值。
   </details>

4. **`0.6.0-alpha` 和 `0.7.0-dev` 两个 Schema 版本有什么区别？**
   <details>
   <summary>查看答案</summary>
   答案：`0.6.0-alpha` 是稳定版，推荐新代码使用；`0.7.0-dev` 是实验版，包含实验后端和状态生命周期 API，调用时需要显式声明 `experimental: true`。
   </details>

5. **MXC 的状态生命周期 API 包含哪五个阶段？**
   <details>
   <summary>查看答案</summary>
   答案：provision → start → exec → stop → deprovision。这五个阶段避免每次都从零拉起 sandbox，适合需要长连接的 Agent 工具调用场景。
   </details>

---

## 练习

1. **在自己的 macOS 机器上安装 MXC SDK**，尝试运行 README 中的 SDK 例子，观察 sandbox 的执行日志。
2. **修改 SDK 例子中的 `filesystem` 配置**，尝试限制只能读取 `~/.cache/` 目录，禁止写入任何其他目录，验证隔离是否生效。
3. **对比 `bubblewrap`（Linux）和 `seatbelt`（macOS）的策略表达差异**，思考如何写出一份在两个平台上都能正确生效的 MXC 配置。

---

## 进阶路径

1. **深入后端实现**：阅读 `src/` 目录下的 Rust workspace，理解 `wxc-exec` / `lxc-exec` / `mxc-exec-mac` 如何接收 JSON 配置并派发到对应后端。
2. **参与策略规范反馈**：阅读 `docs/sandbox-policy/v1/policy.md`，在实际使用中记录策略过宽或过严的案例，向微软反馈。
3. **集成到 Agent 框架**：尝试将 MXC 接入自己维护的 Agent 框架或 CI 系统，替换现有的自研沙箱适配。
4. **安全审计**：在 MXC GA 之前，不要将其当作唯一的安全防线，叠加审计、速率限制、资源限额等额外保护层。
5. **关注微 VM 路线**：跟踪 `microvm`（NanVix）和 `hyperlight` 的演进，评估是否需要从 `bubblewrap` 升级到微 VM 后端。

---

## 资料口径说明

1. **信息来源**：本文基于 Microsoft MXC 仓库的 README、SDK 文档和 `docs/sandbox-policy/v1/policy.md` 编写，所有技术细节均来自官方文档。
2. **版本时效性**：MXC 处于 early preview 阶段，Schema 版本（`0.6.0-alpha` / `0.7.0-dev`）和后端支持情况可能快速变化，请以仓库最新代码为准。
3. **安全声明**：微软明确声明当前 MXC profile 不应被视为安全边界，本文中所有关于安全性的讨论均以此为前提，不构成安全建议。
4. **平台支持**：本文中的平台支持矩阵来自 README 的「Platforms」章节，实际可用性可能因操作系统版本、构建配置而有所差异。
5. **代码示例**：本文中的 TypeScript 代码示例来自 SDK 的 README，实际使用时请参考最新版 SDK 的 API 文档。
6. **判断与建议边界**：本文给出的「谁应该关注」和「采用建议」基于技术分析，实际决策需要结合团队的具体场景、风险承受能力和技术栈。

---

## 附：仓库速览

| 指标 | 数值 |
|------|------|
| 仓库 | [microsoft/mxc](https://github.com/microsoft/mxc) |
| 当前 Stars | 585+（早期预览，处于 trending） |
| 当前 Schema | `0.6.0-alpha`（稳定）/ `0.7.0-dev`（实验） |
| 主体语言 | Rust（native binary）+ TypeScript（SDK） |
| 许可证 | 仓库内 `LICENSE.md` 详述（早期预览条款） |
| 状态标签 | early preview（README 顶部 WARNING 明示） |
