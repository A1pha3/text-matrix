---
title: "SIA（Self-Improving AI）：同时改 harness 和权重的自改进 Agent 框架"
date: "2026-06-12T21:08:43+08:00"
slug: "sia-self-improving-ai-harness-weights"
description: "SIA 是 hexo-ai 开源的自改进 AI 框架，由 Meta / Target / Feedback 三类 Agent 协同组成生成循环，同时更新 harness（提示词 + 工具装配）和 weight（模型参数）。论文在 LawBench 拿到 70.1% Top-1、MLE-Bench Hard 取得 14× Triton kernel 加速和 502% 单细胞 RNA 去噪改进。本文拆解其双轴更新机制、四类内置任务、Profile 配置和评估管线。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "自改进", "Harness Engineering", "Benchmark", "OpenHands"]
---

# SIA（Self-Improving AI）：同时改 harness 和权重的自改进 Agent 框架

> **目标读者**：在跑 Agent benchmark、调 Agent harness 提示词、想理解"权重 + 提示词双轴微调"的研究者 / 工程师
> **核心问题**：能不能让一个 Agent 在没有人类重写 prompt 的情况下，靠自己**同时调 harness（提示词 / 工具装配）和 weight（模型微调）**两轴，把 benchmark 分数单调推上去？
> **难度**：⭐⭐⭐⭐（需要熟悉 Agent 框架 + benchmark 评估管线 + LLM 微调）
> **来源**：GitHub [hexo-ai/sia](https://github.com/hexo-ai/sia)，MIT / Python 3.11+ / 论文 arXiv:2605.27276

---

## 一、核心判断

SIA 不是一个"prompt 进化器"，也不是"模型微调脚本"，而是**把 harness 演进和 weight 演进拼成同一条生成管线**的自改进 Agent 框架。

- 它把"自改进"切成两条**正交**通道：H 通道（改 prompt / 工具装配 / 执行循环）和 W 通道（直接微调 Target 模型权重）。论文在 LawBench / MLE-Bench Hard / TriMul CUDA / scRNA-seq denoising 四类任务上分别独立报告了 H-only、W-only 和 W+H 的结果——SOTA 都由 W+H 拿到。
- 它用**三类 Agent 协同**的循环取代了"单 Agent + reflection"模式：Meta-Agent 读 `task.md` 写初始 Target Agent；Target Agent 跑任务、留下 `agent_execution.json`；Feedback Agent 读执行轨迹 + 评估分，决定**改 harness 还是改 weights**。
- 它把"评估"做成框架一等公民：每代结束 `evaluate.py` 跑出 `results.json`，分数字段直接被注入下代 Feedback 的 prompt。这意味着**自改进的"标量奖励"是真的标量**，不是 LLM 自评。

这三件事的合成效果是：仓库既能当 **MLE-Bench 排行榜刷分器**（用户场景），也能当**自改进研究底座**（研究者场景）——这是它和 Reinforce / Self-Refine / Reflexion 等单点方案最大的差别。

---

## 二、系统地图

### 2.1 三类 Agent 的职责切分

SIA 的生成循环靠三种角色跑出增量，每代都跑一遍：

| 角色 | 触发时机 | 职责 | 产物 |
| --- | --- | --- | --- |
| **Meta-Agent** | 第 1 代开始 | 读 `data/public/task.md`，基于 task 包自带的 `reference_target_agent.py` 写出初代 Target Agent | `gen_1/target_agent.py` |
| **Target / Task-Specific Agent** | 每代 | 跑任务（最多 `--max_gen` 次自改进代），留下动作 / 结果 / 异常日志 | `agent_execution.json` |
| **Feedback / Improvement Agent** | 每代结束 | 读执行轨迹 + `results.json`，决定改 prompt / 工具装配 / 权重增量训练 | `improvement.md`（从 gen 2 开始） |

> **关键点**：Meta 和 Feedback 是同一类模型的不同 prompt，**目标函数不同**——Meta 求"在零样本下写出能跑的 Target"，Feedback 求"在看到结果后定位失败模式"。论文里 Feedback 既能直接调 prompt（H 通道），也能产出 LoRA / SFT 训练数据丢给 W 通道的微调器。

### 2.2 H 通道 vs W 通道：什么叫"两轴"？

| 通道 | 作用对象 | 改动粒度 | 触发条件 | 论文信号 |
| --- | --- | --- | --- | --- |
| **H 通道（Harness）** | Target Agent 的 prompt、工具调用循环、retry 策略、文件 I/O 约定 | 离散、文本级 | Feedback 判定"prompt / 工具装配不合理" | LawBench +56.6% Top-1（W+H 70.1%） |
| **W 通道（Weights）** | Target 模型自身的参数 | 连续、参数级 | Feedback 判定"模型本身知识 / 行为不够" | scRNA-seq denoising +502% MSE_norm（0.220 → 0.289） |

H 和 W **不是互斥而是叠加**的。论文实验分别跑了 SIA-H、SIA-W、SIA-W+H，W+H 在四类任务上**全部 SOTA**。这意味着：harness 演进挖的是"这个 prompt 让不让模型把答案写对"，weight 演进挖的是"模型自己有没有这个能力"。

### 2.3 仓库结构

```
sia/
├── sia/
│   ├── cli.py                 # sia run / sia web 入口
│   ├── orchestrator.py        # 三 Agent 协调 + 代际调度
│   ├── feedback.py            # Feedback Agent prompt + 决定 H / W 的策略
│   ├── evaluation.py          # 跑 evaluate.py 收集 metrics
│   ├── defaults/
│   │   ├── providers/         # 内置 provider 配置（OpenAI / Anthropic / Google / 自定义）
│   │   └── profiles/          # 内置 profile（default-meta、default-target、kimi-nebius-target …）
│   ├── tasks/                 # 4 个内置任务
│   │   ├── gpqa/
│   │   ├── lawbench/
│   │   ├── longcot-chess/
│   │   └── spaceship-titanic/ # Kaggle 比赛数据集
│   └── prepare_mlebench_dataset.py  # 把 MLE-Bench 比赛转成 task dir
├── docs/
│   ├── architecture.md        # 目录 / 调度 / 自定义 prompt
│   ├── walkthrough.md         # 自定义任务走查
│   ├── configuration.md       # agent_impl / model / API key
│   └── troubleshooting.md
└── EVALUATION_GUIDE.md        # evaluate.py 契约
```

`runs/run_{run_id}/gen_{n}/` 是每次运行的产物目录，**全自包含**：

```
runs/run_1/gen_3/
├── target_agent.py             # 这一代 Target 的源码
├── agent_execution.json        # 调用轨迹
├── results.json                # evaluate.py 出的 metrics
├── improvement.md              # gen ≥ 2 才有：Feedback 的修改理由
├── context.md                  # 注入给下代 Feedback 的上下文
└── submission.csv              # 任务实际输出（Kaggle 任务里就是提交文件）
```

---

## 三、一个真实任务流：从"零"跑到"W+H SOTA"

下面用论文里的 **LawBench** 任务，把"三 Agent + 两轴"串成一条可复现的剧本。

### 3.1 任务定义（task.md 摘要）

LawBench 任务要求 Target Agent 阅读中国法院刑事判决书，预测 191 个罪名之一。`data/public/task.md` 里只写了输入路径 / 输出 schema / 评估指标（Top-1 / Top-5 准确率），不含答案。

### 3.2 Gen 1：Meta-Agent 写 Target

```bash
sia run --task lawbench --max_gen 5 --run_id 1
```

- Meta-Agent 收到 `task.md` 后，拷贝 `sia/tasks/_shared/reference_target_agent.py` 作为模板
- 改写为：先把判决书分块 → 用 LLM 提取"行为 / 法条引用 / 量刑情节" → 路由到 191 类分类器 → 投票
- 产物：`runs/run_1/gen_1/target_agent.py`

### 3.3 Gen 1：Target 跑 + 评估

Target 在 `data/public/` 跑预测，写到 `gen_1/submission.csv`；orchestrator 触发 `evaluate.py --gen-dir gen_1/`，对比 `data/private/` 拿到 `results.json`（如 `top1=0.42, top5=0.71`）。

### 3.4 Gen 1→2：Feedback 决定改哪条轴

Feedback Agent 读 `agent_execution.json` + `results.json`：

- 看 `agent_execution.json` 发现 38% 的失败集中在"无法识别'共同犯罪'情节"——属于**模型知识盲点**
- 决定走 **W 通道**：用这 38% 失败案例构造 LoRA 训练数据，微调 Target 模型
- 同步小幅改 H：调整分块策略让"共同犯罪"那段不被截断
- 写 `improvement.md`："38% 失败路径集中在共同犯罪识别，W 通道注入 1200 条人工标注样本，H 通道把分块窗口从 4k 提到 6k。"

### 3.5 Gen 2→N：循环继续

每代都是 `Target 跑 → 评估 → Feedback 决定 H/W/W+H → 写 improvement.md` 的闭环。`sia web` 会在 `127.0.0.1:8000` 起一个 dashboard，把每代的 `target_agent.py` 源码、improvement 计划、accuracy-across-generations 折线图、per-domain 细分都摆出来。

最终 W+H 在 LawBench 拿到 **70.1% Top-1**（论文报告基线 45%，H-only 56.6%）。

---

## 四、Benchmark 解读：测的是什么、不能推什么

论文在四类任务上分别跑了基线、SIA-H、SIA-W、SIA-W+H。逐项拆：

| 任务 | 测的是什么 | 报告数字 | 解释边界 |
| --- | --- | --- | --- |
| **MLE-Bench Hard** | 真实 Kaggle ML 比赛，要求完整 ML pipeline（数据清洗 / 建模 / 调参 / 提交） | SIA 在 5 代内 #1 across all generations | 测的是"端到端 ML 工程能力"；不能推出"在 SOTA 学术 benchmark 上同样能赢" |
| **LawBench**（罪名预测） | 191 类中国法院刑事判决书罪名分类 | SIA-W+H Top-1 70.1%（基线 45%，H-only 56.6%，W-only 64.3%） | 数字显示 H 和 W 都有贡献，**H 和 W 的增益不可互相替代**；但样本量是 191 类长尾，Top-5 涨幅小说明 W 在罕见类目上拉得动 |
| **TriMul CUDA**（AlphaFold-3 Triton Kernel） | 在 H100 上实现并优化 Triangle Multiplicative Update | 14× 加速 vs baseline | 测的是"模型写 CUDA / Triton 的能力 + 是否会写 perf benchmark"；不能推出"在 AMD GPU / 国产 NPU 上一样" |
| **scRNA-seq denoising** | 单细胞 RNA 测序缺失值填充 | MSE_norm 0.289（W+H）vs 0.220（SOTA） | W+H **反向跑赢**这个 SOTA——说明 W 通道在"模型本身不会的事"上能补上。**但 denoising 不是纯生成任务**，H 通道的提升很小，反推出 SIA 的 H 通道主要价值在生成 / 决策类任务 |

**几条不能从论文直接推出的结论**：

- 不能推出"在任意自定义任务上 SIA-W+H 都会 SOTA"——论文里任务包都自带 `reference_target_agent.py`，自带 `evaluate.py`，自带打分逻辑。如果任务**没有明确标量奖励**，Feedback 决定 H/W 的策略会失效。
- 不能推出"SIA 的 H 通道 ≈ Self-Refine / Reflexion"——SIA 的 H 通道是**结构化改写**（改 prompt + 改工具装配 + 改 retry 拓扑），不是单点反思。
- 不能推出"W 通道就是 LLM 微调"——Feedback Agent 决定**微什么数据 + 怎么 LoRA**，框架本身不绑死一种微调器。

---

## 五、Profile 与 Provider：可拆可换的最小配置

SIA 把"哪个模型 + 哪个 endpoint + 哪类 agent 跑哪个角色"全收敛到 JSON：

```jsonc
// providers/my-endpoint.json
{
  "provider_id": "my-endpoint",
  "name": "My Endpoint",
  "client_kind": "openai",                 // anthropic | openai | google
  "base_url": "https://api.example.com/v1",
  "api_key_env": "MY_ENDPOINT_API_KEY"
}
```

```jsonc
// profiles/my-target.json
{
  "profile_id": "my-target",
  "name": "My model on My Endpoint",
  "model": "vendor/my-model",
  "provider_id": "my-endpoint",
  "agent_reference": "default"             // task 包的参考实现 / 自定义目录
}
```

```bash
export MY_ENDPOINT_API_KEY="..."
sia run --task gpqa --target-agent-profile my-target
```

Meta / Target 可以**用不同 agent_impl**（`openhands` / `claude` / `pydantic-ai`）。`claude` 实现是 Anthropic-only，OpenHands 实现支持 Gemini / OpenAI / Anthropic。

> Profile + Provider 解耦的好处是：跑 `kimi-nebius-target` 这样的内置 profile，**不必改任何 Python 代码**就能切 target 模型；Meta / Feedback 用强模型（如 Claude Opus），Target 用弱模型（如 Kimi-K2.6）做"成本对冲"是论文里推荐的玩法。

---

## 六、评估管线的契约

每代结束 orchestrator 自动跑：

```bash
python evaluate.py --gen-dir runs/run_1/gen_1
```

自定义任务只要在 `data/public/evaluate.py` 暴露一个 `evaluate(gen_dir) -> dict` 函数即可。返回的 dict 会被：

1. 写到 `gen_1/results.json`（被 `sia web` dashboard 拉成 accuracy-across-generations 折线图）
2. 注入到下代 Feedback 的 prompt，作为"上一代分数"字段
3. 通过 `improvement.md` 的 frontmatter 关联到 `context.md`，用于跨代上下文拼接

**评估函数的契约核心**：

| 约束 | 含义 |
| --- | --- |
| 输入 | `--gen-dir` 路径，里面应有 `submission.csv` 或约定的输出文件 |
| 输出 | 任意 dict，但**至少有一个数值字段**作为主分数（论文里叫 `primary_metric`） |
| 不允许的副作用 | 读 `data/private/` 之外的数据；写 `runs/` 之外的文件 |
| 必须可独立运行 | `python evaluate.py --gen-dir <gen>` 单独跑通，方便调试 |

这条契约的好处是：**自改进循环的"奖励"完全来自 evaluate.py，不来自 LLM 自评**——这是论文和很多"reflection-based"工作最大的方法学差异。

---

## 七、适用边界与决策建议

### 7.1 什么时候用 SIA

- 你手上有**可量化的标量奖励**（benchmark 排行榜、Kaggle 比赛、内部评测集），且愿意为它写 `evaluate.py`
- 你的任务对 Target Agent 的能力是**端到端、长链路**的（ML 比赛、代码生成、决策制定）
- 你愿意接受**生成 N 代 × 每代 LLM 推理 + 可能的微调**的计算开销
- 你想**研究 harness 演进 vs weight 演进的相对贡献**

### 7.2 什么时候不要用

- 你的任务没有"对 / 错"标量，只有"用户满意"——SIA 没有 RLAIF / 偏好建模那一套
- 你的任务样本量太小（每代少于 100 例），Feedback 决定 H/W 的统计信号不够
- 你想跑"单 Agent + 短期反思"——用 Self-Refine / Reflexion 就够，SIA 太重
- 你的任务**长上下文推理**（如 100k+ token 单题）——SIA 默认 chunking 不一定合适，得自己写 Target

### 7.3 采用顺序建议

1. **先用内置任务跑通**：`gpqa` / `longcot-chess` 是单机几分钟级，`lawbench` / `spaceship-titanic` 需要外部数据
2. **用 OpenHands 实现开跑**（多 provider），`claude` 实现是 Anthropic-only 路径
3. **写自己的 `evaluate.py`**：哪怕只跑 5 个样本，能让 Feedback 拿到标量就行
4. **先看 H-only 是不是够了**：论文里 H-only 在不少任务上已经能到基线的 1.2×，W 通道**贵且不一定总是更优**
5. **W 通道慎重上**：先确认 H 通道的 improvement 理由稳定，再开 LoRA / SFT 训练循环

---

## 八、引用

```bibtex
@article{hebbar2026sia,
  title   = {SIA: Self Improving AI with Harness \& Weight Updates},
  author  = {Hebbar, Prannay and Manawat, Yogendra and Verboomen, Samuel
             and Ivanova, Alesia and Palanimalai, Selvam and Bhatia, Kunal
             and Baskaran, Vignesh},
  journal = {arXiv preprint arXiv:2605.27276},
  year    = {2026},
  url     = {https://arxiv.org/abs/2605.27276}
}
```

---

## 九、参考链接

- 仓库：<https://github.com/hexo-ai/sia>
- 论文：<https://arxiv.org/abs/2605.27276>
- 架构文档：<https://github.com/hexo-ai/sia/blob/main/docs/architecture.md>
- 自定义任务走查：<https://github.com/hexo-ai/sia/blob/main/docs/walkthrough.md>
- 评估契约：<https://github.com/hexo-ai/sia/blob/main/EVALUATION_GUIDE.md>
- 排错手册：<https://github.com/hexo-ai/sia/blob/main/docs/troubleshooting.md>
