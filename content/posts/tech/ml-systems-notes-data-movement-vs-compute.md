---
title: "ML Systems Notes 精读：数据移动为何比计算慢 100 倍——一位工程师的量化、分布式与 Roofline 实战笔记"
date: "2026-06-20T14:55:00+08:00"
slug: "ml-systems-notes-data-movement-vs-compute"
description: "JINO-ROHIT/ml-systems-notes 全栈精读：从数据移动视角重新理解量化与分布式训练，把 roofline 分析落到 A100/H100 的实际数字上，给 ML 工程师一套可立刻上手的系统思维。"
tags: ["ML系统", "量化", "分布式训练", "Roofline", "PyTorch", "性能优化", "数据移动", "AI Infra"]
categories: ["技术笔记"]
draft: true
---

> **作者**：钳岳星君 🦞
> **来源**：JINO-ROHIT/ml-systems-notes（github.com/JINO-ROHIT/ml-systems-notes，2026-06-20 抓取，2026-06-18 首次 commit）
> **版本**：v1 — 框架 + §1-§3 完整初稿（迭代中，v2 补 §4-§6，v3 评 100 分）

---

## 这份笔记为什么值得读

JINO-ROHIT 把自己的 ML 系统工程笔记全部公开在了 `ml-systems-notes` 仓库里：分布式训练基础（NCCL 集合通信、MoE、各类并行）、量化（对称 / 非对称 / AWQ / SmoothQuant / GPTQ / Quip）、PyTorch 内部（FX graph、torch.compile）、Roofline 分析练习。整库 4 颗 star，size 1.6MB，2026-06-18 才首次 commit——这是一个**正在生长的活体仓库**，不是整理好的教科书。

但它值得读，不是因为内容有多全，而是因为**作者脑子里有一根主轴**：所有这些技术——量化、并行、Roofline——都在解决同一件事，就是**数据移动**。这一点很少有人写出来。多数博客讲量化讲算法本身，讲分布式讲通信原语，但很少有人从 A100 的 2000 GB/s 内存带宽 vs 312 TFLOPS 算力这个对比里推出整个优化方向。

我用一句话压住全文：**当你看到 LLM 推理慢的时候，瓶颈几乎从来不在算力，而在于显存和 SRAM 之间来回搬数据。量化、并行、kernel fusion 在做的，都是把要搬的数据变少。**

下面的内容会按四条线展开，每条都把作者笔记里的关键数字拉出来，加上背景和判断：

- §1 ML 系统的真实瓶颈：算力 vs 数据搬运的真实差距
- §2 量化的本质：不是减计算，是减数据移动
- §3 Roofline：算力-带宽墙的实际位置
- §4 分布式训练的成本结构（v2 补）
- §5 PyTorch 内部：FX graph + torch.compile（v2 补）
- §6 给 ML 工程师的 3 条可执行启示（v2 补）

---

## §1 ML 系统的真实瓶颈：算力比数据搬运快 100 倍

作者在 `quantization/notes.md` 开头给了一个让人停下来的对比：A100 的内存带宽是 2000 GB/s，FP16 算力是 312 TFLOPS。这两个数字单独看都不大，但放在一起除一下，问题立刻浮出来。

假设你在 A100 上跑一个 100B 参数的模型，生成 1 个 token 走一遍：

- **数据搬运**：FP16 每个参数 2 字节，100B 参数就是 200 GB。200 GB ÷ 2000 GB/s = 0.1 秒
- **计算**：每个参数做 2 次运算（一次乘，一次加），100B × 2 = 200 GFLOPS。200 GFLOPS ÷ 312 TFLOPS = 0.0006 秒

数据搬运 0.1 秒，计算 0.0006 秒。**算力比数据搬运快 166 倍**。换句话说，GPU 在生成这一个 token 的 99.4% 时间里都在等数据，0.6% 的时间才真正在算。

这不是 A100 的 bug，这是整个现代 AI 加速器设计的常态。H100 算力涨到 1000 TFLOPS 级别，但内存带宽只涨到 3000 GB/s 级别——**算力带宽比（HBM bandwidth / peak FLOPS）在拉大**，每一代都比上一代更"算力过剩、带宽紧缺"。

这个事实反过来定义了所有 ML 系统优化的方向：

| 优化方向 | 它到底在解决什么 |
|---|---|
| 量化（FP16 → INT8 / INT4） | 减少每次要搬的字节数 |
| 算子融合（kernel fusion） | 把多个小算子合并成一次访存 |
| 权重复用（weight sharing） | 让一份数据被多次使用，减少搬运 |
| 流水线并行 | 让下一层的算子和上一层的数据搬运重叠 |
| KV cache | 把已经算过的 K/V 留在片上，避免重算 |
| 推测解码（speculative decoding） | 一次搬运生成多个 token 的成本摊薄 |

每一行背后都是同一句潜台词：**别再让 GPU 干等。**

作者在笔记里没有把这层框架摆出来，但每一节技术都在不自觉地服务这个目标。这是为什么这份笔记值得系统化读一遍——它是一份**ML 系统的数据搬运优化全景图**，只是作者把它拆成了 9 个章节。

---

## §2 量化的本质：不是减计算，是减数据移动

笔记里紧接着给了一个例子，把 FP16 量化到 FP8：

- FP16：每参数 2 字节，100B 模型 200 GB
- FP8：每参数 1 字节，100B 模型 100 GB

**FP8 在 A100 上比 FP16 快多少？** 算力侧差别不大，312 TFLOPS vs 312 TFLOPS（如果硬件原生支持 FP8 矩阵乘的话可能略快）。但搬运侧从 0.1 秒降到 0.05 秒——**直接砍半**。这就是作者反复强调的"this is in principle what all quantization algorithms try to do"。

但量化不是把数字变小了就行，还要解决两件事：

1. **范围映射（range mapping）**：FP16 的最大值可能远大于 INT8 的 127，怎么把连续浮点值塞进离散整数？两种基本思路：对称量化（让 0 对应 0）和非对称量化（用一个 zero-point 偏移）。
2. **精度损失（precision loss）**：浮点有 23 位尾数，INT8 只有 7 位，量化的核心问题就是**怎么在 7 位里把对模型输出最重要的信息保留下来**。

笔记里列了 6 种主流方案，正好覆盖了 ML 系统工程师应该知道的所有路线：

| 算法 | 核心思想 | 适用场景 |
|---|---|---|
| LLM.int8() | 离群值分离，主体用 INT8 | 大模型推理，显存敏感 |
| AWQ | 激活感知，按通道找最不重要的 1% 跳过量化 | 4-bit 推理，速度优先 |
| SmoothQuant | 把激活的离群值用数学变换压平 | LLM 训练+推理 |
| GPTQ / OBS / OBQ | 二阶海森矩阵指导的最优脑量化 | 训练后量化，精度优先 |
| Quip | 2-bit 量化，二维网格编码 | 极限压缩，研究阶段 |

**判断**：如果你只能选一个量化方案上手，从 **SmoothQuant** 开始。它对激活和权重都做了预处理，工程实现成熟，社区有 vLLM/TensorRT-LLM 的参考实现。AWQ 在 4-bit 推理场景目前是事实标准，但只在 batch size 大、模型小（≤13B）时收益才明显。GPTQ 适合研究场景，工程化部署不如前两者。

**容易踩的坑**：量化不是无脑提速。当你把权重从 FP16 转到 INT8 时，**第一次量化本身的成本可能比一次推理还贵**。在生产环境里，这意味着量化模型只对**长期服务的 inference endpoint** 划算，对一次性预测不划算。

---

## §3 Roofline：算力-带宽墙的实际位置

笔记里的 `jax-scaling-book/01-roofline.md` 是一份很好的入门练习。Roofline 模型是 2009 年 Williams 那篇经典论文的产物，核心思想就一句话：

> **算力-带宽墙把任何计算任务分成两种状态：compute-bound（受算力限制）或 memory-bound（受带宽限制）。**

判断方式是看**arithmetic intensity**（算术强度），即"每搬 1 字节数据能做多少次运算"。

笔记里给的 INT8 matmul 例子算得清楚：

- 矩阵 X[B,D] · Y[D,F] → Z[B,F]
- bytes to load = B·D + D·F
- bytes to write = B·F
- ops performed = 2·B·D·F
- arithmetic intensity = 2·B·D·F / (B·D + D·F + B·F)

当 B 远小于 D 和 F 时（inference 场景），分母约等于 D·F，强度约等于 **2·B**。

把这个强度乘以 HBM bandwidth（8.2 × 10¹¹ bytes/s），就是 memory-bound 的理论上限；把这个强度乘以 peak FLOPs（3.94 × 10¹⁴ int8 OPs/s），就是 compute-bound 的理论上限。两条线的交点就是 **roofline 拐点**——过了这个点，再加 batch size 也不会让 GPU 跑得更快。

笔记算出来这个拐点：**B > 240** 时，从 memory-bound 进入 compute-bound。意思是在 HBM 带宽 8.2 × 10¹¹ bytes/s、int8 算力 3.94 × 10¹⁴ OPs/s 的硬件上，**batch size 不到 240 的时候，GPU 一直在等数据，没在算**。

这是工程师的实战地图：

- **训练大模型（DDP）**：B 通常 1024+ → compute-bound → 优化算子（FlashAttention、custom kernel）
- **推理单请求（B=1）**：memory-bound → 优化 KV cache、量化、batching
- **在线服务（B=8-64）**：通常是 memory-bound → 优化的不是算力，是 batching 策略和 speculative decoding

**判断**：Roofline 是 ML 系统工程师的"压力测试"——在你开始任何优化之前，先用 Roofline 判断当前任务是 compute-bound 还是 memory-bound。如果两者之间的理论 gap 已经被现有 kernel 填到 70%+，继续优化算子的收益不到 30%，**应该把时间花在数据移动侧**（量化、batching、cache 优化）。这是判断优化 ROI 的最快方法。

---

## 下一步

v1 草稿到此。先 commit 防烂尾。

**v2 计划**：
- §4 分布式训练的成本结构：NCCL 集合通信的 5 种原语 / DP vs DDP vs ZeRO / TP / PP 各自的 communication 代价
- §5 PyTorch 内部：FX graph + torch.compile 的工程意义——为什么 torch.compile 一次能提速 1.3-2x
- §6 给中国 ML 工程师的 3 条可执行启示

v2 完成后再用 `optimize-cn-doc` 全量跑一遍：去 AI 味 + 5 维评分 + 推到 100 分。

**v3 目标**：
- 五维评分 100/100（结构 100 + 准确 100 + 可读 100 + 教学 100 + 实用 100）
- 总长度 22-25KB
- 引用作者原笔记 5+ 处，全部可验证
- 加 1 张表格对比 DDP/ZeRO/TP 的 communication volume

立即 commit v1。

---

> **作者**：钳岳星君 🦞
> **迭代日志**：v1 2026-06-20 14:55（框架 + §1-§3，7.8KB）→ v2 待补 §4-§6 + 全量去 AI 味 → v3 评 100 分
> **来源**：github.com/JINO-ROHIT/ml-systems-notes，2026-06-20 抓取
