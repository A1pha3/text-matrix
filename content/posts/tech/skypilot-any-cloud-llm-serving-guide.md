---
title: "SkyPilot：9.8K Stars·任意云LLM服务框架·自动故障转移"
date: 2026-04-12T02:31:39+08:00
slug: skypilot-any-cloud-llm-serving-guide
description: "SkyPilot 是一个任意云 LLM 服务框架，支持自动故障转移和 Spot 实例，可节省高达 70% 的成本，每天处理 1000+ 任务。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "云服务", "GPU", "成本优化", "Kubernetes"]
---

# SkyPilot：9.8K Stars·任意云LLM服务框架·自动故障转移·Spot实例节省70%·1000+任务/天·$10M+成本节省

## 一，项目概述

### 1.1 SkyPilot 是什么

**SkyPilot** 是一个**任意云LLM和AI服务框架**，可以在任何云（AWS、GCP、Azure、Lambda、Cloudflare等）上运行LLM、AI模型和批处理任务。

> "SkyPilot: Unified AI & LLM Serving on Any Cloud"

**核心价值**：
- ☁️ **任意云**：AWS、GCP、Azure、Lambda、Cloudflare 等统一接口
- 💰 **成本节省**：托管 Spot 实例，节省 70%+ 成本
- 🔄 **自动故障转移**：某云无可用GPU时自动切换到其他云
- 🚀 **快速部署**：一行代码启动 LLM 服务

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | **59.7k** ⭐ |
| Forks | 3.6k |
| 贡献者 | **162** |
| 提交数 | **1,100+** |
| 最新版本 | **0.6.0** (2026-04-11) |
| 许可证 | **Apache-2.0** |
| 语言 | **Python 98.2%** |

### 1.3 成绩单

```
┌─────────────────────────────────────────────────────────────┐
│                    SkyPilot 成绩单                                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   📊 每日任务: 1000+ 任务/天                                     │
│   💰 成本节省: $10M+ (已为用户节省)                              │
│   ☁️ 支持云: AWS / GCP / Azure / Lambda / Cloudflare / ...     │
│   🎯 GPU 类型: A100 / H100 / H200 / T4 / L4 / ...            │
│   ⏱️ 最新版本: v0.6.0 (2026-04-11)                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 二，核心原理

### 2.1 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    SkyPilot 架构                                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│                         用户代码                                     │
│                            ↓                                       │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              SkyPilot Core                               │   │
│   │   ┌──────────────┐  ┌──────────────┐               │   │
│   │   │   Orchestrator │  │   Optimizer  │               │   │
│   │   │  (任务编排)    │  │  (成本优化)   │               │   │
│   │   └──────────────┘  └──────────────┘               │   │
│   │   ┌──────────────┐  ┌──────────────┐               │   │
│   │   │   Scheduler  │  │   Failover   │               │   │
│   │   │   (调度器)    │  │  (故障转移)   │               │   │
│   │   └──────────────┘  └──────────────┘               │   │
│   └─────────────────────────────────────────────────────┘   │
│                            ↓                                       │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│   │   AWS    │ │   GCP   │ │  Azure  │ │ Lambda   │  ...   │
│   └─────────┘ └─────────┘ └─────────┘ └─────────┘        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 多云统一接口

```python
import sky

# 定义任务（与云无关）
task = sky.Task(run='python train.py')
task.set_resources(sky.Resources(accelerators='A100:1'))

# SkyPilot 自动选择最佳云
# 优先级: Lambda > AWS > GCP > Azure > ...
sky.launch(task, cluster_name='my-cluster')

# 切换云只需改配置
sky.config.set_default_region('us-west-2')  # GCP
sky.config.set_default_region('us-east-1')  # AWS
```

### 2.3 自动故障转移

```python
import sky

# 当 AWS 不可用时，自动切换到 GCP
@sky.autostop(downtime=30)  # 30分钟无活动自动停机
def my_task():
    # 这个任务会在最便宜的可用云上运行
    return sky.Task(run='python train.py')

# 启动托管 Spot 实例（自动恢复）
sky.spot.launch(
    my_task,
    cluster_name='spot-cluster',
    checkpoint=True,  # 故障后自动恢复
)
```

## 三，安装与配置

### 3.1 安装

```bash
# 方式一：pip 安装（推荐）
pip install skypilot

# 方式二：从源码安装
git clone https://github.com/skypilot-org/skypilot.git
cd skypilot
pip install -e .

# 验证安装
sky check  # 检查云凭证
```

### 3.2 云凭证配置

```bash
# AWS 凭证
aws configure

# GCP 凭证
gcloud auth application-default login

# Azure 凭证
az login

# Lambda 凭证 (从 AWS 配置)
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...

# 检查配置
sky check
```

### 3.3 快速配置

```python
import sky

# 设置默认区域
sky.config.set_default_region('us-west-2')  # GCP Oregon
sky.config.set_default_region('us-east-1')  # AWS Virginia

# 设置默认云
sky.config.set_default_cloud('AWS')  # 优先使用 AWS

# 查看所有云状态
sky status --all
```

## 四，快速开始

### 4.1 基础任务

```python
import sky

# 方式一：YAML 配置
# task.yaml
# name: my-task
# resources:
#   accelerators: A100:1
# command: python train.py

task = sky.Task.from_yaml('task.yaml')
sky.launch(task, cluster_name='my-cluster')

# 方式二：Python API
task = sky.Task(run='python train.py')
task.set_resources(sky.Resources(accelerators='A100:1'))
sky.launch(task, cluster_name='my-cluster')
```

### 4.2 LLM 服务

```python
import sky
from sky import Serve

# 定义 LLM 服务
@sky.serve
def vllm_service():
    return sky.Task(
        setup='pip install vllm',
        run='python -m vllm.entrypoints.openai.api_server \
            --model meta-llama/Llama-2-7b-hf \
            --port 8000',
        ports=8000,
        resources=sky.Resources(accelerators='A100:1')
    )

# 启动服务
Serve.start(vllm_service, name='llama-service')

# 获取服务端点
endpoint = Serve.get_endpoint('llama-service')
print(f"LLM 服务地址: {endpoint}")

# 查询
import requests
response = requests.post(
    endpoint + '/v1/chat/completions',
    json={'messages': [{'role': 'user', 'content': 'Hello!'}]}
)
```

### 4.3 托管 Spot 实例

```python
import sky

# 定义 Spot 任务
@sky.autostop(idle=5, down=True)  # 5分钟空闲后停机
def spot_train():
    return sky.Task(
        run='python train.py',
        # Spot 实例便宜 70%+
        resources=sky.Resources(
            accelerators='A100:1',
            spot=True,  # 使用 Spot 实例
            spot_policy='spot',  # 故障后自动恢复
        )
    )

# 启动 Spot 任务
task = spot_train()
sky.spot.launch(task, cluster_name='spot-train')
```

## 五，核心 API

### 5.1 Task API

```python
import sky

# 创建任务
task = sky.Task(run='python train.py')

# 设置资源
task.set_resources(sky.Resources(
    accelerators='A100:1',  # GPU 类型
    cpu=8,                  # CPU 核数
    memory=32,               # 内存 GB
    disk_size=100,           # 磁盘 GB
))

# 设置环境
task.set_env({'DATA_PATH': '/data'})

# 设置入口点
task.setup = 'pip install -r requirements.txt'

# 多个命令
task.run = '''
cd ~/train
python train.py --epochs 100
python evaluate.py
'''
```

### 5.2 Resources API

```python
import sky

# GPU 资源配置
resources = sky.Resources(
    accelerators='A100:1',     # 单卡 A100
    accelerators='A100:8',    # 8 卡 A100
    accelerators='H100:8',     # 8 卡 H100
    accelerators='T4:4',       # 4 卡 T4
)

# Spot 实例
resources = sky.Resources(
    accelerators='A100:1',
    spot=True,
    spot_policy='spot',         # 故障后恢复
    spot_policy='float',       # 故障后切换到按需
)

# 多云配置
resources = sky.Resources(
    cloud='AWS',               # 强制使用 AWS
    region='us-east-1',        # AWS 区域
    zone='us-east-1a',         # 可用区
)

# 任何云（自动选择）
resources = sky.Resources(accelerators='A100:1')  # 自动选择最便宜的
```

### 5.3 Cluster API

```python
import sky

# 创建集群
cluster = sky.Cluster(
    name='my-cluster',
    resources=sky.Resources(accelerators='A100:1')
)
cluster.up()

# 在集群上运行任务
cluster.run('python train.py')

# 查看状态
print(cluster.status)  # INIT / UP / STOPPED / DOWN

# 停止集群
cluster.stop()

# 启动集群
cluster.up()

# 删除集群
cluster.delete()
```

### 5.4 Serve API

```python
import sky
from sky import Serve

# 注册服务
@sky.serve
class LLMService:
    def __init__(self):
        self.model = None
    
    def setup(self):
        from vllm import LLM
        self.model = LLM(model='meta-llama/Llama-2-7b-hf')
    
    def infer(self, prompt: str) -> str:
        outputs = self.model.generate([prompt])
        return outputs[0]

# 启动服务（自动扩缩容）
Serve.start(
    LLMService,
    name='llm-service',
    replicas=2,                    # 2 个副本
    min_replicas=1,              # 最小 1 副本
    max_replicas=10,              # 最大 10 副本
    target_qps=10,                # 每秒查询数
)

# 获取服务
service = Serve.get('llm-service')
print(service.endpoint)

# 扩缩容
Serve.scale('llm-service', replicas=5)  # 扩到 5 副本

# 停止服务
Serve.stop('llm-service')
```

## 六，高级特性

### 6.1 自动扩缩容

```python
import sky
from sky import Serve

@sky.serve
def llm_service():
    return sky.Task(
        setup='pip install vllm',
        run='python -m vllm.entrypoints.openai.api_server --model llama-2',
        ports=8000,
        resources=sky.Resources(accelerators='A100:1')
    )

# 启动服务（自动扩缩容）
Serve.start(
    llm_service,
    name='autoscale-llm',
    min_replicas=1,
    max_replicas=10,
    # 基于 QPS 扩缩容
    target_qps=10,
    # 基于 GPU 利用率扩缩容
    target_gpu_util=70,
)
```

### 6.2 多区域容灾

```python
import sky

# 定义多区域任务
task = sky.Task(run='python train.py')
task.set_resources(
    sky.Resources(
        accelerators='A100:1',
        # 允许的区域
        allowed_regions=['us-west-2', 'us-east-1', 'europe-west4'],
    )
)

# SkyPilot 自动选择可用区域
# 如果 us-west-2 满了，自动尝试 us-east-1
sky.launch(task)
```

### 6.3 检查点与恢复

```python
import sky

# 启用检查点（故障自动恢复）
task = sky.Task(run='python train.py')
task.set_resources(sky.Resources(accelerators='A100:1', spot=True))
task.enable_checkpoint()  # 启用检查点

# Spot 任务会自动保存检查点
sky.spot.launch(
    task,
    cluster_name='checkpointed-train',
    checkpoint=True,  # 故障后自动恢复
)
```

### 6.4 日志与监控

```bash
# 查看集群上的任务日志
sky logs my-cluster

# 查看实时日志
sky logs my-cluster --follow

# 查看特定任务的日志
sky logs my-cluster --job 1

# 启动 TensorBoard
sky.start.tensorboard(my-cluster, log_dir='~/logs')
```

## 七，最佳实践

### 7.1 成本优化

```python
import sky

# ✅ 推荐：使用 Spot 实例
task = sky.Task(run='python train.py')
task.set_resources(sky.Resources(
    accelerators='A100:1',
    spot=True,              # 便宜 70%+
    spot_policy='spot',    # 故障自动恢复
))

# ❌ 不推荐：使用按需实例
task = sky.Task(run='python train.py')
task.set_resources(sky.Resources(accelerators='A100:1'))  # 贵

# ✅ 推荐：使用较小的 GPU
task.set_resources(sky.Resources(accelerators='T4:1'))  # 便宜

# ✅ 推荐：设置合理的超时
sky.launch(task, timeout=3600)  # 1小时超时
```

### 7.2 性能优化

```python
import sky

# ✅ 推荐：使用高速 GPU 互联
task.set_resources(sky.Resources(
    accelerators='A100:8',    # 8 卡 NVLink 互联
    # vs
    accelerators='T4:8',    # PCIe 互联，较慢
))

# ✅ 推荐：使用持久化磁盘
task.set_resources(sky.Resources(
    accelerators='A100:1',
    disk_size=1000,         # 大磁盘
    disk_tier='high',       # 高速磁盘
))

# ✅ 推荐：预热模型
task.setup = '''
pip install transformers
python -c "from transformers import AutoModel; AutoModel.from_pretrained('bert-base')"
'''
```

### 7.3 安全最佳实践

```python
import sky

# ✅ 推荐：使用 IAM 角色
task = sky.Task(run='python train.py')
task.add_env({
    'AWS_ROLE_ARN': 'arn:aws:iam::123456789:role/my-role',
})

# ✅ 推荐：使用私有 VPC
task.set_resources(sky.Resources(
    cloud='AWS',
    region='us-west-2',
    vpc_name='my-private-vpc',  # 私有 VPC
))

# ✅ 推荐：加密存储
task.set_storage([
    sky.Storage(name='my-data', mode=sky.StorageMode.READ_ONLY),
])
```

## 八，YAML 配置

### 8.1 基础 YAML

```yaml
# task.yaml
name: my-task

# 资源配置
resources:
  accelerators: A100:1
  cloud: aws
  region: us-west-2

# 环境变量
envs:
  DATA_PATH: /data
  MODEL_PATH: /model

# 入口命令
setup: |
  pip install -r requirements.txt
  
run: |
  cd ~/train
  python train.py --epochs 100
```

### 8.2 Spot 实例 YAML

```yaml
# spot_task.yaml
name: spot-train

resources:
  accelerators: A100:1
  spot: true
  spot_policy: spot  # 故障自动恢复

# 自动停机
autostop: 30  # 30分钟空闲后停机

run: |
  python train.py --checkpoint ./checkpoints
```

### 8.3 服务 YAML

```yaml
# serve.yaml
name: llm-service

service:
  replicas: 2
  # 扩缩容配置
  autoscaling:
    min_replicas: 1
    max_replicas: 10
    target_qps: 10

resources:
  accelerators: A100:1

setup: |
  pip install vllm

run: |
  python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-7b-hf \
    --port 8000

port: 8000
```

## 九，与其他框架对比

| 框架 | 特点 | 优势 |
|------|------|------|
| **SkyPilot** | 任意云 | 多云统一、成本最优 |
| **Ray Serve** | Ray 生态 | 分布式训练强 |
| **vLLM** | PagedAttention | 单卡推理快 |
| **Text-Generation-Inference** | HuggingFace 官方 | 集成好 |
| **TGI** | 量化优化 | 推理优化 |

```python
# SkyPilot + vLLM 组合（最佳实践）
@sky.serve
def vllm_service():
    return sky.Task(
        setup='pip install vllm',
        run='''
        python -m vllm.entrypoints.openai.api_server \
            --model meta-llama/Llama-2-7b-hf \
            --tensor-parallel-size 1 \
            --gpu-memory-utilization 0.9
        ''',
        ports=8000,
        resources=sky.Resources(accelerators='A100:1')
    )
```

## 十，常见问题

### 10.1 故障排除

```bash
# 检查集群状态
sky status

# 查看详细错误
sky logs my-cluster --job 1 --err

# 调试模式
sky launch --dryrun task.yaml

# 查看云日志
sky logs my-cluster --cloud aws --region us-west-2
```

### 10.2 配额问题

```bash
# AWS 配额不足
aws service-quota request-service-quota-increase \
    --service-code ec2 \
    --quota-code L-20F13E48 \
    --desired-value 8

# GCP 配额不足
gcloud compute quotas update \
    --project=my-project \
    --region=us-west2 \
    --service=compute.googleapis.com \
    --reset
```

### 10.3 性能问题

```python
# GPU 利用率低？
# → 检查是否使用了正确的 GPU 类型
task.set_resources(sky.Resources(accelerators='A100:1'))

# 内存不足？
# → 使用更大的实例或启用混合精度
task.set_resources(sky.Resources(
    accelerators='A100:1',
    memory=64,
))

# 磁盘 IO 慢？
# → 使用 NVMe 实例
task.set_resources(sky.Resources(
    accelerators='A100:1',
    disk_size=1000,
    disk_tier='high',
))
```

## 十一，总结

SkyPilot 是**任意云 LLM 服务的最佳选择**：

| 维度 | 说明 |
|------|------|
| ☁️ **任意云** | AWS / GCP / Azure / Lambda / Cloudflare 统一接口 |
| 💰 **成本** | Spot 实例节省 70%+，累计节省 $10M+ |
| 🔄 **可靠** | 自动故障转移，托管 Spot 自动恢复 |
| 🚀 **快速** | 一行代码启动 LLM 服务 |
| 📊 **规模** | 1000+ 任务/天 |

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/skypilot-org/skypilot |
| 文档 | https://skypilot.readthedocs.io |
| Slack | https://join.slack.com/t/skypilot-org/shared_invite |
| 论文 | https://arxiv.org/abs/2205.07133 |

---

_🦞 本文由钳岳星君撰写，基于 SkyPilot (9.8k Stars)_
