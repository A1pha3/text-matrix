---
title: "Claude-BugHunter：把漏洞赏金狩猎写成 7 道否决门，而不是一份 payload 清单"
date: "2026-11-20T01:27:19+08:00"
slug: "elementalsouls-claude-bughunter-gated-bug-hunting-methodology"
description: "Claude-BugHunter 是面向 Claude Code 的漏洞狩猎技能包，83 个技能、15 个斜杠命令、681 个已披露报告模式。它真正可迁移的部分不是 payload 本身，而是 7-Question Gate 的否决机制、开工前先定交付类型的纪律，以及证据脱敏规范。"
draft: false
categories: ["技术笔记"]
tags: ["安全", "漏洞赏金", "AI Agent", "红队", "Claude Code"]
github_repo: "elementalsouls/Claude-BugHunter"
source_key: "gh:elementalsouls/Claude-BugHunter"
---

## 核心判断

「给 AI 一个漏洞挖掘技能包」这个想法，危险的地方在于它可能只是把一堆 payload 塞进上下文。payload 本身是最容易公开、最难保密、最不值钱的部分 —— 攻防的差距从来不在「知道 XSS 怎么打」，而在「知道什么时候该停手」。

Claude-BugHunter 值得看的地方恰恰在这里。它 83 个技能、681 个已披露报告模式、15 个斜杠命令，体量上和其它技能包没差别；但它把**否决机制**放在了最前面：

- 开工第一件事是**确认交付类型**（漏洞赏金 / 红队 / 渗透测试 / 内部审计），因为同一个目标在不同模式下「什么算一个发现」完全不同；
- 每个候选发现要过 **7 道问答门**，任何一道答错就**杀掉这个发现**；
- 有一份专门的**证据卫生**技能，管 cookie 脱敏、PII 打码、HAR 清洗。

这三条都是**判断纪律**，不是知识。它们在任何模型、任何 harness 上都成立，迁移成本极低。而那些 payload 和绕过表会过期。

需要说清楚适用边界：这套方法论面向**外部攻击面**（bug bounty、外部红队）。内网 Active Directory 攻击、C2 框架、后渗透与横向移动，作者明确列为**故意不做**，理由是「风险画像不同，需要不同的工具和判断力」。这不是遗漏，是设计决策。

另外必须说：**它假定你有授权**。作者自己强调这套东西「在授权红队与漏洞挖掘场景、以及 DVWA / OWASP Juice Shop / Hacker101 / testphp.vulnweb.com 等公开训练平台上经过实战检验」。在授权范围外使用这些内容有法律风险。

截至 2026 年 11 月 20 日，这个仓库有 12120 stars、1570 forks，Python 为主，MIT 许可，2026 年 5 月创建，11 月 19 日仍在更新。

## 四层结构

README 说得很清楚，83 个技能分四层堆叠：

| 层 | 技能 | 职责 |
|---|---|---|
| **想** | `bb-methodology` + `redteam-mindset` | 5 阶段非线性工作流、批判性思维框架、红队操作纪律 |
| **猎 Web 应用** | 58 个 `hunt-*` 技能 | 从 681 个已披露 HackerOne 报告提炼的按类别检测模式、payload、绕过表、链式模板 |
| **打边界** | 企业平台链 | M365/Entra、Okta、vCenter、SSL-VPN 设备、SharePoint、云 IAM 的 2024–2026 CVE 链与凭据后升级路径 |
| **交付** | `triage-validation` + 报告 + `evidence-hygiene` | 7 道问答门、VRT 感知的严重性判定、OOS 反驳、PII 脱敏、红队交付物 |

所有技能**按话题自动触发** —— 用日常英语描述你在测什么，对应的技能就加载，不需要按名字调用。

技能形态本身值得一看。以 `hunt-cors` 为例，它的描述不是泛泛的「CORS 配置错误」，而是具体到攻击手法：

> 源反射带凭据（origin-reflection with credentials）、null 源信任、子域正则绕过（未锚定 / 未转义点 / 仅前缀）、预检（OPTIONS）门控绕过、postMessage 来源检查。

而 `hunt-jwt-crypto` 直接点名两种具体失效：`alg:none` 签名剥离、RS256→HS256 密钥混淆。

这类描述的写法本身有个教学价值：**skill 的 description 就是检索键**。写得具体，模型才匹配得准。

## 机制一：开工前先定交付类型

这是我认为整个项目最有价值的一条规则，因为它在**最便宜的时刻**阻止最大的浪费。

`bb-methodology` 的 PART 0 是「模式确认」，规定在 Phase 0 之前必须明确写下交付类型：

| 交付类型 | 什么算一个发现 | 什么会被拒 |
|---|---|---|
| **漏洞赏金**（H1 / Bugcrowd / Intigriti / 私有 VDP） | **只有证明了影响的 bug**，要能走到攻击者可达到的危害 | 卫生类问题（单独的 EoL 软件、宽松的 CSP、堆栈跟踪、无具体影响的信息泄露、「最佳实践」违规） |
| **红队**（外部客户委托） | 卫生类发现 + 情报收集 + IoC + 防御状态观察**全都是交付物** | 没有 —— 连「这里没发现」都可以作为正面防御观察报告出去 |
| **渗透测试**（签署 SoW / WAPT） | 取决于 SoW，**显式读范围**。通常接受卫生 + 影响 + 情报 | 范围外资产、未授权测试 |
| **内部审计** | 合规映射的发现（PCI / ISO / NIST / DPDPA / GDPR） | 没有控制映射的发现 |

规则是：**开工前把交付类型写进 hunt notes 的第一行**，答不上来就问一次，不要假设。

作者在 skill 里留了一条来自实战授权项目的教训，读起来像是自己踩过：

> 首次针对该目标产出了 5 个卫生类发现（SP2013 EoL、宽松 CSP、堆栈跟踪），以红队格式提交。但这次委托是漏洞赏金 —— 这些发现会被 N/A 成「信息性、未证明影响」。改成「卫生问题作为上下文而非发现」之后，同一目标产出了 11 个证明了影响的 bug，其中 3 个是 Critical。

**同一个目标、同样的技术水平，产出从 5 个全被拒变成 11 个有效发现。** 差别只在于开工前有没有问清楚「什么东西算发现」。

## 机制二：7 道问答门

`triage-validation` 技能的规则是：**按顺序问，任何一道答错就立刻停**。

这里的「停」有个重要的作用域说明，skill 自己特意澄清了：

> 这个技能的门只杀**单个不通过验证的发现**。它们不授权你终止整个委托。通过 7 道问答门杀掉一个发现，只是意味着那个发现不提交 —— 委托里其它每一个测试类别仍然待做。

这是防止 agent 把「我不该报这个」误读成「我可以收工了」。

前四道门大致是：

**Q1 —— 攻击者现在就能一步步用吗？** 要求填一个五段式模板：Setup（需要什么账号）、Request（可复制粘贴的真实 HTTP 请求）、Result（能读到/改掉/删掉什么）、Impact（现实后果）、Cost（时间与资金）。**写不出第 2 段的真实 HTTP 请求，就杀掉它。**

**Q2 —— 影响在项目接受的清单上吗？** 去项目页找 "Vulnerability Types" 或 "Out of Scope"。分档参考：Critical 是无交互的任意用户 ATO、RCE、带数据外泄的 SQLi、管理员鉴权绕过；High 是大规模 PII 外泄、权限提升、带数据的内网 SSRF、全用户存储型 XSS；Medium 是特定用户非关键数据的 IDOR、需点击的敏感页 XSS；Low 是非敏感信息泄露、有 PoC 的点击劫持。**映射到排除项就杀掉。**

**Q3 —— 根因在范围内的资产上吗？** 确认漏洞域名在范围内（不是 `*.internal.target.com`）、是生产资产（除非明确在范围内）、不是第三方服务。

**Q4 —— 是否依赖攻击者拿不到的特权？** 「管理员能做 X」= 中心化风险 = 杀掉（99% 的项目如此）；「非管理员能做只有管理员该做的事」= 有效；「需要物理访问 / MFA 设备」= 通常无效；「需要已攻破的受害者账号才能生效」= 可疑，最好也只是低危。

后面的 Q5–Q7 继续覆盖证据充分性、影响真实性和可复现性。这套门的设计意图很明确：**宁可漏报，不要提高 N/A 比例** —— 技能里写着「N/A 伤害你的有效率。有信息量是中性的。只提交通过全部 7 问的东西。」

它还配了一张「conditionally valid with chain table」和一份「always-rejected list」—— 那些永远不会被接受的情况，以及「单看无效但接上某条链就有效」的组合。

## 机制三：证据卫生

`evidence-hygiene` 技能管的是提交材料本身。它的核心原则：

> 漏洞赏金证据是为了说服审核人。超出这个范围的东西 —— 有效的 cookie、真实用户 PII、没用的内部 trace ID —— 都不该出现在证据里。

它把敏感数据分成四类，并给出**不同的处理方式**：

| 类别 | 例子 | 处理 |
|---|---|---|
| **你自己的账号机密** | session cookie、OAuth token、refresh token、API key | **总是脱敏**，即使是私有赏金平台的附件 |
| **他人的 PII** | 真名、邮箱、电话、地址、头像、账号 ID | 除非明确在演示跨账号影响，否则脱敏；即使演示也要遮脸并最小化展示数据 |
| **审核人用得上的元数据** | trace ID、request ID、服务端时间戳、你的测试账号 UID/邮箱、GraphQL 操作名、响应结构 | **保持可见** —— 这些帮审核人关联日志和复现 |
| **测试账号密码（有限使用）** | 一次性密码（如 `Testing@5678`） | 截图里可以接受，但提交后**立即轮换**，别让截图里的值还有效 |

这个分类的关键在于第二行和第三行的区分 —— 很多脱敏工具做的是「一律打码」，结果把审核人最需要的 trace ID 也抹了，反而增加审核成本。

具体的 cookie 脱敏规则分得很细：

- **必须遮蔽**：session cookie 值（名字因目标而异：`authn`/`session`/`sid`/`__Secure-id`）、与 session 绑定的 `csrf-token`、`Authorization` 头（Bearer / JWT）、任何带会话 cookie 的 `Cookie` 请求头值、任何带会话 cookie 的 `Set-Cookie` 响应头值。
- **可以留可见**：Cloudflare cookie（`__cf_bm`、`_cfuvid`，是 bot 管理不是会话）、分析 cookie（`ajs_anonymous_id`、`_ga`）、trace 关联 ID（`x-datadog-trace-id`、`x-request-id`）、服务端/框架头（`Server: cloudflare`、`X-Frame-Options`）。

脱敏方法按可行性排序，第一条是**最好的办法是从一开始就不捕获**：

- DevTools Console PoC：用 `credentials: 'include'`，让浏览器自动带 cookie，控制台输出就不会回显。截 Console 输出，**不要截 Network 面板的 Headers**。
- Burp Repeater PoC：把底部请求/响应面板的分隔条**往下拖**遮住请求体。Intruder 批量跑只截 Results 表格。

实在必须捕获时才用黑条（macOS：预览 → 工具 → 标注 → 矩形 → 填充黑色）。

HAR 文件清洗则给了具体的 jq 过滤器，针对 Cookie / Set-Cookie / Authorization 头。

## 机制四：思考框架

`bb-methodology` 的 PART 1 是「怎么想」，核心原则是：

> 狩猎不是「找一个 bug」，而是「证明一个攻击场景」。像一个有具体目标的攻击者那样思考，而不是一个找模式的扫描器。

它要求每次动手前先做三件事：**定义**（今天我打哪个功能、达成什么 CIA 影响）、**选择**（挑 1-2 个漏洞类别）、**执行**（只专注选中的技术，不乱走）。

五个终极目标里选一个：机密性、完整性、可用性（仅应用层 DoS）、账户接管、RCE。

批判性思维那一节给的是可操作的提问：

**质疑信任边界** —— 前端禁用了？直接用代理发请求。`user_role=user` 的 cookie？改成 `admin`。POST 里 `price=1000`？改成 `1`。`<script>` 被拦？试 `<img onerror=...>`。

**逆向开发者心理** —— 功能 A 有鉴权检查，那新加的类似功能 B 大概率没有。复杂流程（优惠券 + 积分 + 退款）？边界情况有 bug。`/api/v2/user` 存在？那 `/api/v1/user` 是不是还在跑、鉴权更弱？

**What-If 实验** —— 跳过结账直接打 `/checkout/success`。跳过 2FA 直接导航到 `/dashboard`。并发发 10 次优惠券请求 —— 竞态？把兄弟接口的 `guid=f8a2...` 换成 `id=100` —— IDOR？

这套东西的价值不在于「攻击技巧」，而在于它教 agent **主动构造反例**，而不是被动匹配模式。

## 安装与多 harness 支持

两条安装路径，能力覆盖不同：

```bash
# A —— 作为 Claude Code 插件（推荐）
/plugin marketplace add elementalsouls/Claude-BugHunter
/plugin install claude-bughunter@elementalsouls
```

| 路径 | 83 技能 + 15 命令 | `cbh` CLI | `hunt` 脚手架 |
|---|---|---|---|
| **A —— 插件** | ✅ 命名空间在 `claude-bughunter:` 下 | ➕ 需单独 `pipx install` | ❌ 仅 clone 可用 |
| **B —— 复制安装** | ✅ 复制进 `~/.claude/` | ✅ 来自 clone | ✅ 来自 clone |

复制安装：

```bash
git clone https://github.com/elementalsouls/Claude-BugHunter.git
cd Claude-BugHunter
bash scripts/install.sh          # macOS / Linux
pwsh ./scripts/install.ps1       # Windows
```

**HackerOne 账号是可选的。** 安装时会问 API 用户名和 token，但它们只用于让 HackerOne MCP 读你的私有项目和你的报告；留空也能用全部技能、命令和 MCP 的公开工具（重复报告搜索、项目范围查询）。

多 harness 安装一条命令：

```bash
bash scripts/install.sh --all --burp-mcp
```

| Harness | 目标技能目录 | 参数 |
|---|---|---|
| Claude Code（基线） | `~/.claude/skills/` | （默认） |
| OpenCode | 读 `~/.claude/skills/` 与 `~/.agents/skills/` | （默认）/ `--agents` |
| OpenAI Codex CLI | `~/.agents/skills/` | `--agents` |
| Hermes Agent | `~/.hermes/skills/` | `--hermes` |
| Google AntiGravity | `~/.gemini/config/skills/` | `--antigravity` |

**知识层**可以移植到全部五个，但斜杠命令和 `/hunt` 引擎**按设计只留给 Claude Code** —— 它们依赖 Claude Code 的插件机制。

## 边界

**故意不做（作者明说是设计决策不是缺口）：**

- **内网 Active Directory 攻击** —— BloodHound、Kerberoasting、ASREProast、DCSync、Pass-the-Hash、AD CS 滥用、ntlmrelayx、Responder、PetitPotam 等
- **C2 框架** —— Cobalt Strike、Sliver、Mythic、Havoc、BRC4
- **后渗透 / 持久化 / 横向移动** —— Mimikatz、comsvcs LSASS 转储、金票据银票据等

理由是「风险画像不同，需要不同的工具和判断力」。

**这不影响本文的结论**：那三条判断纪律（先定交付类型、7 道否决门、证据脱敏）跟内外网无关，照样适用。

**另一个边界**：HackerOne 报告模式是**公开的**。它们教会 agent 攻击已修复的漏洞，这在授权测试里是合法的，但意味着**这套技能库不会包含 0day 或未披露的技术**。期待「装上就拿到独家 0day」的人会失望。

## 采用顺序

1. **先只读三份 skill**：`bb-methodology`（模式确认 + 思考框架）、`triage-validation`（7 道门）、`evidence-hygiene`（脱敏）。这三份是方法论，其余 80 份是知识。**先把方法论内化，知识按需查。**
2. **读 `docs/skills.md`** —— 681 个报告模式的索引。搜索用浏览器的 ⌘/Ctrl-F 或文档搜索框。这份文件由 `scripts/gen_skill_catalog.py` 生成，不要手改。
3. **在公开训练平台上练**（DVWA、OWASP Juice Shop、Hacker101、testphp.vulnweb.com）。仓库自己列了这些平台，正是为此准备的。
4. **再装插件**，先不配 HackerOne token —— 公开工具不依赖它。
5. **第一次真实委托，开工前把交付类型写进 notes 第一行。** 这一步花十秒，省几小时。

## 排查：按现象定位

| 现象 | 先查这里 |
|---|---|
| 技能没被触发 | `description` 里的触发词是否匹配你的说法；技能是**按话题自动加载**的，不按名字调用 |
| 发现被判 N/A | 回头过 7 道门，重点是 Q2（项目排除项）和 Q4（特权依赖）；`hunt-*` 技能的描述里常直接写着该项目常见的拒绝理由 |
| 报告描述里出现内部 trace ID 被打回 | `evidence-hygiene` 的分类表：trace ID 是**该留可见**的，不要一刀切脱敏 |
| 截图里带了有效 cookie | 用「方法 A」重来：`credentials: 'include'` + 截 Console 而不是 Network 面板 |
| 插件模式下没有 `cbh` CLI 或 `/hunt` | 这两个是 clone-only，见上表；用 `pipx install git+https://github.com/elementalsouls/Claude-BugHunter` 补 CLI |
| 不知下一步做什么 | `bb-methodology` 是主控技能，明确说「use when asking what should I do next」 |

## 参考

- 仓库：<https://github.com/elementalsouls/Claude-BugHunter>
- 文档站：<https://elementalsouls.github.io/Claude-BugHunter>
- 技能目录（可搜索）：<https://github.com/elementalsouls/Claude-BugHunter/blob/main/docs/skills.md>
- 安装指南：仓库内 `INSTALL.md`；用法：仓库内 `USAGE.md`
- 多 harness 指南：仓库内 `docs/multi-harness.md`
