---
title: "Octop：腾讯开源的自托管多智能体 AI 助手，一个进程装下全家人的数字分身"
date: 2026-09-23T04:10:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["AI 助手", "自托管", "多智能体", "开源项目"]
description: "TencentCloud/Octop 是腾讯云开源的自托管 AI 助手平台：单进程跑起 Web 控制台、CLI、七个 IM 渠道与定时任务，多用户隔离、专家库、RAG 知识库、浏览器与终端自动化全在一台自己的机器上。本文拆解其架构取舍、消息流转与上手路径。"
github_repo: "TencentCloud/Octop"
source_key: "gh:TencentCloud/Octop"
slug : octop-self-hosted-multi-agent-assistant
---

## 核心判断

自托管 AI 助手这个赛道，大部分项目止步于"套壳聊天界面"。Octop（[TencentCloud/Octop](https://github.com/TencentCloud/Octop)）的差异点在于它认真做了三件难而正确的事：**单进程架构**（没有外部消息队列，重启安全）、**多用户隔离**（JWT + 每用户独立 agent 工作区，明确面向家庭和小团队共享）、**双向 ACP**（Agent Client Protocol，智能体客户端协议——既能被 IDE 调用，也能把编码任务委派给 Claude Code / Codex 等外部 agent）。IM 渠道、RAG 知识库、浏览器与终端自动化、cron 定时任务全部收进同一个进程。README 中文版的原话是"可并行运作的数字生命体"——这个定位决定了它的产品形态：不是一堆零散工具，而是住在你电脑里的一个助手群。

项目 2026 年 7 月开源，MIT 协议，由腾讯云维护，不到三个月涨到约 6,200 Stars、780 Forks（2026 年 10 月初查询）。最新版本 v1.0.2b5（9 月 29 日发布），Python 3.12+。

## 系统地图

Octop 建在自研的 Octop Harness 运行时栈上——四个独立开源仓库组成核心件，由 Octop 主项目组装进一个进程：

| 层 | 技术 | 职责 |
|----|------|------|
| Web 框架 | FastAPI + uvicorn | API 与控制台后端 |
| Agent 运行时 | [Octop Harness](https://github.com/TencentCloud/octop-harness) | 模型路由、工具、技能、对话检查点 |
| IM 网关 | [Octop Gateway](https://github.com/TencentCloud/octop-gateway) | 多平台消息桥接，归一化为单一处理管道 |
| 记忆 | [Octop Memory](https://github.com/TencentCloud/octop-memory) | 分层召回 + 全文检索，随工作区迁移 |
| 浏览器 | [Octop Browser](https://github.com/TencentCloud/octop-browser) | 基于 CDP 的浏览器自动化，持久化 profile |
| 控制面数据库 | SQLite（WAL，默认）/ PostgreSQL | 全部状态，开机重建 |
| 前端 | React 18 + TypeScript + Vite + Ant Design | Web 控制台 |
| 调度 | APScheduler | cron 定时任务 |

架构上最值得注意的取舍：**没有外部队列或消息代理**。Web UI、IM、cron 三个表面全部经由进程内的 `HarnessProcessor` 路由（每个 agent 一个运行时实例），整个状态在启动时从控制面数据库重建。换来的是部署简单（一条 `octop run`）和重启安全，代价是单进程的扩展上限——对家庭/小团队场景，这笔账算得过来。

核心进程之外还有三层扩展机制，不动架构：**Connectors**（OAuth 应用 + MCP 网关）把外部服务接进来，内置腾讯文档、腾讯会议、腾讯新闻等连接器；**知识库**对你的文档做 RAG（Retrieval-Augmented Generation，检索增强生成）检索，语料可在同一部署内共享给多个 agent；**插件**（`octop plugin`）装第三方能力，内置插件以种子形式预置、在控制台按需开关。

## 关键机制

**多用户与专家库。** 一个管理员账户，家庭成员各自登录。每个用户可拥有多个 agent；"专家"（expert）则是带完整配置的 agent——独立的工作区、模型供应商、渠道和 cron，切专家就是换一套人格和工具。内置专家库在启动时扫描 `infra/agents/experts/library/`，另有 16 套 MBTI 人格模板加交互式测验给 agent 定性格。共享做了两层：专家可以发布给同部署的其他用户，技能与子 agent 可进共享资源池，新专家直接复用现成配置。

**AgentTeams（Beta）。** 一个协调者 agent 自主调度多个成员专家，协作完成多步任务——把"多个专家"从并列摆放变成有分工的组织，控制台有独立面板管理。

**ACP 双向集成。** 入站方向：`octop acp --agent main` 起一个 stdio ACP 服务器，Zed、OpenCode 等编辑器工具可以直接调用你的 Octop agent。出站方向：在控制台 ACP 页配置 runner（全局按用户生效，内置 OpenCode、CodeBuddy、Claude Code、Codex），再按 agent 启用 `acp_runner`，就能在聊天里把编码任务委派出去，全程带权限门控。

**安全设计。** JWT 多用户隔离、工具调用审批、shell 命令护栏、PII（个人身份信息）脱敏；所有数据落在本地 `~/.octop/`。shell 的 allow/deny 规则放在 `~/.octop/security/tool_guard/`，用户可以直接编辑。Docker 部署时首次初始化生成随机管理员密码，写入容器内 `/data/.octop/credential.txt`（可用 `OCTOP_DEFAULT_PASSWORD` 环境变量覆盖）；密码策略要求至少 8 位、含字母和数字，弱密码会被拒绝并回退到随机生成。

**可插拔后端。** 工作区支持本地磁盘、Docker 沙箱、PostgreSQL、COS/S3——AI 在隔离边界内操作文件，而不是直接碰宿主机。工作区后端与控制面数据库相互独立，换存储不用动 agent。

**远程桌面与终端 AI+。** 控制台可以直接查看并操作主机桌面（Linux/Windows/macOS），无头 Linux 服务器可一键起隔离桌面，远程办公、操作 GUI 应用都走这条路。终端 AI+ 在浏览器里开交互式 shell，AI 辅助执行命令、排查故障。

## 一次消息的完整流转

把抽象机制串起来看一次真实任务：家人在飞书里对 Octop 说"每天早上 8 点把我的日程汇总发到这个群"。

1. **Gateway 收消息**：Octop Gateway 从飞书拉取消息，剥掉平台差异（发送者身份、会话、附件格式），归一化成统一格式；
2. **HarnessProcessor 路由**：按消息归属找到对应的用户与 agent 运行时，没有外部队列，进程内直接分发；
3. **Agent 执行**：Octop Harness 加载该 agent 的技能与记忆，模型决定"创建 cron 任务"，APScheduler 登记定时作业；若动作涉及 shell 命令或敏感工具，先停在审批门控等确认；
4. **回复走原路**：响应沿同一管道回到飞书群。第二天早上 8 点，cron 触发的汇总重复第 2、3 步，主动推送到群里。

三个入口（Web UI、IM、cron）共用同一条管道——这就是单进程设计在真实任务里的样子：没有消息中间件，没有跨进程状态，重启后一切从数据库重建。

## 上手路径

最推荐的路径是一键安装脚本（用 uv 在 `~/.octop/` 下隔离 venv 自动装 Python 3.12，无需预装）：

```bash
# macOS / Linux
curl -fsSL https://finnie-1258344699.cos.ap-guangzhou.myqcloud.com/octop/install.sh | bash

# Windows (PowerShell)
irm https://finnie-1258344699.cos.ap-guangzhou.myqcloud.com/octop/install.ps1 | iex

# 初始化（交互式向导：建库、JWT 密钥、首个管理员）
octop init

# 启动（前台跑 API + Web 控制台）
octop run
```

然后打开 `http://127.0.0.1:8088`。可选扩展：安装时加 `--extras browser` 下载 Playwright Chromium（浏览器自动化所需，系统已有 Chrome/Chromium 时自动跳过）。IM 渠道在控制台里配，或用 `octop channel install`；支持的渠道有飞书、钉钉、QQ、微信、Telegram、Discord、企业微信，另有 HTTP/SSE/WebSocket API 供程序调用。

其他安装方式：PyPI（`pip install octop`，本地嵌入模型加 `octop[local-embedding]`）、Docker Compose（`docker compose -f docker/docker-compose.yml up -d`，README 标注为生产推荐）、GitHub Releases 桌面安装包（Windows/macOS/Linux 原生客户端，还有飞牛 NAS 的 fpk 包）。注册为系统服务用 `octop service start`（systemd / launchd / Windows service）。

日常维护三条命令值得记住：`octop update` 升级只替换程序本体，`~/.octop/` 下的数据库、工作区、密钥和配置原样保留；`octop backup` 导出备份，跨版本升级前官方建议先备份；`octop memory slim` 备份并瘦身 SQLite 记忆库，终端和控制台都能看到进度。

提醒一句：安装脚本的下载源是腾讯云 COS 直链，审慎环境可以先读脚本再执行——这是所有 `curl | bash` 式安装的通用注意事项，不是 Octop 独有的问题。

## 适用边界

- **目标场景是家庭与小团队**，不是高并发企业服务——单进程架构决定了它的扩展上限，多实例横向扩展不是当前设计目标；
- **需要自备模型供应商**：Octop 是助手框架，LLM 能力来自你配置的 provider（OpenAI 兼容 API、DashScope/Qwen、Ollama 等预设），项目本身不绑定某家模型；
- Roadmap 变化很快，以官方仓库当前状态为准：共享资源池、专家共享、桌面客户端三项已经落地，AgentTeams 处于 Beta，移动端在内测；自进化技能蒸馏、Managed Agents、云边协同、插件市场还在计划中。官方明确 roadmap 仅为指示性（indicative only），选型时不要把未落地项当作承诺；
- 与腾讯云同组织的 CubeSandbox（AI Agent 沙箱）、TencentDB Agent Memory（团队级记忆中枢）定位完全不同，Octop 的主轴是"自托管多用户助手平台"；它依赖的 Harness、Gateway、Memory、Browser 四个核心件是独立开源仓库，想单独研究或复用其中一件也可以直接去各自的仓库。

一句话：如果你想要一个数据完全留在自己机器上、家人同事能共用、还能接 IM 渠道和外部编码 agent 的 AI 助手底座，Octop 是目前这个方向上完成度相当高的开源选项。急着给家庭或小团队搭私有助手的，可以直接上；主要想借鉴架构的，先读上面四个核心件仓库，再回到主项目看它们如何被组装成一个进程。
