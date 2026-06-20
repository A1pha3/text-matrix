---
title: "微软 PowerToys：Windows 上最值得安装的生产力工具套件"
date: "2026-04-30T10:06:53+08:00"
slug: "microsoft-powertoys-windows-productivity-suite-guide"
description: "Microsoft PowerToys 是微软官方推出的 Windows 生产力工具集，提供 30+ 实用工具，覆盖窗口管理、文件批量处理、快捷键定制、屏幕取色与 OCR 等场景。本文详解其核心工具、安装方式及上手指南，帮助 Windows 用户快速判断价值并完成首次配置。"
draft: false
categories: ["技术笔记"]
tags: ["Windows", "PowerToys", "微软", "生产力工具", "开源"]
---

# 微软 PowerToys：Windows 上最值得安装的生产力工具套件

PowerToys 是微软官方维护的一套 Windows 生产力工具合集，截至 2026 年 4 月已更新至 **v0.99.1**，在 GitHub 上拥有超过 **13 万 Star** 和 7900 多个 Fork，是 Windows 平台最受关注的开源项目之一。项目最初于 2019 年开源，采用 MIT 许可证，主力语言为 C#。

## 学习目标

读完本文，可以掌握以下能力：

- 说出 PowerToys 在 Windows 原生功能之外填补的具体场景
- 按启动器、窗口管理、文件处理、开发运维、键鼠增强五类定位所需工具
- 用 winget / Microsoft Store / 安装包三种方式完成安装与更新
- 判断哪些工具值得优先启用、哪些可以按需再开
- 了解 PowerToys 的遥测数据范围与关闭方式

---

## 为什么关注 PowerToys

Windows 本身的功能已经相当完善，但批量重命名文件、快速定位窗口、用快捷键弹出剪贴板历史等高频操作，要么步骤繁琐，要么根本没有内置方案。PowerToys 由 Microsoft 官方团队维护，补的就是这些缺口。

- 项目由 Microsoft 官方团队维护，非社区爱好者作品
- 最新版本 v0.99.1 发布于 2026-04-29，仍在活跃开发中
- 支持 x64 和 ARM64 架构，兼容 Windows 10 和 Windows 11
- 所有工具均为免费软件，不含广告

---

## 核心工具一览

PowerToys 目前包含超过 30 个独立工具，按功能分为五类。下表先给总览，后文逐类展开。

| 类别 | 代表工具 | 解决的问题 |
|------|----------|------------|
| 启动器与快速访问 | PowerToys Run、Command Palette、Advanced Paste | 应用启动、命令执行、剪贴板增强 |
| 窗口管理 | FancyZones、Always on Top、Crop And Lock | 窗口布局、置顶、裁剪 |
| 文件与系统工具 | File Explorer Add-ons、PowerRename、Image Resizer、Peek | 文件预览、批量重命名、图片缩放 |
| 开发与运维工具 | Hosts File Editor、Registry Preview、Environment Variables、Text Extractor、Color Picker | hosts/注册表/环境变量管理、OCR、取色 |
| 键盘与鼠标增强 | Keyboard Manager、Shortcut Guide、Mouse Utilities、Mouse Without Borders | 按键重映射、快捷键提示、跨设备键鼠 |

### 启动器与快速访问

**PowerToys Run** 类似 macOS Spotlight，按下 `Alt + Space` 调出搜索框，可启动应用、搜索文件、执行计算，支持插件扩展。

**Command Palette** 提供了类似 VS Code 命令面板的体验，通过快捷键调出命令列表，执行各种系统操作。

**Advanced Paste** 扩展剪贴板功能，支持粘贴历史、粘贴为纯文本、将剪贴板内容发送到其他设备。

### 窗口管理

**FancyZones** 是窗口布局管理器，可将屏幕划分为多个区域，拖拽窗口到指定区域实现精准排布，多显示器场景尤为实用。

**Always on Top** 将任意窗口固定在最前端，不受其他窗口遮挡，适合对比文档或参考网页时使用。

**Crop And Lock** 对窗口进行裁剪，只显示特定区域，同时保持窗口功能完整。

### 文件与系统工具

**File Explorer Add-ons** 为资源管理器增加预览能力，无需打开文件即可在右侧预览面板查看 PDF、图片、代码文件等。

**PowerRename** 提供批量重命名功能，支持正则表达式匹配和替换，处理大量文件时效率远超资源管理器默认重命名。

**Image Resizer** 在资源管理器右键菜单中增加图片批量缩放选项，选中图片后直接调整尺寸。

**Peek** 是轻量级文件预览工具，按空格键即可预览文件内容，支持代码高亮、PDF、图片等多种格式。

### 开发与运维工具

**Hosts File Editor** 提供图形化 hosts 文件编辑器，方便管理本地域名映射，适合多测试环境间切换。

**Registry Preview** 用于预览 reg 文件内容，修改注册表前可检查变更范围，降低误操作风险。

**Environment Variables** 提供环境变量图形化管理界面，比系统自带的高级系统属性更直观。

**Text Extractor**（即 PowerOCR）提供 OCR 识别功能，可从屏幕任意区域提取文字，处理截图、扫描件或无法复制的网页内容时常用。

**Color Picker** 是屏幕取色器，在任意位置点击即可获取颜色的 HEX、RGB 值并自动复制到剪贴板。

### 键盘与鼠标增强

**Keyboard Manager** 允许重新映射键盘按键，甚至将一组按键组合映射到另一组，适合外接键盘布局不匹配或需要自定义快捷键的场景。

**Shortcut Guide** 按住 Windows 键超过一秒后，显示当前应用程序的所有可用快捷键。

**Mouse Utilities** 中的 Find My Mouse 功能，同时按左右鼠标键可让鼠标指针以波纹动画高亮显示，双屏或高分屏场景下定位指针很方便。

**Mouse Without Borders** 将多台电脑连接成统一工作站，用一套键盘鼠标控制多台设备，支持跨设备剪贴板共享和文件拖拽传输。

### 其他工具

**Awake** 防止电脑进入睡眠状态，替代系统电源计划，长时间运行下载、编译等任务时使用。

**Workspaces** 保存和恢复窗口布局，一键恢复工作状态，适合在开发、开会、写作等场景间快速切换。

**ZoomIt** 是经典的屏幕放大和标注工具，广泛用于屏幕录制和演示。

---

## 安装方式

### 通过 winget 安装（推荐）

```powershell
winget install Microsoft.PowerToys -s winget
```

更新也会自动处理，安装范围（用户级/机器级）会保持一致。

### 直接下载安装包

前往 [GitHub Releases](https://github.com/microsoft/PowerToys/releases) 页面，选择对应架构的安装包：

| 安装范围 | 架构 | 文件名 |
|---------|------|--------|
| 用户级 | x64 | PowerToysUserSetup-0.99.1-x64.exe |
| 用户级 | ARM64 | PowerToysUserSetup-0.99.1-arm64.exe |
| 机器级 | x64 | PowerToysSetup-0.99.1-x64.exe |
| 机器级 | ARM64 | PowerToysSetup-0.99.1-arm64.exe |

### Microsoft Store

也可以在 Microsoft Store 中搜索 PowerToys，一键安装，自动更新。

---

## 采用顺序建议

1. **先装 PowerToys Run**：启动器是最高频入口，装完即可替代开始菜单搜索
2. **再开 FancyZones**：多窗口并排场景下收益直接，27 寸及以上显示器尤为明显
3. **按需启用 Text Extractor**：屏幕取字是高频刚需，替代了以往需要打开网页 OCR 工具的繁琐步骤
4. **逐步试其他工具**：PowerRename、Color Picker、Hosts File Editor 等按遇到的具体场景启用

每个工具在设置中都有独立的开关和配置选项，按需启用即可。最直接的上手路径：用 winget 安装，打开 PowerToys Run 体验几天，再按需开启其他工具。

---

## 隐私说明

PowerToys 会收集基本的诊断遥测数据，用于改进产品。微软提供了详细的 [PowerToys Data and Privacy](https://aka.ms/powertoys-data-and-privacy-documentation) 文档，说明了收集的数据类型和关闭方式。如果对隐私有顾虑，可以查阅官方文档了解详情。

---

## 小结

PowerToys 是 Windows 平台上为数不多由操作系统厂商官方维护的开源生产力工具集合，MIT 许可证开源，同时以可直接安装的二进制形式发布。

> 项目地址：[https://github.com/microsoft/PowerToys](https://github.com/microsoft/PowerToys)
> 官方文档：[https://aka.ms/powertoys-docs](https://aka.ms/powertoys-docs)
> 最新版本：v0.99.1（2026-04-29）
