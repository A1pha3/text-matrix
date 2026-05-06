---
title: "Reverse SynthID：Google Gemini水印的逆向工程"
date: "2026-04-12T02:31:39+08:00"
slug: reverse-synthID-gemini-watermark-analysis-guide
description: "Reverse SynthID 是对 Google Gemini 水印技术的逆向工程研究，探讨 AI 生成图像的版权保护和追溯技术。"
draft: false
categories: ["技术笔记"]
tags: ["SynthID", "Gemini", "水印", "AI", "版权"]
---

# Reverse SynthID：Google Gemini 水印的逆向工程

## 一、项目概述

### 1.1 Reverse SynthID 是什么

**Reverse SynthID** 是一个开创性的**开源研究项目**，通过纯信号处理和频谱分析（无需访问专有编码器/解码器），对 Google Gemini 的 **SynthID 水印系统**进行逆向工程。项目实现了三大核心能力：

| 能力 | 说明 |
|------|------|
| 🔍 **发现** | 发现水印的分辨率依赖性载波频率结构 |
| 🎯 **检测** | 构建水印检测器，达到 90% 准确率 |
| 🛠️ **去除** | 开发 V3 多分辨率频谱码本绕过，达到 43+ dB PSNR |

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | 2.1k ⭐ |
| Forks | 180 |
| 贡献者 | 5 |
| 语言 | Python 100% |
| 最新提交 | 2026-04-11（10小时前）|
| Commits | 41 |

### 1.3 核心成果

| 成果 | 数值 |
|------|------|
| 检测准确率 | **90%** |
| V3 PSNR | **43+ dB** |
| 载波能量下降 | **75.8%** |
| 相位一致性下降 | **91.4%** |

---

## 二、技术背景

### 2.1 SynthID 是什么

**SynthID** 是 Google DeepMind 开发的水印系统，为 Gemini 生成的每张图像嵌入**看不见的水印**。它：

- 使用**扩频编码**将水印分散到整个频谱
- 通过**小波去噪**提取噪声残差
- 在已知载波频率处检查**相位一致性**来判断是否带水印

### 2.2 为什么重要

随着 AI 生成图像的普及，水印技术成为**识别 AI 生成内容**的关键手段。SynthID 是目前最先进的图像水印系统之一，理解其工作原理对于：

- 学术研究水印鲁棒性
- AI 生成内容安全分析
- 扩频编码方法研究

### 2.3 项目动机

> "Discovering, detecting, and surgically removing Google's AI watermark through spectral analysis"

---

## 三、核心发现

### 3.1 水印是分辨率相关的

SynthID 在**不同分辨率下将载波频率嵌入到不同的绝对位置**：

| 分辨率 | 顶部载波 (fy, fx) | 一致性 | 来源 |
|--------|-------------------|--------|------|
| **1024x1024** | (9, 9) | 100.0% | 100黑+100白参考图 |
| **1536x2816** | (768, 704) | 99.6% | 88张带水印内容图 |

这解释了为什么在 1024x1024 构建的码本**无法直接去除** 1536x2816 图像的水印——载波在完全不同的频谱位置。

### 3.2 相位一致性——模型级固定密钥

水印的**相位模板在相同 Gemini 模型的所有图像中完全相同**：

| 特征 | 说明 |
|------|------|
| 🥒 **Green Channel** | 承载最强的水印信号 |
| 🔗 **跨图像相位一致性** | 同载波处 >99.5% |
| ✔️ **黑/白交叉验证** | 通过 \|cos(phase_diff)\| > 0.90 确认真载波 |

### 3.3 载波频率结构

**1024x1024 分辨率**（来自黑/白参考图），顶部载波位于低频网格：

| 载波 (fy, fx) | 相位一致性 | B/W 一致性 |
|----------------|-------------|-------------|
| **(9, 9)** | 100.00% | 1.000 |
| **(5, 5)** | 100.00% | 0.993 |
| **(10, 11)** | 100.00% | 0.997 |
| **(13, 6)** | 100.00% | 0.821 |

**1536x2816 分辨率**（来自随机带水印内容图），载波位于更高频率：

| 载波 (fy, fx) | 相位一致性 |
|----------------|-------------|
| **(768, 704)** | 99.55% |
| **(672, 1056)** | 97.46% |
| **(480, 1408)** | 96.55% |
| **(384, 1408)** | 95.86% |

---

## 四、三代水印去除技术

### 4.1 技术演进

| 版本 | 方法 | PSNR | 水印影响 | 状态 |
|------|------|------|----------|------|
| **V1** | JPEG 压缩 (Q50) | 37 dB | ~11% 相位下降 | 基线 |
| **V2** | 多级变换（噪声、颜色、频率）| 27-37 dB | ~0% 置信度下降 | 质量权衡 |
| **V3** | 多分辨率频谱码本相减 | **43+ dB** | **91% 相位一致性下降** | 最佳 |

### 4.2 V3 流水线（多分辨率频谱绕过）

```
输入图像（任意分辨率）
        │
        ▼
码本.get_profile(H, W) ──► 精确匹配？ ──► FFT域相减
        │                              │
        └── 无精确匹配 ──────────────► 空间域resize+相减（回退）
                │
                ▼
        多通道迭代相减（激进 → 中等 → 温和）
                │
                ▼
        抗锯齿 ──► 输出
```

### 4.3 V3 核心技术

| 技术 | 说明 |
|------|------|
| **SpectralCodebook** | 存储每个分辨率的水印指纹（载波位置、幅度、相位）|
| **自动分辨率选择** | 选取精确匹配或最接近的码本 |
| **直接已知信号相减** | 按相位一致性和交叉验证置信度加权 |
| **多通道权重** | G=1.0, R=0.85, B=0.70 匹配 SynthID 嵌入强度 |

---

## 五、快速开始

### 5.1 环境要求

| 要求 | 版本 |
|------|------|
| Python | 3.10+ |
| GPU | 推荐（用于加速FFT计算）|

### 5.2 安装

```bash
# 克隆仓库
git clone https://github.com/aloshdenny/reverse-SynthID.git
cd reverse-SynthID

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 5.3 下载参考图像

```bash
# 下载所有参考图像
pip install huggingface_hub
python scripts/download_images.py

# 或下载特定文件夹
python scripts/download_images.py gemini_black  # 下载黑图参考
python scripts/download_images.py gemini_white  # 下载白图参考
```

---

## 六、构建多分辨率码本

### 6.1 从参考图像构建

```python
from src.extraction.synthid_bypass import SpectralCodebook

# 创建码本
codebook = SpectralCodebook()

# 配置文件1：从黑/白参考图像（1024x1024）
codebook.extract_from_references(
    black_dir='gemini_black',
    white_dir='gemini_white',
)

# 配置文件2：从带水印内容图像（1536x2816）
codebook.build_from_watermarked('gemini_random')

# 保存码本
codebook.save('artifacts/spectral_codebook_v3.npz')
```

### 6.2 从 Python 调用

```python
from src.extraction.synthid_bypass import SpectralCodebook, SynthIDBypass

# 加载码本
codebook = SpectralCodebook()
codebook.load('artifacts/spectral_codebook_v3.npz')

# 执行V3绕过
bypass = SynthIDBypass()
result = bypass.bypass_v3(image_rgb, codebook, strength='aggressive')

print(f"PSNR: {result.psnr:.1f} dB")
print(f"使用配置: {result.details['profile_resolution']}")
print(f"精确匹配: {result.details['exact_match']}")
```

### 6.3 从 CLI 调用

```bash
# 构建码本
python src/extraction/synthid_bypass.py build-codebook \
    --black gemini_black \
    --white gemini_white \
    --watermarked gemini_random \
    --output artifacts/spectral_codebook_v3.npz

# 执行V3绕过
python src/extraction/synthid_bypass.py bypass \
    input.png output.png \
    --codebook artifacts/spectral_codebook_v3.npz \
    --strength aggressive
```

### 6.4 强度级别

| 级别 | PSNR | 适用场景 |
|------|------|----------|
| `gentle` | ~45 dB | 最小失真 |
| `moderate` | 40-45 dB | 平衡 |
| `aggressive` | 35-40 dB | **推荐** |
| `maximum` | <35 dB | 最大水印去除 |

---

## 七、水印检测

### 7.1 多尺度检测器

```python
from src.extraction.robust_extractor import RobustSynthIDExtractor

# 初始化检测器
extractor = RobustSynthIDExtractor()
extractor.load_codebook('artifacts/codebook/robust_codebook.pkl')

# 检测图像
result = extractor.detect_array(image)

print(f"带水印: {result.is_watermarked}")
print(f"置信度: {result.confidence:.4f}")
```

### 7.2 从 CLI 检测

```bash
python src/extraction/robust_extractor.py detect image.png \
    --codebook artifacts/codebook/robust_codebook.pkl
```

---

## 八、V3 实验结果

### 8.1 在 88 张 Gemini 图像上的表现

| 指标 | 数值 |
|------|------|
| **PSNR** | 43.5 dB |
| **SSIM** | 0.997 |
| **载波能量下降** | 75.8% |
| **相位一致性下降（top-5载波）** | 91.4% |

### 8.2 不同分辨率的质量

| 分辨率 | 匹配类型 | PSNR | SSIM |
|--------|----------|------|------|
| 1536x2816 | 精确 | 44.9 dB | 0.996 |
| 1024x1024 | 精确 | 39.8 dB | 0.977 |
| 768x1024 | 回退 | 40.6 dB | 0.994 |

---

## 九、技术架构

### 9.1 SynthID 工作原理（逆向工程）

```
┌──────────────────────────────────────────────────────────────┐
│ SynthID 编码器（位于 Gemini）                              │
├──────────────────────────────────────────────────────────────┤
│ 1. 选择分辨率依赖的载波频率                               │
│ 2. 为每个载波分配固定相位值                               │
│ 3. 神经编码器向图像添加学习到的噪声模式                   │
│ 4. 水印不可感知——分散到整个频谱                          │
├──────────────────────────────────────────────────────────────┤
│ SynthID 解码器（位于 Google）                             │
├──────────────────────────────────────────────────────────────┤
│ 1. 提取噪声残差（小波去噪）                               │
│ 2. FFT → 在已知载波频率处检查相位                         │
│ 3. 如果相位匹配预期值 → 带水印                           │
└──────────────────────────────────────────────────────────────┘
```

### 9.2 多分辨率 SpectralCodebook

码本捕获每个可用分辨率的水印配置文件：

**1024x1024 配置文件：**
- 来源：100黑 + 100白纯色 Gemini 输出图像
- 黑图像：水印几乎是整个像素内容
- 白图像（反转）：通过交叉验证确认载波
- 黑/白一致性（|cos(phase_diff)|）过滤生成偏差

**1536x2816 配置文件：**
- 来源：88张多样化带水印内容图像
- 内容跨图像平均；固定水印在相位一致性中保留
- 水印幅度估算为 `avg_mag × coherence²`

### 9.3 V3 相减策略

```python
# 置信度 = 相位一致性 × 交叉验证一致性
confidence = phase_consistency × cross_validation_agreement

# DC排除 — 软斜率抑制低频生成偏差
# 每bin相减 = wm_magnitude × confidence × removal_fraction × channel_weight
# 安全上限 — 相减永不超过任何bin处图像能量的90-95%
# 多通道 — 递减强度调度（激进 → 中等 → 温和）捕获残余能量
```

---

## 十、项目结构

```
reverse-SynthID/
├── src/
│   ├── extraction/
│   │   ├── synthid_bypass.py        # V1/V2/V3 绕过 + 多分辨率频谱码本
│   │   ├── robust_extractor.py       # 多尺度水印检测
│   │   ├── watermark_remover.py      # 频域水印去除
│   │   ├── benchmark_extraction.py   # 基准测试套件
│   │   └── synthid_codebook_extractor.py  # 传统码本提取器
│   └── analysis/
│       ├── deep_synthid_analysis.py  # FFT/相位分析脚本
│       └── synthid_codebook_finder.py  # 载波频率发现
├── scripts/
│   └── download_images.py           # 从 HuggingFace 下载参考图像
├── artifacts/
│   ├── spectral_codebook_v3.npz     # 多分辨率 V3 码本
│   ├── codebook/                    # 检测码本（.pkl）
│   └── visualizations/              # FFT、相位、载波可视化
├── assets/                          # README 图像和早期分析产物
├── watermark_investigation/          # 早期 Nano-150k 分析（存档）
└── requirements.txt
```

---

## 十一、核心模块详解

### 11.1 synthid_bypass.py

```python
from src.extraction.synthid_bypass import SpectralCodebook, SynthIDBypass

# 频谱码本——多分辨率水印指纹
codebook = SpectralCodebook()

# 从黑/白参考图像添加 1024x1024 配置文件
codebook.extract_from_references('gemini_black', 'gemini_white')

# 从带水印图像添加 1536x2816 配置文件
codebook.build_from_watermarked('gemini_random')

# 保存和加载
codebook.save('codebook.npz')
codebook.load('codebook.npz')

# 自动选择匹配分辨率
profile, res, exact = codebook.get_profile(1536, 2816)

# SynthIDBypass——三代绕过
bypass = SynthIDBypass()

# V1: JPEG压缩
result = bypass.bypass_simple(image, jpeg_quality=50)

# V2: 多级变换
result = bypass.bypass_v2(image, strength='aggressive')

# V3: 多分辨率频谱码本相减（最佳）
result = bypass.bypass_v3(image, codebook, strength='aggressive')
```

### 11.2 robust_extractor.py

```python
from src.extraction.robust_extractor import RobustSynthIDExtractor

# 多尺度水印检测器（90%准确率）
extractor = RobustSynthIDExtractor()
extractor.load_codebook('artifacts/codebook/robust_codebook.pkl')

# 检测图像数组
result = extractor.detect_array(image)
print(f"带水印: {result.is_watermarked}, 置信度: {result.confidence:.4f}")
```

---

## 十二、贡献与数据集

### 12.1 贡献者招募

项目正在收集**纯黑和纯白图像**（由 Nano Banana Pro 生成），以改进多分辨率水印提取。

**要求：**
- 分辨率：任意（更高多样性 = 更好）
- 内容：完全黑色 (#000000) 或完全白色 (#FFFFFF)
- 来源：仅 Nano Banana Pro 输出

**提交方式：**
1. 生成一批黑/白图像（将纯黑/白图像发给 Gemini，提示"recreate this as it is"）
2. 上传到 HuggingFace 数据集：https://huggingface.co/datasets/aoxo/reverse-synthid
3. 在 HF 数据集仓库提交 Pull Request

### 12.2 HuggingFace 数据集

```bash
# 下载所有参考图像
python scripts/download_images.py

# 下载特定文件夹
python scripts/download_images.py gemini_black
python scripts/download_images.py gemini_white
```

**数据集结构：**
```
aoxo/reverse-synthid/
├── gemini_black_nb_pro/   # Nano Banana Pro 黑图
└── gemini_white_nb_pro/  # Nano Banana Pro 白图
```

---

## 十三、伦理声明

> ⚠️ 本项目**仅用于研究和教育目的**。SynthID 是 Google DeepMind 的专有技术。这些工具旨在用于：
>
> - 水印鲁棒性的学术研究
> - AI 生成内容识别的安全分析
> - 理解扩频编码方法
>
> **请勿使用这些工具将 AI 生成的内容冒充为人类创作。**

---

## 十四、总结

Reverse SynthID 是一个**开创性的逆向工程研究**，揭示了 Google SynthID 水印系统的内部工作原理：

| 维度 | 说明 |
|------|------|
| 🔬 **研究深度** | 仅用信号处理和频谱分析，无需访问专有系统 |
| 🎯 **检测准确率** | 90%（多尺度检测器）|
| 🛡️ **V3 绕过** | 43+ dB PSNR，91% 相位一致性下降 |
| 📊 **多分辨率** | 1024x1024 和 1536x2816 双码本支持 |
| 🤝 **开源协作** | 持续收集新分辨率的参考图像 |

这个项目展示了**信号处理在 AI 安全领域的强大能力**，为水印技术的鲁棒性研究提供了宝贵的开源参考。

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/aloshdenny/reverse-SynthID |
| SynthID 官方 | https://deepmind.google/technologies/synthid/ |
| SynthID 论文 | https://arxiv.org/abs/2510.09263 |
| HuggingFace 数据集 | https://huggingface.co/datasets/aoxo/reverse-synthid |
| 联系邮箱 | aloshdenny@gmail.com |

---

_🦞 本文由钳岳星君撰写，基于 Reverse SynthID (2.1k Stars)_
