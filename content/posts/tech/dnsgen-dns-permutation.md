---
title: "DNSGen：智能 DNS 域名变形引擎——子域名枚举的进阶武器"
date: 2026-04-14T22:20:00+08:00
slug: "dnsgen-dns-permutation"
description: "DNSGen 是 1K Stars 的智能 DNS 域名变形工具，支持 8 种高级变形技术（Word Insertion、Cloud Patterns、Microservice 等）。配合 Findomain 和 massdns 使用，可显著扩展子域名发现范围，支持自定义云平台词表和带注释词表格式。"
draft: false
categories: ["技术笔记"]
tags: ["安全", "BugBounty", "DNS", "子域名枚举", "DNSGen", "渗透测试"]
---

# DNSGen：智能 DNS 域名变形引擎——子域名枚举的进阶武器

> **目标读者**：安全研究员、渗透测试工程师、Bug Bounty 猎人、对子域名枚举感兴趣的开发者
> **预计阅读时间**：35-45 分钟
> **前置知识**：DNS 基础概念、了解过子域名枚举工具
> **难度定位**：⭐⭐⭐⭐ 专家设计

---

## §1 学习目标

完成本篇文章后，你将能够：

1. **理解域名变形的核心原理**：为何简单的排列组合能发现更多子域名
2. **掌握 DNSGen 的 8 种变形技术**：每种技术的适用场景
3. **理解 DNSGen vs altdns 的区别**：DNSGen 的独特优势
4. **能够完成生产级使用**：安装、配置、与 massdns 集成

---

## §2 原理分析：为什么需要域名变形

### 2.1 CT 日志的盲区

CT 日志只能发现已有证书的子域名，对于：
- 变形子域名（如 staging.api.example.com）
- 云平台子域名（如 s3.amazonaws.com）
- 内部工具子域名（如 jenkins.internal.com）

CT 日志**无法发现**，但 DNSGen **可以生成**。

### 2.2 变形 vs 暴力枚举

| 方法 | 优点 | 缺点 |
|------|------|------|
| **暴力枚举** | 覆盖全面 | 字典庞大、速度慢 |
| **CT 日志** | 速度快 | 只能发现已有证书 |
| **DNSGen 变形** | 智能生成、效率高 | 依赖已知域名作为种子 |

---

## §3 八种变形技术

### 3.1 Word Insertion（词语插入）

```
输入：api.example.com
变形：staging.api.example.com, dev.api.example.com, test.api.example.com
```

### 3.2 Number Manipulation（数字操作）

```
输入：api2.example.com
变形：api1.example.com, api3.example.com
```

### 3.3 Word Affixing（词语附加）

```
输入：www.example.com
变形：devwww.example.com, newwww.example.com
```

### 3.4 Cloud Provider Patterns（云平台模式）

```
输入：example.com
变形：api-aws.example.com, storage-azure.example.com
```

### 3.5 Region Prefixes（区域前缀）

```
输入：api.example.com
变形：us-east.api.example.com, eu-west.api.example.com
```

### 3.6 Microservice Patterns（微服务模式）

```
输入：example.com
变形：auth-service.example.com, user-api.example.com
```

### 3.7 Internal Tooling（内部工具）

```
输入：example.com
变形：jenkins.example.com, gitlab.example.com, grafana.example.com
```

### 3.8 Port Prefixing（端口前缀）

```
输入：api.example.com
变形：8080.api.example.com, 8443.api.example.com
```

---

## §4 安装与使用

### 4.1 安装

```bash
pip install dnsgen
# 或
git clone https://github.com/AlephNullSK/dnsgen
cd dnsgen/
uv sync
```

### 4.2 基本使用

```bash
# 基础变形
dnsgen domains.txt

# 使用自定义词表
dnsgen -w custom_wordlist.txt domains.txt -o results.txt

# 快速模式
dnsgen -f domains.txt
```

### 4.3 自定义词表格式

```text
# 环境名称
dev
staging
test
qa

# 云平台
aws
azure
gcp

# 微服务
auth
user
payment
```

---

## §5 与 massdns 集成

### 5.1 完整工作流

```bash
# 1. Findomain 发现基础子域名
findomain -t example.com -o passive_subdomains.txt

# 2. DNSGen 变形
dnsgen passive_subdomains.txt -o mutated_wordlist.txt

# 3. massdns 解析
massdns -r resolvers.txt -t A -o S mutated_wordlist.txt
```

---

## §6 相关资源

| 资源 | 链接 |
|------|------|
| **GitHub** | [github.com/AlephNullSK/dnsgen](https://github.com/AlephNullSK/dnsgen) |
| **altdns** | [github.com/infosec-au/altdns](https://github.com/infosec-au/altdns) |
| **massdns** | [github.com/blechschmidt/massdns](https://github.com/blechschmidt/massdns) |

---

**文档信息**
难度：⭐⭐⭐⭐ | 类型：专家设计 | 更新日期：2026-04-14 | 预计阅读时间：35-45 分钟
