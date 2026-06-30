---
title: "RD-Agent：微软自动化研发智能体完全指南"
date: "2026-04-01T16:55:00+08:00"
slug: rd-agent-microsoft-research-automation-guide
aliases:
  - /posts/tech/rd-agent-microsoft-research-automation-guide/
categories: ["技术笔记"]
tags: ["RD-Agent", "Microsoft", "AI Agent", "量化交易", "MLE-bench", "自动化研发"]
description: "微软研究院开源的自动化研发智能体框架 RD-Agent 完全指南，涵盖 RD 循环、MLE-bench 最强性能、RD-Agent(Q) 量化交易等全方位讲解。"
---

## 学习目标

阅读本文后，你将能够：

1. **理解 RD-Agent 的核心设计**：掌握 R（研究）和 D（开发）自动化循环的原理
2. **部署 RD-Agent**：在本地或服务器上安装和配置 RD-Agent
3. **运行 MLE-bench**：使用 RD-Agent 参加机器学习工程竞赛
4. **应用 RD-Agent(Q)**：将 RD-Agent 应用到量化交易场景
5. **扩展 RD-Agent**：自定义新的研究循环和开发策略
6. **贡献到 RD-Agent**：理解代码结构，提交 PR 和改进建议

---



# RD-Agent：微软自动化研发智能体完全指南

> 预计阅读时间：35 分钟 | 难度：⭐⭐⭐⭐

---

> **目标读者**：AI 研究工程师、自动化研发从业者

## 一、项目概述

### 1.1 什么是 RD-Agent

**RD-Agent**（Research & Development Agent）是微软研究院开源的自动化研发智能体框架，专注于数据驱动场景的模型和数据的自动化开发。框架核心设计思路是**"R"代表提出新想法，"D"代表实现它们**，通过自动化的研究循环推动具有工业价值的技术创新。

### 1.2 关键数据

| 指标 | 数值 |
|------|------|
| **GitHub Stars** | 12,164 |
| **GitHub Forks** | 1,420 |
| **协议** | MIT |
| **主语言** | Python 98.9% |
| **提交数** | 1,005 |
| **发布版本** | 已发布 |

### 1.3 定位

RD-Agent 致力于自动化工业研发中最关键和最有价值的环节：
- **数据驱动**：从真实材料（报告、论文等）中提取关键公式和特征
- **自动化循环**：提出想法 → 实现 → 验证 → 改进
- **端到端**：覆盖从研究到落地的完整流程

---

## 二、MLE-Bench 最强选手

### 2.1 MLE-Bench 是什么

MLE-Bench 是 OpenAI 发布的基准测试，评估 AI 智能体在 75 个 Kaggle 竞赛上的机器学习工程能力，涵盖真实世界的 ML 工程场景。

### 2.2 RD-Agent 性能

**RD-Agent 在 MLE-Bench 上稳居榜首：**

| Agent | Low=Lite (%) | Medium (%) | High (%) | All (%) |
|-------|-------------|------------|----------|----------|
| **RD-Agent o3(R)+GPT-4.1(D)** | 51.52±6.9 | 19.3±5.5 | 26.67±0 | **30.22±1.5** |
| **RD-Agent o1-preview** | 48.18±2.49 | 8.95±2.36 | 18.67±2.98 | **22.4±1.1** |
| AIDE o1-preview (基线) | 34.3±2.4 | 8.8±1.1 | 10.0±1.9 | 16.9±1.1 |

> **o3(R)+GPT-4.1(D)** 版本的特殊设计：用 Research Agent (o3) 与 Development Agent (GPT-4.1) 协同，在降低成本的同时提升效率。

**难度分级标准（MLE-Bench）：**
- **Low=Lite**：资深 ML 工程师可在 2 小时内完成（不含模型训练）
- **Medium**：需要 2-10 小时
- **High**：需要 10 小时以上

### 2.3 详细运行记录

| 版本 | 详细记录 |
|------|----------|
| RD-Agent o1-preview | [在线查看](https://aka.ms/RD-Agent_MLE-Bench_O1-preview) |
| RD-Agent o3(R)+GPT-4.1(D) | [在线查看](https://aka.ms/RD-Agent_MLE-Bench_O3_GPT41) |

---

## 三、RD-Agent(Q)：智能量化交易

### 3.1 核心定位

**RD-Agent(Q)** 是首个**数据中心的量化多智能体框架**，通过协同的因子-模型联合优化，自动化量化策略的全栈研发和交易。

### 3.2 核心性能

| 指标 | 数值 |
|------|------|
| **成本** | 低于 $10 |
| **ARR 提升** | 相比基准因子库提升 **2 倍** |
| **因子数量** | 减少 **70%** |
| **效果** | 超越 SOTA 深度时序模型 |

### 3.3 交替优化

RD-Agent(Q) 采用**交替因子-模型优化**：
- **因子优化**：发现对预测更有价值的新因子
- **模型优化**：基于新因子优化预测模型
- **协同增强**：两者相互促进，实现更优的准确性和鲁棒性平衡

---

## 四、核心架构

### 4.1 目录结构

```text

### 4.2 核心模块

| 模块 | 说明 |
|------|------|
| **Research Agent (R)** | 提出新想法、研究假设 |
| **Development Agent (D)** | 实现代码、验证想法 |
| **Factor Loop** | 因子发现与优化 |
| **Model Loop** | 模型架构与训练 |
| **Data Mining** | 数据提取与特征工程 |

---

## 五、快速开始

### 5.1 系统要求

> ⚠️ **RD-Agent 目前仅支持 Linux 系统**

### 5.2 Docker 安装（推荐）

```bash
# 确保 Docker 已安装
docker run hello-world

# 创建 conda 环境
conda create -n rdagent python=3.10
conda activate rdagent

# 安装 RD-Agent
pip install rdagent

# 健康检查
rdagent health_check --no-check-env
```textbash
git clone https://github.com/microsoft/RD-Agent
cd RD-Agent
make dev
```textbash
cat << EOF > .env
CHAT_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_BASE=<your_unified_api_base>
OPENAI_API_KEY=<your_openai_api_key>
EOF
```textbash
cat << EOF > .env
EMBEDDING_MODEL=azure/<Model deployment>
CHAT_MODEL=azure/<your deployment name>
AZURE_API_KEY=<your_key>
AZURE_API_BASE=<your_base>
AZURE_API_VERSION=<api_version>
EOF
```textbash
cat << EOF > .env
# 使用 DeepSeek 官方 API
CHAT_MODEL=deepseek/deepseek-chat
DEEPSEEK_API_KEY=<your_key>

# 嵌入使用 SiliconFlow（DeepSeek 无嵌入模型）
EMBEDDING_MODEL=litellm_proxy/BAAI/bge-m3
LITELLM_PROXY_API_KEY=<your_siliconflow_key>
LITELLM_PROXY_API_BASE=https://api.siliconflow.cn/v1
EOF
```textbash
REASONING_THINK_RM=True
```textbash
rdagent fin_quant
```textbash
rdagent fin_factor
```textbash
rdagent fin_model
```textbash
# 准备财报数据
wget https://github.com/SunsetWolf/rdagent_resource/releases/download/reports/all_reports.zip
unzip all_reports.zip -d git_ignore_folder/reports

# 运行
rdagent fin_factor_report --report-folder=git_ignore_folder/reports
```textbash
# 下载数据集
wget https://github.com/SunsetWolf/rdagent_resource/releases/download/ds_data/arf-12-hours-prediction-task.zip
unzip arf-12-hours-prediction-task.zip -d ./git_ignore_folder/ds_data

# 配置环境变量
dotenv set DS_LOCAL_DATA_PATH="$(pwd)/git_ignore_folder/ds_data"
dotenv set DS_CODER_ON_WHOLE_PIPELINE True
dotenv set DS_IF_USING_MLE_DATA False
dotenv set DS_SAMPLE_DATA_BY_LLM False
dotenv set DS_SCEN rdagent.scenarios.data_science.scen.DataScienceScen

# 运行
rdagent data_science --competition arf-12-hours-prediction-task
```textbash
# 1. 配置 Kaggle API
# (1) 创建 API Token: Settings → Create New Token → 下载 kaggle.json
# (2) 移动到 ~/.config/kaggle/
# (3) 修改权限: chmod 600 ~/.config/kaggle/kaggle.json

# 2. 加入竞赛
# 访问 Kaggle 竞赛页面点击 Join Competition

# 3. 运行
mkdir -p ./git_ignore_folder/ds_data
dotenv set DS_LOCAL_DATA_PATH="$(pwd)/git_ignore_folder/ds_data"
dotenv set DS_CODER_ON_WHOLE_PIPELINE True
dotenv set DS_IF_USING_MLE_DATA True
dotenv set DS_SAMPLE_DATA_BY_LLM True
dotenv set DS_SCEN rdagent.scenarios.data_science.scen.KaggleScen

rdagent data_science --competition tabular-playground-series-dec-2021
```textbash
rdagent general_model <paper_url>

# 示例
rdagent general_model "https://arxiv.org/pdf/2210.09789"
```textbash
rdagent ui --port 19899 --log-dir log/ --data-science
```textbash
cd web
npm install
npm run build:flask  # 为 Flask 后端构建

# 启动
rdagent server_ui --port 19899
# 访问 http://127.0.0.1:19899
```textbash
rdagent health_check --no-check-env --no-check-docker
```text
Research → Develop → Verify → (迭代)
    ↑                        ↓
    ←←←←←←←←←←←←←←←←←←←←←
```

### 9.3 后端支持

| 后端 | 说明 |
|------|------|
| **LiteLLM** | 默认支持，多提供商 |
| **OpenAI API** | 传统支持 |
| **Azure OpenAI** | 企业级支持 |
| **DeepSeek** | 实验性支持 |

---

## 十，推荐做法

### 10.1 环境配置

| 检查项 | 命令 |
|--------|------|
| Docker 安装 | `docker run hello-world` |
| 健康检查 | `rdagent health_check` |
| 端口占用 | `rdagent health_check --no-check-env --no-check-docker` |

### 10.2 量化交易建议

| 建议 | 说明 |
|------|------|
| **低成本** | RD-Agent(Q) 在 $10 以内即可运行 |
| **少因子** | 相比传统方法减少 70% 因子 |
| **交替优化** | 因子-模型协同进化 |

### 10.3 Kaggle 竞赛建议

| 步骤 | 操作 |
|------|------|
| **API 配置** | 创建并配置 kaggle.json |
| **数据准备** | 下载并解压数据集 |
| **参数调优** | 使用 RD-Agent 自动调参 |

---

## 十一、常见问题

**Q1: RD-Agent 支持 Windows 或 macOS 吗？**

目前仅支持 Linux 系统。

**Q2: 如何选择 LLM 后端？**

推荐使用 LiteLLM 后端，支持 OpenAI、Azure、DeepSeek 等多个提供商。

**Q3: MLE-bench 上 RD-Agent 的优势是什么？**

通过 Research Agent 和 Development Agent 的分工协作，RD-Agent 能在复杂 ML 工程任务上取得领先成绩。

**Q4: RD-Agent(Q) 的成本如何？**

在低于 $10 的成本下，RD-Agent(Q) 能实现比基准因子库高 2 倍的 ARR。

---

## 十二、项目信息

| 信息 | 内容 |
|------|------|
| 许可证 | MIT |
| 主语言 | Python 98.9% |
| 文档 | [rdagent.readthedocs.io](https://rdagent.readthedocs.io/en/latest/) |
| 论文 | [arXiv:2505.14738](https://arxiv.org/abs/2505.14738) |
| 技术报告 | [RD-Agent Tech Report](https://aka.ms/RD-Agent-Tech-Report) |

---

## 相关链接

💻 **GitHub**：[microsoft/RD-Agent](https://github.com/microsoft/RD-Agent)

🖥️ **在线演示**：[rdagent.azurewebsites.net](https://rdagent.azurewebsites.net)

📖 **文档**：[rdagent.readthedocs.io](https://rdagent.readthedocs.io/en/latest/index.html)

📄 **论文**：[arXiv](https://arxiv.org/abs/2505.14738)

🎥 **演示视频**：[YouTube](https://www.youtube.com/watch?v=JJ4JYO3HscM)



---

## 自测题

### 问题 1：RD-Agent 的核心设计是什么？

<details>
<summary>查看答案</summary>

RD-Agent 的核心设计是"R"（研究）和"D"（开发）自动化循环：提出想法 → 实现 → 验证 → 改进。

</details>

### 问题 2：RD-Agent 在 MLE-bench 上的表现如何？

<details>
<summary>查看答案</summary>

RD-Agent 是 MLE-bench 的最强选手，在 75 个 Kaggle 竞赛上展现出顶尖的机器学习工程能力。

</details>

### 问题 3：RD-Agent(Q) 是什么？

<details>
<summary>查看答案</summary>

RD-Agent(Q) 是将 RD-Agent 应用到量化交易场景的版本，自动化研究和开发量化交易策略。

</details>

### 问题 4：如何部署 RD-Agent？

<details>
<summary>查看答案</summary>

RD-Agent 是 Python 项目，可以通过 pip 安装，或在 Docker 中运行。

</details>

### 问题 5：如何贡献到 RD-Agent？

<details>
<summary>查看答案</summary>

阅读 CONTRIBUTING.md，提交 PR、修复 Bug、改进文档、分享使用案例。

</details>

---

## 练习

### 练习 1：部署 RD-Agent 并运行示例

**任务**：在本地部署 RD-Agent，运行官方示例，理解 R&D 循环。

**参考答案**：
```bash
# 参考 RD-Agent GitHub 仓库的 README
```

### 练习 2：参加 MLE-bench 竞赛

**任务**：使用 RD-Agent 参加一个 Kaggle 竞赛，提交结果。

**参考答案**：
```python
# 参考 RD-Agent 的 MLE-bench 示例代码
```

### 练习 3：扩展 RD-Agent 支持新的模型

**任务**：修改 RD-Agent 的代码，支持新的 LLM（如本地部署的模型）。

**参考答案**：
```python
# 参考 RD-Agent 的模型配置代码
```

---

## 进阶路径

如果你已经掌握本文内容，可以继续深入以下方向：

1. **深入研究 RD-Agent 架构**：了解核心模块、循环机制、策略实现
2. **优化 R&D 循环**：研究如何提升想法质量、实现效率、验证准确性
3. **应用到新领域**：将 RD-Agent 应用到其他数据驱动领域（如生物信息、材料科学）
4. **贡献到 RD-Agent 项目**：提交 PR、修复 Bug、改进文档
5. **构建企业级部署**：研究如何在企业环境中部署 RD-Agent（数据隐私、权限管理、审计日志）
6. **集成到 ML 平台**：将 RD-Agent 集成到 MLflow、Kubeflow 等 ML 平台
7. **研究自动化研发**：深入研究自动化机器学习、AutoML、AI 研究的未来方向

---

## 资料口径说明

本文档基于以下来源和假设：

1. **信息来源**：本文基于 RD-Agent GitHub 仓库（https://github.com/microsoft/RD-Agent）的 README、论文和文档
2. **版本时效性**：本文描述的是 RD-Agent 的主分支代码，可能与你使用的版本存在差异
3. **性能数据**：本文提到的 MLE-bench 性能数据基于微软研究院的评估结果，实际表现可能因任务而异
4. **量化交易**：RD-Agent(Q) 的量化交易能力是基于研究原型，实际投资需谨慎
5. **更新记录**：本文最后更新于 2026-04-01。如果项目有重大更新，请及时更新本文档

---

