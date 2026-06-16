---
title: "SIA：自我改进 AI 框架，让 Agent 自动改自己的 Harness 与权重"
date: "2026-06-12T15:09:00+08:00"
slug: "sia-hexo-ai-tool-guide"
description: "SIA（hexo-ai/sia）是一个自我改进 AI 框架，让语言模型 Agent 循环改写 harness 与权重。本文拆解三 Agent 协作机制、benchmark 含义与自定义任务接入路径。"
draft: false
categories: ["技术笔记"]
tags: ["SIA", "AI Agent", "自我改进", "Harness更新", "权重更新"]
---

## 学习目标

下面几件事读完应该有答案：

1. 用准确术语解释 SIA（Self-Improving AI）解决的是什么问题，以及它和传统 prompt 工程、Agent 框架的本质区别。
2. 描述 Meta-Agent、Target-Agent、Feedback-Agent 三个角色在一次「代际（generation）」中的协作闭环。
3. 看懂 README 中 `sia run` 与 `sia web` 的关键参数与产物结构，知道一次运行会在磁盘上留下什么。
4. 解释 LawBench、Triton kernel、scRNA-seq 三个 benchmark 数字各自在测什么、不能直接推出什么。
5. 知道如何为 SIA 准备一个自定义任务目录，以及如何基于 MLE-Bench 比赛直接引导出任务。

## 阅读前说明

仓库路径里的 `hexo-ai` 容易让人误以为这是一个 Hexo 博客主题工具，但 SIA 跟 Hexo 没有任何关系，它是一个自我改进 AI 框架，命名只是 hexolabs.com 这家实验室的账号前缀。本文所有事实都来自：

1. 官方 GitHub README 中明确写出的能力、命令与参数。
2. 论文摘要（Hebbar et al., 2026, arXiv:2605.27276）中明确写出的实验结论。
3. 仓库侧栏可以看到的公开数据：1.4k stars、168 forks、MIT 协议、Python 91.9% / HTML 8.1%。

凡是无法在上面三个来源直接确认的细节，文中都会显式标注为「未在 README 中明确说明」或「按一般工程经验推断」。

## 一、一句话理解 SIA

SIA 的目标是用一个语言模型 Agent 反复迭代，自动改进另一个 Agent 在指定基准任务上的表现。这里的「改进」不是只调提示词，而是同时改两件事：

- **Harness**（执行环境、提示模板、工具描述、参数化代码）：决定 Agent「怎么跑」。
- **权重**（通过微调/再训练手段更新的模型参数）：决定 Agent「跑出来什么能力」。

论文中把它叫做 *SIA: Self Improving AI with Harness & Weight Updates*。README 的导语总结得更直接：「SIA is a Self Improving AI framework to autonomously improve the performance of any AI system (Model / Agent) on a benchmark task.」

如果只看 30 秒，可以把 SIA 理解为：

1. 你给 SIA 一个基准任务和一份评估脚本。
2. SIA 在每一代里写一个目标 Agent，让它跑、给它打分。
3. 反馈 Agent 看这一代的失败/成功，改写目标 Agent 的代码或重训它的权重。
4. 跑 N 代后，留下分数最高的目标 Agent 作为「产物」。

## 二、先看系统地图：三个 Agent 与一代的协作

在前 20% 给出一张地图，是分析型文章的基本要求。下表把 README 里散落在三段话里的角色串起来。

| 角色 | 任务来源 | 产物 | 下游消费者 |
|------|----------|------|------------|
| **Meta-Agent** | 任务描述（`data/public/task.md`） | 初始 Target Agent 的代码（首代） | Target-Agent、Feedback-Agent |
| **Target-Agent / Task-Specific Agent** | Meta 写的代码 / 上一代 Target | 执行日志、提交文件 | 评估器、Feedback-Agent |
| **Feedback / Improvement Agent** | Target 的执行日志、评估分数 | 改写后的 Target 代码或权重更新说明 | 下一代 Meta-Agent、下一代 Target |

> 注：SIA 在每一代里有 1 个 Target-Agent，但 Meta-Agent 与 Feedback-Agent 在 README 中按角色分别命名；论文与代码层是否复用同一份模型实例，README 未明确说明，按一般工程经验两者既可共用同一份 profile，也可拆开。

一个最小闭环可以压成三步：

1. **生成**：Meta 看任务描述，吐出第一代 Target Agent。
2. **执行 + 评估**：Target Agent 在公开输入上跑，评估器拿私有标签打分，生成 `results.json`。
3. **改写**：Feedback Agent 读执行日志和分数，改写 Target Agent 的代码（或发起权重更新），产生下一代。

`--max_gen` 控制这个循环跑几代。`--run_id` 决定这次跑的整体目录前缀。默认 `--max_gen=3`，意味着在你没显式调参的情况下，仓库会从首代 + 改两轮 → 留下三份 Target Agent 代码。

## 三、一次任务是怎么流过系统的

抽象的「Meta 生成、Feedback 改写」读起来很顺，但要真正理解 SIA，需要把一次具体任务在磁盘上的产物串起来。下面是 README 给出的目录约定（一次 `sia run --task gpqa --max_gen 5 --run_id 1` 的产物）：

```text
runs/
└── run_1/
    ├── gen_1/
    │   ├── target_agent.py        # 这一代的目标 Agent 代码
    │   ├── agent_execution.json   # 执行轨迹
    │   ├── improvement.md         # gen >= 2 时，反馈 Agent 给的改写说明
    │   ├── submission.csv         # GPQA 类任务的提交文件
    │   └── results.json           # 评估器吐出的分数
    ├── gen_2/
    │   └── …
    └── gen_5/
        └── …
```

把一次 `gpqa` 任务按上面的产物展开，过程大致是：

1. **Meta 读 `task.md`**，按任务包内置的 `reference/reference_target_agent.py` 模板，吐出一个 `target_agent.py` 落到 `gen_1/`。GPQA 这种多选题任务，第一代基本就是「调模型 + 解析选项 + 提交答案」。
2. **Target-Agent 执行**。它读 `data/public/` 里的题目，调用 provider 配置的模型，把答案写到 `submission.csv`。执行细节全部落到 `agent_execution.json`。
3. **评估器运行**。仓库自带 `evaluate.py`，从 `data/private/` 拿标签算指标，写 `results.json`。
4. **Feedback-Agent 介入**。它同时看到 `agent_execution.json`（错题过程）和 `results.json`（总分数），吐出一份 `improvement.md` 解释「为什么这一代错了、下一代怎么改」。
5. **Meta 复用作 Feedback**。在 README 的描述里，Meta-Agent 和 Feedback-Agent 是同一种「上层 Agent」，所以下一代 `target_agent.py` 可以理解为「Meta 拿上一代代码 + 改写说明 + 分数，重新生成」。
6. 循环 5 次后，磁盘上留下 5 份 `target_agent.py`、5 份 `agent_execution.json`、5 份 `results.json`、4 份 `improvement.md`。

Web 可视化器（`sia web`）就是把这些目录读出来画成「跨代准确率曲线、按域拆分、每代代码 diff、执行轨迹」的看板，README 明确说它会在 `sia run` 运行时自动拉起（`http://127.0.0.1:8000`），不需要也行，加上 `--no-web` 即可关掉。

## 四、自定义 Profile：把模型和 Agent 解耦

SIA 的一个工程亮点是「Provider + Profile」两层 JSON 配置，把模型选型从代码里抽出来：

- **Provider** 描述「去哪里调模型、密钥怎么读」：OpenAI 兼容端点、Anthropic、或者 Google 通用协议都行。
- **Profile** 描述「一个角色用哪个模型、哪个 provider、哪份 agent_reference」：Meta 和 Target 可以各持一份 profile。

```jsonc
// providers/my-endpoint.json
{
  "provider_id": "my-endpoint",
  "name": "My Endpoint",
  "client_kind": "openai",           // anthropic | openai | google
  "base_url": "https://api.example.com/v1",
  "api_key_env": "MY_ENDPOINT_API_KEY"
}

// profiles/my-target.json
{
  "profile_id": "my-target",
  "name": "My model on My Endpoint",
  "model": "vendor/my-model",
  "provider_id": "my-endpoint",
  "agent_reference": "default"        // 或 { "source": "./my_agent_dir/", "entrypoint": "main.py" }
}
```

这种解耦带来的一个直接好处是：同一个目标 Agent 框架可以在不同模型之间换着用。例如 README 给出的官方示范是用 Kimi-K2.6 在 Nebius 上当 Target：

```bash
export NEBIUS_API_KEY="..."      # + ANTHROPIC_API_KEY for the default meta agent
sia run --task gpqa --target-agent-profile kimi-nebius-target --max_gen 5 --run_id 2
```

Meta-Agent 默认走 Claude Agent SDK（`pip install 'sia-agent[claude]'`），所以 Meta 默认绑定 Anthropic。如果想让 Meta 也走多 provider，需要切到 OpenHands 后端（`pip install 'sia-agent[openhands]'`），这一限制 README 已经写明。

## 五、Benchmark 解读：先看测的是什么，再看数字

README 列了四个 benchmark，每个数字都需要带着「测的是哪部分 SIA」这个视角去看，否则容易把不同来源的百分比拼成同一句话。

### 5.1 OpenAI MLE-Bench Hard

- **测什么**：真实 Kaggle 机器学习比赛任务，Agent 要写、跑、迭代完整 ML pipeline。
- **SIA 的角色**：README 只写「SIA ranks #1 across all generations tested」，没有给出对照基线。
- **不能直接推出什么**：单看 #1 无法反推「改 harness」和「改权重」各自贡献了多少，也没法判断是模型选型还是 harness 优化的功劳。

### 5.2 LawBench（191 个罪名分类）

- **测什么**：根据中文法院判决书预测罪名。
- **数字**：SIA-W+H 达到 70.1% Top-1 准确率；论文摘要里写相对基线有 56.6% 提升（这是「相对提升」，不是绝对值），基线 SOTA 是 45%。
- **能推出什么**：在这个高度结构化的中文法律分类任务上，Harness + Weight 同时更新带来的增益明显。
- **不能直接推出什么**：191 类罪名分类不代表跨法律子任务都好；中文文本的提升幅度也不能直接迁移到英文长尾任务。

### 5.3 AlphaFold-3 TriMul Triton Kernel

- **测什么**：把 Triangle Multiplicative Update 实现成 Triton kernel，同时要正确、要快（H100 延迟目标）。
- **数字**：SIA-W+H 达到 14× 速度提升。
- **能推出什么**：在「写算子 + 调优」这类强反馈循环里，反馈 Agent 拿真实延迟作为奖励信号，可以把 kernel 写出比人工参考更优的版本。
- **不能直接推出什么**：14× 是相对 SIA 自带参考实现而言（README 没有说对照是谁），不是相对 cuBLAS/PyTorch 内核；且只覆盖了 AlphaFold-3 的一个子算子。

### 5.4 scRNA-seq Denoising

- **测什么**：填补单细胞 RNA 测序中的缺失基因表达值。
- **数字**：SIA-W+H 给出 0.289 的 MSEnorm（越低越好），超过 SOTA 0.220。
- **能推出什么**：在一个传统上靠领域知识手工调模型的任务里，自我改进循环也能找到超过 SOTA 的方案。
- **不能直接推出什么**：MSEnorm 只是去噪任务里的一项指标，跨数据集泛化、跨细胞类型表现、生物学下游分析的有效性，README 都没有给出。

> 通用结论：上面四组数字共同支撑「SIA 在多类任务上跑得通」，但「权重 + harness」两个更新机制各自贡献了多少，需要在论文层做消融才能确认，README 没有直接说。

## 六、接一个自定义任务：什么时候用 SIA、什么时候不必

README 把「自定义任务」做成三步走：

1. **准备一个任务目录**：

   ```text
   my-task/
   ├── data/
   │   ├── public/
   │   │   ├── task.md           # SIA 读这个文件
   │   │   └── …                 # 允许 Agent 看到的输入
   │   └── private/              # 私有评估数据，Agent 永远看不到
   └── reference/
       ├── reference_target_agent.py
       └── SAMPLE_TASK_DESCRIPTIONS.md  # 可选：给 Meta-Agent 的示例任务
   ```

2. **写一个 `evaluate.py`**：暴露 `evaluate()` 函数，决定提交文件格式，对照 `data/private/` 评估，返回一个指标字典。
3. **跑起来**：

   ```bash
   sia run --task_dir ./my-task --max_gen 5 --run_id 1
   ```

如果你懒得自己写任务目录，README 还提供了一个 MLE-Bench 自动引导入口：

```bash
python -m sia.prepare_mlebench_dataset -c "spaceship-titanic"
sia run --task_dir ./tasks/spaceship-titanic --max_gen 5 --run_id 1
```

这个工具会通过 Kaggle API 拉数据集、拆 public/private、把参考 Agent 模板放进 `reference/`，然后就可以直接 `sia run`。

### 什么时候该用 SIA

- 你有一个**有量化评估**、**有 held-out 测试集**的明确任务（分类、回归、检索质量、kernel 性能、imputation 指标等）。
- 提示词工程或一次性的 Agent 框架调优**已经触到天花板**。
- 你愿意提供多代（README 默认建议 ≥3 代）的 API 预算，并且接受反馈 Agent 改写 Agent 后需要人工巡检产物。

### 什么时候不必用 SIA

- 任务缺乏可计算的评估信号（典型如开放式创意写作、主观审美）。
- 数据集太小，Feedback-Agent 没有稳定反馈（建议评估样本 ≥ 几百条，再考虑多代迭代）。
- 评估指标里存在「越优化越糟」的反向激励（比如过度拟合私有集），这种情况 SIA 的「分数上升」很可能只是反馈循环放大了过拟合。

## 七、采用顺序与决策建议

把上面的内容压成一条上手顺序，按这条路径走可以最大程度避免被 README 的功能列表淹没：

1. **先用 CLI 跑通一个内置任务**：`pip install 'sia-agent[claude]'` → `export ANTHROPIC_API_KEY` → `sia run --task gpqa --max_gen 3 --run_id 1`。这一步只验证「循环能跑、产物会落盘、Web 看板能打开」。
2. **看 `runs/run_1/` 下的产物**：重点看 `agent_execution.json` 和 `improvement.md`，确认 Feedback-Agent 给出的「改写理由」是不是你想要的语义颗粒度。
3. **准备自定义任务目录**：先写一个最简 `evaluate.py`，用一两个例子试通评估回路，再补 `task.md` 和 `data/public/`。
4. **profile 化模型**：把 Meta 拆出去走 OpenHands 后端，Target 走自定义 provider/模型，对比「同 harness 不同模型」与「同模型不同 harness」的代际曲线。
5. **决定是否启用权重更新**：SIA-W+H 的 SOTA 提升主要来自 harness + 权重一起动；只改 harness（README 提到的 SIA-H 形态）会更便宜，但提升幅度也更低，按预算和监管要求取舍。

如果你只是想要一个会自己改 prompt 的 Agent，先看 `text-matrix` 上其他更轻量的工具；如果你想要一个会自己改自己代码、并且把每代差异和分数都落盘的实验台，SIA 现在的产物结构已经能直接接住这种需求。

## 八、结尾判断：SIA 的真实价值不是「自我改进」四个字

去掉所有形容词后，SIA 在工程上做的事情其实是三件：

1. 把「生成目标 Agent」和「评估目标 Agent」拆成两个独立角色，让反馈信号进入下一轮生成。
2. 把模型、provider、Agent 角色、参考实现这四类信息压成 JSON profile，让一次实验可以在「同一份 harness、不同模型」与「同一份模型、不同 harness」之间切换。
3. 把每代产物（代码、执行日志、改写说明、分数）落到一个固定目录结构上，让多代对比、失败回放和权重更新可以追溯。

它解决的问题不是「让 AI 自我进化」这种泛化口号，而是「在评估信号存在的前提下，把多 Agent 迭代这件事变成可观测、可回放、可换模型的工程流程」。论文里 56.6% / 14× / 502% / 70.1% 这些数字，是这种工程流程在四类不同任务上的副作用，而不是它存在的理由。

如果你打算评估 SIA 是否值得进入你自己的 pipeline，建议从「评估信号是不是已经准备好」和「能不能接受每代重新训练 / 重新生成代码的成本」这两个问题开始，而不是从「SIA 听起来多强」开始。

## 进一步阅读

- 官方 README：仓库首页 `README.md`
- 仓库文档目录：
  - `docs/architecture.md` — 目录布局、代际流转、提示词定制
  - `docs/walkthrough.md` — 自定义任务逐步走通
  - `docs/configuration.md` — Agent 实现、模型、API key、CLI 完整参考
  - `EVALUATION_GUIDE.md` — 为自定义任务写 `evaluate.py`
  - `docs/troubleshooting.md` — 常见报错与修复
- 论文：Hebbar et al., 2026, *SIA: Self Improving AI with Harness & Weight Updates*, arXiv:2605.27276
