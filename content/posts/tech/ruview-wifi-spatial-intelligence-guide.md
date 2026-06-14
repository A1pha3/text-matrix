---
title: "WiFi 空间智能：RuView 如何用 WiFi 信号实现人体感知"
date: "2026-05-14T20:32:00+08:00"
slug: "ruview-wifi-spatial-intelligence"
aliases:
     - "/posts/tech/ruview-wifi-presence-respiration-detection/"
     - "/posts/tech/ruview-wifi-spatial-intelligence-platform/"
     - "/posts/tech/ruvnet-ruview-wifi-densepose-guide/"
description: "RuView 是一个基于 WiFi CSI（信道状态信息）的空间智能平台，无需摄像头即可实现人体存在检测、呼吸心率监测、姿态估计和穿墙感知。本文深入解析其技术原理、架构设计、安装配置与主要应用场景。"
draft: false
categories: ["技术笔记"]
tags: ["WiFi感知", "CSI", "ESP32", "Rust", "空间智能", "人体感知"]
---

# WiFi 空间智能：RuView 如何用 WiFi 信号实现人体感知

想象一个不再需要摄像头的世界——在这个世界里，你能感知房间里是否有人，能测量呼吸频率和心率，能追踪人在空间中的移动，甚至能隔墙探测生命迹象。这一切，只需要你家中已有的 WiFi 路由器。

**RuView**（[https://github.com/ruvnet/RuView](https://github.com/ruvnet/RuView)）正是这样一个项目。它将普通的 WiFi 信号转化为实时空间智能，主要能力包括：

- **存在感知**：检测人员在场、计数、追踪出入
- **生命体征**：无接触式呼吸频率与心率监测
- **活动识别**：行走、坐卧、手势、跌倒检测
- **穿墙感知**：通过 F Fresnel 区几何建模实现 5 米深度穿墙

该项目在 GitHub 上已获得约 55,000 颗星，以 Rust 语言编写，基于 [RuVector](https://github.com/ruvnet/ruvector/) 和 Cognitum Seed 构建，完全运行在边缘硬件上——不需要云端，不需要摄像头，不需要互联网连接。

## 1. 原理：WiFi 信号如何"看见"人

WiFi 感知的基础是 **CSI（Channel State Information，信道状态信息）**。当你使用 WiFi 时，数据以无线电波的形式在路由器和设备之间传输。当有人移动、甚至是呼吸时，他们的身体会散射和吸收这些无线电波，导致信号发生变化。CSI 正是对这些变化的高精度测量。

### 1.1 从 RSSI 到 CSI

传统的 WiFi 设备只使用 **RSSI（Received Signal Strength Indicator，接收信号强度指示器）**——这是一个粗粒度的信号强度值，只能告诉你"信号强还是弱"。CSI 则提供了细粒度的信息：当信号从发射器传播到接收器时，它会经过多条路径（直射、反射、散射），CSI 记录了每条路径上信号的振幅和相位变化。

现代 ESP32-S3 芯片可以采集每条 WiFi 链路上 56 个子载波的 CSI 数据。一个包含 N 个节点的 mesh 网络可以产生 N×(N-1) 条链路，每条链路 56 个子载波，加上多频段融合（3 个频道 × 56 个子载波 = 168 个虚拟子载波），系统获得了远高于单点 RSSI 的空间分辨率。

### 1.2 信号处理流程

RuView 的信号处理链路如下：

```
WiFi 路由器 → 无线电波穿过房间 → 遇到人体 → 信号散射
     ↓
ESP32 mesh（4-6 个节点）在频道 1/6/11 上通过 TDM 协议捕获 CSI
     ↓
多频段融合：3 频道 × 56 子载波 = 168 虚拟子载波/链路
     ↓
多静态融合：N×(N-1) 条链路 → 注意力加权跨视角嵌入
     ↓
相干门（Coherence Gate）：接受/拒绝测量 → 可稳定工作数天而无需调参
     ↓
信号处理：Hampel 滤波、SpotFi、Fresnel、BVP、频谱图 → 清洁特征
     ↓
AI 骨干（RuVector）：注意力机制、图算法、压缩、场模型
     ↓
Signal-Line 协议（CRV）：6 阶段 gestalt → 感知 → 拓扑 → 相干 → 搜索 → 模型
     ↓
神经网络：处理后的信号 → 17 个身体关键点 + 生命体征 + 房间模型
     ↓
输出：实时姿态、呼吸、心率、房间指纹、漂移告警
```

关键处理环节包括：

- **Hampel 滤波**：去除异常值
- **SpotFi**：消除多径干扰
- **Fresnel 建模**：几何分析穿墙能力
- **BVP（Blood Volume Pulse）提取**：从 CSI 信号中分离心率成分
- **频谱图分析**：识别呼吸频率（0.1-0.5 Hz）和心率（0.8-2.0 Hz）

### 1.3 无需摄像头的自学习系统

RuView 的训练不需要摄像头。Self-Learning 系统（ADR-024）从原始 WiFi 数据中自举学习，无需任何标注数据。MERIDIAN（ADR-027）确保模型在任何房间中都能工作，而不仅仅是在训练环境中。

## 2. 系统架构

### 2.1 硬件层级

RuView 支持多种硬件配置，从零成本到完整系统：

| 方案 | 硬件 | 成本 | 全 CSI | 能力 |
|------|------|------|--------|------|
| **ESP32 + Cognitum Seed**（推荐） | ESP32-S3 + [Cognitum Seed](https://cognitum.one) | ~$140 | 是 | 姿态、呼吸、心率、运动、存在感知 + 持久向量存储、kNN 搜索、见证链、MCP 代理 |
| **ESP32 Mesh** | 3-6 个 ESP32-S3 + WiFi 路由器 | ~$54 | 是 | 姿态、呼吸、心率、运动、存在感知 |
| **Research NIC** | Intel 5300 / Atheros AR9580 | ~$50-100 | 是 | 3×3 MIMO 完整 CSI |
| **任意 WiFi 设备** | Windows、macOS 或 Linux 笔记本 | $0 | 否 | 仅 RSSI：粗粒度存在和运动检测 |

### 2.2 软件架构

RuView 用 Rust 编写，关键组件包括：

- **wifi-densepose-ruvector**：AI 骨干，基于注意力机制的图神经网络
- **wifi-densepose-wasm-edge**：60 个边缘 WASM 模块，编译为 `wasm32-unknown-unknown`，在 ESP32-S3 上通过 WASM3 运行
- **ESP32 固件**：CSI 采集、边缘推理、无线通信

边缘模块采用 `no_std` Rust 编写，通过 12 个函数组成的 API 与主机通信，每个模块 5-30 KB，支持 OTA 上传。

### 2.3 关键设计决策

RuView 采用了几个重要的架构决策：

**无摄像头训练**：原始 DensePose From WiFi 研究来自卡内基梅隆大学，证明了可以使用 10 个传感器信号（无任何标签）训练 17 个 COCO 关键点的姿态估计模型。

**密码学见证链**：每条测量都通过 Ed25519 进行密码学见证，确保数据完整性和不可否认性。

**本地学习**：尖峰神经网络（SNN）可在 30 秒内适应新环境，学习完全在本地进行，不依赖云端。

**多频段 mesh 扫描**：跨越 6 个 WiFi 频道的动态跳频，将邻居路由器作为"免费雷达照射源"，3 倍感知带宽。

## 3. 安装与快速开始

### 3.1 Docker 体验（无需硬件）

没有任何硬件？先用 Docker 运行模拟数据评估整个信号处理流水线：

```bash
docker pull ruvnet/wifi-densepose:latest
docker run -p 3000:3000 ruvnet/wifi-densepose:latest
# 打开 http://localhost:3000
```

验证确定性参考信号（无需硬件）：

```bash
python archive/v1/data/proof/verify.py
```

### 3.2 ESP32-S3 实时感知

**第一步：烧录固件**

```bash
python -m esptool --chip esp32s3 --port COM9 --baud 460800 \
  write_flash 0x0 bootloader.bin 0x8000 partition-table.bin \
  0xf000 ota_data_initial.bin 0x20000 esp32-csi-node.bin
```

**第二步：配置网络**

```bash
python firmware/esp32-csi-node/provision.py --port COM9 \
  --ssid "YourWiFi" --password "secret" --target-ip 192.168.1.20
```

**第三步：运行感知服务器**

```bash
# 实时 RF 房间扫描
node scripts/rf-scan.js --port 5006

# SNN 实时学习
node scripts/snn-csi-processor.js --port 5006

# Mincut 正确计数人员
node scripts/mincut-person-counter.js --port 5006
```

### 3.3 完整系统（ESP32 + Cognitum Seed）

ESP32 流式传输 CSI → 网桥转发到 Seed → 持久存储 + kNN 搜索 + 见证链：

```bash
# 运行感知服务器
python -m sensing.server --port 5006

# 打开实时观测台
# https://ruvnet.github.io/RuView/
```

连接 ESP32-S3 节点后，打开 [姿态融合演示](https://ruvnet.github.io/RuView/pose-fusion.html)，可实现实时双模态姿态估计（网络摄像头 + WiFi CSI）。详细说明参见 [ADR-059](https://github.com/ruvnet/RuView/blob/main/docs/adr/ADR-059-live-esp32-csi-pipeline.md)。

## 4. 能力详解

### 4.1 呼吸与心率监测

呼吸检测使用带通滤波（0.1-0.5 Hz）加上零交叉 BPM 算法，范围 6-30 BPM。心率检测使用带通滤波（0.8-2.0 Hz），范围 40-120 BPM。

这两种检测都是完全无接触的——人不需要佩戴任何设备，也不需要面对传感器。这使得它在养老院看护、医院非危重病人监测、睡眠监测等场景中具有独特优势。

### 4.2 姿态估计

RuView 支持 17 个 COCO 关键点的姿态估计。技术规格：

- **无摄像头训练**：PCK@20 ≈ 2.5%（使用代理标签）
- **有摄像头监督训练**：目标是 35%+ PCK@20（ADR-079，数据采集和评估阶段仍在进行中）
- **M4 Pro 上的处理速度**：171K emb/s

姿态估计的工作流程：CSI 子载波振幅/相位 → 神经网络 → 17 个身体关键点。

### 4.3 存在感知

使用训练模型 + PIR 融合，准确率接近 100%，延迟仅 0.012 ms。这使得它可以作为智能建筑自动化系统的精准触发器——比传统 PIR 传感器更可靠，且不受光照条件影响。

### 4.4 穿墙感知

通过 Fresnel 区几何建模和多径建模实现，最远可达 5 米深度。这使其适用于搜救（通过废墟探测幸存者）、安防（隔墙检测入侵）和医疗（监测病房中的病人活动）。

### 4.5 边缘智能

边缘模块是直接运行在 ESP32 上的小程序——无需互联网、无云费用、即时响应。截至目前已实现 60 个模块，分布在 13 个类别中，通过 609 个测试：

| 类别 | 模块数 | 示例 |
|------|--------|------|
| 🏥 医疗健康 | 8 | 睡眠呼吸暂停、心律失常、步态分析 |
| 🔐 安防 | 8 | 入侵检测、周界入侵、逗留检测 |
| 🏢 智能建筑 | 7 | 区域占用、HVAC 控制、电梯计数 |
| 🛒 零售服务 | 7 | 队列长度、停留热力图、客流统计 |
| 🏭 工业 | 7 | 叉车接近、密闭空间、结构振动 |
| 🔮 特殊研究 | 6 | 睡眠分期、情绪检测、手语 |
| 📡 信号智能 | 6 | 闪光注意力、相干门、时间压缩 |
| 🧠 自适应学习 | 4 | DTW 手势学习、异常吸引子、EWC 终身学习 |
| 🗺️ 空间推理 | 5 | PageRank 影响力、微型 HNSW |
| ⏱️ 时序分析 | 3 | 日常规律、异常检测、规则验证 |
| 🛡️ AI 安全 | 3 | 信号重放攻击检测、WiFi 干扰 |
| ⚛️ 量子启发 | 3 | 相干性映射、最优传感器配置 |
| 🤖 自主与特殊 | 4 | 自愈 mesh、自主规划 |

## 5. 技术限制与已知问题

项目文档明确列出了以下限制：

- **ESP32-C3 和原始 ESP32 不支持**：因为它们是单核，不足以完成 CSI DSP 处理
- **单节点部署空间分辨率有限**：建议使用 2+ 个节点，或添加 Cognitum Seed 以获得最佳效果
- **无摄像头姿态精度有限**：PCK@20 ≈ 2.5%（代理标签），有摄像头监督训练的目标是 35%+ PCK@20，但评估阶段（ADR-079 P7-P9）仍在进行中，尚未发布实际测量结果

## 6. 应用场景

### 6.1 医疗健康

- **养老院/辅助生活**：跌倒检测、睡眠时呼吸监测，无需可穿戴设备合规问题
- **医院非危重病人监测**：床位持续呼吸和心率监测，无需有线传感器；异常时护士告警
- **急救室分诊**：自动计数和等待时间估计；检测等待区病人的异常呼吸（痛苦指标）

### 6.2 智能建筑

- **办公空间利用率**：哪些办公桌/房间实际被占用；会议室未使用检测；基于真实存在感的 HVAC 优化
- **酒店**：无需门传感器即可知道房间占用情况；迷你吧/浴室使用模式；空房节能
- **会议室**：无人使用时自动关闭灯光和空调

### 6.3 零售与公共场所

- **零售客流与流动**：实时人流、区域停留时间、队列长度——无摄像头、无 opt-in、GDPR 友好
- **餐厅翻台率追踪**：无需餐厅区域摄像头即可追踪餐桌周转、厨房人员、洗手间占用
- **公共厕所占用**：在摄像头不可能部署的环境中实现实时占用检测

### 6.4 极端场景

- **搜救**：通过废墟检测呼吸签名；START 分诊颜色分类；3D 定位（WiFi-Mat 灾难模块，ADR-001）
- **消防**：进入前通过烟雾和墙壁定位 occupants；呼吸检测远程确认生命迹象
- **穿墙安防**：检测墙体后方人员；清理房间确认；人质生命体征远程监测

## 7. 为什么选择 RuView

### 7.1 对比传统方案

| | WiFi 感知优势 | 传统替代方案 |
|---|-------------|-------------|
| 🔒 | **无视频、无 GDPR/HIPAA 成像规定** | 摄像头需要同意、标识、数据保留政策 |
| 🧱 | **可穿墙、穿过货架和杂物** | 摄像头需要每个房间的视线 |
| 🌙 | **可在完全黑暗中工作** | 摄像头需要红外或可见光 |
| 💰 | **$0-$8/区域**（现有 WiFi 或 ESP32） | 摄像头系统：$200-$2,000/区域 |
| 🔌 | **WiFi 已无处不在部署** | PIR/雷达传感器需要每个房间新布线 |

### 7.2 技术优势

- **完全本地运行**：数据不上云，适合隐私敏感场景
- **边缘智能**：60 个 WASM 模块，支持本地决策，响应时间 <10 ms
- **自适应学习**：无需标签，在 30 秒内适应新环境
- **开源**：MIT 许可证，代码完全开放可审查

## 8. 总结

RuView 体现了一种不同的空间感知思路：利用无处不在的 WiFi 信号，通过 CSI 分析和机器学习，实现原本需要摄像头或专用传感器才能完成的功能。在隐私敏感场景、穿墙感知、黑暗环境等传统方案受限的领域，它有独特优势。

随着 ESP32-S3 等低成本硬件普及，部署 WiFi 感知系统的门槛已大幅降低。从养老院看护到智能建筑，从零售分析到搜救场景，WiFi 空间智能正在打开新的可能性。

对 WiFi 感知技术感兴趣的话，建议从 Docker 模拟环境开始体验，再逐步引入 ESP32 硬件构建自己的感知系统。项目文档中的 ADR（Architecture Decision Records）详细记录了每个设计决策的背景和考量，是深入理解系统设计的好资源。

> 项目地址：[https://github.com/ruvnet/RuView](https://github.com/ruvnet/RuView)  
> 官方演示：[https://ruvnet.github.io/RuView/](https://ruvnet.github.io/RuView/)  
> Cognitum Seed：[https://cognitum.one](https://cognitum.one)