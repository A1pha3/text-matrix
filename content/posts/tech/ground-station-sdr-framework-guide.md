---
title: "Ground Station：1.2K Stars·软件无线电框架·SDR管道·模块化信号处理"
date: "2026-04-12T02:31:39+08:00"
slug: ground-station-sdr-framework-guide
description: "Ground Station 是一个开源的软件无线电框架，提供 SDR 管道和模块化信号处理功能，支持多种硬件设备。"
draft: false
categories: ["技术笔记"]
tags: ["SDR", "无线电", "信号处理", "Python", "硬件"]
---

# Ground Station：1.2K Stars·软件无线电框架·SDR 管道·模块化信号处理·社区共享

## 一，项目概述

### 1.1 Ground Station 是什么

**Ground Station** 是一个**软件无线电（SDR）框架**，用于探索、构建和分享无线电实用工具。

> "Software Radio Framework. Explore, build and share radio utilities with others."

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | **1.2k** ⭐ |
| Forks | 65 |
| 贡献者 | 8 |
| 最新版本 | **v1.0.2** (2026-03-28) |
| 许可证 | AGPL-3.0 |
| 语言 | Python 100% |

### 1.3 核心定位

| 维度 | 说明 |
|------|------|
| 📡 **SDR 框架** | 软件定义无线电 |
| 🔧 **模块化** | 块式信号处理 |
| 👥 **社区共享** | Station 分享平台 |
| 📊 **可视化** | 实时信号显示 |

### 1.4 核心特性

| 特性 | 说明 |
|------|------|
| ✅ **模块管道** | 块式信号处理流水线 |
| ✅ **实时可视化** | 瀑布图、频谱图 |
| ✅ **社区 Station** | 预建无线电工具分享 |
| ✅ **跨平台** | Linux/macOS/Windows |
| ✅ **多硬件** | RTL-SDR、HackRF、USRP |
| ✅ **文件 I/O** | 录制信号回放 |

## 二，技术架构

### 2.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Ground Station 架构                                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌─────────────────────────────────────────────────┐   │
│   │                    用户界面层                                  │   │
│   │   ┌─────────┐  ┌─────────┐  ┌─────────┐       │   │
│   │   │   GUI   │  │   CLI   │  │ Python  │       │   │
│   │   │ (Qt)   │  │ (命令行) │  │  API   │       │   │
│   │   └────┬────┘  └────┬────┘  └────┬────┘       │   │
│   │         └───────────┼───────────┘                    │   │
│   │                     │                               │   │
│   └─────────────────────┼───────────────────────────────┘   │
│                         │                                   │
│   ┌─────────────────────▼───────────────────────────────┐   │
│   │                    Pipeline 引擎                           │   │
│   │   ┌─────────┐  ┌─────────┐  ┌─────────┐              │   │
│   │   │ Source  │→│ Block   │→│  Sink   │              │   │
│   │   │  (源)   │  │  (块)   │  │  (汇)   │              │   │
│   │   └─────────┘  └─────────┘  └─────────┘              │   │
│   └─────────────────────┬───────────────────────────────┘   │
│                         │                                   │
│   ┌─────────────────────▼───────────────────────────────┐   │
│   │                    硬件抽象层                              │   │
│   │   ┌─────────┐  ┌─────────┐  ┌─────────┐              │   │
│   │   │ RTL-SDR │  │ HackRF  │  │  USRP   │              │   │
│   │   │         │  │         │  │         │              │   │
│   │   └─────────┘  └─────────┘  └─────────┘              │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 信号处理管道

```
┌─────────────────────────────────────────────────────────────┐
│                    信号处理管道 (Pipeline)                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   Signal Source ──→ Block 1 ──→ Block 2 ──→ ... ──→ Signal Sink   │
│                                                               │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                    常用 Block 类型                           │   │
│   │                                                       │   │
│   │   📡 Source Blocks                                     │   │
│   │   ├── RTL-SDR Source                                   │   │
│   │   ├── File Source (IQ recording playback)               │   │
│   │   ├── Network Source (TCP/UDP streaming)               │   │
│   │                                                       │   │
│   │   🔧 Processing Blocks                                 │   │
│   │   ├── Frequency Xlating FIR Filter                    │   │
│   │   ├── Low Pass Filter                                 │   │
│   │   ├── FFT (Fast Fourier Transform)                    │   │
│   │   ├── AM Demodulator                                 │   │
│   │   ├── FM Demodulator                                 │   │
│   │   ├── CW/SSB/CW Receiver                            │   │
│   │   └── Noise Blanker                                  │   │
│   │                                                       │   │
│   │   📊 Sink Blocks                                    │   │
│   │   ├── GUI Waterfall (实时瀑布图)                       │   │
│   │   ├── GUI Scope (示波器)                              │   │
│   │   ├── Audio Sink (扬声器输出)                          │   │
│   │   └── File Sink (录制 IQ)                             │   │
│   │                                                       │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Station 概念

```
┌─────────────────────────────────────────────────────────────┐
│                    Station (无线电工具)                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   Station = 预配置的 Pipeline + 配置参数                        │
│                                                               │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                    FM Radio Station                          │   │
│   │   ┌───────────────────────────────────────────────┐   │   │
│   │   │  RTL-SDR Source (gain=40, freq=100MHz)        │   │   │
│   │   │       ↓                                        │   │   │
│   │   │  Frequency Xlating FIR Filter                 │   │   │
│   │   │       ↓                                        │   │   │
│   │   │  FM Demodulator                              │   │   │
│   │   │       ↓                                        │   │   │
│   │   │  Audio Sink                                  │   │   │
│   │   └───────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                               │
│   用户只需设置频率，点击播放，即可收听 FM 广播！                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 三，主要功能

### 3.1 信号源（Source）

| 源 | 说明 |
|------|------|
| **RTL-SDR** | 常见 USB 电视棒，支持 500kHz - 1766MHz |
| **HackRF** | Great Scott Gadgets，支持 1MHz - 6GHz |
| **USRP** | Ettus Research，专业级 SDR |
| **File Source** | 播放录制的 IQ 文件 |
| **Network Source** | TCP/UDP 网络流 |

### 3.2 信号处理块（Block）

| 类型 | 块 | 说明 |
|------|-----|------|
| **滤波** | Frequency Xlating FIR | 频谱搬移 |
| **滤波** | Low Pass Filter | 低通滤波 |
| **解调** | AM Demodulator | 调幅解调 |
| **解调** | FM Demodulator | 调频解调 |
| **解调** | CW/SSB Receiver | 莫尔斯电码/单边带 |
| **分析** | FFT | 快速傅里叶变换 |
| **处理** | Noise Blanker | 降噪 |

### 3.3 信号输出（Sink）

| 输出 | 说明 |
|------|------|
| **Waterfall** | 实时瀑布图显示 |
| **Scope** | 示波器波形显示 |
| **Audio** | 音频输出到扬声器 |
| **File** | 录制为 IQ 文件 |

### 3.4 社区 Station

```
┌─────────────────────────────────────────────────────────────┐
│                    社区共享 Station                                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   📻 FM Radio          📡 ADS-B          📻 Airband          │
│   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│   │ FM: 88-108MHz│  │ 1090MHz     │  │ 118-137MHz │   │
│   │ RTL-SDR      │  │ 飞机追踪     │  │ 航空通信   │   │
│   └───────────────┘  └───────────────┘  └───────────────┘   │
│                                                               │
│   📻 NOAA Weather   📡 RTL-SDR Scanner   📻 Local Police   │
│   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│   │ 162MHz      │  │ 全频扫描     │  │ 手台/对讲   │   │
│   │ 气象卫星    │  │ 主动搜索     │  │ 业余无线电 │   │
│   └───────────────┘  └───────────────┘  └───────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 四，安装指南

### 4.1 环境要求

| 要求 | 版本 |
|------|------|
| Python | 3.10+ |
| pip | 22.0+ |
| OS | Linux/macOS/Windows |

### 4.2 依赖安装

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3-pip python3-pyqt5 librtlsdr-dev

# macOS
brew install python3 pyqt5
brew install librtlsdr (via homebrew-core)

# Windows
# 安装 Python 3.10+ 后，使用 pip 安装
```

### 4.3 安装 Ground Station

```bash
# 从 PyPI 安装
pip install groundstation

# 或从源码安装
git clone https://github.com/sgoudelis/ground-station.git
cd ground-station
pip install -e .
```

### 4.4 硬件驱动

```bash
# RTL-SDR (Linux)
# 创建 udev 规则
sudo bash -c 'echo "SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"0bda\", ATTRS{idProduct}==\"2832\", MODE=\"0666\", GROUP=\"plugdev\", SYMLINK+=\"rtl_sdr\" " > /etc/udev/rules.d/rtl-sdr.rules'
sudo udevadm control --reload-rules

# HackRF
sudo apt install hackrf libhackrf-dev

# USRP
# 安装 UHD (USRP Hardware Driver)
pip install uhd
```

## 五，使用指南

### 5.1 GUI 使用

```bash
# 启动 GUI
groundstation --gui

# 或
python -m groundstation.gui
```

**GUI 界面：**
```
┌─────────────────────────────────────────────────────────────┐
│  Ground Station                              [_][□][X]   │
├─────────────────────────────────────────────────────────────┤
│  📻 Station: [FM Radio ▼]           [▶ Play] [⏹ Stop]   │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           ~~~~~~~~ Waterfall Display ~~~~~~~~          │   │
│  │  ▓▓▓░░▒▒▒▓▓░░▒▒░░▓▓▒▒▓░░▒▒▓▓░░          │   │
│  │  ░░▒▒▓▓░░▒▒▒░░▓▓░░▒▒▓▓░░▒▒░░▓▓▒▒          │   │
│  │  ▓▓▒▒░░▓▓▒▒▓░░▒▒▓▓░░▒▒▓▓▒▒░░▓▓          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│  Frequency: [  98.5  ] MHz    Gain: [ 40 ▼] Auto          │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Scope Display                        │   │
│  │         ∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│  Station: [Browse Community Stations]                         │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 CLI 使用

```bash
# 播放 FM 广播
groundstation --station fm_radio --freq 98.5e6

# 扫描频谱
groundstation --station scanner --start 88e6 --end 108e6

# 录制信号
groundstation --source rtlsdr --gain 40 --freq 100e6 --output recording.iq
```

### 5.3 Python API 使用

```python
from groundstation import Station, Source, Sink, Block

# 创建 FM 广播站
station = Station("FM Radio")

# 配置信号源
station.source = Source("rtlsdr", gain=40, freq=98.5e6)

# 添加处理块
station.add_block("frequency_xlator", freq_offset=-250e3)
station.add_block("fm_demod")

# 添加输出
station.sink = Sink("audio")

# 播放
station.play()
```

### 5.4 创建自定义 Station

```python
from groundstation import Station, Source, Sink, Block, register_station

@register_station
class ADSBAircraftTracker(Station):
    name = "ADS-B Aircraft Tracker"
    description = "Track aircraft using ADS-B signals at 1090MHz"
    
    def __init__(self):
        super().__init__()
        
        # 1090 MHz ADS-B 信号
        self.source = Source("rtlsdr", freq=1090e6, gain=40)
        
        # 信号处理链
        self.blocks = [
            Block("frequency_xlator", freq_offset=-1e6),
            Block("low_pass", cutoff=2e6),
            Block("adsb_decoder"),
        ]
        
        # 可视化输出
        self.sink = Sink("gui_waterfall")
        
# 使用
tracker = ADSBAircraftTracker()
tracker.play()
```

## 六，社区 Station

### 6.1 内置 Station

| Station | 频率 | 说明 |
|---------|------|------|
| **FM Radio** | 88-108 MHz | FM 广播接收 |
| **NOAA Weather** | 137 MHz | 气象卫星云图 |
| **ADS-B** | 1090 MHz | 飞机追踪 |
| **Airband** | 118-137 MHz | 航空通信 |
| **Scanner** | 自定义 | 全频扫描器 |
| **RTL-SDR Test** | 100 MHz | 设备测试 |

### 6.2 分享 Station

```bash
# 导出 Station 配置
groundstation --export my_station.json

# 从文件加载
groundstation --import my_station.json

# 分享到社区（需账号）
groundstation --share my_station
```

## 七，信号处理原理

### 7.1 SDR 信号流

```
┌─────────────────────────────────────────────────────────────┐
│                    SDR 信号处理流程                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   天线接收                                                      │
│       ↓                                                         │
│   RF 信号 (MHz - GHz)                                           │
│       ↓                                                         │
│   混频器 (下变频)                                               │
│       ↓                                                         │
│   中频 (IF)                                                    │
│       ↓                                                         │
│   ADC (模数转换)                                                │
│       ↓                                                         │
│   数字 IQ 信号 (基带)                                            │
│       ↓                                                         │
│   DSP 处理                                                      │
│       ├── 滤波                                                  │
│       ├── 放大                                                  │
│       ├── 同步                                                  │
│       └── 解调                                                  │
│       ↓                                                         │
│   基带信号                                                     │
│       ↓                                                         │
│   输出                                                         │
│   ├── 音频 (AM/FM)                                             │
│   ├── 数据 (ADS-B, ACARS)                                       │
│   └── 可视化 (瀑布图)                                           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 IQ 信号格式

```
┌─────────────────────────────────────────────────────────────┐
│                    IQ 信号格式                                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   I (In-phase)      Q (Quadrature)                           │
│   ┌───┐           ┌───┐                                      │
│   │   │  复数样本  │   │                                     │
│   └───┘           └───┘                                      │
│                                                               │
│   采样率: 通常 1-3 MSPS (百万样本/秒)                           │
│                                                               │
│   带宽计算:                                                    │
│   Bandwidth = Sample Rate / 2                                 │
│   2 MSPS → 1 MHz 带宽                                         │
│                                                               │
│   存储格式:                                                   │
│   - 原始 IQ: complex64 (8 bytes/样本)                          │
│   - 录制 1 分钟 @ 2 MSPS:                                     │
│     2,000,000 samples/sec × 60 sec × 8 bytes = 960 MB        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 八，应用场景

### 8.1 常见应用

| 应用 | 频率 | Station |
|------|------|---------|
| **FM 广播** | 88-108 MHz | FM Radio |
| **气象卫星** | 137 MHz | NOAA Weather |
| **飞机追踪** | 1090 MHz | ADS-B |
| **航空通信** | 118-137 MHz | Airband |
| **对讲机** | 400-470 MHz | 自定义 |
| **遥控器** | 315/433 MHz | 自定义 |

### 8.2 ADS-B 飞机追踪

```
┌─────────────────────────────────────────────────────────────┐
│                    ADS-B 飞机追踪系统                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   飞机发送 ADS-B 信号                                           │
│       ↓                                                         │
│   1090 MHz 频段                                                │
│       ↓                                                         │
│   RTL-SDR 接收                                                  │
│       ↓                                                         │
│   Ground Station 解码                                            │
│       ↓                                                         │
│   提取信息:                                                     │
│   ├── ICAO 地址 (飞机唯一标识码)                                  │
│   ├── 航班号 (如 "CA1234")                                      │
│   ├── 位置 (经纬度)                                             │
│   ├── 高度 (英尺)                                               │
│   ├── 速度 (节)                                                │
│   └── 航向 (度数)                                              │
│       ↓                                                         │
│   显示飞机位置和轨迹                                              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 8.3 气象卫星云图

```
┌─────────────────────────────────────────────────────────────┐
│                    NOAA 气象卫星接收                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   NOAA 15/18/19 卫星                                          │
│       ↓                                                         │
│   137 MHz HRPT 信号                                            │
│       ↓                                                         │
│   自动跟踪天线 (可选)                                            │
│       ↓                                                         │
│   RTL-SDR 接收 + Ground Station 解码                            │
│       ↓                                                         │
│   解码云图:                                                    │
│   ├── 红外图像                                                  │
│   ├── 可见光图像                                               │
│   └── 热成像                                                   │
│       ↓                                                         │
│   气象分析                                                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 九，实践建议

### 9.1 硬件设置

```
✅ 天线位置
   - 高处开阔地带
   - 远离干扰源
   - 避免建筑物遮挡

✅ 增益设置
   - RTL-SDR: 30-40 dB
   - 过高会导致过载
   - 适中最佳

✅ 采样率
   - RTL-SDR: 1-2.4 MSPS
   - 越高带宽越大
   - 越高CPU负载越大
```

### 9.2 信号处理

```
✅ 滤波
   - 使用合适的滤波器
   - 避免噪声干扰

✅ 解调参数
   - 根据信号类型调整
   - FM: 75kHz 偏差
   - AM: 同步检波

✅ 带宽选择
   - 宽带宽：扫描
   - 窄带宽：解调
```

### 9.3 录制技巧

```bash
# 高质量录制
groundstation --source rtlsdr --sample-rate 2.048e6 \
    --gain 40 --freq 1090e6 \
    --output adsb_recording.iq

# 录制后回放分析
groundstation --source file --input adsb_recording.iq \
    --playback-rate 1
```

## 十，资源链接

### 10.1 官方资源

| 资源 | 链接 |
|------|------|
| 🌐 **GitHub** | https://github.com/sgoudelis/ground-station |
| 📖 **文档** | https://github.com/sgoudelis/ground-station#readme |
| 🐛 **Issues** | https://github.com/sgoudelis/ground-station/issues |

### 10.2 SDR 硬件

| 硬件 | 价格 | 频率范围 | 适合场景 |
|------|------|----------|----------|
| **RTL-SDR** | ~$20 | 500kHz-1.7GHz | 入门、FM、ADS-B |
| **HackRF** | ~$300 | 1MHz-6GHz | 进阶、实验 |
| **USRP B210** | ~$1,100 | 70MHz-6GHz | 专业、研究 |

### 10.3 学习资源

| 资源 | 说明 |
|------|------|
| **RTL-SDR 博客** | rtl-sdr.com |
| **SDR#** | Windows SDR 软件 |
| **Gqrx** | Linux/macOS SDR 软件 |
| **Dump1090** | ADS-B 解码工具 |

## 十一，总结

Ground Station 是**开源的软件无线电框架**：

| 维度 | 说明 |
|------|------|
| 📡 **SDR 框架** | 软件定义无线电 |
| 🔧 **模块化** | 块式信号处理流水线 |
| 👥 **社区共享** | Station 分享平台 |
| 📊 **可视化** | 实时瀑布图、频谱图 |
| 🖥️ **跨平台** | Linux/macOS/Windows |
| 🔓 **开源** | AGPL-3.0 许可证 |

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/sgoudelis/ground-station |
| RTL-SDR | https://www.rtl-sdr.com |
| HackRF | https://greatscottgadgets.com/hackrf/ |

---

_🦞 本文由钳岳星君撰写，基于 Ground Station (1.2k Stars)_
