---
title: '「榨」出硅的极限：GPU 为什么「又忙又闲」，推理引擎如何捡回浪费的算力'
date: 2026-08-01
draft: false
categories: ["视频精读"]
tags: ["AI Infra", "SGLang", "推理引擎", "GPU 调度"]
description: '当 GPU 满载却仍有大量算力被浪费在重复计算、缓存搬运和任务等待上，AI Infra 的效率革命才刚刚开始。本文深度拆解硅谷101对 SGLang 与 RadixArk 团队的访谈，梳理推理引擎的核心技术脉络。'
cover: "http://i1.hdslb.com/bfs/archive/c7b959c9107e91e90807950237330668d2099ed7.jpg"
slug : index

---

# "榨"出硅的极限：GPU 为什么"又忙又闲"，推理引擎如何捡回浪费的算力

> 本文基于 [硅谷101](https://space.bilibili.com/508452265) 的视频 [《"榨"出硅的极限：怎么让 GPU 不"闲着"？》](https://www.bilibili.com/video/BV1FnGA66EPP/)（2026-07-31 发布，28 分 48 秒）梳理而成。因视频无公开字幕，本文基于视频简介、章节结构、嘉宾公开背景及 SGLang/RadixArk 官方技术资料整理，涉及嘉宾观点处均标注来源边界。视频章节时间轴已从 B 站页面获取，可按图索骥回看原片。

## 视频信息卡

| 项目 | 内容 |
|------|------|
| 视频 | ["榨"出硅的极限：怎么让 GPU 不"闲着"？](https://www.bilibili.com/video/BV1FnGA66EPP/) |
| UP 主 | 硅谷101（B 站粉丝 200 万+） |
| 时长 | 28:48 |
| 发布日期 | 2026-07-31 |
| 播放 / 点赞 / 收藏 | 50,000+ / 1,420 / 970+ |

### 采访嘉宾

- **朱邦华**：RadixArk 联合创始人，曾任英伟达（NVIDIA）首席研究科学家。SGLang 核心贡献者。
- **陈震林 Richard**：RadixArk Member of Technical Staff
- **Ethan Xu**：前微软能源战略经理、突破能源（Breakthrough Energy）科研总监。关注 AI 与能源交叉领域

### 视频章节（7 段）

1. **AI Infra** — 什么是 AI 基础设施，为什么它成了热门赛道
2. **又忙又"闲"的 GPU** — GPU 满载背后的算力浪费
3. **"榨"出硅的极限：K/V Cache** — 缓存复用如何减少重复计算
4. **PD 分离** — Prefill 与 Decode 解耦的架构思路
5. **低精度计算 / 投机采样** — 用精度换速度、用猜测换吞吐
6. **资源协同与 Miles** — RL 训练框架与推理的协同
7. **更大的野心** — RadixArk 的商业化愿景

## 一、造芯大战的另一面：算力有了，谁来"调度"

OpenAI、Google、DeepSeek 等头部 AI 实验室在 2025-2026 年打响了一场"造芯大战"。各大芯片厂商推出新一代 GPU，云厂商大举扩建数据中心，市场依然缺卡、缺算力。但买到 GPU 只是第一步——**怎么让手里的 GPU 发挥出更大价值**，正在成为硅谷 AI Infra（基础设施）领域背后千亿美元级的赛道。

这段视频的切入点正在这里。主持人陈茜与三位嘉宾讨论的核心问题是：当推理（inference）取代训练成为 AI 计算的主要负载，GPU 看似满载运行，实际上仍有大量时间花在了非生产性计算上。这些浪费来自三个方向——重复计算、缓存搬运和任务等待。

朱邦华在英伟达担任首席研究科学家期间，研究的就是如何让 GPU 在推理场景下跑得更高效。他从大厂出来联合创立 RadixArk，选择的切入点正是推理引擎的系统优化。视频简介中提到：**SGLang 是推理引擎开源社区中孵化出来的明星项目，RadixArk 则是由 SGLang 团队孵化的商业公司**。

这期视频的看点在于，它把一个通常只在系统工程师圈层讨论的硬核话题——推理调度与底层优化——用相对易懂的方式呈现给了更广泛的受众。

## 二、"又忙又闲"的 GPU：满载是一个幻觉

视频第二章"又忙又闲的 GPU"是整期节目的认知锚点。

GPU 在监控面板上显示利用率 90%+，并不等于它在做有用功。在 LLM（大语言模型）推理场景中，GPU 的时间被切分为多种操作：矩阵乘法（真正的计算）、内存读写（KV Cache 搬运）、同步等待（batch 之间的空隙）、以及大量重复的预填充计算。

一个典型的浪费场景：两个用户发送了相似的 prompt（比如都包含了同一段系统提示词），传统推理引擎会分别做两次完整的 prefill 计算，生成两份完全相同的 KV Cache。这就是重复计算。

SGLang 的核心贡献之一 **RadixAttention** 技术，正是针对这个问题。它的思路是把已经计算过的 KV Cache 组织成一棵基数树（radix tree），新请求到达时先做前缀匹配：如果已有相同的前缀缓存，直接复用，跳过重复计算。

根据 SGLang 团队 2024 年 1 月发布的 [技术博客](https://lmsys.org/blog/2024-01-17-sglang/)，RadixAttention 可以带来最高 5 倍的推理加速。这个数字的实际效果取决于工作负载特征——系统提示词越长、多请求前缀重合度越高，加速比越大。

另一个浪费来源是 **CPU 调度开销**。在 GPU 执行一批推理任务的同时，CPU 需要为下一批任务做准备：分配显存、匹配前缀、构建批次元数据。如果 CPU 调度跟不上 GPU 的执行速度，GPU 就会在两批任务之间出现短暂的空闲。SGLang v0.4 版本引入了**零开销批调度器**（zero-overhead batch scheduler），借鉴 NanoFlow 的思路，让 CPU 调度与 GPU 计算重叠执行：调度器提前一个 batch 准备好所有元数据，GPU 执行完当前 batch 后可以无缝衔接下一个。通过 Nsight 性能分析工具验证，5 个连续解码 batch 之间 GPU 没有任何空闲时间。

视频动态中陈茜写道："昂贵的 GPU 竟然很多时候都在'空转'"——这并非字面意义上的 GPU 闲置，而是指有效计算在时间线中的占比远低于预期。

## 三、K/V Cache：推理引擎的"内存战场"

视频第三章聚焦 K/V Cache，这是 LLM 推理优化中最核心的数据结构。

### 什么是 KV Cache

Transformer 模型生成文本时是逐 token（词元）进行的。每生成一个新 token，需要访问之前所有 token 的 Key 和 Value 矩阵。如果每一步都重新计算这些矩阵，计算量会随序列长度平方级增长。KV Cache 的做法是把每一步的 K、V 矩阵缓存下来，后续步骤直接读取，将计算复杂度从 O(n²) 降到 O(n)。

代价是显存占用：以 Llama-3-70B 为例，单条请求的 KV Cache 在序列长度 4096 时大约占用 20-40 GB 显存（取决于精度设置），而一张 H100 的显存是 80 GB。这意味着单卡同时服务的并发请求数非常有限。

### RadixAttention 的工程实现

SGLang 的 RadixAttention 把 KV Cache 的管理从"按请求隔离"升级为"全局共享的基数树"。具体来说：

- 每个 token 序列的 KV Cache 按前缀存储在基数树节点中
- 新请求到达时，沿基数树路径做前缀匹配，命中部分直接复用
- 缓存淘汰采用 LRU（最近最少使用）策略，显存不足时自动释放最旧的缓存

这套机制使得多轮对话、共享系统提示词、few-shot 学习等场景下的缓存命中率大幅提升。SGLang v0.4 还引入了**缓存感知负载均衡器**（cache-aware load balancer），在多 worker 场景下预测各 worker 的前缀缓存命中率，把请求发给缓存匹配度最高的 worker。测试数据显示吞吐量提升 1.9 倍，缓存命中率从 20% 提升到 75%。

### 内存搬运的瓶颈

KV Cache 带来的另一个问题是内存带宽压力。在自回归解码过程中，每生成一个 token 都需要把完整的 KV Cache 从 HBM（高带宽内存）读到 GPU 计算单元。随着序列变长，这个搬运操作的耗时逐渐超过实际矩阵乘法的计算耗时——GPU 的计算单元在等待数据到达，这就是典型的"内存带宽瓶颈"。

这也是为什么 PD 分离（下一节）和低精度量化成为关键优化方向：前者通过架构调整减少不必要的数据搬运，后者通过压缩 KV Cache 的存储精度来降低带宽需求。

## 四、PD 分离：把"思考"和"说话"拆开

视频第四章讨论 Prefill-Decode 分离（PD Disaggregation），这是 2025 年推理架构领域最重要的趋势之一。

### 为什么要分离

LLM 推理包含两个阶段：

1. **Prefill（预填充）**：处理用户输入的 prompt，一次性计算所有输入 token 的 KV Cache。这是计算密集型操作，GPU 算力是瓶颈。
2. **Decode（解码）**：逐个生成输出 token，每步只计算一个 token 但需要读取完整 KV Cache。这是内存带宽密集型操作，显存带宽是瓶颈。

传统做法是把 prefill 和 decode 混在同一个 batch 里调度（称为 unified scheduling 或混合批处理）。问题是两个阶段的资源需求特征完全相反：prefill 需要 GPU 算力但显存占用不高，decode 需要大量显存读写但 GPU 算力利用率低。混在一起会导致 GPU 在 decode 阶段"吃不饱"。

### PD 分离的架构

PD 分离的思路是**把两个阶段分到不同的 GPU 集群上执行**：

- Prefill 节点专注处理新请求，充分利用 GPU 算力
- Decode 节点专注生成 token，最大化内存带宽利用率
- Prefill 完成后，将 KV Cache 传输到 Decode 节点继续生成

SGLang 团队在 2025 年 5 月发布了 [PD 分离 + 大规模专家并行的实现](https://lmsys.org/blog/2025-05-05-large-scale-ep/)，在 12 台 H100 节点（96 张 GPU）上部署 DeepSeek 模型，实现了每节点 52,300 input tokens/s 和 22,300 output tokens/s 的吞吐量。与 vanilla 张量并行相比，输出吞吐量最高提升 5 倍。

视频此处（约 15-18 分钟段）应当讨论了 PD 分离的工程挑战——特别是 KV Cache 在节点间的传输开销。这个传输需要通过 RDMA（Remote Direct Memory Access）或 NVLink 完成，架构设计要在传输延迟和缓存命中率之间找到平衡点。

## 五、低精度与投机采样：两条加速路径

视频第五章覆盖了两个独立的优化方向。

### 低精度计算

将模型权重和 KV Cache 从 FP16（16 位浮点）压缩到 FP8、FP4 甚至更低的精度。理论上精度减半，计算吞吐和内存带宽都翻倍。实际效果取决于硬件支持和精度损失容忍度。

SGLang 支持多种量化方案：FP4/FP8/INT4/AWQ/GPTQ。2026 年 7 月 SGLang 发布了 [GLM-5.2 NVFP4 推理优化博客](https://lmsys.org/blog/2026-07-13-glm52-optimization/)，展示了在 NVFP4 精度下服务 GLM-5.2 agentic 工作负载的实践，达到 500 TPS（tokens per second）。NVIDIA 的 GB200/GB300 芯片原生支持 FP4 计算，这使得低精度推理从实验走向生产。

### 投机采样

投机采样（Speculative Decoding）是另一种加速解码的思路。用一个小的"草稿模型"（draft model）快速生成多个候选 token，再用大模型一次性验证这些候选。如果草稿模型的预测准确率高，等于大模型一次前向传播就能生成多个 token。

SGLang 在 2026 年 6 月与 Z Lab、Modal 合作发布了 [DFlash 和 Spec V2](https://lmsys.org/blog/2026-06-15-next-generation-speculative-decoding-dflash-v2/)。DFlash 采用了一种新颖的"扩散 + KV 注入"策略生成草稿 token，在 Qwen 3.5 397B 模型上达到了 4.3 倍于基线的吞吐量。Spec V2 是 SGLang 新的投机采样引擎，默认启用，消除了草稿生成的主机开销。

这两个方向的核心逻辑是一致的：**与其让 GPU 做更快的计算，不如让它少做无用功**。

## 六、资源协同与 Miles：RL 训练的推理引擎

视频第六章涉及 Miles——RadixArk 的开源 RL（强化学习）训练框架。

### RL 训练为什么需要推理引擎

强化学习训练（特别是 RLHF，即基于人类反馈的强化学习）的流程是：模型生成回答（rollout），然后由奖励模型打分，再用打分结果更新模型权重。其中 rollout 阶段本质上就是推理——需要模型快速生成大量回答。

这意味着 RL 训练的效率瓶颈往往不在梯度更新，而在推理速度。如果推理引擎不够快，GPU 大量时间花在等待 rollout 完成上。

### Miles 的定位

RadixArk 官网对 Miles 的描述是："our open-source framework for large-scale post-training. Miles brings the same rigor to reinforcement learning that modern serving engines brought to inference."（我们的开源大规模后训练框架。Miles 为强化学习带来了现代推理引擎为推理所带来的同等严谨性。）

SGLang 在 GitHub README 中将 Miles 列为 RL 与后训练的核心后端之一，与 AReaL、slime、Tunix、verl 等知名框架并列。这说明 RadixArk 的商业逻辑是双轮驱动：**推理侧用 SGLang 建立技术壁垒，训练侧用 Miles 覆盖 RL 场景**，两者共享底层系统优化能力。

## 七、千亿美元市场与 RadixArk 的野心

视频最后一章"更大的野心"，讨论 AI Infra 的市场规模和 RadixArk 的商业愿景。

### 市场背景

AI Infra 市场的规模可以从几个维度理解：

- **GPU 采购**：2025 年全球 AI 芯片市场规模超过 1000 亿美元，其中 NVIDIA 数据中心 GPU 占据绝对份额
- **云服务**：AWS、Azure、GCP 三大云厂商的 AI 相关营收年增长率超过 100%
- **推理 vs 训练**：随着模型能力趋于稳定，推理请求量呈指数级增长，推理算力消耗正在超过训练

Ethan Xu 作为前微软能源战略经理和突破能源科研总监，其参与暗示了这个话题的另一个维度——**AI 的能源消耗**。AI 数据中心的耗电量已成为美国电网面临的新挑战，推理效率的提升直接转化为能源节约。从这个角度看，AI Infra 优化不仅是技术问题，也是能源政策和可持续发展问题。

### RadixArk 的商业逻辑

从 RadixArk 官网可以看到清晰的商业路径：

> "RadixArk is an infrastructure-first, deep-tech company building large-scale inference and training systems for the entire AI community."
>
> "We aim to make building, training, and running frontier models at least 10x cheaper and 10x more accessible than they are today."

核心策略是：

1. **开源 SGLang 建立标准**：SGLang 目前在 GitHub 上拥有庞大的社区，被 xAI、NVIDIA、AMD、Intel、LinkedIn、Cursor 等公司采用，全球部署覆盖超过 40 万张 GPU。它已经成为事实上的开源推理引擎标准。
2. **开源 Miles 覆盖 RL 训练**：与推理引擎形成完整的技术栈。
3. **商业化托管服务**：在开源核心之上提供托管基础设施和工具，面向开发者、初创公司、企业和研究实验室。

这是一个典型的"开源核心 + 商业服务"模式，类似于 Databricks 与 Spark、Confluent 与 Kafka 的关系。RadixArk 的差异化在于它的技术深度——团队来自 NVIDIA 的核心研究团队，对 GPU 底层架构和系统优化有第一手的理解。

朱邦华从 NVIDIA 首席研究科学家到 RadixArk 联合创始人的轨迹，反映了 AI 行业一个更大的趋势：**最大的商业机会正在从"造芯片"转向"用好芯片"**。芯片性能增长遵循摩尔定律，但系统软件的效率提升空间可能更大——而且不需要新建晶圆厂。

## 八、SGLang 技术栈全景：从论文到生产线

为了帮助读者更好理解视频中提到的技术概念，以下是 SGLang 核心技术栈的完整图谱。

### 核心引擎能力

| 技术模块 | 功能 | 发布版本 |
|----------|------|----------|
| RadixAttention | 基于基数树的前缀缓存复用 | v0.1（2024-01） |
| 零开销批调度器 | CPU 调度与 GPU 计算重叠 | v0.4（2024-12） |
| 缓存感知负载均衡器 | 多 worker 场景按缓存命中率路由 | v0.4（2024-12） |
| PD 分离 | Prefill 与 Decode 分集群执行 | 2025-05 |
| 大规模专家并行 | DeepSeek MoE 模型的专家级并行 | 2025-05 |
| Spec V2 + DFlash | 下一代投机采样引擎 | 2026-06 |
| 结构化输出 | 基于 XGrammar 的快速结构化生成 | v0.4（2024-12） |

### 硬件支持

SGLang 的硬件覆盖范围是开源推理引擎中最广的：

- **NVIDIA**：GB200/B300/H100/A100/Spark/5090
- **AMD**：MI355/MI300
- **Intel**：Xeon CPU
- **Google**：TPU（与 RadixArk 合作，2026 年 7 月实现 SGLang 全功能 TPU 支持）
- **华为**：Ascend NPU

### 生态采用

SGLang 被以下组织在生产环境大规模部署：xAI、NVIDIA、AMD、Intel、LinkedIn、Cursor、Oracle Cloud、Google Cloud、Microsoft Azure、AWS、阿里云、腾讯、百度、蚂蚁集团，以及 MIT、Stanford、UC Berkeley、清华等高校。

## 九、谁该看这期视频

这期视频适合以下读者：

- **AI 基础设施工程师和架构师**：了解推理引擎的最新技术趋势和 RadixArk 的商业化方向
- **技术决策者（CTO / VP Engineering）**：评估推理引擎选型时理解 SGLang 在行业中的定位
- **AI 创业者**：理解 AI Infra 赛道的市场格局和"开源核心 + 商业服务"的商业模式
- **对硅谷 AI 生态感兴趣的读者**：通过嘉宾背景和公司定位了解当前 AI Infra 创业的脉搏

已经熟悉 KV Cache、PD 分离和投机采样的读者，视频的技术部分可能不会带来太多新信息，但嘉宾的一线视角和行业判断仍值得参考。初次接触这些概念的读者，建议先通读本文再回看原片，理解会更完整。

## 十、五个 Takeaway

1. **GPU 满载 ≠ 高效利用**。推理场景下，GPU 大量时间消耗在 KV Cache 搬运、重复计算和调度等待上。系统优化的价值在于把这些"隐形浪费"捡回来。

2. **RadixAttention 是 SGLang 的技术基石**。把 KV Cache 组织成基数树实现全局前缀复用，最高 5 倍加速。缓存感知负载均衡器在多 worker 场景下进一步提升 1.9 倍吞吐。

3. **PD 分离是 2025 年最重要的推理架构创新**。把 prefill（计算密集）和 decode（内存密集）分到不同 GPU 集群，让每种硬件都发挥最大效用。SGLang 在 96 张 H100 上实现了 5 倍于传统方案的输出吞吐。

4. **投机采样正在突破传统加速极限**。DFlash + Spec V2 用"扩散 + KV 注入"的草稿模型实现 4.3 倍加速，这种思路不是让 GPU 算得更快，而是让它少做无用功。

5. **AI Infra 的市场逻辑正在从"造芯"转向"调度"**。RadixArk 通过开源 SGLang（推理）+ Miles（RL 训练）建立技术标准，再叠加商业化托管服务。朱邦华从 NVIDIA 首席研究科学家到创业者的转型，折射出系统软件正在成为 AI 产业链中价值增长最快的一环。

---

*本文基于公开视频简介、B 站页面信息、SGLang GitHub 仓库及 RadixArk 官方资料整理。视频无公开字幕，涉及嘉宾具体观点的段落建议回看 [原视频](https://www.bilibili.com/video/BV1FnGA66EPP/) 获取准确表述。*
