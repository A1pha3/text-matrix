---
title: "MiniMind：从零开始用 3 块钱训练 64M 参数的大语言模型"
date: "2026-04-12T12:00:00+08:00"
slug: "minimind-llm-training-from-scratch"
github_repo: "jingyaogong/minimind"
source_key: "gh:jingyaogong/minimind"
aliases:
  - /posts/tech/minimind-llm-training-from-scratch/

description: "MiniMind 是 54.8k Stars 的开源 LLM 训练项目，3 元钱 + 2 小时即可训练 64M 参数模型。覆盖预训练、SFT、LoRA、DPO、PPO、GRPO、CISPO、Agentic RL、工具调用的完整链路，所有核心算法从零 PyTorch 原生实现。"
categories: ["技术笔记"]
tags: ["LLM", "PyTorch", "MoE", "RLHF", "强化学习"]
---

# MiniMind：从零开始用 3 块钱训练 64M 参数的大语言模型

本文的目标是把 MiniMind 这条从零到对话模型的完整链路拆开讲清楚：预训练、SFT、LoRA（低秩适配）、蒸馏、DPO/PPO/GRPO/CISPO 强化学习、工具调用与 Agentic RL 各自解决什么问题，代码落在哪个文件，默认超参数是多少。读完后你应当能独立跑通 minimind-3 的推理与训练，并能对照源码解释每个阶段的设计取舍。

## 目录

- 一、项目概览：定位、实时统计与已发布模型
- 二、核心功能：训练链路、技术特性与成本
- 三、技术架构：模型结构、混合专家、项目结构与数据流
- 四、快速开始：安装、推理与训练
- 五、配置选项详解：预训练 / SFT / LoRA 默认参数
- 六、知识蒸馏
- 七、强化学习：统一视角（DPO / PPO / GRPO / CISPO / Agentic RL）
- 八、工具调用与自适应思考
- 九、框架集成：HuggingFace / llama.cpp / ollama / vllm
- 十、RoPE 长度外推
- 十一、OpenAI 风格兼容接口服务
- 十二、推荐做法
- 十三、动手练习与自测
- 十四、进阶方向
- 十五、常见问题
- 十六、总结
- 十七、参考文献

## 一、项目概览

**MiniMind** 是由 jingyaogong 开发的开源大语言模型训练项目，其核心理念是"大道至简"——让每个人都能从零开始，仅用约 3 元钱成本与 2 小时训练时间，即可训练出规模约为 64M 参数的超小型语言模型 MiniMind。按 README 的口径，"2 小时"指 SFT 阶段在单张 NVIDIA 3090 上跑完 1 epoch 的实测耗时，"3 块钱"是对应时段的 GPU 租用成本。

该项目在 GitHub 上获得了 **54.8k Stars** 和 **7.2k Forks**（截至 2026 年 8 月），是开源 LLM 训练领域的标杆项目。

### 1.1 定位

大语言模型（Large Language Model, LLM）的出现引发了全球范围内对 AI 的空前关注。然而，动辄数百亿参数的模型规模使得它们对个人设备而言不仅难以训练，甚至连部署都显得遥不可及。

MiniMind 的诞生正是为了打破这一困境：

1. **从零开始训练**：真正从零开始构建语言模型，而非仅仅使用 LoRA（低秩适配）等技术微调现有大模型
2. **极低训练成本**：最低只需不到 3 元钱的服务器成本，即可亲身体验从 0 到 1 构建语言模型的全过程
3. **完全透明可控**：所有核心算法代码均从 0 使用 PyTorch 原生实现，不依赖第三方库提供的高层抽象接口

### 1.2 技术统计

| 指标 | 数值 |
|------|------|
| Stars | 54.8k |
| Forks | 7.2k |
| Commits | 361 |
| 最新提交 | 2026-08-06 |
| 许可证 | Apache-2.0 |
| 主要语言 | Python |

以上数字来自 GitHub API（应用程序接口）实时查询，统计截至 2026-08-19，仓库仍在活跃更新。

### 1.3 已发布模型

模型名带 moe 后缀的是 MoE（混合专家模型）架构版本，其余为 Dense 架构：

| 模型 | 参数量 | 发布日期 |
|------|--------|----------|
| **minimind-3** | 64M | 2026.04.01 |
| **minimind-3-moe** | 198M / A64M | 2026.04.01 |
| minimind2-small | 26M | 2025.04.26 |
| minimind2-moe | 145M | 2025.04.26 |
| minimind2 | 104M | 2025.04.26 |
| minimind-v1-small | 26M | 2024.08.28 |
| minimind-v1-moe | 4×26M | 2024.09.17 |
| minimind-v1 | 108M | 2024.09.01 |

## 二、核心功能

### 2.1 完整训练流程覆盖

MiniMind 提供了从预训练到强化学习的完整训练链路：

| 训练阶段 | 说明 | 核心文件 |
|----------|------|----------|
| **Tokenizer** | 分词器训练，支持 `<tool_call>`、`<tool_response>`、`<think>` 等模板标记 | `train_tokenizer.py` |
| **Pretrain** | 预训练，学习基础语言能力和世界知识 | `train_pretrain.py` |
| **SFT** | 监督微调，指令跟随与对话能力 | `train_full_sft.py` |
| **LoRA** | 低秩适配，参数高效微调 | `train_lora.py` |
| **KD** | 知识蒸馏，从大模型提取知识 | `train_distillation.py` |
| **DPO** | 直接偏好优化，RLHF（基于人类反馈的强化学习）简化版 | `train_dpo.py` |
| **RLAIF** | 基于 AI 反馈的强化学习（PPO / GRPO / CISPO） | `train_ppo.py` / `train_grpo.py` |
| **Tool Use** | 工具调用能力，已并入 SFT 主线数据 | `scripts/eval_toolcall.py`（测试） |
| **Agentic RL** | 智能体强化学习，多轮 Tool-Use 场景下的 GRPO / CISPO | `train_agent.py` |

### 2.2 核心技术特性

1. **原生 PyTorch 实现**：所有核心算法从 0 实现，不依赖 transformers/trl/peft 等高层抽象
2. **MoE 支持**：支持 Dense + MoE 两种架构
3. **长文本支持**：通过 YaRN 实现 RoPE 长文本外推
4. **多框架兼容**：兼容 transformers、trl、peft 等主流框架，以及 llama.cpp、vllm、ollama 等推理引擎
5. **可视化支持**：wandb / swanlab 训练可视化，支持动态启停训练
6. **分布式训练**：支持单机多卡 DDP、DeepSpeed

### 2.3 训练成本

基于单卡 NVIDIA 3090 的经验估算：

| 模型 | 参数量 | Pretrain | SFT | Tool Call | RLAIF |
|------|--------|----------|-----|-----------|-------|
| **minimind-3** | 64M | ≈1.21h / 1.57￥ | ≈1.10h / 1.43￥ | ≈0.9h / 1.17￥ | ≈1.1h / 1.43￥ |
| **minimind-3-moe** | 198M / A64M | ≈1.69h / 2.20￥ | ≈1.54h / 2.00￥ | ≈1.26h / 1.64￥ | ≈1.54h / 2.00￥ |

**从零训练 minimind zero 总成本控制在约 3 元钱、2 小时以内。**

## 三、技术架构

### 3.1 模型结构

minimind-3 采用 Transformer 架构的 Decoder-Only 结构，配置向 Qwen3 / Qwen3-MoE 生态对齐：

| 配置项 | 值 |
|--------|-----|
| 词汇表大小 | 6400 |
| 最大位置编码 | 32768 |
| RoPE theta | 1e6 |
| 层数 | 8 |
| 模型维度 | 768 |
| KV 头数 | 4 |
| Q 头数 | 8 |

**架构特点**：
- 预标准化（Pre-Norm）+ RMSNorm
- SwiGLU 激活函数
- RoPE 旋转位置编码
- GQA（Grouped Query Attention，分组查询注意力机制）

### 3.2 MoE 架构

minimind-3-moe 在相同结构上扩展 MoE 前馈层：

- 默认配置：**4 experts / top-1 routing**
- 相比同尺寸 Dense 模型，训练慢约 **50%**（因原生 PyTorch 未做 kernel fusion）
- 如需更优性能，可基于 Triton 自定义 kernel、DeepSpeed-MoE、Megatron-LM 优化

### 3.3 项目结构

```text
minimind/
├── model/        # model_minimind.py 模型定义、model_lora.py LoRA 实现
├── trainer/      # train_pretrain / train_full_sft / train_lora / train_distillation
│                 # train_dpo / train_ppo / train_grpo / train_agent / train_tokenizer
├── dataset/      # 数据集目录，含 lm_dataset.py 与格式说明
├── scripts/      # web_demo / serve_openai_api / chat_api / convert_model / eval_toolcall
└── eval_llm.py   # CLI 推理入口，训练输出保存在 out/
```

### 3.4 数据流程

```text
原始数据 → 清洗 / 去重 / 格式统一 → Tokenizer 训练
→ Pretrain 预训练 → SFT 监督微调
→ [可选] LoRA / DPO / PPO / GRPO / CISPO / Agentic RL
→ 模型权重 (.pth) → [导出] HuggingFace / llama.cpp / vllm / ollama
```

## 四、快速开始

### 4.1 环境安装

```bash
# 克隆仓库
git clone --depth 1 https://github.com/jingyaogong/minimind
cd minimind

# 安装依赖
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple
```

### 4.2 模型推理

**下载模型**：

```bash
# 方式1：ModelScope
modelscope download --model gongjy/minimind-3 --local_dir ./minimind-3

# 方式2：HuggingFace
git clone https://huggingface.co/jingyaogong/minimind-3
```

**CLI（命令行工具）推理**：

```bash
# Transformers 格式
python eval_llm.py --load_from ./minimind-3

# PyTorch 原生格式（确保 ./out 目录下有对应权重）
python eval_llm.py --load_from ./model --weight full_sft
```

**WebUI**（可选）：

```bash
# 先复制模型到 scripts 目录
cp -r minimind-3 ./scripts/minimind-3

# 启动 Streamlit
cd scripts && streamlit run web_demo.py
```

### 4.3 模型训练

**第一步：下载数据**

从 [ModelScope](https://www.modelscope.cn/datasets/gongjy/minimind_dataset/files) 或 [HuggingFace](https://huggingface.co/datasets/jingyaogong/minimind_dataset/tree/main) 下载数据，放入 `./dataset/` 目录。

**推荐下载（快速复现）**：

```text
pretrain_t2t_mini.jsonl  (~1.2GB)
sft_t2t_mini.jsonl       (~1.6GB)
```

**第二步：预训练（必须）**

```bash
cd trainer

# 单卡训练
python train_pretrain.py

# 或使用 torchrun（多卡）
torchrun --nproc_per_node 1 train_pretrain.py
```

训练后输出：`out/pretrain_*.pth`

**第三步：SFT（必须）**

```bash
cd trainer
python train_full_sft.py
```

训练后输出：`out/full_sft_*.pth`

**第四步：测试模型**

```bash
python eval_llm.py --weight full_sft
```

## 五、配置选项详解

以下默认值直接来自各训练脚本的 argparse 定义（仓库当前主线），与早期版本可能不同。

### 5.1 预训练配置

入口 `trainer/train_pretrain.py`：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `epochs` | 2 | 训练轮数 |
| `batch_size` | 32 | 批大小 |
| `learning_rate` | 5e-4 | 初始学习率 |
| `max_seq_len` | 340 | 训练最大截断长度 |
| `grad_clip` | 1.0 | 梯度裁剪阈值 |

学习率按 cosine 调度衰减（`get_lr`，下限为初始值的 0.1 倍），权重默认保存到 `out/pretrain_*.pth`。README 建议快速复现时把 `max_seq_len` 调到约 768 配合 `*_mini` 数据。

### 5.2 SFT 配置

入口 `trainer/train_full_sft.py`：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `epochs` | 2 | 训练轮数 |
| `batch_size` | 16 | 批大小 |
| `learning_rate` | 1e-5 | 初始学习率，比预训练小约两个数量级 |
| `max_seq_len` | 768 | 训练最大截断长度 |

SFT 学习率调低是为了在注入指令跟随能力时尽量不破坏预训练学到的语言能力；权重默认保存到 `out/full_sft_*.pth`。

### 5.3 LoRA 配置

LoRA 在 `model/model_lora.py` 中原生实现：对所有输入输出维度相等的 Linear 层挂一个低秩分支 A·B，`apply_lora` 默认秩 `rank=16`；A 用高斯初始化、B 用全零初始化，训练开始时分支输出为 0，不改变原模型行为。`trainer/train_lora.py` 的默认参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `epochs` | 10 | 训练轮数 |
| `batch_size` | 32 | 批大小 |
| `learning_rate` | 1e-4 | 初始学习率 |
| `max_seq_len` | 340 | 训练最大截断长度 |
| `lora_name` | `lora_medical` | LoRA 权重名称 |

README 提到 `train_lora.py` 在 CPU 上通常也能较快跑完，适合没有 GPU 的环境体验微调流程。

## 六、知识蒸馏

MiniMind 同时支持黑盒蒸馏和白盒蒸馏两种思路。

**黑盒蒸馏**（更常见）：对教师模型输出做监督微调。MiniMind 当前主线 full_sft 数据里已混入大量黑盒蒸馏信号（如 DeepSeek R1、Qwen3 的高质量回答）。

$$\mathcal{L}_{blackbox} = \mathrm{CE}(y_{teacher}, p_{student})$$

**白盒蒸馏**（更精细）：额外拟合教师模型的 token（词元）分布。`train_distillation.py` 在已完成 SFT 的权重基础上，继续用教师模型提供的分布信号训练学生模型，README 建议把它作为理解白盒蒸馏流程的参考实现。

$$\mathcal{L}_{whitebox} = \alpha \mathcal{L}_{CE} + (1-\alpha) T^2 \mathrm{KL}(p_t^T \parallel p_s^T)$$

其中 $\alpha$ 为 CE 损失权重，$T$ 为温度参数，$p_t^T$ 和 $p_s^T$ 分别为教师和学生模型在温度 $T$ 下的 softmax 分布。

```bash
cd trainer
torchrun --nproc_per_node 1 train_distillation.py
```

## 七、强化学习：统一视角

MiniMind 的 RL 训练覆盖 DPO、PPO、GRPO、CISPO 和 Agentic RL。这些算法并非割裂独立，而是在统一优化视角下对同一目标函数的不同设计权衡。

### 7.1 统一框架

所有 Policy Optimization (PO) 算法实际上都在优化同一个期望：

$$\mathcal{J}_{PO} = \mathbb{E}_{q \sim P(Q), o \sim \pi(O|q)} \left[ \underbrace{f(r_t)}_{\text{策略项}} \cdot \underbrace{g(A_t)}_{\text{优势项}} - \underbrace{h(KL_t)}_{\text{正则项}} \right]$$

不同算法只是对这三个组件的不同实例化：

| 算法 | 策略项 $f(r_t)$ | 优势项 $g(A_t)$ | 正则项 $h(KL_t)$ | 训练模型数 |
|------|------------------|------------------|-------------------|-----------|
| **DPO** | $\log r_w - \log r_l$ | 无显式优势项 | 隐含在 $\beta$ 中 | 1（前向参与 2） |
| **PPO** | $\min(r, \text{clip}(r))$ | $R - V(s)$ | $\beta \cdot \mathbb{E}[KL]$ | 2 |
| **GRPO** | $\min(r, \text{clip}(r))$ | $\frac{R - \mu}{\sigma}$ | $\beta \cdot KL_t$ | 1 |
| **CISPO** | $\text{clip}(r, 0, \epsilon_{max}) \cdot A_t \cdot \log \pi_\theta$ | $\frac{R - \mu}{\sigma}$ | $\beta \cdot KL_t$ | 1 |

### 7.2 DPO：直接偏好优化

DPO 从 PPO 带 KL 约束的目标推导出对偏好对的解析训练目标，直接最大化"chosen 优于 rejected"的对数几率，无需同步训练 Reward/Value 模型。

$$\mathcal{L}_{DPO} = -\mathbb{E}\left[\log \sigma\left(\beta\left[\log \frac{\pi_\theta(y_w|x)}{\pi_{ref}(y_w|x)} - \log \frac{\pi_\theta(y_l|x)}{\pi_{ref}(y_l|x)}\right]\right)\right]$$

训练范式：Off-policy，使用静态偏好数据集，Ref 模型固定（预先缓存输出）。

```bash
cd trainer
python train_dpo.py
```

### 7.3 PPO：近端策略优化

PPO 是 LLM RL 领域最常见的基线方法，包含 Actor（生成回答）和 Critic（评估回答价值）双网络：

$$\mathcal{L}_{PPO} = -\mathbb{E}\left[\min(r_t \cdot A_t, \text{clip}(r_t, 1-\epsilon, 1+\epsilon) \cdot A_t)\right] + \beta \cdot \mathbb{E}[KL]$$

PPO 需要同时维护两个网络，显存占用约为单网络方法的 1.5-2 倍。训练初期 Critic 估计不准会影响 Actor 梯度方向，导致收敛缓慢。

```bash
cd trainer
python train_ppo.py
```

### 7.4 GRPO：组相对策略优化

GRPO 的核心创新是"分组相对价值估计"：对同一个问题生成 N 个回答并计算各自奖励，用组内平均奖励作为 baseline。高于 baseline 的回答被鼓励，低于 baseline 的被抑制，无需额外训练 Critic 网络。

$$\mathcal{L}_{GRPO} = -\mathbb{E}\left[\min(r_t \cdot A_t, \text{clip}(r_t, 1-\epsilon, 1+\epsilon) \cdot A_t) - \beta \cdot KL_t\right]$$

GRPO 的 reward 呈现更稳定的上升趋势，相比 PPO 的双网络优化，单网络架构训练更稳定且收敛上限更高。

需要注意退化组（Degenerate Groups）问题：如果某个问题上 N 个回答的奖励几乎一样，学习信号接近 0。在超小模型上尤其明显。

```bash
cd trainer
python train_grpo.py
```

### 7.5 CISPO：裁剪重要性采样策略优化

CISPO 关注 PPO/GRPO 中 ratio 被 clip 后梯度流被硬截断的问题。它把策略项改写为"裁剪权重 × log 概率"的形式，使 ratio 即使被截断也不会把梯度路径一起截断。

$$\mathcal{L}_{CISPO} = -\mathbb{E}\left[\min(r_t, \epsilon_{max}) \cdot A_t \cdot \log \pi_\theta(a_t|s) - \beta \cdot KL_t\right]$$

CISPO 可直接视作 GRPO 的 loss 变体：在 `train_grpo.py` 中把 `loss_type` 配置为 `cispo` 即可。

### 7.6 Agentic RL

MiniMind 的 Agentic RL 聚焦于让百 M 小模型在有限工具集上学会基础的调用、观察与再规划能力。训练脚本 `train_agent.py` 把 RLVR/RLAIF 风格的数据组织方式与 online RL 的 rollout 过程结合。

数据格式为 `agent_rl.jsonl` / `agent_rl_math.jsonl`，相比普通对话数据多了 `gt`（Ground Truth）作为最终校验目标。训练时优化的不再是单轮回答 $y$，而是一条多轮轨迹 $\tau$：

$$\tau = (a_1, o_1, a_2, o_2, \ldots, a_T), \quad a_t \sim \pi_\theta(\cdot|s_t, \mathcal{T})$$

奖励对整条轨迹联合打分：

$$R(\tau) = R_{answer} + R_{tool} + R_{format} + R_{rm} - R_{unfinished}$$

同时考虑工具调用合法性、gt 命中、格式闭合、未完成惩罚与 Reward Model 分数。和普通 PPO/GRPO 相比，这是多轮 rollout、延迟 reward 的范式。

```bash
cd trainer
python train_agent.py
```

### 7.7 奖励稀疏问题

对于 MiniMind 这种 0.1B 参数量极小的模型，在通用任务上会遇到严重的奖励稀疏（Reward Sparsity）问题：模型生成的候选回答几乎全部错误，导致所有奖励分数 $r(x,y) \approx 0$，优势函数 $A(x,y) \approx 0$，策略梯度信号消失。

为缓解此问题，MiniMind 选择 model-based 的连续性奖励信号（如 InternLM2-1.8B-Reward），而非 rule-based 的二元奖励。即使回答质量都差，也能区分"更差"（-3.0）和"没那么差"（-2.8）的细微差异，为优势函数提供非零梯度。

### 7.8 RL 数据准备

| 数据集 | 大小 | 用途 |
|--------|------|------|
| `dpo.jsonl` | 53MB | DPO 偏好训练（chosen vs rejected） |
| `rlaif.jsonl` | 24MB | PPO/GRPO/CISPO 训练 |
| `agent_rl.jsonl` | 86MB | Agentic RL 多轮 Tool-Use 训练 |
| `agent_rl_math.jsonl` | 18MB | Agentic RL 数学补充数据 |

## 八、工具调用与自适应思考

### 8.1 Tool Calling

当前 toolcall 能力已并入 `sft_t2t` / `sft_t2t_mini` 主线数据，默认 full_sft 即具备基础 Tool Call 能力。训练数据主要由 qwen3-4b 采样约 10w 条构成，工具列表覆盖约 10 个模拟的自定义工具（例如查询时间、数学计算、获取天气）。

数据格式遵循 OpenAI 风格：`tools` 挂在 `system` 消息上，`tool_calls` 挂在 `assistant` 消息上，训练时由 `chat_template` 自动展开为 `<tool_call>` 与 `<tool_response>` 片段：

```json
{"conversations": [
  {"role": "user", "content": "帮我算一下 256 乘以 37"},
  {"role": "assistant", "content": "", "tool_calls": "[{\"name\":\"calculate_math\",\"arguments\":{\"expression\":\"256 * 37\"}}]"},
  {"role": "tool", "content": "{\"result\":\"9472\"}"},
  {"role": "assistant", "content": "256 乘以 37 等于 9472。"}
]}
```

测试工具调用：

```bash
python eval_toolcall.py --weight full_sft
```

### 8.2 自适应思考

MiniMind 将显式思考能力统一到模板层，与主流大模型的模板设计保持一致：

- `open_thinking=0`：默认注入空的 `<think>\n\n</think>`，模型倾向直接回答
- `open_thinking=1`：模板预先注入 `<think>` 起始标签，模型输出显式思考过程与最终回答

CLI、OpenAI API（应用程序接口）、WebUI 三个入口均支持该开关：

```bash
python eval_llm.py --load_from ./minimind-3 --open_thinking 1
```

> 注意：当前同时开启 Tool Call 与显式思考时，模型通常不太稳定。原因在于训练数据里缺少"reasoning 与 tool call 同时存在"的联合蒸馏样本。

## 九、框架集成

### 9.1 导出为 HuggingFace 格式

```python
# 使用 transformers 加载
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("./minimind-3")
tokenizer = AutoTokenizer.from_pretrained("./minimind-3")
```

### 9.2 导出为 llama.cpp 格式

按 README 的流程，先克隆 llama.cpp 并与模型目录放在同级路径，然后在 `convert_hf_to_gguf.py` 的 `get_vocab_base_pre` 函数末尾补一段 MiniMind tokenizer 兼容分支（临时复用 qwen2 项），再执行转换与量化：

```bash
# 在 llama.cpp 目录下执行，将在模型目录下生成对应的 gguf 文件
python convert_hf_to_gguf.py /path/to/minimind-model

# 量化（可选）
./build/bin/llama-quantize /path/to/model/xxxx.gguf /path/to/model/xxxx.q8.gguf Q8_0
```

### 9.3 使用 ollama 部署

```bash
ollama run jingyaogong/minimind-3
```

### 9.4 使用 vllm 部署

需要 CUDA 环境，以 OpenAI 兼容 API 服务形式启动：

```bash
vllm serve /path/to/model --model-impl transformers --served-model-name "minimind" --port 8998
```

## 十、RoPE 长度外推

MiniMind 支持通过 YaRN 算法进行 RoPE 位置编码的长度外推，使模型能够更稳定地处理超出训练长度的文本序列。

原生 torch 模型推理时添加参数即可启用：

```bash
python eval_llm.py --weight full_sft --inference_rope_scaling
```

Transformers 格式模型可在 `config.json` 中配置（参数与 `model_minimind.py` 的默认 rope_scaling 一致）：

```json
{
  "rope_scaling": {"type": "yarn", "factor": 16.0,
    "original_max_position_embeddings": 2048,
    "beta_fast": 32.0, "beta_slow": 1.0, "attention_factor": 1.0}
}
```

README 用不同长度的《西游记》白话文本做过对比：启用 YaRN 外推后，长文本场景下模型的困惑度（PPL）明显下降。

## 十一、OpenAI API 兼容服务

MiniMind 提供兼容 OpenAI API（应用程序接口）的轻量聊天服务，便于接入 FastGPT、Open-WebUI、Dify 等第三方 UI：

```bash
cd scripts && python serve_openai_api.py
```

测试接口：

```bash
cd scripts && python chat_api.py
```

API 请求示例：

```bash
curl http://localhost:8998/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "model-identifier",
       "messages": [{"role": "user", "content": "世界上最高的山是什么？"}],
       "temperature": 0.7, "max_tokens": 1024,
       "stream": true, "open_thinking": true}'
```

接口额外支持 `reasoning_content`、`tool_calls`、`open_thinking` 等字段。

## 十二、推荐做法

### 12.1 训练稳定性

仓库训练器已内置的默认做法，直接沿用即可：

1. **梯度裁剪**：各 trainer 默认 `grad_clip=1.0`，防止梯度爆炸
2. **学习率调度**：`get_lr` 按 cosine 衰减，下限为初始学习率的 0.1 倍，无额外 warmup 步骤
3. **混合精度**：CUDA 设备上默认走 autocast，`--dtype` 可选 bf16 / fp16 等

### 12.2 成本优化

1. **从小数据开始**：先用 `*_mini.jsonl` 快速验证流程
2. **LoRA 优先**：如只需微调，优先使用 LoRA（成本低、速度快）
3. **单卡起步**：单张 3090 即可复现 MiniMind Zero 全流程，多卡再用 DDP

### 12.3 模型选择建议

| 场景 | 推荐模型 | 理由 |
|------|----------|------|
| 快速验证概念 | minimind-3 (64M) | 训练最快、成本最低 |
| 平衡性能与成本 | minimind2 (104M) | 性价比最优 |
| 追求更高性能 | minimind-3-moe (198M) | 激活参数量最小 |

## 十三、动手练习与自测

### 练习

1. **推理对比**：下载 minimind-3 权重后运行 `python eval_llm.py --load_from ./minimind-3`，先用默认参数问几个问题，再加 `--open_thinking 1` 重问一遍，观察思考过程对回答的影响。
2. **复现训练**：只下载 `pretrain_t2t_mini.jsonl` 与 `sft_t2t_mini.jsonl`，在单卡上依次跑通预训练与 SFT，记录实际耗时并与官方的约 2 小时口径对比。
3. **RL 算法切换**：在 `train_grpo.py` 中把 `--loss_type` 在 `grpo` 与 `cispo` 之间切换，观察 reward 曲线的差异，对照 §7.5 理解两者在梯度截断上的区别。

### 自测

1. 为什么 SFT 的默认学习率（1e-5）比预训练（5e-4）低约两个数量级？
2. GRPO 用什么代替了 PPO 中的 Critic 网络？为什么它对超小模型更友好？
3. MiniMind 的 RL 为什么选择奖励模型打分而不是规则二元奖励？（提示：参考 §7.7 奖励稀疏问题）
4. `open_thinking` 与 Tool Call 同时开启时为什么容易不稳定？

参考答案均可在本文对应章节与仓库 README 中找到。

## 十四、进阶方向

- **读透 PO 统一视角**：对照 README 的"PO 算法统一视角"章节，把 DPO / PPO / GRPO / CISPO 的策略项、优势项、正则项逐个在源码里找到对应实现。
- **切换 rollout 后端**：`trainer/rollout_engine.py` 把参数更新与轨迹展开解耦，可尝试接入 SGLang 等远端推理引擎提升采样吞吐。
- **换数据做自己的任务**：参照 `dataset/dataset.md` 的格式把自有数据整理成 jsonl，替换 `*_mini` 数据重新训练，验证数据质量对小模型的影响。
- **扩展 MoE 规模**：修改 `model_minimind.py` 中的 `num_experts` 与 `num_experts_per_tok`，观察训练耗时变化，理解 README 所说的 kernel 启停开销。
- **部署上线**：把权重转成 GGUF 量化后交给 llama.cpp / ollama，或用 `serve_openai_api.py` 接入 Open-WebUI、FastGPT 等前端。

## 十五、常见问题

**Q: 训练需要什么显卡？**

A: 官方教程以单张 NVIDIA 3090 为基准，MiniMind Zero 全流程约 2 小时可复现；显存更小的环境可以调低 `batch_size`，或先用 LoRA 体验微调。

**Q: 可以用 CPU 训练吗？**

A: 可以。README 说明 CUDA 不可用时可选择 CPU 或 MPS 运行，但训练速度差异很大；`train_lora.py` 在 CPU 上通常也能较快跑完，预训练和 SFT 仍建议用 GPU。

**Q: 如何延长上下文长度？**

A: 通过 YaRN 外推技术，可以在推理时免训练地将上下文扩展到 2048 及以上（见 §10）。

**Q: 训练数据从哪里来？**

A: 项目提供了预处理好的数据集，包括预训练数据、SFT 数据、RLHF 偏好数据与 Agentic RL 数据，可从 ModelScope 或 HuggingFace 下载（见 §17 参考文献）。

**Q: 如何进行模型量化？**

A: llama.cpp 路线用 `llama-quantize` 对 GGUF 量化（如 Q8_0）；transformers 路线可结合第三方量化库按需选择。

## 十六、总结

MiniMind 在开源 LLM 训练领域做了一件少见的事：真正从零训练（不是微调），3 元钱 2 小时跑完全流程，预训练到 RLHF 到工具调用一条线打通，核心算法全部 PyTorch 原生实现，训练完的权重可以直接扔进 transformers、ollama、vllm 跑推理。

入门学习者可以用它弄懂"训练一个 LLM 到底要经历哪些步骤"；有经验的开发者可以拿它当基座，验证自己的训练策略或对比不同 RL 算法的效果。

## 十七、参考文献

本文事实均以下列来源为准，统计数字为 2026-08-19 通过 GitHub API 实时查询：

- [MiniMind GitHub 仓库](https://github.com/jingyaogong/minimind)：项目源码与 README，本文的结构、成本、算法说明主要出处
- [MiniMind 模型权重（HuggingFace）](https://huggingface.co/jingyaogong/minimind-3)
- [MiniMind 数据集（ModelScope）](https://www.modelscope.cn/datasets/gongjy/minimind_dataset/files)：预训练 / SFT / RL 数据下载
- [MiniMind 数据集（HuggingFace）](https://huggingface.co/datasets/jingyaogong/minimind_dataset/tree/main)
- [DPO-En-Zh-20k](https://huggingface.co/datasets/llamafactory/DPO-En-Zh-20k)：`dpo.jsonl` 的抽样来源
- [InternLM2-1.8B-Reward](https://huggingface.co/internlm/internlm2-1_8b-reward)：RL 训练默认演示用的奖励模型
- [MiniMind 视频介绍（Bilibili）](https://www.bilibili.com/video/BV12dHPeqE72)