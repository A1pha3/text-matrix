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

## 学习目标

在阅读完本文后，你应该能够：

1. **理解 shadPS4 的技术架构**：掌握其核心设计理念（C++ 重写、跨平台支持、模块化设计、Vulkan 渲染），以及项目目录结构
2. **掌握构建与安装方法**：能够在 Windows、Linux、macOS 或 Docker 环境中成功构建 shadPS4 核心
3. **配置与运行游戏**：了解如何获取合法的 PS4 固件文件，掌握命令行与 GUI（QtLauncher）的使用方式
4. **自定义键盘和鼠标映射**：能够根据个人喜好配置手柄、键盘和鼠标的映射关系
5. **参与开发与调试**：了解如何报告问题、查看游戏兼容性列表、参与代码贡献

## 目录

1. [学习目标](#学习目标)
2. [项目概述](#项目概述)
3. [技术架构](#技术架构)
4. [构建指南](#构建指南)
5. [使用方法](#使用方法)
6. [键盘和鼠标映射](#键盘和鼠标映射)
7. [调试和问题报告](#调试和问题报告)
8. [参与开发](#参与开发)
9. [版本信息](#版本信息)
10. [安装速查](#安装速查)
11. [参考链接](#参考链接)
12. [自测题](#自测题)
13. [练习](#练习)
14. [进阶路径](#进阶路径)
15. [资料口径说明](#资料口径说明)

---

## 项目概述

shadPS4 并不是一个完整的产品——它属于"能跑部分游戏的在研模拟器"，距离"完全兼容"还有距离。项目由社区驱动，目前处于早期开发阶段，已经能够成功运行包括《血源》（Bloodborne）、《黑暗之魂 重制版》（Dark Souls Remastered）和《荒野大镖客》（Red Dead Redemption）在内的多款游戏。

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

## 自测题

以下问题用于检验你对 shadPS4 模拟器的理解程度：

1. **shadPS4 的核心设计理念是什么？**
   <details>
   <summary>点击查看答案</summary>
   shadPS4 采用了现代化的技术栈和设计理念：C++ 重写（整个项目使用 C++ 从零开始编写，而非基于现有的模拟器代码）、跨平台支持（支持 Windows、Linux、macOS 和 FreeBSD）、模块化设计（核心与 GUI 分离，便于维护和扩展）、Vulkan 渲染（使用现代图形 API）。
   </details>

2. **shadPS4 核心与 QtLauncher 的区别是什么？**
   <details>
   <summary>点击查看答案</summary>
   shadPS4 本身是模拟器核心，不包含图形用户界面。QtLauncher 是包含 GUI 的版本，适合最终用户使用。如果只是想使用模拟器玩游戏，应该下载 QtLauncher 版本，而不是直接使用 shadPS4 核心。
   </details>

3. **如何获取 PS4 固件文件？有什么法律注意事项？**
   <details>
   <summary>点击查看答案</summary>
   固件模块需要从你合法拥有的 PlayStation 4 游戏机上提取。这些模块必须放置在模拟器的 `sys_modules` 文件夹中。重要提示：这些模块只能从你合法拥有的 PS4 上提取，不得从其他来源获取。
   </details>

4. **shadPS4 支持哪些平台？有什么限制？**
   <details>
   <summary>点击查看答案</summary>
   支持 Windows、Linux、macOS 和 FreeBSD 平台。macOS 用户需要注意：需要 macOS 15.4 或更高版本、Xcode 15+、支持 Metal 的 GPU。由于 GPU 问题，Intel Mac 目前存在严重 bug。
   </details>

5. **如何报告 shadPS4 的问题？报告前应该做什么？**
   <details>
   <summary>点击查看答案</summary>
   在报告问题之前，建议先查看 shadPS4 游戏兼容性列表（https://github.com/shadps4-compatibility/shadps4-game-compatibility），了解已知问题和限制。当遇到问题时：1. 先查阅快速入门指南；2. 查看是否已有相同问题的报告；3. 收集详细的错误日志；4. 在 Discord 服务器中寻求帮助。
   </details>

## 练习

以下练习帮助你实践使用 shadPS4 模拟器：

### 练习 1：在 Linux 上构建 shadPS4

**任务**：在 Linux 平台上从源码构建 shadPS4 模拟器核心。

**步骤**：
1. 安装依赖：`sudo apt install cmake build-essential vulkan-tools libvulkan-dev python3`（Ubuntu/Debian）或 `sudo dnf install cmake gcc-c++ vulkan-tools vulkan-devel python3`（Fedora）
2. 克隆仓库：`git clone https://github.com/shadps4-emu/shadPS4.git`
3. 创建构建目录：`cd shadPS4 && mkdir build && cd build`
4. 配置：`cmake ..`
5. 构建：`cmake --build .`
6. 验证：运行生成的可执行文件，检查是否启动成功

**参考答案**：构建成功后，应该能看到 shadPS4 核心的命令行界面。如果遇到依赖问题，参考 `documents/building-linux.md` 文件。

### 练习 2：配置键盘和鼠标映射

**任务**：根据你的个人喜好，自定义 shadPS4 的键盘和鼠标映射配置。

**步骤**：
1. 启动 shadPS4（核心或 QtLauncher）
2. 进入设置菜单
3. 找到键盘和鼠标映射配置
4. 修改默认映射（例如，将手柄按钮映射到不同的键盘按键）
5. 保存配置并测试

**参考答案**：配置成功后，按下你自定义的键盘按键应该能触发对应的 PS4 手柄按钮动作。绑定配置会按游戏保存，所以不同游戏可以有不同映射。

### 练习 3：参与 shadPS4 开发

**任务**：为 shadPS4 项目贡献代码，修复一个简单的问题或添加一个小功能。

**步骤**：
1. 阅读 CONTRIBUTING.md 文件了解贡献指南
2. Fork 项目仓库到你的 GitHub 账号
3. 创建特性分支：`git checkout -b fix-some-issue`
4. 进行开发：修复 bug 或添加功能
5. 提交 Pull Request
6. 等待项目维护者的审查和反馈

**参考答案**：贡献成功后，你的 Pull Request 应该能通过 GitHub Actions 的持续集成检查（代码质量和测试覆盖）。项目维护者会在 Discord 或 GitHub 上提供反馈。

## 进阶路径

如果你希望更深入地使用或开发 shadPS4，可以按照以下路径进行：

1. **掌握多个平台的构建**：不要只停留在你熟悉的平台，尝试在 Windows、Linux、macOS 上分别构建 shadPS4，理解跨平台兼容性的挑战
2. **研究渲染管线**：深入阅读 shadPS4 的 Vulkan 渲染代码，理解 PS4 的图形 API 是如何被模拟的
3. **参与逆向工程**：如果你对 PS4 的内部工作机制感兴趣，可以参与 fpPS4、Panda3DS 等项目的逆向工程工作
4. **改进游戏兼容性**：选择一个你感兴趣的游戏，研究它在 shadPS4 上运行失败的原因，并尝试修复
5. **优化性能**：研究如何优化 shadPS4 的 CPU 指令翻译、内存管理、渲染性能等
6. **参与社区**：加入 shadPS4 的 Discord 服务器，与其他开发者和用户交流经验
7. **文档贡献**：为 shadPS4 编写或改进文档（如构建指南、调试指南、游戏兼容性报告等）

## 资料口径说明

本文档基于以下来源和假设：

1. **信息来源**：本文主要基于 shadPS4 的 GitHub 仓库（https://github.com/shadps4-emu/shadPS4）的 README、文档文件和配置信息。所有数字（Stars、版本信息等）来自仓库公开信息，截至本文写作时。
2. **构建依赖时效性**：文章描述了不同平台的构建依赖（如 CMake 版本、Vulkan SDK 版本等），但这些依赖的版本会随项目更新而变化。请以仓库最新版本为准。
3. **固件文件合法性**：文章提及需要从合法拥有的 PS4 上提取固件模块，但具体提取方法、法律边界在不同国家/地区可能有所不同。用户需要自行了解并遵守当地法律。
4. **游戏兼容性**：文章提及查看游戏兼容性列表，但兼容性状态会随项目开发而不断变化。某个游戏在本文写作时可能不兼容，但在最新版本中可能已经可以运行。
5. **macOS 支持限制**：文章说明了 macOS 平台的限制（需要 macOS 15.4+、Intel Mac 存在严重 bug 等），但这些限制可能会在未来版本中得到改善。
6. **局限性**：本文未深入评估 shadPS4 的性能表现、游戏兼容性详细列表、或与其他 PS4 模拟器（如有）的对比。这些评估需要结合实际测试经验和最新版本。

---

## 参考链接

- GitHub：https://github.com/shadps4-emu/shadPS4
- 官网：https://shadps4.net/
- Discord：https://discord.gg/bFJxfftGW6
- X (Twitter)：https://x.com/shadps4
- 游戏兼容性：https://github.com/shadps4-compatibility/shadps4-game-compatibility
- 快速入门：https://github.com/shadps4-emu/shadPS4/wiki/I.-Quick-start-%5BUsers%5D