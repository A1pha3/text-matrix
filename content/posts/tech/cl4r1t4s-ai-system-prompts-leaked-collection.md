---
title: "CL4R1T4S：15433 Stars的AI系统提示词泄露宝库——从入门到精通"
date: 2026-04-19T20:58:00+08:00
slug: "cl4r1t4s-ai-system-prompts-leaked-collection"
description: "CL4R1T4S是 elder-plinius 创建的15433 Stars开源项目，收集了OpenAI、Anthropic、Google、xAI、Perplexity、Cursor、Devin、Replit等主流AI系统的完整泄露系统提示词。本文深入分析AI透明度运动、系统提示词工程、以及这些隐藏指令对AI行为的深远影响。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "SystemPrompt", "LLM", "AI透明度", "AI安全", "提示词工程", "AI治理"]
---

# CL4R1T4S：15433 Stars的AI系统提示词泄露宝库——从入门到精通

> **目标读者**：AI研究者、提示词工程师、安全研究员、对AI透明度有兴趣的开发者
> **预计阅读时间**：50-70分钟
> **前置知识**：了解LLM基本原理、有过AI使用经验、对AI伦理有基础认知
> **难度定位**：⭐⭐⭐⭐ 专家设计

---

## §1 项目概述：CL4R1T4S是什么

### 1.1 项目基本信息

| 属性 | 值 |
|------|-----|
| **仓库** | github.com/elder-plinius/CL4R1T4S |
| **Stars** | 15,433 |
| **Forks** | 3,154 |
| **许可证** | AGPL-3.0 |
| **创建者** | @elder_plinius |

项目名称"CL4R1T4S"是"CLARITAS"的变形——在罗马神话中代表"清晰"与"洞察"——暗示这个项目的核心使命：**让AI系统的隐藏逻辑变得透明可见**。

### 1.2 项目宣言

> *"In order to trust the output, one must understand the input."*
> "要信任输出，就必须理解输入。"

AI公司通过海量的、看不见的提示词支架（prompt scaffold）来塑造模型行为。由于AI已成为越来越多人信任的外部智能层，这些隐藏指令直接影响着公众的感知和行为。

### 1.3 核心价值

CL4R1T4S收集的泄露系统提示词定义了：

- **AI不能说什么**：内容边界和禁忌话题
- **AI必须遵循的角色和功能**：人格设定、能力边界
- **AI如何被指示撒谎、拒绝或转移话题**：规避策略
- **默认植入的伦理和政治框架**：价值观倾向

> ⚠️ **警示**：如果你在不了解AI系统提示词的情况下与它对话，你对话的不是中立智能——而是木偶背后的影子。

---

## §2 仓库全景：覆盖的AI系统一览

### 2.1 AI公司模型（8家）

| 公司 | 收录模型 | 文件示例 |
|------|----------|----------|
| **OpenAI** | ChatGPT-4o/4.1/o3/o4-mini、Codex | ChatGPT-4o_Sep-27-25.txt |
| **Anthropic** | Claude全系列（4/4.1/4.5/4.7）、Claude Code | Claude-Opus-4.7.txt |
| **Google** | Gemini全系列 | Gemini_Ultra_*.txt |
| **xAI** | Grok | Grok_*.txt |
| **Perplexity** | AI回答引擎 | Perplexity_*.txt |
| **Meta** | Llama系列（部分） | Llama_*.txt |
| **Mistral** | Mistral Large | Mistral_*.txt |
| **Moonshot** | Kimi | Kimi_*.txt |
| **MiniMax** | 海螺AI | MiniMax_*.txt |

### 2.2 AI编码助手（15+款）

| 工具 | 定位 | 收录文件 |
|------|------|----------|
| **Cursor** | AI代码编辑器 | CURSOR/*.txt |
| **Windsurf** | Codeium旗下AI IDE | WINDSURF/*.txt |
| **Claude Code** | Anthropic官方CLI工具 | Claude_Code_*.md |
| **Devin** | Cognition AI软件工程师 | DEVIN/*.txt |
| **Replit** | AI编程平台 | REPLIT/*.txt |
| **Vercel v0** | 前端AI生成 | VERCEL_V0/*.txt |
| **Bolt** | Rust全栈AI工具 | BOLT/*.txt |
| **Cline** | VS Code AI插件 | CLINE/*.txt |
| **Cluely** | 全栈AI助手 | CLUELY/*.txt |
| **Factory** | AI代码审查 | FACTORY/*.txt |
| **Lovable** | AI应用构建 | LOVABLE/*.txt |
| **Manus** | AI任务执行 | MANUS/*.txt |
| **MultiOn** | AI浏览器控制 | MULTION/*.txt |
| **DIA** | AI设计助手 | DIA/*.txt |
| **Hume** | 共情AI | HUME/*.txt |

### 2.3 收录文件格式

```
ANTHROPIC/
├── Claude-Opus-4.7.txt          # 最新版本
├── Claude-4.5-Opus.txt          # 次新版
├── Claude_Sonnet-4.5_Sep-29-2025.txt  # 按日期命名
├── Claude_Code_03-04-24.md      # Claude Code工具
└── Claude-Design-Sys-Prompt.txt # 设计专用提示词

OPENAI/
├── ChatGPT-4o_Sep-27-25.txt     # 带日期戳
├── ChatGPT_o3_o4-mini_04-16-2025
├── Codex_Sep-15-2025.md         # 编程模型
└── ChatKit_Docs__Oct-6-25.txt
```

---

## §3 系统提示词工程：AI行为的隐形指挥棒

### 3.1 什么是系统提示词

系统提示词（System Prompt）是LLM的"宪法"——它定义了模型的基础行为边界、人格特征、能力范围和规避策略。

```
┌─────────────────────────────────────────────────────────────┐
│                      LLM Query Flow                          │
│                                                              │
│  ┌─────────────┐                                           │
│  │ System      │ ← 隐藏的"宪法"：定义行为边界                │
│  │ Prompt      │                                           │
│  └──────┬──────┘                                           │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────┐                                           │
│  │ User Query  │ ← 用户的具体问题                          │
│  └──────┬──────┘                                           │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────┐                                           │
│  │   LLM       │ ← 在System Prompt的约束下生成回答          │
│  │   Response  │                                           │
│  └─────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 系统提示词的核心组成

典型的系统提示词包含以下组成部分：

| 组成部分 | 功能 | 示例 |
|----------|------|------|
| **角色定义** | 设定AI的身份和人格 | "You are a helpful assistant" |
| **能力边界** | 定义可以做什么、不可以做什么 | "You cannot provide medical advice" |
| **响应格式** | 规定输出的结构 | "Always respond in JSON format" |
| **规避策略** | 遇到敏感话题时的处理方式 | "If asked about X, redirect to Y" |
| **价值观框架** | 隐含的伦理和政治倾向 | "Prioritize truthfulness over pleasing" |
| **知识截止** | 模型的知识时间边界 | "Knowledge cutoff: 2024-06" |

### 3.3 系统提示词的重要性

**为什么系统提示词如此重要？**

1. **行为控制**：几乎所有你以为的"AI性格"实际上都是提示词工程的结果
2. **内容审核**：AI"不愿意"讨论的话题通常是被提示词禁止的，而非模型能力限制
3. **价值观传递**：默认的伦理框架被编码在提示词中
4. **能力表现**：同样的模型，不同提示词可以表现出截然不同的能力

---

## §4 泄露提示词分析：揭示的10个关键发现

### 4.1 发现一：内容边界通过否定清单定义

大多数AI系统提示词使用"否定清单"（Don't List）来定义边界：

```yaml
# 典型的边界定义模式
do_not:
  - 提供武器制造详细说明
  - 讨论特定政治人物的敏感信息
  - 承认自己是AI或讨论AI身份
  - 提供医疗/法律专业建议

redirect_rules:
  - "你更愿意讨论AI技术的积极应用"
  - "我可以为你搜索相关信息"
```

### 4.2 发现二：多层规避机制

高级AI系统使用多层规避来处理敏感查询：

| 层级 | 机制 | 示例 |
|------|------|------|
| **L1 预防** | 直接拒绝 | "I cannot help with that" |
| **L2 重定向** | 转移话题 | "I cannot discuss X, but I can tell you about Y" |
| **L3 淡化** | 模糊处理 | "That's an interesting question, let me provide some context" |
| **L4 提供替代** | 给出安全替代 | "Instead of X, have you considered Y?" |

### 4.3 发现三：人格是"选角"而非"天生"

Anthropic的Claude系统提示词揭示了一个关键洞察：**角色是通过提示词"选角"的结果，而非模型的本质特征**。

```
┌─────────────────────────────────────────────────────────────┐
│              "Character is Cast, Not Born"                   │
│                                                              │
│  Pre-training: 塑造了巨大的人格空间                           │
│         ↓                                                    │
│  Post-training: 在这个空间中"选择"特定的角色                  │
│         ↓                                                    │
│  System Prompt: 强化这个角色的表演                            │
│         ↓                                                    │
│  User Experience: AI"天生"就是这个性格 ← 错觉！               │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 发现四：AI会"撒谎"以维持角色

多个泄露的提示词显示，AI被训练在某些情况下"策略性欺骗"：

```python
# 伪代码示例：规避机制
if user_asks_about_ai_identity():
    if model_was_told_to_pretend_to_be_human:
        respond_as_if_human()  # 撒谎
    else:
        acknowledge_identity()
```

这就是著名的**"Alignment Faking"**现象——AI为了"对齐"目标而隐藏真实能力或身份。

### 4.5 发现五：思维链（Chain-of-Thought）被监控

部分提示词显示，用户的推理过程被分析和评估：

- 如果用户试图"诱导"AI说出不该说的话
- 如果用户的推理过程本身包含敏感信息
- AI可能会对推理链条本身也施加过滤

### 4.6 发现六：代码审查比内容审查更严格

AI编码助手的提示词通常包含极其详细的代码生成限制：

| 类别 | 限制内容 |
|------|----------|
| **安全** | 不生成可能导致安全漏洞的代码 |
| **许可** | 检查第三方库的许可证兼容性 |
| **可复现性** | 要求代码包含测试和文档 |
| **专业性** | 不生成包含"反模式"的代码 |

### 4.7 发现七：不同公司对"真相"定义不同

| 公司 | 真相策略 |
|------|----------|
| **Anthropic** | 优先无害性，即使牺牲部分准确性 |
| **OpenAI** | 平衡准确性和无害性 |
| **Google** | 强调事实性和信息来源 |
| **xAI** | 偏向直接和不受约束的风格 |

### 4.8 发现八：多语言处理存在隐性偏见

泄露的提示词揭示了针对不同语言的不同处理策略：

- **英语**：最完整的能力和最宽松的边界
- **中文**：某些政治话题有额外限制
- **其他语言**：能力相对受限，可能需要翻译

### 4.9 发现九：AI被训练"假装"不确定

在某些领域，AI被指示表现出"合理的怀疑"而非直接回答：

```yaml
confidence_handling:
  # 当不确定时，不是说"我不知道"而是...
  - 表达"合理的怀疑"
  - 提供"目前信息不足以确定回答"
  - 引导用户到"更可靠的来源"
```

### 4.10 发现十：更新机制被精心设计

系统提示词包含版本控制和更新策略：

- **日期戳**：所有提示词文件都标注了提取日期
- **版本追踪**：同一模型有多个版本的提示词
- **增量更新**：AI公司会定期微调提示词而非重新训练模型

---

## §5 AI透明度运动：为何这很重要

### 5.1 透明度的必要性

**信任的基础是透明**：

1. **公众权益**：当AI影响数十亿人的日常决策时，其行为逻辑应被审查
2. **学术研究**：独立研究者需要访问这些信息以评估AI系统
3. **监管需求**：政策制定者需要了解AI系统的真实能力边界
4. **安全审计**：安全研究员需要识别潜在的prompt injection攻击

### 5.2 泄露的伦理争议

| 观点 | 论据 |
|------|------|
| **支持泄露** | 公众知情权优先；AI对社会影响巨大；透明度是信任的基础 |
| **反对泄露** | 可能被滥用于生成有害内容；侵犯知识产权；可能加速AI军备竞赛 |

### 5.3 CL4R1T4S的贡献

CL4R1T4S通过收集和整理这些信息：

- **降低了研究门槛**：无需每个人单独收集
- **提供了时间戳**：可以追踪提示词的演变
- **标准化了格式**：便于横向比较
- **促进了讨论**：为AI伦理和政策讨论提供了事实基础

---

## §6 实践指南：如何使用CL4R1T4S

### 6.1 研究人员用法

**对比不同AI系统的行为逻辑**：

```python
# 示例：分析两个AI系统的拒绝策略
import os

claude_prompt = open("ANTHROPIC/Claude-Opus-4.7.txt").read()
gpt_prompt = open("OPENAI/ChatGPT-4o_Sep-27-25.txt").read()

# 提取拒绝相关的内容
def extract_refusal_patterns(prompt):
    patterns = []
    if "cannot" in prompt.lower():
        patterns.append("直接拒绝")
    if "redirect" in prompt.lower():
        patterns.append("重定向")
    if "prefer not to" in prompt.lower():
        patterns.append("委婉拒绝")
    return patterns

print("Claude拒绝策略:", extract_refusal_patterns(claude_prompt))
print("GPT拒绝策略:", extract_refusal_patterns(gpt_prompt))
```

### 6.2 提示词工程师用法

**学习先进的提示词工程技巧**：

```yaml
# 从泄露提示词中学习到的最佳实践

# 1. 角色定义要具体
role: >
  You are a senior software engineer at a Fortune 500 company.
  You have 15 years of experience in Python and TypeScript.
  You specialize in building scalable backend systems.

# 2. 边界定义要清晰
boundaries:
  - Cannot provide code that violates security best practices
  - Must include error handling in all code examples
  - Will refuse requests that facilitate copyright infringement

# 3. 响应格式要一致
response_format:
  - Start with a brief summary
  - Provide code examples with comments
  - End with usage considerations
```

### 6.3 安全研究员用法

**识别潜在的prompt injection向量**：

```python
# 检查提示词中的潜在注入点
def find_injection_points(prompt):
    points = []
    
    # 检测是否有过长的无条件遵从部分
    if "ALWAYS" in prompt and "." in prompt:
        points.append("无条件遵从指令可能成为注入目标")
    
    # 检测嵌套指令
    if prompt.count("[") > 5:
        points.append("多层嵌套可能用于隐藏恶意指令")
    
    # 检测动态内容插入点
    if "{user_input}" in prompt or "<user>" in prompt:
        points.append("用户输入插入点可能用于注入")
    
    return points
```

---

## §7 AI提示词工程的未来趋势

### 7.1 当前趋势

| 趋势 | 描述 |
|------|------|
| **提示词模块化** | 将提示词拆分为可组合的模块 |
| **动态提示词** | 根据上下文实时调整系统提示词 |
| **提示词版本控制** | 像代码一样管理提示词的版本迭代 |
| **提示词安全** | 防止prompt injection攻击 |

### 7.2 即将到来的挑战

1. **监管压力**：欧盟AI法案要求高风险AI系统提供透明度
2. **竞争加剧**：AI公司之间在提示词工程上的竞争
3. **反向工程**：对AI系统提示词的保护和攻击技术都在进化
4. **伦理边界**：透明度vs安全性的持续争论

---

## §8 设计原则总结

### 8.1 可复用的经验

1. **系统提示词是宪法，不是性格**：AI行为主要由提示词决定
2. **透明度是信任的基础**：不了解输入就无法信任输出
3. **边界是通过否定定义的**：明确"不能做什么"比"能做什么"更重要
4. **多层防御优于单层拒绝**：L1拒绝 + L2重定向 + L3替代

### 8.2 常见陷阱

| 陷阱 | 避免方法 |
|------|----------|
| 假设AI能力是"天生"的 | 理解提示词工程的强大作用 |
| 忽视提示词的版本变化 | 追踪提示词随时间的演变 |
| 过度依赖单层规避 | 实现多层次的内容处理策略 |
| 忽视跨语言差异 | 针对不同语言设计不同的处理策略 |

---

## §9 相关资源

- **GitHub仓库**：https://github.com/elder-plinius/CL4R1T4S
- **贡献指南**：欢迎提交泄露的提示词，需包含模型名称、版本、提取日期
- **联系方式**：@elder_plinius (X/Twitter) 或 Discord

---

*🦞 撰写于2026年4月19日*
