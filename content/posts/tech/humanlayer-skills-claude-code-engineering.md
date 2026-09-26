---
title: "humanlayer/skills：六个直击 Claude Code 真实痛点的工程技能"
date: 2026-09-12T03:45:00+08:00
slug: "humanlayer-skills-claude-code-engineering"
github_repo: "humanlayer/skills"
source_key: "gh:humanlayer/skills"
description: "HumanLayer 出品的 Claude Code skills 合集，六个技能各自瞄准真实工程痛点：CLAUDE.md 指令遵循、React prop 类型收敛、迭代式 agent 工作流、控制回路设计、PR 可视化描述与视觉解释。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "AI 工程化", "开源"]
---

# 当 skills 合集开始做减法

Agent skills 生态正在经历一场数量竞赛，而 HumanLayer 的这个合集反其道而行：**只有六个技能，每一个都对应一个可验证的工程痛点**。HumanLayer 是 12-Factor Agents 的作者团队——那份把 agent 可靠性写成十二条工程原则的指南，在 GitHub 上已获逾两万星。这个背景决定了合集的取向：不追花哨能力，专注让 coding agent 在真实代码库里更可控。

> **项目地址**：[github.com/humanlayer/skills](https://github.com/humanlayer/skills)

## 核心数据（截至 2026-09）

| 项目 | 值 |
|------|-----|
| Stars / Forks | 约 4,200 / 134 |
| 开源协议 | MIT |
| 主要语言 | TypeScript |
| 技能数量 | 6 |
| 仓库形态 | Claude Code plugin marketplace，`npx skills add` 安装 |
| 最近提交 | 2026-08 |

## 六个技能，六种工程痛点

| 技能 | 痛点 | 一句话机制 |
|---|---|---|
| improve-claude-md | CLAUDE.md 指令遵循率低 | 用 `<important if>` 条件块重写指令 |
| narrow-react-prop-types | prop 类型被 Storybook/mock 撑宽 | 按真实代码路径收敛类型 |
| build-iterated-agentic-loop | 想要可持续迭代的 agent 工作流 | 生成 repo 内 skill + GitHub Actions 循环 |
| design-control-loop | agent 任务缺乏结构化设计 | 访谈式设计传感器/控制器/执行器回路 |
| visual-pr | PR 描述与实现脱节 | 用可视化结构大纲写 PR 描述 |
| show-me | 需要快速理解陌生话题 | 图表 + 代码形态草图 + HTML 产物解释 |

前四个是"改代码、建系统"型，后两个是"解释"型。以下逐个展开。

## 一、improve-claude-md：让 CLAUDE.md 不再被无视

**问题根源**：Claude Code 每加载一份 CLAUDE.md，都会注入一条系统提示：

> "this context may or may not be relevant to your tasks. You should not respond to this context unless it is highly relevant to your task."

这句提示的本意是防止模型被无关上下文干扰，副作用是：模型会主动忽略它判定为"不相关"的内容。文件越长、杂项越多，被忽略的概率越大——连真正该遵守的规则也一起丢掉。写了几十条指令，模型只稳定遵循一部分，根子在这里。

**机制**：improve-claude-md 的思路不是加指令，而是把指令重构成 `<important if="条件">` 块。条件满足时，块内指令才被"点亮"：

```markdown
<important if="you are adding or modifying imports">
- Use `@/` absolute imports (see tsconfig.json for path aliases)
- Avoid default exports except in route files
</important>
<important if="you are creating new components">
- Use functional components with explicit prop interfaces
</important>
```

这个 XML 标签模式与 Claude Code 系统提示同源，等于给模型一个显式的相关性信号，抵消掉"may or may not be relevant"的模糊化。这与 HumanLayer 在 12-Factor Agents 中"小而精的提示词优于大而全"的主张一脉相承。

**五条原则**：

1. **基础上下文保持裸文本**：项目身份、目录地图、技术栈——对 90% 以上的任务都相关，不该被包裹。判断标准：几乎每次任务都要用的留外面，只有特定类型工作才需要的包进去。
2. **条件必须具体**：坏条件如 "you are writing or modifying any code" 几乎匹配一切，等于没包；每条规则要有自己的窄触发条件。
3. **保持简短**：不要拆成多个文件逼 agent 反复读；`<important if>` 的要点是全部内联、按条件加权——agent 都看得到，但只关注匹配项。
4. **做减法**：linter、formatter、pre-commit hook 能强制的规则删掉；agent 从现有代码模式就能学到的删掉；代码片段换成文件路径引用（"see `src/utils/example.ts`"）。
5. **保留全部命令**：命令表是基础参考，即使某些命令少用。

最终输出结构固定：单行项目身份 → 裸的项目地图 → 包裹的命令表 → 每条规则各自一个 `<important if>` 块 → 每个领域（测试、API、状态管理、i18n）各自一块。

## 二、narrow-react-prop-types：把类型从"文档"恢复为"约束"

**问题**：React 组件的 TypeScript 类型会被一个隐蔽的过程逐渐撑宽。为了让 Storybook 故事、测试、mock 数据好写，props 被不断放宽——可选属性、宽联合类型、`?? []` 兜底、`onSelect?.()` 可选回调。真实运行路径只用其中一小部分，类型系统却允许了大量不存在的状态。

**机制**：这个技能把**非测试、非 Storybook 的调用点**当作 prop 契约的唯一事实源。流程：

1. **识别可疑组件**：大而多可选字段的 props 接口、可选回调、`items ?? []` 类兜底、demo 向的 `defaultFoo`。
2. **找出所有真实使用点**：把调用点分成 live code paths（路由、已接线的组件、hooks、生产导出）与 support code（stories、测试、fixtures、mocks）。只有 live code paths 决定组件 API 支持什么。
3. **推导每个 prop 的归属**：Required（所有真实调用点都传）、Optional（有真实调用点省略且构成有意义状态）、Removed（无真实调用点使用）。
4. **收紧类型**：公共 prop 类型、内部子组件 props 一起收紧；同步更新共享同一类型的所有变体。
5. **删除兜底逻辑**：只为宽松类型存在的 `?? []`、`&&` 防御性代码一并删除。
6. **让测试适配契约，而不是反过来**：stories/测试崩了就去提供真实 handler 和状态，或建 fixture/helper；绝不把已收紧的 prop 改回可选。

类型推导优先用工具类型而非手写近似：`Parameters<typeof fn>[0]`、`ReturnType<typeof fn>`、`Extract<Union, Shape>`、`React.Dispatch<React.SetStateAction<T>>`。

**为什么有效**：类型越宽，组件需要处理的状态分支越多——每个可选 prop 都引入一条必须正确维护的分支。收紧类型把"不可能的状态"从代码里删除，组件逻辑随之简化。这是把类型系统从"文档"恢复为"约束"。

## 三、build-iterated-agentic-loop 与 design-control-loop：两个"建系统"技能

这两个技能共享同一套工程观：**agent 任务不该靠一次性提示词，而该被设计成可调度、可测量、可人工干预的循环**。

### 3.1 design-control-loop：把控制论搬进代码库

这个技能用访谈的方式，为你的代码库定制一个 **agentic 控制回路**，心智模型借自控制论：

- **Set point（设定点）**：想让代码库某个属性到达的状态——一条不变量、一个覆盖率阈值、或一个"每次运行减少若干"的方向。
- **Sensor（传感器）**：测量当前状态与设定点的差距。现有工具就是现成的原材料：静态分析、AST 搜索、测试套件、类型检查器，甚至一个自定义脚本。
- **Controller（控制器）**：根据测量决定下一个小的、低风险的增量。可以是确定性的脚本，也可以是按自然语言标准做决策的 agent，还可能与 sensor 或 actuator 融合。
- **Actuator（执行器）**：应用变更并开 PR 的编码 agent，配一个 repo 内 skill 承载它的判断力。
- **Disturbances（扰动）**：队友并行提交、依赖升级、生成代码——持续改变系统的外部因素。
- **Dampener（阻尼器，可选）**：回归门，在循环慢慢改善问题的同时阻止问题恶化。

执行分八个阶段（A-H）：先读懂代码库再提问；访谈定设计；写 actuator skill；让每个组件都能本地独立运行；再接入 CI 做成定时工作流；把人类放进回路——一个版本化的 memory/反馈文件每次运行注入 actuator 上下文，PR 上还能用 `/iterate` 让 agent 更新记忆；默认每个 loop 只允许一个 open PR，防止 PR 堆积超过审阅速度；最后验证 YAML、dry-run、再提速。

### 3.2 build-iterated-agentic-loop：把循环变成脚手架

如果说 design-control-loop 是"为你定制"，build-iterated-agentic-loop 则是"给你一套模板"：生成 repo 内 skill，外加一个迭代式 coding-agent GitHub Actions 工作流——含 prompt、memory 文件和参考模板（skill 骨架、PR 响应模板、agent-runner 模板、工作流 YAML）。装好即有一条可跑的循环，适合不想从零设计的人。

## 四、visual-pr 与 show-me：两个"解释"技能

### 4.1 visual-pr：PR 描述也是工程产物

PR 描述通常沦为提交日志的复述。visual-pr 把它改造成一个**可视化结构大纲**：Why the change 只写一句话；Special things to note 一到三条（迁移、兼容性约束、刻意的省略）；Change outline 用结构视图而非逐文件流水账——SQL 表与接口契约变化配伪代码、关键类型变化、浅文件树、React 组件树、调用/数据流变化。每个视图只保留审阅者需要的，用 `diff` 块展示既有形状的变化，用完整目标形状展示新内容。它调用 `gh pr view` 检查现有 PR、`gh pr edit` 更新描述，并把描述存进 `.humanlayer/tasks/` 目录。

### 4.2 show-me：先图后文

show-me 是纯解释性技能，且 `disable-model-invocation: true`——只能由用户显式调用，不让模型自作主张打断对话。它按主题挑选最小的视图：伪代码展示逻辑、调用树展示控制流、组件树展示 UI 结构、浅文件树展示文件职责、Mermaid 展示交互/数据流，`diff` 展示"什么变了"。对过于密集的概念，写一个聚焦的 HTML 文件（图表、信息图或微型 slide deck）并在浏览器打开。

## 五、方法论主线：六个技能是 12-Factor Agents 的可安装形态

12-Factor Agents 的十二条原则里，有几条能直接映射到这六个技能：

- **Small, focused agents** → improve-claude-md 做减法、narrow-react-prop-types 收敛状态空间
- **Own your control flow** → design-control-loop 把控制回路显式化
- **Contact humans with tool calls** → memory 文件、`/iterate`、open-PR 上限都是把人工审核制度化
- **Own your prompts / context window** → `<important if>` 块就是对上下文窗口的精细化管理

这个合集的价值不在某一个技能，而在于示范了 skills 生态里一种稀缺的品质：**每个技能都有明确的问题定义和验收标准**。improve-claude-md 的效果可以用指令遵循率验证；narrow-react-prop-types 的产出可以直接过类型检查。相比之下，大量"提升代码质量"类 skills 连判断是否生效的标准都没有。

## 适用边界

- **适合**：Claude Code 重度用户，尤其是 CLAUDE.md 已经膨胀、TypeScript 类型被测试代码污染的团队；想借鉴"如何写一个好 skill"的 skill 作者。
- **不适合**：期待大而全技能库的用户（去 anthropics/claude-plugins-community 或 openai/skills 更合适）；非 Claude Code 生态（调用方式绑定斜杠命令）。
- **注意**：仓库迭代快（2026-03 创建，2026-08 仍有提交），模板与 API 可能变动；生产使用前先在隔离分支验证效果。

## 延伸阅读

- [humanlayer/skills](https://github.com/humanlayer/skills) —— 本文主体
- [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents) —— 方法论出处，GitHub 逾两万星
- [Building companies with Claude Code（Anthropic 博客）](https://claude.com/blog/building-companies-with-claude-code) —— HumanLayer 创始人 Dexter Horthy 的访谈，交代合集的团队背景
- [Agent Skills 规范](https://agentskills.io/specification) —— build-iterated-agentic-loop 与 design-control-loop 生成 skill 时遵循的规范
