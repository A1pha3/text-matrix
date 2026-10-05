---
title: "OpenMAIC：清华大学开源的多智能体交互课堂，一句话生成一整门课"
date: 2026-08-31T04:05:00+08:00
lastmod: "2026-09-29T20:00:00+08:00"
slug: "openmaic-multi-agent-interactive-classroom"
github_repo: "THU-MAIC/OpenMAIC"
source_key: "gh:THU-MAIC/OpenMAIC"
description: "OpenMAIC 是清华大学开源的多智能体交互式课堂平台，一句话把任意主题或文档变成含幻灯片、测验、仿真与 PBL 的课程，AI 老师与 AI 同学可讲可画可讨论。本文以 v1.1.2 为口径，覆盖 Agent 工作台、持久会话与课堂聊天迁移到 agent loop 的最新变化。"
draft: false
categories: ["技术笔记"]
tags: ["AI 教育", "多智能体", "开源", "LangGraph"]
---

# OpenMAIC：清华大学开源的多智能体交互课堂，一句话生成一整门课

## 核心判断

"AI 生成课程"这件事，多数产品止步于把大纲填进 PPT 模板；OpenMAIC 把课堂本身当成一个多智能体系统来做——AI 老师讲课、在白板上写画推导，AI 同学实时参与讨论，幻灯片、测验、交互仿真、项目式学习（PBL，Project-Based Learning）只是这套系统的产出物。它出自清华团队 THU-MAIC，有 JCST 2026 论文背书（《From MOOC to MAIC: Reimagine Online Teaching and Learning Through LLM-Driven Agents》，2026-04-10 在线发表，DOI 10.1007/s11390-025-6000-0），2026 年 6 月随 v0.3.0 从 AGPL-3.0 换到 MIT，目前 39,467 Stars（2026-09-29 GitHub 数据）。本文以 v1.1.2（2026-09-28）为口径。

技术栈一句话：Next.js 16 + React 19 + TypeScript 5 + LangGraph 1.1 + Tailwind 4，多智能体编排走 LangGraph，课堂播放与课堂动作各由独立引擎驱动。

## 系统地图：两条产品线，一套运行时

| 产品线 | 形态 | 适合 |
|--------|------|------|
| 经典一键生成器 | 输入主题/材料，直接产出完整课堂 | 快速产出一节课 |
| Agent 工作台（v1.0.0 起） | 与 agent 对话，由它规划大纲、逐页构建与修改 | 需要反复打磨的课程生产 |

两条线共用同一套课堂运行时。以"上传一份 PDF 讲义生成课程"为例，一条请求这样流过系统：

1. **材料摄取**：文档、音频、视频上传，或网页搜索抓取。文档解析有 MinerU、AliDocMind 等云端选项；音视频可在本地 ffmpeg/ffprobe 抽取与云端解析之间二选一，两者都没有时明确报错，不会静默给出空转写。
2. **大纲规划**：`@openmaic/generation` 把生成拆成两段——先出课程大纲，再逐场景生成内容；经典模式下大纲可以先编辑再生成（v0.2.2 起）。
3. **多智能体构建**：LangGraph 编排生成幻灯片、测验、交互 HTML、PBL 任务，可按生成步骤路由不同模型——v1.1.0 起，大纲、幻灯片、交互页、场景动作可以各配各的模型。工作台模式下这是一个 Postgres 支撑的持久 agent 会话：租约执行、心跳、崩溃恢复、可取消、可在运行中追加指令，agent 通过经过校验的工具原子地修补单个场景，而不是整块覆写。
4. **课堂呈现**：Playback Engine 状态机驱动播放，Action Engine 执行 21 种课堂动作（语音讲解、白板画图/写字/形状/图表、聚光灯、激光笔等），AI 老师与 AI 同学的讨论由 LangGraph 状态机管理。Deep Interactive 模式（v0.2.0 起）还能产出 3D 可视化、仿真、小游戏、思维导图与在线编程五类交互页。
5. **导出**：可编辑 `.pptx`、交互式 `.html`、MP4 视频（v0.3.1 起），或离线课堂 ZIP。

课堂内还有一层对话，这是 v1.1.0（2026-09-24）最大的变化：课堂聊天从"导演图"迁到了 agent loop。学生可以指着某个幻灯片元素、交互组件或白板笔迹提问；提问时系统会采样声明了状态的交互页，老师因此能解释学生眼前实际跑出来的那次实验结果，而不只是复述课件。答题前老师可以按需读课件、查交互实验的实时状态、搜索网页。

## 值得注意的工程决策

**Provider 中立落到了凭据与路由的细节上。** LLM、图片、视频、TTS/ASR、搜索、存储后端全部可插拔，README 列出的清单很长：OpenAI、Azure OpenAI、Anthropic、Amazon Bedrock、Google Gemini、DeepSeek、Qwen、Kimi、MiniMax、Grok、OpenRouter、豆包、腾讯混元、小米 MiMo、GLM，外加 Ollama 本地模型和任何 OpenAI 兼容 API。比清单更值得学的是三条约束：凭据只存在服务端，不进浏览器；每个能力有统一的关闭开关（`<CAP>_<PREFIX>_ENABLED=false`）；模型路由解析失败时直接报错，而不是猜一个厂商兜底。

**持久会话按长任务系统设计。** 构建会话存数据库，带租约与心跳，worker 重启后可恢复；运行中可以取消、转向，事件历史可回放。数据库维护的修订计数器记录每个场景的新旧，前端只拉取变过的场景。课程生成动辄几十次模型调用，这套机制决定了一次中途失败是"从头再来"还是"接着跑"。

**默认零数据库。** 不配 Postgres 也能跑：课程文档、学习记录、素材走浏览器存储。`@openmaic/storage` 把这些原语抽象成可替换的存储接口，Postgres 参考实现接管文档、学习运行时、素材、agent 会话与用户技能，素材字节可落 Postgres 或 S3，HTTP 契约也允许接外部存储服务。

**本地化路线是给教育场景留的出口。** Lemonade 作为本地 OpenAI 兼容 provider 覆盖 LLM、图片、TTS、ASR，不需要 API key；FunASR 提供本地语音识别（SenseVoiceSmall、Paraformer、Fun-ASR-Nano），CPU 也能跑 sensevoice。学生数据的敏感度，教育机构比一般团队在意得多。

**教学法被编码成了技能。** `skills/agent-runtime/` 下有 24 个内置技能，覆盖的不只是幻灯片、测验、PPTX 导入这些"件"，还有一排课程设计方法：费曼学习法（feynman-learning）、最近发展区（zone-of-proximal-development）、螺旋式课程（spiral-curriculum）、逆向教学设计（understanding-by-design）、社会情感学习（social-emotional-learning）、事实核查（fact-check）、深度研究（deep-research）、教师风格复用（teacher-style-clone）。用户自建技能按所有者存储，走同一套运行时读写。"怎么教"从 prompt 里的隐性约定，变成了可审计、可组合的显式单元。

**生态打通走标准技能格式。** 仓库自带 SKILL.md 格式的 OpenMAIC Skill：OpenClaw 用户 `clawhub install openmaic` 即装，Codex、DeepSeek、WorkBuddy 等工作台导入 `skills/openmaic/` 目录即可。配合 OpenClaw，可以从飞书、Slack、Telegram 等 20+ 聊天应用里说一句 "teach me quantum physics" 直接生成课堂，也可以在 IDE 里用。

## 版本节奏与安全维护

v0.1.0（2026-03-26）到 v1.1.2（2026-09-28），六个月十五个 release，主分支 changelog 里还压着一轮未发布的 owner 身份与多租户持久化重构。这个节奏对采用者的含义很直接：功能在快速演进，持久化层仍在动，生产环境要锁定版本、跟 changelog、订阅安全公告。

安全响应值得单独说。v1.1.1 与 v1.1.2（2026-09-26/28）连发两个安全版本，修的是同一类 SSRF 问题：MinerU 云解析和一批 provider 路由会把调用方可控的 URL 直接抓取，存在打内网的余地（GHSA-cpjc-vgjh-c5jp、GHSA-g87c-cm4q-cw5x 两个公告）。修法是系统性的——所有 provider 请求收敛到严格传输层，只连已校验地址、拒绝重定向、限制响应与解压体积。一个教育项目把自部署的 SSRF 面当头等事来修，这是加分项。

## 快速上手

环境要求 Node.js ≥ 22.19、pnpm ≥ 10（package.json 的 engines 字段同样锁在 22.19.0）：

```bash
git clone https://github.com/THU-MAIC/OpenMAIC.git
cd OpenMAIC
pnpm install
cp .env.example .env.local   # 至少配一个 LLM provider 的 key，如 OPENAI_API_KEY
pnpm dev                      # http://localhost:3000
```

生产部署用 `pnpm build && pnpm start`。三件自部署必读：

- **ACCESS_CODE 默认不开**：`.env.example` 默认未设置访问码，此时所有路由——包括 API——对访客直接可达，README 原话叫 fail-open。公网部署务必设长随机值（至少 16 位），它是唯一的站点级口令。
- **要持久会话就配 Postgres**：浏览器存储够个人体验；工作台的持久会话与服务端素材池需要 `DATABASE_URL`，素材字节可另配 S3。
- **本地音视频抽取要装 ffmpeg**，或者配 AliDocMind 云端抽取；两者都没有，音视频素材会带明确的设置提示报错。

不想自己部署有三条捷径：官方 Live Demo（open.maic.chat）、README 里的 Vercel 一键部署按钮、OpenClaw hosted 模式（demo 站取 access code 即用）。中英文体验指南（v1.0.0 版）都挂在飞书 wiki 上。

## 适用边界

- **它是课堂生成器，不是通用 PPT 工具**。追求商业路演片的用户会嫌它重，它的价值在教学互动这一层。
- 这是一个完整的 Next.js 应用。个人用默认配置（浏览器存储）很轻；要服务端持久化，就是 Next.js + Postgres（可选 S3）的运维面，不是丢个静态页就能跑的轻量工具。
- 多智能体 + TTS + 仿真的 token 与算力消耗不低。v1.1.0 给渲染服务加了准入控制与单任务资源预算，说明团队自己也意识到了这一点；大规模教学场景还是要先算成本账。
- 迭代快意味着 API 与存储层都可能变。锁定版本跟进 changelog，别把内部存储结构当稳定接口依赖。

## 采用建议

顺序建议：先用 hosted demo 验证生成质量对你的学科是否成立；值得深入就自部署一个单 key 实例（配 ACCESS_CODE），喂自己的讲义，把经典模式与工作台模式各跑一遍；确定投入课程生产，再上 Postgres 持久化与按步骤的模型路由。企业培训团队做 PoC 时，把 provider 中立与本地化（Lemonade/FunASR）列为第一优先验证项，这决定它能不能过数据合规。纯个人学习，demo 就够。

对工程师，这个仓库另有一层价值：它是少见的把 LangGraph 编排、租约式 agent 会话、可插拔存储和 21 种课堂动作引擎放进同一个生产级应用的完整样本。想看多智能体怎么走出 demo、走进课堂，值得通读。
