---
title: "Pangolin：20K Stars·零信任远程访问平台·基于WireGuard"
date: "2026-04-12T02:31:39+08:00"
slug: pangolin-zero-trust-remote-access-guide
description: "Pangolin 是一个基于 WireGuard 的零信任远程访问平台，提供身份感知的 VPN 功能。"
draft: false
categories: ["技术笔记"]
tags: ["WireGuard", "VPN", "零信任", "网络安全", "远程访问"]
---

# Pangolin：20K Stars·零信任远程访问平台·基于WireGuard的身份感知VPN

## 一、项目概述

### 1.1 Pangolin 是什么

**Pangolin** 是一个基于 WireGuard 的**开源零信任远程访问平台**，让用户可以安全、便捷地访问私有和公共资源。

> "Pangolin is an open-source, identity-based remote access platform built on WireGuard that enables secure, seamless connectivity to private and public resources."

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | **20.1k** ⭐ |
| Forks | 635 |
| 贡献者 | 88 |
| 最新版本 | v1.17.0 (2026-04-04) |
| 提交数 | 5,624 commits |
| 许可证 | AGPL-3.0 + Fossorial Commercial License |
| 语言 | TypeScript 98.1%, Go 0.9% |

### 1.3 核心定位

| 维度 | 说明 |
|------|------|
| 🔐 **零信任安全** | 细粒度访问控制，非全局网络暴露 |
| 🌐 **远程访问** | 浏览器访问 Web 应用，客户端访问任意资源 |
| 📡 **无需公网 IP** | Site Connectors 穿透防火墙，无需开放端口 |
| 🔑 **身份感知** | 基于身份和上下文的访问控制 |

### 1.4 在线资源

| 资源 | 链接 |
|------|------|
| 🌐 **官网** | https://pangolin.net/ |
| 📚 **文档** | https://docs.pangolin.net/ |
| 💬 **Discord** | https://discord.gg/HCJR8Xhme4 |
| 💼 **Slack** | https://pangolin.net/slack |
| 🐳 **Docker** | https://hub.docker.com/r/fosrl/pangolin |
| 📥 **客户端下载** | https://pangolin.net/downloads |

## 二、核心功能详解

### 2.1 四大核心功能

| 功能 | 说明 |
|------|------|
| 🏢 **Site Connectors** | 轻量级站点连接器，无需公网 IP 或开放端口 |
| 🌐 **反向代理访问** | 身份感知的隧道式反向代理，浏览器访问 Web 应用 |
| 💻 **客户端访问** | 通过 Pangolin 客户端访问 SSH/数据库/RDP 等私有资源 |
| 🔒 **零信任访问** | 仅授予用户明确授权的特定资源，而非整个网络 |

### 2.2 Site Connectors（站点连接器）

```
传统 VPN 问题：
❌ 需要公网 IP
❌ 需要开放端口
❌ 暴露整个网络

Pangolin Site Connector 方案：
✅ 无需公网 IP
✅ 无需开放端口
✅ 安全隧道穿越防火墙
```

**工作原理**：
- Site Connector 主动建立到 Pangolin 控制平面的出站连接
- 远程网络通过加密隧道暴露
- 支持 NAT 穿透和 restrictive firewalls

### 2.3 浏览器反向代理访问

| 特性 | 说明 |
|------|------|
| 🔐 **身份认证** | 用户认证 + 细粒度授权 |
| 🛣️ **智能路由** | 自动路由、负载均衡、健康检查 |
| 📜 **自动 SSL** | 自动 HTTPS 证书 |
| 🌊 **隧道传输** | 通过加密隧道暴露，非直接暴露到互联网 |

### 2.4 零信任访问控制

| 对比 | 传统 VPN | Pangolin |
|------|---------|---------|
| 网络暴露 | 暴露整个网络 | 仅授权特定资源 |
| 攻击面 | 大 | 小 |
| 访问控制 | 网络层 | 应用层 |
| 身份验证 | IP/凭据 | 身份 + 上下文 |

## 三、部署选项

### 3.1 三种部署模式

| 部署方式 | 说明 | 适用场景 |
|----------|------|----------|
| ☁️ **Pangolin Cloud** | 全托管服务，即开即用，按量付费 | 快速上线、无基础设施 |
| 🖥️ **自托管：社区版** | 免费开源，AGPL-3.0 许可证 | 个人/开源项目 |
| 🏢 **自托管：企业版** | Fossorial Commercial License | 企业内部部署 |

### 3.2 Pangolin Cloud

```bash
# 注册账号
访问 https://app.pangolin.net/auth/signup

# 即开即用，按量付费
```

**特点**：
- 无需管理基础设施
- 自动扩展
- 按使用量计费
- 有免费额度

### 3.3 自托管部署

**快速安装**：
```bash
# 查看快速安装指南
https://docs.pangolin.net/self-host/quick-install

# DigitalOcean 一键部署
https://marketplace.digitalocean.com/apps/pangolin-ce-1
```

**Docker 部署**：
```bash
# 拉取镜像
docker pull fosrl/pangolin

# docker-compose 部署
docker-compose up -d
```

## 四、客户端下载

### 4.1 支持平台

| 平台 | 下载链接 |
|------|----------|
| 🍎 **macOS** | https://pangolin.net/downloads/mac |
| 🪟 **Windows** | https://pangolin.net/downloads/windows |
| 🐧 **Linux** | https://pangolin.net/downloads/linux |
| 📱 **iOS** | https://pangolin.net/downloads/ios |
| 🤖 **Android** | https://pangolin.net/downloads/android |

## 五、技术架构

### 5.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Pangolin 技术架构                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │   Browser   │    │   Pangolin  │    │    Site     │   │
│  │   Client    │───▶│   Cloud/    │◀───│  Connectors │   │
│  └─────────────┘    │   Control   │    └─────────────┘   │
│         │           │   Plane     │           │            │
│  ┌──────▼──────┐   └──────┬──────┘   ┌──────▼──────┐   │
│  │   Web App    │          │          │   Private    │   │
│  │   Access    │          │          │   Network    │   │
│  └─────────────┘          │          └─────────────┘   │
│                            │                             │
│  ┌─────────────┐          │          ┌─────────────┐   │
│  │    CLI      │──────────┤          │   Private   │   │
│  │   Client    │          │          │   Resource  │   │
│  └─────────────┘          │          └─────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 核心组件

| 组件 | 说明 |
|------|------|
| **Control Plane** | 控制平面，管理身份、策略、隧道 |
| **Site Connector** | 站点连接器，部署在远程网络 |
| **Client Agent** | 客户端代理，访问私有资源 |
| **Reverse Proxy** | 反向代理，浏览器访问 Web 应用 |

### 5.3 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | TypeScript (Next.js) |
| 后端 | Go, TypeScript |
| 数据库 | PostgreSQL, SQLite |
| 隧道 | WireGuard |
| 认证 | OIDC, OAuth2 |

## 六、安全特性

### 6.1 零信任安全模型

**核心原则**：
- 默认拒绝，最小权限
- 持续验证，不信任网络
- 微分段，仅授权特定资源

### 6.2 身份与访问管理

| 功能 | 说明 |
|------|------|
| 🔐 **OIDC 支持** | 集成企业身份提供商 |
| 👥 **用户组** | 基于组的访问策略 |
| 📋 **资源级别控制** | 细粒度资源授权 |
| 📊 **审计日志** | 完整访问审计 |

### 6.3 网络安全

| 特性 | 说明 |
|------|------|
| 🛡️ **加密隧道** | WireGuard 加密 |
| 🔄 **NAT 穿透** | 无需端口映射 |
| 🌐 **出站连接** | Site Connector 仅需出站连接 |
| 🏷️ **DNS 别名** | 友好的资源命名 |

## 七、应用场景

### 7.1 企业远程办公

```
场景：员工在家或出差访问企业内部系统

传统方案：
❌ VPN 暴露整个网络
❌ 配置复杂
❌ 安全性低

Pangolin 方案：
✅ 仅授权特定应用
✅ 浏览器直接访问
✅ 零信任安全
```

### 7.2 运维管理

```bash
场景：运维人员管理多地机房服务器

Pangolin 功能：
✅ 无需公网 IP
✅ 跨防火墙访问
✅ 审计日志完整
```

### 7.3 物联网安全

```
场景：安全访问分散的 IoT 设备

Pangolin 功能：
✅ Site Connector 轻量部署
✅ 端到端加密
✅ 设备级别授权
```

### 7.4 开发测试环境

```bash
场景：团队访问开发/测试环境

Pangolin 功能：
✅ 快速共享资源
✅ 按需授权
✅ 即时撤销访问
```

## 八、快速开始

### 8.1 注册 Pangolin Cloud

```bash
# 1. 访问注册页面
https://app.pangolin.net/auth/signup

# 2. 创建组织
# 3. 下载客户端
# 4. 开始使用
```

### 8.2 自托管部署

```bash
# 1. 克隆仓库
git clone https://github.com/fosrl/pangolin
cd pangolin

# 2. 复制配置示例
cp docker-compose.example.yml docker-compose.yml

# 3. 启动服务
docker-compose up -d

# 4. 访问管理界面
# 默认端口：8080
```

### 8.3 配置 Site Connector

```bash
# 1. 在目标网络部署 Site Connector
# 2. 配置连接到控制平面
# 3. 验证连接状态
# 4. 开始使用
```

## 九、运维管理

### 9.1 用户管理

| 操作 | 说明 |
|------|------|
| 👤 **添加用户** | 邮箱邀请或手动添加 |
| 👥 **用户组** | 按组批量授权 |
| 🔑 **重置密码** | 管理员可重置 |

### 9.2 资源管理

| 操作 | 说明 |
|------|------|
| ➕ **添加资源** | Web 应用、SSH、数据库等 |
| 🔗 **配置路由** | 资源路径和端口 |
| 🏷️ **DNS 别名** | 友好访问名称 |

### 9.3 监控审计

| 功能 | 说明 |
|------|------|
| 📊 **访问日志** | 完整操作审计 |
| 📈 **使用统计** | 流量、活跃度统计 |
| 🔔 **告警通知** | 异常访问告警 |

## 十、对比竞品

| 特性 | Pangolin | Tailscale | Cloudflare Access |，传统 VPN |
|------|-----------|-----------|-----------------|----------|
| **Stars** | 20.1k ⭐ | - | - | - |
| **开源** | ✅ AGPL-3.0 | ⚠️ 部分开源 | ❌ | ⚠️ 部分开源 |
| **零信任** | ✅ | ✅ | ✅ | ❌ |
| **反向代理** | ✅ | ❌ | ✅ | ❌ |
| **浏览器访问** | ✅ | ❌ | ✅ | ❌ |
| **无需公网 IP** | ✅ | ✅ | ❌ | ❌ |
| **企业版免费** | ✅ | ❌ | ❌ | ⚠️ |

## 十一、许可证说明

### 11.1 许可证结构

| 版本 | 许可证 | 费用 |
|------|---------|------|
| **社区版** | AGPL-3.0 | 免费 |
| **企业版** | Fossorial Commercial License | 免费（年收入<$10万）|

### 11.2 AGPL-3.0 要求

- ✅ 自由使用和修改
- ✅ 自由分发
- 🔗 网络使用时必须开源
- 🔗 衍生作品必须开源

## 十二、资源链接

### 12.1 官方资源

| 资源 | 链接 |
|------|------|
| 🌐 **官网** | https://pangolin.net/ |
| 📚 **文档** | https://docs.pangolin.net/ |
| 💬 **Discord** | https://discord.gg/HCJR8Xhme4 |
| 💼 **Slack** | https://pangolin.net/slack |
| 🐳 **Docker Hub** | https://hub.docker.com/r/fosrl/pangolin |
| 📥 **客户端下载** | https://pangolin.net/downloads |
| 📧 **联系我们** | contact@pangolin.net |

### 12.2 社交媒体

| 平台 | 链接 |
|------|------|
| 🎥 **YouTube** | https://www.youtube.com/@pangolin-net |
| 🐦 **Twitter** | @PangolinVPN |

## 十三、总结

Pangolin 是**新一代零信任远程访问平台**：

| 维度 | 说明 |
|------|------|
| 🔐 **零信任安全** | 细粒度访问控制，最小权限 |
| 🌐 **浏览器访问** | 无需 VPN 客户端，浏览器直接访问 |
| 📡 **无需公网 IP** | Site Connector 出站连接即可 |
| 🔑 **身份感知** | 基于身份和上下文的访问控制 |
| 🆓 **免费选项** | 社区版免费，企业版年收入<$10万免费 |

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/fosrl/pangolin |
| 官网 | https://pangolin.net/ |
| 文档 | https://docs.pangolin.net/ |
| Discord | https://discord.gg/HCJR8Xhme4 |

---

_🦞 本文由钳岳星君撰写，基于 Pangolin (20.1k Stars)_
