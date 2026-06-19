---
title: "GitHub Actions 生态：从基础工作流到自定义 Action 开发"
date: 2026-05-15T10:25:00+08:00
categories: ["技术笔记"]
tags: ["GitHub", "GitHub Actions", "CI/CD", "DevOps", "自动化", "Action"]
draft: false
slug: github-actions-ecosystem-deep-dive
description: "GitHub Actions 把仓库事件变成自动化触发器。本文拆解事件触发层、Job 编排层、Action 组件层三层抽象，覆盖工作流语法、Context 变量、Secrets 管理和自定义 Action 开发全链路。"
---

# GitHub Actions 生态：从基础工作流到自定义 Action 开发

> GitHub Actions 把仓库事件（push、PR、release）变成自动化触发器。它把自动化拆成三层抽象：事件触发层决定"什么时候跑"，Job 编排层决定"在哪跑、按什么顺序跑"，Action 组件层决定"每一步具体做什么"。三层各解决一类可靠性问题——触发层管事件匹配的确定性，编排层管执行环境隔离与依赖顺序，组件层管逻辑复用与供应链安全。读完这篇文章，你能判断什么时候用社区 Action、什么时候自己写，以及 Actions 和 GitHub Apps 的边界划在哪里。

## 1. 什么是 GitHub Actions

[GitHub Actions](https://github.com/features/actions) 是 GitHub 内置的 CI/CD 和自动化平台。它通过 YAML 工作流文件定义自动化任务，响应仓库中的事件（push、PR、release、issue 等）。

整套系统由四类对象分工，先看它们各自的边界：

| 概念 | 负责什么 | 在系统中的位置 |
|---|---|---|
| **Workflow** | 定义"什么时候干什么" | 自动化的顶层单元，放在 `.github/workflows/*.yml` |
| **Job** | 分配运行环境和执行顺序 | Workflow 里的执行单元，默认并行 |
| **Step** | 实际执行命令或调用 Action | Job 里的最小步骤，顺序执行 |
| **Action** | 封装可复用逻辑 | 别人写好的 Step 组件，三种形态：JavaScript/TypeScript、Docker、Composite |

Workflow 收到事件后，把任务分给多个 Job（默认并行），每个 Job 里顺序执行 Step。Step 可以是 shell 命令，也可以引用现成的 Action，复用别人写好的逻辑。

## 2. 快速上手：一个完整工作流

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

当你在 `develop` 分支 push 代码时，GitHub 的事件系统匹配到 `on.push.branches: [main, develop]`，触发 Workflow。Workflow 里定义了 `test` 和 `build` 两个 Job，因为 `build` 声明了 `needs: test`，所以 `test` 先跑。

`test` Job 被分配到 `ubuntu-latest` Runner 上，Runner 按 Step 顺序执行：先 checkout 代码（`actions/checkout@v4`），再装 Node.js，再跑 `npm ci` 和 `npm test`。如果 `npm test` 返回非零退出码，Job 失败，`build` 不会启动。全部通过后，Runner 上传 coverage 产物，`build` Job 启动，构建 Docker 镜像。

这条执行链里有两个设计要点：**Step 的原子性**——每个 Step 要么全过要么失败，上一个 Step 的产物自动保留到下一个 Step 的文件系统；**Job 间的数据隔离**——`needs` 只控制执行顺序，不传递文件，跨 Job 共享文件必须靠 `upload-artifact` / `download-artifact`。这个隔离是有意为之：每个 Job 跑在独立 Runner 上，文件系统不共享，避免上一个 Job 的残留污染下一个 Job。

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

`on` 字段支持事件过滤、路径过滤、手动输入、定时任务和外部事件。其中 `workflow_dispatch` 适合发布类操作（需要人工确认环境），`schedule` 适合定时巡检（注意 cron 用的是 UTC 时间），`repository_dispatch` 适合从外部系统（如另一个仓库的 workflow 或第三方服务）通过 API 触发。

## 3. GitHub Actions Marketplace

[Marketplace](https://github.com/marketplace?type=actions) 是社区 Actions 的索引站，可以直接在 workflow 中引用。下面是几类高频官方 Action：

| Action | 用途 |
|---|---|
| `actions/checkout@v4` | 克隆仓库代码 |
| `actions/setup-node@v4` | 配置 Node.js 环境 |
| `actions/setup-python@v5` | 配置 Python 环境 |
| `actions/upload-artifact@v4` | 上传构建产物 |
| `actions/download-artifact@v4` | 下载构建产物 |
| `actions/create-release@v1` | 创建 GitHub Release |
| `github/dependabot-action@v2` | 运行 Dependabot 更新 |

### 版本锁定策略

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

引用 Action 有三种粒度：`@v4` 这类 major tag 跟随大版本更新，兼容性可控；`@master` / `@latest` 跟随分支或最新 tag，行为不可预测，供应链攻击面最大；SHA 固定最严格，任何改动都会在 commit 历史里显式体现。生产环境建议至少用 major tag，对安全敏感的流水线（如发布、部署）用 SHA 固定。上例中的 `@bypass-clean` 是分支引用，稳定性介于 major tag 和 `@master` 之间，仅在该分支确实维护了稳定语义时才适合使用。

## 4. 自定义 Action 开发

当社区 Action 不能满足需求时，可以自己写。Action 有三种形态，选择依据是运行时需求和隔离边界：

- **JavaScript/TypeScript Action**：跑在 Runner 的 Node.js 进程里，启动快，适合调 GitHub API 或做轻量逻辑。
- **Docker 容器 Action**：跑在独立容器里，环境完全隔离，适合需要特定工具链（如旧版编译器、特殊 CLI）的场景。代价是每次都要拉镜像，启动慢。
- **Composite Action**：把多个 Step 打包成一个可引用单元，不引入新运行时，适合团队内复用多步脚本。

### 类型一：JavaScript/TypeScript Action

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

JavaScript Action 必须把编译产物 `dist/index.js` 一起提交到仓库——Runner 执行时直接跑这个文件，不会替你跑 `npm install` 和 `npm run build`。`using: 'node20'` 指定 Runner 内置的 Node.js 运行时，目前主流 Runner 支持 `node16` 和 `node20`。

### 类型二：Docker 容器 Action

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

Docker Action 的输入通过环境变量传递，变量名是 `INPUT_` 加上 input 名大写。`entrypoint.sh` 必须以非零退出码表示失败，`set -e` 确保任何命令失败立即退出。注意：Docker Action 只能在 Linux Runner 上运行。

### 类型三：Composite Action（脚本集合）

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

Composite Action 把多个 Step 打包，调用方只写一行 `uses:`。它不引入新运行时，所有 Step 跑在调用方的 Runner 上。`outputs` 通过 `steps.<id>.outputs.<name>` 暴露给调用方，`$GITHUB_OUTPUT` 是当前 Runner 写出 step output 的标准方式（旧版用 `::set-output`，已废弃）。

## 5. GitHub Agentic Workflows 中的 Actions

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

Agentic Workflows 把 LLM 调用、MCP（Model Context Protocol）server 编排和任务协调封装成 Action，让 agent 之间的协作也走 Step + Job 的编排模型。这套库还在早期演进中，API 可能变动，引用时建议锁定具体版本。

## 6. 高级特性

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

Matrix 把一组变量做笛卡尔积，每个组合跑一个 Job。上例生成 5 个 Job（3×2 减去 1 个 exclude）。适合多版本兼容性测试。代价是 Job 数量爆炸——3 个维度各 3 个值就是 27 个 Job，会快速吃满并发额度。

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

`needs` 建立执行顺序，`if` 做条件过滤。`environment` 字段不仅声明运行环境，还会触发 GitHub 的环境保护规则（如 required reviewers、deployment branch 限制）——这是把部署门禁写进 workflow 的标准方式。

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

Secret 注入有三层粒度：仓库级（Settings → Secrets）、环境级（绑定到 `environment`，可配审批）、组织级（跨仓库共享）。`env` 可以写在 Job 级（所有 Step 可见）或 Step 级（仅该 Step 可见）。Runner 会在日志里把 secret 值替换成 `***`，但要注意：把 secret 拼进命令行参数或写进文件后，脱敏不再生效。

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

缓存按 `key` 命中，命中时跳过下载；未命中时按 `restore-keys` 做前缀模糊匹配，部分命中也能加速。`hashFiles` 把 lockfile 内容算进 key，依赖变了缓存自动失效。`actions/setup-node@v4` 内置了 `cache: 'npm'` 选项，能省掉单独写缓存 Step。

### 5. OIDC 联邦（无密钥部署）

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789012:role/github-actions
    aws-region: us-east-1
```

OIDC（OpenID Connect）让 Runner 用一个短期 token 向云厂商换取临时凭证，不再把长期 Access Key 塞进 Secret。token 由 GitHub 签发，云厂商验证签名后发放几分钟到几小时有效的凭证。配置一次后，凭证轮换、泄露面、审计链路都比长期 Key 好得多。AWS、GCP、Azure 都支持，前提是在云侧配置好信任关系（trust policy）。

## 7. GitHub Actions 与 GitHub Apps 的区别

| 维度 | GitHub Actions | GitHub Apps |
|---|---|---|
| 触发方式 | 仓库事件（push/PR 等） | Webhook 事件推送 |
| 运行位置 | GitHub 托管或自托管 runner | 外部服务器 |
| 权限模型 | GITHUB_TOKEN | App Installation Token |
| 适用场景 | CI/CD、自动化构建 | 外部集成、数据处理 |
| 安装方式 | workflow 文件引用 | GitHub Marketplace 安装 |

两者可以配合：Actions 触发外部 App 处理复杂逻辑，App 把结果通过 API 写回 GitHub。判断边界的经验法则——如果自动化逻辑围绕"仓库内事件 + 有限步骤 + 无状态"，用 Actions；如果需要"跨仓库协调、持久状态、长期运行的 Webhook 服务"，用 GitHub Apps。把跨仓库逻辑硬塞进一个 workflow，维护成本会快速上升。

## 8. 从哪里开始

GitHub Actions 的采用顺序建议从现成 Action 起步，再过渡到 Composite，最后才考虑自己写 JavaScript 或 Docker Action——复杂度递增，维护成本也递增。具体取决于当前需求：

- **只想跑个 CI**：从 Marketplace 找现成的 Action（`checkout` + `setup-node` + `cache` 三件套基本够用），只写 shell 命令级别的 Step。这一步几乎零维护成本。
- **团队需要统一自动化逻辑**：写 Composite Action，把多步脚本打包成一个可引用单元，放在组织级 `.github` 仓库里共享。维护成本集中在脚本本身，不引入额外运行时。
- **需要和外部系统交互或复杂逻辑**：用 JavaScript/TypeScript Action 调 GitHub API 或第三方服务，把编译后的 `dist/index.js` 提交到仓库。维护成本包括依赖升级和 dist 同步。
- **需要隔离的工具链或特殊运行时**：用 Docker 容器 Action。维护成本最高，每次运行都要拉镜像，且只能在 Linux Runner 上跑。

三个容易踩的坑：

1. **不要把 Secret 写进 workflow YAML**——用 `${{ secrets.XXX }}` 注入，Runner 会自动脱敏日志。但 secret 一旦被拼进命令行参数或写进文件，脱敏就失效了。
2. **`needs` 不传文件**——Job 之间的文件共享靠 `upload-artifact` / `download-artifact`，别指望上一个 Job 的文件系统残留。每个 Job 跑在独立 Runner 上，文件系统天然隔离。
3. **OIDC 比长期 Token 安全得多**——用 AWS/GCP/Azure 时，优先配 OIDC 联邦而不是手动塞 Access Key。长期 Key 一旦泄露，轮换和审计的成本远高于一次性配 OIDC。

最后回到 Actions 和 GitHub Apps 的分工：Actions 适合仓库内事件驱动的自动化，GitHub Apps 适合跨仓库、需要持久状态的集成。如果发现自己在一个 workflow 里维护大量跨仓库逻辑或长期运行的 Webhook 服务，该考虑迁移到 GitHub Apps。

**相关资源：**
- [GitHub Actions 官方文档](https://docs.github.com/en/actions)
- [Actions Marketplace](https://github.com/marketplace?type=actions)
- [awesome-actions](https://github.com/sdras/awesome-actions) - 社区精选 Actions 列表
- [gh-aw-actions](https://github.com/github/gh-aw-actions) - GitHub Agentic Workflows 共享 Action 库
