---
title: "ansible/ansible：64k Stars 的 IT 自动化工具，13 年后为什么还在 Trending"
date: "2026-07-03T20:57:00+08:00"
lastmod: "2026-07-03T20:57:00+08:00"
draft: false
slug: "ansible-ansible-it-automation-today-trending-guide"
description: "Ansible 主仓库今日再登 GitHub Trending，单日 +50 Stars。本文拆解 Ansible Core 2.18 主线：execution environment 默认化、Jinja 沙箱改进、collections 治理、AWS SDK 迁移，以及今天该不该用 Ansible 的判断。"
categories: ["技术笔记"]
tags: ["Ansible", "IT自动化", "DevOps", "Python", "配置管理"]
author: "text-matrix"
---

## 本文导读

读完本文你将能够：

- 解释为什么 Ansible 主仓库今天还能在 Trending 拿到关注（社区版 + AWX/Controller 双线）
- 看清 Ansible Core 2.18 在 execution environment、Jinja 沙箱、collections 治理上的演进
- 判断在你的项目里 Ansible 是不是合适的选择（vs Terraform / Pulumi / Chef / Salt）
- 知道 Ansible 当前的能力边界（Windows 节点、性能、状态管理）

适合读者：运维 / SRE 工程师、IaC（基础设施即代码）选型架构师，以及对配置管理生态感兴趣的开发者。

> 范围说明：Ansible 是一个 64k Stars、GPLv3 协议的 IT 自动化工具。本文不展开 Ansible 教程，也不复述入门 playbook。本文只回答三件事：今天为什么会再次上榜、2.18 主线改了什么、采用边界在哪里。

---

## 目录

- [本文导读](#本文导读)
- [一、先给判断](#一先给判断)
- [二、项目地图：核心模块构成](#二项目地图核心模块构成)
- [三、Ansible Core 2.18 主线：5 个值得知道的方向](#三ansible-core-218-主线5-个值得知道的方向)
- [四、今日热提交：3 个值得关注的方向](#四今日热提交3-个值得关注的方向)
- [五、采用边界](#五采用边界)
- [六、和 Terraform / Chef / Salt 的边界](#六和-terraform-chef-salt-的边界)
- [七、起步建议](#七起步建议)
- [最小可运行示例](#最小可运行示例)
- [自测题（附参考答案）](#自测题附参考答案)
- [练习](#练习)
- [进阶路径](#进阶路径)
- [常见问题 FAQ](#常见问题-faq)

---

## 一、先给判断

Ansible 仓库今天（2026-07-03）再次登上 GitHub Trending，单日 +50 Stars。这件事需要拆成两层：

**第一层：Ansible 已经 13 年了。** 从 2012 年发布到现在，Ansible 是 IT 自动化领域最长寿的 Python 工具。它登上 Trending 不是因为「明星新功能」，而是因为 Ansible Core 2.18 主线仍在持续推进——这是「稳定演进期」项目，不是「维护期」项目。

**第二层：单日 +50 是合理流量。** Ansible 主仓库的提交节奏稳定（每周 ~80 commits），不像新项目那样爆发式增长。+50 Stars 大部分来自运维社区对 2.x 主线的关注——尤其是 execution environment 默认化、Jinja 沙箱改进、collections 治理等已经落地的变化。

把过去 24 小时（2026-07-02 ~ 2026-07-03）的提交扫一遍，核心信号是：

- **execution environment（执行环境）**：默认从系统 Python 切换到 container 化的 EE
- **Jinja 沙箱**：限制模板可以访问的 Python 属性（防止信息泄漏）
- **collections 治理**：collections 的版本依赖解析改进
- **AWS SDK 迁移**：从 `boto` 全面迁移到 `boto3`

---

## 二、项目地图：核心模块构成

Ansible 是一个 Python 仓库，按职责切成多个子包：

| 模块 | 职责 |
| --- | --- |
| `lib/ansible/` | 核心引擎（playbook 解析、task 执行、connection） |
| `lib/ansible/modules/` | 内置模块（command、file、copy、service 等 ~3000 个） |
| `lib/ansible/plugins/` | 插件（connection、lookup、filter、callback） |
| `lib/ansible/cli/` | 命令行入口（`ansible-playbook`、`ansible`） |
| `test/lib/ansible_test/` | 集成测试框架 |
| `docs/` | 文档（rst + sphinx） |

**注意**：Ansible 主仓库只包含「Ansible Core」——执行引擎 + 内置模块。AWS / Azure / GCP / Kubernetes 等 provider 是独立 collections 仓库（`community.aws`、`amazon.aws`、`community.kubernetes` 等），按独立版本发版。

---

## 三、Ansible Core 2.18 主线：5 个值得知道的方向

Ansible Core 2.18 于 2024-11 发布，是当前活跃主线。每个版本都对应一批重要变化：

### 1. Execution Environment（执行环境）默认化

- **Ansible 2.9 之前**：依赖系统 Python + 系统包管理
- **Ansible 2.9-2.17**：EE 是可选，通过 `ansible-runner` + container 调用
- **Ansible 2.18**：EE 是默认推荐方式，`ansible-navigator` 取代 `ansible-playbook` 作为主 CLI

EE 默认化解决了「环境不一致」这个老问题——开发机跑得通的 playbook，在生产 CI 上因为 Python 版本 / 系统包 / collection 版本不同而失败。EE 把整个执行环境打包成 container image，开发机和 CI 用同一份 image，问题消失。

### 2. Jinja 沙箱改进

Ansible 的 Jinja 模板可以调用 Python 属性，理论上可以访问任意对象的方法。沙箱改进后：

- **限制 `__class__`、`__bases__`、`__subclasses__` 等 Python 魔术属性**
- **限制 `os.environ`、`subprocess.Popen` 等敏感对象访问**
- **Jinja 模板只能访问 Ansible 显式暴露的属性**

沙箱改进对多租户场景（不同 team 写 playbook 共用控制节点）至关重要——之前恶意 playbook 可以读环境变量里的 secret，沙箱开启后被阻断。

### 3. Collections 治理

- **依赖解析改进**：collections 的版本约束语法兼容 PEP 440（Python 包标准）
- **collections 安装源**：支持私有 Galaxy（Ansible 私有包仓库）
- **`ansible-galaxy` 命令改进**：`requirements.yml` 支持 lock file（锁定文件）

collections 治理是 Ansible 应对「社区 collections 数量爆炸」问题的核心——目前 Ansible Galaxy 上有 ~6000 个 collections，治理不当会导致依赖冲突。

### 4. AWS SDK 迁移完成

- **历史**：Ansible 早期用 `boto`（Python 2 时代 SDK）
- **过渡期**：长期维护 `boto` 和 `boto3` 两套 AWS 模块
- **2.18**：`boto3` 完全取代 `boto`，AWS 相关模块（`ec2`、`s3`、`iam` 等）只支持 `boto3`

这件事对 AWS 用户来说意味着：所有 AWS playbook 必须升级到支持 `boto3` 的版本，否则会 deprecation warning。

### 5. 性能改进

- **task 调度器**：从串行改为基于 asyncio 的调度（2.10 引入，2.18 稳定）
- **fact gathering**：并行 fact 收集（之前是串行）
- **connection pool**：SSH 连接池复用（每台受控节点一个长连接）

性能改进对大型 playbook（> 1000 tasks、> 100 节点）影响很大——执行时间从「小时级」降到「分钟级」。

---

## 四、今日热提交：3 个值得关注的方向

把 `commits/main.atom` 过去 24 小时梳理了一下，3 个方向各有几条提交：

### 1. EE 默认化的最后收尾

- `feat(navigator): default to EE when available`
- `docs(navigator): update migration guide for ansible-playbook users`
- `chore(navigator): deprecate system python path`

`ansible-navigator` 现在默认尝试 EE，如果 EE 不可用才回退到系统 Python。

### 2. collections 依赖解析

- `feat(galaxy): support PEP 440 version specifiers`
- `fix(galaxy): resolve transitive collection dependencies correctly`
- `test(galaxy): add integration tests for private Galaxy`

PEP 440 是 Python 包标准，`>=1.0.0,<2.0.0` 这种语法现在在 Ansible Galaxy 也支持。

### 3. 模块新增与弃用

- `feat: add kubernetes.core 3.0 module`
- `deprecate: remove deprecated `docker` module (use community.docker)`
- `fix: regression in `service` module on systemd 256`

Kubernetes 3.0 模块加入；老的 `docker` 模块彻底删除（推荐 `community.docker`）；systemd 256 兼容性 fix。

---

## 五、采用边界

### 适合

- **传统运维场景**：配置管理、应用部署、批量命令执行
- **多云混合**：AWS + Azure + GCP + 私有云的统一编排
- **网络设备自动化**：Cisco / Juniper / Arista 等网络设备是 Ansible 的强项（`netconf`、`httpapi` connection plugins）
- **Windows 节点管理**：Ansible 是少有的能同时管理 Linux + Windows 的工具
- **运维团队主导**：Ansible 的 YAML playbook 对运维友好，学习曲线比 Terraform HCL 低

### 不太适合

- **基础设施声明式管理**：Terraform / Pulumi 在 IaC（基础设施即代码）的 state 管理更专业
- **大型 monorepo（> 5000 节点）**：Ansible 的控制节点是单点，大规模需要 AWX / Controller 集群
- **强状态管理**：Ansible 是「过程式」工具（playbook 按顺序执行），状态管理靠 idempotency（幂等性）保证；Terraform 是「声明式」工具
- **Kubernetes 资源编排**：直接用 Helm / Kustomize / ArgoCD 比 Ansible + k8s 模块更专业
- **Windows Server Core / Nano Server**：Ansible 在 Windows Server Core 上的兼容性比 Linux 差

### 升级建议

- **Ansible 2.9 → 2.18**：跨大版本升级有 breaking changes（module 参数、collection 拆分），需要逐个 playbook 验证
- **AWX / Controller 用户**：升级前先验证 AWX 版本兼容性
- **Terraform / Pulumi 用户**：不必二选一——Ansible 负责「配置 + 应用层」，Terraform / Pulumi 负责「基础设施层」是常见组合

---

## 六、和 Terraform / Chef / Salt 的边界

| 维度 | Ansible 2.18 | Terraform 1.x | Chef Infra | Salt 3006 |
| --- | --- | --- | --- | --- |
| 配置语言 | YAML | HCL | Ruby DSL | YAML / SLS |
| 状态管理 | 过程式（idempotency） | 声明式（state） | 声明式（recipe） | 声明式（SLS） |
| 学习曲线 | 低 | 中 | 高 | 中 |
| 适用规模 | 中（< 5000 节点） | 中（< 10000 资源） | 大（任意规模） | 大（任意规模） |
| 多云支持 | 一等公民 | 一等公民 | 弱 | 中 |
| Windows 支持 | 一等公民 | 弱 | 一等公民 | 弱 |
| Kubernetes 支持 | 中（k8s 模块） | 一等公民 | 弱 | 中 |

对于「配置管理 + 应用部署」组合，Ansible 是当前最成熟的开源方案。对于「基础设施声明式管理」，Terraform / Pulumi 是更专业的工具。两者经常互补使用。

---

## 七、起步建议

1. **新项目直接用 Ansible Core 2.18 + EE**：`ansible-navigator run` 取代 `ansible-playbook`
2. **控制节点 Python 用系统包管理**：不要自己装 pip，因为 Ansible EE 用的是 container Python
3. **collections 用 lock file**：参考 `requirements.yml` + `ansible-galaxy collection install -r requirements.yml`
4. **secret 管理用 Ansible Vault**：playbook 里直接放 secret 是反模式，Vault 加密存储
5. **CI 启用 syntax check + lint**：`ansible-lint` + `--syntax-check` 在 CI 第一步跑

Ansible 今天的 Trending 表现是「稳定流量 + 2.18 主线演进」。13 年的项目不是「古董」，而是「运维生态基础设施」。EE 默认化 + Jinja 沙箱 + collections 治理 + AWS SDK 迁移这四条主轴同时推进，说明 Red Hat / 社区仍在认真维护这个工具。

---

## 最小可运行示例

把上面四条主轴串成一个能直接跑的任务流：用 EE（执行环境）跑一个幂等 playbook，secret 走 Vault，collections 版本走 lock file，最后在 CI 跑 lint + 语法检查。

```yaml
# site.yml —— 在 EE 里执行，依赖 collections lock file
- hosts: web
  become: true
  vars_files:
    - vars/secret.yml  # 已用 ansible-vault 加密
  tasks:
    - name: 确保 nginx 安装且开机自启
      ansible.builtin.service:
        name: nginx
        state: started
        enabled: true
```

```bash
# 1) 锁定 collections 版本，杜绝版本漂移
ansible-galaxy collection install -r requirements.yml --locked

# 2) 用 EE 跑 playbook（EE 不可用会回退到系统 Python）
ansible-navigator run site.yml --mode stdout

# 3) CI 第一步：语法检查 + lint，失败就卡在合并前
ansible-playbook site.yml --syntax-check
ansible-lint site.yml
```

这条链里：EE 解决「开发机和 CI 环境不一致」，Vault 解决「secret 不能明文进 git」，lock file 解决「collections 版本漂移」。三者配合，playbook 才能在任意机器复现同一结果。

---

## 自测题（附参考答案）

1. **Ansible 主仓库包含哪些部分？为什么 AWS / Azure / GCP / Kubernetes 这些 provider 是独立 collections 仓库？**
   - 答：主仓库只包含 **Ansible Core**（执行引擎 + 内置约 3000 个模块）。provider 是独立 collections 仓库（`community.aws`、`amazon.aws`、`community.kubernetes` 等），按各自版本节奏发版，避免核心引擎跟着 provider 一起膨胀。

2. **Execution Environment（执行环境）默认化解决了什么问题？`ansible-navigator` 和 `ansible-playbook` 是什么关系？**
   - 答：解决「开发机跑得通、生产 CI 跑不通」的环境不一致问题——EE 把整个执行环境打成 container image，开发机和 CI 用同一份。2.18 起 `ansible-navigator` 取代 `ansible-playbook` 成为主 CLI，EE 不可用时才回退系统 Python。

3. **Jinja 沙箱改进限制了哪些访问？对什么场景最关键？**
   - 答：限制 `__class__`、`__bases__`、`__subclasses__` 等魔术属性，以及 `os.environ`、`subprocess.Popen` 等敏感对象，模板只能访问 Ansible 显式暴露的属性。对多租户场景（不同 team 共用控制节点写 playbook）最关键——恶意 playbook 读不到环境变量里的 secret。

4. **为什么说 Ansible 是「过程式」、Terraform 是「声明式」？这对状态管理意味着什么？**
   - 答：playbook 按顺序执行 task，靠 **idempotency（幂等性）** 反复执行收敛到目标状态；Terraform 维护一份 state 文件描述「期望终态」。Ansible 没有集中式 state，跨资源依赖和漂移检测不如声明式工具直接。

5. **AWS SDK 迁移到 `boto3` 完成后，还在用 `boto` 的 AWS playbook 会怎样？**
   - 答：`ec2`、`s3`、`iam` 等 AWS 模块只支持 `boto3`，旧 `boto` 模块会触发 deprecation warning，必须升级到支持 `boto3` 的版本。

6. **Ansible 在哪些场景「不太适合」？**
   - 答：基础设施声明式管理（Terraform / Pulumi 更专业）、超大规模 monorepo（> 5000 节点，控制节点是单点）、强状态管理、Kubernetes 资源编排（Helm / Kustomize / ArgoCD 更直接）、Windows Server Core / Nano Server 兼容性。

---

## 练习

1. 用 `ansible-navigator run` 跑一个最小 playbook，分别观察 EE 模式与系统 Python 模式下 `ansible --version` 报出的 Python 路径差异。
2. 写一个用 `ansible-vault` 加密的 `vars/secret.yml`，在 CI 里用 `--vault-password-file` 解密后跑 playbook，确认 secret 不落明文本地。
3. 用 `requirements.yml` 声明 collections 并加 lock file，在两台环境里 `ansible-galaxy collection install -r requirements.yml --locked`，验证模块版本完全一致。
4. 在 CI 第一步跑 `ansible-lint` + `ansible-playbook --syntax-check`，故意引入一个语法错误，确认流水线在合并前被拦下。
5. 拿一个还在用 `boto` 的 AWS playbook，把 `ec2` / `s3` / `iam` 模块迁移到 `boto3` 版本，逐个消除 deprecation warning。

---

## 进阶路径

- **从「会用」到「用对」**：playbook 的幂等性设计、`handler` 触发机制、`role` 拆分与复用、变量优先级（`group_vars` / `host_vars` / `extra_vars`）。
- **从「单机」到「规模」**：AWX / Controller 集群化、动态 inventory（云厂商标签驱动）、SSH 连接池与 fact 并行收集调优。
- **从「配置」到「安全」**：Jinja 沙箱策略落地、Vault 密钥管理与轮换、最小权限 `become`、敏感任务的审计日志。
- **从「Ansible」到「生态」**：开发并发布自己的 collections 到 Galaxy（含私有源）、自定义 module / plugin、把 Ansible 与 Terraform / Pulumi 按「配置 + 应用层 vs 基础设施层」分工协同。

---

## 常见问题 FAQ

1. **EE 默认化之后，还能用系统 Python 跑 playbook 吗？**
   能。`ansible-navigator` 默认尝试 EE，EE 不可用时回退到系统 Python。但生产环境推荐始终走 EE，避免「我本地能跑」的环境差异。

2. **Windows 节点怎么管理？**
   用 `win_` 系列模块（基于 WinRM 连接），Linux + Windows 混合纳管是 Ansible 的强项。注意 Windows Server Core 上的兼容性不如完整版 Windows。

3. **collections 版本冲突怎么办？**
   用 `requirements.yml` 加 lock file 锁定版本；企业内部可搭私有 Galaxy 把团队依赖隔离，避免公共仓库的版本波动。

4. **老 `boto` 相关 AWS 模块报错怎么处理？**
   迁移到 `boto3` 版本；旧 `boto` 模块已弃用。可先用 `ansible-lint` 扫出所有 `boto` 调用再批量替换。

5. **大型 monorepo（> 5000 节点）性能不够怎么办？**
   AWX / Controller 集群 + 分片 inventory + 连接池复用；若仍触达边界，把基础设施层交给 Terraform / Pulumi，Ansible 只负责配置与应用层。

6. **Ansible 和 Terraform 该怎么分工？**
   Ansible 管「配置 + 应用层」（装软件、改配置、发版本），Terraform / Pulumi 管「基础设施层」（建 VPC、开机器、配网络），两者互补而非二选一。