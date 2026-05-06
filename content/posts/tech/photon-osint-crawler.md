---
title: "Photon：极速 OSINT 爬虫——域名发现、敏感信息提取与情报收集从入门到精通"
date: "2026-04-14T22:35:00+08:00"
slug: "photon-osint-crawler"
description: "Photon 是 12.8K Stars 的极速 OSINT 爬虫，支持 8 种数据提取（URL、参数、Intel、文件、密钥、JS 端点、正则匹配、DNS 数据），多线程极速爬取，可提取邮箱、API 密钥、S3 Bucket 等敏感信息，集成 Wayback Machine 和 DNSdumpster 插件。"
draft: false
categories: ["技术笔记"]
tags: ["安全", "OSINT", "爬虫", "BugBounty", "Photon", "信息收集", "渗透测试"]
---

# Photon：极速 OSINT 爬虫——域名发现、敏感信息提取与情报收集从入门到精通

> **目标读者**：安全研究员、渗透测试工程师、Bug Bounty 猎人、对 OSINT 感兴趣的开发者
> **预计阅读时间**：40-50 分钟
> **前置知识**：Python 基础、HTTP 协议理解、了解过网络爬虫概念
> **难度定位**：⭐⭐⭐⭐ 专家设计

---

## §1 学习目标

完成本篇文章后，你将能够：

1. **理解 OSINT 爬虫的设计理念**：为何需要专用爬虫而非通用爬虫
2. **掌握 Photon 的核心架构**：多线程、插件系统
3. **理解 8 种数据提取能力**：URL、参数、Intel、文件、密钥等
4. **能够完成生产级部署**：安装、Docker、代理配置

---

## §2 原理分析：OSINT 爬虫 vs 通用爬虫

### 2.1 通用爬虫的问题

| 问题 | 说明 |
|------|------|
| 速度慢 | 需要解析整个页面 |
| 资源消耗大 | 内存占用高 |
| 难以提取结构化信息 | 需要大量自定义解析 |
| 无法提取敏感信息 | API 密钥容易被忽略 |

### 2.2 Photon 的定位

Photon 是专为 OSINT 设计的极速爬虫，核心设计理念：

- **只关心有价值的数据**：URL、参数、密钥、邮箱
- **不关心页面内容**：不需要渲染
- **快速发现资产**：多线程并发

---

## §3 8 种数据提取能力

### 3.1 URLs 提取

```
输入页面: <a href="https://example.com/about">About</a>
提取结果: https://example.com/about
```

### 3.2 Intel 提取

| 类型 | 示例 |
|------|------|
| **邮箱** | `admin@example.com` |
| **社交媒体** | `@username` |
| **AWS S3 Buckets** | `company-logs.s3.amazonaws.com` |
| **IP 地址** | `192.168.1.1` |

### 3.3 敏感文件发现

| 文件类型 | 风险等级 |
|----------|----------|
| `.env`, `.config` | **高** |
| `.sql`, `.db` | **极高** |
| `.key`, `.pem` | **极高** |
| `.pdf`, `.doc` | 中 |

### 3.4 密钥/Token 提取

```
AWS Access Key:     AKIAIOSFODNN7EXAMPLE
GitHub Token:       ghp_xxxxxxxxxxxx
Stripe Key:         sk_live_xxxxxxxxxx
```

---

## §4 安装与使用

### 4.1 安装

```bash
pip install photon
# 或
git clone https://github.com/s0md3v/Photon.git
cd Photon
pip install -r requirements.txt
```

### 4.2 Docker

```bash
docker build -t photon .
docker run -it --name photon photon:latest -u example.com
```

### 4.3 基本使用

```bash
# 基础爬取
photon -u example.com

# 指定线程数
photon -u example.com -t 20

# 保存结果
photon -u example.com -o output/

# 使用 Wayback Machine
photon -u example.com --wayback

# 导出 JSON
photon -u example.com --json
```

---

## §5 插件系统

### 5.1 Wayback 插件

从 archive.org 获取历史 URL：

```bash
photon -u example.com --wayback
```

### 5.2 DNSdumpster 插件

提取 DNS 相关数据：

```bash
photon -u example.com --dns
```

### 5.3 Exporter 插件

导出格式：

```bash
photon -u example.com --json
photon -u example.com --csv
```

---

## §6 相关资源

| 资源 | 链接 |
|------|------|
| **GitHub** | [github.com/s0md3v/Photon](https://github.com/s0md3v/Photon) |
| **PyPI** | [pypi.org/project/photon](https://pypi.org/project/photon/) |
| **Wiki** | [Photon Wiki](https://github.com/s0md3v/Photon/wiki) |

---

**文档信息**
难度：⭐⭐⭐⭐ | 类型：专家设计 | 更新日期：2026-04-14 | 预计阅读时间：40-50 分钟
