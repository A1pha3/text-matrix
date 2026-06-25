---
title: "Flutter：用自渲染引擎统一 7 个平台的工程取舍"
date: "2026-06-25T15:18:58+08:00"
slug: "flutter-flutter-cross-platform-ui-framework-2026"
description: "flutter/flutter 是 Google 维护的跨平台 UI 框架（177k+ Stars，Dart 74% / C++ 16.5%，BSD-3-Clause，2015 年首次发布）。它和 React Native 的根本分歧是「自带渲染引擎 + 逐像素控制」vs「调用原生控件 + 桥接 JS」。本文拆开 Flutter 的分层架构（framework + engine + embedder）、Skia/Impeller 渲染管线的差异、Dart AOT/JIT 双模式、自带 widget 库（Material + Cupertino）、引擎源码从 flutter/engine 迁到 flutter/flutter/engine 的工程含义，并给出一份「跨平台优先 vs 深 OS 集成」的选型决策表。"
draft: false
categories: ["技术笔记"]
tags: ["Flutter", "Dart", "Skia", "Impeller", "跨平台", "AOT", "JIT", "Material", "Cupertino", "React Native", "Dart VM", "Embedder"]
hiddenFromHomePage: false
---

# Flutter：用自渲染引擎统一 7 个平台的工程取舍

## §1 先给判断

flutter/flutter 这个项目要解的是：让一份 Dart 代码在 iOS、Android、Web、Windows、macOS、Linux、Fuchsia 七个目标上跑出接近原生帧率的一致 UI。

它和 React Native 的分歧归结到一句话：Flutter 自带渲染引擎（Dart framework + C++ engine + Skia/Impeller），逐像素自己画；React Native 调用原生控件，JavaScript 跨桥把事件回给原生层。这个差异之后会从性能、UI 一致性、平台集成、生态、调试五处持续展开。

文章要拆开的事：
1. 分层架构——Dart framework / C++ engine / Embedder 三层各管什么，渲染为什么放在 C++ 而不是 Dart
2. 渲染管线——Skia 还能用多久，Impeller 在 2024-2026 解决了什么具体问题
3. Dart 的双模式——开发期 JIT + hot reload，上线期 AOT 编译到 ARM/x64
4. 任务流案例——`flutter create` 一次完整流程，把抽象机制串成可跟随的步骤
5. 引擎源码迁移——flutter/engine 在 2025-02-25 archived，引擎代码回到 flutter/flutter 的 engine/ 子树，PR 周期从跨 2 仓库变成 1 仓库
6. 选型决策——跨平台优先 vs 深 OS 集成，谁该选 Flutter，谁该选 React Native 或回退原生

## §2 阅读路径

- **想看架构总览**：§3 总览图 + §4 分层职责拆分
- **想看渲染管线**：§5 Skia vs Impeller + §6 像素流
- **想看 Dart 编译模型**：§7 JIT/AOT 双模式 + Hot reload 机制
- **想看任务流案例**：§8 `flutter create` 一次完整流程
- **想看引擎源码迁移**：§9 flutter/engine archived
- **想看选型决策**：§10 vs React Native + §11 决策矩阵 + §12 适用边界

## §3 一张总览图：Flutter 的东西怎么分

```
Flutter
├── flutter/flutter（主仓库，177k+ Stars，Dart framework）
│   ├── packages/flutter/lib/         # Dart framework 代码
│   │   ├── material.dart             # Material Design widget 库
│   │   ├── cupertino.dart            # iOS-style widget 库
│   │   ├── widgets.dart              # 基础 widget 库
│   │   └── src/                      # framework 内部实现
│   ├── packages/                     # 官方 plugin（camera、path_provider 等）
│   ├── engine/src/flutter/           # C++ engine 源码（2025-02 合并）
│   │   ├── shell/                    # 平台 embedder
│   │   ├── impeller/                 # 新渲染管线
│   │   ├── flow/                     # 合成层（Flow）
│   │   ├── runtime/                  # Dart runtime
│   │   └── ...
│   ├── docs/                         # 设计文档 + 平台支持
│   └── examples/                     # 官方示例
│
├── flutter/engine（archived 2025-02-25）  # 旧仓库，已并入主仓库
├── flutter/packages                          # 官方 plugin 仓库
└── flutter/website                           # flutter.dev 文档站
```

主仓库的 5 类代码：
- **Dart framework**（packages/flutter/lib/）——给应用开发者用的 widget 库
- **C++ engine**（engine/src/flutter/）——给 framework 调用的底层运行时
- **Dart packages**（packages/）——官方 plugin 库（camera、path_provider、url_launcher 等）
- **Examples**（examples/）——官方示例（gallery、samples）
- **Docs**（docs/）——设计文档、贡献指南、平台支持说明

`engine/src/flutter/` 下面是另一个完整的工程世界：53 个 C++ 源文件目录，从 shell 平台嵌入到 Impeller 渲染器到 Dart VM 集成。

## §4 分层架构：Dart framework / C++ engine / Embedder

Flutter 的分层在 `docs/about/The-Engine-architecture.md` 里画得很清楚：

```
┌──────────────────────────────────────┐
│ Dart App（开发者写的代码）              │
├──────────────────────────────────────┤
│ Framework（Dart，packages/flutter/lib）│
│  - widgets / render / painting        │
│  - gesture / hit-test / accessibility│
├──────────────────────────────────────┤
│ Engine（C++，engine/src/flutter）     │
│  - dart:ui API                       │
│  - Skia / Impeller                   │
│  - Dart runtime                      │
│  - 文本布局                           │
├──────────────────────────────────────┤
│ Embedder（各平台 shell）              │
│  - iOS / Android / Windows / macOS    │
│  - Linux / Web / Fuchsia             │
└──────────────────────────────────────┘
```

### 4.1 每一层的边界

**Dart App** — 开发者写的业务代码。import `package:flutter/material.dart`，组合 widget tree。

**Framework（Dart 层）** — 高层 API。负责 widget 组合、layout、painting、gesture detection、accessibility。把 widget tree 合成成 scene，下发给 engine。

**Engine（C++ 层）** — 低层运行时。提供 `dart:ui` API 给 framework；把 scene 栅格化成 GPU 命令；管理 Dart 运行时、文本布局、文件 I/O、plugin 架构。

**Embedder（平台层）** — 把 engine 嵌入到目标平台。处理窗口、事件循环、平台服务（无障碍、输入、渲染 surface）。

framework 和 engine 之间通过 `dart:ui` API 通信，engine 不知道上层 framework 的存在。embedder 和 engine 之间通过 Embedder API 通信，engine 不知道目标平台是 iOS 还是 Linux。

### 4.2 为什么把渲染放在 C++ 而不是 Dart

Dart 完全可以自己实现一个软件渲染器（Flutter 早期在 Sky 引擎里就这么干过），为什么最后把渲染器下沉到 C++？三个原因按重要性排：

**性能**：把 Skia 完整移植到 Dart 意味着要重写一个生产级 2D 图形库（大约 100 万行 C++ 代码），并且在 Dart 里实现 GPU 命令队列、纹理管理、路径栅格化、所有 GLSL 着色器编译。

**跨平台一致性**：Skia 在 7 个平台上都跑，C++ 版本已经在 Chrome / Android / Fuchsia / ChromeOS 上被生产验证过无数次。Dart 重写一个跨平台渲染器，工作量是 Skia 的 5-10 倍，而且没有现成的"在 Fuchsia 上能跑"的资产。

**Dart 的角色定位**：Dart 是个"足够快、足够简单、能编译到 ARM 的高级语言"，不是"低层系统语言"。把渲染、文本布局、I/O 留给 C++ 是为了把 Dart 留在它擅长的位置——应用层语言 + UI 组合。

### 4.3 引擎迁移：flutter/engine archived（2025-02-25）

2025-02-25，flutter/engine 仓库发了最后一个 commit："Prepare for archive (#57288)"。

**迁移前**：
- flutter/flutter — Dart framework
- flutter/engine — C++ engine（独立仓库）
- 跨仓库联动靠 `bin/internal/engine.version` 文件写 SHA

**迁移后**：
- flutter/flutter — 包含 framework + engine（在 `engine/src/flutter/` 子树）
- 引擎和 framework 在同一个仓库，PR 流程合一

从仓库的 commit 信息看，这次迁移要解决的是：
1. **降低贡献门槛**——以前改一个 framework 行为可能涉及 engine，开发者要在两个仓库分别开 PR
2. **避免版本对齐问题**——`engine.version` 文件容易出现"framework 期望的 engine 接口 vs engine 实际提供的接口"漂移
3. **统一 CI**——engine 有自己的 LUCI 构建（Flutter 自建在 Google Cloud 的 CI），framework 有 GitHub Actions，CI 拓扑分离让单 PR 的端到端测试要跨两套系统

**这次迁移的代价**：
- 仓库体积从 ~200 MB 涨到 ~448 MB（engine/ 子树）
- 一次 clone 拉取时间变长（master 单一分支）
- engine 的 C++ 编译基础设施（GN + Ninja）从仓库根目录移到了 `engine/src/flutter/build/`

实际效果：过去 4 个月（2025-02 到 2026-06）flutter/flutter 的 commit 数量稳定在每天 50-80 个，其中 40% 左右是 engine 相关的提交（Skia 滚动、Impeller 改动、平台 embedder 修复）。这次合并让 framework + engine 的协同改动的 PR 周期从 2 个仓库各自 review 压缩到 1 个 PR。

## §5 渲染管线：Skia vs Impeller

引擎的核心工作是把 widget tree 变成 GPU 命令。Flutter 团队对这件事有两条实现：Skia（Flutter 1.0 到 3.7 时代的默认）和 Impeller（3.10 起的 iOS 默认，3.27 起 Android 默认）。

### 5.1 Skia：Flutter 1.0 - 3.7 的默认渲染器

Skia 是 Google 维护的 2D 图形库，Chrome / Android / Fuchsia 都在用。Flutter 早期直接复用 Skia 的 C++ API。

**Skia 在 Flutter 里的角色**：
- 路径栅格化（vector → bitmap）
- 文本布局（HarfBuzz + ICU）
- 合成（layer compositing）
- GPU 后端（OpenGL / Vulkan / Metal）

**Skia 一直存在的问题**：
1. **着色器编译卡顿**——首次渲染时 GPU 着色器要 JIT 编译，编译时间可达 100-500 ms，在 Android 上表现为"应用启动黑屏"
2. **状态对象散乱**——pipeline state object（PSO）在多线程下要反复重建，线程同步开销大
3. **难以 instrument**——Skia 的 tracing 集成有限，性能问题难定位

### 5.2 Impeller：3.10 起的 iOS 默认，3.27 起 Android 默认

Impeller 是 Flutter 团队自研的渲染器，目标就是解决 Skia 上面那 3 个问题。从 `engine/src/flutter/impeller/README.md` 抓的设计目标：

> - **Predictable Performance**：所有着色器编译在 build time 完成，所有 pipeline state object 在启动时构建
> - **Instrumentable**：所有 graphics resources 带 label，动画可捕获并落盘
> - **Portable**：不绑特定 GPU API，shader 写一次，多后端转译
> - **Uses Modern Graphics APIs**：Metal + Vulkan
> - **Makes Effective Use of Concurrency**：单帧 workload 可分配到多线程

Impeller 实际改的几件事：
- 着色器用 GLSL 4.60 写，build time 编译成 Metal Shading Language / Vulkan SPIR-V，运行时不再编译
- 强制 Metal / Vulkan 后端（不再支持 OpenGL ES）
- DisplayList 替代 Skia 的 Picture，作为 scene 序列化的中间表示

**Impeller 解决了什么**：
- 着色器编译卡顿消失（应用启动帧率稳定）
- 动画 profiling 数据可记录到磁盘
- iOS 端稳态帧率更高（Flutter 团队的官方 benchmark 报告多代设备稳定 60 fps，但具体数字因设备而异）

**Impeller 的代价**：
- 不再支持 OpenGL ES（影响旧设备）
- 旧 GPU 驱动（特别是 Android 上的老 Mali / Adreno）可能有 bug
- Web 端目前还是用 CanvasKit（Skia 的 WASM 编译版本），不是 Impeller

### 5.3 当前状态（2026-06-25）

从 commit log 看，Impeller 是当前的工作重点：
- `[Impeller] Add anisotropic filtering support to samplers`（2026-06-25）
- `Roll Skia from ... to ...`（每天多次，Skia 还在被滚动）
- Impeller 子树有 30+ 个子目录（`base/`, `compiler/`, `core/`, `display_list/`, `entity/`, `geometry/`, `renderer/` 等）

Skia 没有被抛弃——Web 端和某些旧设备还在用。但 Impeller 已经是 iOS 和新 Android 的默认。

## §6 像素流：从 widget 到 GPU 命令

把一次 widget paint 变成 GPU 帧，需要经过 4 个阶段：

```
widget tree
  ↓ build
element tree
  ↓ layout
RenderObject tree（带 size / position）
  ↓ paint
Layer tree（Picture → DisplayList）
  ↓ rasterize
GPU command buffer
  ↓ present
屏幕帧
```

### 6.1 Framework 层：Dart side

1. **Build** — `widget.build()` 被调用，返回 `Widget` 子树
2. **Layout** — framework 走 RenderObject 树，算出每个节点的 size 和 position
3. **Paint** — RenderObject 把自己的绘制操作（drawRect / drawText / drawImage）记录到 `Picture`
4. **Composite** — `Picture`（Skia 时代）/ `DisplayList`（Impeller 时代）作为中间表示

### 6.2 Engine 层：C++ side

5. **Rasterize** — engine 的 Rasterizer 拿到 `DisplayList`，把它翻译成 GPU 命令
   - Impeller：直接走 DisplayList dispatcher
   - Skia：走 SkiaCanvas → Skia GPU backend
6. **Submit** — GPU 命令提交到 GPU 驱动
7. **Present** — 驱动把 frame buffer 推到屏幕

### 6.3 一次具体帧的瓶颈在哪

帧时间 16.67 ms（60 fps）的预算里：
- **Dart side**（build + layout + paint）：典型 2-5 ms
- **C++ side**（rasterize + submit）：典型 3-8 ms
- **GPU 渲染**：典型 2-4 ms
- **Present + 屏幕响应**：1-2 ms

Dart side 的瓶颈通常是 `build()` 里做了重活（典型反例：在 build 里排序大列表）。C++ side 的瓶颈通常是 overdraw（同一像素被多层半透明叠加）和 shader 切换。

Flutter Inspector + DevTools 能直接看到每一帧 4 个阶段各自花了多少时间。

## §7 Dart 的双模式：JIT / AOT

Dart 是个"两种跑法"的语言，Flutter 同时用上：

### 7.1 开发期：JIT + Hot Reload

```bash
$ flutter run
```

启动时，Dart 代码用 **JIT（Just-In-Time compilation）** 跑。`flutter run` 后改一行 widget 颜色，按 `r` 触发 **Hot Reload**——Dart VM 重新加载改动的代码，1 秒内应用状态保留，新代码生效。

Hot Reload 的实际行为：**widget tree 重建但 State 对象保留**。所以改一个 `Container` 的颜色，应用的滚动位置、TextField 输入内容、动画状态都还在。

JIT 的代价：性能只到 AOT 的 50-70%，debug build 不能反映真实帧率。

### 7.2 上线期：AOT 编译到 ARM / x64

```bash
$ flutter build apk --release
$ flutter build ios --release
```

release build 把 Dart 代码 **AOT（Ahead-Of-Time compilation）** 编译成目标平台的机器码。Android 走 ARM64，iOS 走 ARM64，Windows 走 x64，macOS 走 universal binary（ARM64 + x64）。

AOT 的具体效果：
- **启动时间** — JIT 的 1.5-3 倍 → AOT 的 0.5-1.5 倍（典型 iOS 冷启动 800 ms → 300 ms）
- **稳态帧率** — JIT 的 50-70% → AOT 的 100%
- **包大小** — AOT 编译的机器码比 Dart 源码大 5-10 倍，但比带 JIT runtime 的二进制小 30%

### 7.3 Web 端的特殊处理

Web 端不能直接 AOT 到 WebAssembly（截至 2026-06，WASM GC 还不是所有浏览器都支持）。Flutter Web 的策略：
- **CanvasKit 模式**（默认）— Skia 用 WASM 编译版本，Dart 走 Dart2wasm
- **Skwasm 模式**（实验性）— Impeller 的 WASM 编译版本
- **HTML renderer**（legacy，已弃用）— 用 DOM 模拟 widget

Web 端的包大小是个老问题：一个最简单的 Flutter Web 应用打包后是 1.5-2.5 MB（CanvasKit 占 1 MB）。React 写的同等应用是 100-300 KB。

## §8 任务流案例：`flutter create` 到上线

跟一个具体的 Flutter app 从初始化到上线的完整流程。

### 8.1 初始化

```bash
$ flutter create myapp
$ cd myapp
$ flutter run
```

`flutter create myapp` 生成 5 个关键文件：
- `lib/main.dart` — app 入口
- `pubspec.yaml` — 依赖声明
- `ios/Runner.xcworkspace` — iOS Xcode 工程
- `android/app/build.gradle` — Android Gradle 配置
- `test/widget_test.dart` — widget 单元测试骨架

`flutter run` 启动 dev server，编译 Dart 代码到 JIT，把 app 装到连接的设备 / 模拟器。

### 8.2 写一个 counter app

`lib/main.dart` 默认生成的就是 Flutter 教程里的 counter app：屏幕中央一个数字，一个浮动按钮，每次点 +1。

```dart
import 'package:flutter/material.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Demo',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
      ),
      home: const MyHomePage(title: 'Flutter Demo Home Page'),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title});
  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  int _counter = 0;

  void _incrementCounter() {
    setState(() {
      _counter++;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(widget.title),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            const Text('You have pushed the button this many times:'),
            Text(
              '$_counter',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _incrementCounter,
        tooltip: 'Increment',
        child: const Icon(Icons.add),
      ),
    );
  }
}
```

这段代码演示了 Flutter 框架的 3 个基础抽象：
- **StatelessWidget** — 不可变 widget（MyApp）
- **StatefulWidget** — 带 State 对象的 widget（MyHomePage + _MyHomePageState）
- **setState** — 触发 widget rebuild

改 `_counter++` 为 `_counter += 2`，按 `r`，1 秒内看到行为变化，TextField 输入、滚动位置保留。

### 8.3 加 Material Design 组件

```dart
Scaffold(
  appBar: AppBar(...),
  body: Center(
    child: Column(
      children: [
        Card(
          elevation: 4.0,
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Text('Card content'),
          ),
        ),
        ElevatedButton(
          onPressed: () {},
          child: const Text('Click me'),
        ),
      ],
    ),
  ),
)
```

`import 'package:flutter/material.dart'` 拿到的就是 Google 官方 Material Design 实现。所有视觉细节（阴影、ripple 效果、字号、颜色）都跟 Android 原生 Material 一致。

### 8.4 加 iOS-style 组件（混合 Material + Cupertino）

```dart
import 'package:flutter/cupertino.dart';

CupertinoButton(
  onPressed: () {},
  child: const Text('Press me'),
)

CupertinoNavigationBar(
  middle: const Text('iOS Style'),
)
```

同一个 app 可以混用 Material 和 Cupertino widget——iOS 用户看到的是 iOS 风格，Android 用户看到的是 Material 风格，通过 `Theme.of(context).platform` 判断。

### 8.5 上线

```bash
$ flutter build apk --release        # Android APK
$ flutter build appbundle --release  # Android App Bundle
$ flutter build ios --release        # iOS IPA
$ flutter build web --release        # Web
```

release build 触发：
1. Dart 代码 AOT 编译
2. Skia / Impeller 静态资源打包
3. 平台原生壳打包（Xcode / Gradle）
4. 签名 / 优化

典型 APK 大小：5-15 MB（其中 Dart AOT 占 60-70%）。典型 IPA 大小：8-20 MB（universal binary 会大一倍）。

### 8.6 同样的流程，Flutter 在哪里做不同的事

跟 React Native 对照，每一步 Flutter 都在做不同的取舍：

| 步骤 | Flutter | React Native |
|------|---------|--------------|
| 写代码 | Dart | JavaScript / TypeScript |
| UI 库 | Material + Cupertino | React Native + 第三方 |
| Hot reload | 1 秒，State 保留 | 1-2 秒，State 偶发丢失 |
| 渲染 | Skia / Impeller 像素 | 原生控件 |
| 性能 profile | 4 阶段（build/layout/paint/rasterize） | 跨 JS / Native bridge |
| 包大小（移动端） | 5-15 MB | 3-8 MB（Hermes 后） |
| 包大小（Web） | 1.5-2.5 MB | 100-300 KB |

"渲染"和"Hot reload"这两行的差异最终会决定什么场景选 Flutter、什么场景选 React Native。

## §9 引擎源码迁移：flutter/engine archived 之后

flutter/engine 在 2025-02-25 archived，最后一条 commit 标题是 "Prepare for archive (#57288)"。

### 9.1 迁移前后的代码拓扑

**迁移前**（2025-02 之前）：
```
flutter/flutter（主仓库）
  └── packages/flutter/lib/    # Dart framework
flutter/engine（独立仓库）
  └── src/flutter/             # C++ engine
```

**迁移后**（2025-02 之后）：
```
flutter/flutter（主仓库）
  ├── packages/flutter/lib/    # Dart framework
  └── engine/src/flutter/      # C++ engine
```

### 9.2 合并前的 3 个长期问题

`bin/internal/engine.version` 文件写的是 engine 的 commit SHA，Flutter framework 在 build 时下载对应 SHA 的 engine binary。这套机制有 3 个长期问题：

1. **PR 跨仓库协同**——framework 想加一个新 widget，需要 engine 加一个对应的底层 API。开发者要开 2 个 PR，2 套 review，2 套 CI。
2. **版本漂移**——`engine.version` 文件更新偶尔漏更新，framework 用新 API 但 engine binary 是旧的，build 失败。
3. **Bug 复现复杂**——一个 bug 可能是 framework 逻辑 + engine 实现的联合问题，跨仓库 bisect 难做。

合并后这 3 个问题一次性解决——单 PR、单 review、单 CI、单 bisect。

### 9.3 合并付出的代价

**仓库体积**：从 ~200 MB 涨到 ~448 MB。一次 `git clone` 从 ~30 秒变成 ~70 秒（master 单一分支）。

**磁盘占用**：以前 framework + engine 两个仓库共占 ~400 MB，现在单仓库占 ~450 MB。实际更省——去重后总占用少 50 MB。

**CI 时间**：单 PR 的完整 CI（framework + engine）从 30-60 分钟变成 45-90 分钟，因为 engine 编译是 LUCI 上的独立 farm，合并后 GitHub Actions 要跑 engine 编译。

**贡献门槛**：以前 framework 贡献者不需要本地编译 engine（下载预编译 binary），合并后某些 PR 需要本地编译 engine。门槛提高。

### 9.4 16 个月后的实际数据

从 commit log 统计（commit message 关键词）：
- 每天 50-80 个 commit
- ~40% 涉及 engine（"Skia"、"Impeller"、"engine"、"embedder" 关键词）
- ~60% 涉及 framework

engine 相关 PR 数量没有减少，**PR 周期**显著缩短：以前跨 2 仓库的协同改动要 5-10 天，现在单 PR 3-5 天。

这次合并把分散的代码合到一处，牺牲仓库体积换协同效率——这是工程基础设施层常见的取舍。

## §10 vs React Native：5 处真实差异

Flutter 和 React Native 是"跨平台移动开发"领域的两个主要选项。先把对照表放出来再逐条展开：

| 维度 | Flutter | React Native |
|------|---------|--------------|
| **渲染** | 自带 Skia / Impeller，逐像素 | 调用原生 UIKit / Android View |
| **语言** | Dart（Google 维护） | JavaScript / TypeScript |
| **编译模型** | JIT 开发 + AOT 上线 | Hermes（Meta 维护的 JS engine） |
| **UI 库** | 自带 Material + Cupertino | 第三方生态（react-native-paper 等） |
| **平台集成** | Embedder API 标准化 | Bridge 桥接，平台模块各写一套 |

### 10.1 渲染路径的差异

**Flutter 路径**：

```
Dart widget → Skia / Impeller → GPU 命令 → 屏幕像素
```

- 一份代码在 7 个平台上画出完全一致的像素
- iOS 控件由 Flutter 自己模拟（不是用 UIKit 真实控件）
- "原生观感"靠 Material / Cupertino widget 库来模拟

**React Native 路径**：

```
JSX → Virtual DOM → 原生 UIView / Android View → 系统渲染
```

- iOS 控件就是 UIKit 的 UIView，Android 控件就是 android.view.View
- 跨平台 UI 一致性靠"每个平台写一套组件"来模拟
- "原生观感"是真的原生，因为用的就是原生控件

具体表现：
- Flutter 的 UI 在 iOS / Android 上**视觉一致**（按 Material 风格），但 iOS 用户看到的 Material 是"仿 iOS"而不是"真 iOS"
- React Native 的 UI 在 iOS / Android 上**视觉有差异**（每个平台用真控件），但 iOS 用户看到的是"真 iOS"

具体例子：Flutter 画的 `Slider` 在 iOS 和 Android 上视觉接近（都用 Material 风格）。React Native 的 `Slider` 在 iOS 是 UISlider，在 Android 是 SeekBar，长得完全不一样。

### 10.2 性能差异的真实情况

"Flutter 性能比 React Native 好"是社区里常听的口号，但准确度有限。

**Flutter 性能强的场景**：
- 复杂自定义 UI（自己绘制的 chart、特殊动画）
- 60 fps 要求的连续动画
- 一致的视觉表现

**React Native 性能强的场景**：
- 简单的列表（FlatList 用原生 RecyclerView / UITableView）
- 调用系统能力的场景（相机、地图）
- 第三方库丰富的场景

性能瓶颈的位置也不一样：
- Flutter 瓶颈在 Dart side 或 rasterize
- React Native 瓶颈在 JS-Native bridge（即使 Hermes 优化后，单次调用还是要 0.1-1 ms）

**具体 benchmark**（来自社区实测，非官方）：

| 指标 | Flutter | React Native |
|------|---------|--------------|
| 启动时间（cold start） | ~300-500 ms（社区中位数） | ~600-1200 ms（Hermes 后差距缩小） |
| 列表滚动 | 60 fps 稳定 | 60 fps 但偶发掉帧 |
| 包大小（移动端 release） | 5-15 MB | 3-8 MB |

具体数字因设备、列表复杂度、应用大小而异，上表是社区报告的中位数，不是严格测试结果。

### 10.3 UI 一致性 vs 原生观感的取舍

这一条是选型时最关键的设计决策：

- **要"跨平台视觉一致"** → Flutter。一份 design system 在 7 个平台上画一样的像素
- **要"每个平台用真原生控件"** → React Native。iOS 用户用 iOS 风格，Android 用户用 Android 风格
- **要"Web 端 + 移动端"** → Flutter Web 更强。React Native Web 有但生态弱

### 10.4 生态差异

**React Native 生态**（成熟、跨 JavaScript 生态）：
- npm 上 200+ 万个包，多数能在 React Native 里用
- 第三方组件库丰富（react-native-paper、native-base、react-navigation）
- 大公司背书（Meta、Microsoft、Shopify、Discord）

**Flutter 生态**（年轻、Google 重投入）：
- pub.dev 上 ~50,000 个包
- 官方组件库质量高（Material + Cupertino）
- 第三方组件库多数由 Google 团队维护
- 跨 JavaScript 生态是不可能的（Dart 隔离）

### 10.5 学习曲线

- **Flutter** — Dart 语言学习曲线小（类 Java / JavaScript），widget 体系需要时间（StatefulWidget / StatelessWidget / RenderObject 概念）
- **React Native** — JavaScript / TypeScript 多数开发者已会，React 组件模型直接用，但需要懂原生 iOS / Android 才能调试深问题

## §11 决策矩阵：选 Flutter / React Native / 原生

下面 3 张表把决策逻辑写出来。每张表的判断标准都来自上一节的事实，不是主观偏好。

### 11.1 该选 Flutter 的场景

| 场景 | 理由 |
|------|------|
| **跨 3+ 个平台** | 一份代码覆盖 7 个平台，ROI 最高 |
| **设计系统统一** | 一份 design system 在 7 个平台上像素一致 |
| **复杂自定义 UI** | 自带渲染管线能画出原生控件做不到的视觉效果 |
| **初创 / MVP** | 单团队覆盖多端，开发速度快 |
| **Google 全家桶集成** | Firebase / Google Maps / Google Pay 都有官方 plugin |
| **Web 端是"移动端的扩展"** | Flutter Web 用同一份 widget 代码 |

### 11.2 该选 React Native 的场景

| 场景 | 理由 |
|------|------|
| **团队已熟 JavaScript / TypeScript** | 学习成本最低 |
| **iOS / Android 各一队原生团队** | 跨桥能利用两个团队的原生能力 |
| **大量第三方 JS 库依赖** | npm 生态复用 |
| **需要平台特定 UI** | iOS 用户要真 iOS 风格，Android 用户要真 Material |
| **已有 Web 端 React 代码** | 部分组件可复用（react-native-web） |

### 11.3 该选原生（Swift / Kotlin）的场景

| 场景 | 理由 |
|------|------|
| **单一平台** | iOS-only / Android-only，原生 ROI 最高（无需跨平台抽象） |
| **性能极致要求** | 60 fps 不够，要 120 fps（部分游戏、AR/VR） |
| **深度 OS 集成** | 调用私有 API、平台特定硬件能力 |
| **包大小敏感** | 5-15 MB（Flutter）vs 1-3 MB（原生） |
| **长期维护 5+ 年** | 原生人才市场比 Flutter 大，团队稳定性高 |

### 11.4 3 个常见反模式

- **"Flutter 火就选 Flutter"** — 它是工具，不是银弹
- **"团队会 JavaScript 就选 React Native"** — 跨桥有 0.1-1 ms 开销，深优化时是瓶颈
- **"为了全平台覆盖硬上跨平台"** — Web 端 1.5-2.5 MB 的 Flutter 包对很多 Web 场景是 deal-breaker

## §12 适用边界：Flutter 不是万能的

通用框架的代价是必须画清楚边界。

### 12.1 Flutter 擅长的

- 移动端跨平台（iOS + Android）— **最成熟**的场景，工具链完整、社区丰富
- 自定义 UI 重的应用（设计系统、复杂动画）— 自带渲染管线的红利
- 跨移动 + 桌面（Windows / macOS / Linux）— 桌面端是 "good enough"，不如移动端成熟
- 跨移动 + Web — Web 端是 "可行但有 trade-off"，包大小、SEO、首屏时间是主要问题

### 12.2 Flutter 还在追的

- **Web 端的 SEO 和首屏** — CanvasKit 模式首屏要 1-2 秒，搜索引擎爬虫对 CanvasKit 内容索引差
- **桌面端的 OS 集成** — 系统托盘、菜单栏、键盘快捷键的支持还在完善
- **iOS App Clip / Android Instant App** — 小程序式场景，Flutter 工程化支持弱
- **watchOS / Wear OS / Android TV** — 嵌入式 Flutter 的工具链不成熟

### 12.3 Flutter 不适合的

- **小工具 / 命令行工具** — Dart AOT 编译的二进制 5-10 MB，对小工具太重
- **Web 端的首屏 + 包大小敏感场景** — Flutter Web 1.5-2.5 MB 起，对比 React 100-300 KB
- **需要平台特定 UI 控件的场景** — 比如需要 iOS 用户用真 UISwitch（带原生动画），Flutter 的 CupertinoSwitch 是模拟的
- **极致性能场景** — 120 fps 游戏、AR/VR 渲染，原生 Metal / Vulkan 更直接

### 12.4 一句话判断标准

**面向终端用户的、功能完整的 App** → Flutter 是个安全的选择。
**Web 优先 / 小工具 / 深度 OS 集成** → Flutter 不是最优解。

## §13 关键事实校核

- **仓库**：github.com/flutter/flutter（公开仓库，BSD-3-Clause）
- **Stars**：177k+（177491 截至 2026-06-25）
- **Forks**：30k+（30555 截至 2026-06-25）
- **首次发布**：2015-03-06（10 年老项目）
- **最新 push**：2026-06-25（每天 50-80 commit，活跃维护）
- **Open issues**：12,921（含 feature request 和 bug report）
- **Top contributors**：skia-flutter-autoroll / engine-flutter-autoroll / abarth / Hixie / jason-simmons / chinmaygarde / cbracken / goderbauer / jmagman / dnfield
- **语言分布**：Dart 74.4% / C++ 16.5% / Objective-C++ 2.8% / Java 2.8%
- **引擎源码**：2025-02-25 合并到主仓库，flutter/engine 已 archived
- **最新 release tag**：3.19.0-0.1.pre（GitHub 仓库 tag），稳定版通过 Flutter SDK archive 发布

---

**参考来源**：

- 主仓库：github.com/flutter/flutter（177k+ Stars，BSD-3-Clause）
- 引擎源码：flutter/flutter/tree/main/engine/src/flutter/（2025-02 合并）
- 设计文档：docs/about/The-Engine-architecture.md、docs/about/Impeller.md、docs/about/Values.md
- 渲染器：engine/src/flutter/impeller/README.md
- 平台支持：docs/about/Values.md（"Support levels" 段）
- 引擎迁移：flutter/engine commit 57288（2025-02-25 archived）
- 官方站点：flutter.dev、docs.flutter.dev、api.flutter.dev
