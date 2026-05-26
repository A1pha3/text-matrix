+++
title = "Coding Agent 工作流"
date = "2026-05-18T10:35:00+08:00"
draft = false
url = "/coding-agent/"
type = "topic"
description = "聚焦 Claude Code、Codex、Cline、Roo Code 与浏览器/MCP 工具链的 Coding Agent 工作流专题页，帮助开发者从工具认知走到真实可复用的工程实践。"
audience = [
  "已经开始使用 Claude Code、Codex、Cline 或 Roo Code 的开发者",
  "想从“让 AI 帮我写几段代码”进化到“让 AI 真正参与工程流程”的实践者",
  "正在思考 MCP、Skills、浏览器自动化和上下文系统怎么组合的人"
]

outcomes = [
  "知道不同 Coding Agent 工具各自适合什么场景",
  "建立 Skills、MCP、浏览器能力和验证流程之间的连接方式",
  "把一次性工具体验收束成更稳定的工程工作流"
]

[[starterPack]]
title = "Treat Coding Agents Like Developers"
url = "/posts/tech/treat-coding-agents-like-developers/"
note = "先建立方法论，再决定怎么选工具。"

[[starterPack]]
title = "Everything Claude Code：完整指南"
url = "/posts/tech/ai-agent/everything-claude-code-comprehensive-guide/"
note = "从主流路径进入最完整的 Coding Agent 工作流。"

[[starterPack]]
title = "Chrome DevTools MCP 与 AI Coding Agents 使用指南"
url = "/posts/tech/chrome-devtools-mcp-ai-coding-agents-guide/"
note = "把 Coding Agent 接进真实浏览器和调试环境。"
+++

# Coding Agent 工作流

如果说 `AI Agent` 更像一个总类概念，那么 `Coding Agent` 关心的是另一件更具体的事：如何让模型真正参与代码理解、修改、调试、验证和工程协作，而不是只在聊天框里给出一段看起来合理的建议。

这个专题页聚焦的不是“哪个工具最火”，而是如何形成一条真实可复用的 Coding Agent 工作流。你会看到工具对比、技能系统、浏览器自动化、上下文管理、长代码库协作，以及一些更接近生产实践的经验。

## 这条路径适合谁

- 已经开始使用 Claude Code、Codex、Cline 或 Roo Code 的开发者
- 想从“让 AI 帮我写几段代码”进化到“让 AI 真正参与工程流程”的实践者
- 正在思考 MCP、Skills、浏览器自动化、上下文系统该怎么组合的人

## 先判断你需要哪一类内容

| 你的当前问题 | 优先看什么 | 目标 |
|---|---|---|
| 我还分不清 Claude Code、Codex、Cline、Roo Code 的差异 | 第 1、3 部分 | 建立工具边界感 |
| 我已经在用某个工具，但输出不稳定 | 第 2、4 部分 | 学会通过配置、Skills、MCP 和上下文组织增强稳定性 |
| 我想让 Agent 真正参与项目协作 | 第 5 部分 | 从单点使用进入流程化协作 |
| 我担心在真实代码库里不可控 | 第 1、2、5 部分 | 先建立方法论，再看编排与 harness |

## 如果你有明确目标，建议这样读

### 想先选工具

按这个顺序读：

1. [Everything Claude Code：完整指南](/posts/tech/ai-agent/everything-claude-code-comprehensive-guide/)
2. [OpenAI Codex 轻量级 Coding Agent 指南](/posts/tech/openai-codex-lightweight-coding-agent/)
3. [Cline：AI Coding Agent 实战指南](/posts/tech/cline-ai-coding-agent-guide/)
4. [Roo Code：AI Coding Agent 使用指南](/posts/tech/roo-code-ai-coding-agent-guide/)

### 想提升已有工具的上限

按这个顺序读：

1. [Claude Code 最佳实践指南](/posts/tech/ai-agent/claude-code-best-practice-guide/)
2. [Claude Code 模板与配置指南](/posts/tech/claude-code-templates-configuration-guide/)
3. [Browserbase Skills：让 Claude Code 拥有浏览器自动化能力](/posts/tech/browserbase-skills-claude-code-browser-automation-guide/)
4. [CodeGraph：把 AI Coding Agent 的代码探索变成图查询](/posts/tech/codegraph-semantic-code-knowledge-graph-for-ai-coding-agents/)

### 想把 Coding Agent 用进真实项目

按这个顺序读：

1. [Treat Coding Agents Like Developers](/posts/tech/treat-coding-agents-like-developers/)
2. [How Claude Code Works in Large Codebases](/posts/tech/how-claude-code-works-in-large-codebases/)
3. [Chrome DevTools MCP 与 AI Coding Agents 使用指南](/posts/tech/chrome-devtools-mcp-ai-coding-agents-guide/)
4. [JCode：Coding Agent Harness 设计](/posts/tech/jcode-coding-agent-harness/)

## 推荐阅读顺序

### 1. 先建立整体认知

先理解 Coding Agent 和传统“AI 写代码”有什么不同，再进入具体工具，不然后面很容易陷入“换工具焦虑”。

1. [Treat Coding Agents Like Developers](/posts/tech/treat-coding-agents-like-developers/)
2. [How Claude Code Works in Large Codebases](/posts/tech/how-claude-code-works-in-large-codebases/)
3. [React Doctor：AI Coding Agent 如何理解前端代码](/posts/tech/react-doctor-ai-coding-agent/)

### 2. 从 Claude Code 进入主流工作流

Claude Code 相关内容在站内积累最深，适合作为主路径入口。先把它理解透，再横向比较其他工具会轻松很多。

1. [Everything Claude Code：完整指南](/posts/tech/ai-agent/everything-claude-code-comprehensive-guide/)
2. [Claude Code 最佳实践指南](/posts/tech/ai-agent/claude-code-best-practice-guide/)
3. [Claude Code 技能、插件与扩展能力指南](/posts/tech/ai-agent/claude-code-skills-agent-plugins-guide/)
4. [Claude Code 模板与配置指南](/posts/tech/claude-code-templates-configuration-guide/)

### 3. 再横向看其他 Coding Agent

这一阶段的重点不是“选唯一工具”，而是理解不同工具的交互方式、边界和适用场景。

1. [OpenAI Codex 轻量级 Coding Agent 指南](/posts/tech/openai-codex-lightweight-coding-agent/)
2. [Cline：AI Coding Agent 实战指南](/posts/tech/cline-ai-coding-agent-guide/)
3. [Roo Code：AI Coding Agent 使用指南](/posts/tech/roo-code-ai-coding-agent-guide/)
4. [DeepSeek TUI：终端 Coding Agent 指南](/posts/tech/deepseek-tui-terminal-coding-agent-guide/)

### 4. 把 Skills、MCP 和浏览器能力接进来

真正让 Coding Agent 变强的，往往不是“换了一个模型”，而是你有没有把工具调用、技能系统、浏览器环境和上下文组织好。

1. [Awesome Codex Skills：Codex Agent Skills 目录](/posts/tech/awesome-codex-skills-codex-agent-skills/)
2. [Browserbase Skills：让 Claude Code 拥有浏览器自动化能力](/posts/tech/browserbase-skills-claude-code-browser-automation-guide/)
3. [Chrome DevTools MCP 与 AI Coding Agents 使用指南](/posts/tech/chrome-devtools-mcp-ai-coding-agents-guide/)
4. [CodeGraph：把 AI Coding Agent 的代码探索变成图查询](/posts/tech/codegraph-semantic-code-knowledge-graph-for-ai-coding-agents/)

### 5. 进入更复杂的协作与编排

当单 Agent 已经能稳定完成一段工作后，才值得进一步看多 Agent、Harness、自动化例行任务和更长链路的编排。

1. [Ruflo：Claude Code 多 Agent Swarm 指南](/posts/tech/ruflo-claude-code-multi-agent-swarm-guide/)
2. [Claude Code Routines：自动化例行工作流](/posts/tech/claude-code-routines-automation/)
3. [JCode：Coding Agent Harness 设计](/posts/tech/jcode-coding-agent-harness/)
4. [Everything Claude Code Agent Harness Performance](/posts/tech/everything-claude-code-agent-harness-performance/)

## 如果你只想先看 6 篇

1. [Treat Coding Agents Like Developers](/posts/tech/treat-coding-agents-like-developers/)
2. [Everything Claude Code：完整指南](/posts/tech/ai-agent/everything-claude-code-comprehensive-guide/)
3. [Claude Code 最佳实践指南](/posts/tech/ai-agent/claude-code-best-practice-guide/)
4. [OpenAI Codex 轻量级 Coding Agent 指南](/posts/tech/openai-codex-lightweight-coding-agent/)
5. [Cline：AI Coding Agent 实战指南](/posts/tech/cline-ai-coding-agent-guide/)
6. [Chrome DevTools MCP 与 AI Coding Agents 使用指南](/posts/tech/chrome-devtools-mcp-ai-coding-agents-guide/)

## 这条路径背后的判断标准

我对 Coding Agent 内容的筛选标准主要是这四条：

- 能不能帮助你形成更稳定的工程工作流，而不只是展示一次性的 demo 效果
- 能不能解释工具边界、失败模式和协作方式，而不只是罗列功能
- 能不能和 Skills、MCP、浏览器自动化、上下文系统这些能力连接起来
- 能不能在真实代码库里持续复用，而不是只在小样例里成立

## 这条路径里最容易踩的 3 个误区

1. 把工具当成全部答案。真正影响结果的，常常不是换模型，而是上下文、技能系统、浏览器能力和验证流程。
2. 在没有方法论时横跳工具。工具比较重要，但先建立稳定工作流，比反复换工具更重要。
3. 只看“会不会生成代码”，不看“能不能验证、能不能持续协作”。这会直接决定它能不能进入真实项目。

后面如果站内继续积累更多 Claude Code、Codex、MCP 和 Coding Agent 相关文章，这个专题页会持续更新，逐步变成更完整的工作流索引。

## 下一步动作

如果你已经开始把 Coding Agent 用进真实项目，下一步建议这样走：

1. 返回 [AI Agent 学习路径](/ai-agent/)，把工具经验重新放回更完整的系统图景
2. 进入 [开源 AI 工具解读](/open-source-ai-tools/)，建立你自己的长期工具栈判断框架
3. 如果你想交流具体工作流、内容合作或产品合作，可以直接查看 [联系页面](/contact/)
