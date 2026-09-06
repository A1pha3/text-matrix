---
title: "authentik：把身份认证从拼凑多个系统，变成一套自部署的统一身份层"
date: 2026-08-11T03:22:16+08:00
lastmod: 2026-09-06T00:00:00+08:00
slug: "authentik-open-source-identity-provider"
github_repo: "goauthentik/authentik"
source_key: "gh:goauthentik/authentik"
description: "authentik 是一个开源身份提供商（IdP），支持 OIDC、SAML、LDAP、RADIUS、SCIM、Kerberos 等协议，提供 SSO、多因素认证、用户生命周期管理和可视化认证流程编排，适用于从个人实验室到企业级集群的自部署场景。"
draft: false
categories: ["技术笔记"]
tags: ["身份认证", "SSO", "IdP", "开源", "安全"]
---

## 这个项目真正解决的是什么

身份认证几乎每个稍微复杂的应用都需要。选云服务（Okta、Auth0、Entra ID 这类托管身份提供商，IdP）省心，但代价是把身份数据交给第三方；自己搭，传统路线是 Keycloak + LDAP + Nginx 三个系统拼在一起，协议、生命周期、认证流程各管各的，维护成本被摊到多个组件上。

authentik 的切入点不是再提供一个认证单体，而是把上述几件事收进**一个**可自部署的系统：同一套身份源同时服务现代 Web 应用（OIDC/SAML）、传统应用（LDAP）、网络设备（RADIUS），认证流程用可视化编排，用户生命周期（注册、分组、映射、同步）也在同一处管理。它真正收编的，是"多套认证基础设施各自为政"这个更常见的工程负担。

核心数据：25.4K Stars、约 2K Forks（2026 年 9 月核对）。技术栈是多语言组合：核心逻辑是 Python/Django，管理界面是 TypeScript，负责协议接入的 outpost（LDAP、RADIUS、proxy 等）是 Go；2026.8 起 server 的请求入口与 proxy outpost 已用 Rust 重写，核心仍是 Django。2026.2 起项目把大版本节奏调整为约三个月一轮，2026.5 是首个新节奏版本，当前稳定版为 2026.8 系列（2026.8.0 发布于 2026 年 8 月 18 日，9 月初跟进 2026.8.1）。

## 系统地图：一次认证请求会穿过什么

在进入细节前，先看这套系统由哪几块组成、一次请求如何流动：

```mermaid
flowchart LR
    U[用户浏览器] -->|1 访问应用| P[Proxy Provider<br/>反向代理]
    P -->|2 未认证,重定向| F[Flow 编排器]
    F -->|3 依次执行 Stage| S1[Identification]
    S1 --> S2[Password]
    S2 --> S3[Authenticator Validate<br/>MFA: TOTP/WebAuthn]
    S3 -->|4 校验通过| T[Token 与 Session]
    T -->|5 注入 Cookie/断言| P
    P -->|6 放行| A[下游应用]
    F -.->|旁路: LDAP/SCIM 目录同步| D[LDAP / SCIM]
```

两条主线需要分开看：**认证流程**（Flow + Stage，决定"谁、怎么验证、是否放行"）和**目录同步**（LDAP/SCIM，决定"用户数据如何出入系统"）。前者是实时请求路径，后者是异步同步路径，不要混成一条线。

还有一类容易被忽略的组件是 **outpost**。LDAP、RADIUS、proxy 这类协议的流量并不直接由 Django 处理，而是由独立的轻量进程落地：outpost 可以与 server 同容器嵌入，也可以独立部署，由 worker 通过挂载的 Docker socket 统一管理。协议越多，越值得理解这条边界——改协议配置，实际生效的是 outpost。

## 认证流程编排：Flow 与 Stage

authentik 的核心差异在 **Flow**，一个可视化认证流程编辑器。每个 Flow 由一系列 Stage 按顺序组成，Stage 类型覆盖认证的常见环节：

- **Identification**：收集用户名或邮箱
- **Password**：密码验证
- **Authenticator Validate**：MFA 验证（TOTP、WebAuthn、Duo、SMS）
- **Consent**：OAuth 授权同意页
- **Prompt**：动态表单，在注册或登录时收集额外字段
- **User Write**：注册或更新用户属性
- **Email**：发送验证邮件

Stage 类型共有 25 种，覆盖从验证码到邀请码的常见环节。让这些 Stage 协同工作的粘合剂是 **Policy（策略）**——用 Python 表达式书写的条件判断，绑定到 Flow、Stage 或应用上，决定某个 Stage 是否执行。像"公司内网自动通过 SSO，外部访问要求 MFA"这类分支，在管理界面给 Password 或 Authenticator Validate 挂一个按 IP 段判断的 Policy 即可，只有复杂条件才需要写表达式。绑定到 Flow、Stage 或应用的策略、用户、组授权还能设置过期时间（2026.8 新增），"临时放行三天"这类需求到期自动失效，不用再记着去撤销。这套设计把 Keycloak 里靠配置堆出来的 Authentication Flow，变成了一段可读、可复用的流程定义。

### 一次登录如何穿过整个系统

用一个具体任务把上面两条主线串起来：用户访问一个挂载了 Proxy Provider 的自托管应用。

1. 请求先到 authentik 的反向代理，代理检查会话。
2. 未认证，代理把请求重定向到登录 Flow。
3. Flow 依次执行 Identification（收集用户名）、Password（校验密码）、Authenticator Validate（若策略要求 MFA，校验 TOTP）。
4. 校验通过，authentik 生成会话，Proxy Provider 给浏览器注入 Cookie。
5. 代理带着认证上下文放行，应用正常返回。

如果同一用户信息还要进下游系统，则走 SCIM 同步这条旁路，把用户变更推到订阅了该同步的应用。两条路径一个管"访问当下"，一个管"数据一致"，各自独立。

## 用户生命周期管理

authentik 不只在认证时发一个 token，也管理用户从进入到离开的完整过程：

- **注册**：自助注册、邀请制、管理员创建
- **分组与角色**：用户分组，基于角色的权限分配
- **属性映射**：自定义用户属性到 SAML claim / OIDC scope 的映射
- **恢复**：密码重置流程
- **SCIM 同步**：用户变更自动同步到下游应用
- **紧急处置**：账号锁定（Account Lockdown，企业版，2026.5 引入），一键停用账号、作废密码、结束全部会话并吊销令牌，处理疑似被盗的账号

一个身份源同时服务目录、认证、授权，是这套系统相比"各组件各管一段"的主要价值。

## 协议支持

authentik 作为统一身份层，开源版本同时提供：

- **OAuth2 / OIDC**：现代 Web 和移动应用的标准认证授权；2026.8 起通过 OpenID 基金会官方认证（OpenID Certified™），覆盖 OP 的 Basic、Implicit、Hybrid、Config、Form Post 配置，以及 RP-Initiated、Front-Channel、Back-Channel 三类登出配置
- **SAML 2.0**：服务提供者（SP）发起和 IdP 发起的 SSO，支持前后端通道单点登出（SLO）
- **LDAP**：传统应用和基础设施组件的目录服务
- **RADIUS**：网络设备、VPN、Wi-Fi 认证
- **SCIM**：用户生命周期同步到下游应用
- **Kerberos**：作为外部身份源接入，让已有的 AD 域用户免密登录（企业预览特性）
- **Proxy Provider**：反向代理模式保护没有原生认证集成的应用
- **RAC（Remote Access Control）**：通过浏览器访问远程的 Windows、macOS、Linux 主机（RDP/SSH/VNC），2025.2 起随开源版提供

OAuth2/OIDC 侧还提供受信令牌交换（token exchange）、按 RFC 8693 的 on-behalf-of 委托、动态客户端注册（DCR），以及防止令牌被窃后滥用的 key-bound ID token——这些都在开源版本内。

企业版在此基础上额外提供：**WS-Federation**（签发 SAML 1.1 断言，用于对接仍依赖该协议的 Microsoft 365 与 Entra ID）和 **SSF（Shared Signals Framework）**（向 Apple 等下游系统异步推送实时安全事件）。更完整的协议与版本差异见[官方特性页](https://goauthentik.io/features/)。

## 企业功能

开源版本（MIT）包含全部核心功能；SSO、MFA、Flow 编排、所有协议在开源版本中完整可用，不是"核心功能收费"的模式。企业版（EE License）在其上叠加面向治理与自动化管理的特性：2026.8 新增特权访问管理（PAM，用户可申请带到期时间的访问）、计划内的用户下线和副账号（agent accounts）；2026.2 起提供对象生命周期管理（Object Lifecycle Management，对应用、组、角色安排周期性评审，当前为预览特性）；2026.5 起的账号锁定（Account Lockdown）也属于企业版。上一节的 Kerberos 身份源同样以企业预览形式归在这里。是否为此付费，取决于你更需要治理审批能力，还是只需要自托管 SSO 本身。

## 部署方式

| 方式 | 推荐场景 | 说明 |
|------|----------|------|
| Docker Compose | 小型/测试环境 | 官方推荐入门方式，PostgreSQL + server + worker 三个容器 |
| Kubernetes (Helm) | 生产环境 | 官方 Helm Chart，支持水平扩展 |
| AWS CloudFormation | AWS 部署 | 官方 CloudFormation 模板 |
| DigitalOcean Marketplace | 快速试用 | 一键部署 |

### Docker Compose 最小部署

```yaml
# docker-compose.yml（最小可运行，需替换 <password> 与 <secret-key>）
services:
  postgresql:
    image: docker.io/library/postgres:16-alpine
    environment:
      POSTGRES_DB: authentik
      POSTGRES_USER: authentik
      POSTGRES_PASSWORD: <password>   # 需替换为强密码
    volumes:
      - database:/var/lib/postgresql/data
  server:
    image: ghcr.io/goauthentik/server:2026.8
    command: server
    depends_on:
      - postgresql
    environment:
      AUTHENTIK_SECRET_KEY: <secret-key>          # openssl rand -base64 60 生成
      AUTHENTIK_POSTGRESQL__HOST: postgresql
      AUTHENTIK_POSTGRESQL__PASSWORD: <password>  # 与 postgresql 保持一致
    ports:
      - "9000:9000"    # HTTP 入口
      - "9443:9443"    # HTTPS 入口
  worker:
    image: ghcr.io/goauthentik/server:2026.8
    command: worker
    depends_on:
      - postgresql
    environment:
      AUTHENTIK_SECRET_KEY: <secret-key>
      AUTHENTIK_POSTGRESQL__HOST: postgresql
      AUTHENTIK_POSTGRESQL__PASSWORD: <password>
volumes:
  database:
```

`<password>` 与 `<secret-key>` 是占位符：数据库密码替换为强密码，secret key 用 `openssl rand -base64 60` 生成，server 与 worker 的同名变量保持一致。持久化卷与完整配置见[官方文档](https://docs.goauthentik.io/docs/install-config/install/docker-compose/)。9000 是 HTTP 入口、9443 是 HTTPS 入口，生产应只暴露 9443。

2025.10 起 authentik 移除了 Redis 依赖，缓存、任务队列、WebSocket 与嵌入式 outpost 全部由 PostgreSQL 承载，最小部署只需这三个容器；server 镜像同时运行内置 proxy outpost，无需单独部署。示例里的 worker 没有挂载 Docker socket，因此只能使用嵌入式 outpost；需要自动部署独立 outpost 时，再给 worker 挂载 `/var/run/docker.sock`。

## 与同类工具对比

| 维度 | authentik | Keycloak | Authelia | Auth0 (Okta) |
|------|-----------|----------|----------|--------------|
| 协议覆盖 | SAML/OIDC/LDAP/RADIUS/SCIM，Kerberos 为企业预览 | SAML/OIDC/LDAP/Kerberos | OIDC | OIDC/SAML |
| 认证流程编排 | 可视化 Flow | 配置式 Authentication Flow | 2FA/规则 | Actions/Rules |
| 自部署 | ✅ Docker/K8s | ✅ Docker/K8s | ✅ Docker | ❌ |
| 管理界面 | 完整 Web UI | 完整 Web UI | 基础 Web UI | 完整 Web UI |
| 许可证 | MIT (+ EE) | Apache 2.0 | Apache 2.0 | 商业 |
| 语言 | Python/TS/Go/Rust | Java/TS | Go | — |

authentik 相对 Keycloak 的主要差异：可视化 Flow 编排（Keycloak 用配置式 Authentication Flow），Python 技术栈（对运维团队更容易贡献），以及对 RADIUS 和 SCIM 的原生支持。Kerberos 两边都有，但 Keycloak 内置在社区版，authentik 的企业预览需要付费。Authelia 更轻，官方文档只有 OIDC 与 Trusted Headers，至今没有 SAML 支持，只适合纯 OIDC 的场景。

## 适用边界

**适合**：

- 需要自部署统一身份基础设施的团队或组织
- 有多种协议需求（SAML + OIDC + LDAP）的异构应用环境
- 希望摆脱商业 IdP 供应商锁定的组织
- 有合规要求、需身份数据留在内网的场景

**不适合**：

- 只需要简单登录功能的个人项目（OAuth proxy 或 Authelia 更轻量）
- 需要 authentik 团队以外的商业支持的场景（社区支持为主）
- 无运维能力维护 PostgreSQL + server/worker 三容器的场景
- Python 生态不熟悉的团队做深度定制（核心逻辑是 Python/Django）

## 采用顺序

如果你的场景符合"自部署统一身份层"，建议按这个顺序走：

1. 先用 Docker Compose 起一套，把登录 Flow 和 OIDC 接一个真实应用，验证流程编排是否满足你需要的分支策略。
2. 确认需要多协议时，再规划 LDAP 目录接入和 SCIM 同步，把现有应用逐步迁入。
3. 生产环境用 Helm 部署，只暴露 9443，把 PostgreSQL 与 authentik 的持久化与备份纳入现有运维体系。

只有单一协议、单应用的轻量需求，不必上 authentik，Authelia 或一个 OAuth proxy 更省事。

## 常见问题

**忘记管理员密码怎么重置？** 普通用户在管理界面（Directory → Users）选中后点 Reset password 即可。丢失 akadmin 密码时，在 server 容器里执行 `docker compose exec server ak changepassword akadmin`，按提示输入新密码；也可以用 `docker compose run --rm server create_recovery_key 10 akadmin` 生成一个 10 分钟有效的恢复链接。两种方式都不需要重建数据库。

**9000 和 9443 分别是什么？** 9000 是 HTTP 入口、9443 是 HTTPS 入口。生产只暴露 9443，HTTP 用于内部或调试。

**开源版和 EE 版怎么选？** 开源版已含 SSO、MFA、Flow、全部协议。多数自托管场景开源版够用；需要特权访问管理（PAM）、对象生命周期管理、WS-Federation 这类治理与自动化特性才考虑 EE。

## 维护指引

- 升级前先读官方 release notes；2026.8 带来多项企业功能（PAM、计划内用户下线等）和开源的对象自定义属性，同时包含破坏性变更（转发头只信任受信代理、hash_password 不再接受命令行传参），生产环境建议先在测试环境验证再升级。
- 备份对象是 PostgreSQL 数据库；2025.10 起 authentik 不再依赖 Redis，缓存、任务队列与会话均由 PostgreSQL 承载，备份这一处即可。
- 修改 Flow 前先在测试环境验证，生产 Flow 变更会影响所有登录入口。
- 项目开源协议 MIT（核心）。