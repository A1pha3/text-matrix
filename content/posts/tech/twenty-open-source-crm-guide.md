---
title: "Twenty：开源CRM平台的崛起"
date: 2026-03-29T15:35:00+08:00
slug: "twenty-open-source-crm-guide"
description: "Twenty 是 GitHub 42.5k Stars 的开源 CRM 平台，Salesforce 的现代替代品。本文全面介绍其功能架构、技术栈、快速部署和定制开发。"
draft: false
categories: ["技术笔记"]
tags: ["CRM", "开源", "TypeScript", "NestJS", "React"]
---

# Twenty：开源CRM平台的崛起

## 一、项目概览

**Twenty** 是一个现代化的开源 CRM（客户关系管理）平台，旨在成为 Salesforce 的开源替代品。该项目在 GitHub 上获得了 **42.5k Stars** 和 **5.6k Forks**，已经成为开源 CRM 领域最受欢迎的项目之一。

### 1.1 核心定位

Twenty 的诞生源于三个核心观察：

1. **CRMs 太贵了，用户被锁定**：Salesforce、HubSpot 等传统 CRM 平台价格高昂，企业难以摆脱数据束缚
2. **体验需要革新**：现有 CRM 界面过时，需要借鉴 Notion、Airtable、Linear 等现代工具的 UX 设计
3. **开源和社区的力量**：数百名开发者正在一起构建 Twenty，未来将形成强大的插件生态

### 1.2 技术统计

| 指标 | 数值 |
|------|------|
| Stars | 42.5k |
| Forks | 5.6k |
| Commits | 11,073 |
| 最新版本 | v1.19.0 (2026-03-23) |
| 主要语言 | TypeScript 80.1% |
| 许可证 | GPL |

## 二、核心功能

### 2.1 灵活的数据视图

Twenty 支持多种视图模式，满足不同工作场景需求：

- **筛选器（Filters）**：按条件过滤数据
- **排序（Sort）**：按字段升序/降序排列
- **分组（Group By）**：按属性自动分组
- **看板视图（Kanban）**：直观展示工作流程
- **表格视图（Table）**：支持大数据量浏览

### 2.2 自定义对象和字段

不同于传统 CRM 的固定数据结构，Twenty 允许用户：

- 创建自定义对象（Custom Objects）
- 添加自定义字段
- 定义对象之间的关系
- 调整字段类型和验证规则

### 2.3 权限管理系统

基于角色的访问控制（RBAC，Role-Based Access Control）：

- 创建自定义角色
- 细粒度配置权限
- 支持组织和个人级别的权限设置

### 2.4 工作流自动化

通过触发器和动作实现业务流程自动化：

```typescript
// 工作流配置示例
{
  trigger: {
    type: "record_created",
    object: "Task",
    conditions: [{ field: "priority", equals: "high" }]
  },
  actions: [
    { type: "update_record", field: "status", value: "urgent" },
    { type: "send_notification", channel: "email", to: "manager@company.com" }
  ]
}
```

### 2.5 丰富的集成

支持多种数据类型的管理：

- 邮件关联
- 日历事件同步
- 文件管理
- 任务追踪

## 三、技术架构

### 3.1 技术栈

| 层级 | 技术选型 |
|------|----------|
| **后端框架** | NestJS + BullMQ（消息队列） |
| **数据库** | PostgreSQL + Redis（缓存） |
| **前端框架** | React + Jotai（状态管理） |
| **样式方案** | Linaria（CSS-in-JS） |
| **国际化** | Lingui |
| **Monorepo** | Nx |

### 3.2 项目结构

```
twenty/
├── packages/           # 核心包目录
├── .cursor/           # AI编码辅助配置
├── .github/           # GitHub Actions CI/CD
├── .vscode/           # VS Code 配置
├── .yarn/             # Yarn 依赖管理
├── CLAUDE.md          # AI 开发者指南
└── nx.json            # Nx 构建配置
```

### 3.3 架构特点

**Nx Monorepo 优势：**
- 代码共享和复用
- 统一的构建系统
- 高效的增量构建
- 跨项目依赖管理

**前后端分离：**
- 前端：React SPA，状态管理采用 Jotai
- 后端：NestJS 渐进式框架，模块化设计
- API：GraphQL（推荐）或 REST

## 四、快速开始

### 4.1 本地开发环境

```bash
# 克隆仓库
git clone https://github.com/twentyhq/twenty.git
cd twenty

# 安装依赖（使用 Yarn）
yarn install

# 启动开发服务器
yarn dev
```

### 4.2 Docker 部署

```bash
# 使用 Docker Compose 一键部署
docker-compose up -d

# 访问地址
# http://localhost:3000
```

### 4.3 环境要求

| 组件 | 最低要求 |
|------|----------|
| Node.js | 24+ |
| PostgreSQL | 14+ |
| Redis | 6+ |
| Docker | 20+ |

## 五、使用指南

### 5.1 基础概念

**对象（Objects）**：Twenty 中的核心数据实体，如 Company、Contact、Deal 等

**字段（Fields）**：对象的属性，如公司名称、联系人邮箱、交易金额

**视图（Views）**：数据的展示方式，保存用户的查看偏好

**工作区（Workspace）**：团队协作空间，包含所有数据和配置

### 5.2 常见工作流

**创建新联系人：**
1. 进入 Contacts 模块
2. 点击「新建联系人」
3. 填写必填字段（姓名、邮箱等）
4. 可选关联到公司
5. 保存

**创建自动化工作流：**
1. 进入 Settings → Workflows
2. 点击「新建工作流」
3. 配置触发条件（如「任务状态变更为完成」）
4. 添加动作（如「发送邮件通知」）
5. 激活工作流

## 六、配置与扩展

### 6.1 自定义字段

Twenty 支持多种字段类型：

| 字段类型 | 说明 |
|----------|------|
| 文本（Text） | 短文本或长文本 |
| 数字（Number） | 整数或浮点数 |
| 日期（Date） | 日期或日期时间 |
| 关系（Relation） | 关联其他对象 |
| 枚举（Select） | 单选或多选 |
| 布尔（Boolean） | 是/否 |

### 6.2 API 集成

Twenty 提供 RESTful API 和 GraphQL API：

```bash
# 获取所有公司
curl -X GET "https://your-instance.twenty.app/api/companies" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 6.3 Webhooks

配置 Webhooks 接收实时事件：

```json
{
  "events": ["company.created", "deal.updated", "task.completed"],
  "url": "https://your-app.com/webhook",
  "secret": "your-webhook-secret"
}
```

## 七、插件系统

Twenty 正在构建插件能力，计划支持：

- **自定义字段渲染器**：自定义字段在前端的展示方式
- **动作扩展**：扩展自动化工作流的动作类型
- **数据源集成**：连接外部数据系统
- **UI 主题**：自定义界面样式

插件生态将是 Twenty 未来发展的重要方向。

## 八、对比传统 CRM

| 维度 | Twenty | Salesforce | HubSpot |
|------|--------|-----------|---------|
| **价格** | 开源免费 | 昂贵 | 中等 |
| **部署方式** | 自托管 | SaaS | SaaS/自托管 |
| **定制化** | 高度可定制 | 需要管理员 | 中等 |
| **技术栈** | 现代 TypeScript | 老旧 | 现代 |
| **社区** | 活跃开源社区 | 官方支持 | 官方支持 |
| **学习曲线** | 中等 | 陡峭 | 中等 |

## 九、最佳实践

### 9.1 数据建模

- 从业务需求出发设计对象和关系
- 避免过度设计，先用起来再迭代
- 善用自定义字段扩展标准对象

### 9.2 权限管理

- 遵循最小权限原则
- 为不同角色创建专门的权限配置
- 定期审计权限设置

### 9.3 性能优化

- 使用视图筛选减少数据加载量
- 合理使用缓存（Redis）
- 避免在触发器中执行耗时操作

## 十、常见问题

**Q: Twenty 和 Pipedrive/Highrise 有什么区别？**

A: Twenty 是完全开源的，支持自托管，数据完全属于你自己。Pipedrive 和 Highrise 是 SaaS 服务，数据存储在第三方。

**Q: 是否需要编程知识才能使用？**

A: 不需要。Twenty 提供了直观的 UI，运营人员可以直接使用。但如果你想进行深度定制开发（如创建自定义插件），需要具备一定的 TypeScript/React 开发能力。

**Q: 如何保证数据安全？**

A: Twenty 支持：
- 细粒度的权限控制
- 数据加密存储
- 审计日志
- 定期备份（需要自行配置）

**Q: 能迁移现有数据吗？**

A: 可以。Twenty 提供了数据导入功能，支持 CSV 格式。同时提供 REST API 可用于批量数据迁移。

## 十一、总结

Twenty 代表了开源 CRM 的新势力。它：

- ✅ **完全开源**：代码透明，无供应商锁定
- ✅ **功能完整**：覆盖 CRM 核心需求，并持续迭代
- ✅ **技术现代**：TypeScript 全栈，架构清晰易扩展
- ✅ **社区活跃**：42.5k Stars，大量开发者参与贡献
- ✅ **可自托管**：数据完全自主掌控

无论你是独立开发者、中小企业还是大型组织，Twenty 都值得一试。

---

**相关资源：**

- 🌐 官网：https://twenty.com
- 📚 文档：https://docs.twenty.com
- 💬 Discord：https://discord.gg/cx5n4Jzs57
- 🐙 GitHub：https://github.com/twentyhq/twenty
- 🗺️ 路线图：https://github.com/orgs/twentyhq/projects/1
