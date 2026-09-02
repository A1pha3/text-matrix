---
title: "Claude API 基础专题（二）：提示词工程"
date: "2026-03-25T10:30:00+08:00"
slug: "claude-api-prompting-engineering"
aliases:
  - /posts/tech/claude-api-prompting-engineering/
description: "系统讲解 Claude API 的提示词工程技巧：提示词的基本原则、系统提示词、Few-shot 学习、链式思考与扩展思考、温度与采样参数、提示词评估与迭代、常见反模式与排查。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "提示词", "Python"]
---

# Claude API 基础专题（二）：提示词工程

> **目标读者**：正在用 Claude API 写应用、希望输出更稳定可用的开发者
> **前置知识**：了解 Messages API 的基本调用，会用 Python 调 `client.messages.create`
> **学习目标**：学完能独立判断一条提示词哪里写得不好、知道该改什么，能针对任务选对系统提示词、示例、思考模式和采样参数，并有一套评估迭代的方法

提示词的质量直接决定 API 输出的下限。同一个模型，一句话和一段设计过的提示词，产出的可能一个是空泛套话，一个是能直接进代码评审的答案。这一篇不讲玄学，只讲 Claude 上能验证、可操作的写法。

读完本文你会得到一条完整的主线：**先想清楚任务要什么（要素），再用结构把任务讲清楚（清晰、上下文、结构化），最后按任务类型挑对辅助手段（系统提示词、示例、思考模式、采样参数）**。

章节导航：

1. [提示词基本原则](#提示词基本原则)
2. [系统提示词深度应用](#系统提示词深度应用)
3. [Few-shot 学习](#few-shot-学习)
4. [链式思考与扩展思考](#链式思考与扩展思考)
5. [Temperature 与采样参数](#temperature-与采样参数)
6. [提示词评估与迭代](#提示词评估与迭代)
7. [常见反模式](#常见反模式)
8. [常见问题与排查](#常见问题与排查)

---

## 提示词基本原则

### 好的提示词需要什么

一段高质量的提示词，至少包含五个要素。缺哪个，Claude 就会在哪个环节含糊：

| 要素 | 说明 | 示例 |
|------|------|------|
| **角色/身份** | Claude 应该扮演什么角色 | "你是一位资深架构师" |
| **任务描述** | 需要完成什么任务 | "审查以下代码的安全性" |
| **上下文** | 相关的背景信息 | "这段代码是一个用户认证模块" |
| **输出格式** | 期望的返回格式 | "用表格列出所有问题" |
| **约束条件** | 任何限制或要求 | "不要修改原有代码逻辑" |

这五要素不是固定模板，而是自查清单。写提示词卡住时，逐项问自己：角色定清楚了吗？任务动词明确吗？上下文给够了吗？格式说清楚了吗？有没有边界？漏掉任何一项，输出就会朝不可控的方向漂。

### 清晰明确

Claude 对模糊请求会给出模糊回答，这不算模型的错，是输入没给足信息。

```python
from anthropic import Anthropic

client = Anthropic()

# 模糊：任务、背景、格式全都不明
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "帮我看看这段代码"}]
)

# 清晰：任务动词、代码、输出要求一次说清
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": """审查下面这段 Python 代码的安全性：

    def get_user(user_id):
        query = f"SELECT * FROM users WHERE id = {user_id}"
        return db.execute(query)

请用表格列出：
1. 所有安全漏洞
2. 每个漏洞的风险等级（高/中/低）
3. 修复建议"""
    }]
)
```

判定标准很简单：把提示词拿给一个只懂技术的同事看，如果对方需要追问才能动手，Claude 也一样会猜。

### 上下文充足

Claude 需要足够信息才能给出有效回答。上下文不足的直接后果：

- 回答过于笼统，没有针对性
- 需要多轮澄清，浪费 token
- 理解偏差，答非所问

给上下文不是把资料整段丢进去。先想清楚"这个任务最终结果用在哪儿、给谁看"，再把相关的那部分信息放进来。和答案无关的大段资料只会稀释注意力。

### 结构化

复杂任务拆成带标记的区块，Claude 才能逐条处理。用 `## 数据`、`## 分析维度`、`## 输出要求` 这类分区，相当于给 Claude 画了流程图：

```python
prompt = """你是一位数据分析师。请分析以下销售数据。

## 数据
[销售数据JSON]

## 分析维度
1. 整体趋势：月度销售额变化
2. 地域分布：各地区占比
3. 产品表现：TOP 5 产品
4. 异常检测：识别异常值

## 输出要求
- 每个维度用小标题
- 包含数据可视化建议（ASCII 图表）
- 最后给出 3 个可执行的建议
"""

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=2000,
    messages=[{"role": "user", "content": prompt}]
)
```

分区标记的作用是给指令和内容划定边界，让 Claude 知道哪段是任务、哪段是素材、哪段是格式要求。复杂提示词里，区块比大段散文更容易被正确执行。

---

## 系统提示词深度应用

### 系统提示词的作用

系统提示词（System Prompt）设置 Claude 的默认行为，影响整个对话，且不会轻易被用户输入覆盖。在 Messages API 里，系统提示词放在**顶层 `system` 参数**，不是放在消息数组里——Claude 的消息里没有 `system` 这个角色，写 `{"role": "system", ...}` 会直接报错。

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

系统提示词最适合放两类内容：一类是"无论用户问什么都要遵守"的规则，另一类是跨请求复用的背景设定。它会反复参与每轮生成，所以别把一次性任务细节塞进去——那会白白占用每次请求的输入 token。

### 系统提示词的层级结构

一段可维护的系统提示词，通常按职责分层：

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

分层的意义在于改起来容易：要加一条约束，就改"行为约束"区块；要换输出格式，就动"输出格式"区块，不用整段重写。

### 防范提示词注入

当你的应用把用户输入拼进提示词时，需要把它当成不可信数据来对待。这里先纠正一个常见误区：**靠关键词过滤"请忽略之前的指令"这类黑名单，防不住注入**。攻击者换一种措辞、用 base64、或改变大小写就能绕过，过滤器只制造虚假的安全感。

正确做法是隔离和校验：

1. **隔离**：系统提示词走顶层 `system` 参数，用户输入只进 `user` 消息，两者天然分离。绝不把用户输入直接拼进系统提示词。
2. **校验工具调用**：Claude 想调用工具时，返回的是 `tool_use` 请求，真正执行前由你的代码校验参数。比如 Claude 要读文件，先检查路径是否在白名单目录内。
3. **把模型输出当不可信数据**：Claude 生成的文本、工具参数，在做权限判断、执行命令、写入数据前都要二次确认，尤其是面向公众的输入。

```python
# 安全：系统提示词与用户输入分通道，用户输入不参与系统提示词拼装
def create_messages(user_input: str):
    system = (
        "你是一个客服助手。只回答与产品相关的问题。"
        "当用户询问无关话题时，回复：抱歉，我只能帮助解决产品问题。"
    )
    return system, [{"role": "user", "content": user_input}]

# 调用时把 system 放在顶层参数
system, messages = create_messages(user_input)
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system=system,
    messages=messages,
)
```

注入防护的完整边界超出本文范围，但记住一个判断：任何让"用户输入影响系统行为"的路径，都要在代码层拦一道，而不是指望提示词或过滤器兜底。

### 动态系统提示词

按场景切换系统提示词，比把所有规则塞进一个提示词里更可靠。不同任务对角色、格式的要求完全不同，混在一起反而互相干扰：

```python
class PromptManager:
    SYSTEM_PROMPTS = {
        "code_review": """你是一位资深代码审查员。

职责：
1. 发现代码中的 bug 和安全漏洞
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
    def get_prompt(cls, task_type: str) -> str:
        return cls.SYSTEM_PROMPTS.get(task_type, cls.SYSTEM_PROMPTS["writing"])
```

场景化系统提示词还有一个好处：每个场景的提示词独立演进，改一个不影响其他场景。场景多起来之后，建议把提示词从代码里挪到配置或独立文件，方便非工程师一起维护。

---

## Few-shot 学习

### 什么是 Few-shot

在提示词里给出少量输入-输出示例，让 Claude 照着模式输出，比 zero-shot（不给示例）更稳定。示例传递的是"输出长什么样"，Claude 对格式和风格的模仿能力很强。

```python
# Zero-shot：只给任务
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "把以下中文翻译成英文：今天天气真好"
    }]
)

# Few-shot：给示例，输出更可预期
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
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

判断标准：任务里"输出长什么样"比"怎么思考"更重要，Few-shot 就划算；任务依赖长链条推理，Few-shot 帮不上忙，那是扩展思考的领域。

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
# 错误示例：第 3 条标注错了，模型会被带偏
prompt = """判断数字奇偶性：
示例：
- "5" → 奇数
- "8" → 偶数
- "3" → 偶数  ← 错误！

判断：
- "7" → """
```

**示例数量适中，不是越多越好：**

| 任务复杂度 | 建议示例数 |
|-----------|-----------|
| 简单（分类、格式化） | 2-3 个 |
| 中等（风格转换） | 3-5 个 |
| 复杂（推理） | 5-10 个 |

示例太多会挤占上下文，且给 Claude 更多可模仿的错误模式。够用就行，重点是每个示例都覆盖一个真实的输入形态。

---

## 链式思考与扩展思考

"让模型多想想"在 Claude 上有两种做法：提示词层面的链式思考，和 API 层面的扩展思考（Extended Thinking）。先分清两者的差别，再决定用哪个。

### 链式思考（CoT）提示

在提示词里要求 Claude 先展示推理过程再给答案，能提升复杂任务的准确率。这是一种提示词技巧，不依赖 API 参数：

```python
# 标准提示词 - 直接给答案
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "小明有 5 个苹果，小红给了他 3 个，小明吃掉了 2 个。小明现在有多少个苹果？"
    }]
)

# 链式思考 - 要求展示推理
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": """小明有 5 个苹果，小红给了他 3 个，小明吃掉了 2 个。小明现在有多少个苹果？

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

给推理任务一个明确的步骤结构，比一句笼统的"请思考"更可靠：

```python
prompt = """分析以下代码的性能问题。

代码：
    def find_duplicates(arr):
        result = []
        for i in range(len(arr)):
            for j in range(len(arr)):
                if arr[i] == arr[j] and i != j:
                    result.append(arr[i])
        return list(set(result))

分析步骤：
1. 识别代码的时间复杂度
2. 找出具体的性能瓶颈
3. 提出优化方案
4. 给出优化后的代码"""
```

也可以在推理后加一步自我验证，让 Claude 检查结论是否满足约束：

```python
prompt = """某物流规则规定：重量超过 20 公斤的包裹需要额外缴费。请核对下面这条陈述是否正确。

陈述："15 公斤的包裹不需要额外缴费。"

思考步骤：
1. 写出规则的触发条件（重量 > 20 公斤）
2. 对比给定包裹的重量
3. 检查是否满足触发条件
4. 给出结论并说明依据"""
```

**注意**：不要在简单任务上滥用 CoT。事实问答、简单分类这类任务让它"逐步思考"只会白白增加 token 消耗，甚至让答案变啰嗦。

### 扩展思考（Extended Thinking）

扩展思考是 API 层的能力，让 Claude 在给出答案前，用一段显式的内部推理来探索和检验思路。对 Claude 4 系列模型，它比"提示词里求它想"更可靠，因为推理由模型原生完成，且不会占用给你看的输出格式。

开启方式是在请求里加 `thinking` 参数：

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=8192,
    thinking={
        "type": "enabled",
        "budget_tokens": 4096,
    },
    messages=[{
        "role": "user",
        "content": "设计一个在 O(n) 时间内找出数组中出现次数最多的元素的算法，并说明为什么你的方案正确。"
    }]
)

# 响应里会先出现 thinking 块，再出现 text 块
for block in response.content:
    if block.type == "thinking":
        print("推理过程:", block.thinking)
    elif block.type == "text":
        print("最终答案:", block.text)
```

几个必须知道的约束：

- `budget_tokens` 是 Claude 可用于内部思考的 token 上限，**最小 1024**，且必须**小于 `max_tokens`**。
- 预算给得大，复杂问题往往答得更细，但延迟和成本都上升；预算超过约 32k 后，模型通常用不满，收益递减。
- 响应中的 `thinking` 块带 `signature`，多轮对话时原样传回即可，不需要自己保存推理内容。
- 型号差异：`claude-sonnet-4-20250514` 支持手动 `thinking` 配置；较新的 Opus 4.6 / Sonnet 4.6 推荐用 `thinking: {"type": "adaptive"}`（自适应思考），让模型自己决定想多深，需要控制深度时配合 `effort` 参数。

### 扩展思考与 CoT 提示怎么选

- **开了扩展思考，就不要再让模型"请逐步思考"**。两者叠加会降低效果，Anthropic 的指南明确建议：使用扩展思考时不要再用 step-by-step 提示。
- 简单推理（一步两步能算清的）：CoT 提示就够，别开扩展思考，省延迟省 token。
- 复杂推理（数学证明、算法设计、深度分析、多步代理任务）：用扩展思考。
- 扩展思考下的 CoT 提示仍可以给出任务的具体边界和约束，只是不要要求它把推理过程写出来——模型自己会想。

---

## Temperature 与采样参数

### Temperature 的作用

`temperature` 控制生成时概率分布的平滑程度，值越高输出越多样，值越低越稳定。Claude API 的取值范围是 **0.0 到 1.0**，传大于 1.0 的值会被拒绝并报 400 错误。

| Temperature | 效果 | 适用场景 |
|-------------|------|----------|
| 0.0 | 几乎确定 | 代码生成、数学计算 |
| 0.2-0.4 | 低随机性 | 事实问答、分类 |
| 0.5-0.7 | 中等随机性 | 一般对话、写作 |
| 0.8-1.0 | 高随机性 | 创意写作、脑暴 |

```python
# 确定性输出 - 每次结果基本一致
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

一个容易踩的坑：`temperature=0` 不等于绝对确定。它只是把采样压到最高概率 token，模型底层仍有波动，长输出和复杂任务下仍可能出现差异。追求可复现时，把它当"尽力而为"，不要当保证。

### top_p 参数

`top_p`（核采样）从累积概率达到 p 的词集中采样。值越小，候选词越少，输出越保守。

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

经验法则：通常只调 `temperature` 或 `top_p` 中的一个，另一个用默认值。两个都改，效果叠加但难以预测，排查时也分不清是谁导致的。

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

这些数字是起点不是终点。生产环境里，最终值应该来自你对自己任务的实际测试，而不是照抄表格。

### 实际应用

把参数和任务类型绑定，写一个简单的配置分发函数：

```python
def get_response(task_type: str, prompt: str, **kwargs):
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

把参数集中在配置里，而不是散落在每个调用处，后续调参只需要改一个地方。

---

## 提示词评估与迭代

提示词很少一次写对，评估和迭代是常规工作。先定评估口径，再跑对照实验。

### 评估维度

| 维度 | 问题 |
|------|------|
| **准确性** | 输出正确率如何？ |
| **一致性** | 相同输入下结果稳定吗？ |
| **相关性** | 回答是否切题？ |
| **完整性** | 所有要点都覆盖了吗？ |
| **效率** | Token 消耗是否合理？ |

一致性可以用输出哈希的重复率量化——相同输入、相同参数下，输出的哈希越集中，说明越稳定：

```python
import hashlib
from collections import Counter


def calculate_consistency(responses: list[str]) -> float:
    hashes = [hashlib.md5(r.encode()).hexdigest() for r in responses]
    counter = Counter(hashes)
    most_common = counter.most_common(1)[0][1]
    return most_common / len(responses)
```

### A/B 测试框架

对比两版提示词时，同一批测试用例、同一参数、跑多次，才能排除随机波动：

```python
def evaluate_prompt(prompt_v1: str, prompt_v2: str, test_cases: list[dict], n: int = 5):
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
```

注意两点：对照实验里 `temperature` 要固定（通常 0.0），否则差异分不清来自提示词还是随机性；测试用例要覆盖典型输入和边界输入，只测一条"完美输入"得不出可靠结论。

### 迭代优化流程

比较粗糙但有效的迭代方式是：跑一批用例，人工看输出找问题，把改进意见喂回给模型让它改提示词，再跑下一轮：

```python
def iterative_prompt_optimize(initial_prompt: str, test_cases: list[dict], iterations: int = 5):
    current_prompt = initial_prompt

    for i in range(iterations):
        print(f"=== 迭代 {i + 1} ===")
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


def modify_prompt(prompt: str, feedback: str) -> str:
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

人工看输出是最关键的一环：模型不会告诉你它哪里理解错了，只有你对照测试用例能看出来。

---

## 常见反模式

### 1. 提示词过于复杂

把角色、经验、规则堆成几百字，Claude 抓不住重点。

```python
# 过度工程化
prompt = """你是一位在 Google 工作 10 年的资深软件工程师，拥有计算机博士学位，
专精于分布式系统和大数据处理。请按以下 12 条原则审查代码：
1. 性能优先 2. 可读性第二 3. 维护性第三 4. 安全第一 5. 兼容性
6. 扩展性 7. 测试覆盖 8. 文档完整 9. 命名规范 10. 错误处理
11. 日志规范 12. 代码风格（每条再展开 50 字说明，并给出反例）"""

# 简洁明确
prompt = """你是一位代码审查员。审查以下代码，关注性能和可读性。
用表格列出问题，每个问题包含：位置、问题、修复建议。"""
```

### 2. 约束条件自相矛盾

```python
# 冲突：既要 1 行又要详细注释，Claude 只能选一个满足
prompt = """写一个 Python 函数：
- 必须简洁（1 行）
- 必须包含详细注释
- 必须处理所有错误情况"""

# 合理：明确优先级
prompt = """写一个 Python 函数，平衡简洁性和健壮性。
包含必要的注释（每个逻辑块一行），处理好主要错误。"""
```

### 3. 示例与任务不匹配

```python
# 示例风格和任务风格不一致
prompt = """翻译成中文：
示例："Hello world" → "你好世界"
任务："Good morning" →"""

# 示例匹配任务风格（正式商务语气）
prompt = """翻译成中文（正式商务语气）：
示例："Thank you for your inquiry" → "感谢您的询盘"
示例："Please find attached" → "请见附件"
任务："We look forward to hearing from you" →"""
```

### 4. 忽视 Token 限制

把整本手册塞进提示词让 Claude "基于以上内容回答"，不如只提取相关段落。上下文窗口不是无限的，塞得越满，每轮请求越贵越慢，模型也越容易在无关内容里迷失。

### 5. 所有指令都塞进用户消息

```python
# 不推荐：角色设定混在用户消息里，且每次都要重复
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
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
    max_tokens=1024,
    system="""你是一位翻译助手。
规则：
1. 保持原文语气
2. 使用自然的中文表达
3. 人名音译""",
    messages=[{"role": "user", "content": "翻译：The quick brown fox..."}]
)
```

---

## 常见问题与排查

**为什么代码里写 `{"role": "system", ...}` 会报错？**

Claude 的 Messages API 没有 `system` 消息角色。系统提示词必须放在顶层 `system` 参数。消息数组里只有 `user` 和 `assistant` 两种角色。

**提示词里加了"请逐步思考"，输出反而变差？**

检查是否同时开了扩展思考（`thinking` 参数）。两者叠加会降低效果，使用扩展思考时不要再要求模型展示 step-by-step 推理。

**`temperature` 传 1.5 为什么报 400？**

Claude API 的 `temperature` 只接受 0.0-1.0。需要更多随机性时，用 1.0 并配合调高 `top_p`，或者考虑任务本身是否需要这么高的多样性。

**相同输入，输出总是不一样，怎么固定？**

把 `temperature` 降到 0。但要明白这只能大幅降低差异，不能保证完全一致——模型底层采样仍有波动。追求严格可复现的测试，更适合固定 prompt 跑对照，而不是依赖参数。

**示例给了很多，效果反而变差？**

示例数量不是越多越好。检查示例是否相互矛盾、是否覆盖了错误模式、是否和任务风格一致。把明显错误的示例删掉，保留覆盖边界情况的那几个。

**关键词过滤能防提示词注入吗？**

不能。过滤器只挡已知写法，攻击者换个说法就绕过了。正确做法是隔离（用户输入只进 `user` 消息）+ 校验（工具调用前检查参数）+ 把模型输出当不可信数据。

---

## 参数速查

| 场景 | Temperature | top_p |
|------|-------------|-------|
| 代码生成 | 0.0-0.2 | 默认 |
| 数学计算 | 0.0 | 默认 |
| 事实问答 | 0.1-0.3 | 默认 |
| 创意写作 | 0.7-0.9 | 0.95 |

---

## 接着往下走

把本文的示例在本地跑通一遍，能加深不少理解。建议这样练：

写一个"提取+分类"双任务提示词，先写一版 zero-shot，再加 3-5 个示例，跑同一批输入对比两者的稳定性和错误类型。重点观察：示例在哪些输入上仍然失效，以及模型是"跟着格式"还是"理解语义"。

对同一个任务同时开/关扩展思考（`thinking` 参数）跑一轮，记录延迟、token 消耗和输出质量。这能帮你建立"什么复杂度值得开思考"的直觉。

本系列其余专题分别覆盖 API 基础、工具调用、RAG、MCP 与 Agent；协议细节以 [Anthropic 官方文档](https://docs.anthropic.com/) 为准。

相关参考：

- [Anthropic 提示词工程文档](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)
- [扩展思考（Extended Thinking）](https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking)
- [Messages API 参考](https://docs.anthropic.com/en/api/messages)

---

*字数：约 5600 字 | 更新日期：2026-03-25*
