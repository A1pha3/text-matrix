---
title: "GTweak：一站式 Windows 系统优化工具"
date: "2026-05-14T11:43:00+08:00"
slug: "gtweak-windows-optimizer"
description: "GTweak 是由 Greedeks 开发的一款开源 Windows 系统优化工具，聚合了 HWID/KMS 激活、系统去臃肿、隐私关闭、服务管理等功能，支持 13 种语言，适合需要快速部署理想 Windows 环境的用户。"
draft: false
categories: ["技术笔记"]
tags: ["Windows", "系统优化", "去臃肿", "激活工具", "开源"]
---

## 项目概览

**GTweak**（[Greedeks/GTweak](https://github.com/Greedeks/GTweak)）是一个专注于 Windows 10/11 系统调校的开源工具，目前 GitHub 星标数已超过 960，Fork 80 次。该项目采用 C# 开发，基于 .NET Framework 4.8 构建，遵循 BSD 3-Clause 开源协议。最近一次发布为 2026 年 4 月底的 5.4.9 版本，距今不到一个月，保持着较高的维护频率。

从功能定位上看，GTweak 属于典型的 Windows Tweak（系统调校）工具，与知名的 MSMG Toolbelt、Sophia Script 等属于同一赛道，但覆盖面更广——它将激活、系统精简、隐私控制、服务管理、界面定制等功能全部整合到了一个可执行文件中，用户无需复杂操作即可完成「理想 Windows 环境」的快速部署。

---

## 核心能力解析

根据 README 文档，GTweak 的功能覆盖以下几个维度：

### 激活

支持通过 **HWID**（硬件 ID 永久激活）和 **KMS**（本地密钥管理服务）两种方式激活 Windows，无需依赖第三方激活工具。

### 系统安全与隐私

- 关闭 Windows Defender、SmartScreen、Antimalware Service Executable（MsMpEng）
- 禁用 VBS（Virtualization-Based Security）和 UAC
- 关闭键鼠记录器与遥测数据收集（覆盖 Windows、NVIDIA、Intel）
- 通过 hosts 和防火墙规则屏蔽 Microsoft 收集数据的影子域名
- 禁用 Task Scheduler 中与数据收集相关的计划任务

### 更新与组件管理

- 禁用或暂停 Windows 更新
- 清除已下载的临时更新文件
- 卸载 OneDrive、Microsoft Edge 并清理 WebView2 残留
- 移除 Windows 10/11 中预装的 UWP 应用（Xbox、Candy Crush、Mail 等）

### AI 功能清理

- 关闭 Cortana（小娜）
- 禁用 Copilot（Windows 侧边栏 AI 助手）
- 禁用 Recall（Windows 11 截图与回忆功能）

### 网络协议优化

- 禁用 Teredo、ISATAP、IPv6 等在中国大陆较少使用的隧道协议

### 系统服务管理

- 禁用不必要和不常用的系统服务，减少后台资源占用

### 界面与交互定制

- 更换主题、窗口设置、任务栏布局、图标
- 配置键盘鼠标：关闭按键过滤、粘滞键、指针加速等辅助功能
- 调整电源计划为「终极性能」模式

### 硬件监控与维护

- 查看硬件配置
- 监控系统组件状态
- 使用 NTFS 压缩目录以节省磁盘空间
- 清理 RAM、临时文件、图标缓存
- 安全删除 Windows.old 升级残留目录

### 脚本执行

- 以 TrustedInstaller 权限执行自定义 .ps1、.cmd、.bat、.reg 脚本

---

## 系统要求与安装

GTweak 的系统要求非常明确：

- **Windows 10** 起（build 18362，即 1903 及以后版本）
- **Windows 11** 完整支持
- 必须安装 **.NET Framework 4.8**

项目主页提供了直接下载入口，用户可以下载 `GTweak.exe` 单文件运行，无需安装。压缩包形式（`GTweak.zip`）也一并提供。项目使用 Costura.Fody 将依赖打包为单文件发布，体积约 6MB 左右。

> ⚠️ 使用前需关闭杀毒软件或主动将 GTweak 添加到 Windows Defender 排除列表。工具专门针对官方 Windows 镜像设计，若使用的是经过裁剪或修改的系统版本，使用风险由用户自行承担。

---

## 技术架构

从仓库结构来看，GTweak 采用典型 WPF（Windows Presentation Foundation）桌面应用架构：

- 主要源码位于 `.Source/GTweak/` 目录
- 使用 `WPF-UI` NuGet 包实现现代 Fluent Design 界面风格
- 语言文件通过 `Localize.xaml` 实现多语言国际化，已支持 14 种语言（含简体中文、繁体中文）
- 使用 `TaskScheduler` NuGet 包管理 Windows 计划任务
- 使用 `Newtonsoft.Json` 处理配置与数据序列化
- 使用 `Ookii.Dialogs.Wpf` 提供原生对话框支持

代码的国际化设计较为完善：每种语言对应一个独立文件夹（如 `en/`、`zh-cn/`），包含 `Localize.xaml` 文件。贡献翻译只需 Fork 仓库、复制英文基准文件、翻译后提交 PR，流程在 README 中有详细说明。

---

## 适用场景与注意事项

**适合使用 GTweak 的场景：**

- 新装机后快速关闭 Windows 默认的隐私收集项
- 在不想安装第三方激活工具的情况下完成 Windows 激活
- 清理预装的无用 UWP 应用释放磁盘和内存
- 远程桌面场景下优化网络协议配置
- 需要以 TrustedInstaller 权限执行注册表或 PowerShell 脚本

**需要谨慎评估的场景：**

- 使用了精简版或修改版 Windows 镜像（可能存在功能异常）
- 需要保留 Defender、SmartScreen 或其他安全功能的用户
- 企业环境（部分优化项可能影响域策略或合规性）
- 需要保留 Cortana、Copilot 等 AI 功能的用户（这些功能已被默认禁用）

---

## 总结

GTweak 是一个功能覆盖面极广的 Windows 系统优化工具，将过去需要多个独立脚本协同才能完成的系统调校工作统一到了一个图形界面中。它在隐私保护、系统精简和激活这三个方向上做得尤为彻底，适合有一定动手能力、追求「干净 Windows」体验的用户使用。开源属性加上活跃的多语言社区贡献，使其在同类型工具中具备较高的可信度——任何人都可以审查源码并验证其安全性。

项目当前维护状态良好，最近一次 release 距今不足一个月，适合作为日常装机辅助工具使用。

> 项目地址：[https://github.com/Greedeks/GTweak](https://github.com/Greedeks/GTweak)
> 最新版本：5.4.9