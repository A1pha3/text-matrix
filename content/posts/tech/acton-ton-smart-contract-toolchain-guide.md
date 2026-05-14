---
title: "Acton：TON智能合约开发一站式工具链完全指南"
date: "2026-05-14T10:55:00+08:00"
slug: "acton-ton-smart-contract-toolchain-guide"
description: "Acton是由TON官方提供的Rust编写智能合约开发工具链，涵盖项目脚手架、构建、测试、调试、部署、验证全生命周期，支持Tolk工作流、内置测试工具、Fork模式、Gas快照、覆盖率分析和变异测试。提供macOS和Linux跨平台二进制安装，是TON生态最完整的开发者工具。"
draft: false
categories: ["技术笔记"]
tags: ["TON", "智能合约", "Rust", "区块链开发", "FunC"]
---

# Acton：TON智能合约开发一站式工具链完全指南

**Acton**（[ton-blockchain/acton](https://github.com/ton-blockchain/acton)）是 TON 官方推出的 Rust 编写的智能合约开发工具链，覆盖从项目创建、编译、测试、调试到部署的完整生命周期。它将原本分散在多个工具（FunC 编译器、Tolk、TON OS 等）中的能力整合为一个统一的 CLI，极大降低了 TON 智能合约的开发门槛。

核心特点：
- **单一 CLI**：一个命令完成合约全生命周期
- **Rust 原生性能**：工具链和测试运行时均使用 Rust，编译和测试速度极快
- **Tolk 工作流**：原生支持 Tolk（TON 的智能合约语言）开发
- **丰富的测试能力**：Fork 模式、Gas 快照、覆盖率、变异测试
- **浏览器测试 UI**：可视化查看失败的测试、trace、log 和覆盖率

## 与旧工具链的对比

| 阶段 | 旧工具链 | Acton |
|------|----------|-------|
| 项目创建 | `ton-dev-cli` 或手动 | `acton new` |
| 编译 | `func` 编译器 | `acton build` |
| 测试 | 手动配置 testnet | `acton test`（内置） |
| 调试 | `ton-local-vm` | `acton debug`（内置） |
| 部署 | 多工具组合 | `acton deploy` |
| 验证 | 第三方工具 | `acton verify` |

## 安装

### 官方安装脚本（推荐）

```bash
curl -LsSf https://github.com/ton-blockchain/acton/releases/latest/download/acton-installer.sh | sh
```

### 手动下载

从 [GitHub Releases](https://github.com/ton-blockchain/acton/releases/latest) 下载对应平台压缩包：

| 平台 | 架构 | 下载 |
|------|------|------|
| macOS | ARM64 | `acton-aarch64-apple-darwin.tar.gz` |
| macOS | x86_64 | `acton-x86_64-apple-darwin.tar.gz` |
| Linux | x86_64 | `acton-x86_64-unknown-linux-gnu.tar.gz` |
| Linux | ARM64 | `acton-aarch64-unknown-linux-gnu.tar.gz` |

```bash
# 解压并加入 PATH
tar xzf acton-*.tar.gz
sudo mv acton /usr/local/bin/
acton --version
```

### Docker

```bash
# 查看版本
docker run --rm ghcr.io/ton-blockchain/acton:latest --version

# 在当前目录运行构建
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace \
  ghcr.io/ton-blockchain/acton:latest \
  build
```

## 快速上手：从零到 Testnet

### 1. 创建项目

```bash
acton new my-token --template token
cd my-token
```

生成的项目结构：

```
my-token/
├── src/
│   └── contract.fc     # FunC/Tolk 合约源码
├── tests/
│   └── contract.spec.ts # 测试用例
├── scripts/
│   └── deploy.ts       # 部署脚本
└── Acton.toml          # 项目配置
```

### 2. 编译合约

```bash
acton build
```

编译产物输出到 `build/` 目录，生成 `.cell` 文件（TVM 二进制格式）。

### 3. 编写测试

`tests/contract.spec.ts`：

```typescript
import { test, it, deploy, send } from '@ton/contracts-test';

test('Token: deploy and check balance', async () => {
  // 部署合约
  const contract = await deploy('build/token.cell');

  // 调用 get_balance 方法
  const balance = await contract.invoke('get_balance');

  // 断言
  it('should have zero initial balance', async () => {
    expect(balance).toEqual(0n);
  });
});
```

### 4. 运行测试

```bash
acton test

# 查看详细输出
acton test --verbose

# 生成覆盖率报告
acton test --coverage
```

### 5. 本地调试

```bash
acton debug tests/contract.spec.ts --breakpoint src/contract.fc:42
```

### 6. 部署到 Testnet

```bash
# 配置钱包（助记词导入）
acton wallet import

# 部署
acton deploy --network testnet

# 指定手续费上限
acton deploy --network testnet --gas-limit 1.5
```

## 高级功能

### Fork 模式

在测试网络中 Fork 主网状态，快速验证合约与真实数据的交互：

```bash
acton test --fork mainnet --block 34567890
```

### Gas 快照

记录测试中每次执行的 Gas 消耗，detect 回归：

```bash
acton test --gas-snapshot tests/snapshot.json
```

### 覆盖率分析

```bash
acton test --coverage --coverage-format html
# 输出到 coverage/index.html
```

### 变异测试（Mutation Testing）

通过"注入 bug"验证测试套件的质量：

```bash
acton test --mutation
```

### 验证工具

将已部署合约的代码与本地源码进行比对验证：

```bash
acton verify --network mainnet --address EQCD...your-address...
```

## TypeScript 包装器（dApp 开发）

Acton 自动为每个合约生成 TypeScript 客户端：

```bash
acton build --ts-wrapper
```

生成 `wrappers/Token.ts`：

```typescript
import { Address, beginCell, Contract, contractAddress } from 'ton-core';
import { Token } from './wrappers/Token';

// 部署后获取合约实例
const token = Contract.fromAddress(Address.parse('EQCD...'));

// 调用合约方法
const balance = await token.invoke('get_balance', { owner: myAddress });
console.log(balance);
```

## 项目模板

```bash
# 查看可用模板
acton new --list-templates

# 创建不同类型项目
acton new my-nft --template nft
acton new my-gaming --template game
acton new my-dao --template dao
```

## 适用场景

- **TON 生态开发者**：替代原有的多工具组合，提升开发体验
- **安全审计**：内置覆盖率+变异测试，是合约审计的利器
- **dApp 前端团队**：自动生成的 TypeScript 包装器简化前端集成
- **学习 TON 合约开发**：一个 CLI 搞定所有，降低学习曲线

## 平台支持说明

- **一级支持平台**：macOS（ARM64 + x86_64）、Linux GNU（x86_64 + ARM64）
- **不支持**：原生 Windows（需通过 WSL2 + Ubuntu）
- **Beta**：Trunk 构建、源码构建

## 总结

Acton 将 TON 智能合约开发的全流程整合为一套工具链，显著降低了开发复杂度和工具学习成本。其 Rust 原生实现保证了性能，而 Fork 模式、Gas 快照、覆盖率分析等高级测试功能则让它成为专业合约开发的利器。对于任何想要进入 TON 生态的开发者，Acton 都是绕不开的第一站。

官方文档：[https://ton-blockchain.github.io/acton/docs/welcome](https://ton-blockchain.github.io/acton/docs/welcome)