---
title: "shadPS4：从「能进游戏」到「能玩完」，一个 C++ PS4 模拟器的半年爬坡"
date: "2026-04-12T01:54:00+08:00"
lastmod: 2026-10-04
slug: shadps4-ps4-emulator-guide
github_repo: "shadps4-emu/shadPS4"
source_key: "gh:shadps4-emu/shadPS4"
description: "shadPS4 是用 C++ 从零编写的开源 PS4 模拟器，本文发表时 star 已过 3 万，半年后连发四个版本：新配置系统、自研网络后端 shadnet、ZArchive 单文件游戏、Mesa KosmicKrisp 驱动落地 macOS。本文拆解它的三件套分工、四平台构建门槛、兼容性报告纪律，以及为什么《血源》至今仍是 Ingame 而非 Playable。"
draft: false
categories: ["技术笔记"]
tags: ["C++", "模拟器", "开源"]
---

## 从「能不能跑」到「能不能玩完」

PS4 模拟器是个门槛极高的赛道：要在 x86-64 上原生执行 PS4 的 x64 代码、把主机 GPU 的 GNM 图形调用翻译成 Vulkan、再把几十个系统库 High-Level Emulation（HLE，高层模拟）逐一补齐。shadPS4 是这个赛道上目前最活跃的开源项目——用 C++ 从零编写，不基于任何现有模拟器的代码。

它不是完整产品，官方 README 开头就把预期压低："shadPS4 is early in development, don't expect a flawless experience"。但姿态低不等于进展慢。本文发表那周（2026 年 4 月），仓库 star 已达 30,744（Wayback Machine 4 月 13 日快照实拍）；到 2026-10-04 复查，star 涨到 33,069，半年里发了 v0.16 到 v0.19 四个正式版本，另有以日期命名的 pre-release 滚动构建（最新一条 10 月 4 日）。

更值得看的是这半年补了什么：配置系统重做、自研网络后端、macOS 换上 Mesa 的 KosmicKrisp 驱动、视频播放从黑屏变正常。核心模拟已经过了「能不能开机」的阶段，现在的战场是「能不能稳定玩完一整局」。一个能说明精度现状的事实是：《血源》在官方兼容性仓库里至今标的是 **Ingame**（能进游戏但有破坏性问题），而不是 Playable（无重大问题可玩）——「跑起来了」和「玩得完」之间，还有很长的路。

## 系统地图：三件套各管一段

看懂 shadPS4 先要分清三个仓库的分工，混在一起谈是这类项目解读最常见的误区：

| 组件 | 仓库 | 职责 | 面向谁 |
|------|------|------|--------|
| 模拟器核心 | shadps4-emu/shadPS4 | CPU/GPU/内核/系统库模拟，命令行启动 | 开发者、命令行用户 |
| QtLauncher | shadps4-emu/shadps4-qtlauncher | 官方图形启动器：游戏库、设置、手柄配置 | 普通用户 |
| 兼容性仓库 | shadps4-compatibility/shadps4-game-compatibility | 按游戏收集可玩性报告，五级标签分类 | 所有人查表用 |

主仓库 README 强调核心不含 GUI——只想玩游戏的用户应该直接下载 QtLauncher 的构建产物。2026-10-04 读数：主仓 33,069 star / 2,609 fork，GPL-2.0 协议，主语言 C++，默认分支 main，当天仍有提交；QtLauncher 是 2025 年 9 月从主仓库拆出的独立仓库，486 star。

半年四个版本的演进脉络，官方 release notes 给得很清楚：

| 版本 | 发布 | 代号 | 关键变化 |
|------|------|------|----------|
| v0.16.0 | 2026-06-01 | Plutie-fueled | 官方称当时最大更新：新配置系统架构落地，按游戏管理设置的基础 |
| v0.17.0 | 2026-07-30 | Garbage Collector's Edition | 自研网络后端 **shadnet** 首次集成（大厅、房间、好友、邀请，尚不能多人联机）；**ZArchive** 支持把每游戏两万个文件压成单文件；macOS 接入 Mesa 的 **KosmicKrisp** Vulkan 驱动，兼容性与速度明显改善 |
| v0.18.0 | 2026-08-18 | UltraPersona | 修 v0.17 的 shadnet 授权问题；AvPlayer 改为 LLE 加载（需新固件模块，坏视频的游戏恢复）；内核事件标志重写，《旺达与巨像》启动挂起被修复，官方口径是「能稳定进入菜单」；实验性 red zone 保护，修 12 代起 Intel CPU 在 Windows 上的批量崩溃 |
| v0.19.0 | 2026-10-02 | The Shadoween special | 信号仿真再次重写；支持从 RIF 许可证加载 entitlements；DLC 以 ZAR 格式加载；vdec2 支持 H.265/HEVC；大量 GPU 修复，「一些游戏真的可以通关了」 |

两个细节能看出这个社区的气质。一是版本代号都很随意——「垃圾清运工特别版」「旺达与人偶」——跟工程内容的严肃程度形成反差。二是 v0.18 里有一个跨项目协作的注脚：解锁 AvPlayer LLE 的关键（在 LLE LibcInternal 启动时调用 `sceLibcInternalMemoryMutexEnable`）是另一个 PS4 模拟器 ChonkyStation4 的开发者 liuk7071 找到的，release notes 署名致谢。

## 技术底盘：C++ 从零写，站在四个项目的肩膀上

shadPS4 的技术路线有两个要点。一是 CPU 侧不走翻译路线：PS4 的游戏代码本身就是 x86-64，模拟器做的是在宿主机上原生执行这些代码，难点转移到内存布局、信号量和系统调用的仿真上——v0.19 「信号仿真再次重写」就是在补这块的精度。二是 GPU 侧把主机的 GNM 调用翻译成 Vulkan，着色器编译器以 yuzu 的 Hades 编译器为蓝图设计，让团队可以专心对付「模拟一颗现代 AMD GPU」这个难题。

README 的特别鸣谢一节，实际上是这个项目的技术谱系表：

- **Panda3DS**：同作者 wheremyfoodat 的 3DS 模拟器，在「原生执行 PS4 二进制的 x64 代码」上帮了大忙；
- **fpPS4**：另一个 PS4 模拟器团队，协助逆向 PS4 操作系统和库的复杂部分；
- **yuzu**：着色器编译器的蓝图来源；
- **felix86**：x86-64 到 RISC-V 的 Linux 用户态模拟器；
- **emudev.org**：硬件文档与逆向工程社区， shadPS4 核心成员 shadow 也是成员。

macOS 这条线的演化最直观地体现了「驱动也是模拟器的一部分」。本文发表时，macOS 构建文档只要求 Xcode 16+ 和两套 Homebrew（ARM 原生套装装工具、x86_64 套装装库）；v0.17 之后，官方改用 Mesa 里的 KosmicKrisp——一个面向 Apple Silicon 的 Vulkan 驱动，构建文档相应变成了一串新依赖（meson、ninja、pkg-config、llvm、spirv-tools、spirv-llvm-translator、libclc，再加 pip 装 mako/packaging/pyyaml）。不想自建驱动的话，配置时加 `-DENABLE_SYSTEM_VULKAN=ON` 可以跳过，但前提是你自己装好了兼容的 Vulkan 环境。

对调着色器渲染问题的开发者，documents/patching-shader.md 记录了一条完整的补丁工作流：配置打开 `dumpShaders` 抓出 SPIR-V，用 `spirv-cross` 反编译成 GLSL 手工修改，再用 `glslc` 编译回 SPIR-V 放进 `shader/patch` 目录，打开 `patchShaders` 生效——不重编译模拟器就能验证一个着色器假设。

源码目录也值得扫一眼：`src/` 是核心模拟器，`cmake/`、`externals/`（子模块形式的外部依赖）、`documents/`（构建、调试、补丁文档）、`tests/`、`scripts/`、`LICENSES/`。本文初版列出的 `dist/` 目录已在近期版本中移除，构建产物走 CMake 的 build 目录。

## 构建指南：四平台的真实门槛

初版文章在这里错得最离谱：写的是「Visual Studio 2019 或更高版本、CMake 3.20+、Python 3.8+、Vulkan SDK」。实际上项目在本文发表之前就要求 **Visual Studio 2022 加装 Clang 组件**，编译器是 Clang 19——官方的理由写得很直白：「CI 的代码格式化用的是 clang19」。以下全部以 2026-10-04 的构建文档为准。

### Windows

两条路线，任选其一：

- **Visual Studio 2022**：安装时勾选 Desktop development with C++，再到 Individual Components 里补装 C++ Clang Compiler for Windows 和 MSBuild support for LLVM 两项，然后直接用 VS 打开源码目录构建。产物在 `Build\x64-Clang-Release\`。
- **VSCode + Build Tools**：装 Git for Windows、LLVM 19.1.1、CMake 4.2.3 及以上、Ninja 1.13.2 及以上，再装 Visual Studio Build Tools（只要 MSVC 与 Windows SDK 组件，不需要 IDE）。

注意 **ARM64 不支持**——文档原话是「编不过也跑不起来」，相关说明仅供开发者参考。另外想编译旧版本测试的话，`git clone` 不要带 `--depth 1`，否则历史被裁掉。

### Linux

Clang 19 是推荐编译器（官方 Linux 构建和 CI 都用它），GCC 14 也在 CI 测试范围，但用 GCC 构建出问题时，请先用 Clang 建一次再报 `[APP BUG]`。Ubuntu 24.04 的默认 clang 包还是 18，要先加 apt.llvm.org 的 LLVM 19 源。完整依赖比很多教程写的长得多，这是 Debian/Ubuntu 的官方清单：

```bash
sudo apt install build-essential clang-19 git cmake libasound2-dev \
    libpulse-dev libopenal-dev libssl-dev zlib1g-dev libedit-dev \
    libudev-dev libevdev-dev libsdl2-dev libjack-dev libsndio-dev \
    libvulkan-dev vulkan-validationlayers libpng-dev
```

缺了 SDL2、ALSA、PulseAudio 这些音频输入依赖，配置阶段就过不去。Fedora、Arch、OpenSUSE 的对应命令在 building-linux.md 里都有现成清单。两个额外的路标：AUR 上的 `shadps4-git` 包非官方维护且默认 GCC 编译，用不用自己掂量；Immutable 发行版（Fedora Kinoite、SteamOS）推荐用 distrobox 开个 Arch 容器在容器里构建。NixOS 用户直接用仓库自带的 flake：`nix build .?submodules=1#linux.release`。

### macOS

Xcode 26.0 或更新版本是硬门槛（本文发表时还是 Xcode 16+，且官方口径为「macOS 15.4+，Intel Mac 有严重 bug」；现在 README 明确写成 **macOS 26.0+，Intel Mac 不再支持**）。构建走 Homebrew + Clang + CMake，KosmicKrisp 驱动的依赖清单见上一节；生成构建目录时固定 x86_64 架构：

```bash
git clone --recursive https://github.com/shadps4-emu/shadPS4.git
cd shadPS4
cmake -S . -B build/ -DCMAKE_OSX_ARCHITECTURES=x86_64
cmake --build build/ --parallel$(sysctl -n hw.ncpu)
```

### Docker

不想配本地环境，documents/building-docker.md 给了 Docker + VSCode 的容器化构建流程，保持 IDE 开发体验不变。

## 跑起来：固件、命令行与 QtLauncher

无论核心还是 QtLauncher，跑游戏都绕不开固件。shadPS4 以 LLE（低层模拟）方式加载一部分 PS4 系统模块，它们必须从你合法拥有的 PS4 主机上 dump 出来，放进模拟器的 `sys_modules` 目录。支持清单半年内从 15 个扩到 **34 个**——扩容的直接原因就是 v0.18 把 AvPlayer 改成了 LLE 加载，视频播放需要真实的 `libSceAvPlayer.sprx` 和 `libSceAvPlayerStreaming.sprx`。以下为 2026-10-04 的完整清单：

| 模块 | 模块 | 模块 | 模块 |
|------|------|------|------|
| libSceAt9Enc.sprx | libSceAudiodec.sprx | libSceAudiodecCpu.sprx | libSceAudiodecCpuDdp.sprx |
| libSceAudiodecCpuDtsHdLbr.sprx | libSceAudiodecCpuHevag.sprx | libSceAudiodecCpuM4aac.sprx | libSceAvPlayer.sprx |
| libSceAvPlayerStreaming.sprx | libSceBeisobmf.sprx | libSceBemp2sys.sprx | libSceCesCs.sprx |
| libSceFont.sprx | libSceFontFt.sprx | libSceFreeTypeOl.sprx | libSceFreeTypeOptOl.sprx |
| libSceFreeTypeOt.sprx | libSceJpegDec.sprx | libSceJpegEnc.sprx | libSceJson.sprx |
| libSceJson2.sprx | libSceLibcInternal.sprx | libSceNgs2.sprx | libScePngEnc.sprx |
| libScePsmKitSystem.sprx | libSceRtc.sprx | libSceRudp.sprx | libSceSystemGesture.sprx |
| libSceUlt.sprx | libSceWkFontConfig.sprx | libSceXml.sprx | libSceDepth.sprx |
| libScePadTracker.sprx | libSceMoveTracker.sprx | | |

用核心直接启动时，命令行参数不多，日常就这几条模式（README 原样）：

```bash
shadPS4 CUSA00001 # 在游戏安装目录列表里找 CUSA00001 并启动
shadPS4 --fullscreen true --config-clean CUSA00001    # 游戏参数始终放在最后
shadPS4 -g CUSA00001 --fullscreen true --config-clean # 除非手动指定，否则见上一条
shadPS4 /path/to/game.elf # 直接启动 PS4 ELF 文件，适合启动不叫 eboot.bin 的可执行文件
shadPS4 CUSA00001 -- -flag1 -flag2 # 把参数透传给游戏可执行文件的 argv
```

全部参数看 `shadPS4 --help`。普通用户则装 QtLauncher：从它的 releases 页下载对应平台的构建产物，解压即用——主仓库的每日 pre-release 与 QtLauncher 的构建是配套的。

游戏跑起来之后，这几个全局快捷键值得记住（部分键盘需按住 Fn）：

| 按键 | 功能 |
|------|------|
| F10 | FPS 计数器 |
| Ctrl+F10 | 视频调试信息 |
| F11 | 全屏切换 |
| F12 | RenderDoc 捕获（RenderDoc 不可用时退化为仅游戏画面截图） |
| Alt+F12 | 含 HUD/对话框叠加层的完整截图 |

Alt+F12 这一档是本文发表当天（2026-04-12，PR #4248）才合入的截图功能：RenderDoc 关闭时，F12 抓纯游戏画面、Alt+F12 连模拟器 HUD 一起抓；RenderDoc 开启时，F12 仍是 RenderDoc 抓帧。Mac 用户注意：用 Command 替代 Control，进全屏用 Command+F11 避免与系统快捷键冲突。

手柄开箱即用（Xbox 和 DualShock 均可），键盘默认映射如下，可在 QtLauncher 设置里按游戏自定义，每个绑定最多三个按键，也支持鼠标按钮和鼠标移动映射到摇杆：

| 手柄按钮 | 键盘映射 | 手柄按钮 | 键盘映射 |
|----------|----------|----------|----------|
| LEFT AXIS UP / DOWN | W / S | OPTIONS | RETURN |
| LEFT AXIS LEFT / RIGHT | A / D | BACK / TOUCH PAD | SPACE |
| RIGHT AXIS UP / DOWN | I / K | L1 / R1 | Q / U |
| RIGHT AXIS LEFT / RIGHT | J / L | L2 / R2 | E / O |
| TRIANGLE | Numpad 8 或 C | L3 / R3 | X / M |
| CIRCLE | Numpad 6 或 B | PAD UP / DOWN | UP / DOWN |
| CROSS | Numpad 2 或 N | PAD LEFT / RIGHT | LEFT / RIGHT |
| SQUARE | Numpad 4 或 V | | |

## 调试与报告：把「不工作」变成有效情报

模拟器项目的生死线在社区纪律上，shadPS4 把这件事拆成了两层。

第一层是开发者调试。documents/Debugging/Debugging.md 覆盖了 RenderDoc 抓帧（Linux 下 Wayland 不可用，要以 `SDL_VIDEODRIVER=x11` 跑）、VS/VSCode 的调试配置、日志分析路径。一条容易踩的规矩写在加粗警告里：**不要把无法在模拟器源码中定位的理论性问题发到模拟器 issue 区**。「Amplitude 启动即崩，access violation」这种只有游戏名的报告是不合格样本；合格样本长这样——「Crash in `Shader::Gcn::CFG::EmitBlocks()`, out of bounds list access」，带栈回溯、指向仓库里的具体代码。拿不准的小问题去 Discord 的 #development 频道先聊。

第二层是面向所有用户的兼容性报告，规则细到近乎苛刻，每条都有明确的理由：

- **只收正式大版本的测试结果**（比如 v0.19.0），每日构建的结果不算数——否则同一个游戏会涌进无数不可复现的报告。
- **报告字段必须齐全**：游戏名、CUSA 编号、游戏版本、模拟器版本、状态、操作系统。同一 CUSA 在同一 OS 下只报一次，状态变化在原 issue 下补评论和新日志。
- **必须原版 dump**：打了补丁或重新打包成 FPKG 的报告直接删除，盗版报告删帖封号。
- **不许改影响游戏行为的设置**：PS4 Neo Mode、Devkit Console Mode、Vblank 频率动过的报告会被关闭；Readbacks 这类允许的实验性设置会打上 experimental 标签方便筛选。
- **日志必须原样**：手工删「重复行」会让日志失去证据力；日志超过 100MB 导致崩溃断言缺失时可以用过滤器，但必须在报告里注明。

兼容性状态分五级，查表之前先弄清口径：

| 标签 | 含义 |
|------|------|
| status-playable | 无重大问题，可以通关 |
| status-ingame | 能进入游戏玩法，但存在崩溃、挂起、贴图损坏、顶点爆炸或音频损坏等破坏性问题 |
| status-menus | 能到菜单，继续推进就冻结或崩溃 |
| status-boots | 有画面或声音输出，但到不了菜单 |
| status-nothing | 启动即崩，或黑屏挂死 |

2026-10-04 的存量是：Playable 384、Ingame 579、Menus 324、Boots 353、Nothing 567。也就是说，六个报告里只有约一个达到「可通关」。招牌游戏《血源》的三个区版（CUSA00900/CUSA03173/CUSA00207）加上《老猎人》版全部停在 Ingame——能进游戏、能战斗，但有破坏性问题等着你。拿它当「模拟器成熟度」的参照系，比看任何宣传视频都准。

## 一份游戏 dump 的完整旅程

把前面的机制串成一条用户路径：假设你有一台可破解的 PS4 和一份合法 dump 的游戏。

1. **装 QtLauncher**，从 releases 下载最新构建，解压运行。
2. **dump 固件模块**，把上表 34 个 `.sprx` 放进 `sys_modules`——这是最容易被跳过、也最容易造成「游戏闪退」的一步，兼容性仓库甚至为此单独立了规矩：先 dump 固件再报告。
3. **添加游戏目录**。游戏可以是解开的文件夹，也可以是 v0.17 之后的 ZArchive 单文件。
4. **查兼容性仓库**，按 CUSA 编号搜索你的游戏，看标签和最新评论——特别留意是不是用正式版本测的。
5. **调设置**。先全默认；确实要动 Readbacks 之类的实验性开关，记得这会让你的报告被贴上 experimental 标签。
6. **运行与取证**。F10 看帧率，Alt+F12 截图，日志保存在默认位置且不要手工编辑。
7. **回传结果**。游戏能玩/不能玩，都去兼容性仓库对应 issue 下补一条带日志的评论——这个项目的兼容性地图，就是这么一格一格填出来的。

## 参与开发

核心团队八人：georgemoralis（创始人）、psucien、viniciuslrangel、roamic、squidbus、frodo、Stephen Miller、kalaposfos13，Logo 出自 Xphalnos。贡献流程不复杂：读 CONTRIBUTING.md，开 PR 即可，仓库的 GitHub Actions 挂着 Build and Release 与 Run Tests 两条流水线，另有 Copilot 做拉取请求的初筛审查。克隆时记得 `--recursive`——外部依赖全走子模块。

## 采用建议：谁现在就该上手，谁再等等

- **现在就可以用**：手上有可 dump 的 PS4、想试《血源》《黑暗之魂 重制版》《荒野大镖客》《如龙 0》《驾驶俱乐部》级别游戏的玩家；愿意接受「玩到一半可能崩」预期的人。README 截图墙上的 Bloodborne、初音未来 Project DIVA、如龙 0、DRIVECLUB 是当前兼容面的直观展示。
- **macOS 用户**：只剩 Apple Silicon 一条路，系统要求 macOS 26.0+，Intel Mac 已被放弃。
- **这三类人建议再等等**：追求「装上就能通联想库」的轻度用户——兼容性列表里 Nothing 和 Ingame 加起来还过半；想玩多人联机的——shadnet 目前只有分数上传和好友系统，官方明说多人游戏还不行；Intel Mac 用户——不再是支持目标。
- **入坑顺序**：先装 QtLauncher 跑现成构建 → 查兼容性列表再试游戏 → 有兴趣再碰源码构建。想深度参与，从复现一个 Ingame 游戏的具体崩溃开始，比从读渲染代码开始更容易找到下手处。

## 资料口径说明

本文初版发布于 2026-04-12，当时读数：30,744 star（Wayback Machine 2026-04-13 快照实拍）、最新版本 v0.15.0、macOS 要求 15.4+。2026-10-04 全面复核并更新：star 33,069、最新正式版本 v0.19.0（每日 pre-release 持续滚动）、macOS 要求 26.0+（Intel 不支持）、固件模块清单 34 项、Linux 推荐编译器 Clang 19、构建文档以当日仓库内容为准。版本发布日期、release notes 引述、兼容性标签与数量均取自 GitHub 公开数据；兼容性数量为开放 issue 的时点读数，会持续变动。固件模块的合法提取方式与各地法律边界请自行确认，本文不展开。
