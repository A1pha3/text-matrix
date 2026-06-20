+++
date = '2026-06-09T21:07:02+08:00'
draft = false
title = 'espectre 深度拆解：10 欧元的 ESP32 + Wi-Fi CSI + ESPHome，做穿墙隐私动检的 Home Assistant 完整方案'
slug = 'espectre-wifi-csi-motion-detection-esp32'
description = 'espectre（francescopace/espectre）把一台 10 欧元的 ESP32 变成“穿墙动检传感器”：采集 Wi-Fi 子载波 CSI → Gain Lock + NBVI 子载波选择 + 移动方差分段（MVS）/神经网络（ML）→ 直接对接 Home Assistant；8,019 stars、ESPHome 原生组件、F1 >99%，是隐私敏感智能家居的最强开源动检方案。'
categories = ['技术笔记']
tags = ['espectre', 'ESP32', 'Wi-Fi CSI', 'ESPHome', 'Home Assistant', '动检', '智能家居', '隐私', 'signal-processing', '开源']
+++

# espectre 深度拆解：10 欧元的 ESP32 + Wi-Fi CSI + ESPHome，做穿墙隐私动检的 Home Assistant 完整方案

> **目标读者**：智能家居玩家、Home Assistant 玩家、做 IoT / 信号处理 / 边缘 AI 的工程师、关注家庭隐私的极客
> **要解决的问题**：能不能用一个 10 欧元的 ESP32、**完全不需要摄像头和麦克风**、**完全本地推理**、**直接对接 Home Assistant** 地检测房间里有没有人在动？穿墙、零云端、零训练数据采集。
> **难度**：⭐⭐⭐（中级；要懂 YAML + 一点信号处理 + Home Assistant 基础）
> **预计阅读时间**：25 分钟

| → | [espectre 是什么](#一espectre-是什么) | [定位判断](#二定位判断) | [系统地图](#三系统地图仓库结构总览) | [5 阶段管道](#四边界拆分csi-数据流与-5-阶段处理管道) | [Gain Lock](#五关键机制-1gain-lock把不可控的硬件增益锁死) | [NBVI](#六关键机制-2nbvi-自动子载波选择零配置的-f1-96) | [MVS / ML](#七关键机制-3mvs-与-ml-两种检测算法) | [HA 集成](#八关键机制-4与-home-assistant-的原生集成) | [部署案例](#九任务流案例10-分钟从拆包到-ha-上线) | [隐私](#十隐私与伦理作者写得很克制) | [采用建议](#十一采用顺序与决策建议) | [进阶路径](#十二进阶路径) |

## 学习目标

读完这篇文章，你应该能够：

1. 说清楚 Wi-Fi CSI 动检和 PIR / 毫米波雷达 / 摄像头方案在物理原理、隐私模型、可识别信息上的差异
2. 解释 Gain Lock 为什么必须先锁定 AGC 和 FFT scaling，以及老款 ESP32 没有 `phy_force_rx_gain` 时为什么改用 CV 归一化
3. 描述 NBVI 自动子载波选择的 4 步流程，并说明为什么 MVS 模式启动后 10 秒必须保持房间静止
4. 在 Home Assistant 里通过 ESPHome Native API 接入 espectre，并写出基于 `binary_sensor.motion` 的自动化 YAML
5. 判断自己的场景是否适合 espectre，包括人数统计、跌倒检测、超大面积、硬实时等不适合场景的边界

---

## 一、espectre 是什么

`espectre`（GitHub：[francescopace/espectre](https://github.com/francescopace/espectre)，官网 [espectre.dev](https://espectre.dev)）是 Francesco Pace 在 2025-10 末发布的**Wi-Fi CSI 动检系统**，GPL-3.0。它把一台 ~10 欧元的 ESP32 开发板（推荐 S3 / C6 / C3 / C5）变成一个**穿墙、无摄像头、无麦克风、无可穿戴设备**的人体动检传感器，原生集成 Home Assistant。

截至 2026-06-09 的仓库状态：

| 指标 | 数值 |
|---|---|
| 仓库 | [francescopace/espectre](https://github.com/francescopace/espectre) |
| Stars | 8,019 |
| Forks | 626 |
| 主语言 | Python（micro-espectre 训练 / 验证） + C++（ESPHome 组件） |
| 许可证 | GPL-3.0 |
| 创建时间 | 2025-10-26 |
| 最近推送 | 2026-06-08（持续活跃） |
| 最新 Release | v2.8.0（2026-05-21 验证） |
| 硬件成本 | ~10 欧元（ESP32-S3 / C6 DevKit） |
| 检测算法 | MVS（移动方差分段，默认）/ ML（神经网络，实验性） |
| Home Assistant 集成 | ESPHome Native API（自动发现） |
| 性能（自报） | MVS F1 ≥ 96%，ML F1 ≥ 99%（多芯片验证） |

> 数据来源：GitHub 仓库页面、PERFORMANCE.md 与 ALGORITHMS.md（截至 2026-06-09）。

它在 README 里用三句话概括自己的卖点：

> 1. **做什么**：用 Wi-Fi 检测运动（无摄像头、无麦克风）
> 2. **需要什么**：一台约 10 欧元的 ESP32 设备（推荐 S3 和 C6，也支持其他型号）
> 3. **配置时间**：10-15 分钟

工作原理的类比（README 原文）：

> 当房间里有人移动时，他们会"扰动"在路由器和传感器之间传播的 Wi-Fi 波。就像你把手放在手电筒前晃动，能看到影子变化一样。

---

## 二、定位判断

在展开技术细节之前，先给出对 espectre 的判断：

1. **它是一条完整的 CSI 动检栈，而不是单点传感器**。从 CSI 原始 I/Q 数据采集、增益锁定、子载波选择、移动方差分段 / 神经网络判别，到 ESPHome 原生组件、Home Assistant 自动发现——信号处理 + 边缘 AI + 智能家居集成在同一个仓库里完成，中间没有断层。市面上多数 Wi-Fi 动检项目只覆盖其中一两层（要么只采集 CSI，要么只做算法，要么只做 HA 集成）。
2. **它的工程文档密度是判断成熟度的硬指标**。`micro-espectre/ALGORITHMS.md` 741 行、`PERFORMANCE.md` 207 行，作者把每一步算法都配了公式、参数表和实测数据。这个篇幅在开源 IoT 动检项目里属于偏上水平，可以据此判断它不是 demo 级玩具。
3. **CSI 数据本身不含可识别信息，这是隐私模型的物理基础**。无摄像头、无麦克风、无云端、无路由器配置。CSI 只反映无线电信道的物理特征（子载波幅度 / 相位的统计变化），不含语音、图像、人脸。摄像头方案采集的是可识别生物特征，毫米波雷达方案采集的是微多普勒谱（可推算呼吸 / 心率），CSI 采集的是信道统计——三者采集对象不同，隐私暴露面也不同。
4. **它有明确边界**。只输出 IDLE / MOTION 二元状态，不识别人数、身份、姿态、动作类型。如果你要做"老人跌倒检测"，它只能告诉你"有 / 无活动"，不能区分"正常坐下"和"摔倒"。
5. **它的成本结构对家庭场景友好**。10 欧元硬件 + ESPHome YAML 配置 + Home Assistant 自动发现，没有付费墙、没有云端订阅。同等条件下，毫米波雷达模组（如 RD-03D）约 15-30 欧元，带摄像头的本地 ReID 方案约 50-100 欧元，PIR 方案约 5 欧元但精度低且不能穿墙。

---

## 三、系统地图：仓库结构总览

`espectre` 是一个**“双平台”** 仓库——C++ 跑在 ESP32 端做推理，Python 跑在 PC / Mac 端做模型训练与验证。

```
espectre/
├── components/             # ESPHome 组件（C++，烧进 ESP32）
│   └── espectre/           # 主组件源码
├── micro-espectre/         # Python 训练 / 验证 / 离线分析
│   ├── ALGORITHMS.md       # 741 行算法详解
│   ├── src/
│   │   ├── csi_streamer.py
│   │   ├── nbvi_calibrator.py
│   │   ├── mvs_detector.py # 移动方差分段
│   │   ├── ml_detector.py  # 神经网络检测
│   │   ├── ml_weights.py
│   │   ├── filters.py      # Hampel / Low-pass
│   │   ├── segmentation.py
│   │   ├── threshold.py
│   │   ├── features.py
│   │   ├── config.py
│   │   ├── detector_interface.py
│   │   └── runtime_policy.py
│   ├── models/             # 训练好的 ML 模型权重
│   ├── data/               # CSI 训练数据 + dataset_info.json
│   ├── notebooks/          # Jupyter 实验
│   ├── tests/              # pytest
│   ├── examples/           # espectre-monitor.html / espectre-theremin.html
│   └── tools/              # 数据采集脚本
├── docs/                   # 文档（架构、对比、安全）
├── examples/               # ESPHome YAML 示例
├── test/                   # PlatformIO 单元测试
├── PERFORMANCE.md          # 207 行实测性能
├── SETUP.md                # 装配置指南
├── TUNING.md               # 调参指南
├── ALGORITHMS.md           # 指向 micro-espectre 详细算法
├── SECURITY.md
├── ROADMAP.md
└── CHANGELOG.md
```

### 双平台策略

仓库明确采用 **two-platform strategy**（README 与 ROADMAP.md 都有强调）：

- **生产端**：`components/espectre/`（C++）——烧进 ESP32，跑在 ESPHome 上，做实时推理；
- **研发端**：`micro-espectre/`（Python）——跑在 PC / Mac 上，做数据采集、模型训练、离线验证、算法迭代。

这两个平台共享同一份算法语义（`micro-espectre/src/mvs_detector.py` 与 ESP32 C++ 组件实现同一套 MVS 逻辑），通过同一份 `PERFORMANCE.md` 验证。算法在 Python 上研发、在 C++ 上量产的分工，让作者可以在 PC 上快速迭代 NBVI / MVS / ML 算法，再把稳定版本移植到资源受限的 ESP32 上。

---

## 四、边界拆分：CSI 数据流与 5 阶段处理管道

`espectre` 的关键是这条 5 阶段处理管道（来自 README）：

```
┌─────────────┐
│  CSI Data   │  原始 Wi-Fi 信道状态信息
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Gain Lock  │  AGC/FFT 稳定化（~3 秒）
│             │  锁定硬件增益，获得稳定测量
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Auto     │  自动子载波选择（启动时一次）
│ Calibration │  用 NBVI 算法挑 12 个最优子载波
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Adaptive   │  auto: P95 × 1.1 | min: P100
│  Threshold  │  或固定阈值
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Hampel    │  湍流异常值剔除
│   Filter    │  （默认开启）
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Low-pass   │  噪声平滑
│   Filter    │  （可选，默认关闭）
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Detection   │  MVS 或 ML 得分
│ Evaluation  │  每个 evaluation_interval 包评估一次
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Hit Filter  │  motion_on_hits / motion_off_hits
│             │  边沿驱动 IDLE ↔ MOTION
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Home        │  边沿触发 motion 二元信号
│ Assistant   │  + 周期发布 Movement Score / Threshold
└─────────────┘
```

---

## 五、关键机制 1：Gain Lock——把不可控的硬件增益锁死

Wi-Fi CSI 数据最大的“脏源”是**ESP32 自带的自动增益控制 (AGC) 和 FFT scaling**。如果不锁定，接收端 AGC 会随信号强度自动调整，导致同一个物理运动在 CSI 幅度上呈现完全不同的数值。

espectre 的解法来自 Espressif 官方 esp-csi 例程：

```c
extern void phy_fft_scale_force(bool force_en, int8_t force_value);
extern void phy_force_rx_gain(bool force_en, int8_t force_value);

if (packet_count < 300) {
    agc_samples[packet_count] = phy_info->agc_gain;   // uint8_t
    fft_samples[packet_count] = phy_info->fft_gain;   // int8_t
} else if (packet_count == 300) {
    median_agc = calculate_median(agc_samples, 300);
    median_fft = calculate_median(fft_samples, 300);
    phy_fft_scale_force(true, median_fft);
    phy_force_rx_gain(true, median_agc);
    on_gain_locked_callback();
}
```

**3 秒 / 300 个包采集 → 取中位数 → 强制锁定**。为什么用中位数而不是均值？README 解释：因为偶发异常包会拉偏均值，中位数更鲁棒。

锁定后，所有后续 CSI 数据都有**稳定的硬件增益基线**，基线方差才可信，自适应阈值才能算准。

### 没 Gain Lock 怎么办？

老款 ESP32（基线版本）和 ESP32-S2 没有 `phy_fft_scale_force` / `phy_force_rx_gain` 这两个 undocumented 函数。espectre 给出的 fallback 是 **CV Normalization**：

```
turbulence = σ(amplitudes)         # 增益锁定时
turbulence = σ(amplitudes) / μ(amplitudes)  # 增益未锁定时（CV，变异系数）
```

CV 是无量纲比值，**对线性增益缩放数学不变**：

```
CV(kA) = σ(kA) / μ(kA) = k·σ(A) / k·μ(A) = σ(A) / μ(A) = CV(A)
```

即使 AGC 在跑、信号强度在变，**CV 反映的信道“湍流程度”依然稳定**。

---

## 六、关键机制 2：NBVI 自动子载波选择——零配置的 F1 96%+

Wi-Fi HT20 模式下有 64 个 OFDM 子载波，**不是每个子载波都适合动检**。有些子载波对环境变化极敏感、噪声大；有些对运动几乎没反应。

espectre 的解法是 **NBVI（Normalized Band Variance Index）**——启动时花 ~10 秒，自动从 64 个子载波中选 12 个**非连续**的最优子载波，**实现 F1 > 96% 且零人工配置**。

NBVI 算法的思路：

1. 启动后采集 `10 × window_size` 个 CSI 包（默认 `window_size=100`，即 1000 包）；
2. 计算每个子载波在 10 个连续窗口上的方差；
3. 计算**谱多样性**——相邻子载波方差不应高度相关（避免冗余）；
4. 选出 12 个**方差大 + 谱多样性高**的子载波。

这种"启动时自校准"的思路贯穿整个项目——NBVI 在做、Hampel 滤波在过滤异常、自适应阈值在算 P95——所有需要手工调的超参都被算法在启动 / 运行时自动算出来。

**实战经验**：README 特别提醒 MVS 模式下，**启动后 10 秒内必须保持房间安静**（不能有人走动），否则校准出来的基线方差会偏，导致后续误报率高。ML 模式因为是基于训练好的模型权重，不需要这步校准。

---

## 七、关键机制 3：MVS 与 ML 两种检测算法

espectre 提供两种检测算法，可通过 `detection_algorithm` 参数切换：

### 7.1 MVS（Moving Variance Segmentation，移动方差分段）—— 默认

关键公式：

```
turbulence(packet) = σ(amplitudes_of_12_subcarriers)
moving_variance(window) = Var(turbulence_over_last_100_packets)
motion = (moving_variance > adaptive_threshold)
```

其中 `adaptive_threshold`：

- `auto` 模式：`P95(turbulence) × 1.1`（在窗口内取 95 分位再乘 1.1）
- `min` 模式：取最大湍流值（`P100`）
- `manual` 模式：固定值

`motion_on_hits` / `motion_off_hits` 两个参数控制边沿去抖——**连续 N 个窗口超过阈值才报 MOTION，连续 M 个窗口低于阈值才报 IDLE**。这能极大降低短暂抖动造成的误报。

### 7.2 ML（神经网络检测器）—— 实验性，2025 末新增

ML 模式使用训练好的神经网络权重（`micro-espectre/models/`），输入是窗口内的湍流序列，输出是 motion probability。

README 强调：

> **New ML Detector**: Neural network-based motion detection. No calibration required, runs on-device. This is an experimental feature, and feedback is welcome in the dedicated [ML detector discussion](https://github.com/francescopace/espectre/discussions/126).

> **新 ML 检测器**：基于神经网络的运动检测。无需校准，在设备上运行。这是一个实验性功能，欢迎在专门的 [ML 检测器讨论区](https://github.com/francescopace/espectre/discussions/126) 反馈。

ML 模式跳过了 10 秒启动校准——不需要在启动后保持房间安静，因为它不依赖自适应阈值。

### 7.3 实测性能（自报 v2.8.0，2026-05-21 验证）

`PERFORMANCE.md` 给出的多芯片实测数据（所有芯片同一组统一配置：window=100、NBVI、Hampel 开启、adaptive percentile-based threshold）：

| 芯片 | 算法 | Recall | Precision | FP Rate | F1 |
|---|---|---|---|---|---|
| ESP32-C3 | MVS Default | 98.5% | 100.0% | 0.0% | 99.3% |
| ESP32-C3 | ML | 100.0% | 100.0% | 0.0% | 100.0% |
| ESP32-C6 | MVS Default | 99.7% | 100.0% | 0.0% | 99.9% |
| ESP32-C6 | ML | 100.0% | 100.0% | 0.0% | 100.0% |
| ESP32-S3 | MVS Default | 99.7% | 100.0% | 0.0% | 99.9% |
| ESP32-S3 | ML | 100.0% | 100.0% | 0.0% | 100.0% |
| ESP32 (原版) | MVS Default | 99.4% | 100.0% | 0.0% | 99.7% |

训练集规模：

| 芯片 | Baseline 包 | Movement 包 | 总计 |
|---|---|---|---|
| ESP32-C3 | 4094 | 4076 | 8170 |
| ESP32-C5 | 4350 | 4336 | 8686 |
| ESP32-C6 | 4755 | 4890 | 9645 |
| ESP32-S3 | 4360 | 4375 | 8735 |
| ESP32 | 4159 | 4083 | 8242 |
| 合计 | 21,718 | 21,760 | 43,478 |

> 数据来源：仓库 `PERFORMANCE.md`（v2.8.0，2026-05-21 验证）。

**注意：作者用 Precision = 100% + F1 ≥ 99% 这种漂亮数据时，应当意识到实测数据集规模仅 ~43k 包，且是单环境单路由器的；跨家庭、跨路由器、跨墙体材型的实际表现可能略低。**这个项目目前有 8,019 stars，但工业级可靠性还需要在多场景下独立验证。

---

## 八、关键机制 4：与 Home Assistant 的原生集成

espectre 走的是 **ESPHome Native API**——这是 ESPHome 官方推荐的最稳定、低延迟集成方式。

### 8.1 自动发现

ESP32 烧完固件、配好 Wi-Fi 后，Home Assistant 会**自动发现**设备，**不需要任何手工添加**。你马上会看到 3 类实体：

| 实体类型 | 用途 |
|---|---|
| `binary_sensor.motion` | 二元动检信号（边沿触发，状态变化时立即推送） |
| `sensor.movement_score` | 实时 Movement Score（湍流分），周期推送 |
| `number.threshold` | 可调节阈值（自动化里可调） |

调试版 YAML（`-dev.yaml`）还会暴露更多 debug 传感器：

- `free_heap`（剩余堆内存）
- `max_block_size`（最大连续块）
- `loop_time`（主循环耗时）

这三个 debug 传感器非常关键——ESP32 跑 CSI + Wi-Fi + ESPHome + 推理管道，**内存吃紧时会先在这里报警**。

### 8.2 单个 ESP32 接多个房间？

单个 ESP32 监听一整个 Wi-Fi 覆盖范围。README 估算：

> One sensor can monitor ~50 m². For larger homes, use multiple sensors (1 sensor every 50-70 m² for optimal coverage).

> 一个传感器可以监测约 50 m²。对于更大的房屋，使用多个传感器（每 50-70 m² 一个传感器以获得最佳覆盖）。

多 ESP32 部署时，每个房间一个 sensor，全部自动发现到 Home Assistant，在 HA 里组成 zones / groups：

```
┌─────────┐  ┌─────────┐  ┌─────────┐
│ ESP32   │  │ ESP32   │  │ ESP32   │
│ Room 1  │  │ Room 2  │  │ Room 3  │
└────┬────┘  └────┬────┘  └────┬────┘
     │            │            │
     └────────────┴────────────┘
                  │
                  │ ESPHome Native API
                  ▼
         ┌────────────────────┐
         │   Home Assistant   │
         │   (Auto-discovery) │
         └────────────────────┘
```

---

## 九、任务流案例：10 分钟从拆包到 HA 上线

一个完整的最小部署流程（基于 `SETUP.md` Option A：Web Flash，零代码）：

### 9.1 硬件

- ESP32-S3 DevKit × 1（~10 欧元）
- USB-C 线 × 1
- 2.4 GHz 路由器 × 1（家里现成的就行）
- Home Assistant 跑在任何设备上（Raspberry Pi / NAS / PC / 云）

### 9.2 烧固件（5 分钟）

1. 打开 [Releases](https://github.com/francescopace/espectre/releases/latest) 下载对应芯片的 `.bin`（如 `espectre-2.5.0-esp32s3.bin`）
2. 打开 [ESPConnect](https://thelastoutpostworkshop.github.io/ESPConnect/)（Chrome）
3. 接 ESP32 USB → Connect → 选串口 → 选 `.bin` → Flash

### 9.3 配 Wi-Fi（3 分钟）

烧完固件后用任一方式配网：

| 方式 | 操作 |
|---|---|
| BLE（最简单） | ESPHome 或 Home Assistant Companion App |
| USB | [web.esphome.io](https://web.esphome.io) → Connect → Configure WiFi |
| Captive Portal | 连 "espectre Fallback" Wi-Fi → 浏览器配置 |

### 9.4 摆放（2 分钟）

| 距离 | 信号 | 多径 | 灵敏度 | 噪声 | 推荐 |
|---|---|---|---|---|---|
| < 2m | 强 | 极小 | 低 | 低 | ❌ 太近 |
| **3-8m** | 强 | 良好 | 高 | 低 | ✅ **最佳** |
| > 10-15m | 弱 | 不稳定 | 低 | 高 | ❌ 太远 |

摆放要点：

- ✅ 放在监测区域（不必正对路由器）
- ✅ 离地 1–1.5 米（桌面 / 茶几高度）
- ✅ 用 IPEX 外置天线（接收更好）
- ❌ 避免与路由器之间有金属遮挡（冰箱、金属柜）
- ❌ 避免塞进角落（多径多样性下降）

### 9.5 启动后保持安静（MVS 模式）

启动后 10 秒内**保持房间完全静止**——这是 NBVI 自动校准窗口，决定了后续阈值 / 基线方差的准确性。ML 模式跳过这一步。

### 9.6 Home Assistant 自动上线

HA 应该在 30 秒内自动发现设备，三个实体立即可用。在 HA 里建一条自动化：

```yaml
automation:
  - alias: "客厅动检 → 开灯"
    trigger:
      platform: state
      entity_id: binary_sensor.living_room_motion
      to: "on"
    action:
      service: light.turn_on
      target:
        entity_id: light.living_room
      data:
        brightness_pct: 80
```

完成。这就是从拆包到自动化的全部流程。

---

## 十、隐私与伦理：作者写得很克制

`espectre` 的隐私模型在 `README` 末尾 + `SECURITY.md` 里讲得很克制，值得专门看：

### 10.1 收集的是什么

- OFDM 子载波的幅度 / 相位
- 统计信号方差
- **不收集**：个人身份、通信内容、图像、音频

CSI 只反映**无线电信道的物理特征**，不含可识别信息。

### 10.2 隐私优势

- 无摄像头（视觉隐私）
- 无麦克风（音频）
- 无可穿戴设备
- 仅聚合统计指标，无原始识别数据

### 10.3 ⚠️ 警告（作者主动声明）

> **WARNING**: Despite the intrinsic anonymity of CSI data, this system can be used for:
> - **Non-consensual monitoring**: Detecting presence/movement of people without their explicit consent
> - **Behavioral profiling**: With advanced AI models, inferring daily life patterns
> - **Domestic privacy violation**: Tracking activities inside private homes

> **警告**：尽管 CSI 数据本身具有匿名性，本系统仍可能被用于：
> - **非同意监测**：在未经明确同意的情况下检测人员的存在 / 移动
> - **行为画像**：借助高级 AI 模型推断日常生活模式
> - **家庭隐私侵犯**：追踪私人住宅内的活动

### 10.4 用户责任（作者明列）

> The user is solely responsible for using this system and must:
> 1. **Obtain explicit consent** from all monitored persons
> 2. **Respect local regulations** (GDPR in EU, local privacy laws)
> 3. **Clearly inform** about the presence of the sensing system
> 4. **Limit use** to legitimate purposes
> 5. **Protect data** with encryption and controlled access
> 6. **DO NOT use** for illegal surveillance, stalking, or violation of others' privacy

> 用户对使用本系统负全部责任，并且必须：
> 1. **获得所有被监测者的明确同意**
> 2. **遵守当地法规**（欧盟 GDPR、当地隐私法）
> 3. **明确告知**传感系统的存在
> 4. **限制用途**于合法目的
> 5. **通过加密和受控访问保护数据**
> 6. **不得用于**非法监视、跟踪或侵犯他人隐私

作者在 SECURITY.md 里列出了三类滥用场景（非同意监测、行为画像、家庭隐私侵犯）和六条用户责任，这种把伦理责任写进安装前必读文档的做法，在开源 IoT 动检项目里属于少数。多数同类项目只在 LICENSE 里加一句免责声明，不会主动列出具体滥用场景。

---

## 十一、采用顺序与决策建议

### 11.1 适合用 espectre 的场景

- **智能家居自动化**：检测有人进房就开灯 / 开空调 / 播放音乐，无人 5 分钟就关
- **家庭安防**：与 HA 报警系统联动，检测到 MOTION 持续 N 秒（人在）+ 无人在家 = 报警
- **老人看护**：检测活动频率——过去 24 小时无活动 = 异常提醒
- **节能**：按房间有人 / 无人动态控制 HVAC
- **儿童监护**：夜里孩子离开房间报警
- **小型办公 / 工作室**：会议室占用检测，替代 PIR 但更精准
- **隐私敏感场景**：卧室、浴室、医疗房间、心理咨询室——任何不允许摄像头的房间

### 11.2 不适合用 espectre 的场景

- **人数统计 / 身份识别**——它只输出 IDLE / MOTION，不识别人
- **动作类型识别**——它不能区分"走过" vs "挥手" vs "摔倒"
- **超大面积 / 复杂户型**——单传感器覆盖 50 m²，大平层 / 别墅需要部署多个
- **需要 < 100ms 延迟的实时控制**——评估窗口是 100 个包（约 1–2 秒），不适合硬实时
- **完全没有 Home Assistant 经验的纯硬件玩家**——`SETUP.md` 假设你有 HA / ESPHome 基础

### 11.3 采用顺序

如果你决定上手，建议按这个顺序推进，每一步验证通过再进入下一步：

1. **单设备验证（第 1 天）**：用一台 ESP32-S3 跑通 SETUP.md Option A（Web Flash），在 HA 里确认 `binary_sensor.motion`、`sensor.movement_score`、`number.threshold` 三个实体出现。在自己常待的房间放一天，观察 movement_score 在静止 / 走动 / 离开时的数值范围。
2. **阈值调参（第 2-3 天）**：根据上一步观察到的 movement_score 分布，用 `number.threshold` 调整阈值。如果误报多，调高 `motion_on_hits`；如果漏报多，调低阈值或减小 `motion_off_hits`。参考 `TUNING.md`。
3. **多房间部署（第 1 周）**：在 50-70 m² 范围内加第二台、第三台 ESP32，每台独立校准。在 HA 里用 zones / groups 把多个 sensor 组织成房间级占用状态。
4. **自动化联动（第 2 周）**：把 `binary_sensor.motion` 接入 HA 自动化，先做低风险场景（开灯、关灯、HVAC 切换），跑一周稳定后再接安防报警。
5. **算法切换（可选）**：如果 MVS 模式在你的环境下误报率高，可以试 ML 模式（`detection_algorithm: ml`）。ML 不需要启动校准，但模型权重是作者训练的，跨环境泛化能力需要自己验证。

### 11.4 决策建议

| 你的情况 | 推荐 |
|---|---|
| 想要"最低成本、零云端、隐私友好"的动检 | ✅ espectre + ESP32-S3（10 欧元） |
| 想要识别身份 / 动作类型 | ❌ 上毫米波雷达（如 ESP32 + RD-03D）或本地 ReID 摄像头 |
| 想要低延迟（< 100ms）硬实时 | ❌ 上 PIR + 红外阵列 |
| 想要做老人跌倒检测 | ⚠️ espectre 只能检测"有 / 无活动"，不能识别姿态；建议组合 IMU 可穿戴 |
| 想要做安防 | ✅ espectre + HA 报警系统，但建议在 HA 里加**多源融合**（门窗磁 + 玻璃破碎 + espectre），单传感容易被绕开 |

---

## 十二、进阶路径

如果你已经跑通基础部署，下面是几个可以继续深入的方向：

### 12.1 算法层深入

- **读 `micro-espectre/ALGORITHMS.md`**：741 行算法详解，覆盖 CSI 物理模型、Gain Lock 推导、NBVI 谱多样性公式、MVS 阈值自适应、ML 模型架构。这是理解整个系统为什么这么设计的核心文档。
- **跑 `micro-espectre/` 的 Jupyter notebooks**：在 PC 上复现作者的离线分析流程，用真实 CSI 数据跑一遍 NBVI 选择和 MVS 检测，建立对参数敏感度的直觉。
- **训练自己的 ML 模型**：用 `micro-espectre/tools/` 的采集脚本在你自己的环境里收数据，训练针对你家墙体材型、路由器、家具布局的定制模型权重。

### 12.2 系统层扩展

- **多传感器融合**：在 HA 里把多个房间的 espectre 和门窗磁、PIR、毫米波雷达组合，用 HA 的 Bayesian sensor 或自定义 template sensor 做占用状态融合，降低单点误报。
- **长期活动统计**：把 `sensor.movement_score` 写入 HA 的 long-term statistics，用 Grafana 或 HA 自带统计图做 24 小时 / 7 天活动模式分析，用于老人看护场景。
- **跨 session 记忆**：在 HA 里记录每天的 MOTION 时长分布，结合其他传感器（门窗、光照、温湿度）做异常检测——比如"过去 12 小时无活动"自动推送提醒。

### 12.3 贡献回上游

- **跨环境数据集**：作者的多芯片验证数据集是单环境单路由器的。如果你在不同墙体材型、不同路由器、不同户型下采集了数据，可以考虑贡献给 `micro-espectre/data/`，帮助改进 ML 模型的泛化能力。
- **新芯片适配**：仓库目前支持 S3 / C6 / C3 / C5 / 原版 / S2。如果你手上有其他 ESP32 变体（如 ESP32-P4），可以测试并反馈 Gain Lock fallback 行为。
- **ML 模型迭代**：ML 检测器还在实验阶段（discussion #126），作者明确欢迎反馈。如果你训练出了更好的模型权重，可以提 PR。

### 12.4 自测检查

用这几个检查项验证你是否真的掌握了 espectre 的部署和调参：

- [ ] 能说清楚 Gain Lock 锁定的是哪两个硬件参数，以及为什么用中位数而不是均值
- [ ] 能解释 NBVI 为什么选 12 个非连续子载波，而不是连续的 12 个
- [ ] 在自己的环境里测出 MVS 模式的 movement_score 在静止 / 走动 / 离开三个状态下的典型数值范围
- [ ] 能在 HA 里写出基于 `binary_sensor.motion` 的自动化，并配置 `motion_on_hits` / `motion_off_hits` 控制去抖
- [ ] 能判断自己的场景是否应该切到 ML 模式，并说出切换的代价（模型权重泛化性、内存占用）

---

## 十三、结语

`espectre` 把 Wi-Fi CSI 采集、信号处理、边缘 AI 推理、ESPHome 组件、Home Assistant 集成这条完整链路用 GPL-3.0 开源了出来。对正在做智能家居、IoT 信号处理或边缘 AI 的工程师来说，它同时是一套可用的动检方案和一个可学习的工程参考——前者解决"卧室里有没有人"的问题，后者展示"如何把研究算法落地成 ESPHome 组件"。

它的边界同样明确：只输出 IDLE / MOTION 二元状态，不识别人数、身份、姿态；单传感器覆盖约 50 m²；自报 F1 ≥ 99% 的数据来自单环境单路由器，跨场景表现需要自己验证。如果你的需求落在这些边界内，按"采用顺序"那一节的 5 步推进，半天内可以跑通一个房间的基础部署。
