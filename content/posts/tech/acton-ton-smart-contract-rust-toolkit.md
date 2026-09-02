---
title: "Acton：TON 智能合约全生命周期开发工具链"
date: "2026-05-14T12:47:00+08:00"
slug: "acton-ton-smart-contract-rust-toolkit"
github_repo: "ton-blockchain/acton"
description: "Acton 是 TON 官方推出的全功能智能合约开发工具链，基于 Rust 编写，用单条 CLI 覆盖项目脚手架、编译、测试、脚本、钱包操作、网络部署和调试等合约全生命周期环节，是 TON 生态当前最完整的开发基础设施之一。"
draft: false
categories: ["技术笔记"]
tags: ["智能合约", "Rust", "Web3"]
---

# Acton：TON 智能合约全生命周期开发工具链

## 学习目标

完成本文阅读后，你将能够：

1. 说出 Acton 解决的 TON 工具链碎片化问题及其能力边界
2. 使用 `acton new`/`build`/`test`/`script`/`wallet` 完成一个合约从创建到测试网部署的完整生命周期
3. 区分 FunC、Tact、Tolk 三种 TON 合约语言的定位，并说明为什么 Acton 选择 Tolk-first
4. 判断现有项目是否应该迁移到 Acton，并给出迁移的优先顺序

## 目录

1. [项目概览](#项目概览)
2. [安装与项目创建](#安装与项目创建)
3. [核心能力](#核心能力)
   - 3.1 [编译与测试](#编译与测试)
   - 3.2 [脚本部署与钱包](#脚本部署与钱包)
   - 3.3 [语言与生态支持](#语言与生态支持)
4. [任务流案例：NFT 合约从创建到部署](#任务流案例nft-合约从创建到部署)
5. [FunC、Tact 与 Tolk](#func-tact-与-tolk)
6. [适用场景与采用顺序](#适用场景与采用顺序)
7. [决策建议](#决策建议)
8. [常见问题与排查](#常见问题与排查)
9. [动手练习](#动手练习)
10. [自测清单](#自测清单)
11. [进阶路径](#进阶路径)

## 项目概览

Acton 把 TON 合约开发里原本散落在 `func`、`fift` 和多个第三方工具之间的命令，收束到一个用 Rust 编写的二进制里，覆盖从项目脚手架到测试网部署的全部环节。本文描述的行为对应撰写时 Acton 仓库 `master` 分支的状态，命令与产物路径以仓库 README 和官方文档为准。

TON 合约开发长期存在工具链碎片化：编译用 `func`，字节码工具用 `fift`，本地测试要另接测试框架，部署和钱包操作又要换一套 CLI——这些工具的命令风格、配置文件和错误信息彼此不兼容。一套 Jetton 合约的开发链路里，编译、本地测试、部署、源码校验各用不同的命令，每次还要确认"当前用的是哪个网络、哪个钱包、哪个编译器版本"。

Acton 用 `acton` 一个二进制把这些环节串起来。命令按职责分组：

| 分组 | 命令 | 职责 |
|------|------|------|
| 项目创建 | `acton new`、`acton init` | 脚手架与模板、接入既有项目 |
| 编译检查 | `acton build`、`acton check`、`acton fmt` | 编译、静态检查、格式化 |
| 测试调试 | `acton test`、`acton disasm`、`acton retrace` | 测试、反汇编、重放链上交易 |
| 钱包部署 | `acton wallet`、`acton script` | 钱包管理、本地模拟/链上部署 |

这些分组之间有依赖关系：项目创建产出源码目录，`acton build` 把源码变成字节码（`.boc`/`.cell`）并配合 `.abi` 描述接口，测试与调试验证逻辑，`acton script` 提交部署交易，`acton wallet` 为部署提供签名的钱包。后续章节按这条链路展开。

```
+------------+      +--------------+      +--------------+
| 项目创建     | ---> | 编译检查       | ---> | 测试调试       |
| acton new  |      | build/check  |      | test/disasm  |
| acton init |      | fmt          |      | retrace      |
+------------+      +--------------+      +--------------+
                          ^                      ^
                          |                      |
                   +------+----------------------+-------+
                   |     钱包部署                          |
                   |     acton wallet / acton script      |
                   +--------------------------------------+
```

[↑ 回到目录](#目录)

## 安装与项目创建

Acton 分发的是一套编译好的二进制，不需要用户自己装 Rust 工具链或手动编译。官方推荐用 installer 脚本安装在 64 位 macOS 或 Linux 上：

```bash
curl -LsSf https://github.com/ton-blockchain/acton/releases/latest/download/acton-installer.sh | sh

# 验证安装
acton --version
```

想用容器也可以拉官方镜像（以 `<version>` 指代版本号）：

```bash
docker run --rm ghcr.io/ton-blockchain/acton:<version> --version
```

平台支持分两层：**一级平台**为 macOS（ARM64、x86_64）和 Linux GNU（x86_64、ARM64），Linux 以 Ubuntu 20.04 及以上为基线；**原生 Windows 暂不支持**，要用就在 WSL 里装 Ubuntu 20.04 及以上再走 Linux 安装路径。如果你要自己从源码编译（贡献者/二次开发用），可参考仓库里的 CONTRIBUTING.md。

装好后从官方模板建项目最省事。模板自带完整的 `sources/`、`tests/` 和 `scripts/` 目录结构，新建后即可直接 `acton build`：

```bash
# 用 counter 模板创建项目
acton new first_counter --template counter
cd first_counter

# 已有仓库，不建模板，直接接入
cd your-repo && acton init

# 编译，跑测试
acton build
acton test
```

官方模板包括 `counter`（计数器）、`jetton`（代币）、`nft`、`w5-extension`（钱包 v5 扩展）和 `empty`（空项目）。`--app` 会额外生成带 TypeScript 前端的项目，适合想要 dApp 完整骨架的人。

[↑ 回到目录](#目录)

## 核心能力

### 编译与测试

`acton new` 是项目脚手架入口，可以指定模板，也可以在已有目录里用 `acton init` 接入。新建后用 `acton build` 编译：

```bash
# 编译所有配置的合约
acton build

# 只编译某个合约及其依赖
acton build Wallet

# 清缓存重编译 / 输出编译信息
acton build --clear-cache
acton build --info

# 常用选项：--out-dir 指定产物目录，--gen-dir 指定生成辅助文件目录，
# --output-abi 指定 ABI JSON 输出目录，--graph 生成合约依赖关系图
```

测试由 `acton test` 承担，是 Acton 的强项：支持 fork 模式（模拟链上状态）、gas 快照、覆盖率、突变测试（mutation testing）和模糊测试（fuzz）。测试文件用 Tolk 编写，默认放在 `tests/`：

```bash
# 跑全部测试
acton test

# 只跑某个测试文件 / 按过滤器跑
acton test tests/wallet.test.tolk
acton test --filter "wallet.*"

# 覆盖率报告
acton test --coverage --coverage-format lcov

# 突变测试（针对指定合约）
acton test --mutate --mutate-contract Wallet

# gas 快照，便于跨改动对比
acton test --snapshot gas-snapshot.json

# fork 测试网/主网状态跑测试
acton test --fork-net testnet
```

`acton test --ui` 启动本地 Web 页面，展示失败用例、调用轨迹和详细日志。调试复杂合约逻辑时这比命令行输出直观——你能直接看到具体哪条 TVM 指令触发了退出码，命令行下要在几百行文本里 grep 才能定位到同一信息。

代码质量相关有三条命令：`acton check` 做静态/写法检查，`acton fmt` 做格式化，`acton fmt --check` 只检查不格式化，适合接进 CI。

### 脚本部署与钱包

TON 的部署习惯是"写一段部署脚本，脚本里调用合约方法并处理链上交互"。Acton 用 `acton script` 执行这类 Tolk 脚本：先在本地模拟跑通，再对上测试网/主网执行：

```bash
# 本地模拟执行（不产生真实链上交易）
acton script scripts/deploy.tolk

# 部署到测试网
acton script scripts/deploy.tolk --net testnet

# 用 TON Connect 钱包
acton script scripts/deploy.tolk --net testnet --tonconnect

# fork 主网状态做只读查询
acton script query.tolk --fork-net mainnet
```

安全执行顺序是：`acton build` → `acton test` → `acton script <path>` 本地模拟 → `acton script <path> --net testnet` 上测试网。

钱包通过 `acton wallet` 管理，支持创建、导入、查看余额和签名外部消息：

```bash
# 新建一个本地钱包（v5r1 版本）
acton wallet new --name deployer --version v5r1 --local

# 导入已有助记词
acton wallet import --name my_wallet "word1 word2 ... word24"

# 查看余额
acton wallet list --balance

# 向测试网要测试币
acton wallet airdrop deployer --net testnet

# 签名外部消息
cat body.boc.base64 | acton wallet sign deployer
```

文档里最常见的启动链路是：建 project → build → 建钱包 → 脚本上测试网。下面第 3.1、3.2 的命令组合在一起，就覆盖了"从一段源码到一笔链上交易"的完整路径。

### 语言与生态支持

Acton 是 Tolk-first 的工具链：默认语言是 **Tolk**，测试、脚本、部署脚本都用 Tolk 编写。选择 Rust 实现底层，是为了大型套件下的启动开销——Rust 原生的编译加执行总耗时在套件规模放大时增长相对平缓，具体基准数据见仓库 README，本文不展开。

dApp 侧，`acton new --app` 能生成带 TypeScript 前端的项目骨架，并自动生成合约的 TypeScript 封装（wrapper），前端调用合约方法时有类型提示和自动补全，不用对照 ABI 手写每个方法签名。低层工具也内置：`acton disasm contract.boc` 反汇编字节码，`acton retrace <transaction_hash>` 重放链上交易，方便排查。

[↑ 回到目录](#目录)

## 任务流案例：NFT 合约从创建到部署

下面用一个 NFT（Non-Fungible Token，非同质化代币）合约，展示一次完整任务如何流过 Acton 各组成环节。NFT 涉及铸造、转账和元数据查询，覆盖消息处理、存储读写和 getter 这三条最常见的合约路径。

### 1. 创建项目

```bash
acton new nft_collection --template nft
cd nft_collection
```

选 `nft` 模板是因为它已经带好结构体和接口骨架，比从 `empty` 起步省事。

### 2. 编写合约

在 `sources/contracts/nft_collection.tolk` 里定义合约。下面是一段用 Tolk 写的示意逻辑（仅用于理解语法结构，不是可直接上主网的完整 NFT 标准实现，完整实现需按 [TEP-62](https://github.com/ton-blockchain/TEPs/blob/master/text/0062-nft-standard.md) 补 item 合约与 TL-B 序列化）：

```tolk
// sources/contracts/nft_collection.tolk
// Tolk 是 Acton 的默认语言，语法接近 Rust

struct ItemInfo {
    index: uint256;
    owner: Address;
    content: String;
}

// 合约状态
storage owner: Address
storage nextIndex: uint32
storage items: map<uint32, ItemInfo>

// 初始化
init(owner: Address) {
    self.owner = owner;
    self.nextIndex = 0;
    self.items = emptyMap();
}

// 入站消息处理：铸造
fun onMint() { /* 校验 sender 为 owner，写 storage，回复消息 */ }

// 出站 getter：供链下查询
get collectionOwner(): Address { return self.owner; }
get itemInfo(index: uint32): ItemInfo { /* 读 map，找不到返回占位 */ }
```

Tolk 用 `struct` 定义复合数据、`storage` 声明持久状态、`init` 做初始化、`get` 暴露链下可调用函数——这类高层结构让合约比纯栈式的 FunC 好写很多。

### 3. 编译

```bash
acton build
```

`acton build` 调用 Tolk 编译器，把 `.tolk` 源码编译成 TVM 字节码并输出 ABI 描述文件。

### 4. 测试

在 `tests/` 下用 Tolk 编写测试，覆盖铸造成功、权限校验失败等场景：

```bash
acton test --snapshot gas-snapshot.json
```

gas 快照便于在后续修改中检测回归：NFT 对 gas 敏感，因为单次铸造可能触发多次存储写入，改动后对比快照就能看出是否多烧了 gas。

### 5. 本地模拟 + 部署到测试网

```bash
# 先在本地模拟部署脚本，确认逻辑正确
acton script scripts/deploy.tolk

# 再真正上测试网
acton script scripts/deploy.tolk --net testnet
```

部署脚本负责：读取 ABI 和字节码、连接钱包（`acton wallet` 创建并 airdrop 测试币）、签名并广播部署交易。部署成功后脚本会输出合约地址。

### 6. 自测问题

读完上面这条链路后，试着回答：如果 `acton script --net testnet` 部署后合约地址在浏览器里打开异常，最可能从哪几类原因入手排查？请参照文档给出一到两个具体方向。

参考思路：先确认钱包在 `--net testnet` 下确实有余额（`acton wallet list --balance`），再确认 `Acton.toml`/部署脚本里目标网络与钱包一致，最后用 `acton retrace <tx>` 重放部署交易看链上实际报错。能说出"钱包余额—网络配置—交易重放"这三步，就说明你把"构建—部署"这条链路的故障点理清了。

[↑ 回到目录](#目录)

## FunC、Tact 与 Tolk

TON 智能合约生态里主要有三种开发语言，定位各不相同。Acton 默认并优先支持 **Tolk**。官方资料：[TON 文档站 FunC 章节](https://docs.ton.org/v3/documentation/smart-contracts/func/overview)、[tact-lang.org](https://tact-lang.org/)、[ton-blockchain/tolk 仓库](https://github.com/ton-blockchain/tolk)。

**Tolk** 是 ton-blockchain 组织维护的较新语言，类 Rust 语法，也是 Acton 的主角语言。它直接编译到 TVM 字节码，在保留高级语法的同时能对底层指令做精细控制（如手动选择 cell 编码、直接操作 slice/builder）。Acton 的测试、脚本、模板和文档都以 Tolk 为准。Tolk 仍在快速迭代，标准库与审计工具链尚在完善，主网生产案例不多；存量且已审计的合约不建议立刻迁到 Tolk，等稳定版确认生态后再说。

**FunC** 是 TON 的低层合约语言，语法接近 C，需要手动管理栈和 cell。主网的标准合约（钱包、Jetton、NFT）最初都用 FunC 编写，生态里的安全审计工具和 gas 基准也以 FunC 为参照。选它可复用主网已有资产，代价是开发速度慢、易出错。

**Tact** 是一个编译到 FunC 的高级语言，语法接近 TypeScript，支持结构体和接口，定位是"比 FunC 好写"。要更快出合约可以选 Tact，代价是生成的 FunC 中间产物在极端 gas 优化场景下不如手写精细。Tact 由独立社区维护，不叠在 Acton 的 Tolk-first 工作流里。

给不同起点的团队一句话结论：对 FunC 语法和生态都熟就继续用 FunC；看重开发速度且接受独立工具链就试 Tact；想用一把统一的 CLI + 高层语法跑通全流程，就跟着 Acton 走 Tolk。

[↑ 回到目录](#目录)

## 适用场景与采用顺序

### 适用场景

Acton 在下面几个场景里有明确收益：

- **从零启动 TON 合约项目**：`acton new --template` 一步建好骨架，省去分别配置编译器和测试框架的前置工作，也不用自己拼接多套工具。
- **需要高质量本地测试**：fork 模式、gas 快照、覆盖率、突变测试和 fuzz 都内置在同一条 `acton test` 里，CI 里就能跑出有深度的验证，不必另接第三方测试框架。
- **在 testnet 和 mainnet 之间切换**：`acton script <path> --net` 把网络切换收束成一个参数，部署脚本里不再写网络分支判断。
- **dApp 前端需要类型安全的合约绑定**：`acton new --app` 自动生成 TypeScript 封装和前端骨架，前端调用合约方法时有完整类型提示。
- **需要链下调试与链上重放**：`acton disasm` 反汇编、`acton retrace <tx>` 重放交易，把"链上出了什么事"变成可复现的调试现场。

反过来，如果你的场景只是"写一段 FunC 合约、偶尔本地验一下"，已有工具链够用，装 Acton 反而要多学一套命令。

### 采用顺序

**新项目：** 直接用 `acton new --template` 创建项目，从第一天就跑通"创建—编译—测试—部署"链路，避免后续迁移成本。

**老项目迁移：** 建议按顺序逐步替换：

1. 先用 `acton build` 替换原有的 `func` 编译步骤，确认产物一致
2. 再用 `acton test` 替换原有测试方式，先跑通现有用例，再逐步引入 fork 模式和 gas 快照、突变测试
3. 最后用 `acton script` + `acton wallet` 替换原有的部署脚本和钱包操作，统一运维入口

[↑ 回到目录](#目录)

## 决策建议

三组团队可以从 Acton 拿到确定收益，另外两组暂时不必。

**建议现在用的：**

- **新 TON 项目组**：从 `acton new` 起步，第一天就把编译、测试、部署串成一条链路。
- **对本地测试深度有要求的团队**：把 `acton test` 的 fork 模式、gas 快照、突变测试接进 CI，每次 PR 自动验证合约行为并对比 gas。有人改了一行逻辑导致 gas 上涨，CI 直接在 PR 里标出来，不用等链上部署后发现。
- **频繁切换 testnet/mainnet 的团队**：`acton script --net` 省掉每次部署前人工确认"这次该连哪个 RPC、用哪个钱包"的心智开销。

**可以暂缓的：**

- **已有成熟部署脚本且稳定运行的团队**：如果现有编译和部署流程稳定，切到 `acton` 的边际收益有限，建议等下一次工具链大版本或 Tolk 稳定版发布时再评估。
- **只用 FunC 写合约、不跑深测试、不部署的单人项目**：现有工具链覆盖了编译和本地验证，够用。等合约要上 testnet 做多轮部署验证时再来，学习曲线不会白费。

**决策检查清单：**

1. 你是否需要高品质的本地测试（fork/gas/突变）？如果是，`acton test` 一装就有。
2. 你是否频繁在 testnet 和 mainnet 之间切换？如果是，`--net` 参数能省掉每次人工确认。
3. 你是否想要 dApp 前端自动类型绑定？如果是，`acton new --app` 直接给。

三条里占两条以上，就值得一试；否则先用现有工具链更划算。

[↑ 回到目录](#目录)

## 常见问题与排查

### 编译失败

**现象**：`acton build` 报错，提示找不到编译器或语法错误。

**排查**：

1. 确认 Acton 正确安装：`acton --version` 有版本输出。
2. 确认在项目根目录、且 `acton init` 已生成配置。
3. 检查源码语法：Tolk 语法随版本迭代可能变化，对照 ton-blockchain/tolk 官方仓库文档检查。

**修复**：

- 用 `acton build --clear-cache` 清缓存后重编。
- 语法错误按报错信息修复，注意 TON 合约的 cell 存储限制和 gas 消耗。

### 测试失败

**现象**：`acton test` 报错，或测试结果不符合预期。

**排查**：

1. 看测试输出，区分是编译错误、运行时错误还是断言失败。
2. 检查 fork/模拟状态是否设置正确：`--fork-net` 需要正确的链上下文（多网络配置下尤其如此）。
3. 用 `acton test --snapshot gas-snapshot.json` 生成 gas 快照，对比前后差异。

**修复**：

- 状态模拟不正确时，检查测试里的钱包与合约地址是否正确。
- gas 超预期时，检查合约逻辑是否有不必要的存储读写或循环。

### 部署失败/合约上链后异常

**现象**：`acton script --net testnet` 报错，或部署后合约行为不对。

**排查**：

1. 确认钱包有测试币：`acton wallet list --balance`，余额不足先 `acton wallet airdrop deployer --net testnet`。
2. 确认 `--net` 与钱包网络一致，别拿主网钱包配 testnet（或反过来）。
3. 用 `acton retrace <transaction_hash>` 重放部署交易，看链上实际执行结果和报错。

**修复**：

- 余额不足就 airdrop 或转账。
- 网络不匹配就统一 `--net`。
- 重放交易定位具体报错后修合约或脚本。

[↑ 回到目录](#目录)

## 动手练习

1. **把 `acton test --snapshot` 接进 CI**：写一个 GitHub Actions 或 GitLab CI 配置，每次 PR 自动跑 `acton test` 并生成 gas 快照，与 base 分支的快照做 diff。看看编译产物 `build/` 是否该在 CI 里缓存复用，为什么。
2. **用 `acton new --app` 建一个带 TypeScript 前端的项目**：在前端调用合约的 getter，观察自动生成的 wrapper 有多大程度省掉了手写 ABI 解析。

做完练习 1，试着向自己解释为什么 gas 快照能有效检测回归，以及为什么阈值不能设得太松（压力下会放过真实回归）。做完练习 2，再想想 TypeScript wrapper 的生成是编译期固定，还是随链上变化——这决定了前端要不要跟随合约发版。

[↑ 回到目录](#目录)

## 自测清单

1. 说出 Acton 的命令分组及其职责，以及它替代了 TON 旧生态里的哪些工具。
2. 用一条命令从模板建项目、编译、跑测试，分别是什么？
3. 解释 fork 模式、gas 快照、突变测试各自解决什么问题。
4. 说出 `acton script` 本地模拟与 `--net testnet` 上链的区别，以及部署前为什么先本地跑一遍。
5. 复述采用顺序的三步，并解释为什么老项目建议逐步迁移而不是一次性切换。

（参考答案见各对应章节；答不出的部分回到对应小节重读。）

[↑ 回到目录](#目录)

## 进阶路径

跑通基本流程后，下面几条方向可以按兴趣挑选：

1. **读 Acton 源码**：克隆 [ton-blockchain/acton](https://github.com/ton-blockchain/acton)，重点看编译器集成和测试运行器实现，理解 Tolk 如何被统一到同一套 CLI 下。
2. **对比三种语言写同一合约**：分别用 FunC、Tact、Tolk 写一个 Jetton，对比代码量和 gas 消耗，体会 Acton 为什么押注 Tolk。
3. **配置多网络部署流水线**：在 CI 里把"本地测试 → testnet 部署 → 接入 mainnet 配置"串成流水线，用 `acton script <path> --net` 切网络。
4. **深入 TVM**：用 `acton disasm` 反编译 `.boc`，理解 Tolk 编译器生成的字节码，以及如何在极端 gas 优化场景下手写更精细的逻辑。
5. **给上游提 issue 或 PR**：遇到 bug 或缺功能，先在 [ton-blockchain/acton](https://github.com/ton-blockchain/acton) issues 里搜索，没有再提新 issue。

---

*本文基于 Acton 项目（github.com/ton-blockchain/acton）的官方 README 与文档撰写，相关信息可能随版本更新而变化；版本号、命令与平台支持请以项目仓库的实际页面和官方文档为准。*