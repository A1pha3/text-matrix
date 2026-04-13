+++
date = '2026-04-13T23:51:22+08:00'
draft = false
title = 'Transfer Learning：迁移学习全栈资源库'
+++

# Transfer Learning：迁移学习全栈资源库

**Transfer Learning**（迁移学习）是由王晋东（jindongwang）发起的"迁移学习全栈资源库"，涵盖论文、教程、代码、数据集、会议期刊等完整学术生态。被CVPR、 NeurIPS、IJCAI、IEEE TKDE等顶会顶刊广泛引用。

**核心统计：**
- Stars: 14.3k | Forks: 3.8k | Watchers: 332
- Contributors: 38 | Deployments: 500+
- License: MIT
- 语言: Python 86.4% | MATLAB 4.1% | Jupyter 3.5%
- 最新提交: Feb 10, 2026 (2 months ago)

## 为什么这是迁移学习必读资源？

### 1. 覆盖18个研究领域

从传统方法到深度学习，从理论到实践：

| 领域 | 说明 |
|------|------|
| Survey | 综述文章汇总 |
| Theory | 理论基础 |
| Pre-training/Finetuning | 预训练与微调 |
| Knowledge Distillation | 知识蒸馏 |
| Traditional Domain Adaptation | 传统域适应 |
| Deep Domain Adaptation | 深度域适应 |
| Domain Generalization | 领域泛化 |
| Source-free Domain Adaptation | 无源域域适应 |
| Multi-source Domain Adaptation | 多源域适应 |
| Heterogeneous Transfer Learning | 异构迁移学习 |
| Online Transfer Learning | 在线迁移学习 |
| Zero-shot/Few-shot Learning | 零样本/少样本学习 |
| Multi-task Learning | 多任务学习 |
| Transfer Reinforcement Learning | 迁移强化学习 |
| Transfer Metric Learning | 迁移度量学习 |
| Federated Transfer Learning | 联邦迁移学习 |
| Lifelong Transfer Learning | 终身迁移学习 |
| Safe Transfer Learning | 安全迁移学习 |

### 2. 顶会顶刊广泛引用

- **会议**: CVPR'22, NeurIPS'21, IJCAI'21, ESEC/FWE'20, IJCNN'20, ACM MM'18, ICME'19
- **期刊**: IEEE TKDE, ACM TIST, Information Sciences, Neurocomputing, IEEE TCDS

### 3. 完整的学习路径

**Books (书籍):**
- 《Introduction to Transfer Learning: Algorithms and Practice》- Springer 2021
- 《迁移学习》（杨强）- 中文经典
- 《迁移学习导论》（王晋东、陈益强）

**Video Tutorials (视频教程):**
- B站《迁移学习》系列（中文）
- Hung-yi Lee @ NTU 课程
- Recent Advances of Transfer Learning 2022

## 研究领域详解

### Domain Adaptation (领域自适应)

核心问题：源域有标签、目标域无标签，如何迁移知识。

**传统方法:**
- TCA (Transfer Component Analysis)
- JDA (Joint Distribution Adaptation)
- CORAL (Correlation Alignment)

**深度方法:**
- DANN (Domain-Adversarial Neural Network)
- MCD (Maximum Classifier Discrepancy)
- CDAN (Conditional Adversarial Domain Adaptation)

### Domain Generalization (领域泛化)

无需目标域数据，模型泛化到未知域。

**最新Survey:** IJCAI-21 第一篇Domain Generalization综述

### Knowledge Distillation

知识蒸馏综述：2020年最新Survey

### Federated Transfer Learning

联邦迁移学习：隐私保护下的迁移学习

## 代码库 (Code)

**统一代码基线:**

| 代码库 | 说明 |
|--------|------|
| DeepDA | 深度域适应统一代码 |
| DeepDG | 深度域泛化统一代码 |

```bash
# GitHub Codespaces直接运行
https://github.dev/jindongwang/transferlearning

# 或Google Colab
https://colab.research.google.com/drive/1MVuk95mMg4ecGyUAIG94vedF81HtWQAr
```

**PyTorch微调教程:**
```python
import torchvision.models as models

# 加载预训练模型
model = models.resnet50(pretrained=True)

# 修改最后一层适应新任务
num_ftrs = model.fc.in_features
model.fc = nn.Linear(num_ftrs, num_classes)

# 微调
for param in model.parameters():
    param.requires_grad = False
for param in model.fc.parameters():
    param.requires_grad = True
```

## 数据集与Benchmark

收录常用迁移学习数据集及论文结果：

- Office-Home (4个域)
- VisDA (合成→真实)
- DomainNet (6个域)
- DIGITS
- USPS→MNIST

## 相关项目扩展

| 项目 | 说明 |
|------|------|
| llm-eval | 大语言模型评测 |
| llm-enhance | 大语言模型增强 |
| promptbench | LLM基准评测 |
| Semi-supervised Learning | 半监督学习 |
| Activity Recognition | 行为识别 |

## 理论 (Theory)

**经典论文:**
- ICML-20: Few-shot domain adaptation by causal mechanism transfer
- CVPR-19: Characterizing and Avoiding Negative Transfer
- NIPS-06: Analysis of Representations for Domain Adaptation
- ML-10: A Theory of Learning from Different Domains
- NIPS-08: Learning Bounds for Domain Adaptation
- COLT-09: Learning Bounds for Domain Adaptation

**MMD度量:**
- A Hilbert Space Embedding for Distributions
- Optimal Kernel Choice for Large-scale Two-sample Tests

## 著名学者

收录迁移学习领域的核心学者及其代表工作，详见 `doc/scholar_TL.md`

包括: 杨强(Qiang Yang)、Mingsheng Long (THU)、Sinno Jialin Pan等

## 应用领域

| 领域 | 说明 |
|------|------|
| Computer Vision | 视觉迁移 |
| Medical/Healthcare | 医疗健康 |
| NLP | 自然语言处理 |
| Time Series | 时序数据 |
| Speech | 语音 |
| Recommendation | 推荐系统 |
| Autonomous Driving | 自动驾驶 |

## 项目结构

```
transferlearning/
├── code/              # 统一代码库
│   ├── DeepDA/       # 深度域适应
│   └── DeepDG/       # 深度域泛化
├── data/             # 数据集与Benchmark
├── doc/              # 论文与文档
│   ├── awesome_paper.md
│   ├── scholar_TL.md
│   └── transfer_learning_application.md
├── notebooks/         # Jupyter教程
└── README.md
```

## 使用建议

**入门路径:**
1. 阅读Tutorials中的书籍和视频
2. 运行PyTorch微调教程
3. 在代码库中选择对应方法
4. 使用数据集进行实验

**研究路径:**
1. 阅读Survey了解各领域最新进展
2. 精读Theory论文理解理论基础
3. 复现state-of-the-art结果

## 引用

```bibtex
@Misc{transferlearning.xyz,
  howpublished = {\url{http://transferlearning.xyz}},
  title = {Everything about Transfer Learning and Domain Adaptation},
  author = {Wang, Jindong and others}
}
```

## 总结

Transfer Learning是迁移学习领域最全面的开源资源：

| 资源类型 | 内容 |
|----------|------|
| 论文 | 18个领域，覆盖1996-2024 |
| 教程 | 书籍+视频+B站+PPT |
| 代码 | 统一代码基线 |
| 数据集 | 常用Benchmark及结果 |
| 学者 | 领域核心研究者 |

无论是入门还是做研究，这都是不可替代的资源库。
