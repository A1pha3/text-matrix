+++
github_repo = "trimstray/the-book-of-secret-knowledge"
source_key = "gh:trimstray/the-book-of-secret-knowledge"
date = '2026-05-22T15:54:25+08:00'
draft = false
title = 'The-Book-of-Secret-Knowledge：程序员技术手册合集'
slug = 'the-book-of-secret-knowledge-developer-swiss-army-knife'
description = 'trimstray/the-book-of-secret-knowledge 是一份巨型单文件 README 技术索引，按 CLI/GUI/Web 工具、系统与网络、容器编排、手册教程、博客播客等章节收录上千条精选链接，面向系统与网络管理员、DevOps、渗透测试者与安全研究员。'
categories = ['技术笔记']
tags = ['DevOps', '工具', '教程', 'Linux']
+++

# The-Book-of-Secret-Knowledge：程序员技术手册合集

搜一条命令、找一个工具，结果往往散落在博客、文档和论坛里，下次要用还得再搜一遍。trimstray 维护的 [the-book-of-secret-knowledge](https://github.com/trimstray/the-book-of-secret-knowledge) 就是冲着这个麻烦来的：作者把自己日常工作里反复查阅的清单、手册、速查表和命令，收进同一个 README，按章节排好，随时可查、可检索。

## 项目概览

仓库本体就是一份 README：约 4400 行、207 KB，2018 年 6 月创建，MIT 协议开源，接受社区 PR。作者 trimstray（Michał Ży）自述，这些材料都来自他每天的工作。截至 2026 年 9 月，仓库已有超过 24 万 stars，是 GitHub 上最受欢迎的 awesome 类清单之一。

README 开头的 For whom 一节写得很直白：人人可用，但主要面向系统与网络管理员、DevOps、渗透测试者与安全研究员。

内容分两条线。一条是**链接索引**，从 CLI 工具到教程、播客，每条一两句话加官方链接；另一条是**可执行命令集**，Shell One-liners 等三章直接给命令，拿来就能敲。检索时两条线互相补位，后文的案例会展示它们怎么配合。

## 内容地图：15 个章节

README 按官方目录列出 15 个主章节，前 12 个是链接索引，后 3 个是命令集：

| 章节 | 形态 | 收录内容 |
|------|------|----------|
| CLI Tools | 链接索引 | Shell 与插件、文本编辑器、文件与目录、网络/DNS/HTTP/SSL、安全审计、系统诊断、日志分析、数据库等命令行工具 |
| GUI Tools | 链接索引 | 终端模拟器、浏览器、密码管理器、IM 客户端等图形界面工具 |
| Web Tools | 链接索引 | 在线 SSL 检查、HTTP 头校验、DNS 查询、编解码与正则测试、CVE/Exploit 库、私有搜索引擎等 |
| Systems/Services | 链接索引 | 操作系统、HTTP/DNS 服务、安全加固指南 |
| Networks | 链接索引 | 网络工具与实验环境 |
| Containers/Orchestration | 链接索引 | Docker/K8s 的命令、Web 工具、安全与最佳实践 |
| Manuals/Howtos/Tutorials | 链接索引 | Shell、Python、sed/awk、\*nix 与系统加固等教程 |
| Inspiring Lists | 链接索引 | 其他 awesome 清单与资源合集 |
| Blogs/Podcasts/Videos | 链接索引 | 值得订阅的技术博客、播客与视频 |
| Hacking/Penetration Testing | 链接索引 | Metasploit、Burp Suite、sqlmap 等渗透工具，字典与漏洞资源，靶场与 CTF 平台 |
| Your daily knowledge and news | 链接索引 | 日常技术资讯源 |
| Other Cheat Sheets | 链接索引 | 更多领域的速查表 |
| Shell One-liners | 命令集 | 按 lsof、find、ssh、tcpdump、openssl 等工具分小节，每小节给出具体场景的命令，是全文件篇幅最大的板块 |
| Shell Tricks | 命令集 | Shell 使用技巧 |
| Shell Functions | 命令集 | 可复用的 Shell 函数 |

小标题多是"对象 + 用途"，想找哪一类，从目录就能直接跳到对应列表。

## 如何查阅

### 前置条件

本机装有 `git`，以及 `rg` 或 `grep` 任一文本检索工具。只在网页上看可以不装；想把它当本地速查手册用，先执行下面的克隆步骤。

### 克隆与验证

```bash
git clone https://github.com/trimstray/the-book-of-secret-knowledge.git
cd the-book-of-secret-knowledge

# 感受体量：约 4400 行、207 KB
wc -lc README.md

# 列出章节骨架，对照上面的表格
rg '^#{2,4} ' README.md
```

执行后应看到一份章节标题列表。若 `rg` 无输出，多半是本机没装 ripgrep，改用 `grep -E '^#{2,4} ' README.md`。

### 检索定位

```bash
# 分页浏览整份目录
less README.md

# 查安全工具：nmap 和 Metasploit 在 CLI Tools 与 Hacking 两章都有收录
rg -i 'nmap|metasploit' README.md

# 只抽取某个章节的条目
sed -n '/^#### CLI Tools/,/^#### GUI Tools/p' README.md
```

`sed` 抽出的是带 HTML 标记的原始条目，观感不如渲染后的网页，检索足够用。检索链路始终是：关键词 → 章节 → 条目给出的官方出处。

## 一次真实检索：查谁占着 443 端口

接手一台陌生服务器，想知道哪个进程在监听 443。翻到 Shell One-liners 的 lsof 小节，答案就在那里：

```bash
# 查看使用特定端口的进程
lsof -i tcp:443
```

同一小节还列着十来条变体——列出全部监听端口、按用户查打开的文件、找最大的十个已打开文件——一条命令不够用时可以就地换招。

如果任务超出一条命令的范围，比如要做持续的端口审计，再顺着 CLI Tools 或 Networks 章节的链接挑专门工具。命令集负责"现在就能敲"，链接索引负责"下一步去哪"，两条线在一次排查里先后出场。

## 采用建议

- **运维与网络工程师**：克隆下来当本地速查手册，配合 `rg` 按任务查命令；`Systems/Services` 的加固指南值得通读一遍。
- **渗透测试与安全研究**：`Hacking/Penetration Testing` 一章从工具、字典到靶场和 CTF 平台都齐了，但相关命令务必只在自有或已授权的环境里执行，不要对他人系统操作。
- **初学者**：先过 `Manuals/Howtos/Tutorials` 和 `Blogs/Podcasts/Videos` 两章建立技术地图；注意它给出的是教程出处而非教程本身，学习仍要按链接走。

两点提醒。仓库最后一次推送是 2024 年 11 月，之后基本没有更新——收录的以经典稳定工具为主，当作速查手册不受影响，但想追新工具得另寻来源。链接索引类章节只给出处、不给用法，具体怎么用要二次跳转；命令集章节的命令够直接，却没有原理讲解，出了错还得靠手册和 `man` 页。
