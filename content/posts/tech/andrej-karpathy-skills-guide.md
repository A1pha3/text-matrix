+++
github_repo = "multica-ai/andrej-karpathy-skills"
source_key = "gh:multica-ai/andrej-karpathy-skills"
date = '2026-05-19T23:58:56+08:00'
lastmod = '2026-09-21T12:00:00+08:00'
draft = false
title = 'Andrej Karpathy Skills：AI 编程行为指南'
slug = 'andrej-karpathy-skills'
description = '根据 Karpathy 对 LLM 编程通病的观察整理的一份 CLAUDE.md 行为准则：让 AI 在动手前暴露假设、保持最小改动、按可验证的目标收尾。'
categories = ['技术笔记']
tags = ['Claude', 'AI Agent', '开发工具']
+++

## 快速信息卡

| 指标 | 数值 |
|------|------|
| Stars | 214,402（截至 2026-09-21） |
| Forks | 21,673 |
| 许可证 | MIT（README 与插件配置中声明，仓库无独立 LICENSE 文件） |
| 作者 | forrestchang（Jiayuan，[X @jiayuan_jy](https://x.com/jiayuan_jy)），仓库现由 multica-ai 组织维护 |
| 语言 | 文档（Markdown） |
| 仓库 | [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) |

## 学习目标

读完本文，你应该能够：

1. **理解 AI 编程的根问题**：明白为什么 AI 在决策环节缺约束，以及这会导致什么故障
2. **掌握四项原则**：Think Before Coding、Simplicity First、Surgical Changes、Goal-Driven Execution 各自堵什么漏洞
3. **知道如何安装**：Claude Code 插件、项目级 CLAUDE.md、Cursor 规则，哪种适合你
4. **识别过度工程**：能从 AI 生成的代码中识别隐藏假设、过度抽象、顺手改等故障
5. **评估适用性**：判断你的团队是否应该采用这套准则，以及如何与现有工作流整合

andrej-karpathy-skills 是一个把 Andrej Karpathy 推文洞察整理为 `CLAUDE.md` 行为准则的开源项目，用来约束 AI Coding Agent 在编码前的决策环节。它的做法是把"先思考、先确认、先对齐目标"写成 AI 可读的硬规则，让 AI 在动手前主动暴露假设、列出权衡、给出可验证的成功标准。本文先拆解这套准则的四项原则与生效机制，再给出安装方式、实战案例、横向对比和采用建议。

## 这篇文章会带你看到什么

| 模块 | 内容 | 适用读者 |
|------|------|----------|
| 背景与判断 | Karpathy 推文的核心问题与项目回应 | 想了解项目来路的读者 |
| 准则生效机制 | `CLAUDE.md` 如何被 AI 读取并约束推理路径 | 想理解机制底座的读者 |
| 四项原则 | Think Before Coding、Simplicity First、Surgical Changes、Goal-Driven Execution | 想理解准则设计的读者 |
| 安装与集成 | Claude Code 插件、`CLAUDE.md`（新建/追加）、Cursor 规则 | 准备落地的开发者 |
| 实战案例 | 隐藏假设与过度工程两个反范本，含任务流变化 | 想看具体改写的读者 |
| 横向对比 | 与 claude-cookbooks 等 5 个项目的定位差异 | 选型决策者 |
| 采用建议 | 何时用完整流程、何时简化、如何与现有工作流整合 | 已安装或准备安装的团队 |

## Karpathy 的判断：AI 编程的根问题在决策环节

2026 年，AI 编程助手已经无处不在。Andrej Karpathy 在[一条推文](https://x.com/karpathy/status/2015883857489522876)里点破了根本问题：

> *"AI 模型会替用户做出错误假设，然后一声不吭地按这些假设跑下去。它们不会管理自己的困惑，不会主动澄清，不会暴露矛盾，不会呈现权衡——该推回的时候也不推回。"*

他同时指出代码层面的两组典型病症。一是过度复杂：

> *"它们极度喜欢把代码和 API 搞得过度复杂，堆砌抽象层，不清理死代码……本来 100 行能搞定的事，非要搞出 1000 行。"*

二是顺手改：

> *"它们仍会时不时改掉或删掉自己没有充分理解的注释和代码，即使这些改动与任务本身毫无关系。"*

这三段话指向同一个机制：AI 在编码前的决策环节缺约束。它默认把模糊需求当成明确指令，把单次任务当成可复用框架，把"能跑"当成"达成目标"。andrej-karpathy-skills 的做法是在这个环节插入一层硬规则，让 AI 在写第一行代码前先完成假设暴露、方案列举和成功标准定义——三段观察分别对应了下面四项原则中的三组漏洞。

## 准则如何生效：`CLAUDE.md` 的机制

`CLAUDE.md` 是 Claude Code 在每次会话启动时自动读取的项目级指令文件，内容会被注入到模型上下文里。Cursor 通过 `.cursor/rules/*.mdc` 实现等价机制。这两类文件的作用对象都是 AI 模型本身，约束的是模型在生成代码前的推理路径。

andrej-karpathy-skills 在这套机制上做了一个明确选择：只写 AI 必须遵守的行为边界，不写 Prompt 模板，也不写使用教程。开发者把文件放进项目，AI 在每次会话里都会读到这些规则，并在执行任务时主动对齐。

同一份内容在仓库里维护着三种形态：`CLAUDE.md`（Claude Code 用）、`.cursor/rules/karpathy-guidelines.mdc`（Cursor 用）、`skills/karpathy-guidelines/SKILL.md`（Agent Skills 用）。仓库要求贡献者在修改四项原则时同步更新这三处，改一处漏一处会被视为破坏一致性。

## 四项原则：每条都在堵一个具体漏洞

### Think Before Coding：堵"默默假设"

> **不要假设。不要隐藏困惑。要呈现权衡。**

AI 的常见故障是：用户说"加个功能"，它默默选了一个解释然后埋头开干，做完了才发现理解错了。这条原则要求 AI 在动手前完成四件事：

- **明确说出假设**，不确定就问，不靠猜
- **存在多种解释时全部摆出来**，让用户选，不默默挑一个
- **有更简单的方案就说出来**，该推回时就推回
- **感到困惑立即停下**，说出哪里不清楚，然后提问

这条原则的代价是多一轮对话，收益是消除整段返工。

### Simplicity First：堵"过度抽象"

> **用能解决问题的最少代码。不做任何投机设计。**

Karpathy 最痛恨的故障是 AI 动不动搞一套 Strategy Pattern、Abstract Factory、Plugin System——用户只是想打印个 "Hello World"。这条原则划了几条硬边界：

- 不做超出要求的功能
- 单次使用的代码不抽象
- 没被要求的"灵活性"和"可配置性"不加
- 不为不可能发生的场景写错误处理
- 写了 200 行而 50 行就够，推倒重写

准则还配了一个自检问题：**"资深工程师会不会说这段代码过度复杂？"会，就简化。**

抽象的代价是阅读成本和修改成本。在需求还没出现时预建抽象，会让后续真正的需求被既有抽象绑架。

### Surgical Changes：堵"顺手改"

> **只动你必须动的。只清理你自己制造的烂摊子。**

编辑既有代码时：

- 不"顺手改进"相邻的代码、注释、格式
- 不重构没坏的东西
- 遵循既有风格，哪怕你有自己的偏好
- 发现与任务无关的死代码，指出来，但不要删

自己的改动产生孤儿时：

- 自己的改动导致没人用的 import/变量/函数，自己删掉
- 之前就存在的死代码，除非被要求，否则不删

准则给的检验标准是：**每一行改动都能直接追溯到用户的请求。**这条原则保护的是代码审查的可追溯性——一次提交只解决一个问题，review 才能聚焦。

### Goal-Driven Execution：堵"能跑就算完成"

> **定义成功标准。循环验证直到达成。**

Karpathy 说过：*"AI 极其擅长循环执行直到满足特定目标。不要告诉它要做什么，给它成功标准，然后看它跑。"*

这条原则要求把模糊指令转化为可验证目标，README 给了三个标准转换：

| 模糊指令 | 转换为可验证目标 |
|----------|------------------|
| "加个验证功能" | "为非法输入写测试，然后让测试通过" |
| "修这个 bug" | "写一个能复现 bug 的测试，然后让它通过" |
| "重构 X" | "重构前后测试全部通过" |

多步骤任务必须列出计划：

```
1. [步骤] → 验证: [检查点]
2. [步骤] → 验证: [检查点]
3. [步骤] → 验证: [检查点]
```

准则末尾点明了底层逻辑：强的成功标准让 AI 能独立循环；弱的标准（比如"让它能跑"）需要人不断澄清。把"够了"写成可运行的检查，AI 才能稳定收敛。

## 安装与集成：四种方式

### 方式一：Claude Code 插件（推荐）

Claude Code 用户通过插件市场安装：

```bash
# 添加市场插件
/plugin marketplace add forrestchang/andrej-karpathy-skills

# 安装插件
/plugin install andrej-karpathy-skills@karpathy-skills
```

安装后，这个指南会跨所有项目生效。仓库已从 forrestchang 个人账号迁入 multica-ai 组织，但 README 与插件市场仍使用 forrestchang 路径，GitHub 会自动重定向，命令原样可用。

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

要区分两种情况。**克隆本仓库直接用**：项目内置了 Cursor 规则 `.cursor/rules/karpathy-guidelines.mdc`，且标记为 `alwaysApply: true`，在 Cursor 里打开就自动生效，可在 Settings → Rules 里确认。**用到你自己的项目**：把这个 `.mdc` 文件复制到你项目的 `.cursor/rules/` 目录（不存在就新建），或者把 `CLAUDE.md` 内容合并进你的规则文件。注意 Cursor 默认不读取 `CLAUDE.md` 和 `.claude-plugin/`，指望"放个 CLAUDE.md 两边通吃"是不行的。

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

任务流变化：用户提需求 → AI 列假设和选项 → 用户确认范围 → AI 给最简方案 → 用户拍板 → AI 实现。对比旧流程"用户 → AI → 代码 → Code Review → 发现问题 → 打回 → AI 修改 → 再次 Review"，沟通成本被前置到了编码之前，整段返工换成了预先的一轮对话。

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

> 只有当真正需要多种折扣策略时，才值得引入抽象。需求还没来，不要预建。

## 横向对比：定位差异

| 项目 | 定位 | Stars（截至 2026-09-21） | 特点 |
|------|------|-------|------|
| **andrej-karpathy-skills** | AI 行为准则 | 214,402 ⭐ | 一个文件约束 AI 的决策质量，4 条核心原则 |
| [dair-ai/Prompt-Engineering-Guide](https://github.com/dair-ai/Prompt-Engineering-Guide) | Prompt 工程指南 | 78,514 ⭐ | 面向人的学习资料汇编，覆盖面广，不给 AI 直接读 |
| [openinterpreter/open-interpreter](https://github.com/openinterpreter/openinterpreter) | 本地 AI 编程 | 68,397 ⭐ | 让 AI 在本地电脑上执行代码的工具，不约束行为 |
| [anthropics/claude-cookbooks](https://github.com/anthropics/claude-cookbooks)（原 anthropic-cookbook） | 官方示例集 | 52,861 ⭐ | 面向人的 Prompt 模板与 API 用法示例，侧重技巧 |
| [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents) | LLM 应用构建原则 | 26,324 ⭐ | 给开发者看的 12 条构建原则，约束的是软件设计，不是模型行为 |

andrej-karpathy-skills 的差异化在于作用对象：上面这些项目要么面向人（教程、原则、示例集），要么面向工具链（本地执行），没有哪个直接进模型上下文、约束模型生成代码前的推理路径。它管的是 AI 怎么干活，而不是人怎么写软件。

## 项目架构

```
andrej-karpathy-skills/
├── CLAUDE.md                    # 核心指南文件
├── README.md                    # 英文说明
├── README.zh.md                 # 中文说明
├── CURSOR.md                    # Cursor 使用说明
├── EXAMPLES.md                  # 15 个实战案例 ⭐（学习价值极高）
├── .cursor/rules/
│   └── karpathy-guidelines.mdc  # Cursor 项目级规则
├── .claude-plugin/              # Claude Code 插件配置
│   ├── marketplace.json
│   └── plugin.json
└── skills/
    └── karpathy-guidelines/
        └── SKILL.md             # Agent Skills 形态
```

`EXAMPLES.md` 单独拎出来就是一部 AI 编程反范本百科全书，建议通读。

## 局限与边界

准则本身标注了一个重要取舍：

> *"这些准则偏向谨慎而非速度。对于琐碎任务（改错字、明显的一行代码改动），请自行判断——不是每个改动都需要完整走一遍流程。"*

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

## 怎么判断它起作用了

README 给了四条可观察的生效标志，装上之后随时可以对照检查：

- **diff 里只剩被要求的改动**——没有顺手改格式、顺手重构
- **因过度复杂导致的返工变少**——代码第一次就写得简单
- **澄清问题出现在动手之前**——而不是犯错之后
- **PR 干净、最小**——没有夹带的"改进"

如果这几条都没出现，多半是 `CLAUDE.md` 没被正确加载，回看下一节的排查清单。

## 采用建议

**给个人开发者**：如果你日常用 Claude Code 或 Cursor，优先用方式一的插件路径，让准则跨项目生效。第一次试用时挑一个新功能开发任务，观察 AI 是否在动手前主动列假设和选项。如果 AI 仍然埋头就写，检查 `CLAUDE.md` 是否被正确加载。

**给团队**：把 `CLAUDE.md` 纳入仓库，让所有成员的 AI 会话读到同一份规则。在 Code Review 阶段，把"是否暴露假设""是否做最小改动""是否给可验证标准"列为 review 检查项，让工具行为和人的审查互相印证。

**给已有 `CLAUDE.md` 的项目**：用方式三追加，避免覆盖既有规则。追加后通读一遍合并后的文件，确认四项原则与既有规则没有冲突。

**何时绕开准则**：typo 修正、单行改动、明确限定范围的小修改，可以直接让 AI 动手，跳过完整流程。准则本身允许这种判断。

---

## 常见问题与故障排查

### Q1：安装了插件，但 AI 仍然不按准则行事，为什么？

**A**：先确认 `CLAUDE.md` 是否真的进了上下文。在 Claude Code 中，用 `/memory` 查看项目指令文件是否被识别，用 `/context` 查看 `CLAUDE.md` 是否占用上下文。如果没被加载，依次检查：

1. 文件是否在项目根目录
2. 文件名是否是 `CLAUDE.md`（大小写敏感）
3. 文件内容是否是有效的 Markdown

### Q2：准则会不会让 AI 变慢？

**A**：会让对话变多，但不会让代码变慢。准则要求 AI 在动手前先列假设和选项，这会增加一轮对话，但能消除整段返工。Karpathy 在准则里明确说了："这些准则偏向谨慎而非速度。对于琐碎任务，请自行判断。"

### Q3：如果我和 AI 对需求的理解有分歧，准则能解决吗？

**A**：能。Think Before Coding 原则要求 AI "明确说出假设，不确定就问"。如果 AI 仍然不提问，先按 Q1 排查文件加载；加载无误还不行，换一个指令遵循能力更强的模型试试。

### Q4：团队里有人不喜欢准则约束，怎么办？

**A**：准则不是强制的。你可以把它当成"推荐流程"而不是"硬性规定"。在 Code Review 阶段，把"是否暴露假设""是否做最小改动"列为 review 检查项，让团队逐步形成共识，而不是强制推行。

### Q5：Cursor 和 Claude Code 的准则会冲突吗？

**A**：不会。Claude Code 用 `CLAUDE.md`，Cursor 用 `.cursor/rules/*.mdc`，两套机制独立。如果同一个项目同时用 Claude Code 和 Cursor，需要维护两份规则文件（CURSOR.md 明确说明 Cursor 默认不读取 `CLAUDE.md`）。建议把核心准则内容提取出来做成共享文档，再分别适配到 `CLAUDE.md` 和 `.cursor/rules/*.mdc`。

---

## 动手练习

### 练习 1：安装并测试准则

在你的一个现有项目里添加 `CLAUDE.md` 文件（从 andrej-karpathy-skills 仓库下载），然后给 AI 提一个模糊需求（如"加个导出功能"），观察 AI 是否在动手前主动列假设和选项。记录观察结果。

<details>
<summary>参考思路</summary>

1. 下载 `CLAUDE.md`：`curl -o CLAUDE.md https://raw.githubusercontent.com/multica-ai/andrej-karpathy-skills/main/CLAUDE.md`
2. 给 AI 提模糊需求："加个导出用户数据的功能"
3. 观察 AI 的反应：
   - 是否符合 Think Before Coding 原则（主动列假设、问澄清问题）
   - 是否符合 Simplicity First 原则（给最简方案）
   - 是否符合 Surgical Changes 原则（只改必要的代码）
   - 是否符合 Goal-Driven Execution 原则（给可验证标准）
4. 如果 AI 仍然埋头就写，检查 `CLAUDE.md` 是否被正确加载

</details>

### 练习 2：识别过度工程

下面这段 AI 生成的代码有什么问题？如何用 Karpathy 四项原则改进？

```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import Protocol, Union
from dataclasses import dataclass

class DataExporter(ABC):
    @abstractmethod
    def export(self, data: list) -> str: pass

class JSONExporter(DataExporter):
    def export(self, data: list) -> str:
        import json
        return json.dumps(data)

class CSVExporter(DataExporter):
    def export(self, data: list) -> str:
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(data[0].keys())
        for item in data:
            writer.writerow(item.values())
        return output.getvalue()

class ExcelExporter(DataExporter):
    def export(self, data: list) -> str:
        # 预留的 Excel 导出功能
        pass

class ExporterFactory:
    @staticmethod
    def get_exporter(format: str) -> DataExporter:
        if format == 'json':
            return JSONExporter()
        elif format == 'csv':
            return CSVExporter()
        elif format == 'excel':
            return ExcelExporter()
        else:
            raise ValueError(f"Unsupported format: {format}")

# 使用
exporter = ExporterFactory.get_exporter('json')
result = exporter.export([{'name': 'Alice', 'age': 30}])
```

<details>
<summary>参考思路</summary>

**问题**：
1. 过度抽象：为了"导出"这个功能，引入了 Abstract Factory、Strategy Pattern 等设计模式
2. 过度工程：写了 `ExcelExporter` 但这个类没有实现（只是预留）
3. 不必要的依赖：用了 `abc`, `enum`, `typing.Protocol`, `dataclasses` 等模块
4. 没遵循 Simplicity First：用户只是想导出数据，不需要这么复杂的架构

**改进**：
```python
import json

def export_to_json(data: list) -> str:
    """导出数据为 JSON 格式。"""
    return json.dumps(data, ensure_ascii=False, indent=2)

# 如果需要 CSV
import csv
from io import StringIO

def export_to_csv(data: list) -> str:
    """导出数据为 CSV 格式。"""
    if not data:
        return ""
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()

# 使用
result = export_to_json([{'name': 'Alice', 'age': 30}])
```

只有当真正需要多种导出格式时，才值得引入抽象。需求还没来，不要预建。

</details>

### 练习 3：定制你的 CLAUDE.md

在你的 `CLAUDE.md` 文件里加上一条适合你团队的规则（如代码风格、测试要求、日志规范），然后在下一个任务里观察 AI 是否遵守这条规则。

<details>
<summary>参考思路</summary>

**示例定制规则**：

```markdown
## Team-Specific Rules

### Code Style
- Always use double quotes for strings
- Always add type hints to function signatures
- Always add docstrings to public functions

### Testing
- Always write unit tests for new functions
- Always achieve at least 80% code coverage

### Logging
- Always log function entry and exit at DEBUG level
- Always log errors at ERROR level with full context
```

**验证方法**：
1. 把上面的规则加到 `CLAUDE.md`
2. 让 AI 写一个新函数
3. 检查 AI 是否遵守了这些规则（如是否加了类型提示、是否写了测试、是否加了日志）
4. 如果 AI 没遵守，检查规则是否写清楚了（AI 能理解吗？）

</details>

---

## 自测题

### 问题 1：四项原则分别堵什么漏洞？

<details>
<summary>查看答案</summary>
<b>答案</b>：
1. Think Before Coding：堵"默默假设"
2. Simplicity First：堵"过度抽象"
3. Surgical Changes：堵"顺手改"
4. Goal-Driven Execution：堵"能跑就算完成"
</details>

### 问题 2：Karpathy 观察到的"过度抽象"具体指什么？准则如何对抗它？

<details>
<summary>查看答案</summary>
<b>答案要点</b>：
Karpathy 在推文里描述的现象是：模型"极度喜欢把代码和 API 搞得过度复杂，堆砌抽象层，不清理死代码，100 行能搞定的事搞出 1000 行"。Simplicity First 把这条观察逐条反着写进规则：不做超出要求的功能、单次使用不抽象、没要求的灵活性不加、不为不可能的场景设防、200 行能压到 50 行就重写。每一条都对应现象的一个侧面。
</details>

### 问题 3：什么时候应该绕开准则？

<details>
<summary>查看答案</summary>
<b>答案</b>：
- typo 修正
- 简单的单行代码改动
- 明显的格式化调整
- 已明确限定范围的小修改

准则本身允许这种判断。关键是"明确限定范围"——如果范围不明确，还是要走完整流程。
</details>

### 问题 4：Goal-Driven Execution 如何让 AI 稳定收敛？

<details>
<summary>查看答案</summary>
<b>答案要点</b>：
AI 擅长在明确目标下循环优化，不擅长在模糊目标下自行判断"够了"。Goal-Driven Execution 要求把模糊任务转化为可验证目标（如"为非法输入写测试，然后让测试通过"），强的成功标准让 AI 能独立循环，AI 才能稳定收敛。
</details>

### 问题 5：如果你是团队 Lead，怎么推行这套准则？

<details>
<summary>查看答案</summary>
<b>答案要点</b>：
1. 先把 `CLAUDE.md` 纳入仓库，让所有成员的 AI 会话读到同一份规则
2. 在 Code Review 阶段，把"是否暴露假设""是否做最小改动""是否给可验证标准"列为 review 检查项
3. 不要强制推行，让团队逐步形成共识
4. 挑一个新功能开发任务，让团队体验"AI 主动列假设"和"AI 埋头就写"的差异
</details>

---

## 进阶路径

### 阶段 1：快速体验（1 天）

- [ ] 安装 andrej-karpathy-skills 插件（Claude Code）或复制 `CLAUDE.md` 到项目根目录
- [ ] 挑一个简单任务（如"加个导出功能"），观察 AI 是否在动手前主动列假设
- [ ] 对照"怎么判断它起作用了"一节的四条标志，记录基线

### 阶段 2：深度使用（1 周）

- [ ] 把所有活跃项目都加上 `CLAUDE.md`
- [ ] 通读 `EXAMPLES.md`，理解 AI 编程的反范本
- [ ] 在 Code Review 阶段检查 AI 是否符合四项原则
- [ ] 根据你的团队规范，定制 `CLAUDE.md`（如加上代码风格、测试要求）

### 阶段 3：团队推行（2-4 周）

- [ ] 把 `CLAUDE.md` 纳入团队仓库，让所有成员共享同一份规则
- [ ] 在 Code Review 检查项里加入"AI 准则符合度"
- [ ] 收集团队反馈，调整准则细节（如哪些任务可以绕开准则）
- [ ] 培训团队成员：如何判断"简单任务"和"复杂任务"

### 阶段 4：定制与贡献（1-3 个月）

- [ ] 基于四项原则，扩展出适合你团队的定制准则（如加上安全规则、性能规则、日志规则）
- [ ] 向 andrej-karpathy-skills 提交 Feature Request 或 PR（注意同步维护 `CLAUDE.md`、`.mdc` 与 `SKILL.md` 三处）
- [ ] 分享你的定制准则（写博客、开 issue、提交到仓库）

### 进阶资源

- [Andrej Karpathy 原推](https://x.com/karpathy/status/2015883857489522876) — 项目灵感来源
- [andrej-karpathy-skills 仓库](https://github.com/multica-ai/andrej-karpathy-skills)
- [EXAMPLES.md](https://github.com/multica-ai/andrej-karpathy-skills/blob/main/EXAMPLES.md) — AI 编程反范本百科全书
- [Multica 平台](https://github.com/multica-ai/multica) — 同一作者的开源编码代理管理平台，50,967 Stars（截至 2026-09-21）
- [Claude Code 官方文档](https://docs.anthropic.com/en/docs/claude-code)
- [Cursor Rules 文档](https://cursor.com/docs/rules)

---

*本文基于 2026-05-19 GitHub Trending 数据撰写；2026-09-21 对照仓库与 GitHub API 复核全文，更新 Stars、许可证、四项原则细则与对比项目数据。*
