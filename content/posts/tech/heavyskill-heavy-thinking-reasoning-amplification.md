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

> **难度**：⭐⭐⭐⭐ | **类型**：专家设计 | **更新日期**：2026-05-06 | **预计阅读时间**：20 分钟
>
> **目标读者**：AI 研究者、LLM 应用开发者、Agent 系统架构师
>
> **前置知识**：了解 LLM 基本原理、Chain-of-Thought推理、Agent概念

---

## 背景与问题动机

### 简单推理的局限性

传统大语言模型推理采用单链式思维（Chain-of-Thought，CoT），即模型一次性生成完整的推理链条。这种方式存在几个根本性缺陷：

**错误级联**：推理早期的一个错误会传播到整个链条，导致最终答案完全错误。由于模型在生成过程中无法回头修改已经输出的内容，错误一旦发生就无法纠正。

**认知盲区**：单一推理路径意味着模型只能探索解空间的一个局部。当正确解法需要"换一种思路"时，单链推理无法提供这种灵活性。

**置信度缺失**：单链推理不提供答案的置信度信息。在需要可靠性的场景（如代码竞赛、数学证明），无法判断当前答案是否可信。

### 现有解决方案的不足

**Best-of-N（多数投票）**：生成 N 个独立答案，选择出现次数最多的作为最终答案。多数投票假设"正确答案更容易被多次生成"，但这在推理任务中往往不成立——正确答案可能只有一条，而错误答案有无数种。

**Pass@N**：允许 N 次生成尝试中只要有一次成功即算通过。这需要多次独立运行，成本高昂，且没有真正利用多次推理的多样性来提升推理质量。

**Self-Consistency**：对 CoT 的改进，通过采样多条推理路径并聚合。但多数投票的聚合方式丢失了推理过程中的关键信息，无法进行真正的"深思"。

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

第一阶段生成 K 条完全独立的推理轨迹。每条轨迹由一个独立的"思考者"生成：

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
    valid = [t for t in trajectories if not is_repetitive(t)]
    return valid
```

**关键设计**：
- 温度采样确保轨迹多样性
- 过滤机制剔除重复内容
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
) -> List[str]:
    """对推理轨迹进行批判性分析"""
    selected = cache.select(k=config.reason_k, strategy="max_diversity")
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
    )
    return summaries
```

**深思的核心逻辑**：

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
迭代 2：将深思结果作为新的"专家思考者"加入轨迹集 → Stage 2 重新深思
迭代 3：重复...
```

典型场景下 2-3 次迭代即可收敛。

---

## 项目架构与代码分析

### 整体目录结构

```
HeavySkill/
├── workflow/                    # 模式一：Python 异步流水线
│   ├── pipeline.py              # 完整流程编排
│   ├── parallel_reasoning.py    # 阶段一：并行推理
│   ├── sequential_deliberation.py  # 阶段二：顺序深思
│   ├── memory_cache.py         # 轨迹存储与选择
│   ├── prompts.py              # 提示词模板
│   ├── config.py               # 配置数据类
│   ├── utils.py                 # 工具函数
│   └── agent/
│       ├── base.py             # 抽象 Agent 接口
│       └── openai_compatible.py # OpenAI 兼容异步 API 客户端
├── scripts/
│   ├── run_heavyskill.py       # CLI 入口
│   ├── run_heavyskill.sh        # 示例脚本
│   └── evaluate.py              # 准确率评估
├── skill/
│   └── heavyskill.md            # Claude Code Skill 提示词
├── examples/
│   └── example_math.json        # 示例输入数据
├── paper/
│   └── heavyskill.pdf           # 论文
├── requirements.txt
└── pyproject.toml
```

### 核心模块分析

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
) -> HeavySkillResult:
    # 阶段一：并行推理
    trajectories = await parallel_reason(query, config)
    cache = MemoryCache(trajectories)

    # 阶段二：顺序深思（支持迭代）
    summaries = []
    for iteration in range(config.iterations):
        summaries = await deliberate(query, cache, config)
        if config.iterations > 1:
            cache.add_deliberation(summaries)
    return HeavySkillResult(
        trajectories=trajectories,
        summaries=summaries,
        final_answer=summaries[0] if summaries else ""
    )
```

#### MemoryCache（memory_cache.py）

MemoryCache 负责管理和选择推理轨迹，支持多种选择策略：

| 策略 | 说明 |
|------|------|
| `random` | 随机选择 |
| `max_answer_num` | 选择答案出现次数最多的轨迹 |
| `max_diversity` | 最大化答案多样性 |

```python
class MemoryCache:
    def __init__(self, trajectories: List[str]):
        self.trajectories = trajectories
        self.deliberations = []

    def select(self, k: int, strategy: str = "random") -> List[str]:
        if strategy == "max_diversity":
            return self._max_diversity_select(k)
        elif strategy == "max_answer_num":
            return self._max_answer_num_select(k)
        return random.sample(self.trajectories, min(k, len(self.trajectories)))
```

#### OpenAI 兼容 Agent（agent/openai_compatible.py）

系统不绑定特定模型，支持任何 OpenAI 兼容 API：

```python
class OpenAICompatibleAgent:
    async def generate(
        self,
        prompt: str,
        n: int = 1,
        temperature: float = 1.0,
        max_tokens: int = 2048,
        top_p: float = 1.0,
    ) -> List[str]:
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            n=n,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )
        return [choice.message.content for choice in response.choices]
```

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
from heavyskill.workflow import HeavySkillConfig

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

### 与 Best-of-N 的对比

| 方法 | MATH-500 准确率 | AIME 2024 准确率 |
|------|----------------|-----------------|
| Best-of-8（多数投票） | 基准 | 基准 |
| HeavySkill-K=8 | +X.X% | +X.X% |
| HeavySkill-K=16 | +X.X% | +X.X% |

Heavy thinking 一致性地优于 Best-of-N 多数投票策略。

### 关键发现

1. **深思深度和宽度可通过 RLVR 扩展**：iterations（迭代次数）和 K（并行轨迹数）都是有意义的 Scaling 维度

2. **更强模型受益更多**：通过深思，更强的 LLM 可以接近 Pass@N 的表现

3. **推理质量优于答案数量**：精心的一次深思比多次浅层采样更有价值

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

继承 MemoryCache 并实现自定义选择逻辑：

```python
class CustomMemoryCache(MemoryCache):
    def _my_strategy_select(self, k: int) -> List[str]:
        # 自定义选择逻辑
        # 例如：优先选择包含特定关键词的轨迹
        pass
```

### 自定义提示词模板

在 prompts.py 中扩展提示词模板：

```python
def build_custom_prompt(
    query: str,
    trajectories: List[str],
    prompt_type: str = "general",
) -> str:
    if prompt_type == "custom":
        return CUSTOM_TEMPLATE.format(
            query=query,
            trajectories="\n\n".join(trajectories)
        )
    return build_summary_prompt(query, trajectories, prompt_type)
```

### 批量评估框架

使用 scripts/evaluate.py 构建评估流水线：

```python
from heavyskill.scripts.evaluate import evaluate

results = evaluate(
    dataset="math benchmarks",
    model="deepseek-r1",
    reason_k=8,
    iterations=2,
)
```

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
  author={Wang, Jianing and Guo, Linsen and others},
  journal={arXiv preprint arXiv:2605.02396},
  year={2026}
}
```