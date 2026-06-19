---
title: "FreeDomain：156k Stars 免费域名平台完全指南"
date: "2026-04-06T22:22:00+08:00"
slug: "freedomain-free-domain-guide"
description: "全面介绍 156k Stars 的 FreeDomain 免费域名平台，涵盖可用域名扩展（.DPDNS.ORG 等）、注册流程、DNS 配置（Cloudflare/FreeDNS）、使用场景、社区参与和使用建议。"
draft: false
categories: ["技术笔记"]
tags: ["FreeDomain", "免费域名", "DNS", "Cloudflare", "域名注册", "自助托管"]
---

## 先把判断说清楚

FreeDomain 解决的是"零成本给一个项目挂上自定义域名"这件事，不解决"项目做大之后的品牌资产稳定性"。它把 `.dpdns.org`、`.us.kg` 这类后缀的子域名免费委托给个人开发者使用，配合 Cloudflare 等 DNS 提供商，可以在不花一分钱的前提下完成"注册域名 → 配置 DNS → 部署站点 → 上 HTTPS"的完整链路。

这件事的价值边界很明确：对个人 side project、demo 站点、内网穿透、教学实验来说，省下每年 $10–$15 的域名续费是有意义的；对商业产品、长期品牌、需要邮件投递可靠性的业务来说，免费域名带来的稳定性、所有权和 SEO 风险远超省下的钱。这篇文章会把这两条线都讲透，并给出迁移路径。

技术栈位置上，FreeDomain 只动 DNS 层最上面那一格——它把 `dpdns.org` 这个真实注册的域名，以 NS 委托的方式切出子域名交给用户。应用层（你的 Web 服务、API、静态站点）和解析层（Cloudflare 的权威 DNS + CDN）都不在它管辖范围内。理解这个分工，是后面所有配置和风险判断的前提。

## FreeDomain 在 DNS 体系里的位置

要把 FreeDomain 讲准确，得先回到 DNS 的层级结构。

互联网域名从右向左逐级委托。根域名服务器把 `.org` 委托给 PIR 运营的权威服务器，PIR 把 `dpdns.org` 这个二级域名注册给 DigitalPlat Foundation，DigitalPlat 再把 `yourname.dpdns.org` 这个三级域名的解析权以 NS 记录的形式委托给用户指定的权威 DNS（通常是 Cloudflare 的 nameserver）。

所以 `.dpdns.org` 不是一个真正的顶级域（TLD），它是 `dpdns.org` 这个普通二级域名下的三级域名。同理，`.us.kg` 是 `us.kg` 下的三级域名，`.qzz.io` 是 `qzz.io` 下的三级域名。ICANN 的 TLD 列表里找不到它们，浏览器地址栏里看到的"自定义后缀"只是 DNS 委托链路造成的视觉效果。

这件事决定了 FreeDomain 的几个根本属性：

第一，它不需要走 ICANN 注册局，运营成本只有一台管理面板服务器 + 几个真实域名的年费，所以能免费。

第二，用户拿到的不是"域名所有权"，而是"在 DigitalPlat 拥有的域名下开设子域名的使用权"。AGPL-3.0 许可证覆盖的是 FreeDomain 这个项目的代码，不是用户注册的子域名——子域名的使用条款由 DigitalPlat 的服务协议约束，违反条款可以被回收。

第三，整个系统的稳定性挂在 DigitalPlat 这一个组织上。如果 `dpdns.org` 这个母域名因为滥用被 PIR 撤销，或者 DigitalPlat 停止维护，所有挂在上面的子域名会一起失效。这是免费域名最核心的风险，后面会单独展开。

目前 FreeDomain 在 GitHub 上拿到 156k+ Stars，托管了 400,000+ 个子域名。项目由 DigitalPlat Foundation 的 Edward Hsing 独立维护，仓库地址 `DigitalPlatDev/FreeDomain`，主语言是 HTML（管理面板），辅以少量 JavaScript 和 Python。Stars 数高不等于服务等级高——这是一个社区维护的免费服务，没有 SLA，没有商业兜底。

## 可用的域名后缀和它们的实际差异

FreeDomain 当前开放注册的后缀有五个：

```
yourname.dpdns.org    # 主力后缀，使用最广
yourname.us.kg        # 短后缀，kg 是科特迪瓦国家代码
yourname.qzz.io       # .io 系，看起来更"技术"
yourname.xx.kg        # 短后缀
yourname.qd.je        # .je 是泽西岛国家代码
```

这些后缀在功能上完全等价——都是 DigitalPlat 拥有的二级域名下开设的三级域名，都支持 NS 委托到第三方 DNS 提供商。差异只在视觉和可用性上：

- `.dpdns.org` 是项目主推后缀，文档最全，社区案例最多，遇到问题最容易搜到答案。
- `.us.kg` 字符短，但 `.kg` 是科特迪瓦 ccTLD，受该国注册局政策约束，理论上存在国家层面政策变动的风险。
- `.qzz.io` 视觉上接近付费的 `.io` 域名，但本质仍是子域名，不要被外观误导。

选择上没有技术理由偏好某一个，按视觉偏好选即可。如果项目可能长期演进，建议优先 `.dpdns.org`，因为它是项目主域名，被回收或停运的概率相对最低。

## 从注册到上线：一个完整的工程案例

下面用一个具体场景把流程串起来：你想给一个 Hugo 静态博客挂上 `myblog.dpdns.org`，托管在 Cloudflare Pages 上，全程零成本。

### 第一步：在 FreeDomain 注册子域名

打开 `https://dash.domain.digitalplat.org/`，用邮箱注册账户并完成邮箱验证。在仪表盘的搜索框输入想要的域名前缀，系统会列出所有可用后缀。选中 `myblog.dpdns.org`，点击注册。

注册成功后，域名进入你的管理列表，但此时它还没有任何 DNS 记录——FreeDomain 自己不提供解析，它只提供 NS 委托。你需要把域名的权威 DNS 指向 Cloudflare。

### 第二步：在 Cloudflare 添加站点

登录 `https://dash.cloudflare.com/`，点击 "Add a Site"，输入 `myblog.dpdns.org`，选择 Free 计划。Cloudflare 会扫描当前 DNS 记录（这一步通常扫不到东西，因为 FreeDomain 默认不配记录），然后给你分配两个 nameserver，形如：

```
megan.ns.cloudflare.com
loyd.ns.cloudflare.com
```

记下这两个 nameserver，下一步要用。

### 第三步：在 FreeDomain 设置 NS 委托

回到 FreeDomain 仪表盘，进入 `myblog.dpdns.org` 的管理页面，找到 Nameserver 设置项，把 Cloudflare 给的两个 nameserver 填进去，保存。

这一步的技术含义是：你告诉 FreeDomain，"以后任何对 `myblog.dpdns.org` 的 DNS 查询，都转给 Cloudflare 的这两台权威服务器去回答"。FreeDomain 会在 `dpdns.org` 的权威 DNS 上为 `myblog` 写一条 NS 记录，指向 Cloudflare 的 nameserver。从此这个子域名的所有 A、AAAA、CNAME、MX 记录都在 Cloudflare 那边管理。

### 第四步：在 Cloudflare 配置解析记录

回到 Cloudflare 的 DNS 管理界面，为 `myblog.dpdns.org` 添加解析记录。如果用 Cloudflare Pages 托管，添加一条 CNAME 指向 Pages 给的 `*.pages.dev` 域名：

```
类型: CNAME
名称: @
目标: myblog.pages.dev
代理状态: 已代理（橙色云）
```

如果用自己的服务器，添加 A 记录指向服务器 IP：

```
类型: A
名称: @
值: 203.0.113.10
代理状态: 已代理（橙色云）
```

"已代理"状态会把流量先送到 Cloudflare 的 CDN 节点，再回源到你的服务器，同时自动签发 SSL 证书。这是免费方案能拿到 HTTPS 的关键——Cloudflare 的 Universal SSL 对所有走代理的域名免费签发。

### 第五步：等待 DNS 传播

NS 委托的变更不是全球即时生效的。`dpdns.org` 的 NS 记录有 TTL（Time To Live），各级递归 DNS 也会按 TTL 缓存。实测下来，Cloudflare 那边通常几分钟就能看到记录生效，但部分地区的递归 DNS 可能要等几小时才会刷新缓存。

传播完成后，访问 `https://myblog.dpdns.org` 就能看到你的站点，浏览器地址栏会有 HTTPS 锁标。整个流程下来，钱包没动一下。

### 用 GitHub Actions 自动化部署

手动上传静态文件到 Cloudflare Pages 不是长久之计，正常做法是把站点代码托管在 GitHub，用 GitHub Actions 在 push 时自动构建并部署到 Cloudflare Pages。这套 CI/CD 也是免费的——GitHub Actions 对公开仓库免费 2000 分钟/月，Cloudflare Pages 免费额度 500 次构建/月。

在仓库根目录加一个 workflow 文件：

```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloudflare Pages

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Hugo
        uses: peaceiris/actions-hugo@v3
        with:
          hugo-version: 'latest'

      - name: Build
        run: hugo --minify

      - name: Deploy to Cloudflare Pages
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: myblog
          directory: public
```

`CLOUDFLARE_API_TOKEN` 在 Cloudflare Dashboard → My Profile → API Tokens 创建，权限选 "Cloudflare Pages — Edit"。把 token 和 account ID 填到 GitHub 仓库的 Secrets 里。

配置完成后，每次 push 到 `main` 分支，GitHub Actions 会自动构建 Hugo 站点并部署到 Cloudflare Pages，几分钟后 `myblog.dpdns.org` 上的内容就更新了。整套链路零成本、全自动，是个人开发者搭博客的标准姿势。

## DNS 配置的工程直觉

理解 DNS 传播，需要先理解缓存层级。当你访问 `myblog.dpdns.org` 时，DNS 查询会经过这样的链路：

1. 本地操作系统的 DNS 缓存（macOS 是 `mDNSResponder`，Linux 是 `systemd-resolved` 或 `nscd`）
2. 路由器或企业内网的 DNS 转发器
3. ISP 的递归 DNS 服务器（如 `8.8.8.8`、`114.114.114.114`）
4. 根域名服务器 → `.org` TLD 权威 → `dpdns.org` 权威 → Cloudflare 权威

每一层都会按 TTL 缓存上一层的回答。你改了 Cloudflare 上的 A 记录，Cloudflare 权威服务器立即生效，但下游所有缓存层都要等 TTL 到期才会重新查询。这就是为什么"DNS 传播"是一个渐进过程，而不是一个瞬间事件。

TTL 的工程取舍是：TTL 短，变更生效快，但查询压力大、解析慢；TTL 长，解析快、负载低，但变更生效慢。Cloudflare 默认 TTL 是 300 秒（5 分钟），适合需要频繁切换 IP 的场景；如果是稳定服务，可以调到 3600 秒（1 小时）甚至更长。

排查 DNS 问题时，常用的命令：

```bash
# 查询域名的权威 NS 记录，确认 NS 委托是否生效
dig NS myblog.dpdns.org +short

# 查询 A 记录，看实际解析到哪个 IP
dig A myblog.dpdns.org +short

# 追踪整个 DNS 查询链路，看哪一层返回了什么
dig myblog.dpdns.org +trace

# 查询特定递归 DNS（如 Cloudflare 的 1.1.1.1）的解析结果
dig @1.1.1.1 myblog.dpdns.org
```

如果 `dig NS` 返回的还是 DigitalPlat 默认的 nameserver，说明 NS 委托还没生效或配置有误；如果返回的是 Cloudflare 的 nameserver，但 A 记录还是错的，说明 Cloudflare 那边的记录配置有问题。

### 关于 CNAME Flattening

RFC 1034 规定根域名（apex，即 `myblog.dpdns.org` 这种裸域名）不能配 CNAME 记录，只能配 A/AAAA。这给托管平台带来麻烦——Cloudflare Pages、Vercel、Netlify 给的都是 `*.pages.dev`、`*.vercel.app` 这类 CNAME 目标，没法直接配到根域名上。

Cloudflare 的解法叫 CNAME Flattening：在 Cloudflare 那边把根域名的 CNAME 记录在权威响应时"压平"成 A 记录。也就是说你在 Cloudflare 控制台给 `@` 配 CNAME 指向 `myblog.pages.dev`，Cloudflare 会内部解析这个 CNAME 链，最终以 A 记录的形式返回 IP 给查询方。这样既绕开了 RFC 限制，又让根域名能直接指向托管平台的 CNAME 目标。

这是选 Cloudflare 的另一个隐性优势——其他免费 DNS 提供商不一定支持 CNAME Flattening，根域名只能配 A 记录，意味着你必须有自己的公网 IP，没法用 Cloudflare Pages 这类只给 CNAME 的托管服务。

### DNSSEC 的取舍

DNSSEC（DNS Security Extensions）给 DNS 响应加上数字签名，防止 DNS 响应被中间人篡改。理论上是个好东西，但在免费域名场景下基本用不上。

原因在于 DNSSEC 需要逐级配置信任链：根域名 → TLD → 你的域名 → 子域名，每一级都要把下一级的公钥指纹（DS 记录）写到上一级。FreeDomain 的母域名 `dpdns.org` 是否启用了 DNSSEC 取决于 DigitalPlat，用户无法控制；即使母域名启用了 DNSSEC，子域名的 DNSSEC 配置也需要 Cloudflare 那边支持并手动开启。

实际操作中，免费域名 + Cloudflare 的组合默认不开 DNSSEC，对绝大多数场景够用。DNSSEC 主要防范的是 DNS 劫持，而 Cloudflare 的 DoH（DNS over HTTPS）和 DoT（DNS over TLS）已经从客户端到递归 DNS 这一段解决了窃听问题，剩下的递归 DNS 到权威 DNS 这一段，攻击面相对小。除非你的应用对 DNS 完整性有强需求，否则不用折腾 DNSSEC。

## 为什么选 Cloudflare 而不是其他 DNS 提供商

FreeDomain 官方文档列出的 DNS 托管选项有 Cloudflare、FreeDNS（afraid.org）、Hostry 三家。在免费方案里，Cloudflare 几乎是唯一合理的选择，原因不在 DNS 本身，而在 DNS 之外的东西。

DNS 解析这件事，主流免费提供商做得都不差。FreeDNS 老牌稳定，Hostry 简洁易用，解析速度都不慢。但免费域名用户的真实需求不是"DNS 能解析"，而是"零成本上线一个能用的 HTTPS 站点"。这个需求里 DNS 只占三分之一，另外三分之二是 CDN 和 SSL。

Cloudflare 的免费计划同时给三样东西：

- **权威 DNS**：全球 Anycast 网络，解析延迟低，免费额度无限查询。
- **CDN 代理**：开启"已代理"后，流量走 Cloudflare 边缘节点，源站 IP 隐藏，静态资源缓存加速，DDoS 防护免费包含。
- **Universal SSL**：自动签发并续期 SSL 证书，HTTPS 开箱即用，无需自己折腾 Let's Encrypt。

FreeDNS 和 Hostry 都不提供 CDN 和 SSL，只做 DNS 解析。如果用它们，你要自己解决 CDN（找另一家免费 CDN）和 HTTPS（自己跑 `certbot` 或上 Let's Encrypt），复杂度直接翻倍，而且免费 CDN 的稳定性普遍不如 Cloudflare。

所以默认选 Cloudflare 不是因为它"最好"，而是因为它在免费档把 DNS + CDN + SSL 三件事打包解决了。只有一种情况考虑别的提供商：你的源站已经在用别的 CDN（比如 Vercel、Netlify 自带 CDN），只需要 DNS 解析，这时候 FreeDNS 也够用。

## 常用 DNS 记录类型和它们的作用

配置 DNS 时会遇到几种记录类型，理解它们的语义比记表格重要。

**A 记录**把域名指向 IPv4 地址。最基础的记录类型，源站有公网 IPv4 时用它。

**AAAA 记录**把域名指向 IPv6 地址。如果源站支持 IPv6，建议同时配 A 和 AAAA，让客户端自己选协议。

**CNAME 记录**把域名指向另一个域名，而不是 IP。常用于把 `www` 指向 `@`，或者把自定义域名指向 `*.pages.dev`、`*.netlify.app` 这类托管平台给的域名。CNAME 不能和 A/AAAA 共存于同一主机名（RFC 1034 的限制），所以根域名（`@`）通常用 A，子域名用 CNAME。

**MX 记录**指定邮件服务器。格式是 `优先级 邮件服务器域名`，例如 `10 mail.example.com`。注意 MX 必须指向域名，不能直接指向 IP。

**TXT 记录**存任意文本，主要用于域名验证（Google Search Console、各种第三方服务）和邮件认证（SPF、DKIM、DMARC）。

**NS 记录**把子域名的解析权委托给另一组权威 DNS。这是 FreeDomain 工作的基础——`dpdns.org` 的 NS 记录把 `myblog` 这个子域名的解析权委托给 Cloudflare。

实际配置时，A 和 CNAME 用得最多，MX 和 TXT 看需求，NS 一般不需要手动改（除非做二级委托）。

## 使用场景和适用边界

免费域名的适用场景有一个共同特征：**域名的稳定性不是项目的核心约束**。

**个人博客和作品集**。开发者想给自己的 Hugo/Hexo 博客挂个自定义域名，但不想每年花 $12 续费。博客的读者主要是朋友和搜索引擎，域名换了影响不大。这是免费域名最典型的场景。

**开源项目展示页**。给 GitHub 仓库配一个 `myproject.dpdns.org` 的落地页，文档、demo、截图都挂上面。项目死了域名也跟着丢，无所谓。

**内网穿透和自托管服务**。配合 frp、Cloudflare Tunnel、Tailscale 这类工具，给家里的 NAS、Home Assistant、Jellyfin 挂个域名，从外网访问。这种场景下域名是"便利设施"而不是"业务入口"，免费域名完全够用。

以 Cloudflare Tunnel 为例，它的工作原理是在你的内网机器上跑一个 `cloudflared` 客户端，主动连到 Cloudflare 边缘节点建立反向隧道，外部访问 `home.dpdns.org` 时流量经 Cloudflare 边缘节点回源到你的内网服务，不需要公网 IP，不需要开端口。配合免费域名，整个内网穿透方案零成本：

```bash
# 安装 cloudflared
brew install cloudflared

# 登录（会打开浏览器授权）
cloudflared tunnel login

# 创建隧道
cloudflared tunnel create home-services

# 配置隧道指向本地服务（如 NAS 的 5000 端口）
cloudflared tunnel route dns home-services home.dpdns.org

# 运行
cloudflared tunnel run home-services
```

这种用法把 FreeDomain 的"零成本域名"和 Cloudflare 的"零成本隧道 + CDN + SSL"叠在一起，是个人开发者搭自托管服务最划算的组合。

**教学和实验环境**。学 DNS、学 HTTPS、学 CDN，需要一个真实域名做实验，但又不想为实验花钱。免费域名是最佳教具。

**API 端点和 Webhook 回调**。给 side project 的 API 挂个域名，方便第三方服务回调。但要注意：如果 API 是给付费客户用的，不要用免费域名——客户看到 `.dpdns.org` 会怀疑服务的可靠性。

反过来，下面这些场景必须用付费域名：

**商业产品和 SaaS**。付费用户对域名稳定性有合理预期，免费域名随时可能失效，一旦失效就是直接的业务损失。

**长期品牌资产**。品牌域名是公司资产的一部分，写在所有营销材料、合同、名片上。免费域名不属于你，属于 DigitalPlat，不能作为品牌资产。

**邮件投递可靠性要求高的业务**。免费域名因为滥用历史，MX 记录配置不规范的情况普遍，邮件容易被 Gmail、Outlook 标记为垃圾邮件。做交易邮件、营销邮件，必须用自有域名并配齐 SPF/DKIM/DMARC。

**SEO 是核心流量来源的项目**。搜索引擎对免费域名的信任度低于独立域名，且免费域名上的内容质量参差不齐，整体权重低。靠 SEO 引流的项目，省域名钱是捡芝麻丢西瓜。

## 风险清单：免费域名的代价

把免费域名的风险列清楚，是为了让决策有依据，不是为了劝退。

**服务停运风险**。DigitalPlat Foundation 是一个小型非营利组织，FreeDomain 的运营依赖赞助和创始人个人投入。如果赞助断流、创始人退出、母域名（`dpdns.org` 等）被注册局撤销，所有子域名会一起失效。这种事在免费域名历史上发生过多次——Freenom 提供的 `.tk`、`.ml`、`.ga`、`.cf` 等免费 ccTLD 在 2023 年因为滥用问题被 Meta 起诉，最终整个 Freenom 服务停摆，ICANN 在 2024 年初终止了其注册资质，数百万网站一夜消失，许多小项目的域名至今无法恢复。FreeDomain 的风险结构类似——它依赖单一组织持有母域名，没有 ICANN 资质背书，没有商业兜底，只是规模比 Freenom 小一些，被滥用的概率也低一些。但"规模小"不等于"不会出事"，Freenom 当年也是从一个小项目做大的。

**域名被回收风险**。FreeDomain 的服务条款禁止滥用（钓鱼、垃圾邮件、恶意软件分发），违反条款的子域名会被回收。问题在于"滥用"的判定权在 DigitalPlat 手里，没有独立仲裁机制。如果你的子域名被误判或被举报，申诉渠道有限。另外，FreeDomain 要求每 180 天登录续订一次，忘记续订域名会被释放，别人可以抢注。

**SEO 劣势**。搜索引擎对免费域名整体信任度低，因为同一母域名下大量子域名质量参差不齐。Google 在 Search Central 文档里没有明确歧视免费域名，但实际排名表现上，独立域名普遍更好。如果你的项目依赖搜索引擎流量，这是一个隐性成本。

**邮箱不可用风险**。在 `yourname.dpdns.org` 上配置邮箱（MX 记录指向邮件服务商）技术上可行，但实际投递效果差。Gmail、Outlook、腾讯企业邮等主流邮件服务商对免费域名的邮件有较强的垃圾邮件过滤倾向，因为历史上这类域名被用于群发垃圾邮件的案例太多。即使你配齐了 SPF、DKIM、DMARC，仍然可能进垃圾箱。

**子域名抢注风险**。如果你注册了 `myblog.dpdns.org`，别人可以注册 `myblog-api.dpdns.org`、`myblog-login.dpdns.org` 这类近似子域名，用于钓鱼或社会工程攻击。这是共享母域名的固有风险，独立域名不存在这个问题。

**HTTPS 证书依赖 Cloudflare**。如果走 Cloudflare 代理，SSL 证书是 Cloudflare 签发的 Universal SSL，证书有效期为 1 年，自动续期。但如果某天你把 NS 从 Cloudflare 切走，证书会失效，需要自己重新签发。这个锁定效应要心里有数。

## 迁移路径：项目做大后怎么换域名

如果项目从 side project 演进到需要长期运营，迁移到付费域名的标准路径如下。

**第一步：买一个独立域名**。在 Cloudflare Registrar、Porkbun、Namecheap 这类注册商买一个 `.com`、`.org`、`.dev` 域名，年费 $10–$15。Cloudflare Registrar 是注册商成本价直销，没有加价，推荐。

**第二步：在新域名上复刻 DNS 配置**。在 Cloudflare 添加新域名，把旧域名上的所有 A、AAAA、CNAME、MX、TXT 记录原样复制到新域名。TTL 调短到 300 秒，方便后续切换。

**第三步：双域名并行运行一段时间**。让新域名和旧域名同时指向同一套服务，观察新域名的解析、HTTPS、邮件投递是否都正常。这个阶段建议至少跑两周，覆盖各种边缘情况。

**第四步：301 重定向旧域名到新域名**。在源站（或 Cloudflare 的 Redirect Rules）配置 301 永久重定向，把所有旧域名 URL 重定向到新域名的对应路径。这样旧域名的 SEO 权重会逐步转移到新域名，用户书签也不会失效。

```nginx
# Nginx 示例：旧域名 301 到新域名
server {
    listen 443 ssl;
    server_name myblog.dpdns.org;
    return 301 https://myblog.com$request_uri;
}
```

**第五步：更新所有外部引用**。GitHub 仓库的 README、社交媒体简介、名片、合同、邮件签名——所有出现旧域名的地方都换成新域名。这一步最容易遗漏，建议建一个 checklist 逐项核对。

**第六步：保留旧域名至少 6 个月**。不要立刻释放旧域名，让 301 重定向持续运行一段时间，给搜索引擎和用户充足的迁移时间。6 个月后可以释放，或者继续保留作为别名。

整个迁移过程的技术成本不高，主要工作量在"更新外部引用"这一步。所以决策时机很重要：项目早期用免费域名没问题，但一旦确认要长期运营，越早迁移成本越低。

## 实践建议

**域名安全**。启用 FreeDomain 账户的邮箱验证，定期登录检查域名状态。Cloudflare 账户开启两步验证。DNS API Token（如果用 Cloudflare API 自动化）按最小权限原则签发，不要给 Account 级别的编辑权限。强密码 + 密码管理器是基本操作。

**续订提醒**。FreeDomain 要求每 180 天续订一次，错过续订域名会被释放。建议在日历里设一个每 5 个月一次的循环提醒，留一个月缓冲期。

**DNS 缓存排查**。变更 DNS 后如果发现部分地区还是旧记录，先清本地缓存再排查：

```bash
# macOS
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder

# Linux (systemd-resolved)
sudo systemd-resolve --flush-caches

# Linux (nscd)
sudo service nscd restart

# Windows
ipconfig /flushdns
```

本地缓存清完还是旧的，就是 ISP 递归 DNS 的缓存问题，等 TTL 到期即可。可以用 `dig @1.1.1.1 yourdomain.com` 直接查 Cloudflare 递归 DNS 的结果，绕过本地 ISP 缓存。

**监控**。免费方案下，监控主要靠免费工具。UptimeRobot 提供 50 个监控点免费额度，5 分钟检查一次 HTTP 状态码，异常邮件告警。SSL 证书到期监控用 CertDB 或自己写脚本调 Cloudflare API 检查。这些不是 FreeDomain 的责任，是用户自己要做的运维工作。

**子域名规划**。即使主域名是 `myblog.dpdns.org`，也建议规划好子域名结构：`blog` 用作博客、`api` 用作 API、`static` 用作静态资源 CDN。不要把所有服务都堆在根域名上，子域名拆分有利于后续迁移和权限隔离。

## 社区参与和问题反馈

FreeDomain 是开源项目，社区参与渠道如下：

- **Telegram 群组**：`https://t.me/digitalplatdomain`，日常讨论和公告。
- **Discord 服务器**：`https://discord.gg/ma4RZzMmVW`，实时交流。
- **GitHub 仓库**：`https://github.com/DigitalPlatDev/FreeDomain`，提 Issue、PR、查源码。
- **滥用举报**：`abusereport@digitalplat.org`，发现钓鱼、垃圾邮件等滥用行为时举报。

遇到问题时的排查顺序：先查仓库 `documents/domains/faq.md` 和 `documents/tutorial/index.md`，再在 GitHub Issues 搜索类似问题，最后才考虑提新 Issue 或在社区求助。社区不是商业支持，没有人有义务回答你的问题，提问前先做功课是基本礼仪。

## 常见问题

**域名注册需要付费吗？**
不需要。FreeDomain 的注册、续订、NS 委托全部免费，没有任何隐藏费用。DigitalPlat 的运营成本由赞助覆盖。

**域名有使用期限吗？**
有。注册后每 180 天需要登录仪表盘续订一次，不续订域名会被释放。这是为了回收被遗弃的子域名，不是商业限制。

**支持 HTTPS/SSL 吗？**
支持，但需要通过 Cloudflare 代理实现。开启 Cloudflare 的"已代理"状态后，Universal SSL 自动签发证书，HTTPS 开箱即用。如果不用 Cloudflare，需要自己用 Let's Encrypt 签发证书。

**可以使用子域名吗？**
可以。你注册 `myblog.dpdns.org` 后，可以在 Cloudflare 上为它配置任意子域名（如 `www.myblog.dpdns.org`、`api.myblog.dpdns.org`），数量没有限制。

**如果域名被滥用怎么办？**
发邮件到 `abusereport@digitalplat.org` 举报。DigitalPlat 会对滥用行为进行处理，包括回收子域名。

## 相关资源

**官方链接**：

- 仪表盘：`https://dash.domain.digitalplat.org/`
- 域名平台：`https://domain.digitalplat.org/`
- GitHub 仓库：`https://github.com/DigitalPlatDev/FreeDomain`
- Telegram：`https://t.me/digitalplatdomain`
- Discord：`https://discord.gg/ma4RZzMmVW`
- 赞助：`https://hcb.hackclub.com/donations/start/digitalplat`

**项目内文档**：

- 教程：`documents/tutorial/index.md`
- FAQ：`documents/domains/faq.md`
- DNS 托管指南：`documents/domains/dns-hosting.md`

## 什么时候用，什么时候不用

把整篇文章收束成一个决策框架：

**用免费域名**：个人项目、demo、实验、内网穿透、教学。这些场景下，域名的稳定性不是核心约束，省下的 $12/年有边际效用。

**用付费域名**：商业产品、长期品牌、邮件业务、SEO 项目、需要合同约束的所有权。这些场景下，$12/年的成本相对于风险可以忽略。

FreeDomain 是一个值得尊敬的开源项目——它把"零成本拥有自定义域名"这件事做到了工程上可用、文档上完整、社区上活跃。但尊敬项目不等于无脑使用。理解它的技术本质（二级域名委托）、它的风险结构（依赖单一组织）、它的适用边界（非商业、非长期），才能用得其所。

如果你正在做一个 side project，想给它挂个域名又不想花钱，FreeDomain + Cloudflare 是当前最好的免费方案。如果你正在做一个想长期运营的产品，花 $12 买一个 `.com`，把 FreeDomain 留给下一个 side project。
