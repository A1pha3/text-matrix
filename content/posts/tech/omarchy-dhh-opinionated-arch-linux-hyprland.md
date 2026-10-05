---
title: "Omarchy：DHH 的「禅意 Linux」，从「有主见」走向「agentic」"
date: 2026-08-30T03:33:00+08:00
lastmod: 2026-10-04
draft: false
description: "DHH 主导的 Omarchy 把 Arch、Hyprland、Quickshell 和一套精心挑选的应用打包成「有主见」的 Linux 发行版，一个月内又把官方定位语从 opinionated 改成了 fun & agentic。本文从安装体验、快捷键体系、omarchy CLI、AI 编程代理集成到快照回滚，拆解它凭什么拿下 4.4 万 star。"
tags: ["Linux", "Arch", "Hyprland", "AI Agent", "开源"]
categories: ["技术笔记"]
github_repo: "omacom/omarchy"
source_key: "gh:omacom/omarchy"
slug: omarchy-dhh-opinionated-arch-linux-hyprland
---

## 一个反常识的产品：把「折腾」卖成「不需要折腾」

Linux 桌面圈有个长期共识：想要 Hyprland 这种平铺式窗口管理器的体验，就得接受在 Arch Wiki 里泡一周的代价。装系统、配显卡、调 HiDPI、写配置文件——这套流程几乎是「极客身份认证」。

Omarchy 的立场恰恰相反：**这套体验应该像 MacBook 开箱一样直接能用**。它是 Ruby on Rails 之父 David Heinemeier Hansson（DHH）主导、omacom 团队维护的 Linux 发行版，官方一句话介绍是 "Beautiful, modern & opinionated Linux"——美丽的、现代的、**有主见的**。

"Opinionated（有主见）" 是理解这个项目的钥匙。它不提供安装向导让你从几十种组件里挑，而是直接替你做完所有决定：Arch 作底、Hyprland 作窗口管理器、Quickshell 作桌面外壳、SDDM 作登录管理器、snapper 做快照、Limine 做引导。预装 Neovim、Chromium、Obsidian、LibreOffice、Kdenlive、OBS Studio，甚至还有一个复古 Winamp 风格的终端音乐播放器 Cliamp。手册开场白说得直白："There's zero bloat here: Just everything I use"——这里没有臃肿，只有我在用的一切。

这种「禅意组装」（omakase，日语「お任せ」，意为「交给主厨决定」）哲学与 Rails 一脉相承：框架替你做约定，你专注于做事本身。但官方同时强调 "But this is your computer. You're free to change everything"——有主见不等于锁死，所有替你做的决定都可以推翻。

数据能说明热度：2026-10-04 的 GitHub 读数是 43,931 star、5,201 fork，主语言 Shell，MIT 协议，最新版本 v4.0.4（9 月 15 日发布），当天还在合并提交。本文发表那周仓库还在 3.5 万 star，五周涨了近 9 千。真正值得注意的信号藏在文案里：发文两天后（9 月 1 日，PR #9584），官方把定位语从 "Beautiful, modern & opinionated" 改成了 **"Beautiful, fun & agentic"**；官网现在的副标语是 "The malleable OS for the age of agents"——「有主见」的发行版，正在把自己重新定义为「AI 代理时代的可塑系统」。

## 安装：一分钟级别，但有两个必须知道的坑

Omarchy 通过 ISO 安装，支持两种模式：

- **整盘安装**：擦掉整块硬盘（默认全盘加密）
- **空闲空间安装**：装在未分配空间里，实现与 Windows 双启动（需先在 Windows 里关闭 BitLocker）

手册给的参考时长是：最快的机器上不到 1 分钟，老机器也不超过 5 分钟；官网的口径更激进——"as little as 35 seconds on the fastest machines"。

两个容易踩的坑值得提前说：

1. **必须在 BIOS 里关闭 Secure Boot 和 TPM**。手册的解释很直接：这些是微软为 Windows 及其盟友发行版设计的安全机制，Omarchy 不在此列。
2. **全盘加密的密码输入不支持蓝牙键盘**。开机解密阶段蓝牙驱动尚未加载，需要有线键盘或 2.4GHz 接收器键盘。

安装器还藏着两个进阶选项：在第一屏按 `Ctrl+C` 可以切换为「替他人安装」模式——个人化配置（键盘布局、用户名、密码）延迟到对方首次开机时完成，密码同时就是加密密码；在磁盘格式化确认时按 `Ctrl+C` 则可以切换为无加密安装。已经用起来的机器要送人，也不必重装，安全手册里的 reset 流程可以把它交还给新主人。另外 ISO 支持完全无人值守安装（把配置放在第二块盘上），适合批量装机和虚拟机基础镜像。

## 快捷键体系：Super 键就是一切

Omarchy 的交互哲学是「键盘优先」。所有绑定按 `Super + K` 随时查看（Tmux/Herdr 绑定分别是 `Super + Alt + K` 和 `Super + Ctrl + K`），无需背文档。

核心操作一层就能摸到：

| 按键 | 功能 |
|------|------|
| `Super + Space` | Omarchy 主菜单（应用和一切） |
| `Super + Escape` | 系统菜单（挂起、重启等） |
| `Super + W / Q` | 关闭窗口 |
| `Super + T` | 窗口在平铺/浮动间切换 |
| `Super + L` | dwindle 与滚动布局切换 |
| `Super + F` | 全屏 |
| `Super + 1/2/3/4` | 跳转工作区 |
| `Super + Shift + 1/2/3/4` | 把窗口移到对应工作区 |
| `Super + Tab` | 切换工作区 |
| `Super + S` | 切换 scratchpad（置顶便签区） |
| `Super + Arrow` | 按方向移动窗口焦点 |
| `Super + G` | 窗口分组 |

窗口调整也全在 Super 键体系内：`Super + Minus/Equal` 伸缩窗口，配合 Shift/Alt/Ctrl 变换步长；`Super + Alt + Home` 可以保存当前窗口宽度，之后用 `Super + Home` 恢复——这个细节对「这个窗口就该这么宽」的用户非常友好。

## omarchy CLI：给 AI 代理留的正门

这是 Omarchy 最有意思的设计之一。所有菜单和系统操作都封装进了 `omarchy` 命令行工具：

```bash
omarchy update              # 更新 Omarchy 和系统包
omarchy theme list          # 列出主题
omarchy theme set <name>    # 应用主题
omarchy font list           # 列出字体
omarchy screenshot          # 截图
omarchy debug               # 打印调试信息
```

手册原文点明了动机：**"This is particularly helpful when you're having an AI agent work with you on customization or configuration"**——当你让 AI 代理帮你定制系统时，这个 CLI 特别有用。命令按组划分，每组还有独立的 `--help`，分组清单由 `bin/omarchy` 里的 `GROUP_DESCRIPTIONS` 表驱动，五十多个组覆盖音频、蓝牙、亮度、剪贴板、显示、网络、电源。方向的变化写在 `agent` 组的描述里：这五周它从 "AI coding agent usage data" 升级成了 "AI coding agents, their usage, and subscription accounts"，旁边还新开了 `openclaw` 组——CLI 的重心正随着整个项目的叙事往 AI 代理倾斜。

仓库里也确实有 `agents/` 目录和 AGENTS.md、CLAUDE.md 文件——这是一个从第一天就为「人类 + AI 协作管理桌面」设计的发行版。

## AI 编程代理：从「正门」到「主航道」

如果说 CLI 只是给 AI 留了扇门，`manual/17-ai.md` 整章展示的就是门后的房子。Omarchy 把 AI 编程代理当一等公民，但不替你选边：十几个主流编程代理 CLI 全部预接线，以 mise 管理的 lazy 桩命令放在 `~/.local/bin/`，第一次真正运行才下载。现役清单包括 `claude`（Claude Code）、`codex`（OpenAI Codex）、`opencode`、`agy`（Google Antigravity CLI）、`copilot`（GitHub Copilot CLI）、`crush`、`grok`、`pi`、`omp`（Oh My Pi）、`ori`（OpenRouter 的 harness，能把其他代理跑到任意模型上），这一个月又新增了 `hermes`（Nous Research）、`muse`（Meta 的 Muse Code）和 `cursor-agent`（Cursor CLI）。选 Claude 为默认代理时还会顺带给 Chromium、Chrome、Brave、Edge 装浏览器扩展，让浏览器里的 Claude 与终端打通。

默认代理机制是整套设计的枢纽：

- `omarchy default agent <name>` 或菜单里选择，装好的机器会弹一次性通知邀请你做这个选择
- `Super + Shift + Ctrl + A` 在独立终端窗口启动默认代理
- `omarchy agent prompt "Review this project"` 直接把任务派给代理，代理以「不中途停下来问」的模式运行——准备好它会真的动你的系统
- 代理拒绝为家目录记住信任，所以从 `$HOME` 启动时会自动切到 `~/Work`

顶栏的 agents 面板把所有订阅集中在一页：每个代理和账户的套餐、5 小时会话与每周限额的用量百分比（或预付余额），底下还有跨代理的汇总（本周 token、最常用模型）。这一个月它还长出了多账户管理：同一提供商的多个付费套餐（比如一个个人 Max、一个公司账号）可以同时登录，`omarchy agent account add claude Work` 添加、`account use` 切换、`account mode auto` 开启自动切换——活跃账户用量过阈值默认弹通知（阈值 95%），自动模式下超阈值就切到余量最大的账户，临近阈值时轮询频率从 15 分钟加密到 3 分钟。

更激进的是崩溃诊断：Omarchy 监听 systemd-coredump，进程段错误时弹出「Process crashed」通知，点一下就把 core dump 连同 diagnose-crash 技能一起交给默认代理，由它判断这个崩溃值不值得报给上游。不想被打扰可以 `omarchy crash mute hyprland` 按程序静音。

连主题都是联动的：切换 Omarchy 主题时，Claude Code、Pi、OpenCode（以及装了 Hermes 之后的 Hermes）会跟着换装。这一个月新出现的 `default/agents/skills/omarchy-app/` 则是一份官方 agent 技能——教代理按 Omarchy 自家应用（Hype、Monologue、Omacut）的方式用 C++ 和 Qt Quick 写桌面应用，编译器和 Qt 依赖随系统预装。换句话说，这个发行版不仅让 AI 代理管理自己，还在教代理给它造应用。

## TUI 工具箱：终端里长出完整工作流

Omarchy 预装了一套打磨过的 TUI 应用，几乎每个都绑了快捷键：

- **Lazygit**（终端里的 Git 图形客户端，Neovim 内 `Space G G` 启动）
- **Lazydocker**（`Super + Shift + D`，容器管理）
- **Btop**（`Super + Ctrl + T`，系统资源监控，菜单里叫 Activity）
- **Herdr**（`Super + Ctrl + Return`，持久化会话的终端工作区管理器，可 detach/reconnect；快捷键手册直接叫它 agent manager）
- **Fastfetch**（系统信息，菜单里的 About）
- **dua**（磁盘占用分析，交互式下钻定位空间杀手）
- **Cliamp**（`Super + Shift + Alt + M`，Winamp 2.x 风格音乐播放器，内置 lo-fi 电台）

这份清单体现了 Omarchy 的选品标准：不是堆砌「最受欢迎」的工具，而是每个场景选一个作者自己真正在用的。

## 快照与回滚：敢在滚动发行版上「有主见」的底气

Arch 是滚动更新发行版，坏更新是真实风险。Omarchy 的答案是 snapper 快照 + Limine 引导：

1. **每次系统更新自动创建快照**，也可手动 `omarchy-snapshot create`
2. 出问题时在 Limine 引导菜单里选择历史快照启动
3. 进入快照系统后点通知即可恢复，或直接 `omarchy-snapshot restore`

配套的纪律是：手册明确拦下直接跑 `pacman -Syu` 的老手——那样会错过随包更新一起走的快照、迁移和配置更新，系统会把你引回 `omarchy update`。

需要注意的边界：快照恢复的是根文件系统，**不包含 `/home`**——它解决的是「坏更新回滚」，不是「误删文件恢复」。且该功能仅适用于 Limine 引导的安装（Omarchy 2.0 起默认；GRUB 或 systemd-boot 的老安装没有）。如果从不碰引导菜单，也可以在菜单里开启 Direct Boot 直进系统，代价是恢复快照前得先从 BIOS 手动选 Limine；部分固件（American Megatrends 和 Apple）不认自定义 EFI 条目，Direct Boot 在这些机器上会拒绝开启。

## 仓库结构速览：一个 Shell 驱动的发行版长什么样

从仓库根目录能清晰看到它的组织方式：

- `default/` — 系统默认配置的源头（hypr、pacman、sddm、snapper、systemd、uwsm、foot/ghostty/alacritty 终端配置、chromium/firefox 等）
- `install/` — 安装器（config、hardware、provisioning、必装包清单 `omarchy-base.packages` 与可选包 `omarchy-other.packages`）
- `manual/` — 51 篇手册文档，是官方文档的权威源
- `agents/` — 给 AI 贡献者的 7 篇任务指南（加命令、写安装脚本、改 Quickshell 桌面、做验收测试等）
- `themes/`、`bin/`、`shell/`、`migrations/`、`test/` — 主题、CLI 入口、shell 逻辑、版本迁移与测试

AGENTS.md 把文档切成三棵树：`agents/skills/` 是「做 X 时读这篇」的任务程序，`docs/` 是系统形状的参考，`manual/` 是最终用户文档——界限是给谁看的，而不是内容属于哪个模块。

值得注意 `migrations/` 目录的存在：一个「有主见」的发行版必须替既有用户处理版本间的配置变迁，这是它与「一套 dotfiles 集合」的本质区别。另外手册覆盖了 Mac 外设支持、双系统、Windows 虚拟机、游戏、PDF 填写等长尾场景——51 篇的体量说明它认真对待「日常主力机」这个定位。

## 适合谁，不适合谁

**适合**：想体验平铺窗口管理器 + 终端优先工作流、但不想从零配置的人；Rails/DHH 的追随者；想把 Linux 变成「开箱即用的生产力工具」而非爱好本身的人；以及想让 AI 代理帮自己管理桌面的尝鲜者。

**不适合**：需要 Secure Boot/TPM 合规环境的企业用户；依赖蓝牙键盘且只愿全盘加密的用户；想精细挑选每一个组件的「控制型」用户——不过官方会提醒你，这只是默认有主见，每一层都可以改。

Omarchy 证明了一件事：Linux 桌面的「易用性」问题，未必需要靠向 Windows/macOS 靠拢来解决，也可以由一个品味极高的人把「硬核路线」替你配好。而它这一个月的演变给出了第二层判断：当一个发行版把「给 AI 代理的正门」做成主航道，桌面 Linux 的竞争维度可能正在从「对人多友好」变成「对代理多友好」。这大概是它能持续登上 GitHub 趋势榜的真正原因。

> 仓库：[omacom/omarchy](https://github.com/omacom/omarchy) · 官网：[omarchy.org](https://omarchy.org) · 协议：MIT · 当前版本：v4.0.4（2026-10-04 读数：43,931 star）
