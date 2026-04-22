---
title: "VoltAgent/awesome-agent-skills：1100+官方AI Agent技能集合，兼容Claude Code和Codex"
slug: voltagent-awesome-agent-skills-17k
date: 2026-04-22T16:10:00+08:00
description: "全面解析 VoltAgent/awesome-agent-skills：1100+官方AI Agent技能集合，来自Anthropic、Google、Vercel、Stripe等顶级团队，兼容Claude Code、Codex、Cursor等主流AI编码工具。"
categories: ["技术笔记"]
tags: ["VoltAgent", "Agent Skills", "Claude Code", "AI Agent", "开源"]
---

# VoltAgent/awesome-agent-skills：1100+官方AI Agent技能集合，兼容Claude Code和Codex

## 🎯 概述

**VoltAgent/awesome-agent-skills** 是目前最全面的 AI Agent 技能集合，收录了来自**顶级开发团队的1100+官方技能**，包括 Anthropic、Google Labs、Vercel、Stripe、Cloudflare、Netlify、Trail of Bits、Sentry、Expo、Hugging Face、Figma 等。

> **GitHub**: [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills)  
> **Stars**: 17,189 ⭐  
> **技能数量**: 1100+  
> **许可证**: Various

### 核心特点

| 特点 | 说明 |
|------|------|
| **官方出品** | 来自真实工程团队，非 AI 批量生成 |
| **多平台兼容** | Claude Code、Codex、Cursor、GitHub Copilot、OpenCode、Windsurf |
| **顶级厂商** | Anthropic、Google、Vercel、Stripe、Cloudflare 等 |
| **持续更新** | 最后更新保持同步 |

---

## 🏛️ 支持的厂商与技能类型

### 官方技能厂商

| 厂商 | 代表技能 |
|------|---------|
| **Anthropic** | docx、pptx、xlsx、pdf、mcp-builder、frontend-design |
| **Google Gemini** | gemini-api-dev、vertex-ai-api-dev、gemini-live-api-dev |
| **Vercel** | Next.js 部署、优化、配置 |
| **Stripe** | stripe-best-practices、upgrade-stripe |
| **Cloudflare** | Workers、Pages、D1、KV |
| **Supabase** | postgres-best-practices |
| **Expo** | React Native 最佳实践 |
| **Trail of Bits** | 安全审计技能 |

---

## ⚡ 快速开始

### 安装 Claude Code 技能

```bash
# 使用 Claude Code 的 /skills 命令安装
# 访问 officialskills.sh 查找技能

# 例如安装 Stripe 技能
claude "/skills install stripe/stripe-best-practices"
```

### 兼容平台

| 平台 | 支持状态 |
|------|---------|
| Claude Code | ✅ 官方支持 |
| Codex | ✅ 兼容 |
| Cursor | ✅ 兼容 |
| GitHub Copilot | ⚙️ 部分兼容 |
| Windsurf | ⚙️ 部分兼容 |

---

## 💡 应用场景

### 1. 文档生成

Anthropic 官方技能可以生成 Word、PowerPoint、Excel、PDF 文档：

```bash
# Claude Code 中使用
/skills use anthropics/pptx
# 生成技术演示文稿
```

### 2. 基础设施即代码

HashiCorp 官方技能帮助编写 Terraform 配置：

```bash
# 部署 Azure 基础设施
/skills use hashicorp/azure-verified-modules
```

### 3. 安全审计

Trail of Bits 安全团队的官方技能：

```bash
# 执行安全审计
/skills use trail-of-bits/security-audit
```

### 4. 数据库开发

Supabase、Neon、ClickHouse 等数据库技能：

```bash
# PostgreSQL 最佳实践
/skills use supabase/postgres-best-practices
```

---

## 🔗 资源链接

| 资源 | 链接 |
|------|------|
| GitHub | [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) |
| 技能市场 | [officialskills.sh](https://officialskills.sh/) |
| VoltAgent 官网 | [voltagent.dev](https://voltagent.dev) |

---

*🦞 VoltAgent/awesome-agent-skills：让 AI Agent 调用官方认证的最佳实践。*
