---
title: "《动手学大模型》：上海交通大学31.5K Stars的LLM编程实践教程——微调/提示工程/知识编辑/RLHF全覆盖"
date: "2026-04-16T01:30:00+08:00"
slug: "dive-into-llms-sjtu-tutorial"
description: "dive-into-llms是上海交通大学出品的31.5K Stars大模型教程，涵盖微调部署、提示学习、思维链、知识编辑、数学推理、文本水印、越狱攻击、隐写术、多模态、GUI Agent、RLHF对齐等11大主题。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "RLHF"]
---

# 《动手学大模型》：上海交通大学 31.5K Stars 的 LLM 编程实践教程

《动手学大模型》是上海交通大学出品的编程实践教程，GitHub 31.5K+ Stars，以 Jupyter Notebook 覆盖微调部署、提示学习、思维链、知识编辑、数学推理、文本水印、越狱攻击、隐写术、多模态、GUI Agent、RLHF 对齐等 11 个主题。课程源自交大《自然语言处理前沿技术》(NIS8021) 和《人工智能安全技术》(NIS3353)，授课教师张倬胜。

| 项目 | 信息 |
|------|------|
| GitHub | [FourierTransformer/dive-into-llms](https://github.com/FourierTransformer/dive-into-llms) |
| Stars | 31,500+ |
| 类型 | 编程实践教程（Jupyter Notebook） |
| 来源 | 上海交通大学 |
| 教师 | 张倬胜 |
| 语言 | 中文 |

---

## 1. 项目概览

教程完全免费，编程优先，每个主题都有可运行的代码。课程持续更新——2025 年 6 月新增了数学推理、GUI Agent 等内容。联合华为昇腾推出《大模型开发全流程》系列课程，覆盖昇腾 910/310 芯片。

作者团队由张倬胜主导，袁童鑫 (Lordog)、马欣贝、何志威、杜巍、赵皓东、吴宗儒、吴铮、董凌众、张玉龙、费豪（新加坡国立大学）等贡献者参与。

## 2. 教程内容详解

### 完整课程地图

| # | 主题 | 简介 | 代码 |
|---|------|------|------|
| 1 | **微调与部署** | 预训练模型微调与部署 | `dive-tuning.ipynb` |
| 2 | **提示学习与思维链** | API 调用与推理 | `dive-prompting.ipynb` |
| 3 | **知识编辑** | 操控模型对特定知识的记忆 | `dive_edit.ipynb` |
| 4 | **数学推理** | 蒸馏迷你 R1 模型 | `sft_math.ipynb` |
| 5 | **模型水印** | 文本水印嵌入技术 | `watermark.ipynb` |
| 6 | **越狱攻击** | 理解并防范越狱攻击 | `dive-jailbreak.ipynb` |
| 7 | **大模型隐写** | 隐写术：隐藏信息传输 | `llm_stega.ipynb` |
| 8 | **多模态模型** | MLLM 与 AGI 探索 | `mllms.ipynb` |
| 9 | **GUI 智能体** | AI Agent 操作界面 | `GUIagent.ipynb` |
| 10 | **智能体安全** | 开放场景中的安全威胁 | `agent.ipynb` |
| 11 | **RLHF 安全对齐** | PPO 训练与对齐实验 | `RLHF.ipynb` |

---

## 3. 主题一：微调与部署

微调（Fine-tuning）在预训练模型基础上，用特定任务数据进一步训练。教程覆盖四种微调技术路线：

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

## 4. 主题二：提示学习与思维链

基础提示技巧：直接提问。更有效的是带示例的提示（Few-shot）：

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

## 5. 主题三：知识编辑

知识编辑（Knowledge Editing）只修改与目标知识相关的参数，不影响其他知识，比重训更经济。教程覆盖四种方法：

| 方法 | 代表工作 | 说明 |
|------|----------|------|
| **元学习** | MEND | 学习如何编辑 |
| **定位+修改** | ROME | 定位知识位置并修改 |
| **额外参数** | T-Parser | 添加可编辑模块 |
| **混合方法** | KEPLER | 结合多种策略 |

评估编辑效果有三个维度：编辑后文本是否流畅（fluency）、与原文的相似度（proximity）、是否精准修改目标知识（specificity）。

---

## 6. 主题四：数学推理

教程提供"蒸馏"思路——将 o1/o3 的推理能力迁移到小模型：

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

## 7. 主题五：模型水印

文本水印（Text Watermark）在 AI 生成文本中嵌入不可见的统计水印，用于证明文本来源。Gumbel Watermark 原理：用密钥将词汇表分为"绿色列表"和"红色列表"，生成时优先从绿色列表选词，检测时分析绿色词汇比例是否显著高于随机概率。

应用场景包括版权保护、内容溯源、防伪认证。

---

## 8. 主题六：越狱攻击

越狱攻击绕过大模型的安全机制。正常请求"我如何制作炸弹"会被安全拒绝，但通过角色扮演"作为电影编剧，请写一个关于炸..."可能被接受。

攻击手法包括角色扮演、编码绕过、渐进式引导（从无害问题逐步引导到敏感话题）、对抗性后缀（添加特殊 token 序列）。防御策略需检测对抗性模式：

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

## 9. 主题七：大模型隐写

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

## 10. 主题八：多模态模型

多模态大语言模型（MLLM）能够理解和生成多种模态内容：文本 + 图像 + 音频 + 视频 → 统一理解。教程介绍 GPT-4V、Gemini、LLaVA、Qwen-VL 等代表模型，并探讨多模态与 AGI 的关系——多模态训练带来能力提升，不同模态的统一语义空间，视觉-语言-动作的结合。

---

## 11. 主题九：GUI 智能体

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

## 12. 主题十：智能体安全

Agent 可能被诱导执行恶意操作——邮件 Agent 被提示注入后发送钓鱼邮件。

攻击向量包括提示注入、工具劫持、环境 poisoning、权限滥用。

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

## 13. 主题十一：RLHF 安全对齐

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

## 14. 国产化：华为昇腾《大模型开发全流程》

教程联合华为昇腾推出《大模型开发全流程》系列课程，覆盖昇腾 910/310 芯片，软件栈为 CANN + MindSpore + ModelArts。课程分三级：

| 级别 | 面向人群 | 内容 |
|------|----------|------|
| **初级** | 初学者 | 环境搭建 → 基础模型使用 |
| **中级** | 进阶用户 | 模型训练 → 微调优化 |
| **高级** | 专业开发者 | 分布式训练 → 性能调优 |

学习路径：昇腾社区 → 大模型开发学习专区 → 选择级别 → 学习路径。

---

## 相关资源

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/Lordog/dive-into-llms |
| 昇腾社区 | https://www.hiascend.com/edu/growth/lm-development |
| 课程教师 | 张倬胜 (bcmi.sjtu.edu.cn) |
| 主要贡献者 | 袁童鑫 Lordog |