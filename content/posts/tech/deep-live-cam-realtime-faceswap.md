---
title: "Deep-Live-Cam：89.7k Stars 一键实时换脸与视频深度伪造（Deepfake）工具"
date: "2026-03-28T22:00:00+08:00"
slug: "deep-live-cam-realtime-faceswap"
description: "深度解读 Deep-Live-Cam：89.7k Stars 的实时换脸与视频深度伪造工具，一键操作、仅需一张照片，支持 webcam 直播、视频通话、电影角色扮演等多种场景。"
draft: false
categories: ["技术笔记"]
tags: ["Deep-Live-Cam", "实时换脸", "深度伪造", "Deepfake", "AI视频"]
---

# Deep-Live-Cam：89.7k Stars 一键实时换脸与视频深度伪造工具

> **目标读者**：对 AI 换脸技术感兴趣的内容创作者、开发者
> **核心问题**：如何用一张照片实现实时换脸和视频深度伪造？
> **难度**：⭐⭐⭐（进阶实用）
> **来源**：GitHub hacksider/Deep-Live-Cam，2026-03-28

---

## 一、项目概览

### 1.1 为什么这个项目值得关注

[Deep-Live-Cam](https://github.com/hacksider/Deep-Live-Cam) 是**一键实时换脸与视频深度伪造工具**，只需一张照片即可实现实时换脸和视频深度伪造。

**核心数据：**

| 指标 | 数值 |
|------|------|
| GitHub Stars | **90.7k** |
| Forks | 13.2k |
| Contributors | 57 |
| 最新版本 | 2.7 beta（2026-03-11） |
| License | AGPL-3.0 |
| 语言 | Python 100% |

**核心定位：**

> Real-time face swap and video deepfake with a single click and only a single image.

### 1.2 媒体报道

| 媒体 | 标题 |
|------|------|
| Ars Technica | "Deep-Live-Cam goes viral, allowing anyone to become a digital doppelganger" |
| Yahoo! | "OK, this viral AI live stream software is truly terrifying" |
| CNN Brasil | "AI can clone faces on webcam; understand how it works" |
| PetaPixel | "Deepfake AI Tool Lets You Become Anyone in a Video Call With Single Photo" |
| IShowSpeed | "What the F**! Why do I look like Vinny Jr? I look exactly like Vinny Jr!?" |

---

## 二、核心功能

### 2.1 三大使用模式

| 模式 | 说明 | 使用场景 |
|------|------|----------|
| **Image/Video Mode** | 选择源脸照片 + 目标图片/视频，一键生成 | 静态换脸、图片创作 |
| **Webcam Mode** | 选择源脸照片，摄像头实时预览 | 直播、视频通话 |
| **Live Show** | 结合 OBS 等工具进行直播推流 | 线上表演、内容创作 |

### 2.2 特色功能

| 功能 | 说明 | 示例 |
|------|------|------|
| **Mouth Mask** | 保留原始嘴型，准确复现口型 | 唱歌、说话 |
| **Face Mapping** | 多人脸同时换脸 | 多人视频通话 |
| **Many Faces** | 一个视频中替换所有出现的人脸 | 病毒视频创作 |
| **Movie Mode** | 实时观看电影，替换主角脸 | 娱乐体验 |

### 2.3 硬件支持

| 硬件 | 支持情况 |
|------|----------|
| **NVIDIA GPU** | ✅ CUDA 加速 |
| **AMD GPU** | ✅ DirectML |
| **Mac Silicon** | ✅ Metal |
| **CPU** | ✅ 通用支持 |
| **Intel GPU** | ✅ |

---

## 三、工作原理

### 3.1 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Deep-Live-Cam 架构                              │
├─────────────────────────────────────────────────────────────┤
│  输入层                                                      │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │ Source Face │  │ Target Video │                         │
│  │ (单张照片)   │  │ (图片/视频)   │                         │
│  └──────────────┘  └──────────────┘                         │
├─────────────────────────────────────────────────────────────┤
│  核心处理层                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ InsightFace │  │ Face Swapper│  │ Face       │       │
│  │ 人脸检测    │  │ 脸部交换     │  │ Enhancer  │       │
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
| **CUDA**（NVIDIA GPU 加速）/ **DirectML**（AMD GPU 加速） | GPU 加速推理 |

---

## 四、快速开始

### 4.1 方式一：预构建版本（推荐新手）

**下载地址：** https://deeplivecam.net/index.php/quickstart

支持平台：

| 平台 | 说明 |
|------|------|
| Windows | 一键安装包 |
| Mac Silicon | Apple Silicon 专用 |
| CPU | 无需显卡 |

### 4.2 方式二：手动安装

**环境要求：**

| 要求 | 说明 |
|------|------|
| Python | 3.10+ |
| NVIDIA/AMD GPU | 可选，建议使用 |
| ffmpeg | 视频处理必需 |

**安装步骤：**

```bash
# 克隆仓库
git clone https://github.com/hacksider/Deep-Live-Cam.git
cd Deep-Live-Cam

# 安装依赖
pip install -r requirements.txt

# 下载模型
# 从 https://huggingface.co/hacksider/deep-live-cam/tree/main 下载所有模型

# 运行
python run.py
```

### 4.3 三步实时换脸

```
1️⃣ 选择一张人脸照片（Source Face）
2️⃣ 选择摄像头（Camera）
3️⃣ 点击 "Live!" 开始实时换脸
```

### 4.4 命令行模式

```bash
# 指定源脸和目标
python run.py -s source.jpg -t target.mp4

# 指定输出路径
python run.py -s source.jpg -t target.mp4 -o output/

# 保持原始帧率
python run.py -s source.jpg -t target.mp4 --keep-fps

# 保持原始音频
python run.py -s source.jpg -t target.mp4 --keep-audio

# 多人脸模式
python run.py -s source.jpg -t target.mp4 --many-faces

# 嘴型遮罩
python run.py -s source.jpg -t target.mp4 --mouth-mask
```

### 4.5 Webcam 直播设置

```bash
# 1. 运行程序
python run.py

# 2. 选择源脸照片
# 3. 点击 "Live"
# 4. 等待预览出现（10-30秒）
# 5. 使用 OBS 等工具进行屏幕捕获直播
```

---

## 五、应用场景

### 5.1 内容创作

| 场景 | 说明 |
|------|------|
| **Meme 创作** | 用 Many Faces 功能批量换脸创作病毒视频 |
| **电影扮演** | 把自己脸换到电影角色上观看 |
| **虚拟主播** | 实时换脸进行直播 |

### 5.2 娱乐体验

| 场景 | 说明 |
|------|------|
| **视频通话** | Zoom/Teams 中实时换脸 |
| **Omegle 整蛊** | 视频聊天中惊喜朋友 |
| **直播表演** | IShowSpeed 等主播使用 |

### 5.3 专业应用

| 场景 | 说明 |
|------|------|
| **电影制作** | 角色换脸后期处理 |
| **服装设计** | AI 模特展示 |
| **数字人** | 虚拟形象生成 |

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
| **知情同意** | 使用真人脸需获得授权 |
| **标注义务** | 分享深度伪造内容必须标注 |
| **合法使用** | 遵守当地法律法规 |

### 6.3 项目方声明

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

---

## 九、总结

### 9.1 关键价值

Deep-Live-Cam 的实际门槛：一张照片 + 一次点击，就能跑出专业级实时换脸效果。

| 传统方式 | Deep-Live-Cam 方式 |
|----------|-------------------|
| 专业团队制作 | 只需一张照片 |
| 复杂配置 | 一键操作 |
| 离线使用 | 实时 webcam |
| 高端显卡必需 | CPU 也可运行 |

### 9.2 技术亮点

1. 一键操作：选照片 + 点 Live
2. 单张照片输入，不需要训练流程
3. 实时预览：10–30 秒出效果
4. 覆盖 NVIDIA / AMD / Apple / Intel / CPU
5. 直播、视频、图片三种模式
6. 开源可定制：CLI 和二次开发都支持

### 9.3 注意事项

| 注意事项 | 说明 |
|----------|------|
| 道德使用 | 仅用于正当目的 |
| 隐私保护 | 使用真人脸需获得授权 |
| 合规标注 | 分享时标注为深度伪造 |

---

**相关话题标签**

#Deep-Live-Cam #实时换脸 #深度伪造 #Deepfake #AI 视频 # webcam

**来源**

- GitHub：https://github.com/hacksider/Deep-Live-Cam

---

*Deep-Live-Cam 由 hacksider 开发，采用 AGPL-3.0 许可证。请负责任地使用此工具。*
