---
title: "S-UI：SagerNet/Sing-Box 多协议 Web 管理面板快速上手"
date: "2026-05-22T03:00:00+08:00"
slug: "s-ui-sing-box-web-panel-quickstart"
description: "S-UI 是基于 SagerNet/Sing-Box 的高级 Web 管理面板，支持 VLESS、VMess、Trojan、Shadowsocks 等多协议代理，提供流量监控、订阅服务、客户端管理与 Dark/Light 主题，适合需要图形化管控代理节点的用户快速部署使用。"
draft: false
categories: ["技术笔记"]
tags: ["Sing-Box", "SagerNet", "代理面板", "多协议", "网络工具"]
---

# S-UI：SagerNet/Sing-Box 多协议 Web 管理面板快速上手

S-UI 是一个构建在 SagerNet/Sing-Box 之上的高级 Web 管理面板，目前在 GitHub 已有约 8900 颗星、1500 个 Fork。项目核心目标是让用户通过图形界面管理多种代理协议节点，无需手工编辑配置文件即可完成节点接入、流量监控和订阅分发。

本文面向有代理协议使用基础、想通过 Web 面板集中管理多个节点的技术用户，介绍如何快速完成安装、配置核心功能和日常使用边界。

<!--more-->

## 系统定位

S-UI 本质上是一个**前端交互层 + 后端 Go 服务**，它调用 Sing-Box 的 API 来管理节点配置和收集流量数据。Sing-Box 负责底层代理能力，S-UI 负责把这些能力暴露成可操作的图形界面。

所以 S-UI 是 Sing-Box 的可视化管控工具，不是代理协议实现。它的主要能力在于：

- **多协议统一接入**：一个面板管理 VLESS、VMess、Trojan、Shadowsocks、Hysteria、TUIC 等多种协议节点。
- **多客户端/ inbound 管理**：同面板下管理多个客户端，每个客户端可以单独设置流量限额和过期时间。
- **订阅服务**：内置订阅生成器，支持 link/json/clash+info 三种格式。
- **流量可视化**：实时展示每个 inbound 的流量使用情况以及系统状态。
- **多语言界面**：支持英语、波斯语、越南语、简体中文、繁体中文、俄语。

> ⚠️ 项目免责声明明确指出：该软件仅用于个人学习与沟通，请勿用于非法用途，请勿在生产环境中使用。

## 快速安装

### Linux / macOS 一键脚本

```sh
bash <(curl -Ls https://raw.githubusercontent.com/alireza0/s-ui/master/install.sh)
```

脚本会自动检测操作系统和 CPU 架构，适配 amd64、arm64、armv7、armv6、armv5、386、s390x 等平台。安装完成后面板运行在 **2095 端口**，订阅服务运行在 **2096 端口**，默认账号密码均为 `admin`。

### Windows

1. 从 [GitHub Releases](https://github.com/alireza0/s-ui/releases/latest) 下载最新的 Windows 包（如 `s-ui-windows-amd64.zip`）。
2. 解压到任意目录。
3. 以管理员身份运行 `install-windows.bat`，按向导完成安装。
4. 安装完成后访问 http://localhost:2095/app。

### Docker 部署

```shell
mkdir s-ui && cd s-ui
wget -q https://raw.githubusercontent.com/alireza0/s-ui/master/docker-compose.yml
docker compose up -d
```

容器暴露的端口为 2095（面板）、2096（订阅）、443、80，数据目录映射到 `db/` 和 `cert/`。

### 环境变量配置

| 变量 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `SUI_LOG_LEVEL` | string | `"info"` | 日志级别：debug/info/warn/error |
| `SUI_DEBUG` | boolean | `false` | 开启调试模式 |
| `SUI_BIN_FOLDER` | string | `"bin"` | 二进制文件目录 |
| `SUI_DB_FOLDER` | string | `"db"` | 数据库文件目录 |
| `SINGBOX_API` | string | - | 外部 Sing-Box API 地址 |

## 核心功能一览

### 支持的协议

S-UI 对接 Sing-Box，支持以下协议族：

**通用协议**：Mixed、SOCKS、HTTP、HTTPS、Direct、Redirect、TProxy

**V2Ray 系协议**：VLESS、VMess、Trojan、Shadowsocks

**其他协议**：ShadowTLS、Hysteria、Hysteria2、Naive、TUIC

同时支持 XTLS 协议，以及透明代理、SSL 证书、端口管理等高级路由配置。

### inbound 管理

每个 inbound 代表一个客户端接入点。面板支持为每个 inbound 设置：

- 通信协议和加密参数
- 流量上限（traffic cap）和到期时间
- 启用/禁用状态

inbound 列表页会实时展示每个客户端的连接数和流量消耗，方便判断哪些节点压力较大。

### 订阅服务

面板内置订阅生成器，无需额外配置即可对外提供订阅链接。支持的格式：

- **通用 link**：原始节点链接
- **JSON**：节点配置 JSON 格式
- **Clash + info**：Clash 格式并附带节点信息

订阅服务默认端口 2096、路径 `/sub/`。可以通过环境变量或配置文件修改端口和路径。

### 主题与多语言

面板支持 Dark/Light 主题切换，界面语言目前支持英、中（简/繁）、波斯、越南、俄语共 6 种语言。

## 一个 inbound 的完整接入流程

以创建一个 VLESS + TLS 的 inbound 为例，走一遍面板的标准操作路径：

1. 登录面板（默认 http://localhost:2095/app，账号 admin/admin）。
2. 进入 **Inbound** 管理页，点击 **Add Inbound**。
3. 选择协议类型为 **VLESS**，填写节点标签和端口。
4. 设置传输层参数（TLS 证书路径、域名、SNI 等）。
5. 填写客户端 UUID（可用面板一键生成）。
6. 设置流量限额和过期时间（可选）。
7. 保存。此时面板会通过 Sing-Box API 注册这个 inbound，并返回节点链接或订阅地址。

订阅格式的选择取决于客户端：普通代理工具通常使用 link 格式，Clash 系列客户端使用 Clash 格式。

这个流程覆盖了面板最常用的场景。如果需要做端口映射、域名分流或 PROXY Protocol 配置，可以在 inbound 高级设置里找到对应选项。

## 常见坑点

**端口被占用**：安装脚本不会自动检查 2095/2096 端口是否已被占用。如果安装失败，先确认端口状态或手动修改配置。

**订阅链接打不开**：检查防火墙是否放行 2096 端口，订阅路径是否被 URL 过滤工具拦截。Clash 格式的订阅在部分客户端里可能需要 Base64 解码后才能使用。

**Docker 部署时数据目录权限**：映射 `db/` 目录时如果遇到写入权限问题，确认容器内运行用户对主机目录有写权限，或者在 docker-compose 里以 `user: uid:gid` 方式指定。

**多客户端流量统计**：面板统计的是 S-UI 已注册的 inbound 流量，如果节点直连绕过 Sing-Box，流量不会被计入。

## 适用边界

S-UI 适合以下场景：

- 个人或小团队管理 3~10 个代理节点，需要图形化配置而不是改配置文件。
- 需要为不同用户/设备分配独立账号和流量配额。
- 需要集中生成多个客户端的订阅链接。

不适合以下场景：

- 需要在生产环境长期运行（项目明确不建议）。
- 需要对海量节点做精细化路由策略（面板提供基础的路由配置，但深度定制仍需编辑 Sing-Box 配置文件）。
- 对安全审计有严格要求的环境（面板默认账密简单，建议安装后立即修改密码并启用 TLS）。

## 项目结构速览

S-UI 后端采用 Go 编写，主要目录结构如下：

| 目录 | 作用 |
|------|------|
| `api/` | REST API 路由定义 |
| `app/` | inbound/用户/订阅等业务逻辑 |
| `cmd/` | 命令行入口 |
| `config/` | 配置加载与校验 |
| `core/` | 核心业务逻辑 |
| `database/` | 数据持久化（SQLite） |
| `network/` | 网络相关处理 |
| `service/` | 系统服务（定时任务、健康检查） |
| `sub/` | 订阅生成器 |
| `web/` | 前端静态文件（编译后） |
| `middleware/` | HTTP 中间件 |

前端代码在独立的 [s-ui-frontend](https://github.com/alireza0/s-ui-frontend) 仓库，作为 git submodule 引入主项目。

## 维护状态

项目最近一次提交为 2026-05-19，距今约 2 天（数据采集时），维护活跃度高。GitHub Issues 约有 39 个 open issues，说明社区反馈活跃。License 为 GPL-3.0。

## 参考链接

- GitHub：https://github.com/alireza0/s-ui
- 前端仓库：https://github.com/alireza0/s-ui-frontend
- Telegram 群组（官方支持）：https://t.me/XrayUI
- API 文档：https://github.com/alireza0/s-ui/wiki/API-Documentation