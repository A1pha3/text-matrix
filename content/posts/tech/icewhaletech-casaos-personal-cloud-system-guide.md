---
title: "CasaOS 项目导读：把家庭/小型工作室服务器装成个人云的开源方案"
date: "2026-06-25T21:09:51+08:00"
slug: "icewhaletech-casaos-personal-cloud-system-guide"
description: "IceWhaleTech/CasaOS 是一个面向家庭场景的开源个人云系统，主代码用 Go 写、UI 用 Vue 写，提供一行命令安装、App Store、Docker 应用管理、文件/磁盘/系统小部件。本文拆解其系统组件、端口与运行机制、硬件/系统兼容矩阵与维护状态，并给出上手和适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["CasaOS", "个人云", "Go", "Docker", "家庭服务器"]
---

# CasaOS 项目导读：把家庭/小型工作室服务器装成个人云的开源方案

> **目标读者**：想在家用 NUC/旧笔记本/树莓派/家庭服务器上跑个人云的开发者
> **前置知识**：知道 Docker 是什么，会用 SSH 登录 Linux
> **预计阅读时间**：12 分钟 | **难度**：⭐⭐

---

## 一、核心判断

[CasaOS](https://github.com/IceWhaleTech/CasaOS) 是给"家庭场景"设计的个人云操作系统层：把一台装好 Debian/Ubuntu/Raspberry Pi OS 的 x86/ARM 小主机一键变成带 Web UI、Docker 应用市场、文件管理、系统小部件的家庭服务器。

它与 NAS（Network Attached Storage，网络附加存储）系统（如 TrueNAS、OpenMediaVault）的根本差异是把"应用管理"提到与"文件管理"同等地位：内置 App Store 可以一键装 Nextcloud、HomeAssistant、AdGuard、Jellyfin、*arr 全家桶等 100,000+ Docker 应用，UI 设计是"所见即所得"，不要求用户具备命令行或 Docker 知识。

当前仓库状态：34,504 stars、1,977 forks，Go + Vue，Apache-2.0 协议，2021-09-26 创建，最近一次代码 push 时间为 2025-08-06，2026-06-25 仓库元数据仍有更新（主页/issue 等）。最新稳定版 v0.4.15 发布于 2024-12-19，v0.4.17-alpha1 发布于 2025-04-17。

## 二、系统地图

CasaOS 在仓库里只是一个"网关入口"，完整系统由多个子仓库组合：

| 组件 | 角色 | 关键依赖 |
|------|------|----------|
| `CasaOS`（本仓） | 网关主进程，负责路由、文件、磁盘、应用管理 API | Go 1.x、SQLite、Redis、GoSystemd |
| `CasaOS-UI` | Web 前端（Vue） | 与网关同源部署 |
| `CasaOS-AppStore` | 应用市场索引 | 静态 JSON + 社区维护 |
| `CasaOS-UserService` | 用户管理与多用户 | — |
| `CasaOS-LocalStorage` | 本地存储抽象 | — |
| `CasaOS-MessageBus` | 事件总线（WebSocket） | OpenAPI 规范在主仓 `api/` 下生成 |
| `CasaOS-Common` | 共享 model / utils | 多个子仓共用 |

主仓 `main.go` 启动后通过 `route.InitV1Router`/`InitV2Router` 暴露 `/v1`、`/v2` 两套 API，再把 OpenAPI 文档挂到 `/doc`。`api/casaos/openapi.yaml` 通过 `oapi-codegen` 在 `go:generate` 阶段直接生成 Go 类型与服务端代码：

```go
//go:generate bash -c "mkdir -p codegen && go run github.com/deepmap/oapi-codegen/cmd/oapi-codegen@v1.12.4 \
//  -generate types,server,spec -package codegen api/casaos/openapi.yaml > codegen/casaos_api.go"
```

主仓 `route/` 下有 `v1.go` / `v2.go` / `init.go` / `periodical.go` 四个核心文件；`service/` 下按领域切成 `app.go`、`file.go`、`storage.go`、`system.go`、`notify.go`、`peer.go`、`socket.go`、`health.go` 等。

## 三、关键子系统

### 3.1 应用管理

`/v1/apps`、`/v1/app_management` 一类接口把 Docker 引擎包成 CasaOS 的"应用"概念。每个应用在文件层是一段 docker-compose（Docker 的多容器编排格式）描述，UI 层呈现为图标 + 状态 + 资源占用 widget。应用市场 (`/v1/app_store`) 走标准 JSON feed，安装/升级/卸载全部走 Docker 引擎封装。

### 3.2 文件管理

`/v1/file`、`/v1/folder`、`/v1/batch`、`/v1/image` 接口负责文件上传、下载、批量操作。底层走 `pkg/fs`、`pkg/samba` 共享到局域网 SMB（Server Message Block，Windows 文件共享协议）客户端；Samba 配置在 `pkg/samba/`。

### 3.3 磁盘与存储

`/v1/storage`、`/v1/driver` 把 Linux 块设备、ZFS、exFAT、NTFS、ext4 等多种文件系统抽象成"驱动器"概念，UI 上像 macOS 一样拖动就能挂载。

### 3.4 消息总线与实时状态

`MessageBus` 是 WebSocket 实现，硬件状态、App 状态、通知事件通过它推到前端。`main.go` 里 `route.SendAllHardwareStatusBySocket` 用 `cron` 每 5 秒推一次硬件指标。

### 3.5 系统小部件

`pkg/config` + `route/periodical.go` 周期性收集 CPU、内存、磁盘、网络指标，前端 widget 直接消费 MessageBus 推送。

## 四、硬件与系统兼容矩阵

README 显式列出的支持范围：

| 架构 | 状态 |
|------|------|
| amd64 / x86-64 | ✅ |
| arm64 | ✅ |
| armv7 | ✅ |

| 系统 | 状态 |
|------|------|
| Debian 12 | ✅ 官方推荐 |
| Ubuntu Server 20.04 | ✅ |
| Raspberry Pi OS | ✅ |
| Elementary 6.1 | ✅ 社区支持 |
| Armbian 22.04 | ✅ 社区支持 |
| Alpine | 🚧 |
| OpenWrt | 🚧 |
| ArchLinux | 🚧 |

典型部署目标：ZimaBoard（项目原本就是 ZimaBoard 众筹产品预装系统）、Intel NUC、树莓派、旧笔记本、淘汰 PC。

## 五、最小上手流程

一行安装（任选其一）：

```sh
wget -qO- https://get.casaos.io | sudo bash
# 或
curl -fsSL https://get.casaos.io | sudo bash
```

装完后：

1. 浏览器打开 `http://<服务器IP>`，初始化管理员账号。
2. 第一次登录会被提示绑定 CasaOS 账户（用于跨设备同步应用配置和远程访问）。
3. App Store 选 Nextcloud、Jellyfin、AdGuard 等一键装。
4. 在系统设置里挂载硬盘/USB 设备，文件 widget 立刻能看到。
5. 终端内 `casaos -v` 看版本；`casaos-uninstall` 卸载（v0.3.3+）。

升级走 `Settings → Update` 内的 UI，或在 SSH 终端里：

```sh
wget -qO- https://get.casaos.io/update | sudo bash
# 或
curl -fsSL https://get.casaos.io/update | sudo bash
```

## 六、命令与配置清单

主进程监听本地回环端口（启动时 `net.Listen("tcp", "127.0.0.1:0")` 让系统分配端口），由前端反向代理暴露 80/443。常见路由前缀：

```text
/v1/sys         系统信息
/v1/port        端口管理
/v1/file        文件读写
/v1/folder      目录管理
/v1/batch       批量任务
/v1/image       镜像/图标
/v1/samba       SMB 共享
/v1/notify      通知
/v1/driver      驱动器
/v1/cloud       云端同步
/v1/recover     恢复
/v1/other       杂项
/v1/zt          ZeroTier
/v1/test        自检
/doc            API 文档
```

主进程在开机时由 systemd 拉起（`go-systemd/daemon` 库做了 watchdog 通知），所有数据落在 `RuntimePath` 下的 SQLite 数据库。

## 七、维护状态与边界

几个值得在采用前评估的点：

- **更新节奏放缓**：v0.4.15 稳定版之后只有 v0.4.17-alpha1 在 2025-04 之后没有再发新版，主仓最后一次 push 是 2025-08-06。如果你追求"持续更新"，需要看 issue 跟踪。
- **依赖较重**：CasaOS 网关 + Docker + Samba + ZeroTier + 系统小部件，对于只想跑一个 Nextcloud 的用户来说，包络偏大。
- **官方云服务依赖**：默认会引导注册 CasaOS 账户并启用 ZeroTier，介意云端绑定的需要手动关掉。
- **企业级场景不推荐**：CasaOS 官方定位就是"home scenario"，对 RBAC（Role-Based Access Control，基于角色的访问控制）、审计、多租户等需求没有原生支持。

## 八、采用顺序与适用人群

| 场景 | 推荐度 | 说明 |
|------|--------|------|
| 家用 NAS 替代 + 跑几个 Docker 服务 | ⭐⭐⭐⭐⭐ | 一行命令搞定门槛最低 |
| 小型工作室文件共享 + 媒体服务器 | ⭐⭐⭐⭐ | Jellyfin + Nextcloud 组合是社区主流用法 |
| 教学/演示用家庭服务器 | ⭐⭐⭐⭐ | UI 直观，零命令行基础也能用 |
| 生产级企业 NAS | ⭐⭐ | 缺审计、缺高可用、缺 SLA |
| 单容器边缘网关 | ⭐⭐ | 系统开销过大 |

CasaOS 的核心价值是把"家用服务器"这个概念从"装 Linux + 装 Docker + 写 compose"压缩到"插电源、跑一行命令、打开网页装应用"。如果你的目标人群是家庭或非技术背景的成员，这个抽象层是合适的；如果是给企业或 7×24 跑关键服务的场景，再看 TrueNAS Scale、Unraid 这类更"严肃"的方案。
