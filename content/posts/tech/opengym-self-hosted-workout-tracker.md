---
title: "openGym：自托管健身追踪器，数据真正归你所有"
date: 2026-10-07T03:24:10+08:00
slug: "opengym-self-hosted-workout-tracker"
github_repo: "DuarteSantos8/openGym"
source_key: "gh:DuarteSantos8/openGym"
description: "openGym 是一个自托管的健身房与自重训练追踪器，支持计划编排、引导式训练、肌肉疲劳热力图与 FitNotes/Strong/Hevy 数据导入，数据存放在自己服务器上，配合 Passkey 登录与多端同步。"
draft: false
categories: ["技术笔记"]
tags: ["自托管", "健身", "PWA", "开源"]
---

## 为什么值得关注 openGym

健身追踪类应用有一个共同的问题:你的训练数据存在别人的服务器上,公司倒闭或产品转型时,数据可能随之消失。openGym 选择了一条相反的路线——**数据放在你自己的服务器、你自己的文件夹里**。

这个项目 2026 年 7 月创建,不到三个月已经积累了超过 5,400 星。它不是一个原型 demo,而是一个功能完整的现代应用:可安装到主屏幕的 PWA(Progressive Web App)、Passkey 登录、离线可用、手机与电脑之间同步,全部跑在一条 `docker compose up` 命令之后。

## 它解决什么问题

主流的健身 App 通常把数据留在服务端,靠订阅制盈利。openGym 的核心判断是:**训练数据是用户的资产,应该由用户自己保管**。

- 无账号体系依赖:用 Passkey(人脸、指纹)登录,不绑第三方账户
- 无订阅、无广告、无遥测
- 数据在你自己控制的文件夹里,可以随时导出为一份 JSON
- 可 fork:整个项目是 AGPL v3 协议,想改就改

它依然具备现代应用该有的体验,而不是一个"能用但难用"的自托管玩具。

## 核心能力

**训练计划编排**

- 内置 1,324 个动作库,带动画演示,可按肌肉群在身体地图上浏览,按自有器械过滤
- 四个起步计划(Push/Pull/Legs、Upper/Lower、全身、5×5)可直接加载为可编辑的常规计划
- 支持超级组、热身组、递减组、休息暂停、计时动作(平板支撑、悬挂、农夫行走)、按时间与速度计的有氧、每动作独立休息时间、计划性减载
- 可以创建自己的动作,上传自己的照片、GIF 或短视频;上传前设备端会剥离位置信息

**引导式训练**

- 今日训练自动开始,重量从上次记录自动预填,组间休息计时器自动运行,训练中自动识别 PR(个人纪录)
- 安静的训练界面:每个动作一个菜单,组号就是菜单本身
- 可选 RIR(Reps in Reserve,预留次数)或 RPE(自感用力度)记录,带颜色与通俗解释
- 杠铃片计算:根据你拥有的片重,自动算出身前杠、EZ 杠、陷阱杠、史密斯机需要加几片
- 自重动作知道自身不带负荷:只记次数,用负重腰带时额外记录

**进度追踪**

- 每个计划或动作可选线性、Greyskull LP、双进阶(可见次数区间)或加时间等进阶规则,每个目标都解释为什么是这个数字
- 估算 1RM(单次最大重量),带独立曲线;结构性平衡比率(Poliquin、Thibaudeau、ATG)
- 一年活动热力图;肌肉地图三种模式:训练量分布、恢复中、久未训练
- 体重曲线可对照目标线;训练后可以事后编辑、补记纸面记录、调整日期

**账户与数据**

- Passkey 登录,数据按档案在多设备间同步;每个实例可切换为密码登录;新设备用一次性代码或二维码配对
- 两台设备同时编辑会合并而不是互相覆盖
- 支持从 FitNotes、Strong、Hevy(CSV 或 API key)以及 Apple Health 体重数据导入;随时导出全部数据为 JSON
- 17 种语言,包括从右到左的阿拉伯语

**可选的 AI 扩展(默认关闭)**

- AI 教练:起草一周训练计划,之后根据你的记录建议调整,每次改动都由你确认;运行在你自己服务器上,用自己的 API key(Anthropic、OpenAI、Gemini 或任何兼容 OpenAI 的端点,含 Ollama)
- MCP 服务器:让 Claude Desktop 之类的助手能回答关于你训练历史的问题;只读、本地,不参与 Docker 构建

## 快速开始

前置条件:Docker 与 Docker Compose。

```bash
git clone https://github.com/DuarteSantos8/openGym
cd openGym
cp .env.example .env
docker compose pull      # 预构建镜像,amd64 + arm64
docker compose up -d
```

打开 `http://localhost:8080`,点击 **Create profile** 即可开始。首次启动会下载一次动作媒体(约 140 MB)。

要在手机上用 Passkey 登录,需要域名上的 HTTPS,`.env` 里改两行即可。自托管指南覆盖 Cloudflare Tunnel、Caddy、Traefik 和 nginx 四种方式,另有局域网 HTTPS 与 Kubernetes 专项指南。

## 适用边界

- **需要自托管环境**:没有 Docker 或不想维护服务器,不适合;官方 demo 可以先体验
- **追求数据主权**:这是最核心的卖点;如果不在意数据归属,主流的免费 App 也够用
- **移动端体验**:PWA 可安装、可离线,但不是原生 App;对原生性能有强需求需要评估
- **数据迁移成本**:提供 FitNotes/Strong/Hevy 导入,迁移路径是现成的

## 阅读路径

- 想立刻上手:README 的 Quick start + `docs/SELF_HOSTING.md`
- 想了解同步原理:README 的 "How sync works"
- 想接入 AI 教练:`docs/AI_COACH.md`
- 想了解迭代节奏:CHANGELOG.md 按版本记录了全部变更
