---
title: "Meetily 解读：把「会议数据不出本机」做成一键安装的桌面应用，v0.4 起连总结模型都内置了"
date: 2026-07-04T21:16:32+08:00
lastmod: 2026-10-04T00:00:00+08:00
slug: zackriya-solutions-meetily-privacy-first-meeting-assistant-guide
github_repo: "Zackriya-Solutions/meetily"
source_key: "gh:Zackriya-Solutions/meetily"
description: "Meetily（Zackriya-Solutions/meetily）是隐私优先的开源 AI 会议助手：录音、实时转写在本机完成，总结可选内置 GGUF 模型、Ollama、OpenAI/Claude/Groq/OpenRouter 或自建端点。基于 Tauri + Rust，Whisper 12 档模型与 Parakeet v3 双转写引擎，数据存本地 SQLite。"
draft: false
categories: ["技术笔记"]
tags: ["Tauri", "Whisper", "Parakeet", "本地AI", "Rust", "llama.cpp"]
---

## 快速信息卡

| 属性 | 值 |
|------|-----|
| **GitHub Stars** | 31,423（2026-10-04 读数） |
| **GitHub Forks** | 3,435 |
| **主要语言** | Rust |
| **开源协议** | MIT |
| **桌面框架** | Tauri（Rust 后端 + Next.js 前端） |
| **当前版本** | v0.4.1（2026-09-12） |
| **转写引擎** | Whisper（whisper-rs，12 档模型）/ Parakeet（ONNX，默认 0.6B-v3-int8） |
| **总结提供方** | 内置 GGUF 引擎、Ollama、OpenAI、Claude、Groq、OpenRouter、自定义 OpenAI 兼容端点 |
| **项目定位** | 隐私优先的本地 AI 会议助手 |

---

# Meetily 解读：把「会议数据不出本机」做成一键安装的桌面应用，v0.4 起连总结模型都内置了

会议转写工具已经不少，但几乎默认把音频传上云端。Meetily 走的是另一条路：录音、实时转写全部跑在用户自己的电脑上；总结这一步，现在连 Ollama 都不用装——应用内置了一个基于 llama.cpp 的推理引擎和 4 款量化模型，选「Built-in AI」就能完全离线出纪要。录音、转写文本、总结结果都存进本地 SQLite。对律师、医生、合规团队这类对会议内容敏感的人群，这条路线比纯 SaaS 实际得多。

有个值得注意的时间差：README 顶部至今还写着「说话人分离计划 6 月中旬上线 PRO」，而 PRO 官网已经挂着 v1.11.0 的说话人分离功能介绍。仓库的文档叙事滞后于代码，本文以代码和官方页面为准，把能验证的事实拆出来。

## 它到底解决什么问题

Meetily 的 README 把痛点拆成三条：

1. **数据隐私**：援引 IBM 2024 报告，平均单次数据泄露成本 440 万美元；到 2025 年欧盟累计开出 58.8 亿欧元 GDPR 罚单；加州当年发生 400 多起非法录音诉讼
2. **成本控制**：云端转写按分钟计费，重度用户每月开销不小
3. **厂商锁定**：主流 SaaS 把数据存在自家服务器，存储位置和保留期限由厂商说了算

针对这三条，Meetily 给出三层解法：

- **本地转写**：Whisper / Parakeet 模型在用户机器上跑，音频不离开设备
- **本地总结**：内置模型或 Ollama 不花钱，也没有按分钟计费
- **本地存储**：录音、转写、总结都写入本地 SQLite，没有云端副本

难点在于把这三条装进一个「开箱即用」的桌面应用（macOS / Windows 安装包，Linux 自构建），而不是让用户自己跑 Docker、配 GPU 服务。这个约束直接决定了它的技术栈选择——实际上 Meetily 早期版本就是 FastAPI 加 Docker 的服务端架构，后来才整个迁进 Tauri，旧后端现在还留在仓库里，这点在架构一节展开。

## 整体架构：Rust 后端，五块组件

Meetily 是单进程自包含的桌面应用：Tauri 负责窗口和系统事件，Rust 承担核心逻辑，Next.js 前端负责界面。官方架构文档（docs/architecture.md）把核心拆成五块组件，各有单一职责：

| 组件 | 职责 |
|------|------|
| Tauri Core | 管理窗口与事件，通过命令系统把 Rust 能力暴露给前端 |
| Audio Engine | 采集麦克风与系统音频，做混音与 ducking |
| Transcription Engine | 调用本地 Whisper / Parakeet 模型实时转写，支持 GPU 加速 |
| Database | 本地 SQLite，存会议元数据、转写文本与总结 |
| Summary Engine | 调用 LLM 生成结构化总结，内置引擎、本地 Ollama 或远程 API |

这份文档说的「Rust 核心」对应代码里的 `frontend/src-tauri/src/`：`audio`、`whisper_engine`、`parakeet_engine`、`database`、`summary` 各占一个模块，Anthropic、Groq、OpenAI、OpenRouter、Ollama 五家 API 客户端也各自一个目录，边界很清楚。

仓库顶层还有个容易误读的 `backend/` 目录——Python FastAPI、Docker Compose、独立 whisper-server 全在里面。它不是现行架构的一部分：`backend/README.md` 自称 "Legacy Backend Archive"，明确写着当前支持的应用路径不再使用这套后端，这些文件「仅供历史参考与迁移上下文，不应用于新装、生产部署或对受支持应用的安全评估」。早期 Meetily 就是这套服务端架构，v0.x 迁移到自包含 Tauri 之后，旧代码留在了仓库里。看到有人还在按 Docker 方式部署 Meetily，多半是照着旧教程走的。

前端不直接接触音频和模型推理，一切通过 Tauri Commands 走 Rust。数据流向是一条单向链：

```text
[Audio Engine]        采集麦克风 + 系统音频（ducking 防回授）
      │
      ▼
[Transcription Engine]   Whisper / Parakeet 本地实时转写（GPU 加速）
      │
      ▼
[SQLite Database]      会议元数据、转写文本、总结
      ▲
      │
[Summary Engine]       内置 GGUF 引擎 / Ollama / 远程 API
      ▲
      │
[Next.js 前端]        界面操作、展示与配置（经 Tauri Commands 调后端）
```

转写和总结是两条相对独立的链路，中间由 SQLite 承接：转写引擎写入文本，总结引擎读取文本产出纪要。这种拆分让「换转写引擎」和「换总结模型」互不影响，也是后面几节讨论引擎和提供方的基础。

## 一次会议如何流过系统

把模块串成一个具体场景：你打开 Meetily，点开始，和客户开了一小时会。

1. **采集**：Audio Engine 同时捕获麦克风和系统音频（你的声音 + 对方电脑的播放声），做混合与 ducking，避免扬声器回授，并做 clipping 预防。
2. **转写**：音频按片段交给转写引擎，Whisper 或 Parakeet 在本地把语音转成文字；GPU 可用时走 Metal / CUDA / Vulkan 加速。文字实时出现在前端面板。语音活动检测（VAD）负责切分片段——v0.4.1 专门修过一个把连续语音切碎成 4 秒以下小请求、导致各引擎幻觉文本的问题。
3. **落库**：转写文本、时间戳、会议元数据写入本地 SQLite。
4. **总结**：会议结束，Summary Engine 把转写文本交给选定的 LLM——内置引擎或 Ollama 全程不出网，OpenAI / Claude / Groq / OpenRouter 走远程——按内置模板生成结构化纪要。
5. **编辑与导出**：在前端编辑器里改总结，然后按需导出。

整个过程里，只有第 4 步选了远程模型时转写文本会出网；音频从头到尾不离开本机。这也是 Meetily 与云端 SaaS 最本质的差别。

## 引擎选型：Whisper 与 Parakeet 的差异

Meetily 提供两套本地转写引擎，都通过模型目录内置在应用里：

| 引擎 | 底座 | 模型目录 | 定位 |
|------|------|----------|------|
| Whisper | whisper.cpp 的 Rust 绑定 whisper-rs | 12 档：tiny 到 large-v3，f16 与 Q5 量化各半，从 31 MB 的 tiny-q5_1 到 2,951 MB 的 large-v3 | 多语种、档位齐全，中英混合会议的首选 |
| Parakeet | ONNX Runtime | 默认 parakeet-tdt-0.6b-v3-int8，约 0.6B 参数的量化版 | 欧洲语系低延迟实时转写 |

Whisper 侧默认模型是 `large-v3-turbo`（1,549 MB），配置常量里标注它是「精度与速度的推荐平衡点」。12 档模型全部从 HuggingFace 的 `ggerganov/whisper.cpp` 官方仓库下载，文件就是标准的 ggml 格式，意味着你在别处下载的同款模型也能放进目录直接用。

Parakeet 侧有个常见误解值得纠正：不少资料（包括本文旧版）说它「以英文为主」。实际默认的 parakeet-tdt-0.6b-v3 是 NVIDIA 的多语言模型，覆盖英语、西语、法语、德语、俄语等 25 种欧洲语言——但不含中文。所以「中英混合会议优先 Whisper」这个结论依然成立，理由不是 Parakeet 只会英语，而是它的语言表里没有中文。模型文件从项目自建镜像（meetily.towardsgeneralintelligence.com）下载，v2 版走 HuggingFace 上 istupakov 的转换仓库，README 致谢栏也注明了这层关系。

仓库的 GitHub 描述称其 Parakeet / Whisper 实时转写「比常规方案快 4 倍」。这是官方宣传口径，没有公开的对照 benchmark 说明「常规方案」是什么、测的哪段链路，把它理解为「流式处理 + GPU 加速带来的体感提升」比当作精确倍数更合适。自己验证的办法也简单：同一台机器上分别跑内置引擎和云端 API 记一次延迟。

实际使用有三个细节：

1. **模型都在本地**：两套引擎的模型文件在用户机器上加载（README 明确「转写模型、录音、转写文本都留在机器上」），不经过任何云端转写接口。
2. **Import & Enhance（Beta）**：把历史录音拖进应用，可以换模型或换语言重新转写，全部本地处理。
3. **引擎切换不掉数据**：重转写走的是同一套落库链路，旧记录保留，新结果覆盖。

## 音频捕获与 GPU 加速

音频采集由 Audio Engine 负责，README 明确支持三种形态：

- 纯麦克风捕获
- 麦克风 + 系统音频同时捕获，带智能 ducking（压低系统音量避免回授）和 clipping 预防
- 一次会议同时录下「你的声音 + 你听到的播放声」，合成一份待转写音轨

GPU 加速的情况按「安装包还是源码构建」分三种，不能一概而论：

| 形态 | 加速情况 |
|------|----------|
| macOS 安装包 | Metal + CoreML 自动启用，无需配置 |
| Windows 安装包 | Whisper 以 Vulkan 构建打包，要求支持 AVX2 的 x64 CPU（不要求 AVX-512）；README 特别注明标准安装包不会自动选 CUDA |
| Linux / 任何源码构建 | 构建脚本自动探测，CUDA / ROCm / Vulkan / OpenBLAS 按优先级选择，探测不到就纯 CPU |

「自动」的实现值得看一眼，因为它是源码构建体验的关键。构建脚本 `build-gpu.sh` / `dev-gpu.sh` 先定位 `package.json`，再运行 `scripts/auto-detect-gpu.js`（或直接读 `TAURI_GPU_FEATURE` 环境变量）探测硬件，然后按探测结果编译 `llama-helper` 这个 sidecar 二进制，放进 `src-tauri/binaries` 交给 Tauri 打包。探测优先级是 NVIDIA CUDA → AMD ROCm（hipblas）→ Vulkan → OpenBLAS → 纯 CPU。

探测逻辑里藏着一条重要边界：驱动装了不等于加速生效。`nvidia-smi` 能看到卡但没装 CUDA toolkit（`nvcc` 不可用），脚本直接回退 CPU 并打印原因；Vulkan 同理，`vulkaninfo` 存在还不够，`VULKAN_SDK` 和 `BLAS_INCLUDE_DIRS` 两个环境变量都设了才算数。BUILDING.md 的故障排查表把每种「有硬件没加速」的场景都列了对应办法，也可以用 `TAURI_GPU_FEATURE=cuda`（或 `vulkan`、`hipblas`）强制指定。

顺带说明一个易混点：这个 `llama-helper` sidecar 管的不是转写，而是总结——它是总结引擎的本地 LLM 推理进程，下一节展开。转写走的是 whisper-rs（whisper.cpp 的 Rust 绑定）和 ONNX Runtime 两条完全独立的路径。

## 构建链路与平台支持

### 直接安装

- **Windows**：从 Releases 下载 `meetily_0.4.1_x64-setup.exe`（或 MSI），图形化安装
- **macOS**：从 Releases 下载 `meetily_0.4.1_aarch64.dmg`（仅 Apple Silicon 版本）
- **Linux**：无预编译包，从源码构建

### 从源码构建

README 的快速开始给的是：

```bash
git clone https://github.com/Zackriya-Solutions/meeting-minutes
cd meeting-minutes/frontend
pnpm install --frozen-lockfile
./build-gpu.sh
```

两个细节：克隆地址是 `meeting-minutes`——README 的克隆与发布链接一直指向这个旧仓库名，与当前展示仓库 `meetily` 不同（GitHub 会自动重定向，不影响使用）；`pnpm install` 后面带 `--frozen-lockfile`，BUILDING.md 要求 pnpm 钉在 9.15.9，锁文件与依赖集合保持一致是官方构建的前提。

三端依赖与命令（来自官方 BUILDING.md）：

| 平台 | 依赖 | 构建命令 |
|------|------|----------|
| Linux | build-essential、cmake、git | `./dev-gpu.sh`（开发）/ `./build-gpu.sh`（生产） |
| macOS | cmake、node、pnpm（Homebrew） | `pnpm tauri:dev` / `pnpm tauri:build` |
| Windows | Node.js、Rust、pnpm 9.15.9、Visual Studio Build Tools（C++ 工作负载）、CMake | `pnpm install --frozen-lockfile` 后 `pnpm tauri:dev` / `pnpm tauri:build` |

Linux 构建产物是 `Meetily_<版本>_amd64.AppImage`，路径在 `src-tauri/target/release/bundle/appimage/`。Windows 源码构建默认 CPU-only，想启用加速按上一节的探测逻辑装好对应 SDK；面向他人的分发构建走官方 CI workflow，会启用 Vulkan 并把 Rust 目标钉在 x86-64-v2。

## 总结提供方：七条路，内置引擎是底线

转写是本地，总结这一步的选择比 README 宣传的更多。代码里的 `LLMProvider` 枚举列了七种：

| 提供方 | 模型位置 | 说明 |
|--------|----------|------|
| Built-in AI | 用户本机（应用内置） | llama.cpp 推理引擎 + 4 款内置 GGUF 模型，不依赖任何外部服务 |
| Ollama | 用户本地 | README 推荐的默认选项，无 API 费用，全程不出网 |
| OpenAI | OpenAI API | 官方 API 直连 |
| Claude | Anthropic API | 远程高质量总结 |
| Groq | Groq API | 低延迟推理 |
| OpenRouter | 第三方聚合 | 一个入口切换多家模型 |
| 自定义 OpenAI 兼容端点 | 用户自己的部署 | 接入内网 vLLM、TGI、LM Studio、LocalAI 等，不改代码 |

内置引擎（代码里叫 BuiltInAI，也接受 `local-llama` 这个别名）是最容易被忽略的一条：README 的功能清单完全没提它，但代码里是一条完整链路——`llama-helper` sidecar 以 JSON over stdin/stdout 的协议与 Rust 主进程通信，支持 temperature、top_k、top_p、各类惩罚系数和停止符；内置 4 款模型目录：

| 模型 | 量化 | 体积 | 上下文 | 官方定位 |
|------|------|------|--------|----------|
| Qwen 3.5 2B | Q4_K_M | 1,221 MB | 32K | Balanced |
| Qwen 3.5 4B | Q4_K_M | 2,614 MB | 32K | High Quality |
| Gemma 3 1B | Q8_0 | 1,019 MB | 32K | Fast |
| Gemma 3 4B | Q4_K_M | 2,374 MB | 32K | Balanced |

每款模型带预调的采样参数（Qwen 用「总结特调」档：temperature 0.5、轻度重复惩罚；Gemma 沿用其 instruct 推荐档），提示词模板也按模型家族分开。实际意义是：一台没装 Ollama 的干净电脑，装上 Meetily、下载一个 1 GB 左右的模型，就能获得完全离线的会议纪要——这是「隐私优先」从口号变成默认体验的关键一步，也是它与「套壳 API」类会议工具的真实差距。

远程提供方按 README 的口径，Ollama（本地）仍是推荐默认，远程几家按质量和延迟自选。自定义端点作为独立配置项开放，企业可以把私有 LLM 服务直接接进来。总结产物是结构化纪要：后端内置一套 prompt 模板，不绑定具体模型；社区版只有默认模板，多模板和自定义模板属 PRO（见下一节）。模型越强，结构化程度越好。

## 适用边界与限制

| 维度 | 社区版现状 | 边界 |
|------|-----------|------|
| 操作系统 | macOS / Windows 安装包，Linux 自构建 | 无 iOS / Android 端 |
| 会议接入 | 捕获麦克风 + 系统音频 | 不「加入」会议；Zoom / Meet 里需手动共享扬声器/系统声音，它才能采集到对方 |
| 转写语言 | 多语种自动检测 | Whisper 覆盖最广；Parakeet v3 支持 25 种欧洲语言、不含中文；中英混合优先 Whisper |
| 离线使用 | 支持 | 转写全本地；总结选内置引擎或 Ollama 即可完全离线 |
| 说话人分离 | 不支持 | 已在 PRO v1.11.0 上线（实时标注 + 导入音频重转写，设备端运行） |
| 高级导出 | 基础导出 | PDF / DOCX / Markdown 格式化导出属 PRO |
| Windows GPU 加速 | 安装包为 Vulkan 构建（AVX2 必须） | PRO 官网把「用 NVIDIA 卡加速 Windows 转写」列为 PRO 功能 |
| MCP / CLI / Webhooks | 不支持 | PRO 功能：让 Claude、Cursor 等 MCP 助手查询会议，脚本经签名 webhook 响应总结完成 |
| 日历与自动入会 | 不支持 | PRO 路线图包含 |

## Meetily PRO 与社区版的边界

Meetily 采用「开源社区版 + 闭源商业版」双轨制，官网的对比表把差异列得很直白：

- **社区版（MIT）**：永久免费开源，含本地转写、AI 总结（任意 provider）、默认总结模板；README 明确 "free & open source forever"。
- **PRO 版**：独立代码库（版本号自成体系，当前 v1.11.0），定价 $10/用户/月（年付，官网标注较原价 $25/月直降 60%），14 天免费试用。功能差异：更高准确度的转写模型、6 个内置 + 自定义总结模板、PDF / DOCX / Markdown 格式化导出、说话人分离（实时标注「谁说了什么」，改名一次全稿同步，支持合并重复说话人）、自动检测并加入会议、日历集成、面向 2–100 人团队的自托管部署、GDPR 审计支持，以及 MCP / CLI / webhook 集成。

PRO 与社区版不是同一代码库的功能开关，而是两套代码。说话人分离就是现成的例子：PRO v1.11.0 已经上线，社区版对比表里对应行仍是 "No"——PRO 的新能力不会自动回流。README 里「说话人分离计划 6 月中旬上线」的表述停留在 6 月，直到 10 月初都没更新，查证 PRO 功能状态以官网对比表为准。100 人以上或需要托管合规方案的组织，官方引导转向 Meetily Enterprise（定制报价，含组织级模板库和 SLA）。

## 常见问题与故障排查

### Q: 转写到底在本地还是云端？

本地。Whisper / Parakeet 模型跑在用户机器上，音频不离开设备。只有总结环节选了远程模型（OpenAI / Claude / Groq / OpenRouter）时，转写文本会发往对应 API；选内置引擎或 Ollama 则完全不出网。

### Q: 不想装 Ollama，还能本地总结吗？

能。总结提供方选 Built-in AI，按提示下载一款内置模型（1–2.6 GB）即可，推理由应用自带的 llama-helper 引擎完成。这是 v0.4 系列内置的能力，README 没有宣传但代码和设置界面里都在。

### Q: 怎么接入公司内部的私有大模型？

在总结配置里填自定义 OpenAI 兼容端点，指向你的 vLLM、TGI、LM Studio、LocalAI 等部署即可，不需要改 Meetily 代码。

### Q: Windows 上 GPU 加速怎么开？

分三层看：官方安装包自带 Vulkan 构建的 Whisper（要求 AVX2 的 x64 CPU），开箱即用但不含 CUDA；源码构建默认 CPU-only，装好 CUDA toolkit 后 `TAURI_GPU_FEATURE=cuda` 可强制启用；官网把「Windows 上用 NVIDIA 卡加速」的完整支持列为 PRO 功能。三种路径的边界在 README、BUILDING.md 和 PRO 对比表里各说了一部分，合在一起才是全貌。

### Q: Linux 没有预编译包吗？

没有，需从源码构建，产物是 AppImage。依赖 build-essential、cmake、git，构建命令 `./build-gpu.sh`，脚本会自动探测 GPU 并选择加速方式。

## 总结

Meetily 的价值不在「多一个会议转写工具」，而在把「会议数据留在本机」做成一键安装的桌面应用——v0.4 内置本地总结引擎之后，这条路线第一次做到了零外部依赖。它适合：

- **律师、医生、顾问**：客户对话必须本地处理
- **企业合规团队**：会议内容需要审计但不上公网
- **重度会议用户**：会议量大，不想按分钟被云端 SaaS 计费

不适合：

- 需要说话人分离的多人会议（PRO v1.11.0 已有，社区版没有）
- 需要移动端录音（只有桌面端）
- Linux 用户不接受源码编译（无预编译包）
- 想要 MCP 助手查会议、脚本自动化（PRO 独占）

一个务实的采用顺序：个人或小团队、内容敏感，直接上社区版 + 内置引擎或本地 Ollama，全程不出网；要 PDF/DOCX 导出、说话人分离、MCP 集成或 Windows 上的 NVIDIA 加速，PRO 每用户每月 10 美元起，先试 14 天再决定；100 人以上或需托管合规方案，看 Enterprise。在「数据不出本机 + 不需要会议平台自动接入」的组合里，Meetily 是开源生态中少数的成熟选择之一。

## 参考资料

- 仓库：https://github.com/Zackriya-Solutions/meetily（克隆与发布链接指向旧名 meeting-minutes，自动重定向）
- 官网与 PRO 对比表：https://meetily.ai 、https://meetily.ai/pro/
- 架构文档：`docs/architecture.md`（仓库内）
- 构建文档：`docs/BUILDING.md`、`docs/building_in_linux.md`、`docs/GPU_ACCELERATION.md`（仓库内）
- 遗留后端说明：`backend/README.md`（仓库内，Legacy Backend Archive）
- 相关项目：[whisper.cpp](https://github.com/ggerganov/whisper.cpp)、[Parakeet ONNX](https://huggingface.co/istupakov/parakeet-tdt-0.6b-v3-onnx)、[NVIDIA parakeet-tdt-0.6b-v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3)、[Screenpipe](https://github.com/mediar-ai/screenpipe)、[transcribe-rs](https://crates.io/crates/transcribe-rs)
