---
title: "The Book of Secret Knowledge：开发者/运维/安全人员知识锦集"
date: "2026-05-23T15:30:00+08:00"
lastmod: "2026-09-25T12:00:00+08:00"
slug: the-book-of-secret-knowledge-developer-sysadmin-resource
github_repo: "trimstray/the-book-of-secret-knowledge"
source_key: "gh:trimstray/the-book-of-secret-knowledge"
description: "GitHub 24.6 万 stars 的技术知识锦集，一份 4400 多行的巨型 README 收录约 900 个外部资源——手册、速查表、博客、技巧、单行命令、命令行工具和 Web 工具，涵盖 Linux、DevOps、网络安全等领域。"
tags: ["Awesome List", "DevOps", "Security", "Linux"]
categories: ["技术笔记"]
author: 钳岳星君
---

[trimstray/the-book-of-secret-knowledge](https://github.com/trimstray/the-book-of-secret-knowledge) 真正特别的地方，不是 24.6 万颗星，而是形态：整个仓库就是一份 4400 多行的 README，把系统管理员、运维、渗透测试人员日常工作里"需要但记不住"的知识——手册、速查表、单行命令、工具清单——收进了一个可以 `grep` 的文本文件里。作者从 2018 年开始维护，最后一次提交停在 2024 年 11 月，但收录的对象大多是 lsof、nmap、tcpdump 这类几十年稳定的老牌 Unix 工具，今天翻开仍然可用。

## 一份会自己长大的操作手册

仓库顶部的座右铭是 *"Knowledge is powerful, be careful how you use it!"*。作者在 "What is it" 一节的自述是：这是"我每天工作中用到的各种材料和工具的集合"，"对我来说是一个无价的知识来源，我经常回头翻"。它一开始就不是给访客看的展览品，而是作者自己的工作手册，顺手放了出来。

受众一节写得很直白：

> "For everyone, really. Here everyone can find their favourite tastes. But to be perfectly honest, it is aimed towards System and Network administrators, DevOps, Pentesters, and Security Researchers."
> — 官方 README

翻译过来：谁都能翻，但说实话，它面向的是系统与网络管理员、DevOps、渗透测试人员和安全研究员。如果你日常要和 Linux 服务器打交道、做自动化运维或者安全分析，这本书值得放在手边。

## 十五个章节的地图

README 的目录列了 15 个主章节。按内容性质，大致可以分成四组：

| 分组 | 章节 | 收录内容 |
|------|------|----------|
| 工具与软件 | CLI Tools、GUI Tools、Web Tools | 命令行、图形界面、在线三类工具，每条附一句话说明 |
| 基础设施 | Systems/Services、Networks、Containers/Orchestration | 系统/服务、网络、容器与编排方向的资源 |
| 学习资料 | Manuals/Howtos/Tutorials、Inspiring Lists、Blogs/Podcasts/Videos、Other Cheat Sheets、Your daily knowledge and news | 教程、博客播客视频、其他速查表、每日知识与新闻源 |
| 安全与 Shell | Hacking/Penetration Testing、Shell One-liners、Shell Tricks、Shell Functions | 渗透测试资源，以及三类可直接复制的 shell 内容 |

所有章节在同一个文件里，靠顶部的总目录和每章开头的 TOC 锚点跳转。这也是它和一般 awesome 列表最大的差别：别的列表往往一个主题一个 README，或者一层层套子目录；这里全部平铺在一个文件里，211 KB 的体量，`grep` 一下比任何搜索框都快。

## 差异化在 Shell 三章

工具章节本身是"链接 + 一句话点评"的清单，各家的 awesome 列表都有。真正少见的 Shell One-liners、Shell Tricks、Shell Functions 三章，收录的不是链接，而是代码。

Shell One-liners 按工具分成 54 个小节（其中两节是系统、网络方向的杂项归类），从 terminal、lsof、find、strace 到 tcpdump、nmap、awk、sed、grep，每节列若干条带注释的单行命令。比如 lsof 一节里：

```bash
# 列出处于监听状态的端口
lsof -Pni4 | grep LISTEN | column -t

# 查谁占着 443 端口
lsof -i tcp:443
```

Shell Tricks 收录了拿到反弹 shell 后把它变成"干净可用"交互环境的完整步骤（`script /dev/null -c bash` 起步，配合 `stty raw -echo; fg` 六步走完）。Shell Functions 给了两个写好的函数：`DomainResolve`（curl 加 jq 调 DNS 解析域名）和 `GetASN`（查 IP 所属 ASN），依赖标注清楚，复制进 `.bashrc` 就能用。

## 一个任务串起这些命令

假设你接手一台陌生服务器，要先摸清它在对外提供什么服务。这本书里的命令可以按顺序串起来：

```bash
# 第一步：列出所有监听中的端口
lsof -Pni4 | grep LISTEN | column -t

# 第二步：对可疑端口，查是哪个进程在监听
fuser -v 53/udp

# 第三步：顺着 PID 看这个进程从哪个目录跑起来
lsof -p <PID> | grep cwd

# 需要摸一圈内网时：快速扫描网段里的存活主机和开放端口
nmap -F --open 192.168.0.0/24
```

四条命令全部出自 Shell One-liners 章节，覆盖了"看端口 → 定进程 → 找目录 → 扫网段"的完整排查链。这个例子也说明了这份手册的定位：它不解释原理，但当你知道要做什么、忘了具体参数怎么写时，翻到对应工具一节就能拿到答案。

## 为什么是这个体量

24.6 万 stars（2026 年 9 月读数）、1.4 万 forks，这个体量在 GitHub 的知识锦集类仓库里位居前列。几个说得出口的原因：

- **选品克制**。README 里专门写着：*"This repository is not meant to contain everything but only good quality stuff."*（这个仓库不打算什么都收，只收好东西。）贡献规则也要求 PR 附上"有效且论证充分的说明"。全书约 900 个去重后的外部链接，对覆盖这个主题范围来说不算多。
- **跨领域一次收齐**。Linux、网络、容器、安全、shell 技巧在一个文件里，不用分头收藏十几个列表。
- **许可开放**。MIT 许可证，可以自由 fork、摘抄、二次整理。
- **有社区托底**。仓库在 Open Collective 上接受赞助，贡献者名单长期开放。

## 必须知道的现状：已经停更

README 里"会定期加入新条目"的说法已经过时了。仓库的最后一次提交是 2024 年 11 月 19 日，此后近两年没有更新——PR 的合并会留下提交记录，没有新提交就意味着外来的 PR 不会再被收进来。

这构成一个使用上的边界：书里的链接可能陆续失效（作者自己在 Contributing 一节也承认有些链接临时不可用），新增的工具和话题不会再进来。但另一面，它收录的主干是 Unix 世界几十年不变的那批工具，命令用法过时的速度很慢。把它当成"2018 到 2024 年沉淀下来的一份静态手册"来用，价值基本不受影响；指望它跟进 2025 年之后的新工具，则要另找渠道。

## 对比其他 Awesome List

GitHub 上有大量 awesome-xxx 列表，the-book-of-secret-knowledge 的独特之处在于：

- 里面有不少直接可用的命令和配置示例，不只是链接收集——Shell 三章尤其明显
- 偏向实操，回答的不是"这个领域有什么好资源"，而是"干这个活用哪条命令"
- 跨领域覆盖，Linux、网络、安全、开发工具全在一个文件里，grep 一把就能搜

代价是单文件形态在网页端读起来偏重，适合"查"而不适合"从头读到尾"。

## 怎么用

两种用法，按需选择：

1. **clone 下来当本地资料库**：遇到具体问题时 `grep -i` 关键词，比网页滚动快得多。
2. **网页端按目录跳读**：不知道自己不知道什么的时候，顺着 15 个章节的目录扫一遍，把全书当知识地图用，标记出和自己工作相关的章节。

```bash
git clone https://github.com/trimstray/the-book-of-secret-knowledge.git
cd the-book-of-secret-knowledge
grep -i -A 3 "nmap" README.md
```

如果你是系统管理员、DevOps 工程师或安全研究员，这份手册现在就该进你的工具箱——它收录的命令在停更前已经稳定存在了很多年，停更后还会稳定很多年。如果你主要写应用代码、很少碰服务器，先收藏，等真的要排查线上问题时再来查也不迟。

---

**一句话总结：** 24.6 万 stars 不是刷出来的，是一份克制选品、单文件、可 grep 的一线运维安全手册近十年沉淀的自然结果。接受"已停更"这个前提，它的命令今天依然好用。

## 参考来源与口径说明

- 仓库元数据（stars 245,839、forks 14,392、MIT 许可证、创建于 2018-06-23、最后推送 2024-11-19）：GitHub API，2026-09-25 读数。
- 章节结构、作者自述、受众说明、贡献规则、Shell One-liners/Tricks/Functions 章节内容与文中全部命令：master 分支 README.md 当前版本（4,442 行、约 211 KB），逐节核对。
- "约 900 个外部链接"为对 README 中 `http(s)` 链接去重后的统计（907 个，已剔除指向仓库自身的锚点），非官方口径。
- 停更状态依据 commits API 前三条记录：2024-11-19（作者本人提交）之后无新提交。
- 本文为项目转述与使用判断，非官方文档；引文均为 README 原文（英文）及其中文翻译。
