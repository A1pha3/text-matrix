---
title: "The Book of Secret Knowledge：运维安全从业者的终极工具索引"
date: "2026-05-23T03:05:00+08:00"
slug: "the-book-of-secret-knowledge-sysadmin-toolkit"
description: "The Book of Secret Knowledge 是 trimstray 在 GitHub 上维护的一个巨型工具索引仓库，收录 CLI/GUI 工具、Web 服务、渗透测试、系统加固等领域的精选资源，面向系统管理员、DevOps 和安全研究员。本文从项目定位、章节结构、核心亮点三个维度进行全面解读，并给出阅读建议与适用边界分析。"
draft: false
categories: ["技术笔记"]
tags: ["DevOps", "安全工具", "运维", "开源", "网络工具"]
---

## 项目概览与定位

**The Book of Secret Knowledge**（简称 TBSK）是 GitHub 用户 [trimstray](https://github.com/trimstray) 维护的一个知识型仓库，核心内容是一份超长分类清单——把作者日常工作中用到的各类工具分门别类整理成一个页面。

这个项目的本质是一个**"工具索引"，而不是一个框架、库或命令行工具**。它不提供安装程序，不提供 API，也没有可运行的代码。它做的事只有一件：**帮你在最短时间内找到最合适的工具**，至于怎么用，那是你的事。

README 开篇有一句话道出了项目的初衷：

> *"Knowledge is powerful, be careful how you use it!"*

---

## 为什么值得关注

### 1. 收录工具质量较高

作者在 CONTRIBUTING 指南里明确写道：

```diff
+ This repository is not meant to contain everything but only good quality stuff.
```

不是什么都往里塞，只收录经过筛选的优质资源。这个定位保证了每一类工具下列出的条目都有基本的可用性，而不是谷歌搜索结果的无脑堆砌。

### 2. 由实战经验驱动，而非 SEO 驱动

大多数"awesome-xxx"类列表的问题在于：谁都能提交 PR，排名靠的是 star 数量而非实用性。TBSK 的维护者有明确的筛选意图，目录结构直接对应实战场景——网络、安全、容器、审计——而不是凑一个"最全列表"的篇幅。

### 3. 覆盖面极广，跨多个技术领域

作为一个运维/安全背景的从业者，你通常需要跨多个领域找工具：网络扫描、流量分析、SSL 检测、日志审计、容器安全、Web 漏洞扫描……TBSK 把这些分散在十多个章节里，每章都是一个完整的子目录，覆盖从"你知道这个工具存在"到"你知道该在什么场景用它"的认知路径。

---

## 章节结构纵览

以下是 README 中 14 个主要章节的分类逻辑与代表性工具。

> 注：以下工具列表均直接来自 README 的原始收录，顺序与原文保持一致。标注 **\*** 的链接表示该 URL 暂时不可用。

### CLI Tools — 命令行工具集

这是全仓库最厚的章节，横跨十几个子类。

**Shell 与插件**

- [GNU Bash](https://www.gnu.org/software/bash/) — POSIX 兼容 Shell
- [Zsh](https://www.zsh.org/) — 交互式 Shell，有强大的插件生态
- [Oh My ZSH!](https://ohmyz.sh/) — Zsh 配置管理框架
- [Starship](https://github.com/starship/starship) — 跨平台 Rust 提示符
- [fzf](https://github.com/junegunn/fzf) — 命令行模糊搜索

**文件管理器**

- [ranger](https://github.com/ranger/ranger) — Vim 风格的终端文件管理器
- [nnn](https://github.com/jarun/nnn) — 极轻量文件管理器

**网络工具**（极长，包含 50+ 工具的子类）

- [nmap](https://nmap.org/) — 端口扫描与网络发现
- [masscan](https://github.com/robertdavidgraham/masscan) — 异步高速端口扫描
- [RustScan](https://github.com/RustScan/RustScan) — 目标是比 nmap 更快的替代
- [mtr](https://github.com/traviscross/mtr) — traceroute + ping 组合
- [tcpdump](https://www.tcpdump.org/) — packet analyzer
- [Wireshark](https://www.wireshark.org/) — GUI 网络协议分析仪
- [Scapy](https://scapy.net/) — Python 封包/解包库

**DNS 专项**

- [massdns](https://github.com/blechschmidt/massdns) — 高性能 DNS 批量查询
- [Subfinder](https://github.com/subfinder/subfinder) — 子域名发现
- [Amass](https://github.com/OWASP/Amass) — OWASP 子域名枚举工具
- [dnscrypt-proxy 2](https://github.com/jedisct1/dnscrypt-proxy) — 加密 DNS 代理

**HTTP 负载与测试**

- [wrk](https://github.com/wg/wrk) — HTTP benchmark 工具
- [wrk2](https://github.com/giltene/wrk2) — 恒定吞吐版 wrk
- [Vegeta](https://github.com/tsenart/vegeta) — Go 编写的恒定吞吐负载测试
- [Siege](https://www.joedog.org/siege-home/) — HTTP 负载测试
- [SlowHTTPTest](https://github.com/shekyan/slowhttptest) — 应用层 DoS 模拟

**SSL/TLS 检测**

- [testssl.sh](https://github.com/drwetter/testssl.sh) — 纯 Shell 的 TLS 检测
- [SSLyze](https://github.com/nabla-c0d3/sslyze) — Python SSL 扫描库
- [mkcert](https://github.com/FiloSottile/mkcert) — 本地可信证书零配置工具

**数据库工具**

- [osquery](https://github.com/osquery/osquery) — SQL 接口的系统监控框架
- [pgcli](https://github.com/dbcli/pgcli) — Postgres CLI（自动补全 + 语法高亮）

**系统诊断与调优**

- [strace](https://github.com/strace/strace) — Linux 系统调用追踪
- [bpftrace](https://github.com/iovisor/bpftrace) — eBPF 高层追踪语言
- [sysdig](https://github.com/draios/sysdig) — 容器感知系统探索工具
- [FlameGraph](http://www.brendangregg.com/flamegraphs.html) — stack trace 可视化
- [htop](https://github.com/hishamhm/htop) — 交互式进程查看器
- [GoAccess](https://goaccess.io/) — 实时 Web 日志分析

---

### GUI Tools — 图形界面工具集

相对于 CLI 章节的深度覆盖，GUI 工具章节更偏向"你知道有这个工具存在"层面的普及。

**终端模拟器**

- [Guake](https://github.com/Guake/guake) — GNOME 下拉式终端
- [Kitty](https://sw.kovidgoyal.net/kitty/) — GPU 渲染终端，支持图片显示
- [Alacritty](https://github.com/alacritty/alacritty) — OpenGL 终端模拟器

**密码管理**

- [KeePassXC](https://keepassxc.org/) — 开源密码管理器
- [Bitwarden](https://bitwarden.com/) — 开源密码同步服务
- [Vaultwarden](https://github.com/dani-garcia/vaultwarden/) — Rust 版 Bitwarden 兼容服务

**加密通讯**

- [Signal](https://www.signal.org/) — 端到端加密通讯
- [Matrix](https://matrix.org/) — 去中心化实时通讯协议

---

### Web Tools — 在线服务与检测工具

这个章节的价值在于把大量"只需要用一次"的在线工具做了归类，省去每次都去搜索的麻烦。

**SSL/TLS 在线检测**

- [SSL Labs Server Test](https://www.ssllabs.com/ssltest/) — 最权威的 SSL 配置检测
- [badssl.com](https://badssl.com/) — 测试客户端对各种错误 SSL 配置的容忍度
- [cipherli.st](https://github.com/RaymiiOrg/cipherli.st) — 各服务器软件的强加密配置模板

**DNS 查询**

- [DNSdumpster](https://dnsdumpster.com/) — DNS 枚举与可视化
- [Security Trails](https://securitytrails.com/) — DNS 与安全数据 API
- [crt.sh](https://crt.sh/) — 证书透明度日志搜索

**漏洞与威胁情报**

- [CVE Mitre](https://cve.mitre.org/) — 官方 CVE 数据库
- [Exploit DB](https://www.exploit-db.com/) — 公开漏洞与 POC 归档
- [Shodan](https://www.shodan.io/) — 联网设备搜索引擎
- [Censys](https://censys.io/) — 互联网资产发现与安全分析

**隐私与加密**

- [Panopticlick](https://panopticlick.eff.org/) — 浏览器指纹检测
- [Have I been pwned?](https://haveibeenpwned.com/) — 数据泄露查询

---

### Systems/Services — 系统与服务

**HTTP 服务**

- [Varnish Cache](https://varnish-cache.org/) — HTTP 缓存加速
- [OpenResty](https://openresty.org/en/) — Nginx + LuaJIT Web 平台
- [HAProxy](https://www.haproxy.org/) — TCP/HTTP 负载均衡器

**DNS 服务**

- [Unbound](https://nlnetlabs.nl/projects/unbound/about/) — 递归 DNS 解析器（支持 DNS-over-TLS）
- [PowerDNS](https://www.powerdns.com/) — 权威 DNS 服务器

**安全加固**

- [Pi-hole](https://github.com/pi-hole/pi-hole) — DNS 级广告拦截
- [Maltrail](https://github.com/stamparm/maltrail) — 恶意流量检测系统

---

### Networks — 网络

- [NetBox](https://github.com/digitalocean/netbox) — IPAM 与数据中心基础设施管理
- [CapAnalysis](https://www.capanalysis.net/ca/) — PCAP 可视化分析

---

### Containers/Orchestration — 容器与编排

**编排工具**

- [Traefik](https://traefik.io/) — 云原生反向代理
- [Kong](https://github.com/Kong/kong) — API Gateway
- [Portainer](https://github.com/portainer/portainer) — Docker 可视化管理

**安全**

- [Trivy](https://github.com/aquasecurity/trivy) — 容器漏洞扫描（CI 友好）
- [docker-bench-security](https://github.com/docker/docker-bench-security) — Docker 安全基线检查
- [Harbor](https://goharbor.io/) — 云原生镜像仓库

**学习资源**

- [kubernetes-the-hard-way](https://github.com/kelseyhightower/kubernetes-the-hard-way) — 在 GCP 上手动搭 K8s（最接近生产的学习路径）
- [kubernetes-failure-stories](https://github.com/hjacobs/kubernetes-failure-stories) — 公开的 K8s 生产故障案例汇编

---

### Manuals/Howtos/Tutorials — 手册与教程

这一章与其说是"工具"，不如说是"学什么"，收录了大量高质量的学习资源。

**Shell 与命令行**

- [pure-bash-bible](https://github.com/dylanaraps/pure-bash-bible) — 纯 Bash 替代外部命令的技巧集合
- [the-art-of-command-line](https://github.com/jlevy/the-art-of-command-line) — 一页纸掌握命令行
- [Shell Style Guide](https://google.github.io/styleguide/shellguide.html) — Google Shell 编码规范

**Linux 与网络**

- [strace-little-book](https://github.com/NanXiao/strace-little-book) — strace 入门
- [linux-tracing-workshop](https://github.com/goldshtn/linux-tracing-workshop) — Linux tracing 工具实战
- [http2-explained](https://github.com/bagder/http2-explained) — HTTP/2 详细解释
- [http3-explained](https://github.com/bagder/http3-explained) — HTTP/3 与 QUIC 协议文档

**系统加固**

- [The Practical Linux Hardening Guide](https://github.com/trimstray/the-practical-linux-hardening-guide) — Linux 加固指南
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks/) — 100+ 技术的安全配置基准（免费 PDF）

**Web 安全**

- [OWASP WSTG](https://github.com/OWASP/wstg) — Web 安全测试指南
- [API-Security-Checklist](https://github.com/shieldfy/API-Security-Checklist) — API 安全设计清单

---

### Hacking/Penetration Testing — 渗透测试

这个章节没有在 README 中详细展开工具列表，而是通过" inspiring lists"的形式将资源归类，具体工具散落在前面的 CLI Tools 和 Web Tools 章节中。

---

### Shell One-liners / Tricks / Functions

TBSK 收录了大量实战中沉淀下来的单行命令、Shell 技巧和函数。这些内容对于需要快速完成特定任务（比如从日志里提取信息、写一个快速监控脚本）的工程师来说，往往比完整的工具集更实用。

---

## 核心亮点分析

### 工具选品逻辑：以"任务"而不是以"工具名"分类

大多数工具列表是按工具名首字母排序或者按"最受欢迎"排序。TBSK 按任务场景分类——DNS、HTTP 压测、SSL 检测、日志分析——让读者在遇到具体问题时直接按图索骥，而不是在几百个工具里大海捞针。

### 分类深度不一，但每一类都尽量给出最优解

作者对某些领域的覆盖极深（如网络工具下的 HTTP 压测子章节收录了 20+ 工具），但对另一些领域的覆盖较浅。这是筛选策略的代价，不是缺陷：作者在 CONTRIBUTING 里明确说了"只收录优质资源"，而不是"做最全列表"。每一类工具的深度取决于该领域的工具密度和作者的实际使用经验。

### 维护活跃度尚可

仓库没有详细的更新日志，但从 RSS feed 可以追踪提交历史。最近的提交（2026 年初）显示维护者仍在处理 dead link 和新工具收录。

---

## 适用边界

**适合用这本书的人：**

- 系统/网络/DevOps 工程师，遇到问题时需要快速找到合适的工具
- 安全研究员需要一个经过筛选的工具索引，而不是去各大博客里自己筛选
- 初中级工程师想了解"业界成熟方案有哪些"，通过章节结构建立全局认知

**不适合用这本书的人：**

- 想找某个具体问题的完整解决方案（这本书是索引，不是教程）
- 想学某个工具的用法（需要去该工具的文档或专门教程）
- 需要每类工具都有深度 benchmark 或性能对比（这本书不提供这些）

---

## 如何使用这本书

### 场景一：遇到具体问题，快速查找

```
问题：需要找一个工具来检测 SSL 配置是否有漏洞
→ 进入 Web Tools → SSL/Security 章节
→ 看到 SSL Labs Server Test、testssl.sh、Cipherli.st
→ 选一个直接用
```

### 场景二：建立某领域的全局认知

```
想了解"HTTP 压测有什么工具可选"
→ 进入 CLI Tools → Network (HTTP) 子章节
→ 对照表：
  - wrk / wrk2 — 恒定吞吐，精准延迟
  - Vegeta — Go 版，功能相近
  - Siege — 偏向回归测试
  - SlowHTTPTest — 专门测 DoS 边界
→ 根据场景选一个
```

### 场景三：贡献或扩展

项目接受 PR，但要求遵循 CONTRIBUTING 指南的质量标准。如果你想添加新工具，建议先确认该工具在同类中确实有代表性，而不是凑数。如果发现 dead link，可以提 issue 或直接 PR 修改。

---

## 总结

The Book of Secret Knowledge 不是一个会让你"Wow"的新技术框架，而是一个帮你**少重复造轮子**的日常参考手册。它把一个资深运维/安全工程师的实战工具箱做了系统性归档，让你不用每次遇到问题都去搜索"what is the best tool for xxx"，而是直接翻这个目录找到方向。

对于刚入行的工程师，这本书是一个很好的"认知地图"——让你知道在这个行业里，每个领域的成熟方案大概是什么样的。对于资深工程师，它更像一本字典——不需要每次都翻，但知道它在那里，遇到了新场景就知道去哪里查。

GitHub：https://github.com/trimstray/the-book-of-secret-knowledge