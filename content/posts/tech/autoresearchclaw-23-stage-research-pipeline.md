---
title: "AutoResearchClaw：全自动 23 阶段研究论文生成管道，从想法到论文的完整实践"
slug: autoresearchclaw-23-stage-research-pipeline
github_repo: "aiming-lab/AutoResearchClaw"
source_key: "gh:aiming-lab/AutoResearchClaw"
aliases:
  - "/posts/tech/autoresearchclaw-full-autonomous-research-agent/"
date: "2026-04-21T07:45:00+08:00"
description: "全面解析 AutoResearchClaw：一个开源的全自动研究论文生成管道（v0.5.0），23 阶段闭环流程涵盖文献发现、实验设计、多领域执行代理、论文撰写全链路，支持多代理辩论、Human-in-the-Loop 协作、MetaClaw 跨运行学习、VerifiedRegistry 抗伪造与四层引用验证，以及 ARC-Bench 55 主题跨学科开放基准。"
categories: ["技术笔记"]
tags: ["LLM", "Multi-Agent", "OpenClaw", "ARC-Bench", "Self-Evolution", "HITL"]
---

# AutoResearchClaw：全自动 23 阶段研究论文生成管道，从想法到论文的完整实践

## 核心判断

AutoResearchClaw 把研究流程拆成 23 个可中断的阶段，关键价值在两件事：所有文献绑定真实 API（arXiv、Semantic Scholar、OpenAlex），所有论文数字必须能回溯到实验运行。这两点决定了它生成的论文能当学术产出，不只是 demo。2026 年 5 月，项目团队的方法论文提交到 arXiv（[arXiv:2605.20025](https://arxiv.org/abs/2605.20025)），系统已在数学、统计、生物、计算、NLP、强化学习、视觉、鲁棒性 8 个领域各生成过一篇可展示的完整论文。

> **GitHub**: [aiming-lab/AutoResearchClaw](https://github.com/aiming-lab/AutoResearchClaw) · **许可证**: MIT · **语言**: Python 3.11+ · **当前版本**: v0.5.0
>
> | 指标 | 数值 |
> |------|------|
> | ⭐ Stars | 14.4k+（2026-09-13 观测） |
> | 🍴 Forks | 1.7k+ |
> | 📜 方法论文 | [arXiv:2605.20025](https://arxiv.org/abs/2605.20025) |
> | 🏆 已展示论文 | 8 领域 8 篇 |

一句话定位：**"Chat an Idea. Get a Paper."** —— 输入一个研究想法，输出一篇完整的学术论文。

## 学习目标

读完本文应能：

1. 说清 23 个阶段如何分成 Phase A-H，每个 Phase 的核心职责
2. 解释 `VerifiedRegistry` 如何防止 LLM 编造实验数据，判断一篇论文是否可复现
3. 根据研究想法（如"量子门噪声作为正则化器"）说出完整的 23 阶段流转路径
4. 识别 MetaClaw 的自进化机制，理解"跨运行学习"在工程系统中的价值
5. 说出 v0.5.0 引入的多领域执行代理（ColliderAgent、COBRApy、统计模拟）和 ARC-Bench 基准（55 个开放研究主题）解决了什么问题
6. 对比 AutoResearchClaw 与 GPT-Researcher / Karpathy autoresearch / AI Scientist 的定位差异，解释为什么缺少实验真值绑定就难以产出可复现的学术成果

## 目录

- [核心判断](#核心判断)
- [学习目标](#学习目标)
- [版本演进](#版本演进)
- [系统总览](#系统总览)
- [Phase A-B：研究与文献阶段](#phase-a-b研究与文献阶段)
- [Phase C：知识综合与假设生成](#phase-c知识综合与假设生成)
- [Phase D-E：实验设计与执行](#phase-d-e实验设计与执行)
- [Phase F-G：分析与论文写作](#phase-f-g分析与论文写作)
- [Phase H：质量保障与发布](#phase-h质量保障与发布)
- [v0.5.0：多领域实验代理与 ARC-Bench](#v050多领域实验代理与-arc-bench)
- [Human-in-the-Loop Co-Pilot 系统](#human-in-the-loop-co-pilot-系统)
- [MetaClaw：跨运行自进化学习](#metaclaw跨运行自进化学习)
- [Sentinel 看门狗与 Claim Verification](#sentinel-看门狗与-claim-verification)
- [OpenClaw 集成](#openclaw-集成)
- [快速开始](#快速开始)
- [与同类项目对比](#与同类项目对比)
- [采用建议](#采用建议)
- [资源链接](#资源链接)
- [自测题](#自测题)
- [进阶路径](#进阶路径)

## 版本演进

项目从 v0.1.0 的纯自主管道演进到 v0.5.0 的多领域研究平台，关键能力的时间线：

| 版本 | 日期 | 核心更新 |
|------|------|---------|
| **v0.1.0** | 2026-03-15 | 首发 23 阶段全自动管道，"Chat an Idea. Get a Paper." |
| **v0.2.0** | 2026-03-16 | CodeAgent / BenchmarkAgent / FigureAgent 三代理子系统；Docker 沙箱加固；4 轮论文质量审计（AI-slop 检测、7 维评分、NeurIPS checklist） |
| **v0.3.0** | 2026-03-17 | MetaClaw 跨运行自进化；受控实验显示鲁棒性 +18.3% |
| **v0.3.2** | 2026-03-22 | ACP 协议支持（Claude Code / Codex / Copilot / Gemini / Kimi）；VerifiedRegistry 抗伪造 |
| **v0.4.0** | 2026-04-01 | **HITL Co-Pilot 系统**：多种干预模式、SmartPause、Paper Co-Writer、成本守卫 |
| **v0.5.0** | 2026-05-19 | **多领域实验代理**：高能物理（ColliderAgent）、生物学（COBRApy）、统计模拟；**ARC-Bench** 55 主题开放基准 |

理解这条演进线很重要——它解释了为什么本文里有些特性（如 HITL、MetaClaw）在 v0.1.0 里不存在。v0.1.0 是一个"纯自主 ML 研究 demo"，后续版本逐步补上跨学科能力和人机协作能力。

## 系统总览

### 23 阶段管道全景

```text
Phase A: 研究定位            Phase E: 实验执行
  1. TOPIC_INIT               12. EXPERIMENT_RUN
  2. PROBLEM_DECOMPOSE         13. ITERATIVE_REFINE  ← 自愈循环

Phase B: 文献发现            Phase F: 分析与决策
  3. SEARCH_STRATEGY           14. RESULT_ANALYSIS    ← 多代理分析
  4. LITERATURE_COLLECT        15. RESEARCH_DECISION  ← PROCEED/REFINE/PIVOT
  5. LITERATURE_SCREEN [门控]
  6. KNOWLEDGE_EXTRACT

Phase C: 知识综合            Phase G: 论文写作
  7. SYNTHESIS                 16. PAPER_OUTLINE
  8. HYPOTHESIS_GEN ←辩论     17. PAPER_DRAFT
                               18. PEER_REVIEW        ← 方法论-证据一致性检查
Phase D: 实验设计            19. PAPER_REVISION
  9. EXPERIMENT_DESIGN [门控]
 10. CODE_GENERATION         Phase H: 终稿生成
 11. RESOURCE_PLANNING         20. QUALITY_GATE [门控]
                               21. KNOWLEDGE_ARCHIVE
                               22. EXPORT_PUBLISH     ← LaTeX 导出
                               23. CITATION_VERIFY    ← 引用相关性验证
```

### 并行机制边界

23 个阶段大部分是串行门控，但有 3 处并行或循环机制需要先拆开，否则会把整条管道误读成单线流程：

1. **Phase B 多源检索**：`SEARCH_STRATEGY` 和 `LITERATURE_COLLECT` 按配置顺序查询 OpenAlex、Semantic Scholar、arXiv 三个数据源，某一数据源失败时熔断降级到备选源。
2. **Phase E 自愈循环**：`EXPERIMENT_RUN` → `ITERATIVE_REFINE` 是一个最多 10 轮的循环，按错误类型分派修复策略，不是线性推进。
3. **Phase G 写作流水线**：`PAPER_OUTLINE` → `PAPER_DRAFT` → `PEER_REVIEW` → `PAPER_REVISION` 严格串行；`PEER_REVIEW` 用多个审稿人视角的 prompt 分别评审后汇总。

3 个门控节点（Stage 5 `LITERATURE_SCREEN`、Stage 9 `EXPERIMENT_DESIGN`、Stage 20 `QUALITY_GATE`）会阻塞管道，等待人工审核或 `--auto-approve` 自动放行。HITL 模式下还会在更多位置触发暂停。

### 任务流案例：从想法到论文

假设输入研究想法"量子门噪声能否作为结构化正则化器"，完整流程如下：

1. **Stage 1 `TOPIC_INIT`**：把想法转为 SMART 目标，检测到 NVIDIA RTX 3090、CUDA 11.8、24GB 显存
2. **Stage 3-6 文献发现**：多源检索量子机器学习论文，提取知识卡片，识别已有方法和局限
3. **Stage 7 `SYNTHESIS`**：聚类后识别 gap——量子噪声的正则化效应未被系统研究
4. **Stage 8 `HYPOTHESIS_GEN`**：innovator / pragmatist / contrarian 三个角色辩论后输出假设，每个带 `novelty_score`
5. **Stage 9 `EXPERIMENT_DESIGN` [门控]**：人类审核基线（Dropout、Label Smoothing、MixUp），添加 STL-10 数据集
6. **Stage 10-13 实验执行**：`CodeAgent` 生成训练代码，沙箱运行，`ITERATIVE_REFINE` 修复维度不匹配
7. **Stage 14-15 决策**：结果支持假设 → `PROCEED`
8. **Stage 16-19 论文写作**：IMRAD 结构，`PEER_REVIEW` 检查方法论-证据一致性
9. **Stage 20 `QUALITY_GATE` [门控]**：综合评分通过
10. **Stage 22-23 导出**：LaTeX 终稿 + 四层引用验证

耗时方面，官方 HITL 指南给的口径是：纯自主执行一次典型运行约 2-4 小时；Co-Pilot 模式下人的典型投入是每次运行 30-60 分钟，其余时间管道自动推进，实际挂钟时间取决于人工响应速度和实验时长。

## Phase A-B：研究与文献阶段

### Stage 1-2：研究定位

**TOPIC_INIT** 将用户的研究想法转化为结构化的 SMART 研究目标，同时自动检测硬件环境（NVIDIA CUDA / Apple MPS / CPU-only），为后续实验代码生成提供依据。硬件检测的意义在于：`CodeAgent` 生成代码时会根据 GPU 类型选择 `torch.cuda` 或 `torch.mps`，避免运行时才发现设备不匹配。

```json
{
  "gpu_type": "NVIDIA RTX 3090",
  "cuda_version": "11.8",
  "memory_gb": 24,
  "recommended_package": "torch>=2.0.0"
}
```

（示意配置，实际字段以运行产物为准。）

**PROBLEM_DECOMPOSE** 把研究目标拆成带研究问题的结构化问题树，圈定后续文献检索和假设生成的边界。

### Stage 3-6：文献发现

文献发现阶段是整个管道的质量基石。AutoResearchClaw 采用多源搜索策略，原因是单一数据源覆盖面不够，且任何 API 都可能临时不可用。检索后端的优先顺序由 `literature_search.sources` 配置决定，默认从 OpenAlex 开始：

| 数据源 | 默认顺序 | 特点 |
|--------|--------|------|
| **OpenAlex** | 第一优先 | 开放学术元数据图谱，免费额度高（约 1 万次/天） |
| **Semantic Scholar** | 第二优先 | 引用网络分析；配置 `s2_api_key` 可提高速率限制 |
| **arXiv** | 第三优先 | 预印本平台，更新快，全文可得 |

**LITERATURE_COLLECT** 的关键特性：

- **查询扩展**：自动生成同义词、近义词查询，提升覆盖率
- **去重机制**：多源结果合并时去重（配置项 `max_results_per_query` 是去重前的单查询上限）
- **熔断降级**：某一数据源失败时自动切换到备选源

**KNOWLEDGE_EXTRACT** 从每篇论文中提取结构化的知识卡片，为后续 `SYNTHESIS` 阶段提供可聚类的输入：

```json
{
  "paper_id": "arxiv:2301.00001",
  "title": "Attention Is All You Need",
  "key_findings": ["Transformer 架构", "自注意力机制", "并行计算效率"],
  "method": "encoder-decoder + multi-head attention",
  "limitations": ["计算复杂度 O(n²)", "位置信息编码需要额外设计"],
  "research_gap": "长期依赖建模效率问题"
}
```

## Phase C：知识综合与假设生成

### Stage 7：综合分析

`SYNTHESIS` 阶段将文献知识聚类，识别研究空白。聚类依据是方法论相似性，这样能发现跨方法的研究机会——关键词匹配会把不同表述的同类方法归到不同簇：

```text
输入：6 篇论文的知识卡片
     ↓
知识聚类（基于方法论相似性）
     ↓
gap_1: Transformer 在长期依赖任务上的效率问题
gap_2: 注意力机制的稀疏化可能性
gap_3: 跨模态 Transformer 的可行性
     ↓
输出：synthesis.md（研究空白分析报告）
```

### Stage 8：多代理辩论假设生成

`HYPOTHESIS_GEN` 采用多代理辩论机制生成可证伪的假设。单代理容易陷入自我确认——它倾向于生成自己已经知道的假设。引入多个辩论角色后，假设在生成阶段就要经受不同立场的质疑，输出更经得起后续实验检验。ML 领域的默认角色组合是 **innovator（创新者）/ pragmatist（实用主义者）/ contrarian（反对者）**，辩论引擎支持多轮陈述与反驳：

```python
DEBATE_ROLES_HYPOTHESIS = {
    "innovator":  "...",  # 提出新颖假设方向
    "pragmatist": "...",  # 评估可行性、资源与时间约束
    "contrarian": "...",  # 主动找反例与失败模式
}

多轮辩论后输出假设，每个带 novelty_score
```

| 假设 | 新颖性评分 | 可行性评分 | 预期产出 |
|------|-----------|-----------|---------|
| 量子门噪声作为结构化正则化器 | 8/10 | 6/10 | 论文 1 |
| 纠缠特征选择 | 7/10 | 4/10 | 论文 2（搁置） |
| 量子采样数据增强 | 5/10 | 8/10 | 论文 3（快速验证） |

## Phase D-E：实验设计与执行

### Stage 9：门控式实验设计

`EXPERIMENT_DESIGN` 是第一个关键门控节点。在此处设门控的原因是：实验设计一旦确定，后续代码生成、资源规划、沙箱执行都会沿着这个方向走，错误越早发现成本越低。系统生成：

- **基线选择**：根据研究领域自动推荐经典方法和当前 SOTA（BenchmarkAgent 走 Surveyor → Selector → Acquirer → Validator 四步流程，支持 HuggingFace 数据集和 Google Scholar 检索）
- **数据集层级**：Tier 1（小型/缓存）→ Tier 2（中型）→ Tier 3（大型），由 `benchmark_agent.tier_limit` 控制
- **评估指标**：准确率、F1、AUC 等领域标准指标
- **消融实验计划**：明确需要 ablation study 的组件

人类专家在此阶段可以：

- 添加或删除基线方法
- 调整数据集选择
- 验证实验可重复性

### Stage 10-11：硬件感知代码生成

**CODE_GENERATION** 是管道中最复杂的阶段之一。`CodeAgent` 采用多阶段架构，先规划再生成，原因是直接生成完整代码容易产生文件间依赖混乱：

```yaml
code_agent:
  enabled: true
  architecture_planning: true      # 先规划架构，再生成代码
  sequential_generation: true      # 按依赖顺序生成文件
  hard_validation: true            # AST 验证，阻止硬编码指标与相同消融
  hard_validation_max_repairs: 2   # 校验失败最多修复次数
  exec_fix_max_iterations: 3       # 执行反馈修复次数
```

`hard_validation` 会做 AST 检查，阻止代码里出现硬编码的指标数字和"换汤不换药"的相同消融组——这是抗伪造的第一道防线，确保论文里的数字只能来自真实实验运行。

**RESOURCE_PLANNING** 估算实验所需资源：

| 资源类型 | 估算依据 |
|---------|---------|
| GPU 时间 | 模型参数量 × 数据集大小 × 训练轮次 |
| 内存 | 模型参数 + Batch Size × 中间激活 |
| 存储 | 数据集大小 × checkpoint 数量 |

### Stage 12-13：自愈式实验执行

**沙箱执行环境**的行为由 `experiment` 配置段控制，默认约束相当紧：

```yaml
experiment:
  mode: "sandbox"
  time_budget_sec: 300             # 单次运行最长 300 秒
  max_iterations: 10               # 自愈循环最多 10 轮
  sandbox:
    python_path: ".venv/bin/python"
    allowed_imports: [math, random, json, csv, numpy, torch, sklearn]
    max_memory_mb: 4096
```

在这层约束之上，沙箱还有三个执行期防线：AST 校验拒绝硬编码指标的代码；实验 harness 不可变，生成代码改不了实验参数；输出检测到 NaN/Inf 立即快速失败并捕获部分结果。`allowed_imports` 白名单和 4GB 内存上限共同限制了生成代码的爆炸半径——生成的代码可能因为模型幻觉引入恶意或低质依赖，白名单把可执行范围收窄到科学计算常用库。

**ITERATIVE_REFINE** 自愈循环：

```text
实验运行失败 → 诊断错误类型
     │
     ├── 类型 1：导入错误 → 修复 import
     ├── 类型 2：维度不匹配 → 修复 tensor shape
     ├── 类型 3：NaN/Inf → 调整学习率/初始化
     └── 类型 4：超时 → 减少数据量/简化模型
     │
     ↓
最多 10 轮迭代（max_iterations: 10），
或未完成条件占比降到 50% 以下仍无法继续（min_completion_rate: 0.5）
```

按错误类型分派修复策略。自由修复（把错误信息直接丢给 LLM）容易陷入"改一处坏另一处"的循环，分类修复让每轮迭代有明确的成功条件。

**抗伪造机制**：

```python
@dataclass
class VerifiedRegistry:
    """Registry of all numbers grounded in experiment data."""
    values: dict[float, str] = field(default_factory=dict)  # 数值 → 实验来源
    condition_names: set[str] = field(default_factory=set)  # 真实跑过的条件组
    primary_metric: float | None = None

    def add_value(self, value: float, source: str) -> None:
        """注册一个实验产出的数值，同时登记舍入与百分比变体。"""
        ...

    def is_verified(self, number: float, tolerance: float = 0.01) -> bool:
        """按 1% 相对容差回查数值是否来自真实实验。"""
        ...

    def lookup(self, number: float) -> str | None:
        """返回数值的实验来源描述，未注册则返回 None。"""
        ...
```

（摘自 `researchclaw/pipeline/verified_registry.py`，省略了字段与变体注册细节。）

`VerifiedRegistry` 在 Stage 17 写作前从实验产物构建：每个实验产出的数值连同 1-4 位小数的舍入变体、百分比换算（×100/÷100）一并注册。写作阶段系统把真实结果表直接注入论文，后续质量门控再把论文文本中的数字逐个回查注册表——对不上且无法落地的数字会被拒绝。幻觉引用则走另一条路径：验证不通过的引用从正文和 bibliography 中自动移除。这从机制上封死了 LLM 在写作时编造实验数据的空间。

## Phase F-G：分析与论文写作

### Stage 14-15：结果分析与决策

**RESULT_ANALYSIS** 用多代理辩论从互补视角审视结果，ML 领域的默认角色是 **optimist（乐观者）/ skeptic（怀疑者）/ methodologist（方法论者）**——分别负责发掘结果的价值、挑战结论的有效性、检查实验方法是否站得住。单一视角容易漏掉问题：统计显著但实际意义微弱的结果，只看 p 值会被当作成功。

**RESEARCH_DECISION** 三路决策：

| 决策 | 条件 | 后续动作 |
|------|------|---------|
| **PROCEED** | 结果支持假设 | 进入论文写作阶段 |
| **REFINE** | 结果部分支持 | 返回 Stage 13 优化实验 |
| **PIVOT** | 结果不支持假设 | 返回 Stage 8 重新生成假设 |

`PIVOT` 路径是管道设计上的一个重要取舍——它允许放弃当前假设回到 Stage 8，避免强行写一篇负面结果的论文。这增加了管道的诚实度，但也意味着运行时间和成本不可预测。

### Stage 16-19：论文写作流水线

**论文结构**（按 IMRAD 格式，字数目标来自官方 prompt 配置，总计 5000-6500 词）：

| 章节 | 字数目标（词） | 核心内容 |
|------|---------------|---------|
| Abstract | 150-250 | 问题、方法、结果、贡献 |
| Introduction | 800-1000 | 研究背景、动机、贡献点 |
| Related Work | 600-800 | 按主题分组，对比已有方法与局限 |
| Method | 1000-1500 | 形式化定义、算法描述、复杂度分析 |
| Experiments | 800-1200 | 数据集、基线、超参、指标、硬件信息 |
| Results | 600-800 | 主结果表、显著性讨论、消融分析 |
| Discussion | 400-600 | 关键发现解读、与已有工作对比 |
| Limitations | 200-300 | 范围、数据、方法的诚实评估 |
| Conclusion | 200-300 | 总结与未来工作 |

**长度守卫机制**：修订阶段被明确要求维持甚至增加论文长度，各章节不得低于字数下限，全文低于 4000 词会被判定为严重不达标。原因是 LLM 在修订时容易过度删减，导致章节缺失。

**PEER_REVIEW** 模拟顶会审稿：prompt 要求至少 2 个审稿人视角（ML 领域用 NeurIPS/ICML 审稿人 prompt 库），项目自带的评分 rubric 按五个维度打 1-10 分：

| 维度 | 考察点 |
|------|--------|
| Novelty | 想法是否真正新颖（10 分 = breakthrough） |
| Rigor | 实验设计是否严谨、是否报告统计显著性 |
| Clarity | 写作是否组织清晰、易于跟随 |
| Impact | 对领域的潜在影响力 |
| Experiments | 基线是否公平、消融是否完整 |

审稿的核心检查是"方法论-证据一致性"：论文声明与实验证据逐条对照，回查 `VerifiedRegistry`，确保每个数字都有实验来源。这是抗伪造机制在写作阶段的延伸。

## Phase H：质量保障与发布

### Stage 20：质量门控

`QUALITY_GATE` 是最后一个门控节点，实现上有两个值得注意的设计：

1. **作者模型不能自评**。写论文的模型不给自己打分——只要配置了独立评审模型，门控就用它来裁判，避免"自己夸自己"。
2. **与实验摘要交叉核对**。门控会加载内容最丰富的实验摘要，连同论文一起送给评审模型；实验状态是 failed 且没有产出指标时，论文表格里出现的任何数字都按伪造处理、严重扣分。

通过阈值由 `research.quality_threshold` 控制（默认 4.0，10 分制），未达标则打回，门控拒绝时管道回滚。

### Stage 21-22：知识归档与多格式导出

`KNOWLEDGE_ARCHIVE` 把本次运行的知识归档（默认 Markdown 后端，可切 Obsidian），供 `MetaClaw` 提取教训。`EXPORT_PUBLISH` 输出多格式产物：

```text
artifacts/rc-20260310-143200-a1b2c3/
├── paper_final.md              # Markdown 终稿
├── paper.tex                   # LaTeX 源码
├── references.bib              # BibTeX 引用
├── charts/                     # 自动生成图表
│   ├── accuracy_comparison.pdf
│   └── ablation_study.pdf
└── code/                       # 开源代码包
    ├── experiment.py
    └── requirements.txt
```

**支持的会议模板**（由 `export.target_conference` 选择）：

- NeurIPS 2025
- ICLR 2026
- ICML 2026

### Stage 23：四层引用验证

LLM 容易幻觉引用——生成看起来合理但实际不存在的论文。单层验证（如只查 arXiv ID）会被"ID 存在但标题不匹配"绕过。四层验证逐级收紧：

| 验证层 | 数据源 | 检查内容 |
|--------|--------|---------|
| **第一层** | arXiv API | 验证 arXiv ID 存在性 |
| **第二层** | CrossRef / DataCite | 验证 DOI 对应的元数据 |
| **第三层** | Semantic Scholar + arXiv | 标题检索与匹配度：相似度 ≥ 0.80 判 VERIFIED，0.50-0.80 判 SUSPICIOUS，< 0.50 判 HALLUCINATED |
| **第四层** | LLM 相关性评分 | 评估每条引用与研究主题的相关性（0.0-1.0） |

验证结果分为 VERIFIED / SUSPICIOUS / HALLUCINATED / SKIPPED 四档，写在 `verification_report.json` 里。判为 HALLUCINATED 的引用会被 `annotate_paper_hallucinations` 从正文 `\cite{}` 和 Markdown 引用中自动移除，再清理残留标点——这就是"低相关性引用自动从 bibliography 剔除"的落地位置。

## v0.5.0：多领域实验代理与 ARC-Bench

v0.5.0（2026-05-19）带来两个标志性更新：实验执行阶段（Stage 10-13）不再只走默认 ML 沙箱，而是能根据研究领域路由到专业执行器；同时发布了 ARC-Bench——一个 55 主题的开放自主研究基准。

### 多领域实验代理

AutoResearchClaw 的实验执行层原本只有"ML 沙箱"（`CodeAgent` + Python + PyTorch）。v0.5.0 按领域拆出多类专业执行器：

| 领域 | 执行器 | 执行方式 | 示例场景 |
|------|--------|---------|---------|
| **ML / 深度学习** | CodeAgent（默认） | 本地沙箱 · Python/PyTorch | 图像分类、RLHF、Transformer 变体 |
| **高能物理 (HEP)** | ColliderAgent | Magnus 云 · Lagrangian → FeynRules → MadGraph5 → Delphes | 新粒子探测、LHC 数据分析 |
| **生物学** | BiologyAgent（COBRApy） | 基因组尺度代谢建模 | 细菌代谢通路、酶反应网络 |
| **统计学** | SimulationAgent | 模拟研究 · 蒙特卡洛 | A/B 测试框架、贝叶斯估计 |
| **化学 / 材料** | Docker 通用执行器 | 自定义 Docker 镜像 | 分子动力学、晶体结构预测 |

领域识别由 `detect_domain` 完成，策略分三级：先做关键词匹配（快、确定性强），歧义主题交给 LLM 分类，两者都命中时按混合规则定主领域、标次要领域。用户也可以用 `--profile` 或 `project.profile:` 强制指定领域；实际执行器由 `experiment.mode` 决定（`sandbox` / `docker` / `ssh_remote` / `collider_agent` / `biology_agent` / `stat_agent` 等）。

这个改动解决的问题很实际：ML 沙箱白名单里根本没有 `feynrules` 或 `cobrapy`，跨领域研究在旧版里会卡在 Stage 10 永远过不了。

HEP 模式还有一个人机协作细节值得单独说：`project.profile=hep_ph` 且 `experiment.mode=collider_agent` 时，Stage 10（代码生成）会变成 HITL 门控——管道把物理 prompt（`collider_plan.md`）在编辑器里打开，人工审核或修改后 ColliderAgent 才开跑；拒绝则退回 Stage 9 重新设计实验，Stage 8 的假设保持不变。物理模拟成本高，这一道人工闸门省的是真金白银。

### ARC-Bench：55 主题开放基准

ARC-Bench（Autonomous Research Capability Benchmark）是目前少见的专门面向"自主研究"的开放基准。它没有像 MMLU 那样用多选题测试知识，而是给出 **55 个完整的研究问题**，每个主题附带一份 manifest（研究问题 + 数据条件 + 评估指标 + 数据集）和一份可分级评分的 rubric：

| 领域 | 主题数 | 示例 |
|------|--------|------|
| ML | 25 | "Self-supervised pretraining on tabular data" |
| HEP | 10 | "Dark matter detection at LHC Run 3" |
| 量子 | 10 | "Variational quantum eigensolver for drug docking" |
| 生物学 | 7 | "CRISPR off-target prediction with foundation models" |
| 统计 | 3 | "Bootstrap confidence intervals for A/B test" |

基准的设计哲学是：自主研究系统的能力不能靠"答对一个问题"衡量，要看它能不能走完整条研究路径——从文献综述、假设生成、实验设计到论文写作。评分分两层：**每主题科学 rubric**（权重 100，考察实验是否真跑了、数字是否正确、结论是否支持假设）加一张统一的**论文质量 meta rubric**（19 个叶子项、4 个桶：paper-content 权重 30、code-orchestration 18、visual-layout 17、content-accuracy 21，其中 no-fabrication 是 content-accuracy 下的叶子项），综合后约 54% 看科学、46% 看论文质量。

读这些数字时要留意边界：ARC-Bench 量的是单次运行的产物质量，同一系统重复运行存在方差；跨系统对比要求相同的 judge 配置，不同 LLM 后端跑出的分数不能直接混着排座次。

基准数据已同步到 Hugging Face（[AIMING-Lab-UNC/ARC-Bench](https://huggingface.co/datasets/AIMING-Lab-UNC/ARC-Bench)），代码在 `experiments/arc_bench/` 目录下。

## Human-in-the-Loop Co-Pilot 系统

v0.4.0 引入的 HITL 系统把管道从纯自主运行改为人类-AI 协作。纯自主模式的问题是：研究假设、基线选择、论文结构这些决策需要领域判断，LLM 单独做容易产出看似合理但学术上站不住的结果。

### 干预模式

| 模式 | 命令 | 暂停点 | 适用场景 |
|------|------|--------|---------|
| **Full Auto** | `--auto-approve` | 从不 | 快速探索 |
| **Gate Only** | `--mode gate-only` | 3 个门控（Stage 5/9/20） | 轻度监督 |
| **Checkpoint** | `--mode checkpoint` | 每个 Phase 边界（8 个检查点） | 阶段性审核 |
| **Co-Pilot** | `--mode co-pilot` | 关键阶段 + SmartPause | **官方主推** |
| **Step-by-Step** | `--mode step-by-step` | 每个阶段之后 | 学习管道 |
| **Express** | `--mode express` | 只看 3 个最关键门控 | 资深用户 |
| **Custom** | `--mode custom` | 用 `stage_policies` 逐阶段定义策略 | 精细控制 |

默认关闭：不配置 `hitl.enabled: true` 或 `--mode` 时，管道行为与 v0.3.x 完全一致。

暂停的管道可以在另一个终端接续操作：

```bash
researchclaw attach artifacts/rc-2026-xxx    # 接管暂停的管道
researchclaw status artifacts/rc-2026-xxx    # 查看管道与 HITL 状态
researchclaw approve artifacts/rc-2026-xxx --message "LGTM"
researchclaw reject artifacts/rc-2026-xxx --reason "Missing key baseline"
researchclaw guide artifacts/rc-2026-xxx --stage 9 --message "Use ResNet-50 as primary baseline"
```

### 三大协作工坊

#### Idea Workshop（Stage 7-8）

人类研究者与 AI 就研究假设进行深度讨论：

```text
研究者 > Hypothesis 1 最有前景，但需要更具体。
         噪声应建模为随机正则化器，
         需要与 Dropout、Label Smoothing、MixUp 对比。

AI > 更新后的假设：
     "我们从理论上将量子门噪声表征为结构化随机正则化器，
     并经验验证其性能优于 Dropout、Label Smoothing 和 MixUp
     在小样本分类任务上的表现。"

     基线已更新：+ Dropout, + Label Smoothing, + MixUp, + CutMix
```

#### Baseline Navigator（Stage 9）

AI 推荐基线方法，人类添加领域专业知识：

```text
AI > 推荐的基线：
     [AI] ResNet-50（标准图像分类基线）
     [AI] ViT-B/16（Transformer 基线）
     [AI] Dropout（正则化基线）

研究者 > 添加 Label Smoothing 和 MixUp 作为基线，
         并添加 STL-10 数据集。

AI > 已更新。当前检查清单：
     [✓] 基线：5 个（ResNet-50, ViT-B/16, Dropout, Label Smoothing, MixUp）
     [✓] 数据集：3 个（CIFAR-10, CIFAR-100, STL-10）
     [✓] 指标：accuracy, F1
```

#### Paper Co-Writer（Stage 16-19）

支持三种协作模式：

- **AI-first**：AI 写草稿，人类编辑
- **Human-first**：人类写关键段落，AI 扩展和润色
- **Interleaved**：交替协作，人类写 Method，AI 写 Related Work

### SmartPause：置信度驱动的动态暂停

`SmartPause` 在固定门控之外动态决定某个阶段的产出是否需要人工过目。真实机制不是简单的阈值判断，而是把四个信号加权合成一个置信分：

```python
class ConfidenceSignal:
    quality_score: float            # PRM 或启发式的产出质量分（权重 0.30）
    confidence_score: float         # LLM 自评估置信度（权重 0.25）
    novelty_risk: float             # 产出越新颖风险越高（权重 0.15，取反）
    historical_rejection_rate: float # 该阶段历史被拒比例（权重 0.10，取反）
    criticality: float              # 阶段关键度（权重 0.20，取反）

class SmartPause:
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold

    def should_pause(self, signal: ConfidenceSignal) -> bool:
        return signal.overall_confidence < self.threshold
```

（摘自 `researchclaw/hitl/smart_pause.py`，权重与阶段关键度表为真实配置。）

阶段关键度是逐阶段标定的：Stage 15（RESEARCH_DECISION）和 Stage 20（QUALITY_GATE）关键度最高（0.7），归档、导出这类低风险阶段只有 0.1。直觉上这很合理——假设取舍和放行决策错不得，而"导出文件"错了大不了重跑。

## MetaClaw：跨运行自进化学习

LLM 没有跨会话记忆——每次运行都是独立的，上次踩过的坑这次还会踩。`MetaClaw` 解决的就是这个问题：把每次运行的失败和警告转化为可复用的技能文件，注入后续运行的 LLM Prompt。

### 工作原理

```text
运行 N 执行 → 捕获失败/警告作为 Lesson
                      ↓
          MetaClaw Lesson → Skill 转换
                      ↓
          arc-* Skill 文件存储在 ~/.metaclaw/skills/
                      ↓
运行 N+1 → build_overlay() 将 Skills 注入每个 LLM Prompt
                      ↓
          LLM 避免已知陷阱 → 更高质量、更少重试
```

### 实验结果

以下数据来自项目作者报告的受控 A/B 实验（相同主题、相同 LLM、相同配置），具体实验设置详见仓库文档：

| 指标 | 基线 | +MetaClaw | 提升 |
|------|------|-----------|------|
| Stage 重试率 | 10.5% | 7.9% | **-24.8%** |
| REFINE 循环次数 | 2.0 | 1.2 | **-40.0%** |
| Pipeline 阶段完成率 | 18/19 | 19/19 | **+5.3%** |
| 鲁棒性综合分 | 0.714 | 0.845 | **+18.3%** |

`REFINE` 循环次数下降 40% 是最显著的改进——这说明 MetaClaw 注入的技能主要在帮助 LLM 一次性生成正确的实验代码，减少自愈循环的触发。

读这组数字要留意两点：综合分是作者定义的加权指标（完成率 40% + 重试降低 30% + REFINE 效率 30%），不是行业通用分数；实验在单主题上做 A/B，样本量小，+18.3% 不能直接外推成普遍提升幅度。MetaClaw 是可选项（`metaclaw_bridge.enabled: true` 开启），关闭时管道行为不变。

## Sentinel 看门狗与 Claim Verification

这套系统有两道容易被混在一起的防线：一个保障"管道进程活着"，一个保障"论文内容真实"。分开看更清楚。

### Sentinel 看门狗：进程级守护

仓库根目录的 `sentinel.sh` 是一个进程看门狗，解决的问题是：一次运行要跑几个小时，半夜崩了没人管。管道每完成一个阶段就写一份 `heartbeat.json`（含 PID、最近阶段、时间戳）；Sentinel 周期性检查这份心跳，发现心跳过期（默认 300 秒）且进程已死就自动重启管道，最多重试 5 次，连续失败后进入 360 秒冷却，避免无意义的重启风暴。检查间隔、过期阈值、重试上限都可用环境变量调整（`SENTINEL_CHECK_INTERVAL` / `SENTINEL_STALE_THRESHOLD` / `SENTINEL_MAX_RETRIES` / `SENTINEL_COOLDOWN`）。

需要说明的是，README 把"NaN/Inf 检测、论文声明-证据一致性、引用相关性评分、抗伪造"统称为 Sentinel 的质量监控职责，但这些检查在代码里实际分布在各自的位置：NaN/Inf 检测在实验沙箱，数字一致性在 `VerifiedRegistry` 与质量门控，引用评分在四层验证器。Sentinel 本身管的是进程存活，不是内容质量。

### Claim Verification（内联事实校验）

`ClaimVerification` 是 v0.4.0 引入的一段内联逻辑——它从 AI 生成的论文文本中提取所有事实性声明，逐条回查已收集的文献和 `VerifiedRegistry`：

```text
AI 生成文本（示意）："我们的方法在 STL-10 上达到 92.3% 准确率，超过当前 SOTA。"
                    ↓ ClaimVerification 提取
声明列表：
  [1] "准确率 92.3%" → 回查 VerifiedRegistry ✅（来自真实实验运行）
  [2] "超过当前 SOTA" → 回查 Related Work 章节的 SOTA 表格 → ⚠️ 表格显示 SOTA 是 93.1%
                    ↓
  标记 [2] 为 UNGROUNDED，不进入最终论文
```

这和四层引用验证是互补关系：四层验证管"引用"，ClaimVerification 管"论文正文里的每个数字和声明"。

### 4 轮论文质量审计

Stage 20 附近的论文定稿阶段还有一道 v0.2.0 引入的审计流程：论文要过 4 轮检查——AI-slop 检测（识别模板腔和机器生成痕迹）、7 维度评审打分、NeurIPS checklist 核对、最终 pass。写作阶段的修订循环也会检查"是否存在样板短语、是否读起来像 AI 生成"，检查不过就重写。

### 其他值得知道的特性

| 特性 | 说明 |
|------|------|
| **Knowledge Base** | 每次运行自动构建 6 类结构化知识库（decision / experiment / finding / literature / question / review），后续运行可查询 |
| **Branch Exploration** | 在假设阶段分叉管道，并行探索多个研究方向，结果并排对比后择优合并 |
| **ALHF 干预学习** | 记录人类在 HITL 中的 approve/reject 模式，用于优化后续的暂停决策 |
| **SHA256 可复现** | 所有阶段产物带校验和与不可变 manifest，支持多级撤销 |

## OpenClaw 集成

AutoResearchClaw 与 OpenClaw 集成，实现"零配置"研究体验——用户不需要手动 clone 仓库、安装依赖、配置 API key，OpenClaw 会自动处理。

### 最简使用方式

```text
1️⃣  分享 GitHub 仓库 URL 给 OpenClaw
2️⃣  OpenClaw 自动读取 RESEARCHCLAW_AGENTS.md → 理解管道
3️⃣  说出："Research [你的研究主题]"
4️⃣  完成 —— OpenClaw 自动处理 clone、install、config、run
```

### OpenClaw Bridge

```yaml
openclaw_bridge:
  use_cron: true              # ⏰ 定时研究运行
  use_message: true           # 💬 进度通知（Discord/Slack/Telegram）
  use_memory: true            # 🧠 跨会话知识持久化
  use_sessions_spawn: true    # 🔀 为并发阶段生成并行子会话
  use_web_fetch: true         # 🌐 文献综述期间实时网络搜索
  use_browser: false          # 🖥️ 基于浏览器的论文收集
```

### ACP 代理支持

AutoResearchClaw 可以使用任何 ACP 兼容的编码代理作为 LLM 后端，这意味着用户不需要单独申请 OpenAI 或 Anthropic 的 API key，可以直接复用已有的编码代理订阅：

| 代理 | 命令 | 说明 |
|------|------|------|
| Claude Code | `claude` | Anthropic |
| Codex CLI | `codex` | OpenAI |
| Copilot CLI | `gh` | GitHub |
| Gemini CLI | `gemini` | Google |
| OpenCode | `opencode` | SST |
| Kimi CLI | `kimi` | Moonshot |

```yaml
llm:
  provider: "acp"
  acp:
    agent: "claude"   # 任何 ACP 兼容的代理 CLI 命令
    cwd: "."          # 代理的工作目录
  # 无需 base_url 或 api_key —— 代理自行处理认证
```

ACP 模式下代理通过 acpx 通信，在全部 23 个阶段维持单一持久会话。

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/aiming-lab/AutoResearchClaw.git
cd AutoResearchClaw

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装
pip install -e .
```

### 配置

```bash
# 交互式配置（推荐）
researchclaw setup
researchclaw init

# 或手动配置
cp config.researchclaw.example.yaml config.arc.yaml
```

最小配置示例：

```yaml
project:
  name: "my-research"

research:
  topic: "Your research topic here"

llm:
  base_url: "https://api.openai.com/v1"
  api_key_env: "OPENAI_API_KEY"
  primary_model: "gpt-4o"
  fallback_models: ["gpt-4o-mini"]

experiment:
  mode: "sandbox"
  sandbox:
    python_path: ".venv/bin/python"
```

### 运行

```bash
# 完整自主运行 —— 无需人工干预
researchclaw run --config config.arc.yaml --topic "Your research idea" --auto-approve

# Co-Pilot 模式 —— 在关键决策点协作
researchclaw run --config config.arc.yaml --topic "Your research idea" --mode co-pilot
```

### 输出

输出目录：`artifacts/rc-YYYYMMDD-HHMMSS-<hash>/deliverables/`

```text
├── paper_final.md              # 完整论文（Markdown）
├── paper.tex                   # LaTeX 源码
├── references.bib              # BibTeX 引用
├── verification_report.json    # 4 层引用验证报告
├── reviews.md                  # 多代理评审记录
├── experiment runs/            # 生成的代码 + 沙箱结果
└── charts/                     # 自动生成的图表
```

## 与同类项目对比

| 特性 | AutoResearchClaw (v0.5) | GPT-Researcher | Karpathy autoresearch | AI Scientist (Sakana AI) |
|------|------------------------|----------------|----------------------|--------------------------|
| 产出物 | 完整论文 + LaTeX + 实验代码 | 研究报告（文献综述为主） | 训练实验日志与更优模型 | 完整论文 + 自动评审 |
| 实验执行 | 沙箱 + 自愈 + 多领域代理 | 无 | 单 GPU nanochat 训练循环 | 有（自动化代码实验） |
| 论文数字绑定实验真值 | VerifiedRegistry（1% 容差回查 + 结果表注入） | 不涉及 | 指标即训练日志（val_bpb） | 无同类机制 |
| 引用验证 | 4 层（arXiv / DOI / 标题匹配 / LLM 相关性） | 无 | 无论文产物 | 检索式引用，无分层验证 |
| 跨运行学习 | MetaClaw 技能注入 + 30 天衰减 | 无 | 无 | 无 |
| HITL 协作 | 7 种模式 + SmartPause + 三大工坊 | 无 | 人工维护 program.md | 无 |
| ARC-Bench 基准 | ✅ 55 主题跨学科开放基准 | ❌ | ❌ | ❌ |
| LaTeX 导出 | ✅ NeurIPS / ICLR / ICML 模板 | ❌ | ❌ | ✅ |

四者的定位差异：**GPT-Researcher 停在文献综述**，产出报告，不跑实验也不写论文；**Karpathy autoresearch** 把"研究"收敛为单 GPU 训练循环——代理改 `train.py`、跑 5 分钟训练、看 val_bpb、保留或丢弃，验证了自主实验的可行性，但不生产论文；**AI Scientist** 能端到端生成论文并自动评审，但论文数字与实验真值之间没有注册与回查机制。AutoResearchClaw 的核心差异点在**实验执行（沙箱 + 自愈 + 多领域代理）和抗伪造链路（VerifiedRegistry + 落地校验 + 四层引用验证）**——这条链路决定了它产出的论文能否作为可复现的学术成果提交给顶会。

## 采用建议

### 适合的场景

- **探索性研究**：快速验证一个想法是否值得深入，Full Auto 模式下几小时就能拿到初步论文
- **教学场景**：Step-by-Step 模式可以用来学习研究流程的各个阶段
- **重复性实验**：MetaClaw 积累的技能库在同类研究主题上会持续生效

### 不适合的场景

- **需要原创性突破的研究**：23 阶段流程更适合增量研究，突破性假设很难通过多代理辩论的可行性筛选
- **涉及敏感数据的研究**：沙箱环境的 `allowed_imports` 白名单可能不支持私有数据集的访问方式
- **需要严格同行评审的研究**：`PEER_REVIEW` 是 LLM 模拟的，不能替代真实审稿

### 采用顺序

1. 先用 Full Auto 模式跑一个简单主题，观察管道行为和输出质量
2. 切换到 Gate Only 模式，在 3 个门控点审核，感受人工干预的效果
3. 生产环境用 Co-Pilot 模式，配合 SmartPause 处理低置信度场景
4. 长期使用开启 MetaClaw，积累技能库提升后续运行质量

### 成本控制

```yaml
hitl:
  cost_budget_usd: 50.0        # 达到预算阈值时告警/暂停
  notifications:
    channels: ["terminal"]     # terminal | slack | webhook
  timeouts:
    default_human_timeout_sec: 86400  # 24 小时超时
    auto_proceed_on_timeout: false
```

预算守卫在花费达到预算的 50%、80%、100% 时分别告警，到 100% 管道暂停，不会超支。运行成本主要消耗在 LLM 调用上，取决于主题复杂度、`ITERATIVE_REFINE` 触发次数和所选模型——建议先按上面方式设一个硬预算跑几次，再根据自己的消耗曲线调整。

### 技能库扩展

```bash
# 列出所有加载的技能
researchclaw skills list

# 安装自定义技能
researchclaw skills install /path/to/my-skill/

# 校验技能格式
researchclaw skills validate ./my-skill
```

内置 20 个技能覆盖科学写作（IMRAD 结构、引文格式）、文献搜索（系统评价、PRISMA 方法论）、化学（RDKit 分子分析、SMILES、药物发现）、生物学等；单个技能在 frontmatter 里加 `enabled: false` 即可禁用。社区还有 150+ 学科技能可用（[K-Dense-AI/claude-scientific-skills](https://github.com/K-Dense-AI/claude-scientific-skills)），也可以把 `SKILL.md` 放进 `.claude/skills/` 直接加载。

## 资源链接

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/aiming-lab/AutoResearchClaw |
| 方法论文 | https://arxiv.org/abs/2605.20025 |
| 英文 README | https://github.com/aiming-lab/AutoResearchClaw/blob/main/README.md |
| 中文文档 | https://github.com/aiming-lab/AutoResearchClaw/blob/main/docs/README_CN.md |
| HITL 指南 | https://github.com/aiming-lab/AutoResearchClaw/blob/main/docs/HITL_GUIDE.md |
| 领域集成指南 | https://github.com/aiming-lab/AutoResearchClaw/blob/main/docs/DOMAIN_INTEGRATION_GUIDE.md |
| 集成指南 | https://github.com/aiming-lab/AutoResearchClaw/blob/main/docs/integration-guide.md |
| 论文展示 | https://github.com/aiming-lab/AutoResearchClaw/blob/main/docs/showcase/SHOWCASE.md |
| ARC-Bench 数据集 | https://huggingface.co/datasets/AIMING-Lab-UNC/ARC-Bench |
| Discord 社区 | https://discord.gg/u4ksqW5P |

## 自测题

回答下面 5 个问题，检验你是否理解了 AutoResearchClaw 的核心机制：

1. **AutoResearchClaw 的 23 个阶段如何分成 Phase A-H？每个 Phase 的核心职责是什么？**
   - 参考答案：Phase A-B（研究定位与文献发现）→ Phase C（知识综合与假设生成）→ Phase D-E（实验设计与执行）→ Phase F-G（分析与论文写作）→ Phase H（质量保障与发布）。每个 Phase 包含 2-6 个阶段，用门控节点分隔。

2. **VerifiedRegistry 如何防止 LLM 编造实验数据？你能判断一篇论文是否可复现吗？**
   - 参考答案：VerifiedRegistry 从实验运行产物构建，把每个实验数值连同舍入与百分比变体注册进表；写作阶段注入真实结果表，质量门控再把论文中的数字按 1% 相对容差逐个回查，无法落地的数字会被拒绝。判断可复现性：检查论文是否附带 `verification_report.json` 与实验摘要，确认每个数字都能对上实验记录、代码可在沙箱中重新运行。

3. **如果你输入研究想法"量子门噪声作为正则化器"，完整流程会经过哪些关键阶段？**
   - 参考答案：Stage 1（TOPIC_INIT）→ Stage 3-6（文献发现）→ Stage 7（SYNTHESIS）→ Stage 8（HYPOTHESIS_GEN，多代理辩论）→ Stage 9（EXPERIMENT_DESIGN [门控]）→ Stage 10-13（实验执行与自愈）→ Stage 14-15（决策）→ Stage 16-19（论文写作与评审）→ Stage 20-23（质量门控、导出、引用验证）。

4. **MetaClaw 的自进化机制是什么？为什么它能减少 Stage 重试率和 REFINE 循环次数？**
   - 参考答案：MetaClaw 把每次运行的失败和警告转化为可复用的技能文件（arc-* Skill），存储在 ~/.metaclaw/skills/，后续运行时通过 build_overlay() 注入每个 LLM Prompt。减少重试的原因：技能文件帮助 LLM 避免已知陷阱，一次性生成正确的实验代码。

5. **对比 AutoResearchClaw 与 GPT-Researcher / Karpathy autoresearch / AI Scientist，为什么通用研究工具难以产出可复现的学术成果？**
   - 参考答案：GPT-Researcher 停在文献综述，不跑实验不写论文；Karpathy autoresearch 只做单 GPU 训练循环，不生产论文；AI Scientist 能写论文但没有把数字绑定到实验真值的机制。可复现的学术成果需要同时满足三件事：真实实验执行、论文数字可回溯到实验记录、引用可验证到真实文献——AutoResearchClaw 的沙箱执行 + VerifiedRegistry + 四层引用验证正是对着这三件事设计的。

---

## 进阶路径

完成本文阅读后，按以下四个阶段深化理解：

- [ ] **阶段一：跑通 Full Auto 模式** — 用一个简单主题（如"图像分类中的数据增强"）跑完整管道，观察各阶段输出和质量
- [ ] **阶段二：理解门控节点** — 梳理 Stage 5、9、20 三个门控的阻塞条件，理解 Human-in-the-Loop 如何在关键决策点介入
- [ ] **阶段三：测试 Co-Pilot 模式** — 在关键决策点人工审核，感受人机协作在研究流程中的价值
- [ ] **阶段四：开启 MetaClaw 积累技能库** — 观察第二次运行是否减少了 Stage 重试率和 REFINE 循环次数

## 练习

### 练习一：跑通 Full Auto 模式

**目标**：用一个简单主题跑完整管道，观察各阶段输出和质量。

**步骤**：
1. 安装 AutoResearchClaw（`git clone` + `pip install -e .`）
2. 用 Full Auto 模式跑一个简单主题（如"图像分类中的数据增强"）
3. 观察各阶段输出，特别是 `VerifiedRegistry` 如何防止数据造假
4. 检查输出的论文质量，评估是否达到可提交水平

**通过标准**：完整跑通管道，理解各阶段的输出和质量。

### 练习二：测试 Co-Pilot 模式

**目标**：在关键决策点人工审核，感受人机协作在研究流程中的价值。

**步骤**：
1. 用 Co-Pilot 模式跑一个研究想法
2. 在 Stage 8（Hypothesis Generation）和 Stage 9（Experiment Design）两个门控点人工审核
3. 感受 Human-in-the-Loop 如何在关键决策点介入
4. 对比 Full Auto 模式和 Co-Pilot 模式的输出质量差异

**通过标准**：成功在门控点介入，理解 HITL 的价值。

### 练习三：验证 VerifiedRegistry 机制

**目标**：理解 VerifiedRegistry 如何防止 LLM 编造实验数据。

**步骤**：
1. 阅读仓库中 `researchclaw/pipeline/verified_registry.py` 的实现，重点看 `add_value` 的变体注册和 `is_verified` 的容差匹配
2. 尝试手动修改论文中的数字，看是否会被检测出来
3. 理解为什么这个机制能从根源上防止数据造假
4. 对比 AutoResearchClaw 与 GPT-Researcher 在抗伪造机制上的差异

**通过标准**：理解 VerifiedRegistry 的工作原理和价值。

## 资料口径说明

本文关键判断的取径方式（最近一次核实：2026-09-13）：

1. **23 阶段管道的划分和门控节点**：来自仓库 README 和代码实现（`researchclaw/pipeline/stages.py`），已验证与代码中的 Stage 定义一致。
2. **VerifiedRegistry 的抗伪造机制**：来自源码 `researchclaw/pipeline/verified_registry.py`（dataclass 实现、1% 容差、舍入/百分比变体注册）及 `_paper_writing.py` 中的结果表注入逻辑。
3. **MetaClaw 的自进化机制与实验数据**：来自 README MetaClaw 章节；综合分构成（完成率 40%/重试 30%/REFINE 效率 30%）来自同一章节的官方注释。
4. **v0.5.0 多领域代理**：路由机制来自 `researchclaw/domains/detector.py`（三级检测）与 `researchclaw/experiment/factory.py`（按 `experiment.mode` 选择执行器）；HEP 门控细节来自 README "HEP-ph Physics Mode" 章节；ARC-Bench 主题分布来自 v0.5.0 release notes，rubric 结构来自 `experiments/arc_bench/README.md`（19 叶子 4 桶，总权重 86）。
5. **干预模式、SmartPause、成本守卫**：来自 README HITL 章节与 `researchclaw/hitl/smart_pause.py`（阈值 0.7、五信号加权、阶段关键度表）；CLI 命令来自 README；2-4 小时/30-60 分钟耗时口径来自 `docs/HITL_GUIDE.md`。
6. **Sentinel 的定位**：来自仓库根目录 `sentinel.sh` 源码（心跳监控 + 自动重启，默认参数已列）；README 将若干质量检查归在 Sentinel 名下，本文已按代码实际归属拆分说明。
7. **论文字数与评分 rubric**：字数目标来自 `prompts.default.yaml`（各章节下限与 5000-6500 总目标）；五维 rubric 来自 `researchclaw/assessor/rubrics.py`；辩论角色来自 `researchclaw/prompts/ml.py`（hypothesis: innovator/pragmatist/contrarian；analysis: optimist/skeptic/methodologist）。
8. **引用验证分层**：来自 `researchclaw/literature/verify.py`（三层 API 验证 + 相似度阈值 0.80/0.50）与 `_review_publish.py` 的 `_check_citation_relevance`（LLM 相关性评分），四层合称与 README 描述一致。
9. **版本演进时间线**：逐个 release 对照 GitHub release notes 与 README News 章节。
10. **方法论文**：arXiv:2605.20025，2026-05-19 提交（v2 修订于 2026-05-23），README 首页引用。
11. **与同类项目的对比**：GPT-Researcher 定位为其官方仓库描述的深度研究报告工具；Karpathy autoresearch 定位核实自 `karpathy/autoresearch` 仓库描述与 README（"AI agents running research on single-GPU nanochat training automatically"，不生产论文）；AI Scientist 为 Sakana AI 开源的端到端研究系统，列入 AutoResearchClaw README 致谢。
12. **链接与观测数据**：仓库、文档、论文、数据集链接均已验证（2026-09-13）；Stars 14,408、Forks 1,669 为 2026-09-13 GitHub API 观测值。
