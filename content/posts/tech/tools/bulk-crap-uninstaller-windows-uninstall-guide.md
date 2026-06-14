---
title: "Bulk Crap Uninstaller：Windows 批量程序卸载完全指南"
slug: "bulk-crap-uninstaller-windows-uninstall-guide"
aliases:
  - /posts/tech/bulk-crap-uninstaller-windows-uninstall-guide/
date: "2026-03-31T14:25:00+08:00"
categories: ["技术笔记"]
tags: ["BCUninstaller", "Windows", "卸载工具", "批量卸载", "系统清理"]
description: "全面解析 Bulk Crap Uninstaller (BCU)：18.1k Stars 的免费开源 Windows 程序卸载器。支持 NSIS、InnoSetup、MSI、Steam、Windows Store Apps 等多种卸载系统，批量卸载、自动清理残留、检测孤儿应用。Apache-2.0 开源许可证。"
---

# Bulk Crap Uninstaller：Windows 批量程序卸载使用指南

## §1 学习目标

完成本文档后，你将能够：

- ✅ 理解 Bulk Crap Uninstaller 的定位与核心功能
- ✅ 掌握 BCU 的系统架构与卸载检测机制
- ✅ 熟练使用 GUI 批量卸载程序
- ✅ 熟练使用命令行（Console）进行自动化卸载
- ✅ 清理程序残留与检测孤儿应用
- ✅ 处理 Windows Store Apps 和 Steam 应用
- ✅ 导入预定义卸载列表进行批量操作
- ✅ 自定义卸载规则和处理逻辑

---

## §2 项目概述

### 2.1 什么是 Bulk Crap Uninstaller？

**Bulk Crap Uninstaller**（简称 **BCUninstaller**，官方仓库：[Klocman/Bulk-Crap-Uninstaller](https://github.com/Klocman/Bulk-Crap-Uninstaller)）是一款免费的（开源自由软件）Windows 程序卸载器。

**官方描述**：

> Bulk Crap Uninstaller (or BCUninstaller) is a free (as in speech) program uninstaller. It excels at removing large amounts of applications with minimal user input. It can clean up leftovers, detect orphaned applications, run uninstallers according to premade lists, and much more! Even though BCU was made with IT pros in mind, it can be used by anyone with a basic understanding of how applications are installed/uninstalled in Windows.

翻译：Bulk Crap Uninstaller（简称 BCUninstaller）是一款免费的（开源自由软件）程序卸载器。它擅长以最少的用户输入批量移除大量应用程序。它可以清理残留、检测孤儿应用、根据预定义列表运行卸载程序，以及更多功能！

### 2.2 核心数据

```
Stars:     18,100 (18.1k)
Forks:     792
贡献者:    41 人
提交数:   1,660 次
发布版本:  70 个
标签数:   71 个
许可证:   Apache-2.0
主要语言: C# 96.7%, Inno Setup 3.1%
最新版本: v6.1 (2026-03-06)
最新提交: 4ecea11 (2026-03-08)
```

### 2.3 主要特性

| 特性 | 说明 |
|------|------|
| **批量卸载** | 一键批量卸载多个程序 |
| **残留清理** | 自动清理卸载后的残留文件和注册表 |
| **孤儿检测** | 检测 orphaned applications（孤儿应用）|
| **预定义列表** | 根据预创建的卸载列表自动运行卸载 |
| **多卸载系统支持** | NSIS、InnoSetup、Msiexec 等 |
| **Windows Store Apps** | 完全支持 Windows 应用商店应用 |
| **Steam 支持** | 支持 Steam 安装的应用 |
| **Windows Features** | 支持 Windows 功能组件 |

### 2.4 系统兼容性

**BCUninstaller v6**

| 要求 | 说明 |
|------|------|
| 最低系统 | Windows 10（可能支持 Windows 7）|
| 运行时 | .NET 8 desktop runtime（便携版不需要）|

**BCUninstaller v5**

| 要求 | 说明 |
|------|------|
| 最低系统 | Windows 7 SP1 + 所有平台更新 |
| 运行时 | .NET 6 desktop runtime（便携版不需要）|

**BCUninstaller v1 - v4**

| 要求 | 说明 |
|------|------|
| 最低系统 | Windows XP（后续版本可能不稳定）|
| 运行时 | .Net Framework 4.5 |

### 2.5 版本类型

| 类型 | 说明 | 文件大小 |
|------|------|----------|
| **Setup** | 安装版，正常安装 BCU，如果系统缺少必需的 .NET 运行时，会自动安装 | 较小 |
| **Portable** | 自包含版本，不需要 .NET 运行时，包含运行时所以文件较大 | 较大 |
| **net** | 独立便携版，需要预装 .NET 运行时 | 较小 |

### 2.6 下载来源

| 来源 | 网址 |
|------|------|
| GitHub Releases | https://github.com/Klocman/Bulk-Crap-Uninstaller/releases |
| dAppCDN | https://dappcdn.com/download/utilities/bulk-crap-uninstaller |
| FossHub | https://www.fosshub.com/Bulk-Crap-Uninstaller.html |
| SourceForge | https://sourceforge.net/projects/bulk-crap-uninstaller/ |

---

## §3 技术架构详细分析

### 3.1 支持的卸载系统

BCUninstaller 支持多种卸载系统，兼容性极广：

| 卸载系统 | 说明 |
|----------|------|
| **NSIS** | Nullsoft Scriptable Install System，常用于开源软件 |
| **InnoSetup** | 另一个流行的安装/卸载系统 |
| **Msiexec** | Windows MSI 安装包标准卸载 |
| **Windows Store Apps** | Windows 应用商店应用 |
| **Steam** | Steam 平台游戏和应用 |
| **Windows Features** | Windows 系统功能组件 |

### 3.2 核心检测机制

**程序检测**

BCU 通过以下方式检测已安装的程序：

- Windows 注册表卸载项
- 常见安装目录
- 卸载程序列表
- Windows Store 应用列表
- Steam 应用列表

**残留检测**

卸载后，BCU 会检测以下残留：

- 文件和文件夹残留
- 注册表项残留
- 临时文件
- 孤立的应用数据

**孤儿应用检测**

Orphaned applications（孤儿应用）是指：

- 安装文件已被删除但卸载记录仍存在
- 卸载不完整导致残留
- 手动删除的程序残留

### 3.3 卸载流程

```
检测已安装程序
    ↓
用户选择要卸载的程序
    ↓
收集卸载信息
    ↓
运行卸载程序（NSIS/InnoSetup/Msiexec等）
    ↓
清理残留文件和注册表
    ↓
验证卸载结果
```

---

## §4 安装与配置

### 4.1 下载地址

从 GitHub Releases 下载最新版本：

```bash
https://github.com/Klocman/Bulk-Crap-Uninstaller/releases
```

或从以下镜像下载：

- FossHub：https://www.fosshub.com/Bulk-Crap-Uninstaller.html
- SourceForge：https://sourceforge.net/projects/bulk-crap-uninstaller/
- dAppCDN：https://dappcdn.com/download/utilities/bulk-crap-uninstaller

### 4.2 版本选择

| 场景 | 推荐版本 |
|------|----------|
| Windows 10/11 用户 | v6（Setup 或 Portable）|
| Windows 7 用户 | v5（需要 .NET 6）|
| Windows XP 用户 | v4（需要 .NET Framework 4.5）|
| IT 专业人员 | v6 Portable |

### 4.3 便携版配置

Portable 版本无需安装，下载后直接运行。建议创建以下目录结构：

```
BCU-Portable/
├── Bulk-Crap-Uninstaller-Portable.exe
├── settings/           # 配置目录
├── uninstall_lists/     # 卸载列表目录
└── logs/               # 日志目录
```

### 4.4 系统要求

**v6 版本**

- OS: Windows 10 及以上（可能支持 Windows 7）
- 运行时: .NET 8 desktop runtime（Setup 版自动安装）
- 架构: x64（v6 不再包含 x86 版本）

**v5 版本**

- OS: Windows 7 SP1 及以上
- 运行时: .NET 6 desktop runtime（Portable 版已内置）
- 如遇 DLL 错误，运行 Windows Update

---

## §5 使用说明

### 5.1 主界面概览

BCU 主界面分为以下几个区域：

```
┌─────────────────────────────────────────────────────────┐
│ [工具栏] 卸载 | 更新 | 设置 | 控制台 |
├─────────────────────────────────────────────────────────┤
│ [搜索框] 🔍 输入程序名称搜索...                    │
├─────────────────────────────────────────────────────────┤
│ [程序列表]                                          │
│  ☐ 程序A - 版本1.0 - 2024-01-01                   │
│  ☐ 程序B - 版本2.5 - 2024-02-15                   │
│  ☐ 程序C - 版本1.2 - 2024-03-20                   │
├─────────────────────────────────────────────────────────┤
│ [详情面板]                                            │
│  安装日期: 2024-01-01                              │
│  安装大小: 1.5 GB                                   │
│  卸载方式: NSIS                                      │
│  残留: 找到 3 项                                     │
└─────────────────────────────────────────────────────────┘
```

### 5.2 批量卸载程序

**步骤 1：选择程序**

1. 启动 BCU
2. 在程序列表中，勾选要卸载的程序（可多选）
3. 可使用搜索框快速筛选

**步骤 2：配置卸载选项**

右键点击选中程序，或点击"选项"按钮：

| 选项 | 说明 |
|------|------|
| 静默卸载 | 不显示卸载程序界面 |
| 强制卸载 | 即使卸载失败也继续 |
| 清理残留 | 卸载后自动清理残留 |
| 跳过验证 | 跳过卸载结果验证 |

**步骤 3：执行卸载**

点击"卸载选中"按钮，BCU 将自动：

1. 收集卸载信息
2. 运行适当的卸载程序
3. 清理残留（如果启用）
4. 显示卸载结果

### 5.3 清理残留文件

**手动清理**

1. 在程序列表中，选择要清理的程序
2. 点击"清理残留"按钮
3. BCU 将扫描并显示发现的残留
4. 选择要删除的项
5. 点击"删除选中"确认清理

**自动清理设置**

在"设置"中启用自动清理：

```
设置 → 卸载设置 → 卸载后自动清理残留
```

### 5.4 检测孤儿应用

1. 点击"检测孤儿应用"
2. BCU 将扫描系统
3. 显示发现的孤儿应用列表
4. 可选择删除或忽略

**孤儿应用特征**：

- 无安装文件但有卸载记录
- 卸载不完整
- 手动删除的程序

### 5.5 使用卸载列表

BCU 支持根据预定义列表批量执行卸载。

**创建卸载列表**

1. 在程序列表中选择要卸载的程序
2. 点击"导出列表"
3. 保存为 `.txt` 或 `.json` 文件

**导入卸载列表**

1. 点击"导入列表"
2. 选择列表文件
3. BCU 将自动选择列表中的程序
4. 确认后执行卸载

**卸载列表格式**

```json
{
  "programs": [
    {
      "name": "Program A",
      "version": "1.0",
      "uninstaller": "C:\\Program Files\\ProgramA\\uninstall.exe",
      "silent": true
    },
    {
      "name": "Program B",
      "uninstaller": "C:\\Program Files\\ProgramB\\uninstall.exe",
      "args": "/S"
    }
  ]
}
```

---

## §6 命令行（Console）使用

### 6.1 BCU-Console 简介

BCU 提供命令行版本 `BCU-Console.exe`，适合 IT 专业人员自动化脚本使用。

### 6.2 基本命令

**批量卸载**

```bash
BCU-Console.exe --uninstall "Program1" "Program2" "Program3"
```

**带参数的静默卸载**

```bash
BCU-Console.exe --uninstall "Program Name" --silent --args "/S"
```

**清理残留**

```bash
BCU-Console.exe --clean "Program Name"
```

**导出程序列表**

```bash
BCU-Console.exe --export-list --output installed_programs.txt
```

**使用卸载列表**

```bash
BCU-Console.exe --import-list uninstall_list.json
```

### 6.3 常用命令行参数

| 参数 | 说明 |
|------|------|
| `--uninstall` | 指定要卸载的程序名 |
| `--silent` | 静默模式，不显示界面 |
| `--args` | 传递给卸载程序的参数 |
| `--no-clean` | 不清理残留 |
| `--force` | 强制卸载，即使失败 |
| `--export-list` | 导出程序列表 |
| `--import-list` | 导入卸载列表 |
| `--detect-orphans` | 检测孤儿应用 |
| `--help` | 显示帮助信息 |

### 6.4 自动化脚本示例

**PowerShell 批量卸载脚本**

```powershell
# 批量卸载脚本
$programs = @(
    "Program A",
    "Program B",
    "Program C"
)

foreach ($program in $programs) {
    Write-Host "正在卸载: $program"
    .\BCU-Console.exe --uninstall $program --silent --no-clean
}

Write-Host "批量卸载完成"
```

**批处理文件**

```batch
@echo off
echo 正在卸载预定义程序...
BCU-Console.exe --import-list uninstall_list.json --silent
echo 卸载完成
pause
```

---

## §7 高级功能

### 7.1 自定义卸载规则

BCU 允许用户自定义卸载处理规则。

**创建自定义规则**

1. 打开 BCU 设置
2. 导航到"卸载规则"
3. 点击"添加规则"
4. 配置规则条件：

```json
{
  "conditions": {
    "name_contains": "Program Name",
    "installer_type": "NSIS"
  },
  "actions": {
    "silent": true,
    "args": "/S",
    "clean_after": true
  }
}
```

### 7.2 Windows Store Apps 管理

BCU 完全支持 Windows Store Apps。

**列出所有 Windows Store Apps**

```bash
BCU-Console.exe --list-windows-store-apps
```

**卸载 Windows Store App**

```bash
BCU-Console.exe --uninstall "App Name" --platform windows-store
```

### 7.3 Steam 应用管理

**列出所有 Steam 应用**

```bash
BCU-Console.exe --list-steam-apps
```

**卸载 Steam 应用**

```bash
BCU-Console.exe --uninstall "Game Name" --platform steam
```

### 7.4 Windows Features 管理

**列出所有 Windows Features**

```bash
BCU-Console.exe --list-windows-features
```

**禁用/启用 Windows Feature**

```bash
BCU-Console.exe --set-feature "Hyper-V" --disable
```

---

## §8 卸载系统详细分析

### 8.1 NSIS 卸载

NSIS（Nullsoft Scriptable Install System）是最流行的开源安装系统之一。

**NSIS 卸载特征**：

- 通常使用 `uninstall.exe` 或 `uninstall-nsis.exe`
- 支持 `/S` 参数进行静默卸载
- 常见于：小红伞、CCleaner、WinRAR 等

**BCU 处理方式**：

1. 检测 NSIS 卸载程序
2. 自动添加 `/S` 参数
3. 等待卸载完成
4. 清理残留

### 8.2 InnoSetup 卸载

InnoSetup 是另一个流行的安装系统。

**InnoSetup 卸载特征**：

- 通常为 `unins000.exe`
- 支持 `/VERYSILENT` 或 `/SILENT` 参数
- 支持 `/NORESTART` 参数

**BCU 处理方式**：

1. 检测 InnoSetup 卸载程序
2. 自动选择适当的静默参数
3. 处理卸载进度

### 8.3 MSI 卸载

Windows Installer (MSI) 是 Windows 标准安装系统。

**MSI 卸载特征**：

- 使用 `msiexec.exe`
- 需要产品 GUID 或 MSI 文件

**BCU 处理方式**：

1. 从注册表读取 MSI 产品代码
2. 使用 `msiexec /x{GUID}` 卸载
3. 自动处理依赖关系

### 8.4 残留清理机制

BCU 的残留清理包括：

| 类型 | 清理内容 |
|------|----------|
| **注册表** | HKLM\Software、HKCU\Software、HKLM\Uninstall 等 |
| **文件系统** | Program Files、AppData、ProgramData 等 |
| **临时文件** | Windows Temp、用户 Temp |
| **快捷方式** | 开始菜单、桌面、快速启动 |

---

## §9 推荐做法

### 9.1 IT 专业人员使用场景

**企业批量部署**

在企业环境中，使用 BCU 进行标准化卸载：

1. 创建标准化卸载列表
2. 通过 GPO/脚本批量执行
3. 定期检测孤儿应用

```powershell
# 企业批量卸载脚本
$ UninstallList = Get-Content "\\server\share\uninstall_list.txt"
foreach ($app in $UninstallList) {
    .\BCU-Console.exe --uninstall $app --silent --no-clean
}
```

**系统重装前清理**

重装系统前，使用 BCU 彻底清理：

1. 导出当前程序列表
2. 选择性卸载不需要的程序
3. 清理所有残留
4. 确保系统干净

### 9.2 普通用户使用场景

**磁盘空间清理**

当磁盘空间不足时：

1. 启动 BCU
2. 按"安装大小"排序
3. 选择不常用的大程序卸载
4. 勾选"清理残留"

**卸载不掉的程序**

遇到卸载不了的程序时：

1. 尝试使用 BCU 强制卸载
2. 使用"清理残留"功能
3. 检测孤儿应用

### 9.3 安全注意事项

**谨慎操作**

- 卸载前确认程序名称
- 不要随意卸载系统组件
- 备份重要数据

**建议**

- 创建系统还原点后再进行批量卸载
- 重要程序先导出设置
- 保留卸载日志

---

## §10 常见问题

### Q1：BCU 支持 Windows 11 吗？

支持。BCU v6 完全支持 Windows 10 和 Windows 11。

### Q2：Portable 版本和 Setup 版本有什么区别？

- **Setup 版本**：需要安装，会创建开始菜单快捷方式，自动安装 .NET 运行时（如需要）
- **Portable 版本**：无需安装，自包含 .NET 运行时，可放在 U 盘运行

### Q3：卸载失败怎么办？

1. 尝试勾选"强制卸载"选项
2. 尝试勾选"跳过验证"选项
3. 手动运行程序的卸载程序
4. 使用"清理残留"功能清理

### Q4：如何卸载 Windows Store Apps？

BCU 支持 Windows Store Apps。在主界面中，Windows Store Apps 会显示在单独的区域，可以像普通程序一样卸载。

### Q5：BCU 会删除用户数据吗？

默认情况下，BCU 只删除：

- 程序安装的文件
- 程序创建的残留数据
- 注册表中的卸载记录

用户个人文件（如文档、图片）不会被删除。如需删除用户数据，可使用"清理残留"功能中的"包含用户数据"选项。

### Q6：如何创建卸载列表？

1. 在 BCU 中选择要卸载的程序
2. 点击"导出列表"
3. 选择保存位置和格式（.txt 或 .json）

### Q7：BCU 支持多语言吗？

支持。BCU 内置多语言支持，包括英语、中文等。

### Q8：如何获取 nightly build？

访问 GitHub Actions 页面下载最新的 nightly build：

```
https://github.com/Klocman/Bulk-Crap-Uninstaller/actions/workflows/ci.yaml
```

---

## §11 总结

### 11.1 主要优势

| 优势 | 说明 |
|------|------|
| **免费开源** | Apache-2.0 许可证 |
| **批量卸载** | 一键批量卸载多个程序 |
| **残留清理** | 自动清理卸载后的残留 |
| **孤儿检测** | 检测和清理孤儿应用 |
| **多系统支持** | NSIS、InnoSetup、MSI、Steam、Windows Store |
| **命令行支持** | 适合 IT 专业人员自动化 |
| **便携版** | 无需安装，U 盘运行 |

### 11.2 适用场景

| 场景 | 推荐功能 |
|------|----------|
| 企业批量部署 | 命令行 + 卸载列表 |
| 系统清理 | 批量卸载 + 残留清理 |
| 磁盘空间管理 | 按大小排序卸载大程序 |
| 软件测试 | 快速批量卸载测试环境 |

### 11.3 相关资源

| 资源 | 链接 |
|------|------|
| 官方网站 | https://www.bcuninstaller.com/ |
| GitHub 仓库 | https://github.com/Klocman/Bulk-Crap-Uninstaller |
| 在线文档 | https://htmlpreview.github.io/?https://github.com/Klocman/Bulk-Crap-Uninstaller/blob/master/doc/BCU_manual.html |
| GitHub Releases | https://github.com/Klocman/Bulk-Crap-Uninstaller/releases |
| FossHub 下载 | https://www.fosshub.com/Bulk-Crap-Uninstaller.html |

### 11.4 项目状态

⚠️ **寻找新的维护者** ⚠️

项目当前正在寻找新的维护者来接管开发工作。如果您有兴趣，请访问项目的 Discussion 页面：

```
https://github.com/Klocman/Bulk-Crap-Uninstaller/discussions/289
```

---

*文档版本 1.0 | 撰写日期：2026-03-31 | 基于 v6.1 (2026-03-06) | Stars: 18.1k ⭐*