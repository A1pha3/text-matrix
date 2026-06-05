+++
date = '2026-05-23T13:09:23+08:00'
draft = false
title = 'Fooocus：专注提示词与生成的 AI 图像工具'
slug = 'fooocus-ai-image-generation-focus-on-prompting'
description = 'Fooocus 是 lllyasviel 开源的 AI 图像生成工具，基于 Stable Diffusion 但专注于提示词与生成，把复杂参数隐藏到后台，降低上手门槛。'
categories = ['技术笔记']
+++
# Fooocus：专注提示词与生成的 AI 图像工具，SD 级质量更简单

**分类：** AI 图像 · 生成  
**Stars：** 48,807  
**地址：** https://github.com/lllyasviel/Fooocus  
**官网：** https://fooocus.com

Fooocus 的思路很直接：把 Stable Diffusion（SD）的质量保留下来，把操作复杂度砍掉。它不追求 ComfyUI 那种节点式工作流的灵活性，也不像 Midjourney 那样走闭源路线——它只做两件事：让你写好提示词，然后生成图像。安装完成就能出图，不需要先搞懂 ControlNet、LoRA、VAE 这些组件分别干什么。

如果你已经在用 SD WebUI 但被参数劝退，或者想给团队找一个零培训成本的开源图像生成工具，Fooocus 是目前最接近"打开就用"的选择。但如果你需要精确控制模型管线或自定义节点编排，ComfyUI 更适合你。

---

## 它到底简化了什么

SD 生态的问题不在功能少，而在门槛高。装完 WebUI 只是开始，接下来还有 ControlNet 的姿态控制、LoRA 的风格微调、VAE 的色彩还原——每一层都有自己的参数和兼容性要求。Fooocus 把这些都内置了，并且默认就配好了。你不需要知道它们存在，它们已经在后台工作了。

这个设计取舍是明确的：牺牲定制深度，换取生成效率。对于概念设计、社媒配图、电商主图这类场景，这个取舍是划算的。

---

## 核心特性

### 1. 零配置出图
安装后直接可用，内置模型和参数已经调好，不需要手动下载或配置额外组件。

### 2. 内置提示词引擎
自动补全提示词、处理反向提示词、应用风格预设。不需要背 `masterpiece, best quality` 这类质量标签，Fooocus 会在后台自动注入。

### 3. 多风格预设
内置建筑、摄影、插画、动漫等风格模板，一键切换，不需要调 LoRA 权重或修改采样参数。

### 4. 优化过的生成管线
相比原生 SD WebUI，生成速度更快，显存占用更低——对消费级显卡更友好。

### 5. 基于 SD 生态的开源架构
可以接入社区模型和插件，没有被锁死在封闭系统里。

---

## 一次完整生成流程

以"生成一张赛博朋克风格的城市夜景"为例，看看一次请求在 Fooocus 中经历了什么：

1. **输入提示词**：`cyberpunk city at night, neon lights, rain, cinematic lighting`
2. **选择风格**：从预设里选 `Cinematic`——Fooocus 会自动注入对应的质量标签和采样参数
3. **设置反向提示词**：`blurry, low resolution, distorted`——或者留空，让内置引擎补默认的负面词
4. **点击生成**：Fooocus 把提示词扩展、风格参数、反向提示词整合后送入 SD 模型，返回结果
5. **快速迭代**：不满意就改提示词、换风格，点击生成——没有其他需要调整的参数

整个过程里，用户只需要关心"画面里有什么"和"什么风格"。管线细节完全不暴露。

---

## 安装

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

## 提示词技巧

### 基础写法
```
正向提示词: A cosmic lighthouse at sunset, volumetric lighting, cinematic
风格选择: Photorealistic / Anime / Architectural
点击生成
```

### 进阶技巧
- 用质量标签提升细节：`masterpiece, best quality, extremely detailed`
- 用反向提示词排除不需要的元素：`blurry, low quality, distorted`
- 切换 base model 以适配不同风格的 SD 模型（写实、二次元等）

---

## 常见问题

**Q: 和 SD WebUI 有什么区别？**
Fooocus 内置了 ControlNet、LoRA 等组件并自动配置，WebUI 需要手动安装和调参。如果你需要精确控制每个组件的参数，用 WebUI；如果只想写提示词出图，用 Fooocus。

**Q: 显存不够怎么办？**
Fooocus 默认对消费级显卡做了优化，4 GB 显存就能跑。如果仍然 OOM（显存不足），可以在设置里降低分辨率或切换到更轻量的模型。

**Q: 能用自己的模型吗？**
可以。把模型文件放到 Fooocus 的 `models` 目录下，启动时选择即可。

---

## 适用场景

| 场景 | 说明 |
|------|------|
| 概念设计 | 产品、建筑、角色的快速概念图 |
| 内容创作 | 博客配图、社媒内容生成 |
| 游戏美术 | 场景和角色的探索性设计 |
| 电商主图 | 商品展示图背景生成 |

---

## 对比同类工具

| 工具 | 质量 | 易用性 | Stars | 定制性 |
|------|------|--------|-------|--------|
| **Fooocus** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 48K | ⭐⭐⭐ |
| ComfyUI | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 33K | ⭐⭐⭐⭐⭐ |
| Stable Diffusion WebUI | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 130K+ | ⭐⭐⭐⭐⭐ |
| Midjourney | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | - | ❌ |

---

## 什么时候该用 Fooocus

- 你或你的团队需要零培训成本的开源图像生成工具
- 主要用途是概念设计、配图生成、风格探索——不需要精细的管线控制
- 设备有限（消费级显卡），需要低显存占用的方案

## 什么时候不该用

- 你需要自定义 ControlNet 参数、编排多节点工作流——ComfyUI 更合适
- 你需要社区最丰富的插件和模型生态——SD WebUI 的生态更成熟
- 你需要商用级的批量生成和 API 集成——Midjourney 或 DALL·E 的 API 更稳定

---

**相关工具：** [ViMax Agentic Video](vimax-agentic-video-generation-hku) · [Supervision](supervision-computer-vision-toolbox)