---
title: "drawDB：在浏览器里画数据库 ER 图并直接生成 SQL"
date: 2026-08-11T03:22:16+08:00
slug: "drawdb-browser-erd-editor-sql-generator"
github_repo: "drawdb-io/drawdb"
source_key: "gh:drawdb-io/drawdb"
description: "drawDB 是一个纯前端的数据库实体关系图编辑器，无需注册账号即可在浏览器中拖拽建表、设外键、生成多方言 SQL 和迁移脚本，支持 Docker 一键部署。"
draft: false
categories: ["技术笔记"]
tags: ["数据库设计", "ER图", "SQL生成", "前端工具", "开源"]
---

## 这个项目解决了什么

数据库设计阶段，开发者要么在纸上线描表结构，要么用重量级工具（Navicat、DataGrip、dbdiagram.io）。前者不可复用，后者要么收费、要么需要注册账号、要么不能自部署。drawDB 把这件事简化到打开浏览器就能做：拖拽建表、连线设外键、一键导出多方言 SQL（MySQL、PostgreSQL、SQLite、MariaDB、SQL Server、Oracle），全程不用注册。

核心数据：38.7K Stars、3.2K Forks、JavaScript 为主、AGPLv3 协议、在线演示站 drawdb.app。

## 核心能力

drawDB 的功能集中在"画图 → 生成 SQL"这条主线上：

- **可视化建表**：在画布上放置表卡片，逐字段定义名称、类型、约束（NOT NULL、UNIQUE、PRIMARY KEY、AUTO_INCREMENT）
- **关系连线**：表之间拖线建立外键关系，自动在 SQL 中生成 `FOREIGN KEY` 约束
- **多方言导出**：支持 MySQL、PostgreSQL、SQLite、MariaDB、SQL Server、Oracle 六种 SQL 方言
- **迁移脚本生成**：在已有表结构和目标表结构之间生成 `ALTER TABLE` 迁移脚本
- **导入反向工程**：从现有 SQL DDL 脚本反向解析出 ER 图
- **自动排列**：2026-08-09 合入的 auto-arrange 功能（PR #1097），可自动整理表布局
- **模板库**：预设常见业务场景的表结构模板，快速起步

## 技术实现

drawDB 是一个纯前端应用，技术栈：

- **框架**：React + Vite
- **画布渲染**：基于 HTML/CSS 的 DOM 操作（非 Canvas/WebGL），表和连线都是 DOM 元素
- **状态管理**：React 内置状态（无 Redux/Zustand）
- **数据持久化**：LocalStorage（无需后端），可选对接 drawdb-server 实现文件分享

这意味着整个应用可以静态部署——`npm run build` 产出纯静态文件，用任何静态服务器或 Docker（Nginx）托管即可。

## 快速上手

### 本地开发

```bash
git clone https://github.com/drawdb-io/drawdb
cd drawdb
npm install
npm run dev
```

### Docker 部署

```bash
docker build -t drawdb .
docker run -p 3000:80 drawdb
```

Docker 镜像内是 Nginx 托管的静态文件，启动后访问 `http://localhost:3000` 即可。

如果需要文件分享功能，需要额外部署 [drawdb-server](https://github.com/drawdb-io/drawdb-server)，按 `.env.sample` 配置环境变量。不部署也不影响核心画图功能。

## 适用边界

**适合**：

- 项目初期快速设计数据库结构并和团队讨论
- 教学场景（数据库课程、ORM 概念演示）
- 从 SQL DDL 快速理解既有数据库结构
- 生成迁移脚本评估表结构变更影响

**不适合**：

- 超大规模数据库设计（数百张表以上，DOM 渲染会卡）
- 需要版本协同编辑的场景（无多人协作功能）
- 需要直接连接数据库执行 DDL 的场景（drawDB 只生成 SQL，不执行）
- 商业闭源项目（AGPLv3 协议要求衍生作品同样开源）

项目最近一次发布无 Release 记录，但提交活跃（2026-08-09 auto-arrange、DOMPurify 安全升级），说明处于持续迭代中。
