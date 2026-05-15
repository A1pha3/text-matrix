---
title: "GitHub Apps pre-commit-ci：自动化的代码质量门神"
date: 2026-05-15T10:25:00+08:00
categories: ["技术笔记"]
tags: ["GitHub", "pre-commit", "CI/CD", "DevOps", "代码质量", "自动化"]
draft: false
---

# GitHub Apps pre-commit-ci：自动化的代码质量门神

> lint、format、type-check……每次提交前要跑一堆检查？pre-commit-ci 把这些全部自动化——不用本地配置，不用担心团队成员跳过检查，每次 PR 都自动跑，在合并之前就堵住代码质量问题。

## 一、什么是 pre-commit-ci

[pre-commit-ci](https://github.com/apps/pre-commit-ci) 是 GitHub 官方出品的 GitHub App，专门为 [pre-commit](https://pre-commit.com/) 生态提供云端 CI 执行能力。

核心逻辑很简单：

1. 你在仓库配置 `.pre-commit-config.yaml`
2. 开发者本地运行 `git commit` 时触发 pre-commit hooks（可选）
3. **pre-commit-ci 在 CI 中自动运行所有 hooks**，不依赖本地配置
4. PR 必须在所有检查通过后才能合并

这样做的好处是：**团队里没人能跳过检查**。哪怕有人本地没装 pre-commit，或者 `.pre-commit-config.yaml` 更新后本地没同步，CI 里都会跑最新的配置。

## 二、核心功能

### 1. 完全托管的 hook 执行

```
PR 提交
  ↓
pre-commit-ci 自动拉取最新 .pre-commit-config.yaml
  ↓
在云端隔离环境执行所有 hooks
  ↓
报告通过/失败，更新 PR 状态
```

### 2. 自动更新 hook 版本

pre-commit 的 hooks 经常更新（black、ruff、mypy……）。手动更新很烦，pre-commit-ci 可以自动帮你更新：

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0  # ← 这里会自动更新
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
```

开启 Auto-update 后，pre-commit-ci 会定期（比如每周一）发起 PR，自动更新 hooks 到最新版本。你只需要审查并合并这个更新 PR。

### 3. 失败时清晰报告

当某个 hook 失败时，pre-commit-ci 会：
- 在 PR 上留下注释，说明是哪个 hook 失败、失败原因
- 在 CI 日志中显示完整的 diff（哪些格式问题被自动检测到）
- 某些 hooks 支持自动修复（`ruff format`，`black`），pre-commit-ci 可以直接创建修复 PR

## 三、安装与配置

### 1. 安装 App

1. 访问 [pre-commit-ci App](https://github.com/marketplace/pre-commit-ci)
2. 点击 "Install"
3. 选择要启用 CI 的仓库（可以选全部或指定仓库）

### 2. 在仓库中添加配置文件

创建 `.pre-commit-ci.yaml`：

```yaml
# .pre-commit-ci.yaml
# 全局配置
version: 1

# 自动更新配置
update:
  enabled: true        # 开启自动更新 hook 版本
  schedule: weekly     # 每周一发起一次更新 PR
  
# labels 配置
labels:
  pre-commit-ci: automated    # 自动更新 PR 的标签
  
# 失败策略
failfast: true  # 有一个 hook 失败就停止，不跑后面的
```

### 3. 添加 pre-commit 配置

创建或确认 `.pre-commit-config.yaml`：

```yaml
# .pre-commit-config.yaml
repos:
  # 通用 hooks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: detect-private-key

  # Python 代码格式化
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  # Type check (Python)
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy

  # 通用安全扫描
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
```

### 4. 本地启用（可选）

```bash
# 安装 pre-commit
pip install pre-commit

# 在仓库目录初始化
cd your-repo
pre-commit install

# 手动跑一次所有 hooks（测试用）
pre-commit run --all-files
```

## 四、与 GitHub Actions 配合

pre-commit-ci 不替代完整的 CI/CD（那是 GitHub Actions 的职责），但两者可以很好地配合：

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  # pre-commit-ci 只负责代码质量检查
  pre-commit:
    uses: pre-commit-ci/github-action@v1
    with:
      args: "run --all-files"
    secrets: inherit
  
  # 其余 CI（测试、构建、部署）交给 GitHub Actions
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements-dev.txt
      - run: pytest tests/
      
  build:
    runs-on: ubuntu-latest
    needs: [pre-commit, test]
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t myapp .
```

## 五、自动修复 PR 示例

当 `ruff format` 或 `black` 发现格式问题时，pre-commit-ci 可以自动创建修复 PR：

```yaml
# .pre-commit-ci.yaml
autofix:
  enabled: true           # 开启自动修复
  autorubys: true         # 自动修复 Ruby
  autopep8: true          # 自动修复 Python 格式
  autoblack: true         # 自动修复 Python（black）
  autorruff: true         # 自动修复 Python（ruff）
```

一旦开启，每次 PR 的格式化问题会自动生成一个 `pre-commit-ci/autofix/xxx` 分支的修复 PR，你只需要合并即可。

## 六、团队使用最佳实践

### 分仓库策略

大型组织可以分级别配置：

```yaml
# 高安全级别仓库 - 严格检查
update:
  enabled: true
  schedule: daily
failfast: true

# 普通仓库 - 标准检查  
update:
  enabled: true
  schedule: weekly
failfast: false
```

### 与 CODEOWNERS 配合

在 CODEOWNERS 中指定 pre-commit 相关文件的所有者：

```
# CODEOWNERS
.pre-commit-config.yaml @your-org/devops-team
.pre-commit-ci.yaml @your-org/devops-team
```

### 与 GitHub Branch Protection 配合

```yaml
# Branch Protection Rules
require_status_checks: true
required_status_checks:
  - context: pre-commit-ci/patch  # pre-commit-ci 检查必须通过
  - context: ci/test              # 单元测试必须通过
```

## 七、为什么需要 pre-commit-ci

| 对比维度 | 本地 pre-commit | pre-commit-ci |
|---|---|---|
| 执行依赖 | 开发者本地环境 | 云端隔离环境 |
| 配置同步 | 依赖开发者手动更新 | 每次 CI 自动拉取最新配置 |
| Hook 版本 | 开发者各自为政 | 可以自动更新到最新版本 |
| 强制执行 | 开发者可能跳过 | 无法绕过 CI 检查 |
| 适用场景 | 小团队、信任基础 | 中大型团队、需要质量门禁 |

## 八、常见问题

**Q: pre-commit-ci 和 GitHub Actions 的 pre-commit action 有什么区别？**

pre-commit-ci 是专门的 GitHub App，提供自动更新、修复 PR 等高级功能。使用方式是 `uses: pre-commit-ci/github-action@v1`。而 `actions/cache` + `pre-commit` 手动配置是更灵活但需要更多维护工作的方案。

**Q: 私有仓库可以免费使用吗？**

pre-commit-ci 对公开仓库免费，私有仓库需要付费计划。具体定价查看 [GitHub Marketplace](https://github.com/marketplace/pre-commit-ci)。

## 小结

pre-commit-ci 是代码质量自动化的利器——把 pre-commit hooks 的执行从本地搬到云端，确保每次 PR 都经过一致的检查，且 hook 版本始终保持最新。对于追求代码一致性和质量门禁的团队，这是不可或缺的工具。

**相关资源：**
- [pre-commit CI App](https://github.com/apps/pre-commit-ci)
- [pre-commit 官方文档](https://pre-commit.com/)
- [Awesome Pre-commit Hooks](https://github.com/pre-commit/awesome-pre-commit)