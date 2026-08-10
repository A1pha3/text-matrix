---
title: "authentik：可自部署的开源身份提供商，替代 Okta 与 Auth0"
date: 2026-08-11T03:22:16+08:00
slug: "authentik-open-source-identity-provider"
github_repo: "goauthentik/authentik"
source_key: "gh:goauthentik/authentik"
description: "authentik 是一个开源身份提供商（IdP），支持 SAML、OAuth2/OIDC、LDAP、RADIUS 等协议，提供 SSO、多因素认证、用户生命周期管理和可视化认证流程编排，适用于从个人实验室到企业级集群的自部署场景。"
draft: false
categories: ["技术笔记"]
tags: ["身份认证", "SSO", "IdP", "开源", "安全"]
---

## 这个项目解决了什么

身份认证是几乎所有非平凡应用都需要的基础设施。用云服务（Okta、Auth0、Entra ID）省事但把身份数据交给了第三方，自建又往往意味着拼凑 Keycloak + LDAP + Nginx 的复杂工程。authentik 的定位是：**一个可以完全自部署的身份基础设施，覆盖 SSO、MFA、用户管理、权限治理，同时提供企业级版本满足大规模部署需求**。

核心数据：24.5K Stars、1.9K Forks、Python 为主语言、活跃维护（最近提交 2026-08-10），当前版本 2026.8.0（RC 阶段）。

## 核心能力

### 协议支持

authentik 不只做一种认证协议，而是作为统一的身份层同时提供：

- **SAML 2.0**：服务提供者（SP）发起和 IdP 发起的 SSO
- **OAuth2 / OIDC**：现代 Web 和移动应用的标准认证授权
- **LDAP**：传统应用和基础设施组件的目录服务
- **RADIUS**：网络设备、VPN、Wi-Fi 认证
- **SCIM**：用户生命周期同步到下游应用
- **Proxy Provider**：反向代理模式保护没有原生认证集成的不安全应用

这意味着同一个身份源可以同时给现代 Web 应用、传统 LDAP 应用和网络设备提供认证。

### 认证流程编排

authentik 的核心特色是 **Flow**——一个可视化的认证流程编辑器。每个 Flow 由一系列 Stage 组成，Stage 类型包括：

- **Identification**：用户输入用户名/邮箱
- **Password**：密码验证
- **Authenticator Validate**：MFA 验证（TOTP、WebAuthn、Duo、SMS）
- **Consent**：OAuth 授权同意页面
- **User Write**：注册或更新用户属性
- **Email**：发送验证邮件
- **Custom**：自定义 Python 代码

Flow 可以根据条件（如用户来源、设备信任度、IP 范围）动态分支。例如"公司内网自动通过 SSO，外部访问要求 MFA"这样的策略不需要写代码，在管理界面配置即可。

### 用户生命周期管理

authentik 不只是"认证完了发个 token"，还管理用户的完整生命周期：

- **注册**：自助注册、邀请制、管理员创建
- **分组与角色**：用户分组管理，基于角色的权限分配
- **属性映射**：自定义用户属性到 SAML claim / OIDC scope 的映射
- **恢复**：密码重置流程
- **SCIM 同步**：用户变更自动同步到下游应用

### 企业功能

开源版本（MIT）包含全部核心功能。企业版（EE License）额外提供：

- **企业许可管理**
- **高级 SCIM 集成**
- **合规报告导出**
- **优先支持响应**

这不是"核心功能收费"的模式——SSO、MFA、Flow 编排、所有协议在开源版本中完整可用。

## 部署方式

| 方式 | 推荐场景 | 说明 |
|------|----------|------|
| Docker Compose | 小型/测试环境 | 官方推荐入门方式，两个容器（server + worker） |
| Kubernetes (Helm) | 生产环境 | 官方 Helm Chart，支持水平扩展 |
| AWS CloudFormation | AWS 部署 | 官方 CloudFormation 模板 |
| DigitalOcean Marketplace | 快速试用 | 一键部署 |

### Docker Compose 最小部署

```yaml
# docker-compose.yml（简化版）
services:
  postgresql:
    image: docker.io/library/postgres:16
    environment:
      POSTGRES_DB: authentik
      POSTGRES_USER: authentik
      POSTGRES_PASSWORD: <password>
  redis:
    image: docker.io/library/redis:alpine
  server:
    image: ghcr.io/goauthentik/server:latest
    command: server
    ports:
      - "9000:9000"
      - "9443:9443"
  worker:
    image: ghcr.io/goauthentik/server:latest
    command: worker
```

详细配置参考[官方文档](https://docs.goauthentik.io/docs/install-config/install/docker-compose/)。

## 与同类工具对比

| 维度 | authentik | Keycloak | Authelia | Auth0 (Okta) |
|------|-----------|----------|----------|--------------|
| 协议覆盖 | SAML/OIDC/LDAP/RADIUS/SCIM | SAML/OIDC/LDAP | SAML/OIDC | OIDC/SAML |
| 认证流程编排 | 可视化 Flow 编排 | 基于流程的配置 | 2FA/规则 | Actions/Rules |
| 自部署 | ✅ Docker/K8s | ✅ Docker/K8s | ✅ Docker | ❌ |
| 管理界面 | 完整 Web UI | 完整 Web UI | 基础 Web UI | 完整 Web UI |
| 许可证 | MIT (+ EE) | Apache 2.0 | Apache 2.0 | 商业 |
| 语言 | Python/Go | Java | Go | — |

authentik 相对于 Keycloak 的主要差异：可视化 Flow 编排（Keycloak 用配置式 Authentication Flow），Python 技术栈（对运维团队更容易贡献），以及对 RADIUS 和 SCIM 的原生支持。

## 适用边界

**适合**：

- 需要自部署统一身份基础设施的团队或组织
- 有多种协议需求（SAML + OIDC + LDAP）的异构应用环境
- 希望摆脱商业 IdP 供应商锁定的组织
- 有合规要求需要身份数据留在内网的场景

**不适合**：

- 只需要简单登录功能的个人项目（OAuth proxy 或 Authelia 更轻量）
- 需要 authentik 团队以外的商业支持的场景（社区支持为主）
- 无运维能力维护 PostgreSQL + Redis + authentik 三组件的场景
- Python 生态不熟悉的团队做深度定制（核心逻辑是 Python/Django）

项目开源协议 MIT（核心），当前正处于 2026.8.0 版本 RC 阶段（rc6），迭代频繁。
