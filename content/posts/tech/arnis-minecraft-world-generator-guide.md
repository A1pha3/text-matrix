---
title: "Arnis：18K Stars·Minecraft真实世界地图生成器·OpenStreetMap地理数据"
date: "2026-04-12T02:31:39+08:00"
slug: arnis-minecraft-world-generator-guide
github_repo: "louis-e/arnis"
source_key: "gh:louis-e/arnis"
description: "Arnis 用 OpenStreetMap 矢量数据、卫星高程和 ESA WorldCover 地表分类生成 Minecraft 世界，支持 Java、Bedrock 和 Luanti 三个目标，还能用 NASA 高程生成月球和火星。本文按 v3.2.0 拆解它的数据流水线、参数体系和部署方式。"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "OpenStreetMap", "Minecraft", "GIS"]
---

# Arnis：用 OpenStreetMap 把真实城市搬进 Minecraft

Arnis 把 OpenStreetMap（OSM）的矢量地理数据转换成 Minecraft 方块世界。它读入 `building`、`highway`、`waterway` 等标签，叠上卫星高程和 ESA WorldCover 地表分类，生成可进入、可踩、可挖的世界，输出同时覆盖 Java 版（1.17+）、Bedrock 版和 Luanti（Minetest）。仓库用 Rust 写成，提供 Tauri 图形界面和无 GUI 的命令行两条入口，桌面探索和服务器批量生成都能覆盖。

项目由 Louis Erbkamm（louis-e）于 2022 年发起，2024 年 12 月出圈后持续高频迭代。截至 2026-09-18，已有约 18,000 Stars、1,500 Forks、63 位贡献者，最新版本是 2026-09-09 发布的 v3.2.0「Horizon Update」。迭代速度意味着参数会变——本文所有命令和参数都对照 v3.2.0 的 `src/args.rs` 核实过，版本更迭后请以仓库 README 和 `--help` 输出为准。

## 学习目标

读完本文，你能够：说清 Arnis 的数据从哪来、经过哪些处理、写到哪去；在 GUI 或命令行跑通第一次生成；按场景选对生成模式和参数；判断自己的需求适不适合交给它。

## 目录

- [项目速览](#项目速览)
- [快速上手](#快速上手)
- [数据流水线](#数据流水线)
- [架构与模块](#架构与模块)
- [参数与调优](#参数与调优)
- [横向对比与采用建议](#横向对比与采用建议)
- [资源与延伸](#资源与延伸)
- [常见问题](#常见问题)
- [自测题](#自测题)
- [进阶路径](#进阶路径)

## 项目速览

> "Arnis creates complex and accurate Minecraft Java Edition (1.17+), Bedrock Edition, and Luanti (Minetest) worlds that reflect real-world geography, topography, and architecture."
> —— Arnis README

| 指标 | 数值（2026-09-18 快照） |
|------|------|
| Stars / Forks | 17,963 / 1,509 |
| 贡献者 | 63+ |
| 最新版本 | v3.2.0「Horizon Update」（2026-09-09） |
| 许可证 | Apache-2.0（Luanti 映射表文件另行遵循 LGPL-2.1+） |
| 主语言 | Rust（GUI 通过 Tauri 桥接） |
| 官网 | [arnismc.com](https://arnismc.com) |

能力边界：

| 维度 | 支持情况 |
|------|----------|
| 输出目标 | Java 1.17+、Bedrock、Luanti（Minetest） |
| 生成模式 | `geo-terrain`（默认，真实地形 + OSM 对象）、`geo-only`（平地 + OSM 对象）、`terrain-only`（只生成真实地形） |
| 天体 | 地球之外，`--body moon` / `--body mars` 用 NASA PDS 高程生成月球和火星表面 |
| 数据源 | OpenStreetMap 矢量、卫星高程（默认 Mapterhorn + 区域高分辨率源）、ESA WorldCover 地表分类、可选 Overture Maps 补充建筑 |
| 入口 | GUI（Tauri）+ CLI + Nix flake + 浏览器版 MapSmith |
| 平台 | Windows / macOS / Linux |

## 快速上手

### 三种安装方式

**方式一：下载预编译版本**。到 [GitHub Releases](https://github.com/louis-e/arnis/releases/latest) 拿对应平台的包。v3.2.0 提供 Windows exe、macOS universal、Linux tar.gz 和 AppImage 四种产物，解压即用。

**方式二：源码编译**

```bash
git clone https://github.com/louis-e/arnis.git
cd arnis

# GUI 版
cargo run --release

# 无 GUI 的命令行版
cargo run --release --no-default-features -- \
  --output-dir="YOUR_PATH/.minecraft/saves/worldname" \
  --bbox="min_lat,min_lng,max_lat,max_lng"
```

无 GUI 版本不依赖 Tauri 的 WebKit，编译产物更小，适合服务器和无显示器的 Linux 主机。

**方式三：Nix 直接运行**

```bash
nix run github:louis-e/arnis -- \
  --output-dir=YOUR_PATH/.minecraft/saves/worldname \
  --bbox="min_lat,min_lng,max_lat,max_lng"
```

### GUI：框选即生成

启动图形界面后三步：在地图上用矩形工具框选目标区域，选择一个 Minecraft 世界，点 **Start Generation**。界面里还可以调世界比例、出生点、建筑室内生成等选项。

GUI 适合首次探索和小范围验证。需要批量生成或脚本化时，切到 CLI。

### CLI：可脚本化的参数化生成

```bash
cargo run --release --no-default-features -- \
  --output-dir="~/.minecraft/saves/MyWorld" \
  --bbox="40.7128,-74.0060,40.7580,-73.9855"
```

最小命令只需要两个参数：`--output-dir` 指定世界输出目录，`--bbox` 指定经纬度边界框。四个值按 `min_lat,min_lng,max_lat,max_lng` 排列，对应矩形区域的西南角和东北角。坐标可以从 OpenStreetMap 网站导出，也可以用 [bboxfinder](http://bboxfinder.com/) 交互式框选后复制。

注意两个历史包袱：老版本教程里的 `--terrain` 现在是被接受但不生效的占位参数（地形默认开启，想要平地用 `--mode geo-only`）；`--path` 是 `--output-dir` 的废弃别名，新脚本用后者。

## 数据流水线

### 从查询到落盘

```
bbox (min_lat,min_lng,max_lat,max_lng)
        │
        ▼
┌─────────────────────────────────────────────────────┐
│ 1. Overpass API 查询                                 │
│    按 bbox 拉取 OSM 节点/路径/关系                    │
│    （terrain-only 模式跳过此步）                      │
├─────────────────────────────────────────────────────┤
│ 2. 可选：Overture Maps 补充建筑（--overture）         │
│    补上 OSM 缺失的卫星识别建筑足迹                    │
├─────────────────────────────────────────────────────┤
│ 3. 高程拉取                                          │
│    默认 Mapterhorn + 区域高分辨率源（如 USGS 3DEP）   │
│    --aws-only-elevation 回退 AWS Terrain Tiles(~30m) │
│    月球/火星走 NASA PDS                               │
├─────────────────────────────────────────────────────┤
│ 4. ESA WorldCover 地表分类（10m 分辨率）              │
│    决定地表材质：林地/草地/耕地/建成区/水体等          │
├─────────────────────────────────────────────────────┤
│ 5. 坐标投影与方块映射                                 │
│    经纬度 → Minecraft XZ，海拔 → Y 轴                 │
│    OSM 标签按类型分派给近 30 个处理子模块             │
├─────────────────────────────────────────────────────┤
│ 6. 世界写入                                          │
│    Java: region 文件 + level.dat                      │
│    Bedrock: .mcworld    Luanti: map.sqlite            │
└─────────────────────────────────────────────────────┘
```

各阶段耗时构成不同：Overpass 查询受服务端限流和区域大小约束，bbox 越大等待越久，超时会被截断；高程和地表分类是网络拉取，受带宽和缓存影响；方块写入是 CPU 和磁盘 I/O，Rust 端用 rayon 自动并行，不需要手动指定线程数。三个环节里网络拉取占大头，所以小 bbox 总是更稳。

### OSM 元素到方块的映射

Arnis 把 OSM 标签翻译成方块的工作分派给 `src/element_processing/` 下的近 30 个子模块——`buildings.rs` 管建筑、`highways.rs` 管道路、`waterways.rs` 管水系、`railways.rs` 管铁路，`landuse.rs`、`leisure.rs`、`tourisms.rs`、`historic.rs` 各管一摊，甚至还有 `advertising.rs` 处理广告牌、`power.rs` 处理电力设施。标签越全，还原越细。

建筑是做得最深的一块。高度优先认 OSM 的 `height` 标签，没有就按 `building:levels` 层数换算：住宅类每层约 3 格，商业和公共建筑每层 4 格，屋顶类型（山墙或平顶）按建筑类型和足迹自动选。代码里还有一条摩天楼判据——高度超过 120 格（随 scale 缩放）且满足「高度 ≥ 40 格并且不小于 footprint 最长边的两倍」的比例条件，才套用专门的摩天楼造型（全高竖向鳍片立面）。这些规则意味着：标签完整的城市中心能生成出层次分明的天际线，标签稀疏的小城镇则只能得到低矮的普通楼体。Arnis 按标签生成，无法凭空补全——数据缺了，去 OSM 补。

道路默认铺灰色混凝土粉末和青色陶瓦的混合路面，认 OSM 的 `surface=*` 标签选材质。宽度按道路等级换算成横向格数，主干道比小巷宽得多。

### 地表与水体：卫星分类打底，OSM 标签覆盖

这是理解 Arnis 生成效果的关键一环，也是它和「只查 OSM」的工具最大的差别。

地表材质的第一层来自 ESA WorldCover 2021 卫星数据：10 米分辨率、11 个地表类别（林地、灌木、草地、耕地、建成区、水体、红树林等），托管在 AWS S3 上切成 3×3 度的 Cloud-Optimized GeoTIFF 瓦片。Arnis 用 HTTP Range 请求只读需要的那一小块，避免整块下载约 500 MB 的瓦片。有了这一层，一块区域是森林还是农田，不依赖当地 OSM 贡献者画没画过 `landuse`——卫星看过就算数。

第二层是 OSM 标签覆盖：同一块地上，如果 OSM 有明确的 `landuse`、`natural` 标签，以标签为准；水体的岸线也用 OSM 数据修正卫星分类的锯齿（源码里的 `osm_land_override.rs` 和 `osm_water_override.rs` 干的就是这件事）。湖海这些大面积水域来自 WorldCover 的水体类别，河流运河这类线状水系来自 OSM 的 `waterway`。

### 建筑立面、树木与 3D 道具

v3.x 还加了三层细节，默认开启、都能关掉：

- **建筑立面**：`--building-facades` 用 Mapillary 街景影像给建筑生成贴图立面（需自备 Mapillary API 令牌），配合 `--facade-detail`、`--facade-px` 控制精细度。
- **树木**：默认放内置的 schematic 树包（按真实树种建模的预制结构），`--max-tree-size` 限制最大树型（small≤6 格、medium≤12、big≤20、tall≤28、giant）；`--legacy-trees` 退回旧的程序化生成树。`--canopy-height` 则改用 Meta/WRI 全球树冠高度图决定树的位置和大小，比「看到林地就撒树」准确得多。
- **3D 道具**：默认加载外部 3D 模型（3DMR 与 Wikimedia 来源）和内置道具（汽车、船、起重机等），`--use-3d` 一个开关全部关闭。

## 架构与模块

```
arnis/
├── src/
│   ├── main.rs               # 入口与编排
│   ├── args.rs               # CLI 参数定义（约 1500 行，参数的唯一事实来源）
│   ├── retrieve_data.rs      # Overpass/curl/wget 下载与截断检测
│   ├── osm_parser.rs         # OSM 数据解析
│   ├── elevation/            # 高程：provider 选择、缓存、后处理
│   ├── land_cover/           # ESA WorldCover 拉取、岸线修正、OSM 覆盖
│   ├── element_processing/   # 近 30 个 OSM 标签处理子模块
│   ├── coordinate_system/    # 坐标系与 bbox
│   ├── projection/           # 经纬度 → 方块坐标投影
│   ├── block_definitions.rs  # 方块定义
│   ├── world_editor/         # 世界写入
│   ├── trees/                # 树包与树生成
│   ├── building_facades/     # 建筑立面（Mapillary 影像）
│   └── gui/                  # Tauri 图形界面
├── capabilities/             # Tauri 能力声明
├── Cargo.toml
└── tauri.conf.json
```

结构上的分界线很清楚：数据获取（Overpass、高程、WorldCover）、数据处理（解析、投影、标签分派）、世界写入（Java/Bedrock/Luanti 各自的方块映射）三层互相独立。要加一种新的地物，改 `element_processing/` 里对应的子模块；要接一个新的高程源，在 `elevation/providers/` 里加一个 provider（现成五个：Mapterhorn、AWS Terrain Tiles、USGS 3DEP、NASA Planetary、区域源）。

## 参数与调优

### 常用参数

| 参数 | 默认 | 说明 |
|------|------|------|
| `--output-dir` | 必填 | 世界输出目录（`--path` 为废弃别名） |
| `--bbox` | 必填 | 边界框 `min_lat,min_lng,max_lat,max_lng` |
| `--mode` | `geo-terrain` | `geo-only` 平地加对象；`terrain-only` 只生成真实地形 |
| `--scale` | 1.0 | 方块数/米，1.0 为真实尺寸，允许 0.05–4.0 |
| `--ground-level` | — | 世界地面高度 |
| `--spawn-lat` / `--spawn-lng` | bbox 中心 | 出生点经纬度，需落在 bbox 内 |
| `--rotation` | 0 | 顺时针旋转角度，范围 -90 到 90 |
| `--interior` | 关 | 生成建筑室内 |
| `--fillground` | 关 | 填充地下并生成矿脉（生存模式可玩性的基础） |
| `--bedrock` / `--luanti` | 关 | 输出 Bedrock `.mcworld` 或 Luanti `map.sqlite` |
| `--file` / `--save-json-file` | — | 读入/保存本地 OSM JSON，便于复用同区域数据 |

完整参数以 `src/args.rs` 和 `--help` 输出为准。v3.x 的完整清单还包括 `--overture`、`--canopy-height`、`--building-facades`、`--disable-height-limit`（实验性，Java 1.21.4+ 可把建筑高度上限扩展到 Y=-2032..2031）等，上文相关小节已各自说明。

### scale：最容易误读的参数

`--scale` 的语义是每米对应几个方块，1.0 就是真实尺寸：一栋 30 米宽的楼生成 30 格宽。它不是「缩放倍数越大世界越大越粗糙」，两个方向都有代价——调大（如 2.0）放大细节，城市可探索性更好，但 Overpass 拉取范围不变、方块数量翻倍，生成时间和存档体积都上去；调小到 0.3 以下，代码会自动跳过建筑道路等对象（塞不下），只剩地形。想生成大范围又保留对象，正确做法是缩 bbox，而不是压 scale。

### 大区域与 Overpass 限流

Overpass 是公共免费服务，bbox 拉太大轻则慢、重则查询被截断。三个办法按顺序试：

1. **缩小 bbox**，分多次生成各自独立的世界，要拼大地图就用 MCEdit 类工具后期合并；
2. **`--save-json-file` 存下 OSM 数据，`--file` 复用**，调试参数时反复生成不必反复查询；
3. 只要地形不要建筑时用 `--mode terrain-only`，直接跳过 Overpass 查询。

### 服务器部署

```bash
# 无 GUI 编译，避开 Tauri 的 WebKit 依赖
cargo build --release --no-default-features

# 产物拷到服务器直接跑
scp target/release/arnis user@server:/path/to/minecraft/
```

线程数由 rayon 按 CPU 核数自动分配，没有 `--jobs` 这类手动并行参数。服务器上跑批生成时，真正的限制是 Overpass 限流和磁盘写入，不是 CPU。

## 横向对比与采用建议

| 工具 | 数据来源 | 定位 |
|------|----------|------|
| **Arnis** | OSM + 卫星高程 + WorldCover | 从真实地理数据自动生成，Java/Bedrock/Luanti 三目标 |
| **MapSmith**（官方） | 同 Arnis | 浏览器版，无需安装，适合移动端和更大地图 |
| **WorldPainter** | 手工绘制 | 交互式手绘地形，创作自由度高，但不自动还原真实城市 |

同类「真实数据驱动」的工具里，Arnis 是数据源最全、迭代最活跃的一个。按场景给建议：

1. **想看自己家在 Minecraft 里长什么样**：GUI 或 MapSmith，框选小区块，几分钟出结果。
2. **城市级还原或教学项目**：CLI，先小区域验证参数，再扩大范围；教学场景留意 `--fillground`，默认世界没有地下矿脉。
3. **服务器批量生成**：`--no-default-features` 编译，用 `--file`/`--save-json-file` 复用 OSM 数据，尊重 Overpass 限流。
4. **二次开发**：改标签映射去 `element_processing/`，加数据源去 `elevation/providers/` 或 `land_cover/`，参数定义集中在 `args.rs`。

不适合的场景：实时多人联机（生成是离线批处理）、超大范围一次生成（Overpass 和内存都顶不住）。

## 资源与延伸

| 资源 | 链接 |
|------|------|
| 官网（唯一官方下载源之一） | https://arnismc.com |
| GitHub 仓库 | https://github.com/louis-e/arnis |
| 文档 Wiki | https://github.com/louis-e/arnis/wiki |
| 发布页 | https://github.com/louis-e/arnis/releases |
| 问题反馈 | https://github.com/louis-e/arnis/issues |
| Discord | https://discord.gg/mA2g69Fhxq |
| MapSmith（浏览器版） | https://arnismc.com/mapsmith/ |
| ESA WorldCover 数据 | https://esa-worldcover.org/ |

项目出圈后被多家媒体报道并进入学术论文：AWS 公共部门博客 [Building Realistic Minecraft Worlds with Open Data](https://aws.amazon.com/de/blogs/publicsector/building-realistic-minecraft-worlds-with-open-data-on-aws-how-arnis-uses-elevation-datasets-at-scale/)（讲它如何大规模使用高程数据集）、Hackaday、Tom's Hardware、XDA Developers 的报道，以及 K-12 洪水教育的 Floodcraft 论文。原始链接都在仓库 README 里。

⚠️ **安全提示**：README 明确声明 arnismc.com 和 github.com/louis-e/arnis 是仅有的官方渠道，其他声称与项目有关的下载站都可能带恶意软件。

## 常见问题

**生成的世界能直接玩生存模式吗？**
基础生成只覆盖地形、建筑和环境。加 `--fillground` 会填充地下并生成矿脉，这是生存模式的基本条件；怪物、村庄这类游戏性内容不在生成范围内，进游戏后按需补。

**建筑看起来千篇一律？**
大概率是当地 OSM 标签稀疏。去 OpenStreetMap 补充建筑类型和层数标签，下次生成立刻变好——这也是给项目做贡献最直接的方式。想改映射规则本身，fork 后改 `element_processing/` 对应模块。

**Overpass 查询很慢或失败？**
缩小 bbox，或用 `--file` 复用已保存的 OSM 数据。只要地形时切 `--mode terrain-only`，完全不碰 Overpass。

## 自测题

1. Arnis 的三个生成模式分别适合什么场景？`--terrain` 参数现在是什么行为？
2. 建筑高度优先认哪个 OSM 标签？每层换算成多少格？
3. 地表材质为什么以 ESA WorldCover 卫星分类打底，OSM 标签在什么情况下覆盖它？
4. `--scale` 设成 0.2 会发生什么？想生成大范围又保留建筑，正确做法是什么？
5. 在服务器上批量生成时，瓶颈通常在哪两个环节？为什么没有 `--jobs` 参数？

## 进阶路径

建议按这个顺序深入：

1. **GUI 快速验证**——预编译版框选自家小区，建立对生成质量的直觉。
2. **CLI 参数实验**——试 `--scale`、`--interior`、`--fillground`、`--mode` 的组合，观察存档差异。
3. **读 `args.rs`**——所有参数的注释都在这一个文件里，是理解能力边界的最快路径。
4. **改一个映射规则**——从 `element_processing/` 挑一个子模块，让某种标签生成你想要的方块，给上游提 PR（README 承诺合并后会定期发版）。
5. **反哺 OSM**——发现家乡数据不完整就去补标签，这是所有下游工具受益的改进。

延伸阅读：[OpenStreetMap Wiki](https://wiki.openstreetmap.org/)（标签体系）、[ESA WorldCover](https://esa-worldcover.org/)（地表分类数据）、仓库 Wiki 的技术解释与路线图。

---

## 资料口径说明

本文的事实核查基线：GitHub 仓库元数据与 README、`src/args.rs` 参数定义、`src/land_cover/mod.rs`、`src/element_processing/buildings.rs`、`highways.rs`、`src/elevation/` 与 `src/land_cover/` 模块源码，均为 2026-09-18 的 main 分支快照（对应 v3.2.0 发布后）。Stars、Forks、贡献者数取自 GitHub API 当日返回值。

已知边界：Arnis 迭代很快，参数名和默认值可能随版本变化，v2.x 时代的教程（含本文旧版）中的 `--path`、`--terrain`、`--water-level` 等用法已失效或语义变化；生成效果取决于当地 OSM 数据质量；本文未实际运行全部参数组合，涉及行为的描述均以源码注释和 README 为据。
