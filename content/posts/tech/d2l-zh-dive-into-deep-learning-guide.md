---
title: "D2L-ZH 动手学深度学习：李沐团队开源教材解读"
date: "2026-04-12T02:31:39+08:00"
slug: d2l-zh-dive-into-deep-learning-guide
github_repo: "d2l-ai/d2l-zh"
description: "D2L-ZH（动手学深度学习）是李沐团队编写的开源深度学习教材，中英文版被 70 多个国家的 500 多所大学采用，提供 PyTorch、TensorFlow、MXNet、PaddlePaddle 四种框架实现。本文从定位、章节、配套资源、框架选择、环境配置到学习路径做完整解读。"
draft: false
categories: ["技术笔记"]
tags: ["深度学习", "PyTorch", "TensorFlow", "MXNet", "PaddlePaddle"]
---

《动手学深度学习》（Dive into Deep Learning，简称 D2L）解决的不是"看懂深度学习"，而是"把它跑起来"。书里每个概念都配了可运行的代码，改一个参数、看一次输出，公式和实现之间不再有断层。中文版仓库 d2l-zh 由李沐团队维护，截至 2026 年 8 月 GitHub 星标约 79.7k，中英文版被 70 多个国家的 500 多所大学用作教材或参考书。同一套章节内容，提供 PyTorch、TensorFlow、MXNet、PaddlePaddle 四种框架实现。

## 项目定位

D2L 的出发点写在仓库首页——"理解深度学习的最佳方法是学以致用"。这个定位把它和两类常见教材区分开：

| 教材类型 | 代表 | 强项 | 短板 |
|---------|------|------|------|
| 偏理论 | Goodfellow 等《Deep Learning》 | 数学严谨 | 代码缺位 |
| 偏工程 | 框架官方教程 | 代码齐全 | 跳过原理 |
| 两者兼顾 | D2L | 代码与公式一一对应 | 覆盖深度不如专著 |

D2L 用 Jupyter Notebook 承载可运行代码，用 LaTeX 排版数学推导，用 [discuss.d2l.ai](https://discuss.d2l.ai) 讨论区承接提问。三者互相补位：动手改代码验证公式，卡住时去讨论区找答案，读者从"看得懂"到"改得动"的路径是通的。

作者团队的构成决定了教材的两种视角。李沐 2023 年离开亚马逊，与导师 Alexander J. Smola 共同创办 BosonAI 投身基础大模型，此前任亚马逊资深首席科学家，是 MXNet 的主要作者之一；Smola 现任 Boson.ai CEO，此前是亚马逊副总裁、杰出科学家。Aston Zhang 是仓库最主要的维护者，来自亚马逊；Zachary C. Lipton 任教于卡内基梅隆大学。工业工程与学术理论在这里各占一头。

教材的推荐名单可在 [d2l-zh GitHub 首页](https://github.com/d2l-ai/d2l-zh) 查阅。学术界包括韩家炜（美国伊利诺伊大学香槟分校 Michael Aiken Chair 教授）、Bernhard Schölkopf（马普所智能系统院院长）、周志华（南京大学计算机科学与技术系主任）、张潼（香港科技大学教授）。工业界包括黄仁勋（NVIDIA 创始人兼 CEO）、余凯（地平线创始人兼 CEO）、漆远（复旦大学"浩清"教授、人工智能创新与产业研究院院长）、沈强（将门创投创始合伙人）。

版本方面，稳定版本为 v2.0.0，2022 年 12 月 8 日发布，对应人民邮电出版社 2023 年出版的纸质书《动手学深度学习（PyTorch 版）》。之后仓库持续提交勘误、跟进框架版本，但未发布新的版本号。需要最新内容看在线版，需要稳定快照用 v2.0.0 tag。

## 章节结构：从线性回归到 BERT 的 15 章

v2.0.0 共 15 章加一个附录，整体按"基础 → 卷积与循环 → 注意力与优化 → 应用"推进：

| 部分 | 章节 | 主题 |
|------|------|------|
| 一 | 1-5 | 基础：从线性回归到多层感知机 |
| 二 | 6-9 | 卷积与循环网络 |
| 三 | 10-12 | 注意力机制与优化算法 |
| 四 | 13-15 | 计算机视觉与自然语言处理应用 |
| 附录 | 16 | 深度学习工具 |

**第一部分：基础（第 1-5 章）**

第 1 章引言解释深度学习为什么在 2012 年后爆发，给出数据、算力、算法三个驱动因素。第 2 章预备知识覆盖张量运算、线性代数、微积分、概率论和 Pandas 基础，没有 ML 背景也能从这里跟上后续推导。第 3 章用线性回归和 Softmax 回归引入"模型 + 损失 + 优化器"的训练范式，这个模式贯穿全书。第 4 章多层感知机引入激活函数、反向传播、过拟合与 Dropout，把线性模型扩展到非线性。第 5 章深度学习计算讲层与块的组合、参数管理、延后初始化、GPU 计算，相当于一份框架使用手册。

**第二部分：卷积与循环网络（第 6-9 章）**

第 6 章卷积神经网络从互相关运算讲起，引入填充、步幅、池化、多输入多输出通道。第 7 章现代卷积网络按历史顺序介绍 AlexNet、VGG、NiN、GoogLeNet、ResNet、DenseNet。残差连接是这一章的核心——它解释了为什么网络能一路加深而不退化。第 8 章循环神经网络引入状态更新公式和沿时间反向传播（BPTT）。第 9 章现代循环网络讲 GRU、LSTM、双向 RNN、编码器-解码器架构和 Beam Search。

**第三部分：注意力与优化（第 10-12 章）**

第 10 章注意力机制从注意力评分函数讲到自注意力，再到 Transformer，是后续理解 BERT、GPT 的地基。第 11 章优化算法讲 SGD、小批量 SGD、Momentum、AdaGrad、RMSProp、Adam，学习率调度的必要性是这一章的主线。第 12 章计算性能讨论并行计算、异步计算、多 GPU 训练。

**第四部分：应用（第 13-15 章）**

第 13 章计算机视觉讲图像增广、微调、目标检测（边界框、锚框、SSD、R-CNN 系列）、语义分割、风格迁移，最后是两个 Kaggle 实战。第 14 章自然语言处理：预训练覆盖 Word2Vec、GloVe、子词嵌入、BERT，包括预训练数据集和预训练 BERT 的完整流程。第 15 章自然语言处理：应用讲情感分析、自然语言推断、微调 BERT 做下游任务。

第 16 章是附录"深度学习工具"，介绍 Jupyter Notebook、Amazon SageMaker、Amazon EC2 实例的使用、服务器与 GPU 的选型，以及如何为本书贡献内容。

## 配套资源：在线版、视频课、工具包

**在线版与历史版本**

中文第二版在线阅读地址为 [zh.d2l.ai](https://zh.d2l.ai)，第一版（已不再更新）在 [zh-v1.d2l.ai](https://zh-v1.d2l.ai)。英文版在 [d2l.ai](https://d2l.ai)，对应仓库 [d2l-en](https://github.com/d2l-ai/d2l-en)。

在线阅读页每个章节都提供 Notebook 下载，可导入 Colab 等在线环境直接运行，不用先装任何软件。每节末尾都有小结和练习——小结把该节讲透的内容压缩成几条要点，练习用来对照检查自己是否真的读懂了。中文版仓库整体以 Apache-2.0 协议开源，可自由使用和二次分发。

**视频课程**

加州大学伯克利分校 2019 年春学期的 STAT 157 课程（Introduction to Deep Learning）以本书为教材，课程地址在 [courses.d2l.ai/berkeley-stat-157](http://courses.d2l.ai/berkeley-stat-157/index.html)。中文版课件（含教学视频地址）在 [github.com/d2l-ai/berkeley-stat-157](https://github.com/d2l-ai/berkeley-stat-157) 的 `slides-zh` 目录下。这套视频对应的是较早版本，章节编号与 v2.0.0 不完全一致，看的时候留意一下即可。

**d2l 工具包**

教材配套一个 Python 工具包 `d2l`，封装了绘图、数据加载、训练循环等常用函数，让正文代码聚焦于模型本身而不是样板代码。安装方式：

```bash
# 从 PyPI 安装（教材 v2.0.0 对应的固定版本）
pip install d2l==0.17.6

# 或从源码安装（获取仓库最新代码）
git clone https://github.com/d2l-ai/d2l-zh.git
cd d2l-zh
pip install -e .
```

工具包按框架分成四个模块文件：`d2l/mxnet.py`、`d2l/paddle.py`、`d2l/tensorflow.py`、`d2l/torch.py`。日常使用时只导入对应框架的模块，并统一取名为 `d2l`，方便照着正文抄代码：

```python
from d2l import torch as d2l
# 或
from d2l import tensorflow as d2l
```

## 框架支持：同一份章节，四套实现

章节正文是框架无关的（数学推导、概念解释），代码实现同时提供 PyTorch、TensorFlow、MXNet、PaddlePaddle 四套。在线阅读页顶部可切换框架，GitHub 仓库中每个章节的 Notebook 按框架后缀区分。

PyTorch 是主打实现，章节最完整、测试最充分，也是纸质书选用的框架。下面是一个完整的 PyTorch 训练示例，能看到 d2l 工具包如何把训练循环压缩成一行调用：

```python
import torch
from d2l import torch as d2l

# 1. 加载数据：Fashion-MNIST 是教材常用的入门数据集
batch_size = 256
train_iter, test_iter = d2l.load_data_fashion_mnist(batch_size)

# 2. 定义模型：一个简单的 MLP
net = torch.nn.Sequential(
    torch.nn.Flatten(),
    torch.nn.Linear(784, 256),
    torch.nn.ReLU(),
    torch.nn.Linear(256, 10)
)

# 3. 初始化参数
def init_weights(m):
    if type(m) == torch.nn.Linear:
        torch.nn.init.normal_(m.weight, std=0.01)

net.apply(init_weights)

# 4. 定义损失和优化器
loss = torch.nn.CrossEntropyLoss(reduction='none')
trainer = torch.optim.SGD(net.parameters(), lr=0.1)

# 5. 训练：d2l.train_ch3 封装了 epoch 循环、绘图、测试集评估
num_epochs = 10
d2l.train_ch3(net, train_iter, test_iter, loss, num_epochs, trainer)
```

这段代码走完了一次完整任务流：`load_data_fashion_mnist` 负责下载数据集、切分训练与测试迭代器；`train_ch3` 内部调用 `train_epoch_ch3` 完成单个 epoch 的训练，每个 epoch 结束后计算测试集精度并绘制训练曲线。数据、模型、优化器三条线在这里汇合，正是第 3 章"模型 + 损失 + 优化器"范式的最小可运行版本。

需要注意，教材的部分代码片段省略了数据加载步骤，直接调用 `train_ch3` 会报 `NameError: train_iter is not defined`。先执行第 1 步拿到迭代器，再传入训练函数。

TensorFlow 实现的 API 风格类似，模型定义换成 `tf.keras.Sequential`，训练循环同样由 `d2l.train_ch3` 封装：

```python
import tensorflow as tf
from d2l import tensorflow as d2l

batch_size = 256
train_iter, test_iter = d2l.load_data_fashion_mnist(batch_size)

net = tf.keras.Sequential([
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(256, activation='relu'),
    tf.keras.layers.Dense(10)
])

loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
trainer = tf.keras.optimizers.SGD(learning_rate=0.1)

d2l.train_ch3(net, train_iter, test_iter, loss, 10, trainer)
```

MXNet 和 PaddlePaddle 的覆盖度不如前两者，部分章节可能只有 PyTorch 版本。四个框架的取舍可以这样看：

| 框架 | 覆盖完整度 | 适合哪类读者 |
|------|-----------|-------------|
| PyTorch | 最完整，正文与纸质书主推 | 多数人首选，也是当前研究与开源生态的主流 |
| TensorFlow | 完整 | 习惯 Keras、面向工业部署 |
| MXNet | 部分章节 | 已有 MXNet 技术栈的存量项目 |
| PaddlePaddle | 部分章节 | 使用国产框架与国内生态 |

选框架跟着用途走：要跟主流论文和开源生态，选 PyTorch；要落到已有 TensorFlow 的生产链路，再考虑 TensorFlow。MXNet 和 PaddlePaddle 覆盖度有限，学习阶段不是必选项。

## 环境配置：两条本地路径 + 云 GPU

官方只提供 conda 和 pip 两种本地安装方式，没有官方 Docker 镜像。网上流传的 Docker 方案是社区镜像，版本和教材不一定对得上。

**路径一：Miniconda（官方推荐）**

官方安装流程从 Miniconda 开始，测试环境是 Python 3.9：

```bash
# 创建并激活环境
conda create --name d2l python=3.9
conda activate d2l

# 安装 PyTorch（按官网选择对应 CUDA 版本）
pip install torch torchvision

# 安装 d2l 工具包（与教材 v2.0.0 配套的固定版本）
pip install d2l==0.17.6
```

**路径二：pip + venv（轻量替代）**

不想装 conda 的话，用系统 Python 建虚拟环境即可：

```bash
# 创建并激活虚拟环境
python -m venv d2l-env
source d2l-env/bin/activate  # Windows 用 .\d2l-env\Scripts\activate

# 安装依赖
pip install torch torchvision
pip install d2l==0.17.6 jupyterlab
```

**下载 Notebook 代码**

环境装完后，还需要教材的 Notebook 代码。可以从 [zh.d2l.ai](https://zh.d2l.ai) 每个章节页面下载，或直接拉取打包文件：

```bash
curl https://zh-v2.d2l.ai/d2l-zh-2.0.0.zip -o d2l-zh.zip
unzip d2l-zh.zip && rm d2l-zh.zip
cd pytorch  # 或 tensorflow / mxnet / paddle
jupyter notebook
```

**路径三：云 GPU（无本地 GPU 时）**

附录里详细介绍了 Amazon SageMaker 和 EC2 实例的使用。不用 AWS 的话，Google Colab、Kaggle Notebooks、AutoDL 等平台也能跑教材代码。注意 Colab 默认的 CUDA 版本可能与最新 PyTorch 不匹配，按报错提示降级 PyTorch 即可。

## 学习路径：5 周入门 + 进阶分流

以下是一个 5 周入门计划，适合每周投入 10-15 小时的读者。

读完的评判标准不是"翻过"，而是"重写得出来"。每章做两件事：先把代码亲手敲一遍、改参数观察结果，再合上书，把该章的核心公式和训练流程讲给自己听。把"看过"变成"会做"，远胜过逐节读完后却不动手。如果你的注意力主要在理解概念而不是搭环境，可以先靠在线阅读版本跑通代码，再回头补本地环境。

**第 1 周：基础（第 1-3 章）**

第 1 章快速浏览即可，重点放在第 2 章预备知识。对张量运算、广播机制、自动求导不熟的话，这一章得动手敲代码。第 3 章线性回归是全书训练范式的最小完整示例，理解"模型 → 损失 → 优化器 → 训练循环"四件套是后续所有章节的基础。

**第 2 周：从 MLP 到计算图（第 4-5 章）**

第 4 章引入激活函数和 Dropout，第 5 章讲框架的模块化设计。这两章的代码会反复出现在后续章节，值得花时间把 `nn.Sequential`、`nn.Module`、参数初始化、`.to(device)` 这些操作练熟。

**第 3 周：卷积网络（第 6-7 章）**

第 6 章是 CNN 基础，第 7 章是经典架构。学完第 7 章后，自己用 PyTorch 复现一个 ResNet-18 并在 CIFAR-10 上训练，能有效检验对残差连接的理解。

**第 4 周：循环网络与注意力（第 8-10 章）**

第 8-9 章是 RNN 基础，第 10 章注意力机制是理解后续 BERT、GPT 的关键。读 Transformer 时配合论文《Attention Is All You Need》，教材的代码实现能把论文里的公式映射到实际计算上。

**第 5 周：优化与应用（第 11-13 章）**

第 11 章优化算法对调参很有帮助，第 13 章计算机视觉的应用（目标检测、语义分割）能让你看到 CNN 在真实任务中的样子。第 14-15 章 NLP 部分按需学习，主要做 CV 可以跳过。

**进阶分流**

入门之后，按目标选择方向：

- **工程实践方向**：补第 12 章计算性能，学习多 GPU 训练、混合精度、分布式数据并行（DDP），再去看 Hugging Face Transformers 的源码。
- **论文复现方向**：从教材引用的原始论文入手，按"读论文 → 看教材实现 → 自己从头实现 → 对比官方实现"的循环训练。教材每章末尾的"讨论"部分会给出延伸阅读。
- **教学备课方向**：结合 STAT 157 的课件和作业，按自己的课程节奏重组章节。教材的 Jupyter Notebook 格式方便改造成课堂演示。

## 常见问题

**`pip install d2l` 装的版本和教材代码对不上**：PyPI 包发布频率低于教材代码更新。如果遇到 `AttributeError`，先确认是否装了固定版本 `pip install d2l==0.17.6`，仍不对就从源码安装：`pip install git+https://github.com/d2l-ai/d2l-zh.git`。

**`d2l.train_ch3` 报 `NameError: train_iter is not defined`**：代码片段省略了数据加载步骤。完整调用顺序是先执行 `train_iter, test_iter = d2l.load_data_fashion_mnist(batch_size)`，再把迭代器传入 `train_ch3`。

**`torch.cuda.is_available()` 返回 False**：依次排查：1）`nvidia-smi` 确认显卡正常；2）CUDA 版本与 PyTorch 安装命令匹配；3）`pip list | grep torch` 确认没有同时装 CPU 版和 GPU 版。

**Colab 上运行教材代码报 CUDA 相关错误**：在 Notebook 开头加 `!pip install -U torch torchvision` 让 PyTorch 自动适配 CUDA。仍报错则切换运行时为 CPU。

**MXNet 和 PaddlePaddle 章节不全**：这两个框架的覆盖度仍在补充中，部分章节只有 PyTorch 版本。必须用某个框架时，可参考 PyTorch 实现自行翻译。

**第一版和第二版的区别**：第二版（v2.0.0）新增了注意力机制、BERT、自然语言推断等内容，第一版已不再更新。直接读第二版。

## 进阶路径

教材覆盖深度学习的基础到中级内容，学完后按以下方向深入：

**Transformer 与大模型**：教材第 10、14 章是 Transformer 和 BERT 的入门，接下来读论文《Attention Is All You Need》、BERT 原论文、GPT 系列论文，然后上手 Hugging Face Transformers 库。大模型训练的工程细节看 Megatron-LM、DeepSpeed 的文档和源码。

**计算机视觉**：教材第 13 章讲了目标检测和语义分割的基础，进阶看 DETR、Mask R-CNN、Vision Transformer（ViT）的论文。代码实践从 mmdetection 或 Detectron2 入手。

**生成模型**：教材对生成模型覆盖较少（只有风格迁移）。想学扩散模型（Diffusion），从论文《Denoising Diffusion Probabilistic Models》开始，配合 Hugging Face Diffusers 库实践。GAN 部分可以看教材英文版的扩展章节。

**强化学习**：D2L 对强化学习覆盖有限，进阶看 Sutton & Barto 的《Reinforcement Learning: An Introduction》，以及 OpenAI Spinning Up 教程。

**系统与工程**：对深度学习系统本身感兴趣（而不是应用），看 MLSys（Machine Learning Systems）方向的内容，如 TVM、XLA、PyTorch 的分布式训练实现。CMU 10-414/10-714（Deep Learning Systems）课程是一个扎实的起点。

## 资源链接与引用

**官方网站**

- 中文第二版在线阅读：[zh.d2l.ai](https://zh.d2l.ai)
- 中文第一版（归档）：[zh-v1.d2l.ai](https://zh-v1.d2l.ai)
- 英文版：[d2l.ai](https://d2l.ai)
- 讨论区：[discuss.d2l.ai](https://discuss.d2l.ai)

**GitHub 仓库**

- 中文版：[github.com/d2l-ai/d2l-zh](https://github.com/d2l-ai/d2l-zh)
- 英文版：[github.com/d2l-ai/d2l-en](https://github.com/d2l-ai/d2l-en)
- STAT 157 课件：[github.com/d2l-ai/berkeley-stat-157](https://github.com/d2l-ai/berkeley-stat-157)

**引用格式**

```bibtex
@book{zhang2023dive,
  title={Dive into Deep Learning},
  author={Zhang, Aston and Lipton, Zachary C. and Li, Mu and Smola, Alexander J.},
  publisher={Cambridge University Press},
  note={\url{https://D2L.ai}},
  year={2023}
}
```

---
