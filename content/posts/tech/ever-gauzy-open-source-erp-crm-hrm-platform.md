---
title: "Ever Gauzy：一个 AGPL 开源平台想把 ERP、CRM、HRM 全部塞进来"
date: 2026-09-25T03:30:00+08:00
draft: false
description: "7.9k star 的开源商业管理平台 Ever Gauzy 深度解读：NestJS + Angular 全家桶架构、时间追踪与会计模块拆解、四种部署形态，以及 AGPL 协议对商用的影响。"
tags: ["开源", "ERP", "CRM", "自托管", "TypeScript"]
categories: ["技术笔记"]
github_repo: "ever-co/ever-gauzy"
source_key: "gh:ever-co/ever-gauzy"
slug : ever-gauzy-open-source-erp-crm-hrm-platform
---

## 一句话说清它是什么

[Ever Gauzy](https://github.com/ever-co/ever-gauzy) 是一个开源的**商业管理平台**——用一个词概括就是把 ERP（企业资源计划）、CRM（客户关系管理）、HRM（人力资源管理）、ATS（招聘追踪）、项目管理五套系统合并成一个应用。截稿时约 7,900 star，TypeScript 为主（占比超 90%），AGPL-3.0 协议，2019 年开源，至今仍在高频迭代。

它的定位很直接：中小企业通常买不起（也不需要）SAP/Oracle 级别的 ERP，但又确实需要超过 Excel 能力的进销存、开票、员工管理——Gauzy 想做这个夹缝市场里"自己部署、按需取用"的那一个。

## 功能面：广得有点吓人

按官方 README 的完整列表，它覆盖：员工管理与入职、时间追踪与活动监控、招聘管道（ATS）、客户/线索管理、项目与任务、OKR/KPI、销售管道与报价、会计/开票/收支、库存与供应链、设备共享、多组织管理、审批流、邮件模板、报表分析……外加 Upwork、HubStaff 等第三方集成。

对这种"全家桶"要有清醒预期：**广度和深度是矛盾的**。它的每个模块大概率不如垂直 SaaS 专精（比如开票比不了专业财务软件），价值在于数据在一个库里流转——时间追踪的工时直接进工资单，项目成本直接进财务报表，不需要在五个系统之间导 CSV。

## 技术架构：老派但扎实的全栈 TypeScript

技术栈取证（来自仓库 languages API 和 README）：

- **后端**：NestJS + TypeORM/MikroORM/Knex 双 ORM 策略——这个组合值得注意，TypeORM 处理关系映射，MikroORM 补位，换来的是对 SQLite（默认/演示）、PostgreSQL（生产推荐）、MySQL/MariaDB、CockroachDB、MS SQL 甚至 MongoDB 的广泛兼容
- **前端**：Angular + RxJS，基于 ngx-admin 模板体系
- **工程化**：Nx + Lerna monorepo，一个仓库装下 API、Web、桌面端多个应用
- **语言构成**：TypeScript 45.5MB + SCSS 3.2MB，几乎纯 TS 项目

**Headless API 是关键设计**：整个平台的能力通过 REST API 暴露（文档在 api.gauzy.co/docs），前端只是 API 的一个消费者。官方的另一款产品 Ever Teams（团队协作平台）就是直接挂在 Gauzy API 上运行的——这意味着你也可以把 Gauzy 当**后端业务中台**用，自己写前端。

## 四种部署形态

Gauzy 在部署上给了少见的完整选项：

1. **在线 Demo**（demo.gauzy.co）：每天重置数据，先看再装
2. **Gauzy Server**：自带 API + SQLite，一条命令跑起给中小组织用，可外接 PostgreSQL
3. **桌面全量版**（Win/Mac/Linux）：UI + API + 数据库打包成一个桌面应用，个人或连接远程 Server 用
4. **Docker Compose / K8s**：标准生产路径，官方推荐 PostgreSQL + Kubernetes

一个安全细节值得表扬：Demo 环境的默认账号（`admin@ever.co` / `admin`）只作用于演示，生产安装的 API **会在没有显式设置 `DEMO_SUPER_ADMIN_PASSWORD` 等环境变量时拒绝 seed 数据**——从代码层面杜绝了"默认弱口令带上线"这个经典事故。

## 上手实操

最快的本地体验路径：

```bash
git clone https://github.com/ever-co/ever-gauzy.git
cd ever-gauzy
# 用官方预构建镜像跑 Demo 形态（需 Docker Compose ≥ v2.20）
docker-compose -f docker-compose.demo.yml up
```

默认管理员 `admin@ever.co / admin`（仅限本地/演示）。想认真评估，建议直接切 PostgreSQL 并通读 `.env.demo.compose` 的配置项——数据库类型、种子数据开关都在那里。

## 必须想清楚的三件事

**1. AGPL-3.0 协议是商用红线。** Gauzy 用的是 AGPL 而不是 MIT/Apache——如果你基于它做二次开发并提供网络服务，**修改后的源代码有义务公开**。想拿它做 SaaS 底座封闭商用的，先去理解 AGPL 的网络传播条款，或者联系官方（ever.co）谈商业授权。这是它和 LibreChat（MIT）这类项目本质不同的地方。

**2. 功能广 = 评估成本高。** 全家桶的坑在于你很难快速判断"我需要的那个模块它做得够不够好"。建议反向评估：列出你未来 12 个月**必须**用的三个模块（比如时间追踪+开票+员工管理），Demo 环境里只测这三个，其他当赠品。

**3. 项目在快速演进期。** SaaS 版标注 Alpha，文档标注 WIP，commit 频率很高（截稿当日仍有推送）。自托管请锁定 release 版本，跟随 `master` 分支裸跑风险自负。

## 什么场景值得选它

**适合：**
- 5~50 人的远程团队/外包公司/工作室，核心诉求是工时追踪 + 开票 + 员工管理一体化；
- 愿意接受 AGPL（或预算购买商业授权）的技术型团队；
- 需要 Headless 业务中台、自己掌控前端的开发者。

**不适合：**
- 需要专业财务合规（如中国财税发票体系）的场景——会计模块是通用模型，本地化深度有限；
- 只想要单点功能（比如只要 CRM）的团队——上全家桶的运维成本不划算，垂直方案更合适；
- 无 TypeScript/运维能力的非技术团队——桌面版可以试，但出问题没人修。

## 结语

Ever Gauzy 是那种"雄心大于精致度"的项目：功能清单长得像 ERP 教科书目录，工程底座（Nx monorepo、双 ORM、Headless API）却搭得相当认真。它不适合所有人，但对恰好落在它目标区间里的小团队，这是开源世界里少有的"一套系统管完生意"的可选答案。评估时记住两个关键词：**AGPL** 和 **三模块测试法**。

> 仓库：https://github.com/ever-co/ever-gauzy ｜ 官网：https://gauzy.co ｜ 文档：https://docs.gauzy.co
