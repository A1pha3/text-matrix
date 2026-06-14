---
title: "shadPS4：30.7K Stars·开源PlayStation 4模拟器"
date: "2026-04-12T01:54:00+08:00"
slug: shadps4-ps4-emulator-guide
description: "shadPS4 是一个开源的 PlayStation 4 模拟器，使用 C++ 编写，支持 Windows、Linux、macOS 和 FreeBSD，能够运行 Bloodborne 等游戏。"
draft: false
categories: ["技术笔记"]
tags: ["C++", "模拟器", "PS4", "PlayStation", "游戏"]
---

# shadPS4：30.7K Stars·开源 PlayStation 4 模拟器·C++重写的跨平台 PS4 模拟器

## 项目概述

shadPS4 是一个开源的 PlayStation 4 模拟器项目，使用 C++ 编写，支持 Windows、Linux、macOS 和 FreeBSD 平台。该项目由社区驱动，目前处于早期开发阶段，已经能够成功运行包括《血源》（Bloodborne）、《黑暗之魂 重制版》（Dark Souls Remastered）和《荒野大镖客》（Red Dead Redemption）在内的多款游戏。

需要特别注意的是，shadPS4 本身是模拟器核心，不包含图形用户界面。如果只是想使用模拟器玩游戏的最终用户，应该下载包含 GUI 的 QtLauncher 版本，而不是直接使用 shadPS4 核心。

## 技术架构

### 核心设计理念

shadPS4 采用了现代化的技术栈和设计理念：

- **C++ 重写**：整个项目使用 C++ 从零开始编写，而非基于现有的模拟器代码
- **跨平台支持**：支持 Windows、Linux、macOS 和 FreeBSD
- **模块化设计**：核心与 GUI 分离，便于维护和扩展
- **Vulkan 渲染**：使用现代图形 API

### 项目结构

项目源码目录结构清晰，各目录职责明确：

- **src/**：核心模拟器代码
- **cmake/**：CMake 构建配置
- **externals/**：外部依赖和子模块
- **documents/**：文档和构建指南
- **tests/**：测试代码
- **dist/**：发布版本

## 构建指南

### Windows 构建

Windows 平台构建需要以下前置条件：

- Visual Studio 2019 或更高版本
- CMake 3.20+
- Python 3.8+（用于构建脚本）
- Vulkan SDK

详细构建步骤请参考项目中的 `documents/building-windows.md` 文件。

### Linux 构建

Linux 平台需要安装以下依赖：

```bash
# Ubuntu/Debian
sudo apt install cmake build-essential vulkan-tools libvulkan-dev python3

# Fedora
sudo dnf install cmake gcc-c++ vulkan-tools vulkan-devel python3
```

详细构建步骤请参考 `documents/building-linux.md`。

### macOS 构建

macOS 用户需要满足以下条件：

- macOS 15.4 或更高版本
- Xcode 15+
- 支持 Metal 的 GPU

注意：由于 GPU 问题，Intel Mac 目前存在严重 bug。

macOS 构建详细步骤请参考 `documents/building-macos.md`。

### Docker 构建

项目支持使用 Docker 进行容器化构建，适合不想配置本地开发环境的用户。详细说明请参考 `documents/building-docker.md`。

## 使用方法

### 获取固件文件

shadPS4 可以加载部分 PlayStation 4 固件文件。以下是支持的固件模块，必须放置在模拟器的 `sys_modules` 文件夹中：

| 模块 | 模块 | 模块 | 模块 |
|------|------|------|------|
| libSceAudiodec.sprx | libSceCesCs.sprx | libSceFont.sprx | libSceFontFt.sprx |
| libSceFreeTypeOt.sprx | libSceJpegDec.sprx | libSceJpegEnc.sprx | libSceJson.sprx |
| libSceJson2.sprx | libSceLibcInternal.sprx | libSceNgs2.sprx | libScePngEnc.sprx |
| libSceRtc.sprx | libSceSystemGesture.sprx | libSceUlt.sprx | |

重要提示：这些模块需要从您合法拥有的 PlayStation 4 游戏机上提取。

### 命令行使用

shadPS4 核心的命令行使用方式如下：

```bash
# 基本用法：使用游戏目录 ID 启动游戏
shadPS4 CUSA00001

# 完整命令示例：全屏启动并使用默认配置
shadPS4 --fullscreen true --config-clean CUSA00001

# 游戏参数始终是最后一个
shadPS4 CUSA00001 --fullscreen true --config-clean

# 简写形式
shadPS4 -g CUSA00001 --fullscreen true --config-clean

# 直接启动 PS4 ELF 可执行文件
shadPS4 /path/to/game.elf

# 向游戏可执行文件传递参数
shadPS4 CUSA00001 -- -flag1 -flag2
```

完整的命令列表和详细说明，请运行 `shadPS4 --help`。

### GUI 使用

对于普通用户，推荐下载包含图形界面的 QtLauncher：

- 访问 [shadps4-emu/shadps4-qtlauncher releases](https://github.com/shadps4-emu/shadps4-qtlauncher/releases)
- 下载适合您操作系统的最新版本
- 解压后直接运行即可

QtLauncher 提供了用户友好的图形界面，无需记忆复杂的命令行参数。

## 键盘和鼠标映射

### 默认快捷键

| 按钮 | 功能 |
|------|------|
| F10 | FPS 计数器 |
| Ctrl+F10 | 视频调试信息 |
| F11 | 全屏切换 |
| F12 | RenderDoc 捕获 |

### 手柄映射

Xbox 和 DualShock 手柄开箱即用，支持自动识别。

### 键盘映射

| 手柄按钮 | 键盘映射 |
|----------|----------|
| LEFT AXIS UP | W |
| LEFT AXIS DOWN | S |
| LEFT AXIS LEFT | A |
| LEFT AXIS RIGHT | D |
| RIGHT AXIS UP | I |
| RIGHT AXIS DOWN | K |
| RIGHT AXIS LEFT | J |
| RIGHT AXIS RIGHT | L |
| TRIANGLE | Numpad 8 或 C |
| CIRCLE | Numpad 6 或 B |
| CROSS | Numpad 2 或 N |
| SQUARE | Numpad 4 或 V |
| PAD UP | UP |
| PAD DOWN | DOWN |
| PAD LEFT | LEFT |
| PAD RIGHT | RIGHT |
| OPTIONS | RETURN |
| BACK / TOUCH PAD | SPACE |
| L1 | Q |
| R1 | U |
| L2 | E |
| R2 | O |
| L3 | X |
| R3 | M |

注意：某些键盘可能需要按住 Fn 键来使用 F1-F12 功能键。Mac 用户应使用 Command 键替代 Control 键，并使用 Command+F11 进入全屏以避免与系统快捷键冲突。

键盘和鼠标映射可以在设置菜单中自定义，绑定配置会按游戏保存。支持每个绑定最多三个按键、鼠标按钮和鼠标移动映射到摇杆输入等功能。

## 调试和问题报告

### 调试文档

项目提供了详细的调试文档，位于 `documents/Debugging/Debugging.md`。内容包括：

- 如何测试游戏兼容性
- 如何收集调试信息
- 如何报告问题

### 游戏兼容性

在报告问题之前，建议先查看 shadPS4 游戏兼容性列表：

- 访问 [shadps4-game-compatibility](https://github.com/shadps4-compatibility/shadps4-game-compatibility)
- 查看已测试游戏的运行状态
- 了解已知问题和限制

### 提交问题

当遇到问题时，请：

1. 先查阅快速入门指南
2. 查看是否已有相同问题的报告
3. 收集详细的错误日志
4. 在 Discord 服务器中寻求帮助

## 参与开发

### 团队成员

shadPS4 由以下核心成员维护：

- **georgemoralis**：项目创始人
- **psucien**：核心开发者
- **viniciuslrangel**：核心开发者
- **roamic**：核心开发者
- **squidbus**：核心开发者
- **frodo**：核心开发者
- **Stephen Miller**：核心开发者
- **kalaposfos13**：核心开发者

Logo 由 Xphalnos 设计。

### 贡献代码

欢迎社区贡献代码！请遵循以下步骤：

1. 阅读 CONTRIBUTING.md 文件了解贡献指南
2. Fork 项目仓库
3. 创建特性分支
4. 进行开发
5. 提交 Pull Request

项目使用 GitHub Actions 进行持续集成，确保代码质量和测试覆盖。

### 特别鸣谢

项目团队对以下项目和团队表示特别感谢：

- **Panda3DS**：提供了理解和解决执行 PS4 二进制代码问题的帮助
- **fpPS4**：在理解 PS4 操作系统和库的复杂部分方面提供了大量帮助
- **yuzu**：着色器编译器以 yuzu 的 Hades 编译器为蓝本设计
- **felix86**：x86-64 到 RISC-V 的 Linux 用户空间模拟器
- **emudev.org**：硬件文档和逆向工程社区

## 版本信息

最新版本为 v0.15.0（代号 RE6_PRIG），发布于 2026 年 3 月 17 日。项目采用 GPL-2.0 开源许可证。

## 安装速查

```bash
# 核心构建（需要 CMake、Vulkan SDK、C++ 编译器）
git clone https://github.com/shadps4-emu/shadPS4.git
cd shadPS4
cmake -B build
cmake --build build

# QtLauncher 下载（最终用户使用）
# 访问 https://github.com/shadps4-emu/shadps4-qtlauncher/releases
```

## 参考链接

- GitHub：https://github.com/shadps4-emu/shadPS4
- 官网：https://shadps4.net/
- Discord：https://discord.gg/bFJxfftGW6
- X (Twitter)：https://x.com/shadps4
- 游戏兼容性：https://github.com/shadps4-compatibility/shadps4-game-compatibility
- 快速入门：https://github.com/shadps4-emu/shadPS4/wiki/I.-Quick-start-%5BUsers%5D