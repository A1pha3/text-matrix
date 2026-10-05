---
title: "ODS（原 DreamServer）：一条命令跑起完整本地 AI 栈"
date: "2026-05-17T20:11:45+08:00"
lastmod: "2026-10-04T10:00:00+08:00"
slug: "dreamserver-local-ai-stack-guide"
github_repo: "Osmantic/ODS"
source_key: "gh:Osmantic/ODS"
description: "ODS（前身 DreamServer）是 Osmantic 开源的本地 AI 服务器方案：一条命令自动检测硬件、选模型、启动全套服务——推理、聊天、语音、Agent、工作流、RAG、图片生成，数据不出本机。本文解析其架构、安装、硬件分级与运行模式，并给出采用建议。"
draft: false
categories: ["技术笔记"]
tags: ["开源", "本地部署", "LLM", "Docker", "RAG", "语音AI", "n8n", "ODS", "LiteLLM"]
band: review
gates: ["事实性", "去AI味", "观点依据"]
---

本地跑 AI 一直卡在同一个地方：模型只是起点，真正让人放弃的是后面那一串——聊天界面、推理引擎、语音识别、语音合成、向量库、工作流引擎、图片生成，每个都要单独装、单独配，还要让它们互相找得到对方。ODS（前身 DreamServer）把这个"周末工程"压缩成一条命令：自动检测硬件、自动选模型、自动把全套服务拉起来并接好线。本文基于 v3.0.0 Pre-Release 解析它怎么做到这一点，以及在 2026 年 10 月这个时点，什么人该上、什么人该等。

## 学习目标

读完这篇文章，你可以：

1. 说清 ODS 的定位：全栈本地 AI 服务器，不是单一推理引擎
2. 理解它的服务分层（聊天推理、语音、Agent、知识搜索、创意、隐私运维），以及一次请求如何穿过这些服务
3. 按官方安装命令在 Linux、macOS 或 Windows 上跑起来，并根据硬件选择正确的 Tier 和模型 Profile
4. 区分三种运行模式（local / cloud / hybrid）的适用场景和切换方式
5. 用 `ods` CLI 完成日常管理：状态查看、启停、模型切换、服务启用与禁用
6. 判断 ODS 是否适合你的场景，以及当前 V3 Pre-Release 阶段需要注意什么

## 目录

- [项目概览](#项目概览)
- [为什么本地 AI 难用](#为什么本地-ai-难用)
- [服务架构详解](#服务架构详解)
- [一次语音提问如何流过系统](#一次语音提问如何流过系统)
- [安装流程](#安装流程)
- [硬件自动检测与模型选择](#硬件自动检测与模型选择)
- [引导模式（Bootstrap）](#引导模式bootstrap)
- [日常管理命令](#日常管理命令)
- [扩展系统：让服务成为一等公民](#扩展系统让服务成为一等公民)
- [三种运行模式详解](#三种运行模式详解)
- [API 兼容性](#api-兼容性)
- [硬件需求与选型建议](#硬件需求与选型建议)
- [与同类项目对比](#与同类项目对比)
- [适用场景与采用建议](#适用场景与采用建议)
- [常见问题](#常见问题)
- [总结](#总结)
- [练习与自测](#练习与自测)
- [进阶路径](#进阶路径)
- [参考资源](#参考资源)

## 项目概览

**ODS**（Osmantic Deployment System，仓库：[Osmantic/ODS](https://github.com/Osmantic/ODS)）是 Osmantic 维护的全栈本地 AI 开源项目。它的前身叫 DreamServer，由 Light-Heart-Labs 组织开发，2026 年下半年项目转移至 Osmantic 并更名为 ODS，旧仓库地址会自动跳转到新仓库。当前版本是 v3.0.0 Pre-Release（2026-09-24 发布），官方定位是"在正式发布前接受公开测试与打磨"。

它解决的问题是真实的：本地跑 AI 不是一个模型的事，而是十几项服务的安装、配置与互联。ODS 把这一切封装成一条命令——Stars 6,969，Forks 988（2026-10-04 GitHub API 数据）。基础代码以 Apache 2.0 许可发布；其中 Pixel（自研自主 Agent）随仓库一起分发，但使用单独的 Pixel License for ODS，仅限在 ODS 内使用。

### 目标读者

- 想在本地跑 AI、不想折腾二十个配置文件的技术爱好者
- 对数据隐私有要求（不想把对话发给第三方）的开发者或小型团队
- 希望拥有 AI 基础设施主权（不按月付订阅）的个人或组织

### 本文覆盖范围与数据基准

本文覆盖项目定位、服务架构、安装流程、日常管理、扩展机制与硬件选型。不覆盖云端部署细节、模型微调方法、生产级高可用设计。

文中数据与命令核对至 2026-10-04，基于 v3.0.0 Pre-Release 和 main 分支文档（官方支持矩阵更新于 2026-09-23）。这个项目迭代很快，操作细节请以[官方 QUICKSTART](https://github.com/Osmantic/ODS/blob/main/ods/QUICKSTART.md) 为准。

## 为什么本地 AI 难用

你在 ChatGPT 或 Claude 里发的每一条消息，都会离开你的设备，落到别人控制的服务器上。轻量任务无所谓，但医疗、法律、商业策略这类对话，很多人本来就没打算让它们出办公室。

即使不在乎隐私，你也在按月付租金。每个 token 都计费，账单随用量增长。

而自建的全套体验并不便宜：把十几项开源服务逐一组装、写 Docker 配置、解决版本冲突、让它们互相发现，通常要花掉一两个周末。多数人撑到一半就回到订阅去了——不是能力问题，是时间不值当。

ODS 把这件事压缩成一条命令、十五到三十分钟。

## 服务架构详解

先给一张系统地图。ODS 的服务按职责分六层，核心编排由 `docker-compose.base.yml` 直接管理 7 个基础服务（推理、界面、Dashboard、模型路由、远程出口），其余服务以扩展清单（manifest）的形式放在 `ods/extensions/services/` 下，共 30 余个，按需启用。官方友好指南的表述是"约两打服务清单，外加若干主机辅助工具"。

| 层 | 服务 | 一句话职责 |
|------|------|------|
| 聊天推理 | Open WebUI、llama-server、LiteLLM、TEI Embeddings | 界面、推理、路由、向量化 |
| 语音 | Whisper、Kokoro | 听、说 |
| Agent | Pixel（首选）、Hermes、OpenClaw（弃用）、n8n、APE、OpenCode、Memory Shepherd | 自主执行、自动化、治理 |
| 知识搜索 | Qdrant、SearXNG、Perplexica、Brave Search | 检索自己的文档与全网信息 |
| 创意 | ComfyUI、Fooocus | 本地图片生成 |
| 隐私运维 | Privacy Shield、Dashboard、Dashboard API、Token Spy、Langfuse、Tailscale、ODS Proxy | 敏感信息剥离、监控、组网 |

这些服务通过内部 Docker 网络互联。下面按层展开。

### 聊天与推理层

| 服务 | 作用 |
|------|------|
| **Open WebUI** | 浏览器里的主界面，布局类似 ChatGPT，支持对话历史、文件上传、网页搜索、多语言。访问地址 `http://localhost:3000`。 |
| **Portal** | V3 新增的总入口（`http://localhost:3001/pixel`），聚合模型管理、服务状态、设置向导。Windows 安装器结束时自动打开的就是它。Open WebUI 仍然独立存在，两者是并行的两个界面。 |
| **llama-server** | 推理引擎，实际执行 LLM 的地方，基于 llama.cpp。逐词生成、流式返回。Docker 模式下容器内监听 8080，宿主机映射到 `127.0.0.1:11434`；macOS 上它脱离容器原生运行，用 Metal GPU 加速。 |
| **LiteLLM** | API 网关，扮演智能接线员：每个请求进来后由它决定路由到本地模型还是云端（OpenAI/Anthropic 等），支撑 local / cloud / hybrid 三种模式。 |
| **TEI Embeddings** | 文本向量化服务，为 RAG（检索增强生成，让 AI 基于你的文档回答问题）和搜索工作流提供 embedding 计算。 |

### 语音层

| 服务 | 作用 |
|------|------|
| **Whisper** | 语音转文字。接收语音输入、转写为文本后交给聊天界面，运行在本地硬件上，音频数据不出机器。 |
| **Kokoro** | 文字转语音，把 AI 的回复合成自然语音。与 Whisper 同时开启时，构成完整的语音对话闭环，可以完全不动键盘。 |

### Agent 与自动化层

这一层在 V3 变化最大。

| 服务 | 作用 |
|------|------|
| **Pixel** | V3 引入的自研自主 Agent，ODS 里的首选。在合格的 Linux 主机（Ubuntu 24.04/26.04、Debian 12，systemd）和 Apple Silicon Mac 上原生运行，直接嵌入 Open WebUI 和 Dashboard 工具栏——普通对话可以就地变成一次带工具调用的 Agent 执行。注意它用的是 ODS 专有许可，不是 Apache 2.0。 |
| **Hermes Agent** | 可移植的默认 Agent 和回退选择：在不满足 Pixel 条件的发行版、WSL1、原生 Windows 上由它顶上，通过带认证的代理访问。 |
| **OpenClaw** | 早期的自主 Agent 框架，仍可用但已标记弃用，不再是默认路径。 |
| **n8n** | 工作流自动化平台，400+ 集成（Slack、Email、数据库、API），可视化编辑器拖拽即成，本地 AI 作为决策大脑。 |
| **APE**（Agent Policy Engine） | 审计和治理自主 Agent 工具调用行为的策略引擎。 |
| **OpenCode** | 基于浏览器的 AI 编程助手，与本地推理栈集成。 |
| **Memory Shepherd** | 主机侧辅助工具，负责 Agent 记忆生命周期管理。 |

### 知识与搜索层

| 服务 | 作用 |
|------|------|
| **Qdrant** | 向量数据库，RAG 的存储与检索底座。喂入 PDF、报告、笔记后按语义检索而非关键词匹配——问"3 月份供应商合同做了什么决定"，它找的是语义相关内容，不是字面命中。 |
| **SearXNG** | 自托管元搜索，不追踪、不记录、无广告。AI 需要最新信息时把查询发给它，由它聚合 Google、DuckDuckGo、Wikipedia 等来源。 |
| **Perplexica** | 深度研究引擎，基于 SearXNG 做更深层的检索与归纳。 |
| **Brave Search** | 可选的 Brave Search API 集成（付费）。 |

### 创意层

| 服务 | 作用 |
|------|------|
| **ComfyUI** | 基于节点的图片生成界面，使用 SDXL Lightning。聊天界面可以直接发起图片生成请求，几秒出图，无需 Midjourney 或 DALL-E 订阅。 |
| **Fooocus** | V3 新增的备选图片生成前端，开箱即用取向。 |

### 隐私与运维层

| 服务 | 作用 |
|------|------|
| **Privacy Shield** | PII（个人身份信息）清洗代理，在 API 调用离开本机前自动剥离敏感信息。 |
| **Dashboard** | 实时状态面板：GPU 利用率、内存、服务健康、模型管理。 |
| **Dashboard API** | 为 Dashboard 提供数据的管理接口。 |
| **Token Spy** | Token 消耗监控，覆盖本地和经过代理的 LLM 请求。 |
| **Langfuse** | 可选的 LLM 可观测性与链路追踪平台。 |
| **Tailscale** | V3 新增的可选组网，把家里的 ODS 安全地暴露给外部设备。 |
| **ODS Proxy** | V3 新增的代理服务层。 |

## 一次语音提问如何流过系统

层级表是静态的，看一次真实请求怎么走，服务之间的配合才具体。

假设你对着麦克风说："帮我查一下这篇 PDF 里关于验收标准的部分，总结成三点。"

1. **Whisper** 把语音转成文字，交给 Open WebUI——相当于你"打"了这句话，音频没有离开过机器。
2. **Open WebUI** 组装上下文，把请求发给 **LiteLLM**。local 模式下它直接转给 **llama-server**。
3. **llama-server** 生成回答。因为问题指向你上传的 PDF，流程会先经过检索：**TEI Embeddings** 把问题向量化，**Qdrant** 按语义找出 PDF 里的相关段落，拼进上下文再生成——这就是 RAG。
4. 如果问题需要联网信息（本例不需要），请求会转给 **SearXNG** 聚合搜索结果后再回来。
5. 回答流式返回，**Kokoro** 合成语音播放。

整个链条里，只有第 4 步的搜索查询会出网（还是发给自托管的 SearXNG，由它匿名查询），模型推理和文档检索全部发生在本机。切到 hybrid 模式后，变化只有一处：LiteLLM 可能在本地繁忙时把第 3 步改走云端 API——这时 Privacy Shield 会在请求出门前清洗一遍 PII。

## 安装流程

### Linux / macOS 一行命令

```bash
curl -fsSL https://install.osmantic.com/ods.sh | bash
```

前置条件：Docker（含 Compose v2）已安装并运行；NVIDIA 卡需要 Container Toolkit，AMD Strix Halo 需要 ROCm，Intel Arc 需要 Intel 计算运行时；磁盘预留 40 GB 以上。

也可以手动安装：

```bash
git clone https://github.com/Osmantic/ODS.git
cd ODS
./install.sh
```

### Windows（PowerShell，走 WSL2）

V3 的 Windows 安装器改成了 WSL2 路线：在**普通** PowerShell 窗口（不要以管理员运行）粘贴官方安装块，安装器会检查磁盘空间（40 GB）和硬件虚拟化，按需帮你启用 WSL2、用 winget 装 Docker Desktop（中途重启一次）、装 Ubuntu 24.04，然后在 Ubuntu 内完成 ODS 安装（Pixel 路径，默认禁用 Hermes 与 OpenClaw），最后自动打开 Portal。

NVIDIA 显卡需要先把 Windows 驱动升到 570 或更新。完整命令块见[官方 QUICKSTART](https://github.com/Osmantic/ODS/blob/main/ods/QUICKSTART.md)；已有的原生 Windows 安装不会被自动迁移或删除，切换前先读[Windows Quickstart](https://github.com/Osmantic/ODS/blob/main/ods/docs/WINDOWS-QUICKSTART.md)。

### macOS（Apple Silicon）

前置条件：Apple Silicon（M1+）和正在运行的 Docker Desktop。

```bash
git clone https://github.com/Osmantic/ODS.git
cd ODS
./install.sh
```

llama-server 在 macOS 上原生运行（Metal GPU 加速），其余服务跑在 Docker 里，安装器会配置 LaunchAgent 开机自启。日常管理用 `./ods-macos.sh status` 一族命令。

### 云端模式（无 GPU 时可选）

```bash
./install.sh --cloud
```

全套服务照常启动，只有 LLM 推理换成 OpenAI/Anthropic 等远程 API。

### 常用安装旗标

| Linux/macOS | 作用 |
|------|------|
| `--all` | 启用推荐的全量栈 |
| `--voice` | 启用 Whisper + Kokoro 语音 |
| `--workflows` | 启用 n8n 工作流 |
| `--rag` | 启用 Qdrant 与 embeddings |
| `--tier 3` | 强制指定硬件/模型层级 |
| `--no-bootstrap` | 跳过快速启动，等完整模型下载完 |

### 卸载

Linux、macOS 或 Windows 的 Ubuntu 子系统内：

```bash
cd ~/ods
./ods-uninstall.sh --force
```

## 硬件自动检测与模型选择

安装器检测 GPU 类型和显存，按官方支持矩阵（2026-09-23 更新）匹配层级与模型：

| 层级 | 硬件 | 模型 | 显存要求 | 后端 |
|------|------|------|------|------|
| `NV_ULTRA` | NVIDIA 90 GB+（含 Grace Blackwell 统一内存） | Qwen3-Coder-Next | ≥ 90 GB | CUDA |
| `4` | NVIDIA 40 GB+ / 多卡 | Qwen3 30B A3B | ≥ 40 GB | CUDA |
| `3` | NVIDIA 20 GB+ | Qwen3 30B-A3B | ≥ 20 GB | CUDA |
| `2` | NVIDIA 12 GB+ | Qwen3.5 9B | ≥ 12 GB | CUDA |
| `1` | NVIDIA 4 GB+ | Qwen3.5 9B | ≥ 4 GB | CUDA |
| `0` | CPU / < 4 GB GPU | Qwen3.5 2B | 无要求 | CPU |
| `SH_LARGE` | AMD Strix Halo 90 GB+ 统一内存 | Qwen3-Coder-Next | ≥ 90 GB | ROCm |
| `SH_COMPACT` | AMD Strix Halo < 90 GB | Qwen3 30B A3B | 64 GB 统一内存起 | ROCm |
| `ARC` | Intel Arc ≥ 12 GB（A770、B580） | Qwen3.5 9B | ≥ 12 GB | SYCL |
| `ARC_LITE` | Intel Arc 6–11 GB（A750、A380） | Qwen3.5 4B | 6–11 GB | SYCL |
| `CLOUD` | 无本地 GPU | Claude（API） | — | LiteLLM |

两点值得注意。第一，Tier 1 的门槛降到了 4 GB 显存（仍跑 Qwen3.5 9B，靠 CPU 分担），4 GB 以下才落到 Tier 0 的 2B 模型——低配机器的可用性比大多数同类方案好。第二，Intel Arc 是当前唯一的实验性平台（Tier C）：安装器和运行时在 A770/A750 上端到端可用（SYCL，Intel 的 GPU 计算后端），但 ComfyUI 和 Whisper 暂无 Arc 加速。

AMD 离散显卡（Strix Halo 之外）官方标注"需要验证"，没有给出 tier 基准，选购前留意。

### Apple Silicon（统一内存）

硬件类别 `apple_silicon`（8 GB+ 统一内存）对应 Tier 2，`apple_silicon_pro`（36 GB+）对应 Tier 3；官方推荐 16 GB 以上统一内存、20 GB 以上磁盘。模型匹配沿用同一套 Qwen 层级逻辑，推理走 Metal。

### 模型家族选择

默认 `MODEL_PROFILE=qwen`。换成 Gemma 4 系列：

```bash
MODEL_PROFILE=gemma4 ./install.sh
```

`auto` 的语义是"硬件够格时优先 Gemma 4，入门与云端路径保留 Qwen 兜底"。也可以直接指定层级：

```bash
./install.sh --tier 3
```

## 引导模式（Bootstrap）

网络慢时的体验设计：安装器先下载一个能在两分钟内跑起来的小模型，让你立刻开始对话；完整模型在后台继续下载，完成后自动切换，全程无需干预。

它解决的是本地 AI 安装工具的通病——"等模型下完才能用"。十几个 GB 的下载被变成了一个可用的等待窗口。不想用这个行为可以加 `--no-bootstrap`。

## 日常管理命令

日常管理入口是 `ods` 命令（前身是 `dream`，更名后同步替换）：

| 命令 | 作用 |
|------|------|
| `ods status` | 查看所有服务状态、GPU 负载、健康状况 |
| `ods start` / `ods stop` / `ods restart` | 启动、停止、重启系统 |
| `ods list` | 列出可用服务，哪些在运行、哪些待开启 |
| `ods logs <服务名>` | 查看指定服务的实时日志，如 `ods logs whisper` |
| `ods doctor` | 诊断安装与服务问题 |
| `ods mode local` / `cloud` / `hybrid` | 切换运行模式 |
| `ods model list` / `ods model current` / `ods model swap <层级>` | 查看、切换模型 |
| `ods enable <服务>` / `ods disable <服务>` | 启用、禁用单个服务 |

多数时候你只需要开着 `http://localhost:3000` 聊天，`ods` 命令留给管理和排查的时刻。macOS 上另有一组 `./ods-macos.sh start|stop|restart|status|logs` 管理原生推理进程。

## 扩展系统：让服务成为一等公民

每个服务——官方内置还是自己加的——遵循同一个模式：独占一个文件夹，内含两份文件。

1. **manifest**：描述服务名称、端口、健康检查方式、依赖关系
2. **compose 配置**：告诉 Docker 如何运行这个服务

系统启动时扫描所有服务目录，读取 manifest 并纳入统一管理：CLI 补全、Dashboard 展示、健康检查覆盖，不需要在任何中心配置文件里注册。加一个有 Docker 镜像的新服务，把文件夹放进 `ods/extensions/services/`、运行 `ods enable` 即可；禁用（`ods disable <服务>`）本质上是重命名一个标记文件，可逆、即时生效。也可以在 `docker-compose.override.yml` 里把某个服务标记为 disabled，V3 的核心 compose 就是这么管理可选服务的。

这个设计的关键在于：内置服务和自定义服务是平等的。你自定义的服务在 Dashboard 里和核心服务长得一样，在 CLI 里享有同样的补全。

## 三种运行模式详解

### local 模式

默认模式。全部 LLM 请求由本地 llama-server 处理，数据不出机器，断网也能用。适合隐私要求严格的场景。

### cloud 模式

```bash
./install.sh --cloud
```

没有合适的 GPU 或不想本地推理时用。与 local 模式的差别只在推理路由——聊天界面、语音、RAG、工作流仍然全部在本地运行，AI 能力来自远程 API。官方支持矩阵把"无本地 GPU + Claude API"列为正式的 CLOUD 层级。

### hybrid 模式

本地优先，云端兜底。LiteLLM 检测本地服务状态：正常时走本地；繁忙或不可用时自动转发云端。用户无感知。

本地 GPU 偏弱又不想放弃隐私时，这个模式最有价值：日常轻任务走本地，复杂任务走云端，边界对用户透明。

## API 兼容性

llama-server 提供 OpenAI 兼容 API。任何原本指向 ChatGPT 的工具——开发者工具、自动化脚本、第三方聊天客户端——改一个地址参数就能指向本地 ODS，代码不用动。V3 又在前面加了认证网关（ODS Proxy/LiteLLM），Agent 走模型时同样从这条路过。

## 硬件需求与选型建议

### 最低配置（体验）

- 8 GB RAM
- 无独显可纯 CPU 运行（Tier 0，Qwen3.5 2B，速度有限）
- 40 GB 以上可用磁盘（模型 + 容器镜像；macOS 官方口径 20 GB 起）

### 推荐配置（日常）

- 16 GB+ RAM
- 12 GB+ 显存（如 RTX 3060 12GB）或 16 GB+ 统一内存的 Apple Silicon
- 跑 Qwen3.5 9B，覆盖大多数日常对话与写作

### 高性能配置（专业级）

- 32 GB+ RAM
- 20–40 GB 显存（RTX 3090/4090、A6000）跑 Qwen3 30B-A3B（MoE，混合专家架构，推理成本低但需要装得下权重）；90 GB+ 走 NV_ULTRA 的 Qwen3-Coder-Next
- 更长上下文与更复杂推理

### 存储

模型文件和 Docker 镜像都吃磁盘，首装前预留足量空间。用 SSD，机械硬盘会拖慢推理响应。

## 与同类项目对比

| 特性 | ODS | Ollama | LM Studio |
|------|------|------|------|
| 定位 | 全栈 AI 服务器（推理+聊天+语音+Agent+工作流+RAG+图片） | LLM 推理引擎 | 桌面端 AI 聊天客户端 |
| 服务数量 | 核心 7 项 + 30 余个可启用扩展 | 单一推理服务 | 单一桌面应用 |
| 安装 | 一条命令自动编排 | 相对简单 | 简单 |
| 扩展性 | manifest 驱动，任意 Docker 服务 | 模型管理为主 | 应用层面定制 |
| 工作流自动化 | 内置 n8n（400+ 集成） | 无 | 无 |
| RAG | Qdrant + 完整 embedding 流水线 | 需自行搭建 | 无 |
| 语音对话 | Whisper + Kokoro 完整闭环 | 无 | 无 |
| 隐私 | 本地优先，含 PII 清洗代理 | 本地 | 本地 |

Ollama 和 LM Studio 把"本地跑模型"这件事做得足够好，如果你要的只是跑模型，用它们更轻。ODS 的差异在于"跑完模型之后"：对话、语音、自动化、读自己的文档、生成图片，这些环节的互联是预配置好的，不需要你自己处理服务发现和端口映射。

## 适用场景与采用建议

**很适合：**

- 隐私敏感场景（医疗、法律、财务数据不出本地网络）
- 团队内部 AI 工具（不用为每个成员付月费）
- 需要本地 RAG（让 AI 基于自有文档回答）
- 语音 AI（实时语音对话，完全离线）
- 工作流自动化（n8n 400+ 集成，本地 AI 做决策大脑）
- 想横向比较模型（一条命令切换层级与家族）

**限制与注意事项：**

- 依赖 Docker，熟悉 Docker 生态会顺利很多
- 完整安装磁盘占用不小（模型 + 镜像）
- n8n、ComfyUI、RAG 初次配置有学习曲线
- 30B MoE 档位需要高端显卡
- **当前是 V3 Pre-Release**：官方明确说明完整机群资格验证尚未完成，main 分支持续合入修复。追求稳定的生产环境，建议等正式发布，或按官方建议固定 tag 并保留验证凭据
- Pixel 的 ODS 专有许可与主仓库的 Apache 2.0 不同，二次分发前需要分别确认

按场景给个采用顺序：手头有 12 GB+ 显卡、36 GB+ 的 Mac 或 Strix Halo，现在就可以装来日常用，遇到问题靠 Discord 和 Issues 反馈；只有核显或老机器，用 `--cloud` 模式先把全栈体验跑起来，硬件到位再切本地；只想本地跑个模型对话，选 Ollama 或 LM Studio，ODS 对你是杀鸡用牛刀；计划放进生产环境，等 V3 正式发布后再评估。

## 常见问题

### 没有合适的 GPU 能跑吗？

能，但纯 CPU 推理（Tier 0）速度有限，只适合体验。更好的路径是 `./install.sh --cloud`：功能栈完整，推理由云端 API 承担。

### 如何更新？

进入安装目录执行 `ods-update.sh`，或 `git pull` 后重跑 `./install.sh`。更新前看一下 [GitHub Releases](https://github.com/Osmantic/ODS/releases) 和[源码更新说明](https://github.com/Osmantic/ODS/blob/main/ods/docs/SOURCE-UPDATES.md)；需要可复现环境时，固定 tag 或经审计的 commit。

### 可以只运行部分服务吗？

可以。V3 的核心服务默认全量启动，禁用单个服务用 `ods disable <服务>`，或在 `docker-compose.override.yml` 里标记 disabled。历史版本的 compose profiles（voice、workflows 等）已移除。

### 支持多用户吗？

支持。项目提供[多用户设置文档](https://github.com/Osmantic/ODS/blob/main/ods/docs/MULTI-USER-SETUP.md)，企业级 SSO（经由 Hermes）也有专门文档。个人使用默认单用户即可。

### 遇到问题哪里求助？

GitHub Issues 提交问题，Discord 社群（[discord.gg/qGVygYada3](https://discord.gg/qGVygYada3)）交流经验。`ods doctor` 是排查安装问题的第一站。项目活跃度高，文档没覆盖的问题直接提 Issue。

## 总结

ODS 没有发明新技术，它做的是把十几种成熟工具的拼图变成一条命令可运行的系统：硬件检测决定模型档位，引导模式消灭下载等待，manifest 驱动的扩展系统让内置与自定义服务平权，LiteLLM 把本地与云端路由变成一个可切换的策略问题。

它也不是没有代价。系统复杂度意味着更长的安装时间和更大的磁盘占用；V3 Pre-Release 意味着现在上车要容忍偶发问题；Pixel 的专有许可让"整个项目完全开源"这个说法不再严格成立。

判断很直接：如果你要的是完整的本地 AI 工作站而不是单一推理引擎，ODS 是当前把门槛做得最低的方案之一；如果你只要跑模型，Ollama 更合适；如果把稳定性排在第一位，把 ODS 放进观察清单，等 V3 正式发布。

## 练习与自测

### 练习 1：跑通第一个对话

1. 用一行命令安装 ODS（参考「安装流程」）
2. 打开 `http://localhost:3001/pixel` 确认 Portal 就绪，再到 `http://localhost:3000` 开始对话
3. 上传一个 PDF，问"这个文档里讲了什么？"，观察 RAG 链路
4. 在设置里开启语音，用麦克风对话，确认 Whisper + Kokoro 全链路工作

预期：30 分钟内完成从安装到第一个带 RAG 的对话。

### 练习 2：切换运行模式，观察差异

1. 分别执行 `ods mode local`、`ods mode cloud`、`ods mode hybrid`
2. 每个模式下发同一条消息，记录响应速度、是否需要联网、模型归属
3. 断网后测试 local 模式是否照常工作

### 练习 3：添加和禁用服务

1. `ods list` 查看所有可用服务
2. 启用 ComfyUI（`ods enable comfyui`），生成一张图片
3. 禁用一个不需要的服务（`ods disable <服务名>`）
4. `ods status` 确认状态变化，再恢复它

### 自测问题

1. 引导模式（Bootstrap）解决了什么问题？`--no-bootstrap` 适合什么场景？
2. 三种运行模式各自适合什么场景？高端 GPU 团队想要突发负载时的云端兜底，选哪种？
3. 扩展系统如何做到"内置服务和自定义服务平等"？添加自己的服务需要改中心配置文件吗？
4. Pixel、Hermes、OpenClaw 三者的关系是什么？在原生 Windows 上默认由谁承担 Agent 职责？
5. 你的机器是 8 GB 显存，默认会落在哪个 Tier、跑哪个模型？为什么这个档位不建议跑 30B MoE？

## 进阶路径

### 阶段一：基本可用（1–3 天）

- 完成安装，跑通第一个对话
- 用 `ods status` 认识每个服务的职责，找到自己所在的 Tier
- 切换一次模型（比如从 Qwen 换到 Gemma 4）

### 阶段二：进阶使用（1–2 周）

- 配置 hybrid 模式并压测本地/云端切换行为
- 用 n8n 搭一条真实自动化（比如会议纪要自动入库）
- 开启 Token Spy 与 Langfuse，建立消耗与链路基线
- 远程访问场景配置 Tailscale，避免直接暴露端口

### 阶段三：深度定制（1 个月+）

- 通读[扩展系统文档](https://github.com/Osmantic/ODS/blob/main/ods/docs/EXTENSIONS.md)，给 ODS 加一个自己的服务
- 在 Open WebUI 里定制系统提示词，固化团队工作流
- 有能力时给 [Osmantic/ODS](https://github.com/Osmantic/ODS) 提 Issue 或 PR——Pre-Release 阶段的反馈对项目最有价值

### 阶段四：规模化（持续）

- 多成员使用时参考多用户文档统一部署与权限
- 监控 token 消耗、GPU 利用率与服务可用性
- 定期跟进上游更新，固定验证过的版本基线（参见 KNOWN-GOOD-VERSIONS 文档）

## 参考资源

- GitHub 仓库：[Osmantic/ODS](https://github.com/Osmantic/ODS)
- 快速开始：[QUICKSTART.md](https://github.com/Osmantic/ODS/blob/main/ods/QUICKSTART.md)
- 工作原理友好指南：[HOW-ODS-SERVER-WORKS.md](https://github.com/Osmantic/ODS/blob/main/ods/docs/HOW-ODS-SERVER-WORKS.md)
- 支持矩阵与硬件层级：[SUPPORT-MATRIX.md](https://github.com/Osmantic/ODS/blob/main/ods/docs/SUPPORT-MATRIX.md)
- Pixel 许可与边界：[PIXEL.md](https://github.com/Osmantic/ODS/blob/main/ods/docs/PIXEL.md)
- V3 发布说明：[RELEASE_NOTES_3.0.0.md](https://github.com/Osmantic/ODS/blob/main/ods/docs/RELEASE_NOTES_3.0.0.md)
- Discord 社区：[discord.gg/qGVygYada3](https://discord.gg/qGVygYada3)
- 视频演示：[YouTube 演示视频](https://youtu.be/nO8xFNHX-HA)
