---
title: "apple/container：把每个 Linux 容器塞进独立轻量 VM 的 macOS 原生容器工具"
date: "2026-06-10T21:03:59+08:00"
slug: "apple-container-macos-lightweight-vm-containers"
github_repo: "apple/container"
description: "Apple 官方开源的 macOS 容器工具，每个 Linux 容器运行在独立轻量 VM 中。本文拆解其架构、组件协作、1.0 到 1.3 的版本演进与适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["Apple", "macOS", "Swift"]
---

## 学习目标

- 弄清 `apple/container` 与 Docker Desktop、Rancher Desktop、Colima 等"共享 Linux VM"方案的根本差异：每个容器对应一台轻量虚拟机。
- 理解 CLI、`container-apiserver`、XPC helper 之间的进程边界与调用链。
- 读懂 1.0.0 引入的 `container machine`、TOML 配置、`container cp`，以及 1.1 到 1.3 的安全修复与破坏性变更。
- 知道当前版本的硬约束：仅 Apple silicon、macOS 26 才获得完整支持、内存回收不彻底、macOS 15 网络降级。

## 目录

1. [为什么值得关注](#1-为什么值得关注)
2. [系统地图：组件拆分与职责边界](#2-系统地图组件拆分与职责边界)
3. [一个容器从 CLI 到 VM 的完整路径](#3-一个容器从-cli-到-vm-的完整路径)
4. [1.0.0 的关键变更](#4-100-的关键变更)
5. [1.1 到 1.3：安全修复与破坏性变更](#5-11-到-13安全修复与破坏性变更)
6. [与 Docker Desktop / Rancher Desktop 的取舍对比](#6-与-docker-desktop--rancher-desktop-的取舍对比)
7. [当前版本的硬约束](#7-当前版本的硬约束)
8. [快速上手路径](#8-快速上手路径)
9. [常见问题排查](#9-常见问题排查)
10. [练习](#10-练习)
11. [自测题](#11-自测题)
12. [进阶路径](#12-进阶路径)
13. [这篇文章没覆盖什么](#13-这篇文章没覆盖什么)
14. [适用人群与采用建议](#14-适用人群与采用建议)
15. [总结](#15-总结)
16. [资料口径说明](#16-资料口径说明)

---

## 1. 为什么值得关注

2026-06-09，Apple 在 GitHub 上把 `apple/container` 切到 1.0.0，距离 2025-05-30 创建仓库刚好一周年。之后三个月又连发四个版本，到 2026-08-29 已到 1.3.1。Stars 从发布时的约 2.9 万涨到 49,722——对一个要求 macOS 26 + Apple silicon 的工具来说，这个增速说明"macOS 原生容器"确实补上了一个空位。

`container` 走了一条与主流方案不同的工程路线：在 macOS 上给**每一个** Linux 容器分配一台独立的轻量虚拟机，而不是"共享一台 Linux VM + 容器进程隔离"。这两条路线在安全性、网络模型、内存开销、镜像兼容性上的取舍不一样，下游开发者的使用方式也不一样。

仓库当前状态（截至 2026-09-07）：

- 仓库：[apple/container](https://github.com/apple/container)
- Stars / Forks：49,722 / 1,783
- 主语言：Swift
- License：Apache-2.0
- 最新版本：`1.3.1`（2026-08-29）
- 配套基础库：[containerization](https://github.com/apple/containerization)，负责底层容器、镜像、进程管理

注意：README 写明稳定性"只在 patch 版本之间有保证"（比如 1.3.0 和 1.3.1 之间），minor 版本可能包含 breaking change——1.3.0 就移除了镜像操作的 `--scheme auto`。下游依赖 `Containerization` Swift package 的项目要锁版本。

---

## 2. 系统地图：组件拆分与职责边界

在看命令之前，先把进程结构固定下来，否则后面所有 CLI 行为都说不清。

```text
 ┌─────────────────────┐
 │ container CLI       │ ← 用户入口
 │ (Sources/CLI)       │
 └──────────┬──────────┘
            │ XPC（service: com.apple.container.apiserver）
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
│ Plugins/CoreImages │ │ Plugins/NetworkVmnet │
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
 │ (Plugins/RuntimeLinux)│
 └──────────┬───────────┘
            │ Virtualization.framework
            ▼
 ┌──────────────────────┐
 │ 轻量 Linux VM        │ ← 一个容器 = 一个 VM
 │ (ext4 rootfs,        │
 │  OCI image payload)  │
 └──────────────────────┘
```

`container` 与 macOS 系统框架的耦合点（`docs/technical-overview.md` 原文列出的六项）：

- `Virtualization.framework`：管理 Linux 虚拟机及其外设。
- `vmnet` 框架：管理容器挂载的虚拟网络（macOS 26 才提供完整的多网络、容器互通能力）。
- `XPC`：进程间通信，CLI 与 `apiserver`、helper 之间都用。
- `launchd`：`container-apiserver` 是 launch agent，跟着用户会话走。
- `Keychain Services`：访问 registry 凭证。
- `unified logging system`：所有日志走 OSLog，subsystem 为 `com.apple.container`。

把进程拆成 `apiserver` + 多个 helper，而不是写成一个胖守护进程，背后是资源隔离与崩溃半径的考量：每起一个容器，VM、虚拟网卡、文件系统都要拉一份独立资源；如果把这些都装进一个进程，崩溃半径太大，也不好用 `launchd` 的 privilege separation 来收紧权限边界。

1.2.0 起 `Sources/Plugins/` 下多了一个 `K8s` 目录，对应新增的 `k8s` plugin，可以在本地拉起一套 Kubernetes 集群，插件机制和 helper 是同一套 XPC 架构的延伸。

---

## 3. 一个容器从 CLI 到 VM 的完整路径

读 README 和 `docs/technical-overview.md` 时，最容易被"它就是 `docker run`"这种直觉带偏。下面用一个最小例子，把整条调用链过一遍。

输入：

```bash
container run -it --rm ubuntu:latest /bin/bash
```

实际发生的事：

1. **CLI 解析**：`Sources/CLI` 解析参数，向 `container-apiserver` 发起一次创建请求。如果 `apiserver` 没启动，第一次 `run` 会自动 `system start`。
2. **镜像拉取**：`apiserver` 通过 XPC 把任务交给 `container-core-images`。它负责和 OCI registry 通讯，把镜像的 layer 解压到本地内容存储。registry 访问默认走 HTTPS；1.0 到 1.2 版本提供 `--scheme auto`，对 localhost、RFC1918 私有网段和内部 DNS 域自动降级 HTTP，1.3.0 起这个选项被移除。
3. **rootfs 准备**：与 `docker` 把所有 layer 用 overlayfs 叠加不同，`container` 为每个容器组装一个完整的 ext4 rootfs，构建逻辑在 [containerization](https://github.com/apple/containerization) 包里。`--read-only` 等选项决定这个 rootfs 是否可写。
4. **网络分配**：`container-network-vmnet` 在 vmnet 上分配一个虚拟网卡。macOS 26 下，每个容器可以挂到独立的 `vmnet` 网络，容器之间能互通；macOS 15 下，所有容器共享一张 `default` 网段，且容器之间不能直接通讯。
5. **VM 启动**：`apiserver` 再派生一个 `container-runtime-linux` helper（每个容器一个），让它用 `Virtualization.framework` 启动一台轻量 Linux VM，rootfs 挂进 VM。
6. **进程执行**：VM 内由轻量 init（vminitd）拉起用户指定的命令。`-i/-t` 决定是否挂 TTY；`--init` 会改用一个专用的 init 镜像，可以在 OCI 进程启动前先跑 VM 层的 daemon、eBPF filter、调试探针等。
7. **回收**：`--rm` 决定了进程退出后是否销毁 VM 和 rootfs；不指定的话，VM 会停但 rootfs 保留，下次 `start` 复用。

关键差异在于：`container` 把**每个 OCI 镜像实例化为一台完整的 Linux VM**。容器之间不共享内核、不共享文件系统 page cache，安全性更高；代价是每个容器的冷启动要拉一台 VM，启动开销与"共享 VM 模式"不在一个数量级。官方文档对性能的说法只有一句"boot times comparable to containers running in a shared VM"，没有公开数字，自己量。

---

## 4. 1.0.0 的关键变更

1.0.0 的 release notes（[releases/tag/1.0.0](https://github.com/apple/container/releases/tag/1.0.0)）把变更切成 Core / Network / Storage 三块。这里只挑影响使用方式的几个：

### 4.1 `container machine`（新功能）

定位上，`container machine` 是"环境容器"：保留 init，可以跑 `systemd`，可以注册长连服务。和 `container run` 的差异：

- **持久**：rootfs 和配置持久化在 `~/Library/Application Support/com.apple.container/` 下，重启后保留。
- **Home 目录自动映射**：宿主 `$HOME` 挂到容器内的 `/Users/<username>`，可以用 macOS 上的编辑器直接改 Linux 里的文件，反之亦然。挂载模式可用 `rw`（默认）、`ro`、`none`。
- **用户名映射**：容器内默认用户与宿主同名。首次启动时内置的 setup 脚本会按 `CONTAINER_UID`、`CONTAINER_GID` 等环境变量创建这个用户；想自定义就往镜像里放一个 `/etc/machine/create-user.sh`。
- **服务管理**：装了 `systemd` 的镜像里可以直接 `systemctl start postgresql`，适合用来跑开发期的数据库、缓存。
- **资源默认值**：内存默认取宿主的一半，`container machine set` 调整后需要 stop 再 start 才生效。
- **嵌套虚拟化**（M3 及以上 + macOS 15+）：给 machine 配一个开启 `CONFIG_KVM=y` 的自定义内核，容器内能拿到 `/dev/kvm`，默认内核不支持。

最小用法：

```bash
container machine create alpine:latest --name dev
container machine set-default dev
container machine run -n dev # 进交互 shell
container machine run -n dev -- uname -a # 执行单条命令退出

# 调资源（需 stop 后再 start 生效）
container machine set -n dev cpus=4 memory=8G

# 别名
m ls
m run -n dev
```

自带别名 `m`，所有 `container machine` 子命令都可以写成 `m <sub>`。`docs/container-machine.md` 给了一个 Ubuntu 24.04 + systemd 的 Dockerfile 示例，适合当 `container machine` 的基础镜像模板。

### 4.2 TOML 配置文件取代 `system property`

之前的系统设置是 `UserDefault`-backed 的，用 `container system property get/set` 改。1.0.0 把这套改成了 TOML 配置文件，用户级配置在 `~/.config/container/config.toml`（尊重 `XDG_CONFIG_HOME`），安装级在 `<installRoot>/etc/container/config.toml`，前者覆盖后者，都没写的键回落到硬编码默认值。

`docs/container-system-config.md` 给出了完整 schema，顶层分七段外加插件段：

```toml
[build]      # builder VM 的资源与镜像
[container]  # 每容器默认资源（默认 4 CPU / 1g 内存）
[dns]        # 容器主机名的本地 DNS 域
[kernel]     # 客户机内核的二进制路径、下载地址与 digest
[network]    # 新网络的默认子网
[registry]   # 默认 registry 域（默认 docker.io）
[vminit]     # vminitd 初始化镜像
[plugin.<id>] # 各插件自己的配置段
```

破坏性变化：`container system property get` 和 `container system property set` 被移除，老脚本需要重写；`container system property list`（别名 `ls`）保留，用来打印合并后的实际配置，支持 `--format json`。迁移教程见 [docs/tutorials/container-system-config-tutorial.md](https://github.com/apple/container/blob/main/docs/tutorials/container-system-config-tutorial.md)。

### 4.3 `container cp`

`container cp` 终于补上了。Docker 用户一直依赖的命令：`container cp <container>:<path> <host-path>` 双向复制。同一版还修了 `system df` 的 accounting 错误。1.1.0 又修了相对路径导致 `cp` 失败的问题。

### 4.4 XPC 资源泄漏修复

`container-network-vmnet` 之前依赖 XPC 连接的隐式生命周期，长时间运行后会泄漏 IP 地址。1.0.0 改成"XPC connection-as-lease"，helper 进程退出时显式归还资源。这是一项稳定性修复，用户无需手动操作即可受益。

---

## 5. 1.1 到 1.3：安全修复与破坏性变更

如果你在 1.0.0 发布时试过就放下，这三个月的演进值得重新看一眼。各版本 release notes 的要点：

| 版本 | 日期 | 关键内容 |
|------|------|----------|
| 1.1.0 | 2026-07-06 | 非 root 容器内 Unix domain socket 挂载修复；`container cp` 相对路径修复 |
| 1.2.0 | 2026-07-29 | **5 个安全公告**（见下文）；`k8s` plugin；`container export`；`container build --ssh`；`--read-only-path` / `--masked-path` |
| 1.2.1 | 2026-08-07 | patch 修复 |
| 1.2.2 | 2026-08-08 | patch 修复 |
| 1.3.0 | 2026-08-24 | 默认 Kata 内核升到 3.32.0-debug；文档大面积重组；⌨️ 移除镜像操作的 `--scheme auto`，默认 HTTPS |
| 1.3.1 | 2026-08-29 | patch 修复 |

1.2.0 的安全公告值得单独说。官方 GitHub Security Advisories 修复了四个 `container` 问题和一个 `containerization` 问题，包括：

- [CVE-2026-64786](https://github.com/apple/container/security/advisories/GHSA-xwgf-4rc5-p4m4)：裸名镜像的 `Config.Env` 条目会继承启动进程的环境变量。
- [CVE-2026-64773](https://github.com/apple/container/security/advisories/GHSA-wg28-286f-56v6)：TCP 端口转发器对已发布端口的预连接数据无缓冲上限。
- [CVE-2026-64777](https://github.com/apple/container/security/advisories/GHSA-2v2q-4q35-h585)：构建文件系统同步可通过 symlink 读到构建上下文之外的宿主文件。
- [GHSA-5h49-6pr7-9mv4](https://github.com/apple/containerization/security/advisories/GHSA-5h49-6pr7-9mv4)（containerization 包）：解包归档到宿主时未重置特殊权限位。

前三个官方标注为 medium，但都是"宿主与容器边界"上的问题——对一台把安全当卖点的工具，这些公告本身就是信号：还在 1.0/1.1 的环境应直接升到 1.2.0 以上。

1.3.0 的 `--scheme auto` 移除影响私有 registry 工作流：如果你的内网 registry 靠 HTTP 降级工作，升级后拉取会失败，需要在 `[registry]` 或网络层面另行处理（见第 9.3 节）。

---

## 6. 与 Docker Desktop / Rancher Desktop 的取舍对比

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
| 长期服务 | `container machine` 原生支持（init/systemd） | 容器内仍可装 systemd，但共享 VM 隔离更弱 |

跑"一次性进程 + OCI 镜像"（CI 步骤里的构建、单元测试、临时工具），`container run` 的语义和 `docker run` 几乎一致；跑"长连接的开发数据库 / 系统服务"，更合理的入口是 `container machine`，因为它能保留状态并启用 `systemd`。

---

## 7. 当前版本的硬约束

仓库 README 和 `technical-overview.md` 写明了几条限制，动手前要先知道：

### 7.1 平台

- **仅 Apple silicon**：Intel Mac 不在支持范围。
- **macOS 26 才获得完整支持**：README 的口径是"We do not support older versions of macOS"，并且 maintainers 通常不处理无法在 macOS 26 上复现的问题。`technical-overview.md` 承认 macOS 15 上能跑，但列出了下面这些功能限制——可以理解为"能运行，出问题自理"。

### 7.2 macOS 15 的网络降级

- **容器互通关闭**：vmnet 在 macOS 15 上只提供"互不可见"的网络模式，容器之间无法直接通讯。
- **单一网络**：所有容器只能挂到 `default` 网段；`container network` 子命令在 macOS 15 上不可用，`container run` / `container create` 带 `--network` 会直接报错。
- **IP 分配漂移**：macOS 15 上容器网络要等第一个容器启动才能创建，而负责分 IP 的网络 helper 必须先于容器启动，两者可能就子网地址达成不一致，导致部分容器完全断网。正常情况下 vmnet 用 `192.168.64.1/24` 创建容器网络，macOS 15 上 helper 默认也用这个网段——对不上就会出问题。官方 troubleshooting 文档（`troubleshooting.md`）在 1.3.0 文档重组后已不在仓库中，实践中可以在 macOS 15 上多跑几次 `container system stop && container system start` 复测。

### 7.3 内存回收不彻底

Virtualization.framework 只实现了部分 memory ballooning。容器进程释放的内存页只回到 VM 内部，不会还给 macOS。跑大量重内存容器时，需要偶尔重启来降占用。这是 Apple 的设计取舍——不完整实现 ballooning，换来更简单的 VM 生命周期管理。

### 7.4 镜像 / 多平台构建

- `container build` 默认走 BuildKit（`docs/command-reference.md` 原文："The build runs in isolation using BuildKit"），构建过程本身跑在一个 builder VM 中，`container builder` 子命令管理它的生命周期。
- 多平台镜像：`container build --arch arm64 --arch amd64 ...`，但 amd64 产物需要在 x86-64 主机上才能真正运行（macOS 上的 amd64 模拟慢且不完整）。
- `--rosetta` 可以在容器内启用 Rosetta x86 模拟，适合某些只能跑 x86 二进制的工具链；`[build]` 配置段的 `rosetta = false` 则反过来，让构建只产 arm64 镜像。

### 7.5 版本边界

README 的原话："The container project is currently under active development. Its stability, both for consuming the project as a Swift package and the `container` tool, is only guaranteed within patch versions"。到了 1.x 这句话仍然成立——1.3.0 就实际移除了 `--scheme auto`。下游依赖 `Containerization` Swift package 的项目要锁 patch 版本，升级 minor 前先读 release notes。

---

## 8. 快速上手路径

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

# 5. 跑一个长生命周期开发机（用带 systemd 的镜像，模板见 docs/container-machine.md）
container build -t local/ubuntu-machine:latest . # 使用官方 Ubuntu 24.04 + systemd Dockerfile
container machine create local/ubuntu-machine:latest --name dev
container machine set-default dev
container machine run -n dev -- apt-get install -y postgresql
container machine run -n dev -- systemctl start postgresql

# 6. 升级 / 卸载
/usr/local/bin/update-container.sh
/usr/local/bin/uninstall-container.sh -d # -k 保留用户数据
```

排错入口（1.3.0 文档重组后的结构）：`docs/how-to.md` 是功能问答集，`docs/logs.md` 讲 `container logs` 与 `container system logs`，`docs/command-reference.md` 是全部命令的参考，装不上或报错时按 `docs/bug-report-how-to.md` 收集信息提 issue。

---

## 9. 常见问题排查

实际跑下来，下面几类问题最常踩到。每条给出定位思路与最小复现/修复命令。

### 9.1 `container system start` 失败

症状：`container run` 第一次自动拉起 `apiserver` 时报错，或手动 `container system start` 卡住。

定位步骤：

```bash
# 1. 看 apiserver 是否在跑
launchctl list | grep container

# 2. 看系统日志（官方入口，等价于按 subsystem 过滤 OSLog）
container system logs

# 3. 需要更细的实时输出时
log stream --predicate 'subsystem = "com.apple.container"' --info --debug

# 4. 强制重启系统服务
container system stop
container system start
```

常见原因：`/usr/local` 安装目录权限被改、Keychain 凭证异常、`launchd` agent plist 残留旧版本。重装 `.pkg` 通常能解决前两类。

### 9.2 容器拿不到 IP / 网络不通

症状：`container run` 起来了，但容器内 `curl`、`apt-get` 全部超时。

定位步骤：

```bash
# 1. 看分配到的网卡与 IP
container run --rm alpine:latest -- ip addr

# 2. 看网络 helper 的分配记录
container system logs | grep "allocated attachment"
```

macOS 15 上 vmnet 与 `container-network-vmnet` 第一次启动可能子网地址不一致（正常应为 `192.168.64.0/24` 段），导致部分容器完全断网，多跑几次 `container system stop && container system start` 复测；macOS 26 上若仍不通，检查 `--network` 选项是否指向了未创建的网络名。

### 9.3 镜像拉取失败 / 401

症状：`container pull` 或 `container run` 报 `unauthorized` 或 `dial tcp` 超时。

定位步骤：

```bash
# 1. 登录 registry（凭证进 Keychain，不写 ~/.docker/config.json）
container registry login ghcr.io

# 2. 确认 Keychain 里有没有对应凭证
security find-internet-password -s ghcr.io
```

两点常踩的坑：

- `container` 不读 `~/.docker/config.json`，凭证统一走 Keychain Services。
- 私有 registry 走 HTTP 的方式在 1.3.0 变了：1.0 到 1.2 版本对 localhost、RFC1918 私有网段（10/8、127/8、172.16/12、192.168/16）和内部 DNS 域自动降级 HTTP；1.3.0 起 `--scheme auto` 被移除，默认 HTTPS，靠 HTTP 降级工作的内网 registry 升级后会直接失败，需要给 registry 配证书或在网络层处理。

### 9.4 内存占用只升不降

症状：跑完一批容器后，macOS 内存压力持续走高。

这是 7.3 提到的 ballooning 不完整导致的。临时缓解：

```bash
container system stop
# 重启系统服务后，VM 全部销毁，内存归还给 macOS
container system start
```

长期方案：把重内存任务集中到 `container machine` 上跑，定期 `machine stop` + `machine run` 回收。

### 9.5 `container system property` 命令报错

症状：老脚本里 `container system property get` 直接报 `unknown command`。

这是 1.0.0 的破坏性变更，`get`/`set` 子命令已被移除，改为直接编辑 TOML 配置文件（路径见 4.2）。注意 `container system property list` 还在，用它查看合并后的实际配置。迁移路径见 `docs/tutorials/container-system-config-tutorial.md`。

---

## 10. 练习

### 练习一：安装 apple/container 并运行第一个容器

1. 安装 `container`：按照官方 README 的说明
2. 启动 `container-apiserver`
3. 创建一个 Linux 容器：`container run -it ubuntu:latest bash`
4. 观察：每个容器是否对应一个独立 VM？
5. 记录：安装耗时、启动延迟、资源占用

### 练习二：对比 apple/container 与 Docker Desktop

1. 在 Docker Desktop 里运行同一个容器
2. 在 apple/container 里运行同一个容器
3. 对比：启动延迟、资源占用、网络模型、文件共享
4. 评估：你的场景更适合哪个工具？

### 练习三：修改 TOML 配置并验证

1. 创建 `~/.config/container/config.toml`
2. 在 `[container]` 段配置默认 CPU 与内存（参考 4.2 的 schema）
3. 用 `container system property list` 查看合并后的配置，验证改动生效
4. 记录：配置过程、遇到的问题、解决方案

---

## 11. 自测题

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

`docker` 把所有 layer 用 overlayfs 叠加成一份共享 rootfs；`container` 为每个容器组装一个完整的 ext4 rootfs。后果：容器之间不共享 page cache，安全性更高（看不到别的容器的文件系统痕迹），但每个容器的 rootfs 占用更大、冷启动要准备一份独立 ext4 镜像，启动开销更高。
</details>

### Q4：版本约束

团队想在 macOS 15 的 Intel Mac 上用 `container` 跑 CI，会遇到哪些阻塞？

<details>
<summary>参考答案</summary>

三处阻塞：(1) 仅支持 Apple silicon，Intel Mac 直接不可用；(2) macOS 15 上 vmnet 网络降级，容器之间不互通、`--network` 不可用；(3) README 写明不支持旧版 macOS，maintainers 通常不处理无法在 macOS 26 上复现的问题。
</details>

### Q5：`container machine` vs `container run`

什么场景下应该选 `container machine` 而不是 `container run`？给出一个具体例子。

<details>
<summary>参考答案</summary>

需要持久状态、长连接服务、或 `systemd` 服务管理的场景选 `container machine`。例如：本地开发需要一台长期跑 PostgreSQL 的 Linux 环境，希望宿主重启后数据库数据保留、能用 `systemctl start postgresql` 管理、宿主 `$HOME` 能直接挂进去编辑配置文件——这种用 `container machine create` + `machine run` 比 `container run -d` 更合适，因为 `machine` 的 rootfs 持久化、支持 systemd、自动映射 Home 目录。
</details>

---

## 12. 进阶路径

掌握基础用法后，下面几条线值得继续深入。

### 12.1 读源码的入口顺序

按调用链从外到内读，最容易建立全局观：

1. `Sources/CLI`：命令行入口与参数解析，看 `container run` 怎么拼请求。
2. `Sources/APIServer`：常驻进程的请求处理；服务层实现在 `Sources/Services/ContainerAPIService`。
3. `Sources/Plugins/`：三个 XPC helper——`CoreImages`（镜像与内容存储）、`NetworkVmnet`（虚拟网络）、`RuntimeLinux`（每容器一个的 VM 管理）。
4. `Sources/ContainerOS`：轻量 Linux 环境相关源码。
5. `Sources/ContainerXPC/`：进程间通信 schema。
6. 配套仓库 [containerization](https://github.com/apple/containerization)：底层容器、镜像、进程管理原语，rootfs 组装也在这里。

### 12.2 自定义 init 镜像

`container run --init` 默认用一个轻量 init 镜像。想跑自定义的 eBPF filter、调试探针、VM 层 daemon，可以替换 init 镜像。`docs/command-reference.md` 对 `--init-image` 的说明是"在 OCI 容器启动之前定制 boot 时行为"；构建时把 init 镜像当普通 OCI 镜像构建，再通过 `--init-image` 传入。

### 12.3 多网络与容器互通（macOS 26）

macOS 26 下 vmnet 支持多网络，可以搭出"前端网络 + 后端网络"的隔离拓扑：

```bash
# 创建两个网络
container network create frontend
container network create backend

# 把 web 容器挂到 frontend，db 容器挂到 backend
container run -d --name web --network frontend nginx:latest
container run -d --name db --network backend postgres:latest
```

同网络容器互通，跨网络默认隔离。适合模拟生产环境的网络分段。`[dns]` 配置段还能给容器主机名追加本地域（比如 `my-web-server.test`），配合 `curl http://my-web-server.test` 直接按名字访问。

### 12.4 写 Swift 客户端直接调 `Containerization`

`container` CLI 本身就是 `Containerization` Swift package 的一个上层封装。如果想在自家工具链里直接编排 VM（比如做 CI runner、做 macOS 上的沙箱执行器），可以直接依赖 `Containerization`，绕开 CLI。API 文档在 [apple.github.io/container/documentation/](https://apple.github.io/container/documentation/)。注意 7.5 提到的稳定性约束——锁 patch 版本。

### 12.5 跟踪 release 节奏

仓库 release 节奏较快，建议订阅 [releases.atom](https://github.com/apple/container/releases.atom)，每次 minor 版本出来先看 release notes 的 Breaking Changes 段（⌨️ 标记），再决定是否升级。

---

## 13. 这篇文章没覆盖什么

下面这些**没有**在本文给出权威结论：

- 1.x 各版本的具体性能数字（启动耗时、内存占用、IO 吞吐）。仓库没有公开的 benchmark，本文中所有性能描述都来自 `technical-overview.md` 的定性表述，不外推具体百分比。
- `container` 与 `containerization` Swift package 内部的 API 细节。API doc 在 [apple.github.io/container/documentation/](https://apple.github.io/container/documentation/)，要看具体类签名直接读 doc。
- macOS 26 中 vmnet 多网络模式的全部参数。本文只引用了 `--network` 选项的存在与格式。
- 内部 helper 进程之间的 XPC schema。仓库没有把 schema 单独抽出文档，要研究时直接读 `Sources/ContainerXPC/`。
- `k8s` plugin 的完整用法。1.2.0 引入，本文只提及存在，未展开部署流程。

---

## 14. 适用人群与采用建议

适合立刻尝试的场景：

- macOS 本地做容器化开发，且希望不依赖 Docker Desktop license。
- 需要在 Apple silicon Mac 上跑多个**互相隔离**的 Linux 服务（`container machine`）。
- 已经接受 macOS 26 升级，且团队习惯用 OCI 标准镜像。

建议观望的场景：

- 还在 macOS 15 / Intel Mac 上工作，且无法立刻升级（功能会被显著裁剪，且不在官方支持范围）。
- 跑大规模 CI 流水线，需要在多架构之间快速切换（每容器一台 VM 的启动开销目前没有公开数据支撑"够快"）。
- 已经在用 `colima` / OrbStack / Rancher Desktop，且对当前方案没有安全或功能上的明确不满。

决定采用的话，按这个顺序推进：

1. **先装一台 Apple silicon Mac + macOS 26 试运行**，确认日常 `container run` / `container build` 不会卡住。
2. **再上 `container machine` 替代 docker-compose 里的长连接服务**，先在非生产开发机上跑一段时间。
3. **最后才考虑迁移 CI / 生产编排**：minor 版本仍在引入破坏性变更（1.3.0 移除 `--scheme auto`），等稳定性承诺覆盖到 minor 再动。

---

## 15. 总结

`apple/container` 的核心取舍就一句话：用"每容器一台轻量 VM"换"VM 级隔离 + OCI 镜像兼容"，代价是冷启动开销与内存回收的不彻底。这个取舍在 macOS 26 + Apple silicon 上才完整兑现，macOS 15 与 Intel Mac 都有功能裁剪。

三条主线：

- **进程结构**：CLI → `container-apiserver`（常驻 launch agent）→ `container-runtime-linux`（每容器一个 helper）→ `Virtualization.framework` 拉起 VM。崩溃半径与权限边界靠这套拆分控制。
- **使用入口**：一次性任务用 `container run`，长连接服务与开发环境用 `container machine`。两者共享底层 VM 机制，但 `machine` 多了 rootfs 持久化、Home 目录映射、systemd 支持。
- **版本节奏**：1.0.0 之后三个月连发到 1.3.1，1.2.0 修了五个安全问题，1.3.0 移除了 `--scheme auto`——升级前读 release notes 是这个项目的必修课。

---

## 16. 资料口径说明

本文基于 apple/container 仓库（[apple/container](https://github.com/apple/container)）公开文档与源码整理，数据快照日期为 2026-09-07，需要说明的边界：

1. **版本时效性**：`container` 处于 "active development" 状态，稳定性只在 patch 版本之间有保证，minor 版本可能引入破坏性变更。
2. **平台限制**：当前仅支持 Apple silicon (ARM64)；macOS 26 为官方支持版本，macOS 15 可运行但有功能限制且不在官方支持范围。
3. **性能数据**：官方未发布 benchmark，文中性能描述均为官方文档的定性表述，未经标准化测试验证。
4. **适用边界**：`container` 的设计目标是为 macOS 提供原生容器工具，不适合 Linux 服务器或 Windows 环境。
