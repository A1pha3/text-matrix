---
title: "Hysteria 2：QUIC协议加持的抗审查代理工具完全指南"
date: "2026-05-14T10:45:00+08:00"
slug: "hysteria2-quic-proxy-guide"
description: "Hysteria是一款基于QUIC协议的高速、抗审查代理工具，支持SOCKS5、HTTP代理、TCP/UDP转发、TUN等丰富模式，以自定义QUIC协议伪装为HTTP/3流量，突破网络审查的同时提供卓越的传输性能。本文详细解析其核心原理、架构设计、安装配置与典型场景。"
draft: false
categories: ["技术笔记"]
tags: ["代理", "QUIC", "抗审查", "Go", "网络工具"]
---

# Hysteria 2：QUIC协议加持的抗审查代理工具完全指南

Hysteria（也称 Hysteria 2）是一个基于 **QUIC 协议**的高速、抗审查代理工具，由 Go 语言实现，编译为单一静态二进制文件，部署极简。与传统 Shadowsocks、V2Ray 等代理方案不同，Hysteria 从协议层面将流量伪装为标准 HTTP/3，从而在深度包检测（DPI）环境下也能保持连接畅通，同时借助 QUIC 的多路复用与丢包恢复机制，即使在不稳定网络下也能维持高吞吐。

## 核心能力速览

| 能力 | 说明 |
|------|------|
| 协议 | 自定义 QUIC，伪装为 HTTP/3 |
| 代理模式 | SOCKS5、HTTP Proxy、TCP/UDP 转发、TUN 模式 |
| 性能 | 专为丢包网络设计，超越 TCP |
| 跨平台 | macOS、Windows、Linux，ARM64 / x86_64 |
| 部署 | 单一静态二进制，无外部依赖 |

## 工作原理

### QUIC 协议基础

QUIC 是 Google 于 2012 年提出的传输层协议，2019 年成为 HTTP/3 的底层协议。与 TCP 相比，QUIC 的核心优势在于：

- **零往返建立连接（0-RTT）**：首次连接无需握手延迟
- **多路复用**：一条连接上并行多个数据流，不存在 TCP 的队头阻塞
- **丢包独立恢复**：一个流丢包不影响其他流
- **连接迁移（Connection Migration）**：网络切换（如 Wi-Fi 切蜂窝）时连接不中断

### Hysteria 的协议伪装

Hysteria 在 QUIC 之上构建了自己的控制平面与数据平面，并将流量特征伪装成标准 HTTP/3。具体来说：

- 客户端与服务器之间建立一条 QUIC 连接
- QUIC 握手阶段会发送 TLS 1.3 证书，与真实 HTTPS 流量无法区分
- DPI 设备看到的是一段带有标准 TLS 握手特征的 HTTP/3 流，而非代理协议握手

这使得 Hysteria 在中国大陆等部署了严格 DPI 的网络环境中，比普通代理协议更难被检测和封锁。

### 拥塞控制

Hysteria 内置了专为高丢包网络设计的拥塞控制算法（如 BBR 的变体），能够在卫星网络、跨国链路等高延迟高丢包环境下保持良好性能。

## 安装

### 官方脚本（一键）

```bash
# Linux/macOS
curl -fsSL https://get.hysteria.network | bash

# 或指定版本
curl -fsSL https://get.hysteria.network/@v2.5.0 | bash
```

### 二进制下载

从 [GitHub Releases](https://github.com/apernet/hysteria/releases) 下载对应平台压缩包，解压后得到 `hysteria` 可执行文件。

### Docker

```bash
docker run --rm \
  -v /path/to/config.toml:/etc/hysteria/config.toml \
  -p 443:443 \
  -p 443:443/udp \
  goofball404/hysteria server
```

## 配置

Hysteria 使用 TOML 格式配置文件。以下是典型场景的配置：

### 服务端

```toml
# /etc/hysteria/config.toml
[server]
bind = ":443"
tls = { cert = "/path/to/cert.crt", key = "/path/to/private.key" }

# 认证
auth = { type = "password", password = "your-secret-password" }

# 速度限制（可选）
# speed_limits = "1Gbps"
```

### 客户端

```toml
# config.toml
server = "your-server-ip:443"

# 认证密码（与服务端一致）
auth = { type = "password", password = "your-secret-password" }

# TLS 配置
tls = { insecure = false }  # 生产环境设为 false

# 代理协议（以 SOCKS5 为例）
socks5 = { listen = "127.0.0.1:1080" }
http = { listen = "127.0.0.1:8080" }
```

### 生成 TLS 证书（Let's Encrypt 示例）

```bash
certbot certonly --standalone -d your-domain.com --agree-tos -n -e tls-sni-01-challenge
# 证书路径：/etc/letsencrypt/live/your-domain.com/fullchain.pem
# 私钥路径：/etc/letsencrypt/live/your-domain.com/privkey.pem
```

## 运行

```bash
# 服务端
hysteria server -c /etc/hysteria/config.toml

# 客户端（后台运行）
hysteria client -c config.toml
```

## TUN 模式（推荐）

TUN 模式将 Hysteria 虚拟为一张网络设备，所有流量自动经代理转发，适合全局代理场景：

```toml
# 服务端 config.toml
[server]
tun = { name = "hysteria-tun", mtu = 1500 }
```

```toml
# 客户端 config.toml
tun = {
  name = "hysteria-tun",
  mtu = 1500,
  # 路由：默认所有流量走代理
  route = { default = true }
}
```

## 多用户与访问控制

```toml
[server]
# 基于 IP 的速率限制
rate_limit = "100Mbps"

# 允许特定 CIDR
allow_ip = ["10.0.0.0/8", "192.168.0.0/16"]

# 流量统计
traffic_stats = true
```

## 性能对比

> 数据来源为 Hysteria 官方测试，在 20% 丢包率的跨国链路上测试吞吐：

| 方案 | 平均吞吐 | 备注 |
|------|----------|------|
| 直连 TCP | ~5 Mbps | 受丢包严重影响 |
| WireGuard | ~35 Mbps | UDP 表现优于 TCP |
| Hysteria | ~85 Mbps | QUIC 多流+BBR 显著胜出 |

## 适用场景

- **高审查环境**：伪装为 HTTP/3，难以被 DPI 识别
- **高丢包网络**：跨国链路、卫星网络等 QUIC 优势明显
- **单端口多服务**：一条 443 端口承载 SOCKS5、HTTP、TUN 多种服务
- **轻量部署**：单一二进制，配合 cron 即可实现自动更新

## 注意事项

- **TLS 证书**：生产环境务必使用真实受信任的证书，不可自签（否则流量会被识别为异常）
- **端口 443 独占**：服务端 443 端口需未被占用
- **客户端与服务端版本需匹配**：跨大版本可能不兼容
- **TUN 模式需 root/管理员权限**

## 总结

Hysteria 2 通过 QUIC 协议的自定义实现，在抗审查与高性能之间取得了难得的平衡。对于身处高审查网络环境、同时对带宽质量有要求的用户，它是一个值得优先考虑的代理方案。其单文件部署、自动更新、TOML 配置等工程细节也降低了运维复杂度。

官网：[https://v2.hysteria.network](https://v2.hysteria.network)