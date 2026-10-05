---
title: "rommapp/romm：ROM 收藏的出路不是更好的前端，是一个多用户的库后端"
date: "2026-07-03T20:57:00+08:00"
lastmod: "2026-09-30T00:00:00+08:00"
draft: false
slug: "rommapp-romm-self-hosted-rom-manager-guide"
description: "romm 是一款自托管 ROM 管理器与播放器：扫描识别、十多个元数据源、浏览器模拟器与服务端串流、多用户权限与跨设备存档同步。本文按 v5.3.1 口径拆解其架构与采用边界。"
categories: ["技术笔记"]
tags: ["自托管", "Python", "游戏"]
author: "text-matrix"
---

## 本文导读

读完本文你将能够：

- 说清 romm 与 EmulationStation 这类前端解决的是两个不同层面的问题
- 看懂 romm 的扫描识别流程：文件名解析、哈希计算、多源元数据聚合
- 理解它的多用户模型：角色与权限组、会话与令牌、设备绑定与存档同步
- 知道四种浏览器模拟器运行时各自覆盖什么，串流模式如何把 PS3/Switch 这类平台带进浏览器

> 口径说明：本文以 romm v5.3.1（2026-09-23 发布）为基准，仓库数据核实于 2026-09-30。romm 迭代很快，文中 API 端点与功能清单以仓库的 `docs/BACKEND_ARCHITECTURE.md` 与官方文档站 docs.romm.app 为准。

---

## 一、先给判断

EmulationStation、RetroBat、LaunchBox 这些工具解决的是「在一台设备上把游戏库呈现好」。但收藏量上去之后，真正麻烦的是另一层问题：几十个平台的 ROM 散在多块硬盘上，元数据要靠脚本抓，几个家庭成员的存档互相覆盖，想在客厅玩还得先把文件拷过去。

romm（ROM Manager）做的事情是把这一层抽成一个自托管服务：一个 FastAPI 后端管扫描、识别、元数据、权限和存档，一个 Vue 3 前端负责浏览和游玩，浏览器里直接用模拟器运行时跑游戏。它不是「网页版的 EmulationStation」——前者是库后端，后者是本地前端，两者甚至可以配合使用。

这个项目 2023 年 3 月创建，目前 13,200+ Stars、AGPL-3.0，版本号已经走到 5.3.1。它能持续涨星，靠的不是某个明星功能，而是把「扫描、识别、多用户、多端」这四件事都做成了开箱即用的整体。

---

## 二、系统地图

romm 的代码分两大块，仓库顶层一目了然：

| 组件 | 职责 | 技术栈 |
| --- | --- | --- |
| `backend/` | REST API、扫描调度、元数据聚合、用户与权限、后台任务 | FastAPI、SQLAlchemy 2.0、Alembic、RQ 任务队列、Socket.IO |
| `frontend/` | 游戏库浏览、模拟器启动、控制台模式（Console Mode） | Vue 3.5、Vite、TypeScript、Pinia、Socket.IO |

部署形态是一个容器 + 一个数据库：官方示例 `examples/docker-compose.example.yml` 只有两个服务——`romm` 和 `romm-db`（MariaDB，也支持 MySQL 和 PostgreSQL）。会话、任务队列和缓存用的 Redis/Valkey 默认连 `127.0.0.1`，也就是主容器内置的实例，小规模部署不必单独起服务。

后端的分层在仓库自带的 `docs/BACKEND_ARCHITECTURE.md`（2100+ 行）里写得很清楚：endpoints 层做请求校验，handler 层放业务逻辑（扫描、元数据、文件系统、鉴权），adapters 层封装十多个外部 API 客户端，models 层是 SQLAlchemy 模型。实时通信走两条 Socket.IO 通道——`/ws` 推扫描进度和通知，`/netplay` 管联机房间。文件变化由 watchfiles 监视库目录，检测到新增 ROM 自动触发重扫。

---

## 三、扫描与识别：一个 ROM 文件进来会发生什么

这是 romm 最核心的机制，值得整个拆开讲。

### 1. 目录即平台

romm 不需要你在网页里逐个建平台。把文件放进库目录，扫描器按文件夹发现平台：

```text
library/
├─ roms/
│  ├─ gbc/
│  │  ├─ game_1.gbc
│  │  └─ game_4/          # 多文件游戏用子文件夹
│  │     ├─ game_4.gba
│  │     └─ dlc/  hack/  manual/
│  └─ ps/
│     └─ game_5/          # game_5_cd_1.iso, game_5_cd_2.iso
└─ bios/
   └─ ps/                 # scph1001.bin
```

文件夹名对上官方 slug（`snes/`、`gba/`）即可，大小写不敏感；Batocera、RetroBat、ES-DE 的命名习惯（如 `megadrive/`）也兼容，其他名字可以在 `config.yml` 里绑定到正确平台。从 EmulationStation 迁移过来时，多数现有目录结构可以直接沿用。

### 2. 文件名解析与哈希

对每个 ROM 文件，扫描器先解析文件名：方括号和圆括号里的标记被拆成区域、语言、修订号、版本等标签（官方例子是 `tetris [1.0001](HACK)[!].gba`），多文件游戏里的 `dlc/`、`hack/`、`manual/` 子目录会作为标签显示在 UI 里。然后计算 CRC32、MD5、SHA1 三个哈希——这是后面一切识别的基础。

有几类特殊处理值得知道：CHD v5 镜像的 SHA1 从文件头提取；PS1、PS2、PSP 有序列号索引表（启动时缓存进 Redis），可以按 serial code 精确命中；MAME 和 ScummVM 有各自的名称索引。Switch 和 PS3/PS4/PS5 这类平台**跳过哈希计算**——它们的 ROM 太大且无对应识别算法，romm 对这些平台做的是库管理而非逐文件识别。

### 3. 十多个元数据源，按优先级聚合

识别不是查单一数据库。romm 把外部服务封装成一组 adapter，扫描时按可配置的优先级依次查询，每个字段取首个命中，手动修改过的元数据拥有最高优先级：

| 用途 | 服务 | 说明 |
| --- | --- | --- |
| 游戏元数据 | IGDB、ScreenScraper、MobyGames、LaunchBox、TheGamesDB | 基础信息、封面、截图、手册 |
| 哈希识别 | Hasheous、PlayMatch | 按 ROM 哈希反查游戏 |
| 成就 | RetroAchievements | 成就与进度，配套 RAHasher 算专属哈希 |
| 游玩时长 | HowLongToBeat | 通关时间估算 |
| PC 游戏 | Steam | PC 平台的商店元数据 |
| Flash/浏览器游戏 | Flashpoint | Browser 平台的数据源 |
| 封面艺术 | SteamGridDB | 多尺寸 Grid、Logo、图标 |
| 本地数据库 | gamelist.xml、Libretro 缩略图 | 读取已有前端的数据 |

官方 compose 示例里预填的推荐配置是 ScreenScraper 账号、RetroAchievements 和 SteamGridDB 的 key——不配 IGDB 也能完整工作。查询词本身做过规范化（去冠词、去标点、Unicode NFKD 归一化），模糊匹配用 Jaro-Winkler 相似度，所以「文件名很脏」的 ROM 也有相当概率命中。

### 4. 六种扫描类型

扫描不是只有「全量」一种：`QUICK` 只扫新文件并对已有文件做对账（仅对新增或变化的文件重新算哈希）；`UNMATCHED` 只重扫没有元数据的 ROM；`HASHES` 专门重算全部哈希。大批量导入时先跑 QUICK、再对漏网之鱼跑 UNMATCHED，比每次全量快得多。扫描进度通过 WebSocket 实时推到前端。

---

## 四、多用户：romm 与本地前端的分界线

这部分是 EmulationStation 们完全不覆盖的层面。

**角色与权限。** 用户只有 admin 和 user 两类：admin 绕过一切权限检查，普通用户的权限完全来自所属权限组加个人覆盖（早期版本 viewer/editor 的划分已并入权限组）。权限粒度是 22 个 scope，从 `roms.read`、`collections.write` 到 `tasks.run`，可以精确控制一个账号「只能看、不能删」。另有 Kiosk 模式发放匿名只读身份，适合客厅机。

**登录方式。** 网页端主链路是服务端会话：登录后发 `romm_session` cookie（默认 14 天，会话存 Redis），配合 CSRF 双提交校验。API 客户端走另一条路：OAuth2 密码模式拿 JWT（30 分钟，配 7 天 refresh token），或者创建 `rmm_` 前缀的 client token——后者带 scope、可设过期、以 SHA-256 哈希入库，是给第三方客户端用的正式凭证。企业场景可以接 OIDC 单点登录。四条认证链在同一个 `HybridAuthBackend` 里依次尝试。

**设备与存档。** 每个设备（Web、Android 上的 Argosy、muOS 上的 Grout、RetroArch）与账号绑定，存档和即时状态按用户隔离，跨设备同步有三种模式可选：走 API、文件传输、推拉模式（推拉模式支持 SSH 传输）。丈夫的《塞尔达》存档不会被儿子覆盖，Switch 上没打完的进度回家在浏览器里接着玩——这类需求在这个模型里是一等公民。

---

## 五、浏览器游玩：四种运行时，各管一段

romm 内置了四个浏览器模拟器运行时，按平台自动选择：

| 运行时 | 覆盖 | 说明 |
| --- | --- | --- |
| EmulatorJS 4.2.3 | NES/SNES/GBA/PS1 等主流复古平台 | 主力运行时，容器镜像内置 |
| Ruffle | Flash 游戏 | Browser 平台，配合 Flashpoint 元数据 |
| js-dos 8.4.1 | DOS 游戏 | 内置于镜像 |
| FAKE-08 | PICO-8 虚拟主机 | 内置于镜像 |

游玩链路不需要装任何东西：浏览器向后端请求 ROM 文件，命中时由 nginx X-Accel 重定向直接吐给浏览器，交给对应运行时在 WebAssembly 里执行，存档和状态写回后端的用户资产目录。官方文档对「支持」的定义很克制：约 400 个平台的清单里，「支持」指文件夹识别加至少一家元数据源覆盖；EmulatorJS 是否有可玩核心在平台表里逐个标注。对没有内嵌核心的平台，还有第二条路。

**模拟器串流**是 5.x 的重头功能：在服务端跑真正的模拟器，把画面、声音和手柄输入经 WebRTC 串给浏览器，官方文档的原话是「你的浏览器只是一块屏幕」。broker 预配的模拟器覆盖了内嵌运行时碰不了的当代平台——PS2 走 PCSX2、PS3 走 RPCS3、PS4 走 shadPS4、Switch 走 Eden、Xbox 360 走 Xenia、Wii U 走 Cemu、3DS 走 Azahar，其余平台由 RetroArch 兜底。代价是部署门槛：独立容器（仅 amd64）、强制 HTTPS、只读挂载 ROM 库、ROM 必须解压，以及服务端真跑得动这些模拟器的算力。轻量路线和重量路线各取所需。不走串流的对战场景走 netplay：`/netplay` 通道负责联机房间管理，房间状态存 Redis，支持密码和人数上限。

前端另有 Console Mode（主机/客厅界面），配合手柄和 Kiosk 匿名模式，就是把一台闲置主机变成游戏厅的用法。

---

## 六、任务流：从一堆文件到浏览器开玩

把前面的机制串成一个真实场景——导入 500 个 ROM 并在手机浏览器上玩其中一个：

1. **放文件**：按平台 slug 把 ROM 拷进 `library/roms/` 对应文件夹，BIOS 放 `library/bios/`。watchfiles 监视到变化，自动入队一次扫描。
2. **扫描**：RQ 的独立扫描 worker 消费任务；解析文件名标签、算三个哈希、按优先级查元数据源；封面和截图下载到 `resources/`，进度实时推到浏览器。
3. **人工兜底**：扫完后在「未识别」列表里处理漏网的——按哈希搜一遍 Hasheous/PlayMatch，再不行手动从任一元数据源选定，手动结果优先级最高。
4. **建账号**：给家人各建一个 user，放进只读或受限权限组；每人收藏自己的游戏，存档天然隔离。
5. **开玩**：手机浏览器登录，点开游戏，EmulatorJS 加载运行；存档写回后端。第二天在 PC 上打开，进度还在；装了 Argosy 的 Android 掌机通过 QR 配对绑定设备后，存档自动同步过去。

这条链路里没有一步需要写脚本——这正是它和「裸文件夹 + 前端」方案的本质区别。

---

## 七、API 与生态

romm 的 API 是它作为「库后端」的正式接口：base URL 是 `/api`，Swagger 在 `/api/docs`，分页、过滤、WebSocket 一应俱全。主要端点组：

- `roms/`：列表（分页、多维过滤）、分块上传（单块 64MB）、多文件读取、内置 ROM 补丁器（打 romhack 和翻译补丁不用下载）、手动、笔记
- `platforms/`、`collections/`、`saves/`、`states/`、`firmware/`
- `music/`：游戏原声播放，曲目按艺术家/专辑/流派/年份分面检索
- `search/`：跨全部元数据源搜索、封面搜索
- `feeds/`：生成 Tinfoil、WebRcade、PKGi 等格式的订阅源——这是和外部启动器对接的正规方式
- `stats/`、`play-sessions/`：库统计与游玩会话

官方客户端三个：**Playnite 插件**（Windows 桌面整合）、**Argosy**（Android，面向 Anbernic、Retroid Pocket 等掌机的手柄优先界面）、**Grout**（掌机自制固件客户端，支持 muOS、Batocera、Knulli、TrimUI 等十种固件，无线下载 ROM 和 BIOS 并自动同步存档）。社区生态里还有 iOS 客户端、SteamOS 的 Decky 插件、Switch homebrew、Discord 机器人等。第三方应用统一走 client token + QR 配对，不需要交出自己的密码。

---

## 八、采用边界

### 适合

- **多平台收藏党**：平台一多，手工维护元数据和封面就崩溃了，扫描识别是刚需
- **家庭/小团队共享一台 NAS**：多用户隔离和存档同步是本地前端给不了的
- **想随处开玩的人**：浏览器即开即玩 + 掌机存档同步，游戏机不用来回拷文件
- **已经有 ES-DE/Batocera 目录结构的人**：目录布局兼容，迁移成本主要是配一次元数据源

### 不太适合

- **只有一个平台、几十个 ROM**：EmulationStation 或 RetroBat 更轻，服务化是过度设计
- **指望零配置玩当代主机**：内嵌运行时只覆盖复古平台，PS3/Switch 这些要串流路线，而串流需要 amd64 宿主机、HTTPS 和跑得动模拟器的算力
- **完全离线环境**：元数据识别依赖外部服务，断网时只剩裸文件管理
- **对资源占用极度敏感**：一个 Python 后端加一个数据库，比静态前端重，树莓派级别设备建议先看官方最低配置

### 起步路径

1. 按[官方 Quick Start](https://docs.romm.app/latest/Getting-Started/Quick-Start-Guide/) 用示例 compose 起服务（`romm` + MariaDB 两个容器）
2. 配元数据源：ScreenScraper 账号免费注册，RetroAchievements 和 SteamGridDB 各拿一个 key，这三样是官方示例的推荐组合
3. 先放 50 个 ROM 跑一遍 QUICK 扫描，检查识别命中率，顺手处理「未识别」列表
4. 有掌机或第二台设备时，再接 Argosy/Grout 并配置存档同步

值得强调的边界是：romm 只管理你合法拥有的 ROM 文件，不提供任何游戏文件本身；BIOS 需要自行放入。它把「收藏管理」这件麻烦事做成了服务，但每一份 ROM 的来源合规，仍然是使用者自己的责任。

对于已经积累了几十个平台 ROM 的玩家，romm 的价值可以用一句话概括：它把元数据、多用户、多端同步这三件「自己拼脚本」的事变成了部署一次就能用的整体——而它的 AGPL-3.0 许可和「无追踪、无付费功能」的承诺，让这套东西的门槛只剩下一台常开的主机。
