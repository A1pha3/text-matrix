+++
date = '2026-05-19T23:58:56+08:00'
draft = false
title = 'Andrej Karpathy Skills：AI 编程行为指南'
slug = 'andrej-karpathy-skills'
description = 'Karpathy 亲授的 AI 编程行为指南，通过 CLAUDE.md 文件规范 AI Coding Agent 的行为模式，让 AI 从话痨自嗨转向精准执行。'
categories = ['技术笔记']
tags = ['AI', 'Claude', 'Agent', '开发工具']
+++

andrej-karpathy-skills 是一个把 Andrej Karpathy 推文洞察整理为 `CLAUDE.md` 行为准则的开源项目，用来约束 AI Coding Agent 在编码前的决策环节。它的核心做法是把"先思考、先确认、先对齐目标"写成 AI 可读的硬规则，让 AI 在动手前主动暴露假设、列出权衡、给出可验证的成功标准。本文先拆解这套准则的四项原则与生效机制，再给出安装方式、实战案例、横向对比和采用建议。

## 这篇文章会带你看到什么

| 模块 | 内容 | 适用读者 |
|------|------|----------|
| 背景与判断 | Karpathy 推文的核心问题与项目回应 | 想了解项目来路的读者 |
| 准则生效机制 | `CLAUDE.md` 如何被 AI 读取并约束推理路径 | 想理解机制底座的读者 |
| 四项原则 | Think Before Coding、Simplicity First、Surgical Changes、Goal-Driven Execution | 想理解准则设计的读者 |
| 安装与集成 | Claude Code 插件、`CLAUDE.md`、Cursor 规则四种方式 | 准备落地的开发者 |
| 实战案例 | 隐藏假设与过度工程两个反范本，含任务流变化 | 想看具体改写的读者 |
| 横向对比 | 与 anthropic-cookbook 等 5 个项目的定位差异 | 选型决策者 |
| 采用建议 | 何时用完整流程、何时简化、如何与现有工作流整合 | 已安装或准备安装的团队 |

## Karpathy 的判断：AI 编程的根问题在决策环节

2026 年，AI 编程助手已经无处不在。Andrej Karpathy 在一条推文里点破了根本问题：

> *"AI 模型会替用户做出错误假设，然后一声不吭地按这些假设跑下去。它们不会管理自己的困惑，不会主动澄清，不会暴露矛盾，不会呈现权衡——该推回的时候也不推回。"*

他同时指出代码层面的典型病症：

> *"它们极度喜欢把代码和 API 搞得过度复杂，堆砌抽象层，不清理死代码……本来 100 行能搞定的事，非要搞出 1000 行。"*

这两段话指向同一个机制：AI 在编码前的决策环节缺约束。它默认把模糊需求当成明确指令，把单次任务当成可复用框架，把"能跑"当成"达成目标"。andrej-karpathy-skills 的做法是在这个环节插入一层硬规则，让 AI 在写第一行代码前先完成假设暴露、方案列举和成功标准定义。

## 准则如何生效：`CLAUDE.md` 的机制

`CLAUDE.md` 是 Claude Code 在每次会话启动时自动读取的项目级指令文件，内容会被注入到模型上下文里。Cursor 通过 `.cursor/rules/*.mdc` 实现等价机制。这两类文件的作用对象都是 AI 模型本身，约束的是模型在生成代码前的推理路径。

andrej-karpathy-skills 在这套机制上做了一个明确选择：只写 AI 必须遵守的行为边界，不写 Prompt 模板，也不写使用教程。开发者把文件放进项目，AI 在每次会话里都会读到这些规则，并在执行任务时主动对齐。

## 四项原则：每条都在堵一个具体漏洞

### Think Before Coding：堵"默默假设"

> **不要假设。不要隐藏困惑。要呈现权衡。**

AI 的常见故障是：用户说"加个功能"，它默默选了一个解释然后埋头开干，做完了才发现理解错了。这条原则要求 AI 在动手前完成三件事：

- **主动说出假设**，不确定就问
- **遇到多种解释时列出选项**，让用户选
- **发现不清晰的地方立即停下来问清楚**，不靠猜测推进

这条原则的代价是多一轮对话，收益是消除整段返工。

### Simplicity First：堵"过度抽象"

> **最小代码解决当下问题，不要 speculative。**

Karpathy 最痛恨的故障是 AI 动不动搞一套 Strategy Pattern、Abstract Factory、Plugin System——用户只是想打印个 "Hello World"。这条原则划了几条硬边界：

- 只实现被要求的功能，不做扩展
- 单次使用的代码不抽象
- 没被要求的"灵活性"和"可配置性"不加
- 200 行能搞定的，不写到 2000 行

抽象的代价是阅读成本和修改成本。在需求还没出现时预建抽象，会让后续真正的需求被既有抽象绑架。

### Surgical Changes：堵"顺手改"

> **只动你必须动的，清理干净你自己的烂摊子。**

AI 经常"顺便"改一堆不相关的东西——改格式、调注释、甚至重构隔壁代码。这条原则要求：

- 只改**直接服务于用户请求**的代码
- 不"优化"相邻的代码、注释、格式
- 自己引入的未使用 import/变量，**自己删掉**
- 之前就有的死代码，不主动删，除非被要求

这条原则保护的是代码审查的可追溯性。一次提交只解决一个问题，review 才能聚焦。

### Goal-Driven Execution：堵"能跑就算完成"

> **定义成功标准，循环验证直到达成。**

Karpathy 说过：*"AI 极其擅长循环执行直到满足特定目标。不要告诉它要做什么，给它成功标准，然后看它跑。"*

这条原则要求把模糊任务转化为可验证目标：

```
❌ "添加验证功能"
✅ "为非法输入写测试用例 → 运行测试确认失败 → 实现验证 → 确认测试通过"
```

多步骤任务必须列出计划：

```
1. [步骤] → 验证: [检查点]
2. [步骤] → 验证: [检查点]
3. [步骤] → 验证: [检查点]
```

这条原则的底层逻辑是：AI 擅长在明确目标下循环优化，不擅长在模糊目标下自行判断"够了"。把"够了"写成可运行的检查，AI 才能稳定收敛。

## 安装与集成：四种方式

### 方式一：Claude Code 插件（推荐）

Claude Code 用户通过插件市场安装：

```bash
# 添加市场插件
/plugin marketplace add forrestchang/andrej-karpathy-skills

# 安装插件
/plugin install andrej-karpathy-skills@karpathy-skills
```

安装后，这个指南会跨所有项目生效。

### 方式二：项目级 `CLAUDE.md`（新项目）

```bash
curl -o CLAUDE.md https://raw.githubusercontent.com/multica-ai/andrej-karpathy-skills/main/CLAUDE.md
```

### 方式三：追加到现有项目（已有 `CLAUDE.md`）

```bash
echo "" >> CLAUDE.md
curl https://raw.githubusercontent.com/multica-ai/andrej-karpathy-skills/main/CLAUDE.md >> CLAUDE.md
```

### 方式四：Cursor 用户

项目内置了 Cursor 规则 `.cursor/rules/karpathy-guidelines.mdc`，打开项目即可自动生效，无需额外配置。

## 实战案例：任务如何流过准则

### 案例 1：隐藏假设被强制暴露

**用户要求：** "加个导出用户数据的功能"

**AI 以前的做法：**

```python
def export_users(format='json'):
    users = User.query.all()
    if format == 'json':
        with open('users.json', 'w') as f:
            json.dump([u.to_dict() for u in users], f)
    elif format == 'csv':
        with open('users.csv', 'w') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'email', 'name'])
            writer.writeheader()
            writer.writerows([u.to_dict() for u in users])
    return f"Exported {len(users)} users"
```

**问题：** 假设了全量导出、文件路径、导出字段——全是坑。

**按准则后的做法：**

```
在开始实现之前需要澄清：

1. **范围**：导出所有用户还是筛选后子集？（涉及隐私）
2. **格式**：你说"导出"是指：
   - 浏览器下载文件？
   - 后台任务发邮件通知？
   - API 返回数据？
3. **字段**：包含哪些用户字段？（部分字段可能敏感）
4. **数据量**：通常多少用户？（影响实现方式）

最简单的方案：添加返回分页 JSON 的 API 端点。
如果需要文件导出，需要更多信息。

您倾向哪种方案？
```

任务流变化：用户提需求 → AI 列假设和选项 → 用户确认范围 → AI 给最简方案 → 用户拍板 → AI 实现。整段返工被前置的一轮对话消除。对比旧流程"用户 → AI → 代码 → Code Review → 发现问题 → 打回 → AI 修改 → 再次 Review"，沟通成本前置到了编码之前。

### 案例 2：过度工程被砍回最小实现

**用户要求：** "加个计算折扣的函数"

**AI 以前的做法：**

```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import Protocol, Union
from dataclasses import dataclass

class DiscountStrategy(ABC):
    @abstractmethod
    def calculate(self, amount: float) -> float: pass

class PercentageDiscount(DiscountStrategy):
    def __init__(self, percentage: float): self.percentage = percentage
    def calculate(self, amount: float) -> float:
        return amount * (self.percentage / 100)

class FixedDiscount(DiscountStrategy):
    def __init__(self, fixed_amount: float): self.fixed_amount = fixed_amount
    def calculate(self, amount: float) -> float:
        return min(self.fixed_amount, amount)

@dataclass
class DiscountConfig:
    strategy: DiscountStrategy
    min_purchase: float = 0.0
    max_discount: float = float('inf')

class DiscountCalculator:
    def __init__(self, config: DiscountConfig): self.config = config
    def apply_discount(self, amount: float) -> float:
        if amount < self.config.min_purchase: return 0
        discount = self.config.strategy.calculate(amount)
        return min(discount, self.config.max_discount)
```

**按准则后的做法：**

```python
def calculate_discount(amount: float, percent: float) -> float:
    """计算折扣金额。percent 传入 0-100。"""
    return amount * (percent / 100)

# 用法
discount = calculate_discount(100.0, 10.0)  # 减 10 元
```

> 只有当真正需要多种折扣策略时，才需要引入抽象。需求还没来，不要预建。

## 横向对比：定位差异

| 项目 | 定位 | Stars（截至 2026-05-19） | 特点 |
|------|------|-------|------|
| **andrej-karpathy-skills** | AI 行为准则 | 137k ⭐ | 专注解决 AI 编程中的决策质量，4 条核心原则，极简实现 |
| [anthropics/anthropic-cookbook](https://github.com/anthropics/anthropic-cookbook) | Prompt 技巧集 | 16.7k | 大量具体场景的 Prompt 模板，侧重技巧，不约束 AI 行为 |
| [dair-ai/Prompt-Engineering-Guide](https://github.com/dair-ai/Prompt-Engineering-Guide) | Prompt 工程指南 | 64k | 覆盖范围广，偏理论，适合学习，不直接给 AI 用 |
| [microsoft/AI-App-Accelerator](https://github.com/microsoft/AI-App-Accelerator) | 企业 AI 应用 | 11k | 面向企业场景，偏架构和流程，重量级 |
| [OpenInterpreter/open-interpreter](https://github.com/OpenInterpreter/open-interpreter) | 本地 AI 编程 | 48k | 让 AI 在本地电脑上执行代码，工具类项目 |

andrej-karpathy-skills 的差异化定位在于：它直接给 AI 看、约束 AI 行为，在 AI 的决策环节介入。其他项目要么面向人（教程、Prompt 集合），要么面向工具链（本地执行、企业架构），都没有在模型生成代码前的推理路径上设约束。

## 项目架构

```
andrej-karpathy-skills/
├── CLAUDE.md                    # 核心指南文件（MIT License）
├── README.md                    # 英文说明
├── README.zh.md                  # 中文说明
├── CURSOR.md                    # Cursor 配置说明
├── EXAMPLES.md                  # 大量实战案例 ⭐（学习价值极高）
├── .cursor/rules/
│   └── karpathy-guidelines.mdc  # Cursor 项目级规则
├── .claude-plugin/              # Claude Code 插件配置
└── skills/
    └── karpathy-guidelines/     # 技能包
```

`EXAMPLES.md` 单独拎出来就是一部 AI 编程反范本百科全书，建议通读。

## 局限与边界

准则本身标注了一个重要 tradeoff：

> *"这些准则偏向谨慎而非速度。对于简单任务（改个错字、明显的一行代码），请自行判断——不是每个改动都需要完整走一遍流程。"*

何时使用完整流程：

- 新功能开发
- 复杂逻辑修改
- 多文件改动
- 涉及外部依赖或 API

何时简化：

- 打字修正（typo）
- 简单的单行代码改动
- 明显的格式化调整
- 已明确限定范围的小修改

## 采用建议

**给个人开发者**：如果你日常用 Claude Code 或 Cursor，优先用方式一的插件路径，让准则跨项目生效。第一次试用时挑一个新功能开发任务，观察 AI 是否在动手前主动列假设和选项。如果 AI 仍然埋头就写，检查 `CLAUDE.md` 是否被正确加载。

**给团队**：把 `CLAUDE.md` 纳入仓库，让所有成员的 AI 会话读到同一份规则。在 Code Review 阶段，把"是否暴露假设""是否做最小改动""是否给可验证标准"作为 review 检查项，与准则形成闭环。

**给已有 `CLAUDE.md` 的项目**：用方式三追加，避免覆盖既有规则。追加后通读一遍合并后的文件，确认四项原则与既有规则没有冲突。

**何时绕开准则**：typo 修正、单行改动、明确限定范围的小修改，可以直接让 AI 动手，跳过完整流程。准则本身允许这种判断。

## 延伸阅读与资源

- [Andrej Karpathy 原推](https://x.com/karpathy/status/2015883857489522876) — 项目灵感来源
- [Multica 平台](https://github.com/multica-ai/multica) — 29k Stars（截至 2026-05-19），开源 AI 代理管理平台
- [Claude Code 官方文档](https://docs.anthropic.com/en/docs/claude-code)
- [Cursor Rules 文档](https://cursor.com/docs/rules)
- `EXAMPLES.md` — 建议每个 AI 编程使用者通读一遍

---

*本文基于 2026-05-19 GitHub Trending 数据撰写，Stars 数据为该日快照，后续可能有变化。*
