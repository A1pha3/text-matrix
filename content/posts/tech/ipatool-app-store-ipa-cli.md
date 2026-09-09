---
title: "ipatool：用命令行下载 App Store 应用包"
date: 2026-09-04T03:27:35+08:00
slug: "ipatool-app-store-ipa-cli"
github_repo: "majd/ipatool"
source_key: "gh:majd/ipatool"
description: "ipatool 是一个用 Go 编写的命令行工具，支持在 iOS、iPadOS、tvOS、visionOS 与 macOS 上搜索并下载 App Store 应用包（.ipa / .pkg），覆盖认证、搜索、购买、列出版本与下载等完整链路。本文讲解其命令矩阵、典型用法与边界。"
draft: false
categories: ["技术笔记"]
tags: ["iOS", "CLI", "Go", "App Store", "逆向"]
---

## 核心判断

日常获取 iOS 应用安装包，路径通常是越狱社区或第三方站点，来源不可控、版本滞后。ipatool 给出的是一条更直接的路径：直接对 App Store 走一遍"登录 → 搜索 → 购买授权 → 下载 .ipa"的完整流程，全部在命令行里完成。它不是绕过授权——`purchase` 命令正是去申请授权许可；它消除的是 GUI 层面的黑盒，把 App Store 的获取链路变成可脚本化、可审计的命令。

截至本文写作时，项目 v2.5.0（2026-08-31 发布），GitHub 10.8k stars，Go 实现，MIT 许可。支持 Windows、Linux 与 macOS，可在 iOS、iPadOS、tvOS、visionOS、macOS 五个平台搜索与下载。

## 安装

macOS 用户可直接用 Homebrew 安装：

```bash
brew install ipatool
```

其他系统从 GitHub Releases 下载对应平台的二进制，或用 Go 工具链自行编译：

```bash
go build -o ipatool
```

## 命令矩阵

ipatool 以子命令组织，核心链路围绕"搜索 → 版本 → 下载"展开。

### 认证

```bash
ipatool auth login          # 登录 App Store
ipatool auth info           # 当前账号信息
ipatool auth revoke         # 撤销凭据
```

### 搜索

```bash
ipatool search "微信" --platform iphone
```

`--platform` 可选 `iphone`（iOS）、`ipad`（iPadOS）、`appletv`（tvOS）、`visionos`、`macos`；`-l/--limit` 控制返回条数（visionOS 上限 12）。

### 购买授权

```bash
ipatool purchase -b com.tencent.xin
```

`-b/--bundle-identifier` 指定应用的 Bundle ID。这一步为账号获取该应用的使用授权，是后续下载的前提（免费应用同样需要走这一流程拿到授权记录）。

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

按购买时间倒序列出账号名下应用。

## 一条完整的链路

把上面的命令串起来，就是一次标准的取包流程：

```bash
# 1. 登录（首次会要求输入密码，双重验证码在进程中处理）
ipatool auth login

# 2. 搜索拿到 Bundle ID
ipatool search "微信" --platform iphone -l 1

# 3. 获取授权（免费应用同样需要，这是后续下载的前提）
ipatool purchase -b com.tencent.xin

# 4. 下载到指定位置
ipatool download -b com.tencent.xin --platform iphone -o ./wechat.ipa
```

连续跑多个应用时，登录态只认证一次即可复用。脚本化环境统一追加 `--non-interactive`；需要机器可读的结果时用 `--format json` 输出，便于记录版本号或做后续审计。

## 几个值得注意的点

- **交互模式默认开启**：自动化环境要加 `--non-interactive`
- **输出可机器可读**：`--format text|json` 全局生效，`json` 便于对接脚本
- **凭据存钥匙串**：macOS 上通过钥匙串存取，`--keychain-passphrase` 用于解锁；登录会话的持久化 Cookie 则落在 `~/.ipatool/` 目录，属敏感文件，别随意共享
- **版本元数据**：`get-version-metadata -b <bundle> --external-version-id <id>` 解析 `list-versions` 返回的外部版本号对应的元数据
- **活跃维护**：近期提交包括 visionOS/macOS 搜索下载支持、瞬时认证响应的重试修复，v2.5.0 刚发布

## 适用边界

- **需要 Apple ID**：工具假设你有一个可用的 App Store 账号，登录态来自真实账号授权
- **账号有一定风险**：工具通过非官方客户端登录，Apple 可能对来自非官方客户端的账号做限流或标记；如非必要，用次要账号
- **不是"免费白嫖"工具**：它下载的是你账号已授权或有权限获取的应用包，用途应限于个人备份、测试或合法分发场景
- **授权随账号走**：`purchase` 记录的授权绑定账号，换设备需重新登录
- **GUI 依赖消除**：适合 CI、脚本化批量获取，但请遵守所在司法辖区的下载与分发规定

## 结论

ipatool 的价值是把 App Store 的应用获取链路压缩成几条可复用的命令，适合需要批量、可重复、可脚本化拿 .ipa/.pkg 的开发者或测试团队。它保持了对授权体系的尊重（每一步都走官方流程），因此不是灰色工具，而是一个把官方链路工程化的 CLI。用之前先想清楚用途边界——下载的包怎么用、在哪里用，才是真正需要你判断的部分。
