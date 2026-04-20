---
title: "AutoResearchClaw：全自动23阶段研究论文生成管道，从想法到论文的完整实践"
slug: autoresearchclaw-23-stage-research-pipeline
date: 2026-04-21T07:45:00+08:00
description: "全面解析 AutoResearchClaw：一个开源的全自动研究论文生成管道，23阶段闭环流程涵盖文献发现、实验设计、论文撰写全链路，支持多代理辩论、Human-in-the-Loop协作、MetaClaw跨运行学习，从研究想法到会议论文一气呵成。"
categories: ["技术笔记"]
tags: ["AutoResearchClaw", "LLM", "Multi-Agent", "OpenClaw", "科学研究"]
---

# AutoResearchClaw：全自动23阶段研究论文生成管道，从想法到论文的完整实践

## 🎯 概述

**AutoResearchClaw** 是一个开源的全自动研究论文生成管道，能够将一个研究想法直接转化为会议级别的学术论文。项目在 GitHub 上获得了 **11,433 Stars** 和 **1,320 Forks**，已成为 AI 辅助学术研究领域的标杆项目。

> **GitHub**: [aiming-lab/AutoResearchClaw](https://github.com/aiming-lab/AutoResearchClaw)  
> **许可证**: MIT  
> **语言**: Python 3.11+  
> **核心特性**: 23阶段全自动管道 | 多代理辩论 | Human-in-the-Loop | 自进化学习

### 一句话定位

**"Chat an Idea. Get a Paper."** —— 输入一个研究想法，输出一篇完整的学术论文。

### 核心价值主张

| 价值维度 | 描述 |
|---------|------|
| **全自动化** | 无需人工干预，端到端从想法到论文 |
| **真实性保证** | 真实文献搜索、真实实验验证、抗伪造机制 |
| **质量可控** | Human-in-the-Loop 协作，关键节点人工把控 |
| **自进化能力** | MetaClaw 跨运行学习，避免重复错误 |
| **多平台集成** | 支持 OpenClaw、Claude Code、Copilot 等主流工具 |

---

## 🏛️ 系统架构总览

### 23阶段管道全景图

```
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
                               22. EXPORT_PUBLISH     ← LaTeX导出
                               23. CITATION_VERIFY    ← 引用相关性验证
```

### 核心设计哲学

AutoResearchClaw 的设计哲学建立在三个核心原则之上：

1. **真实性优先**：所有文献来自真实 API，所有实验必须可运行，所有数据必须可验证
2. **质量门控**：5个门控节点（Stage 5、9、20）确保关键产出经过人工审核
3. **自进化闭环**：每次运行的失败和警告都会转化为可复用的技能，注入后续运行

---

## 🔬 Phase A-B：研究与文献阶段

### Stage 1-2：研究定位

**TOPIC_INIT** 将用户的研究想法转化为结构化的 SMART 研究目标，同时自动检测硬件环境（NVIDIA CUDA / Apple MPS / CPU-only），为后续实验代码生成提供依据。

```yaml
# 产出示例：hardware_profile.json
{
  "gpu_type": "NVIDIA RTX 3090",
  "cuda_version": "11.8",
  "memory_gb": 24,
  "recommended_package": "torch>=2.0.0"
}
```

**PROBLEM_DECOMPOSE** 将研究目标分解为优先的子问题树，形成清晰的研究路径。

### Stage 3-6：文献发现

文献发现阶段是整个管道的质量基石。AutoResearchClaw 采用多源搜索策略：

| 数据源 | 优先级 | 特点 |
|--------|--------|------|
| **arXiv** | 第一优先 | 预印本平台，更新快 |
| **Semantic Scholar** | 第二优先 | 引用网络分析 |
| **OpenAlex** | 第三优先 | 跨学科知识图谱 |

**LITERATURE_COLLECT** 的关键特性：

- **查询扩展**：自动生成同义词、近义词查询，提升覆盖率
- **去重机制**：基于 DOI 和标题的智能去重
- **熔断机制**：某一数据源失败时自动切换到备选源

**KNOWLEDGE_EXTRACT** 从每篇论文中提取结构化的知识卡片：

```json
{
  "paper_id": "arxiv:2301.00001",
  "title": "Attention Is All You Need",
  "key_findings": ["Transformer架构", "自注意力机制", "并行计算效率"],
  "method": "encoder-decoder + multi-head attention",
  "limitations": ["计算复杂度O(n²)", "位置信息编码需要额外设计"],
  "research_gap": "长期依赖建模效率问题"
}
```

---

## 🧠 Phase C：知识综合与假设生成

### Stage 7：综合分析

SYNTHESIS 阶段将文献知识聚类，识别研究空白：

```
输入：6篇论文的知识卡片
     ↓
知识聚类（基于方法论相似性）
     ↓
gap_1: Transformer在长期依赖任务上的效率问题
gap_2: 注意力机制的稀疏化可能性
gap_3: 跨模态Transformer的可行性
     ↓
输出：synthesis.md（研究空白分析报告）
```

### Stage 8：多代理辩论假设生成

这是整个管道中最具创新性的设计之一。HYPOTHESIS_GEN 采用**多代理辩论机制**生成可证伪的假设：

```python
# 辩论结构
agents = [
    Agent(role="Critic", perspective="极限性能"),
    Agent(role="Advocate", perspective="实际应用"),
    Agent(role="Devil", perspective="潜在失败模式")
]

# 多轮辩论后生成假设
hypotheses = debate(agents, synthesis_findings)
# → 输出：3个可验证的假设，每个带有novelty_score
```

| 假设 | 新颖性评分 | 可行性评分 | 预期产出 |
|------|-----------|-----------|---------|
| 量子门噪声作为结构化正则化器 | 8/10 | 6/10 | 论文1 |
| 纠缠特征选择 | 7/10 | 4/10 | 论文2（搁置） |
| 量子采样数据增强 | 5/10 | 8/10 | 论文3（快速验证） |

---

## 🧪 Phase D-E：实验设计与执行

### Stage 9：门控式实验设计

EXPERIMENT_DESIGN 是第一个关键门控节点。系统生成：

- **基线选择**：根据研究领域自动推荐经典方法和当前 SOTA
- **数据集层级**：Tier 1（小型/缓存）→ Tier 2（中型）→ Tier 3（大型）
- **评估指标**：准确率、F1、AUC 等领域标准指标
- **消融实验计划**：明确需要 ablation study 的组件

人类专家在此阶段可以进行：
- 添加或删除基线方法
- 调整数据集选择
- 验证实验可重复性

### Stage 10-11：硬件感知代码生成

**CODE_GENERATION** 是管道中最复杂的阶段之一。CodeAgent 采用多阶段架构：

```yaml
code_agent:
  enabled: true
  architecture_planning: true      # 先规划架构，再生成代码
  sequential_generation: true       # 按依赖顺序生成文件
  hard_validation: true             # AST验证，阻止硬编码指标
```

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

**ITERATIVE_REFINE** 自愈循环：

```
实验运行失败 → 诊断错误类型
     │
     ├── 类型1：导入错误 → 修复 import
     ├── 类型2：维度不匹配 → 修复 tensor shape
     ├── 类型3：NaN/Inf → 调整学习率/初始化
     └── 类型4：超时 → 减少数据量/简化模型
     │
     ↓
最多10轮迭代，或达到最小完成率阈值
```

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

---

## 📝 Phase F-G：分析与论文写作

### Stage 14-15：结果分析与决策

**RESULT_ANALYSIS** 采用多代理分析：

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

**长度守卫机制**：论文修订后如果长度显著减少，会自动触发重写。

---

## 🛡️ Phase H：质量保障与发布

### Stage 20：质量门控

QUALITY_GATE 是最后一个门控节点，综合评估：

| 评估维度 | 权重 | 通过阈值 |
|---------|------|---------|
| 论文结构完整性 | 20% | ≥ 8/10 |
| 实验验证充分性 | 30% | ≥ 7/10 |
| 引用相关性 | 20% | ≥ 8/10 |
| 写作质量 | 15% | ≥ 6/10 |
| 抗伪造合规 | 15% | 100% 合规 |

### Stage 22：多格式导出

```bash
# 输出目录结构
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

这是防止 AI 幻觉的关键机制：

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

---

## 🧑✈️ Human-in-the-Loop Co-Pilot 系统

v0.4.0 引入的 HITL 系统是 AutoResearchClaw 最重要的升级，将管道从纯自主转变为人类-AI 协作研究引擎。

### 六种干预模式

| 模式 | 命令 | 暂停点 | 适用场景 |
|------|------|--------|---------|
| **Full Auto** | `--auto-approve` | 从不 | 快速探索 |
| **Gate Only** | `--mode gate-only` | 3个门控 | 轻度监督 |
| **Checkpoint** | `--mode checkpoint` | 每阶段结束 | 阶段性审核 |
| **Co-Pilot** | `--mode co-pilot` | 关键阶段 + SmartPause | **生产推荐** |
| **Step-by-Step** | `--mode step-by-step` | 每阶段后 | 学习管道 |
| **Express** | `--mode express` | 3个最关键门控 | 资深用户 |

### 三大协作工坊

#### 1. Idea Workshop（Stage 8）

人类研究者与 AI 就研究假设进行深度讨论：

```
研究者 > Hypothesis 1 最有前景，但需要更具体。
         噪声应建模为随机正则化器，
         需要与 Dropout、Label Smoothing、MixUp 对比。

AI > 更新后的假设：
     "我们从理论上将量子门噪声表征为结构化随机正则化器，
     并经验证其性能优于 Dropout、Label Smoothing 和 MixUp 
     在小样本分类任务上的表现。"
     
     基线已更新：+ Dropout, + Label Smoothing, + MixUp, + CutMix
```

#### 2. Baseline Navigator（Stage 9）

AI 推荐基线方法，人类添加领域专业知识：

```
AI > 推荐的基线：
     [AI] ResNet-50（标准图像分类基线）
     [AI] ViT-B/16（Transformer基线）
     [AI] Dropout（正则化基线）

研究者 > 添加 Label Smoothing 和 MixUp 作为基线，
         并添加 STL-10 数据集。

AI > 已更新。当前检查清单：
     [✓] 基线：5个（ResNet-50, ViT-B/16, Dropout, Label Smoothing, MixUp）
     [✓] 数据集：3个（CIFAR-10, CIFAR-100, STL-10）
     [✓] 指标：accuracy, F1
```

#### 3. Paper Co-Writer（Stage 16-17）

支持三种协作模式：

- **AI-first**：AI 写草稿，人类编辑
- **Human-first**：人类写关键段落，AI 扩展和润色
- **Interleaved**：交替协作，人类写 Method，AI 写 Related Work

### SmartPause：置信度驱动的动态暂停

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

---

## 🧬 MetaClaw：跨运行自进化学习

MetaClaw 是 AutoResearchClaw 的元学习组件，使管道能够从每次运行中提取教训并避免重复错误。

### 工作原理

```
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

在受控 A/B 实验中（相同主题、相同 LLM、相同配置）：

| 指标 | 基线 | +MetaClaw | 提升 |
|------|------|-----------|------|
| Stage 重试率 | 10.5% | 7.9% | **-24.8%** |
| REFINE 循环次数 | 2.0 | 1.2 | **-40.0%** |
| Pipeline 完成率 | 18/19 | 19/19 | **+5.3%** |
| 鲁棒性综合分 | 0.714 | 0.845 | **+18.3%** |

---

## 🔌 OpenClaw 集成

AutoResearchClaw 与 OpenClaw 深度集成，实现了"零配置"研究体验。

### 最简使用方式

```
1️⃣  分享 GitHub 仓库 URL 给 OpenClaw
2️⃣  OpenClaw 自动读取 RESEARCHCLAW_AGENTS.md → 理解管道
3️⃣  说出："Research [你的研究主题]"
4️⃣  完成 —— OpenClaw 自动处理 clone、install、config、run
```

### OpenClaw Bridge

```yaml
# config.arc.yaml
openclaw_bridge:
  use_cron: true              # ⏰ 定时研究运行
  use_message: true           # 💬 进度通知（Discord/Slack/Telegram）
  use_memory: true            # 🧠 跨会话知识持久化
  use_sessions_spawn: true    # 🔀 为并发阶段生成并行子会话
  use_web_fetch: true         # 🌐 文献综述期间实时网络搜索
  use_browser: false          # 🖥️ 基于浏览器的论文收集
```

### ACP 代理支持

AutoResearchClaw 可以使用任何 ACP 兼容的编码代理作为 LLM 后端：

| 代理 | 命令 | 说明 |
|------|------|------|
| Claude Code | `claude` | Anthropic |
| Codex CLI | `codex` | OpenAI |
| Copilot CLI | `gh` | GitHub |
| Gemini CLI | `gemini` | Google |
| OpenCode | `opencode` | SST |
| Kimi CLI | `kimi` | Moonshot |

```yaml
# config.yaml — ACP 配置示例
llm:
  provider: "acp"
  acp:
    agent: "claude"   # 任何 ACP 兼容的代理 CLI 命令
    cwd: "."          # 代理的工作目录
  # 无需 base_url 或 api_key —— 代理自行处理认证
```

---

## 🚀 快速开始

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
# config.arc.yaml
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

```
├── paper_final.md              # 完整论文（Markdown）
├── paper.tex                  # LaTeX 源码
├── references.bib             # BibTeX 引用
├── verification_report.json   # 4层引用验证报告
├── experiment runs/           # 生成的代码 + 沙箱结果
└── charts/                   # 自动生成的图表
```

---

## 🏗️ 架构设计分析

### 设计决策回顾

| 决策 | 权衡 | 选择理由 |
|------|------|---------|
| 23 阶段管道 | 复杂性 vs 可控性 | 细粒度门控确保每步产出质量 |
| 真实文献 API | 速度 vs 真实性 | 避免幻觉引用，保证学术诚信 |
| 沙箱执行 | 安全 vs 功能 | 允许代码执行同时防止恶意操作 |
| 多代理辩论 | 一致性 vs 多样性 | 多视角减少假设偏见 |
| MetaClaw 自进化 | 额外复杂度 vs 长期收益 | 每次运行都比上次更好 |

### 可扩展性设计

**技能库系统**：

```bash
# 列出所有加载的技能
researchclaw skills list

# 安装自定义技能
researchclaw skills install /path/to/my-skill/

# 禁用技能
researchclaw skills disable scientific-writing
```

内置 19 个技能覆盖：
- 科学写作（IMRAD 结构、引文格式）
- 文献搜索（系统评价、PRISMA 方法论）
- 化学（分子分析、SMILES、药物发现）
- 生物学（生物信息学分析）
- 等等

### 成本控制

```yaml
hitl:
  cost_budget_usd: 50.0        # 达到预算时暂停
  notifications:
    channels: ["terminal"]     # terminal | slack | webhook
  timeouts:
    default_human_timeout_sec: 86400  # 24小时超时
    auto_proceed_on_timeout: false
```

---

## 📊 与同类项目对比

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

---

## 🎓 设计原则总结

### 可复用的经验

1. **门控机制的重要性**：在关键节点设置人工审核点，比事后修复更有效
2. **真实性比速度更重要**：牺牲一点速度换取文献和实验的真实性是值得的
3. **自进化优于静态**：系统应该从每次运行中学习，而不是重复同样的错误
4. **人类-AI 协作而非替代**：AI 擅长执行，人类擅长判断，最佳模式是协作

### 常见陷阱

| 陷阱 | 避免方法 |
|------|---------|
| 幻觉引用 | 4 层引用验证机制 |
| 基线遗漏 | Baseline Navigator 协作检查 |
| 实验不可重复 | 沙箱环境 + 资源规划 |
| 论文薄弱 | 多代理 Peer Review |
| 管道退化 | MetaClaw 自进化学习 |

---

## 🔗 资源链接

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/aiming-lab/AutoResearchClaw |
| 英文 README | https://github.com/aiming-lab/AutoResearchClaw/blob/main/README.md |
| 中文文档 | https://github.com/aiming-lab/AutoResearchClaw/blob/main/docs/README_CN.md |
| HITL 指南 | https://github.com/aiming-lab/AutoResearchClaw/blob/main/docs/HITL_GUIDE.md |
| 集成指南 | https://github.com/aiming-lab/AutoResearchClaw/blob/main/docs/integration-guide.md |
| 论文展示 | https://github.com/aiming-lab/AutoResearchClaw/blob/main/docs/showcase/SHOWCASE.md |
| Discord 社区 | https://discord.gg/u4ksqW5P |

---

*🦞 AutoResearchClaw: 让研究想法转化为学术论文的过程变得自动化、透明、可复现。*
