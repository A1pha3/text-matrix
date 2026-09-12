---
title: "从零手写神经网络：Karpathy 的 nn-zero-to-hero 到底在教什么"
date: "2026-06-02T12:00:00+08:00"
slug: karpathy-nn-zero-to-hero-neural-networks-course
github_repo: "karpathy/nn-zero-to-hero"
source_key: "gh:karpathy/nn-zero-to-hero"
description: "Andrej Karpathy 的 nn-zero-to-hero 不是在教你怎么用 PyTorch，而是在逼你面对一个事实：如果你说不清 loss.backward() 里每一层梯度是怎么算出来的，那你其实并不理解自己训练的模型。8 个 Lecture，从手动反向传播一路写到 GPT。"
tags: ["Karpathy", "PyTorch", "GPT", "Transformer"]
categories: ["技术笔记"]
author: 钳岳星君
---

Andrej Karpathy 的 [Neural Networks: Zero to Hero](https://github.com/karpathy/nn-zero-to-hero)（GitHub 约 2.2 万 star，MIT 许可证）把 PyTorch 的高级 API 扔到一边，让你从 `numpy` 数组和 Python 原始运算开始，一行一行地把神经网络里真正在发生的事写出来。它不教你调参——它逼你搞清楚 `loss.backward()` 到底做了什么。

这门课的教学主张可以浓缩成一句话，也是 Karpathy 在访谈里反复说的：**如果不能从零构建它，就不算理解它。** 整门课都是这句话的执行——先手动实现 autograd，再关掉 autograd 手动反传，最后在理解梯度的情况下从零写 GPT。

课程的分水岭在第五讲。前四讲你用 PyTorch 的自动微分写模型，第五讲 Karpathy 把 autograd 关掉，让你手动把梯度从 Cross Entropy Loss 一路反推到 Embedding 表。做完这一讲，反向传播对你来说不再是「autograd 替我算的」，而是「我知道梯度经过哪些层、在哪被压缩、最终落在谁身上」。

## 学习目标

读完这篇文章，下面几个问题应该有答案：

- 这 8 个 Lecture 各自解决什么问题，它们之间怎么串成一条线
- 为什么 L5（手动反向传播）是整门课最关键的一讲
- 一个训练样本在课程的不同阶段经历了什么变换
- 根据你的背景，该选完整路径、核心路径还是查漏补缺路径
- 这门课不适合谁，以及学完后下一步往哪走

## 课程全景：8 个 Lecture 如何串成一条线

这 8 个 Lecture 之间有一条从手工求导到生成文本的连续路径，每一步都在为下一步铺路。先把全景图放在前面，再逐讲拆开。

| 讲 | 视频时长 | 名字 | 你最终写出来的东西 |
|----|---------|------|-------------------|
| L1 | 2h25m | micrograd | 一个约 150 行的 autograd 引擎 |
| L2 | 1h57m | makemore Part 1 | 一个 bigram 字符级语言模型 |
| L3 | 1h15m | makemore Part 2 | 一个 MLP 语言模型 + 完整训练方法论 |
| L4 | 1h55m | makemore Part 3 | 激活值/梯度统计诊断 + BatchNorm |
| L5 | 1h55m | makemore Part 4 | 关掉 autograd 的徒手反向传播 |
| L6 | 56m | makemore Part 5 | 一个 WaveNet 风格的层次化 CNN |
| L7 | 1h56m | Let's build GPT | 从零实现一个 GPT 级别 Transformer |
| L8 | 2h13m | GPT Tokenizer | 一个 GPT-2 兼容的 BPE 分词器 |

时长取自课程官方 syllabus；加上自己动手重写代码的时间，完整走一遍的实际投入大约是视频时长的两倍。

**两条主线，在 L5 交汇：**

| 主线 | 覆盖 Lecture | 核心问题 |
|------|-------------|----------|
| 梯度流 | L1, L4, L5 | 梯度到底是怎么流回去的？ |
| 生成流 | L2, L3, L6, L7, L8 | 字符怎么变成 token，token 怎么变成下一个 token？ |

前半段（L1-L5）在回答「梯度流」问题：autograd 怎么工作、激活值和梯度在深层网络里怎么分布、手动反推时每一步的 `dL/dx` 长什么样。后半段（L6-L8）在回答「生成流」问题：从 bigram 到 MLP 到 CNN 到 Transformer，模型能看到的上下文越来越长，生成质量随之提升。

两条线交汇在 L5——你在那讲已经用手算过一轮梯度了，所以到了 L7 看 Transformer 的 Multi-Head Attention 时，脑子里跑的不再是「黑箱调参」，而是「这个矩阵乘完，梯度会从哪里进来、从哪里出去」。

## 逐讲拆解：每节在解决什么问题

### L1 — micrograd：把链式法则写成能跑的代码

Karpathy 从零实现了一个叫 `Value` 的 Python 类。每个 `Value` 记住自己是由哪些运算产生的，反向传播时沿着这张计算图逐节点回填梯度。

听这一讲的时候，链式法则会从公式变成一行能跑的代码：`self.grad += local_gradient * upstream_gradient`。Jupyter 里画出来的 `a * b + c` 计算图，以及 `backward()` 逐节点更新梯度的过程，比任何教材里的示意图都直观。

这一讲视频约 2.5 小时，核心产出是一个不到 150 行的 autograd 引擎。它和 Karpathy 单独维护的 [micrograd](https://github.com/karpathy/micrograd) 仓库是同一套思想的不同实现——读懂这一讲的版本后，再去看独立仓库源码，会发现每一行都认识。

### L2 — makemore Part 1：语言模型的第一个训练循环

先用纯统计计数实现一版 bigram——数出每个字符后面跟着各字符的次数，直接归一化成概率；再用 PyTorch 的 `torch.Tensor` 把同一个模型写成神经网络版本。输入是美国社保局（ssa.gov）发布的 2018 年最常见名字清单，约 3.2 万个英文名字，模型要学的是：给定前一个字符，下一个字符最可能是什么。

这节的关键不在模型本身（bigram 太简单了），而在**训练循环的骨架**：怎么把字符映射成整数索引、怎么算 negative log likelihood loss、怎么从训练好的分布里采样生成新名字。这套骨架会贯穿后续所有 Lecture。

跟着做完，模型会从乱码变成「看起来有点像人名的字符串」，loss 曲线在下降——然后卡住，因为 bigram 只能看一个字符的上下文。这个「卡住」的体验本身就是下一讲的动机。

### L3 — makemore Part 2：MLP 与训练的工程直觉

把 bigram 扩展成多层感知机（MLP），同时引入一整套训练方法论：

- **Train / Dev / Test 划分**：为什么你不能用训练集评估模型
- **学习率调参**：太大发散、太小收敛太慢，Karpathy 手动试了几个数量级给你看效果
- **过拟合与欠拟合**：Train loss 和 Dev loss 之间的 gap 是怎么拉开的
- **超参数搜索**：不靠自动工具，而是用简单的网格搜索感受每个参数的影响

这讲更重要的收获在训练循环里：你会开始建立「看 loss 曲线判断问题」的直觉——Train loss 不动、Dev loss 和 Train loss 之间的 gap 拉开、loss 震荡——每种现象背后对应什么原因，Karpathy 都当场改参数演示了一遍。

### L4 — makemore Part 3：神经网络内部的健康诊断

把 MLP 拆开来看：前向传播时每层激活值的均值和标准差是什么样的，反向传播时每层梯度的规模又是多少。

然后引入一个真实问题：深层网络的激活值分布和梯度规模如果不加控制，训练会变得非常脆弱——梯度消失让你训不动，梯度爆炸让 loss 满天飞。

Batch Normalization 就是在这里登场的。Karpathy 不仅讲了 BN 的公式，还让你在代码里看到 BN 前后激活值分布的变化。先看到问题，再看到解法生效——比直接背 BN 公式有效得多。

### L5 — makemore Part 4：反向传播的「压力测试」

**难度最高的一讲。** 把一个带 BatchNorm 的 2 层 MLP 拿出来，关掉 PyTorch 的 autograd，从 Cross Entropy Loss 开始，手动把梯度一层一层往回推：Loss → 线性层 → Tanh → BatchNorm → 线性层 → Embedding。

每一步都要手写出 `dL/dx` 的表达式，然后用 PyTorch 的 autograd 结果做对照验证。你会反复遇到「这里少了一个求和」「那个维度广播没考虑」的错误——然后修掉它们。

做完这一讲你不会从此放弃 autograd 改用手写反向传播。但你会获得一种对梯度的物理直觉：路过 BatchNorm 时梯度被压缩了多少、穿过 Tanh 饱和区时梯度还剩多少、反向推到 Embedding 层时梯度是均匀分布还是集中在少数 token 上。这些细节在你以后 debug 训练问题时，会反复用上。

### L6 — makemore Part 5：卷积与层次化架构

引入 CNN 架构，参考了 DeepMind 2016 年 WaveNet 的层次化设计：用树状结构逐步扩大感受野，让浅层看局部模式、深层看长距离依赖。

同时引入 `torch.nn` 模块的底层用法，以及一种重要的开发习惯：一边读论文里的公式，一边对着 PyTorch 文档把公式翻译成代码。Karpathy 在视频里直接打开文档现场查 API——他想让你看到，即使是他也需要查文档。

### L7 — Let's build GPT：Transformer 的完整实现

从零实现一个 GPT 级别的 Transformer。不是调 `transformers` 库，是手写 Multi-Head Attention、FeedForward、LayerNorm、残差连接和整个 decoder-only 架构。

这节课建立在前面所有积累之上：你已经理解了张量运算（L2）、训练循环（L2-L3）、激活函数与归一化（L4）、梯度流动（L5），所以当你看到 Self-Attention 里 `Q @ K^T / sqrt(d_k)` 这行代码时，你脑子里同时在想三件事：

1. 这个矩阵乘法的输出形状是什么
2. softmax 之后的梯度会怎么流回去
3. 为什么除以 sqrt(d_k) 而不是别的数

### L8 — Let's build the GPT Tokenizer：分词器的秘密

从零实现 BPE（Byte Pair Encoding）分词算法。这节解开了一个让很多人困惑的现象：为什么 ChatGPT 有时候数不对单词里的字母数？为什么中文被切成奇怪的碎片？

答案全在 tokenizer 里。Karpathy 带着你从字节级开始，逐步合并最高频的字节对，最终构建出和 GPT-2 兼容的分词器。做完你会理解：LLM 看到的从来不是「文字」，而是一串整数 ID。很多奇怪的模型行为，根子在 tokenization 这一步就已经种下了。

## 一个训练样本在课程里的完整旅程

把整个课程串起来看，一个名字 `"Alice"` 在课程的不同阶段会经历不同的处理：

1. **字符映射（L2 建立）**：名字被按字符拆开，每个字符对应一个整数索引。字符级模型用的是 27 个符号——26 个字母加上一个表示名字开头/结尾的边界符，`"Alice"` 因此变成 6 个索引（5 个字母 + 1 个结束符）
2. **预测下一个字符（L2-L3）**：bigram 只看前一个字符，MLP 把窗口扩到前三个字符。模型在 `"A"` 之后猜下一个最可能是 `"l"` 还是别的
3. **反向传播（L1、L5）**：猜错之后，梯度从 loss 一路回流，准确落到每个 Embedding 向量和线性层的权重上
4. **BatchNorm（L4）**：让更深的网络在训练过程中激活值和梯度保持稳定，不会中途训不动
5. **CNN（L6）**：层次化卷积把模型的有效视野从 3 个字符扩大到几十个字符，能捕捉更长距离的名字结构
6. **Transformer（L7）**：注意力机制让 `"ice"` 可以直接关联到更早的 `"Al"`，跨过中间所有字符
7. **BPE（L8）**：输入从字符换成子词 token——这才是 GPT 实际吃进去的东西

同一个名字在课程的不同阶段被反复处理，每次加入新机制后 loss 都在下降。Karpathy 刻意选了同一个数据集贯穿整门课——每一次架构升级的效果都直接体现在 loss 曲线上，而不是换一套数据让你重新适应。

## 怎么学：三条路径

### 完整路径（约 30 小时）

按 L1 → L8 顺序走，每个 Notebook 都亲手敲一遍。八讲视频本身约 14.5 小时，再加上重写代码和消化，实际投入大约是这个数的两倍。适合想扎扎实实过一遍的人。

### 核心路径（约 17 小时）

**L1 + L5 + L7 + L8**。这四讲覆盖了这门课最有区分度的内容，视频合计约 8.5 小时，按完整路径同样的投入比例，实际大约 17 小时：

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

## 自测清单

做完课程后，用下面这些问题检验你的理解程度。如果你能不看笔记回答出大部分，说明这门课的核心内容已经内化了。

**L1-L2（基础）**
- [ ] 不看代码，画出 `a * b + c` 的计算图，标注每个节点的前向值和反向梯度
- [ ] 解释 negative log likelihood loss 的计算过程：从概率到 loss 的每一步

**L3-L4（训练直觉）**
- [ ] Train loss 不降、Dev loss 和 Train loss 之间的 gap 持续拉大、loss 震荡——这三种现象分别对应什么问题
- [ ] BatchNorm 在前向传播和反向传播时分别做了什么

**L5（核心压力测试）**
- [ ] 手写出 Cross Entropy Loss 对 logits 的梯度表达式
- [ ] 解释梯度穿过 Tanh 激活函数时为什么会被压缩

**L7（Transformer）**
- [ ] 写出 Self-Attention 中 `Q @ K^T / sqrt(d_k)` 每一步的矩阵形状
- [ ] 解释为什么除以 `sqrt(d_k)` 而不是 `d_k`

**L8（分词器）**
- [ ] 描述 BPE 算法的一次合并迭代：怎么找到最高频字节对、合并后词表发生了什么变化
- [ ] 解释为什么 tokenizer 会导致中文被切成奇怪的碎片

## 常见问题

**Q: 没有 GPU 能学完这门课吗？**

能。Karpathy 刻意控制了数据规模（L2-L6 以同一个约 3.2 万个名字的人名数据集为主，L7 用的是莎士比亚文本），所有计算都可以在 CPU 上完成。L1 只需要 `numpy`。

**Q: 需要多少数学基础？**

矩阵乘法、链式法则、softmax 的定义。如果你看到 `softmax(logits)` 能写出公式，看到 `dL/dx = dL/dy * dy/dx` 不觉得陌生，就够用了。L5 会用到一些矩阵微积分，但 Karpathy 每一步都拆得很细，跟着算就行。

**Q: 和吴恩达的 Deep Learning Specialization 怎么选？**

吴恩达的课从数学推导出发，适合想系统建立理论框架的人。Karpathy 的课从代码出发，适合想建立工程直觉的人。两者不是替代关系——如果你时间充裕，先上吴恩达建立数学基础，再用 Karpathy 的课把公式变成代码直觉。

**Q: L5 太难了，能跳过吗？**

可以，但跳过 L5 之后再看 L7 的 Transformer，你对梯度的理解会停在「autograd 帮我算了」的层面。L5 不是让你以后手写反向传播，而是让你以后再看到 `loss.backward()` 时，脑子里有一个清晰的梯度流动图。如果时间确实紧，可以先做 L1+L7+L8，回头再补 L5。

**Q: 学完这门课能直接上手训练 GPT 吗？**

不能。这门课教你的是从零实现一个微型 GPT 级别的 Transformer，不是在大规模数据上训练可部署的模型。学完后你理解的是 Transformer 的内部机制，离生产级训练还差分布式训练、数据工程、RLHF 等一大截。但这门课给的基础，是你理解那些高级话题的前提。

## 学完之后

做完这 8 讲再回到日常工作里去调 `model.fit()` 和 `trainer.train()`，你排查 loss 不下降、梯度爆炸、学习率不合适这些问题的路径会完全不一样——你不是在文档和报错信息之间来回搜，而是在脑子里回溯梯度流：哪一层可能把梯度截断了，哪个初始化让激活值漂了。

用一句话决定现在该不该开始：

- **现在就该开始**：你在写或调模型训练代码，但 loss 出问题时只能靠猜、靠试参数。这门课给你一套「先想梯度流，再动手改」的排查顺序。
- **可以再等等**：你的工作以业务开发为主，短期不会碰训练细节。先继续用框架和现成工具，等真正需要 debug 训练时再回来补，课程不会过期。
- **从哪开始**：时间紧就按核心路径（L1 + L5 + L7 + L8）走，时间充裕就完整过一遍。

学完之后，下一步可以往两个方向走：

- **纵向深入**：读 GPT-2 和 GPT-3 的论文原文，你已经有了手写 Transformer 的经验，论文里的公式不再抽象
- **横向扩展**：看 Karpathy 的 [makemore](https://github.com/karpathy/makemore) 和 [nanoGPT](https://github.com/karpathy/nanoGPT)，把课程里的概念迁移到更完整的实现上

---

下次你敲 `loss.backward()` 的时候，你会知道从那行代码出发，梯度正在穿过哪些层、经过哪些非线性变换、最终落在哪些参数上。这不是一个抽象的理解——是你在 L5 里亲手算过的那条路径。说到底，这门课想留给你的就是 Karpathy 那句话：如果不能从零构建它，就不算理解它。