---
title: "RD-Agent：微软自动化研发智能体完全指南"
date: "2026-04-01T16:55:00+08:00"
lastmod: "2026-09-23T10:00:00+08:00"
slug: rd-agent-microsoft-research-automation-guide
github_repo: "microsoft/RD-Agent"
source_key: "gh:microsoft/RD-Agent"
aliases:
  - /posts/tech/rd-agent-microsoft-research-automation-guide/
categories: ["技术笔记"]
tags: ["Microsoft", "AI Agent", "量化交易"]
description: "微软开源的自动化研发智能体框架 RD-Agent 完全指南：RD 循环机制、MLE-Bench 榜首成绩、RD-Agent(Q) 量化交易、安装配置与场景命令详解。"
---

## 学习目标

阅读本文后，你将能够：

1. **理解 RD 循环**：说清 R（研究）和 D（开发）两个智能体如何配合，以及 Copilot 与 Agent 两种角色的边界
2. **部署 RD-Agent**：在 Linux 上完成安装、模型配置和健康检查
3. **解读 MLE-Bench 成绩**：知道这些数字在测什么、优势来自哪里、不能推出什么
4. **运行量化场景**：用 RD-Agent(Q) 做因子发现和模型优化的联合迭代
5. **选择合适的 UI**：区分 Streamlit UI 和 Web UI 的分工与安全配置
6. **找到扩展路径**：定位源码结构，按官方文档扩展新场景或参与贡献

---

# RD-Agent：微软自动化研发智能体完全指南

> 预计阅读时间：30 分钟 | 难度：⭐⭐⭐⭐

---

> **目标读者**：AI 研究工程师、自动化研发从业者

## 一、项目概述

### 1.1 什么是 RD-Agent

**RD-Agent**（Research & Development Agent）是微软开源的自动化研发智能体框架，聚焦数据驱动场景中模型和数据的自动化开发。它把工业研发中最核心的动作抽象成两个组件：**R 负责提出新想法，D 负责把想法实现成可运行的代码**，再让两者循环迭代、从真实反馈中进化。

### 1.2 关键数据

| 指标 | 数值（2026-09-23 核对） |
|------|------|
| **GitHub Stars** | 14,718 |
| **GitHub Forks** | 1,926 |
| **协议** | MIT |
| **主语言** | Python 约 87%（Web UI 前端为 Vue） |
| **提交数** | 1,019 |
| **最新发布** | v0.8.0（2025-11-03） |
| **Python 要求** | 3.10 / 3.11（CI 充分测试） |
| **平台** | 仅支持 Linux |

### 1.3 定位

RD-Agent 想自动化的是数据驱动研发的三个关键动作：

- **读材料**：从研报、论文等真实材料中提取关键公式、特征和模型描述
- **做实现**：把提取出的公式和模型写成可运行的代码，并靠反馈循环不断改进
- **提想法**：基于当前知识和观察，主动提出新的假设

围绕这套循环，项目已经落到五类场景：量化交易（Qlib 循环）、财报因子提取、论文转模型、Kaggle/数据科学竞赛，以及 LLM 微调（FT-Agent）。

---

## 二、框架怎么工作：RD 循环与场景

### 2.1 R 和 D 的分工

框架的方法论来自对数据挖掘专家日常工作的抽象：专家先提出假设（比如"RNN 结构能捕捉时序数据的模式"），然后设计实验、把实验写成代码、执行代码拿到反馈（指标、损失曲线等），再根据反馈改进下一轮迭代。

RD-Agent 把这条链自动化：

| 组件 | 职责 |
|------|------|
| **Research（R）** | 基于知识库和观察提出假设，规划实验 |
| **Development（D）** | 把假设实现为代码，执行实验 |
| **反馈回路** | 执行结果回写知识库，驱动下一轮假设质量提升 |

官方把这套设计称为第一个"支持与真实世界验证挂钩"的科研自动化框架——假设不是空转，每一轮都要在真实数据上跑出结果。

### 2.2 先分清：Copilot 与 Agent

读场景前要先拆开两个角色，它们对应两种自动化深度：

- **Copilot**：跟随人类指令，自动化重复性工作。典型如财报因子提取——人指定材料，智能体负责读和实现。
- **Agent**：更自主，主动提出想法追求更好的结果。典型如 Qlib 因子循环——无人值守地持续提出、验证、淘汰因子。

### 2.3 场景矩阵

| 领域 | 模型实现 | 数据构建 |
|------|---------|---------|
| **金融** | 🤖 迭代提出想法并进化（模型循环）；🦾 自动读财报并实现 | 🤖 迭代提出想法并进化（因子循环）；🦾 自动读财报提取因子 |
| **医疗** | 🤖 迭代提出医疗预测模型并进化 | - |
| **通用** | 🦾 自动读论文实现模型；🤖 Kaggle 自动调参 | 🤖 Kaggle 自动特征工程 |

除此之外还有两个较新的场景：**FT-Agent**（自主 LLM 微调，对应 ICML 2026 论文 FT-Dojo）和 **Agent² RL-Bench**（评估 LLM 智能体能否自主工程化 RL 后训练流程的基准）。

### 2.4 一次因子进化如何流转

以金融因子循环（`rdagent fin_factor`）为例，一条任务流是这样的：

1. 启动后，R 侧从知识库中已有的因子和回测观察出发，提出一个新因子假设（含计算逻辑描述）；
2. D 侧把假设翻译成基于 Qlib（微软开源的量化投资平台）的因子实现代码；
3. 代码在容器里执行，跑真实行情数据拿到回测指标；
4. 指标反馈回写知识库，R 侧据此决定下一步是改进这个因子还是换方向；
5. 循环往复，直到人喊停。

源码里这条链对应得也很直白：`rdagent/components/` 下有 `proposal`（提假设）、`coder`（写实现）、`runner`（跑实验）、`knowledge_management`（管知识库），场景差异主要体现在 `rdagent/scenarios/` 下的适配层。

### 2.5 仓库结构

```text
RD-Agent/
├── rdagent/                 # Python 包主体
│   ├── app/                 # 各场景 CLI 入口（qlib_rd_loop、data_science、finetune 等）
│   ├── components/          # 研发循环组件：proposal、coder、runner、knowledge_management 等
│   ├── scenarios/           # 场景适配：qlib、kaggle、data_science、finetune、rl 等
│   ├── oai/                 # LLM 后端（LiteLLM 集成、模型配置）
│   ├── core/                # 核心抽象：evolving 框架、实验、知识库、场景定义
│   ├── log/ 与 utils/
├── web/                     # Web UI 前端（Vue，配合 server_ui 使用）
├── docs/                    # 文档源文件
├── test/                    # 测试
├── constraints/             # 依赖约束
└── pyproject.toml
```

---

## 三、MLE-Bench 当前最强选手

### 3.1 MLE-Bench 在测什么

MLE-Bench 是 OpenAI 发布的基准，用 75 个 Kaggle 竞赛的真实数据集评估 AI 智能体的机器学习工程能力。它测的不是"会不会写一段训练代码"，而是完整工程链路：理解竞赛任务、处理数据、训练模型、产出可提交的结果。

### 3.2 RD-Agent 的成绩

**RD-Agent 目前位居 MLE-Bench 榜首：**

| Agent | Low=Lite (%) | Medium (%) | High (%) | All (%) |
|-------|-------------|------------|----------|----------|
| **RD-Agent o3(R)+GPT-4.1(D)** | 51.52±6.9 | 19.3±5.5 | 26.67±0 | **30.22±1.5** |
| **RD-Agent o1-preview** | 48.18±2.49 | 8.95±2.36 | 18.67±2.98 | **22.4±1.1** |
| AIDE o1-preview（此前公开最佳） | 34.3±2.4 | 8.8±1.1 | 10.0±1.9 | 16.9±1.1 |

读这组数字有三个要点：

**o3(R)+GPT-4.1(D) 的意义在成本结构，不在绝对分数。** 这个版本把研究端交给 o3、开发端交给 GPT-4.1，官方说明的设计目标是缩短每轮平均耗时、用更便宜的模型组合降低总成本。它比 o1-preview 全自用版本高出约 8 个百分点，同时更省钱——框架把"哪种能力该用哪个模型"这个问题显式拆开了。

**方差不可忽略。** o1-preview 的成绩基于 5 个独立随机种子，o3(R)+GPT-4.1(D) 基于 6 个。Low 档 ±6.9 的标准差意味着单次跑分波动不小，横向对比其他 agent 时要看多 seed 均值。

**这些数字不能推出什么：** 不代表换上最新模型就能自动复现榜首（结果绑定特定模型组合与框架版本）；All 档 30.22 是"完整做出可用提交"的比例，离 Kaggle 人类获奖水平还有明显距离；High 档只有约 27%，长周期任务仍是短板。

**难度分级标准（MLE-Bench 官方口径）：**
- **Low=Lite**：资深 ML 工程师 2 小时内可完成（不含模型训练时间）
- **Medium**：需要 2-10 小时
- **High**：需要 10 小时以上

### 3.3 详细运行记录

| 版本 | 详细记录 |
|------|----------|
| RD-Agent o1-preview | [在线查看](https://aka.ms/RD-Agent_MLE-Bench_O1-preview) |
| RD-Agent o3(R)+GPT-4.1(D) | [在线查看](https://aka.ms/RD-Agent_MLE-Bench_O3_GPT41) |

---

## 四、RD-Agent(Q)：量化交易场景

### 4.1 核心定位

**RD-Agent(Q)** 是首个数据中心的量化多智能体框架，通过因子-模型联合优化，自动化量化策略的全栈研发。这项工作对应的论文已被 NeurIPS 2025 接收。

### 4.2 核心结果

官方在真实股票市场上的实验结论：

| 指标 | 数值 |
|------|------|
| **成本** | 低于 $10 |
| **ARR**（年化收益率） | 相比基准因子库高约 2 倍 |
| **因子数量** | 减少 70% 以上 |
| **模型对比** | 在更小资源预算下超越 SOTA 深度时序模型 |

"减少 70% 以上因子"值得单独说：多数自动化因子挖掘倾向于堆数量，RD-Agent(Q) 反过来验证了"少而准"的因子集合配合联合优化，收益更高、过拟合风险更低。

### 4.3 交替优化机制

RD-Agent(Q) 的核心机制是**交替因子-模型优化**：

- **因子优化**：发现对预测更有价值的新因子
- **模型优化**：基于新因子集合优化预测模型
- **交替进行**：更好的因子让模型上限更高，更强的模型又能更准确地给因子定价，官方称这带来了预测精度与策略鲁棒性之间更好的权衡

注意官方免责声明的边界：RD-Agent 面向金融研发流程，**不构成任何投资建议**，也未达到可直接实盘的就绪度。

---

## 五、快速开始

### 5.1 系统要求

> ⚠️ **RD-Agent 目前仅支持 Linux 系统**

大多数场景依赖 Docker，安装前确认当前用户**不使用 sudo** 即可运行 Docker 命令：

```bash
docker run hello-world
```

### 5.2 安装

**用户安装**（推荐，conda 环境 + PyPI）：

```bash
conda create -n rdagent python=3.10
conda activate rdagent
pip install rdagent
```

**开发者安装**（想用最新版或参与贡献）：

```bash
git clone https://github.com/microsoft/RD-Agent
cd RD-Agent
make dev
```

### 5.3 健康检查

安装完成先跑一次（`--no-check-env` 表示此时还没配模型，跳过环境检查）：

```bash
rdagent health_check --no-check-env
```

`health_check` 检查三件事：环境变量配置是否有效、Docker 是否可用、默认端口（19899）是否被占用。配置好模型后不带参数再跑一次是必要步骤：

```bash
rdagent health_check
```

只查端口占用：

```bash
rdagent health_check --no-check-env --no-check-docker
```

### 5.4 配置模型

场景运行依赖三项能力：ChatCompletion、json_mode、embedding query。默认后端是 **LiteLLM**，可以用任意 LiteLLM 支持的模型。

**方式一：Chat 与 Embedding 用同一个 API base（以 OpenAI 为例）**

```bash
cat << EOF > .env
# 任何 LiteLLM 支持的模型
CHAT_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_BASE=<your_unified_api_base>
OPENAI_API_KEY=<your_openai_api_key>
EOF
```

**方式二：Chat 与 Embedding 分开配置**（例如 embedding 走 SiliconFlow，注意需要 `litellm_proxy` 前缀）

```bash
cat << EOF > .env
CHAT_MODEL=gpt-4o
OPENAI_API_BASE=<your_chat_api_base>
OPENAI_API_KEY=<your_openai_api_key>

EMBEDDING_MODEL=litellm_proxy/BAAI/bge-large-en-v1.5
LITELLM_PROXY_API_KEY=<your_siliconflow_api_key>
LITELLM_PROXY_API_BASE=https://api.siliconflow.cn/v1
EOF
```

**Azure OpenAI**（使用前确认你的 Azure 密钥支持 embedding 模型）：

```bash
cat << EOF > .env
EMBEDDING_MODEL=azure/<Model deployment supporting embedding>
CHAT_MODEL=azure/<your deployment name>
AZURE_API_KEY=<your_key>
AZURE_API_BASE=<your_base>
AZURE_API_VERSION=<api_version>
EOF
```

**DeepSeek**（实验性支持；DeepSeek 没有嵌入模型，embedding 走 SiliconFlow）：

```bash
cat << EOF > .env
CHAT_MODEL=deepseek/deepseek-chat
DEEPSEEK_API_KEY=<your_deepseek_api_key>

EMBEDDING_MODEL=litellm_proxy/BAAI/bge-m3
LITELLM_PROXY_API_KEY=<your_siliconflow_key>
LITELLM_PROXY_API_BASE=https://api.siliconflow.cn/v1
EOF
```

**推理模型注意**：如果所用模型的回复里带思考过程（如 `<think>` 标签），需要额外设置：

```bash
REASONING_THINK_RM=True
```

> 直接使用 OpenAI API 或 Azure OpenAI 的旧配置方式属于**已弃用（deprecated）后端**，仍可用但不建议新项目采用，配置细节见官方文档。

---

## 六、运行场景命令

以下命令每个对应一个官方演示，选择需要的场景运行。

### 6.1 量化交易三个入口

```bash
rdagent fin_quant    # 因子与模型联合进化（Qlib 自循环）
rdagent fin_factor   # 仅因子进化
rdagent fin_model    # 仅模型进化
```

### 6.2 财报因子提取

```bash
# 一般形式
rdagent fin_factor_report --report-folder=<your financial reports folder>

# 具体例子：先下载示例财报
wget https://github.com/SunsetWolf/rdagent_resource/releases/download/reports/all_reports.zip
unzip all_reports.zip -d git_ignore_folder/reports
rdagent fin_factor_report --report-folder=git_ignore_folder/reports
```

### 6.3 论文转模型实现

```bash
rdagent general_model <paper_url>

# 示例
rdagent general_model "https://arxiv.org/pdf/2210.09789"
```

更多论文示例用 `rdagent general_model -h` 查看。

### 6.4 数据科学竞赛（本地数据）

```bash
# 下载数据集
wget https://github.com/SunsetWolf/rdagent_resource/releases/download/ds_data/arf-12-hours-prediction-task.zip
unzip arf-12-hours-prediction-task.zip -d ./git_ignore_folder/ds_data/

# 配置环境变量
dotenv set DS_LOCAL_DATA_PATH "$(pwd)/git_ignore_folder/ds_data"
dotenv set DS_CODER_ON_WHOLE_PIPELINE True
dotenv set DS_IF_USING_MLE_DATA False
dotenv set DS_SAMPLE_DATA_BY_LLM False
dotenv set DS_SCEN rdagent.scenarios.data_science.scen.DataScienceScen

# 运行
rdagent data_science --competition arf-12-hours-prediction-task
```

下载竞赛描述文件时需要用到 chromedriver。

### 6.5 Kaggle 竞赛

前置步骤：

1. 注册并登录 Kaggle；
2. 配置 API：头像 → `Settings` → `Create New Token` 下载 `kaggle.json`，移到 `~/.config/kaggle/`，执行 `chmod 600 ~/.config/kaggle/kaggle.json`；
3. 在[竞赛详情页](https://www.kaggle.com/competitions/tabular-playground-series-dec-2021/data)点击 `Join Competition` 接受规则。

```bash
mkdir -p ./git_ignore_folder/ds_data
dotenv set DS_LOCAL_DATA_PATH "$(pwd)/git_ignore_folder/ds_data"
dotenv set DS_CODER_ON_WHOLE_PIPELINE True
dotenv set DS_IF_USING_MLE_DATA True
dotenv set DS_SAMPLE_DATA_BY_LLM True
dotenv set DS_SCEN rdagent.scenarios.data_science.scen.KaggleScen

rdagent data_science --competition tabular-playground-series-dec-2021
```

### 6.6 LLM 微调（FT-Agent）

```bash
# 运行前需配置 FT_TARGET_BENCHMARK 与 FT_BENCHMARK_DESCRIPTION
rdagent llm_finetune --base-model Qwen/Qwen2.5-7B-Instruct
```

完整的基准说明、数据集注意事项和示例见仓库 `rdagent/app/finetune/llm/README.md`。

---

## 七、监控运行结果：两个 UI

RD-Agent 有两个界面，分工不同，不要混用。

### 7.1 Streamlit UI

查看运行日志，**data_science 场景目前只能用它看**：

```bash
rdagent ui --port 19899 --log-dir log/ --data-science
```

`--data-science` 设为 `True` 时展示数据科学场景日志，否则设为 `False`。

### 7.2 Web UI

`web/` 目录下是独立的前端，配合 Flask 后端 `server_ui` 使用，支持实时交互和轨迹查看（暂不支持 data_science 场景）：

```bash
cd web
npm install
npm run build:flask   # 构建静态资源到 server_ui 默认目录

rdagent server_ui --port 19899
# 访问 http://127.0.0.1:19899
```

安全机制要知道四条：

1. **默认只绑 127.0.0.1，无需认证 token**，进程控制、上传、轨迹 API 仅本机可访问；
2. **远程访问必须显式配置 token**，服务器拒绝在未设 token 时绑定非本地地址：

```bash
export UI_SERVER_AUTH_TOKEN='<a-long-random-token>'
rdagent server_ui --port 19899 --host 0.0.0.0
```

浏览器首次用 `http://<server-host>:19899/?token=<token>` 建立会话，token 随后存入 HTTP-only cookie；API 客户端改用 `Authorization: Bearer <token>` 请求头。公网暴露时官方建议套 HTTPS 反向代理，并避免在代理日志里记录带 token 的查询串。

3. **上传文件与轨迹目录隔离**：上传目录（`UI_UPLOAD_FOLDER`，默认 `./git_ignore_folder/uploads`）里的文件不会被当作持久化轨迹反序列化；`.dill`、`.pickle`、`.pkl`、`.py`、`.pyc`、`.pyo` 结尾的上传文件直接拒绝；
4. **旧版 pickle 轨迹默认不加载**（pickle 反序列化可执行代码），确需加载受信任的历史轨迹时显式开启 `UI_LOAD_LEGACY_PICKLE_TRACES=true`。

常用存储相关环境变量：

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `UI_STATIC_PATH` | `./git_ignore_folder/static` | Web UI 静态资源目录 |
| `UI_TRACE_FOLDER` | `./git_ignore_folder/traces` | 轨迹数据与进程日志目录 |
| `UI_UPLOAD_FOLDER` | `./git_ignore_folder/uploads` | 上传文件隔离目录，需单独挂载/备份/清理 |
| `UI_SERVER_AUTH_TOKEN` | 空 | 非 localhost 绑定时必填 |
| `UI_CORS_ALLOWED_ORIGINS` | `[]` | JSON 数组形式的浏览器源白名单，空即禁用 CORS |
| `UI_MAX_UPLOAD_MB` | `20` | 单个 HTTP 请求（含全部上传文件）上限，单位 MiB |

> 端口 `19899` 是示例默认值，启动前建议用 `rdagent health_check --no-check-env --no-check-docker` 确认未被占用。

---

## 八、推荐做法

| 环节 | 建议 |
|------|------|
| **环境** | Linux + Docker 免 sudo + conda（Python 3.10/3.11），装完先跑 `health_check` |
| **模型选择** | 默认走 LiteLLM；新配置不要用已弃用的旧后端 |
| **量化场景** | 先用 `fin_factor`（单循环）验证配置，再上 `fin_quant`（联合进化） |
| **成本控制** | 参考 o3(R)+GPT-4.1(D) 的思路：研究端与开发端用不同价位的模型组合 |
| **远程部署 UI** | 必须配 `UI_SERVER_AUTH_TOKEN`，并置于 HTTPS 反向代理之后 |
| **Kaggle 场景** | 该场景是当前官方重点开发方向，注意跟进版本更新 |

---

## 九、常见问题

**Q1: RD-Agent 支持 Windows 或 macOS 吗？**

不支持，官方明确仅支持 Linux。Windows 用户可用 WSL2，macOS 用户可用远程 Linux 环境，但官方只对 Linux 提供支持承诺。

**Q2: 如何选择 LLM 后端？**

默认 LiteLLM 后端，同一套 `.env` 写法适配 OpenAI、Azure、DeepSeek、SiliconFlow 等提供商。如果模型的回复带 `<think>` 标签，记得设 `REASONING_THINK_RM=True`。

**Q3: MLE-Bench 上 RD-Agent 的优势来自哪里？**

R/D 分工让"提出想法"和"实现想法"各自演化，配合从真实反馈中改进的知识库。o3+GPT-4.1 组合还证明了研究端与开发端可以按能力需求分别选型，兼顾分数与成本。

**Q4: RD-Agent(Q) 的成本与效果如何？**

官方实验口径：低于 $10 的模型调用成本，ARR 相比基准因子库高约 2 倍，因子数量减少 70% 以上，并在更小资源预算下超越 SOTA 深度时序模型。实验结论，非收益承诺。

**Q5: Streamlit UI 和 Web UI 用哪个？**

看 data_science 场景日志用 Streamlit（`rdagent ui --data-science`）；需要实时交互和轨迹查看用 Web UI（`rdagent server_ui`），后者暂不支持 data_science 场景。

---

## 十、项目信息

| 信息 | 内容 |
|------|------|
| 许可证 | MIT |
| 主语言 | Python 约 87%（含 Vue Web UI） |
| 文档 | [rdagent.readthedocs.io](https://rdagent.readthedocs.io/en/latest/) |
| 总技术报告 | [arXiv:2505.14738](https://arxiv.org/abs/2505.14738) |
| 量化论文 | [R&D-Agent-Quant, arXiv:2505.15155](https://arxiv.org/abs/2505.15155)（NeurIPS 2025） |
| 微调论文 | [FT-Dojo, arXiv:2603.01712](https://arxiv.org/abs/2603.01712)（ICML 2026） |
| 基准论文 | [Agent² RL-Bench, arXiv:2604.10547](https://arxiv.org/abs/2604.10547) |

项目论文谱系还包括早期方法论工作《Towards Data-Centric Automatic R&D》（arXiv:2404.11276）与《Collaborative Evolving Strategy for Automatic Data-Centric Development》（arXiv:2407.18690），以及入选 ACL 2026 Findings 的《Reasoning as Gradient》（arXiv:2603.01692）。

---

## 相关链接

💻 **GitHub**：[microsoft/RD-Agent](https://github.com/microsoft/RD-Agent)

🖥️ **在线演示**：[rdagent.azurewebsites.net](https://rdagent.azurewebsites.net)

📖 **文档**：[rdagent.readthedocs.io](https://rdagent.readthedocs.io/en/latest/index.html)

📄 **技术报告**：[RD-Agent Tech Report](https://aka.ms/RD-Agent-Tech-Report)

🎥 **演示视频**：[YouTube 播放列表](https://www.youtube.com/watch?v=JJ4JYO3HscM&list=PLALmKB0_N3_i52fhUmPQiL4jsO354uopR)

💬 **社区**：[Discord](https://discord.gg/ybQ97B6Jjy) | [微信群二维码（issue #880）](https://github.com/microsoft/RD-Agent/issues/880)

📦 **成功案例轨迹**：[demo_traces.zip](https://github.com/SunsetWolf/rdagent_resource/releases/download/demo_traces/demo_traces.zip)（官方 Live Demo 展示的 5 条执行轨迹，可用 `rdagent ui` 回放）

---

## 自测题

### 问题 1：RD-Agent 把研发过程拆成了哪两个组件？各自负责什么？

<details>
<summary>查看答案</summary>

R（Research）负责提出假设和规划实验，D（Development）负责把假设实现成代码并执行。执行结果作为反馈回写知识库，驱动下一轮更好的假设。

</details>

### 问题 2：o3(R)+GPT-4.1(D) 这个组合的设计目标是什么？

<details>
<summary>查看答案</summary>

缩短每轮循环的平均耗时，并用更经济的模型组合降低总成本——研究端用 o3，开发端用 GPT-4.1，按能力需求分别选型，而不是单模型打天下。

</details>

### 问题 3：RD-Agent(Q) 的"交替因子-模型优化"是什么意思？

<details>
<summary>查看答案</summary>

因子优化发现更有预测价值的新因子，模型优化基于新因子集合改进预测模型，两者交替进行、相互成就，最终在预测精度和策略鲁棒性之间取得更好的权衡，同时把因子数量压缩了 70% 以上。

</details>

### 问题 4：部署前需要确认哪三件事？

<details>
<summary>查看答案</summary>

Linux 操作系统、免 sudo 的 Docker（`docker run hello-world` 验证）、未占用的 19899 端口。前两件用 `rdagent health_check --no-check-env` 覆盖检查。

</details>

### 问题 5：Web UI 绑定到 0.0.0.0 前必须做什么？

<details>
<summary>查看答案</summary>

设置 `UI_SERVER_AUTH_TOKEN` 环境变量。服务器会拒绝在未设 token 的情况下绑定非本地地址；远程访问时通过 `?token=` 建立会话或用 Bearer 头认证，并建议置于 HTTPS 反向代理之后。

</details>

---

## 练习

### 练习 1：完成一次健康检查

**任务**：在 Linux 机器上装好 RD-Agent，让 `rdagent health_check` 全部通过。

**提示**：先确认 Docker 免 sudo 可用（`docker run hello-world`），再用 conda 建 Python 3.10 环境装包，`health_check --no-check-env` 通过后配置 `.env`，最后不带参数跑 `health_check` 验证模型配置。三项分别对应环境变量、Docker、端口。

### 练习 2：跑通一轮因子进化并回放

**任务**：配置好模型后运行 `rdagent fin_factor`，观察至少两轮假设-实现-反馈循环，再用 `rdagent ui` 回放日志。

**提示**：重点观察两件事——R 侧第二轮的假设有没有引用第一轮的回测反馈；D 侧实现失败时代码是如何被修正的。这两处是 RD 循环区别于"单次代码生成"的关键。

### 练习 3：为 DeepSeek 配置可运行的 `.env`

**任务**：只用 DeepSeek 官方 API 和 SiliconFlow，写出能通过 `health_check` 的完整配置。

**提示**：两个易错点——`CHAT_MODEL` 需要 `deepseek/` 前缀；DeepSeek 没有嵌入模型，embedding 必须走 `litellm_proxy` 前缀的第三方服务。完整模板见本文 5.4 节。

---

## 进阶路径

1. **读总技术报告**：[arXiv:2505.14738](https://arxiv.org/abs/2505.14738) 覆盖整体框架设计与 MLE-Bench 实验细节
2. **深入量化场景**：[R&D-Agent-Quant 论文](https://arxiv.org/abs/2505.15155) + [复现文档](https://rdagent.readthedocs.io/en/latest/scens/quant_agent_fin.html)
3. **尝试 FT-Agent**：按仓库 `rdagent/app/finetune/llm/README.md` 做基准驱动的 LLM 微调实验
4. **跟进 Kaggle 场景**：官方 Roadmap 显示这是当前重点开发方向
5. **扩展新场景**：参照 `rdagent/scenarios/` 现有实现，配合[开发文档](https://rdagent.readthedocs.io/en/latest/development.html)接入新的数据驱动场景
6. **参与贡献**：从 [CONTRIBUTING.md](https://github.com/microsoft/RD-Agent/blob/main/CONTRIBUTING.md) 入手，或在代码库里 `grep -r "TODO:"` 找切入点；提交前确认通过 CI 检查

---

## 资料口径说明

1. **信息来源**：本文基于 [microsoft/RD-Agent](https://github.com/microsoft/RD-Agent) 仓库 README、`docs/` 文档、`rdagent/app/cli.py` 源码与官方论文
2. **数据口径**：Stars、Forks、提交数、语言占比为 2026-09-23 通过 GitHub API 核对的读数，会随时间变化；最新发布版本以 [Releases 页](https://github.com/microsoft/RD-Agent/releases)为准
3. **性能数据**：MLE-Bench 成绩与 RD-Agent(Q) 实验结果均转述自官方 README 与论文，为研究环境下的测量值，不构成对实际效果的承诺
4. **投资边界**：按官方 Legal Disclaimer，RD-Agent 面向金融研发流程，不构成投资建议，未达到可直接用于金融投资的就绪度
5. **更新记录**：本文初稿写于 2026-04-01，2026-09-23 对照 main 分支（v0.8.0 之后）全面核对更新，覆盖 Web UI 安全机制、FT-Agent、Agent² RL-Bench 等新增内容

---
