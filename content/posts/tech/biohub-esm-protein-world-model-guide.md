---
title: "Biohub/esm：蛋白质世界的世界模型，从序列预测到药物设计"
date: "2026-05-30T03:05:00+08:00"
slug: "biohub-esm-protein-world-model-guide"
description: "Biohub发布的esm是一个蛋白质生物学世界模型，包含ESMC语言模型、ESMFold2结构预测和ESM Atlas（10亿级蛋白质结构图谱）。本文深入解析其核心架构、三大组件协同机制及在蛋白质设计中的应用边界。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "蛋白质", "世界模型", "结构预测", "药物设计", "开源"]
---

# Biohub/esm：蛋白质世界的世界模型，从序列预测到药物设计

## 一句话判断

esm不只是又一个蛋白质预测模型——它构建了一套从序列理解到结构预测再到功能解释的完整科学推理链，ESMFold2在多个指标上已可比肩甚至超越AlphaFold3，而ESM Atlas则第一次把「世界模型」的概念真正落实到了生物学领域。

## 系统地图

esm不是一个单一模型，而是一套三层架构的科学引擎：

```
┌─────────────────────────────────────────────┐
│           ESM Atlas（10亿蛋白质地图）          │
│  稀疏自编码器(SAE) → 可解释特征 → 自然语言描述  │
├─────────────────────────────────────────────┤
│       ESMFold2（结构预测层）                  │
│  ESMC 6B embeddings + 扩散结构预测          │
├─────────────────────────────────────────────┤
│           ESMC（蛋白质语言模型）               │
│  30B参数语言模型，从20亿蛋白质序列学习         │
└─────────────────────────────────────────────┘
```

三者关系：ESMC是底层世界模型，学习了蛋白质序列背后的进化规律；ESMFold2在此基础上做结构预测；ESM Atlas则用稀疏自编码器把ESMC的内部表征「翻译」成人类可理解的生物学语言。

## 核心组件逐层解析

### ESMC：蛋白质语言模型

ESMC（Evolutionary Scale Modeling of the Cambrian）是一个30B参数的掩码语言模型，在约20亿条蛋白质序列上训练。与ESM2相比，ESMC提出了新的Scaling Frontier——随着模型规模增大，长程结构理解能力出现涌现（emergent）特性。

关键设计：

- **全序列掩码训练**：随机遮盖部分氨基酸，要求模型预测完整序列
- **多层表征输出**：默认只返回最后一层，但可通过`output_hidden_states=True`获取所有Transformer层的表征
- **两条推理路径**：本地Hugging Face运行（适合定制和微调）或Biohub云平台（开箱即用）

```python
from transformers import AutoModelForMaskedLM, AutoTokenizer

model = AutoModelForMaskedLM.from_pretrained("Biohub/ESMC-6B", device_map="auto").eval()
tokenizer = AutoTokenizer.from_pretrained("Biohub/ESMC-6B")

inputs = tokenizer(sequences, return_tensors="pt", padding=True)
inputs = {k: v.to(model.device) for k, v in inputs.items()}
with torch.inference_mode():
    output = model(**inputs)
```

官方文档明确说明PyPI包「即将发布」，当前需通过`pip install esm@git+https://github.com/Biohub/esm.git@c94ed8d`从GitHub安装。

### ESMFold2：融合语言模型的结构预测

ESMFold2是整个系统中工程化程度最高的组件。它以ESMC 6B的语言模型表征作为输入，结合扩散（diffusion）结构预测头部，直接从序列预测高分辨率全原子结构。

核心创新：

1. **单序列模式**：不需要MSA（多序列比对），速度比传统方法快一个数量级
2. **扩散采样**：通过优化后的扩散采样步数控制精度/速度权衡
3. **配体与修饰支持**：支持DNA、RNA、小分子配体输入，以及化学修饰（modification）

```python
from esm.models.esmfold2 import ESMFold2Model, StructurePredictionInput, ProteinInput
model = ESMFold2Model.from_pretrained("biohub/ESMFold2").cuda().eval()
spi = StructurePredictionInput(
    sequences=[ProteinInput(id="A", sequence=HHAI_SEQ)]
)
result = ESMFold2InputBuilder().fold(model, spi, num_loops=3, num_sampling_steps=50)
```

输出包含pLDDT（置信度）、pTM、ipTM等质量指标，可用于判断预测可信度。官方宣称在DockQ pass-rate等指标上「match or exceed AlphaFold3」，但该说法尚未有第三方独立评测广泛验证。

### ESM Atlas：世界模型的可解释性层

这是esm最具野心的部分。ESMC训练了30B参数的语言模型，但这些知识以神经表征形式储存在模型权重中，人类无法直接理解。Atlas项目通过**稀疏自编码器（SAE）**把这套表征分解为约16,000个可解释特征。

工作方式：

```
ESMC隐藏层表征 → 稀疏自编码器(SAE) → 离散特征激活 → Agent生成自然语言描述
```

每个特征对应一个生物学意义（如「此位置可能参与蛋白质相互作用」），由Agent pipeline映射到已知蛋白质数据库中的实体。这相当于为ESMC的「大脑」提供了一份可视化地图。

Atlas覆盖了超过10亿个蛋白质的结构预测数据，组织在Biohub平台上供查询。

## 任务流案例：设计一个蛋白质binder

以设计靶向某个蛋白质的结合肽（binder）为例，完整流程如下：

1. **输入目标序列**：将目标蛋白序列输入ESMFold2，选择单序列模式快速预测结构
2. **生成候选序列**：在ESMC表征空间中进行优化搜索，或直接使用ESMFold2的逆向设计（inversion）能力生成de novo minibinder序列
3. **结构验证**：将候选序列重新输入ESMFold2，确认能否正确折叠且结合界面合理
4. **功能预估**：通过ESM Atlas查询候选序列的表征特征，评估功能活性
5. **实验迭代**：在实验室合成并测试，依据结果调整序列

官方在5个治疗靶点上验证了此流程，声称hit rate和亲和力都达到可接受水平，但完整实验方案尚未公开发布。

## 能力边界与不确定性

### 已验证的能力

- 从头预测蛋白质结构（单序列模式，无需MSA）
- 蛋白质-配体复合物结构预测（DNA、RNA、小分子）
- 蛋白质语言模型表征提取（适合下游任务微调）
- 10亿级蛋白质结构/表征的可查询地图

### 尚未充分验证或存在局限的

- **性能对标声明**：官方称ESMFold2「match or exceed AlphaFold3」，但这是自测结果，第三方独立评测有限
- **binder设计实际效果**：官方展示了5个靶点的验证数据，但样本量小，泛化能力未知
- **计算资源门槛**：ESMC-6B和ESMFold2均需要大量GPU内存，本地运行门槛较高
- **生物安全边界**：项目包含Frontier Safety章节，但具体guardrails实现细节未完全公开

### 不能从这些指标推出的结论

- ESMFold2全面超越AlphaFold3（目前只有官方自测数据）
- 这套系统可以直接用于临床药物设计（目前仍在科研验证阶段）
- SAE特征解释完全准确（由Agent生成，存在幻觉可能）

## 适用人群与采用建议

**优先考虑使用的场景：**

- 需要快速从序列得到结构，且无本地MSA计算资源
- 在ESMC表征空间做下游任务（分类、聚类、功能预测）的研究团队
- 需要大规模蛋白质结构数据查询（通过Atlas）
- 蛋白质设计早期探索（binder、酶改造等）

**可以等等再上车的场景：**

- 需要经过充分验证的生产级结构预测管线（目前仍建议交叉对比AlphaFold2/3）
- 对可解释性有严格要求的监管场景（SAE特征的可靠性仍在研究中）
- 计算资源受限的中小团队

## 技术规格速览

| 组件 | 模型规模 | 输入 | 输出 |
|------|----------|------|------|
| ESMC | 6B参数（另有30B版本） | 蛋白质序列 | 隐藏层表征 |
| ESMFold2 | ESMC 6B + 扩散头 | 序列±配体 | 3D结构(cif/pdb) |
| ESM Atlas SAE | 层30/60各一套 | ESMC表征 | 16K可解释特征 |

许可证：MIT，可商用。

## 如何开始

**云平台（最快）：**

```python
pip install esm  # 即将发布PyPI，当前用git+...安装
from esm.sdk import esmc_client
model = esmc_client(model="esmc-600m-2024-12", url="https://biohub.ai", token="<your_token>")
```

**本地Hugging Face：**

```python
from transformers import AutoModelForMaskedLM, AutoTokenizer
model = AutoModelForMaskedLM.from_pretrained("Biohub/ESMC-6B", device_map="auto")
```

**官方资源：**

- GitHub：https://github.com/Biohub/esm
- 论文：https://biohub.ai/papers/esm_protein.pdf
- Atlas平台：https://biohub.ai/esm/protein/atlas
- 教程：https://github.com/Biohub/esm/tree/main/cookbook/tutorials