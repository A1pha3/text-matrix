---
title: "OpenMontage 架构解析：把 AI 编程助手改造成视频制作工厂的开源尝试"
date: "2026-06-17T21:01:47+08:00"
lastmod: "2026-10-02"
slug: "calesthio-openmontage-agentic-video-production-guide"
github_repo: "calesthio/OpenMontage"
source_key: "gh:calesthio/OpenMontage"
description: "calesthio/OpenMontage 是官方口径下首个开源的智能体视频生产系统，用 12 条生产流水线、100+ 注册工具、700+ 份 Agent Skill 与知识文件，把 AI 编程助手变成一个视频制作团队。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Python"]
---

# OpenMontage 架构解析：把 AI 编程助手改造成视频制作工厂的开源尝试

## 快速信息卡

> **GitHub 仓库**： [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage)
>
> | 指标 | 数值 |
> |------|------|
> | ⭐ Stars | 62,235 |
> | 🍴 Forks | 7,942 |
> | 📜 License | AGPLv3 |
> | 💻 主要语言 | Python |
> | 🏠 官网 | [openmontage.video](https://www.openmontage.video/) |
> | 📅 最近推送 | 2026-09-06 |
> | 🔗 在线预览 | [GitHub README](https://github.com/calesthio/OpenMontage#readme)（另有[中文版 README](https://github.com/calesthio/OpenMontage/blob/main/README_zh-CN.md)） |
>
> Stars、Forks 与推送时间为 2026-10-02 的 GitHub API 读数，会随项目演进变化。

---

## 学习目标

读完本文，可以掌握以下能力：

- 解释 OpenMontage 的"无代码编排器"定位，以及它如何把 AI 编程助手变成视频导演
- 理解三层知识架构（tools/pipeline_defs、skills、.agents/skills）的分工与协作方式
- 跟踪一次"从一句话到成片"的完整路径，理解阶段骨架与导演技能卡如何配合
- 掌握 Provider 评分选择器的 7 维评分逻辑，以及决策审计如何避免"prompt spaghetti"
- 识别 OpenMontage 的适用边界（适合什么场景、不适合什么场景、迁移风险）

---

## 目录

- [快速信息卡](#快速信息卡)
- [学习目标](#学习目标)
- [一、核心判断](#一核心判断这不是一个视频工具而是一个无代码编排器)
- [二、系统地图：三层知识架构](#二系统地图三层知识架构)
- [三、12 条生产流水线](#三12-条生产流水线从动画解说片到角色动画)
- [四、Provider 评分选择器](#四provider-评分选择器避免prompt-spaghetti)
- [五、质控门禁](#五质控门禁把看起来像视频挡在门外)
- [六、零 API Key 路径](#六零-api-key-路径完全离线的入门方式)
- [七、任务流案例](#七任务流案例一句-prompt-走过-openmontage)
- [八、采用顺序与适用边界](#八采用顺序与适用边界)
- [九、小结](#九小结)
- [自测题](#自测题)
- [练习](#练习)
- [常见问题](#常见问题)
- [进阶路径](#进阶路径)

---

OpenMontage 想回答的问题不是"如何用 AI 生成一段视频"，而是"如何让你的 AI 编程助手变成一个完整的视频制作团队"。它不写任何传统意义上的协调代码——Claude Code、Cursor、Copilot、Windsurf、Codex 这些编程 Agent 本身就是导演，OpenMontage 提供的是流水线剧本、工具手册和质控门禁。

截至 2026 年 10 月 2 日，这个由 calesthio 维护的项目在 GitHub 上有 62,235 Stars、7,942 Forks，License 是 AGPLv3，最近一次推送在 2026 年 9 月 6 日。仓库内打包了 12 条生产流水线、100+ 个注册工具、700+ 份 Agent Skill 与生产知识文件、20 余份 JSON Schema。

本文是一篇架构分析。文章先讲 OpenMontage 为什么不能用"普通 AI 视频工具"的视角去看，再拆三层知识架构、流水线剧本格式、Provider 评分选择器与质控门禁，最后用一个具体任务跑通"从一句话到成片"的完整链路。

## 一、核心判断：这不是一个视频工具，而是一个"无代码编排器"

OpenMontage 的 README 用一句话点明了自己的位置：

> OpenMontage uses an **agent-first architecture**. There is no code orchestrator. Your AI coding assistant IS the orchestrator.

这意味着：

- 仓库里**没有**类似 Airflow、Prefect 那样的 DAG 调度器，也没有 LangGraph、CrewAI 那种显式状态机。所有流水线剧本都是 YAML 描述的"导演脚本"，由 Agent 在运行时自行解读并执行。
- Python 只提供工具（`tools/`）与持久化（`lib/checkpoint.py`），不参与调度逻辑。"如何编排"完全写在 Markdown Skills 与 YAML Manifest 里。
- 创作决策、Provider 选择、风格判断、Renderer 决策全部走**显式审计日志**，每一步都记录备选项、置信度与决策理由，方便事后回放。

这个选择带来的直接后果是：所有"调度正确性"都依赖 Agent 正确读取并执行 Skills。一旦 Agent 走偏，OpenMontage 没有兜底机制——它不会"自动修正"Agent 的判断，只会在质控门禁处**拦截**次品并要求重做。

如果你期待的是一个"开箱即用、一键出片"的工具，OpenMontage 不是。它的价值在于：当你已经有一个能读文件、跑 Python 的 AI Agent 时，它让这个 Agent 具备一整套视频生产方法论和工具箱。

## 二、系统地图：三层知识架构

OpenMontage 把"工具能力 / 使用约定 / 领域知识"明确切成三层，让 Agent 按需读取：

```
┌──────────────────────────────────────────────────────────┐
│  Layer 1: tools/ + pipeline_defs/                        │
│  ─ "What exists"（可执行能力 + 流水线剧本）                  │
│  · 100+ 个注册工具，分布在 video/audio/graphics/          │
│    enhancement/analysis/avatar/subtitle 等子目录           │
│  · 12 份生产流水线 YAML Manifest                           │
├──────────────────────────────────────────────────────────┤
│  Layer 2: skills/                                         │
│  ─ "How to use it"（OpenMontage 内部约定与质量标准）        │
│  · skills/pipelines/  — 每条流水线的阶段导演技能卡          │
│  · skills/creative/   — 创意技法（hook、pacing、镜头）     │
│  · skills/core/       — 核心工具技能（Remotion/HyperFrames）│
│  · skills/meta/       — Reviewer、Checkpoint 协议、        │
│                         动画运行时选择、配音表演            │
├──────────────────────────────────────────────────────────┤
│  Layer 3: .agents/skills/                                 │
│  ─ "How it works"（外部领域知识包，90+ 个目录）             │
│  · Flux、Remotion、Kling 等供应商的 prompt 写法、          │
│    参数细节、失败模式                                       │
│  · GSAP、Three.js、Manim 等动画库用法，甚至 Vercel         │
│    的 React 编写规范                                       │
└──────────────────────────────────────────────────────────┘
```

### 关键观察

- **Layer 1 是机器可调用的**（Python 工具 + 强 Schema 约束的 Pipeline Manifest）。
- **Layer 2 是 Agent 必须先读后用的**——每条流水线的 Manifest 用 `required_skills` 显式声明各阶段要读的技能卡，技能卡解释每一步该做什么、不能跳过什么、什么情况下需要请求人工审批。
- **Layer 3 是按需加载的领域知识**，Provider Selector 选完厂商后会提示"去读哪个 `.agents/skills/xxx`"。选 Kling 就读 Kling 的 prompt 知识包，选 Remotion 就读 React 场景的合成知识包。

这种分层让 OpenMontage 看起来"没有状态机"，实际把状态机拆成了两份：Manifest 是静态结构，Skill 是动态方法论。Agent 通过"读 Manifest → 读 Skill → 调 Tool → Checkpoint → 自我 Review"的循环推进。

## 三、12 条生产流水线：从动画解说片到角色动画

每条流水线对应一个独立的视频生产工作流，结构与命名都遵循 `pipeline_defs/<name>.yaml` 规范：

| Pipeline | 产出形态 | 典型场景 |
|----------|----------|----------|
| `animated-explainer` | AI 生成的解说片（研究 + 旁白 + 视觉 + 音乐） | 科普、教学、Topic 拆解 |
| `animation` | 动态图形、动态排版、动画序列 | 社媒、产品演示、抽象概念 |
| `avatar-spokesperson` | 数字人讲解视频 | 企业内训、公告 |
| `character-animation` | SVG 绑定 + 姿势库 + GSAP 时间线的卡通角色动画 | 角色短片、动画 IP 内容 |
| `cinematic` | 预告片、情绪驱动剪辑 | 品牌短片、预热 |
| `clip-factory` | 一长段素材 → 多条排序后的短视频 | 长内容拆条 |
| `documentary-montage` | CLIP 索引的免费素材库 → 主题蒙太奇 | 视频随笔、情绪片、B-roll |
| `hybrid` | 既有素材 + AI 生成的补充视觉 | 给老素材加特效 |
| `localization-dub` | 字幕、翻译、配音 | 多语言发行 |
| `podcast-repurpose` | 播客高光 → 短视频 | 播客营销 |
| `screen-demo` | 屏幕录制 + 包装 | 产品演示、文档 |
| `talking-head` | 镜头主导的演讲视频 | 演示、Vlog、采访 |

`pipeline_defs/` 下实际有 13 份 YAML：除上面 12 条外，还有一份 `framework-smoke.yaml`，是用于框架契约测试的最小清单，不对应真实生产工作流。

**所有流水线共享同一个 7 阶段骨架**：

```
research → proposal → script → scene_plan → assets → edit → compose
```

每个阶段在仓库里对应一份"导演技能卡"。以 `animated-explainer` 为例，其 Manifest 的 `required_skills` 指向 `skills/pipelines/explainer/` 下的 `research-director.md`、`proposal-director.md` 等九份技能文件——技能目录名（explainer）与流水线名（animated-explainer）不强制一致，由 Manifest 显式声明。这套 v2.0 Manifest 还引入了 `executive-producer` 编排技能，统一管理阶段流转与返工上限——以 `animated-explainer` 为例：每阶段最多 3 次修订、3 次退回、20 分钟墙钟时间，默认预算 $2.00。

Agent 在进入一个阶段时必须先读对应技能卡，再决定调用哪些 Layer 1 工具、是否需要进入 Reviewer 流程、是否要停下来等人工审批。

`research` 阶段是 OpenMontage 区别于"普通 AI 视频工具"的关键。Agent 在写第一行脚本之前，必须先做 15–25+ 次网络搜索，覆盖 YouTube、Reddit、Hacker News、新闻站、学术来源——把观众问题、趋势角度、视觉参考收集成结构化研究简报，并附引用。视频内容直接基于这些真实信号，不靠模型"凭空创作"。

## 四、Provider 评分选择器：避免"prompt spaghetti"

OpenMontage 内置的 Provider 覆盖视频 20+、图像 15+、TTS 10+ 家，另有音乐与音效生成。视频从云端 Kling（fal.ai 网关与官方直连）、Runway Gen-4、Google Veo 3.1 到本地 WAN 2.1/2.2、Hunyuan、CogVideo、LTX-Video 都有。面对这么多选项，传统做法是写一堆 `if provider == "X"` 的分支。OpenMontage 选择了一条**统一路径**：

> 每次工具选择都跑 7 维评分，并把结果写入决策日志。

**7 个维度与默认权重：**

| 维度 | 默认权重 | 含义 |
|------|----------|------|
| 任务适配 (task fit) | 30% | 当前 Provider 适合这条任务吗 |
| 输出质量 (output quality) | 20% | 画面/音频本身的质量水位 |
| 控制力 (control) | 15% | 风格/参数可调范围 |
| 可靠性 (reliability) | 15% | 失败率、超时、限流 |
| 成本效率 (cost) | 10% | 单次调用花费 |
| 延迟 (latency) | 5% | 端到端响应速度 |
| 连续性 (continuity) | 5% | 与前一步的视觉/风格一致性 |

Agent 把"用户用自然语言写的需求"（比如 "Pixar-style animated short with character consistency"）喂给 Selector，Selector 先做意图展开与风格信号归一化，再按 7 维度对所有可用 Provider 评分。胜出者连同评分、备选项、置信度一起写入决策日志。

这样做有两个直接好处：

1. **可审计**——事后能查"为什么这一步选了 Veo 而不是 Kling"，并能复现当时的判断。
2. **可降级**——如果一个 Provider 临时不可用，按同样评分逻辑可以立刻切到次优选项，整个评分过程对 Agent 透明。

Selector 的输出还会带上胜出 Provider 对应的 `agent_skills`，Agent 拿到名字的同时就知道该读哪个 Layer 3 知识包，不会拿着 Provider 名字乱写 prompt。

## 五、质控门禁：把"看起来像视频"挡在门外

OpenMontage 面对的最大风险是 Agent 自由度过高、最后交付出"PowerPoint 动画"式的劣质品。仓库的应对策略是在渲染前与渲染后各设一道门。

### 5.1 渲染前（Pre-compose Validation）

- **交付承诺校验**：提案承诺的是 "motion-led"（以动效为主）的视频，素材里却 80% 是静态图——校验失败，强制重排（实现在 `lib/delivery_promise.py`）。
- **Slideshow 风险评分**：6 维分析（重复度、装饰性视觉、动效偏弱、镜头意图、字体过度依赖、未被证实的电影化声明），打分到 critical 直接拦截（实现在 `lib/slideshow_risk.py`）。
- **Renderer Family 校验**：Remotion / HyperFrames / FFmpeg 必须有显式选择，禁止渲染时临时切换。

### 5.2 渲染后（Post-render Self-Review）

每次 Render 完成，运行时自动跑：

- `ffprobe` 校验（码率、时长、轨道完整性）
- 在 4 个位置抽帧，检测黑帧与覆盖物损坏
- 音频电平分析（静音段、削波）
- 交付承诺复核（这条视频真的实现了当初承诺的形态吗）
- 字幕完整性核对

任意一项不通过，视频**不会被呈现给用户**，而是回到 edit 阶段重做。

### 5.3 决策审计与预算

每一次 Provider 选择、风格 Playbook 选择、Renderer 家族选择、降级路径都会被记录。预算控制也走同样路径：

- 渲染前**预估**花费
- 调用前**预留**额度
- 调用后**对账**实际花费
- 三种模式：`observe`（只记录）/ `warn`（超额告警）/ `cap`（硬限）
- 默认每笔超过 $0.50 触发人工审批，总预算 $10，可在 `config.yaml` 调整

### 5.4 Backlot 看板：让过程可见，让审批强制

流水线一长，聊天窗口很难回答"现在跑到哪了"。OpenMontage 自带 Backlot 看板（`python -m backlot open`）：阶段点亮、剧本以手稿页形式落位、场景卡在素材生成时闪烁，Provider 决策和花费实时上墙。

人工审批也**不是建议，而是门禁**：checkpoint 写入器会拒绝没有记录审批的"已完成"门禁阶段，被替换的历史 checkpoint 一并归档——审计链（含门禁流转）在多次返工后仍然完整。

## 六、零 API Key 路径：完全离线的入门方式

对只想"先看一眼"的人，OpenMontage 提供了 `make setup` 开箱即可用的零密钥路径：

| 能力 | 免费工具 | 作用 |
|------|----------|------|
| 旁白 | Piper TTS | 完全本地、离线的人声朗读 |
| 开放素材 | Archive.org + NASA + Wikimedia Commons | 免费/开放的档案素材 |
| 额外素材 | Pexels + Unsplash + Pixabay | 免费素材（开发者 Key 免费申请） |
| 合成 (React) | Remotion | React 写镜头、动画、字幕、Talking Head |
| 合成 (HTML/GSAP) | HyperFrames | HTML+CSS+GSAP 做动态排版、SVG 角色动画 |
| 后期 | FFmpeg | 编码、字幕烧录、混音、色彩 |
| 字幕 | 内置 | 自动生成带字级时间戳的字幕 |

零密钥路径能跑三类典型工作流：

1. **图像驱动视频**：Piper 念稿、Remotion 把静态图剪成完整视频。
2. **真实素材蒙太奇**：告诉 Agent 你想做"documentary montage"，它会从 Archive.org、NASA、Wikimedia Commons 拉一批开放素材，按 CLIP 检索排序后剪出真实动效的视频——不是把图片 Ken Burns 一下了事。
3. **本地角色动画**：SVG 角色绑定、姿势库、GSAP 时间线交给 HyperFrames 渲染，产出卡通角色表演，落到 `projects/<project-name>/renders/final.mp4`。

README 首页陈列的样片都标注了成本：60 秒 Pixar 风格动画短片 THE LAST BANANA 用 Kling v3（经 fal.ai）生成六段动效、Google Chirp3-HD 旁白，总成本 $1.33；科幻预告 SIGNAL FROM TOMORROW 走 Veo 加 Remotion；三维展示 OBJECTS IN OVERDRIVE 没用生成式视频，用 Blender 物理动画加 FFmpeg 合成。官方给出的成本档位：配置图像/视频 Provider 后，单条 prompt 约 $0.15–$1.50；完整配置约 $1–$3。

Renderer 在 Proposal 阶段就锁定成 `render_runtime`，然后贯穿整条流水线：Remotion 与 HyperFrames 不能"运行时偷偷切换"，这是仓库明确点名的"治理违规"。

## 七、任务流案例：一句 prompt 走过 OpenMontage

README 的 Quick Start 用这条 prompt 做演示，我们顺着它走一遍全程：

> "Make a 60-second animated explainer about how neural networks learn"

1. **Pipeline 选择**（Layer 1）：Agent 读 `pipeline_defs/animated-explainer.yaml`，确认 7 阶段骨架、所需技能卡与工具集合。
2. **Research 阶段**（Layer 2）：读 `skills/pipelines/explainer/research-director.md`，发起 15–25 次网络搜索（YouTube、Reddit、Hacker News、新闻与学术来源），把"神经网络学习"的高赞科普、常见误区、视觉化范式收集成结构化简报。
3. **Proposal 阶段**（Layer 2）：读 `skills/pipelines/explainer/proposal-director.md`，整理研究发现，给出 3 个以上差异化方案、各自工具栈与预估花费，并按要求同时呈现 Remotion / HyperFrames 两种渲染运行时的取舍。等待用户审批；方案获批后先制作一段 10–15 秒样片，再进入 Script 阶段。
4. **Script 阶段**：读 `script-director.md`，写 60 秒旁白脚本与声调指引；调用 Piper 或 ElevenLabs 选声线并跑出样音。
5. **Scene Plan 阶段**：把脚本拆成一组镜头，标注每个镜头的视觉要求（图像/动图/真实素材）、节奏、字幕样式。
6. **Assets 阶段**（Layer 1 + Layer 3）：Image Selector 在 FLUX、Google Imagen、Recraft、GPT Image 2、Local Diffusion 之间按 7 维评分，胜出后被告知去读对应 Layer 3 prompt 知识包；逐镜头出图。音乐走 Suno / ElevenLabs Music，同样由评分器选定。
7. **Edit 阶段**：把图、音、字幕按 Scene Plan 排成时间线；运行 Pre-compose Validation。
8. **Compose 阶段**（Remotion 或 HyperFrames）：按 `render_runtime` 渲染。渲染完成后自动跑 Post-render Self-Review，全部通过才输出 `final.mp4`。

整个过程中所有 Provider 选择、风格选择、Renderer 选择、降级路径都进决策日志；每一阶段产出物通过 `lib/checkpoint.py` 落盘 JSON，支持从检查点恢复。

## 八、采用顺序与适用边界

### 8.1 适合什么场景

- 已经在用 Claude Code / Cursor / Copilot，想把"做视频"也交给同一个 Agent。
- 团队有可观测的"AI 视频生产"诉求，需要审计日志、预算门禁、质控门禁。
- 接受"用自然语言驱动、不写编排代码"的范式，能容忍 Agent 偶发走偏（被门禁拦截后重做即可）。
- 项目对多模态产出有需求：解说片、蒙太奇、本地化、播客拆条共享同一套工具栈。

### 8.2 不适合什么场景

- 期待"一键出片、不读 README 就能跑"：OpenMontage 严重依赖 Agent 正确执行 Skills。
- 没有编程 Agent 的环境：所有指令都依赖 Agent 能"读文件 + 跑 Python + 读 Markdown"，纯 Web UI 用户用不到它。
- 极端低成本量产：即便零密钥路径也需要本地 FFmpeg + Node.js 18+ + Python 3.10+（HyperFrames 渲染要求 Node.js ≥ 22），高质量路径会调用 Kling/Veo/Suno 等付费 API。
- 法律/合规敏感场景：AGPLv3 + 大量第三方 Provider，需要法务提前评估。

### 8.3 推荐的起步顺序

1. `git clone` + `make setup`，再跑 `make demo` 渲染零密钥样片，确认环境没问题。
2. 拿一条现有内容（YouTube 视频、播客片段），从"参考视频"路径出发，让 Agent 给出几个差异化方案与预估成本，看过样片再决定要不要全量生产。
3. 拿到一批 Provider Key 后，按样例 prompt gallery（`PROMPT_GALLERY.md`）逐档升级：纯图 → 图像 + 音乐 → 图像 + 视频 → 完整音视频。
4. 在 `config.yaml` 里把预算模式从 `observe` 调到 `warn` 或 `cap`，再开始跑生产流量。

## 九、小结

OpenMontage 不是一个"AI 视频生成模型"，而是一套**让 AI 编程助手具备视频生产能力的方法论 + 工具 + 流水线剧本**。它的核心设计有四条：

- 用"无代码编排"重新定义 Agent 与工具的关系——Agent 读 Skills、用 Tools、做 Checkpoint，仓库不写状态机。
- 用"三层知识架构"区分工具能力、内部约定、领域知识，避免把所有内容塞进一个超长 Prompt。
- 用"7 维评分 + 决策审计"取代硬编码的 if-else，让 Provider 选择既可解释又可降级。
- 用"Pre/Post-render 双重门禁"把"看起来像视频"挡在交付之前。

对于已经在用编程 Agent 做生产的团队，这是一份值得花一个下午读 README、再花一晚跑通零密钥样片的开源方案。它不会取代专业剪辑师，但会让 Agent 在"做视频"这件事上多出一整套可审计、可治理的工作流。

---

## 自测题

1. **OpenMontage 的核心定位是什么？它和普通 AI 视频生成工具的根本区别在哪里？**
   - 参考答案：OpenMontage 是一个"无代码编排器"，它不写任何传统意义上的协调代码，而是让 Claude Code、Cursor、Copilot 等编程 Agent 本身成为导演。区别在于：普通工具是"一键出片"的黑盒，OpenMontage 提供的是流水线剧本、工具手册和质控门禁，让 Agent 具备完整的视频生产能力。

2. **三层知识架构分别解决什么问题？Agent 在不同阶段该读哪层？**
   - 参考答案：Layer 1（tools/ + pipeline_defs/）解决"有什么可执行能力"（机器可调用）；Layer 2（skills/）解决"怎么用"（Agent 必须先读后用）；Layer 3（.agents/skills/）解决"领域知识"（按需加载）。Agent 在进入一个阶段时必须先读对应 Layer 2 技能卡，Provider 选择后读 Layer 3 知识包。

3. **Provider 评分选择器的 7 维评分分别是哪 7 个维度？为什么不用硬编码的 if-else？**
   - 参考答案：任务适配(30%)、输出质量(20%)、控制力(15%)、可靠性(15%)、成本效率(10%)、延迟(5%)、连续性(5%)。不用 if-else 的原因是：可审计（事后能查"为什么选 Veo 而不是 Kling"）、可降级（Provider 不可用时按同样逻辑切到次优选项）、可扩展（新增 Provider 只需调整评分输入，不需要改所有 if-else 分支）。

4. **质控门禁在哪些环节拦截次品？分别检查什么？**
   - 参考答案：渲染前（Pre-compose Validation）检查交付承诺、Slideshow 风险评分、Renderer Family 校验；渲染后（Post-render Self-Review）检查 ffprobe 校验、抽帧检测、音频电平分析、交付承诺复核、字幕完整性核对。任意一项不通过，视频不会被呈现给用户，而是回到 edit 阶段重做。

5. **如果你想把 OpenMontage 用于生产环境，推荐的采用顺序是什么？**
   - 参考答案：1) `git clone` + `make setup`，跑 `make demo` 零密钥样片确认环境；2) 拿一条现有内容，让 Agent 给出几个差异化方案与预估成本；3) 拿到 Provider Key 后，按样例 prompt gallery 逐档升级；4) 在 `config.yaml` 里把预算模式调到 `warn` 或 `cap`，再开始跑生产流量。

---

## 练习

### 练习 1：跑通零密钥路径

**任务**：在不配置任何 API Key 的情况下，安装 OpenMontage 并跑通 `make demo` 的零密钥样片。

**步骤**：
1. `git clone` 仓库并安装依赖
2. 运行 `make setup` 配置零密钥路径
3. 运行 `make demo` 生成样片
4. 查看生成的视频文件，理解 Remotion 和 Piper TTS 如何协作

**验证**：能够解释样片使用了 OpenMontage 的哪些组件。

---

### 练习 2：理解 Provider 评分选择逻辑

**任务**：阅读 Provider Selector 的实现，理解 7 维评分逻辑。

**步骤**：
1. 从 `lib/scoring.py` 入手找到评分引擎实现
2. 理解意图展开与风格信号归一化过程
3. 手动修改某个维度的权重，观察选择结果变化
4. 阅读一份决策日志，理解审计逻辑

**验证**：能够解释为什么某一步选择了特定 Provider，以及置信度是如何计算的。

---

### 练习 3：创建一个自定义流水线

**任务**：参考现有的 12 条生产流水线，定义一个你自己的视频生产工作流。

**步骤**：
1. 选择一个现有流水线（如 `animated-explainer`）作为参考
2. 定义你的流水线的 7 阶段骨架
3. 编写对应的 Stage Director 技能卡（每个阶段一份）
4. 测试流水线是否能够被正确执行

**验证**：Agent 能够读取你的流水线定义并按照预期执行。

---

### 练习 4：分析质控门禁的效果

**任务**：故意构造一个低质量视频产出，观察质控门禁如何拦截。

**步骤**：
1. 构造一个素材质量差、Renderer 选择不明的提案
2. 对照 `lib/delivery_promise.py` 与 `lib/slideshow_risk.py`，观察 Pre-compose Validation 如何拦截
3. 查看 Post-render Self-Review 的审计报告
4. 理解 Slideshow 风险评分的 6 维分析

**验证**：能够解释质控门禁在哪些环节拦截了次品，以及为什么。

---

### 练习 5：集成一个新的 Provider

**任务**：假设你要为 OpenMontage 添加对一个新视频生成模型的支持。

**步骤**：
1. 理解 Layer 3 知识包的写法
2. 编写新 Provider 的 prompt 知识包
3. 将其注册进 `lib/providers`，纳入评分选择器
4. 测试选择逻辑是否能够正确识别新 Provider

**验证**：OpenMontage 在面临选择时能够考虑你的新 Provider，并能够正确读取对应的 Layer 3 知识包。

---

## 常见问题

### OpenMontage 和普通的 AI 视频生成工具有什么区别？

普通 AI 视频生成工具（如 Runway、Pika）是"一键出片"的黑盒，用户无法控制生成过程。OpenMontage 是一个"无代码编排器"，它让编程 Agent（如 Claude Code、Cursor）具备视频生产能力，用户可以控制整个生产流程、选择 Provider、设置预算门禁。

### 零密钥路径生成的视频质量如何？

零密钥路径使用 Piper TTS（本地语音）、Remotion（本地渲染）和免费素材库，质量足以预览和测试，但达不到商业制作水准。要生成高质量视频，仍需配置 Kling、Veo、Suno 等付费 API。

### OpenMontage 支持哪些编程 Agent？

官方支持 Claude Code、Cursor、Copilot、Windsurf、Codex，仓库为各家内置了专属指令文件（`CLAUDE.md`、`CURSOR.md`、`COPILOT.md`、`CODEX.md`、`.windsurfrules`）。只要 Agent 能"读文件 + 跑 Python + 读 Markdown"即可使用。

### 如何控制视频生成成本？

在 `config.yaml` 中设置预算模式：
- `observe`：只记录，不限制
- `warn`：超额告警
- `cap`：硬限制

也可以设置单笔超过 $0.50 需人工审批，以及总预算上限（默认 $10）。

### OpenMontage 的 License 是否允许商用？

OpenMontage 使用 AGPLv3 License，这意味着如果你修改了 OpenMontage 并作为服务部署，你需要开源你的修改。使用 OpenMontage 而不修改（仅调用）则不受此限制。

### 渲染失败后如何调试？

查看 Post-render Self-Review 的审计报告，其中包含了 ffprobe 校验结果、抽帧检测截图、音频电平分析。也可以打开 Backlot 看板（`python -m backlot open`）实时查看阶段进度，或查决策日志理解 Agent 在选择 Provider 和 Renderer 时的决策过程。

---

## 进阶路径

### 阶段一：快速上手（1 周）
- 目标：跑通零密钥路径，理解三层架构
- 行动：安装 OpenMontage，跑通 `make demo` 零密钥样片，阅读 `skills/pipelines/explainer/` 下的 Stage Director 技能卡，理解 Agent 如何读 Skill 后执行
- 验收：能解释三层知识架构的分工，并成功跑通零密钥样片

### 阶段二：Provider 评分与决策审计（2-4 周）
- 目标：掌握 7 维评分逻辑，理解决策审计如何避免"prompt spaghetti"
- 行动：阅读 `lib/scoring.py`，理解意图展开与风格信号归一化，手动修改评分维度权重观察结果变化，阅读几份决策日志理解审计逻辑
- 验收：能为一个新 Provider 编写评分逻辑，并解释为什么某一步选择了特定 Provider

### 阶段三：自定义流水线（1 个月）
- 目标：编写自己的 YAML Pipeline Manifest，定义新的视频生产工作流
- 行动：参考现有 12 条生产流水线，编写一个自定义流水线（例如"产品演示视频"），定义 7 阶段骨架，编写对应的 Stage Director 技能卡，测试并迭代
- 验收：能编写完整的 YAML Manifest 和对应的技能卡，并让 Agent 正确执行新流水线

### 阶段四：二次开发与社区贡献（长期）
- 目标：贡献新 Provider、新工具，或基于 OpenMontage 架构开发自定义系统
- 行动：阅读 OpenMontage 的核心代码（Python 工具、Checkpoint 协议），理解 Agent-Skill-Tool 的协作机制，尝试添加新 Provider 或新工具，提交 PR 到官方仓库
- 验收：能修改或扩展 OpenMontage 的功能，并贡献到官方仓库或社区

**进阶资源**：
- [OpenMontage GitHub 仓库](https://github.com/calesthio/OpenMontage)
- [OpenMontage 官网](https://www.openmontage.video/)
- [样例 Prompt Gallery](https://github.com/calesthio/OpenMontage/blob/main/PROMPT_GALLERY.md)
- [Remotion 官方文档](https://www.remotion.dev/docs)
- [HyperFrames 项目](https://github.com/heygen-com/hyperframes)
