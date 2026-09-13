+++
github_repo = "apps/dependabot"
source_key = "gh:apps/dependabot"
date = '2026-05-17T00:00:00+08:00'
draft = false
title = 'GitHub Dependabot：自动化依赖更新'
slug = 'github-dependabot-automated-dependency-updates-guide'
description = 'Dependabot 实操指南：两条更新链路的分工、dependabot.yml 配置、安全更新定制、auto-merge 与 CI 集成，以及 PR 过多时的收敛办法。'
categories = ['技术笔记']
tags = ['GitHub', 'DevOps', '教程', '依赖管理']
+++

# GitHub Dependabot：自动化依赖更新

第三方依赖是漏洞的主要入口，手动追踪更新既耗时又容易遗漏——Log4Shell 爆发时，不少项目就栽在一个长期没人更新的 log4j 老版本上。

Dependabot（[github.com/apps/dependabot](https://github.com/apps/dependabot)）是 GitHub 内置的依赖更新工具，2019 年被 GitHub 收购后成为平台原生功能。它以 Pull Request（PR）的形式自动提交更新：安全补丁和版本迭代都走可审查的 PR 流程，而不是让你盯着 CVE 公告手动改版本号。

## 学习目标

读完后你应当能独立完成这几件事：

1. 分清 Version Updates 和 Security Updates 两条链路的触发机制，知道各自的开关在哪里
2. 写出适合团队规模的 `dependabot.yml`，包括分组策略和忽略规则
3. 判断什么时候用 Dependabot、什么时候换 Renovate
4. 为 Dependabot PR 配好 CI 验证和 auto-merge，且不踩 `GITHUB_TOKEN` 权限的坑
5. 排查 Dependabot 不工作、PR 过多这类常见问题

## 目录

1. [Dependabot 是什么](#1-dependabot-是什么)
2. [工作原理详解](#2-工作原理详解)
3. [完整配置：dependabot.yml](#3-完整配置dependabotyml)
4. [Security Updates 进阶配置](#4-security-updates-进阶配置)
5. [Version Updates 实践建议](#5-version-updates-实践建议)
6. [与 CI/CD 流水线的集成](#6-与-cicd-流水线的集成)
7. [常见问题（FAQ）](#7-常见问题faq)
8. [替代方案对比](#8-替代方案对比)
9. [自检清单](#9-自检清单)
10. [参考链接](#10-参考链接)
11. [自测题](#自测题)
12. [练习](#练习)
13. [进阶路径](#进阶路径)

---

## 1. Dependabot 是什么

Dependabot 由 GitHub 官方维护，随平台一起运行，不需要安装第三方应用。它做四件事：

- **监控** 仓库里的依赖清单和 lock 文件（如 `package.json`、`Gemfile`、`requirements.txt`、`go.mod`）
- **检测** 可用的新版本和已知安全漏洞
- **自动创建** PR，附上版本变化和上游的 release notes / changelog 链接
- **可选地** 自动合并（auto-merge）经过验证的更新

Dependabot 分为两大更新类型，触发机制完全不同：

| 类型 | 说明 | 触发方式 |
|------|------|----------|
| **Version Updates** | 检测依赖新版本（功能迭代） | 按 `dependabot.yml` 的 schedule 执行，也可手动触发 |
| **Security Updates** | 修复存在已知漏洞的依赖 | 仓库设置里的开关；GitHub Advisory Database 收录漏洞后自动建 PR |

### 支持的生态

`dependabot.yml` 中的 `package-ecosystem` 使用生态标识，而不是包管理器名字。两个容易写错的点：npm 和 Yarn 共用 `npm` 这一个生态（Yarn 没有独立标识）；Cargo 的清单文件是 `Cargo.toml`，不是 `Cargo.lock`。

| 生态标识 | 包管理器 / 清单文件 |
|----------|---------------------|
| `bundler` | Ruby Bundler（`Gemfile`） |
| `cargo` | Rust Cargo（`Cargo.toml`、`Cargo.lock`） |
| `composer` | PHP Composer（`composer.json`） |
| `docker` | Dockerfile、Compose 文件中的基础镜像 |
| `github-actions` | 工作流中 `uses:` 引用的 Action |
| `gomod` | Go modules（`go.mod`） |
| `gradle` | Java Gradle（`build.gradle`） |
| `maven` | Java Maven（`pom.xml`） |
| `mix` | Elixir Hex（`mix.exs`） |
| `npm` | npm、Yarn、pnpm（`package.json` 与各类 lock 文件） |
| `nuget` | .NET NuGet（`.csproj` 等工程文件） |
| `pip` | Python pip、pipenv、poetry、uv（`requirements.txt`、`pyproject.toml` 等） |
| `pub` | Dart/Flutter pub（`pubspec.yaml`） |

> ⚠️ 注意：安全更新只针对清单或 lock 文件里声明的依赖触发。Yarn 项目统一写 `package-ecosystem: "npm"`，照着"Yarn"另写一个生态会导致配置无效。

---

## 2. 工作原理详解

### 2.1 Version Updates 流程

```text
┌──────────────────────────────────────────────────┐
│  Dependabot 引擎（GitHub 云端）                   │
│                                                  │
│  1. 读取仓库默认分支上的 .github/dependabot.yml   │
│  2. 按 schedule 扫描各生态的清单文件              │
│  3. 查询对应 registry（npm、PyPI 等）             │
│  4. 解析出可用的更新版本                          │
│  5. 生成含 changelog / release notes 的 PR       │
│  6. 等待 review，或按配置自动合并                 │
└──────────────────────────────────────────────────┘
```

几个影响日常使用的行为细节：

- **PR 数量上限**：`open-pull-requests-limit` 控制同时打开的版本更新 PR 数，默认 5。补足了配额就不建新 PR，直到有 PR 被合并或关闭
- **分组策略**：`groups` 可把同一生态的多个依赖合并进一个 PR，这是控制 PR 洪水的第一手段（见 §5.1）
- **更新范围**：`directory`（或支持 glob 的 `directories`）配合 `package-ecosystem`，monorepo 里可以按子目录分别控制
- **版本约束**：解析遵循各生态的版本规则，`ignore` 规则可以把某些依赖或某类更新挡在外面

### 2.2 Security Updates 流程

```text
GitHub Advisory Database 收录新漏洞
            │
            ▼
    GitHub 检测依赖图，标记受影响的仓库并生成 Dependabot alert
            │
            ▼
    Dependabot 尝试升级到包含补丁的最低版本，创建 PR
    （标题以 🔐 开头，默认带 dependencies、security 标签）
            │
            ▼
    PR 合并后对应的 alert 自动关闭
```

安全更新和版本更新是两条独立链路：前者由仓库设置控制，不依赖 `dependabot.yml`；后者必须写配置文件才会运行。Dependabot 给安全 PR 选的是**包含补丁的最低版本**，而不是最新版——它只求消除漏洞，不顺便升级。

还有一点区别值得知道：npm 生态里，为了修复一个间接依赖，Dependabot 可以连父依赖一起更新甚至删除多余的子依赖；其他生态做不到这一点，间接依赖需要父依赖同时更新时，Dependabot 会放弃并在 alert 上报错。

### 2.3 Pull Request 内容

每个 Dependabot PR 通常包含：

1. 版本变化（旧版本 → 新版本）
2. 上游项目的 release notes 或 changelog 摘要（上游在 GitHub 上发布 release 时）
3. PR 作者为 `dependabot[bot]`，commit 由 Dependabot 签名，显示为 Verified
4. CI 状态——Dependabot PR 会正常触发仓库的 workflow（权限限制见 §6）

---

## 3. 完整配置：dependabot.yml

配置文件放在仓库的 `.github/dependabot.yml`。路径固定，放别处不生效。

### 3.1 最小配置

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
```

这会每周检查一次项目根目录的 `package.json` 和 lock 文件，有更新就建 PR。

### 3.2 完整生产级配置

```yaml
# .github/dependabot.yml
version: 2

updates:
  # ── npm：前端依赖 ──────────────────────────────
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "daily"
      time: "09:00"
      timezone: "Asia/Shanghai"
    open-pull-requests-limit: 10
    groups:
      production-dependencies:
        dependency-type: "production"
        update-types:
          - "version-update:semver-major"
      development-dependencies:
        dependency-type: "development"
        update-types:
          - "version-update:semver-minor"
          - "version-update:semver-patch"
    ignore:
      - dependency-name: "lodash"
        versions: ["4.x"]
      - dependency-name: "react"
        update-types: ["version-update:semver-major"]
    commit-message:
      prefix: "deps"
      include: "scope"
    labels:
      - "dependencies"
      - "npm"

  # ── GitHub Actions ──────────────────────────────
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    commit-message:
      prefix: "ci"
    labels:
      - "ci"

  # ── Go modules ──────────────────────────────────
  - package-ecosystem: "gomod"
    directory: "/"
    schedule:
      interval: "weekly"
    ignore:
      - dependency-name: "golang.org/x/*"
        update-types: ["version-update:semver-major"]
    commit-message:
      prefix: "deps"
    labels:
      - "dependencies"
      - "go"

  # ── Python pip ──────────────────────────────────
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    commit-message:
      prefix: "py"
    labels:
      - "dependencies"
      - "python"

  # ── Docker 基础镜像 ─────────────────────────────
  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "docker"
```

### 3.3 配置字段详解

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `package-ecosystem` | string | 生态标识，必填 | `"npm"`, `"pip"`, `"gomod"` |
| `directory` / `directories` | string / list | 清单文件所在路径；`directories` 支持 glob（如 `**/*`），适合 monorepo | `"/frontend"` |
| `schedule.interval` | string | 检查频率，必填。GitHub.com 支持 `daily`、`weekly`、`monthly`、`cron`；`quarterly` 等更长周期仅 GitHub Enterprise Server 3.19+ 可用 | `"weekly"` |
| `schedule.time` | string | 触发时间（24 小时制），仅 daily/weekly 有效；不设则随机分配 | `"09:00"` |
| `schedule.timezone` | string | 时区（IANA 格式），不设按 UTC | `"Asia/Shanghai"` |
| `schedule.day` | string | weekly 时指定星期几 | `"monday"` |
| `open-pull-requests-limit` | int | 同时打开的版本更新 PR 上限，默认 5，`0` 表示关闭版本更新 | `5` |
| `groups` | object | 依赖分组，可指定作用于版本更新还是安全更新 | 见上方与 §5.1 |
| `ignore` | list | 忽略特定依赖、版本或更新类型 | 见 §5.2 |
| `allow` | list | 只更新白名单内的依赖 | 见 §5.4 |
| `commit-message.prefix` | string | commit message 前缀 | `"deps"` |
| `commit-message.include` | string | `"scope"` 在前缀后以括号附加范围 | `"scope"` |
| `labels` | list | 自动添加的 PR 标签（仓库需已存在） | `["dependencies"]` |
| `reviewers` | list | 版本更新 PR 的审核人；安全更新 PR 建议改用 CODEOWNERS（见 §4） | `["team:frontend"]` |
| `registries` | list | 引用顶层 `registries` 定义的私有源，`"*"` 表示全部 | 见 §4.3 |

### 3.4 commit-message 选项

```yaml
commit-message:
  prefix: "deps"                  # 每条 commit 以 "deps:" 开头，如 "deps: Bump lodash from 4.17.15 to 4.17.21"
  prefix-development: "dev-deps"  # 开发依赖用另一个前缀
  include: "scope"                # 前缀后以括号附加范围信息
```

PR 标题沿用首条 commit message，所以这里的设置同样决定 PR 标题长什么样。对提交规范有要求的团队（如 Conventional Commits），`prefix` 是最低成本的接入方式。

---

## 4. Security Updates 进阶配置

安全更新和版本更新是两条独立链路，先把两件事分清：

- **开关在仓库设置里，不依赖 `dependabot.yml`。** 在 Settings → Code security and analysis 中开启 `Dependabot alerts` 和 `Dependabot security updates` 后，漏洞收录即自动建 PR，没有 schedule 可言。
- **`dependabot.yml` 的大多数选项同时作用于安全 PR**：`labels`、`assignees`、`commit-message`、`groups`、`ignore`、`allow` 都会改变安全 PR 的形态，`target-branch` 除外。但有两个例外要记住：安全 PR **不计入** `open-pull-requests-limit`（这个数字只管版本更新）；安全 PR 的审核人官方推荐用 **CODEOWNERS** 文件（`.github/CODEOWNERS` 声明路径与负责团队的映射）管理，而不是配置里的 `reviewers`。
- **能不能建 PR 取决于能否解析出修复版本。** 依赖必须处于受影响范围、且存在不破坏依赖图的升级路径；解析不出来时只有 alert，没有 PR。

### 4.1 只收安全更新，不跑例行版本更新

目标：漏洞来了能收到修复 PR，但不想要每周的例行升级 PR。按是否需要定制 PR，有两种做法。

不需要定制，就完全不用写 `dependabot.yml`：仓库设置里开启 alerts 和 security updates 即可。

需要给安全 PR 打标签、分组或使用私有注册表，就写生态条目，并用 `open-pull-requests-limit: 0` 关闭版本更新：

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "daily"
    open-pull-requests-limit: 0   # 版本更新一个 PR 也不开，只剩安全更新
    labels: ["npm dependencies"]
    assignees: ["alice"]
```

`0` 只限制版本更新，安全 PR 不受此限额影响，会照常出现——这正是"条目仍在、只留安全更新"的官方推荐写法。注意生态条目里写了 `schedule: interval: "daily"` 并不会让安全更新天天跑，schedule 只对版本更新生效；它的作用是保留条目，让 labels 等定制有落点。

> 不要试图用 `allow` 的 `update-types: ["security"]` 来"只收安全更新"——`update-types` 只接受 `version-update:semver-patch`、`version-update:semver-minor`、`version-update:semver-major` 三种值，`security` 不是合法取值。

### 4.2 分组作用于安全更新

`groups` 可以显式声明只服务哪一类更新。安全漏洞常常一次涉及同一框架的多个包，分组能把它们合成一个 PR：

```yaml
groups:
  golang-security:
    applies-to: security-updates
    patterns:
      - "golang.org*"
```

`applies-to` 取 `security-updates` 或 `version-updates`，不声明则两种都生效。

### 4.3 私有注册表支持

依赖来自私有 npm registry、Python index 或 Docker registry 时，先在顶层定义 `registries` 认证，再在对应 `updates` 条目里引用：

```yaml
version: 2
registries:
  private-npm:
    type: "npm-registry"
    url: "https://registry.mycompany.com"
    username: ${{ secrets.REGISTRY_USERNAME }}
    password: ${{ secrets.REGISTRY_PASSWORD }}
    replaces-base: true   # 用该地址替代生态默认的 registry

  private-pypi:
    type: "python-index"
    url: "https://pypi.mycompany.com/simple"
    username: ${{ secrets.PYPI_USERNAME }}
    password: ${{ secrets.PYPI_PASSWORD }}

updates:
  - package-ecosystem: "npm"
    directory: "/"
    registries:
      - private-npm
    schedule:
      interval: "weekly"
```

一个容易踩的坑：`${{ secrets.NAME }}` 里的 NAME 必须定义在 **Dependabot secrets**（Settings → Secrets and variables → Dependabot）里，而不是 Actions secrets——Dependabot 不读后者的存储。同名的两套 secrets 互相独立，配错了表现就是 Dependabot 一直拿不到认证。

---

## 5. Version Updates 实践建议

### 5.1 分组策略

不分组时，每个依赖的更新各占一个 PR，一个中型前端项目在第一次运行后可能同时冒出几十上百个 PR。按风险分组是第一道收敛手段：

```yaml
groups:
  # 生产依赖的大版本更新单独处理（风险更高，值得单独 review）
  major-production:
    dependency-type: "production"
    update-types:
      - "version-update:semver-major"
  # minor 和 patch 打包处理
  minor-patch-production:
    dependency-type: "production"
    update-types:
      - "version-update:semver-minor"
      - "version-update:semver-patch"
  # 开发依赖放一起
  development:
    dependency-type: "development"
```

也可以按依赖名分组（`patterns`，支持通配符），比如把一个框架的全部官方包合成一个 PR。

### 5.2 忽略策略

```yaml
ignore:
  # 完全忽略（永不需要更新）
  - dependency-name: "lodash"
  # 忽略特定版本
  - dependency-name: "axios"
    versions: ["0.21.0"]
  # 忽略某类更新（大版本由人手动跟进）
  - dependency-name: "react"
    update-types: ["version-update:semver-major"]
```

忽略 major 更新的合理场景：大版本通常伴随 breaking change，需要配合代码改造，不适合自动 PR。设一条 ignore，等团队准备好时再手动升级并删掉规则。

### 5.3 自动合并（Auto-Merge）

目标：patch 和 minor 更新在 CI 全绿后自动合入，人只看 major。

**第一步：允许 auto-merge**

仓库设置 Settings → General → Pull Requests 中勾选 `Allow auto-merge`。

**第二步：设置合并门槛**

在 branch protection rule（或 ruleset）中为默认分支配置 required status checks，保证"CI 通过"是硬条件，而不是碰运气：

```
Settings → Branches → Add branch rule（pattern: main）
  - Require a pull request before merging：决定是否必须有人批准
  - Require status checks to pass before merging：必开，选择 test、lint 等关键检查
```

"要求分支与主分支保持最新"这个选项要权衡：开启后每次主分支有新合入，等待中的 PR 都会重新触发 CI，队列容易堵；关闭则可能合入基于过期基线的更新。小团队建议先关。

**第三步：对 Dependabot PR 开启 auto-merge**

三种方式任选：

1. 在 PR 页面点一次 `Enable auto-merge`（有写权限的人都可以点，无需管理员）；
2. 用 workflow 批量处理，官方推荐的做法是配合 `dependabot/fetch-metadata` 判断更新类型后执行 `gh pr merge --auto`：

```yaml
# .github/workflows/dependabot-auto-merge.yml
name: Dependabot auto-merge
on: pull_request

permissions:
  contents: write
  pull-requests: write

jobs:
  dependabot:
    runs-on: ubuntu-latest
    if: ${{ github.event.pull_request.user.login == 'dependabot[bot]' }}
    steps:
      - name: Fetch metadata
        id: metadata
        uses: dependabot/fetch-metadata@v2
      - name: Enable auto-merge for patch and minor
        if: ${{ steps.metadata.outputs.update-type == 'version-update:semver-patch' || steps.metadata.outputs.update-type == 'version-update:semver-minor' }}
        run: gh pr merge --auto --merge "$PR_URL"
        env:
          PR_URL: ${{ github.event.pull_request.html_url }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

3. 通过 GraphQL API 的 `enablePullRequestAutoMerge` mutation，效果等同于界面上点按钮。

两个边界：如果仓库启用了 merge queue，`GITHUB_TOKEN` 无权把 PR 加入队列，需要换成有合并权限的 PAT 或 GitHub App token；如果 branch protection 要求人工批准，auto-merge 会在批准后自动完成合并——想真正零干预，就要给 Dependabot PR 配自动批准（`gh pr review --approve`）或放开这条规则。

> ⚠️ **注意**：auto-merge 的安全性完全由 CI 决定。测试覆盖不足时开启它，等于让破坏性更新直接进主干。宁可先只对 patch 放行。

### 5.4 使用 `allow` 精细控制

`allow` 在每个生态条目里只能写一次（并列多个条目，不要重复写 `allow:` 键），它和 `ignore` 分别从两端收窄范围：

```yaml
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    # 只跟进白名单里的依赖，未列出的一律不更新
    allow:
      - dependency-name: "lodash"
      - dependency-name: "axios"
```

按更新级别收窄则用 `ignore` 更直接（`update-types` 只接受 `version-update:semver-*` 三种值）：

```yaml
    ignore:
      - dependency-name: "*"
        update-types: ["version-update:semver-major"]  # 大版本手动处理
```

---

## 6. 与 CI/CD 流水线的集成

### 6.1 在 Dependabot PR 上运行测试

Dependabot PR 会正常触发 `pull_request` 事件的 workflow。把测试任务的触发条件限定为机器人 PR，避免干扰普通 PR 的流水线：

```yaml
# .github/workflows/dependabot-tests.yml
name: Dependabot Tests

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  test:
    if: ${{ github.event.pull_request.user.login == 'dependabot[bot]' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: npm test
```

判断是否为 Dependabot PR，用 `github.event.pull_request.user.login == 'dependabot[bot]'`。官方推荐这个写法而不是 `github.actor`——后者在 re-run 等场景下可能是手动触发者，判断会失效。

### 6.2 自动打标签和指派审核人

`GITHUB_TOKEN` 在 workflow 里默认是只读的，想改 PR 必须显式声明 `permissions`，否则 `gh pr edit` 会报 403：

```yaml
# .github/workflows/dependabot-label.yml
name: Dependabot PR Setup

on:
  pull_request:

permissions:
  contents: read
  pull-requests: write
  issues: write

jobs:
  setup:
    if: ${{ github.event.pull_request.user.login == 'dependabot[bot]' }}
    runs-on: ubuntu-latest
    steps:
      - name: Label PR
        run: |
          gh pr edit "$PR_URL" \
            --add-label "dependencies" \
            --add-label "automated-pr"
        env:
          PR_URL: ${{ github.event.pull_request.html_url }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

给安全 PR 分派审核人，优先用 CODEOWNERS 而不是 workflow：把 `package-lock.json`、`go.mod` 等清单文件交给对应团队 OWN，Dependabot 的 PR 就会自动请求他们审核，安全更新同样适用。

还有一条 secrets 的边界：Dependabot PR 触发的 workflow run 读不到 Actions secrets，能读到的是 Dependabot secrets。workflow 里需要凭据（比如跑集成测试连私有源）时，secret 要配在 Settings → Secrets and variables → Dependabot 下。

---

## 7. 常见问题（FAQ）

### Q1: Dependabot 没有工作，如何排查？

1. 确认 `.github/dependabot.yml` 存在于默认分支、YAML 语法有效、`package-ecosystem` 和 `directory` 与实际清单文件对得上（Yarn 写 `npm`，Cargo 清单写 `Cargo.toml`）
2. 确认仓库 Settings → Code security and analysis 中相关功能已开启——Dependabot 是平台内置功能，没有独立的"安装应用"步骤，找不到 Settings → Integrations → Dependabot 这样的菜单
3. 打开 Insights → Dependency graph → Dependabot 面板，每次检查的结果和错误信息都在 last checked 一栏
4. 生态条目里用到的 `labels` 必须已存在于仓库，标签不存在时 PR 会创建失败

```bash
# 验证 YAML 语法（本地）
python3 -c "import yaml; yaml.safe_load(open('.github/dependabot.yml'))"
```

### Q2: Dependabot PR 太多，如何减少？

按见效程度排序：

1. 启用 `groups` 分组，把同生态的依赖合并成少量 PR（见 §5.1）
2. 用 `ignore` 排除 major 更新和确认不跟的依赖
3. 把更新频率从 `daily` 降到 `weekly`
4. `open-pull-requests-limit` 控制并发上限（超过配额时新更新会排队而不是丢弃）

### Q3: 如何只接收安全更新？

见 §4.1：不写 `dependabot.yml` 时安全更新照常工作；要保留标签等定制，就用 `open-pull-requests-limit: 0` 关闭版本更新。`update-types: ["security"]` 不是合法配置，写上无效。

### Q4: 如何更新 GitHub Actions 自身？

```yaml
- package-ecosystem: "github-actions"
  directory: "/"
  schedule:
    interval: "weekly"
  open-pull-requests-limit: 3
```

配置后，工作流里 `uses:` 引用的 Action 有新版本时会收到 PR。这是低成本高收益的配置，建议所有仓库都加。

### Q5: 企业私有包注册表如何配置？

完整配置和 secrets 的存放位置见 §4.3。要点重复一遍：`${{ secrets.* }}` 引用的是 Dependabot secrets，不是 Actions secrets。

### Q6: Dependabot PR 的 CI 失败了怎么办？

1. 先看 CI 日志确认失败原因——最常见的是更新破坏了 API 兼容性
2. 确认是误报或需要锁定版本时，在 PR 里评论 `@dependabot ignore this dependency`，Dependabot 会把它写进 `ignore` 规则
3. 需要代码适配的更新，把 PR 对应的分支拉到本地改完推送（或者放弃自动更新，手动升级后用 `@dependabot close` 关闭）
4. PR 分支落后于主分支时，`@dependabot rebase` 可以让它变基

### Q7: monorepo 项目如何配置？

每个子目录一个生态条目，各自独立排期：

```yaml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/packages/core"
    schedule:
      interval: "daily"
  - package-ecosystem: "npm"
    directory: "/packages/web"
    schedule:
      interval: "daily"
  - package-ecosystem: "npm"
    directory: "/packages/mobile"
    schedule:
      interval: "daily"
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

子目录数量多时，用支持 glob 的 `directories` 一条搞定全部子包：

```yaml
  - package-ecosystem: "npm"
    directories:
      - "/packages/**/*"
    schedule:
      interval: "daily"
```

### Q8: 如何查看 Dependabot 更新历史？

1. **面板**：Insights → Dependency graph → Dependabot，能看到每个生态的最近检查时间和错误
2. **GraphQL API**：

```bash
gh api graphql -f query='
{
  repository(owner: "OWNER", name: "REPO") {
    vulnerabilityAlerts(first: 10) {
      nodes {
        vulnerableManifestFilename
        securityVulnerability {
          severity
          package { name }
        }
      }
    }
  }
}'
```

---

## 8. 替代方案对比

| 工具 | 类型 | 费用 | 特点 |
|------|------|------|------|
| **Dependabot** | GitHub 内置 | 免费（所有套餐，含私有仓库） | 原生集成、零安装，Security Updates 与告警打通 |
| **Renovate** | 开源 + Mend 托管 SaaS | 自托管免费；托管版有免费额度与付费档 | 配置粒度最细，支持更多生态和调度策略，monorepo 表现成熟 |
| **Snyk** | SaaS + CLI | 免费档 + 商业版 | 安全视角最强，含许可证合规，修复 PR 之外还有持续监测 |
| **npm outdated / yarn upgrade** | CLI | 免费 | 零配置手动执行，适合一次性检查或很小的项目 |

### Renovate vs Dependabot 功能对比

| 功能 | Renovate | Dependabot |
|------|----------|------------|
| PR 分组 | ✅ 规则更细 | ✅ |
| Docker 基础镜像更新 | ✅ | ✅（`docker` 生态） |
| GitHub Actions 更新 | ✅ | ✅ |
| 自动合并 | ✅ 配置内声明 | ✅ 依赖 branch protection + workflow 配合 |
| 私有注册表 | ✅ | ✅ |
| 自托管 | ✅ | ❌ 仅 GitHub 托管服务 |
| 配置文件 | `renovate.json` | `dependabot.yml` |
| 开源 | ✅（MPL-2.0） | ❌ 闭源运营 |

**选型判断：**

- 在 GitHub 上刚起步或仓库数量多、维护精力有限：Dependabot，配置几分钟搞定，安全更新开箱即用
- 需要精细调度（按依赖设不同节奏、锁定窗口期、复杂 monorepo 拓扑）：Renovate 的配置表达力明显更强
- 安全合规有硬要求（许可证审计、SBOM、策略报告）：Snyk 或 Renovate 企业版， Dependabot 只解决"更新"这一件事

---

## 9. 自检清单

完成配置后，逐项确认：

- [ ] `.github/dependabot.yml` 存在于默认分支且是有效 YAML
- [ ] `package-ecosystem` 与清单文件类型匹配（Yarn → `npm`，Cargo → `Cargo.toml`）
- [ ] `directory` 指向清单文件实际所在路径
- [ ] `schedule.interval` 设置合理（建议 daily 或 weekly）
- [ ] `ignore` 覆盖了需要人工处理的依赖和 major 更新
- [ ] `groups` 已配置，PR 数量在团队可消化的范围内
- [ ] 私有依赖配置了 `registries`，凭据存在 Dependabot secrets 里
- [ ] 安全更新开关已在仓库设置中确认开启
- [ ] CI 在 Dependabot PR 上运行且结论明确（pass/fail）
- [ ] branch protection 配置了 required status checks
- [ ] 若开启 auto-merge：确认放行的更新类型有足够的测试覆盖
- [ ] 团队知道 `@dependabot` 常用命令（rebase / close / ignore this dependency）

---

## 10. 参考链接

- [Dependabot 官方文档](https://docs.github.com/en/code-security/dependabot)
- [dependabot.yml 配置选项参考](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference)
- [About Dependabot security updates](https://docs.github.com/en/code-security/dependabot/dependabot-security-updates/about-dependabot-security-updates)
- [Automating Dependabot with GitHub Actions](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/automating-dependabot-with-github-actions)
- [私有注册表配置](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/configuring-access-to-private-registries-for-dependabot)
- [GitHub Advisory Database](https://github.com/advisories)
- [Renovate 官方文档](https://docs.renovatebot.com/)
- [Snyk 官方文档](https://docs.snyk.io/)

---

## 自测题

1. Version Updates 和 Security Updates 的触发机制有什么区别？各自的"开关"分别在哪里？
2. 团队维护一个 npm monorepo（`/packages/core`、`/packages/web`、`/packages/mobile`），`dependabot.yml` 怎么写？如果想一条配置覆盖全部子包，用什么选项？
3. 为什么 `groups` 分组重要？不分组会发生什么？`open-pull-requests-limit` 设为 0 会限制安全更新 PR 吗？
4. 内部 npm registry 需要认证，Dependabot 怎么访问？凭据应该存在哪套 secrets 里？
5. 你的 Dependabot PR 上 `gh pr edit` 报 403，最可能的原因是什么？
6. 什么时候应该从 Dependabot 切到 Renovate？列出至少两个信号。

## 练习

**练习 1：给现有项目配 Dependabot（20 分钟）**

挑一个你维护的 GitHub 仓库，写出 `.github/dependabot.yml`：覆盖项目用到的所有包管理器、设定合理的检查频率、生产依赖和开发依赖分组、给一个想手动跟进的依赖加 `ignore`。推送后在 Insights → Dependency graph → Dependabot 面板确认第一次检查的结果。

**练习 2：模拟安全漏洞响应（15 分钟）**

假设项目依赖 `axios@0.21.0`，GitHub Advisory Database 刚收录一个 Critical 级 RCE 漏洞。走一遍流程：安全 PR 出现后看什么（修复版本、diff 范围）、跑什么（CI 之外要不要补回归）、什么时候合？把"从告警到合入"的时间上限写成团队的 SLA。

**练习 3：对比 Renovate 配置（30 分钟）**

把练习 1 的配置翻译成等价的 `renovate.json`。对比两者的表达能力：哪些地方 Dependabot 更简洁，哪些 Renovate 更强？写一段 100 字以内的选型结论。

## 进阶路径

**阶段一：基础自动化（1 小时）**

在自己的仓库里跑通第一条 Version Update PR 和 Security Update PR，确认面板上能看到检查记录。

**阶段二：CI 集成与分组（2 小时）**

按 §6 的模板写一个 Dependabot 专用 workflow（测试 + 打标签），同时调优分组，把并发 PR 控制在 5 个以内。

**阶段三：auto-merge 与零干预（半天）**

在测试覆盖达标的前提下，配置 branch protection + auto-merge，让 patch 和 minor 自动合入。把"哪些类型绝不自动合"写成明文规则并告知团队。

**阶段四：规模化与策略文档（1 天）**

团队有 10+ 个仓库时，写一份依赖更新策略：统一的 `dependabot.yml` 模板、分组与 auto-merge 规则、告警响应 SLA。验收标准：新同事照文档 10 分钟内配好一个仓库。
