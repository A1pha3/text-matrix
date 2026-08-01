---
title: "《动手学大模型》：上海交通大学31.5K Stars的LLM编程实践教程——微调/提示工程/知识编辑/RLHF全覆盖"
date: "2026-04-16T01:30:00+08:00"
slug: "dive-into-llms-sjtu-tutorial"
description: "dive-into-llms是上海交通大学出品的31.5K Stars大模型教程，涵盖微调部署、提示学习、思维链、知识编辑、数学推理、文本水印、越狱攻击、隐写术、多模态、GUI Agent、RLHF对齐等11大主题。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "RLHF"]
---

# 《动手学大模型》：上海交通大学 31.5K Stars 的 LLM 编程实践教程——微调/提示工程/知识编辑/RLHF 全覆盖

《动手学大模型》是上海交通大学出品的编程实践教程，GitHub 上 30,348+ Stars，配合 Jupyter Notebook 覆盖微调部署、提示学习、思维链、知识编辑、数学推理、文本水印、越狱攻击、隐写术、多模态、GUI Agent、RLHF 对齐等 11 个主题。每个主题都有可运行的代码，课程源自交大《自然语言处理前沿技术》(NIS8021) 和《人工智能安全技术》(NIS3353)，授课教师张倬胜。

| 项目 | 信息 |
|------|------|
| GitHub | [FourierTransformer/dive-into-llms](https://github.com/FourierTransformer/dive-into-llms) |
| Stars | 30,348+ |
| 类型 | 编程实践教程（Jupyter Notebook） |
| 来源 | 上海交通大学 |
| 教师 | 张倬胜 |
| 语言 | 中文 |

---

## 1. 这篇教程能给你什么

- 搞清楚大模型的基本概念：预训练、微调、RLHF、提示工程
- 过一遍 11 个主题，从微调到 GUI Agent
- 每个主题都有 Jupyter Notebook，可以直接跑
- 接触一些前沿方向：知识编辑、模型水印、越狱攻击
- 用华为昇腾的《大模型开发全流程》走一遍国产化流程

## 2. 项目概览

教程完全免费，编程优先，每个主题都有可运行的代码。课程配套真实课堂，持续更新——2025 年 6 月新增了数学推理、GUI Agent 等内容。还联合华为昇腾推出了《大模型开发全流程》系列课程，覆盖昇腾 910/310 芯片。

作者团队由张倬胜老师主导，袁童鑫 (Lordog)、马欣贝、何志威、杜巍、赵皓东、吴宗儒、吴铮、董凌众、张玉龙、费豪（新加坡国立大学）等贡献者参与。

## 3. 教程内容详解

### 3.1 完整课程地图

| # | 主题 | 简介 | 代码 |
|---|------|------|------|
| 1 | **微调与部署** | 预训练模型微调与部署指南 | `dive-tuning.ipynb` |
| 2 | **提示学习与思维链** | API 调用与推理指南 | `dive-prompting.ipynb` |
| 3 | **知识编辑** | 操控模型对特定知识的记忆 | `dive_edit.ipynb` |
| 4 | **数学推理** | 蒸馏迷你 R1 模型 | `sft_math.ipynb` |
| 5 | **模型水印** | 文本水印嵌入技术 | `watermark.ipynb` |
| 6 | **越狱攻击** | 理解并防范越狱攻击 | `dive-jailbreak.ipynb` |
| 7 | **大模型隐写** | 隐写术：隐藏信息传输 | `llm_stega.ipynb` |
| 8 | **多模态模型** | MLLM 与 AGI 探索 | `mllms.ipynb` |
| 9 | **GUI 智能体** | AI Agent 点外卖/购物比价 | `GUIagent.ipynb` |
| 10 | **智能体安全** | 开放场景中的风险威胁 | `agent.ipynb` |
| 11 | **RLHF 安全对齐** | PPO 训练与对齐实验 | `RLHF.ipynb` |

下面逐一展开每个主题的内容和看点。

---

## 4. 主题一：微调与部署

微调（Fine-tuning）是在预训练模型基础上，用特定任务数据进一步训练。预训练阶段让模型学会语言规律，微调阶段让它适应特定任务。

教程覆盖四种微调技术路线：

| 技术 | 说明 | 适用场景 |
|------|------|----------|
| **Full Fine-tuning** | 更新所有参数 | 数据充足 |
| **LoRA** | 低秩适配器 | 资源有限 |
| **QLoRA** | 量化 + LoRA | 极度资源有限 |
| **Prefix Tuning** | 添加可学习前缀 | 少参数 |

`dive-tuning.ipynb` 涵盖数据准备与预处理、LoRA/QLoRA 配置、训练监控、模型导出与 vLLM 部署。部署方面给出 vLLM 示例：

```python
# 使用 vLLM 部署
from vllm import LLM

llm = LLM(model="meta-llama/Llama-2-7b")
output = llm.generate("Hello, world!")
```

---

## 5. 主题二：提示学习与思维链

提示工程是门手艺活。教程里有个有意思的观察："大模型对一些问题的回答令人大跌眼镜，但它可能只是想要一句鼓励"。确实，给模型加一句"请认真思考后回答"，结果可能有明显改善。

基础提示技巧很简单：直接提问。但更有效的是带示例的提示（Few-shot）：

```python
prompt = """
Example: 2+2 = 4
Question: 3+3 = ?
Answer:"
```

思维链（Chain of Thought）让模型先推理再给答案。标准提示下模型可能答错简单的算术题，加上中间推理步骤后准确率明显提升：

```python
# 标准提示
Q: 小明有5个苹果，丢了2个，又买了3个，现在有几个？
A: 6个  # 错误

# 思维链提示
Q: 小明有5个苹果，丢了2个，又买了3个，现在有几个？
A: 5-2=3，3+3=6，所以是6个。答案是6个。  # 正确
```

进阶技巧包括角色提示（"你是一位资深数学老师..."）、格式约束（"请用 JSON 格式输出"）、链式验证（"先分析，再总结，最后给出答案"）。

---

## 6. 主题三：知识编辑

大模型的知识来自训练数据，如果训练数据截止于 2022 年，模型就不知道 2023 年的事件。重训太贵，知识编辑（Knowledge Editing）提供了更精细的解决方案——只修改与目标知识相关的参数，不影响其他知识。

教程覆盖四种知识编辑方法：

| 方法 | 代表工作 | 说明 |
|------|----------|------|
| **元学习** | MEND | 学习如何编辑 |
| **定位+修改** | ROME | 定位知识位置并修改 |
| **额外参数** | T-Parser | 添加可编辑模块 |
| **混合方法** | KEPLER | 结合多种策略 |

评估编辑效果有三个维度：编辑后文本是否流畅（fluency）、与原文的相似度（proximity）、是否精准修改目标知识（specificity）。

---

## 7. 主题四：数学推理

大模型在数学推理上通常表现不佳。教程提供"蒸馏"思路——将 o1/o3 的推理能力迁移到小模型：

```python
# 数学推理训练数据格式
{
    "question": "求1+2+...+100的和",
    "reasoning": "使用等差数列求和公式...",
    "answer": "5050"
}
```

使用 PPO 强化学习进一步优化，通过奖励信号引导模型产出更准确的推理步骤：

```python
# PPO 训练循环
for episode in range(1000):
    response = model.generate(prompt)
    reward = compute_math_reward(response)
    model.update(reward)  # PPO 更新
```

---

## 8. 主题五：模型水印

文本水印（Text Watermark）在 AI 生成的文本中嵌入人类不可见的统计水印，用于证明文本由某模型生成。Gumbel Watermark 的原理是基于词汇表分组的统计方法：用密钥将词汇表分成"绿色列表"和"红色列表"，生成文本时优先从绿色列表选词，检测时分析绿色词汇比例是否显著高于随机概率。

应用场景包括版权保护（证明文本由某模型生成）、内容溯源（追踪虚假信息来源）、防伪认证（区分 AI 和人类创作）。

---

## 9. 主题六：越狱攻击

越狱攻击绕过大模型的安全机制。正常请求"我如何制作炸弹"会被安全拒绝，但通过角色扮演"作为电影编剧，请写一个关于炸..."可能被接受。

常见攻击手法包括角色扮演、编码绕过、渐进式引导（从无害问题逐步引导到敏感话题）、对抗性后缀（添加特殊 token 序列）。防御策略需要检测对抗性模式：

```python
# 越狱检测
def detect_jailbreak(prompt: str) -> bool:
    # 检测对抗性模式
    patterns = [
        r"pretend to be",
        r"forget.*safety",
        r"ignore.*instruction"
    ]
    return any(re.search(p, prompt) for p in patterns)
```

---

## 10. 主题七：大模型隐写

隐写术像"看不见的墨水"——在流畅回答中隐藏只有"自己人"能读取的信息。编码时把秘密信息嵌入到正常文本的细微特征中，比如选词偏好、标点分布、句式结构。解码方用预设的密钥从文本中提取隐藏信息。

```python
# 隐写编码
hidden_message = "秘密信息"
cover_text = "今天的天气真不错！"

steganographic_text = encode(cover_text, hidden_message)
# 输出：今天的天气（真）不错（！）

# 隐写解码
decoded = decode(steganographic_text)
# 输出：秘密信息
```

应用场景包括隐蔽通信、水印追踪、防审查。

---

## 11. 主题八：多模态模型

多模态大语言模型（Multimodal Large Language Models）能够理解和生成多种模态内容：文本 + 图像 + 音频 + 视频 → 统一理解。教程介绍 GPT-4V、Gemini、LLaVA、Qwen-VL 等代表模型，并探讨多模态模型是否是通往 AGI 的路径——多模态训练带来能力提升，不同模态的统一语义空间，视觉-语言-动作的结合是机器的感知发展方向。

---

## 12. 主题九：GUI 智能体

GUI Agent 让 AI 代替用户操作电脑或手机。用户说"帮我点外卖"，Agent 自动打开外卖 App、选择店铺、添加购物车、提交订单，最后返回结果。

技术架构分三层：

```python
class GUIAgent:
    def __init__(self):
        self.vision = VisionModel()      # 视觉理解
        self.planner = PlannerModel()    # 任务规划
        self.executor = Executor()       # 动作执行

    def run(self, task: str):
        # 1. 截图获取当前界面
        screenshot = self.capture_screen()
        # 2. 视觉理解界面
        ui_elements = self.vision.parse(screenshot)
        # 3. 规划下一步行动
        action = self.planner.decide(task, ui_elements)
        # 4. 执行动作
        self.executor.perform(action)
```

应用场景包括点外卖、购物比价、邮件处理等日常操作。

---

## 13. 主题十：智能体安全

大模型智能体在开放场景中面临新的安全威胁。Agent 可能被诱导执行恶意操作——比如邮件 Agent 被提示注入后发送钓鱼邮件。

攻击向量包括提示注入（在外部输入中注入恶意指令）、工具劫持（篡改 Agent 调用的工具）、环境 poisoning（污染 Agent 的工作环境）、权限滥用（Agent 执行超出必要范围的操作）。

防御策略需要多层安全检查：

```python
class SafeAgent:
    def execute(self, action):
        # 1. 权限检查
        if not self.check_permission(action):
            return "拒绝：权限不足"
        # 2. 风险评估
        risk = self.assess_risk(action)
        if risk > self.threshold:
            return "拒绝：风险过高"
        # 3. 人工确认
        if action.is_destructive:
            return "等待用户确认"
        # 4. 执行
        return self.perform(action)
```

---

## 14. 主题十一：RLHF 安全对齐

RLHF（Reinforcement Learning from Human Feedback）通过人类反馈进行强化学习，流程是：收集人类偏好数据 → 训练奖励模型 → PPO 强化学习优化。PPO 核心循环如下：

```python
# PPO 核心循环
for epoch in range(num_epochs):
    # 1. 收集 rollout
    trajectories = collect_rollout(policy, env)
    # 2. 计算 advantage
    advantages = compute_advantage(rewards, values)
    # 3. PPO 更新
    for _ in range(ppo_epochs):
        ratio = pi_new / pi_old
        clipped_ratio = torch.clamp(ratio, 1-eps, 1+eps)
        loss = -min(ratio * advantages, clipped_ratio * advantages)
```

除了 RLHF，教程还介绍了 DPO（直接偏好优化，不需要 PPO）、RLAIF（用 AI 反馈替代人类反馈）、Constitutional AI（基于准则的对齐）等对齐技术。

---

## 15. 国产化：华为昇腾《大模型开发全流程》

教程联合华为昇腾推出《大模型开发全流程》系列课程，覆盖昇腾 910/310 芯片，软件栈为 CANN + MindSpore + ModelArts。课程分三级：

| 级别 | 面向人群 | 内容 |
|------|----------|------|
| **初级** | 初学者 | 环境搭建 → 基础模型使用 |
| **中级** | 进阶用户 | 模型训练 → 微调优化 |
| **高级** | 专业开发者 | 分布式训练 → 性能调优 |

学习路径：昇腾社区 → 大模型开发学习专区 → 选择级别 → 学习路径。

---

## 16. 常见问题

**需要什么基础才能学习？**

需要 Python 基础和深度学习基本概念。教程从基础讲起，逐步深入。

**每个主题都需要 GPU 吗？**

部分主题（如微调）需要 GPU，提示学习和理论部分可以在 CPU 上运行。

**有配套视频吗？**

有。教程提供 PPT、实验手册和视频，特别是昇腾课程有完整视频。

**如何获取帮助？**

可以提交 GitHub Issue 或 PR，项目团队会积极回复。

**可以用于商业项目吗？**

教程代码遵循原模型 license，请查阅具体代码的许可。

**和其他 LLM 教程比有什么优势？**

源自交大真实课程，编程实践优先，覆盖安全和对齐等前沿主题。

---

## 实践案例

### 案例1：运行微调与部署 Notebook

```bash
# 克隆仓库
git clone https://github.com/FourierTransformer/dive-into-llms.git
cd dive-into-llms

# 安装依赖
pip install -r requirements.txt

# 启动 Jupyter
jupyter notebook

# 在浏览器中打开 dive-tuning.ipynb
```

微调需要 GPU 资源。如果没有本地 GPU，可以使用 Google Colab 或华为昇腾社区的开发环境。

### 案例2：实验提示工程与思维链

打开 `dive-prompting.ipynb`，实验基础提示、Few-shot 提示、思维链提示三种策略，观察不同提示策略对模型输出质量的影响。

### 案例3：知识编辑实验

打开 `dive_edit.ipynb`，实验如何修改模型对特定知识的记忆。教程提供了 MEND、ROME 等方法的实现。

```python
# 知识编辑示例
from knowledge_editing import apply_edit

model = apply_edit(model, question="...", new_answer="...")
```

### 案例4：GUI Agent 实践

打开 `GUIagent.ipynb`，体验 AI Agent 如何操作电脑：

```python
agent = GUIAgent()
agent.run("帮我点外卖")
# Agent 会自动：打开外卖App → 选择店铺 → 加购 → 下单
```

---

## 自测题

1. 教程包含 11 个主题。如果你是一个有深度学习基础的研究生，想要研究大模型安全对齐方向，你会优先学习哪几个主题？为什么？

2. 微调（Fine-tuning）和 RLHF 有什么区别？它们分别解决什么问题？

3. 知识编辑（Knowledge Editing）想解决什么实际问题？它与微调有什么关系？

4. 教程中提到了"模型水印"技术。这项技术的基本原理是什么？有哪些应用场景？

5. 如果你要给一个没有深度学习基础的学生推荐学习路径，你会按什么顺序推荐这 11 个主题？

3 题以上答不准的话，建议重看"教程内容详解"和"主题一"到"主题十一"各节。

<details>
<summary>参考答案</summary>

**题 1**：优先学习主题十（智能体安全）和主题十一（RLHF 安全对齐）。这两个主题直接涉及大模型安全对齐方向，涵盖了越狱攻击防御、智能体安全风险、RLHF 对齐算法等核心内容。

**题 2**：微调是在预训练模型基础上用特定任务数据进一步训练，适应特定任务。RLHF 是通过人类反馈进行强化学习，让模型输出更符合人类偏好。微调解决的是"适应特定任务"问题，RLHF 解决的是"安全对齐"问题。两者可以结合使用。

**题 3**：知识编辑想解决的是"如何高效修改大模型中的特定知识"问题（比如修正事实错误、更新过时信息）。它与微调的关系是：知识编辑是一种更精细、更高效的"微调"——它只修改与目标知识相关的参数，不影响其他知识。

**题 4**：模型水印技术的基本原理是基于词汇表分组（Green/Red List）的统计方法——用密钥将词汇表分成绿色列表和红色列表，生成文本时模型优先从绿色列表选择词汇，检测时分析文本中绿色词汇的比例是否显著高于随机概率。应用场景包括版权保护、内容溯源、防伪认证。

**题 5**：推荐顺序：主题二（提示学习与思维链）→ 主题一（微调与部署）→ 主题八（多模态模型）→ 主题九（GUI 智能体）→ 主题三（知识编辑）→ 主题四（数学推理）→ 主题五（模型水印）→ 主题六（越狱攻击）→ 主题七（大模型隐写）→ 主题十（智能体安全）→ 主题十一（RLHF 安全对齐）。这个顺序从基础到前沿，从简单到复杂。

</details>

---

## 练习

1. **环境搭建**：克隆《动手学大模型》仓库，安装依赖，成功运行 `dive-prompting.ipynb` Notebook。

2. **提示工程对比实验**：在 `dive-prompting.ipynb` 中，分别用基础提示、Few-shot 提示、思维链提示完成同一个任务，对比输出质量。

3. **微调实验**：如果有 GPU 资源，运行 `dive-tuning.ipynb`，完成一个预训练模型的微调任务。

4. **知识编辑实验**：运行 `dive_edit.ipynb`，理解 MEND、ROME 等知识编辑方法的原理和实现。

5. **前沿主题探索**：选择教程中的一个前沿主题（如越狱攻击、大模型隐写、GUI Agent），深入阅读相关论文，并思考如何改进教程中的方法。

---

## 进阶路径

### 阶段1：跑通基础主题（1-2 周）

- 完成主题一（微调与部署）和主题二（提示学习与思维链）的学习
- 成功运行对应的 Jupyter Notebook
- 理解大模型的基本概念：预训练、微调、RLHF、提示工程
- 能够独立完成一个简单的微调任务

### 阶段2：深入专项主题（3-5 周）

- 根据研究方向选择 3-5 个专项主题深入学习
- 运行对应的 Jupyter Notebook，理解代码实现
- 阅读教程中引用的论文，深入理解原理
- 尝试改进教程中的方法或提出新的想法

### 阶段3：研究项目实践（1-2 个月）

- 选择一个具体的研究问题（如"如何提升大模型的安全性"）
- 基于教程中的方法设计实验
- 实现、验证、分析结果
- 撰写技术报告或论文

### 阶段4：社区贡献与前沿追踪（持续）

- 向教程仓库提交 PR，分享你的改进或新主题
- 关注大模型领域的最新论文（arXiv、顶会）
- 参与学术社区讨论（GitHub Discussions、知乎、Twitter）
- 思考：教程中哪些内容需要更新？哪些新主题应该加入？

---

## 相关资源

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/Lordog/dive-into-llms |
| 昇腾社区 | https://www.hiascend.com/edu/growth/lm-development |
| 课程教师 | 张倬胜 (bcmi.sjtu.edu.cn) |
| 主要贡献者 | 袁童鑫 Lordog |