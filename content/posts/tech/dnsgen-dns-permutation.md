---
title: "DNSGen：智能 DNS 域名变形引擎——子域名枚举的进阶武器"
date: "2026-04-14T22:20:00+08:00"
slug: "dnsgen-dns-permutation"
github_repo: "AlephNullSK/dnsgen"
description: "DNSGen 是 1K Stars 的智能 DNS 域名变形工具，支持 8 种高级变形技术（Word Insertion、Cloud Patterns、Microservice 等）。配合 Findomain 和 massdns 使用，可显著扩展子域名发现范围，支持自定义云平台词表和带注释词表格式。"
draft: false
categories: ["技术笔记"]
tags: ["安全", "BugBounty", "DNS", "渗透测试"]
---

# DNSGen：智能 DNS 域名变形引擎——子域名枚举的进阶武器

DNSGen 是一个用 Python 编写的子域名变形工具：输入一批已知子域名，生成一批"可能存在"的候选，再用 massdns 批量解析，就能在不依赖商业工具的情况下扩大资产发现范围。本文面向渗透测试和 Bug Bounty 场景，讲清它的原理、八种变形技术、三段式工作流，以及和 altdns 的取舍。开始之前，最好已经了解 DNS 基础和子域名枚举的大致思路。

## 学习目标

读完本文，你应该能：

1. 说清域名变形与暴力枚举、CT 日志的差异，以及它适合解决什么问题
2. 复述 DNSGen 的 8 种变形技术，判断每种针对什么场景
3. 安装 DNSGen，编写带注释的自定义词表并完成一次变形
4. 把 DNSGen 接入 Findomain + massdns 的三段式枚举流水线
5. 对比 DNSGen 与 altdns，按场景选择合适的工具

## 目录

- [1 为什么需要域名变形](#1-为什么需要域名变形)
- [2 DNSGen 是什么](#2-dnsgen-是什么)
- [3 八种变形技术](#3-八种变形技术)
- [4 安装与使用](#4-安装与使用)
- [5 完整子域名枚举工作流](#5-完整子域名枚举工作流)
- [6 与 altdns 对比](#6-与-altdns-对比)
- [7 常见问题排查](#7-常见问题排查)
- [8 自测题](#8-自测题)
- [9 练习](#9-练习)
- [10 进阶路径](#10-进阶路径)
- [11 相关资源](#11-相关资源)

---

## 1 为什么需要域名变形

子域名枚举的思路大体分两类：一类是"查"，另一类是"猜"。

"查"指从证书透明度日志（CT 日志，如 crt.sh）拉取出现过证书的子域名。它的缺点是明显的：只能发现**已经申请过证书**的子域名。对于尚未暴露在证书里的内网服务、云平台桶、临时环境，CT 日志一无所知。

"猜"就是域名变形。拿到一个已知子域名作为种子，按固定的模式生成一批"可能存在"的候选，再去逐个解析。DNSGen 做的是后一件事。

### 1.1 CT 日志的盲区

CT 日志只能发现已有证书的子域名，对于：

- 变形子域名（如 `staging.api.example.com`）
- 云平台子域名（如 `s3.amazonaws.com` 上的桶）
- 内部工具子域名（如 `jenkins.internal.com`）

CT 日志**无法发现**，但 DNSGen **可以生成**。

### 1.2 三种方法各有利弊

| 方法 | 优点 | 缺点 |
|------|------|------|
| **暴力枚举** | 覆盖全面 | 字典庞大、速度慢 |
| **CT 日志** | 速度快 | 只能发现已有证书 |
| **DNSGen 变形** | 智能生成、效率高 | 依赖已知域名作为种子 |

三者互补：先用 CT 日志拿"已知的"，再用变形补"可能的"。这也是后面完整工作流的编排逻辑。

---

## 2 DNSGen 是什么

DNSGen 是一个用 Python 写的命令行工具，输入一个已知子域名列表，按预置的词表和变形规则生成一批候选域名，输出到标准输出或文件，供后续批量解析使用。它不负责解析域名，只负责"生成候选"这一环——和它搭档的 massdns 才负责批量解析。

- 项目仓库：<https://github.com/AlephNullSK/dnsgen>
- 语言：Python
- 定位：子域名枚举流水线中的"变形生成"环节
- 搭配工具：Findomain（被动收集）、massdns（批量解析）

它解决的核心问题：**在已知子域名基础上，用低成本方式扩大候选集，提高命中未发现资产的概率。**

---

## 3 八种变形技术

DNSGen 的变形规则分八类。理解每一类"针对什么场景"比死记命令更重要。

### 3.1 Word Insertion（词语插入）

在子域名前插入环境词，捕捉开发、测试环境：

```
输入：api.example.com
变形：staging.api.example.com, dev.api.example.com, test.api.example.com
```

适合发现：暂未纳入正式域的预发布环境。

### 3.2 Number Manipulation（数字操作）

对带数字的子域名做 ±1 操作，覆盖版本升级遗留的旧实例：

```
输入：api2.example.com
变形：api1.example.com, api3.example.com
```

### 3.3 Word Affixing（词语附加）

在子域名前缀加修饰词：

```
输入：www.example.com
变形：devwww.example.com, newwww.example.com
```

### 3.4 Cloud Provider Patterns（云平台模式）

把云厂商和资源类型拼进域名，命中托管在对象存储、托管服务上的资产：

```
输入：example.com
变形：api-aws.example.com, storage-azure.example.com
```

这类候选往往指向 S3 桶、Azure 存储等可公开读取的资源，是漏洞挖掘的高价值目标。

### 3.5 Region Prefixes（区域前缀）

按云区域拼接，捕捉多区域部署：

```
输入：api.example.com
变形：us-east.api.example.com, eu-west.api.example.com
```

### 3.6 Microservice Patterns（微服务模式）

按服务名拼接，命中按微服务拆分的内部架构：

```
输入：example.com
变形：auth-service.example.com, user-api.example.com
```

微服务架构下，这类域名常指向没有接入网关、直接暴露的内部接口。

### 3.7 Internal Tooling（内部工具）

拼接常见运维工具名，命中内网管理后台：

```
输入：example.com
变形：jenkins.example.com, gitlab.example.com, grafana.example.com
```

### 3.8 Port Prefixing（端口前缀）

把端口号拼进子域名，捕捉开发环境常用的非标端口映射：

```
输入：api.example.com
变形：8080.api.example.com, 8443.api.example.com
```

---

## 4 安装与使用

### 4.1 安装

```bash
pip install dnsgen
# 或从源码安装
git clone https://github.com/AlephNullSK/dnsgen
cd dnsgen/
uv sync
```

### 4.2 基本使用

```bash
# 基础变形：读取 seeds.txt，每个种子域名生成一批候选
dnsgen domains.txt

# 使用自定义词表，并输出到文件
dnsgen -w custom_wordlist.txt domains.txt -o results.txt

# 快速模式：只启用部分变形技术，减少生成量
dnsgen -f domains.txt
```

### 4.3 自定义词表格式

词表是纯文本，每行一个词，`#` 开头的是注释。注释让词表可以按用途分组，方便团队维护：

```text
# 环境名称
dev
staging
test
qa

# 云平台
aws
azure
gcp

# 微服务
auth
user
payment
```

---

## 5 完整子域名枚举工作流

DNSGen 单独用意义有限——它只生成候选，不解析。完整的子域名枚举流水线（Findomain + DNSGen + massdns）是三段式：

```bash
# 1. Findomain 从 CT 日志等被动源收集基础子域名
findomain -t example.com -o passive_subdomains.txt

# 2. DNSGen 以基础子域名为种子，生成变形候选
dnsgen passive_subdomains.txt -o mutated_wordlist.txt

# 3. massdns 批量解析所有候选，筛出真实存在的
massdns -r resolvers.txt -t A -o S mutated_wordlist.txt
```

### 5.1 一次真实任务怎么流过这条流水线

假设目标是 `example.com`，流程如下：

1. **被动收集**：`findomain -t example.com` 从证书日志、搜索引擎等公开来源拉回一批已暴露的子域名，比如 `api.example.com`、`mail.example.com`。这一步快，但只能拿到"已知的"。
2. **变形扩展**：把上面这批种子交给 DNSGen，它按八类规则生成 `staging.api.example.com`、`jenkins.example.com`、`8080.api.example.com` 等成百上千个候选。这一步把"已知的"扩展成"可能的"。
3. **批量解析**：massdns 用一份解析器列表（`resolvers.txt`）以高并发把这些候选全部查询一遍，输出其中真实解析出 A 记录的域名。

整条流水线的意义：被动收集保证基础盘，变形扩展负责"撞"出未在证书日志里出现过的内部资产，massdns 负责把空想过滤掉，只留下真实存在的。

### 5.2 产出怎么用

massdns 输出的存活域名，可以继续接入端口扫描、指纹识别、漏洞验证等后续环节。变形这一步的价值在于：很多内部工具、预发布环境不会申请公网证书，CT 日志里永远看不到它们，但它们可能直接暴露在公网 DNS 上——这恰恰是攻击面和排查对象。

---

## 6 与 altdns 对比

altdns（<https://github.com/infosec-au/altdns>）是同类工具中另一个常用选择。两者目标一致：从种子域名生成置换候选。差异在实现语言和定位上：

| 维度 | DNSGen | altdns |
|------|--------|--------|
| 语言 | Python | Go |
| 词表格式 | 带注释，便于按用途分组维护 | 纯文本词表 |
| 安装 | `pip install dnsgen` | 编译二进制或下载 release |
| 定位 | 快速集成，逻辑直观 | 偏性能，适合大规模候选集 |
| 场景 | 想快速接入 Python 工具链 | 候选量巨大、追求解析吞吐 |

选择建议：追求**简单、可读、容易改**选 DNSGen；候选集规模很大、或希望**单二进制部署**选 altdns。两者的产出都交给 massdns 解析，没有锁定关系。

---

## 7 常见问题排查

### 问题 1：pip install dnsgen 失败

**原因**：Python 版本过低或依赖冲突。

```bash
# 1. 检查 Python 版本（需要 3.7+）
python --version

# 2. 使用 uv 安装（推荐）
uv pip install dnsgen

# 3. 从源码安装
git clone https://github.com/AlephNullSK/dnsgen
cd dnsgen/
uv sync
```

### 问题 2：生成的域名数量过多

**原因**：输入域名数量多，或自定义词表过大，导致候选组合爆炸。

```bash
# 1. 使用快速模式（减少变形技术）
dnsgen -f domains.txt

# 2. 限制词表大小（只保留核心词）
head -n 50 custom_wordlist.txt > small_wordlist.txt
dnsgen -w small_wordlist.txt domains.txt

# 3. 先控制种子数量：用 CT 日志拿基础子域名，再变形
findomain -t example.com -o base_subdomains.txt
dnsgen base_subdomains.txt -o results.txt
```

### 问题 3：与 massdns 集成时解析速度慢

**原因**：并发数过低，或 DNS 解析器质量差。

```bash
# 1. 使用高质量解析器列表
curl https://public-dns.info/nameservers.txt > resolvers.txt
massdns -r resolvers.txt -t A -o S mutated_wordlist.txt

# 2. 增加并发数
massdns -r resolvers.txt -t A --timeout 5 -o S mutated_wordlist.txt

# 3. 小规模场景：不用 massdns，直接逐条 dig
dnsgen domains.txt | while read subdomain; do
  dig +short "$subdomain"
done
```

### 问题 4：自定义词表不生效

**原因**：词表格式错误，或文件路径不对。

```bash
# 1. 检查词表格式（每行一个词，# 开头的是注释）
cat custom_wordlist.txt

# 2. 使用绝对路径指定词表
dnsgen -w /full/path/to/custom_wordlist.txt domains.txt

# 3. 快速验证词表是否生效
dnsgen -f -w custom_wordlist.txt test.txt | head -20
```

---

## 8 自测题

用 5 个问题检验自己是否吃透 DNSGen：

1. **域名变形的核心原理是什么？为什么它能发现 CT 日志发现不了的子域名？**
2. **DNSGen 的 8 种变形技术分别适合什么场景？**
3. **如何编写一个带注释的自定义词表？**
4. **如何将 DNSGen 集成到完整的子域名枚举工作流？**
5. **DNSGen 和 altdns 的核心差异是什么？什么场景选哪个？**

**参考答案**：

1. 域名变形通过对已知子域名进行智能排列组合（如插入环境词、添加数字后缀、附加云平台模式），生成可能存在的子域名。CT 日志只能发现已有证书的子域名，而变形能发现尚未申请证书的内部服务子域名。
2. Word Insertion 适合发现环境变体（dev、staging）；Cloud Patterns 适合发现云平台服务；Microservice Patterns 适合发现微服务架构；其余类推。
3. 每行一个词，`#` 开头的是注释。注释可以帮助团队协作时理解每个词的用途。
4. 先用 Findomain 从 CT 日志获取基础子域名，再用 DNSGen 变形生成更多候选，最后用 massdns 批量解析。
5. DNSGen 用 Python，词表支持注释，适合快速集成；altdns 用 Go，单二进制部署、性能更高。选 DNSGen 追求简单，选 altdns 追求大规模性能。

---

## 9 练习

### 练习 1：基础变形实战

创建一个包含 3 个已知子域名的文件 `seeds.txt`（如 `www.example.com`、`api.example.com`、`admin.example.com`），使用 DNSGen 生成变形域名，并将结果保存到 `mutated.txt`。

**目标**：掌握 DNSGen 基础用法。

### 练习 2：自定义词表编写

为某电商平台编写自定义词表，包含以下类型的词：

- 环境（dev、staging、prod）
- 地区（us、eu、asia）
- 服务（payment、order、user、admin）

使用这个词表对 `shop.example.com` 进行变形。

**目标**：掌握带注释词表的编写和使用。

### 练习 3：完整工作流集成

编写一个 Bash 脚本，自动化执行以下流程：

1. 使用 Findomain 从 CT 日志获取基础子域名
2. 使用 DNSGen 进行变形
3. 使用 massdns 解析所有候选域名
4. 将存活的子域名保存到 `alive.txt`

**目标**：掌握完整子域名枚举工作流的自动化。

### 练习 4：云平台发现

针对某目标，使用 DNSGen 的 Cloud Provider Patterns 技术生成可能存在于 AWS、Azure、GCP 的子域名。手动验证这些子域名是否存在，并分析它们可能暴露的服务。

**目标**：理解云平台子域名的风险。

### 练习 5：性能优化

对比以下三种方式的性能：

1. 纯 DNSGen + 逐条 dig 解析
2. DNSGen + massdns（10 并发）
3. DNSGen + massdns（100 并发）

记录每种方式的处理时间和发现的子域名数量。

**目标**：掌握性能优化的方法。

---

## 10 进阶路径

### 10.1 基础阶段（第 1-2 周）

- [ ] 理解域名变形原理
- [ ] 安装并熟练使用 DNSGen 基础功能
- [ ] 编写第一个自定义词表
- [ ] 完成练习 1 和练习 2

### 10.2 进阶阶段（第 3-4 周）

- [ ] 将 DNSGen 集成到完整子域名枚举工作流
- [ ] 掌握与 Findomain、massdns 的协同使用
- [ ] 编写自动化脚本（练习 3）
- [ ] 学习 altdns，对比两者差异

### 10.3 高级阶段（第 5-8 周）

- [ ] 研究 DNSGen 源码，理解 8 种变形技术的实现
- [ ] 贡献代码到上游（提交 PR）
- [ ] 开发自定义变形技术（如基于机器学习的智能变形）
- [ ] 在企业渗透测试工作流中推广 DNSGen 最佳实践

---

## 11 相关资源

| 资源 | 链接 |
|------|------|
| **GitHub** | [github.com/AlephNullSK/dnsgen](https://github.com/AlephNullSK/dnsgen) |
| **altdns** | [github.com/infosec-au/altdns](https://github.com/infosec-au/altdns) |
| **massdns** | [github.com/blechschmidt/massdns](https://github.com/blechschmidt/massdns) |
| **Findomain** | [github.com/Findomain/Findomain](https://github.com/Findomain/Findomain) |
| **证书透明度日志** | [crt.sh](https://crt.sh) |

---

**文档信息**

类型：专家设计 | 更新日期：2026-04-14 | 难度：⭐⭐ | 预计阅读时间：15 分钟
