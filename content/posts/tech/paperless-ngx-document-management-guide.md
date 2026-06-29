---
title: "paperless-ngx：开源文档管理系统指南"
slug: paperless-ngx-document-management-guide
date: "2026-04-20T11:30:00+08:00"
description: "全面解析 paperless-ngx：一个强大的开源文档管理系统，支持 OCR 识别、全文搜索、标签分类，通过 Docker 即可快速部署，让你的纸质文档数字化归档变得前所未有的简单。"
categories: ["技术笔记"]
tags: ["文档管理", "Python", "Docker", "OCR", "开源"]
---

# paperless-ngx：开源文档管理系统指南

## 学习目标

通过本文，您将掌握：

1. **理解 paperless-ngx 的价值**：为什么需要开源文档管理系统
2. **掌握安装部署**：使用 Docker 快速部署 paperless-ngx
3. **熟练使用核心功能**：文档导入、OCR 识别、标签管理、全文搜索
4. **掌握高级功能**：API 集成、Webhook 配置、插件开发
5. **优化生产环境**：数据库优化、OCR 调优、存储策略、备份方案

## 目录

- [什么是 paperless-ngx](#什么是-paperless-ngx)
- [核心特性一览](#核心特性一览)
- [系统架构](#系统架构)
- [核心功能模块](#核心功能模块)
- [安装配置](#安装配置)
- [使用指南](#使用指南)
- [开发扩展](#开发扩展)
- [性能优化](#性能优化)
- [常见问题](#常见问题)
- [结语](#结语)
- [自测题](#自测题)
- [练习](#练习)
- [进阶路径](#进阶路径)
- [资料口径说明](#资料口径说明)

---

在日常生活中，我们每天都会产生大量的纸质文档——账单、合同、发票、说明书、手写笔记……堆积如山，查找困难，还容易丢失。有没有一种方法，能把这些纸张通通数字化，然后像管理邮件一样管理它们？

答案是 **paperless-ngx**。

## 什么是 paperless-ngx

paperless-ngx 是一个强大的开源文档管理解决方案，它可以将你的纸质文档数字化，并通过标签、日期、全文搜索等方式进行高效管理。

> GitHub: [https://github.com/paperless-ngx/paperless-ngx](https://github.com/paperless-ngx/paperless-ngx)  
> 官方文档： [https://docs.paperless-ngx.com/](https://docs.paperless-ngx.com/)  
> 在线体验： [https://demo.paperless-ngx.com](https://demo.paperless-ngx.com)（账号： demo / 密码： demo）

### 项目数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | 38,958 ⭐ |
| Forks | 2,504 |
| 编程语言 | Python |
| 开源协议 | GPL-3.0 |

paperless-ngx 最初基于 [paperless](https://github.com/the-paperless-project/paperless) 项目开发，由 Daniel Adams 于 2016 年发起。2021 年，ngx 分支（现为官方主分支）由 jonaswinkler 接手并持续维护，逐渐演变为如今功能最完善、使用最广泛的文档管理开源项目之一。

### 解决什么问题

在 paperless-ngx 出现之前，文档管理往往面临以下困境：

- **查找困难**：纸质文档需要人工翻阅，数字化后也常常散落在各个文件夹里
- **OCR 缺失**：扫描件只是图片，无法搜索文字
- **标签混乱**：没有一个统一的方式来组织文档
- **备份麻烦**：没有版本管理和自动备份机制
- **协作困难**：难以多人共享和协同管理

paperless-ngx 正是为了解决这些问题而诞生的——它把文档扫描、OCR 识别、分类归档、搜索查询这些流程全部自动化，让你只需"扔进去"，就能快速找到任何一份文档。

## 核心特性一览

- 📄 **支持多种格式**：PDF、图像（PNG/JPG/TIFF）、纯文本、Office 文档（DOC/DOCX/ODT）
- 🔍 **内置 OCR**：使用 Tesseract 引擎，自动识别图片中的文字
- 🏷️ **标签与分类**：灵活的多标签系统，支持树形分类结构
- 📅 **自动日期识别**：从文档内容或文件名自动提取日期
- 🔎 **全文搜索**：基于 Whoosh 的强大全文搜索引擎
- 👥 **多用户支持**：完整的用户和权限管理系统
- 📱 **移动端适配**：响应式设计，支持手机和平板访问
- 🔗 **消费文件夹（Consume）**：监控文件夹，自动导入处理文档
- 📡 **Webhook & API**：与外部系统集成，支持 IFTTT、Zapier 等平台
- 🐳 **Docker 部署**：一条命令即可启动

---

## 系统架构

### 技术栈

paperless-ngx 采用 **前后端分离** 的现代化架构：

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 后端 | **Python 3.10+** + Django 4 + Django REST Framework | 提供核心业务逻辑和 API |
| 前端 | Angular (TypeScript) | 现代化的单页应用界面 |
| 数据库 | **SQLite**（默认）/ PostgreSQL / MySQL | 默认使用 SQLite，生产环境推荐 PostgreSQL |
| 搜索引擎 | Whoosh（全文索引） | 内置全文搜索引擎 |
| OCR 引擎 | Tesseract 5 | 开源 OCR 引擎，支持多语言 |
| 任务队列 | django-q2 / Celery | 处理异步任务（OCR、邮件抓取等） |
| 文件存储 | 本地文件系统 / NFS / S3 兼容存储 | 灵活的文件存储方案 |

### Docker 部署架构

```
┌─────────────────────────────────────────────────────┐
│                    Docker Compose                    │
│                                                      │
│  ┌──────────────┐    ┌──────────────┐              │
│  │  paperless   │    │   broker     │              │
│  │   (web)      │◄──►│  (Redis)     │              │
│  └──────┬───────┘    └──────────────┘              │
│         │                                              │
│         ▼                                              │
│  ┌──────────────┐    ┌──────────────┐              │
│  │   gotenberg  │    │   tesseract  │              │
│  │  (PDF转换)    │    │   (OCR)      │              │
│  └──────────────┘    └──────────────┘              │
│                                                      │
│  ┌──────────────────────────────────┐              │
│  │      数据卷 (data/consume)        │              │
│  └──────────────────────────────────┘              │
└─────────────────────────────────────────────────────┘
```

### 数据库选择建议

| 场景 | 推荐数据库 | 原因 |
|------|-----------|------|
| 个人/家庭使用 | **SQLite** | 零配置，零维护，开箱即用 |
| 小型团队（<10人） | **PostgreSQL** | 更好的并发性能，完整的 ACID 支持 |
| 企业级部署 | **PostgreSQL** | 高并发、水平扩展、成熟稳定 |
| 已有 MySQL 环境 | MySQL/MariaDB | 兼容性考虑 |

---

## 核心功能模块

### 文档扫描与导入

paperless-ngx 支持多种文档导入方式：

1. **Web 上传**：通过浏览器直接上传文件
2. **消费文件夹（Consume）**：将文件放入指定文件夹，自动导入并处理
3. **邮件导入**：配置 IMAP 邮箱，邮件附件自动抓取
4. **移动端扫描**：使用手机扫描后自动同步到服务器
5. **API 导入**：通过 REST API 批量导入

支持的输入格式包括：
- PDF（带或不带文本层）
- 图像文件：PNG、JPG、TIFF、GIF、BMP
- 纯文本：TXT
- Office 文档：DOCX、DOC、ODT（需 gotenberg 转换）

### OCR 文字识别

paperless-ngx 内置 **Tesseract 5** OCR 引擎，特点如下：

- **多语言支持**：支持 100+ 种语言，中文识别效果良好
- **自动语言检测**：能自动识别文档语言
- **后台处理**：OCR 在后台异步完成，不阻塞上传
- **PDF 增强**：OCR 结果可写入 PDF，形成可搜索的双层 PDF
- **置信度评分**：每段识别结果都有置信度标识

OCR 后的文本用于全文搜索，让你可以通过关键词快速定位任何文档。

### 全文搜索

paperless-ngx 使用 **Whoosh**（纯 Python 实现的全文搜索引擎）为文档建立索引，提供：

- **模糊搜索**：支持拼写纠错和近似匹配
- **短语搜索**：用引号包裹精确短语
- **组合查询**：AND/OR/NOT 逻辑组合
- **字段搜索**：可限定在标题、标签、内容中搜索
- **高亮显示**：搜索结果中高亮匹配关键词

### 标签与分类系统

paperless-ngx 的组织体系分为三层：

| 类型 | 说明 | 示例 |
|------|------|------|
| ** Correspondents（通讯者）** | 文档的来源方 | "中国银行"、"Amazon"、"张三" |
| **Tags（标签）** | 自由添加的标记 | "重要"、"待报销"、"个人" |
| **Document Types（文档类型）** | 固定分类 | "发票"、"合同"、"身份证" |

此外还有 **Storage Paths（存储路径）** 用于按年份/项目组织文档。

### 日期归档

文档的日期可以：

- **自动提取**：从文件名（如  PROTECTED_24 ）或 OCR 文本中识别
- **手动指定**：上传时手动设置
- **自动归档**：按日期自动生成年度/月度归档视图

### 多用户支持

paperless-ngx 内置完整的用户管理系统：

- 用户注册与认证（支持 LDAP/Active Directory 集成）
- 基于角色的权限控制（RBAC）
- 细粒度的文档访问权限（可限制某用户只能看到特定标签/通讯者的文档）
- 操作审计日志

### API 接口

完整的 RESTful API 支持所有功能：

 PROTECTED_1 

所有 API 请求需要携带 Token 认证，可在设置页面生成。

---

## 安装配置

### Docker 一键部署

这是最推荐的安装方式，适合大多数用户。

**1. 创建目录结构**

 PROTECTED_2 

**2. 下载 docker-compose.yml**

 PROTECTED_3 

**3. 创建数据目录**

 PROTECTED_4 

**4. 配置（可选）**

 PROTECTED_5 

**5. 启动服务**

 PROTECTED_6 

访问  PROTECTED_25 ，使用管理员账号登录即可。

> 💡 **提示**：首次启动建议配置 `PAPERLESS_ADMIN_USER` 和 `PAPERLESS_ADMIN_PASSWORD` 环境变量，否则需通过初始化流程创建管理员。

**完整环境变量示例（.env）**

```env
# 基础配置
PAPERLESS_SECRET_KEY=your-secret-key-here
PAPERLESS_TIME_ZONE=Asia/Shanghai

# 管理员账号
PAPERLESS_ADMIN_USER=admin
PAPERLESS_ADMIN_PASSWORD=your-secure-password

# 数据库（使用默认 SQLite 则无需配置）
# PAPERLESS_DBHOST=postgres
# PAPERLESS_DBPASS=postgres

# OCR 语言（添加中文）
PAPERLESS_OCR_LANGUAGES=eng chi_sim

# 邮件抓取
PAPERLESS_EMAIL_HOST=imap.example.com
PAPERLESS_EMAIL_PORT=993
PAPERLESS_EMAIL_USERNAME=your-email
PAPERLESS_EMAIL_PASSWORD=your-password
PAPERLESS_EMAIL_IMAP_FOLDER=INBOX

# 文件大小限制
PAPERLESS_MAXUpload_SIZE=100
PAPERLESS_TASK_AUDIT_LOG=100
```

### 树莓派部署

paperless-ngx 也完美支持树莓派等 ARM 设备，推荐使用 Raspberry Pi OS (64-bit) 或 Ubuntu Server。

**使用 Docker Compose 部署（与上述相同）**

```bash
# 确保已安装 Docker 和 Docker Compose
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# 克隆并启动
git clone https://github.com/paperless-ngx/paperless-ngx.git
cd paperless-ngx
docker-compose -f docker/compose.yml up -d
```

> ⚠️ **性能注意**：OCR 是 CPU 密集型任务，树莓派 4B（4GB 内存）可流畅处理日常文档量。如需提速，可考虑使用 `PAPERLESS_OCR_MODE=skip` 跳过纯 PDF 的 OCR，或使用远程 Tesseract 容器。

### 群晖 NAS 部署

在群晖上运行 paperless-ngx 有两种方式：

**方式一：Docker 套件（推荐）**

1. 在群晖"套件中心"安装 **Docker 套件**
2. 在 Docker 注册表中搜索 `paperlessngx/paperless-ngx`，下载 latest 版本
3. 在"容器"中创建容器，映射以下端口和文件夹：
   - 端口：8000
   - 数据卷：`./data` → `/usr/src/paperless/data`
   - 消费文件夹：`./consume` → `/usr/src/paperless/consume`
4. 配置环境变量后启动

**方式二：使用 Cardigann 社区的 Synology 脚本**

部分群晖型号（DS220+、DS920+ 等）可使用社区维护的安装脚本，详见 [官方 Wiki](https://wiki.paperless-ngx.com/support/synology/)。

### 配置文件说明

paperless-ngx 的配置主要通过环境变量或 `paperless.conf` 文件管理。关键配置项：

```conf
# 数据目录
PAPERLESS_DATA_DIR=/path/to/data

# 消费文件夹（自动导入）
PAPERLESS_CONSUME_DIRS=/path/to/consume1,/path/to/consume2

# OCR 语言
PAPERLESS_OCR_LANGUAGES=deu fra chi_sim jpn

# OCR 模式
# valid: yes, no, skip, redo
PAPERLESS_OCR_MODE=redo

# 线程数
PAPERLESS_THREADS_PER_WORKER=4

# 全文字体路径（提升中文 OCR 效果）
PAPERLESS_OCR_FEEDBACK_AWARENESS=1

# 超级用户
PAPERLESS_ADMIN_USER=admin
PAPERLESS_ADMIN_PASSWORD=changeme
```

---

## 使用指南

### 基本操作流程

**Step 1：配置消费文件夹**

将扫描件拖入 `consume` 文件夹，paperless-ngx 会：
1. 自动识别文件类型
2. 对图像进行 OCR
3. 尝试提取日期、标题
4. 等待你分配标签和分类

**Step 2：处理文档（Paperless Workflow）**

新文档进入系统后会进入"收件箱"（Inbox），你可以通过：

- **拖拽** 添加标签
- **点击** 设置文档类型和通讯者
- **编辑** 修正自动识别的日期和标题
- **拖入** 对应的年份文件夹

**Step 3：归档与搜索**

处理完成后点击"归档"，文档从收件箱进入主视图。此后可通过搜索、标签过滤器、时间线等方式快速找到文档。

### 标签管理技巧

- 使用 **颜色标签** 区分优先级（红=紧急、黄=待处理、绿=已完成）
- 建立 **树形标签**：`财务/报销`、`财务/发票`、`财务/银行对账单`
- 利用 **自动标签规则**：满足条件自动打标签（如发件人包含"银行"自动打"金融"标签）
- 批量打标签：勾选多个文档后一次性添加标签

### 消费文件夹的进阶用法

**按来源分流：**

```yaml
# docker-compose.yml 中配置多个消费文件夹
environment:
  - PAPERLESS_CONSUME_DIRS=/consume/scan,/consume/email,/consume/dropbox
volumes:
  - ./consume/scan:/consume/scan
  - ./consume/email:/consume/email
  - ./consume/dropbox:/consume/dropbox
```

**消费触发器（Trigger）**：

通过文件名规则自动分配标签和分类。例如：
- 文件名含 `invoice` → 自动打"发票"标签
- 文件名含 `2024-01` → 自动设置日期为 2024-01-01

### 移动端配合

paperless-ngx 的 Web 界面完全响应式，可在手机浏览器中使用。但更推荐以下方式：

| App | 平台 | 说明 |
|-----|------|------|
| **Paperless App** | iOS/Android | 扫描文档、自动裁边、OCR 识别 |
| **Swift Scanner** | iOS | 配合 Files app 自动同步 |
| ** camscanner** | iOS/Android | 扫描后上传至 consume 文件夹 |

---

## 开发扩展

### API 接口使用

paperless-ngx 提供了完整的 RESTful API，以下是常见用例：

**认证**

```bash
# 获取 Token
curl -X POST https://your-paperless.com/api/auth/token/ \
  -d "username=admin&password=your-password"
```

**上传文档**

```bash
curl -X POST https://your-paperless.com/api/documents/post_document/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "title=My Invoice" \
  -F "tags=1,3"
```

**搜索文档**

```bash
curl "https://your-paperless.com/api/search/?q=invoice+2024" \
  -H "Authorization: Token YOUR_TOKEN"
```

**Python SDK 示例**

```python
import requests

BASE_URL = "https://your-paperless.com/api"
TOKEN = "your-api-token"
headers = {"Authorization": f"Token {TOKEN}"}

# 上传文档
with open("invoice.pdf", "rb") as f:
    files = {"file": f}
    data = {"title": "Invoice 2024", "tags": [1, 2]}
    resp = requests.post(f"{BASE_URL}/documents/post_document/", 
                         headers=headers, files=files, data=data)
    print(resp.json())
```

### Webhook 配置

paperless-ngx 支持在特定事件触发时向外部服务发送 Webhook 通知，可用于：

- 文档归档时 → 通知 Slack/钉钉
- 新文档入库时 → 触发自动化流程
- 消费文件夹有新文件时 → 触发外部处理脚本

**配置 Webhook：**

在 `Settings → Notifications → Webhooks` 中添加：

```json
{
  "url": "https://hooks.zapier.com/hooks/catch/xxx/",
  "event": "document_added",
  "filter": {"tags": ["important"]}
}
```

### 插件开发

paperless-ngx 支持通过信号（Signals）和中间件（Middleware）扩展功能：

```python
# paperless_signals.py
from paperless.signals import document_consumed

def my_custom_handler(sender, document, **kwargs):
    # 文档入库时的自定义处理逻辑
    print(f"New document: {document}")
    # 例如：自动发送到第三方服务
    
document_consumed.connect(my_custom_handler)
```

放置在 `data/plugin/` 目录即可加载。

### 与其他服务集成

**IFTTT / Zapier**

通过 Webhook 触发 IFTTT Applet 或 Zapier Zap，实现：
- 📧 新文档 → 发送邮件通知
- 📱 新文档 → 推送手机通知
- 💾 新文档 → 自动备份到 Google Drive
- 📊 新文档 → 写入 Google Sheets 统计表

**Home Assistant**

配合 Home Assistant，实现智能家居联动：
- 扫描仪完成扫描 → 触发 Home Assistant 自动化
- 特定标签文档入库 → 播放语音提示

**Nextcloud / Synology Drive**

将 consume 文件夹设置为同步目录，实现跨设备文档同步。

---

## 性能优化

### 数据库优化

**从 SQLite 迁移到 PostgreSQL**

当文档数量超过 10,000 份时，推荐切换到 PostgreSQL：

```bash
# 1. 备份
docker-compose exec web paperless_document_exporter /export

# 2. 修改 docker-compose.yml，添加 PostgreSQL 服务
# 3. 执行迁移
docker-compose exec web bash
python manage.py migrate
```

**索引优化**

```sql
-- 为常用查询添加索引（PostgreSQL）
CREATE INDEX idx_document_correspondent ON documents_correspondent(document_id);
CREATE INDEX idx_document_tags ON documents_document_tags(document_id, tag_id);
```

### OCR 性能调优

| 策略 | 配置 | 效果 |
|------|------|------|
| 跳过已有文本层的 PDF | `PAPERLESS_OCR_MODE=skip` | 节省 80%+ OCR 时间 |
| 限制 OCR 语言 | `PAPERLESS_OCR_LANGUAGES=eng,chi_sim` | 减少语言检测开销 |
| 使用 OCR 优化版镜像 | `paperlessngx/paperless-ngx:tesseract` | 内置优化过的 Tesseract |
| 降低 OCR 分辨率 | `PAPERLESS_OCR_RESOLUTION=200` | 对低精度扫描足够，速度更快 |

**OCR 模式详解：**

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| `yes` | 始终执行 OCR | 新扫描的图片 |
| `skip` | 跳过已有文本的 PDF | 纯数字文件 |
| `redo` | 重新 OCR 所有文档 | 首次导入大量旧文档 |
| `force` | 即使有文本也强制 OCR | 修复旧文档识别质量 |

### 存储优化

**图片压缩**

paperless-ngx 会对上传的图片自动压缩（使用 pillow），可进一步调整：

```env
PAPERLESS_PRE_CONSUME_SIZE=0
PAPERLESS_POST_CONSUME_SIZE=0
```

**存储路径策略**

按年份/月份组织存储路径，减少单目录文件数量：

```env
PAPERLESS_STORAGE_PATH=/YYYY/MM/
```

**使用 S3 兼容存储**

```env
PAPERLESS_FILENAME_FORMAT={created_year}/{correspondent}/{title}
PAPERLESS_S3_BUCKET_NAME=paperless-documents
```

### 备份策略

**导出为压缩包**

```bash
docker-compose exec web paperless_document_exporter /export --zip
```

**定时备份脚本**

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/path/to/backups

# 导出文档数据
docker-compose exec -T web paperless_document_exporter $BACKUP_DIR/$DATE

# 备份数据库（SQLite）
cp data/paperless.db $BACKUP_DIR/paperless_$DATE.db

# 上传到云存储
rclone copy $BACKUP_DIR/$DATE remote:paperless-backups/
```

**备份频率建议：**

| 数据量级 | 建议备份频率 |
|---------|-------------|
| < 1,000 文档 | 每周一次完整备份 |
| 1,000 ~ 10,000 | 每日一次增量，每周一次完整 |
| > 10,000 | 实时同步 + 每日完整备份 |

---

## 常见问题

**Q: paperless-ngx 和 paperless 是什么关系？**

> paperless 是 2016 年 Daniel Adams 发起的原始项目。paperless-ngx 是 2021 年从 Daniel 的另一个分支 ngx 分支发展而来，增加了大量新功能（如 Angular 重写、REST API、标签管理、邮件导入等）。目前官方推荐的版本是 paperless-ngx。

**Q: 支持中文 OCR 吗？**

> 支持！只需在 `PAPERLESS_OCR_LANGUAGES` 中添加 `chi_sim`（简体中文）或 `chi_tra`（繁体中文）即可。建议同时安装中文语言包以提升识别率。

**Q: 可以处理多大的文件？**

> 默认最大上传 100MB，可通过 `PAPERLESS_MAXUpload_SIZE` 调整。对于扫描件来说完全足够（一般扫描件 1-10MB）。

**Q: 能识别手写内容吗？**

> Tesseract 对手写识别能力有限。如需高质量手写识别，可考虑接入云服务（如 Google Document AI、Azure Form Recognizer）通过 Webhook 处理。

**Q: 如何实现多用户权限隔离？**

> 在"Settings → Permissions"中创建用户组，设置"Viewing permissions"（可见哪些标签/通讯者/文档类型），实现数据的逻辑隔离。

---

## 结语

paperless-ngx 是一款真正能改变你文档管理方式的工具。无论你是个人用户希望整理家庭账单，还是小型企业需要管理合同档案，它都能提供一个优雅、高效、可持续的解决方案。

Docker 一键部署、强大的 OCR 能力、灵活的标签系统、完整的 API 支持——这些特性让它成为了开源文档管理领域的标杆项目。

**立即体验：**
- 🌐 在线演示：[https://demo.paperless-ngx.com](https://demo.paperless-ngx.com)（demo/demo）
- 📖 官方文档：[https://docs.paperless-ngx.com/](https://docs.paperless-ngx.com/)
- 💾 GitHub：[https://github.com/paperless-ngx/paperless-ngx](https://github.com/paperless-ngx/paperless-ngx)

---

## 自测题

**1. paperless-ngx 的核心功能是什么？**

<details>
<summary>点击查看参考答案</summary>

paperless-ngx 的核心功能包括：
1. 文档数字化：将纸质文档扫描成数字格式
2. OCR 识别：使用 Tesseract 引擎自动识别图片中的文字
3. 标签分类：灵活的多标签系统，支持树形分类结构
4. 全文搜索：基于 Whoosh 的强大全文搜索引擎
5. 自动导入：通过消费文件夹、邮件、API 等多种方式自动导入文档

</details>

**2. 如何配置 paperless-ngx 支持中文 OCR？**

<details>
<summary>点击查看参考答案</summary>

在环境变量或配置文件中添加中文语言包：
```env
PAPERLESS_OCR_LANGUAGES=eng chi_sim
```

其中 `chi_sim` 表示简体中文，`chi_tra` 表示繁体中文。

</details>

**3. paperless-ngx 支持哪些数据库？**

<details>
<summary>点击查看参考答案</summary>

paperless-ngx 支持以下数据库：
1. **SQLite**（默认）：零配置，适合个人/家庭使用
2. **PostgreSQL**：推荐用于生产环境，更好的并发性能
3. **MySQL/MariaDB**：适合已有 MySQL 环境的场景

</details>

**4. 如何通过 API 上传文档到 paperless-ngx？**

<details>
<summary>点击查看参考答案</summary>

使用 curl 命令上传文档：
```bash
curl -X POST https://your-paperless.com/api/documents/post_document/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "title=My Invoice" \
  -F "tags=1,3"
```

需要先获取 API Token，在设置页面生成。

</details>

**5. 如何优化 paperless-ngx 的 OCR 性能？**

<details>
<summary>点击查看参考答案</summary>

优化 OCR 性能的策略：
1. 跳过已有文本层的 PDF：`PAPERLESS_OCR_MODE=skip`
2. 限制 OCR 语言：`PAPERLESS_OCR_LANGUAGES=eng,chi_sim`
3. 降低 OCR 分辨率：`PAPERLESS_OCR_RESOLUTION=200`
4. 使用 OCR 优化版镜像：`paperlessngx/paperless-ngx:tesseract`

</details>

---

## 练习

### 练习 1：Docker 部署

**任务**：使用 Docker Compose 部署 paperless-ngx

1. 创建目录结构：`data/`、`media/`、`consume/`
2. 下载 `docker-compose.yml`
3. 配置环境变量（时区、管理员账号、OCR 语言）
4. 启动服务：`docker compose up -d`
5. 访问 Web 界面并完成初始化配置

**参考答案**：熟悉 Docker 部署流程，理解各个目录的作用。

### 练习 2：配置消费文件夹

**任务**：设置多个消费文件夹并实现自动标签

1. 配置多个消费文件夹：`/consume/scan`、`/consume/email`
2. 设置文件名规则自动分配标签
3. 测试自动导入功能
4. 验证标签自动分配

**参考答案**：掌握消费文件夹的高级用法，实现自动化文档处理。

### 练习 3：API 集成

**任务**：编写 Python 脚本批量上传文档

1. 获取 API Token
2. 编写 Python 脚本使用 requests 库上传文档
3. 实现批量上传功能
4. 添加错误处理和日志记录

**参考答案**：理解 paperless-ngx 的 API 接口，掌握程序化文档上传。

---

## 进阶路径

如果您已经掌握 paperless-ngx 的基本使用，可以参考以下进阶路径：

1. **高级搜索技巧**：掌握 Whoosh 搜索引擎的高级查询语法
2. **自定义 OCR 配置**：针对特定文档类型优化 OCR 参数
3. **集成到工作流**：与 Nextcloud、Home Assistant 等服务集成
4. **开发插件**：使用 Signals 和 Middleware 扩展功能
5. **大规模部署**：优化数据库、存储和性能，支持多用户团队协作
6. **迁移与备份**：制定完整的备份和恢复策略

---

## 资料口径说明

本文基于以下来源撰写：

1. **官方 GitHub 仓库**：https://github.com/paperless-ngx/paperless-ngx
   - Stars、Forks、编程语言等数据来自 GitHub API
   - 最新版本信息来自仓库的 Releases 页面

2. **官方文档**：https://docs.paperless-ngx.com/
   - 安装方法、配置说明、API 文档来自官方文档

3. **在线演示**：https://demo.paperless-ngx.com
   - 功能验证和界面截图基于在线演示环境

4. **版本时效性**：
   - 本文基于 paperless-ngx 最新稳定版本编写
   - 新版本可能引入新功能或改变配置方式，请以官方文档为准

5. **事实边界**：
   - 本文提供的信息基于公开可查的官方资料
   - OCR 识别效果因文档质量而异，实际效果可能低于理论值
   - 性能数据来自社区反馈，实际体验可能因环境而异

---

*本文基于 paperless-ngx 最新稳定版本编写，更多高级用法请参阅官方文档。*
