---
title: "NeMo Skills：LLM 技能提升流水线完全指南"
date: 2026-04-01T16:50:00+08:00
slug: nemo-skills-llm-skill-pipeline-guide
categories: ["技术笔记"]
tags: ["NeMo Skills", "LLM", "NVIDIA", "合成数据", "模型训练", "评估基准"]
description: "NVIDIA 开源 LLM 技能提升工具集 NeMo Skills 完全指南，涵盖合成数据生成、模型训练、基准评估等全方位讲解。"
---
# NeMo Skills：LLM 技能提升流水线完全指南

## 一、项目概述

### 1.1 什么是 NeMo Skills

**NeMo Skills** 是 NVIDIA 开源的 LLM 技能提升工具集，提供从合成数据生成、模型训练到基准评估的完整流水线。支持在本地工作站运行，并可一键扩展到大规模 Slurm 集群。

### 1.2 关键数据

| 指标 | 数值 |
|------|------|
| **GitHub Stars** | 905 |
| **GitHub Forks** | 169 |
| **协议** | Apache-2.0 |
| **主语言** | Python 98.9% |
| **提交数** | 1,089 |
| **贡献者** | 87+ |

### 1.3 核心定位

NeMo Skills 围绕 LLM 开发全流程：
- **合成数据生成**（SDG）
- **模型训练**（Training）
- **基准评估**（Evaluation）

> 免责声明：此项目仅用于研究目的，非 NVIDIA 官方产品。

---

## 二、核心功能

### 2.1 灵活的 LLM 推理

| 功能 | 说明 |
|------|------|
| **多后端支持** | TensorRT-LLM、vLLM、sglang、Megatron |
| **无缝切换** | API 提供商、本地服务、Slurm 集群一键切换 |
| **弹性扩展** | 从1块GPU扩展到数万台GPU |

### 2.2 模型评估

NeMo Skills 支持全方位评估：

| 类别 | 基准 |
|------|------|
| **数学（自然语言）** | aime24、aime25、hmmt_feb25 |
| **数学（形式语言）** | minif2f、proofnet、putnam-bench |
| **代码** | swe-bench、livecodebench、bird |
| **科学知识** | hle、scicode、gpqa |
| **指令遵循** | ifbench、ifeval |
| **长上下文** | ruler、mrcr、aalcr、longbench-v2 |
| **工具调用** | bfcl_v3 |
| **多语言** | mmlu-prox、flores-200、wmt24pp |
| **语音与音频** | asr-leaderboard、mmau-pro |
| **视觉语言模型** | mmmu-pro |

### 2.3 模型训练

| 框架 | 说明 |
|------|------|
| **NeMo-RL** | NVIDIA RL 训练框架 |
| **verl** | Volcengine RL 训练框架 |

---

## 三、快速开始

### 3.1 安装

```bash
# 克隆仓库
git clone https://github.com/NVIDIA-NeMo/Skills.git
cd Skills

# 安装依赖
pip install -e .

# 验证安装
ns --help
```

### 3.2 基本命令

```bash
# 查看所有可用命令
ns --help

# 运行评估
ns eval --model nvidia/nemotron-3-8b

# 运行数据生成
ns generate --model meta-llama/llama-3
```

### 3.3 配置

```bash
# 查看配置选项
ns config --help

# 设置 API key
export OPENAI_API_KEY=your_key
```

---

## 四、评估流水线

### 4.1 评估配置

```yaml
# evaluation.yaml
model: nvidia/nemotron-3-8b
benchmarks:
  - math/aime24
  - code/swe-bench
  - instruction/ifbench
parallel: 8  # 并行 Slurm 任务数
judge: self-host  # 自托管 LLM 评判
```

### 4.2 运行评估

```bash
# 运行完整评估
ns eval --config evaluation.yaml

# 运行特定基准
ns eval --benchmark math/aime24

# 分布式评估
ns eval --parallel 64
```

### 4.3 评估结果

| 指标 | pass@1 | GenSelect |
|------|---------|-----------|
| 数学 | 提升显著 | 领先 |
| 代码 | 提升显著 | 领先 |
| 科学 | 提升显著 | 领先 |

---

## 五、合成数据生成（SDG）

### 5.1 SDG 配置

```yaml
# sdg.yaml
model: meta-llama/llama-3.1-405b
num_gpus: 8
batch_size: 32
temperature: 0.8
top_p: 0.95
```

### 5.2 运行 SDG

```bash
# 生成数学数据
ns generate --task math --num_samples 100000

# 生成代码数据
ns generate --task code --num_samples 50000

# 扩展到集群
ns generate --task math --num_gpus 1024
```

### 5.3 数据质量

生成的合成数据经过多轮过滤和质量评估，确保高质量。

---

## 六、模型训练

### 6.1 训练流水线

```bash
# 使用 NeMo-RL 训练
ns train --config train.yaml --framework nemorl

# 使用 verl 训练
ns train --config train.yaml --framework verl
```

### 6.2 分布式训练

```bash
# 单节点多卡
ns train --num_gpus 8

# 多节点集群
ns train --num_nodes 32 --num_gpus_per_node 8
```

---

## 七、已发布模型与数据集

### 7.1 OpenReasoning

| 模型 | 说明 | 发布时间 |
|------|------|----------|
| **OpenReasoning** | 数学、代码、科学 SoTA | 2025-07-18 |

**评估结果**：在数学、代码、科学基准上达到当时最高水平。

### 7.2 OpenMathReasoning

**数据集规模**：
- 306K 数学问题（来自 AoPS 论坛）
- 3.2M 长链式思维（CoT）解决方案
- 1.7M 工具集成推理（TIR）解决方案
- 566K GenSelect 样本

**模型**：OpenMath-Nemotron 系列，在发布时为开源数学推理最强模型。

### 7.3 OpenMathInstruct-2

**数据集**：14M 问题-解决方案对（使用 Llama3.1-405B-Instruct 生成）

**效果**：相比 Llama3.1-Instruct 有显著提升。

### 7.4 Nemotron-Math-v2

**数据集**：用于训练 NVIDIA-Nemotron-3-Nano-30B-A3B-BF16

### 7.5 Nemotron-Post-Training-Dataset-v1

用于训练 OpenReasoning 模型，包含数学和代码数据。

---

## 八、架构分析

### 8.1 目录结构

```
Skills/
├── core/                 # 核心模块
├── docs/                 # 文档
├── nemo_skills/         # NeMo Skills 核心代码
├── recipes/             # 训练配方
├── requirements/        # 依赖
├── tests/              # 测试
├── dockerfiles/         # Docker 配置
├── cluster_configs/     # 集群配置
└── recipes/            # 训练脚本
```

### 8.2 核心组件

| 组件 | 说明 |
|------|------|
| **推理引擎** | 支持多后端推理 |
| **评估器** | 多基准评估 |
| **数据生成器** | 合成数据生成 |
| **训练器** | 分布式训练支持 |

### 8.3 扩展机制

| 扩展点 | 说明 |
|--------|------|
| **自定义基准** | 添加新的评估基准 |
| **自定义模型** | 支持新的模型后端 |
| **自定义数据** | 使用自有数据集训练 |

---

## 九、集群部署

### 9.1 单机部署

```bash
# 本地安装
pip install -e .

# 快速测试
ns eval --benchmark math/aime24
```

### 9.2 Slurm 集群部署

```bash
# 配置集群
ns cluster setup --config cluster_config.yaml

# 提交集群任务
ns submit --num_gpus 1024 --task generate
```

### 9.3 Docker 部署

```bash
# 构建镜像
docker build -t nemo-skills:latest -f dockerfiles/Dockerfile .

# 运行容器
docker run --gpus all nemo-skills:latest ns --help
```

---

## 十，最佳实践

### 10.1 评估优化

| 优化 | 方法 |
|------|------|
| **并行评估** | 使用 Slurm 并行化 |
| **自托管评判** | 减少 API 调用成本 |
| **批量处理** | 提高吞吐量 |

### 10.2 数据生成优化

| 优化 | 方法 |
|------|------|
| **温度采样** | 根据任务调整 temperature |
| **去重过滤** | 去除重复样本 |
| **质量过滤** | 多轮质量评估 |

### 10.3 训练优化

| 优化 | 方法 |
|------|------|
| **梯度累积** | 增加有效 batch size |
| **混合精度** | 加速训练 |
| **分布式** | 多节点并行 |

---

## 十一，常见问题

**Q1: NeMo Skills 和 NeMo有什么区别？**

NeMo 是 NVIDIA 的对话式 AI 框架，NeMo Skills 是构建在 NeMo 之上的 LLM 技能提升工具集。

**Q2: 需要什么硬件？**

推理可以本地运行，训练建议使用 NVIDIA GPU（8卡以上）。

**Q3: 如何添加自定义基准？**

参考 docs/ 目录下的指南，创建新的基准配置文件即可。

---

## 十二，项目信息

| 信息 | 内容 |
|------|------|
| 许可证 | Apache-2.0 |
| 主语言 | Python 98.9% |
| 文档 | [nvidia-nemo.github.io/Skills](https://nvidia-nemo.github.io/Skills/) |

---

## 相关链接

💻 **GitHub**：[NVIDIA-NeMo/Skills](https://github.com/NVIDIA-NeMo/Skills)

📖 **文档**：[nvidia-nemo.github.io/Skills](https://nvidia-nemo.github.io/Skills/)

🤖 **HuggingFace**：[nvidia](https://huggingface.co/nvidia)
