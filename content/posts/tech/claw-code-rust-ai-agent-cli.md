---
title: "Claw Code: Rust 实现的开源 AI Agent CLI 工具"
date: "2026-04-30T20:00:00+08:00"
slug: "claw-code-rust-ai-agent-cli"
description: "Claw Code 是 ultraworkers 团队开源的 Rust 实现的 claw CLI agent harness，提供跨平台 AI Agent 开发框架，支持 Anthropic/OpenAI API、多工具调用、会话管理和 MCP 协议，可通过容器化工作流快速部署。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Rust", "Claude", "MCP协议", "命令行工具"]
---

## 项目概览

[Claw Code](https://github.com/ultraworkers/claw-code) 是 ultraworkers 团队开源的 AI Agent（人工智能代理）开发框架，采用 Rust 语言实现，是 `claw` CLI agent harness 的公开参考实现。截至 2026 年初，该项目已在 GitHub 获得接近 19 万颗星，成为 AI Agent 开源领域最受关注的 CLI 工具之一。

项目的核心定位是：**为开发者提供一个生产级的 Rust CLI 运行环境，用于构建、运行和调试多工具调用的 AI Agent**。canonical 实现位于仓库的 `rust/` 目录，是当前真正的代码基线。

### 关键背景：不是 `cargo install claw-code`

> ⚠️ **不要执行 `cargo install claw-code`！** crates.io 上的 `claw-code` 是一个早已废弃的空壳包，只会打印 `"claw-code has been renamed to agent-code"`，不会安装真正的 claw 工具。正确的做法是从本仓库源码构建，或直接安装上游二进制 `cargo install agent-code`。

---

## 快速开始

### 环境要求

- **Rust**（建议通过 [rustup.rs](https://rustup.rs/) 安装）
- **API Key**：Claw Code 支持多后端，核心是 `ANTHROPIC_API_KEY`（Anthropic API 密钥，Claude 订阅账号的登录态**不支持**作为认证凭证）

### 构建步骤

```bash
# 1. 克隆并构建整个 Rust workspace
git clone https://github.com/ultraworkers/claw-code
cd claw-code/rust
cargo build --workspace

# 2. 设置 API Key
export ANTHROPIC_API_KEY="sk-ant-..."

# 3. 运行健康检查（首次使用必做）
./target/debug/claw doctor

# 4. 运行第一个 Prompt
./target/debug/claw prompt "say hello"
```

### Windows（PowerShell）注意事项

Windows 下二进制文件名为 `claw.exe`，路径分隔符也不同：

```powershell
# PowerShell 中
$env:ANTHROPIC_API_KEY = "sk-ant-..."
.\rust\target\debug\claw.exe doctor
.\rust\target\debug\claw.exe prompt "say hello"
```

Windows 平台首个常见问题是 Rust 未正确安装，验证方式：

```powershell
cargo --version
```

---

## 二进制位置与 PATH 配置

`cargo build --workspace` 完成后，二进制**不会**自动安装到系统 PATH，需手动定位：

| 构建类型 | macOS / Linux | Windows |
|----------|--------------|---------|
| Debug（默认） | `rust/target/debug/claw` | `rust/target/debug/claw.exe` |
| Release | `rust/target/release/claw` | `rust/target/release/claw.exe` |

### 方式一：软链接（Linux/macOS）

```bash
ln -s $(pwd)/rust/target/debug/claw /usr/local/bin/claw
claw --help   # 全局可用
```

### 方式二：`cargo install --path`

```bash
# 从 rust/ 目录执行
cargo install --path . --force
claw --help   # 安装到 ~/.cargo/bin/
```

---

## 核心架构

Claw Code 的代码组织如下：

```
claw-code/
├── rust/                    # canonical Rust workspace + claw CLI 二进制
│   ├── src/
│   └── Cargo.toml
├── src/ + tests/            # 配套 Python 参考工作区（非主运行时）
├── USAGE.md                 # 任务导向的使用指南（推荐优先阅读）
├── PARITY.md                # Rust 移植进度与迁移说明
├── ROADMAP.md               # 路线图与待办事项
├── PHILOSOPHY.md            # 项目定位与设计哲学
└── docs/container.md        # 容器优先工作流文档
```

### 文档地图

| 文档 | 用途 |
|------|------|
| [USAGE.md](https://github.com/ultraworkers/claw-code/blob/main/USAGE.md) | CLI 命令详解、认证、会话、配置 |
| [rust/README.md](https://github.com/ultraworkers/claw-code/blob/main/rust/README.md) | crate 层级结构、CLI surface、特性列表 |
| [PARITY.md](https://github.com/ultraworkers/claw-code/blob/main/PARITY.md) | Rust 移植的当前进度与已知差异 |
| [ROADMAP.md](https://github.com/ultraworkers/claw-code/blob/main/ROADMAP.md) | ACP/Zed 支持等活跃功能规划 |
| [rust/MOCK_PARITY_HARNESS.md](https://github.com/ultraworkers/claw-code/blob/main/rust/MOCK_PARITY_HARNESS.md) | 确定性 Mock 服务测试框架说明 |

---

## 会话管理与工具生态

Claw Code 支持会话持久化和多工具调用，这是其区别于简单 CLI chat 的关键能力。具体功能包括：

- **会话管理**：保存和恢复多轮对话上下文
- **多后端兼容**：Anthropic（Claude）、OpenAI 等 API 可切换
- **MCP 协议支持**：通过 Model Context Protocol 连接外部工具和数据源
- **容器化部署**：`docs/container.md` 提供了 Docker 环境下的标准化部署方案

ACP（Agent Communication Protocol）和 Zed 集成的完整支持仍在路线图中，参见 [ROADMAP.md](https://github.com/ultraworkers/claw-code/blob/main/ROADMAP.md)。

---

## 适用场景与优势

### 适合使用 Claw Code 的场景

1. **本地 AI Agent 原型开发**：Rust 实现带来优秀的启动速度和低内存占用
2. **需要私有化部署的 Agent 应用**：不依赖第三方云服务，API Key 自持
3. **跨平台 CLI 工具链构建**：macOS、Linux、Windows 全平台支持
4. **调试和测试 AI 工具调用**：内置 `claw doctor` 健康检查和 Mock 测试框架

### 优势

- **开源透明**：MIT 许可，代码完全开放，不存在厂商锁定
- **Rust 性能**：原生二进制，无运行时依赖，适合嵌入式或服务端长期运行
- **活跃生态**：配套工具链包括 clawhip、oh-my-claudecode、oh-my-openagent 等社区项目

---

## 常见问题

### Q: `claw doctor` 报告 API Key 无效怎么办？

确认使用的是 **Anthropic API Key**（`ANTHROPIC_API_KEY`），而非 Claude 网页版的登录 Session。API Key 需要在 [Anthropic Console](https://console.anthropic.com/) 申请。

### Q: 构建速度太慢怎么办？

默认 Debug 模式编译较快，但若追求运行时性能，可使用 Release 模式（编译时间约 5-10 分钟）：

```bash
cargo build --workspace --release
```

### Q: `claw` 命令找不到？

二进制不在 PATH 中。使用完整路径运行，或按前述方式创建软链接：

```bash
./rust/target/debug/claw --help
```

### Q: 支持 Windows 吗？

支持。推荐使用 PowerShell，Git Bash 和 WSL 也是可行替代方案。唯一需要注意的是路径和后缀名差异（`.exe`）。

---

## 总结

Claw Code 代表了开源 AI Agent 工具链的一个重要方向——用 Rust 实现生产级 CLI harness，兼顾性能和跨平台能力。其设计思路强调本地化、工具化和可审计性，适合开发者构建自己的 AI Agent 工作流。

如果你是 AI 应用开发者，建议从 `claw doctor` 开始验证环境，再结合 USAGE.md 深入探索会话管理和 MCP 集成能力。项目仍处于活跃开发阶段，ACP/Zed 完整支持的进展值得持续关注。

**相关链接：**
- GitHub: https://github.com/ultraworkers/claw-code
- UltraWorkers Discord: https://discord.gg/5TUQKqFWd

---

*本文基于 ultraworkers/claw-code 公开仓库信息撰写，主要功能描述以 README 和官方文档为准。*