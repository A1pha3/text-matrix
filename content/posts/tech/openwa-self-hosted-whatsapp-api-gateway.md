+++
date = '2026-05-20T00:00:00+08:00'
draft = false
title = 'OpenWA：免费开源自托管 WhatsApp API 网关'
slug = 'openwa-self-hosted-whatsapp-api-gateway'
description = 'OpenWA 是一个免费开源的自托管 WhatsApp API 网关，支持消息收发、群组管理、媒体处理，无需官方商业账号即可接入 WhatsApp 生态。'
categories = ['技术笔记']
+++

# OpenWA：免费开源自托管 WhatsApp API 网关

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

## 十、资源链接

- GitHub：[rmyndharis/OpenWA](https://github.com/rmyndharis/OpenWA)
- 文档：项目 README 内置详细 API 文档
- 社区：GitHub Issues 是主要反馈渠道

---

*用开源方案低成本接入 WhatsApp，适合有技术能力的团队做快速验证。商业级产品建议走官方 API 路线。*