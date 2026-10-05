---
title: "Ever Gauzy：从时间追踪长出来的 AGPL 全家桶，想把小公司的生意系统装进一个仓库"
date: 2026-09-25T03:30:00+08:00
lastmod: 2026-10-03
draft: false
description: "8.1k star 的开源商业管理平台 Ever Gauzy 深度解读：时间追踪/销售财务/组织管理三条业务主线，NestJS + Angular 单仓十四应用，从桌面单机到 K8s 的部署阶梯，MCP Server 接入 AI 助手，以及 Community/Small Business/Enterprise 三档许可的商用决策。"
tags: ["开源", "ERP", "CRM", "自托管", "TypeScript"]
categories: ["技术笔记"]
github_repo: "ever-co/ever-gauzy"
source_key: "gh:ever-co/ever-gauzy"
slug : ever-gauzy-open-source-erp-crm-hrm-platform
---

## 一句话说清它是什么

[Ever Gauzy](https://github.com/ever-co/ever-gauzy) 是一个开源的**商业管理平台**，官方定位一句话：ERP（企业资源计划）、CRM（客户关系管理）、HRM（人力资源管理）、ATS（招聘追踪）、PM（项目与工作管理）加员工时间追踪，全部装进一个应用。截稿时 8,161 star（2026-10-03 读数），TypeScript 约占代码量的九成，AGPL-3.0 协议，2019 年开源，至今保持日更节奏——仅 2026-10-03 一天就发了 v111.49.0 到 v111.49.4 五个 release。

它在产品体系里的重心可以从结构里看出来：时间追踪是唯一拥有专属桌面安装物的功能线（Desktop Timer、监控代理），Ever Co. 的商标清单里单独注册了 Ever Cloc™，旗下 ever-works 组织还维护着 229 star 的 awesome-time-tracking 精选清单。**时间追踪和生产力监控是全平台最扎实的部分**，ERP/CRM 是围绕它长出来的枝干。

目标用户也很明确：中小企业通常买不起（也不需要）SAP/Oracle 级别的 ERP，但又确实需要超过 Excel 能力的进销存、开票、员工管理——Gauzy 想做这个夹缝市场里"自己部署、按需取用"的那一个。

## 三条业务主线，十四个应用

### 功能先拆成三条线看

README 的功能清单有三十多项，直接读容易晕。按业务动线拆成三条主线更清楚：

| 业务主线 | 覆盖功能 | 成熟度判断 |
| --- | --- | --- |
| 时间追踪与生产力监控 | 桌面 Timer、截图与活动监控、工时表、请假与节假日审批 | 起家本事，桌面应用齐备 |
| 销售与财务 | 客户/线索、销售管道、报价与估算、开票、收支、支付 | 数据与工时打通是价值所在 |
| 组织与项目 | 员工档案与入职、候选人面试（ATS）、项目任务、OKR/KPI、目标 | 通用模型，本地化深度有限 |

除此之外还有仪表盘、报表分析、多组织、多币种、多语言、角色权限、邮件模板、Upwork/HubStaff 集成等横向能力。对全家桶要有清醒预期：**广度和深度是矛盾的**，每个模块大概率不如垂直 SaaS 专精（开票比不了专业财务软件），价值在于数据在一个库里流转——工时直接进工资单，项目成本直接进财务报表，不需要在五个系统之间导 CSV。

### 一个仓库里到底住了谁

Gauzy 是 Nx + Lerna 管理的 monorepo，`apps/` 下有 14 个应用，按用途分四组：

| 分组 | 应用 | 干什么 |
| --- | --- | --- |
| 核心平台 | `api`、`gauzy`（Web UI）、`server`、`server-api` | API 服务 + Angular 前端 + 打包成 Gauzy Server 的安装物 |
| 桌面端 | `desktop`、`desktop-timer`、`desktop-api`、`agent` | 全功能桌面版、员工记时器、桌面 API 桥、跨平台监控代理 |
| AI 接入 | `mcp`、`server-mcp`、`mcp-auth` | 独立 MCP Server 及其 OAuth 认证配套（详见下文） |
| 支撑 | `cli`、`worker`、`gauzy-e2e` | 命令行工具、后台任务、端到端测试 |

`packages/` 下另有 22 个共享包，`contracts` 放前后端共用的类型定义，`plugin`/`plugins`/`plugin-ui` 构成插件体系，`auth`、`scheduler`、`core` 各管一摊。读源码前先看 `contracts`，整个平台的实体和接口契约都从那里长出来。

## 技术架构：老派但扎实的全栈 TypeScript

技术栈取证（来自仓库 languages API 和 README）：

- **后端**：NestJS + TypeORM/MikroORM/Knex——TypeORM 处理关系映射，换来的是对 SQLite（默认，供演示）、PostgreSQL 与 MySQL（README 明言两者皆可作生产）、MariaDB、CockroachDB、MS SQL、Oracle 甚至 MongoDB 的广泛兼容，切换只需改配置
- **前端**：Angular + RxJS，基于 ngx-admin 模板体系
- **工程化**：Nx + Lerna monorepo，API、Web、桌面端、MCP、CLI 全在一个仓库
- **语言构成**：TypeScript 46.9MB + SCSS 3.3MB（languages API，2026-10-03），TypeScript 折算约 88%，说"全栈 TypeScript"名副其实

**Headless API 是关键设计**：整个平台的能力通过 REST API 暴露（Swagger 文档在 api.gauzy.co/docs），前端只是 API 的一个消费者。官方的另一款产品 Ever Teams（团队协作平台）就是直接挂在 Gauzy API 上运行的——而且 Ever Teams 用的是 React (Next.js) / React Native (Expo) 技术栈，与 Gauzy 的 Angular 前端完全不同源。这意味着你也可以把 Gauzy 当**后端业务中台**用，自己写前端。

## AI 接入：MCP Server 不是 PPT 功能

多数传统 ERP 项目对 AI 浪潮的反应是加个聊天窗口，Gauzy 的做法是把整个平台包成了一个 [MCP Server](https://github.com/ever-co/ever-gauzy/tree/develop/apps/mcp)（`@gauzy/mcp`），让 Claude Desktop、ChatGPT 这类 AI 助手直接读写 Gauzy 的项目管理、时间追踪、员工管理数据：

- **三种 transport**：Stdio（本地直连 Claude Desktop）、HTTP（JSON-RPC 2.0 over HTTP，供 Web 应用与测试）、WebSocket（实时双向）
- **企业级门禁**：HTTP/WebSocket 模式可选 OAuth 2.0 授权，会话存 Redis 支持多实例扩展
- **现成实例**：生产环境 mcp.gauzy.co，演示环境 mcpdemo.gauzy.co

配套动向还有两个：Ever Co. 新仓库 [ever-works/ever-works](https://github.com/ever-works/ever-works)（"The Workshop for AI"，一个自主研究、发布并维护整门生意的 agentic runtime，起步阶段 156 star）；Gauzy 的 PR 一律要求基于 `develop` 分支，而 AI 代码审查工具 CodeRabbit 已经挂在了仓库上。对想给内部 AI 助手接业务数据的团队，这条 MCP 路径是目前开源 ERP 里少见的现成答案。

## 部署形态：从试听到生产的完整阶梯

Gauzy 在部署上给了少见的完整选项，按评估顺序排：

| 形态 | 适合谁 | 要点 |
| --- | --- | --- |
| 在线 Demo（demo.gauzy.co） | 所有人第一站 | 数据每日重置，超管 `admin@ever.co/admin`，员工 `employee@ever.co/12345678` |
| Gauzy Server | 中小组织 | 自带 API + SQLite（可外接 PostgreSQL）+ 前端，装好即可服务多个浏览器/桌面客户端 |
| Desktop App | 个人试用/单机 | UI + API + SQLite 三合一，也能连远程 Server 或官方 API |
| Desktop Timer App | 一线员工 | 只做时间与活动追踪（截图监控），装在员工电脑上，须连 Server |
| Docker Compose | 生产（小规模） | 生产配置会连带拉起整套基础设施（见下） |
| Kubernetes | 生产（推荐） | 官方提供 Helm Charts、Terraform Modules、Pulumi 项目（AWS EKS/RDS Serverless/ECS），`.deploy/k8s` 里还有 DigitalOcean 集群的实际配置 |

不想碰命令行还有 Easypanel、RepoCloud 一键部署模板和 Hostinger 通道。桌面三件套（Server、Desktop App、Desktop Timer）都从官方 [Downloads](https://web.gauzy.co/downloads) 页取。

**生产 Compose 的分量要有预期**：`docker-compose.yml` 除了 Gauzy 自身，还会拉起 PostgreSQL、Pgweb（数据库客户端，:8081）、OpenSearch + Dashboards（搜索，:5601）、Dejavu、MinIO（S3 兼容对象存储）、Jitsu（开源 Segment 替代，数据摄取）、Redis、Cube（语义层，撑报表与 BI，:4000）、Zipkin（链路追踪）——一共约十个基础设施组件。对比之下，demo 配置只跑 API、Web、DB 三个容器。好消息是这些组件全部可裁剪：没有 Redis 就用进程内缓存，没有 OpenSearch 就用数据库内建搜索，没有 MinIO 就用本地文件系统——README 对每一路降级都明说"仅建议测试/演示环境这么跑"。

一个安全细节值得单独说：Demo 环境的默认账号只作用于演示，生产安装**必须在首次启动前设置 `DEMO_SUPER_ADMIN_PASSWORD`、`DEMO_ADMIN_PASSWORD`、`DEMO_EMPLOYEE_PASSWORD`，否则 API 拒绝写入种子数据**；`.env.compose` 里的四个 JWT/会话密钥若留空白或默认值，API 直接拒绝启动。从代码层面杜绝了"默认弱口令带上线"和"共享密钥上线"这两个经典事故。

## 生产化的安全清单（README 里少见的坦诚）

Gauzy 的 README 用了整整一节讲生产安全配置，值得逐条过一遍再上线：

- **密钥四件套**：`JWT_SECRET`、`JWT_REFRESH_TOKEN_SECRET`、`JWT_VERIFICATION_TOKEN_SECRET`、`EXPRESS_SESSION_SECRET` 必须换成强随机值（官方示例 `openssl rand -hex 64`），空白或默认值无法启动
- **种子口令三件套**：上一节的 `DEMO_*_PASSWORD`，留默认值同样拒绝 seed
- **反代信任**：`TRUST_PROXY` 设为代理跳数（单层 nginx/ingress 设 `1`）或可信网段，登录限流才按真实客户端地址计数；全程走 Cloudflare 才开 `THROTTLE_TRUST_CF_CONNECTING_IP`
- **多副本限流**：API 跑多个副本时必须 `REDIS_ENABLED=true`，否则限流桶按进程各算一份，实际限流值被副本数稀释
- **账号锁定**：同一账号连续失败 `AUTH_MAX_FAILED_ATTEMPTS` 次（默认 10）且来自至少两个不同地址，账号返回 429 并带 `Retry-After`，持续 `AUTH_LOCKOUT_SECONDS`（默认 900 秒）；单地址失败永不锁号。README 也坦承这机制的软肋——知道邮箱就能恶意锁号，可设 `AUTH_MAX_FAILED_ATTEMPTS=0` 关闭按账号锁定，只留按地址限流

能把"为什么这么配"写进 README 的项目不多，这份坦诚本身就是工程成熟度的信号。

## 上手实操

最快的本地体验路径：

```bash
git clone https://github.com/ever-co/ever-gauzy.git
cd ever-gauzy
# 用官方预构建镜像跑 Demo 形态（需 Docker Compose ≥ v2.20）
docker-compose -f docker-compose.demo.yml up
```

打开 http://localhost:4200，用 `admin@ever.co / admin`（超管）或 `employee@ever.co / 12345678`（员工，可试记时）登录。这组凭据只在 `DEMO=true` 的栈里存在，生产部署没有。想认真评估，通读 `.env.demo.compose`——数据库类型、种子数据开关都在那里。

不用 Docker 的话，手动路径是：Node.js 22.x 或 24.x + Yarn 1.22.x，`yarn bootstrap` 装依赖，`yarn start` 同时拉起 API（:3000/api）和 UI（:4200），首次启动自动种子最小数据集；`yarn seed` 可随时重建（生产禁用），`yarn seed:all` 生成海量演示数据（约 10 分钟）。

## 一单外包生意怎么流过系统

抽象功能列表不如走一遍真实业务。设想一个五人外包团队接了个网站项目：

1. **接活**：销售在 CRM 里建客户和线索，谈成后在销售管道推进到成交，建报价单
2. **建项**：项目经理建项目挂到该客户下，分配任务；同时给新同事发入职链接，员工档案进 HRM
3. **记时**：员工电脑上的 Desktop Timer 选中该项目开始工作，截图与活动监控自动上报——外包按小时计费的场景里，这就是对客户计费的凭证
4. **开票**：月末把项目工时直接生成发票发给客户，收款记入收支
5. **复盘**：老板在仪表盘看项目毛利（收入减去按员工费率算出的工时成本），数据不用二次录入

这条链上任何一环换成独立 SaaS，都要手动导一次 CSV。Gauzy 的价值不在单点最强，而在第 4 步那张发票是从第 3 步的工时表直接长出来的。

另一个正在成立的玩法：把 Claude Desktop 通过 MCP Server 接到公司 Gauzy 上，直接问"这个项目这个月烧了多少工时"——数据不出内网，不用再写一遍查询接口。

## 商用之前：许可决策树

Gauzy 用的是 AGPL 而不是 MIT/Apache，这是评估它绕不开的一道题。官方在 [LICENSES.md](https://github.com/ever-co/ever-gauzy/blob/develop/LICENSES.md) 里写得很清楚，实际是三档许可：

| 许可档 | 条件 | 费用 |
| --- | --- | --- |
| Community Edition（默认） | AGPL-3.0 全套义务：修改版用于网络服务须公开完整源码、保留版权声明、专利授权 | 免费 |
| Small Business License | 年收入不超过 100 万美元的企业，用于单一自有公司，源码可保持专有 | $99 一次性买断（官网定价页限时价） |
| Enterprise License | 年收入超 100 万美元的企业，不限自有公司数量，源码可保持专有 | $139/月（年付 $1,668） |

三条路怎么选，按顺序问自己：

1. **你能接受 AGPL 吗？** 关键条款是：修改后的版本如果用来对外提供网络服务，完整源代码必须公开。内部使用不受影响——自托管给自己公司用，改再多也不用公开。想拿它做对外 SaaS 底座又不愿开源的，才需要往下看。
2. **公司年收入低于 100 万美元？** $99 买断 Small Business，价格低于大多数垂直 SaaS 一年的订阅费。
3. **开源/非营利项目？** 按官方 wiki 的验收标准申请，可免费拿 Enterprise 许可加免费托管。

比起"联系销售谈报价"的黑箱双许可，这种明码标价的分档在 open-core 项目里算厚道的。

## 采用顺序与适用边界

**建议的评估路径**：Demo 里花一小时点功能 → 本地 Docker 起一套试数据流 → 认真跑 Desktop Timer 一周看截图监控的接受度 → 过一遍上面的安全清单 → 锁 release 版本上生产。

**反向评估法**比通读功能清单有效：列出你未来 12 个月**必须**用的三个模块（比如时间追踪+开票+员工管理），Demo 环境里只测这三个，其他当赠品。

**适合：**
- 5~50 人的远程团队/外包公司/工作室，核心诉求是工时追踪 + 开票 + 员工管理一体化；
- 愿意接受 AGPL（或花 $99 买断）的技术型团队；
- 需要 Headless 业务中台、自己掌控前端的开发者——现成的 MCP Server 让这个选项比一年前更实际。

**不适合：**
- 需要专业财务合规（如中国财税发票体系）的场景——会计模块是通用模型，本地化深度有限；
- 只想要单点功能（比如只要 CRM）的团队——上全家桶的运维成本不划算，垂直方案更合适；
- 无 TypeScript/运维能力的非技术团队——桌面版可以试，但出问题没人修。

## 结语

Ever Gauzy 是那种"雄心大于精致度"的项目：功能清单长得像 ERP 教科书目录，工程底座（Nx monorepo、多数据库兼容、Headless API、日更节奏）却搭得相当认真；时间追踪的看家本事与 ERP 的新枝干之间，成熟度落差真实存在。它不适合所有人，但对恰好落在目标区间里的小团队，这是开源世界里少有的"一套系统管完生意"的可选答案。评估时记住两件事：**先过许可决策树，再用三模块测试法**。

> 仓库：https://github.com/ever-co/ever-gauzy ｜ 官网：https://gauzy.co ｜ 文档：https://docs.gauzy.co
