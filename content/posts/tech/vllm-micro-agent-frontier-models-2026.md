---
title: "Micro-Agent：在 Model API 内部用协作打 frontier model——vLLM Semantic Router 拆解"
date: 2026-06-30T15:58:00+08:00
lastmod: 2026-06-30T16:08:00+08:00
draft: false
slug: "vllm-micro-agent-frontier-models-2026"
categories: ["技术剖析", "AI 基础设施", "LLM 推理"]
tags: ["vllm", "semantic-router", "micro-agent", "model-routing", "agentic-routing", "model-api", "ai-infrastructure", "serving-layer", "ensemble", "评分聚合"]
description: 把 vLLM Semantic Router 的 micro-agent 设计完整拆开：5 种 Looper（Confidence / Ratings / ReMoM / Fusion / Workflows）在 router 里如何取代「换更大的模型」，Auto Recipes 怎么用一个模型名对外暴露 4 类协作，3 个 benchmark 记分牌怎么读，以及为什么 frontier model 的下一战场在 router。
---

## 学习目标

读完这篇文章你应该能回答：

- **vLLM Semantic Router 的 micro-agent 设计想解决什么**：为什么 frontier model 之间的差距在从权重迁移到 router 层
- **5 种 Looper 的工作原理与边界**：Confidence / Ratings / ReMoM / Fusion / Workflows 各自适合什么任务、不适合什么任务
- **Auto Recipe 怎么用一个 model name 暴露多种协作**：信号提取 + task-shape 投影 + 路由决策
- **记分牌怎么读**：VSR Closed vs VSR Hybrid 在 3 个 benchmark 上的数字能推出什么、不能推出什么
- **什么时候不要上 micro-agent**：延迟、成本、工具需求、长链规划的边界
- **怎么把它用到自己的推理服务里**：第一步该看什么、第二步该做什么

## 适合谁读

- 自己做推理服务、需要决定多模型协作策略的 infra / 平台工程师
- 在评估 "Fugu / Semantic Router / LangGraph / CrewAI" 这类方案的架构师
- 对 AI serving stack 演化方向感兴趣的 LLM 系统研究者
- 想理解 "协作" vs "更大的模型" 这条新轴线的应用层工程师

## 一、为什么 vLLM 这次没追新模型

所有人都在等下一个 frontier model。

但 vLLM 这次讲的不是"我们又发了一个 70B"。他们讲的是一个更底层的判断——**frontier model 之间的差距，正在从权重迁移到它前面那一层**。

Routers 正在变成 AI 推理的 control plane。第一代 router 的活很朴素：把对的请求路由到对的模型。这件事在生产里已经很重要——AI 推理不再是"一个模型打天下"。router 能省钱（判断什么时候该上前沿模型、什么时候开源/本地就够）、能把安全策略变成可执行的事（把敏感请求送到更严的模型、过滤器、复核链路）、能协调云与边（隐私/低延迟意图留在本地、难的活升级到云端）。

这些都是重要的活。

但下一件更有意思：

**Router 可以让模型变好。**

不改权重。不让每个应用都自己搭一套专属 agent 图。把一次 model API 调用变成 serving 层里一场**有边界的协作**。

Fugu 一出来声音那么大，是因为它把"模型可以是一个门面、门面背后是一支队伍"这个想法做成了商业产品。围绕这个想法的研究——Fugu 技术报告、Conductor、Trinity 这些协调论文——给"orchestration"补了一套可用的语言。

但 vLLM Semantic Router 的愿景不同，差在抽象放在哪：协作不该只活在一个商业端点里，也不该只活在某个应用专属的 agent 图里。它应该成为**开放的 serving 原语**。

vLLM Semantic Router 把这件事带进了开放的 serving 层。用户的请求还是指向一个模型：

```json
{
  "model": "vllm-sr/auto",
  "messages": [{"role": "user", "content": "..."}]
}
```

在那个稳定的 model identity 后面，router 可以挑 recipe、扇出到 worker、收集法定人数、验证分歧、综合出最终答案、修补输出契约、最后按 OpenAI 兼容的格式返回一条正常响应。

要点不是把复杂度暴露给调用方。

**要点是让协作感觉像一个模型。**

## 二、Sakana Fugu 给的启示：模型是门面，门面背后是队伍

在进入 vLLM 的具体设计之前，先把 Fugu 这一脉的脉络理清——vLLM 的 micro-agent 思路直接站在这条线上。

Fugu 的论文（arxiv 2606.21228）核心论断是：商业部署里所谓的"模型"实际上是一个**多组件的协作系统**——权重只是其中一项，更大一部分是 inference-time 的路由、升级、聚合、验证。Fugu 把它打包成"一个模型名"卖给客户，背后的实现是 planner + worker + judge 的编排。

这个想法的研究语言来自协调类论文：

- **Conductor**（arxiv 2512.04388）：把多模型协作抽象成"指挥-执行"的范式，强调"何时升级、升级到谁"是显式控制变量
- **Trinity**（arxiv 2512.04695）：把 ensemble 拆成"广度采样—证据综合—最终裁决"三段，强调综合器必须有明确的输入契约

这些论文给出了一个共同的语言——"模型"是一个**由多个推理节点组成的可调系统**。Fugu 的产品价值在于：把这件事藏在一个 model name 后面卖出去。

vLLM 的判断是：**这个藏法不该只属于一家商业 API**。一个 model API 后面跑 5 个候选 + 一个综合器这种事，本质是 serving 层的活，不该被锁在某个商业后端里。它应该是任何 vLLM 部署都能用的能力——开箱即用、可观测、可调参。

这是 micro-agent 这个词的来源：**小（在一次请求内完成）、像 agent（带协作结构）、但属于 serving runtime（不是应用层逻辑）**。

## 三、vLLM Semantic Router 的差异化抽象

把 vLLM 的方案跟其他几条路线对一下，能更清楚它到底在做什么：

| 路线 | 抽象放哪 | 谁拥有协作逻辑 | 用户看到什么 |
|------|----------|----------------|--------------|
| 单一 frontier API | 商业后端内 | API 提供方 | 一个黑盒 model name |
| 应用层 agent 框架（LangGraph / CrewAI） | 应用代码 | 每个应用自己 | 复杂图 + 多 API key |
| vLLM Semantic Router | **serving 层** | 部署 vLLM 的团队 | 一个 model name |

第三列的差异是核心。**用户看到的就是一个 model name**——`vllm-sr/auto`，OpenAI 兼容。协作的复杂度、worker 的数量、rejection 策略、合成器选择、token 预算——全部在 router 内部。

这件事的工程意义在于：协作是**基础设施**，不是**应用代码**。

基础设施的语义意味着：模型别名、provider 策略、credentials、成本元数据、信号、决策、重试、超时、trace、OpenAI 兼容响应——所有这些东西 router 本来就拥有。micro-agent 只是把这些已有的能力**重新组合成一次协作**。

不需要每个应用都重新发明轮子。

## 四、整体架构：5 种 Looper 在 router 里怎么跑

在 vLLM Semantic Router 里，**Looper 就是 micro-agent 的执行运行时**。

一条请求以普通的 chat completion 进入 router。router 提取信号、把它们投影到 task-shape 或 risk band、匹配一个决策、然后选一个算法。算法可以是普通的"单模型路由"，也可以是一条**Looper 路由**。

目前主要的 Looper 模式有 5 种：

- **Confidence**：顺序升级循环。先试便宜的候选、测置信度、不够再升级
- **Ratings**：有上限的扇出循环。在 `max_concurrent` 硬上限内并行多个候选、用 rating-aware 权重聚合
- **ReMoM**：重复的 mixture-of-model 推理。扇出广度采样、等到足够的成功响应、跑最后一段综合
- **Fusion**：panel-judge-final 模式。多个独立响应变成证据、judge 看完给 finalizer
- **Workflows**：micro-agent workflow runtime。支持静态角色或动态 planner、在有界 worker 步数内执行、最后综合出响应

一个 Looper 在 router 内部有显式的结构。下面是一个简化版的 recipe 配置——实际的 router recipe 一般是 YAML，能直接打到 `vllm-sr/auto` 模型名后面：

```yaml
# 简化版 recipe 结构（实际由 vLLM Semantic Router 配置系统读入）
recipes:
  gpqa-diamond:
    type: remom
    candidates:
      - model: open-model-A
      - model: open-model-B
      - model: open-model-C
      - model: closed-frontier-1
    quorum:
      min_success: 3        # K 路成功后才综合
      timeout_ms: 12000
    synthesis:
      model: closed-frontier-1
      output_contract: "ANSWER: X"   # 强制合同
      max_tokens: 256
    fallback:
      on_synthesis_fail: best_evidence   # 降级到最佳有效证据
    budget:
      max_tokens_total: 8000
      max_latency_ms: 15000

  livecodebench:
    type: workflows
    planner:
      model: closed-frontier-1
      workers_allowed: [open-coder-7b, open-coder-13b, closed-frontier-1]
    steps:
      - role: patcher
        max_attempts: 3
      - role: verifier
        on_test_fail: retry_patcher
      - role: finalizer
    budget:
      max_steps: 8
      max_parallelism: 2
```

**两个细节值得展开**：

1. **`max_tokens_total` 和 `max_latency_ms` 是 router-level 强约束**——单次请求超过任意一个上限，router 直接 abort。这跟应用层 "try-except" 不同，是**基础设施级的死线**。
2. **`on_synthesis_fail: best_evidence` 是关键降级**——综合器失败但 worker 出了有效证据时，路由不必塌成 API 错误。这就是 ReMoM 跟"把请求当成 4 路独立调用然后全挂了"的差别。

Looper 在 router 里的执行时序大致是：

```
请求进入 → 信号提取 → task-shape 投影 → 匹配 recipe → 
  Looper 调度 → worker 派发（带 trace ID）→ 收集响应 →
    法定人数检查 → 综合 / 评分 / judge → 输出合同校验 →
      失败降级 或 返回 → trace 折叠到 OpenAI 响应里
```

trace 是 router 的 first-class 工件——每个 Looper 实例有一个 trace_id，从 worker 派发到综合完成全程可追。这跟应用层 agent 框架"日志在应用里"完全不是一回事。

![router-capability-layer](https://vllm.ai/blog-assets/figures/2026-06-29-micro-agent-frontier-models/router-capability-layer.png)
图 1：router 正在从"模型选择"走向"能力构造"

![looper-micro-agents](https://vllm.ai/blog-assets/figures/2026-06-29-micro-agent-frontier-models/looper-micro-agents.png)
图 2：Looper 算法在 router 里跑，但 model API 这层接口保持不变

实现细节上，一个 Looper 不是一个"多问几个模型"的口号——它是一个**带预算、带拓扑、带 trace、带失败策略的小运行时**。下面 5 节把每种 Looper 拆开。

## 五、Confidence：成本感知的顺序升级

Confidence 是**为成本敏感场景设计的循环**。它先从一个更小或更便宜的候选开始，再评估输出是否够自信。

置信度信号可以来自：

- token 级的 log probability
- logprob margin（top-1 与 top-2 的差）
- 混合分数
- 自校验
- AutoMix 风格的 entailment 验证器

分数过线 → router 立刻返回。分数不够 → 路由升级到下一个候选。重要的不是"能升级"这件事——而是**升级变成了一条显式 router 策略**：阈值、失败行为、停止条件都是可见的、可调的。

![confidence-loop](https://vllm.ai/blog-assets/figures/2026-06-29-micro-agent-frontier-models/confidence-loop.png)
图 3：Confidence 把"升级"变成一条可测的停止策略

这条循环最常见的部署形态：

- **A 类查询走小模型**：FAQ、检索型问答、模板化任务——小模型置信度 > 0.9 直接出
- **B 类查询走中模型**：需要一定推理的对话——小模型置信度不够时升级一次
- **C 类查询走大模型**：复杂推理、长上下文、敏感领域——直接到 frontier，中间不试小模型

Confidence 信号的取值范围和阈值设计在生产里有一些隐性约定：

```
信号源              典型取值范围      推荐升级阈值      适用
─────────────────────────────────────────────────────────────
token logprob       -5.0 ~ 0.0       < -1.5 升级       MCQ、短答
logprob margin      0.0 ~ 5.0        < 1.2 升级         双候选区分
混合分数            0.0 ~ 1.0        < 0.7 升级        复杂推理
自校验              pass/fail        fail 升级          模型自评强
entailment          entail/neutral   neutral 升级      答案在原文里
```

阈值不是凭感觉调的——通常从历史请求的"置信度 vs 正确率"曲线读出来：把过去一周的请求按 logprob 分桶，每个桶统计实际准确率，**准确率开始 < 业务阈值（如 0.85）的那个 logprob 值，就是升级阈值**。

Confidence 的代价是**有界延迟**——所有升级是串行的，最坏情况 = sum(每级延迟)。在 P99 延迟敏感的链路里这是约束，所以 router 通常会把 Confidence 限制在 2-3 级以内。一个常见的反模式是把 Confidence 配成"5 级升级"——单次请求延迟上限直接变成 5 × 单模型延迟，下游服务扛不住。

## 六、Ratings：硬上限内的并行质控

Ratings 是**受控的 ensemble 循环**。它并行启动多个候选，但只跑到配置的 `max_concurrent` 上限。

这件事看起来"不就是并发了"，但有具体的工程边界：

- **没硬上限的并行 = 每次请求都变成 N 路扇出**，N 一旦失控就退化成"DoS 自己"
- **有 `max_concurrent` 之后，operator 拿到了一个旋钮**——想保质量可以拧大，想保成本可以拧小

router 收集成功的响应、按 rating-aware 权重聚合、按路由策略处理失败。Ratings 在生产里特别适合 A/B 风格的评估、ensemble 策略、以及 operator 已经对每个候选的质量信号有先验知识的路由。

![ratings-loop](https://vllm.ai/blog-assets/figures/2026-06-29-micro-agent-frontier-models/ratings-loop.png)
图 4：Ratings 让多候选执行保持有界、且对 rating 敏感

具体来说，rating 的来源可以是：

- **历史准确率**：每个候选在过去 N 次同类任务上的成功率
- **置信度日志**：每个候选输出的 token 概率均值
- **业务标签**：业务侧给某些 query 打的"必须用模型 A"标签
- **成本权重**：在多目标优化里把"成本"作为反向 rating

聚合策略一般是加权投票或 score fusion，关键点在于**失败响应怎么算**——Ratings 默认会把失败响应从分母里扣掉（不是当 0 分），避免一个挂掉的 worker 拖累整个 ensemble。

## 七、ReMoM：广度采样 + 综合器

ReMoM 在任务**推理方差大**且**输出格式必须守住**的场景特别有用。

它的工作流：

1. **广度扇出**：发 N 路独立推理请求
2. **法定人数等待**：等到 K 路成功响应（K ≤ N，留出失败容差）
3. **合同综合**：让一个综合器把 K 路证据合并成符合输出契约的答案
4. **失败降级**：如果综合器失败但前面 worker 出了有效证据，路由不必塌成 API 错误——可以回退到"最佳有效证据"作为响应

![remom-loop](https://vllm.ai/blog-assets/figures/2026-06-29-micro-agent-frontier-models/remom-loop.png)
图 5：ReMoM 把广度、法定人数、综合、降级都做成 serving-time 的控制项

ReMoM 跟 Ratings 的差别：

- **Ratings 是横向比较**——N 路投票、谁一致听谁的
- **ReMoM 是纵向综合**——N 路采证、综合器收口

前者适合"答案唯一、需要压低方差"的场景（如客观题、检索型），后者适合"答案需要被构造、需要守住合同"的场景（如长文本生成、复杂代码、约束输出）。

ReMoM 的成本曲线是**先摊薄、后综合**——单次请求的 token 总量 = N × (单路 token) + 综合器 token。所以 N 一般不超过 5-7，否则综合器的输入长度会突破它的上下文窗口。

## 八、Fusion：把分歧变成证据

Fusion 的 bet 不一样。**有用的对象有时候不是"平均答案"，而是分歧的结构**。

独立 panel 答案成为证据。judge 看到一致、矛盾、独到见解，finalizer 返回一个答案——trace 折叠在 API 后面。

Fusion 在以下场景特别合适：

- **存在合理竞争路径的 hard MCQ**：多个模型对"为什么是 B 而不是 A"有不同推理链
- **长文本专家判断**：需要把不同维度的反馈综合成最终评价
- **精确答案任务**：单模型的"自信但错"很脆，多个独立证据能压低单点错误率

![fusion-loop](https://vllm.ai/blog-assets/figures/2026-06-29-micro-agent-frontier-models/fusion-loop.png)
图 6：Fusion 不藏分歧——它把分歧变成证据

Fusion 跟 ReMoM 的差别：

- **ReMoM 的综合器是"答案生成器"**——它要 produce 一个新答案
- **Fusion 的 judge 是"分歧分析器"**——它要 explain 一致/矛盾/独到，最后 finalizer 用这个分析收口

所以 Fusion 的输出质量高度依赖 judge 的能力——一个弱的 judge 会让 Fusion 退化成"几个弱答案的加权平均"。在生产里 Fusion 通常要求 judge 是一个 frontier model。

## 九、Workflows：角色预算下的工作流

Workflows 是**最像 agent 的模式**，也是边界必须最严的模式。

- planner **只能选白名单里的 worker 模型**
- plan **必须先校验**
- step **被 max steps、max parallelism、timeout、error policy 限制**
- 最终响应 **仍要满足输出契约**

对 SWE 风格任务来说，这意味着 router 可以表达 planner、patcher、verifier、finalizer——但不让应用自己拥有专属 agent stack。对生产服务来说这个区分很关键：**循环很强大，但仍由基础设施管着**。

![workflows-loop](https://vllm.ai/blog-assets/figures/2026-06-29-micro-agent-frontier-models/workflows-loop.png)
图 7：Workflows 给 router 一个有界的角色系统，不是一个无界的自主 agent

Workflows 跟前面 4 种循环的关键区别是**plan 的存在**。Confidence / Ratings / ReMoM / Fusion 都可以写成"router 内部固定图"——不需要动态决策。Workflows 不行：planner 必须先想好"这一步派给谁、下一步等什么条件"。

Workflows 的强约束不是凭空加的——它的存在理由是 planner 一旦能自由发挥，router 就失控了：

- **planner 不能发明 worker**——只能从白名单选
- **plan 必须先验**——校验通过才执行
- **step 必须有上限**——max steps 是硬天花板
- **超时必须可中断**——任何 worker step 都能被 cancel

这些约束的目的不是限制能力，而是**让 router 仍拥有对资源、延迟、成本的最终控制权**。

## 十、Auto Recipes：一个模型名 = 多种协作

公开接口还是一个 model name——`vllm-sr/auto`。在 router 内部，**用信号和投影来选对的循环**。

难度、风险、合同压力、延迟、成本——不再是 prompt 里的注释，而是**路由事实**，可以挑 Confidence、Ratings、ReMoM、Fusion、Workflows、或者回退路径。

![auto-recipe-loop](https://vllm.ai/blog-assets/figures/2026-06-29-micro-agent-frontier-models/auto-recipe-loop.png)
图 8：Auto recipes 让信号挑协作模式，但保持一个 model identity

这就是"agent as app logic"和"micro-agent as serving runtime"的差别：

| 维度 | App-level agent | Router-level micro-agent |
|------|-----------------|--------------------------|
| 谁拥有图 | 应用代码 | router 配置 |
| 谁控制预算 | 应用层 hardcode | router 策略 |
| 谁看 trace | 应用日志 | router trace + 业务日志 |
| 谁能换协作 | 改应用 + 重发版 | router 调参 |

router 控制**预算、策略、拓扑、trace、失败模式**——这是 micro-agent 的归属问题。

一个具体的 Auto Recipe 例子：识别到 prompt 是 GPQA 风格 → 选 ReMoM + 4 路广度 + 1 个 frontier 综合器 + 严格 ANSWER: X 合同守住。识别到 prompt 是 LiveCodeBench 风格 → 选 Workflows + planner/patcher/verifier 角色。识别到 prompt 是普通对话 → 选 Confidence + 1-2 级升级。

信号提取这一步本身也值得拆开。router 拿到 prompt 后会跑一层轻量分析（不调模型，而是基于 token 序列的特征）：

```
提取阶段         信号              典型实现
─────────────────────────────────────────────────────────────
token 分析       prompt 长度       token 数直方图
语义启发         任务类型          关键词 + pattern 匹配
                  （代码/数学/对话）
风险识别         敏感词           分类器 / 正则
合同压力         输出格式要求      解析用户 schema
难度预估         推理复杂度        启发式评分
成本预算         token 上限        路由策略读
```

这一层**不是模型调用**——本质是"prompt 的元数据提取"。它的目的是让 router 在派给 worker 之前就知道"这条请求大致需要什么级别的处理"。这一步如果不显式做，router 就只能用"所有请求同等对待"——这就退化回单模型路由了。

## 十一、关键洞见：没有万能循环，循环必须"长得像任务"

从 vLLM 的 eval 工作里得到的最重要教训不是"哪个算法总是赢"。

正好相反：

**最好的循环是 task-shaped 的。**

GPQA-Diamond 要严格的多选答案保存。LiveCodeBench 要可运行代码 + 隐藏测试的鲁棒性。Humanity's Last Exam 要分歧解决 + 精确答案格式。SWE 风格任务需要 planner、patcher、verifier、finalizer。

`vllm-sr/auto` **不应该**等于"总是跑最大的循环"。它应该等于：**挑最贴合这个任务的 recipe**。

![benchmark-shaped-recipes](https://vllm.ai/blog-assets/figures/2026-06-29-micro-agent-frontier-models/benchmark-shaped-recipes.png)
图 9：信号和投影让 router 挑 benchmark-shaped 的协作模式

在 vLLM 的 recipe 里，shape 是显式的：

- **GPQA-Diamond** 把难的科学多选 prompt 路由到 ReMoM recipe + 严格 `ANSWER: X` 保存
- **LiveCodeBench** 先识别约束、starter code、标准输入、float tolerance、超时风险、隐藏测试风险，然后选 code-shaped 的循环
- **HLE** 先识别形式推理、分歧风险、长上下文、精确答案压力，然后在更深 ReMoM、更小 Fusion、回退路径之间选

router-side 协作比 prompt engineering 走得远，因为**prompt 只是 recipe 的一个维度**。recipe 还要定义：模型池、模型角色、推理力度、并发度、法定人数、超时、综合模型、回退策略、输出契约、可观测性标签。

把这些变量从"应用代码里的注释"提到"router 里的 first-class 概念"——是 micro-agent 的真正价值。

## 十二、记分牌怎么读：数字是证据但不是全部

vLLM 在三个难 benchmark 上 eval 了当前的 closed-model recipe。数字有用——它说明这个想法不只是审美。

![three-eval-scorecard](https://vllm.ai/blog-assets/figures/2026-06-29-micro-agent-frontier-models/three-eval-scorecard.png)
图 10：VSR Closed / VSR Hybrid 跨 LiveCodeBench、GPQA-Diamond、Humanity's Last Exam 的记分牌

记分牌术语：

- **VSR Closed**：recipe 只用 closed-model 后端
- **VSR Hybrid**：recipe 混用 open 和 closed 模型——在高风险判断、修复、综合、回退的位置用更强的 closed 模型

| Benchmark | VSR 记分牌行 | 分数 | 参考基线 |
|-----------|--------------|------|----------|
| LiveCodeBench（2025-01 至 2025-04） | VSR Closed | 92.6 | Fugu Ultra 92.0 / Fugu 90.3 / GPT-5.5 90.7 / Opus 4.8 90.3 |
| GPQA-Diamond | VSR Closed | 96.0 | Fugu Ultra 95.5 / Fugu 95.5 / Gemini 3.1 Pro 94.3 / GPT-5.5 93.6 |
| Humanity's Last Exam | VSR Closed | 50.0 | Fugu Ultra 50.0 / Fugu 48.5 / Gemini 3.1 Pro 45.0 |
| Humanity's Last Exam | VSR Hybrid | 47.1 | GLM-5.2 40.5 / Qwen3.7 Max 41.4 / GPT-5.5 41.4 |

**记分牌要小心读**。它**不**等于"每个请求都应该用每个 closed 模型"——那是错误的产品。

它真正说明的是这件事：**router 拥有的协作能造出一个比底下单独调用更强的 model identity**。它能在保留一个 API 表面的同时打过或追平 frontier 单模型基线。

产品形态对应 4 条线：

- **用户看到**：一个 model name
- **operator 控制**：recipe
- **系统能**：在不换客户端集成的前提下变好
- **生态能**：open 和 closed 模型在同一个 serving 抽象下参与

### 关于这个记分牌必须说明的几件事

**1. 它测的是模型协作，不是模型本身**

VSR Closed 在 LiveCodeBench 拿到 92.6，意思是"用 4-5 个 closed 模型协作的 recipe"在这个 benchmark 上能打过任何一个单模型基线。这不能用来推断 VSR 团队有"更强的 92.6 模型"——他们有一个**更好的协作 recipe**。

**2. Hybrid 不一定赢**

在 HLE 上 VSR Hybrid（47.1）低于 VSR Closed（50.0）。这直接说明 **HLE 这种"精确答案 + 长推理"任务，judge 和综合器都必须是 frontier 级别的**——open 模型在这一档拉不动。

**3. 不读 trace 不算真正评估过**

记分牌只显示最终分数。recipe 优劣藏在 trace 里——一个 50.0 分的 recipe 可能因为综合器把 4 路 49 分答案合并成 50；一个 47.1 分的 recipe 可能因为综合器把 4 路 35 分答案合并成 47。trace 告诉你哪个 recipe 更稳、哪个 recipe 走到 50 分的成本更低。

**4. 不算账就不算完整**

VSR 的 50.0 在 HLE 上追平 Fugu Ultra——这背后是一个用户发一个请求、router 跑了 4-5 个 frontier 调用、消耗的 token 总量是单模型的 4-5 倍、延迟是 P99 的几倍。这个数字在产品里意味着什么（成本结构、延迟分布、能跑什么规模的流量），记分牌不告诉你。

## 十三、这给模型服务带来什么变化

老一代的 serving stack 是被动的——接一个 model name、把请求送进后端。

下一代 serving stack 是主动的。它会问：

- **对这条请求我们有什么证据？**
- **它落在哪个质量、成本、延迟、安全 band？**
- **一个模型够吗？**
- **不够的话，应该跑哪种协作模式？**
- **要保住什么答案合同？**
- **一个 provider 慢或错时应该怎么办？**
- **怎么在保留完整 trace 的同时返回一条干净的响应？**

这不是应用层胶水。**这是基础设施**。

Micro-agent 属于 router 是因为 router 本来就拥有 micro-agent 需要的东西——model aliases、provider policy、credentials、成本元数据、信号、决策、重试、超时、trace、OpenAI 兼容响应语义。

把 micro-agent 放在应用层是浪费：

- **重复发明**：每个应用都要重新写一遍"派发给多个模型、收集结果、综合输出"
- **失去统一可观测性**：trace 散落在应用日志里，router 看不到
- **失去统一策略**：成本控制、安全策略、A/B 实验都要在每个应用里重新实现

把 micro-agent 放在 router 是复用：

- **一次实现、所有调用方受益**
- **trace 进入 router 的标准观测管线**
- **策略、预算、合同都是 router 的一等公民**

## 十四、Micro-Agent 与传统 Agent 的边界

| 维度 | Micro-Agent（router 层） | 传统 Agent（应用层） |
|------|-------------------------|---------------------|
| 范围 | 一次请求内 | 跨多次请求、长时间 |
| 状态 | 无持久化（请求级） | 有 session / memory |
| 工具 | 仅 model 调用 | 任意外部工具 |
| 预算 | router 强约束 | 应用自管 |
| 可观测性 | router trace | 应用日志 |
| 失败模式 | 显式 error policy | 隐式异常处理 |
| 角色 | 固定 5 种 Looper | 任意自定义图 |

**Micro-Agent 不是要取代应用层 agent**。它是给"一次请求内的协作"一个**基础设施级的归属**。长时间跨请求的、有持久状态的、需要外部工具的、要做长链路规划的——这些还是属于应用层 agent 框架（LangGraph、CrewAI 等）。

**Micro-Agent 是 router 内置的能力**，应用层 agent 是 router 上层的应用。两者可以共存：router 用 micro-agent 处理单次请求的协作；应用层 agent 用 router 的 micro-agent 当作"更高质量的一次模型调用"，再在它上面做长链路规划。

## 十五、可借鉴的工程模式

虽然 vLLM Semantic Router 是一个具体的 router 实现，但里面沉淀的工程模式**可以用到任何 AI 推理基础设施里**：

| 模式 | 来自哪种 Looper | 适用场景 | 关键设计点 |
|------|----------------|----------|------------|
| 顺序置信度升级 | Confidence | 成本敏感的对话/检索 | 阈值显式可调 |
| 硬上限并行 | Ratings | A/B、ensemble | max_concurrent 是旋钮 |
| 广度 + 综合 | ReMoM | 推理方差大、合同要求高 | 法定人数先于综合 |
| 分歧即证据 | Fusion | 多解合理、需压单点错误 | judge 必须 frontier |
| 角色预算 | Workflows | SWE 风格、规划型任务 | planner 在白名单里挑 |
| Auto Recipe | 全部 5 种 | 路由即决策 | 信号 first-class |
| 失败降级到最佳证据 | ReMoM | 高可用推理 | 不塌成 API 错误 |
| 显式输出合同 | 全部 | 任何"答案格式"任务 | 综合器守合同 |
| 隐藏 trace 的 API 表面 | 全部 | OpenAI 兼容 | 用户只见一个 model name |
| 失败响应从分母扣 | Ratings | 任何 ensemble | 不让坏 worker 拖累 |

最后两条是**关键洞察**——micro-agent 之所以能用一个 model name 撑起所有复杂度，靠的是"trace 折叠在 API 后面"+"失败响应有显式处理"。这两件事如果没做对，协作要么退化成"用户要懂内部图"，要么退化成"一个挂的 worker 把整个 ensemble 拖垮"。

## 十六、什么时候不要用 micro-agent

不是所有场景都适合 router-side 协作。下面这些情况要谨慎：

- **极低延迟链路**（< 50ms P99）：Confidence 串行升级、ReMoM 广度采样——单次请求的延迟下限是"最深的链路"。如果延迟是硬指标，不要上 micro-agent
- **单次请求 token 预算极小**（< 1K）：ReMoM 的综合器输入长度会超 5 路总和，单请求 token 直接爆。Ratings 也要至少 N × 单路 token
- **多轮对话状态强依赖**：router 是无状态的，多轮上下文属于应用层。micro-agent 能做的只是"在一次请求内协作"
- **需要外部工具**：micro-agent 只能调 model，不能调搜索/数据库/计算器。SWE 风格的"调用工具"仍属于应用层
- **大流量低成本场景**：每次请求都跑 4-5 个模型调用，token 总量是单模型的 4-5 倍。如果流量大且成本敏感，先优化单模型或选更小的模型

**Micro-Agent 适合的是**：单次请求质量优先、token 成本可承受、延迟可接受 P99 ~秒级、答案需要保住合同、推理方差大、失败可降级——这一类"中高质量推理"的场景。

## 十七、自测题

1. vLLM Semantic Router 的"一个 model name 暴露 5 种协作"这件事，跟 LangGraph 这种应用层 agent 框架在**抽象归属**上有什么根本差别？（提示：看 trace、策略、预算分别归谁）
2. Confidence 升级循环里，**信号来源**有 5 种（logprob / logprob margin / 混合 / 自校验 / entailment verifier），各自适合什么场景？什么场景下用 entailment verifier 比用 logprob 更好？
3. ReMoM 的"广度 + 综合"为什么不能简化为 Ratings 的"并行 + 投票"？（提示：综合器和投票在"答案来源"上有什么不同）
4. Fusion 的 judge 必须是 frontier 模型这件事——如果用小模型做 judge，输出会退化为什么形态？
5. Workflows 里的"planner 只能在白名单里挑 worker"这件事，去掉会出什么问题？（提示：失败模式 + 资源控制 + 可观测性）
6. VSR Closed 在 HLE 上 50.0 / VSR Hybrid 47.1——Hybrid 反而低 2.9 分这件事，能推出"open + closed 混用不如只用 closed"这个结论吗？为什么？
7. 一个企业要在自己的推理服务里上 micro-agent，**第一步应该做什么**？（提示：先看自己当前请求的"质量方差分布"，还是先选 Looper 类型？）

### 进阶思考题（动手才答得出的）

8. 选一个你日常在用的 LLM API（GPT-5.5 / Claude Opus 4.8 / Gemini 3.1 Pro 任一），用同一个 prompt 跑 10 次，统计 token 级别 logprob 的分布。**这条 prompt 在 vLLM Semantic Router 的 Confidence 循环里会不会升级？为什么？**
9. 把一个你负责的应用拆成"单请求质量敏感"和"长链规划敏感"两类。**哪一类应该走 micro-agent、哪一类应该走应用层 agent 框架？**
10. 算一下你当前的"模型协作预算"：一次请求从单模型升级到 5 路 ReMoM，token 总量和延迟变成几倍？**这个倍数在你的成本结构里能不能跑？**

<details>
<summary>参考答案提示</summary>

1. 抽象归属差在 trace / 策略 / 预算归谁：LangGraph 三者都在应用代码里，router 看不到；vLLM Semantic Router 三者都在 router 策略里，应用层只看到一个 model name。
2. logprob 适合"答案概率集中在某 token"的任务（如 MCQ）；logprob margin 适合"区分两个候选"；混合适合"主信号 + 副信号"；自校验适合"模型能自我评估"的领域；entailment verifier 适合"答案需要外部语义验证"的任务（如多步推理、答案在原文里找不到）——后者的代价是**多一次 verifier 推理**，但能解决 logprob 误判。
3. ReMoM 的综合器**生成新答案**（拿证据重组），Ratings 的投票**选现成答案**（取共识）。当任务答案是"必须被构造"时（如带约束的代码、合同守住的长文本），综合器是唯一选择；投票会丢信息。
4. 退化成"几个弱答案的加权平均"或"judge 自己倾向某个候选的偏差传递"——本质是**judge 能力上限 = ensemble 能力上限**。
5. 去掉白名单会出现：(a) planner 选了一个不存在的 worker，运行时挂掉；(b) planner 选了未经批准的开源模型，绕过合规；(c) 资源不可控，router 失去成本 / 延迟可预测性；(d) trace 失去统一性，观测管线要按 worker 拆。
6. 不能。这个 2.9 分差只说明**HLE 这个特定 benchmark**上 Hybrid 配置不如 Closed——可能是 judge 用了 open 模型拖了后腿（judge 必须是 frontier 这条铁律的证据）。换 benchmark / 换 judge 配置 / 改综合策略，Hybrid 可能在别的任务上赢。
7. 第一步是**看自己当前请求的质量方差分布**——把生产请求按"小模型答得对/错"分类，统计"答错的请求"集中在什么类型。如果 80% 错的是同一类（比如代码生成），那第一步是**针对这类任务上 ReMoM 或 Workflows**，不是"先把 5 种 Looper 都上"。
8. 关键看 logprob 分布的尾部和分布跨度。尾部在 -2 以下的 prompt 容易升级；跨度大（top-1 / top-2 差 < 1.0）的 prompt 也容易升级。如果升级阈值是 -1.5，那么尾部 < -1.5 的部分会触发升级——这部分占你 10 次里的几次，就是 Confidence 在你这条 prompt 上的"升级率"。
9. 单请求质量敏感（一次回答要准确、要保住合同、要压低方差）→ micro-agent；长链规划敏感（多轮上下文、跨请求状态、外部工具、长链路推理）→ 应用层 agent 框架。
10. 单模型 → 5 路 ReMoM：token 总量变成 ~5-6 倍（5 路 worker + 1 个综合器），延迟变成 ~max(5 路延迟) + 综合器延迟。最坏情况 5-10 倍。这对你的成本结构意味着：原本 $1 / 1K 请求变成 $5-6 / 1K；原本 P99 1s 变成 P99 3-5s。能跑 → 上；不能跑 → 只在关键路径上 ReMoM，其它仍走单模型。

</details>

## 十八、一句话总结

vLLM Semantic Router 的 micro-agent 把"在前沿模型之前加一层"这件事，从应用代码搬到了 serving runtime——5 种 Looper（Confidence / Ratings / ReMoM / Fusion / Workflows）在 router 里跑，3 个 benchmark 追平或打过 frontier 单模型基线，公开接口还是一个 OpenAI 兼容的 model name。**Frontier model 的下一战场不在权重，在 router**。

---

**原文**：[Micro-Agent: Beat Frontier Models with Collaboration inside Model API](https://vllm.ai/blog/2026-06-29-micro-agent-frontier-models)
**作者**：vLLM Semantic Router Team
**发布日期**：2026-06-29
**关联研究**：Sakana Fugu Technical Report (arxiv 2606.21228) / Conductor (arxiv 2512.04388) / Trinity (arxiv 2512.04695)
**协议**：CC BY-SA 4.0
