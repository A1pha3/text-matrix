---
title: "Meetily：隐私优先的AI会议助手，本地实时转录与总结"
date: 2026-08-04T03:20:00+08:00
slug: "meetily-privacy-first-meeting-assistant"
github_repo: "Zackriya-Solutions/meetily"
description: "Meetily 是一款开源的隐私优先AI会议助手，基于 Rust 构建，支持实时转录、说话人识别和AI总结，所有数据本地处理无需云服务。"
draft: false
categories: ["技术笔记"]
tags: ["会议助手", "隐私", "Rust", "AI转录", "开源"]
---

## 项目概览

[Meetily](https://github.com/Zackriya-Solutions/meetily) 是一款开源的隐私优先 AI 会议助手，基于 Rust + Tauri 构建，核心能力是**本地实时转录 + AI 总结**。截至 2026 年 8 月，该项目在 GitHub 收获超过 28000 Star，最新版本 v0.4.0 提供 macOS（Apple Silicon）和 Windows 安装包，Linux 需从源码编译。

一句话定位：**所有录音、转录文本、AI 生成的摘要都留在你的机器上，不经过任何云服务。**

| 基本信息 | |
|---|---|
| 仓库 | `Zackriya-Solutions/meetily` |
| 语言 | Rust（后端）+ Next.js（前端），Tauri 打包 |
| 许可证 | MIT |
| 最新版本 | v0.4.0（2026-06-05 发布） |
| 支持平台 | macOS（aarch64）、Windows（x64）、Linux（源码构建） |
| 转录模型 | Whisper / Parakeet（NVIDIA 出品） |
| AI 总结提供商 | Ollama（本地）、Claude、Groq、OpenRouter、自定义 OpenAI 兼容端点 |

## 为什么需要：会议隐私的真实代价

市面上的会议转录工具（Otter、Fireflies、通义听悟等）几乎都走云端处理。这意味着你的会议录音、内部讨论、商业策略要上传到第三方服务器。这不是假设性的风险：

- IBM 2024 报告显示，数据泄露事件平均成本已达 440 万美元
- 截至 2025 年，GDPR 罚款累计超 58.8 亿欧元
- 仅加州一地，今年已有 400+ 起非法录音诉讼

对于金融、法律、医疗、国防等敏感行业，云端会议转录在合规层面几乎是不可接受的。即便非敏感场景，把内部讨论交给不可控的云服务，也不是一个好习惯。

Meetily 的解法很直接：**转录模型跑在本地，AI 总结也优先使用本地 Ollama**，数据不出设备。如果本地算力不足，也支持配置远程 LLM 端点，但音频数据始终不会上传。

## 核心功能

### 实时本地转录

使用 Whisper 或 NVIDIA Parakeet 模型在本地设备上做语音转文字，完全离线运行。Parakeet TDT 0.6B 模型在转录速度上比传统 Whisper 快约 4 倍（项目描述数据）。

### 多种 AI 总结后端

转录完成后，Meetily 将文本发送给 LLM 生成会议摘要。支持的后端：

- **Ollama（推荐）**：完全本地，隐私零妥协
- **Claude / Groq / OpenRouter / OpenAI**：如果你接受文本层面的远程处理
- **自定义 OpenAI 兼容端点**：对接组织内部部署的模型服务

### 音频导入与重新转录（Beta）

支持导入已有的音频文件进行转录。这意味着你可以用其他设备录音，事后导入 Meetily 处理，也可以用不同模型或语言对历史录音重新转录。

### 专业音频混合

同时捕获麦克风输入和系统音频（会议平台的播放音），内置智能 ducking 和削波防护。这一点很关键——如果只录麦克风，对方说话的内容就丢了。

### GPU 加速

构建时自动检测 GPU 类型并启用对应加速：

| 平台 | 加速方式 |
|---|---|
| Apple Silicon（M 系列） | Metal + CoreML |
| NVIDIA | CUDA |
| AMD / Intel | Vulkan |

无需手动配置，构建脚本 `build-gpu.sh` 会自动检测。

## 安装指南

### macOS（Apple Silicon）

```bash
# 1. 下载 dmg 安装包
# 从 GitHub Releases 页面下载 meetily_0.4.0_aarch64.dmg
# https://github.com/Zackriya-Solutions/meetily/releases/download/v0.4.0/meetily_0.4.0_aarch64.dmg

# 2. 打开 dmg，将 Meetily 拖入 Applications 文件夹

# 3. 从 Applications 启动 Meetily
```

文件大小约 47 MB，首次打开时 macOS 可能提示无法验证开发者，需在系统设置 > 隐私与安全中手动允许。

### Windows（x64）

```bash
# 方式一：安装程序（推荐）
# 下载 meetily_0.4.0_x64-setup.exe（约 41 MB）
# 双击运行即可安装

# 方式二：MSI 安装包（企业部署）
# 下载 meetily_0.4.0_x64_en-US.msi（约 67 MB）
```

### Linux（源码构建）

Linux 没有预编译包，需要从源码编译。前置依赖：Rust 工具链、Node.js、pnpm。

```bash
# 安装基础依赖（Ubuntu/Debian）
sudo apt update
sudo apt install build-essential cmake git

# 克隆仓库
git clone https://github.com/Zackriya-Solutions/meeting-minutes
cd meeting-minutes/frontend

# 安装前端依赖
pnpm install

# 构建生产版本（自动检测 GPU）
./build-gpu.sh
```

构建脚本会自动检测你的 GPU 环境：

| 检测条件 | 结果 |
|---|---|
| `nvidia-smi` 存在且找到 CUDA toolkit | 启用 CUDA |
| `rocm-smi` 存在且找到 ROCm | 启用 HIPBlas |
| Vulkan SDK 配置完整 | 启用 Vulkan |
| 以上都不满足 | 纯 CPU 模式（仍可用，速度稍慢） |

> **注意**：仅安装 GPU 驱动是不够的，还需要对应的开发 SDK（CUDA Toolkit / ROCm / Vulkan SDK）。很多人卡在这里——有显卡但跑的是 CPU 模式，通常就是因为缺 SDK。

## 快速使用

### 第一步：选择转录模型

打开 Meetily 后，在设置中选择 Whisper 或 Parakeet 作为转录引擎。Apple Silicon 用户建议选 Parakeet（速度更快），如果转录准确度不够再切回 Whisper。

### 第二步：配置 AI 总结后端

如果你已经在本地跑 Ollama：

1. 在设置中将 AI 提供商选为 Ollama
2. 确认 Ollama 服务地址（默认 `http://localhost:11434`）
3. 选择一个已拉取的模型（如 `llama3`、`qwen2.5`）

如果暂时没有本地 LLM，也可以先用 Claude 或 OpenAI 做总结，后续随时切换回本地。

### 第三步：开始会议

点击录音按钮，Meetily 会同时捕获麦克风和系统音频。会议过程中实时显示转录文本。结束后点击「生成摘要」，几秒到几十秒内（取决于模型和硬件）即可得到结构化的会议纪要。

### 第四步：导入历史音频

如果你有之前的会议录音文件，直接导入即可转录。这对于迁移历史数据很实用。

## 常见坑点

### 1. macOS 首次启动被 Gatekeeper 拦截

Meetily 的 dmg 没有 Apple 公证签名。首次打开会提示「无法打开，因为无法验证开发者」。解决：系统设置 > 隐私与安全 > 点击「仍要打开」。

### 2. Windows 系统音频捕获需要权限

Windows 上 Meetily 需要捕获系统音频（会议平台的声音）。首次使用时需要在 Windows 设置中授予音频录制权限。如果发现转录只有自己的声音没有对方的声音，检查系统音频捕获权限和设备选择。

### 3. Linux 上 GPU 没有生效

这是最常见的构建问题。`build-gpu.sh` 检测的是开发 SDK，不是驱动。具体来说：

- 有 NVIDIA 显卡但没装 `nvidia-cuda-toolkit` → 跑 CPU 模式
- 有 AMD 显卡但没装 ROCm → 跑 CPU 模式
- 想用 Vulkan 但没设 `VULKAN_SDK` 环境变量 → 跑 CPU 模式

验证方式：查看构建日志中是否出现 `--features cuda` / `--features hipblas` / `--features vulkan`，如果都没有就是纯 CPU。

### 4. Ollama 总结质量不如预期

Ollama 的总结效果取决于你用的模型。对于中文会议，建议用参数量较大的模型（如 `qwen2.5:14b` 或更大），小模型的摘要可能丢失关键信息。英文场景下 `llama3:8b` 基本够用。

### 5. 转录延迟与模型选择

Whisper 模型准确度高但速度慢，Parakeet 速度快 4 倍但某些场景（口音重、专业术语密集）可能不如 Whisper。建议先用 Parakeet 试一段录音，如果准确度不满意再切 Whisper。

## 适用边界

### Meetily 适合你，如果：

- **隐私是硬性要求**：你在处理商业敏感、法律保密、医疗 HIPAA 合规或国防级别的对话
- **网络受限**：在无外网环境或严格内网环境下工作
- **不想按月付费**：愿意用本地算力换零订阅费
- **技术背景允许**：Linux 用户需要编译能力，所有用户需要一定的模型配置知识
- **个人或小团队**：不需要大规模会议管理平台，只要快速转录 + 摘要

### Meetily 不适合你，如果：

- **需要多语言实时翻译**：Meetily 做的是转录，不是翻译
- **需要说话人识别**：社区版暂不提供自动区分说话人的能力（PRO 版计划支持）
- **深度团队协作**：没有日历集成、任务分配、CRM 对接等功能（这些是 PRO / Enterprise 的方向）
- **设备算力有限**：如果你只有一台老旧笔记本且没有 GPU，转录速度可能不理想
- **Linux 用户且不想折腾编译**：没有预编译包，从源码构建是唯一路径

### 社区版 vs PRO 版

Meetily 社区版（MIT 开源，本文介绍的版本）永久免费。PRO 版是不同代码库的商业产品，提供更高准确度的转录模型、自定义摘要模板、PDF/DOCX 导出、自动检测并加入会议、日历集成等。如果你只需要本地转录和基础摘要，社区版完全够用。

## 小结

Meetily 在「隐私优先的会议助手」这个赛道上做得相当扎实：Rust 后端保证了性能和内存安全，Tauri 让安装包保持小巧（47 MB），多 GPU 后端覆盖了主流硬件，AI 总结后端的灵活性也足够。

它不试图替代成熟的 SaaS 会议平台——没有团队协作、没有 CRM 集成、没有日历同步。它的价值主张很纯粹：**你的会议数据，一个字节都不离开你的设备。** 对于隐私敏感场景，这就是最好的选择。
