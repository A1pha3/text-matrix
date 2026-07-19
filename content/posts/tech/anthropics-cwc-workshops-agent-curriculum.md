---
title: "cwc-workshops：Anthropic 的 Code with Claude 工作坊资料集"
date: 2026-07-20T03:02:36+08:00
categories: ["技术笔记"]
tags: ["anthropic", "claude", "workshops", "agent", "mcp"]
description: "cwc-workshops 是 Anthropic 官方 Code with Claude 工作坊的材料合集，覆盖 10 个 workshop，从模型选型、agent 分解、managed agents 到评测驱动开发，每个都是 Anthropic 团队亲自跑过的实操课。"
---

# cwc-workshops：Anthropic 的 Code with Claude 工作坊资料集

## 一句话判断

cwc-workshops 不是"教程合集"，而是 Anthropic 自己**跑过的实操工作坊原始材料**——每个 workshop 都对应一个 Anthropic 团队跑过的 workshop session，配源码、配置、笔记。它最适合那些想看"Anthropic 内部怎么用 Claude Code / Managed Agents / Skills / MCP"的人。

## 项目定位

- **仓库**：`anthropics/cwc-workshops`，Apache-2.0 协议，TypeScript / Python
- **GitHub Stars**：1.75K，Forks 497（2026-06-26 数据）
- **状态**："Workshop materials. Not maintained and not accepting contributions."——这是 Anthropic 跑完 workshop 之后归档的原始材料，**不会再更新**，但也不删
- **内容载体**：每个 workshop 一个子目录，含完整源码 + 笔记 + 配置

## 10 个 Workshop 全景

| Workshop | 主轴 | 关键技术 |
|----------|------|----------|
| `rightmodel/` | Picking the Right Model | Claude Code SKILL + LLM eval suite + 模型 / inference param sweep |
| `agent-decomposition/` | Compose Multi-Agent Systems with Skills and MCP | 把 400 行单 agent 拆成 skills + code execution + callable_agents |
| `how-we-claude-code/` | How We Claude Code | AI 辅助产品 workflow 三阶段：interview → divergent design → Vite + React app |
| `ship-your-first-managed-agent/` | Ship Your First Managed Agent | Streamlit 事故 dashboard + 离线 SRE Agent，通过 7 个小函数接通 |
| `agent-battle/` | Agent Battle | 45 分钟竞赛配置 Managed Agent，钻石最多胜、token 最少破平 |
| `agents-that-remember/` | Agents That Remember | 给 amnesiac agent 加 memory store + Dreaming Service |
| `eval-driven-agent-development/` | Eval-Driven Agent Development | PPTX 生成 agent 6 个 variant + 10-task eval suite + 双层 grader |
| `production-ready-agent/` | Production-Ready Agent | Deal Desk：M&A 研究多 agent + memory store + Linear MCP + graded investment thesis |
| `research-desk/` | The Research Desk | SEC filings research desk：versioned agent 调度 + edgartools Skill + outcome-graded scorecards |

每个 workshop 都遵循同一个模板：

1. **目标**：用 1-2 句话讲清楚这个 workshop 解决什么问题
2. **场景**：模拟一个真实业务 / 工程场景
3. **材料**：完整可运行的代码 + 数据集 + 配置文件
4. **演进路径**：从最 naive 的实现逐步迭代到 production-grade
5. **评测**：每个 variant 都对应一个 eval 任务，能跑出量化对比

## 关键机制拆解

### 1. Managed Agents + Skills + MCP 三件套

Anthropic 在 2025-2026 年的 agent 技术栈是 Managed Agents（托管 agent runtime）+ Skills（SKILL.md 协议）+ MCP（外部工具协议）三件套。cwc-workshops 的几乎所有 workshop 都围绕这三件套展开：

- **Skills**：用 SKILL.md 把领域知识 / 工作流编码成可被 agent 加载的指令
- **MCP**：通过 MCP server 把外部工具接入 agent
- **Managed Agents**：托管的 agent runtime，支持 sub-agent 调度、memory store、eval 跟踪

这三个组件的关系是：Skills 描述"做什么"，MCP 提供"用什么做"，Managed Agents 负责"调度"。三者组合起来就是完整的 agent 系统。

### 2. eval-driven development 的范例

`eval-driven-agent-development/` 和 `agent-battle/` 两个 workshop 都把 eval 做成核心环节：

- **Programmatic grader**：对可验证的产物（PPTX XML metric、code correctness）做程序化评分
- **LLM-as-judge**：对不可验证的产物（生成的 slide 质量、生成的答案有用性）用 LLM 评分
- **Two-layer grader**：程序化 + LLM 双层评分，互补盲区

这种"每改一个 prompt 都跑一次 eval"的模式是当前 agent 工程化的核心方法论。cwc-workshops 直接给出了**Anthropic 内部如何用这套方法论迭代 agent**的范例。

### 3. 真实业务场景

workshop 不是 toy example：

- `production-ready-agent/` 模拟 Deal Desk M&A 研究
- `research-desk/` 模拟 SEC filings research desk
- `ship-your-first-managed-agent/` 模拟 SRE 事故响应

每个场景都对应一个"在企业里有真实价值的 agent 应用"。学习者做完这些 workshop 等于把 Anthropic 团队的实战经验跑了一遍。

### 4. 归档而非维护

README 明确说"Not maintained and not accepting contributions"——这意味着：

- **代码可能用旧版本 SDK**：读者要自己适配到当前 SDK
- **配置可能用过时的 model id**：要按当前可用模型做替换
- **但核心设计思想不过时**：Skills + MCP + Managed Agents 的方法论仍然代表 Anthropic 的当前方向

对学习者来说，关键是**理解每个 workshop 的设计意图**，而不是逐行复用代码。

## 适用人群

- **AI 工程师**：想看 Anthropic 内部怎么用 Managed Agents + Skills + MCP
- **Agent 架构师**：想学 eval-driven development 方法论
- **教育者**：想在公司 / 高校内部跑类似 workshop 的人
- **产品经理**：想理解 agent 技术的边界和落地形态

## 不适合谁

- **零基础 AI 学习者**：workshop 默认你已经会用 Claude Code + 理解 MCP
- **期待长期维护的人**：README 明确"not maintained"
- **只想看"如何用 Claude 写代码"的人**：大部分 workshop 不聚焦 Claude Code 本身，而是 Managed Agents

## 仓库地址

https://github.com/anthropics/cwc-workshops

## 阅读路径建议

1. 先读 README 的 workshop 列表，挑一个你最关心的场景
2. 跑该 workshop 的源码，确认环境能正常工作
3. 重点读 workshop 的笔记（`README.md` / `NOTES.md`）理解设计意图
4. 跑对应的 eval suite，看 variant 之间的量化对比