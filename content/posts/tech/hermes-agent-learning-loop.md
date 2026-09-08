---
title: "Hermes Agent：自带学习闭环的自我进化智能体"
date: 2026-09-09T03:50:00+08:00
slug: "hermes-agent-learning-loop"
github_repo: "NousResearch/hermes-agent"
source_key: "gh:NousResearch/hermes-agent"
description: "Hermes Agent 是 Nous Research 开源的自进化 AI 智能体，核心特色是内建学习闭环：从经验自动创建技能、使用中自我改进、跨会话检索历史对话并持续深化对用户的理解。本文解析其学习闭环机制、多平台网关架构与部署形态。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Hermes", "自我改进", "开源智能体", "Nous Research"]
---

# Hermes Agent：自带学习闭环的自我进化智能体

## 先给判断

大部分 AI 智能体框架的卖点是"能调用更多工具"，Hermes Agent 的卖点不一样：**它是目前少数把学习闭环做进产品本体的开源智能体**——从经验中自动沉淀技能（skills）、技能在使用中自我改进、定期提醒自己持久化知识、能检索自己的历史会话、并跨会话逐步建立对用户的理解。这个定位来自 Nous Research（README 原话："The self-improving AI agent"），24 万+ Stars 的社区热度说明它踩中了"智能体越用越懂你"这个真实需求。

第二个关键判断：**它不绑定你的笔记本**。单一网关进程同时接入 Telegram、Discord、Slack、WhatsApp、Signal 和 CLI，执行环境可以放在 5 美元的 VPS、GPU 集群或闲时几乎零成本的 serverless 沙箱上——你在手机上发消息，它在云上干活。

## 系统地图：六个子系统怎么咬合

| 子系统 | 职责 | 关键机制 |
|---|---|---|
| 学习闭环 | 经验 → 技能 → 改进 | 复杂任务后自主创建技能；使用中自我改进；周期性提醒持久化知识；兼容 agentskills.io 开放标准 |
| 记忆 | 跨会话连续性 | 智能体自主策展的记忆 + FTS5 全文检索历史会话 + LLM 摘要召回；Honcho 辩证式用户建模 |
| 消息网关 | 多平台接入 | 单进程覆盖 Telegram/Discord/Slack/WhatsApp/Signal/Email；语音转写；跨平台对话延续 |
| 调度 | 无人值守自动化 | 内建 cron 调度器，自然语言定义日报/备份/审计，结果投递到任意平台 |
| 并行 | 任务分身 | 派生隔离子代理（subagents）处理并行工作流；Python 脚本经 RPC 调用工具，把多步管道折叠成零上下文开销的单轮 |
| 执行后端 | 跑在哪 | 七种终端后端：本地、Docker、SSH、Singularity、Modal、Daytona、Vercel Sandbox；Modal/Daytona 支持 serverless 休眠 |

模型层完全开放：Nous Portal、OpenRouter、OpenAI、自建端点均可，`hermes model` 一条命令切换，无锁定。

## 学习闭环拆解：它和普通 Agent 框架差在哪

这是全文最值得慢看的部分。传统智能体每次会话都是白纸；Hermes 的闭环有四个咬合点：

1. **技能自创建**：完成复杂任务后，智能体把过程中验证有效的做法提炼成技能文件，下次直接复用而非从头摸索。
2. **技能自改进**：技能不是写完就冻结——使用中发现更好的做法会回写进技能本身。
3. **持久化提醒（nudges）**：智能体会被周期性提醒把重要上下文写进记忆，对抗"聊完就忘"。
4. **历史检索**：FTS5 索引全部会话，配合 LLM 摘要做跨会话召回——"我们上个月讨论过的那个方案"是真能查到的。

再加一层 Honcho 用户建模：随着交互累积，智能体对"你是谁、你怎么做事"的理解逐次加深。这套组合在开源智能体里相当少见。

## 快速上手

### 安装（Linux / macOS / WSL2 / Termux）

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

### 安装（Windows 原生 PowerShell）

```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

安装器自带 uv、Python 3.11、Node.js、ripgrep、ffmpeg 和便携版 Git Bash（MinGit，装在 `%LOCALAPPDATA%\hermes\git`，不动系统 Git，无需管理员权限）。

### 启动

```bash
source ~/.bashrc    # 重载 shell
hermes              # 进入终端对话
```

常用命令一览：

```bash
hermes              # 交互式 CLI
hermes model        # 选模型供应商
hermes tools        # 配置工具开关
hermes gateway      # 启动消息网关（Telegram、Discord 等）
hermes setup        # 全套设置向导
hermes claw migrate # 从 OpenClaw 迁移（设置/记忆/技能/API key）
hermes doctor       # 自检
```

### 跳过攒 API key：Nous Portal

不想为模型、搜索、画图、TTS、云浏览器各办一个 key 的话，`hermes setup --portal` 一条命令走 OAuth 登录 Nous Portal：300+ 模型 + 全套工具网关（Firecrawl 搜索、FAL 画图、OpenAI TTS、Browser Use 云浏览器）打包在一个订阅里。各工具仍可换回自己的 key，网关按后端粒度开关，不是全有或全无。

## 任务流案例：Telegram 上的一次夜间任务

串一个具体场景看子系统怎么协作：

1. 白天你在 Telegram 对 Hermes 说："每晚 11 点跑一次网站健康检查，异常就告诉我。"
2. **调度系统**登记一条 cron 任务，自然语言即配置。
3. 到点后任务在云上后端（比如 Modal）唤醒执行——闲时环境休眠，几乎零成本。
4. 检查发现某接口 5xx 飙升，智能体**派生子代理**并行抓取日志、复现请求、定位到具体提交。
5. 结果经**网关**投递回你的 Telegram，附修复建议；这次排查过程被**学习闭环**沉淀成技能，下次同类故障直接走捷径。

全程你没开电脑。

## 项目状态

- Stars 243,392 / Forks 50,184（2026-09-08 取自 `gh repo view`）
- 语言：Python；协议：MIT
- 版本节奏：v0.20.6（2026-08-27）→ v0.21.0（2026-08-31）→ v0.21.1（2026-09-07），迭代密集
- 提交活跃至当日；提供中/乌尔都/西语多语言 README 与完整文档站

## 适用边界

- **适合**：想要一个长期陪跑、越用越顺手的全天候个人智能体的用户；需要跨 Telegram/Discord 等平台统一入口的团队；做智能体轨迹研究的人（仓库自带批量轨迹生成与压缩，面向下一代工具调用模型训练）。
- **不适合**：只需要一次性问答的场景（学习闭环的价值发挥不出来）；对自进化行为持保守态度的生产环境（技能自动创建/改进意味着行为会随时间变化，需要接受这一点）。
- **注意**：Windows 原生支持完整但较新，遇到问题走 issue；Termux 需按官方指南装 `.[termux]` 精选依赖而非 `.[all]`。

## 结语

Hermes Agent 把"智能体的记忆和成长"从论文概念做成了可安装的产品：技能自创建、自改进、会话可检索、用户建模，四个闭环点都有对应机制落地，而非营销话术。配合七种执行后端和多平台网关，它更像一个"住在你聊天软件里的同事"，而不是一个命令行工具。对认真想把 AI 智能体纳入日常工作流的开发者，值得一试。

项目地址：<https://github.com/NousResearch/hermes-agent>

官方文档：<https://hermes-agent.nousresearch.com/docs/>
