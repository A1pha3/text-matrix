---
title: "llama.cpp：12.6 万 Star 的纯 C/C++ LLM 推理引擎完全指南"
date: "2026-04-06T22:45:00+08:00"
slug: "llama-cpp-gogu-gpu-llm-inference-guide"
github_repo: "ggml-org/llama.cpp"
aliases:
  - "/posts/tech/llama.cpp-cpp-llm-inference-guide/"
description: "llama.cpp（ggml-org/llama.cpp）是纯 C/C++ 实现、无任何框架依赖的大语言模型推理引擎，126k+ Stars。本文基于官方 README 与 CLI 文档核实的事实，详解 GGUF 格式、量化原理（Q4_K/Q5_K/Q6_K/IQ 系列）、16 种硬件后端、统一 llama 命令行（cli/serve）、OpenAI 兼容 API 与性能优化。"
draft: false
categories: ["技术笔记"]
tags: ["llama.cpp", "LLM推理", "GGUF", "量化", "CPU推理", "GPU加速", "本地部署"]
---

## 学习目标

读完本文并完成自测后，你将能够：

- 解释 llama.cpp 的架构定位：它把「模型权重 → 可推理的本地服务」这条链路里的每一环分别做了什么
- 理解 GGUF 为什么是自包含的、为什么能内存映射加载，以及它和 PyTorch 权重、ggml 库的关系
- 看懂量化：为什么 4-bit 量化几乎无损地省掉 75% 内存，k-quant 与 i-quant 的区别，以及如何按硬件挑选量化级别
- 用当前（2026 年）的统一命令 `llama cli` / `llama serve` 完成从下载模型到提供 OpenAI 兼容 API 的全流程
- 针对内存、显存、并发三组瓶颈，做有依据的性能调优（KV cache 量化、Flash Attention、GPU 分层、--fit）

---

## 阅读导航

- 想立刻跑起来 → `§4 安装` 与 `§5 快速开始`
- 想理解为什么它这么快 → `§3 技术架构`（ggml、GGUF、量化原理）
- 想给业务提供 API → `§6 API 服务器`
- 想让推理更快 / 更省内存 → `§7 性能优化`
- 想转换自己的模型 → `§8 模型转换与量化`
- 想判断它适不适合你 → `§1.3 能力边界`

---

## §1 核心认知

### 1.1 一句话定位

**llama.cpp 是一套纯 C/C++ 实现、无框架依赖的大语言模型推理引擎**：吃进一个 GGUF 格式的模型文件，吐出一个能在 CPU、GPU 或 NPU 上高效运行的推理服务。项目主页用一句话概括：*LLM inference in C/C++*。

它由 Georgi Gerganov 于 2023 年 3 月创建，现由 ggml-org 组织维护，最初是为了让 Meta 开源的 LLaMA 模型不依赖 Python 和 PyTorch 也能跑起来。今天它已经支持几乎所有主流开源模型架构，成为本地推理事实上的地基——Ollama、LM Studio、Jan 等桌面工具，底层都基于它。

### 1.2 为什么会有它：一段简史

2023 年 2 月，Meta 开源 LLaMA。当时跑大模型的「标准姿势」是 PyTorch + GPU + Python 环境：环境依赖重、启动慢、且默认要求 CUDA 显卡。llama.cpp 用最朴素的方式破了这个局——把整个推理过程用 C/C++ 重写：

- **零 Python 运行时**：编译出的二进制直接跑，不装环境
- **CPU 优先**：x86 的 AVX/AVX2/AVX512/AMX 指令集、ARM 的 NEON，把「没有显卡的笔记本」变成可用的推理设备
- **Apple Silicon 一等公民**：ARM NEON + Accelerate + Metal 三件套，让 M 系列芯片成为本地推理的主流平台

这三个选择叠加，让「本地跑大模型」从实验室操作变成了开发者日常。

### 1.3 能力边界

| 场景 | 是否适合 llama.cpp | 原因 |
|------|:---:|------|
| 个人电脑本地跑 1B–70B 模型 | ✅ | CPU/GPU/NPU 全覆盖，量化灵活 |
| 隐私敏感、数据不出内网 | ✅ | 完全离线，不联网也能推理 |
| 边缘设备（树莓派、手机、嵌入式） | ✅ | 有 Android、RISC-V、WebGPU 后端 |
| 高并发生产服务（每秒数百请求） | ⚠️ 需谨慎 | 更推荐 vLLM / SGLang 等批处理优化框架 |
| 大规模分布式训练/推理集群 | ❌ | 定位是本地推理，非训练框架 |

一句话：**llama.cpp 的价值在「单机、少卡、离线、可控」**，不在「大规模并发服务」。

---

## §2 项目数据与生态

### 2.1 核心数据（2026-09-04 从 GitHub API 核实）

| 维度 | 数值 |
|------|------|
| 仓库 | [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) |
| 定位 | LLM inference in C/C++ |
| Stars | 126,417 ⭐ |
| Forks | 22,514 |
| Contributors | 1,957 |
| Commits | 10,786 |
| License | MIT |
| 语言构成 | C++ 56.2%、C 15.5%、Python 7.3%、CUDA 5.4%、TypeScript 4.2%、Svelte 2.2%、其他 9.2% |
| 创建时间 | 2023-03-10 |
| 最新发布 | v0.3.0（滚动发布，Release 共 7,000+ 个） |
| 官方站点 | [llama.app](https://llama.app/) |

注意两点：仓库已从个人的 `ggerganov/llama.cpp` 迁到组织 `ggml-org/llama.cpp`；当前主语言是 C++（约 56%），老旧的「C 94%」说法早已过时。

### 2.2 硬件后端（16 种）

llama.cpp 采用「核心 + 后端」架构，同一个模型文件在不同设备上由不同后端加速：

| 后端 | 目标设备 |
|------|----------|
| Metal | Apple Silicon |
| CUDA | NVIDIA GPU |
| HIP | AMD GPU |
| MUSA | 摩尔线程（Moore Threads）GPU |
| Vulkan | 通用 GPU |
| SYCL | Intel GPU |
| OpenCL | Adreno GPU |
| CANN | 昇腾（Ascend）NPU |
| OpenVINO | Intel CPU/GPU/NPU |
| ZenDNN | AMD CPU |
| BLAS / BLIS | 通用 CPU |
| RPC | 多机远程推理 |
| WebGPU | 浏览器 |
| VirtGPU、IBM zDNN、Hexagon | 特殊/虚拟化设备 |

### 2.3 支持的量化范围

官方 README 明确支持 **1.5-bit 到 8-bit** 的整数量化（Q2_K ~ Q8_0 及 i-quant 系列），这是「内存受限设备也能跑模型」的根基。量化细节见 `§3.3`。

### 2.4 依赖的第三方库

llama.cpp 尽量零依赖，但内嵌了几个单头文件库：`cpp-httplib`（server 的 HTTP 服务）、`stb`（图像解码，多模态用）、`nlohmann/json`（JSON）、`miniaudio`（音频解码，多模态用）。全部是 MIT / Public Domain，无重型框架。

---

## §3 技术架构

### 3.1 ggml：张量计算库

llama.cpp 构建在 [ggml](https://github.com/ggml-org/ggml) 张量库之上。ggml 是一个 C 语言实现的张量计算框架，为推理场景做了针对性设计：

- **内存友好**：支持内存映射加载权重，避免一次性把整个模型读进内存
- **多后端抽象**：同一套算子（矩阵乘、注意力等）可以调度到 CPU/GPU/NPU 不同后端
- **自动并行**：有向无环图（DAG）式执行，自动并行化

理解这一层，就理解了 llama.cpp 能横跨这么多硬件的原因：**推理算子与硬件后端解耦**。

### 3.2 GGUF：模型文件格式

GGUF（GGML Universal Format）是 llama.cpp 定义的模型文件格式，2023 年 8 月取代了早期的 GGML / GGMF 格式。它的核心设计目标：

| 特性 | 说明 |
|------|------|
| **自包含** | 权重、超参数、分词器、元数据全部打在一个文件里，拷贝即用 |
| **内存映射** | 支持 mmap 按需读页，加载速度取决于磁盘而非把整个文件读入内存 |
| **类型化元数据** | 每个元数据键值对都带类型（int/float/string/array），机器可解析 |
| **架构无关** | 文件头声明 `architecture`（如 llama、qwen、gemma），不同架构共用格式 |

转换路径是：

```
PyTorch (.safetensors/.bin)  ──convert_hf_to_gguf.py──▶  GGUF (f16)  ──llama quantize──▶  GGUF (Q4_K_M)
```

GGUF 是 llama.cpp 与 Hugging Face 生态衔接的桥梁——HF 上的模型通过 `-hf` 参数可直接下载 GGUF 版（见 `§5`）。

### 3.3 量化：为什么能又快又省

**核心瓶颈是内存带宽，不是算力。** 自回归解码是「一次生成一个 token」，每一步都要把全部权重从内存读到计算单元。权重精度越低，每步读的字节越少，解码速度几乎线性提升。这就是量化的收益来源。

内存换算（每参数字节数）：

| 精度 | 每参数字节 | 8B 模型约 | 说明 |
|------|-----------|----------|------|
| FP16 | 2.0 | ~16 GB | 无损失，原始精度 |
| Q8_0 | 1.0 | ~8.5 GB | 接近无损 |
| Q6_K | 0.8 | ~6.7 GB | k-quant，质量很好 |
| Q5_K_M | 0.68 | ~5.7 GB | k-quant |
| **Q4_K_M** | **0.58** | **~4.9 GB** | **官方默认推荐，性价比最高** |
| Q3_K_M | 0.42 | ~3.5 GB | 质量明显下降 |
| IQ2_XS / IQ1_S | <0.3 | <2.5 GB | 需 imatrix，极小内存 |

**k-quant 与 i-quant 的区别**：

- **k-quant（Q4_K、Q5_K、Q6_K）**：以 256 个权重为「超块」，内部再分组，用共享的 scale 和 min 值压缩。经典、稳定、无需额外数据，`Q4_K_M` 是其中「质量/体积」折中最好的档位。
- **i-quant（IQ1/IQ2/IQ3/IQ4）**：使用**重要性矩阵（imatrix）**指导量化，能用更少的 bit 保住更重要的权重，但需要先用校准数据生成 imatrix 文件才能发挥最佳质量。

**选择建议（按内存）**：

| 内存/显存 | 推荐量化 | 理由 |
|-----------|----------|------|
| 4–6 GB | Q4_K_M | 8B 级模型的甜点位 |
| 8 GB | Q5_K_M | 同样 8B 级，质量更好 |
| 12–16 GB | Q6_K 或 Q8_0 | 体积换质量，仍远小于 FP16 |
| 2 GB 级极限 | IQ2_XS 等 | 配合 imatrix，能塞进极小设备 |
| 显存紧张但想跑更大模型 | CPU+GPU 混合（`-ngl` 分层） | 见 `§7.4` |

---

## §4 安装

四种方式，按推荐度排序：

**方式一：官方应用 llama.app（macOS）**

到 [llama.app](https://llama.app/) 下载安装，自带图形界面与模型管理，开箱即用。

**方式二：预编译二进制**

从 [Releases](https://github.com/ggml-org/llama.cpp/releases) 下载对应平台的二进制，解压即用，无需编译。

**方式三：源码编译（CMake，推荐进阶用户）**

```bash
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j $(nproc)
```

按需开启后端（示例：CUDA / Metal / Vulkan）：

```bash
# NVIDIA GPU
cmake -B build -DLLAMA_CUDA=ON -DCMAKE_BUILD_TYPE=Release

# Apple Silicon
cmake -B build -DLLAMA_METAL=ON -DCMAKE_BUILD_TYPE=Release

# 通用 GPU（Vulkan）
cmake -B build -DLLAMA_VULKAN=ON -DCMAKE_BUILD_TYPE=Release
```

编译产物在 `build/bin/` 下，核心是统一命令 `llama`（子命令见 `§5`、`§6`）。

> 2025 年起项目已移除 Makefile，统一走 CMake；官方文档也明确推荐 CMake。

**方式四：Docker**

官方提供三组镜像（每组含 `full` / `light` / `server` 三种，另有 `-cuda` / `-rocm` / `-musa` 变体）：

```bash
# 拉取 server 镜像（OpenAI 兼容 API）
docker pull ghcr.io/ggml-org/llama.cpp:server

# 运行
docker run -v /path/to/models:/models -p 8080:8080 \
  ghcr.io/ggml-org/llama.cpp:server \
  -m /models/your-model.gguf --host 0.0.0.0 --port 8080
```

---

## §5 快速开始

2026 年的 llama.cpp 采用**统一命令 `llama` + 子命令**的结构，最常用的两个是 `llama cli`（交互推理）和 `llama serve`（API 服务）。

### 5.1 直接从 Hugging Face 拉模型并推理

这是官方 Quick Start 推荐的最短路径，`-hf` 会自动下载 GGUF 模型（默认量化 Q4_K_M，若仓库无此档位则取第一个文件）：

```bash
llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF
```

输入提示词即可对话。`-hf` 也可指定量化档位：

```bash
llama cli -hf ggml-org/GLM-4.7-Flash-GGUF:Q4_K_M
```

### 5.2 使用本地 GGUF 文件

```bash
llama cli -m ./models/qwen2.5-7b-instruct-q4_k_m.gguf \
  -p "用一句话介绍量子计算" \
  -n 256
```

- `-m`：模型路径
- `-p`：提示词
- `-n / --predict`：生成 token 数（-1 表示无限，默认值）
- `-c / --ctx-size`：上下文长度（默认 0，取模型自带值）
- `-t / --threads`：CPU 线程数（默认 -1，自动）
- `-fa`：Flash Attention（默认 auto）

### 5.3 交互模式与采样参数

```bash
llama cli -m ./models/qwen2.5-7b-instruct-q4_k_m.gguf \
  --temp 0.8 --top-k 40 --top-p 0.95 --repeat-penalty 1.1
```

当前默认采样链（`--samplers`）为：

```
penalties;dry;top_n_sigma;top_k;typ_p;top_p;min_p;xtc;temperature
```

几个关键采样的作用：

| 参数 | 默认 | 作用 |
|------|------|------|
| `--temp` | 0.80 | 温度，越高越随机；0 则贪心 |
| `--top-k` | 40 | 只在概率前 K 个 token 里采样 |
| `--top-p` | 0.95 | 累积概率到 p 为止的 token 集合里采样 |
| `--min-p` | 0.05 | 过滤掉相对概率过低的 token |
| `--repeat-penalty` | 1.0 | 重复惩罚，>1 抑制重复 |
| `-s / --seed` | -1 | 随机种子，固定可复现 |

---

## §6 API 服务器

### 6.1 启动服务

```bash
# 指定本地模型
llama serve -m ./models/qwen2.5-7b-instruct-q4_k_m.gguf \
  --host 0.0.0.0 --port 8080

# 或直接指定 HF 模型（自动下载）
llama serve -hf ggml-org/Qwen3.5-0.8B-GGUF
```

### 6.2 OpenAI 兼容接口

`llama serve` 提供 OpenAI 兼容的 REST API，主流端点：

- `POST /v1/chat/completions` — 对话补全
- `POST /v1/completions` — 文本补全
- `POST /v1/embeddings` — 向量化
- `GET /v1/models` — 模型列表
- `GET /health` — 健康检查

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-7b",
    "messages": [
      {"role": "system", "content": "你是一个严谨的助手"},
      {"role": "user", "content": "解释一下什么是 GGUF 格式"}
    ],
    "max_tokens": 300
  }'
```

流式输出（SSE）只需加 `"stream": true`，与 OpenAI 协议一致，可无缝替换 SDK 的 base_url：

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5-7b","messages":[{"role":"user","content":"讲个冷笑话"}],"stream":true}'
```

### 6.3 并发

`-np / --parallel` 控制并行序列数，适合多用户/多请求场景：

```bash
llama serve -m ./models/qwen2.5-7b-instruct-q4_k_m.gguf \
  -c 8192 -np 4 --host 0.0.0.0 --port 8080
```

注意：并行数会按比例扩大 KV cache 内存占用（见 `§7.2`）。

---

## §7 性能优化

### 7.1 先估算内存

推理内存 ≈ 模型权重 + KV cache + 计算中间量。权重部分：

```
权重内存（GB）≈ 参数量（B）× 每参数字节数
```

8B 模型 Q4_K_M 约 4.9 GB，Q8_0 约 8.5 GB，FP16 约 16 GB。选量化档位前，先看这份预算。

### 7.2 KV Cache 量化（最有效的省内存手段）

KV cache 随上下文长度线性增长，长上下文下经常反超权重成为内存大头。默认 `f16` 类型，可用 `-ctk / -ctv` 分别指定 K、V 的类型，支持 `q8_0`、`q4_0`、`q4_1`、`iq4_nl` 等：

```bash
llama serve -m ./models/qwen2.5-7b-instruct-q4_k_m.gguf \
  -c 32768 -ctk q8_0 -ctv q8_0
```

长上下文 + KV 量化，通常能省下 30–50% 的 cache 内存，质量损失很小。这是跑大 context 的必选项。

### 7.3 Flash Attention

`-fa`（`--flash-attn`）默认 `auto`，在支持的设备上自动启用。它把注意力的内存复杂度从 O(n²) 降到 O(n)，长上下文收益显著，基本无条件开启：

```bash
llama cli -m ./models/qwen2.5-7b-instruct-q4_k_m.gguf -fa -c 32768
```

### 7.4 GPU 分层与自动适配

`-ngl / --gpu-layers` 控制把多少层放进显存，**默认已自动（auto）**：

```bash
# 全量放 GPU
llama cli -m ./models/qwen2.5-7b-instruct-q4_k_m.gguf -ngl all

# 显存不够时分层（部分层 CPU，其余 GPU），实现 CPU+GPU 混合推理
llama cli -m ./models/qwen2.5-7b-instruct-q4_k_m.gguf -ngl 24
```

`--fit`（默认 on）会自动调整未指定参数以适配设备内存，并可用 `--fit-target` 设定每张卡的预留余量。模型大于显存时，**不要整模型硬塞 GPU**——用 `-ngl` 分层，让 GPU 算一层、CPU 算一层，是官方推荐的混合方案。

多 GPU 时用 `-sm` 选择切分方式：

| 模式 | 行为 | 适用 |
|------|------|------|
| `layer`（默认） | 按层流水线切分 | 显存叠加最有效 |
| `row` | 按行并行切分 | 单请求加速 |
| `tensor` | 权重+KV 并行（实验） | 高端场景 |

### 7.5 基准测试

`llama bench` 内置推理基准，比较不同模型/量化/线程的 token/s：

```bash
llama bench -m ./models/qwen2.5-7b-instruct-q4_k_m.gguf -t 8 -ngl all
```

输出会给出 prompt 处理速度（prefill，tokens/s）与生成速度（decode，tokens/s）两列，后者决定对话体验。

### 7.6 常见调优清单

| 目标 | 手段 |
|------|------|
| 生成更快 | 提升 `-ngl`；用 `-fa`；降低 KV cache 精度 |
| 省内存 | KV 量化 `-ctk/-ctv`；降低量化档位；`-c` 减到够用 |
| 长上下文 | `-fa` + KV 量化 + 足够的 `-c` |
| 多用户 | `-np` 并行 + 相应加大 `-c` |
| 模型>显存 | `-ngl` 分层混合推理，别硬塞 |
| 载入更稳 | `--load-mode mlock` 锁定内存防换页（取代已废弃的 `--mlock`） |

---

## §8 模型转换与量化

### 8.1 Hugging Face 模型转 GGUF

转换脚本是 `convert_hf_to_gguf.py`（早期叫 `convert.py`）：

```bash
# 先下载 HF 模型（以非门控模型为例）
huggingface-cli download Qwen/Qwen2.5-7B-Instruct --local-dir ./qwen2.5-7b

# 转 GGUF（f16）
python convert_hf_to_gguf.py ./qwen2.5-7b --outfile ./models/qwen2.5-7b-f16.gguf --outtype f16
```

### 8.2 量化

```bash
llama quantize ./models/qwen2.5-7b-f16.gguf ./models/qwen2.5-7b-q4_k_m.gguf Q4_K_M
```

### 8.3 i-quant 与 imatrix

若想用 IQ 系列（更低 bit），先用校准语料生成 imatrix（`imatrix` 未并入统一命令，仍用独立二进制 `llama-imatrix`）：

```bash
llama-imatrix -m ./models/qwen2.5-7b-f16.gguf -f ./calibration.txt \
  --outfile ./models/qwen2.5-7b-imatrix.dat

llama quantize ./models/qwen2.5-7b-f16.gguf \
  ./models/qwen2.5-7b-iq2_xs.gguf IQ2_XS --imatrix ./models/qwen2.5-7b-imatrix.dat
```

没有 imatrix 的 i-quant 质量会明显打折，宁可用 Q4_K_M。

---

## §9 常见问题

**Q1：模型加载就报内存不足？**

先算预算（`§7.1`）。依次：换更低量化档位 → 减小 `-c` → 用 `-ngl` 分层。确认文件完整性：`ls -lh` 看大小是否与 HF 页面一致。

**Q2：GPU 加速没生效？**

- 确认编译时开了对应后端（`-DLLAMA_CUDA=ON` / `-DLLAMA_METAL=ON` / `-DLLAMA_VULKAN=ON`）
- 确认 `-ngl` 没设成 0 或禁用
- 运行 `llama cli --list-devices` 查看可用的设备列表

**Q3：生成质量差？**

先看量化档位是否过低（Q3 以下质量退化明显）；再检查采样参数——`--temp` 过高会随机，`--repeat-penalty` 过高会绕圈子。多数场景保持默认采样链即可。

**Q4：Hugging Face 下载慢？**

设置镜像或加速：

```bash
export HF_ENDPOINT=https://hf-mirror.com
# 或
HF_HUB_ENABLE_HF_TRANSFER=1 huggingface-cli download ...
```

**Q5：服务端口被占用？**

`lsof -i :8080` 查占用，换 `--port` 即可。

---

## §10 生态集成

llama.cpp 是生态的「底座」而不是「终点」，围绕它有一整层工具：

| 项目 | 角色 |
|------|------|
| [Ollama](https://ollama.com) | 模型管理与推理平台，底层基于 llama.cpp |
| [LM Studio](https://lmstudio.ai) | 图形化模型管理 + 推理 |
| [Jan](https://jan.ai) | 本地 ChatGPT 替代 |
| [text-generation-webui](https://github.com/oobabooga/text-generation-webui) | Web 界面 |
| [LocalAI](https://localai.io) | 自托管 OpenAI 替代 |

如果不需要图形界面、想要最大可控性，直接用 `llama serve` 就是最轻的一条路——一个二进制，一个 OpenAI 兼容端点。

---

## 自测：检查你的理解

1. 为什么「内存带宽」是自回归解码的瓶颈，量化为何能同时提速和降内存？
2. GGUF 相比 PyTorch 权重格式，自包含和 mmap 分别带来什么实际好处？
3. 一台 8GB 内存的 MacBook，跑 8B 模型该选哪档量化？为什么不是 FP16？
4. 显存 8GB、模型 Q4_K_M 需 4.9GB，但你要开 32k 上下文，内存还是不够——按顺序该调哪三个参数？
5. `llama serve` 与 OpenAI SDK 对接，需要改什么、不需要改什么？

---

## 进阶路径

1. **熟练操作**：用 `llama cli` 跑通 3 个不同架构模型（如 Qwen、Gemma、LLaMA 系），对比 `llama bench` 输出
2. **理解格式**：用十六进制查看器打开 GGUF 文件头，辨认 magic、版本、tensor 数量与元数据区
3. **量化实验**：同一模型分别量化 Q4_K_M、Q6_K、Q8_0，用基准和生成质量对比取舍
4. **服务化**：`llama serve` + OpenAI SDK 实现一个流式对话应用，再测 `-np` 并发的资源曲线
5. **深入源码**：读 `ggml` 的矩阵乘算子与 `llama` 的采样链实现；关注 libllama API（issue #9289）与 llama-server REST API 规范（issue #9291）
6. **为项目做贡献**：从修文档、补后端测试开始，逐步进入算子优化

---

## 资料口径说明

- **事实来源**：GitHub API（stars/forks/contributors/commits/language 统计）、官方 README（后端列表、量化范围、Quick Start 命令）、官方 CLI 文档 `tools/cli/README.md`（参数与默认值）、Docker 文档 `docs/docker.md`（镜像名与用法），以上均为 2026-09-04 从仓库 master 分支核实。
- **命令约定**：统一命令 `llama cli / llama serve` 为当前官方 Quick Start 写法；旧版独立二进制名（`llama-cli`、`llama-server`）已并入统一命令。
- **模型示例**：`ggml-org/Qwen3.5-0.8B-GGUF`、`ggml-org/GLM-4.7-Flash-GGUF` 取自官方 README / CLI 文档示例，未杜撰。其余模型名为已广泛发布的事实（Qwen2.5、Llama 3.1 等）。
- **数据口径**：Star 等指标随时间变化，文中数值以 2026-09-04 为准；量化档位对应的字节数/内存为工程近似值。
- **已知过时内容已修正**：仓库归属（ggerganov→ggml-org）、语言占比（C 为主→C++ 为主）、KV cache 参数（`--kv-cache-type`→`-ctk/-ctv`）、内存锁定参数（`--mlock/--mmap`→`--load-mode`）、转换脚本名（`convert.py`→`convert_hf_to_gguf.py`）。
