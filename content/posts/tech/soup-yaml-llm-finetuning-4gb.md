---
title: "Soup：一条 YAML 微调大模型，4 GB 显存跑 8B 的工程账本"
date: 2026-09-27T03:23:02+08:00
draft: false
description: "MakazhanAlpamys/Soup 用一个 YAML 配置加一条命令封装 LLM 微调全流程，其 layer streaming 技术让 8B 模型在 4 GB 笔记本 GPU 上训练。本文拆解其配置体系、基准数字的来龙去脉、论文 v3 撤回的机理解释与 v0.75 的工程取舍。"
categories: ["技术笔记"]
tags: ["Soup", "LLM 微调", "LoRA", "开源训练工具", "Python"]
github_repo: "MakazhanAlpamys/Soup"
source_key: "gh:MakazhanAlpamys/Soup"
slug: soup-yaml-llm-finetuning-4gb
---

## 它解决什么问题

训练 LLM 时，基础设施的摩擦有多大？README 引用的估计是：有经验的团队也有 30-50% 的时间耗在 GPU 环境、依赖和调度上，而不是改进模型本身。Soup（MakazhanAlpamys/Soup，截至 2026-09-30 为 7,690 stars / 1,230 forks，Python，Apache-2.0）的答案是把整条链路压进一个 YAML 和一条命令：

```bash
pip install "soup-cli[train]"
soup init --template chat
soup train
```

`pipx`/`uv tool` 是推荐装法（应用自带隔离环境），`[train]` extra 才带训练栈（torch、transformers、peft、trl 等），裸 `soup-cli` 是轻核心，`soup init` 和数据检查命令装完即可用。Python 仅支持 3.10-3.12——3.13+ 会解析到未测试的 PyTorch wheel 并在原生扩展处崩溃，README 对此有明确说明。训练栈还有一条硬要求：torch ≥ 2.6.0（v0.75.0 起），2.5.1 无法导入 trl 0.29，所有偏好训练器直接失效。

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

这份示例与仓库自带的 `chat` 模板几乎逐字对应，不是示意。配置的唯一真相源是 `src/soup_cli/config/schema.py`——每个字段在代码里有定义，文档不另行漂移。

## 4 GB 显存训练 8B：layer streaming 怎么做到

Soup 最抓眼球的宣称是「在 RTX 3050 Laptop 4 GB 上微调 Llama-3.1-8B-Instruct」。机制叫 **layer streaming**：把冻结的基座模型整体挡在 VRAM 之外，pin 进页锁定的主机内存，逐个 decoder layer 喂给 GPU。VRAM 里常驻的只有 LoRA 适配器、它的梯度和优化器状态——它们很小；基座由一条专用 CUDA 流预取，上一层还在计算时，下一层已经搬进两个预分配的缓冲区（8B 下每个约 113 MB），加载与计算重叠。峰值显存由最大的那一层决定——原本装不下的模型因此能训起来。

代价写在物理里：每层每个 step 要被读两次，前向一次，反向重算一次——`dL/dx = Wᵀ · dL/dy` 需要下层权重就位。官方文档的原话是 "this is physics, not an implementation detail"：流式买显存的方式就是付出时间。

实测口径（仓库提供，v0.72.2 测得，#331 修复之前）：8B + NF4 量化 + LoRA，batch 1、seq 512，吞吐 119.6 tok/s、峰值显存 3.32 GB；H100 上的独立复现（中位数）为 113.00 tok/s、同样 3.32 GB，流式的前向与常驻运行 bit-exact（逐位一致）。仓库提供 Colab T4 notebook（`notebooks/proof-4gb.ipynb`），把进程显存封顶到 4 GB 后断言流式模型与常规模型逐位相同——宣称可以自己验证，不是宣传页。

读这组数字先分清三件事：它测的是训练吞吐和峰值显存，不是推理速度，更不是模型质量；它回答的是「8B 能不能在 4 GB 卡上训起来、代价多大」，每层读两次的物理已经否掉了「流式更快」的期待；它也不能跨卡外推，3050 与 H100 两个数字说明的是同一机制在不同硬件上都成立。

数字的新鲜度同样值得说：v0.73.0 的正确性修复（#331，下一节详述）在 32B 档位带来 -4.8% 的代价（72B 为 -3.7%），4 GB 卡的复测一度挂在 issue #361，README 至今印着 "re-measurement pending"。但 issue 已于 2026-09-27 关闭：同一张 3050、同一套协议在修复后的代码上实测 208.6 tok/s、峰值 2.40 GB（分配口径，保留 2.66 GB）。维护者逐项复核后的结论更值得转述：74% 的提升主要来自 SM 时钟从 952 MHz 翻到 1935 MHz——单时钟吞吐降到原来的 85.8%，与两次运行各自 GEMM 上限占比之比（59/68 = 86.8%）在 1% 内吻合，即相对各自硬件上限，两次运行效率一致，提升全部来自时钟；pin 在内存的基座仓库从 3.60 GB 涨到 5.70 GB，恰好等于 embed_tokens 与未绑定 lm_head 两个 0.525B bf16 张量（2.10 GB）被移进 pin 存储区——仓库变大而峰值变小，这组反直觉数字互洽到 GB 级。读这个项目的数字要跟到 issue：文档可以滞后，测量记录不滞后。另注意该功能默认关闭（`stream_layers: true` 显式开启）且仍标注 BETA；配置面还有 `stream_source`（`ram`/`disk`，磁盘层 v0.72.3 起支持）与 `stream_buffers`（2-8 路，默认 2 路双缓冲）可调。

## 一次 4 GB 训练步的流转

把机制串成一次真实训练：`soup train` 启动先做 VRAM pre-flight，判断这张卡放不放得下；通过后基座 pin 进内存，训练进入稳态——当前层在 GPU 上计算时，下一条 decoder layer 正在专用 CUDA 流上搬进第二个缓冲区；LoRA 侧照常前向、反传、更新；反向需要下层权重时，该层被第二次读入。NF4 层的反量化发生在 checkpoint 区内，这正是 #331 修复后的行为。

修复之前，超过约 165 MiB/层的 NF4 模型（32B 及以上）踩一个静默错误：bitsandbytes 的融合算子把打包权重和 quant_state 挂在普通属性上，梯度检查点无法丢弃重算，引用又别名到已被复用的流式缓冲槽——结果是前向逐位正确、loss 曲线健康、除最后几个缓冲层外所有层的梯度都是错的。8B 和 14B 从未受影响。修复的代价用「修复禁用」的对照组量出：32B 吞吐 -4.8%、峰值显存 +2.9%，梯度 256/256 全对，对照组只有 8-12/256。

训练结束，`save_model` 把 adapter 存成 safetensors——这一步在 peft 0.21 上曾整段静默失败，见下节。

## 一条被撤回的机理解释

Soup 不只放了基准，还发了预印本：*Exact Layer Streaming: LoRA Fine-Tuning of an 8B Model on a 4 GB Laptop GPU*（Zenodo，概念 DOI 10.5281/zenodo.21771064，当前版本 v3，2026-08-13）。v3 做的最重要的事是撤回一条解释：v0.73.0 曾写下「layer streaming 的瓶颈在主机到设备传输，不在 GPU」，那是从 H100 复现推出的推断，从未实测；8 月 11 日补测，结论为假——公布的配置下，删光所有主机到设备的传输字节只换来 1.4%，计算流等待拷贝占一个 step 的 0.20%，整个 step 跑在同卡同会话 GEMM 上限的 71.3%，最大的流式专属开销是每层 NF4 反量化，占 9.8%。论文还补上了此前的空白：0.5B 到 72B 的前向逐位一致、8B/14B 的反向验证，以及流式与常驻训出的模型质量无差别——「训出来的模型能不能用」第一次被测。撤回以发布新版本的方式进行，v1/v2 保留各自可引用的版本 DOI，为的是留下「何时声称了什么」的完整记录；配套测量记录按原样发布，包括 H100 验证中被否掉的六个假设和对照组逮住的三个假阳性。

## v0.75 的工程取舍：宁可拒绝，不可静默

读 Soup 的 Release Notes 像在读一份事故复盘集，v0.75.0 的核心主题是消灭「静默失效」：

- **未知配置键直接拒绝加载**（breaking）：v0.74 只对 `quantizaton` 这类拼写错误的键给警告，更早的版本直接丢弃——校验通过、训练照跑、设置没生效，这是最危险的一类失败。v0.75 起 CLI 直接 exit 1、API 抛 `ValueError`，并提示你可能想拼的字段。
- **MLX 后端补齐承诺**：同一份 `soup.yaml` 在 transformers 后端和 MLX 后端曾训练出**不同的配方**——六个训练选项（`train_on_responses_only`、调度器、梯度累积等）被校验、被接受、然后什么都没读。v0.75 逐一接上；32 个优化器名中 MLX 只有 8 个有等价物，其余 24 个按名拒绝而非静默回退成 AdamW。现在 `soup doctor --config` 会列出当前后端不读的配置项。
- **验证损失从「算了就扔」变成被记录、被流式、被展示**。

这个版本的另一个注脚：60 个 PR 全部来自维护者之外的 22 个人。

紧接着的 v0.75.1（2026-09-21）把「静默失效」的清理延伸到保存侧。peft 0.21 改了 adapter 张量的筛选方式，而 layer streaming 包装层的模块名带着 `.inner.` 前缀，于是 `stream_layers: true` 下保存的 adapter 全是零张量：`adapter_model.safetensors` 只有 40 字节，不报错、不留痕，`trainer.save_model`、`save_steps` 定时 checkpoint、`get_peft_model_state_dict` 导出路径全部中招，且无法恢复、只能重训。官方结论写得毫不留情：此修复之前、peft ≥ 0.21 下用流式保存的任何 adapter 都作废。同一版还修了 `soup runs clean --keep-weights` 在 Click 8.1 下的开关翻转——带上这个旗标反而删掉非最优 checkpoint。另有一个版本纪律的细节：v0.75.1 不是从 main 切的，而是 v0.75.0 加 25 个 cherry-pick 的回移版，main 上还压着下一整个 minor 的未发布改动。

## 工具链完整性

训练之外，Soup 覆盖了「训-测-运」全链路：

```bash
soup chat  --model ./output                    # 直接对话验证
soup merge --adapter ./output                  # LoRA 合并回基座
soup export --model ./output --format gguf --quant q4_k_m   # 导出给 Ollama/llama.cpp
soup push  --model ./output --repo you/my-model
```

导出目标还包括 ONNX、TensorRT、AWQ、GPTQ、BitNet。训练模板共 21 种（以 `src/soup_cli/templates/manifest.json` 为准），除 chat / code / tool-calling / reasoning / vision / KTO / ORPO / SimPO / RLHF / pretrain / MoE / longcontext / embedding / audio，还有一组受监管行业的合规模板——HIPAA、SOC 2、EU AI Act、SR 11-7，另配医疗模板。现成配方方面，`soup recipes list` 里有一百多个拿来即用的配方（Mixtral、DeepSeek R1/V3、Phi-4 等）；环境跑不通时，`soup doctor` 一次给出 GPU、系统资源、依赖和版本。偏好浏览器工作流的话，`soup ui` 起一个本地面板（训练设置、实时指标、数据集探索、模型对话）。最新发布版 v0.75.1（2026-09-21），仓库截至 2026-09-29 仍有成批提交，main 的基准目录里已出现 v0.76.0 的记录（CUDA graph 解码、工具调用判别）——发布版尚未跟进，以 Release 页为准。

## 适用边界

- **个人/小团队想在本地 GPU 上做 QLoRA 微调、不想碰 infra** → 这是 Soup 的靶心场景，值得作为默认起点；
- **需要多层实验管理、分布式多机训练的研究团队** → Soup 的抽象层会开始碍事，你大概率要回到裸 transformers/DeepSpeed；
- **想吃 4 GB 训 8B 的宣称** → 照 issue #361 的实测行读：修复后代码在同一张 3050 上给出 208.6 tok/s、2.40 GB 峰值，但提升主要来自时钟，BETA 标记未摘；自己用官方 Colab notebook 跑一遍再下结论；
- **用 `stream_layers: true` 且 peft ≥ 0.21 的老存档** → 先查 `adapter_model.safetensors` 是否只有 40 字节：是，则存档全零，直接重训；
- **`grpo_variant: gspo` 用户注意** → gspo 是 GRPO 的序列级变体，v0.75 起换成论文 arXiv:2507.18071 的公开目标函数，替换原先一个列居中启发式（padding token 会波及共享其列的所有行的梯度）；旧 gspo 配置不可复现历史结果。

采用顺序：第一站在 Colab T4 上跑 `proof-4gb.ipynb`，亲手验证逐位一致；日常微调先走默认常驻路径，把 `stream_layers` 留给显存真的不够的场景，开启时记下 Soup 版本号；训完立刻 `soup chat` 抽查，确认没踩 peft 保存坑，再 merge、export；吃不准后端读了哪些配置，`soup doctor --config` 一步到位。

项目地址：https://github.com/MakazhanAlpamys/Soup（发布版 v0.75.1，Apache-2.0，数据核对日 2026-09-30）
