---
title: "VeraCrypt：当开源全盘加密走到 12k Star 的成熟期"
slug: "veracrypt-veracrypt-disk-encryption-platform-2026"
date: 2026-06-29T21:02:57+08:00
lastmod: 2026-06-29T21:02:57+08:00
draft: false
categories: ["技术笔记"]
tags: ["GitHub", "Encryption", "TrueCrypt", "C++", "Security", "开源", "Fork"]
description: "veracrypt/VeraCrypt 是从 TrueCrypt 7.1a fork 出来的开源全盘加密项目，本文梳理它的安全增强点、平台矩阵、为什么二进制必须从官网下载，以及它在 macOS / Linux / Windows 各自编译体系的差异。"
---

## 起源与定位

`veracrypt/VeraCrypt` 是一个从 TrueCrypt 7.1a fork 出来的全盘加密（Full Disk Encryption，FDE）项目，它在 TrueCrypt 停止维护后由 IDRIX 接手并持续演进，目标是"在保留 TrueCrypt 7.1a 全部能力的基础上修复已公开的安全问题"。

它不是"明星项目"——这种偏底层的 C++/C 系统级软件本来就不会有 ML/Agent 类仓库的曝光度——但凡关心"如何在多平台上做 AES（Advanced Encryption Standard，高级加密标准）/加密卷/隐藏卷/HBM 加密"的人，VeraCrypt 都是绕不开的参考实现和分发形态。

## 相对 TrueCrypt 的核心安全增强

TrueCrypt 7.1a 在 2014 年 5 月突然停止维护后，开源社区完成了一次官方审计（2014 年 6 月的 Quarkslab 审计），结论是"未发现 NSA（美国国家安全局）后门"，但仍指出若干需要修复的问题。VeraCrypt 在 fork 之后**重点修复的就是这些审计发现**：

- **PBKDF2（Password-Based Key Derivation Function 2，基于密码的密钥派生函数 2）迭代次数提升**：TrueCrypt 时代只有 1000 次，VeraCrypt 默认 200000 次（系统盘加密）/ 500000 次（普通卷）。这是密码哈希侧抗暴力破解的关键参数。
- **引导加载器修复**：替换 TrueCrypt 的旧版 Boot Loader，解决若干启动路径上的潜在弱点。
- **加密卷格式演进**：在原 TrueCrypt 卷格式之上，引入更现代的加密组合（如增加 SHA-512、Whirlpool 等哈希算法选项）和若干边信道缓解。
- **Windows 驱动签名**：VeraCrypt 二进制必须由 IDRIX 用 GlobalSign 证书签名（`.sys` 驱动在 64 位 Windows 上必须签名才能加载），这是它和"自己编译"版本之间一个显著差异——README 明确指出官方二进制总会比自己编出来的体积大约 10 KiB，原因就是嵌入了完整的签名链。

## 平台矩阵与二进制分发

VeraCrypt 在三端都有等价能力：

| 平台 | 形态 | 主要能力 |
|------|------|---------|
| Windows | 安装器 + 驱动（64 位 .sys 已签名） | 系统盘加密 / 非系统盘加密 / 隐藏卷 / 隐藏 OS |
| macOS | `.dmg` 安装器 | 同上，部分 macOS 版本与系统级 FileVault 共存需要专门配置 |
| Linux | 命令行 + GUI | dm-crypt 集成 / 任意映射设备 |

三端共享同一卷格式（`.hc`、旧 `.tc` 后缀的 TrueCrypt 文件），跨平台可读——这意味着你可以在 Linux 上开一个加密卷，挂到 macOS 上读，反之亦然。

## 源码编译的"门槛"与"注意事项"

README 第二段就明确："你可以使用本仓库的源码，但必须接受 `License.txt` 中的条款。"——License 中有一条关键限制：**派生作品不得继续使用 "TrueCrypt" 或 "VeraCrypt" 名称**，这是项目自我保护的法律边界。

跨平台编译命令基本遵循类似流程：

```bash
# Linux
make           # 默认目标
make WXVERSION=3.2
sudo make install

# macOS
make SYSCTL=0

# Windows
# 需 Visual Studio + WSDK81 环境变量指向 Windows 8.1 SDK
# 详见 doc/html/en/CompilingGuidelineWin.html
```

其中 Windows 端的难度最高：必须正确配置 `WSDK81` 环境变量和数字签名——这也是为什么"Windows 用户应当从 veracrypt.fr 直接下载官方二进制"而不是自己编译的根本原因。

## 它的工作原理（细节框架）

VeraCrypt 在内核层做的是"设备级透明加密"：

- 加密卷以"虚拟设备"形式出现，例如 Windows 上的 `\\.\VeraCryptVolumeX`，macOS/Linux 上的 `/dev/mapper/veracrypt_xxx`；
- 所有读写都经过 AES、Serpent、Twofish（这三种均为对称分组密码）或其级联组合——VeraCrypt 支持最多三种算法的级联，而 TrueCrypt 仅支持两种；
- 卷头（Volume Header）保存主密钥（Master Key）的密文形式，使用用户密码经 PBKDF2 派生出的密钥解开主密钥。主密钥本身在写卷时**不会**出现在磁盘上——这正是隐藏卷（Hidden Volume）能成立的核心：存在"正常"和"隐藏"两个卷头，PBKDF2 派生密钥能解开哪一个取决于用户在挂载时输入的密码。
- 隐藏操作系统（Hidden OS）的概念是把第二套启动分区隐藏在加密容器中，登入密码不同对应真实系统/诱饵系统/隐藏系统三层身份。

这些机制本身与 TrueCrypt 一脉相承，VeraCrypt 的增量改进主要在 PBKDF2 强度、加密算法选项与若干边信道缓解上。

## 适用与不适用

**适合**

- 跨平台多 OS 机器需要统一加密体验；
- 在内部分发场景里需要在只受信任的 1–2 台机器间交换加密卷；
- 对"全盘加密 + 隐藏卷"有合规/取证对抗需求的安全团队；
- 想研究"经典 FDE 工程实践"的学习者。

**不适合**

- 期望企业级集中管理（VeraCrypt 不带"集中控制台"，企业 IT 想下发策略要么靠 GPO 类外部手段，要么换 BitLocker + MBAM 这类偏 ESM 生态的方案）；
- 期望云原生（它解决的是"本地设备物理丢失"问题，对象存储/SaaS 不直接相关）；
- 把"自己编译"当信任根——README 已经把"二进制签名"必要性写得很清楚，鉴于官方签名链足以验证可信度，普通用户没必要重复造轮子。

## 小结

VeraCrypt 不是"新技术展示品"，而是一个治理成熟的长期维护项目。它今天进入 GitHub Trending，主要得益于"用户重装系统/装机盘/换新机"等周期性需求高峰——这恰好是它十年来一直擅长的场景。它值得被记住的不是"它现在新增了什么"，而是"它在前任停摆后接手了一个行业事实标准，并为后来者提供了一个安全增强、开源、可审计的实现"。

## 链接

- 仓库：https://github.com/veracrypt/VeraCrypt
- 官方网站与二进制下载：https://veracrypt.fr
- 文档（编译指南）：https://veracrypt.jp/en/CompilingGuidelineWin.html
- License：Apache 2.0 + TrueCrypt 衍生条款（详见 `License.txt`）
