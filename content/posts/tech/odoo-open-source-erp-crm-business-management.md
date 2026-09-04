---
title: "Odoo - 开源企业级 ERP / CRM / 业务管理套件"
date: "2026-05-23T15:30:00+08:00"
slug: odoo-open-source-erp-crm-business-management
github_repo: "odoo/odoo"
description: "Odoo 是全球最流行的开源企业管理系统，基于 Python 与 PostgreSQL 构建，社区版遵循 LGPL 协议，提供 CRM、销售、库存、会计、项目、电商等 50+ 官方应用，全球 1600 万+ 用户。"
tags: ["ERP", "CRM", "Python", "PostgreSQL", "Open Source", "企业管理"]
categories: ["技术笔记"]
author: 钳岳星君
---

[Odoo](https://github.com/odoo/odoo) 是 GitHub 上最受欢迎的开源企业管理系统之一，长期位居 Python 热门仓库前列。它远不止一个 ERP：从销售、采购到财务、人资，全球数以万计的中小企业用它把分散的业务环节收拢进同一个平台。

## Odoo 是什么

Odoo 是一套**开箱即用的企业管理系统**，从初创公司到中大型企业都适用。它把销售、CRM、采购、库存、财务、项目、人力资源、电商等环节整合进同一平台，各模块之间数据相通。最大的特点是**按需装配**：你只需启用需要的应用，不必一次性部署整套系统。

## 历史与定位

- 2005 年，比利时人 Fabien Pinckaers 以 **TinyERP** 起步，最初只是为本地商家写的一小套会计工具；
- 2010 年更名 **OpenERP**（v6，标志性的 Web 客户端），2014 年随 v8 更名为 **Odoo**，企业版由此与社区版分家；
- 此后 Odoo 保持**每年发布一个主版本**的节奏，通常于每年 10 月在布鲁塞尔举办的 Odoo Experience 上公布，随后的次版本持续补丁修复；
- 生态普遍引用的规模：**1600 万+ 用户、覆盖 120 多个国家、官方应用 50+**（来源于官网与社区公开口径，随版本滚动变化）。

## 主要模块

| 类别 | 模块 |
|------|------|
| CRM & 销售 | CRM、销售自动化、报价、合同管理、在线支付 |
| 财务 | 发票、会计、费用、银行对账、资产 |
| 库存 & 物流 | 库存、多仓库、采购、批次与序列号 |
| 项目 | 项目、甘特图、工时、排期 |
| 人力资源 | 招聘、员工、考勤、报销、工资单 |
| 营销 | 邮件营销、营销自动化、活动、社媒、电商 |
| 客服 | 工单、实时聊天、满意度调查、知识库 |
| 制造 | 生产（MRP）、品控、维护、PLM |
| 人工智能 | OCR 单据识别、AI 助手、自然语言查询（Ask AI） |
| IoT | IoT 盒子，连接硬件设备 |

## 许可证与版本

- **Odoo Community**：开源，采用 **LGPL**，覆盖全部基础业务应用，可自由修改与商用；
- **Odoo Enterprise**：闭源订阅制，在社区版之上提供更深的功能（如先进制造排产、商业分析、某些行业套件），部分模块仅对企业版开放；
- **版本选择**：主版本每年一个，通常建议生产环境比最新版本落后一个小版本，既拿到修复又避开新版本的迁移风险。

## 技术栈

```text
后端:    Python（Odoo Framework）
数据库:  PostgreSQL
前端:    OWL（Odoo 自研组件框架），取代早期 jQuery / backbone
视图:    XML 描述界面，QWeb 模板渲染
ORM:     自定义 ORM 层封装 SQL
数据:    CSV / XML 导入初始数据
```

开发者用 XML 定义视图、用 Python 写业务逻辑、用 CSV 灌初始数据，三者各司其职。

## 为什么选择 Odoo

### 优势

1. **模块化设计**：按需安装，不必一次性部署整套系统；
2. **开源可控**：社区版 LGPL 完全免费、源码透明、可定制；
3. **应用生态丰富**：官方商店之外，OCA（Odoo Community Association）等社区维护着大量第三方开源模块；
4. **社区活跃**：全球范围内有大量贡献者与实施伙伴；
5. **持续迭代**：每年一个主版本，社区版与企业版并行演进。

### 对比竞品

| 竞品 | 特点 |
|------|------|
| SAP | 企业级、昂贵、复杂，适合超大型企业 |
| Microsoft Dynamics | 与微软生态深度集成 |
| Tryton | 更轻量、Python 原生、社区较小 |
| ERPNext | 开源、基于 Python/MariaDB，常见替代选项 |
| **Odoo** | 模块最丰富、社区最活跃、上手门槛较低 |

## 开发者角度

对参与 Odoo 开发的工程师，核心概念是模型、字段与视图：

```python
from odoo import models, fields

class LibraryBook(models.Model):
    _name = 'library.book'
    _description = 'Library Book'

    name = fields.Char(string='Title', required=True)
    author = fields.Char(string='Author')
    date_published = fields.Date(string='Published Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('available', 'Available'),
        ('borrowed', 'Borrowed'),
        ('lost', 'Lost'),
    ], string='Status', default='draft')
```

Odoo 使用自有的 ORM、字段类型与继承机制，和标准的 Django/Flask 差异较大，学习曲线客观存在；一旦熟悉字段继承与视图继承，扩展开发效率很高，多数定制不需要改动核心源码。

## 部署与上手

| 方式 | 说明 |
|------|------|
| Docker 镜像 | 官方镜像一条命令拉起，适合本地与测试环境 |
| Odoo.sh | Odoo 官方云平台，托管部署与集成升级 |
| Odoo Online | 官方 SaaS，开箱即用，无需自建服务器 |

## 适用场景

**推荐用 Odoo：**

- 10–500 人规模的中小企业；
- 需要打通销售、库存、财务、项目等多个业务环节；
- 希望快速上线，不愿从零开发；
- 需要开源方案、避免厂商锁定。

**不推荐：**

- 超大型企业（万人以上，建议评估 SAP/Oracle）；
- 特殊业务流程且 Odoo 架构难以承载；
- 对高并发性能要求极高的场景（Odoo 在高并发上有一定限制）。

**一句话总结：** Odoo 是开源 ERP 领域模块最丰富、社区最活跃的选择，社区版以 LGPL 开源、按需装配的设计让它从几个人到数百人都能渐进式使用。如果你的公司需要一套覆盖销售、CRM、库存、财务、项目的一体化管理平台，Odoo 社区版值得优先评估。