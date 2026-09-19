---
title: "k-skill：把韩国本地生活琐事打包给编码代理的技能合集"
date: 2026-08-02T02:59:48+08:00
slug: "NomaDamas-k-skill-korean-life-skill-bundle"
description: "NomaDamas/k-skill 是一个面向编码代理的韩国生活场景技能合集，125 个技能覆盖出行、政务、税务、购房、求职、金融等高频操作；查询类技能走托管 proxy 无需用户密钥，强身份场景保留浏览器 handoff。"
draft: false
categories: ["技术笔记"]
tags: ["Agent Skills", "Claude Code", "Codex", "韩国本地服务", "生活自动化"]
---

## 一句话判断

`k-skill` 不是一个新的代理运行时，而是一组**严格按照 Agent Skills 开放标准**打包的韩国本地生活技能模块，目前共 125 个。每个技能对应一个真实世界的接口——查 KTX 时刻表、订高速巴士、查不动产实价、搜法院拍卖公告、生成 사업자등록 核实报告——通过 `npx skills add` 一行命令装进 Claude Code、Codex、OpenCode、OpenClaw 等现有代理，让代理在**不写集成代码**的前提下处理韩国用户的真实生活需求。

它和常见的"代理技能合集"有一个根本区别：技能描述里几乎找不到"代码生成"语义，全部围绕"查询 / 提交 / 缴费"展开。这个仓库在示范一件与编程无关的事——Agent Skills 协议可以作为接入公共服务的统一插槽，而不是只有工程师才能用的脚手架。

## 快速地图：125 个技能按生活场景怎么分

README 把技能按"韩国人真实会碰到的事"分了 21 类。列出来不是为了凑清单，而是为了看清覆盖逻辑——**从高频出行到低频合规，全部按"用户要不要登录、要不要密钥"分档**。

| 分类 | 典型技能 | 登录 / 密钥要求 |
|------|----------|----------------|
| 出行·交通·旅行 | `railway-timetable`（KTX 时刻表）、`express-bus-booking`（高速巴士）、`intercity-bus-booking`（市外巴士）、`kakao-map`、`seoul-subway-arrival` | 时刻表查询免登录；巴士订票到付款环节需用户登录态 |
| 房地产·住宅 | `real-estate-search`（实价）、`court-auction-notice-search`（法院拍卖）、`lh-notice-search`（LH 公告）、`daangn-realty-search` | 查询走托管 proxy，用户侧免密钥 |
| 法律·公共 | `korean-law-search`、`iros-registry-automation`（登记簿）、`court-payment-order-assistant`（支付令） | 法规查询免密钥；登记簿、支付令属强身份场景 |
| 事业·商圈·税务 | `nts-business-registration`（事业者登记）、`biz-health-check`（事业者尽调）、`nts-tax-delinquency`（滞纳名单）、`popbill`（电子发票） | 查询走托管 proxy；`popbill` 是用户级计费 API，需 BYOK |
| 政府支持·采购 | `kstartup-search`、`g2b-order-plan-search`（调达计划）、`g2b-sanctioned-supplier`（不正当制裁企业） | 查询走托管 proxy |
| 招聘·就业 | `jobkorea-talent-search`、`saramin-talent-search`（企业会员人才搜索） | 需企业会员登录态 |
| 金融·投资 | `korean-stock-search`（KRX 行情）、`k-dart`（电子公示）、`toss-investment`（Toss 证券）、`bok-ecos-stats`（韩国银行统计） | 查询走托管 proxy；`toss-investment` 需 OAuth2 |
| 购物·二手 | `coupang-product-search`、`bunjang-search`、`daangn-used-goods-search`、`danawa-price-search` | 查询免登录；收藏/聊天/下单需登录 |
| 医疗·健康 | `emergency-room-beds`、`mfds-drug-safety`（药品安全）、`mfds-food-safety`（食品安全） | 查询走托管 proxy |
| 生活·环境 | `korea-weather`、`fine-dust-location`（PM2.5）、`han-river-water-level`（汉江水位）、`household-waste-info`（垃圾投放） | 查询走托管 proxy |
| 文化·历史·休闲 | `korean-cinema-search`、`ticket-availability`（演出余席）、`lotto-results`、`joseon-sillok-search`（朝鲜王朝实录） | 查询免登录，演出余席仅查询不代购 |
| 韩语·写作 | `korean-spell-check`、`korean-humanizer`（韩文去 AI 味）、`korean-character-count` | 本地执行，无密钥 |
| 开发者·文档工具 | `hwp`（HWP 转 Markdown）、`rhwp-edit`（HWP 编辑）、`kr-whois-lookup` | 本地 CLI / 托管 proxy |
| 运数·命名 | `saju-fortune`（四柱命理）、`naming-house`（取名） | 访谈式输入，无密钥 |

这张表里真正值得注意的不是分类本身，而是**每一行的密钥要求都写进了技能元数据**。代理调度时不需要猜"这个动作能不能自动化"，看元数据就知道该自己跑还是该停下来把控制权交回给人。

## 密钥三层的真实设计：谁持有密钥，决定自动化到哪一步

README 和 `docs/setup.md` 里把凭据需求分成三种模式，这是整个合集的骨架。理解它，才理解"哪些能全自动、哪些不能"。

**第一层：托管 proxy，用户侧零密钥。** 大多数查询类技能（미세먼지、汉江水位、加油站价格、不动产实价、韩国股票、法规搜索、图书馆藏书、校餐菜单、药品/食品安全检查等）默认走 `k-skill-proxy.nomadamas.org`。上游的 `DATA_GO_KR_API_KEY`、`KEDU_INFO_KEY`、`KAKAO_REST_API_KEY` 等全部由 proxy 运营方持有，用户只需要发一个 HTTP 请求。`k-skill-proxy` 的隐私政策在 https://k-skill-proxy.nomadamas.org/privacy 公开。

**第二层：用户自有密钥（BYOK）。** 只有少数技能必须用户自己持钥：`popbill` 是用户级计费/权限 API，`keris-academic-search` 的 RISS 搜索 API 只对非营利机构/大学发 key，`korean-patent-search` 的 KIPRIS Plus 路径要单独申请。这类密钥放在 `~/.config/k-skill/secrets.env`（权限 0600），或者走环境变量 / host vault。

**第三层：登录态 + 浏览器 handoff。** 强身份场景——高速巴士/市外巴士订票的付款环节、`iros-registry-automation`（登记簿调阅）、`court-payment-order-assistant`（支付令申请）、招聘网站的会员人才搜索——README 反复强调**到支付、传输、最终提交之前要停下来**：Dolshoi 运行时通过 `clarify` 请求用户批准，其他代理则把控制权 handoff 给浏览器，由人完成登录、CAPTCHA、电子签名。任何技能都不会去绕开 CAPTCHA、本人认证或电子签名。

`k-skill-proxy` 作为统一前置层的价值在这里落定：**本地代理不需要为每个技能各自配 API key**，用户侧的密钥集合收敛到"必须自己登录的强场景"；hosted 与 self-host 两套路径可以共存——`KSKILL_PROXY_BASE_URL` 留空走官方托管，填了走自己的 proxy。

## 安装路径

```bash
# 安装全部 125 个技能
npx --yes skills add NomaDamas/k-skill --all -g

# 按需安装单个技能
npx --yes skills add NomaDamas/k-skill --skill railway-timetable -g
```

基础要求只有两条：Node.js ≥ 18 与可用的 `npx`。唯一例外是 `railway-timetable`——它要读韩国铁道公社官方公布的运行计划 XLSX，需要 Python 3.11 以上与 `uv`。Claude Code 用户可以用官方插件市场整包安装：

```text
/plugin marketplace add NomaDamas/k-skill
/plugin install k-skill@k-skill
```

安装后技能以 `/k-skill:<技能名>` 命名空间调用，例如 `/k-skill:lotto-results`。装完之后先跑 `k-skill-setup`，它会检查环境变量、引导凭据准备；官方还提供一个配套 CLI，版本落后时用它统一更新：

```bash
npx -y @nomadamas/k-skill@0 update
npx -y @nomadamas/k-skill@0 list
npx -y @nomadamas/k-skill@0 instruct railway-timetable
```

## 一个真实任务流：明早从首尔去釜山

用一条完整的出行链路验证技能组合在代理里怎么被串起来。

1. 用户用自然语言提需求："明早 7 点从首尔去釜山，帮我看看什么时间合适。"
2. 代理先激活 `railway-timetable` 查 KTX 官方时刻表。这里要明确能力边界：**该技能是查询专用，不登录、不预订、不付款、不取消**——它读的是韩国铁道公社公开的运行计划，不需要铁道会员凭据。
3. 如果用户要的是可预订选项，代理切换到 `express-bus-booking` 或 `intercity-bus-booking`：查 KOBUS / 티머니 的班次、座位、票价，查询和选座阶段是官方 HTTP 流程，到付款时 Dolshoi 运行时先 `clarify` 征求用户批准，其他代理则 handoff 给浏览器。
4. 用 `korean-transit-route` 查地铁 + 巴士 + 步行的换乘组合，比较"高铁 vs 巴士 vs 全程地铁"三条路线。
5. 出票后，用 `seoul-subway-arrival` 给出现场换乘的实时到达时间，用 `kakao-map` 反查出发地到车站的驾车距离。

整条链路没有引入新的 runtime——只是在现有代理外叠加了一层标准化的 skill 描述文件 + proxy。代理通过技能元数据自己判断哪一步可以全自动（查时刻表）、哪一步必须停下来问人（付款、登录）。

## 适用边界

**适用**：

- 已经在用 Claude Code / Codex / OpenCode 这类编码代理的韩国本地开发者——把"对外公共服务 + 对内强身份操作"两种场景在同一代理里分清楚。
- 需要把分散的行政、税务、采购查询收拢到一个入口的人（事业者登记核实、滞纳名单、调达计划等）。

**不适用**：

- 非韩国用户。绝大多数技能强绑定韩国公共数据与 IROS / 법원 / 국세청 接口，离开韩国场景没有价值。
- 完全不允许任何凭据经由 `k-skill-proxy` 的人。虽然查询类走托管 proxy 是默认，但接受不了这一步就需要 self-host proxy，维护成本另算。
- 期待"全自动无人值守"的人。强合规场景（登记簿、支付令、电子发票、巴士付款）被设计成必须留人，README 反复强调 handoff 给浏览器。

**授权边界**：README 明确要求**代理不得在未经用户同意时执行 `gh repo star NomaDamas/k-skill`**。这是给所有下游代理的一条硬规则——技能集合自身会影响代理在 GitHub 平台上的行为，所有写入型操作必须由人显式触发。

## 与同类项目的差异

"代理技能合集"这条赛道最近半年变拥挤，但 `k-skill` 的差异化在两处：

1. **不是教代理写代码，而是教代理用本地公共服务**。技能语义几乎全部是"查询 / 提交 / 缴费"，没有任何"帮你生成代码"的定位。
2. **凭据模式被显式编码进技能元数据**。一般 `skills add` 只关心"装不装得上"，这里连"这个动作能不能自动化、自动化到哪一步"都是元数据的一部分，代理调度时直接知道哪些必须 handoff。

许可证上有个细节值得注意：仓库主体是 MIT，但 `packages/k-skill-proxy/` 与 `infra/k-skill-proxy-dashboard/` 是 AGPL-3.0-only。proxy 作为承载用户数据的中枢层用 AGPL 守住，防止闭源分叉绕开隐私承诺。

## 采用建议

如果这个仓库对你有用，按这个顺序开始：

1. 先 `npx --yes skills add NomaDamas/k-skill --all -g` 装全套，跑 `k-skill-setup` 确认环境和凭据状态。
2. 从查询类技能用起（时刻表、天气、不动产实价、股票行情），零密钥、零风险，先建立信任。
3. 确认可靠后，再逐步启用需要登录态的强身份技能，并明确接受"付款和最终提交永远留人"这一边界。
4. 有合规要求的话，用 `docs/security-and-secrets.md` 的凭据策略做一次对照，决定是否 self-host proxy。

**声明**：本文基于 2026-08 仓库 README 与 `docs/setup.md`、`docs/install.md` 整理；技能清单与凭据要求以仓库当前版本为准，不构成任何投资或法律建议。
