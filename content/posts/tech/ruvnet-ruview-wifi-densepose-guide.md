---
title: "RuView：WiFi 空间感知与人体感知技术完全指南"
slug: "ruvnet-ruview-wifi-densepose-guide"
date: 2026-03-31T12:55:00+08:00
categories: ["技术笔记"]
tags: ["RuView", "WiFi", "CSI", "人体感知", "穿墙感知", "生命体征", "姿态估计"]
description: "全面解析 RuView：WiFi 空间感知与人体感知系统（44.7k Stars，MIT 许可证）。通过 WiFi CSI 实现无需摄像头的姿态估计、穿墙感知、呼吸心率监测。基于 Rust + Python，支持 ESP32-S3/Raspberry Pi/60GHz 毫米波多种硬件。从入门到精通，包含架构分析、原理讲解、部署配置和开发扩展。"
---

# RuView：WiFi 空间感知与人体感知技术完全指南

## §1 学习目标

学完本文档后，你将能够：

- 理解 WiFi CSI（信道状态信息）的基础概念与工作原理
- 掌握 RuView 的系统架构与核心模块
- 了解 RuView 如何通过 WiFi 信号实现人体姿态估计、呼吸心率监测、穿墙感知
- 学会在不同硬件配置（ESP32-S3、Raspberry Pi）上部署 RuView
- 掌握 Docker 部署与本地开发环境的搭建
- 了解 RuView 的自学习系统（RuVector）的工作机制
- 学会在医疗监护、安防监控、智能家居等场景中应用 RuView
- 掌握性能调优与故障排查的方法

---

## §2 项目概述

### 2.1 什么是 RuView

RuView（官方仓库：[ruvnet/RuView](https://github.com/ruvnet/RuView)）是一个**基于 WiFi 的空间感知与人体感知系统**（WiFi DensePose）。它通过分析 WiFi 信道状态信息（CSI），实现无需摄像头的人体姿态估计、呼吸心率监测、存在检测等功能。

RuView 的核心创新：**利用无处不在的 WiFi 信号，让任何空间都具备"感知能力"**——无需穿戴设备、无需摄像头、保护隐私、穿墙可行。

### 2.2 核心数据

```
Stars:     44,700+（44.7k）
Forks:     6,000+（6k）
提交:     328+ 次
分支:     142 branches
标签:     19 tags
贡献者:   9 人
许可证:   MIT
主要语言: Rust 1.85+ (高性能 DSP), Python (ML 训练)
测试:     1,300+ 测试用例
```

### 2.3 版本与发布

| 版本 | 状态 | 发布日期 |
|------|------|---------|
| **v2.x** | 主流开发 | 2026 年 |
| **v1.x** | 遗留版本 | Python 实现 |

最新提交：`eb69444`（2026-03-30）- fix(server): correct RSSI byte offset in frame parser (#332)

### 2.4 为什么需要 RuView

**传统感知方案的局限**

| 方案 | 隐私问题 | 穿墙能力 | 成本 | 复杂环境 |
|------|---------|---------|------|---------|
| 摄像头 | ❌ 严重 | ❌ 无 | 中 | 受光照影响 |
| 可穿戴设备 | ✅ 无 | ✅ 支持 | 高 | 需随身携带 |
| 红外PIR | ✅ 无 | ❌ 微弱 | 低 | 受温度影响 |
| **RuView** | ✅ **无** | ✅ **5米** | **低** | **不受影响** |

**RuView 的独特优势**

- **隐私保护**：无需摄像头，不采集任何图像数据
- **穿墙感知**：可穿透非金属墙体，感知距离达 5 米
- **无需配合**：无需被测人员穿戴或配合设备
- **连续监测**：7×24 小时无间断监测
- **基础设施**：利用现有 WiFi AP，无需专用设备

---

## §3 原理分析

### 3.1 WiFi CSI 基础

**CSI vs RSSI**

WiFi 信号分析主要有两种方法：

| 指标 | RSSI | **CSI** |
|------|------|---------|
| 全称 | Received Signal Strength Indicator | **Channel State Information** |
| 精度 | 粗粒度（dBm） | **细粒度（子载波级别）** |
| 信息量 | 仅信号强度 | **相位 + 幅度** |
| 感知能力 | 存在检测 | **姿态估计、生命体征** |

**CSI 的物理意义**

当人体在 WiFi 信号传播路径上移动时，会引起信号的多径效应（Multipath Effect）。CSI 测量的是每个子载波的幅度和相位变化，这些变化包含了人体的位置和运动信息。

```
WiFi 发射器 → 直接路径 → WiFi 接收器
          ↘        ↗
            人体反射路径
          ↗        ↘
         次要反射路径
```

当人体移动时，反射路径长度变化，导致 CSI 信号的相位偏移和幅度变化。通过分析这些变化，可以推断人体的位置和姿态。

### 3.2 WiFi DensePose 原理

DensePose 是一个将 2D 图像中所有人体像素映射到 3D 人体表面的系统。RuView 将这一概念迁移到 WiFi 域：

**输入**：WiFi CSI 数据（复数形式，每个子载波的 I/Q 数据）

**处理流程**：

```
CSI 原始数据
      │
      ▼
┌─────────────────┐
│  信号预处理       │  滤波、去噪、标准化
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  多径分离       │  分离直接路径和人体反射路径
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  人体分割       │  定位人体所在区域
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  姿态估计       │  提取关节点位置、骨架
└────────┬────────┘
         │
         ▼
输出：人体姿态 + 生命体征
```

### 3.3 呼吸心率监测原理

人体呼吸和心跳引起胸腔的微小位移，这个位移会调制 WiFi 信号的相位：

**呼吸监测**

- 呼吸频率范围：6-30 BPM（成人平静呼吸）
- 胸腔位移：约 1-12 mm
- 对应相位变化：极微小（微弧度量级）
- 需要高信噪比的硬件和精密的信号处理算法

**心率监测**

- 心率范围：40-120 BPM（成人）
- 心脏跳动引起的胸腔位移：约 0.1-1 mm
- 需要更敏感的算法（如小波变换、谱分析）

**算法核心**

```python
# 简化版呼吸提取算法
def extract_breathing(csi_data, sample_rate=1000):
    # 1. 提取相位
    phase = np.angle(csi_data)
    
    # 2. 去除载波相位偏移（carrier phase offset, CPO）
    phase_unwrapped = np.unwrap(phase)
    
    # 3. 带通滤波（0.1-0.5 Hz 对应 6-30 BPM）
    from scipy.signal import butter, filtfilt
    b, a = butter(2, [0.1/30, 0.5/30], btype='band')
    breathing_signal = filtfilt(b, a, phase_unwrapped)
    
    # 4. FFT 计算呼吸频率
    freqs = np.fft.rfftfreq(len(breathing_signal), 1/sample_rate)
    power = np.abs(np.fft.rfft(breathing_signal))**2
    
    # 5. 找峰值频率
    peak_idx = np.argmax(power)
    breathing_rate = freqs[peak_idx] * 60  # 转换为 BPM
    return breathing_rate
```

### 3.4 自学习系统（RuVector）

RuView 内置自学习系统 RuVector，无需人工标注即可从原始 WiFi 数据中学习人体感知能力：

**核心思想**

传统方法需要大量标注数据（人体姿态的图像 + 对应的 CSI 数据），而 RuVector 通过**自监督学习**直接从 CSI 数据中提取有用的表示。

**技术方案**

```python
class RuVector:
    """
    RuView 的自学习向量记忆系统
    核心：对比学习（Contrastive Learning）+ 记忆增强
    """
    
    def __init__(self, embedding_dim=256):
        self.encoder = CSIEncoder(embedding_dim)
        self.memory = VectorMemory(capacity=10000)
        self.prototype_bank = PrototypeBank()
    
    def learn(self, csi_batch, labels=None):
        """
        从 CSI 数据中学习表示
        如果有标签（呼吸频率、心率等），使用监督学习
        如果没有标签，使用对比学习
        """
        embeddings = self.encoder(csi_batch)
        
        if labels is not None:
            # 监督学习
            loss = self.supervised_loss(embeddings, labels)
        else:
            # 对比自监督学习
            loss = self.contrastive_loss(embeddings)
        
        # 更新记忆
        self.memory.add(embeddings)
        return loss
    
    def retrieve(self, query):
        """从记忆中检索相似样本"""
        return self.memory.search(query, k=5)
```

---

## §4 架构分析

### 4.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        RuView 系统                          │
├─────────────────────────────────────────────────────────────┤
│  感知层                                                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ ESP32  │  │ ESP32   │  │  Pi 4   │  │  60GHz  │        │
│  │  CSI   │  │  mmWave │  │ CSI +   │  │  Radar  │        │
│  │ 采集器  │  │  雷达   │  │ 边缘推理 │  │  高精度  │        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
│       └──────────────┬┴──────────────┘                  │
│                      ▼                                    │
│  通信层                                                      │
│  ┌─────────────────────────────────────────────┐          │
│  │           WebSocket / MQTT / HTTP             │          │
│  └─────────────────────────────────────────────┘          │
│                      ▼                                    │
│  处理层                                                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ CSI    │  │ 姿态   │  │ 生命   │  │ 异常   │        │
│  │ 预处理  │  │ 估计   │  │ 体征   │  │ 检测   │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
│                      ▼                                    │
│  应用层                                                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ 医疗   │  │ 安防   │  │ 智能   │  │ 救灾   │        │
│  │ 监护   │  │ 监控   │  │ 家居   │  │ 现场   │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 核心模块

| 模块 | 功能 | 技术栈 |
|------|------|-------|
| **firmware** | ESP32-S3 CSI 采集固件 | C++ / FreeRTOS |
| **wifi-densepose-rs** | Rust 版核心算法（高性能 DSP） | Rust |
| **mmwave** | 60GHz mmWave 雷达处理 | Python |
| **ui** | Web 可视化界面 | React / TypeScript |
| **server** | 数据接收与分发服务 | Python / FastAPI |
| **docs** | 架构决策记录（62 ADR） | Markdown |

### 4.3 硬件配置

**方案一：ESP32-S3 传感器网格（推荐）**

成本：约 $54（3-6 个节点）

```
┌─────────────────────────────────────────────┐
│              ESP32-S3 Sensor Node           │
├─────────────────────────────────────────────┤
│  ESP32-S3-WROOM-1 (Xtensa LX7 @ 240MHz)    │
│  8MB Flash / 8MB PSRAM                      │
│  2.4GHz WiFi (802.11n)                      │
│  1x IPEX 天线接口                           │
│  5x 模拟输入 (用于扩展)                     │
└─────────────────────────────────────────────┘
```

配置示例（3 节点覆盖 30㎡）：

```yaml
# deployment/esp32/config.yaml
nodes:
  - id: node_1
    position: [0, 0, 2.5]  # x, y, z (米)
    role: transmitter
    power: 15  # dBm
    
  - id: node_2
    position: [5, 0, 2.5]
    role: receiver
    power: 15
    
  - id: node_3
    position: [2.5, 5, 2.5]
    role: receiver
    power: 15
```

**方案二：Raspberry Pi + 外置 WiFi 网卡**

```bash
# 使用支持 monitor 模式的网卡
# 推荐：AWUS036ACM (RTL8812AU)
sudo apt install bc wc gawk
./setup_p网卡.sh
```

### 4.4 目录结构

```
RuView/
├── firmware/                    # ESP32-S3 固件
│   ├── esp32-csi-tool/        # CSI 采集工具
│   ├── esp32-wifi/            # WiFi 配置
│   └── components/             # ESP-IDF 组件
├── rust-port/                  # Rust 重写版本
│   ├── wifi-densepose-rs/      # Rust DSP 核心
│   │   ├── src/
│   │   │   ├── csi.rs         # CSI 解析
│   │   │   ├── pose.rs        # 姿态估计
│   │   │   ├── vitals.rs      # 生命体征
│   │   │   └── lib.rs
│   │   └── Cargo.toml
│   └── wifi-utils-rs/          # WiFi 工具库
├── mmwave/                     # 60GHz mmWave 雷达
│   └── processing/              # 雷达信号处理
├── ui/                         # Web 界面
│   ├── src/
│   │   ├── components/         # React 组件
│   │   ├── hooks/             # 自定义 hooks
│   │   └── pages/             # 页面
│   └── Dockerfile
├── server/                     # Python FastAPI 服务
│   ├── api/
│   │   ├── v1/
│   │   │   ├── csi.py         # CSI 数据接口
│   │   │   ├── pose.py        # 姿态数据接口
│   │   │   └── vitals.py      # 体征数据接口
│   │   └── websocket.py       # 实时推送
│   ├── ml/
│   │   ├── model.py           # ML 模型推理
│   │   ├── preprocessor.py    # 数据预处理
│   │   └── postprocessor.py   # 结果后处理
│   └── main.py
├── docs/                       # 文档
│   ├── adr/                   # 架构决策记录 (62 ADR)
│   │   ├── ADR-001-why-rust.md
│   │   ├── ADR-002-csi-format.md
│   │   └── ...
│   └── architecture.md        # 系统架构文档
├── examples/                   # 示例
│   ├── medical/               # 医疗监护示例
│   │   └── sleep-monitoring/
│   └── smart-home/            # 智能家居示例
├── tests/                      # 测试
│   ├── unit/                  # 单元测试
│   ├── integration/            # 集成测试
│   └── benchmark/              # 性能测试
├── docker/                     # Docker 配置
│   ├── docker-compose.yml
│   └── Dockerfile
└── README.md
```

### 4.5 数据流

```
ESP32-S3 节点
      │ (UDP, CSI 数据包)
      ▼
WiFi AP / 直接以太网
      │
      ▼
┌─────────────────┐
│  Server (Python)  │
│  - CSI 解析      │  10.0.0.x:3000
│  - 格式转换      │
└────────┬────────┘
         │
         │ (gRPC / Protobuf)
         ▼
┌─────────────────┐
│  Rust DSP (可选) │
│  - 实时处理      │
│  - 54K fps      │
└────────┬────────┘
         │
         │ (WebSocket)
         ▼
┌─────────────────┐
│  Web UI (React) │
│  - 可视化       │
│  - 实时显示     │
└─────────────────┘
```

---

## §5 功能详解

### 5.1 人体姿态估计

RuView 通过分析 WiFi CSI 数据的相位变化，实现 2D/3D 人体姿态估计：

**支持的能力**

| 能力 | 精度 | 延迟 | 说明 |
|------|------|------|------|
| 存在检测 | >99% | <100ms | 是否有人 |
| 位置追踪 | ~30cm | <200ms | 2D/3D 坐标 |
| 骨架估计 | 13-17 关节点 | <500ms | COCO 格式 |
| 行为识别 | >90% | <1s | 站立/坐下/躺下/摔倒 |
| 呼吸追踪 | ±1 BPM | <1s | 连续监测 |

**API 使用示例**

```python
import requests

# 获取当前姿态
response = requests.get("http://localhost:8000/api/v1/pose/latest")
pose_data = response.json()

print(f"检测到 {len(pose_data['persons'])} 人")
for person in pose_data['persons']:
    print(f"  ID: {person['id']}")
    print(f"  位置: ({person['x']:.2f}, {person['y']:.2f})")
    print(f"  骨架: {person['keypoints'][:5]}...")  # 前5个关节点
```

**WebSocket 实时订阅**

```python
import asyncio
import websockets

async def subscribe_pose():
    uri = "ws://localhost:8000/ws/pose"
    async with websockets.connect(uri) as ws:
        await ws.send('{"action": "subscribe", "room": "living_room"}')
        
        async for message in ws:
            data = json.loads(message)
            if data['type'] == 'pose_update':
                print(f"姿态更新: {data['person_count']} 人")
                for person in data['persons']:
                    print(f"  {person['id']}: {person['pose']}")

asyncio.run(subscribe_pose())
```

### 5.2 生命体征监测

**呼吸监测**

```python
# 获取当前呼吸率
response = requests.get("http://localhost:8000/api/v1/vitals/breathing")
breathing_data = response.json()

print(f"呼吸率: {breathing_data['rate']:.1f} BPM")
print(f"呼吸幅度: {breathing_data['amplitude']:.2f} mm")
print(f"呼吸规律性: {breathing_data['regularity']:.1%}")
```

**心率监测**

```python
# 获取心率
response = requests.get("http://localhost:8000/api/v1/vitals/heart_rate")
hr_data = response.json()

print(f"心率: {hr_data['rate']:.1f} BPM")
print(f"心率变异性 (HRV): {hr_data['hrv']:.1f} ms")
```

**批量历史数据查询**

```python
# 查询过去 1 小时的呼吸率数据
params = {
    "metric": "breathing_rate",
    "start": "2026-03-30T00:00:00",
    "end": "2026-03-30T01:00:00",
    "resolution": "1m"  # 1分钟分辨率
}
response = requests.get("http://localhost:8000/api/v1/vitals/history", params=params)
history = response.json()

print(f"数据点: {len(history['data_points'])}")
for point in history['data_points'][:5]:
    print(f"  {point['timestamp']}: {point['value']:.1f} BPM")
```

### 5.3 穿墙感知

RuView 支持穿透非金属墙体进行感知：

**支持的场景**

| 墙体类型 | 最大穿透厚度 | 精度衰减 |
|---------|------------|---------|
| 木材/石膏板 | 30 cm | <10% |
| 玻璃 | 10 cm | <5% |
| 混凝土（钢筋较少）| 15 cm | <20% |
| 金属 | ❌ 不支持 | - |

**启用穿墙模式**

```python
# 配置穿墙感知
config = {
    "through_wall": {
        "enabled": True,
        "wall_type": "drywall",  # drywall / concrete / glass
        "thickness_cm": 15,
        "compensation": True  # 自动补偿精度衰减
    }
}
requests.post("http://localhost:8000/api/v1/config/update", json=config)
```

### 5.4 多目标追踪

RuView 支持同时追踪多个目标：

```python
# 获取所有追踪目标
response = requests.get("http://localhost:8000/api/v1/tracking/all")
tracking_data = response.json()

print(f"当前追踪 {tracking_data['active_count']} / {tracking_data['max_count']} 个目标")

for target in tracking_data['targets']:
    print(f"\n目标 {target['id']}:")
    print(f"  轨迹长度: {len(target['trajectory'])} 点")
    print(f"  当前速度: {target['velocity']:.2f} m/s")
    print(f"  在场时长: {target['dwell_time']:.1f} 秒")
```

---

## §6 使用说明

### 6.1 环境要求

**最低配置**

| 组件 | 要求 |
|------|------|
| CPU | ARM Cortex-A72 (Raspberry Pi 4) 或 x86_64 |
| 内存 | 4 GB RAM |
| 存储 | 16 GB SDD |
| WiFi | 2.4GHz 802.11n 支持 monitor 模式 |
| 网络 | 100Mbps 以太网或高速 WiFi |

**推荐配置**

| 组件 | 推荐 |
|------|------|
| CPU | x86_64 (Intel i5+) |
| 内存 | 8 GB+ RAM |
| 存储 | 256 GB+ SSD |
| GPU | NVIDIA GPU (CUDA) 用于加速推理 |

### 6.2 Docker 部署（推荐）

**快速启动**

```bash
# 克隆仓库
git clone https://github.com/ruvnet/RuView.git
cd RuView

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f server
```

**访问服务**

- Web UI: http://localhost:3000
- API 文档: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/ws

**自定义配置**

```bash
# 创建配置目录
mkdir -p config/override

# 复制默认配置
cp docker/default-config.yaml config/override/config.yaml

# 编辑配置
vim config/override/config.yaml

# 使用自定义配置启动
CONFIG_PATH=config/override docker-compose up -d
```

### 6.3 本地开发环境

**Rust 环境（用于 wifi-densepose-rs）**

```bash
# 安装 Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# 验证安装
rustc --version  # rustc 1.85.0

# 构建 Rust DSP 库
cd rust-port/wifi-densepose-rs
cargo build --release
```

**Python 环境（用于 server 和 ML）**

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

**ESP32 固件烧录**

```bash
# 安装 ESP-IDF
. $HOME/esp/esp-idf/install.sh
. $HOME/esp/esp-idf/export.sh

# 配置项目
cd firmware/esp32-csi-tool
idf.py set-target esp32s3
idf.py menuconfig

# 烧录固件
idf.py flash monitor
```

### 6.4 ESP32-S3 节点配置

**硬件连接**

```
ESP32-S3-WROOM-1
    │
    ├── 3.3V ──────── USB 5V (通过 USB-C)
    ├── GND ───────── USB GND
    ├── GPIO1 ──────── IPEX 天线 (可选, 板载天线默认启用)
    └── GPIO2 ──────── LED 指示灯 (可选)
```

**配置 WiFi AP**

```bash
# 连接 ESP32 串口
screen /dev/ttyUSB0 115200

# 配置 WiFi AP
AT+CWMODE=3        # SoftAP+Station 模式
AT+CWJAP="YourSSID","YourPassword"  # 连接 WiFi
AT+CIFSR            # 查看 IP 地址
```

### 6.5 常用命令

```bash
# 查看服务状态
curl http://localhost:8000/api/v1/health

# 获取 CSI 统计
curl http://localhost:8000/api/v1/csi/stats

# 获取设备列表
curl http://localhost:8000/api/v1/devices

# 重启服务
docker-compose restart server

# 查看实时日志
docker-compose logs -f --tail=100

# 停止所有服务
docker-compose down
```

---

## §7 开发扩展

### 7.1 自定义信号处理器

RuView 的信号处理管道支持插件式扩展：

```rust
// my_processor.rs
use wifi_densepose_rs::prelude::*;

pub struct MyProcessor {
    threshold: f32,
}

impl Processor for MyProcessor {
    fn process(&self, csi: &CSIFrame) -> Result<ProcessingOutput> {
        // 自定义处理逻辑
        let filtered = self.apply_filter(&csi.data);
        let peaks = self.detect_peaks(&filtered);
        
        Ok(ProcessingOutput {
            detections: peaks,
            metadata: ProcessingMetadata::new(),
        })
    }
}

// 注册处理器
register_processor!("my_processor", MyProcessor::new);
```

### 7.2 添加新的感知模式

在 `server/ml/` 中添加新的 ML 模型：

```python
# server/ml/models/my_model.py
from .base import BaseModel

class MyPerceptionModel(BaseModel):
    """自定义感知模型"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.model = self.load_model(config['model_path'])
    
    def infer(self, csi_data: np.ndarray) -> dict:
        # 预处理
        processed = self.preprocess(csi_data)
        
        # 推理
        raw_output = self.model.predict(processed)
        
        # 后处理
        result = self.postprocess(raw_output)
        
        return result
```

### 7.3 Web UI 扩展

在 `ui/src/components/` 中添加新组件：

```typescript
// ui/src/components/MyPanel.tsx
import React from 'react';
import { Card, Metric, Text } from '@tremor/react';

interface MyPanelProps {
  data: MyDataType;
}

export const MyPanel: React.FC<MyPanelProps> = ({ data }) => {
  return (
    <Card className="my-panel">
      <Text>自定义面板</Text>
      <Metric>{data.value}</Metric>
      <Text>更新时间: {data.timestamp}</Text>
    </Card>
  );
};

export default MyPanel;
```

### 7.4 与 Home Assistant 集成

```yaml
# Home Assistant configuration.yaml
sensor:
  - platform: rest
    name: RuView Breathing Rate
    resource: http://localhost:8000/api/v1/vitals/breathing
    value_template: "{{ value_json.rate }}"
    unit_of_measurement: "BPM"
    scan_interval: 5

automation:
  - alias: "呼吸率异常告警"
    trigger:
      platform: numeric_state
      entity_id: sensor.ruview_breathing_rate
      above: 25  # 超过 25 BPM
    action:
      service: notify.mobile_app
      data:
        message: "检测到呼吸率异常: {{ states('sensor.ruview_breathing_rate') }} BPM"
```

---

## §8 最佳实践

### 8.1 部署最佳实践

**网络配置**

- 使用千兆以太网连接服务器和 ESP32 节点
- 如果使用 WiFi，确保 AP 位置靠近传感器节点
- 避免在同一信道上部署大量 WiFi AP

**天线选择**

```yaml
# 推荐天线配置
antenna:
  type: omnidirectional  # 全向天线
  gain: 5 dBi           # 增益
  polarization: vertical  # 垂直极化
  placement:
    height: 2.0-3.0 m   # 安装高度
    orientation: vertical
    separation: 3-5 m   # 节点间距
```

**环境干扰管理**

```python
# 配置干扰抑制
config = {
    "noise_handling": {
        "enabled": True,
        "dynamic_threshold": True,
        "ignore_periods": [
            {"start": "06:00", "end": "07:00"},  # 避开干扰时段
        ]
    }
}
```

### 8.2 性能调优

**Rust DSP 加速**

```bash
# 使用 GPU 加速（需要 NVIDIA CUDA）
cargo build --release --features cuda

# 使用 SIMD 加速
RUSTFLAGS="-C target-feature=+avx2" cargo build --release
```

**并发处理**

```python
# server/config.py
processing:
  worker_threads: 4          # CPU 核心数
  max_batch_size: 32         # 批量大小
  timeout_ms: 100             # 单帧处理超时
```

### 8.3 数据管理

**历史数据保留**

```python
# 配置数据保留策略
data_retention = {
    "raw_csi": "7d",      # 原始 CSI 保留 7 天
    "processed": "30d",    # 处理后数据保留 30 天
    "alerts": "90d",       # 告警数据保留 90 天
    "vitals": "1y"        # 体征数据保留 1 年
}
```

**数据导出**

```bash
# 导出为 CSV
curl "http://localhost:8000/api/v1/vitals/history?format=csv&start=2026-03-01&end=2026-03-31" \
  -o vitals_export.csv

# 导出为 JSON
curl "http://localhost:8000/api/v1/tracking/export?format=json&start=2026-03-01" \
  -o tracking_export.json
```

### 8.4 故障排查

**CSI 数据质量检查**

```bash
# 检查 CSI 数据质量
curl "http://localhost:8000/api/v1/csi/quality_report"

# 返回示例
{
  "signal_strength": -45,  # dBm (越好 > -50)
  "snr": 25,               # 信噪比 (越好 > 20)
  "packet_loss": 0.001,     # 丢包率 (越好 < 0.01)
  "csi_valid_rate": 0.998   # CSI 有效率 (越好 > 0.99)
}
```

**常见问题**

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| 检测不到人 | 天线方向错误 | 调整天线极化方向 |
| 呼吸率不准 | 信号太弱 | 增加节点或调近距离 |
| 延迟高 | CPU 负载高 | 减少并发或升级硬件 |
| 穿墙不工作 | 金属墙体 | 换成非金属墙体位置 |

---

## §9 常见问题

### Q1：需要多少个 WiFi 节点才能正常工作？

**最低配置**：2 个节点（1 个发射 + 1 个接收），覆盖约 15-20㎡

**推荐配置**：3-4 个节点，覆盖 30-50㎡，支持更好的多目标追踪

**大型场景**：6+ 个节点，支持 100㎡+ 和多目标

### Q2：与传统摄像头监控系统相比，RuView 的精度如何？

| 指标 | RuView | 摄像头 |
|------|--------|--------|
| 位置精度 | 约 30 cm | 约 5 cm（高清）|
| 姿态精度 | 13-17 关节点 | 25 关节点（COCO）|
| 隐私 | ✅ 无图像 | ❌ 采集图像 |
| 光照影响 | 无 | 强 |
| 穿墙 | ✅ 支持 | ❌ 不支持 |

RuView 精度略低于视觉方案，但隐私保护和穿墙能力是其独特优势。

### Q3：可以同时监测多少人？

单 AP 配置下：**3-5 人**（依赖环境复杂度）

影响因素：
- 环境复杂度（家具、隔断等）
- 人员密集度
- 监测区域大小

如需监测更多人，建议增加节点数量或分区部署。

### Q4：数据如何存储和处理？是否会上传云端？

**本地处理**：所有数据在本地处理，不上传云端

**存储位置**：`/data/ruview/` 目录

**存储格式**：SQLite + Parquet（高效压缩）

**云端集成**（可选）：如需云端功能，可配置 MQTT 转发到云端服务器。

### Q5：如何校准系统？

```bash
# 启动校准模式
curl -X POST "http://localhost:8000/api/v1/calibration/start"

# 放置校准物体（人形反射板）
# 系统自动进行校准...

# 完成校准
curl -X POST "http://localhost:8000/api/v1/calibration/complete"

# 查看校准报告
curl "http://localhost:8000/api/v1/calibration/report"
```

### Q6：支持哪些硬件平台？

**已测试平台**：

- ✅ ESP32-S3（官方推荐，CSI 采集）
- ✅ Raspberry Pi 4B（边缘计算）
- ✅ x86_64 服务器（高性能部署）
- ✅ NVIDIA Jetson（GPU 加速）
- ✅ 60GHz mmWave 雷达（扩展感知）

**计划支持**：

- 🔄 ESP32-C3（低成本版本）
- 🔄 WiFi 7 (802.11be, 更强 CSI)

---

## §10 总结

RuView 代表了空间感知技术的未来方向——**利用无处不在的 WiFi 信号，让任何空间都具备"感知能力"**，同时保护隐私、穿透遮挡、无需配合。

**核心优势**

- **隐私保护**：无需摄像头，不采集图像数据
- **穿墙感知**：穿透非金属墙体，感知距离达 5 米
- **生命体征**：呼吸 6-30 BPM、心率 40-120 BPM 连续监测
- **多目标追踪**：支持 3-5 人同时追踪
- **自学习能力**：RuVector 无需人工标注即可学习
- **开源可扩展**：Rust + Python，插件式架构

**适用场景**

- 🏥 **医疗监护**：睡眠监测、老人跌倒检测、新生儿监护
- 🏠 **智能家居**：存在检测、行为识别、节能控制
- 🔒 **安防监控**：入侵检测、周界防护、隐私监控
- 🚑 **救灾现场**：废墟下生命探测、搜救辅助
- 🚗 **车载感知**：车内遗留检测、驾驶员监测

**链接资源**

- GitHub 仓库：https://github.com/ruvnet/RuView
- 官方文档：https://ruvnet.github.io/RuView/
- Docker 镜像：`ruvnet/wifi-densepose:latest`
- 架构决策记录：62 ADR 在 `docs/adr/` 目录

---

*🦞 文档版本 1.0 | 撰写日期：2026-03-31 | 基于仓库 commit eb69444 (2026-03-30)*