---
title: "Caddy：把 HTTPS 变成默认值的 Web 服务器，十一年后怎么样了"
description: "Caddy 是 Matthew Holt 2014 年起开发的 Web 服务器平台，第一个把自动 HTTPS 做成默认行为，如今 7.7 万 stars、服务过万亿次请求。本文拆解它的 CertMagic 证书自动化、单一 JSON 配置文档与模块化架构三根支柱，并给出与 nginx 的选型对照。"
date: 2026-10-06T03:25:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Caddy", "Web 服务器", "HTTPS", "Go", "反向代理"]
github_repo: "caddyserver/caddy"
source_key: "gh:caddyserver/caddy"
slug : caddy-automatic-https-web-server
---

## 核心判断

2014 年，Matthew Holt 在 Brigham Young University 读计算机时开始写 Caddy，次年它成为**第一个默认自动启用 HTTPS 的 Web 服务器**。十一年后的今天：7.7 万 stars、数百名贡献者、官方口径「服务过万亿次请求、管理数百万张 TLS 证书」，v2.11.7 发布于 2026 年 10 月 3 日，最近提交 10 月 4 日——这是一个已经跑完「新锐→成熟→基础设施」全程的项目。

但它常被中文社区低估为「小 nginx」。实际定位差别很大：**Caddy 首先是一个用配置驱动、可在线变更的 Go 应用运行平台**，HTTP 服务器只是它的两个内置 app 之一（另一个是 `tls`）。理解了这一点，它的很多「怪」设计——配置是单一 JSON 文档、API 才是主要配置入口、Caddyfile 只是「配置适配器」——才顺理成章。

## 系统地图

| 支柱 | 是什么 | 解决什么 |
|------|--------|---------|
| CertMagic | 自动证书管理：ACME 申请、续期、撤销、集群协调 | HTTPS 的运维成本 |
| 单一配置文档 | 全部配置在一个 JSON 文档里，API 在线热改 | 配置漂移与隐藏变量 |
| 模块化架构 | 一切功能皆 Go 模块，xcaddy 按需编译 | 扩展性与体积取舍 |

### CertMagic：HTTPS 的默认值

Caddy 的自动 HTTPS 不是「可选的便捷功能」，是默认行为：公开域名走 ZeroSSL / Let's Encrypt（多签发方自动回退），内部名称与 IP 用全托管的本地 CA，集群内多实例可协调避免重复申请，还支持 ECH（Encrypted Client Hello）。证书自动化被抽成了独立库 [caddyserver/certmagic](https://github.com/caddyserver/certmagic)，Go 项目可以单独取用。

一个常被低估的工程价值：README 特意强调 Caddy「在其他服务器因 TLS/OCSP/证书问题宕机时保持在线」。证书运维的失败模式（OCSP 响应器抽风、速率限制、时钟漂移）恰恰是传统方案里最阴的一类事故，把这一整层收进经过万亿级流量验证的库，是真实的风险消除。

### 单一配置文档：配置的面目

对比一下心智模型。nginx 的配置散落在 CLI 标志、环境变量、多个 conf 文件里；Caddy 把**几乎所有配置收进一个 JSON 文档**，你在文档里设置的值，直接对应内存中驱动 HTTP 处理器与 TLS 握手的那些已初始化类型的真实字段。

主要配置入口是 HTTP API——在线加载、变更、导出配置，配合文档化的 JSON schema。Caddyfile？它是一个「配置适配器」（config adapter）：Caddy 支持把 Caddyfile、JSON 5、YAML、TOML 甚至 nginx 配置转换成原生 JSON。换句话说，**Caddyfile 是给人写的糖，JSON 才是机器的真相**。这解决了配置管理里一个长期痛点：没有一个统一、可 diff、可程序化操作的配置真相源。

### 模块化：xcaddy 的取舍

Caddy 的一切能力（HTTP 处理器、TLS 存储后端、配置适配器……）都是模块。官方二进制不带非标准模块，扩展走 `xcaddy build`：给你一个空 Go module，import 你要的插件，编译出专属二进制。无 libc 依赖，单文件跑在任何地方。

这个模型的代价是加插件要重新编译（对习惯 nginx 动态模块的人是个转身），收益是零冗余、构建可复现、以及「Caddy 本体适合任何长时运行的 Go 程序」这个平台定位——你的 Go 服务可以直接作为 Caddy app 跑进同一个进程，白得自动化文档、优雅在线配置变更等基础设施。

## 快速上手

```bash
# macOS
brew install caddy

# 或从 GitHub Releases 下载单文件二进制
caddy run              # 前台运行
```

最小 Caddyfile：

```
example.com {
    reverse_proxy localhost:8080
}
```

两条命令，HTTPS 就绪——域名解析到位即可，证书申请与续期全自动，无需 certbot 定时任务。官方强烈建议所有用户（不论经验）先过一遍 [Getting Started](https://caddyserver.com/docs/getting-started)；深入配置结构看 [JSON 文档](https://caddyserver.com/docs/json/)，它由配置 schema 自动生成，是「单一真相源」的直接体现。

带插件构建：

```bash
xcaddy build \
  --with github.com/caddyserver/forwardproxy
```

## 选型对照：Caddy vs nginx

| 维度 | Caddy | nginx |
|------|-------|-------|
| HTTPS | 默认自动，含内部 CA | 需 certbot 等外挂 |
| 配置 | 单一 JSON 文档 + API 热改 | 多文件 + reload |
| 写法 | Caddyfile 极简 | nginx conf（生态示例最多） |
| 扩展 | Go 模块，xcaddy 重编译 | 动态模块 / 重编译 |
| 性能 | 足够绝大多数场景（Go 实现） | 极限吞吐与长连接场景的基准 |

诚实地说：极限性能竞赛里 nginx/OpenResty 仍有优势，存量生态（教程、Stack Overflow 答案、运维肌肉记忆）也厚得多。Caddy 的甜区是**个人项目、中小团队、需要快速把一堆服务安全挂上域名的场景**——在「从零到 HTTPS 就绪」这个指标上，它可能仍是没有对手的。

## 适用边界

- 「Caddy」是注册商标（Stack Holdings GmbH），正确称呼是 Caddy，不是 CaddyServer；
- 项目现属 ZeroSSL（HID Global 旗下），商业支持由 Ardan Labs 提供，ZeroSSL 生态的走向值得留意；
- 重度依赖 nginx 现有配置资产或 Lua 扩展的团队，迁移成本可能大于收益；
- 加非官方插件 = 维护自己的构建流水线，这是模块化模型的真实账单。

## 结语

Caddy 最重要的遗产不是它自己有多少市场份额，而是它证明了一件事：**HTTPS 的运维成本可以是零，只要你把它设计成默认值而不是附加题**。2015 年这激进的立场如今已是行业常识，cert-manager、Traefik 等后来者都在这条路上。十一年后回看，它依然是最完整地实践这个理念的一个——如果你还没在什么项目里用过它，下次需要挂一个域名时，试试两行 Caddyfile 的体验。

仓库：[caddyserver/caddy](https://github.com/caddyserver/caddy)，文档：[caddyserver.com/docs](https://caddyserver.com/docs)，Apache-2.0 协议。
