+++
date = '2026-05-19T23:58:56+08:00'
draft = false
title = 'Andrej Karpathy Skills：AI 编程行为指南'
slug = 'andrej-karpathy-skills-guide'
description = 'Karpathy 亲授的 AI 编程行为指南，通过 CLAUDE.md 文件规范 AI Coding Agent 的行为模式，让 AI 从话痨自嗨转向精准执行。'
categories = ['技术笔记']
tags = ['AI', 'Claude', 'Agent', '开发工具']
+++

# Andrej Karpathy Skills：AI 编程行为指南

---

## 🔥 为什么这个项目炸了？

2026 年，AI 编程助手已经无处不在。但 Andrej Karpathy 在一条推文里点破了一个根本性问题：

> *"AI 模型会替用户做出错误假设，然后一声不吭地按这些假设跑下去。它们不会管理自己的困惑，不会主动澄清，不会暴露矛盾，不会呈现权衡——该推回的时候也不推回。"*

Karpathy 还犀利地补充：

> *"它们极度喜欢把代码和 API 搞得过度复杂，堆砌抽象层，不清理死代码……本来 100 行能搞定的事，非要搞出 1000 行。"*

这条推文引发了 AI 编程社区的广泛共鸣。而 **andrej-karpathy-skills** 正是对这一洞察的系统性回应——一个 **CLAUDE.md 文件**，直接告诉 AI 该怎么干活。

---

## 🧠 核心理念：四项原则

这个项目只做了一件事：把 Karpathy 的观察变成一套可操作的 AI 行为准则。准则浓缩为四句话：

### 1️⃣ Think Before Coding（三思而后行）

> **不要假设。不要隐藏困惑。要呈现权衡。**

AI 常见的毛病是：用户说"加个功能"，它就默默选了一个解释然后埋头开干，结果做完了才发现理解错了。

准则要求 AI：
- **主动说出自己的假设**，不确定就问
- **遇到多种解释时，列出选项**，不要默默选一个
- **发现不清晰的地方，立即停下来问清楚**，而不是靠猜继续

### 2️⃣ Simplicity First（简单优先）

> **最小代码解决当下问题，不要 speculative。**

Karpathy 最痛恨的，就是 AI 动不动搞一套 Strategy Pattern、Abstract Factory、Plugin System——用户只是想打印个"Hello World"。

准则：
- 只实现被要求的功能，不做扩展
- 单次使用的代码不抽象
- 没有被要求的"灵活性"和"可配置性"不要加
- 200 行能搞定的，不要写到 2000 行

### 3️⃣ Surgical Changes（精准改代码）

> **只动你必须动的，清理干净你自己的烂摊子。**

AI 经常"顺便"改一堆不相关的东西——改格式、调注释、甚至重构隔壁的代码。

准则：
- 只改**直接服务于用户请求**的代码
- 不"优化"相邻的代码、注释、格式
- 你引入了未使用的 import/变量？**自己删掉**
- 之前就有的死代码？不主动删，除非被要求

### 4️⃣ Goal-Driven Execution（目标导向执行）

> **定义成功标准，循环验证直到达成。**

Karpathy 说过：*"AI 极其擅长循环执行直到满足特定目标。不要告诉它要做什么，给它成功标准，然后看它跑。"*

准则要求将模糊任务转化为可验证目标：

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

---

## 🚀 入门指南：5 分钟让你的 AI 脱胎换骨

### 方式一：Claude Code 插件（推荐 ⭐）

Claude Code 用户一行命令搞定：

```bash
# 添加市场插件
/plugin marketplace add forrestchang/andrej-karpathy-skills

# 安装插件
/plugin install andrej-karpathy-skills@karpathy-skills
```

安装后，这个指南会跨所有项目生效。

### 方式二：项目级 CLAUDE.md（新项目）

```bash
curl -o CLAUDE.md https://raw.githubusercontent.com/multica-ai/andrej-karpathy-skills/main/CLAUDE.md
```

### 方式三：追加到现有项目（已有 CLAUDE.md）

```bash
echo "" >> CLAUDE.md
curl https://raw.githubusercontent.com/multica-ai/andrej-karpathy-skills/main/CLAUDE.md >> CLAUDE.md
```

### 方式四：Cursor 用户

项目内置了 Cursor 规则 `.cursor/rules/karpathy-guidelines.mdc`，打开项目即可自动生效，无需额外配置。

---

## 📖 实战案例：AI 以前怎么错，现在怎么改

### 案例 1：隐藏假设

**用户要求：** "加个导出用户数据的功能"

**❌ AI 以前的做法：**
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

**✅ 按准则来：**
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

### 案例 2：过度工程

**用户要求：** "加个计算折扣的函数"

**❌ AI 以前的做法：**
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

**✅ 按准则来：**
```python
def calculate_discount(amount: float, percent: float) -> float:
    """计算折扣金额。percent 传入 0-100。"""
    return amount * (percent / 100)

# 用法
discount = calculate_discount(100.0, 10.0)  # 减10元
```
> 记住：只有当你真正需要多种折扣策略时，才需要引入抽象。需求还没来，不要预建。

---

## 🔍 与同类项目横向对比

| 项目 | 定位 | Stars | 特点 |
|------|------|-------|------|
| **andrej-karpathy-skills** | AI 行为准则 | 137k ⭐ | 专注解决 AI 编程中的决策质量，4 条核心原则，极简实现 |
| [anthropics/anthropic-cookbook](https://github.com/anthropics/anthropic-cookbook) | Prompt 技巧集 | 16.7k | 大量具体场景的 Prompt 模板，偏技巧而非行为 |
| [dair-ai/Prompt-Engineering-Guide](https://github.com/dair-ai/Prompt-Engineering-Guide) | Prompt 工程指南 | 64k | 覆盖范围广，偏理论，适合学习而非直接给 AI 用 |
| [microsoft/AI-App-Accelerator](https://github.com/microsoft/AI-App-Accelerator) | 企业 AI 应用 | 11k | 面向企业场景，偏架构和流程，重量级 |
| [OpenInterpreter/open-interpreter](https://github.com/OpenInterpreter/open-interpreter) | 本地 AI 编程 | 48k | 让 AI 在本地电脑上执行代码，工具类项目 |

**差异化定位：** andrej-karpathy-skills 是唯一一个**直接给 AI 看、约束 AI 行为**的项目，而非给人看的教程或 Prompt 集合。它的价值在于**在 AI 的决策环节介入**，而不是事后补救。

---

## 💡 为什么这对开发者很重要？

### 传统工作流的问题

```
用户 → AI → 代码 → Code Review → 发现问题 → 打回 → AI 修改 → 再次 Review → ...
```

AI 埋头写，开发者埋头审，循环往复，效率极低。

### 使用该准则后的工作流

```
用户 → AI 提问（Clarification） → AI 执行 → 验证通过 → PR → Review 通过 ✅
```

把沟通成本前置，消除了大量的返工。

### Karpathy 的核心洞察

> *"LLM 在满足特定目标方面极其擅长。不要告诉它要做什么，给它成功标准，然后放手让它跑。"*

这句话指出了 AI 编程助手的正确用法：**不是给命令，而是给目标。** 而这个项目，正是把这一理念落地的实践建议。

---

## 🏗️ 项目架构一览

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

其中 **EXAMPLES.md** 单独拎出来就是一部 AI 编程反范本百科全书，强烈建议通读。

---

## ⚖️ 局限性与注意事项

### ⚠️ 权衡说明

准则本身有一个重要的 tradeoff 标注：

> *"这些准则偏向谨慎而非速度。对于简单任务（改个错字、明显的一行代码），请自行判断——不是每个改动都需要完整走一遍流程。"*

### 何时使用完整流程：
- 新功能开发
- 复杂逻辑修改
- 多文件改动
- 涉及外部依赖或 API

### 何时简化：
- 打字修正（typo）
- 简单的单行代码改动
- 明显的格式化调整
- 已明确限定范围的小修改

---

## 🌟 为什么它今天冲上了趋势榜？

1. **Karpathy 效应**：Karpathy 的一句话引发了这个项目的诞生，他的背书让这个项目自带流量
2. **AI 编程的普遍痛点**：几乎每个使用 AI 编程助手的人都经历过 AI 自顾自写代码、越改越乱的痛苦
3. **零门槛落地**：一个文件，改名放到项目目录，立刻生效。不需要换工具，不需要学新东西
4. **Multica 生态加持**：母公司 [multica](https://github.com/multica-ai/multica)（开源托管 AI 代理平台，29k Stars）的背书让项目更有可信度
5. **实操性极强**：EXAMPLES.md 里的案例直接告诉 AI"你以前怎么错的，现在怎么改"，AI 可以直接学习

---

## 📚 延伸阅读与资源

- 🔗 [Andrej Karpathy 原推](https://x.com/karpathy/status/2015883857489522876) — 项目灵感来源
- 🔗 [Multica 平台](https://github.com/multica-ai/multica) — 29k Stars，开源 AI 代理管理平台
- 🔗 [Claude Code 官方文档](https://docs.anthropic.com/en/docs/claude-code)
- 🔗 [Cursor Rules 文档](https://cursor.com/docs/rules)
- 📖 EXAMPLES.md — 建议每个 AI 编程使用者通读一遍

---

## 结语

**andrej-karpathy-skills** 成功的本质，是把 Karpathy 对 AI 编程失误的深度观察，转化为一套 AI 可执行、开发者可复用的行为准则。它不需要任何新的技术发明，不需要训练模型，不需要复杂的系统——只是改变了一个 Prompt 文件的内容。

但这个改变，解决的是 AI 编程中最核心的问题：**AI 不再自顾自跑，而是先思考、先确认、先对齐目标再动手。**

如果你使用 Claude Code、Cursor、Windsurf 等 AI 编程工具，把这个 CLAUDE.md 放到你的项目里——你的开发体验会有质的飞跃。

---

*本文基于 2026-05-19 GitHub Trending 数据撰写。*