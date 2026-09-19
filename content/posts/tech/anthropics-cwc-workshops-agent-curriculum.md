---
title: "cwc-workshops：Anthropic 的 Code with Claude 工作坊资料集"
date: 2026-07-20T03:02:36+08:00
categories: ["技术笔记"]
tags: ["Anthropic", "Claude", "AI Agent", "MCP"]
description: "cwc-workshops 是 Anthropic 官方 Code with Claude 工作坊的材料合集，9 个 workshop 覆盖模型选型、agent 分解、Managed Agents、记忆、评测驱动开发，每个都是 Anthropic 团队跑过的实操课。"
slug: anthropics-cwc-workshops-agent-curriculum
github_repo: "anthropics/cwc-workshops"
source_key: "gh:anthropics/cwc-workshops"

---

# cwc-workshops：Anthropic 的 Code with Claude 工作坊资料集

## 一句话判断

cwc-workshops 不是"教程合集"，而是 Anthropic 自己跑过的实操工作坊原始材料——9 个 workshop 各对应一场 Code with Claude 现场课，配源码、配置和走查笔记。它最适合想看"Anthropic 内部怎么用 Claude Managed Agents、Skills、MCP 组织 agent 系统"的人：不是听结论，而是把他们现场跑过的路径自己再跑一遍。

## 项目定位

- **仓库**：`anthropics/cwc-workshops`，Apache-2.0 协议，TypeScript 为主、Python 次之，另有 JavaScript、Shell 和 HTML
- **GitHub Stars**：2106，Forks 623（2026-09-19 数据）
- **时间线**：2026 年 5 月 6 日建仓，最后一次推送停在 2026 年 8 月 27 日
- **状态**：README 原话是 "Workshop materials. Not maintained and not accepting contributions."——工作坊跑完归档的原始材料，不再维护，但也不删
- **内容载体**：每个 workshop 一个子目录，含完整源码、数据和配置

## 9 个 Workshop 全景

| 目录 | 主轴 | 你实际动手的部分 |
|------|------|------------------|
| `rightmodel/` | Picking the Right Model | 用一个 Claude Code SKILL 先审计评测套件的健康度，再做 model × thinking × effort 网格扫描，找质量/成本/延迟的最优配置 |
| `agent-decomposition/` | Compose Multi-Agent Systems with Skills and MCP | 把一个 402 行系统 prompt、12 个工具、3 个硬编码 subagent 的库存 agent 拆解重组，每改一步跑一次 eval |
| `how-we-claude-code/` | How We Claude Code | 三阶段走完 AI 辅助产品流程：访谈成 spec、四份分歧设计稿、可运行时验证的 Vite + React 应用 |
| `ship-your-first-managed-agent/` | Ship Your First Managed Agent | 在 Streamlit 事故面板旁补齐 7 个函数（约 38 行），把离线的 SRE Agent 接上线 |
| `agent-battle/` | Agent Battle | 45 分钟竞赛：配置 Managed Agent 驱动本地游戏 bot，钻石最多者胜，token 最少者破平 |
| `agents-that-remember/` | Agents That Remember | 从跨会话失忆的 agent 出发，逐层加 memory store 和 Dreaming Service，45 分钟"从金鱼到同事" |
| `eval-driven-agent-development/` | Eval-Driven Agent Development | 迭代一个 PPTX 生成 agent，5 个任务、双层 grader，每次改 prompt 都量化对比 |
| `production-ready-agent/` | Production-Ready Agent | Deal Desk：M&A 研究多 agent 团队，协调者调度 4 个并行研究 sub-agent，产出带评分的投资论点 |
| `research-desk/` | The Research Desk | SEC 财报研究台：head of research 按 ticker 派出分析师会话，edgartools 读 filings，scorecard 出评 |

每个 workshop 都遵循同一个模板：

1. **目标**：用 1-2 句话讲清楚这个 workshop 解决什么问题
2. **场景**：模拟一个真实业务 / 工程场景
3. **材料**：完整可运行的代码 + 数据集 + 配置文件
4. **演进路径**：从最 naive 的实现逐步迭代到 production-grade
5. **评测**：每一版改动都有对应的 eval 任务，能跑出量化对比

## 关键机制拆解

### 1. Managed Agents：7/9 个 workshop 的地基

9 个 workshop 里，除 `rightmodel/`（Claude Code + SKILL）和 `how-we-claude-code/`（prompt 工程与前端验证）外，其余 7 个都建在 Claude Managed Agents 上——Anthropic 的托管 agent 运行时，2026 年仍处 research preview 阶段（`agents-that-remember/` 要求组织先加入 preview，`research-desk/` 的 Deployments 功能也标注 research preview）。

它的资源模型有四层，`ship-your-first-managed-agent/` 的 README 按此排序教学：

- **Agent**：定义系统 prompt、技能、工具的配置实体，支持版本化更新
- **Environment**：云上沙箱容器，预装运行时并可限制网络出口
- **Session**：一次有状态的对话运行，可列举、可恢复
- **Events**：会话内的事件流，工具调用、消息、确认都走这条流

四层各自的分工在 workshop 里反复出现：agent 定"谁在干活"，environment 定"在哪干"，session 存"干到哪了"，events 记"每一步发生了什么"。Skills 和 MCP 挂在 agent 配置上：SKILL.md 把领域知识编码成可加载的指令，MCP server 把外部工具接进来。理解这四层，剩下 7 个 workshop 的代码结构基本可以预测。

### 2. 一个任务如何流过系统：Incident-2277

`ship-your-first-managed-agent/` 把整套机制装进了一个事故场景：凌晨两点 PagerDuty 响了，checkout 服务 p99 延迟涨到基线的 10 倍。你要做的是把面板旁边那个离线的 SRE Agent 接上线——`agent.py` 里 7 个函数，全部 `raise NotImplementedError`，填完约 38 行：

| # | 函数 | 对接的 API |
|---|------|-----------|
| 1 | `setup_agent()` | `skills.create` + `agents.create` |
| 2 | `setup_environment()` | `environments.create` |
| 3 | `upload_log()` | `files.upload` |
| 4 | `start_session()` | `sessions.create` |
| 5 | `stream_reply()` | `sessions.events.stream` + `.send` |
| 6 | `handle_tool()` | 本地执行，读 `data/*.json` |
| 7 | `delete_session()` | `sessions.delete` |

上线后问它"延迟尖峰是什么引起的"，看它干活：在云端沙箱里 grep 一份 7 万行的 JSON 日志，通过事件流回调你机器上的 `get_metrics`、`get_recent_deploys`、`get_diff` 三个本地工具，把日志、指标、部署记录、diff 四份证据的时间戳对齐，最后点名 commit `a3f9c21`——14:31:18 UTC 上线，把批量查询改成了逐行循环，p99 从 65 ms 爬到 3600 ms，数据库连接池饱和，20% 的结账请求开始失败。

这个案例之所以值得细看，在于它把"云端 agent + 本地工具"的分工演透了：重活在托管沙箱里跑，敏感数据和私有接口留在自己机器上，`handle_tool()` 的 README 注释写着——these handlers run on **your** machine, not the cloud — that's the point。把 mock JSON 换成 Datadog 客户端，这就是生产系统。

### 3. eval 是贯穿全仓库的第二条主线

"怎么证明你的 agent 变好了"是每个 workshop 都在回答的问题，答案因产物形态而异：

- **rightmodel**：分两步。先审计（audit）——按任务设计、harness 设计、指标卫生、grader 设计（含 LLM 评审的偏见）四类检查清单排查评测套件自身的可靠性；再扫描（sweep）——把评测包进 model × thinking × effort 的网格，逐格记录 pass rate、成本、延迟，产出三张对比图加一句话推荐。没有现成评测的读者可以用 Sierra 的 tau2-bench（airline 域）替代，50 个任务里取按 Haiku 基线通过率分层的 20 个子集
- **eval-driven-agent-development**：PPTX 生成 agent 配双层 grader——程序化评分直接解析 `.pptx` 的 XML 结构指标，LLM-as-judge 在本地 Docker 里用 LibreOffice 把幻灯片渲染成 JPG 后评审视觉效果。5 个任务（求职、环境、面包、社媒、科普各一个 5 页 deck），仓库提供起点 `agent.yaml` 加 `solutions/` 里 4 个进阶配置（polish、diagram、qa-loop、model-swap），`--baseline` 记录基线分，之后每次运行都显示与基线的差值
- **production-ready-agent / research-desk**：用 outcome rubric——运行时通过 `user.define_outcome` 定义"什么算合格"，每个分析产出对照评分卡（scorecard）打分

值得一提：仓库主 README 称 eval workshop 是 "six variants / 10-task suite"，但仓库实际文件是 5 个任务、起点配置加 4 个 solution——引用时以文件为准。这类出入本身就是归档材料的典型风险。

### 4. 真实业务场景，不是 toy example

- `production-ready-agent/` 模拟 Deal Desk：M&A 研究团队，协调者并行调度 4 个研究 sub-agent，从 memory store 读过往交易的教训，经 MCP 连 Linear，产出带评分的投资论点。UI 流式展示每个事件，受控工具调用需要人工确认，还能点进每个 sub-agent 的会话线程
- `research-desk/` 模拟 SEC 财报研究台：head of research 通过自定义工具 `dispatch_analysts` 按 ticker 派出分析师会话，每个分析师再带财务提取和风险分析两个专家 sub-agent；云环境限制网络出口只能访问 SEC 和包管理源，凭证全部由服务端解析，浏览器永不接触 key。长期部署形态是定时任务每周生成研究备忘录
- `ship-your-first-managed-agent/` 模拟 SRE 事故响应

场景数据都是虚构的（Deal Desk 的 README 明说 "All companies and financials are fictitious"），但工作形态是真的：并行调度、记忆复用、人工确认门、评分产出，这些正是企业 agent 落地要过的坎。

### 5. 归档材料的正确用法

README 明确说 "not maintained"，2026 年 8 月底之后大概率不会再有修正。这意味着：

- **代码可能用旧版本 SDK**：仓库里的配置写死了当时的模型（如 eval workshop 的 `agent.yaml` 用 `claude-sonnet-4-6`），跑不通时要自己换成当前可用的模型
- **平台功能在快速演进**：Managed Agents 处于 research preview，API 面会变，workshop 代码与最新文档有出入时以文档为准
- **但设计思想不过时**：四层资源模型、双层 grader、outcome 评分、云端执行与本地工具的分工，这些模式在 Anthropic 自己的文档里也一直是主线

对学习者来说，关键是理解每个 workshop 的设计意图，而不是逐行复用代码。引用仓库数字时也要留意——主 README 与实际文件偶有出入（见上文 eval 一节），以文件为准。

## 环境与前置条件

9 个 workshop 的依赖差异不小，动手前先对表：

| Workshop | 运行时 | 额外依赖 | 特殊要求 |
|----------|--------|----------|----------|
| `rightmodel/` | Claude Code | Anthropic API key | 方案 B 需 Python 3.12 或 3.13 |
| `agent-decomposition/` | Python | uv | — |
| `how-we-claude-code/` | bun（阶段 3） | — | 阶段 1/2 只需读 prompt 文件 |
| `ship-your-first-managed-agent/` | Python 3.10+ | Anthropic API key | — |
| `agent-battle/` | Python | Anthropic API key | 多人赛需主持人按 HOST.md 组织 |
| `agents-that-remember/` | Shell | Anthropic API key | 组织需加入 research preview |
| `eval-driven-agent-development/` | Node.js 22+ | ant CLI ≥1.6.0、Docker | grader 的渲染步骤跑本地容器 |
| `production-ready-agent/` | Node.js（bun） | ant CLI、jq | API key 需开通 Managed Agents beta |
| `research-desk/` | Node.js 22+ | EDGAR_IDENTITY | 长驻进程，不面向 serverless 托管 |

`ant` CLI 是 Managed Agents 的命令行入口（`brew install anthropics/tap/ant`），`eval-driven-agent-development/`、`production-ready-agent/` 和 `agents-that-remember/` 都靠它创建环境和 agent。前置门槛有两档：多数 workshop 用普通 Anthropic API key 就能跑；`production-ready-agent/` 和 `research-desk/` 要求开通 Managed Agents 权限的 key；`agents-that-remember/` 还要组织先加入 research preview——没有资格就先跳过，不影响其余八个。

## 适用人群

- **AI 工程师**：想看 Anthropic 内部怎么用 Managed Agents + Skills + MCP 组织 agent 系统
- **Agent 架构师**：想学 eval 驱动开发的方法论，从审计清单到双层 grader 都有可抄的作业
- **教育者**：想在公司或高校内部跑类似 workshop 的人，`agent-battle/` 连主持人手册都备好了
- **产品经理**：想理解 agent 技术的边界和落地形态，Deal Desk 和 Research Desk 就是两个活样例

## 不适合谁

- **零基础 AI 学习者**：workshop 默认你已经会用 Claude Code、理解 MCP
- **期待长期维护的人**：README 明确 "not maintained"，SDK 和模型 id 要自己适配
- **只想看"如何用 Claude 写代码"的人**：9 个里只有 `rightmodel/` 和 `how-we-claude-code/` 涉及 Claude Code 本身，其余主线是 Managed Agents

## 仓库地址

https://github.com/anthropics/cwc-workshops

## 阅读路径建议

1. **先跑 `ship-your-first-managed-agent/`**：7 个函数、38 行代码，成本最低，还能一次建全 Agent → Environment → Session → Events 的完整心智模型
2. **再按兴趣分叉**：关心质量保障就跑 `eval-driven-agent-development/` 加 `rightmodel/`；关心跨会话记忆就跑 `agents-that-remember/`；关心多 agent 编排就按 `agent-decomposition/` → `production-ready-agent/` → `research-desk/` 的顺序推进，复杂度递增
3. **带团队一起学就用 `agent-battle/`**：45 分钟竞赛自带计分规则和主持人手册，当团建加培训都合适
4. **每个 workshop 的读法**：先读 README（部分带 WORKSHOP.md）理解设计意图，跑通源码，最后跑 eval 看各版本之间的量化差距——差距怎么来的，就是这场工作坊要教的东西
