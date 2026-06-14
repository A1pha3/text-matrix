---
title: "SkillOpt：微软联合上交复旦同济，让AI Skills实现「强化学习式」自动化优化"
date: "2026-05-27T16:30:00+08:00"
slug: "skillopt-microsoft-self-evolving-agent-skills"
description: "微软联合上海交大、复旦、同济发布SkillOpt框架，首次将技能（Skill）视为AI Agent的外部可训练状态，通过独立优化器模型实现文本空间的bounded edit优化，在52个评估单元中全部取得最佳或并列最佳，GPT-5.5直接对话准确率飙升23.5分。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Skill", "Prompt优化", "微软", "文本空间优化", "强化学习", "机器学习"]
hiddenFromHomePage: false
---

🦞 钳岳星君 · 2026 年 5 月 27 日

---

## 引言：Skill 不应该是「一次性写好」的静态产物

当前 AI Agent 的技能（Skill）开发模式本质上仍然停留在手工时代：工程师凭借经验编写 Skill，运行几次发现没有 bug 就算验收通过。这种模式存在三个根本性问题：

1. **无反馈闭环**：Skill 写完后无法根据实际执行效果自动改进
2. **无安全保障**：随意重写 Skill 可能引入新的错误或破坏已有正确的规则
3. **无系统训练**：缺乏一套可重复、可审计、可量化的优化流程

微软联合上海交通大学、复旦大学、同济大学等机构发布了一篇重要论文——**SkillOpt: Executive Strategy for Self-Evolving Agent Skills**，首次提出将 Skill 视为 AI Agent 的外部可训练状态，通过类似深度学习优化器的范式对 Skill 进行系统化训练。

> 论文核心观点："我们主张，Skill 应当作为 Agent 的外部冻结状态的『训练』对象，并且训练过程还要『让权重空间优化具有可重复性』！"

---

## 1. 核心思想：将 Skill 视为外部可训练的权重

### 1.1 传统 Skill 开发的问题

| 方法 | 描述 | 问题 |
|------|------|------|
| 手工编写 | 工程师凭经验编写，一次性完成 | 依赖个人经验，无法保证最优 |
| 一次生成 | 用 LLM 一次性生成 Skill，不再修改 | 缺乏反馈，无法迭代优化 |
| 随意自修 | 简单让模型自己修改 Skill | 无验证环节，可能越改越差 |

论文指出，以上三种方法**没有任何一种**表现得像一个真正的深度学习优化器——它们都无法可靠地在反馈基础上提升起点。

### 1.2 SkillOpt 的核心洞察

SkillOpt 的核心思想是：**将 Skill 文档（skill document）作为外部状态，用训练模型权重的方式进行优化**。

类比深度学习中的权重优化：

| 深度学习概念 | SkillOpt 对应 | 含义 |
|-------------|-------------|------|
| 权重（Weights） | Skill 文档 | 外部可修改的状态 |
| 梯度（Gradient） | 编辑方向（edit direction） | 从轨迹中提取的修改信号 |
| 学习率（Learning Rate） | 编辑预算（Edit Budget Lt） | 限制每次更新的步长 |
| 验证集（Validation） | 验证门控（Validation Gate） | 只有提升验证集分数才接受 |
| 动量（Momentum） | 慢/元更新（Slow/Meta Update） | 跨 epoch 保持稳定方向 |

论文设计了一个**独立的优化器模型（optimizer model）**，这个模型读取 Agent 执行任务的轨迹，根据试错表现对 Skill 进行编辑操作（增加、删除、替换文本）。关键在于：**每一次编辑都必须在独立的验证集上通过分数检验，只有得分更高的变更才会被保留**。

这与大模型的强化学习过程（如 PPO）如出一辙——不是直接修改权重，而是通过反馈信号引导优化方向。

---

## 2. 技术架构：SkillOpt 的四大核心组件

### 2.1 整体流程图

```
训练数据 D_tr → Rollout Batch（目标模型执行任务）
     ↓
轨迹轨迹（Trajectories）
     ↓
Minibatch Reflection（优化器模型分析成功/失败）
     ↓
结构化编辑（Add/Delete/Replace）
     ↓
聚合与排序（按编辑预算Lt裁剪）
     ↓
候选Skill（candidate skill）
     ↓
验证门控（Validation Gate）→ 验证集D_sel评分
     ↓
通过 → 更新best_skill.md
拒绝 → 进入Rejected-Edit Buffer（负面反馈）
```

### 2.2 组件一：Rollout Evidence（前向传播）

在每个优化步骤中，**冻结的目标模型**使用当前 Skill 执行一批训练任务（从训练集 D_tr 采样）。每个任务产生一个**轨迹τ**和一个**评分 r**：

```
(τ(s), r(s)) = h(M, x, s)
```

其中 h 是执行环境（harness），M 是冻结的目标模型，x 是任务，s 是当前 Skill。

**关键设计点**：
- 小批量更新快但噪声大；大批量能暴露更多规律但计算成本高
- 支持**累积（accumulation）**：多个 rollout 批次分别 reflection 后合并成一次更新，解耦执行吞吐量和更新频率

### 2.3 组件二：Minibatch Reflection（反向传播）

优化器模型将轨迹转化为 Skill 编辑操作，这是 SkillOpt 的核心创新点。

**流程**：
1. **分离成功与失败**：将轨迹按执行结果分组
2. **划分为 Reflection Minibatch**：每个 minibatch 包含多个相似轨迹
3. **生成结构化编辑**：优化器输出 add/delete/replace 操作，或在 rewrite 模式下给出完整重写建议

**为什么需要 minibatch 而不是单个轨迹**？
- 单个轨迹往往产生偶发的修复建议
- Minibatch 能暴露可复用的程序性错误（如：总是查错来源、写错格式、未验证工具结果）

**本地提案合并**：
- 先分别合并失败驱动和成功驱动的编辑
- 再将两者合并，优先保留失败修正
- 过虑重复、矛盾、仅针对特定例子的建议

### 2.4 组件三：Bounded Text Updates（受限文本更新）

这是**与随意重写 Prompt 的本质区别**。

**学习率 analogues in SkillOpt**：

| 深度学习 | SkillOpt | 作用 |
|---------|---------|------|
| 学习率 | 编辑预算 Lt | 限制每次应用的编辑数量 |
| 学习率调度 | Lt 调度器（constant/linear/cosine/autonomous） | 控制编辑节奏 |
| 参数空间约束 | 慢更新字段（protected field） | 防止快速编辑覆盖持久规则 |

论文实验发现，**每步设置 4 到 8 个编辑操作的预算效果最好**。最终的最佳 Skill 往往只包含 1 到 4 个被接受的核心修改。

**Lt 调度器**：
- **Constant**：保持 Lt 不变
- **Linear**：线性衰减
- **Cosine**（默认）：从较大编辑逐步衰减到较小的巩固步骤
- **Autonomous**：自适应调整

### 2.5 组件四：Validation Gate 与 Rejected-Edit Buffer

**验证门控（Validation Gate）**：
- 每个候选 Skill 在验证集 D_sel 上评估
- 只有分数**严格高于**当前最佳分数时才接受（平局也拒绝）
- 这是将反射转化为"提出-验证-接受"优化而非无条件自编辑的关键

**被拒编辑缓冲区（Rejected-Edit Buffer）**：
- 论文最精彩的设计之一
- 被拒绝的编辑并非白费，而是存储为负面反馈
- 同一 epoch 内，后续 reflection 调用会收到这个缓冲区
- 优化器模型可以避免重复尝试失败的编辑，专注于未解决的问题

### 2.6 组件五：Epoch-wise Slow/Meta Update

**慢更新（Slow Update）**：
- 在 epoch 结束时触发
- 采样同一训练项：使用上一 epoch 的 Skill 和当前 Skill 各执行一次
- 将结果分为四类：提升、回归、持续失败、稳定成功
- 优化器模型将这些跨 epoch 的教训写入 Skill 文档的 protected slow-update 字段
- 这个字段受保护，快速编辑无法覆盖

**元技能（Meta Skill）**：
- 优化器侧才有的技能
- 总结哪些编辑模式有帮助、哪些被拒绝、哪些失败跨 epoch 持续存在
- 这个元指导被添加到未来优化器 prompt 中
- **但不会随部署的 Skill 一起发布**——保持部署产物的精简

**关键价值**：快速更新学习当前批次；慢/元更新学习相邻 epoch 的规律。两者分离确保局部修改不会覆盖持久的程序性教训。

---

## 3. 实验结果：52 个评估单元全部最佳

### 3.1 实验设置

**数据集（6 个基准）**：

| 基准 | 任务类型 | 特点 |
|------|---------|------|
| SearchQA | 单轮 QA | 有自然语言搜索问题 |
| SpreadsheetBench | 表格执行 | 最多 24 步工具调用，真实 openpyxl/pandas 运行时 |
| OfficeQA | 文档推理 | 多工具循环执行 |
| DocVQA | 文档问答 | 多模态 QA |
| LiveMathematicianBench | 数学推理 | 数学问题解决 |
| ALFWorld | 具身决策 | 最多 50 步的持久化环境交互 |

**目标模型（7 个）**：
- GPT-5.5、GPT-5.4、GPT-5.4-mini、GPT-5.4-nano、GPT-5.2
- Qwen3.5-4B、Qwen3.6-35B-A3B

**执行环境（3 种）**：
- Direct Chat（直接对话）
- Codex Harness（代码执行沙箱）
- Claude Code Harness（代码执行环境）

### 3.2 主要结果

| 配置 | 无 Skill | 最佳基线 | SkillOpt | 提升 |
|------|---------|---------|---------|------|
| GPT-5.5 Direct Chat | 58.8 | 76.9 | **82.3** | +23.5 |
| GPT-5.5 Codex | - | - | **最佳** | +24.8 |
| GPT-5.5 Claude Code | - | - | **最佳** | +19.1 |

**关键数据点**：
- **52 个评估单元，SkillOpt 在所有单元上均取得最佳或并列最佳**
- 在 GPT-5.5 直接对话中：
  - SearchQA：77.7 → 87.3（+9.6）
  - SpreadsheetBench：41.8 → 80.7（+38.9）
  - OfficeQA：33.1 → 72.1（+39.0）
  - DocVQA：78.8 → 91.2（+12.4）
  - LiveMathematicianBench：37.6 → 66.9（+29.3）
  - ALFWorld：83.6 → 95.5（+11.9）

**对比基线（均被击败）**：
- Human Skill（人工编写）
- One-shot LLM Skill（一次性生成）
- Trace2Skill（轨迹级技能蒸馏）
- TextGrad（梯度风格自然语言优化）
- GEPA（Pareto 反思性 Prompt 演化）
- EvoSkill（技能夹层演化）

### 3.3 消融实验：为什么有效

论文通过消融实验验证了各组件的贡献：

**文本学习率**：
- 无学习率（随意重写）：84.6/75.7/57.3
- 有学习率（bounded update）：87.1/77.5/61.3
- 结论：**限制每次修改量比随意重写稳定得多**

**Rejected-Edit Buffer**：
- 无缓冲区：85.5/72.9/58.9
- 有缓冲区：87.1/77.5/61.3
- 结论：被拒编辑提供的负反馈显著提升稳定性

**Slow/Meta Update（最重要发现）**：
- 移除两者：86.3/55.0/59.7
- 仅移除 meta skill：85.1/75.7/58.1
- 完整版：87.1/77.5/61.3
- **结论：在 SpreadsheetBench 上，移除慢/元更新导致性能暴跌 22.5 点**

---

## 4. 迁移学习：Skill 作为可复用工件

### 4.1 跨模型迁移

| 源模型 | 目标模型 | 基准 | 直接优化 | 迁移后 |
|--------|---------|------|---------|--------|
| GPT-5.4 | GPT-5.4-mini | 36.1 | 47.5 | 45.5 |
| GPT-5.4 | GPT-5.4-nano | 23.5 | 42.5 | 26.5 |

**结论**：在 SpreadsheetBench 上，GPT-5.4 优化的 Skill 迁移到小模型仍然有效，恢复 82%的原领域增益。

### 4.2 跨 Harness 迁移

| 源 Harness | 目标 Harness | 基准 | 迁移后 |
|-----------|-------------|------|--------|
| Codex | Claude Code | 22.1 | **81.8**（+59.7） |
| Claude Code | Codex | 27.5 | 71.1（+43.6） |

**结论**：这是最令人惊喜的发现——在不同执行环境之间迁移时，增益不仅没有消失，反而在 SpreadsheetBench 上超越了原领域表现。这表明**优化后的 Skill 编码的是可复用的程序性知识，而非环境特定的命令**。

### 4.3 跨基准迁移

| 源基准 | 目标基准 | 模型 | 基准分数 | 迁移后 |
|--------|----------|------|---------|--------|
| OlympiadBench | Omni-MATH | GPT-5.4 | 56.6 | **60.3**（+3.7） |
| OlympiadBench | Omni-MATH | GPT-5.4-nano | 38.8 | 40.1（+1.3） |

**结论**：数学基准之间的迁移虽然幅度较小，但全部为正，说明优化后的 Skill 编码的是可迁移的数学解题程序而非特定格式。

---

## 5. 工程实现：SkillOpt 的实用价值

### 5.1 最终产物：best_skill.md

训练完成后，SkillOpt 导出一个紧凑的**best_skill.md 文件**：
- 大小：**300-2000 tokens**（仅需 1-4 个接受的编辑）
- 特点：**可检查、可移植、无需模型权重更新即可部署**

### 5.2 Harness 无关性

SkillOpt 通过一个**轻量级适配器接口**支持不同执行环境：

```python
# 适配器接口（伪代码）
class HarnessAdapter:
    def construct_batch(self, task): ...
    def inject_skill(self, skill): ...
    def run_native_harness(self): ...
    def return_scored_trajectory(self): ...
```

同一优化器适用于：
- Direct QA（直接问答）
- 表格执行（SpreadsheetBench）
- 文档推理（OfficeQA）
- 多模态 QA（DocVQA）
- 具身环境（ALFWorld）
- Codex/Claude Code 风格的代码执行循环

### 5.3 零推理时模型调用

**关键设计**：优化器模型只在离线训练时调用，部署时只使用静态的 best_skill.md。这意味着：
- 部署时**不增加任何额外的模型推理成本**
- Skill 优化是一次性离线投资，收益在部署时完全兑现

### 5.4 开源与复现

论文开源了代码：https://aka.ms/skillopt

---

## 6. 行业意义：提示词工程进入机器学习时代

### 6.1 核心结论

> **"我们主张，Skill 应当作为 Agent 的外部冻结状态来被『训练』，并且训练过程还要『让权重空间优化具有可重复性』！**

这篇论文的结论十分深刻：**Skill（Prompt）完全配得上、也需要一套系统级的训练流程**。

这意味着提示词工程（Prompting）和模型训练（Training）之间的界限正在变得模糊。提示词工程完全进入了机器学习的领域——我们再也不需要人类去手动瞎改和调试提示词了！

### 6.2 对 Agent 框架设计的启示

论文提出的设计原则值得所有 Agent 框架设计者借鉴：

1. **独立的优化器模型**：将"编辑 Skill"的能力从目标模型中分离出来
2. **验证门控机制**：每一次编辑都必须有明确的反馈才能接受
3. **编辑预算（学习率）**：限制单次修改量，保证更新的稳定性
4. **被拒编辑缓冲区**：将失败转化为学习信号
5. **慢/元更新**：保持跨 epoch 的一致性，避免震荡
6. **产物可迁移**：一次优化，多处部署

### 6.3 适用场景

SkillOpt 特别适合以下场景：

| 场景 | 描述 |
|------|------|
| 企业知识库问答 | 针对特定领域的专业问答 Skill 优化 |
| 代码助手定制 | 针对公司代码规范的代码生成 Skill |
| 数据分析 Agent | 针对特定数据格式和报表规范的 Agent |
| 客服机器人 | 针对产品知识和回复规范的对话 Skill |
| 研究助手 | 针对论文阅读和文献整理的学术 Skill |

---

## 7. 总结

SkillOpt 是 AI Agent 开发领域的一项重要突破。它证明了：

1. **Skill 不是静态产物，而是可训练的对象**
2. **通过类强化学习的训练流程，Skill 可以从"能用"进化到"好用"**
3. **优化后的 Skill 具有跨模型、跨环境、跨基准的迁移能力**
4. **整个过程零推理时开销，产物即插即用**

随着 AI Agent 在各行各业的广泛应用，如何让 Agent 的技能持续进化、适应不同场景将成为核心挑战。SkillOpt 提供了一个优雅且可复现的解决方案——**将提示词工程带入机器学习的时代**。

---

## 参考资料

- 论文：SkillOpt: Executive Strategy for Self-Evolving Agent Skills（arXiv:2605.23904）
- 作者：Yifan Yang*, Ziyang Gong*, Weiquan Huang*, Qihao Yang*, 等（微软 + 上海交大 + 复旦 + 同济）
- 代码：https://aka.ms/skillopt