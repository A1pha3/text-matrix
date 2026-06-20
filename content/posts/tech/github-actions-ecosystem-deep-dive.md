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

## 学习目标

读完本文后，你应能：

- 说清 Workflow / Job / Step / Action 四类对象的边界，以及 `needs` 控制执行顺序但不传文件这个设计背后的隔离意图。
- 跟着一条 `push` 事件走完触发匹配、Job 分配、Step 执行、产物上传的完整链路，定位每一步失败时该看哪层日志。
- 在 `@v4` / `@master` / SHA 固定三种引用粒度里做选择，说出各自对应的供应链风险等级。
- 判断自己的自动化需求该用 Composite Action、JavaScript Action 还是 Docker Action，以及什么时候该迁移到 GitHub Apps 而不是继续堆 workflow。

## 目录

1. [什么是 GitHub Actions](#1-什么是-github-actions)
2. [快速上手：一个完整工作流](#2-快速上手一个完整工作流)
3. [GitHub Actions Marketplace](#3-github-actions-marketplace)
4. [自定义 Action 开发](#4-自定义-action-开发)
5. [GitHub Agentic Workflows 中的 Actions](#5-github-agentic-workflows-中的-actions)
6. [高级特性](#6-高级特性)
7. [GitHub Actions 与 GitHub Apps 的区别](#7-github-actions-与-github-apps-的区别)
8. [从哪里开始](#8-从哪里开始)
9. [常见问题排查](#常见问题排查)
10. [自测题](#自测题)
11. [进阶路径](#进阶路径)

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
| `actions/cache@v4` | 缓存依赖与构建产物 |
| `actions/github-script@v7` | 在 Step 中直接调用 GitHub API |
| `softprops/action-gh-release@v2` | 创建 GitHub Release（社区维护，事实标准） |

> 注：Dependabot 不是 Action，而是 GitHub 内置功能，通过仓库根目录的 `.github/dependabot.yml` 配置文件启用，无需在 workflow 里 `uses:`。早期的 `actions/create-release@v1` 已被官方归档，发布 Release 改用 `softprops/action-gh-release@v2` 或 `actions/github-script@v7` 直接调用 Releases API。

### 版本锁定策略

```yaml
# ✅ 推荐：锁定 Action 版本（避免供应链攻击）
- uses: actions/checkout@v4

# ❌ 避免：使用 @master 或 @latest（版本漂移风险）
# - uses: actions/checkout@master

# ✅ 推荐：指定版本范围
- uses: actions/checkout@v4.1.0

# ✅ 推荐：使用 SHA 固定版本（最高安全级别）
- uses: actions/checkout@11c0af8e7a0da7e71dbb23e6a26b5d31c4a21b15
```

引用 Action 有三种粒度：`@v4` 这类 major tag 跟随大版本更新，兼容性可控；`@master` / `@latest` 跟随分支或最新 tag，行为不可预测，供应链攻击面最大；SHA 固定最严格，任何改动都会在 commit 历史里显式体现。生产环境建议至少用 major tag，对安全敏感的流水线（如发布、部署）用 SHA 固定。介于两者之间的 `@v4.1.0` 这类 minor/patch tag 兼顾稳定性和可读性，适合需要明确版本但又不打算每次提交都更新 SHA 的场景。

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

三个容易踩的坑会在下面「常见问题排查」一节展开，这里先列结论：

1. **不要把 Secret 写进 workflow YAML**——用 `${{ secrets.XXX }}` 注入，Runner 会自动脱敏日志。但 secret 一旦被拼进命令行参数或写进文件，脱敏就失效了。
2. **`needs` 不传文件**——Job 之间的文件共享靠 `upload-artifact` / `download-artifact`，别指望上一个 Job 的文件系统残留。每个 Job 跑在独立 Runner 上，文件系统天然隔离。
3. **OIDC 比长期 Token 安全得多**——用 AWS/GCP/Azure 时，优先配 OIDC 联邦而不是手动塞 Access Key。长期 Key 一旦泄露，轮换和审计的成本远高于一次性配 OIDC。

最后回到 Actions 和 GitHub Apps 的分工：Actions 适合仓库内事件驱动的自动化，GitHub Apps 适合跨仓库、需要持久状态的集成。如果发现自己在一个 workflow 里维护大量跨仓库逻辑或长期运行的 Webhook 服务，该考虑迁移到 GitHub Apps。

## 常见问题排查

### Job 一直卡在 queued 不进 in_progress

最常见的原因是 Runner 槽位耗尽。GitHub 托管 Runner 对免费账号有并发额度（通常 20 个并发 Job），自托管 Runner 池容量不足时也会排队。先看仓库 Settings → Actions → Runners 列表里有没有 idle 的 Runner，再确认账号的并发额度。Matrix 策略 3×3×3 = 27 个 Job 是常见的爆量来源，必要时用 `max-parallel` 限流：

```yaml
strategy:
  max-parallel: 5
  matrix:
    # ...
```

另一个隐蔽原因是 `environment` 字段绑定了 required reviewers，Job 会停在 queued 等审批。检查 workflow 里的 `environment:` 配置和仓库 Settings → Environments 的审批规则。

### artifact 下载失败或为空

`actions/upload-artifact@v4` 与 `@v3` 不兼容，跨大版本无法互传产物。确认上传和下载用同一个 major 版本。`path` 必须是 Runner 工作目录下的相对路径，绝对路径或 `..` 跳出工作目录都会失败。空目录上传会被静默丢弃，下载时报 "no artifact found"。默认保留期 90 天，仓库可改短到 1 天，过期后 `download-artifact` 直接 404。

跨 Job 共享时还要注意 `name` 必须一致：

```yaml
# 上传 Job
- uses: actions/upload-artifact@v4
  with:
    name: build-output        # 这个名字
    path: dist/

# 下载 Job
- uses: actions/download-artifact@v4
  with:
    name: build-output        # 必须对上
```

### Secret 在日志里没有脱敏成 `***`

Runner 的脱敏只对**完整匹配 secret 字面值**的日志行生效。一旦 secret 被拆开、拼接、转码或写进文件再 cat 出来，脱敏就失效。典型踩坑场景：

```bash
# ❌ 拼进命令行参数，ps 可见，脱敏失效
./deploy.sh --token ${{ secrets.DEPLOY_TOKEN }}

# ❌ 写进文件再输出，文件内容不是 secret 字面值
echo "token=${{ secrets.DEPLOY_TOKEN }}" > .env
cat .env

# ✅ 通过环境变量传递，Runner 仍能脱敏
env:
  DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
run: ./deploy.sh --token "$DEPLOY_TOKEN"
```

如果 secret 是 JSON 或包含特殊字符，先用 `base64` 编码再注入，运行时解码，避免 shell 转义把字面值打散。

### Runner 并发额度耗尽

GitHub 托管 Runner 的并发额度按账号计费档位分配，免费档通常 20 个。Matrix 笛卡尔积是主要爆量来源，3 维度各 3 值就是 27 个 Job，单次 push 直接超限。处理方式按场景选：

- **测试矩阵**：用 `max-parallel` 限流，或把低频组合挪到 nightly schedule。
- **多服务构建**：拆成多个 workflow，按服务粒度触发（paths 过滤），避免一次 push 触发全量。
- **长期高并发**：上自托管 Runner 或 Larger Runner（付费档），自托管 Runner 不占托管额度。

### workflow 触发了但 Job 没跑

先看 `on` 字段的事件过滤是否命中。`push.branches` 和 `pull_request.branches` 的语义不同：`push` 看的是**推送目标分支**，`pull_request` 看的是**PR 的 base 分支**。`paths` 过滤只对 `push` 和 `pull_request` 生效，`workflow_dispatch` 和 `schedule` 不看 paths。Tag 触发用 `push.tags`，写错成 `push.branches` 是常见误用。

另一个原因是 workflow 文件在默认分支上不存在。GitHub 只从默认分支读取 workflow 定义，feature 分支上改 workflow 不会生效，必须先合并到 main/master。

## 自测题

<details>
<summary>1. `needs: [lint, test]` 声明后，`build` Job 能直接读到 `test` Job 里 `npm test` 生成的 `coverage/` 目录吗？为什么？</summary>

不能。`needs` 只控制执行顺序，不传递文件。每个 Job 跑在独立 Runner 上，文件系统天然隔离。跨 Job 共享产物必须用 `actions/upload-artifact` 上传、`actions/download-artifact` 下载。
</details>

<details>
<summary>2. 同一个 Action 引用，`@v4`、`@master`、SHA 固定三种方式在供应链安全上的差异是什么？生产环境发布流水线该选哪种？</summary>

`@v4` 跟随 major tag，维护者可以在 v4 下推送任意 commit，兼容性可控但存在被篡改风险；`@master` 跟随分支，行为完全不可预测，供应链攻击面最大；SHA 固定最严格，任何改动都会在 commit 历史里显式体现，但更新需要手动改 SHA。生产发布流水线建议用 SHA 固定，配合 Dependabot 自动提 PR 升级 SHA，兼顾安全和可维护性。
</details>

<details>
<summary>3. 为什么把 `${{ secrets.API_KEY }}` 直接拼进 `run: ./call-api --key ${{ secrets.API_KEY }}` 会导致日志脱敏失效？正确写法是什么？</summary>

Runner 的脱敏只对日志中完整匹配 secret 字面值的字符串生效。直接拼进命令行参数后，`ps`、shell 错误信息或子进程的 stderr 可能输出被截断、转义或重组的 token 片段，不再完整匹配字面值，脱敏失效。正确写法是通过 `env` 注入环境变量，子进程读环境变量而不是命令行参数：

```yaml
env:
  API_KEY: ${{ secrets.API_KEY }}
run: ./call-api --key "$API_KEY"
```
</details>

<details>
<summary>4. Matrix 策略 `node-version: [18, 20, 22]` × `os: [ubuntu-latest, windows-latest, macos-latest]` 会生成多少个 Job？如果免费账号并发额度是 20，会发生什么？</summary>

9 个 Job（3×3 笛卡尔积）。如果账号并发额度是 20，单次触发不会超限，但叠加其他 workflow 同时触发就可能排队。如果加上 `exclude` 排除 1 个组合就是 8 个。如果再加一个维度（如 `arch: [x64, arm64]`）就变成 18 个，接近上限。建议用 `max-parallel` 限流，避免单次 push 占满全部额度影响其他 workflow。
</details>

<details>
<summary>5. Dependabot 应该在 workflow 里 `uses: github/dependabot-action@v2` 调用，还是在仓库根目录放 `.github/dependabot.yml`？为什么？</summary>

放 `.github/dependabot.yml`。Dependabot 是 GitHub 内置功能，由 GitHub 服务端按配置文件定期扫描，不需要在 workflow 里 `uses:` 调用。`github/dependabot-action` 这个引用本身不准确，Dependabot 的运行不依赖 Actions Runner。配置文件方式还能享受 GitHub 的内置 PR 模板、安全公告关联和 rate limit 豁免。
</details>

## 进阶路径

读完本文后，可以按以下方向继续深入：

- **Self-hosted Runner 安全治理**：自托管 Runner 拿到仓库代码和 secret，在 PR 触发场景下存在被恶意 fork 提交代码执行的风险。需要理解 `pull_request_target` 与 `pull_request` 的权限差异、Runner 标签隔离、ephemeral Runner（容器化、用完即销毁）的部署模式。生产环境推荐用 ARC（Actions Runner Controller）在 Kubernetes 上跑 ephemeral Runner。
- **Reusable Workflow**：当多个仓库的 CI 流程趋同时，把 workflow 定义抽到一个中央仓库，其他仓库用 `uses: org/repo/.github/workflows/ci.yml@v1` 引用。配合 `workflow_call` 的 `inputs` 和 `secrets` 传参，可以实现组织级 CI 标准化，避免每个仓库维护一份雷同的 YAML。注意 reusable workflow 的权限继承和 secret 传递规则与普通 workflow 不同。
- **Organization-level Secrets 治理**：组织级 secret 可以按仓库或环境分发，配合 required reviewers 和 deployment branch 限制实现细粒度访问控制。进阶玩法包括用 OIDC 联邦把云厂商凭证完全从 secret 里移除、用 GitHub API 自动轮换 secret、用 audit log 追踪 secret 访问记录。组织级 secret 的访问策略（all repositories / selected repositories）需要和团队边界对齐，避免过度暴露。

**相关资源：**
- [GitHub Actions 官方文档](https://docs.github.com/en/actions)
- [Actions Marketplace](https://github.com/marketplace?type=actions)
- [awesome-actions](https://github.com/sdras/awesome-actions) - 社区精选 Actions 列表
- [gh-aw-actions](https://github.com/github/gh-aw-actions) - GitHub Agentic Workflows 共享 Action 库
