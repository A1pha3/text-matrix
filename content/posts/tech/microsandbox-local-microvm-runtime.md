---
title: "microsandbox：100 毫秒内启动的本地微型虚拟机"
date: 2026-08-19T03:26:14+08:00
slug: "microsandbox-local-microvm-runtime"
github_repo: "superradcompany/microsandbox"
source_key: "gh:superradcompany/microsandbox"

description: "microsandbox 是一个 Rust 编写的本地优先 microVM 运行时，用 OCI 标准镜像在 100 毫秒内启动隔离虚拟机，支持 AI Agent、用户代码、CI 等不可信负载，提供 Rust、Python、TypeScript、Go 多语言 SDK。"
categories: ["技术笔记"]
tags: ["microVM", "Rust", "容器", "隔离", "AI Agent"]
---

# microsandbox：100 毫秒内启动的本地微型虚拟机

AI Agent（智能体）要跑用户代码、插件要执行第三方脚本、CI 要构建不可信产物——这些场景都需要隔离，但传统虚拟机太重、普通容器隔离又太薄。microsandbox 站在两者之间：**一个本地优先的 microVM（微型虚拟机）运行时，启动速度在 100 毫秒级**，用起来却像 Docker 一样熟悉。

读完本文，你会清楚三件事：microVM 和容器的隔离边界差在哪里；microsandbox 如何用占位符机制让密钥“可用但不可见”；如何通过 CLI（命令行工具）或 SDK（软件开发包）启动并控制一个沙箱。

## 目录

- 一分钟总览
- 为什么是 microVM 而不是容器
- 架构：libkrun、agentd 与 14 个 crate
- 上手：CLI 与多语言 SDK
- 秘密保护：占位符与网络边界替换
- AI Agent 场景的针对性设计
- 适用边界
- 自检与排障
- 常见问题 FAQ
- 动手练习
- 进阶方向
- 参考文献

## 一分钟总览

microsandbox 由 superradcompany 开发（Y Combinator 支持），Rust 编写，Apache 2.0 协议，仓库约 7,700 stars（截至 2026-08-19）。它把**不可信负载**（AI Agent、用户代码、插件、CI 任务、开发环境、爬虫、自动化）跑进快速启动的本地 microVM 里，提供硬件级隔离，同时保持 Docker 风格的工作流。

```sh
npx microsandbox run debian      # 一条命令启动一个 microVM
msb run debian                   # 安装 CLI 后的等价写法
```

关键特性（来自仓库 README）：

- **硬件级隔离**：microVM 技术，隔离边界在硬件虚拟化层而非进程层
- **跨平台**：Linux（KVM，内核虚拟机模块）、macOS（Apple Silicon 自带 Hypervisor）、Windows 10+（WHP，Windows Hypervisor Platform）
- **OCI 兼容**：直接跑 Docker Hub、GHCR 或任意 OCI（开放容器倡议）仓库的标准容器镜像
- **毫秒级启动**：平均启动时间低于 100 毫秒（README 注明测量环境为 M1 机器的 guest 启动）
- **可嵌入**：在代码里直接拉起 VM，无需安装服务器，也无需常驻 daemon（守护进程）
- **秘密不泄漏**：不可利用的密钥永远不进入 VM
- **长驻会话**：沙箱可分离（detached）模式运行，适合长生命周期任务

## 为什么是 microVM 而不是容器

容器共享宿主内核，隔离靠 namespace（命名空间）+ cgroup（控制组），同一个内核漏洞可能同时打穿所有容器。microVM 则给每个沙箱一个**独立、最小化的虚拟机**，自己的内核、自己的内存布局，隔离边界是真正的硬件虚拟化。

microsandbox 用 OCI 标准镜像做输入——也就是说，你熟悉的 `python:3.12`、`debian` 这些镜像直接就能用，不用重新打包。它把"虚拟机的强隔离"和"镜像生态的熟悉度"结合在了一起：启动一个 microVM 的操作体验，和 `docker run` 几乎没有区别。

## 架构：libkrun、agentd 与 14 个 crate

microsandbox 没有从零实现虚拟化，而是构建在 [libkrun](https://github.com/containers/libkrun) 之上——这是 containers 项目下的轻量级 KVM 运行时库，配合 `libkrunfw` 提供 guest 内核。README 致谢同时提到 [smoltcp](https://github.com/smoltcp-rs/smoltcp)，一个 Rust 编写的嵌入式 TCP/IP 协议栈，用于沙箱内的网络处理。

仓库是一个 Cargo workspace，`crates/` 目录下有 14 个 crate，分工清晰：

| crate | 职责 |
| ------ | ------ |
| `cli` | `msb` 命令行工具 |
| `runtime` | microVM 生命周期管理 |
| `agentd` | 运行在 guest 内的代理进程 |
| `image` | OCI 镜像拉取与缓存 |
| `network` / `vsock` | 网络栈与宿主机-客户机通信 |
| `filesystem` | 卷与文件系统挂载 |
| `protocol` / `db` / `migration` | SDK 通信协议、本地状态与迁移 |
| `metrics` / `metrics-collector` | CPU/内存/网络实时指标 |
| `testing` / `utils` | 测试支撑与公共工具 |

理解这个结构的意义在于：SDK 调用 `create()` 时，实际是以子进程方式启动 runtime，runtime 再通过 libkrun 拉起 microVM——整条链路不需要常驻服务。这也是"无需基础设施"这个卖点的工程来源。

## 上手：CLI 与多语言 SDK

### CLI 安装与基本操作

```sh
curl -fsSL https://install.microsandbox.dev | sh    # macOS / Linux
msb run debian
```

Windows 走 PowerShell 安装脚本 `irm https://install.microsandbox.dev/windows | iex`；brew、npm、uv、cargo 也都能装。底层要求：macOS 需要 Apple Silicon，Linux 需要 KVM 开启，Windows 需要 WHP 开启（Windows Server 还需要嵌套虚拟化）。**项目仍是 beta**，README 明确提示会有 breaking changes、缺失功能和粗糙边角。

CLI 覆盖沙箱、镜像、卷的完整生命周期：

```sh
msb create --name app python     # 创建命名沙箱
msb exec app -- python -c "import this"
msb stop app && msb start app    # 生命周期控制
msb pull python && msb image ls  # 镜像管理
msb metrics app                  # 实时 CPU/内存/网络指标
```

### SDK：在代码里嵌一个沙箱

microsandbox 的 SDK 是它的真正卖点——一行代码就能以子进程方式拉起一个 microVM，不需要任何基础设施。官方提供 **Rust、Python、TypeScript、Go、Ruby** 五种语言的 SDK：

```rust
use microsandbox::Sandbox;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let sandbox = Sandbox::builder("my-sandbox")
        .image("python")
        .cpus(1)
        .memory(512)
        .create()
        .await?;

    let output = sandbox
        .exec("python", ["-c", "print('Hello from a microVM!')"])
        .await?;

    println!("{}", output.stdout()?);
    sandbox.stop().await?;
    Ok(())
}
```

Python 版本几乎逐行对应：

```python
import asyncio
from microsandbox import Sandbox

async def main():
    sandbox = await Sandbox.create(
        "my-sandbox",
        image="python",
        cpus=1,
        memory=512,
    )

    output = await sandbox.exec("python", ["-c", "print('Hello from a microVM!')"])
    print(output.stdout_text)
    await sandbox.stop()

asyncio.run(main())
```

注意一个时序细节：第一次调用 `create()` 会拉取镜像（如果本地没有缓存），耗时取决于网络；后续运行复用缓存，才能体现 100 毫秒级的启动速度。

### 网络管控与秘密注入

Ruby SDK 展示了更精细的管控——限制网络只允许特定 host 与端口，并且秘密以"只可被指定 host 访问"的方式注入：

```ruby
require "microsandbox"

sandbox = Microsandbox::Sandbox.create(
  "my-sandbox",
  image: "python",
  cpus: 1,
  memory: 512,

  network: {
    allowed_hosts: ["api.openai.com"],
    allowed_ports: [443]
  },

  secrets: [{
    env: "OPENAI_API_KEY",
    value: ENV.fetch("OPENAI_API_KEY"),
    allowed_host: "api.openai.com"
  }]
)
```

这里能看到 microsandbox 对 AI 场景的针对性设计：**允许 API（应用程序接口）调用但拒绝横向移动**——Agent 能访问 OpenAI API，却拿不到宿主机的任意网络。至于密钥为什么"进了配置却没进 VM"，下一节展开。

## 秘密保护：占位符与网络边界替换

"秘密不泄漏"在官方文档里不是一句口号，而是一个有精确边界的机制（见 docs/security/secrets.mdx）：

1. 你把一个密钥绑定到环境变量，并列出它允许的 host。
2. guest 环境里收到的是**占位符**（默认形如 `$MSB_<env_var>`），永远不是真实值。
3. 负载像使用密钥一样使用占位符——放进请求头、auth 字段、查询串或正文。
4. 出站流量到达允许的 host 时，宿主机一侧的网络代理解密被拦截的 TLS（传输层安全）连接，验证请求确实去往声称的目的地，再把占位符替换为真实值转发。
5. 上游服务器收到真实密钥，guest 自始至终没有接触过它。

替换动作有四道闸门：TLS 的 SNI（服务器名称指示）必须匹配允许的 host 模式；目标 IP 必须确实通过拦截器解析出来（硬编码 IP 伪造 SNI 不算数）；默认要求被拦截的 TLS 连接；HTTP 请求的 `Host` 头必须与 SNI 一致，封死 domain-fronting。任何一项不满足，占位符原样发出——对端拿到的只是一串无用字符。

文档同时坦诚了这个机制不保护什么：你显式允许的端点会收到真实密钥，所以允许列表要收窄；部分请求形态（HTTP/2 请求体、gzip 编码体、超大定长体）不做替换，此时请求会被阻断而不是带错发出；真实值存活在宿主进程的内存里，宿主被攻陷不在防护范围内。这种把边界写清楚的文档风格，本身就值得加分。

## AI Agent 场景的针对性设计

项目把自己定位为"agent-ready"，配套做得比较完整：

- **Agent Skills**：安装 [superradcompany/skills](https://github.com/superradcompany/skills) 后，Claude Code、Cursor、Codex、Gemini CLI、GitHub Copilot 等编码 Agent 都学会了使用 microsandbox
- **MCP server**：[microsandbox-mcp](https://github.com/superradcompany/microsandbox-mcp) 让任何兼容 MCP（模型上下文协议）的 Agent 通过结构化工具调用管理沙箱生命周期、执行命令、访问文件系统
- **嵌入友好**：SDK 以子进程启动 VM，不要求先架起服务器或常驻 daemon
- **长驻会话**：detached 模式适合需要跨多轮对话存活的 Agent 工作区

README 列出的使用方也能佐证定位：Vercel 的 Eve、Chaitin 的 agent-compose、LlamaIndex 的 sandboxed-lit 等十个项目已在生产中使用。

## 适用边界

- **适合**：需要跑不可信代码的 AI Agent 平台、插件沙箱、CI 构建隔离、开发环境隔离、爬虫与自动化。
- **不适合**：如果你的负载完全可信、只需要进程隔离，容器可能更轻；如果你需要全功能 VM（GUI，图形用户界面、完整设备模拟），microVM 的极简设计反而不够。
- **注意**：beta 阶段，breaking changes 预期存在；macOS 需要 Apple Silicon（Intel Mac 即使走 Rosetta 也不支持），Linux 需要 KVM，老硬件跑不了。

## 自检与排障

官方为三个平台各写了一份排障文档，共同的第一步都是：

```sh
msb doctor    # 本地环境自检
```

两个高频错误场景：

- **Linux 上启动失败且报 KVM 相关错误**：先确认 `/dev/kvm` 存在且当前用户可读写（`ls -l /dev/kvm` 检查权限），再确认 kvm 内核模块已加载（Intel 主机通常是 `kvm_intel`，AMD 是 `kvm_amd`）。
- **macOS 上找不到命令或行为异常**：`uname -m` 应输出 `arm64`；若输出 `x86_64`，说明终端跑在 Rosetta 下，而 Rosetta 不能让 Intel 环境支持本地沙箱。运行时根目录在 `~/.microsandbox`，`which msb` 可以确认是否在用旧版本二进制。

## 常见问题 FAQ

**Intel Mac 能用吗？** 不能。本地运行时只支持 Apple Silicon，Rosetta 模拟不算数。

**第一次启动为什么慢？** 首次 `create()` 会拉取 OCI 镜像，耗时取决于网络；镜像缓存后，后续启动才进入 100 毫秒级。

**和 Docker 是什么关系？** 工作流相似：都围绕镜像、命令与数据卷展开，但隔离层不同：Docker 共享宿主内核，microsandbox 每个沙箱是独立 microVM。官方示例里甚至支持"沙箱里跑 Docker"——用 microVM 包住 Docker，避开宿主 daemon。

**密钥绝对安全吗？** 不是绝对，是有精确边界：密钥不会泄漏给允许列表之外的 host，但允许列表内的端点会收到真实值；宿主进程被攻陷也不在防护范围内。

## 动手练习

1. 安装 CLI 后运行 `msb run python -- python3 -c "print('hi')"`，观察镜像拉取与第二次运行的耗时差异。
2. 用 `msb create --name dev python` 建一个命名沙箱，练习 `exec` / `stop` / `start` / `rm` 全生命周期。
3. 在自己的语言里跑通官方 SDK 示例，然后加上 `allowed_hosts` 限制，验证沙箱内访问其他域名会被阻断。

## 进阶方向

- 读 [docs/security](https://github.com/superradcompany/microsandbox/tree/main/docs/security) 的 isolation、network、hardening 三篇，理解 DNS pin 与 SNI 校验的完整设计
- 试官方示例里的 Warm Workers（快照工具链后启动干净 worker）和 GitHub Actions Runner（每个 job 一个一次性 microVM）
- 对比 Firecracker、Kata Containers 等同类 microVM 方案，关注启动路径与镜像格式的差异

## 参考文献

1. microsandbox 仓库与 README：https://github.com/superradcompany/microsandbox
2. 官方文档（SDK / CLI / 安全模型 / 排障）：https://docs.microsandbox.dev
3. 密钥机制说明：仓库内 `docs/security/secrets.mdx`
4. 底层依赖 libkrun：https://github.com/containers/libkrun
5. Agent Skills：https://github.com/superradcompany/skills ；MCP server：https://github.com/superradcompany/microsandbox-mcp
