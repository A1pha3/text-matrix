---
title: "GeoLibre：跨平台开源 GIS 分析平台"
date: "2026-07-31T02:53:11+08:00"
draft: false
categories: ["技术笔记"]
tags: ["GIS", "MapLibre", "Tauri", "DuckDB", "开源"]
description: "GeoLibre 是基于 Tauri v2、MapLibre GL JS 和 DuckDB-WASM Spatial 构建的跨平台开源 GIS 工具，支持 Web、桌面、移动端和 Jupyter 多环境。"
slug: opengeos-geolibre-cross-platform-gis-guide

---

## 项目概览

GeoLibre 是由 GIS 领域知名贡献者 Qiusheng Wu（opengeos）发起的开源地理信息系统（GIS, Geographic Information System）平台。它的核心定位是 **"一套代码，多端运行，数据本地化"**：浏览器、桌面（Windows / macOS / Linux）、原生 Android、Google Play 上架包、Jupyter Notebook / Colab、PyPI / conda-forge / AUR / Flatpak / Microsoft Store / CodeSandbox 全部共享同一份 React + TypeScript 工作区。

相比 QGIS、ArcGIS Pro 这类传统桌面 GIS，GeoLibre 把"轻量、零安装、跨端一致体验"放到了产品哲学的最前面。用户在浏览器里打开 [web.geolibre.app](https://web.geolibre.app/) 就能获得一个完整可用的 GIS 工作台；如果需要处理敏感数据或大文件，再切到桌面端或 Jupyter，二者共享同一份项目格式 `.geolibre.json`。这种"同源同构"（same source, same shape）的设计在开源 GIS 圈子里相当罕见——大多数同类工具要么是纯桌面（QGIS），要么是纯 Web（kepler.gl、Mapbox Studio），很少有项目愿意同时维护五个发行渠道。

项目的 release 节奏稳定，每个版本都在 [Zenodo](https://doi.org/10.5281/zenodo.20785400) 上 mint DOI，方便学术引用。截至 2026 年 7 月，1.0 版本已正式发布，并同步登陆 Microsoft Store、Google Play、FlatHub（FlatPark）、AUR、PyPI、conda-forge、CodeSandbox。

## 核心能力

GeoLibre 不是单纯的地图可视化工具，它的能力边界相当宽，可以拆成六个层次看。

### 多格式数据导入

平台内置覆盖了几乎所有主流 GIS 数据格式：GeoJSON、Shapefile（自动解压 zip）、KML/KMZ（自带保留 Google Earth 内嵌样式的解析器）、GeoParquet、GPX、FlatGeobuf、PMTiles、MBTiles、Zarr、LiDAR 点云、Gaussian Splats（高斯泼溅）、COG/GeoTIFF、ArcGIS FeatureServer/VectorTileServer、XYZ/WMS/WMTS、3D Tiles（tileset）、Overture Maps、Microsoft Planetary Computer 与 Google Earth Engine。

值得称道的是 KML 处理路径：内置解析器读取 KML 时会保留 `simplestyle-spec` 属性（fill、stroke、stroke-width 等），按要素单独着色；当遇到解析器无法识别的 KML 节点，再 fallback 到 DuckDB Spatial 读取几何，但样式会丢失。这种"先精致回退，再功能回退"的两段式策略，比大多数 GIS 工具直接一刀切更贴近用户预期。

### 空间 SQL 工作台

SQL Workspace 是 GeoLibre 最具差异化的功能之一。它不是一个简易的查询框，而是同时提供三种 SQL 引擎供用户切换：

- **DuckDB-WASM Spatial** —— 默认引擎，纯浏览器运行，零网络依赖；
- **PGlite / PostGIS** —— WebAssembly 编译的 PostgreSQL + PostGIS，适合熟悉 PG 生态的用户；
- **Apache Sedona（SedonaDB）** —— 通过本地 FastAPI sidecar 或 CereusDB（SedonaDB 的 WASM 版）在浏览器里跑 DataFusion + Arrow 的空间 SQL 引擎。

三种引擎共享同一个 SQL 编辑器和结果渲染层，切换引擎不会丢失查询上下文。这种"前端可见、底层可换"的 SQL 工作台在 GIS 圈子里几乎是孤品。

### 700+ 客户端地理处理

Processing → Vector 菜单下提供 700 多个客户端地理处理工具（GIS Tools），底层走 Turf.js，无需后端。当用户安装 Python sidecar 的 `vector` extra（GeoPandas + Shapely）后，工具会自动切换到 projection-aware（投影感知）的版本；当 sidecar 不可用时，浏览器端还有一个 **Pyodide** 引擎——CPython 编译到 WebAssembly 的产物，让 GeoPandas/Shapely 也能在纯浏览器环境运行。

三个引擎共享 `backend/geolibre_server/geolibre_server/vector_ops.py` 这一个 geometry 模块，Vite 插件将其复制到 bundle，Pyodide Worker 从 CDN 加载 Pyodide 后调用 `run_vector_tool`。结果是：**桌面 sidecar、Pyodide 浏览器引擎返回的结果完全一致**，因为代码是同一份。

### 3D 与行星底图

平台默认走 MapLibre GL JS 二维矢量瓦片，但每个分屏（split pane）都可以切换到 CesiumJS 3D 地球模式，呈现 3D Tiles、GeoJSON 立体化、栅格/矢量瓦片叠加。更有趣的是底图（basemap）系统支持**行星级别切换**：地球、月球、火星、水星、金星、木卫一（Io）、欧罗巴（Europa）、甘尼米德（Ganymede）、卡利斯托（Callisto）、泰坦（Titan）、冥王星、冥卫一（Charon）——每个项目可以单独配置 ellipsoid（参考椭球体），所以距离、面积、缩放比例都按所选天体计算。背后的底图来源是 OpenPlanetaryMap 和 USGS Astrogeology。

Atmosphere Effects 插件提供深空星空背景、视差星场、彗星轨迹和地球大气光晕。它的视觉设计借鉴了 Leonel Dias 的《Globe atmosphere, halo, and comets》一文中的 Canvas 2D 分层方案、"screen" 混合模式和 limb-sampling 思路。

### 属性表与时空动画

矢量图层自动生成可排序、可过滤的属性表（attribute table），选中要素后地图会定位并高亮；Time Slider 插件配合 `maplibre-gl-time-slider`，把 COG、XYZ/WMTS、WMS-Time、按时间过滤的 GeoJSON 全部接到一条可拖动的时间轴上。纽约曼哈顿建筑按 1850–2025 建造年份逐年浮现的演示（[nyc-buildings-and-subways](https://share.geolibre.app/giswqs/nyc-buildings-and-subways)）就是这条时间轴的典型用法。

### 项目共享与可嵌入

每个项目保存为 `.geolibre.json`，包含图层、视图、样式、SQL 查询甚至分屏 2D/3D 配置。把这份 JSON 传到 [share.geolibre.app](https://share.geolibre.app) 就生成可分享链接；通过 `<iframe>` 或 SDK 嵌入到第三方页面时支持只读视图、限定工具栏等场景。

## 技术栈拆解

GeoLibre 的前端是 npm workspaces monorepo，核心包划分为六层：

| 包 | 职责 |
|---|---|
| `@geolibre/core` | 领域类型、项目 JSON schema、全局状态（Zustand store） |
| `@geolibre/map` | MapLibre 生命周期、图层同步、GeoJSON / 栅格 / 瓦片 / MBTiles、控制与选中样式 |
| `@geolibre/ui` | shadcn 风格的共享 UI 原子组件 |
| `@geolibre/processing` | 客户端算法注册表 |
| `@geolibre/plugins` | 插件接口与内建插件 |
| `geolibre-desktop` | 外壳布局、Tauri I/O、组合 |

整套架构的关键设计原则是 **"store 与引擎解耦"**。`@geolibre/core` 持有的是普通 `GeoLibreLayer` 记录与 `MapViewState`（不是 MapLibre 对象），因此 MapLibre 是默认渲染器，Cesium 可以在不修改 store 的情况下作为"另一种渲染器"订阅同一个状态——这就是 3D 地球分屏不需要做引擎抽象层（engine abstraction layer）的原因。同样的模式让 SecondaryMapCanvas 双向同步、CesiumCanvas 双向同步、layer sync 复用 per-pane 可见性覆盖与组合效果都成为自然结果。

### DuckDB-WASM Spatial 的角色

DuckDB-WASM 承担的是 **"需要转换才能渲染的格式"** 这一段流水线的责任。具体来说：

```sql
INSTALL spatial;
LOAD spatial;
```

GeoParquet 直接走 DuckDB Parquet reader + Spatial extension；其他本地矢量格式先尝试 Spatial 的 `ST_Read`，如果 WASM 扩展装不下 GDAL reader 就走 shpjs 或自研 KML parser。整个矢量导入路径对用户是透明的——他们只在 Add Data 对话框里看到一份文件列表，背后由 DuckDB 在浏览器进程里悄悄完成了格式归一化。

### Cesium 与 MapLibre 的双向相机同步

CesiumCanvas 与 MapLibre canvas 之间要双向同步，相机模型却完全不同：MapLibre 用 Web-Mercator + nadir-referenced pitch + bearing；Cesium 用 metric range + horizon-referenced pitch + heading。`packages/map/src/cesium-camera.ts` 的解决方案是 **按"地面分辨率"（ground resolution, 米/像素）对齐**——这样即使两个分屏高度不同，屏幕上同一物体的尺寸仍然一致。同步环路里有一个 tolerance 检查来抑制 apply → `moveEnd` 回声，避免抖动。

### 离线策略（PWA）

独立 Web 构建是可安装的 PWA（Progressive Web App, 渐进式 Web 应用）。Workbox 策略拆得很细：

- **App shell 预缓存** —— HTML 与启动 JS/CSS chunk 预缓存，第二次访问离线即用；
- **CacheFirst 运行时缓存** —— 内容哈希化的 `/assets/` 下的 MapLibre、DuckDB-WASM Spatial、MapLibre feature-plugin chunk 在首次使用后缓存，让本地文件工作流（DuckDB Spatial 转换）首次联网跑通后就能离线使用；
- **底图白名单缓存** —— 仅 CORS 友好的 OpenFreeMap、CARTO 默认底图缓存，其他远程服务（私有 WMS、ArcGIS、企业瓦片）刻意不缓存。

Pyodide 与 PGlite/PostGIS 默认从 jsDelivr CDN 加载（cross-origin），service worker 不缓存，所以这两个引擎**默认非离线可用**。把 `VITE_PYODIDE_INDEX_URL` 指向同源镜像可以让 Pyodide 可缓存；`GEOLIBRE_PGLITE_CDN=0` 构建可以把 PostGIS 重新打入 bundle（代价是 ~22 MB 重新进入 Tauri 二进制）。这种"明确告诉用户哪些是离线的、哪些不是"的设计比一刀切的离线保证更诚实。

## 多平台架构

GeoLibre 同一份代码通过四条独立路径分发，每条路径适配自己的运行时约束：

### 桌面：Tauri v2

桌面壳由 Tauri v2 提供，承载 React UI + MapLibre + DuckDB-WASM + Cesium 的完整 WebView。Tauri 的能力边界决定了哪些功能是"桌面独占"的：

- **本地文件系统** —— 通过 dialog-selected path 读取 MBTiles、Shapefile、GeoTIFF，避免浏览器沙箱；
- **Rust 原生 HTTP 客户端** —— `guarded_http_client` 在 native 进程里跑 tile / style / OGC GetCapabilities 拉取，并**信任系统证书存储**（OS trust store），企业 CA 无需额外配置；
- **mTLS 双向认证** —— `GEOLIBRE_HTTP_CLIENT_CERT` 指向 .pem（PKCS#8 unencrypted 私钥）或 .p12/.pfx 证书，`GEOLIBRE_HTTP_CLIENT_CERT_PASSWORD` 触发 PKCS#12 路径；
- **Python sidecar** —— 桌面启动时按需 spawn FastAPI，绑定 127.0.0.1，把 Python 处理栈挡在浏览器 bundle 之外。

### Android：原生 Tauri 目标

Android 走 Tauri 移动目标，已经上架 Google Play。UI 自适应响应式布局给小屏做了专门适配。

### Web：构建产物 + PWA

`apps/geolibre-desktop` 的 Vite 构建产物同时产出 Web 版本。容器镜像（`ghcr.io/opengeos/geolibre`）用 nginx 托管 `dist/` 静态资源，并把 Python sidecar（uvicorn）反向代理到 `/sidecar`，浏览器通过同源访问避免 CORS。`GEOLIBRE_DISABLE_SIDECAR=1` 可关掉 sidecar 只跑 nginx。

### Jupyter：PyPI / conda-forge 嵌入式 wheel

Python 包把 GeoLibre Web 构建以 `GEOLIBRE_EMBED=1` 标志嵌入到 wheel 里，配合 Notebook Panel 在 Jupyter / Colab 里直接渲染。这是六个发行渠道里最特别的一个——它把 Web 应用反过来嵌入 Python 内核，让"用 Python 处理数据 + 用 GeoLibre 可视化"在同一进程里闭环。

## 适用场景

GeoLibre 的能力组合决定了它特别适合以下几类工作：

**教育与培训**——零安装门槛让老师和学生能在浏览器里完成整个 GIS 课程，Jupyter 集成又让数据科学课程可以在 notebook 里嵌入地图。

**现场数据采集与回放**——Android 原生应用 + 离线缓存适合野外作业，回到办公室再切到桌面做深度分析。

**敏感数据本地处理**——DuckDB-WASM + 本地文件 + 不上传的设计，让它在涉密、隐私、医疗、政务场景里比 SaaS 模式更可接受。

**科研可复现性**——Zenodo DOI 引用 + `.geolibre.json` 项目格式 + Jupyter 嵌入式发布，构成完整的可复现研究流水线。

**轻量 Web 地图嵌入**——`share.geolibre.app` 链接 + iframe 嵌入让博客、新闻、报告里塞一张可交互地图的成本极低。

**Python 生态 GIS 工作者**——sidecar 的 GeoPandas/Shapely 路径补齐了 Python 桌面 GIS 长期存在的"无轻量开源选择"的空白。

## 边界与不足

坦诚地说，GeoLibre 并非没有短板，几个值得在上手前了解的边界：

**WebKitGTK 性能悬崖**。Linux 桌面走 WebKitGTK，它的 WebGL/合成路径显著慢于 Chromium。在低缩放级别（low zoom）下任何瓦片层都会触发持续加载，导致 FPS 跌到个位数。这是 WebView 引擎本身的限制，不是 GeoLibre 的 bug，但 Linux 用户会感受到明显的卡顿。可考虑临时调高 `maxTileCacheSize`、用 512px 栅格瓦片替代 256px、`fadeDuration: 0`，但目前这些缓解措施还没有默认启用。

**PostGIS 引擎离线受限**。PGlite/PostGIS 默认从 jsDelivr 加载，首次使用需要联网。完整离线需要自建 CDN 镜像或重新打包。

**桌面端与 Web 端的边界差异**。某些依赖 Tauri 文件系统访问的流程（MBTiles 自定义协议、私有文件系统路径）只能在桌面跑；纯 Web 走浏览器沙箱，能用的源受限于 CORS。文档明确指出"依赖桌面文件系统的功能仍需安装桌面应用"。

**Cesium 球面需要 token**。Cesium World Imagery 与 Terrain 需要 Cesium Ion token，没有 token 时分屏的 2D/3D 切换按钮自动隐藏。Token 可以构建时（`CESIUM_TOKEN`）或运行时（Settings → Environment Variables 里的 masked field）配置，运行时配置存在 `DesktopSettings` 的 localStorage 里、永远不会写入 `.geolibre.json`。

**插件生态还在早期**。插件 API 是 MapLibre 类型的，Cesium 视图不是插件——这意味着社区贡献的第三方插件数量还不多。`plugins.geolibre.app` 是官方插件市场，但相比 QGIS 的成熟插件库仍有差距。

**Python sidecar 的 vector / sedona extra 是可选的**。默认安装不包含 GeoPandas、Shapely、Apache Sedona，需要显式安装 `geolibre[vector]` 或 `geolibre[sedona]` 才能用投影感知的矢量工具与 Sedona SQL。

## 小结

GeoLibre 把"开源、轻量、跨端、数据本地"这四个传统上互相矛盾的要求缝合到了一个统一的 npm workspace 里。它的关键技术决策——store 与渲染引擎解耦、DuckDB-WASM 做浏览器内格式归一化、Cesium 作为"另一种渲染器"而非新引擎、三种 SQL 引擎共享一份 UI、Python sidecar 与 Pyodide 共用同一份 geometry 模块——都体现了一个清晰的取舍：把跨端一致性放在性能峰值之前，把数据主权放在云端便利之前。

对于需要"一个工具覆盖教学、现场、分析、嵌入、复现"全流程的 GIS 工作者，GeoLibre 值得花一个下午时间把文档通读一遍。它的文档结构（Getting Started / Features / Demos / User Guide / Tutorials / Reference 七大块）也折射出项目自身的成熟度。

---

## 参考

- [GeoLibre Web](https://web.geolibre.app/)
- [GeoLibre 项目仓库](https://github.com/opengeos/GeoLibre)
- [Architecture 文档](https://github.com/opengeos/GeoLibre/blob/main/docs/architecture.md)
- [Features 文档](https://geolibre.app/features/)
- [Zenodo 引用](https://doi.org/10.5281/zenodo.20785400)
- Wu, Q. (2026). *GeoLibre: A lightweight, cloud-native GIS platform for visualizing, exploring, and analyzing geospatial data*. Zenodo.