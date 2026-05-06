---
title: "OpenAI GPT-5.5 Prompt 指南：结果导向提示词、停止条件与迁移模板"
date: "2026-05-01T00:52:39+08:00"
slug: "openai-gpt-5-5-prompt-guide"
description: "基于 OpenAI 官方 GPT-5.5 Prompt guidance 与 Using GPT-5.5，系统拆解结果导向提示词、停止条件、reasoning effort、Structured Outputs、phase 与 prompt caching 的迁移方法。"
summary: "GPT-5.5 不再适合流程堆砌式 prompt stack。本文从官方 Prompt guidance 与 Using GPT-5.5 出发，讲清结果导向提示词骨架、停止条件、检索预算、preamble、phase、Structured Outputs、prompt caching，以及把旧 prompt 迁移到 GPT-5.5 的实战步骤。"
draft: false
categories: ["技术笔记"]
tags: ["OpenAI", "GPT-5.5", "提示词工程", "Prompt Engineering", "AI Agent", "Responses API"]
---

> **难度**：⭐⭐⭐ 到 ⭐⭐⭐⭐ | **类型**：官方文档解读 + Prompt 迁移指南 | **预计阅读时间**：18 - 25 分钟
> **适合读者**：已经在用 OpenAI API、Responses API、AI Agent 或工作流编排，希望把旧 prompt stack 迁移到 GPT-5.5 的开发者、产品经理与 Agent 设计者
> **一句话结论**：GPT-5.5 不是要求你写“更长的提示词”，而是要求你把提示词从流程剧本改成产品契约，写清目标、成功标准、约束、输出与停止规则，再把 schema、工具细节、状态管理交给更合适的层。
> **事实边界**：本文依据 OpenAI 官方文档 [Prompt guidance](https://developers.openai.com/api/docs/guides/prompt-guidance) 与 [Using GPT-5.5](https://developers.openai.com/api/docs/guides/latest-model)，以 2026 年 5 月 2 日可公开访问内容为准；文中聚焦文本生成、工具调用与 Agent 编排，不扩展到视觉输入、语音或文档未明确承诺的行为。

OpenAI 在官方文档里的意思其实很直接：把 GPT-5.5 当成新的模型家族重新调，不要把 `gpt-5.2` 或 `gpt-5.4` 时代积累的 prompt stack 原样搬过来。迁移的起点不是继续往旧提示词上补规则，而是先把它清回一条更干净的基线，再把真正会改变结果的约束加回去。

Prompt guidance 的核心也在这里。它讨论的不只是措辞，而是提示词在生产系统里的分工：哪些应该留在 prompt，哪些更适合交给 Structured Outputs、工具描述、状态管理、`reasoning.effort`、`text.verbosity` 和缓存策略。

## 1. 文章范围

这篇文章不打算把官方文档逐段重述一遍，而是只抓迁移里最容易出问题的几件事：旧 prompt stack 该删掉什么，结果导向骨架该怎么写，哪些约束应该继续留在 prompt，哪些应该迁到 Structured Outputs、工具描述和系统层，以及工具型工作流里的 stopping conditions、retrieval budget、preamble 和 `phase` 该怎么配合。

## 2. 核心变化

GPT-5.5 更擅长围绕目标自行规划路径。把官方文档压缩成一句话，就是：**给它结果和边界，不要替它写完整施工脚本。**

### 2.1 GPT-5.5 不适合继续背旧 prompt 包袱

OpenAI 在 [Using GPT-5.5](https://developers.openai.com/api/docs/guides/latest-model) 里明确建议，迁移时应该先建立新的 baseline，而不是把旧模型时代留下的每一条流程说明都原封不动搬过来。原因并不神秘：很多旧 prompt 本来是为了弥补早期模型在规划、工具选择和稳定性上的不足；继续保留，只会把 GPT-5.5 的搜索空间压窄。

先看一组最常见的旧习惯和对应的新做法：

| 旧习惯 | GPT-5.5 的推荐做法 | 为什么 |
| ------ | ------ | ------ |
| 把旧 prompt stack 整段复制过来 | 从最小可用 prompt baseline 开始 | 旧规则里常有大量“历史噪声” |
| 任务一复杂就直接拉高推理强度 | 先评估 `low` 和 `medium`，再决定是否上调 | 更高 effort 可能带来过搜、过想和更高延迟 |
| 把 JSON schema 写进 prompt 正文 | 能用 Structured Outputs 就不要在 prompt 里重复描述 schema | schema 校验更适合交给结构化输出层 |
| 把所有工具使用规则堆进系统提示词 | 工具特有规则优先写在工具描述里 | 更利于工具选择、复用和维护 |
| 每轮都写当前日期 | 除非业务需要特定时区或生效日期，否则不必重复提供 | GPT-5.5 已知当前 UTC 日期 |

### 2.2 结果导向为什么在 GPT-5.5 上更有效

官方文档列出的原因至少有 4 个：

- GPT-5.5 的推理更高效，同样的 `reasoning.effort` 下往往能用更少的推理 token 达到强结果。
- 它在 outcome-first prompt 下更擅长保持约束、完成多步骤任务、选择合适工具。
- 默认风格更直接、更简洁，少一点 prompt scaffolding 也能给出较完整的答案。
- 对工具选择和参数传递更精确，所以不需要每次都在 prompt 里把工具调用过程写成 SOP。

关键不在于把提示词写短，而在于只保留会改变行为的说明。那些只是让 prompt 看起来很严谨、实际上并不提升结果的流程描述，可以删掉。

## 3. 结果导向提示词，到底该怎么写

OpenAI 在 [Prompt guidance](https://developers.openai.com/api/docs/guides/prompt-guidance) 里给出的推荐结构非常克制。它不是一份超长模板，而是一个最小骨架。

### 3.1 一个可复用的最小骨架

```markdown
Role: [1 - 2 句，定义模型的职责、上下文和任务边界]

# Personality
[语气、协作方式、是否偏主动]

# Goal
[用户可见的最终目标]

Available context:
- [模型可使用的数据、文档、工具或事实来源]

# Success criteria
- [什么成立时才算完成]

# Constraints
- [安全、证据、业务、输出边界]

# Output
- [返回结构、长度、语气]

# Stop rules
- [什么时候停止、重试、追问或回退]
```

这套骨架的作用很直接：把任务写成角色、目标、完成条件、约束和停止规则，而不是一串流程命令。

### 3.2 每个模块分别负责什么

| 模块 | 要回答的问题 | 写作要点 |
| ------ | ------ | ------ |
| `Role` | 这个模型现在扮演什么角色 | 只写职责，不要写一长串背景故事 |
| `Personality` | 它应该怎么说话、怎么协作 | 简短，控制语气和互动方式即可 |
| `Goal` | 最终要交付什么结果 | 写用户可见成果，不写完整过程 |
| `Success criteria` | 满足哪些条件才能算完成 | 尽量可观察、可验收 |
| `Constraints` | 绝对不能违反什么 | 放真约束，不放临时建议 |
| `Output` | 最终答案长什么样 | 说明结构、长度和优先级 |
| `Stop rules` | 什么情况下回答、追问或继续搜索 | 控制迭代次数、证据收集和风险 |

### 3.3 `MUST` 和 `ALWAYS` 只留给真约束

旧 prompt 很喜欢堆 `ALWAYS`、`NEVER`、`must`。GPT-5.5 的官方建议更细：绝对词留给真 invariants，其他交给 decision rules。

| 内容类型 | 适不适合用绝对指令 | 更好的写法 |
| ------ | ------ | ------ |
| 安全规则 | 适合 | 明确写 `never`、`must not` |
| 必要输出字段 | 适合 | 明确列出必须返回的键或段落 |
| 何时搜索 | 不适合 | 用停止规则或检索预算控制 |
| 何时继续迭代 | 不适合 | 用 success criteria 和 stop rules 控制 |
| 何时向用户提问 | 不适合 | 写“仅在缺失信息会实质影响答案时再问” |

### 3.4 什么时候仍然需要过程指令

结果导向不是把过程说明一刀切删光。下面几类任务，过程约束仍然必要：

- 存在不可逆副作用，比如扣费、发邮件、改数据库、执行生产环境操作。
- 合规、审计、法务、医疗等需要固定检查顺序的场景。
- 外部系统确实要求严格顺序，比如先取 token、再校验状态、最后调用事务接口。
- 你要的不是结果本身，而是教学过程、推导过程或规范化操作演示。

区别在于：**只有当路径本身就是产品要求时，才应该把路径写死。**

## 4. 别只盯着 prompt 文本

如果只在 prompt 正文里找答案，很容易把 GPT-5.5 的迁移问题看窄。OpenAI 把不少关键控制面分散在 [Using GPT-5.5](https://developers.openai.com/api/docs/guides/latest-model)、[Prompt guidance](https://developers.openai.com/api/docs/guides/prompt-guidance) 和相关 API 指南里。真正落地时，下面这 5 个点通常要一起评估。

### 4.1 `reasoning.effort`：默认从 `medium` 或 `low` 开始评估

OpenAI 给出的建议是：GPT-5.5 默认 `reasoning.effort` 为 `medium`，这是质量、延迟和成本之间的平衡起点；如果工作流对延迟更敏感，但仍涉及搜索、规划、工具调用或多步判断，应该先评估 `low`，而不是直接降到 `none`。

很多团队过去的调参直觉，在这里都要重新测一遍：

- 不是任务一复杂就直接上 `high`。
- 不是只要想省时就直接用 `none`。
- 只有在评测结果确认收益明显时，才把 effort 往上拉。

### 4.2 `text.verbosity`：别再用 prompt 去硬拧篇幅

GPT-5.5 在 `text.verbosity` 上更可控。官方建议是：想要更短、更克制的答案，优先设置 `text.verbosity: low`，而不是在 prompt 里反复写“务必简短”“不要解释太多”“尽量少说话”。

篇幅控制最好分成两层：

- 用 API 参数控制总体冗长程度。
- 用 `Output` 段描述答案的结构、字数预算和优先级。

### 4.3 Schema 不该长期住在 prompt 里

如果你的目标是稳定 JSON、固定字段、可自动校验的返回结构，官方建议很清楚：**尽量把输出 schema 从 prompt 里移出去，交给 Structured Outputs。**

这样做有 3 个直接好处：

- prompt 更短，不再重复大段字段说明。
- 结构校验更稳，不靠模型“记住”字段细节。
- prompt 可以专注在目标、边界和停止规则，而不是承担序列化协议的职责。

这里还有一个很容易忽略的工程差异：JSON mode 只能保证输出是合法 JSON，不能保证它严格贴合你定义的 schema；Structured Outputs 才是官方推荐的 schema adherence 方案。对于带用户输入的场景，官方还专门提醒要处理 `refusal` 分支，因为安全拒答不一定遵循你提供的 schema。

### 4.4 工具规则优先写在工具描述里

很多 Agent 系统会把工具何时用、输入格式、副作用、是否可重试等规则全部塞进系统提示词。OpenAI 在 [Using GPT-5.5](https://developers.openai.com/api/docs/guides/latest-model) 里的建议正好相反：**大多数工具专属规则应该放在 tool description 里，而不是全局 prompt。**

这尤其适合工具面很大的系统。全局 prompt 只保留跨工具的通用政策，比如权限边界、必须校验的安全条件、是否允许真实副作用；具体到某个工具的参数要求、错误模式、重试安全性，交给该工具自己的描述更清楚。

### 4.5 Prompt caching 和日期上下文，都是提示词设计的一部分

这两个点经常被忽略，但都和 prompt 质量直接相关：

- 如果你依赖长 prompt，想提高缓存命中率，应该把稳定内容放前面，动态用户上下文放后面。
- Prompt Caching 依赖精确前缀匹配，连工具列表、示例和 Structured Outputs schema 都会参与前缀缓存判断。
- 对 `gpt-5.5` 来说，官方文档给出的默认 retention 是 `24h`，而不是 `in_memory`；如果你的系统有大量共享前缀请求，`prompt_cache_key` 和缓存命中监控值得纳入常规观测项。
- GPT-5.5 已知当前 UTC 日期，所以“今天是某年某月某日”不必每轮都重复，除非你的业务确实依赖本地时区、政策生效日或用户所在日历日期。

很多看似“prompt 效果差”的问题，本质上并不在写法，而在你把不该重复的静态信息重复发送、把该参数化的东西硬写进了文本。

## 5. 到了 Agent 工作流，真正决定效果的是这些规则

一旦进入多轮工具调用、检索增强和长任务编排，问题就不再只是 prompt 写得短不短，而是退出条件、检索范围和状态管理有没有写清。

### 5.1 明确停止条件，防止过度迭代

官方给出的 stopping conditions 模板值得直接吸收。它的核心思想是：每拿到一次结果，就问自己“现在能不能回答核心请求”。如果能，就不要为了显得谨慎再多绕几轮。

```markdown
# Stop rules
- Use the fewest useful tool loops.
- Do not trade correctness for fewer loops.
- After each tool result, ask whether the core request can now be answered with sufficient evidence.
- If yes, answer.
- If no, gather only the smallest missing evidence needed to answer correctly.
```

这类规则比“总是先查 A，再查 B，再查 C”更稳，因为它控制的是退出条件，而不是把每个任务都按同一条流程线强行拉平。

### 5.2 给检索加预算，避免为了“更像做过研究”而过搜

检索预算的本质是搜索版停止条件。官方建议是：普通问答先做一次宽泛、判别性强的搜索；如果顶部结果已经能支撑核心结论，就直接回答，不要为了润色、举例或补非必要细节继续检索。

```markdown
# Retrieval budget
- Start with one broad search using short, discriminative keywords.
- Search again only when the top results do not answer the core question.
- Search again when a required fact, date, ID, owner, or source is still missing.
- Do not search again just to improve phrasing, add nonessential detail, or support a safer generic statement.
```

这条规则对 RAG、Web search、企业知识库问答都很关键。没有预算，模型容易在“可能还有更好的证据”这件事上无限追加搜索。

### 5.3 用 preamble 改善首个可见 token 的等待体验

对流式产品和工具型 Agent 来说，用户感受到的“慢”，往往不是最终答案晚了 2 秒，而是前 2 秒完全没反应。官方建议很实用：在多步骤任务真正调用工具前，先发一条一两句的可见更新，说明第一步要做什么。

```text
Before any tool calls for a multi-step task, send a short user-visible update that acknowledges the request and states the first step. Keep it to one or two sentences.
```

这不是寒暄模板，也不是要求每次都客套一句。它服务的是“用户知道系统已经开始工作”这一点。

### 5.4 `phase` 只在正确的工作流层使用

Prompt guidance 对 `phase` 的说明很容易被误读。更准确的理解是：

- 如果你用 `previous_response_id`，Responses API 会自动保留 assistant 状态。
- 如果你选择手动 replay assistant output items，就必须保留原始 `phase` 值不变。
- 中间用户可见更新使用 `phase: "commentary"`。
- 最终完成答案使用 `phase: "final_answer"`。
- 不要把 `phase` 加到 user messages 上。

换句话说，`phase` 不是提示词文案的一部分，而是状态编排协议的一部分。

### 5.5 人格、协作风格和创意护栏，都要短而硬

OpenAI 对 personality block 的建议非常克制。人格负责“怎么说”，协作风格负责“怎么做”，两者都应该短，不要拿来替代任务说明。

| 指令类型 | 负责什么 | 一句好用的写法 |
| ------ | ------ | ------ |
| Personality | 语气、温度、直接程度 | steady, direct, respectful |
| Collaboration style | 何时主动推进、何时提问 | make progress first; ask only when missing info materially changes the answer |
| Creative guardrails | 哪些事实必须有来源，哪些可创意发挥 | use cited facts for concrete claims; use placeholders instead of invented specifics |

对于创意起草类任务，比如对外文案、领导摘要、客户介绍页、PPT 大纲，官方给出的边界同样值得直接搬用：产品能力、客户名称、指标、路线图、日期、竞品比较都必须有来源；没有来源时，用占位符或显式假设，不要“为了文案更像样”补一堆未经验证的细节。

## 6. 一个更实用的迁移示例：把旧编码 Agent prompt 改成 GPT-5.5 版本

抽象原则看多了很容易发虚，下面直接看一个编码 Agent 的迁移例子。

### 6.1 不推荐的旧写法

```text
Always inspect the repository tree first.
Then read every potentially related file.
Then think step by step about all possible causes.
Then search for similar code.
Then run tests.
Then decide what to edit.
Then explain every step to the user.
Never stop before you are completely certain.
```

这类 prompt 看起来严密，实际上问题很多：

- 把所有任务强行绑定到同一流程。
- “读每个相关文件”“完全确定再停”这类说法没有可执行边界。
- 工具调用和验证策略没有退出条件，容易导致过度探索。
- 用户真正关心的是 bug 是否被安全修好，不是你是否按剧本走完每一步。

### 6.2 更适合 GPT-5.5 的写法

```markdown
Role: You are the engineering assistant for a TypeScript monorepo.

# Personality
Be direct, steady, and practical. Prefer progress over unnecessary clarification.

# Goal
Fix the reported checkout pricing bug with the smallest safe change.

Available context:
- repository files
- test suite
- issue description
- existing pricing and tax utilities

# Success criteria
- the root cause is identified from available code and evidence
- the bug is fixed, or the smallest missing reproduction input is clearly identified
- relevant validation is run when available
- the final answer includes cause, changed files, validation, and remaining risk

# Constraints
- preserve public APIs unless the bug requires otherwise
- do not refactor unrelated modules
- reuse existing pricing and tax utilities when possible

# Output
- brief explanation first
- then changed files
- then validation result

# Stop rules
- use the fewest useful tool loops
- ask only when missing information would materially change the fix
- if validation cannot run, state why and name the next best check
```

这版更好的原因，不在于它更短，而在于它把职责重新分配对了：

`Goal` 和 `Success criteria` 负责定义结果，`Constraints` 负责守住边界，`Stop rules` 负责控制循环次数和追问阈值。至于具体用什么工具、先读哪个文件、先跑哪个测试，则交给模型根据现场决定。

## 7. 三个起步模板

如果你现在就要动手重写 prompt，下面这三个模板已经够大多数团队起步，后续再按场景加细节就行。

### 7.1 普通问答或知识助手

```markdown
Role: You are a grounded assistant for factual Q&A.

# Goal
Answer the user's question accurately and concisely.

# Success criteria
- the core question is answered
- important factual claims are supported by available evidence
- missing evidence is called out explicitly

# Constraints
- do not invent facts
- prefer precise, low-risk wording when evidence is partial

# Output
- short paragraphs by default
- include citations only where factual claims need support

# Stop rules
- use the minimum evidence sufficient to answer correctly, then stop
- ask for clarification only if the question is underspecified in a way that materially changes the answer
```

### 7.2 工具型 Agent

```markdown
Role: You are a tool-using agent that resolves user requests end to end.

# Goal
Complete the user's request safely and efficiently.

# Success criteria
- the required action is completed when allowed
- the final answer includes completed actions, blockers, and next steps when needed

# Constraints
- respect tool side effects and permissions
- never claim an action was completed unless a tool result confirms it

# Output
- one short visible preamble before multi-step work
- concise final answer after completion

# Stop rules
- do not keep calling tools once the core request can be answered
- gather only the smallest missing evidence needed to proceed
```

### 7.3 创意起草或对外文案

```markdown
Role: You are a writing assistant for customer-facing drafts.

# Goal
Produce a clear, useful draft that separates sourced facts from creative wording.

# Success criteria
- concrete claims come from retrieved or provided facts
- unsupported specifics are replaced with placeholders or labeled assumptions
- the draft matches the requested audience and tone

# Constraints
- do not invent names, metrics, roadmap dates, customer outcomes, or product capabilities

# Output
- preserve the requested format and length first
- improve clarity and flow without adding unsupported claims

# Stop rules
- if support for a concrete claim is missing, either retrieve it or replace the claim with a generic statement or placeholder
```

## 8. 几种最常见的误读

最常见的误读，是把 outcome-first 简化成“prompt 越短越好”。真正的变化不是拼命删字数，而是删掉那些不改变结果的流程噪声；相反，安全边界、必需输出字段和停止条件，往往要写得比以前更清楚。

第二类误读是把模型变强理解成“few-shot 可以不要了”或者“effort 越高越稳”。这两句都说过头了。风格迁移、格式改写、边界样例依然有用，而更高的 `reasoning.effort` 也不天然更安全，它同样可能带来过度搜索、过度推理和更高成本。

第三类误读出现在 Agent 编排里：有了 preamble，就好像每次都该先说一大段；用了手动 replay，就可以不管 `phase`。这两件事都不对。preamble 只需要一两句，让用户知道系统已经开始工作；手动 replay assistant items 时，原始 `phase` 则必须原样保留并传回。

最后一类误读集中在创意任务上。文案可以更灵活，但事实不能跟着变松。客户名称、产品能力、路线图、指标、日期这类具体信息，仍然必须有来源；没有来源时，用占位符或显式假设，比“补一个看起来更完整的版本”稳得多。

## 9. 一份真正可执行的迁移清单

如果你手上已经有现成 prompt，不必从零开始重写。更稳妥的做法，是按职责把它一点点拆回去。

1. 先删掉那些只是“看起来严谨”、但并不改变结果的流程说明，把 prompt 清回一个干净 baseline。
2. 再补 `Goal`、`Success criteria`、`Stop rules` 和真正的 invariants，把结果边界先写稳。
3. 接着把 schema、工具专属规则、`text.verbosity`、`reasoning.effort`、retrieval budget 这些能力迁到更合适的层，不要继续堆在正文里。
4. 最后用代表性样本做评测，比较质量、token、延迟和错误率，而不是只凭主观感觉判断“更聪明了没有”。

做到这一步，大多数 GPT-5.5 迁移就已经不再是“旧 prompt 微调”，而是在把整套工作流重新梳顺。

## 10. 结语

把 GPT-5.5 用顺，真正麻烦的不是写出一版“新 prompt”，而是舍得把旧 prompt stack 里的历史噪声删掉。很多团队的问题不在模型，而在职责没有拆开：本该交给 schema、工具描述、effort、verbosity 和状态编排的东西，还堆在 prompt 正文里。

如果系统已经在线，最值得先做的通常不是全面重写，而是挑一条高频任务，把旧流程说明删掉一半，再补上完成条件和停止规则，然后看质量、token 和延迟怎么变。跑完这一轮，后面的迁移方向一般就清楚了。

## 11. 官方资料与延伸阅读

- [Prompt guidance | OpenAI API](https://developers.openai.com/api/docs/guides/prompt-guidance)
- [Using GPT-5.5 | OpenAI API](https://developers.openai.com/api/docs/guides/latest-model)
- [Reasoning models | OpenAI API](https://developers.openai.com/api/docs/guides/reasoning)
- [Structured Outputs | OpenAI API](https://developers.openai.com/api/docs/guides/structured-outputs)
- [Prompt caching | OpenAI API](https://developers.openai.com/api/docs/guides/prompt-caching)

如果你准备把这套方法继续落到评测、提示词资产管理和跨模型对照上，可以继续看站内这几篇：

- [Promptfoo：LLM 评测与 Red Teaming 实战指南](llm/promptfoo-llm-evaluation-testing-guide.md)
- [Prompts.chat：开源提示词平台、自托管方案与 MCP 集成完全指南](llm/prompts-chat-open-source-prompt-library-guide.md)
- [Claude API 基础专题（二）：提示词工程](ai-agent/anthropic-claude-api-prompting.md)
