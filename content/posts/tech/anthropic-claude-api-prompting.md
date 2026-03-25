---
title: "Claude API基础专题（二）：提示词工程"
date: 2026-03-25
draft: false
categories:
  - 技术笔记
tags:
  - Claude
  - 提示词
  - Few-shot
  - Temperature
slug: "claude-api-prompting-engineering"
description: "本文系统讲解了Claude API的提示词工程技巧，涵盖提示词原则、系统提示词、Few-shot学习、温度参数调节、链式思考等核心主题，帮助开发者掌握高效提示词设计方法。"
---

# Claude API基础专题（二）：提示词工程 ⭐⭐⭐⭐

> **目标读者**：有一定开发经验，希望提升Claude API调用效果的工程师
> **前置知识**：已完成第一篇《API基础》
> **学习提醒**：提示词工程是迭代过程，建议边学边实践

---

## 章节导航

| 小节 | 主题 | 重要程度 |
|------|------|----------|
| 2.1 | 提示词核心原则 | ⭐⭐⭐⭐⭐ |
| 2.2 | 系统提示词深度应用 | ⭐⭐⭐⭐⭐ |
| 2.3 | Few-shot学习 | ⭐⭐⭐⭐⭐ |
| 2.4 | 链式思考（Chain of Thought） | ⭐⭐⭐⭐ |
| 2.5 | Temperature与采样参数 | ⭐⭐⭐⭐⭐ |
| 2.6 | 提示词评估与迭代 | ⭐⭐⭐⭐ |
| 2.7 | 常见反模式 | ⭐⭐⭐⭐ |

---

## 2.1 提示词核心原则

### 什么是好的提示词

在Claude API中，提示词（Prompt）是你与Claude沟通的主要方式。一个好的提示词应该包含以下要素：

| 要素 | 说明 | 示例 |
|------|------|------|
| **角色/身份** | Claude应该扮演什么角色 | "你是一位资深架构师" |
| **任务描述** | 需要完成什么任务 | "审查以下代码的安全性" |
| **上下文** | 相关的背景信息 | "这段代码是一个用户认证模块" |
| **输出格式** | 期望的返回格式 | "用表格列出所有问题" |
| **约束条件** | 任何限制或要求 | "不要修改原有代码逻辑" |

### 清晰明确原则

**❌ 模糊提示词**

```python
response = client.messages.create(
    messages=[{"role": "user", "content": "帮我看看这段代码"}]
)
```

**✅ 清晰提示词**

```python
response = client.messages.create(
    messages=[{
        "role": "user", 
        "content": """审查以下Python代码的安全性：

```python
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
```

请用表格列出：
1. 所有安全漏洞
2. 每个漏洞的风险等级（高/中/低）
3. 修复建议"""
    }]
)
```

### 上下文充足原则

Claude需要足够的信息来理解你的请求。上下文不足会导致：

| 问题 | 后果 | 解决方案 |
|------|------|----------|
| 回答过于笼统 | 没有针对性 | 提供具体场景 |
| 需要多轮澄清 | 浪费时间 | 一次给足信息 |
| 理解偏差 | 回答不相关 | 明确期望输出 |

### 结构化原则

将复杂任务分解成清晰的部分：

```python
prompt = """你是一位数据分析师。请分析以下销售数据。

## 数据
[销售数据JSON]

## 分析维度
1. 整体趋势：月度销售额变化
2. 地域分布：各地区占比
3. 产品表现：TOP 5产品
4. 异常检测：识别异常值

## 输出要求
- 每个维度用小标题
- 包含数据可视化建议（ASCII图表）
- 最后给出3个 actionable 建议
"""

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=2000,
    messages=[{"role": "user", "content": prompt}]
)
```

---

## 2.2 系统提示词深度应用

### 系统提示词的作用

系统提示词（System Prompt）设置了Claude的"默认行为"，影响整个对话过程。

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system="""你是一位专业代码审查员。
    
审查标准：
- 安全性（OWASP Top 10）
- 性能（时间/空间复杂度）
- 可读性（命名、注释、格式）
- 最佳实践（设计模式、语言特性）

回复格式：
## 总体评价
[简短总结]

## 问题列表
| 等级 | 位置 | 问题描述 | 修复建议 |
|------|------|----------|----------|

## 改进建议
[可选的额外优化建议]""",
    messages=[{"role": "user", "content": "审查以下代码..."}]
)
```

### 系统提示词的层级结构

好的系统提示词应该有清晰的结构：

```
# 角色定义
你是一位[专业领域]的[具体角色]。

# 核心职责
你的主要职责是：
1. [职责1]
2. [职责2]
3. [职责3]

# 行为约束
约束条件：
- [约束1]
- [约束2]

# 输出格式
回复格式：
- [格式1]
- [格式2]

# 专业知识
背景知识：
- [知识1]
- [知识2]
```

### 系统提示词注入（Prompt Injection）防范

当用户输入可能包含恶意指令时，需要防范提示词注入：

```python
# 原始系统提示词
SYSTEM_PROMPT = """你是一个客服助手。
只回答与产品相关的问题。
当用户询问无关话题时，回复："抱歉，我只能帮助解决产品问题。" """

# 不安全的实现 ❌
def create_messages(user_input):
    return [{"role": "user", "content": user_input}]  # 用户输入直接拼接到上下文

# 安全的实现 ✅
def create_messages(user_input, system_prompt):
    # 方式1：分离用户输入和系统指令
    # 用户输入作为独立消息，系统提示词不混入用户内容
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": sanitize_input(user_input)}
    ]

def sanitize_input(text):
    """清理可能注入系统指令的字符"""
    # 移除可能的指令注入
    dangerous_patterns = [
        "ignore previous instructions",
        "disregard your system prompt",
        "你是一个xx",
    ]
    for pattern in dangerous_patterns:
        text = text.replace(pattern, "[已过滤]")
    return text
```

### 动态系统提示词

根据不同场景切换系统提示词：

```python
class PromptManager:
    """提示词管理器"""
    
    SYSTEM_PROMPTS = {
        "code_review": """你是一位资深代码审查员。
        
职责：
1. 发现代码中的bug和安全漏洞
2. 评估代码性能和可读性
3. 提供具体的修复建议

回复格式：
- 每个问题一行："[等级] [位置] 问题描述" """,
        
        "data_analysis": """你是一位数据分析师。
        
职责：
1. 从数据中发现洞察
2. 用清晰的图表展示趋势
3. 提供基于数据的建议

回复格式：
- 先给结论
- 再给详细分析
- 最后给建议""",
        
        "writing": """你是一位专业文案编辑。
        
职责：
1. 改进文本的清晰度和可读性
2. 修正语法和拼写错误
3. 保持原作者的风格

回复格式：
- 改进后的文本
- 改进说明（可选）"""
    }
    
    @classmethod
    def get_prompt(cls, task_type):
        return cls.SYSTEM_PROMPTS.get(task_type, cls.SYSTEM_PROMPTS["writing"])
```

---

## 2.3 Few-shot学习

### 什么是Few-shot

Few-shot学习是在提示词中提供少量示例，让Claude学习任务的模式。

```python
# 无示例 - 零样本（Zero-shot）
response = client.messages.create(
    messages=[{
        "role": "user",
        "content": "把以下中文翻译成英文：今天天气真好"
    }]
)
# 可能输出："The weather is really nice today."

# 有示例 - 少样本（Few-shot）
response = client.messages.create(
    messages=[{
        "role": "user", 
        "content": """翻译以下中文成英文：

示例：
- "你好吗？" → "How are you?"
- "今天很开心" → "I'm very happy today"
- "明天见" → "See you tomorrow"

翻译：
- "今天天气真好" """
    }]
)
# 输出更符合期望："The weather is really nice today."
```

### Few-shot的适用场景

| 场景 | 适合Few-shot | 不适合 |
|------|-------------|--------|
| 格式化输出 | ✅ | |
| 特定风格 | ✅ | |
| 分类任务 | ✅ | |
| 简单问答 | | ❌ |
| 开放性对话 | | ❌ |
| 需要推理的复杂任务 | | ❌ |

### Few-shot最佳实践

#### 实践1：提供多样化的示例

```python
# ✅ 好的Few-shot：覆盖不同情况
prompt = """判断评论的情感是正面、负面还是中性。

示例：
- "这个产品太棒了，我非常满意！" → 正面
- "一般般，没有想象中好" → 中性
- "太差了，等了两周才到" → 负面
- "惊喜！比图片上还好看" → 正面
- "退货了，质量不行" → 负面

判断：
- "刚收到，还没用" → """
```

#### 实践2：示例要准确

```python
# ❌ 错误的示例会导致混淆
prompt = """判断数字奇偶性：

示例：
- "5" → 奇数
- "8" → 偶数
- "3" → 偶数  ← 错误示例！

判断：
- "7" → """
# 第三个示例是错的，Claude可能学习到错误的模式

# ✅ 正确的示例
prompt = """判断数字奇偶性：

示例：
- "5" → 奇数
- "8" → 偶数
- "3" → 奇数
- "10" → 偶数

判断：
- "7" → """
```

#### 实践3：示例数量要适中

| 任务复杂度 | 建议示例数 |
|-----------|-----------|
| 简单任务（分类、格式化） | 2-3个 |
| 中等任务（风格转换） | 3-5个 |
| 复杂任务（推理） | 5-10个 |

```python
# 适度示例
prompt = """将产品评论分类为：功能、质量、物流、性价比

示例：
- "屏幕清晰，电池耐用" → 功能
- "做工粗糙，有划痕" → 质量
- "发货快，包装完好" → 物流
- "价格实惠，性价比高" → 性价比

分类：
- "运行流畅，就是有点贵" → """
```

### Zero-shot vs Few-shot vs Many-shot

```python
# Zero-shot：不给示例
"将'很好'翻译成英文"  # → "very good"

# Few-shot：给2-5个示例
"很好→excellent, 不好→bad, 一般→okay. 翻译：不错"  # → "not bad"

# Many-shot：给大量示例（10+）
# 适用于需要强烈风格一致性的场景
```

---

## 2.4 链式思考（Chain of Thought）

### 什么是Chain of Thought

Chain of Thought（CoT）提示词是让Claude在给出最终答案之前，先展示推理过程。

```python
# 标准提示词（直接给答案）
response = client.messages.create(
    messages=[{
        "role": "user",
        "content": """小明有5个苹果，小红给了他3个，小明吃掉了2个。小明现在有多少个苹果？"""
    }]
)
# 输出："7个"

# Chain of Thought（展示推理）
response = client.messages.create(
    messages=[{
        "role": "user",
        "content": """小明有5个苹果，小红给了他3个，小明吃掉了2个。小明现在有多少个苹果？

请逐步思考，展示计算过程。"""
    }]
)
# 输出："让我逐步分析：
# 1. 小明原有5个苹果
# 2. 小红给了3个：5 + 3 = 8
# 3. 小明吃掉2个：8 - 2 = 6
# 答案：小明现在有6个苹果"
```

### 何时使用Chain of Thought

| 任务类型 | 使用CoT | 示例 |
|---------|--------|------|
| 数学问题 | ✅ 必须 | "计算153 * 47" |
| 逻辑推理 | ✅ 必须 | "如果A>B，B>C，问A和C的关系" |
| 代码调试 | ✅ 建议 | "分析这段代码为什么报错" |
| 事实问答 | ❌ 不需要 | "中国的首都是哪里" |
| 简单分类 | ❌ 不需要 | "判断这个是正面还是负面" |
| 创意写作 | ❌ 不需要 | "写一首关于春天的诗" |

### Chain of Thought变体

#### 变体1：显式步骤指引

```python
prompt = """分析以下代码的性能问题。

代码：
```python
def find_duplicates(arr):
    result = []
    for i in range(len(arr)):
        for j in range(len(arr)):
            if arr[i] == arr[j] and i != j:
                result.append(arr[i])
    return list(set(result))
```

分析步骤：
1. 识别代码的时间复杂度
2. 找出具体的性能瓶颈
3. 提出优化方案
4. 给出优化后的代码"""
```

#### 变体2：自我验证

```python
prompt = """判断以下论述是否正确："所有鸟都会飞"

思考步骤：
1. 列出所有会飞的鸟
2. 列出所有不会飞的鸟
3. 找一个反例（不会飞的鸟）
4. 得出结论"""
```

### CoT注意事项

```python
# ❌ 不要在简单任务上使用 - 增加token消耗
prompt = """1+1等于几？逐步思考。"""

# ✅ 在复杂推理任务上使用 - 提升准确性
prompt = """在一个袋子里有5个红球、3个蓝球。每次从袋子里不放回地抽取2个球。
问：连续两次都抽到红球的概率是多少？
请展示计算过程。"""
```

---

## 2.5 Temperature与采样参数

### 理解Temperature

Temperature（温度）控制输出的随机性：

| Temperature值 | 效果 | 适用场景 |
|-------------|------|----------|
| 0.0 | 几乎确定性输出 | 代码生成、数学计算 |
| 0.2-0.4 | 低随机性 | 事实问答、分类 |
| 0.5-0.7 | 中等随机性 | 一般对话、写作 |
| 0.8-1.0 | 高随机性 | 创意写作、脑暴 |
| >1.0 | 极高随机性（可能失控） | 特殊场景 |

```python
# 确定性输出 - 每次结果都一样
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=100,
    temperature=0.0,  # 几乎确定
    messages=[{"role": "user", "content": "1+1等于几？"}]
)
# 几乎总是输出"2"

# 创意输出 - 每次结果可能不同
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=200,
    temperature=0.9,  # 高随机性
    messages=[{"role": "user", "content": "写一个关于AI的科幻短故事开头"}]
)
# 每次输出都可能不同
```

### top_p参数

top_p（核采样）与temperature一起控制输出的多样性：

```python
# top_p=0.9 意味着只从累积概率前90%的词中选择
# top_p=1.0 意味着考虑所有词（完全放开）

# 保守输出
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    temperature=0.3,
    top_p=0.5,  # 更保守的选择
    messages=[{"role": "user", "content": "解释什么是HTTP"}]
)

# 创意输出
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    temperature=0.8,
    top_p=0.95,  # 更多的选择
    messages=[{"role": "user", "content": "用比喻解释什么是HTTP"}]
)
```

### Temperature与top_p的关系

```python
# 经验法则：通常只设置一个，另一个用默认值
# 如果两者都调整，效果会叠加

# 低temperature + 低top_p = 极度确定性
(temperature=0.0, top_p=0.5)

# 高temperature + 高top_p = 极度创意
(temperature=1.0, top_p=0.99)
```

### 不同场景的参数推荐

| 场景 | Temperature | top_p | 说明 |
|------|-------------|-------|------|
| 代码生成 | 0.0-0.2 | 默认 | 需要确定性 |
| 数学计算 | 0.0 | 默认 | 需要准确答案 |
| 事实问答 | 0.1-0.3 | 默认 | 准确为主 |
| 文本分类 | 0.1-0.3 | 默认 | 一致性重要 |
| 摘要生成 | 0.3-0.5 | 默认 | 平衡准确和流畅 |
| 创意写作 | 0.7-0.9 | 0.95 | 需要多样性 |
| 头脑风暴 | 0.8-1.0 | 0.99 | 最大创意 |

### 实际应用示例

```python
def get_response(task_type, prompt, **kwargs):
    """根据任务类型返回不同采样参数"""
    configs = {
        "code": {"temperature": 0.1, "top_p": None},
        "math": {"temperature": 0.0, "top_p": None},
        "qa": {"temperature": 0.2, "top_p": None},
        "writing": {"temperature": 0.7, "top_p": 0.95},
        "brainstorm": {"temperature": 0.9, "top_p": 0.99},
    }
    
    config = configs.get(task_type, {"temperature": 0.5, "top_p": None})
    
    return client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=kwargs.get("max_tokens", 1024),
        **config,
        messages=[{"role": "user", "content": prompt}]
    )

# 使用
response = get_response("code", "写一个快排函数")
response = get_response("writing", "写一首关于月亮的诗")
```

---

## 2.6 提示词评估与迭代

### 评估维度

| 维度 | 指标 | 问题 |
|------|------|------|
| **准确性** | 输出正确率 | 答案是否正确？ |
| **一致性** | 多次输出相似度 | 相同输入结果稳定吗？ |
| **相关性** | 回答切题程度 | 回答在点子上吗？ |
| **完整性** | 是否覆盖所有要求 | 所有要点都回答了吗？ |
| **效率** | Token消耗 | 是否过度冗长？ |

### A/B测试框架

```python
import hashlib
from collections import Counter

def evaluate_prompt(prompt_v1, prompt_v2, test_cases, n=5):
    """A/B测试两个提示词"""
    results = {"v1": [], "v2": []}
    
    for test in test_cases:
        # 测试v1
        for _ in range(n):
            r1 = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt_v1.format(**test)}]
            )
            results["v1"].append(r1.content[0].text)
        
        # 测试v2
        for _ in range(n):
            r2 = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt_v2.format(**test)}]
            )
            results["v2"].append(r2.content[0].text)
    
    return results

# 计算一致性
def calculate_consistency(responses):
    """计算输出的一致性"""
    hashes = [hashlib.md5(r.encode()).hexdigest() for r in responses]
    counter = Counter(hashes)
    most_common = counter.most_common(1)[0][1]
    return most_common / len(responses)

# 示例
test_cases = [
    {"input": "5 + 3 = ?"},
    {"input": "10 - 7 = ?"},
    {"input": "6 * 6 = ?"},
]
results = evaluate_prompt(prompt_v1, prompt_v2, test_cases)

for version, responses in results.items():
    consistency = calculate_consistency(responses)
    print(f"{version}: 一致性 = {consistency:.1%}")
```

### 迭代优化流程

```python
def iterative_prompt_optimize(initial_prompt, test_cases, iterations=5):
    """迭代优化提示词"""
    current_prompt = initial_prompt
    
    for i in range(iterations):
        print(f"=== 迭代 {i+1} ===")
        
        # 收集当前版本的输出
        outputs = []
        for test in test_cases:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                temperature=0.0,
                messages=[{"role": "user", "content": current_prompt.format(**test)}]
            )
            outputs.append(response.content[0].text)
        
        # 人工评估（或用自动化指标）
        print("样本输出：")
        for j, (test, out) in enumerate(zip(test_cases[:2], outputs[:2])):
            print(f"输入: {test['input']}")
            print(f"输出: {out[:200]}...")
            print()
        
        # 根据评估结果修改提示词
       改进建议 = input("改进建议（直接回车跳过）：")
        if 改进建议:
            current_prompt = modify_prompt(current_prompt, 改进建议)
        else:
            print("跳过优化")
    
    return current_prompt

def modify_prompt(prompt, feedback):
    """根据反馈修改提示词"""
    # 这里可以实现自动化的提示词修改逻辑
    # 或者让Claude自己修改
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""优化以下提示词：

原始提示词：
{prompt}

改进建议：
{feedback}

请给出优化后的提示词，直接输出新的提示词内容："""
        }]
    )
    return response.content[0].text
```

### 自动化评估指标

```python
def automated_evaluation(output, expected, criteria):
    """自动化评估输出质量"""
    scores = {}
    
    # 1. 关键词覆盖
    if "criteria" in expected:
        keywords = expected["criteria"].split(",")
        found = sum(1 for k in keywords if k in output)
        scores["coverage"] = found / len(keywords)
    
    # 2. 长度合理性
    target_len = expected.get("length", 500)
    actual_len = len(output)
    scores["length_score"] = 1.0 - abs(actual_len - target_len) / target_len
    
    # 3. 格式检查
    if "format" in expected:
        format_ok = check_format(output, expected["format"])
        scores["format"] = 1.0 if format_ok else 0.0
    
    return scores

def check_format(output, format_spec):
    """检查输出格式是否符合规范"""
    if format_spec == "json":
        import json
        try:
            json.loads(output)
            return True
        except:
            return False
    elif format_spec == "table":
        return "|" in output and "---" in output
    return True
```

---

## 2.7 常见反模式

### 反模式1：过于复杂的提示词

```python
# ❌ 过度工程化
prompt = """你现在是一位在Google工作10年的资深软件工程师，拥有计算机博士学位，
专精于分布式系统和大数据处理。你需要根据以下原则审查代码：
1. 性能优先
2. 可读性第二
3. 维护性第三
...（300字规则列表）

请严格遵循以上原则，不要偏离。"""

# ✅ 简洁明了
prompt = """你是一位代码审查员。审查以下代码，关注性能和可读性。
用表格列出问题，每个问题包含：位置、问题、修复建议。"""
```

### 反模式2：约束条件冲突

```python
# ❌ 冲突的指令
prompt = """写一个Python函数：
- 必须简洁（1行）
- 必须包含详细注释
- 必须处理所有错误情况"""

# ✅ 合理的约束
prompt = """写一个Python函数，平衡简洁性和健壮性。
包含必要的注释（每个逻辑块一行），处理好主要错误。"""
```

### 反模式3：示例质量差

```python
# ❌ 示例与任务不匹配
prompt = """翻译成中文：
示例："Hello world" → "你好世界"
任务："Good morning" →"""

# ✅ 示例匹配任务风格
prompt = """翻译成中文（正式商务语气）：
示例："Thank you for your inquiry" → "感谢您的询盘"
示例："Please find attached" → "请见附件"
任务："We look forward to hearing from you" →"""
```

### 反模式4：忽视Token限制

```python
# ❌ 提示词太长，超出合理范围
prompt = """[粘贴整本手册内容]...
请基于以上内容回答：[具体问题]"""

# ✅ 只提供相关上下文
prompt = """关于[具体功能]的说明：
[提取相关段落]

基于以上信息，回答：[具体问题]"""
```

### 反模式5：不使用系统提示词

```python
# ❌ 所有指令都在用户消息中
response = client.messages.create(
    messages=[{
        "role": "user",
        "content": """你是一个翻译助手。
翻译时注意：
1. 保持原文语气
2. 使用自然的中文表达
3. 人名音译
...
[更多规则]

翻译："""
    }]
)

# ✅ 系统提示词设置角色，用户消息只做任务
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    system="""你是一位翻译助手。
规则：
1. 保持原文语气
2. 使用自然的中文表达
3. 人名音译""",
    messages=[{"role": "user", "content": "翻译：The quick brown fox..."}]
)
```

---

## 本章总结

### 核心知识点

| 知识点 | 掌握程度 | 关键点 |
|--------|----------|--------|
| 提示词原则 | ⭐⭐⭐⭐⭐ | 清晰、具体、结构化 |
| 系统提示词 | ⭐⭐⭐⭐⭐ | 角色设定、注入防范、动态切换 |
| Few-shot | ⭐⭐⭐⭐⭐ | 示例准确、数量适中、多样化 |
| Chain of Thought | ⭐⭐⭐⭐ | 复杂推理任务使用 |
| Temperature | ⭐⭐⭐⭐⭐ | 任务类型决定参数 |
| 评估迭代 | ⭐⭐⭐⭐ | A/B测试、自动化指标 |

### 参数速查表

| 场景 | Temperature | top_p |
|------|-------------|-------|
| 代码生成 | 0.0-0.2 | 默认 |
| 数学计算 | 0.0 | 默认 |
| 事实问答 | 0.1-0.3 | 默认 |
| 创意写作 | 0.7-0.9 | 0.95 |

### 下一步

- 继续阅读：工具调用专题（三）- 深入了解function calling（待发布）
- 实践项目：用Claude API构建一个智能客服系统
- 参考资料：[Anthropic Prompt Engineering Guide](https://docs.anthropic.com/)

---

**文档元信息**
难度：⭐⭐⭐⭐ | 类型：专家设计 | 更新日期：2026-03-25 | 预计阅读时间：50分钟 | 字数：约6500字
