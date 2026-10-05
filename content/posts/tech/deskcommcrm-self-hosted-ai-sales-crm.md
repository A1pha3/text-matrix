---
title: "DeskcommCRM：从 WhatsApp CRM 长起来的开源 AI 销售 OS"
date: 2026-09-18T03:50:00+08:00
lastmod: 2026-10-01
slug: "deskcommcrm-self-hosted-ai-sales-crm"
github_repo: "melgarafael/DeskcommCRM"
source_key: "gh:melgarafael/DeskcommCRM"
description: "DeskcommCRM 是 Next.js 16 + React 19 + Supabase 栈的自托管开源销售系统，AI 代理在 WhatsApp 上接待、资格判定与跟进，内置 72 个工具的 MCP 服务端，语音另有 WhatsApp 通话与 SIP 电话两条线。本文拆解其安装器设计、事件驱动架构与适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["CRM", "AI Agent", "WhatsApp", "自托管", "Next.js"]
---

## 核心判断

巴西市场的大量生意在 WhatsApp 上成交，而商业 CRM 按席位收月费、把聊天数据锁在别人服务器里的模式，与这个场景天然冲突。DeskcommCRM 的定位因此非常具体：**一个 MIT 许可、自托管的开源销售系统，AI 代理在 WhatsApp 上接待、资格判定与跟进，自我描述为 Kommo、Octadesk 和 Intercom 的开源替代**。

名字来自 Desk + comm（commerce）。仓库 2026 年 4 月 28 日创建时是个电商 CRM，社区把它用进了诊所、房产中介、信息产品和各类服务业，维护者 Rafael Melgaço 顺着这个走向把它改口叫"销售操作系统（Sales OS）"：代理带租户级 RAG 回答客户、推进管道、触发自动化，并且知道什么时候把对话交还给人。

它的工程亮点不在模型层，而在交付层：一条命令的 VPS 安装器、幂等的数据库 schema、自动回滚的一键更新。这些是自托管软件最难做对的部分，这个仓库把它们做出了产品级的完成度。截至 2026-10-01，仓库 4,306 stars、1,089 forks，最新版本 v1.69.0（2026-09-30）——从 9 月 17 日的 v1.32.0 到 v1.69.0 只用了 13 天，高峰期一天发数个版本。迭代速度说明这是个活项目，也意味着任何解读文里的版本号都有保质期，机制比数字长寿。

## 技术栈与架构

| 层 | 选型 |
|---|---|
| 前端/应用 | Next.js 16 App Router（Turbopack）+ React 19 + strict TypeScript（package.json：next ^16.3.6、react ^19.3.0、typescript ^6.0.3） |
| 数据库/认证/存储 | Supabase（Postgres + RLS 行级安全 + pgvector、Auth、Realtime、Storage），Session pooler 连接 |
| WhatsApp 通道 | WAHA（devlikeapro/waha，compose 钉住免费 Core 镜像标签，可用 WAHA_IMAGE 换 Plus）或 Meta 官方 Cloud API |
| AI | Vercel AI SDK v7：OpenRouter、Requesty、Anthropic、OpenAI、Google 任选，装机时选定，之后可在界面按子系统分别切换——负责对话的模型不必是负责索引的模型 |
| 限流/校验/遥测 | Upstash Redis（滑动窗口）、Zod、Sentry（装机遇选，上报前脱敏） |
| 部署 | Docker Compose + Caddy 自动 HTTPS；app/worker/scheduler 三张镜像由 CI 强制构建，另有按需启用的 voice-agent 镜像 |
| 代理协议 | 内置 MCP 服务端，72 个工具一一映射既有 REST 端点 |

技术栈是主流的组合，没有 exotic 依赖。架构上最值得注意的一条纪律：**没有任何数据库触发器直接发 HTTP 请求**。每个事件（新线索进来、阶段变更、WhatsApp 消息到达）写进 event_log 表，由安装器部署在宿主机上的 cron 每分钟排水，消费者是 workers/ 目录下的常驻 worker——AI 响应、情感分析、RAG 索引、LGPD（巴西通用数据保护法）导出与抹除、媒体处理、语音代理等各占一个。慢消费者只会堆积不会雪崩，重试和审计有统一的落点。

MCP 这一条容易读反：现在的形态是**内置 MCP 服务端**（`app/api/mcp/`），把 CRM 已有的操作包成 72 个工具（线索、预约、知识检索、组织记忆、自动化规则、人工接管、隐私请求等），供自家代理引擎和外部代理消费；认证复用 REST 的 `dsk_` API key，工具执行走与 REST 相同的 RLS 策略，变更记审计日志（actor 记为 ai_agent）。把整个 CRM 开放给任意第三方代理生态的 Public MCP 还在路线图上，尚未发布。

## 安装器：这个仓库最值得读的部分

大多数自托管项目的 README 停在 `docker compose up`，DeskcommCRM 的 `hostgator-setup-kit/install.sh` 做到了商业软件的水准：

1. **只问用户才知道的事**（域名、API key、管理员密码），技术性密钥全部自动生成。
2. **逐项前置校验**：key 填错当场拒绝，而不是跑到第三步才报错。
3. **Supabase 可以由安装器代建**：导出 `SUPABASE_ACCESS_TOKEN` 后，它创建项目、等待数据库就绪、取回四项凭据、用一次真实连接实测推断 pooler host——README 的原话是 no copy-paste。
4. **幂等**：重复执行不重复建 cron、不重复建用户，中断后可续跑；幂等性本身也被 CI 专门验证（见下文"工程文化"）。
5. **环境自适应**：检测到 VPS 已有反代占用 80/443 时自动改为经由反代发布；Hostinger 式 `--network host` 场景则主动询问而非猜测——README 的原话是，发布在错误的反代后面，"successfully installs a mute website"（装出一个"成功"但打不开的站点）。

部署前还有一条低门槛路径：在自己电脑上跑 `hostgator-setup-kit/comecar.sh`，它会按你的场景给出该买的套餐和对应的安装命令；全自动部署支持把 `.env.hostgator.example` 复制为 `.env` 填好后执行 `install.sh --yes`。

更新链路同样有讲究。界面上的一键更新只发起请求，实际执行者是安装时部署在 VPS 宿主机上的更新代理（agent.sh 的自述是"roda por cron a cada 5 minutos"），所以点击后最多 5 分钟开始执行。更新前自动备份数据库，按"备份 → 代码 → 数据库 → 上线"四阶段推进，新版本健康检查失败则自动回滚到上一镜像并把回滚记录写进 `.env`——不写下来，下次重启就会把坏版本悄悄拉起来。更新代理失联时，界面会明说自动更新不可用并给出手动命令，不假装更新成功。数据库升级靠重放幂等的 `baseline.sql`，它同时承担"自愈"角色，修复旧版本弄乱的数据，数据库忙时自动重试最多三轮；`update.sh` 只更新到已发布的 release tag，绝不追 main 分支，也拒绝降级（`--force` 才放行，属于故意留的口子）。

一个值得抄的细节：`supabase/migrations/` 里 0001–0009 和 0013 都是 `SELECT 1;` 桩，迁移链从零建不起来，真实 schema 只活在 `baseline.sql` 里；README 直接警告开发者，`supabase db push` 会"成功"然后留给你一个空库。自托管用户拿到的每一次 schema 变更，靠"版本化迁移 + baseline.sql 幂等附录"双写送达，这条纪律写进了贡献的 Definition of Done。

## AI 代理：72 把工具与带闸门的自我改进

AI 侧的能力围绕销售漏斗组织：代理在 WhatsApp 上接待、资格判定（qualify）、跟进，把对话推进管道，在合适时机交还给人——交接全程审计，AI 是一等分配对象。单租户 RAG（pgvector）管知识检索，代理还能在对话中自行执行技能、读写组织记忆、做情感分析；每个组织有 AI 花费上限，花销在 Usage & budget 界面可见。

代理可用的工具就是上面那 72 个 MCP 工具，从 `crm_search_contacts` 到 `crm_request_human_handoff`，命名、权限包（atender/vender）都在 `lib/mcp/tools/catalogo/` 静态目录里声明。目录文件里写着给谁看的规则：description 讲给模型听，rotulo 和 explicacao 讲给诊所老板、房产中介这类配置者听，另有一个单元测试机械地把关"外行友好"。

项目对"代理自我改进"的着墨超出一般 CRM：已解决的对话沉淀为新知识；AI Evolution 界面展示代理是否在变好、错在哪、还差什么没教；AI 给自己提改进建议（Proposals），确认后作为新版本应用——所有提议必须过人工这一关。最新的 v1.69.0 又加了一个叫 Jev 的观察者：跟进流程里常用 AI 对客户回复做分类时，Jev 同题作答但不拍板，只在后台累计两边的一致率，一致率攒够之前"让 Jev 决定"的按钮根本不出现。

## 语音：两条电话线，都默认关闭

语音能力分两条线，落地时间都在近期，且设计上都很克制：

- **WhatsApp 语音通话**（v1.19.0，2026-09-11）：坐席在收件箱里直接拨打或接听客户的 WhatsApp 电话，浏览器里走 WebRTC。底层是第三方开源项目 WaCalls（Go 服务端，MIT），把你的号码作为一个新的 WhatsApp 连接设备配对——这等于多一个封号风险的接入点，所以开启前管理员必须在设置里勾选确认接受 WhatsApp 封号风险；通话录音在当前版本刻意关闭，录音属 LGPD 敏感数据，接入抹除级联的方案留待后续。
- **SIP 电话 + AI 语音代理**（v1.41.0，2026-09-20）：这才是 AI 接电话——CRM 通过 SIP 中继接打电话，AI 语音代理与对方对话，通话转写进联系人历史。号码在 Conexões › Telefone 登记，各自绑定一个语音代理；实现上自带 Asterisk 配置（ARI/PJSIP/RTP），voice-agent worker 用 OpenAI Realtime（gpt-realtime）做语音到语音。整个模块藏在 `COMPOSE_PROFILES=telefonia` 开关后面，不开就当它不存在。

## 自动化与防封

自动化规则采用 WHEN/IF/THEN 三元形式（葡语界面写作 QUANDO / SE / ENTÃO，`RuleEditor.tsx` 里就是三块标题），由安装器一并部署的事件 cron 驱动——没有这个 cron，规则只会在队列里堆积。规则创建后默认暂停，人工审过才生效；每次执行的每步动作在 Activity 时间线里可查，外部 webhook 调用失败可以手动重试。

线索入口不限于 WhatsApp：每个租户可以开"捕获源"——一个带 token 的公共端点（`/api/v1/webhooks/in/<token>`），落地页、自建表单或 Zapier/n8n POST 一段 JSON 过来，线索直接落进指定管道和阶段。

WhatsApp 通道的防封是产品级功能：发送带节流、抖动和时间窗，STOP 关键词检测，发送保护（窗口/节奏/上限）可配，限流原因直接翻译在会话里给坐席看。这些缓解措施反过来说明问题真实存在——WAHA 走非官方协议，封号风险始终自担。

## 工程文化：把"别信我，去测"写进文档

这个仓库最罕见的不是某个功能，而是它对自己文档的态度。README 讲合并必过的五道 CI 关卡（verify、build-and-size、invariants、e2e、imagens-ok）时，特意加了一句"这个清单之前写过四道又写过五道——去实测，别照抄"，并给出一条 `gh api` 命令让读者自己查分支保护规则。

invariants 关卡会起一个干净的 Postgres，先用 install 模式灌 `baseline.sql`，再用 update 模式重放以证明幂等，然后跑 RBAC、分配、路由、跟进、webhook、自动化的不变量测试。其中 RLS 隔离测试创建两个组织，用与生产相同的 `auth.uid()` 路径模拟 JWT，证明 A 组织用户在 conversations、messages、contacts、crm_leads 四张表里看不到 B 组织的任何一行——并且先跑一个对照用例证明 B 组织的行真的存在，否则对着空表测试也会"通过"。

社区侧同样量化：仓库的 PR 分诊手册（TRIAGEM.md）开头就摆数据——公开的前 60 天，6 位外部贡献者提了 16 个 PR，合并 15 个、关闭 0 个；同时坦承分支保护并不强制人工 review，"你身后没有网，你的错误会进 main"。文档体系有统一索引和优先规则，两份文档打架时听谁的写得很明白。对想学自托管软件交付工程的人，这套 `hostgator-setup-kit/` 和 `docs/` 是很好的参考实现——尤其适合拿它对照自己项目里 `update.sh` 的粗糙程度。

## 适用边界

- **主场景是 WhatsApp 销售**：不在 WhatsApp 上做生意的团队，它的大部分差异化用不上。
- **巴西基因明显**：README 与大部分文档以葡语为主（有英、西译本，翻译靠社区），集成对象（Nuvemshop 电商、LGPD 合规模块）面向巴西市场，VTEX 和 Shopify 适配器在路线图上。中国用户可直接复用其架构，但本地化（企业微信、飞书等通道）需要自行改造。
- **语音是可选项**：两条语音线默认关闭，WhatsApp 通话要额外配对设备、有封号风险，SIP 电话要自备中继和 Asterisk；不用语音的团队不受影响。
- **需要一台 VPS + Supabase 账号 + AI API key**：推荐 4 GB 内存起步；Supabase 免费档不自带备份，README 提醒用 cron 每天跑 `backup.sh`。
- **支持是社区性质的按现状提供**：没有 SLA；谁部署谁就是数据的 LGPD 控制者，维护者接触不到你的数据库和 WhatsApp 会话。
- **HostGator 合作链接**：README 带有商业推广性质的合作链接（圣保罗机房），选型时应注意区分工程内容与推广内容。

## 结论

DeskcommCRM 站在"垂直场景 + 自托管 + AI 代理"三个趋势的交叉点上，交付链路（单命令安装、幂等升级、自动回滚、CI 门禁、量化文档）达到了许多商业产品都没有的水准。13 天 37 个 minor 的迭代速度意味着本文的版本号很快过期，但几条主心骨——事件不直发 HTTP、MCP 工具映射既有 REST、schema 只认 baseline.sql 一个真相、提议型自我改进必须过人工——短期内看不出会变。适合两类人：在 WhatsApp 上做销售、想摆脱 SaaS 月费的团队，直接部署；以及在做自托管产品或 agent 工程的开发者，把它的安装器和文档当教材来读。

项目地址：[melgarafael/DeskcommCRM](https://github.com/melgarafael/DeskcommCRM)
