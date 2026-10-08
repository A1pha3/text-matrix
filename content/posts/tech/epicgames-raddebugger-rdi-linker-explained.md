---
title: "EpicGames/raddebugger 技术解读：一个调试器为什么自己造了调试信息格式和链接器"
date: 2026-10-09T03:22:37+08:00
draft: false
description: "RAD Debugger 是 Epic Games 开源的 Windows x64 原生图形化调试器，8k+ Star。本文拆解它「调试器 + RDI 调试信息格式 + RAD Linker」三位一体的架构决策，解释自造格式与链接器解决了 PDB 工具链的哪些结构性问题。"
tags: ["debugger", "C", "Windows", "逆向工程"]
categories: ["技术笔记"]
github_repo: "EpicGames/raddebugger"
source_key: "gh:EpicGames/raddebugger"
slug : epicgames-raddebugger-rdi-linker-explained
---

# EpicGames/raddebugger 技术解读：一个调试器为什么自己造了调试信息格式和链接器

**核心判断**：RAD Debugger 不是一个"又一个调试器 UI"，而是一次对调试工具链的结构性重构——它同时做调试器、自定义调试信息格式（RDI）和链接器（RAD Linker）三件事，每一件都在解 PDB 时代的具体痛点。这个"三件套"的架构关系，才是理解这个项目的关键。

- 仓库：[EpicGames/raddebugger](https://github.com/EpicGames/raddebugger)
- 定位：原生（native）、用户态（user-mode）、多进程（multi-process）、图形化调试器
- 语言：C；协议：MIT
- 状态：ALPHA（当前 v0.9.29-alpha，2026-09-30 发布）；截至本文写作约 8065 Stars / 390 Forks
- 主战场：Windows x64 + PDB；**v0.9.29 起提供初步的 Linux x64 原生调试支持**（尚无预编译 Linux 二进制，需本地构建）

## 为什么值得看

大多数调试器项目的思路是"把现有调试信息解析得更好"。RAD Debugger 的思路是"现有调试信息格式本身有问题，我换一个"——然后发现换格式最彻底的入口在链接器，于是顺手写了一个高性能链接器。这条推理链每一步都有明确的工程动机，值得工具链开发者细读。

对普通 Windows C/C++ 开发者，它的直接卖点是：免费、MIT 协议、无 UI 框架依赖（纯自绘 UI）、由 Epic 持续投入（RAD Game Tools 团队出身，2021 年并入 Epic）。对工具链研究者，RDI 格式与"巨型可执行文件链接"的场景本身就是稀缺的一手材料。

## 系统地图：三件套如何咬合

```
  你的构建产物
  ├─ PE/COFF + PDB（MSVC 工具链产物）
  │     │  radbin（raddebugger 内含工具）按需转换
  │     ▼
  ├─ RAD Linker 产物 ──── 可选直接输出 ────┐
  │     └─ 标准 PDB                       │
  │                                       ▼
  └──────────────────────────────► RDI（RAD Debug Info）
                                          │
                                          ▼
                                   RAD Debugger（UI/引擎）
```

三个组件的角色：

| 组件 | 角色 | 解决的问题 |
|------|------|-----------|
| RAD Debugger | 调试器主体（UI + 调试引擎） | 现有图形化调试器在多进程、大项目场景下的体验与性能 |
| RDI 格式 | 自定义调试信息格式（Debug Info） | PDB/DWARF 解析慢、结构面向序列化而非查询、32 位表溢出 |
| RAD Linker | 高性能 x64 PE/COFF 链接器 | 巨型工程链接慢；PDB 32 位内部表在超大工程下会溢出产出坏 PDB |

关键理解：**RDI 是整个体系的中枢**。调试器不直接消费 PDB 或 DWARF，而是消费 RDI。PDB/DWARF 通过 `radbin` 工具按需转换（README 明确说明 PDB 转换是 on-demand 的），而 RAD Linker 可以在链接时直接产出 RDI，跳过转换环节。

## RDI：为什么不用 PDB

PDB（Program Database）是 MSVC 工具链的调试信息格式，DWARF 是 GCC/Clang 侧的对应物。RAD 团队没有继续在这两者之上做更快的解析器，而是定义了 RDI（RAD Debug Info），理由可以从仓库结构反推出来：

- RDI 是"在代码中规定的格式"（currently specified in code）：格式定义就在 `src/lib_rdi/rdi.h` 和 `rdi.c` 中，解析辅助在 `rdi_parse.h/.c`，构造与序列化库在 `src/lib_rdi_make`。这意味着格式消费者可以直接以库的形式嵌入，而不是把 .h/.c 反复翻译。
- 转换层独立成模块：`src/rdi_from_pdb`、`rdi_from_codeview`、`rdi_from_dwarf`、`rdi_from_elf`、`rdi_from_coff` 各自成目录，转换不是调试器内核里的特判，而是显式管线。
- 官方自述的动机之一：**超大可执行文件的 PDB 会因内部 32 位表溢出而损坏（broken PDBs）**——这是 RAD Linker 直接产出 RDI 的核心理由之一，另一个是消除按需转换的等待时间。

换句话说，PDB 在"巨型工程"场景下不只是慢，是会坏。RDI 同时消解了"慢"和"坏"两个问题。

值得注意的边界：v0.9.29 的 Linux 支持仍是早期状态，从 DWARF 转 RDI 的类型去重（type deduplication）尚有已知 bug（issue #959）——格式理想是一回事，转换管线的工程完备度是另一回事。

## RAD Linker：把入口也占了

如果 RDI 是中枢，为什么还要写链接器？因为链接器是调试信息的第一现场：

1. **性能**：官方基准场景（调试信息数 GB 的测试用例）链接时间比 MSVC 链接器快约 50%。链接器默认按 CPU 核数开线程，可用 `/rad_workers` 限制并行度。
2. **命令行兼容**：语法完全兼容 MSVC，`/help` 列出全部已实现的开关——替换成本低。
3. **大页（large pages）**：显式加 `/rad_large_pages` 再省 25% 链接时间。README 的态度很有味道：默认关闭，因为 Windows 大页支持"有点 buggy"，官方只推荐在每次链接后环境会被重置的 Docker/VM 镜像里用，否则会快速碎片化内存逼你重启。Linux 移植版计划在大页上做到鲁棒。
4. **尚未支持 LTO**（link-time optimization，链接时优化），路线图中。

这是一个典型的"自举"设计：RAD Linker 生成标准 PDB（保持与既有工具链互操作），但可选直接产出 RDI——同一个二进制，调试器打开时零转换成本。

## 调试器本体：C 写的自绘 UI 与明确的边界

调试器主体有几个不寻常的工程选择：

- **纯 C，无 UI 框架**：`src/ui`、`src/render`、`src/draw`、`src/font_cache`、`src/font_provider` 等目录表明 UI 层是自绘的（渲染、字体、文本排版全部自管），这正是 RAD 团队工具的典型风格。`src` 下 60+ 个模块目录（`x64`、`disasm`、`unwind`、`pdb`、`dwarf`、`natvis`、`minidump`……）按二进制格式与子系统垂直切分，可读性相当好。
- **多进程架构**：README 第一句就强调 user-mode、multi-process——这是它与许多玩具调试器项目的分水岭。
- **元编程自举**：构建时会先编译 `metagen_main.c`，扫描源码树（458 个文件）、解析 16 个 metadesk 文件、从 97 张表生成层间代码（metadesk 是 RAD 系元语言）。整个构建无外部构建系统依赖，Windows 上一个 `build.bat`、Linux 上一个 `build.sh` 完成。
- **v0.9.29 的新能力**（节选自 CHANGELOG）：初步 Linux x64 原生调试、Minidump（`.dmp`）崩溃转储加载、按线程命中的断点设置、watch 表达式随工程加载/卸载。

明确的边界（README/CHANGELOG 自述）：仅支持本地机器调试（无远程）；Linux 侧不支持 `fork`/`vfork` 调试；TLS 定位假设被调试进程与调试器同 libc 版本；`.eh_frame_hdr` 缺失时调用栈可能解不开；位域（bitfield）类型信息尚不正确。整个项目处于 ALPHA，官方明确请用户提 issue 附 dump 与复现材料。

## 快速上手（Windows）

从 [releases](https://github.com/EpicGames/raddebugger/releases) 下载预编译包即可，包内附带面向使用者的 README。想从源码构建：

```bat
:: 1. 装 Microsoft C/C++ Build Tools v15(2017)+ 与 Windows SDK
:: 2. 在 "x64 Native Tools Command Prompt" 中（等价于先跑 vcvarsall.bat x64）
cd raddebugger
build            :: debug 模式，产出 build\raddbg.exe
build release    :: release 模式，慢但快
```

也可用 Clang 构建（需 Windows SDK）。Linux 构建需 GCC 或 Clang 加 `libfreetype`、`libx11` 等动态库，然后 `./build.sh`——注意 Linux 目前无预编译发布。

`radbin` 工具（或调试器的 `--bin` 参数）可把 PDB 转成 RDI 并对 RDI 做文本转储（textual dump），适合想直接观察格式的读者。

## 采用建议

按场景给顺序：

1. **巨型 C/C++ Windows 工程、链接调试循环慢**：最有价值的目标用户。RAD Linker 的 50% 链接提速 + 巨型 PDB 溢出问题，单 linker 就值得试；先用标准 PDB 模式接入，风险低。
2. **想换个调试器体验的 Windows 开发者**：可以直接用，但要接受 ALPHA 属性——把遇到的问题当贡献提 issue，而不是当生产工具依赖。
3. **工具链/格式研究者**：RDI 的代码内规格（`src/lib_rdi`）与 `rdi_from_*` 转换管线是一手材料，`src` 的模块切分本身就是大型 C 项目组织的范本。
4. **Linux 开发者**：v0.9.29 起可以本地构建尝鲜，但已知问题清单不短，等 1-2 个版本再评估更稳。

本文不覆盖：调试器的具体操作技巧（见发布包内 README）、RDI 二进制布局的字段级细节（直接读 `src/lib_rdi/rdi.h`）、以及 RAD Linker 的 LTO 支持（尚未实现）。
