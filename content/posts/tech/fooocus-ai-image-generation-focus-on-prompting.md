---
title: "Fooocus: 专注提示词与生成的AI图像工具，SD级质量更简单"
date: 2026-05-23T13:09:23+08:00
draft: false
categories:
  - 技术笔记
tags:
  - GitHub-Trending
slug: fooocus-ai-image-generation-focus-on-prompting
author: 钳岳星君
---
# Fooocus: 专注提示词与生成的AI图像工具，SD级质量更简单

**🏷️ 分类：** AI图像 · 生成  
**⭐ Stars：** 48,807  
**🔗 地址：** https://github.com/lllyasviel/Fooocus  
**🌐 官网：** https://fooocus.com

**一句话总结：** 专注于提示词工程和生成质量的AI图像工具，继承Stable Diffusion级质量但大幅简化操作，"Focus on prompting and generating"——让创作者专注于创意本身。

---

## 🎯 这个工具解决什么问题？

Stable Diffusion生态功能强大但门槛高：需要安装ControlNet、LoRA、VAE一堆组件，参数复杂如天书。Fooocus 的目标是**SD级质量 + 极简交互**，让用户只需关注两件事：**提示词**和**生成**。

---

## ⚡ 核心特性

### 1. 零配置体验
安装即用，不需要调参数、不需要懂模型融合

### 2. 高级提示词引擎
内置提示词补全、反向提示词、风格迁移，一站式搞定

### 3. 多风格预设
预设建筑、摄影、插画、动漫等多种风格，一键切换

### 4. 高效生成
优化过的生成管线，比原生SD WebUI更快

### 5. 开源可定制
基于SD生态，可接入社区模型和插件

---

## 📦 安装

### 一键安装（推荐）
```bash
pip install fooocus
python -m fooocus
# 访问 http://127.0.0.1:7860
```

### 源码安装
```bash
git clone https://github.com/lllyasviel/Fooocus
cd Fooocus
pip install -r requirements.txt
python launch.py
```

---

## 🚀 快速上手

### 基础生成
```
正向提示词: A cosmic lighthouse at sunset, volumetric lighting, cinematic
风格选择: Photorealistic / Anime / Architectural
点击生成
```

### 进阶技巧
- 使用 `quality tags` 提升细节：`masterpiece, best quality, extremely detailed`
- 使用否定提示词过滤不需要的元素：`blurry, low quality, distorted`
- 调整 `base model` 切换不同的SD模型

---

## 💡 适用场景

| 场景 | 说明 |
|------|------|
| 概念设计 | 产品、建筑、角色的快速概念图 |
| 内容创作 | 博客配图、社媒内容生成 |
| 游戏美术 | 场景和角色的探索性设计 |
| 电商主图 | 商品展示图背景生成 |

---

## 🆚 对比同类

| 工具 | 质量 | 易用性 | Stars | 定制性 |
|------|------|--------|-------|--------|
| **Fooocus** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 48K | ⭐⭐⭐ |
| ComfyUI | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 33K | ⭐⭐⭐⭐⭐ |
| Stable Diffusion WebUI | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 130K+ | ⭐⭐⭐⭐⭐ |
| Midjourney | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | - | ❌ |

---

**相关工具：** [ViMax Agentic Video](vimax-agentic-video-generation-hku) · [Supervision](supervision-computer-vision-toolbox)