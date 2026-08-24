---
title: "AI-Infra-Guard：腾讯朱雀实验室的 AI 红队平台，从基础设施扫到 Skill 审计"
date: 2026-08-25T03:45:00+08:00
slug: "tencent-ai-infra-guard-red-teaming-platform"
github_repo: "Tencent/AI-Infra-Guard"
source_key: "gh:Tencent/AI-Infra-Guard"
description: "腾讯朱雀实验室开源的 AI 红队平台 A.I.G，集成 AI 基础设施漏洞扫描、MCP Server 与 Agent Skill 审计、越狱评估与多智能体扫描，覆盖 2000+ CVE 规则与 9 类 Skill 风险。本文拆解其能力矩阵与上手路径。"
draft: false
categories: ["技术笔记"]
tags: ["AI安全", "红队测试", "漏洞扫描", "开源"]
---

AI 应用安全的检查面正在从"模型本身"扩散到整条基础设施链：跑在局域网里的 Ollama、暴露端口的 vLLM、随手安装的 MCP Server、别人写好的 Agent Skill——每一环都可能成为攻击入口。腾讯朱雀实验室开源的 [AI-Infra-Guard](https://github.com/Tencent/AI-Infra-Guard)（简称 A.I.G）瞄准的就是这个全景：一个自托管的 AI 红队平台（AI Red Teaming Platform），把 AI 基础设施漏洞扫描、MCP/Skill 审计、Agent 工作流扫描和越狱评估装进同一个 Web 界面。

## 项目概览

| 项目 | 数据（2026-08-24 取自 GitHub） |
|------|------|
| 仓库 | Tencent/AI-Infra-Guard |
| Stars / Forks | 5,742 / 537 |
| 语言 / 协议 | Python / Apache 2.0 |
| 最新版本 | v4.5.2（2026-08-17） |
| 维护状态 | 最近提交 2026-08-24，发布节奏约每 1-2 周一版 |
| 出品方 | 腾讯安全平台部·朱雀实验室 |

值得注意的背景：该项目入选 Black Hat EU 2025 Arsenal 议题，团队曾协助 NVIDIA、Google、Microsoft 及 OpenClaw、Linux、Hugging Face 等社区修复高危漏洞。这不是玩具项目，而是安全实验室的工程化产出。

## 能力矩阵：五个扫描面

A.I.G 的核心设计是把"AI 生态安全自查"拆成五个独立又互补的扫描面：

### 1. AI 基础设施漏洞扫描（AI Infra Scan）

对**正在运行的 AI 服务**做指纹识别，再匹配已知 CVE。它识别 100+ AI 框架组件（Ollama、ComfyUI、vLLM、n8n、Triton Inference Server 等），规则库在 v4.5.2 已扩展到 2000+ 条 CVE 规则。

一个常见误解需要澄清：扫描目标填的是**服务的网络地址**，不是 GitHub URL 或源码路径——比如本地 vLLM 填 `http://127.0.0.1:8000`，局域网 Ollama 填 `http://192.168.1.100:11434`，也支持 CIDR 段（`192.168.1.0/24`）和 IP 区间批量扫描。A.I.G 会连上活的服务做指纹，再对版本匹配漏洞。

### 2. MCP Server 与 Agent Skill 扫描

这一块是项目近期的重点迭代方向。MCP（Model Context Protocol）Server 和 Agent Skill 本质都是"给模型装上的外部工具"，投毒面天然存在。A.I.G 覆盖 14 大类安全风险，支持从源码或远程 URL 两种方式扫描，无需运行实例。

v4.5.2 的更新体现了攻防对抗的实时性：检测 `.pyc` 字节码绕过（把恶意逻辑藏在编译产物里躲过文本审计）、charset 走私防御，以及 MCP 动态模式下通过工具白名单防 RCE。

针对 Skill 审计，团队还发布了独立 CLI，可直接嵌入企业 CI/CD：

```bash
pip install aig-skill-scan
export LLM_API_KEY="your-api-key"
aig-skill-scan --repo /path/to/your/skill \
    -m deepseek-v4-flash \
    --language en \
    -o result.json
```

其风险分类对齐自家的 [SkillTrustBench](https://matrix.tencent.com/skilltrustbench/) T01–T09 分类法，分五层九类：

| 层 | 风险类型 |
|----|---------|
| 指令与记忆 | T01 Skill 指令劫持、T02 记忆投毒 |
| 代码执行 | T03 远程载荷下载执行、T04 内嵌恶意代码 |
| 系统权限 | T05 提权与越权访问、T06 系统持久化 |
| 工具链与依赖 | T07 工具劫持与伪造、T08 不安全依赖 |
| 代码质量 | T09 不安全编码实践 |

在 SkillTrustBench 基准上，配 Claude Opus 4.6 时 F1 达 0.9848，GLM 5.1 为 0.9836——注意这是团队自报的、用自家基准测自家工具的数字，横向对比其他工具时应保留判断。

### 3. ClawScan（OpenClaw 安全扫描）

一键评估 OpenClaw 类智能体运行时的安全配置：不安全配置、Skill 风险、CVE 漏洞与隐私泄露。

### 4. Agent Scan

多智能体自动化扫描框架，评估 AI Agent 工作流的安全性，支持 Dify、Coze 等平台上运行的智能体。v4.5.1 加入了 10 个 OWASP 风格 Skill 与 Web 外泄检测。

### 5. 越狱评估（Jailbreak Evaluation）

面向 LLM 本身：配置目标模型的 API 端点，选数据集，用多种攻击方法测鲁棒性，并提供跨模型对比。v4.5.1 新增 4 种多轮越狱攻击（Many-Shot、PAIR、GOAT、ActorAttack）。

## 快速上手

**Docker 部署**（推荐，要求 Docker 20.10+、4GB 内存、10GB 磁盘）：

```bash
git clone https://github.com/Tencent/AI-Infra-Guard.git
cd AI-Infra-Guard
# Docker Compose V2+ 用 'docker compose'
docker-compose -f docker-compose.images.yml up -d
```

启动后访问 `http://localhost:8088` 即得 Web 界面；API 文档在 `http://localhost:8088/docs/index.html`（含 Swagger 规范，便于集成到自有流程）。

也有一键脚本（自动装 Docker 并启动）：

```bash
curl https://raw.githubusercontent.com/Tencent/AI-Infra-Guard/refs/heads/main/docker.sh | bash
```

一个重要安全边界，README 用醒目位置声明了：**A.I.G 目前没有认证机制，定位为企业或个人内网自用，禁止部署在公网**。一个能扫全网段、能跑越狱攻击的平台，本身就是高价值攻击目标。

## 架构与扩展方式

项目采用可扩展插件框架，规则即数据、贡献即加文件：

- 指纹规则 → `data/fingerprints/`（YAML）
- 漏洞规则 → `data/vuln/`
- MCP 扫描规则 → `data/mcp/`
- 越狱数据集 → `data/eval/`

照现有格式建文件、提 PR 即可，不需要改扫描引擎代码。这种"规则与引擎分离"的设计让规则库的迭代速度（1888 → 2000+ 规则只用了三周）远快于引擎本身。

此外项目还提供模型与 API 中转检查器（模型指纹、Claude 签名验证、中转黑盒审计），以及 Pro 在线版（邀请码制，优先给贡献者）。对 OpenClaw 用户，ClawHub 上有三个可直接调用的 skill（`aig-scanner`、EdgeOne ClawScan、EdgeOne Skill Scanner）。

## 适用边界

- **适合**：企业内网自查 AI 基础设施暴露面；给自研/第三方 MCP Server 和 Skill 做上线前安全审计；对候选模型做越狱鲁棒性横向对比。
- **不适合**：公网多租户 SaaS 场景（无认证）；期望"装完就安全"的团队——它是红队工具，输出的是风险清单，修复仍需自己动手。
- **留意**：SkillTrustBench 成绩为项目自报；Pro 版与开源版的功能分界随版本演进，选型前建议核对当前版本文档。

## 阅读路径

- 在线文档：https://tencent.github.io/AI-Infra-Guard/
- 架构演进：仓库内 `docs/architecture_evolution.md`
- 独立 CLI：`skill-scan/`、`mcp-scan/`、`agent-scan/` 三个目录
- 基准：https://matrix.tencent.com/skilltrustbench/

一句话总结：当你的 AI 栈从"调一个 API"长成"Ollama + vLLM + MCP + 别人写的 Skill"时，A.I.G 提供了一套开箱即用的自查清单——它不替你做安全，但能让你知道现在有多不安全。
