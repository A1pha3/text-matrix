---
title: "Trivy 实战指南：Aqua Security 开源的「全能」安全扫描器"
date: "2026-06-04T15:00:00+08:00"
slug: trivy-aquasecurity-security-scanner-guide
github_repo: "aquasecurity/trivy"
description: "Trivy 是 Aqua Security 维护的 37K+ Stars 综合安全扫描器，覆盖容器镜像、文件系统、Git 仓库、K8s 集群、VM 镜像，集成 CVE 漏洞、SBOM、IaC 错误配置、密钥与 License 扫描。"
categories: ["技术笔记"]
tags: ["DevSecOps", "Kubernetes"]
---

# Trivy 实战指南：Aqua Security 开源的「全能」安全扫描器

## 读完能做什么

学习目标很具体：装好 Trivy，扫第一个容器镜像；按目标选对子命令，文件系统、Git 仓库、Kubernetes 集群各走各的路；导出 CycloneDX 或 SPDX 格式的 SBOM（软件物料清单）；把 Trivy 接进 CI 流水线和 K8s 集群。前置要求是熟悉命令行，了解容器和依赖管理的基本概念。

## 目录

- [核心判断](#核心判断)
- [项目地图](#项目地图)
- [安装与快速上手](#安装与快速上手)
- [核心能力](#核心能力)
- [典型场景](#典型场景)
- [进阶技巧](#进阶技巧)
- [与同类的对比](#与同类的对比)
- [边界与盲点](#边界与盲点)
- [采用建议](#采用建议)
- [动手练习与自测](#动手练习与自测)
- [常见问题 FAQ](#常见问题-faq)
- [参考文献](#参考文献)

## 核心判断

[Trivy](https://github.com/aquasecurity/trivy) 把 **CVE 漏洞、SBOM、IaC（Infrastructure as Code，基础设施即代码）错误配置、敏感密钥、License 风险**五类扫描压进同一个 CLI（命令行工具）二进制。它能在容器镜像、文件系统、Git 远程仓库、虚拟机镜像、Kubernetes 集群（cluster）这 5 种目标上做同一种事——告诉你哪儿不安全、为什么、怎么修。

它拉开差距的地方在三件事：

1. **一个二进制替代一套工具链**：漏洞、配置、密钥、SBOM 共用同一套命令语法，CI 里不用拼装多个工具。
2. **运行时无关**：单个静态二进制，不依赖 Docker daemon（守护进程）、外部数据库或服务发现，容器镜像也是官方分发渠道之一。
3. **生态广度**：GitHub Actions、VS Code 插件、Trivy Operator、Kyverno/Gatekeeper 策略集成都由 Aqua 官方维护。

如果团队正面临 SBOM 合规（美国 EO 14028 行政令、欧盟 CRA 网络弹性法案）、多云镜像治理、K8s 集群扫描这类问题，Trivy 是当下很务实的起点。

## 项目地图

| 维度 | 关键信息 |
|------|----------|
| 仓库 | [aquasecurity/trivy](https://github.com/aquasecurity/trivy) |
| 主页 | [trivy.dev](https://trivy.dev) |
| 文档 | [trivy.dev/docs/latest/](https://trivy.dev/docs/latest/) |
| 许可证 | Apache-2.0 |
| 最新版本 | v0.74.0（2026 年 8 月发布） |
| 社区规模 | 37K+ Stars / 600+ Forks（2026 年 8 月核实） |

### Trivy 能扫什么（Targets × Scanners）

| Target \ Scanner | CVE 漏洞 | SBOM | IaC 错误配置 | 密钥 | License |
|------------------|----------|------|--------------|------|---------|
| 容器镜像 | ✅ | ✅ | ✅¹ | ✅ | ✅² |
| 文件系统 | ✅ | ✅ | ✅ | ✅ | ✅² |
| Git 仓库 | ✅ | ✅ | ✅ | ✅ | ✅² |
| Kubernetes | ✅ | ✅ | ✅ | ✅ | – |
| VM 镜像 | ✅ | ✅ | ✅¹ | ✅ | ✅² |

¹ 扫描目标内嵌的 IaC 文件（如镜像里的 Kubernetes YAML、Terraform 文件），需要显式启用 `--scanners misconfig`；官方文档提示对 VM 镜像这一能力在多数场景用处有限。

² License 扫描默认关闭，需要显式启用 `--scanners license`。镜像、文件系统、VM 三类目标默认只开启漏洞和密钥两种扫描。

SBOM 通过 `--format cyclonedx` 或 `--format spdx-json` 导出，不是独立的 scanner 开关。同一份 CLI 语法既能跑 `trivy image`（镜像扫描），也能跑 `trivy k8s`，心智模型一致，这是 Trivy 区别于其它扫描器的关键。

## 安装与快速上手

官方分发渠道覆盖了主流平台：

```bash
# macOS / Linux Homebrew
brew install trivy

# Docker
docker run aquasec/trivy image python:3.4-alpine

# 直接下载二进制
# https://github.com/aquasecurity/trivy/releases/latest/

# Debian / Ubuntu 的 apt 源、RHEL / CentOS 的 yum 源见官方安装文档
# 其它渠道：官方 Install Script、asdf/mise、Arch pacman、OpenSUSE zypper、
# MacPorts、Nix/NixOS、FreeBSD；Windows 从 Releases 页下载 zip
```

> ⚠️ **Canary build**：main 分支每次 push（推送）都会触发 canary 构建，产物发布在 Docker Hub、GitHub Container Registry、ECR 和 GitHub Actions 工件里。方便提前试用新特性，但官方明确提示 canary 可能带有严重 bug，不要上生产。

### 一行命令的安全体检

```bash
# 扫容器镜像
trivy image python:3.4-alpine

# 扫本地项目（漏洞 + 密钥 + IaC 错误配置）
trivy fs --scanners vuln,secret,misconfig myproject/

# 扫 K8s 集群（需要 kubeconfig）
trivy k8s --report summary cluster
```

漏洞报告默认是表格，列为 **LIBRARY（库名）/ VULNERABILITY ID（漏洞编号）/ SEVERITY（严重度）/ INSTALLED VERSION（已装版本）/ FIXED VERSION（修复版本）/ TITLE（标题）**。默认按严重度排序，重点问题一眼能挑出来。

## 核心能力

### 1. 漏洞扫描（CVE）

Trivy 的漏洞数据不是来自单一来源，而是按目标类型分两条线：

- **OS 包**：只用对应发行版官方安全公告——Alpine secdb、Ubuntu CVE Tracker、Debian Security Bug Tracker / OVAL、RHEL OVAL 与安全数据 API（应用程序接口）、Amazon Linux Security Center、Oracle Linux OVAL、SUSE CVRF 等。
- **语言包**：主要用 GitHub Advisory Database（安全公告数据库，GHSA），覆盖 npm、pip、RubyGems、Composer、Maven、Go 等生态。
- **NVD**（美国国家漏洞库）不作为 advisory 来源，只在数据源没有给出严重度时按 CVSS 分数兜底。

为什么优先用厂商数据？因为 OS 厂商会 backport（回移）上游修复，发行版里的修复版本和上游不同；只有厂商公告能给出该发行版真正可用的 fix version。严重度同理优先取厂商评级，NVD 对同一个 CVE 的评级经常与厂商不一致。

```bash
trivy image --severity HIGH,CRITICAL python:3.4-alpine
```

这条命令只列出 HIGH 和 CRITICAL 级 CVE，每条都带 fix version，便于决定是升级依赖还是弃用镜像。

### 2. SBOM（软件物料清单）

美国 EO 14028 行政令和欧盟 CRA 都把 SBOM 列为软件供应链合规要求。Trivy 原生支持两种标准格式：

```bash
# CycloneDX
trivy image --format cyclonedx --output sbom.cdx.json python:3.12

# SPDX JSON
trivy image --format spdx-json --output sbom.spdx.json python:3.12

# SPDX Tag-Value（适合人类阅读）
trivy image --format spdx --output sbom.spdx python:3.12
```

`image`、`fs`、`vm` 等子命令都支持这些格式。CI 里不再需要额外跑 `syft`，`trivy image` 顺手就出 SBOM。

### 3. IaC 错误配置

Trivy 能读懂 Terraform、CloudFormation、Kubernetes YAML、Helm Chart、Dockerfile、Ansible、Azure ARM 等格式，输出「配置导致的风险」而不是代码级漏洞。所有配置先转换成统一结构再交给 Rego 检查规则求值，这也是它能用 [OPA Rego](https://www.openpolicyagent.org/docs/latest/#rego) 写自定义检查的原因。

```bash
# 扫 Terraform 目录
trivy config terraform/

# 扫 K8s YAML
trivy config k8s/cluster.yaml
```

### 4. 密钥与敏感信息

内置规则覆盖 AWS Access Key、GCP Service Account（服务账号）、GitHub / GitLab Personal Access Token（访问令牌）、Slack Token 等常见类型，还会扫描编译后的 Python `.pyc` 文件：

```bash
trivy fs --scanners secret myproject/
```

命中结果给出文件、行号和匹配摘录，摘录中的敏感内容会打码（显示为 `*****`），避免把真密钥打进 CI 日志。

### 5. License 合规

```bash
trivy fs --scanners license myproject/
```

默认扫描包管理器（apk、apt-get、dnf、npm、pip、gem 等）记录的包级 License，并按 Google License Classification 分级映射严重度：Forbidden 记为 CRITICAL、Restricted 记为 HIGH、Reciprocal 记为 MEDIUM。加 `--license-full` 后还会扫描源码文件、Markdown 和 LICENSE 文档，代价是耗时明显变长。`--ignored-licenses` 可以把白名单内的 License 从结果里剔除。

## 典型场景

### 场景 A：CI 流水线

最常见的姿势是 GitHub Actions：

```yaml
# .github/workflows/trivy.yaml
name: trivy
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: "myapp:${{ github.sha }}"
          format: "table"

          exit-code: "1"
          ignore-unfixed: true
          vuln-type: "os,library"
          severity: "CRITICAL,HIGH"
```

`exit-code: "1"` 配 `severity: "CRITICAL,HIGH"`：扫到 HIGH 以上就让 Action 失败，PR 直接红。这是把 Trivy 装进 PR gate 的标准配方，参数名与 trivy-action 官方 README 一致。

### 场景 B：Kubernetes 集群持续扫描

Trivy Operator 把 Trivy 装进 K8s 集群，持续扫描工作负载镜像并把结果写成 CRD：

```bash
# 安装 Operator
helm repo add aqua https://aquasecurity.github.io/helm-charts
helm repo update
helm install trivy-operator aqua/trivy-operator \
  --namespace trivy-system --create-namespace

# 查看扫描报告
kubectl get vulnerabilityreports -A
```

Operator 会生成 12 类报告 CRD，包括 `VulnerabilityReport`、`ConfigAuditReport`、`ExposedSecretReport`、`SbomReport` 及对应的 Cluster 级变体。配合 Kyverno 或 Gatekeeper 等策略引擎，还能在准入阶段依据扫描结果拦截带高危漏洞的镜像。

### 场景 C：IDE（集成开发环境）里看漏洞

VS Code 装 [Trivy Extension](https://github.com/aquasecurity/trivy-vscode-extension)：

- 打开 Dockerfile 或 K8s manifest 实时高亮问题
- 一键跳转到 CVE 详情
- 不用等到 CI 才发现配置错误

### 场景 D：本地开发

```bash
# 写完 Dockerfile 后，build 之前先扫一遍基础镜像
trivy image --severity HIGH,CRITICAL myimage:dev
```

比 push 完才发现几百个 CVE 省一晚上时间。

## 进阶技巧

### 只关心「能修的」

```bash
trivy image --ignore-unfixed myimage:tag
```

加了 `--ignore-unfixed`，没有 fix version 的漏洞会被忽略——这类 CVE 升级也修不掉，没必要为它 fail CI。

### 用 .trivyignore 豁免已知问题

```text
# 接受风险
CVE-2018-14618

# 豁免到 2026-12-31 为止
CVE-2019-14697 exp:2026-12-31

# 豁免 IaC 错误配置
AVD-DS-0002

# 豁免 License
GPL-3.0
```

`trivy fs` / `trivy image` 默认读取项目根目录的 `.trivyignore`，每行一个 ID 或注释，支持 `exp:` 过期日期，覆盖漏洞、错误配置、密钥、License 四类扫描。结构化需求用 `.trivyignore.yaml`，可以按扫描器分组并写豁免理由。

### 离线与私有网络部署

Trivy 的漏洞库、Java 索引库和检查规则都以 OCI 镜像形式发布（如 `ghcr.io/aquasecurity/trivy-db`），默认按 `mirror.gcr.io` → `ghcr.io` 的顺序拉取。私有化部署的做法：

1. 用 crane、ORAS 等工具把这几个 OCI 数据库同步到内部镜像仓库。
2. 用 `--db-repository` 指向私有源，配合 `--skip-db-update` 跳过自动更新。
3. 需要断开 Maven Central 外联时加 `--offline-scan`。

IaC 检查规则有内置副本随二进制分发，断网时也能用发布时点的规则做错误配置扫描。

### 并发与批量

`--parallel` 控制并行扫描的 goroutine 数，默认 5；设为 1 是串行，设为 0 则自动按 CPU 核数取值。多镜像批量：

```bash
for img in $(cat images.txt); do
  trivy image --severity CRITICAL --quiet "$img"
done
```

`--quiet` 只输出结果不打印进度信息，CI 日志干净。

### 内置合规报告

`--compliance` 把一组检查聚合成行业标准报告，支持 `trivy image` 和 `trivy k8s`：

```bash
trivy k8s cluster --compliance k8s-cis-1.23 --report summary
trivy image --compliance docker-cis-1.6.0 myimage:tag
```

内置报告包括 NSA/CISA Kubernetes Hardening Guidance（`k8s-nsa-1.0`）、CIS Kubernetes Benchmark（`k8s-cis-1.23`）、CIS Docker Benchmark（`docker-cis-1.6.0`）等。官方标注该功能为实验性，接口可能变化。

## 与同类的对比

| 工具 | 漏洞 | SBOM | IaC | 密钥 | 集群扫描 | 集成 |
|------|------|------|-----|------|----------|------|
| **Trivy** | ✅ | ✅ | ✅ | ✅ | ✅ | Operator/Actions/VS Code |
| Snyk | ✅ | ✅ | ✅ | ✅ | ❌ | 商业 |
| Grype | ✅ | ❌ | ❌ | ❌ | ❌ | Anchore 生态 |
| Syft | ❌ | ✅ | ❌ | ❌ | ❌ | Anchore 生态 |
| Kubescape | ❌ | ❌ | ✅ | ❌ | ✅ | ARMO 生态 |
| Checkov | ❌ | ❌ | ✅ | ❌ | ❌ | Bridgecrew 生态 |

Trivy 的优势是一个二进制替代多个工具——CI 不需要拼 Grype + Syft + Checkov + gitleaks。代价是每一项都不一定是最强的那一个。

## 边界与盲点

- **上游延迟会传导**：漏洞库本身持续更新，但全新 CVE 在 NVD 等上游还没有分析结论时，严重度会暂时回退到其它厂商评级或标记为 UNKNOWN，高敏场景需要自己盯上游公告。
- **K8s 集群扫描吃权限**：`trivy k8s` 依赖 kubeconfig 里的身份，需要能读取集群资源的权限，受限的 service account（服务账号）跑不全。
- **密钥扫描没有修复建议**：扫到密钥只告诉你在哪、什么类型，不会建议迁移到 Vault 的哪条路径。
- **License 默认只看包元数据**：源码文件和 LICENSE 文档需要 `--license-full` 才会扫，静态链接进二进制的库依然识别不到。

## 采用建议

### 适合谁

- 想把 DevSecOps 一把梭：漏洞 + SBOM + IaC + 密钥全打
- 多云 / 多 K8s 集群合规汇报，需要统一工具链
- SBOM 是合规刚需（CRA、EO 14028）

### 不适合谁

- 已经在用 Snyk / Prisma Cloud 商业方案，迁移成本不划算
- 只扫依赖漏洞，不需要 IaC 和集群——Grype 够轻
- 主要做 IaC 错误配置，不关心 CVE——Checkov 更专

### 落地顺序

1. **先接 CI**：GitHub Actions + `exit-code 1` 拦 HIGH/CRITICAL，1-2 周覆盖主仓。
2. **再开 SBOM**：每天跑一次 `--format cyclonedx` 归档，对接 Dependency-Track 这类平台。
3. **最后 K8s Operator**：装在长期集群，配合监控看趋势。

## 动手练习与自测

1. 扫一个老镜像并只看高危项：`trivy image --severity HIGH,CRITICAL python:3.4-alpine`，数一数 CRITICAL 有几条，挑一条查它的 fix version。
2. 对同一个镜像分别导出两种 SBOM：`--format cyclonedx` 和 `--format spdx-json`，用 `jq` 对比两个文件里记录的组件数量是否一致。
3. 在任意项目根目录建一个 `.trivyignore`，写入一条刚扫到的 CVE ID，重跑扫描确认它从结果里消失。
4. 断网演练：加 `--offline-scan` 再扫一次，观察哪些扫描器还能出结果、哪些报错，理解各扫描器对外部资源的依赖。

自测标准：做完 1-3 题，说明已经掌握 Trivy 的日常用法；第 4 题能解释清楚报错原因，说明理解了数据库与扫描器的依赖关系。

## 常见问题 FAQ

**Trivy 怎么读？**

官方 FAQ 给的答案：`tri` 读作 trigger 的 tri，`vy` 读作 envy 的 vy。

**为什么新爆发的 CVE 显示 UNKNOWN 严重度？**

严重度优先取数据源评级。上游还没给出评级时，Trivy 先按 CVSS 分数推算，CVSS 也没有就标 UNKNOWN，等上游补齐后随数据库更新刷新。

**`trivy fs` 为什么不扫 JAR 包？**

`trivy fs` / `trivy repo` 面向代码仓库，目标是 lock 文件（如 package-lock.json），不解析 JAR、二进制这类构建产物；要扫 JAR 用 `trivy image` 或 `trivy rootfs` 扫包含它的镜像或文件系统。

**报 "failed to download vulnerability DB" 之类的数据库错误怎么排查？**

先确认机器能访问 `mirror.gcr.io` 和 `ghcr.io`；受限网络按[离线小节](#离线与私有网络部署)把 OCI 数据库同步到内部仓库并配置 `--db-repository`；高负载时段官方公共仓库可能限流，稍后重试或改用镜像源。

## 参考文献

1. Trivy 仓库与 README（Targets/Scanners、Canary build、快速上手示例）：[github.com/aquasecurity/trivy](https://github.com/aquasecurity/trivy)
2. Trivy 官方文档（安装、扫描器、数据库与离线部署）：[trivy.dev/docs/latest/](https://trivy.dev/docs/latest/)
3. trivy-action（GitHub Actions 参数）：[github.com/aquasecurity/trivy-action](https://github.com/aquasecurity/trivy-action)
4. Trivy Operator（Helm 安装与报告 CRD）：[aquasecurity.github.io/trivy-operator](https://aquasecurity.github.io/trivy-operator/latest/)
5. Trivy VS Code 插件：[github.com/aquasecurity/trivy-vscode-extension](https://github.com/aquasecurity/trivy-vscode-extension)
6. OPA Rego 语言（自定义检查规则）：[openpolicyagent.org](https://www.openpolicyagent.org/docs/latest/#rego)

仓库地址：[aquasecurity/trivy](https://github.com/aquasecurity/trivy)，官网：[trivy.dev](https://trivy.dev)，许可证：Apache-2.0。
