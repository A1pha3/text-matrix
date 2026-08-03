---
title: "Chatwoot：开源全渠道客服平台，Intercom/Zendesk 的自托管替代"
date: 2026-08-01T02:54:21+08:00
draft: false
categories: ["技术笔记"]
tags: ["Chatwoot", "客服", "全渠道", "开源", "Ruby", "Rails", "自托管"]
description: "Chatwoot 是 35k Stars 的开源客服平台，将网站实时聊天、邮件、WhatsApp、Telegram、Facebook、Instagram 等渠道统一到一个收件箱，支持 AI agent 自动应答、团队协作和自助知识库，可自托管部署。"
slug: chatwoot-chatwoot-omnichannel-support-guide
github_repo: "chatwoot/chatwoot"

---

## 一句话判断

如果你在寻找 Intercom 或 Zendesk 的开源替代品，Chatwoot 几乎是目前最成熟的选择。35,000+ Stars、活跃维护、全渠道聚合、内置 AI agent、自托管数据自主——它在功能覆盖上已经可以和商业产品正面竞争。

## 项目概览

| 维度 | 数据 |
|------|------|
| 仓库 | chatwoot/chatwoot |
| Stars | ~35,000 |
| Forks | ~8,400 |
| 语言 | Ruby（Rails）/ Vue.js（前端） |
| 许可证 | 自定义（基于 MIT，有商业限制） |
| 部署 | Docker / Heroku / DigitalOcean / Kubernetes |

Chatwoot 定位为"现代客服平台"——不是简单的聊天插件，而是覆盖邮件、电话、社交媒体和网站的全渠道客户支持系统。

## 核心功能

### Captain：AI 客服 Agent

Chatwoot 内置了名为 **Captain** 的 AI agent，可以自动回复常见问题、减轻人工客服负担。Captain 让团队将精力集中在复杂对话上，常规查询由 AI 自动解决。

### 全渠道统一收件箱

所有客户对话汇聚到一个界面：

- **实时聊天**：网站嵌入聊天组件
- **邮件**：将支持邮箱接入 Chatwoot
- **社交媒体**：Facebook、Instagram、Twitter
- **即时通讯**：WhatsApp、Telegram、Line
- **短信**：SMS 渠道接入

客服人员不需要在多个平台间切换，所有对话在同一个收件箱处理。

### 知识库门户

内置帮助中心，可以发布帮助文章、FAQ 和使用指南。客户可自行查找答案，减少重复咨询。

### 协作与效率

- **私信和 @提及**：团队内部讨论不影响客户可见的对话
- **标签系统**：分类和组织对话
- **快捷回复**：预设常用回复模板
- **自动分配**：按客服可用性自动路由对话
- **自定义视图**：按条件筛选和保存收件箱视图
- **工作时间**：设置营业时间和自动回复
- **团队和自动化**：按团队划分工作流

### 客户数据与集成

- **联系人管理**：完整的客户画像和交互历史
- **自定义属性**：扩展客户数据字段
- **预聊天表单**：聊天前收集用户信息
- **Slack 集成**：直接在 Slack 中处理对话
- **Dialogflow 集成**：接入聊天机器人
- **Shopify 集成**：查看和管理客户订单
- **Google Translate**：实时翻译客户消息
- **Linear 集成**：在 Chatwoot 中创建和管理 Linear 工单

### 报表与分析

- **实时视图**：监控进行中的对话
- **多维度报表**：对话/客服/收件箱/标签/团队维度
- **CSAT 报表**：客户满意度测量
- **可下载报表**：离线分析

## 技术栈

Chatwoot 的技术选型偏向成熟稳定的 Rails 生态：

- **后端**：Ruby on Rails
- **前端**：Vue.js
- **实时通信**：ActionCable（WebSocket）
- **数据库**：PostgreSQL
- **缓存**：Redis
- **部署**：Docker 官方镜像、Heroku 一键部署、DigitalOcean Kubernetes

## 部署方式

### Docker（推荐自托管）

```bash
docker run -d \
  -e SECRET_KEY_BASE=your_secret \
  -e REDIS_URL=redis://redis:6379 \
  -e POSTGRES_HOST=postgres \
  -e POSTGRES_USERNAME=chatwoot \
  -e POSTGRES_PASSWORD=your_password \
  -p 3000:3000 \
  chatwoot/chatwoot:latest
```

### Heroku 一键部署

README 提供了一键部署按钮，点击后按提示设置环境变量即可。

### DigitalOcean Kubernetes

DigitalOcean Marketplace 提供 1-Click Kubernetes 部署。

## 适用边界

**适合**：

- 中小团队需要全渠道客服但不想付费给 Intercom/Zendesk
- 对数据自主性有要求的组织（自托管）
- 需要多语言支持的国际化团队（Crowdin 社区翻译）
- 希望用 AI agent 辅助客服但保持人工兜底的团队

**不适合**：

- 需要 100% 定制化 UI 的团队（Chatwoot 的界面框架固定）
- 对 License 有严格合规要求的项目（Chatwoot 使用自定义 License，非标准 OSS）
- 需要深度电话/语音支持的团队（Chatwoot 的电话渠道相对弱）

## 相关链接

- 仓库：[github.com/chatwoot/chatwoot](https://github.com/chatwoot/chatwoot)
- 官网：[chatwoot.com](https://www.chatwoot.com)
- 文档：[chatwoot.com/help-center](https://www.chatwoot.com/help-center)
- Docker 镜像：[hub.docker.com/r/chatwoot/chatwoot](https://hub.docker.com/r/chatwoot/chatwoot)
- Discord：[discord.gg/cJXdrwS](https://discord.gg/cJXdrwS)
