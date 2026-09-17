---
title: "Tinycast：一个不到 100 MB 内存的全原生 macOS 启动器"
date: 2026-09-18T03:40:00+08:00
slug: "tinycast-native-macos-launcher"
github_repo: "abue-ammar/tinycast"
source_key: "gh:abue-ammar/tinycast"
description: "Tinycast 用 Swift 6 与 SwiftUI/AppKit 写成一个零第三方依赖的 macOS 启动器，内存占用低于 100 MB，还能原生跑 Raycast 扩展。本文梳理它的功能清单、安装路径与适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["macOS", "Swift", "启动器", "开源软件", "效率工具"]
---

## 核心判断

macOS 启动器这个品类长期被两极占据：一极是 Raycast 这样的重量级选手，功能全面但基于自己的扩展生态持续膨胀；另一极是系统自带的 Spotlight，轻，但定制能力有限。Tinycast 选择了一条罕见的路线：**用 Swift 6 + SwiftUI/AppKit 写一个全原生（fully native）的启动器，零第三方依赖、不用 Electron、无遥测，常驻内存低于 100 MB**——同时它还能直接运行已有的 Raycast 扩展，渲染为原生 SwiftUI 界面。

这个"原生 + 兼容 Raycast 扩展"的组合是它最大的差异化：你不是在 Raycast 和轻量工具之间二选一，而是用一个更小的运行时承接已有的扩展资产。截至本文写作，仓库约 6.1k stars、283 forks，2026 年 6 月底创建，Beta 渠道保持接近每日的发布节奏，是一个活跃早期项目。

## 它能做什么

README 列出的功能覆盖了启动器的常规盘面，几项值得单独说：

- **应用启动 + 全局热键**：模糊搜索启动应用、置顶收藏、查看运行中的应用；一个全局快捷键从任意位置呼出面板。还支持给单个应用绑定专属热键，按键即在"聚焦/隐藏"间切换。
- **剪贴板历史**：文本与图片，可搜索，直接回贴到当前应用。
- **文件搜索**：复用 Spotlight 索引，自己不建索引——这是一个明确的工程取舍，省掉了索引进程的内存和磁盘开销。
- **计算器**：面板内联完成数学、单位、实时汇率与加密货币换算。
- **Quicklinks / Snippets / 自定义命令**：URL、搜索、深链变成命令；Markdown 模板带动态占位符与关键词展开；shell 命令可通过模糊搜索或独立热键执行。
- **窗口管理**：34 个 Rectangle 风格的操作（半屏、四分之一、三等分、跨显示器移动、Spaces 切换等）。
- **Apple Shortcuts 集成**：搜索并运行"快捷指令"应用里建好的 shortcut。
- **AI 聊天与 Quick Actions**：可用自己的 API key 在面板内聊天，对选中文本做改语法、改写、翻译、摘要。README 特别强调 AI 功能默认关闭。

对中文用户来说，这类工具的实际价值取决于日常流程中有多少动作可以收敛进面板。Tinycast 的功能面已经接近 Raycast 的常用子集，差距主要在扩展生态的广度——而它用 Raycast 扩展兼容来补这一块。

## 工程取舍：为什么能小

Tinycast 的小不是优化出来的，是选型决定的：

| 决策 | 含义 |
|---|---|
| SwiftUI + AppKit，零第三方依赖 | 没有 Electron/Chromium 运行时，没有依赖链的版本漂移 |
| 文件搜索走 Spotlight | 不维护私有索引，省掉常驻索引开销 |
| 无遥测 | 没有上报链路，也少一个隐私面 |
| 内存预算写进贡献指南 | README 的贡献要求里明确每个 PR 受内存预算约束，视觉改动需提交前后对比视频 |

这套约束也解释了它对功能请求的保守态度：贡献指南要求先开 issue 征得同意再写代码，未关联 approved issue 的 PR 会被直接关闭，且"别的启动器有"本身不构成加功能的理由。对一个以"小"为核心卖点的项目，这是合理的自我保护。

## 安装

通过 Homebrew 安装（macOS 26 及以上）：

```sh
brew trust --tap abue-ammar/tinycast
brew tap abue-ammar/tinycast
brew install --cask tinycast          # Apple silicon，macOS 26+
brew install --cask tinycast-universal # Intel
```

Homebrew 会在安装和更新时自动清除隔离标记。如果从 Releases 页下载 DMG，应用是自签名的，需要手动清一次：

```sh
xattr -dr com.apple.quarantine "/Applications/Tinycast.app"
```

首次使用需要在 **Settings → General** 录制全局快捷键；粘贴和关键词展开功能需要授予辅助功能（Accessibility）权限，系统会在首次使用时提示。

值得注意的是它的最低系统要求是 macOS 26——这是相当激进的新系统门槛，还在 macOS 15 Sequoia 上的用户只能用不再维护的 `tinycast-sequoia` cask。另外它可以直接导入 Raycast 的现有配置（Settings 里提供 import from Raycast），迁移成本较低。

## 适用边界

- **需要 macOS 26+**：老系统用户基本无缘主线版本。
- **AGPL-3.0 许可证**：个人使用无感，但想基于它做商业分发的人需要认真读一遍 AGPL 的传染条款。
- **单人项目，功能集刻意封闭**：README 明说功能面是"deliberately closed"，期待它快速长出长尾功能的人可能会失望。
- **早期阶段**：主版本还在 0.11.x beta，日常稳定性尚可（beta 渠道日更），但 API 和行为仍可能变化。

## 结论

Tinycast 的意义在于证明了一件事：在不牺牲功能广度（Raycast 扩展兼容）的前提下，macOS 启动器可以做到原生、无依赖、百兆内存以内。对于在意内存占用、不喜欢 Electron、又已经积累了一批 Raycast 扩展的用户，它值得装一个试试；对依赖冷门扩展或老系统的用户，现在观察就好。

项目地址：[abue-ammar/tinycast](https://github.com/abue-ammar/tinycast)
