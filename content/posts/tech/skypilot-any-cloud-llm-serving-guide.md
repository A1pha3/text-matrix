---
title: "SkyPilot：10.5K Stars·任意云 LLM 服务框架·自动故障转移"
date: "2026-04-12T02:31:39+08:00"
slug: skypilot-any-cloud-llm-serving-guide
github_repo: "skypilot-org/skypilot"
description: "SkyPilot 是伯克利 Sky Computing Lab 开源的 AI 编排框架，统一管理 25+ 云、Kubernetes 与 Slurm，支持 Spot 实例自动恢复与 SkyServe 模型服务，可节省约 70% 的 GPU 成本。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "GPU", "成本优化", "Kubernetes"]
---

# SkyPilot：任意云 LLM 服务框架·自动故障转移·Spot 实例节省约 70%

SkyPilot 把分散在多朵云、多个集群里的 GPU 抽象成一台统一的机器：你写一份任务描述，它负责挑选最便宜的可用资源、开机、跑任务、故障后自动恢复，跑完再关机。这篇笔记基于 2026 年 8 月的官方文档与仓库状态，讲清楚它解决的问题、真实用法和坑。

读完你会掌握：SkyPilot 的三种核心抽象怎么选；用 YAML 定义一个任务并在云上跑起来；用 SkyServe 把一个开源 LLM 服务上线并自动扩缩容；用托管任务在 Spot 实例上安全地跑长任务。

## 一，项目概述

### 1.1 SkyPilot 是什么

SkyPilot 是一个面向 AI 负载的编排控制面。它由加州大学伯克利分校的 Sky Computing Lab 开发，2021 年 8 月建立仓库，2022 年开源，论文发表在 USENIX NSDI 2023。2026 年 7 月项目成立公司（SkyPilot 公司），完成 2000 万美元种子轮，由 Lux Capital 领投。

它的定位是把你已经拥有、但分散在各处的算力统一起来：AWS、GCP、Azure，以及 Lambda、CoreWeave、Nebius、RunPod 等 GPU 云，还有你自己的 Kubernetes 集群和 Slurm 集群。官方目前的口径是支持 25+ 朵云加 Kubernetes、Slurm。

它解决的核心问题有三个：

- **算力分散**：单个云或区域经常买不到卡，但换一朵云可能马上就有货。SkyPilot 自动在不同云之间切换。
- **成本差异大**：同一块 GPU 在不同云、不同区域的定价可以相差数倍。SkyPilot 在启动时查询各云报价，选最便宜且有货的。
- **运维负担重**：开机、装环境、跑任务、处理预占、关机，这些本应由框架接管，而不是让工程师盯着控制台。

### 1.2 核心数据

以下数据截至 2026 年 8 月：

| 指标 | 数值 |
|------|------|
| Stars | 约 10.5k |
| Forks | 约 1.2k |
| 贡献者 | 265 |
| 提交数 | 5,689（master） |
| 最新版本 | v0.13.1rc1（2026-07） |
| 许可证 | Apache-2.0 |
| 语言 | Python |

### 1.3 关键指标

```
支持基础设施: 25+ 云 + Kubernetes + Slurm
Spot 实例: 自动恢复，可节省约 70% GPU 成本
SkyServe: 多区域/多云副本，成本降低约 50%
下载量: 1400 万+（第三方统计）
生产用户: Meta FAIR、Shopify、Nubank、H Company
SkyServe 生产案例: LMSys ChatBot Arena
```

需要说明的是，网络上流传的"1000+ 任务/天""$10M+ 成本节省"等说法我无法在官方来源里核实，本文不采用。

## 二，核心原理

### 2.1 架构概览

SkyPilot 的架构可以简化为三层：用户入口、控制面、后端基础设施。

```
┌─────────────────────────────────────────────────────────────┐
│                        用户入口                                │
│            sky CLI / Python SDK / Dashboard                   │
└────────────────────────────┬────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                      SkyPilot 控制面                          │
│   成本优化器：对比各云/区域报价，选最便宜且有货的资源             │
│   控制器：管理任务与服务的生命周期、故障恢复、扩缩容              │
└───────┬──────────────┬──────────────┬───────────────────────┘
        ↓              ↓              ↓
   ┌─────────┐   ┌───────────┐   ┌────────────┐
   │ AWS/GCP │   │  GPU 云    │   │ Kubernetes │
   │ /Azure  │   │ Lambda 等  │   │  /Slurm    │
   └─────────┘   └───────────┘   └────────────┘
```

用户不直接和云 API 打交道。你提交一份任务描述（YAML 或 Python），SkyPilot 的成本优化器查询各云报价和容量，决定把任务放到哪里；控制器负责后续的开机、执行、监控和清理。

### 2.2 三种核心抽象

SkyPilot 只提供三种抽象，理解它们的适用场景就掌握了这个工具：

| 抽象 | 命令 | 适用场景 |
|------|------|----------|
| 集群 | `sky launch` / `sky exec` | 交互式开发、调试、跑短任务，集群长期保留 |
| 托管任务 | `sky jobs launch` | 长时间训练、批量推理，无人值守，自动恢复 |
| SkyServe | `sky serve up` | 模型服务，自动负载均衡、扩缩容、多区域副本 |

- **集群**适合开发和实验：开一个带 GPU 的机器，SSH 进去或连 VSCode 改代码，跑完 `sky stop` 停掉保留状态。
- **托管任务**适合要跑很久、不想盯着的活：它管理任务全生命周期，节点崩溃、Spot 预占、GPU 报错都能自动恢复。
- **SkyServe**适合对外提供推理服务：它把一个已有的推理框架（vLLM、SGLang、TGI 等）部署到多个副本后面，给你一个统一入口。

### 2.3 成本优化与故障转移原理

成本优化发生在提交任务的那一刻。SkyPilot 会拿到各云实时的实例报价与可用容量，在满足你资源要求的前提下，按成本从低到高排序选择。你不指定云时，它只按"最便宜且有货"这个原则选。

故障转移分两个层次：

- **启动阶段**：首选云或区域没货时，自动按优先级列表向后尝试，无需你干预。
- **运行阶段**：通过托管任务或 SkyServe 的控制器监控运行状态，节点故障或 Spot 被预占时，自动在别的云/区域重新拉起，并从检查点继续。

这也是"Spot 实例 + 自动恢复"能省钱的原因：Spot 便宜，但会被云厂商随时回收；SkyPilot 把回收后的恢复动作自动化，可靠性交给框架，省钱收益留给你。

## 三，安装与配置

### 3.1 安装

要求 Python 3.9 以上。推荐用带 `[all]` 或按需选择云平台的安装方式：

```bash
# 支持所有云（含 Kubernetes、Slurm）
pip install "skypilot[all]"

# 或只装你实际用到的云
pip install "skypilot[aws,gcp]"
```

### 3.2 云凭证配置

在云厂商侧准备好凭证，SkyPilot 只是复用你已有的认证：

```bash
# AWS
aws configure

# GCP
gcloud auth application-default login

# Azure
az login

# 私有 Kubernetes 集群
# 配置好 ~/.kube/config 即可
```

新式 GPU 云（Lambda、Nebius、CoreWeave 等）通常复用 AWS 凭证，或按其文档设置 API Key。

### 3.3 验证配置

```bash
# 检查哪些云已启用
sky check

# 查看当前可用的 GPU 型号（跨所有已启用基础设施）
sky gpus list
```

`sky check` 会列出每朵云的 enabled/disabled 状态，任何云不可用都会有提示，按提示补齐凭证即可。

## 四，快速开始

### 4.1 第一个任务

写一个 YAML 描述任务：要什么资源、做什么事。

```yaml
# hello_sky.yaml
resources:
  accelerators: T4:1

run: |
  nvidia-smi
  echo "Hello, SkyPilot!"
```

提交：

```bash
sky launch -c hello hello_sky.yaml
```

`-c` 给集群起名。SkyPilot 会先估算成本并让你确认，然后自动开机、执行任务。任务结束后集群仍在，方便你继续用。

### 4.2 交互式开发

需要一块 GPU 做实验时，直接开一个开发节点：

```bash
# 开一个带 8 卡 A100-80GB 的开发节点
sky launch -c dev --gpus A100-80GB:8

# 等待开机完成后 SSH 进去
ssh dev
```

已有集群想跑新任务而不重新配置，用 `sky exec`：

```bash
sky exec dev task2.yaml
```

### 4.3 托管任务

长时间任务用 `sky jobs launch`，它会自动管理生命周期并在失败时恢复：

```bash
sky jobs launch -n myjob hello_sky.yaml

# 查看所有托管任务
sky jobs queue

# 查看某个任务的日志
sky jobs logs 1

# 取消任务
sky jobs cancel 1
```

托管任务跑在一个临时集群上，结束后自动清理，不占用你的常驻资源。

## 五，LLM 服务

模型服务是 SkyPilot 最常用的场景，下面用一个开源模型（Llama 3.1 8B + vLLM）走完整流程。

### 5.1 单副本试运行

先写一份服务 YAML。这里 GPU 用一组候选列表，`use_spot: true` 表示可以选 Spot 实例，SkyPilot 会在满足条件且最便宜的那款上跑：

```yaml
# serve.yaml
resources:
  accelerators: {L4, A10g, A10, L40, A40, A100, A100-80GB}
  ports: 8000
  use_spot: true

envs:
  MODEL_NAME: meta-llama/Llama-3.1-8B-Instruct

setup: |
  pip install vllm

run: |
  python -m vllm.entrypoints.openai.api_server \
    --model $MODEL_NAME --port 8000
```

启动单副本，先验证服务本身没问题：

```bash
# --env 把 HuggingFace Token 传进去，下载模型权重用
sky launch -c vllm-demo serve.yaml --env HF_TOKEN=hf_xxx

# 拿到节点 IP
IP=$(sky status --ip vllm-demo)

# 验证 OpenAI 兼容接口
curl http://$IP:8000/v1/models
curl http://$IP:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "meta-llama/Llama-3.1-8B-Instruct",
       "messages": [{"role": "user", "content": "Hello!"}]}'
```

### 5.2 用 SkyServe 上线

验证通过后，在 YAML 里加一个 `service` 段，就变成 SkyServe 服务定义：多个副本、探活路径、扩缩容策略都写在这里。

```yaml
# service.yaml
service:
  replicas: 2
  readiness_probe: /v1/models
  replica_policy:
    min_replicas: 1
    max_replicas: 4
    target_qps_per_replica: 2

resources:
  accelerators: {L4, A10g, A10, L40, A40, A100, A100-80GB}
  ports: 8000
  use_spot: true

envs:
  MODEL_NAME: meta-llama/Llama-3.1-8B-Instruct

setup: |
  pip install vllm

run: |
  python -m vllm.entrypoints.openai.api_server \
    --model $MODEL_NAME --port 8000
```

上线与使用：

```bash
# 部署服务，-n 指定服务名
sky serve up -n llama-svc service.yaml --env HF_TOKEN=hf_xxx

# 查看副本状态，直到 READY
sky serve status llama-svc

# 拿到统一入口地址
ENDPOINT=$(sky serve status --endpoint llama-svc)

# 通过入口访问，SkyServe 自动把请求分发到各副本
curl $ENDPOINT/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "meta-llama/Llama-3.1-8B-Instruct",
       "messages": [{"role": "user", "content": "Hello!"}]}'

# 不再需要时下线
sky serve down llama-svc
```

### 5.3 自动扩缩容

`replica_policy` 是 SkyServe 的扩缩容核心：`min_replicas` 和 `max_replicas` 限定副本数量范围，`target_qps_per_replica` 是每个副本的目标 QPS。当请求量上升、单副本实际 QPS 超过目标时，SkyServe 自动加副本；空闲时缩回 `min_replicas`。副本会尽量铺到不同区域/云上，既提高可用性，也避免单一区域容量不足。

要注意 SkyServe 目前仍是 beta 状态。官方明确说它适合内部服务和 R&D、批量推理，暂不建议直接对外承担生产流量。下一代 SkyServe 正在做生产化改造，方向包括 prefill/decode 分离、缓存感知路由、TP/DP/PP/Wide-EP 支持、自定义指标扩缩容、scale-to-zero、TLS 与 API Key 鉴权等。

## 六，托管任务与 Spot 实例

### 6.1 Managed Jobs 的作用

托管任务（`sky jobs`）管理一个任务的完整生命周期：资源配置、自动故障恢复、跑完清理。它适合单任务长时间运行，也适合一次性提交成百上千个并行任务。

它具备四个关键能力：

- **自动恢复**：节点崩溃、Spot 预占、GPU 故障、NCCL 超时都能自动恢复；应用本身的错误也可以按配置重试。
- **跨基础设施扩展**：任务可以分散在你所有可用的云、区域、集群上。
- **托管流水线**：一个 YAML 里定义多个相互依赖的任务（数据处理 → 训练 → 推理），顺序执行。
- **Spot 支持**：可选跑在自动恢复的 Spot 实例上。

### 6.2 在 Spot 实例上跑长任务

Spot 实例便宜（官方口径可节省约 70% 的 GPU 成本），但会被云厂商随时回收。托管任务 + Spot 的组合让"便宜"和"可靠"同时成立：

```yaml
# spot-train.yaml
name: spot-train
resources:
  accelerators: A100:8
  use_spot: true
  job_recovery:
    strategy: EAGER_NEXT_REGION

run: |
  torchrun --nproc_per_node=8 train.py
```

```bash
sky jobs launch -n spot-train spot-train.yaml
```

`use_spot: true` 让优化器优先考虑 Spot 实例；`job_recovery.strategy: EAGER_NEXT_REGION` 表示节点故障或预占后直接跳到下一个区域重试，因为一个区域出现预占通常意味着该区域资源正紧张。

### 6.3 检查点与恢复

Spot 被回收时任务进程会中断，所以训练代码要把进度写到持久化存储。SkyPilot 支持两种方式：

- **云存储桶**：用 `file_mounts` 把 S3/GCS/Azure Blob 桶挂载进任务。

```yaml
file_mounts:
  /checkpoints:
    source: s3://my-bucket/checkpoints
    mode: MOUNT
```

- **Kubernetes 卷**：在 K8s 后端上使用 PVC，适合 K8s 用户。

配合恢复策略，任务重新拉起后从 `/checkpoints` 里的最新检查点继续训练，而不是从头再来。应用错误的重试次数可以在 `job_recovery` 里配置（例如 `max_restarts_on_errors`）。

## 七，Python SDK

除 YAML 外，SkyPilot 也提供 Python SDK。注意 SDK 调用是异步的：大多数调用返回一个 request ID，用 `sky.get(request_id)` 等待结果。

```python
import sky

# 定义任务，指定资源（infra 指基础设施/云）
task = sky.Task(run='python train.py')
task.set_resources(sky.Resources(infra='aws', accelerators='A100:1'))

# 提交并等待结果
request_id = sky.launch(task, cluster_name='my-cluster')
sky.get(request_id)

# 查询集群状态
sky.status()
```

常用的 SDK 函数和 CLI 是一一对应的：`sky.launch`、`sky.exec`、`sky.status`、`sky.stop`、`sky.down`、`sky.autostop`。对多数场景，CLI + YAML 已经足够，SDK 主要用在需要把 SkyPilot 嵌进自己的脚本或平台里的时候。

## 八，YAML 配置参考

### 8.1 基础字段

```yaml
name: my-task          # 任务名（可选）
workdir: .             # 本地目录，会同步到远端 ~/sky_workdir
num_nodes: 1           # 分布式训练的节点数

resources:
  accelerators: H100:8 # GPU 型号与数量
  cpus: 32+            # 最小 CPU 核数
  memory: 128+         # 最小内存（GB）
  disk_size: 512       # 磁盘大小（GB）
  use_spot: false      # 是否使用 Spot 实例
  ports: 8000          # 需要对外开放的端口

envs:                  # 环境变量
  MODEL_NAME: meta-llama/Llama-3.1-8B-Instruct

setup: |               # 只执行一次的准备命令
  pip install -r requirements.txt

run: |                 # 主命令
  python train.py
```

### 8.2 多基础设施与容灾

不写 `infra` 时 SkyPilot 自动选最便宜的可用资源。想控制候选范围，用 `any_of`（无序候选）或 `ordered`（按顺序候选）：

```yaml
resources:
  accelerators: H100:8
  any_of:
    - infra: aws/us-east-1
    - infra: gcp/us-central1
    - infra: kubernetes
```

### 8.3 服务配置

```yaml
service:
  replicas: 2                     # 初始副本数
  readiness_probe: /v1/models     # 就绪探活路径
  replica_policy:                 # 扩缩容策略
    min_replicas: 1
    max_replicas: 4
    target_qps_per_replica: 2
```

`service` 段可以加在任意任务 YAML 末尾，把普通任务变成 SkyServe 服务。需要鉴权时，vLLM 这类引擎自带 `--api-key`，配合 `secrets` 字段传入。

## 九，与其他框架对比

先明确一点：SkyPilot 和下面这些工具大多不是竞品，而是不同层。

| 工具 | 定位 | 与 SkyPilot 的关系 |
|------|------|--------------------|
| SkyPilot | 多云/多集群 AI 编排控制面 | 本文主角 |
| Kubernetes | 单集群内的容器编排 | SkyPilot 可以把 K8s 作为后端之一 |
| Ray Serve | 在已有集群内做分布式推理服务 | 可被 SkyServe 作为副本内的推理框架使用 |
| vLLM / SGLang / TGI | 推理引擎（单机内加速推理） | 通常作为 SkyServe 的引擎，配合使用 |
| Modal / RunPod | 无服务器 GPU 平台 | 更封闭的托管方案，SkyPilot 是 BYOC（自带算力） |

最常用的组合是 **SkyServe + vLLM**：vLLM 负责把模型跑快，SkyServe 负责把 vLLM 铺到多个云/区域并做好负载均衡和扩缩容。

## 十，常见问题

### 10.1 集群相关

```bash
# 查看所有集群及状态
sky status

# 流式查看集群当前任务的日志
sky logs my-cluster

# 查看托管任务日志（用任务 ID）
sky jobs logs JOB_ID

# 停掉集群（保留磁盘状态，省钱）
sky stop my-cluster

# 彻底删除集群
sky down my-cluster

# 设置空闲自动停机：30 分钟无任务就停机，-d 表示直接删除
sky autostop my-cluster -i 30 --down
```

### 10.2 配额不足

配额是云厂商的硬限制，SkyPilot 只是提示。处理方法：

- 用 `sky gpus list` 看哪些区域、云有货，换一个配额充足的区域。
- 提交时加 `--retry-until-up`，让 SkyPilot 在容量不足时自动重试或切换。
- 到云厂商控制台申请提高配额（AWS 的 EC2 配额、GCP 的 GPU 配额）。

### 10.3 模型权重下载失败

开源模型权重在 HuggingFace，需要：

```bash
# 用 --env 传 HF Token，或者写进 YAML 的 secrets 字段
sky launch -c demo serve.yaml --env HF_TOKEN=hf_xxx
```

Gated 模型（如 Llama 3.1）需要先在 HuggingFace 页面申请访问权，再在命令行传入对应账号的 Token。

## 十一，总结

SkyPilot 解决的是 AI 算力的"碎片化"问题：把多朵云、Kubernetes、Slurm 上的 GPU 统一成一个可编程的资源池，自动完成选型、开机、容灾和清理。三种核心抽象各有定位——集群做开发，托管任务跑长活，SkyServe 对外服务。

实际使用时记住三条原则：第一，能用托管任务就用托管任务，把容灾交给框架；第二，长任务配合 Spot 实例和检查点，成本与可靠兼得；第三，服务上线前先在单副本上验证，再交给 SkyServe 扩副本。

---

**相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/skypilot-org/skypilot |
| 文档 | https://skypilot.readthedocs.io |
| 官网 | https://skypilot.ai |
| 论文（NSDI 2023） | https://www.usenix.org/system/files/nsdi23-yang-zongheng.pdf |
| vLLM 服务示例 | https://github.com/skypilot-org/skypilot/tree/master/llm/vllm |

---

*本文由钳岳星君撰写，基于 SkyPilot（约 10.5k Stars，数据截至 2026-08）*
