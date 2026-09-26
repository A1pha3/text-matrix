---
title: "Soup：一条 YAML 微调大模型，4 GB 显存跑 8B 的工程账本"
date: 2026-09-27T03:23:02+08:00
draft: false
description: "MakazhanAlpamys/Soup 用一个 YAML 配置加一条命令封装 LLM 微调全流程，其 layer streaming 技术让 8B 模型在 4 GB 笔记本 GPU 上训练。本文拆解其配置体系、基准数据的诚实标注与 v0.75 的工程取舍。"
categories: ["技术笔记"]
tags: ["Soup", "LLM 微调", "LoRA", "开源训练工具", "Python"]
github_repo: "MakazhanAlpamys/Soup"
source_key: "gh:MakazhanAlpamys/Soup"
slug : soup-yaml-llm-finetuning-4gb
---

## 它解决什么问题

LLM 微调的基础设施摩擦是真实存在的：即便是有经验的团队，README 引用的估计是 30-50% 的时间耗在跟 GPU 机器、环境、超参搏斗上，而不是改进模型。Soup（MakazhanAlpamys/Soup，7,277 stars / 1,159 forks，Python，Apache-2.0）的答案是把整条链路压进一个 YAML 和一条命令：

```bash
pip install "soup-cli[train]"
soup init --template chat
soup train
```

`pipx`/`uv tool` 是推荐装法（应用自带隔离环境），`[train]` extra 才带训练栈（torch、transformers、peft、trl 等），裸 `soup-cli` 是轻核心。Python 仅支持 3.10-3.12——3.13+ 会解析到未测试的 PyTorch wheel 并在原生扩展处崩溃，README 对此有明确说明。

一条完整的 `soup.yaml` 长这样：

```yaml
base: meta-llama/Llama-3.1-8B-Instruct
task: sft
data:
  train: ./data/train.jsonl
  format: alpaca
  val_split: 0.1
training:
  epochs: 3
  lr: 2e-5
  batch_size: auto        # 自动探测
  lora: { r: 64, alpha: 16 }
  quantization: 4bit
output: ./output
```

配置的唯一真相源是仓库里的 `config/schema.py`——每个字段在代码里有定义，文档不另行漂移。

## 4 GB 显存训练 8B：layer streaming 怎么做到

Soup 最抓眼球的宣称是「在 RTX 3050 Laptop 4 GB 上微调 Llama-3.1-8B-Instruct」。机制叫 **layer streaming**：把冻结的基座模型整体挡在 VRAM 之外，pin 在内存里，前向时**逐个 decoder layer 喂给 GPU**，VRAM 里只保留两个约 113 MB 的层缓冲区。

实测口径（仓库提供，v0.72.2 版本测得）：8B + NF4 量化 + LoRA，batch 1、seq 512，吞吐 119.6 tok/s、峰值显存 3.32 GB；H100 上独立复现为 113.00 tok/s、同样 3.32 GB 峰值，且流式结果与常驻显存运行 **bit-exact**（逐位一致）。仓库还提供了 Colab T4 notebook（`notebooks/proof-4gb.ipynb`），把进程显存封顶到 4 GB 后断言流式模型与常规模型逐位相同——宣称是可以自己验证的，不是宣传页。

值得专门指出的诚实标注：这两组数字测于 v0.72.2，**其后的 v0.73.0 正确性修复在 32B 档位带来了 -4.8% 的代价，且尚未在 4 GB 卡上重新测量**（追踪于 issue #361）。README 原文直接写明 "re-measurement pending"——一个把基准数据的新鲜度主动挂出来的项目，在开源训练工具里并不多见。另注意该功能默认关闭（`stream_layers: true` 显式开启）且仍标注 BETA。

## v0.75 的工程取舍：宁可拒绝，不可静默

读 Soup 的 Release Notes 像在读一份事故复盘集，v0.75.0 的核心主题是消灭「静默失效」：

- **未知配置键直接拒绝加载**（breaking）：v0.75 之前，`quantizaton` 这类拼写错误的键会通过校验后被丢弃，训练照跑但设置没生效——这是最危险的一类失败。现在 CLI 直接 exit 1、API 抛 `ValueError`，并提示你可能想拼的字段。
- **MLX 后端补齐承诺**：同一份 `soup.yaml` 在 transformers 后端和 MLX 后端曾训练出**不同的配方**——六个训练选项（`train_on_responses_only`、调度器、梯度累积等）被校验、被接受、然后什么都没读。v0.75 逐一接上；32 个优化器名中 MLX 只有 8 个有等价物，其余 24 个按名拒绝而非静默回退成 AdamW。
- **验证损失从「算了就扔」变成被记录、被流式、被展示**。

这个版本的另一个注脚：60 个 PR 全部来自维护者之外的 22 个人。

## 工具链完整性

训练之外，Soup 覆盖了「训-测-运」全链路：

```bash
soup chat  --model ./output                    # 直接对话验证
soup merge --adapter ./output                  # LoRA 合并回基座
soup export --model ./output --format gguf --quant q4_k_m   # 导出给 Ollama/llama.cpp
soup push  --model ./output --repo you/my-model
```

导出目标还包括 ONNX、TensorRT、AWQ、GPTQ、BitNet。训练模板覆盖 chat / code / tool-calling / reasoning / vision / KTO / ORPO / SimPO / RLHF / pretrain / MoE / longcontext / embedding / audio 等 18 种。偏好浏览器工作流的话，`soup ui` 起一个本地面板（训练设置、实时指标、数据集探索、模型对话）。最新版本 v0.75.1（2026-09-21）持续在硬化云运行与产物保留，截至 2026-09-26 仍有活跃提交。

## 适用边界

- **个人/小团队想在本地 GPU 上做 QLoRA 微调、不想碰 infra** → 这是 Soup 的靶心场景，值得作为默认起点；
- **需要多层实验管理、分布式多机训练的研究团队** → Soup 的抽象层会开始碍事，你大概率要回到裸 transformers/DeepSpeed；
- **想吃 4 GB 训 8B 的宣称** → 记住那是 BETA、默认关闭、基准待复测（issue #361），自己用官方 Colab notebook 验证一遍再下结论；
- **`grpo_variant: gspo` 用户注意**：v0.75 起换成论文 arXiv:2507.18071 的序列级目标函数，旧 gspo 配置不可复现历史结果。

项目地址：https://github.com/MakazhanAlpamys/Soup（v0.75.1，Apache-2.0，DOI: 10.5281/zenodo.21771064）
