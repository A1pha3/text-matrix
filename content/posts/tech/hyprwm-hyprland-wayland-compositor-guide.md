---
title: "Hyprland 拆解：甩掉 wlroots 之后，它把底层换成了自己的六个仓库"
date: 2026-07-23T02:50:00+08:00
lastmod: "2026-09-20T00:00:00+08:00"
slug: "hyprwm-hyprland-wayland-compositor-guide"
github_repo: "hyprwm/Hyprland"
source_key: "gh:hyprwm/Hyprland"
description: "对着 hyprwm/Hyprland main 分支逐条核查后拆解它：README 里那句「100% independent」到底排除了什么、又留下了哪六个自家仓库；布局为什么从 IHyprLayout 改叫 algorithm；配置文件怎么从 hyprlang 换到 Lua；插件的 ABI 约束和函数钩子的 x86_64 限制从哪来；以及 391 个配置项、38 条 IPC 命令怎么读。"
draft: false
categories: ["技术笔记"]
tags: ["C++", "Wayland", "Linux 桌面", "架构分析", "开源项目解读"]
---

> **判断**：Hyprland 真正的工程选择不是「自己写一个合成器」，而是「不要 wlroots，但也不要重新发明后端」。它的做法是把后端交给自己的 aquamarine，把工具层交给另外五个 hyprwm 库（hyprutils、hyprlang、hyprcursor、hyprgraphics、hyprwayland-scanner），主仓库只留合成器本体。理解这一点，才能理解它的插件为什么必须同编译器同机器编译、函数钩子为什么只在 x86_64 上可用、以及视觉能力的边界画在哪里。
>
> **读完后能做什么**：说出 Hyprland 的依赖图里哪一层负责什么；判断某个视觉效果是主仓的还是 hyprutils 的；解释配置从 `.conf` 迁到 `.lua` 之后热重载的真实行为；评估在自己那台机器（发行版、显卡、架构）上装它要付什么代价；以及用仓库自带的一手材料复核本文任何一条断言。
>
> **依据**：[hyprwm/Hyprland](https://github.com/hyprwm/Hyprland) `main@83cf6a6`（末次提交 2026-09-19，`VERSION` 写 `0.56.0`），最新 release 为 `v0.56.2`（2026-08-05），GitHub API（应用程序接口）在 2026-09-20 读到 38,601 stars / 2,015 forks / 427 位贡献者 / 117 个 release / BSD-3-Clause。功能清单出自 `README.md`，构建与依赖约束出自 `CMakeLists.txt`，行为按 `src/` 下源码逐条对照，配置项统计自 `src/config/values/ConfigValues.cpp`。官方 wiki 已迁到 `wiki.hypr.land`，本文凡引用 wiki 处均标明页面。文中出现的命令行均为 Linux 侧操作，本文作者的环境是 macOS，未实跑 Hyprland 本体，未实跑的具体范围在 §13 逐条列出。

## 目录

- [§1 先划清三件事：合成器、后端、工具库](#1-先划清三件事合成器后端工具库)
- [§2 「100% independent」排除了什么，留下了什么](#2-100-independent排除了什么留下了什么)
- [§3 渲染主线：动画树、曲线归属与 11 种模糊变体](#3-渲染主线动画树曲线归属与-11-种模糊变体)
- [§4 布局主线：从 IHyprLayout 到 algorithm](#4-布局主线从-ihyprlayout-到-algorithm)
- [§5 配置主线：Lua 接棒 hyprlang，热重载是一个 inotify](#5-配置主线lua-接棒-hyprlang热重载是一个-inotify)
- [§6 插件主线：能改的地方最多，约束也最硬](#6-插件主线能改的地方最多约束也最硬)
- [§7 IPC 与 hyprctl：两个套接字、38 条命令](#7-ipc-与-hyprctl两个套接字38-条命令)
- [§8 任务流案例：按下 SUPER+2 之后](#8-任务流案例按下-super2-之后)
- [§9 常见故障与排查入口](#9-常见故障与排查入口)
- [§10 采用边界：谁现在上，谁再等等](#10-采用边界谁现在上谁再等等)
- [§11 下一步读哪份代码](#11-下一步读哪份代码)
- [§12 六个自测问题](#12-六个自测问题)
- [§13 事实核验与引用](#13-事实核验与引用)

## §1 先划清三件事：合成器、后端、工具库

谈 Hyprland 的架构要把三个容易混在一起的东西分开。第一件是 Wayland 合成器本体，也就是那个持有窗口树、决定谁在哪个位置、把各表面贴成最终画面的进程。第二件是**后端**：怎么打开显示器、怎么拿到 DRM（直接渲染管理）平面、怎么处理输出热插拔和 vsync。第三件是**工具库**：颜色、数学、动画插值、配置语言解析、指针格式。

wlroots 把第二件和第三件打包提供了一个通用实现，Sway、Wayfire、labwc 这一批合成器都直接坐在它上面。Hyprland 的 README 里那句 `100% independent, no wlroots, no libweston, no kwin, no mutter` 说的是它不坐在这四个里的任何一个上面。

| 层 | 谁负责 | 在哪个仓库 | 强制依赖 |
|----|--------|-----------|---------|
| 合成器本体 | 窗口树、工作空间、布局、装饰、渲染通道 | `hyprwm/Hyprland` | 是 |
| 显示与输入后端 | DRM / Wayland 会话、输出、设备事件 | `hyprwm/aquamarine` | `aquamarine>=0.15.0` |
| 动画与内存原语 | `CAnimatedVariable`、曲线、`SP`/`WP`/`UP` 指针 | `hyprwm/hyprutils` | `hyprutils>=0.14.0` |
| 配置语言 | hyprlang 语法解析与 handler | `hyprwm/hyprlang` | `hyprlang>=0.6.7` |
| 指针主题 | hyprcursor 格式与加载 | `hyprwm/hyprcursor` | `hyprcursor>=0.1.7` |
| 颜色与图像资源 | `CColor`、OkLab、图像解码 | `hyprwm/hyprgraphics` | `hyprgraphics>=0.5.1` |
| 协议代码生成 | 从 XML 生成 C++ 绑定 | `hyprwm/hyprwayland-scanner` | `find_package` 要求 0.3.10 |
| 扩展协议定义 | Hyprland 自己的 protocol XML | `hyprwm/hyprland-protocols`（git 子模块） | 否，`>=0.7.0` 可选 |

这张表是本文后面所有结论的地基。它有两个直接后果：Hyprland 的视觉能力上限由它自己的 `src/render/` 决定，但动画的数学精度由 hyprutils 与 hyprgraphics 决定；而 wlroots 的更新节奏确实卡不住它，代价是这六个仓库任何一个的 ABI（二进制接口）变化都要跟着动。

## §2 「100% independent」排除了什么，留下了什么

`CMakeLists.txt` 是最诚实的一手材料。逐条读下来，排除的是 wlroots 这个具体项目，留下的依赖清单反而比一个基于 wlroots 的合成器更长。

必需包（`pkg_check_modules(... REQUIRED ...)`）里属于 hyprwm 的有五个：aquamarine、hyprlang、hyprcursor、hyprutils、hyprgraphics。第六个 hyprwayland-scanner 走 `find_package(hyprwayland-scanner 0.3.10 REQUIRED)`。剩下的都是公共基础设施：`wayland-server>=1.22.91`、`wayland-protocols>=1.49`、`libinput>=1.29`、`xkbcommon>=1.11.0`、`gbm`、`libdrm`、`cairo`、`pango`、`pangocairo`、`pixman-1`、`lcms2`、`re2`、`muparser`、`gio-2.0`、`libcanberra`、`libeis-1.0`、`uuid`、`xcursor`。另有 `pkg_search_module(LUA REQUIRED ... lua>=5.5 lua<5.6)` 把 Lua 解释器钉死在 5.5 这条线上，`muparser`、`re2`、`glaze`（v7.2.0，JSON 读写）各占一个具体职责。语言标准写死在 `set(CMAKE_CXX_STANDARD 26)`，CMake 下限 3.30。

三个第三方依赖值得单独说，因为它们直接暴露了这套系统的能力边界：

- **aquamarine**（471 stars，BSD-3-Clause）自述是 "a very light linux rendering backend library"（一个很轻的 Linux 渲染后端库），给应用提供两套后端抽象：跑在一个 Wayland 会话的窗口里（也就是嵌套），或者跑在原生 DRM 会话上。同一个 README 还声明与渲染 API 无关（Vulkan 或 OpenGL）、不提供其他语言的绑定、只支持 C++。所谓「不依赖 wlroots」，实际是把后端换成了 hyprwm 自己的这个更薄的库。
- **udis86**（git 子模块，x86 反汇编器）在主仓库里只有一个使用点：`src/plugins/HookSystem.cpp` 的 33、34、41 行，`ud_init` 之后紧跟 `ud_set_mode(&udis, 64)` 与 AT&T 语法输出。一个反汇编器出现在 Wayland 合成器的依赖表里并不奇怪：函数钩子要先知道被覆盖的那条指令有多长，才能安全地盖一个跳转过去。
- **tracy**（git 子模块，性能分析器）只在 `USE_TRACY` 打开时把 `subprojects/tracy/public/TracyClient.cpp` 加进编译。

主仓库自己的体量：`src/` 下 434 个 `.cpp` 与 479 个 `.hpp`，合计 135,376 行；`src/protocols/` 有 64 个协议实现文件；`src/render/shaders/glsl/` 有 52 个文件（32 个 `.frag`、16 个 `.glsl`、2 个 `.vert`、2 个头文件）；`tests/` 下 53 个 `.cpp` 单元测试，集成测试另放在 `hyprtester/`。GitHub 语言统计里 C++ 占 6,495,045 字节，GLSL 136,336，Lua 30,837——最后这个数字在 §5 会解释它为什么存在。

README 的 "Easily expandable and readable codebase" 这句自我评价，能核对到的客观部分是仓库根的 `AGENTS.md`：类名 `CMyClass`、结构体 `SMyStruct`、接口 `IMyInterface`、成员 `m_variable`；内存一律用 hyprutils 的 `SP<>`/`WP<>`/`UP<>`，转换一律用 `rc<>`/`sc<>`/`cc<>`；禁止 `using namespace std;`（把整个标准命名空间灌进当前作用域）；禁止留未初始化的基础类型；单行 if/else 不写花括号。这套约定由 `.clang-format`、`.clang-tidy` 和 13 个 GitHub workflow 兜住。至于是不是真的「好读」，只能自己下去看一遍，这不是一个可以引用的事实。

## §3 渲染主线：动画树、曲线归属与 11 种模糊变体

先给一个准确的定位：**动画变量的实现不在主仓库，在 hyprutils**。`src/helpers/AnimatedVariable.hpp:69` 只有一行别名：

```cpp
using CAnimatedVariable = Hyprutils::Animation::CGenericAnimatedVariable<VarType, SAnimationContext>;
```

主仓库负责的是给这些变量喂曲线、决定谁在动、以及每帧把值刷进纹理。三件事各自的落点：

- 曲线管理：`src/animation/AnimationManager.cpp`。构造函数里唯一一次 `addBezierWithName` 调用注册的是 `linear`，即 `Vector2D(0.0, 0.0)` 到 `Vector2D(1.0, 1.0)` 这条对角线；其余命名曲线全部由配置提供。弹簧曲线类型是 `Hyprutils::Animation::SSpringCurve`，通过 `addSpringWithName` 注册。所以「贝塞尔加弹簧」是两种曲线形状，不是两套系统。
- 分帧：`CHyprAnimationManager` 建了一个 500 微秒的事件循环定时器（`std::chrono::microseconds(500)`）驱动 `frameTick()`。
- 归属：`src/config/shared/animation/AnimationTree.cpp` 的 `setConfigForNode(name, enabled, speed, bezier, style)` 把一条配置打进动画树的一个节点。动画的层级是一棵树。`AnimationTree.cpp` 的 `reset()` 建两类节点：根上的 `global` 与 `__internal_fadeCTM`，然后挂在 `global` 下面的 `windows`、`layers`、`fade`、`border`、`borderangle`、`shadowangle`、`glowangle`、`workspaces`、`zoomFactor`、`monitorAdded`。再往下才是真正取配置的叶子：`windowsIn`、`windowsOut`、`windowsMove`、`layersIn`、`layersOut`、`fadeIn`、`fadeOut`、`fadeSwitch`、`fadeShadow`、`fadeGlow`、`fadeDim` 等。所以给 `windows` 配一条动画等于给它三个子节点同时配，想单独管进场就写 `windowsIn`。完整清单见 wiki 的 [Animations 页](https://wiki.hypr.land/configuring/core/animations/)。

颜色动画有一个值得单独写的取舍。`AnimationManager.cpp` 里的 `updateColorVariable` 不走 RGB 线性插值，而是把首末色都转成 OkLab 再逐通道 `std::lerp`，原注释是 "This is not as fast as just lerping rgb, but it's WAY more precise"。RGB 插值经过灰色时的亮度塌陷，在边框和发光这种大跨度变色场景里肉眼看得见，OkLab 分支就是用一点算力换掉这个瑕疵。

三种视觉效果的分工也分得很开，`src/render/` 下三个子目录各管一段：

```text
src/render/decorations/    边框、投影、分组条、内发光，外加 AnimatedDecorationGradient 让渐变随时间走
src/render/transformer/    两个内置变换器：MotionBlurTransformer 与 WobbleTransformer
src/render/shaders/glsl/   52 个文件，其中一批以 *finish.frag 命名，对应下面那张模糊变体表
```

README 里 "many types of blur" 这句含糊话，在源码里是一个精确枚举。`src/config/values/ConfigValues.cpp:239` 起，`decoration:blur:variant` 默认 0，取值 0 到 10：

| 编号 | 名称 | 编号 | 名称 |
|------|------|------|------|
| 0 | `kawase`（默认） | 6 | `prism` |
| 1 | `frost` | 7 | `heat_shimmer` |
| 2 | `ripple` | 8 | `acrylic` |
| 3 | `drops` | 9 | `aurora` |
| 4 | `water` | 10 | `haze` |
| 5 | `fluid_jar` | | |

选项自己的描述就是一句成本警告："Blur variants enhance regular blur, but may increase GPU and CPU usage, significantly so if they are animated."。三个带动画的变体键——`decoration:blur:aurora:speed`、`decoration:blur:drops:speed`、`decoration:blur:heat_shimmer:speed`——描述里都另外写明了打开动画会涨 GPU 占用。基础模糊参数是 `size` 8（0 到 100）、`passes` 1（0 到 10）、`noise` 0.0117、`contrast` 0.8916、`vibrancy` 0.1696。

每种变体又带自己的参数，默认值都写在同一个文件里：`acrylic` 的 `refraction` 24、`bulb` 48、`clarity` 0.82、`aberration` 0.025、`tint` 0x14EEF5FF；`ripple` 的 `strength` 30、`radius` 400、`width` 32、`duration` 0.45 秒；`fluid_jar` 的 `speed` 3.7、`fill_amount` 0.5、`mass` 1.4、`precision` 2，描述里作者顺手写了一句 "4x is expensive. 8x is extreme and unnecessary"。窗口抖动的弹簧参数是 `decoration:wobble:stiffness` 200、`damping` 12、`mass` 1。

自适应渲染（不脏就不出帧）在 main 上的键名是 `debug:vfr`，默认 true。它的描述只有一句："controls the VFR status of Hyprland. Do not turn off unless debugging"（VFR 即可变刷新率）。也就是说这已经是一个调试开关，不再是调优旋钮。wiki 的 config-options 页同样把它归在 Debug 一组，但推荐语是 "Heavily recommended to leave enabled to conserve resources"，与源码里那句「别关，除非调试」的分寸不同。键名与推荐语都会随版本漂移，别信任何一篇文章包括本文给你的值，信 `hyprctl deprecated-config`，见 §7。

## §4 布局主线：从 IHyprLayout 到 algorithm

`src/layout/` 现在的文件树会误导还在按旧文档找东西的人。目录里没有 `DwindleLayout.cpp`，也没有 `IHyprLayout.hpp`，而是：

```text
src/layout/LayoutManager.{cpp,hpp}
src/layout/algorithm/{Algorithm, FloatingAlgorithm, ModeAlgorithm, TiledAlgorithm}
src/layout/algorithm/floating/default/DefaultFloatingAlgorithm
src/layout/algorithm/tiled/{dwindle, master, monocle, scrolling}
src/layout/space/Space
src/layout/target/{Target, WindowTarget, WindowGroupTarget}
src/layout/supplementary/{DragController, WorkspaceAlgoMatcher}
```

平铺和浮动被拆成了两个并列的抽象（`ITiledAlgorithm` 与 `IFloatingAlgorithm`），一个窗口在平铺算法之上还可以叠一层浮动算法。`space/` 管几何划分，`target/` 管「这次操作作用在谁身上」。`supplementary/` 放两件东西：`WorkspaceAlgoMatcher` 对应 README 的 Per Workspace Layouts（按工作空间指定算法），`DragController` 管拖拽落点。发布说明也跟着改了口径，v0.56.0 里的条目前缀写作 `algo/dwindle`、`algo/master`、`algo/scrolling`。

内置平铺算法四个：dwindle（BSP 式二叉树）、master（主从）、scrolling（横向滚动带）、monocle（单窗铺满）。配置前缀的分布很能说明资源投在哪：`master:` 14 项、`dwindle:` 11 项、`scrolling:` 9 项、`monocle:` **0 项**。monocle 没有可配项，它就是一个铺满。

再往上还有第五、第六种来源，都走同一套注册口：

1. **Lua 布局**：仓库自带四份示例，`example/layouts/` 下的 `columns.lua`、`grid.lua`、`manual.lua`、`spiral.lua`。wiki 的 custom-layouts 页给出的注册形式是 `hl.layout.register(name, { recalculate, layout_msg? })`，之后以 `lua:columns` 这样的名字引用。
2. **插件布局**：`src/plugins/PluginAPI.hpp:216-217` 提供 `addTiledAlgo` 与 `addFloatingAlgo`，两者都收一个 `std::function<UP<...>()>` 工厂加一个 `std::type_info*`。

版本边界要说清楚：`addLayout` 在同一个文件里第 202 行，已经标了 `[[deprecated]]`，上面注释直接写 "deprecated: addTiledAlgo, addFloatingAlgo"。所以「插件可以加自定义布局」这件事在旧版本走 `IHyprLayout*`、在新版本走算法工厂，不是两条并存的路线。判断某个 API 在你这个版本还在不在，最省事的是读装在你机器上的那份头文件：`CMakeLists.txt` 把 `src/**` 的头随 `hyprland.pc` 一起装进 include 目录，插件的 include 路径写作 `<hyprland/src/plugins/PluginAPI.hpp>`。

## §5 配置主线：Lua 接棒 hyprlang，热重载是一个 inotify

这一层是 Hyprland 最近一年变化最大的地方。仓库里已经没有 `example/hyprland.conf`，取而代之的是 `example/hyprland.lua`。第 18 到 23 行原样是：

```lua
hl.monitor({
    output   = "",
    mode     = "preferred",
    position = "auto",
    scale    = "auto",
})
```

第 43 到 49 行是一段注释掉的自启动示例，它比任何说明都能体现新配置的形状：

```lua
-- Or execute your favorite apps at launch like this:
--
-- hl.on("hyprland.start", function () 
--   hl.exec_cmd(terminal)
--   hl.exec_cmd("nm-applet")
--   hl.exec_cmd("waybar & hyprpaper & firefox")
-- end)
```

环境变量则在第 58、59 行，写成 `hl.env("XCURSOR_SIZE", "24")` 这样的一对调用。

注释里那句 "You can (and should!!) split this configuration into multiple files" 指的是 `require("myColors")`——拆分文件靠 Lua 自己的模块机制，不靠专用 include 语法。wiki 的 [core 配置页](https://wiki.hypr.land/configuring/core/)写明配置文件是 `$XDG_CONFIG_HOME/hypr/hyprland.lua`。§3 那些选项在这里写成嵌套表：`hl.config({ category = { option = value } })`。

`src/config/lua/` 是这套东西的实现，`objects/` 下 12 个对象类型把合成器状态直接暴露给配置：`LuaWindow`、`LuaWorkspace`、`LuaMonitor`、`LuaGroup`、`LuaLayerSurface`、`LuaKeybind`、`LuaWindowRule`、`LuaLayerRule`、`LuaWorkspaceRule`、`LuaEventSubscription`、`LuaTimer`、`LuaNotification`。同一目录里还有 `layout/`（对应 §4 的 Lua 布局）、`Emergency.hpp` 和 `DefaultConfig.hpp`。反过来，§1 那个 30,837 字节的 Lua 统计并不来自这里：全仓库的 `.lua` 文件加起来正好这个数，其中 `example/` 占 18,197（四份布局示例加主示例配置），`hyprtester/` 占 12,640（集成测试脚本），`src/` 下**一个 `.lua` 也没有**。GitHub 按扩展名归类，很容易让人以为合成器里跑着一坨脚本；实际上这套 Lua 能力全部由 C++ 通过 Lua 5.5 的 C API 实现。

**hyprlang 没有退出构建，但已经退出配置入口。** `CMakeLists.txt:152` 仍把 `hyprlang>=0.6.7` 列为 REQUIRED，`src/config/ConfigValue.hpp` 里 `Hyprlang::INT`、`FLOAT`、`STRING`、`CUSTOMTYPE` 依然是配置值的内部类型，`decoration:blur:variant` 这种 `分类:子:键` 也仍然是内部真名。可往回看入口就只剩一条：`src/config/ConfigManager.cpp` 的两个分支都构造 `Lua::CConfigManager`，`ConfigManager.hpp:26-28` 的 `eConfigManagerType` 枚举里只有 `CONFIG_LUA` 一个成员，负责找路径的 `src/config/supplementary/jeremy/Jeremy.cpp:35` 只按 `findConfig("hyprland", "lua")` 查（调试构建查 `hyprlandd`）。

wiki 的 using-hyprctl 页还写着 `hyprctl reload full-reset` 用于 "switching to/from Lua/hyprlang"，但 `Commands.cpp:1237-1250` 里这个分支做的只有四件事：重置配置管理器、清缓存路径、重新 init、刷一遍 `CConfigValueBase` 缓存，没有任何按语言分叉的代码。这一句目前是文档在替实现说话，别拿它规划迁移。

热重载的行为在 `src/config/shared/inotify/ConfigWatcher.cpp`，逐条读下来有四点是实际会碰到的：

```cpp
const uint32_t  fileMask      = IN_CLOSE_WRITE | IN_DONT_FOLLOW;
const uint32_t  directoryMask = fileMask | IN_CREATE | IN_DELETE | IN_MOVED_TO | IN_MOVED_FROM;
const uint32_t  mask          = isDirectory ? directoryMask : fileMask;
```

1. 文件监听的是 `IN_CLOSE_WRITE`，也就是**关闭写入才触发**，不是内容一改就重读。编辑器边写边同步的中间状态不会造成半成品重载。
2. 目录监听额外加 `IN_CREATE | IN_DELETE | IN_MOVED_TO | IN_MOVED_FROM`。
3. `IN_DONT_FOLLOW` 加上一段显式的符号链接处理：如果路径本身是符号链接，就对 `canonical()` 后的真实路径再挂一个 `IN_CLOSE_WRITE` 监听。用 `stow` 或手写软链把配置放进 `~/.config/hypr/` 的人，这里是它能工作的原因。
4. 任何一次触发之后，全部 watch 先清空再按当前配置路径重建。原注释解释了动机：既然分不清是哪一个 fired，重建一次的成本又低。

`misc:disable_autoreload` 默认 false，它挂了一个 `REFRESH_CONFIG_WATCHER` 刷新位。这带出配置生效的分级。写盘触发重载只是第一级；重载之后，大部分值直接生效，另一部分要靠 `REFRESH_*` 标记去通知具体使用者。派发工作由 `src/config/supplementary/propRefresher/PropRefresher.cpp` 承担：`REFRESH_BLUR_FB` 重建模糊帧缓冲，`REFRESH_MONITOR_STATES` 重排显示器，`REFRESH_CONFIG_WATCHER` 重建监听列表。所以「改了没反应」还有第三种可能：重载确实跑了，只是这一项要走 `REFRESH_*` 才落到使用者手里，而那一步没发生。

## §6 插件主线：能改的地方最多，约束也最硬

`src/plugins/` 只有六个文件、1,688 行；三个 `.cpp` 合起来 1,137 行（`PluginAPI.cpp` 458、`HookSystem.cpp` 408、`PluginSystem.cpp` 271），三个 `.hpp` 合计 551 行。它的头注释把最重要的约束写在了第一屏：

```cpp
#define HYPRLAND_API_VERSION "0.1"
```

> The Hyprland API passes C++ objects over, so no ABI compatibility is guaranteed.
> Make sure to compile your plugins with the same compiler as Hyprland, and ideally,
> on the same machine.

这一句解释了很多人的实际故障：插件不是「装上就能跑」的扩展包，它是以 Hyprland 自身编译期布局运行在自己进程里的本机代码。头注释还警告 `pluginInit` 是同步调用的，任何阻塞调用都会卡住合成器，并举了 `system("hyprctl ...")` 这种自锁写法为例。

插件侧要实现三个导出符号：`pluginAPIVersion`（必需）、`pluginInit`（必需，返回 `PLUGIN_DESCRIPTION_INFO{name, description, author, version}`）、`pluginExit`（可选，出错卸载时不会被调用）。`pluginAPIVersion` 的作用在注释里写着 "In case of a version mismatch, will eject the .so"。wiki 的开发页补充了失败时的具体字样——"Mismatched headers! Can't proceed."——目的是把版本错配带来的随机崩溃挡在加载阶段。

API 本身在快速移动。`PluginAPI.hpp` 里挂着 9 处 `[[deprecated]]`：`addConfigValue`、`addConfigKeyword`、`getConfigValue`、`registerCallbackDynamic`、`unregisterCallback`、`addLayout`、`removeLayout`、`getFunctionAddressFromSignature`、`addDispatcher`。替代方向要逐个看：配置值走 V2 接口，`registerCallbackDynamic` 的注释指向 `Event::bus()`，`unregisterCallback` 只说 "just reset the pointer you received with registerCallbackDynamic"，布局那两个指向 §4 的算法工厂。写或读插件时以本机 `HyprlandAPI.hpp` 为准，不要照抄网上的旧例子。

函数钩子（拦截并重写合成器内部函数）是唯一带架构限制的一条。`HookSystem.cpp` 用 udis86 反汇编目标指令求长度，第 31 到 49 行是 `ud_init` / `ud_set_mode(&udis, 64)` / `ud_disassemble`；紧接着第 147 行和第 251 行各有一处：

```cpp
#if !defined(__x86_64__)
    return false;
#endif
```

两处守卫分别落在 `CFunctionHook::hook()`（143 行起）和 `unhook()`（249 行起）。也就是说在 x86_64 之外的平台上，函数钩子既不崩也不报日志，直接返回失败；某个插件因此掉多少能力，取决于它到底用钩子做了什么，本文不估这个比例。事件钩子与布局注册不走这条路，不受此限。

装载与分发是 `hyprpm`，它跟主仓打包在一起（`hyprpm/` 目录，自带 bash / fish / zsh 补全脚本）。wiki 的 using-plugins 页给出的流程是 `hyprpm add <仓库>`、`hyprpm list`、`hyprpm enable/disable <名>`、`hyprpm reload`、`hyprpm update`，编译需要 `cpio, cmake, git, meson and gcc`。不走 hyprpm 也可以 `hyprctl plugin load <绝对路径>`，wiki 特意强调 "Path has to be absolute!"。插件自己的配置值必须落在 `plugin:` 命名空间里，`PluginAPI.hpp` 的注释原话是 "All config values MUST be in the plugin: namespace"。这也解释了 §5 的选项统计里为什么没有 `plugin:` 前缀：那些键由插件在运行时注册，编译期枚举里不存在。

## §7 IPC 与 hyprctl：两个套接字、38 条命令

两个 Unix 域套接字的路径都在源码里拼，两行就够：

```cpp
// src/ipc/s1/Unix.cpp:242
m_socketPath = std::format("{}/.socket.sock", g_pCompositor->m_instancePath);
// src/ipc/s2/Unix.cpp:93
const auto PATH = std::format("{}/.socket2.sock", g_pCompositor->m_instancePath);
```

`m_instancePath` 是 `$XDG_RUNTIME_DIR/hypr/<实例签名>`，签名在 `src/Compositor.cpp:211` 生成：`{GIT_COMMIT_HASH}_{std::time(nullptr)}_{随机数}`，随机数来自 `uniform_int_distribution(0, INT32_MAX)`，随后 `setenv` 成 `HYPRLAND_INSTANCE_SIGNATURE`。签名里带上提交哈希不是恶趣味——它让「哪个实例是哪个二进制起的」在事后仍然可查。若 `$XDG_RUNTIME_DIR` 不以 `/run/user` 开头，日志会打一条 "looks non-standard" 警告但继续跑（`Compositor.cpp:204`）。

两个套接字分工明确。`s1` 是请求应答：`SRequest` 里带 `command`、`format`（`FORMAT_NORMAL` 或 `FORMAT_JSON`）、`refresh`、`all`、`includeConfig`、`follow`、`pid` 七个字段，`SResponse` 允许返回字符串，也允许返回一个 `SP<CPromise<std::string>>` 异步兑现，回复模式只有 `REPLY_MODE_CLOSE` 与 `REPLY_MODE_FOLLOW` 两种。`rollinglog` 就用后者把日志流推给客户端。`s2` 是单向事件广播，`SEvent{event, data}`，每个客户端一条写队列，`flush()` 处理半包（记 `m_writeOffset`，`EAGAIN` 就等下一轮）。wiki 的 [IPC 页](https://wiki.hypr.land/ipc/)给的事件线格式是 `EVENT>>DATA\n`，例 `workspace>>2`。

`src/ipc/s1/Commands.cpp` 里 `registerCommand` 共 38 处，匹配方式只有精确与前缀两种。信息类命令：`workspaces`、`workspacerules`、`activeworkspace`、`clients`、`activewindow`、`layers`、`version`、`devices`、`splash`、`cursorpos`、`binds`、`globalshortcuts`、`systeminfo`、`animations`、`submap`、`status`、`locked`、`descriptions`、`configerrors`、`deprecated-config`、`decorations`、`monitors`。动作类：`dispatch`、`reload`、`reloadshaders`、`kill`、`output`、`setcursor`、`getoption`、`getprop`、`seterror`、`switchxkblayout`、`notify`、`dismissnotify`、`plugin`、`eval`、`repl`、`rollinglog`。

命令行侧的旗标写在 `hyprctl/hyprctl.usage`（一个喂给 complgen 生成三种 shell 补全的语法文件）：`-i | --instance`、`-j`（JSON）、`-r`（下发命令后刷新状态）、`--batch`（分号分隔多条）、`-q | --quiet`。

对读者最有用的三条，恰好也都是排查入口：

```bash
# 只看配置有没有错，不启动合成器
Hyprland --verify-config

# 列出当前配置里已废弃的选项，全干净时输出 "all good!"
hyprctl deprecated-config

# 结构化取状态，交给 jq 或脚本
hyprctl -j monitors | jq -r '.[].description'
```

`--verify-config` 在 `src/main.cpp:39` 的 usage 文本里，注意它没有出现在 `docs/Hyprland.1.rst`——man 页只列了 `-h`、`-c`、`--socket`（指定 Wayland 套接字名）、`--wayland-fd` 四条，落后于实现。同理 `--safe-mode`、`--systeminfo`、`--version-json`、`--locked-cmd`、`--i-am-really-stupid`（跳过 root 检查）都只在代码里。以 `Hyprland --help` 为准，别以 man 页为准。

## §8 任务流案例：按下 SUPER+2 之后

抽象机制在一次真实按键里怎么配合，逐步标注落点。除第 3 步的动作解析层只确认了目录与入口之外，其余各步的落点都按行读过。

1. **键盘事件进入合成器**：`src/managers/input/InputManager.cpp:1721`，`passEvent = Keybinds::mgr()->onKeyEvent(event, pKeyboard) && !PROTO::inputCapture->isCaptured()`。紧接着第 1727 行是 `if (!passEvent) return;`——语义要读反一面：`onKeyEvent` 返回 false 才表示绑定吃掉了这次按键、不再转发给聚焦窗口，返回 true 是放行。同一行上面还有一支 `passEvent = DISALLOWACTION && ...`，会话不允许动作时直接放行。
2. **按键解析**：`src/keybinds/Manager.cpp:190` 的 `CKeybindManager::onKeyEvent`。先做 XKB 翻译，`KEYCODE = KEY_EVENT.keycode + 8`（evdev 与 XKB 的固定偏移），再 `xkb_state_key_get_one_sym` 取 keysym。这里有状态可切：`keyboard->m_resolveBindsBySym` 决定按符号还是按原始键位匹配，多布局用户按同一个物理键触发不同绑定就是这一支。会话未激活（`m_sessionActive` 为假）或设备被禁（`m_allowBinds`）时直接放行。
3. **动作执行**：解析结果交给 `src/config/shared/actions/`（`ConfigActions.cpp`）和 `src/keybinds/{Resolver, MatchResolver, Registry}.cpp`，最终落到工作空间切换。
4. **切工作空间**：`src/output/Monitor.cpp:1353` 的 `CMonitor::changeWorkspace`。第 1387 行算动画方向：`ANIMTOLEFT = NEW_ID && OLD_ID && (shouldWraparound(*NEW_ID, *OLD_ID) ^ (*NEW_ID > *OLD_ID))`。那个异或就是 `animations:workspace_wraparound` 的落点——开了它，从 1 切到最大编号时方向翻转，视觉上变成「往右跨过去」而不是「往左倒退一整轮」。
5. **两侧同时起动画**：紧接着的第 1390 与 1391 行分别对旧工作空间发 `ANIMATION_TYPE_OUT`、对新工作空间发 `ANIMATION_TYPE_IN`，样式取 `pWorkspace->m_animationStyle`。`WorkspaceAnimationController.cpp:42` 按样式前缀分流：`slidevert` / `slidefadevert` 走纵向，`:81` 的 `slidefade` 是滑加淡。
6. **每帧推进**：`CHyprAnimationManager` 的 500 微秒定时器起 `frameTick`，按叶子选中的曲线取 y 值。随后对每个活动变量调 `updateVariable`（几何量在 `begun()` 与 `goal()` 之间线性取点）或 `updateColorVariable`（转 OkLab 再插值）。窗口、层、弹窗分别由 `src/desktop/view/animationControllers/` 下的三个 controller 接管。
7. **决定刷哪块区域**：`AnimationManager.cpp` 的 `preDamageWorkspace` 是这条链上最实用的一段。普通工作空间切换只损伤相关窗口；特殊工作空间（scratchpad）可能跨显示器且带 dim 与 blur，于是直接 `damageMonitor`；浮动窗口的包围盒一旦跨了显示器边界，也退化成整窗损伤。函数里那句 `TODO: just make this into a damn callback already vax...` 是作者自己留的账。

这条链的分工是看得见的：按键解析、状态迁移、动画推进、损伤计算四段各自独立，中间靠动画变量与损伤区域两个概念衔接。「输入只管捕获、窗口管理只管状态、渲染只管画」这类说法要成立，就得像上面七步一样每一步都指得出一个文件。

## §9 常见故障与排查入口

按现象分四类，每类给一条能在本机自查的证据。以下命令本身取自仓库源码与官方 wiki，本文未在 Linux 环境实跑。

**启动就退出或黑屏。** 先确认不是会话管理的问题。仓库的 `misc:disable_watchdog_warning` 描述提到不通过 `start-hyprland` 启动会有警告，`start/` 目录就是这个看门狗二进制，它通过 `--watchdog-fd` 与合成器握手，并负责 NixOS 上的 nixGL 注入。用登录管理器或 TTY 直接起 `Hyprland` 时，`systemd/` 目录与 `example/hyprland.service` 这条服务单元路径就没走。诊断入口是 `hyprctl rollinglog` 与 `--systeminfo`。

**配置改了但行为不变。** 三种可能，按顺序排：这个键是不是已经废弃（`hyprctl deprecated-config`）；这个键是不是需要刷新位（§5 的 `REFRESH_*`，最稳妥的做法是 `hyprctl reload`）；你改的是不是当前真正加载的那份文件（`hyprctl configerrors` 与 `hyprctl -j getoption` 会暴露实际读到的值）。

**NVIDIA 上闪屏、掉帧或花屏。** 官方 wiki 的 nvidia 页里最硬的一条是：50xx 及更新型号必须用开源内核模块，老专有驱动不支持。FAQ 页另给了一个 525.60.11，但它的上下文是笔记本外接显示器黑屏，不是通用启动门槛，别当最低版本读。源码侧专门为此留了一个开关：`opengl:nvidia_anti_flicker` 默认 true，描述承认代价是"reduces flickering on nvidia at the cost of possible frame drops on lower-end GPUs"。另一个相关项是 `render:ctm_animation`，源码里 0/1/2 对应 disable/enable/auto，默认为 auto；wiki 说明这个 auto 的含义是在 NVIDIA 上关掉色彩矩阵变换的动画。

**插件加载失败。** 优先按 §6 的 ABI 约束排查：编译器不一致、头文件哈希不一致、Hyprland 更新后没重编。`pluginInit` 里做了阻塞调用会表现为启动卡住而不是报错。`hyprctl plugin load` 的相对路径不要赌：wiki 明确要求绝对路径（"Path has to be absolute!"），而 IPC 侧并不校验，参数最终原样交给 `PluginSystem.cpp:77` 的 `dlopen`，能不能加载取决于进程当前工作目录。权限系统开启时（`ecosystem:enforce_permissions` 默认 false）hyprpm 还需要 `hl.permission()` 显式放行。

**弹出窗口关不掉或者反复出现。** 有两个不是 bug 的弹窗：`ecosystem:no_update_news` 关掉升级提示，`ecosystem:no_donation_nag` 关掉一年两次的捐赠提示。默认值都是 false，也就是两个都开着。锁屏崩溃后想恢复锁屏程序，需要显式打开 `misc:allow_session_lock_restore`。

## §10 采用边界：谁现在上，谁再等等

把上面所有事实合起来，选择判据比「它好不好看」清楚得多。

**现在就适合**：你在 Arch 或 NixOS 上，想要平铺加动画加高自定义，并且愿意读源码级文档。官方 [Installation 页](https://wiki.hypr.land/getting-started/installation/)的原话是 "We officially run and test Hyprland on Arch and NixOS, and we guarantee Hyprland will work there"，同一页还提醒 point-release 发行版（Fedora、Ubuntu、Pop!_OS 等）"will have major issues running Hyprland"，并直接写了 "Ubuntu's Hyprland is extremely outdated"。打包者名单里带星号的是非官方支持，Hypr 团队不维护任何发行版包。

**先等一等**：需要一台几乎不维护的机器长期稳定的人；主用内核模块版本达不到上面门槛的 NVIDIA 用户；在 ARM 板子上且依赖某个函数钩子型插件的人（§6 那个 `#if !defined(__x86_64__)` 会让它静默失效）；以及完全不接受自己写配置的人——`misc:force_default_wallpaper`、`misc:disable_hyprland_logo`、`misc:disable_splash_rendering` 这些键的存在本身说明，出厂默认就是一个带 logo、带随机标语、带动画少女壁纸的桌面。

**自己动手编**：语言标准 C++26，wiki 给的编译器下限是 gcc 16 或 clang 19，CMake 3.30 起。构建选项里可以砍功能：`NO_XWAYLAND`、`NO_SYSTEMD`、`NO_UWSM`、`NO_HYPRPM`。贡献流程有一道硬门槛：`.github/workflows/vouch-prs.yml` 用 mitchellh/vouch 拉取 `hyprwm/.github` 里的中央 `VOUCHED.td` 名单，未被引荐者的 PR 会被自动检查拦下。这不友善，但它是显式写在工作流里的。

**发布节奏**：117 个 release，v0.54.0（2026-02-27）到 v0.55.0（2026-05-09）到 v0.56.0（2026-07-20），大致两个半月一个 minor。v0.56.0 的标题下写着 "brought to you by the Hyprland Corp." 和 "No breaking changes! :)"，正文按模块前缀给每条改了什么的改动打了标签，`algo/dwindle`、`config/lua`、`decoration/glow`、`desktop/windowRule`、`protocols/xdg-shell` 用斜杠，`hyprctl`、`plugins`、`renderer`、`groups` 用冒号，每条后面带 PR 号与作者。想追某项能力从哪个版本开始有，这份分类比翻提交记录快。要注意 `main` 的 `VERSION` 文件在核查当天仍是 `0.56.0`，而 tag 已经到 `v0.56.2`，patch 版本不落回 `main` 的 `VERSION`，所以别拿这个文件当已安装版本的依据，用 `hyprctl version`。

## §11 下一步读哪份代码

按你想回答的问题选，不要按目录顺序读。

| 你想搞清 | 打开 | 为什么是它 |
|---------|------|-----------|
| 有哪些配置项、默认值、取值范围 | `src/config/values/ConfigValues.cpp`（835 行，391 项） | 每个选项的名字、描述文本、默认值、min/max 和 OptionMap 在同一个 `MS<>()` 调用里，比任何二手文档都准 |
| 一个配置改动什么时候生效 | `src/config/supplementary/propRefresher/PropRefresher.cpp` | 刷新位是唯一的「改了到底动不动」真值表 |
| 模糊和发光到底怎么画出来 | `src/render/shaders/glsl/` 加 `src/render/decorations/` | `*finish.frag` 文件名与 §3 那张变体表一一对应 |
| 布局算法接口现在长什么样 | `src/layout/algorithm/` 与 `src/plugins/PluginAPI.hpp:196-220` | 一边是内置实现，一边是插件注册口，两边对照能立刻看出 `addLayout` 已废弃 |
| 事件与 IPC 的契约 | `src/ipc/s1/Commands.cpp` 末尾的注册块 | 38 条命令的名字、匹配方式和 JSON 支持全在那几十行 |
| 按键为什么没触发 | `src/keybinds/Manager.cpp:190` 起的 `onKeyEvent` | XKB 翻译、`+8` 偏移、`m_resolveBindsBySym` 分支都在这里 |
| 配置能不能不用 Lua | `src/config/lua/` 与 `src/config/ConfigManager.hpp` | 虚接口加单一实现的结构，本身就说明了可替换点 |

仓库自己给贡献者的入口是 `AGENTS.md`（v0.56.0 起存在，PR #14835）。里面除了命名规范，还有一条与本文每一节都相关的硬规则："Flag silent config breakage: e.g. changing an existing option's behavior. This is not allowed." 后面这一条约束，是一个每天动 391 个配置项的项目用来把「功能演进」和「静默改变用户桌面行为」分开的界线。

## §12 六个自测问题

答不出就回到对应小节，别往下读。

1. 一个基于 wlroots 的合成器和 Hyprland，在「谁去开 DRM 平面」这件事上分工有什么不同？答案要能落到一个具体仓库名。（§2）
2. `decoration:blur:variant` 从 0 改成 9，你付的代价是什么、这笔代价记在谁头上？（§3）
3. 为什么 `monocle:` 前缀下一个配置项都没有，而 `master:` 有 14 个？这透露了布局抽象层的什么信息？（§4）
4. 你用 `stow` 把 `hyprland.lua` 软链进 `~/.config/hypr/`，保存后为什么还会自动重载？（§5）
5. 一个 `.so` 在你机器上加载成功、在同事机器上让合成器崩，两条最可能的原因分别是什么？（§6）
6. 你想确认一篇文章给你的键名是不是当前版本还在用的，跑哪条命令？期望输出是什么？（§7）

## §13 事实核验与引用

**核验方法**。仓库按 `git clone --depth 1 https://github.com/hyprwm/Hyprland.git` 克隆取得，核查点为 `main@83cf6a6ed540dc37808434259c6a3ba663de9616`（末次提交 2026-09-19）。计数类断言的复现命令：

```bash
find src -name '*.cpp' | wc -l                          # 434
find src -name '*.hpp' | wc -l                          # 479
find src -name '*.cpp' -o -name '*.hpp' | xargs wc -l | tail -1   # 135376
ls src/protocols/*.cpp | wc -l                          # 64
ls src/render/shaders/glsl/ | wc -l                     # 52
ls .github/workflows/*.y*ml | wc -l                     # 13
wc -l src/plugins/* | tail -1                           # 1688
grep -c 'registerCommand' src/ipc/s1/Commands.cpp       # 38
grep -c '\[\[deprecated\]\]' src/plugins/PluginAPI.hpp     # 9
grep -o 'MS<[A-Za-z]*>("[a-zA-Z0-9_:.]*"' \
  src/config/values/ConfigValues.cpp | wc -l            # 391
grep -c '"monocle:' src/config/values/ConfigValues.cpp  # 0
find . -name '*.lua' | xargs wc -c | tail -1            # 30837
```

仓库体量用 blobless 加不检出（`--filter=blob:none --no-checkout`）几秒可拿全树，但要跑 `grep` 就得完整 `--depth 1` 克隆，blobless 上逐文件取 blob 会慢到不可用。这一点值得记在任何想复核本文的人的备忘里。

**未实跑项**。本文作者环境是 macOS，没有 Linux 内核模式设置（KMS）环境，`Hyprland --verify-config`、`hyprctl` 全部子命令、`hyprpm` 流程均未实际执行，其语法与开关取自 `src/main.cpp` 的 usage 文本、`src/ipc/s1/Commands.cpp` 的注册块、`hyprctl/hyprctl.usage`、`hyprpm/` 目录，以及 wiki 的 using-hyprctl 与 using-plugins 两页。`vouch-prs.yml` 的行为按工作流文件本身读出，未在一个真实 PR 上观察过。

**unresolved**。三条。其一，`debug:vfr` 与 wiki 的推荐语在分寸上不一致（源码写「别关，除非调试」，wiki 写「强烈建议保持开启以省资源」），本文两处都引，不裁决。其二，`hyprctl reload full-reset` 的 wiki 描述与 `Commands.cpp` 的实现不符（见 §5），按哪个走取决于你的版本，本文按实现写。其三，动画 `speed` 字段的单位换算在 `src/` 内找不到实现，它落在 hyprutils 的动画变量里，所以本文不给具体数值。另有一条本文没能定位到页面：wiki 的 custom-layouts 页在 2026-09-20 已不可达，§4 里 `hl.layout.register` 与 `lua:name` 那两处的原文以 `src/config/lua/layout/` 下的实现为准。

**失效条件**。四类断言最容易过期：`src/config/values/ConfigValues.cpp` 的计数与前缀分布（每个 minor 都会动）；`PluginAPI.hpp` 里 `[[deprecated]]` 的名单（§6 列了 9 处，下一批随时可能补进来）；配置语言的入口（本文核查的那个提交上 `eConfigManagerType` 只有 `CONFIG_LUA`，而 wiki 仍在讲 Lua 与 hyprlang 之间切换，说明这一层还在迁移中段，方向随时可能变）；以及 wiki 的 URL 结构——本文引用的路径在核查当天有效，而部分旧路径已退化成只剩面包屑的目录页。再核一遍的成本是上面那个克隆加十来条命令，十几分钟。

**参考**：[hyprwm/Hyprland](https://github.com/hyprwm/Hyprland)、[hyprwm/aquamarine](https://github.com/hyprwm/aquamarine)、[Hyprland wiki（配置）](https://wiki.hypr.land/configuring/)、[Hyprland wiki（安装）](https://wiki.hypr.land/getting-started/installation/)、[NVIDIA 指南](https://wiki.hypr.land/nvidia/)、[hyprctl 使用](https://wiki.hypr.land/configuring/core/advanced-configuration/using-hyprctl/)、[IPC 协议](https://wiki.hypr.land/ipc/)、[插件使用](https://wiki.hypr.land/hyprland-plugins/using-plugins/)、[插件开发入门](https://wiki.hypr.land/hyprland-plugins/development/getting-started/)、[v0.56.0 发布说明](https://github.com/hyprwm/Hyprland/releases/tag/v0.56.0)。
