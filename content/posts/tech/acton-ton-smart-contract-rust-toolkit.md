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
- [快速上手](#快速上手)
- [核心能力](#核心能力)
  - [编译与测试](#编译与测试)
  - [部署与生态](#部署与生态)
- [任务流案例：NFT 合约从创建到验证](#任务流案例nft-合约从创建到验证)
- [FunC、Tact 与 Tolk](#func-tact-与-tolk)
- [适用场景与采用顺序](#适用场景与采用顺序)
- [决策建议](#决策建议)
- [常见问题与排查](#常见问题与排查)

## 项目概览

Acton 是 [ton-blockchain 组织](https://github.com/ton-blockchain)推出的 TON 智能合约全生命周期开发工具链，Rust 编写。本文基于 Acton v0.X（截至撰写时仓库尚未发布稳定版本号，命令与产物路径以仓库 README 为准）。TON（The Open Network）由 Telegram 团队发起，现由 TON Foundation 维护；智能合约使用 FunC 语言（TON 官方低层合约语言，类 C 语法）编写，运行在 TON Virtual Machine（TVM）上。

TON 合约开发长期存在工具链碎片化：开发者需要同时管理 `func`（FunC 编译器）、`fift`（TVM 字节码工具）、`tonos-cli`（钱包操作）和多个第三方测试框架——这些工具的命令风格、配置文件和错误信息彼此不兼容。一套 Jetton 合约的开发链路里，编译用 `func`，本地测试用 `@ton/sandbox`，部署用 `tonos-cli`，验证用 tonverifier.app 的手动上传——四次上下文切换，每次都要确认"当前用的是哪个网络、哪个钱包、哪个编译器版本"。

Acton 用 `acton` 一个二进制替代 `func`/`fift`/`tonos-cli` 等多个工具，覆盖从项目脚手架到链上验证的全部环节。四个命令组按职责分开：

| 分组 | 命令 | 职责 |
|------|------|------|
| 项目创建 | `acton new` | 脚手架与模板 |
| 编译测试 | `acton build`、`acton test`、`acton lint`、`acton fmt`、`acton debug` | 编译、测试、检查、调试 |
| 部署运维 | `acton script`、`acton deploy`、`acton verify` | 脚本执行、网络部署、源码验证 |
| 语言与生态支持 | FunC、Tact、Tolk、TypeScript 绑定 | 多语言与 dApp 支持 |

## 快速上手

下面五条命令串起"安装—创建—编译—测试—部署"的完整链路。Acton 工具链自身编译需要 Rust 1.70+，但用户项目本身不强制依赖 Rust——FunC/Tact 合约源码由 Acton 内置编译器处理，Rust 仅用于编写原生测试用例。

```bash
# 安装（Acton 工具链自身编译需要 Rust 1.70+）
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

跑通这条链路后再往下看核心能力，会更容易把每条命令对应到具体子系统。

## 核心能力

### 编译与测试

`acton new` 是项目脚手架入口，支持 FunC 合约和 Tact 合约两种模板（Tact 是 TON 上的高级合约语言，编译到 FunC）。模板里预置了 `sources/contracts/`、`tests/` 和 `Acton.toml` 三件套，新建后即可直接 `acton build`。

编译环节由 `acton build` 负责——FunC 或 Tact 源码 → `.tvc`（TVM 字节码文件）。测试环节由 `acton test` 承担：Rust 原生测试运行器，支持 fork 模式（模拟 TON 区块链状态）、gas 快照、覆盖率统计、mutation testing 和模糊测试。`acton lint` 和 `acton fmt` 分别做代码检查和格式化，`acton debug` 提供断点调试，配合浏览器版测试 UI 查看调用栈和日志。

`acton test --ui` 启动本地 Web 页面，展示失败用例、调用轨迹和详细日志。调试复杂合约逻辑时比命令行输出直观得多——你能看到具体哪条 TVM 指令触发了退出码 -14，而不是在终端里 grep 几百行文本。

### 部署与生态

部署侧三条命令覆盖"脚本—上链—验证"的完整运维链路。`acton script` 运行合约脚本，用于调用合约方法或执行部署前置操作；`acton deploy` 将合约部署到指定网络（testnet 或 mainnet）；`acton verify` 在 TON 区块链浏览器上执行合约源码验证，通过后浏览器显示源码链接，用户可以核对合约逻辑。

生态侧的选择是 Rust 而非 Node.js 或 Python 的原因很实际：合约项目规模变大后，测试用例从几十条涨到上万条，Node.js 的 `@ton/sandbox` 在运行时是 TypeScript 编译产物，大型测试套件的启动和运行时间随用例数线性增长。Rust 原生测试运行器在万级用例下编译和执行的耗时增长曲线比解释型语言平缓得多（具体数字见仓库 README 基准数据，本文不展开）。

语言覆盖上，Acton 原生支持 Tolk——TON 生态的另一种合约开发语言（类 Rust 语法）。内置支持包括语法高亮配置、编译器集成和测试框架对接，已在用 Tolk 的团队无需切换工具。dApp 开发方面，Acton 自动生成 TypeScript 绑定文件，配合 `acton script` 可以快速编写与合约交互的前端脚本——前端调用合约方法时有类型提示和自动补全，不用对照 ABI 手写每个方法签名。

## 任务流案例：NFT 合约从创建到验证

下面用一个 NFT（Non-Fungible Token，非同质化代币）合集合约，展示一次完整任务如何流过 Acton 各子系统。NFT 合约涉及铸造、转账和元数据查询——刚好覆盖消息处理、存储读写和 getter 这三条最常用的合约路径。每一步都标注了对应的 Acton 命令组（项目创建→编译测试→部署运维）。

### 1. 创建项目

```bash
acton new nft_collection --template tact
cd nft_collection
```

选择 Tact 模板的原因是 NFT 合约涉及结构体和接口，Tact 的面向对象语法比 FunC 的栈操作更适合表达这类抽象。

### 2. 编写合约

在 `sources/contracts/nft_collection.tact` 中定义 `NFTCollection` 合约，包含 `mint`、`transfer`、`get_item_info` 三个方法。下面是合约骨架（仅展示接口和关键逻辑，完整实现需补全 NFT 标准 TL-B 序列化和存储读写）：

```tact
// sources/contracts/nft_collection.tact
struct ItemInfo {
    index: Int as uint256;
    owner: Address;
    content: String;
}

contract NFTCollection {
    owner: Address;
    nextIndex: Int as uint256;
    royalty: Int as uint16; // 百分比，例如 5 表示 5%

    init(owner: Address, royalty: Int) {
        self.owner = owner;
        self.nextIndex = 0;
        self.royalty = royalty;
    }

    // 铸造新 NFT，仅 collection owner 可调用
    receive("mint") {
        let ctx = context();
        require(ctx.sender == self.owner, "Not authorized");
        let itemIndex = self.nextIndex;
        self.nextIndex = self.nextIndex + 1;
        // 实际实现里这里会向 item 合约发送 internal message
        // 本文省略 item 合约部署逻辑
        reply("Minted: " + itemIndex.toString().asComment());
    }

    // 转移 NFT 所有权，由 item 合约回调触发
    receive(msg: Transfer) {
        let ctx = context();
        require(ctx.sender == self.owner, "Not authorized");
        // 更新 owner 记录、转发给新 item 合约
        reply("Transferred");
    }

    // Getter 方法，供链下查询当前 item 信息
    get fun get_item_info(index: Int): ItemInfo {
        // 实际实现从 storage 读取
        return ItemInfo { index: index, owner: self.owner, content: "" };
    }
}

message Transfer {
    from: Address;
    to: Address;
    itemId: Int as uint256;
}
```

这段代码展示了 Tact 的几个关键特性：`struct` 定义复合数据、`contract` 内部用 `receive` 处理入站消息、`get fun` 暴露链下可调用的 getter、`Int as uint256` 显式标注 TL-B 编码宽度。FunC 实现等价逻辑需要手动操作栈和 builder/slice，代码量会显著增加。

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

### 7. 自测问题

读完上面的任务流后，试着回答下面这个问题，检验你是否理解了 Acton 各子系统的边界：

> 如果 `acton verify` 失败，最可能的原因是什么？请按"编译器版本—源码完整性—参数顺序"三个维度各给一个具体场景，并说明对应排查命令。

参考思路：编译器版本不一致（本地 Tact 编译器与浏览器端版本不同，可用 `acton build --show-compiler-version` 对比）、源码未提交完整（`sources/` 下有未跟踪的 include 文件，可用 `git status` 检查）、参数顺序错误（`Acton.toml` 里的 `init_data` 字段顺序与合约 `init` 函数签名不匹配，可用 `acton debug --trace-init` 打印实际拼装的 cell）。能说出这三类，说明你已经把"编译—部署—验证"这条链路的故障点理清了。

## FunC、Tact 与 Tolk

TON 智能合约主要有三种开发语言，Acton 对三者都提供支持。三种语言并存的原因比各自语法更重要：FunC 是 TVM 原生语言，随 TON 主网一起发布，能直接控制栈和 cell；Tact 和 Tolk 是后来为降低开发门槛推出的高级语言，分别走 TypeScript 风格和 Rust 风格。官方文档：[TON 文档站 FunC 章节](https://docs.ton.org/v3/documentation/smart-contracts/func/overview)、[tact-lang.org](https://tact-lang.org/)、[ton-blockchain/tolk 仓库](https://github.com/ton-blockchain/tolk)。

**FunC** 是 TON 官方低层合约语言，语法接近 C，需要手动管理栈操作。主网标准合约（钱包、Jetton、NFT）最初都用 FunC 编写，生态里的安全审计工具和 gas 基准也以 FunC 为参照。选它意味着能直接复用主网已有的合约逻辑和审计报告，代价是开发速度慢——一个 Jetton 合约在 FunC 里要手写 cell 序列化、消息解析和 getter 方法注册，代码量比 Tact 大 2-3 倍。

**Tact** 是编译到 FunC 的高级语言，语法接近 TypeScript，支持结构体、接口和面向对象模式。选择 Tact 通常是因为团队需要更快出合约——同样的 Jetton 逻辑，Tact 用 `contract` + `receive` + `get fun` 三块就能表达，FunC 需要手动管理所有栈操作。代价是生成的 FunC 中间产物在极端 gas 优化场景下不如手写精细（实际差额通常在 5-15%，取决于合约复杂度）。

**Tolk** 是 ton-blockchain 组织维护的较新语言，类 Rust 语法，定位在 FunC 和 Tact 之间：比 FunC 可读性好、比 Tact 更靠近 TVM 底层。Tolk 仍在快速迭代（当前 v0.7+），适合熟悉 Rust 又需要精确控制 TVM 行为的团队。暂时不建议把存量和已审计的 FunC 合约迁移到 Tolk——等 v1.0 稳定版发布后再评估。

三种语言的选择不涉及"哪个更好"，只看团队侧重点：gas 极端敏感、已有 FunC 代码库的团队选 FunC；追求开发速度、新项目为主选 Tact；熟悉 Rust 且需要更细粒度控制选 Tolk。

## 适用场景与采用顺序

### 适用场景

Acton 的价值在不同项目阶段不一样。下面按场景列出匹配度和理由：

- **从零启动 TON 合约项目**：`acton new` 脚手架和统一 CLI 省掉了 funk/fift/tonos-cli 三套工具的选择和配置时间。你不需要在读三个仓库的 README 之后才决定"到底该装哪个"——一条 `cargo install acton` 覆盖全部。
- **需要在 testnet 和 mainnet 之间频繁切换**：`acton deploy --network` 把网络切换从"改配置文件 + 换 RPC 地址 + 换钱包"收束成一条参数。部署脚本里不再需要写 `if (network === 'mainnet')` 的分支判断。
- **对 gas 消耗有回归检测需求**：`acton test` 的 gas 快照让"改一行逻辑是否多烧了 0.01 TON"变成可量化的 CI 检查。改合约逻辑之后跑一遍 `acton test`，gas 快照对比直接告诉你是否有回归——不需要手动部署到 testnet 再查链上记录。
- **Tact/FunC 合约需要源码验证**：`acton verify` 一条命令把源码+编译参数提交到浏览器端重新编译并比对，省掉了手动上传文件、选编译器版本、等结果的步骤。
- **dApp 前端需要类型安全的合约绑定**：Acton 自动生成的 TypeScript 绑定让前端调用合约方法时有完整的类型提示——`minter.getTotalSupply()` 的返回值类型是 `bigint` 而不是 `any`。

反过来，如果你的场景只是"用 Tact 写一个 demo 合约、不部署、不验证"，Tact 自带工具链已经够用，装 Acton 反而多学一套命令。

### 采用顺序

**新项目：** 直接使用 `acton new` 创建项目，从第一天就跑通完整工具链，避免后续迁移成本。

**老项目迁移：** 建议按以下顺序逐步替换：

1. 先用 `acton build` 替换 `func`/`fift`，验证编译产物一致
2. 再用 `acton test` 替换原有测试框架，先跑通现有用例，再逐步引入 fork 模式和 gas 快照
3. 最后用 `acton deploy` 和 `acton verify` 替换部署脚本，统一运维入口

## 决策建议

三组团队可以从 Acton 拿到确定收益，另外两组暂时不必。

**建议现在上的：**

- **新 TON 项目组**：从 `acton new` 起步，第一天就把编译、测试、部署、验证串成一条链路，比先装 funk/fift/tonos-cli 再迁移省一轮成本。
- **频繁切换 testnet/mainnet 的团队**：`acton deploy --network` 省掉的是每次部署前人工确认"这次该用哪个 RPC、哪个钱包"的心智开销。部署脚本数量从 N 个网络 × M 个合约收敛到 1 个。
- **需要 gas 回归检测的团队**：把 `acton test` 接进 CI，每次 PR 自动跑 gas 快照对比。有人改了一行排序逻辑导致 mint gas 涨了 15%，CI 直接在 PR 里标出来，不用等到链上部署后发现。

**可以暂缓的：**

- **已有成熟的 CI/CD 合约部署流程的团队**：如果 funk/fift/tonos-cli 已经被封装进自动化脚本并且稳定运行了一段时间，切换成 `acton` 的边际收益有限。建议等到下一次工具链大版本升级（例如 Tact 2.0 或 Tolk 1.0 发布）时再评估。
- **只用 Tact 写合约、不涉及部署和验证的单人项目**：Tact 自带工具链覆盖了编译和本地测试，够用。等你的合约要上 testnet 做多轮部署验证时再来装 Acton，学习曲线不会白费。

**决策检查清单**：

在决定是否切到 Acton 之前，回答下面三个问题：

- 你的团队现在是不是同时维护 funk、fift 和 tonos-cli 三套工具的配置和版本？
- 你是不是每周至少部署一次合约到 testnet 或 mainnet？
- 你的 CI 里有没有 gas 回归检测——或者说，上一次有人改了合约逻辑，你知道 gas 变化了吗？

三个问题中答"是"越多，迁移到 Acton 的收益越明确。答了两个"否"，先不要动——继续用现有工具链，等上面三个条件发生变化再评估。

## 常见问题与排查

### 验证失败的常见原因

`acton verify` 失败时，按下面三类原因逐一排查：

- **编译器版本不一致**：本地用的 Tact/FunC 编译器版本与浏览器端重新编译时使用的版本不同，导致字节码差异。排查命令：`acton build --show-compiler-version`，把输出与浏览器端声明的版本对比。
- **源码未提交完整**：`sources/` 下有未跟踪的 include 文件或 `.tact` 中引用的 stdlib 路径在提交时被 `.gitignore` 排除，浏览器端拿不到完整源码。排查命令：`git status` 检查未跟踪文件，`acton verify --dry-run` 本地模拟浏览器端编译。
- **参数顺序错误**：`Acton.toml` 里的 `init_data` 字段顺序与合约 `init` 函数签名不匹配，拼装出的 cell 与链上部署时的 cell 不一致。排查命令：`acton debug --trace-init` 打印实际拼装的 cell，与部署时的 `init_data` cell 逐字节对比。

### FAQ

**Q1：`acton build` 产物与 `func` 直接编译的结果不一致怎么办？**

先对比编译器版本（`acton build --show-compiler-version` 与 `func -V`），再对比编译选项（`-O` 优化级别、`-c` 配置文件路径）。Acton 默认开启的优化级别可能与你的 `func` 命令不同，把两边对齐后产物应当一致；若仍不一致，到 Acton 仓库提 issue 附上最小复现用例。

**Q2：`acton test` 的 fork 模式如何配置 RPC 节点？**

在 `Acton.toml` 的 `[test.fork]` 段配置 `rpc_url` 和 `block_height`（留空则 fork 最新区块）。testnet 和 mainnet 的 RPC 节点列表参考 [TON 文档](https://docs.ton.org/v3/guidelines/nodes/running-nodes)，建议用自建节点避免公共节点的速率限制。

**Q3：Acton 支持 Tolk 的哪些版本？**

Acton 跟随 [ton-blockchain/tolk](https://github.com/ton-blockchain/tolk) 主线，通常在 Tolk 发布新版本后一到两周内适配。若你的项目锁定了某个 Tolk 旧版本，在 `Acton.toml` 的 `[toolchain]` 段指定 `tolk = "0.7.x"`，Acton 会下载对应版本而不是用内置最新版。

**Q4：`acton deploy` 部署到 mainnet 时钱包余额不足会怎样？**

Acton 会在签名前查询钱包余额，若不足以支付部署交易的 gas，会直接报错退出，不会广播半签名交易。报错信息里会给出预估所需 gas 和当前余额的差值，补足后重跑即可。

**Q5：Acton 能否与现有的 Blueprint 脚手架项目共存？**

可以。Acton 读取的是 `Acton.toml`，Blueprint 读取的是 `package.json` 和 `wrangler.toml`，两套配置互不干扰。但建议在同一项目里只保留一套工具链，避免 `build/` 目录产物冲突。迁移时先用 `acton build` 验证产物与 Blueprint 一致，再逐步替换。

## 动手练习

下面三个练习覆盖 Acton 的核心链路，从基础操作到故障排查逐步递进。建议按顺序完成——第一个半小时能做完，第三个需要你对照真实项目改配置。

### 练习一：跑通 NFT 合约全生命周期

按本文"任务流案例"一节走一遍：创建项目 → 编写合约骨架 → 编译 → 部署到 testnet → 验证。完成后回答：

1. `acton build` 的产物路径和文件名是什么？
2. `acton deploy --network testnet` 部署成功后输出的合约地址，在 tonscan.org（testnet 版本）上能查到吗？
3. `acton verify` 有没有报错？如果有，对照"常见问题与排查"里的三类原因定位。

### 练习二：给合约补测试并读取 gas 快照

在练习一的项目 `tests/` 目录下补三个测试用例：

1. 铸造成功：mint 操作后 `nextIndex` 加 1
2. 非 owner 铸造失败：用另一个钱包地址发 mint 消息，验证返回码非 0
3. 连续铸造 gas 对比：连续 mint 3 次，记录每次 `gasUsed`——第二次和第三次是否一致？如果不一致，找出 FunC 里导致 gas 差异的指令（提示：检查 `total_supply` 存储写入操作是否在第二次之后被 TVM 缓存）

完成后，你能解释为什么同样的操作在链上的 gas 消耗可能不同——这涉及 TVM 的存储缓存机制和 cell 序列化的增量成本。

### 练习三：把练习一的合约从 Tact 改写成 FunC（或反过来）

如果你用 Tact 写了练习一的合约，现在用 FunC 重写同一个逻辑（只实现 `mint` 和 `get_item_info`）。反过来也一样。完成后对比：

1. 两版代码行数差多少？
2. FunC 版的 `acton test` 跑完，gas 消耗比 Tact 版高还是低？差多少？
3. 你在 FunC 版里手写了哪些 Tact 编译器自动生成的东西（如 getter 方法注册、TL-B 序列化）？

这个练习让你直观感受高级语言编译器的"隐形成本"——Tact 帮你省掉的代码，编译器替你写了，但这些自动生成的 FunC 中间代码在极端场景下可能多消耗 gas。

## 自测清单

用"能/不能"回答下面 8 个问题，答"不能"的条目就是该回去重读的章节。

| # | 自测项 | 答"不能"时回看 |
|---|--------|---------------|
| 1 | 能说出 Acton 解决了 TON 工具链碎片化中的哪三个具体痛点 | [项目概览](#项目概览) |
| 2 | 能用一条命令从零搭建 FunC 项目并编译出 `.tvc` 文件 | [快速上手](#快速上手) |
| 3 | 能解释 `acton test` 为什么用 Rust 实现而不是 Node.js——以及这对万级测试用例的编译耗时意味着什么 | [编译与测试](#编译与测试) |
| 4 | 能描述一次 NFT 合约从 `acton new` 到 `acton verify` 的完整链路中，每个命令输入什么、输出什么 | [任务流案例](#任务流案例nft-合约从创建到验证) |
| 5 | 能区分 FunC、Tact、Tolk 三者的适用场景和各自的 gas 代价 | [FunC、Tact 与 Tolk](#func-tact-与-tolk) |
| 6 | 能给一个已有 Blueprint 项目写出三阶段的 Acton 迁移计划 | [采用顺序](#采用顺序) |
| 7 | 能在 `acton verify` 失败时按"编译器版本→源码完整性→参数顺序"的顺序排查 | [常见问题与排查](#常见问题与排查) |
| 8 | 能解释为什么同一个 mint 操作连着跑两次，gas 消耗可能不同 | [动手练习](#动手练习) |

## 进阶路径

读到这里已经掌握了 Acton 的操作面。如果想深入 TON 合约开发的工程体系，按下面的顺序推进：

1. **读 TON 标准合约源码**：Jetton（TEP-74）和 NFT（TEP-62）的标准实现是理解 TON 合约设计模式的最佳入口。去 [ton-blockchain/token-contract](https://github.com/ton-blockchain/token-contract) 仓库，先读懂 `jetton-minter.fc` 的消息路由逻辑，再对照本文的 Tact 版本看编译器做了哪些转换。
2. **理解 TVM 的存储与 gas 模型**：[TON 文档的 TVM 章节](https://docs.ton.org/v3/documentation/tvm/tvm-overview) 解释 cell 持久化存储的读写成本——为什么 `store_uint` 和 `load_uint` 的 gas 不等价、为什么合约长期未触达后第一次调用 gas 更高（存储费累积）。
3. **用 `acton debug` 深入 TVM 指令级**：打开 `acton debug --ui`，跑一遍 mint 操作，在浏览器里逐条看 TVM 指令执行。跟踪一次 `recv_internal` 调用中消息解析、cell 操作和存储写入的完整指令序列。这比任何文档都更直接地建立"FunC 代码→TVM 指令→Gas 消耗"的映射直觉。
4. **引入形式化验证**：Acton 预留了 `acton verify` 的形式化验证接口（区别于链上源码验证的 `acton verify`），但目前仍在开发中。可以先用 [ton-blockchain/tolk-fuzzer](https://github.com/ton-blockchain/tolk-fuzzer) 对 FunC 合约做模糊测试，覆盖消息格式异常、边界值和并发场景。

每一步都对应一个具体的工程能力——从"会用工具"到"理解工具背后的虚拟机"再到"能用工具验证合约安全性"。不需要一次走完，但建议至少走到第二步再开始写生产合约。
