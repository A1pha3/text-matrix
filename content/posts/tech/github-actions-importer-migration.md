---
title: "GitHub Actions Importer：自动化迁移 CI/CD 到 GitHub Actions"
date: 2026-05-15T10:25:00+08:00
categories: ["技术笔记"]
tags: ["GitHub", "GitHub Actions", "CI/CD", "DevOps", "迁移", "自动化"]
draft: false
---

# GitHub Actions Importer：自动化迁移 CI/CD 到 GitHub Actions

> Jenkins、Travis CI、CircleCI、GitLab CI……每个平台都有自己的一套 CI/CD 配置。GitHub Actions Importer 把这个迁移过程自动化——自动转换流水线、验证转换结果、按计划推进迁移，让平台迁移不再是一项痛苦的手工活。

## 一、项目概述

[GitHub Actions Importer](https://github.com/github/gh-actions-importer)（Stars: 1208+）是 GitHub 官方出品的 CI/CD 迁移工具，用于将现有流水线自动转换为 GitHub Actions 工作流。

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

## 八、最佳实践

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

## 十、相关资源

- [GitHub Actions Importer 官方文档](https://docs.github.com/en/actions/migrating-to-github-actions/automating-migration-with-github-actions-importer)
- [迁移学习实验室](https://github.com/actions/importer-labs)
- [GitHub Actions 官方文档](https://docs.github.com/en/actions)