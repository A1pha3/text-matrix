---
title: "Hysteria：基于 QUIC 协议的高性能抗审查代理工具"
date: "2026-05-14T12:45:00+08:00"
slug: "hysteria-quic-proxy-censorship-resistance"
description: "Hysteria 是一款基于定制 QUIC 协议的高速、抗审查代理工具，支持 SOCKS5、HTTP Proxy、TCP/UDP 转发和 TUN 模式，通过将流量伪装为标准 HTTP/3 数据包在不稳定和丢包严重的网络环境下仍能保持卓越性能，GitHub 今日新增约 485 星。"
draft: false
categories: ["技术笔记"]
tags: ["代理", "QUIC", "抗审查", "网络", "隐私"]
---

## 项目概览

Hysteria 是 apernet 团队推出的代理工具，与传统基于 TCP 的代理方案不同，它构建在定制版 QUIC 协议之上，专为不稳定和高丢包网络环境设计。GitHub 今日新增约 485 星，项目提供全平台架构的预编译二进制，并拥有丰富的第三方客户端适配。

核心设计目标有两个：一是性能，在丢包和高延迟环境下依然保持高吞吐；二是隐蔽性，协议流量伪装为标准 HTTP/3，难以被深度包检测（DPI）识别和阻断。

## 核心技术：定制 QUIC 协议

QUIC 是 Google 主导的网络协议标准，也是 HTTP/3 的底层传输协议。Hysteria 使用了自己定制的 QUIC 实现，相比标准 QUIC 有以下关键改动：

**拥塞控制优化：** 在丢包严重的环境下，标准 QUIC 的 CUBIC 或 BBR 拥塞控制会保守地大幅缩减发送窗口。Hysteria 的拥塞控制算法针对"高丢包高延迟"链路做了专门优化，在恶劣环境下仍能维持较高吞吐量。

**前向纠错（FEC）：** Hysteria 支持可选的前向纠错机制，在部分数据包丢失时通过冗余数据恢复，而非等待重传。这对于卫星链路、移动网络等高延迟场景尤为关键。

**连接迁移（Connection Migration）：** 移动网络切换 Wi-Fi/4G 时，标准 TCP 连接会中断。QUIC 的连接迁移特性允许 Hysteria 在网络路径变化时保持连接不断开。

## 多模式支持

Hysteria 提供了丰富的代理模式，覆盖绝大多数使用场景：

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| SOCKS5 Proxy | 标准 SOCKS5 代理协议 | 浏览器、应用全局代理 |
| HTTP Proxy | HTTP CONNECT 代理 | Web 流量透明代理 |
| TCP Forward | TCP 端口转发 | 游戏、远程桌面等 TCP 应用 |
| UDP Forward | UDP 端口转发 | VoIP、视频流等 UDP 应用 |
| TUN Mode | 透明代理（类似 VPN） | 全局流量代理，支持 TUN 接口的系统 |

这种多模式设计使 Hysteria 既可以作为单应用代理工具，也可以作为全局流量管理方案。对于需要在公司网络中透明代理特定目标流量的场景，TUN 模式提供了不需要修改应用配置的解决方案。

## 抗审查机制

Hysteria 协议的隐蔽性是其区别于普通代理的关键。QUIC 协议本身是 HTTP/3 的传输层，标准 HTTPS 流量也基于 QUIC。这意味着 Hysteria 的流量在 DPI（深度包检测）设备看来，与普通的 Google、Cloudflare HTTPS 请求没有本质区别。

检测并阻断这种流量需要censorship 系统进行 HTTPS 指纹分析或主动探测（Active Probing），而非简单的协议特征匹配。但这种深度检测有极高的误判风险——如果一个审查系统开始阻断所有 HTTPS 流量，其后果将是互联网的大规模中断。因此，Hysteria 在多数审查环境下具备天然的通过能力。

## 快速上手

服务端部署（Linux amd64）：

```bash
# 下载服务端二进制
wget https://github.com/apernet/hysteria/releases/latest/download/hysteria-linux-amd64
chmod +x hysteria-linux-amd64

# 生成认证密钥（可选）
openssl rand -base64 32

# 启动服务端
./hysteria-linux-amd64 server -c config.json
```

客户端配置示例（`config.json`）：

```json
{
  "server": "your-server-domain:443",
  "auth": {
    "type": "password",
    "password": "your-auth-password"
  },
  "bandwidth": {
    "up": "10 Mbps",
    "down": "50 Mbps"
  },
  "socks5": {
    "listen": "127.0.0.1:1080"
  },
  "http": {
    "listen": "127.0.0.1:8080"
  }
}
```

```bash
# 启动客户端
./hysteria-linux-amd64 client -c config.json
```

配置中的 `bandwidth` 字段用于协商速率上限，服务端据此优化流控参数。

## 适用场景

- **高丢包网络环境**：移动热点、海外云服务跨洲传输等高延迟链路
- **审查严格地区的抗审查通信**：需要隐蔽流量的场景
- **游戏加速**：针对 UDP 流量的优化有助于降低游戏延迟
- **替代传统 VPN**：在 TUN 模式下实现全局代理，部署比 OpenVPN 更简单

## 优势与局限

Hysteria 的优势在于 QUIC 协议在恶劣网络环境下的性能优势，以及流量伪装带来的抗审查能力。但需要注意：作为代理工具，用户需自行确保部署目的的合法性；服务端需要拥有可访问的公网域名和 TLS 证书；Hysteria 并不提供完整的科学上网解决方案，需要配合实际可用的网络出口使用。

## 总结

Hysteria 代表了新一代代理工具的设计思路：用现代传输协议（QUIC）解决传统代理在复杂网络环境下的性能问题，用协议伪装解决内容审查问题。对于需要稳定跨洲传输、或在高审查环境下保持连接的技术用户，Hysteria 提供了开箱即用的高效方案。