---
title: "MiniMind：从零开始用3块钱训练64M参数的大语言模型"
date: 2026-03-29T15:51:00+08:00
slug: "minimind-llm-training-from-scratch"
description: "MiniMind 是 44.4k Stars 的开源 LLM 训练项目，3 元钱 + 2 小时即可训练 64M 参数模型。覆盖预训练、SFT、LoRA、RLHF、工具调用的完整链路。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "大模型训练", "PyTorch", "MoE", "RLHF"]
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

## 六、进阶训练

### 6.1 知识蒸馏（Knowledge Distillation）

**黑盒蒸馏**（更常见）：对教师模型输出做监督微调

$$\mathcal{L}_{blackbox} = \mathrm{CE}(y_{teacher}, p_{student})$$

**白盒蒸馏**（更精细）：额外拟合教师模型的 token 分布

$$\mathcal{L}_{whitebox} = \alpha \mathcal{L}_{CE} + (1-\alpha) T^2 \mathrm{KL}(p_t^T \parallel p_s^T)$$

```bash
cd trainer
torchrun --nproc_per_node 1 train_distillation.py
```

### 6.2 DPO 偏好优化

DPO（Direct Preference Optimization）是一种简化的 RLHF 方法：

```bash
cd trainer
python train_dpo.py
```

### 6.3 RLAIF 基于 AI 反馈的强化学习

支持 PPO、GRPO、CISPO 等多种算法：

```bash
cd trainer
python train_rlaif.py    # PPO
python train_grpo.py     # GRPO / CISPO
```

### 6.4 工具调用训练

```bash
cd trainer
python train_tool.py
```

## 七、框架集成

### 7.1 导出为 HuggingFace 格式

```python
# 使用 transformers 加载
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("./minimind-3")
tokenizer = AutoTokenizer.from_pretrained("./minimind-3")
```

### 7.2 导出为 llama.cpp 格式

```bash
# 转换模型
python -m llama_cpp.convert --model-file ./minimind-3 --output-file ./minimind-3.bin

# 量化（可选）
./quantize ./minimind-3.bin ./minimind-3-q4.bin q4_0
```

### 7.3 使用 ollama 部署

```bash
ollama run jingyaogong/minimind-3
```

### 7.4 使用 vllm 部署

```bash
vllm serve /path/to/model --served-model-name minimind
```

## 八、最佳实践

### 8.1 训练稳定性

1. **使用 warmup**：预热步数有助于训练稳定
2. **梯度裁剪**：设置 `max_grad_norm=1.0` 防止梯度爆炸
3. **学习率调度**：使用 cosine 或 linear 衰减

### 8.2 成本优化

1. **从小数据开始**：先用 `*_mini.jsonl` 快速验证流程
2. **LoRA 优先**：如只需微调，优先使用 LoRA（成本低、速度快）
3. **混合精度**：使用 FP16/BF16 加速训练

### 8.3 模型选择建议

| 场景 | 推荐模型 | 理由 |
|------|----------|------|
| 快速验证概念 | minimind-3 (64M) | 训练最快、成本最低 |
| 平衡性能与成本 | minimind2 (104M) | 性价比最优 |
| 追求更高性能 | minimind-3-moe (198M) | 激活参数量最小 |

## 九、常见问题

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

## 十、总结

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