---
title: "Securo：自托管开源个人财务管理器，让记账数据彻底离开第三方云"
date: "2026-08-28T03:33:00+08:00"
slug: "securo-self-hosted-open-source-finance-manager"
github_repo: "securo-finance/securo"
source_key: "gh:securo-finance/securo"
description: "解读开源项目 Securo：隐私优先的自托管个人财务管理器，Docker 一键部署，多账户、预算、净资产报表、OFX/QIF/CAMT/CSV 导入、自动分类规则引擎，可选银行同步（Pluggy / Enable Banking / SimpleFIN）、OIDC 单点登录、Passkey 登录与自托管 AI Agent，AGPL-3.0 协议。"
draft: false
categories: ["技术笔记"]
tags: ["自托管", "个人财务", "开源", "Docker", "隐私"]
---

# Securo：自托管开源个人财务管理器，让记账数据彻底离开第三方云

> **阅读时间**：约 12 分钟
>
> **适用读者**：想摆脱商业记账 App 数据收割的个人用户；在寻找可自托管家庭财务管理方案的自托管爱好者
>
> **前置知识**：会用 Docker 或 Podman；了解基本的反代与 HTTPS 概念即可

## 为什么值得关注

商业记账 App 的商业模式决定了它必须拿走你的数据：账户、消费、习惯，全都在别人的服务器上转一圈。Securo 的口号很直接——**"Finance apps want your data. This one doesn't."**（记账应用想要你的数据，这个不要。）

[Securo](https://github.com/securo-finance/securo) 是一个开源（AGPL-3.0）、自托管、隐私优先的个人财务管理器，核心能力：

- **多账户管理**，带滚动余额（running balance）
- **交易管理**：搜索、筛选、CSV 导出
- **文件导入**：OFX、QIF、CAMT、CSV 四种主流账单格式
- **自动分类规则引擎**：定义规则后交易自动归类
- **周期交易与预算**、**目标与储蓄进度**、**资产管理与估值追踪**
- **报表**：净资产（Net Worth）、收支对比，附分类迷你图
- **可选银行同步**：巴西 Pluggy、欧洲约 2500 家 PSD2 银行（Enable Banking）、美国及国际银行（SimpleFIN），且协议可扩展
- **多用户 + 管理面板**、TOTP 两步验证、OIDC 单点登录、Passkey 登录
- **可选 AI Agent**：自托管 LLM 对话 + MCP 工具调用 + 每个独立的 RAG 知识库

截至本文写作，项目约 **2.4k Stars**、305 Forks，主要语言为 Python（后端）+ 前端 SPA（仓库内 `backend/` 与 `frontend/` 分离），最新版本 **v0.14.5**（2026-08-27 发布），最新提交在同一天——维护节奏相当密集，从 v0.14.3 到 v0.14.5 在 8 天内连发三个版本。

## 十秒上手：一条命令跑起来

Linux / macOS 下官方提供安装脚本（依赖 Docker 或 Podman，两者都没有时脚本会自动装 Docker）：

```bash
curl -fsSL https://usesecuro.com/install.sh | bash
```

Windows 用户先装 Docker Desktop，然后：

```bash
git clone https://github.com/securo-finance/securo.git && cd securo
docker compose up --build
```

打开 `http://localhost:3000`，创建账号，完成。没有注册引导流程、没有云账号绑定——因为数据从头到尾只存在你自己的机器上。

仓库同时提供 `docker-compose.prod.yml` 与 `charts/`（Kubernetes Helm Chart），生产部署和 K8s 场景都有现成路径；Artifact Hub 上可查其 Chart 包。官方还提供在线 Demo（demo.usesecuro.com）供试用。

## 银行同步：三种接入模式覆盖三大市场

银行同步是记账工具最硬核的需求，Securo 用"Provider 插件"方式实现：凭据写进 `.env`，重启容器后对应 Provider 自动注册，互不干扰。

**Pluggy（巴西银行）**：在 pluggy.ai 注册拿到 Client ID / Secret 填入即可。

**Enable Banking（欧洲 PSD2）**：覆盖约 2500 家欧洲银行。需要在 enablebanking.com 创建 Production 应用并下载 PEM 私钥，放到 `./secrets/` 目录（已 gitignore）。注意两点：回调 URI 必须与 EB 后台登记的完全一致；生产环境强制 HTTPS，本地开发得靠 ngrok/cloudflared 隧道或用 EB sandbox。另外 EB 免费档有限制——想导入的账户要先在 EB 门户里预关联，否则连接返回空账户列表（Securo 会在界面上给出带门户链接的提示条，而不是静默失败）。

**SimpleFIN（美国与国际）**：这是一个只读开放协议，**不需要 API key**——每条连接用 SimpleFIN Bridge 发放的一次性 Setup Token 携带自己的凭据。开发者页面有免费 demo token，不接真银行也能试。只开一个开关：

```
SIMPLEFIN_ENABLED=true
SIMPLEFIN_API_URL=https://beta-bridge.simplefin.org   # sandbox；真实银行用 bridge.simplefin.org
```

这套设计对国内用户的启示在于：即使你的银行不在支持列表里，OFX/QIF/CAMT/CSV 文件导入 + 自动分类规则引擎仍然构成完整的离线工作流——银行同步是锦上添花，不是生存前提。

## 登录体系：本地密码、OIDC、Passkey 三轨并行

Securo 的认证设计细节比大多数自托管项目考究。

**Passkey 默认开启**，支持 Touch ID / Face ID / Windows Hello / 安全钥匙，无需配置。但 WebAuthn 标准本身有两条铁律（任何设置都绕不开）：

1. IP 地址永远无效——`http://192.168.1.10:3000` 注册不了 passkey
2. 明文 HTTP 永远无效，`localhost` 例外

所以要么在 `http://localhost:3000` 上用，要么把 Securo 挂到域名 + HTTPS 反代后面，并把 `FRONTEND_URL` 指向该域名（顺带解决 CORS 和 OAuth 回调）。需要把 passkey 钉死到单一域名时再设 `WEBAUTHN_RP_ID`。对不可用地址，UI 会给出解释而不是静默失败——这个细节值得所有自托管项目学。

**OIDC 单点登录**支持 Authentik、Pocket ID 等标准 Provider。它有一个防御性设计：开启 `LOCAL_AUTH_ENABLED=false`（纯 SSO 模式）的前提是 OIDC 三项配置齐全，否则启动直接报验证错误，避免出现"没有任何可用登录方式"的实例。纯 SSO 模式下密码登录、注册、改密、TOTP 全部被后端拒绝（前端相应控件隐藏），但已有的密码哈希、会话、passkey、TOTP 配置不会被删——留了清理路径，不留炸弹。

已有账号迁移到 SSO 由 `OIDC_EXISTING_USER_LINK_MODE` 控制：默认 `disabled`（永不自动关联）；`verified_email` 在 Provider 声明 `email_verified=true` 且邮箱相同时关联；`email` 仅凭邮箱匹配就关联——README 明确警告：只有当你完全信任 Provider 对每个邮箱的所有权时才用它，因为能在 Provider 侧设置某个邮箱的人就能认领对应的 Securo 账号。这种"把信任边界写进文档"的做法很加分。

还支持可选的角色同步（`OIDC_SYNC_ROLES=true`），默认取 `groups` 声明，可换成 `OIDC_ROLES_CLAIM` 指定的其他字段。它把 Provider 的群组/角色映射进 Securo 内置权限：

```
OIDC_SYNC_ROLES=true
OIDC_ROLES_CLAIM=groups
OIDC_ADMIN_ROLES=securo-admins
OIDC_WORKSPACE_ROLE_MAP={"securo-owners":"owner","securo-editors":"editor","securo-viewers":"viewer"}
```

- `OIDC_ADMIN_ROLES`：每次 OIDC 登录时授予或吊销 Securo 的 admin（`is_superuser`）
- `OIDC_WORKSPACE_ROLE_MAP`：把 Provider 群组映射到个人 workspace 的 `owner` / `editor` / `viewer` 三档，多条映射命中时取最高权限
- 保持 `OIDC_SYNC_ROLES=false` 则所有项目内角色仍由 Securo 本地管理

新 OIDC 用户默认自动开通（`OIDC_AUTO_REGISTER=true`），用 Provider 声明的已验证邮箱建立账号；设 `false` 则只允许邮箱与 Provider 声明匹配的存量 Securo 用户登录。纯 SSO 的全新实例有个启动门槛：必须保证首次登陆者能成为 admin——通常保持 `OIDC_AUTO_REGISTER=true`、开 `OIDC_SYNC_ROLES=true`，并让该身份的角色声明命中 `OIDC_ADMIN_ROLES` 中的某个值，否则第一个账号不会是管理员。

## 可选 AI Agent：自托管 LLM + MCP 工具调用

在 `.env` 里加两行即可开启：

```
AGENTS_ENABLED=true
COMPOSE_PROFILES=agents
```

支持 OpenAI、Anthropic、Ollama 及 OpenAI 兼容端点多 Provider 接入，通过 **MCP**（Model Context Protocol）对你的记账数据做工具调用，每个 Agent 配独立 RAG 知识库，前端有 ⌘J 全局聊天面板。默认关闭、关闭时零成本——不想让任何 LLM 碰数据的用户可以完全无视这个模块。

非 Docker 部署（裸机/LXC）时 `COMPOSE_PROFILES=agents` 只是让 Compose 启动额外的 `mcp-server` 容器，裸机场景只设 `AGENTS_ENABLED=true`，手动把内置 MCP server（同虚拟环境里的 uvicorn 应用）跑在 API 旁边即可——具体是起一个 `uvicorn mcp_server.main:app`，监听 `127.0.0.1:8765`，再用 `AGENTS_BUILTIN_MCP_URL=http://127.0.0.1:8765/mcp` 指给后端。注意：**MCP server 不在时 Agent 仍能聊天，但没有任何工具、读不到你的数据**，后端日志会记录它连不上哪个 MCP server——这又是一个"可降级但不静默"的设计。

多币种场景配一个免费的 Open Exchange Rates key 即可自动汇率换算；不配则跨币种按 1:1 兜底并在界面上给出视觉警告——又一次"不静默出错"。

## 技术栈一览

README 明确列出的技术栈（选型相当主流，维护成本低、上手容易）：

| 层 | 技术 |
|---|---|
| 后端 | FastAPI + SQLAlchemy + Alembic（迁移）+ Celery（异步任务） |
| 前端 | React + TypeScript + Vite + Tailwind CSS |
| 数据库 | PostgreSQL |
| 队列 | Redis + Celery |

对自托管使用者，这套选择意味着两件实际的好事：一是**文档与生态极其成熟**，遇到问题搜得到；二是需要的中间件就两个——PostgreSQL 与 Redis，docker-compose 一步起齐，Homelab 玩家基本都有现成的。

## 工程质量观察

从仓库本身能看到几个值得注意的工程实践：

- **CI + 覆盖率徽章**：README 顶部挂着 CI 与 Coverage 端点徽章，测试是持续跑的
- **版本节奏**：8 月内 v0.14.3 → v0.14.5 三连发，修复粒度细到"i18n 补荷兰语入口""重复收款人拒绝时说明原因"这类小切口的 issue
- **部署矩阵完整**：install.sh（裸机快速）、docker-compose（标准/生产）、Helm Chart（K8s）、GHCR 容器镜像，四条路径都有
- **安全文档齐全**：SECURITY.md、CODE_OF_CONDUCT.md、CONTRIBUTING.md、.pre-commit-config.yaml、renovate.json 一应俱全，依赖自动更新也在跑

协议是 **AGPL-3.0**——对个人自托管毫无影响，但如果想拿它做商业化 SaaS 需要注意 AGPL 的网络分发条款（修改后对外提供服务须开源修改）。

## 适合谁、不适合谁

**适合**：

- 受不了商业记账 App 隐私政策、想 Family 财务数据不出内网的人
- 已有 Homelab（Docker/K8s/NAS），想加一个家庭多用户记账系统的玩家
- 欧洲用户（PSD2 银行同步开箱即用）或巴西用户（Pluggy）

**需要斟酌**：

- 国内用户：银行同步三家 Provider 都不覆盖中国大陆银行，实际工作流是"网银下载 OFX/CSV → 导入 → 规则引擎自动分类"，多一步手工但完全可用
- 纯小白：至少需要会跑 Docker 和配置 `.env`，比商业 App 门槛高一个量级（这是所有自托管软件的共同代价）
- 想要手机原生 App 体验的：目前以 Web UI 为主

## 结语

Securo 没有发明什么新技术，但它把"隐私优先的个人财务"这件事做成了一个工程上扎实、边界上诚实（每个可降级功能都写清楚兜底行为）的自托管产品。从 passkey 地址校验的 UI 解释，到 OIDC 纯 SSO 模式的防呆启动校验，再到 Enable Banking 免费档限制的提前预警——这些细节说明作者真的在按"自己要用"的标准做软件。如果你一直在找记账数据彻底离开第三方云的方案，它值得一个 Docker 容器的位置。

> 项目地址：https://github.com/securo-finance/securo
> 官网：https://usesecuro.com/ · 文档：https://docs.usesecuro.com/ · Demo：https://demo.usesecuro.com/
