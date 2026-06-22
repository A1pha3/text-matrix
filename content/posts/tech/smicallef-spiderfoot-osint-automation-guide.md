---
title: "SpiderFoot 架构分析：200+ 模块的 OSINT 自动化引擎与 YAML 关联规则"
date: "2026-06-22T15:06:00+08:00"
slug: "smicallef-spiderfoot-osint-automation-guide"
categories: ["技术笔记"]
tags: ["OSINT", "安全工具", "威胁情报", "架构分析", "Python"]
description: "SpiderFoot 是一个开源 OSINT 自动化工具,核心架构是 200+ 模块通过 publisher/subscriber 模型解耦的爬虫网络,加上 v4.0 引入的 YAML 关联规则引擎把碎片组合成画像。"
---

# SpiderFoot 架构分析:200+ 模块的 OSINT 自动化引擎与 YAML 关联规则

## 核心判断

SpiderFoot 是一个**经典老牌 OSINT 自动化工具**(自 2012 年起开发),它真正的工程价值不在某个具体模块,而在**模块之间通过 publisher/subscriber 模型解耦的爬虫网络**--一个模块发现新实体(域名/IP/邮箱),发布事件;订阅该实体类型的其他模块被触发,产生新数据;数据再被发布,继续触发下一轮。

v4.0 引入的 **YAML 关联引擎** 把这种"碎片化数据收集"进一步升级成"数据-数据之间的判断":37 条预定义规则把"同一个目标在多源上呈现的同型信号"组合成结论(比如域名在 Shodan、HIBP、AlienVault 三个来源里同时被标黑 → 触发高风险规则)。

理解这两层(数据流层 + 关联判断层)就够了,SpiderFoot 的其他设计都是围绕这两层在转。

## 系统地图

```
                         ┌──────────────────────────────┐
                         │  Web UI (:5001)  /  CLI       │
                         │  sf.py -l 127.0.0.1:5001      │
                         └──────────────┬───────────────┘
                                        │ 启动扫描
                                        ▼
              ┌─────────────────────────────────────────────────┐
              │  Scan Engine (扫描引擎)                          │
              │  - 接受目标(域名/IP/邮箱/用户名/CIDR/...)        │
              │  - 维护事件队列                                  │
              │  - 派发到模块                                    │
              └────────┬────────────────────────────────────────┘
                       │ event bus
       ┌───────────────┼───────────────┬──────────────┐
       ▼               ▼               ▼              ▼
   Module A        Module B        Module C       Module D
   (DNS 查询)      (AbuseIPDB)     (crt.sh)       (Shodan)
       │               │               │              │
       └─publish→ event queue ←subscribe─┘
                       │
                       ▼
              ┌────────────────────────┐
              │  Correlation Engine    │
              │  YAML rules (37 条)    │
              │  把多源数据关联判断    │
              └────────────────────────┘
                       │
                       ▼
              ┌────────────────────────┐
              │  SQLite                │
              │  CSV / JSON / GEXF 导出│
              └────────────────────────┘
```

- **Web UI / CLI**:Python 内置 HTTP server,Web UI 走 React 风格 SPA
- **扫描引擎**:接受目标 → 派发初始事件 → 模块产新事件 → 持续触发直到队列空
- **200+ 模块**:分两类--**内部模块**不调外部 API(纯字符串/正则/被动 DNS),**外部模块**调第三方 API(部分要 key)
- **关联引擎**:YAML 规则,新数据进来时匹配规则,匹配上就触发预定义标签
- **存储**:SQLite 后端,支持自定义 SQL 查询;导出 CSV / JSON / GEXF(给 Gephi 这类可视化工具)

## 边界拆分

### 输入目标类型

| 类型 | 示例 |
| --- | --- |
| IP 地址 | `8.8.8.8` |
| 域名 / 子域名 | `evilcorp.com`、`vpn.evilcorp.com` |
| 主机名 | `mail.evilcorp.com` |
| 子网(CIDR) | `203.0.113.0/24` |
| ASN | `AS15169` |
| 邮箱 | `cto@evilcorp.com` |
| 电话 | `+1-555-1234` |
| 用户名 | `evilcorp_admin` |
| 人名 | `John Smith` |
| 比特币地址 | `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa` |

### 模块分类:内部 vs 外部

- **内部模块**:DNS Brute-forcer、Bitcoin Finder、Email Extractor、Country Name Extractor、Base64 Decoder、CMSeeK wrapper--不需 API key,纯本地处理
- **外部模块**(部分要 key):
  - **免费层**:Abuse.ch、Abusix、AdGuard DNS、Ahmia(暗网)、AlienVault OTX、Archive.org、crt.sh、Cloudflare DNS、HIBP free、BitcoinAbuse
  - **Tiered API**(免费额度 + 付费):Shodan、HaveIBeenPwned、GreyNoise、SecurityTrails、Censys、C99、BGPView
  - **商业 API**:Dehashed、Clearbit

### 数据形态:active vs passive

- **Passive**:只查公开数据库/历史数据(Shodan、HIBP、crt.sh、Archive.org)- 不接触目标,合规风险低
- **Active**:直接对目标发请求(DNS zone transfer、port scan、banner grab、dark web search、TOR 集成)--可能触发目标侧日志,需要授权

## 关键机制

### 机制 1:Publisher/Subscriber 解耦

模块 A 处理完数据,调用 `notifyListeners(event_type, data)`,监听 `event_type` 的所有模块被触发,各自处理。

举个例子,以 `evilcorp.com` 起手:

1. **DNS Raw Records** 模块 → 解析 A/MX/NS/TXT → publish 多个 IP + 多个 host
2. **AbuseIPDB** 订阅 IP 类型 → 对每个 IP 调 AbuseIPDB → publish `blacklisted_ip`
3. **Shodan** 订阅 IP 类型 → 调 Shodan → publish 开放端口 + banner
4. **HIBP** 订阅 email 类型(从 TXT 记录 / web 抓取提取出 email 后)→ 查 breach
5. **crt.sh** 订阅域名类型 → 查证书透明日志 → 发现 `vpn.evilcorp.com` / `dev.evilcorp.com` → 重新触发上述链路
6. **关联引擎** 在每轮事件进来时检查 37 条规则 → 匹配上就标关联标签

整条链路是**自动递归**的--一个发现会触发下一层发现,直到所有订阅者跑完或撞上限。

### 机制 2:YAML 关联规则(v4.0 引入)

README 给了 `correlations/template.yaml`,规则结构是声明式的:

```yaml
- name: "Domain in multiple blacklists"
  watch:
    - "Blacklisted IP Address"
  meta:
    risk: "High"
    description: "Domain resolves to IP found in multiple blacklists"
  required:
    - "Blacklisted IP Address" >= 2 different sources
```

含义:当同一个域名下出现 ≥ 2 个不同来源标记的 `Blacklisted IP Address`,关联引擎打 "High" 风险标签。

`required` 字段声明触发条件,`watch` 是触发的事件类型,`meta` 是规则的元信息。37 条预定义规则覆盖常见的"多源同型"模式:

- 域名挂在多个黑名单
- ASN 下多个 IP 被黑
- 邮箱关联多个 breach
- 比特币地址在多个诈骗库
- TLS 证书过期 + 子域接管
- ......

这套机制的价值:**模块只管收集事实,关联引擎管判断**--职责分离让加新模块和加新规则可以独立进行。

### 机制 3:External Tool 集成

README 提到 SpiderFoot 可以**调用外部工具**:`DNSTwist`(typosquatting)、`Whatweb`(技术栈指纹)、`Nmap`(端口扫描)、`CMSeeK`(CMS 漏洞)。

集成方式是在目标系统装好这些工具,SpiderFoot 检测到二进制就调用,检测不到就跳过--没有硬依赖,但装了能让模块集合变大。

### 机制 4:可视化与导出

- **GEXF 导出**:Gephi 兼容的图格式,实体和关联都画成图--能直观看到"邮箱 → 域名 → IP → ASN"的关联网
- **CSV / JSON 导出**:给 SIEM 喂数据(Splunk、ElasticSearch)
- **REST export**:SpiderFoot HX 商业版特性

### 机制 5:TOR 集成

支持走 TOR 出口节点做暗网搜索(Ahmia 模块)。需要本地跑 tor daemon,SpiderFoot 通过 SOCKS proxy 走流量。

## 任务流案例

### 案例:域名为目标的端到端扫描

```bash
python3 ./sf.py -s evilcorp.com -m all -F JSON -o results.json
```

内部流程:

```
T0: 提交 evilcorp.com 目标
T1: DNS Raw Records 模块 → 解析 A 记录 203.0.113.42、MX mail.evilcorp.com、NS ns1.evilcorp.com
T2: Web scraping 模块 → 抓 evilcorp.com 主页 → 提取 email cto@evilcorp.com, 提取地址字符串
T3: crt.sh 模块 → 证书透明日志 → 发现 vpn.evilcorp.com, dev.evilcorp.com, admin.evilcorp.com
T4: 子域名被加入事件队列,递归触发 T1-T3(对每个子域再做一遍)
T5: AbuseIPDB/Shodan 对所有解析出的 IP 标记 + 返回 open ports/banners
T6: HIBP 对 cto@evilcorp.com 查询 breach → 命中 3 个 breach
T7: Bitcoin Finder 扫描抓到的网页 → 找出网页中提到的 bitcoin address
T8: 关联引擎对所有事件匹配 37 条规则
   - "Domain in multiple blacklists":203.0.113.42 在 2 个黑名单 → 触发
   - "Email in multiple breaches":cto@evilcorp.com 命中 3 个 → 触发
   - "Subdomain hijack exposure":旧 TLS 证书 + 失效 NS → 触发
T9: 关联标签汇总到扫描结果页
T10: 用户导出 GEXF → Gephi 可视化
```

### 案例:多目标递归

```bash
python3 ./sf.py -s 203.0.113.0/24 -m sfp_abuseipdb,sfp_shodan
```

子网扫描 + 仅启用 2 个模块--可以控制扫描的"广度"和"深度",避免一次扫描跑出 100 万个事件。

## Benchmark/测什么、不能推出什么

README **没有**提供内部 benchmark。但**实测经验**(用户社区 + 文档提示):

- **全模块 1 个域名**:30 分钟到 2 小时,取决于网络延迟和外部 API rate limit
- **仅启用免费模块**:无 API key 成本,但 200 个模块中很多是付费 API 限速的 tier
- **GEXF 导出文件大小**:复杂目标 1-50 MB,导入 Gephi 可能要 RAM
- **关联引擎规则匹配**:是事件触发的,不是定时跑,数据量大时会有匹配延迟

不能推出的:

- **不能**保证全覆盖--SpiderFoot 看不到的"暗数据"(私有数据库、付费情报源)需要付费工具或 SpiderFoot HX
- **不能**替代主动渗透测试--SpiderFoot 是 recon(侦察)阶段工具,不是 exploitation
- **不能**当 SIEM 用--它做扫描,不做 7×24 监控(那也是 HX 的领域)

## 采用建议

### 适合

- **渗透测试 recon 阶段**--在主动测试前摸清目标暴露面
- **红蓝对抗 / 蓝队防御**--自查自己组织暴露了什么
- **威胁情报研究**--关联 IOC(Indicator of Compromise)
- **SOC analyst 调查**--拿到一个 IP / email / 域名,跑一遍 SpiderFoot 拼出画像
- **OSINT 学习**--200+ 模块本身就是 OSINT 资料库,挨个看一遍能学到大量"哪里能找到什么"

### 不适合

- **实时监控**--这是扫描工具,不是监控工具。需要监控的去看 [SpiderFoot HX](https://www.spiderfoot.net/hx) 商业版
- **多租户 / 多人协作**--开源版是单用户
- **APT 级威胁情报**--开源情报源覆盖不到的,需要商业源
- **暗网大规模爬取**--TOR 性能受限,Ahmia 等引擎只覆盖公开 onion 搜索引擎

### 上手

```bash
# 稳定版(v4.0)
wget https://github.com/smicallef/spiderfoot/archive/v4.0.tar.gz
tar zxvf v4.0.tar.gz
cd spiderfoot-4.0
pip3 install -r requirements.txt
python3 ./sf.py -l 127.0.0.1:5001

# 开发版(master)
git clone https://github.com/smicallef/spiderfoot.git
cd spiderfoot
pip3 install -r requirements.txt
python3 ./sf.py -l 127.0.0.1:5001
```

打开 http://127.0.0.1:5001,New Scan → 选目标类型(域名/IP/邮箱/...)→ 选模块(默认 all)→ 启动 → 实时看事件流。

### 必读

1. **README 的 "WRITING CORRELATION RULES" 段** + `correlations/template.yaml`--自己写关联规则的范式
2. **README 的 "MODULES / INTEGRATIONS" 大表**--200+ 模块清单 + 哪些要 key 哪些免费
3. **`correlations/` 目录**--37 条预定义规则的 source of truth
4. **商业版 [SpiderFoot HX](https://www.spiderfoot.net/hx) 对比表**--确认自己用开源版就够,还是需要商业能力

### 替代品对比

| 工具 | 定位 | 差异 |
| --- | --- | --- |
| **theHarvester** | 邮件/子域名收集 | 轻量,只覆盖 passive email + subdomain,无关联引擎 |
| **Recon-ng** | 模块化 recon 框架 | 类似 SpiderFoot 但模块少很多,基于 Python |
| **Amass** | 子域枚举专家 | 主打子域,深度最强,其他维度不如 SpiderFoot |
| **SpiderFoot** | 200+ 模块广度 + 关联引擎 | 覆盖面最广,关联判断独有 |

## 法律与伦理边界

- **Passive 模块**(Shodan/HIBP/crt.sh/Archive.org)合规风险低--只查公开数据库
- **Active 模块**(DNS zone transfer、port scan、banner grab)需要**书面授权**--无授权扫描可能违反 CFAA(美国)、网络安全法(中国)、Computer Misuse Act(英国)等
- **暗网扫描**(Ahmia + TOR)需要明确合规授权--许多司法管辖区对访问暗网内容有特殊规定
- **GDPR / 隐私法**--SpiderFoot 收集的数据可能含个人数据(PII),需按当地法规处理

工具是中性的,**使用方式决定合规性**。
