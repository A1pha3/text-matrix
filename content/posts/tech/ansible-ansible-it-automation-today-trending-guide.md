---
title: "ansible/ansible：64k Stars 的 IT 自动化工具，13 年后为什么还在 Trending"
date: "2026-07-03T20:57:00+08:00"
lastmod: "2026-07-03T20:57:00+08:00"
draft: false
slug: "ansible-ansible-it-automation-today-trending-guide"
description: "Ansible 主仓库今日再登 GitHub Trending。本文拆解 ansible-core 2.18 主线：execution environment 成为推荐执行方式、模板执行的信任边界、collections 治理、AWS 模块的 boto3 化，以及今天该不该用 Ansible 的判断。"
categories: ["技术笔记"]
tags: ["DevOps", "Python"]
author: "text-matrix"
---

## 本文导读

读完本文你将能够：

- 解释为什么 Ansible 主仓库今天还能在 Trending 拿到关注（社区版 + AWX/Controller 双线）
- 看清 ansible-core 2.18 在 execution environment、模板信任边界、collections 治理上的演进
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

**第二层：单日 +50 是合理流量。** Ansible 主仓库的提交节奏稳定（每周 ~80 commits），不像新项目那样爆发式增长。+50 Stars 大部分来自运维社区对 2.x 主线的关注——尤其是 execution environment 成为推荐执行方式、模板信任边界、collections 治理等已经落地的变化。

把近期提交逐条看下来，核心信号集中在四条主线：

- **execution environment（执行环境）**：EE 从「可选」变成推荐执行方式，本机、CI 与 AWX 共用容器化环境
- **模板执行的信任边界**：模板不做运行时沙箱，安全靠 Vault 与 RBAC 落在边界上，而非模板引擎隔离
- **collections 治理**：版本依赖解析、私有 Galaxy 源、lock file 支持
- **AWS SDK**：AWS 模块早已只依赖 `boto3`，新功能在 `amazon.aws` / `community.aws` collection 里独立演进

---

## 二、项目地图：核心模块构成

Ansible 是一个 Python 仓库，按职责切成多个子包：

| 模块 | 职责 |
| --- | --- |
| `lib/ansible/` | 核心引擎（playbook 解析、task 执行、connection） |
| `lib/ansible/modules/` | 内置模块（command、file、copy、service 等几百个核心模块） |
| `lib/ansible/plugins/` | 插件（connection、lookup、filter、callback） |
| `lib/ansible/cli/` | 命令行入口（`ansible-playbook`、`ansible`） |
| `test/lib/ansible_test/` | 集成测试框架 |
| `docs/` | 文档（rst + sphinx） |

**注意**：Ansible 主仓库只包含「Ansible Core」——执行引擎 + 内置模块。AWS / Azure / GCP / Kubernetes 等 provider 是独立 collections 仓库（`community.aws`、`amazon.aws`、`community.kubernetes` 等），按独立版本发版。

---

## 三、ansible-core 2.18 主线：5 个值得知道的方向

ansible-core 2.18 于 2024-11 发布，是当前活跃主线（社区发行版 Ansible 11 内置）。下面按对采用决策的影响排序，先说执行方式，再说安全、依赖与性能。

### 1. Execution Environment 成为推荐执行方式

- **EE（Execution Environment，执行环境）** 是一个容器镜像，把 ansible-core、collections 以及它们依赖的 Python 包一次性打包。
- AWX / Automation Controller 始终以 EE 为执行单元；本机开发时，EE 也从「可选」逐渐变成「推荐」。
- `ansible-navigator` 是现代主推的 CLI/TUI，它把 playbook 放进指定 EE 里运行，`--mode stdout` 可以保持传统命令行观感；`ansible-playbook` 仍然可用，但默认走系统 Python，缺少 EE 的隔离保证。

EE 解决的是「开发机能跑、生产 CI 跑不了」的环境不一致：开发机和 CI 用同一份 image，Python 版本、系统包、collection 版本全部一致，问题自然消失。

### 2. 模板执行的信任边界

Ansible 的模板和 playbook **不做运行时沙箱**。官方文档把「谁能改 playbook / 模板」明确当成一条信任边界——模板里有足够自由度，能最终执行任意命令，指望模板引擎兜底是把风险放错了位置。

对多租户场景（不同团队共用控制节点写 playbook），更稳妥的做法是把信任建立在边界而不是模板引擎上：

- 用 Ansible Vault 加密 secret，playbook 里只留引用；
- 用 AWX / Controller 的 RBAC 限制谁能提交、谁能运行 playbook；
- 把控制节点当作需要保护的资产，而不依赖 Jinja 隔离。

### 3. Collections 治理

- **依赖解析**：collection 的版本约束兼容 PEP 440 语法，`>=1.0.0,<2.0.0` 这类写法在 Galaxy 上可直接使用。
- **私有源**：支持私有 Galaxy（企业内部包仓库），团队能把自己的 collection 与公共仓库隔离。
- **安装方式**：`ansible-galaxy collection install -r requirements.yml` 是标准做法；要钉死已解析的版本，再用 lock file 落盘。

生态里 collection 的数量仍在快速增长，治理跟不上就会出现「一个 playbook 把大量依赖一起拉进来」的版本冲突。版本约束、私有源、lock file 三者合起来，正是缓解这一点的配套手段。

### 4. AWS 模块的 boto3 化

- AWS 模块早就从 ansible-core 拆出，落在 `amazon.aws` / `community.aws` 两个 collection 里，并统一只依赖 `boto3`。
- `boto` 是 Python 2 时代的 SDK，早已不维护；迁移随 collection 拆分早年完成，并不是 2.18 的新动作。
- 对 AWS 用户，关键不是「2.18 要不要迁移」，而是确认自己用的 collection 在 `requirements.yml` 里锁定了 `boto3` 兼容版本；老 `boto` 调用会被上游直接弃用。

### 5. 大规模执行在哪提速

性能瓶颈通常不在「单机跑得慢」，而在调度、连接、并发三处：

- **worker 进程**：ansible-core 为每个受控主机 fork 一个 worker 进程，并发度由 `forks` 参数控制，任务按 strategy（默认 linear）推进。
- **SSH 长连接复用**：借助 OpenSSH 的 ControlPersist 复用连接，一台主机只建一次握手，省掉重复认证。
- **fact 收集并行**：facts 在各主机之间并行收集，不串行等待。

对上千 task、上百节点的大型 playbook，这几项是决定执行时长的关键；规模再往上，就要靠 AWX / Controller 集群 + 动态 inventory，而不是指望单控制节点。

---

## 四、近期热提交：3 个值得关注的方向

`commits/main.atom` 过去 24 小时的提交（以下按主题归纳，不逐字引用提交标题）集中在三个方向：

### 1. EE-first 的执行路径收尾

接连几笔提交都在打磨「优先用 EE 执行」的路径：默认尝试用 EE 运行，并保留系统 Python 作为回退路径，同时更新面向 `ansible-playbook` 老用户的迁移文档。方向是把新用户的默认姿势引导到容器化执行上——这是 §三.1 的落地动作，而不是在攒新功能。

### 2. collection 依赖解析补强

`ansible-galaxy` 的版本解析在向前走：支持更宽泛的版本约束、正确解析 collection 的传递依赖，并为私有 Galaxy 场景补集成测试。对治理的意义见 §三.3，这里是把「能安装」推进到「装得对」。

### 3. 模块与 collection 的新增、弃用

- `kubernetes.core` 跟随上游 collection 独立发版节奏继续演进（新版本与 ansible-core 本体无关）。
- 老 `docker` 模块被移除，统一改用 `community.docker`——这正是「能力从内核拆到 collection」趋势的一个例证。

这类改动说明一件事：Ansible 的创新速度体现在 collection 层，而不是 ansible-core 本体；看 Ansible 生态是否活跃，别只盯着主仓库。

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

1. **新项目直接走 ansible-core 2.18 + EE**：本机用 `ansible-navigator run --mode stdout`，AWX / Controller 里则配一份 EE image。
2. **依赖落在 EE 里，而不是控制节点的系统 Python**：需要临时加 Python 包时，写进 EE 的 requirements 并重建 image，不要往系统 Python 里 `pip install`。
3. **collections 用 requirements.yml 固定版本区间，必要时配 lock file**：`ansible-galaxy collection install -r requirements.yml` 是标准安装方式。
4. **secret 管理用 Ansible Vault**：playbook 里直接放 secret 是反模式，Vault 加密存储，只留引用。
5. **CI 第一步跑 `ansible-lint` + `--syntax-check`**：语法或风格不过就卡在合并前。

Ansible 今天的 Trending 表现是「稳定流量 + 2.18 主线演进」。13 年的项目不是「古董」，而是「运维生态基础设施」。EE 成为推荐执行方式、模板信任边界、collections 治理、AWS 模块 boto3 化这几条主线并行，说明 Red Hat / 社区仍在认真维护这个工具。

---

## 最小可运行示例

把上面的主线串成一个能直接跑的任务流：用 EE（执行环境）跑一个幂等 playbook，secret 走 Vault，collections 版本固定在 requirements.yml，最后在 CI 跑 lint + 语法检查。

```yaml
# site.yml —— 在 EE 里执行，依赖 requirements.yml 固定 collection 版本
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
# 1) 安装 collections（按 requirements.yml 的版本区间装）
ansible-galaxy collection install -r requirements.yml

# 2) 用 EE 跑 playbook（推荐）；无 EE 时回退系统 Python
ansible-navigator run site.yml --mode stdout

# 3) CI 第一步：语法检查 + lint，失败就卡在合并前
ansible-playbook site.yml --syntax-check
ansible-lint site.yml
```

这条链里：EE 解决「开发机和 CI 环境不一致」，Vault 解决「secret 不能明文进 git」，requirements.yml 固定 collection 版本区间。三者配合，playbook 才能在任意机器复现同一结果。

---

## 自测题（附参考答案）

1. **Ansible 主仓库包含哪些部分？为什么 AWS / Azure / GCP / Kubernetes 这些 provider 是独立 collections 仓库？**
   - 答：主仓库只包含 **Ansible Core**（执行引擎 + 内置的 `ansible.builtin` 模块集，几百个常用模块）。provider 是独立 collections 仓库（`amazon.aws`、`community.aws`、`kubernetes.core` 等），按各自版本节奏发版，避免核心引擎跟着 provider 一起膨胀。

2. **EE（执行环境）是什么，解决了什么问题？`ansible-navigator` 和 `ansible-playbook` 是什么关系？**
   - 答：EE 是一个容器镜像，把 ansible-core、collections 和依赖打包成同一执行环境，解决「开发机跑得通、生产 CI 跑不通」的环境不一致。`ansible-navigator` 是现代主推的 CLI/TUI，把 playbook 放进指定 EE 里跑（可用 `--mode stdout` 保留命令行观感）；`ansible-playbook` 仍在，但默认走系统 Python。AWX / Controller 始终以 EE 为执行单元。

3. **Ansible 对模板做运行时沙箱吗？多租户场景的信任边界该建在哪？**
   - 答：不做运行时沙箱。官方把「谁能改 playbook / 模板」视为信任边界，模板有足够自由度执行任意命令。多租户安全靠边界：用 Vault 加密 secret、用 AWX / Controller 的 RBAC 限制提交与运行、把控制节点当作受保护资产，而不是依赖模板引擎隔离。

4. **为什么说 Ansible 是「过程式」、Terraform 是「声明式」？这对状态管理意味着什么？**
   - 答：playbook 按顺序执行 task，靠 **idempotency（幂等性）** 反复执行收敛到目标状态；Terraform 维护一份 state 文件描述「期望终态」。Ansible 没有集中式 state，跨资源依赖和漂移检测不如声明式工具直接。

5. **AWS 模块统一依赖 `boto3` 后，还在用 `boto` 的 AWS playbook 会怎样？**
   - 答：AWS 模块都在 `amazon.aws` / `community.aws` collection 里并只支持 `boto3`；老 `boto` 调用被上游弃用，需要把 `requirements.yml` 锁到支持 `boto3` 的 collection 版本，并替换相关模块调用。

6. **Ansible 在哪些场景「不太适合」？**
   - 答：基础设施声明式管理（Terraform / Pulumi 更专业）、超大规模 monorepo（> 5000 节点，控制节点是单点）、强状态管理、Kubernetes 资源编排（Helm / Kustomize / ArgoCD 更直接）、Windows Server Core / Nano Server 兼容性。

---

## 练习

1. 用 `ansible-navigator run` 跑一个最小 playbook，分别观察 EE 模式与系统 Python 模式下 `ansible --version` 报出的 Python 路径差异。
2. 写一个用 `ansible-vault` 加密的 `vars/secret.yml`，在 CI 里用 `--vault-password-file` 解密后跑 playbook，确认 secret 不落明文本地。
3. 用 `requirements.yml` 声明 collection 版本区间，在两个不同环境里分别 `ansible-galaxy collection install -r requirements.yml`，再用 `ansible-galaxy collection list` 比对已安装版本；若需钉死版本，研究 lock file 的启用方式。
4. 在 CI 第一步跑 `ansible-lint` + `ansible-playbook --syntax-check`，故意引入一个语法错误，确认流水线在合并前被拦下。
5. 拿一个还在用 `boto` 的 AWS playbook，把 `ec2` / `s3` / `iam` 模块迁移到 `boto3` 版本，逐个消除 deprecation warning。

---

## 进阶路径

- **从「会用」到「用对」**：playbook 的幂等性设计、`handler` 触发机制、`role` 拆分与复用、变量优先级（`group_vars` / `host_vars` / `extra_vars`）。
- **从「单机」到「规模」**：AWX / Controller 集群化、动态 inventory（云厂商标签驱动）、SSH 连接池与 fact 并行收集调优。
- **从「配置」到「安全」**：Vault 密钥管理与轮换、最小权限 `become`、敏感任务的审计日志、把「信任边界」落到实处（谁有权限提交和运行 playbook）。
- **从「Ansible」到「生态」**：开发并发布自己的 collections 到 Galaxy（含私有源）、自定义 module / plugin、把 Ansible 与 Terraform / Pulumi 按「配置 + 应用层 vs 基础设施层」分工协同。

---

## 常见问题 FAQ

1. **EE 成为推荐执行方式后，还能用系统 Python 跑 playbook 吗？**
   能。`ansible-playbook` 以及 `ansible-navigator` 的系统 Python 模式都能跑；但 CI 和 AWX / Controller 推荐统一走 EE，避免「我本地能跑」的环境差异。

2. **Windows 节点怎么管理？**
   用 `win_` 系列模块（基于 WinRM 连接），Linux + Windows 混合纳管是 Ansible 的强项。注意 Windows Server Core 上的兼容性不如完整版 Windows。

3. **collections 版本冲突怎么办？**
   用 `requirements.yml` 加 lock file 锁定版本；企业内部可搭私有 Galaxy 把团队依赖隔离，避免公共仓库的版本波动。

4. **老 `boto` 相关 AWS 模块报错怎么处理？**
   先在 `requirements.yml` 里确认 `amazon.aws` / `community.aws` 的版本，再用 `ansible-lint` 扫出旧的 `boto` 调用并替换；老 `boto` 已被上游弃用。

5. **大型 monorepo（> 5000 节点）性能不够怎么办？**
   AWX / Controller 集群 + 分片 inventory + 连接池复用；若仍触达边界，把基础设施层交给 Terraform / Pulumi，Ansible 只负责配置与应用层。

6. **Ansible 和 Terraform 该怎么分工？**
   Ansible 管「配置 + 应用层」（装软件、改配置、发版本），Terraform / Pulumi 管「基础设施层」（建 VPC、开机器、配网络），两者互补而非二选一。