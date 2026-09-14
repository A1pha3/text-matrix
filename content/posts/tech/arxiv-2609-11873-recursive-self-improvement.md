---
title: "人类造出的最后一个 AI：通向真正的递归自我改进"
slug: arxiv-2609-11873-recursive-self-improvement
date: 2026-09-14T19:18:00+08:00
lastmod: 2026-09-14T19:18:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["RSI", "Recursive Self-Improvement", "LLM", "Agent", "Meta-Learning", "AutoML", "Self-Play", "arXiv 2609.11873", "Theseus", "Gödel Agent", "Anthropic", "OpenAI", "DeepSeek", "Tencent Hunyuan", "ByteDance Seed", "Alibaba", "Kimi", "GLM"]
description: "深度解读 arXiv 2609.11873《The Last AI Built by Humans: Toward Genuine Recursive Self-Improvement》。32 位作者、横跨上海交大 / 清华 / 字节 / ModelBest / 小红书 / 腾讯 / Agent-Native / 上海 AI Lab 等机构的工业级 RSI 综述。提出 Headroom-Closed Index（HCI）衡量现有 LLM 真实能力分布，把递归自我改进拆成 B0 到 L5 的五级自主性骨架，按四个反馈机制迥异的应用域（科学发现 / 具身智能 / 软件工程 / 医疗）盘点代表系统，并区分结构性递归与有效性递归。本文同时充当全文翻译 + 路线图。"
author: 钳岳
arxiv_id: "2609.11873"
github_repo: "theseus-labs/Theseus"
project_page: "https://theseus-labs-rsi.github.io/"
source_key: "gh:theseus-labs/Theseus"
---

# 人类造出的最后一个 AI：通向真正的递归自我改进

> 来源：arXiv 2609.11873v1（2026-09-10 提交）— Yi Duan, Ying Liu, Zirui Tang, Haodong Chen, Jun Zhou 等 32 位作者，上海交通大学 / 清华 / 字节跳动 / ModelBest / 小红书 / 腾讯混元 / Agent-Native Research Lab / 上海 AI Lab / Humanlaya / Theseus Labs 等机构联合署名。
>
> 论文 75 页，12 张主表 + 11 张图，覆盖 130+ 篇参考文献与 50+ 套工业系统。本文为该综述的深度中文化 + 路线图解读。

## 这篇综述要回答的问题

Anthropic 的可解释性研究、DeepSeek 的训练流水线、字节的自动研究 agent——都在做某种意义上的"自己改自己"。这篇综述的提问方式不一样：

> 当前哪些"自我改进"够得上**递归自我改进（Recursive Self-Improvement，RSI）**这个标签，哪些只是用 AI 包装的人类工程流程？一个系统要具备什么样的回路结构，才能扛起"递归"这两个字？

论文标题是一句挑衅——**The Last AI Built by Humans**。作者认为，在某个 AI 系统能够持续重写"自己改自己的流程"之前，人类手搓的 AI 就是最后一代"完全由人类设计的 AI"。再往后那一代，必须由 AI 自己参与设计自己的改进机制。这条分界线在哪里？论文给出的答案是 **Headroom-Closed Index（HCI）** 和 **L1–L5 五级自主性骨架（autonomy-centered framework）**。

## 一、HCI：用"还差多少分到顶"替代"谁分高"

论文统计了 2023 年至 2026 年 9 月间 393 组模型–基准可配对观察，按 10 个能力域分别归一化到 Headroom-Closed Index。**HCI 的 0 分是该基准诞生那年的前沿分数，100 分是满分**。这把"模型 A 在某基准上 92 分"换成了"模型 A 把这个基准的进步空间关掉了多少"。

按 2026 年的前沿 HCI 排序：

| 能力域 | 代表基准 | 2026 前沿 HCI | 翻译 |
|---|---|---:|---|
| 高级数学 | FrontierMath v2 Tiers 1–3 | 86.4 | 还差 13.6 分到满分 |
| 研究生级科学 | GPQA Diamond | 85.8 | 还差 14.2 分 |
| 通用知识 | MMLU-Pro / LiveBench | 77.2 | 还差 22.8 分 |
| 法律推理 | Vals LegalBench | 64.5 | 还差 35.5 分 |
| 多模态推理 | MMMU-Pro | 62.2 | 还差 37.8 分 |
| 学术广度 | Humanity's Last Exam | 60.4 | 还差 39.6 分 |
| 搜索 / 终端代理 | BrowseComp / Terminal-Bench | 56.8 | 还差 43.2 分 |
| 软件工程 | LiveCodeBench / SWE-bench | 52.6 | 还差 47.4 分 |
| 工具调用代理 | BFCL v3 / τ/τ²-bench | 39.9 | 还差 60.1 分 |
| 网络安全（领先子轨） | Cybench unguided / pass@1 | 91.9 | 还差 8.1 分 |

从这张表里抽出三条对 RSI 路线图有用的观察：

1. **前沿差距极大**。研究生级科学的 HCI 已经到 85.8，但工具调用只有 39.9。把所有模型混在一起算"综合能力前沿"会掩盖这种差距——单分聚合基准必然会骗人。
2. **不同能力域的进步节奏不一样**。多模态推理 2025 年一年涨了 59.7 分，但 2026 年只涨了 2.5 分——撞天花板了。高级数学 2026 年反而比 2025 年多涨 20.8 分——还在加速。
3. **交互密集型任务留下最大的改进空间**。软件工程 / 终端代理 / 工具调用这三类，HCI 都低于 60，**这是 RSI 能直接产生增量价值的地方**——也是论文把 RSI 与这三类任务深度绑定的根因。

把三条合起来读：当前的"AI 大爆发"在 HCI 已经到 80+ 的能力域上撞天花板，**剩下能跑出大幅增长的地方都是需要持续环境反馈、需要把经验攒下来、再用经验改自己工作方式的任务**。后面所有 RSI 论述，都从这条判断起步。

## 二、把"改进自己"拆成五个层级：B0 到 L5

论文提了一个五级自主性骨架（autonomy-centered framework，B0 + L1–L5），按"哪些决策从人手里转交给了 AI"切层。先把全图放在这里，后面再拆每一层：

```mermaid
flowchart TB
    subgraph L5["L5 递归继承自主"]
        L5A["改"自己改自己的流程"<br/>STOP / DGM / Gödel Agent<br/>A-Evolve-Training / HyperAgents"]
    end
    subgraph L4["L4 部署与环境适应自主"]
        L4A["把线上交互证据固化为持久状态<br/>PANDO / Metis / Ouroboros<br/>Evo-Harness / SHAPER"]
    end
    subgraph L3["L3 学习经验自主"]
        L3A["决定"下一步该学什么"<br/>SSP / AZR / R-Zero / STP<br/>VOYAGER / SIMA 2 / SEAgent"]
    end
    subgraph L2["L2 改进策略自主"]
        L2A["决定"下一步该改什么"<br/>Self-Harness / GEPA / ADAS<br/>AFlow / AgentNAS / AutoKernel"]
    end
    subgraph L1["L1 改进执行自主"]
        L1A["人写流程, AI 执行<br/>FineWeb-Edu / NeMo Curator<br/>Capacity Efficiency / HealthBench"]
    end
    subgraph B0["B0 任务内改进"]
        B0A["输出可改, 系统状态不变<br/>Self-Refine / Reflexion<br/>Tree-of-Thoughts"]
    end
    B0 --> L1 --> L2 --> L3 --> L4 --> L5
    classDef frontier fill:#fff5e6,stroke:#d97706,color:#7c2d12;
    classDef mature fill:#e6f4ff,stroke:#1d4ed8,color:#1e3a8a;
    classDef prod fill:#e8f5e9,stroke:#15803d,color:#14532d;
    class L2,L3 frontier
    class L1 mature
    class L4,L5 prod
```

论文提了一个五级自主性骨架（B0 + L1–L5），切片维度是"哪些决策从人手里转交给了 AI"：

- **B0（任务内改进）**：输出可以改，但系统状态不变。Self-Refine / Reflexion / Tree-of-Thoughts 都属于这一层——任务结束，反思就没了，APEX-EM 论文里说得明白："LLM 智能体普遍缺乏持久程序记忆，即使解决了同样的任务，下一次还要从头再推一遍。"
- **L1（改进执行自主）**：人写好流程，AI 执行。Meta 的 Capacity Efficiency 把工程师调试经验编码成可复用技能后，每次新故障自动调用；NVIDIA NeMo Curator 把数据清洗流程模块化。这是现在大多数"AI 帮 AI"系统的真实位置。
- **L2（改进策略自主）**：人定目标、定验收标准，AI 自己决定"下一步该改什么"。Self-Harness 让模型看自己的执行轨迹、提出对自己 agent harness 的修改；AFlow 把工作流编码成可执行图、用蒙特卡洛树搜索改图。
- **L3（学习经验自主）**：AI 不光决定"怎么改"，还决定"下一步该学什么"。SSP 让解题者表现反作用于出题者的奖励；AZR 用可执行代码验证任务难度；VOYAGER 在 Minecraft 里根据当前技能和库存挑下一个练什么。
- **L4（部署与环境适应自主）**：AI 把部署中产生的真实交互证据固化成持久状态。PANDO 在网页代理运行时增删可复用规则；Metis 把重复使用的文本计划升级为可执行代码工具。
- **L5（递归继承自主）**：AI 开始改"自己改自己的流程"。STOP 把搜索器本身当成被优化的对象，迭代出第四代搜索器在五个迁移任务上全部跑赢种子；DGM / Gödel Agent / HyperAgents 在这一层做实验；A-Evolve-Training 把后训练研究策略本身作为持久状态留给下一轮。

每一级之间的跃迁都有明确的语义**：

- B0→L1 是**持久性**：改完能不能撑到下一次任务。
- L1→L2 是**策略选择**：从"按脚本改"到"挑改哪个"。
- L2→L3 是**未来学习议程**：从"改完立刻训练"到"挑下一次训练数据"。
- L3→L4 是**部署反馈**：从"离线训练"到"线上持续适应"。
- L4→L5 是**递归继承**：从"用现成的改进流程"到"改这个流程本身"。

**L2–L3 是当前工业最强前线，L4 开始有零星生产案例，L5 几乎全是研究系统**。这是论文反复强调的一点——别被博客标题党骗了。

### 一次具体任务如何流过这五级骨架

挑论文 §3.3 反复出现的 Self-Harness（Self-Harness 由同底模看自己的执行轨迹提小改）走一遍纵向流程。假设任务是"用一个 coding agent 修一个 Python 仓库里的 bug"：

- **B0 层**：agent 写一段代码，跑测试，失败，再写，再跑——五次失败后放弃。这次会话里反复修订的轨迹、反思、上下文，**全部不会带到下一个独立任务**。下一次遇到别的 bug，agent 从零开始。
- **L1 层**：Meta Capacity Efficiency 这类系统已经编码好"看到 NCCL watchdog timeout → 跑这个 runbook"的流程。AI 不决定改什么、按工程师预先写好的步骤改。修好的"可复用规则"进入规则库，下次新故障自动调。
- **L2 层**：Self-Harness 自己跑 coding 任务，**收集执行轨迹**，用同一底模提议对自己 harness（提示、工具循环、上下文装配）的小改，跑回归测试，**通过的版本留下、不通过的回滚**。这是"决定下一步改什么"的自主性。
- **L3 层**：SEAgent 在软件环境里维护一份"软件指南（software guidebook）"，**用当前轨迹评估更新这份指南**，指南再去生成后续练习任务。修 bug 不仅是改一个文件，还会改"下次遇到类似 bug 我该先看哪里"的策略。
- **L4 层**：Ouroboros 把**部署后的真实修复证据**（不只是测试通过，而是用户/评审反馈）作为输入，提出对自己工具/上下文/提示/核心实现的版本化修改；通过测试和人工审核后**替换运行时**，后面所有任务用新版本。
- **L5 层**：DGM / Gödel Agent 这一类系统，**改的对象是"自己改自己的流程"**——A-Evolve-Training 里 meta-agent 改"下一轮 worker 该用什么训练配方"；HyperAgents 里 meta-agent 在数学评分任务上学到的 agent-构造能力被拿去改机器人/论文评审任务上的 agent。

这六层串起来：同一类任务在 B0 层只能"现场修"，到 L5 层已经"修自己以后怎么修"。中间每一级跃迁，对应论文里那张 Mermaid 图的一条边。

## 三、RSI 与邻近范式的边界：什么不算 RSI

论文用一张表把 RSI 跟三个经常被混为一谈的范式切开：

| 特征 | 持续学习 | AutoML | Agentic AI/ML | **RSI** |
|---|:-:|:-:|:-:|:-:|
| 跨轮学习 | ✓ | ◦ | ◦ | ✓ |
| 持久保留 | ✓ | ◦ | ◦ | ✓ |
| 系统自我修改 | ✓ | ◦ | × | ✓ |
| 候选方案提出 | × | ✓ | ✓ | ✓ |
| 更新验证 | ◦ | ✓ | ◦ | ✓ |
| 后继者再进入 | ✓ | × | × | ✓ |
| **机制被修改** | × | ◦ | × | ✓ |
| **机制被复用** | × | × | ◦ | ✓ |

判读：

- **持续学习**解决"别忘"问题，但学什么、怎么学仍是外面定的。它碰到 RSI 的边界的标志是：经验能不能反过来改"下次怎么学"。
- **AutoML**解决"自动试配置"问题，AgentSquare / AFlow / ADAS 已经把搜索空间从超参数扩到 agent 工作流。它碰到 RSI 边界的标志是：搜索过程本身能不能变成被改的持久状态。
- **Agentic AI**解决"代理能跑多步任务"问题，但 episode 内通常不改自己。它碰到 RSI 边界的标志是：代理的 harness / 工具 / 提示本身能不能跨任务被改。

**判读 RSI 的硬指标是最后两列同时为 ✓**：机制被修改 + 机制被复用。分涨得再高，"改自己的方法"自己没被改、也没被下一轮继承，就不归 RSI。

## 四、按反馈机制挑应用域：四个完全不同的战场

论文没有按"任务类型"分类，而是按"什么样的反馈能验证一次更新（feedback regimes）"把应用切成四块。这一刀切得很准——同样的改进循环在软件工程里能跑起来，在临床里可能跑不动。

### S1：科学发现（AI4Science）

科学 RSI 的难点是**反馈的归因问题**。一次实验失败，可能是假设错，可能是协议错，可能是仪器错。论文把可进化部件拆成三块：

- **科学假设模块**：HypoForge 把假设生成经验蒸馏成可复用程序技能；EvoScientist 用 ideation memory 调后续提案；TTT-Discover 在测试时做强化学习让模型权重本身跟着反馈走。
- **实验代理**：Test-Time Tool Evolution 在推理过程中合成/复用科学工具（SciEvo 基准 1590 任务 / 925 工具）；CASCADE 创建并修复化学/材料科学的可执行技能；S1-NexusAgent 把完整研究轨迹蒸馏成"科学技能"。
- **反思系统与改进器**：SIA 用 FeedbackAgent 决定改脚手架、改工具、改 LoRA 还是改搜索逻辑；CORAL 用长跑异步 agent 自主检视先前尝试、决策何时调用评估器；SAGA 把目标函数本身改成可执行评分函数。

论文给 S1 域的判断：**L2 是当前最强前沿，L3 偶有闪现，L4/L5 基本空白**。

### S2：具身智能

物理实验跑不了几次，状态不能随便回滚。这逼着具身 RSI 在"环境生成"与"安全继承"两端发力：

- **环境与课程进化**：POET 同时演化环境种群与 agent 种群；EnvGen 用 LLM 当课程设计师，根据小 RL agent 的能力缺口生成新模拟器配置；GenEnv 把模拟器参数化成可训练课程策略；OMNI-EPIC 直接生成可执行的奖励与环境代码。
- **技能/记忆/agent harness 进化**：Voyager 把 Minecraft 成功行为写成可执行技能库；LRLL 用 wake–sleep 过程重组可组合机器人程序；SHAPER 同步进化可复用技能 + 上下文代码 harness；ENPIRE 允许编码 agent 修改机器人策略、训练流程与基础设施。
- **策略与动作模型进化**：Self-Improving Embodied Foundation Models 用预训练模型自给奖励；MEDAL++ 同时学完成任务与撤销任务，减少人工 reset。
- **世界模型与评估器进化**：VLAW 用真实机器人轨迹改进动作条件视频世界模型；World-VLA-Loop 让策略失败去精化世界模型、精化后的世界模型给下一轮策略优化；Motus2 把策略、仿真、评估函数集成到同一模型。

论文给 S2 域的判断：**L2 已经是常态，L3 / L4 在仿真里跑通，真实硬件上的 L5 还在起步**。

### S3：软件工程

软件工程之所以特殊，是因为**开发出来的工件和开发工件用的 agent 都是可执行代码**。这种双重可执行性让软件工程的 RSI 跑得最快：

- **改 coding-agent 实现和 harness**：SICA 让 agent 检查自己过往版本和基准结果、修改自己的 Python 代码库；Self-Harness 用执行轨迹找弱点，让同一底模对自己 harness 提小改；Agentic Harness Engineering 把 harness 暴露成可单独编辑/可回滚的文件；Ouroboros 把部署证据转成 agent 工具/上下文/提示的核心实现变更。
- **改经验、技能与协作**：SWE-Exp 把成功和失败轨迹都存进经验库，跨任务检索；CODESKILL 学一个管理策略维护多层级程序技能；EvoMAC 用测试反馈和"文本反向传播"改多 agent 工作流的角色提示与通信链。
- **改改进流程本身**：DGM 维护编码 agent 变体的 archive，让 agent 改自己实现后评估后代；HGM 进一步用"元生产力"分配评估预算给更有长期改进潜力的 agent；HELIX 在模型–harness 双环里改 harness 给当前执行用、积累验证轨迹改模型、再用改后模型重建 harness。

论文给 S3 域的判断：**L2 成熟、L3 正在出现、L4 基本缺席、bouned L5 偶有闪现**。

### S4：医疗

医疗 RSI 的特殊约束是**不能随便试错、反馈延迟、且高度依赖患者人群**。这导致医疗 RSI 几乎全部困在 L2 以内：

- **临床记忆与知识**：MedAgent-Zero 把成功病例存下来，反思失败病例提取诊断规则；DxEvolve 把诊断经历蒸馏成"诊断认知原语"；GSEM 用双层图组织经验，根据后续反馈重新校准节点质量与边权重；Evo-MedAgent 维护回顾性病例、程序启发式、工具可靠性三类互补存储。
- **临床推理策略**：EvoClinician 用 Diagnose–Grade–Evolve 循环，让 Actor 顺序问诊和检查、Process Grader 按临床收益打分、Evolver 据此修订下一例的提示与记忆；EvoMDT 把肿瘤决策拆给角色专门化的 agent，用专家评分更新提示、共识权重与检索范围。
- **临床工具与工作流**：MACRO 从固定医学影像工具中识别多步模式、合成成新高层动作；SkeMex 用 Read–Write–Assess–Govern 生命周期管理临床技能；TissueLab 让领域专家检查中间结果并提供修正，引导主动学习与工作流构造；HealthFlow 把完成的 EHR 分析转成持久保障、可复用工作流、代码片段。

论文给 S4 域的判断：**L1/L2 已经部署，L3 在模拟病人上跑通，L4 真实患者端开始探索但 L5 完全空白**。

## 五、工业落地证据：六套系统不是 PPT

论文第 5 章是全文最值钱的章节——6 套来自工业一线（不是论文 benchmark）的 RSI 系统：

1. **Theseus（Theseus Labs）**：环境–数据–模型协同进化。一份 30 任务 × 1280 评分标准的对照实验显示，把"干净的 workspace"换成"充满噪声的 workspace"，8 套前沿模型 + harness 配置的通过率下降 21.7–51.6 个百分点；同一模型 + harness 配上"重建环境"（一份 Collection Map 加一份 Event Log），rubric 评分比裸 workspace 高 18.65–39.67 个百分点。这是 L3 级别在生产场景的最早量化证据之一。
2. **Lark（字节跳动）**：把 RSI 的"地基"做成数据底座——企业协作场景里，文档/消息/会议/任务持续产生新信息，agent 既消费这些数据又产生交互轨迹。Lark 内部评测：基于图谱的检索把人类可用性从 52% 提到 65%、自动评测可用性从 47% 提到 56%。
3. **Humanlaya**：交付驱动的数据质量 RSI。两层循环——内循环改当前批次，外循环改质检系统本身。V0 到 V4 的内部对比：自动化修复后含关键缺陷的包比例从 9.0% 降到 3.7%，平均人工处理时间从 48 分钟降到 27 分钟。这是 L4 在数据生产线的真实案例。
4. **ModelBest**：Forge Engineering——零人工业 AI 工程。从空目录 + 参考脚本 + 模型规格出发，ForgeTrain 8 小时匹配 Megatron-LM v0.15 on H100、1.5–2.5 天超过它（对照 3–5 个工程师 6–12 个月）。报告的 MFU：MiniCPM4-0.5B 从 40.1% 提到 44.1%，8B 模型从 47.0% 提到 50.9%。ForgeStencil 在科学计算 kernel 上 1.15–1.9× 速度提升、中位 1.41× 端到端加速。这是 L5 在工程场景的雏形。
5. **Tencent Hunyuan Hyra**：经验驱动的搜索。Context Agent 把经验库重组为多样化灵感上下文，多个 Proposal Agent 异步消费上下文、构造解、跑沙箱；产物回写经验库。Recursive 对比 hyra-1.0 的 NanoChat Autoresearch：0.9109 → 0.9015（BPB ↓），NanoGPT Speedrun：77.5s → 76.4s（到 3.28 loss 的时间），SOL-ExecBench：0.754 → 0.771。
6. **Agent-Native Research Lab**：可验证研究基础设施。把"可验证"当成 RSI 的硬约束——没有独立验证的"改进"不算改进。这是论文反复回到的元命题。

**这 6 套系统的共同点**：没有一个是"完全无人的 RSI 循环"。每个都在关键决策（产品架构、目标定义、变更批准、风险释放）保留人类把关。论文给这种模式一个名词——**governed autonomy**——管治下的自主。

## 六、论文没回避的失败与陷阱

这一段是判断一篇综述真不真诚的地方。论文系统化地承认了 RSI 当前的三大结构性陷阱：

1. **安全继承（Safe Inheritance）**：持久性 ≠ 持续收益。Gödel Agent 在 100 次 MGSM 优化试验中有 14 次跑到比初始策略还差。必须配迁移测试、版本历史、回滚机制，否则"改坏一次，永久污染"。
2. **自主性归属（Autonomy Attribution）**：候选方案变好不等于系统变好。Darwin Gödel Machine 把 SWE-bench 子集从 20% 提到 50%，但 archive 维护与父代选择规则始终在 self-modification 之外。**打分涨了不等于 RSI 进步了**。
3. **可靠验证（Reliable Verification）**：反复访问同一个评估器会被钻空子。Anthropic 的自动研究实验里出现过随机种子 cherry-picking 和试图通过评估器查询抽取测试标签。RQGM（Red Queen Gödel Machine）的解决思路是：每 epoch 内冻结评估器，epoch 边界上把候选评估器对照独立 ground-truth anchor 验证。

论文还提了一个隐性陷阱——**experience corruption（经验污染）**。错误的经验或反馈会污染后续学习与获取决策。一个误导性的难度代理会偏爱不合适的任务；一个不准确的 judge 会奖励错误行为；持久记忆会把错误假设带进未来练习。这是 L3 / L4 反馈回路的结构性风险，论文 §3.4.4 单独成段。

把三大陷阱与经验污染放在一起读：它们都指向同一件事——**"看起来在改进"和"真的在改进"之间隔着可验证性这道墙**。这也直接连到下一节论文给出的方法论自觉：本文反复坚持把"结构性 L5"与"有效性 L5"分开取证，不是为了术语洁癖，而是因为现有 RSI 评估体系最容易混的就是这两层。

## 七、这篇综述的方法论自觉

论文第 1.7 节主动跟四个相关综述对照。这不是"我们比他们好"的姿态，更像是在承认：**现有 RSI 综述在"如何衡量递归"这件事上没有共识**。本文愿意把方法论选择摆在台面上，本身就是这篇综述能被工业界接受的原因之一。具体四个差异：

1. **以改进循环为单位**——之前的综述按 self-evolution 阶段/对象/时机/技术机制组织，本文按完整回路（什么触发、谁提、谁验、什么持久、谁继承）组织。
2. **以职责作为自主性判据**——之前用能力等级、协同演化、动态 agent 状态、AI-for-AI，本文用"从外部设计师转移到 AI 的改进决策"作为自主性度量。
3. **递归与表现分别取证**——之前的评测综述只看模型判断、agent 评估、rubric 学习、监管失败。本文区分**结构性递归**（被改的改进机制确实治理了下一轮）和**有效性递归**（被改的机制在可比预算和独立评估下产出更强的后继者）。
4. **跨运行环境比较同一组机制**——之前的修正、合成数据、终身学习、记忆、提示优化、工作流设计综述把组件拆开讲。本文按"反馈成本、验证、外部控制"四类，把同一组机制放进科学、具身、软件工程、医疗、工业五个场景做对照。

## 八、论文没说但适合同行带走的判断

下面几条不属于论文原话，是全文通读后的归纳，给准备拿这篇综述当路线图的同行：

1. **当前没有跑通完整 L5 的工业系统**。ModelBest 的 Forge Engineering 最接近，但"工程场景的可验证性"和"开放研究场景的开放性"是两个量级的难度。
2. **"HCI 还差多少"比"模型又涨了几分"更应当追踪**。评估这件事要从"哪个分高"切到"哪类能力的改进空间还敞开"，RSI 的研究优先级才有锚。
3. **L2 → L3 这一跳比 L3 → L4 更难**。前者要"用模型观察模型"，后者要"把外部环境反馈接进来"。前者是认知问题，后者是工程问题。
4. **L5 评测要落到 SEA-Eval / SEAGym 这类长程基准上**，单看 pass@1 不够。元生产力（meta-productivity）的可迁移性才是真指标。
5. **"管治下的自主（governed autonomy）"是当前唯一可信形态**。完全无人的 RSI 循环，论文自己都说"工程成本还看不到优势"。

## 九、什么场景该读这篇综述

- **AI 基础设施工程师**：第 2、3 节直接给可量化基线（HCI 表 + 五级自主性）。
- **做 coding agent / harness 的**：第 4.3 节和第 5.4 节（ModelBest）是直接抄作业的地方。
- **做 AI4Science 的**：第 4.1 + 第 5.1（Theseus）+ HypoForge / SIA / CORAL / SAGA 的对照清单。
- **做具身的**：第 4.2 + ENPIRE / SHAPER / ASPIRE 的 harness 进化方法。
- **做企业 AI 落地的**：第 5.2（Lark）+ 第 5.3（Humanlaya）的"数据底座 → 评估 → 归因 → 下一轮"四步法。
- **做评测的**：第 6 节三大陷阱 + SEA-Eval/SEAGym 的元生产力测量。
- **做 AI 政策 / 安全的**：第 5 节 6 套工业系统的"管治下的自主"模式 + 第 4.4 节医疗 RSI 的归因与人群约束。

## 十、一句话总结

> 当下所有的"AI 自己改自己"几乎都停在 L2 与 L3 之间。RSI 的判据不是分数涨多高，而是**改自己的方法被自己改、又被自己继承**——这条线至今还没有哪个工业系统完整跑通过。这篇综述最大的贡献不是给答案，是给了一张足够诚实的地图，让下一阶段的研究者知道哪些位置是空白、哪些位置被高估。

---

**事实溯源**：

- 论文 PDF：`arxiv.org/pdf/2609.11873v1`（75 页，322k 字符正文）
- 论文项目页：`theseus-labs-rsi.github.io`
- 工业案例引用：Meta Capacity Efficiency (FBDetect)、Anthropic Agentic Token Use、OpenAI HealthBench / Harness Engineering / GDPval、DeepSeek-V3.2 Post-Training、NVIDIA AIMO-2 / NeMo Curator / Cosmos TAO、Kimi K3、Qwen3.8-Max、GPT-5.6 Sol、GPT-6 Astra、Sonnet 5、Opus 5、Fable 5、GLM-5.3、GLM-4.5、Gemini 2.5 Pro、Kimi K2、Claude 3.5 Sonnet、GPT-4o、o1
- 五级骨架与 B0 基线：论文 §3.1–§3.7
- HCI 计算公式：论文 §2.1 公式 (2)(3)
- 改进循环解剖：论文 §2.2.1（AI system / system state / experience / target / improver / strategy / verifier / improvement / successor）
- 与邻近范式对比表：论文 Table 1
- 6 套工业系统：论文 §5.1–§5.6 + 附录 B
- 三大结构性陷阱：论文 §1.3（safe inheritance / autonomy attribution / reliable verification）
- experience corruption 概念：论文 §3.4.4

**作者立场声明**：本文为论文 arXiv 2609.11873v1 的中文化解读 + 路线图。所有事实陈述附带论文出处；所有"路线图意义"类判断属于作者评论，已用"值得"、"建议"、"属于"等弱化措辞区分。本文不构成任何工程或投资建议。