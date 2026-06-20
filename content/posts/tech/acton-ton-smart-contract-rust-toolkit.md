---
title: "Acton：TON 智能合约全生命周期开发工具链"
date: "2026-05-14T12:47:00+08:00"
slug: "acton-ton-smart-contract-rust-toolkit"
description: "Acton 是 TON 官方推出的全功能智能合约开发工具链，基于 Rust 语言编写，覆盖项目脚手架、编译、测试、脚本、钱包操作、网络部署、形式化验证和调试等合约全生命周期环节，是 TON 生态目前最完整的开发基础设施。"
draft: false
categories: ["技术笔记"]
tags: ["TON", "智能合约", "Rust", "区块链开发", "Web3"]
---

# Acton：TON 智能合约全生命周期开发工具链

## 学习目标

完成本文阅读后，你将能够：

1. 说出 Acton 解决的 TON 工具链碎片化问题及其能力边界
2. 使用 `acton new`/`build`/`test`/`deploy`/`verify` 完成一个合约从创建到链上验证的完整生命周期
3. 区分 FunC、Tact、Tolk 三种 TON 合约语言的适用场景
4. 判断现有项目是否应该迁移到 Acton，并给出迁移的优先顺序

## 目录

- [项目概览](#项目概览)
- [核心能力](#核心能力)
  - [项目创建](#项目创建)
  - [编译测试](#编译测试)
  - [部署运维](#部署运维)
  - [语言与生态支持](#语言与生态支持)
- [快速上手](#快速上手)
- [任务流案例：NFT 合约从创建到验证](#任务流案例nft-合约从创建到验证)
- [FunC、Tact 与 Tolk](#func-tact-与-tolk)
- [适用场景与采用顺序](#适用场景与采用顺序)
- [决策建议](#决策建议)

## 项目概览

Acton 是 ton-blockchain 组织推出的 TON 智能合约全生命周期开发工具链，使用 Rust 编写。TON（The Open Network）由 Telegram 团队发起，现由 TON Foundation 维护；其智能合约使用 FunC 语言（TON 官方低层合约语言，类 C 语法）编写，运行在 TON Virtual Machine（TVM，TON 虚拟机）上。

TON 合约开发长期存在工具链碎片化问题：开发者需要同时管理 `func`（FunC 编译器）、`fift`（TVM 字节码工具）、`tonos-cli`（钱包操作）和多个第三方测试框架，这些工具的命令风格、配置文件和错误信息彼此不兼容。Acton 把这些能力统一到一条 `acton` CLI 命令下，覆盖从项目脚手架到链上验证的全部环节。

Acton 的 CLI 命令按职责分为四组：

| 分组 | 命令 | 职责 |
|------|------|------|
| 项目创建 | `acton new` | 脚手架与模板 |
| 编译测试 | `acton build`、`acton test`、`acton lint`、`acton fmt`、`acton debug` | 编译、测试、检查、调试 |
| 部署运维 | `acton script`、`acton deploy`、`acton verify` | 脚本执行、网络部署、源码验证 |
| 语言与生态支持 | FunC、Tact、Tolk、TypeScript 绑定 | 多语言与 dApp 支持 |

## 核心能力

### 项目创建

- `acton new`：项目脚手架创建，支持 FunC 合约和 Tact 合约两种模板（Tact 是 TON 上的高级合约语言，编译到 FunC）

### 编译测试

- `acton build`：编译 FunC 或 Tact 源码，生成 `.tvc`（TVM 字节码文件）
- `acton test`：Rust 原生测试运行器，支持 fork 模式（模拟 TON 区块链状态）、gas（链上执行燃料费）快照、覆盖率统计、mutation testing（变异测试）和模糊测试
- `acton lint` / `acton fmt`：代码检查和格式化
- `acton debug`：断点调试支持，配合浏览器版测试 UI 查看调用栈和日志

`acton test --ui` 会启动一个本地 Web 页面，展示失败的测试用例、调用轨迹（trace）和详细日志。调试复杂合约逻辑时比命令行输出更直观。

### 部署运维

- `acton script`：运行合约脚本，用于调用合约方法或执行部署前置操作
- `acton deploy`：将合约部署到指定网络（testnet（测试网）或 mainnet（主网））
- `acton verify`：在 TON 区块链浏览器上执行合约源码验证

### 语言与生态支持

**Rust 原生实现：** 工具链和测试运行时均由 Rust 实现。相比基于 Node.js 或 Python 的旧方案，Rust 原生方案在测试用例数量增大时编译和执行耗时的增长更平缓。

**Tolk 工作流：** Acton 原生支持 Tolk——TON 生态的另一种合约开发语言（类 Rust 语法）。内置支持包括语法高亮配置、编译器集成和测试框架对接。已在使用 Tolk 的团队无需切换工具。

**dApp（去中心化应用）开发支持：** Acton 自动生成 TypeScript 绑定文件，配合 `acton script` 可以快速编写与合约交互的前端脚本。前端与合约协同开发时，合约接口的类型安全在 TS 层得到保证。

## 快速上手

```bash
# 安装（需要 Rust 1.70+）
cargo install acton

# 创建新项目（FunC 模板）
acton new my_contract --template func
cd my_contract

# 项目结构
# ├── sources/
# │   └── contracts/
# │       └── main.fc    # FunC 合约源码
# ├── tests/
# │   └── main.rs        # Rust 原生测试文件
# └── Acton.toml         # 项目配置

# 编译合约
acton build

# 运行测试
acton test

# 部署到 testnet
acton deploy --network testnet
```

## 任务流案例：NFT 合约从创建到验证

下面以一个 NFT（Non-Fungible Token，非同质化代币）合集合约为例，展示一次完整任务如何流过 Acton 的各个子系统。NFT 合约涉及铸造、转账和元数据查询，能覆盖大部分常用合约路径。

### 1. 创建项目

```bash
acton new nft_collection --template tact
cd nft_collection
```

选择 Tact 模板的原因是 NFT 合约涉及结构体和接口，Tact 的面向对象语法比 FunC 的栈操作更适合表达这类抽象。

### 2. 编写合约

在 `sources/contracts/nft_collection.tact` 中定义 `NFTCollection` 合约，包含 `mint`、`transfer`、`get_item_info` 三个方法。

### 3. 编译

```bash
acton build
```

Acton 调用 Tact 编译器，先将 `.tact` 编译为 FunC，再编译为 `.tvc` 字节码。产物路径为 `build/nft_collection.tvc`。

### 4. 测试

在 `tests/nft_collection.rs` 中编写测试，覆盖铸造成功、重复铸造失败、转账权限校验等场景。运行测试：

```bash
acton test
```

测试运行器会记录每个操作的 gas 消耗。NFT 合约对 gas 敏感，因为单次铸造可能触发多次存储写入，gas 快照便于在后续修改中检测回归。

### 5. 部署到测试网

```bash
acton deploy --network testnet
```

Acton 读取 `Acton.toml` 中的钱包配置，签名并广播部署交易。部署成功后输出合约地址。

### 6. 链上验证

```bash
acton verify
```

`acton verify` 把源码和编译参数提交到 TON 区块链浏览器，浏览器重新编译并比对链上字节码。验证通过后，合约地址在浏览器中会显示源码链接，用户可以核对合约逻辑。

## FunC、Tact 与 Tolk

TON 智能合约主要有三种开发语言，Acton 对三者都提供支持：

**FunC** 是 TON 官方低层合约语言，语法接近 C，需要开发者手动管理栈（stack）操作，适合对 gas 消耗和执行效率有精细控制需求的场景。

**Tact** 是建立在 FunC 之上的高级语言，语法更接近 TypeScript/Rust，支持结构体、接口和面向对象模式，编译到 FunC 后部署到 TVM。Tact 让合约开发体验更接近现代 Web2 开发。

**Tolk** 是 TON 生态较新的合约语言，类 Rust 语法，定位介于 FunC 和 Tact 之间，兼顾表达力和执行效率。

选择哪种语言取决于团队背景和项目对精细控制的需求：追求极致 gas 优化选 FunC，追求开发效率选 Tact，习惯 Rust 语法选 Tolk。

## 适用场景与采用顺序

### 适用场景

- TON 智能合约的完整开发流程管理
- 需要快速搭建合约原型并测试的团队
- Tact/FunC 合约的形式化验证和 linting
- dApp 前端 TypeScript 绑定自动生成
- TON 测试网/主网的合约部署与运维

### 采用顺序

**新项目：** 直接使用 `acton new` 创建项目，从第一天就跑通完整工具链，避免后续迁移成本。

**老项目迁移：** 建议按以下顺序逐步替换：

1. 先用 `acton build` 替换 `func`/`fift`，验证编译产物一致
2. 再用 `acton test` 替换原有测试框架，先跑通现有用例，再逐步引入 fork 模式和 gas 快照
3. 最后用 `acton deploy` 和 `acton verify` 替换部署脚本，统一运维入口

## 决策建议

Acton 适合以下团队优先采用：

- 正在启动新 TON 项目的团队——直接用 Acton 可以省去工具选型成本
- 需要在 testnet 和 mainnet 之间频繁切换的团队——`acton deploy --network` 统一了网络切换
- 对 gas 优化有强需求的团队——`acton test` 的 gas 快照提供回归检测

以下团队可以暂缓采用：

- 已有成熟 CI/CD 流程且工具链稳定的团队——迁移成本可能高于收益
- 仅使用 Tact 单一语言且不涉及部署的团队——Tact 自带工具链已能满足基本需求
