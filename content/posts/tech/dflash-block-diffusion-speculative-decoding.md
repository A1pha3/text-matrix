---
title: "DFlash：把扩散模型关进草稿阶段，投机解码才拿到五倍加速"
date: "2026-04-17T16:35:00+08:00"
slug: "dflash-block-diffusion-speculative-decoding"
github_repo: "z-lab/dflash"
source_key: "gh:z-lab/dflash"
description: "DFlash 用一次前向并行吐出一整块草稿 token，把投机解码的草稿阶段从自回归换成块扩散，质量仍由目标模型验证兜底。本文按 commit 07ebd93 的源码和 arXiv:2602.06036v2 逐条核对它的 KV 注入、一步去噪、无损验证规则与真实加速数字，并写清 2026-08 打包改版后 CLI、依赖与支持范围的变化，以及 DFlash 2 多出来的那一个 token 从哪来。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "推理加速", "扩散模型", "投机解码", "vLLM", "SGLang"]
lastmod: "2026-09-20T00:00:00+08:00"
---

DFlash 容易被介绍成"用扩散模型来写文本，所以能并行"。源码读下来，这个说法把因果讲反了。它之所以敢把去噪步骤压到只剩一步，不是因为扩散模型本身够好，而是因为它把扩散模型放在了草稿位置上：写错的词元（token）会在验证阶段被整段丢掉，草稿的质量下限不再需要谁来守。

一旦扩散只负责起草，两件事同时成立：草稿可以做得很浅很快，输出却仍然精确等于目标模型的分布。论文的实测加速因此不是 1.x 级别。在 Transformers 后端、关闭思考模式的设定下平均 4.9×，最高点 6.1×，而同样草稿预算下的 EAGLE-3 停在 2× 上下。

这篇文章按三个问题展开：自回归草稿的天花板卡在哪里、DFlash 用什么换掉了它、以及这些数字在什么条件下才会成立。第三问最需要小心，因为同一份代码在并发 1 和并发 32 下给出的结论完全不同。

## 目录

- [1. 判断：它省掉的不是推理，是草稿的串行步骤](#1-判断它省掉的不是推理是草稿的串行步骤)
- [2. 仓库现状与核实口径](#2-仓库现状与核实口径)
- [3. 系统地图：三段职责，一条数据回路](#3-系统地图三段职责一条数据回路)
- [4. 自回归草稿的天花板写在一个公式里](#4-自回归草稿的天花板写在一个公式里)
- [5. 目标特征注入 KV，而不是拼进输入](#5-目标特征注入-kv而不是拼进输入)
- [6. 一步去噪：块内除锚点外全是 mask](#6-一步去噪块内除锚点外全是-mask)
- [7. 训练的四处非标准做法](#7-训练的四处非标准做法)
- [8. 无损性来自验证规则，而不是草稿猜得准](#8-无损性来自验证规则而不是草稿猜得准)
- [9. 一次提问如何流过整个系统](#9-一次提问如何流过整个系统)
- [10. 部署入口已经收敛成一条命令](#10-部署入口已经收敛成一条命令)
- [11. 支持范围，以及草稿为什么不能跨目标复用](#11-支持范围以及草稿为什么不能跨目标复用)
- [12. 怎么读本文的性能数字](#12-怎么读本文的性能数字)
- [13. DFlash 2：候选列表里还留着 2.5 个 token 的选择空间](#13-dflash-2候选列表里还留着-25-个-token-的选择空间)
- [14. DFlash 2 的两处新增在代码里长什么样](#14-dflash-2-的两处新增在代码里长什么样)
- [15. 按症状排查](#15-按症状排查)
- [16. 采用顺序：谁先上、谁再等](#16-采用顺序谁先上谁再等)
- [17. 五个自测题](#17-五个自测题)
- [18. 下一步读哪份代码](#18-下一步读哪份代码)
- [19. 维护指引：本文断言的核实方法与失效条件](#19-维护指引本文断言的核实方法与失效条件)
- [20. 参考来源](#20-参考来源)

## 1. 判断：它省掉的不是推理，是草稿的串行步骤

投机解码（speculative decoding）里有两笔成本：草稿花了多少时间，以及一次验证能收下多少个 token。加速比是这两笔成本的比值，任何一侧省得不够，另一侧就得赔回去。

DFlash 的判断落在这里：草稿侧的串行是主要矛盾，而草稿不需要独立成章。它不要求草稿模型自己会写文本，只要求它猜中大语言模型（LLM）接下来会写什么。于是草稿可以做成挂在目标模型上的一个适配器，5 层 Transformer 架构，共享目标的嵌入向量与输出头并冻结它们，只在推理时跑一次前向。

代价写在同一个地方：这个适配器和它的目标模型是绑死的。换目标模型就得重训草稿，没有跨模型通用的 DFlash checkpoint。第 11 节展开这条边界。

## 2. 仓库现状与核实口径

下表数字采集于 2026-09-20，来源是 GitHub 与 PyPI 的公开应用程序接口（API）；仓库代码取自 `main` 分支的提交 `07ebd93`（2026-08-18）。清单类信息最容易过期，所以每个数都注明它来自哪个字段，第 19 节给出复核命令。

| 项 | 值 | 来源 |
|---|---|---|
| Stars / Forks / Watchers | 6,102 / 432 / 45 | `/repos/z-lab/dflash` |
| Open issues | 103 | 同上 |
| 许可证 | MIT | `LICENSE`，`pyproject.toml` 的 `license` 字段 |
| 创建 / 最近推送 | 2026-01-04 / 2026-08-18 | `created_at`、`pushed_at` |
| 唯一 tag 与正式版 | `v0.1.0`（2026-08-18） | `/tags`、`/releases` |
| PyPI 版本 | 仅 `0.1.0`，2026-08-18 上传 | `pypi.org/pypi/dflash/json` |
| Python 要求 | `>=3.10` | `pyproject.toml` |
| 运行时依赖 | `tqdm==4.70.0`、`datasets==5.0.1`、`requests==2.34.2` | 同上 |
| 可选依赖组 | 只有 `local` 一个 | `[project.optional-dependencies]` |
| 代码规模 | 5 个 Python 文件，共 2,181 行 | `dflash/` 目录 |

`local` 组内部按平台切分：Linux 装 `jinja2==3.1.6`、`torch==2.13.0`、`transformers==5.15.0`，Apple Silicon 装 `mlx==0.32.0`、`mlx-lm==0.31.3`、`huggingface-hub==1.27.0`。两处细节容易被忽略：这个组在 Linux 上不装 MLX，在 macOS 上不装 torch，两个本地后端各自只被其中一个平台覆盖；vLLM 与 SGLang 从不出现在依赖里，它们是外部服务进程。

## 3. 系统地图：三段职责，一条数据回路

读这套代码前先分清三段，否则很容易把"草稿怎么生成"和"草稿怎么被接受"混成一件事。

```text
 prompt
   │
   ▼
 目标模型 prefill（权重不动）
   ├─ 出首 token，作为第一个锚点
   └─ 留下若干层隐状态 ──► 均匀取 5 层 → concat → 一次投影 → RMSNorm
                                          │
 [锚 token, mask, mask, …, mask] ─────────┤
                                          ▼
 草稿模型（5 层）：一次前向并行填出 block_size-1 个位置
   · 块内双向可见；目标特征只作 K/V 注入每一层，不进 Q、不进 FFN
   · 嵌入与 LM head 复用目标模型的，且冻结
                                          │
                                          ▼
 目标模型再一次前向，验证「锚 + 整块草稿」
   ├─ 贪心：取最长匹配前缀；采样：按 p/q 做拒绝采样
   ├─ 再补 1 个 bonus token ⇒ 本轮前进 1…block_size 个 token
   └─ 被拒位置的 KV 裁掉；接受前缀的隐状态成为下一轮上下文
                                          │
                                          └──► 下一个块
```

| 组件 | 承担的事 | 明确不承担的事 | 代码位置 |
|---|---|---|---|
| 目标模型 | 出首 token、出隐状态、验证整块 | 不知道草稿存在，结构与权重一字未改 | `dflash_generate` 里两次 `target(...)` |
| 草稿模型 | 一次前向并行填出一块 | 不做采样决策以外的任何推理，不产出最终文本 | `DFlashDraftModel` |
| 验证规则 | 决定收下几个 token、补哪一个 | 不做近似、不放宽，错了就整段丢 | `_rejection_sample` 与 `model.py` 的贪心分支 |
| 基准脚本 | 在同一进程里跑自回归与投机两条路并对比 | 不测绝对速度排名，只给相对倍数 | `dflash/benchmark.py` |

## 4. 自回归草稿的天花板写在一个公式里

论文 §3.1 用 Sadhukhan 等人的记号把每 token 平均延迟写成：

$$L=\frac{T_{\text{draft}}+T_{\text{verify}}}{\tau}$$

其中 $\tau\in[1,\gamma+1]$ 是一轮里平均被收下的 token 数，含目标模型白送的那个 bonus token；加速比为 $\eta=L_{\text{target}}/L$。分歧点在分子的 $T_{\text{draft}}$。自回归草稿每多猜一个 token 就多跑一次前向，$T_{\text{draft}}=\gamma\cdot t_{\text{step}}$，与 $\gamma$ 线性相关；并行草稿整块一次出，$T_{\text{draft}}=t_{\text{parallel}}$，对中等块长几乎不敏感。

这条线性关系解释了为什么自回归草稿只能做浅。EAGLE-3 的草稿就是一个 Transformer 层，容量摆在那里，$\gamma$ 再大 $\tau$ 也很快饱和，论文的措辞是这条路线"实际把可达加速封顶在 2–3×"。草稿一旦不再按 token 计费，加深就不再直接赔进延迟。作者给的对比是：5 层 DFlash 出 16 个 token，比 1 层 EAGLE-3 出 8 个 token 延迟更低，接受长度反而更长（论文图 3）。

顺带说清"块扩散"在这里指什么，它和图像扩散不是一回事。块扩散（block diffusion，Arriola 等人 2025 提出的形式）把序列切成块：块内位置互相可见、并行去噪，块与块之间保留因果顺序。DFlash 只取走"块内并行"这一件东西，其余环节都被它改掉了。

## 5. 目标特征注入 KV，而不是拼进输入

一种常见的误读是：DFlash 的草稿模型独立推理，不依赖目标模型的内部信息。代码里恰好相反，草稿的全部条件信息都来自目标模型的隐状态。注入方式才是它与 EAGLE 系列真正的分水岭。

取特征的过程很短。`build_target_layer_ids` 在 `1` 到 `num_target_layers-3`（0 起始索引，即第二层到倒数第三层）之间均匀取点，取几个取决于草稿层数；草稿只有一层时退化为取中间层。`extract_context_feature` 按这些层号把隐状态沿隐藏维 `cat` 起来，`DFlashDraftModel.__init__` 里的 `self.fc` 再把它压回草稿的隐藏维，过 `hidden_norm`。论文的默认配置是 5 层草稿配 5 组特征。

真正的选择在注意力里。`Qwen3DFlashAttention.forward` 里只有 Q 分支来自草稿 token：

```python
q      = self.q_proj(hidden_states)          # 草稿（含 mask 位置）
k_ctx  = self.k_proj(target_hidden)          # 目标模型特征
k_noise = self.k_proj(hidden_states)         # 草稿自身
k = torch.cat([k_ctx, k_noise], dim=1)       # 目标特征只当 KV 条目用
```

目标特征绕过草稿的 Q 投影、输出投影和 FFN，只以 K/V 的形式出现在**每一层**，并写进草稿自己的 KV 缓存里跨轮复用（论文 §A.3）。EAGLE-3 的做法是把特征与 token 嵌入融合后从输入端喂进去，层数一深就被稀释，这也是它加层不太涨的原因。消融实验（论文 §5.5.5，Qwen3-4B、5 层草稿、块长 8）给出的结论是：无论草稿是自回归还是块扩散，逐层注入都比只在输入端注入拿到更长的接受长度。

代价小得有点不成比例。多出来的可训练参数只有一个共享投影 $W_c\in\mathbb{R}^{D\times 5D}$。论文以 Qwen3.5-35B-A3B（$D=2048$、BF16）算过这笔账：$5\times2048\times2048\times2\approx 42$ MB，相对约 70 GB 的目标模型可以忽略。激活侧同样不大：批大小 1、序列长 2048 时投影的输入/输出约 40 MB / 8 MB，块长 16 解码时的临时激活不到 400 KB。

## 6. 一步去噪：块内除锚点外全是 mask

推理时的"加噪"没有噪声，是掩码。`dflash_generate` 一开始就把输出张量整个填成 `mask_token_id`，每轮取 `verify_size = min(block_size, 剩余预算)` 个位置当作待填块；MLX 侧写得更直白：

```python
# dflash/model_mlx.py: 块 = 上一个已确认 token + (bs-1) 个 mask
block = mx.array([[tokens[-1]] + [mask_id] * (bs - 1)])
```

第一个位置是锚：上一轮验证里目标模型自己吐出来的那个 token，干净、可信。剩下 `bs-1` 个位置一次前向同时填完，贪心时取 `argmax`，采样时按分布抽。没有逐步去噪迭代，没有多步调度——这是"block diffusion drafter"和 dLLM 之间的实际差别。

之所以敢只走一步，靠的是锚点带着信息进来。除了块首 token，草稿还看到整段目标特征。论文引用的观察来自 Samragh 等人：大型自回归模型的隐状态里本来就以某种形式编码了未来若干个 token。草稿于是更像"读目标的下一步意图"，而不是"从零续写"。反向消融支持这个判断：作者训练了一个完全不看目标特征的 5 层块扩散草稿，加速只剩 2–3×（论文表 10）。这和"把 EAGLE 换成块扩散但不给条件信息"没有区别，说明增益主要不来自扩散本身。

块内可见性由配置决定，不是全局因果。`layer_types` 里 `sliding_attention` 的层默认取因果掩码，`full_attention` 的层默认非因果（`self.is_causal = layer_type == "sliding_attention"`，除非 `is_causal` 显式给出），滑窗层的可见范围再被 `sliding_window` 截断。训练时用的是块对角的稀疏掩码：块内双向、跨块不可见、注入的目标特征始终可读。多个草稿块拼成一条序列一次前反向，靠 FlexAttention 实现。

## 7. 训练的四处非标准做法

标准块扩散训练把 response 均分成块、块内随机遮蔽。DFlash 改了四处，每处都对应推理时的一个具体行为（论文 §4.2、§A.1）：

| 改动 | 做法 | 为什么这么改 |
|---|---|---|
| 锚点随机采样 | 从 response 里随机挑 token 作为块首，遮蔽其后 `block_size-1` 个位置，一个序列采 512 个锚点 | 推理时草稿永远条件于"目标刚产出的干净 token"，均分块对不上这个分布；随机锚点顺带起数据增强作用（表 13：接受长度与加速都更好） |
| 位置衰减的交叉熵 | $w_k=\exp(-(k-1)/\gamma)$，块长 16/10/8 分别取 $\gamma=7/5/4$ | 块内前一个 token 错，后面全作废，早期位置对 $\tau$ 的贡献不成比例地大；消融（图 5）显示比均匀加权收敛更快也更高 |
| 冻结嵌入与输出头 | 草稿共享目标模型的嵌入向量层（token embedding）和输出头（LM head），两者不参与训练，只更新草稿的 Transformer 层 | 少训一大量参数，同时把草稿钉在目标的表示空间里，逼它做适配器而不是独立语言模型 |
| 训练数据用目标自己的输出 | 约 800K 条 NVIDIA Nemotron Post-Training Dataset V2 与 CodeAlpaca 混合，但答案换成目标模型重新生成的 response | 草稿要拟合的是"这个目标模型会怎么写"，不是"标准答案长什么样" |

其余超参：AdamW，学习率 $6\times10^{-4}$，梯度裁剪 1.0，余弦调度、warmup 比例 0.04，6 个 epoch，最大序列长 3072（Qwen3-Coder 用 4096），每条序列采 512 个锚点位置。特征可以在线算（online），也可以预先缓存后离线读（offline）。后者省算力，代价是缓存目标隐状态的存储量随抽取层数线性增长——这也是论文把目标特征从 3 组加到 5 组时给出的唯一代价。

训练代码不在仓库里。README 的旧版本写过"训练 recipe 会很快开源"，而 `07ebd93` 的仓库里仍然只有推理与基准两个入口。自训草稿这条路目前只能参照论文描述自行复现。

## 8. 无损性来自验证规则，而不是草稿猜得准

"lossless" 是投机解码最容易被含糊带过的词。看代码就不含糊了。贪心时（温度设为 0）：

```python
# dflash/model.py: 只接受最长匹配前缀
posterior = torch.argmax(output.logits, dim=-1)
acceptance_length = (block_output_ids[:, 1:] == posterior[:, :-1]).cumprod(dim=1).sum(dim=1)[0].item()
bonus = posterior[:, acceptance_length][0]
```

`cumprod` 的作用是让第一个不匹配及其后所有位置一起归零——不是逐位置独立判断，而是一旦断了后面全丢。随后 `bonus` 从目标模型自己的分布里取，所以哪怕整块一个都没接受，这一轮也至少产出 1 个 token。变量 `acceptance_length` 最大只能到 `block_size-1`（草稿位置一共就这么多），加上 bonus 才是本轮真正推进的 token 数，范围 1…`block_size`；把草稿数记作 $\gamma=\text{block\_size}-1$，正好对上 §3.1 里 $\tau\in[1,\gamma+1]$ 的区间。

采样时换成标准的拒绝采样。`_rejection_sample` 里接受概率是 $p/q$，$p$ 为目标分布落在该 token 上的概率，$q$ 为草稿分布。截断方式同样是 `cumprod` 前缀。一旦拒绝，补位 token 不再取目标的 argmax，而是从残差分布 $\max(p-q,0)$ 归一化后抽：

```python
residual = target_probs[0, accepted].clone()
residual.sub_(draft_probs[0, accepted])     # 或按候选集 scatter_add_ 扣掉 q
residual.clamp_min_(0)
```

这一步不能省。逐位置独立抽样、或者在拒绝处直接用目标 argmax，都会把输出分布推到目标分布之外，只是"看起来差不多"。残差采样才是让加速与目标模型逐 token 同分布的那个机制；MLX 分支里 `draft_indices` 那一套是同一件事的候选集版本（第 14 节）。

草稿越准，收益越大；草稿不准，退化路径是"这一轮只前进 1 个 token"，而不是输出变了。这是把扩散关进草稿阶段的真正收益：草稿的质量下限被验证规则接管了。

## 9. 一次提问如何流过整个系统

拿 README 里反复使用的那个示例问题走一遍：`"How many positive whole-number divisors does 196 have?"`，配置 `block_size=16`、贪心解码。

1. `apply_chat_template` 把消息渲染成提示词（prompt），`_reasoning_kwargs` 决定要不要传 `enable_thinking` 或某个 reasoning 档位（第 10 节）。
2. 目标模型 prefill 整段 prompt，`logits_to_keep=1` 只留最后一个位置的 logits，同时 `output_hidden_states=True` 把选中的 5 层隐状态带出来；`extract_context_feature` 拼成 `target_hidden`。首 token 由 `sample` 决定，写进输出并作为第一个锚点。
3. 第一轮草稿：输入是 `[锚, mask ×15]` 的嵌入（`_raw_input_embeddings`，再乘 `input_embedding_scale`），位置从 `start - target_hidden.shape[1]` 起算，好让草稿同时看见历史和当前块。一次前向后 `[:, 1-verify_size:]` 切出块内位置，`argmax` 填出 15 个候选。
4. 目标模型把"锚 + 15 个候选"当成一条长度为 16 的序列再前向一次，得到 16 个位置的分布。贪心分支逐位比对，假设第 9 个候选断了：接受 8 个，加上 `bonus` 共前进 9 个 token，而这只花了一次目标前向。
5. 收尾动作是这轮真正费事的地方：`_crop_to(past_key_values_target, start)` 把目标 KV 裁回合法前缀，`_crop_to(past_key_values_draft, start)` 对草稿做同样的事，然后 `target_hidden = extract_context_feature(...)[:, :produced, :]`——下一轮的条件特征只保留本轮被接受的那几个位置的隐状态。
6. 回到第 3 步，直到 `start + 1 >= max_length` 或命中 `stop_token_ids`。

如果目标是 Qwen3.5 这类混合线性注意力结构，第 5 步在 MLX 上还要多做一层。`can_trim_prompt_cache` 返回 False 时，脚本装上 `_GDNStateCapture`，把 `GatedDeltaNet.__call__` 暂时替换成会记录 conv state 与 GDN 输入的版本；被拒之后用接受前缀重放 `gated_delta_update` 来恢复状态（`_capture.rollback`）。线性注意力没有可以裁掉的 KV，只能重算。这段补丁是全仓库最不显眼、却最能说明"混合架构会拖累投机解码"的地方。

## 10. 部署入口已经收敛成一条命令

2026-08-18 的两个提交把安装方式整个换了：`Prepare PyPI release` 与 `Add unified DFlash CLI and packaging`。此后统一走一条命令行工具（CLI）入口，`README` 里只剩两条安装命令：

```bash
pip install dflash            # 只作为 OpenAI 兼容服务端的客户端
pip install "dflash[local]"   # 需要本地跑 Transformers / MLX 时再加
```

`[project.scripts]` 注册的入口是 `dflash = "dflash.cli:main"`，两个子命令 `generate` 与 `benchmark`，后端只有 `transformers`、`mlx`、`openai` 三个取值。旧文档里 `uv pip install -e ".[transformers]"`、`".[vllm]"`、`".[sglang]"` 这类写法已经失效——当前 `pyproject.toml` 只剩 `local` 一个可选组（这些组在 4 月的版本里存在过），`python -m dflash.benchmark --backend vllm` 同样走不通，vLLM 与 SGLang 现在都通过 OpenAI 兼容协议接入：

```bash
# 本地：Transformers 后端
dflash generate transformers \
    --model meta-models/Muse-Glimmer-30B \
    --draft z-lab/Muse-Glimmer-30B-DFlash2 \
    --reasoning high --temperature 1 --top-p 0.95 --top-k 64 \
    "How many positive whole-number divisors does 196 have?"

# 本地：Apple Silicon，目标与草稿都走 4-bit
dflash generate mlx \
    --model mlx-community/Qwen3.8-27B-4bit \
    --draft z-lab/Qwen3.8-27B-DFlash2 \
    --draft-bits 4 --block-size 5 --reasoning xhigh \
    "How many positive whole-number divisors does 196 have?"

# 远端：任何 OpenAI 兼容服务（SGLang / vLLM / …）
dflash generate openai --base-url http://127.0.0.1:8000 --model Qwen/Qwen3.8-27B \
    "How many positive whole-number divisors does 196 have?"
```

`cli.py` 里有三条约束最常撞上。`--draft` 对两个本地后端必填，缺了直接 `parser.error`。`--temperature`（温度）取 0 即贪心解码。`--reasoning` 的语义由目标模型的聊天模板决定，逻辑在 `_reasoning_kwargs`：模板里有 `enable_thinking` 才允许 `on`/`off`，要传档位（如 `high`、`xhigh`）则模板里必须有 `reasoning_strength` 或 `reasoning_effort`，否则抛 `ValueError`。README 为两个模型家族分别指定了档位键与默认值——Muse 走 `reasoning_strength`，取值 `low`/`medium`/`high`/`xhigh`，默认 `high`；Qwen3.8 走 `reasoning_effort`，取值 `low`/`medium`/`xhigh`，默认 `xhigh`。旧示例里的 `enable_thinking=False` 现在应该写成 `--reasoning off`。

服务端配置在各家上游，README 用链接指向对应的 PR。按合并状态实测：

| 引擎 | 启动命令与关键参数 | DFlash 进主干 | DFlash 2 进主干 |
|---|---|---|---|
| vLLM | `vllm serve Qwen/Qwen3.8-27B --speculative-config '{"method": "dflash", "model": "incoai/Qwen3.8-27B-DFlash2", "num_speculative_tokens": 7}'` | #36847，2026-03-30 | #52816，2026-08-21 |
| SGLang | `python -m sglang.launch_server --model-path Qwen/Qwen3.8-27B --speculative-algorithm DFLASH --speculative-draft-model-path incoai/Qwen3.8-27B-DFlash2 --speculative-num-draft-tokens 8` | #22077，2026-04-07 | #35371，2026-08-19 |
| llama.cpp | `llama-server -hf … -hfd … --spec-type draft-dflash --spec-draft-n-max 7` | #22105，2026-06-28 | #27342，2026-08-27 |
| oMLX | 装 z-lab 维护的 oMLX 派生版本所带的 `0.6.2-dflash2` 预构建包，在 Model Manager 里填 draft model 与 `Verify mode: dflash` | — | 该派生版本 |
| TensorRT-LLM | 见其 quickstart | #12794，2026-04-27 | 本文未核实 |
| Ollama | 构建 PR 分支后 `ollama create --draft-quantize int4` | — | #17865 **仍是 open** |

两份清单不完全一样。README 的 `For serving benchmarks` 一句列的是 SGLang、vLLM、oMLX、llama.cpp；DFlash 2 发布文另外把 TensorRT-LLM 与 Ollama 也写进可用列表，并声称 DFlash "现在跑在 SGLang、vLLM、TensorRT-LLM 和 llama.cpp 里"。前一句是仓库口径，后一句是发布方口径，差别在 oMLX 与 TensorRT-LLM 上。可以确定的是：README 旧版那句"vLLM 需要装 nightly"在 2026-09 已经不需要，DFlash 早在 3 月底就进了 vLLM 主干；而 Ollama 的支持要自己拉 PR 分支编译，不能算现成可用。

## 11. 支持范围，以及草稿为什么不能跨目标复用

`README` 的 `Supported Models` 一节是当前的权威清单，按家族给，不逐个列 checkpoint id：

- Qwen：Qwen3.6（27B、35B-A3B）、Qwen3.5（4B、9B、27B、35B-A3B、122B-A10B、397B-A17B）、Qwen3（4B/8B 非思考、Coder-Next、Coder-30B-A3B）
- Gemma 4（12B、31B、26B-A4B）；MiniMax M2.5、M2.7；Kimi K2.5、K2.6、K2.7-Code
- 其他：GPT-OSS（20B、120B）、Llama-3.1-8B、GLM 5.1、Alpamayo 1.5 / R1 10B
- DFlash 2：`z-lab/Muse-Glimmer-30B-DFlash2`、`z-lab/Qwen3.8-27B-DFlash2`

但"支持"分两个层次，混起来最容易踩坑。README 明写：Transformers 后端只覆盖 DFlash 2 的 Muse-Glimmer-30B 和 DFlash 的 Qwen3、LLaMA-3.1-8B；MLX 后端覆盖 DFlash 2 的 Qwen3.8-27B 与 DFlash 的 Qwen3、Qwen3.5、Qwen3.6、Gemma 4。**其余 checkpoint 只能走 OpenAI 兼容服务端**，本地 Python 接口接不上。

草稿与目标绑死不是工程妥协，是配置里写明的。草稿 checkpoint 的 `config.json` 有一个 `dflash_config` 块，`load_draft` 会逐项读取：

```python
block_size          # 一个块占几个位置（含锚点），缺省 16
target_layer_ids    # 抽取目标哪几层的隐状态，缺失直接 KeyError
mask_token_id       # 词表里哪个 id 当掩码，同样必填
input_embedding_scale / output_multiplier / final_logit_softcapping
conv_kernel_size / conv_group_size / selector_rank / selector_top_k   # DFlash 2 专用
```

`num_target_layers` 取的是顶层配置而非这个块，只有 PyTorch 侧会用它：`build_target_layer_ids` 拿它推导层号，MLX 侧则直接读现成的 `target_layer_ids`。再叠加草稿复用目标的嵌入与 LM head、特征按目标的层号切片，一个 checkpoint 只能加速它配的那一个目标。README 末句"其他 checkpoint 可以通过 OpenAI 兼容服务来跑"其实也建立在这个前提上：服务端加载的是配好的一对。

README 里还有一条 MLX 口径：目标或草稿走量化时把块长压到 5 以内，理由是 MLX 现有量化 matmul kernel 在较大 verify 宽度下效率下降。

## 12. 怎么读本文的性能数字

先说这些数字测的是什么。论文主表用 Transformers 后端、NVIDIA H200、最多生成 2048 token，指标是相对同模型自回归基线的端到端加速比与平均接受长度 $\tau$。服务侧表格换成单张 B200 上的 SGLang（FA4 后端、开启 Spec-v2 调度重叠）与 vLLM，指标是 tok/s。第三方数字来自各自厂商，设定又不相同。三类之间不能互相换算。

论文侧：

| 设定 | 结果 |
|---|---|
| Qwen3 instruct、思考模式关闭、贪心 | 平均 4.9×，是 EAGLE-3（tree 16）的 2.4× |
| 同上、`temperature=1` | 平均 4.1×，是 EAGLE-3 的 2.2× |
| Qwen3-8B（图 1 的最高点） | 6.1× |
| Qwen3-4B / 8B 开启思考，GPQA、MATH-500、AIME25 | T=0 约 4.5×、T=1 约 3.9×，$\tau$ 在 4.55–5.82 之间 |
| SGLang，Qwen3-8B Math500，并发 1→32 | 5.1× → 2.8×（HumanEval 4.2× → 2.4×） |
| SGLang，Qwen3-4B Math500（$\tau=8.01$） | 4.8× → 2.9×；HumanEval（$\tau=6.63$）4.0× → 2.2× |
| vLLM，Qwen3.5-9B 绝对吞吐，并发 1→32 | Math500 849→9,836 tok/s，倍数 4.0×→1.9× |
| SGLang 并发 8，对照目标模型自带的 MTP | Qwen3.5-9B 的 Math500 一列：MTP 6.7/$1.7\times$，DFlash 7.3/$3.5\times$ |

DFlash 2 侧的数字来自 Inco AI 的发布文（2026-08-18），指标是每请求平均接受长度。Qwen3.5-4B 五个数据集的均值从 DFlash 的 4.92 抬到 5.97，多出 1.05 个 token、约 21%，同期 MTP 为 4.54、DSpark 为 5.49。另两组对照：Qwen3.8-27B（块长 8）对自带 MTP 是 4.80 vs 4.28，Muse Glimmer（块长 16）对 Meta 官方 DFlash 草稿是 5.70 vs 4.44。折算成吞吐，作者给的是相对自回归解码 2.7–3.4× 与 3.1–4.6×。

第三方数字只能转述。NVIDIA 在 8×DGX B300 + TensorRT-LLM 上测 gpt-oss-120b，声称在同一交互水平（每用户 500–600 tok/s）下吞吐提升超过 15×，比 EAGLE-3 高 1.5×，批大小 1 时交互性翻倍。同一篇里还有 Gemma 4 31B 在单卡 Blackwell Ultra + vLLM 上最高 5.8×，以及 SGLang 单卡 B200 上 Qwen3-8B 的 Math500、HumanEval 分别为 5.1×、4.2×（与论文表 3 是同一组数据）。

**从这些数字不能推出什么**，四条：

1. 加速比是同一实现内部的比值，不是绝对速度排名。基线换成另一个 kernel、另一个后端版本，分子分母一起变，倍数没有可比性。
2. 并发越高倍数越小是预期行为，不是回归。批处理本来就在用并行度掩盖串行的访存瓶颈，草稿再叠一层并行，边际收益被压薄。vLLM 那一行最典型：并发 1→32 时绝对吞吐从 849 涨到 9,836 tok/s，倍数却从 4.0× 掉到 1.9×——该看的是"同并发下比基线快多少"，而不是"最大倍数"。
3. 论文报的量是平均接受长度 $\tau$，没有报整体接受率。DFlash 2 发布文里那个 85.4% 是另一回事：它是位置 0 上的条件 Recall@1，也就是"前面位置全对时，本位首选命中"的比例，不能读成"草稿 85% 的情况下都对"。
4. 论文主表都是"最多生成 2048 token"的短任务。长上下文另有一组证据：在 4K 上下文上训出的 Qwen3.5-27B 草稿，序列一过 4K 接受长度就明显下滑（hotpotqa 从 4K 的 4.91 掉到 16K 的 3.61）；用 LongAlign-10K 的 1.6K 条样本微调 3 个 epoch 后，同一位置升到 6.05，32K 上的 gov_report 也从 2.09 回到 3.56（表 4）。长文本业务要按这组数字判断，而不是照搬 4.9×。

自己的环境怎么量，由 `benchmark.py` 的实现决定口径。Transformers 后端走的是最干净的一条对照：同一进程里对每条样本跑两遍，`block_size=1` 当基线（此时草稿分支被整个跳过），`block_size=draft.block_size` 当投机；正式计时前两边各生成 min(64, max_new_tokens) 个 token 做 warmup，数据集顺序用 `random.Random(42)` 洗牌。MLX 后端的基线不是同一套代码——它调 `mlx_lm` 自己的 `stream_generate`，warmup 也只跑 `"Hi"` 三个 token，因此它给出的加速比是跨实现的比较。两种后端最后都打印基线吞吐、DFlash 吞吐、`Decoding speedup`、平均接受长度，以及一个 0…block_size 的接受长度直方图。

两个坑要单独说。`Average Acceptance length` 是"每请求均值的再平均"，长回答的请求不会获得更大权重。OpenAI 后端只报端到端 tok/s 和 `meta_info` 里的 `spec_accept_length`、`spec_verify_ct`，**不会**自动给出加速比，想要倍数得自己把服务端投机解码关掉再跑一遍。

## 13. DFlash 2：候选列表里还留着 2.5 个 token 的选择空间

DFlash 2 是 2026-08-18 放出的后续版本，发布文署名 Inco AI。同一个草稿在两份材料里前缀不同：README 写 `z-lab/Qwen3.8-27B-DFlash2`，发布文的命令与模型集合用 `incoai/` 前缀。它的标题是 "Keep Drafting Parallel"，态度很明确：不改回自回归草稿，而是在保持一次前向的前提下补两处损失。

第一处的证据来自一张很朴素的表。在 Qwen3-4B、5 层草稿、GSM8K 上，按"前面位置全对"为条件统计各草稿位置的正确率。位置 0 的 top-1 是 85.4%，而 top-16 里含正确 token 的概率是 99.5%；到位置 6，两者降到 72.9% 与 87.8%。一个总能从 16 个候选里挑对的 oracle 能把 $\tau$ 从 4.27 提到 6.79。也就是说，**正确答案已经在列表里，只是没被选到**——缺的不是更好的预测，是一次选择。

选起来也不必花大钱。作者主张相关性是局部的：一个候选合不合适，主要取决于紧挨着的前一个 token。于是每对相邻候选这样打分：

$$S_t(a,b)=U_t(b)+\langle A(a)\odot H(h_t),\;B(b)\rangle$$

$U_t(b)$ 就是 DFlash 自己给的 logit，后一项把前驱 $a$ 与后继 $b$ 各查一个 256 维嵌入、逐元素相乘后在上下文门 $H(h_t)$ 下内积——一个低秩的双线性相邻词打分器。打分本身完全并行，唯一串行的是在算好的分数上做一次贪心走链。代价：多 2.0M 参数、多 0.6% 的 draft–verify 周期延迟，$\tau$ 从 4.27→4.61（T=0）、3.78→4.25（T=1）。同表里 DSpark 的写法要 +77.8M 参数、+9.6% 延迟才换到 4.49/4.08。作者的说法是"选择比预测便宜"，并且离 oracle 还有空间。

第二处叫 suffix decay：即使选择完美，Recall@16 也从 99.5% 一路滑到 87.8%，说明候选本身在块尾不够用。作者先排除了"加深"这条路——15 层草稿确实把位置 6 从 72.86% 抬到 78.73%，但参数 ×3、周期延迟 +15.2%，前几个位置几乎没收益。然后他们看注意力预算：块内注意力占比从第 1 层的 30% 掉到第 5 层的 8%，剩下的集中在少数头上。既然块内职责短程，就用一个两抽头的动态深度可分离卷积顶上：

$$\operatorname{Conv}_k(x)_t=k_{t,0}\odot x_t+k_{t,1}\odot x_{t-1}$$

每个系数由"学出来的基核 + 由当前隐状态算出的修正"合成，每 16 个通道共享一个修正；块的第一个位置读上一个已确认 token 的表示。这个模块只在块内作用、不带跨步状态，所以不动注意力、不动 LM head、不动验证就能插进去。结果：+16.5M 参数（3%）、+0.7% 周期延迟，5 层草稿加卷积后的逐位置正确率逼近 15 层；第 4、5 层的平均块内注意力占比从 9.4% 降到 0.5%，也就是卷积把短程活儿接走了，注意力回去读上下文。

两个模块合起来只加 1.3% 周期延迟。这是 DFlash 2 最实在的地方：收益全部落在"一次目标前向多收下多少 token"上，而草稿成本几乎不变。

## 14. DFlash 2 的两处新增在代码里长什么样

`DFlash2DraftModel` 继承 `DFlashDraftModel`，构造时给每个 decoder layer 挂两个卷积模块，再挂一个 `candidate_selector`。加载路径靠架构名判别，两份实现（PyTorch、MLX）用的是同一个约定：

```python
draft_class = (DFlash2DraftModel
               if "DFlash2DraftModel" in (config.architectures or [])
               else DFlashDraftModel)
```

`GroupedDynamicCausalConv` 里 `base_kernel` 形状 `(2, kernel_size, hidden_size)`，第 0 维把 `prepare` 与 `finish` 两次调用的基核分开存（`base_kernel[0]` 给前者、`base_kernel[1]` 给后者）；注意力与 MLP 各自持有一个独立实例，即 `layer.attention_conv` 与 `layer.mlp_conv`。`kernel_projection` 是从隐状态到 $2\cdot k\cdot \text{groups}$ 的无偏置线性层，也就是"修正"部分。分组数来自 `conv_group_size`，与发布文里"每 16 通道共享一个修正"对应。

`CandidateSelector.select` 就是那条贪心走链，逻辑一共十几行：

```python
unary, candidates = torch.topk(logits, self.top_k, dim=-1, sorted=False)
hidden = self.hidden_projection(hidden)
predecessor = anchor_ids                      # 从上一个已确认 token 起走
for position in range(hidden.shape[1]):
    scores = unary[:, position] + torch.einsum(
        "br,bkr->bk",
        self.predecessor_codebook(predecessor) * hidden[:, position],
        self.successor_codebook(candidates[:, position]),
    )
    index = torch.argmax(scores, dim=-1)          # temperature>0 时改为按 scores 抽样
    predecessor = candidates[:, position].gather(-1, index[:, None])[:, 0]
    path.append(predecessor)
```

注意它返回的不只是 `path`，还有 `candidates` 与（采样时的）`q_rows`。草稿分布不再是整个词表上的 softmax，而是"top-k 候选 + 一个配对项"，于是验证端计算 $q$ 时不能直接 gather，得先把落在候选集上的概率求和：

```python
q = (draft_probs * (draft_indices == draft_tokens[..., None])).sum(-1)
```

同一段逻辑在 `_rejection_sample` 里通过 `draft_indices is None` 分支共存——这处细节很容易被忽略，自己改草稿结构时如果漏掉它，无损性就没了。

块首锚点参与嵌入但不产出 logits，这一约束在两条实现里表达得不一样：PyTorch 侧靠切片（`draft_hidden[:, 1 - verify_size:, :]`、`block_output_ids[:, 1:] = draft_tokens`），MLX 侧用 `logits_start=1` 参数。权重键名的兼容处理也分家：PyTorch 在 `DFlash2DraftModel.from_pretrained` 里用 `key_mapping` 把 `candidate_selector.*_codebook` 映射到带 `.weight` 的写法，MLX 则在 `load_draft` 里手工 `pop` 再改名。两处都是 2026-08-18 的提交专门处理过的事。

## 15. 按症状排查

下面每一条都对应仓库里现存的报错字符串或显式约束，触发条件写在中间那一列。

| 现象 | 直接原因 | 处理 |
|---|---|---|
| `--draft is required for local backends` | `generate`/`benchmark` 选了 `transformers` 或 `mlx` 却没给草稿 | 补 `--draft`；只有 `openai` 后端允许省略 |
| `This model supports only --reasoning on/off` | 传了档位，但目标聊天模板里没有 `reasoning_strength`/`reasoning_effort` | 改传 `on`/`off`，或按 README 用该模型支持的那个档位键 |
| `This model does not support --reasoning on/off` | 模板里没有 `enable_thinking` 却传了 `on`/`off` | 去掉 `--reasoning` |
| `Unknown dataset '…'. Available: […]` | 数据集名不在 `DATASETS` 里 | 只有 `gsm8k`、`math500`、`humaneval`、`mbpp`、`mt-bench` |
| `Draft config layer_types length must match num_hidden_layers.` / `Unsupported draft layer_types: […]` | 手写或改过的草稿 `config.json` 与层数不一致，或用了 `full_attention`/`sliding_attention` 之外的值 | 按草稿层数重排 `layer_types` |
| `Draft config must define sliding_window for sliding_attention layers.` | 有滑窗层但没给窗口大小 | 补 `sliding_window` |
| `Cannot find embed_tokens in <Model>` / `Cannot find layers in <Model>` | MLX 的 `bind`/`get_layers` 没适配这层模型包装 | 检查模型是否被包在 `model` 或 `language_model.model` 下 |
| `non-trimmable cache count (N) != captured GDN inputs (M)` | 混合线性注意力目标上，缓存里不可裁剪的层数与捕获到的 GatedDeltaNet 层数不等 | 这条断言的前提是"所有不可裁剪缓存都是 GDN 层"；不满足就不能用 MLX 回退路径 |
| 加速比远低于论文 | 常见两类：并发已经很高（倍数随并发单调下降），或推理块长大于训练块长 | 降 `--block-size`；块长的泛化是单向的，见本节末段与论文 §5.5.4 |
| `dflash benchmark openai` 不报加速比 | 该后端只统计端到端吞吐 | 关掉服务端投机解码再跑一遍同一数据集，自行取比值 |

块长这一条值得多说一句，因为它是少数有反向证据的自由参数。论文分别用块长 8 和 16 训练两个草稿再交叉测试：块长 8 的模型在 Math500 上 35.7% 的块是整块接受，说明预算常常没用满；**训练块长大的模型可以在推理时用更小的块，接受长度接近天生小块训练的那个，反过来则不成立**。所以线上想收小块时，该拿一个训练块长为 16 的 checkpoint 降参数跑，而不是指望块长 8 的草稿撑到 16。至于取几层，消融（表 6）的结论是 8 层接受长度更长、5 层端到端更快——除非你的瓶颈在草稿侧而不在验证侧。

## 16. 采用顺序：谁先上、谁再等

先上的场景有三个共同点：解码占端到端时间大头、并发压得不高、目标模型有配套的草稿。单条长回答、交互式编码、agent 工具调用循环都属于这一类；NVIDIA 用多智能体工作流作为 15× 那组数字的背景不是巧合，agent 的 token 消耗量把解码延迟直接放大成了成本。批大小 1 的本地部署也属于这一类，此时验证那一次前向几乎白送。

可以再等一等的：

- 输出很短或者模板化程度低。一轮只前进 1–2 个 token 时，草稿开销就开始显形。
- 高并发且已经打满算力。倍数会掉到 2× 上下（§12 的 vLLM 行），此时先算绝对吞吐是否划算，而不是照搬宣传语里的最大倍数。
- 长上下文业务且不做微调。在 4K 上下文上训出的草稿，序列一过 4K 接受长度就往下掉，需要 LongAlign 那类数据再训一轮。
- 目标模型没有现成 checkpoint。自训草稿要自己复现论文那套"用目标模型重新生成 response"的数据管线，而仓库里没有训练代码。

真要上，顺序建议这样排。先用 `dflash benchmark transformers`（或 MLX）在同一进程里量一次相对加速，确认你的数据分布上 $\tau$ 明显大于 1。再在测试服务上开投机跑 `dflash benchmark openai`，把 `spec_accept_length` 与吞吐和关掉投机的同配置服务并排比对。最后按生产环境的并发档位重估收益。整个过程中值得盯的不是倍数，是接受长度直方图——它压在 1–2 上时，说明该换 checkpoint 或降块长，而不是加卡。

## 17. 五个自测题

1. 为什么 DFlash 敢把去噪压成一步，而独立的扩散语言模型不行？答案要同时落在草稿的角色和验证规则上。
2. `cumprod` 在验证里做了什么？把它换成逐位置独立比较会破坏什么性质？
3. 一个草稿 checkpoint 的 `config.json` 里，哪些字段决定了它只能配某个目标模型？至少说出 `dflash_config` 下的三个。
4. 并发从 1 提到 32，绝对吞吐上升而加速倍数下降，这两件事为什么不矛盾？此时该用哪个指标决定是否继续开着投机。
5. 把推理块长设成比训练块长更大，论文里有没有支持这种泛化的证据？反过来呢？

五题的答案依次落在第 6 与第 8 节、第 8 节、第 11 节、第 12 节和第 15 节。答不出的那一题，通常就是对应那节里最容易被跳过的机制。

## 18. 下一步读哪份代码

想验证本文关于机制的断言，`dflash/model.py` 里按这个顺序读大约 200 行就够：`build_target_layer_ids` → `extract_context_feature` → `Qwen3DFlashAttention.forward` 的 k/v 拼接 → `dflash_generate` 的主循环（`verify_size`、`_crop_to`、贪心接受三处）。

其余分流按问题找。想知道目标特征为什么能提升接受长度，读论文 §5.5.5 与 §A.2 的两组消融。想知道混合架构的代价落在哪，读 `model_mlx.py` 的 `_GDNStateCapture`。想自己接一个后端，`cli.py` 的三个分支就是最小调用面。至于 DFlash 2 的两处新增，全在 `CandidateSelector` 和 `GroupedDynamicCausalConv` 两个类里，PyTorch 与 MLX 各一份，可以对照着读。

## 19. 维护指引：本文断言的核实方法与失效条件

本文的结论分三类，失效条件不同，复核方式也不同。

**版本敏感类**（安装命令、可选依赖组、命令行参数、支持模型列表、后端能力边界、各引擎 PR 状态）以提交 `07ebd93` / 正式版 `v0.1.0` 为准。复核：

```bash
git clone --depth 1 https://github.com/z-lab/dflash.git
curl -s https://api.github.com/repos/z-lab/dflash | jq '{stargazers_count,pushed_at,license:.license.spdx_id}'
curl -s https://pypi.org/pypi/dflash/json | jq '.info.version, (.releases|keys)'
for pr in vllm-project/vllm/pulls/52816 sgl-project/sglang/pulls/35371 \
          ggml-org/llama.cpp/pulls/27342 ollama/ollama/pulls/17865; do
  curl -s "https://api.github.com/repos/$pr" | jq '"\(.title) merged=\(.merged) @\(.merged_at)"'
done
```

**论文事实类**绑定 arXiv:2602.06036v2：加速比、接受长度、层数与块长、超参、消融结论、显存估算都在这类。v1 提交于 2026-02-05，v2 修于 2026-05-28。这类结论不随仓库改版失效，但论文出 v3 就得重读。

**二手转述类**只到"某方如此声称"这一层：NVIDIA 的 15× 与 5.8×、Google TPU 的 3×、CoreWeave 默认启用 DFlash、Hugging Face 累计下载 350 万、各厂商发布自家的 DFlash 草稿，都在这一类。本文没有复现条件，也不把它们当作实测结果。这类数字最容易随版本迭代变化，引用时必须带着出处。

改动本文时最容易漏两处。一是新增性能数字要同时写明后端与并发，否则 §12 的读法失效；二是别把 $\tau$ 与条件 Recall@1 混成一个量，这两个名字在文中都出现过，含义不同。

## 20. 参考来源

以下链接均在 2026-09-20 实测可访问：

- 仓库：<https://github.com/z-lab/dflash>（MIT，6,102 Stars，最近推送 2026-08-18）
- 论文：Chen, Liang, Liu. *DFlash: Block Diffusion for Flash Speculative Decoding*. arXiv:2602.06036v2 — <https://arxiv.org/abs/2602.06036>
- 项目页：<https://z-lab.ai/projects/dflash/>（`dflash.z-lab.ai` 重定向至此）
- DFlash 2 发布文：<https://inco.ai/blog/dflash2/>
- DFlash 模型集合：<https://huggingface.co/collections/z-lab/dflash>、<https://huggingface.co/collections/z-lab/dflash-2>
- NVIDIA 技术博客，讲 DFlash 在 Blackwell 上的推理提速：<https://developer.nvidia.com/blog/boost-inference-performance-up-to-15x-on-nvidia-blackwell-using-dflash-speculative-decoding/>
- Google 开发者博客（TPU 上的扩散式投机解码）：<https://developers.googleblog.com/supercharging-llm-inference-on-google-tpus-achieving-3x-speedups-with-diffusion-style-speculative-decoding/>
- 上游集成 PR：vLLM #36847、#52816；SGLang #22077、#35371；llama.cpp #22105、#27342；TensorRT-LLM #12794；Ollama #17865（截至本文仍未合并）

```bibtex
@article{chen2026dflash,
  title   = {{DFlash: Block Diffusion for Flash Speculative Decoding}},
  author  = {Chen, Jian and Liang, Yesheng and Liu, Zhijian},
  journal = {arXiv preprint arXiv:2602.06036},
  year    = {2026}
}

@misc{inco2026dflash2,
  title  = {DFlash 2: Keep Drafting Parallel},
  author = {{Inco AI}},
  year   = {2026},
  month  = {August},
  url    = {https://inco.ai/blog/dflash2/}
}
```
