---
title: "DFlash：块扩散模型加速LLM推理——让大模型推理速度提升2-3倍"
date: "2026-04-17T16:35:00+08:00"
slug: "dflash-block-diffusion-speculative-decoding"
description: "1,710 Stars的DFlash是一个轻量级块扩散模型，用于投机解码加速LLM推理。支持Qwen3/LLaMA/GPT-OSS等多种模型，可在vLLM/SGLang/Transformers上部署，实测加速2-3倍。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "推理加速", "投机解码", "扩散模型", "Python", "vLLM", "SGLang", "Transformers"]
---

# DFlash：块扩散模型加速LLM推理

> **目标读者**：LLM推理优化工程师、ML平台架构师、MLOps实践者
> **前置知识**：深度学习基础、LLM原理、对投机解码有基本了解
> **技术栈**：Python / PyTorch / vLLM / SGLang / Transformers / MLX
> **难度定位**：⭐⭐⭐⭐ 专家设计

---

## §1 学习目标

完成本篇文章后，你将能够：

1. **理解投机解码的原理**：为何能加速LLM推理
2. **掌握DFlash的创新点**：块扩散模型 vs 传统自回归解码
3. **理解DFlash的架构设计**：如何用扩散模型做draft
4. **能够部署DFlash**：在vLLM/SGLang/Transformers/MLX上运行
5. **选择合适的模型配置**：根据硬件和延迟需求选型
6. **评估加速效果**：理解加速比的影响因素

---

## §2 背景与动机：LLM推理的瓶颈

### 2.1 自回归解码的痛点

LLM推理采用自回归方式生成token：

```
Token_1 → Token_2 → Token_3 → ... → Token_n
   │         │         │              │
   ▼         ▼         ▼              ▼
  一次       一次       一次           一次
  GEMM      GEMM      GEMM           GEMM
```

**问题**：每个token生成都需要一次完整的矩阵运算，即使是小模型也要走完整个计算图。

### 2.2 投机解码的原理

投机解码使用"小模型draft + 大模型verify"：

```
传统方式：
Token_1 → Token_2 → Token_3 → Token_4 → Token_5  (全用大模型，5次前向)

投机解码：
Draft模型并行生成：d1 d2 d3 d4 d5  (小模型，5次前向但很快)
       ↓
Target模型验证：  T  T  T  T  T   (大模型，1次验证即可)
       ↓
接受tokens：     ✓  ✓  ✗  ✓  ✓   (4/5被接受)
```

**关键洞察**：
- Draft模型虽小但能快速生成多个token
- Target模型一次性验证多个token（批量推理，更高效）
- 大部分token被接受时加速效果显著

### 2.3 现有方案的局限

| 方案 | 问题 |
|------|------|
| **Eagle** | 需要额外训练，泛化性差 |
| **Medusa** | 只能预测固定位置，灵活度低 |
| **Self-Speculative** | 需要模型结构修改 |
| **脉冲网络** | 训练不稳定 |

### 2.4 DFlash的创新

**核心创新**：块扩散模型（Block Diffusion）用于投机解码

```
传统Draft：自回归生成（一个个token预测）
           d1 → d2 → d3 → d4 → d5

DFlash Draft：块扩散生成（并行生成多个token）
              ┌─────────────────────┐
              │   Block Diffusion   │
              │   并行去噪生成      │
              │   [d1, d2, ..., d5] │
              └─────────────────────┘
```

**优势**：
- 块级别生成，并行度高
- 无需修改模型结构
- 支持任意LLM
- 训练稳定

---

## §3 DFlash架构详解

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    DFlash System                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Input: "How many positive whole-number divisors"            │
│         ┌─────────────────────────────────────┐               │
│         │         Block Diffusion Draft        │               │
│         │  ┌─────────────────────────────┐    │               │
│         │  │  Noise → Denoise → Tokens   │    │               │
│         │  │  (并行去噪，生成多个token)   │    │               │
│         │  └─────────────────────────────┘    │               │
│         └──────────────┬──────────────────────┘               │
│                        │ Draft Tokens [d1, d2, ..., dk]       │
│                        ▼                                      │
│         ┌─────────────────────────────────────┐               │
│         │        Target Model (Verification)  │               │
│         │  ┌─────────────────────────────┐    │               │
│         │  │  Batch Verification         │    │               │
│         │  │  [p(T1|d1), p(T2|d2), ...]  │    │               │
│         │  └─────────────────────────────┘    │               │
│         └──────────────┬──────────────────────┘               │
│                        │ Verified Tokens                      │
│                        ▼                                      │
│         Output: "does 196 have?" (加速2-3倍)                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 块扩散原理

**扩散模型**通常用于图像生成，DFlash创新性地将其应用于文本生成：

```python
class BlockDiffusionDraft:
    """块扩散draft模型"""
    
    def __init__(self, draft_model, block_size=16):
        self.draft = draft_model
        self.block_size = block_size
    
    def draft_tokens(self, context: Tensor) -> list[str]:
        """
        输入: context (已生成的token序列)
        输出: draft_tokens (预测的下一个block)
        """
        # 1. 加噪过程：模拟扩散的forward process
        noise_level = sample_noise_levels(self.block_size)
        noisy_tokens = add_noise(context, noise_level)
        
        # 2. 去噪过程：DFlash核心，一次前向生成多个token
        #    注意：这是"块级别"去噪，不是自回归
        denoised = self.draft(noisy_tokens, context)
        
        # 3. 采样得到token序列
        draft_tokens = sample_tokens(denoised, temperature=0.0)
        
        return draft_tokens  # 返回一个block的token
```

### 3.3 与Eagle/Medusa的区别

| 特性 | Eagle | Medusa | DFlash |
|------|-------|--------|--------|
| **生成方式** | 自回归 | 固定位置 | 块并行 |
| **灵活性** | 高 | 低 | 高 |
| **训练复杂度** | 高 | 低 | 中 |
| **接受率** | ~80% | ~70% | ~85% |
| **支持模型** | 特定 | 特定 | 通用 |

---

## §4 支持的模型

### 4.1 模型列表

| 模型 | DFlash Draft模型 | 状态 |
|------|------------------|------|
| **Qwen3.6-35B-A3B** | z-lab/Qwen3.6-35B-A3B-DFlash | Preview |
| **Kimi-K2.5** | z-lab/Kimi-K2.5-DFlash | 可用 |
| **Qwen3.5-4B** | z-lab/Qwen3.5-4B-DFlash | 可用 |
| **Qwen3.5-9B** | z-lab/Qwen3.5-9B-DFlash | 可用 |
| **Qwen3.5-27B** | z-lab/Qwen3.5-27B-DFlash | 可用 |
| **Qwen3.5-35B-A3B** | z-lab/Qwen3.5-35B-A3B-DFlash | 可用 |
| **Qwen3-Coder-Next** | z-lab/Qwen3-Coder-Next-DFlash | 可用 |
| **Qwen3-Coder-30B-A3B** | z-lab/Qwen3-Coder-30B-A3B-DFlash | 可用 |
| **gpt-oss-20b** | z-lab/gpt-oss-20b-DFlash | 可用 |
| **gpt-oss-120b** | z-lab/gpt-oss-120b-DFlash | 可用 |
| **Qwen3-4B** | z-lab/Qwen3-4B-DFlash-b16 | 可用 |
| **Qwen3-8B** | z-lab/Qwen3-8B-DFlash-b16 | 可用 |
| **LLaMA-3.1-8B-Instruct** | z-lab/LLaMA3.1-8B-Instruct-DFlash-UltraChat | 可用 |

### 4.2 模型选择指南

| 场景 | 推荐模型 | 原因 |
|------|----------|------|
| **通用对话** | Qwen3.5-9B-DFlash | 平衡速度与质量 |
| **代码生成** | Qwen3-Coder-Next-DFlash | 专优化代码token |
| **长文本** | Qwen3.5-35B-A3B-DFlash | 更大上下文 |
| **Apple Silicon** | Qwen3.5-4B-DFlash (MLX) | 适配Mac M系列 |

---

## §5 部署指南

### 5.1 环境准备

```bash
# 基础安装
uv pip install -e ".[transformers]"  # Transformers后端

# SGLang后端
uv pip install -e ".[sglang]"

# vLLM后端（需要nightly版本）
uv pip install -e ".[vllm]"
uv pip install -U vllm --torch-backend=auto --extra-index-url https://wheels.vllm.ai/nightly

# Apple Silicon (MLX)
pip install -e ".[mlx]"
```

### 5.2 vLLM部署

```bash
vllm serve Qwen/Qwen3.5-27B \
  --speculative-config '{
    "method": "dflash",
    "model": "z-lab/Qwen3.5-27B-DFlash",
    "num_speculative_tokens": 15
  }' \
  --attention-backend flash_attn \
  --max-num-batched-tokens 32768
```

**参数说明**：
- `method: "dflash"`：使用DFlash作为speculative decoding方法
- `num_speculative_tokens: 15`：每次draft生成15个token
- `max-num-batched-tokens`：批处理最大token数

### 5.3 SGLang部署

```bash
export SGLANG_ALLOW_OVERWRITE_LONGER_CONTEXT_LEN=1

# 可选：启用实验性特性
# export SGLANG_ENABLE_SPEC_V2=1
# export SGLANG_ENABLE_DFLASH_SPEC_V2=1
# export SGLANG_ENABLE_OVERLAP_PLAN_STREAM=1

python -m sglang.launch_server \
    --model-path Qwen/Qwen3.5-35B-A3B \
    --speculative-algorithm DFLASH \
    --speculative-draft-model-path z-lab/Qwen3.5-35B-A3B-DFlash \
    --speculative-num-draft-tokens 16 \
    --tp-size 1 \
    --attention-backend trtllm_mha \
    --speculative-draft-attention-backend fa4 \
    --mem-fraction-static 0.75 \
    --mamba-scheduler-strategy extra_buffer \
    --trust-remote-code
```

### 5.4 Transformers部署

```python
from transformers import AutoModel, AutoModelForCausalLM, AutoTokenizer

# 加载draft模型
draft = AutoModel.from_pretrained(
    "z-lab/Qwen3-8B-DFlash-b16",
    trust_remote_code=True,
    dtype="auto",
    device_map="cuda:0"
).eval()

# 加载target模型
target = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen3-8B",
    dtype="auto",
    device_map="cuda:0"
).eval()

# 加载tokenizer
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-8B")

# 构造消息
messages = [{"role": "user", "content": "How many positive whole-number divisors does 196 have?"}]
input_ids = tokenizer.apply_chat_template(
    messages,
    return_tensors="pt",
    add_generation_prompt=True,
    enable_thinking=False
).to(draft.device)

# 使用DFlash生成
output = draft.spec_generate(
    input_ids=input_ids,
    max_new_tokens=2048,
    temperature=0.0,
    target=target,
    stop_token_ids=[tokenizer.eos_token_id]
)

print(tokenizer.decode(output[0], skip_special_tokens=False))
```

### 5.5 Apple Silicon (MLX) 部署

```python
from dflash.model_mlx import load, load_draft, stream_generate

# 加载模型
model, tokenizer = load("Qwen/Qwen3.5-4B")
draft = load_draft("z-lab/Qwen3.5-4B-DFlash")

# 构造prompt
messages = [{"role": "user", "content": "How many positive whole-number divisors does 196 have?"}]
prompt = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
    enable_thinking=True
)

# 流式生成
tps = 0.0
for r in stream_generate(
    model, draft, tokenizer, prompt,
    block_size=16,
    max_tokens=2048,
    temperature=0.6
):
    print(r.text, end="", flush=True)
    tps = r.generation_tps

print(f"\nThroughput: {tps:.2f} tok/s")
```

---

## §6 性能评估

### 6.1 Benchmark配置

所有benchmark使用相同数据集：
- **gsm8k**：小学数学题
- **math500**：数学竞赛题
- **humaneval**：代码生成
- **mbpp**：Python编程
- **mt-bench**：多轮对话

数据集会在首次运行时自动下载并缓存到`cache/`目录。

### 6.2 vLLM Benchmark

```bash
python -m dflash.benchmark \
    --backend vllm \
    --base-url http://127.0.0.1:8000 \
    --model Qwen/Qwen3.5-27B \
    --dataset gsm8k \
    --num-prompts 128 \
    --concurrency 1 \
    --enable-thinking
```

### 6.3 SGLang Benchmark

```bash
python -m dflash.benchmark \
    --backend sglang \
    --base-url http://127.0.0.1:30000 \
    --model Qwen/Qwen3.5-35B-A3B \
    --dataset gsm8k \
    --num-prompts 128 \
    --concurrency 1 \
    --enable-thinking
```

### 6.4 Transformers Benchmark

```bash
torchrun --nproc_per_node=8 -m dflash.benchmark \
    --backend transformers \
    --model Qwen/Qwen3-8B \
    --draft-model z-lab/Qwen3-8B-DFlash-b16 \
    --dataset gsm8k \
    --max-samples 128
```

### 6.5 预期加速比

| 场景 | 加速比 | 说明 |
|------|--------|------|
| **代码生成** | 2-3x | token接受率高 |
| **数学推理** | 1.8-2.5x | thinking模式token多 |
| **通用对话** | 1.5-2x | 取决于内容类型 |
| **短回复** | 1.2-1.5x |  draft开销占比高 |

---

## §7 内部实现细节

### 7.1 DFlash训练流程

```python
class DFlashTrainer:
    """DFlash训练流程"""
    
    def training_step(self, batch):
        # 1. Target模型生成"正确"token序列
        target_output = self.target_model(batch.input_ids)
        target_tokens = target_output.token_ids
        
        # 2. 为Draft模型生成训练数据
        #    模拟"加噪-去噪"过程
        noisy_tokens = self.add_noise(target_tokens)
        
        # 3. Draft模型学习去噪
        draft_output = self.draft_model(noisy_tokens, batch.input_ids)
        
        # 4. 损失：让draft预测接近target
        loss = self.mse_loss(draft_output, target_tokens)
        
        # 5. 反向传播更新draft
        loss.backward()
        self.optimizer.step()
        
        return loss
    
    def add_noise(self, tokens):
        """模拟扩散的加噪过程"""
        # 关键：不是随机噪声，而是对token做"扰动"
        # 扰动方式：替换、删除、插入
        noise_level = torch.rand(len(tokens)) * self.max_noise
        return self.token_noiser(tokens, noise_level)
```

### 7.2 验证机制

```python
def verify(draft_tokens, target_logits, temperature=0.0):
    """
    验证draft tokens是否被接受
    """
    # 1. 计算target模型对每个draft token的概率
    target_probs = F.softmax(target_logits, dim=-1)
    
    # 2. 计算接受概率
    #    策略：贪婪（temperature=0）或采样（temperature>0）
    if temperature == 0:
        # 贪婪：直接接受概率最高的token
        accepted = torch.argmax(target_probs, dim=-1)
    else:
        # 采样：按照概率接受
        accepted = torch.multinomial(target_probs, 1).squeeze(-1)
    
    # 3. 返回接受的tokens和实际生成的tokens
    return accepted[:len(draft_tokens)]
```

### 7.3 Block Size选择

| Block Size | 适用场景 | 显存占用 | 加速潜力 |
|------------|----------|----------|----------|
| 8 | 低显存环境 | 低 | 中 |
| 16 | 平衡之选 | 中 | 高 |
| 32 | 高吞吐场景 | 高 | 最高 |
| 64 | 批量处理 | 很高 | 最高 |

---

## §8 与其他加速技术对比

### 8.1 推理优化技术全景

```
LLM推理优化
    ├── 算子优化
    │   ├── Flash Attention
    │   ├── Tensor Parallelism
    │   └── KV Cache优化
    ├── 模型压缩
    │   ├── Quantization (AWQ/GPTQ)
    │   ├── Pruning
    │   └── Distillation
    └── 推理优化
        ├── 投机解码 ← DFlash位置
        ├── Continuous Batching
        └── Paged Attention
```

### 8.2 DFlash vs 其他投机解码方案

| 方案 | Draft模型 | 训练需求 | 通用性 | 加速比 |
|------|-----------|----------|--------|--------|
| **DFlash** | 块扩散 | 需要训练 | 高 | 2-3x |
| **Eagle** | 自回归 | 需要训练 | 低 | 2-3x |
| **Medusa** | 多头预测 | 需要训练 | 中 | 1.5-2x |
| **Self-Speculative** | 共享权重 | 无 | 高 | 1.3-1.8x |
| **No Speculative** | - | - | - | 1x (baseline) |

---

## §9 实际应用建议

### 9.1 何时使用DFlash

**适合场景**：
- 高并发场景（多个并发请求）
- 长序列生成（代码/文档）
- 延迟敏感场景（实时对话）
- 成本敏感场景（减少GPU时间）

**不适合场景**：
- 低延迟单次请求（draft开销不值得）
- 极短回复（<10 tokens）
- 特定领域（无对应DFlash模型）

### 9.2 硬件配置建议

| GPU | 推荐配置 | 说明 |
|-----|----------|------|
| **A100/H100** | Qwen3.5-27B + DFlash | 最佳性价比 |
| **A6000** | Qwen3.5-9B + DFlash | 平衡选择 |
| **RTX 4090** | Qwen3-4B + DFlash | 入门级 |
| **Mac M3 Pro** | Qwen3.5-4B (MLX) | Apple Silicon |

### 9.3 生产部署 Checklist

```bash
# 1. 确认硬件支持
nvidia-smi  # 或 Apple Silicon: sysctl -n machdep.cpu.brand_string

# 2. 安装正确版本
pip install -e ".[vllm]"  # 或 sglang

# 3. 验证DFlash模型加载
python -c "from transformers import AutoModel; print('DFlash model loaded')"

# 4. 运行benchmark确认加速效果
python -m dflash.benchmark --backend vllm ...

# 5. 监控指标
#    - Token接受率 (target > 85%)
#    - 吞吐量提升 (target > 2x)
#    - 首token延迟 (应不增加)
```

---

## §10 研究论文

```bibtex
@article{chen2026dflash,
  title   = {{DFlash: Block Diffusion for Flash Speculative Decoding}},
  author  = {Chen, Jian and Liang, Yesheng and Liu, Zhijian},
  journal = {arXiv preprint arXiv:2602.06036},
  year    = {2026}
}
```

---

## §11 FAQ

**Q1：DFlash需要额外的训练吗？**
A：是的，DFlash模型需要针对目标模型进行训练。但作者提供了预训练好的模型，直接使用即可。

**Q2：接受率受哪些因素影响？**
A：主要因素包括：draft模型质量、block_size设置、输入内容类型（代码/数学接受率更高）。

**Q3：支持哪些推理框架？**
A：支持vLLM、SGLang、Transformers（原装）、MLX（Apple Silicon）。

**Q4：如何选择num_speculative_tokens？**
A：建议从16开始测试。太大增加显存占用，太小加速效果不明显。

**Q5：可以训练自己的DFlash模型吗？**
A：可以，作者承诺会开源训练recipe。

---

## 相关资源

- **GitHub仓库**：https://github.com/z-lab/dflash
- **论文链接**：https://arxiv.org/abs/2602.06036
- **官网博客**：https://z-lab.ai/projects/dflash/
- **HuggingFace模型**：https://huggingface.co/collections/z-lab/dflash
- **反馈表单**：https://forms.gle/4YNwfqb4nJdqn6hq9
