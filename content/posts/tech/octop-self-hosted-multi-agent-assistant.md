---
title: "Octop：腾讯开源的自托管多智能体 AI 助手，一个进程装下全家人的数字分身"
date: 2026-09-23T04:10:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["AI 助手", "自托管", "多智能体", "开源项目"]
description: "TencentCloud/Octop 是腾讯云开源的自托管 AI 助手平台：单进程跑起 Web 控制台、CLI、飞书钉钉等 IM 渠道与定时任务，多用户隔离、专家库、RAG 知识库、浏览器与终端自动化全在一台自己的机器上。本文拆解其架构取舍与上手路径。"
github_repo: "TencentCloud/Octop"
source_key: "gh:TencentCloud/Octop"
slug : octop-self-hosted-multi-agent-assistant
---

## 核心判断

自托管 AI 助手这个赛道，大部分项目止步于"套壳聊天界面"。Octop（[TencentCloud/Octop](https://github.com/TencentCloud/Octop)）的差异点在于它认真做了三件难而正确的事：**单进程架构**（没有外部消息队列，重启安全）、**多用户隔离**（JWT + 每用户独立 agent 工作区，明确面向家庭和小团队共享）、**双向 ACP**（既能被 IDE 调用，也能把编码任务委派给 Claude Code / Codex 等外部 agent）。加上 IM 渠道、RAG 知识库、浏览器/终端自动化和 cron 定时任务，它更像一个可以住在自己电脑里的"数字生活形态"——这是 README 的原话，也是项目的定位。

项目由腾讯云开源，MIT 协议，截至 2026 年 9 月约 4,600 Stars、531 Forks，版本 v1.0.1，Python 3.12+。

## 系统地图

Octop 建在一套自研的 Harness 运行时栈上，各层职责清晰：

| 层 | 技术 | 职责 |
|----|------|------|
| Web 框架 | FastAPI + uvicorn | API 与控制台后端 |
| Agent 运行时 | harness-agent | 模型路由、工具、技能、对话检查点 |
| IM 网关 | harness-gateway | 多平台消息桥接，归一化为单一处理管道 |
| 记忆 | harness-memory | 分层召回 + 全文检索，随工作区迁移 |
| 浏览器 | harness-browser | 基于 CDP 的浏览器自动化，持久化 profile |
| 控制面数据库 | SQLite（WAL，默认）/ PostgreSQL | 全部状态，开机重建 |
| 前端 | React 18 + TypeScript + Vite + Ant Design | Web 控制台 |
| 调度 | APScheduler | cron 定时任务 |

架构上最值得注意的取舍：**没有外部队列或消息代理**。Web UI、IM、cron 三个表面全部经由一个进程内的 `HarnessProcessor` 路由，整个状态在启动时从控制面数据库重建。这换来的是部署简单（一条 `octop run`）和重启安全，代价是单进程的扩展上限——对家庭/小团队场景，这笔账算得过来。

## 关键机制

**多用户与专家库。** 一个管理员账户 + 家庭成员共享，每个用户可拥有多个 agent，各自带独立的工作区、模型供应商、渠道和 cron。内置专家库（启动时扫描 `infra/agents/experts/library/`）按场景切换"专家"；另有 16 套 MBTI 人格模板给 agent 设定性格。

**ACP 双向集成。** 入站方向：`octop acp --agent main` 起一个 stdio ACP 服务器，Zed、OpenCode 等编辑器工具可以直接用你的 Octop agent。出站方向：在控制台配置 runner（内置 OpenCode、CodeBuddy、Claude Code、Codex），在聊天中把编码任务委派出去，带权限门控。

**安全设计。** JWT 多用户隔离、工具调用审批、shell 命令护栏、PII（个人身份信息）脱敏；所有数据落在本地 `~/.octop/`。Docker 部署时首次 init 生成随机管理员密码写入容器内文件，密码策略要求至少 8 位含字母数字。

**可插拔后端。** 工作区支持本地磁盘、Docker 容器、PostgreSQL、COS/S3——AI 在隔离边界内操作文件，而不是直接碰宿主机。

## 上手路径

最推荐的路径是一键安装脚本（用 uv 在 `~/.octop/` 下隔离 venv 自动装 Python 3.12，无需预装）：

```bash
# macOS / Linux
curl -fsSL https://finnie-1258344699.cos.ap-guangzhou.myqcloud.com/octop/install.sh | bash

# 初始化（交互式向导：建库、JWT 密钥、首个管理员）
octop init

# 启动（前台跑 API + Web 控制台）
octop run
```

然后打开 `http://127.0.0.1:8088`。可选扩展：`--extras browser` 装 Playwright Chromium（浏览器自动化），`--extras channels-feishu` 开飞书渠道。

其他安装方式：PyPI（`pip install octop`）、Docker Compose（README 标注为生产推荐）、GitHub Releases 桌面安装包（Windows/macOS/Linux，甚至有飞牛 NAS 的 fpk 包）。注册为系统服务用 `octop service start`（systemd / launchd / Windows service）。

提醒一句：安装脚本的下载源是腾讯云 COS 直链，审慎环境可以先读脚本再执行——这是所有 `curl | bash` 式安装的通用注意事项，不是 Octop 独有的问题。

## 适用边界

- **目标场景是家庭与小团队**，不是高并发企业服务——单进程架构决定了它的扩展上限，多实例横向扩展不是当前设计目标；
- **需要自备模型供应商**：Octop 是助手框架，LLM 能力来自你配置的 provider（含本地模型），项目本身不绑定某家模型；
- Roadmap（共享资源池、专家共享、AgentTeams、自进化技能蒸馏、原生客户端）官方标注为"指示性，可能随社区发展调整"，选型时不建议把 roadmap 项当作承诺；
- 与同 owner 已写的 cubesandbox（沙箱）、tencentdb-agent-memory（数据库记忆）是完全不同的项目，Octop 的主轴是"自托管多用户助手平台"。

一句话：如果你想要一个数据完全留在自己机器上、家人同事能共用、还能接飞书钉钉和 Claude Code 的 AI 助手底座，Octop 是目前这个方向上完成度相当高的开源选项。
