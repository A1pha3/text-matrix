---
title: "Acton：TON智能合约开发一站式工具链完全指南"
date: "2026-05-14T10:55:00+08:00"
slug: "acton-ton-smart-contract-toolchain-guide"
description: "TON 生态的工具链由 Blueprint 脚手架、FunC/Tolk 编译器、@ton/sandbox 本地沙盒、@ton/test-utils 测试断言库等独立工具组成，没有单一官方工具链。本文以一个 Jetton 代币合约为例，串联编写、编译、测试、调试、部署、验证七个阶段，给出工具选型、采用顺序和常见错误排查。"
draft: false
categories: ["技术笔记"]
tags: ["TON", "智能合约", "Rust", "区块链开发", "FunC"]
---

# TON 智能合约开发工具链完全指南：从 FunC 编写到链上验证

TON（The Open Network）生态没有单一官方工具链，由 Blueprint 脚手架、FunC/Tolk 编译器、@ton/sandbox 本地沙盒、@ton/test-utils 测试断言库等独立工具组成完整开发链路。早期文章提到的"Acton 一站式 CLI"在 TON 官方仓库中并不存在，本文按真实工具链重写，以一个 Jetton（TON 上的代币标准，类似 ERC-20）代币合约为例，串联编写、编译、测试、调试、部署、验证七个阶段，给出每个阶段的工具选型、采用顺序和常见错误排查。

读完本文，你应当能够：

1. 说出 Blueprint、FunC/Tolk 编译器、@ton/sandbox、@ton/test-utils 四类工具的职责边界
2. 用 `npm create ton@latest` 创建一个 TON 合约项目，并解释 `contracts/`、`wrappers/`、`tests/` 三个目录的分工
3. 用 `@ton-community/func-js` 把 FunC 源码编译为 TVM Cell，并写出最小可运行的编译脚本
4. 用 `@ton/sandbox` 的 `Blockchain` 类编写本地单元测试，断言合约 getter 返回值和消息处理结果
5. 把合约部署到 Testnet（测试网），并用 tonverifier.app 完成源码验证

## 目录

- [TON 工具链总览](#ton-工具链总览)
- [任务流案例：Jetton 代币合约全生命周期](#任务流案例jetton-代币合约全生命周期)
  - [1. 项目脚手架：Blueprint](#1-项目脚手架blueprint)
  - [2. 编写合约：FunC 与 Tolk](#2-编写合约func-与-tolk)
  - [3. 编译：func-js 与 tolk 编译器](#3-编译func-js-与-tolk-编译器)
  - [4. 本地测试：@ton/sandbox 与 @ton/test-utils](#4-本地测试tonsandbox-与-tontest-utils)
  - [5. 调试与 Trace 分析](#5-调试与-trace-分析)
  - [6. 部署到 Testnet](#6-部署到-testnet)
  - [7. 链上验证](#7-链上验证)
- [工具选型与采用顺序](#工具选型与采用顺序)
- [常见问题与错误排查](#常见问题与错误排查)
- [自测检查清单](#自测检查清单)
- [进阶路径](#进阶路径)

## TON 工具链总览

TON 合约开发涉及两条并行链路：**编译链路**把源码变成 TVM 字节码，**测试链路**在本地或链上验证合约行为。两条链路用不同工具，不能混用。

| 阶段 | 主力工具 | 备选或旧工具 | 说明 |
|------|----------|--------------|------|
| 项目脚手架 | Blueprint（`@ton/blueprint`） | 手动 `package.json` | 管理目录约定、编译脚本、部署脚本 |
| 合约编写 | FunC、Tolk | — | FunC 是 TON 原生函数式合约语言；Tolk 是 2024 年起官方主推的现代合约语言 |
| 编译 | `@ton-community/func-js`、`tolk` CLI | `func` 二进制 | 输出 TVM Cell（TON 虚拟机的二进制格式） |
| 本地测试 | `@ton/sandbox`、`@ton/test-utils` | `ton-contract-executor`（已废弃） | sandbox 提供 `Blockchain` 类模拟 TVM；test-utils 提供 Jest 断言 |
| 链上交互 | `@ton/ton`、`@ton/crypto` | `ton` CLI | `TonClient4` 连接 Testnet 或 mainnet（主网） |
| 部署 | Blueprint `run` 脚本 | `ton-cli` | 用 TypeScript 脚本发送部署消息 |
| 验证 | tonverifier.app | tonscan.org | 比对链上合约代码与本地源码 |

`ton-contract-executor` 在 2023 年后已被 `@ton/sandbox` 取代，新项目不应再用。`func` 二进制和 `tolk` CLI 是底层编译器，Blueprint 通过 `@ton-community/func-js` 在 Node.js 进程内调用，通常不需要手动安装二进制。

## 任务流案例：Jetton 代币合约全生命周期

下面以一个最小可运行的 Jetton 代币合约为线索，把上表中的工具串起来。Jetton 是 TON 的代币标准（TEP-74），对应以太坊的 ERC-20。完整流程：编写合约源码 → 编译为 Cell → 本地测试 → 调试 Trace → 部署到 Testnet → 链上验证。

### 1. 项目脚手架：Blueprint

Blueprint 是 TON 官方维护的项目脚手架，封装了目录约定、编译脚本、测试运行器和部署脚本。用 `npm create ton@latest` 创建项目：

```bash
npm create ton@latest my-jetton
```

交互式提示会询问合约名称和模板（默认选 FunC + Blueprint 模板）。生成目录结构：

```text
my-jetton/
├── contracts/
│   └── jetton_minter.fc      # FunC 合约源码
├── wrappers/
│   └── JettonMinter.ts       # TypeScript 包装器（编译入口 + 部署消息构造 + getter 调用）
├── tests/
│   └── JettonMinter.spec.ts  # Jest + @ton/sandbox 测试
├── scripts/
│   └── deployJettonMinter.ts # 部署脚本
├── package.json
└── tsconfig.json
```

`wrappers/` 是 Blueprint 的约定：每个合约配一个 TypeScript 包装器，封装编译入口、部署消息构造和 getter 调用。`tests/` 默认用 Jest，配合 `@ton/sandbox` 和 `@ton/test-utils`。

### 2. 编写合约：FunC 与 Tolk

FunC（TON 函数式合约语言）是 TON 早期合约语言，语法接近 ML 家族；Tolk（TON 现代合约语言）是 2024 年起官方主推的替代语言，语法更接近 TypeScript。两者都编译到 TVM（TON 虚拟机）字节码。

以 FunC 为例，Jetton minter 的核心逻辑（精简版，省略 Jetton wallet 部分）：

```func
;; jetton_minter.fc
global int total_supply;
global slice admin_address;
global cell jetton_wallet_code;

() init() impure {
  ;; 存储布局：total_supply | admin_address | jetton_wallet_code
}

int get_total_supply() method_id {
  return total_supply;
}

() recv_internal(int my_balance, int msg_value, slice in_msg_full, slice in_msg_body) impure {
  if (in_msg_body.slice_empty?()) {
    return ();
  }
  int op = in_msg_body~load_uint(32);
  if (op == 0x178d4519) {  ;; Mint 操作码
    int amount = in_msg_body~load_coins();
    total_supply += amount;
    return ();
  }
  return ();
}
```

`recv_internal` 是合约接收内部消息的入口。`load_uint(32)` 读取 32 位操作码，`load_coins()` 读取变长整数（TON 的代币金额编码）。`0x178d4519` 是 Jetton 标准定义的 Mint 操作码。

Tolk 的等价写法语法更现代（类型注解、对象参数），但 Tolk 仍在活跃迭代（2025 年发布 v0.7+），生产项目建议优先选 FunC，等 Tolk 稳定后再迁移。本文后续示例统一用 FunC。

### 3. 编译：func-js 与 tolk 编译器

Blueprint 在 `wrappers/JettonMinter.ts` 中调用 `@ton-community/func-js` 编译 FunC。最小编译脚本：

```typescript
import { compileFunc, compilerVersion } from '@ton-community/func-js';
import { Cell } from '@ton/core';
import * as fs from 'fs';
import * as path from 'path';

export async function compileJettonMinter(): Promise<Cell> {
  const result = await compileFunc({
    targets: ['jetton_minter.fc'],
    sources: {
      'jetton_minter.fc': fs.readFileSync(
        path.resolve(__dirname, '../contracts/jetton_minter.fc'),
        'utf8',
      ),
    },
  });

  if (result.status === 'error') {
    throw new Error(`FunC compile error: ${result.message}`);
  }

  console.log('func-js version:', await compilerVersion());  // func-js 0.4.0+ 返回 Promise，旧版同步返回字符串
  return Cell.fromBoc(Buffer.from(result.codeBoc, 'base64'))[0];
}
```

`compileFunc` 接收源码字符串（不是文件路径），返回 `codeBoc`（base64 编码的 TVM Cell）。`Cell.fromBoc` 把它解析成 `@ton/core` 的 `Cell` 对象，后续测试和部署都用这个对象。

Tolk 编译用 `tolk` CLI：

```bash
tolk compile jetton_minter.tolk --output jetton_minter.cell
```

或在 Node.js 中用 `tolk-js`（API 与 `func-js` 类似）。编译产物是 `.cell` 文件，即 TVM 二进制格式（Bag of Cells，BoC）。一个合约对应一个 Cell。

### 4. 本地测试：@ton/sandbox 与 @ton/test-utils

`@ton/sandbox` 提供 `Blockchain` 类，在本地进程内模拟 TVM 执行，不需要连接 Testnet。`@ton/test-utils` 给 Jest 加 TON 专用断言（如 `toEqual` 支持 `bigint`）。

`tests/JettonMinter.spec.ts`：

```typescript
import { Blockchain, SandboxContract, TreasuryContract } from '@ton/sandbox';
import { beginCell, toNano } from '@ton/core';
import '@ton/test-utils';
import { JettonMinter } from '../wrappers/JettonMinter';

describe('JettonMinter', () => {
  let blockchain: Blockchain;
  let deployer: SandboxContract<TreasuryContract>;
  let minter: SandboxContract<JettonMinter>;

  beforeEach(async () => {
    blockchain = await Blockchain.create();
    deployer = await blockchain.treasury('deployer');
    minter = blockchain.openContract(
      await JettonMinter.fromInit(deployer.address),
    );
  });

  it('should deploy with zero total supply', async () => {
    const deployMsg = beginCell()
      .storeUint(0, 32)   // Deploy opcode
      .storeUint(0n, 64)  // queryId
      .endCell();

    await minter.send(
      deployer.getSender(),
      { value: toNano('0.05') },
      deployMsg,
    );

    const supply = await minter.getTotalSupply();
    expect(supply).toEqual(0n);
  });

  it('should mint tokens to admin', async () => {
    const mintMsg = beginCell()
      .storeUint(0x178d4519, 32)  // Mint opcode
      .storeUint(1n, 64)          // queryId
      .storeCoins(toNano('100'))  // amount
      .endCell();

    await minter.send(
      deployer.getSender(),
      { value: toNano('0.05') },
      mintMsg,
    );

    const supply = await minter.getTotalSupply();
    expect(supply).toEqual(toNano('100'));
  });
});
```

`blockchain.treasury('deployer')` 创建一个有初始余额的虚拟钱包，作为部署者和消息发送者。`blockchain.openContract` 把合约包装成可调用对象，`send` 发送内部消息，`getTotalSupply` 调用 getter（只读方法）。

运行测试：

```bash
npx blueprint test
# 或直接用 Jest
npx jest tests/JettonMinter.spec.ts
```

### 5. 调试与 Trace 分析

TON 没有 FunC 源码级断点调试器。TVM 是栈式虚拟机，源码映射到 TVM 指令的映射关系不直接，断点调试在工程上难以实现。调试主要靠 `@ton/sandbox` 的 Trace 输出和退出码分析。

`@ton/sandbox` 在 `send` 后返回交易结果，包含退出码、Gas（链上执行燃料费）消耗和 emit 的事件：

```typescript
const result = await minter.send(
  deployer.getSender(),
  { value: toNano('0.05') },
  mintMsg,
);

if (result.transactions.length > 0) {
  const tx = result.transactions[0];
  const compute = tx.description.computePhase;
  if (compute.type === 'vm') {
    console.log('exit code:', compute.exitCode);
    console.log('gas used:', compute.gasUsed);
  }
  console.log('events:', result.events);
}
```

常见退出码：

- `0`：成功
- `-14`：Cell underflow（消息体字段读取顺序与合约 `load_*` 不匹配）
- `4`：Stack underflow（FunC 调用约定错误，通常是参数数量不对）
- `132`：自定义错误码（合约逻辑主动抛出）

合约行为异常时，先打印 `exitCode` 和 `events`，再对照 FunC 源码定位。复杂场景可以用 `@ton/sandbox` 的 `debug` 模式输出每条 TVM 指令，但输出量很大，建议只在定位特定指令时开启。

### 6. 部署到 Testnet

Testnet 是 TON 的公开测试环境，代币无价值，用于上线前验证。mainnet 是生产环境。Testnet 水龙头 Telegram 机器人：@testgiver_ton_bot。

部署脚本 `scripts/deployJettonMinter.ts`：

```typescript
import { TonClient4, WalletContractV4 } from '@ton/ton';
import { mnemonicToPrivateKey } from '@ton/crypto';
import { toNano, beginCell } from '@ton/core';
import { JettonMinter } from '../wrappers/JettonMinter';
import * as dotenv from 'dotenv';

dotenv.config();

async function deploy() {
  const mnemonic = process.env.DEPLOYER_MNEMONIC;
  if (!mnemonic) {
    throw new Error('DEPLOYER_MNEMONIC not set in .env');
  }

  // 1. 连接 Testnet v4 节点
  const client = new TonClient4({
    endpoint: 'https://testnet-v4.tonhubapi.com',
  });

  // 2. 从助记词派生钱包密钥
  const keyPair = await mnemonicToPrivateKey(mnemonic.split(' '));
  const wallet = client.open(
    WalletContractV4.create({
      workchain: 0,
      publicKey: keyPair.publicKey,
    }),
  );
  const sender = wallet.sender(keyPair.secretKey);

  // 3. 构造合约实例（fromInit 内部调用 compileJettonMinter 并计算地址）
  const minter = client.open(
    await JettonMinter.fromInit(sender.address),
  );

  // 4. 发送部署消息（wrapper 自动填充 stateInit）
  await minter.send(
    sender,
    { value: toNano('0.1') },
    beginCell().storeUint(0, 32).storeUint(0, 64).endCell(),
  );

  console.log('JettonMinter deployed at:', minter.address.toString());
}

deploy();
```

运行：

```bash
# .env 文件中放助记词（12 或 24 个单词）
echo 'DEPLOYER_MNEMONIC="word1 word2 ... word12"' > .env

# 执行部署
npx blueprint run deployJettonMinter --network testnet
```

`TonClient4` 连接 Testnet v4 节点。`WalletContractV4` 是 TON 钱包合约 V4 版本，用助记词派生密钥。部署消息是一条带 `stateInit`（合约代码 + 初始数据）的内部消息，合约收到后完成初始化。

### 7. 链上验证

部署后，链上只有编译后的 Cell，外部无法直接看到源码。源码验证把本地源码和链上 Cell 比对，证明两者一致。

用 [tonverifier.app](https://tonverifier.app)（原 DTON Verifier）：

1. 打开 tonverifier.app，连接钱包
2. 输入合约地址（Testnet 或 mainnet 均可）
3. 上传合约源码文件（`jetton_minter.fc` 及所有 `#include` 的文件）
4. 选择编译器版本（与 `compilerVersion()` 输出一致）
5. 提交验证

验证通过后，tonscan.org 上该合约页面会显示"Verified"标记并展示源码。dApp 前端团队通常以此作为集成前提——tonverifier 通过后 tonscan 才展示源码，未验证的合约在集成方眼里缺少可追溯依据。

## 工具选型与采用顺序

新团队接入 TON 合约开发，建议按以下顺序采用：

1. **先上 Blueprint + FunC + @ton/sandbox**：这是 2025 年最稳定的组合，文档和社区案例最多。用 `npm create ton@latest` 起步，2 天内能跑通本地测试。
2. **再接 @ton/ton + Testnet 部署**：本地测试稳定后，用 `TonClient4` 连 Testnet，验证合约在真实网络环境下的 Gas 消耗和消息流。
3. **最后评估 Tolk 迁移**：Tolk 语法更现代，但仍在迭代。等 Tolk 发布稳定版（预计 2026 年）且社区库完善后再迁移存量合约。

哪些团队不必急着上 Tolk：

- 合约已上线且稳定运行的团队：迁移成本高于收益
- 团队对 FunC 已熟练：FunC 仍被官方支持，没有废弃时间表
- 安全审计要求高的团队：Tolk 工具链（fuzzing、形式化验证）还不成熟

哪些团队可以先用 Tolk：

- 新项目、合约逻辑复杂、团队有 TypeScript 背景
- 愿意承受工具链迭代风险的早期项目

## 常见问题与错误排查

### FunC 编译报 `undefined function`

原因：`#include` 路径错误或源码未传入 `sources`。`compileFunc` 的 `sources` 是一个 `{ [filename]: content }` 字典，所有依赖文件都要手动加入，不会自动从磁盘读取。

### @ton/sandbox 测试报 `exit code -14`

原因：消息体 Cell 序列化顺序与合约 `load_*` 调用顺序不匹配。用 `beginCell()` 构造消息时，`storeUint`、`storeCoins`、`storeAddress` 的调用顺序必须与 FunC 中 `load_uint`、`load_coins`、`load_msg_addr` 的顺序完全一致。

### Testnet 部署后合约无响应

排查顺序：

1. 用 tonscan.org（Testnet）查合约地址是否已上链
2. 检查部署消息的 `value` 是否足够覆盖 Gas（建议 `toNano('0.05')` 以上）
3. 检查钱包余额是否足够（Testnet 水龙头：@testgiver_ton_bot）
4. 用 `TonClient4` 的 `getAccount` 查合约状态，确认 `state` 是否为 `active`

### tonverifier 验证失败

原因：编译器版本不匹配或源码有改动。在 `wrappers/` 中打印 `compilerVersion()`，用相同版本重新验证。如果合约用了 `#include`，确认所有 include 文件都已上传。

### Gas 消耗超预期

TON 的 Gas 按 TVM 指令计费。用 `@ton/sandbox` 的 `result.transactions[0].description.computePhase.gasUsed` 查看具体消耗。常见优化方向：

- 减少 `dict` 操作（每次 `lookup` 消耗较高）
- 用 `int` 替代 `cell` 存储小数据
- 避免在 `recv_internal` 中做重计算，能放到 getter 里的逻辑不要写进消息处理

## 自测检查清单

读完本文后，用以下问题自测：

1. Blueprint、FunC 编译器、@ton/sandbox 三者的职责边界分别是什么？
2. `compileFunc` 返回的 `codeBoc` 是什么格式？如何转成 `Cell` 对象？
3. `@ton/sandbox` 的 `blockchain.treasury` 和 `blockchain.openContract` 分别做什么？
4. 合约部署到 Testnet 后，如何用 `TonClient4` 查询合约 getter？
5. tonverifier.app 验证合约时，需要提交哪些文件？验证的是什么？

5 题都能答出，说明已掌握 TON 合约开发工具链的核心。答不出的章节建议重读，特别是第 3、4 节的编译与测试链路。

## 进阶路径

- **FunC 进阶**：读 [TON 官方文档](https://docs.ton.org/v3/guidelines/smart-contracts/) 的 Jetton 标准实现，理解 masterchain 与 workchain 的消息流
- **TVM 底层**：读 [TVM 概览](https://docs.ton.org/v3/documentation/tvm/tvm-overview)，理解栈式虚拟机、Continuation 和 Gas 计费模型
- **安全审计**：用 [ton-blockchain/ton-sec-tools](https://github.com/ton-blockchain/ton-sec-tools) 做 FunC 静态扫描，重点关注重入、整数溢出、权限校验缺失
- **Tolk 迁移**：跟踪 [ton-blockchain/tolk](https://github.com/ton-blockchain/tolk) 仓库，等 v1.0 稳定后评估迁移
