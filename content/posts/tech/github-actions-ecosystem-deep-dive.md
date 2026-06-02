---
title: "GitHub Actions 生态入门：从基础工作流到自定义 Action 开发"
date: 2026-05-15T10:25:00+08:00
categories: ["技术笔记"]
tags: ["GitHub", "GitHub Actions", "CI/CD", "DevOps", "自动化", "Action"]
draft: false
---

# GitHub Actions 生态入门：从基础工作流到自定义 Action 开发

> GitHub Actions 把 GitHub 仓库事件（push、PR、release）变成了自动化触发器。它的设计核心不是"能跑脚本"，而是把自动化拆成了三层可组合的抽象——事件触发层、Job 编排层、Action 组件层——每一层解决不同的可靠性问题。读完这篇文章，你应该能判断：什么时候用社区 Action、什么时候自己写、以及 Actions 和 GitHub Apps 的边界在哪里。

## 一、什么是 GitHub Actions

[GitHub Actions](https://github.com/features/actions) 是 GitHub 内置的 CI/CD 和自动化平台。它通过 **YAML 工作流文件** 定义自动化任务，响应 GitHub 仓库中的各种事件（push、PR、release、issue 等）。

先看一个简化版的总览——搞清楚这套系统里几样东西怎么分工：

| 概念 | 负责什么 | 一句话定位 |
|---|---|---|
| **Workflow** | 定义"什么时候干什么" | 自动化脚本的总入口 |
| **Job** | 分配运行环境和执行顺序 | Workflow 里的执行单元 |
| **Step** | 实际干活 | Job 里的最小步骤 |
| **Action** | 封装可复用逻辑 | 别人写好的 Step 组件 |

Workflow 收到事件后，把任务分给多个 Job（默认并行），每个 Job 里顺序执行 Step。Step 可以是 shell 命令，也可以引用现成的 Action——这就是 Actions 生态的核心：你不必从零写每一步。

核心概念：

- **Workflow（工作流）**：定义在 `.github/workflows/*.yml` 中，是自动化的顶层单元
- **Job（任务）**：工作流中的一个步骤集合，默认并行执行
- **Step（步骤）**：Job 中的最小单元，可以是 shell 命令或 Action
- **Action（动作）**：可复用的自动化组件，可以是 JavaScript/TypeScript、Docker 容器或 Composite（脚本集合）

## 二、快速上手：一个完整工作流

### 基础 Node.js CI 工作流

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run tests
        run: npm test
      
      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage/

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Build Docker image
        run: |
          docker build -t myapp:${{ github.sha }} .
          docker push myapp:${{ github.sha }}
```

这个工作流里有一条隐藏的执行链，值得拆开看：当你在 `develop` 分支 push 代码时，GitHub 的 **事件系统** 匹配到 `on.push.branches: [main, develop]`，触发了 Workflow。Workflow 里定义了两个 Job——`test` 和 `build`——因为 `build` 写了 `needs: test`，所以 `test` 先跑。

`test` Job 被分配到 `ubuntu-latest` Runner 上，Runner 按 Step 顺序执行：先 checkout 代码（`actions/checkout@v4`），再装 Node.js，再跑 `npm ci` 和 `npm test`。如果 `npm test` 返回非零退出码，Job 失败，`build` 不会启动。如果全部通过，Runner 上传 coverage 产物，然后 `build` Job 启动，构建 Docker 镜像。

这个链条里真正值得关注的是两个点：**Step 的原子性**（每个 Step 要么全过要么失败，上一个 Step 的产物自动保留到下一个 Step）和 **Job 间的数据传递**（`needs` 只控制执行顺序，不传递文件——文件传递靠 `upload-artifact` / `download-artifact`）。

### 触发条件（on）详解

```yaml
on:
  # 特定分支和路径
  push:
    branches: [main]
    paths:
      - 'src/**'
      - '*.go'
      - '!.tmp/**'
  
  # PR 类型过滤
  pull_request:
    types: [opened, synchronize, reopened]
  
  # 手动触发
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deploy environment'
        required: true
        default: 'staging'
  
  # 定时触发
  schedule:
    - cron: '0 3 * * *'  # 每天凌晨3点
  
  # 外部事件（repository_dispatch）
  repository_dispatch:
    types: [deploy]
  
  # Tag 触发
  push:
    tags:
      - 'v*'
```

## 三、GitHub Actions  Marketplace

GitHub Actions Marketplace 是发现和分发自动化组件的地方。你可以直接在 workflow 中引用社区维护的 Actions。

### 热门官方 Actions

| Action | 用途 |
|---|---|
| `actions/checkout@v4` | 克隆仓库代码 |
| `actions/setup-node@v4` | 配置 Node.js 环境 |
| `actions/setup-python@v5` | 配置 Python 环境 |
| `actions/upload-artifact@v4` | 上传构建产物 |
| `actions/download-artifact@v4` | 下载构建产物 |
| `actions/create-release@v1` | 创建 GitHub Release |
| `github/dependabot-action@v2` | 运行 Dependabot 更新 |

### 使用 Actions 的最佳实践

```yaml
# ✅ 推荐：锁定 Action 版本（避免供应链攻击）
- uses: actions/checkout@v4

# ❌ 避免：使用 @master 或 @latest（版本漂移风险）
# - uses: actions/checkout@master

# ✅ 推荐：指定版本范围
- uses: actions/checkout@bypass-clean

# ✅ 推荐：使用 SHA 固定版本（最高安全级别）
- uses: actions/checkout@11c0af8e7a0da7e71dbb23e6a26b5d31c4a21b15
```

## 四、自定义 Action 开发

### 类型一：JavaScript/TypeScript Action

适合轻量级、与 GitHub API 交互的场景。

**项目结构：**

```
my-action/
├── action.yml          # Action 元数据
├── package.json
├── src/
│   └── main.ts         # 入口代码
└── dist/
    └── index.js        # 编译输出
```

**action.yml：**

```yaml
name: 'My Custom Action'
description: 'A demo custom action'
author: 'Your Name'

inputs:
  repo-token:
    description: 'GitHub token'
    required: true
  message:
    description: 'Message to comment'
    required: false
    default: 'Hello from custom action!'

runs:
  using: 'node20'
  main: 'dist/index.js'
```

**src/main.ts：**

```typescript
import * as core from '@actions/core';
import * as github from '@actions/github';

async function run() {
  const token = core.getInput('repo-token', { required: true });
  const message = core.getInput('message');
  const { context } = github;

  const octokit = github.getOctokit(token);
  
  await octokit.rest.issues.createComment({
    owner: context.repo.owner,
    repo: context.repo.repo,
    issue_number: context.issue.number,
    body: message
  });

  core.setOutput('result', 'Comment posted successfully');
}

run().catch(error => {
  core.setFailed(error.message);
});
```

**打包：**

```bash
npm install
npm run build
```

### 类型二：Docker 容器 Action

适合需要在隔离环境中运行的场景（如需要特定工具链）。

**action.yml：**

```yaml
name: 'Docker Action Demo'
description: 'Run a task in a Docker container'

inputs:
  image:
    description: 'Docker image to use'
    required: true
  args:
    description: 'Arguments to pass'

runs:
  using: 'docker'
  image: 'Dockerfile'
  args:
    - ${{ inputs.args }}
```

**Dockerfile：**

```dockerfile
FROM ubuntu:22.04

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
```

**entrypoint.sh：**

```bash
#!/bin/bash
set -e
echo "Hello from Docker action!"
echo "Input image: $INPUT_IMAGE"
echo "Args: $INPUT_ARGS"
```

### 类型三：Composite Action（脚本集合）

最简单的自定义 Action，直接组合现有 Actions 和脚本。

```yaml
# action.yml
name: 'Deploy to Cloud'
description: 'Build, tag, and deploy container to cloud'

inputs:
  environment:
    description: 'Target environment'
    required: true
  image:
    description: 'Container image'
    required: true

outputs:
  deployed-url:
    description: 'URL of deployed resource'
    value: ${{ steps.deploy.outputs.url }}

runs:
  using: 'composite'
  steps:
    - name: Login to registry
      uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Tag image
      run: |
        docker tag ${{ inputs.image }} \
          ghcr.io/${{ github.repository }}:${{ github.sha }}

    - name: Push image
      run: docker push ghcr.io/${{ github.repository }}:${{ github.sha }}

    - name: Deploy
      id: deploy
      run: |
        url=$(kubectl rollout status deployment/myapp)
        echo "url=$url" >> $GITHUB_OUTPUT

    - name: Notify
      run: |
        echo "Deployed to ${{ inputs.environment }} successfully"
```

## 五、GitHub Agentic Workflows 中的 Actions

GitHub 官方提供了 [gh-aw-actions](https://github.com/github/gh-aw-actions) 作为 Agentic Workflows 的共享 Action 库：

```yaml
# 使用官方共享 Actions
jobs:
  agent-workflow:
    runs-on: ubuntu-latest
    steps:
      # MCP server 文件管理
      - uses: github/gh-aw-actions/mcp-file-manager@v1
        with:
          operation: 'provision'
          mcp-config: './mcp.json'
      
      # 任务协调
      - uses: github/gh-aw-actions/task-coordinator@v1
        with:
          workflow: 'code-review'
          context: ${{ toJson(github.event.inputs) }}
```

## 六、高级特性

### 1. Matrix 策略（并行测试）

```yaml
jobs:
  test:
    strategy:
      matrix:
        node-version: [18, 20, 22]
        os: [ubuntu-latest, windows-latest]
        exclude:
          - node-version: 22
            os: windows-latest  # 排除不兼容组合
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm test
```

### 2. 依赖关系与条件执行

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - run: npm run lint
  
  test:
    needs: lint  # 必须等 lint 完成
    runs-on: ubuntu-latest
    steps:
      - run: npm test
  
  deploy:
    needs: [lint, test]
    if: github.ref == 'refs/heads/main'  # 仅 main 分支部署
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://myapp.com
```

### 3. 秘密变量与环境

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://myapp.com
    env:
      DB_HOST: ${{ secrets.DB_HOST }}
      API_KEY: ${{ secrets.API_KEY }}
    steps:
      - name: Deploy
        run: ./deploy.sh
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
```

### 4. 缓存依赖

```yaml
steps:
  - uses: actions/checkout@v4
  
  - name: Cache npm packages
    uses: actions/cache@v4
    with:
      path: ~/.npm
      key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}
      restore-keys: |
        ${{ runner.os }}-npm-

  - name: Install
    run: npm ci
```

### 5. OIDC 联邦（无密钥部署）

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789012:role/github-actions
    aws-region: us-east-1
```

## 七、GitHub Actions 与 GitHub Apps 的区别

| 维度 | GitHub Actions | GitHub Apps |
|---|---|---|
| 触发方式 | 仓库事件（push/PR等） | Webhook 事件推送 |
| 运行位置 | GitHub 托管或自托管 runner | 外部服务器 |
| 权限模型 | GITHUB_TOKEN | App Installation Token |
| 适用场景 | CI/CD、自动化构建 | 外部集成、数据处理 |
| 安装方式 | workflow 文件引用 | GitHub Marketplace 安装 |

两者可以配合使用：Actions 触发外部 App 处理复杂逻辑，App 将结果通过 API 写回 GitHub。

## 从哪里开始

GitHub Actions 的上手路径取决于你当前的需求：

- **只想跑个 CI**：从 Marketplace 找现成的 Action（`checkout` + `setup-node` + `cache` 三件套基本够用），只写 shell 命令级别的 Step。
- **团队需要统一自动化逻辑**：写 Composite Action，把多步脚本打包成一个可引用的单元，放在同一个仓库或组织的 `.github` 仓库里共享。
- **需要和外部系统交互或复杂逻辑**：用 JavaScript/TypeScript Action，调 GitHub API 或第三方服务，然后把编译后的 `dist/index.js` 提交到仓库。
- **需要隔离的工具链或特殊运行时**：用 Docker 容器 Action。

三个容易踩的坑：

1. **不要把 Secret 写进 workflow YAML**——用 `${{ secrets.XXX }}` 注入，Runner 会自动脱敏日志。
2. **`needs` 不传文件**——Job 之间的文件共享靠 `upload-artifact` / `download-artifact`，别指望上一个 Job 的文件系统残留。
3. **OIDC 比长期 Token 安全得多**——如果你用 AWS/GCP/Azure，优先配 OIDC 联邦而不是手动塞 Access Key。

最后，Actions 和 GitHub Apps 的分工值得再强调一遍：**Actions 适合"仓库内事件驱动的自动化"**，GitHub Apps 适合"跨仓库、需要持久状态的集成"。如果你发现自己在一个 workflow 里维护大量跨仓库逻辑或需要长期运行的 Webhook 服务，那可能是 GitHub Apps 的地盘。

**相关资源：**
- [GitHub Actions 官方文档](https://docs.github.com/en/actions)
- [Actions Marketplace](https://github.com/marketplace?type=actions)
- [awesome-actions](https://github.com/sdras/awesome-actions) - 社区精选 Actions 列表
- [gh-aw-actions](https://github.com/github/gh-aw-actions) - GitHub Agentic Workflows 共享 Action 库