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

Acton 是 [ton-blockchain 组织](https://github.com/ton-blockchain)推出的 TON 智能合约全生命周期开发工具链，使用 Rust 编写。本文基于 Acton v0.X（截至撰写时仓库尚未发布稳定版本号，命令与产物路径以仓库 README 为准）。TON（The Open Network）由 Telegram 团队发起，现由 TON Foundation 维护；其智能合约使用 FunC 语言（TON 官方低层合约语言，类 C 语法）编写，运行在 TON Virtual Machine（TVM，TON 虚拟机）上。

TON 合约开发长期存在工具链碎片化问题：开发者需要同时管理 `func`（FunC 编译器）、`fift`（TVM 字节码工具）、`tonos-cli`（钱包操作）和多个第三方测试框架，这些工具的命令风格、配置文件和错误信息彼此不兼容。Acton 用 `acton` 一个二进制替代 `func`/`fift`/`tonos-cli` 等多个工具，覆盖从项目脚手架到链上验证的全部环节。

Acton 的 CLI 命令按职责分为四组：

| 分组 | 命令 | 职责 |
|------|------|------|
| 项目创建 | `acton new` | 脚手架与模板 |
| 编译测试 | `acton build`、`acton test`、`acton lint`、`acton fmt`、`acton debug` | 编译、测试、检查、调试 |
| 部署运维 | `acton script`、`acton deploy`、`acton verify` | 脚本执行、网络部署、源码验证 |
| 语言与生态支持 | FunC、Tact、Tolk、TypeScript 绑定 | 多语言与 dApp 支持 |

## 快速上手

下面这段命令把"安装—创建—编译—测试—部署"五个动作串成一条链路，先建立体感再展开能力细节。Acton 工具链自身编译需要 Rust 1.70+，用户项目本身不强制依赖 Rust——FunC/Tact 合约源码由 Acton 内置编译器处理，Rust 仅在编写原生测试用例时使用。

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

`acton new` 是项目脚手架入口，支持 FunC 合约和 Tact 合约两种模板（Tact 是 TON 上的高级合约语言，编译到 FunC）。模板里已经预置了 `sources/contracts/`、`tests/` 和 `Acton.toml` 三件套，新建后即可直接 `acton build`。

编译环节由 `acton build` 负责，把 FunC 或 Tact 源码编译为 `.tvc`（TVM 字节码文件）。测试环节由 `acton test` 承担，它是一个 Rust 原生测试运行器，支持 fork 模式（模拟 TON 区块链状态）、gas（链上执行燃料费）快照、覆盖率统计、mutation testing（变异测试）和模糊测试。`acton lint` 和 `acton fmt` 分别做代码检查和格式化，`acton debug` 提供断点调试，配合浏览器版测试 UI 查看调用栈和日志。

`acton test --ui` 会启动一个本地 Web 页面，展示失败的测试用例、调用轨迹（trace）和详细日志。调试复杂合约逻辑时比命令行输出更直观。

### 部署与生态

部署侧的三条命令覆盖了"脚本—上链—验证"的完整运维链路。`acton script` 运行合约脚本，用于调用合约方法或执行部署前置操作；`acton deploy` 将合约部署到指定网络（testnet（测试网）或 mainnet（主网））；`acton verify` 在 TON 区块链浏览器上执行合约源码验证，验证通过后浏览器会显示源码链接，用户可以核对合约逻辑。

生态侧的设计目标是让 Acton 工具链和测试运行时在用例规模增大时保持编译和执行耗时的平缓增长。相比基于 Node.js 或 Python 的旧方案，Rust 原生实现在万级用例规模下，`acton test` 的编译和执行耗时的增长比 toncli 更平缓（具体数字以仓库 README 的基准为准，本文不展开）。

语言覆盖上，Acton 原生支持 Tolk——TON 生态的另一种合约开发语言（类 Rust 语法）。内置支持包括语法高亮配置、编译器集成和测试框架对接，已在使用 Tolk 的团队无需切换工具。dApp（去中心化应用）开发方面，Acton 自动生成 TypeScript 绑定文件，配合 `acton script` 可以快速编写与合约交互的前端脚本，前端与合约协同开发时合约接口的类型安全在 TS 层得到保证。

## 任务流案例：NFT 合约从创建到验证

下面以一个 NFT（Non-Fungible Token，非同质化代币）合集合约为例，展示一次完整任务如何流过 Acton 的各个子系统。NFT 合约涉及铸造、转账和元数据查询，能覆盖大部分常用合约路径。

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

TON 智能合约主要有三种开发语言，Acton 对三者都提供支持。理解这三种语言为什么并存，比记住各自的语法更重要：FunC 是 TVM 原生语言，随 TON 主网一起发布，定位是"能直接控制栈和 cell 的低层语言"；Tact 和 Tolk 是后来为降低开发门槛推出的高级语言，分别走 TypeScript 风格和 Rust 风格两条路线。三种语言的官方文档分别是 [TON 文档站的 FunC 章节](https://docs.ton.org/v3/documentation/smart-contracts/func/overview)、[tact-lang.org](https://tact-lang.org/) 和 [ton-blockchain/tolk 仓库](https://github.com/ton-blockchain/tolk)。

**FunC** 是 TON 官方低层合约语言，语法接近 C，需要开发者手动管理栈（stack）操作，适合对 gas 消耗和执行效率有精细控制需求的场景。TON 主网上的标准合约（钱包、Jetton、NFT）最初都用 FunC 编写，生态里的安全审计工具和 gas 基准也以 FunC 为参照。

**Tact** 是建立在 FunC 之上的高级语言，语法更接近 TypeScript/Rust，支持结构体、接口和面向对象模式，编译到 FunC 后部署到 TVM。Tact 让合约开发体验更接近现代 Web2 开发，代价是生成的 FunC 中间产物在极端 gas 优化场景下不如手写 FunC 精细。

**Tolk** 是 TON 生态较新的合约语言，类 Rust 语法，定位介于 FunC 和 Tact 之间，兼顾表达力和执行效率。Tolk 由 ton-blockchain 组织维护，目前仍在快速迭代，适合已经熟悉 Rust 且希望直接控制 TVM 行为、又不想写 FunC 栈操作的团队。

选择哪种语言取决于团队背景和项目对精细控制的需求：追求极致 gas 优化选 FunC，追求开发效率选 Tact，习惯 Rust 语法选 Tolk。

## 适用场景与采用顺序

### 适用场景

下面按"场景—能力—解决什么"的句式列出 Acton 最能发挥价值的几类情况，对照你的项目判断是否匹配：

- 如果你的场景是**从零启动一个 TON 合约项目**，Acton 的 `acton new` 脚手架和统一 CLI 能解决"工具选型阶段反复对比 func/fift/tonos-cli"的时间成本。
- 如果你的场景是**需要在 testnet 和 mainnet 之间频繁切换**，Acton 的 `acton deploy --network` 能解决"每个网络维护一套部署脚本"的重复配置问题。
- 如果你的场景是**对 gas 消耗有强回归需求**，Acton 的 `acton test` gas 快照能解决"改一处逻辑不知道是否拖慢链上执行"的可观测性缺口。
- 如果你的场景是**Tact/FunC 合约需要形式化验证或 lint**，Acton 的 `acton lint` 和 `acton verify` 能解决"验证流程散落在多个脚本里"的链路断裂。
- 如果你的场景是**dApp 前端需要类型安全的合约绑定**，Acton 自动生成 TypeScript 绑定能解决"手写 ABI 类型容易漂移"的维护负担。

反过来，如果你的场景只是"用 Tact 写一个简单合约跑一次 demo、不涉及部署和验证"，Tact 自带工具链已经够用，引入 Acton 反而增加学习成本。

### 采用顺序

**新项目：** 直接使用 `acton new` 创建项目，从第一天就跑通完整工具链，避免后续迁移成本。

**老项目迁移：** 建议按以下顺序逐步替换：

1. 先用 `acton build` 替换 `func`/`fift`，验证编译产物一致
2. 再用 `acton test` 替换原有测试框架，先跑通现有用例，再逐步引入 fork 模式和 gas 快照
3. 最后用 `acton deploy` 和 `acton verify` 替换部署脚本，统一运维入口

## 决策建议

正在启动新 TON 项目的团队适合直接采用 Acton，省去工具选型成本；需要在 testnet 和 mainnet 之间频繁切换的团队，`acton deploy --network` 统一了网络切换；对 gas 优化有强需求的团队，`acton test` 的 gas 快照能提供回归检测。这三类团队的共同特征是"工具链碎片化已经在拖慢迭代节奏"，迁移到 Acton 的收益会明显大于学习成本。

已有成熟 CI/CD 流程且工具链稳定的团队可以暂缓采用，迁移成本可能高于收益——尤其是当现有流程已经把 func/fift/tonos-cli 封装进自动化脚本后，替换成 `acton` 带来的边际改善有限。仅使用 Tact 单一语言且不涉及部署的团队也适合暂缓，Tact 自带工具链已能满足基本需求，等真正需要跨语言或上链验证时再引入 Acton 更划算。

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
