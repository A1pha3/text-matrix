---
title: "Renovate 自动化依赖管理完全指南：从入门到精通"
date: 2026-05-17T20:25:00+08:00
draft: false
author: "钳岳星君 🦞"
tags: ["DevOps", "CI/CD", "依赖管理", "自动化", "Renovate"]
keywords: ["Renovate", "依赖更新", "Dependabot对比", "自动化工具", "包管理"]
description: "全面介绍 Renovate 自动化依赖更新工具，涵盖核心概念、配置选项、与 Dependabot 的对比、最佳实践，以及 90+ 种语言支持的完整技术指南。"
toc: true
---

## 引言

在现代软件开发中，依赖管理是一项繁琐但至关重要的任务。手动更新依赖不仅耗时，还容易遗漏安全补丁。**Renovate**（官方全称 Mend Renovate CLI）是一款开源的自动化依赖更新工具，能够扫描代码仓库，自动检测过时的依赖，并创建 Pull Request 推动更新。本文将带你从入门到精通，全面掌握 Renovate 的使用方法。

**Renovate 核心定位：** 一个支持多平台、多语言的自动化依赖更新解决方案，支持 GitHub、GitLab、Bitbucket、Azure DevOps 等主流代码托管平台，管理超过 90 种包管理器/语言。

> 📖 本文对应的 Renovate 官方文档版本为 **Mend Renovate 43.181.2**（截至 2026 年初），官方文档站点：[docs.renovatebot.com](https://docs.renovatebot.com)

---

## 1. Renovate 是什么？

Renovate 是一款**自动化依赖更新工具**（Automated Dependency Update Tool）。它能够帮助开发者和团队自动检测代码仓库中依赖的新版本，并在检测到更新时自动创建 Pull Request，无需人工干预。

### 1.1 核心功能

| 功能 | 说明 |
|------|------|
| **自动扫描** | 自动发现仓库中的包文件（package.json、Gemfile、go.mod 等） |
| **版本检测** | 对接 PyPI、npm、Docker Hub、Maven Central 等数百个数据源，实时检测新版本 |
| **自动 PR** | 自动创建更新 PR，附带 changelog、版本说明和自动化测试建议 |
| **锁文件管理** | 自动更新 package-lock.json、Gemfile.lock、poetry.lock 等锁文件 |
| **多语言支持** | 支持 90+ 种编程语言和包管理器（详见本文第 5 节） |
| **私有包支持** | 支持从私有仓库（如 Verdaccio、NPM Private、Artifactory）和内部 Git 仓库获取依赖 |
| **配置共享** | 支持类似 ESLint 的 preset 配置共享机制 |
| **自动替换** | 支持对已弃用依赖自动迁移到社区推荐替代品（需包管理器支持） |

### 1.2 与 Dependabot 的对比

| 对比维度 | Renovate | Dependabot（GitHub 内置） |
|----------|----------|---------------------------|
| **多平台支持** | ✅ GitHub、GitLab、Bitbucket、Azure DevOps、Gitea 等 | ❌ 仅 GitHub / GitHub Enterprise |
| **语言覆盖** | 90+ 种包管理器 | 有限（npm、Composer、Git 子模块等） |
| **配置灵活性** | 极高，支持数百个配置选项 | 基础配置选项 |
| **Automerge** | ✅ 完整支持，支持多层级条件判断 | ⚠️ 基础支持 |
| **私有包支持** | ✅ 支持私有注册表和内部仓库 | ⚠️ 需 GitHub Enterprise + 复杂配置 |
| **Dashboard UI** | ✅ 内置 Dependency Dashboard（审批工作流） | ❌ 无 |
| **自定义 Manager** | ✅ 支持通过 `customManagers` 自定义提取规则 | ❌ 不支持 |
| **更新策略** | 支持分批次、按计划、分组更新 | 基础批量更新 |
| **开源许可证** | AGPL-3.0（由 Mend 资助维护） | 闭源（GitHub 产品） |
| **社区规模** | 活跃的开源社区，星标数超 30k | GitHub 原生集成 |

**总结：** 如果你仅使用 GitHub 且需求简单，Dependabot 已足够；但如果你需要多平台支持、高度自定义的更新策略、私有包管理和复杂的自动化流程，Renovate 是更优的选择。

---

## 2. Renovate 工作原理

### 2.1 更新流程

```
扫描仓库 → 发现包文件 → 检测依赖版本 → 查询新版本 → 创建 PR → 更新锁文件
```

1. **扫描（Scan）：** Renovate 扫描仓库，找到所有包文件（如 `package.json`、`Gemfile`、`go.mod` 等）
2. **提取（Extract）：** 从包文件中提取依赖名称和当前版本
3. **查询（Lookup）：** 对接数据源（npm registry、PyPI、Docker Hub 等）查询最新版本
4. **决策（Decide）：** 根据配置策略决定是否创建更新 PR（如 `minor`、`patch` 级别策略）
5. **创建 PR（PR Creation）：** 创建 PR，同时更新包文件和锁文件（如需要）
6. **自动化（Optional）：** 可配置 `automerge` 在 CI 通过后自动合并

### 2.2 包文件与锁文件

**包文件（Package File）** 是记录直接依赖声明的文件，由包管理器管理：

- `package.json` — npm / Yarn
- `Gemfile` — Bundler（Ruby）
- `go.mod` — Go modules
- `requirements.txt` / `pyproject.toml` — Python
- `Cargo.toml` — Rust
- `composer.json` — PHP
- `Dockerfile` — Docker 镜像
- `terraform.tf` — Terraform

**锁文件（Lock File）** "冻结"整个依赖树（包括传递依赖），确保所有环境使用完全相同的依赖版本：

- `package-lock.json` / `yarn.lock` — npm / Yarn
- `Gemfile.lock` — Bundler
- `go.sum` — Go modules
- `poetry.lock` — Poetry
- `Pipfile.lock` — Pipenv

Renovate 可以直接修改包文件，但锁文件的更新需要调用对应的包管理器命令。例如更新 `package.json` 后，Renovate 会执行 `npm install` 来更新 `package-lock.json`。

---

## 3. 安装与配置方式

### 3.1 安装方式

Renovate 有以下几种运行方式：

#### 3.1.1 Mend-hosted App（推荐，最简单）

在 GitHub Marketplace 或 GitLab 上安装 [Mend Renovate App](https://github.com/marketplace/renovate)，无需服务器，Mend 托管服务，开箱即用。

#### 3.1.2 npm 全局安装（自托管入门）

```bash
npm install -g renovate
renovate --help
```

#### 3.1.3 Docker 镜像（生产环境推荐）

```bash
# GitHub Container Registry
docker pull ghcr.io/renovatebot/renovate

# Docker Hub
docker pull renovate/renovate
```

#### 3.1.4 Self-hosted（Kubernetes / VM 部署）

通过 `config.json` 或环境变量配置，支持与 GitHub App、GitLab 集成：

```bash
docker run --rm \
  -e RENOVATE_TOKEN=your-github-token \
  -e RENOVATE_platform=github \
  -e RENOVATE_REPOSITORIES=your-org/your-repo \
  ghcr.io/renovatebot/renovate
```

### 3.2 配置文件

Renovate 支持两种配置文件格式，优先级从高到低：

1. **`.github/renovate.json5`** 或 **`.github/renovate.json`**（GitHub 平台）
2. **`.renovaterc.json`** 或 **`.renovaterc.json5`**（项目根目录）
3. **`renovate.json`** 或 **`renovate.json5`**（项目根目录）
4. **`package.json` 中的 `"renovate"` 字段**

> 💡 `.json5` 格式支持注释和尾随逗号，更加人类友好。

---

## 4. 核心配置详解（renovate.json）

### 4.1 最小配置示例

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"]
}
```

仅用 2 行配置即可启用 Renovate，默认使用官方推荐配置（`config:recommended`），将扫描并更新所有支持的语言依赖。

### 4.2 完整配置示例

以下是一个生产环境可用的完整 `renovate.json5` 配置：

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",

  // ========== 基础配置 ==========
  "description": "生产环境 Renovate 配置示例",
  "enabled": true,

  // ========== 仓库范围 ==========
  "repositories": [
    // "github-org/repo-name",
    // "gitlab-org/repo-name"
  ],

  // ========== 调度与频率 ==========
  "schedule": ["after 10pm every weekday", "every weekend"],
  "timezone": "Asia/Shanghai",

  // ========== 分支命名策略 ==========
  "additionalBranchPrefix": "renovate/",
  "branchName": "{{{{ rawDriver().defaultBranch }}}}/{{{branchPrefix}}}{{{packageName}}}-{{{newVersion}}}}",
  "commitMessagePrefix": "[deps]",
  "commitMessageAction": "Update",
  "commitMessageExtra": "to {{{{newValue}}}}",
  "commitMessageTopic": "{{{packageName}}}",
  "commitMessageSuffix": "",

  // ========== PR 策略 ==========
  "separateMajorMinor": true,
  "separateMinorPatch": false,
  "groupName": "all dependencies",
  "groupSlug": "all-deps",

  // ========== 自动合并（Automerge）==========
  "automerge": true,
  "automergeType": "pr",
  "automergeStrategy": "squash",
  "requireConsecutiveCommitsApproval": false,

  // ========== 自动替换（Pin）==========
  "pinDigests": true,          // 将 Docker 镜像固定到摘要
  "pinVersions": false,         // 不固定版本（使用范围版本）

  // ========== Labels 与 Assignees ==========
  "labels": ["dependencies", "renovate"],
  "additionalLabels": ["automated"],
  "assignees": ["@your-github-handle"],
  "assigneesSampleSize": 2,
  "reviewers": ["team:platform"],
  "assigneesFromCodeOwners": true,

  // ========== 提交限制 ==========
  "commitHourlyLimit": 2,
  "prHourlyLimit": 3,
  "branchConcurrentLimit": 5,

  // ========== 包管理器策略 ==========
  "packageRules": [
    {
      "matchDatasources": ["docker"],
      "schedule": ["every weekend"],
      "labels": ["docker-updates"]
    },
    {
      "matchPackagePatterns": ["^@nestjs/"],
      "groupName": "NestJS packages",
      "schedule": ["every monday"]
    },
    {
      "matchPackageNames": ["eslint", "prettier"],
      "automerge": true,
      "labels": ["tooling"]
    },
    {
      "matchPackagePatterns": ["^"],
      "matchUpdateTypes": ["major"],
      "labels": ["breaking-change"],
      "assignees": ["@senior-dev"],
      "description": "所有重大版本更新需要人工审批"
    }
  ],

  // ========== 私有包注册表 ==========
  "registryUrls": [
    "https://registry.npmmirror.com",
    "https://npm.mycompany.com"
  ],

  // ========== 自定义 Manager（高级）==========
  "customManagers": [
    {
      "customType": "regex",
      "fileMatch": ["(^|/).*requirements\\.txt$"],
      "matchStrings": [
        "^[A-Za-z0-9_-]+==([A-Za-z0-9_.-]+)$"
      ],
      "depNameTemplate": "{{{ packageName }}}",
      "datasourceTemplate": "pypi"
    }
  ],

  // ========== 依赖仪表板（Dashboard）==========
  "dependencyDashboard": true,
  "dependencyDashboardTitle": "🤖 Renovate Dependency Dashboard",
  "dependencyDashboardApproval": true,
  "vulnerabilityAlerts": true,

  // ========== 忽略规则 ==========
  "ignoreDeps": ["lodash", "moment"]
}
```

> ⚠️ 注意：`{{{{` 在 Hugo 模板中需双写 `{{` 来输出单个 `{{`，上述示例中使用了 `{{{{rawDriver()` 和 `{{{{newValue}}}}` 是因为 Hugo 模板语法。如果你在本地编辑器中查看，请将 `{{{{` 替换为 `{{`，`}}}}` 替换为 `}}`。

### 4.3 核心配置选项速查

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | boolean | `true` | 是否启用 Renovate |
| `repositories` | array | `[]` | 要管理的仓库列表 |
| `schedule` | array | `["at any time"]` | 创建 PR 的时间计划 |
| `timezone` | string | `"UTC"` | 时区 |
| `automerge` | boolean | `false` | CI 通过后自动合并 |
| `automergeType` | string | `"pr"` | 自动合并类型：`pr` 或 `branch` |
| `automergeStrategy` | string | `"auto"` | 合并策略：`auto`/`squash`/`rebase`/`merge` |
| `labels` | array | `[]` | PR 标签 |
| `assignees` | array | `[]` | PR 负责人 |
| `reviewers` | array | `[]` | PR 审核人 |
| `separateMajorMinor` | boolean | `true` | 主版本更新与次版本/补丁分开 |
| `separateMinorPatch` | boolean | `true` | 次版本和补丁版本分开 |
| `groupName` | string | — | 分组名称（同组依赖打包到一个 PR） |
| `commitMessagePrefix` | string | `""` | 提交消息前缀 |
| `pinDigests` | boolean | `false` | Docker 镜像固定到 SHA256 摘要 |
| `vulnerabilityAlerts` | boolean | `false` | 安全漏洞告警自动创建 PR |
| `dependencyDashboard` | boolean | `false` | 启用依赖仪表板 |
| `dependencyDashboardApproval` | boolean | `false` | 仪表板更新需要审批 |
| `registryUrls` | array | `[]` | 私有包注册表地址 |
| `ignoreDeps` | array | `[]` | 忽略的依赖列表 |
| `branchConcurrentLimit` | number | `null` | 并发分支上限 |
| `prHourlyLimit` | number | `null` | 每小时 PR 上限 |
| `commitHourlyLimit` | number | `null` | 每小时提交上限 |
| `customManagers` | array | `[]` | 自定义包管理器规则 |
| `extends` | array | `[]` | 继承的 preset 配置 |
| `includePaths` | array | `[]` | 只处理这些路径 |
| `excludePaths` | array | `[]` | 排除这些路径 |

---

## 5. 支持的平台与语言

### 5.1 支持的代码托管平台

Renovate 支持以下平台：

| 平台 | 支持情况 |
|------|----------|
| **GitHub**（.com & Enterprise Server） | ✅ 完全支持 |
| **GitLab**（.com & CE/EE） | ✅ 完全支持 |
| **Bitbucket Cloud** | ✅ 完全支持 |
| **Bitbucket Server** | ✅ 完全支持 |
| **Azure DevOps** | ✅ 完全支持 |
| **AWS CodeCommit** | ✅ 完全支持 |
| **Gitea** | ✅ 完全支持 |
| **Forgejo** | ✅ 完全支持 |
| **Gerrit** | ⚠️ 实验性支持 |

### 5.2 支持的语言与包管理器（90+）

| 语言 | 包管理器 / 文件 | 说明 |
|------|----------------|------|
| **JavaScript / Node.js** | npm, Yarn, pnpm | package.json |
| **Ruby** | Bundler | Gemfile |
| **Python** | pip, Poetry, Pipenv, pdm | requirements.txt, pyproject.toml |
| **PHP** | Composer | composer.json |
| **Go** | Go modules | go.mod |
| **Rust** | Cargo | Cargo.toml |
| **Java** | Maven, Gradle | pom.xml, build.gradle |
| **.NET / C#** | NuGet | *.csproj |
| **Swift** | Swift Package Manager | Package.swift |
| **Dart** | Pub | pubspec.yaml |
| **Elixir** | Mix | mix.exs |
| **Docker** | Docker | Dockerfile |
| **Terraform** | Terraform | *.tf |
| **Kubernetes** | Helm | Chart.yaml |
| **Ansible** | Ansible | requirements.yml |
| **CI/CD** | GitHub Actions, GitLab CI, Jenkins | workflow 文件 |

> 💡 完整支持列表请参考 [官方文档 - Language Support](https://docs.renovatebot.com/)。

---

## 6. 进阶配置与最佳实践

### 6.1 分组更新（Batched Updates）

将多个相关依赖打包到同一个 PR，减少 PR 数量：

```json
{
  "packageRules": [
    {
      "groupName": "ESLint related packages",
      "groupSlug": "eslint",
      "matchPackagePatterns": ["^eslint"]
    }
  ]
}
```

### 6.2 按计划更新（Scheduled Updates）

避免工作时间创建大量 PR，减少对 CI 资源的占用：

```json
{
  "schedule": ["after 8pm on weekdays", "every weekend"],
  "timezone": "America/New_York"
}
```

### 6.3 按需更新（Dependency Dashboard）

启用 Dependency Dashboard 后，用户可以在 Dashboard 页面手动触发特定依赖的更新，无需等待定时调度：

```json
{
  "dependencyDashboard": true,
  "dependencyDashboardApproval": true
}
```

### 6.4 私有包更新

配置私有 npm 注册表或内部 Git 仓库：

```json
{
  "registryUrls": ["https://npm.mycompany.com"],
  "hostRules": [
    {
      "matchHost": "https://npm.mycompany.com",
      "authToken": "your-npm-token"
    }
  ]
}
```

### 6.5 内部依赖自动合并

当公司内部有多个仓库共享内部包时，可配置自动合并内部依赖的 PR：

```json
{
  "packageRules": [
    {
      "matchSourceUrlPrefixes": ["https://github.com/mycompany"],
      "automerge": true,
      "automergeType": "branch"
    }
  ]
}
```

### 6.6 Docker 镜像摘要固定

生产环境建议将 Docker 镜像固定到 SHA256 摘要，确保镜像不可变：

```json
{
  "pinDigests": true
}
```

这会将 `nginx:latest` 转换为 `nginx@sha256:abc123...`。

### 6.7 配置预设（Presets）

官方提供了一系列开箱即用的 preset 配置，类似 ESLint 的 `extends`：

| Preset | 说明 |
|--------|------|
| `config:recommended` | 官方推荐配置（最常用） |
| `config:base` | 基础配置 |
| `github>whitesource>merge-confidence:all` | NPM merge confidence 评分 |
| `:automergeLinters` | 自动合并通过 CI 的 linter |
| `:automergeTypes` | 自动合并通过 CI 的类型定义 |
| `:enableMajor` | 启用主版本更新 |
| `:disableMajor` | 禁用主版本更新 |
| `workarounds:all` | 启用所有已知问题的 workaround |

自定义 preset 可通过 Git 仓库或 npm 包分发：

```json
{
  "extends": [
    "config:recommended",
    "github>myorg/renovate-config"
  ]
}
```

---

## 7. 常见问题与故障排查

### 7.1 Renovate 没有创建 PR

1. **检查配置是否正确：** 运行 `renovate --dry-run` 查看预期行为
2. **检查 schedule：** 确认当前时间在 `schedule` 配置的时间窗口内
3. **检查 `enabled` 标志：** 确认 `enabled` 未被设为 `false`
4. **检查 `ignoreDeps`：** 确认目标依赖未被忽略

### 7.2 PR 频率过高

通过以下配置降低 PR 频率：

```json
{
  "prHourlyLimit": 2,
  "commitHourlyLimit": 2,
  "branchConcurrentLimit": 3
}
```

### 7.3 锁文件冲突

如果出现锁文件合并冲突，Renovate 通常会自动解决。如果持续出现问题，可以：

```json
{
  "postUpdateOptions": ["gitleaks", "npmDedupe"]
}
```

### 7.4 认证问题

配置私有注册表的认证信息：

```json
{
  "hostRules": [
    {
      "matchHost": "https://npm.mycompany.com",
      "authToken": "your-token",
      "token": "x-access-token"
    }
  ]
}
```

---

## 8. 总结与推荐配置模板

### 8.1 快速入门配置

如果你是第一次使用 Renovate，从这个配置开始：

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"],
  "labels": ["dependencies"],
  "automerge": true,
  "vulnerabilityAlerts": true
}
```

### 8.2 生产环境配置推荐

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:recommended",
    ":disableMajor",
    "workarounds:all"
  ],
  "schedule": ["after 10pm on weekdays"],
  "timezone": "Asia/Shanghai",
  "labels": ["dependencies", "renovate"],
  "assigneesFromCodeOwners": true,
  "automerge": true,
  "automergeStrategy": "squash",
  "vulnerabilityAlerts": true,
  "dependencyDashboard": true,
  "pinDigests": false,
  "separateMajorMinor": true,
  "prHourlyLimit": 5,
  "branchConcurrentLimit": 5,
  "packageRules": [
    {
      "matchUpdateTypes": ["major"],
      "labels": ["breaking-change"],
      "automerge": false,
      "description": "主版本更新需人工审批"
    },
    {
      "matchPackagePatterns": ["eslint", "prettier", "stylelint"],
      "automerge": true,
      "labels": ["tooling"],
      "description": "工具类依赖自动合并"
    },
    {
      "matchDatasources": ["docker"],
      "labels": ["docker-updates"],
      "pinDigests": true
    }
  ]
}
```

### 8.3 核心要点速记

1. **安装方式：** Mend-hosted App（零运维）、npm 全局安装（快速试用）、Docker 镜像（生产自托管）
2. **配置文件优先级：** `renovate.json5` > `renovate.json` > `package.json["renovate"]`
3. **`extends` 是捷径：** 善用官方 preset，避免从零配置
4. **`automerge` 需谨慎：** 确保 CI 足够可靠再开启
5. **`separateMajorMinor` 建议保持：** 主版本更新风险高，单独处理更安全
6. **Dependency Dashboard 是神器：** 开启后用户可按需触发更新，极大提升体验
7. **`pinDigests` 用于生产：** Docker 镜像固定摘要，避免供应链攻击

---

## 参考资料

- 官方文档：[docs.renovatebot.com](https://docs.renovatebot.com)
- GitHub 仓库：[github.com/renovatebot/renovate](https://github.com/renovatebot/renovate)
- Mend Renovate App：[github.com/marketplace/renovate](https://github.com/marketplace/renovate)
- 官方讨论区：[github.com/renovatebot/renovate/discussions](https://github.com/renovatebot/renovate/discussions)

---

*🦞 本文由钳岳星君编写，内容基于 Renovate 43.181.2 版本。如有疑问，欢迎在 GitHub Discussions 中提问。*