---
title: "Self-Hosting 终极指南：mikeroyal/Self-Hosting-Guide 20.6k Stars 自托管资源合集深度导读"
date: "2026-06-15T21:03:21+08:00"
slug: "self-hosting-guide-mikeroyal-complete-local-hosting-handbook"
description: "mikeroyal/Self-Hosting-Guide 是 20.6k Stars 的自托管资源合集，覆盖 Docker、WireGuard、Home Assistant、Nextcloud 等 34 个主题的中文导读。"
draft: false
categories: ["技术笔记"]
tags: ["Self-Hosting", "自托管", "Docker", "WireGuard", "Awesome List"]
---

## 学习目标

通过本文，你将快速建立对 `mikeroyal/Self-Hosting-Guide` 这份 7000+ 行 README 的整体认知：

- 知道 Self-Hosting 这条赛道在 GitHub 上的代表资源形态与典型读者
- 弄清这份 Guide 的目录结构：从「通用工具」到「按技术栈分类」的双层骨架
- 理解自托管（Self-Hosting）选型时最常遇到的几条技术边界：Docker vs Podman、WireGuard vs Tailscale、Nextcloud vs Synology
- 知道如何把这份 README 当作 awesome-list 使用，而不是把它当作教程逐条执行

---

## 一句话判断

这是一份**自托管领域的 awesome-list**，不是教程合集。它的价值在于把 34 个主题、几百个开源项目按场景组织到一起，让读者在 1-2 小时内完成对整个赛道版图的扫描，而不是替代官方文档或上手教程。

读者用它的方式应该是「按目录定位 → 找到对应主题 → 跳转到对应官方仓库或官网文档」，而不是从头到尾读完。

---

## 仓库基本盘

| 维度 | 数值 |
|------|------|
| 仓库地址 | <https://github.com/mikeroyal/Self-Hosting-Guide> |
| Stars | 20,617 |
| Forks | 1,047 |
| 主语言（仓库） | Dockerfile（实质为 Markdown 资源合集） |
| Topics | authentication, awesome, awesome-list, decentralized, docker-compose, home-assistant, home-automation, linux, oauth, observability, open-source, privacy, raspberry-pi, reverse-proxy, self-hosted, self-hosting, selfhosted, ssh, wireguard |
| License | 未指定（仓库无显式 LICENSE 文件） |
| 首次创建 | 2022-02-06 |
| 最近更新 | 2026-06-15（README 仍在维护，但 `pushed_at` 显示最近一次提交停留在 2025-06-27，更新频率趋于放缓） |
| README 体量 | 约 7,147 行 |

> ⚠️ 仓库没有 LICENSE 文件意味着除 README 内的明确许可声明外，**默认遵循 GitHub ToS**，引用与重分发时建议保留原作者署名（Mike Royal）。

---

## 目录骨架：两层组织

这份 README 的目录设计有清晰的「**先通用工具，再按技术栈分主题**」的双层结构：

### 第一层：通用工具（`Getting Started with Self-Hosting`）

按使用场景分类，覆盖自托管路径上的所有通用工具：

- 容器（Containers）：Docker、Podman、Lima、Colima、Portainer、Containerd 等
- CI/CD：Drone、Woodpecker（Drone 社区分叉）
- Development：Web 服务器、大语言模型（LLMs）、ChatGPT 客户端
- Automation：Ansible 等配置管理工具
- Cloud Storage / Cloud：Linode、DigitalOcean、Back4app、Nextcloud、MinIO
- Databases（SQL / NoSQL 分支）
- Remote Access / Virtualization / Password Management
- SSH / VPN / LDAP / DNS
- Log Management / Service Discovery / Security
- Monitoring / Dashboards / Analytics / Search
- Notifications / RSS / Websites/Blogs
- Social（Nostr / iMessage / Communications）
- Business Management / Collaboration / Encryption
- Backups / Snapshots / Archiving
- Home Server / Media Server / Smart Home
- Voice Assistants / Video Surveillance / TTS / Video & Audio Processing
- Podcasting / Audiobooks / Health / Gardening / Maps / Bookmarks
- Photos / Pastebins / Note-Taking / Time Monitoring / Wikis
- Gaming / Foundations-Projects
- System Hardware / Operating Systems / Storage / File systems / Books / Podcasts / YouTube Channels / Tutorials & Resources / Subreddits

### 第二层：按技术栈分主题（# 顶级章节）

每一节独立成主题，详细展开该方向下的工具链与上手路径：

| 主题 | 覆盖范围 |
|------|----------|
| **WireGuard** | WireGuard 协议本体 + Tailscale/Netmaker 托管方案 + PiVPN/Unraid/pfSense/OpenWRT/Home Assistant 上的部署手册 |
| **Nextcloud** | 自托管云盘 + 协作套件 |
| **Raspberry Pi** | 各型号硬件 + 学习资源 + OS（Home Assistant、Homebridge、ESPHome）+ 升级方案 |
| **Grafana** | 可视化与监控面板 |
| **Networking** | 网络工具集 |
| **Docker** | 容器运行时深度展开 |
| **Kubernetes** | 容器编排 |
| **Ansible** | 配置管理 |
| **Databases** | SQL / NoSQL 数据库 |
| **Telco 5G** | 电信级开源方案 |
| **Open Source Security** | 安全工具、框架、基准 |
| **Differential Privacy** | 差分隐私研究资源 |
| **Machine Learning** | ML 框架与在线学习资源 |
| **IoT Protocols** | IoT 通信协议 |
| **Operating systems** | 操作系统选型 |
| **Middleware** | 中间件 |
| **Node Flow editors** | 节点流编辑器（Node-RED 类） |
| **Toolkits / Data Visualization / Search / Hardware** | 配套工具与硬件 |
| **In-memory data grids** | 内存数据网格 |
| **Home automation** | 智能家居 |
| **Robotics** | 机器人 |
| **Mesh networks** | 网状网络 |
| **Blockchain Development** | 区块链开发 |
| **Node.js / C/C++ / Java / Python / Rust / Swift / XML Development** | 按语言组织的开发资源 |

总计 **34 个独立主题章节**，每一节都遵循「概念 → 工具列表 → 学习资源 → 实战部署（如有）」的统一节奏。

---

## 内容结构特征

### 1. 概念先行，工具后置

每一节开头先用一段话讲清楚该技术是什么、解决了什么问题，再列出相关工具与上手路径。例如 WireGuard 章节：

> WireGuard® is a straight-forward, fast and modern VPN that utilizes state-of-the-art cryptography. It aims to be faster, simpler, leaner, and more useful than IPsec while avoiding the massive headache.

随后才展开 Tailscale（WireGuard 之上的 mesh 网络方案）、Netmaker、以及 PiVPN/Unraid/pfSense/OpenWRT/Home Assistant 五种部署环境的具体操作。

这种结构让它比「单纯工具列表」多了入门门槛的解释，又比「教程」更短，适合在选型阶段快速对齐认知。

### 2. 大量跨项目横向引用

README 全文充斥跨项目引用，例如 Docker 章节直接列出 Kompose（Docker Compose → Kubernetes 转换）、SwarmKit、Containerd、Portainer、Yacht、HashiCorp Nomad 等上下游工具，并把所有可观测性工具（Nginx Proxy Manager、WatchTower、Autoheal、Diun、Dozzle）归在同一节内。

这意味着**单靠 README 无法完成工具间的「决策比较」**，它只告诉你「这些是同类工具」，不直接告诉你「选哪个」。

### 3. 实战部署片段有限

只有少数章节（WireGuard on PiVPN/Unraid/pfSense/OpenWRT/Home Assistant、Raspberry Pi 的 Home Assistant、Back4app Web Deployment 等）给出了具体的命令或操作步骤；其他章节主要停留在「概念 + 工具列表 + 官方链接」层。

---

## 三类典型读者

| 读者类型 | 在这份 README 中找什么 |
|----------|------------------------|
| **刚接触自托管的工程师** | 通用工具层的「Containers / CI/CD / Databases / Monitoring」一站式了解整个栈 |
| **已经在跑 NAS/Home Lab** | 按技术栈章节横向比较同类方案（Portainer vs Yacht、WireGuard vs Tailscale） |
| **采购/选型阶段的架构师** | WireGuard / Nextcloud / Home Assistant / Kubernetes 等主题的快速版本核对，再跳到官方文档做决策 |

---

## 自托管选型常踩的几条边界

把 README 通读一遍，至少能识别出下面几条工程决策点。这些边界在 README 内并未直接给出推荐，但目录结构本身暗示了常见权衡：

### 1. Docker vs Podman

`# Containers` 节同时收录了 Docker 全家桶（Docker Compose、Kompose、SwarmKit、Containerd）和 Podman。两个引擎都符合 OCI（Open Container Initiative）规范，差异主要在：

- **守护进程**：Docker 有 dockerd 单点，Podman 是无守护进程（daemonless）
- **systemd 集成**：Podman 原生支持 systemd，Docker 需 rootful 或 rootless 模式手动配置
- **桌面端生态**：Docker Desktop 是 macOS/Windows 上最成熟的方案；Linux 桌面用户用 Podman 更轻量
- **Compose 兼容**：Podman 4+ 已兼容大部分 Compose 语法，但少部分 Docker 专属特性需要适配

### 2. WireGuard vs Tailscale

README 把 WireGuard 协议、Tailscale（基于 WireGuard 的 mesh VPN）和 Netmaker（自托管版 Tailscale 替代）放在同一节。本质选择是：

| 维度 | 原生 WireGuard | Tailscale | Netmaker |
|------|----------------|-----------|----------|
| 控制平面 | 自建 | 托管（免费层 100 设备） | 自建 |
| NAT 穿透 | 需手动配对 | 自动（DERP 中继） | 自动 |
| 学习成本 | 高（手动管密钥） | 极低 | 中 |
| 数据落地 | 完全私有 | 控制面走 Tailscale | 完全私有 |

### 3. Nextcloud vs 商业云盘

`# Nextcloud` 章节强调「完全自托管 + 协作套件」，但 README 没有对比 Synology Drive、Seafile、FileRun 等同类方案。如果是从云盘迁回自托管，单纯看这份 README 会直接落到 Nextcloud 上，需要额外比较。

### 4. Home Assistant vs 通用智能家居网关

Raspberry Pi 章节把 Home Assistant 放在首位，但同时列出 Homebridge（Apple HomeKit 桥）和 ESPHome（ESP 设备固件）。HA 是「全栈方案」，Homebridge/ESPHome 是「组件方案」，选型取决于用户是想要一站式还是模块化拼装。

### 5. Grafana vs Uptime Kuma vs Promtail

`# Grafana` 和 `# Monitoring`/`# Dashboards` 是分开的两节，意味着这份 README 不替你做可观测性选型——它默认你需要 Grafana + Prometheus + Loki + Promtail 这种「全家桶」，但实际上**轻量级场景下 Uptime Kuma + cAdvisor 的组合更省事**。

---

## 与同类 awesome-list 的对比

| 仓库 | 特点 | 与本指南的关系 |
|------|------|----------------|
| [awesome-selfhosted/awesome-selfhosted](https://github.com/awesome-selfhosted/awesome-selfhosted) | 仅列软件，不做主题展开 | 本指南把 awesome-selfhosted 的工具按场景重新组织 |
| [trimstray/the-book-of-secret-knowledge](https://github.com/trimstray/the-book-of-secret-knowledge) | 偏 IT 运维/网络工具 | 与 Networking、Open Source Security 节有重叠 |
| [kickstartcoding/docker-curriculum](https://github.com/prakhar1989/docker-curriculum) | 真正的 Docker 入门教程 | 本指南的 # Docker 节只做导航，教程要外跳 |
| [kubernetes/website](https://github.com/kubernetes/website) | K8s 官方文档 | 本指南的 # Kubernetes 节相当于目录页 |

简单说：**本指南是 awesome-list 与 topic guide 的混合体**——既不取代 awesome-selfhosted 的纯工具清单，也不像 docker-curriculum 那样一步步带跑。

---

## 推荐使用方式

把它当作一份**带场景感知的 awesome-list 入口**：

1. **第一遍扫描**：直接读 `## Tools for Self-Hosting` 的所有三级标题，记住每个分类下「最有名的 2-3 个项目」即可；
2. **按需深挖**：在选定方向（如 WireGuard）后，跳到 `# WireGuard` 一节读概念与方案，再跳到 Tailscale / Netmaker / PiVPN 等具体官方仓库；
3. **横向比较**：当 README 同一节内出现 ≥3 个同类项目时，自己到各项目主页对比活跃度、issue/PR 节奏、最新 release 日期；
4. **不要照搬部署片段**：只有 WireGuard on PiVPN、Raspberry Pi 上的 Home Assistant、Back4app Web Deployment 等少数子章节给了实战命令；其他「Setting up XX」的章节通常只给了官方文档跳转。

---

## 适用边界与已知问题

- **无 LICENSE 文件**：引用与重分发时需保留作者署名
- **更新频率放缓**：`pushed_at` 最近一次提交停留在 2025-06-27，README 显示 `2026-06-15 updated_at` 来自 GitHub 自动维护性更新（star/topic 同步），不是代码/内容变更
- **实战性较弱**：除少数子章节外，大部分内容停留在「链接索引」层
- **国际化缺失**：README 全英文，没有翻译分支（fork 出的中文化版本未在仓库内提及）
- **Issues/PRs 数量 57+**：作为 awesome-list 仓库，issue 区常出现「建议加入 XX」「建议删除 YY」的争议；维护者响应速度不固定

---

## 总结

`mikeroyal/Self-Hosting-Guide` 是一份**结构清晰、覆盖极广的自托管资源导览**。它的真正价值不在 README 本身的教程深度，而在于：

1. 给刚入自托管赛道的人一张「完整地图」，避免漏掉主流方案
2. 给已经在跑服务的人提供「按技术栈横向索引」，避免每次选型都要从头搜索
3. 给作者 Mike Royal 一份持续维护的个人技术目录，方便在多设备、多项目中复用

如果你只想快速查「Nextcloud 怎么装、WireGuard 用哪个方案、Home Assistant 跑在哪种硬件上」这类问题，这份 README 的目录结构本身已经足够。**但要真正落地任何一个项目，仍需跳转到对应官方仓库或官方文档**——这一点是这份 README 故意保持的边界。

> 项目地址：<https://github.com/mikeroyal/Self-Hosting-Guide>
> 最新提交：2025-06-27
> Stars：20.6k+