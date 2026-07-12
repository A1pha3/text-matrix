---
title: "SharpEmu：用 C# 从零写的实验性 PS5 模拟器，1148 Stars 的早期项目在 Windows 上走到哪一步"
date: 2026-07-13T03:03:54+08:00
slug: par274-sharpemu-csharp-emulator
description: "SharpEmu 是开发者 par274（GitHub ID）维护的实验性 PS5 模拟器项目，C# 编写、GPL-2.0、1148 Stars，主攻 Windows。本文拆开它的 6 个模块（Core/CPU/HLE/Libs/GUI/CLI）、当前能力（eboot.bin 加载、PRX 模块、AGC 初始化）、已测试游戏（Demon's Souls 等），以及「实验性」标签在工程层面的真实含义。"
draft: false
categories: ["技术笔记"]
tags: ["C#", ".NET", "PS5", "模拟器", "HLE"]
---

# SharpEmu：用 C# 从零写的实验性 PS5 模拟器，1148 Stars 的早期项目在 Windows 上走到哪一步

## §1 先给判断

SharpEmu 是一个**实验性的** PlayStation 5 模拟器，纯 C# 编写、.NET SDK 构建、1148 Stars（2026-07-12 数据）、GPL-2.0 许可。它值得专门拆开看的原因有三条：

1. **C# 写模拟器的少见样本**：绝大多数现代模拟器（PCSX2、Ryujinx、ShadPS4、Citra）用 C++ 或 Rust；SharpEmu 选了 .NET 平台，目标是「基础设施先行」。
2. **PS5 的早期空白**：相比 PS3/PS4 模拟器，PS5 模拟器生态极薄，公开项目一只手数得过来（Kyty 是少数）。SharpEmu 是这一空白里的新成员。
3. **诚实标注状态**：README 反复用 WARNING 块标注「实验性」「目前主攻 Windows」「当前重点是准确性而非游戏兼容」——这是同类项目少见的克制。

仓库地址：`https://github.com/par274/sharpemu`。最新 release tag `win64-main-d2fca37`（2026-07-12 自动构建），代码最近 commit 同样 2026-07-12，活跃度极高——过去一个月平均 1-3 个 PR/天。

文章主轴：拆开 6 个模块（Core/CPU/HLE/Libs/GUI/CLI）+ 当前能力清单 + 已测试游戏 + 与 ShadPS4/Kyty/Ryujinx 的边界关系，最后给一份「你要不要现在就跟这个项目」的判断框架。

## §2 项目坐标：放在模拟器生态里看

PS5 模拟器生态（2026 年中）大致有三类位置：

| 类型 | 代表 | 目标 | SharpEmu 位置 |
|------|------|------|---------------|
| 主机端修改/调试工具 | PS5 SDK 工具链、官方的 Target Manager | 主机上的开发调试 | 不选 |
| 用户态高保真模拟 | Kyty、ShadPS4 思路 | 跑商业游戏 | 长期目标 |
| 实验性/学习用模拟 | SharpEmu | 摸清架构，跑通已知案例 | **当前位置** |

作者明确写：

> SharpEmu focuses exclusively on the PlayStation 5. Our goal is **not** to emulate PS4 games, as there is already an excellent emulator dedicated to that platform: **ShadPS4**.

也就是说，**PS4 模拟留给 ShadPS4，SharpEmu 只做 PS5**。这是定位选择，不是技术限制。

## §3 模块拓扑：6 个工程集

仓库 `src/` 下的 6 个 C# 工程集：

```
src/
├── SharpEmu.CLI/               # 命令行启动器
├── SharpEmu.Core/              # 核心仿真逻辑
├── SharpEmu.CPU/               # CPU 指令仿真
├── SharpEmu.GUI/               # Avalonia GUI 启动器
├── SharpEmu.HLE/               # High-Level Emulation（HLE）模块管理
└── SharpEmu.Libs/              # PS5 系统库实现（29 个子库）
```

外层：

- `SharpEmu.slnx`：解决方案入口
- `Directory.Build.props` + `Directory.Packages.props`：集中 MSBuild 属性与 NuGet 包版本
- `global.json`：固定 .NET SDK 版本
- `nuget.config`：NuGet 源
- `scripts/`：构建辅助脚本
- `assets/`：项目资源
- `LICENSES/` + `REUSE.toml`：SPDX 许可合规
- `.github/`：CI 与 PR 模板

整套项目走「一个解决方案 + 多个工程集」的现代 .NET 风格，用 `Directory.Packages.props` 统一包版本——这是 .NET 8+ 的中央包管理（CPM）实践。

## §4 SharpEmu.Core：仿真引擎骨架

`src/SharpEmu.Core/` 下：

```
Core/
├── IFileSystem.cs              # 文件系统抽象
├── PhysicalFileSystem.cs       # 物理文件系统实现
├── SharpEmu.Core.csproj
├── packages.lock.json
├── Cpu/                        # CPU 仿真引用
├── Loader/                     # ELF / eboot.bin 加载
├── Memory/                     # 内存管理
└── Runtime/                    # 运行时调度
```

四个子目录正好对应模拟器核心的四个职责：

- **Loader**：解析 `eboot.bin` 和 `.elf` 文件——这是 PS5 自研游戏的入口格式
- **Memory**：构建 guest 内存模型——PS5 用 64-bit 寻址、虚拟内存
- **Cpu**：CPU 仿真（委托给 SharpEmu.CPU 工程集）
- **Runtime**：线程、调度、Fiber、PlayGo 场景

`PhysicalFileSystem.cs` 把 host 文件系统抽象成 PS5 沙箱视角——guest 程序通过 `IFileSystem` 接口读「游戏目录」时，实际命中 host 的某个具体路径。这是沙箱与兼容性之间的桥梁。

## §5 SharpEmu.CPU：指令集仿真

`src/SharpEmu.CPU/` 是指令仿真核心。PS5 用的是 AMD x86-64 定制架构（基于 Zen 2），不是自研 ISA——这意味着 SharpEmu 的 CPU 工程集理论上可以用 JIT（Just-In-Time 编译）把 guest 指令翻译到 host x86-64，避免纯解释执行的性能瓶颈。

但 README 写「executing native CPU instructions」用的是「execute」（执行）而不是「JIT compile」——SharpEmu 当前应该是解释执行模式，性能远低于原生或 JIT 方案。这对实验性项目是合理选择：先把指令语义跑通，再考虑 JIT。

## §6 SharpEmu.HLE：高层仿真模块管理

`src/SharpEmu.HLE/` 文件清单：

```
HLE/
├── CpuContext.cs               # CPU 上下文
├── CpuRegister.cs              # 寄存器视图
├── ExportedFunction.cs         # HLE 导出函数基类
├── Generation.cs               # 代码生成辅助
├── GuestThreadExecution.cs     # Guest 线程执行
├── HleDataSymbols.cs           # HLE 数据符号表
├── ICpuMemory.cs               # 内存抽象
├── IGuestMemoryAllocator.cs    # Guest 内存分配
├── IModuleManager.cs           # 模块管理接口
├── ISymbolCatalog.cs           # 符号目录接口
├── ModuleManager.cs            # PRX/SYS_MODULE 管理
├── OrbisGen2Result.cs          # Orbis（PS5 OS）Gen2 结果类型
├── SharpEmu.HLE.csproj
├── SysAbiExportAttribute.cs    # Sys ABI 导出标记
├── SysAbiFunction.cs           # Sys ABI 函数包装
├── SysAbiSymbol.cs             # Sys ABI 符号
└── Aerolib/                    # 一个 HLE 库子目录
```

HLE（High-Level Emulation）的核心思路：**不重新实现 PS5 OS 内核，而是在 guest 程序调用系统函数时，由 SharpEmu 直接处理**。

例如 guest 程序调用 `sceVideoOutSubmitBuffers`（PS5 视频输出 API），传统 LLE（Low-Level Emulation）需要仿真整个 PS5 内核到能处理这个调用；HLE 则是 SharpEmu 直接 hook 这个函数，转发到自己的实现。

关键 HLE 概念：

| 概念 | 含义 |
|------|------|
| `SysAbiFunction` | PS5 系统 ABI 的函数包装（带 `SysAbiExportAttribute`） |
| `IModuleManager` | 加载 PS5 PRX（动态链接库）和 SYS_MODULE |
| `ISymbolCatalog` | 符号解析表，把函数名映射到 SysAbi |
| `GuestThreadExecution` | 在 guest 线程模型上跑 HLE 调用 |
| `CpuContext` / `CpuRegister` | 把 CPU 状态暴露给 HLE |

`ModuleManager.cs` 实现了 PRX 模块管理——PS5 游戏常常依赖多个系统 PRX（类似 Windows 的 DLL），HLE 要能识别「`libSceVideoOut.prx` 导出函数 X」并转到 SharpEmu 实现。

## §7 SharpEmu.Libs：29 个 PS5 系统库的 HLE 实现

`src/SharpEmu.Libs/` 是最大的工程集，目录列表：

```
Libs/
├── Agc/                        # AGC（PS5 GPU）相关
├── Ampr/                       # AMPR（PS5 Media Engine）
├── AppContent/                 # 应用内容管理
├── Audio/
├── AvPlayer/                   # 音视频播放
├── CommonDialog/
├── CxxAbiExports.cs            # C++ ABI 导出
├── DiscMap/                    # 光盘映射
├── Fiber/                      # PS5 Fiber（协程）
├── GameUpdate/                 # 游戏更新
├── Ime/                        # 输入法
├── Json/
├── Kernel/                     # 内核关键 API
├── LibcInternalExports.cs      # libc 内部
├── LibcStdioExports.cs         # libc stdio
├── Mouse/
├── Network/
├── Ngs2/                       # 下一代 Sound System
├── Np/                         # Network Platform（账号、奖杯等）
├── NpGameIntent/
├── Pad/                        # 手柄
├── PlayGo/                     # PlayGo（PS5 边下边玩）
├── Rtc/                        # 实时时钟
├── SaveData/                   # 存档
├── Share/
├── SharpEmu.Libs.csproj
├── SystemGesture/
├── SystemService/
├── Ult/                        # PS5 通用库
├── UserService/
└── VideoOut/                   # 视频输出（关键！）
```

29 个目录几乎一对一映射到 PS5 公开的 SDK 模块。每个目录里是 HLE 函数的 C# 实现。

几个值得专门提的模块：

### §7.1 VideoOut

README 提到的「Video outputs in some games」「Some games have reached like `sceVideoOut` and AGC stages」——`VideoOut/` 是 SharpEmu 已能让部分游戏输出视频的关键模块。

CHANGELOG 显示 2026-07-11 至 2026-07-12 有 `[AGC] Quake rendering progress: WAIT_REG_MEM, draw fixes, VideoOut, and HLE improvements` 这种密集提交——AGC（PS5 GPU 驱动）正在被持续还原。

### §7.2 Pad

PS5 DualSense 手柄支持——SharpEmu 的 `Pad/` 模块处理手柄输入。

### §7.3 PlayGo

PS5 的「边下边玩」机制——`PlayGo/` 处理游戏部分下载场景。README 列了「PlayGo scenarios」作为已支持能力之一。

### §7.4 Fiber

PS5 协程——`Fiber/` 处理 PS5 的 Fiber API，README 列「`Fiber` and `AMPR` exports」为已支持能力。

## §8 SharpEmu.GUI：Avalonia 跨平台 GUI

`src/SharpEmu.GUI/` 关键文件：

```
GUI/
├── App.axaml / App.axaml.cs
├── DiscordRichPresence.cs       # Discord Rich Presence 集成
├── EmulatorProcess.cs           # 启动子进程跑仿真
├── GameEntry.cs                 # 游戏条目模型
├── GuiLauncher.cs               # GUI 启动器主控
├── GuiSettings.cs               # GUI 设置
├── LogLine.cs                   # 日志行模型
├── MainWindow.axaml / MainWindow.axaml.cs
├── SharpEmu.GUI.csproj
├── SndPreviewPlayer.cs          # 音频预览
├── Atrac9/                      # ATRAC9 音频解码
└── packages.lock.json
```

注意 `.axaml`——这是 **Avalonia** 的 XAML 格式，不是 WPF/UWP。Avalonia 是 .NET 的跨平台 UI 框架，类似 WPF 但能跑在 Windows / Linux / macOS 上。这和作者在 README 说的「Windows 优先、Linux/macOS 规划中」一致——Avalonia 让 GUI 工程集「一次写好，将来跨平台不用重写」。

几个亮点：

- **`DiscordRichPresence`**：把当前模拟的游戏状态发到 Discord（参考 ShadPS4 的做法）
- **`GameEntry`**：游戏库条目模型，配合 GUI 启动器
- **`Atrac9/`**：PS5 用的 ATRAC9 音频编解码
- **`SndPreviewPlayer`**：预览游戏声音

## §9 SharpEmu.CLI：命令行启动器

`src/SharpEmu.CLI/` 是命令行入口。README 的使用方式：

```powershell
.\SharpEmu "eboot.bin" 2>&1 | Tee-Object -FilePath "log.txt"
```

也就是说 GUI 不是唯一入口——你可以纯命令行跑仿真。CLI 的存在降低了两类用户的门槛：

1. **开发者**：CI/批处理更容易
2. **高级用户**：不需要 GUI 也能跑

## §10 当前能力清单（README 明文）

README 列了 SharpEmu 当前能做什么：

- 加载 `eboot.bin` 和 `.elf` 文件
- 执行 native CPU 指令
- 读取基本游戏元数据（title、version 等）
- 加载系统模块（PRX / SYS_MODULE）
- 部分支持一些内核函数
- `Fiber` 和 `AMPR` exports
- PlayGo 场景
- 初始加载游戏文件
- Shader/resource submits 和 AGC initial
- 部分游戏视频输出

部分游戏已经达到 `sceVideoOut` 和 AGC 阶段。

值得专门指出的两个含义：

1. **「执行 native CPU 指令」≠ 「跑游戏」**：CPU 指令能跑通，但要让一个商业游戏从头跑到尾，需要图形、音频、输入、保存、网络、奖杯等一整条链路——其中大部分仍在 HLE 实现阶段。
2. **AGC initial 阶段**：AGC 是 PS5 GPU 驱动，「initial」表示驱动初始化已经能完成，但距离 Vulkan 级光栅化还有距离（README 里 Dreaming Sarah 的「Real texture rendering」是早期里程碑）。

## §11 已测试游戏（README 收录）

README 列了 4 个已测试案例：

| 游戏 | 类型 | 当前阶段 | 备注 |
|------|------|---------|------|
| Demon's Souls Remake [PPSA01341] | 3A 大作 | 视频循环 + shader 准备转 SPIR-V/Vulkan | 距离可玩很远 |
| Poppy Playtime Chapter 1 [PPSA20591] | 独立恐怖 | 早期 | Issue #3 |
| SILENT HILL: The Short Message [PPSA10112] | 中型作品 | 早期 | Issue #4 |
| Dreaming Sarah [PPSA02929] | 独立小品 | **真实纹理渲染** | Splash 贴图已显示 |

特别提 **Dreaming Sarah**——它能用真实纹理渲染 splash 画面，这是 SharpEmu 当前最大的里程碑之一。能渲染真实纹理意味着：

- AGC 基础渲染管线已通
- 纹理上传和着色器绑定能工作
- 至少一个完整的渲染帧能产出

这对一个 2026-03 才创建（仓库 `created_at: 2026-03-11`）的项目是相当快的进展。

## §12 与 ShadPS4 / Kyty / Ryujinx 的关系

README 的 Special Thanks 列出三个参照项目：

| 项目 | 提供给 SharpEmu 的帮助 |
|------|---------------------|
| **ShadPS4**（PS4 模拟器） | 帮助理解 PlayStation 4 基础架构 |
| **Kyty**（PS5 模拟器） | 研究 native 代码执行的关键参照（少数公开 PS5 仿真项目） |
| **Ryujinx**（Switch 模拟器） | 文件系统处理与 C# 实现模式的参考 |

注意：

1. **ShadPS4 是 PS4 不是 PS5**：SharpEmu 用的是其架构思路，不是直接移植
2. **Kyty 几乎唯一**：PS5 模拟器公开项目一只手数得过来，Kyty 是主要参照
3. **Ryujinx 的 C# 模式**：作为同样用 C# 写的模拟器，Ryujinx 的低层架构对 SharpEmu 是直接借鉴对象

## §13 关键 commit 模式：commit message 编码约定

CHANGELOG 风格很规整——commit message 用 `[模块]` 前缀：

```
[agc] Reset transparent Chowdren effect-layer fills (#83)
[github] Fix placeholder formatting in game compatibility template (#84)
Libs: add libSceDiscMap HLE exports (ported from Kyty) (#79)
[AGC] Quake rendering progress: WAIT_REG_MEM, draw fixes, VideoOut, and HLE impr
[GUI] Basic hotkey and full-screen support (#75)
[GUI] Console Search & Log Path Selector (#74)
GUI: Discord Rich Presence (#73)
```

这种前缀约定的好处：

- 仓库活跃度一目了然——哪个模块最近被改
- PR review 容易分类
- CHANGELOG 自动生成友好

这是值得其它开源项目借鉴的工程实践——特别是「[模块] 类型 + 描述」的格式让 PR 历史成为可检索的「设计日志」。

## §14 最近 commit 节奏（2026-07-11 至 07-12 摘录）

| 日期 | commit |
|------|--------|
| 2026-07-12 | `[agc] Reset transparent Chowdren effect-layer fills (#83)` |
| 2026-07-12 | `[github] Fix placeholder formatting in game compatibility template (#84)` |
| 2026-07-12 | `Libs: add libSceDiscMap HLE exports (ported from Kyty) (#79)` |
| 2026-07-12 | `Fix UnmanagedCallersOnly boot crash & Core Engine Improvements (CPU, HLE, AGC)` |
| 2026-07-12 | `[GUI] Basic hotkey and full-screen support (#75)` |
| 2026-07-11 | `[GUI] Console Search & Log Path Selector (#74)` |
| 2026-07-11 | `GUI: Discord Rich Presence (#73)` |
| 2026-07-11 | `[AGC] Quake rendering progress: WAIT_REG_MEM, draw fixes, VideoOut, and HLE impr` |
| 2026-07-11 | `Add sceKernelNanosleep to libKernel (#72)` |
| 2026-07-11 | `core: unify clock dispatch logic, add precise clocks, and enforce coalesced time` |

能读出三点：

1. **CPU 引擎改进密集**：UnmanagedCallersOnly boot crash + clock dispatch + 精确时钟——CPU 仿真在持续打磨
2. **GUI 同步推进**：Discord Rich Presence、热键、全屏、日志搜索——不是只盯核心引擎
3. **HLE 库扩充**：libSceDiscMap、libKernel nanosleep 都是 PS5 SDK 的真实函数

## §15 「实验性」在工程层面的真实含义

作者在 README 多处强调 experimental 和 research：

> [!WARNING]  
> Currently the primary development target is Windows.

> [!WARNING]  
> SharpEmu is an experimental PS5 emulator developed from scratch in C#. The current focus is on accuracy and infrastructure setup rather than game-specific compatibility.

> This project is developed purely for research and educational purposes. There are no commercial goals associated with it.

翻译过来：

1. **不承诺游戏兼容**：可能跑通一些独立游戏，但 3A 大作（Demon's Souls、SILENT HILL）的渲染/物理/音频链路远远未完成
2. **不承诺跨平台**：Linux/macOS 用户能编译但不是开发目标
3. **不承诺路线图时间表**：作者明确说项目没有 roadmap 时间承诺
4. **不承诺生产可用**：定位是「了解 PS5 架构 + 反向工程学习」

这是诚实标签，不是免责声明——读 SharpEmu 源码/参与开发是合理的；但指望它现在能替代真机跑大作，是不合理的期望管理。

## §16 决策表：你要不要现在就跟这个项目

| 你是谁 | 你的诉求 | 建议 |
|--------|---------|------|
| PS5 逆向/安全研究员 | 想摸 PS5 系统架构 | ✅ SharpEmu 是公开 PS5 模拟器里可读性最高的 C# 实现 |
| 想给 PS5 模拟器生态贡献代码 | 想 PR | ✅ 欢迎，活跃度极高（每天 1-3 个 PR） |
| 普通玩家想跑 PS5 游戏 | 想玩 Demon's Souls | ❌ 远不到可玩状态 |
| 模拟器学习者 | 想研究 PS5 HLE 模式 | ✅ 29 个 Libs 目录的命名映射是现成教材 |
| 在用 ShadPS4 的 PS4 玩家 | 想升级到 PS5 模拟 | ⚠️ ShadPS4 仍更成熟；SharpEmu 5 年内不会追上 |
| 想找 PS3/PS2/PS1 模拟器 | — | ❌ 不在项目范围 |
| Linux/macOS 玩家 | 想在非 Windows 跑 | ⚠️ Avalonia GUI 跨端代码已就位，但运行时仿真仍需打磨 |

## §17 资料口径与边界

**已确认**（仓库可见证据）：
- 1148 Stars / 69 Forks / 23 open issues（GitHub API 2026-07-12 数据）
- GPL-2.0 许可
- C# 语言主导
- 仓库 `created_at: 2026-03-11`（即项目年龄约 4 个月）
- 6 个 C# 工程集（Core/CPU/HLE/Libs/GUI/CLI）
- SharpEmu.Libs 下 29 个 PS5 SDK 模块目录
- 主分支 `main`
- 最近 commit 2026-07-12
- 已支持能力 10 项（README 列）
- 已测试游戏 4 个（README 列）
- GUI 框架 Avalonia（从 `.axaml` 文件推断）
- Central Package Management 用法（`Directory.Packages.props` 存在）

**已显式标注**：
- CPU 仿真当前是解释执行还是 JIT——未在 README 明文，按 README 用词「execute」推断为解释执行
- 性能数字——README 没给任何 FPS 或加载时间基准
- 商业游戏兼容度——4 个测试案例的进展程度以 README 描述为准

**不在本文覆盖**：
- PS5 SDK 模块的完整函数列表（29 个目录里的具体导出函数未一一列）
- SharpEmu 与 Kyty 在 CPU 仿真上的具体差异
- Linux/macOS 编译是否真能跑通（README 只说 planned）
- 与 PS5 主机系统版本（1.x/2.x/3.x）的对应关系

## §18 参考链接

- 仓库主链接：<https://github.com/par274/sharpemu>
- Discord：<https://discord.gg/6GejPEDqpc>
- 兼容性问题跟踪：<https://github.com/par274/sharpemu/issues>
- 参照项目：
  - ShadPS4（PS4 模拟器）：<https://github.com/shadps4-emu/shadPS4>
  - Kyty（PS5 模拟器）：<https://github.com/InoriRus/Kyty>
  - Ryujinx（Switch 模拟器，C#）：<https://github.com/Ryujinx/Ryujinx>
- GPL-2.0 许可：<https://github.com/par274/sharpemu/blob/main/LICENSE.txt>

## §19 自测题

1. SharpEmu 6 个 C# 工程集分别承担什么职责？Core 和 HLE 的边界是什么？
2. README 列了 10 项「当前能力」，其中哪三项是「基础设施」、哪三项是「接近可玩」？
3. Dreaming Sarah 能渲染真实纹理这个里程碑意味着 AGC 仿真走到哪一步？
4. 作者把 PS4 模拟留给 ShadPS4 这个定位选择是技术限制还是产品决策？给出你的判断依据。
5. SharpEmu 用 C# 而不是 C++/Rust 写模拟器，列出三个可能的工程权衡（性能 / 可维护性 / JIT 难度）。