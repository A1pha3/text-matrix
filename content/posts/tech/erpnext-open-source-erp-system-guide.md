---
title: "ERPNext：开源ERP系统完整指南"
date: 2026-05-20T09:09:49+08:00
slug: "erpnext-open-source-erp-system-guide"
github_repo: "frappe/erpnext"
source_key: "gh:frappe/erpnext"
description: "ERPNext 是基于 Frappe 框架的开源 ERP 系统，采用 GPL-3.0 许可证，覆盖会计、库存、制造、销售、采购、项目、资产等业务模块。本文从产品定位、功能模块、技术架构到 Docker 部署实践进行系统解读，并给出适用边界判断与二次开发路径。"
draft: false
categories: ["技术笔记"]
tags: ["开源", "ERP", "Python", "企业管理"]
---

# ERPNext：开源 ERP 系统完整指南

> **目标读者**：正在评估开源 ERP 的中小企业管理者、准备实施或二次开发的工程师、实施顾问
> **前置知识**：了解基本业务流程（记账、库存、销售）；做二次开发需要 Python 基础
> **难度定位**：⭐⭐ 入门到进阶

---

## 学习目标

读完本文，你应该能做这几件事：

1. 判断 ERPNext 是否适合你的业务规模和行业，说清楚它替代不了什么
2. 说出会计、库存、制造、项目这几个核心模块各自解决什么问题
3. 理解 Frappe 框架的 DocType 机制为什么让定制成本变低
4. 用 Docker 在本机跑起一个 ERPNext 测试环境，并完成第一笔销售发票录入
5. 知道二次开发的三条路径（界面定制、脚本、独立应用）分别用在什么场景

---

## 本文目录

1. [ERPNext 是什么](#erpnext-是什么)
2. [功能模块](#功能模块)
3. [技术架构](#技术架构)
4. [适用边界](#适用边界)
5. [快速开始：用 Docker 跑一个测试环境](#快速开始用-docker-跑一个测试环境)
6. [二次开发](#二次开发)
7. [常见问题](#常见问题)
8. [自测题](#自测题)
9. [练习](#练习)
10. [进阶路径](#进阶路径)

---

## ERPNext 是什么

[ERPNext](https://github.com/frappe/erpnext) 是印度 Frappe Technologies 公司开发的开源 ERP 系统，GitHub 上有约 39.4k stars（2026 年 9 月中旬核实）。它把会计、库存、制造、销售、采购、项目、资产管理这些业务装进同一个系统，数据在一次录入后全链路流转——一张销售发票提交后，应收账款、库存扣减、总账分录同步发生，不需要在各模块间导入导出。

当前主线版本是 v16（2026 年 9 月时最新为 v16.35.0），v15 仍在维护期，版本线情况可在 [GitHub Releases](https://github.com/frappe/erpnext/releases) 查询。

它和商业 ERP（SAP、Oracle）的差距不在功能清单而在深度：超大型企业需要的集团财务合并、多工厂精细排程、跨国合规，ERPNext 覆盖不了或做得很浅。它的价值区间在中小企业——这部分用户买不起 SAP 的授权和实施，又受够了 Excel 和互相不通的小工具。这里要说清一个常被误读的点：ERPNext 应用是 GPL-3.0，而它底层的 Frappe 框架是 MIT 协议。对最终用户，两者都意味着软件本身零授权费用，你付出的成本是服务器、实施和后续维护。

另外值得知道：ERPNext 不是孤立产品，它构建在 Frappe 框架上，同一家公司还有托管平台 Frappe Cloud、人力资源应用 Frappe HR 等。这意味着你可以把它当现成软件用，也可以当平台在其上开发自己的业务应用。

---

## 功能模块

ERPNext 官方列出的模块包括会计、采购、销售、CRM、库存、制造、项目、POS、质量、支持、资产等。下面挑业务关联最紧密的几个展开。

### 会计

会计是 ERPNext 的地基，其他模块的业务单据最终都会落到总账。核心机制是复式记账：科目表（Chart of Accounts）定义账户结构，每张发票、每笔付款提交时自动生成总账分录（GL Entry），不需要会计手工录凭证。系统内置试算平衡表、资产负债表、利润表、现金流量表等标准报表。

多公司、多币种是原生支持的：一套系统可以管理多个子公司和分支，各自独立核算，出合并报表；不同币种的交易按汇率换算入账。对有跨境业务的公司，这一点往往是决定性的。

### 库存

物料主数据、多仓库、批次和序列号追踪、库存账龄报告。库存和会计是联动的——每次收发货都会产生库存分录，仓库里少了货，总账上的存货科目同步减少，对不上账的情况在系统内不存在。

支持通过再订货点自动触发物料需求，补货建议可以直接转采购单。

### 制造

覆盖多级物料清单（Multi-level BOM）、生产计划、工单、委外加工和质检。BOM 支持嵌套（半成品再组成成品），工单领料时按 BOM 展开扣料。产能规划和车间级精细排程是这个模块的弱项，复杂离散制造的深度需求需要外挂 MES 或降低预期。

### 销售与采购

销售侧覆盖从报价单、销售订单到发货、开票、收款的 Order-to-Cash 流程；采购侧对应 Procure-to-Pay：采购申请、采购订单、收货、付款。定价规则、价格清单、供应商记分卡都是内置功能。CRM 模块管理线索和商机，可以和销售订单衔接。

### 项目

项目立项、任务分解、工时表（Timesheet）、项目收入与成本核算。咨询、软件开发这类按人天计费的服务商可以用它把工时直接转成发票，项目利润一目了然。

### 资产

资产生成、折旧计提、维修记录、报废处理的全生命周期管理。折旧计划按资产类别配置，自动按期生成折旧分录进总账。

### 其他模块

POS（多门店、班次管理）、质量管理（检验计划、不合格报告）、客服工单（SLA、客户门户）、官网和电商集成等。此外，人力资源与薪酬自 v15 起拆分为独立应用 [Frappe HR](https://github.com/frappe/hrms)，需要单独安装；医疗场景的 Healthcare 模块由第三方团队 earthians 维护。装不装、用不用这些扩展，按业务需要决定。

---

## 技术架构

### Frappe 框架与 DocType

ERPNext 的底层是同公司开发的 [Frappe 框架](https://docs.frappe.io/framework)，一个 Python 全栈 Web 框架，服务端用 Python 和 MariaDB，前端是 JavaScript。

理解 Frappe 的关键是 DocType。在 Frappe 里，每个业务对象——销售发票、客户、物料——都是一个 DocType：它定义这个对象的字段结构，框架据此自动生成数据库表、REST API 和表单界面，权限规则也挂在 DocType 上。也就是说，你定义一次数据结构，增删改查界面、API、存储就都有了。

这是 Frappe 系产品定制成本低的根源：加一个字段、改一个表单布局，在界面上操作 DocType 就完成，不用写前后端代码，也不用重启服务。ERPNext 里的每张单据背后都是一个可修改的 DocType 定义，你在系统里看到的每个表单都是元数据驱动的。

前端方面，新版界面基于 [Frappe UI](https://github.com/frappe/frappe-ui) 组件库构建，它是一套 Vue 3 + Tailwind CSS 的组件集合。实时通知和消息推送由 Node.js 的 Socket.IO 服务承担。

### 运行时组成

一套完整的 Frappe/ERPNext 环境不是单个进程，官方 Docker 配置里包含这些服务：

| 服务 | 职责 |
|------|------|
| frontend | Nginx，静态资源与请求路由 |
| backend | Python 应用，处理动态请求 |
| websocket | Node.js Socket.IO，实时消息 |
| queue-short / queue-long | RQ 后台任务队列，按长短任务分级 |
| scheduler | 定时任务（自动备份、到期提醒等） |
| db / redis-cache / redis-queue | MariaDB 与 Redis |

数据库主用 MariaDB；用 Docker 部署时可以通过 compose 覆盖文件改用 PostgreSQL。

### bench：多站点管理工具

Frappe 应用用 [bench](https://github.com/frappe/bench) 命令行工具管理。bench 的模型是一个目录（bench）装多个站点（site），每个站点独立数据库、独立配置，可以装不同的应用组合。日常运维命令如 `bench update`（升级）、`bench backup`（备份）、`bench migrate`（数据库迁移）都通过它执行。

---

## 适用边界

**适合**：

- 预算有限、需要一体化系统的中小企业：会计、库存、销售、采购一次到位
- 业务流程相对标准的贸易、轻制造、服务型企业
- 有 Python 开发能力、想把 ERP 当平台深度定制的团队

**不适合**：

- 需要集团财务合并、多工厂精细排程的超大型企业
- 车间自动化程度高、需要与 MES/PLC 实时联动的重制造场景
- 期望零配置开箱即用的团队——ERPNext 的模块要按业务逐一配置，会计科目表、仓库结构、BOM 都需要实施投入，这是它"免费"的另一面

一个务实的评估办法：先用官网 [Live Demo](https://frappe.io/erpnext/demo) 和本文的 Docker 环境跑通你的核心业务流程，再看差距在哪。差距落在配置能解决的范围，ERPNext 合适；落在需要动框架源码的范围，慎重。

---

## 快速开始：用 Docker 跑一个测试环境

**前置条件**：本机已安装 Docker 和 Docker Compose。

官方 Docker 仓库 [frappe/frappe_docker](https://github.com/frappe/frappe_docker) 提供了一个单文件配置 pwd.yml，专门用于快速体验，包含全部服务组件和一份预置配置：

```bash
# 下载官方快速体验配置
curl -O https://raw.githubusercontent.com/frappe/frappe_docker/develop/pwd.yml

# 启动整套环境
docker compose -f pwd.yml up -d
```

首次启动时，create-site 容器会自动建站并安装 ERPNext 应用，需要等待几分钟。可以用日志观察进度：

```bash
docker compose -f pwd.yml logs -f create-site
```

看到建站完成的信息后，浏览器访问 `http://localhost:8080`，用默认账号登录：

- 用户名：`Administrator`
- 密码：`admin`

**验收标准**：登录成功，看到 ERPNext 的初始化设置向导，语言和地区选择里有中文选项。

登录后可以跟着向导创建一家测试公司（选好币种和会计年度），然后在"会计"模块建一个客户、一张销售发票并提交——提交后到总账报表里查这张发票生成的分录，这是感受"单据驱动记账"最直接的方式。

**注意**：pwd.yml 是官方文档明确定位为测试和演示的配置，数据不保证持久化，密码也是公开的默认值。生产部署要用同仓库的 Easy Install 脚本或 compose 覆盖文件方案，参考 [frappe_docker 文档](https://docs.frappe.io/erpnext/installation)。

**实验结束后清理**：

```bash
docker compose -f pwd.yml down -v
```

`-v` 会删掉数据卷，测试数据一并清空。

不想装任何东西的话，官网 [Live Demo](https://frappe.io/erpnext/demo) 提供了在线演示环境；正式使用还有官方托管 Frappe Cloud，不按用户数收费，按计算资源计费。

---

## 二次开发

定制需求分三档，成本从低到高：

**第一档：界面配置。** 在"自定义表单"（Customize Form）里给任意 DocType 加字段、改布局、加下拉选项；用工作流引擎配置审批流。零代码，升级时保留。

**第二档：脚本。** Client Script（浏览器端 JavaScript）和 Server Script（服务端 Python）挂在 DocType 的事件上，处理校验、联动、自动计算这类逻辑。适合个性化规则，注意服务端脚本需要开启 `server_script_enabled`，且性能敏感的逻辑不适合长期跑在脚本层。

**第三档：独立应用（App）。** 把定制写成独立的 Frappe 应用，用 `bench new-app` 创建、`bench install-app` 装到站点。DocType 扩展、新模块、报表都放进自己的应用里，和 ERPNext 源码解耦，这是官方推荐的正式二次开发方式，也是社区所有扩展应用的形态。

无论哪一档，动手前建议先读 [Frappe 框架文档](https://docs.frappe.io/framework)的 DocType 部分——理解了 DocType，其余 API 和机制都是围绕它展开的。

---

## 常见问题

### Q1：ERPNext 真的免费吗？

**A**：软件本身免费。ERPNext 采用 GPL-3.0 许可证（GPL-3.0 是强 copyleft 协议：如果你基于它做修改并提供网络服务或分发软件，需要遵守相应的开源义务，商用前建议让法务确认一遍）。自托管时你要承担服务器、运维和升级成本；官方托管 Frappe Cloud 和商业支持服务收费，但那是服务费，不是软件授权费。

### Q2：能替代 SAP 或 Oracle 吗？

**A**：看规模。中小企业（几十到几百人）的会计、库存、销售、采购、制造需求，ERPNext 能覆盖大部分。超大型企业的集团财务合并、跨多国税务合规、高并发多工厂协同，SAP/Oracle 的深度目前没有开源系统能追平。把 ERPNext 当"降配 SAP"不恰当，它是另一个价位段的最优解。

### Q3：实施要多久？

**A**：没有统一答案，取决于三件事：上多少模块（只上会计加库存，和会计、库存、制造、全渠道一起上，工作量差一个量级）；数据迁移量（历史单据迁不迁、迁多少年）；定制度（纯配置和写自定义应用，周期和风险完全不同）。可以先只上一两个模块跑三个月，稳定后再扩，比一次性全上风险小得多。

### Q4：中文和多币种支持如何？

**A**：内置简体中文、繁体中文等三十多种语言翻译（翻译覆盖度随版本推进，个别深层界面可能有英文残留，可在翻译平台参与补全）。多币种、多公司、多税率是原生功能，跨国业务可以按公司维度配置不同本位币。

### Q5：怎么备份？

**A**：一条命令备份数据库和附件：

```bash
bench backup --with-files
```

备份文件落在站点的 `private/backups` 目录。生产环境建议把自动备份（scheduler 服务默认开启）配上异地存储——同步到 S3 或其他对象存储，只存在本机的备份扛不住磁盘故障。scheduler 服务本身跑在环境里，恢复流程也值得在上线前实际演练一次。

---

## 自测题

1. ERPNext 用什么许可证？对企业商用和网络服务场景分别意味着什么？
2. 一张销售发票提交后，系统里发生了哪几件事？
3. DocType 是什么？为什么它让 Frappe 系产品的定制成本变低？
4. 界面加字段、写 Server Script、写独立应用，三种定制方式各适合什么场景？
5. pwd.yml 为什么不能用于生产环境？

---

## 练习

### 练习 1：搭建环境并创建公司

**目标**：完成测试环境部署，跑通初始化。

**步骤**：
1. 按本文"快速开始"一节用 pwd.yml 启动环境
2. 用 Administrator/admin 登录，完成设置向导
3. 创建测试公司：设置公司名、默认币种、会计年度
4. 添加一个客户、一个供应商、一个物料

**验收标准**：公司仪表板可访问；客户、供应商、物料三个列表各有一条数据。

### 练习 2：录入第一笔销售发票并核对总账

**目标**：理解单据驱动记账的机制。

**步骤**：
1. 在"会计"模块查看科目表的结构
2. 创建销售发票：选择练习 1 建的客户和物料，填写数量和价格
3. 提交发票
4. 打开总账报表（General Ledger），筛选这家公司，找到发票对应的分录

**验收标准**：发票提交成功；总账里能看到对应的应收账款借方和收入贷方分录；试算平衡表能打开且数据对得上。

### 练习 3：用 Customize Form 加一个自定义字段

**目标**：体验第一档定制的完整流程。

**步骤**：
1. 搜索并打开"自定义表单"（Customize Form）
2. 选择"客户"（Customer）
3. 添加字段：标签"客户等级"，类型 Select，选项填 `A\nB\nC`
4. 保存，刷新页面
5. 打开任意客户记录，验证新字段出现且可选

**验收标准**：客户表单出现"客户等级"下拉框；选了等级的客户记录能正常保存、能按该字段筛选。

---

## 进阶路径

| 阶段 | 做什么 | 资源 |
|------|--------|------|
| 入门 | 跑通 Docker 环境，完成本文 3 个练习 | 本文 + [ERPNext 官方文档](https://docs.frappe.io/erpnext) |
| 实践 | 按你的业务配一套完整流程（科目表、仓库、BOM） | 官方文档各模块章节 |
| 开发 | 学 DocType 与 Frappe API，写一个自定义应用 | [Frappe 框架文档](https://docs.frappe.io/framework) |
| 生产 | 用 Easy Install 或 compose 方案部署，配备份与监控 | [frappe_docker 文档](https://github.com/frappe/frappe_docker) |
| 社区 | 提 issue、参与翻译、读源码 | [GitHub](https://github.com/frappe/erpnext) |

生产化之前必须考虑的三件事：备份策略（见 Q5）、版本升级路径（bench 迁移有版本跨度限制，跨大版本升级要逐级做）、以及上线后的权限模型梳理（角色和权限点挂在 DocType 上，实施时配错权限是常见事故来源）。

---

**相关资源**

| 资源 | 链接 |
|------|------|
| 官网 | [frappe.io/erpnext](https://frappe.io/erpnext) |
| 官方文档 | [docs.frappe.io/erpnext](https://docs.frappe.io/erpnext) |
| GitHub | [github.com/frappe/erpnext](https://github.com/frappe/erpnext) |
| Frappe 框架文档 | [docs.frappe.io/framework](https://docs.frappe.io/framework) |
| 社区论坛 | [discuss.frappe.io](https://discuss.frappe.io) |

---

**文档信息**
难度：⭐⭐ | 类型：入门到进阶 | 更新日期：2026-09-23 | Stars 数据截至 2026-09-16
