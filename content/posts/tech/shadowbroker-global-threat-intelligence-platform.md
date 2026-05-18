---
title: "ShadowBroker：聚合60+情报源的实时地理空间智能平台"
date: 2026-05-18
tags: ["OSINT", "地理空间", "情报", "开源", "Next.js"]
categories: ["工具"]
---

# ShadowBroker：聚合60+情报源的实时地理空间智能平台

**ShadowBroker** 是一个去中心化情报平台，将来自 60+ 实时情报源的公开数据（飞机、船只、卫星、冲突区、CCTV、GPS干扰等）聚合到一张暗色调地图界面上。35+ 可切换数据层，支持 SAR 地表变化检测，多种视觉模式（DEFAULT / SATELLITE / FLIR / NVG / CRT）。右键任意位置可查看国家档案、国家元首资料和最新 Sentinel-2 卫星照片。

<!-- more -->

## 核心功能

### 情报数据层（35+）
- **航空追踪** — 追踪 Air Force One、亿万富翁私人飞机、所有军用飞机 ADS-B 信号
- **舰船追踪** — 25,000+ AIS 船只、渔船活动（Global Fishing Watch）、超级游艇
- **卫星监测** — 军事侦察、SIGINT、SAR、早期预警、空间站 — 按任务类型着色
- **实时 CCTV** — 6个国家 11,000+ 摄像头（伦敦、纽约、加州、西班牙、新加坡等）
- **GPS 干扰区** — 从飞机应答机 NAC-P 退化分析推导实时显示
- **广播监听** — KiwiSDR 短波收音机、警察扫描仪、业余无线电 APRS
- **地质与环境** — 地震、火山、活跃野火（NASA FIRMS）、气象预警、空气质量
- **军事与基础设施** — 军事基地、35,000+ 电厂、2,000+ 数据中心、互联网中断区域
- **SAR 地表变化检测** — NASA OPERA 和 Copernicus EGMS 的毫米级变形监测

### AI Agent 集成
ShadowBroker 内置 HMAC 签名 Agent 命令通道，支持 OpenClaw 及任何支持 Claude/GPT/LangChain 协议的自定义 Agent。Agent 可获得所有 35+ 数据层的读写权限，实时查看地图并执行操作。

### InfoNet 实验性网络
首个内置去中心化情报网格：混淆通信、Dead Drop P2P、嵌入式终端 CLI。无账号、无注册，隐私尚未完全保证（实验性 testnet）。

## 快速启动

```bash
git clone https://github.com/bigbodycobain/Shadowbroker.git
cd Shadowbroker
docker compose pull
docker compose up -d
```

访问 `http://localhost:3000`

> **内存不足？** 默认后端分配 4GB。内存小于 4GB 的机器设置 `BACKEND_MEMORY_LIMIT=3G`，或减少启用的数据源。

## 技术栈

- **前端**: Next.js
- **地图引擎**: MapLibre GL
- **后端**: FastAPI + Python
- **数据源**: 60+ 公开情报 feed

## 免责声明

本工具完全基于公开的开源情报（OSINT）数据构建。不使用任何机密、受限或非公开数据。飞机位置为基于公开报告的估算。军事主题 UI 仅为美学设计。

- GitHub: https://github.com/BigBodyCobain/Shadowbroker