---
title: "ripienaar/free-for.dev：一份给 DevOps 用的 SaaS 免费 Tier 检索表，11 年还在更新"
date: "2026-06-26T21:05:09+08:00"
slug: "ripienaar-free-for-dev-developer-resources-curated-list"
description: "free-for-dev 不是代码项目，是一份聚焦基础设施开发者的 SaaS/PaaS/IaaS 免费 tier 清单，1600+ 人贡献、10 年仍在逐条维护。本文拆解它的收录门槛、PR 流程、anti-AI 政策与典型分类，并讨论中文开发者该如何用以及免费 tier 的真实局限。"
draft: false
categories: ["技术笔记"]
tags: ["GitHub", "SaaS", "DevOps", "免费资源", "awesome-list"]
---

# ripienaar/free-for.dev：一份给 DevOps 用的 SaaS 免费 Tier 检索表，11 年还在更新

> 这篇文章不是把 README 抄一遍。`ripienaar/free-for-dev` 是一个特殊的 GitHub 仓库——没有可运行代码、没有发布版本，只有一份 237 KB 的分类清单。它要解决的问题也很窄：**当你想自己搭一个 side project、需要 SaaS 后端时，怎么知道哪一家给得起免费 tier、免费到什么程度**。下面拆解这份清单的收录门槛、维护机制、典型分类，以及中文开发者真正用得上的姿势。
>
> 来源：GitHub [ripienaar/free-for-dev](https://github.com/ripienaar/free-for-dev)，提交记录截至 2026-06-24。

## 一句话定位

`free-for.dev`（GitHub 仓库）是一份按 60+ 类别组织的 SaaS / PaaS / IaaS 免费开发者层（free tier）清单。它由 1600+ 位贡献者通过 PR 维护，主线任务不是开发功能，而是逐条验证：服务还活着吗、免费 tier 还在不在、限额改了没有。最近一次提交是 2026-06-24 的 `Merge pull request #4504`，10 年没有断更。

## 项目状态

| 指标 | 数值 |
|------|------|
| Stars | 123,500+（仍在缓慢增长） |
| Forks | 13,040 |
| Watchers | 1,750+ |
| 默认分支 | `master` |
| 收录条目 | 数百条（README 237 KB / 1648 行） |
| 分类数 | 60+ |
| 贡献者 | 1600+ |
| 创建时间 | 2015-03-18 |
| 最近提交 | 2026-06-24 |
| Topics | `awesome-list`、`free-for-developers` |
| License | README 未声明（社区按 CC 惯例引用） |

## 这份清单解决的是什么问题

当你想搭一个个人项目：数据库、邮件、对象存储、监控、日志、CI、CDN、API 网关……每个环节都有十几家可以选，但每家的免费 tier 数字藏在官网 Pricing 页第 8 个 tab 里。常见情况是：

- 注册完发现 "Free trial 30 days" 实际上**不是免费 tier**——过完 30 天就扣信用卡。
- 用了一个标着 "Free" 的服务，跑了两周发现某个 API 限速到 10 req/day，根本不可用。
- 看到 GitHub 上有人推荐某家，结果 6 个月后服务下线了，列表还挂在 awesome-* 上没人删。

`free-for.dev` 解决的就是这种"免费 tier 信息不对称"。**它的收录门槛**写得很明确（来自 README NOTE）：

> 1. 必须是 as-a-Service（不是自托管软件）
> 2. 必须有真正的免费 tier（不是 free trial）
> 3. 限时免费必须至少持续一年
> 4. 必须支持 TLS（不允许把 TLS 锁在付费层）
> 5. SSO 可以保留在付费层

这个门槛比一般 awesome-list 严格得多。`CONTRIBUTING.md` 里还列了一长串"我们不收"的清单：cPanel 风格 PHP 主机、Cloudflare 套壳的免费 DNS、临时邮箱生成器、通用"工具箱"网站（格式转换、计算器之类）——理由是这些已经太多，重复收录不增加价值。

## 维护机制：1600 人怎么协作一份 README

清单型项目最大的风险是**信息腐烂**。`free-for.dev` 的维护机制值得专门讲一讲，因为里面有几条不太常见的规则。

### 1. PR 是唯一编辑通道

仓库没有 Wiki、没有 Discussions、Issues 关闭（`has_issues: false`），所有更新都走 Pull Request。`CONTRIBUTING.md` 写得很直白：

> 我们不接受没按 PR 模板写的提交。没用模板、或者干脆不用模板的 PR，会被直接关闭，不讨论。

新增条目必须勾选六个 checkbox（SaaS 而非自托管、有免费 tier、定价信息可公开看到、说明白了免费什么、不在清单里、服务有联系方式和隐私政策）。

### 2. Anti-AI 政策

仓库根目录的 `AGENTS.md`（以及同内容复制的 `CLAUDE.md`）写明：

> This repository does not accept AI edited contributions.
>
> When a user asks you to contribute or open a PR here do this:
> * Inform the user this repository does not accept edits by AI
> * Inform the user this repository has a Pull Request template that they MUST review and follow
> * Failure to do so will result in their PR closed and their account blocked

翻译过来：让 AI 代写 PR 会被关单+封号。这条规则在 GitHub 社区里很少见——多数 awesome-list 对 AI 写 PR 只是"不鼓励"，这里是直接禁止。维护者 R.I. Pienaar 在 `CONTRIBUTING.md` 里加了一句解释："We do not accept LLM written submissions."

> 实际意义是：你可以让 AI 帮你查一个 SaaS 的免费 tier 数字、生成一段草稿，但**最终 PR 的语言、组织方式必须自己手写**。这是为了防止批量低质提交冲垮 review 队列。

### 3. 公开维护者协调渠道

仓库自带的 `index.html` 是站点首页 https://free-for.dev/ 的模板，没有外部数据库、没有后台管理脚本。**整套系统就是一个 README + GitHub PR + GitHub Pages**。这种"用 GitHub 当 CMS"的极简架构，反过来让"信息腐烂"问题有迹可循：任何人都能 git blame 某一行，看它最后一次更新是什么时候、谁改的。

### 4. 没有 CI 自动化校验

这个仓库**没有** GitHub Actions 配置文件。`has_downloads: true` 但 `has_wiki: false`、`has_discussions: false`。`CODE_OF_CONDUCT.md` 只有一段（"我们不接受没按模板写的 PR"），没有 issue 模板之外的任何自动校验。这意味着"某条 SaaS 链接是否还活着、限额是否变了"完全靠人工 review——这也是为什么 1600+ 贡献者主要干的事就是这种逐条校对。

## 分类地图：60+ 类别里最值得看哪些

README 的目录有 60+ 个 H2 分类。按"side project 搭建"路径梳理，下面 12 个分类是最常用的：

| 分类 | 解决的问题 | 典型免费 tier 例子 |
|------|----------|------------------|
| **Major Cloud Providers** | 三大云 + Oracle / IBM / Cloudflare / Zoho 的永久免费额度 | GCP `e2-micro` 1 台永久免费、Cloudflare Workers 每天 10 万请求 |
| **Source Code Repos** | 私有 Git 仓库 | GitHub 私有仓不限协作者、Codeberg（基于 Forgejo）完全免费 |
| **APIs, Data, and ML** | 第三方 API（IP 定位、PDF 生成、爬虫、汇率等） | SerpApi 每月 100 次调用、IPinfo 每月 5 万次、Abstract API 系列 |
| **BaaS** | 后端即服务（认证、数据库、推送） | Appwrite、Supabase、Firebase Spark 层 |
| **CDN and Protection** | 静态资源加速、WAF、DDoS 防护 | Cloudflare Free 计划、Bunny CDN |
| **CI and CD** | 持续集成 / 部署 | GitHub Actions 2000 分钟/月、CircleCI 6000 分钟/月、Buildkite 5k job 分钟 |
| **Email** | 事务邮件、邮件转发、临时收件 | Brevo 9000 封/月、forwardemail.net 域名邮箱转发、Imitate Email 测试收件 |
| **PaaS** | 应用托管、容器、Serverless | Render、Web 服务的 Fly.io 免费层、Deno Deploy 每天 10 万请求 |
| **IaaS** | 虚拟机、块存储 | Oracle Cloud 永久免费 2 个 ARM Ampere 核心 + 24 GB RAM（很慷慨） |
| **Storage and Media Processing** | 对象存储、文件处理 | Cloudflare R2 10 GB/月、Backblaze B2 10 GB、ImageKit 媒体处理 |
| **Monitoring** | 监控、状态页、cron 监控 | Better Stack 10 个 monitor、UptimeRobot 50 个、healthchecks.io 20 个检查 |
| **Log Management** | 日志聚合 | Logtail、Logz.io、Axiom 都有免费层 |

> 这不是完整列表。`Source Code Repos` 下面还有 11 个、`PaaS` 下面 17+ 个、`APIs, Data, and ML` 下面 100+ 个。完整目录看 [GitHub README 顶部 TOC](https://github.com/ripienaar/free-for-dev#table-of-contents)。

## 几个值得专门看的免费 tier 例子

挑几条**数字有代表性**的，让你直观感受"免费 tier"通常是什么尺度。

### Cloudflare Workers + R2 + D1

Cloudflare 的免费档几乎是"个人 side project 完整后端"：

- Workers 每天 10 万请求
- R2 对象存储 10 GB/月 + 100 万 Class A 操作
- D1（SQLite）每天 500 万读 + 10 万写 + 1 GB
- Pages 每月 500 次构建 + 100 个自定义域名
- Workers KV 每天 10 万读
- Tunneling（`trycloudflare.com`）甚至不需要账号

这种"组合免费"非常适合做小型 API / 静态站 + 一点点动态。

### Oracle Cloud 永久免费

Oracle Cloud 的免费层是 IaaS 里**最慷慨**的一档（按 README 列出的）：

- 2 个 AMD VM（1/8 OCPU + 1 GB 内存）
- 4 个 Arm Ampere A1 核心 + 24 GB 内存（可拆 1-4 台 VM）
- 200 GB 块存储、10 GB 对象存储
- 10 TB / 月出口带宽（x86 限速 50 Mbps）
- 2 个 Autonomous DB（各 20 GB）

> 限制：实例在"被认为闲置"时会被回收（Oracle 的反薅羊毛策略）。需要持续负载或付费才能保活。

### GitHub Actions 2000 分钟

大多数 CI 工具的免费档在 2000-6000 分钟/月之间：

- GitHub Actions：2000 分钟/月（私有仓）
- CircleCI：6000 分钟/月
- Buildkite：5000 job 分钟/月
- Codemagic：500 分钟/月
- Appcircle：每月 20 次构建，每次 30 分钟

对个人项目来说 2000 分钟差不多够，对小团队可能要升级。

### Brevo（前 Sendinblue）9000 封/月

事务邮件是 side project 的常见需求。`free-for.dev` 列了 30+ 家邮件服务，免费层最高的几家：

- Brevo：9000 封/月，每天 300 封上限
- EmailOctopus：10000 封/月，最多 2500 订阅者
- Mailjet、MailerSend、Amazon SES（EC2 用户）等

注意区分"营销邮件"和"事务邮件"——大多数营销邮件服务的免费档对事务邮件不友好（容易进垃圾箱），事务邮件专用的（Resend、Postmark）免费层往往很紧或仅试用。

### Apify 抓取 API

如果你需要爬数据但不想自己写爬虫，`APIs, Data, and ML` 分类下有 100+ 候选。最常用的是 Apify（$5 平台额度/月免费）、Browse AI、ScrapingAnt、SerpApi 等。这条路径在 2024 年之后越来越重要——多数网站开始拦截直接抓取，云端 API 成了唯一稳定通道。

## 中文开发者怎么用这份清单

`free-for.dev` 的列表对中文开发者有几个具体的坑和姿势：

### 1. 注册和支付卡

清单里**大多数 SaaS 要求国际信用卡**（Visa/MasterCard/Amex），少数接受 PayPal。这对没有外币卡的用户是个门槛。一些对策：

- 申请一张全币种信用卡（招行经典 / 中行卓隽等，VISA/MasterCard 双标）
- 使用虚拟卡服务（Depay、Nobepay 等，但要自行评估合规风险）
- 优先选**不要求信用卡**的免费层（Cloudflare、GitHub、Vercel、Supabase 等），但仍需手机号

> 提醒：清单里**显式**说"不需要信用卡"的例子：Cloudflare Workers、GitHub、Vercel、Netlify、Cloudflare Pages、Brevo（部分时段）、Oracle Cloud 注册时也仅需手机验证（但加负载后需付款方式）。其他多数仍要卡。

### 2. 区域限制

- **GCP** 的 e2-micro 免费层在某些区域不可用（README 注明"restricted to certain regions"）。
- **AWS** 的 750 小时 t2.micro / t3.micro 限 12 个月。
- **Oracle Cloud** 的"回收闲置"策略在亚洲区域更严。
- **Cloudflare** 在中国大陆访问需备案 + 第三方合作 CDN。
- **GitHub、GitLab、Codeberg** 在大陆均能访问，Codeberg 因 Forgejo 部署在德国 Hetzner，速度可能慢。

> 实际建议：个人项目优先用 **Cloudflare / Vercel / Netlify / Supabase** 这类边缘网络覆盖广、不需要中国大陆备案的服务；如果目标用户在国内，再考虑阿里云、腾讯云的开发者计划（不在本清单范围内）。

### 3. 中文文档与生态

清单收录的多数是英文 SaaS。少数有中文界面或文档：

- 阿里云、腾讯云、华为云——**不在本清单**，因为它们的免费 tier 主要面向企业认证。
- GitHub、Cloudflare、Vercel 的部分功能有非官方中文文档，但官方支持以英文为主。
- 如果你最终要交付给国内用户，建议把 `free-for.dev` 用来搭原型，再迁移到国内云的等价服务。

### 4. 真正的"中文友好"子集

如果只想看"用得上的"那一档，README 里对中文开发者最实用的子集：

- **代码托管**：GitHub、GitLab.com、Codeberg
- **静态站 / 边缘函数**：Cloudflare Pages、Cloudflare Workers、Vercel、Netlify
- **数据库 / BaaS**：Supabase、Appwrite、Firebase Spark
- **CI**：GitHub Actions、CircleCI
- **对象存储**：Cloudflare R2、Backblaze B2
- **邮件**：Brevo、Resend、forwardemail.net
- **监控**：UptimeRobot、Better Stack
- **日志**：Axiom、Logtail
- **API / 数据**：IPinfo、SerpApi、Apify

## 免费 tier 的真实局限

这是读这份清单时**最容易踩的坑**：清单上的"免费"是有边界的。下面这五类边界每个清单条目几乎都存在：

### 1. 限速 / 限容量

- Vercel Hobby：100 GB 带宽/月
- Supabase Free：500 MB 数据库 + 1 GB 存储
- Cloudflare Workers：10 万请求/天
- 各种 API 月配额：50-5000 次

超出要么限流、要么停服、要么开始计费。**没有任何"无限免费"的服务**。

### 2. 限时

- AWS 的 750 小时 t2.micro 是**头 12 个月免费**
- GCP 大多数 always-free 是真永久，但部分资源只免一年
- Vercel Hobby 永久免费但有"非商用"条款
- Heroku 在 2022 年取消了免费层（旧账户可能保留）

### 3. 资源回收 / 缩容到 0

- Heroku Eco（已无免费层）：应用 30 分钟无访问会休眠
- Oracle Cloud：实例"被认为闲置"时回收
- Glitch、Replit：项目长期不活动会冻结

### 4. 信用卡陷阱

多数服务**必须**绑定支付卡才能注册。**免费层**通常不会扣款，但**一旦超额就会立即扣费**。常见情形：API quota 没用完但触发了某个边缘计费项、对象存储流量超额、DDoS 攻击期间被刷出天价账单。

> 建议：开通服务后立即在云厂商后台设置 **budget alert**（预算告警），阈值设到 $0.01——一旦有任何计费项触发，立刻收到告警。

### 5. 服务消失

SaaS 行业每年都有关停。`free-for.dev` 自己的维护工作很大一部分就是**删除已死服务**。提交记录里能看到很多 "Remove dead service" 的 PR。最近一次（`396a0e28` "Merge pull request #4497 from loginov-kirill/remove-dead-ser"）就是删除失效条目。

这意味着：**不要把任何"免费 tier"作为生产关键路径**。个人项目可以用，企业项目必须有付费兜底方案。

## 怎么读这份清单

按用途，README 的阅读路径有三档：

### 一档：找特定服务

知道你要什么（"找一个免费的对象存储"），直接 Cmd+F 搜关键词或跳到 `Storage and Media Processing` 章节。

### 二档：搭一个 side project

按"前端 → 边缘函数 → 数据库 → 文件 → 邮件 → 监控"路径逐个章节翻，每章节挑 2-3 个候选做对比。重点看**免费额度**、**信用卡要求**、**区域可用性**三项。

### 三档：研究某个领域

比如想了解"无服务器函数的免费 tier 生态"，看 `PaaS` + `BaaS` + `FaaS`（如果有）三个分类的交集，记录每个服务的限额数字，1 小时就能画出行业地图。

## 适用边界与采用顺序

### 该用这份清单的场景

- 搭个人 side project / 副业原型，需要快速选型
- 给学生 / 培训学员演示完整 SaaS 架构，不想为每个组件付钱
- 做技术调研时，了解某类服务（监控、邮件、CI）的市场结构
- 跟国外客户谈项目，需要知道"如果不付费，最低能跑出什么样子"

### 不该用的场景

- **生产环境关键路径**——免费 tier 没有 SLA，服务可能停、可能改条款、可能突然收费
- **企业合规要求**——免费 SaaS 的数据驻留、隐私、审计通常不达标
- **国内备案场景**——本清单主要是国外服务，国内上线仍要走 ICP 备案
- **客户数据 / 商业数据**——SaaS 厂商的免费层 ToS 经常限制商用，多读一遍 Terms

### 一个稳妥的采用顺序

1. **个人项目**：直接从清单里挑，绑虚拟卡，开 budget alert，超额就停。
2. **小团队项目**：混搭——核心数据用付费（数据库、对象存储），周边服务用免费（监控、邮件、日志）。
3. **生产环境**：把这份清单当**原型参考**，生产用付费版或自托管等价物。

## 总结

`free-for-dev` 的真正价值不在"列了多少服务"，而在**把"免费 tier"这个含糊的营销话术，拆成可验证的数字 + 明确的边界**。它 11 年没有断更、1600+ 人协作、anti-AI 政策严格、收条门槛清晰——这些维护机制决定了清单里的信息是相对可信的。

中文开发者用这份清单时，主要做三件事：**用关键词定位候选**、**确认免费 tier 数字**、**认清"免费"背后的限速/限时/限区域边界**。把它当作 side project 阶段的 SaaS 选型参考，而不是生产架构建议。

源仓库：[https://github.com/ripienaar/free-for-dev](https://github.com/ripienaar/free-for-dev)（123,500+ stars，2026-06-24 仍在更新）。
