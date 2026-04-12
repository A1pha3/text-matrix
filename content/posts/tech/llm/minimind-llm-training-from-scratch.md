---
title: "MiniMind：从零开始用3块钱训练64M参数的大语言模型"
date: 2026-04-12T12:00:00+08:00
slug: "minimind-llm-training-from-scratch"
aliases:
  - /posts/tech/minimind-llm-training-from-scratch/
description: "MiniMind 是 44.4k Stars 的开源 LLM 训练项目，3 元钱 + 2 小时即可训练 64M 参数模型。覆盖预训练、SFT、LoRA、DPO、PPO、GRPO、CISPO、Agentic RL、工具调用的完整链路，所有核心算法从零 PyTorch 原生实现。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "大模型训练", "PyTorch", "MoE", "RLHF", "GRPO", "强化学习"]
---

# MiniMind：从零开始用3块钱训练64M参数的大语言模型

## 一、项目概览

**MiniMind** 是由 jingyaogong 开发的开源大语言模型训练项目，其核心理念是"大道至简"——让每个人都能从零开始，仅用约 3 元钱成本与 2 小时训练时间，即可训练出规模约为 64M 参数的超小型语言模型 MiniMind。

该项目在 GitHub 上获得了 **44.4k Stars** 和 **5.3k Forks**，成为开源 LLM 训练领域的标杆项目。

### 1.1 核心定位

大语言模型（Large Language Model, LLM）的出现引发了全球范围内对 AI 的空前关注。然而，动辄数百亿参数的模型规模使得它们对个人设备而言不仅难以训练，甚至连部署都显得遥不可及。

MiniMind 的诞生正是为了打破这一困境：

1. **从零开始训练**：不是仅仅使用 LoRA 等技术微调现有大模型，而是真正从零开始构建语言模型
2. **极低训练成本**：最低只需不到 3 元钱的服务器成本，即可亲身体验从 0 到 1 构建语言模型的全过程
3. **完全透明可控**：所有核心算法代码均从 0 使用 PyTorch 原生实现，不依赖第三方库提供的高层抽象接口

### 1.2 技术统计

| 指标 | 数值 |
|------|------|
| Stars | 44.4k |
| Forks | 5.3k |
| Commits | 320 |
| 最新提交 | 2026-03-27 |
| 许可证 | Apache-2.0 |
| 主要语言 | Python |

### 1.3 已发布模型

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

### 2.1 全链路训练流程覆盖

MiniMind 提供了从预训练到强化学习的完整训练链路：

| 训练阶段 | 说明 | 核心文件 |
|----------|------|----------|
| **Tokenizer** | 分词器训练，支持 `<tool_call>`、`<tool_response>`、`<think>` 等模板标记 | `train_tokenizer.py` |
| **Pretrain** | 预训练，学习基础语言能力和世界知识 | `train_pretrain.py` |
| **SFT** | 监督微调，指令跟随与对话能力 | `train_full_sft.py` |
| **LoRA** | 低秩适配，参数高效微调 | `train_lora.py` |
| **KD** | 知识蒸馏，从大模型提取知识 | `train_distillation.py` |
| **DPO** | 直接偏好优化，RLHF 简化版 | `train_dpo.py` |
| **RLAIF** | 基于 AI 反馈的强化学习 | `train_rlaif.py` |
| **GRPO/CISPO** | 新型强化学习算法 | `train_grpo.py` |
| **Tool Use** | 工具调用能力 | `train_tool.py` |
| **Agentic RL** | 智能体强化学习 | `train_agentic_rl.py` |

### 2.2 核心技术特性

1. **原生 PyTorch 实现**：所有核心算法从 0 实现，不依赖 transformers/trl/peft 等高层抽象
2. **MoE 混合专家**：支持 Dense + MoE 两种架构
3. **长文本支持**：通过 YaRN 实现 RoPE 长文本外推
4. **多框架兼容**：兼容 transformers、trl、peft、llama.cpp、vllm、ollama、Llama-Factory
5. **可视化支持**：wandb / swanlab 训练可视化
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

minimind-3 采用 Transformer Decoder-Only 结构，配置向 Qwen3 / Qwen3-MoE 生态对齐：

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
- GQA（Grouped Query Attention）

### 3.2 MoE 架构

minimind-3-moe 在相同结构上扩展 MoE 前馈层：

- 默认配置：**4 experts / top-1 routing**
- 相比同尺寸 Dense 模型，训练慢约 **50%**（因原生 PyTorch 未做 kernel fusion）
- 如需更优性能，可基于 Triton 自定义 kernel、DeepSpeed-MoE、Megatron-LM 优化

### 3.3 项目结构

```
minimind/
├── model/                    # 模型结构定义
│   └── model_minimind.py    # MiniMind 系列模型
├── trainer/                  # 训练器
│   ├── train_pretrain.py    # 预训练
│   ├── train_full_sft.py    # 全参数 SFT
│   ├── train_lora.py         # LoRA 微调
│   ├── train_distillation.py # 知识蒸馏
│   ├── train_dpo.py          # DPO 偏好优化
│   ├── train_rlaif.py        # RLAIF
│   ├── train_grpo.py         # GRPO / CISPO
│   └── train_tool.py         # 工具调用
├── dataset/                  # 数据集目录
├── scripts/                  # 脚本
│   └── web_demo.py           # Streamlit WebUI
├── out/                      # 输出权重目录
└── eval_llm.py              # 模型评估
```

### 3.4 数据流程

```
原始数据
    ↓
[数据清洗 + 去重 + 格式统一]
    ↓
Tokenizer 训练
    ↓
Pretrain 预训练
    ↓
SFT 监督微调
    ↓
[可选] LoRA / DPO / RLAIF / Tool Use / Agentic RL
    ↓
模型权重 (.pth)
    ↓
[导出] HuggingFace / llama.cpp / vllm / ollama
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

**CLI 推理**：

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

```
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

### 5.1 预训练配置

关键参数在 `train_pretrain.py` 中：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `dim` | 768 | 模型维度 |
| `n_layers` | 8 | 层数 |
| `seq_len` | 512 | 序列长度 |
| `batch_size` | 16 | 批大小 |
| `lr` | 1e-3 | 学习率 |
| `warmup_steps` | 100 | 预热步数 |

### 5.2 SFT 配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `dim` | 768 | 模型维度（需与预训练一致） |
| `seq_len` | 512 | 序列长度 |
| `batch_size` | 8 | 批大小 |
| `lr` | 5e-5 | 学习率（比预训练小） |
| `epoch` | 3 | 训练轮次 |

### 5.3 LoRA 配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `lora_rank` | 8 | LoRA 秩 |
| `lora_alpha` | 16 | LoRA alpha |
| `lora_dropout` | 0.05 | Dropout |
| `target_modules` | ["q_proj", "k_proj", "v_proj", "o_proj"] | 目标模块 |

## 六、知识蒸馏

MiniMind 同时支持黑盒蒸馏和白盒蒸馏两种思路。

**黑盒蒸馏**（更常见）：对教师模型输出做监督微调。MiniMind 当前主线 full_sft 数据里已混入大量黑盒蒸馏信号（如 DeepSeek R1、Qwen3 的高质量回答）。

$$\mathcal{L}_{blackbox} = \mathrm{CE}(y_{teacher}, p_{student})$$

**白盒蒸馏**（更精细）：额外拟合教师模型的 token 分布。`train_distillation.py` 在已完成 SFT 的权重基础上，继续用教师模型提供的分布信号训练学生模型。

$$\mathcal{L}_{whitebox} = \alpha \mathcal{L}_{CE} + (1-\alpha) T^2 \mathrm{KL}(p_t^T \parallel p_s^T)$$

其中 $\alpha$ 为 CE 损失权重，$T$ 为温度参数，$p_t^T$ 和 $p_s^T$ 分别为教师和学生模型在温度 $T$ 下的 softmax 分布。

```bash
cd trainer
torchrun --nproc_per_node 1 train_distillation.py
```

## 七、强化学习：统一视角

MiniMind 的 RL 训练覆盖 DPO、PPO、GRPO、CISPO 和 Agentic RL。这些算法并非割裂独立，而是在统一优化视角下对同一目标函数的不同设计权衡。

### 7.1 统一框架

所有 Policy Optimization (PO) 算法本质上都在优化同一个期望：

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

为缓解此问题，MiniMind 选择 model-based 的连续性奖励信号（如 InternLM2-1.8B-Reward），而非 rule-based 的二元奖励。即使回答质量都差，也能区分"更差"(-3.0)和"更差"(-2.8)的细微差异，为优势函数提供非零梯度。

### 7.8 RL 数据准备

| 数据集 | 大小 | 用途 |
|--------|------|------|
| `dpo.jsonl` | 53MB | DPO 偏好训练（chosen vs rejected） |
| `rlaif.jsonl` | 24MB | PPO/GRPO/CISPO 训练 |
| `agent_rl.jsonl` | 86MB | Agentic RL 多轮 Tool-Use 训练 |
| `agent_rl_math.jsonl` | 18MB | Agentic RL 数学补充数据 |

## 八、工具调用与自适应思考

### 8.1 Tool Calling

当前 toolcall 能力已并入 `sft_t2t` / `sft_t2t_mini` 主线数据，默认 full_sft 即具备基础 Tool Call 能力。训练数据主要由 qwen3-4b 采样约 10w 条构成，工具列表覆盖约 10 个模拟的自定义工具。

数据格式遵循 OpenAI 风格：

```json
{
  "conversations": [
    {"role": "system", "content": "# Tools ...", "tools": "[...]"},
    {"role": "user", "content": "帮我算一下 256 乘以 37"},
    {"role": "assistant", "content": "", "tool_calls": "[{\"name\":\"calculate_math\",\"arguments\":{\"expression\":\"256 * 37\"}}]"},
    {"role": "tool", "content": "{\"result\":\"9472\"}"},
    {"role": "assistant", "content": "256 乘以 37 等于 9472。"}
  ]
}
```

测试工具调用：

```bash
python eval_toolcall.py --weight full_sft
```

### 8.2 自适应思考

MiniMind 将显式思考能力统一到模板层，与主流大模型的模板设计保持一致：

- `open_thinking=0`：默认注入空的 `<think/>\n\n`，模型直接回答
- `open_thinking=1`：模板注入 `<think/>` 起始标签，模型输出显式思考过程

CLI、OpenAI-API、WebUI 三个入口均支持该开关：

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

```bash
# 转换模型
python -m llama_cpp.convert --model-file ./minimind-3 --output-file ./minimind-3.bin

# 量化（可选）
./quantize ./minimind-3.bin ./minimind-3-q4.bin q4_0
```

### 9.3 使用 ollama 部署

```bash
ollama run jingyaogong/minimind-3
```

### 9.4 使用 vllm 部署

```bash
vllm serve /path/to/model --served-model-name minimind
```

## 十、RoPE 长度外推

MiniMind 支持通过 YaRN 算法进行 RoPE 位置编码的长度外推，使模型能够更稳定地处理超出训练长度的文本序列。

原生 torch 模型推理时添加参数即可启用：

```bash
python eval_llm.py --weight full_sft --inference_rope_scaling
```

Transformers 格式模型可在 `config.json` 中配置：

```json
{
  "rope_scaling": {
    "type": "yarn",
    "factor": 16.0,
    "original_max_position_embeddings": 2048,
    "beta_fast": 32.0,
    "beta_slow": 1.0,
    "attention_factor": 1.0
  }
}
```

启用 YaRN 外推后，在长文本场景下模型的 PPL 明显下降。

## 十一、OpenAI API 兼容服务

MiniMind 提供兼容 OpenAI API 的轻量聊天服务，便于接入 FastGPT、Open-WebUI、Dify 等第三方 UI：

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
  -d '{
    "model": "minimind",
    "messages": [
      {"role": "user", "content": "世界上最高的山是什么？"}
    ],
    "temperature": 0.7,
    "max_tokens": 1024,
    "stream": true,
    "open_thinking": true
  }'
```

接口额外支持 `reasoning_content`、`tool_calls`、`open_thinking` 等字段。

## 十二、最佳实践

### 12.1 训练稳定性

1. **使用 warmup**：预热步数有助于训练稳定
2. **梯度裁剪**：设置 `max_grad_norm=1.0` 防止梯度爆炸
3. **学习率调度**：使用 cosine 或 linear 衰减

### 12.2 成本优化

1. **从小数据开始**：先用 `*_mini.jsonl` 快速验证流程
2. **LoRA 优先**：如只需微调，优先使用 LoRA（成本低、速度快）
3. **混合精度**：使用 FP16/BF16 加速训练

### 12.3 模型选择建议

| 场景 | 推荐模型 | 理由 |
|------|----------|------|
| 快速验证概念 | minimind-3 (64M) | 训练最快、成本最低 |
| 平衡性能与成本 | minimind2 (104M) | 性价比最优 |
| 追求更高性能 | minimind-3-moe (198M) | 激活参数量最小 |

## 十三、常见问题

**Q: 训练需要多少显存？**

A: minimind-3 (64M) 在 3090 上约需 8GB 显存。minimind-3-moe (198M) 约需 16GB。

**Q: 可以用 CPU 训练吗？**

A: 可以使用 LoRA 进行 CPU 训练（`train_lora.py`），但预训练和 SFT 建议使用 GPU。

**Q: 如何延长上下文长度？**

A: 通过 YaRN 外推技术，可以在推理时免训练地将上下文扩展到 2048 及以上。

**Q: 训练数据从哪里来？**

A: 项目提供了预处理好的数据集，包括预训练数据、SFT 数据、RLHF 偏好数据，可从 ModelScope 或 HuggingFace 下载。

**Q: 如何进行模型量化？**

A: 可使用 llama.cpp 进行量化，或使用 transformers 的 `BitsAndBytes` 进行 INT8/INT4 量化。

## 十四、总结

MiniMind 代表了开源 LLM 训练的新范式：

- ✅ **从零开始**：真正从零训练，不是简单的微调
- ✅ **极低门槛**：3 元钱、2 小时即可完成训练
- ✅ **全链路覆盖**：预训练、SFT、LoRA、RLHF、工具调用全覆盖
- ✅ **纯 PyTorch**：所有核心算法从 0 实现，透明可控
- ✅ **生态兼容**：无缝对接 transformers、ollama、vllm 等主流框架

无论你是 LLM 入门学习者，还是希望深入理解大模型训练原理的开发者，MiniMind 都是一个绝佳的起点。

---

**相关资源**：

- 🐙 [GitHub](https://github.com/jingyaogong/minimind)
- 🤗 [HuggingFace](https://huggingface.co/collections/jingyaogong/minimind)
- 📖 [ModelScope](https://www.modelscope.cn/studios/gongjy/MiniMind)
- 🎥 [视频介绍](https://www.bilibili.com/video/BV12dHPeqE72)