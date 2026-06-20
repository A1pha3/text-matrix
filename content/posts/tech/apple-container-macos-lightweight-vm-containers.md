---
title: "apple/container：把每个 Linux 容器塞进独立轻量 VM 的 macOS 原生容器工具"
date: "2026-06-10T21:03:59+08:00"
slug: "apple-container-macos-lightweight-vm-containers"
description: "Apple 官方开源的 macOS 容器工具，每个 Linux 容器运行在独立轻量 VM 中。本文拆解其架构、组件协作、1.0.0 新特性与适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["Apple", "macOS", "容器", "Virtualization", "Swift"]
---

## 学习目标

- 弄清 `apple/container` 与 Docker Desktop、Rancher Desktop、Colima 等"共享 Linux VM"方案的根本差异：每个容器对应一台轻量虚拟机。
- 理解 CLI、`container-apiserver`、XPC helper 之间的进程边界与调用链。
- 读懂 1.0.0 引入的 `container machine`、TOML 配置替换、`container cp` 等关键变更。
- 知道当前版本的硬约束：仅 Apple silicon、macOS 26 才完整支持、内存回收不彻底、macOS 15 网络限制。

## 目录

1. [为什么写这篇文章](#1-为什么写这篇文章)
2. [系统地图：组件拆分与职责边界](#2-系统地图组件拆分与职责边界)
3. [一个容器从 CLI 到 VM 的完整路径](#3-一个容器从-cli-到-vm-的完整路径)
4. [1.0.0 的关键变更](#4-100-的关键变更)
5. [与 Docker Desktop / Rancher Desktop 的取舍对比](#5-与-docker-desktop--rancher-desktop-的取舍对比)
6. [当前版本的硬约束](#6-当前版本的硬约束)
7. [快速上手路径](#7-快速上手路径)
8. [常见问题排查](#8-常见问题排查)
9. [自测题](#9-自测题)
10. [进阶路径](#10-进阶路径)
11. [这篇文章没覆盖什么](#11-这篇文章没覆盖什么)
12. [适用人群与采用建议](#12-适用人群与采用建议)
13. [总结](#13-总结)

---

## 1. 为什么写这篇文章

2026-06-09，Apple 在 GitHub 上把 `apple/container` 切到 1.0.0，距离 2025-05-30 创建仓库刚好一周年。这次发布一并引入了新的 `container machine` 子命令，把"系统设置"从 `UserDefault` 迁到 TOML 配置文件，并修掉了一个 IP 地址泄漏的 XPC 资源问题。

值得专门写一篇，是因为 `container` 走了一条与主流方案不同的工程路线：在 macOS 上给**每一个** Linux 容器分配一台独立的轻量虚拟机，而不是大家熟悉的"共享一台 Linux VM + 容器进程隔离"。这两条路线在安全性、网络模型、内存开销、镜像兼容性上的取舍不一样，下游开发者的使用方式也不一样。

仓库当前状态（截至 2026-06-10）：

- 仓库：[apple/container](https://github.com/apple/container)
- Stars / Forks：28,586 / 805
- 主语言：Swift
- License：Apache-2.0
- 最新版本：`1.0.0`（2026-06-09）
- 配套基础库：[containerization](https://github.com/apple/containerization)，负责底层容器、镜像、进程管理

注意：`container` 仍处于"active development"状态，README 明确写出 1.0.0 之前 minor 版本可能包含 breaking changes。

---

## 2. 系统地图：组件拆分与职责边界

在看命令之前，先把进程结构固定下来，否则后面所有 CLI 行为都说不清。

```text
 ┌─────────────────────┐
 │ container CLI       │ ← 用户入口
 │ (Sources/CLI)       │
 └──────────┬──────────┘
            │ HTTP / Unix socket
            ▼
 ┌─────────────────────┐
 │ container-apiserver │ ← launch agent，`system start` 拉起
 │ (Sources/APIServer) │
 └────┬─────────┬──────┘
      │ XPC     │ XPC
 ┌────┘         └────────────┐
 ▼                           ▼
┌────────────────────┐ ┌──────────────────────┐
│ container-core-    │ │ container-network-   │
│ images             │ │ vmnet                │
│ (镜像 / 内容存储)   │ │ (虚拟网络、IP 分配)   │
└────────────────────┘ └──────────────────────┘
 ▲
 │ 每个容器一个进程
 │
 ┌─────────────────────────────┘
 │
 ▼
 ┌──────────────────────┐
 │ container-runtime-   │ ← 每容器一个 helper
 │ linux                │   管理该容器的 VM 生命周期
 │ (Sources/Services)   │
 └──────────┬───────────┘
            │ Virtualization.framework
            ▼
 ┌──────────────────────┐
 │ 轻量 Linux VM        │ ← 一个容器 = 一个 VM
 │ (ext4 rootfs,        │
 │  OCI image payload)  │
 └──────────────────────┘
```

`container` 与 macOS 系统框架的耦合点：

- `Virtualization.framework`：管理 Linux 虚拟机及其外设。
- `vmnet` 框架：管理容器挂载的虚拟网络（macOS 26 才提供完整的多网络、容器互通能力）。
- `XPC`：进程间通信，CLI 与 `apiserver`、helper 之间都用。
- `launchd`：`container-apiserver` 是 launch agent，跟着用户会话走。
- `Keychain Services`：访问 registry 凭证（不再让用户手动 `docker login` 写到磁盘）。
- `unified logging system`：所有日志走 OSLog。

把进程拆成 `apiserver` + 多个 helper，而不是写成一个胖守护进程，背后是资源隔离与崩溃半径的考量：每起一个容器，VM、虚拟网卡、文件系统都要拉一份独立资源；如果把这些都装进一个进程，崩溃半径太大，也不好用 `launchd` 的 privilege separation 来收紧权限边界。

---

## 3. 一个容器从 CLI 到 VM 的完整路径

读 README 和 `docs/technical-overview.md` 时，最容易被"它就是 `docker run`"这种直觉带偏。下面用一个最小例子，把整条调用链过一遍。

输入：

```bash
container run -it --rm ubuntu:latest /bin/bash
```

实际发生的事：

1. **CLI 解析**：`Sources/CLI` 解析参数，向 `container-apiserver` 发起一次创建请求。如果 `apiserver` 没启动，第一次 `run` 会自动 `system start`。
2. **镜像拉取**：`apiserver` 通过 XPC 把任务交给 `container-core-images`。它负责和 OCI registry 通讯（HTTP / HTTPS，loopback / RFC1918 自动走 HTTP），把镜像的 layer 解压到本地内容存储。
3. **rootfs 准备**：与 `docker` 把所有 layer 用 overlayfs 叠加不同，`container` 的做法是构建一个完整的 ext4 rootfs（具体路径在 `Sources/ContainerOS` 和 `Sources/Containerization` 仓库里）。`--read-only` 等选项决定这个 rootfs 是否可写。
4. **网络分配**：`container-network-vmnet` 在 vmnet 上分配一个虚拟网卡。macOS 26 下，每个容器可以挂到独立的 `vmnet` 网络，容器之间能互通；macOS 15 下，所有容器共享一张 `default` 网段，且容器之间不能直接通讯。
5. **VM 启动**：`apiserver` 再派生一个 `container-runtime-linux` helper（每个容器一个），让它用 `Virtualization.framework` 启动一台轻量 Linux VM，rootfs 挂进 VM。
6. **进程执行**：VM 内由轻量 init 拉起用户指定的命令。`-i/-t` 决定是否挂 TTY；`--init` 会改用一个专用的 init 镜像，可以在 OCI 进程启动前先跑 VM 层的 daemon、eBPF filter、调试探针等。
7. **回收**：`--rm` 决定了进程退出后是否销毁 VM 和 rootfs；不指定的话，VM 会停但 rootfs 保留，下次 `start` 复用。

关键差异在于：`container` 把**每个 OCI 镜像实例化为一台完整的 Linux VM**。容器之间不共享内核、不共享文件系统 page cache，安全性更高；代价是每个容器的冷启动要拉一台 VM，启动开销与"共享 VM 模式"不在一个数量级。

---

## 4. 1.0.0 的关键变更

1.0.0 的 release notes（[releases/tag/1.0.0](https://github.com/apple/container/releases/tag/1.0.0)）把变更切成 Core / Network / Storage 三块。这里只挑影响使用方式的几个：

### 4.1 `container machine`（新功能）

定位上，`container machine` 是"环境容器"：保留 init，可以跑 `systemd`，可以注册长连服务。和 `container run` 的差异：

- **持久**：rootfs 和配置持久化在 `~/Library/Application Support/container/` 下，重启后保留。
- **Home 目录自动映射**：宿主 `$HOME` 挂到容器内的 `/Users/<username>`，可以用 macOS 上的编辑器直接改 Linux 里的文件，反之亦然。
- **用户名映射**：容器内默认用户与宿主同名，UID/GID 通过 `CONTAINER_UID/CONTAINER_GID` 环境变量传入，方便权限对齐。
- **服务管理**：装了 `systemd` 的镜像里可以直接 `systemctl start postgresql`，适合用来跑开发期的数据库、缓存。

最小用法：

```bash
container machine create alpine:latest --name dev
container machine set-default dev
container machine run -n dev # 进交互 shell
container machine run -n dev -- uname -a # 执行单条命令退出

# 调资源（需 stop 后再 run 生效）
container machine set -n dev cpus=4 memory=8G

# 别名
m ls
m run -n dev
```

自带别名 `m`，所有 `container machine` 子命令都可以写成 `m <sub>`。`docs/container-machine.md` 给了一个 Ubuntu 24.04 + systemd 的 Dockerfile 示例，适合当 `container machine` 的基础镜像模板。

### 4.2 TOML 配置文件取代 `system property`

之前的系统设置是 `UserDefault`-backed 的，用 `container system property get/set` 改。1.0.0 把这套改成了 TOML 配置文件，[container-system-config.md](https://github.com/apple/container/blob/main/docs/container-system-config.md) 描述了字段，`docs/tutorials/container-system-config-tutorial.md` 给出迁移教程。破坏性变化：`container system property get` 和 `container system property set` 被移除，老脚本需要重写。

### 4.3 `container cp`

`container cp` 终于补上了。Docker 用户一直依赖的命令：`container cp <container>:<path> <host-path>` 双向复制。这个功能依赖 4.2 的 storage 改动（`system df` 之前有 accounting 错误，1.0.0 修了）。

### 4.4 XPC 资源泄漏修复

`container-network-vmnet` 之前依赖 XPC 连接的隐式生命周期，长时间运行后会泄漏 IP 地址。1.0.0 改成"XPC connection-as-lease"，helper 进程退出时显式归还资源。这是一项稳定性修复，用户无需手动操作即可受益。

---

## 5. 与 Docker Desktop / Rancher Desktop 的取舍对比

| 维度 | apple/container | Docker Desktop / Rancher Desktop / Colima |
|------|------------------|-------------------------------------------|
| 隔离单元 | 每个容器 = 一台 VM | 所有容器共享一台 Linux VM |
| 内核 | 每个容器独立 Linux 内核 | 共享一个内核 |
| 网络 | vmnet，macOS 26 多网络、容器互通 | Docker bridge / Lima user-v2 |
| 启动开销 | 每容器一台 VM，启动较慢 | 共享 VM 内冷启动快 |
| 安全性 | VM 级隔离 | 共享内核，靠 namespace + capability |
| OCI 兼容性 | 完全兼容 | 完全兼容 |
| 镜像构建 | 内置 BuildKit，builder 也跑在 VM 中 | 同样支持 BuildKit |
| 平台要求 | 仅 Apple silicon；macOS 26 完整支持 | Intel / Apple silicon 均可 |
| Service / systemd | `container machine` 原生支持 | 容器内仍可装 systemd，但共享 VM 隔离更弱 |

读这张表时抓住一条主线：跑"一次性进程 + OCI 镜像"（比如 CI 步骤里的构建、单元测试、临时工具），`container run` 的语义和 `docker run` 几乎一致；跑"长连接的开发数据库 / 系统服务"，更合理的入口是 `container machine`，因为它能保留状态并启用 `systemd`。

---

## 6. 当前版本的硬约束

仓库 README 和 `technical-overview.md` 都明确写了几个"非兼容性 / 限制"，动手前要先知道：

### 6.1 平台

- **仅 Apple silicon**：Intel Mac 不在支持范围。
- **macOS 26 才能跑完整功能**：macOS 15 可以装，但 README 写明"maintainers typically will not address issues that cannot be reproduced on macOS 26"，意味着 macOS 15 上的问题不一定会被修。

### 6.2 macOS 15 的网络降级

- **容器互通关闭**：vmnet 在 macOS 15 上只提供"互不可见"的网络模式，容器之间无法直接通讯。
- **单一网络**：所有容器只能挂到 `default` 网段；`container network` 子命令、`--network` 选项在 macOS 15 上用会报错。
- **IP 分配漂移**：vmnet 与 `container-network-vmnet` 在第一次启动时可能就子网地址不一致，导致部分容器完全断网。仓库给了 troubleshooting 步骤，建议在 macOS 15 上多跑几次 `container system stop && container system start` 复测。

### 6.3 内存回收不彻底

Virtualization.framework 只实现了部分 memory ballooning。容器进程释放的内存页只回到 VM 内部，不会还给 macOS。跑大量重内存容器时，需要偶尔重启来降占用。这是 Apple 的设计取舍——不完整实现 ballooning，换来更简单的 VM 生命周期管理。

### 6.4 镜像 / 多平台构建

- `container build` 默认走 BuildKit，构建过程本身也跑在一个 builder VM 中。
- 多平台镜像：`container build --arch arm64 --arch amd64 ...`，但 amd64 产物需要在 x86-64 主机上才能真正运行（macOS 上的 amd64 模拟慢且不完整）。
- `--rosetta` 可以在容器内启用 Rosetta x86 模拟，适合某些只能跑 x86 二进制的工具链。

### 6.5 早期项目边界

README 明确写道："The container project is currently under active development. Its stability, both for consuming the project as a Swift package and the `container` tool, is only guaranteed within patch versions"。1.0.0 之前 minor 版本可能含 breaking change；下游依赖 `Containerization` Swift package 的项目要注意锁版本。

---

## 7. 快速上手路径

本地试一下，下面是一组最小命令（macOS 26 + Apple silicon）：

```bash
# 1. 安装：到 release 页下载 .pkg，双击安装，授权放在 /usr/local
# https://github.com/apple/container/releases

# 2. 拉起系统服务
container system start

# 3. 跑一次性容器
container run -it --rm ubuntu:latest /bin/bash

# 4. 跑一个后台 web 服务，把 8080 映射到宿主的 8080
container run -d --name web -p 8080:80 nginx:latest

# 5. 跑一个长生命周期开发机
container machine create alpine:latest --name dev
container machine set-default dev
container machine run -n dev -- apk add postgresql
container machine run -n dev -- /usr/bin/postgres -D /var/lib/postgresql/data

# 6. 升级 / 卸载
/usr/local/bin/update-container.sh
/usr/local/bin/uninstall-container.sh -d # -k 保留用户数据
```

排错入口：`docs/troubleshooting.md`（README 链接过去），重点关注 `system start` 失败、网络失效、镜像拉取失败这三类。

---

## 8. 常见问题排查

实际跑下来，下面几类问题最常踩到。每条给出定位思路与最小复现/修复命令。

### 8.1 `container system start` 失败

症状：`container run` 第一次自动拉起 `apiserver` 时报错，或手动 `container system start` 卡住。

定位步骤：

```bash
# 1. 看 apiserver 是否在跑
launchctl list | grep container

# 2. 看 OSLog 输出（unified logging）
log stream --predicate 'subsystem == "com.apple.container"' --info --debug

# 3. 强制重启系统服务
container system stop
container system start
```

常见原因：`/usr/local` 安装目录权限被改、Keychain 凭证被清空、`launchd` agent plist 残留旧版本。重装 `.pkg` 通常能解决前两类。

### 8.2 容器拿不到 IP / 网络不通

症状：`container run` 起来了，但容器内 `curl`、`apt-get` 全部超时。

定位步骤：

```bash
# 1. 看分配到的网卡与 IP
container run --rm alpine:latest -- ip addr

# 2. macOS 15 上多跑几次 stop/start 复测子网漂移
container system stop && container system start
```

macOS 15 上 vmnet 与 `container-network-vmnet` 第一次启动可能子网地址不一致，导致部分容器完全断网；macOS 26 上若仍不通，检查 `--network` 选项是否指向了未创建的网络名。

### 8.3 镜像拉取失败 / 401

症状：`container pull` 或 `container run` 报 `unauthorized` 或 `dial tcp` 超时。

定位步骤：

```bash
# 1. 看 registry 凭证是否在 Keychain
security find-internet-password -s ghcr.io

# 2. 用 HTTP registry（loopback / RFC1918 自动走 HTTP）
container run --rm --registry my-registry.corp:5000/myimage:latest
```

`container` 不再读 `~/.docker/config.json`，凭证统一走 Keychain Services。私有 registry 走 HTTP 时，地址必须在 RFC1918 或 loopback 段才会自动降级。

### 8.4 内存占用只升不降

症状：跑完一批容器后，macOS 内存压力持续走高，`container system stop` 也没释放。

这是 6.3 提到的 ballooning 不完整导致的。临时缓解：

```bash
# 销毁所有未运行的 rootfs 与 VM 状态
container system stop
# 重启系统服务后内存归还给 macOS
container system start
```

长期方案：把重内存任务集中到 `container machine` 上跑，定期 `machine stop` + `machine start` 回收。

### 8.5 `container system property` 命令报错

症状：老脚本里 `container system property get` 直接报 `unknown command`。

这是 1.0.0 的破坏性变更，`system property` 子命令已被移除。迁移路径见 `docs/tutorials/container-system-config-tutorial.md`，新写法是直接编辑 TOML 配置文件。

---

## 9. 自测题

读完上面这些，用下面几道题检验理解。答案在每题下方折叠区。

### Q1：进程边界

`container run` 起一个容器时，`container-apiserver` 与 `container-runtime-linux` 各负责什么？为什么拆成两个进程？

<details>
<summary>参考答案</summary>

`container-apiserver` 是常驻 launch agent，负责接收 CLI 请求、调度镜像拉取（通过 `container-core-images`）、分配网络（通过 `container-network-vmnet`），再派生 `container-runtime-linux` helper。`container-runtime-linux` 每容器一个，专门用 `Virtualization.framework` 管理这台 VM 的生命周期。拆开是为了把"长期常驻 + 高权限"的 apiserver 与"短生命周期 + 单容器资源"的 helper 隔离，缩小崩溃半径，也方便 `launchd` 做 privilege separation。
</details>

### Q2：网络差异

同一台 Mac 上跑两个容器 A、B，macOS 15 与 macOS 26 下容器互通情况分别是什么？

<details>
<summary>参考答案</summary>

macOS 15：vmnet 只提供"互不可见"模式，A、B 都挂到 `default` 网段但彼此不能直接通讯；`--network` 选项与 `container network` 子命令不可用。macOS 26：每个容器可挂到独立 vmnet 网络，同网络的容器之间能直接互通，跨网络默认隔离。
</details>

### Q3：rootfs 差异

`container` 与 `docker` 在构建容器 rootfs 时的做法有什么不同？这个差异带来什么后果？

<details>
<summary>参考答案</summary>

`docker` 把所有 layer 用 overlayfs 叠加成一份共享 rootfs；`container` 为每个容器构建一个完整的 ext4 rootfs。后果：容器之间不共享 page cache，安全性更高（看不到别的容器的文件系统痕迹），但每个容器的 rootfs 占用更大、冷启动要拷贝/准备一份独立 ext4 镜像，启动开销更高。
</details>

### Q4：版本约束

团队想在 macOS 15 的 Intel Mac 上用 `container` 跑 CI，会遇到哪些阻塞？

<details>
<summary>参考答案</summary>

三处阻塞：(1) 仅支持 Apple silicon，Intel Mac 直接不可用；(2) macOS 15 上 vmnet 网络降级，容器之间不互通、`--network` 不可用；(3) README 明确写 maintainers 通常不会修无法在 macOS 26 上复现的问题，意味着 macOS 15 上的 bug 不会得到官方修复。
</details>

### Q5：`container machine` vs `container run`

什么场景下应该选 `container machine` 而不是 `container run`？给出一个具体例子。

<details>
<summary>参考答案</summary>

需要持久状态、长连接服务、或 `systemd` 服务管理的场景选 `container machine`。例如：本地开发需要一台长期跑 PostgreSQL 的 Linux 环境，希望宿主重启后数据库数据保留、能用 `systemctl start postgresql` 管理、宿主 `$HOME` 能直接挂进去编辑配置文件——这种用 `container machine create` + `machine run` 比 `container run -d` 更合适，因为 `machine` 的 rootfs 持久化、支持 systemd、自动映射 Home 目录。
</details>

---

## 10. 进阶路径

掌握基础用法后，下面几条线值得继续深入。

### 10.1 读源码的入口顺序

按调用链从外到内读，最容易建立全局观：

1. `Sources/CLI`：命令行入口与参数解析，看 `container run` 怎么拼请求。
2. `Sources/APIServer`：常驻进程的请求处理，看镜像拉取、网络分配、helper 派生怎么串起来。
3. `Sources/Services`：`container-runtime-linux` 等 helper，看 VM 生命周期管理。
4. `Sources/ContainerOS`：轻量 Linux rootfs 的构建逻辑。
5. `Sources/ContainerXPC/`：进程间通信 schema。
6. 配套仓库 [containerization](https://github.com/apple/containerization)：底层容器、镜像、进程管理原语。

### 10.2 自定义 init 镜像

`container run --init` 默认用一个轻量 init 镜像。想跑自定义的 eBPF filter、调试探针、VM 层 daemon，可以替换 init 镜像。`docs/technical-overview.md` 的 "Init Images" 一节给了字段说明，构建时把 init 镜像当普通 OCI 镜像构建，再通过 `--init-image` 传入。

### 10.3 多网络与容器互通（macOS 26）

macOS 26 下 vmnet 支持多网络，可以搭出"前端网络 + 后端网络"的隔离拓扑：

```bash
# 创建两个网络
container network create frontend
container network create backend

# 把 web 容器挂到 frontend，db 容器挂到 backend
container run -d --name web --network frontend nginx:latest
container run -d --name db --network backend postgres:latest
```

同网络容器互通，跨网络默认隔离。适合模拟生产环境的网络分段。

### 10.4 写 Swift 客户端直接调 `Containerization`

`container` CLI 本身就是 `Containerization` Swift package 的一个上层封装。如果想在自家工具链里直接编排 VM（比如做 CI runner、做 macOS 上的沙箱执行器），可以直接依赖 `Containerization`，绕开 CLI。API 文档在 [apple.github.io/container/documentation/](https://apple.github.io/container/documentation/)。注意 6.5 提到的稳定性约束——锁 patch 版本。

### 10.5 跟踪 release 节奏

仓库 release 节奏较快，建议订阅 [releases.atom](https://github.com/apple/container/releases.atom)，每次 minor 版本出来先看 release notes 的 Breaking Changes 段，再决定是否升级。`docs/migrating-to-1.0.md` 给了从 0.x 到 1.0 的迁移清单，可作为后续 minor 升级的模板。

---

## 11. 这篇文章没覆盖什么

下面这些**没有**在本文给出权威结论：

- 1.0.0 之后的具体性能数字（启动耗时、内存占用、IO 吞吐）。仓库目前没有公开的 benchmark，本文中所有性能描述都来自 `technical-overview.md` 的定性表述，不外推具体百分比。
- `container` 与 `containerization` Swift package 内部的 API 细节。API doc 在 [apple.github.io/container/documentation/](https://apple.github.io/container/documentation/)，要看具体类签名直接读 doc。
- macOS 26 中 vmnet 多网络模式的全部参数。本文只引用了 `--network` 选项的存在与格式。
- 内部 helper 进程之间的 XPC schema。仓库没有把 schema 单独抽出文档，要研究时直接读 `Sources/ContainerXPC/`。

---

## 12. 适用人群与采用建议

适合立刻尝试的场景：

- macOS 本地做容器化开发，且希望不依赖 Docker Desktop license。
- 需要在 Apple silicon Mac 上跑多个**互相隔离**的 Linux 服务（`container machine`）。
- 已经接受 macOS 26 升级，且团队习惯用 OCI 标准镜像。

建议观望的场景：

- 还在 macOS 15 / Intel Mac 上工作，且无法立刻升级（功能会被显著裁剪）。
- 跑大规模 CI 流水线，需要在多架构之间快速切换（每容器一台 VM 的启动开销目前没有公开数据支撑"够快"）。
- 已经在用 `colima` / OrbStack / Rancher Desktop，且对当前方案没有安全或功能上的明确不满。

决定采用的话，按这个顺序推进：

1. **先装一台 Apple silicon Mac + macOS 26 试运行**，确认日常 `container run` / `container build` 不会卡住。
2. **再上 `container machine` 替代 docker-compose 里的长连接服务**，先在非生产开发机上跑一段时间。
3. **最后才考虑迁移 CI / 生产编排**：1.0.0 之前不建议把 CI 流水线或 Kubernetes 节点换成 `container`，等 minor 版本稳定一段时间再动。

---

## 13. 总结

`apple/container` 1.0.0 的核心取舍就一句话：用"每容器一台轻量 VM"换"VM 级隔离 + OCI 镜像兼容"，代价是冷启动开销与内存回收的不彻底。这个取舍在 macOS 26 + Apple silicon 上才完整兑现，macOS 15 与 Intel Mac 都有功能裁剪。

记住三条主线：

- **进程结构**：CLI → `container-apiserver`（常驻 launch agent）→ `container-runtime-linux`（每容器一个 helper）→ `Virtualization.framework` 拉起 VM。崩溃半径与权限边界靠这套拆分控制。
- **使用入口**：一次性任务用 `container run`，长连接服务与开发环境用 `container machine`。两者共享底层 VM 机制，但 `machine` 多了 rootfs 持久化、Home 目录映射、systemd 支持。
- **版本约束**：1.0.0 之前 minor 版本可能含 breaking change，`system property` 已被 TOML 配置取代，凭证走 Keychain 而非 `~/.docker/config.json`。下游依赖 `Containerization` 的项目要锁 patch 版本。

下一步动作：在 macOS 26 + Apple silicon 上跑一遍第 7 节的最小命令，再按第 8 节的排查清单对照本地环境，最后按第 10 节的进阶路径选一条线深入。
