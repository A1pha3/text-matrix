---
title: "Paperless-ngx：开源文档管理系统的完整指南"
date: "2026-05-25T20:08:27+08:00"
slug: "paperless-ngx-document-management-system-guide"
description: "Paperless-ngx 是一个基于 Django 的开源文档管理系统，支持扫描、OCR 识别、索引和归档功能。本文详细解析其核心功能、架构设计、Docker 部署方式以及适用场景。"
draft: false
categories: ["技术笔记"]
tags: ["开源", "文档管理", "Django", "OCR", "Python"]
---

# Paperless-ngx：开源文档管理系统的完整指南

Paperless-ngx 是一个社区维护的开源文档管理系统（Document Management System，DMS），其核心功能是将纸质文档数字化为可搜索的在线归档库。用户只需扫描文档，系统自动完成 OCR（光学字符识别）识别、全文索引和分类归档，彻底告别纸质文件堆积。

## 项目定位

Paperless-ngx 是 Paperless 项目的官方继承者。原始 Paperless 项目由 the-paperless-project 维护，后来演变为 Paperless-ng（由 Jonas Winkler 主导），最终在 2022 年合并为现在的 Paperless-ngx，由社区团队共同推进开发。

从定位上看，这是一个**快速上手型**项目：安装简单、界面直观、最小示例可以在 10 分钟内跑通，适合个人和家庭用户管理发票、合同、手册等日常文档，也适合小团队处理归档需求。

核心特点：

- 基于 Django + Angular 构建
- 内置 Tesseract OCR 引擎
- 支持 PDF、图片等多种格式
- 提供完整 Web UI 和 REST API
- Docker Compose 一键部署

## 核心功能解析

### 文档扫描与 OCR

用户通过 Web 上传或邮件导入文档后，Paperless-ngx 自动调用 Tesseract 进行 OCR 识别，将扫描件中的文字提取为可搜索文本。识别后的文本存储在数据库中，支持精确关键词搜索。

这个过程对用户是透明的——上传即搜，无需手动触发。

### 自动分类与标签

系统支持基于规则自动为文档打标签、分配 correspondent（对应方）和 document type（文档类型）。规则支持正则表达式匹配，可以通过文档内容自动归类。例如所有来自某家保险公司的邮件自动标记为"保险"类型。

### 全文搜索与过滤

Web UI 提供实时搜索框和多种过滤维度（日期范围、标签、类型、对应方）。搜索结果高亮匹配词，支持按相关度或日期排序。

### 多用户与权限

支持创建多用户账号，不同用户可以看到不同的视图和标签。但权限模型相对简单——没有细粒度的文档级访问控制，更适合作为个人工具或小型团队共享使用。

## 技术架构

Paperless-ngx 的技术栈：

| 层次 | 技术选型 |
|------|----------|
| 后端 | Django + Django REST Framework |
| 前端 | Angular（独立部署，Go 语言编写，配合 SWAG） |
| 数据库 | PostgreSQL（生产推荐）或 SQLite（开发/轻量使用） |
| OCR | Tesseract |
| 任务队列 | Paperless Paperless（基于 Django Channels） |
| 部署 | Docker Compose |

数据库中存储的是文档元数据、OCR 文本和搜索索引，实际文件保存在配置的归档目录中。OCR 识别是计算密集操作，Docker 部署时 Tesseract 运行在独立容器中，避免阻塞主服务。

## 安装与快速开始

最推荐的部署方式是 Docker Compose。官方在仓库根目录提供了完整的配置文件：

```bash
# 克隆仓库
git clone https://github.com/paperless-ngx/paperless-ngx.git
cd paperless-ngx

# 启动服务
docker compose up -d

# 访问 Web UI
# 默认地址：http://localhost:8000
# 登录凭证：demo / demo（演示模式）
```

首次启动后建议修改管理员密码。数据目录和端口可以在 `docker-compose.yml` 中按需调整。

## 适用边界

**适合的场景：**
个人和家庭用户的文档归档（发票、合同、证件扫描件）；小团队（5 人以内）的共享文档库；需要离线部署、避免使用云服务的场景。

**不太适合的场景：**
需要细粒度权限控制的企业级文档管理；超大批量（百万级以上）的文档处理；需要与 Office 套件深度集成的协作编辑场景。

## 阅读路径

如果想深入定制 Paperless-ngx，推荐顺序：

1. 官方文档：https://docs.paperless-ngx.com/
2. Docker 配置文件：`docker/compose/` 目录
3. 任务处理模块：`paperless/apps.py` 中的 `AppConfig`
4. OCR 工作流：`paperless/management/commands/document_consumer.py`

---

*本文档基于 GitHub 仓库 2026 年 5 月最新信息编写，Stars：41,118，License：GPL-3.0。*