---
title: "Deep-Live-Cam：一键实时换脸工具的技术原理与使用指南"
date: "2026-03-28T22:00:00+08:00"
slug: "deep-live-cam-realtime-faceswap"
github_repo: "hacksider/Deep-Live-Cam"
description: "Deep-Live-Cam 实时换脸工具：一张照片即可实时换脸，支持 webcam 直播、视频通话、电影角色扮演。"
draft: false
categories: ["技术笔记"]
tags: ["AI视频"]
---

## 一、项目概览

[Deep-Live-Cam](https://github.com/hacksider/Deep-Live-Cam) 是一键实时换脸与视频深度伪造工具，只需一张照片即可实现实时换脸。

| 指标 | 数值 |
|------|------|
| GitHub Stars | 90.7k |
| Forks | 13.2k |
| Contributors | 57 |
| 最新版本 | 2.7 beta（2026-03-11） |
| License | AGPL-3.0 |
| 语言 | Python 100% |

> Real-time face swap and video deepfake with a single click and only a single image.

与需要大量训练数据的传统换脸方案不同，Deep-Live-Cam 的特点在于：

- **零训练**：无需针对目标人物训练模型
- **实时性**：10-30 秒内完成预处理，之后实时推流
- **全平台**：覆盖 NVIDIA / AMD / Apple / Intel / CPU

---

## 二、核心功能

### 2.1 三种使用模式

| 模式 | 说明 | 使用场景 |
|------|------|----------|
| **Image/Video Mode** | 选择源脸照片 + 目标图片/视频，一键生成 | 静态换脸、图片创作 |
| **Webcam Mode** | 选择源脸照片，摄像头实时预览 | 直播、视频通话 |
| **Live Show** | 结合 OBS 等工具进行直播推流 | 线上表演、内容创作 |

### 2.2 特色功能

| 功能 | 说明 |
|------|------|
| **Mouth Mask** | 保留原始嘴型，准确复现口型（唱歌、说话） |
| **Face Mapping** | 多人脸同时换脸 |
| **Many Faces** | 替换视频中所有出现的人脸 |
| **Movie Mode** | 实时观看电影，替换主角脸 |

### 2.3 硬件支持

| 硬件 | 支持情况 |
|------|----------|
| **NVIDIA GPU** | CUDA 加速 |
| **AMD GPU** | DirectML |
| **Mac Silicon** | Metal |
| **CPU** | 通用支持 |
| **Intel GPU** | 支持 |

---

## 三、工作原理

### 3.1 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Deep-Live-Cam 架构                       │
├─────────────────────────────────────────────────────────────┤
│  输入层                                                      │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │ Source Face │  │ Target Video │                         │
│  │ （单张照片）  │  │ （图片/视频） │                         │
│  └──────────────┘  └──────────────┘                         │
├─────────────────────────────────────────────────────────────┤
│  核心处理层                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ InsightFace │  │ Face Swapper│  │ Face        │       │
│  │ 人脸检测     │  │ 脸部交换     │  │ Enhancer    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
├─────────────────────────────────────────────────────────────┤
│  加速层                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ CUDA    │ │ DirectML │ │ Metal    │ │ CPU      │     │
│  │ NVIDIA  │ │ AMD      │ │ Apple    │ │ 通用     │     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
├─────────────────────────────────────────────────────────────┤
│  输出层                                                      │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │ Preview      │  │ Output      │                         │
│  │ 实时预览     │  │ 图片/视频保存 │                         │
│  └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 核心技术依赖

| 组件 | 说明 |
|------|------|
| **InsightFace** | 人脸检测、分析、识别库 |
| **ffmpeg** | 视频编解码、处理 |
| **CUDA / DirectML / Metal** | GPU 加速推理 |

---

## 四、快速开始

### 4.1 安装

**预构建版本**（推荐）：https://deeplivecam.net/index.php/quickstart

| 平台 | 说明 |
|------|------|
| Windows | 一键安装包 |
| Mac Silicon | Apple Silicon 专用 |
| CPU | 无需显卡 |

**手动安装**（环境要求：Python 3.10+、ffmpeg）：

```bash
git clone https://github.com/hacksider/Deep-Live-Cam.git
cd Deep-Live-Cam
pip install -r requirements.txt
# 从 https://huggingface.co/hacksider/deep-live-cam/tree/main 下载模型
python run.py
```

### 4.2 三步实时换脸

```
1️⃣ 选择一张人脸照片（Source Face）
2️⃣ 选择摄像头（Camera）
3️⃣ 点击 "Live!" 开始实时换脸
```

### 4.3 命令行模式

```bash
python run.py -s source.jpg -t target.mp4                    # 指定源脸和目标
python run.py -s source.jpg -t target.mp4 -o output/         # 指定输出路径
python run.py -s source.jpg -t target.mp4 --keep-fps         # 保持原始帧率
python run.py -s source.jpg -t target.mp4 --keep-audio       # 保持原始音频
python run.py -s source.jpg -t target.mp4 --many-faces       # 多人脸模式
python run.py -s source.jpg -t target.mp4 --mouth-mask       # 嘴型遮罩
```

### 4.4 Webcam 直播设置

```bash
python run.py
# 选择源脸照片 → 点击 "Live" → 等待预览出现（10-30 秒）→ 使用 OBS 等工具进行屏幕捕获直播
```

---

## 五、应用场景

| 场景 | 类别 | 说明 |
|------|------|------|
| Meme 创作 | 内容创作 | Many Faces 批量换脸创作病毒视频 |
| 电影扮演 | 娱乐 | 把自己脸换到电影角色上观看 |
| 虚拟主播 | 内容创作 | 实时换脸进行直播 |
| 视频通话 | 娱乐 | Zoom/Teams 中实时换脸 |
| 直播表演 | 娱乐 | 主播互动表演 |
| 电影制作 | 专业 | 角色换脸后期处理 |
| 服装设计 | 专业 | AI 模特展示 |
| 数字人 | 专业 | 虚拟形象生成 |

---

## 六、道德声明与合规

### 6.1 内置安全措施

| 措施 | 说明 |
|------|------|
| **内容审核** | 自动拦截裸体、暴力等不当内容 |
| **敏感素材拦截** | 战争 footage 等敏感材料 |

### 6.2 用户责任

| 要求 | 说明 |
|------|------|
| **知情同意** | 使用真人脸须获得授权 |
| **标注义务** | 分享深度伪造内容必须标注 |
| **合法使用** | 遵守当地法律法规 |

### 6.3 项目方立场

> We are aware of the potential for unethical applications and are committed to preventative measures. We may shut down the project or add watermarks if legally required.

---

## 七、技术参数

### 7.1 命令行参数

| 参数 | 说明 |
|------|------|
| `-s, --source` | 源脸照片路径 |
| `-t, --target` | 目标图片/视频路径 |
| `-o, --output` | 输出路径 |
| `--frame-processor` | 帧处理器（face_swapper, face_enhancer） |
| `--keep-fps` | 保持原始帧率 |
| `--keep-audio` | 保持原始音频 |
| `--many-faces` | 替换所有人脸 |
| `--mouth-mask` | 嘴型遮罩 |
| `--live-mirror` | 镜像预览 |
| `--max-memory` | 最大内存使用（GB） |
| `--execution-provider` | 执行 Provider（cpu/cuda/directml） |

### 7.2 模型下载

| 模型 | 下载地址 |
|------|----------|
| 所有模型 | https://huggingface.co/hacksider/deep-live-cam/tree/main |

---

## 八、资源链接

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/hacksider/Deep-Live-Cam |
| 官网 | https://deeplivecam.net/ |
| 预构建版本 | https://deeplivecam.net/index.php/quickstart |
| 模型下载 | https://huggingface.co/hacksider/deep-live-cam/tree/main |