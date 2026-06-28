---
title: "AutoResearchClaw：全自动 23 阶段研究论文生成管道，从想法到论文的完整实践"
slug: autoresearchclaw-23-stage-research-pipeline
aliases:
  - "/posts/tech/autoresearchclaw-full-autonomous-research-agent/"
date: "2026-04-21T07:45:00+08:00"
description: "全面解析 AutoResearchClaw：一个开源的全自动研究论文生成管道，23 阶段闭环流程涵盖文献发现、实验设计、论文撰写全链路，支持多代理辩论、Human-in-the-Loop 协作、MetaClaw 跨运行学习，从研究想法到会议论文一气呵成。"
categories: ["技术笔记"]
tags: ["AutoResearchClaw", "LLM", "Multi-Agent", "OpenClaw", "科学研究"]
---

# AutoResearchClaw：全自动 23 阶段研究论文生成管道，从想法到论文的完整实践

## 核心判断

AutoResearchClaw 把研究流程拆成 23 个可中断的阶段，关键价值在两件事：所有文献绑定真实 API（arXiv、Semantic Scholar、OpenAlex），所有论文数字必须通过 `VerifiedRegistry` 追溯到实验运行。这两点决定了它生成的论文能当学术产出，不只是 demo。

> **GitHub**: [aiming-lab/AutoResearchClaw](https://github.com/aiming-lab/AutoResearchClaw)
> **许可证**: MIT
> **语言**: Python 3.11+
> **核心特性**: 23 阶段全自动管道 | 多代理辩论 | Human-in-the-Loop | 自进化学习

> **GitHub 仓库**: [aiming-lab/AutoResearchClaw](https://github.com/aiming-lab/AutoResearchClaw)
>
> | 指标 | 数值 |
> |------|------|
> | ⭐ Stars | 13,609+ |
> | 🍴 Forks | 1,593+ |
> | 📜 License | MIT |
> | 💻 主要语言 | Python |
> | 📅 最后更新 | 2026-06-26 |

一句话定位：**"Chat an Idea. Get a Paper."** —— 输入一个研究想法，输出一篇完整的学术论文。

## 学习目标！

读完本文应能：

1. 说清 23 个阶段如何分成 Phase A-H，每个 Phase 的核心职责
2. 解释 `VerifiedRegistry` 如何防止 LLM 编造实验数据，能判断一篇论文是否可复现
3. 根据研究想法（如"量子门噪声作为正则化器"）说出完整的 23 阶段流转路径
4. 识别 MetaClaw 的自进化机制，理解"跨运行学习"在工程系统中的价值
5. 对比 AutoResearchClaw 与 GPT-Researcher / MiniMax 的差距，能解释为什么后者不能产出可复现的学术成果

## 目录

- [核心判断](#核心判断)
- [学习目标](#学习目标)
- [系统总览](#系统总览)
- [Phase A-B：研究与文献阶段](#phase-a-b 研究与文献阶段)
- [Phase C：知识综合与假设生成](#phase-c 知识综合与假设生成)
- [Phase D-E：实验设计与执行](#phase-d-e 实验设计与执行)
- [Phase F-G：分析与论文写作](#phase-f-g 分析与论文写作)
- [Phase H：质量保障与发布](#phase-h 质量保障与发布)
- [Human-in-the-Loop Co-Pilot 系统](#human-in-the-loop-co-pilot-系统)
- [MetaClaw：跨运行自进化学习](#metaclaw 跨运行自进化学习)
- [OpenClaw 集成](#openclaw-集成)
- [快速开始](#快速开始)
- [采用建议](#采用建议)
- [资源链接](#资源链接)
- [自测题](#自测题)
- [进阶路径](#进阶路径)

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

1. **Phase B 内部并行**：`SEARCH_STRATEGY` 和 `LITERATURE_COLLECT` 可以并行查询 arXiv、Semantic Scholar、OpenAlex 三个数据源，某一数据源失败时熔断切换到备选源。
2. **Phase E 自愈循环**：`EXPERIMENT_RUN` → `ITERATIVE_REFINE` 是一个最多 10 轮的循环，按错误类型（导入错误、维度不匹配、NaN/Inf、超时）分派修复策略，不是线性推进。
3. **Phase G 写作流水线**：`PAPER_OUTLINE` → `PAPER_DRAFT` → `PEER_REVIEW` → `PAPER_REVISION` 是串行，但 `PEER_REVIEW` 的多代理可以并行评分。

3 个门控节点（Stage 5 `LITERATURE_SCREEN`、Stage 9 `EXPERIMENT_DESIGN`、Stage 20 `QUALITY_GATE`）会阻塞管道，等待人工或自动审核。HITL 模式下还会在更多位置触发暂停。

### 任务流案例：从想法到论文

假设输入研究想法"量子门噪声能否作为结构化正则化器"，完整流程如下：

1. **Stage 1 `TOPIC_INIT`**：把想法转为 SMART 目标，检测到 NVIDIA RTX 3090、CUDA 11.8、24GB 显存
2. **Stage 3-6 文献发现**：从 arXiv 检索量子机器学习论文，提取知识卡片，识别已有方法和局限
3. **Stage 7 `SYNTHESIS`**：聚类后识别 gap——量子噪声的正则化效应未被系统研究
4. **Stage 8 `HYPOTHESIS_GEN`**：3 个代理（Critic/Advocate/Devil）辩论后生成 3 个假设，每个带 `novelty_score`
5. **Stage 9 `EXPERIMENT_DESIGN` [门控]**：人类审核基线（Dropout、Label Smoothing、MixUp），添加 STL-10 数据集
6. **Stage 10-13 实验执行**：`CodeAgent` 生成训练代码，沙箱运行，`ITERATIVE_REFINE` 修复维度不匹配
7. **Stage 14-15 决策**：结果支持假设 → `PROCEED`
8. **Stage 16-19 论文写作**：IMRAD 结构，`PEER_REVIEW` 检查方法论-证据一致性
9. **Stage 20 `QUALITY_GATE` [门控]**：综合评分通过
10. **Stage 22-23 导出**：LaTeX 终稿 + 4 层引用验证

Co-Pilot 模式下整个流程大约需要 4-8 小时，主要瓶颈在人类响应速度和实验运行时间。

## Phase A-B：研究与文献阶段

### Stage 1-2：研究定位

**TOPIC_INIT** 将用户的研究想法转化为结构化的 SMART 研究目标，同时自动检测硬件环境（NVIDIA CUDA / Apple MPS / CPU-only），为后续实验代码生成提供依据。硬件检测的意义在于：`CodeAgent` 生成代码时会根据 GPU 类型选择 `torch.cuda` 或 `torch.mps`，避免运行时才发现设备不匹配。

```yaml
产出示例：hardware_profile.json
{
  "gpu_type": "NVIDIA RTX 3090",
  "cuda_version": "11.8",
  "memory_gb": 24,
  "recommended_package": "torch>=2.0.0"
}
```

**PROBLEM_DECOMPOSE** 将研究目标分解为优先的子问题树，形成清晰的研究路径。

### Stage 3-6：文献发现

文献发现阶段是整个管道的质量基石。AutoResearchClaw 采用多源搜索策略，原因是单一数据源覆盖面不够，且任何 API 都可能临时不可用：

| 数据源 | 优先级 | 特点 |
|--------|--------|------|
| **arXiv** | 第一优先 | 预印本平台，更新快 |
| **Semantic Scholar** | 第二优先 | 引用网络分析 |
| **OpenAlex** | 第三优先 | 跨学科知识图谱 |

**LITERATURE_COLLECT** 的关键特性：

- **查询扩展**：自动生成同义词、近义词查询，提升覆盖率
- **去重机制**：基于 DOI 和标题的智能去重
- **熔断机制**：某一数据源失败时自动切换到备选源

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

`HYPOTHESIS_GEN` 采用多代理辩论机制生成可证伪的假设。单代理容易陷入自我确认——它会倾向于生成自己已经知道的假设。引入 Critic、Advocate、Devil 三个视角后，假设在生成阶段就要经受"极限性能""实际应用""潜在失败模式"三方面的质疑，输出更经得起后续实验检验：

```python
辩论结构
agents = [
    Agent(role="Critic", perspective="极限性能"),
    Agent(role="Advocate", perspective="实际应用"),
    Agent(role="Devil", perspective="潜在失败模式")
]

多轮辩论后生成假设
hypotheses = debate(agents, synthesis_findings)
→ 输出：个可验证的假设，每个带有 novelty_score
```

| 假设 | 新颖性评分 | 可行性评分 | 预期产出 |
|------|-----------|-----------|---------|
| 量子门噪声作为结构化正则化器 | 8/10 | 6/10 | 论文 1 |
| 纠缠特征选择 | 7/10 | 4/10 | 论文 2（搁置） |
| 量子采样数据增强 | 5/10 | 8/10 | 论文 3（快速验证） |

## Phase D-E：实验设计与执行

### Stage 9：门控式实验设计

`EXPERIMENT_DESIGN` 是第一个关键门控节点。在此处设门控的原因是：实验设计一旦确定，后续代码生成、资源规划、沙箱执行都会沿着这个方向走，错误越早发现成本越低。系统生成：

- **基线选择**：根据研究领域自动推荐经典方法和当前 SOTA
- **数据集层级**：Tier 1（小型/缓存）→ Tier 2（中型）→ Tier 3（大型）
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
  sequential_generation: true       # 按依赖顺序生成文件
  hard_validation: true             # AST 验证，阻止硬编码指标
```

`hard_validation` 会做 AST 检查，阻止代码里出现硬编码的指标数字——这是抗伪造的第一道防线，确保论文里的数字只能来自真实实验运行。

**RESOURCE_PLANNING** 估算实验所需资源：

| 资源类型 | 估算依据 |
|---------|---------|
| GPU 时间 | 模型参数量 × 数据集大小 × 训练轮次 |
| 内存 | 模型参数 + Batch Size × 中间激活 |
| 存储 | 数据集大小 ×  checkpoint 数量 |

### Stage 12-13：自愈式实验执行

**沙箱执行环境**：

```python
class SandboxHarness:
    def __init__(self, config):
        self.time_guard = TimeGuard(max_seconds=300)
        self.metric_validator = MetricValidator()
        self.memory_limit = 4 * 1024 * 1024 * 1024  # 4GB
        self.allowed_imports = ['math', 'random', 'numpy', 'torch']
    
    def run(self, code: str) -> ExperimentResult:
        # AST 验证：确保没有硬编码指标
        # 不可变 harness：防止代码修改实验参数
        # NaN/Inf 快速失败：检测到异常值立即终止
```

沙箱的 `allowed_imports` 白名单和 `memory_limit` 限制了生成代码的爆炸半径。生成的代码可能因为模型幻觉引入恶意或低质依赖，白名单机制把可执行范围收窄到科学计算常用库。

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
最多 10 轮迭代，或达到最小完成率阈值
```

按错误类型分派修复策略。自由修复（把错误信息直接丢给 LLM）容易陷入"改一处坏另一处"的循环，分类修复让每轮迭代有明确的成功条件。

**抗伪造机制**：

```python
class VerifiedRegistry:
    """
    确保论文中的数据来自真实实验
    """
    def __init__(self):
        self.verified_metrics = set()
        self.unverified_warnings = []
    
    def register(self, key: str, value: float, source: str):
        # 所有指标必须来自 experiment_run 或 ITERATIVE_REFINE
        # 手动添加的数据会被标记为 unverified
        if source in ALLOWED_SOURCES:
            self.verified_metrics.add(key)
        else:
            self.unverified_warnings.append(key)
    
    def validate(self, paper_text: str) -> ValidationResult:
        # 论文中的所有数字必须来自 verified_metrics
        # 未验证的数字会被替换为 [VERIFIED: X.X] 或警告
```

`VerifiedRegistry` 是论文写作阶段（Stage 16-19）的输入约束。论文里出现的每个数字都会被检查是否在 `verified_metrics` 中注册过，未注册的数字会被替换为 `[VERIFIED: X.X]` 标记或触发警告。这从机制上杜绝了 LLM 在写作时编造实验数据。

## Phase F-G：分析与论文写作

### Stage 14-15：结果分析与决策

**RESULT_ANALYSIS** 采用多代理分析，三个视角分别检查统计显著性、实际意义、与现有工作对比。单一视角容易漏掉问题——统计显著但实际意义微弱的结果，单看 p 值会被当作成功：

```python
analysis_agents = [
    Agent(perspective="统计显著性"),
    Agent(perspective="实际意义"),
    Agent(perspective="与现有工作对比")
]

analysis_report = multi_agent_debate(results, agents)
```

**RESEARCH_DECISION** 三路决策：

| 决策 | 条件 | 后续动作 |
|------|------|---------|
| **PROCEED** | 结果支持假设 | 进入论文写作阶段 |
| **REFINE** | 结果部分支持 | 返回 Stage 13 优化实验 |
| **PIVOT** | 结果不支持假设 | 返回 Stage 8 重新生成假设 |

`PIVOT` 路径是管道设计上的一个重要取舍——它允许放弃当前假设回到 Stage 8，避免强行写一篇负面结果的论文。这增加了管道的诚实度，但也意味着运行时间和成本不可预测。

### Stage 16-19：论文写作流水线

**论文结构**（按 IMRAD 格式）：

| 章节 | 字数目标 | 核心内容 |
|------|---------|---------|
| Abstract | 150-250 | 问题、方法、结果、贡献 |
| Introduction | 800-1000 | 研究背景、动机、贡献点 |
| Related Work | 1000-1500 | 已有方法、差距分析 |
| Method | 1500-2000 | 技术方案、理论分析 |
| Experiments | 1500-2000 | 设置、结果、统计检验 |
| Conclusion | 300-500 | 总结、局限性、未来工作 |

**PEER_REVIEW** 模拟顶会审稿：

```yaml
review_rubric:
  - 评分维度: ["原创性", "技术深度", "实验完整性", "写作质量"]
  - 评分范围: 1-10
  - 检查项:
      - 所有基线是否包含？
      - 消融实验是否充分？
      - 论文声明与实验证据是否一致？
```

`PEER_REVIEW` 的检查项"论文声明与实验证据是否一致"会回查 `VerifiedRegistry`，确保论文里的每个数字都有实验来源。这是抗伪造机制在写作阶段的延伸。

**长度守卫机制**：论文修订后如果长度显著减少，会自动触发重写。原因是 LLM 在修订时容易过度删减，导致章节缺失。

## Phase H：质量保障与发布

### Stage 20：质量门控

`QUALITY_GATE` 是最后一个门控节点，综合评估：

| 评估维度 | 权重 | 通过阈值 |
|---------|------|---------|
| 论文结构完整性 | 20% | ≥ 8/10 |
| 实验验证充分性 | 30% | ≥ 7/10 |
| 引用相关性 | 20% | ≥ 8/10 |
| 写作质量 | 15% | ≥ 6/10 |
| 抗伪造合规 | 15% | 100% 合规 |

抗伪造合规要求 100%，其他维度允许阈值通过——这个设计取舍反映了项目的优先级：可以接受论文写得一般，但不能接受数据造假。

### Stage 21-22：知识归档与多格式导出

`KNOWLEDGE_ARCHIVE` 把本次运行的知识归档，供 `MetaClaw` 提取教训。`EXPORT_PUBLISH` 输出多格式产物：

```bash
输出目录结构
artifacts/rc-20260310-143200-a1b2c3/
├── paper_final.md              # Markdown 终稿
├── paper.tex                  # LaTeX 源码
├── references.bib             # BibTeX 引用
├── charts/                    # 自动生成图表
│   ├── accuracy_comparison.pdf
│   └── ablation_study.pdf
└── code/                      # 开源代码包
    ├── experiment.py
    └── requirements.txt
```

**支持的会议模板**：

- NeurIPS 2025
- ICLR 2026
- ICML 2026

### Stage 23：四层引用验证

LLM 容易幻觉引用——生成看起来合理但实际不存在的论文。单层验证（如只查 arXiv ID）会被"ID 存在但标题不匹配"绕过。四层验证逐级收紧：

| 验证层 | 数据源 | 检查内容 |
|--------|--------|---------|
| **第一层** | arXiv API | 验证 arXiv ID 存在性 |
| **第二层** | CrossRef / DataCite | 验证 DOI 对应的元数据 |
| **第三层** | Semantic Scholar | 验证标题匹配度 |
| **第四层** | LLM Relevance | 评估引用与论文内容相关性 |

```python
class CitationVerifier:
    def verify(self, citation: Citation) -> VerificationResult:
        # Layer 1: arXiv ID check
        arxiv_valid = self.check_arxiv_id(citation.arxiv_id)
        
        # Layer 2: DOI metadata
        doi_valid = self.check_doi(citation.doi)
        
        # Layer 3: Title match
        title_similarity = self.check_title_match(
            citation.title, 
            citation.extracted_from
        )
        
        # Layer 4: LLM relevance
        relevance_score = self.llm_judge_relevance(
            citation.claim,
            citation.full_text
        )
        
        return VerificationResult(
            layers_passed=sum([arxiv_valid, doi_valid, ...]),
            relevance_score=relevance_score
        )
```

## Human-in-the-Loop Co-Pilot 系统

v0.4.0 引入的 HITL 系统把管道从纯自主运行改为人类-AI 协作。纯自主模式的问题是：研究假设、基线选择、论文结构这些决策需要领域判断，LLM 单独做容易产出看似合理但学术上站不住的结果。

### 六种干预模式

| 模式 | 命令 | 暂停点 | 适用场景 |
|------|------|--------|---------|
| **Full Auto** | `--auto-approve` | 从不 | 快速探索 |
| **Gate Only** | `--mode gate-only` | 3 个门控 | 轻度监督 |
| **Checkpoint** | `--mode checkpoint` | 每阶段结束 | 阶段性审核 |
| **Co-Pilot** | `--mode co-pilot` | 关键阶段 + SmartPause | **生产推荐** |
| **Step-by-Step** | `--mode step-by-step` | 每阶段后 | 学习管道 |
| **Express** | `--mode express` | 3 个最关键门控 | 资深用户 |

### 三大协作工坊

#### Idea Workshop（Stage 8）

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

`SmartPause` 在固定门控之外，根据上下文置信度动态触发暂停。低置信度信号包括假设新颖性过低、基线缺失标准方法、实验超时率过高。这解决了固定门控无法覆盖所有风险点的问题：

```python
class SmartPause:
    def __init__(self, hitl_config):
        self.confidence_threshold = 0.7
        self.low_confidence_signals = [
            "novelty_score < 0.5",
            "baseline_missing_standard_method",
            "experiment_timeout_rate > 30%"
        ]
    
    def should_pause(self, context: StageContext) -> bool:
        # 基于上下文的置信度决定是否暂停
        confidence = self.calculate_confidence(context)
        return confidence < self.confidence_threshold
```

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
| Pipeline 完成率 | 18/19 | 19/19 | **+5.3%** |
| 鲁棒性综合分 | 0.714 | 0.845 | **+18.3%** |

`REFINE` 循环次数下降 40% 是最显著的改进——这说明 MetaClaw 注入的技能主要在帮助 LLM 一次性生成正确的实验代码，减少自愈循环的触发。

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
config.arc.yaml
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
config.yaml — ACP 配置示例
llm:
  provider: "acp"
  acp:
    agent: "claude"   # 任何 ACP 兼容的代理 CLI 命令
    cwd: "."          # 代理的工作目录
  # 无需 base_url 或 api_key —— 代理自行处理认证
```

## 快速开始

### 安装

```bash
克隆仓库
git clone https://github.com/aiming-lab/AutoResearchClaw.git
cd AutoResearchClaw

创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

安装
pip install -e .
```

### 配置

```bash
交互式配置（推荐）
researchclaw setup
researchclaw init

或手动配置
cp config.researchclaw.example.yaml config.arc.yaml
```

最小配置示例：

```yaml
config.arc.yaml
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
完整自主运行 —— 无需人工干预
researchclaw run --config config.arc.yaml --topic "Your research idea" --auto-approve

Co-Pilot 模式 —— 在关键决策点协作
researchclaw run --config config.arc.yaml --topic "Your research idea" --mode co-pilot
```

### 输出

输出目录：`artifacts/rc-YYYYMMDD-HHMMSS-<hash>/deliverables/`

```text
├── paper_final.md              # 完整论文（Markdown）
├── paper.tex                  # LaTeX 源码
├── references.bib             # BibTeX 引用
├── verification_report.json   # 4 层引用验证报告
├── experiment runs/           # 生成的代码 + 沙箱结果
└── charts/                   # 自动生成的图表
```

## 与同类项目对比

| 特性 | AutoResearchClaw | GPT-Researcher | MiniMax |
|------|------------------|----------------|---------|
| 研究管道阶段 | 23 阶段 | ~5 阶段 | ~10 阶段 |
| 引用验证 | 4 层验证 | 无 | 无 |
| 实验执行 | 沙箱+自愈 | 无 | 无 |
| 多代理辩论 | ✅ | ❌ | ✅ |
| MetaClaw 自进化 | ✅ | ❌ | ❌ |
| HITL 协作 | ✅ | ❌ | ❌ |
| LaTeX 导出 | ✅ | ❌ | ✅ |
| OpenClaw 集成 | ✅ | ❌ | ❌ |

GPT-Researcher 停在文献综述阶段，不生成实验和论文；MiniMax 覆盖更多阶段但没有引用验证和自愈执行。AutoResearchClaw 的差异点在实验执行和抗伪造机制——这两个特性决定了它能否产出可复现的学术成果。

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
  cost_budget_usd: 50.0        # 达到预算时暂停
  notifications:
    channels: ["terminal"]     # terminal | slack | webhook
  timeouts:
    default_human_timeout_sec: 86400  # 24 小时超时
    auto_proceed_on_timeout: false
```

`cost_budget_usd` 是硬上限——达到预算时管道会暂停，不会超支。一次完整运行的成本主要消耗在 LLM 调用上，使用 GPT-4o 级别模型大约 $5-$50，取决于实验复杂度和 `ITERATIVE_REFINE` 循环次数。

### 技能库扩展

```bash
列出所有加载的技能
researchclaw skills list

安装自定义技能
researchclaw skills install /path/to/my-skill/

禁用技能
researchclaw skills disable scientific-writing
```

内置 19 个技能覆盖：

- 科学写作（IMRAD 结构、引文格式）
- 文献搜索（系统评价、PRISMA 方法论）
- 化学（分子分析、SMILES、药物发现）
- 生物学（生物信息学分析）
- 等等

## 资源链接

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/aiming-lab/AutoResearchClaw |
| 英文 README | https://github.com/aiming-lab/AutoResearchClaw/blob/main/README.md |
| 中文文档 | https://github.com/aiming-lab/AutoResearchClaw/blob/main/docs/README_CN.md |
| HITL 指南 | https://github.com/aiming-lab/AutoResearchClaw/blob/main/docs/HITL_GUIDE.md |
| 集成指南 | https://github.com/aiming-lab/AutoResearchClaw/blob/main/docs/integration-guide.md |
| 论文展示 | https://github.com/aiming-lab/AutoResearchClaw/blob/main/docs/showcase/SHOWCASE.md |
| Discord 社区 | https://discord.gg/u4ksqW5P |
## 自测题

回答下面 5 个问题，检验你是否理解了 AutoResearchClaw 的核心机制：

1. **AutoResearchClaw 的 23 个阶段如何分成 Phase A-H？每个 Phase 的核心职责是什么？**
   - 参考答案：Phase A-B（研究定位与文献发现）→ Phase C（知识综合与假设生成）→ Phase D-E（实验设计与执行）→ Phase F-G（分析与论文写作）→ Phase H（质量保障与发布）。每个 Phase 包含 2-6 个阶段，用门控节点分隔。

2. **VerifiedRegistry 如何防止 LLM 编造实验数据？你能判断一篇论文是否可复现吗？**
   - 参考答案：VerifiedRegistry 要求论文中的所有数字必须来自真实实验运行（experiment_run 或 ITERATIVE_REFINE），手动添加的数据会被标记为 unverified。判断可复现性：检查论文是否包含所有实验的 VerifiedRegistry 日志，以及代码是否可在沙箱中重新运行。

3. **如果你输入研究想法"量子门噪声作为正则化器"，完整流程会经过哪些关键阶段？**
   - 参考答案：Stage 1（TOPIC_INIT）→ Stage 3-6（文献发现）→ Stage 7（SYNTHESIS）→ Stage 8（HYPOTHESIS_GEN，多代理辩论）→ Stage 9（EXPERIMENT_DESIGN [门控]）→ Stage 10-13（实验执行与自愈）→ Stage 14-15（决策）→ Stage 16-19（论文写作与评审）→ Stage 20-23（质量门控、导出、引用验证）。

4. **MetaClaw 的自进化机制是什么？为什么它能减少 Stage 重试率和 REFINE 循环次数？**
   - 参考答案：MetaClaw 把每次运行的失败和警告转化为可复用的技能文件（arc-* Skill），存储在 ~/.metaclaw/skills/，后续运行时通过 build_overlay() 注入每个 LLM Prompt。减少重试的原因：技能文件帮助 LLM 避免已知陷阱，一次性生成正确的实验代码。

5. **对比 AutoResearchClaw 与 GPT-Researcher / MiniMax，为什么后两者不能产出可复现的学术成果？**
   - 参考答案：GPT-Researcher 停在文献综述阶段，不生成实验和论文；MiniMax 覆盖更多阶段但没有引用验证和自愈执行。AutoResearchClaw 的差异点在实验执行（沙箱+自愈）和抗伪造机制（VerifiedRegistry + 四层引用验证），这两个特性决定了它能否产出可复现的学术成果。

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
1. 阅读 `VerifiedRegistry` 的代码实现
2. 尝试手动修改论文中的数字，看是否会被检测出来
3. 理解为什么这个机制能从根源上防止数据造假
4. 对比 AutoResearchClaw 与 GPT-Researcher 在抗伪造机制上的差异

**通过标准**：理解 VerifiedRegistry 的工作原理和价值。

## 资料口径说明

本文关键判断的取径方式：

1. **23 阶段管道的划分和门控节点**：来自仓库 README 和代码实现，已验证与代码中的 Stage 定义一致。

2. **VerifiedRegistry 的抗伪造机制**：来自代码实现（`VerifiedRegistry` 类），已验证它能防止论文中的数字来自非实验运行。

3. **MetaClaw 的自进化机制**：来自代码实现和项目文档，实验结果数据来自作者报告的受控 A/B 实验。

4. **与同类项目的对比**：来自各项目的 README 和功能对比，已验证准确性。

5. **链接有效性**：仓库、文档、论文链接均已验证（2026-06-26），Discord 社区链接有效。
