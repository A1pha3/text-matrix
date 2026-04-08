---
title: "Andrej Karpathy Skills：Claude Code进化指南"
date: 2026-04-08T12:45:00+08:00
slug: "andrej-karpathy-skills-claude-code-guide"
description: "Andrej Karpathy Skills 是一份改进 Claude Code 行为的 CLAUDE.md 指南，源于 Karpathy 对 LLM 编程陷阱的深刻洞察。掌握四大原则：Think Before Coding、Simplicity First、Surgical Changes、Goal-Driven Execution，让 AI 编程从"幻觉不断"到"精准可控"。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "AI编程", "最佳实践", "Agent Skills", "Karpathy"]
---

# Andrej Karpathy Skills：Claude Code进化指南

## 1. 学习目标

通过本文你将掌握：

- 理解 Karpathy 指出的 LLM 编程四大陷阱
- 熟练运用四大原则改进 Claude Code 行为
- 安装和配置本技能（插件或 CLAUDE.md）
- 在团队中推广 AI 编程最佳实践
- 解决实际使用中的常见问题

## 2. 问题根源：Karpathy 的洞察

### 2.1 LLM 编程的四大陷阱

Andrej Karpathy 在 2026 年初发表了一系列关于 LLM 编程的深刻观察，指出了当前 AI 编程助手的根本性问题：

**陷阱一：盲目假设**
> "The models make wrong assumptions on your behalf and just run along with them without checking."

LLM 经常默默地做出假设并一路执行下去，不检查、不确认、不质疑。这些错误假设会在代码中埋下难以发现的 bug。

**陷阱二：隐藏困惑**
> "They don't manage their confusion, don't seek clarifications, don't surface inconsistencies, don't present tradeoffs, don't push back when they should."

当 LLM 不理解需求时，它不会说出来，而是假装理解，产出一个可能完全错误的解决方案。它不会问"这个边界条件是什么"，而是猜测一个然后执行。

**陷阱三：过度工程**
> "They really like to overcomplicate code and APIs, bloat abstractions, don't clean up dead code... implement a bloated construction over 1000 lines when 100 would do."

这是最常见的陷阱。LLM 喜欢"过度设计"——创建永远用不到的抽象层、添加未请求的"灵活性"、保留死代码。200 行能解决的问题，它会写成 1000 行。

**陷阱四：副作用盲区**
> "They still sometimes change/remove comments and code they don't sufficiently understand as side effects, even if orthogonal to the task."

LLM 有时会"顺便"修改它不理解的部分——删除注释、改变与任务正交的代码。这往往导致难以调试的回归问题。

### 2.2 为什么需要专项指南

Karpathy 的核心洞察是：

> "LLMs are exceptionally good at looping until they meet specific goals... Don't tell it what to do, give it success criteria and watch it go."

**关键转变**：从告诉 LLM "怎么做"到定义"成功标准"，让它自己循环直到达标。

这份指南正是基于这一洞察，将 Karpathy 的原则转化为可操作的 CLAUDE.md 规则。

## 3. 四大原则深度解析

### 3.1 Think Before Coding（编码前思考）

**核心理念**：不要假设，不要隐藏困惑，主动呈现权衡。

这是最容易违反的原则。当 LLM 遇到不明确的需求时，它倾向于：
- 默默选择一个解释并执行
- 不问"这个需求是什么意思"
- 遇到冲突时选择忽略而非指出

**强制规则**：

```markdown
## Think Before Coding
- State assumptions explicitly — If uncertain, ask rather than guess
- Present multiple interpretations — Don't pick silently when ambiguity exists  
- Push back when warranted — If a simpler approach exists, say so
- Stop when confused — Name what's unclear and ask for clarification
```

**实际示例**：

| LLM 的常见错误 | Think Before Coding 要求 |
|--------------|----------------------|
| 假设用户想要 REST API | "我理解你想要一个 API，但有几个实现选项..." |
| 忽略边界条件 | "这个函数的边界情况（空输入、极大值）没有明确..." |
| 选择性忽略需求 | "我注意到需求中提到 X，但它与需求 Y 冲突..." |

### 3.2 Simplicity First（简洁优先）

**核心理念**：用最少的代码解决问题，不做任何投机性设计。

**Karpathy 的警告**：
- 如果 200 行能解决，1000 行就是过度工程
- 永远不要创建"将来可能用到"的抽象
- 除非明确要求，不要添加"灵活性"或"可配置性"

**强制规则**：

```markdown
## Simplicity First
- Minimum code that solves the problem. Nothing speculative.
- No features beyond what was asked
- No abstractions for single-use code
- No "flexibility" or "configurability" that wasn't requested
- No error handling for impossible scenarios
- If 200 lines could be 50, rewrite it
```

**自检问题**：
- "高级工程师会说这太复杂了吗？"如果是的，简化。
- "这个抽象层有被其他代码使用吗？"如果没有，删除。
- "这个配置项用户真的会改吗？"如果不会，移除。

### 3.3 Surgical Changes（精准修改）

**核心理念**：只触碰必须改的，只清理自己造成的垃圾。

**Karpathy 的观察**：
LLM 喜欢"顺手改进"——在修改 A 功能时，顺便重构了无关的 B 代码，修复了"看起来像 bug"的 C 问题。这些"顺便"往往引入难以追踪的回归。

**强制规则**：

```markdown
## Surgical Changes
- Don't "improve" adjacent code, comments, or formatting
- Don't refactor things that aren't broken
- Match existing style, even if you'd do it differently
- If you notice unrelated dead code, mention it — don't delete it
- Remove imports/variables/functions that YOUR changes made unused
- Don't remove pre-existing dead code unless asked
```

**边界判断**：

| 情况 | 正确做法 |
|------|---------|
| 你的修改使某个函数变成孤立的 | 删除这个函数 |
| 发现一个早已存在的死代码 | 只提及，不删除 |
| 看到不一致的代码风格 | 忽略，保持原样 |
| 你的修改创建了未使用的导入 | 删除这个导入 |

### 3.4 Goal-Driven Execution（目标驱动执行）

**核心理念**：定义成功标准，循环直到验证通过。

**Karpathy 的洞见**：
> "LLMs are exceptionally good at looping until they meet specific goals."

LLM 非常擅长在明确的成功标准下循环执行。但它需要人类给出可验证的目标，而非指令。

**强制规则**：

```markdown
## Goal-Driven Execution
- Define success criteria. Loop until verified.
- Transform imperative tasks into verifiable goals:

Instead of: "Add validation"
Transform to: "Write tests for invalid inputs, then make them pass"

Instead of: "Fix the bug"  
Transform to: "Write a test that reproduces it, then make it pass"

Instead of: "Refactor X"
Transform to: "Ensure tests pass before and after"
```

**多步任务格式**：

```markdown
1. [Step 1] → verify: [check criteria]
2. [Step 2] → verify: [check criteria]  
3. [Step 3] → verify: [check criteria]
```

**成功标志**：

当你看到以下行为时，说明指南正在起作用：

✅ **Diff 更干净** — 只有请求的更改出现
✅ **更少重写** — 代码第一次就足够简单
✅ **问题在实现前提出** — 而非在错误后
✅ **PR 简洁** — 没有顺便的重构或"改进"

## 4. 安装与配置

### 4.1 Option A：Claude Code 插件（推荐）

这是推荐的安装方式，一次安装，所有项目可用。

**第一步：添加 marketplace**

在 Claude Code 中执行：
```
/plugin marketplace add forrestchang/andrej-karpathy-skills
```

**第二步：安装插件**
```
/plugin install andrej-karpathy-skills@karpathy-skills
```

这会将指南安装为 Claude Code 插件，在所有项目中自动生效。

### 4.2 Option B：CLAUDE.md（项目级）

适用于需要项目特定规则或不想使用插件的场景。

**新项目**：
```bash
curl -o CLAUDE.md https://raw.githubusercontent.com/forrestchang/andrej-karpathy-skills/main/CLAUDE.md
```

**已有项目（追加）**：
```bash
echo "" >> CLAUDE.md
curl https://raw.githubusercontent.com/forrestchang/andrej-karpathy-skills/main/CLAUDE.md >> CLAUDE.md
```

### 4.3 项目级定制

将以下内容添加到你的项目 CLAUDE.md：

```markdown
## Project-Specific Guidelines
- Use TypeScript strict mode
- All API endpoints must have tests
- Follow the existing error handling patterns in `src/utils/errors.ts`
- No console.log in production code
```

## 5. 与其他技能的对比

| 技能 | 核心定位 | 与本技能关系 |
|------|---------|-------------|
| karpathy-llm-wiki | 知识管理 | 本技能改进编码，本技能改进写作 |
| claude-code-skills | Agent 技能集合 | 本技能是底层规则，Skills 是上层能力 |
| mattpocock-skills | 垂直领域技能 | 本技能是通用规则，Skills 是专项任务 |

**协同使用**：
```
"用 Simplicity First 的方式实现这个 API，然后记录到 wiki"
```

## 6. 团队推广指南

### 6.1 为什么需要团队统一

当团队中只有部分人使用这些规则时：
- AI 生成的代码风格不一致
- 代码审查时难以判断 AI 贡献的质量
- 返工和重构增加

### 6.2 推广步骤

1. **演示问题**：展示 Karpathy 描述的典型陷阱
2. **解释原则**：用实际代码示例说明四大原则
3. **统一安装**：团队统一使用插件或 CLAUDE.md
4. **代码审查**：在 Review 中标注违反规则的行为
5. **持续强化**：随着时间推移，AI 会内化这些原则

### 6.3 常见阻力及应对

| 阻力 | 应对策略 |
|------|---------|
| "太慢了" | 这是权衡——减少返工实际上更快 |
| "我的需求很简单" | 简单任务用判断——不是每个改动都需要全套流程 |
| "规则太死板" | 这些是指南不是法律——可按需调整 |

## 7. 最佳实践

### 7.1 自检清单

在提交任何 AI 生成的代码前：

- [ ] **Think Before Coding**：我是否验证了所有假设？
- [ ] **Simplicity First**：这段代码是否最简？有没有投机性设计？
- [ ] **Surgical Changes**：这个 Diff 是否只包含必要改动？
- [ ] **Goal-Driven**：我是否定义了成功标准？

### 7.2 给 AI 的提示词改进

| 原始提示词 | 改进后提示词 |
|-----------|-------------|
| "帮我写一个 API" | "用 TDD 方式写一个 CRUD API，先写测试，成功标准：所有测试通过且符合 REST 规范" |
| "修复这个 bug" | "先写一个能重现这个 bug 的测试，然后让测试通过" |
| "重构这个模块" | "在不改变外部行为的前提下重构，确保重构前后测试都通过" |

### 7.3 权衡说明

Karpathy 的 Guidelines 偏向**谨慎而非速度**。这不是为了慢，而是为了减少在非关键任务上的代价高昂的错误。

> "For trivial tasks (simple typo fixes, obvious one-liners), use judgment — not every change needs the full rigor."

**目标是在非平凡工作上减少代价高昂的错误，而非拖慢简单任务。**

## 8. FAQ

**Q: 这些规则会限制 AI 的创造力吗？**

A: 不会。这些规则约束的是"盲目的创造力"——没有方向的创作。真正的创造力应该在明确的成功标准下发挥。

**Q: 如何平衡 Simplicity First 和架构演进？**

A: 原则是"不要投机性设计"。架构演进是必要的设计决策，不算投机。但如果当前只需要一个单文件脚本，就不要创建微服务架构。

**Q: 团队中可以有不同的项目规则吗？**

A: 可以。CLAUDE.md 是项目级的。项目可以有自己的额外规则，但基础四大原则应该统一。

**Q: 这些规则对所有编程语言适用吗？**

A: 四大原则是语言无关的。具体实现（如类型系统、测试框架）应根据语言调整。

**Q: 什么时候应该忽略这些规则？**

A: 当任务极其简单时（如修复typo）、当规则明显不适用时。关键是**有意识地判断**，而非盲目遵循或忽视。

## 9. 总结

Andrej Karpathy Skills 是一份将 AI 编程大师的洞察转化为可操作指南的杰作。四大原则：

| 原则 | 核心问题 | 解决 |
|------|---------|------|
| Think Before Coding | 盲目假设 | 显式声明，主动质疑 |
| Simplicity First | 过度工程 | 最简代码，拒绝投机 |
| Surgical Changes | 副作用盲区 | 精准修改，只清自己的垃圾 |
| Goal-Driven Execution | 模糊目标 | 定义成功，循环验证 |

**核心价值**：从"告诉 AI 怎么做"转变为"给 AI 成功标准，让它循环达标"。

这不是限制 AI 的能力，而是让它发挥真正擅长的部分：**在明确目标下的持续执行**。

---

*🦞 每日08:00自动更新*
