---
title: "CasaOS 项目导读：一行命令装出个人云，主仓停更一年后还值得装吗"
date: "2026-06-25T21:09:51+08:00"
lastmod: "2026-10-02T00:00:00+08:00"
slug: "icewhaletech-casaos-personal-cloud-system-guide"
github_repo: "IceWhaleTech/CasaOS"
source_key: "gh:IceWhaleTech/CasaOS"
description: "IceWhaleTech/CasaOS 是面向家庭场景的开源个人云系统，由九个组件拼成，一行命令装在裸 Linux 上。本文基于 2026-10 的仓库读数与源码核查，拆解它的组件地图、应用管理链路与运行机制，并给出主仓停更一年后的采用判断：什么人今天还适合装它，什么人应该转向 ZimaOS。"
draft: false
categories: ["技术笔记"]
tags: ["Go", "Docker", "NAS", "ZimaOS"]
---

# CasaOS 项目导读：一行命令装出个人云，主仓停更一年后还值得装吗

> **目标读者**：想在家用 NUC/旧笔记本/树莓派/家庭服务器上跑个人云的开发者
> **前置知识**：知道 Docker 是什么，会用 SSH 登录 Linux
> **预计阅读时间**：12 分钟 | **难度**：⭐⭐

---

## 一、开场判断

[CasaOS](https://github.com/IceWhaleTech/CasaOS) 是给"家庭场景"设计的个人云操作系统层：把一台装好 Debian/Ubuntu/Raspberry Pi OS 的 x86/ARM 小主机一行命令变成带 Web UI、Docker 应用市场、文件管理、系统小部件的家庭服务器。

2026 年 10 月回头看这个项目，事实是这样的：主仓 main 分支最后一次代码提交停在 2025-08-06（改的还是 README），最新稳定版 v0.4.15 发布于 2024-12-19，此后的 v0.4.17-alpha1（2025-04-17，加入 RISC-V 初始支持）再无后续。但这个项目并没有被丢弃——官方应用商店 2026 年 9 月还在更新应用版本；2026-09-28，官方在主仓、用户服务、应用管理三个仓库的同名分支里同步提交了一批认证安全修复；它的继任者 ZimaOS 每隔几周发一个版本。开发重心挪走了，系统本身还在被维护。

所以本文要回答的其实是三个问题：这套系统由什么组成、装上之后日常怎么用、以及站在今天，什么人还适合装它。

## 二、系统地图：九个组件拼成的一套系统

先纠正一个常见误解：GitHub 上的 `IceWhaleTech/CasaOS` 仓库不等于 CasaOS 这套系统。一键安装脚本（v0.4.16）实际部署的是九个组件的组合，以七个 systemd 服务的形式运行：

| 组件 | systemd 服务 | 安装版本 | 职责 |
|------|--------------|----------|------|
| CasaOS（主仓） | `casaos.service` | v0.4.15 | 文件、磁盘、系统信息的 API 服务 |
| CasaOS-Gateway | `casaos-gateway.service` | v0.4.9-alpha4 | Web 入口，对外暴露 80/443 |
| CasaOS-UI | （静态文件） | v0.4.25 | Vue 前端 |
| CasaOS-AppManagement | `casaos-app-management.service` | v0.4.10-alpha2 | 应用安装/启停/卸载（docker compose 封装） |
| CasaOS-UserService | `casaos-user-service.service` | v0.4.8 | 用户账号管理 |
| CasaOS-LocalStorage | `casaos-local-storage.service` | v0.4.4 | 本地存储与挂载抽象 |
| CasaOS-MessageBus | `casaos-message-bus.service` | v0.4.4-3-alpha2 | 组件间事件总线 |
| CasaOS-CLI | — | v0.4.4-3-alpha1 | `casaos` 命令行 |
| rclone | `rclone.service` | v1.61.1 | 云存储挂载 |

组件之间有一个有趣的不对称：主仓坐拥 37,292 star（2026-10-02 读数），而真正承担应用管理的 CasaOS-AppManagement 只有 26 个 star。给这个项目点星的人，大多数并没有打开它的仓库地图——名气在主仓，代码在别处。

各组件是独立发版的：主仓停在 v0.4.15，UI 却已经走到 v0.4.25。日常"升级 CasaOS"实际是升级一组版本号各异的二进制，这也是后面讨论维护状态时要留意的点。

## 三、主仓里有什么：文件、存储、系统三条主线

主仓当前有 146 个 Go 文件，`go.mod` 声明 Go 1.21。它监听本机回环地址的随机端口（`main.go` 里 `net.Listen("tcp", net.JoinHostPort(LOCALHOST, "0"))`），对外流量由 Gateway 转发。API 按三代并存的组织方式挂在 `main.go` 的 `HandlerMultiplexer` 上：

```text
v1   echo 手写路由     文件/磁盘/系统/SMB/ZeroTier 等大部分功能
v2   OpenAPI 代码生成  文件上传等重构后的接口
v3   文件路由          新一代文件接口
doc  API 文档页
```

`route/v1.go` 注册了 v1 的全部前缀，可以当作主仓能力清单来读：

```text
/v1/sys      系统信息、版本检查、CPU/内存/磁盘利用率
/v1/port     端口占用检查
/v1/file     文件读写、上传、WebSocket 传输
/v1/folder   目录管理、大小统计
/v1/batch    批量复制/移动/删除
/v1/image    图片读取
/v1/samba    SMB 连接与共享管理
/v1/cloud    云存储（rclone 挂载）的列表与卸载
/v1/driver   磁盘驱动器列表
/v1/notify   通知
/v1/other    全局搜索
/v1/zt       ZeroTier 本地 API 代理
```

三条值得展开的主线：

**文件与存储。** 文件操作横跨 v1/v2/v3 三代路由——新一代 v3 甚至整个只为文件而设，可见重构的倾斜程度。磁盘管理把 Linux 块设备、ext4/NTFS/exFAT 等文件系统抽象成"驱动器"，UI 上点一下即可挂载；`/v1/cloud` 背后是 rclone，挂载云盘后和本地目录一样出现在文件管理器里。SMB 共享（连接与共享两套子资源）由 `/v1/samba` 管理，底层配置生成在 `pkg/samba/`。

**系统状态推送。** `main.go` 起了一个每 5 秒触发一次的定时器（`robfig/cron/v3`，`@every 5s`），反复调用 `route.SendAllHardwareStatusBySocket` 把 CPU、内存、磁盘、网络指标经 WebSocket 推给前端——首页那些实时跳动的小部件，数据源就在这里。组件间的事件则走独立的 MessageBus 服务，主仓启动时通过生成的客户端（oapi-codegen 从 MessageBus 的 OpenAPI 规范生成）向总线注册自己会发布的事件类型。

**认证模型。** v1 路由挂了 JWT 中间件，但跳过条件是请求来源为本机回环地址（`127.0.0.1` / `::1`）——设计意图是组件间本地调用免认证。这个"本机请求跳过 JWT"的逻辑正是后文 2026-09-28 安全修复的主题，此处先记下。

API 的生成方式也值得一提：`main.go` 头部两条 `go:generate` 指令，分别用 `oapi-codegen@v1.12.4` 从本地 `api/casaos/openapi.yaml` 生成服务端代码、从 MessageBus 仓库的在线规范生成客户端代码。接口定义即代码，这是 v0.4.x 架构拆分后维持多仓库协作一致性的手段。

## 四、应用从哪来：AppStore 与 AppManagement

这是原仓库里最容易被误解的部分。应用管理**不在主仓**——主仓的 v1 路由里找不到 `/v1/apps` 之类的路由，安装、启停、卸载应用全部由独立的 CasaOS-AppManagement 服务负责，它把每个应用描述成一段 docker compose 配置来管理。

应用清单来自 CasaOS-AppStore 仓库。这个仓库的现状很能说明项目的真实生态：

- `Apps/` 目录下有 178 个官方精选应用（AdGuard Home、Jellyfin、Nextcloud、*arr 系列等），仓库 2026-09-24 还在提交——OpenClaw 更新到 2026.9.6、Transmission 更新到 4.1.3，都是最近两周的事；
- README 标题已经改成 "ZimaOS AppStore Source"，同时保留 legacy v1 兼容输出，让 CasaOS v0.4.x 这类老客户端继续消费同一份商店数据；
- 第三方应用商店列表维护在 awesome.casaos.io，装第三方源即可扩展清单。

主仓 README 说 "Over 100,000 apps from the Docker ecosystem can be easily installed"，注意这个口径指的是 Docker 生态里的应用可以经"自定义安装"（填一段 compose）接入，不是商店里躺着一百万个一键应用。精选一键装的是那 178 个，其余靠 compose 自行接入。

一个应用从点击到跑起来的完整流转是这样的：在 UI 的应用商店里点 Jellyfin 的"安装"→ 请求经 Gateway 转给 AppManagement 服务 → 它从 AppStore 的 feed 拉取该应用的 compose 定义 → 调 Docker 引擎拉镜像、起容器 → 运行状态经 MessageBus 推回 UI，变成应用列表里那个亮起的图标。理解这条链路，排查"商店装不上/图标转圈"时才知道该看哪个组件的日志。

## 五、维护状态：停更的时间线，与没有停下的部分

把仓库时间线摆出来，比一句"更新放缓"更有用：

```text
2024-12-19  v0.4.15 稳定版（迄今最新）
2025-04-17  v0.4.17-alpha1（RISC-V 初始支持，此后再无 release）
2025-08-06  main 分支最后三次提交（更新 README）
2025-11-11  issue #2390：Debian/Ubuntu 升级 Docker 5.29 后 Web UI 应用列表失效
2026-07     社区 PR 仍有人提交，但以关闭告终、未合并（#2524 对齐 Go 版本、#2548 文件更新）
2026-09-28  主仓/用户服务/应用管理三仓库同步提交认证安全修复
```

两个方向的事实都要看到。

**停更的代价是真实的。** issue #2390 是个典型样本：2025 年 11 月起，Debian/Ubuntu 用户 apt 升级 Docker 到 5.29 后，CasaOS 的 Web UI 应用列表整个失效， issue 挂了 10 个月、26 条评论，没有修复发布。上游 Docker 不会等你，这正是"壳模式"（装在裸 Linux 上的管理层）的固有风险——底座变了，壳没人改就裂。

**维护也没有完全停止。** 2026-09-28 那批修复值得细看：三个仓库各有一个 `fix/local-jwt-origin` 分支，提交信息同为 "fix(auth): validate local origin before skipping JWT"，主仓还补了 debug 端点的保护与测试。对照上一节说的"本机回环请求跳过 JWT"逻辑，这批修复补的正是跳过认证时缺失的来源校验。同一天、三个仓库、同一主题——这是一次协调的安全维护动作。但要清楚它的现状：**全部停留在分支上，没有进入 main，更没有打包成任何发布版本**。已安装的用户不会收到。

官方的演进重心在 ZimaOS。ZimaOS 的 README 写得明白："ZimaOS is evolved from CasaOS"——从 CasaOS 演化而来的整机操作系统，基于 Buildroot 构建、带 OTA 更新，v1.7.1（2026-08-21）与 v1.8.0-beta1（2026-09-24）保持约每月一版的节奏；更远处还有 ZimaOS-Blue（官方描述为 Local-First Agent Runtime，2026-05 启动）这样的新尝试。CasaOS 仓库的 SECURITY.md 自述"active development、v1.0 前支持有限"，按上面这条时间线看，这句自述已明显滞后于现实，漏洞报告邮箱（wiki@casaos.io）仍然有效。

给"维护状态"下个结论：**CasaOS v0.4.x 处于"安全维护模式"——不再加功能、基本不修非安全 bug，安全修复在做但不发版；商店数据源因与 ZimaOS 共用而持续新鲜；真正的产品迭代在 ZimaOS。**

## 六、上手与日常维护

安装（脚本已验活，2026-10-02 返回 200）：

```sh
wget -qO- https://get.casaos.io | sudo bash
# 或
curl -fsSL https://get.casaos.io | sudo bash
```

装完之后的几件事：

1. 浏览器打开 `http://<服务器IP>`，初始化向导一共三步：欢迎页、创建本地管理员账号（用户名/密码/头像）、完成。**不需要注册任何云账户**——这点和不少人的印象不同，v0.4.25 的初始化代码（`Welcome.vue`）里没有账户绑定步骤。
2. 应用商店里挑应用一键装；想在清单之外装东西，用"自定义安装"贴一段 docker compose。
3. 硬盘/U 盘在存储页面点选挂载，文件管理器立即可见；局域网共享走 SMB 设置。
4. 版本查询 `casaos -v`；卸载用 `casaos-uninstall`（安装脚本会把它放到 `/usr/bin/`）。

升级走 UI 的 Settings → Update，或在 SSH 终端执行：

```sh
wget -qO- https://get.casaos.io/update | sudo bash
```

日常运维两条经验：服务出问题时按 `systemctl status casaos-gateway`、`casaos-app-management` 等单元名逐个查，七个服务的分工就是第二节那张表；升级 Docker 前先搜一下 CasaOS 仓库的 issue 列表——#2390 那类兼容性问题往往先在那里爆发，锁定 Docker 版本等官方跟进是当前更稳妥的做法。

## 七、采用建议：谁还适合装它

| 场景 | 推荐度 | 说明 |
|------|--------|------|
| 旧电脑/NUC 变家庭服务器，图形界面管理 Docker 应用 | ⭐⭐⭐⭐ | 一行命令装完，商店与文件管理开箱可用 |
| 家庭文件共享 + 媒体服务器 | ⭐⭐⭐⭐ | Jellyfin + SMB 是社区最常见组合 |
| 想要持续迭代与官方 OTA 的家用 NAS | ⭐⭐ | 这正是 ZimaOS 的定位，建议直接看 ZimaOS |
| 生产级/企业场景 | ⭐ | 无审计、无高可用，官方定位就是 home scenario |
| 已经装了 v0.4.x 的存量用户 | ⭐⭐⭐ | 可继续用，按第五节的边界管理预期 |

选型时把三个选项放在一起看更清楚：**CasaOS** 是装在你已有 Linux 上的管理壳，系统层更新自己负责，适合"我就要在这台机器的 Debian 上加个图形管理"的人；**ZimaOS** 是整机操作系统，装整盘、带 OTA，官方当前所有新产品能力都落在这里，适合"给我一台开箱即用的家庭服务器"的人；**OpenMediaVault/TrueNAS** 则在存储可靠性上更严肃，适合把 NAS 当正经存储设施的人。

装 CasaOS 前要接受的现实：不会再有新版本发布；上游 Docker 之类的依赖变动可能破坏 UI 且修复周期以月计；2026-09 的安全修复尚未进入可安装的版本，公网直连暴露需要谨慎（家庭内网 + 不做端口映射是当前合理的暴露面）。

## 八、结语

CasaOS 的历史贡献是把"家用服务器"的门槛从"装 Linux、装 Docker、写 compose"压缩到"插电、跑一行命令、打开网页装应用"，37,000 多个 star 是这个判断的票数。2026 年的它是另一回事：一个稳定但冻结的 v0.4.x，安全维护在分支上继续，商店数据因与 ZimaOS 共享而保鲜，产品演进则整体迁往 ZimaOS。如果你要的是"装好就不想再折腾"的家庭服务器，今天装 CasaOS 依然是可用选项——前提是接受第五节那条时间线，并且知道官方的下一章写在另一个仓库里。

> 仓库：[IceWhaleTech/CasaOS](https://github.com/IceWhaleTech/CasaOS) · 官网：[casaos.zimaspace.com](https://casaos.zimaspace.com) · 应用商店源：[IceWhaleTech/CasaOS-AppStore](https://github.com/IceWhaleTech/CasaOS-AppStore) · 继任项目：[IceWhaleTech/ZimaOS](https://github.com/IceWhaleTech/ZimaOS) · 协议：Apache-2.0
