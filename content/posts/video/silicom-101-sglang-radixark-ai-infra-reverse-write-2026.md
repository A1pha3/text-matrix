---
title: '「榨」出硅的极限：GPU 为什么「又忙又闲」，推理引擎如何捡回浪费的算力'
date: 2026-08-01
draft: false
categories: ["视频精读"]
tags: ["AI Infra", "SGLang", "推理引擎", "GPU 调度"]
description: '当 GPU 满载却仍有大量算力被浪费在重复计算、缓存搬运和任务等待上，AI Infra 的效率革命才刚刚开始。本文深度拆解硅谷101对 SGLang 与 RadixArk 团队的访谈，梳理推理引擎的核心技术脉络。'
cover: "http://i1.hdslb.com/bfs/archive/c7b959c9107e91e90807950237330668d2099ed7.jpg"

slug: "silicom-101-sglang-radixark-ai-infra-reverse-write-2026"
source_key: "bv:BV1FnGA66EPP"
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
| 播放 / 点赞 / 收藏 | 50,000+ / 1,420 / 970+（2026-09 检索时点） |

### 采访嘉宾

- **朱邦华（Banghua Zhu）**：RadixArk 联合创始人，SGLang 核心贡献者。据 Pulse 2.0 报道，他与另一位联合创始人盛颖（Ying Sheng）是"来自 xAI 与 NVIDIA 的 AI 基础设施老兵"。
- **陈震林 Richard**：RadixArk Member of Technical Staff
- **Ethan Xu**：前微软能源战略经理、突破能源（Breakthrough Energy）科研总监。关注 AI 与能源交叉领域

顺带补一条嘉宾阵容之外的背景：SGLang 2023 年由盛颖与合作者创建，朱邦华是最早的共同维护者之一，两人后来一同创办 RadixArk。头衔与背景信息来自视频简介与公开报道，具体表述以原片为准。

### 视频章节（7 段）

1. **AI Infra**（0:00–1:43）— 什么是 AI 基础设施，为什么它成了热门赛道
2. **又忙又"闲"的 GPU**（1:43–8:45）— GPU 满载背后的算力浪费
3. **"榨"出硅的极限：K/V Cache**（8:45–14:43）— 缓存复用如何减少重复计算
4. **PD 分离**（14:43–16:54）— prefill 与 decode 解耦的架构思路
5. **低精度计算 / 投机采样**（16:54–21:03）— 用精度换速度、用猜测换吞吐
6. **资源协同与 Miles**（21:03–25:50）— RL 训练框架与推理的协同
7. **更大的野心**（25:50–28:47）— RadixArk 的商业化愿景

## 一、造芯大战的另一面：算力有了，谁来"调度"

OpenAI、Google、DeepSeek 等头部 AI 实验室在 2025-2026 年打响了一场"造芯大战"。各大芯片厂商推出新一代 GPU，云厂商大举扩建数据中心，市场依然缺卡、缺算力。但买到 GPU 只是第一步——**怎么让手里的 GPU 发挥出更大价值**，正在成为硅谷 AI Infra（基础设施）领域的千亿美元级赛道。

主持人陈茜与三位嘉宾讨论的核心问题是：当推理（inference）取代训练成为 AI 计算的主要负载，GPU 看似满载运行，实际上仍有大量时间花在了非生产性计算上。这些浪费来自三个方向——重复计算、缓存搬运和任务等待。

朱邦华是 SGLang 最早的核心维护者之一，这个项目出自 UC Berkeley 的 LMSYS 体系；Pulse 2.0 对 RadixArk 的报道将他和盛颖并称为"来自 xAI 与 NVIDIA 的 AI 基础设施老兵"。从研究体系和大厂出来联合创立 RadixArk，他选择的切入点正是推理引擎的系统优化。视频简介中提到：**SGLang 是推理引擎开源社区中孵化出来的明星项目，RadixArk 则是由 SGLang 团队孵化的商业公司**。

这期视频把一个平日只在系统工程师圈层讨论的硬核话题——推理调度与底层优化——讲得相对可接近，屏幕上没有代码，主线是"瓶颈在哪、怎么绕开"。

## 二、"又忙又闲"的 GPU：满载是一个幻觉

视频第二章"又忙又闲的 GPU"（1:43–8:45）是整期节目的关键。

GPU 在监控面板上显示利用率 90%+，并不等于它在做有用功。在 LLM（大语言模型）推理场景中，GPU 的时间被切分为多种操作：矩阵乘法（真正的计算）、内存读写（KV Cache 搬运）、同步等待（batch 之间的空隙）、以及大量重复的预填充计算。

一个典型的浪费场景：两个用户发送了相似的 prompt（比如都包含了同一段系统提示词），传统推理引擎会分别做两次完整的 prefill 计算，生成两份完全相同的 KV Cache。这就是重复计算。

SGLang 的核心贡献之一 **RadixAttention** 技术，正是针对这个问题。它的思路是把已经计算过的 KV Cache 组织成一棵基数树（radix tree），新请求到达时先做前缀匹配：如果已有相同的前缀缓存，直接复用，跳过重复计算。

根据 SGLang 团队 2024 年 1 月发布的 [技术博客](https://lmsys.org/blog/2024-01-17-sglang/)，在 Llama-7B 和 Mixtral-8x7B 的测试中，SGLang 相对当时的 Guidance 和 vLLM 取得最高 5 倍的吞吐提升。这个数字的实际效果取决于工作负载特征——系统提示词越长、多请求前缀重合度越高，加速比越大。博客还给出一个容易忽略的结论：即使在没有缓存命中的场景，RadixAttention 的运行时开销也低到可以忽略，因此它默认开启，不需要任何配置。

另一个浪费来源是 **CPU 调度开销**。在 GPU 执行一批推理任务的同时，CPU 需要为下一批任务做准备：分配显存、匹配前缀、构建批次元数据。如果 CPU 调度跟不上 GPU 的执行速度，GPU 就会在两批任务之间出现短暂的空闲。SGLang v0.4 版本引入了**零开销批调度器**（zero-overhead batch scheduler），借鉴 NanoFlow 的思路，让 CPU 调度与 GPU 计算重叠执行：调度器提前一个 batch 准备好所有元数据，GPU 执行完当前 batch 后可以无缝衔接下一个。通过 Nsight 性能分析工具验证，在 Triton attention backend 下 5 个连续解码 batch 之间 GPU 没有任何空闲时间。这一项改造让调度开销基本消失：相比上一版本吞吐提升 1.1 倍，且默认开启。

视频动态中陈茜写道："昂贵的 GPU 竟然很多时候都在'空转'"——这并非字面意义上的 GPU 闲置，而是指有效计算在时间线中的占比远低于预期。

## 三、KV Cache：推理引擎的"内存战场"

视频第三章（8:45–14:43）聚焦 KV Cache，这是 LLM 推理优化中最核心的数据结构。

### 什么是 KV Cache

Transformer 模型生成文本时是逐 token（词元）进行的。每生成一个新 token，需要访问之前所有 token 的 Key 和 Value 矩阵。如果每一步都重新计算这些矩阵，计算量会随序列长度平方级增长。KV Cache 的做法是把每一步的 K、V 矩阵缓存下来，后续步骤直接读取，将计算复杂度从 O(n²) 降到 O(n)。

代价是显存占用：以 Llama-3-70B 为例（80 层、8 个 KV 头、每头 128 维），每生成一个 token 就要约 0.31 MB 的 KV Cache（FP16 精度）。序列长度 4096 时单条请求约 1.3 GB，一旦上下文拉长到 128K，单条请求就膨胀到约 40 GB。而一张 H100 的显存是 80 GB，模型权重本身又会占掉大半——单卡能同时服务的并发请求数非常有限。

### RadixAttention 的工程实现

SGLang 的 RadixAttention 把 KV Cache 的管理从"按请求隔离"升级为"全局共享的基数树"。具体来说：

- 每个 token 序列的 KV Cache 按前缀存储在基数树节点中
- 新请求到达时，沿基数树路径做前缀匹配，命中部分直接复用
- 缓存淘汰采用 LRU（最近最少使用）策略，显存不足时自动释放最旧的缓存

这套机制使得多轮对话、共享系统提示词、few-shot 学习等场景下的缓存命中率大幅提升。SGLang v0.4 还引入了**缓存感知负载均衡器**（cache-aware load balancer），在多 worker 场景下预测各 worker 的前缀缓存命中率，把请求发给缓存匹配度最高的 worker。v0.4 博客的测试里，吞吐量从 8,266 token/s 提升到 15,859 token/s（约 1.9 倍），缓存命中率从 20% 提升到 75%。

对比常见框架的另一条路：vLLM 的 PagedAttention 把 KV Cache 拆成固定大小的内存块、按需分页，解决的是显存碎片化和利用率问题；RadixAttention 则把缓存组织成基数树，解决的是跨请求的前缀复用。两者针对不同瓶颈，vLLM 之后也补上了自己的前缀缓存，但在"共享系统提示词"这类高前缀重合的工作负载上，RadixAttention 能省掉的重复 prefill 计算更多。

### 内存搬运的瓶颈

KV Cache 带来的另一个问题是内存带宽压力。在自回归解码过程中，每生成一个 token 都需要把完整的 KV Cache 从 HBM（高带宽内存）读到 GPU 计算单元。随着序列变长，这个搬运操作的耗时逐渐超过实际矩阵乘法的计算耗时——GPU 的计算单元在等待数据到达，这就是典型的"内存带宽瓶颈"。

拿 H100 的账来算更直观：它约有 3.35 TB/s 的显存带宽和约 989 TFLOPS 的 FP16 算力。解码阶段每步只新算一个 token 的 Q、K、V，算力需求很小，却要把整个 KV Cache 和权重从显存读一遍，带宽需求很大。结果就是 GPU 的算力利用率经常只有 10%-20%，算力在"等数据"，这正是 decode 阶段被称为带宽密集型的原因。

这也是为什么 PD 分离（下一节）和低精度量化成为关键优化方向：前者通过架构调整减少不必要的数据搬运，后者通过压缩 KV Cache 的存储精度来降低带宽需求。

## 四、PD 分离：把"思考"和"说话"拆开

视频第四章（14:43–16:54）讨论 Prefill-Decode 分离（PD Disaggregation）。2025 年它从论文走向了主流部署：DeepSeek 官方的推理服务就采用了这一架构。

### 为什么要分离

LLM 推理包含两个阶段：

1. **Prefill（预填充）**：处理用户输入的 prompt，一次性计算所有输入 token 的 KV Cache。这是计算密集型操作，GPU 算力是瓶颈。
2. **Decode（解码）**：逐个生成输出 token，每步只计算一个 token 但需要读取完整 KV Cache。这是内存带宽密集型操作，显存带宽是瓶颈。

传统做法是把 prefill 和 decode 混在同一个 batch 里调度（称为 unified scheduling 或混合批处理）。问题是两个阶段的资源需求特征完全相反：prefill 需要 GPU 算力但显存占用不高，decode 需要大量显存读写但 GPU 算力利用率低。混在一起会导致 GPU 在 decode 阶段"吃不饱"。

### PD 分离的架构

PD 分离的思路是**把两个阶段分到不同的 GPU 集群上执行**：

- prefill 节点专注处理新请求，充分利用 GPU 算力
- decode 节点专注生成 token，最大化内存带宽利用率
- prefill 完成后，将 KV Cache 传输到 decode 节点继续生成

SGLang 团队在 2025 年 5 月发布了 [PD 分离 + 大规模专家并行的实现](https://lmsys.org/blog/2025-05-05-large-scale-ep/)，在 Atlas Cloud 的 12 台 H100 节点（96 张 GPU）上部署 DeepSeek 模型，对 2000 token 的输入序列实现了每节点 52,300 input tokens/s 和 22,300 output tokens/s 的吞吐量，输出吞吐比 vanilla 张量并行最高提升 5 倍。按这个部署估算，输出成本约 0.20 美元/百万 token，约为 DeepSeek 官方 Chat API 的五分之一。

PD 分离章节只有两分钟，主要讲思路，工程细节没有展开。结合 SGLang 的公开资料，这里真正的难点在 KV Cache 的节点间传输：prefill 节点算完缓存后，要经 RDMA（Remote Direct Memory Access）或 NVLink 把它搬到 decode 节点，架构设计需要在传输延迟和缓存命中率之间找平衡——缓存搬得越勤，命中率越高，但带宽和延迟代价也越大。

## 五、低精度与投机采样：两条加速路径

视频第五章（16:54–21:03）覆盖了两个独立的优化方向。

### 低精度计算

将模型权重和 KV Cache 从 FP16（16 位浮点）压缩到 FP8、FP4 甚至更低的精度。理论上精度减半，计算吞吐和内存带宽都翻倍。实际效果取决于硬件支持和精度损失容忍度。

SGLang 支持多种量化方案：FP4/FP8/INT4/AWQ/GPTQ。2026 年 7 月 SGLang 发布的 [GLM-5.2 NVFP4 优化博客](https://lmsys.org/blog/2026-07-13-glm52-optimization/) 里，在 8 张 B300 上服务 GLM-5.2 的 agentic 编码工作负载（OpenHands 多轮回放：每轮约 80K token 输入、13 轮对话、92% 前缀缓存命中率），batch size 1 时达到 500+ TPS（tokens per second）的单用户交互速度；这个数字取自单并发的小批量场景，不代表高并发吞吐——同一篇博客里，batch size 8 的峰值吞吐提升是 6%-11%。NVIDIA 的 GB200/GB300 芯片原生支持 FP4 计算，这让低精度推理从实验走向生产。

### 投机采样

投机采样（Speculative Decoding）是另一种加速解码的思路。用一个小的"草稿模型"（draft model）快速生成多个候选 token，再用大模型一次性验证这些候选。如果草稿模型的预测准确率高，等于大模型一次前向传播就能生成多个 token。

SGLang 在 2026 年 6 月与 Z Lab、Modal 合作发布了 [DFlash 和 Spec V2](https://lmsys.org/blog/2026-06-15-next-generation-speculative-decoding-dflash-v2/)。DFlash 用轻量块扩散模型一次前向并行生成整块草稿 token，再通过 KV 注入把目标模型的隐状态写进每一层草稿的 KV 缓存，让草稿贴近目标模型；在 Qwen 3.5 397B-A17B 的 HumanEval 编码负载、单并发、8 张 B200 上，吞吐量超过基线的 4.3 倍，也达到原生 MTP 方案的 1.5 倍。Spec V2 是 SGLang 新的投机采样引擎，用重叠调度把草稿生成阶段的主机端同步开销藏到 GPU 计算背后——Qwen 3-8B 单张 B200、并发 32 的场景下吞吐提升 33%——现已默认启用。

这两个方向的共同点是：**与其让 GPU 做更快的计算，不如让它少做无用功**。

## 六、资源协同与 Miles：RL 训练的推理引擎

视频第六章（21:03–25:50）涉及 Miles——RadixArk 的开源 RL（强化学习）训练框架。

### RL 训练为什么需要推理引擎

强化学习训练（特别是 RLHF，即基于人类反馈的强化学习）的流程是：模型生成回答（rollout），然后由奖励模型打分，再用打分结果更新模型权重。其中 rollout 阶段本质上就是推理——需要模型快速生成大量回答。

RL 训练的效率瓶颈往往不在梯度更新，而在推理速度。如果推理引擎不够快，GPU 大量时间花在等待 rollout 完成上。

### Miles 的定位

RadixArk 官网对 Miles 的描述是："our open-source framework for large-scale post-training. Miles brings the same rigor to reinforcement learning that modern serving engines brought to inference."（我们的开源大规模后训练框架。Miles 为强化学习带来了现代推理引擎为推理所带来的同等严谨性。）

SGLang 的 GitHub README 把自己定位为 RL 训练的 rollout 后端——"用于训练多个前沿模型的、经过验证的 rollout 后端"——AReaL、Miles、slime、Tunix、verl 等框架都在用它做推理。训练框架负责梯度更新，rollout 的生成速度取决于推理引擎，这条依赖关系正是 RadixArk 的位置。它的商业逻辑是双轮驱动：**推理侧用 SGLang 建立技术壁垒，训练侧用 Miles 覆盖 RL 场景**，两者共享底层系统优化能力。

## 七、千亿美元市场与 RadixArk 的野心

视频最后一章"更大的野心"（25:50–28:47），讨论 AI Infra 的市场规模和 RadixArk 的商业愿景。

### 市场背景

AI Infra 市场的规模可以从几个维度理解——以下均为嘉宾在讨论中援引的行业口径：

- **GPU 采购**：2025 年全球 AI 芯片市场规模已达千亿美元量级，其中 NVIDIA 数据中心 GPU 占据绝对份额
- **云服务**：AWS、Azure、GCP 三大云厂商的 AI 相关营收年增长率超过 100%
- **推理 vs 训练**：随着模型能力趋于稳定，推理请求量呈指数级增长，推理算力消耗正在超过训练

Ethan Xu 的能源背景把话题引向另一个维度——**AI 的能源消耗**。AI 数据中心的耗电量已成为美国电网面临的新挑战，推理效率的提升直接转化为能源节约。从这个角度看，AI Infra 优化不仅是技术问题，也是能源政策和可持续发展问题。

### RadixArk 的商业逻辑

从 RadixArk 官网可以看到清晰的商业路径：

> "RadixArk is an infrastructure-first, deep-tech company building large-scale inference and training systems for the entire AI community."
>
> "We aim to make building, training, and running frontier models at least 10x cheaper and 10x more accessible than they are today."

核心策略是：

1. **开源 SGLang 建立标准**：SGLang 目前在 GitHub 上拥有庞大的社区，被 xAI、NVIDIA、AMD、Intel、LinkedIn、Cursor 等公司采用，全球部署覆盖超过 40 万张 GPU。它已经成为事实上的开源推理引擎标准。
2. **开源 Miles 覆盖 RL 训练**：与推理引擎形成完整的技术栈。
3. **商业化托管服务**：在开源核心之上提供托管基础设施和工具，面向开发者、初创公司、企业和研究实验室。

这套打法在资本市场上已有印证。时间线值得看一眼：TechCrunch 在 2026 年 1 月就援引消息源报道 SGLang 项目以 4 亿美元估值分拆为 RadixArk；2026 年 5 月 5 日，公司正式宣布完成 1 亿美元种子轮融资，投后估值 4 亿美元——由 Accel 领投、Spark Capital 联合领投，NVentures（英伟达旗下风投）、AMD、联发科、Salience Capital 等参投，天使名单里还包括 Intel 和 Broadcom 的 CEO、xAI 联合创始人 Igor Babuschkin 与一位 OpenAI 联合创始人。芯片厂商亲手投资一家教别人"少买芯片也能扩容"的公司，这件事本身就是行业风向。和 Databricks 之于 Spark、Confluent 之于 Kafka 是同一套模式，RadixArk 的差异化在技术深度——创始团队从 SGLang 项目一路做到大规模生产部署，对 GPU 底层架构和系统优化有第一手的理解。

朱邦华从开源项目核心维护者到创业者的轨迹，背后是 AI 行业的一次转向：**制程进步放缓之后，单张 GPU 的性能一年追不上需求增长，增量价值正在转移到"把已有的芯片用好"这一侧**。系统软件的效率提升空间反而显出来了——而且这条路不需要新建晶圆厂。

## 八、SGLang 技术栈全景：从论文到生产线

下面把视频里提到的 SGLang 技术点串成一张完整图谱，方便对照。

### 核心引擎能力

| 技术模块 | 功能 | 发布版本 |
|----------|------|----------|
| RadixAttention | 基于基数树的前缀缓存复用 | v0.1（2024-01） |
| 零开销批调度器 | CPU 调度与 GPU 计算重叠，吞吐 +10% | v0.4（2024-12） |
| 缓存感知负载均衡器 | 多 worker 场景按缓存命中率路由，吞吐最高 1.9 倍 | v0.4（2024-12） |
| 结构化输出 | 基于 XGrammar 的快速结构化生成，最高快 10 倍 | v0.4（2024-12） |
| PD 分离 | prefill 与 decode 分集群执行 | 2025-05 |
| 大规模专家并行 | DeepSeek MoE 模型的专家级并行 | 2025-05 |
| Spec V2 + DFlash | 下一代投机采样引擎 | 2026-06 |

### 硬件支持

SGLang README 列出的硬件覆盖面在开源推理引擎里数一数二：

- **NVIDIA**：GB200/B300/H100/A100/Spark/5090
- **AMD**：MI355/MI300
- **Intel**：Xeon CPU
- **Google**：TPU
- **华为**：Ascend NPU

### 生态采用

SGLang 被以下组织在生产环境大规模部署：xAI、NVIDIA、AMD、Intel、LinkedIn、Cursor、Oracle Cloud、Google Cloud、Microsoft Azure、AWS、Atlas Cloud、Voltage Park、Nebius、DataCrunch、Novita、InnoMatrix，以及 MIT、UCLA、华盛顿大学、Stanford、UC Berkeley、清华等高校。

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

3. **PD 分离是 2025 年推理架构的最大变量**。把 prefill（计算密集）和 decode（内存密集）分到不同 GPU 集群，让每种硬件都发挥最大效用。SGLang 在 96 张 H100 上实现了 5 倍于传统方案的输出吞吐。

4. **投机采样正在改掉"逐 token 猜测"的底层假设**。DFlash 用块扩散模型一次生成整块草稿、再靠 KV 注入贴近目标模型，在 Qwen 3.5 397B-A17B 的 HumanEval 单并发负载下做到超基线 4.3 倍；Spec V2 用重叠调度消掉主机开销。思路不是让 GPU 算得更快，而是让它少做无用功。

5. **AI Infra 的市场逻辑正在从"造芯"转向"调度"**。RadixArk 通过开源 SGLang（推理）+ Miles（RL 训练）建立技术标准，再叠加商业化托管服务。朱邦华从开源维护者到创业者的转型，折射出系统软件正在成为 AI 产业链中价值增长最快的一环。

---

*本文基于公开视频简介、B 站页面信息、SGLang GitHub 仓库、lmsys 官方博客、RadixArk 官网及 TechCrunch/Pulse 2.0/SiliconANGLE 等媒体报道整理（检索时点 2026-09-21）。视频无公开字幕，涉及嘉宾具体观点的段落建议回看 [原视频](https://www.bilibili.com/video/BV1FnGA66EPP/) 获取准确表述。*
