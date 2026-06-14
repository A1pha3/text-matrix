---
title: "Arnis：14.8K Stars·Minecraft真实世界地图生成器·OpenStreetMap地理数据"
date: "2026-04-12T02:31:39+08:00"
slug: arnis-minecraft-world-generator-guide
description: "Arnis 是一个使用 OpenStreetMap 地理数据生成 Minecraft 真实世界地图的工具，使用 Rust 语言编写，支持高性能渲染。"
draft: false
categories: ["技术笔记"]
tags: ["Minecraft", "Rust", "OpenStreetMap", "地理数据", "游戏"]
---

Arnis：.K Stars·Minecraft 真实世界地图生成器·OpenStreetMap 地理数据·Rust 高性能

一、项目概述

. Arnis 是什么

**Arnis** 是一个将**真实世界地理位置**转换为**Minecraft 世界**的开源工具。

> "Arnis creates complex and accurate Minecraft Java Edition (1.17+) and Bedrock Edition worlds that reflect real-world geography, topography, and architecture."

. 核心数据

| 指标 | 数值 |
|------|------|
| Stars | **14.8k** ⭐ |
| Forks | 1.2k |
| 贡献者 | 49 |
| 最新版本 | **v2.6.0** (2026-04-07) |
| 许可证 | Apache-2.0 |
| 语言 | Rust 99.8% |

. 核心定位

| 维度 | 说明 |
|------|------|
| 🎮 **Minecraft 生成** | Java 1.17+ 和 Bedrock Edition |
| 🗺️ **真实地理** | OpenStreetMap 数据 |
| 🏔️ **地形还原** | 高程数据 |
| 🏠 **建筑还原** | 真实世界建筑 |
| 🌐 **跨平台** | Windows/macOS/Linux |

. 核心特性

| 特性 | 说明 |
|------|------|
| ✅ **开源免费** | Apache-2.0 许可证 |
| ✅ **多版本支持** | Minecraft Java 1.17+ / Bedrock |
| ✅ **地理数据** | OpenStreetMap |
| ✅ **高程数据** | 真实地形 |
| ✅ **跨平台** | Windows/macOS/Linux |
| ✅ **GUI + CLI** | 图形界面和命令行 |

二、快速开始

. 下载安装

**方式一：下载预编译版本**

1. 访问 [GitHub Releases](https://github.com/louis-e/arnis/releases/latest)
2. 选择对应平台的二进制文件
3. 解压并运行

**方式二：源码编译**

```bash
克隆仓库
git clone https://github.com/louis-e/arnis.git
cd arnis

编译（无 GUI）
cargo build --release --no-default-features

或编译（有 GUI）
cargo build --release
```

**方式三：Nix 一键运行**

```bash
nix run github:louis-e/arnis -- --terrain --path="YOUR_PATH/.minecraft/saves/worldname" --bbox="min_lat,min_lng,max_lat,max_lng"
```

. GUI 使用

```bash
启动图形界面
cargo run
```

操作步骤：
1. 在地图上使用矩形工具选择区域
2. 选择 Minecraft 世界
3. 点击 "Start Generation" 开始生成

. CLI 使用

**命令行生成地形**：

```bash
cargo run --no-default-features -- \
 --terrain \
 --path="C:/YOUR_PATH/.minecraft/saves/worldname" \
 --bbox="40.7128,-74.0060,40.7580,-73.9855"
```

参数说明：
| 参数 | 说明 | 示例 |
|------|------|------|
| `--terrain` | 生成地形 | 必填 |
| `--path` | Minecraft 存档路径 | `~/.minecraft/saves/` |
| `--bbox` | 边界框坐标 | `min_lat,min_lng,max_lat,max_lng` |

三、数据源

. OpenStreetMap

Arnis 使用 **OpenStreetMap (OSM)** 作为主要地理数据源。

```
┌─────────────────────────────────────────────────────────────┐
│ OpenStreetMap 数据处理流程 │
├─────────────────────────────────────────────────────────────┤
│ │
│ 1. 区域选择 │
│ └─► 用户在地图上选择矩形区域 │
│ │
│ 2. Overpass API 查询 │
│ └─► 获取 OSM 建筑、道路、水体等数据 │
│ │
│ 3. 数据处理 │
│ └─► 转换为 Minecraft 方块 │
│ │
│ 4. 世界生成 │
│ └─► 输出 .minecraft 存档 │
│ │
└─────────────────────────────────────────────────────────────┘
```

. 高程数据

| 数据类型 | 来源 | 用途 |
|----------|------|------|
| 地形高度 | SRTM / DEM | 山脉、峡谷 |
| 水体 | OSM | 海洋、湖泊 |
| 建筑高度 | OSM tags | 建筑物高度 |

四、支持的 Minecraft 版本

. Java Edition

| 版本 | 支持状态 |
|------|----------|
| 1.17 | ✅ |
| 1.18 | ✅ |
| 1.19 | ✅ |
| 1.20 | ✅ |
| 1.21+ | ✅ |

. Bedrock Edition

| 版本 | 支持状态 |
|------|----------|
| 最新 Bedrock | ✅ |

五、高级配置

. 生成选项

```bash
完整参数示例
cargo run --no-default-features -- \
 --terrain \
 --path="~/.minecraft/saves/MyWorld" \
 --bbox="40.7128,-74.0060,40.7580,-73.9855" \
 --scale=1.0 \ # 世界缩放比例
 --spawn-point="40.73,-73.99" \ # 出生点
 --interior=true \ # 生成室内
 --water-level=62 # 水位高度
```

. 配置参数表

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--scale` | 1.0 | 地形缩放比例 |
| `--spawn-point` | 中心点 | 出生点坐标 |
| `--interior` | false | 是否生成建筑室内 |
| `--water-level` | 62 | 水位高度 |
| `--tree-density` | 0.5 | 树木密度 |
| `--biome` | auto | 生物群系 |

. 自定义区域

```bash
指定纽约曼哈顿
--bbox="40.7000,-74.0200,40.7800,-73.9500"

指定伦敦市中心
--bbox="51.5000,-0.1500,51.5200,-0.1000"

指定东京涩谷
--bbox="35.6500,139.7000,35.6700,139.7200"
```

六、架构设计

. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│ Arnis 系统架构 │
├─────────────────────────────────────────────────────────────┤
│ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 用户界面层 │ │
│ │ ┌─────────┐ ┌─────────┐ ┌─────────┐ │ │
│ │ │ GUI │ │ CLI │ │ Nix │ │ │
│ │ │ (Tauri) │ │ (args) │ │ flakes │ │ │
│ │ └────┬────┘ └────┬────┘ └────┬────┘ │ │
│ └───────┼────────────┼────────────┼──────────────────────┘ │
│ │ │ │ │
│ ┌───────▼────────────▼────────────▼───────────────────────┐ │
│ │ 核心引擎层 │ │
│ │ ┌─────────────────────────────────────────────┐ │ │
│ │ │ World Generator │ │ │
│ │ │ • Terrain Generation │ │ │
│ │ │ • Building Transpilation │ │ │
│ │ │ • Infrastructure (roads, water) │ │ │
│ │ └─────────────────────────────────────────────┘ │ │
│ │ ┌─────────────────────────────────────────────┐ │ │
│ │ │ Data Processor │ │ │
│ │ │ • OSM Parser │ │ │
│ │ │ • Elevation Handler │ │ │
│ │ │ • Block Mapper │ │ │
│ │ └─────────────────────────────────────────────┘ │ │
│ └───────────────────────────┬─────────────────────────────┘ │
│ │ │
│ ┌───────────────────────────▼─────────────────────────────┐ │
│ │ 数据源层 │ │
│ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │ │
│ │ │ Overpass │ │ DEM │ │ OSM │ │ │
│ │ │ API │ │ (高程) │ │ (地图) │ │ │
│ │ └─────────────┘ └─────────────┘ └─────────────┘ │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

. 关键模块

| 模块 | 说明 |
|------|------|
| `world_gen` | Minecraft 世界生成器 |
| `osm_parser` | OpenStreetMap 数据解析 |
| `elevation` | 高程数据处理 |
| `block_mapper` | 方块映射器 |
| `gui` | Tauri 图形界面 |

. 项目结构

```
arnis/
├── src/
│ ├── main.rs # 入口
│ ├── world_gen/ # 世界生成
│ │ ├── terrain.rs # 地形生成
│ │ ├── buildings.rs # 建筑转换
│ │ └── infrastructure.rs # 基础设施
│ ├── data/
│ │ ├── osm.rs # OSM 解析
│ │ └── elevation.rs # 高程处理
│ └── gui/ # GUI 界面
├── capabilities/ # Tauri 能力
├── Cargo.toml
└── tauri.conf.json
```

七、OpenStreetMap 数据处理

. 支持的 OSM 元素

| OSM 元素 | Minecraft 对应 |
|----------|----------------|
| `building=yes` | 石砖/木材建筑 |
| `highway` | 道路 |
| `waterway` | 河流/运河 |
| `landuse=forest` | 森林 |
| `landuse=farm` | 农田 |
| `leisure=park` | 公园 |
| `natural=water` | 湖泊/海洋 |

. 建筑映射规则

```rust
// 建筑高度映射
fn map_building_height(levels: u32) -> u32 {
 match levels {
 1 => 4, // 1 层 → 4 格高
 2 => 7, // 2 层 → 7 格高
 3 => 10, // 3 层 → 10 格高
 4..=10 => 13, // 4-10 层 → 13 格高
 _ => 20, // 超高层 → 20 格高
 }
}
```

. 道路生成

| OSM highway 类型 | Minecraft 方块 |
|-----------------|----------------|
| motorway | 石头台阶 |
| primary | 圆石台阶 |
| secondary | 砂砾 |
| residential | 泥土 |
| footway | 砂土 |

八、学术与媒体认可

. 媒体报道

| 来源 | 标题 |
|------|------|
| **AWS Blog** | Building Realistic Minecraft Worlds with Open Data |
| **Hackaday** | Bringing OpenStreetMap Data into Minecraft |
| **Tom's Hardware** | Minecraft Tool Lets You Create Scale Replicas of Real-World Locations |
| **XDA Developers** | Hometown Minecraft Map: Arnis |

. 学术论文

| 论文 | 发表 |
|------|------|
| **Floodcraft** | Game-based Interactive Learning Environment using Minecraft for Flood Mitigation |

九、安装方式对比

. 各平台安装

| 平台 | 推荐方式 |
|------|----------|
| **Windows** | 下载 .exe 或 `cargo build` |
| **macOS** | 下载 .app 或 `cargo build` |
| **Linux** | 下载二进制或 Nix |
| **NixOS** | `nix run github:louis-e/arnis` |

. 依赖要求

| 依赖 | 版本要求 |
|------|----------|
| Rust | 1.70+ |
| Cargo | 最新稳定版 |
| Minecraft | Java 1.17+ 或 Bedrock |

十、实践建议

. 大型世界生成

```bash
分块生成大区域
区块
cargo run -- --terrain --path="~/minecraft/saves/World_Part1" \
 --bbox="40.7000,-74.0200,40.7400,-73.9800"

区块
cargo run -- --terrain --path="~/minecraft/saves/World_Part2" \
 --bbox="40.7400,-74.0200,40.7800,-73.9800"
```

. 生成优化

```bash
启用多线程
cargo run --release -- \
 --terrain \
 --jobs=8 \ # 8 线程
 --bbox="40.71,-74.01,40.76,-73.96"
```

. 服务器部署

```bash
编译为无 GUI 版本
cargo build --release --no-default-features

部署到服务器
scp target/release/arnis user@server:/path/to/minecraft/
```

十一、VS 其他方案

| 工具 | 数据源 | Minecraft 版本 | 许可证 |
|------|--------|---------------|--------|
| **Arnis** | OSM | Java + Bedrock | Apache-2.0 |
| **EarthMC** | 专有 | Java | 专有 |
| **MineOS** | 自定义 | Java | 开源 |

十二、资源链接

. 官方资源

| 资源 | 链接 |
|------|------|
| 🌐 **官网** | https://arnismc.com |
| 📖 **文档** | https://github.com/louis-e/arnis/wiki |
| 💬 **Discord** | https://discord.gg/mA2g69Fhxq |
| 🐛 **问题反馈** | https://github.com/louis-e/arnis/issues |
| 📦 **发布页** | https://github.com/louis-e/arnis/releases |

. 相关项目

| 项目 | 说明 |
|------|------|
| **MapSmith** | 浏览器版在线生成 |
| **Floodcraft** | 洪水教育游戏 |

. 下载地址

⚠️ **安全提示**：请仅从以下地址下载：
- https://arnismc.com
- https://github.com/louis-e/arnis/releases

十三、总结

Arnis 是** Minecraft 地图生成的革命性工具**：

| 维度 | 说明 |
|------|------|
| 🗺️ **真实地理** | OpenStreetMap 精确还原 |
| 🏔️ **地形高程** | 真实地形起伏 |
| 🏠 **建筑** | 真实世界建筑 |
| ⚡ **高性能** | Rust 语言驱动 |
| 🌐 **跨平台** | Windows/macOS/Linux |
| 📖 **开源** | Apache-2.0 许可证 |

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/louis-e/arnis |
| 官网 | https://arnismc.com |
| Discord | https://discord.gg/mA2g69Fhxq |
| MapSmith | https://arnismc.com/mapsmith/ |

---

_🦞 本文由钳岳星君撰写，基于 Arnis (14.8k Stars)_
