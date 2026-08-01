---
title: "Claude API基础专题（二）：提示词工程"
date: "2026-03-25T10:30:00+08:00"
slug: "claude-api-prompting-engineering"
aliases:
  - /posts/tech/claude-api-prompting-engineering/
description: "系统讲解Claude API的提示词工程技巧，涵盖提示词原则、系统提示词、Few-shot学习、温度参数调节、链式思考等主题，帮助开发者掌握高效提示词设计方法。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "提示词", "Python"]
---

# Claude API 基础专题（二）：提示词工程

## 提示词基本原则

### 好的提示词需要什么

一段高质量的提示词，至少包含五个要素：

| 要素 | 说明 | 示例 |
|------|------|------|
| **角色/身份** | Claude 应该扮演什么角色 | "你是一位资深架构师" |
| **任务描述** | 需要完成什么任务 | "审查以下代码的安全性" |
| **上下文** | 相关的背景信息 | "这段代码是一个用户认证模块" |
| **输出格式** | 期望的返回格式 | "用表格列出所有问题" |
| **约束条件** | 任何限制或要求 | "不要修改原有代码逻辑" |

### 清晰明确

Claude 对模糊请求会给出模糊回答。

```python
# 模糊
response = client.messages.create(
    messages=[{"role": "user", "content": "帮我看看这段代码"}]
)

# 清晰
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

### 上下文充足

Claude 需要足够的信息才能给出有效回答。上下文不足的直接后果：

- 回答过于笼统，没有针对性
- 需要多轮澄清，浪费 token
- 理解偏差，答非所问

### 结构化

复杂任务拆解成清晰的部分，Claude 才能逐条处理：

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

## 系统提示词深度应用

### 系统提示词的作用

系统提示词（System Prompt）设置 Claude 的默认行为，影响整个对话。和用户消息不同，系统提示词不会被用户的输入覆盖。

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system="""你是一位专业代码审查员。

审查标准：
- 安全性（OWASP Top 10）
- 性能（时间/空间复杂度）
- 可读性（命名、注释、格式）
- 推荐做法（设计模式、语言特性）

回复格式：
## 总体评价
[简短总结]

## 问题列表
| 等级 | 位置 | 问题描述 | 修复建议 |

## 改进建议
[可选的额外优化建议]""",
    messages=[{"role": "user", "content": "审查以下代码..."}]
)
```

### 系统提示词的层级结构

```
# 角色定义
你是一位[专业领域]的[具体角色]。

# 主要职责
你的主要职责是：
1. [职责1]
2. [职责2]

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

### 防范提示词注入

当用户输入可能包含恶意指令时，系统提示词和用户消息必须分离：

```python
SYSTEM_PROMPT = """你是一个客服助手。
只回答与产品相关的问题。
当用户询问无关话题时，回复："抱歉，我只能帮助解决产品问题。" """

# 不安全：用户输入直接拼接到上下文
def create_messages(user_input):
    return [{"role": "user", "content": user_input}]

# 安全：系统提示词和用户消息分离
def create_messages(user_input, system_prompt):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": sanitize_input(user_input)}
    ]

def sanitize_input(text):
    dangerous_patterns = [
        "ignore previous instructions",
        "disregard your system prompt",
    ]
    for pattern in dangerous_patterns:
        text = text.replace(pattern, "[已过滤]")
    return text
```

### 动态系统提示词

根据场景切换系统提示词，比把所有规则塞进一个提示词里更可靠：

```python
class PromptManager:
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
- 先给结论，再给详细分析，最后给建议""",

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

## Few-shot 学习

### 什么是 Few-shot

在提示词中提供少量示例，让 Claude 学习任务的模式，比 zero-shot 更稳定。

```python
# Zero-shot
response = client.messages.create(
    messages=[{
        "role": "user",
        "content": "把以下中文翻译成英文：今天天气真好"
    }]
)

# Few-shot - 示例让输出更可预期
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
```

### 适用场景

| 场景 | 适合 Few-shot | 不适合 |
|------|-------------|--------|
| 格式化输出 | ✅ | |
| 特定风格 | ✅ | |
| 分类任务 | ✅ | |
| 简单问答 | | ❌ |
| 开放性对话 | | ❌ |
| 需要推理的复杂任务 | | ❌ |

### 推荐做法

**示例要多样化，覆盖不同边界情况：**

```python
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

**示例必须准确，一个错误示例就能带偏模型：**

```python
# 错误示例
prompt = """判断数字奇偶性：
示例：
- "5" → 奇数
- "8" → 偶数
- "3" → 偶数  ← 错误！

判断：
- "7" → """
```

**示例数量适中：**

| 任务复杂度 | 建议示例数 |
|-----------|-----------|
| 简单（分类、格式化） | 2-3个 |
| 中等（风格转换） | 3-5个 |
| 复杂（推理） | 5-10个 |

---

## 链式思考（Chain of Thought）

### 什么是 CoT

让 Claude 在给出最终答案之前先展示推理过程，能显著提升复杂任务的准确率。

```python
# 标准提示词 - 直接给答案
response = client.messages.create(
    messages=[{
        "role": "user",
        "content": "小明有5个苹果，小红给了他3个，小明吃掉了2个。小明现在有多少个苹果？"
    }]
)

# Chain of Thought - 展示推理
response = client.messages.create(
    messages=[{
        "role": "user",
        "content": """小明有5个苹果，小红给了他3个，小明吃掉了2个。小明现在有多少个苹果？

请逐步思考，展示计算过程。"""
    }]
)
```

### 何时使用 CoT

| 任务类型 | 使用 CoT | 示例 |
|---------|--------|------|
| 数学问题 | ✅ 必须 | "计算 153 * 47" |
| 逻辑推理 | ✅ 必须 | "如果 A>B，B>C，问 A 和 C 的关系" |
| 代码调试 | ✅ 建议 | "分析这段代码为什么报错" |
| 事实问答 | ❌ 不需要 | "中国的首都是哪里" |
| 简单分类 | ❌ 不需要 | "判断这个评论是正面还是负面" |
| 创意写作 | ❌ 不需要 | "写一首关于春天的诗" |

### CoT 变体

**显式步骤指引：**

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

**自我验证：**

```python
prompt = """判断以下论述是否正确："所有鸟都会飞"

思考步骤：
1. 列出所有会飞的鸟
2. 列出所有不会飞的鸟
3. 找一个反例（不会飞的鸟）
4. 得出结论"""
```

### 注意

不要在简单任务上滥用 CoT，它会白白增加 token 消耗。只在需要推理链条的任务上使用。

---

## Temperature 与采样参数

### Temperature 的作用

Temperature 控制输出概率分布的平滑程度，影响随机性：

| Temperature | 效果 | 适用场景 |
|-------------|------|----------|
| 0.0 | 几乎确定 | 代码生成、数学计算 |
| 0.2-0.4 | 低随机性 | 事实问答、分类 |
| 0.5-0.7 | 中等随机性 | 一般对话、写作 |
| 0.8-1.0 | 高随机性 | 创意写作、脑暴 |
| >1.0 | 极高随机性 | 特殊场景（可能失控） |

```python
# 确定性输出 - 每次结果都一样
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=100,
    temperature=0.0,
    messages=[{"role": "user", "content": "1+1等于几？"}]
)

# 创意输出 - 每次结果可能不同
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=200,
    temperature=0.9,
    messages=[{"role": "user", "content": "写一个关于AI的科幻短故事开头"}]
)
```

### top_p 参数

top_p（核采样）从累积概率达到 p 的词集中采样。值越小，候选词越少。

```python
# 保守输出
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    temperature=0.3,
    top_p=0.5,
    messages=[{"role": "user", "content": "解释什么是HTTP"}]
)

# 创意输出
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    temperature=0.8,
    top_p=0.95,
    messages=[{"role": "user", "content": "用比喻解释什么是HTTP"}]
)
```

经验法则：通常只调整 temperature 或 top_p 中的一个，另一个用默认值。两者都改时效果会叠加。

### 不同场景的参数推荐

| 场景 | Temperature | top_p | 说明 |
|------|-------------|-------|------|
| 代码生成 | 0.0-0.2 | 默认 | 确定性优先 |
| 数学计算 | 0.0 | 默认 | 准确优先 |
| 事实问答 | 0.1-0.3 | 默认 | 准确为主 |
| 文本分类 | 0.1-0.3 | 默认 | 一致性重要 |
| 摘要生成 | 0.3-0.5 | 默认 | 平衡准确和流畅 |
| 创意写作 | 0.7-0.9 | 0.95 | 需要多样性 |
| 头脑风暴 | 0.8-1.0 | 0.99 | 最大创意 |

### 实际应用

```python
def get_response(task_type, prompt, **kwargs):
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

response = get_response("code", "写一个快排函数")
response = get_response("writing", "写一首关于月亮的诗")
```

---

## 提示词评估与迭代

### 评估维度

| 维度 | 问题 |
|------|------|
| **准确性** | 输出正确率如何？ |
| **一致性** | 相同输入下结果稳定吗？ |
| **相关性** | 回答是否切题？ |
| **完整性** | 所有要点都覆盖了吗？ |
| **效率** | Token 消耗是否合理？ |

### A/B 测试框架

```python
import hashlib
from collections import Counter

def evaluate_prompt(prompt_v1, prompt_v2, test_cases, n=5):
    results = {"v1": [], "v2": []}

    for test in test_cases:
        for _ in range(n):
            r1 = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt_v1.format(**test)}]
            )
            results["v1"].append(r1.content[0].text)

        for _ in range(n):
            r2 = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt_v2.format(**test)}]
            )
            results["v2"].append(r2.content[0].text)

    return results

def calculate_consistency(responses):
    hashes = [hashlib.md5(r.encode()).hexdigest() for r in responses]
    counter = Counter(hashes)
    most_common = counter.most_common(1)[0][1]
    return most_common / len(responses)
```

### 迭代优化流程

```python
def iterative_prompt_optimize(initial_prompt, test_cases, iterations=5):
    current_prompt = initial_prompt

    for i in range(iterations):
        print(f"=== 迭代 {i+1} ===")
        outputs = []
        for test in test_cases:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                temperature=0.0,
                messages=[{"role": "user", "content": current_prompt.format(**test)}]
            )
            outputs.append(response.content[0].text)

        print("样本输出：")
        for j, (test, out) in enumerate(zip(test_cases[:2], outputs[:2])):
            print(f"输入: {test['input']}")
            print(f"输出: {out[:200]}...")
            print()

        feedback = input("改进建议（直接回车跳过）：")
        if feedback:
            current_prompt = modify_prompt(current_prompt, feedback)
        else:
            print("跳过优化")

    return current_prompt

def modify_prompt(prompt, feedback):
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

---

## 常见反模式

### 1. 提示词过于复杂

```python
# 过度工程化
prompt = """你现在是一位在Google工作10年的资深软件工程师，拥有计算机博士学位，
专精于分布式系统和大数据处理。你需要根据以下原则审查代码：
1. 性能优先
2. 可读性第二
3. 维护性第三
...（300字规则列表）"""

# 简洁明确
prompt = """你是一位代码审查员。审查以下代码，关注性能和可读性。
用表格列出问题，每个问题包含：位置、问题、修复建议。"""
```

### 2. 约束条件自相矛盾

```python
# 冲突：既要1行又要详细注释
prompt = """写一个Python函数：
- 必须简洁（1行）
- 必须包含详细注释
- 必须处理所有错误情况"""

# 合理
prompt = """写一个Python函数，平衡简洁性和健壮性。
包含必要的注释（每个逻辑块一行），处理好主要错误。"""
```

### 3. 示例与任务不匹配

```python
# 示例风格和任务风格不一致
prompt = """翻译成中文：
示例："Hello world" → "你好世界"
任务："Good morning" →"""

# 示例匹配任务风格
prompt = """翻译成中文（正式商务语气）：
示例："Thank you for your inquiry" → "感谢您的询盘"
示例："Please find attached" → "请见附件"
任务："We look forward to hearing from you" →"""
```

### 4. 忽视 Token 限制

把整本手册塞进提示词让 Claude "基于以上内容回答"，不如只提取相关段落。

### 5. 所有指令都塞进用户消息

```python
# 不推荐
response = client.messages.create(
    messages=[{
        "role": "user",
        "content": """你是一个翻译助手。翻译时注意：
1. 保持原文语气
2. 使用自然的中文表达
3. 人名音译
翻译：The quick brown fox..."""
    }]
)

# 推荐：角色设定放系统提示词，用户消息只做任务
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

## 参数速查

| 场景 | Temperature | top_p |
|------|-------------|-------|
| 代码生成 | 0.0-0.2 | 默认 |
| 数学计算 | 0.0 | 默认 |
| 事实问答 | 0.1-0.3 | 默认 |
| 创意写作 | 0.7-0.9 | 0.95 |

**参考资源：** [Anthropic Prompt Engineering Guide](https://docs.anthropic.com/)