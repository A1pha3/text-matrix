---
title: "microsandbox：100 毫秒内启动的本地微型虚拟机"
date: 2026-08-19T03:26:14+08:00
slug: "microsandbox-local-microvm-runtime"
github_repo: "superradcompany/microsandbox"
source_key: "gh:superradcompany/microsandbox"
description: "microsandbox 是一个 Rust 编写的本地优先 microVM 运行时，用 OCI 标准镜像在 100 毫秒内启动隔离虚拟机，支持 AI Agent、用户代码、CI 等不可信负载，提供 Rust、Python、TypeScript、Go 多语言 SDK。"
draft: false
categories: ["技术笔记"]
tags: ["microVM", "Rust", "容器", "隔离", "AI Agent"]
---

# microsandbox：100 毫秒内启动的本地微型虚拟机

AI Agent 要跑用户代码、插件要执行第三方脚本、CI 要构建不可信产物——这些场景都需要隔离，但传统虚拟机太重、普通容器隔离又太薄。microsandbox 站在两者之间：**一个本地优先的 microVM 运行时，启动速度在 100 毫秒级**，用起来却像 Docker 一样熟悉。

## 一分钟总览

microsandbox 由 superradcompany 开发，Rust 编写，Apache 2.0 协议。它把**不可信负载**（AI Agent、用户代码、插件、CI 任务、开发环境、爬虫、自动化）跑进快速启动的本地 microVM 里，提供硬件级隔离，同时保持 Docker 风格的工作流。

```
npx microsandbox run debian      # 一条命令启动一个 microVM
msb run debian                   # 安装 CLI 后的等价写法
```

关键特性：

- **硬件级隔离**：microVM 技术，隔离边界在硬件层而非进程层
- **跨平台**：Linux（KVM）、macOS（Apple Silicon）、Windows（WHP）
- **OCI 兼容**：直接跑 Docker Hub、GHCR 或任意 OCI 仓库的标准容器镜像
- **秒级启动**：平均启动时间低于 100 毫秒
- **可嵌入**：在代码里直接拉起 VM，无需常驻 daemon
- **秘密不泄漏**：不可利用的秘密密钥永远不进入 VM

## 为什么是"microVM"而不是"容器"

容器共享宿主内核，隔离靠 namespace + cgroup，同一个内核漏洞可能同时打穿所有容器。microVM 则给每个沙箱一个**独立、最小化的虚拟机**，自己的内核、自己的内存布局，隔离边界是真正的硬件虚拟化。

microsandbox 用 OCI 标准镜像做输入——也就是说，你熟悉的 `python:3.12`、`debian` 这些镜像直接就能用，不用重新打包。它把"虚拟机的强隔离"和"镜像生态的熟悉度"结合在了一起。

## 上手：一条命令与多语言 SDK

### CLI

```sh
curl -fsSL https://install.microsandbox.dev | sh    # macOS / Linux
msb run debian
```

底层要求：macOS 需要 Apple Silicon，Linux 需要 KVM，Windows 需要 WHP。**项目仍是 beta**，README 明确提示会有 breaking changes。

### SDK：在代码里嵌一个沙箱

microsandbox 的 SDK 是它的真正卖点——`Sandbox::builder("...").create()` 直接以子进程方式启动一个 microVM，不需要任何基础设施：

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

同样提供了 **Python、TypeScript、Go、Ruby** 的 SDK，Python 版本几乎逐行对应：

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

Ruby SDK 还展示了更精细的管控——限制网络只允许特定 host 与端口，并且秘密以"只可被指定 host 访问"的方式注入：

```ruby
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

这里能看到 microsandbox 对 AI 场景的针对性设计：**允许 API 调用但拒绝横向移动**——Agent 能访问 OpenAI API，却拿不到宿主机的任意网络，密钥本身也不进 VM。

## AI Agent 场景的针对性

项目把自己定位为"agent-ready"：

- **无泄露的秘密**：密钥永不进入 VM，规避了"把密钥复制进沙箱"这条经典泄漏路径
- **长驻会话**：沙箱可分离模式运行，适合长生命周期任务
- **Agent Skills 与 MCP**：配套提供 [Agent Skills](https://github.com/superradcompany/skills) 和 [MCP server](https://github.com/superradcompany/microsandbox-mcp)，让 Agent 能自己创建沙箱
- **嵌入友好**：`Sandbox::builder(...).create()` 以子进程启动，无需设置服务器或常驻 daemon

## 适用边界

- **适合**：需要跑不可信代码的 AI Agent 平台、插件沙箱、CI 构建隔离、开发环境隔离、爬虫与自动化。
- **不适合**：如果你的负载完全可信、只需要进程隔离，容器可能更轻；如果你需要全功能 VM（GUI、完整设备模拟），microVM 的极简设计反而不够。
- **注意**：beta 阶段，breaking changes 预期存在；macOS 需要 Apple Silicon，Linux 需要 KVM，老硬件跑不了。

## 小结论

microsandbox 把一个过去很重的技术——microVM 隔离——压缩进了"100 毫秒启动 + 一条命令 + 多语言 SDK"的轻量形态。对 AI Agent 生态来说，它补上的是"Agent 需要跑不可信代码，但不想为此架设整套基础设施"的那块拼图。如果你正在给 Agent 或插件做沙箱隔离，它的 SDK 形态值得一试。
