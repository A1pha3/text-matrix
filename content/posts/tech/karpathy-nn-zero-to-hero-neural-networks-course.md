---
title: "从零手写神经网络：Karpathy 的 nn-zero-to-hero 到底在教什么"
date: "2026-06-02T12:00:00+08:00"
slug: karpathy-nn-zero-to-hero-neural-networks-course
description: "Andrej Karpathy 的 nn-zero-to-hero 不是在教你怎么用 PyTorch，而是在逼你面对一个事实：如果你说不清 loss.backward() 里每一层梯度是怎么算出来的，那你其实并不理解自己训练的模型。22.5k stars，8 个 Lecture，从手动反向传播一路写到 GPT。"
tags: [Neural Networks, Deep Learning, Karpathy, PyTorch, Jupyter Notebook, GPT, Backpropagation, Transformer, BPE, BatchNorm]
categories: ["技术笔记"]
author: 钳岳星君
---

市面上大多数深度学习教程在教你「怎么调库」。Andrej Karpathy 的 [Neural Networks: Zero to Hero](https://github.com/karpathy/nn-zero-to-hero)（22,500+ Stars，MIT 许可证）走的是另一条路：他把 PyTorch 的高级 API 扔到一边，让你从 `numpy` 数组和 Python 原始运算开始，一行一行地把神经网络里真正在发生的事写出来。

这门课真正的分水岭在第五讲。前四讲你在用 PyTorch 的自动微分偷懒，第五讲 Karpathy 把 autograd 关掉，让你手动把梯度从 Cross Entropy Loss 一路反推到 Embedding 表。做完这一讲的人都有一个共同的感受：之前以为自己懂反向传播，其实是 autograd 替你懂了。

## 课程全景：8 个 Lecture 如何串成一条线

这 8 个 Lecture 之间有一条从手工求导到生成文本的连续路径，每一步都在为下一步铺路：

```text
L1 micrograd        →  手工实现反向传播（纯 Python，无框架）
L2 makemore P1      →  用 PyTorch 写第一个 bigram 语言模型
L3 makemore P2      →  升级为 MLP，引入训练方法论
L4 makemore P3      →  诊断网络内部：激活值分布、梯度流、BatchNorm
L5 makemore P4      →  关掉 autograd，徒手反向传播穿过整个网络  ← 分水岭
L6 makemore P5      →  引入 CNN 架构（WaveNet 风格）
L7 Let's build GPT  →  从零实现 Transformer / GPT
L8 GPT Tokenizer    →  从零实现 BPE 分词器
```

前半段（L1-L5）在回答一个问题：「梯度到底是怎么流回去的？」后半段（L6-L8）在回答另一个：「字符是怎么变成 token、token 是怎么变成下一个 token 的？」

两条线交汇在 L5——你在那讲已经用手算过一轮梯度了，所以到了 L7 看 Transformer 的 Multi-Head Attention 时，脑子里跑的不再是「黑箱调参」，而是「这个矩阵乘完，梯度会从哪里进来、从哪里出去」。

## 逐讲拆解：每节在解决什么问题

### L1 — micrograd：把链式法则写成能跑的代码

Karpathy 从零实现了一个叫 `Value` 的 Python 类。每个 `Value` 记住自己是由哪些运算产生的，反向传播时沿着这张计算图逐节点回填梯度。

听完这一讲，链式法则对你来说不再是一个公式——你会亲眼看到它在计算图里变成 `self.grad += local_gradient * upstream_gradient` 这一行代码。你会在 Jupyter 里亲眼看着一个简单表达式 `a * b + c` 的计算图被画出来，然后看到 `backward()` 逐个节点更新梯度值。

这节约 2 小时，核心产出是一个不到 150 行的 autograd 引擎。Karpathy 后来把它拆成了独立仓库 [micrograd](https://github.com/karpathy/micrograd)。

### L2 — makemore Part 1：语言模型的第一个训练循环

用 PyTorch 的 `torch.Tensor` 实现一个 bigram 字符级语言模型。输入是一串名字（比如全世界的人名），模型要学的是：给定前一个字符，下一个字符最可能是什么。

这节的关键不在模型本身（bigram 太简单了），而在**训练循环的骨架**：怎么把字符映射成整数索引、怎么算 negative log likelihood loss、怎么从训练好的分布里采样生成新名字。这套骨架会贯穿后续所有 Lecture。

做完你会看到模型从乱码变成「看起来有点像人名的字符串」，loss 曲线在下降——然后卡住，因为 bigram 只能看一个字符的上下文。这个「卡住」的体验本身就是下一讲的动机。

### L3 — makemore Part 2：MLP 与训练的工程直觉

把 bigram 扩展成多层感知机（MLP），同时引入一整套训练方法论：

- **Train / Dev / Test 划分**：为什么你不能用训练集评估模型
- **学习率调参**：太大发散、太小收敛太慢，Karpathy 手动试了几个数量级给你看效果
- **过拟合与欠拟合**：Train loss 和 Dev loss 之间的 gap 是怎么拉开的
- **超参数搜索**：不靠自动工具，而是用简单的网格搜索感受每个参数的影响

这讲更重要的收获藏在训练循环的细节里：你会开始建立「看 loss 曲线判断问题」的直觉——Train loss 不动、Dev loss 和 Train loss 之间的 gap 拉开、loss 震荡——每种现象背后对应什么原因，Karpathy 都当场改参数给你演示了一遍。

### L4 — makemore Part 3：神经网络内部的健康诊断

把 MLP 拆开来看：前向传播时每层激活值的均值和标准差是什么样的，反向传播时每层梯度的规模又是多少。

然后引入一个真实问题：深层网络的激活值分布和梯度规模如果不加控制，训练会变得非常脆弱——梯度消失让你训不动，梯度爆炸让 loss 满天飞。

Batch Normalization 就是在这里登场的。Karpathy 不仅讲了 BN 的公式，还让你在代码里看到 BN 前后激活值分布的变化。这种「先看到问题，再看到解法生效」的节奏，比直接背 BN 公式有效得多。

### L5 — makemore Part 4：反向传播的「压力测试」

**难度最高的一讲。** 把一个带 BatchNorm 的 2 层 MLP 拿出来，关掉 PyTorch 的 autograd，从 Cross Entropy Loss 开始，手动把梯度一层一层往回推：Loss → 线性层 → Tanh → BatchNorm → 线性层 → Embedding。

每一步都要手写出 `dL/dx` 的表达式，然后用 PyTorch 的 autograd 结果做对照验证。你会反复遇到「这里少了一个求和」「那个维度广播没考虑」的错误——然后修掉它们。

做完这一讲你不会从此放弃 autograd 改用手写反向传播——但你会获得一种对梯度的物理直觉：路过 BatchNorm 时梯度被压缩了多少、穿过 Tanh 饱和区时梯度还剩多少、反向推到 Embedding 层时梯度是均匀分布还是集中在少数 token 上。这些细节在你以后 debug 训练问题时，会反复用上。

### L6 — makemore Part 5：卷积与层次化架构

引入 CNN 架构，参考了 DeepMind 2016 年 WaveNet 的层次化设计：用树状结构逐步扩大感受野，让浅层看局部模式、深层看长距离依赖。

同时引入 `torch.nn` 模块的底层用法，以及一种重要的开发习惯：一边读论文里的公式，一边对着 PyTorch 文档把公式翻译成代码。Karpathy 在视频里直接打开文档现场查 API，这是刻意为之——他想让你看到，即使是他也需要查文档。

### L7 — Let's build GPT：Transformer 的完整实现

从零实现一个 GPT 级别的 Transformer。不是调 `transformers` 库，是手写 Multi-Head Attention、FeedForward、LayerNorm、残差连接和整个 decoder-only 架构。

这节课建立在前面所有积累之上：你已经理解了张量运算（L2）、训练循环（L2-L3）、激活函数与归一化（L4）、梯度流动（L5），所以当你看到 Self-Attention 里 `Q @ K^T / sqrt(d_k)` 这行代码时，你脑子里同时在想三件事：

1. 这个矩阵乘法的输出形状是什么
2. softmax 之后的梯度会怎么流回去
3. 为什么除以 sqrt(d_k) 而不是别的数

这三件事，是调 `model.generate()` 的人永远不会想到的。

### L8 — Let's build the GPT Tokenizer：分词器的秘密

从零实现 BPE（Byte Pair Encoding）分词算法。这节解开了一个让很多人困惑的现象：为什么 ChatGPT 有时候数不对单词里的字母数？为什么中文被切成奇怪的碎片？

答案全在 tokenizer 里。Karpathy 带着你从字节级开始，逐步合并最高频的字节对，最终构建出和 GPT-2 兼容的分词器。做完你会理解：LLM 看到的从来不是「文字」，而是一串整数 ID。很多奇怪的模型行为，根子在 tokenization 这一步就已经种下了。

## 一个训练样本在课程里的完整旅程

把整个课程串起来看，一个名字 `"Alice"` 在这个课程体系里会经历什么：

1. **L8 的分词器**把它切成 `["A", "l", "i", "c", "e"]`，映射成整数 ID `[37, 52, 45, 43, 49]`
2. **L2-L3 的 MLP** 只拿前一个字符预测下一个：看到 37，猜下一个最可能是 52
3. **L1 和 L5 的反向传播**保证猜错之后，梯度能准确到达每个 Embedding 向量、每个线性层的权重
4. **L4 的 BatchNorm** 保证 10 层 MLP 训下去不会梯度消失
5. **L6 的 CNN** 让模型能同时看到 `"Ali"` 三个字符的模式
6. **L7 的 Transformer** 让 `"ice"` 能直接注意到 5 个位置之前的 `"Al"`，跨越中间所有字符

同一个样本在课程的不同阶段被反复使用，每次加入新的机制后 loss 都在下降。这不是凑巧——Karpathy 刻意选了同一个数据集贯穿整门课，让每一次架构升级的效果都直接体现在 loss 曲线上，而不是换一套数据让你重新适应。

## 怎么学：三条路径

### 完整路径（约 30 小时）

按 L1 → L8 顺序走，每个 Notebook 都亲手敲一遍。适合想扎扎实实过一遍的人。

### 核心路径（约 15 小时）

**L1 + L5 + L7 + L8**。这四讲覆盖了这门课最有区分度的内容：

- L1 给你 autograd 的底层直觉
- L5 把这个直觉压到极限——手动反传穿过整个网络
- L7 让你在真正理解梯度的情况下实现 Transformer
- L8 让你看清 LLM 输入端的真相

L2-L4 和 L6 可以在做完核心路径后回头补，不会影响对主线的理解。

### 查漏补缺路径

如果你已经用过 PyTorch 但总觉得对反向传播没底，直接看 L5。如果你在调 Transformer 但说不清 Self-Attention 的梯度流，看 L7 的前半部分。如果被 tokenizer 的诡异行为搞过心态，看 L8。

## 谁适合、谁不适合

**适合：**

- 用过 PyTorch 但觉得「能跑通但说不清原理」的工程师
- 看过吴恩达课程、想从数学推导转到代码直觉的人
- 准备读 GPT 论文但需要先把地基打牢的研究者

**不适合：**

- Python 都写不利索的纯新手（建议先写三个月 Python）
- 需要三天内上线一个业务模型的人（直接用 HuggingFace + LoRA）
- 只想了解 AI 概念、不打算写代码的产品或管理人员

**一个实用的判断标准：** 如果你看到 `x @ w + b` 这行代码时，能在脑子里画出 x 是 `(32, 768)`、w 是 `(768, 10)`、结果是 `(32, 10)`，那你可以直接开始。如果不行，先找本线性代数教材把矩阵乘法练熟。

## 环境搭建

```bash
git clone https://github.com/karpathy/nn-zero-to-hero.git
cd nn-zero-to-hero

python3 -m venv nn-env
source nn-env/bin/activate
pip install jupyter numpy torch

cd lectures/micrograd
jupyter notebook
```

L1 只需要 `numpy`，不需要 GPU。L2 开始用 PyTorch，但所有计算都可以在 CPU 上跑——Karpathy 刻意控制了数据规模，不会让你的笔记本风扇起飞。

一个实操建议：**不要复制粘贴代码。** 每个 Notebook 都新建一个空白 `.py` 文件，看着视频一边暂停一边自己敲。抄一遍和看着抄一遍，对理解的影响不在一个量级。

## 延伸项目

课程中的核心组件被 Karpathy 拆成了独立仓库：

- [micrograd](https://github.com/karpathy/micrograd) — 约 150 行的 autograd 引擎，读完 L1 后去看源码，会发现每一行都认识
- [makemore](https://github.com/karpathy/makemore) — 字符级语言模型的完整实现，比课程里的版本更完善
- [minbpe](https://github.com/karpathy/minbpe) — BPE 分词器的独立实现，和 L8 配套

课程视频在 [YouTube](https://www.youtube.com/@AndrejKarpathy)，B 站有中文搬运。

## 学完之后

做完这 8 讲再回到日常工作里去调 `model.fit()` 和 `trainer.train()`，你排查 loss 不下降、梯度爆炸、学习率不合适这些问题的路径会完全不一样——你不是在文档和报错信息之间来回搜，而是在脑子里回溯梯度流：哪一层可能把梯度截断了，哪个初始化让激活值漂了。

下一步可以往两个方向走：

- **纵向深入**：读 GPT-2 和 GPT-3 的论文原文，你已经有了手写 Transformer 的经验，论文里的公式不再抽象
- **横向扩展**：看 Karpathy 的 [makemore](https://github.com/karpathy/makemore) 和 [nanoGPT](https://github.com/karpathy/nanoGPT)，把课程里的概念迁移到更完整的实现上

---

如果学完只带走一句话：下次你敲 `loss.backward()` 的时候，你会知道从那行代码出发，梯度正在穿过哪些层、经过哪些非线性变换、最终落在哪些参数上。知道这件事，和不知道这件事，是两种完全不同的工程师。