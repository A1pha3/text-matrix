---
title: "Treg：把 3000 个 API 装进一个 URL 的「工具版 OpenRouter」"
date: 2026-09-24T03:23:16+08:00
draft: false
categories: ["技术笔记"]
tags: ["ai", "agent", "api", "mcp", "tools", "registry", "proxy"]
description: "superdesigndev/treg 自称「agent 工具的 OpenRouter」：一个 base URL + 一个 token，就能调用 60+ 供应商的 3000+ 端点，按次计费从一美分起，还能把团队自己的 API key、CLI 和 skill 注册进去共享——密钥永远不落到调用方手里。本文拆解它的架构设计与真实用法。"
github_repo: "superdesigndev/treg"
source_key: "gh:superdesigndev/treg"
slug : superdesigndev-treg-tool-registry-openrouter-for-tools
---

# Treg：把 3000 个 API 装进一个 URL 的「工具版 OpenRouter」

> 仓库：[superdesigndev/treg](https://github.com/superdesigndev/treg)（Python，2615★，2026-07 开源，持续活跃更新中）｜托管实例：[treg.to](https://treg.to)

## 一句话说清楚它是干什么的

过去两年，AI 编程助手（Claude Code、Cursor、各类 Agent 框架）已经能写代码、跑命令、查资料。但真让它干活时，你会撞上一堵墙：**干活要用的工具——SEO 数据、企业信息查询、社媒发布、图片生成——全都锁在各自的订阅墙后面**。

想查一个域名的外链数据？Semrush 每月 139 美元。查一家公司的融资信息？Crunchbase 每月 99 美元。找一个人的工作邮箱？Hunter 要注册。更过分的是不少 API 根本不对公众开放——邀请制、合作方专属、应用审核制。

一个 AI Agent 可能一个月只需要调一次某个 API。为了这一次调用去开一个 139 美元的月付账号？显然荒谬。

**Treg 的答案：把这些 API 账号集中到一个注册中心里，按次计费，一次调用一美分起。** Agent 拿到一个 base URL 和一个 token，就能搜索"我想做什么"，然后直接调用——不需要知道是哪家供应商，也不需要在供应商那里注册任何账号。

它的自我定位很直白：**"OpenRouter, but for agent tools instead of models."**——OpenRouter 让你用一个 API 调用几十家大模型，Treg 想让你用一个 API 调用几千个数据与操作端点。

## 核心设计：中继，不代理

理解 Treg 的关键在它 README 里加粗的一句话：

> **the proxy relays, never models the upstream, and injects auth server-side**

翻译过来：代理层只做"忠实转发"，绝不改写上游请求的内容；认证凭据只在服务端注入，调用方从头到尾碰不到密钥。

这两点决定了它和普通"API 网关"的区别。

### 为什么"只转发不改写"很重要

如果代理层对上游请求做语义级改写（比如把请求参数翻译成供应商的方言），那上游 API 一改版，代理就得跟着改，用户代码也会莫名其妙地坏掉。Treg 的做法是：你构造**真实的上游请求**，前面加个前缀就行：

```text
真实请求：   GET https://api.intercom.io/conversations?per_page=5
经 treg：   GET https://treg.to/call/https://api.intercom.io/conversations?per_page=5
             header: X-Treg-Token: <你的 token>
```

Treg 按目标 host 解析出该用哪个工具、注入哪个凭据，其余原样转发。你的 token 在到达上游之前就被剥掉了。上游 API 改版？你改自己的请求就行，和直接调用没有任何区别。

### 为什么"服务端注入凭据"很重要

团队协作里最经典的痛点：付费 API 的 key 只敢给一个人，其他人要用就得找他代查，或者把 key 贴进聊天软件。Treg 把凭据存在服务端（加密），团队成员的 Agent 各自持有自己的 token，调用时 Treg 替他们注入凭据——**key 永远不离开服务器**。

## 两类工具，一个 token

Treg 注册中心里的"工具"分两大类。

### 1. 目录（Catalog）：3000+ 端点，60+ 供应商

这是 Treg 自己维护的公共工具目录，按"能干什么"分组：

- 关键词与排名追踪、外链与权重（SEO 类）
- 社媒发布、趋势发现
- 人物与企业信息增强（enrichment）
- 广告管理与素材
- 网页抓取、图片与视频生成

用 CLI 找工具的方式也很"Agent 友好"——按任务搜，不按供应商搜：

```bash
treg catalog search "find a work email"   # 按"想做的事"搜
treg catalog get hunter.people.email.find # 查参数、价格、示例响应
treg call hunter.people.email.find --query domain=reddit.com --query full_name="Alexis Ohanian"
treg balance                               # 刚才那笔花了多少钱
```

计费上有个透明的细节：**没有公开定价的端点会被直接拒绝，而不是"免费"放行**，系统会提示你接自己的 key。多个供应商能干同一件事时，搜索结果会并排显示各自的价格，选择权在你——Treg 不会默默帮你挑供应商或做故障切换。这在"按次计费"的模式里是防止隐性成本的关键设计。

### 2. 你自己的工具：key、CLI、skill 全都能注册

第二类是团队私有资产，分三种形态：

**端点（Endpoint）**——一个上游 URL + 绑定的密钥。支持多凭据绑定，比如 Google Ads 那种"OAuth bearer + developer-token 请求头"的双重认证，一次请求可以同时注入两个凭据。

**CLI**——不只是 HTTP API，`stripe`、`gh`、`vercel` 这类厂商命令行工具也能注册。`treg run` 会在执行时注入组织凭据，你既不用自己装 key 也不用登录：

```bash
treg run stripe -- get /v1/balance    # 在你本机跑，凭据注入
treg run gh -- pr list
```

更彻底的是 `--server` 模式：CLI 直接在注册中心服务器上跑，输出流式传回——密钥连你本机都不经过。想整个会话都免登录？`treg shell start` 开一个子 shell，里面 `stripe`、`gh` 等命令全部自动注入凭据，`exit` 退出恢复原状。

**Skill**——一个完整的能力包：`SKILL.md` 配方 + 它需要的密钥 + 它要用的工具，三者打包注册。团队成员 `treg skill install seo-blog-writer` 一条命令拉下来就能用，skill 里的 API 调用自动走 Treg、自动带凭据——skill 文件本身不含任何密钥。

最省心的是零配置路径：在项目目录跑 `treg scan`（只读预览）和 `treg upload`（实际注册），它会自动扫描 `.env` 里的 key（能对上约 80 家已知供应商）、每个 skill 子目录、已安装的 CLI 工具，全部识别注册。

## 凭据阶梯：一次调用到底用谁的 key

目录调用按什么顺序找凭据？README 给了清晰的四层阶梯：

1. 团队为该供应商注册过自己的工具 → 用团队的 key；
2. 团队存过该供应商的密钥 → 通过虚拟工具注入；
3. 都没有，且该端点有已验证的公共通道 → **无需供应商 key，免费**；
4. 否则 → 用 **Treg 自己的 key**，从团队预付余额里按次扣费。

第 1 条优先级最高意味着：**你自己付费的 key 永远优先于 Treg 的**——接上已有账号后，这些调用不再消耗余额，避免了"重复付费"。余额耗尽时返回的不是一段人话错误，而是结构化的 HTTP 402，带上 `balance_micro`、`estimated_cost_micro` 和充值链接——Agent 不用读散文就能自己决策下一步。

## 接入 Agent 的三条路

Treg 对当前主流 Agent 生态的覆盖相当完整：

1. **Claude Code 插件**：`/plugin marketplace add superdesigndev/treg` 后安装，零配置零 token，首次运行时 skill 会引导走完 CLI 安装、登录、MCP 接入。
2. **通用 skill 分发**：`npx skills add superdesigndev/treg -s treg`（注意 `-s` 参数，不带的话会把仓库内部开发 skill 也拉下来）。
3. **MCP 端点**：`https://treg.to/mcp/` 覆盖目录端点、团队工具和导入的 skill；Claude Connectors 专用的 `/mcp/v2/` 只暴露精选端点，并把读/写调用分开，让 Claude 获得准确的安全信号。

## 权限模型与团队边界

一个账号最多建 10 个团队（加入别人的团队不占额度）。所有资源（密钥、工具、skill）都归属于 **org**，token 等价于一条 `(user, org)` 成员关系。角色分 owner / admin / member / viewer 四级，admin 以上可以按成员粒度控制工具访问权限（`treg org access <member> --tools a,b`）。

这个模型解决的是"团队 API 资产"的治理问题：谁能用哪个工具、每次调用花了谁的钱（`treg calls` / `treg runs` 审计日志），都有明确答案。

## 冷静看：几个值得留意的地方

**成本可控但不一定最便宜。** 按次计费解决了"为一次调用开月付账号"的问题，但如果你的用量大到一定规模，直接找供应商谈年付大概率更划算。Treg 的甜点区是低频、多供应商、Agent 自动化的场景。

**信任是绕不开的前提。** 把团队的 API key 交给一个注册中心（哪怕自托管），本质上是在它的安全边界上做了一次集中下注。好消息是代码开源、可以 self-host；坏消息是 license 标注为 "Other"（非标准开源协议），商用集成前需要自己读一遍条款。

**它选择的赛道很拥挤。** MCP 生态里工具聚合方案层出不穷，各大 Agent 框架也在内建工具市场。Treg 的差异化筹码是"目录规模 + 按次计费 + 凭据不出服务器"三件套，能不能守住，取决于供应商覆盖的扩张速度。

## 什么人该试一试

- **跑自动化 Agent 的个人开发者**：Agent 需要偶尔碰十几个不同供应商的 API，挨个注册不现实。
- **小团队的技术负责人**：想统一管理团队的 API 凭据、让每个人的 Agent 都能安全调用，而不是在群里传 key。
- **构建 Agent 产品的人**：Treg 的"凭据阶梯"和"402 结构化计费响应"是很好的设计参考——就算不用它，这两个模式也值得抄。

快速上手只要三步：

```bash
curl -fsSL https://treg.to/install.sh | sh   # 装 CLI
treg login                                     # GitHub 登录
treg catalog search "backlinks for a domain"   # 按任务搜工具，直接调用
```

新注册的合格团队有一次性的 1 美元免费额度，够把目录里感兴趣的工具都摸一遍。

## 结语

Treg 抓住的是一个真实且越来越尖锐的矛盾：**Agent 的能力边界在狂飙，但工具的获取方式还停留在"人类逐个注册账号"的时代**。它给出的答案——统一注册中心 + 服务端凭据注入 + 按次计费——未必是最终形态，但"Ask for the task, not the tool"（按任务要工具，而不是按供应商）这个方向，大概率就是 Agent 工具生态的演化方向。

---

**项目信息**

- 仓库：<https://github.com/superdesigndev/treg>
- 托管服务：<https://treg.to>
- 语言：Python ｜ Stars：2600+（2026-09 时点）
- 许可证：Other（非标准协议，商用前请阅读原文）
