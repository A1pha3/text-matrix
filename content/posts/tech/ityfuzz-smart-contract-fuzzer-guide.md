---
title: "ItyFuzz：极速智能合约混合模糊测试器指南"
date: "2026-04-01T01:03:00+08:00"
slug: "ityfuzz-smart-contract-fuzzer-guide"
description: "解析 ItyFuzz (1.1k Stars)：极速 EVM/MoveVM 智能合约混合模糊测试器，结合符号执行和模糊测试技术，在大型项目上发现126个漏洞（vs Echidna 0个），支持链上分叉/闪电贷/重入攻击自动利用。"
draft: false
categories: ["技术笔记"]
tags: ["ItyFuzz", "智能合约", "模糊测试", "符号执行", "EVM", "MoveVM", "漏洞挖掘", "安全审计", "LibAFL", "区块链安全"]
---

# ItyFuzz：极速智能合约混合模糊测试器指南

## §2 项目概述

### 2.1 什么是 ItyFuzz？

**ItyFuzz**（[GitHub 仓库](https://github.com/fuzzland/ityfuzz)）是一个**极速的 EVM 和 MoveVM 智能合约混合模糊测试器**，结合符号执行（symbolic execution）和模糊测试（fuzzing）技术，用于在链下和链上发现智能合约漏洞。

**官方描述**：

> ItyFuzz is a blazing-fast EVM and MoveVM smart contract hybrid fuzzer that combines symbolic execution and fuzzing to find bugs in smart contracts offchain and onchain.

它解决的问题是：智能合约安全审计中，人工逐行审查耗时且容易遗漏，纯模糊测试又难以触发深层逻辑漏洞。ItyFuzz 把符号执行和模糊测试拼在一起，前者负责构造精确输入触发复杂路径，后者负责快速撒网覆盖基本路径。

### 2.2 核心数据

| 指标 | 数值 |
|------|------|
| **Stars** | 1,074 (1.1k) |
| **Forks** | 172 |
| **Watchers** | 14 |
| **提交数** | 1,175 |
| **分支数** | 97 |
| **发布版本** | 48 个标签 |
| **部署数** | 393 |
| **许可证** | MIT |

### 2.3 技术栈

| 类别 | 技术 | 占比 |
|------|------|------|
| **核心语言** | Rust | 92.2% |
| **智能合约** | Solidity | 4.5% |
| **构建/测试** | Python | 1.7% |
| **脚本** | Shell | 0.7% |
| **Move 语言** | Move | 0.4% |
| **模板** | Handlebars | 0.3% |

### 2.4 核心特性

| 特性 | 说明 |
|------|------|
| **链上分叉** | 在任意链的任意区块高度测试合约 |
| **精准漏洞利用生成** | 自动生成精度丢失、整数溢出、资金盗取等漏洞利用代码 |
| **重入攻击支持** | 具体利用潜在重入漏洞探索更多代码路径 |
| **极速调度** | 优先测试更可能有漏洞的代码 |
| **符号执行** | 生成比纯模糊测试覆盖更多代码路径的测试用例 |
| **闪电贷支持** | 模拟攻击者拥有无限资金 |
| **清算支持** | 模拟在模糊测试期间从流动性池买卖任意代币 |
| **反编译支持** | 对无源码合约进行模糊测试 |
| **复杂初始化** | 支持 Foundry 设置脚本、Anvil RPC 分叉或 JSON 配置文件 |
| **LibAFL 驱动** | 基于 SOTA 模糊测试引擎 |

### 2.5 适用场景

| 场景 | 描述 |
|------|------|
| **安全审计** | 自动化发现智能合约漏洞 |
| **开发测试** | 在部署前发现潜在安全问题 |
| **漏洞赏金** | 自动化生成漏洞利用代码 |
| **回归测试** | 确保合约升级不引入新漏洞 |

## §3 性能基准

### 3.1 大型真实项目对比

| 工具 | 发现漏洞数 |
|------|------------|
| **ItyFuzz** | **126** |
| Mythril | 9 |
| Echidna | 0 |

### 3.2 小型合约对比

| 指标 | 结果 |
|------|------|
| **测试覆盖提升** | 比 SMARTIAN 高 10% |
| **测试时间** | 仅需 SMARTIAN 的 1/30 |

### 3.3 Daedaluzz 基准测试

在 Consensys 的 Daedaluzz 基准测试中（不使用符号执行）：

| 指标 | 结果 |
|------|------|
| **比 Echidna 发现更多漏洞** | +44% |
| **比 Foundry 发现更多漏洞** | +31% |
| **速度比 Echidna 快** | 2.5x |
| **速度比 Foundry 快** | 1.5x |

## §4 安装与部署

### 4.1 一键安装

```bash
curl -L https://ity.fuzz.land/ | bash ityfuzzup
```

### 4.2 从源码编译

```bash
# 克隆仓库
git clone https://github.com/fuzzland/ityfuzz
cd ityfuzz

# 使用 Rust 编译
cargo build --release

# 运行测试
cargo test
```

### 4.3 Docker 部署

```bash
# 构建 Docker 镜像
docker build -t ityfuzz .

# 运行容器
docker run -it ityfuzz
```

## §5 使用指南

### 5.1 模糊测试已部署的智能合约

#### 5.1.1 基本用法

```bash
# 使用默认 EVM RPC 测试合约
ityfuzz evm \
    -t <目标合约地址> \
    --etherscan-api-key <API密钥>
```

#### 5.1.2 分叉特定链的合约

```bash
# 分叉 Polygon 并在特定区块测试
ETH_RPC_URL=https://polygon-rpc.com ityfuzz evm \
    -t 0xbcf6e9d27bf95f3f5eddb93c38656d684317d5b4,0x5d6c48f05ad0fde3f64bab50628637d73b1eb0bb \
    -c polygon \
    --onchain-block-number 35718198
```

#### 5.1.3 使用闪电贷

```bash
# 启用闪电贷支持（模拟无限资金攻击）
ETH_RPC_URL=https://polygon-rpc.com ityfuzz evm \
    -t <目标合约地址> \
    -c polygon \
    --flashloan \
    --onchain-block-number <区块号>
```

### 5.2 运行 Foundry Invariant 测试

```bash
# 运行 Foundry invariant 测试
ityfuzz evm \
    -m test/Invariant.sol:Invariant \
    -- forge test
```

### 5.3 常见命令选项

| 选项 | 说明 | 示例 |
|------|------|------|
| `-t` | 目标合约地址 | `-t 0x...` |
| `-c` | 链名称 | `-c polygon` |
| `--etherscan-api-key` | Etherscan API 密钥 | `--etherscan-api-key <key>` |
| `--flashloan` | 启用闪电贷模拟 | `--flashloan` |
| `--onchain-block-number` | 链上区块高度 | `--onchain-block-number 35718198` |
| `-m` | 模块/测试文件 | `-m test/Invariant.sol:Invariant` |
| `--forge` | 运行 Foundry 测试 | `-- forge test` |

## §6 核心特性详解

### 6.1 链上分叉（Chain Forking）

ItyFuzz 支持在任意链的任意区块高度创建合约分叉，允许对历史状态进行测试：

```bash
# 在特定区块分叉以太坊
ETH_RPC_URL=https://eth-mainnet.rpc.example.com ityfuzz evm \
    -t <合约地址> \
    --onchain-block-number 15000000
```

### 6.2 精准漏洞利用生成

ItyFuzz 不仅能发现漏洞，还能自动生成精确的漏洞利用代码：

| 漏洞类型 | 支持 |
|----------|------|
| **精度丢失** | ✅ |
| **整数溢出** | ✅ |
| **资金盗取** | ✅ |
| **Uniswap 配对误用** | ✅ |
| **重入攻击** | ✅ |
| **闪电贷攻击** | ✅ |

### 6.3 重入攻击支持

```bash
# 测试重入漏洞
ityfuzz evm \
    -t <合约地址> \
    --reentrancy
```

### 6.4 清算支持

```bash
# 模拟清算操作
ityfuzz evm \
    -t <合约地址> \
    --liquidation
```

### 6.5 反编译支持

对无源码的字节码合约进行测试：

```bash
# 对字节码进行反编译和测试
ityfuzz evm \
    -t <字节码地址> \
    --decompile
```

## §7 工作原理

### 7.1 混合模糊测试架构

ItyFuzz 采用**混合模糊测试**方法，结合两种技术的优势：

1. **模糊测试（Fuzzing）**
   - 快速生成大量随机输入
   - 高效探索基本代码路径
   - 发现简单的逻辑错误

2. **符号执行（Symbolic Execution）**
   - 生成覆盖更多代码路径的测试用例
   - 精确触发复杂漏洞
   - 解决约束条件生成精确输入

### 7.2 LibAFL 引擎

ItyFuzz 基于 LibAFL（最先进的模糊测试引擎）构建：

- 高性能模糊测试调度
- 并行模糊测试支持
- 可插拔的模糊测试策略
- 丰富的覆盖率跟踪

### 7.3 极速调度（Power Scheduling）

ItyFuzz 使用智能调度算法优先测试更可能有漏洞的代码区域：

```rust
// 调度策略伪代码
fn schedule_power(corpus, coverage, vulnerabilities) {
    // 根据覆盖率和新发现调整功率分配
    for item in corpus {
        power = calculate_power(item, coverage, vulnerabilities);
        assign_power(item, power);
    }
}
```

## §8 已发现漏洞

### 8.1 精选新漏洞

| 项目 | 漏洞类型 | 资产风险 |
|------|----------|----------|
| BSC $rats NFT | 整数溢出导致无限铸造 | $79,000 |
| 9419 Token | 错误逻辑导致价格操纵 | $35,000 |
| BSC Mevbot | 无守卫 DPPFlashLoanCall | $19,000 |
| FreeCash | 错误逻辑导致价格操纵 | $12,000 |
| 0xnoob Token | 错误逻辑导致价格操纵 | $7,000 |
| Baby Wojak Token | 错误逻辑导致价格操纵 | $4,000 |
| Arrow | 错误仓位逻辑导致资金损失 | 审计中发现 |

### 8.2 漏洞利用自动生成

ItyFuzz 可以自动生成超过 80% 历史黑客事件的漏洞利用代码，无需了解具体攻击细节。

## §9 项目结构

### 9.1 目录结构

```
ityfuzz/
├── src/                    # 核心源代码
├── benches/                # 基准测试
├── ityfuzzup/             # 自动更新程序
├── onchain_scripts/        # 链上脚本
├── server/                 # 服务器组件
├── solidity_utils/         # Solidity 工具
├── tests/                  # 测试用例
├── ui/                     # 用户界面
├── Cargo.toml              # Rust 项目配置
├── Cargo.lock              # 依赖锁定
├── Dockerfile              # Docker 配置
├── Makefile.toml           # 构建配置
├── rust-toolchain.toml     # Rust 工具链配置
└── README.md              # 项目文档
```

### 9.2 主要模块

| 模块 | 说明 |
|------|------|
| **src/** | 模糊测试基本逻辑、符号执行、EVM/MoveVM 执行器 |
| **benches/** | 性能基准测试套件 |
| **solidity_utils/** | Solidity 合约解析和处理工具 |
| **server/** | Web 服务器和 API |
| **ui/** | 命令行界面组件 |

## §10 集成与扩展

### 10.1 Foundry 集成

ItyFuzz 可以直接运行 Foundry invariant 测试：

```solidity
// test/Invariant.sol
contract Invariant {
    function invariant_balance() public view {
        require(address(this).balance >= 0);
    }
}
```

```bash
# 运行 Foundry invariant 测试
ityfuzz evm -m test/Invariant.sol:Invariant -- forge test
```

### 10.2 自定义配置

通过 JSON 配置文件初始化复杂合约：

```json
{
    "init": {
        "rpc": "https://eth-mainnet.rpc.example.com",
        "block_number": 15000000
    },
    "contracts": [
        "0x..."
    ],
    "flashloan": true
}
```

### 10.3 Etherscan API

```bash
# 设置 Etherscan API 密钥
export ETHERSCAN_API_KEY=your_api_key

# 自动获取合约源码
ityfuzz evm -t <合约地址> --etherscan-api-key $ETHERSCAN_API_KEY
```

## §11 实践建议

### 11.1 测试策略

| 阶段 | 策略 |
|------|------|
| **初始测试** | 使用默认设置运行基础模糊测试 |
| **深度测试** | 启用符号执行和闪电贷 |
| **针对性测试** | 使用特定区块高度和 RPC |
| **回归测试** | 集成到 CI/CD 流程 |

### 11.2 性能优化

| 技巧 | 说明 |
|------|------|
| **并行测试** | 使用多线程加速测试 |
| **选择区块** | 使用漏洞发生前的区块 |
| **过滤无关交易** | 减少噪音输入 |
| **启用符号执行** | 对复杂路径进行深度测试 |

### 11.3 安全注意事项

- ⚠️ 仅在测试网络上运行
- ⚠️ 不要在生产环境暴露 RPC 凭证
- ⚠️ 定期更新到最新版本
- ⚠️ 结合人工代码审计

## §12 常见问题

### Q1：ItyFuzz 与 Echidna 有何区别？

ItyFuzz 使用混合方法（模糊测试 + 符号执行），在大型项目上明显优于 Echidna（126 vs 0 漏洞）。 Echidna 主要依赖纯模糊测试。

### Q2：ItyFuzz 支持哪些链？

支持所有 EVM 兼容链（以太坊、Polygon、BSC、Avalanche 等）和 MoveVM 链（Sui、Aptos）。

### Q3：需要源码才能测试吗？

不需要。ItyFuzz 支持字节码反编译测试，但有源码可以获得更好的覆盖率。

### Q4：如何加速测试？

使用并行测试、选择合适的区块高度、启用符号执行。

### Q5：ItyFuzz 可以完全替代人工审计吗？

不能。ItyFuzz 是自动化工具，但人工审计仍不可替代，两者搭配使用效果更好。

## §13 总结

ItyFuzz 与 Echidna、Mythril 的根本区别在于**混合模糊测试**（fuzzing + 符号执行）和**自动漏洞利用生成**。在大型项目上，它的检测能力远超 Echidna 和 Mythril（126 vs 9 vs 0），但这个数字来自官方基准测试，实际效果取决于合约复杂度和配置。对于无源码合约，反编译模式是它的独特优势；对于 Foundry 用户，invariant 测试集成降低了迁移成本。

ItyFuzz 不能替代人工审计，两者各有所长，搭配使用比单独依赖任一方更可靠。

### 13.4 相关链接

| 资源 | 链接 |
|------|------|
| **GitHub** | https://github.com/fuzzland/ityfuzz |
| **文档** | https://docs.ityfuzz.rs |
| **论文** | https://dl.acm.org/doi/pdf/10.1145/3597926.3598059 |
| **Twitter** | https://twitter.com/fuzzland_ |
| **Discord** | https://discord.com/invite/qQa436VEwt |

## §14 附录：术语表

| 术语 | 说明 |
|------|------|
| **Fuzzing（模糊测试）** | 使用随机数据作为输入测试程序 |
| **Symbolic Execution（符号执行）** | 使用符号而非具体值执行程序 |
| **EVM** | Ethereum Virtual Machine，以太坊虚拟机 |
| **MoveVM** | Move 语言虚拟机（Sui/Aptos 使用） |
| **Flashloan（闪电贷）** | 无抵押的借贷攻击向量 |
| **Reentrancy（重入）** | 合约调用自身时的攻击向量 |
| **Invariant（不变量）** | 合约应始终满足的条件 |
| **LibAFL** | Advanced Fuzzing Library，最先进的模糊测试框架 |

---

*基于 ItyFuzz (1.1k Stars) | 性能数据来源：官方基准测试*