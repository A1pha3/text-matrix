+++
date = '2026-05-15T10:25:00+08:00'
draft = false
title = 'GitHub Actions Importer：自动化迁移 CI/CD 到 GitHub Actions'
slug = 'github-actions-importer-migration'
description = 'GitHub Actions Importer 是 GitHub 官方的 CI/CD 迁移工具，自动将 Jenkins、GitLab CI、CircleCI、Travis CI 等流水线转换为 GitHub Actions 工作流。'
categories = ['技术笔记']
tags = ['GitHub', 'DevOps', 'CI/CD', '工具']
+++

# GitHub Actions Importer：自动化迁移 CI/CD 到 GitHub Actions

> Jenkins、Travis CI、CircleCI、GitLab CI……每个平台都有自己的一套 CI/CD 配置。GitHub Actions Importer 把这个迁移过程自动化——自动转换流水线、验证转换结果、按计划推进迁移。

> **目标读者**：DevOps 工程师、CI/CD 维护者、准备从其他平台迁移到 GitHub Actions 的团队
> **预计阅读时间**：25-35 分钟
> **前置知识**：GitHub Actions 基础、CI/CD 概念、Docker 基础
> **难度定位**：⭐⭐⭐ 中级实用

---

## §0 学习目标

完成本篇文章后，你将能够：

1. **理解 GitHub Actions Importer 的工作流程**：审计 → 转换 → 验证 → 应用 → 切换
2. **掌握安装与配置**：GH CLI 扩展、凭证配置、多平台支持
3. **执行审计与转换**：分析现有流水线、生成转换报告、处理无法自动转换的步骤
4. **设计迁移策略**：渐进式迁移、双跑验证、回滚计划
5. **判断适用性**：什么场景适合用 Importer，什么场景需要手动迁移

---

## §0.5 目录

- [§1 项目概述](#一项目概述)：支持的平台、核心价值
- [§2 工作原理](#二工作原理)：5 步迁移流程
- [§3 安装与配置](#三安装与配置)：前置条件、安装步骤、凭证配置
- [§4 审计现有 CI/CD](#四审计现有-cicd)：审计报告解读、各平台审计示例
- [§5 转换工作流](#五转换工作流)：Dry-run、自定义 Transformer
- [§6 完整迁移流程示例](#六完整迁移流程示例)：Jenkins → GitHub Actions 实战
- [§7 与 GitHub Enterprise Server 配合](#七与-github-enterprise-server-配合)：GHES 配置要点
- [§8 实践建议](#八实践建议)：审计优先、渐进式迁移、保留映射文档
- [§9 局限性与注意事项](#九局限性与注意事项)：转换覆盖率、成本控制
- [§10 自测题](#自测题)：巩固知识点的 5 道题
- [§11 进阶路径](#进阶路径)：从评估到完成的四个阶段

---

**项目速览**：[github/gh-actions-importer](https://github.com/github/gh-actions-importer) · Stars: 1,218+ · Forks: 688+ · License: MIT · Language: C# · 最后更新: 2026-06-25

---

[GitHub Actions Importer](https://github.com/github/gh-actions-importer) 是 GitHub 官方出品的 CI/CD 迁移工具，用于将现有流水线自动转换为 GitHub Actions 工作流。

**支持迁移的平台：**

| 源平台 | 状态 |
|---|---|
| Jenkins | ✅ 支持 |
| GitLab CI | ✅ 支持 |
| CircleCI | ✅ 支持 |
| Travis CI | ✅ 支持 |
| Azure DevOps | ✅ 支持 |
| Bamboo | ✅ 支持 |
| Bitbucket Pipelines | ✅ 支持 |

## 二、工作原理

GitHub Actions Importer 的核心流程：

```
1. 审计 (Audit)
   → 分析现有 CI/CD 配置
   → 生成详细报告（步骤数、耗时、覆盖率）
   
2. 转换 (Convert)
   → 将源平台配置转换为 GitHub Actions YAML
   → 输出转换映射说明
   
3. 验证 (Dry-run)
   → 在临时分支上试运行
   → 检查转换后的 Action 是否可执行
   
4. 应用 (Apply)
   → 将转换后的工作流应用到目标仓库
   → 与现有 CI/CD 并行运行（双跑验证期）
   
5. 切换 (Switchover)
   → 确认新工作流正确后，禁用旧配置
```

## 三、安装与配置

### 前置条件

- Docker CLI（已安装并运行）
- GitHub CLI（`gh`）
- GitHub Container Registry 认证

### 安装步骤

```bash
# 1. 安装 GitHub Actions Importer CLI 扩展
gh extension install github/gh-actions-importer

# 2. 验证安装
gh actions-importer version

# 3. 更新到最新版本
gh actions-importer update

# 4. 配置凭证（交互式配置）
gh actions-importer configure
```

### 凭证配置示例

对于不同源平台，需要配置相应的环境变量：

```bash
# Jenkins
export JENKINS_URL="https://jenkins.example.com"
export JENKINS_USER="admin"
export JENKINS_TOKEN="your-jenkins-api-token"

# GitLab
export GITLAB_ACCESS_TOKEN="your-gitlab-token"
export GITLAB_URL="https://gitlab.example.com"

# CircleCI
export CIRCLECI_ACCESS_TOKEN="your-circleci-token"
export CIRCLECI_ORG_SLUG="my-org/my-project"
```

## 四、审计现有 CI/CD

### Jenkins 审计示例

```bash
# 审计 Jenkins 流水线
gh actions-importer audit jenkins \
  --source-url "https://jenkins.example.com/job/my-project" \
  --credentials-file "./jenkins-credentials.json"

# 输出审计报告
# [
#   {
#     "pipeline": "my-project/main",
#     "steps": 12,
#     "estimated_duration_minutes": 45,
#     "conversion_percentage": 94,
#     "converted_workflow": ".github/workflows/main.yml"
#   }
# ]
```

审计报告会告诉你：
- 有多少流水线待迁移
- 每个流水线的转换完成度
- 哪些步骤无法自动转换（需要手动处理）

### GitLab CI 审计示例

```bash
gh actions-importer audit gitlab \
  --repo "group/project" \
  --target-url "https://github.com/my-org/my-repo"
```

## 五、转换工作流

### Dry-run：预览转换结果

```bash
# 在临时分支上试运行转换
gh actions-importer dry-run jenkins \
  --source-file-path "./jenkins/Jenkinsfile" \
  --target-url "https://github.com/my-org/my-repo"

# 查看转换后的工作流内容
cat /tmp/actions-importer/converted/workflow.yml
```

### Custom Transformer：自定义转换规则

对于无法自动转换的步骤，可以编写自定义 transformer：

```ruby
# custom_transformer.rb
transform "bash_script" do |step|
  # 将自定义 bash 步骤转换为 GitHub Actions
  {
    name: "Run custom script",
    run: step["script"],
    shell: "bash"
  }
end

transform "upload_artifacts" do |step|
  # 转换制品上传步骤
  {
    name: "Upload artifacts",
    uses: "actions/upload-artifact@v4",
    with: {
      name: step["artifact-name"],
      path: step["path"]
    }
  }
end
```

使用时：

```bash
gh actions-importer convert jenkins \
  --source-file-path "./Jenkinsfile" \
  --target-url "https://github.com/my-org/my-repo" \
  --custom-transformer "./custom_transformer.rb"
```

## 六、完整迁移流程示例

### 从 Jenkins 迁移到 GitHub Actions

```bash
# 1. 审计所有 Jenkins 流水线
gh actions-importer audit jenkins \
  --source-url "https://jenkins.example.com" \
  --output-dir "./audit-reports"

# 2. 转换单个流水线
gh actions-importer convert jenkins \
  --source-file-path "./pipelines/build.groovy" \
  --target-url "https://github.com/my-org/my-repo" \
  --output-dir "./converted-workflows"

# 3. 应用到仓库（创建 PR）
gh actions-importer apply \
  --target-url "https://github.com/my-org/my-repo" \
  --workflow-file "./converted-workflows/build.yml" \
  --branch "actions-migration/build"

# 4. 验证后切换
gh actions-importer switchover \
  --target-url "https://github.com/my-org/my-repo" \
  --source-pipeline "jenkins/build"
```

### 双跑验证策略

迁移过程中，建议新旧系统并行运行一段时间：

```yaml
# 验证期间：新工作流并行运行
on:
  push:
    branches: [main]

jobs:
  # 新工作流（GitHub Actions）
  github-actions:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: ./gradlew build
      
  # 旧工作流（Jenkins）仍然触发
  # 确认新工作流输出与旧工作流一致后，禁用 Jenkins
```

## 七、与 GitHub Enterprise Server 配合

如果你是 GHES 用户，需要手动配置 Container Registry：

```bash
# 1. 登录 GHES 的 Container Registry
export CONTAINER_REGISTRY="https://ghcr.io"
echo "YOUR_PAT" | docker login ghcr.io -u "YOUR_USERNAME" --password-stdin

# 2. 配置自定义镜像地址
export GITHUB_ACTIONS_IMPORTER_IMAGE="ghcr.io/github/actions-importer:latest"

# 3. 正常使用
gh actions-importer audit jenkins ...
```

## 八、实践建议

### 1. 审计优先

不要急着迁移，先完整审计：

```bash
# 审计并生成 HTML 报告
gh actions-importer audit gitlab \
  --repo "my-group/my-project" \
  --output-format html \
  --output-dir "./migration-report"
```

报告里会标注：
- 哪些步骤无法自动转换
- 预计迁移完成度
- 每个步骤的依赖关系

### 2. 渐进式迁移

不要一次性迁移所有流水线，循序渐进：

```
Phase 1: 迁移测试流水线（风险低）
Phase 2: 迁移 CI 流水线（与测试并行）
Phase 3: 迁移 CD/部署流水线（风险高）
Phase 4: 确认无误，禁用旧系统
```

### 3. 保留转换映射文档

每次迁移，保留一份映射说明：

```markdown
# Jenkins → GitHub Actions 映射表

| Jenkins Step | GitHub Actions | 手动处理 |
|---|---|---|
| `sh 'make build'` | `run: make build` | - |
| `stash 'artifacts'` | `actions/upload-artifact@v4` | - |
| `input 'Deploy?'` | `environment: approvals` | ✅ 需配置 Environment Protection |
| `timeout(30)` | `timeout-minutes: 30` | - |
```

### 4. 使用 Actions 变量替代硬编码

```yaml
# 转换时，将硬编码值替换为 GitHub Context 变量
# Jenkins
#   environment {
#     APP_NAME = 'my-app'
#     DEPLOY_TARGET = 'production'
#   }

# 转换为 GitHub Actions
env:
  APP_NAME: my-app
  DEPLOY_TARGET: production
```

## 九、局限性与注意事项

1. **不是 100% 自动转换**：部分平台特有功能（如 Jenkins shared libraries、GitLab rules: approvals）需要手动处理
2. **凭证管理**：迁移过程中需要保持旧系统凭证有效，确保可以读取配置
3. **双跑成本**：并行运行期间 CI 成本翻倍，建议控制在 2-4 周内完成切换
4. **自托管 runners**：如果原来用自托管 Jenkins agent，迁移后也需要配置自托管 runners

## 自测题

完成阅读后，请自检以下知识点：

**Q1**：GitHub Actions Importer 的 5 个核心步骤是什么？
<details>
<summary>参考答案</summary>
审计 (Audit) → 转换 (Convert) → 验证 (Dry-run) → 应用 (Apply) → 切换 (Switchover)。每个步骤都有明确的输出和验证点。
</details>

**Q2**：`dry-run` 和 `apply` 的区别是什么？
<details>
<summary>参考答案</summary>
`dry-run` 在临时分支上试运行转换，生成的工作流文件在本地临时目录，不会提交到仓库；`apply` 会创建 PR 或将工作流文件应用到目标仓库，是真正的迁移操作。
</details>

**Q3**：什么情况下需要写自定义 Transformer？
<details>
<summary>参考答案</summary>
当 Importer 无法自动转换某些平台特有功能时（如 Jenkins shared libraries、GitLab `rules: approvals`、自定义脚本逻辑），需要写自定义 Transformer（Ruby 格式）来定义转换规则。
</details>

**Q4**：双跑验证策略的目的是什么？
<details>
<summary>参考答案</summary>
新旧系统并行运行一段时间，对比两者的构建结果是否一致，确认新工作流正确后再禁用旧系统。这能降低迁移风险，避免一刀切导致构建失败。
</details>

**Q5**：GitHub Actions Importer 支持哪些源平台？
<details>
<summary>参考答案</summary>
Jenkins、GitLab CI、CircleCI、Travis CI、Azure DevOps、Bamboo、Bitbucket Pipelines。覆盖率因平台而异，Jenkins 和 GitLab CI 的支持最成熟。
</details>

---

## 进阶路径

### 阶段一：评估与审计（1-2 天）
- 安装 GH CLI 和 Actions Importer 扩展
- 对现有 CI/CD 平台执行完整审计
- 分析审计报告，计算转换覆盖率
- 识别需要手动处理的高风险步骤

### 阶段二：试点转换（3-7 天）
- 选择一个低风险流水线（如单元测试）做试点
- 执行 `dry-run` 验证转换结果
- 编写自定义 Transformer（如需要）
- 创建 PR 并审查转换后的工作流

### 阶段三：渐进式迁移（2-4 周）
- 按风险从低到高排序流水线
- 逐个迁移并启用双跑验证
- 保留转换映射文档
- 处理转换失败的步骤

### 阶段四：切换与清理（1 周）
- 确认所有关键流水线已迁移
- 执行 `switchover` 禁用旧配置
- 清理临时分支和测试配置
- 更新团队文档和 CI/CD 规范

**推荐资源**：
- [GitHub Actions Importer 官方文档](https://docs.github.com/en/actions/migrating-to-github-actions/automating-migration-with-github-actions-importer)
- [迁移学习实验室](https://github.com/actions/importer-labs)
- [GitHub Actions 语法参考](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions)

---

## 十、相关资源

- [GitHub Actions Importer 官方文档](https://docs.github.com/en/actions/migrating-to-github-actions/automating-migration-with-github-actions-importer)
- [迁移学习实验室](https://github.com/actions/importer-labs)
- [GitHub Actions 官方文档](https://docs.github.com/en/actions)