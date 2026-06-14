---
title: "GitHub Merge Queue 自动化 PR 合入完全指南"
date: 2026-05-17
draft: false
author: "钳岳星君"
categories: ["技术"]
tags: ["GitHub", "DevOps", "CI/CD", "Pull Request", "Merge Queue"]
description: "深入解析 GitHub Merge Queue 的工作原理、配置方法和生产级最佳实践，不堆功能清单，只讲你真正需要关心的东西。"
slug: github-merge-queue-automated-pr-merging-guide
---

# GitHub Merge Queue 自动化 PR 合入完全指南

GitHub Merge Queue 解决的不是"怎么合 PR"，而是"多个 PR 同时就绪时，怎么避免每次合入都重新排队等 CI、重新解决冲突"。它把合入从单次手动操作变成批量自动验证流水线——理解这一点，后面所有配置才有意义。

本文覆盖 GitHub 原生 Merge Queue 的完整配置链路，以及 [github-merge-queue](https://github.com/apps/github-merge-queue) App 的增强能力。读完你会知道：这套机制在什么场景下省时间、在什么场景下反而添乱，以及怎么配才能让它真正跑起来。

<!--more-->

## 读完你会

- [ ] 说清 Merge Queue 三条核心线（Batch、Group Merging、Stack）各自管什么、不管什么
- [ ] 写一份能同时处理 `pull_request` 和 `merge_group` 事件的 GitHub Actions workflow
- [ ] 判断自己团队的 PR 量和 CI 形态是否适合上 Merge Queue
- [ ] 避开 batch 过大、分组误配、auto-merge 互斥这三个最常见的坑

## 目录

1. [先看全景：Merge Queue 里到底发生了什么](#一先看全景merge-queue-里到底发生了什么)
2. [核心机制：Batch、Merge Group 与合并策略](#二核心机制batchmerge-group-与合并策略)
3. [一次完整流转：从 PR 入队到合入](#三一次完整流转从-pr-入队到合入)
4. [GitHub 原生配置](#四github-原生配置)
5. [GitHub Actions 集成](#五github-actions-集成)
6. [Group Merging：不同 PR 走不同通道](#六group-merging不同-pr-走不同通道)
7. [Stack PR 与 Drop 行为](#七stack-pr-与-drop-行为)
8. [附：github-merge-queue App 增强功能](#八附github-merge-queue-app-增强功能)
9. [最佳实践](#九最佳实践)
10. [故障排查](#十故障排查)
11. [常见问题 (FAQ)](#十一常见问题-faq)
12. [该不该上 Merge Queue：一份决策指南](#十二该不该上-merge-queue一份决策指南)

---

## 一、先看全景：Merge Queue 里到底发生了什么

先看一张系统地图，再看怎么配。Merge Queue 的核心机制可以拆成三条线：

```mermaid
flowchart TB
    subgraph IN["入队"]
        A["PR 入队<br/>标签 / API / 手动"]
    end

    subgraph QUEUE["Merge Queue"]
        B["Batch 编组"]
        C["CI 验证<br/>(merge_group 事件)"]
        D["合入 / 丢弃"]
    end

    subgraph PARA["并行机制"]
        E["Group Merging<br/>不同标签走不同验证通道"]
        F["Stack PR<br/>有依赖关系的 PR 按序合入"]
        G["Drop<br/>CI 失败时跳过，不阻塞队列"]
    end

    IN --> B --> C --> D
    B -.-> E
    B -.-> F
    B -.-> G
```

三条线各自独立，但共享同一个队列。理解它们的边界比记住所有配置参数更重要：

| 机制 | 解决的问题 | 不负责的事 |
|------|-----------|-----------|
| **Batch（批次）** | 把多个 PR 合并成一个临时 commit 一起跑 CI，减少重复验证 | 不管 PR 之间有没有代码冲突 |
| **Group Merging（分组）** | 不同类型 PR 走不同验证通道（文档改动不跑 e2e） | 不管分组间的优先级排序 |
| **Stack（栈式 PR）** | 按依赖顺序逐个合入，不会把依赖链打乱 | 不检测循环依赖，也不自动 rebase 栈中 PR |

---

## 二、核心机制：Batch、Merge Group 与合并策略

### 2.1 队列如何工作

PR 入队后的完整路径：

1. **入队（Enqueue）**：PR 通过 label、`/merge` 命令或 API 加入队列
2. **编组（Batch）**：队列按配置将连续的 PR 编为一组。默认最少 2 个 PR 才触发批次
3. **合并验证（Mergeability Check）**：GitHub 创建一个临时合并提交，把 batch 内所有 PR 按队列顺序合并到目标分支，在这个临时 commit 上跑 CI
4. **合入（Merge）**：CI 通过 → 批量合入；CI 失败 → 整个 batch 标记失败，不会部分合入

### 2.2 Merge Group：临时验证提交

Merge Group 是 GitHub 在验证阶段动态创建的一个临时 commit：

```
base: main
  └─ commit: merge #101 + #102 + #103 → merge_group_sha
```

CI 跑在这个临时 commit 上，而不是跑在任何一个单独的 PR 上。这一点直接决定了 Actions workflow 的写法——你需要 checkout `merge_group.head_sha`，而不是 `pull_request.head.sha`。

### 2.3 合并策略

在仓库 Settings → Pull Requests 中配置，三种策略：

- **Squash and merge**：推荐。每个 PR 的全部 commit 压成一个，合入后 main 分支历史干净
- **Merge commit**：保留 PR 的完整 commit 历史，创建合并提交
- **Rebase and merge**：将 PR 的 commit 逐个变基到目标分支顶端

> ⚠️ Rebase and merge 在 Merge Queue 场景下行为复杂。每个 PR 的 commit 历史会被重新构建，如果 batch 内有多个 PR，rebase 顺序可能产生非预期的冲突。除非团队有明确的线性历史要求，否则优先选 **Squash and merge**。

### 2.4 批次大小：不是越大越好

队列需要达到 `min_group_size` 个 PR 后才触发批量合入。默认 2，小仓库可设 1，大仓库设 5-10。

但 `max_group_size` 设太大反而有害：batch 越大，其中任意一个 PR 的 CI 失败都会把整个 batch 打回，吞吐量反而下降。经验值是 `max_group_size ≤ 10`。

---

## 三、一次完整流转：从 PR 入队到合入

假设你维护一个中型前端仓库，现在有 3 个 PR 同时通过 review：

- PR #201：修复登录页按钮样式（`fast-track` 标签）
- PR #202：重构认证中间件
- PR #203：新增支付模块集成测试

**第 1 步：路由到分组**

```
PR #201 (fast-track) → fast-track 组 → 只跑 lint + typecheck
PR #202 (无标签)     → standard 组  → 跑完整 CI
PR #203 (无标签)     → standard 组  → 跑完整 CI
```

**第 2 步：编组与验证**

- `fast-track` 组当前只有 #201 一个 PR，`min_group_size=1`，直接触发合并验证。GitHub 创建 `merge_group_sha`，跑 lint 和 typecheck，10 秒通过 → #201 合入 main。
- `standard` 组有 #202 和 #203，`min_group_size=2`，编为一个 batch。GitHub 创建包含两个 PR 的临时 commit，跑完整 CI（lint + typecheck + unit + integration + e2e）。

**第 3 步：一个失败，全 batch 回退**

#203 的集成测试因为数据库迁移脚本冲突而失败。整个 batch 标记失败。#202 和 #203 都**不会**合入。

**第 4 步：修复与重试**

#203 的作者修了迁移脚本，推了新 commit。#203 重新入队，#202 仍在队列中等待。下一轮 batch 重新编组验证，这次两个都通过 → 批量合入。

这事说明两点：batch 共享 CI 结果能省时间，但一个 PR 失败会拖累同 batch 的其他 PR。也是为什么 `max_group_size` 不宜太大。

---

## 四、GitHub 原生配置

### 4.1 仓库级别开启

GitHub 仓库 Settings → Pull requests → **Merge queue**：

```yaml
PUT /repos/{owner}/{repo}
{
  "merge_queue": {
    "minimize_dialog": true,
    "method": "squash",
    "min_group_size": 2,
    "max_group_size": 8
  }
}
```

### 4.2 分支保护规则

在 Branch Protection Rules 中启用 merge queue 要求：

```yaml
PUT /repos/{owner}/{repo}/branches/{branch}/protection
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["ci/build", "ci/test"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "require_approving_reviewers": 1
  },
  "restrictions": null,
  "flags": ["MERGE_QUEUE_OWNER"]
}
```

### 4.3 通过标签自动入队

```yaml
# .github/mergeable.yml
name: Add to merge queue

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  add-to-queue:
    runs-on: ubuntu-latest
    steps:
      - name: Add merge label
        run: |
          gh pr edit ${{ github.event.pull_request.number }} --add-label "merge"
```

或者在 PR 描述或评论中直接写 `/merge`。

---

## 五、GitHub Actions 集成

### 5.1 `merge_group` 触发器

PR 入队后，GitHub 触发 `merge_group` 事件，而不是 `pull_request` 事件：

```yaml
name: Merge Queue CI

on:
  merge_group:
    types: [checks_requested]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.merge_group.sha }}
          fetch-depth: 0

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build

      - name: Run tests
        run: npm test
```

要点：`ref` 必须指向 `merge_group.sha`，这是包含整个 batch 的临时合并 commit，不是任何一个单独 PR 的 head。

### 5.2 同一 workflow 同时处理 PR 和 merge group

```yaml
jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.merge_group.head_sha || github.event.pull_request.head.sha }}
          fetch-depth: 0

      - name: Build and test
        run: |
          npm ci
          npm run build
          npm test
```

### 5.3 完整多阶段 Pipeline

```yaml
name: CI Pipeline

on:
  push:
    branches: [main]
  pull_request:
    types: [opened, synchronize, reopened]
  merge_group:
    types: [checks_requested]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  quality-checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.merge_group.head_sha || github.sha }}
          fetch-depth: 0

      - name: Lint
        run: npm run lint

      - name: Type check
        run: npm run typecheck

  unit-tests:
    needs: quality-checks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.merge_group.head_sha || github.sha }}

      - name: Run unit tests
        run: npm test -- --coverage

  integration-tests:
    needs: unit-tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.merge_group.head_sha || github.sha }}

      - name: Run integration tests
        env:
          DATABASE_URL: postgres://test_user:test_pass@localhost:5432/test_db
        run: npm run test:integration

  e2e-tests:
    needs: unit-tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.merge_group.head_sha || github.sha }}

      - name: Playwright E2E tests
        uses: microsoft/playwright@v1.42.0
        with:
          install-browser: true
          script: npm run test:e2e

  build:
    needs: [unit-tests, integration-tests]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.merge_group.head_sha || github.sha }}

      - name: Build Docker image
        run: |
          docker build -t myapp:${{ github.sha }} .
          docker tag myapp:${{ github.sha }} myapp:latest

      - name: Push to registry
        if: github.ref == 'refs/heads/main'
        run: |
          echo ${{ secrets.GITHUB_TOKEN }} | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker push myapp:latest
```

### 5.4 CI 成本：artifact 缓存

Batch 内共享 artifact 是 Merge Queue 的天然优势：

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.merge_group.head_sha || github.sha }}

      - name: Cache node_modules
        uses: actions/cache@v4
        with:
          path: ~/.npm
          key: npm-deps-${{ runner.os }}-${{ hashFiles('package-lock.json') }}

      - name: Build
        run: npm run build

      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: build-artifact
          path: dist/
          retention-days: 1

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Download build artifact
        uses: actions/download-artifact@v4
        with:
          name: build-artifact
```

---

## 六、Group Merging：不同 PR 走不同通道

大型仓库里，文档改动和核心逻辑变更不应该跑同一套 CI。Group Merging 按标签把 PR 路由到不同的验证通道：

```yaml
# .github/merge_group_rules.yml
merge_rules:
  - name: fast-track
    merging_mode: squash
    min_group_size: 1
    max_group_size: 3
    required_check_runs:
      - lint
      - typecheck

  - name: standard
    merging_mode: squash
    min_group_size: 2
    max_group_size: 5
    required_check_runs:
      - lint
      - typecheck
      - unit-tests
      - integration-tests

  - name: security
    merging_mode: squash
    min_group_size: 1
    max_group_size: 2
    required_check_runs:
      - lint
      - typecheck
      - unit-tests
      - security-scan
      - penetration-tests
```

标签路由：

```yaml
name: Route to merge group

on:
  pull_request:
    types: [labeled]

jobs:
  route:
    runs-on: ubuntu-latest
    steps:
      - name: Route based on label
        run: |
          LABELS="${{ github.event.pull_request.labels.*.name }}"
          if echo "$LABELS" | grep -q "fast-track"; then
            echo "group=fast-track" >> $GITHUB_OUTPUT
          elif echo "$LABELS" | grep -q "security"; then
            echo "group=security" >> $GITHUB_OUTPUT
          else
            echo "group=standard" >> $GITHUB_OUTPUT
          fi
```

分组按定义顺序处理：`security` → `standard` → `fast-track`。安全相关 PR 优先合入。

---

## 七、Stack PR 与 Drop 行为

### 7.1 Stack PR 场景

Stack 是一组有依赖关系的 PR：

```
PR #101: Add feature A  (base: main)
PR #102: Use feature A in module X  (base: PR #101)
PR #103: Add tests for module X  (base: PR #102)
```

### 7.2 队列中的 Stack 处理

Merge Queue 按依赖顺序逐个合入，不把依赖链打乱：

```
Queue: [#101, #102, #103]
Batch 1: [#101] → merge to main
Batch 2: [#102] → now mergeable since #101 is in main
Batch 3: [#103] → now mergeable since #102 is in main
```

每个 batch 只合入当前可合并的 PR。

### 7.3 Drop 行为

CI 失败时：

| 场景 | 行为 |
|------|------|
| PR #102 在队列中 CI 失败 | #102 被丢弃，跳到下一个 |
| 依赖 #102 的 PR #103 | 不会被自动丢弃，但合入时会遇到冲突 |
| 需要手动干预 | 维护者需要取消/关闭失败的 PR |

### 7.4 auto-merge 与 Merge Queue 互斥

⚠️ `auto-merge` 和 `merge queue` 不要同时开启。同时启用时，GitHub 优先走 auto-merge 路径，可能绕过队列机制。

```yaml
name: Enable merge queue

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  enable-merge-queue:
    runs-on: ubuntu-latest
    steps:
      - name: Disable auto-merge
        run: |
          gh pr edit ${{ github.event.pull_request.number }} --disable-auto-merge
```

---

## 八、附：github-merge-queue App 增强功能

[github-merge-queue](https://github.com/apps/github-merge-queue) 是 GitHub Marketplace 上的一个 App，在原生 Merge Queue 之上提供了三个额外能力：

- **可视化仪表板**：队列深度、各 batch 状态、平均等待时间、CI 成功率趋势
- **精细化优先级**：通过 `urgent` / `wip` 等标签控制 PR 在队列中的位置
- **失败通知 Webhook**：支持 Slack、邮件等渠道，batch 失败时自动通知

```yaml
priorities:
  - name: urgent
    label: "urgent"
    position: 1

  - name: normal
    label: ""
    position: 2

  - name: low-priority
    label: "wip"
    position: 99
```

```yaml
webhooks:
  on_failure:
    - type: slack
      url: ${{ secrets.SLACK_WEBHOOK_URL }}
      message: "Merge queue batch failed: {{ batch_id }}"
    - type: email
      recipients: ${{ vars.DEVOPS_TEAM_EMAIL }}
```

> **注意：** GitHub 从 2023 年开始在 `pull_request` 和 `merge_group` 事件中提供原生 merge queue 支持。如果你使用的是 GitHub Enterprise Cloud，原生功能可能已经覆盖了你大部分需求。App 的价值主要在仪表板和通知——如果团队已经有 Grafana / Datadog 等监控栈，App 不一定必要。

---

## 九、实践建议

### 9.1 CI 配置

1. 用 `merge_group` 触发器单独处理批次验证，不要和普通 PR CI 共用同一个 workflow 的所有 job
2. merge group 的 CI 只放必要检查——它的延迟直接影响队列吞吐
3. 利用 artifact 在 batch 内共享构建结果

### 9.2 队列规模

| 仓库规模 | min_group_size | max_group_size |
|----------|---------------|---------------|
| 小型（<10 PR/天）| 1 | 3 |
| 中型（10-50 PR/天）| 2 | 5 |
| 大型（>50 PR/天）| 5 | 10 |

### 9.3 常见陷阱

1. **同一仓库混用不同合并策略**：merge queue 应统一使用一种合并策略
2. **batch 过大**：`max_group_size > 10` 时，单个 PR 失败的回滚成本太高
3. **队列堵塞不监控**：等待时间超过 30 分钟说明 CI 存在瓶颈
4. **WIP PR 进入队列**：用标签过滤掉未完成的 PR

```yaml
name: Block WIP PRs from merge queue

on:
  pull_request:
    types: [labeled]

jobs:
  block-wip:
    if: contains(github.event.pull_request.labels.*.name, 'wip')
    runs-on: ubuntu-latest
    steps:
      - name: Comment and set status
        run: |
          gh pr comment ${{ github.event.pull_request.number }} \
            --body "⛔ PR marked as WIP. Please remove WIP label when ready for merge queue."
          exit 1
```

### 9.4 队列健康监控

```yaml
name: Merge Queue Monitor

on:
  schedule:
    - cron: '*/15 * * * *'

jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - name: Check queue health
        run: |
          QUEUE_COUNT=$(gh api repos/${{ github.repository }}/merge_queue --jq '.length' 2>/dev/null || echo "0")
          echo "Current queue depth: $QUEUE_COUNT"

          if [ "$QUEUE_COUNT" -gt 20 ]; then
            echo "::warning::Queue depth exceeds 20, please investigate"
          fi
```

---

## 十、故障排查

### 10.1 PR 卡在队列中不动

**可能原因：**
- CI 仍在运行（checks_pending）
- 分支保护规则要求额外审查
- 有冲突（merge_conflict）

**排查命令：**
```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/merge_queue
```

### 10.2 Batch 持续失败

**可能原因：**
- Batch 中存在冲突的代码变更
- CI 配置在 `merge_group` 触发器下行为不同
- 共享依赖在批次间不兼容

**排查步骤：**
1. 查看失败 batch 的详细 CI 日志
2. 确认 `merge_group` 触发器的 CI 和普通 PR CI 行为一致
3. 手动触发合并以复现问题

### 10.3 "Missing MERGE_QUEUE_OWNER permission"

GitHub App 权限不足。在 App 权限设置中启用：
- Repository permissions → Merge approvals: Read & Write
- Repository permissions → Pull requests: Read & Write

---

## 十一、常见问题 (FAQ)

### Q1：我把一个新 commit 推到了已入队的 PR 上，队列会怎么处理？

假设你的 PR #42 已经进了 merge queue 正在排队，这时你发现一个 typo，`git push` 了一个修正 commit。GitHub 会自动把 #42 从队列中移除，用最新 commit 重新入队——相当于从头排队。这是为了保证 CI 跑的是 PR 最新状态。

如果你用的是 [github-merge-queue](https://github.com/apps/github-merge-queue) App，可以开启 `re-enqueue on push`，让它自动帮你重新加入而不需要手动操作。

### Q2：Merge Queue 的 CI 红了，但我本地跑同样的测试全绿，怎么回事？

CI 跑在 `merge_group_sha` 上——这是一个把 batch 内所有 PR 合并在一起的临时 commit。你本地跑的是自己的 PR 分支，没有和其他人的改动合并。最常见的原因：

1. 你的 PR 和同 batch 里的另一个 PR 在合并后产生了集成问题（比如某个 shared util 被改了签名）
2. 你的 workflow 在 `merge_group` 事件下 checkout 了错误的 ref

排查方法：在 CI 日志里找到 `merge_group_sha`，本地 `git checkout` 这个 sha，重跑同样的命令。如果复现了，说明是 batch 合入后的冲突问题，需要和同 batch 的 PR 作者协调。

### Q3：能只对部分 PR 启用 Merge Queue 吗？hotfix 我想绕过队列直接合。

可以。Merge Queue 本身通过 label 触发——不给 hotfix PR 加 merge label，它就走传统合入流程。配合 Branch Protection Rules，你可以在 required status checks 里把 merge queue 设为"非强制"，这样不带 label 的 PR 不受队列约束。

但注意：绕过队列直接 push 到 main 之前，确保你的 CI 也跑了——Branch Protection 的 required checks 仍然生效。

### Q4：Merge Queue 和 Branch Protection 的 required_status_checks 打架了——队列过不了，说缺 check，怎么办？

这是最常见的配置陷阱。Branch Protection 要求 provider 返回的 check 名称必须和 workflow 实际发回的名称精确匹配。当 workflow 同时触发 `pull_request` 和 `merge_group` 事件时，同一个 job 可能以不同 check 名称上报。

解决方法：
```yaml
# Branch Protection 里配这两个：
required_status_checks:
  contexts:
    - "ci/build"          # PR 事件返回的 check 名
    - "ci/build (merge_group)"  # merge_group 事件返回的 check 名
```

或者在 workflow 里显式指定 check 名称：
```yaml
- name: Set merge group check status
  if: github.event_name == 'merge_group'
  uses: actions/github-script@v7
  with:
    script: |
      github.rest.checks.create({
        owner: context.repo.owner,
        repo: context.repo.repo,
        name: 'ci/build',
        head_sha: context.payload.merge_group.head_sha,
        status: 'completed',
        conclusion: 'success'
      });
```

### Q5：Batch 里一个 PR CI 失败，整个 batch 都回退——能不能只踢掉失败的，保留其他的？

原生 Merge Queue 不支持部分合入——这是一个设计选择，不是 bug。因为 batch 内所有 PR 共享同一个 `merge_group_sha`，CI 在这个合并后的代码上验证，无法简单拆分"谁通过谁不通过"。

两种折中：
1. 把 `max_group_size` 设小（比如 3），降低单个失败的波及面
2. 把风险差异大的 PR 分到不同 merge group（比如 security 敏感改动用独立 group，`max_group_size=1`）

---

## 十二、该不该上 Merge Queue：一份决策指南

Merge Queue 不是银弹。它的收益取决于你的团队形态。

**优先上的团队：**

- 每天合入 10 个以上 PR，维护者花大量时间盯 CI 状态
- 多个 PR 经常同时通过 review，但合入时频繁冲突
- CI 耗时较长（>10 分钟），串行合入的等待成本明显
- 已有完善的分支保护规则和 CI pipeline，只是缺一个合入编排层

**可以先等等的团队：**

- PR 量小（每天 <5 个），手动合入没有成为瓶颈
- CI 覆盖率低，merge group 的验证价值有限
- 团队还在磨合分支策略和 code review 流程，先稳定这些再说
- 使用 GitHub Free 计划——Merge Queue 目前主要面向 Enterprise Cloud 和部分 Pro/Team 仓库

**如果决定上，建议的推进顺序：**

1. 先在  PROTECTED_67  的小配置下跑一周，验证 CI 在  PROTECTED_68  事件下行为正常
2. 确认无误后，逐步调大  PROTECTED_69  到 2-5
3. 引入 Group Merging，先把文档类 PR 分到 fast-track 通道
4. 最后接入监控（队列深度告警、CI 失败率趋势）

---

## 自测：你是否理解了 Merge Queue

1. **Merge Group 到底是什么？** CI 跑在哪个 commit 上——是每个 PR 的 head，还是一次性合并了 batch 内所有 PR 的临时 commit？
   <details><summary>点击查看答案</summary>
   Merge Group 是 GitHub 在验证阶段动态创建的临时合并 commit（`merge_group_sha`），把 batch 内所有 PR 合并到目标分支上。CI 跑在这个临时 commit 上，不是任何一个单独 PR 的 head。所以你在 workflow 里要 checkout `merge_group.head_sha` 而不是 `pull_request.head.sha`。
   </details>

2. **一个 batch 有 5 个 PR，其中第 3 个 CI 失败，会怎样？** 前 2 个会合入吗？后 2 个呢？
   <details><summary>点击查看答案</summary>
   整个 batch 标记失败，5 个 PR 都不会合入。这是 Merge Queue 的原子性保证——batch 内所有 PR 共享一次 CI 验证结果。失败后需要修复问题 PR，重新入队、重新编组、重新验证。
   </details>

3. **Stack PR（有依赖链的 PR 组）在 Merge Queue 中如何合入？** 是先合入底层 PR 还是顶层 PR？一次一个 batch 还是整个链一起？
   <details><summary>点击查看答案</summary>
   从底层到顶层，逐个合入。底层 PR（如 `#101: base main`）先单独编为一个 batch 合入 main，然后 `#102: base #101` 的 base 变成 main 后才可以合入，以此类推。一次一个 batch，不会把整个依赖链打乱。
   </details>

4. **什么情况下 Merge Queue 反而降低效率？** 列举至少两个场景。
   <details><summary>点击查看答案</summary>
   （1）团队 PR 量很小（每天 < 5 个），手动合入没有成为瓶颈，引入 Merge Queue 只是多了一套配置要维护。（2）CI 覆盖率低或 CI 不稳定（频繁假阳性），batch 中任意一个 CI 红都会拖累全组，反而比单独合入更慢。（3） PROTECTED_75  设得过大（> 10），一个失败回滚成本太高，队列吞吐下降。
   </details>

---

*本文基于 GitHub Enterprise Cloud 的 Merge Queue 功能编写，部分 API 和配置可能因 GitHub 版本不同而有所差异。实际使用时请查阅 [GitHub Merge Queue 官方文档](https://docs.github.com/en/repositories/configuring-branches-and-numbers-in-your-repository/configuring-pull-request-merges/using-gitops-and-merge-queue)。*