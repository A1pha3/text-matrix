---
title: "Insomnia 项目导读：覆盖 GraphQL/REST/gRPC/WebSocket 的开源 API 客户端"
date: "2026-06-25T21:10:32+08:00"
slug: "kong-insomnia-cross-platform-api-client-guide"
github_repo: "Kong/insomnia"
description: "Kong/insomnia 是成熟的开源跨平台 API 客户端，支持 GraphQL、REST、WebSockets、SSE、gRPC 等协议，仓库采用 monorepo 架构，把桌面端、inso CLI、共享 API/数据层、脚本执行环境与测试包分离。本文拆解其 monorepo 布局、3 种存储后端、inso CLI 子命令与 CI 集成方式，并给出采用建议。"
draft: false
categories: ["技术笔记"]
tags: ["GraphQL", "gRPC", "Electron"]
---

# Insomnia 项目导读：覆盖 GraphQL/REST/gRPC/WebSocket 的开源 API 客户端

> **目标读者**：后端/全栈工程师，需要在多个协议上调试、测试、设计 API 的开发者
> **前置知识**：用过 Postman 或同类 API 客户端，对 HTTP/GraphQL/gRPC 有基本概念
> **预计阅读时间**：11 分钟 | **难度**：⭐⭐

---

## 一、核心判断

[Insomnia](https://github.com/Kong/insomnia) 是一个**老牌、跨协议、跨平台**的开源 API 客户端，主仓库由 Kong 维护。仓库创建于 2016-04-23，至今已 10 年，约 40K stars、2.4K forks，TypeScript + Electron，Apache-2.0 协议，截至 2026-08 仍保持高频提交。

它要解决的问题不是"再做一个 Postman"，而是把**多协议（REST / GraphQL / WebSockets / SSE / gRPC）+ 多存储（Local Vault / Git Sync / Cloud Sync）+ 多形态（桌面 GUI + inso CLI）**在同一份 collection 模型上串起来，并通过 Kong 的商业化产品（Cloud Sync、Mock Server、Enterprise SSO）提供付费增值。

理解 Insomnia 的关键不在 GUI 而在 **monorepo 的边界设计**：

- `insomnia`（主包，Electron 桌面应用）
- `insomnia-inso`（命令行工具，CI/CD 集成入口）
- `insomnia-api` / `insomnia-data`（核心 API 与数据访问）
- `insomnia-scripting-environment`（pre-request / post-response 脚本沙箱）
- `insomnia-testing` / `insomnia-smoke-test`（测试基础设施）
- `insomnia-analytics`（共享埋点）

桌面 GUI、inso CLI、第三方插件、未来的 SDK 共用 `insomnia-api` 和 `insomnia-data` 这两层核心能力，UI 与编排逻辑彼此独立。

## 二、系统地图

| 包 | 角色 |
|------|------|
| `packages/insomnia` | Electron + React 桌面端，路由层用 react-router |
| `packages/insomnia-inso` | Node.js CLI，入口 `bin/inso`，子命令 `lint-specification` / `run test` / `script` / `export-specification` |
| `packages/insomnia-api` | 不依赖 Electron 的 API 业务逻辑 |
| `packages/insomnia-data` | 数据持久化抽象（NeDB 兼容、SQLite 后端迁移中） |
| `packages/insomnia-vcs` | Git Sync 的版本控制引擎，负责与任意 Git 仓库同步 collection |
| `packages/insomnia-scripting-environment` | 脚本沙箱，对接 ndb / request / response / 环境变量对象 |
| `packages/insomnia-testing` | 单元测试工具与 collection runner |
| `packages/insomnia-smoke-test` | Playwright 端到端测试 |
| `packages/insomnia-analytics` | 桌面与 CLI 共享的埋点 SDK |

> 注意点：仓库默认分支是 `develop`（不是 `main`），新 PR 默认开向 develop。克隆时记得 `git clone -b develop`。

## 三、3 种存储后端

Insomnia 的差异化在存储层。同一份 collection 可以选择三种落地方式之一，互不强制：

| 存储 | 适用人群 | 数据落点 |
|------|----------|----------|
| **Local Vault** | 个人本地开发，不上云 | 本机加密目录，零外部依赖 |
| **Git Sync** | 团队想用 Git 做 collection 协作 | 任意第三方 Git 仓库（GitHub、GitLab、内部 Gitea） |
| **Cloud Sync** | 多设备、跨地域协作 | Kong 提供的云端，可选端到端加密（E2EE） |

README 强调："拥有 Insomnia 账号不强制你把数据上云"——账号只用于产品能力和云端协作，敏感 collection 仍可走 Local Vault 或 Git Sync。其中 Git Sync 的同步逻辑封装在 `packages/insomnia-vcs`，这也是 Git 生态协作模型的落点。

另外有一个 **Private Environments** 特性：环境变量永远存在本地，从不进入云，与所选存储后端解耦，对企业里"环境变量不能出公司"是重要卖点。

## 四、协议覆盖

Insomnia 不只是 HTTP 客户端。README 明确列出的协议矩阵：

| 协议 | 调试 | 设计 | 测试 | Mock |
|------|------|------|------|------|
| REST / HTTP | ✅ | ✅ (OpenAPI 编辑器) | ✅ | ✅ |
| GraphQL | ✅ | — | ✅ | ✅ |
| WebSockets | ✅ | — | ✅ | — |
| SSE（Server-Sent Events） | ✅ | — | ✅ | — |
| gRPC | ✅ | ✅ (.proto) | ✅ | ✅ |
| 任意 HTTP 兼容协议 | ✅ | — | — | — |

> "Any other HTTP compatible protocol"是 README 的原话，实际是通过自定义插件 + raw HTTP 调试实现。

每个协议对应一个 UI 视图：REST 是经典的 Request/Response tab，GraphQL 带 schema explorer，gRPC 通过 `.proto` 文件导入方法。

## 五、inso CLI

`insomnia-inso` 是把 Insomnia 能力带到 CI/CD 流水线的关键。安装与启动：

```shell
# 安装 monorepo 依赖
npm i

# 启动 watch 模式编译 inso
npm run inso-start

# 跑 inso
./packages/insomnia-inso/bin/inso -v
```

inso 的子命令覆盖四大场景：

| 子命令 | 用途 |
|--------|------|
| `lint-specification` | 校验 OpenAPI/AsyncAPI 规范 |
| `run test` | 在 CI 里跑 collection 的测试套件 |
| `export-specification` | 把 collection 导出成 spec |
| `script` | 执行预请求/后响应脚本，便于回归测试 |

典型 CI 流程：

```shell
# 1. 校验接口规范
inso lint-specification openapi.yaml

# 2. 跑回归测试
inso run test "Echo Test Suite" -w ./fixtures --env Dev --verbose

# 3. CI 失败时直接退出非零状态
```

Node.js 与 Electron 依赖不同的 `node-libcurl` 预编译产物，根 `package.json`（`@getinsomnia/node-libcurl`）提供两个脚本按需切换：

```shell
npm run install-libcurl-node      # inso 运行环境（Node runtime）
npm run install-libcurl-electron  # 桌面端运行环境（Electron runtime）
```

## 六、插件与扩展

桌面端开放插件系统，[Insomnia Plugin Hub](https://insomnia.rest/plugins/) 提供官方与社区插件，常见用途包括自定义主题、第三方认证/OAuth 流程、自定义渲染器、文档生成等。

README 列出的社区项目值得关注：

- [Insomnia Documenter](https://github.com/jozsefsallai/insomnia-documenter)——配合 `insomnia-plugin-documenter` 插件，或直接拿 collection 的 export 文件，生成静态 API 文档站
- [GitHub API Spec Importer](https://github.com/swinton/github-rest-apis-for-insomnia)——把 GitHub REST API 全套路由规格导入 Insomnia
- [Swaggymnia](https://github.com/mlabouardy/swaggymnia)——从已有 API 生成 Swagger 文档

`packages/insomnia-scripting-environment` 把插件脚本能访问的对象（`pm`/`insomnia`/`require`/网络模块）封在沙箱里，避免插件影响主进程安全。

## 七、安全与合规

README 明确写到 Insomnia 账号体系的合规边界：

- ISO27001
- SOC 2 Type II
- ISO27018
- Gold CSA STAR

这套合规在桌面应用里属于少见配置。如果你的企业有这些合规要求，使用 Cloud Sync + 启用 E2EE 是一条相对省力的路。

## 八、维护状态

- **活跃度高**：截至 2026-08 仍有近期提交，社区维护健康，star 增速平稳。
- **桌面端**走 Electron + React；插件系统持续演进，仓库也引入 `.codegraph`、`.claude` 等约定用于 Agent 协作开发。
- **发版节奏**：项目改用统一的 `core@` 版本号发布，最新为 core@13.2.0（2026-08-25），inso 随之一同发布。
- **Kong 收购后定位**：核心功能持续开源，Cloud Sync / 高级协作走付费；不存在"突然闭源"的风险。license 为 Apache-2.0，第三方可商用但不可使用 Insomnia 商标。

## 九、采用顺序与边界

| 场景 | 推荐度 | 说明 |
|------|--------|------|
| 日常 REST/GraphQL 调试 | ⭐⭐⭐⭐⭐ | 比 Postman 更轻、原生 Git Sync 是杀手锏 |
| gRPC 服务开发 | ⭐⭐⭐⭐⭐ | 比 grpcui/grpcurl 强在带 GUI + 测试 |
| 团队 API 协作（Git Sync） | ⭐⭐⭐⭐ | commit-driven review 是 Postman 做不到的 |
| CI/CD 接口测试（inso） | ⭐⭐⭐⭐ | inso 是 Postman/Newman 的真正开源替代 |
| Mock Server | ⭐⭐⭐ | 走 Cloud Sync 才有；自托管能力有限 |
| 离线/内网企业部署 | ⭐⭐⭐ | Local Vault + Git Sync 可解，但失去协作能力 |

对大多数个人开发者，Insomnia 比 Postman 强在三件事：原生 Git Sync、原生 GraphQL、原生 gRPC；对大多数团队，强在 CI 里直接 `inso run test` 跑同一份 collection。如果你的工作流以 REST 为主、只在 Postman UI 里点鼠标、不接 CI，迁移收益相对有限。
