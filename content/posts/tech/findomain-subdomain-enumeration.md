---
title: "Findomain：5秒挖掘8万子域名——域名发现与监控从入门到精通"
date: "2026-04-14T22:10:00+08:00"
slug: "findomain-subdomain-enumeration"
description: "Findomain 是 3.7K Stars 的极速子域名发现工具，基于 Rust 实现，支持 14+ 数据源（Certspotter、Crt.sh、Virustotal 等）。5.5秒发现 84,110 个子域名，内置 Discord/Slack/Telegram Webhook 监控告警，支持 DNS over TLS 和暴力枚举。"
draft: false
categories: ["技术笔记"]
tags: ["安全", "BugBounty", "OSINT", "子域名枚举", "Findomain", "Rust"]
---

# Findomain：5秒挖掘8万子域名——域名发现与监控从入门到精通

> **目标读者**：安全研究员、Bug Bounty 猎人、渗透测试工程师、对 OSINT 感兴趣的开发者
> **预计阅读时间**：40-50 分钟
> **前置知识**：DNS 基础概念、HTTP 协议、了解过子域名枚举工具
> **难度定位**：⭐⭐⭐⭐ 专家设计

---

## §1 学习目标

完成本篇文章后，你将能够：

1. **理解子域名枚举的核心原理**：证书透明日志（Certificate Transparency）vs 暴力枚举
2. **掌握 Findomain 的技术架构**：Rust 实现的高性能设计
3. **理解 14+ 数据源的整合策略**：各 API 的优缺点
4. **能够完成生产级部署**：从安装到配置
5. **掌握子域名监控**：Webhook 告警配置

---

## §2 原理分析：子域名枚举的技术本质

### 2.1 证书透明日志（CT）

Findomain 主要依赖 Certificate Transparency 日志：

- 包含所有被 CA 签发过的证书
- 无需暴力尝试，直接查询真实存在的证书
- 速度快，覆盖全面

### 2.2 Findomain 的技术路线

```
① 证书透明日志查询（主力）
   └─ Crt.sh、Certspotter、Facebook CT

② 公开 API 查询
   └─ Virustotal、SecurityTrails、Bufferover

③ DNS 解析验证
   └─ 验证子域名是否真实存在

④ 暴力枚举（可选）
   └─ 作为补充手段
```

---

## §3 性能对比

| 工具 | 耗时 | 发现数量 | CPU | 内存 |
|------|------|----------|-----|------|
| **Findomain** | **5.5 秒** | **84,110** | 极低 | 极低 |
| 其他工具 | 显著更长 | 少很多 | 高 | 高 |

---

## §4 功能详解

### 4.1 子域名监控

支持 Discord、Slack、Telegram Webhook 告警：

```bash
findomain -t example.com --monitoring \
  --webhook-url "https://discord.com/api/webhooks/xxx" \
  --target example.com
```

### 4.2 数据源

| 数据源 | 说明 | 需要 Key |
|--------|------|----------|
| **Crt.sh** | 证书透明日志（最爱）| 否 |
| **Certspotter** | CT 日志 API | 否 |
| **Virustotal** | 威胁情报 | 免费 Key 可用 |
| **SecurityTrails** | 历史 DNS | 付费 Key |

---

## §5 安装与使用

### 5.1 安装

```bash
# Linux
wget https://github.com/Findomain/Findomain/releases/latest/download/findomain-linux.zip
unzip findomain-linux.zip
chmod +x findomain
sudo mv findomain /usr/local/bin/

# macOS
brew install findomain
```

### 5.2 基本使用

```bash
# 基础发现
findomain -t example.com

# 使用所有 API（包括需要 Key 的）
findomain -t example.com --include-key-api

# 输出 JSON
findomain -t example.com --json

# 保存到文件
findomain -t example.com -o results.txt
```

### 5.3 与 massdns 集成

```bash
# 发现 + 变形 + 解析
findomain -t example.com -o subdomains.txt
dnsgen subdomains.txt > mutations.txt
massdns -r resolvers.txt -t A -o S mutations.txt
```

---

## §6 相关资源

| 资源 | 链接 |
|------|------|
| **官网** | [findomain.app](https://findomain.app) |
| **GitHub** | [github.com/Findomain/Findomain](https://github.com/Findomain/Findomain) |
| **Discord** | [discord.gg/y5JaRbX](https://discord.gg/y5JaRbX) |

---

**文档信息**
难度：⭐⭐⭐⭐ | 类型：专家设计 | 更新日期：2026-04-14 | 预计阅读时间：40-50 分钟
