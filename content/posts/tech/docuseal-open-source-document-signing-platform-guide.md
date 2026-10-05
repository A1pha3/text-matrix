---
title: "DocuSeal 拆解：模板、提交、Webhook 三条主线，和一条写进许可证的署名条款"
date: "2026-05-05T11:35:00+08:00"
lastmod: "2026-09-30T00:00:00+08:00"
slug: "docuseal-open-source-document-signing-platform-guide"
github_repo: "docusealco/docuseal"
source_key: "gh:docusealco/docuseal"
description: "对照 docusealco/docuseal 的 master 分支、GitHub Release 3.3.0 与官方 API 文档拆解 DocuSeal：Template、Submission、Submitter 三个资源如何组成签署流程，11 种 Webhook 事件与 X-Docuseal-Signature 验签怎么接，SQLite、PostgreSQL 与本地磁盘、S3 这些默认值从哪来，以及 AGPLv3 附加署名条款和 Pro 功能墙对自托管采用的实际影响。"
draft: false
categories: ["技术笔记"]
tags: ["开源", "PDF", "文档处理", "Docker"]
---

# DocuSeal 拆解：模板、提交、Webhook 三条主线，和一条写进许可证的署名条款

> **目标读者**：正在给自己的产品或公司流程选电子签名方案的工程师——关心数据放在哪、API 能不能驱动全流程、许可证有什么实际约束。
> **核心问题**：DocuSeal 用什么模型组织签署流程，自托管时默认值落在哪里，哪些能力开源版就有、哪些在 Pro 墙外。
> **事实边界**：本文核对的是 `docusealco/docuseal` 的 `master` 分支（2026-09-30 浅克隆）、GitHub Release `3.3.0`（2026-09-28 发布）与官方 API 文档 [docuseal.com/docs](https://www.docuseal.com/docs)（2026-09-30 读取）。API 行为指到文档页，代码行为指到仓库内文件；仓库与文档之外的内容不写成事实。

## 一句话判断

DocuSeal 把电子签名拆成三个资源：**Template**（模板）定义"签什么"，**Submission**（提交）是一次具体的签署请求，**Submitter**（签署方）是请求里的每一方。Web 界面和 REST API 操作同一套模型，Webhook 把每一步状态变化推回业务系统。

这个结构决定了它的取舍：自托管、API（应用程序接口）驱动、数据不出自己的服务器；代价写在许可证里——AGPLv3 加一条 Section 7(b) 附加条款，要求在交互界面保留 DocuSeal 署名。白标、SSO（单点登录）、批量发送、API 创建模板这些企业向能力则在 Pro 版清单里。

## 项目坐标（2026-09-30 核对）

| 字段 | 值 |
|------|------|
| 仓库 | [docusealco/docuseal](https://github.com/docusealco/docuseal)，默认分支 `master`，建仓 2023-07-03，最近推送 2026-09-28 |
| 社区数据 | Stars 18,633 · Forks 1,878 · Watchers 71 · 贡献者 6 人（主要维护者 omohokcoj，2,473 次提交） |
| 最新版本 | [3.3.0](https://github.com/docusealco/docuseal/releases)（2026-09-28），此前 3.2.6（2026-09-21） |
| 许可证 | AGPLv3 + [Section 7(b) 附加条款](https://github.com/docusealco/docuseal/blob/master/LICENSE_ADDITIONAL_TERMS) |
| 语言构成 | Ruby 38.1% · Vue 28.3% · HTML 20.8% · JavaScript 12.5%（GitHub Languages API） |
| 技术栈 | Rails 单体 + Vue 3 前端 + Sidekiq（Webhook 队列）+ Redis（本机自动启动） |
| 官方入口 | [docuseal.com](https://www.docuseal.com) · [demo.docuseal.tech](https://demo.docuseal.tech) · [Docker Hub](https://hub.docker.com/r/docuseal/docuseal) |

几个数字值得先看一眼：贡献者只有 6 人，其中一人提交了 2,473 次——这是一个典型的单一维护者主导的项目。18,633 个 Stars 说明社区需求真实存在，但也意味着深度定制前要先评估上游的响应速度。

## 系统地图：六个部件，三条主线

DocuSeal 是一个传统的 Rails 单体应用，没有微服务拆分。部署起来是一个容器（或 compose 里的三个），理解起来可以按六个部件走：

| 部件 | 职责 | 代码位置（master 分支） |
|------|------|------|
| Web 界面（Vue 3） | 模板构建器、签署页、管理后台 | `app/javascript/template_builder/`、`app/javascript/submission_form/` |
| Rails 应用 | 页面渲染、管理端与集成 REST API | `app/controllers/`（API 路由在 `namespace :api` 下） |
| Webhook 派发 | Sidekiq 专用队列，按事件推 HTTP 回调 | `app/jobs/send_*_webhook_request_job.rb`、`lib/send_webhook_request.rb` |
| 文件存储 | 签署文档与附件 | `config/storage.yml`（本地磁盘 / S3 / GCS / Azure） |
| 数据库 | 模板、提交、用户、Webhook 配置 | SQLite（默认）/ PostgreSQL / MySQL，由 `DATABASE_URL` 决定 |
| 邮件通知 | 签署邀请、完成回执 | `config/environments/production.rb` 的 SMTP 配置块 |

三条主线贯穿这些部件：**模板**（签什么）、**提交**（谁在签哪一份）、**Webhook**（结果怎么回来）。后面三节各拆一条。

## 主线一：模板——先定义"签什么"

模板是一份 PDF 加一组表单字段。开源版的创建入口是 Web 构建器：把 PDF 拖进去，在页面上拖放字段，所见即所得（WYSIWYG）。

字段类型按 README 的口径是 12 种（Signature、Date、File、Checkbox 等）；对照 `master` 分支的构建器源码（`app/javascript/template_builder/field_type.vue`），默认下拉实际列出 13 种：`text`、`signature`、`initials`、`date`、`number`、`image`、`checkbox`、`multiple`、`file`、`radio`、`select`、`cells`、`stamp`。另有四种类型默认隐藏、按配置开启：`payment`（收款）、`phone`（手机验证）、`verification`（证件核验）、`kba`（知识型身份验证）——后几种与身份验证相关，属于 Pro/云版的能力范围。同一文件里还有 `heading`、`strikeout`、`datenow`（签署日期）三个名字，它们是静态元素或自动填充值，不算填写字段。

除了在界面上画，模板还能从文档生成，三种方式按 README 都列在 Pro 功能里：

| 方式 | 做法 | 出处 |
|------|------|------|
| PDF + 文本标签 | 在 PDF 里写 `{{Field Name;role=Signer1;type=date}}` 形式的标签，上传时解析成字段 | [官方指南](https://www.docuseal.com/guides/use-embedded-text-field-tags-in-the-pdf-to-create-a-fillable-form) |
| DOCX + 变量 | `[[variable_name]]` 定义动态内容变量，`{{signature}}` 定义字段 | [官方指南](https://www.docuseal.com/guides/use-dynamic-content-variables-in-docx-to-create-personalized-documents) |
| HTML API | 用 `<text-field>`、`<signature-field>` 等 11 种自定义标签写 HTML，服务端排版成 PDF | [官方指南](https://www.docuseal.com/guides/create-pdf-document-fillable-form-with-html-api) |

HTML 方式对程序化生成模板最友好：标签支持 `role` 属性绑定签署方、`style` 属性控制字段的位置和尺寸，签名字段还能用 `drawn`（手绘）、`typed`（输入）、`upload`（上传图片）指定录入方式。对应端点是 `POST /templates/html`，请求体里 `external_id` 参数值得注意——传同一个 `external_id` 会更新既有模板而不是新建，适合"模板跟着代码走"的发布流程。

模板支持文件夹（`folder_name`）和共享链接（`shared_link`）组织，克隆与合并各有独立端点。签署完成的 PDF 会嵌入数字签名，DocuSeal 也提供对已签 PDF 的签名验证（README 列出的核心功能，对应源码 `lib/verify_pdf_signature.rb` 与 `/verify_pdf_signature` 路由）。

## 主线二：提交与签署——一次签署请求的生命周期

Template 是静态定义，Submission 是它的一次运行实例。从 API 创建一次提交（`POST /submissions`），核心参数只有两个：

```json
{
  "template_id": 123456,
  "submitters": [
    { "role": "Property Owner", "email": "owner@example.com" },
    { "role": "Renter", "email": "renter@example.com" }
  ]
}
```

`role` 对应模板里字段的 `role` 属性，同一角色可以对应多个字段。签署顺序由 `order` 参数控制，**默认 `preserved`（保序）**：第一方签完，第二方才收到邀请邮件；传 `random` 则同时发给所有人。这个默认值对合同场景是正确的——保序是少数需要显式放开的能力。

每个 submitter（签署方）还有一批可选参数，常用的几个：

- `require_email_2fa` / `require_phone_2fa`：打开签署链接前要求邮箱或短信验证码；
- `completed_redirect_url`：签完跳回业务系统的地址；
- `values`：预填字段值；
- `completed: true`：API 直接代签，用于系统方作为签署角色的自动化；
- `expire_at`：提交整体过期时间。

一次提交的状态变化会同时体现在两个层面。单个签署方视角是 `form.viewed`（打开）→ `form.started`（开始填写）→ `form.completed`（签完）或 `form.declined`（拒签）；整单视角是 `submission.created` → `submission.completed`，中途可能 `submission.expired` 或被归档为 `submission.archived`。这两组状态名同时是 Webhook 的事件名，Web UI 里也有对应的列表页（如 `submissions/archived` 路由）。

## 主线三：Webhook——把结果推回业务系统

Webhook 配置在管理后台维护，每个 URL 记录可以订阅一部分事件。源码里 `WebhookUrl::EVENTS`（`app/models/webhook_url.rb`）定义了全部 11 种：

| 事件 | 触发时机 |
|------|------|
| `form.viewed` | 签署方首次打开表单 |
| `form.started` | 签署方开始填写 |
| `form.completed` | 一方完成签署 |
| `form.declined` | 一方拒签 |
| `submission.created` | 提交创建 |
| `submission.completed` | 全部签署方完成 |
| `submission.expired` | 提交过期 |
| `submission.archived` | 提交归档 |
| `template.created` / `template.updated` / `template.archived` | 模板生命周期 |

新记录默认订阅 `form.viewed`、`form.started`、`form.completed`、`form.declined` 四种。请求是 POST，载荷三个字段：

```json
{
  "event_type": "form.completed",
  "timestamp": "2026-09-30T12:00:00.000+08:00",
  "data": { }
}
```

`data` 的内容随事件而变：`form.*` 事件携带该签署方的序列化结果，`submission.*` 事件携带整单状态。每个请求带两个可识别特征——`User-Agent` 固定为 `DocuSeal.com Webhook`，签名放在 `X-Docuseal-Signature` 头里。

验签算法在 `lib/webhook_urls/signatures.rb`，五十行不到，值得读一遍：密钥以 `whsec_` 前缀开头；签名是 `{时间戳}.{HMAC-SHA256(密钥, "{时间戳}.{请求体}")}`，时间戳参与摘要计算，容忍 ±5 分钟偏差。服务端照抄一遍就能验：

```python
import hashlib
import hmac
import time

def verify_docuseal_signature(secret: str, body: bytes, header: str, tolerance: int = 300) -> bool:
    ts, sig = header.split(".", 1)
    if abs(time.time() - int(ts)) > tolerance:
        return False
    expected = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)
```

两个工程细节影响接入设计。第一，重试机制：投递失败（4xx/5xx）后按 2^n 分钟间隔重试，源码上限 `MAX_ATTEMPTS = 12` 次，官方文档的口径是"生产账户 48 小时内多次重试"——所以接收端要做成幂等的，同一事件的 `event_uuid` 可能到达多次。第二，多租户部署（SaaS，软件即服务）下 Webhook 目标强制 HTTPS 且禁止 localhost，自托管单实例没有这个限制，本地开发可以直接回调解到自己机器上。后台还有发送测试事件的功能（对应 `send_test_webhook_request_job.rb`），接通后先发一条测试再上真流量。

## 一次两方签署的完整流转

把三条主线串起来。场景：房东-租客的租房合同，模板已在 Web 构建器里画好（含双方各自的 `signature` 字段），业务系统要驱动签署并收回已签文件。

**第一步，创建提交。** 业务系统调 API，`order` 用默认保序，房东先签：

```bash
curl -X POST https://your-host/api/submissions \
  -H "X-Auth-Token: API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": 123456,
    "submitters": [
      { "role": "Property Owner", "email": "owner@example.com" },
      { "role": "Renter", "email": "renter@example.com" }
    ]
  }'
```

DocuSeal 给房东发签署邀请邮件。房东打开链接，`form.viewed`、`form.started` 两个 Webhook 先后到达业务系统——到这里可以顺带做"客户已开始签署"的业务提醒。

**第二步，房东签完。** `form.completed` 到达，载荷里是房东这份签署结果的序列化数据。因为默认保序，租客此时才收到邀请。

**第三步，整单完成。** 租客签完后 `form.completed` 与 `submission.completed` 先后到达，验签通过后，业务系统拉取已签文件：

```bash
curl -H "X-Auth-Token: API_KEY" \
  https://your-host/api/submissions/12345/documents
```

这个端点在提交未完成时返回部分签署的文档，完成后返回最终已签版本，一次调用两种语义。整个流程里业务系统只做了两次 API 调用，其余靠 Webhook 驱动——这是 DocuSeal 集成模型的典型形态：调用创建，回调收尾。

## API 总量与接入方式

认证用 `X-Auth-Token` 请求头携带 API 密钥（自托管实现在 `app/controllers/api/api_base_controller.rb`，密钥在管理后台的设置页生成）。云版网关是 `api.docuseal.com`（全球）与 `api.docuseal.eu`（欧洲）；自托管实例接口挂在自己的域名下，源码路由在 `/api/` 命名空间，如 `/api/submissions`。

官方文档列出的端点按三个资源组织，共 22 个：

| 资源 | 端点（路径按官方文档原文） |
|------|------|
| Submissions | `GET /submissions` · `GET /submissions/{id}` · `GET /submissions/{id}/documents` · `POST /submissions` · `POST /submissions/pdf` · `POST /submissions/docx` · `POST /submissions/html` · `PUT /submissions/{id}` · `DELETE /submissions/{id}` |
| Submitters | `GET /submitters` · `GET /submitters/{id}` · `PUT /submitters/{id}` |
| Templates | `GET /templates` · `GET /templates/{id}` · `POST /templates/pdf` · `POST /templates/docx` · `POST /templates/html` · `POST /templates/{id}/clone` · `POST /templates/merge` · `PUT /templates/{id}` · `PUT /templates/{id}/documents` · `DELETE /templates/{id}` |

对照源码路由，自托管版没有 `POST /templates/pdf|docx|html` 三个模板创建端点——与 README 把"API 创建模板"划入 Pro 功能一致。开源版的 API 覆盖提交、签署方、模板管理与文档拉取，创建模板走 Web 构建器。

接入不限于裸 HTTP。官方维护 8 种语言的 SDK（软件开发工具包）和命令行工具：

| 语言 | 安装 |
|------|------|
| JavaScript / TypeScript | `npm install @docuseal/api` |
| Python | `pip install docuseal` |
| Ruby | `gem install docuseal` |
| PHP | `composer require docusealco/docuseal-php` |
| Java | `implementation 'com.docuseal:docuseal-java:+'` |
| C# | `dotnet add package Docuseal` |
| Go | `go get github.com/docusealco/docuseal-go` |
| CLI | `npm install -g docuseal` |

另有 MCP（Model Context Protocol）服务器 `https://mcp.docuseal.com`，`claude mcp add --transport http docuseal https://mcp.docuseal.com/` 即可在 Claude Code 里驱动签署流程。

## 部署：从单容器到带证书的生产组合

评估用一个容器就够：

```bash
docker run --name docuseal -p 3000:3000 -v .:/data docuseal/docuseal
```

容器里 `/data` 目录承载全部状态：默认 SQLite 数据库、自动生成的 `docuseal.env`（内含 `SECRET_KEY_BASE`，权限 0600）、本地附件。挂载它，销毁容器不丢数据。

生产部署用官方 compose 文件，三个服务：

```bash
curl https://raw.githubusercontent.com/docusealco/docuseal/master/docker-compose.yml > docker-compose.yml
sudo HOST=your-domain-name.com docker compose up
```

结构是 `docuseal/docuseal:latest` 应用 + PostgreSQL 18 数据库 + Caddy 反向代理。`HOST` 环境变量同时做两件事：传给 Caddy 签发 Let's Encrypt 证书（`caddy reverse-proxy --from $HOST --to app:3000`），传给应用启用 `FORCE_SSL`（强制 HTTPS 与安全 Cookie）。前提是域名已解析到这台服务器，且 80/443 端口可达。

配置全部走环境变量，以下是源码里实际读取的常用项（`config/environments/production.rb`、`config/storage.yml`、`config/dotenv.rb`）：

| 用途 | 变量 | 说明 |
|------|------|------|
| 数据库 | `DATABASE_URL` | 留空用 SQLite；填 PostgreSQL 或 MySQL 连接串切换 |
| 邮件 | `SMTP_ADDRESS` | 总开关：不设置则整组 SMTP 配置不生效 |
| 邮件 | `SMTP_PORT` / `SMTP_DOMAIN` / `SMTP_USERNAME` / `SMTP_PASSWORD` | 端口默认 587 |
| 邮件 | `SMTP_ENABLE_STARTTLS` | 默认开启，显式传 `false` 关闭 |
| 对象存储 | `S3_ATTACHMENTS_BUCKET` + `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_REGION` | S3 存储；`AWS_REGION` 默认 `us-east-1` |
| 对象存储 | `S3_ENDPOINT` | 设置后走 path-style，可接 MinIO 等兼容存储 |
| 对象存储 | `GCS_CREDENTIALS` / `GCS_PROJECT` / `GCS_BUCKET` | Google Cloud Storage |
| 对象存储 | `AZURE_STORAGE_ACCOUNT_NAME` / `AZURE_STORAGE_ACCESS_KEY` / `AZURE_CONTAINER` | Azure Blob |
| 其他 | `FORCE_SSL`、`WORKDIR`、`RUBY_YJIT_ENABLE` | 强制 HTTPS、数据目录、Ruby YJIT 加速 |

不配置任何存储变量时，附件落在 `{WORKDIR}/attachments` 本地目录。密钥管理有一条捷径：设置 `AWS_SECRET_MANAGER_ID` 后，其余配置可以从 AWS Secrets Manager 拉取，避免敏感项明文进环境变量。

不想自己管服务器，README 提供 4 个平台的一键部署入口，各自指向独立的模板仓库：[Heroku](https://heroku.com/deploy?template=https://github.com/docusealco/docuseal-heroku)、[Railway](https://railway.com/deploy/IGoDnc)、[DigitalOcean](https://cloud.digitalocean.com/apps/new?repo=https://github.com/docusealco/docuseal-digitalocean/tree/master&refcode=421d50f53990)、[Render](https://render.com/deploy?repo=https://github.com/docusealco/docuseal-render)。

## 排查四则

**邮件不发。** 先确认 `SMTP_ADDRESS` 设置了——源码里它是开关，没设置时其余 `SMTP_*` 变量根本不会被读，投递走 Rails 默认配置（本机 25 端口），通常会失败。已设置仍不发，看容器日志里 ActionMailer 的投递记录，再查 STARTTLS：默认开启，个别只收裸 SMTP 的老服务器需要显式传 `SMTP_ENABLE_STARTTLS=false`。

**Webhook 收不到。** 按顺序查三处：该 URL 记录有没有订阅这个事件（默认只订阅 `form.*` 四种，`submission.*` 与 `template.*` 要手动加）；目标地址从容器内可达吗（自托管没有 localhost 限制，但防火墙挡出站会静默失败）；接收端是否返回了 4xx/5xx——返回了就会进入 2^n 分钟间隔的重试，48 小时内最多 12 次，接收端修复后不必手动补发。

**API 返回 401。** 认证头是 `X-Auth-Token`，不是 `Authorization: Bearer`——这是 DocuSeal 与多数 API 习惯不同的地方。云版确认打到 `api.docuseal.com`，自托管确认打到自己的主机名而不是容器名。

**证书签发失败。** Caddy 需要 DNS 已解析到本机且 80/443 从公网可达，两者缺一即失败。用 `dig your-domain-name.com` 和 `nc -zv your-domain 443` 分别验证，再看 compose 输出里 Caddy 的日志。

## 许可、Pro 版与采用边界

许可证是 AGPLv3 加一条 Section 7(b) 附加条款，两条约束分开看。AGPL 的网络条款意味着：改了 DocuSeal 源码并对外提供签署服务，修改部分要开源。附加条款更简单——`LICENSE_ADDITIONAL_TERMS` 只有一句话：交互界面必须保留 DocuSeal 原始署名（"Powered by DocuSeal"一类的标识）。想合法去掉它，路径是购买 Pro 的白标授权，而不是改样式表。

Pro 版能力按 README 清单：公司 Logo 与白标、用户角色、自动催签、短信邀请与身份验证、条件字段与公式、CSV/XLSX 批量发送、SSO/SAML、HTML/PDF/DOCX API 创建模板、嵌入式签署表单与嵌入式表单构建器（React/Vue/Angular/JavaScript SDK）。注意嵌入式 SDK 的仓库是公开的（如 [docusealco/docuseal-react](https://github.com/docusealco/docuseal-react)），代码可见不等于授权可商用。

和 DocuSign 的差异不在签名算法，而在责任与自由的分配：

| 维度 | 自托管 DocuSeal | 商业签署 SaaS |
|------|------|------|
| 数据位置 | 签署文件与个人信息全在自己服务器 | 存在供应商云上 |
| 集成自由 | API、Webhook、SDK 全量开放，无调用计量 | 按套餐限额，深度集成走供应商的生态 |
| 合规责任 | 电子签名的法律效力、留存、审计由你的部署与流程负责 | 供应商提供合规框架与认证背书 |
| 功能广度 | 核心签署流程完整，企业功能在 Pro 墙外 | 合规、身份验证、审批流成套 |
| 成本结构 | 服务器 + 自己的运维时间 | 按量/按席位订阅 |

电子签名的法律效力因国家与文件类型而异（中国《电子签名法》对"可靠电子签名"有专门要求），选择自托管方案前，这一步要按自己的辖区确认，本文不给普适结论。

**采用建议**按三步走。第一步，拿 [demo.docuseal.tech](https://demo.docuseal.tech) 或 `docker run` 单容器验证表单 builder 是否够画你的业务表单——这一步不过，后面不用看。第二步，compose 部署到测试环境，配好 SMTP，跑通一次真实的两方签署和 Webhook 回调，重点验证验签代码与幂等处理。第三步，做集成设计时对照 Pro 清单盘点：需要白标、SSO、批量发送、API 建模板中任何一项，评估 Pro 或云版；一项都不需要，开源版自托管就是终态。反过来的场景也明确：如果签署是低频、内部、对品牌呈现不敏感的流程，先用现成 SaaS 的免费额度可能比维护一套自托管服务更省。

## 维护指引

本文全部数字与机制描述锚定在三类可复查的来源上，更新时按此核对：

1. **仓库元数据**（Stars、版本、语言构成）：GitHub API，`repos/docusealco/docuseal` 与 `/releases`、`/languages` 端点；
2. **代码行为**（字段类型、Webhook 事件与验签、环境变量、路由）：`master` 分支的 `app/javascript/template_builder/field_type.vue`、`app/models/webhook_url.rb`、`lib/webhook_urls/signatures.rb`、`lib/send_webhook_request.rb`、`config/environments/production.rb`、`config/storage.yml`、`config/routes.rb`；
3. **API 契约**（端点、参数、SDK）：[docuseal.com/docs](https://www.docuseal.com/docs) 与各端点的 `.md` 文档页。

DocuSeal 迭代较快（3.x 系列 两周内发了三个版本），涉及端点行为与 Pro 功能边界的段落，引用前先对照上述位置复核；数字变化但结构不变的，只改坐标表即可。
