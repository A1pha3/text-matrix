---
title: "TREK 项目导读：自托管实时协作旅行规划平台"
date: "2026-06-25T21:13:00+08:00"
slug: "mauriceboe-trek-self-hosted-travel-planner-guide"
description: "mauriceboe/TREK 是 6,210 Stars 的自托管实时协作旅行规划平台,基于 NestJS 11 + SQLite。本文拆解其模块矩阵、安全部署与 MCP 接入。"
draft: false
categories: ["技术笔记"]
tags: ["TREK", "自托管", "旅行规划", "NestJS", "MCP"]
---

# TREK 项目导读：自托管实时协作旅行规划平台

> **目标读者**：想找一个能完全掌控数据的旅行规划工具的独立用户 / 小团队；想研究 NestJS + React + SQLite 全栈实时协作架构的工程师；对 MCP（Model Context Protocol）感兴趣的 AI 应用开发者
> **前置知识**：知道 Docker / Docker Compose，能接受 AGPL-3.0 协议，对 OAuth 2.1 / OIDC / WebAuthn 有基本概念
> **预计阅读时间**：14 分钟 | **难度**：⭐⭐

---

## 一、核心判断

`mauriceboe/TREK` 想做的事情比"另一个旅行 app"野心更大——它要做一个**完全自托管、实时协作、内置 AI 接入**的旅行规划平台。截至 2026-06-25，仓库累计 6,210 Stars、590 Forks、AGPL-3.0 协议，最新 Release v3.1.2（2026-06-23，bugfix）。代码量级不小：NestJS 11 后端 + React 19 前端 + WebSocket 实时层 + SQLite 存储 + Docker / Helm 部署支持，是 2024-2026 年典型的"自托管优先 + AI 友好"全栈应用模板。

它的产品边界非常清晰：

- **自托管优先**：所有数据存自己的 SQLite（`./data/travel.db`），不上传第三方
- **实时协作**：WebSocket 同步多用户编辑（行程拖拽、评论、打包清单勾选）
- **AI 原生集成**：内置 MCP（Model Context Protocol）服务器，150+ tools / 30 resources，27 个 OAuth scope 覆盖 13 个权限组
- **移动端 PWA**：可装到 iOS / Android 主屏，离线缓存（Service Worker + Workbox）

相比 Notion Template 类的"用通用工具模拟旅行规划"，TREK 的差异化在于**"专门为旅行场景设计的实时协作 + 真实地图 + 离线 + AI"**。AGPL-3.0 是双刃剑：自托管免费，但"网络服务"形式的修改必须开源——对自用没问题，做商业 SaaS 改版要谨慎。

---

## 二、系统地图：单仓多模块 + WebSocket 实时层

TREK 的代码组织是 NestJS 风格的多模块单体，前端用 Vite + React：

```
┌──────────────────────────────────────────────────────────────────┐
│  L3 前端（React 19 + Vite + TypeScript + Tailwind）              │
│    web/ · 拖拽行程 · 地图 · 预算 · 打包 · Journal · Atlas · 20 语言│
│    Zustand 状态管理 · Leaflet / Mapbox GL · PWA · i18n          │
├──────────────────────────────────────────────────────────────────┤
│  L2 后端（NestJS 11 + Node.js 22）                                │
│    server/ · 模块：trips / places / reservations / costs /      │
│      packing / documents / collab / journal / atlas / MCP /     │
│      auth / admin / notifications                                │
│    TypeORM + better-sqlite3 · JWT + OAuth 2.1 + OIDC + Passkeys│
│    WebSocket（ws）· 实时同步                                      │
├──────────────────────────────────────────────────────────────────┤
│  L1 集成层（可开关 Addons）                                       │
│    Lists / Costs / Documents / Collab / Vacay / Atlas /         │
│    Journey / AirTrail / MCP                                      │
├──────────────────────────────────────────────────────────────────┤
│  L0 基础设施                                                       │
│    SQLite（./data/travel.db）· Uploads（./uploads/）· 备份         │
│    Docker / Docker Compose / Helm chart · Nginx / Caddy 反代      │
└──────────────────────────────────────────────────────────────────┘
```

WebSocket 走 `/ws` 路径，反向代理必须支持 upgrade。状态共享靠 Zustand 集中管理，前后端类型共享走 TS 共享包。

---

## 三、核心能力矩阵：10+ 模块覆盖旅行全周期

`README.md` 给的功能矩阵非常密，按"规划 / 管理 / 协作 / 移动 / AI / 管理"6 组归类：

| 组 | 模块 | 关键能力 |
|---|------|----------|
| 🧭 规划 | Trip planning | 拖拽行程编辑、Leaflet/Mapbox 3D 地图、Places 搜索（Google / OSM）、GPX/KML 导入、Google Maps 列表导入、16 天天气预报（Open-Meteo）、路线优化、分类筛选 |
| 🧳 管理 | Travel management | 预订（航班/酒店/餐厅，PDF 邮件导入用 KDE Itinerary）、费用分摊（Splitwise 式）、打包清单、行李称重、文档附件（≤50MB）、PDF 导出 |
| 👥 协作 | Collaboration | WebSocket 实时同步、多用户角色、邀请链接、OIDC SSO、2FA（TOTP）、Passkeys（WebAuthn）、群聊 / 共享笔记 / 投票 / 打卡 |
| 📱 移动 | Mobile & PWA | iOS / Android 装到主屏、Service Worker 离线缓存（tiles + API + 上传队列）、独立窗口 + 主题状态栏、触摸布局 |
| 🧩 Addons | Addons | Lists / Costs / Documents / Collab / Vacay / Atlas / Journey / AirTrail / MCP（admin 端可关） |
| 🤖 AI | AI / MCP | 内置 MCP Server（OAuth 2.1）· 150+ tools / 30 resources · 27 OAuth scope / 13 权限组 · 预置 prompt（trip-summary / packing-list / budget-overview）|
| ⚙️ 管理 | Admin | 用户管理、邀请、打包模板、类别、addon 开关、API key、备份、GitHub 历史、SMTP / Webhook / ntfy 通知、20 种语言、深色模式 |

这套模块矩阵的广度在自托管项目里算高的——同体量的项目大多只覆盖 2-3 个领域。

---

## 四、技术栈细节：为什么选这一组

`README.md` 列的 tech stack 每一个都有明确理由：

- **Node.js 22 + NestJS 11**：NestJS 的 module / controller / service / guard 分层让"多模块 + 多权限 + 多集成"的代码组织可控
- **SQLite（better-sqlite3）**：单文件、零运维、内置加密（TREK 默认对 API key / MFA / SMTP 等敏感字段用 `ENCRYPTION_KEY` 做 at-rest 加密）。相比 Postgres，对自托管用户友好——不需要单独跑数据库进程
- **React 19 + Vite + TypeScript + Tailwind**：标准 2024-2026 主流前端栈
- **Leaflet / Mapbox GL**：开源优先（Leaflet）+ 高端可选（Mapbox 3D 建筑、地形）
- **Zustand**：轻量级 state store，比 Redux 适合中小项目
- **ws（WebSocket）**：直接用 Node.js 的 `ws` 库，不上 Socket.io 以减少依赖
- **WebAuthn + TOTP + OIDC + JWT**：认证四件套，覆盖企业 SSO 到个人 2FA
- **MCP（Model Context Protocol）**：Anthropic 推的"AI 工具调用"协议，TREK 既是 MCP server 也能接 AirTrail 这类 MCP client

这种选型在 2026 年看非常"工程合理"——没有为用而用 Rust / Go / GraphQL，每个选择都对应一个具体需求。

---

## 五、30 秒启动 + 5 种部署方式

**最快路径（一行）**

```bash
ENCRYPTION_KEY=$(openssl rand -hex 32) docker run -d -p 3000:3000 \
  -e ENCRYPTION_KEY=$ENCRYPTION_KEY \
  -v ./data:/app/data -v ./uploads:/app/uploads mauriceboe/trek
```

第一次启动会 seed 管理员账号——如果设了 `ADMIN_EMAIL` / `ADMIN_PASSWORD` 就用那对，否则随机生成并打印到容器 log（`docker logs trek`）。开浏览器 `http://localhost:3000` 即可。

**生产级 Docker Compose**

`README.md` 给的完整 compose 模板值得一看：

```yaml
services:
  app:
    image: mauriceboe/trek:latest
    read_only: true
    security_opt: [no-new-privileges:true]
    cap_drop: [ALL]
    cap_add: [CHOWN, SETUID, SETGID]
    tmpfs: [/tmp:noexec,nosuid,size=64m]
    environment:
      - ENCRYPTION_KEY=${ENCRYPTION_KEY:-}
      - TZ=${TZ:-UTC}
      - APP_URL=${APP_URL:-}    # OIDC + 邮件链接必填
      # - FORCE_HTTPS=true       # 仅在 TLS 终结反代后
      # - TRUST_PROXY=1
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

安全默认做得很到位：`read_only` 根文件系统 + `cap_drop ALL` + `tmpfs /tmp` + healthcheck。**注意一个坑**：`/app` 路径**不能挂载卷**，否则会覆盖镜像里的应用代码导致启动失败（README 有 `[!IMPORTANT]` 警告）。

**Helm / Kubernetes**

```bash
helm repo add trek https://mauriceboe.github.io/TREK
helm repo update
helm install trek trek/trek
```

**PWA 安装**

HTTPS 下浏览器 → iOS Share → Add to Home Screen / Android Menu → Install app。装好后独立窗口、有图标、有 splash、状态栏主题化。

**反向代理**

`README.md` 同时给 Nginx（含 WebSocket upgrade 完整配置）和 Caddy（Caddyfile 2 行自动处理 TLS + WS）两种示例。**WebSocket 路径 `/ws` 一定要支持 upgrade**（Nginx 里 `proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade";`），否则实时同步直接挂掉。

---

## 六、MCP 集成：把整个 TREK 暴露给 AI

TREK 的 MCP server 是它的"AI 入口"，设计得很认真：

- **150+ tools / 30 resources**：覆盖 trips / days / places / reservations / packing / costs 等所有模块
- **27 OAuth scope × 13 权限组**：把权限粒度做到"操作 × 模块"级别，可以给 AI 助手只授权"读 + 写 packing list"而不给"删 trip"
- **OAuth 2.1 认证**：标准协议，Claude / Cursor / Continue 等 MCP client 都能直接连
- **预置 prompt**：`trip-summary` / `packing-list` / `budget-overview` 等开箱即用的提示词
- **速率限制**：`MCP_RATE_LIMIT`（默认 300 / 用户 / 分钟）、`MCP_MAX_SESSION_PER_USER`（默认 20 并发）
- **Addon-aware**：MCP 工具列表会根据管理员开启的 addon 动态调整（关掉 Atlas 就看不到 atlas_* 工具）

从工程角度看，TREK 的 MCP 集成做了正确的事：**不把 AI 当成"特殊功能"，而是当成"另一种客户端"**——和其他 client 一样走 OAuth 2.1 + scope 控制 + 速率限制。

---

## 七、数据、加密与备份

- **数据库**：`./data/travel.db`（SQLite 单文件）
- **上传文件**：`./uploads/`（每文件 ≤ 50MB）
- **日志**：`./data/logs/trek.log`（自动轮转）
- **At-rest 加密**：`ENCRYPTION_KEY` 加密 API key / MFA secret / SMTP 凭据 / OIDC 凭据。README 提示升级到带 ENCRYPTION_KEY 的版本后，可用 `docker exec -it trek node --import tsx scripts/migrate-encryption.ts` 做密钥轮换（脚本会先做时间戳 DB 备份）
- **自动备份**：admin panel 可配置定时备份 + 保留策略
- **手动恢复**：admin panel 直接上传备份文件恢复

如果 `ENCRYPTION_KEY` 没设，老版本会回退到 `data/.jwt_secret` 派生密钥，新安装则自动生成密钥——README 明确建议新部署**主动生成** `openssl rand -hex 32`。

---

## 八、采用顺序与适用边界

**适合采用的场景**：

- 一群朋友 / 一个小团队计划一次复杂旅行（多人协作 + 地图 + 预算 + 打包清单全在一个地方）
- 数据敏感场景（不希望旅行数据上 Notion / Google Docs / 第三方 SaaS）
- 已经在跑 Immich / Nextcloud 等自托管服务，想加一个"旅行专用"工具
- 已经在用 Claude / Cursor，想把自己的旅行数据通过 MCP 暴露给 AI 助手自动整理
- 想研究 NestJS + React + WebSocket + SQLite 完整自托管模板的工程师

**谨慎采用的场景**：

- 1-2 个人计划一次简单旅行：Google Maps / Apple Notes 可能更轻
- 需要"航空公司值机 / 酒店会员积分"等深度集成：TREK 不做这些，定位是规划而非出行全流程
- 不能接受 AGPL-3.0 的组织：自用免费，但如果你做"修改后向第三方提供网络服务"，整个修改必须开源——企业法务会卡
- 没有 HTTPS / 反代运维能力：WebSocket 路径需要 proxy 支持 upgrade，TLS 终结 + 健康检查都需要自己配

**不适用的场景**：

- 找"现成旅游攻略 + AI 推荐目的地"：TREK 是**规划工具**不是**推荐引擎**
- 单向"上传照片 + 自动成册"：Journey 模块能做但 Immich / Google Photos 更专注
- 需要和航空公司 API / 酒店 PMS 系统直连：TREK 不做集成，靠用户上传 PDF 邮件用 KDE Itinerary 解析

---

## 九、总结：自托管优先 + AI 原生 + 实时协作的三角

TREK 的真正信号是：**自托管工具也能追上前沿（实时协作 / AI 集成 / PWA / Passkey）**。很多自托管项目到 2026 年还停留在"单用户 / 无实时 / 无 AI"的阶段，TREK 用 NestJS + React + SQLite 这个相对保守的栈，把"自托管优先 + 实时协作 + MCP 集成"三角都跑通了。这背后是项目维护者对"全栈工程合理选型"的判断力——不为了赶时髦上 Rust / GraphQL / 微服务，而是让每个技术选择都对应到具体需求。

如果你想**自托管旅行数据**——直接 `docker run` 跑起来；如果你想**给 AI 助手暴露自己的旅行数据**——把 MCP scope 配好；如果你想**研究一个完整的现代自托管全栈项目**——TREK 的代码组织、模块拆分、部署模板、安全默认值都是值得读的范例。AGPL-3.0 是这套价值的代价，但对个人 / 内部使用完全够用。
