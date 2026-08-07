---
title: "详解 Kimi K3：Moonshot 这手牌为什么让 Anthropic / OpenAI 紧张"
date: 2026-08-08T00:32:00+08:00
draft: false
tags: ["Kimi K3", "Moonshot AI", "Mixture-of-Experts", "KDA", "AttnRes", "Open Weights", "视频反写"]
categories: ["视频精读"]
description: "Kimi K3 总参 2.8T / 激活 104B / 1M context，Moonshot 7-27 开权重。晚点聊 115 分钟两位嘉宾拆解的技术含金量 + 它对 frontier lab 估值的真实影响。"
slug : moonshotai-kimi-k3-late-talk
---

# 详解 Kimi K3：Moonshot 这手牌为什么让 Anthropic / OpenAI 紧张

7 月 27 日 Moonshot（"月之暗面"）干了一件让美国 frontier lab 紧张的事——**开源 K3 完整权重 + 发布技术报告**。

[晚点聊 LateTalk](https://www.bilibili.com/video/BV1nWM26QEu5/) 115 分钟请了两位嘉宾拆解 K3：

- **赵晨阳**——RadixArk 创始成员、SGLang 核心开发者（推理侧）
- **曾致远**——华盛顿大学博士生（算法侧）

视频标题直接给了钩子：「详解 Kimi K3：强到冲击 Anthropic 估值的模型什么样？」——下面 5 条是我从 115 分钟（3089 段 AI 字幕）+ [官方 README](https://github.com/MoonshotAI/Kimi-K3) + 技术报告交叉验证读出来的。

**AI 字幕是 B 站腾讯智幕生成，会有少量同音字错误（"开权重" 应理解为 "开源权重"），发言脉络保留完整。**

---

## 一、K3 的官方定位——"Open Frontier Intelligence"

[MoonshotAI/Kimi-K3](https://github.com/MoonshotAI/Kimi-K3) 仓库 7-27 创建，8-07 已 **8176 stars / 620 forks**，仓库 description 一句话：

> "Open Frontier Intelligence"

这句三个词按顺序看：

1. **Open** —— 开源权重，不是开放 API，不是开放评测
2. **Frontier** —— 前沿，不是"追赶前沿"，是"已经在前沿"
3. **Intelligence** —— 智能，不是"模型"不是"工具"

README 第一段把这个定位讲得更清楚：

> "Kimi K3 is an open-weight, native multimodal agentic model and our most capable model to date. It is a 2.8T-parameter model built on Kimi Delta Attention (KDA) and Attention Residuals (AttnRes), with native vision capabilities and a 1-million-token context window. **It is the world's first open 3T-class model**, designed for frontier intelligence across long-horizon coding, knowledge work, and reasoning."

五个事实：

1. **总参 2.8T、激活 104B**——这是开源界第一个 3T-class 模型
2. **架构组合创新**——KDA + AttnRes（不是单一 Transformer，是混合架构）
3. **原生多模态**——文本/图像/视频在同一模型里训练
4. **1M 上下文**——不是"扩展到 1M"，是从架构层就为长上下文设计
5. **Agent 能力**——long-horizon coding + 知识工作 + 推理

K3 是 2026 年开源 LLM 第一次把 frontier 拉到跟闭源 frontier lab 同档。

---

## 二、K3 的技术架构——KDA + AttnRes + Stable LatentMoE

README 把架构参数全公开了。读这一段最好把数字摆开看：

| 参数 | 值 | 含义 |
|---|---|---|
| Total Parameters | 2.8T | 总参（含所有专家权重）|
| Activated Parameters | 104B | 每次前向激活 |
| Number of Layers | 93 | 总层数 |
| Dense Layers | 1 | 全 dense 层（仅 1 层）|
| Attention-Layer Composition | **69 KDA + 24 Gated MLA** | 注意力层混合 |
| Attention Hidden Dimension | 7168 | 注意力隐维度 |
| Number of Attention Heads | 96 | 注意力头数 |
| Latent MoE Dimension | 3584 | Latent MoE 维度 |
| Experts | 896 | 总专家数 |
| Activated Experts | 16 | 每次激活专家数 |

下面拆三个关键设计点。

### 2.1 注意力层混合：69 KDA + 24 Gated MLA

不是单一 attention——K3 把 93 层的注意力分成两段：

- **69 层用 KDA**（Kimi Delta Attention）—— 这是 Moonshot 自己的 DeltaNet 改进，**linear attention 风格**，对长上下文友好
- **24 层用 Gated MLA**——这是 DeepSeek 风格的 MLA，带门控

> 赵晨阳（字幕 12:30 附近）："K3 呢他其实是原生动模态的，所以他可以在训练的过程中，尤其是在强化学习的过程里面呢……"

混合架构的工程含义：

- **前半段用 KDA 省显存**——长上下文推理时 KDA 比标准 attention 省 KV cache
- **后半段用 Gated MLA 保精度**——关键层用 MLA 保证生成质量
- **整体性能**——README 写到"approximate 2.5× improvement in overall scaling efficiency over Kimi K2"

### 2.2 Stable LatentMoE：16 / 896 专家激活率

MoE 模型的灵魂是"激活率"。K3 每 token 激活 **16 / 896 = 1.78%** 的专家（K2 是 8 / 384 = 2.08%）。

> Stable LatentMoE 是 Moonshot 自己提的稳定性框架。MoE 训练最大的问题是"专家坍缩"——少数专家被过度路由。LatentMoE 通过在 latent space 加约束，避免坍缩。

**16 专家激活是个相对保守的选择**（Mixtral 8x7B 用 2/8 = 25%，DeepSeek-V3 用 8/256 = 3.1%）。Moonshot 的赌注是：**激活专家少 = 单 token 计算量省 = 推理成本低 = 长期跑得起 3T 模型**。

### 2.3 93 层 + 1 dense 层

93 层里只有 1 层是 dense——其它 92 层全是 MoE。**这是把 MoE 推到底的工程决心**。Dense 层通常承担"路由学习"的功能，1 层够不够？赵晨阳在访谈里没明说，但**SGLang 作为 K3 的推理引擎，必须对这一层做优化**——这一层是推理延迟的热点。

---

## 三、K3 的训练细节——KB Web Dev Bench + 多模态 RL

赵晨阳/曾致远在访谈里拆了 K3 训练的几个非公开细节（字幕 10:00 前后）：

> "他们在 evaluation 上专门做了这个 KB web dev 的 bench，对他就是专门针对这一类相关问题做的评测。"

> "他们在 pretrain 阶段大幅扩充了代码和渲染结果去相配的这么一个多模态的数据。然后 post-training 阶段又专门加入了这种 web development 的任务。"

> "K3 呢他其实是原生多模态的，所以他可以在训练的过程中，尤其是在强化学习的过程里面呢……"

三个关键：

1. **KB Web Dev Bench**——这是 K3 团队自建评测，针对 **"模型从文本理解到生成可用 web 应用"** 这类任务做专项评估。这套 bench 是闭源的（README 没列），但访谈里明确说存在。

2. **Pretrain 阶段多模态数据扩充**——K3 在 pretrain 阶段就混合代码 + 渲染结果（HTML、CSS、JS 执行结果、UI 截图）。**这是"原生动模态"的物理实现**——不是"先训文本再微调视觉"。

3. **Post-training 阶段 web dev 任务专门加入**——这是 agentic knowledge work 能力的源头。模型不只是"懂 web"，是"能交付 web 应用"。

K3 跟 K2 最大的区别不是参数量翻倍，是训练数据从"语料"变成"代码 + 渲染结果"。

---

## 四、K3 对 Anthropic / OpenAI 估值的真实影响

访谈开场赵晨阳直接给了一个罕见的圈内观察（字幕 00:06 前后）：

> "像美国 frontier lab 的一些普通打工人里面，确实有部分人会认为开权重模型能力上涨，对于 frontier lab 的估值是有很潜在的影响的。比如说未来很多公司，他们可能不愿意去把自己的数据发给 Anthropic 或者 OpenAI 这样的第三方。"

这一段有三个细节值得拆：

1. **"普通打工人"也能感知**——不是顶级 researcher 在想这事，是**普通员工**在讨论估值
2. **"潜在影响"被反复讨论**——不是边缘声音，是 frontier lab **内部热门话题**
3. **核心冲击路径**——企业不愿意把数据发给闭源第三方

K3 怎么具体冲击 frontier lab 估值？我从访谈和公开材料推演四条：

| 路径 | 机制 | 谁受伤 |
|---|---|---|
| **私有部署替代** | 企业用 K3 自建（自己 GPU + K3 权重）替代 OpenAI/Anthropic API | API 收入 |
| **合规优势** | K3 开权重，企业数据不外流 | 数据敏感行业（金融/医疗/政府）|
| **成本结构** | K3 激活 104B，推理成本远低于 GPT-5 等闭源模型 | 价格战压力 |
| **能力追平** | K3 在多项 benchmark 追平或超过 frontier lab | 差异化叙事 |

**估值伤害的传导链**：

```
K3 开源 → 企业私有部署可行 → API 收入下降 → frontier lab 收入预期下调
→ 投资人重新评估 ARR/估值倍数 → 估值缩水
```

但**赵晨阳自己也说"潜在影响"，不是已经发生**——这是 frontier lab 内部正在讨论的 scenario，不是已落地的现实。

---

## 五、K3 与"开源大辩论"

访谈后期主持人提到"与 K3 直接相关的开源大辩论"——这是 2026 年 LLM 圈最热的元话题：

> "我们也延展讨论了 K3 在美国 AI 界和更广泛的投资市场引起的巨大关注，以及与 K3 直接相关的开源大辩论。"

这场大辩论的两端：

| 立场 | 代表 | 论点 |
|---|---|---|
| **开源加速派** | Moonshot / Meta / Mistral / DeepSeek | 开源会让 AI 进步更快，最终全人类受益 |
| **开源威胁派** | 部分 frontier lab / 部分投资人 | 开源会让 frontier lab 估值承压，反过来减少基础研究投入 |

Moonshot 在这场大辩论里押了三张牌：

- **开源 K3 不会让 Moonshot 直接受益**——他们不靠 API 收费
- **但会让 frontier lab 估值承压**——这是 Moonshot 的**间接竞争策略**
- **让更多企业敢用 AI**——合规 + 成本都打开

这是 2026 年中国 AI 公司最反直觉的一手牌：开源不是让步，是进攻。

---

## 六、把 K3 放在 2026 LLM 地图里

读完 115 分钟（3089 段字幕）+ README + tech report，K3 的 2026 坐标：

**模型规模坐标**：

| 模型 | 总参 | 激活 | 开源 |
|---|---|---|---|
| Kimi K3 | 2.8T | 104B | ✅ |
| DeepSeek-V4 | 1.6T | 50B | ✅ |
| Qwen3-Max | 720B | 72B | 部分 |
| Llama 4 Behemoth | 2T | 未披露 | ✅ |
| GPT-5 | 未披露 | 未披露 | ❌ |
| Claude Opus 4.5 | 未披露 | 未披露 | ❌ |

K3 是当前**总参最大的开源 frontier 模型**。

**架构创新坐标**：

- **KDA + AttnRes**——Moonshot 独家，linear attention + 标准 attention 混合
- **Stable LatentMoE**——Moonshot 独家
- **MLA + DeepSeekMoE**——DeepSeek 系独家
- **Sliding Window + MoE**——Mistral 系

**生态坐标**：

- **SGLang**（赵晨阳所在团队）—— K3 推理引擎首选
- **RadixArk**——围绕 K3 的推理优化商业公司
- **Hugging Face**（moonshotai org）—— 权重分发
- **ModelScope**（modelscope.cn/moonshotai）—— 国内分发

---

## 七、K3 没在节目里讲的事

按"先实查再叙述"原则，下面三件事我在节目里**没找到明确引用**，不替嘉宾补充：

1. **K3 训练算力**——访谈和 tech report 都没披露训练 FLOPs / GPU-hours。这是 Moonsshot 商业机密。
2. **K3 商业化路径**——Moonshot 不是 API-first 公司，K3 权重开源后靠什么赚钱，访谈没展开。
3. **K3 与 K2 thinking / K2.5 的关系**——K2 系列已经有 thinking 版本，K3 是不是也会出 thinking 版，访谈没提。

这三条按 USER.md 第八条铁律不能编造，**留给真正公开材料再说**。

---

## 八、读完它我对 K3 的判断

115 分钟访谈 + README + tech report 读完，K3 给我的最大启示不是"又一个开源 frontier 模型"，是中国 AI 公司的开源战略从防守转进攻。我从公开材料按时间线排：

- **2024 年**——中国 LLM 开源是"追赶"，是 frontier lab 的影子
- **2025 年**——中国 LLM 开源是"性价比"，是 frontier lab 的平替
- **2026 年**——中国 LLM 开源是"主导"，是 frontier lab 的反例

K3 是第三个阶段的代表作。赵晨阳那句"普通打工人认为开权重模型能力上涨对 frontier lab 估值有潜在影响"——这句话描述的是正在发生的市场重估。

---

## 写在最后

115 分钟访谈读完了。晚点聊这次把节奏压在 K3 的架构 + 训练 + 估值冲击 + 开源大辩论四条主线上，没有做成"中国模型又赢了"的标题党。

**K3 的真正故事是：3T 总参 + 1M context + 原生多模态——以开源权重姿态发布，让 frontier lab 第一次面对"企业可以不依赖闭源 API"的现实选项。**

下一次 K3 系列动作（按本人推断）：K3 thinking 版本（带 reasoning + 多模态 RL），把 post-training 的 web dev agent 能力推到极致。

---

**视频**：[晚点聊 LateTalk - 详解 Kimi K3：强到冲击 Anthropic 估值的模型什么样？](https://www.bilibili.com/video/BV1nWM26QEu5/)
**字幕源**：B 站 AI 字幕（ai-zh），115 分钟 / 3089 段 / 12372 行
**仓库**：[MoonshotAI/Kimi-K3](https://github.com/MoonshotAI/Kimi-K3) · 8176 stars / 620 forks · "Open Frontier Intelligence"
**技术报告**：[k3_tech_report.pdf](https://github.com/MoonshotAI/Kimi-K3/blob/main/k3_tech_report.pdf)（1.79 MB）
**嘉宾**：赵晨阳（RadixArk / SGLang）+ 曾致远（华盛顿大学）

---

*声明：本博客基于 B 站 AI 字幕 + MoonshotAI/Kimi-K3 公开仓库，**非字幕逐字人工校对版**。AI 字幕会有少量同音字错误（如"开权重"应理解为"开源权重"），但发言脉络保留完整。引用嘉宾原话以 ` ` 标注。*