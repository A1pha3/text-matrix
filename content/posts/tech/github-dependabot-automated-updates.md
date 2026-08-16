---
title: "GitHub Dependabot：自动化依赖更新"
date: "2026-05-15T10:25:00+08:00"
slug: "github-dependabot-automated-updates"
github_repo: "github/dependabot-action"
description: "Dependabot 把依赖更新的责任从人的记忆力转移到系统上，支持 Alerts、Version Updates 和 Security Updates 三条独立机制，覆盖 npm、pip、Go、Cargo 等主流生态。"
draft: false
categories: ["技术笔记"]
tags: ["GitHub", "DevOps", "依赖管理", "工具"]
---

# GitHub Dependabot：自动化依赖更新

Dependabot 解决的真正问题是把依赖更新的责任从人的记忆力转移到系统上，而不是自动发 PR。漏洞出现后小时级响应、版本落后自动追平，这些靠人盯 RSS 或手动 `npm outdated` 做不到。下面先把三条机制拆开，再逐条看怎么配、怎么用。

| 机制 | 触发方式 | 产物 | 典型场景 |
|---|---|---|---|
| Dependabot Alerts | GitHub Advisory Database 匹配到漏洞 | Security 标签页告警 + 修复建议 | 发现 `lodash` CVE，知道该升到哪个版本 |
| Version Updates | `.github/dependabot.yml` 中配置的 schedule | 自动创建依赖更新 PR | 每周检查 npm 依赖，把 `react` 从 18.2 升到 18.3 |
| Security Updates | Alerts 判定有可用补丁的漏洞 | 紧急 PR，绕过正常 schedule | `express` 出现 RCE（远程代码执行）漏洞，不等下周直接发 PR |

三条线独立运作，但在一个仓库里会同时生效。理解这个边界之后，再看细节就不会混。

## 一、Dependabot 是什么

[Dependabot](https://github.com/dependabot) 是 GitHub 官方出品的自动化依赖更新工具，支持的生态系统包括 npm、Maven、pip、Go、Cargo、NuGet、GitHub Actions、Docker、Composer、Bundler 等。

GitHub.com 上的 Dependabot 是平台自带的能力，在仓库 Settings 里开启即用，日常使用不必关心它的实现。另有一个开源实现 [dependabot-core](https://github.com/dependabot/dependabot-core)（含官方维护的 [github/dependabot-action](https://github.com/github/dependabot-action)），供 GHES 或自托管场景使用——普通团队用不到，后面第 4 节单独讲。

## 二、核心功能

### 1. Dependabot Alerts

当依赖出现已知漏洞时，GitHub 自动在 Security 标签页生成告警：

- **漏洞数据库**：来自 GitHub Advisory Database、NVD 和生态伙伴
- **严重程度分级**：Critical、High、Medium、Low
- **直接修复建议**：显示受影响版本范围，给出应升级的目标版本

Alerts 只负责"告诉你出事了"和"该升到哪个版本"。它不创建 PR——那个是 Security Updates 的事。

### 2. Dependabot Version Updates

按 schedule 定期扫描依赖，检测到新版本就创建更新 PR：

```yaml
# .github/dependabot.yml
version: 2
updates:
  # npm 每月检查一次
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "monthly"
    open-pull-requests-limit: 5
    commit-message:
      prefix: "deps"
    labels:
      - "dependencies"
    reviewers:
      - "@org/devops"

  # GitHub Actions 每周检查
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    commit-message:
      prefix: "ci"
```

### 3. Security Updates

Security Updates 为依赖图中每一个有可用补丁的告警自动创建修复 PR，不受 schedule 约束，升级到能避开漏洞的最小安全版本：

- **触发条件**：Dependabot Alerts 判定依赖存在有修复版本的漏洞
- **自动发起 PR**：无需等待 schedule，通常把依赖升到修复版本即可
- **PR 仍走常规流程**：合并依然受 Branch Protection Rules 约束，CI 不通过不会自动合入

Security Updates 与 Version Updates 是两套独立机制：前者在仓库 Settings 的 Advanced Security 中开启，不依赖 `.github/dependabot.yml`；后者靠配置文件驱动。`dependabot.yml` 只能定制 Security Update PR 的行为（标签、分组、`open-pull-requests-limit` 等），不能决定开关——开关始终在 Settings 里。

## 三、详细配置

### 基础配置

创建 `.github/dependabot.yml`：

```yaml
# .github/dependabot.yml
version: 2

updates:
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
      day: "wednesday"
    open-pull-requests-limit: 10
    commit-message:
      prefix: "py"
    ignore:
      # 忽略 patch 版本更新（如 1.2.3 → 1.2.4）
      - dependency-name: "*"
        update-types: ["version-update:semver-patch"]
    groups:
      production-dependencies:
        dependency-type: "production"
      development-dependencies:
        dependency-type: "development"
```

### 按生态详细配置

**npm:**

```yaml
- package-ecosystem: "npm"
  directory: "/frontend"
  schedule:
    interval: "weekly"
  versioning-strategy: "increase"
  commit-message:
    prefix: "npm"
  allow:
    - dependency-name: "react"
    - dependency-name: "react-dom"
  ignore:
    - dependency-name: "typescript"
      versions: ["4.9.0", "4.9.5"]
```

**GitHub Actions:**

```yaml
- package-ecosystem: "github-actions"
  directory: "/"
  schedule:
    interval: "daily"
    time: "09:00"
  open-pull-requests-limit: 3
  commit-message:
    prefix: "ci"
  labels:
    - "github-actions"
  ignore:
    - dependency-name: "actions/checkout"
      update-types: ["version-update:semver-patch"]
```

**Maven:**

```yaml
- package-ecosystem: "maven"
  directory: "/"
  schedule:
    interval: "daily"
  commit-message:
    prefix: "mvn"
  target-branch: "develop"
  allow:
    - dependency-name: "org.springframework.boot:*"
```

## 四、dependabot-action 与 GHES

GitHub.com 上的 Dependabot 由官方维护的 [github/dependabot-action](https://github.com/github/dependabot-action)（Updater Action）驱动，它在 GitHub 内部负责执行 version 与 security 更新任务。这个 Action **不支持在 workflow 文件中直接使用**——它是给 GitHub 自己的 Dependabot 服务跑的，不是给人手动调用的。

需要关注它的只有一种场景：GitHub Enterprise Server。GHES 默认无法访问 GitHub.com 上的 Actions，需要管理员用官方 [actions-sync](https://github.com/actions/actions-sync) 工具把依赖的 action 同步到企业实例：

```bash
# actions-sync 需要在能访问 GitHub.com API 的机器上运行
# 1. 安装后登录 GitHub.com 与 GHES 的 API
actions-sync sync \
  --cache-dir .actions-sync \
  github/dependabot-action \
  --target-token $GHES_TOKEN \
  --target-url https://ghes.example.com
```

同步完成后，还需为 Dependabot 更新配置自托管的 runner（Linux + Docker），并让 GHES 能访问内部 registry。这属于企业管理员的工作，普通团队用不到。

对企业内网开发团队而言，另一个选择是自托管 [dependabot-core](https://github.com/dependabot/dependabot-core) 或官方 [Dependabot CLI](https://github.com/dependabot/cli)，在自己的 CI 里跑依赖更新。GitHub.com 用户不需要碰这些。

## 五、Dependabot 与安全

### 开启漏洞自动修复

Security Updates 的开关不在 `dependabot.yml` 里，而在仓库 **Settings → Code security and analysis → Dependabot security updates** 中勾选。开启后，凡是依赖图里出现有修复版本的告警，Dependabot 都会自动创建修复 PR，不受 schedule 约束。

`dependabot.yml` 能影响的是这些修复 PR 长什么样，比如用 `groups` 把同一生态的安全修复合并成一个 PR：

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      # 安全修复专用分组：一个 PR 合入一个生态的所有安全更新
      npm-security:
        applies-to: security-updates
        patterns:
          - "*"
```

如果只想保留安全更新、关掉常规版本更新，把 `open-pull-requests-limit` 设为 `0` 即可——Alerts 与 Security Update PR 不受这个字段影响。

### 配合 GitHub Advisory Database

- GitHub 自动扫描依赖树
- 发现漏洞后立即在 Security 标签页显示
- 同时在 Dependabot Alerts 中列出

### 合并策略

```yaml
# 区分开发依赖和生产依赖的合并策略
- package-ecosystem: "pip"
  directory: "/"
  schedule:
    interval: "daily"
  open-pull-requests-limit: 3

  # 只有开发依赖可以自动合并
  allow:
    - dependency-name: "*"
      update-types: ["version-update:semver-patch"]
      dependency-type: "development"

  # 生产依赖必须人工审查
  labels:
    - "dependencies"
    - "requires-review"
```

## 六、分组与批量处理

大型项目中依赖很多，逐个 PR 处理太碎片化。Dependabot 支持分组：

```yaml
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      # 开发工具组（可以批量更新）
      dev-tools:
        patterns:
          - "eslint-*"
          - "prettier-*"
          - "babel-*"
      # UI 库组
      ui-libs:
        patterns:
          - "@mui/*"
          - "antd"
          - "radix-*"
```

## 七、一次安全漏洞从发现到修复的完整路径

以 Express 4.18 后端仓库为例，已开启 Security Updates：

1. **漏洞入库**：Express 4.18 的一个 RCE 漏洞被收入 GitHub Advisory Database，标记为 Critical。
2. **Alerts 触发**：GitHub 扫描仓库的 `package-lock.json`，发现依赖树包含 `express@4.18.2`，在 Security 标签页生成告警，同时通知仓库管理员。
3. **Security Update PR 生成**：因为仓库在 Settings 里开启了 Dependabot security updates，Dependabot 不等 weekly schedule，直接创建一个 PR，把 `express` 升到修复版本 `4.19.0`，PR 标题为 `build(deps): bump express from 4.18.2 to 4.19.0`。
4. **CI 验证**：PR 触发 GitHub Actions，跑 lint → test → build。如果 CI 挂了——比如某个中间件不兼容 `4.19.0`——PR 不会自动合并，开发者需要手动介入。
5. **审查与合并**：`CODEOWNERS` 把 `package.json` 分配给 `@org/backend-team`，团队 review changelog、确认 CI 通过后合并。
6. **自动化兜底**：如果 CI 全绿且 `allow` 配置了 `dependency-type: "development"` 的 auto-merge 策略，patch 级更新可以直接合入——但本例是生产依赖，不走自动合并。

这条路径里的关键设计是：**告警、扫描、PR 创建、CI 验证各自独立**——Dependabot 不替你判断"能不能合"，只负责把选择推到人面前。

## 八、实践建议

### 1. 配置合理的更新频率

| 依赖类型 | 建议频率 | 理由 |
|---|---|---|
| 生产核心依赖 | weekly | 更新越频繁，每次变更越小，出问题时回溯范围也越小 |
| 开发工具 | biweekly | ESLint、Prettier 等工具链变更对运行时无影响，降低噪音 |
| GitHub Actions | monthly | Action 版本变更通常只涉及 CI 行为，不需要高频追踪 |
| 底层基础设施 | monthly | 数据库驱动、框架大版本等，稳定性优先 |

### 2. 设置合并门禁

Dependabot 只创建 PR，合不合并由分支保护规则说了算。在仓库 **Settings → Branches** 中给默认分支添加规则，勾选 "Require status checks to pass before merging"，把 CI 的 check 加进去即可。想精确到某类依赖，可以把 CI 按 `package-ecosystem` 拆成多个 job，规则里只对对应的 check 打勾。

也可以写成文件式配置（`.github` 下的 branch protection 需要借助第三方 Action 或 `gh api` 脚本，GitHub 没有原生 YAML 管理分支规则）：

```bash
# 用 gh api 设置 required status checks（示例）
gh api -X PUT repos/{owner}/{repo}/branches/{branch}/protection \
  -H "Accept: application/vnd.github+json" \
  -f "required_status_checks[strict]=true" \
  -f 'required_status_checks[contexts][]=ci/lint' \
  -f 'required_status_checks[contexts][]=ci/test'
```

### 3. 使用 CODEOWNERS 控制审查流

```
# CODEOWNERS
/.github/dependabot.yml @org/devops-team
package.json @org/frontend-team
requirements.txt @org/backend-team
pom.xml @org/java-team
```

### 4. 监控 Dependabot 指标

用 GitHub GraphQL API 拉取依赖图清单，可以了解仓库依赖的全貌（以下查询需开启 Dependency Graph）：

```bash
# 将 YOUR_ORG/YOUR_REPO 替换为实际仓库
gh api graphql -f query='
  {
    repository(owner: "YOUR_ORG", name: "YOUR_REPO") {
      dependencyGraphManifests(first: 10) {
        nodes {
          filename
          dependencies(first: 20) {
            nodes {
              packageName
              requirements
              packageManager
            }
          }
        }
      }
    }
  }'
```

## 九、常见问题

**Q: 团队维护 30 个微服务仓库，Dependabot 每周创建 40+ 个 PR——低风险更新能不能自动合入？**

不能直接合入，需要额外配置。Dependabot 只负责把 PR 送到你面前，合并必须过 Branch Protection Rules。想让 patch 级开发依赖自动合入，需要两步：先在 `.github/dependabot.yml` 中用 `allow` 限定范围（比如 `dependency-type: "development"` 且 `update-types: ["version-update:semver-patch"]`），再配 GitHub Actions 或第三方 bot 在 CI 全绿时 auto-merge。生产依赖不建议走自动合并，哪怕 CI 全绿。

**Q: monorepo 里 `lodash@4.17.20` 被一个 EOL 旧模块锁死了，在找到替代方案前不能动——怎么让 Dependabot 别再提这个 PR？**

用 `ignore` 配置跳过特定版本：

```yaml
ignore:
  - dependency-name: "lodash"
    versions: ["4.17.20"]
  - dependency-name: "express"
    update-types: ["version-update:semver-major"]
```

第一个 rule 按版本号精确跳过，第二个 rule 跳过所有大版本更新。如果你的项目不希望 Dependabot 对某个包提任何 PR，只写 `dependency-name` 不加 `versions` 即可。

**Q: 公司有私有 npm registry（`npm.mycompany.com`），Dependabot 能扫描里面的内部包吗？**

可以，但需要两步：先在顶级 `registries` 键里定义 registry，再在每个 update 条目里用 `registries` 字段引用它：

```yaml
version: 2
registries:
  my-npm-registry:
    type: "npm-registry"
    url: "https://npm.mycompany.com"
    token: "${{secrets.NPM_TOKEN}}"
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    registries:
      - my-npm-registry
```

前提是私有 registry 实现了 npm registry API 且包版本遵循 semver。如果内部包不走 semver 或 registry 不兼容标准 API，Dependabot 无法解析版本，需要换 Renovate 或自定义方案。

**Q: Dependabot 和 Renovate 选哪个？**

Dependabot 的优势是零额外服务、GitHub 原生集成、Security Alerts 直接联动——如果你的依赖生态不超过 3 种、不需要跨仓库统一配置、Security Updates 是刚需，Dependabot 就够用。Renovate 在以下场景更强：跨仓库共享 preset 配置、需要细粒度分组规则、依赖仪表盘展示、合并策略高度自定义。简化的判断标准：全在 GitHub 生态内 → Dependabot；跨 GitLab/Bitbucket 或需要统一治理 → Renovate。

**Q: PR 数量太多看不过来怎么办？**

三个手段组合使用：第一，用 `open-pull-requests-limit` 限制同时打开的 PR 数；第二，用 `groups` 把同类依赖打包进一个 PR（比如所有 ESLint 插件合成一个 "update dev tools" PR）；第三，调整 `schedule interval` ——把开发工具从 weekly 降到 monthly，减少噪音。如果 PR 仍然过多，回溯检查是否该用 `ignore` 跳过某些高频但不关键的依赖。

## 采用的优先级

Dependabot 的配置工作量和收益不是线性的。建议按以下顺序落地：

1. **先开 Alerts**（零配置，在仓库 Settings → Code security and analysis 中勾选即生效）。这是收益最高的第一步——你至少能知道哪些依赖有已知漏洞。
2. **再开 Security Updates**（同样在 Settings 里勾选，无需写配置）。让有修复版本的漏洞自动生成修复 PR，把响应时间从"下次有人想起来"缩短到小时级。
3. **然后上 Version Updates**（写 `.github/dependabot.yml`）。先从一个生态系统开始（比如 npm），跑两周看 PR 质量和 CI 通过率，再扩展到其他生态系统。
4. **最后加分组和 auto-merge 策略**。前提是 CI 覆盖率够高——如果测试不足以拦住回归，auto-merge 反而引入风险。

如果你的仓库依赖少、更新频率低（比如一个静态站点），Alerts 就够了，不需要配 Version Updates。Dependabot 的价值体现在依赖多、生态杂、安全要求高的项目上——配得越重，回报递减越明显。

## 自测

1. 你的仓库用的是 `requirements.txt`，Dependabot 的 `package-ecosystem` 应该填什么值？`directory` 应该填 `/` 还是 `/backend`？
2. Dependabot Alerts 和 Security Updates 的本质区别是什么？（不是"一个发告警一个发 PR"——Alerts 只告知，Security Updates 负责行动，它绕过了什么？）
3. 你收到一个标题为 `build(deps): bump express from 4.18.2 to 4.19.0` 的 PR——标题里的前缀说明它来自 Dependabot，但你能从标题判断它来自 Version Updates 还是 Security Updates 吗？
4. 团队的一个 Markdown 文档站点没有任何运行时依赖——你应该只开 Alerts 还是配完整的 `.github/dependabot.yml`？给出理由。

**相关资源：**

- [Dependabot 官方文档](https://docs.github.com/en/code-security/supply-chain-security)
- [dependabot-action](https://github.com/github/dependabot-action)
- [GitHub Advisory Database](https://github.com/advisories)