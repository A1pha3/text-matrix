---
title: "Unciv：用 Kotlin Multiplatform + LibGDX 在低端设备上重制 Civ V 的工程取舍"
date: "2026-06-17T21:04:44+08:00"
slug: "yairm210-unciv-android-civ-v-remake-guide"
description: "Unciv 是基于 LibGDX 与 Kotlin Multiplatform 的开源 Civ V 重制版，把核心规则塞进共享 core 模块并在 Android、桌面、Server 三端复用。"
draft: false
categories: ["技术笔记"]
tags: ["Unciv", "Kotlin Multiplatform", "LibGDX", "Civ V", "游戏开发"]
---

## 一句话判断

Unciv 不是一个"用 Kotlin 写的游戏"，它是一个把 Civ V 的全部机制用一份共享 `core` 模块重新实现、然后分别在 Android、桌面、Server 三端渲染出来的开源 4X（eXplore, eXpand, eXploit, eXterminate）项目。它最值得拆的不是游戏性，而是仓库结构：在 Gradle 多模块 + Kotlin Multiplatform 的约束下，把游戏规则、UI、跨端入口拆得干净，并通过 JSON 化的 Ruleset（规则集）让"Moddability"成为产品级能力。README 标题写得很直白——"small, fast, moddable, FOSS, in-depth 4X that can still run on a potato"。这句话是产品定位，也是架构约束：必须在低端设备上跑，因此代码必须紧凑、模块必须可裁剪、扩展必须靠 JSON 而不是 fork。

## 项目位置

[yairm210/Unciv](https://github.com/yairm210/Unciv) 是 GitHub 上规模最大的开源 Civ 重制项目之一：

| 指标 | 数值 |
|------|------|
| Stars / Forks | 10,566 / 1,840 |
| 主要语言 | Kotlin（核心逻辑）+ Java（少量胶水） |
| 渲染引擎 | LibGDX |
| 协议 | MPL-2.0（文件级 copyleft，即修改 MPL 文件须开源，但可与私有代码链接） |
| 最新 Release | 4.20.14（2026-06-16） |
| Gradle 模块 | `core`（KMP）、`android`（Android 入口）、`desktop`（桌面入口）、`server`（多人对战）、`tests` |
| 支持平台 | Android（Google Play / F-Droid）、Windows（MSI / Scoop / Chocolatey）、Linux（Flathub / AUR / Pi-Apps）、macOS（Homebrew）、Web/CLI（headless） |

要理解 Unciv 的形状，先抛掉"这是一个 Android 游戏"的旧印象。`android/` 是其中之一，但所有核心玩法都在 `core/`；桌面端走 `desktop/`，多人对战服务走 `server/`，`tests/` 负责跨端覆盖。下面把这张工程全景画清楚。

## 系统地图

`settings.gradle.kts` 直接给出了模块声明：`desktop`、`core`、`tests`、`server` 永远存在，`android` 只有在检测到 `ANDROID_HOME`（Android SDK 路径）时才会 include。这意味着仓库在 CI（Continuous Integration，持续集成）和开源贡献者的普通 Linux 机器上**不需要 Android SDK** 也能跑核心构建——这是它能保持低门槛贡献的关键设计。

```text
┌─────────────────────────────────────────────────────────────────────┐
│                       core (Kotlin Multiplatform)                   │
│  - 全部游戏规则、回合、AI、Mod 加载、序列化                            │
│  - target: JVM（JVM_1_8）                                            │
│  - 纯逻辑层：logic/、automation/、models/、ui 渲染抽象                 │
│  - 无平台依赖：LibGDX 仅作为渲染/输入抽象暴露在 ui/ 子包               │
└──────────────┬──────────────┬────────────────────┬─────────────────┘
               │              │                    │
   ┌───────────▼──────┐  ┌────▼───────────┐  ┌────▼──────────┐
   │   android/       │  │   desktop/     │  │   server/     │
   │   (Android 入口) │  │   (桌面入口)   │  │   (多人服务)  │
   │                  │  │                │  │                │
   │ - AndroidLauncher│  │ - DesktopLauncher│ │ - UncivServer │
   │ - assets 在仓库内│  │ - packr 打包 JRE│ │ - WebSocket + │
   │   (android/assets│  │ - MSI / JAR    │  │   Ktor        │
   │    是唯一 assets │  │                │  │ - 无头模式    │
   │    源)          │  │                │  │                │
   └──────────────────┘  └────────────────┘  └────────────────┘
                                │
                ┌───────────────▼────────────────┐
                │   tests/  (跨端单元 + 桌面集成)  │
                │   - Ruleset 兼容性、地图生成、   │
                │     AI 决策树回归                │
                └────────────────────────────────┘
```

读这张图要锁定四件事，否则后面所有判断都会跑偏：

1. **所有规则都在 `core/`，没有 Android-only 逻辑**。`core/build.gradle.kts` 只有一个 `id("kotlin")` 插件与 `jvmTarget = JVM_1_8` 目标，没有 Android plugin、没有桌面 plugin。这意味着你在 Android 上跑的是同一份 JVM 字节码，桌面也是——LibGDX 在两端都是 JVM 进程。这是 Unciv 能在低端设备上跑起来的根本原因：JVM 启动开销比 Android Activity 启动小一个数量级。
2. **`assets` 集中在 `android/assets/`**。`desktop/build.gradle.kts` 的 `tasks.register<JavaExec>("run")` 把 `workingDir = file("../android/assets")` 作为运行工作目录；这是为了桌面端复用 Android 端同一份游戏资源（JSON、贴图、字体、音效）。所有 Mod 加载、规则 JSON、UI 皮肤都从这套目录里读，三端共享。
3. **`desktop/` 的发行版打包用 packr**。`Dockerfile` 显示 `gradle desktop:packrLinux64` 会用 [libgdx/packr](https://github.com/libgdx/packr) 把 JRE 与 JAR 一起打成单文件；Windows 的 MSI 由 Gradle 任务生成。这是 Unciv 能"双击即玩"的关键——不需要用户预先装 Java。
4. **`server/` 是个独立的 JVM 服务**。`server/build.gradle.kts` 把 `mainClass` 设为 `com.unciv.app.server.UncivServer`，启动后提供 WebSocket 接口供其他玩家加入多人对局；游戏逻辑仍来自 `core/`，服务器只是"调度 + 持久化"，不渲染画面。

## 一次回合从点击"Next Turn"到 AI 行动

光看结构容易把 Unciv 误读成"普通的回合制游戏"。它真正的差异在于"逻辑 + 视图分离"——`core/` 把回合切分成纯数据操作，UI 只负责把结果显示出来。下面用"玩家点 Next Turn、触发所有 AI 玩家行动一次"为例，看一次回合在系统里的实际流转（具体类名以仓库当前版本为准，命名遵循 Kotlin 约定）：

1. **玩家点击按钮**。`core/src/com/unciv/ui/screens/worldscreen/WorldScreen` 接收到 NextTurn 事件，调用 `gameInfo.nextTurn()`。
2. **回合序列入口**。`core/src/com/unciv/logic/GameInfo.nextTurn()` 是核心入口：按顺序调用 `TurnManager.startTurn()`，遍历所有 `Civilization` 实例。
3. **玩家文明行动**。当前玩家的城市、单位、研究、政策、宗教分别由 `CityManager`、`UnitManager`、`TechManager`、`PolicyManager`、`ReligionManager` 处理；每个管理器只更新自己的领域，不跨界修改其他领域状态。
4. **AI 文明行动**。非玩家文明走 `core/src/com/unciv/logic/automation/` 下的决策树：`Automation` 选择下一步动作（建城、研究、攻击、防御），`BarbarianManager` 处理野蛮人，`NextTurnAutomation` 把决策落到具体 `MapUnit` / `Tile` / `City` 上。
5. **回合结算**。`TurnManager.endTurn()` 计算产出、消耗、升级、随机事件；`BackwardCompatibility` 在最后跑一遍迁移，把旧存档数据补齐成新版本 schema（这是 4.x 系列兼容旧存档的关键机制）。
6. **UI 刷新**。LibGDX 渲染线程在下一帧通过 `WorldScreen.update()` 把新的 `GameInfo` 状态显示出来；网络对战场景下，服务器把序列化后的 `GameInfo` 通过 WebSocket 推送给所有客户端。

理解这条链路再看性能优化，瓶颈就清晰了：AI 决策树是回合内最重的部分（数个文明 × 数十个城市 × 数百单位）；`core/` 的"分领域管理器"设计让单回合只触发相关领域代码，不做整库扫描。这也是 Unciv 在低端 Android 上能跑 8 个 AI 文明的标准对局的根本原因。

## Moddability：把 JSON 当成产品 API

Unciv 把"Moddability"做成了产品级能力，而不是 README 里的口号。`docs/Modders/Mods.md` 直接给出了三种 Mod 类型：扩展 Mod（在现有规则集基础上加内容）、基础规则集 Mod（完全替换规则集）、视听 Mod（仅改图像、音效、UI 皮肤）。这套设计有几个工程含义：

- **规则描述完全 JSON 化**。`android/assets/jsons/` 下是 Units、Nations、Buildings、Improvements、Resources、Terrains、Policies、Beliefs、Quests 等十多个 JSON 文件；Mod 只是在同结构目录下覆盖或新增。
- **Mod 加载是目录扫描**。游戏启动时扫描 `mods/` 目录（桌面端放在 JAR 同目录），按 ModOptions 配置决定是叠加还是替换规则集；Mod 之间按文件名顺序合并。
- **图像、音效、UI 皮肤都是资源覆盖**。`Images/` 下的贴图按规则集 ID 命名，Mod 放同名文件即覆盖；UI 皮肤、tileset、unitset 都是这套机制。
- **不能加新机制**。仓库作者在 `Mods.md` 明确写："The game only knows how to recognize existing definitions, so you can't add *new* unique abilities to nations/units/buildings/etc, only play around with existing ones"——这是有意为之的边界：扩展只能复用现有 unique 表达式，不能 fork 游戏代码。

工程上最值得借鉴的设计：**Moddability 的边界 = `core/` 中规则的 JSON 化深度**。Unciv 把每一个"可调参数"都做成 JSON 字段并暴露文档，把每一个"不可调逻辑"留在 Kotlin 里。Modder 永远不会需要 PR，Forker 也不需要。

## Docker headless：在服务器上跑 Unciv

Unciv 的 `Dockerfile` 是仓库里最容易被忽视、却最有意思的一段。它用 `accetto/ubuntu-vnc-xfce-opengl-g3` 作为基础镜像（带 OpenGL 的 VNC Ubuntu），通过 `gradle desktop:packrLinux64` 打包桌面端，最后再叠加一个 runtime 镜像，把整个 Unciv 桌面跑在 headless VNC（无显示器时通过 VNC 远程访问桌面）里：

```bash
# README 给出的最小化路径
docker run -d -p 6901:6901 -p 5901:5901 ghcr.io/yairm210/unciv
# 然后浏览器访问
http://localhost:6901/vnc.html?password=headless
```

这套部署的工程含义：

- **`docker-compose.yml` 是一份文件**（不是目录），只有一个 service，意味着 Unciv 不需要数据库或外部依赖；所有存档都写本地文件系统。
- **底层是桌面程序 + VNC**，不是 WebAssembly 也不是 Web 前端。这意味着渲染走 OpenGL、键盘鼠标事件由 VNC 桥接，性能接近原生；但代价是无法在浏览器里直接玩，必须通过 noVNC 客户端连接。
- **`deploy/Unciv-Linux64.zip` 是发行产物**。CI 跑 `gradle desktop:zipLinuxFilesForJar` + `desktop:packrLinux64` 后产出单文件可分发包；这才是桌面用户的真正交付物，Docker 镜像主要是给 CI、自动化测试、远程玩家准备的。

## 上游 Civ 机制覆盖度：哪些写了、哪些没写

README 把 Roadmap 写得很清楚：

```text
* Polish!
    * UI+UX improvements
    * Better automation, AI etc. in-game
* G&K mechanics - see #4697
* BNW mechanics - trade routes, world congress, etc.
```

理解这段 Roadmap 要搭配"作者立场"来看：

- **只做 Civ V 原版 + DLC 的内容**。`Mods.md` 明确："If it's in the original Civ V, then yes! If not, then the feature won't be added to the base game — possibly it will be added as a way to mod the game"——这条边界是产品级承诺，避免社区漫无边际的 feature creep（功能蔓延，需求失控性增长）。
- **G&K（Gods & Kings）正在做**。issue #4697 是这一阶段的 tracking issue；BNW（Brave New World）的贸易路线与世界大会等机制排在 G&K 之后。
- **不做 Civ VI 机制**。README："Considering how long it took to get this far, no."
- **不做 iOS、Steam**。前者因为付费 + 测试门槛，后者因为 Steam 担心与 Firaxis 的法律风险——这两个都是工程外的取舍，但作者把它写进了 README 防止用户提 issue 追问。

这套"边界 > 增长"的取舍是 Unciv 能在 11 年（仓库 2015 年起算到 2026 年）保持单作者主导 + 社区贡献节奏的关键。没有这条边界，4.x 早就被 feature creep 拖死了。

## 构建与贡献：从零跑起来

仓库 `docs/Developers/Building-Locally.md` 给出了两条路径：

- **Android Studio（推荐）**。Clone 后用 Android Studio 打开，Gradle 会自动同步；如果首次同步失败，多半是 Android SDK Build-Tools 35.0.0 没装，装好后重启 Studio 即可。Android Studio 会自动生成三个 Run Configuration：`android`、`Desktop`、`Run unit tests`。
- **命令行**。Linux/macOS 用 `./gradlew desktop:run` 启动桌面端；`./gradlew server:run` 启动多人服务；`./gradlew desktop:dist` + `desktop:packrLinux64` 打 Linux 单文件包。

环境上一个值得记的小坑：**Android Studio 默认 run config 的 working directory 必须设为 `$ProjectFileDir$/android/assets`**，否则会报 `docs/uniques.md (No such file or directory)` 错误——这是因为游戏运行时从 working dir 加载 JSON 规则集，没设对就读不到。这是 LibGDX 桌面工程的通用习惯，新人最容易踩。

## 谁该用、谁可以等

适合选 Unciv 的场景：

- 想在低端 Android 设备（4GB RAM 以下的入门机）玩 Civ V 风格的 4X 游戏；
- 想为 Civ V 设计自定义 Mod，但 Civ V 原版 Workshop 工具链不友好；
- 想学习 Kotlin Multiplatform + LibGDX 的工程实践，Unciv 是公开仓库里结构最清晰的样本；
- 想搭建 Civ V 风格的多人对战服务，`server/` 模块可直接复用。

可以再等等或换方案的场景：

- 追求 Civ V 原版画质与 BGM——Unciv 明确写"If you want high-res graphics, amazing soundtracks, animations etc, I highly recommend Firaxis's Civ-V-like game, 'Civilization V'"；
- 想做 Civ VI / Humankind 风格的玩法——Unciv 边界明确写"只做 Civ V"；
- 团队级多人对战的稳定性需求——`server/` 仍由单作者维护，事务、观战、回放等企业级功能尚不完善。

## 边界与未覆盖

- 本文没有展开 `core/src/com/unciv/logic/automation/` 下 AI 决策树的实现细节——这部分是 Unciv 最有技术含量的部分，但代码量大、需要结合单个 PR 看；后续可单独写一篇源码分析。
- 本文没有涉及 `core/` 中 Purity 自定义编译插件（`buildSrc/` 下）的内部实现——这是作者为约束函数纯度写的 Kotlin 编译插件，对提升代码可读性有显著作用，但需要单独拆解。
- 本文没有跑 benchmark。仓库没有公开"AI 决策耗时""存档加载延迟""多人回合同步延迟"等数字，规模化评估只能结合自己压测；不要直接套用其它 4X 游戏的通用经验。

Unciv 是一份"边界清晰 + 工程克制"的开源答案：核心玩法完整、Moddability 真实、跨端交付完整，剩下的取舍在"DLC 进度"和"iOS/Steam 等发行边界"上。

## 一句话回顾

Unciv 用 Gradle 多模块 + Kotlin Multiplatform 把游戏规则、UI、跨端入口拆得干净，所有规则 JSON 化、Moddability 真实可玩、Docker headless 让 CI 与远程玩家都能跑起来。它的工程价值不在"重制 Civ V"，而在"用一套开源工程纪律约束一个长期单人项目"。要不要学它，看的是"是否想用 Moddability + 跨端 JVM 重写一款中度复杂度的产品"。