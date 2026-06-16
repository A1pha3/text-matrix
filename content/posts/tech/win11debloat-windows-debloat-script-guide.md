---
title: "Win11Debloat：4.7 万 Star 的 PowerShell 脚本，给 Windows 10/11 做一次彻底、可回退的清理与定制"
date: "2026-06-15T21:02:07+08:00"
slug: "win11debloat-windows-debloat-script-guide"
description: "Win11Debloat 是一款单文件 PowerShell 脚本（MIT），47743+ Stars，支持 Windows 10/11。它能卸载预装应用、关闭遥测、禁用 Copilot/Recall/AI 功能、恢复经典右键菜单、调整任务栏、关闭 Bing 搜索等。本文覆盖 9 大类功能、三种运行方式、参数化与可回退机制、适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["Windows", "PowerShell", "系统优化", "开源工具", "Debloat"]
---

# Win11Debloat：单文件 PowerShell 脚本给 Windows 10/11 做彻底、可回退的清理

## 一、项目是什么

Win11Debloat 是一款轻量、单文件、无需安装的 PowerShell 脚本，用来快速清理 Windows 10/11 上的预装应用、关闭遥测、禁用 AI 功能、恢复旧版 UI 元素、调整任务栏/开始菜单/文件资源管理器等。它把原本要手动翻几十个设置页面的工作集中到一个交互菜单里，同时提供完整的命令行参数，方便系统管理员在多台机器上批量执行。

| 维度 | 数据 |
|------|------|
| 仓库 | [Raphire/Win11Debloat](https://github.com/Raphire/Win11Debloat) |
| Stars | 47,743+ ⭐ |
| Forks | 1,929+ |
| 主语言 | PowerShell |
| 许可证 | MIT |
| 支持系统 | Windows 10 / Windows 11 |
| 运行方式 | 交互菜单 / 命令行参数 / Sysprep 模式 |
| 默认分支 | master |
| 最近更新 | 2026-06（持续维护） |

值得先说一个判断：**它不是"流氓优化工具"**——所有改动都基于公开的 Windows 注册表、PowerShell cmdlet、组策略，没有 rootkit 类的"激进操作"；并且几乎所有改动都有官方"还原指南"（[Reverting Changes](https://github.com/Raphire/Win11Debloat/wiki/Reverting-Changes) 文档），被卸载的预装应用多数也能从 Microsoft Store 重新装回。

## 二、为什么需要它

新装 Windows 10/11 后，系统会自带一长串普通用户用不到的预装应用（Candy Crush、Bing 天气、Teams 通知、Copilot、Recall 等），并默认开启不少"在后台收集数据"的服务、显示推广位（Bing 搜索、Search Highlights、设置首页广告等）。手动一项一项关掉这些设置需要：

- 翻遍"设置 → 应用 → 已安装应用"
- 改几十个组策略（gpedit.msc）
- 改几十个注册表项
- 手动卸载 Xbox Game Bar、OneDrive、Teams

Win11Debloat 把这堆工作封装成一个交互式菜单 + 几百个开关参数。系统管理员和企业 IT 部门可以在新机器到手第一天就用同一个脚本把所有用户配置对齐。

## 三、三种运行方式

### 3.1 一行命令快速启动（推荐新手）

以管理员身份打开 PowerShell 或 Terminal，粘贴：

```powershell
& ([scriptblock]::Create((irm "https://debloat.raphi.re/")))
```

这行命令会从 `debloat.raphi.re` 下载脚本并直接执行——不需要先下载任何文件。脚本启动后呈现一个交互菜单（[菜单截图](https://github.com/Raphire/Win11Debloat#win11debloat)），按数字键选择要做的调整即可。

### 3.2 传统方法（手动下载）

1. 从 [Releases](https://github.com/Raphire/Win11Debloat/releases/latest) 下载最新版本的 ZIP
2. 解压到任意目录
3. 双击 `Run.bat`，在 UAC 提示中点"是"以管理员权限运行

适合不能直接拉远程脚本的环境（如完全离线、企业代理严格拦截 irm）。

### 3.3 高级方法（命令行参数 + 脚本文件）

适合写进自动化流程：

```powershell
Set-ExecutionPolicy Unrestricted -Scope Process -Force
cd c:\Win11Debloat
.\Win11Debloat.ps1 -RunDefaults -Silent
```

`-RunDefaults` 会按官方"默认设置预设"（Default Settings Preset）一次性应用大部分常用清理项；`-Silent` 跳过交互菜单直接执行。完整的参数列表在 [Wiki: Command-line Interface](https://github.com/Raphire/Win11Debloat/wiki/Command%E2%80%90line-Interface#parameters)。

## 四、九大类功能详解

以下分类与 README 的"Features"段落一一对应。

### 4.1 应用卸载（App Removal）

移除多种预装应用，对应 Microsoft Store 中的"App Removal"页面。**几乎所有被移除的应用都可以从 Microsoft Store 重新安装**——这是它和"强制删除"型工具的关键区别。常用清理目标：

- Xbox Game Bar / Xbox Identity Provider / Xbox 应用
- Candy Crush 系列、Disney+、Spotify 推广版
- Teams（新版 + 经典版）
- OneDrive（可选）

### 4.2 隐私与推荐内容（Privacy & Suggested Content）

关闭系统对用户的"主动观察"，是 Win11Debloat 最实用的部分之一：

- 关闭遥测（telemetry）、诊断数据、活动历史、应用启动跟踪、定向广告
- 关闭"提示与建议"、跨 Windows 推广
- 关闭 Windows 定位服务、应用的定位权限
- 关闭"查找我的设备"位置跟踪
- 关闭锁屏的 Windows Spotlight、提示与技巧
- 关闭桌面背景中的 Windows Spotlight 选项
- 关闭 Microsoft Edge 中的广告、推荐、MSN 新闻源
- 隐藏 Microsoft 365 在"设置 → 主屏幕"的广告（可选整页隐藏）

### 4.3 AI 功能（AI Features）

2025 年后 Windows 推送 AI 化的主要载体，Win11Debloat 给出了一键关闭路径：

- 禁用并移除 Microsoft Copilot
- 禁用 Windows Recall（截图回忆功能）
- 禁用 Click to Do（AI 文本/图像分析工具）
- 阻止 WSAIFabricSvc（AI 服务）自动启动
- 关闭 Edge 中的 AI 功能
- 关闭 Paint 中的 AI 功能
- 关闭 Notepad 中的 AI 功能

### 4.4 系统（System）

- 禁用文件拖动共享托盘
- **恢复 Windows 10 风格经典右键菜单**（Windows 11 默认隐藏了"复制/粘贴/重命名"等基础项到二级菜单）
- 关闭鼠标加速度（"增强指针精度"）
- 禁用 Sticky Keys 快捷键（防止游戏时误触）
- 关闭 Storage Sense 自动磁盘清理
- 关闭"快速启动"，确保每次关机都是完整关机
- 关闭 BitLocker 自动设备加密
- 关闭 Modern Standby 期间的网络连接以省电

### 4.5 Windows Update

- 延迟更新推送（避免新版本首发 bug 影响）
- 防止登录状态下自动重启
- 关闭"传递优化"（不把你的带宽分享给其他 PC 做更新分发）

### 4.6 外观（Appearance）

- 启用系统与应用的深色模式
- 关闭透明度效果
- 关闭动画与视觉效果

### 4.7 开始菜单与搜索（Start Menu & Search）

- 移除或替换开始菜单上所有固定应用
- 隐藏"推荐"区域
- 隐藏"所有应用"区
- 禁用开始菜单里的 Phone Link 移动设备集成
- 禁用 Windows 搜索里的 Bing 网络搜索 + Copilot 集成
- 禁用 Windows 搜索里的 Microsoft Store 应用建议
- 禁用任务栏搜索框的 Search Highlights（动态品牌内容）
- 禁用本地 Windows 搜索历史

### 4.8 任务栏（Taskbar）

- 任务栏图标左对齐（Windows 11 默认居中）
- 隐藏/替换任务栏的搜索图标/框
- 隐藏任务视图按钮
- 禁用任务栏与锁屏的 Widgets
- 隐藏"聊天(meet now)"图标
- 右键菜单启用"结束任务"选项
- 启用"最近激活点击"行为（点击任务栏应用图标可在多窗口间切换）
- 多显示器下的图标显示策略
- 任务栏按钮合并模式选择

### 4.9 文件资源管理器（File Explorer）

- 修改文件资源管理器默认打开位置
- 显示已知文件类型的扩展名
- 显示隐藏文件、文件夹、驱动器
- 隐藏导航窗格中的"主页"或"图库"区
- 隐藏重复的可移动驱动器条目
- 把常用文件夹（桌面、下载等）加回"此电脑"
- 隐藏导航窗格的 3D 对象、音乐、OneDrive 文件夹
- 隐藏右键菜单的"包含到库中""共享"等条目
- 修改驱动器字母位置或可见性

### 4.10 多任务（Multi-tasking）

- 禁用窗口贴靠
- 禁用贴靠建议
- 禁用拖拽窗口到顶部时的"贴靠布局"建议
- 配置 Alt+Tab 是否显示标签

### 4.11 可选 Windows 功能（Optional Windows Features）

- 启用 Windows Sandbox（轻量沙盒桌面环境，安全运行可疑应用）
- 启用 WSL（Windows Subsystem for Linux，直接跑 Linux 环境）

### 4.12 其他（Other）

- 禁用 Xbox Game Bar 集成与游戏/录屏，关闭 `ms-gamingoverlay`、`ms-gamebar` 弹窗
- 清理 Brave 浏览器中的 bloat（AI、Crypto、News 等）

## 五、面向系统管理员的高级特性

### 5.1 跑给"另一个用户"用

[Advanced Features 文档](https://github.com/Raphire/Win11Debloat/wiki/Advanced-Features#running-as-another-user) 描述了如何对当前未登录的用户应用清理——常见场景是新装机的多账户环境。

### 5.2 Sysprep 模式

[Sysprep 模式](https://github.com/Raphire/Win11Debloat/wiki/Advanced-Features#sysprep-mode) 把清理动作应用到 Windows Default User Profile——之后所有新建用户都会自动继承这套设置。企业 IT 做镜像时最常用。

### 5.3 完整 CLI 参数化

[Command-line Interface Wiki](https://github.com/Raphire/Win11Debloat/wiki/Command%E2%80%90line-Interface#parameters) 列出了所有可单独开关的参数（例如 `-DisableCopilot`、`-DisableRecall`、`-ClassicRightClickMenu`），方便按需选择：

```powershell
.\Win11Debloat.ps1 -RunDefaults -Silent
.\Win11Debloat.ps1 -DisableCopilot -DisableRecall -HideSearchBox
.\Win11Debloat.ps1 -RunDefaults -Silent -Sysprep
```

参数化的好处是：

- **可审计**：执行前能写出明确的 PowerShell 脚本，CI 系统能 diff
- **可版本化**：把整套参数写进 Git，升级到新版本时能 review 哪些默认值变了
- **可分批**：新机器到手先跑一遍"基线"，再按需叠加特定参数

## 六、可回退机制

这是它和"激进清理工具"最大的区别。每个改动都有对应的"还原路径"：

| 改动类型 | 还原方式 |
|----------|----------|
| 预装应用卸载 | 从 Microsoft Store 重新安装 |
| 注册表项改动 | 提供对应 `.reg` 文件恢复，或脚本内的 revert 流程 |
| 组策略改动 | gpedit.msc 或注册表反向写入 |
| Copilot/Recall 关闭 | Windows 功能更新会重新启用，需要重新跑脚本关闭 |
| AI 功能关闭 | 部分 AI 功能在功能更新后会重新开启 |

完整的还原步骤见 [Wiki: Reverting Changes](https://github.com/Raphire/Win11Debloat/wiki/Reverting-Changes)。

## 七、典型使用流程

### 7.1 普通个人用户

1. 用 3.1 的一行命令启动
2. 在交互菜单里勾选要做的项
3. 重启

### 7.2 极客玩家

1. 下载 Release ZIP
2. 编辑 `Win11Debloat.ps1` 调用方式，按 Wiki 配出自己偏好的预设
3. 把整个目录放一份到 OneDrive / NAS
4. 每次新装机跑一次

### 7.3 系统管理员 / 企业 IT

1. 下载 Release ZIP
2. 写一个 `deploy.ps1`，调用 `Win11Debloat.ps1 -RunDefaults -Silent -Sysprep`
3. 集成到镜像制作流程或 SCCM / Intune 任务序列
4. 升级 Win11Debloat 时 review changelog，看默认值是否变了

## 八、适用边界

### 8.1 适合

- **新装 Windows 10/11 后的"第一天清理"**——省 1-2 小时手动配置
- **不想要 Copilot/Recall/AI 推送的隐私敏感用户**
- **怀念 Windows 10 经典 UI 的用户**（经典右键菜单、左对齐任务栏）
- **企业镜像制作、Sysprep 后批量配置**
- **玩 Windows Sandbox / WSL 想要一行开启的开发者**

### 8.2 不适合

- **不想跑 PowerShell 脚本的纯图形界面用户**——尽管有交互菜单，UAC 弹窗 + 脚本执行仍然要求最低限度理解
- **使用了非标准 Windows 版本**（LTSC 裁剪版、某些 OEM 定制版）——某些参数可能没有对应项
- **依赖 Microsoft 365 Copilot 工作的用户**——关掉 Copilot 之后再启用会需要手动跑反向脚本
- **生产服务器**——Win11Debloat 主要面向桌面端 Windows，Server 系列的功能覆盖不完整

### 8.3 已知风险

- 大版本 Windows 11 功能更新（年度大版本）会**重置部分注册表项**——AI 关闭、任务栏居中、Copilot 卸载等都需要重跑脚本
- 部分预装应用和 Windows 组件深度耦合（例如 Cortana、Xbox 身份认证），卸载后某些游戏或应用可能要求重新安装
- 关闭"快速启动"后系统启动会略慢，但换来完整的关机语义

## 九、与其他 Windows 优化工具对比

| 工具 | 形态 | 许可 | 关键差异 |
|------|------|------|----------|
| **Win11Debloat** | 单文件 PS 脚本 | MIT | 可回退、参数化、Sysprep、活跃维护 |
| O&O ShutUp10 | GUI 应用 | 免费 | 图形化好，但不开源、不能脚本化 |
| Debloat Windows 10 (旧项目) | PS 脚本 | MIT | 已停维护，2020 年后无更新 |
| Win10/11 Initial Setup Script | PS 脚本 | MIT | 范围类似，偏 Windows 10 时代 |
| ReviOS / AtlasOS | 定制镜像 | 闭源 | 改系统 ISO 级别，激进但不可回退 |

## 十、参考链接

- 官方仓库：[github.com/Raphire/Win11Debloat](https://github.com/Raphire/Win11Debloat)
- Wiki 首页：[github.com/Raphire/Win11Debloat/wiki](https://github.com/Raphire/Win11Debloat/wiki/)
- 默认设置预设：[Default Settings](https://github.com/Raphire/Win11Debloat/wiki/Default-Settings)
- 命令行参数：[Command-line Interface](https://github.com/Raphire/Win11Debloat/wiki/Command%E2%80%90line-Interface#parameters)
- 还原指南：[Reverting Changes](https://github.com/Raphire/Win11Debloat/wiki/Reverting-Changes)
- 高级功能（Sysprep、其他用户）：[Advanced Features](https://github.com/Raphire/Win11Debloat/wiki/Advanced-Features)
- 讨论区：[GitHub Discussions](https://github.com/Raphire/Win11Debloat/discussions)
- Releases：[Latest Release](https://github.com/Raphire/Win11Debloat/releases/latest)

---

**一句话总结**：Win11Debloat 是 2026 年 Windows 10/11 上最稳的一款"开箱即清"PowerShell 工具——它把 9 大类、近百个开关收敛成 1 个交互菜单 + 1 套参数化命令行，加上完整的可回退机制，是个人用户和系统管理员在 Windows 桌面清理场景下都值得收藏的开源方案。
