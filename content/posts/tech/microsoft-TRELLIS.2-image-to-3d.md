---
title: "TRELLIS.2：用 O-Voxel 把图像到 3D 生成推到 4B 参数级别"
date: 2026-08-02T02:59:48+08:00
slug: "microsoft-TRELLIS.2-image-to-3d"
description: "TRELLIS.2（microsoft/TRELLIS.2）是 Microsoft 推出的 4B 参数图像到 3D 生成模型，用 field-free 稀疏体素结构 O-Voxel 表达任意拓扑结构，支持 512³/1024³/1536³ 三档分辨率与 PBR 材质属性，并通过 Sparse 3D VAE 把资产压到紧凑潜空间。"
draft: false
categories: ["技术笔记"]
tags: ["3D 生成", "Image-to-3D", "Sparse Voxel", "DiT", "PBR"]
---

# TRELLIS.2：用 O-Voxel 把图像到 3D 生成推到 4B 参数级别

`microsoft/TRELLIS.2` 把"图像到 3D 生成"从传统 iso-surface 场的限制里拉了出来。核心贡献是 **O-Voxel**——一种"field-free"稀疏体素结构，配合 4B 参数的 vanilla DiT 和 Sparse 3D VAE（16× 下采样），让模型在 H100 上用约 3 秒生成 512³ 全纹理资产、17 秒生成 1024³、60 秒生成 1536³，并能原生表达开放表面、非流形几何和内含封闭结构。

## O-Voxel：不再被 iso-surface 束缚

传统 3D 生成普遍走 SDF / occupancy field，再 marching cubes 出 mesh。这种"field-based"路径有两个硬伤：

- **开放表面表达力差**——衣物、树叶会被强制闭合
- **非流形几何会塌陷**——薄壳、自相交结构

O-Voxel 是 **field-free sparse voxel**：每个体素直接携带"是否属于物体" + 几何 + 材质信息，跳过 iso-surface 中间层，自然能处理：

- ✅ Open surfaces（衣物、叶片）
- ✅ Non-manifold geometry
- ✅ Internal enclosed structures（空腔、内嵌零件）

## Sparse 3D VAE：16× 下采样

模型用的不是普通 3D VAE，而是 **Sparse 3D VAE with 16× spatial downsampling**，专为稀疏体素设计。效果是把 1024³ 的资产压到 ~64³ 的潜空间，再用 DiT 在潜空间里生成。

这条路线的代价是 VAE 必须做稀疏运算——普通 dense conv 在 1024³ 上显存直接爆。收益是：

- 潜空间紧凑 → DiT 训练和推理都在小张量上
- 解码端直接还原 1024³ 全纹理 mesh
- 单一 VAE 适配所有分辨率档位

## 完整 PBR 材质建模

TRELLIS.2 不只生成颜色，还建模完整的 PBR 属性：

- Base Color
- Roughness
- Metallic
- Opacity（支持半透明）

这意味着生成的资产可以直接送进 Blender / Unity / Unreal Engine 渲染，无需补材质。

## 性能档位（H100 GPU）

| 分辨率 | 总耗时 | 拆解（几何 + 材质） |
|--------|--------|-------------------|
| 512³ | ~3s | 2s + 1s |
| 1024³ | ~17s | 10s + 7s |
| 1536³ | ~60s | 35s + 25s |

数据流做到 "rendering-free + optimization-free"：纹理 mesh → O-Voxel 在单 CPU 上 < 10s；O-Voxel → 纹理 mesh 在 CUDA 上 < 100ms。

## 一次任务流：从单张图到可渲染资产

1. **输入**：单张 RGB 图（如一张咖啡杯照片）
2. **图像编码**：用图像编码器（DINOv2 / SigLIP 类视觉 encoder）拿到条件向量
3. **DiT 采样**：4B 参数的 vanilla DiT 在 O-Voxel 潜空间里采样，条件由图像特征注入
4. **Sparse 3D VAE 解码**：把潜空间解码回完整 O-Voxel（含 PBR 通道）
5. **O-Voxel → 纹理 mesh**：CUDA 加速的体素到 mesh 直接转换
6. **导出**：导出 GLB / OBJ / FBX，可直接拖进 Blender

整个流水线不需要 marching cubes 之前的中间场拟合，因此对开放结构 / 非流形几何天然友好。

## 适用边界

**适用场景：**

- 有 NVIDIA H100 / A100 工作站，想批量做 image-to-3D 的团队
- 需要 PBR 材质属性（不是单色 Lambert）的下游管线（游戏、电商、AR/VR）
- 对开放表面、薄壳、内嵌结构表达力有要求的场景（衣物、植物、机械内腔）

**不适用场景：**

- 没有 H100 级别显存：512³ 都需要显著 VRAM，更高分辨率需要 80GB+ A100 / H100
- 大场景重建（建筑级、城市级）：模型按单资产训练，跨资产拼接不是它的目标
- 实时交互生成：60s / 1536³ 的耗时决定它不能做实时预览
- 文字到 3D：仓库当前只放出了 image-to-3D 推理代码

## 与 Tripo / Meshy / CSM 的差异

| 维度 | TRELLIS.2 | Tripo / Meshy / CSM |
|------|-----------|---------------------|
| 表达力 | 任意拓扑、PBR | 多走 SDF + Lambert，材质粗糙 |
| 拓扑处理 | field-free O-Voxel | marching cubes 派生，开口受限 |
| 部署要求 | 4B 参数 + H100 | 通常 SaaS，本地部署受限 |
| 学术透明度 | 论文 + 推理代码 + 检查点齐 | 部分闭源 |
| PBR 材质 | 4 通道完整 | 通常只有 base color |

对做严肃 3D 资产生成的团队，TRELLIS.2 的真正价值不是"再快一点"，而是"终于敢生成带孔的衣物和内嵌机械结构了"。

## 路线图

仓库已勾选：

- [x] Paper release（[arxiv 2512.14692](https://arxiv.org/abs/2512.14692)）
- [x] Image-to-3D 推理代码
- [x] 4B 预训练检查点（[Hugging Face](https://huggingface.co/microsoft/TRELLIS.2-4B)）

下一步可关注 text-to-3D、更高分辨率、以及 O-Voxel 格式在 DCC 工具链里的原生支持。