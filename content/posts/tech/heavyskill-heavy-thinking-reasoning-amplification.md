---
title: "HeavySkill 完全指南：测试时 Scaling 的推理增强技术"
date: "2026-05-06T18:19:57+08:00"
slug: "heavyskill-heavy-thinking-reasoning-amplification"
description: "HeavySkill 通过并行推理 + 顺序深思两阶段架构，将复杂推理任务分解为 K 条独立推理轨迹与关键分析合成。GitHub 13 Stars，新型测试时 Scaling 技术，支持 Claude Code Skill 与 Python Pipeline 两种使用模式。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "LLM", "推理增强", "测试时Scaling", "Agent", "Claude Code"]
---

# HeavySkill 完全指南：测试时 Scaling 的推理增强技术

> **难度**：⭐⭐⭐⭐ | **类型**：专家设计 | **更新日期**：2026-05-06 | **预计阅读时间**：25 分钟
>
> **目标读者**：AI 研究者、LLM 应用开发者、Agent 系统架构师
>
> **前置知识**：了解 LLM 基本原理、Chain-of-Thought 推理、Agent 概念

---

## 背景与问题动机

### 简单推理的局限性

传统大语言模型推理采用单链式思维（Chain-of-Thought，CoT），即模型一次性生成完整的推理链条。这种方式存在几个根本性缺陷：

**错误级联**：推理早期的一个错误会传播到整个链条，导致最终答案完全错误。由于模型在生成过程中无法回头修改已经输出的内容，错误一旦发生就无法纠正。

**认知盲区**：单一推理路径意味着模型只能探索解空间的一个局部。当正确解法需要「换一种思路」时，单链推理无法提供这种灵活性。

**置信度缺失**：单链推理不提供答案的置信度信息。在需要可靠性的场景（如代码竞赛、数学证明），无法判断当前答案是否可信。

### 现有解决方案的不足

**Best-of-N（多数投票）**：生成 N 个独立答案，选择出现次数最多的作为最终答案。多数投票假设「正确答案更容易被多次生成」，但这在推理任务中往往不成立——正确答案可能只有一条，而错误答案有无数种。

**Pass@N**：允许 N 次生成尝试中只要有一次成功即算通过。这需要多次独立运行，成本高昂，且没有真正利用多次推理的多样性来提升推理质量。

**Self-Consistency**：对 CoT 的改进，通过采样多条推理路径并聚合。但多数投票的聚合方式丢失了推理过程中的关键信息，无法进行真正的「深思」。

HeavySkill 的核心创新在于：不只是生成多条推理轨迹，而是通过**顺序深思（Sequential Deliberation）**对所有轨迹进行批判性分析，从而产生真正优于任何单条轨迹的合成答案。

---

## 核心原理：两阶段推理架构

HeavySkill 将复杂推理分解为两个阶段：

```
┌─────────────────────────────────────────────────────────┐
│                      用户查询                            │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│            阶段一：并行推理（Parallel Reasoning）          │
│                                                         │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐    ┌──────┐  │
│   │ 思考者 1 │ │ 思考者 2 │ │ 思考者 3 │ ... │  K   │  │
│   └────┬─────┘ └────┬─────┘ └────┬─────┘    └──┬───┘  │
│        │             │             │             │      │
└────────┼─────────────┼─────────────┼─────────────┼──────┘
         │             │             │             │
         ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────┐
│                    轨迹记忆缓存                          │
│         （存储和组织 K 条推理轨迹）                        │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│          阶段二：顺序深思（Sequential Deliberation）      │
│                                                         │
│   - 分析答案在不同轨迹中的分布                             │
│   - 跨轨迹交叉验证推理链                                   │
│   - 识别逻辑错误与正确方法                                 │
│   - 通过批判性思考合成最终答案                             │
│                                                         │
│              ┌─── 迭代更新（可选） ◄──┐                  │
│              └───────────────────────────────────┘      │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                    最终答案                               │
└─────────────────────────────────────────────────────────┘
```

### 阶段一：并行推理

第一阶段生成 K 条完全独立的推理轨迹。每条轨迹由一个独立的「思考者」生成：

```python
async def parallel_reason(
    query: str,
    config: HeavySkillConfig,
    agent: OpenAICompatibleAgent = None,
) -> List[str]:
    """生成 K 条独立的推理轨迹"""
    trajectories = await agent.generate(
        prompt=query,
        n=config.reason_k,  # K 值：并行轨迹数量
        temperature=config.reason_temperature,
        max_tokens=config.reason_max_tokens,
        top_p=config.reason_top_p,
    )
    # 过滤掉重复/退化的回答
    valid = [t for t in trajectories if not duplication(t, think_end_tag)]
    return valid
```

**关键设计**：
- 温度采样确保轨迹多样性
- 过滤机制剔除重复内容（使用 `duplication()` 函数检测复读/截断）
- 完全独立的生成过程，无信息泄露

**K 值的权衡**：
- K 越大，轨迹多样性越高，深思阶段可用的信息越丰富
- K 越大，计算成本线性增长
- 推荐：Workflow 模式 K=8+，Claude Code Skill 模式 K=3~5

### 阶段二：顺序深思

第二阶段对所有轨迹进行批判性分析，合成最终答案：

```python
async def deliberate(
    query: str,
    cache: MemoryCache,
    config: HeavySkillConfig,
    agent: Optional[OpenAICompatibleAgent] = None,
    trajectory_selection: str = "max_diversity",
) -> List[str]:
    """对推理轨迹进行批判性分析"""
    # 从缓存中选择轨迹（支持多种选择策略）
    selected = cache.select(k=config.reason_k, strategy=trajectory_selection)

    # 如果超出 token 预算，进行截断
    selected = clip_trajectories(selected, config.max_trajectory_tokens)

    # 构建深思提示词
    prompt = build_summary_prompt(
        query=query,
        trajectories=selected,
        prompt_type=config.prompt_type,
        language=config.language,
    )

    # 生成 summary_k 个深思输出
    summaries = await agent.generate(
        prompt=prompt,
        n=config.summary_k,
        temperature=config.summary_temperature,
        max_tokens=config.summary_max_tokens,
    )
    return summaries
```

**深思的核心逻辑**（来自实际 prompts.py）：

1. **答案分布分析**：哪些答案出现了？频率如何？
2. **推理质量评估**：哪些推理链逻辑严密？哪些有缺陷？
3. **交叉验证**：不同方法是否指向同一结果？
4. **批判性评估**：
   - 多数共识是信号但不是正确答案的证明
   - 少数派答案若有严谨逻辑支撑，可能是正确的
   - 所有轨迹都可能出错——准备好重新推理
5. **合成最终答案**：基于分析产生最优答案

**深思不是投票**：不简单地选择多数答案，而是真正分析推理质量。

### 迭代增强（可选）

对于极困难的问题，可进行迭代深思：

```
迭代 1：Stage 1 (K条) + Stage 2 (深思) → 得出深思结果
迭代 2：将深思结果作为新的「专家思考者」加入轨迹集 → Stage 2 重新深思
迭代 3：重复...
```

典型场景下 2-3 次迭代即可收敛。

---

## 项目架构与代码分析

### 整体目录结构

```
HeavySkill/
├── workflow/                    # 核心 Python 异步流水线
│   ├── __init__.py
│   ├── pipeline.py             # 完整流程编排
│   ├── deepthink_workflow.py    # 高级研究实验工作流（57KB）
│   ├── parallel_reasoning.py    # 阶段一：并行推理
│   ├── sequential_deliberation.py  # 阶段二：顺序深思
│   ├── memory_cache.py         # 轨迹存储与选择
│   ├── prompts.py              # 提示词模板
│   ├── config.py               # 配置数据类
│   ├── utils.py                # 工具函数
│   └── agent/
│       ├── base.py             # 抽象 Agent 接口
│       ├── openai_compatible.py  # OpenAI 兼容异步 API 客户端
│       ├── vllm.py             # vLLM 专用 Agent
│       └── api.py              # 通用 API Agent
├── scripts/
│   ├── run_heavyskill.py       # CLI 入口
│   ├── run_heavyskill.sh        # 示例脚本
│   └── evaluate.py             # 准确率评估脚本
├── skill/
│   └── heavyskill.md           # Claude Code Skill 提示词
├── examples/
│   └── example_math.json        # 示例输入数据
├── paper/
│   └── heavyskill.pdf           # 论文
├── requirements.txt
└── pyproject.toml
```

### 核心模块分析

#### HeavySkillConfig（config.py）

完整的配置数据类：

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class HeavySkillConfig:
    # Model
    model_name: str = "default"
    api_base: str = "http://localhost:8080"
    api_key: str = "EMPTY"

    # Stage 1: Parallel Reasoning
    reason_k: int = 8
    reason_temperature: float = 1.0
    reason_max_tokens: int = 32768
    reason_top_p: float = 0.95

    # Stage 2: Sequential Deliberation
    summary_k: int = 4
    summary_temperature: float = 0.7
    summary_max_tokens: int = 32768
    summary_model_name: Optional[str] = None
    summary_api_base: Optional[str] = None
    summary_api_key: Optional[str] = None

    # Memory & Selection
    max_trajectory_tokens: int = 128000
    trajectory_selection: str = "max_diversity"
    iterations: int = 1
    language: str = "en"
    prompt_type: str = "general"

    # Response parsing
    answer_tag: str = "answer_clipped"
    think_start_tag: str = "<think>"
    think_end_tag: str = "\n</think>\n\n"

    # Network
    timeout: float = 600.0
    max_retries: int = 3

    # 便捷属性：如果未指定 summary_* 配置，默认复用 reasoning 配置
    @property
    def summary_model(self) -> str:
        return self.summary_model_name or self.model_name

    @property
    def summary_base(self) -> str:
        return self.summary_api_base or self.api_base

    @property
    def summary_key(self) -> str:
        return self.summary_api_key or self.api_key
```

**关键配置参数**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `reason_k` | 8 | 并行推理轨迹数量 |
| `reason_temperature` | 1.0 | 推理温度（高温度=高多样性） |
| `reason_max_tokens` | 32768 | 单条轨迹最大 token 数 |
| `reason_top_p` | 0.95 | Top-p 采样参数 |
| `summary_k` | 4 | 深思输出数量 |
| `summary_temperature` | 0.7 | 深思温度（较低=更聚焦） |
| `summary_max_tokens` | 32768 | 深思输出最大 token 数 |
| `iterations` | 1 | 深思迭代轮数 |
| `trajectory_selection` | "max_diversity" | 轨迹选择策略 |
| `max_trajectory_tokens` | 128000 | 轨迹 token 预算上限 |
| `think_start_tag` | `"<think>"` | 思考内容开始标签 |
| `think_end_tag` | `"\n</think>\n\n"` | 思考内容结束标签 |

#### Pipeline（pipeline.py）

Pipeline 是整个系统的编排器，协调两个阶段的执行：

```python
@dataclass
class HeavySkillResult:
    query: str
    trajectories: List[str]      # K 条并行推理轨迹
    summaries: List[str]          # summary_k 个深思输出
    iterations_done: int
    final_answer: str = ""

async def run_heavyskill(
    query: str,
    config: HeavySkillConfig,
    reasoning_agent: Optional[OpenAICompatibleAgent] = None,
    summary_agent: Optional[OpenAICompatibleAgent] = None,
) -> HeavySkillResult:
    # 初始化 Agent
    if reasoning_agent is None:
        reasoning_agent = OpenAICompatibleAgent(
            model_name=config.model_name,
            api_base=config.api_base,
            api_key=config.api_key,
        )
    if summary_agent is None:
        summary_agent = OpenAICompatibleAgent(
            model_name=config.summary_model,
            api_base=config.summary_base,
            api_key=config.summary_key,
        )

    # 阶段一：并行推理
    trajectories = await parallel_reason(query, config, agent=reasoning_agent)
    cache = MemoryCache(trajectories)

    # 阶段二：顺序深思（支持迭代）
    summaries = []
    for iteration in range(config.iterations):
        summaries = await deliberate(
            query=query,
            cache=cache,
            config=config,
            agent=summary_agent,
            trajectory_selection=config.trajectory_selection,
        )
        # 多轮迭代：将深思结果加入轨迹集
        if config.iterations > 1 and iteration < config.iterations - 1:
            for s in summaries:
                cache.add_deliberation(s)

    return HeavySkillResult(
        trajectories=trajectories,
        summaries=summaries,
        iterations_done=config.iterations,
        final_answer=summaries[0] if summaries else "",
    )
```

#### MemoryCache（memory_cache.py）

MemoryCache 负责管理和选择推理轨迹，支持多种选择策略：

| 策略 | 说明 |
|------|------|
| `random` | 随机选择 |
| `max_answer_num` | 选择答案出现次数最多的轨迹 |
| `max_diversity` | 最大化答案多样性（默认） |

#### 提示词模板（prompts.py）

系统提供两种深思提示模板：

**通用模板（General）** 适用于日常对话和开放性推理：

```
You are a professional reasoner and AI assistant.

Here is a user query, and multiple thinkers attempt to give their thought processes independently.
Each thinker has written its own thought response to answer the given query.

# ====== Query Start ======
{problem}
# ====== Query End ======

# ====== Thinkers Thought Response Start ======
{response_prompt}
# ====== Thinkers Thought Response End ======

Look at the above query and thought response from each thinker, your task is to carefully
analyze the thought processes of different thinkers, and ultimately formulate a response
that can answer a given query.

Note:
1. You must follow the requirements and instructions given in the query.
2. It is generally believed that when most thinkers get the similar answer, the answer may
   be correct. But you can't do it so superficially, because the correct answer may come
   from very few thinkers, or even no thinker gives the correct answer. For this reason,
   when analyzing, you NEED adhere to the principles of professionalism and critical
   thinking, carefully identify these thought processes, and give the final answer.
3. If you realize that none of these thinkers have answered correctly, you can even learn
   from the wrong experiences in the thought process of these thinkers and re-think the
   given problem to give the answer you think is most correct.
```

**STEM 模板** 适用于数学、科学、工程等需要严谨推理的领域：

```
You are a great reasoner.

Here is a problem, and multiple thinkers attempt to give their thought processes independently.
Each thinker has written its own thought process towards the final answer.

# ====== Problem ======
{problem}
# ====== Problem End ======

# ====== Thinkers Thought Process ======
{response_prompt}
# ====== Thinkers Thought Process End ======

Look at the above problem and thought process from each thinker, summarize from these
thought processes and finally give your answer.

Note:
- It is generally believed that when most thinkers...
- Please DO NOT just solve the given problem independently like other thinkers, but
  summarize the thought process of all thinkers. In other words, you need to give the
  summary first, and then give the final answer.
- Your final answer after the summary should within boxed for math/STEM problems.
```

#### 工具函数（utils.py）

**`split_response()`** — 解析模型的思考内容和答案内容：

```python
def split_response(
    response: str,
    think_start_tag: str = "<think>",
    think_end_tag: str = "\n</think>\n\n"
) -> tuple:
    """Split a response into thinking content and answer content."""
    if think_end_tag in response:
        parts = response.split(think_end_tag)
        think_content = parts[0].replace(think_start_tag, "").strip()
        answer_content = parts[-1].strip()
    else:
        think_content = response.replace(think_start_tag, "").strip()
        answer_content = ""
    return think_content, answer_content
```

**`clip_trajectories()`** — 轨迹 token 预算裁剪：

```python
def clip_trajectories(
    trajectories: List[str],
    max_total_tokens: int,
    estimate_fn=None,
) -> List[str]:
    """Clip trajectories from the beginning if total tokens exceed the budget."""
    if estimate_fn is None:
        estimate_fn = estimate_token_count

    token_counts = [estimate_fn(t) for t in trajectories]
    total = sum(token_counts)

    if total <= max_total_tokens:
        return trajectories

    excess = total - max_total_tokens
    cut_per_trajectory = excess // len(trajectories) + 1

    clipped = []
    for text, count in zip(trajectories, token_counts):
        if count <= cut_per_trajectory:
            clipped.append(text)
            continue
        ratio = cut_per_trajectory / count
        char_cut = int(len(text) * ratio)
        clipped.append(text[char_cut:])

    return clipped
```

**`duplication()`**（在 deepthink_workflow.py 中）— 检测复读/截断：

```python
def duplication(response, think_end_tag):
    # 如果模型出现复读导致截断的问题
    if response[-512:] == response[-1024:-512]:
        return True
    # 如果输出存在超长截断的问题，也忽略
    if think_end_tag not in response:
        return True
    return False
```

#### deepthink_workflow.py（高级研究工作流）

这是 57KB 的高级研究实验工作流，提供更丰富的功能：

1. **Permutation 策略**：支持按不同排列组合构造并行思考集
2. **Pass@K 和 Major@K 指标计算**：统计意义上的评估
3. **多 Agent 支持**：集成 vLLM Agent、APIAgent 等
4. **更细致的复读检测**：针对 thinking 阶段输出的特殊处理

---

## 两种使用模式

### 模式一：Workflow（Python 流水线）

适合批量评估、研究实验、自定义部署。

**安装**：

```bash
git clone https://github.com/wjn1996/HeavySkill.git
cd HeavySkill
pip install -e .
```

**基础用法**：

```bash
python scripts/run_heavyskill.py \
    --query "Find the number of paths of length 16 on an 8x8 grid that change direction exactly four times." \
    --model "deepseek-r1" \
    --api_base "http://localhost:8080" \
    --reason_k 8 \
    --summary_k 4 \
    --prompt_type "stem" \
    --output "outputs/result.json" \
    --verbose
```

**关键参数**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--reason_k` | 8 | 并行推理轨迹数量 |
| `--summary_k` | 4 | 深思输出数量 |
| `--iterations` | 1 | 深思迭代轮数 |
| `--prompt_type` | general | 提示词类型：`general` 或 `stem` |
| `--language` | en | 输出语言：`en` 或 `cn` |
| `--trajectory_selection` | max_diversity | 轨迹选择策略 |

**使用独立深思模型**（可选）：

```bash
python scripts/run_heavyskill.py \
    --query "Your problem here" \
    --model "r1-distill-qwen-7b" \
    --api_base "http://localhost:8080" \
    --summary_model "qwen3-32b" \
    --summary_api_base "http://localhost:8081" \
    --reason_k 16 \
    --summary_k 4
```

**批量模式**：

```bash
python scripts/run_heavyskill.py \
    --input_file "examples/example_math.json" \
    --model "deepseek-r1" \
    --api_base "http://localhost:8080" \
    --output "outputs/batch_result.json"
```

### 模式二：Skill（Claude Code / Agentic Harness）

适合在 AI 原生 IDE 中进行交互式推理。

**安装**：将 Skill 文件复制到 Claude Code 的 skills 目录：

```bash
cp skill/heavyskill.md ~/.claude/skills/heavyskill.md
```

**使用协议**：

**阶段一：并行推理**

在 Claude Code 中，遇到复杂推理任务时，启动 K=3~5 个独立推理 Agent：

```
为以下问题生成 3 条独立的推理轨迹：

问题：{用户查询}

每个 Agent 必须：
- 从头开始逐步解决给定问题
- 展示完整的推理链
- 得出最终答案
- 不与其他 Agent 通信
- 尽可能使用不同的推理方法（如代数法 vs 几何法）
```

**阶段二：顺序深思**

收集所有轨迹后，执行批判性分析：

```
多位独立思考者已尝试解决此问题。分析他们的推理：

问题：{用户查询}

思考者 #1：{轨迹1}
思考者 #2：{轨迹2}
思考者 #3：{轨迹3}

你的任务：
- 分析所有思考者的思维过程
- 识别每种方法中的逻辑错误或漏洞
- 确定哪些推理路径最可靠
- 如果所有思考者都错了，从他们的错误中独立重新推理
- 提供最终确定的答案
```

**关键原则**：

- **独立性至关重要**：并行 Agent 不能共享上下文
- **多样性有帮助**：鼓励不同的解题策略
- **深思是合成，不是投票**：不只看多数答案，分析推理质量
- **语言一致性**：输出语言匹配查询语言
- **格式一致性**：数学用 `\boxed{}`，代码用代码块

---

## API 兼容性

HeavySkill 支持任何 OpenAI 兼容 API 端点：

| 服务 | API Base 示例 |
|------|--------------|
| vLLM | `--api_base http://localhost:8000` |
| DeepSeek API | `--api_base https://api.deepseek.com` |
| Together AI | `--api_base https://api.together.xyz` |
| OpenRouter | `--api_base https://openrouter.ai/api` |
| Local Ollama | `--api_base http://localhost:11434` |

**配置示例（使用 DeepSeek）**：

```python
config = HeavySkillConfig(
    model_name="deepseek-reasoner",
    api_base="https://api.deepseek.com",
    api_key="your-api-key",
    reason_k=8,
    summary_k=4,
)
```

---

## 实验结果与核心发现

根据论文 arXiv:2605.02396，HeavySkill 在多个维度展现优势：

### 核心发现（来自论文摘要）

论文摘要明确指出：

> 「我们提出 HeavySkill，将深度思考视为编排框架中的最小执行单元，也是内化于模型参数中的内在技能……实验结果表明，这种内在技能一致性地优于传统的 Best-of-N（BoN）策略；更强的 LLM 甚至可以接近 Pass@N 的表现。」

### 关键发现

1. **一致性地超越 Best-of-N**：Heavy thinking 在各种任务上一致性地优于多数投票策略

2. **更强模型受益更多**：通过深思，更强的 LLM 可以接近 Pass@N 的表现

3. **深度和宽度皆可扩展**：
   - **深度（iterations）**：迭代深思轮数
   - **宽度（K）**：并行推理轨迹数量
   - 这两个维度都可以通过 RLVR（强化学习）进一步扩展

4. **有望实现自我进化的 LLM**：将复杂推理内化到模型参数中，而不依赖脆弱的编排层

---

## 与 Claude Code 的集成

HeavySkill 的 Skill 模式专为 Claude Code 等 Agentic Harness 设计。

### 集成优势

**开箱即用**：无需编写代码，直接复制 Skill 文件即可使用

**交互友好**：适合复杂推理任务的探索性分析

**可迭代**：在 Claude Code 中可以多轮对话逐步深化推理

### 使用场景

适合以下场景激活 HeavySkill：

- 数学竞赛问题（AMC、AIME、IMO）
- 复杂逻辑推理
- 代码竞赛 / 算法问题
- 正确性关键且可验证的任务
- 对初始方法不确定的问题

不适合简单的事实查询、直白的代码编辑、主要依赖信息检索的任务。

---

## 扩展与二次开发

### 自定义轨迹选择策略

在 MemoryCache 中扩展选择逻辑：

```python
def _max_answer_num_select(self, k: int) -> List[str]:
    """选择答案出现次数最多的轨迹"""
    from collections import Counter
    answers = [extract_boxed_answer(t) or t[-200:] for t in self.trajectories]
    counter = Counter(answers)
    # 返回答案出现次数最多的轨迹
    answer_counts = [(t, counter[extract_boxed_answer(t) or t[-200:]]) for t in self.trajectories]
    answer_counts.sort(key=lambda x: x[1], reverse=True)
    return [t for t, _ in answer_counts[:k]]
```

### 自定义提示词模板

在 prompts.py 中扩展提示词模板：

```python
PROMPT_REGISTRY = {
    "general": {"en": SUMMARY_PROMPT_GENERAL_EN, "cn": SUMMARY_PROMPT_GENERAL_CN},
    "stem": {"en": SUMMARY_PROMPT_STEM, "cn": SUMMARY_PROMPT_STEM},
}

def build_custom_prompt(
    query: str,
    trajectories: List[str],
    prompt_type: str = "general",
    language: str = "en",
) -> str:
    if prompt_type == "custom":
        return CUSTOM_TEMPLATE.format(
            problem=query,
            response_prompt=format_thinkers_prompt(trajectories)
        )
    return build_summary_prompt(query, trajectories, prompt_type, language)
```

### 批量评估框架

使用 scripts/evaluate.py 构建评估流水线：

```bash
python scripts/evaluate.py \
    --result_file "outputs/result.json" \
    --target_file "path/to/targets.json"
```

评估脚本会：
1. 提取每个预测答案的 `\boxed{}` 内容
2. 与目标答案进行匹配（支持数值容差）
3. 输出准确率统计

---

## 总结

HeavySkill 代表了测试时计算 Scaling 的新范式：不只是生成更多轨迹，而是通过深思将多条推理轨迹合成真正优越的答案。

**核心优势**：

| 特性 | 说明 |
|------|------|
| 两阶段架构 | 并行推理 + 顺序深思，分工明确 |
| 即插即用 | 支持任意 OpenAI 兼容 API |
| 双重模式 | Workflow 适合批量，Skill 适合交互 |
| 可扩展 | iterations 和 K 都是有意义的 Scaling 维度 |
| 自我进化 | 可通过 RLVR 将推理能力内化到模型 |

**适用场景**：

- 需要高可靠性的复杂推理任务
- 数学、代码、逻辑推理场景
- 希望提升现有 LLM 推理质量的开发者

**资源链接**：

- GitHub：https://github.com/wjn1996/HeavySkill
- 论文：https://arxiv.org/abs/2605.02396

---

**原文来源**：GitHub wjn1996/HeavySkill
**论文引用**：
```bibtex
@article{wang2026heavyskill,
  title={HeavySkill: Heavy Thinking as the Inner Skill in Agentic Harness},
  author={Wang, Jianing and Guo, Linsen and Chen, Zhengyu and Guo, Qi and Zang, Hongyu and Shi, Wenjie and Ma, Haoxiang and Xi, Xiangyu and Li, Xiaoyu and Wang, Wei and Cai, Xunliang},
  journal={arXiv preprint arXiv:2605.02396},
  year={2026},
  url={https://arxiv.org/abs/2605.02396}
}
```