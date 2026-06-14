---
title: "Acton：TON 智能合约全生命周期开发工具链"
date: "2026-05-14T12:47:00+08:00"
slug: "acton-ton-smart-contract-rust-toolkit"
description: "Acton 是 TON 官方推出的全功能智能合约开发工具链，基于 Rust 语言编写，覆盖项目脚手架、编译、测试、脚本、钱包操作、网络部署、形式化验证和调试等合约全生命周期环节，是 TON 生态目前最完整的开发基础设施。"
draft: false
categories: ["技术笔记"]
tags: ["TON", "智能合约", "Rust", "区块链开发", "Web3"]
---

## 项目概览

Acton 是 ton-blockchain 组织推出的 TON 智能合约全生命周期开发工具链，使用 Rust 编写，GitHub 今日新增约 18 星。TON（The Open Network）是由 Telegram 团队设计的区块链项目，其智能合约使用 FunC 语言（类 C 语法）编写，运行在 TON Virtual Machine（TVM）上。Acton 将这一生态中原本分散在多个工具中的能力统一到了一条 CLI 命令下。

对于 TON 智能合约开发者来说，Acton 的关键价值在于消除工具链碎片化问题：不需要同时管理 `func`（FunC 编译器）、`fift`（TVM 字节码工具）、`tonos-cli`（钱包操作）和第三方测试框架，而是通过统一的 `acton` 命令行工具完成从创建项目到部署上线的全部流程。

## 核心能力

**全生命周期覆盖：** Acton 是真正的 all-in-one 工具链，一条 CLI 贯穿以下环节：

- `acton new`：项目脚手架创建，支持 FunC 合约和 Tact 合约两种模板（Tact 是 TON 上的高级合约语言，编译到 FunC）
- `acton build`：编译 FunC 或 Tact 源码，生成 `.tvc` 字节码文件
- `acton test`：Rust 原生测试运行器，支持 fork 模式（模拟 TON 区块链状态）、gas 快照、覆盖率统计、变异测试（mutation testing）和模糊测试
- `acton script`：运行合约脚本，用于调用合约方法或执行部署前置操作
- `acton deploy`：将合约部署到指定网络（testnet 或 mainnet）
- `acton verify`：在 TON 区块链浏览器上执行合约源码验证
- `acton lint` / `acton fmt`：代码检查和格式化
- `acton debug`：断点调试支持，配合浏览器版测试 UI 查看调用栈和日志

**原生性能：** 工具链本身和测试运行时均由 Rust 实现，相比基于 Node.js 或 Python 的旧方案，在大规模测试场景下有显著的速度优势。

**Tolk 工作流：** Acton 原生支持 Tolk——TON 生态的另一种合约开发语言（类 Rust 语法）。内置的 Tolk 支持包括语法高亮配置、编译器集成和测试框架对接。对于已在使用 Tolk 的团队，Acton 提供了无需切换工具的直接支持。

**dApp 开发支持：** Acton 自动生成 TypeScript 绑定文件，配合 `acton script` 可以快速编写与合约交互的前端脚本。对于需要前端 + 合约协同开发的 dApp 项目，合约接口的类型安全在 TS 层得到原生保证。

**浏览器版测试 UI：** `acton test --ui` 会启动一个本地 Web 页面，展示失败的测试用例、调用轨迹（trace）和详细的日志输出。这个功能在调试复杂合约逻辑时比命令行输出更直观。

## 快速上手

```bash
# 安装（需要 Rust 1.70+）
cargo install acton

# 创建新项目（FunC 模板）
acton new my_contract --template func
cd my_contract

# 查看项目结构
# ├── sources/
# │   └── contracts/
# │       └── main.fc      # FunC 合约源码
# ├── tests/
# │   └── main.spec.ts     # 测试文件
# └── Acton.toml          # 项目配置

# 编译合约
acton build

# 运行测试
acton test

# 部署到 testnet
acton deploy --network testnet
```

## FunC 与 Tact

TON 智能合约主要有两种开发语言：

**FunC**（Functional Communicating）是 TON 官方设计的低层合约语言，语法接近 C，需要开发者手动管理栈（stack）操作，适合对 gas 消耗和执行效率有精细控制需求的场景。

**Tact** 是建立在 FunC 之上的高级语言，语法更接近 TypeScript/Rust，支持结构体、接口和面向对象模式，编译到 FunC 后部署到 TVM。Tact 让合约开发体验更接近现代 Web2 开发，同时保留了 Tact-first 的工作流支持。

Acton 对两种语言都提供了一等公民支持，选择哪种取决于团队背景和项目对精细控制的需求。

## 适用场景

- TON 智能合约的完整开发流程管理
- 需要快速搭建合约原型并测试的团队
- Tact/FunC 合约的形式化验证和 linting
- dApp 前端 TypeScript 绑定自动生成
- TON 测试网/主网的合约部署与运维

## 总结

Acton 是 TON 生态走向成熟开发工具链的重要一步。它将过去分散在多个工具和脚本中的 TON 合约开发流程统一为一条 Rust 原生的 CLI，大幅降低了入门门槛，同时通过 Rust 的性能和类型安全为大型项目提供了可扩展的基础设施。对于任何认真投入 TON 合约开发的团队，Acton 是目前最值得优先采用的开发工具。