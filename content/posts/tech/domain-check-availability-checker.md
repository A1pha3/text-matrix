---
title: "domain-check：极速域名可用性检查——1,200+ TLDs + AI 代理支持的从入门到精通"
date: "2026-04-14T22:25:00+08:00"
slug: "domain-check-availability-checker"
description: "domain-check 是 261 Stars 的 Rust 域名检查工具，支持 1,200+ TLDs、RDAP+WHOIS 双协议、100 并发。内置 11 个预设（startup、tech、creative 等），支持域名生成模式，提供 CLI/Rust库/MCP Server 三种形态，可集成到 Claude、Cursor 等 AI 代理。"
draft: false
categories: ["技术笔记"]
tags: ["域名", "RDAP", "WHOIS", "Rust", "MCP", "域名检查", "品牌保护"]
---

# domain-check：极速域名可用性检查——1,200+ TLDs + AI 代理支持的从入门到精通

---

## §1 学习目标

完成本篇文章后，你将能够：

1. **理解域名检查的技术原理**：RDAP vs WHOIS 协议的区别
2. **掌握 domain-check 的架构设计**：双协议引擎设计
3. **能够完成生产级使用**：安装、配置、CI/CD 集成
4. **理解域名生成模式**：\w、\d、? 通配符 + 前缀后缀组合

---

## §2 原理分析：RDAP vs WHOIS

### 2.1 WHOIS 的问题

| 问题 | 说明 |
|------|------|
| 协议古老 | 1985 年设计 |
| 格式不标准 | 每个注册商格式不同 |
| 隐私法规限制 | GDPR 等 |
| 限流严重 | 容易被封 |

### 2.2 RDAP 优势

| 特性 | WHOIS | RDAP |
|------|-------|------|
| 设计年代 | 1985 | 2015 |
| 标准化 | 低 | 高（RFC 7480-7484）|
| 隐私合规 | 困难 | 内置 |
| 访问控制 | 无 | 有 |

### 2.3 双协议引擎

domain-check 采用 **RDAP 优先 + WHOIS 兜底**：

```
RDAP 查询 → 成功 → 返回结果
    ↓ 失败
WHOIS 查询 → 成功 → 返回结果
    ↓ 失败
  返回 UNKNOWN
```

---

## §3 11 个内置预设

| 预设 | TLD 数量 | 适用场景 |
|------|----------|----------|
| `startup` | 8 | 科技创业公司 |
| `popular` | 11 | 通用覆盖 |
| `classic` | 4 | 传统 gTLD |
| `enterprise` | 6 | 企业和政府 |
| `tech` | 10 | 开发者工具 |
| `creative` | 10 | 艺术家和媒体 |
| `ecommerce` | 8 | 电商平台 |
| `finance` | 9 | 金融科技 |
| `web` | 10 | Web 服务 |
| `trendy` | 13 | 新潮 TLD |
| `country` | 9 | 国家域名 |

---

## §4 安装与使用

### 4.1 安装

```bash
# Homebrew（macOS）
brew install domain-check

# Cargo
cargo install domain-check

# 下载二进制
curl -L https://github.com/saidutt46/domain-check/releases/latest/download/domain-check-linux.tar.gz | tar -xz
```

### 4.2 基本使用

```bash
# 检查单个域名
domain-check example.com

# 检查多个 TLD
domain-check myapp -t com,org,io,ai

# 使用预设
domain-check myapp --preset startup --pretty

# 检查所有 TLD
domain-check mybrand --all --batch

# 获取详细信息
domain-check mycompany.com --info
```

### 4.3 域名生成

```bash
# 使用通配符
domain-check --pattern "app\d" -t com --dry-run

# 前缀后缀
domain-check myapp --prefix get,try --suffix hub,ly -t com,io
```

---

## §5 MCP Server

domain-check 支持 MCP 协议，可集成到 AI 代理：

```bash
# 安装 MCP Server
cargo install domain-check-mcp

# 添加到 Claude Code
claude mcp add domain-check -- domain-check-mcp
```

然后可以自然语言询问："Is coolstartup.com available?"

---

## §6 相关资源

| 资源 | 链接 |
|------|------|
| **GitHub** | [github.com/saidutt46/domain-check](https://github.com/saidutt46/domain-check) |
| **crates.io** | [crates.io/crates/domain-check](https://crates.io/crates/domain-check) |
| **docs.rs** | [docs.rs/domain-check-lib](https://docs.rs/domain-check-lib) |

---

**文档信息**
难度：⭐⭐⭐⭐ | 类型：专家设计 | 更新日期：2026-04-14 | 预计阅读时间：30-40 分钟
