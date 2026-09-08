---
title: "ansible/ansible：70k Stars 的 IT 自动化工具，14 年后为什么还在 Trending"
date: "2026-07-03T20:57:00+08:00"
lastmod: "2026-09-08T10:00:00+08:00"
draft: false
slug: "ansible-ansible-it-automation-today-trending-guide"
description: "Ansible 主仓库再次登上 GitHub Trending。本文基于 2026 年 9 月的仓库与版本现状，拆解 ansible-core 2.19~2.21 主线：模板引擎重构、Python 基线收紧、执行环境（EE）容器化、collections 治理，以及今天该不该用 Ansible 的判断。"
categories: ["技术笔记"]
tags: ["DevOps", "Python"]
author: "text-matrix"
---

## 本文导读

读完本文你将能够：

- 解释一个 14 年的项目为什么还能登上 GitHub Trending（答案不在新功能，而在架构重心转移）
- 说清 ansible-core 2.19~2.21 三个版本的实质变化，尤其是 2.19 的模板引擎重构——它是 Ansible 十多年来对 playbook 行为影响最大的一次改动
- 判断在你的项目里 Ansible 是不是合适的选择（vs Terraform / Pulumi / Chef / Salt）
- 知道 Ansible 当前的能力边界（Windows 节点、规模上限、状态管理）

适合读者：运维 / SRE 工程师、IaC（基础设施即代码）选型架构师，以及对配置管理生态感兴趣的开发者。

> 范围说明：Ansible 是一个约 70.6k Stars（2026-09-08 核实）、GPLv3 协议的 IT 自动化工具。本文不展开入门教程，也不复述基本 playbook 语法，只回答三件事：它为什么还在被关注、2.19~2.21 主线改了什么、采用边界在哪里。文中所有版本号与仓库数据均核实自官方文档、GitHub API 与 PyPI，核实时间 2026-09-08。

---

## 目录

- [本文导读](#本文导读)
- [一、先给判断](#一先给判断)
- [二、项目地图：核心目录构成](#二项目地图核心目录构成)
- [三、ansible-core 2.19~2.21 主线：模板引擎重构与运行时收紧](#三ansible-core-219221-主线模板引擎重构与运行时收紧)
- [四、近期提交动向：维护与安全修复为主](#四近期提交动向维护与安全修复为主)
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

2026 年 7 月初，Ansible 主仓库再次出现在 GitHub Trending 上。一个 2012 年 3 月创建、已经迭代了 14 年的项目，靠什么拿到新关注？拆开看有两层。

**第一层：它不是在吃老本，而是刚经历了一次伤筋动骨的重构。** ansible-core 2.19（2025 年 7 月发布）重写了模板引擎，引入 data tagging（数据标签）机制，改变了条件判断和变量求值的行为——大量老 playbook 升级后第一次跑就报错。围绕这次重构的适配、迁移和讨论，是 Ansible 近一年社区热度的主要来源。

**第二层：主仓库的提交频率在降，但这是架构决策，不是衰退。** 最近 52 周（截至 2026-09-08）ansible/ansible 仓库共 466 次提交，周均约 9 次——看起来不多，因为 Ansible 的工程重心早已转移到 collection（集合）层：AWS、Kubernetes、Docker、Windows 等能力都在各自独立的仓库里按自己的节奏发版。主仓库只保留执行引擎。看 Ansible 活不活跃，不能只盯着这一个仓库。

把版本演进和近期动向放在一起，当前有四条主线值得知道：

- **模板引擎重构（2.19）**：data tagging 让"字符串什么时候被当成模板渲染"有了明确规则，未受信来源的模板默认不再渲染
- **运行时收紧（2.20 / 2.21）**：控制节点 Python 3.12 起步，一批历史上的宽松行为转为报错或弃用
- **执行环境（EE）容器化**：AWX / Automation Controller 以 EE 为唯一执行单元，CLI 场景官方也在引导，但不强制
- **collections 治理**：版本约束、私有 Galaxy 源、requirements.yml 钉版本，成为多团队协作的标配

---

## 二、项目地图：核心目录构成

Ansible 主仓库是一个 Python 项目，按职责划分目录：

| 目录 | 职责 |
| --- | --- |
| `lib/ansible/executor/` | 任务执行器（worker 进程、strategy 调度） |
| `lib/ansible/template/` | 模板引擎（2.19 重构后 data tagging 的核心所在） |
| `lib/ansible/modules/` | 内置模块（`ansible.builtin`，几百个核心模块） |
| `lib/ansible/plugins/` | 插件（connection、lookup、filter、callback 等） |
| `lib/ansible/cli/` | 命令行入口（`ansible-playbook`、`ansible`、`ansible-galaxy`、`ansible-vault`） |
| `lib/ansible/galaxy/` | collection 安装与依赖解析 |
| `changelogs/` | 变更日志片段（每个 PR 附带，发版时汇编） |
| `test/` | 单元、集成、sanity 测试（含 `ansible-test` 框架） |

两点容易误解的地方：

- **主仓库只包含 Ansible Core**——执行引擎加内置模块。AWS / Azure / Kubernetes / Docker 等能力在独立的 collection 仓库（`amazon.aws`、`kubernetes.core`、`community.docker` 等），按独立版本发版。
- **文档不在这个仓库里。** 官方文档源码在独立的 `ansible/ansible-documentation` 仓库维护，这也是主仓库提交数偏低的原因之一。

---

## 三、ansible-core 2.19~2.21 主线：模板引擎重构与运行时收紧

三个版本的时间线：2.19 于 2025-07-21 发布，2.20 于 2025-11-03 发布，2.21 于 2026 年 5 月发布（[官方发布与维护时间表](https://docs.ansible.com/ansible/latest/reference_appendices/release_and_maintenance.html)）。社区发行版 Ansible 14（2026-06-02 首发，最新 14.3.1）内置 2.21，是当前的推荐起点；Ansible 11、12 已于 2025 年 12 月停止维护，还在 2.18 上跑生产环境应该把升级排上日程了。

### 1. 2.19：模板引擎重构，升级的最大风险点

这是 ansible-core 近十年影响面最大的一次变更，核心是 data tagging：引擎现在给每个值打上来源与信任标签，据此决定它能否被渲染成模板。对 playbook 作者，直接的影响有四条（[官方 2.19 移植指南](https://docs.ansible.com/ansible/latest/porting_guides/porting_guide_core_2.19.html)）：

- **条件表达式必须是布尔值**。`when: inventory_hostname` 这类依赖 Python truthy 判断的写法默认报错，要写成显式比较或过滤器表达式。临时兜底可用 `ALLOW_BROKEN_CONDITIONALS` 配置降级为警告，但这是迁移期的拐杖，不是长期方案。
- **表达式里不能再嵌 `{{ }}`**。`when: 1 + {{ value }} == 2` 这种动态拼接直接报错，应写成 `when: 1 + value == 2`。
- **未受信模板默认不渲染**。只有来自可信来源的字符串才会被当模板求值。官方迁移指南把旧模型描述为"导致大量可构成 CVE 的 RCE 漏洞"——新模型把失败后果从安全漏洞降级为功能失效。
- **只保留 native Jinja 模式**。模板求值为 `None` 不再隐式转成空字符串；`range()` 结果必须加 `| list` 才能存入变量。

升级建议按官方移植指南的说法来：先在 staging 环境把存量 playbook 和 role 全量跑一遍，报错点基本就是这四类的变体。作为补偿，新引擎的报错信息带变量来源（文件、行号、列号），排查体验比旧版好不少。

### 2. 2.20：Python 基线与一批行为收紧

- **控制节点要求 Python 3.12+，受管节点要求 3.9+**。老系统的使用者要先解决解释器问题。
- **`INJECT_FACTS_AS_VARS` 弃用**，2.24 起默认关闭。`{{ ansible_os_distribution }}` 这类写法要迁移到 `{{ ansible_facts['distribution'] }}`。
- **Galaxy v2 API 移除**，collection 服务器必须支持 v3 API——自建 Galaxy / 制品库的团队要确认服务端版本。
- 此外 `failed_when` 抑制的错误信息里 `exception` 键改名，Windows 上 PowerShell 路径引号自动剥离行为移除，依赖这两处写法的 playbook 需要检查。

### 3. 2.21：低风险版本

官方移植指南里几乎所有章节都标注"无显著变化"。唯一值得留意的是：模块与 action 插件仅靠返回非零 `rc` 来暗示失败已被弃用，2.22 起会发运行时警告。这只影响自定义模块作者，普通 playbook 用户可以放心升级。

### 4. 执行环境（EE）：容器化执行走到哪一步了

EE（Execution Environment，执行环境）是一个容器镜像，标准内容包含 `ansible-core`、`ansible-runner`、Python 和内容依赖，可以再加 collections 和自定义组件。它的价值在环境一致性：开发机、CI 和自动化平台用同一份镜像，Python 版本、系统包、collection 版本全部锁死。

当前的位置可以这样概括：**AWX / Automation Controller 里 EE 是唯一执行单元；纯 CLI 场景下 `ansible-playbook` 依然直接跑在系统 Python 上，EE 是官方引导的方向而非强制**。`ansible-navigator`（截至 2026-08 发布 26.8.0，采用日历版本号）是 EE 的配套 CLI/TUI，用 `--mode stdout` 可以保留传统命令行观感。

### 5. collections 治理与 AWS 模块的 boto3 化

collection 的版本约束兼容 PEP 440 语法，`>=1.0.0,<2.0.0` 这类写法可直接用在 `requirements.yml` 里。企业内部可以自建私有 Galaxy，把团队依赖与公共仓库隔离。要复现环境，把 `requirements.yml` 里的版本约束写成精确版本（`version: 6.2.0`）是当前的标准做法——`ansible-galaxy` 至今没有类似 npm lock file 的锁定文件机制，精确约束就是现有的锁定手段。

AWS 模块的情况是历史遗留清理的延续：`boto` 是 Python 2 时代的 SDK，早已停止维护；AWS 模块早年在 collection 拆分时统一迁移到 `boto3`，落在 `amazon.aws` / `community.aws` 两个 collection 里独立演进。今天真正要确认的是自己锁定的 collection 版本仍在维护期——collection 本身也会 EOL，锁着老版本同样有风险。

---

## 四、近期提交动向：维护与安全修复为主

看主仓库 2026 年 8 月到 9 月初的提交（以下为可公开核实的实际提交内容），节奏是维护性的：

- **连接与模块修复**：SSH 连接插件修复了特权提升场景下的 ssh 检测（#87275）；`file` 模块更新文档；`setup_cron` 修复 Alpine 上 busybox crond 的运行方式。
- **安全修复**：`tempfile` 对 prefix/suffix 做了清理，堵住路径遍历（#87453）。这类修复通常伴随独立安全公告，值得关注。
- **Windows 执行通道改进**：压缩 exec wrapper 的输入、分离 PowerShell 执行选项与模块 JSON（#87291、#87433）——Windows 受管节点的传输效率与稳定性仍在打磨。
- **弃用推进**：模块和 action 返回 `skipped` 值的行为被弃用（#87009），与 2.21 对非零 `rc` 失败推断的弃用同属一条线：把"靠返回值隐式推断状态"的老习惯收干净。

这个节奏印证了 §一 的判断：引擎层的激进改动（2.19 重构）已经落地，主仓库进入消化期，剩下的创新发生在 collection 层。想追踪 Ansible 生态的新能力，盯各 collection 的 release 页面比盯主仓库有用。

---

## 五、采用边界

### 适合

- **配置管理与批量操作**：装软件、改配置、重启服务、批量命令执行，Ansible 的原生主场
- **多云混合编排**：AWS + Azure + GCP + 私有云的统一操作入口（各自有官方或社区 collection）
- **网络设备自动化**：Cisco / Juniper / Arista 等设备配置是 Ansible 的传统强项（`netconf`、`httpapi` connection plugins）
- **Linux + Windows 混合环境**：一套工具同时管理两类节点（见 §六 对比表）
- **运维团队主导的项目**：YAML playbook 对运维友好，学习曲线比 Terraform HCL 平缓

### 不太适合

- **基础设施声明式管理**：建 VPC、开机器、管 DNS 这类资源编排，Terraform / Pulumi 的 state 管理更成熟
- **强状态管理需求**：Ansible 是过程式工具，靠幂等性（idempotency）收敛，没有集中 state 文件，漂移检测和跨资源依赖处理不如声明式工具直接
- **Kubernetes 资源编排**：Helm / Kustomize / ArgoCD 是更对口的工具
- **超大节点规模的单一控制面**：单控制节点在数千节点级就要认真调优（`forks`、连接复用、fact 缓存），更大规模需要 AWX / Controller 集群或分片执行

### 升级路径建议

- **还在 2.18 / Ansible 11 的**：这两个版本已 EOL，先升到 Ansible 14（ansible-core 2.21）。重点成本在 2.19 的模板引擎重构，按 §三.1 的清单在 staging 全量回归。
- **跨多个大版本升级**（如 2.9 时代）：模块参数、collection 拆分、Python 基线三处叠加，逐个 playbook 验证，不要跳过移植指南。
- **AWX / Controller 用户**：升级 core 前先核对平台版本兼容矩阵。

---

## 六、和 Terraform / Chef / Salt 的边界

| 维度 | Ansible 2.21 | Terraform 1.16 | Chef Infra | Salt 3008 |
| --- | --- | --- | --- | --- |
| 配置语言 | YAML | HCL | Ruby DSL | YAML / SLS |
| 状态模型 | 过程式（幂等收敛，无 state） | 声明式（state 文件） | 声明式（recipe） | 声明式（SLS） |
| 学习曲线 | 低 | 中 | 高 | 中 |
| Windows 支持 | 强（PSRP / WinRM / SSH 连接） | 弱 | 强 | 弱 |
| 多云资源编排 | 一般 | 一等公民 | 一般 | 一般 |
| 典型角色 | 配置 + 应用部署 | 基础设施供给 | 配置管理 | 配置管理 + 事件驱动 |

两点使用说明：其一，"适用规模"这种数字各工具官方都不给硬上限，本表已略去——真实上限取决于网络延迟、fact 缓存策略和任务粒度，数千节点以上务必实测；其二，Ansible 和 Terraform 在多数团队是互补而非竞争——Terraform 管基础设施供给，Ansible 管配置与应用层，这也是官方社区反复出现的组合。

---

## 七、起步建议

1. **新项目直接从 Ansible 14（ansible-core 2.21）起步**：控制节点 Python 3.12+。纯 CLI 起步可以先用系统 Python，团队规模上来后迁到 EE。
2. **依赖进容器，不进系统 Python**：走 EE 的团队，把 Python 包和 collection 写进 EE 构建定义并重建镜像，不要往控制节点系统环境里 `pip install`。
3. **collections 版本用 requirements.yml 钉精确版本**：`ansible-galaxy collection install -r requirements.yml` 是标准安装方式；要可复现就写精确版本号，没有 lock file 机制可用。
4. **secret 管理用 Ansible Vault**：playbook 里明文放 secret 是反模式。Vault 加密落盘，playbook 里只留引用。
5. **CI 第一步跑 `ansible-lint` 和 `--syntax-check`**：2.19 之后还要加上一条——用 `ALLOW_BROKEN_CONDITIONALS` 的默认值（报错）跑一次完整检查，把 truthy 条件在合并前拦下。

Ansible 的现状可以概括为一句话：引擎层刚刚完成十年一遇的重构，生态层持续分头演进。14 年的项目不是古董，是配置管理这个位置的默认答案之一——前提是你跟得上 2.19 之后的新规则。

---

## 最小可运行示例

把上面的主线串成一个能直接跑的任务流：用 Ansible 14 跑一个幂等 playbook，secret 走 Vault，collections 版本钉死在 requirements.yml，最后在 CI 跑 lint + 语法检查。

```yaml
# site.yml —— 环境无关的幂等 playbook
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
# 1) 安装 collections（requirements.yml 里用精确版本号）
ansible-galaxy collection install -r requirements.yml

# 2) 跑 playbook（有 EE 用 navigator；无 EE 直接 ansible-playbook）
ansible-navigator run site.yml --mode stdout
ansible-playbook site.yml

# 3) CI 第一步：语法检查 + lint，失败就卡在合并前
ansible-playbook site.yml --syntax-check
ansible-lint site.yml
```

这条链里：EE（或固定的系统 Python 环境）解决"开发机和 CI 环境不一致"，Vault 解决"secret 不能明文进 git"，requirements.yml 的精确版本约束解决"两次安装结果不一致"。三者配合，playbook 才能在任意机器复现同一结果。

---

## 自测题（附参考答案）

1. **ansible-core 2.19 的模板引擎重构对存量 playbook 最大的影响是什么？**
   - 答：条件表达式必须是布尔值，依赖 truthy 判断的 `when` 写法默认报错；表达式内嵌 `{{ }}` 被禁止；未受信来源的模板默认不渲染。升级前应在 staging 全量回归存量 playbook，必要时临时用 `ALLOW_BROKEN_CONDITIONALS` 降级。

2. **EE（执行环境）是什么，解决什么问题？`ansible-navigator` 和 `ansible-playbook` 是什么关系？**
   - 答：EE 是包含 `ansible-core`、`ansible-runner`、Python 和内容依赖的容器镜像，解决"开发机能跑、生产 CI 跑不了"的环境不一致。`ansible-navigator` 是 EE 的配套 CLI/TUI（`--mode stdout` 保留命令行观感）；`ansible-playbook` 直接跑在系统 Python 上，仍是 CLI 场景的基础入口。AWX / Automation Controller 里 EE 是唯一执行单元。

3. **Ansible 的模板现在是沙箱吗？多租户场景的信任边界该建在哪？**
   - 答：Jinja 模板仍然不是安全边界。2.19 的 data tagging 确实引入了信任标签，未受信模板默认不渲染，但安全设计仍应建立在边界上：Vault 加密 secret、AWX / Controller 的 RBAC 限制提交与运行、把控制节点当作受保护资产。

4. **为什么说 Ansible 是"过程式"、Terraform 是"声明式"？这对状态管理意味着什么？**
   - 答：playbook 按顺序执行 task，靠幂等性（idempotency）反复执行收敛到目标状态；Terraform 维护一份 state 文件描述期望终态。Ansible 没有集中 state，漂移检测和跨资源依赖处理不如声明式工具直接。

5. **ansible-galaxy 有没有像 npm lock file 那样的锁定文件？怎么保证两次安装结果一致？**
   - 答：没有。当前的标准做法是在 `requirements.yml` 里写精确版本号（如 `version: 6.2.0`），配合私有 Galaxy 隔离上游波动。

6. **Ansible 在哪些场景"不太适合"？**
   - 答：基础设施声明式供给（Terraform / Pulumi 更对口）、需要集中状态管理的场景、Kubernetes 资源编排（Helm / Kustomize / ArgoCD 更直接）、以及超大节点规模下不愿引入 AWX / Controller 集群的单一控制面。

---

## 练习

1. 在一个 2.18 时代的 playbook 里找一条 truthy `when` 条件，先在 Ansible 14 下运行观察报错，再改写成显式布尔表达式；对比 `ALLOW_BROKEN_CONDITIONALS=true` 时的行为差异。
2. 用 `ansible-navigator run` 分别在 EE 与系统 Python 环境跑同一个 playbook，比较两者报出的 Python 路径与已安装 collection 差异。
3. 写一个用 `ansible-vault` 加密的 `vars/secret.yml`，在 CI 里用 `--vault-password-file` 解密后跑 playbook，确认 secret 不落明文。
4. 用 `requirements.yml` 钉死 collection 精确版本，在两个环境分别安装后用 `ansible-galaxy collection list` 比对结果一致。
5. 在 CI 第一步跑 `ansible-lint` + `ansible-playbook --syntax-check`，故意引入一个 2.19 会拒绝的表达式（如 `when` 里嵌 `{{ }}`），确认流水线在合并前拦下。
6. 拿一个还在用 `boto` 的老 AWS playbook，把模块调用迁移到 `amazon.aws` / `community.aws` 的 `boto3` 版本，逐个消除 deprecation warning。

---

## 进阶路径

- **从"会用"到"用对"**：幂等性设计、`handler` 触发机制、`role` 拆分与复用、变量优先级（`group_vars` / `host_vars` / extra vars），以及 2.19+ 的 data tagging 规则——搞清哪些值会被当模板渲染。
- **从"单机"到"规模"**：`forks` 并发调优、SSH ControlPersist 连接复用、fact 缓存（`gather_facts: false` + 按需收集）、AWX / Controller 集群与动态 inventory。
- **从"配置"到"安全"**：Vault 密钥轮换、最小权限 `become`、审计日志，以及把"谁能提交和运行 playbook"的信任边界制度化。
- **从"使用者"到"开发者"**：自定义模块与 action 插件（注意 2.21 起非零 `rc` 失败推断已弃用，必须显式设置 `failed`）、开发并发布自己的 collection 到 Galaxy、用 `ansible-builder` 构建团队 EE。

---

## 常见问题 FAQ

1. **ansible-core 2.18 还能用吗？升级到 2.21 的最大风险是什么？**
   2.18 已于 2026 年 5 月 EOL，不应再用于生产。升级到 2.21 的最大风险在 2.19 的模板引擎重构：条件必须布尔、表达式禁止内嵌 `{{ }}`、未受信模板不渲染。先在 staging 全量回归，再逐层推广。

2. **Windows 节点怎么管理？**
   受管节点要求 Windows Server 2016 或 Windows 10 以上（自带 PowerShell 5.1，无需额外安装）。连接方式有三种：PSRP（较新，负载下更稳）、WinRM（传统方式）、SSH（2.18 起官方支持）。Windows 专用模块在 `ansible.windows`、`community.windows` 等 collection 里。

3. **collections 版本冲突怎么办？**
   在 `requirements.yml` 里用精确版本号钉死每个 collection；企业内部自建私有 Galaxy 把团队依赖与公共仓库隔离。没有 lock file 机制，精确约束就是当前的锁定手段。

4. **还在用 `boto` 的 AWS playbook 怎么办？**
   AWS 模块集中在 `amazon.aws` / `community.aws`，只支持 `boto3`。先确认 collection 版本仍在维护期，再用 `ansible-lint` 扫出旧调用逐个替换。`boto` 本身已停止维护，没有回退选项。

5. **大规模场景下单控制节点吃力怎么办？**
   调 `forks` 并发、开 fact 缓存、启用 SSH 连接复用（ControlPersist）；规模再往上用 AWX / Controller 集群加分片 inventory。若瓶颈本质是资源编排而非配置管理，把那一层交给 Terraform / Pulumi。

6. **Ansible 和 Terraform 该怎么分工？**
   Ansible 管"配置 + 应用层"（装软件、改配置、发版本），Terraform / Pulumi 管"基础设施层"（建 VPC、开机器、配网络）。两者互补而非二选一，这是社区最常见的组合。
