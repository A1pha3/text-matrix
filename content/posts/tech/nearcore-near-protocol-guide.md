---
title: "NEAR Protocol 核心节点完全指南"
date: 2026-03-31T14:45:00+08:00
slug: "nearcore-near-protocol-guide"
description: "全面解析 NEAR Protocol (nearcore)：2.6k Stars 的去中心化应用平台。NEAR 是以太坊竞争对手，采用 Nightshade 分片和 PoS 共识，支持 Rust/JavaScript 智能合约开发。"
draft: false
categories: ["技术笔记"]
tags: ["NEAR Protocol", "NEAR", "nearcore", "区块链", "智能合约", "Rust", "Web3"]
---

# NEAR Protocol 核心节点完全指南

## §1 学习目标

完成本文档后，你将能够：

- ✅ 理解 NEAR Protocol 的核心定位与技术架构
- ✅ 掌握 nearcore 作为参考实现的角色与价值
- ✅ 理解 NEAR 的共识机制与分片设计
- ✅ 熟练构建和运行 nearcore 节点
- ✅ 掌握智能合约开发（Rust + TypeScript）
- ✅ 理解 NEAR 的生态工具链
- ✅ 参与网络验证（Validator）
- ✅ 为 NEAR 协议贡献代码

---

## §2 项目概述

### 2.1 什么是 NEAR Protocol？

**NEAR Protocol**（官方仓库：[near/nearcore](https://github.com/near/nearcore)）是 **NEAR 协议的参考实现**，是一个为服务器级应用和智能合约提供支持的区块链基础设施。

**官方描述**：

> NEAR's purpose is to enable community-driven innovation to benefit people around the world. NEAR provides a developer platform where developers and entrepreneurs can create apps that put users back in control of their data and assets, which is the foundation of "Open Web" movement. NEAR Protocol is an infrastructure for server-less applications and smart contracts powered by a blockchain. NEAR Protocol is built to deliver usability and scalability of modern PaaS like Firebase at fraction of the prices that blockchains like Ethereum charge.

**NEAR 的核心价值主张**：

| 价值 | 说明 |
|------|------|
| **用户数据主权** | 用户重新掌控自己的数据和资产 |
| **开发者友好** | 像 Firebase 一样易用的 PaaS 体验 |
| **低成本** | 比 Ethereum 低得多的价格 |
| **高可扩展性** | 现代化的可扩展基础设施 |
| **Open Web** | "开放网络"运动的基础设施 |

### 2.2 核心数据

```
Stars:     2,600 (2.6k)
Forks:     767
Watchers:  76
贡献者:   253 人
提交数:   9,774 次（master 分支）
分支数:   589 个
标签数:   387 个
发布版本:  247 个
最新版本:  2.10.7 (2026-03-04)
许可证:   Apache-2.0 / MIT
主要语言: Rust 88.8%, Python 8.2%, TypeScript 1.7%
```

### 2.3 NEAR 生态工具链

| 工具 | 说明 |
|------|------|
| **near-api-js** | JavaScript 客户端库，连接 NEAR 协议 |
| **near-sdk-rs** | Rust SDK，用于编写智能合约和有状态的服务器函数 |
| **near-sdk-js** | JavaScript/TypeScript SDK，用于编写智能合约 |
| **NEAR CLI** | 命令行工具，交互 NEAR 网络 |
| **NEAR Studio** | 在线 IDE，开发智能合约 |

### 2.4 相关资源

| 资源 | 链接 |
|------|------|
| 官方网站 | https://near.org |
| 开发者文档 | https://docs.near.org |
| 协议规范 | https://nomicon.io |
| GitHub | https://github.com/near |
| Discord | https://discord.com/invite/nearprotocol |
| Twitter | @NEARProtocol |
| Telegram | https://t.me/cryptonear |
| 论坛 | https://gov.near.org |
| 技术讨论 | https://near.zulipchat.com/ |

---

## §3 技术架构深度解析

### 3.1 协议架构

NEAR Protocol 是一个分片区块链，采用以下核心技术：

**共识机制**

NEAR 使用 **Proof of Stake (PoS)** 共识，通过验证者（Validator）质押 NEAR 代币来保护网络安全。

**分片设计**

NEAR 采用 **Nightshade** 分片方案：

- 将区块链状态分割成多个分片
- 每个分片由一组验证者处理
- 跨分片交易通过 receipts 机制处理

**账户模型**

NEAR 使用 **基于合约的账户模型**：

- 账户 ID 类似域名（如 alice.near）
- 账户由合约代码和存储组成
- 支持密钥对和多重签名

### 3.2 核心组件

| 组件 | 说明 |
|------|------|
| **Runtime** | 智能合约执行环境 |
| **Chain** | 区块链链式结构管理 |
| **Network** | P2P 网络通信 |
| **Consensus** | PoS 共识机制 |
| **Shardchain** | 分片链管理 |
| **Indexer** | 链上数据索引 |

### 3.3 目录结构

nearcore 仓库的目录结构如下：

| 目录 | 说明 |
|------|------|
| `.cargo` | Cargo 构建配置 |
| `.claude` | Claude 代理配置 |
| `.config` | 项目配置 |
| `.devcontainer` | 开发容器配置 |
| `.github` | GitHub Actions CI/CD |
| `benchmarks` | 性能基准测试 |
| `chain` | 区块链链式结构核心 |
| `core` | 核心运行时 |
| `debug_scripts` | 调试脚本 |
| `docker/sandbox` | Docker 沙箱环境 |
| `docs` | 文档 |
| `genesis-tools` | 创世块工具 |
| `integration-tests` | 集成测试 |
| `neard` | NEAR 守护进程主程序 |
| `nightly` | 夜间构建测试 |
| `pytest` | Python 测试 |
| `runtime` | 合约运行时 |
| `scripts` | 构建和部署脚本 |
| `test-loop-tests` | 测试循环测试 |
| `test-utils` | 测试工具 |
| `tools` | 各种工具 |
| `tracing` | 分布式追踪 |
| `utils` | 通用工具函数 |

---

## §4 构建与运行

### 4.1 环境要求

| 要求 | 版本 |
|------|------|
| Rust | 1.85+ |
| Python | 3.10+ |
| 操作系统 | Linux / macOS / Windows (WSL) |
| 内存 | 16GB+ |
| 存储 | 100GB+ SSD |

### 4.2 从源码构建

```bash
# 克隆仓库
git clone https://github.com/near/nearcore
cd nearcore

# 安装 Rust（如未安装）
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 构建发布版本
cargo build --release

# 二进制文件位于 target/release/neard
```

### 4.3 使用 Docker 运行

```bash
# 下载最新镜像
docker pull nearprotocol/nearcore:latest

# 运行本地测试节点
docker run -p 3030:3030 \
  -v ~/.near:/root/.near \
  nearprotocol/nearcore \
  neard run
```

### 4.4 连接到 NEAR 网络

**连接到主网**

```bash
# 初始化配置
neard init --network-id mainnet

# 运行节点
neard run
```

**连接到测试网**

```bash
neard init --network-id testnet
neard run
```

**连接到开发网**

```bash
neard init --network-id localnet
neard run
```

---

## §5 智能合约开发

### 5.1 Rust 智能合约

NEAR 提供 `near-sdk-rs` 用于编写 Rust 智能合约。

**项目结构**

```bash
# 创建新项目
cargo new my-contract --lib
cd my-contract

# 添加依赖
# 在 Cargo.toml 中添加
[dependencies]
near-sdk = "5.0"
near-sdk-ops = "5.0"
```

**编写合约示例**

```rust
use near_sdk::borsh::{BorshDeserialize, BorshSerialize};
use near_sdk::store::Map;
use near_sdk::{env, near_bindgen, AccountId};

#[near_bindgen]
#[derive(BorshDeserialize, BorshSerialize)]
pub struct Contract {
    pub messages: Map<String, String>,
}

impl Default for Contract {
    fn default() -> Self {
        Self {
            messages: Map::new(b"m"),
        }
    }
}

#[near_bindgen]
impl Contract {
    pub fn add_message(&mut self, key: String, value: String) {
        self.messages.insert(key, value);
    }

    pub fn get_message(&self, key: String) -> Option<String> {
        self.messages.get(&key).cloned()
    }
}
```

**编译合约**

```bash
cargo build --target wasm32-unknown-unknown --release
# 输出位于 target/wasm32-unknown-unknown/release/my_contract.wasm
```

### 5.2 JavaScript/TypeScript 智能合约

NEAR 提供 `near-sdk-js` 用于编写 JavaScript/TypeScript 智能合约。

**安装**

```bash
npm install near-sdk-js
```

**编写合约示例**

```javascript
import { NearBindgen, call, view } from "near-sdk-js";

@NearBindgen({})
class Contract {
  constructor() {
    this.messages = {};
  }

  @call
  addMessage({ key, value }) {
    this.messages[key] = value;
    return { success: true };
  }

  @view
  getMessage({ key }) {
    return this.messages[key] || null;
  }
}
```

**编译合约**

```bash
npx near-sdk-js build ./contract.js
# 输出: ./contract.wasm
```

### 5.3 部署合约

```bash
# 部署 Rust 合约
near deploy <account-id> ./target/wasm32-unknown-unknown/release/my_contract.wasm

# 部署 JS 合约
near deploy <account-id> ./contract.wasm
```

---

## §6 NEAR CLI 使用

### 6.1 安装

```bash
npm install -g near-cli
```

### 6.2 登录认证

```bash
# 生成钱包并登录
near login

# 或使用密钥文件
near generate-key <account-id>
```

### 6.3 常用命令

**账户操作**

```bash
# 创建子账户
near create-account <sub-account>.<parent-account> --masterAccount <parent-account>

# 查看账户信息
near state <account-id>

# 删除账户
near delete-account <account-id> <beneficiary-account>
```

**代币操作**

```bash
# 转账
near send <sender> <receiver> <amount>

# 查看余额
near balance <account-id>
```

**合约交互**

```bash
# 调用合约方法（变更状态）
near call <contract-id> <method-name> '{"arg1": "value1"}' --accountId <account-id>

# 查看合约数据（只读）
near view <contract-id> <method-name> '{"arg1": "value1"}'
```

**智能合约操作**

```bash
# 部署合约
near deploy <account-id> <wasm-file>

# 查看合约代码
near code <account-id>
```

---

## §7 验证者（Validator）指南

### 7.1 成为验证者的要求

| 要求 | 说明 |
|------|------|
| **质押数量** | 需质押一定数量的 NEAR 代币 |
| **节点要求** | 稳定运行的全节点 |
| **网络要求** | 可靠的网络连接 |
| **硬件要求** | 16GB+ 内存，100GB+ SSD |

### 7.2 质押 NEAR

```bash
# 委托给验证者
near stake <account-id> <validator-id> <amount>

# 查看当前验证者
near validators current

# 查看即将到来的验证者
near validators next
```

### 7.3 运行验证者节点

```bash
# 初始化验证者节点
neard init --validator

# 配置验证者密钥
cp ~/.near/validator_key.json ~/.near/validator_key.json.bak

# 编辑验证者配置
vim ~/.near/config.json

# 启动验证者
neard run
```

---

## §8 协议开发贡献

### 8.1 开发工作流

NEAR 使用以下开发流程：

```bash
# 1. Fork 仓库
# 访问 https://github.com/near/nearcore 点击 Fork

# 2. 克隆你的 fork
git clone https://github.com/<your-username>/nearcore
cd nearcore

# 3. 添加上游仓库
git remote add upstream https://github.com/near/nearcore.git

# 4. 创建特性分支
git checkout -b feature/my-feature

# 5. 进行更改并提交
git commit -m "feat: add my feature"

# 6. 推送分支
git push origin feature/my-feature

# 7. 在 GitHub 上创建 Pull Request
```

### 8.2 代码规范

NEAR 使用以下工具确保代码质量：

| 工具 | 用途 |
|------|------|
| **cargo fmt** | 代码格式化 |
| **cargo clippy** | Lint 检查 |
| **cargo test** | 单元测试 |
| **cargo deny** | 依赖审计 |

```bash
# 格式化代码
cargo fmt

# Lint 检查
cargo clippy --all --benches --tests --examples

# 运行测试
cargo test

# 审计依赖
cargo deny check
```

### 8.3 测试

NEAR 有多层测试：

```bash
# 单元测试
cargo test --lib

# 集成测试
cargo test --test integration_tests

# 夜间测试（需要特殊配置）
cargo test --nightly
```

### 8.4 提交规范

NEAR 使用 Conventional Commits 规范：

```
<type>(<scope>): <subject>

feat(chain): add new consensus algorithm
fix(runtime): resolve batch transaction issue
docs(docs): update API documentation
```

---

## §9 常见问题

### Q1：nearcore 和 NEAR Protocol 是什么关系？

nearcore 是 NEAR Protocol 的**参考实现**，是用 Rust 编写的全节点软件。它实现了 NEAR 协议的所有规范，任何人都可以用它来运行 NEAR 网络的节点。

### Q2：NEAR 和 Ethereum 有什么区别？

| 特性 | NEAR | Ethereum |
|------|------|----------|
| 共识 | PoS + Nightshade 分片 | PoS + 分片 (2.0) |
| 智能合约语言 | Rust, JS/TS | Solidity, Vyper |
| 开发者体验 | 类似 Firebase | 类似传统 Web3 |
| 费用 | 低（$0.01-0.1/交易）| 高（$1-100/交易）|
| 分片 | Nightshade | Danksharding |

### Q3：如何选择 Rust 或 JavaScript 编写合约？

| 语言 | 适用场景 |
|------|----------|
| **Rust** | 高性能要求、复杂逻辑、长期项目 |
| **JavaScript/TS** | 快速原型、Web 开发者友好 |

### Q4：NEAR 的代币经济模型是什么？

NEAR 使用以下代币机制：
- **总供应量**: 10 亿 NEAR
- ** staking**: 验证者通过质押获得奖励
- **Gas**: 交易和合约执行消耗 Gas
- **存储**: 使用存储需质押代币

### Q5：如何获取 NEAR 测试网代币？

访问 NEAR 水龙头获取测试网代币：

```
https://faucet.testnet.near.org/
```

### Q6：NEAR 支持哪些钱包？

| 钱包 | 说明 |
|------|------|
| **NEAR Wallet** | 官方网页钱包 |
| **MetaMask** | 通过 WalletConnect 连接 |
| **Ledger** | 硬件钱包支持 |
| **Nightly** | 浏览器插件钱包 |

---

## §10 总结

### 10.1 核心优势

| 优势 | 说明 |
|------|------|
| **开发者友好** | 类似 Firebase 的体验 |
| **低成本** | 比 Ethereum 低 100-1000 倍 |
| **高可扩展性** | Nightshade 分片技术 |
| **多语言支持** | Rust + JavaScript/TypeScript |
| **成熟工具链** | CLI、SDK、钱包一应俱全 |
| **活跃社区** | Discord、Telegram、论坛 |

### 10.2 适用场景

| 场景 | 推荐工具 |
|------|----------|
| **DeFi 应用** | near-sdk-rs + Rust |
| **NFT 平台** | near-sdk-js + JavaScript |
| **游戏** | NEAR APIs + React |
| **企业应用** | NEAR Lake + 数据分析 |

### 10.3 项目信息

- 最新版本：2.10.7 (2026-03-04)
- Stars：2.6k
- Forks：767
- 贡献者：253 人
- 许可证：Apache-2.0 / MIT

### 10.4 参与贡献

NEAR 是一个开源项目，欢迎贡献：

- 阅读 [CONTRIBUTING.md](https://github.com/near/nearcore/blob/master/CONTRIBUTING.md)
- 加入 [Discord](https://discord.com/invite/nearprotocol)
- 参与技术讨论 [Zulip](https://near.zulipchat.com/)
- 查看 [规范库](https://github.com/nearprotocol/NEPs)

---

*文档版本 1.0 | 撰写日期：2026-03-31 | 基于 2.10.7 (2026-03-04) | Stars: 2.6k ⭐*