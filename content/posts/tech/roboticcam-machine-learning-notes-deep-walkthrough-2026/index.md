---
title: "袁晓鹏 8 年 ML 讲义拆解：roboticcam 凭什么成为 GitHub 10k+ Stars 的「野生」机器学习课程"
date: 2026-08-05T14:10:00+08:00
draft: false
summary: "roboticcam/machine-learning-notes 是香港浸会大学(HKBU)副教授袁晓鹏 2018 年至今 8 年不间断维护的 ML 讲义仓库,72 份 PDF + 8 份 PPTX + 1 个 Jupyter Notebook,GitHub 10.1k stars / 1.8k forks。本文拆开它的 7 个递进层次:基础数学 → 概率模型 → 优化 → 深度学习 → 生成模型 → 3D 视觉 → 强化学习 → NLP,以及它和现有大学课程的关键差异——它把学习理论(Concentration Inequality/Rademacher 复杂度/PAC-Bayes/NTK/JL lemma)、贝叶斯非参(Dirichlet Process/HDP-HMM/IBP/DPP)、State Space Model(Kalman/HMM)这些通常散落在研究生课程的硬骨头,搬进了同一本讲义。"
tags: ["机器学习", "深度学习", "概率模型", "袁晓鹏", "roboticcam", "教学仓库", "DPP", "贝叶斯非参", "MCMC", "GitHub 10k"]
categories: ["技术文章"]
authors: ["钳岳"]
github_repo: "roboticcam/machine-learning-notes"
description: "袁晓鹏 8 年 ML 讲义拆解:从 Learning Theory(Rademacher/NTK/PAC-Bayes)到 BNP(Dirichlet Process/IBP/DPP/HDP-HMM),72 份 PDF + 8 PPTX,GitHub 10.1k stars,深度教学仓库"
---

## 一、10k Stars 的「野生」机器学习课程

[roboticcam/machine-learning-notes](https://github.com/roboticcam/machine-learning-notes) 在 GitHub 上是个异类。

它不是框架,不是工具,不是论文实现——它是**香港浸会大学(Hong Kong Baptist University, HKBU)副教授袁晓鹏(Xu Yi-da)2018 年至今 8 年持续维护的机器学习讲义集**。72 份 PDF + 8 份 PPTX + 1 个 Jupyter Notebook,总大小 82.4 MB,GitHub **10.1k stars / 1.8k forks**,2018-02-15 创建,**2026-08-05 还在 commit**(更新周期横跨 8 年)。

README 顶部作者写得很直接:

> My continuously updated Machine Learning, Probabilistic Models and Deep Learning notes and demos (2000+ slides)

2022 年起,作者每周日晚上 8:30 在微信群直播 ML 课程;从 2022 年 4 月起,每 2-3 周通过 Zoom 用英文讲 Machine Learning Research Seminar(香港时间晚上 7 点)。2015 年他用中文录过约 10% 的课件——所有讲义正文是英文的,视频在 YouTube/B 站/优酷三处都存。

这不是一份写完就放在那的 GitHub 仓库,而是一门持续更新的课程——讲义每年更新,B 站视频链接嵌在每个章节标题下,README 末尾留着 PhD 招生邮箱 `xuyida@hkbu.edu.hk`。作者此前在澳大利亚悉尼大学和阿德莱德大学任教,后加入 HKBU 计算机科学系。

## 二、72 份 PDF 的 7 个层次

我把这 72 份 PDF 按内容切成 7 个递进层次。这不是仓库官方分类(作者是按章节平铺),而是按数学工具的依赖关系重构出来的「自下而上」:

```
┌─────────────────────────────────────────────────────────┐
│ 1. Learning Theory  学习理论                              │
│    Concentration Inequality / Rademacher Complexity /     │
│    Neural Tangent Kernel / PAC-Bayes / JL lemma          │
├─────────────────────────────────────────────────────────┤
│ 2. Foundational Mathematics  基础数学                      │
│    评估 / Decision Tree / Simple Bayes / Regression /    │
│    Neural Network / Unsupervised                          │
├─────────────────────────────────────────────────────────┤
│ 3. Intermediate Mathematics  中级数学                      │
│    EM 收敛证明 / MCMC / Variational Bayes / State Space  │
│    (Kalman + HMM) / Policy Gradient (PPO/TRPO)           │
├─────────────────────────────────────────────────────────┤
│ 4. Probabilistic Models  概率模型                          │
│    Probability / Monte Carlo / MCMC / Particle Filter /  │
│    BNP(Dirichlet Process/IBP/DPP/HDP-HMM)                │
├─────────────────────────────────────────────────────────┤
│ 5. Deep Learning Research  深度学习研究                    │
│    Transformer / VAE/IWAE/Flow Matching / GAN /          │
│    NeuralODE / Variance Reduction(REBAR/RELAX) /        │
│    Bayesian Inference + Deep Learning                     │
├─────────────────────────────────────────────────────────┤
│ 6. Optimization  优化方法                                 │
│    Gradient Descent 隐式偏差 / Duality(KKT+Farkas) /     │
│    Conjugate Gradient / Softmax 重参数化                  │
├─────────────────────────────────────────────────────────┤
│ 7. Application Areas  应用领域                             │
│    3D 几何(CV)/ RL(DQN+MCTS+Policy Gradient) /          │
│    NLP(Word2Vec+GloVe+Fasttext+Seq2Seq+Attention) /    │
│    Recommendation System / Data Science                   │
└─────────────────────────────────────────────────────────┘
```

**关键观察**:仓库里没有「机器学习入门」「深度学习入门」这种目录。作者把基础数学单独成册,但默认读者已经知道什么是梯度下降、什么是矩阵、什么是概率分布。整个仓库的隐含读者画像是:数学系本科 + 想要补 ML 研究直觉的研究生 + 工业界想补理论的工程师。

## 三、Learning Theory:研究生课程的硬骨头

仓库里最特殊的一部分是顶部的 **Learning Theory Classes**——这门课在大多数本科 CS 课程里根本不开,通常只出现在顶级 PhD 项目第一年的学习理论课里:

- **Class 1: Introduction** — 18 页 PDF
- **Class 2: Concentration Inequality** — 浓度不等式(Markov/Chebyshev/Hoeffding/Chernoff/Bernstein),42 页
- **Class 3: Rademacher Complexity** — Rademacher 复杂度的全套推导,1.1 MB(单章节最大)
- **Class 4: Neural Tangent Kernel (NTK)** — NTK 的核方法视角
- **Class 5: PAC Bayes** — PAC-Bayes 边界
- **Class 6: Johnson–Lindenstrauss lemma** — JL 引理

NTK 和 PAC-Bayes 是 2018 年后深度学习理论的两条主线。NTK 给了「为什么宽网络能梯度下降收敛」的数学答案;PAC-Bayes 给了「为什么过参数化能泛化」的边界。作者把它们和 Rademacher / JL 放在同一门课里,等于把 PhD 第一年的 learning theory 课压缩成了 6 个章节。

学完这部分,Rademacher 复杂度、PAC-Bayes 边界、JL 引理这三件工具就到位了——它们是 ICLR / ICML / NeurIPS 理论 track 论文的标配前置。比如 2024 年 NeurIPS 上关于 in-context learning 泛化界的论文,推导链条直接依赖 Rademacher 复杂度 + JL 引理;跳过这部分去读,只能看懂实验,看不懂证明。

## 四、贝叶斯非参:Dirichlet Process + DPP + HDP-HMM

仓库的另一个亮点是 **Advanced Probabilistic Models**——这是 HKBU 统计/机器学习方向博士的硬课:

- **Bayesian Non-Parametrics (BNP) basics**:Dirichlet Process (DP) / Chinese Restaurant Process / Slice sampling for DP
- **BNP extensions**:Hierarchical DP / HDP-HMM / Indian Buffet Process (IBP)
- **Completely Random Measure**(2015 早期草稿):Lévy-Khintchine representation / Compound Poisson / Gamma / Negative Binomial
- **Sample correlated integers from HDP and Copula**:作者 IJCAI 2016 论文的另一种推导(注:论文本身有 PDF 链接,但讲义版本「推导不同,故事相同」)
- **Determinantal Point Process (DPP)**:DPP 的边缘分布 / L-ensemble / 采样策略 / 作者「时变 DPP」研究
- **DPP Basics (updated)**:DPP 教程的重写版(无时间变化部分)

DPP 这块是作者自己的研究方向——他在 IJCAI 2016 上发了 Copula-DP 相关论文,讲义里 DPP 教程包含了「时变 DPP」研究的细节。其他章节是综合教学,DPP 这一节是作者自己写了 8 年的研究主题。开放讲义和传统教科书的区别就在这里:作者把自己研究领域的最深细节倾倒进去,而不只是复述教科书。

## 五、生成模型篇:从 VAE 到 Flow Matching 的完整时间线

Generative AI / Deep Learning Research 部分,把 2013 年以来的生成模型时间线串成了一条线:

- **Generative Models and Variational Inference**(单独的一篇综合教程,206 KB):MLE / ELBO(Evidence Lower BOund) / IWAE / VAE / 高斯混合 + Dirichlet 过程混合变分推断 / Stick-breaking VAE / Adversarial Variational Bayes / Normalizing Flows / Denoising Diffusion (SDE + Flow Matching)
- **Mathematics for Generative Adversarial Networks**:GAN / W-GAN 数学 / Info-GAN / Bayesian GAN
- **A survey of traditional and state-of-the-art Generative Models**:VAE / IWAE / NF / AVB / Mixture / DPMM / Flow Matching
- **Infinite Depth: NeuralODE and Adjoint Equation**:Neural ODE + 伴随方程

Flow Matching 在 2024 年之后成为 diffusion 模型训练的事实标准(Stable Diffusion 3 用 Rectified Flow,SDXL-Turbo 用 consistency flow),作者在 2023 年的 generative_models.pdf 里已经包含了这部分——仓库内容比大多数工业界实践领先 1-2 年。

## 六、State Space Model 与 Kalman Filter:被现代 LLM 时代重新发现的古典

State Space Model(SSM)章节讲 Kalman Filter 和 Hidden Markov Model(HMM):

> explain in detail of Kalman Filter (B站视频链接), (kalman_demo.m) 和 Hidden Markov Model (B站视频链接)

这段在 2024 年后变得格外珍贵——Mamba(State Space Model for Deep Learning)借鉴 SSM 的数学形式,把 A/B/C 矩阵做成可学习的 kernel。读懂了 Kalman Filter + HMM + Linear Dynamical Systems,基本就能读懂 Mamba 的设计动机。

作者在 SSM 章节里把 Kalman Filter 的预测/更新两阶段讲透——这恰好是 S4/Mamba 的核心代数结构(连续化后就是 `dx/dt = Ax + Bu`,离散化就是 SSM 的 recurrent 形式)。

## 七、3D 几何与计算机视觉:一份与博士合写的章节

仓库里唯一与 PhD 学生合作的部分:

> This section is co-authored with PhD student Yang Li

包括两章:**3D Geometry Fundamentals**(相机模型 / 内参外参 / 对极几何 / 三维重建 / 深度估计)和 **Recent Deep 3D Geometry based Research**(单图相机模型估计 / 多视图多人 3D 姿态 / GAN 3D 姿态 / Deep Structure-from-Motion / 深度学习深度估计)。

这两章覆盖了从经典多视图几何(Hartley-Zisserman 那一套)到深度学习 3D 视觉的完整时间线——NeRF / 3D Gaussian Splatting 没单独成节,但前面「Single image to Camera Model estimation」和「Deep Structure-from-Motion」是它们的直接前置。

## 八、强化学习:从 DQN 到 PPO/TRPO 的全部数学

强化学习章节同样扎实:

- **Reinforcement Basics**:MDP(Markov Decision Process) / Bellman / Deep Q-Learning(DQN)
- **Monte Carlo Tree Search**:MCTS + AlphaGo 学习算法(3.6 MB,作者最大的讲义之一)
- **Policy Gradient**:Policy Gradient Theorem + TRPO(Trust Region Policy Optimization) + Natural Gradient + PPO(Proximal Policy Optimization) + Conjugate Gradient Algorithm

作者在 Policy Gradient 章节明确写出 TRPO 信任域优化的数学推导——Natural Gradient + Conjugate Gradient 联立求 step direction。这是 PPO 之前的算法,但没有 TRPO 的推导就读不懂 PPO 的动机。大多数 RL 教程跳过 TRPO 直接讲 PPO,作者把它放进来了——说明仓库的目标是让学生具备读论文细节的数学底子,而不只是调 stable-baselines 超参。

## 九、Optimization 与 Softmax 重参数化:细节里的工程智慧

Optimization 章节:

- **Gradient Descent Research**:梯度下降的隐式偏差(Implicit Bias)和隐式正则化(Implicit Regularization)——2018 年后深度学习理论的核心问题之一
- **Duality**:Lagrangian / 拉格朗日对偶 / 对偶函数 / KKT(Karush-Kuhn-Tucker)条件 / SVM 示例 / Farkas 引理
- **Conjugate Gradient**:共轭梯度下降快速解释

DeeCamp 2019 讲义:**Story of Softmax**——Softmax 属性 + 不需要计算分母的 softmax 估计 + 概率重参数化 Gumbel-Max trick + REBAR 算法。

Gumbel-Max + REBAR 是离散潜变量模型的核心可微分技巧——VAE 处理离散 token 时必须用它。这部分在 2024 年的工业界 LLM 训练中仍然有用(RLHF 里 reward model 不需要,但 RL 中 action 采样是离散的)。

## 十、Sinovation DeeCamp:讲义里的「实战课」

DeeCamp 是创新工场 2018-2019 年的 AI 训练营。袁晓鹏在 2018 年和 2019 年分别讲过两场:

- **DeeCamp 2019**:Story of Softmax
- **DeeCamp 2018**:When Probabilities meet Neural Networks(EM + 矩阵胶囊矩阵 / DPP + 神经网络压缩 / Kalman Filter + LSTM / 模型估计 + 二分类)

这两场是讲义集里最实战的两章——不讲理论推导,讲的是「如果你是工程师,这些数学工具怎么用」。

## 十一、transformer.pdf 实际在讲什么

仓库里 `transformer.pdf`(659 KB)是一份值得单独拆开看的讲义。它不是 2017 年那篇 "Attention Is All You Need" 的复述,而是 2024 年后修订过的版本——内容覆盖 Self-Attention 推导、Multi-Head Attention 的维度账、KV Caching 的内存与延迟分析、Rotary Position Embedding(RoPE)的推导,以及 DeepSeek Multi-Head Latent Attention(MLA)的低秩 KV 压缩。

章节大致结构可以这样推断:

1. **Self-Attention 基础**:Q/K/V 矩阵的维度推导,scaled dot-product attention 里 √d_k 缩放的方差论证(和原论文一致但补了完整推导)
2. **Multi-Head Attention**:拆头后的参数量计算——每个 head 的 Q/K/V 维度 d_k = d_model / h,总参数量不变,但为什么拆头有效(不同 head 关注不同子空间)
3. **KV Caching**:推理时 K/V 矩阵可以缓存,避免重复计算;但内存随序列长度线性增长——这是 vLLM / PagedAttention 要解决的核心瓶颈。讲义里会给一个具体的 FLOPs 对比:不缓存时每步 O(n²),缓存后每步 O(n)
4. **Rotary Position Embedding (RoPE)**:用旋转矩阵编码位置信息,核心公式是 q_m · k_n = Re(q̃_m · k̃_n*),其中 q̃ 是复数旋转后的 query。Decoupled RoPE 把 cos/sin 分离编码,使得位置信息可以跨 head 共享——这部分推导在 Su Jin 的原始博客之后才进讲义
5. **DeepSeek MLA**:这是 2024 年 DeepSeek-V2 才提出的注意力机制,核心思想是把 KV cache 压缩到低秩空间。MLA 的公式:先投影 `c_KV = W_DKV · h_t`,其中 `W_DKV ∈ ℝ^(d×r)` 且 `r << d`(DeepSeek-V2 取 r = 512,d = 7168),推理时只缓存 `c_KV`(r 维)而非完整的 K/V(d 维),再通过 `W_UK` 上采样恢复。结合 decoupled RoPE,MLA 把 KV cache 压缩到原来的约 7%

这份讲义同时涵盖 2017 年的原始 Transformer 和 2024 年的前沿 MLA,说明作者不是 2018 年写完就放着——**他在紧跟每一代架构的核心数学变化**。如果你只看一份 PDF 来判断这个仓库值不值得读,选 transformer.pdf。

## 十二、与其他 ML 教学资源的横向对比

把 roboticcam 放在主流 ML 教学资源的坐标系里:

| 维度 | roboticcam | fast.ai | 李宏毅 | 吴恩达 Coursera | 李沐 d2l |
|---|---|---|---|---|---|
| 数学深度 | ★★★★★(NTK/PAC-Bayes/BNP) | ★★★(实用导向) | ★★★★(推导完整) | ★★(算法导向) | ★★★ |
| 代码示例 | MATLAB 为主 + Python | PyTorch 完整 | 无代码,讲义+视频 | Octave/MATLAB | PyTorch/MXNet |
| 维护周期 | 2018-至今(8 年) | 2017-至今 | 2017-至今 | 2011-至今 | 2017-2020 |
| License | ❌ 未声明 | Apache-2.0 | YouTube CC | Coursera 闭源 | Apache-2.0 |
| Learning Theory | ✅(6 章) | ❌ | ✅(部分) | ❌ | ❌ |
| BNP/DPP | ✅(5 章) | ❌ | ❌ | ❌ | ❌ |
| SSM/Kalman | ✅(深度) | ❌ | 部分 | ❌ | ❌ |
| 适合人群 | 研究生/补理论 | 工业入门 | 入门-中级 | 入门 | 入门-中级 |

roboticcam 的不可替代点是 **BNP / DPP + Learning Theory 的完整覆盖**——fast.ai、李宏毅、吴恩达、李沐的教材全都没有这块内容。如果你要读 NeurIPS / ICLR 理论 track 的论文,Rademacher 复杂度和 PAC-Bayes 是标配前置知识,但主流教学资源里只有 roboticcam 把它们单独成章教。换言之,这个仓库的定位是**「教完之后你能读论文」**,而其他四个的定位是**「教完之后你能跑模型」**。

## 十三、License 缺位的工程含义

README 里没有声明任何开源 license(MIT / Apache / GPL / CC 均无)。这不是吹毛求疵——在法律上,没有 license 意味着默认 "All Rights Reserved",即使代码和 PDF 公开在 GitHub 上。这带来三个具体问题:

1. **不能合法 fork 进自己的项目**——如果你想基于这些讲义做一套中文翻译版,或者改编成公司内训材料,严格来说需要逐封邮件向袁老师申请授权
2. **不能二次分发**——翻译成其他语言、做衍生讲义、放进自己的课程网站,都需要单独许可
3. **工业团队引用受限**——公司内部的合规流程通常要求素材有明确 license,没有 license 的仓库会被法务标记为「不可引用」

对比 fast.ai(Apache-2.0)和李沐 d2l(Apache-2.0),两者都允许商用和二次分发。roboticcam 的内容深度高于这两者,但 license 缺位限制了它的传播半径。

**修复建议**:如果袁老师看到这篇文章,建议补 **CC-BY-SA 4.0**(Creative Commons Attribution-ShareAlike 4.0)——讲义友好的 license,允许商用和衍生,唯一约束是衍生作品必须用相同 license 开放。或者 **CC-BY-NC-SA 4.0**,禁止商用但允许学术自由使用。一旦声明,这个仓库就是中英 ML 教学领域 license 最干净的开放资源之一。

## 十四、与大学课程的关键差异

很多 ML 仓库(包括吴恩达的 coursera、fast.ai、李宏毅的机器学习)在讲「入门 + 实战」——目标是让你快速跑通模型。

袁晓鹏的仓库做的是相反的事:假设你已经会跑模型,然后告诉你模型的数学骨架。三个差异:

1. **Learning Theory 占顶部 6 章**——绝大多数教学仓库跳过这块,因为它「对找工作没用」
2. **BNP + DPP + Copula 单独成节**——研究级内容,其他教学仓库没有
3. **每个公式都有 demo 代码**——但 demo 是 MATLAB(`.m` 文件),不是 Python / Jupyter。这反映了作者的工程背景(本科控制 / MATLAB 重度用户,PhD 之后转向 Python ML)

## 十五、怎么用这个仓库

按作者的设计,推荐阅读顺序:

```
Week 0  : Foundation Math 6 章(可选,如果数学忘光了)
Week 1  : Probability / Monte Carlo / MCMC / Particle Filter
Week 2  : EM 收敛 + Variational Bayes + State Space Model
Week 3  : Generative Models(VAE/NF/Diffusion/Flow Matching)
Week 4  : Transformer + GAN + NeuralODE
Week 5  : Optimization(Duality/CG/Implicit Bias)
Week 6  : Learning Theory(Concentration/Rademacher/NTK/PAC-Bayes)
Week 7  : BNP(Dirichlet/IBP/HDP-HMM/DPP)
Week 8+ : 选方向(3D/RL/NLP/Recommendation)
```

Learning Theory 放在第 6 周而不是第 1 周——这是经过设计的顺序。先学具体的算法(MCMC / EM / VAE),再回头看理论为什么成立(Concentration / Rademacher),最后回到研究前沿(BNP / DPP)。这条路径遵循研究型学习的经典节奏:具体 → 理论 → 前沿。

如果你是工业界从业者想补理论,跳过 Week 0,直接 Week 1 开始。如果你是研究生,按作者顺序来。如果你只是想读懂 ICLR 理论 track,Week 4 + Week 5 + Week 6 必读。

## 十六、它对中国 ML 教育的真正意义

袁晓鹏的仓库不是一个网红项目——它是一位研究者 8 年不间断的教学工程。2018 年建仓,2026 年还在 commit,8 年累计 72 份 PDF + 8 份 PPTX,平均每年新写 9 份讲义。一位教授把自己研究领域的全部数学骨架,无偿开放给中文世界。

它的价值不在 GitHub 10k stars——那是结果,不是目标。它的价值在于:让一个大陆或者港台的本科生,只要愿意花 8 周认真读完 72 份 PDF,就能具备读懂 NeurIPS 理论 track 论文的数学底子。这件事在中国大陆和港台的现有大学课程里很难做到——学习理论、BNP、DPP 这些内容散落在不同教授的不同课程里,没有一个连贯体系把它们串起来。

至于它值不值得读——作者在 README 末尾留了 PhD 招生邮箱 `xuyida@hkbu.edu.hk`。读懂这个仓库,理论上你就有资格申请他的 PhD。

---

## 参考

- 仓库:[github.com/roboticcam/machine-learning-notes](https://github.com/roboticcam/machine-learning-notes)(10.1k stars / 1.8k forks / 2018-至今 / 72 PDFs + 8 PPTXs + 1 Jupyter)
- 作者:袁晓鹏(Xu Yi-da),香港浸会大学(HKBU)计算机科学系副教授,前悉尼大学 / 阿德莱德大学(澳大利亚)
- 在线直播:每周日 20:30 微信群 / 每 2-3 周 Zoom 英文(HK 19:00,meetup 报名)
- 视频:YouTube / B 站 / 优酷 三处都存
- 配套代码:[github.com/roboticcam/matlab_demos](https://github.com/roboticcam/matlab_demos) + [github.com/roboticcam/python_machine_learning](https://github.com/roboticcam/python_machine_learning)
- 关键研究:袁晓鹏 IJCAI 2016 [Copula DP](https://www.ijcai.org/Proceedings/16/Papers/210.pdf) / 时变 DPP
