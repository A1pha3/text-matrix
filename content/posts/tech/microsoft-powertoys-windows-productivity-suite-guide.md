---
title: "微软 PowerToys：Windows 上最值得安装的生产力工具套件"
date: "2026-04-30T10:06:53+08:00"
slug: "microsoft-powertoys-windows-productivity-suite-guide"
github_repo: "microsoft/PowerToys"
source_key: "gh:microsoft/PowerToys"
description: "Microsoft PowerToys 是微软官方推出的 Windows 生产力工具集，提供 30+ 实用工具，覆盖窗口管理、文件批量处理、快捷键定制、屏幕取色与 OCR 等场景。本文详解其核心工具、安装方式及上手指南，帮助 Windows 用户快速判断价值并完成首次配置。"
draft: false
categories: ["技术笔记"]
tags: ["Windows", "微软", "开源"]
---

# 微软 PowerToys：Windows 上最值得安装的生产力工具套件

PowerToys 是微软官方维护的一套 Windows 生产力工具合集。截至 2026 年 9 月，最新稳定版为 **v0.101.2362.0**（2026 年 8 月 25 日发布），在 GitHub 上有约 **13.9 万 Star** 和 8600 多个 Fork，是 Windows 平台最受关注的开源项目之一。项目 2019 年 5 月开源，采用 MIT 许可证，代码以 C/C++ 与 C# 为主。

Windows 补齐不了的细节，它来补：批量重命名、窗口分区、屏幕取字、跨设备键鼠，这些高频操作要么系统没有内置，要么藏得深、步骤多。PowerToys 把它们做成了 30 多个独立小工具，统一在一个设置中心管理。

## 学习目标

读完本文，可以掌握以下能力：

- 说出 PowerToys 在 Windows 原生功能之外填补的具体场景
- 按启动器、窗口管理、文件处理、开发运维、键鼠增强等类别定位所需工具
- 用 winget / Microsoft Store / 安装包三种方式完成安装与更新
- 判断哪些工具值得优先启用、哪些可以按需再开
- 了解 PowerToys 的诊断数据策略：默认关闭，以及在哪里控制

---

## 目录

- [为什么关注 PowerToys](#为什么关注-powertoys)
- [核心工具一览](#核心工具一览)
  - [启动器与快速访问](#启动器与快速访问)
  - [窗口管理](#窗口管理)
  - [文件与系统工具](#文件与系统工具)
  - [开发与运维工具](#开发与运维工具)
  - [键盘与鼠标增强](#键盘与鼠标增强)
  - [显示、主题与演示](#显示主题与演示)
- [系统要求](#系统要求)
- [安装方式](#安装方式)
  - [通过 winget 安装（推荐）](#通过-winget-安装推荐)
  - [直接下载安装包](#直接下载安装包)
  - [Microsoft Store](#microsoft-store)
- [采用顺序建议](#采用顺序建议)
- [隐私说明](#隐私说明)
- [小结](#小结)
- [自测题](#自测题)
- [练习](#练习)
- [进阶路径](#进阶路径)
- [常见问题 FAQ](#常见问题-faq)

---

## 为什么关注 PowerToys

Windows 本身的功能已经相当完善，但高频操作里总有几个缺口：批量重命名要靠第三方软件、窗口分区只能手动对齐、从截图里抄文字得另开 OCR 网站。PowerToys 由 Microsoft 官方团队维护，补的就是这些缺口。

- 项目由 Microsoft 官方团队维护，非社区爱好者作品
- 最新稳定版 v0.101.2362.0 发布于 2026-08-25，仍在活跃开发中
- 支持 x64 和 ARM64 架构，要求 Windows 10 2004（build 19041）或更高版本
- 所有工具免费，不含广告；MIT 许可证开源，同时提供可直接安装的成品

---

## 核心工具一览

PowerToys 目前包含超过 30 个独立工具（官方 README 列出 31 个），按功能分为六类。下表先给总览，后文逐类展开。

| 类别 | 代表工具 | 解决的问题 |
|------|----------|------------|
| 启动器与快速访问 | Command Palette、PowerToys Run、Advanced Paste | 应用启动、命令执行、剪贴板增强 |
| 窗口管理 | FancyZones、Always on Top、Crop And Lock、Workspaces | 窗口布局、置顶、裁剪、工作区恢复 |
| 文件与系统工具 | File Explorer Add-ons、PowerRename、Peek、File Locksmith、New+、Awake | 文件预览、批量重命名、模板新建、防休眠 |
| 开发与运维工具 | Hosts File Editor、Registry Preview、Environment Variables、Text Extractor、Screen Ruler、Command Not Found | hosts/注册表/环境变量管理、OCR、屏幕测量 |
| 键盘与鼠标增强 | Keyboard Manager、Shortcut Guide、Mouse Utilities、Mouse Without Borders、Quick Accent | 按键重映射、快捷键查询、跨设备键鼠、重音字符 |
| 显示、主题与演示 | Light Switch、PowerDisplay、Color Picker、ZoomIt | 深浅色切换、显示器控制、取色、放大标注 |

### 启动器与快速访问

**Command Palette** 是 PowerToys Run 的下一代演进版，按 `Win + Alt + Space` 呼出。启动应用只是基础，它还能：输入 `>` 执行命令、输入 `??` 用默认浏览器搜索、输入 `$` 直达 Windows 设置页；算式直接键入就能算，此外支持搜索文件、从面板里用 WinGet 发现并安装应用、切换窗口、浏览剪贴板历史、启停 Windows 服务。界面可切到紧凑模式，只留一条搜索框。官方路线图正在为它扩展标签页和 JavaScript/TypeScript 插件能力。

**PowerToys Run** 按 `Alt + Space` 呼出，类似 macOS Spotlight：启动应用、搜索文件、执行计算，靠插件扩展。它比 Command Palette 更轻量，习惯老版交互的用户可以继续用它。

**Advanced Paste** 按 `Win + Shift + V` 呼出，把剪贴板内容转成需要的格式再粘贴：纯文本（`Ctrl + Win + Alt + V` 可直接粘贴纯文本，不开窗口）、Markdown、JSON，或导出为 .txt / .html / .png 文件。它内置本地 OCR，能从图片里提取文字，还能把音视频转码成 .mp3 / .mp4。非 AI 功能全部本地运行；AI 转换默认关闭，开启后可接在线模型或 Foundry Local、Ollama、Phi Silica 等本地模型，不强制订阅任何服务。窗口里还能回看并选用最近复制过的条目。

### 窗口管理

**FancyZones** 是窗口布局管理器：把屏幕划成多个区域，拖窗口进去精准落位。默认按住 `Shift` 拖拽才会显示分区（可在设置里改成拖拽即显示）；开启「覆盖 Windows Snap」后，`Win + 方向键` 就能在分区间移动窗口；拖拽时按住 `Ctrl` 可让窗口同时占据多个分区。多显示器可以各配一套布局。

**Always on Top** 按 `Win + Ctrl + T` 把当前窗口钉在最前，再按一次解除。对照文档、盯日志时不用来回切换。

**Crop And Lock** 把窗口的一块区域裁成独立小窗：`Win + Ctrl + Shift + T` 生成实时缩略窗，镜像原窗口变化；`Win + Ctrl + Shift + R` 则把那块区域「挖」成独立窗口。盯仪表盘某一块区域、看直播画面一角时好用。

**Grab And Move** 按住 `Alt` 在窗口任意位置拖动即可移动窗口，右键拖动则从最近的边角缩放——不必再瞄准窄窄的标题栏和边框。

**Window Hopper** 按住 `Alt` 再按反引号 `` ` ``，只在当前焦点应用的多个窗口间循环切换。`Alt + Tab` 是在所有应用间切，它解决的是同一个应用开了很多窗口的场景。

**Workspaces** 把一组应用连同各自的窗口位置、启动参数存成一个工作区（按 ``Win + Ctrl + ` `` 打开编辑器录制当前桌面状态），一键全部拉起，还能钉成桌面快捷方式。开发、开会、写作几套布局切换，省去逐个开应用、摆窗口的动作。

### 文件与系统工具

**File Explorer Add-ons** 给资源管理器的预览面板和缩略图补上多种格式支持：Markdown、SVG、PDF、G-code、源代码文件等，选中即可预览，不必逐个打开。注意它会覆盖系统里已装的同类预览处理器，有与 Outlook 的 PDF 预览不兼容的反馈。

**PowerRename** 批量重命名，支持正则表达式查找替换，改前有实时预览，确认后才写入；改错了用资源管理器的 `Ctrl + Z` 即可撤销。替换文本里可用 `${}` 计数器（支持起始值、步长、补零，如 `${padding=4;increment=2;start=10}`）。

**Image Resizer** 在资源管理器右键菜单里加一项批量缩放，选中若干图片直接按预设尺寸输出。

**Peek** 选中文件按空格键即弹出预览，支持图片、Office 文档、PDF、视频、网页、Markdown、源代码等格式，还能显示文件夹摘要；方向键可在当前文件夹的文件间连续翻看。

**File Locksmith** 右键选中被占用的文件，立刻列出是哪个进程锁着它。删不掉文件、U 盘弹不出的时候，不用再开资源监视器排查。

**New+** 把自己的常用模板（文件或文件夹结构）放进资源管理器「新建」菜单，周报、项目骨架这类重复创建一次配好。

**Awake** 让电脑临时或持续保持唤醒，不改动系统电源计划设置——它用后台线程向 Windows 申请电源状态，关闭后一切照旧。注意锁屏或注销后 Awake 不生效。跑长任务、演示中途息屏前开它。

### 开发与运维工具

**Hosts File Editor** 图形化编辑 hosts 文件，条目可逐行启用停用，切换测试环境不再手改注释。

**Registry Preview** 双击 .reg 文件前先看它要写什么，降低误导入风险。

**Environment Variables** 图形化管理用户与系统环境变量，比「高级系统设置」里的小对话框直观得多。

**Text Extractor** 按 `Win + Shift + T` 框选屏幕任意区域，识别出的文字直接进剪贴板，代码基于 Joe Finney 的 Text Grab。截图、视频画面、不可复制的网页文字都靠它。

**Color Picker** 按 `Win + Shift + C` 取色，颜色值按配置格式复制进剪贴板，附带的编辑器可微调并保留取色历史。

**Screen Ruler** 按 `Win + Ctrl + Shift + M` 呼出，测量屏幕上元素的像素尺寸，自带边缘检测，设计稿比对、UI 还原检查常用。

**Command Not Found** 是个 PowerShell 7 模块：命令敲错了、没装时，它提示该装哪个 WinGet 包。需要 PowerShell 7 和 Microsoft.WinGet.Client 模块；与部分 PowerShell 配置存在已知不兼容，启用前留意官方 issue。

### 键盘与鼠标增强

**Keyboard Manager** 重映射按键和快捷键，可以单键换单键、组合键换组合键，还能把按键或快捷键映射成一段任意文本；可全局生效，也可只对指定应用生效。前提是 PowerToys 常驻后台，退出后重映射失效。

**Shortcut Guide** 按 `Win + Shift + ?` 打开一份可搜索的快捷键手册。它内置 Windows、PowerToys、Microsoft 365、主流浏览器、Teams/Slack/Discord 等应用的快捷键清单，打开时自动定位到当前前台应用；长按任意 Windows 键，任务栏图标会浮出对应的快捷键指示，也可由此进入完整手册（这一行为可在设置里调整或关闭）。

**Mouse Utilities** 是一组鼠标小工具的合集：**Find My Mouse** 双击 `Ctrl`（或摇晃鼠标）让全屏变暗、只给指针位置打聚光；**Mouse Highlighter** 按 `Win + Shift + H` 高亮每次点击，录演示视频时观众看得清；另有 **Mouse Jump**（跨屏跳转指针）、**Crosshairs**（指针十字线）、**CursorWrap**（指针越过屏幕边缘从对侧出来，多屏横移省距离）。

**Mouse Without Borders** 用一套键鼠控制最多四台电脑，剪贴板互通，文件可直接拖到隔壁机器。

**Quick Accent** 输入带重音字符的另一种姿势：按住字符键再按激活键（左右方向键、空格等可选），或直接长按字符键，弹出候选条选目标字符。代码基于 PowerAccent，需要 é、ü、ñ 这类字符又不想切键盘布局时用它。

### 显示、主题与演示

**Light Switch** 按日出日落或自定义时间表自动切换系统深浅色主题。

**PowerDisplay** 通过 DDC/CI 控制外接显示器：亮度、对比度、音量、输入源、旋转、色温、电源状态都收进一个浮层，可存配置组合一键套用，还带命令行接口。个别显示器对 DDC/CI 支持不稳，设置里会提示。

**ZoomIt** 来自微软 Sysinternals 的经典演示工具，屏幕缩放、放大后标注、录屏、截图都能做，快捷键可自定义，常驻托盘。

---

## 系统要求

- Windows 11，或 Windows 10 version 2004（20H1 / build 19041）及以上
- x64 或 ARM64 处理器
- Microsoft Edge WebView2 运行时（安装器会自动装）

---

## 安装方式

### 通过 winget 安装（推荐）

```powershell
winget install Microsoft.PowerToys -s winget
```

默认装用户级（仅当前用户可用）。要装成全机共用，加 `--scope machine`：

```powershell
winget install --scope machine Microsoft.PowerToys -s winget
```

之后用 winget 更新时，会沿用当前安装范围，不会在用户级/机器级之间跳。

### 直接下载安装包

前往 [GitHub Releases](https://github.com/microsoft/PowerToys/releases) 页面展开 Assets，按架构和安装范围选择（对多数设备，x64 用户级即可）：

| 安装范围 | 架构 | 文件名 |
|---------|------|--------|
| 用户级 | x64 | PowerToysUserSetup-0.101.2362.0-x64.exe |
| 用户级 | ARM64 | PowerToysUserSetup-0.101.2362.0-arm64.exe |
| 机器级 | x64 | PowerToysSetup-0.101.2362.0-x64.exe |
| 机器级 | ARM64 | PowerToysSetup-0.101.2362.0-arm64.exe |

用户级装到 `%LocalAppData%\Programs`，机器级装到 `Program Files`；两种方式都能正常收到更新。

### Microsoft Store

在 Microsoft Store 搜索 PowerToys 一键安装，自动更新。

### 其他方式

Chocolatey、Scoop 等社区包管理器也收录了 PowerToys，安装命令见[官方安装文档](https://learn.microsoft.com/windows/powertoys/install)。

---

## 采用顺序建议

1. **先开 Command Palette**：启动器是最高频入口，`Win + Alt + Space` 呼出，启动应用、算算式、查剪贴板历史都在这一个框里。它是 PowerToys Run 的下一代版本，官方新功能也优先落在它上面
2. **再配 FancyZones**：多窗口并排场景收益直接，27 寸及以上显示器尤为明显
3. **按需启用 Text Extractor 与 Crop And Lock**：屏幕取字和窗口裁剪都是小成本高回报的工具
4. **遇到痛点再加**：文件被占用找 File Locksmith，改 hosts 找 Hosts File Editor，演示录屏加 Mouse Highlighter 和 ZoomIt

每个工具在设置里都有独立开关，全部默认不打扰，装完只开自己要用的。

---

## 隐私说明

PowerToys 的诊断数据**默认关闭**，且完全可选——这是 v0.86 之后的行为。作为开源项目，它上报的每一个遥测事件都在代码库的 [DATA_AND_PRIVACY.md](https://github.com/microsoft/PowerToys/blob/main/DATA_AND_PRIVACY.md) 里逐条列出，写明用途；想开启诊断数据，在设置里手动打开即可。

---

## 小结

PowerToys 是 Windows 平台上少有的由操作系统厂商官方维护的开源生产力工具集，MIT 许可证，免费无广告。30 多个工具各自独立，随装随用：启动器管入口，FancyZones 管布局，剩下几十个按需启用。

> 项目地址：[https://github.com/microsoft/PowerToys](https://github.com/microsoft/PowerToys)
> 官方文档：[https://aka.ms/powertoys-docs](https://aka.ms/powertoys-docs)
> 最新稳定版：v0.101.2362.0（2026-08-25）

---

## 自测题

1. PowerToys Run 的默认呼出快捷键是什么？它的下一代演进版叫什么？
2. FancyZones 主要解决什么痛点？多显示器场景下为什么特别好用？
3. Keyboard Manager 能重映射什么？除了键换键，它还能做什么？
4. PowerToys 的诊断数据默认开启还是关闭？在哪里控制？
5. PowerRename 相比资源管理器自带的 F2 重命名，强在哪里？改错了怎么撤？

<details>
<summary>参考答案</summary>

1. `Alt + Space`；下一代版本是 Command Palette（`Win + Alt + Space`）。
2. 把屏幕划分成多个区域、拖窗口精准入位，多显示器可各配布局，省去手动对齐；开启「覆盖 Windows Snap」后 `Win + 方向键` 即可在分区间移动。
3. 单键换单键、组合键换组合键，还能把按键或快捷键映射成一段文本，支持全局或仅指定应用生效；前提是 PowerToys 常驻后台。
4. 默认关闭，v0.86 起如此，且完全可选；在 PowerToys 设置里控制开关，全部遥测事件在仓库 DATA_AND_PRIVACY.md 中公开列出。
5. 支持正则批量匹配替换、`${}` 计数器补零、实时预览后再写入，一次改上百个文件不费力；改完用资源管理器的 `Ctrl + Z` 撤销。

</details>

---

## 练习

1. 用 winget 装好 PowerToys，按 `Win + Alt + Space` 呼出 Command Palette：启动一个应用、键入一道算式、再用 `??` 搜一次网页。
2. 给 27 寸以上的屏幕配一套 FancyZones 三栏布局，把浏览器、终端、文档分别拖进去；再试试 `Ctrl` 多选分区。
3. 用 Keyboard Manager 把 `Caps Lock` 重映射成 `Ctrl`，用一天看是否顺手。
4. 选中一批截图，用 PowerRename 把 Replace with 填成 `screenshot_${padding=3}` 并启用枚举，预览确认后应用；随后按 `Ctrl + Z` 撤销，验证可回退。
5. 用 Text Extractor 从一张截图里提取文字，再用 Color Picker（`Win + Shift + C`）把界面主色复制进剪贴板。

---

## 进阶路径

- **玩 Command Palette 插件**：命令面板支持扩展，官方路线图正在加标签页和 JavaScript/TypeScript 扩展能力，可以把它改造成个人控制台。
- **读模块源码**：每个工具是独立模块，C++ 与 C# 混用（如 FancyZones 是 C++），挑一两个读源码，弄清它们怎么挂进设置中心。
- **改设置 JSON**：部分高级行为可直接编辑 PowerToys 的设置文件，绕过 UI 限制。
- **组合自动化**：把 Keyboard Manager、Mouse Without Borders 和 AutoHotkey 组合，搭一套跨设备工作流。
- **盯路线图**：v0.102 计划用 WinUI 3 现代化多个工具，并继续扩展 Command Palette，新功能集中在那里。

---

## 常见问题 FAQ

**装完在系统托盘找不到 PowerToys 图标？**
先确认进程在跑：任务管理器里搜 `PowerToys`。没跑就重新打开；图标可能被 Windows 折叠进托盘箭头，点开箭头查看。

**`winget install` 卡住或报网络错误？**
winget 默认走微软商店源，公司网络或代理下可能不稳。可改去 GitHub Releases 直接下安装包，或给 winget 配置代理后重试。

**Command Palette 和 PowerToys Run 该用哪个？**
两者都内置。Command Palette 是 Run 的下一代版本，功能更全（WinGet 安装、服务管理、剪贴板历史），官方新特性优先落在它上面；Run 更轻量成熟。按习惯选一个即可，二者快捷键不同，不冲突。

**PowerToys Run 搜不到我刚装的应用？**
先确认应用已出现在开始菜单、Run 的 Program 插件已启用；再重启 PowerToys 让插件重新枚举一遍。

**FancyZones 拖拽窗口不进区域？**
当前版本默认要按住 `Shift` 拖拽才会显示分区；如果不想按，可在 FancyZones 设置里取消「按住 Shift 键激活分区」。多显示器下要确认布局绑定的是当前屏幕。

**遥测能不能彻底关掉？**
默认就是关的。v0.86 起，诊断数据完全可选且默认不上报；每个事件在 DATA_AND_PRIVACY.md 里有清单可查，不需要额外操作。

**ARM64 设备（如 Surface 系列）能用吗？**
能。PowerToys 提供 ARM64 安装包，最低要求 Windows 10 version 2004。
