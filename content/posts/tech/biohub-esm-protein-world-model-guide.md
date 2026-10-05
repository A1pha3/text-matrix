---
title: "Biohub/esm：蛋白质世界的世界模型，从序列预测到药物设计"
date: "2026-05-30T03:05:00+08:00"
lastmod: "2026-10-02T00:00:00+08:00"
slug: "biohub-esm-protein-world-model-guide"
github_repo: "Biohub/esm"
source_key: "gh:Biohub/esm"
description: "Chan Zuckerberg Biohub 发布的 esm 是一套蛋白质生物学世界模型，包含 ESMC 蛋白质语言模型、ESMFold2 结构预测和 ESM Atlas（覆盖 68 亿序列与 11 亿个预测结构的可解释图谱）。本文解析其三层架构、组件间的协同机制，以及它在蛋白质设计中的适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["世界模型", "开源"]
---

> **快速信息卡**
> - **GitHub**: [Biohub/esm](https://github.com/Biohub/esm)（原 EvolutionaryScale 团队，现归属 Chan Zuckerberg Biohub）
> - **Stars / Forks**: 2,980 / 397（GitHub API 2026-10-02 核实，快速波动以仓库实时为准）
> - **License**: 仓库 LICENSE.md 为标准 MIT（版权 Chan Zuckerberg Biohub, Inc.）；GitHub 页面的许可识别显示为 Other/NOASSERTION，商用前以 LICENSE.md 原文为准
> - **语言**: Python / Jupyter Notebook
> - **维护状态**: 活跃（最近推送 2026-09-16）；`esm` 包已发布到 PyPI（v3.4.post1），ESMC / ESMFold2 也已接入 Hugging Face Transformers（v5.16.0 起）

## 学习目标

读完后你应该能：

1. 说清 ESM 的三层架构（ESMC 语言模型、ESMFold2 结构预测、ESM Atlas 可解释层）和各层职责
2. 说明 ESMFold2 相比 AlphaFold3 的优势与局限，以及官方结论的证据强度
3. 解释 ESM Atlas 如何用稀疏自编码器把神经网络表征翻译成可读的生物学描述
4. 判断 ESM 在蛋白质设计任务中的适用边界（已验证能力 vs 尚未充分验证的）
5. 评估 ESM 是否适合你的场景，并知道从哪一步开始

## 目录

- [一句话判断](#一句话判断)
- [系统地图](#系统地图)
- [核心组件逐层解析](#核心组件逐层解析)
- [任务流案例：设计一个蛋白质 binder](#任务流案例设计一个蛋白质-binder)
- [能力边界与不确定性](#能力边界与不确定性)
- [适用人群与采用建议](#适用人群与采用建议)
- [技术规格速览](#技术规格速览)
- [如何开始](#如何开始)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [常见问题](#常见问题)
- [练习](#练习)
- [资料口径说明](#资料口径说明)

---

# Biohub/esm：蛋白质世界的世界模型

## 一句话判断

esm 不是单个预测模型，而是从序列理解到结构预测、再到功能解释的一条链路。ESMFold2 在蛋白质-蛋白质与抗体-抗原结合基准上展示出接近甚至超过 AlphaFold3 的成绩，ESM Atlas 让「世界模型」变成可检索的生物空间。这些结论目前主要来自官方发布与预印本，第三方独立复现有限。

## 系统地图

esm 由三层组件构成一个流水线，每一层解决一类问题：

```
┌───────────────────────────────────────────────┐
│     ESM Atlas（可搜索图谱）                    │
│     68 亿条序列 + 11 亿个预测结构               │
│     稀疏自编码器(SAE) → 可解释特征 → 自然语言描述 │
├───────────────────────────────────────────────┤
│     ESMFold2（结构预测层）                     │
│     在冻结的 ESMC-6B 表征上接扩散结构预测头       │
├───────────────────────────────────────────────┤
│     ESMC（蛋白质语言模型）                     │
│     300M / 600M / 6B 三档，在约 28 亿条序列上训练 │
└───────────────────────────────────────────────┘
```

三层关系：ESMC 是底层世界模型，学习序列背后的进化规律；ESMFold2 基于它的表征做结构预测；ESM Atlas 再用稀疏自编码器把 ESMC 的内部表征拆解成可解释特征并映射到已知数据库。

## 核心组件逐层解析

### ESMC：蛋白质语言模型

ESMC（ESM Cambrian）是一个掩码语言模型，训练目标是在遮住部分氨基酸后预测完整序列，上下文是进化留下的蛋白质序列，而不是自然语言句子。Biohub 给出的参数量三档为 300M、600M 与 6B，最大的是 6B 版本；训练集约 28.06 亿条覆盖全生命域的序列（UniRef 约 1.56 亿 + JGI 约 20.3 亿 + MGnify 约 6.2 亿）。与 ESM2 相比，ESMC 的核心论点是存在一条 Scaling Frontier：随着模型规模与训练计算量增大，长程结构与功能信息从表征中「浮现」出来的程度持续提升——预印本的拟合显示这一提升随计算量呈对数线性。

设计要点：

- **掩码训练**：随机遮盖约 15% 的氨基酸并要求模型恢复原残基，从而压缩折叠与功能的约束
- **多层表征输出**：默认只返回最后一层，可通过 `output_hidden_states=True` 取各 Transformer 层的表征；长程接触信息集中在最后约 40 层，倒数第二层附近达到峰值，这也是 Atlas 的 SAE 选在 layer 60（6B 共 80 层）的原因
- **两条推理路径**：本地运行（esm 包或 Hugging Face Transformers，便于定制与微调），或走 Biohub 云平台（开箱即用）

```python
import torch
from esm.models.esmc import EsmcForMaskedLM, EsmcTokenizer

model = EsmcForMaskedLM.from_pretrained("biohub/ESMC-6B", device="cuda").eval()
tokenizer = EsmcTokenizer()

inputs = tokenizer(sequences, return_tensors="pt", padding=True)
inputs = {k: v.to(model.device) for k, v in inputs.items()}
with torch.inference_mode():
    output = model(**inputs)
```

`esm` 已发布到 PyPI，直接 `pip install esm` 即可；ESMC、ESMFold2 也能通过 Hugging Face Transformers（v5.16.0 起，含 v5.16.1）用熟悉的 Transformers API 加载，方便嵌入现有 ML 工作流——官方给出的分工是：生产推理与长序列折叠用 esm 包（依赖与推理路径经过优化），快速实验与生态集成用 Transformers。使用 6B 模型前先确认 GPU 显存是否充足（见下文「能力边界」）。

### ESMFold2：融合语言模型的结构预测

ESMFold2 用 ESMC-6B 的表征作为输入，接一个扩散（diffusion）结构预测头，直接从序列产出原子分辨率的全原子结构。相比早期只支持蛋白单体的 ESMFold，它可以处理蛋白质、DNA、RNA、小分子配体以及带修饰的氨基酸组成的复合体系。

架构上，ESMC-6B 的权重保持冻结：全部 80 层表征先汇聚成单一表示，再投影成「成对表示」（pair state，描述任意两个残基间的关系），经 48 层循环折叠迭代更新（官方另有 24 层的 ESMFold2-Fast 变体），最后由全原子扩散变换器（带滑窗原子注意力）去噪出原子坐标。语言模型表征承担了大部分「生物学知识」，折叠头只负责几何实现——这也解释了它的速度与精度：在 Foldbench 上，单序列模式下抗体-抗原复合物的 DockQ 通过率为 50%（±2%），已高于依赖多序列比对（MSA）的 AlphaFold3 的 47%；补上 MSA 后蛋白质-蛋白质与抗体-抗原两项分别升到 76% 和 53%，两项都超过 AlphaFold3（73% 和 47%）。这些对标数字全部出自官方预印本（口径说明见文末）。

核心特性：

1. **单序列模式**：默认不需要 MSA（多序列比对），折叠一个 1024 残基的蛋白约 16 秒，官方称相对传统折叠管线有数量级的提速
2. **可选的 MSA 提升**：困难靶点上可补充 MSA 提升准确率
3. **推理时扩展**：多次扩散采样配合置信度打分，性能随算力单调上升——抗体-抗原通过率从单次采样的 49% 升到 1000 次采样的 65%
4. **长序列支持**：esm 包内置 Fold-CP 上下文并行，官方演示 4 张 H100 折叠 4k 残基、16 张折叠 6.5k 残基

```python
from esm.models.esmfold2 import (
    ESMFold2InputBuilder,
    EsmFold2Model,
    ProteinInput,
    StructurePredictionInput,
)

model = EsmFold2Model.from_pretrained("biohub/ESMFold2", device="cuda").eval()
spi = StructurePredictionInput(
    sequences=[ProteinInput(id="A", sequence=HHAI_SEQ)]
)
result = ESMFold2InputBuilder().fold(
    model, spi, num_loops=20, num_sampling_steps=100, num_diffusion_samples=1, seed=0
)
```

输出包含 pLDDT（置信度）、pTM、ipTM 等质量指标，用于判断预测可信度。AMD ROCm 用户需要 ROCm 6.4 配 PyTorch 2.9 以上。上述代码基于官方 README 的写法，具体 API 会随版本演进，以仓库文档为准。

### ESM Atlas：世界模型的可解释层

这是 esm 里最特别的部分。ESMC 把学到知识压缩进权重，人类无法直接读。Atlas 用**稀疏自编码器（SAE）**把 ESMC 的内部表征拆成约 1.6 万个可解释特征，再让自动化流程把这些特征与已知蛋白质数据库中的实体关联起来。

工作方式：

```
ESMC 隐藏层表征 → 稀疏自编码器(SAE) → 离散特征激活 → Agent 生成自然语言描述
```

Atlas 与预印本分析所用的 SAE 是 `ESMC-6B-sae-layer60-k64-codebook16384`：建在 6B 模型的第 60 层上，码本 16,384（2 的 14 次方）个特征，每个 token 只激活其中 64 个。官方同时开放了一个更大的 SAE 家族（覆盖所有层，维度从 2^13 到 2^17、稀疏度 8–128 不等），供研究者按粒度取用；仓库里还附带一份由 Agent 生成、人工可读的特征描述表。SAE 分两种形态，多数读取第 N 层隐藏态，部分读取相邻层残差更新（`h[N] - h[N-1]`），由各仓库 config 声明，主干模型会据此喂数。

每个特征对应一类可能的生物学意义（例如「此区域可能参与蛋白相互作用」）。Atlas 覆盖约 68 亿条序列，并以 70% 序列一致性聚类出约 11 亿条代表序列、逐一预测结构——预印本称这批结构用约两周算完，其中 4.185 亿个达到高置信（pLDDT > 0.7）。与 AlphaFold 数据库约 8.35 亿、上一代 ESM Atlas 约 3.36 亿的规模相比，这是迄今蛋白质生物学上规模最大的一次 AI 应用，可以在 Biohub 平台上检索结构、功能邻域以及现有数据库尚未标注的进化关联：全部序列经 SAE 特征聚类后，得到约 770 万个成员数不少于 50 的蛋白簇。

## 任务流案例：设计一个蛋白质 binder

以设计靶向某蛋白质的结合肽（binder）为例，官方已把从靶点序列到排序候选的完整协议开源在 [binder_design.ipynb](https://github.com/Biohub/esm/blob/main/cookbook/tutorials/binder_design.ipynb)：

1. **输入目标序列**：把靶点序列送入 ESMFold2，先用单序列模式快速拿到结构
2. **生成候选序列**：从 ESMC 的序列先验出发，把序列松弛为连续变量做梯度优化，温度退火逐步「结晶」出离散序列，损失函数由 ESMFold2 复合物的 ipTM 等指标反传
3. **结构验证与排序**：候选序列重新折叠，用多个 critic 模型集成打分排序；官方实验里 critic 从 4 个加到 19 个、算力从约 500 加到 2400 H100 小时（scFv 为 1800→7700），每个靶点-模态-算力档取 84 个设计去验证
4. **功能预估**：通过 ESM Atlas 查询候选序列的表征特征，评估潜在活性
5. **实验迭代**：合成并测试，按实测结果调整

Biohub 在 2026 年 5 月的发布说明与 2026 年 6 月的预印本中报告，用这套流程针对 5 个治疗相关靶点——受体酪氨酸激酶 EGFR、PDGFRβ，免疫检查点 PD-L1、CTLA-4，以及免疫信号调节因子 CD45——完成纯计算设计，搜索以天计完成（传统开发单个临床前候选 binder 通常需 3–4 年）。所得 binder 在实验室验证中表现出高亲和力（BLI 实测约 68 pM–70 nM）、高特异性和高稳定性：两个设计模态（从头迷你蛋白与抗体衍生的 scFv 片段）在较高算力下的实验命中率分别约 36%–88% 与 15%–29%。结构层面的抽查也对得上：一个 EGFR 迷你蛋白经冷冻电镜解析（分辨率约 3.8 Å），其结合位点与计算预测的 1,108 对原子坐标 RMSD 约 1.2 Å；PD-L1 binder 在细胞免疫检查点实验中恢复了 T 细胞信号，其中 minibinder 的 IC50 约 1.6 nM，已接近已上市抗体 atezolizumab 衍生片段的 2.6 nM。特异性方面，抗 EGFR 设计对最接近的同源蛋白 HER3 无结合，抗 CTLA-4 设计不结合 CD28。新颖性方面，438 个 minibinder 序列 BLAST 检索只有 5 个在公开数据库有显著匹配（序列一致性均低于 34%），倾向于是从头（de novo）生成的新解。需要说明：全部结果来自官方发布与预印本，第三方复现与临床前评估尚未公开。

## 能力边界与不确定性

### 已验证的能力

- 从单条序列预测蛋白质结构，无需 MSA
- 蛋白质-配体复合物结构预测（DNA、RNA、小分子）
- 蛋白质语言模型表征提取，适合下游任务微调
- 大规模蛋白质序列 / 结构的可检索图谱（Atlas）

### 尚未充分验证或存在局限的

- **性能对标声明**：官方称 ESMFold2 在 DockQ 等指标上达到并能超过 AlphaFold3 的结果，主要来自官方预印本，第三方独立评测有限
- **binder 设计实际效果**：官方展示了 5 个靶点的验证数据，每个靶点-模态-算力档只有 84 个设计，样本量小，泛化能力未知
- **计算资源门槛**：ESMC-6B 与 ESMFold2 都需要较多 GPU 内存，本地运行成本高
- **生物安全边界**：官方设有 Frontier Safety 团队并对各组件做了风险评估，Biohub 平台对受控病原体与毒素的关键词和序列部署了检测护栏（可申请提权访问）；预印本附录称在病毒蛋白深度突变扫描数据上，ESMC 的变异效应预测并不优于现有工具。滥用风险的独立评估目前仍属空白。

### 不能由此推出的结论

- ESMFold2「全面超越」AlphaFold3（目前只有官方自测 / 预印本数据）
- 这套系统可直接用于临床药物设计（仍处科研验证阶段）
- SAE 特征解释完全准确（由自动化流程生成，存在幻觉可能）

## 适用人群与采用建议

**适合先尝试：**

- 需要快速从序列拿到结构，且没有充足 MSA 计算资源
- 想在 ESMC 表征空间做下游任务（分类、聚类、功能预测）的研究团队
- 需要大规模结构 / 表征数据查询（通过 Atlas）
- 蛋白质设计的早期探索（binder、酶改造）

**可以等等再上车：**

- 需要充分验证的生产级结构预测管线（建议与 AlphaFold2/3 交叉对比）
- 对可解释性有严格要求的监管场景（SAE 特征仍在研究期）
- 计算资源受限的中小团队

## 技术规格速览

| 组件 | 模型规模 | 输入 | 输出 |
|------|----------|------|------|
| ESMC | 300M / 600M / 6B | 蛋白质序列 | 隐藏层表征 |
| ESMFold2 | 冻结 ESMC-6B + 48 层循环折叠 + 扩散头 | 序列 ± MSA ± DNA/RNA/配体 | 3D 结构（mmcif）+ 置信度 |
| ESMFold2-Fast | 同上，折叠层减为 24，单序列专用 | 蛋白质序列 | 3D 结构 + 置信度 |
| ESM Atlas SAE | 6B 第 60 层，k=64 | ESMC 表征 | 约 1.6 万个可解释特征 |

许可：仓库 LICENSE.md 为标准 MIT（版权 Chan Zuckerberg Biohub, Inc.），ESMC、ESMFold2、SAE 的代码与权重以及 Atlas 数据、binder 设计系统都按这一协议开放；ESM3 的代码与公开权重（esm3-sm-open-v1）同样按 MIT 提供，但更大的 ESM3 权重只开放平台调用。GitHub 仓库页面的许可识别因 LICENSE 文件格式显示为 Other/NOASSERTION，商用前以 LICENSE.md 原文为准。

## 如何开始

### 云平台（最快）

```python
pip install esm  # 已发布到 PyPI
from esm.sdk import esmc_client
model = esmc_client(model="esmc-600m-2024-12", url="https://biohub.ai", token="<your_token>")
```

ESMFold2 走平台时用的是另一个客户端，模型名 `esmfold2-fast-2026-05`：

```python
from esm.sdk.forge import SequenceStructureForgeInferenceClient
from esm.sdk.api import FoldingConfig

client = SequenceStructureForgeInferenceClient(
    model="esmfold2-fast-2026-05", url="https://biohub.ai", token="<your_token>"
)
result = client.fold_all_atom(spi, config=FoldingConfig(num_loops=20, num_sampling_steps=100))
```

批量任务可以把调用包进 `esm.sdk.parallel_executor` 上下文管理器，它会并发发请求并自适应限速。API token 在 [developer console](https://biohub.ai/developer-console/api-keys) 创建。

### 本地运行

```python
from esm.models.esmc import EsmcForMaskedLM, EsmcTokenizer
model = EsmcForMaskedLM.from_pretrained("biohub/ESMC-6B", device="cuda")
```

也可以用 Hugging Face Transformers v5.16.0 起的原生集成加载 `biohub/ESMC-6B` 与 `biohub/ESMFold2`。AMD 显卡需 ROCm 6.4 + PyTorch 2.9 以上。

### 官方资源

- GitHub：https://github.com/Biohub/esm
- 官方发布说明：https://biohub.org/news/world-model-of-protein-biology/
- 预印本：https://www.biorxiv.org/content/10.64898/2026.06.03.729735v1
- Atlas 平台：https://biohub.ai/esm/protein/atlas
- 教程：https://github.com/Biohub/esm/tree/main/cookbook/tutorials

---

## 自测题

1. **ESM 的三层架构各层的职责是什么？**
   参考答案：ESMC 是底层语言模型，在约 28 亿条序列上训练（300M/600M/6B 三档），学习进化规律；ESMFold2 以 ESMC 表征为输入、接扩散头做结构预测；ESM Atlas 用 SAE 把 ESMC 表征拆成可解释特征并映射到数据库。

2. **ESMFold2 相比 AlphaFold3 的优势和局限是什么？**
   参考答案：优势——支持单序列模式（无需 MSA），折叠约 1024 残基的蛋白只要十几秒；可处理 DNA、RNA、小分子与修饰氨基酸；官方预印本称其在蛋白质-蛋白质与抗体-抗原基准上达到并超过 AlphaFold3。局限——对标数据目前只有官方一家的；binder 设计只有 5 个靶点样本，泛化未知。

3. **ESM Atlas 的稀疏自编码器起什么作用？**
   参考答案：ESMC 的知识以神经表征存在权重里，人读不懂。Atlas 用 SAE（6B 第 60 层、码本 16,384）把表征拆成可解释特征，再由自动化流程映射到已知蛋白质数据库，让大规模未注解序列变得可搜索。

4. **这套系统能直接用于临床药物设计吗？**
   参考答案：不能。binder 验证只有 5 个靶点、每档 84 个设计；SAE 解释由自动化流程生成、存在幻觉；计算资源门槛高。目前定位是科研验证工具。

5. **你会从哪几方面测试它是否适合你的团队？**
   参考答案：云平台上跑通一个单序列预测，与 AlphaFold2/3 对比精度和速度；用 ESMC 表征做下游任务微调；用 Atlas 查大规模数据；评估计算资源是否在预算内。

---

## 进阶路径

### 阶段一：快速验证（1–2 周）
- **目标**：跑通 ESMFold2 单序列预测，看懂三层架构
- **行动**：注册 Biohub 云平台，用 `esm.sdk` 预测一个结构，对照官方基准
- **验收**：能说清 ESMC、ESMFold2、ESM Atlas 各自的输入输出及协作方式

### 阶段二：科研应用（2–4 周）
- **目标**：在科研任务中评估 ESM 的适用边界
- **行动**：预测目标结构、微调 ESMC 表征做下游任务、用 Atlas 查特征
- **验收**：能判断它在特定任务上的精度与速度是否达标

### 阶段三：蛋白质设计（1–3 个月）
- **目标**：用 ESM 做 binder、酶改造等设计
- **行动**：按「任务流案例」走一遍，在 ESMC 表征空间优化序列并实验验证
- **验收**：能独立完成一个设计流程，并解释其生物学依据

### 阶段四：方法学改进（长期）
- **目标**：理解方法学局限并提出改进
- **行动**：读 ESMC、ESMFold2、Atlas 的论文，分析架构与训练细节
- **验收**：能批判性评价系统优劣并给出改进方向

---

## 常见问题

### Q1: ESMFold2 的精度真的超过 AlphaFold3 吗？
A：官方预印本称其在 DockQ 基准上达到并能超过 AlphaFold3，尤其在抗体-抗原结合预测上更强。但这是官方结论，建议在实际任务中与 AlphaFold2/3 交叉对比后选用。

### Q2: 需要多少计算资源？
A：ESMC-6B 与 ESMFold2 都需要较大的 GPU 内存。Biohub 云平台是最快的入门方式，不需要本地 GPU；本地运行请查看 HuggingFace 模型卡的硬件说明。

### Q3: ESM Atlas 的特征解释可靠吗？
A：特征由自动化流程生成，存在幻觉可能，更适合作为假设生成工具，而非确定性结论，不应直接用于临床决策。

### Q4: 可以商用吗？
A：仓库 LICENSE.md 为标准 MIT，ESMC、ESMFold2、SAE、Atlas 数据与公开的 ESM3 权重（esm3-sm-open-v1）都可商用；更大的 ESM3 权重只开放平台调用。GitHub 页面因 LICENSE 文件格式识别为 Other/NOASSERTION，商用决策前建议以 LICENSE.md 原文为准并咨询法律意见。

### Q5: 如何获取技术支持？
A：可通过 GitHub Issues 或在官方渠道提问。科研类问题通常在 GitHub Issues 能得到社区或官方回复。

---

## 练习

### 练习 1：跑通 ESMFold2 单序列结构预测

**任务**：在 Biohub 云平台或本地用 ESMFold2 预测一个蛋白质的结构。

**步骤**：
1. 打开 Biohub 平台，或本地按 `esm` 依赖并导入 `EsmFold2Model`
2. 选一条已知蛋白序列（如 GFP，绿色荧光蛋白）
3. 用单序列模式预测（不提供 MSA）
4. 下载 PDB 结果，用 PyMOL 或 ChimeraX 可视化
5. 与实验结构（Protein Data Bank）对比

**参考答案**：
- 单序列模式通常分钟级内完成（预印本口径：1024 残基约 16 秒）
- 计算 RMSD（均方根偏差），检查是否捕获正确的折叠拓扑
- 若拓扑明显错误，说明该蛋白位于 ESMFold2 的能力边界之外

### 练习 2：用 ESMC 表征做聚类

**任务**：用 ESMC 提取序列表征向量并做聚类分析。

**步骤**：
1. 从 UniProt 下载一组功能相关的序列（如全部激酶）
2. 加载 ESMC 模型（600M 起步，资源充裕再用 6B）
3. 提取每个序列的表征（末层隐藏状态平均）
4. 用 sklearn 做 PCA 或 UMAP 降维可视化
5. 检查聚类是否与已知家族分类吻合

**参考答案**：
- ESMC 在大量序列上预训练，应能捕获功能相关模式
- 功能相近的序列在表征空间应更靠近
- 可比较不同层（等价于例程中的 `output_hidden_states=True`）的功能相关性差异

### 练习 3：用 ESM Atlas 查询特征

**任务**：用 ESM Atlas 查一个蛋白质的结构与功能特征。

**步骤**：
1. 打开 ESM Atlas 平台
2. 检索你感兴趣的蛋白质（如刺突蛋白相关靶点）
3. 查看 SAE 特征分解结果，哪些特征被激活
4. 与已知功能注释对照，评估解释是否合理

**参考答案**：
- SAE 特征应能大致捕捉已知功能域
- 解释由自动化流程生成，有幻觉可能，需谨慎
- 把特征当假设来源，再用实验去验证

---

## 资料口径说明

本文的判断与结论来自以下来源，存在明确局限：

1. **主要来源**：[Chan Zuckerberg Biohub 官方发布说明](https://biohub.org/news/world-model-of-protein-biology/)（2026-05-27）、[ESM 预印本](https://www.biorxiv.org/content/10.64898/2026.06.03.729735v1)（Candido et al., 2026-06-04）、[esm GitHub 仓库](https://github.com/Biohub/esm)的 README 与代码示例。
2. **断言强度**：ESMFold2 对比 AlphaFold3、binder 设计的成绩均为官方发布与预印本口径，第三方独立复现有限。
3. **稳定性边界**：代码示例基于 `esm` 包现有 Python API（v3.4.post1，含 HF Transformers 集成），具体签名会随版本变化。
4. **时效性**：初稿基于 2026 年 5–6 月的版本撰写，2026-10-02 对照仓库与预印本核订（stars/forks、许可状态、API 类名均以当日仓库状态为准）。

🦞 文档版本：2026-10-02 | ESM 版本：esm v3.4.post1（ESMC-6B / ESMFold2） | 来源：[GitHub](https://github.com/Biohub/esm)