---
title: "Mole：一条命令深度清理Mac，45k Stars的macOS全能维护工具"
date: "2026-04-07T17:20:00+08:00"
slug: mole-mac-clean-optimize-tool
description: "深度解析Mole：macOS全能维护工具，合并CleanMyMac/AppCleaner/DaisyDisk/iStat于一个二进制，45k Stars，支持深度清理、智能卸载、磁盘分析、实时监控。"
categories: ["技术笔记"]
tags: ["macOS", "系统维护", "清理工具", "Shell", "Go"]
draft: false
---

# Mole：macOS全能维护工具

## 项目概述

**Mole**是由[twa](https://github.com/tw93)（也是Pake和Kaku的作者）开发的macOS全能维护工具，核心定位是**Deep clean and optimize your Mac**。它将CleanMyMac、AppCleaner、DaisyDisk和iStat Menus等多个知名工具的功能整合到一个二进制文件中，提供命令行界面的深度清理和系统优化体验。

| 指标 | 数值 |
|------|------|
| **GitHub Stars** | 45.6k |
| **Forks** | 1.4k |
| **最新版本** | V1.33.0 Lynx (2026-04-02) |
| **编程语言** | Shell 81.3%, Go 18.6% |
| **许可证** | MIT |
| **代码提交** | 2,012次 |
| ** Contributors** | 77+ |

**官方定位**：🐹 Deep clean and optimize your Mac.

---

## 核心特性

### 🧹 All-in-one工具箱

Mole将多个知名macOS维护工具整合于一身：

| 工具 | 功能 | Mole对应命令 |
|------|------|--------------|
| **CleanMyMac** | 系统清理 | `mo clean` |
| **AppCleaner** | 应用卸载 | `mo uninstall` |
| **DaisyDisk** | 磁盘分析 | `mo analyze` |
| **iStat Menus** | 系统监控 | `mo status` |

### 🔍 Deep Cleaning 深度清理

清理缓存、日志、浏览器残留和孤立数据，释放存储空间：

```bash
$ mo clean

扫描缓存目录...
✓ 用户应用缓存      45.2GB
✓ 浏览器缓存        10.5GB
  (Chrome, Safari, Firefox)
✓ 开发者工具        23.3GB
  (Xcode, Node.js, npm)
✓ 系统日志和临时文件  3.8GB
✓ 应用特定缓存        8.4GB
  (Spotify, Dropbox, Slack)
✓ 废纸篓            12.3GB
=============================================================
释放空间: 95.5GB | 当前可用: 223.5GB
=============================================================
```

### 🚀 Smart Uninstaller 智能卸载

卸载应用同时清除所有相关文件：

```bash
$ mo uninstall

选择要卸载的应用:
╔══════════════════════════════════════════════════╗
║  ☑ Photoshop 2024 (4.2GB) | Old          ║
║  ☐ IntelliJ IDEA (2.8GB)  | Recent       ║
║  ☐ Premiere Pro (3.4GB)   | Recent       ║
╚══════════════════════════════════════════════════╝

正在卸载: Photoshop 2024
✓ 已移除应用程序
✓ 清理了12个位置的52个相关文件
  - Application Support
  - Caches
  - Preferences
  - Logs
  - WebKit storage
  - Cookies
  - Extensions
  - Plugins
  - Launch daemons
=============================================================
释放空间: 12.8GB
=============================================================
```

### 💾 Disk Insights 磁盘洞察

可视化磁盘使用情况，快速找到大文件：

```bash
$ mo analyze ~/Documents

分析磁盘 ~/Documents | 总计: 156.8GB
▶ 1. ███████████████████ 48.2% | 📁 Library    75.4GB
2. ██████████░░░░░░░░░ 22.1% | 📁 Downloads  34.6GB
3. ████░░░░░░░░░░░░░░░ 14.3% | 📁 Movies     22.4GB
4. ███░░░░░░░░░░░░░░░░ 10.8% | 📁 Documents  16.9GB
5. ██░░░░░░░░░░░░░░░░░  5.2% | 📄 backup    8.2GB
=============================================================
↑↓←→ 导航 | O 打开 | F 显示详情 | ⌫ 删除 | L 大文件 | Q 退出
```

### 📊 Live Monitoring 实时监控

实时仪表盘显示系统健康状态：

```bash
$ mo status

Mole Status
═══════════════════════════════════════════════════════
Health ● 92                              MacBook Pro · M4 Pro · 32GB · macOS 14.5
═══════════════════════════════════════════════════════
⚙ CPU     ▦ Memory
 45.2% Used      ████████████░░░░░░░ 58.4% Load
 0.82/1.05/1.23 (8 cores)              9.8GB Avail
▤ Disk
 67.2% Used  156.3GB Free   ⚡ Power
  Level ██████████████████ 100%  Status Charged
⇅ Network
  ↑ 0.54 MB/s   ↓ 0.02 MB/s
─────────────────────────────────────────────
Processes
  Chrome  ████████░░ 42.1%
  Terminal ██░░░░░░░ 12.5%
─────────────────────────────────────────────
Health Score: 92 (基于CPU/内存/磁盘/温度/I/O负载)
```

---

## 快速上手

### 安装

**方式一：Homebrew（推荐）**

```bash
brew install mole
```

**方式二：安装脚本**

```bash
# 最新稳定版
curl -fsSL https://raw.githubusercontent.com/tw93/mole/main/install.sh | bash

# 指定版本（如 1.17.0）
curl -fsSL https://raw.githubusercontent.com/tw93/mole/main/install.sh | bash -s 1.17.0

# 主支最新代码
curl -fsSL https://raw.githubusercontent.com/tw93/mole/main/install.sh | bash -s latest
```

### 基础命令

| 命令 | 功能 |
|------|------|
| `mo` | 交互式菜单 |
| `mo clean` | 深度清理 + 已卸载应用残留 |
| `mo uninstall` | 卸载已安装应用 |
| `mo optimize` | 刷新缓存和服务 |
| `mo analyze` | 磁盘可视化分析 |
| `mo status` | 实时系统健康仪表盘 |
| `mo purge` | 清理项目构建产物 |
| `mo installer` | 清理安装包文件 |
| `mo touchid` | 配置Touch ID sudo |
| `mo completion` | 设置Shell补全 |
| `mo update` | 更新Mole |
| `mo remove` | 从系统移除Mole |

---

## 进阶用法

### 安全预览模式

所有危险操作都支持`--dry-run`预览：

```bash
# 预览清理（不实际删除）
mo clean --dry-run

# 预览卸载（不实际删除）
mo uninstall --dry-run

# 预览项目清理（不实际删除）
mo purge --dry-run

# 详细日志预览
mo clean --dry-run --debug
```

### 白名单管理

保护重要文件不被清理：

```bash
# 管理优化白名单
mo optimize --whitelist

# 管理清理白名单
mo clean --whitelist
```

### 项目构建产物清理

清理`node_modules`、`target`、`build`、`dist`等：

```bash
$ mo purge

选择要清理的类别 - 18.5GB (8个已选)
➤ ● my-react-app   3.2GB | node_modules
  ● old-project     2.8GB | node_modules
  ● rust-app        4.1GB | target
  ● next-blog       1.9GB | node_modules
  ○ current-work    856MB | node_modules | Recent
  ● django-api      2.3GB | venv
  ● vue-dashboard   1.7GB | node_modules
  ● backend-service 2.5GB | node_modules

注意: 7天内新建的项目会被标记且默认不选中
```

### 安装包清理

查找并清理DMG/PKG等安装文件：

```bash
$ mo installer

选择要移除的安装包 - 3.8GB (5个已选)
➤ ● Photoshop_2024.dmg    1.2GB | Downloads
  ● IntelliJ_IDEA.dmg      850MB | Downloads
  ● Illustrator_Setup.pkg   920MB | Downloads
  ● PyCharm_Pro.dmg        640MB | Homebrew
  ● Acrobat_Reader.dmg      220MB | Downloads
```

### JSON机器可读输出

支持`--json`标志便于脚本和自动化：

```bash
# 磁盘分析JSON输出
mo analyze --json ~/Documents

# 系统状态JSON输出
mo status --json

# 管道时自动切换JSON
mo status | jq '.health_score'
```

### Touch ID Sudo配置

```bash
# 启用Touch ID sudo
mo touchid enable

# 禁用
mo touchid disable
```

---

## 与同类工具对比

| 工具 | 类型 | 体积 | 价格 | 特色 |
|------|------|------|------|------|
| **Mole** | CLI | ~5MB | 免费开源 | 命令行，深度清理 |
| **CleanMyMac** | GUI | ~50MB | 付费 | 完整系统维护 |
| **AppCleaner** | GUI | ~15MB | 免费 | 应用卸载 |
| **DaisyDisk** | GUI | ~10MB | 付费 | 磁盘可视化 |
| **iStat Menus** | 菜单栏 | ~20MB | 付费 | 实时监控 |
| **lsd** | CLI | ~3MB | 免费 | 磁盘使用 |

### Mole的优势

1. **命令行优先**：适合开发者，融入终端工作流
2. **单一二进制**：无需安装多个应用
3. **免费开源**：MIT许可证，完全免费
4. **高度可脚本化**：支持JSON输出，易于自动化
5. **安全优先**：默认保守，需确认才删除

---

## 技术架构

### 目录结构

```
Mole/
├── bin/                  # 可执行文件
│   └── mole             # 主程序
├── cmd/                  # Go命令源码
│   ├── clean/           # 清理命令
│   ├── uninstall/        # 卸载命令
│   ├── analyze/         # 分析命令
│   ├── status/          # 状态命令
│   └── ...
├── lib/                  # 核心库
│   ├── scanner/          # 文件扫描
│   ├── cleaner/          # 清理逻辑
│   └── utils/            # 工具函数
├── scripts/              # 辅助脚本
├── tests/                # 测试
└── install.sh           # 安装脚本
```

### 技术栈

- **Shell 81.3%**：安装脚本、清理逻辑
- **Go 18.6%**：核心程序、命令实现
- **Makefile**：构建自动化

---

## 安全设计

Mole采用**安全优先**的设计原则：

### 安全机制

| 机制 | 说明 |
|------|------|
| **路径验证** | 所有路径经过严格验证 |
| **受保护目录规则** | 系统关键目录默认保护 |
| **保守清理边界** | 默认只清理确认安全的项目 |
| **明确确认** | 高风险操作需要明确确认 |

### 安全原则

> When risk or uncertainty is high, Mole skips, refuses, or requires stronger confirmation rather than broadening deletion scope.

### 日志记录

```bash
# 文件操作记录到
~/Library/Logs/mole/operations.log

# 禁用日志
MO_NO_OPLOG=1 mo clean
```

### 推荐工作流

```bash
# 1. 先预览
mo clean --dry-run

# 2. 查看详细日志
mo clean --dry-run --debug

# 3. 确认无误后执行
mo clean
```

---

## 使用场景

### 适用场景

| 场景 | 推荐命令 |
|------|----------|
| **磁盘空间不足** | `mo clean` + `mo purge` |
| **卸载应用要干净** | `mo uninstall` |
| **清理安装包** | `mo installer` |
| **查看磁盘分布** | `mo analyze` |
| **监控系统状态** | `mo status` |
| **优化系统性能** | `mo optimize` |
| **清理项目缓存** | `mo purge` |

### 典型工作流

```bash
# 1. 先检查系统状态
mo status

# 2. 分析磁盘使用
mo analyze

# 3. 深度清理
mo clean

# 4. 清理项目缓存
mo purge

# 5. 优化系统
mo optimize
```

---

## FAQ常见问题

### Q: Mole安全吗？

**A**: Mole采用**安全优先**设计：
- 先用`--dry-run`预览
- 默认不删除系统关键文件
- 所有操作记录日志
- 高风险操作需确认

### Q: 和CleanMyMac什么关系？

**A**: Mole是命令行替代品，功能类似但：
- ✅ 完全免费开源
- ✅ 单一二进制
- ✅ 高度可脚本化
- ✅ 适合终端用户

### Q: 支持macOS外系统吗？

**A**: 实验性Windows版本可用：

```bash
# 查看windows分支
git clone -b windows https://github.com/tw93/Mole.git
```

### Q: 如何更新Mole？

```bash
# 更新到稳定版
mo update

# 更新到最新开发版（仅脚本安装）
mo update --nightly
```

---

## 总结

Mole是macOS维护领域的创新工具，它将多个知名工具的功能整合到一个命令行工具中，提供高效、可脚本化的系统维护体验。

**核心价值**：

1. **All-in-one**：一个工具解决所有维护需求
2. **命令行优先**：适合开发者，融入工作流
3. **安全优先**：保守策略，操作前预览
4. **免费开源**：MIT许可，完全透明
5. **高度可组合**：支持管道、脚本、自动化

**推荐人群**：
- ✅ macOS开发者
- ✅ 终端爱好者
- ✅ 需要自动化维护的用户
- ✅ 追求简洁高效的工具用户

**项目地址**：[https://github.com/tw93/Mole](https://github.com/tw93/Mole)

---

*本文基于Mole V1.33.0版本编写，发布时间：2026-04-07*
