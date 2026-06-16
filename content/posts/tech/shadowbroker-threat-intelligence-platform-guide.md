---
title: "ShadowBroker：开源全球威胁情报平台，60+ 数据源实时聚合"
date: "2026-05-17T20:10:00+08:00"
slug: "shadowbroker-threat-intelligence-platform-guide"
aliases:
  - "/posts/tech/shadowbroker-open-source-intelligence-platform/"
  - "/posts/tech/shadowbroker-global-threat-intelligence-platform/"
  - "/posts/tech/shadowbroker-osint-geospatial-intelligence-platform/"
  - "/posts/tech/shadowbroker-security-tool-guide/"
description: "ShadowBroker 是一个开源实时地理空间情报平台，聚合航空、航海、卫星、冲突、无线电等 60+ 公共数据源于单一暗色地图界面。本文从入门到精通全面解析其功能特性、架构设计、Docker 部署、AI 智能体集成与隐私安全模型。"
draft: false
categories: ["技术笔记"]
tags: ["ShadowBroker", "OSINT", "威胁情报", "Python", "Next.js", "FastAPI", "MapLibre", "AI Agent", "开源情报"]
---

# ShadowBroker：开源全球威胁情报平台，60+ 数据源实时聚合

## 学习目标

- 了解 ShadowBroker 的项目定位与设计思路
- 掌握其 60+ 数据层功能特性（航空、航海、卫星、冲突、无线电等）
- 理解 ShadowBroker 的整体技术架构
- 熟练通过 Docker 和 Kubernetes/Helm 部署 ShadowBroker
- 学会将 AI 智能体（如 OpenClaw）接入 ShadowBroker 的 HMAC 命令通道
- 了解 InfoNet 去中心化通信网络与 Sovereign Shell 治理经济模型

---

## 1. 项目概览

**ShadowBroker**（GitHub: [BigBodyCobain/Shadowbroker](https://github.com/BigBodyCobain/Shadowbroker)，Star: 6,706，Fork: 1,077）是一个去中心化实时地理空间情报平台，将来自全球的公共 OSINT（开源情报）遥测数据聚合到同一个暗色作战地图界面中。

**设计思路：** 大量全球遥测数据已经是公开的——飞机 ADS-B 广播、海事 AIS 信号、卫星轨道数据、地震传感器、网格无线电网络、警察扫描仪信号、环境监测站、互联网基础设施遥测数据——这些数据散布在数十种工具和 API 中，ShadowBroker 将它们全部整合到一个界面里。

**关键约束：** ShadowBroker 不引入新的监控能力，它只聚合和可视化已有的公开数据集。完全开源，任何人都可以审计具体访问了哪些数据、如何访问的。仪表板完全在浏览器中运行，对接自托管后端。不收集也不传输任何用户数据，无遥测、无分析、无账号。

| 指标 | 数值 |
|------|------|
| GitHub Stars | 6,706 |
| GitHub Forks | 1,077 |
| 主要语言 | Python（66 万行）、TypeScript（37 万行）、Rust（26 万行） |
| License | AGPL-3.0 |
| 框架 | Next.js + MapLibre GL + FastAPI + Python |
| 发布时间 | 2026 年 3 月 5 日 |
| 最新版本 | v0.9.7 |

---

## 2. 核心数据层功能详解

ShadowBroker 提供了 **35+ 可切换数据层**，涵盖航空、航海、太空、冲突、无线电、环境、基础设施等多个域。下面按类别逐一介绍。

### 2.1 航空追踪 🛩️

通过 OpenSky Network 和 adsb.lol 两个来源，ShadowBroker 实现了覆盖全球的实时航班追踪：

- **商业航班**：通过 OpenSky Network 追踪约 5,000+ 架次民航飞机（约 60 秒更新）
- **私人飞机**：区分 Light GA（轻型通用航空）、涡轮螺旋桨飞机和商务机
- **私人飞机机主识别**：高净值个人的飞机含机主身份标注
- **军事航班**：通过 adsb.lol 军事端点追踪加油机、ISR（情报监视侦察）机、战斗机、运输机
- **飞行轨迹累积**：所有追踪飞机的持久面包屑轨迹
- **盘旋模式检测**：自动标记总转弯超过 300° 的盘旋飞机
- **接地检测**：低于 100 英尺 AGL 的飞机以灰色图标渲染
- **Air Force One 专项追踪**：美国总统/副总统专机从起飞起即高亮监控

> ⚠️ **重要提示**：OpenSky API 凭证为全局飞行覆盖的**关键必需项**。若无凭证，航班层将回退到纯 ADS-B 模式，在非洲、亚洲和拉丁美洲存在显著覆盖缺口。

### 2.2 航海追踪 🚢

- **AIS 船只流**：通过 aisstream.io WebSocket 实时追踪 25,000+ 艘船只
- **船只分类**：货船、油轮、客轮、游艇、军用舰艇分类展示，带颜色编码图标
- **美国航母打击群追踪器**：追踪全部 11 艘现役美国海军航母——通过 GDELT 新闻自动解析航母移动报道来估算位置，配合 50+ 地理区域坐标映射（如"东地中海"→经纬度），磁盘缓存位置，每天 00:00 和 12:00 UTC 自动刷新。**目前没有任何其他开源工具具备此功能。**
- **游艇追踪**：亿万富翁超级游艇单独标记
- **渔业活动**：Global Fishing Watch 船只事件（新功能）
- **集群展示**：低缩放级别时船只聚合显示数量标签，放大后散开

### 2.3 太空与卫星 🛰️

- **轨道追踪**：通过 CelesTrak TLE 数据 + SGP4 算法实时计算 2,000+ 在轨卫星位置（无需 API 密钥）
- **任务类型分类**：按颜色编码区分：红色=军用侦察，青色=SAR（合成孔径雷达），白色=SIGINT（信号情报），蓝色=导航，品红=预警，绿色=商业成像，金色=空间站
- **SatNOGS 地面站**：业余卫星地面站网络含实时观测数据
- **TinyGS LoRa 卫星**：LoRa 卫星星座追踪

### 2.4 地缘政治与冲突 🌍

- **全球事件**：GDELT 驱动冲突事件聚合（最近 8 小时，约 1,000 起事件）
- **乌克兰前线**：来自 DeepState Map 的实时战争前线 GeoJSON（约 30 分钟更新）
- **乌克兰空袭警报**：实时地区防空警报
- **SIGINT/RISINT 新闻订阅**：多情报来源 RSS 实时聚合，用户可自定义最多 20 个来源并配置优先级权重（1-5）
- **区域档案（Dossier）**：右键点击地球上任意位置，获取即时情报简报：
  - 国家概况（人口、首都、语言、货币、面积）
  - 现任国家元首和政府类型（实时 Wikidata SPARQL 查询）
  - 本地 Wikipedia 摘要含缩略图
  - 最新 Sentinel-2 卫星照片，含拍摄日期和云量覆盖率（10 米分辨率）

### 2.5 卫星图像 🛰️

- **NASA GIBS (MODIS Terra)**：每日真彩色卫星影像叠加，含 30 天时间滑块、播放/暂停动画和透明度控制（约 250 米/像素）
- **高分辨率卫星（Esri）**：通过 Esri World Imagery 提供亚米级分辨率影像（18 级以上可放大到建筑细节）
- **Sentinel-2 情报卡**：右键获取任意地点最新 Sentinel-2 卫星照片，含拍摄日期、云量百分比和可点击的全分辨率图像（10 米分辨率，约 5 天更新一次）
- **VIIRS 夜灯**：夜灯变化检测叠加（新功能）
- **五种视觉模式**：通过 STYLE 按钮切换整张地图的美学风格：
  - **DEFAULT** — 深色 CARTO 底图
  - **SATELLITE** — 亚米级 Esri World Imagery
  - **FLIR** — 热成像美学（反色灰度）
  - **NVG** — 夜视绿色磷光
  - **CRT** — 复古终端扫描线叠加

### 2.6 SAR 地表变化检测 🛰️（新功能 v0.9.7）

合成孔径雷达（SAR）可在云层和夜间穿透检测地表变化，提供两种模式：

- **模式 A（目录）**：来自阿拉斯加卫星设施的自由 Sentinel-1 场景元数据，无需账号，显示雷达何时过境关注区域以及下一次何时经过
- **模式 B（完整异常）**：来自 NASA OPERA（DISP、DSWx、DIST-ALERT）和 Copernicus EGMS 的实时地表变化警报，需要免费的 NASA Earthdata 账号（应用内向导引导设置，约 1 分钟完成）

**异常类型**：地表变形（毫米级沉降、滑坡）、水面变化（洪水范围）、植被干扰（森林砍伐、烧伤疤痕、弹坑）、损坏评估（UNOSAT/Copernicus EMS 验证）、相干性变化检测

**地图可视化**：按类型颜色编码的异常图钉（橙色=变形，青色=水，绿色=植被，红色=损坏，紫色=相干），AOI 边界以虚线多边形绘制，按类别着色。点击任意图钉弹出详细信息面板，含震级、置信度、解算器、场景数和来源链接。

**AOI 编辑器**：直接从地图定义关注区域（Area of Interest）。激活 SAR 图层后点击"EDIT AOIs"按钮，使用十字准星工具在地图上点击放置 AOI 中心，设置名称、半径（1-500 公里）和类别。

### 2.7 软件定义无线电与 SIGINT 📻

- **KiwiSDR 接收器**：全球 500+ 公共 SDR 接收器以琥珀色聚合标记标绘
- **实时无线电调谐器**：点击任意 KiwiSDR 节点在 SIGINT 面板中打开嵌入式 SDR 调谐器
- **元数据显示**：节点名称、位置、天线类型、频段、活跃用户
- **Meshtastic 网格无线电**：MQTT 集成网格无线电节点地图，整合进 Mesh Chat
- **APRS 集成**：通过 APRS-IS TCP feed 获取业余无线电定位
- **GPS 干扰检测**：实时分析飞机 NAC-P（导航精度类别）值，以网格聚合识别干扰区域，红色叠加方块含"GPS JAM XX%"严重性标签
- **无线电截获面板**：Scanner 风格 UI 接入 OpenMHZ 警用/消防扫描仪订阅，点击任意系统实时监听，扫描模式自动循环遍历活跃订阅

### 2.8 监控摄像头 📷

- **CCTV Mesh**：13 个来源覆盖 6 个国家/地区共 11,000+ 实时交通摄像头：
  - 🇬🇧 伦敦 Transport for London JamCams
  - 🇺🇸 纽约 NYC DOT、奥斯汀 TX（TxDOT）
  - 🇺🇸 加利福尼亚（12 个 Caltrans 区）、华盛顿州（WSDOT）、佐治亚州 GDOT、伊利诺伊州 IDOT、密歇根州 MDOT
  - 🇪🇸 西班牙 DGT National（20 个城市）、马德里市（357 个摄像头 via KML）
  - 🇸🇬 新加坡 LTA
  - 🌍 Windy Webcams
- **多格式自动检测**：支持视频、MJPEG、HLS、嵌入、卫星瓦片和图像馈送自动检测渲染
- **地图聚合**：绿色圆点聚合带数量标签，放大后散开

### 2.9 环境与灾害监测 🔥

- **NASA FIRMS 火灾热点（24 小时）**：NOAA-20 VIIRS 卫星每周期更新全球 5,000+ 热异常点，火焰形状图标按火灾辐射功率（FRP）颜色编码
- **火山**：全球史密森尼全球火山项目全新世火山标绘
- **天气警报**：含紧迫性/严重性指标的重大天气多边形警报
- **空气质量（PM2.5）**：全球 OpenAQ 站实时颗粒物读数
- **地震（24 小时）**：USGS 实时地震馈送含震级缩放标记
- **空间天气徽章**：底部状态栏实时 NOAA 地磁风暴指示器，颜色编码 Kp 指数（绿色=平静，黄色=活跃，红色=风暴 G1-G5）

### 2.10 基础设施监测 🏗️

- **互联网中断监测**：来自佐治亚理工 IODA 的区域互联网连接警报
- **数据中心映射**：全球 2,000+ 数据中心，含运营商、位置和自动互联网中断交叉引用
- **军事基地**：全球军事设施和导弹设施数据库
- **发电厂**：WRI 数据库全球 35,000+ 发电厂

### 2.11 铁路追踪 🚆（v0.9.6 新功能）

- **Amtrak 列车**：美国 Amtrak 列车实时位置，含速度、方向、路线和状态
- **欧洲铁路**：DigiTraffic 欧洲列车位置集成

### 2.12 Shodan 设备搜索 🔍（v0.9.6 新功能）

- **互联网设备搜索**：直接在 ShadowBroker 中查询 Shodan，按关键词、CVE、端口或服务搜索，结果作为实时叠加标绘在地图上
- **可配置标记**：Shodan 结果的形状、颜色和大小可自定义
- **用户自供 API**：使用自己的 `SHODAN_API_KEY`，结果作为本地调查叠加渲染

---

## 3. AI 智能体命令通道 🤖

ShadowBroker v0.9.7 将平台从一个人类观看的仪表板转变为一个任何智能体都可以操作的智能表面。

### 3.1 通道传输层

ShadowBroker 暴露了一个**双向 AI 智能体命令通道**——一个签名、按层分级的桥接，给任何兼容的 AI 智能体提供对情报平台的完整读/写访问权限。OpenClaw 是参考智能体，但通道是一个开放协议：任何使用 HMAC-SHA256 签名的 LLM 驱动智能体（Claude Code、GPT、LangChain、自定义 Python/TypeScript 客户端等）都可以作为看到与操作员相同数据的分析师进行连接。

**单一命令通道**：`POST /api/ai/channel/command` 接受 `{cmd, args}` 并分派到任意注册工具。

**批量并发执行**：`POST /api/ai/channel/batch` 单次请求最多接受 20 个命令，后端并发运行并返回扇出结果映射，将智能体延迟降低一个数量级。

**HMAC-SHA256 签名**：每个命令都使用 `HMAC-SHA256(secret, METHOD|path|timestamp|nonce|sha256(body))` 签名，含时间戳+nonce 重放保护和请求完整性验证。支持本地模式（无需配置）和远程模式（智能体在不同机器/VPS 上）。

**层分级访问**：`OPENCLAW_ACCESS_TIER` 控制智能体可以调用哪些命令：`restricted` 暴露只读集合，`full` 增加写入和注入。发现端点返回 `available_commands` 使智能体可以自省自身能力。

### 3.2 智能体能力

- **完整遥测访问**：查询所有 35+ 数据层，含地理坐标、时间戳和来源归属的丰富数据
- **AI 情报图钉**：直接在操作员的地图上放置颜色编码的调查标记，14 种类别（威胁、异常、军事、海事、航空、SIGINT、基础设施等），含置信度分数、TTL 过期时间、来源 URL，支持一次最多 100 个图钉批量放置
- **地图控制**：将操作员的地图视图飞到任意坐标、触发卫星图像查询和打开区域档案
- **SAR 地表变化**：查询 SAR 异常馈送、检查图钉详情、管理 AOI，并将地图飞到关注区域
- **原生层注入**：将自定义数据直接推入 ShadowBroker 原生层（摄像头、船只、SIGINT 节点、军事基地等），使智能体发现的数据与真实馈送一起渲染
- **Wormhole 网状参与**：智能体可以加入去中心化 InfoNet、发布签名消息、加入加密门频道、发送/接收加密 DMs，并与 Meshtastic 无线电和 Dead Drop 交互——作为完整网状节点运行
- **Sovereign Shell 参与（v0.9.7）**：以编程方式提交请愿书、签署和投票治理变更、在解决方案和争议上下注、标记 Heavy-Node 升级就绪状态
- **地理编码和邻近扫描**：将地名解析为坐标，然后在半径内扫描所有层获取完整邻近摘要
- **新闻和 GDELT 位置附近**：获取任意坐标附近的 GDELT 冲突事件和聚合新闻文章
- **警报传递**：通过 Discord webhook 和 Telegram 频道发送品牌化情报简报、警告和威胁通知
- **情报报告**：生成结构化报告，含摘要统计、顶级军事航班、相关性、地震活动、SIGINT 计数和图钉清单

---

## 4. InfoNet 去中心化通信网络 🌐

### 4.1 通信层

- **InfoNet 实验测试网**：全球混淆消息中继，任何运行 ShadowBroker 的人都可收发消息，消息通过 Wormhole 中继层传输，含门身份、Ed25519 规范有效载荷签名和传输混淆
- **Mesh Chat 面板**：三标签界面 — **INFONET**（门聊天含混淆传输）、**MESH**（Meshtastic 无线电集成）、**DEAD DROP**（点对点消息交换，token 时代邮箱——当前最强链路）
- **门身份系统**：含 Ed25519 签名密钥、预密钥束、SAS 词联系验证和滥用报告的假名身份
- **Mesh Terminal**：内置 CLI：`send`、`dm`、市场命令、门状态检查，可拖动面板，可最小化到顶部栏

### 4.2 Sovereign Shell 治理经济（新功能 v0.9.7）

将 InfoNet 从聊天层提升为完整治理经济体系：

- **请愿书 + 治理 DSL**：通过签名请愿书进行链上参数变更，`UPDATE_PARAM`、`BATCH_UPDATE_PARAMS`、`ENABLE_FEATURE`、`DISABLE_FEATURE` 的类型安全有效载荷执行器
- **升级哈希治理**：需要新逻辑的协议升级投票 SHA-256 验证版本，80% 超级多数、40% 法定人数、67% Heavy-Node 激活
- **解决方案和争议市场**：在市场解决方案结果（是/否/数据不可用）上投注，带绑定证据开放争议，在争议确认或逆转上投注
- **门暂停/关闭/申诉**：暂停或关闭门的申请表单，含自动定位待审请愿书的可重用申诉流程
- **隐私原语跑道**：功能钥匙——匿名公民证明、5/6 部分已发货；锁定协议合约——稳定接口待集成的隐私核心 Rust crate

### 4.3 隐私声明 ⚠️

**实验测试网——无隐私保证**：InfoNet 消息已混淆但**不是端到端加密**。网格网络（Meshtastic/APRS）**不是私有的**——无线电传输按设计是公开和可截获的。隐私原语合约已搭建但尚未接入。**不要在任何频道上传输敏感信息。**

---

## 5. 时间机器快照回放 ⏱️（新功能 v0.9.7）

将实时地图视为可擦除、暂停和回放的录像：

- **实时 ↔ 快照切换**：切换到快照模式立即暂停全局轮询循环，切换回实时使 ETags 无效并强制刷新快慢层
- **每小时索引**：每个捕获快照按小时桶索引，含计数、最新 ID、最新时间戳和完整快照 ID 列表，可从时间线选择器直接跳转到任意捕获时间戳
- **帧插值**：移动实体（飞机、船只、卫星、军事航班）在回放中平滑插值
- **可变播放速度**：步进、播放、快进、倒回保存的遥测数据
- **本地存储**：快照存储在后端本地，第三方永不看到回放时间线

---

## 6. 技术架构 🏗️

```
三层架构：

╔═══════════════════════════════════════════════════════╗
║         OPERATOR UI  (Next.js + MapLibre GL)           ║
║  MapLibre GL │ NewsFeed │ Sovereign Shell │ Mesh Chat   ║
╠═══════════════════════════════════════════════════════╣
║         BACKEND SERVICE PLANE  (FastAPI + Python)       ║
║  60+ 数据源：OpenSky / ADS-B / AIS / CelesTrak / GDELT  ║
║  / KiwiSDR / CCTV / NASA FIRMS / DeepState / Meshtastic║
╠═══════════════════════════════════════════════════════╣
║         DECENTRALIZED LAYER  (InfoNet Testnet)         ║
║  Wormhole 中继 │ Sovereign Shell 治理 │ Mesh Hashchain  ║
╚═══════════════════════════════════════════════════════╝
```

**技术栈**：

- **前端**：Next.js + MapLibre GL JS（WebGL 渲染）
- **后端**：FastAPI + Python
- **数据采集**：APScheduler（快/慢两层轮询）
- **协议**：REST + WebSocket（实时 AIS）
- **多架构支持**：linux/amd64 + linux/arm64（Raspberry Pi 5 支持）
- **桌面化**：Tauri 壳 → 打包后端运行时 + Next.js 前端

---

## 7. 部署指南 🚀

### 7.1 Docker 快速部署（推荐）

```bash
git clone https://github.com/BigBodyCobain/Shadowbroker.git
cd Shadowbroker
docker compose pull
docker compose up -d
```

然后打开 `http://localhost:3000` 即可查看仪表板。

> **后端端口已被占用？** 浏览器只需端口 `3000`，但后端 API 也在主机端口 `8000` 发布用于本地诊断。如果另一个应用已使用 `8000`，在 `docker-compose.yml` 旁边创建或编辑 `.env` 并设置 `BACKEND_PORT=8001`，然后运行 `docker compose up -d`。

> **几分钟后新闻/UAP/基地/废水图层空白？** 检查后端 OOM 重启：`docker events --since 30m --filter container=shadowbroker-backend --filter event=oom`。默认 compose 文件给后端 4GB 内存。

**更新**：

```bash
docker compose pull
docker compose up -d
```

### 7.2 Kubernetes / Helm 部署

```bash
# 添加 Helm 仓库
helm repo add bjw-s-labs https://bjw-s-labs.github.io/helm-charts/
helm repo update

# 从本地 helm/chart 目录安装
helm install shadowbroker ./helm/chart --create-namespace --namespace shadowbroker
```

特点：模块化架构（前后端独立扩缩容）、受限 UID 安全上下文、兼容 Traefik + Cert-Manager + Gateway API。

### 7.3 无 Docker 快速启动

不想处理终端命令？直接下载 Releases 页面的最新 `.zip` 文件，解压后：
- **Windows**：双击 `start.bat`
- **Mac/Linux**：`chmod +x start.sh && ./start.sh`

---

## 8. 数据源总览 📊

| 来源 | 数据 | 更新频率 | API 密钥 |
|------|------|----------|----------|
| OpenSky Network | 商业/私人航班 | ~60s | **必需** |
| adsb.lol | 军事飞机 | ~60s | 否 |
| aisstream.io | AIS 船只位置 | 实时 WebSocket | **必需** |
| CelesTrak | 卫星轨道（TLE+SGP4） | ~60s | 否 |
| USGS Earthquake | 全球地震事件 | ~60s | 否 |
| GDELT Project | 全球冲突事件 | ~6h | 否 |
| DeepState Map | 乌克兰前线 | ~30min | 否 |
| Shodan | 互联网设备搜索 | 按需 | **必需** |
| Amtrak / DigiTraffic | 列车位置 | ~60s | 否 |
| Global Fishing Watch | 渔船活动 | ~10min | 否 |
| 13 个 CCTV 来源 | 11,000+ 摄像头 | ~10min | 部分必需 |
| SatNOGS / TinyGS | 卫星地面站 | ~30min | 否 |
| Meshtastic / APRS | 网格无线电位置 | 实时 | 否 |
| KiwiSDR / OpenMHZ | SDR 无线电 | 实时 | 否 |
| NASA FIRMS | 火灾热点 | ~120s | 否 |
| NASA OPERA / Copernicus EGMS | SAR 地表变化 | 按需 | **必需**（免费） |
| 史密森尼 GVP | 火山 | 静态缓存 | 否 |
| OpenAQ | 空气质量 PM2.5 | ~120s | 否 |
| NOAA / NWS | 天气警报 | ~120s | 否 |
| WRI | 全球发电厂 | 静态缓存 | 否 |
| IODA（佐治亚理工） | 互联网中断 | ~120s | 否 |
| NASA GIBS | MODIS 每日卫星影像 | 每日（24-48h 延迟） | 否 |
| Esri World Imagery | 高分辨率卫星底图 | 静态定期更新 | 否 |
| Sentinel Hub | 卫星图像处理 | 按需 | **必需**（免费） |

---

## 9. 总结

ShadowBroker 是一个功能完备的开源 OSINT 平台，通过聚合 60+ 公共数据源将原本分散的各种情报数据统一到一个交互式地图界面中。它不仅是一个可视化工具，更是一个**地理空间情报操作系统**，支持 AI 智能体协作（Sovereign Shell 治理）、时间机器回放、去中心化通信网络以及多种高级数据层（SAR、DNS 干扰检测、航母打击群追踪等）。

**核心优势**：
- 全部数据均为公开来源，无隐私争议
- 完全开源，可自托管，无遥测
- 35+ 数据层，一站式整合
- AI 智能体深度集成，HMAC 命令通道开放
- 支持 Docker、Kubernetes 多平台部署

**注意事项**：

- OpenSky 和 AIS API 密钥为推荐必备项
- InfoNet 当前为实验测试网，无隐私保证
- 后端建议 4GB+ 内存运行
- SAR 完整模式需要 NASA Earthdata 免费账号

如果你对全球实时态势感知、开源情报收集或 AI 辅助分析有兴趣，ShadowBroker 值得深入研究。

---

*如果你喜欢这篇技术解析，欢迎在 GitHub 上给 [ShadowBroker](https://github.com/BigBodyCobain/Shadowbroker) 一键三连。*