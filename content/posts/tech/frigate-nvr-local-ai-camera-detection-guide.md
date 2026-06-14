---
title: "Frigate NVR：本地运行的 AI 摄像头目标检测监控方案"
date: "2026-05-25T09:12:29+08:00"
slug: "frigate-nvr-local-ai-camera-detection-guide"
description: "Frigate 是专为 Home Assistant 设计的开源 NVR（网络视频录像机），通过 OpenCV 和 TensorFlow 在本地实现 IP 摄像头目标检测，支持 GPU/AI 加速、MQTT 集成、24/7 录制和 WebRTC 低延迟直播，32.9k Stars。"
draft: false
categories: ["技术笔记"]
tags: ["Home Assistant", "NVR", "TensorFlow", "目标检测", "开源监控"]
---

# Frigate NVR：本地运行的 AI 摄像头目标检测监控方案

Frigate 是今天 GitHub Trending 上为数不多的非 AI 编程类项目——一个为 **Home Assistant** 深度集成打造的本地 NVR 系统，主打用 AI 在摄像头上做实时目标检测，不依赖云端。所有推理都在本地完成，隐私不会流出局域网。

**核心判断：** 如果你已经有 IP 摄像头，想把录像和 AI 检测能力接入 Home Assistant，Frigate 是目前开源社区里最成熟、文档最完整、社区最活跃的方案。它不是一个通用监控软件，而是一个"AI 检测优先"的本地录像系统。

## 适用场景

Frigate 解决的是这个具体问题：传统 NVR 只是录像，看录像靠人工；Frigate 在录像的同时用 TensorFlow 做本地目标检测，检测到人/车/宠物等对象时才触发自动化，真正让摄像头变成智能传感器。

适合以下用户：

- Home Assistant 用户，想把摄像头纳入自动化体系
- 有 GPU 或 AI 加速卡（如 Google Coral、Intel Myriad X），想跑本地目标检测
- 需要低延迟直播 + 检测通知，不想用云服务
- 对隐私有要求，检测和录像必须本地运行

不适合以下场景：

- 没有任何 IP 摄像头，需要从零购买设备
- 只需要远程查看实时画面，不需要 AI 检测
- 网络环境复杂，无法稳定访问摄像头 RTSP 流

## 系统架构

Frigate 的架构围绕"只在必要时检测"这个原则设计，核心组件如下：

```
摄像头 RTSP 流
    │
    ▼
┌─────────────────────┐
│  FFmpeg 重流化        │ ← 统一处理不同摄像头的编码格式
│  (re-streaming)      │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│  运动检测 (Motion)   │ ← 低开销，判断哪里发生了变化
└─────────────────────┘
    │
    ▼ (仅当 motion 区域触发)
┌─────────────────────┐
│  TensorFlow 对象检测  │ ← 独立进程，可 GPU/加速卡加速
│  (Object Detection)  │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│  检测结果 → MQTT     │ ← 推送给 Home Assistant
│  录像写入 → 存储     │ ← 按时间或按对象保留
└─────────────────────┘
```

三个关键设计决策值得注意：

1. **运动检测先于目标检测**：先用轻量运动检测判断画面是否值得跑 AI，而不是每帧都跑检测。这让 Frigate 能在 CPU 上也能运行。
2. **检测进程独立**：TensorFlow 检测跑在独立进程，和主录像进程解耦，主录像不会因为检测负载而卡顿。
3. **MQTT 作为主集成协议**：检测结果通过 MQTT 发布，Home Assistant 收到后可以立即触发自动化，这是 Frigate 和 HA 集成最深的层面。

## 快速开始

### 前提条件

- Docker 或 Docker Compose
- 至少一个支持 RTSP 流的 IP 摄像头
- 推荐配置：GPU 或 AI 加速卡（Google Coral TPU、Intel GPU、华为昇腾 NPU 等）

### 安装

官方推荐 Docker Compose 方式：

```yaml
version: "3.8"
services:
  frigate:
    container_name: frigate
    image: ghcr.io/blakeblackshear/frigate:stable
    shm_size: "64mb"
    volumes:
      - ./config:/config
      - ./media:/media/frigate
      - /etc/localtime:/etc/localtime:ro
    ports:
      - "5000:5000"
      - "8554:8554"
    environment:
      FRIGATE_RTSP_PASSWORD: "your_rtsp_password"
```

### 配置摄像头

在 `config/config.yml` 中定义摄像头：

```yaml
cameras:
  front_door:
    ffmpeg:
      inputs:
        - path: rtsp://192.168.1.100:554/stream1
          roles:
            - detect      # 用于目标检测的流
            - record      # 用于录像的流
    detect:
      enabled: true
      width: 1920
      height: 1080
      fps: 5
    objects:
      track:
        - person
        - car
        - dog
        - cat
      filters:
        person:
          min_area: 5000
          max_area: 100000
          threshold: 0.7
```

### Home Assistant 集成

通过 HACS 安装 `Frigate Home Assistant Integration`，之后在 HA 中即可看到每个摄像头的检测状态和实体：

```
- sensor.front_door_detection_fps   # 检测帧率
- sensor.front_door_fps            # 总帧率
- camera.front_door                # 实时画面
- switch.front_door_record         # 录像开关
```

MQTT 消息格式示例：

```json
{
  "type": "new",
  "timestamp": 1748141349.123,
  "camera": "front_door",
  "object": {
    "id": "person-e8d3f2",
    "label": "person",
    "confidence": 0.92,
    "box": [0.1, 0.2, 0.5, 0.8],
    "area": 50000
  }
}
```

## 支持的目标检测模型

Frigate 不绑定单一检测模型，可按硬件选择：

| 加速方案 | 适用场景 | 性价比 |
|---------|---------|--------|
| Google Coral TPU (USB/M.2) | 树莓派 + 低功耗 | 最高 |
| Intel OpenVINO (CPU/iGPU/dGPU) | 已有 Intel 硬件 | 高 |
| NVIDIA GPU (CUDA/cuDNN) | 已有 NVIDIA 显卡 | 中 |
| 华为昇腾 NPU | 国内用户 | 高 |
| 纯 CPU (TensorFlow Lite) | 无加速卡 | 勉强可用 |

官方文档列出了完整的[支持检测器列表](https://docs.frigate.video/configuration/object_detectors/)，不同模型在精度和速度上有差异，需要根据摄像头数量和帧率要求选择。

## 录像保留策略

Frigate 支持两种录像保留方式，按需配置：

```yaml
record:
  enabled: true
  retain:
    days: 7
    mode: motion  # 或 "all"（全时录像）
  events:
    retain:
      default: 14
      mode: motion
```

- **motion 模式**：只保留检测到对象前后的录像片段，存储效率高，是默认推荐模式
- **all 模式**：24/7 全时录像，类似传统 NVR

## 为什么值得在 2026 年关注

Frigate 上 Trending 并不是偶然。近半年有几个重要进展：

- **多摄像头同步回放**：支持在一个界面同时回放多个摄像头的历史片段，对多摄像头用户体验提升明显
- **内置遮挡/区域编辑器**：不用第三方工具，在 Web UI 里直接画检测区域和遮挡掩码
- **WebRTC 直播**：相比传统的 HLS 流，延迟从 3-5 秒降到 500ms 左右
- **多语言界面**：官方自带简体中文，有活跃的 Weblate 翻译社区
- **存储后端扩展**：除了本地存储，也支持 S3 兼容存储方案

对于 Home Assistant 用户，Frigate 是将"被动录像"变成"主动感知"的最直接方案。摄像头检测到人 → MQTT 推送 → Home Assistant 自动化，这个链路在 Frigate 出现之前需要自己拼装很多组件。

## 采用建议

从零开始在 Frigate 上投入，建议按以下顺序推进：

1. **先用单个摄像头跑通**：用 Docker Compose 起一个 Frigate，配置一个摄像头的 detect + record + MQTT，确认 HA 能收到事件
2. **选好检测模型**：如果有多张显卡或 Coral TPU，优先上加速；如果只有 CPU，从 TensorFlow Lite 开始
3. **配置自动化**：先从简单的"检测到人推送通知"开始，再逐步扩展到灯光联动、门锁联动等场景
4. **调优参数**：调整 `min_area`、`threshold`、`fps` 等参数，减少误报
5. **扩展到多摄像头**：Frigate 支持统一管理多路摄像头，统一事件流

## 不覆盖的范围

- 摄像头购买指南：Frigate 不负责摄像头的选型和安装
- 局域网网络配置：RTSP 流的稳定传输依赖网络质量
- 商业监控方案：Frigate 是个人/家庭用途为主的项目，不适合大型商业部署
- 云端录像备份：Frigate 本身不提供云同步，需要自己搭 S3 或其他方案

---

**仓库信息**

- GitHub: https://github.com/blakeblackshear/frigate
- 文档： https://docs.frigate.video
- Stars: 32.9k（2026-05-25）
- License: MIT
- 主要语言： Python
