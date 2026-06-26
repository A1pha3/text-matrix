+++
date = '2026-05-20T00:00:00+08:00'
draft = false
title = 'OpenWA：免费开源自托管 WhatsApp API 网关'
slug = 'openwa-self-hosted-whatsapp-api-gateway'
description = 'OpenWA 是一个免费开源的自托管 WhatsApp API 网关，支持消息收发、群组管理、媒体处理，无需官方商业账号即可接入 WhatsApp 生态。'
categories = ['技术笔记']
tags = ['开源', 'API', '自托管', 'WhatsApp']
+++

# OpenWA：免费开源自托管 WhatsApp API 网关

## 读完这篇文章你会知道

- OpenWA 是什么，能在什么场景下替你省掉官方 Business API 的费用
- 如何在一台普通 Linux 服务器上把 OpenWA 跑起来
- REST API 的发送、接收、Webhook 怎么接入你自己的业务系统
- 多设备支持、会话持久化这些特性在什么条件下会省你的事
- 哪些坑（封号风险、频率控制、隐私合规）必须在上线前想清楚

---

## 目录

| → | [项目概述](#一项目概述) | [核心能力](#二核心能力) | [技术架构](#三技术架构) | [快速部署](#四快速部署) | [API 使用示例](#五api-使用示例) | [典型应用场景](#六典型应用场景) | [安全注意事项](#七安全注意事项) | [对比商业方案](#八对比商业方案) | [项目现状与局限](#九项目现状与局限) | [自测](#自测) | [进阶路径](#进阶路径) |

---

## 一、项目概述

**OpenWA**（Open WhatsApp API）是一个免费、开源、自托管的 WhatsApp API 网关项目。它允许开发者通过标准化 API 接口与 WhatsApp 进行交互，实现消息收发、群组管理、媒体文件处理等功能，全程无需依赖 WhatsApp 官方商业账号。

> 仓库：[rmyndharis/OpenWA](https://github.com/rmyndharis/OpenWA)

## 二、核心能力

### 1. 消息收发 API

通过 REST API 发送和接收 WhatsApp 消息，支持：

- **文本消息**：单发/群发
- **媒体消息**：图片、视频、文档、语音
- **位置分享**：发送地理坐标
- **联系人卡片**：vCard 格式
- **模板消息**：官方认可的批量通知格式

### 2. 群组管理

- 创建/解散群组
- 添加/移除成员
- 群组消息监听
- 管理员权限控制

### 3. Webhook 事件订阅

支持多种事件回调：

- `messages.event` — 新消息
- `group.update` — 群组变更
- `connection.status` — 连接状态
- `media.download` — 媒体下载完成

### 4. 多设备支持

- 主设备扫码绑定
- 支持多设备同时在线
- 会话持久化存储

## 三、技术架构

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Client App │ ──► │  OpenWA API  │ ──► │ WhatsApp    │
│  (你的业务)  │     │   Gateway    │     │  (手机端)   │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │  SQLite DB   │
                    │  (会话存储)  │
                    └─────────────┘
```

**技术选型：**

- **后端**：Node.js（原生支持异步，适合 IO 密集型场景）
- **存储**：SQLite（零配置，嵌入式）
- **协议**：Baileys（社区维护的 WhatsApp Web 协议实现）
- **部署**：Docker 一键启动

## 四、快速部署

### Docker 方式（推荐）

```bash
# 拉取镜像
docker pull openwa/wa-automate

# 启动容器
docker run -d \
  --name openwa \
  -p 3000:3000 \
  -e DANGERous_multi_device=true \
  openwa/wa-automate
```

### 手动部署

```bash
# 克隆仓库
git clone https://github.com/rmyndharis/OpenWA.git
cd OpenWA

# 安装依赖
npm install

# 启动服务
npm start
```

### 首次连接

启动后访问 `http://your-server:3000`，页面会显示二维码，用 WhatsApp App 扫码即可绑定。

## 五、API 使用示例

### 发送文本消息

```bash
curl -X POST http://localhost:3000/api/send/text \
  -H "Content-Type: application/json" \
  -d '{
    "number": "8613800138000@c.us",
    "message": "你好，这是通过 OpenWA 发送的消息！"
  }'
```

### 发送图片

```bash
curl -X POST http://localhost:3000/api/send/image \
  -H "Content-Type: application/json" \
  -d '{
    "number": "8613800138000@c.us",
    "url": "https://example.com/image.jpg",
    "caption": "这是一张图片"
  }'
```

### 监听消息（Webhook）

```bash
# 配置 Webhook URL
curl -X POST http://localhost:3000/api/webhook/set \
  -d '{"url": "https://your-app.com/whatsapp-webhook"}'
```

## 六、典型应用场景

| 场景 | 说明 |
|------|------|
| **客服机器人** | 接入 WhatsApp 的自动客服系统 |
| **订单通知** | 电商订单状态实时推送 |
| **社群运营** | 自动欢迎、关键词回复、群管理 |
| **内容分发** | 媒体/文章内容 WhatsApp 分享 |
| **私有协作** |团队内部沟通工具 |

## 七、安全注意事项

⚠️ **重要提醒：**

1. **不要滥用**：大量自动消息可能触发 WhatsApp 封号
2. **频率控制**：建议消息间隔 > 5 秒/条
3. **隐私合规**：收集用户数据需符合当地法规（GDPR/个人信息保护法）
4. **设备安全**：绑定手机保持在线，设备丢失及时重置会话

## 八、对比商业方案

| 对比项 | OpenWA | 官方 Business API | Twilio/MessageBird |
|--------|--------|------------------|-------------------|
| 费用 | **免费** | 按消息计费 | 按消息计费 |
| 部署 | 自托管 | 云服务 | 云服务 |
| 门槛 | 需技术背景 | 需商业认证 | 需账号注册 |
| 稳定性 | 依赖协议稳定性 | **官方保障** | 专业保障 |
| 灵活性 | 高 | 低 | 中 |

## 九、项目现状与局限

**当前状态：** 项目持续维护中，核心功能稳定。

**已知局限：**

- 依赖非官方协议，存在被封禁风险（但对个人用户相对友好）
- 媒体下载偶发超时
- 无官方技术支持

**适合场景：** 技术团队内部工具、个人/小型项目原型验证、预算有限的原型产品。

---

## 自测

1. OpenWA 走的是 WhatsApp Web 协议而非官方 Business API，这两者在稳定性、合规性、费用上各有什么代价？如果你的场景是"给 1 万用户发订单通知"，你会选哪个方案？
2. 文章里建议消息间隔 > 5 秒/条，这个数字是随意给的还是来自某个具体封号阈值？如果你需要每小时发 500 条消息，纯频率控制够吗，还需要什么其他策略？
3. OpenWA 用 SQLite 做会话持久化，这意味着服务重启后不需要重新扫码。但如果 SQLite 文件损坏或丢失，恢复流程是什么？你在部署时会怎么做备份？
4. Webhook 回调在你的业务系统里是同步还是异步处理？如果 OpenWA 发了回调但你的服务暂时 503，消息会重试吗？重试策略在哪里配置？

## 进阶路径

1. **跑通基础发送**：按文中 Docker 方式部署，先用 curl 手动发几条消息，确认扫码绑定和消息收发都正常。
2. **接入业务系统**：把 OpenWA 的 API 封装成你自己项目的服务层（不要直接让业务代码调 OpenWA 的端口），加上重试、限流、消息去重。
3. **Webhook 与状态追踪**：实现消息发送的送达确认（如果 OpenWA 支持回执），把消息状态存进你自己的数据库，做到"用户回复了什么"可查询。
4. **多账号与负载**：如果需要大规模发送，研究 OpenWA 是否支持多实例隔离，以及如何在多个 WhatsApp 账号之间做消息路由。

---

## 十、资源链接

- GitHub：[rmyndharis/OpenWA](https://github.com/rmyndharis/OpenWA)
- 文档：项目 README 内置详细 API 文档
- 社区：GitHub Issues 是主要反馈渠道

---

*用开源方案低成本接入 WhatsApp，适合有技术能力的团队做快速验证。商业级产品建议走官方 API 路线。*