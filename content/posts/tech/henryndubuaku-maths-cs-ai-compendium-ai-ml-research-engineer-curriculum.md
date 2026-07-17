---
title: "HenryNdubuaku/maths-cs-ai-compendium 拆解：一份把 AI/ML 研究工程师之路切成 18 个可执行阶段的 textbook 仓库"
date: 2026-07-18T03:08:50+08:00
lastmod: 2026-07-18T03:08:50+08:00
draft: false
categories: ["技术笔记"]
tags: ["AI/ML", "Curriculum", "学习路径", "Maths", "Compendium"]
description: "maths-cs-ai-compendium 是 Henry Ndubuaku 维护的 AI/ML 研究工程师 textbook,18 章覆盖向量到 ML Systems Design,Apache-2.0 协议,6527 stars,自带 MCP Server。"
weight: 1
slug: "henryndubuaku-maths-cs-ai-compendium-ai-ml-research-engineer-curriculum"
author: text-matrix
---

## 一句话判断

**[HenryNdubuaku/maths-cs-ai-compendium](https://github.com/HenryNdubuaku/maths-cs-ai-compendium) 是一份 Apache-2.0 协议的"AI/ML 研究工程师 textbook",18 章从 Vectors 一路写到 ML Systems Design,作者 Henry Ndubuaku 是去年进 Y Combinator 的从业者,描述里直接写 "Become a cracked AI/ML Research Engineer"。** 它和 OSSU / fast.ai 的最大差别在于**作者亲自整理并以"朋友在 DeepMind / OpenAI / Nvidia 通过面试"作为背书**,且 18 章全部 Available(README 表格里 Status 列无 "Planned"),仓库还附带一个 MCP Server,让 Claude Code / Cursor / VS Code 直接把它当知识库用。

如果你正在从"会用 PyTorch 跑模型"过渡到"能独立设计一个训练 / 推理 / 部署闭环",或者在准备 DeepMind / OpenAI 级别的研究工程师面试,这份 18 章路径值得放进书单。但如果你只想 6 周速成 Transformer,它是错的工具。

---

## 系统地图

Compendium 的真实结构不是 README 顶部的 logo,而是按"作者背景 → 学习理念 → 18 章 syllabus → 学习方法论 → MCP 集成"五层组织的:

```
┌──────────────────────────────────────────────────────────────────────┐
│  顶层定位 (Author positioning)                                           │
│   作者: Henry Ndubuaku,去年进 Y Combinator                                │
│   背景: 在 AI/ML 行业工作多年,笔记本积累 intuition-first 笔记                │
│   背书: 2025 年朋友用这份笔记通过 DeepMind / OpenAI / Nvidia 面试            │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────┐
│  学习理念 (Pedagogy)                                                     │
│   - 不堆符号,从 intuition 出发                                            │
│   - 不假设读者已有先验知识                                                  │
│   - 真实世界语境,不做"为考试而学"的裁剪                                      │
│   - "你只需要 elementary maths + basic python,其他都现学"                   │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────┐
│  18 章 Syllabus (每一章都是 Available)                                    │
│   基础数学 (01–05):                                                     │
│     01 Vectors / 02 Matrices / 03 Calculus / 04 Statistics / 05 Probability│
│   AI/ML 核心 (06–12):                                                   │
│     06 ML / 07 NLP / 08 CV / 09 Audio / 10 Multimodal /                  │
│     11 Autonomous Systems / 12 GNN                                      │
│   系统与工程 (13–18):                                                     │
│     13 Computing & OS / 14 DS&A / 15 ProdSE / 16 SIMD & GPU /            │
│     17 AI Inference / 18 ML Systems Design                              │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────┐
│  学习方法论 (How to study better)                                          │
│   Phase 1 - Cumulative reading: 当天睡前读当天内容,下一讲从头再来补 gap          │
│   Phase 2 - Shadow reading: 读小标题→合书→写解释→对比缺失                     │
│             "类似 masked language modelling"                                  │
│             最终用代码实现每个概念 → 形成 muscle memory                       │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────┐
│  MCP Server 集成 (AI-Native 入口)                                         │
│   - Claude Code / Cursor / VS Code 等可直接挂载                             │
│   - 把 18 章 compendium 当作本地知识库                                       │
│   - 附教学用途的 tools + example implementations                             │
│   - 需要本地 clone 仓库                                                     │
└──────────────────────────────────────────────────────────────────────┘
```

这张图最重要的一条路径:**"作者背书 → intuition-first pedagogy → 18 章 syllabus → 两阶段阅读法 → MCP 接入"**。Compendium 之所以不是又一个 markdown 学习资料合集,是因为它**有作者背景做锚 + 方法论做约束 + AI 原生入口做延伸**——任何一个因素缺失都让它退化成"awesome-X"列表。

---

## 边界与角色划分

把 Compendium 拆成 6 组"不变项",可以一次性回答它和 OSSU、fast.ai、Hugging Face 课程、DeepLearning.AI 短课的差别:

| 维度 | Compendium 的不变项 | 工程含义 |
|------|----------------------|---------|
| 顶层依据 | 作者本人 AI/ML 工作积累 + YC 背景 + 朋友面试结果 | 不是按公开课标准,也不是按论文路线图,而是按"真实研究工程师要会什么" |
| 选材标准 | intuition first + no hand-waving + real-world context | 任何"符号密集"或"脱离实现"的章节都会让读者中途放弃 |
| 内容形态 | 18 章自包含 markdown,目录里全是 Available | 不会发生"读到一半发现后面是 TODO" |
| 教学风格 | 两阶段阅读法(累计阅读 + 遮蔽阅读) | 不是看视频,而是"读→合书→写解释→代码实现" |
| 工程覆盖 | 含 SIMD/GPU/CUDA、Triton、TPU、ML Systems Design | 不只是模型层,系统层和推理层都覆盖 |
| AI 集成 | 原生 MCP Server,挂 Claude Code / Cursor / VS Code | 让 LLM 把 compendium 当 RAG 知识库,而不仅是 PDF 阅读 |

要注意的几个边界:**Compendium 不是学位**——它没有学分、没有证书、不替代正式学位;**它不是速成训练营**——18 章每章都是严肃教材,完整读完至少半年;**它不是论文集**——它教你"够用的原理",不是 paper-by-paper 的 survey;**它不替代教科书**——遇到特别深的数学细节,作者鼓励你额外查资料补 gap。

---

## 关键机制:18 章到底在覆盖什么

把 README 里 18 章的 Summary 列原样梳理(已经过核验),按"数学基础 / AI 核心 / 系统工程"三段拆开:

### 第一段:数学基础 (01–05)

| # | 章节 | 覆盖范围 | 一句话判断 |
|---|------|----------|-----------|
| 01 | Vectors | 空间、模、方向、范数、距离、点/叉/外积、基、对偶 | 是线性代数的入门,不是科普 |
| 02 | Matrices | 性质、特殊矩阵、运算、线性变换、LU/QR/SVD 分解 | 把"矩阵到底是什么"讲清楚 |
| 03 | Calculus | 导数、积分、多元微积分、Taylor 近似、优化与梯度下降 | 直接为深度学习的反向传播铺路 |
| 04 | Statistics | 描述统计、抽样、中心极限定理、假设检验、置信区间 | 不是统计学家视角,是 ML 工程师视角 |
| 05 | Probability | 计数、条件概率、分布、贝叶斯方法、信息论 | 信息论那段是给后续 Transformer / RL 打地基 |

**这段的关键判断**:数学基础只到 5 章,作者不打算把你训练成数学家,而是"让你看到公式不害怕、能复现论文里的推导"。如果你的目标是发论文,读完这 5 章后还得补《Mathematics for Machine Learning》或更深的测度论。

### 第二段:AI/ML 核心 (06–12)

| # | 章节 | 覆盖范围 | 一句话判断 |
|---|------|----------|-----------|
| 06 | Machine Learning | 经典 ML、梯度方法、深度学习、强化学习、分布式训练 | 是全书的中枢,所有章节都从这里辐射 |
| 07 | Computational Linguistics | 句法/语义/语用、NLP、语言模型、RNN/CNN/Attention、Transformer、Text Diffusion、Text OCR、MoE、SSM、现代 LLM 架构、NLP 评测 | NLP 的全景图,SSM/MoE 都覆盖 |
| 08 | Computer Vision | 图像处理、目标检测、分割、视频处理、SLAM、CNN、ViT、扩散、Flow Matching、VR/AR | 把传统 CV 和现代扩散模型都塞进一章 |
| 09 | Audio & Speech | DSP、ASR、TTS、声学活动检测、说话人 diarisation、源分离、主动降噪、WaveNet、Conformer | 语音方向的全栈式覆盖 |
| 10 | Multimodal Learning | 融合策略、对比学习、CLIP、VLM、图像/视频 tokenization、跨模态生成、统一架构、World Models | 2024–2026 主流方向的入口 |
| 11 | Autonomous Systems | 感知、机器人学习、VLA(Self-driving cars)、Space robots | 偏具身 / 自动驾驶方向 |
| 12 | Graph Neural Networks | 几何深度学习、图论、GNN、Graph Attention、Graph Transformer、3D 等变网络 | 覆盖了 Geometric DL 的主线 |

**这段的关键判断**:AI 核心不是按"模型分类"组织,而是按"数据模态"(语言/视觉/语音/多模态/机器人/图)组织——这是它和"按模型分类"的教科书最大的差别。这种组织方式的好处是**当一个新模型出来时,你能马上定位它在哪个模态章节的延伸里**(比如 Mamba 放 SSM,Gato/VLA 放 Autonomous Systems)。

### 第三段:系统与工程 (13–18)

| # | 章节 | 覆盖范围 | 一句话判断 |
|---|------|----------|-----------|
| 13 | Computing & OS | 离散数学、计算机架构、操作系统、并发/并行、编程语言 | 给后续 SIMD/GPU 打地基 |
| 14 | Data Structures & Algorithms | Big O、递归、回溯、DP、数组、哈希、链表、栈、树、图、排序、二分 | 算法面试基础,但不是 LeetCode 题库 |
| 15 | Production Software Engineering | Linux、Git、codebase 设计、测试、CI/CD、Docker、模型 serving、MLOps、监控、"最佳使用 coding agents" | 是把 ML 工程师从 notebook 拽到生产环境的关键 |
| 16 | SIMD & GPU Programming | C++ for ML、框架怎么工作、硬件基础、ARM NEON/I8MM/SME2、x86 AVX、GPU/CUDA、Triton、TPU、RISC-V、Vulkan、WebGPU | 硬件层的全景图,从 ARM 到 RISC-V |
| 17 | AI Inference | 量化、高效架构、serving/batching、edge inference、speculative decoding、成本优化 | 推理优化的入口 |
| 18 | ML Systems Design | 系统基础、云计算、分布式系统、ML 生命周期、feature store、A/B 测试、推荐/搜索/广告/反作弊设计案例 | 是"ML 工程师和研究员的最大区别" |

**这段的关键判断**:13–18 章是 Compendium 和其他"AI 教科书"最大的差异点。**大部分 AI 教科书到第 7 章 NLP 就结束了,Compendium 用 6 章把系统层、推理层、生产层串起来**——这正是"研究工程师"(Research Engineer)和"ML 研究员"(Research Scientist)的分界线。

---

## 学习方法:两阶段阅读法

作者在 README "How To Study Better" 部分给了具体的、可立刻执行的方法,值得直接抄走:

**Phase 1 - Cumulative reading after classes(累计阅读)**

> 每天下课后、睡前把当天材料读一遍。下一讲开始时从头再来,直到读到当前进度,然后用额外研究补 gap。这让大脑把模式连起来。

**Phase 2 - Shadow reading before exams(遮蔽式阅读)**

> 读每个 slide / note 的小标题,合上书,然后在心里复述 + 写下那个概念的解释。只重读你漏掉的部分——**类似 masked language modelling**。最终用代码实现每个概念,形成 muscle memory。

**几个关键 takeaway**:

- **Phase 1 是"重复模式识别",Phase 2 是"主动回忆"**——这是认知科学里两个最有效的学习策略,Compendium 把它们工程化了
- **Phase 2 的"写代码"环节不是可选**——作者明确说"muscle memory 是终极目标",意味着每个概念都要落到实现
- **不靠视频**——Compendium 是 markdown,所有学习都是"读 + 写",不依赖任何人讲解

---

## 如何本地使用 + MCP 接入

README 里说"This repo includes an MCP server that lets any AI assistant (Claude Code, Cursor, VS Code, etc.) use the compendium as a knowledge base." 也就是说仓库自带 MCP server,有以下使用方式:

### 方式 A: 在线阅读(零成本入门)

直接访问 [henryndubuaku.github.io/maths-cs-ai-compendium](https://henryndubuaku.github.io/maths-cs-ai-compendium/)(README 里给的链接),不需要 clone,适合先扫一遍判断是否适合自己。

### 方式 B: 本地 clone + 纯 markdown 阅读(推荐)

```bash
git clone https://github.com/HenryNdubuaku/maths-cs-ai-compendium.git
cd maths-cs-ai-compendium
```

然后按 01 → 18 顺序,用任意 markdown 阅读器(Typora / Obsidian / VS Code Markdown Preview)开始读。**这种方式的优点**:不被 LLM "二手转述"扭曲,直接读作者原文;**缺点**:没有 RAG 增强,跨章节检索要靠自己的笔记。

### 方式 C: MCP Server 接入 AI 助手(进阶)

仓库自带 MCP server,按 README 描述:"It requires a local clone of the repo. Comes with tools for educational purposes and example implementations."

具体步骤:

1. 本地 clone(同方式 B)
2. 启动仓库自带的 MCP server(具体启动方式参考仓库内的 MCP 文档,README 未展开)
3. 在 Claude Code / Cursor / VS Code 里挂载这个 MCP server,把 compendium 当作知识库
4. 学习时遇到问题直接问 AI:"根据 compendium 第 7 章,Transformer 的 attention 公式是什么?",AI 会基于本地 markdown 回答

**这种方式的优点**:把 18 章内容当作 RAG 知识库,问答时可以精确定位章节;**缺点**:需要你配置 MCP(有学习成本),且 LLM 回答仍有幻觉风险,关键概念以原文为准。

---

## 适用边界:谁该用 / 谁不该用

### 推荐使用

- **想从"调参工程师"过渡到"研究工程师"的从业者**——13–18 章的系统内容是这类人群的最大痛点
- **准备 DeepMind / OpenAI / Nvidia 面试的求职者**——README 里明确说 2025 年朋友用这份笔记通过了这些面试,这是最强背书
- **在工作中遇到 ML Systems Design 题目但没系统训练过的工程师**——第 18 章直接给"推荐/搜索/广告/反作弊"的系统设计案例
- **想从 inference 角度重新理解模型的工程师**——第 17 章的 quantisation / speculative decoding / batching / edge inference 串成完整链路
- **想用 MCP 把学习资料 AI-Native 化的早期采用者**——Compendium 的 MCP server 是同类项目里少见的"AI-first 入口"

### 不推荐使用

- **想 6 周速成 Transformer 的初学者**——18 章里 Transformer 知识分布在第 6/7/10/16/17 章,跨度大,不适合赶进度
- **想读论文、写 paper 的学术研究员**——Compendium 是工程师视角,不是 survey 视角,论文引用密度不够
- **想拿学位证的正规学生**——Compendium 没学分、没证书,不能替代正式学位
- **只想学传统 CV 或传统 NLP 的人**——第 7/8 章把传统方法和现代方法混在一起讲,如果你只想看 YOLO 历史,直接读论文更高效
- **不打算写代码的人**——作者明确说"muscle memory"是终极目标,不写代码的纯阅读会浪费 Phase 2 的核心机制

---

## 阅读路径建议(三种 profile)

根据不同背景,Compendium 的最佳起点不一样:

### Profile 1:已经有 ML 工程经验,想补系统层(8 周)

跳过 01–06,从 **第 13 章 Computing & OS** 开始 → 14 DS&A → 15 ProdSE → 16 SIMD/GPU → 17 Inference → 18 ML Systems Design。每章用 Phase 2 的方法,读完小标题后合书写代码。

### Profile 2:数学基础不扎实,但会写 PyTorch(16 周)

从 **第 01 章 Vectors** 开始按顺序读到 06 ML,这一段严格用 Phase 1(累计阅读)巩固基础。然后从 07 开始按"数据模态"挑感兴趣的方向读(比如对 LLM 感兴趣就重点看 07,对自动驾驶感兴趣就重点看 11),最后回到 17/18 收尾。

### Profile 3:零基础但有 Python(24 周以上)

完全按 01 → 18 顺序读,每周一章,严格 Phase 1 + Phase 2 交替,每章至少写 3 段代码验证概念。前 5 章(数学基础)可以放慢到每章 2 周,因为这是后续所有章节的地基。

### 通用建议

- **不要试图一次读完**——18 章是 18 个独立项目,每个都能单独成书
- **跨章节笔记**——第 6 章的"梯度方法"和第 17 章的"量化"会反复出现,做好交叉引用
- **MCP 接入是放大器不是替代**——AI 助手可以帮你定位章节、解释概念,但 Phase 2 的"自己写代码"环节不能省

---

## 仓库健康度(截至 2026-07-18)

| 指标 | 数据 | 解读 |
|------|------|------|
| Stars | 6527 | 增长中(2026-02 创建,半年 6500+) |
| Forks | 805 | fork 比例 ~12%,正常自学路径水平 |
| Watchers | 6527(=Stars) | 用户订阅活跃,不是僵尸仓 |
| License | Apache-2.0 | 可商用、可改、可闭源,无传染性 |
| 默认分支 | main | 无 dev 分支 |
| 创建时间 | 2026-02-03 | 半年内的新仓 |
| 最新 push | 2026-07-16 | 2 天前仍在更新 |
| 最新 metadata 更新 | 2026-07-17 | 仓库元数据 1 天前更新 |
| Open Issues | 8 | 健康(没有堆积 PR / Issue) |
| Discussions | enabled | 有社区讨论 |
| Wiki | enabled | 有额外文档空间 |
| GitHub Pages | enabled | 有在线阅读站(README 顶部的链接) |
| 仓库 size | 8063 KB | 包含图片 + MCP 实现,体积合理 |
| Subscribers | 72 | 关注 release 的开发者数量 |

**关键判断**:

- **README 表格里 18 章全部 Available**,没有 Planned / TODO 状态,这是教科书类项目最容易翻车的地方(承诺写一半没了)
- **作者本人在持续 push**(2026-07-16 仍在更新),不是发完就跑的"毕业项目"
- **Apache-2.0 协议**比 MIT 更适合"教科书"——明确授予专利使用权,适合做企业培训
- **8 个 open issues**——可能包含 typo / 章节补充请求,而不是结构性问题

---

## 总结

Compendium 的真正价值不在 6527 stars,而在**它是少数把"研究工程师"当作完整职业路径来设计的 textbook**——从 Vectors 到 ML Systems Design,18 章覆盖了数学、AI、CV/NLP/Audio/Multimodal/Robotics/GNN、SIMD/GPU、Inference、Systems Design 的全栈式路径,且每一章都自带作者背书 + intuition-first 教学法 + MCP AI-Native 入口。

它不是给所有人的——但如果你正在从"调参工程师"过渡到"独立设计训练/推理/部署闭环的研究工程师",它可能是 2026 年最值得系统读完的一份 syllabus。

---

## 参考链接

- 仓库: [github.com/HenryNdubuaku/maths-cs-ai-compendium](https://github.com/HenryNdubuaku/maths-cs-ai-compendium)
- 在线阅读: [henryndubuaku.github.io/maths-cs-ai-compendium](https://henryndubuaku.github.io/maths-cs-ai-compendium/)
- License: Apache-2.0
- 创建时间: 2026-02-03
- 最新更新: 2026-07-16 push / 2026-07-17 metadata
- 引用: `@book{ndubuaku2025compendium, year={2026}, publisher={GitHub}}`
