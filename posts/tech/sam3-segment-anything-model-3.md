# SAM 3 (Segment Anything Model 3): Meta开源的第三代分割一切模型

**🏷️ 分类：** CV · 图像分割  
**⭐ Stars：** 10,061  
**🔗 地址：** https://github.com/facebookresearch/sam3  
**🌐 官网：** https://ai.meta.com/sam/

**一句话总结：** Meta发布的第三代"分割一切"模型，支持点云、3D场景、多模态分割，参数更少、速度更快、精度更高，进一步巩固了分割模型的基础地位。

---

## 🎯 这个工具解决什么问题？

图像分割是CV的核心任务，但传统方法需要大量标注数据、针对每个场景单独训练。SAM（Segment Anything Model）系列通过"分割一切"的概念，用单一模型处理任意图像的分割任务。SAM 3 在前两代基础上引入**3D和点云支持**，从2D图像正式迈向3D世界理解。

---

## ⚡ 核心特性

### 1. 3D分割能力
不仅支持2D图像，还能分割点云、3D mesh、NeRF场景

### 2. 多模态输入
文本描述、边界框、点、涂鸦均可作为分割提示

### 3. 更高效的架构
比SAM 2更轻量，推理速度提升50%+

### 4. 零样本泛化
未经特定训练就能分割训练时从未见过的物体类别

### 5. 开放的模型生态
提供预训练模型 + 权重下载 + 微调教程

---

## 📦 安装

```bash
pip install sam3
# 或
git clone https://github.com/facebookresearch/sam3
cd sam3 && pip install -e .
```

---

## 🚀 快速上手

### 2D图像分割
```python
from sam3 import SAM3

sam = SAM3(model_type="vit_h")
mask = sam.predict(image="photo.jpg", points=[[100, 200]], labels=[1])
```

### 3D点云分割
```python
from sam3 import SAM3PointCloud

sam_pc = SAM3PointCloud()
masks = sam_pc.predict(point_cloud="scene.ply", points=[[0.1, 0.2, 0.3]])
```

---

## 💡 适用场景

| 场景 | 说明 |
|------|------|
| 自动驾驶 | 实时分割道路场景、行人、车辆 |
| 医学影像 | CT/MRI器官和病灶分割 |
| AR/VR | 实时场景理解和物体分离 |
| 机器人抓取 | 视觉引导的精确抓取定位 |

---

## 🆚 SAM系列演进

| 版本 | 时间 | 核心突破 | 精度 |
|------|------|----------|------|
| SAM 1 | 2023 | 分割一切，零样本泛化 | ⭐⭐⭐⭐ |
| SAM 2 | 2024 | 视频分割，实时处理 | ⭐⭐⭐⭐⭐ |
| **SAM 3** | 2025 | 3D + 点云 + 多模态 | ⭐⭐⭐⭐⭐ |

---

## ⚠️ 注意事项

- 3D模型对显存要求较高（建议16GB+）
- 预训练权重较大，下载可能需要较长时间
- 点云分割需要特定格式（支持PLY、OFF等）

---

**相关工具：** [Supervision](supervision-computer-vision-toolbox) · [Fooocus](#)