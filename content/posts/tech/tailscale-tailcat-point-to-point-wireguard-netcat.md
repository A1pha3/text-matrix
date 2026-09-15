---
title: "tailcat：剥掉控制面的 Tailscale，一只点对点 WireGuard 版 netcat"
date: 2026-09-07T03:23:17+08:00
draft: false
description: tailscale/tailcat 把 Tailscale 的数据面从整套控制面里拆出来，封装成一只不需要账号、不需要 root 的 netcat 式工具。本文拆解它的架构取舍、五种玩法、密钥信任模型与安全边界。
categories: ["技术笔记"]
tags: ["tailscale", "wireguard", "网络", "go"]
github_repo: "tailscale/tailcat"
source_key: "gh:tailscale/tailcat"
slug : tailscale-tailcat-point-to-point-wireguard-netcat
---

## 核心判断

tailcat 回答的问题很小，但答案很锋利：**如果你只想要两台机器之间有一条加密管道，为什么必须注册账号、安装客户端、加入一张 overlay 网络？**

它把 Tailscale 多年打磨的两个组件——WireGuard 加密的数据面 `magicsock` 和 DERP 中继——从整套协调服务器（control plane）里剥离出来，重新包装成一个 netcat 形态的 CLI 和 Go 库。连接元数据不再走控制面同步，而是变成一串可以贴进聊天窗口的临时地址（tailcat address）。一端 `tailcat` 起服务拿到地址，另一端拿地址连过来，中间是端到端 WireGuard 加密，能打洞就直连，打不动就走 DERP 中继兜底。

这不是玩具。它是 Tailscale 官方出品（口号就叫 "Tailscale without Tailscale, by Tailscale"），历史比开源历史长得多：2023 年 9 月就以 derpcat 之名诞生在一场长途航班上，此后多年住在 Tailscale 主仓库的 fork 里，随内部重构几度荒废，直到 2026 年 8 月的 TailscaleUp 大会才独立成库、正式开源。开源一个多月就连发 v0.2.0 到 v0.6.0 五个版本（截至 2026 年 9 月中），7.0k stars、BSD-3-Clause 协议。如果你对 tailscale/tailscale 主仓库的 mesh VPN 已经写过完整指南，可以把它看作同一技术栈的另一个切面——这篇文章只讲这个切面。

## 系统地图

理解 tailcat 只需要分清四层：

| 层 | 组件 | tailcat 里怎么处理 |
|---|---|---|
| 数据面 | WireGuard + magicsock | 保留。端到端加密、STUN 端点发现、NAT 打洞、点对点 UDP 直连 |
| 用户态网络栈 | Netstack（gVisor） | 保留。TCP 连接在进程内终结，不建 TUN 设备、不配路由和 DNS |
| 控制面 | 协调服务器、节点身份、ACL | 整体抛弃。连接元数据由用户自己带外传递 |
| 兜底通道 | DERP 中继 | 保留。默认用官方限速免费节点，可自建 derper |

最有趣的设计在"地址"上。一端启动监听后会打印一串形如 `tcomFwWC...` 的地址：`tc` 前缀加 base64 编码的 CBOR，典型长度约 140 字节。解开来看是四样东西——服务端的 WireGuard 公钥、一把独立的路径发现（path-discovery）公钥、默认还有一把独立的预共享密钥 pre-shared key（PSK），以及 DERP 区域信息（`tailcat parse` 可以不联网解开它看 JSON）。

那把 PSK 是"地址即凭证"的真正出处。隧道由 WireGuard 公钥和这把预共享密钥双重保护：DERP 运营方即使看到双方的公钥，也进不了隧道；对录下来的旧流量，它还提供一层后量子保护。换句话说，**Tailscale 控制面在 tailcat 里的替身，是你复制粘贴的那一下**。

由此换来三个"不需要"：

- 不需要 Tailscale 账号
- 不需要 root / 管理员权限——WireGuard 跑在用户态，TCP 连接由内嵌的 gVisor 网络栈在进程内终结，不改路由表、不动 DNS、不建内核网络设备
- 不需要预先组网——每次连接都是临时协商的

## 安装与最小示例

macOS 一行：

```sh
brew install tailcat
```

Windows 用 Scoop（包在 main bucket，不用加源）：`scoop install tailcat`。

其他渠道覆盖很全：GitHub Releases 提供静态 Linux 二进制（tar.gz）与 deb/rpm 包，覆盖 amd64、arm64、armv7，Windows zip 覆盖 amd64、arm64；ghcr.io/tailscale/tailcat 容器镜像；Nix（nixpkgs 或仓库自带的 flake）；AUR 有 tailcat / tailcat-bin 两个包；conda-forge 走 `pixi global install tailcat`。FreeBSD 和 OpenBSD 只剩一条路——`go install github.com/tailscale/tailcat/cmd/tailcat@latest`，官方说明预期可用但不做常规测试，CI 只保证能编译。

最 netcat 的用法，管道穿两台机器：

```sh
# 服务端（A 机），选定引导中继后打印临时地址，挂起等待
$ tailcat
# Selected bootstrap relay region 302, San Francisco
# 🐈 Server listening with new address: tcomFwWCCcjS5nKNqAod034nWoJZW0LZqDhhC8U_dKdnDRYQ8uNGFpGQEu

# 客户端（B 机）
$ echo hello | tailcat tcomFwWCCcjS5nKNqAod034nWoJZW0LZqDhhC8U_dKdnDRYQ8uNGFpGQEu

# 回到 A 机，管道解除阻塞，hello 落在 stdout
```

## 五种玩法，一个内核

tailcat 的子命令看起来花样不少，内核都一样：一段不需要控制面的 WireGuard 隧道，两端角色不同而已。

**1. 端口暴露（serve / forward）**

```sh
# A 机把本地 8080、8443 暴露出去（serve all 则暴露全部端口）
$ tailcat serve 8080,8443
# B 机连接并直接读到 HTTP 响应
$ tailcat tcXXXX 8080

# 或反向：把 A 机的端口映射成 B 机的本地端口，给浏览器/数据库客户端用
$ tailcat forward tcXXXX 18080:8080
```

`forward` 的本地监听默认只绑 `127.0.0.1`，端口号写 0 让系统挑一个空闲端口；只有当其他机器的客户端也要连进来时才需要 `--bind=0.0.0.0`。`serve exit-node` 模式配合三段式映射，能让客户端触达服务端所在网络里的任意 IP:port——相当于一次性版的 Tailscale exit node：

```sh
$ tailcat serve exit-node
$ tailcat forward tcXXXX 3001:172.23.52.30:3001
```

**2. SSH（serve ssh / no-auth-ssh）**

内置 SSH 服务器接受公钥认证，来源可以是本地 `authorized_keys`、字面公钥行、甚至 GitHub 账号——`user@github` 形式会在服务端启动前拉取一次 `github.com/user.keys`，多个来源逗号分隔：

```sh
$ tailcat serve --ssh-authorized-keys=bradfitz@github,./contractor.pub ssh
$ tailcat ssh tcXXXX ls -la
```

两个容易踩的硬规则：不带 `--ssh-authorized-keys` 的 `serve ssh` 直接启动失败——隧道层放行就用显式的 `no-auth-ssh`；authorized_keys 里的 `command=`、`from=` 选项不支持，遇到同样拒绝启动。

也提供 `no-auth-ssh`：隧道本身就是身份，免密登录。但要认清风险——**地址即凭证**，任何拿到地址的人都能以服务端运行者身份拿到 shell。README 用加粗警告反复强调：不要把 no-auth-ssh 的地址发布到任何公开渠道（包括 DNS TXT 记录）。

**3. inetd 式 exec**

```sh
$ tailcat serve exec -- /usr/bin/fortune
```

每来一条连接就执行一次命令，连接即 stdin/stdout，命令的 stderr 归服务端；命令还能从 `$TAILCAT_PEER_KEY` 和 `$TAILCAT_REMOTE_ADDR` 两个环境变量认出对端。配上 SSH 服务它就变成 OpenSSH `ForceCommand` 的角色——每条 SSH 会话只跑这一条命令，没有 shell、没有 SFTP：

```sh
$ tailcat serve no-auth-ssh -- git-upload-pack /srv/repo.git
```

把仓库裸暴露成一个只读 git 端点，客户端请求的命令则进 `$SSH_ORIGINAL_COMMAND`。

**4. 文件收发**

```sh
$ tailcat recv ~/inbox            # 收件箱：只写不读，发送方无法列目录/回读
$ tailcat cp report.pdf tcXXXX:   # 底层走系统 scp，进度条照常
$ tailcat serve files             # 或把目录只读/读写地供出去
```

细节做得克制：收件箱只写不读——发送方列不了目录、回读不了、也碰不了已有文件；`tailcat cp` 复用系统 `scp`（连接经 tailcat 隧道路由），进度条照常，`-r` 可传目录树；`serve files` 默认只读供出当前目录，`serve --files=/pub:rw files` 才开写。文件服务用 Go 的 `os.Root` 把路径锁死在被供目录内，`..` 和符号链接都逃不出去；`tailcat ls` 原生说 SFTP，机器上没装 OpenSSH 也能用，标准 `sftp`/`scp` 客户端配一条 ProxyCommand 同样能对着它用。传输不压缩（SFTP 协议本身没有压缩，Go 的 SSH 栈也刻意不带——传输层压缩有安全前科，TLS 后来也把它删了），在意体积请先 tar。

**5. 诊断与代理**

`tailcat ping` 每一跳回报走的是 DERP 还是直连路径，`--until-direct` 持续探测直到直连打通（超时默认 10 秒，打不通以非零码退出）：

```sh
$ tailcat ping --until-direct <tc-addr>
pong in 42.1ms via DERP(sfo)
pong in 1.2ms via 203.0.113.7:41641
```

`tailcat socks` 起本地 SOCKS5 代理把任意 CLI 工具的流量送进隧道；tailcat 地址甚至能直接当 URL 主机名用（`curl http://<tc-addr>:8081/`），因为 SOCKS 代理解析器认识它——但注意地址大小写敏感，浏览器会把主机名转小写所以不行。

## 密钥与信任模型

PSK 默认启用，对应的默认密钥模型是"每次启动都是新生"：服务端进程每次运行都现生成一把密钥，打印一个从未存在过的地址，进程一退，密钥丢弃、地址永久作废。你分享出去的地址只对这一次运行有效，泄不泄露都波及不到下一次。

想跨重启保住同一个地址，换 saved key 模式：`tailcat genkey` 把密钥落盘到 `~/.config/tailcat/keys/`，之后启动自动复用。代价随之而来——凡是曾经拿到过这个地址的人，往后都能连上任何一次用这把密钥起的服务，除非用 `serve --allow=<nodekey>` 把隧道限定到指定客户端。`default` 是个魔法键名：它一旦存在，光秃秃的 `tailcat` 命令就不再生成临时密钥而是复用它，`--key=new` 可强制回到一次性密钥；`genkey --list` 和 `genkey --delete` 管理存量。启动横幅会明说用的是哪一种，一眼可查。

地址还能发布成 DNS TXT 记录（格式 `tailcat=tc...`），之后任何接受 tailcat 地址的地方都能直接写域名：

```sh
client$ tailcat genkey --client --key=client-default
server$ tailcat genkey --key=default --fixed-region
server$ tailcat serve --allow=nodekey:cfb6bf...ddfd16 22
client$ tailcat ssh my-server.example.com
```

这造出一个没有任何入站端口的 SSH 服务：WireGuard 在 SSH 协议开始之前就完成了客户端认证，别人的握手被静默忽略，连"这台机器跑着 SSH"都探测不到。前提是服务端必须自己做客户端认证（`--allow` 或 `--ssh-authorized-keys`，二者至少其一）——TXT 记录是公开的、会被全网扫描，地址本身不再构成任何门槛。`tailcat ssh` 对 DNS 目标还留了一道保险：连接前先用一把陌生客户端密钥试探登录，如果服务器居然接受了，说明配置错了，它会拒绝连接并说明原因（`--skip-dns-safety-check` 可跳过）。

嫌短地址每次要查 DERP map 慢，`tailcat resolve` 把它展开成内嵌完整 DERP 信息的自包含长地址，`serve --full-address` 则让服务端直接打印长格式。自建 derper 也顺理成章：derper 需要一个带 TLS 证书的主机名（可经 Let's Encrypt 自取），`genkey --region=derp.example.com` 把中继主机名烘进地址，或用 `--derpmap-url` 指向自维护的 DERP map——客户端从此不碰 Tailscale 的任何服务器，限速政策也是你自己的。

## 一次连接的生命周期

把 README 的碎片拼成完整故事：

1. 服务端启动，生成（或加载）WireGuard 密钥对与默认的 PSK，连上 DERP 中继，把 tailcat 地址打到 stderr，然后等待
2. 用户通过任意渠道把地址送到客户端——聊天软件、邮件、口述都行；客户端解出公钥、路径发现密钥、PSK 与 DERP 区域，生成自己的临时密钥对，连到同一个 DERP
3. 发现握手：客户端经 DERP 发出一条名叫 "Meow" 的 ping，携带自己的节点公钥；服务端收到后把它加进 WireGuard 对端列表并重组网络配置，回一条 "Meowed"
4. 两侧互配为 WireGuard 对端后，WireGuard 握手开始（初期流量走 DERP），隧道就此立起
5. 打洞与握手并行：双方把 STUN 探到的公网端点和本地接口地址经 DERP 以 disco call-me-maybe 消息互换，随后尝试 UDP 打洞；成功则流量升级为直连（`ping --until-direct` 可验证），失败则 DERP 继续兜底——走官方公共中继时吞吐限速
6. 数据传输：客户端在隧道内拨 TCP 端口，两侧的 gVisor 用户态协议栈处理连接，服务端按端口分发给对应的服务

另有一个实验性 WebAssembly 版（<https://tailscale.github.io/tailcat/>），能与 CLI 互传文件和文本；浏览器端目前只能走 DERP 中继、尚无直连能力（WebRTC 支持在 issue #4 里）。

## 适用边界

tailcat 适合的场景有清晰轮廓：临时、点对点、双方都能敲命令、不想引入账号体系。传文件给同事、给承包商开一次 SSH、跨 NAT 调试一个内部端口——这些都是它的主场。

它不适合的也很明确：需要多于两个节点的 mesh、需要持久 ACL 与身份管理、需要服务发现——这些本来就是控制面要解决的问题，砍掉控制面换取简单，代价就在这里。凭证模型是"知道即拥有"：默认的临时地址一次运行一换，天然不产生撤销问题；换用 saved key 换取稳定地址后，收权就只剩 `--allow` 白名单一条路。两个兜底也要心里有数：官方公共 DERP 没有吞吐承诺和 SLA，随时可能限速或收回；Go API、CLI 参数和线上格式都明说不保证兼容，要固化进自动化流程，先把版本钉死。拿它当常驻基础设施用，是用错了工具。

一句话收束：**当你想的是"这两台机器通一下"而不是"我要建一张网"时，tailcat 就是那个最小正确的工具。**
