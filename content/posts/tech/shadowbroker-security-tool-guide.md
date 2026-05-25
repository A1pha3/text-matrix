---
title: "ShadowBroker: 开源全球 OSINT 情报平台，把天空、海洋、卫星全汇在一张地图上"
date: 2026-05-17T20:15:00+08:00
categories: ["技术笔记"]
tags: ["OSINT", "开源", "情报", "Next.js", "FastAPI", "MapLibre"]
description: "ShadowBroker 是一个聚合 60+ 情报源的开源实时 OSINT 平台，追踪航空器、船只、卫星、冲突热点、CCTV 网络、GPS 干扰区等 35+ 数据图层，全部叠加在一张 Dark-Ops 风格的可交互地图上，支持 AI Agent 协同分析和 SAR 地面变化检测。"
---

说起 OSINT 工具，大多数人的印象还停留在一个个孤立的查询网站——查航班去 FlightRadar24，查船只去 MarineTraffic，查地震去 USGS，各玩各的。

**ShadowBroker** 直接把这些全干了，而且全塞进一张地图。

这个由 GitHub 用户 `BigBodyCobain` 主导的开源项目（⭐ 6,708，Fork 1,078），聚合了 60+ 实时情报 Feed，在同一个界面上同时呈现航空器、舰船、卫星、地震、冲突热点、CCTV 直播、GPS 干扰区、SAR 地面变化……甚至还有内置的去中心化通讯协议和 AI Agent 协同通道。

换句话说，它不是一个工具，而是一张**全球实时情报作战地图**。

---

## 核心功能一览

### 🛩️ 航空追踪
ADS-B 实时航班位置（OpenSky Network ~5,000+ 架次），公务机单独分类（高净值人士飞机标注机主），军用航班专用接入点（adsb.lol 军用端）。支持飞行轨迹累积、盘旋检测（>300° 自动标记）、起落判定（高度 <100ft AGL 显示为灰色图标）。亮点：**空军一号一起飞就开始追踪**，总统/副总统机队全程高亮监控。

### 🚢  maritime追踪
25,000+ 船舶 AIS 实时流（aisstream.io WebSocket），按类型分类显示（货轮、油轮、客轮、游艇、军用舰）。特别提供 **美国航母打击群位置估算**——通过 GDELT 新闻自动抓取分析报道，映射到 50+ 地理区域坐标，盘中高亮显示，目前没有其他开源工具做这件事。

### 🛰️ 卫星轨道
CelesTrak TLE 数据 + SGP4 轨道传播，实时追踪 2,000+ 在轨卫星，按任务类型着色（军事侦察=红，SAR=青，SIGINT=白，导航=蓝，早期预警=紫，商业遥感=绿，空间站=金）。集成 SatNOGS 业余卫星地面站网络和 TinyGS LoRa 卫星群。

### 🌍 地缘政治与冲突
GDELT 驱动全球冲突事件聚合（最近 8 小时约 1,000 起），乌克兰前线 GeoJSON 实时图层，乌克兰防空警报实时推送。可自定义 RSS 情报源（最多 20 个，优先级权重 1-5）。

### 📡 软件定义无线电 & SIGINT
500+ KiwiSDR 公开 SDR 接收器地图标注，点击直接打开嵌入式 SDR 调谐器。Police/Fire 扫描仪实时窃听（OpenMHZ），GPS 干扰区网格分析（NAC-P 精度降级检测），Meshtastic Mesh 无线电和 APRS 业余无线电定位集成。

### 📷 CCTV 监控网络
6 个国家/地区 11,000+ 摄像头实时画面（伦敦、纽约、加州、西班牙、新加坡等），地图上直接点开。

### 🛰️ SAR 地面变化检测
**真正的黑科技**——合成孔径雷达成像，穿云透夜，检测全球任意地点地面变化。两种模式：
- **Mode A（Catalog）**：阿拉斯加卫星设施元数据，无需账号，显示雷达过境时间
- **Mode B（Full Anomalies）**：NASA OPERA + 哥白尼 EGMS 实时地面变化告警，需要 NASA Earthdata 免费账号

异常类型覆盖：地面形变（mm 级沉降/滑坡）、水域变化（洪水范围）、植被扰动（毁林/烧痕/弹坑）、损害评估（UNOSAT/哥白尼 EMS 验证）、相干性变化。颜色编码的 AOI 编辑器，定义关注区域后自动告警。

### 🛰️ 卫星影像叠加
- NASA GIBS（MODIS Terra）：每日真彩色，30 天时间滑块，播放动画
- Esri 高分辨率影像：亚米级，缩放到建筑细节（zoom 18+）
- 右键任意位置：最新 Sentinel-2 卫星照片（10m 分辨率，含日期/云量）+ 国家档案 + 各国元首 + Wikipedia 摘要 + 最新 10m 分辨率影像

### 5 种视觉模式
STYLE 按钮一键切换：**DEFAULT**（深色 CARTO） / **SATELLITE**（亚米级 Esri） / **FLIR**（热成像反转灰度） / **NVG**（夜视绿磷） / **CRT**（复古扫描线终端）

---

## InfoNet — 内置去中心化通讯与治理层

v0.9.7 将 InfoNet 从聊天层升级为完整的**治理经济系统**：

- **Gate Chat**：混淆传输 + Ed25519 规范签名，伪匿名身份（Gate Persona），SAS 词接触验证
- **Dead Drop**：点对点消息交换，Token /epoch 邮箱，最强当前隐私通道
- **Mesh Terminal**：内置 CLI，`send`/`dm`/市场命令/门状态查询，可拖拽，最小化到顶栏
- **Sovereign Shell 治理**：链上请愿 + 参数投票 + 升级哈希治理 + 争议市场 + 证据提交 + 门暂停/关闭/申诉
- **隐私原语路线图**：RingCT / 隐身地址 / Pedersen 承诺 / 范围证明 / DEX 匹配（智能合约接口已锁定，等待密码学方案选定后集成）

> ⚠️ **当前为实验性测试网，无隐私保证**：InfoNet 消息已混淆但未端到端加密；Mesh 网络（Meshtastic/APRS）为公开射频传输，天然可被截获；隐私原语合约已搭框架但未上线。请勿传输任何敏感信息。

---

## AI Agent 协同通道

ShadowBroker 内置了 **HMAC 签名的 AI Agent 命令通道**，支持 OpenClaw 以及任何使用该协议的 Agent（Claude、GPT、LangChain 等）。Agent 拥有对全部 35+ 数据层的读写权限，可执行：

- 地图平移/缩放/控制
- 引脚放置与操作
- SAR AOI 巡查与地面变化告警分析
- 情报层查询与交叉关联发现
- 告警推送

Agent 和操作员看到的是同一张地图，可以实时在地图上执行动作。ShadowBroker 本质上是给 AI 配备了一个**看得见的实时全球情报感知层**。

---

## 技术架构

| 组件 | 技术 |
|------|------|
| 前端 | Next.js + MapLibre GL |
| 后端 | FastAPI + Python |
| 部署 | Docker Compose / Kubernetes Helm |
| 卫星轨道 | CelesTrak TLE + SGP4 传播 |
| 隐私协议 | Ed25519 / X25519 / AESGCM / HKDF |
| 地理底图 | CARTO / Esri World Imagery / NASA GIBS |

官方推荐 Docker 部署，一行命令起动：
```bash
git clone https://github.com/bigbodycobain/Shadowbroker.git
cd Shadowbroker
docker compose pull
docker compose up -d
# 打开 http://localhost:3000
```

---

## 结语

ShadowBroker 的定位非常清晰：**把所有公开信号叠加在同一张地图上**。它不创造新的监视能力，只是把已经公开的东西聚合到一个界面里。对于安全研究员、记者、无线电操作者、情报分析人员，或者单纯对"全球实时数据长什么样"感兴趣的人来说，这是一个值得研究的项目。

GitHub：[BigBodyCobain/Shadowbroker](https://github.com/BigBodyCobain/Shadowbroker)

---

*该项目完全运行在浏览器端，对接自托管后端，不收集任何用户数据，无遥测、无分析、无账号系统。*