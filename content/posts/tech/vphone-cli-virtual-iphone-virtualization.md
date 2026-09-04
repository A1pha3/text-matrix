---
title: "vphone-cli：在 Mac 上启动一台虚拟 iPhone"
date: 2026-09-05T03:50:00+08:00
slug: "vphone-cli-virtual-iphone-virtualization"
github_repo: "Lakr233/vphone-cli"
source_key: "gh:Lakr233/vphone-cli"
description: "vphone-cli 利用 Apple Virtualization.framework 与 PCC 研究 VM 基础设施，在 Apple Silicon Mac 上一条命令创建并启动虚拟 iPhone：下载 IPSW、修补启动链、DFU 恢复、安装 CFW、首启。本文拆解其五档固件变体、手动流水线与自动化测试插座，并给出适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["iOS", "虚拟化", "macOS", "逆向", "自动化测试"]
---

## 核心判断

vphone-cli 把一件以前只存在于安全研究实验室的事变成了命令行操作：在 Apple Silicon Mac 上跑一台**真正的 iOS 虚拟机**——不是模拟器，而是用 Apple 自家 Virtualization.framework 启动的 iPhone 系统。它的技术路线基于 PCC（Private Cloud Compute）研究 VM 基础设施与社区对 Apple 虚拟化栈的逆向（致谢 wh1te4ever 的 super-tart writeup），整条链路是：下载并合并 IPSW → 二进制修补启动链 → DFU 恢复 → 安装 CFW（定制固件）→ 首次启动。两条命令即可完成：

```bash
vphone-cli vm create myphone -V jb   # 下载→修补→DFU→CFW→首启，全自动
vphone-cli vm launch myphone
```

这是一台可克隆、可导出、可程序化操控的 iPhone：SSH（端口 22222）、VNC（5901）、以及一个宿主机控制插座（vphone.sock），支持截图、触摸、滑动、硬件按键、剪贴板，每个动作返回内联截图——官方明确面向 AI 驱动的 E2E 测试场景，并配套了 vphone-mcp 的 MCP 服务器封装。

截至本文写作时，仓库 10.4k stars，作者 Lakr233（Axmlsoft 团队成员），需要 Apple Silicon + macOS 15+ + Xcode/iOS SDK。它是研究性质的工具，不是消费级产品——这一点决定了它的全部适用边界。

## 它实际上做了什么

Apple 官方从未开放"跑 iOS"的虚拟化能力；vphone-cli 的路径是深度修补 iOS 固件，让它接受 Virtualization.framework 的私有 PV=3 entitlement 环境。README 给出五档固件变体，安全旁路逐级加深：

| 变体 | 启动链补丁 | CFW 阶段 | 说明 |
|------|-----------|---------|------|
| `less` | 4 | 2 | 近乎无补丁，保留 iOS 全部缓解机制 |
| `regular` | 42 | 10 | 旁路 AMFI/SSV/Img4/TXM |
| `dev` | 53 | 12 | 加 TXM entitlement/debug 旁路 |
| `jb` | 113 | 14 | 完整越狱（首启自动装 Sileo、TrollStore） |
| `exp` | 141 | 18 | jb 超集 + 反 VM 检测研究补丁 |

逐组件的补丁对照在 `research/0_binary_patch_comparison.md`。`vm create` 自动跑完全部步骤；每一步也都可以手动驱动（`vm new` → `fw prepare` → `fw patch` → `vm launch --dfu` → `restore` → `cfw install` → `vm launch`），便于单阶段调试或换 IPSW 升级 iOS 版本。

## 宿主机要求：SIP/AMFI 放松

跑 PV=3 私有 entitlement 的无签名二进制，宿主机必须放松系统防护，README 给两条路：

- **方案 A（最宽松）**：恢复模式里 `csrutil disable` + `csrutil allow-research-guests enable`，重启后 `sudo nvram boot-args="amfi_get_out_of_my_way=1 -v"`。
- **方案 B（保留 SIP）**：`csrutil enable --without debug` + allow-research-guests，再用 `vphone-amfidont` 给单个二进制加白名单，AMFI 系统级保持开启。

`zsh: killed ./vphone-cli` 这个最常见的失败就是 AMFI 没绕过；嵌套虚拟机（Mac 本身是 VM）则直接不支持 PV=3。

## 生命周期管理

VM 的工程化程度超出预期：`vm clone` 用 APFS 快速克隆并生成新设备身份；`vm export` 默认 zstd 压缩（`--max` 走 xz -9）、自动跳过恢复目录；`vm import` 一条命令还原；`--json` 输出让 `vm list` 可脚本化。所有数据集中在 `~/.vphone/`（VMs、IPSW 缓存、工具链产物、deb 缓存、Python venv），可用 `$VPHONE_ROOT` 或分项环境变量重定向——签名后的 .app bundle 因此保持可移植。

已验证环境覆盖 iPhone 17,3 机型从 iOS 18.6.2 到 27.0 beta 的固件组合、macOS 15–27 beta 宿主，实测矩阵在 README 中完整列出。

## 值得记录的坑

README 的 FAQ 是真实使用踩坑的沉淀：初始设置地区不能选日本或欧盟（监管检查 VM 无法通过）；卡在"Press home to continue"时用 VNC 右键模拟 Home 键；`EXC_GUARD` 崩溃需 `--force-exc-guard` 重补丁（iOS 18 基底默认开启）；以及一个写得极认真的已知 bug——Homebrew stable 的 ldid-procursus 2.1.5 在遇到 entitlements 值恰为 0 的苹果系统二进制时触发 `__builtin_clzll(0)` UB，无符号循环计数下溢导致 ldid 无限写内存，需 `brew install --HEAD ldid-procursus` 重编。

## 适用边界

- **适合**：iOS 自动化测试（尤其 AI agent 驱动的 E2E）、安全研究、逆向分析、需要多台可重置 iPhone 的 CI 场景。控制插座 + MCP 封装让它天然适合接入 LLM 工具链。
- **不适合**：日常"想在电脑上玩手机"——SIP 放松、变体选择、DFU 流程的门槛都在；也不适合生产环境 App 分发验证（`jb`/`exp` 变体绕过了大量安全机制，行为与真机不一致，`less` 变体相对接近）。
- **许可证与合规**：修补苹果固件自用属研究范畴，但分发补丁后固件不在此列；具体法律边界仓库未展开，使用者自行评估。

安装：`brew install zqxwce/tap/vphone-cli`；源码构建走 `scripts/setup_tools.sh` + `build.sh`。

## 结语

vphone-cli 是 Apple 生态里少见的"把封闭平台拆开给你看"的工具：它不是官方能力的包装，而是社区对 Virtualization.framework 与 iOS 启动链理解的集大成。对做 iOS 自动化或安全研究的人，一台可克隆、可编程、几分钟重建的虚拟 iPhone 改变了实验的成本结构；对其他人，它更像一份可运行的逆向工程教材。

仓库地址：[Lakr233/vphone-cli](https://github.com/Lakr233/vphone-cli)
