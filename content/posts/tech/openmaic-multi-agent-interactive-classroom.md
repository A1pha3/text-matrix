---
title: "OpenMAIC：清华大学开源的多智能体交互课堂，一句话生成一整门课"
date: 2026-08-31T04:05:00+08:00
slug: "openmaic-multi-agent-interactive-classroom"
github_repo: "THU-MAIC/OpenMAIC"
source_key: "gh:THU-MAIC/OpenMAIC"
description: "OpenMAIC 是清华大学开源的多智能体交互式课堂平台，一句话把任意主题或文档变成含幻灯片、测验、仿真与 PBL 的沉浸式课程，AI 老师与 AI 同学可讲可画可讨论。v1.0.0 引入 Agent 工作台与持久会话，MIT 协议。"
draft: false
categories: ["技术笔记"]
tags: ["AI 教育", "多智能体", "开源", "LangGraph"]
---

# OpenMAIC：清华大学开源的多智能体交互课堂，一句话生成一整门课

## 核心判断

**"AI 生成课程"这件事，多数产品止步于 PPT 生成器；OpenMAIC 的差异在于把课堂当成一个多智能体系统来做**——AI 老师会讲课、会在白板上推导、AI 同学会跟你实时讨论，而幻灯片、测验、交互仿真、项目式学习（PBL，Project-Based Learning）只是这个系统的产出物之一。它由清华团队（THU-MAIC）开发，23,659 Stars，有 JCST 2026 论文背书，2026 年 6 月从 AGPL-3.0 换到 MIT，v1.0.0（2026-08-27）刚加入了 chat-first 的 Agent 工作台。

技术栈一句话：Next.js 16 + React 19 + TypeScript 5 + LangGraph 1.1 + Tailwind 4，一个现代全栈项目的标准配置，多智能体编排走 LangGraph。

## 系统地图：先分清两条产品线

| 产品线 | 形态 | 适合 |
|--------|------|------|
| 经典一键生成器 | 输入主题/材料 → 直接出完整课堂 | 快速产出一节课 |
| v1.0 Agent 工作台 | 与 agent 对话，由它规划课程、逐页构建与修改 | 需要反复调整的课程生产 |

一条请求如何流过系统（以"上传一份 PDF 讲义生成课程"为例）：

1. **材料摄取**：文档/音频/视频上传，或网页搜索抓取（多格式解析含音频视频抽取、MinerU、AliDocMind 等）；
2. **Agent 规划**：工作台 agent 先产出课程大纲（经典模式下大纲可编辑后再生成）；
3. **多智能体构建**：LangGraph 编排下生成幻灯片、测验、交互 HTML 仿真、PBL 任务，可按阶段路由不同模型；
4. **课堂呈现**：AI 老师讲授 + TTS 语音，白板画图写公式，AI 同学参与讨论；
5. **导出**：可编辑 `.pptx`、交互式 `.html`、MP4 视频（v0.3.1 起），或离线课堂 ZIP。

## 值得注意的工程决策

- **Provider 中立**：模型（OpenAI/Anthropic/GLM/Kimi/Qwen…乃至 Ollama 本地模型）、媒体、搜索、存储后端全部可插拔，不强绑任何云厂商；
- **持久会话（durable sessions）**：v1.0 的构建会话存服务端，重启存活、可取消可恢复可中途转向——这是把课程生成当长任务系统而非一次性请求的设计；
- **本地化路线**：Lemonade 本地 AI、FunASR 本地语音识别，给教育场景的数据敏感需求留了出口；
- **生态打通**：内置 OpenClaw 集成，可从飞书、Slack、Telegram 等 20+ 聊天应用里直接说一句"teach me quantum physics"生成课堂；
- **技能化**：20 个内置技能覆盖幻灯片、测验、交互件、PBL、图片、视频、配音、`.pptx` 导入。

版本节奏相当密集：v0.1.0（2026-03）到 v1.0.0（2026-08）七个月内十次 release，最近一周仍在做课堂加载性能优化与存储修复。

## 快速上手

环境要求 Node.js ≥ 20、pnpm ≥ 10：

```bash
git clone https://github.com/THU-MAIC/OpenMAIC.git
cd OpenMAIC
pnpm install
# 配置 .env（至少一个 LLM provider 的 API key，如 OPENAI_API_KEY）
pnpm dev
```

不想自己部署的话有三条捷径：官方 Live Demo（open.maic.chat）、Vercel 一键部署按钮、OpenClaw hosted 模式（官网取 access code 即用）。中英文体验指南都发布在飞书 wiki 上。

## 适用边界

- **它是课程/课堂生成器，不是通用 PPT 工具**——追求精美商业路演片的用户会嫌它重；它的价值在"教学互动"这一层。
- 自部署是完整的 Next.js + （可选）Postgres 服务，不是丢个静态页就能跑的轻量工具；服务器持久化需要自己配存储后端。
- 多智能体 + TTS + 仿真的 token 与算力消耗不低，大规模教学场景要算成本账。
- 项目迭代极快（三个月一次大版本），生产采用建议锁定版本跟进 changelog。

## 采用建议

教师与课程作者优先试 Agent 工作台模式，材料直接喂自己的讲义最能体现差异；企业培训团队值得为它的 provider 中立与本地化选项做一次 PoC；纯个人学习用 hosted demo 即可，零部署成本。对想研究多智能体编排的工程师，这个代码库也是一份不错的 LangGraph 大型实战样本。
