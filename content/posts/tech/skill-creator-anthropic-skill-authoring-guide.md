---
title: "Skill Creator：Anthropic 出品的 AI Agent 技能开发框架完全指南"
date: "2026-04-04T20:31:00+08:00"
slug: "skill-creator-anthropic-skill-authoring-guide"
description: "Skill Creator 是 Anthropic 官方出品的 AI Agent 技能开发框架，通过捕获意图→编写 SKILL.md→测试评估→迭代优化的闭环流程，让任何人能创建生产级的 Claude Code 技能。本文深入解析其核心理念、渐进式披露架构、评估体系和迭代工作流。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "AI Agent", "Skill", "Anthropic", "工作流自动化"]
---

# Skill Creator：Anthropic 出品的 AI Agent 技能开发框架完全指南

> 项目地址：[anthropics/skills - skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator)
>
> 定位：用于创建、改进和评估 AI Agent 技能的系统化框架
>
> 核心理念：像开发产品一样开发技能——用户研究→原型→测试→迭代→发布

## 学习目标

读完本文，你会拿到三样东西：

1. 理解 Skill Creator 的核心理念和工作流
2. 掌握 SKILL.md 的标准结构和 YAML frontmatter 规范
3. 理解渐进式披露（Progressive Disclosure）的三层加载机制
4. 学会编写高质量的技能描述（Description）以优化触发准确率
5. 掌握创建测试用例和运行评估的完整流程
6. 理解迭代优化的闭环工作流
7. 能够使用 Description Optimizer 提升技能的触发效果

---

## 一、核心理念：技能开发的产品方法论

Skill Creator 的核心洞察是：**创建技能和开发产品一样，需要用户研究、原型、测试和迭代**。

传统的技能编写是"一次性完成"——写完 SKILL.md 就结束。但 Skill Creator 认为技能应该**持续演进**，通过真实用户反馈不断优化。

### 技能开发生命周期

```
意图捕获 → 用户访谈 → 编写草稿 → 测试评估 → 用户评审 → 迭代优化 → 扩展测试 → 发布
    ↑                                                                              ↓
    ←←←←←←←←←←←←←←←←←←← 反馈循环 ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
```

**关键原则**：顺序是灵活的——用户可能只想"随便写一个"，这时候可以直接进入评估环节；如果用户已有草稿，则跳过初始编写直接进入迭代优化。

---

## 二、技能解剖：SKILL.md 标准结构

每个技能是一个文件夹，至少包含 SKILL.md 文件：

```
skill-name/
├── SKILL.md (必需)
│   ├── YAML frontmatter (name, description 必须)
│   └── Markdown 指令内容
└── Bundled Resources (可选)
    ├── scripts/      # 可执行脚本
    ├── references/   # 按需加载的参考文档
    └── assets/       # 输出文件（模板、图标、字体）
```

### YAML Frontmatter 必需字段

```yaml
---
name: skill-creator                    # 技能标识符（小写+连字符）
description: Create new skills, modify and improve existing skills,
            and measure skill performance. Use when users want to
            create a skill from scratch, edit or optimize an existing
            skill, run evals to test a skill...
---
```

**Description 是触发机制的核心**——它决定何时激活该技能。好的描述应该：
1. 说明技能**做什么**
2. 明确**何时使用**（包括具体场景和模糊场景）
3. 使用"pushy"语言——稍微积极主动，避免触发不足

### Optional Fields

```yaml
---
name: my-skill
description: ...
compatibility:  # 可选，很少需要
  -Requires: git, node 18+
---
```

---

## 三、渐进式披露：三层加载架构

技能使用三层加载系统，避免上下文溢出：

| 层级 | 内容 | 加载时机 | 理想规模 |
|------|------|----------|----------|
| **元数据** | name + description | 始终在上下文 | ~100 词 |
| **SKILL.md 正文** | 指令主体 | 技能触发时 | <500 行 |
| **Bundled Resources** | 脚本/参考资料 | 按需加载 | 无限制 |

### 为什么这样设计？

LLM 的上下文窗口是有限的。全部加载会导致：
- 成本激增（Token 费用）
- 性能下降（处理更多文本）
- 无关信息干扰

渐进式披露确保：**最相关的信息始终可用，详细资源按需获取**。

### 实践建议

1. SKILL.md 控制在 500 行以内
2. 大于 300 行的参考文件添加目录
3. 从 SKILL.md 清晰引用资源文件并说明何时读取
4. 领域多态时，按变体组织参考文档：

```
cloud-deploy/
├── SKILL.md (工作流 + 选择逻辑)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```

---

## 四、编写技能：六步流程

### 第一步：捕获意图（Capture Intent）

开始编写前，理解用户真正想要什么：

**必问问题**：
1. 这个技能让 Claude 能做什么？
2. 何时触发？（用户说什么/什么场景）
3. 期望的输出格式是什么？
4. 需要测试用例验证技能是否有效？

如果对话中已有现成工作流，直接提取：工具使用、步骤顺序、用户纠错、输入/输出格式。

### 第二步：访谈与研究（Interview and Research）

主动询问边界情况：
- 输入/输出格式的具体要求
- 示例文件
- 成功标准
- 依赖项

检查可用的 MCP（Model Context Protocol）——如果有相关文档搜索、类似技能查找、实践建议查询功能，通过子代理并行研究。

### 第三步：编写 SKILL.md（Write the SKILL.md）

基于访谈结果填充组件：

**Name 命名规范**：
- 小写字母
- 可用连字符
- 不超过 64 字符

**Description 撰写技巧**：
- 说明技能**做什么** AND **何时使用**
- "Pushy" 原则——描述稍微积极主动，避免触发不足

**不好**：`How to build a simple fast dashboard to display internal Anthropic data.`

**好**：`How to build a simple fast dashboard to display internal Anthropic data. Make sure to use this skill whenever the user mentions dashboards, data visualization, internal metrics, or wants to display any kind of company data, even if they don't explicitly ask for a 'dashboard'.`

### 第四步：创建测试用例（Test Cases）

编写 2-3 个真实测试提示——用户实际会说的话：

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": []
    }
  ]
}
```

保存到 `evals/evals.json`。先只写提示，不写断言（assertions）——断言在下一步添加。

### 第五步：运行与评估（Running and Evaluating）

**关键原则**：同一次并行运行 with-skill 和 baseline 版本，不要先跑 with-skill 再跑 baseline。

**创建工作空间**：

```
<skill-name>-workspace/
├── iteration-1/
│   ├── eval-0-with_skill/outputs/
│   ├── eval-0-without_skill/outputs/  (或 old_skill/ 如果是改进)
│   ├── eval-1-with_skill/outputs/
│   └── ...
└── iteration-2/
    └── ...
```

**Step 1：启动所有运行（同一轮次）**

对于每个测试用例，同时启动两个子代理：
- **With-skill 运行**：包含技能路径
- **Baseline 运行**：无技能（新技能）或旧版本（改进技能）

**Step 2：运行期间起草断言**

不要干等——在运行进行时起草定量断言。好的断言：
- 客观可验证
- 描述性名称——在 benchmark viewer 中清晰可读
- 主观性技能（写作风格、设计质量）更适合定性评估

**Step 3：捕获计时数据**

每次子代理完成时，立即保存 `timing.json`：

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

**Step 4：评分、聚合、启动 viewer**

```bash
python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
```

生成 `benchmark.json` 和 `benchmark.md`，然后启动评估 viewer：

```bash
nohup python <skill-creator-path>/eval-viewer/generate_review.py \
  <workspace>/iteration-N \
  --skill-name "my-skill" \
  --benchmark <workspace>/iteration-N/benchmark.json \
  > /dev/null 2>&1 & VIEWER_PID=$!
```

**Step 5：读取反馈**

```json
{
  "reviews": [
    {"run_id": "eval-0-with_skill", "feedback": "the chart is missing axis labels", "timestamp": "..."},
    {"run_id": "eval-1-with_skill", "feedback": "", "timestamp": "..."}
  ],
  "status": "complete"
}
```

空反馈表示用户认为可以。聚焦用户有具体抱怨的测试用例。

### 第六步：迭代改进（Improving the Skill）

**改进思维**：

1. **从反馈泛化**：技能要能被使用百万次，不能只针对这几个测试用例泛化。避免过度拟合的修改或过于严格的 MUST，而是尝试不同隐喻或推荐不同模式。

2. **保持提示精简**：移除没有贡献的内容。阅读转录——如果技能让模型浪费时间做无产出的事，删除那部分指令。

3. **解释原因**：尝试解释每个要求的**原因**。今天的 LLM 很聪明，有良好的心智理论，给它好的 harness 它能超越死板指令真正发挥作用。

4. **寻找测试用例间的重复工作**：如果所有测试用例的子代理都独立写了相似的辅助脚本或采用相同的多步骤方法，这是强烈信号——技能应该 bundle 那个脚本。

---

## 五、描述优化：提升触发准确率

Description 字段是主要触发机制。创建或改进技能后，提供优化描述以提升触发准确率。

### 触发机制原理

Skills 出现在 Claude 的 `available_skills` 列表中，Claude 根据 description 决定是否咨询技能。关键点：

- Claude 只对**无法轻易处理的任务**咨询技能
- 简单的一次性查询（如"读取这个 PDF"）可能不会触发技能，即使描述匹配
- 复杂的、多步骤的或专业化的查询，当描述匹配时会可靠触发

### 优化流程

**Step 1：生成触发评估查询**

创建 20 个评估查询——should-trigger 和 should-not-trigger 的混合：

```json
[
  {"query": "the user prompt", "should_trigger": true},
  {"query": "another prompt", "should_trigger": false}
]
```

查询要求：
- **Should-trigger 查询（8-10 个）**：覆盖不同表述——正式/非正式；包含文件路径、个人上下文、公司名称；用户可能没有明确命名技能或文件类型但明显需要它
- **Should-not-trigger 查询（8-10 个）**：最有价值的是 near-misses——共享关键词/概念但实际需要不同；相邻领域；歧义措辞

**Step 2：用户评审**

使用 HTML 模板呈现评估集供用户评审、编辑查询、切换 should-trigger、添加/删除条目。

**Step 3：运行优化循环**

```bash
python -m scripts.run_loop \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path <path-to-skill> \
  --model <model-id> \
  --max-iterations 5 \
  --verbose
```

自动处理完整优化循环：分割 60% 训练/40% 留出测试，评估当前描述，调用 Claude 提出改进，迭代最多 5 次。

**Step 4：应用结果**

从 JSON 输出取 `best_description`，更新技能的 SKILL.md frontmatter。

---

## 六、子代理系统：专业分工

Skill Creator 使用多个专业子代理：

| 子代理 | 文件 | 职责 |
|--------|------|------|
| **Grader** | `agents/grader.md` | 评估每个断言 |
| **Analyzer** | `agents/analyzer.md` | 分析 benchmark 数据，发现模式 |
| **Comparator** | `agents/comparator.md` | 盲对比两个版本 |
| **Reviewer** | `eval-viewer/generate_review.py` | 生成 HTML 评估界面 |

### Grader 工作流

```python
# 对于每个断言，运行 grader 子代理
# 读取 agents/grader.md
# 评估输出保存到 grading.json
{
  "assertions": [
    {
      "text": "assertion description",
      "passed": true,
      "evidence": "what was found"
    }
  ]
}
```

### Analyzer 发现模式

- 始终通过的断言（无区分力）
- 高方差评估（可能不稳定）
- 时间/Token 权衡

---

## 七、技能解剖示例：目录结构

skill-creator 本身的结构：

```
skills/skill-creator/
├── agents/                    # 子代理定义
│   ├── grader.md
│   ├── analyzer.md
│   └── comparator.md
├── assets/
│   └── eval_review.html      # 评估审查模板
├── eval-viewer/
│   └── generate_review.py    # 评估 viewer 生成器
├── references/
│   └── schemas.md            # 数据结构 schema
├── scripts/
│   ├── aggregate_benchmark.py
│   ├── run_loop.py           # 描述优化循环
│   └── package_skill.py
└── SKILL.md                  # 主技能文件
```

---

## 八、快速上手

### 1. 克隆技能仓库

```bash
git clone https://github.com/anthropics/skills.git
cd skills/skills/skill-creator
```

### 2. 启动 Skill Creator

在 Claude Code 中，直接启动：

```
/manifest https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md
```

或者如果 skill 已安装：

```
/skill skill-creator
```

### 3. 开始创建

告诉 Claude 你想创建什么技能，例如："I want to make a skill for writing documentation"。

Claude 会：
1. 澄清意图和边界情况
2. 编写 SKILL.md 草稿
3. 创建测试用例
4. 运行评估
5. 根据反馈迭代

---

## 九、实践建议

### 描述撰写

- **包含具体场景**：不仅说"做 X"，还说"当你需要做 X 并且 Y 场景时"
- **Pushy 但不夸张**："Make sure to use this skill whenever..." 而不是 "This skill might be useful when..."
- **包含边界情况**：什么情况下**不应该**触发

### 测试用例

- **真实提示**：用户实际会说的话，不是"extract text from PDF"而是"ok so my boss just sent me this xlsx file (its in my downloads, called something like 'Q4 sales final FINAL v2.xlsx') and she wants me to add a column that shows the profit margin as a percentage"
- **Near-misses**：should-not-trigger 的查询要真正测试边界，不是明显无关的内容
- **适量规模**：2-3 个测试用例快速迭代，扩展到更大规模验证泛化

### 迭代优化

- **读转录，不只看输出**：有时候技能让模型浪费时间的方式不明显
- **bundle 重复脚本**：如果所有测试用例都写了相似的辅助脚本，提取到 `scripts/`
- **解释为什么**：不只是 ALWAYS/NEVER，用理论解释原因

---

## 十、常见问题

**Q：技能总是触发不足怎么办？**
A：使用 Description Optimizer 生成更好的描述。确保描述是"pushy"的，包含具体使用场景。

**Q：测试用例应该有多复杂？**
A：足够复杂让 Claude 真正需要技能帮助。简单的"read this file"不会触发技能因为 Claude 直接能做。

**Q：断言应该多精确？**
A：客观可验证的优先。主观评估（如"写作风格好"）留给用户评审，不要强加断言。

**Q：需要多少测试用例？**
A：开始 2-3 个快速迭代，满意后扩展到更大规模验证泛化。

**Q：技能太复杂了怎么办？**
A：考虑分解为多个专注的小技能，通过主技能调度子技能。

---

## 十一、总结

Skill Creator 的做法很直接：**像开发产品一样开发 AI Agent 技能**——意图捕获、渐进式披露、量化评估、迭代优化，一条线走完，任何人都能创建生产级的 Claude Code 技能。

核心要点：

1. **Description 是触发机制**——精心撰写，包含具体场景
2. **渐进式披露**——元数据始终加载，正文按需，Bundled Resources 无限制
3. **测试驱动**——创建真实测试用例，并行运行 with-skill 和 baseline
4. **迭代优化**——基于用户反馈持续改进，不要一次性完成
5. **量化评估**——客观断言 + 定性评审结合

按这套流程走下来，技能开发就从"写完就扔"变成了可度量、可迭代的工程活。

---

**相关链接：**
- GitHub：https://github.com/anthropics/skills
- Skill Creator 路径：https://github.com/anthropics/skills/tree/main/skills/skill-creator
- 官方文档：https://docs.anthropic.com/en/docs/claude-code/skills
