---
title: "Hysteria 2：QUIC 协议加持的抗审查代理工具完全指南"
date: "2026-05-14T10:45:00+08:00"
slug: "hysteria2-quic-proxy-guide"
github_repo: "apernet/hysteria"
aliases:
  - "/posts/tech/hysteria-quic-proxy-censorship-resistance/"
description: "Hysteria 2 是一款基于 QUIC 的开源抗审查代理工具：默认将流量伪装成真实的 HTTP/3 网站访问，配合自研的 Brutal 拥塞控制在高丢包链路上保持吞吐，并提供 obfs 混淆、端口跳跃等分层对抗手段。本文基于 v2.12 官方文档，覆盖服务端部署、客户端配置、TUN 模式与常见问题排查。"
draft: false
categories: ["技术笔记"]
tags: ["代理", "Go", "网络工具"]
---

# Hysteria 2：QUIC 协议加持的抗审查代理工具完全指南

Hysteria 是 apernet 开源的抗审查代理工具，用 Go 编写，服务端和客户端是同一个二进制。它基于 QUIC，默认把流量伪装成一个真实的 HTTP/3 网站，再用自研的 Brutal 拥塞控制在高丢包链路上保住吞吐。本文基于 2026 年 8 月发布的 v2.12.2 官方文档整理，配置示例采用 YAML（官方文档格式）；Hysteria 同样完整支持 TOML 与 JSON，扩展名对应即可。

## 学习目标
读完本文后，你将能够：
1. 说清 Hysteria 的协议原理与分层抗审查机制（网站伪装、obfs 混淆、端口跳跃）
2. 在 Linux 服务器上完成服务端部署：安装、证书、配置、systemd 管理
3. 按场景配置客户端代理模式（SOCKS5/HTTP/TUN）与带宽声明
4. 排查部署与性能上的常见问题：连接失败、速度不达预期、TUN 异常

## 文章目录
1. [核心能力速览](#核心能力速览)
2. [工作原理](#工作原理)
3. [安装](#安装)
4. [服务端配置](#服务端配置)
5. [客户端配置](#客户端配置)
6. [运行与验证](#运行与验证)
7. [TUN 模式](#tun-模式)
8. [端口跳跃](#端口跳跃)
9. [多用户与流量统计](#多用户与流量统计)
10. [性能调优](#性能调优)
11. [适用场景](#适用场景)
12. [常见问题解答](#常见问题解答)
13. [总结与进阶路径](#总结与进阶路径)

---

## 核心能力速览

| 能力 | 说明 |
|------|------|
| 协议 | 基于 QUIC，默认伪装为 HTTP/3 网站流量 |
| 抗审查 | 真实证书 + 网站伪装、obfs 混淆、端口跳跃、Fake TCP（mimic）、ECH |
| 代理模式 | SOCKS5、HTTP、TCP/UDP 端口转发、透明代理（Linux）、TUN |
| 拥塞控制 | Brutal（按声明带宽）或 BBR / Reno |
| 跨平台 | Windows、macOS、Linux、Android、FreeBSD |
| 部署 | 单一静态二进制，官方脚本可一键注册 systemd 服务 |

## 工作原理

### QUIC 与 HTTP/3

QUIC 由 Google 设计并长期在其自家服务上实验，2013 年对外公布，后由 IETF 完成标准化（RFC 9000，2021 年）；HTTP/3（RFC 9114，2022 年）即构建在 QUIC 之上。与 TCP 相比，它有几个对代理场景关键的性质：

- **握手与加密一体**：首次连接一个 RTT（往返时延）就完成传输握手和 TLS 1.3 密钥交换；会话恢复时可以做到 0-RTT。TCP 需要先完成自身握手，再单独走一遍 TLS 握手。
- **流级多路复用**：一条连接承载多条相互独立的流，一条流丢包不会阻塞其他流。TCP 把所有数据排在同一条字节流里，丢一个包，整条连接都得等它重传（队头阻塞）。
- **连接迁移**：QUIC 用 Connection ID 而非「源 IP + 端口」标识连接，Wi-Fi 切到蜂窝这类网络切换不会中断连接。
- **强制加密**：TLS 1.3 内置于协议之中，连报文头部的大部分字段也被加密。

### 一台经得起探测的 HTTP/3 服务器

Hysteria 的抗审查思路是让流量看起来就是普通的网站访问。默认情况下，Hysteria 协议模仿 HTTP/3：客户端与服务端之间的 QUIC 握手使用真实的 TLS 1.3 证书（通常由内置 ACME 自动签发）。更关键的是 masquerade（伪装）机制——对没有通过认证的连接，服务端会把它交给一个真正的网站来响应：可以代理到另一个站点，可以静态托管一个目录，也可以返回一段固定的字符串。审查者主动探测你的 443 端口时，看到的就是一个 HTTP/3 网站；不配置 masquerade 时，所有请求得到 404。

在此之上还有几层可叠加的手段：

- **Chrome 指纹模仿**：自 v2.11.0 起，客户端的 QUIC 握手默认调整得与 Google Chrome 一致，让握手指纹难以被识别，可用 `quic.disableChromeParrot` 关闭。
- **obfs 混淆**：如果所在网络直接封锁 QUIC 或 HTTP/3（而非 UDP 本身），可以开启 Salamander 或 Gecko 混淆，把每个数据包打乱成无规律的随机字节。代价是服务端不再表现为合法的 HTTP/3 服务。
- **端口跳跃**：应对针对特定端口的 UDP 限速或封锁，详见下文。
- **mimic（Fake TCP）**：UDP 被整体封锁时的最后手段，v2.12.0 引入，在 Linux 上把整个连接伪装成 TCP，需要单独安装 mimic 及其内核模块。
- **ECH**：Encrypted Client Hello，把 TLS 握手中的服务器域名信息（SNI）也加密，避免域名在中间链路上泄露。

### 拥塞控制：Brutal

Hysteria 默认使用自研的 Brutal 拥塞控制，这是它"高丢包链路也能跑满"的原因。Brutal 是固定速率模型：客户端在配置里声明自己的上下行带宽，双方按这个速率发包，不因丢包或延迟波动而退让；发生丢包时，它反而按比例提高发送速率来补偿。这让它在跨境长链路上能保持吞吐，但有一个硬性前提——带宽必须声明得准。官方明确警告：声明值超过链路实际上限会适得其反，造成拥塞和不稳定的慢速连接。

未声明带宽，或服务端开启 `ignoreClientBandwidth` 时，走传统算法：BBR（默认，另有 conservative / aggressive 两档 profile）或 Reno。服务端 `bandwidth` 里的限速值只对 Brutal 方向生效。

## 安装

### 部署脚本（Linux 服务端）

官方脚本自动下载最新版并注册 systemd 服务，支持安装、升级、卸载：

```bash
# 安装或升级到最新版
bash <(curl -fsSL https://get.hy2.sh/)

# 安装指定版本
bash <(curl -fsSL https://get.hy2.sh/) --version v2.12.2

# 卸载
bash <(curl -fsSL https://get.hy2.sh/) --remove
```

脚本只会生成一份示例配置（`/etc/hysteria/config.yaml`），改好配置后再启动服务。要求 systemd，主流发行版近两年的稳定版即可（Debian 11+、Ubuntu 22.04 LTS+ 等）；OpenWrt、Alpine、NixOS 不在支持之列。

### 预编译二进制

从 [GitHub Releases](https://github.com/apernet/hysteria/releases) 下载对应平台的可执行文件，Windows、macOS、Linux、Android、FreeBSD 全平台覆盖，x86、ARM64、MIPS、RISC-V 等架构齐全，部分平台另有要求 AVX 的变体。脚本和自动化场景可用固定地址 `https://download.hysteria.network/app/latest/hysteria-linux-amd64`，它始终重定向到最新版。

### Docker

官方镜像为 `tobyxdd/hysteria`，Compose 示例：

```yaml
services:
  hysteria:
    image: tobyxdd/hysteria
    container_name: hysteria
    restart: always
    network_mode: "host"
    cap_add:
      - NET_ADMIN
    volumes:
      - acme:/acme
      - ./hysteria.yaml:/etc/hysteria.yaml
    command: ["server", "-c", "/etc/hysteria.yaml"]

volumes:
  acme:
```

`NET_ADMIN` 只在启用端口跳跃时需要。

## 服务端配置

前置条件：一台有公网 IP 的服务器，一个已解析到它的域名。下面是一份完整可运行的最小配置，证书由内置 ACME 自动申请和续期：

```yaml
listen: :443

acme:
  domains:
    - vpn.example.com
  email: me@example.com

auth:
  type: password
  password: your-strong-password   # 换成强密码

masquerade:
  type: proxy
  proxy:
    url: https://some.site.net/
    rewriteHost: true
```

几个字段的含义：

- `listen`：监听地址，省略时默认 `:443`。省略 IP 表示同时监听 IPv4 和 IPv6。
- `acme`：证书自动签发。`ca` 可选 `letsencrypt` 或 `zerossl`。证书申请走标准端口（HTTP challenge 用 80，TLS-ALPN 用 443），改用其他端口需要自己做端口转发或反代，否则验证会失败。`tls` 与 `acme` 二选一；如果你已有现成证书，改用 `tls: { cert: ..., key: ... }`，文件在每次 TLS 握手时读取，更新后无需重启。
- `auth`：单用户用 `password`；多个用户见下文「多用户与流量统计」。
- `masquerade`：认证失败流量的去向。`proxy` 模式把探测请求反代到真实网站，`file` 模式托管静态目录，`string` 模式返回固定内容。

## 客户端配置

```yaml
server: vpn.example.com:443

auth: your-strong-password        # 与服务端一致

bandwidth:
  up: 30 mbps
  down: 100 mbps

socks5:
  listen: 127.0.0.1:1080

http:
  listen: 127.0.0.1:1080

lazy: true
```

- `server`：只写域名时默认端口 443。也接受 `hysteria2://` 分享链接（此时密码等已含在 URI 中，不能再单独配置）。
- `tls`：这份配置里没写，因为使用 ACME 签发的受信任证书时，验证所需的 SNI 会自动从 `server` 域名提取。
- `bandwidth`：触发 Brutal 的开关，按链路真实上限填写。客户端实际速率取「本地声明」与「服务端限速」中较小的一方。
- `socks5` 与 `http`：自 v2.4.1 起，两个模式配置完全相同的 `listen` 地址，就能在同一个端口上同时服务 SOCKS5 和 HTTP 两种协议。
- `lazy: true`：启动时不立即连接服务器，等到有流量进来才连，适合网络就绪时机不确定的环境（开机自启的客户端尤其有用）。

## 运行与验证

用部署脚本安装后，服务由 systemd 管理：

```bash
nano /etc/hysteria/config.yaml           # 修改配置
systemctl enable --now hysteria-server.service
systemctl restart hysteria-server.service
journalctl --no-pager -e -u hysteria-server.service   # 查看日志
```

客户端直接运行二进制：

```bash
hysteria client -c config.yaml
```

验证链路是否通，最直接的办法是让流量走一遍代理：

```bash
curl --proxy socks5h://127.0.0.1:1080 https://www.cloudflare.com/cdn-cgi/trace
```

返回内容中 `ip=` 显示为服务器地址即为生效。服务端开启 `speedTest: true` 后，还可以对服务器做上下行测速，验证真实带宽。

## TUN 模式

SOCKS5/HTTP 代理只覆盖支持代理协议的应用。TUN 模式创建一块虚拟网卡，用系统路由接管全部流量，跨 Windows、Linux、macOS 可用：

```yaml
tun:
  name: hytun
  mtu: 1500
  address:
    ipv4: 100.100.100.101/30
    ipv6: 2001::ffff:ffff:ffff:fff1/126
  route:
    ipv4: [0.0.0.0/0]
    ipv6: ["2000::/3"]
    ipv4Exclude:
      - 198.51.100.10   # 换成你的服务器地址，否则路由回环
```

使用前有四件事需要知道：

1. **TUN 只转发 TCP 和 UDP**，不支持 ICMP 等其他协议。开着 TUN 去 `ping` 任何网站都不通，这是预期行为，不代表代理坏了；验证要用 TCP/UDP 流量。
2. **`ipv4Exclude` 必须填服务器地址**。默认路由指向 TUN 网卡后，发往服务器的流量会绕回 TUN 自己，形成回环。`route` 的其余字段都可以省略，多数场景下只填 Exclude 就够了。
3. **macOS 上接口名必须以 `utun` 加数字命名**，比如 `utun123`。
4. **Linux 上可能需要关闭反向路径校验**：`sysctl net.ipv4.conf.default.rp_filter=2` 与 `sysctl net.ipv4.conf.all.rp_filter=2`。TUN 需要 root 或管理员权限；FreeBSD 不支持 TUN。

## 端口跳跃

不少 ISP 对长时间大流量的 UDP 连接做限速或阻断，且往往只针对单一端口。端口跳跃让客户端在一个端口区间内周期性跳换，单个端口被限了就换下一个。

服务端（Linux）直接把监听写成端口范围，防火墙重定向规则由 Hysteria 自动配置和清理，需要 root 或 `CAP_NET_ADMIN` 权限：

```yaml
listen: :20000-50000
```

客户端把地址写成多端口格式，跳换间隔由 `transport` 控制（默认固定 30 秒，最短 5 秒；也可用 `minHopInterval`/`maxHopInterval` 做随机间隔，更难被识别）：

```yaml
server: vpn.example.com:20000-50000

transport:
  type: udp
  udp:
    hopInterval: 30s
```

两点边界：UDP 被整体封锁（而非针对端口）时，端口跳跃无济于事，出路是 mimic；mimic 与端口跳跃不能同时使用。

## 多用户与流量统计

多用户认证改用 `userpass`，客户端的 `auth` 相应写成 `用户名:密码`：

```yaml
auth:
  type: userpass
  userpass:
    alice: password1
    bob: password2
```

限制单个用户的速率，用服务端 `bandwidth`（注意它只约束 Brutal 方向）：

```yaml
bandwidth:
  up: 100 mbps
  down: 100 mbps
```

需要按用户统计流量或踢人下线时，开启 Traffic Stats API：

```yaml
trafficStats:
  listen: 127.0.0.1:9999
  secret: 一个用于鉴权的密钥
```

API 通过 HTTP 查询，`secret` 务必设置，否则任何能访问该地址的人都能看到流量数据并踢掉用户。

## 性能调优

QUIC 是用户态协议，CPU 开销天然高于内核态的 TCP。速度上不去时，先分清瓶颈在链路、CPU 还是系统配置：

**系统缓冲区**。Linux 默认值对高速 QUIC 偏小，调大收发缓冲区：

```bash
sysctl -w net.core.rmem_max=16777216
sysctl -w net.core.wmem_max=16777216
```

macOS/BSD 对应的是 `kern.ipc.maxsockbuf`。

**流控接收窗口**。客户端和服务端的 `quic` 配置里有四个窗口参数，默认流窗口 8 MB、连接窗口 20 MB，并带自动伸缩机制；大带宽场景可调大，调整时保持流窗口与连接窗口约 2:5 的比例，避免个别阻塞的流占满整个连接。

**进程优先级**。CPU 紧张的设备上，高负载会引起延迟抖动。systemd 部署可在 `/etc/systemd/system/hysteria-server.service.d/priority.conf` 中加 `Nice=-5`，然后 `systemctl daemon-reload && systemctl restart hysteria-server.service`。

**带宽声明**。这是最常见的「速度慢」根因：Brutal 完全依赖客户端声明的带宽值，声明低了跑不满，声明高了引发拥塞反而更慢。先用有线网络直连测一次真实速率，再据此填写。

## 适用场景

- **高审查网络**：真实证书加网站伪装，主动探测看到的是 HTTP/3 服务器；握手指纹模仿 Chrome；配合 obfs 与 ECH 可以应对协议级封锁。
- **高丢包、高延迟链路**：Brutal 按声明速率发包、不退让，跨境卫星链路、拥塞的国际出口是它的主场。
- **弱网或端口受限环境**：端口跳跃绕开单端口限速，mimic 在 UDP 整体被封时伪装成 TCP。
- **家庭宽带无公网 IP**：Realms（v2.9.0 起）通过 NAT 打洞实现 P2P 直连，无需端口转发和中转。

## 常见问题解答

### Q1：服务端启动失败，提示 443 端口被占用或无权限？

443 被占用时，`ss -lnup | grep 443` 找到占用进程（常见的是 Nginx、Caddy），换端口或让 Hysteria 顶替它。绑定 1024 以下的端口需要特权：systemd 部署的脚本服务已处理好权限；手动运行则用 root，或给二进制赋予 `CAP_NET_BIND_SERVICE` capability。改用 8443 之类的非标准端口可以省去这些麻烦，但伪装的隐蔽性会下降——正常网站的 HTTP/3 就在 443。

### Q2：客户端连上了，但速度远低于预期？

按顺序检查三件事：一是 `bandwidth` 声明是否符合链路真实上限（见「性能调优」一节）；二是系统缓冲区是否还是默认值，Linux 上 `rmem_max`/`wmem_max` 各调到 16 MB 再试；三是服务器 CPU 是否打满——廉价 VPS 的单核性能撑不起高速 QUIC，这不是调参能解决的。

### Q3：TLS 证书验证失败？

生产环境用 ACME 自动签发即可，受信任且免维护。本地测试用自签证书时，客户端可以设 `tls.insecure: true` 跳过验证；更稳妥的做法是填 `tls.pinSHA256` 固定证书指纹，既不依赖 CA 又不受中间人影响。用 openssl 获取指纹：`openssl x509 -noout -fingerprint -sha256 -in your_cert.crt`。

### Q4：TUN 模式起了但用不了？

先确认测试方式：TUN 不转发 ICMP，`ping` 不通是正常的，用浏览器或 `curl` 验证。再查路由回环：服务器地址必须写在 `ipv4Exclude`/`ipv6Exclude` 里。macOS 检查接口名是否为 `utun` 加数字；Linux 上若网卡收不到流量，尝试关闭 `rp_filter`（见 TUN 一节）。Windows Server 2022 和 CentOS 7 需要关闭防火墙，CentOS 7 的老内核还有路由规则缺陷，建议升级内核到 4.17 以上。

## 总结与进阶路径

Hysteria 2 的设计思路清晰：伪装做在协议层（HTTP/3 站点 + 真实证书），性能做在拥塞层（Brutal 固定速率），对抗手段按封锁强度分层递进（端口跳跃 → obfs → mimic）。它适合对吞吐和抗审查都有要求的场景；代价是 Brutal 需要准确声明带宽，QUIC 的用户态实现也比 TCP 代理更吃 CPU。如果你在用 sing-box 或 3rd-party 客户端，Hysteria 2 协议同样被广泛支持，服务端照常部署即可。

进阶方向：

1. 结合 [s-ui]({{< relref "posts/tech/s-ui-sing-box-web-panel-quickstart.md" >}}) 做可视化的多协议面板管理
2. 用 [CLIProxyAPI]({{< relref "posts/tech/cliproxyapi-unified-ai-cli-proxy.md" >}}) 统一管理 AI CLI 工具的请求出站
3. 部署多层 ACL 出站规则（分流、拒绝、GeoIP），参考官方 [ACL 文档](https://hysteria.network/docs/advanced/ACL/)
4. 追踪官方 [Changelog](https://hysteria.network/docs/Changelog/)，2.x 迭代很快，近期版本在持续加入 mimic、ECH、Realms 等新能力

---

## 自测问题
### 题 1：Hysteria 的抗审查核心机制是什么？
<details>
<summary>参考答案</summary>
不是隐藏流量，而是让它成为"合法流量"：QUIC 握手使用真实 TLS 1.3 证书，协议默认模仿 HTTP/3；认证失败的连接由 masquerade 接管，表现为一个正常网站。在此之上可叠加 Chrome 握手指纹模仿、obfs 混淆（对抗协议封锁）、端口跳跃（对抗单端口限速）与 mimic Fake TCP（对抗 UDP 整体封锁）。
</details>

### 题 2：Brutal 拥塞控制为什么在高丢包链路上快？使用前提是什么？
<details>
<summary>参考答案</summary>
Brutal 是固定速率模型：按客户端声明的带宽恒速发包，不因丢包或 RTT 波动退让，丢包时反而加速补偿，因此在高丢包链路上能保持吞吐。前提是带宽声明必须准确——声明超过链路实际上限会造成拥塞，连接又慢又不稳定；未声明带宽时回退到 BBR（默认）或 Reno。
</details>

### 题 3：客户端配置了 TUN 模式后 ping 不通任何网站，代理是否坏了？
<details>
<summary>参考答案</summary>
大概率没有。TUN 只转发 TCP 和 UDP，不支持 ICMP，ping 不通是预期行为，应该用浏览器或 curl 验证。若 TCP/UDP 流量也不通，依次检查：服务器地址是否写入了 ipv4Exclude（排除路由回环）、macOS 接口名是否为 utun 加数字、Linux 是否需要关闭 rp_filter。
</details>

---

## 注意事项

- **obfs 密码两端必须一致**：密码不对时的表现是连接超时，与服务器宕机无异，排错时先查它。
- **不要用 Hysteria 代理 HTTP/3 流量**：QUIC 流量走 QUIC 隧道不会被"加速"，速度取决于两端各自的拥塞控制；浏览器走 HTTP 代理时会自动回落到 HTTP/2，无需干预。
- **证书类型与 Chrome 指纹模仿的兼容性**：模仿 Chrome 握手时，Ed25519 证书会握手失败，请使用 ECDSA 或 RSA 证书；ACME 签发的证书不受影响。
- **客户端与服务端同步升级**：跨版本混用可能出兼容问题（如 v2.8.2 曾因握手参数调整导致新旧版本之间 UDP 转发失效），两端一起升级最稳。
