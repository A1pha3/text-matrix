---
title: "Trivy 实战指南：Aqua Security 开源的「全能」安全扫描器"
date: "2026-06-04T15:00:00+08:00"
slug: trivy-aquasecurity-security-scanner-guide
description: "Trivy 是 Aqua Security 维护的 35K Stars 综合安全扫描器，覆盖容器镜像、文件系统、Git 仓库、K8s 集群、VM 镜像，集成漏洞 CVE、SBOM、IaC 错误配置与密钥扫描。"
draft: false
categories: ["技术笔记"]
tags: ["安全扫描", "CVE", "容器安全", "DevSecOps", "Kubernetes", "SBOM"]
---

# Trivy 实战指南：Aqua Security 开源的「全能」安全扫描器

## 核心判断

`Trivy`（仓库 [aquasecurity/trivy](https://github.com/aquasecurity/trivy)）不是"又一款"漏洞扫描器，而是把 **CVE 漏洞、SBOM 软件物料清单、IaC 错误配置、敏感密钥、License 风险** 五类扫描压进同一把 CLI 刀的工具。它能在容器镜像、文件系统、Git 远程仓库、虚拟机镜像、Kubernetes 集群这 5 种目标上做同一种事——告诉你哪儿不安全、为什么、怎么修。

它拉开差距的地方在三件别家没拼齐的事：

1. **「All-in-one」产品形态**：漏洞、配置、密钥、SBOM 一个二进制搞定，CI 不需要塞一堆 tool
2. **运行时无关**：静态二进制 + 容器化分发，不依赖 daemon、数据库或服务发现
3. **生态广度**：GitHub Actions、VS Code、Trivy Operator、Kyverno/ArgoCD 集成，Aqua 把社区养成了事实标准

如果团队正面临 SBOM 合规（欧盟 CRA、美国 EO 14028）、多云镜像治理、K8s 集群准入扫描这类问题，Trivy 是当下最务实的起点。

## 项目地图

| 维度 | 关键信息 |
|------|----------|
| 仓库 | [aquasecurity/trivy](https://github.com/aquasecurity/trivy) |
| 主页 | [trivy.dev](https://trivy.dev) |
| 文档 | [trivy.dev/docs/latest/](https://trivy.dev/docs/latest/) |
| 许可证 | Apache-2.0 |
| 今日热度 | trending 榜常客，35,495 Stars / 423 Forks |

### Trivy 能扫什么（Targets × Scanners）

| Target \ Scanner | CVE 漏洞 | SBOM | IaC 错误配置 | 密钥 | License |
|------------------|----------|------|--------------|------|---------|
| 容器镜像 | ✅ | ✅ | – | ✅ | ✅ |
| 文件系统 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Git 仓库 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Kubernetes | ✅ | ✅ | ✅ | ✅ | – |
| VM 镜像 | ✅ | ✅ | – | – | ✅ |

这张表是 Trivy 区别于其它扫描器的关键——同一份 CLI 语法既能跑 `trivy image`，也能跑 `trivy k8s cluster`，心智模型一致。

## 安装与快速上手

Trivy 的分发渠道是「管道工的礼物」：基本上你想得到的姿势都给了。

```bash
# macOS / Linux Homebrew
brew install trivy

# Docker
docker run aquasec/trivy image python:3.4-alpine

# 直接下二进制
# https://github.com/aquasecurity/trivy/releases/latest/

# 还可以通过：apt/yum/dnf/portage/scoop/winget/choco
# 以及 scoop scoop install trivy
# 以及 asdf-vm asdf install trivy latest
```

> ⚠️ **Canary build**：main 分支每次 push 都会触发 canary 构建（Docker Hub / GitHub Container Registry / ECR / 二进制），方便提前试用新特性，但**不要上生产**。

### 一行命令的安全体检

```bash
# 扫容器镜像
trivy image python:3.4-alpine

# 扫本地项目（漏洞 + 密钥 + IaC）
trivy fs --scanners vuln,secret,misconfig myproject/

# 扫 K8s 集群（需要 kubeconfig）
trivy k8s --report summary cluster
```

输出分四列：**Library（库名）/ Vulnerability ID（漏洞 ID）/ Severity（严重度）/ Installed Version（已装版本）/ Fixed Version（修复版本）**。默认按严重度降序，重点问题一眼能挑出来。

## 核心能力

### 1. 漏洞扫描（CVE）

Trivy 的漏洞数据库从多个上游同步：

- **NVD**（美国国家漏洞库）
- **GHSA**（GitHub Security Advisory）
- **Red Hat OVAL**（RHSA、RHBA、RHEL 数据）
- **Ubuntu CVE Tracker**
- **Alpine、Debian、RHEL、Oracle、Amazon、OpenSUSE、SLES** 等发行版的安全公告
- 语言包（Composer/Pip/Gem/npm/Cargo/Go/...）

举例，扫一个老镜像：

```bash
$ trivy image --severity HIGH,CRITICAL python:3.4-alpine
```

会列出**所有 HIGH/CRITICAL 级 CVE**，每条都带 **fix version**，便于决定是升级还是弃用镜像。

### 2. SBOM（软件物料清单）

欧盟 CRA、美国 EO 14028、NIST SP 800-218 都把 SBOM 列为合规基线。Trivy 原生支持导出标准格式：

```bash
# CycloneDX
trivy image --format cyclonedx --output sbom.cdx.json python:3.12

# SPDX
trivy image --format spdx-json --output sbom.spdx.json python:3.12

# SPDX Tag-Value（适合人类阅读）
trivy image --format spdx --output sbom.spdx python:3.12
```

> 这意味着 CI 里不再需要额外跑 `syft`——`trivy image` 顺手就出 SBOM。

### 3. IaC 错误配置

Trivy 集成 [OPA Rego](https://www.openpolicyagent.org/docs/latest/#rego)，能读懂 Terraform、CloudFormation、Kubernetes YAML、Helm Chart、Dockerfile，输出不合规的"配置级"问题（不是代码级漏洞，而是"配置导致的风险"）。

```bash
# 扫 Terraform
trivy config terraform/

# 扫 K8s YAML
trivy config k8s/cluster.yaml
```

### 4. 密钥与敏感信息

扫硬编码的 AWS Access Key、GitHub Token、数据库连接串、Slack Webhook：

```bash
trivy fs --scanners secret myproject/
```

匹配规则来自官方 + 社区贡献，命中后会**返回文件名 + 行号 + 摘录**（默认打码，避免把真密钥打印到日志）。

### 5. License 合规

```bash
trivy fs --scanners license myproject/
```

输出依赖树里每个包的 License（MIT/Apache-2.0/GPL-3.0/...），方便法务做 License 白名单/黑名单审查。

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

> `exit-code: "1"` 配 `severity: "CRITICAL,HIGH"`：扫到 HIGH 以上就 fail，PR 直接红。这是把 Trivy 装进 PR gate 的标准配方。

### 场景 B：Kubernetes 集群准入

Trivy Operator 把 Trivy 装到 K8s 集群里，配合 Gatekeeper/Kyverno 实现"先扫后跑"：

```bash
# 安装 Operator
helm repo add aqua https://aquasecurity.github.io/helm-charts
helm install trivy-operator aqua/trivy-operator --namespace trivy-system --create-namespace

# 定义 VulnerabilityReportsI
kubectl get vulnerabilityreports -A
```

它会**定期扫工作负载镜像**，生成 `VulnerabilityReport`/`ConfigAuditReport`/`SbomReport` 三类 CRD。你可以在 Grafana 里看趋势，也可以在 ArgoCD 同步前用 Kyverno 拦下来。

### 场景 C：IDE 里看漏洞

VS Code 装 [Trivy Extension](https://github.com/aquasecurity/trivy-vscode-extension)：

- 打开 Dockerfile/manifest 实时高亮问题
- 一键跳转到 CVE 详情
- 不用等到 CI 才发现

### 场景 D：本地开发

```bash
# 写完 Dockerfile 后，build 之前先扫一遍
trivy image --severity HIGH,CRITICAL myimage:dev
```

比"push 完才发现 200 个 CVE"省一晚上时间。

## 进阶技巧

### 只关心「能修的」

```bash
trivy image --ignore-unfixed myimage:tag
```

加了 `--ignore-unfixed`，**没有 fix version 的漏洞会被忽略**——这种 CVE 升级也修不掉，没必要为它 fail CI。

### 排除不需要的库

```bash
trivy image --skip-dirs ./node_modules --skip-files ./package-lock.json myimage:tag
```

或者写 `.trivyignore`：

```
# CVE-2023-1234  # dev-only mock
CVE-2024-5678
```

`trivy fs` / `trivy image` 默认会读 `.trivyignore`，每行一个 CVE 编号或注释。

### 离线 / 私有网络

Trivy 默认拉 NVD/GHSA 数据库，没网就报错。私有化部署有两种姿势：

1. **Trivy DB 镜像**：自建镜像仓库做 mirror
2. **离线数据库**：[aquasecurity/trivy-db](https://github.com/aquasecurity/trivy-db) 仓库定期 release 离线 tarball，下载后 `--skip-db-update --db-repository <私有源>` 即可

### 多目标批量扫

`trivy fs` 默认并行；想关并行可以 `--parallel 0`；想多镜像批量：

```bash
for img in $(cat images.txt); do
  trivy image --severity CRITICAL --quiet "$img"
done
```

`--quiet` 只打漏洞不打印进度，CI 日志干净。

## 与同类的对比

| 工具 | 漏洞 | SBOM | IaC | 密钥 | 集群扫描 | 集成 |
|------|------|------|-----|------|----------|------|
| **Trivy** | ✅ | ✅ | ✅ | ✅ | ✅ | Operator/Actions/VSCode |
| Snyk | ✅ | ✅ | ✅ | ✅ | ❌ | 商业 |
| Grype | ✅ | ❌ | ❌ | ❌ | ❌ | Anchore 生态 |
| Syft | ❌ | ✅ | ❌ | ❌ | ❌ | Anchore 生态 |
| Kubescape | ❌ | ❌ | ✅ | ❌ | ✅ | ARMOscaler 生态 |
| Checkov | ❌ | ❌ | ✅ | ✅ | ❌ | Bridgecrew 生态 |

> Trivy 的优势是**一个二进制替代多个工具**——CI 不需要拼 Grype + Syft + Checkov + gitleaks。代价是「每一项都不一定是最强」。

## 边界与盲点

- **0-day 滞后**：NVD/GHSA 上游更新到 Trivy release 通常有 1-3 天延迟，高敏场景需要 canary 或私有 db
- **License 扫描依赖元数据**：不读源码、不解析 header，只看 package manifest，所以某些 packed binary 里的 static link 库识别不到
- **K8s 集群扫描需要集群读权限**：默认 service account 权限不够，需要 ClusterRole
- **没有 secret 修复建议**：扫到密钥只告诉你在哪、什么类型，不会建议换成 Vault 哪条路径

## 采用建议

### 适合谁

- 想把 DevSecOps 一把梭：漏洞 + SBOM + IaC + 密钥全打
- 多云 / 多 K8s 集群合规汇报，需要统一工具链
- SBOM 是合规刚需（CRA、EO 14028、FedRAMP）

### 不适合谁

- 已经在用 Snyk/PrismaCloud 商业方案，迁移成本不划算
- 只扫代码漏洞，不需要 IaC/集群——Grype 够轻
- 主要做 IaC 错误配置，不关心 CVE——Checkov 入门更陡但更专

### 落地顺序

1. **先接 CI**：GitHub Actions + `--exit-code 1` 拦 HIGH/CRITICAL，1-2 周覆盖完主仓
2. **再开 SBOM**：每天跑一次 `--format cyclonedx` 归档，对接 Dependency-Track
3. **最后 K8s Operator**：装在长期集群，配 Grafana 看趋势

## 一句话总结

> Trivy 是当下「**漏洞 + SBOM + IaC + 密钥 + License**」五合一做得最均衡的开源扫描器；它的"全能"既是优势（少装 tool），也是局限（每一项都不一定最强）。CI 接入成本低、Operator/Kyverno 集成成熟，是合规驱动型团队的务实选择。

---

*📚 仓库地址：[aquasecurity/trivy](https://github.com/aquasecurity/trivy) · 官网：[trivy.dev](https://trivy.dev) · 文档：[trivy.dev/docs/latest/](https://trivy.dev/docs/latest/) · License：Apache-2.0*
