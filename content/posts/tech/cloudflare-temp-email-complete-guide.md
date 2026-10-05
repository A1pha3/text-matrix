---
title: "Cloudflare 临时邮箱部署指南：零成本自建收发件服务"
date: "2026-04-12T02:31:39+08:00"
lastmod: "2026-10-02T00:00:00+08:00"
slug: cloudflare-temp-email-complete-guide
github_repo: "dreamhunter2333/cloudflare_temp_email"
source_key: "gh:dreamhunter2333/cloudflare_temp_email"
description: "cloudflare_temp_email 部署指南：基于 Workers + D1 + Email Routing 的零成本临时邮箱，覆盖部署前提、三条部署路径、AI 验证码识别与安全配置。"
draft: false
categories: ["技术笔记"]
tags: ["Cloudflare", "TypeScript", "自托管", "开源项目"]
---

# Cloudflare 临时邮箱部署指南：零成本自建收发件服务

## 先给判断

[dreamhunter2333/cloudflare_temp_email](https://github.com/dreamhunter2333/cloudflare_temp_email) 是一个跑在 Cloudflare 免费套餐上的临时邮箱系统：收件靠 Email Routing 转发进 Worker，邮件存 D1（SQLite），前端是 Vue 3 单页应用，验证码提取默认在 Worker 内用本地规则完成，一分钱不花也能跑起来。项目 2023 年 8 月建仓，截至 2026-10-02 已有 11,893 stars、694 次提交、33 位贡献者，最新版本 v1.12.0（2026-09-13），仍在高频迭代。

它适合的场景：注册各类服务时要一堆一次性邮箱、想自己持有域名收发件、或者给 AI agent 配一个能收验证码的信箱。不适合的场景同样明确——你必须有一个托管在 Cloudflare 的域名（这是收件的硬前提），整套系统绑定 Workers/D1/KV/R2，迁去别的平台等于重写；另外项目的定位是"轻量收发与验证码场景"，做正式的企业邮箱或邮件营销，应该看 [listmonk](/posts/tech/listmonk-self-hosted-email-newsletter-platform-guide/) 这类专业系统。

读源码时把它拆成五个部件最省事：`worker/` 是 TypeScript + Hono 写的后端；`frontend/` 是 Vue 3 界面，部署到 Pages；`db/` 是 D1 的建表与迁移 SQL；`mail-parser-wasm/` 是 Rust 编译的 WASM 解析器，专门对付 Node 解析失败的怪邮件；`smtp_proxy_server/` 是一个独立的 Python 服务，给邮件客户端提供 SMTP 发信和 IMAP 收信入口。这五件里只有最后一件需要自己找台机器跑，其余全部落在 Cloudflare 上。

## 项目坐标（2026-10-02 核对）

| 字段 | 值 |
|------|------|
| Stars / Forks | 11,893 / 7,961 |
| 贡献者 / 提交数 | 33 / 694 |
| 最新 release | v1.12.0（2026-09-13）；main 分支已进入 v1.13.0 开发 |
| 许可证 | MIT |
| 语言占比（字节） | TypeScript 66%、Vue 25%、JavaScript 与 Python 各 4%、Rust 0.3% |
| 在线演示 | [mail.awsl.uk](https://mail.awsl.uk/)（作者的常驻实例） |
| 文档站 | [temp-mail-docs.awsl.uk](https://temp-mail-docs.awsl.uk/)（VitePress，中英日三语 README） |

语言占比能说明一件事：Rust 代码只有几千字节，因为 WASM 解析器以 npm 包（`mail-parser-wasm`）形式发布，仓库里是壳与构建配置。真正的大头是 Worker 后端和 Vue 前端两块 TypeScript。

## 部署前提：域名和 Email Routing

这是全文唯一一处"没做就全盘不通"的前提，官方文档专门用一篇[快速开始](https://temp-mail-docs.awsl.uk/zh/guide/quick-start)来强调：

1. 准备一个域名（一级域名或子域名均可），DNS 托管在 Cloudflare；
2. 在该域名上启用 Email Routing，完成电子邮件 DNS 记录下发；
3. Worker 部署完成后，把 Email Routing 的 **Catch-all 规则绑定到这个 Worker**——邮件就是从这里进系统的。

三步缺任何一步，邮箱能创建但永远收不到信。另外 `*.workers.dev` 默认域名在中国大陆无法访问，正式使用前先在 `wrangler.toml` 里配好自定义域名。

## 三条部署路径

官方提供三种方式，按动手成本从低到高：

**一键部署**：README 的 Deploy to Cloudflare 按钮走 `deploy.workers.cloudflare.com`，适合先跑通看看，之后仍要自己补配置。

**GitHub Actions**：fork 仓库后在 Actions 页启用 `Deploy Backend` / `Deploy Frontend` workflow，配好 `CLOUDFLARE_ACCOUNT_ID`、`CLOUDFLARE_API_TOKEN` 两个公共 secrets，再把整份 `wrangler.toml` 填进 `BACKEND_TOML`、前端环境填进 `FRONTEND_ENV`，手动 Run workflow 即可。升级时同步 fork 再跑一次，也支持定时自动更新。

**命令行（下面的主线）**：完全可控，出问题最好排查。

### 用 CLI 部署后端

```bash
npm install wrangler -g
git clone https://github.com/dreamhunter2333/cloudflare_temp_email
cd cloudflare_temp_email/worker
pnpm install
cp wrangler.toml.template wrangler.toml
```

编辑 `wrangler.toml`，最小可跑配置是这几项（完整变量见[官方 worker 变量说明](https://temp-mail-docs.awsl.uk/zh/guide/worker-vars)）：

```toml
name = "cloudflare_temp_email"
main = "src/worker.ts"
compatibility_date = "2025-04-01"
compatibility_flags = [ "nodejs_compat" ]
keep_vars = true

[vars]
PREFIX = "tmp"
DOMAINS = ["mail.example.com"]        # 必须是已启用 Email Routing 的域名
JWT_SECRET = "openssl-rand-hex-32-的输出"  # 登录鉴权签名密钥
ENABLE_USER_CREATE_EMAIL = true
ENABLE_USER_DELETE_EMAIL = true
# ADMIN_PASSWORDS = ["你的管理密码"]    # 不配置则无法进入 admin 控制台

[[d1_databases]]
binding = "DB"                        # 绑定名必须是 DB
database_name = "your-d1-name"
database_id = "xxxxxxxx"
```

`DATABASE_URL` 之类的东西不存在——数据库连接全靠这个 `[[d1_databases]]` 绑定。需要注册用户邮箱验证或 Telegram Bot 时，再补一个 KV 命名空间绑定（`binding = "KV"`）；想用官方限流就加 `[[unsafe.bindings]]` 的 ratelimit 配置（默认示例是 `/api/new_address` 每分钟 10 次）。

部署与验证：

```bash
pnpm run deploy
# 首次部署会提示创建项目，production 分支填 production
```

打开 Worker 的 URL，显示 `OK`、`/health_check` 也返回 `OK`，后端就通了。

### 部署前端：两种形态选一种

**前后端分离**（各一个域名/子域名）：在 `frontend/` 复制 `.env.example` 为 `.env.prod`，把 `VITE_API_BASE` 指向后端地址，然后 `pnpm build` + `pnpm run deploy` 部署到 Pages。注意 Pages 是单页应用，如果在控制台手动上传，"未找到处理"必须选 **SPA 模式**，否则刷新或直接访问 `/admin` 会 404；用 `wrangler pages deploy` 则自动处理。

**单 Worker 带前端**（一个域名搞定）：先在 `frontend/` 跑 `pnpm build:pages`，再在 `wrangler.toml` 里加：

```toml
[assets]
directory = "../frontend/dist/"
binding = "ASSETS"
run_worker_first = true
```

还有第三种中间形态：`pages/` 目录里的 Pages Functions 可以把前端请求同域转发给 Worker，响应更快，配置见[官方文档](https://temp-mail-docs.awsl.uk/zh/guide/cli/pages)。

### 数据库初始化与升级

admin 控制台的"快速设置 → 数据库"页面可以一键初始化和迁移；CLI 侧对应 `admin/db_initialize` 与 `admin/db_migration` 两个接口。升级版本时先看 [CHANGELOG](https://github.com/dreamhunter2333/cloudflare_temp_email/blob/main/CHANGELOG.md)，凡标注 Breaking Changes 的版本（例如 v1.7.0 改了发信通道语义）必须执行数据库 SQL 或补配置，其余功能更新按需开启。

## 核心配置：变量、后台设置与 secrets 各管一摊

这个项目的配置分布在四个地方，新用户最容易在这里迷路：

| 位置 | 放什么 | 例子 |
|------|--------|------|
| `wrangler.toml` 的 `[vars]` | 部署期静态变量 | `DOMAINS`、`JWT_SECRET`、`PASSWORDS`（站点私有密码） |
| wrangler secrets | 敏感令牌 | `TELEGRAM_BOT_TOKEN`（`wrangler secret put` 写入） |
| admin 控制台（存 D1） | 运行时可调的策略 | 黑名单、自动清理规则、OAuth2、AI 提取白名单 |
| 绑定（bindings） | 云资源 | D1、KV、R2/S3、Workers AI、ratelimit |

这个分层解释了为什么有的开关在配置文件里、有的在后台页面上：需要在运行中调整的（比如临时拉黑一个前缀）进了数据库设置，改了要重新部署的（比如域名列表）留在 `[vars]`。

几个常用的安全开关：`PASSWORDS` 让整个站点变成"凭密码进入"的私人实例；`CF_TURNSTILE_SITE_KEY`/`CF_TURNSTILE_SECRET_KEY` 接 Cloudflare 人机验证，配 `ENABLE_GLOBAL_TURNSTILE_CHECK` 后所有登录表单都要过验证；v1.12.0 新增的 `ADMIN_API_IP_WHITELIST` 把全部 `/admin/*` 接口限制到指定来源 IP；v1.6.0 起后台的 IP 白名单"严格模式"则反过来，只放表白名单 IP 调用创建邮箱、发信这类被限流保护的接口。

## 邮件解析与验证码提取

**Rust WASM 解析**是收件链路的底线能力：`mail-parser-wasm` 以 WASM 形式跑在 Worker 里，官方说法是 Node 解析模块失败的邮件它也能解析。默认部署用 Worker 内置解析即可，追求更强解析能力时可以开启 `BACKEND_USE_MAIL_WASM_PARSER` 或参考文档单独配 wasm 解析 Worker。

**验证码提取**在 v1.13.0 起分成两种模式，由 `AI_EXTRACT_MODE` 显式选择：

| 模式 | 提取内容 | 邮件内容去向 | 依赖 |
|------|----------|--------------|------|
| `local`（默认） | 仅验证码 | 不出 Worker，内置规则识别 | 无 |
| `ai` | 验证码、认证链接、服务链接、订阅管理链接等 | 发送到你账号下的 Workers AI | `[ai]` 绑定 |

`local` 模式即使配了 AI 绑定也不会调 AI，隐私敏感的部署可以放心开总开关 `ENABLE_AI_EMAIL_EXTRACT`。`ai` 模式的默认模型是 `@cf/meta/llama-3.1-8b-instruct-fast`（支持 JSON Mode；更便宜的 `fp8-fast` 变体不在 JSON Mode 支持列表，别选），内容超过 4000 字符会截断。要注意 Cloudflare 已于 2026-05-30 弃用旧模型 `@cf/meta/llama-3.1-8b-instruct`——早期教程里写的 `@cf/meta/llama-3-8b-instruct` 更是早已过时，照抄会直接跑不通。成本敏感时，可在 admin 的"AI 提取设置"页配地址白名单（支持 `*@example.com` 这类通配符），白名单外的地址自动回退本地规则。

本地规则本身比想象中能干：支持中英日韩加俄西葡法德意等十余种语言的关键词写法，能识别 `123456 是您的验证码`、`G-123456`、全角数字、分隔符验证码，并主动排除年份、电话号码、订单号这类干扰项。

## 收发件的三条路

**发件**按优先级有三种通道，v1.7.0 起官方推荐第一种：

1. **Cloudflare `send_email` binding**——已启用 Email Routing 的域名无需任何第三方配置即可发信，Workers Paid 套餐每月含 3000 封，超出 $0.35/1000 封；
2. **Resend**——配 API key 走它的 API 或 SMTP；
3. **SMTP**——通过下面的代理服务接任意 SMTP 服务商，支持 DKIM。

发信默认有额度控制（send balance），`DEFAULT_SEND_BALANCE` 大于 0 时新地址自动获得额度，否则需要用户申请或 admin 授予。

**IMAP 收信**不是配置出来的，而是靠一个独立的 Python 服务 `smtp_proxy_server/`：它把 Worker 的 HTTP API 翻译成标准 SMTP（端口 8025）和 IMAP（端口 11143），让 Thunderbird 这类邮件客户端能直接连。Docker 一行起来：

```bash
cd smtp_proxy_server/
docker-compose up -d
# 镜像 ghcr.io/dreamhunter2333/cloudflare_temp_email/smtp_proxy_server:latest
# 环境变量 proxy_url 指向你的 Worker 地址
```

它的 `.env` 配置项很少：`proxy_url`（默认 `http://localhost:8787`）、两个端口、可选的 STARTTLS 证书路径。IMAP 的已读标记持久化在本地 SQLite（`imap_flag_db_path`），容器记得挂载 `data/` 目录，否则客户端重连后已读状态会丢——这是 v1.10.0 专门修过的问题。

## 用户系统与安全模型

匿名用户开箱即用：访问前端、创建地址、拿到一个地址级 JWT（`POST /api/new_address` 直接返回 `{ address, jwt, address_id }`），凭证存浏览器 localStorage，之后所有 `/api/*` 请求走 `Authorization: Bearer <jwt>`。在这个之上还有一层完整的注册用户体系：

- **注册登录**：绑定邮箱地址后可管理多个信箱，注册验证码走 KV 发信；
- **地址密码**（`ENABLE_ADDRESS_PASSWORD`）：每个地址可生成独立密码，支持密码登录；
- **OAuth2**：GitHub、Authentik 等第三方登录，在 admin 后台的 OAuth2 设置页配置（不在配置文件里）；GitHub 私密邮箱场景官方文档给了 `user:email` scope 的完整配置；
- **Passkey**：WebAuthn 无密码登录，注册用户可用，无需开关变量。

接口鉴权分四种凭证，别混用：地址 JWT（`Authorization: Bearer`）、用户 JWT（`x-user-token`）、管理密码（`x-admin-auth`）、站点密码（`x-custom-auth`）。地址 JWT 和用户 JWT 是两套体系，拿用户 JWT 调地址接口只会得到 401。

## 通知与集成

**Telegram Bot** 是最常用的推送面：新邮件实时推送、`/mails` 看历史邮件，还能直接创建地址。命令共九个：`/start`、`/new`、`/address`、`/bind`、`/unbind`、`/delete`、`/mails`、`/cleaninvalidaddress`、`/lang`（最后一个需开 `TG_ALLOW_USER_LANG`）。每用户地址数默认上限 5（`TG_MAX_ADDRESS`），Bot token 用 `wrangler secret put TELEGRAM_BOT_TOKEN` 写入，另外需要 KV 绑定。v1.12.0 还支持把前端打包成 Telegram Mini App。

**Webhook** 走 KV 存配置，总开关 `ENABLE_WEBHOOK`：admin 可配全局 webhook，也可开放给单个地址自配。请求体是模板变量填充的 JSON，除了 `${from}`、`${to}`、`${subject}`、`${url}` 这些基础占位符，v1.9.0 起还能用 `aiExtractType`、`aiExtractResult` 等占位符把验证码提取结果一并推走。官方用 [message-pusher](https://github.com/songquanpeng/message-pusher) 做了完整示例。

**AI agent 接入**是 v1.8.0 起的显式卖点：仓库内置 `cf-temp-mail-agent-mail` skill（`npx degit dreamhunter2333/cloudflare_temp_email/skills/cf-temp-mail-agent-mail` 安装），agent 凭用户提供的地址 JWT + API 地址，调 `/api/parsed_mails`、`/api/parsed_mail/:id` 这两个服务端解析接口就能读信、轮询验证码，不需要自己带 MIME 解析库。创建地址涉及 Turnstile 人机验证，这步仍由人在前端完成——分工就是"人建信箱，agent 收信"。

**兑换码**（v1.12.0，`ENABLE_REDEEM_CODE`）面向"站长发码、用户兑换"的运营场景，可兑换角色、发信额度和专属邮箱，admin 端支持批量生成与导出。

## 版本演进速览（给读过旧教程的读者）

2026 年 4 月以来的七个版本，值得单独点名的变化：

- **v1.7.0（2026-04）**：唯一一个 Breaking Change——`SEND_MAIL` binding 从"仅兼容路径"变为常规兜底发信通道，升级前确认发信行为符合预期；
- **v1.8.0（2026-04）**：前端 6 国语言（zh/en/es/pt-BR/ja/de，默认中文）；新增服务端解析邮件 API 与内置 agent skill；
- **v1.9.0（2026-06）**：无 Workers AI 绑定时验证码提取自动回退内置正则；默认模型切到 `llama-3.1-8b-instruct-fast`；
- **v1.10.0（2026-07）**：邮件外部图片白名单加载（DOMPurify 消毒，可整体关闭）；SPF/DKIM/DMARC 垃圾邮件判定按 RFC 修正；IMAP 已读状态持久化；
- **v1.11.0（2026-08）**：清理任务分批执行（`CLEANUP_BATCH_SIZE`，默认 3000、上限 5000），大幅降低 D1 写入量；
- **v1.12.0（2026-09）**：兑换码、邮件已读/未读状态、`ADMIN_API_IP_WHITELIST`、用户中心发件箱；
- **v1.13.0（main，未发版）**：`AI_EXTRACT_MODE` 显式分 local/ai 两档，默认本地规则——从旧版升级且依赖 AI 识别的部署，必须手动设 `AI_EXTRACT_MODE = "ai"`。

清理策略本身在 admin 后台配置（自动清理规则 + cron 触发器，`wrangler.toml` 里 `[triggers] crons = ["0 0 * * *"]` 一行启用），没有 `CLEANUP_INTERVAL_HOURS` 这类环境变量。

## 常见问题

**创建地址成功但收不到邮件？** 按顺序查三处：域名是否已在 Cloudflare 启用 Email Routing 并下发 DNS 记录；Catch-all 是否绑到了这个 Worker；用的随机子域名地址的话，基础域名 DNS 是否给 `*` 子域配了通配 MX——Email Routing 的子域不继承父域配置，这是官方文档反复强调的坑。

**前端报 Network Error？** 多半是 Cloudflare 安全挑战拦截了 API 请求，或者 `VITE_API_BASE` 配置有误（末尾不要带 `/`）。`worker.dev` 域名在大陆不可访问，先换自定义域名再排查。

**Pages 刷新 404？** 手动上传时没选 SPA 模式，改设置或改用 `wrangler pages deploy`。

**免费额度到底够不够？** Workers 免费档每天 10 万次请求、D1 免费 5 GB 存储、R2 免费 10 GB，个人自用绰绰有余；公开服务或高流量场景按 Cloudflare 牌价评估，收发高峰主要吃 Workers 请求数和 D1 容量（admin 数据库页可直观看到容量占比）。

**想迁移出 Cloudflare？** 收件链路依赖 Email Routing，数据库是 D1，发信推荐通道是 `send_email` binding——三者都是 Cloudflare 专属服务。迁移等于换一套技术栈重写，选型时就该想清楚。

## 上手顺序建议

第一次部署按这个顺序走，每步都有明确的验收点：域名开 Email Routing → CLI 部署后端（`/health_check` 返回 OK）→ 部署前端（能创建地址、能收到测试邮件）→ 配 `ADMIN_PASSWORDS` 进 admin 后台（初始化数据库、按需开清理和 Turnstile）→ 配 Telegram Bot 或 Webhook 做推送。跑通之后再考虑发信（binding 或 Resend）、IMAP 代理、AI 提取模式这些增量配置。

---

## 资源与口径说明

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/dreamhunter2333/cloudflare_temp_email |
| 部署文档（中文） | https://temp-mail-docs.awsl.uk/zh/guide/quick-start |
| 在线演示 | https://mail.awsl.uk/ |
| Telegram 社区 | https://t.me/cloudflare_temp_email |
| 站内相关 | [listmonk：自托管邮件营销系统](/posts/tech/listmonk-self-hosted-email-newsletter-platform-guide/) · [karakeep：自托管书签库](/posts/tech/karakeep-self-hosted-bookmark-ai-tag-guide/) |

本文数据核对于 2026-10-02：GitHub API 读数（stars/forks/提交/贡献者）、v1.12.0 release、main 分支源码（worker 路由、`wrangler.toml.template`、CHANGELOG、内置 skill 与 VitePress 文档）逐项比对。项目迭代很快，配置类细节以官方文档站的[变量说明](https://temp-mail-docs.awsl.uk/zh/guide/worker-vars)为最新口径；Cloudflare 免费额度为官方牌价，以 Cloudflare 文档为准。项目仅供学习和个人用途，请遵守当地法律，勿用于违法行为（README 原文警告）。
