---
title: "Hermes Agent 完全指南：Nous Research 的「自进化」终端 Agent"
date: "2026-06-04T15:00:00+08:00"
slug: hermes-agent-nousresearch-self-improving-agent-guide
description: "Hermes Agent 是 Nous Research 开源的终端 AI Agent，内建技能自创建、对话检索、Honcho 用户建模、Telegram/Discord/WhatsApp 跨平台网关，支持 OpenClaw 一键迁移。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Terminal", "Nous Research", "OpenClaw", "Skills", "MCP"]
---

# Hermes Agent 完全指南：Nous Research 的「自进化」终端 Agent

## 核心判断

`Hermes Agent`（仓库 [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)）是 Nous Research 给"真正会学习的 AI Agent"交出的答卷。它不是又一个「Claude Code 套壳」或「Aider 复刻」——它的**核心差异化**是**"闭环学习循环"**：Agent 完成任务后会自动**创建技能（skill）**、在用时**自我改进**、周期性地**自我推动（nudge）** 把知识沉淀下来，并能**检索自己过去的对话**。

它的护城河在四件别家没拼齐的事：

1. **闭环学习（Closed Learning Loop）**：技能从经验中自动创建并自我改进，跨会话用 FTS5 + LLM 摘要回溯
2. **跨平台网关**：Telegram / Discord / Slack / WhatsApp / Signal / Email **同进程**直连
3. **六大终端后端**：local / Docker / SSH / Singularity / Modal / Daytona，**$5 VPS 跑得动，serverless 闲时几乎免费**
4. **OpenClaw 平滑迁移**：`hermes claw migrate` 一行命令把 SOUL/MEMORY/USER/AGENTS.md/技能/MCP 配置全量搬过来

如果团队正面临"Agent 用完即忘、不能跨会话累积经验"或"想从手机/IM 里驱动 Agent 干活"的痛点，Hermes 是目前最值得评估的方案。

## 项目地图

| 维度 | 关键信息 |
|------|----------|
| 仓库 | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) |
| 文档 | [hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs/) |
| 许可证 | MIT |
| 出品方 | [Nous Research](https://nousresearch.com)（Hermes 模型家族的原作者） |
| 中文支持 | 有专门 [README.zh-CN.md](https://github.com/NousResearch/hermes-agent/blob/main/README.zh-CN.md) |

### 能力矩阵

| 维度 | 实现 |
|------|------|
| 终端界面 | Full TUI（多行编辑、slash 自动补全、对话历史、中断重定向、流式工具输出） |
| 通信网关 | Telegram、Discord、Slack、WhatsApp、Signal、Email 同一 gateway 进程 |
| 记忆机制 | Agent-curated memory + 周期 nudge + FTS5 会话搜索 + LLM 摘要 |
| 用户建模 | [Honcho](https://github.com/plastic-labs/honcho) 辩证式（dialectic）用户画像 |
| 技能标准 | 兼容 [agentskills.io](https://agentskills.io) 开放标准 |
| 定时任务 | 内建 cron 调度器，可投递到任意平台 |
| 并行子代理 | 派生 isolated subagents 并行执行工作流 |
| 终端后端 | local / Docker / SSH / Singularity / Modal / Daytona 六种 |
| 模型供给 | Nous Portal / OpenRouter（200+）/ NovitaAI / NVIDIA NIM / Xiaomi MiMo / z.ai GLM / Kimi / MiniMax / HF / OpenAI / 自定义 endpoint |
| 研究支持 | 批量轨迹生成 + 轨迹压缩（为下一代 tool-calling 模型出训练数据） |

## 安装与快速上手

### 一行安装

Linux / macOS / WSL2 / Termux：

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

Windows 原生（PowerShell，不需要 WSL）：

```powershell
iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)
```

安装器会自动处理：

- `uv`（Python 包管理）
- Python 3.11
- Node.js
- `ripgrep` / `ffmpeg`
- **便携 Git Bash（MinGit，~45MB，解压到 `%LOCALAPPDATA%\hermes\git`）**——不污染系统 Git

> Termux 提示：Hermes 会装 `.[termux]` 精简版 extra（避免 Android 不兼容的语音依赖）。

装完启动：

```bash
source ~/.bashrc    # 或 source ~/.zshrc
hermes              # 进入交互式 CLI
```

### 第一次设置

```bash
hermes              # 弹出 setup 向导
hermes setup        # 或者手动跑全量配置
hermes setup --portal  # 一键连 Nous Portal（覆盖 300+ 模型 + Tool Gateway）
hermes model        # 选模型：Nous Portal / OpenRouter / OpenAI / ...
hermes tools        # 启用 / 禁用具体工具
hermes config set   # 改单个 config 值
hermes gateway      # 启动 IM 网关（Telegram/Discord/...）
hermes doctor       # 诊断环境
hermes update       # 升级
hermes claw migrate # 从 OpenClaw 迁移
```

> 微信桥接用 [AaronWong1999/hermesclaw](https://github.com/AaronWong1999/hermesclaw)，它能让 Hermes Agent 和 OpenClaw **跑在同一个微信号**上。

## 核心能力拆解

### 1. 闭环学习（Closed Learning Loop）

这是 Hermes 最值钱的部分，包含四个机制：

- **Agent-curated memory**：Agent 自己决定什么值得记，比"全部写入"更克制
- **Periodic nudges**：定期主动 push Agent 把零散观察整理成知识
- **Autonomous skill creation**：复杂任务完成后**自动生成新 skill**，下次直接复用
- **Skill self-improvement**：skill 在被使用中持续优化参数
- **FTS5 session search + LLM summarization**：跨会话检索自己的过去

> 实操含义：跑得越久，越顺手；不需要人工"运维"记忆库。

### 2. Honcho 辩证式用户建模

集成 [Honcho](https://github.com/plastic-labs/honcho)，构建"会演化的用户画像"——不是简单的"用户喜欢 X"，而是基于你跟 Agent 的**多轮辩证**得出"你为什么更喜欢 X 而非 Y"。

这种建模对"个性化"很有用，但代价是**需要给 Honcho 写权限足够的数据**——自己评估。

### 3. Skills Hub（agentskills.io 开放标准）

技能描述走 [agentskills.io](https://agentskills.io) 开放标准，意味着：

- 别人的 skill 可以直接 import
- 你写的 skill 也能给别人用
- 不被单一 Agent 平台绑定

浏览/调用 skill：

```bash
hermes skills            # 列出可用 skill
/git-commit              # 触发 git-commit skill（slash 命令风格）
```

### 4. 跨平台消息网关

所有 IM 平台**一个 gateway 进程**：

```bash
hermes gateway setup     # 配置 Telegram/Discord/Slack/WhatsApp/Signal token
hermes gateway start     # 起服务
```

之后从手机/IM 直接给 Agent 发消息，**Hermes 会用同一个对话上下文**。每个平台都支持：

- 语音备忘录转录
- 跨平台会话连续性（在 Telegram 说到一半，Slack 上能接上）
- 定时任务投递（"明早 9 点把这份报告发到 Slack"）

### 5. 并行子代理 + RPC 工具

- **Spawn isolated subagents**：派发隔离的子 Agent 并行跑工作流
- **Python scripts that call tools via RPC**：写 Python 脚本时**零 context 成本**调用工具，多步 pipeline 折叠成一次 turn

适合"我有一个数据 pipeline，要拉数据+分析+写报告"这种场景。

### 6. 六大终端后端

| Backend | 用途 | 成本 |
|---------|------|------|
| `local` | 本机直跑 | 0 |
| `Docker` | 容器隔离 | 0 |
| `SSH` | 远程 VPS | 看你 VPS |
| `Singularity` | HPC 集群 | 看你集群 |
| `Modal` | serverless GPU/CPU | **闲时几乎免费** |
| `Daytona` | serverless dev env | **闲时几乎免费** |

Modal 和 Daytona 的"环境冬眠 + 唤醒"模型对**低频使用**特别友好——只在你发消息时按秒计费。

### 7. MCP 集成

直接接任何 MCP server，扩展能力池。配合 [avifenesh/computer-use-linux](https://github.com/avifenesh/computer-use-linux) 还能让 Hermes 控制 Linux 桌面（AT-SPI 访问树、Wayland/X11 输入、截图、合成器窗口定位）。

## CLI vs IM 命令对照

| 操作 | CLI | IM |
|------|-----|-----|
| 开始聊天 | `hermes` | `hermes gateway setup/start` 后发消息 |
| 重新开始对话 | `/new` 或 `/reset` | `/new` 或 `/reset` |
| 换模型 | `/model [provider:model]` | `/model [provider:model]` |
| 设 personality | `/personality [name]` | `/personality [name]` |
| 重试上一轮 | `/retry` `/undo` | `/retry` `/undo` |
| 压缩 context | `/compress` `/usage` `/insights [--days N]` | `/compress` `/usage` `/insights [days]` |
| 查 skill | `/skills` 或 `/<skill-name>` | `/<skill-name>` |
| 中断任务 | `Ctrl+C` 或发新消息 | `/stop` 或发新消息 |
| 平台状态 | `/platforms` | `/status` `/sethome` |

## OpenClaw 迁移

如果是从 OpenClaw 搬过来：

```bash
# 首次 setup 时自动检测 ~/.openclaw 目录并提示迁移
hermes setup

# 任何时候手动迁移
hermes claw migrate              # 完整预设（含密钥）
hermes claw migrate --dry-run    # 预览
hermes claw migrate --preset user-data   # 只迁数据，密钥不动
hermes claw migrate --overwrite  # 冲突覆盖
```

迁移范围：

- **SOUL.md** → 人设文件
- **MEMORY.md / USER.md** → 记忆条目
- **AGENTS.md** → workspace 指令（`--workspace-target` 指向）
- **用户自建 skills** → `~/.hermes/skills/openclaw-imports/`
- **命令白名单**（approval patterns）
- **IM 平台配置**（Telegram token、allowed users、cwd）
- **API keys**（Telegram / OpenRouter / OpenAI / Anthropic / ElevenLabs）
- **TTS 资源**（workspace 音频文件）

## 典型工作流

### 场景 A：手机指挥 VPS

1. VPS 上跑 `hermes gateway start`
2. Telegram 配 token 给 Gateway
3. 出门在外，发条消息："把昨天那个 bug 重现一下，附 stack trace"

Hermes 会用 ssh backend 在 VPS 上跑命令、收集输出、把结果发回 Telegram。

### 场景 B：每天早上 9 点自动跑日报

```bash
hermes cron add "0 9 * * *" "跑过去 24h 关键指标，整理成日报，发送到 Slack #ops"
```

到点就执行。

### 场景 C：研究目的轨迹采集

```bash
hermes batch-trajectories --tasks ./eval_set.jsonl --output ./trajectories/
```

得到一批 tool-calling 轨迹，**压缩后**可以拿来训练下一版 tool-calling 模型。

## 边界与盲点

- **首次安装拉取依赖较大**：`uv` / Python 3.11 / Node / ripgrep / ffmpeg / MinGit 一把装完，国内网络不一定友好
- **FTS5 搜索是 SQLite 引擎**：跨设备同步没内置，需要自己写同步层
- **Honcho 用户建模是 Optional**：默认开启会采集较多对话数据，**注意隐私边界**
- **Serverless backend（Modal/Daytona）需要账户**：跑通不难，迁移成本要看具体场景
- **Voice 端到端目前仅 Unix 全栈**：Windows 上要 WSL2 才能跑浏览器聊天面板（CLI 和 gateway 原生 OK）
- **学习曲线比"一键 chat"工具陡**：上手得读一遍 docs，但回报也更大

## 与同类对比

| 工具 | 闭环学习 | IM 网关 | 终端后端多样性 | 跨平台 | OpenClaw 迁移 | License |
|------|----------|---------|----------------|--------|---------------|---------|
| **Hermes Agent** | ✅ 四机制闭环 | ✅ 6 平台 | ✅ 6 后端 | ✅ | ✅ | MIT |
| Claude Code | ⚠️ 记忆但无 skill 自创 | ❌ | ⚠️ 本地 | ❌ | – | 商业 |
| Aider | ❌ | ❌ | ⚠️ 本地 | ⚠️ | – | Apache |
| Open Interpreter | ❌ | ❌ | ⚠️ 本地 | ⚠️ | – | MIT |
| Codex CLI | ⚠️ 仅 recall | ❌ | ⚠️ 本地 | ❌ | – | Apache |

> Hermes 的真正价值是"**学习-IM-多后端**"三者合一，且对 OpenClaw 用户做了一等公民的迁移路径。

## 采用建议

### 适合谁

- 想要 Agent **越用越聪明**而不是每次"重新培训"
- 希望从 IM 里指挥 Agent，跨设备、跨平台
- 已经在用 OpenClaw 想换一个有更好学习能力的 Agent
- 有 serverless 算力（Modal/Daytona）但不想为闲时付费

### 不适合谁

- 只想要"写代码"工具——Claude Code / Aider 更聚焦
- 完全离线、零外网环境——很多 IM 网关和 Model API 都需要公网
- 数据合规要求**零数据出本地**——Honcho 用户建模是云端集成

### 落地顺序

1. **先跑起来**：`curl | bash` + `hermes setup --portal` 五分钟试手感
2. **再接 IM**：挑一个常用平台（Telegram/Discord），`hermes gateway setup` 配 token
3. **观察一周学习效果**：跑一批真实任务，看 skill 自动创建和 memory 召回
4. **接 OpenClaw 迁移**：如果满意，`hermes claw migrate` 全量搬过来
5. **最后接 serverless backend**：用 Modal/Daytona 把计算后端放到云

## 一句话总结

> Hermes Agent 是当下**最接近"会成长的 AI 同事"形态**的开源终端 Agent——闭环学习、跨平台 IM 网关、OpenClaw 平滑迁移三件套齐全；学习曲线比"一键 chat 工具"陡，但回报是 Agent 越用越顺手。

---

*📚 仓库地址：[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) · 文档：[hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs/) · License：MIT · 出品方：[Nous Research](https://nousresearch.com)*
