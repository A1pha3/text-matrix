---
title: "DFlash：块扩散模型加速 LLM 推理"
date: "2026-04-17T16:35:00+08:00"
slug: "dflash-block-diffusion-speculative-decoding"
description: "1,710 Stars 的 DFlash 是一个轻量级块扩散模型，用于投机解码加速 LLM 推理。支持 Qwen3/LLaMA/GPT-OSS 等多种模型，可在 vLLM/SGLang/Transformers 上部署，实测加速 2-3 倍。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "推理加速", "扩散模型", "Python", "vLLM", "SGLang"]
---

## 背景与动机：LLM 推理的瓶颈

### 自回归解码的痛点

LLM 推理采用自回归方式生成 token——每个 token 依赖前一个 token 的隐状态，无法并行。这意味着生成 N 个 token 需要 N 次连续的前向计算，每次都要走完完整的计算图。即使模型不大，这个串行依赖也限制了吞吐。

### 投机解码的原理

投机解码的思路是用一个小模型（draft model）快速生成候选 token 序列，再用大模型（target model）批量验证，接受匹配的 token。如果 draft 模型的接受率够高，一次前向可以确认多个 token，等效加速比等于平均接受数。

```
传统方式：
Token_1 → Token_2 → Token_3 → Token_4 → Token_5  (大模型，5 次前向)

投机解码：
Draft 模型并行生成：d1 d2 d3 d4 d5  (小模型，5 次前向但快)
       ↓
Target 模型验证：  T  T  T  T  T   (大模型，1 次批量验证)
       ↓
接受 tokens：     ✓  ✓  ✗  ✓  ✓   (4/5 被接受 → 等效 4x 加速)
```

### 现有方案的局限

| 方案 | 缺陷 |
|------|------|
| Eagle | 自回归 draft，需额外训练，泛化性差 |
| Medusa | 多头预测固定位置，灵活度低 |
| Self-Speculative | 需要模型结构修改 |
| 脉冲网络 | 训练不稳定 |

这些方案的共同问题是 draft 生成方式本质上是自回归的变体，仍然受限于串行依赖。

### DFlash 的做法

DFlash 用块扩散模型（Block Diffusion）做 draft，一次前向并行生成多个 token，而不是逐个预测。块扩散的核心是去噪过程：从噪声开始，通过多步去噪恢复出 token 序列，这个去噪过程天然支持并行。

```
传统 Draft：自回归
          d1 → d2 → d3 → d4 → d5

DFlash Draft：块扩散
         ┌─────────────────────┐
         │   Block Diffusion   │
         │   并行去噪生成      │
         │   [d1, d2, ..., d5] │
         └─────────────────────┘
```

优势：并行度高、无需修改模型结构、支持任意 LLM、训练稳定。

## 架构详解

### 整体流程

```
Input: "196 有多少个正约数？"
         ┌──────────────────────────────┐
         │    Block Diffusion Draft      │
         │   Noise → Denoise → Tokens   │
         │   (并行去噪，生成多个 token)   │
         └──────────────┬───────────────┘
                        │ Draft Tokens [d1, d2, ..., dk]
                        ▼
         ┌──────────────────────────────┐
         │   Target Model (Verification) │
         │   Batch Verification          │
         │   [p(T1|d1), p(T2|d2), ...]   │
         └──────────────┬───────────────┘
                        │ Verified Tokens
                        ▼
         Output: "does 196 have?" (加速 2-3 倍)
```

### 块扩散原理

扩散模型通常用于图像生成——从噪声逐步去噪恢复到图像。DFlash 将这一思路迁移到文本生成：把 token 序列视为需要"恢复"的目标，draft 模型学会从噪声版 token 序列中还原出合理的下一个 block。

```python
class BlockDiffusionDraft:
    """块扩散 draft 模型"""

    def __init__(self, draft_model, block_size=16):
        self.draft = draft_model
        self.block_size = block_size

    def draft_tokens(self, context: Tensor) -> list[str]:
        # 1. 对目标位置加噪
        noise_level = sample_noise_levels(self.block_size)
        noisy_tokens = add_noise(context, noise_level)

        # 2. 块级别去噪——一次前向，不是自回归
        denoised = self.draft(noisy_tokens, context)

        # 3. 采样得到 token 序列
        draft_tokens = sample_tokens(denoised, temperature=0.0)
        return draft_tokens
```

### 与 Eagle/Medusa 的区别

| 特性 | Eagle | Medusa | DFlash |
|------|-------|--------|--------|
| 生成方式 | 自回归 | 固定位置 | 块并行 |
| 灵活性 | 高 | 低 | 高 |
| 训练复杂度 | 高 | 低 | 中 |
| 接受率 | ~80% | ~70% | ~85% |
| 支持模型 | 特定 | 特定 | 通用 |

## 支持的模型

| 目标模型 | DFlash Draft 模型 | 状态 |
|----------|------------------|------|
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

模型选择建议：通用对话用 Qwen3.5-9B-DFlash，代码生成用 Qwen3-Coder-Next-DFlash，长文本用 Qwen3.5-35B-A3B-DFlash，Apple Silicon 用 Qwen3.5-4B-DFlash（MLX 版）。

## 部署指南

### 环境准备

```bash
# Transformers 后端
uv pip install -e ".[transformers]"

# SGLang 后端
uv pip install -e ".[sglang]"

# vLLM 后端（需要 nightly 版本）
uv pip install -e ".[vllm]"
uv pip install -U vllm --torch-backend=auto --extra-index-url https://wheels.vllm.ai/nightly

# Apple Silicon (MLX)
pip install -e ".[mlx]"
```

### vLLM 部署

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

核心参数：`method: "dflash"` 指定使用 DFlash 做投机解码，`num_speculative_tokens: 15` 控制每次 draft 生成的 token 数。

### SGLang 部署

```bash
export SGLANG_ALLOW_OVERWRITE_LONGER_CONTEXT_LEN=1

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

### Transformers 部署

```python
from transformers import AutoModel, AutoModelForCausalLM, AutoTokenizer

draft = AutoModel.from_pretrained(
    "z-lab/Qwen3-8B-DFlash-b16",
    trust_remote_code=True,
    dtype="auto",
    device_map="cuda:0"
).eval()

target = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen3-8B",
    dtype="auto",
    device_map="cuda:0"
).eval()

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-8B")

messages = [{"role": "user", "content": "196 有多少个正约数？"}]
input_ids = tokenizer.apply_chat_template(
    messages, return_tensors="pt", add_generation_prompt=True,
    enable_thinking=False
).to(draft.device)

output = draft.spec_generate(
    input_ids=input_ids, max_new_tokens=2048, temperature=0.0,
    target=target, stop_token_ids=[tokenizer.eos_token_id]
)
print(tokenizer.decode(output[0], skip_special_tokens=False))
```

### Apple Silicon (MLX) 部署

```python
from dflash.model_mlx import load, load_draft, stream_generate

model, tokenizer = load("Qwen/Qwen3.5-4B")
draft = load_draft("z-lab/Qwen3.5-4B-DFlash")

messages = [{"role": "user", "content": "196 有多少个正约数？"}]
prompt = tokenizer.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True,
    enable_thinking=True
)

tps = 0.0
for r in stream_generate(
    model, draft, tokenizer, prompt,
    block_size=16, max_tokens=2048, temperature=0.6
):
    print(r.text, end="", flush=True)
    tps = r.generation_tps

print(f"\nThroughput: {tps:.2f} tok/s")
```

## 性能评估

### Benchmark 配置

所有 benchmark 使用相同数据集：gsm8k（小学数学题）、math500（数学竞赛题）、humaneval（代码生成）、mbpp（Python 编程）、mt-bench（多轮对话）。数据集首次运行时自动下载缓存到 `cache/` 目录。

```bash
# vLLM 后端 benchmark
python -m dflash.benchmark \
    --backend vllm --base-url http://127.0.0.1:8000 \
    --model Qwen/Qwen3.5-27B --dataset gsm8k \
    --num-prompts 128 --concurrency 1 --enable-thinking

# SGLang 后端 benchmark
python -m dflash.benchmark \
    --backend sglang --base-url http://127.0.0.1:30000 \
    --model Qwen/Qwen3.5-35B-A3B --dataset gsm8k \
    --num-prompts 128 --concurrency 1 --enable-thinking

# Transformers 后端 benchmark
torchrun --nproc_per_node=8 -m dflash.benchmark \
    --backend transformers --model Qwen/Qwen3-8B \
    --draft-model z-lab/Qwen3-8B-DFlash-b16 \
    --dataset gsm8k --max-samples 128
```

### 预期加速比

| 场景 | 加速比 | 说明 |
|------|--------|------|
| 代码生成 | 2-3x | token 接受率高 |
| 数学推理 | 1.8-2.5x | thinking 模式 token 多 |
| 通用对话 | 1.5-2x | 取决于内容类型 |
| 短回复 | 1.2-1.5x | draft 开销占比高 |

加速比受 draft 模型质量、block_size 设置、输入内容类型影响。代码和数学推理的 token 模式更规则，接受率更高。

## 内部实现细节

### 训练流程

DFlash 的训练不依赖目标模型的结构信息，只依赖其输出分布：

1. 目标模型在给定输入上生成"正确"的 token 序列
2. 对正确序列做加噪扰动（替换、删除、插入 token）
3. Draft 模型学习去噪——从噪声版本恢复原始序列
4. 损失函数是 draft 输出与目标 token 序列之间的 MSE

这种训练方式使得 draft 模型不依赖目标模型的架构细节，更换目标模型时只需重新生成训练数据，不需要修改训练代码。

### 验证机制

验证阶段，目标模型对 draft 生成的 token 序列做一次前向，得到每个位置上各 token 的概率。如果 draft 预测的 token 在目标模型概率分布中排在前列，就接受它；否则拒绝并从该位置开始重新生成。

```python
def verify(draft_tokens, target_logits, temperature=0.0):
    target_probs = F.softmax(target_logits, dim=-1)
    if temperature == 0:
        # 贪婪解码：接受概率最高的 token
        accepted = torch.argmax(target_probs, dim=-1)
    else:
        # 采样：按概率分布随机采样
        accepted = torch.multinomial(target_probs, 1).squeeze(-1)
    return accepted[:len(draft_tokens)]
```

### Block Size 选择

| Block Size | 适用场景 | 显存占用 | 加速潜力 |
|------------|----------|----------|----------|
| 8 | 低显存环境 | 低 | 中 |
| 16 | 平衡之选 | 中 | 高 |
| 32 | 高吞吐场景 | 高 | 最高 |
| 64 | 批量处理 | 很高 | 最高 |

Block size 越大，单次 draft 生成的 token 越多，但接受率会下降——块内任意一个 token 被拒绝都会导致后续 token 浪费。实践中建议从 16 开始测试。

## 与其他加速技术对比

### 推理优化技术全景

```
LLM 推理优化
    ├── 算子优化
    │   ├── Flash Attention
    │   ├── Tensor Parallelism
    │   └── KV Cache 优化
    ├── 模型压缩
    │   ├── Quantization (AWQ/GPTQ)
    │   ├── Pruning
    │   └── Distillation
    └── 推理策略
        ├── 投机解码 ← DFlash 位置
        ├── Continuous Batching
        └── Paged Attention
```

### DFlash vs 其他投机解码方案

| 方案 | Draft 模型 | 训练需求 | 通用性 | 加速比 |
|------|-----------|----------|--------|--------|
| **DFlash** | 块扩散 | 需要训练 | 高 | 2-3x |
| Eagle | 自回归 | 需要训练 | 低 | 2-3x |
| Medusa | 多头预测 | 需要训练 | 中 | 1.5-2x |
| Self-Speculative | 共享权重 | 无 | 高 | 1.3-1.8x |
| 无投机解码 | - | - | - | 1x (baseline) |

## 实际应用建议

### 何时使用 DFlash

适合场景：高并发推理、长序列生成（代码/文档）、延迟敏感或成本敏感场景。不适合：短回复（<10 tokens）、draft 模型未覆盖的特定领域。

### 硬件配置建议

| GPU | 推荐配置 |
|-----|----------|
| A100/H100 | Qwen3.5-27B + DFlash |
| A6000 | Qwen3.5-9B + DFlash |
| RTX 4090 | Qwen3-4B + DFlash |
| Mac M3 Pro | Qwen3.5-4B (MLX) |

### 生产部署 Checklist

1. 确认硬件支持：`nvidia-smi`
2. 安装正确版本：`pip install -e ".[vllm]"` 或 `[sglang]`
3. 验证 DFlash 模型加载：`python -c "from transformers import AutoModel; print('OK')"`
4. 运行 benchmark 确认加速效果
5. 监控 Token 接受率（目标 > 85%）、吞吐量提升（目标 > 2x）、首 token 延迟（不应增加）

## 常见问题

**DFlash 需要额外训练吗？**
是的，但作者提供了预训练好的模型，直接使用即可。

**接受率受哪些因素影响？**
draft 模型质量、block_size 设置、输入内容类型（代码/数学接受率更高）。

**支持哪些推理框架？**
vLLM、SGLang、Transformers、MLX（Apple Silicon）。

**如何选择 num_speculative_tokens？**
建议从 16 开始测试。太大增加显存占用，太小加速效果不明显。

**可以训练自己的 DFlash 模型吗？**
可以，作者承诺会开源训练 recipe。

## 引用

```bibtex
@article{chen2026dflash,
  title   = {{DFlash: Block Diffusion for Flash Speculative Decoding}},
  author  = {Chen, Jian and Liang, Yesheng and Liu, Zhijian},
  journal = {arXiv preprint arXiv:2602.06036},
  year    = {2026}
}
```

## 相关资源

- GitHub 仓库：https://github.com/z-lab/dflash
- 论文：https://arxiv.org/abs/2602.06036
- 官网：https://z-lab.ai/projects/dflash/
- HuggingFace 模型：https://huggingface.co/collections/z-lab/dflash