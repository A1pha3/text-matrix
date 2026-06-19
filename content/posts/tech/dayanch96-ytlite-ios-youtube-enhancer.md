---
title: "dayanch96/YTLite：iOS版YouTube增强工具，支持下载视频/音频、自定义界面"
slug: dayanch96-ytlite-ios-youtube-enhancer
date: "2026-04-22T17:50:00+08:00"
description: "YTLite 是 iOS 版 YouTube 增强工具，支持视频/音频下载、界面定制、画中画等功能，通过 GitHub Actions 自动构建。"
categories: ["技术笔记"]
tags: ["iOS", "YouTube", "越狱", "Tweak", "下载工具"]
---

# dayanch96/YTLite：iOS 版 YouTube 增强工具，支持下载视频/音频、自定义界面

## 核心判断

YTLite（现名 YouTube Plus）是 iOS 上少数仍在活跃维护的 YouTube 增强 tweak（注入式修改模块）之一，但从 5.2 版本开始转为订阅制，最后一个免费版本是 5.2b4。是否值得投入时间安装，取决于两件事：能否接受 sideload（侧载）签名的 7 天续签周期，以及是否需要它相比 uYouPlus 多出来的那部分功能。

需求只是去广告加下载视频的话，uYouPlus 仍然是更稳妥的选择——完全免费、社区更大、更新更频繁。YTLite 的差异点在界面定制深度和 SponsorBlock 内置：提供超过 100 个可配置选项，包括移除 Feed 元素、重排标签、OLED 模式、Shorts-only 模式，这些在 uYouPlus 里要么没有要么需要额外 tweak。重度使用 YouTube 且对界面有强控制欲的用户，YTLite 值得装；偶尔用的用户，免费版 5.2b4 加 uYouPlus 组合更省心。

## 项目背景与版本现状

| 维度 | 数据 |
|---|---|
| 仓库 | https://github.com/dayanch96/YTLite |
| 最新版本 | 5.2.1（2026-04-23） |
| 支持的 YouTube 版本 | 21.16.2（2026-04-23 测试） |
| 提交数 | 463 |
| 语言占比 | Logos 75.5%、Objective-C 24.2%、Makefile 0.3% |
| 商业模式 | 5.2 起订阅制，5.2b4 是最后免费版 |

仓库根目录的文件结构能直接说明这个 tweak 的技术本质：

```text
YTLite.h          # 头文件
YTLite.x          # Logos 源文件（主注入逻辑）
YTLite.plist      # 配置 plist
Settings.x        # 设置界面注入
Sideloading.x     # 侧载检测逻辑
YouTubeHeaders.h  # YouTube 私有头文件声明
YTNativeShare.x   # 原生分享功能注入
Makefile          # Theos 构建文件
control           # Debian 包控制文件（Theos 标准）
```

`.x` 后缀是 Logos 语法文件，`control` 文件加 `Makefile` 的组合是 Theos 工具链的标志。YTLite 用 Theos 构建，是标准的 iOS tweak，不是普通的 Swift/Objective-C 应用。

## iOS Tweak 的工作原理：注入 YouTube 二进制

理解 YTLite 怎么工作，需要先理解 iOS tweak 的注入机制。

iOS 应用是 Mach-O 二进制，tweak 的本质是一段动态库（dylib），在目标应用启动时被加载，通过 method swizzling（方法混淆）替换或拦截目标类的方法实现。YTLite 用 Logos 语法写这种注入，`%hook` 指令指定要拦截的类，`%orig` 调用原始实现，`%end` 结束拦截块。主注入逻辑写在 `YTLite.x`，设置界面注入写在 `Settings.x`。

`YouTubeHeaders.h` 文件声明了 YouTube 应用的私有类和接口——这些类没有公开文档，是逆向工程得到的。tweak 开发者依赖这些头文件来知道要 hook 哪些类。每次 YouTube 更新，私有类名或方法签名可能变化，这就是为什么 tweak 有「支持的 YouTube 版本」这个概念。YTLite 当前锁定 21.16.2，装的 YouTube 是其他版本时，hook 可能失效。

构建产物是一个 `.dylib`，但它不能独立运行——必须被注入到 YouTube 的应用包里，重新打包成 `.ipa`，再通过 sideload 签名安装到设备。

## 与 uYouPlus、YouTubeReborn 的对比

iOS 上的 YouTube 增强 tweak 有三个主流选择，定位不同：

| 维度 | YTLite (YouTube Plus) | uYouPlus | YouTubeReborn |
|---|---|---|---|
| 核心定位 | 界面定制 + 下载 | 下载为主，界面定制为辅 | 去广告 + 界面调整 |
| 下载能力 | 视频、音频、缩略图、帖子、头像 | 视频、音频（uYou 组件） | 视频、音频 |
| SponsorBlock | 内置 | 需额外集成 | 需额外集成 |
| 界面定制选项 | 100+，包括 OLED、Shorts-only、Feed 清理 | 较少，主要靠 uYou 设置 | 中等 |
| PiP（画中画） | 通过 YouPiP tweak 集成 | 通过 YouPiP tweak 集成 | 内置 |
| 4K 解锁 | 通过 YTUHD tweak 集成 | 通过 YTUHD tweak 集成 | 内置 |
| 定价 | 5.2 起订阅制，5.2b4 免费版 | 完全免费 | 完全免费 |
| 维护活跃度 | 活跃，订阅制后社区有分歧 | 活跃，社区最大 | 活跃 |
| 构建方式 | GitHub Actions 自动构建 | GitHub Actions 自动构建 | GitHub Actions 自动构建 |

三者都依赖 PoomSmart 的 tweak 生态（YouPiP、YTUHD、Return YouTube Dislikes、YouQuality），区别在于整合方式和额外功能。YTLite 的差异化在界面定制的颗粒度——能移除 Feed 里的具体元素、重排底部标签、启用纯黑 OLED 模式、把应用限制为 Shorts-only 模式。这些功能对「把 YouTube 当主力信息源」的用户有价值，对偶尔看视频的用户是过度配置。

选择逻辑可以这样拆：下载是刚需，uYouPlus 的 uYou 组件更成熟；界面控制是刚需，YTLite 更合适；只是去广告，YouTubeReborn 最轻量。

## Sideload 签名机制与 7 天续签

iOS 不允许安装未签名的应用，tweak 注入后的 YouTube 也面临这个问题。YTLite 的安装路径是 sideload，流程如下：

1. 准备一份解密的 YouTube `.ipa` 文件（仓库因法律原因不提供，需自行获取）
2. Fork YTLite 仓库，在 GitHub Actions 里运行 `Create YouTube Plus app` workflow
3. Workflow 把 YTLite 的 `.dylib` 注入到 YouTube `.ipa`，重新打包
4. 下载打包后的 `.ipa`，用 Sideloadly、AltStore 等工具签名安装到设备

签名机制决定了使用成本：

- **免费 Apple ID 签名**：7 天有效期，到期后应用无法打开，需要重新签名。AltStore 可以在同一个 WiFi 下自动续签，但要求电脑定期开机运行 AltServer。
- **付费 Apple Developer 账号签名**：1 年有效期，无需频繁续签，账号成本 99 美元/年。
- **企业证书签名**：理论上长期有效，但苹果会撤销违规企业证书，且企业证书来源灰色，不建议个人使用。

YTLite 仓库里的 `Sideloading.x` 文件包含侧载检测逻辑——这是为了在检测到 sideload 环境时调整某些功能（某些 hook 在越狱环境和 sideload 环境行为不同）。这也说明这个 tweak 同时支持越狱和 sideload 两种安装方式。

## SponsorBlock 集成方式

YTLite 内置 SponsorBlock，这是它相比 uYouPlus 的一个优势。SponsorBlock 是一个众包项目，社区成员标记 YouTube 视频中的赞助片段、片头片尾、自我推广等片段，客户端在播放时自动跳过。

集成方式是 YTLite 直接调用 SponsorBlock 的公开 API。播放视频时，tweak 拿到视频 ID，向 SponsorBlock API 查询该视频的片段标记；返回的标记包含片段类型（sponsor、intro、outro、selfpromo 等）和起止时间；播放器在到达标记起点时自动跳到终点。

这个机制依赖网络请求，首次播放有轻微延迟；标记数据来自社区，冷门视频可能没有标记。YTLite 的设置里可以配置跳过哪些类型的片段，这是「100+ 可配置选项」的一部分。

## 订阅制后的免费版本边界

5.2 版本是一个分水岭。从 5.2 开始，YTLite 转为订阅制，最后一个免费版本是 [5.2b4](https://github.com/dayanch96/YTLite/releases/tag/v5.2b4)。

这个边界对采用决策的影响：

- **5.2b4 及之前**：完全免费，功能完整，但不会获得新功能更新，只可能收到针对 YouTube 版本适配的紧急修复
- **5.2 及之后**：需要订阅，仓库代码仍然公开，但构建产物（release 里的 `.ipa`）需要订阅才能下载

仓库代码本身没有闭源，有能力的用户仍然可以自行构建最新版本，但需要自己处理签名和 YouTube 版本适配。对大多数用户来说，实际选择是在「免费版 5.2b4 + 锁定旧版 YouTube」和「订阅最新版 + 跟随 YouTube 更新」之间。

需要注意：YouTube 会持续更新，旧版 YouTube 可能 eventually 无法登录或无法播放（Google 服务端会拒绝过旧客户端）。5.2b4 锁定的 YouTube 版本越旧，这个风险越高。

## 适用人群与风险边界

按场景给出采用判断：

- **重度 YouTube 用户、对界面有强控制需求**：订阅 YTLite 5.2+，配合 Apple Developer 账号签名避免 7 天续签。SponsorBlock 内置加 OLED 模式加 Feed 清理的组合在 iOS 上没有更好的替代。
- **轻度用户、去广告和下载需求**：用 uYouPlus，免费、社区大、更新频繁。不必为 YTLite 的界面定制能力付费。
- **越狱设备用户**：YTLite 同时支持越狱安装，越狱环境下无需 sideload 续签，体验最好。但越狱本身有安全代价，不在本文讨论范围。
- **企业设备或 MDM 管理设备**：不要装。sideload 应用在 MDM 环境下会被识别和清理，且企业设备装 tweak 有合规风险。

风险边界需要明确：

- **账号风险**：Google 可能检测到非官方客户端并限制账号（从警告到封号）。YTLite 不修改请求指纹，风险低于修改客户端 ID 的 tweak，但不是零风险。
- **签名风险**：免费 Apple ID sideload 的 7 天续签是硬约束，忘记续签应用就打不开。AltStore 自动续签依赖电脑开机，不是完全无感。
- **更新风险**：YouTube 更新后，旧版 tweak 可能失效。YTLite 的「支持的 YouTube 版本」是硬约束，装错版本会导致 hook 失败或应用崩溃。
- **法律风险**：下载 YouTube 视频违反 YouTube 服务条款，SponsorBlock 跳过赞助损害创作者收益。这两个行为在个人使用层面很少被追究，但属于灰色地带。

最后一条：YTLite 的代码质量在 iOS tweak 圈里属于上游水平，Logos 加 Objective-C 的组合是这一类工具的标准写法，读 `YTLite.x` 和 `Settings.x` 能学到 method swizzling 的实际用法。但读代码和装到主力设备是两件事——主力设备上的稳定性和账号安全比 tweak 功能更重要。
