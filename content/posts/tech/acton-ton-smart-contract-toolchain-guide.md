---
title: "TON 智能合约开发工具链完全指南：从 FunC 编写到链上验证"
date: "2026-05-14T10:55:00+08:00"
slug: "acton-ton-smart-contract-toolchain-guide"
github_repo: "ton-blockchain/acton"
source_key: "gh:ton-blockchain/acton"
description: "TON 生态的工具链正从 Blueprint、FunC/Tolk 编译器、@ton/sandbox 本地沙盒、@ton/test-utils 测试断言库组成的拼装链路，向官方的 Acton 一体化工具链演进。本文以一个 Jetton 代币合约为例，串联脚手架、编写、编译、测试、调试、部署、验证七个阶段，给出工具选型、采用顺序和常见错误排查。"
draft: false
categories: ["技术笔记"]
tags: ["智能合约", "TypeScript"]
---

# TON 智能合约开发工具链完全指南：从 FunC 编写到链上验证

TON（The Open Network）生态的工具链正在换代：官方在 2026 年 5 月 11 日发布了 Acton v1.0（[github.com/ton-blockchain/acton](https://github.com/ton-blockchain/acton)），一个围绕 Tolk 语言构建的一体化开发平台，官方文档已把 Blueprint 归入 legacy 章节；而社区里大量存量教程和项目仍在使用 Blueprint 脚手架、FunC 语言、`@ton/sandbox`、`@ton/test-utils` 这套较老的 TypeScript 生态。两条链路各管一段，靠目录约定和 Node.js API 串起来，互相不冲突。本文用一个 Jetton（TON 上的代币标准，类似 ERC-20）代币合约作为线索，先走一遍 Blueprint + FunC 的老链路（脚手架、编写、编译、测试、调试、部署、验证），再说明什么时候适合切到 Acton + Tolk。

## 学习目标

1. Blueprint、FunC/Tolk 编译器、@ton/sandbox、@ton/test-utils 四类工具各自管什么，边界在哪
2. 用 `npm create ton@latest` 创建项目后，`contracts/`、`wrappers/`、`tests/` 三个目录分别承担什么
3. 用 `@ton-community/func-js` 把 FunC 源码编译为 TVM Cell 的最小脚本怎么写
4. 用 `@ton/sandbox` 的 `Blockchain` 类怎么写本地单元测试，怎么断言 getter 返回值、消息处理结果和错误退出码
5. 合约部署到 Testnet（测试网）后，怎么用 verifier.ton.org 完成源码验证

## 目录

- [学习目标](#学习目标)
- [TON 工具链总览](#ton-工具链总览)
- [任务流案例：Jetton 代币合约全生命周期](#任务流案例jetton-代币合约全生命周期)
  - [1. 项目脚手架：Blueprint](#1-项目脚手架blueprint)
  - [2. 编写合约：FunC 与 Tolk](#2-编写合约func-与-tolk)
  - [3. 编译：func-js 与 Tolk 编译器](#3-编译func-js-与-tolk-编译器)
  - [4. 本地测试：@ton/sandbox 与 @ton/test-utils](#4-本地测试tonsandbox-与-tontest-utils)
  - [5. 调试与 Trace 分析](#5-调试与-trace-分析)
  - [6. 部署到 Testnet](#6-部署到-testnet)
  - [7. 链上验证](#7-链上验证)
- [工具选型与采用顺序](#工具选型与采用顺序)
- [常见问题与错误排查](#常见问题与错误排查)
- [自测题](#自测题)
- [动手练习](#动手练习)
- [进阶路径](#进阶路径)
- [资料口径说明](#资料口径说明)

## TON 工具链总览

TON 合约开发涉及两条并行链路：**编译链路**把源码变成 TVM 字节码，**测试链路**在本地或链上验证合约行为。两条链路用不同工具，工具之间不互相替代。

| 阶段 | 主力工具 | 备选或旧工具 | 说明 |
|------|----------|--------------|------|
| 项目脚手架 | Acton（新项目）、Blueprint（存量） | 手动 `package.json` | Acton 是官方新工具链；Blueprint 仍可用，官方文档已将其归入 legacy 章节 |
| 合约编写 | Tolk、FunC | — | Tolk 是官方主推、语法接近 TypeScript 的现代合约语言；FunC 是早期函数式语言，存量合约大量使用 |
| 编译 | `acton build`、`@ton-community/func-js` | `func` 二进制 | 输出 TVM Cell（TON 虚拟机的字节码容器） |
| 本地测试 | `@ton/sandbox`、`@ton/test-utils` | `ton-contract-executor`（已废弃） | sandbox 提供 `Blockchain` 类模拟 TVM；test-utils 提供 Jest 断言 |
| 链上交互 | `@ton/ton`、`@ton/crypto` | `ton` CLI | `TonClient4` 连接 Testnet 或 mainnet（主网） |
| 部署 | Blueprint `run` 脚本 | `ton-cli` | 用 TypeScript 脚本发送部署消息 |
| 验证 | verifier.ton.org | tonscan.org、Actonscan | 比对链上合约代码与本地源码 |

`ton-contract-executor` 在 2023 年后已被 `@ton/sandbox` 取代，新项目不应再用。`func` 二进制和 Tolk 编译器是底层编译器；Blueprint 通过 `@ton-community/func-js` 在 Node.js 进程内调用 FunC 编译器，通常不需要手动安装二进制。Tolk 编译器已并入 Acton，`acton build` 直接出编译产物。

## 任务流案例：Jetton 代币合约全生命周期

用一个最小可运行的 Jetton 代币合约把上表中的工具串起来。Jetton 是 TON 的代币标准（TEP-74），对应以太坊的 ERC-20。完整流程：编写合约源码 → 编译为 Cell → 本地测试 → 调试 Trace → 部署到 Testnet → 链上验证。

需要说明的是：标准 Jetton 由 minter（铸造管理）和每用户一个的 wallet（余额账本）两个合约组成，wallet 侧的消息协议（`internal_transfer` 等）才由 TEP-74 标准化。本文为了聚焦工具链本身，示例合约只维护 `total_supply` 单账本，不部署 wallet 合约；生产实现请参考进阶路径给出的官方仓库。

### 1. 项目脚手架：Blueprint

Blueprint 是 TON 社区通用的项目脚手架，封装了目录约定、编译脚本、测试运行器和部署脚本。用 `npm create ton@latest` 创建项目：

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

`wrappers/` 是 Blueprint 的约定：每个合约配一个 TypeScript 包装器，封装编译入口、部署消息构造和 getter 调用。这样测试和部署脚本都通过同一个包装器调用合约，编译产物和调用逻辑不会散落在不同地方。`tests/` 默认用 Jest，配合 `@ton/sandbox` 和 `@ton/test-utils`。

### 2. 编写合约：FunC 与 Tolk

FunC（TON 函数式合约语言）是 TON 早期合约语言，语法接近 ML 家族；Tolk（TON 现代合约语言）是 2024 年起官方主推的替代语言，语法更接近 TypeScript。两者都编译到 TVM（TON 虚拟机）字节码。

以 FunC 为例，下面是一个完整可编译的单账本 minter——完整可运行是本文示例的前提，所以没有留下任何"此处省略"的部分：

```func
;; jetton_minter.fc
;; 单账本演示版 minter：只维护 total_supply，省略标准 Jetton 的 wallet 合约分发。
;; 生产实现参考 ton-blockchain/jetton-contract（wallet 分发、bounced 处理、元数据）。
#pragma version >=0.4.6;
#include "imports/stdlib.fc";

global int total_supply;
global slice admin_address;

() load_data() impure {
  var ds = get_data().begin_parse();
  total_supply = ds~load_coins();
  admin_address = ds~load_msg_addr();
}

() save_data() impure {
  set_data(begin_cell()
            .store_coins(total_supply)
            .store_slice(admin_address)
            .end_cell());
}

() recv_internal(int msg_value, cell in_msg_full, slice in_msg_body) impure {
  load_data();
  var cs = in_msg_full.begin_parse();
  cs~load_uint(8);                   ;; 消息 flags（含 bounced 标记）
  slice sender = cs~load_msg_addr();

  if (in_msg_body.slice_empty?()) {
    return ();
  }
  int op = in_msg_body~load_uint(32);
  int query_id = in_msg_body~load_uint(64);  ;; 读出以保持字段对齐，本合约不使用

  if (op == 0x642b7d07) {            ;; mint 操作码，与官方参考实现一致
    throw_unless(73, equal_slices_bits(sender, admin_address));
    int amount = in_msg_body~load_coins();
    total_supply += amount;
    save_data();
    return ();
  }
  if (op == 0) {                     ;; 部署确认或普通转账消息，直接接受
    return ();
  }
  throw(0xffff);                     ;; 未识别的操作码
}

int get_total_supply() method_id {
  var ds = get_data().begin_parse();
  return ds~load_coins();
}
```

几个值得说透的细节：

- `recv_internal` 是合约接收内部消息的入口，参数由 TVM 按固定布局压栈：余额、消息价值、完整消息（`cell` 类型）、消息体（`slice` 类型）。
- `0x642b7d07` 是 mint 操作码。TEP-74 只标准化 wallet 侧消息（`transfer` 是 `0xf8a7ea5`、`internal_transfer` 是 `0x178d4519`、`burn` 是 `0x595f07bc`），mint 操作码由 minter 实现自行定义——官方参考实现 [ton-blockchain/jetton-contract](https://github.com/ton-blockchain/jetton-contract) 取 `0x642b7d07`。网上不少教程把 `0x178d4519` 当 mint 码写，那是 `internal_transfer`，照抄会导致合约无法识别铸造消息。
- `throw_unless(73, ...)` 做权限校验，73 对应官方实现的 `error::not_owner`。没有这一行，任何人都能 mint。
- `load_coins()` 读写 TON 的变长金额编码，与 `store_coins()` 成对出现；状态持久化靠 `get_data()`/`set_data()`，`global` 变量只是让读写少传几个参数。
- 部署时 `stateInit` 的 data 部分按 `coins(0) + admin 地址` 布局写入，与 `load_data()` 的解析顺序一致。

Tolk 的等价写法语法更现代、类型更完整，Tolk v1.0 已于 2025 年 7 月发布，且是 Acton 的默认语言。对新项目，官方推荐直接用 Tolk（经由 Acton）；对存量 FunC 项目，FunC 仍被官方支持，没有废弃时间表，可以按团队节奏逐步迁移。下面的示例沿用 FunC，是为了展示 Blueprint 这条仍被大量教程使用的老链路。

### 3. 编译：func-js 与 Tolk 编译器

Blueprint 在 `wrappers/` 里调用 `@ton-community/func-js` 编译 FunC。把编译函数放到 `wrappers/compile.ts`：

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

  console.log('func-js version:', await compilerVersion());
  return Cell.fromBoc(Buffer.from(result.codeBoc, 'base64'))[0];
}
```

`compileFunc` 接收源码字符串（不是文件路径），返回 `codeBoc`（base64 编码的 TVM Cell）。`Cell.fromBoc` 把它解析成 `@ton/core` 的 `Cell` 对象，后续测试和部署都用这个对象。

Tolk 编译走 Acton：在 Acton 项目里执行 `acton build`，编译产物和缓存由工具链管理。想在 Node.js 进程内编译 Tolk，可以用 `@ton/tolk-js`（WASM 封装，仓库 ton-blockchain/tolk-js），API 风格与 `func-js` 类似。编译产物是 Cell 的二进制序列化（Bag of Cells，BoC），一个合约对应一个 Cell。

### 4. 本地测试：@ton/sandbox 与 @ton/test-utils

`@ton/sandbox` 提供 `Blockchain` 类，在本地进程内模拟 TVM 执行，不需要连接 Testnet。`@ton/test-utils` 给 Jest 加 TON 专用断言（如 `toEqual` 支持 `bigint`、`toHaveTransaction` 过滤交易）。

先补上包装器 `wrappers/JettonMinter.ts`，它把编译产物、`stateInit` 数据布局和 getter 调用封装成一个类：

```typescript
import { Address, Cell, Contract, ContractProvider, Sender,
         beginCell, contractAddress } from '@ton/core';
import { compileJettonMinter } from './compile';

export class JettonMinter implements Contract {
  constructor(
    readonly address: Address,
    readonly init: { code: Cell; data: Cell } | null,
  ) {}

  static async fromInit(admin: Address): Promise<JettonMinter> {
    const code = await compileJettonMinter();
    const data = beginCell().storeCoins(0).storeAddress(admin).endCell();
    return new JettonMinter(
      contractAddress(0, { code, data }),
      { code, data },
    );
  }

  async send(sender: Sender, args: { value: bigint }, body: Cell) {
    await sender.send({
      to: this.address,
      value: args.value,
      init: this.init,
      body,
    });
  }

  async getTotalSupply(provider: ContractProvider): Promise<bigint> {
    const stack = await provider.get('total_supply', []);
    return stack.readBigNumber();
  }
}
```

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

  it('should accept deploy confirmation message', async () => {
    const deployMsg = beginCell()
      .storeUint(0, 32)   // 空 op，合约直接接受
      .storeUint(0n, 64)  // queryId
      .endCell();

    const result = await minter.send(
      deployer.getSender(),
      { value: toNano('0.05') },
      deployMsg,
    );

    expect(result.transactions).toHaveTransaction({ exitCode: 0 });
    expect(await minter.getTotalSupply()).toEqual(0n);
  });

  it('should mint tokens when called by admin', async () => {
    const mintMsg = beginCell()
      .storeUint(0x642b7d07, 32)  // Mint opcode
      .storeUint(1n, 64)          // queryId
      .storeCoins(toNano('100'))  // amount
      .endCell();

    await minter.send(
      deployer.getSender(),
      { value: toNano('0.05') },
      mintMsg,
    );

    expect(await minter.getTotalSupply()).toEqual(toNano('100'));
  });

  it('should reject mint from non-admin with exit code 73', async () => {
    const attacker = await blockchain.treasury('attacker');
    const mintMsg = beginCell()
      .storeUint(0x642b7d07, 32)
      .storeUint(2n, 64)
      .storeCoins(toNano('100'))
      .endCell();

    const result = await minter.send(
      attacker.getSender(),
      { value: toNano('0.05') },
      mintMsg,
    );

    expect(result.transactions).toHaveTransaction({
      from: attacker.address,
      to: minter.address,
      exitCode: 73,   // error::not_owner
    });
    expect(await minter.getTotalSupply()).toEqual(0n);
  });
});
```

`blockchain.treasury('deployer')` 创建一个有初始余额的虚拟钱包，作为部署者和消息发送者。`blockchain.openContract` 把合约包装成可调用对象，`send` 发送内部消息，`getTotalSupply` 调用 getter（只读方法）。第三个用例值得专门写：权限校验只有在"非管理员调用被拒"的测试里才算验证过，只测管理员路径的合约不叫测过权限。

运行测试：

```bash
npx blueprint test
# 或直接用 Jest
npx jest tests/JettonMinter.spec.ts
```

### 5. 调试与 Trace 分析

TON 没有 FunC 源码级断点调试器。TVM 是栈式虚拟机，编译器在源码和指令之间做多对多的映射，源码行号到指令位置的对应关系不稳定，传统断点调试在工程上难以落地。调试主要靠 `@ton/sandbox` 的 Trace 输出和退出码分析。

`@ton/sandbox` 在 `send` 后返回交易结果，包含退出码、Gas（链上执行燃料费）消耗和发出的事件：

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

排查合约异常前，先把退出码表放在手边（完整表见 [docs.ton.org 的 Exit codes](https://docs.ton.org/v3/documentation/tvm/tvm-exit-codes)）：

- `0`：执行成功
- `2`：Stack underflow（栈上操作数不够，通常是 FunC 函数调用约定错误，比如参数数量不对）
- `4`：Integer overflow（整数超出表示范围或除零）
- `9`：Cell underflow（从消息体读取的位数超出实际内容——`load_*` 的顺序或字段宽度与 `beginCell()` 里 `store_*` 的写入不一致，最常见的错误）
- `-14`：Out of gas（Gas 耗尽，由 TVM 在 Gas 用尽时抛出）
- 其他正整数：合约用 `throw`/`throw_unless` 主动抛出的自定义错误码，比如本文演示合约的 73 表示非管理员调用 mint

合约行为异常时，先打印 `exitCode` 和 `events`，再对照 FunC 源码定位。复杂场景可以用 `@ton/sandbox` 的 `debug` 模式输出每条 TVM 指令，但输出量很大，适合在定位特定指令时开启。

### 6. 部署到 Testnet

Testnet 是 TON 的公开测试环境，代币无价值，用于上线前验证。mainnet 是生产环境。测试网资金有两个官方渠道：Acton 内置的 `acton wallet airdrop`，或浏览器 [Actonscan 的 faucet](https://testnet.actonscan.com/faucet)。

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

  // 1. 连接 Testnet v4 节点（端点取自 @ton/ton 的 createTestClient4）
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

  // 3. 构造合约实例（fromInit 内部调用编译函数并计算地址）
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

用官方验证器 [verifier.ton.org](https://verifier.ton.org)（TON Contract Verifier）：

1. 打开 verifier.ton.org，连接钱包
2. 输入合约地址（Testnet 或 mainnet 均可）
3. 上传合约源码文件（`jetton_minter.fc` 及所有 `#include` 的文件）
4. 选择编译器版本（与 `compilerVersion()` 输出一致）
5. 提交验证

验证通过后，浏览器（tonscan.org 或 Actonscan）上该合约页面会显示 Verified 标记并展示源码。dApp 前端团队通常把"源码已验证"作为集成前提：未验证的合约只暴露编译后的 Cell，集成方无法核对源码与链上行为是否一致，出问题时无法追溯责任。

## 工具选型与采用顺序

新团队接入 TON 合约开发，可以按下面这个顺序推进：

1. **新项目直接上 Acton + Tolk**：这是官方当前主推的组合，脚手架、编译、测试、部署、验证收进一个 CLI，学习成本更低，文档和示例也围绕它更新。用 `acton new` 起步，模板自带 Jetton、NFT、Counter 等参考实现。
2. **存量 FunC 项目继续用 Blueprint**：如果团队已有在跑的合约和测试，不必立刻迁移。Blueprint + FunC 依然稳定，社区教程多、排错资料全。
3. **评估迁移时机**：FunC 没有废弃时间表，官方也保留支持。等到新特性、团队人手或安全审计要求确实需要 Tolk 的更强类型系统时，再用 Acton 内置的 `acton func2tolk` 命令分批转换。

哪些团队不必急着上 Tolk：

- 合约已上线且稳定运行的团队：迁移成本高于收益
- 团队对 FunC 已熟练：FunC 仍被官方支持，没有废弃时间表
- 安全审计要求高的团队：存量合约在 FunC 上已通过审计，迁移会引入新的审计面

哪些团队可以先用 Tolk：

- 新项目、合约逻辑复杂、团队有 TypeScript 背景
- 愿意跟随生态演进、用官方新工具链起步的早期项目

## 常见问题与错误排查

### FunC 编译报 `undefined function`

原因：`#include` 路径错误或源码未传入 `sources`。`compileFunc` 的 `sources` 是一个 `{ [filename]: content }` 字典，所有依赖文件都要手动加入，不会自动从磁盘读取。

### @ton/sandbox 测试报 `exit code 9`

原因：消息体 Cell 序列化顺序与合约 `load_*` 调用顺序不匹配。用 `beginCell()` 构造消息时，`storeUint`、`storeCoins`、`storeAddress` 的调用顺序和字段宽度必须与 FunC 中 `load_uint`、`load_coins`、`load_msg_addr` 的顺序完全一致。改完序列化代码后，先在测试里打印完整的 `in_msg_body` 解析结果再定位差异。

如果测试报 `exit code -14`，问题不在消息布局，而是 Gas 用尽：检查测试发送的 `value` 是否过低，或合约消息处理里是否有意外的大循环。

### Testnet 部署后合约无响应

排查顺序：

1. 用 tonscan.org（Testnet）查合约地址是否已上链
2. 检查部署消息的 `value` 是否足够覆盖 Gas（建议 `toNano('0.05')` 以上）
3. 检查钱包余额是否足够（用 `acton wallet airdrop` 或 Actonscan faucet 领测试币）
4. 用 `TonClient4` 的 `getAccount` 查合约状态，确认 `state` 是否为 `active`

### verifier 验证失败

原因：编译器版本不匹配或源码有改动。在 `wrappers/` 中打印 `compilerVersion()`，用相同版本重新验证。如果合约用了 `#include`，确认所有 include 文件都已上传。

### Gas 消耗超预期

TON 的 Gas 按 TVM 指令计费。用 `@ton/sandbox` 的 `result.transactions[0].description.computePhase.gasUsed` 查看具体消耗。常见优化方向：

- 减少 `dict` 操作（每次 `lookup` 消耗较高）
- 用 `int` 替代 `cell` 存储小数据
- 避免在 `recv_internal` 中做重计算，能放到 getter 里的逻辑不要写进消息处理（getter 在链下调用时不消耗 Gas，消息处理则按 TVM 指令计费）

## 自测题

1. Blueprint、FunC 编译器、@ton/sandbox 三者的职责边界分别是什么？

   <details>
   <summary>查看答案</summary>

   - Blueprint 管项目脚手架、目录约定、编译/部署脚本编排
   - FunC 编译器把 FunC 源码编译为 TVM Cell
   - @ton/sandbox 在本地进程内模拟 TVM 执行，提供 `Blockchain` 类做单元测试
   - 三者不互相替代——Blueprint 调用编译器，编译器输出 Cell 给 sandbox 加载

   </details>

2. `compileFunc` 返回的 `codeBoc` 是什么格式？如何转成 `Cell` 对象？

   <details>
   <summary>查看答案</summary>

   `codeBoc` 是 base64 编码的 TVM Cell（Bag of Cells，BoC 二进制格式）。
   转换方法：`Cell.fromBoc(Buffer.from(result.codeBoc, 'base64'))[0]`

   </details>

3. `@ton/sandbox` 的 `blockchain.treasury` 和 `blockchain.openContract` 分别做什么？

   <details>
   <summary>查看答案</summary>

   - `blockchain.treasury('deployer')` 创建一个有初始余额的虚拟钱包合约，作为部署者和消息发送者
   - `blockchain.openContract` 把合约包装成可调用对象，提供 `send`（发消息）和 getter 调用方法

   </details>

4. 合约部署到 Testnet 后，如何用 `TonClient4` 查询合约 getter？

   <details>
   <summary>查看答案</summary>

   用 `TonClient4` 连接 Testnet 节点，`client.open(contract)` 打开合约实例后调用 getter 方法；或用 `client.runMethod` 直接调用合约的 `method_id` 方法。

   </details>

5. TVM 退出码 `-14` 和 `9` 分别代表什么？排查方向有什么不同？

   <details>
   <summary>查看答案</summary>

   - `-14` 是 Out of gas：Gas 耗尽，排查方向是发送的 `value` 是否够、消息处理里是否有大循环
   - `9` 是 Cell underflow：消息体读取越界，排查方向是 `store_*` 写入与 `load_*` 读取的顺序和字段宽度是否一致
   - 一个是资源问题，一个是序列化问题，两者的修复位置完全不同

   </details>

6. tonverifier 验证合约时，需要提交哪些文件？验证的是什么？

   <details>
   <summary>查看答案</summary>

   提交合约源码文件（`jetton_minter.fc` 及所有 `#include` 的文件），选择与 `compilerVersion()` 一致的编译器版本。验证的是本地源码编译后的 Cell 与链上合约的 Cell 是否一致。

   </details>

## 动手练习

### 练习一：从零跑通 Jetton 合约全生命周期

按本文"任务流案例"一节逐步操作，每一步都在你自己的机器上执行。跑通后回答：

1. `npm create ton@latest` 创建项目后，`contracts/`、`wrappers/`、`tests/` 三个目录里各有什么文件？
2. `compileFunc` 编译时如果报 `undefined function`，你排查的顺序是什么？
3. 用 `@ton/sandbox` 的 `result.transactions[0].description.computePhase` 查看部署交易的 Gas 消耗和退出码。退出码是 0 吗？如果不是，对照退出码表定位原因。

### 练习二：补测试并对比 @ton/sandbox 和 Testnet 的行为差异

在练习一的项目里补两个测试用例：

1. **错误操作码**：发一个 `op = 0xdeadbeef` 的消息，断言返回的退出码是 `0xffff`（本文演示合约对未识别操作码的行为）。
2. **连续 mint 后查总量**：连续发 3 次 mint 消息（每次 mint 100），断言 `getTotalSupply()` 返回 300。

跑通后，把同一个合约部署到 Testnet，用 `TonClient4` 调用同样的方法。@ton/sandbox 的本地测试和 Testnet 远端调用的 Gas 消耗是否一致？如果不一致，差了多少？搞清楚差异来源——是 sandbox 的 Gas 计费模型简化了某些 TVM 指令，还是 Testnet 上合约存储状态和本地新部署的初始状态不同。

### 练习三：把 Jetton minter 从 FunC 改写成 Tolk（或反过来）

如果你用 FunC 写了练习一的合约，现在用 Tolk 重写同一个逻辑。完成后对比：

1. 两版代码行数差多少？Tolk 省了哪些 FunC 的样板代码？
2. Tolk 的编译产物的 Cell 大小和 FunC 版差多少？用 `Cell.fromBoc` 解析后对比。
3. Tolk 生成的 `.cell` 文件能不能被 FunC 的 `compileFunc` 解析？反过来呢？

## 进阶路径

- **Jetton 标准实现**：读官方参考实现 [ton-blockchain/jetton-contract](https://github.com/ton-blockchain/jetton-contract)，理解 minter → wallet → 用户余额三层的消息传递——本文演示版省略的 wallet 分发、bounced 消息回滚都在这里。标准文档入口见 [docs.ton.org 的合约标准总览](https://docs.ton.org/contracts/standard/overview)。该仓库的 `sandbox_tests` 目录有成套的正负向测试，是写权限和异常测试的现成参照。
- **TVM 底层**：读 [TVM 概览](https://docs.ton.org/v3/documentation/tvm/tvm-overview)，理解栈式虚拟机、Continuation 和 Gas 计费模型。关键概念：TVM 一条指令的 Gas 由指令类型和操作数大小共同决定——`load_uint(256)` 比 `load_uint(32)` 贵，主因是读取的 cell 数据更多，指令本身的复杂度差异不大。
- **安全审计**：演示合约只做了最简单的权限校验（`throw_unless(73, ...)`）。标准 Jetton 至少还要处理：bounced 消息（mint 后 wallet 侧失败时回滚 total_supply）、消息体的严格字段解析、admin 变更路径。把 jetton-contract 仓库里 `error::not_owner`、`error::wrong_op` 这些错误码的用法读一遍，比自己发明错误码可靠。
- **Tolk 迁移**：Acton 内置 `acton func2tolk` 命令，底层调用官方 `@ton/convert-func-to-tolk` 包，迁移流程见 [Acton 的 func2tolk 迁移指南](https://ton-blockchain.github.io/acton/docs/agent-skills/func2tolk)。机械转换完成后仍需人工核对消息处理语义是否一致，再分批替换。早期独立的 ton-blockchain/tolk 仓库已不存在，遇到引用它的旧教程，链接会 404。

## 资料口径说明

1. **Acton**：官方工具链，仓库 [ton-blockchain/acton](https://github.com/ton-blockchain/acton)，v1.0.0 发布于 2026 年 5 月 11 日（GitHub Releases）。Acton 迭代很快，安装方式和命令用法以仓库 README 为准。
2. **Tolk**：Tolk v1.0 于 2025 年 7 月发布（npm 包 `@ton/tolk-js` 1.0.0，2025-07-07）。Tolk 编译器已并入 Acton，`@ton/tolk-js` 提供 WASM 版本。
3. **mint 操作码**：TEP-74 标准化的是 wallet 侧消息（`transfer` `0xf8a7ea5`、`internal_transfer` `0x178d4519`、`burn` `0x595f07bc`）；mint 操作码由 minter 实现自行定义，官方参考实现 jetton-contract 取 `0x642b7d07`，旧版 token-contract 取十进制 21。本文示例与新版参考实现一致。
4. **npm 包版本**：`@ton/ton`、`@ton/core`、`@ton/sandbox`、`@ton/test-utils`、`@ton-community/func-js` 以 npm 查询为准；Testnet 端点 `testnet-v4.tonhubapi.com` 取自 `@ton/ton` 源码的 `createTestClient4`。FunC 编译器的具体版本号请以 `compilerVersion()` 的输出为准，验证源码时用同一版本。
5. 本文仅供学习参考，不构成投资或技术实施建议。合约部署到 mainnet（主网）前，请完成完整测试和安全审计。
