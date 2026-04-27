---
title: "tech 根目录剩余平铺文章归类决策清单"
date: 2026-04-02T11:30:00+08:00
draft: false
tags: ["Hugo", "内容治理", "迁移规划", "信息架构", "技术笔记"]
categories: ["系统基建"]
---

> **🎯 学习目标**
>
> 读完本文，你将了解：
>
> 1. `content/posts/tech/` 根目录剩余平铺文章接下来该如何处理。
> 2. 哪些文章建议迁入 `ai-agent`、`tools`、`quant`。
> 3. 哪些文章更适合继续平铺，而不是强行塞进子目录。
> 4. 后续迁移时应该优先执行什么顺序。

本文档用于承接前几轮真实迁移后的剩余决策工作。目标不是把所有文章都机械地塞进子目录，而是对仍然留在 `tech` 根目录的文章做一次**语义优先、收益优先、风险最小**的归类判断。

---

## 1. 当前前提

截至当前阶段，`tech` 目录的稳定子域只保留 4 个：

- `ai-agent`
- `llm`
- `tools`
- `quant`

其中：

- `Claude` 直接相关内容统一归入 `ai-agent`
- BI、OCR、结构化处理、通用开发工具优先归入 `tools`
- 量化研究、金融数据平台、交易系统优先归入 `quant`
- 跨域综述、资源集合、学习笔记类内容允许继续平铺

因此这份决策清单的核心问题不再是“有没有目录可放”，而是：**现在还值得继续迁什么，哪些不值得动。**

---

## 2. 总体判断

对当前剩余平铺文章而言，最有价值的后续动作不是继续扩目录，而是继续压缩高确定性的 `ai-agent` 散点内容，其次补 `tools`，而 `quant` 应保持克制。

| 方向 | 当前建议 | 原因 |
| --- | --- | --- |
| `ai-agent` | 第一优先 | 剩余高确定性文章最多，聚合收益最高 |
| `tools` | 第二优先 | 仍有一批工具型文章可稳定收拢 |
| `quant` | 保守推进 | 剩余平铺文中高置信候选已经不多 |
| 继续平铺 | 必须保留 | 泛综述、学习笔记、资源型文章不适合硬迁 |

一句话结论：**剩余平铺文章的最高回报动作，是继续收缩 `ai-agent` 散点，再补 `tools`，而不是为了目录完整度继续硬塞 `quant`。**

---

## 3. 建议继续迁入 `ai-agent`

以下文章建议作为下一批优先迁入 `tech/ai-agent/`。

| 当前文件 | 建议 | 原因 |
| --- | --- | --- |
| `astrbot-open-source-ai-chatbot-platform-guide.md` | 迁入 `ai-agent` | 明确是 Agent 聊天机器人平台 |
| `shanclaw-ai-agent-cli-guide.md` | 迁入 `ai-agent` | 虽有 CLI 属性，但核心是 AI Agent CLI |
| `xiaohongshu-mcp-xiaohongshu-model-context-protocol-guide.md` | 迁入 `ai-agent` | 直接服务 Claude Code / Cursor / OpenClaw 的 MCP 能力 |
| `baoyu-skills-ai-agent-guide.md` | 迁入 `ai-agent` | 主体是 AI Agent 技能体系 |
| `supermemory-ai-memory-context-engine.md` | 迁入 `ai-agent` | Agent 记忆与上下文引擎主题明确 |
| `onyx-ai-platform-guide.md` | 迁入 `ai-agent` | 更像 Agent 平台与企业知识系统 |
| `smux-tmux-ai-agent-setup.md` | 倾向迁入 `ai-agent` | 工具外形明显，但核心场景绑定 Agent 工作流 |
| `cmux-ai-terminal-multiplexer.md` | 倾向迁入 `ai-agent` | 与 Agent / AI 终端工作流强绑定 |
| `slavingia-skills-series-guide.md` | 倾向迁入 `ai-agent` | 主题是 skills 与 Agent 方法体系 |
| `general-agent-competition-task-delivery-analysis.md` | 可迁入 `ai-agent` | 更像 Agent 专题分析，聚合价值高于继续平铺 |

这批文章的共同特点是：**读者点进来，本质上是为了了解 Agent 能力、Agent 平台、Agent 工作流，而不是为了看某个孤立工具。**

---

## 4. 建议继续迁入 `tools`

以下文章更适合进入 `tech/tools/`。

| 当前文件 | 建议 | 原因 |
| --- | --- | --- |
| `ghost-headless-cms-expert-guide.md` | 迁入 `tools` | Headless CMS 平台，工具心智稳定 |
| `twenty-open-source-crm-guide.md` | 迁入 `tools` | CRM 平台，更像业务工具而非 AI 主体 |
| `clawmanager-kubernetes-desktop-management.md` | 迁入 `tools` | Kubernetes 桌面管理平面，基础设施工具属性强 |
| `free-for-dev-developer-resources-guide.md` | 迁入 `tools` | 开发者资源与工具箱内容，适合工具聚合 |
| `project-nomad-offline-ai-server.md` | 倾向迁入 `tools` | 离线 AI 服务器平台，更像工具基础设施 |

这里的原则是：**只要文章的主心智是“软件工具 / 平台 / 管理面 / 资源库”，即使有 AI 成分，也优先放进 `tools`。**

---

## 5. `quant` 当前建议保守推进

目前剩余平铺文章中，真正高置信、且值得立即迁入 `quant` 的文章已经很少。

以下文章暂时不建议强迁：

| 当前文件 | 当前建议 | 原因 |
| --- | --- | --- |
| `taxhacker-self-hosted-ai-accounting-guide.md` | 继续观察 | 更像财务 / 税务管理，不是量化研究平台 |
| `worldmonitor-geopolitical-monitoring-system-guide.md` | 继续平铺 | 偏监控与分析，不是交易或投研平台 |
| `echo-ai-prediction-future.md` | 继续平铺 | 更像预测基础设施与研究分析 |
| `mirofish-swarm-intelligence-prediction.md` | 继续平铺 | 预测系统属性强，但量化交易心智不足 |

这里的判断非常简单：**如果它不是在讲量化研究、金融数据平台、股票研究系统或交易实验平台，就不要为了凑目录硬归到 `quant`。**

---

## 6. 明确建议继续平铺

以下类型建议继续保留在 `tech` 根目录平铺：

### 6.1 跨域综述

- `ai-advanced-technology-learning-notes-2026-03.md`
- `ai-security-technical-learning-notes.md`

原因：同时覆盖多个主题域，本身不是目录化承接对象。

### 6.2 泛资源与课程

- `papers-we-love-cs-papers-community.md`
- `coding-interview-university-guide.md`
- `freecodecamp-open-source-curriculum-guide.md`

原因：资源集合或课程导读，更适合继续平铺并依赖标签聚合。

### 6.3 入门型通识教程

- `simple-ml-code-machine-learning-tutorial.md`

原因：更像通识型学习内容，而不是某个稳定子域下的系列文章。

---

## 7. 推荐执行顺序

如果继续推进下一阶段迁移，建议顺序如下：

1. 先迁入高确定性的 `ai-agent` 文章
2. 再迁入高确定性的 `tools` 文章
3. `quant` 仅保留“明确金融研究 / 股票分析 / 量化平台”标准
4. 综述、资源、课程、通识教程继续平铺

这样做的好处是：

- 目录增长仍然可控
- 每次迁移都能提升聚合质量
- 不会因为追求完整度而破坏语义边界

---

## 8. 一句话结论

剩余平铺文章不需要追求“全部迁完”。更合理的做法是：**把高确定性的 Agent 文章继续收进 `ai-agent`，把稳定工具文章继续收进 `tools`，让 `quant` 保持克制，其余内容继续平铺。**
