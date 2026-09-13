---
title: "PyroDash：让 4B 小模型在 token 级触发交接，把 49 美元的账单砍到 1.78"
date: 2026-09-13T12:54:02+08:00
categories: ["技术笔记"]
tags: ["arxiv", "slm", "llm", "collaborative-inference", "grpo", "cost-efficient", "pyrodash"]
github_repo: ""
source_key: ""
description: "PyroDash 提出 token 级单次交接的小-大模型协作推理框架，把「路由」训练进 SLM 自身，用三阶段 GRPO 对齐准确率与美元账单。在 5 个数学推理 benchmark 上，4B SLM + 冻结 LLM 用 1.78 美元完成 LLM-only 49.36 美元的工作，同时平均准确率反超 6.36 个百分点。本文是 arXiv 2607.20327 的中文翻译反写。"
draft: false
slug: arxiv-2607-20327-pyrodash-translation
---

让小模型**自己判断**什么时候把话头交给大模型，比让一个小路由器学会判断这件事更便宜、更干净、更可移植——这是 PyroDash 的核心赌注。

Pyromind Dynamics 在 2026 年 7 月挂出的 *PyroDash: Cost-Efficient Token-Level Small-Large Language Model Collaborative Inference*（arXiv 2607.20327）把 SLM-LLM 协作里的「路由」从外挂的判别器搬进 SLM 的词表里——加一个专门的控制 token `τ_off`，让小模型在自回归生成时**自己决定**这一行代码写到一半要不要把笔交给大模型。这种做法在工业界通常被称为 token-level self-routing，PyroDash 是第一个把训练目标绑到「预填 + 解码美元单价」上的实现。

最关键的实验数字：在五个数学推理 benchmark（GSM8K、Minerva、OlympiadBench、AIME-2024、AIME-2025）上，Qwen3.5-4B 作为 SLM + 冻结的 GLM-5.2-FP8 作为 LLM，跑 λ=0.05 的"质量优先"档，**平均准确率 64.04%，比 LLM-only 基线 57.68% 高出 6.36 个百分点**；跑 λ=0.6 的"成本优先"档，**平均准确率 54.55%，LLM token 占比 1.90%，平均每例 LLM 调用 0.012 次，总成本从 49.36 美元降到 1.78 美元**——96.4% 的成本削减，同时准确率比最强路由基线还高。

这篇文章是那篇论文的翻译反写。保留所有原始数字、模型名、benchmark 名、训练超参和定价；穿插我自己的解读和论文没说出口的边界。

## 一、这篇论文在讲什么

**作者团队**：Niqi Lyu、Pengtao Shi、Wei Qiu、Jianlin Zhong、Sicong Xia、Jianyao Ma、Yicheng Ding 七位，Pyromind Dynamics Inc. 工业出品。

**发表时间**：2026 年 7 月 22 日（v1），挂 arXiv 编号 2607.20327，类别 cs.CL（计算语言学），CC BY 4.0 开放许可。

**核心问题**：当 LLM API 按 token 计费、而你同时跑着本地小模型（SLM）和云端大模型（LLM）时，到底应该在**哪个时刻**让请求从小模型跳到大模型？工业界有四类已知的答案：请求级路由、token 级协作、解码加速、知识蒸馏。每一类都解决了某个子问题，但**几乎没人把训练目标绑到「实际美元账单」上**。PyroDash 的贡献是设计一个奖励函数，把 SLM 在自回归过程中"何时发出控制 token"这一动作直接对接到「与 LLM-only 基线对比的归一化成本」上，并允许通过单一超参 λ 在「多花钱多拿分」与「少花钱差不多分」之间平滑切换。

**核心方法**：三个组件构成的协作推理架构 + 一个三阶段训练流水线。

- **架构**：Collaborate Engine（CE，编排层）+ 训练过的 SLM `M_s` + 冻结的 LLM `M_l`。SLM 在解码时如果输出 `τ_off`，CE 立即终止 SLM、把已生成的部分轨迹 `C_s` 包成一个 prompt、然后**只调一次** LLM 拿到续写；续写结果与 SLM 已生成的 token 拼成最终输出。整个请求最多一次 LLM 调用。
- **训练**：Stage 1 学控制 token `τ_off` 的输入/输出嵌入；Stage 2 用 EasyHard-24k 数据集做有监督冷启动；Stage 3 用 GRPO 在 DAPO-Math 数据集上做"准确率 − λ × 归一化成本"奖励的策略对齐。`M_l` 全程冻结。
- **目标函数**（公式 1）：
  $$\max_{\pi_s} \mathbb{E}_{(q,y)\sim\mathcal{D}}\left[\mathrm{Acc}(O(q;\pi_s), y) - \lambda\,\mathrm{Cost}_{\mathrm{norm}}(q;\pi_s)\right]$$
  其中 `Cost_norm` 是「协作推理实际成本 / LLM-only 推理成本」，`λ ≥ 0` 是成本惩罚系数。

**最重要的实验数字**：在五个数学 benchmark 上，PyroDash 在 λ=0.05 档超过 GLM-5.2-FP8（LLM-only）平均准确率 6.36 个百分点；在 λ=0.6 档把总成本从 $49.36 砍到 $1.78。RouteLLM 与 GlimpRouter 这两个最强基线分别要把 77.37% 与 75.11% 的解码 token 交给 LLM，PyroDash 在 λ=0.6 时只交 1.90%——大约是基线的 **1/40**，而平均准确率还更高（54.55% vs 52.74% 与 54.20%）。

## 二、为什么以前没人把这笔账算清楚

第一性原理看，SLM-LLM 协作最常被吹的两个优势——**便宜**和**本地可控**——其实跟「能不能省钱」不是一回事。让本地 4B 模型跑 100% 的请求确实便宜，但准确率掉到 28.36%（论文 Table 2 的 Qwen3.5-4B 单独跑分）；让云端 LLM 跑 100% 的请求确实准确，但账单掉到 $49.36。问题不是「选哪个」，而是「在推理轨迹的哪一步切」。PyroDash 把这件事拆成三个子问题：

### 2.1 请求级路由看不到中间步骤

FrugalGPT、RouteLLM、Hybrid LLM、MixLLM、LLM Bandit 这一整族方法都是在**请求解码之前**决定用 SLM 还是 LLM：看完输入、判个难度、整条请求交给一边。如果一个看上去简单的请求在中间某一步变难——比如 GSM8K 里"年收入 $10.50 - 维护 $3 = $7.50"之后还要判断 "n > 12 还是 n ≥ 13"——请求级路由没办法在中间救场。PyroDash 论文把这写成「请求级路由决定 *which* model，但不知道 *when*」。

### 2.2 Token 级协作的成本目标不对

CITER（per-token MLP 路由器）、Co-LLM（interleaved decoding）、RelayLLM（bounded LLM spans）这一族做 token 级调度的文献，回答了「决策粒度」问题。但有两个共同短板：（a）需要持续协调两个模型的解码状态，与无状态 API 兼容性差；（b）奖励函数通常是"LLM token 占比"或"FLOP 数"——而商用 API 的账单是「预填 token × 预填单价 + 解码 token × 解码单价」两段独立计价。PyroDash 论文把这点用 Equation 4-7 写得清清楚楚：训练目标里 `Cost_norm = Cost_act / Cost_base`，分子是「(C_s + C_pre) × T_s + C_dec × T_{l,dec}」，分母是「C_pre × T_in + C_dec × T_{l,dec}」，**两边都用真实美元单价**。

### 2.3 解码加速假设一种不同的合作关系

Speculative decoding（Leviathan 2023、SpecInfer、Medusa、MagicDec）也是让小模型给大模型打草稿，但合作关系是「每一步大模型都要审一遍草稿」——LLM 全程参与、要求 logits 访问、目标分布严格不变。这套架构优化的是**延迟与吞吐**，账单却不一定降得下来，因为即使草稿被拒绝也要算 token 钱。PyroDash 把合作关系重新定义成「SLM 写一段，**判定**写不动了，**整段**移交给 LLM，LLM 不再回头」——一次交接，不存在"拒绝"。

PyroDash 的核心工程判断是：**协作推理的训练目标应该对齐商用 API 的计费模型，而不是对齐 FLOP 或 token 占比**。这一点决定了 SLM 学到的「什么时候该交接」是基于真实的美元代价，而不是某个抽象的"工作量"。

## 三、架构：一次交接的协作解码

PyroDash 的运行时由三个组件组成：

- **SLM 引擎**：托管训练过的 `M_s`，按自回归方式解码。每一步要么继续生成常规 token，要么生成控制 token `τ_off`。
- **LLM 引擎**：托管冻结的 `M_l`，只在被请求时调用一次，接收「原始 query + SLM 已生成的部分轨迹 `C_s` + LLM 续写 prompt `P_l`」并返回续写。
- **Collaborate Engine（CE）**：编排层。检测 `τ_off` 出现，调用 `Pack(O_s)` 把控制 token 之前的内容打包成 `C_s`，终止 SLM，向 LLM 发起一次完成调用，把 SLM 输出 `O_s` 和 LLM 续写 `O_l` 拼接成最终输出 `O = O_s ∥ O_l`。

完整的运行时算法（论文 Algorithm 1，单次交接协作解码）：

```text
输入：query q；固定 prompt P_s, P_l；SLM M_s；冻结 LLM M_l
输出：联合输出 O（流式）
 1  O_s ← ∅
 2  foreach token t from M_s(P_s, q) do
 3    if t = τ_off then
 4      C_s ← Pack(O_s)
 5      stop decoding with M_s
 6      O_l ← M_l.Complete(P_l, q, C_s)
 7      stream O_l to user
 8      return O_s ∥ O_l
 9    stream t to user
10    O_s ← O_s ∥ t
11  return O_s
```

这段伪代码的核心不变量是**每个请求最多一次 LLM 调用**：SLM 不再被回访，所以也不会出现 "SLM → LLM → SLM → LLM ..." 那种 token-share 类方法常见的反复预填。论文 Figure 1 把这个流画得很直观：CE 在 `τ_off` 出现那一步接管，之后的控制流不再回到 `M_s`。

这种设计有四个工程后果值得注意：

- **架构与厂商无关**：`M_l` 不需要 retraining、不需要 logits 访问，只需要一个标准的 completion 接口。所以 GPT-6、Claude Sonnet 5.5、GLM-5.2-FP8 都可以当成冻结黑盒挂在 CE 后面。
- **单次交接意味着「不可逆」**：SLM 在某一步决定交出去之后，LLM 续写的内容不会再被 SLM 审查。这意味着 SLM 必须把 `C_s` 写成一个对 LLM 友好的"接力棒"——这一约束在 Stage 2 的 SFT 数据里被显式编码。
- **`τ_off` 是新词**：SLM 的原始词表里没有这个 token。Stage 1 要先把这个 token 注入词表并学一个稳定表示，否则 SLM 在自回归时可能因为不熟悉这个 token 而产生不稳定预测。
- **CE 不做决策**：CE 是 deterministic executor——只负责检测 token、打包上下文、调一次 LLM。所有「是否交接、何时交接」的判断都在 SLM 的 logits 里。这是论文最重要的设计哲学：**让路由决策拥有与小模型同样的训练信号，而不是外挂一个分类器**。

## 四、训练：三阶段把路由写进 SLM

训练的目标是把 `τ_off` 从一个"新词表项"变成"SLM 在正确时机发出去的正确信号"。论文用三阶段渐进流水线（论文 Algorithm 2 + Figure 2）：

### 4.1 数据准备：EasyHard-24k

先建一个 24,061 条样本的数据集 EasyHard-24k（PyroMind 2026a）。每条样本按以下步骤构造：

1. **能力基线**：`M_s` 跑一遍样本，对照 ground truth。对的进 easy 子集（"SLM-only 够用"），错的进 hard 子集（"需要 LLM 协助"）。
2. **重建 CoT**：对 hard 子集，让 `M_l` 重建一条能到达正确答案的 chain-of-thought。**关键约束**：不能用 `M_s` 自己跑出的失败轨迹当 SFT 目标——那会强化引发交接的失败本身。
3. **两套 prompt 条件**：Corpus A 不含 offloading prompt `P_s`，assistant 轨迹里也不含 `τ_off`，保留 SLM 原本的非协作行为；Corpus B 在 system message 里加 `P_s`，easy 目标仍然不含 `τ_off`（"协作模式可用 ≠ 必须调用 LLM"），hard 目标在 CoT 段内动态插入 1–4 个 `τ_off`，给 Stage 2 提供 "token 级交接位置" 的冷启动。

这套数据的核心思想：**让模型先认识"协作模式"和"非协作模式"在词表层面的区别**，再让 Stage 3 用真实成本信号去调整交接位置。论文明确说，Corpus B 里插入的 `τ_off` 位置"不假设是最终最优的能力边界"，只是行为冷启动——这避免了一个常见的 SFT 陷阱：把人为标注当成 ground truth。

### 4.2 Stage 1：控制 token 嵌入学习

原始 SLM 的词表里没有 `τ_off`。直接随机初始化一个新 token 的输入/输出嵌入会让训练早期预测行为剧烈震荡。所以 Stage 1 用 anchor 嵌入做 warm-start：

$$\mathbf{e}_{\tau_{\mathrm{off}}} = \frac{1}{|\mathcal{A}|}\sum_{a\in\mathcal{A}} \mathbf{e}_a + \epsilon, \quad \epsilon \sim \mathcal{N}(0, \sigma^2\mathbf{I})$$

anchor 集合 `𝒜` 选了"自然段落边界"类的 token——句号、换行符、`<eos>` 之类。直觉上 `τ_off` 应该出现在推理轨迹的某个"我快写不动了"的边界，anchor 选段边界符号让这个新 token 起步就处在嵌入空间的合理区域。论文设 σ=0.1。Stage 1 之后丢弃临时 LoRA（rank r=8），只把 `τ_off` 对应的嵌入行 merge 进 base model。

### 4.3 Stage 2：offloading 导向的 SFT 冷启动

Stage 2 在 Corpus A ∪ Corpus B 上做一轮 SFT：

$$\mathcal{L}_{\mathrm{SFT}}(\theta) = -\left(\mathbb{E}_{(x, z_A)\sim\mathcal{D}_A}[\log \mathrm{prob}_\theta(z_A \mid x)] + \mathbb{E}_{(x, z_B)\sim\mathcal{D}_B}[\log \mathrm{prob}_\theta(z_B \mid x, P_s)]\right)$$

- 第一项保留 SLM 独立推理的原有行为（"协作模式关闭时它就是个普通 SLM"）；
- 第二项在 `P_s` 启用时教模型区分 easy（不交）和 hard（在 CoT 中某些位置交）。

这一阶段的产物是一个能"按 prompt 条件发出或不发出 `τ_off`"的 SLM。Stage 2 之后 embedding 层冻结，只在 attention 层挂 LoRA（r=16, α=32），给 Stage 3 的 RL 阶段留出低方差起点。

### 4.4 Stage 3：cost-aware GRPO

冷启动的 SLM 能"发出 `τ_off`"了，但还不知道"什么时候发才划算"。Stage 3 把训练目标接到真实美元账单上。

**奖励函数**：对每个 query `q_i`，先用冻结 `M_l` 单跑一遍算出 LLM-only 基线成本 `Cost_base^i = C_pre × T_in^i + C_dec × T_{l,dec}^i`（Equation 4）。然后在 `P_s` 下让当前策略采样 G=8 条联合输出 `O_{ij}`，每条的真实成本是：

$$\mathrm{Cost}_{\mathrm{act}}^{ij} = (C_s + C_{\mathrm{pre}}) \cdot T_s^{ij} + C_{\mathrm{dec}} \cdot T_{l,\mathrm{dec}}^{ij}$$

（SLM 解码 token 既要算 SLM 自身的钱，也要算 LLM 预填的钱——这是商用 API 的关键不变量。）把归一化效率 `R_eff^{ij} = Cost_act^{ij} / Cost_base^i` 与任务准确率 `R_acc^{ij} = Acc(O_{ij}, y_i)` 拼成总奖励：

$$R_{\mathrm{total}}^{ij} = R_{\mathrm{acc}}^{ij} - \lambda \cdot R_{\mathrm{eff}}^{ij}$$

`Acc` 用 `\boxed{}` 答案做等价比较（math_verify），λ 在验证集上 sweep 选值。

**GRPO 损失**：组内相对优势 `Â^{ij} = (R_total^{ij} − μ_i) / (σ_i + δ)`，loss 是标准的 PPO-clip 形式（Equation 9）。**只有 SLM 生成的 token 进入梯度路径**，`M_l` 冻结所以 LLM 续写不直接反向传播；它的影响完全通过 `R_acc` 与 `R_eff` 两条边传回来。

这套奖励设计的工程含义：

- **基线归一化让 λ 在不同 query 之间可比**。同一 λ 在"成本 5 美元 vs 50 美元"的 query 上语义一致——都是"协作推理是否比 LLM-only 便宜"。
- **G=8 rollouts 给出低成本方差估计**，比装一个 learned critic 便宜得多。
- **价格参数（C_pre, C_dec, C_s）作为超参外置**，换一家云厂商只需要重算 `Cost_base`，策略不需要重训。

## 五、实验：数字怎么读

论文在五个数学推理 benchmark 上做主实验：GSM8K（小学应用题）、Minerva（技术领域定量推理）、OlympiadBench（竞赛级双语多模态）、AIME-2024、AIME-2025（竞赛级，AIME 用 avg@32 抑制采样方差）。模型对：Qwen3.5-4B (SLM) + GLM-5.2-FP8 (LLM)。报告四个指标：准确率、LLM token 占比、平均 LLM 调用次数、估算美元成本。

**主表（论文 Table 1 + Table 2 摘要）**：

| Method | Avg. Acc. (%) | LLM Token Ratio (%) | Avg. LLM Calls | Cost ($) |
|---|---|---|---|---|
| Qwen3.5-4B (SLM-only) | 28.36 | 0.00 | 0.000 | 2.26 |
| Qwen3.5-4B + SFT (Stage 2) | 46.25 | 0.00 | 0.000 | 1.32 |
| RouteLLM (~75% GLM-5.2-FP8) | 52.74 | 77.37 | 0.808 | 44.62 |
| GlimpRouter (τ=0.9) | 54.20 | 75.11 | 1.200 | 31.61 |
| PyroDash (λ=0.05) | **64.04** | 95.34 | 0.975 | 39.29 |
| PyroDash (λ=0.1) | 55.29 | 8.19 | 0.058 | 4.71 |
| PyroDash (λ=0.6) | 54.55 | **1.90** | **0.012** | **1.78** |
| GLM-5.2-FP8 (LLM-only) | 57.68 | 100.00 | 1.000 | 49.36 |

几个值得停下来想一想的数字：

- **64.04% > 57.68%**：4B SLM + 冻结 LLM 在 λ=0.05 档**反超** LLM-only 基线 6.36 个百分点。这是论文最有冲击力的发现——它的反直觉在于：SLM 单独跑只有 28.36%，加上冻结 LLM 之后反而比 LLM 单独跑还准。一个合理的解释是：SLM 在自己的强项区（短链推理）写出了**比 LLM 自己写更干净的 partial trace**，LLM 在这个干净起点上做续写比从零开始更稳。论文 Figure 3 的定性案例（GSM8K #12）展示了这一点——SLM 把年收入算到 `$7.50` 然后交棒，LLM 只需要解一个一元不等式 `7.50n > 90`，无需重做数值计算。
- **$1.78 vs $49.36**：λ=0.6 时总成本削减 96.4%。数字很夸张，但**关键的削减来源**是 LLM 解码 token 从 17.08M 降到 0.23M（论文 Table 4）。SLM 解码 token 从 27.86M 降到 12.07M——SLM 自己也在变短，因为 SLM 学到「写够就交」。这是策略学习的副产物，比单纯的"少调 LLM"更省。
- **1.90% LLM token ratio**：在 0.012 次/例 LLM 调用的水平上，1.90% 是怎么算出来的？每 100 条请求里大约 1.2 条触发 LLM 调用；触发的请求 LLM 输出 token 占那条请求输出 token 的 158%（论文 Table 4 的 12.07M SLM out vs 0.23M LLM out 加权平均后）。这个数字本身比「百分比」更值得看：策略学到了**几乎不动用 LLM，但偶尔用一次就用到底**。
- **RouteLLM 与 GlimpRouter 的 token 占比都 >75%**：这两个最强路由基线**把大部分推理仍交给 LLM**，因为它们的奖励函数或决策规则都没法让 SLM 在 SLM 能解的题上"自己扛下来"。PyroDash 的关键差异是：**奖励函数允许 SLM 通过"不交接"获得正反馈**（`R_eff < 1.0` 时 `R_total` 增大），基线方法做不到这一点。

**λ 扫描（论文 Table 3）**：

| λ | Avg. Acc. (%) | LLM Token Ratio (%) | Avg. LLM Calls | Cost ($) |
|---|---|---|---|---|
| 0.05 | 64.04 | 95.34 | 0.975 | 39.29 |
| 0.1 | 55.29 | 8.19 | 0.058 | 4.71 |
| 0.2 | 54.91 | 3.18 | 0.026 | 2.55 |
| 0.3 | 54.20 | 2.54 | 0.025 | 2.16 |
| 0.6 | 54.55 | 1.90 | 0.012 | 1.78 |

`λ` 从 0.05 到 0.1 时 LLM token 占比掉 91%、成本掉 88%，但准确率掉 8.75 个百分点——**这一段是「质量-成本」曲线最陡的区间**。`λ ≥ 0.1` 之后曲线变缓：成本继续下降，准确率稳定在 54.2–55.3% 之间。这种"边际成本递减"的形态暗示 `λ=0.05` 的策略在「依赖 LLM」这件事上偏离了其余 λ 较远的策略——也许它在学一些"为准确率不惜工本"的边缘行为。

**定性案例（论文 §4.3 + Appendix A）**：

论文给了一个 GSM8K 例子（柠檬树第几年开始赚钱）和五个附录案例（对数方程、晶体密度、不等式、组合、SLM 独立完成）。最值得读的是 Appendix A.5——一条 GSM8K 简单题 "4 朵玫瑰 + 7 朵大丽花 = 多少朵花"，SLM 直接 `4 + 7 = 11`、`4 + 11 = 15`，**没有发出 `τ_off`**，CE 按 Algorithm 1 第 9–11 行直接流式返回 SLM 输出。这条案例证明 SLM 确实学到了"简单题自己扛"——不是被训练成"总想交出去"。

Appendix A.4（AIME-2024 #142 组合题）展示了"中途纠错 + 交接"——SLM 先尝试 `a = b` 的中间项假设，发现矛盾后回退到 `a < b` 的 distinct middle entry 假设，再交接。说明 `τ_off` 不是"我错了就交"，而是"我把有用的部分做完了，剩下的结构搜索交给 LLM"。

## 六、与既有方法的对比：PyroDash 到底新在哪

论文 §2 的相关工作覆盖四族方法，我把每族的核心差异单独拎出来：

| 类别 | 代表方法 | 决策粒度 | 是否需要路由模型 | 训练目标 | 兼容性 |
|---|---|---|---|---|---|
| 请求级路由 | FrugalGPT, RouteLLM, Hybrid LLM, MixLLM, LLM Bandit | 请求（解码前） | 是（cascade 阈值 / learned router） | 质量 / 偏好 / 难度 | 单次 LLM 调用 |
| Token 级协作 | CITER, Co-LLM, RelayLLM | Token | 是（MLP router / latent switch） | Token 占比 / FLOP | 通常需要 logits 访问或维护双模型状态 |
| 解码加速 | Speculative decoding, SpecInfer, Medusa, MagicDec | Token block | 否（draft 模型内置） | LLM 分布对齐 | 必须访问 logits；延迟优化，账单不一定降 |
| 知识蒸馏 | MiniLLM, GKD | 离线 | 否 | 输出分布对齐 | 一次性训练成本，不在推理时协作 |
| **PyroDash** | 本论文 | **Token** | **否（决策内化在 SLM 词表）** | **准确率 − λ × 归一化美元成本** | **无状态 API 兼容** |

PyroDash 与 token 级协作族共享「token 级决策」粒度，但有三个关键差异：

1. **不需要单独 router**：CITER 用 per-token MLP 选模型，Co-LLM 把"切换"当 latent action 学；PyroDash 把这个动作编码成一个新增词表项 `τ_off`，SLM 在自回归时直接输出它。这意味着 PyroDash 不需要维护一个额外的路由网络、路由网络的训练信号、或者路由网络的推理延迟。
2. **奖励函数对齐商用 API 计费**：Co-LLM 没有显式的成本目标；RelayLLM 惩罚 LLM-token 占比而不是「预填 token × 预填单价 + 解码 token × 解码单价」两段计价；PyroDash 用 Equation 5–7 把"调 LLM 多花多少钱"显式折成 `R_eff`，让策略学的是「这次交接换来的准确率提升值不值 `λ` 个归一化单位」。
3. **最多一次交接**：Co-LLM 与 RelayLLM 允许 SLM/LLM 多次交替；PyroDash 单向流转——SLM 交出去之后 LLM 不回交。这避免了"反复预填"带来的隐藏 token 成本，也让推理时延可预测。

与解码加速族的差异是合作关系不同：speculative decoding 里 LLM 始终在场且权威，PyroDash 里 LLM 只在被叫到时才出现，且**不审查 SLM 的部分轨迹**。

与知识蒸馏族的差异是协作时机不同：MiniLLM、GKD 是离线训练时把 LLM 的能力蒸馏到 SLM，让 SLM 部署时独立运行；PyroDash 不试图让 SLM 学会 LLM 的全部能力，而是让 SLM 学会"我不行的时候喊 LLM 帮忙"，两者互补不互斥。

## 七、限制与未回答的问题

论文 §6 自己列了四条限制，我把它们和"我自己看到但论文没明说"的边界分开列：

### 7.1 论文承认的限制

1. **没有分析交接点的合理性**：报告了平均准确率和 LLM token 占比，但没说 SLM 在什么**位置**交接才是真正"它的能力边界"。未来的工作应该把交接位置和具体的推理失败模式关联起来。
2. **没有对照"直接 token-cost 惩罚"**：Stage 3 用的是「归一化成本」（Equation 6），但没有 ablation「不归一化、直接惩罚 token 数」。所以"归一化"这一步到底带来了多少增益是未知的。
3. **只评估了数学推理**：代码生成、工具调用、多模态推理这些场景的迁移性未验证。
4. **成本是估算而非账单**：用的是列出的 token 单价，不是 provider 的实际计费。多轮交互里"一次请求 vs 一次会话"的成本定义差异也没讨论。

### 7.2 论文没说但我看到的边界

- **SLM 必须会写「接力棒 CoT」**：因为 LLM 续写时看到的是 `q + C_s`，如果 SLM 在交接前的 partial trace 是垃圾，LLM 也救不回来。论文假设 Stage 2 的 SFT 数据能让 SLM 学到"有用的 partial reduction"，但这个假设没被显式验证——附录案例看着像，但没说准确率分布。
- **LLM 必须接受「续写」任务**：GLM-5.2-FP8 在实验中是被 prompt `P_l` 引导续写。如果某家 LLM API 不允许"在别人半句话后接写"（比如某些 reasoning-only 端点），CE 的 `M_l.Complete(P_l, q, C_s)` 这一步会失败。论文没讨论兼容性回退。
- **`λ` 的可移植性**：λ 在验证集上 sweep 选值（论文 §4.4），但换 benchmark、换 SLM/LLM 配对后这个值要不要重新选？论文没说。直觉上 λ 是「多花一美元换多少准确率」的偏好参数，应该按业务目标选，而不是按数据集选。
- **单次交接的硬约束**：Algorithm 1 第 5 行 "stop decoding with M_s" 是硬截断。多轮对话里 SLM 第一轮交出去之后，LLM 续写的内容永远不会回到 SLM 的 context。这对单轮问答没事，对"我先问、你答一半、我想追问"这种 multi-turn 是断的——论文承认这一点但没给出方案。
- **GRPO 的方差问题**：G=8 rollouts 在数学题上还行，对长输出（代码生成、多步 agent）方差会爆。论文没用更长上下文任务，所以这条边界是隐性的。

## 八、这篇论文给我的启发

PyroDash 把"协作推理"从"加一个判别器"重新定义成"让小模型在词表里学会一个新动作"。这一重新定义带来三个工程后果：

- **架构可移植**：CE 只依赖一个标准 completion 接口。换 LLM 厂商、换 SLM 型号、换定价模型，只需要重算 `Cost_base` 和 sweep `λ`，不需要改训练流程。
- **训练目标与商用 API 计费对齐**：Equation 5–7 把 token 单价外置成超参，奖励函数直接对应"省了多少美元 / 多花了多少美元"。这是少见的"训练目标 = 业务目标"的工程实例。
- **单次交接的硬约束换来了可预测延迟**：请求要么走 SLM-only，要么走 SLM→LLM 一次。前者的延迟 = SLM 解码；后者的延迟 = SLM 解码到 `τ_off` + LLM 续写。没有"路由网络本身的推理开销"，没有"反复预填的抖动"。

对正在搭 agent 系统的工程师，这条路有几个具体启示：

- **路由决策最好拥有与小模型同样的训练信号**。外挂一个分类器看起来灵活，实际上让"训练数据 / 部署数据 / 计费数据"三层信号互相打架。
- **奖励函数应该对齐业务计费**，而不是对齐 FLOP 或 token 占比。`Cost_norm = Cost_act / Cost_base` 这种结构让 `λ` 在不同 query 之间可比。
- **单次交接 vs 多次交接**是有取舍的：单次换可预测性，多次换灵活性。数学推理、检索增强问答这类**单输出可验证**的任务适合单次；多轮对话、agentic tool use 这类**多步不可逆**的任务可能需要回到多次交接的范式。

PyroDash 不是协作推理的终点——它解决的是"小-大模型按 token 计费的单轮推理"这一具体形态。但它示范了一个原则：**把决策放进模型本身、把目标对齐业务单位、把架构约束写成算法不变量**——这三件事比任何单独的技术 trick 都更能决定一个系统能不能在生产里活下来。