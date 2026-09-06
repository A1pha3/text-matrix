---
title: "tailcat：剥掉控制面的 Tailscale，一只点对点 WireGuard 版 netcat"
date: 2026-09-07T03:23:17+08:00
draft: false
description: tailscale/tailcat 把 Tailscale 的数据面从整套控制面里拆出来，封装成一只不需要账号、不需要 root 的 netcat 式工具。本文拆解它的架构取舍、五种玩法与安全边界。
categories: ["技术笔记"]
tags: ["tailscale", "wireguard", "网络", "go"]
github_repo: "tailscale/tailcat"
source_key: "gh:tailscale/tailcat"
slug : tailscale-tailcat-point-to-point-wireguard-netcat
---

## 核心判断

tailcat 回答的问题很小，但答案很锋利：**如果你只想要两台机器之间有一条加密管道，为什么必须注册账号、安装客户端、加入一张 overlay 网络？**

它把 Tailscale 多年打磨的两个组件——WireGuard 加密的数据面 `magicsock` 和 DERP 中继——从整套协调服务器（control plane）里剥离出来，重新包装成一个 netcat 形态的 CLI 和 Go 库。连接元数据不再走控制面同步，而是变成一串可以贴进聊天窗口的临时地址（tailcat address）。一端 `tailcat` 起服务拿到地址，另一端拿地址连过来，中间是端到端 WireGuard 加密，能打洞就直连，打不动就走 DERP 中继兜底。

这不是玩具。它是 Tailscale 官方出品（口号就叫 "Tailscale without Tailscale, by Tailscale"），仓库创建于 2024 年 10 月，2026 年 9 月初已迭代到 v0.6.0、保持每日提交节奏，6.5k stars、BSD-3-Clause 协议。如果你对 tailscale/tailscale 主仓库的 mesh VPN 已经写过完整指南，可以把它看作同一技术栈的另一个切面——这篇文章只讲这个切面。

## 系统地图

理解 tailcat 只需要分清两层：

| 层 | 组件 | tailcat 里怎么处理 |
|---|---|---|
| 数据面 | WireGuard + magicsock | 保留。端到端加密、NAT 打洞、点对点 UDP 直连 |
| 控制面 | 协调服务器、节点身份、ACL | 整体抛弃。连接元数据由用户自己带外传递 |
| 兜底通道 | DERP 中继 | 保留。默认用官方限速免费节点，可自建 derper |

最有趣的设计在"地址"上。一端启动监听后会打印一串形如 `tcomFwWC...` 的地址，这串地址本身就是全部连接元数据——内含服务端的 WireGuard 公钥和 DERP 区域信息（`tailcat parse` 可以不联网解开它看 JSON）。客户端拿到地址即可发起连接。换句话说，**Tailscale 控制面在 tailcat 里的替身，是你复制粘贴的那一下**。

由此换来三个"不需要"：

- 不需要 Tailscale 账号
- 不需要 root / 管理员权限（纯 userspace，不改路由表、不动 DNS）
- 不需要预先组网——每次连接都是临时协商的

## 安装与最小示例

macOS 一行：

```sh
brew install tailcat
```

其他渠道覆盖很全：静态 Linux 二进制 / deb / rpm（amd64、arm64、armv7）、Windows zip、ghcr 容器镜像、Nix、AUR、conda-forge，或直接 `go install github.com/tailscale/tailcat/cmd/tailcat@latest`。

最 netcat 的用法，管道穿两台机器：

```sh
# 服务端（A 机），打印出临时地址后挂起等待
$ tailcat
🐈 Server listening with new address: tcomFwWCCcjS5nKNqAod034nWoJZW0LZqDhhC8U_dKdnDRYQ8uNGFpGQEu

# 客户端（B 机）
$ echo hello | tailcat tcomFwWCCcjS5nKNqAod034nWoJZW0LZqDhhC8U_dKdnDRYQ8uNGFpGQEu

# 回到 A 机，hello 落地
```

## 五种玩法，一个内核

tailcat 的子命令看起来花样不少，内核都一样：一段不需要控制面的 WireGuard 隧道，两端角色不同而已。

**1. 端口暴露（serve / forward）**

```sh
# A 机把本地 8080、8443 暴露出去
$ tailcat serve 8080,8443
# B 机连接并直接读到 HTTP 响应
$ tailcat tcXXXX 8080

# 或反向：把 A 机的端口映射成 B 机的本地端口，给浏览器/数据库客户端用
$ tailcat forward tcXXXX 18080:8080
```

`serve exit-node` 模式还能让客户端触达服务端所在网络里的任意 IP:port——相当于一次性版的 Tailscale exit node。

**2. SSH（serve ssh / no-auth-ssh）**

内置 SSH 服务器接受公钥认证，来源可以是本地 `authorized_keys`、字面公钥行、甚至 GitHub 账号：

```sh
$ tailcat serve --ssh-authorized-keys=bradfitz@github,./contractor.pub ssh
$ tailcat ssh tcXXXX ls -la
```

也提供 `no-auth-ssh`：隧道本身就是身份，免密登录。但要认清风险——**地址即凭证**，任何拿到地址的人都能以服务端运行者身份拿到 shell。README 用加粗警告反复强调：不要把 no-auth-ssh 的地址发布到任何公开渠道（包括 DNS TXT 记录）。

**3. inetd 式 exec**

```sh
$ tailcat serve exec -- /usr/bin/fortune
```

每来一条连接就执行一次命令，连接即 stdin/stdout；配合 ssh 服务还能当 ForceCommand 用（如 `serve ssh -- git-upload-pack /srv/repo.git`，把仓库裸暴露成一个只读 git 端点）。

**4. 文件收发**

```sh
$ tailcat recv ~/inbox            # 收件箱：只写不读，发送方无法列目录/回读
$ tailcat cp report.pdf tcXXXX:   # 底层走系统 scp，进度条照常
$ tailcat serve files             # 或把目录只读/读写地供出去
```

细节做得克制：文件服务用 Go 的 `os.Root` 把路径锁死在被供目录内，`..` 和符号链接都逃不出去；`tailcat ls` 原生说 SFTP，机器上没装 OpenSSH 也能用。传输不压缩（SFTP 与 Go SSH 栈都刻意不带压缩，理由是传输层压缩的安全前科），在意体积请先 tar。

**5. 诊断与代理**

`tailcat ping` 每一跳回报走的是 DERP 还是直连路径；`tailcat socks` 起本地 SOCKS5 代理把任意 CLI 工具的流量送进隧道；tailcat 地址甚至能直接当 URL 主机名用（`curl http://<tc-addr>:8081/`），因为 SOCKS 代理解析器认识它——但注意地址大小写敏感，浏览器会把主机名转小写所以不行。

## 一次连接的生命周期

把 README 的碎片拼成完整故事：

1. 服务端启动，生成临时 WireGuard 密钥对，打印 tailcat 地址（含公钥 + DERP 区域）
2. 用户通过任意渠道把地址送到客户端——聊天软件、邮件、口述都行
3. 客户端先经 DERP 中继引导连接（默认 DERP map 来自 tailcat.dev，可自建 derper 完全私有化）
4. magicsock 同时尝试 NAT 打洞，成功后升级为点对点 UDP 直连（`ping --until-direct` 可以验证）
5. 全程端到端 WireGuard 加密，即使流量经过 DERP 中继，中继也只见密文

另有一个实验性 WebAssembly 版（<https://tailscale.github.io/tailcat/>），浏览器端目前只能走 DERP 中继、尚无直连能力（WebRTC 支持在 issue #4 里）。

## 适用边界

tailcat 适合的场景有清晰轮廓：临时、点对点、双方都能敲命令、不想引入账号体系。传文件给同事、给承包商开一次 SSH、跨 NAT 调试一个内部端口——这些都是它的主场。

它不适合的也很明确：需要多于两个节点的 mesh、需要持久 ACL 与身份管理、需要服务发现——这些本来就是控制面要解决的问题，砍掉控制面换取简单，代价就在这里。地址是短命的、凭证模型是"知道即拥有"、没有撤销机制（一次连接一段密钥，断了就换）。拿它当常驻基础设施用，是用错了工具。

一句话收束：**当你想的是"这两台机器通一下"而不是"我要建一张网"时，tailcat 就是那个最小正确的工具。**
