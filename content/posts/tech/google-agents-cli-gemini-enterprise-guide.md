---
title: "google/agents-cli：让任意编程助手变成 Gemini Enterprise Agent 部署专家的 CLI 技能套件"
date: "2026-06-30T21:10:22+08:00"
slug: "google-agents-cli-gemini-enterprise-guide"
description: "google/agents-cli 是 Google 官方发布的 CLI + Skills 套件，让 Antigravity CLI、Claude Code、Codex 等任意编程助手具备在 Gemini Enterprise Agent Platform 上创建、评估、部署 AI 代理的能力。本文拆解其定位、Skill 设计、CLI 命令族与典型工作流。"
draft: false
categories: ["技术笔记"]
tags: ["Google Cloud", "Gemini", "Agent", "CLI", "Claude Code", "Codex"]
---

# google/agents-cli：让任意编程助手变成 Gemini Enterprise Agent 部署专家的 CLI 技能套件

## 这篇文章解决什么问题

2026 年的 AI 代理开发有一个真实痛点：搭建一个能在 Google Cloud 上跑起来的 ADK（Agent Development Kit）代理，需要熟悉至少 5 套不同的命令（adk scaffold、Agent Engine、Cloud Run、GKE、Cloud Build）、评估指标（trace、grade、analyze）、发布流程（Gemini Enterprise 注册）。光是把这些工具"知道"就要几天时间。

google/agents-cli 的解决方案是：**给任意编程助手装一组 Skill，让它替你调用这些命令**。你用 Claude Code 或 Codex 时说"用 agents-cli 帮我搭一个压缩文本的代理"，编程助手直接调 agents-cli 的对应命令，不需要你记具体哪个 gcloud 子命令。

读完后你能：

1. 看清 agents-cli 在 Google Cloud agent 工具链中的位置（补充 ADK 的工程化层）
2. 知道 7 个 Skill 各自负责什么，能解决哪些具体问题
3. 理解 agents-cli 与 Antigravity CLI / Claude Code / Codex 的边界——它不是替代品，是装在它们身上的工具集
4. 在自己的项目里评估接入 agents-cli 的成本

## 项目基本事实

| 指标 | 数值 |
|---|---|
| 仓库 | [google/agents-cli](https://github.com/google/agents-cli) |
| Stars / Forks | 3.8k / 437 |
| 语言 | Python |
| License | Apache-2.0 |
| 状态 | Preview（Pre-GA） |
| 文档 | https://google.github.io/agents-cli/ |
| 首次提交 | 2026-04-08 |

仓库 2026 年 4 月才创建，半年内积累近 4k Stars。它跟 ADK（[google/adk-python](https://github.com/google/adk-python)）是姐妹项目——ADK 是 agent framework，agents-cli 是给编程助手用的部署工具集。

## 核心定位澄清

agents-cli **不是**：

- 替代 Antigravity CLI / Claude Code / Codex 的新代理
- ADK 的替代品——它是 ADK 之上的工程化层
- 一个只能在 Google Cloud 内部用的封闭工具——Apache-2.0 协议开源

agents-cli **是**：

- 装在编程助手身上的一组 Skill + CLI 工具
- 把 ADK + Cloud Run + GKE + Agent Engine + Cloud Build + 评估管道 串起来的"工具箱"
- 让 Claude Code / Codex 等通用编程助手在 Google Cloud agent 场景下达到"专业"水准的增强层

## 7 个 Skill

agents-cli 提供 7 个 Skill，每个 Skill 是一组结构化指令集，让编程助手知道怎么调对应命令：

| Skill | 编程助手学到什么 |
|---|---|
| `google-agents-cli-workflow` | 开发生命周期、代码保留规则、模型选择策略 |
| `google-agents-cli-adk-code` | ADK Python API（agents、tools、orchestration、callbacks、state） |
| `google-agents-cli-scaffold` | 项目脚手架（create、enhance、upgrade） |
| `google-agents-cli-eval` | 评估方法论（metrics、datasets、LLM-as-judge、adaptive rubrics） |
| `google-agents-cli-deploy` | 部署（Agent Runtime、Cloud Run、GKE、CI/CD、secrets） |
| `google-agents-cli-publish` | Gemini Enterprise 注册 |
| `google-agents-cli-observability` | 观测（Cloud Trace、logging、第三方集成） |

这 7 个 Skill 对应 agent 从立项到上线的完整生命周期。**单独使用任何一个 Skill 都有意义**（比如只想做 eval 不做 deploy），但完整使用 7 个 Skill 才能发挥 agents-cli 的最大价值。

## 安装

agents-cli 提供两种安装方式，分别对应"完整安装"和"只装 Skill"：

```bash
# 完整安装（CLI + Skill）
uvx google-agents-cli setup

# 只装 Skill 到编程助手
npx skills add google/agents-cli
```

后者只装 Skill 不装 CLI——适合只需要让编程助手知道怎么调命令、但自己手动跑命令的场景。前者两者都装。

环境要求：Python 3.11+、`uv`（包管理工具）、Node.js。

## 典型命令族

CLI 命令按 agent 生命周期分四组：

### Scaffold 组

```bash
agents-cli scaffold <name>              # 创建新 agent 项目
agents-cli scaffold enhance             # 给已有项目加 deploy / CI/CD / RAG
agents-cli scaffold upgrade             # 升级项目到新版 agents-cli
```

### Develop 组

```bash
agents-cli run "prompt"                 # 单 prompt 运行 agent
agents-cli install                     # 安装项目依赖
agents-cli lint                        # 代码质量检查（Ruff）
```

### Evaluate 组

```bash
agents-cli eval generate                # 在 eval 数据集上跑 agent，生成 traces
agents-cli eval grade                   # 给 traces 打分
agents-cli eval dataset synthesize      # 合成多轮 eval 场景
agents-cli eval compare                 # 对比两次 eval 结果
agents-cli eval analyze                 # 聚类失败模式
agents-cli eval metric list             # 列出可用 metrics
agents-cli eval optimize                # 用 eval 数据自动调优 prompt
```

### Deploy & Publish 组

```bash
agents-cli deploy                      # 部署到 Google Cloud
agents-cli publish gemini-enterprise    # 注册到 Gemini Enterprise
agents-cli infra single-project        # 单项目基础设施
agents-cli infra cicd                   # CI/CD pipeline + staging/prod 基础设施
```

### Data 组

```bash
agents-cli infra datastore              # RAG datastore 基础设施
agents-cli data-ingestion               # 数据导入管道
```

## 典型工作流

### 从零搭一个 agent

```bash
# 1. 用编程助手（Claude Code / Codex / Antigravity CLI）启动
# 2. 让编程助手跑：
uvx google-agents-cli setup

# 3. 编程助手问"帮我搭一个 caveman 风格的压缩 agent"
#    → 编程助手调 agents-cli scaffold <name>
#    → 生成项目骨架

# 4. 编程助手根据 adk-code Skill 写 agent 代码
#    → 用 ADK API 实现 caveman 压缩逻辑

# 5. 跑 eval
agents-cli eval generate
agents-cli eval grade

# 6. 部署
agents-cli deploy
agents-cli publish gemini-enterprise
```

整个流程不需要你记具体命令——编程助手通过 Skill 知道该调什么。

### 给已有项目加 RAG + 部署

```bash
# 在已有项目里跑
agents-cli scaffold enhance
# 编程助手根据 scaffold Skill 问你：要加 deploy / CI/CD / RAG？
# 选 RAG → 自动生成 datastore 配置 + 数据导入管道
```

### 跑一次 A/B eval

```bash
agents-cli eval generate
# 修改 prompt
agents-cli eval generate
agents-cli eval compare
# 看两次 eval 的差异
```

## 与其他工具的边界

| 工具 | 关系 |
|---|---|
| ADK (google/adk-python) | agents-cli 在 ADK 之上，ADK 是 framework，agents-cli 是工程化 |
| Antigravity CLI / Claude Code / Codex | agents-cli 不是替代品，是装在它们身上的 Skill + CLI 工具 |
| Vertex AI Agent Engine | agents-cli 的 deploy 命令之一指向 Agent Engine |
| gcloud CLI | agents-cli 调用 gcloud 但封装了一组预定义场景，不需要你直接写 gcloud 命令 |
| LangChain / LlamaIndex | agents-cli 不绑定到任何 agent framework（但 Skill 里默认 ADK） |

## 工程取舍

**优势**：

- 把 Google Cloud agent 工程化的复杂度（多服务、多命令、多配置）压缩成一句话
- 7 个 Skill 覆盖完整生命周期，不需要在不同工具之间切换
- Apache-2.0 协议 + 开源 Skill，可定制
- 编程助手友好设计——Skill 输出结构化、命令路径稳定

**劣势**：

- Preview 状态，API 可能有 breaking change
- 紧耦合 ADK——如果你的 agent 用 LangChain 或其他 framework，Skill 价值会打折
- Google Cloud 锁定——虽然 CLI 开源，但 deploy / publish 命令几乎全部指向 GCP 服务
- Skill 套件的学习曲线——7 个 Skill 各自的适用场景需要花时间理解

## 适用边界

**适合**：

- 在 Google Cloud 上部署 AI agent，且愿意用 ADK 作为框架
- 用 Claude Code / Codex 等编程助手做主力开发，期望编程助手能直接处理 GCP 部署
- 团队里有多个 agent 项目，需要统一的脚手架、eval、部署流程
- 想把 GCP agent 工程化的最佳实践（CI/CD、observability、eval）一次性带到项目里

**不适合**：

- 不打算用 Google Cloud 的项目——deploy / publish 命令几乎全部指向 GCP
- 不使用 ADK 的项目——Skill 默认假设 ADK，迁移成本高
- 已有完整 agent 部署流程的成熟项目——agents-cli 主要解决"从零到一"的问题
- 完全不想用编程助手的开发者——CLI 命令本身可以独立用，但 7 个 Skill 的价值会打折

## 阅读路径

1. 在自己环境跑 `uvx google-agents-cli setup`，看默认配置下的命令清单
2. 用 `agents-cli scaffold <name>` 创建一个最小 demo agent
3. 用 `agents-cli eval generate` 跑一次 eval，看 trace 输出
4. 把编程助手（Claude Code 或 Codex）的 base URL 配好，让它读 agents-cli Skill
5. 让编程助手帮你写一个 RAG agent，从 scaffold 到 deploy 走完整流程
6. 评估 deploy 后的运行成本和观测粒度，决定是否在生产项目里采用

agents-cli 是 Google 在"AI 代理工业化"方向上的一次明确投入——7 个 Skill 的覆盖度、Skill 设计的工程深度、文档的完整度都表明这不是临时项目。但 Preview 状态意味着现在接入需要为后续 API 变化预留缓冲。