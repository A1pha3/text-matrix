---
title: "Omarchy：DHH 主理的 Omakase Linux，从开箱即用到 agentic 桌面系统"
date: 2026-08-17T03:26:00+08:00
slug: "omarchy-dhh-opinionated-linux-distro-guide"
github_repo: "basecamp/omarchy"
source_key: "gh:basecamp/omarchy"
description: "Omarchy 是 DHH 基于 Arch + Hyprland + Quickshell 主理的 Linux 发行版，把「主厨精选」的桌面打包成带包仓库、迁移系统与快照回滚的可维护产品；v4 之后 AI 编码代理成为一等公民。本文梳理其设计哲学、安装路径、更新机制与适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["Linux", "发行版", "DHH", "Hyprland", "Quickshell", "开源"]
---

Linux 桌面世界有个老问题：可定制性无限，但默认体验粗糙。装完 Arch，面对的是黑屏和 Wiki；装完 Ubuntu，面对的是想删掉一半的预装软件。Omarchy 走的是第三条路——由 Ruby on Rails 作者 DHH 主导、37signals 孵化，基于 Arch Linux，把他本人的桌面直接打包成发行版。仓库 2025 年 6 月创建，截至 2026 年 9 月中旬约 40,500 stars、4,500 forks——一年出头跑到这个量级，在 Linux 桌面类项目里属于头部。

先给判断：Omarchy 的价值不在技术创新——Arch 加 Hyprland 谁都能装——而在两件更难的事上：把数千个选择压缩成一套自洽的默认值，再给这套默认值配上产品级的维护体系（自建包仓库、迁移脚本、快照回滚、更新通道）。后一半是它和 GitHub 上随处可见的「一键安装脚本」的分界线。2026 年 8 月发布的 v4.0（代号 Quattro）之后，它又多了一层新身份：官方标语从仓库里的「Beautiful, Modern & Opinionated Linux」升级为官网上的「Beautiful, fun & agentic Linux」——AI 编码代理成了一等公民；同月项目又成立 Omacom 基金会，首发 800 万美元来自八位创始赞助人（含 Michael Dell、Jack Dorsey、Cloudflare 的 Matthew Prince），几天后随追加出资突破 1000 万，商标、基础设施与上游依赖由此转入机构托管。

## Omakase：厨师发办式的设计哲学

项目名 Omarchy 来自日语 Omakase（お任せ，「交给厨师发办」）。这个比喻精确概括了它的取舍：你放弃每个细节的选择权，换来一套经过深思熟虑的完整方案。

技术栈分四层，各司其职：

| 层 | 选择 | 角色 |
|---|---|---|
| 系统底座 | Arch Linux | 滚动更新，软件永远新 |
| 窗口管理 | Hyprland（v4 基于 0.56） | 平铺式窗口管理器，动画流畅、可脚本化；v4 起 Omarchy 的 Hyprland 配置全面转 lua |
| 桌面 Shell | Quickshell | 单进程插件架构，承载顶栏、启动器、通知、锁屏、控制面板 |
| 维护体系 | omarchy CLI + 自建包仓库 | 更新、迁移、快照、主题的统一入口 |

预装清单同样有观点：Neovim 是默认编辑器（欢迎文档里带着「(btw)」的自嘲）、Chromium 浏览器、Obsidian 笔记、LibreOffice 办公套件、Kdenlive 视频剪辑、OBS Studio 录屏直播，v4 起默认终端是 Foot，甚至还有一个复古 Winamp 风格的音乐播放器。DHH 在手册里的原话：「There's zero bloat here: Just everything I use.」（这里没有冗余软件，只有我用的所有东西。）

## 为什么「美」是功能而不是装饰

Omarchy 的欢迎文档有一句值得引用的话：「a beautiful system is a motivating system, and productivity has always been downstream from motivation」（美的系统是激励人的系统，而生产力一直是激励的下游）。

这不是情怀，是产品判断。Linux 桌面长期输给 macOS 的不是能力，是第一次开机时的质感。Omarchy 把主题系统、壁纸、终端配色、TUI 的视觉一致性都当作一等公民：v4 把主题色从 8 色扩到 24 色，切换主题时 btop、Neovim、VS Code 的配色跟着整套换。代价是它不试图像 Windows 或 macOS——手册原话：「It's not trying to be as familiar as possible. It's trying to be beautiful and _better_.」手动编辑配置文件、重度终端，这些 Linux 味道十足的使用方式都被正面拥抱。

## v4 Quattro：从配置合集到可维护的产品

2026 年 8 月 14 日发布的 v4.0.0 是官方自称「项目开始以来最大的一次发布」，之后小版本快速迭代，官网当前下载为 4.0.4。三个变化最值得注意。

**桌面 Shell 整体重写。** 顶栏、启动器、菜单、通知、OSD、控制面板、锁屏、polkit 代理全部收敛进 Quickshell 单进程，改为插件架构；原先拼装的 Waybar、Walker、Mako、SwayOSD、hyprlock、hypridle 等组件全部移除。Shell 从轮询改为事件驱动，空闲时不再占用 CPU。

**交付方式改为系统包。** 内部文件从 git 仓库迁到 pacman 包，ISO 瘦身超过 1 GB（降到 6 GB 以下），官方称安装提速三成。这一步不显眼，却是维护体系能成立的前提：只有包化，才能有干净的迁移与回滚。

**生态开口。** 新增插件系统（`omarchy plugin add <git-url>`，社区索引站 plugins.omarchy.org）；双系统安装、出厂重置、为他人预装、无人值守安装这些「分发」能力也都在 v4 落地。

## AI 代理是一等公民

v4 之后官网的副标题是「The malleable OS for the age of agents」，这不只是口号，手册里有一整章 AI 集成：

- **预接线的编码代理**：Claude Code、Codex、OpenCode、Gemini CLI、Copilot CLI 等近十个代理 CLI 以 mise 管理的 stub 形式放进 `~/.local/bin/`，首次运行才真正下载——装系统时不背这些工具的体积。选一个默认代理（`omarchy default agent <名称>`）之后，`Super + Shift + Ctrl + A` 一键唤起，还能 `omarchy agent prompt "Review this project"` 直接派活——代理以无人值守模式运行，会真的动手改东西。
- **用量面板**：顶栏出现 agents 图标（检测到 AI 使用后才出现），聚合各订阅的用量——5 小时窗口与周限额的百分比、按天按模型的 token 消耗。对同时付多份订阅的人，这省掉了挨个查后台的功夫。
- **崩溃诊断**：系统监听 systemd-coredump，进程段错误时弹出通知，点击即把 core dump 连同 diagnose-crash 技能交给默认代理，让它先判断这个崩溃值不值得报上游。
- **Omarchy Skill**：随系统附带一个教代理修改系统本身的技能（调 Hyprland、改顶栏、做主题），symlink 进 Claude Code、Codex 等各家技能目录。官方标注 experimental，建议先在 plan 模式看它想改什么再放行——代理把配置改砸了，`omarchy reinstall configs` 能兜底。

对把编码代理当日常工具的人，这一层是 Omarchy 和其他发行版差距最大的地方：主题切换能同步给代理（Claude Code、Pi、OpenCode 等跟随），用量有面板，崩溃有诊断——代理被当成系统公民，而不是装完就忘的 CLI。

## 装一台 Omarchy：流程与硬件

安装走 ISO：从 omarchy.org 下载（当前为 4.0.4，附 SHA-256 与签名文件），用 balenaEtcher（Mac/Windows）或 caligula（Linux）写入 U 盘，启动后回答五个配置问题、选一块盘，然后等它装完——官方口径是快机器一分钟以内，老机器也不超过 5 分钟。全盘加密默认开启；既可全盘安装，也可只占用磁盘未分配空间，与 Windows 双系统共存（后者需先在 Windows 里关闭 BitLocker）。

三个容易踩的坑：

- **BIOS 里必须关闭 Secure Boot 和 TPM**。手册解释得很直白：这是微软面向 Windows 及其附属发行版的安全方案，不关装不上。
- **加密密码不能用蓝牙键盘输**。全盘加密的密码在启动早期输入，那时蓝牙驱动还没加载，需要有线或 2.4G 接收器键盘。
- **NVIDIA 看硬件支持面**。官网的说法是「包括 NVIDIA 在内的图形驱动与配置都在安装时自动处理」——前提是受支持的硬件。NVIDIA 老卡用户建议装前翻一下手册的故障排查章。

硬件门槛低得出奇：官网举的例子是 2011 年的 ThinkPad X220 加 2 GB 内存就能流畅运行。x86 PC 和 Intel Mac 是正式支持对象；Apple Silicon 也不再只能靠虚拟机——9 月 11 日官方宣布 Omarchy M 团队，首个发行版本目标完美兼容 M1/M2（含 Pro/Max），配套的免 U 盘原生安装器已能把 Omarchy 分区进既有 macOS 旁；上手前更可以先用 Try Omarchy——一个在 macOS 上以原生应用运行、带硬件加速、接驳摄像头/音频/剪贴板的体验版，不用分任何盘。替别人装机的场景也考虑到了：装机给家人或新员工时，在安装器第一屏按 `Ctrl + C`，键盘布局、用户名、密码这些个人设置会推迟到新主人首次开机时填写；把配置文件放在第二块盘上，ISO 还能完全无人值守安装——把它当 VM 或批量机器的基础镜像用。

## 更新与回滚：滚动发行版的保险丝

Arch 系最大的心理负担是「滚挂了怎么办」。Omarchy 的回答是一套组合拳，值得跟着一次完整的更新走一遍：

1. 新版发布后，时钟右侧出现升级图标。点它（或在菜单选 Update > Omarchy，终端里即 `omarchy update`）。
2. 更新先自动打系统快照——快照能力来自 Limine 引导器（Omarchy 2.0 起为默认；GRUB 或 systemd-boot 安装没有此功能）。
3. 包管理器依次完成三件事：安装最新 Omarchy 包（来自官方自建的包仓库）、跑完所有待执行的迁移脚本把本机配置同步到新版、更新 Arch 系统包（来自 Omarchy 官方 mirror 与 AUR）。
4. 一切正常则结束；出了问题，重启后在 Limine 引导菜单里选更新前的快照启动，点通知确认恢复，系统回到更新前的状态。

第 3 步的迁移（migrations）是「配置合集」与「产品」的又一个分界：上游改了配置结构，由迁移脚本替你改本机配置，而不是靠用户重读变更日志手动跟进。稳定通道的 Arch mirror 还刻意落后正式源一个月，专门用来提前暴露需要配置变更的不兼容。更新通道共四条：stable、RC、edge、dev，新装机默认 stable，想帮着测新版本再去换 edge。

回滚有一条明确边界：快照恢复 root 文件系统，不动 `/home`。它能救挂掉的系统更新，救不了误删的个人文件；`~/.config` 原样保留，若回退到的旧版本库用旧配置格式，可能要手动处理。配置彻底搞坏还有 `omarchy reinstall` 兜底——重装全部默认包并把配置重置为默认（你对默认值的修改会被覆盖）。

另外别绕过它直接 `pacman -Syu`：那样会跳过快照和迁移，Omarchy 会主动拦截直接升级并指回 `omarchy update`（确有把握可按提示对单次事务放行）。

## 手册即文档

Omarchy 把用户手册直接放在仓库的 `manual/` 目录（当前 51 篇，另有在线镜像 learn.omacom.io，更新往往滞后于仓库），作为权威信息源。内容覆盖四个层次：

- **基础**：上手、从 Mac/Windows 迁移、导航、顶栏、主题、快捷键、剪贴板、截图录屏、Omarchy CLI。
- **应用**：终端、Neovim、AI 工具、开发工具、TUI、GUI、浏览器、游戏、PDF、Windows 虚拟机。
- **配置**：更新、dotfiles、Shell 插件、显示器、键鼠、网络、字体、壁纸、自制主题。
- **其余**：Mac 硬件支持、故障排查、FAQ、系统快照、安全、双系统安装、无人值守安装。

把权威文档放进代码仓库，文档随版本演进、截图有明确归属，用户装之前就能通读整个系统要带自己去哪。对比多数发行版把文档散落在 Wiki、论坛和过时博客里的现状，这本身就是产品态度。

## 适合谁，不适合谁

适合：

- 愿意接受平铺窗口管理器交互范式（键盘优先、窗口自动排列）的用户
- 认同「有人替我做决定」的开发者——尤其是本来就欣赏 DHH 品味的那批人
- 想给编码代理配一台顺手机器的 AI 重度用户
- 手头有旧 x86 机器或 Intel Mac、想低成本体验完整 Linux 桌面的尝鲜者

不适合：

- 需要 Windows/macOS 式交互直觉的用户（手册自己就警告了这一点）
- 想从最小系统逐包搭建环境的 Arch 原教旨主义者
- 依赖特定商业软件（如 Adobe 全家桶）且不愿折腾虚拟机的用户——内置的 Windows 11 虚拟机没有 GPU 加速，定位是办公不是游戏

## 小结

Omarchy 是近年 Linux 桌面少见的「有明确作者意图」的作品，v4 之后它多了一层更少见的品质：可维护性。自建包仓库、迁移脚本、快照回滚、四条更新通道，让「一个重度用户的桌面偏好」能像软件产品一样持续交付出去——这是它和 GitHub 上无数 dotfiles 仓库的本质区别。

要上手，按成本从低到高：手头有旧机器或 Intel Mac，ISO 直装试水，代价几乎为零；Apple Silicon 先用 Try Omarchy 看真机效果，正式下手走已发布的 Omarchy M 原生安装器；考虑上主力机之前，先读一遍手册的 Navigation 和 Hotkeys 两章，确认自己能接受键盘优先的工作流——Omarchy 的美，建立在它不接受妥协的前提上。

- 仓库：https://github.com/basecamp/omarchy
- 官网：https://omarchy.org
