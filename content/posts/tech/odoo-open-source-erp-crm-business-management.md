---
title: "Odoo - 开源企业级 ERP / CRM / 业务管理套件"
date: "2026-05-23T15:30:00+08:00"
lastmod: "2026-10-03"
slug: odoo-open-source-erp-crm-business-management
github_repo: "odoo/odoo"
source_key: "gh:odoo/odoo"
description: "Odoo 是 GitHub 上星数最高的 Python 业务应用之一，社区版以 LGPL-3.0 开源。本文梳理它从 TinyERP 到 Odoo 20 的二十年时间线、八大业务域约 50 个官方应用的模块地图、技术栈，以及官方教程里的模型与继承机制，帮你在选型或动手开发前建立整体认知。"
tags: ["ERP", "CRM", "Python", "PostgreSQL", "Open Source", "企业管理"]
categories: ["技术笔记"]
author: 钳岳星君
---

[Odoo](https://github.com/odoo/odoo) 是 GitHub 上最受欢迎的开源企业管理系统之一：截至 2026-10-03，odoo/odoo 仓库 54,809 Stars、33,916 Forks，在 Python 项目中长期位居前列。它远不止一个 ERP——从销售、采购到财务、人资，全球大量中小企业用它把分散的业务环节收拢进同一个平台。本文覆盖它的演进历史、模块地图、技术栈与开发入门；若你更关心架构细节与社区版/企业版边界的深度拆解，可先读[姊妹篇](/posts/tech/odoo-open-source-erp-business-platform-guide/)。

## 从 TinyERP 到 Odoo 20：二十年时间线

Odoo 的历史比大多数当代 SaaS 都长。以下时间点均可在维基百科条目与官方发布记录中核对：

| 年份 | 事件 |
|------|------|
| 2005 | 比利时人 Fabien Pinckaers 发布 **TinyERP**，一套面向本地商家的会计工具（当年 2 月首次发布） |
| 2008 | 更名 **OpenERP** |
| 2012 | **v7.0** 发布（12 月），同期推出 OpenERP Enterprise 订阅——今天企业版/社区版分层的起点 |
| 2014 | 随 **v8** 更名为 **Odoo**，公司名同步更换 |
| 2015 | **v9.0** 起 open-core 模式成型：社区版开源、企业应用专有 |
| 此后每年 | 一年一个大版本，惯例于 9 月末的年度大会 Odoo Experience 发布（v19 于 2025-09、v20 于 2026-09-24 发布） |

当前默认分支是 `20.0`，仓库保留着从 5.0 到 20.0 的全部 17 个版本分支（外加 6.1 这个小版本特例）。注意"有分支"不等于"还在维护"：仓库 SECURITY.md 的支持版本表当前列 16.0–19.0 四个受支持版本，15.0 及更早已停止安全修复，20.0 刚发布尚未入表——**生产环境比最新版落后一个小版本**是社区常见做法，理由正在于此。

## 模块地图：八大业务域，约 50 个官方应用

Odoo 官网导航按八大业务域组织官方应用，每个域 6 个，加上低代码工具 Studio，合计约 50 个（2026-10 官网读数，清单随版本滚动）：

| 业务域 | 官方应用（举例） |
|--------|------------------|
| 财务 Finance | 会计、开票、费用报销、电子签、电子表格（BI）、ESG |
| 销售 Sales | CRM、销售、订阅管理、POS 门店、POS 餐厅、租赁 |
| 网站 Websites | 建站、电商、活动、博客、在线课程、论坛 |
| 供应链 Supply Chain | 库存、制造、维护、PLM、质检、采购 |
| 人力资源 HR | 员工、工资单、招聘、休假、绩效、车队 |
| 营销 Marketing | 社媒、邮件营销、短信营销、营销自动化、WhatsApp、问卷 |
| 服务 Services | 项目、工时、排班、预约、在线客服、工单 |
| 生产力 Productivity | AI、即时通讯 Discuss、VoIP、IoT、文档、知识库 |

这套地图的关键是**按需装配**：你只需启用需要的应用，各模块之间数据相通，不必一次性部署整套系统。注意官网导航是按"官方全家桶"展示的，其中工资单（Payroll）、Studio、电子签等部分应用属企业版专有，社区版并不包含——两版的功能边界，姊妹篇有逐项对比。官方应用之外，[应用商店](https://apps.odoo.com/apps)里有第三方付费与免费模块——官网当前口径是 40k+ 社区模块，从 Shopify 连接器到 MCP Server 都有；OCA（Odoo Community Association）则维护着另一批高质量的开源社区模块。

规模口径上，官网首页写的是 "Join 28 million happy users" 与 "a community of 100k+ developers"（2026-10 读数，营销数字随时间滚动，引用时建议标注时点）。

## 许可证与定价，一句话版本

社区版（odoo/odoo 仓库）以 **LGPL-3.0** 发布，可自由自托管、修改与商用；企业版是闭源订阅增值层。定价页（2026-10 读数）分三档：One App Free 单应用不限用户 €0；Standard 全部应用年付折合 €24.90/用户/月；Custom 档（€44.90 起）解锁自托管企业版、Odoo.sh 私有云与外部 API。另有 €7.90/月的轻度用户档（只报销、打卡之类低频操作）。版本维护策略与两版功能边界的细节，姊妹篇有整节拆解，此处不重复。

## 技术栈

```text
后端:    Python（自研 Odoo 框架，官方要求 Python 3.11+）
数据库:  PostgreSQL（官方文档明确：数据层只支持 PostgreSQL）
前端:    OWL 框架 —— Odoo 自研的 TypeScript UI 框架
视图:    XML 描述界面，QWeb 模板渲染
数据:    CSV / XML 数据文件做初始数据与演示数据
```

两点值得展开：

**OWL**（Odoo Web Library）是理解现代 Odoo 前端的钥匙。它是一个约 30KB gzip、零依赖的 TypeScript 框架，官方 README 的定位是 "It powers Odoo's web client"——整个 Web 客户端都跑在它上面。OWL 自 v14 起进入 Odoo 代码库，其独立仓库 [odoo/owl](https://github.com/odoo/owl) 当前 master 分支正在开发 3.0 alpha（改用 signal 响应式模型）。它有独立的[在线 playground](https://odoo.github.io/owl/playground)，想学前端定制可以直接从那里上手。

**三层架构**是官方文档第一章的内容：展示层 HTML5/JavaScript/CSS，逻辑层纯 Python，数据层仅支持 PostgreSQL。这意味着两件事：选型时不必评估多种数据库；而 Python 代码的任何修改都需要重启服务并配合 `-u` 参数升级模块。

## 开发者第一课：模型、字段与继承

官方后端教程 [server_framework_101](https://www.odoo.com/documentation/20.0/developer/tutorials.html) 共 15 章，用一个房地产广告模块（`estate`）贯穿始终，是上手开发的最短路径。核心概念只有三个：模型、字段、视图。

一个最小的模型定义（教程第三章原文）：

```python
from odoo import fields, models

class TestModel(models.Model):
    _name = "test_model"
    _description = "Test Model"

    name = fields.Char()
```

`_name` 决定 ORM 生成的数据库表名，字段即类属性。教程随后为 `estate.property` 模型添加真实字段——`name`（Char）、`expected_price`（Float）、`date_availability`（Date）、`garden_orientation`（Selection）等十几个字段——并演示用 `./odoo-bin -d rd-demo -u estate` 启动服务，让 ORM 自动建表。字段分两大类：直接存表的简单字段（Boolean、Float、Char、Text、Date、Selection），以及连接记录的关系字段（Many2one、One2many、Many2many）。

真正的门槛不在写模型，而在**三种继承机制**（官方 ORM 参考文档的定义）：

1. **经典继承**：`_name` 与 `_inherit` 同时使用，以现有模型为基类派生新模型，字段、方法全盘继承；
2. **扩展（Extension）**：只写 `_inherit` 不写 `_name`，原位修改现有模型——给 `sale.order` 加一个自定义字段就是这种写法，这是 Odoo 定制生态的基石；
3. **委托继承（`_inherits`）**：组合而非继承，模型把自己没有的字段查找"委托"给子模型，语义是 **has one** 而非 **is one**。注意官方文档的警告原话："_inherits is more or less implemented, avoid it if you can"——能不用就不用。

另一个高频机制是**计算字段**：`total = fields.Float(compute='_compute_total')`，计算方法必须显式赋值；这类字段默认不落库、默认只读，要在搜索和写入场景使用需另行配置。

需要预期的是学习曲线：Odoo 的 ORM、字段系统与继承机制都是自研的，和 Django/Flask 的开发习惯差异较大；但一旦熟悉"模块 + 继承"的扩展方式，多数定制不需要改动核心源码，升级时的维护负担也小得多。

## 部署与上手

| 方式 | 说明 |
|------|------|
| Docker | 官方 `odoo` 镜像（Docker Hub 累计拉取超 5,400 万次），一条命令拉起，适合本地与测试 |
| 打包安装器 | Debian/Ubuntu 的 deb 包、Windows 安装包，官方文档提供仓库配置步骤 |
| 源码 | tarball 或 git clone，配合 `odoo-bin` 直接运行，适合开发 |
| 官方托管 | Odoo Online（SaaS，免运维）与 Odoo.sh（私有云，支持自定义模块） |

学习路径上，[Odoo eLearning](https://www.odoo.com/slides) 有免费视频课程，官方的 [Scale-up 商业游戏](https://www.odoo.com/page/scale-up-business-game)用一个模拟公司把销售、采购、制造流程走一遍，比看文档直观得多。

## 选型对比与适用场景

| 竞品 | 特点 |
|------|------|
| SAP / Oracle | 企业级深度最强，成本与实施复杂度也最高，适合超大型企业 |
| Microsoft Dynamics | 与微软生态深度集成 |
| ERPNext | 开源、Python/Frappe 技术栈，常见替代选项 |
| Tryton | Python 原生、社区较小 |
| **Odoo** | 应用矩阵最全、上手门槛较低，开源核心 + 商业增值 |

**推荐用 Odoo：**

- 需要打通销售、库存、财务、项目等多个环节的中小企业；
- 想从单模块起步（One App Free 档零成本），验证后再逐步扩展；
- 有 Python 技术团队，需要深度定制或本地化部署以满足数据合规。

**不推荐或需谨慎：**

- 万名员工以上的超大型企业——不是不能跑，而是财务与集团管控深度上 SAP/Oracle 仍是更稳的选择；
- 完全没有技术团队且预算仅够自托管的组织——自托管意味着部署、备份、升级全部自理，纯 SaaS 需求应直接看 Odoo Online；
- 追求单点极致的场景——Odoo 的强项是"全"，CRM 不及专精 SaaS、电商不及 Shopify 深度，买它买的是一体化。

**一句话总结：** Odoo 用二十年时间把一个会计工具长成了覆盖八大业务域的应用矩阵，再用 open-core 模式养活每年一个版本的持续投入。对需要一体化的中小企业，社区版零成本起步、按需装配；对开发者，官方教程从零到一个完整模块只要 15 章——两边都值得花一个下午试试。
