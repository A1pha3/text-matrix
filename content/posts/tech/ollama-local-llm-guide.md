---
title: "Ollama：本地大模型运行完全指南"
date: 2026-04-06T22:18:00+08:00
slug: "ollama-local-llm-guide"
description: "全面介绍 168.9k Stars 的 Ollama 本地大模型运行平台，涵盖安装配置、模型管理、Modelfile 自定义、OpenAI 兼容 API、Agent/ReAct 模式、多模态模型、GPU 加速，以及与 LangChain 的集成方法。"
draft: false
categories: ["技术笔记"]
tags: ["Ollama", "本地大模型", "LLM", "隐私计算", "开源", "GPU加速"]
---

## 学习目标

通过本文，你将全面掌握以下核心能力：

- 深入理解 Ollama 的项目定位、核心概念和设计理念
- 掌握 Ollama 的安装、配置和基本使用方法
- 学会运行和管理各种大模型（Llama、Gemma、Mistral 等）
- 理解 Modelfile 自定义模型配置
- 掌握 OpenAI 兼容 API 服务搭建
- 理解 Agent 和 ReAct 模式
- 学会 GPU 加速配置和多模态模型使用
- 掌握 Ollama 与 LangChain 的集成方法

---

## 1. 项目概述

### 1.1 是什么

**Ollama** 是一个让你在**本地机器上运行开源大模型**的平台。它提供了简单的命令来下载、运行和管理 AI 模型，无需云服务，完全离线可用。

核心理念：**隐私优先** - 你的数据永远不需要离开你的机器。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | **144k** |
| GitHub Forks | **56.5k** |
| Commits | **9,600+** |
| Issues | **9,600+** |
| Releases | **100+** |
| 最新版本 | **v0.5.20** (2026-03-30) |
| License | **MIT** |
| 语言 | **Go 98.6%**，Shell 1.0% |

### 1.3 为什么选择 Ollama

| 特性 | 说明 |
|------|------|
| **隐私优先** | 数据完全本地处理，无需上传云端 |
| **简单易用** | 一条命令即可运行模型 |
| **模型丰富** | 100+ 开源模型可选 |
| **GPU 加速** | 支持 CUDA 和 Apple Metal |
| **API 兼容** | OpenAI 兼容接口 |
| **跨平台** | Mac/Linux/Windows |
| **开源免费** | MIT 许可证 |

### 1.4 Ollama vs 其他方案

| 方案 | Ollama | vLLM | LM Studio |
|------|--------|-------|-----------|
| **易用性** | ⭐⭐⭐⭐⭐ 一条命令 | ⭐⭐ 复杂 | ⭐⭐⭐⭐ GUI |
| **模型支持** | ⭐⭐⭐⭐ 100+ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **API** | OpenAI 兼容 | OpenAI 兼容 | 部分兼容 |
| **GPU 利用率** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **隐私** | ⭐⭐⭐⭐⭐ 完全本地 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 2. 安装与配置

### 2.1 安装方式

**macOS（推荐）**：

```bash
# 下载安装
curl -fsSL https://ollama.com/install.sh | sh

# 或使用 Homebrew
brew install ollama
```

**Linux**：

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows**：

从 https://ollama.com/download 下载安装包

### 2.2 验证安装

```bash
# 检查版本
ollama --version

# 查看帮助
ollama --help
```

### 2.3 GPU 配置

**CUDA（NVIDIA）**：

```bash
# 确保安装了 NVIDIA 驱动
nvidia-smi

# Ollama 会自动检测 CUDA
ollama run llama3.2
```

**Apple Metal（M 系列芯片）**：

```bash
# macOS 默认使用 Metal 加速
ollama run llama3.2
```

**手动指定 GPU**：

```bash
# 强制使用 CUDA
CUDA_VISIBLE_DEVICES=0 ollama run llama3.2

# 查看 GPU 使用情况
ollama ps
```

---

## 3. 快速开始

### 3.1 运行第一个模型

```bash
# 下载并运行 Llama 3.2
ollama run llama3.2

# 如果没有指定版本，会自动下载最新版本
# 首次运行会下载模型（约 2GB）
```

### 3.2 对话示例

```
>>> 你好，请介绍一下自己
Hello! I'm Llama 3.2, a large language model developed by Meta. 
I'm trained on a diverse dataset of text from the internet and 
other sources, which helps me understand and generate human-like
language across many topics.

How can I help you today?

>>> 用中文回答：你是什么？
我是 Llama 3.2，由 Meta 公司开发的大型语言模型。
我可以帮助你完成各种任务，比如回答问题、写作、编程等。

>>> /bye
```

### 3.3 常用命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `run` | 运行模型 | `ollama run llama3.2` |
| `pull` | 下载模型 | `ollama pull llama3.2` |
| `list` | 列出已下载模型 | `ollama list` |
| `show` | 显示模型信息 | `ollama show llama3.2` |
| `cp` | 复制模型 | `ollama cp llama3.2 my-model` |
| `rm` | 删除模型 | `ollama rm llama3.2` |
| `ps` | 显示运行中的模型 | `ollama ps` |

---

## 4. 模型管理

### 4.1 模型库概览

Ollama 支持 100+ 开源模型：

| 模型系列 | 代表模型 | 参数量 | 适用场景 |
|---------|---------|--------|---------|
| **Llama** | llama3.2, llama3.1 | 1B-405B | 通用对话 |
| **Gemma** | gemma3, gemma2 | 2B-27B | 轻量高效 |
| **Mistral** | mistral, mixtral | 7B-8x22B | 编程/推理 |
| **Code** | codellama, deepseek-coder | 7B-34B | 代码生成 |
| **Phi** | phi3, phi4 | 3.8B-14B | 端侧部署 |
| **Qwen** | qwen2.5, qwen2.5-coder | 0.5B-72B | 中文/编程 |
| **Llava** | llava, llava-llama3 | 7B-34B | 多模态 |

### 4.2 下载模型

```bash
# 下载指定版本
ollama pull llama3.2:3b      # 3B 参数版本（小内存）
ollama pull llama3.2:11b     # 11B 参数版本
ollama pull llama3.2:90b     # 90B 参数版本（需要大量内存）

# 下载多模态模型
ollama pull llava
ollama pull llava-llama3

# 查看可用的模型标签
ollama show llama3.2
```

### 4.3 模型列表

```bash
# 列出已下载的模型
ollama list

# 示例输出
NAME                    ID           SIZE      MODIFIED
llama3.2               5e1d8c5e3e7c   2.0GB    4 hours ago
gemma3                  7c0c5e4d2b8f   5.2GB    2 days ago
codellama               a1b2c3d4e5f6   3.8GB    3 days ago
```

### 4.4 删除模型

```bash
# 删除模型
ollama rm llama3.2

# 删除所有模型
ollama rm *
```

---

## 5. Modelfile 自定义配置

### 5.1 什么是 Modelfile

Modelfile 是 Ollama 的模型配置文件，允许你：

- 自定义系统提示词
- 调整超参数
- 添加额外权重
- 配置模型行为

### 5.2 创建自定义模型

```bash
# 创建 Modelfile
cat > Modelfile << 'EOF'
FROM llama3.2

# 设置系统提示词
SYSTEM """
你是一个专业的 Python 程序员助手。
你擅长编写高质量、可维护的 Python 代码。
请用中文回答。
"""

# 调整参数
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 4096

# 设置模板
TEMPLATE """
<s>[INST] <<SYS>>
{{ .System }}
<</SYS>>
{{ .Prompt }} [/INST]
"""
EOF

# 创建模型
ollama create my-python-assistant -f Modelfile
```

### 5.3 常用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `temperature` | 创造性（0-2） | 0.8 |
| `top_p` | Nucleus 采样 | 0.9 |
| `num_ctx` | 上下文长度 | 2048 |
| `top_k` | Top-K 采样 | 40 |
| `repeat_penalty` | 重复惩罚 | 1.1 |
| `num_gpu` | GPU 数量 | 自动 |

### 5.4 系统提示词模板

```bash
# 使用中文优化的 Llama
cat > Modelfile << 'EOF'
FROM llama3.2

SYSTEM """
你是一个乐于助人的 AI 助手。
你擅长用简洁清晰的语言解释复杂概念。
请始终用中文回答。
"""

PARAMETER temperature 0.7
PARAMETER num_ctx 4096
EOF

ollama create my-assistant -f Modelfile
ollama run my-assistant
```

---

## 6. OpenAI 兼容 API

### 6.1 启动 API 服务

```bash
# 启动服务器（默认端口 11434）
ollama serve

# 后台运行
nohup ollama serve > server.log 2>&1 &

# 指定端口
OLLAMA_HOST=0.0.0.0:8080 ollama serve
```

### 6.2 API 调用示例

**Chat Completions**：

```bash
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2",
    "messages": [
      {"role": "user", "content": "用 Python 写一个快速排序"}
    ],
    "stream": false
  }'
```

**Responses**：

```bash
curl http://localhost:11434/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2",
    "input": "解释什么是机器学习"
  }'
```

**Embeddings**：

```bash
curl http://localhost:11434/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nomic-embed-text",
    "input": "Hello world"
  }'
```

### 6.3 OpenAI SDK 兼容

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # 占位符，Ollama 不需要真实 key
)

response = client.chat.completions.create(
    model="llama3.2",
    messages=[
        {"role": "user", "content": "你好"}
    ]
)

print(response.choices[0].message.content)
```

### 6.4 LangChain 集成

```python
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="llama3.2",
    temperature=0.7,
    base_url="http://localhost:11434"
)

response = llm.invoke("解释什么是 Python")
print(response.content)
```

---

## 7. Agent 与 ReAct 模式

### 7.1 什么是 Agent

Agent 是 Ollama 的**自主执行任务**模式，可以：

- 调用外部工具（搜索、计算）
- 多步骤推理
- 自主决策下一步行动

### 7.2 使用 Agent

```bash
# 运行支持 Agent 的模型
ollama run llama3.2

# 在对话中使用 /agent 命令
>>> /agent
Available agents:
1. reasoning - Deep research and analysis
2. assistant - General purpose assistant

Select agent (1-2): 1

# Agent 会自动规划并执行任务
```

### 7.3 自定义 Tool

```bash
# 创建包含 Tool 的 Modelfile
cat > Modelfile << 'EOF'
FROM llama3.2

# 定义可用工具
TOOL """
{
  "type": "function",
  "function": {
    "name": "calculate",
    "description": "计算数学表达式",
    "parameters": {
      "type": "object",
      "properties": {
        "expression": {
          "type": "string",
          "description": "要计算的数学表达式"
        }
      }
    }
  }
}
"""

SYSTEM """
你是一个数学助手，可以使用计算器工具。
对于复杂计算，使用 calculate 工具。
"""
EOF

ollama create math-assistant -f Modelfile
ollama run math-assistant
```

### 7.4 ReAct 推理模式

ReAct = Reasoning + Acting

```
用户: 计算 15 * 23 + 17

思考: 用户要求计算数学表达式。我应该使用 calculate 工具。
动作: calculate(expression="15 * 23 + 17")
观察: 结果是 362
思考: 计算完成，现在可以给出最终答案。
最终答案: 15 × 23 + 17 = 362
```

---

## 8. 多模态模型

### 8.1 什么是多模态

多模态模型可以**理解和处理图像+文本**：

- 看图说话
- 图像问答
- 图像内容分析
- 文档理解

### 8.2 使用多模态模型

```bash
# 下载 llava 模型
ollama pull llava

# 或使用最新的 llava-llama3
ollama pull llava-llama3
```

### 8.3 图像分析示例

**通过 API**：

```bash
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llava",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}},
          {"type": "text", "text": "描述这张图片"}
        ]
      }
    ]
  }'
```

**本地图片**：

```bash
# 使用 curl 上传本地图片
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llava",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,$(base64 -i /path/to/image.jpg)"}},
          {"type": "text", "text": "这张图片里有什么？"}
        ]
      }
    ]
  }'
```

### 8.4 多模态应用场景

| 场景 | 说明 |
|------|------|
| **文档理解** | 解析截图、PDF、表格 |
| **图像问答** | 智能图像交互 |
| **视觉搜索** | 图生文检索 |
| **自动化测试** | UI 截图分析 |

---

## 9. GPU 加速与性能优化

### 9.1 GPU 利用率

```bash
# 查看 GPU 使用
ollama ps

# 示例输出
NAME            ID           SIZE      PROCESSOR    UNTIL
llama3.2       a1b2c3d4     2.0GB     100% GPU    4 minutes ago
```

### 9.2 内存优化

```bash
# 查看系统资源
ollama run llama3.2 --info

# 示例输出
{
  "success": true,
  "model": "llama3.2",
  "parameters": "3B",
  "size": "2.0GB",
  "gpu": "Apple M2 Pro",
  "memory": {
    "total": "32GB",
    "used": "8GB",
    "available": "24GB"
  }
}
```

### 9.3 KV Cache 配置

```bash
# 使用更大的上下文
ollama run llama3.2 --num-ctx 8192

# 查看当前上下文大小
ollama show llama3.2 | grep "context length"
```

### 9.4 批量推理

```bash
# 使用 ollama generate
ollama generate --help

# 示例
echo "写一首诗\n写一段代码\n解释一个概念" | ollama run llama3.2
```

---

## 10. 常见问题与解决方案

### 10.1 模型下载失败

```bash
# 检查网络
curl -I https://ollama.com

# 使用代理
HTTPS_PROXY=http://proxy:8080 ollama pull llama3.2

# 重试
ollama pull llama3.2 --insecure
```

### 10.2 内存不足

```bash
# 使用更小的模型
ollama pull llama3.2:3b    # 3B 参数版本

# 减少上下文大小
ollama run llama3.2 --num-ctx 2048

# 清理内存
ollama rm <unused-model>
```

### 10.3 GPU 不被识别

```bash
# NVIDIA: 检查驱动
nvidia-smi

# NVIDIA: 检查 CUDA
nvcc --version

# Apple Silicon: 检查 Metal
metal --version

# 强制使用 CPU（不推荐，性能差）
CUDA_VISIBLE_DEVICES="" ollama run llama3.2
```

### 10.4 API 超时

```bash
# 增加超时时间
OLLAMA_TIMEOUT=300s ollama serve

# 或在请求中设置
curl --max-time 300 http://localhost:11434/v1/chat/completions
```

---

## 11. 最佳实践

### 11.1 开发环境配置

```bash
# 1. 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. 下载开发用模型
ollama pull llama3.2          # 通用对话
ollama pull codellama          # 代码生成
ollama pull nomic-embed-text   # 向量化

# 3. 启动 API 服务
ollama serve &

# 4. 在代码中使用
```

### 11.2 生产环境配置

```bash
# 使用 systemd 管理服务
sudo tee /etc/systemd/system/ollama.service << 'EOF'
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF

sudo systemctl enable ollama
sudo systemctl start ollama
```

### 11.3 安全建议

- 限制 API 访问（防火墙）
- 使用反向代理（Nginx）添加认证
- 定期更新 Ollama 版本
- 不在公网暴露 API

---

## 12. 总结

**Ollama** 是本地运行大模型的**最佳开源方案**：

| 优势 | 说明 |
|------|------|
| **隐私优先** | 数据完全本地，无需上传 |
| **简单易用** | 一条命令运行模型 |
| **模型丰富** | 100+ 开源模型可选 |
| **性能优化** | GPU 加速，开箱即用 |
| **API 兼容** | OpenAI 兼容，易集成 |
| **完全开源** | MIT 许可证 |

**适用场景**：

- 本地 AI 开发测试
- 隐私敏感数据处理
- 离线环境部署
- 嵌入式/端侧 AI
- 学习和实验大模型

**官方资源**：

- GitHub：https://github.com/ollama/ollama
- 官网：https://ollama.com
- 模型库：https://ollama.com/library
- 文档：https://github.com/ollama/ollama#readme
- API 文档：https://github.com/ollama/ollama/blob/main/docs/api.md