---
title: "Arnis：把地球表面装进 Minecraft"
date: "2026-06-24T11:39:09+08:00"
lastmod: "2026-09-29"
slug: "arnis-real-world-to-minecraft-2026"
github_repo: "louis-e/arnis"
source_key: "gh:louis-e/arnis"
description: "Arnis 是一个 Rust + Tauri 桌面应用，把 OpenStreetMap 矢量数据、ESA WorldCover 卫星土地分类、AWS Terrain Tiles 高程数据、Overture Maps 机器学习建筑足迹、3DMR + Wikidata 真实 3D 地标，融合成可游玩的 Minecraft Java / Bedrock / Luanti 世界。本文以 v2.9.0 源码为口径，拆开它的多源数据拼装、高程处理流水线（AWS 博客八步口径与现行实现的对照）、8 种屋顶 + 9 种墙面风格系统、mimalloc + rayon + 流式落盘的性能取舍，并覆盖发布之后的 v3.0 Contour、v3.1 Canopy、v3.2 Horizon 三连发。"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "Tauri", "OpenStreetMap", "Minecraft"]
hiddenFromHomePage: false
---

# Arnis：把地球表面装进 Minecraft

## 学习目标

读完本文，可以：

1. 理解 Arnis 的四个核心机制（多源数据拼装、高程处理流水线、建筑风格系统、Rust 性能取舍）
2. 说清它的数据通道（Overpass API、ESA WorldCover、AWS Terrain Tiles、Overture Maps）的独立性和依赖关系
3. 对照 AWS 博客的"八步高程流水线"口径，理解 v2.9.0 实现里每一步的真实算法与工程取舍
4. 理解建筑风格系统（8 种屋顶 + 9 种墙面 + 5 种生命状态）
5. 提取对地理可视化 / 数据驱动生成项目可复用的 5 条经验

## 目录

- [§1 先给判断](#§1-先给判断)
- [§2 项目定位与系统边界](#§2-项目定位与系统边界)
- [§3 一张总览图：Arnis 的数据怎么拼](#§3-一张总览图arnis-的数据怎么拼)
- [§4 高程处理流水线（核心）](#§4-高程处理流水线核心)
- [§5 建筑风格系统](#§5-建筑风格系统)
- [§6 Rust 性能取舍](#§6-rust-性能取舍)
- [§7 v2.9.0 Mosaic Update 真正改了什么](#§7-v290-mosaic-update-真正改了什么)
- [§8 输出格式与互操作](#§8-输出格式与互操作)
- [§9 发布之后：v3.0 → v3.2](#§9-发布之后v30--v32)
- [§10 5 条可复用经验](#§10-5-条可复用经验)
- [§11 局限与未解](#§11-局限与未解)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [常见问题 FAQ](#常见问题-faq)
- [资料口径说明](#资料口径说明)

## §1 先给判断

Arnis 解决一个具体问题：让一个完全没有 Minecraft 地图编辑经验的人，在几分钟内把自家小区、故乡小镇、或者曼哈顿中城，生成一份**带地形、带建筑、带材质**的可游玩世界。

这不是"把卫星影像拉直贴到 Minecraft 平面"那种伪 3D，而是真实的 3D 体素化：山有高程，河有水深，桥有引坡，停车场画线，机场有跑道和停机坪。Hackaday 在 2024-12-30 报道了它；AWS Public Sector 博客（2026-03-03）披露其用户已接近 30 万；2026-09-29 复核时仓库 stars 为 18.1K，最新版本是 v3.2.0 "Horizon Update"（2026-09-09），甚至已经支持生成月球和火星。

这篇文章的机制分析以 **v2.9.0（2026-06-16 Mosaic Update）源码为口径**，拆四个核心机制：

1. **多源地理数据拼装**——OSM 矢量 + ESA WorldCover 土地覆盖 + AWS Terrain Tiles 高程 + Overture Maps ML 建筑 + 3DMR/Wikidata 真实 3D 模型
2. **高程处理流水线**——AWS 博客总结过八步口径，v2.9.0 的实现已在此基础上换掉了其中三步的算法，本节逐步对照
3. **建筑风格系统**——8 种屋顶 + 9 种墙面深度 + 5 种建筑生命状态
4. **Rust 性能取舍**——`mimalloc` 替换系统分配器、`rayon` 90% CPU 上限、2.9.0 加入的流式落盘 + Bedrock chunk 并行编码

发布之后的 v3.0 → v3.2 三连发（§9）单独说。最后给做地理可视化 / 数据驱动生成项目的人 5 条可复用经验。

## §2 项目定位与系统边界

| 维度 | 内容 |
|------|------|
| **仓库** | `github.com/louis-e/arnis` |
| **最新版本** | v3.2.0 "Horizon Update"（2026-09-09）；本文机制分析以 v2.9.0 "Mosaic Update"（2026-06-16）源码为口径 |
| **作者** | Louis Erbkamm（louis-e），常驻慕尼黑，BMW Group 车载信息娱乐平台开发者，业余维护（AWS 博客作者简介） |
| **License** | Apache 2.0（`src/luanti_block_map.rs` 数据转换自 rollerozxa/MC2MT，LGPL-2.1+） |
| **规模** | 18,088 stars / 1,516 forks / 130 open issues（含 PR）（2026-09-29 读数；本文原稿 2026-06-24 记录 16,259 stars / 1,355 forks / 116） |
| **技术栈** | Rust + Tauri 2 跨平台 GUI + `fastanvil` 0.32/`fastnbt` 2.6（Java Anvil）+ `bedrock-rs`（rev 锁定）+ `rusqlite` 0.40（Luanti 实验性） |
| **输出格式** | Minecraft Java Edition 1.17+（.mca region）/ Bedrock Edition（.mcworld）/ Luanti Mineclonia（map.sqlite，v2.8.0 起实验性） |
| **数据来源** | OpenStreetMap Overpass API + ESA WorldCover 2021 + AWS Terrain Tiles + 区域高分辨率 provider + Overture Maps + 3DMR/Wikidata |
| **用户量** | 近 30 万（AWS 博客 "nearly 300,000 users"，2026-03-03） |
| **目标平台** | Windows / macOS / Linux（浏览器版走 MapSmith） |
| **同源项目** | MapSmith（[arnismc.com/mapsmith](https://arnismc.com/mapsmith/)，浏览器端、按面积付费：Neighborhood €3 → Metro €25） |

Arnis 的产品定位有 3 条明确的边界，决定了它后面所有的工程取舍：

- **零后端、零 API Key**——AWS 博客原话是 "runs entirely on the client's machine with no backend services or API keys"。所有生成计算在用户本地完成，数据走公共开放数据源
- **不替代专业制图工具**——目标是"在 Minecraft 里散步"，不是"1:1 还原城市"
- **只有取数走网络**——OSM、高程、土地覆盖三类数据下载完之后，处理流程不再有外部依赖（v3.1.0 起还支持直接喂本地 `.osm` 文件，彻底离线）

这 3 条边界直接解释了为什么它要自己写 world editor、为什么 2.9.0 才上"流式落盘"、以及为什么 MapSmith 作为云端服务要独立成一个产品线。

### 本文阅读路径

- **只想看技术架构**：读 §3 数据拼装总览 → §4 高程流水线 → §5 建筑风格系统
- **只想看 Rust 工程取舍**：读 §6 性能与内存 → §7 流式落盘与并行化
- **想看发布后的演进**：读 §9 v3.0 → v3.2
- **想看工程经验**：读 §10 的 5 条经验
- **第一次读**：按顺序读，§4 和 §10 是最值得细读的两节

## §3 一张总览图：Arnis 的数据怎么拼

Arnis 不是把一张图糊到 Minecraft 平面上。它并行喂入 4 个独立数据通道，在体素化阶段才汇合；3D 地标还有第 5 条补充通道（OSM 的 `3dmr` 标签 + Wikidata 模型，v2.8.0 引入）。

```
              ┌──────────────────┐
              │   用户选择 bbox  │  (min_lat, min_lng, max_lat, max_lng)
              │   + scale 参数   │
              └────────┬─────────┘
                       │
        ┌──────────────┼──────────────┬──────────────┐
        ▼              ▼              ▼              ▼
   ┌────────┐    ┌──────────┐   ┌──────────┐  ┌──────────┐
   │ Overpass│    │   ESA    │   │ Terrain  │  │ Overture │
   │   API   │    │WorldCover│   │  Tiles + │  │   Maps   │
   │ (OSM)   │    │   2021   │   │ 区域provider│ (ML建筑) │
   └────┬────┘    └────┬─────┘   └────┬─────┘  └────┬─────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
    矢量要素        土地分类        高程栅格       补充建筑
   (way/rel)     (11 类landcover)  (Terrarium)   (非OSM来源)
        │              │              │              │
        └──────────────┴──────────────┴──────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │  Projection + Coord │
                    │  Transform (LL→XZ)  │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │  体素化 + 块类型映射 │
                    │  (World Editor)     │
                    └──────────┬──────────┘
                               ▼
            ┌──────────┬───────────┴───────────┬──────────┐
            ▼          ▼                       ▼          ▼
       Java Anvil   Bedrock .mcworld    Luanti map.sqlite  Preview
       (.mca)       (bedrock-rs)        (rusqlite 实验)   (PNG)
```

四条数据通道彼此独立、互不依赖，可以并发下载和处理。Overpass 的取数策略在 `src/retrieve_data.rs` 里写得相当讲究，不是简单的"一个列表依次试"：

```rust
// src/retrieve_data.rs
let arnis_api_server = "https://api.arnismc.com/overpass/api/interpreter";
let api_servers: Vec<&str> = vec![
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
];
let fallback_api_servers: Vec<&str> = vec![
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
];
```

实际请求计划是：**50% 概率先探测一台随机官方服务器**（源码注释原话 "50% chance: probe one random official server first"），然后 arnis 官方镜像一次，再按随机顺序试剩余官方服务器，最后才是随机排序的回退列表。洗牌是为了不让所有用户同时压同一台机器。

每条通道再细看：

| 通道 | 数据形态 | 关键工程点 |
|------|----------|------------|
| **Overpass API** | OSM JSON（nodes / ways / relations） | `OsmData` 解析 + bbox 裁剪 + 关系子集剪枝（`way(r.relsinbbox)` → `node(w.waysinbbox)`），只保留 bbox 内的节点，减小响应体 |
| **ESA WorldCover** | 10m 分辨率 Cloud-Optimized GeoTIFF（11 类，覆盖纬度 -60° 到 +84°） | HTTP Range 请求只读 bbox 对应的字节段（`land_cover.rs` 注释明确说这是为了避免下载整块 ~500MB 的 GeoTIFF）；按 3×3 度切片命名与缓存 |
| **Terrain Tiles / 区域 provider** | Terrarium 格式 PNG（`elevation_m = (R*256 + G + B/256) - 32768`） | `selector::select_provider` 按 bbox 覆盖范围选分辨率最高的 provider（USGS 3DEP → IGN France → IGN Spain → Japan GSI），都不覆盖再回退 AWS Terrain Tiles；选中的区域 provider 若返回的 NaN 占比超过 50%，自动判定覆盖声明过宽（注释举的例子：IGN France 的 bbox 把比利时算进去了，但比利时坐标拿不到数据），回退 AWS |
| **Overture Maps** | GeoParquet（带 ML 派生的高度、楼层、屋顶形状） | 通过 STAC catalog 动态解析最新 release（PR #1063）；HTTP Range 读 Parquet footer 再取行组；OSM 主来源的建筑跳过避免重复；用 ID 高位 bit 避免和 OSM ID 冲突 |

### 海洋为什么走 ESA 而不是 OSM

`retrieve_data.rs` 里有这么一段注释解释了陆海分离的设计动机：

> Ocean/coastal elements are excluded because ESA WorldCover satellite data handles ocean detection more reliably at 10m resolution (LC_WATER class). Inland water (lakes, rivers, ponds) is still fetched from OSM.

OSM 的 `natural=coastline` 是人工维护的折线，覆盖稀疏且更新慢；ESA WorldCover 2021 是卫星 10m 分辨率的分类，海洋识别更稳定。但内陆水体（湖、河、池塘）OSM 反而更准，所以走 OSM。数据源选择按"哪个在当前语义下更准"，不按"哪个更全"。

### 三个细节决定能不能跑起来

- **provider 探测要按区域**——同一 bbox 在德国走 IGN France、在美国走 USGS，由 `select_provider` 按覆盖 bbox 自动匹配；显式加 `--aws-only-elevation` 可以跳过区域 provider 换速度
- **缓存按 provider 分目录**——高程瓦片按 provider 的 `CACHE_NAME`（`usgs_3dep` 等）落盘，ESA WorldCover 切片单独缓存，启动时 `cleanup_old_cached_tiles` 清理过期瓦片
- **Overture ID 冲突防护**——`OVERTURE_ID_HIGH_BIT = 0x8000_0000_0000_0000` 设置第 63 位，保证和 OSM 的 64 位正整数 ID 永不重叠

## §4 高程处理流水线（核心）

高程是项目最值得展开的工程部分，因为它是**真实世界有缺陷的开源数据 → Minecraft 限制（Y ∈ [-64, 320]）** 的胶水层。

### 4.1 两套口径：AWS 博客的八步与 v2.9.0 的实现

AWS Public Sector 博客（2026-03-03，作者 Louis Erbkamm 与 AWS 解决方案架构师 Cristian Chicas）把高程处理总结成八步：

```
1. Calculate tile zoom and coordinates based on the selected area
2. Check tile cache and fetch missing terrain tiles from Amazon S3
3. Decode terrain tiles to meters (per pixel) and assemble the height grid
4. Apply Gaussian smoothing to remove artifacts
5. Fill NaN values by neighbor interpolation
6. Guard against outliers using percentile-based clamping
7. Compute min/max for adaptive vertical scaling and clamp to height limits
8. Voxelize the map data on the heightmap and save the world
```

这篇博客写于 v2.5 时代。到 v2.9.0，第 4、5、6 步的算法都换代了，执行顺序也不同。`fetch_elevation_data`（`src/elevation/mod.rs`）的实际序列是：

```
选 provider → 拉原始格网
  → filter_elevation_outliers   （IQR 离群检测，最先跑）
  → repair_terrain_anomalies    （5×5 中位数 + MAD 异常修复）
  → fill_nan_values             （3×3 邻域均值迭代填充）
  → 土地覆盖感知修复            （城区高斯平滑 + 水面拉平）
  → scale_to_minecraft          （真实/压缩二选一的自适应缩放）
  → 体素化落盘
```

高斯平滑并没有消失，但被收窄到"建成区"专用；"百分位裁剪"换成了带守卫的 IQR 检测。下面按 v2.9.0 的真实顺序逐一拆解。

### 4.2 网格上限与 provider 实测限制

Minecraft 一个区块是 16×16 方块，1.17+ 世界高度限制是 Y ∈ [-64, 320]。所以"地图分辨率 → 体素分辨率"的换算直接决定山的细节是否丢失。

`src/elevation/mod.rs` 定义了 `MAX_ELEVATION_GRID_DIM: usize = 16384`，注释说清了它的定位：这是**拼接后的上限**——USGS 3DEP、IGN France、IGN Spain 这类"单请求"provider 内部会把 bbox 切成尊重各自单请求上限的子瓦片再拼接；AWS Terrain Tiles、Japan GSI 这类瓦片型 provider 天然按瓦片粒度请求，结构上不受这个上限约束。

- 默认 `--scale 1.0` 下，16384 能覆盖约 256 km² 的 bbox 而不损失原生分辨率（注释同时记录了这条边界的演进：4096² 约 16.8 km² → 8000² 约 64 km² → 16384² 约 268 km²）
- 超过上限后格网被截断，块级高程用**双线性插值**补足——地形仍然生成，只是采样密度低于原生（注释原话 "terrain remains generated, just with sub-native sampling"）
- 内存：16384 × 16384 的 f64 格网约 2 GB；叠加水体混合格网（water_blend_grid）和修复阶段的快照，最大情况峰值约 6 GB（注释原话），MapSmith 部署环境配了 >20 GB

```rust
// src/elevation/mod.rs
// Cap grid dimensions to avoid WMS server rejections.
let grid_width: usize = world_width.clamp(2, MAX_ELEVATION_GRID_DIM);
let grid_height: usize = world_height.clamp(2, MAX_ELEVATION_GRID_DIM);
```

单请求上限写死在 `providers::regional` 的 `USGS_MAX_SINGLE` / `IGN_*_MAX_SINGLE` 常量里，每个值背后都是实测：

| Provider | 协议 | 文档上限 | 实测可靠值 | 原因 |
|----------|------|----------|-----------|------|
| USGS 3DEP | ArcGIS ImageServer | 8000 | 2048 | 文档允许 8000，但 ~3000 之后服务端返回 HTTP 500（源码注释原话），2048 是"reliable sweet spot" |
| IGN France | WMS 1.3.0 | — | 4096 | — |
| IGN Spain | WCS 2.0.1 | — | 4096 | — |
| AWS Terrain Tiles | S3 瓦片 | — | 结构性免疫 | 按瓦片粒度请求 |

USGS 那条注释最值钱的地方是**作者明确把"文档说的"和"实测稳定"分开记录**。它告诉后来者：如果以后换 provider，碰到 HTTP 500 不要先怀疑自己代码，先查 provider 的实测上限。

另一个容易被忽略的取舍在存储层：`ElevationData::heights` 是 `Vec<Vec<f32>>`，rustdoc 注明 "heights are already rounded to integer block Ys at placement time, so the full f64 precision was wasted on a grid that can easily hit 10+ million cells on a city-sized bbox (≈80 MB at f64, halved at f32)"。注意**后处理全程仍是 f64**，只在构造 `ElevationData` 时降一次精度——数值稳定性留给计算，内存省在存储。

### 4.3 解码：Terrarium 公式

AWS Terrain Tiles 把高程编码进 PNG 的 RGB 通道，解码公式在博客和源码里完全一致（`aws_terrain.rs` 里 `TERRARIUM_OFFSET: f64 = 32768.0`）：

```
elevation_m = (R * 256 + G + B/256) - 32768
```

可表达的值域是 -32768 到 +32767.996 米，远超地球表面实际范围（马里亚纳海沟 -11034 米到珠峰 +8849 米）。这套格式也不是 Arnis 的选择题——AWS Terrain Tiles 数据集本身就以 Terrarium PNG 发布（S3 路径 `terrarium/{z}/{x}/{y}.png`），沿用数据集的编码约定即可。AWS 博客还提到两个鲁棒性细节：瓦片下载前先查本地缓存；瓦片损坏就丢弃重下；端点暂时不可用时**回退生成平地**，保证生成流程总能走完。

### 4.4 IQR 离群检测（流水线第一步）

`filter_elevation_outliers`（`src/elevation/postprocess.rs`）不是简单裁剪，而是 **IQR（四分位距）检测**：取 Q1/Q3 之外 3 倍 IQR 的值判为真离群（损坏数据、海底伪影），替换掉。

关键是一个**计数守卫**：如果超过 5% 的值都落在界外，直接放弃过滤——注释说这说明地形本身是双峰的（比如深峡谷），不是数据损坏，"without clipping real terrain on mountains or deep valleys"。没有这个守卫，大峡谷一类的 bbox 会被"修复"成平原。

### 4.5 中位数 + MAD 异常修复

`repair_terrain_anomalies` 处理的是 LiDAR 分类错误、瓦片接缝、provider 抽风这一类局部异常。算法是 **5×5 窗口（24 个邻居）的中位数滤波，配合 MAD（median absolute deviation）** 判定：偏差要同时超过 6 米绝对阈值和 3 倍 MAD 相对阈值才算异常。

两个实现细节值得注意：

- 迭代最多 10 轮，每轮只修边界像素够多的异常簇，从外向内侵蚀——多像素连片的伪影一轮修不完
- 每轮从行快照读取、只写内部单元，行与行之间用 rayon 并行。注释说在 16k² 格网（流水线允许的最大情况）上，这一步是高程后处理里最贵的

它替代的正是 AWS 博客八步口径里的"Apply Gaussian smoothing"——泛化高斯平滑会连山脊一起抹平，中位数滤波保边缘。

### 4.6 NaN 填充

如果 bbox 跨过两块瓦片，边界处可能有 NaN。`fill_nan_values` 的做法：每个 NaN 像素取 **3×3 邻域内所有有效像素的平均值**；每轮迭代基于上一轮的只读快照计算（注释明确说是为了避免扫描顺序带来的方向偏差），行级并行、外层串行收敛，直到没有 NaN。

这是"最简单够用"的方案——不是 Kriging 也不是 IDW，每轮 O(1) 邻居均值，收敛即停。对填补瓦片缝隙这种局部空洞，够用了。

### 4.7 土地覆盖感知修复：高斯的正确位置

高斯平滑在 v2.9.0 里有明确的辖区。`apply_land_cover_repair` 只对**建成区单元格**做高斯平滑，治的是城市 LiDAR/DSM 分类错误——隧道口、高架这些被当成"地面"的点。σ 以格网单元计，按实际米/像素换算，保证不同 provider 分辨率下平滑的物理尺度一致。

水体是另一套逻辑，比陆地精细：

- **静止水体**：用直方图众数（最密的 1 米高程 bin）估计真实水面——注释解释这比百分位稳健，因为岸边墙壁让水体组件的直方图有一个真实水面峰值加一条向上的长尾，而水深数据（bathymetry）给出向下长尾，众数对两种偏差方向都免疫。然后加**不对称容差**：水面 +2 米以内全部拉平（反正 Minecraft 把水渲染成单层方块，保住深度差异也不可见），+2 米以上保留原值——那是真的墙、码头、堤岸
- **流动水体**：逐单元格局部中位数保住坡度梯度，注释特别指出若套用静止水的整段拉平，会把整条河的梯度钳到下游端点的低百分位，产生"横跨峡谷的平带"伪影
- 还有一个波罗的海峡湾的实际案例：AWS Terrarium 在那里混入了水深和海岸均值，水体系统性偏高，整片水域变成"悬空水台 + 悬崖"；修法是量测相邻陆地的第 25 百分位作为基准再拉平

### 4.8 自适应垂直缩放：能放就真实，放不下才压缩

垂直缩放的核心函数 `scale_to_minecraft` 在 `src/elevation/postprocess.rs`。它的逻辑比"放大到某个目标高度"克制得多：

```rust
// src/elevation/postprocess.rs（节选）
let ideal_scaled_range: f64 = height_range * scale;
let available_y_range: f64 = (effective_max_y - TERRAIN_HEIGHT_BUFFER - ground_level) as f64;

let scaled_range: f64 = if ideal_scaled_range <= available_y_range {
    ideal_scaled_range          // 放得下：保持真实比例（打印 "Realistic elevation"）
} else {
    let compression_factor: f64 = available_y_range / height_range;
    height_range * compression_factor   // 放不下：等比压缩（打印压缩比）
};
```

默认参数下可用空间是 319（MAX_Y）− 15（给建筑树木留的 `TERRAIN_HEIGHT_BUFFER`）− (−62)（默认 ground_level）= 366 块。两种结果：

- **曼哈顿**（高差约 30 米）：30 × 1.0 = 30 块，远小于 366 → **保持 1:1 真实比例**，街道起伏按实际米数呈现，不放大
- **大峡谷**（高差约 1800 米）：1800 × 1.0 放不下 → 压缩系数约 0.2，整段映射到 366 块内，山体轮廓和相对起伏保留，绝对比例让位于可玩性

放不下时日志会打出 `Elevation compressed: 1800.0m range -> 366 blocks (4.92:1 ratio, ...)` 这样的行，1800 米的高差被压进 366 块里。缩放产物除了 `mc_heights`，还返回 `min_height_m` 和 `blocks_per_meter` 两个仿射参数——后面雪线计算（§7.4）要用它们把真实米数反解回 Minecraft Y 坐标。零起伏地形有专门处理：保住真实最小高程（雪线要靠它区分高原和平原），全部格子压到 ground_level。

`--disable-height-limit` 可以换用捆绑 datapack 的扩展范围（Java 1.21.4+ 为 Y = -2032..2031，Bedrock 1.21.40+ 为 Y = -512..512，两者标注实验性），高差大的区域因此更少触发压缩。

代价是**逐 bbox 独立缩放**：压缩模式下相邻两个 bbox 的压缩比不同，纵向拼不上。横向拼接已有 `--projection web_mercator` 可解，纵向仍是一个未解的取舍，见 §11。

### 4.9 体素化 + 块类型映射

最后一步，把连续高程 + 土地覆盖分类 + 矢量要素一起转 Minecraft 块。`ground_generation.rs` 的映射（简化）：

```rust
// src/ground_generation.rs（简化）
match class {
    LC_TREE_COVER => (GRASS_BLOCK, DIRT),
    LC_WETLAND    => (MUD, DIRT),
    LC_BARE | LC_SNOW_ICE => {
        // 孤立像素守卫：四周都不是裸地/雪，就混回周围
        // 否则按 value noise 铺土壤斑块 + 多样化岩石
    }
    LC_BUILT_UP   => {
        // 按高度阈值铺石砖系：STONE_BRICKS / CRACKED_STONE_BRICKS / STONE / COBBLESTONE
    }
    // LC_WATER 在此之前已按变深逻辑单独处理
}
```

比"雪地就铺雪块"想得细：裸地/雪有孤立像素守卫和噪声混合，城市地面是一整套带高度阈值的硬质铺装族。`land_cover_bridge_repair.rs` 和 `land_cover_osm_water_override.rs` 两个独立模块负责处理 OSM 和 WorldCover 在桥梁/水域上的冲突；`water_depth.rs` 负责逐格水深（§7.5）。

## §5 建筑风格系统

Minecraft 默认方块只有 1×1×1 立方体，**用纯立方体表达"建筑风格"是 Arnis 在工程上最难的一关**。v2.9.0 的建筑子系统是 v2.8.0 大重构（"building rendering overhaul"，PR #1010）之后的形态，三层表达：

### 5.1 屋顶：8 种形状 + Hipped 的 3 个变体

```rust
// src/element_processing/buildings.rs
pub(crate) enum RoofType {
    Gabled,    // 双坡屋顶（最常见的住宅）
    Hipped,    // 四坡屋顶（注释：including Half-hipped, Gambrel, Mansard variations）
    Skillion,  // 单坡屋顶（车库、棚屋）
    Pyramidal, // 锥形屋顶（塔楼）
    Dome,      // 半球形（清真寺、教堂）
    Cone,      // 圆锥形
    Onion,     // 洋葱顶（俄罗斯东正教）
    Flat,      // 平屋顶（现代商业楼）
}
```

屋顶类型有一个四级决策链（`buildings.rs:893` 附近）：

1. OSM 标签 `roof:shape` 显式声明 → 照办（"If the mapper explicitly tagged a roof shape, always respect it"）
2. 没标签 → 用建筑类型的预设默认
3. 预设也没有 → 若 footprint ≤ 800 块且抽中 90% 概率，自动上 Gabled，否则 Flat
4. 另有特例：无明显朝向的对角建筑（对角度 < 0.35）在没显式标签时从 Gabled/Hipped 降级为 Pyramidal——多边形边扫描让中等旋转的建筑也能用坡屋顶，只有特别斜的才降级

`Hipped` 变体在 OSM 标签层面不分 Half-hipped/Gambrel/Mansard，Arnis 把它们归并后靠 `element_rng`（从元素 ID 派生的确定性 RNG，`src/deterministic_rng.rs`）在同一形状内生成不同的高度、坡度参数，避免整个城市"千楼一面"。确定性还意味着：同一栋楼重复生成结果一致。

### 5.2 墙面：9 种深度风格

这一层是 Arnis 真正出彩的地方。`WallDepthStyle` 不做花哨纹理，而是通过**在墙面上添加浮雕状的方块延伸**来制造深度感：

```rust
pub(crate) enum WallDepthStyle {
    None,               // 无深度（棚屋、温室、极小建筑）
    SubtlePilasters,    // 细柱（住宅、独栋）
    ModernPillars,      // 配对柱 + 水平带（商业、办公、酒店）
    InstitutionalBands, // 柱 + 楼层线（学校、医院）
    IndustrialBeams,    // 仅角柱（工业、仓库）
    HistoricOrnate,     // 石柱 + 拱形窗 + 飞檐（历史建筑）
    ReligiousButtress,  // 阶梯式扶壁 + 飞檐（宗教建筑）
    SkyscraperFins,     // 全高垂直鳍片（现代摩天楼）
    GlassCurtain,       // 极简角部定义（玻璃幕墙）
}
```

通过 `WallDepthStyle × RoofType × BuildingCondition` 的三维组合，Arnis 让同一个街区的 200 栋楼看起来**不重复**。它改变的不是方块颜色，是**建筑轮廓的可读性**。

### 5.3 建筑生命状态：5 种

```rust
// src/element_processing/buildings.rs
pub(crate) enum BuildingCondition {
    Normal,        // 正常
    Construction,  // 建造中（脚手架 + 顶部开放）
    Disused,       // 闲置（保留结构）
    Abandoned,     // 弃用（破洞、缺窗）
    Ruined,        // 废墟（部分墙体 + 碎石）
}
```

从 OSM 标签推断的映射做得比想象细：`building=ruins|collapsed`、`historic=ruins`、`ruins=yes`、`ruins:building`、`abandoned=yes`、`abandoned:building`、`building=construction`、`construction:building` 都算数；但**裸的 `disused=yes` 不算**——源码注释特意说明 "Bare `disused=yes` is ambiguous, only the namespaced form counts"。建造中和废墟的楼顶是开放的（"Construction sites and ruins stay open at the top"）。这个枚举让一座城市能讲完"生老病死"。

### 5.4 Overture Maps 补的建筑

OSM 在**非洲农村、亚洲部分区域、偏远地区**的建筑覆盖稀疏。Overture Maps 用 ML 模型从卫星影像提取建筑轮廓：

```rust
// src/overture.rs 关键常量
const OVERTURE_ID_HIGH_BIT: u64 = 0x8000_0000_0000_0000;
const MAX_OVERTURE_BUILDINGS: usize = 100_000;
```

`OvertureBuilding` 结构体有 10 个独立数据字段：`height`（米）、`min_height`、`num_floors`、`subtype`（residential / commercial）、`class`（house / apartments）、`roof_shape`、`roof_material`（metal / glass / roof_tiles）、`roof_orientation`（along / across）、`facade_color`、`roof_color`。这些字段是建筑风格系统的**直接数据源**——比 OSM 的 `building=yes` 丰富一个数量级。

去重做了两层。第一层按来源：

```rust
// src/overture.rs 注释
// Buildings whose primary source is "OpenStreetMap" are excluded to avoid
// duplicates with the existing OSM data pipeline.
```

第二层按空间：`deduplicate_against_osm` 对每栋 Overture 建筑检查质心是否落在已有 OSM 建筑的包围盒内，兜住那些"来源过滤漏网、两边测绘有差异"的重复。

## §6 Rust 性能取舍

v2.9.0 之前，整个世界驻留内存，生成完再一次性落盘；bbox 一大，内存就成了第一瓶颈。v2.9.0 的 Mosaic Update 把"流式落盘"作为头号特性（release notes 原话："Arnis now streams the world to disk as it generates instead of holding all of it in memory"），背后的工程是几层叠加：

### 6.1 全局分配器：`mimalloc`

```rust
// src/main.rs
// mimalloc scales far better than the system allocator under the concurrent
// 4 KiB section-vec / hashmap churn of tile-parallel processing.
#[global_allocator]
static GLOBAL: mimalloc::MiMalloc = mimalloc::MiMalloc;
```

Minecraft 一个 section 是 16×16×16 = 4096 个方块。Arnis 在体素化阶段会产生大量 4 KiB 左右的 Section Vec，系统分配器在多线程下碎片化严重。`mimalloc` 专为"高并发 + 大量小对象"设计。

### 6.2 线程池上限：90% CPU

```rust
// src/main.rs run_cli()
// Configure thread pool with 90% CPU cap to keep system responsive
floodfill_cache::configure_rayon_thread_pool(0.9);
```

留出余量让系统保持响应。`configure_rayon_thread_pool` 的文档还写了一个细节：显式设置过 `RAYON_NUM_THREADS` 环境变量时直接让 rayon 自己接管——跑分和高级用户的调优入口不受这个默认值影响。

### 6.3 FNV hash 而非 SipHash

```rust
// src/world_editor/mod.rs
/// Uses FNV hashing (not SipHash): `get_ground_level` sits on a hot
/// path (called per-block during placement), so the hash cost matters.
road_surface_overrides: FnvHashMap<(i32, i32), i32>,
```

`get_ground_level` 在放置阶段对每个方块调用一次，哈希成本乘上总方块数就是个不小的数。源码注释只说到"hash cost matters"为止，没给具体纳秒数——这类微优化的实际收益跟负载形态强相关，注释点到为止是诚实的做法。选型逻辑本身站得住：SipHash 的价值在抗哈希洪水攻击，而这里的 key 是内部生成的 `(i32, i32)` 坐标，攻击者控制不了。

### 6.4 Disk-full 错误检测

`is_disk_full_error`（`src/world_editor/mod.rs`）用三条通道判断磁盘满：顶层错误的 Display 字符串、沿 `source()` 链下钻后的强类型匹配（`ErrorKind::StorageFull`，Rust 1.83.0 起稳定）、以及 OS 错误码（112 = Windows `ERROR_DISK_FULL`，28 = Unix `ENOSPC`）：

```rust
// src/world_editor/mod.rs（节选）
let s = err.to_string();
if s.contains("os error 112") || s.contains("os error 28") || s.contains("StorageFull") {
    return true;
}
let mut source = err.source();
while let Some(e) = source {
    if let Some(io_err) = e.downcast_ref::<std::io::Error>() {
        if io_err.kind() == std::io::ErrorKind::StorageFull { return true; }
        if matches!(io_err.raw_os_error(), Some(112) | Some(28)) { return true; }
    }
    let s = e.to_string();
    if s.contains("os error 112") || s.contains("os error 28") || s.contains("StorageFull") {
        return true;
    }
    source = e.source();
}
false
```

字符串匹配排第一是刻意的——注释说顶层错误可能因为缺 `'static` bound 根本没法 downcast。这对用户体感很关键：30 分钟生成跑完最后写盘失败，只弹一个裸的 `os error 28` 会让人摸不着头脑。项目在这个点上修过一次误报：PR #1113 修掉了 #824 报告的"0 字节误判导致弹 Not enough disk space"。

## §7 v2.9.0 Mosaic Update 真正改了什么

如果说 v2.8.0 "Landmark Update" 重做的是**看到什么**（数百个真实 3D 地标、桥型结构、建筑生命周期），v2.9.0 重做的就是**怎么生成**。改动的核心是这几条：

### 7.1 流式落盘（PR #1095，"Perf/large area scaling"）

之前内存上限 = 世界大小上限。流式落盘后，section 写完 region file 立即驱逐，内存占用和 bbox 面积解耦。被驱逐的区域记录在 `flushed_regions: FnvHashSet` 里，`set_block` 有对应的守卫：源码注释写明 "Regions already streamed to disk and evicted; writes to them are dropped by the set_block guard so eviction can't be resurrected"——驱逐之后的迟到写入直接丢弃，防止已落盘数据被内存里的旧状态"复活"。

### 7.2 Bedrock chunk 编码并行化（PR #1074）

Bedrock 的区块格式比 Java Anvil 重（NBT 子区块、版本相关布局），之前编码是单线程。PR #1074 用 rayon 把所有 chunk 的编码铺到多核上。v2.9.0 release notes 把这条和流式落盘并列为本版主打的两个性能改动。

### 7.3 真实车道宽（PR #1104）

道路宽度的真实实现比"车道数 × 3.5 米"更讲究，它同时考虑道路类型和车道数，取两者中较大的：

```rust
// src/element_processing/highways.rs（highway_block_range 节选）
// Explicit width=* wins; else vehicular roads use 3.5 m/lane, never below
// the default. The -1 accounts for the centre block in 2*block_range+1.
if let Some(w) = parse_width_tag_m(tags) {
    block_range = (w / 2.0).round() as i32;
} else if scales_with_lanes {
    let lanes_based = ((lanes as f32 * 3.5 - 1.0) / 2.0).round() as i32;
    block_range = block_range.max(lanes_based);
}
```

三层语义：显式 `width=*` 标签最优先；否则按 3.5 米/车道换算，但**永不低于道路类型的基础宽度**（motorway/primary/trunk 半宽 5 块，secondary 4，tertiary 2，footway 1……）；`lanes` 缺省用各类型默认值，钳制在 1-16，`lane_markings=no` 只取消车道分割线、不改宽度。`lanes=8` 的高速公路和 `lanes=1` 的小巷从此视觉上分得开。

### 7.4 暴雪线（PR #1107）

雪线不是拍一个固定高度。`src/ground.rs` 按绝对纬度分段线性插值：

```rust
// src/ground.rs
/// Climatic snow line in metres by absolute latitude, piecewise-linear through
/// the cited anchors: equator 4500, subtropics (25 deg) 5700, mid-latitudes
/// (46 deg) 3000, poles 0. Source: Wikipedia "Snow line".
fn snow_line_meters(lat_deg: f64) -> f64 { ... }
```

锚点取自 Wikipedia 的 "Snow line" 条目：赤道 4500 米、副热带（25°）5700 米、中纬度（46°）3000 米、极点 0 米。雪线高度先经 §4.8 的仿射参数（`min_height_m` / `blocks_per_meter`）反解成 Minecraft Y 阈值，高于阈值的山顶表层换雪；雪线边缘再叠一层 ±6 块的抖动噪声（`SNOW_EDGE_JITTER`），避免出现一条几何上过于整齐的雪线。副热带雪线反而高于赤道（副热带高压的下沉气流控制下降雪偏少），这个反直觉的锚点说明作者真的查了气候学资料，而不是拍了一个固定值了事。

### 7.5 Per-cell 水深雕刻（PR #1054）

之前所有水域都是"满水方块"，1 米深和 100 米深看起来一样。真实机制在 `src/water_depth.rs`：对 LC_WATER 掩膜跑 **chamfer 3-4 距离变换**，按离岸距离逐格算水深——近岸是宽平的浅滩（前 9 个距离单位内不降坡），往外分级下挖，最深封顶 **6 块**（`MAX_WATER_DEPTH = 6`），水底按深度铺沙、砾石、黏土并种上海草与海带。配套的还有 PR #1102 的**分层水底与水下植被**和 PR #984 的**海湾与游艇码头**。v2.9.0 的水域子系统至此和陆地子系统可玩性相当。

它没有、也不需要真实的水深数据——地形高程在水体上本来就是空的，"离岸多远"是一个完全可从土地覆盖掩膜推出的代理变量，6 块封顶保证了浅水视觉可信、深水不至于挖穿海底。

### 7.6 其他值得知道的

- **烘焙光照**（PR #1055，`--bake-lighting`）：预计算每 chunk 光照，配 Voxy/Chunky 这类 LOD mod 时远处区块直接是亮的
- **机场**：带标线的跑道和停机坪上停飞机（PR #1072）
- **自校准 ETA**（PR #1100）：GUI 进度条按实际吞吐自校准剩余时间，顺带加了 `--benchmark` 埋点
- **矿石**：`--fillground` 开启后地下生成矿石，生存模式可用（release notes 明确这条是给 survival 玩家的）

## §8 输出格式与互操作

### 8.1 两个版本的更新焦点对比

| 维度 | v2.8.0 "Landmark Update"（2026-05-19） | v2.9.0 "Mosaic Update"（2026-06-16） |
|------|----------------------------------------|--------------------------------------|
| 核心方向 | 视觉质量（地标 3D 化） | 性能 / 内存（流式 + 并行） |
| 改动点 | 数百个真实 3D 地标（自由女神像、凯旋门等）+ 桥型结构 + 建造/废墟生命周期 + 3DMR/Wikidata 模型 + Luanti 实验导出 + Legacy Terrain 快速档 | 流式落盘 + Bedrock chunk 并行编码 + 车道宽按 `lanes` 缩放 + 纬度雪线 + 水深雕刻 + 真实跑道 + 烘焙光照 |
| 用户可感知差别 | "我老家教堂终于像教堂了" | 同样 bbox 更省内存、更快出图 |

两版的命名就是各自的价值观："Landmark" 关注视觉质量，"Mosaic" 关注生成效率。

### 8.2 实际 CLI 使用

```bash
# 1. 命令行构建（无 GUI）。--output-dir 是主参数名，--path 是兼容别名
cargo run --no-default-features -- \
  --terrain \
  --output-dir="C:/YOUR_PATH/.minecraft/saves/worldname" \
  --bbox="49.4093,8.6736,49.4264,8.7018"   # 海德堡市中心

# 2. Bedrock 格式（移动端友好）
cargo run --no-default-features -- --bedrock \
  --bbox="40.7580,-73.9855,40.7689,-73.9731"  # 时代广场附近

# 3. 比例调整（0.5 = 每米半个方块；世界边长减半，面积约缩到四分之一）
cargo run --no-default-features -- --scale=0.5 --terrain \
  --output-dir="$HOME/.minecraft/saves/halfscale" \
  --bbox="..."

# 4. 关闭土地覆盖分类（布尔参数用 =false 关闭）
cargo run --no-default-features -- --terrain --land-cover=false \
  --output-dir="$HOME/.minecraft/saves/fast" \
  --bbox="..."

# 5. 只用 AWS Terrain Tiles 高程（跳过区域高分 provider，换取速度）
cargo run --no-default-features -- --terrain --aws-only-elevation \
  --output-dir="$HOME/.minecraft/saves/awsonly" \
  --bbox="..."

# 6. 用 Nix 直接跑（不需要 clone）
nix run github:louis-e/arnis -- --terrain \
  --output-dir=YOUR_PATH/.minecraft/saves/worldname \
  --bbox="min_lat,min_lng,max_lat,max_lng"
```

参数语义（以 v2.9.0 `src/args.rs` 为准）：

| 参数 | 默认 | 说明 |
|------|------|------|
| `--bbox` | 必填 | `min_lat,min_lng,max_lat,max_lng`，唯一无默认值的必填项 |
| `--terrain` | 关 | 开启高程 + 土地覆盖处理 |
| `--scale` | 1.0 | 每米对应多少方块（blocks per meter） |
| `--output-dir`（别名 `--path`） | Java 必填 / Bedrock、Luanti 可选 | Java 不存在会创建；Bedrock 若指定必须是已存在目录（缺省输出到桌面）；Luanti 缺省用系统 worlds 目录 |
| `--bedrock` / `--luanti` | 关 | 二选一，同时给会报错 |
| `--land-cover`（别名 `--city-boundaries`） | 开 | ESA WorldCover 分类；`--land-cover=false` 关闭 |
| `--interior` / `--roof` | 开 | 室内与屋顶生成，同样用 `=false` 关闭 |
| `--no-3d` | 开（3D 模型启用） | 关闭 3DMR + Wikimedia 模型下载 |
| `--rotation` | 0.0 | 顺时针旋转角度，范围 -90 到 90 |
| `--fillground` | 关 | 地下挖空 + 矿石生成（survival 友好） |
| `--ground-level` | -62 | 世界基准地面高度 |
| `--projection` | local | `local` 每次从 (0,0) 起；`web_mercator` 全局投影，用于多代世界拼接 |
| `--disable-height-limit` | 关 | 用捆绑 datapack 扩展 Y 范围（Java 1.21.4+：-2032..2031），实验性 |
| `--aws-only-elevation` | 关 | 跳过区域高分 provider，只用 AWS Terrain Tiles |
| `--bake-lighting` | 关 | 预烘焙 chunk 光照（Voxy/Chunky LOD 场景） |
| `--file` / `--save-json-file` | 无 | 读/存 OSM JSON；两者互斥（同属 location 参数组），bbox 仍需给出以框定范围 |
| `--downloader` | requests | requests / curl / wget |
| `--timeout` | 无 | floodfill 超时秒数（调试用） |

两个值得点名的入口设计：`main.rs` 在超过 250 km²（`MAX_RECOMMENDED_AREA_KM2`）时打一条非阻塞警告，提醒生成会很慢、吃内存、并且**给公共 OSM 和高程服务器造成负载**——允许做，但把代价讲清楚；`--file` 支持喂本地 OSM JSON，重复生成同一区域时不再打 Overpass。

### 8.3 多格式互操作的 Rust 库映射

| 格式 | 文件 | Rust 库 | 支持版本 | 状态 |
|------|------|---------|---------|------|
| Java Anvil | `.mca` region files | `fastanvil` 0.32 + `fastnbt` 2.6 | 1.17+ | 稳定 |
| Bedrock `.mcworld` | zip 压缩的多文件 | `bedrockrs_level` + `bedrockrs_shared`（rev 锁定） | 最新 | 稳定 |
| Luanti Mineclonia | `map.sqlite` | `rusqlite` 0.40 + 自定义 block map | 实验性 | v2.8.0（2026-05）起 |

Bedrock 侧依赖值得单说。`bedrock-crustaceans/bedrock-rs` 是一个多 crate monorepo（`addon`/`core`/`level`/`proto_core`/`shared` 等），Arnis 用 `package` 字段指定其中 `bedrockrs_level` 和 `bedrockrs_shared` 两个 crate，并用 `rev` 钉死版本：

```toml
# Cargo.toml（v2.9.0 节选）
bedrockrs_level = { git = "https://github.com/bedrock-crustaceans/bedrock-rs", rev = "7ef268b", package = "bedrockrs_level" }
bedrockrs_shared = { git = "https://github.com/bedrock-crustaceans/bedrock-rs", rev = "7ef268b", package = "bedrockrs_shared" }
nbtx = { git = "https://github.com/bedrock-crustaceans/nbtx" }

# Freeze nbtx at the last pre-`NbtError`-rename commit; the pinned
# bedrockrs_proto_core leaves it unpinned so cargo update would break it.
[patch."https://github.com/bedrock-crustaceans/nbtx"]
nbtx = { git = "https://github.com/louis-e/nbtx", rev = "551c38ac74f2e68a07d3dbdd354faac0c0ac966e" }
```

`[patch]` 段的注释很典型：被钉住的 `bedrockrs_proto_core` 没有锁 `nbtx` 的版本，一次 `cargo update` 就会撞上上游的 `NbtError` 重命名。Arnis 的解法是 fork + 钉到重命名前的 commit。这是 Rust 生态 monorepo 依赖管理的常见痛点，值得抄的解法。

Luanti（原 Minetest）支持把 block 命名空间抽到独立文件 `luanti_block_map.rs`，避免和 Minecraft 块 ID 写死耦合。文件头注明数据转换自 [rollerozxa/MC2MT](https://github.com/rollerozxa/MC2MT)（"Convert a Minecraft world into a Luanti world"，C++ 原作 Copyright (C) 2016 rollerozxa），3rd3 于 2026 年转成 Rust，按 LGPL-2.1+ 授权。

## §9 发布之后：v3.0 → v3.2

本文初稿截稿于 v2.9.0。此后项目按月一个大版本的节奏推进了三步（以下均出自各版本 release notes）：

- **v3.0.0 "Contour Update"（2026-07-11）**：官方称为 v2.0.0 以来最大的一次发布。高程侧升级为覆盖 20+ 国家的高分辨率数据集（部分区域到 1 米），生成前可以 3D 预览地形；气候接管了生物群系和地表材质，地中海小镇、高山峡谷、北方针叶林观感拉开差距；近 500 个新树种；停车场上有车、水里有船、工地上有吊车和挖掘机，还藏了一个 SpaceX 星舰彩蛋。
- **v3.1.0 "Canopy Update"（2026-08-18）**：真实路牌、交通标志和门牌号；树木改按真实冠层高度图放置，树有多高量多高；卫星水体掩膜被描绘拉直，海岸线干净了一截；scale 下探到 0.05；GUI 记忆设置；**支持本地 `.osm` 文件作为输入**（离线生成的最后一块拼图）；OSM 缺建筑高度时用 Overture 回填。
- **v3.2.0 "Horizon Update"（2026-09-09）**：地图工具栏在地球、月球、火星之间切换，后两者由 NASA 高程档案构建（真实环形山、峡谷和火星极冠）；每栋建筑可以披上真实拍摄的立面照片（内置 113 张，按建筑类型选取）；大区域生成更快、内存更省；Voxy LOD 可随世界预生成；Java 世界可以自定义命名。

一句话概括方向：v2.9.0 解决"生成得动"，v3.x 解决"生成得像"。机制层面的分析（§3-§8）在 v3.2.0 依然大体成立，但逐行核对请以新 tag 为准。

## §10 5 条可复用经验

从 Arnis 的设计里能抽出 5 条对**任何地理 / 数据驱动生成项目**都适用的经验：

### 经验 1：数据源选择按"哪个更准"，不按"哪个更全"

OSM 的 coastline 折线理论上覆盖最完整（志愿者维护 + 全球），但 ESA WorldCover 2021 在 10m 卫星分辨率下海洋识别更稳定。Arnis 对"陆海分界"这个具体语义选了卫星数据，对内陆水体选了 OSM——同一系统里按语义分治，而不是找一份"万能数据源"。

通用化：把"用什么数据源"从"哪个最权威"换成"哪个在当前语义下最准"。前者是站队问题，后者是工程问题。

### 经验 2：provider 的"文档上限"和"实测上限"分开记录

`MAX_ELEVATION_GRID_DIM` 的注释明确记录 USGS 3DEP 文档说 8000、实测 ~3000 就 500、2048 才是可靠档。这种"踩坑经验"如果不写进代码，后来人必然再踩一次。

通用化：所有外部服务的实测上限 / 失败模式 / 延迟分布，应该和"为什么会失败"一起记在代码注释里，和官方文档并存。

### 经验 3：精度降级放在存储层，计算层保持稳定

`ElevationData::heights` 用 f32 存储，理由写在 rustdoc 里：放置时已经取整到方块 Y，f64 精度浪费在一个城市级 bbox 就上千万格的网格上。但**整条后处理链保持 f64**，只在最终构造 `ElevationData` 时降一次精度。

通用化：f32 的 7 位有效数字对"展示用"地理数据足够，但把省内存和保精度拆开——计算算两遍不亏，存两遍真亏。

### 经验 4：Hash 函数按场景选，注释只说必要的

热点路径上的地图用 `FnvHashMap` 替代默认 SipHash，注释只写了一句"hash cost matters"，没有展开难以复现的纳秒级细账。选型逻辑经得起推敲：SipHash 防的是哈希洪水攻击，而 key 是内部生成的坐标，攻击面不存在。

通用化：Rust 默认 `HashMap` 的 SipHash 在 key 不可控时才必要。内部坐标、ID、路径这类 key，`FnvHashMap` / `AHash` 都值得考虑；对外暴露的输入（HTTP query、API 参数）保留 SipHash。优化注释写清楚"为什么这里不一样"，比写一堆测不准的数字更有长期价值。

### 经验 5：错误信息要兜底到底

`is_disk_full_error` 的三条通道里，字符串匹配排在最前——因为顶层错误可能连 downcast 都做不了（缺 `'static` bound）。**永远假设 error chain 中间有不透明的 wrapper**，强类型匹配和字符串兜底不是高低搭配，是必须并存的两层。

通用化：好的错误信息不是"操作失败"，是"因为什么失败 + 用户能做什么"。磁盘满就明说磁盘满，别让用户对着 `os error 28` 猜。

## §11 局限与未解

文章最后要说清楚 Arnis **没解决什么**：

- **纵向拼接仍是逐 bbox 的**——横向已经有 `--projection web_mercator`（EPSG:3857 式全局投影，官方定位就是 multi-generation worlds），但纵向缩放按 bbox 独立计算，压缩比不同的相邻区域纵向对不上。`--disable-height-limit` 扩大 Y 范围能减少触发压缩的概率，但没有消除这个问题
- **不解决"实时生成"**——单次生成从几分钟到更久，取决于 bbox 面积（AWS 博客的口径是"typically completes within minutes, depending on area size"）
- **高程分辨率看地区**——默认按 bbox 自动选区域高分 provider（USGS 1m LiDAR、IGN 1m 等），覆盖不到才回退 AWS Terrain Tiles（约 30m）；山区细节损失主要发生在回退档
- **室内是简易结构**——`--interior` 默认开启，生成的是简化内部，不是完整装修
- **地标覆盖仍在扩张**——数百个地标（v2.8.0 release notes 口径）来自 3DMR 标签 + Wikidata 模型双来源，v2.9.0 加了基督像（PR #1062），还在持续增加

最后一条建议：**用 Arnis 之前先在 OSM 网站上确认目标区域的数据质量**。OSM 在欧洲、日本、北美东海岸覆盖极好；在非洲、东南亚部分区域仍然稀疏。Arnis 不是 OSM 数据的替代品，是 OSM 数据的**体素化渲染器**。

## 自测题

读完后，尝试回答这些问题：

1. Arnis 的四条数据通道（Overpass API、ESA WorldCover、Terrain Tiles、Overture Maps）为什么可以并发下载和处理？
2. IQR 离群检测为什么带一个">5% 就放弃过滤"的计数守卫？没有它会误伤什么？
3. 自适应垂直缩放"能放就真实、放不下才压缩"，这个策略的收益和代价分别是什么？
4. 建筑风格系统如何通过 `WallDepthStyle × RoofType × BuildingCondition` 的三维组合避免"千楼一面"？确定性 RNG 在其中起什么作用？
5. §10 的 5 条可复用经验，哪一条对你的项目最有启发？

## 进阶路径

如果你准备深入 Arnis 的源码或做二次开发，建议按下面顺序推进：

1. **先跑通最小生成** - 用 GUI 或 CLI 生成一个小区域，观察输出，建立直觉。

2. **再读 `retrieve_data.rs` 和 `selector.rs`** - 理解多层回退的下载器和 provider 选择逻辑。

3. **然后读 `elevation/mod.rs` 和 `elevation/postprocess.rs`** - 理解高程流水线的实现，这里的注释本身就值得一读。

4. **最后读 `element_processing/buildings.rs`** - 理解建筑风格系统的实现。

5. **尝试改 `ground_generation.rs`** - 定制土地覆盖到方块的映射规则，适配你的场景。

进阶资源：

- [Arnis GitHub 仓库](https://github.com/louis-e/arnis)
- [AWS Public Sector 博客](https://aws.amazon.com/blogs/publicsector/building-realistic-minecraft-worlds-with-open-data-on-aws-how-arnis-uses-elevation-datasets-at-scale/)
- [OpenStreetMap Wiki](https://wiki.openstreetmap.org/)
- [ESA WorldCover 2021 数据说明](https://esa-worldcover.org/)
- [Overture Maps 文档](https://overturemaps.org/)
- [fastanvil / fastnbt（owengage/fastnbt）](https://github.com/owengage/fastnbt)
- [bedrock-rs（bedrock-crustaceans）](https://github.com/bedrock-crustaceans/bedrock-rs)

---

## 常见问题 FAQ

### Q1：Arnis 生成的世界能直接在生存模式玩吗？

基本能。`--fillground` 会挖空地下并生成矿石（v2.9.0 release notes 明确这是给生存玩家的）。地形、建筑本身都是正常世界数据，其余生存要素按游戏规则运行。

### Q2：bbox 太大导致 Overpass API 限流怎么办？

三条路：把大区域拆成多个小 bbox，横向用 `--projection web_mercator` 保证相邻世界对得上；用 `--save-json-file` 把 OSM 数据缓存成本地 JSON，之后用 `--file` 重放，不再打 Overpass；客户端本来就会自动在 arnis 镜像、官方服务器池和回退池之间轮换，限流时会自己换节点。

### Q3：建筑在 Minecraft 里看起来都一样怎么办？

先看数据源。大城市建筑层数、`roof:shape` 标签完整，生成出来层次分明；小城镇标签稀疏，自动决策链只能靠预设和随机兜底。v2.8.0 起的风格系统（8 种屋顶 + 9 种墙面）已经把同一数据的表达空间拉开了不少，但数据源质量仍是上限。

### Q4：生成速度太慢怎么优化？

按效果排序：`--aws-only-elevation` 跳过区域高分 provider（v2.8.0 起 GUI 里也有等价的 Legacy Terrain 选项）；`--scale` 调小；`--land-cover=false` 关土地覆盖；多线程数用 `RAYON_NUM_THREADS` 环境变量覆盖默认的 90% 上限；服务器部署用 `--no-default-features` 编译，避开 Tauri 的 GUI 依赖。

### Q5：Arnis 和 Minecraft 的 height limit（Y ∈ [-64, 320]）怎么协调？

先保持真实：高程范围乘 scale 之后放得进 366 块可用空间就直接 1:1。放不下才等比压缩。`--disable-height-limit` 换用扩展 Y 范围的 datapack（实验性），高差大的区域基本就不触发压缩了。

---

## 资料口径说明

本文的判断基于以下来源和取径：

1. **版本锚点**：机制分析（§3-§8、§10-§11）以 v2.9.0 tag（2026-06-16）源码为准，关键函数（`fetch_elevation_data`、`filter_elevation_outliers`、`repair_terrain_anomalies`、`fill_nan_values`、`scale_to_minecraft`、`is_disk_full_error`、`snow_line_meters`、`highway_block_range`、`OvertureBuilding`）均对照该 tag 逐一核实；v3.0.0 / v3.1.0 / v3.2.0 的内容出自各自 release notes（§9）
2. **AWS Public Sector 博客**：2026-03-03，"Building realistic Minecraft worlds with Open Data on AWS"（作者 Louis Erbkamm、Cristian Chicas），八步流水线、Terrarium 公式、近 30 万用户、Terrain Tiles 迁移均引自原文；经 Wayback Machine 存档核读
3. **仓库读数**：18,088 stars / 1,516 forks / 130 open issues（含 PR）为 2026-09-29 GitHub API 读数；16,259 / 1,355 / 116 为本文原稿 2026-06-24 记录，两口径并列供对照
4. **CLI 参数**：以 v2.9.0 `src/args.rs` 与 `main.rs` 为准；`--path` 是 `--output-dir` 的兼容别名
5. **事实边界**：项目迭代很快（月度大版本），逐行行为以所用版本的源码为准；本文未实际运行全部参数组合，内存数字除源码注释（16384² f64 ≈ 2 GB、峰值约 6 GB、千万格 f64 ≈ 80 MB）外不再另行背书
6. frontmatter 的 `date` 是本文首发时间，`lastmod` 是本轮复核时间

---

**附录：项目关键链接**

- 仓库：<https://github.com/louis-e/arnis>
- 官网：<https://arnismc.com/>
- 在线版 MapSmith：<https://arnismc.com/mapsmith/>
- AWS Public Sector 博客：<https://aws.amazon.com/blogs/publicsector/building-realistic-minecraft-worlds-with-open-data-on-aws-how-arnis-uses-elevation-datasets-at-scale/>
- Hackaday 报道（2024-12-30）：<https://hackaday.com/2024/12/30/bringing-openstreetmap-data-into-minecraft/>
- 作者 Louis：<https://buymeacoffee.com/louisdev>
