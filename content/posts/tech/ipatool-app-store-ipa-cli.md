---
title: "ipatool：用命令行下载 App Store 应用包"
date: 2026-09-04T03:27:35+08:00
lastmod: 2026-10-01
slug: "ipatool-app-store-ipa-cli"
github_repo: "majd/ipatool"
source_key: "gh:majd/ipatool"
description: "ipatool 是一个用 Go 编写的命令行工具，支持在 iOS、iPadOS、tvOS、visionOS 与 macOS 上搜索并下载 App Store 应用包（.ipa / .pkg），覆盖认证、搜索、购买、列出版本与下载等完整链路。本文拆解其 SAP 认证机制、命令矩阵、凭据存储与典型用法。"
draft: false
categories: ["技术笔记"]
tags: ["iOS", "CLI", "Go", "App Store", "逆向"]
---

## 核心判断

日常获取 iOS 应用安装包，路径通常是越狱社区或第三方站点，来源不可控、版本滞后。ipatool 给出的是一条更直接的路径：直接对 App Store 走一遍"登录 → 搜索 → 购买授权 → 下载 .ipa"的完整流程，全部在命令行里完成。它不是绕过授权——`purchase` 命令正是去申请授权许可；它消除的是 GUI 层面的黑盒，把 App Store 的获取链路变成可脚本化、可审计的命令。

截至 2026 年 10 月初，项目 v2.6.0（2026-09-13 发布），GitHub 11.4k stars、958 forks，Go 实现，MIT 许可。2021 年创建至今持续迭代，v2.4.0 到 v2.6.0 这两个月是近年变化最密集的一段：认证协议整体切换为 SAP 签名请求，补齐 visionOS 与 macOS 平台，还能在越狱 iOS 设备上直接运行。半年前网上的旧教程已经对不上现在的命令行为，值得先看清它的认证机制再上手。

## 认证机制：这个仓库最值得读的部分

App Store 客户端走的是一套不公开的认证协议。ipatool 早期自己模拟这套协议的请求格式，v2.4.0 起改为 SAP 签名请求（release notes 原话是 "Replace App Store authentication with SAP-signed requests"）。源码里的 `internal/sap` 揭示了它的做法：**不重写苹果的私有签名逻辑，而是在 Unicorn CPU 仿真器里加载苹果官方签名库的预编译产物，用仿真执行对本机请求做签名**。签名库按操作系统与 CPU 架构区分，首次登录时下载并缓存到用户缓存目录，iOS 构建则因为本身就是原生环境而直接运行。

这个设计有两个直接可见的后果：

1. **首次登录可能要几分钟**。命令行会提示 "preparing authentication; the first login may take a few minutes"——下载签名库、与苹果的 SAP 服务端完成 setup 与证书交换都在这一步。之后的登录走缓存，不再重复这个过程。
2. **对苹果服务端来说，请求由官方签名代码生成**。这大概是它作为非官方客户端仍能长期稳定工作的原因，也是维护者面对苹果协议变更时选择"运行官方代码"而非"逆向重实现"的工程判断。

登录时若账号开启双重认证，交互模式下进程内直接提示输入 2FA 码；非交互模式则会提示退出后用 `--auth-code` 参数重跑一次。

## 安装

macOS 用户直接用 Homebrew：

```bash
brew install ipatool
```

其他系统从 GitHub Releases 下载对应平台的压缩包——macOS、Linux、Windows 各有 amd64/arm64 两档，v2.6.0 起还提供 `ios-arm64` 产物，可在越狱 iOS 设备上运行，每份产物附带 `.sha256sum` 校验文件。或者用 Go 工具链自行编译：

```bash
go build -o ipatool
```

## 命令矩阵

ipatool 以子命令组织，核心链路围绕"搜索 → 版本 → 下载"展开。

### 认证

```bash
ipatool auth login          # 登录 App Store（交互模式下邮箱、密码、2FA 码依次提示，密码输入有掩码）
ipatool auth info           # 当前账号信息
ipatool auth revoke         # 撤销凭据
```

非交互模式下，`--email` 与 `--password` 是必填参数。

### 搜索

```bash
ipatool search "微信" --platform iphone
```

`--platform` 可选 `iphone`（iOS）、`ipad`（iPadOS）、`appletv`（tvOS）、`visionos`、`macos`；`-l/--limit` 控制返回条数（默认 5，visionOS 上限 12）。v2.6.0 起，搜索结果会列出每个应用支持的平台。

### 购买授权

```bash
ipatool purchase -b com.tencent.xin
```

`-b/--bundle-identifier` 指定应用的 Bundle ID；v2.6.0 起也可用 `-i/--app-id` 直接按数字 ID 授权，省去先查 Bundle ID 的一步。这一步为账号获取该应用的使用授权，是后续下载的前提（免费应用同样需要走这一流程拿到授权记录）。

### 列出可用版本

```bash
ipatool list-versions -b com.tencent.xin
```

也可用 `-i/--app-id` 指定数字 ID；`-b` 会覆盖 `-i`。

### 下载应用包

```bash
ipatool download -b com.tencent.xin --platform iphone
```

`-o/--output` 指定落盘路径；`--external-version-id` 可指定某个具体版本（默认最新版）；`--purchase` 在需要时自动先获取授权。下载到的 iOS 包是 `.ipa`，macOS 应用则是 `.pkg`。

### 查询历史购买

```bash
ipatool list-purchases --page 1 --max-results 10
```

按分页列出账号名下的应用，`-l/--max-results` 默认 10；v2.6.0 起结果包含 Mac 应用，并可用 `--platform` 过滤。这个命令和 `list-versions`、`get-version-metadata` 搭配，就能还原某个应用任意历史版本的下载链路。

## 一条完整的链路

把上面的命令串起来，就是一次标准的取包流程：

```bash
# 1. 登录（首次会下载签名库，可能需要几分钟；2FA 码在进程中处理）
ipatool auth login

# 2. 搜索拿到 Bundle ID
ipatool search "微信" --platform iphone -l 1

# 3. 获取授权（免费应用同样需要，这是后续下载的前提）
ipatool purchase -b com.tencent.xin

# 4. 下载到指定位置
ipatool download -b com.tencent.xin --platform iphone -o ./wechat.ipa
```

连续跑多个应用时，登录态只认证一次即可复用。脚本化环境统一追加 `--non-interactive`，并把邮箱密码显式传给登录命令；需要机器可读的结果时用 `--format json` 输出，便于记录版本号或做后续审计：

```bash
ipatool auth login --non-interactive -e you@example.com -p "$PASSWORD"
ipatool search "微信" --platform iphone --non-interactive --format json
```

## 凭据存在哪里

ipatool 的状态分两处存放，理解这一点对备份和多机部署很重要：

- **账号密码**：交给系统凭据管理器——macOS 是钥匙串，Linux 是 Secret Service。在没有系统凭据管理器的环境（如精简容器）会退化为文件存储，此时需要 `--keychain-passphrase` 提供一个解锁口令——它只用于加密本地凭据文件，与 Apple ID 密码无关。
- **登录会话**：持久化 Cookie 写在状态目录的 `cookies` 文件里。状态目录默认是 `~/.ipatool`；v2.6.0 起若设置了 `XDG_STATE_HOME` 或 `XDG_DATA_HOME`，则改用 `<base>/ipatool` 并在首次运行时自动迁移旧目录，迁移失败（比如跨文件系统）则保留原位置，登录态不受影响。

`cookies` 属敏感文件，凭据目录不要随意共享；换设备后重新登录一次即可。

## 几个值得注意的点

- **交互模式默认开启**：自动化环境要加 `--non-interactive`
- **输出可机器可读**：`--format text|json` 全局生效，`json` 便于对接脚本
- **已下架应用仍可按数字 ID 下载**：download 的实现里，Bundle ID 查不到应用时会回退到你提供的数字 ID 继续流程——源码注释原话是 "Delisted apps may still be downloadable by their numeric ID"。配合 `list-versions` 与 `--external-version-id`，可以取回已下架应用的历史版本
- **会话过期自动处理**：下载与查询链路遇到密码令牌过期会自动重新登录再重试，遇到缺授权且指定了 `--purchase` 时会自动补授权，中断的下载支持断点续传
- **下载产物嵌封面**：v2.6.0 起下载的 IPA 会嵌入 iTunes 封面图（可用时），并修复了 OTA 安装的兼容性
- **活跃维护**：v2.4.0 切换 SAP 认证，v2.5.0 补 visionOS 与 `list-purchases`，v2.6.0 补 macOS App Store 与越狱 iOS 支持，两个月内三个功能版本

## 适用边界

- **需要 Apple ID**：工具假设你有一个可用的 App Store 账号，登录态来自真实账号授权
- **账号有一定风险**：工具通过非官方客户端登录，Apple 可能对来自非官方客户端的账号做限流或标记；如非必要，用次要账号
- **不是"免费白嫖"工具**：它下载的是你账号已授权或有权限获取的应用包，用途应限于个人备份、测试或合法分发场景
- **授权随账号走**：`purchase` 记录的授权绑定账号，换设备需重新登录
- **GUI 依赖消除**：适合 CI、脚本化批量获取，但请遵守所在司法辖区的下载与分发规定

## 结论

ipatool 的价值是把 App Store 的应用获取链路压缩成几条可复用的命令，适合需要批量、可重复、可脚本化拿 .ipa/.pkg 的开发者或测试团队。它保持了对授权体系的尊重（每一步都走官方流程），面对苹果的私有协议也没有走逆向重实现的路，而是让官方签名代码在仿真环境里替自己签名——这让它成为少数能跟上 App Store 协议演进的第三方工具。用之前先想清楚用途边界——下载的包怎么用、在哪里用，才是真正需要你判断的部分。

项目地址：[majd/ipatool](https://github.com/majd/ipatool)
