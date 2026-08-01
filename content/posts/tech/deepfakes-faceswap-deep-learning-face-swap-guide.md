---
title: "FaceSwap：全球最大的开源深度换脸引擎"
date: 2026-08-01T02:54:21+08:00
draft: false
categories: ["技术笔记"]
tags: ["FaceSwap", "深度学习", "换脸", "计算机视觉", "Python"]
description: "FaceSwap（deepfakes/faceswap）是 GitHub 上最知名的开源深度换脸项目，56k+ Stars，完整的 Extract-Train-convert 三步工作流，支持多种模型架构，附带 GUI 和 CLI 双模式，强调伦理使用。"
slug: deepfakes-faceswap-deep-learning-face-swap-guide

---

## 一句话判断

FaceSwap 是 "deepfakes" 这个词的源头项目——2017 年将深度换脸技术从学术界带到大众视野的开源实现。经过多年发展，它已从最初的实验性脚本成长为完整的 Extract → Train → Convert 三步工作流引擎，支持多种神经网络模型，附带 GUI，是学习深度学习图像处理不可绕过的参考实现。

## 项目概览

| 维度 | 数据 |
|------|------|
| 仓库 | deepfakes/faceswap |
| Stars | ~56,900 |
| Forks | ~13,500 |
| 语言 | Python |
| 许可证 | GPL-3.0 |
| 文档 | faceswap.readthedocs.io |

## 项目定位与伦理声明

FaceSwap 在 README 中用了大量篇幅阐述伦理立场，这在本类项目中极为少见。核心声明确立场如下：

- FaceSwap 不用于创建不当内容
- FaceSwap 不用于未经同意的换脸
- FaceSwap 不用于任何非法、不道德或可疑目的
- FaceSwap 的存在是为了实验和发现 AI 技术、社会或政治评论、电影制作以及其他伦理和合理用途

项目团队对不道德使用采取零容忍态度。这个伦理框架是理解项目维护方向的关键——所有功能设计都以"最大化学习和实验价值，最小化滥用潜力"为原则。

## 三步工作流

FaceSwap 的核心是 Extract → Train → Convert 流水线：

### 1. Extract（提取）

```bash
python faceswap.py extract
```

从 `src` 目录的原始照片/视频中提取人脸，输出到 `extract` 目录。这一步使用人脸检测模型定位和裁剪人脸区域。

### 2. Train（训练）

```bash
python faceswap.py train
```

从两个包含不同人脸的文件夹读取图片，训练一个换脸模型。模型保存在 `models` 目录。训练质量取决于训练数据的数量和多样性。

### 3. Convert（转换）

```bash
python faceswap.py convert
```

将训练好的模型应用到原始图片上，生成换脸后的结果到 `modified` 目录。

### GUI 模式

```bash
python faceswap.py gui
```

提供图形界面，降低命令行门槛。所有脚本都支持 `-h/--help` 查看完整参数。

## 环境要求

- Python（支持 Windows、Linux、macOS）
- 现代 NVIDIA GPU（CUDA 支持）获得最佳性能
- AMD GPU 通过 ROCm 支持（Linux）
- 也可在 CPU 上运行，但速度极慢

视频处理使用内置的 `tools.py effmpeg` 工具，或配合 ffmpeg 手动完成视频到图片的转换→处理→合回视频。

## 技术价值：学习意义

抛开换脸本身，FaceSwap 的代码库是学习以下技术的优质教材：

- **人脸检测与对齐**：多种检测器（如 dnn、mtcnn）和对齐策略
- **GAN 与自编码器**：多种模型架构（Original、Villain、Phaze-A 等）
- **训练策略**：mask 策略、loss 函数选择、学习率调度
- **图像后处理**：颜色调整、锐化、mask 混合
- **工程化**：多 GPU 训练、断点续训、可视化面板

## 社区与支持

- **Discord**：[discord.gg/FC54sYg](https://discord.gg/FC54sYg)（SFW 服务器，禁止不当内容）
- **论坛**：[faceswap.dev/forum](https://faceswap.dev/forum)
- **文档**：[faceswap.readthedocs.io](https://faceswap.readthedocs.io)

项目强调：通用支持问题请发到 Discord 或论坛，GitHub Issues 中的支持问题可能被直接关闭。

## 适用边界

**适合**：

- 学习深度学习图像处理和 GAN/自编码器的学生和研究者
- 电影/VFX 行业的合法换脸需求
- 社会评论、讽刺、艺术创作等合法表达场景
- 对计算机视觉 pipeline 工程化感兴趣的开发者

**不适合**：

- 未经他人同意的换脸（违反项目伦理声明）
- 任何违法或侵权用途
- 生产级实时换脸（FaceSwap 是离线处理，非实时）
- 无 GPU 的机器上的快速处理

## 相关链接

- 仓库：[github.com/deepfakes/faceswap](https://github.com/deepfakes/faceswap)
- 文档：[faceswap.readthedocs.io](https://faceswap.readthedocs.io)
- 论坛：[faceswap.dev/forum](https://faceswap.dev/forum)
- Discord：[discord.gg/FC54sYg](https://discord.gg/FC54sYg)
- 安装指南：仓库内 INSTALL.md
