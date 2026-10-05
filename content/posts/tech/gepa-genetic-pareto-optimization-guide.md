---
title: "GEPA：把「为什么失败」喂回优化循环的反射式进化框架"
date: "2026-04-01T01:04:00+08:00"
lastmod: 2026-09-30
slug: "gepa-genetic-pareto-optimization-guide"
github_repo: "gepa-ai/gepa"
source_key: "gh:gepa-ai/gepa"
description: "GEPA（Genetic-Pareto）用 LLM 阅读执行轨迹来诊断失败原因，替代 RL 的标量奖励：rollout 预算最多省 35 倍，Databricks 用开源模型加 GEPA 以 1/90 成本击败 Claude Opus 4.1。本文拆解其引擎循环、适配器契约与生产案例，并给出采用顺序。"
draft: false
categories: ["技术笔记"]
tags: ["提示词工程", "机器学习"]
---

# GEPA：把「为什么失败」喂回优化循环的反射式进化框架

传统优化器只告诉候选方案"你失败了"，不告诉它为什么。RL 把执行轨迹压缩成一个标量奖励，策略梯度从这个数字里反推方向；而一条失败的轨迹里明明躺着错误消息、推理日志、性能数据——这些信息被整个丢掉了。GEPA（Genetic-Pareto）的出发点是：语言本身就是比标量奖励更丰富的学习介质。它让一个 LLM 去读完整的执行轨迹，用自然语言诊断失败原因，再据此改写提示词，整个循环只花 RL 一小部分的 rollout 预算。

这不是一个提示词润色工具，而是一套通用的文本参数优化框架：提示词、代码、智能体架构、调度策略、SVG 都能优化，只要你的系统能被评估。它在论文的六个任务上平均超过 GRPO 6%（最高 20%），用的 rollout 最多少 35 倍；也超过当时领先的提示词优化器 MIPROv2 十个百分点以上。生产侧更硬的证据是 Databricks 用开源模型加 GEPA 以 1/90 的成本击败了 Claude Opus 4.1，以及 Nubank、Microsoft 等公司在预训练和亿级用户产品里的实际采用。

## 系统地图：一个引擎循环、一个集成点、一种学习信号

在拆机制之前，先分清 GEPA 里三个容易混在一起的东西：

| 组件 | 职责 | 你需要碰它吗 |
|------|------|-------------|
| **优化引擎** | 反射式进化循环：Select → Execute → Reflect → Mutate → Accept | 否，开箱即用 |
| **适配器（Adapter）** | 你的系统与引擎之间的唯一集成点：跑评估、把轨迹变成反射数据集 | 是，核心工作量在这里 |
| **ASI（Actionable Side Information）** | 评估器返回的诊断反馈，充当"文本优化的梯度" | 是，反馈质量决定优化上限 |

引擎循环每轮做五件事：从 Pareto 前沿里选一个候选（不同候选擅长不同任务子集，前沿保证了多样性）；在一个小批量上执行，捕获完整轨迹；让反射 LLM 读轨迹、诊断失败；基于所有祖先累积的教训生成改进候选；如果小批量得分提升就接受，并更新前沿。此外还有一个系统感知合并（system-aware merge）：把两个在不同任务上各自 Pareto 最优的候选的优点合并起来，对应 `gepa.optimize` 里的 `use_merge=True`（默认关闭，最多合并 5 次）。

适配器契约由 `GEPAAdapter` 协议定义，只有两个必须实现的方法：

- `evaluate(batch, candidate, capture_traces)`：用候选方案（组件名到组件文本的映射）跑一批数据，返回一个 `EvaluationBatch`——逐样本输出、逐样本分数，以及 `capture_traces=True` 时逐样本的轨迹。注意返回的不是单一分数：GEPA 对小批量分数求和做接受判定，对全量验证集求平均做前沿追踪。
- `make_reflective_dataset(candidate, eval_batch, components_to_update)`：把轨迹提炼成每个组件一份的 JSON 可序列化数据集，交给反射 LLM 去生成改进文本。

还有一个可选的 `propose_new_texts`，让你用自定义的提案逻辑替换默认的"序列化反射数据集让 LLM 改写"；以及可选的 `get_adapter_state`/`set_adapter_state`，用于断点续跑时保存适配器状态。源码注释里还有一条容易被忽略的契约：单个样本失败时不要抛异常，返回带 0.0 兜底分和错误轨迹的合法 `EvaluationBatch`，把异常留给系统性故障——否则一次解析失败就会炸掉整轮优化。

## 一次优化迭代如何流转

用官方快速开始里最小化的例子走一遍完整流程，看抽象机制怎么配合：

```python
import gepa

trainset, valset, _ = gepa.examples.aime.init_dataset()

seed_prompt = {
    "system_prompt": "You are a helpful assistant. Answer the question. "
                     "Put your final answer in the format '### <answer>'"
}

result = gepa.optimize(
    seed_candidate=seed_prompt,
    trainset=trainset,
    valset=valset,
    task_lm="openai/gpt-4.1-mini",
    max_metric_calls=150,
    reflection_lm="openai/gpt-5",
)

print("Optimized prompt:", result.best_candidate['system_prompt'])
```

这个例子里没有显式传适配器，`gepa.optimize` 会用内置的 DefaultAdapter：`task_lm`（GPT-4.1 Mini）是干活的学生模型，拿 `system_prompt` 逐题作答；`reflection_lm`（GPT-5）是读轨迹改提示词的老师模型。分工很讲究——学生便宜大量跑，老师贵但只在小批量轨迹上调用。

150 次 `max_metric_calls` 预算内，引擎反复执行上面那五步。官方教程的结果：GPT-4.1 Mini 在 AIME 2025 上从 46.6% 提到 56.6%，涨了 10 个百分点。看看 README 里贴出的优化后提示词就能明白涨分从哪来——GEPA 从错误轨迹里学出了一整套竞赛策略：模 9 和模 8 的剪枝恒等式、回文数在八进制下的表示边界、如何避免四项等差数列的重复计数。这些规则不是人写的，是反射循环从"哪道题错了、错在哪一步"里提炼出来的。这就是"预计算推理"：把推理花在优化期，把结论固化成提示词留给未来的任务实例。

如果你想在磁盘上看到这一切，`EngineConfig(write_agent_state=True)` 会让每次迭代（无论接受与否）在 `run_dir` 下写出一个 agent 可读的目录：`iterations/<id>/` 里有 `meta.json`、`components/`、记录前后分数与轨迹的 `trace.json`，被接受的迭代还带验证集分数和输出。调试优化过程时，这个目录树比日志直观得多。

## 数字怎么读：出处、口径与不能推出的东西

GEPA 的传播数字很多，先分清哪些出自论文、哪些出自生产博文：

| 数字 | 出处 | 实际含义 |
|------|------|---------|
| **rollout 最多省 35 倍** | 论文（arXiv:2507.19457） | 100–500 次评估对上 GRPO 的 5,000–25,000+ 次 |
| **平均超 GRPO 6%，最高 20%** | 论文，六个任务 | 语义相同预算下的准确率对比 |
| **超 MIPROv2 十个百分点以上** | 论文 | 如 AIME-2025 提升 12% |
| **成本低 90 倍** | Databricks 博文 | 开源模型 + GEPA 对比 Claude Opus 4.1，企业 agent 任务 |
| **ARC-AGI 32% → 89%** | 官方博客 | 靠 `optimize_anything` 发现智能体架构 |
| **Jinja 解决率 55% → 82%** | 官方博客 | 编码 agent 自动学习技能 |
| **云调度成本省 40.2%** | 官方博客 | GEPA 发现的策略胜过专家启发式 |
| **MATH 67% → 93%** | README | DSPy 全程序进化对基础 ChainOfThought |

三个问题按 benchmark 解读的规矩回答。**测的是什么**：论文六个任务覆盖数学推理、结构化输出等，比的是"给定评估预算，哪种优化方法把准确率推得更高"；90 倍成本那项测的是 Databricks 的企业 agent 任务，对比对象是最强闭源模型的直接使用。**数字反映系统的哪部分**：收益主要来自反射循环的样本效率——每条轨迹都被消化成规则，而不是让梯度在稀疏奖励里碰运气；90 倍里还有一大部分来自"开源小模型 + 好提示词"对"闭源旗舰裸用"的替代。**不能推出什么**：35 倍是评估次数之比，不等于墙钟时间之比（反射 LLM 每轮都要调用，单轮更贵）；六个任务的成绩不能外推到所有任务类型——如果您的评估信号本身噪声很大，或者任务无法低成本自动判分，这些数字帮不上忙；90 倍是特定企业任务上的结果，换个任务倍数会变。

还有一条使用曲线值得注意：README 给出的适用场景清单里，最后一条是"与 RL 互补"——先用 GEPA 快速找到好的初始方案，再上 RL/微调榨取额外收益（论文引用的 BetterTogether 组合，arXiv:2407.10930）。这两者不是替代关系。

## 谁在生产环境用它

README 维护的"50+ 生产使用"清单横跨产业界和学术界，挑几个最能说明问题边界的：

- **Databricks**：开源模型 + GEPA 在企业 agent 任务上击败 Claude Opus 4.1，成本只有 1/90。这是被引用最多的案例，也是"省钱的 GEPA"叙事的源头。
- **Nubank**：一亿用户规模的客服 AI，用 DSPy 内嵌 GEPA 优化 LLM-as-a-Judge 提示词，端到端评估准确率 68.88% → 88.89%，两个模型的评审一致性（Cohen's κ）从 0.00 拉到 0.745；落地收益是 5 个部署领域里 AI 交易 NPS 提升 37 个百分点、自助解决率提升 29 个百分点。
- **Microsoft（MAI-Thinking-1）**：用 GEPA/DSPy 优化 Qwen3-30B 的 LLM-judge 提示词，在预训练管线里过滤 Code 页面——约 233B token 的精选数据背后只有约 2,000 条人工标注。这是"优化器放大少量标注"的极端案例。
- **Google**：Agent Development Kit 的官方优化命令 `adk optimize` 由 GEPA 驱动，同时进了 Gemini Enterprise Agent Platform 的质量飞轮。
- **Shopify**：CEO Tobi Lutke 的评价是"DSPy 尤其是 GEPA 在 AI 语境工程领域被严重低估了"。

学术侧，GEPA 已经频繁作为 baseline 出现在医学 NER、临床笔记纠错、Verilog 生成、Text-to-SQL 等论文里——它正在变成提示词优化这个细分方向的对照标准。

## 上手：三条路径

安装本身没有门槛：

```bash
pip install gepa
# 或跟踪 main 最新版
pip install git+https://github.com/gepa-ai/gepa.git
```

Python 要求 3.10 及以上（3.15 以下），外加任意一个 LLM 提供者——OpenAI、Anthropic、Google 都行，GEPA 全程走 API，不需要模型权重。

**路径一：`gepa.optimize` 直接优化提示词**。就是上一节的 AIME 例子，适合单组件提示词优化，默认走 DefaultAdapter。

**路径二：DSPy 管线内嵌（官方推荐）**。如果你的系统已经用 DSPy 写，`dspy.GEPA` 可以进化整个程序——签名、模块、控制流都在优化范围内：

```python
import dspy

optimizer = dspy.GEPA(
    metric=your_metric,
    max_metric_calls=150,
    reflection_lm="openai/gpt-5",
)
optimized_program = optimizer.compile(student=MyProgram(), trainset=trainset, valset=valset)
```

**路径三：`optimize_anything` 优化任意文本产物**。提示词只是特例，任何"能打分的文本"都行。你提供评估函数，用 `oa.log` 把诊断信息喂回反射：

```python
import gepa.optimize_anything as oa
from gepa.optimize_anything import optimize_anything, GEPAConfig, EngineConfig

def evaluate(candidate: str) -> float:
    result = run_my_system(candidate)
    oa.log(f"Output: {result.output}")      # Actionable Side Information
    oa.log(f"Error: {result.error}")         # feeds back into reflection
    return result.score

result = optimize_anything(
    seed_candidate="<your initial artifact>",
    evaluator=evaluate,
    objective="Describe what you want to optimize for.",
    config=GEPAConfig(engine=EngineConfig(max_metric_calls=100)),
)
```

这段代码的关键在两行 `oa.log`：它们就是 ASI 的入口。评估器返回的不该只有一个分数——输出片段、错误消息、性能数据都会被反射 LLM 读到。`EngineConfig` 还有一个省事的开关 `capture_stdio=True`，自动把你评估函数里的 `print` 输出路由进 ASI，不用改一行代码。

几个值得知道的引擎默认值：并行评估默认开启（`parallel=True`，`max_workers` 默认取 CPU 核数，上限 32），`max_metric_calls` 是最重要的预算旋钮，评估缓存（`cache_evaluation`）默认关闭但可以打开省钱。

顺带一提，GEPA 自己也发布成了 Agent Skill：仓库里的 `.claude/skills/gepa-optimize-anything/` 会被 Claude Code 自动发现（Cursor、VS Code/Copilot、Codex、Gemini CLI 等支持 Agent Skills 的运行时同样适用），也可以装成插件，让编码 agent 替你驱动 `optimize_anything`：

```bash
/plugin marketplace add gepa-ai/gepa
/plugin install gepa-optimize-anything@gepa
```

## 内置适配器与框架集成

自己实现适配器之前，先看看内置的八个能不能直接用：

| 适配器 | 用途 | 安装 |
|--------|------|------|
| **DefaultAdapter** | 单轮 LLM 任务的系统提示词优化 | 内置 |
| **DSPy Full Program** | 进化整个 DSPy 程序（签名、模块、控制流） | 需装 DSPy |
| **Generic RAG** | 向量库无关的 RAG 优化（查询改写、上下文合成、答案生成、重排） | 内置 |
| **MCP Adapter** | 优化 MCP 工具描述与系统提示词，支持本地 stdio 与远程 SSE/StreamableHTTP | 内置 |
| **LangChain** | 任意 LangChain 管线：chat 模型、`create_agent` 工具调用、LangGraph 图 | `pip install "gepa[langchain]"` |
| **ConfidenceAdapter** | logprob 感知的分类优化——从结构化 JSON 输出提取 token 级置信度，惩罚"蒙对的答案" | `pip install "gepa[confidence]"` |
| **TerminalBench** | 优化 Terminus 终端使用智能体 | 内置 |
| **AnyMaths** | 数学问题求解与推理任务 | 内置 |

注意这些适配器都不是无参构造：DefaultAdapter 要传 `model`（LiteLLM 字符串或自定义 chat 函数），DSPy 适配器要传 `task_lm`、`metric_fn`、`reflection_lm`，Generic RAG 要传你的 `vector_store` 实例和模型，MCP 适配器要传工具名、任务模型、评分函数和 `server_params`。具体签名以各自源码为准。

要接入完全自定义的系统，实现 `GEPAAdapter` 的两个必选方法即可。真实的接口长这样（摘自 `src/gepa/core/adapter.py`）：

```python
from gepa.core.adapter import EvaluationBatch, GEPAAdapter

class MyAdapter(GEPAAdapter[DataInst, Trajectory, RolloutOutput]):
    def evaluate(
        self,
        batch: list[DataInst],
        candidate: dict[str, str],
        capture_traces: bool = False,
    ) -> EvaluationBatch[Trajectory, RolloutOutput]:
        ...  # 用 candidate 实例化你的系统，跑一遍 batch，返回逐样本输出/分数/轨迹

    def make_reflective_dataset(
        self,
        candidate: dict[str, str],
        eval_batch: EvaluationBatch[Trajectory, RolloutOutput],
        components_to_update: list[str],
    ) -> Mapping[str, Sequence[Mapping[str, Any]]]:
        ...  # 从轨迹提炼每个组件的反射数据集，格式为 组件名 -> 记录列表
```

框架集成方面，除了 DSPy 和上面提过的 Google ADK，还有：MLflow 的 `mlflow.genai.optimize_prompts()` API 用它做自动提示词改进；Comet ML Opik 的 Agent Optimizer 以它为核心算法；Pydantic AI 官方博客发过集成教程；OpenAI Cookbook 和 HuggingFace Cookbook 各有一份自进化智能体/提示词优化指南。

## 适用边界与采用顺序

四类场景 GEPA 的收益最明确：

- **执行昂贵**：科学模拟、带工具调用的复杂智能体、慢编译——每次评估都肉疼时，100–500 次评估对上万次 RL 的差距是决定性的。
- **数据稀缺**：少到 3 个样本就能开跑，不需要大训练集。
- **只有 API**：GPT-5、Claude、Gemini 都拿不到权重，RL 无从谈起，提示词是唯一可优化的面。
- **需要可解释**：人类可读的优化轨迹说清每处改动的原因，这在需要审计的行业里不是加分项，是准入项。

反过来说，三类情况不必急着上：评估指标本身噪声大或语义不稳定的（反射学到的会是噪声规则）；已有大量数据且能承受 RL 训练成本的（RL 的上限仍然更高，GEPA 更适合当热启动）；任务简单到 MIPROv2 级别的优化器就能收敛的（没必要引入反射循环的额外成本）。

给出一条务实的采用顺序：先用 DefaultAdapter 在一个你已有评估集的任务上跑通最小优化（AIME 官方教程可以照抄结构），确认评估信号质量；然后把同样的模式套到你的真实系统上，评估函数里务必用 `oa.log` 或 `capture_stdio` 喂诊断信息——ASI 的质量直接决定反射的天花板；如果系统在 DSPy/LangChain 上，直接走对应适配器，省掉手写评估封装；优化收益确认后，再考虑是否值得追加 RL/微调，以及是否用 `cache_evaluation` 和检查点把迭代成本压下来。

## 项目速览

写作时数据（2026-09-30，GitHub API 读数）：6,816 Stars / 556 Forks / MIT 协议，2025 年 8 月开源，main 分支持续活跃（最新提交 2026-09-29），累计 885 次提交、45 个 release（PyPI 最新 0.1.4）。语言构成 Jupyter Notebook 约 61%、Python 约 39%——前者主要来自文档与教程笔记本，核心引擎是纯 Python。

论文《GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning》（arXiv:2507.19457）出自 UC Berkeley 团队，一作 Lakshya A Agrawal，作者列表里有 Matei Zaharia、Ion Stoica、Dan Klein、Omar Khattab、Christopher Potts——DSPy 与 Berkeley 系统两组人马的合作产物。实验复现工件在 gepa-ai/gepa-artifact 仓库。

| 资源 | 链接 |
|------|------|
| GitHub | <https://github.com/gepa-ai/gepa> |
| 文档 | <https://gepa-ai.github.io/gepa/> |
| 论文 | <https://arxiv.org/abs/2507.19457> |
| PyPI | <https://pypi.org/project/gepa/> |
| Discord | <https://discord.gg/WXFSeVGdbW> |
