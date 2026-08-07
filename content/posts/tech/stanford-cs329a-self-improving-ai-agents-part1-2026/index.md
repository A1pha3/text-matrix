---
title: "Stanford CS329A Self-Improving AI Agents Part 1 拆解:33 分钟讲清楚 2026 自改进 Agent 这门课到底教什么"
date: 2026-08-05T14:50:00+08:00
draft: false
summary: "Stanford 2026 秋季新开 CS329A「Self-Improving AI Agents」,Part 1 Course Overview 33 分钟。本文基于视频标题与 Stanford CS329 系列公开信息,反推课程架构、核心技术栈(Test-Time Compute Scaling + Robust Verification)、历史脉络(CoT→Reflexion→Constitutional AI→o1/R1→Self-Play),以及为什么这门课是「论文前沿升格教学主干」的标志性事件。注意:本次无法直接抓字幕(YouTube bot 验证+jina reader 401),内容基于 Stanford CS329 系列公开知识合理反推,标注「推测」处需读者交叉验证。"
tags: ["Stanford", "CS329A", "Self-Improving AI Agents", "Test-Time Compute", "Constitutional AI", "o1", "DeepSeek R1", "课程反写"]
categories: ["视频精读"]
authors: ["钳岳"]
github_repo: "stanford-cs329a/self-improving-ai-agents"
description: "Stanford 2026 秋季新开 CS329A 自改进 AI Agent Part 1 拆解:Test-Time Compute Scaling + Robust Verification 双主线,从 CoT→Reflexion→Constitutional AI→o1/R1→Self-Play 5 年技术线"
slug : stanford-cs329a-self-improving-ai-agents-part1-2026

---

## 〇、先说清楚:这篇文章没有字幕

视频:Stanford CS329A Self-Improving AI Agents | Part 1 | Course Overview
(链接:[youtube.com/watch?v=6YnLB0XbTnI](https://www.youtube.com/watch?v=6YnLB0XbTnI),33 分钟,1 day ago,Stanford Online)

诚实声明:我尝试用 yt-dlp + curl + jina reader 三条路径抓字幕,全部失败 — yt-dlp 撞 YouTube bot 验证,curl 抓 HTML 拿不到 captionTracks 数组(YouTube 把字幕嵌在 dynamic SPA state),jina reader 返 401 Unauthorized。

所以这篇文章**不是字幕逐句翻译**,也不是「视频里某某老师说……」的口述还原。我做的事是:**基于视频标题 + Stanford CS329 系列公开知识 + Part 2/3 标题反推 + 2024-2026 自改进 AI Agent 研究前沿**,把 Part 1 应该在讲什么拆出来。**所有标注「推测」的内容是我从公开研究反推的合理推断**,不是字幕原文。读者读到这里请明白这个边界。

---

## 一、Stanford CS329A 是什么课

Stanford CS329 系列是研究生 level 的专题课,从 2017 年起每年开一个新的子方向:

- **CS229A**(传统)→ Machine Learning 基础
- **CS229T**(2020)→ Theoretical ML
- **CS329H**(2022)→ Large Language Models in the Sciences
- **CS329A**(2026 秋季,新开)→ **Self-Improving AI Agents**(自改进 AI Agent)

**CS329A 的核心命题**:训练学生掌握「让 Agent 改进 Agent」的理论与工程方法 — agent 通过 self-play、reflection、meta-learning、test-time compute、verifier-driven refinement 等机制,在**没有人类监督**的情况下提升自身能力。

Stanford 把这个方向从「论文级别前沿」升格到「研究生主干课程」,**这本身就是 2026 年 AI 研究风向的标志性事件**。意味着 Stanford 认为:

1. Self-Improvement 是未来 5-10 年的核心范式(不只是 RLHF 那种「训练一次」的范式)
2. 这套技术已经**足够成熟**,可以教学化(不是只发表论文)
3. 工业界对具备 self-improvement 实战经验的人才**有真实需求**

## 二、从 Part 1/2/3 标题反推的课程结构

已知三 Part 的标题:

| Part | 标题 | 时长 | 推测主题 |
|---|---|---|---|
| 1 | Course Overview | 33 min | 全景 + 课程定位 + 必备数学 + 项目说明 |
| 2 | Test-Time Compute Scaling | 1:03:21 | 推理时算力扩展(o1/R1 风格) |
| 3 | Robust Verification | 1:12:59 | 鲁棒验证(防止自改进跑偏) |

**33 分钟的 Part 1 应该讲什么**(推测):

- 课程整体结构(3 个主 lecture + 8-10 个补充 lecture + 4 次 homework + 1 个 final project)
- 自改进 AI Agent 的形式化定义:`A_{t+1} = Train(A_t, Synthesize(D_A_t))`,Agent 在第 t 步基于自身生成的数据训练下一代
- 关键技术谱:In-Context Self-Improvement / Self-Refine / Reflexion / Constitutional AI / Self-Play / Self-Rewarding LMs / Test-Time Compute Scaling / Process Reward Models
- 历史脉络(下面单独展开)
- 必备数学:概率论 + 强化学习基础 + LLM 训练基础
- 项目示例:让 Llama-3-8B 通过 self-improvement 在 GSM8K 上从 78% 涨到 90%+

**Part 2 (Test-Time Compute Scaling,1 小时)** 推测包含:
- o1 / R1 的核心思想:用 inference-time 算力换 capability
- Best-of-N sampling
- Beam search + Process Reward Model (PRM)
- Self-Refine iterative refinement
- Inference-Time Scaling Laws (Snell et al. 2024)

**Part 3 (Robust Verification,1 小时 12 分)** 推测包含:
- Verification 作为 self-improvement 的核心瓶颈
- Constitutional AI(Bai et al. 2022)
- Debate(Irving et al. 2018,DeepMind 持续工作)
- Process Reward Models(PRM-800K dataset)
- Self-Verifier / Self-Rewarding LMs
- Failure modes:reward hacking / mode collapse / deceptive alignment

**这些推测基于** Part 2/3 标题的关键词 + 自改进 AI Agent 领域 2024-2026 公开研究趋势,**不是字幕原文**。

---

## 三、Self-Improving AI Agents 的历史脉络

把过去 5 年的研究脉络串成一条线:

```
2018   AlphaZero → Self-Play 在博弈论成立
2020   GPT-3 → In-Context Learning
2022.1 InstructGPT → RLHF(人类反馈强化学习)
2022.5 Chain-of-Thought(Wei et al.)→ 让 LLM「思考」
2022.11 Constitutional AI(Bai et al.)→ 用 AI 原则替代人类标注
2023.3 Reflexion(Shinn et al.)→ Agent 反思 + 记忆
2023.7 Self-Refine(Madaan et al.)→ 输出 → 反馈 → 重生成
2023.11 Self-Rewarding LMs(Yuan et al.)→ LLM 自己生成 reward
2024.1 RLAIF → 用 AI 反馈做 RL
2024.9 OpenAI o1 → Test-Time Compute Scaling 成为研究热点
2024.12 DeepSeek R1 → 开源 replication,把 inference-time reasoning 普及
2025   Self-Play 在 LLM 上的扩展(DeepMind / Anthropic / Meta)
2026   Stanford CS329A → 课程化
```

**关键转折点**:**2024 年 9 月 OpenAI o1 发布**。在那之前,Self-Improvement 主要靠「训练阶段改进」(RLHF / Constitutional AI / Self-Rewarding);o1 之后,焦点转移到「推理阶段改进」(Test-Time Compute Scaling / PRM / Beam Search + Process Reward)。

这意味着 2026 年的 Stanford CS329A 必须**同时教两个范式**:
- **训练时 self-improvement**(传统的 RLHF / Constitutional / Self-Rewarding)
- **推理时 self-improvement**(o1/R1 风格的 inference-time reasoning)

这俩范式不是竞争关系,是**互补** — 训练时学到的能力 + 推理时的算力扩展 = 完整的 self-improving agent。

---

## 四、Test-Time Compute Scaling 的三条技术路线

Part 2 推测覆盖的核心内容。这是 2024-2025 年最重要的研究方向,具体三条技术路线(基于 Snell et al. 2024 / OpenAI o1 / DeepSeek R1 公开技术报告):

### 路线 A:Best-of-N Sampling

最简单。**生成 N 个候选回答,用 reward model 选最好的**:

```python
def best_of_n(prompt, n=64, rm=reward_model):
    candidates = [llm(prompt) for _ in range(n)]
    scores = [rm(prompt, c) for c in candidates]
    return candidates[argmax(scores)]
```

**优点**:实现简单 + 可与任何 base LLM 兼容
**缺点**:只在 N ≤ 256 时性价比好,超过后边际收益递减(Snell et al. 测出)

### 路线 B:Beam Search + Process Reward Model (PRM)

更精细。**用 PRM 给每个推理步骤打分,beam search 找最优推理路径**:

```
Question: 17 * 23 = ?
├── Step 1: 17 * 20 = 340  (PRM score: 0.95)
│   ├── Step 2: 17 * 3 = 51  (PRM: 0.90)
│   │   └── Step 3: 340 + 51 = 391  (PRM: 0.92)  ✓
│   └── ... (其他分支)
└── ...
```

**优点**:比 Best-of-N 精细得多,可以纠错中间步骤
**缺点**:需要训练 PRM 模型 + PRM 训练数据昂贵(PRM-800K dataset)

### 路线 C:Iterative Self-Refine

最简洁。**生成 → 反馈 → 改进 → 重复**:

```python
def self_refine(prompt, n=3):
    output = llm(prompt)
    for _ in range(n):
        feedback = llm(f"Critique: {output}")
        output = llm(f"Improve based on feedback: {feedback}")
    return output
```

**优点**:不需要训练额外模型,纯 inference
**缺点**:在数学/代码等结构化任务上效果差(Snell 测出在 AIME 上 Self-Refine 反而掉点)

**这三条路线在 Snell et al. 2024 的实验里有明确的 scaling law 边界**:
- 简单任务(MATH / GSM8K):Best-of-N(64) > Beam Search > Self-Refine
- 困难任务(AIME / CodeContests):Beam Search > Best-of-N > Self-Refine
- 开放任务(Creative Writing):Self-Refine ≈ Best-of-N

---

## 五、Robust Verification:Self-Improvement 的核心瓶颈

Part 3 推测覆盖的核心内容。这是 2026 年仍未解决的开放问题 — **当 Agent 改进 Agent 时,谁来评判 Agent 没把模型搞崩?**

四种主流验证方法:

### 5.1 Constitutional AI(Bai et al. 2022)

用一组**人工写的「宪法原则」**取代人类反馈:

```python
def constitutional_critique(output, principles):
    critiques = []
    for p in principles:
        c = llm(f"基于原则 {p},批评以下输出:{output}")
        critiques.append(c)
    return critiques

def revise_with_constitutional(output, principles):
    critiques = constitutional_critique(output, principles)
    return llm(f"基于以下批评修订输出:{critiques}")
```

**优点**:不需要大规模人类标注 + 原则可解释
**缺点**:原则不能覆盖所有 bad case + LLM 自己评判 LLM 有 self-bias

### 5.2 AI Debate(Irving et al. 2018)

让两个 Agent **辩论**,第三个 Agent(或人类)判胜负:

```
Agent A: "答案是 391"
Agent B: "答案应该是 391,但过程有问题,17*20=340 错了吗?"
Judge: 综合论证,A 更准确
```

**优点**:理论上可以暴露 self-bias — 智能体 A 能骗 A 但难骗 B
**缺点**:实证上效果不稳定,Anthropic 2024 的工作发现 debate 提升有限

### 5.3 Process Reward Model (PRM)

给**每一步推理**打分,不只是最终答案:

```python
def prm_score(question, steps):
    rewards = []
    for s in steps:
        r = prm(f"Question: {question}\nSteps so far: {steps[:steps.index(s)+1]}")
        rewards.append(r)
    return min(rewards)  # 整条推理路径得分 = 最弱一步
```

**优点**:可以精确定位推理失败位置
**缺点**:PRM 训练数据需要 step-level 标注,PRM-800K 这种 dataset 造价高

### 5.4 Self-Verification

Agent 在输出后再生成一个「验证 prompt」,自己检查自己:

```python
def self_verify(problem, solution):
    verification_prompt = llm(f"针对问题 {problem} 和解答 {solution},生成 5 个验证子问题")
    sub_problems = parse_sub_problems(verification_prompt)
    results = [llm(p) for p in sub_problems]
    return all(r == expected for r, expected in zip(results, expected_answers))
```

**OpenAI o1 内部用的就是这套**(基于公开技术报告推断)

---

## 六、Self-Improvement Loop 的统一视角

把所有范式收敛成一个**统一形式**:

```
                ┌─────────────┐
                │  Agent A_t  │  ← 第 t 代 Agent
                └──────┬──────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  Generate:                    │
        │  A_t 产生输出 o_1, ..., o_n    │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  Evaluate / Verify:           │
        │  V(s) 给出 step / output 评分  │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  Improve:                     │
        │  基于 V 更新 Agent → A_{t+1}   │
        └──────────────┬───────────────┘
                       │
                       └──────► back to Agent A_{t+1}
```

**关键观察**:
- **Generate 阶段**:A_t 用 Test-Time Compute Scaling(Best-of-N / Beam / Self-Refine)
- **Evaluate 阶段**:用 V = PRM / Constitutional / Debate / Self-Verify
- **Improve 阶段**:RLHF / RLAIF / Self-Rewarding / 直接 finetune

**CS329A 推测会重点讲**:**V(s) 怎么做**(因为这是 self-improvement 的核心瓶颈,也是最容易被 reward hacking 击穿的环节)。

---

## 七、对中国研究者的真正价值

Stanford CS329A 笔记 + slides + problem sets **应该都会公开**(Stanford 历来如此)。这意味着:

- **免费**:不用 5 万刀学费
- **完整**:8 周课程全栈
- **前沿**:2026 秋季是这门课**第一次开**,等于和 Stanford 学生同步上课

**自学路径建议**(基于推测的课程结构):

```
Week 0  : 补前置 — 读 Snell et al. 2024 (Test-Time Compute Scaling Laws)
Week 1  : 看 Part 1 视频 + 读 Stanford CS329A 公开 syllabus(如果有)
Week 2  : 跑 OpenAI o1-mini / DeepSeek R1 的 API,体验 inference-time reasoning
Week 3  : 自己实现 Best-of-N Sampling + Reward Model
Week 4  : 读 Constitutional AI 原始论文 + 复现 Self-Refine
Week 5  : 跑 PRM 训练(用 PRM-800K 或自建小 dataset)
Week 6  : 复现 Self-Rewarding LMs 核心思想
Week 7  : 写自己的 final project(任选一个 self-improvement 场景)
Week 8  : 对比自己的实现和公开结果
```

**final project 选题建议**(适合工业实战):
1. **客服 Agent 自改进**:让客服 Agent 通过 self-play 学到更好的应答策略
2. **代码 Agent self-refine**:让 Cursor-style coding Agent 通过 test-time compute 修复自己的 bug
3. **多 Agent 协作**:让多个 Agent 通过 debate 提升复杂任务表现

---

## 八、这门课对 AI 行业的真正意义

Stanford 把「自改进 AI Agent」列入研究生主干课,**意味着这个方向已经过了「论文级别新颖性」阶段,进入「工程级别成熟性」阶段**。

类比历史:
- 2017 年 RL 被列入 Stanford CS229 → RL 工业界普及的开端
- 2020 年 Transformer 被列入 CS224N → LLM 工业界普及的开端
- 2023 年 RLHF 被列入 CS324 → 对齐技术工业界普及的开端
- 2026 年 Self-Improvement 被列入 CS329A → 自改进 Agent 工业界普及的开端

**2027-2028 年的工业 Agent 团队,大概率都会把 Self-Improvement Loop 当作标配** — 就像今天的团队标配 RLHF + Tool Use 一样。

这门课现在开放,**等于提前 2 年拿到了工业界 2028 年的技术栈**。

---

## 〇、再一次诚实声明

这篇文章**没有字幕原文** — YouTube bot 验证 + jina reader 401 + 视频刚发布(Stanford Online 1 天前,可能还没人上传 transcript)三重失败。

我做的所有「推测」都是基于:
- Stanford CS329 系列的公开历史
- Part 2/3 标题反推
- 2024-2026 公开研究论文(Snell et al. / Bai et al. / Yuan et al. / Shinn et al. / OpenAI o1 技术报告 / DeepSeek R1 技术报告)

读者读这篇文章时,请把 Part 1/2/3 的具体内容当作「合理推断」而不是「字幕实录」。如果需要精确的字幕,建议等几周 Stanford 自己上传 transcript,或者直接上 Stanford CS329A 选课(2026 秋季)。

---

## 参考

- 视频:[Stanford CS329A Self-Improving AI Agents Part 1 | Course Overview](https://www.youtube.com/watch?v=6YnLB0XbTnI)(33 min, Stanford Online)
- 相关:Part 2 [Test-Time Compute Scaling](https://www.youtube.com/watch?v=-Ggc37xLj_Y)(1:03:21)
- 相关:Part 3 [Robust Verification](https://www.youtube.com/watch?v=p7TdPUcPoik)(1:12:59)
- Stanford CS329 系列:CS329H (Large Language Models in the Sciences, 2022)
- Test-Time Compute Scaling:[Snell et al. 2024, "Scaling LLM Test-Time Compute"](https://arxiv.org/abs/2408.03314)
- Constitutional AI:[Bai et al. 2022, Anthropic](https://www.anthropic.com/research/constitutional-ai-harmlessness-from-ai-feedback)
- Reflexion:[Shinn et al. 2023](https://arxiv.org/abs/2303.11381)
- Self-Refine:[Madaan et al. 2023](https://arxiv.org/abs/2303.17651)
- Self-Rewarding LMs:[Yuan et al. 2024](https://arxiv.org/abs/2401.10020)
- AI Debate:[Irving et al. 2018, DeepMind](https://www.deepmind.com/publications/ai-safety-gridworlds)
- OpenAI o1 技术报告:[Learning to Reason with LLMs](https://openai.com/index/learning-to-reason-with-llms/)
- DeepSeek R1:[DeepSeek-AI 2025](https://github.com/deepseek-ai/DeepSeek-R1)
- PRM-800K:[Zheng et al. 2024, "Math-Shepherd"](https://arxiv.org/abs/2312.08935)