---
title: "CFnew - Cloudflare Workers 代理订阅管理面板"
date: "2026-05-23T15:30:00+08:00"
slug: cfnew-cloudflare-workers-proxy-subscription-manager
description: "CFnew 是一款基于 Cloudflare Workers 和 Pages 的代理订阅管理工具，支持 VLESS、Trojan、xhttp 多协议，可生成 Clash、Surge、Sing-box 等多种客户端配置。"
tags: [Cloudflare, Workers, Proxy, VLESS, Trojan, Clash, Surge, Sing-box, 代理, 网络工具]
categories: ["技术笔记"]
author: 钳岳星君
---

[byJoey/cfnew](https://github.com/byJoey/cfnew) 是今日 GitHub Trending 的一员，13,364 颗星、6,489 个 Fork。这是一个运行在 Cloudflare Workers/Pages 上的代理订阅管理面板，支持多协议、多客户端、多语言，功能相当完整。

## 功能概览

### 多协议支持

- **VLESS**：主要传输协议
- **Trojan**：加密传输
- **xhttp**：新一代传输方式

可同时启用多个协议，满足不同场景需求。

### 订阅格式生成

一键生成以下客户端配置：

| 客户端 | 格式 |
|--------|------|
| Clash | YAML |
| Surge | CONF |
| Sing-box | JSON |
| Loon | CONF |
| Quantumult X | CONF |
| V2RAY | JSON |
| Shadowrocket | CONF |
| Stash | YAML |
| Nekoray | CONF |

这意味着无论你用什么代理客户端，都能用 CFnew 统一管理订阅。

### 图形化管理界面

所有配置通过 Web UI 管理，核心亮点：

- **自定义路径**：不用 UUID 当路径，可以自己设置，支持多级路径
- **KV 存储**：配置修改立即生效，无需重新部署
- **延迟测试**：内置测试工具，测试 IP 延迟，自动获取机场码
- **订阅转换**：可自定义转换服务地址

### 高级功能

| 功能 | 说明 |
|------|------|
| 多语言 | 支持中文、波斯语，自动根据浏览器语言切换 |
| ECH 支持 | Encrypted Client Hello，TLS 混淆 |
| 自定义 DNS / ECH 域名 | 图形界面配置 |
| API 管理 | 通过 API 动态添加/删除优选 IP |
| 应用唤醒 | 点按钮自动打开对应客户端 |

## 技术架构

```
前端: Cloudflare Pages (静态页面)
后端: Cloudflare Workers (处理订阅逻辑)
存储: Cloudflare KV (配置存储)
部署: Workers + Pages 双版本
```

v2.9.8 版本的重要更新：

- 订阅转换完全由 Worker 直接生成，不再依赖外部 sub-converter
- 使用 Loyalsoldier rule-providers（Clash）、MetaCubeX SRS（Sing-box）、ACL4SSR（Surge/Loon/QuanX）
- 传输优化：参考 GrainTCP 思路优化 WebSocket/TCP 转发
- 图形化 ALPN 配置
- SOCKS5 降级超时：直连 3.5s 无数据自动 fallback

## 部署要点

⚠️ **部署后必须设置兼容日期为 `2026-01-20`**，否则可能出现兼容性问题。

Pages 部署和 Worker 部署都需要在 Cloudflare 控制台的「运行时」设置中修改兼容性日期。

## 优选 IP 管理

CFnew 支持自定义优选 IP 来源 URL，搭配 byJoey 的另一个项目 [yx-tools](https://github.com/byJoey/yx-tools) 可以快速获取优质节点。

---

**一句话总结：** CFnew 是一个功能完整的 Cloudflare 代理订阅管理器，图形界面 + 多协议支持 + 多格式导出，适合需要在多个代理客户端之间切换、对订阅管理有较高要求、同时希望基础设施成本极低（Cloudflare Workers 免费额度足够个人使用）的用户。