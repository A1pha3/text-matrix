---
title: "Renovate 自动化依赖管理指南"
date: 2026-05-17T20:25:00+08:00
lastmod: "2026-09-29"
draft: false
slug: github-renovate-automated-dependency-management-guide
github_repo: "renovatebot/renovate"
source_key: "gh:renovatebot/renovate"
categories: ["技术笔记"]
tags: ["DevOps", "CI/CD", "依赖管理", "自动化"]
description: "Renovate 自动扫描仓库中的过期依赖并自动开 PR 更新：官方 90+ 包管理器、多平台托管、preset 配置共享与 Dependabot 的真实差距。本文按 44.x 版本线拆配置项、运行方式与排障路径。"
toc: true
---

手动升级依赖是件机械活：盯 release、改版本号、刷新锁文件、跑 CI，哪个环节偷懒都可能漏掉安全补丁。Renovate 把这条链路自动化了——扫描代码仓库、检测过期依赖、自动创建 Pull Request，支持 GitHub、GitLab、Bitbucket、Azure DevOps 等平台。官方 README 的口径是支持超过 90 种包管理器，实际文档站的 manager 列表已列到 119 个（2026-09-29 实测）。

> 📖 Renovate 发版极快，几乎每个工作日都有新版本：本文核查时版本线在 **44.x**（2026-09-29 当天发布了 4 个版本，最新 44.118.1）。配置项层面多年稳定，但**个别字段名和 preset 在近两年大版本里改过名**，旧博客里常见的 `pinVersions`、`matchPackagePatterns`、`config:base` 在当前版本都已失效——本文按 44.x 口径写，并标注了这些变迁。

---

## 1. Renovate 是什么？

Renovate 是一款**自动化依赖更新工具**。它不做构建、不做部署，只负责一件事：让依赖保持新鲜。发现新版本后自动开 PR，你审阅、测试、合并。

### 1.1 核心功能

| 功能 | 说明 |
|------|------|
| **自动扫描** | 自动发现仓库中的包文件（package.json、Gemfile、go.mod 等），包括 monorepo 内嵌套的 |
| **版本检测** | 对接 npm、PyPI、Docker Hub、Maven Central 等数据源检测新版本 |
| **自动 PR** | 创建更新 PR，附 release notes、changelog 链接和 Merge Confidence 徽章 |
| **锁文件管理** | 自动更新 package-lock.json、Gemfile.lock、poetry.lock 等锁文件 |
| **多语言支持** | 官方口径 90+ 种包管理器，文档站列 119 个 manager 条目 |
| **私有包支持** | 支持私有注册表（Artifactory、Verdaccio 等）和内部 Git 仓库 |
| **配置共享** | 类似 ESLint 的 preset 机制，可按仓库分发和继承 |
| **自动替换** | 对已弃用的包自动发起迁移 PR，替换为社区推荐的替代品（replacements） |

### 1.2 与 Dependabot 的对比

Renovate 官方维护了一份[机器人对比页](https://docs.renovatebot.com/bot-comparison/)，措辞相当克制。下表以它为准：

| 对比维度 | Renovate | Dependabot |
|----------|----------|------------|
| **平台支持** | GitHub、GitLab、Bitbucket Cloud/Server、Azure DevOps、Gitea、Forgejo 等多平台 | 仅 GitHub 和 Azure DevOps |
| **包管理器** | 90+（文档站 119 个条目） | 覆盖主流生态（完整列表见 GitHub 文档） |
| **Dependency Dashboard** | ✅ 有，集中查看和触发所有更新 | ❌ 无同类功能 |
| **分组更新** | 内置社区分组 preset（如 monorepo 组） | 支持手动配置 `groups`，安全更新可自动分组 |
| **monorepo 包联动** | `group:monorepos` preset 把同一 monorepo 的包打进一个 PR | 不支持 |
| **merge confidence** | 四个徽章：Age / Adoption / Passing / Confidence | 一个兼容性评分徽章 |
| **自定义提取规则** | `customManagers` 可用正则定义任意依赖源 | ❌ 不支持 |
| **开源状态** | AGPL-3.0，由 Mend 资助，TypeScript 编写 | dependabot-core 以 MIT 开源（Ruby），但只作为 GitHub 内置功能运行 |

一句话总结：只在 GitHub 上、需求就是"例行公事地更新依赖"，Dependabot 够用；要跨平台、要控制 PR 节奏和分组、要管私有包，Renovate 的配置空间大一个量级。

---

## 2. Renovate 工作原理

### 2.1 更新流程

```
扫描仓库 → 提取依赖 → 查询新版本 → 按策略决策 → 创建/更新 PR → （可选）自动合并
```

1. **扫描（Scan）**：找到仓库中所有支持的包文件（`package.json`、`Gemfile`、`go.mod` 等）
2. **提取（Extract）**：从包文件中提取依赖名称和当前版本
3. **查询（Lookup）**：到对应数据源（npm registry、PyPI、Docker Hub 等）查可用版本
4. **决策（Decide）**：按配置策略（更新类型、分组、调度、限流）决定开哪些分支和 PR
5. **创建 PR**：同时更新包文件和锁文件，附 release notes 和徽章
6. **自动化（可选）**：配置 `automerge` 后，CI 通过且满足条件的 PR 直接合并

第一次接入时还有一个**onboarding 序列**：Renovate 先开一个 "Configure Renovate" PR（内含默认配置文件），你合并它之后，Renovate 才开始工作——接下来通常是 "Pin Dependencies" PR（如需要），然后是批量升级 PR。这也是为什么刚接入时 PR 洪水最猛：`prHourlyLimit` 的官方文档正是拿这个场景解释默认值为什么是 2。

### 2.2 包文件与锁文件

**包文件（package file）** 记录直接依赖声明：

- `package.json` — npm / Yarn / pnpm
- `Gemfile` — Bundler（Ruby）
- `go.mod` — Go modules
- `requirements.txt` / `pyproject.toml` — Python
- `Cargo.toml` — Rust
- `composer.json` — PHP

**锁文件（lock file）** 冻结整棵依赖树（含传递依赖），保证各环境装到完全相同的版本：

- `package-lock.json` / `yarn.lock` — npm / Yarn
- `Gemfile.lock` — Bundler
- `go.sum` — Go modules
- `poetry.lock` — Poetry
- `Pipfile.lock` — Pipenv

Renovate 直接编辑包文件；锁文件则调用对应的包管理器命令来更新——比如改完 `package.json` 后执行 `npm install` 刷新 `package-lock.json`。此外还有独立的**锁文件维护**（lock file maintenance）：即使包文件没变，也会定期重装依赖刷新锁文件，默认计划是每周一凌晨 4 点（`["before 4am on monday"]`）。

---

## 3. 运行方式与配置文件

### 3.1 运行方式

按官方 README 的 "Ways to run Renovate"，从省心到自主排列：

**Mend 托管（Cloud-Hosted，推荐起步）**

在 GitHub 上安装 [Mend Renovate App](https://github.com/apps/renovate)，选 "All repositories" 或手动挑选仓库即可，无需服务器。免费 Community 计划可用，支持 GitHub.com 和 Bitbucket Cloud。GitLab.com 的托管版在 2026 年 7 月用新架构重新上线，通过 [Mend Developer Platform](https://developer.mend.io) 安装，目前仅支持 Group 级安装。App 默认跳过 fork（选 "All repositories" 时），也跳过没有可识别包文件的仓库。

**自托管（Self-hosted）**

- **Mend Renovate Community**：官方开源的自托管版本，免费，支持 GitHub / GitLab / Bitbucket Data Center，仓库在 [mend/renovate-ce-ee](https://github.com/mend/renovate-ce-ee)
- **npm 全局安装**：`npm install -g renovate`，适合快速试用
- **Docker 镜像**：`ghcr.io/renovatebot/renovate` 或 Docker Hub 的 `renovate/renovate`，生产自托管的主流选择

**CI 流水线方式**

不想常驻服务的话，官方提供了 [GitHub Action](https://github.com/renovatebot/github-action) 和 [GitLab Renovate Runner](https://gitlab.com/renovate-bot/renovate-runner/)，也可以在任何能跑 `npx renovate` 的流水线里自定义调度。

自托管最小配置长这样：

```bash
docker run --rm \
  -e RENOVATE_TOKEN=your-github-token \
  -e RENOVATE_REPOSITORIES=your-org/your-repo \
  ghcr.io/renovatebot/renovate
```

调试自托管问题时，`dryRun` 配置很有用，它有三个档位：`"extract"` 只扫描依赖，`"lookup"` 加上查询可用更新，`"full"` 完整跑一遍流程但只打日志、不动仓库。这是 self-hosted 专属配置（`globalOnly`），Mend 托管 App 用户用不了。

### 3.2 配置文件

Renovate 在仓库里按**固定顺序查找**配置文件，用找到的第一个（注意：这是查找顺序，不是叠加优先级）：

1. 自定义文件名列表（self-hosted 管理员用 `configFileNames` 指定）
2. `renovate.json` / `renovate.json5`
3. `.github/renovate.json` / `.github/renovate.json5`
4. `.gitlab/renovate.json` / `.gitlab/renovate.json5`
5. `.renovaterc` / `.renovaterc.json` / `.renovaterc.json5`
6. `package.json` 中的 `"renovate"` 字段——**已官方弃用**，文档明确写着 "will be removed in a future release"

`.json5` 格式支持注释和尾随逗号，推荐人手维护的配置用它。

---

## 4. 核心配置详解

### 4.1 最小配置

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"]
}
```

两行即可启用。`config:recommended` 是官方推荐 preset，展开后包含：Dependency Dashboard、语义化提交前缀、忽略 modules 和 tests 目录、monorepo 包分组（`group:monorepos`）、社区推荐分组、merge confidence 徽章、自动替换规则（`replacements:all`）、已知问题规避（`workarounds:all`），以及 GitHub/GitLab/Gitea/Forgejo 等各平台的 digest 变更日志辅助——完整清单可在 [presets 文档](https://docs.renovatebot.com/presets-default/)查看。

### 4.2 生产配置示例

下面是一个仓库级 `renovate.json5` 示例。先说三个**写配置前必须知道的边界**：

1. **仓库级配置里放不了自托管选项**。`platform`、`token`、`repositories`、`autodiscover` 这些属于 self-hosted 配置（写在托管方的 config 文件或环境变量里），放进 `renovate.json` 不会生效。
2. **旧字段名已失效**。`pinVersions` 已被移除（官方迁移规则：`true` 变 `rangeStrategy: "pin"`，`false` 变 `"replace"`，后者本来就是默认值）；`matchPackagePatterns`、`matchSourceUrlPrefixes` 已改名，现在统一用 `matchPackageNames` / `matchSourceUrls` 配通配符。
3. **`branchName` 和 `commitMessage` 不要整体覆盖**。这两个字段的官方文档都挂着弃用警告，建议改用它们的组成部分（`branchPrefix`、`branchTopic`、`commitMessagePrefix` 等）。

```json5
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"],
  "description": "生产环境 Renovate 配置示例",

  // ========== 调度 ==========
  "timezone": "Asia/Shanghai",
  "schedule": ["after 10pm every weekday", "every weekend"],

  // ========== PR 策略 ==========
  "separateMajorMinor": true,     // major 更新单独开 PR
  "separateMinorPatch": false,    // minor 和 patch 合在一起
  "labels": ["dependencies"],

  // ========== 限流 ==========
  "prHourlyLimit": 3,             // 默认 2，按团队审 PR 的吞吐调整
  "prConcurrentLimit": 10,        // 同时打开的 PR 上限（默认 10）

  // ========== 自动合并 ==========
  "automerge": false,             // 建议先全局关闭，按规则单独打开

  // ========== 分支命名 ==========
  "branchPrefix": "renovate/",    // 默认值，写出来是为了明确
  "additionalBranchPrefix": "",   // 在 branchPrefix 之后追加的前缀

  // ========== 分规则 ==========
  "packageRules": [
    {
      "matchDatasources": ["docker"],
      "schedule": ["every weekend"],
      "addLabels": ["docker-updates"]
    },
    {
      // glob 通配：@nestjs 作用域全部
      "matchPackageNames": ["@nestjs/*"],
      "groupName": "NestJS packages",
      "schedule": ["every monday"]
    },
    {
      // 正则匹配：/斜杠包裹/，^锚定开头，覆盖 eslint 及其插件
      "matchPackageNames": ["/^eslint/"],
      "groupName": "ESLint related packages",
      "addLabels": ["tooling"]
    },
    {
      // 精确名单直接列举
      "matchPackageNames": ["prettier", "stylelint"],
      "automerge": true,
      "addLabels": ["tooling"]
    },
    {
      // 所有 major 更新：单独 label + 大版本审批
      "matchUpdateTypes": ["major"],
      "addLabels": ["breaking-change"],
      "dependencyDashboardApproval": true
    }
  ],

  // ========== 私有注册表 ==========
  "hostRules": [
    {
      "matchHost": "npm.mycompany.com",
      "token": "process.env.NPM_TOKEN"
    }
  ],

  // ========== 自定义 manager ==========
  "customManagers": [
    {
      "customType": "regex",
      "managerFilePatterns": ["/(^|/)requirements\\.txt$/"],
      "matchStrings": [
        "renovate: depName=(?<depName>\\S+)( versioning=(?<versioning>\\S+))?\\s+\\S+==(?<currentValue>\\S+)"
      ],
      "datasourceTemplate": "pypi"
    }
  ],

  // ========== 仪表板 ==========
  "dependencyDashboard": true,
  "dependencyDashboardTitle": "🤖 Dependency Dashboard",

  // ========== 忽略 ==========
  "ignoreDeps": ["moment"]
}
```

> 💡 `token: "process.env.NPM_TOKEN"` 是官方约定的写法：Renovate 会在运行时把 `process.env.XXX` 替换为环境变量值，避免把令牌明文提交进仓库。

`customManagers` 的要点：它用 RE2 正则引擎（不支持反向引用和 lookahead），用**命名捕获组**（`(?<depName>...)`、`(?<currentValue>...)`）向 Renovate 传递字段，`depName` 与 `currentValue` 必须在同一条 matchStrings 里匹配到（官方示例正是靠 `\s+` 跨行衔接）；如果用了 `enabledManagers` 限定范围，记得把 `custom.regex` 加进去。上面的例子对应这样的文件，能自动更新版本号：

```
# renovate: depName=django
django==5.0
```

### 4.3 核心配置速查

默认值全部对齐 44.x 源码（`lib/config/options/index.ts`）：

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | boolean | `true` | 是否启用 Renovate |
| `schedule` | array | `["at any time"]` | 允许创建更新分支的时间窗口 |
| `timezone` | string | UTC | IANA 时区名，影响 schedule 计算 |
| `automerge` | boolean | `false` | 满足条件时自动合并 |
| `automergeType` | string | `"pr"` | `pr` / `branch` / `pr-comment` |
| `automergeStrategy` | string | `"auto"` | `auto` / `fast-forward` / `merge-commit` / `rebase` / `rebase-merge` / `squash`；仅 azure、bitbucket、forgejo、gitea、github 平台支持 |
| `labels` | array | `[]` | PR 标签（**替换式**：多处设置时后者覆盖前者） |
| `addLabels` | array | `[]` | 追加式标签，与 `labels` 叠加 |
| `assignees` / `reviewers` | array | `[]` | PR 负责人/审核人，填平台有效用户名（GitHub 支持团队 `team:名称`） |
| `separateMajorMinor` | boolean | `true` | major 与 minor/patch 分开分支 |
| `separateMinorPatch` | boolean | `false` | minor 与 patch 再分开 |
| `pinDigests` | boolean | `false` | Docker 镜像固定到 SHA256 摘要 |
| `vulnerabilityAlerts` | object | **默认启用** | 安全修复策略对象，见 §6.8 |
| `dependencyDashboard` | boolean | `false` | 底层默认关；`config:recommended` 已打开它 |
| `dependencyDashboardApproval` | boolean | `false` | PR 创建前需在 Dashboard 手动批准 |
| `ignoreDeps` | array | `[]` | 忽略的依赖 |
| `prConcurrentLimit` | integer | `10` | 同时打开的 PR/分支上限，`0` 为不限 |
| `branchConcurrentLimit` | integer | `null` | 默认继承 `prConcurrentLimit` |
| `prHourlyLimit` | integer | `2` | 每小时新建 PR 上限，`0` 为不限 |
| `commitHourlyLimit` | integer | `0` | 每小时提交上限，`0` 为不限 |
| `customManagers` | array | `[]` | 自定义 manager 规则 |
| `extends` | array | `[]` | 继承的 preset |
| `includePaths` / `excludePaths` | array | `[]` | 只处理 / 排除的路径 |
| `rebaseWhen` | string | `"auto"` | 分支 rebase 时机，见 §7.3 |

---

## 5. 支持的平台与语言

### 5.1 代码托管平台

官方 README 的平台列表（2026-09-29 口径）：

| 平台 | 支持情况 |
|------|----------|
| **GitHub**（.com & Enterprise Server） | ✅ 完全支持 |
| **GitLab**（.com & CE/EE） | ✅ 完全支持 |
| **Bitbucket Cloud** | ✅ 完全支持 |
| **Bitbucket Server / Data Center** | ✅ 完全支持 |
| **Azure DevOps** | ✅ 完全支持 |
| **Gitea** | ✅ 完全支持 |
| **Forgejo** | ✅ 完全支持 |
| **AWS CodeCommit** | ⚠️ 实验性（AWS 已对新客户关闭该服务） |
| **Gerrit** | ⚠️ 实验性 |
| **SCM-Manager** | ⚠️ 实验性 |

### 5.2 语言与包管理器

官方口径是 "over 90 different package managers"，文档站的 [manager 列表](https://docs.renovatebot.com/modules/manager/)实际收录 119 个条目（2026-09-29 实测）。常见的一些：

| 语言 / 平台 | manager | 包文件 |
|------|------|------|
| JavaScript / Node.js | npm, Yarn, pnpm | package.json |
| Python | pip-compile, pipenv, poetry, pdm | requirements*.txt, pyproject.toml 等 |
| Ruby | bundler | Gemfile |
| Go | gomod | go.mod |
| Rust | cargo | Cargo.toml |
| Java | gradle, maven | build.gradle, pom.xml |
| .NET | nuget | *.csproj, *.fsproj 等 |
| PHP | composer | composer.json |
| Swift | swift | Package.swift |
| Dart | pub | pubspec.yaml |
| Elixir | mix | mix.exs |
| Docker | dockerfile, docker-compose | Dockerfile, compose 文件 |
| Kubernetes | helmfile, kustomize, helm-values | 各类 manifest |
| Terraform | terraform, terragrunt | *.tf |
| CI 配置 | github-actions, gitlabci, azure-pipelines | workflow 文件 |

每个 manager 匹配哪些文件、有什么特殊配置，查官方 manager 文档最可靠。

---

## 6. 进阶用法与实践建议

### 6.1 分组更新（Grouped Updates）

把多个相关依赖打进同一个 PR，减少 CI 消耗和审阅噪音。`config:recommended` 已内置 `group:monorepos`（monorepo 多包联动）和 `group:recommended`（社区维护的常用分组，比如 eslint 全家桶、jest 生态）。自定义分组用 `groupName`：

```json
{
  "packageRules": [
    {
      "matchPackageNames": ["/^eslint/"],
      "groupName": "ESLint related packages"
    }
  ]
}
```

`matchPackageNames` 支持三种写法：精确名（`"eslint"`）、glob 通配（`"@nestjs/*"`）、正则（`"/^eslint/"`，斜杠包裹）。

### 6.2 调度（Schedule）：先理解它的真实语义

一个常见误解：`schedule` 控制 Renovate "什么时候运行"。实际上 Renovate 是被动的——它按管理员的节奏周期性运行（Mend App 对无活动的仓库约每 3 小时检查一次），`schedule` 只是在**每次运行时判断"现在是否允许执行更新"**。官方 Known Limitations 页面的说法是：定时任务要发生，需要"Renovate 运行了"和"当前时间落在配置的窗口内"两件事同时成立。

两个推论：

- 仓库级配置无法让 Renovate 跑得比托管方更频繁；
- Mend App 用户把窗口设得太窄（比如 1 小时）可能一次都赶不上，官方建议**窗口至少 3-4 小时**。

默认时区是 UTC，配了中文团队就显式设 `timezone`：

```json
{
  "schedule": ["after 8pm on friday", "every weekend"],
  "timezone": "Asia/Shanghai"
}
```

### 6.3 Dependency Dashboard：集中控制台

`config:recommended` 默认会在仓库里开一个 Dependency Dashboard issue，列出 Renovate 管理的所有更新（待定、打开、已关闭、出错）。它不只是报表：

- 在 issue 里勾选 checkbox，可以**按需触发**某个被限流或被 schedule 挡住的更新；
- 一键 rebase / retry 多个 PR；
- 重新打开被你关掉的重大更新 PR；
- `dependencyDashboardApproval: true` 时，所有 PR 创建前都要在 Dashboard 批准——新仓库接入期防止 PR 洪水的有效手段。

对重大更新单独设审批是官方文档给的标准做法：

```json
{
  "major": {
    "dependencyDashboardApproval": true
  }
}
```

### 6.4 私有包与凭据（hostRules）

私有注册表和内部 Git 仓库的认证统一走 `hostRules`。字段只有这些：`hostType`、`matchHost`、`token`、`username`、`password`、`timeout`、`enabled`、`insecureRegistry`——没有 `authType`、没有 `authToken`。

```json
{
  "hostRules": [
    {
      "matchHost": "npm.mycompany.com",
      "token": "process.env.NPM_TOKEN"
    }
  ]
}
```

`matchHost` 填域名（或带端口的完整地址），多条规则命中时按"只配 `hostType` > 只配 `matchHost` > 两者都配"的优先级，同级按 `matchHost` 长度取最具体的。要整体禁用某个源的请求，用 `:disableHost(registry.example.com)` preset 或在规则里设 `"enabled": false`。

### 6.5 内部依赖自动合并

公司内部多仓库共享内部包时，可以按源 URL 匹配并自动合并。注意字段名是 `matchSourceUrls`（旧的 `matchSourceUrlPrefixes` 已改名），支持通配：

```json
{
  "packageRules": [
    {
      "matchSourceUrls": ["https://github.com/mycompany/*"],
      "automerge": true,
      "automergeType": "branch"
    }
  ]
}
```

`automergeType: "branch"` 表示不开 PR、直接把更新分支合进基线，适合纯内部依赖的低风险场景。

### 6.6 Docker 镜像摘要固定

生产环境把镜像固定到 SHA256 摘要可以保证不可变性，防供应链投毒：

```json
{
  "pinDigests": true
}
```

效果是把 `nginx:1.27` 变成 `nginx:1.27@sha256:abc123...`。更进一步的官方姿势是 `config:best-practices` preset——它在 `config:recommended` 之上加了 `docker:pinDigests`、GitHub Action 摘要固定（`helpers:pinGitHubActionDigests`）、npm 最低发布龄期（`security:minimumReleaseAgeNpm`）等强化项，适合想一步到位的团队。

### 6.7 配置预设（Presets）

preset 机制类似 ESLint 的 `extends`，嵌套继承，冲突时**数组里靠后的赢**。常用的内置 preset：

| Preset | 说明 |
|--------|------|
| `config:recommended` | 官方推荐基线（含 Dashboard、monorepo 分组、merge confidence 徽章等 15 项） |
| `config:best-practices` | 在 recommended 之上加摘要固定、发布龄期等安全强化 |
| `config:js-app` / `config:js-lib` | JS 应用 / 库的默认配置（区别在 devDependencies 的 pin 策略） |
| `mergeConfidence:all-badges` | 打开全部 merge confidence 徽章（老的 `github>whitesource/merge-confidence:beta` 已迁移至此） |
| `:automergeLinters` / `:automergeTypes` | 自动合并 linter / 类型定义包 |
| `:disableMajor` | 禁用 major 更新 |
| `security:only-security-updates` | 只开安全修复 PR |
| `workarounds:all` | 已知上游问题的规避规则（`config:recommended` 已含，无需重复添加） |

**自定义 preset 的分发方式**：放在 Git 仓库里（与 Renovate 运行的平台同源，如 `github>myorg/renovate-config`），或放在任意 HTTP 服务器上按 URL 引用。**npm 包分发已被官方弃用**，文档明确计划在未来的大版本里移除——新配置别再用 `npm>xxx` 引用。

### 6.8 安全漏洞修复（vulnerabilityAlerts）

`vulnerabilityAlerts` 是一个**默认启用的配置对象**（想关掉要显式写 `"vulnerabilityAlerts": { "enabled": false }`），它读取 GitHub 的 Dependabot alerts 并自动开修复 PR。前提条件：仓库开启 Dependency graph 和 Dependabot alerts，Mend App 需要有 Dependabot alerts 的读权限。

三个值得知道的默认行为：

- **修复策略 `lowest`**：漏洞在 1.1.0 修复、最新版是 1.2.0 时，Renovate 只把版本提到 1.1.0——修复漏洞的最小变更，把功能升级的决定权留给你；
- **插队机制**：安全修复 PR 绕过 `prHourlyLimit`、`schedule` 等全部限流（官方原话 "vulnerability alerts skip the line"）；
- 如果确实要关掉限流插队之外的某些行为，可以在 `vulnerabilityAlerts` 对象里单独设 `prConcurrentLimit`，安全修复有自己的并发预算。

只想收安全修复、不要常规更新的仓库，用 `security:only-security-updates` preset。

---

## 7. 常见问题与故障排查

### 7.1 Renovate 没有创建 PR

按顺序排查：

1. **onboarding PR 合并了吗？** 首次接入时 Renovate 会开一个 "Configure Renovate" PR，合并它之前不会做任何事。直接关掉它等于退出（可逆：改名重开或提交一个配置文件即可重新触发）。
2. **schedule 窗口内吗？** 记住 schedule 只在 Renovate 运行的瞬间做判断，窗口太窄（<3 小时）可能永远赶不上运行时机。
3. **依赖被排除了吗？** 检查 `ignoreDeps`、`excludePaths`、`enabled: false`。
4. **自托管的话，用 `dryRun` 分段排查**：先 `"extract"` 看能不能扫出依赖，再 `"lookup"` 看有没有可用更新——日志在 debug 级别会输出每个依赖的判定结果。
5. **Mend App 用户**：在 Dashboard issue 里手动勾选 checkbox 可以绕过限流立即触发，以此区分"被限流"还是"没识别到更新"。

### 7.2 PR 太多、CI 扛不住

三类旋钮，从粗到细：

```json
{
  "prHourlyLimit": 2,
  "prConcurrentLimit": 5,
  "branchConcurrentLimit": 5
}
```

- `prHourlyLimit`（默认 2）：控制**新建** PR 的速率；
- `prConcurrentLimit`（默认 10）：控制同时打开的 PR 总量；
- `branchConcurrentLimit`（默认继承 `prConcurrentLimit`）：分支层面的并发上限。

再配合 §6.1 分组和 §6.3 审批模式，新仓库接入期的洪水基本可控。

### 7.3 锁文件冲突与 rebase

分支落后于基线时，Renovate 的 rebase 行为由 `rebaseWhen` 控制，默认 `auto`：如果仓库开了 automerge 或要求 PR 必须最新，会自动保持分支更新（`behind-base-branch`）；否则**只在有冲突时 rebase**（`conflicted`）。

锁文件冲突最常见的解法是让 Renovate 重做分支：Renovate 分支落后或冲突时，Dependency Dashboard（及对应 PR 描述）会出现 "rebase/retry" checkbox，勾选它，Renovate 会基于最新基线重新执行更新命令、重新生成锁文件。官方文档对 Dashboard 这项能力的原话是 "Rebase/retry multiple PRs without having to open each individually"。

顺带澄清一个常见张冠李戴：`postUpdateOptions`（如 `gitleaks`、`npmDedupe`）是更新**之后**的额外处理步骤（密钥扫描、依赖去重），跟冲突解决没有关系。

### 7.4 认证问题

私有源 401/403 时，检查 `hostRules` 的三个高频错误：

- 字段名写错：是 `token`，不是 `authToken`；
- `matchHost` 写法过繁：填域名即可（`npm.mycompany.com`），需要匹配端口或路径时再带上（不带协议头时默认按 `https` 处理，官方文档原话）；
- 令牌用了明文：改用 `process.env.MY_TOKEN` 写法，运行时注入。

---

## 8. 总结与推荐配置

### 8.1 快速入门

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"]
}
```

装 App、合并 onboarding PR、等 Dashboard 出现，三步完成。有别的需求都在这个文件上叠加。

### 8.2 生产环境推荐

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:best-practices"],
  "timezone": "Asia/Shanghai",
  "schedule": ["after 10pm every weekday", "every weekend"],
  "prHourlyLimit": 3,
  "prConcurrentLimit": 10,
  "packageRules": [
    {
      "matchUpdateTypes": ["major"],
      "addLabels": ["breaking-change"],
      "dependencyDashboardApproval": true
    },
    {
      "matchPackageNames": ["eslint", "prettier", "stylelint"],
      "automerge": true,
      "addLabels": ["tooling"]
    },
    {
      "matchDatasources": ["docker"],
      "pinDigests": true,
      "addLabels": ["docker"]
    }
  ]
}
```

要点：`config:best-practices` 已经包含 `config:recommended` 和 `workarounds:all`，不要重复往 `extends` 里塞；major 更新走 Dashboard 审批而不是直接 automerge；工具类依赖（linter、formatter）风险低，放心 automerge。

### 8.3 核心要点速记

1. **先选运行方式**：Mend App（零运维）、自托管 CE（免费、可管内部包）、CI 流水线（GitHub Action / Renovate Runner）；
2. **配置文件是查找顺序不是优先级**：`renovate.json` 在根目录就够了，`package.json` 方式已弃用；
3. **`extends` 是捷径**：`config:recommended` 起步，进阶换 `config:best-practices`；
4. **`automerge` 需谨慎**：Renovate 每次运行最多自动合并 1 个分支，且只合与基线同步的分支——CI 足够可靠再开；
5. **schedule 是过滤不是调度**：窗口至少留 3-4 小时；
6. **Dashboard 是控制台**：审批、触发、rebase 都在这里，major 更新建议单独设审批；
7. **旧字段名是坑**：`pinVersions`、`matchPackagePatterns`、`matchSourceUrlPrefixes`、`config:base` 在 44.x 都已失效，网上抄配置时留意。

---

## 参考来源与口径说明

- 版本基线：Renovate **44.x**，GitHub API 核实于 2026-09-29（最新 release 44.118.1，当天发布 4 个版本；stars 22,623、forks 3,338、AGPL-3.0、TypeScript）。Renovate 发版频率极高，阅读时请以 [releases 页](https://github.com/renovatebot/renovate/releases)为准。
- 配置默认值：源码 `lib/config/options/index.ts`（main 分支，2026-09-29）；字段改名与迁移规则见 `lib/config/migrations/custom/`（`pinVersions`→`rangeStrategy` 等）。
- `config:recommended` 的 15 项构成与 `config:best-practices` 定义：`lib/config/presets/internal/config.preset.ts`。
- 90+ 包管理器口径：官方 README 原话 "Supports over 90 different package managers"；119 个条目数为 docs.renovatebot.com/modules/manager/ 页面实测。
- 平台支持（含实验性标注）：官方 README Platforms 一节。
- Dependabot 对比数据：[官方 bot comparison 页](https://docs.renovatebot.com/bot-comparison/)。
- schedule 语义与 Mend App 检查周期、automerge 每次最多合并 1 个分支：[Known Limitations](https://docs.renovatebot.com/known-limitations/)。
- onboarding 流程、配置文件查找顺序、package.json 弃用声明：[Installing and onboarding](https://docs.renovatebot.com/getting-started/installing-onboarding/)。
- hostRules 字段与优先级、vulnerabilityAlerts 默认行为、lock file maintenance 默认计划：[Configuration Options](https://docs.renovatebot.com/configuration-options/) 与 FAQ。
- customManagers 命名捕获组与 RE2 限制：`lib/modules/manager/custom/regex/readme.md`。
- npm preset 分发弃用声明：[Shareable Config Presets](https://docs.renovatebot.com/config-presets/)。
