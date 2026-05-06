---
title: "D2L-ZH动手学深度学习：77K Stars·全球500+高校教材·PyTorch/TensorFlow/JAX"
date: "2026-04-12T02:31:39+08:00"
slug: d2l-zh-dive-into-deep-learning-guide
description: "D2L-ZH（动手学深度学习）是李沐团队编写的经典教材，被全球 500+ 高校采用，覆盖 PyTorch、TensorFlow、JAX 三大框架。"
draft: false
categories: ["技术笔记"]
tags: ["深度学习", "PyTorch", "TensorFlow", "JAX", "李沐"]
---

# D2L-ZH 动手学深度学习：77K Stars·全球500+高校教材·李沐沐神团队·PyTorch/TensorFlow/JAX三大框架

## 一，项目概述

### 1.1 D2L-ZH 是什么

**D2L-ZH（动手学深度学习）**是 **D2L.ai** 项目的**中文翻译版**，由 **Aston Zhang**、**Zachary C. Lipton**、**Mu Li** 和 **Alexander J. Smola** 主编，是一本面向中文读者的**深度学习教材**。

> "理解深度学习的最佳方法是学以致用。"

**核心定位**：一本既能**运行**、又能**讨论**的中文深度学习教材。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | **77k** ⭐ |
| Forks | 12.2k |
| Watchers | 1.1k |
| 贡献者 | **244** |
| 最新版本 | **v2.0.0** (2022-12-08) |
| 许可证 | **Apache-2.0** |
| 语言 | Python 75.3%, HTML 12.1%, TeX 10.7% |

### 1.3 学术推荐

| 推荐人 | 身份 |
|--------|------|
| **韩家炜** | ACM院士、IEEE院士，伊利诺伊大学香槟分校教授 |
| **Bernhard Schölkopf** | ACM院士，德国马克斯·普朗克研究所所长 |
| **周志华** | ACM院士、IEEE院士、AAAS院士，南京大学计算机系主任 |
| **张潼** | ASA院士、IMS院士，香港科技大学教授 |

### 1.4 工业推荐

| 推荐人 | 身份 |
|--------|------|
| **黄仁勋** | NVIDIA 创始人 & CEO |
| **余凯** | 地平线公司 创始人 & CEO |
| **漆远** | 复旦大学"浩清"教授 |

## 二，教材内容

### 2.1 章节结构

```
┌─────────────────────────────────────────────────────────────┐
│                    D2L-ZH 教材章节                                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   第一部分：基础                                                    │
│   ├── 第1章：引言                                                  │
│   ├── 第2章：预备知识                                              │
│   ├── 第3章：线性神经网络                                          │
│   ├── 第4章：多层感知机                                            │
│   └── 第5章：深度学习计算                                          │
│                                                               │
│   第二部分：计算机视觉                                              │
│   ├── 第6章：卷积神经网络                                         │
│   ├── 第7章：现代卷积神经网络                                      │
│   └── 第8章：计算机视觉                                           │
│                                                               │
│   第三部分：自然语言处理                                            │
│   ├── 第9章：循环神经网络                                         │
│   ├── 第10章：现代循环神经网络                                    │
│   ├── 第11章：注意力机制                                         │
│   └── 第12章：自然语言处理应用                                    │
│                                                               │
│   第四部分：扩展主题                                               │
│   ├── 第13章：优化算法                                            │
│   ├── 第14章：计算性能                                            │
│   ├── 第15章：计算机视觉的蹭点                                  │
│   └── 第16章：NLP预训练                                           │
│                                                               │
│   附录                                                          │
│   ├── 工具安装                                                   │
│   ├── 使用 Jupyter Notebook                                       │
│   └── 深度学习工具                                                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 每章内容

| 章节 | 主题 | 核心内容 |
|------|------|----------|
| 第1章 | 引言 | 深度学习概述、应用场景 |
| 第2章 | 预备知识 | Python、Jupyter、线性代数、概率论 |
| 第3章 | 线性神经网络 | 线性回归、Softmax 回归 |
| 第4章 | 多层感知机 | MLP、过拟合、正则化 |
| 第5章 | 深度学习计算 | 层、参数、延后初始化、GPU |
| 第6章 | 卷积神经网络 | 卷积、池化、填充、步幅 |
| 第7章 | 现代 CNN | VGG、NiN、GoogLeNet、ResNet |
| 第8章 | 计算机视觉 | 目标检测、语义分割、样式迁移 |
| 第9章 | 循环神经网络 | RNN、GRU、LSTM |
| 第10章 | 现代 RNN | 编码器-解码器架构、Beam Search |
| 第11章 | 注意力机制 | Transformer、BERT、GPT |
| 第12章 | NLP 应用 | 文本分类、词向量、机器翻译 |
| 第13章 | 优化算法 | SGD、Momentum、Adam |
| 第14章 | 计算性能 | 并行、异步、GPU、TPU |
| 第15章 | CV 技巧 | 数据增强、微调、目标检测 |
| 第16章 | NLP 预训练 | Word2Vec、ELMo、BERT、GPT |

## 三，配套资源

### 3.1 在线资源

| 资源 | 链接 |
|------|------|
| **中文官网 (v2)** | https://zh.d2l.ai |
| **中文官网 (v1)** | https://zh-v1.d2l.ai |
| **英文官网** | https://d2l.ai |
| **英文版 GitHub** | https://github.com/d2l-ai/d2l-en |

### 3.2 视频课程

| 课程 | 来源 | 说明 |
|------|------|------|
| **UC Berkeley STAT 157** | 2019 春 | 深度学习导论课程 |
| **中文课件** | GitHub | 含教学视频地址的中文版课件 |

### 3.3 工具包

```bash
# 安装 D2L 工具包
pip install d2l

# 或从源码安装
git clone https://github.com/d2l-ai/d2l-zh.git
cd d2l-zh/d2l
pip install -e .
```

## 四，环境配置

### 4.1 Python 环境

```bash
# 创建虚拟环境
python -m venv d2l
source d2l/bin/activate  # Linux/macOS
# or
.\d2l\Scripts\activate   # Windows

# 安装 PyTorch
pip install torch torchvision

# 安装 D2L
pip install d2l
```

### 4.2 Jupyter Notebook

```bash
# 安装 Jupyter
pip install jupyterlab

# 启动 Jupyter
jupyter notebook
```

### 4.3 GPU 环境 (CUDA)

```bash
# 确认 CUDA 版本
nvcc --version

# 安装 PyTorch GPU 版本
pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cu118
```

### 4.4 Docker

```bash
# 拉取镜像
docker pull d2lai/d2l-zh

# 运行容器
docker run -it d2lai/d2l-zh
```

## 五，代码结构

### 5.1 D2L 工具包结构

```
d2l/
├── __init__.py           # 包初始化
├── data/                # 数据集
│   ├── __init__.py
│   ├── data_loader.py   # 数据加载
│   └── transforms.py    # 数据增强
├── functions/           # 核心函数
│   ├── __init__.py
│   ├── plt.py          # 绘图函数
│   ├── train.py        # 训练函数
│   └── utils.py        # 工具函数
├── nn/                 # 神经网络模块
│   ├── __init__.py
│   ├── sequential.py   # 顺序容器
│   ├── linear.py       # 线性层
│   ├── conv.py         # 卷积层
│   └── rnn.py          # 循环层
└── optim/              # 优化器
    ├── __init__.py
    ├── sgd.py         # SGD
    ├── adam.py         # Adam
    └── lr_scheduler.py # 学习率调度
```

### 5.2 常用函数

```python
from d2l import torch as d2l

# 绘制图像
d2l.use_svg_display()
d2l.plt.plot(x, y)

# 数据加载
data_iter = d2l.load_data_fashion_mnist(batch_size)

# 训练
d2l.train_ch3(model, data_iter, loss, trainer)
```

## 六，框架支持

### 6.1 支持的框架

| 框架 | 说明 |
|------|------|
| **PyTorch** | 主打框架，最完整实现 |
| **TensorFlow** | 官方实现 |
| **JAX** | 实验性支持 |

### 6.2 PyTorch 实现

```python
import torch
from d2l import torch as d2l

# 定义模型
net = torch.nn.Sequential(
    torch.nn.Flatten(),
    torch.nn.Linear(784, 256),
    torch.nn.ReLU(),
    torch.nn.Linear(256, 10)
)

# 初始化参数
def init_weights(m):
    if type(m) == torch.nn.Linear:
        torch.nn.init.normal_(m.weight, std=0.01)

net.apply(init_weights)

# 训练
loss = torch.nn.CrossEntropyLoss()
trainer = torch.optim.SGD(net.parameters(), lr=0.1)

d2l.train_ch3(net, train_iter, test_iter, loss, 10, trainer)
```

### 6.3 TensorFlow 实现

```python
import tensorflow as tf
from d2l import tensorflow as d2l

# 定义模型
net = tf.keras.Sequential([
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(256, activation='relu'),
    tf.keras.layers.Dense(10)
])

# 编译
net.compile(loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
            optimizer=tf.keras.optimizers.SGD(learning_rate=0.1))

# 训练
d2l.train_ch3(net, train_iter, test_iter,
               loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
               trainer=tf.keras.optimizers.SGD(learning_rate=0.1),
               epochs=10)
```

## 七，学习路径

### 7.1 入门路径

```
┌─────────────────────────────────────────────────────────────┐
│                    D2L-ZH 学习路径                                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   第一周：基础                                                    │
│   ├── 第1章：引言 (1天)                                          │
│   ├── 第2章：预备知识 (2天)                                      │
│   └── 第3章：线性神经网络 (4天)                                  │
│                                                               │
│   第二周：神经网络基础                                            │
│   ├── 第4章：多层感知机 (3天)                                    │
│   └── 第5章：深度学习计算 (4天)                                  │
│                                                               │
│   第三周：计算机视觉                                              │
│   ├── 第6章：卷积神经网络 (3天)                                 │
│   └── 第7章：现代卷积神经网络 (4天)                             │
│                                                               │
│   第四周：自然语言处理                                           │
│   ├── 第9章：循环神经网络 (3天)                                 │
│   └── 第10-11章：注意力机制 (4天)                               │
│                                                               │
│   第五周：进阶主题                                               │
│   ├── 第13章：优化算法 (2天)                                    │
│   └── 第14章：计算性能 (3天)                                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 核心概念速查

| 概念 | 章节 | 说明 |
|------|------|------|
| **梯度下降** | 第3章 | 优化算法基础 |
| **激活函数** | 第4章 | ReLU、Sigmoid、Tanh |
| **Dropout** | 第4章 | 正则化技术 |
| **卷积** | 第6章 | 图像特征提取 |
| **残差连接** | 第7章 | ResNet 核心 |
| **注意力** | 第11章 | Transformer 基础 |
| **BERT** | 第16章 | 预训练语言模型 |

## 八，资源链接

### 8.1 官方网站

| 资源 | 链接 |
|------|------|
| **中文官网 v2** | https://zh.d2l.ai |
| **中文官网 v1** | https://zh-v1.d2l.ai |
| **英文官网** | https://d2l.ai |
| **讨论区** | https://discuss.d2l.ai |

### 8.2 GitHub 仓库

| 仓库 | 说明 |
|------|------|
| **d2l-zh** | 本仓库 (中文版) |
| **d2l-en** | 英文版 |
| **d2l-zh-pytorch** | PyTorch 版 |
| **d2l-zh-tensorflow** | TensorFlow 版 |

### 8.3 引用

```bibtex
@book{zhang2023dive,
  title={Dive into Deep Learning},
  author={Zhang, Aston and Lipton, Zachary C. and Li, Mu and Smola, Alexander J.},
  publisher={Cambridge University Press},
  note={\url{https://D2L.ai}},
  year={2023}
}
```

## 九，总结

D2L-ZH 是**全球最受欢迎的深度学习教材之一**：

| 维度 | 说明 |
|------|------|
| 📚 **内容全面** | 16 章节覆盖基础、CV、NLP、优化 |
| 💻 **代码丰富** | 每章配有可运行代码 |
| 🌍 **国际认可** | 70+ 国家 500+ 高校使用 |
| 🔧 **框架支持** | PyTorch、TensorFlow、JAX |
| 📖 **持续更新** | 244 位贡献者维护 |

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| 中文官网 | https://zh.d2l.ai |
| 英文版 | https://github.com/d2l-ai/d2l-en |
| 讨论区 | https://discuss.d2l.ai |

---

_🦞 本文由钳岳星君撰写，基于 D2L-ZH 动手学深度学习 (77k Stars)_
