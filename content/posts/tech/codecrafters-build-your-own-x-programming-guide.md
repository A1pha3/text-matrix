---
title: "build-your-own-x：GitHub 上 star 最多的仓库，只是一份从零实现的教程清单"
date: "2026-04-25T11:20:00+08:00"
lastmod: 2026-09-02T00:00:00+08:00
slug: codecrafters-build-your-own-x-programming-guide
github_repo: "codecrafters-io/build-your-own-x"
aliases:
 - /posts/tech/build-your-own-x-programming-by-rebuilding/
description: "build-your-own-x：一份按 30 个技术方向整理的外部教程清单，约 53 万 star，GitHub 上最受关注的仓库。它不教你背 API，而是让你从零写出 Git、Docker、BitTorrent。"
draft: false
categories: ["技术笔记"]
tags: ["教育", "编程语言", "系统设计", "学习路径"]
---

大部分程序员的学习路径是：先学会用某个工具，然后读文档，遇到问题去搜答案。这套方法对付日常开发够用，但很难深入——你一直在用技术，很少真正理解它。

[build-your-own-x](https://github.com/codecrafters-io/build-your-own-x) 仓库换了一条路：**从零实现你每天依赖的技术**。不是读源码，不是看教程，是跟着一份份手把手的教程，写出一个能跑的 Git、一个能下载文件的 BitTorrent 客户端、一个能隔离进程的容器。

这个仓库 2018 年由 Daniel Stefanovic 创建，2022 年转入 Codecrafters 组织维护。它的内容只有一个 README，整理着 **30 个技术方向、30+ 种语言的外部教程链接**，如今累计约 **53 万 Stars**，是 GitHub 上 star 最多的仓库。

先说清它到底是什么：这不是一个自带代码的教程项目，而是一份**精选的教程清单**。它不提供需求规范和测试用例，只负责把散落在各处的「从零实现某个技术」的优秀教程按主题归类。判断它有没有价值，要看它选进来的教程质量，而不是它自己写了什么。

## 与传统学习方式的区别

看文档学会的是 API 调用顺序，不是设计决策背后的权衡。读源码面临的是信息过载——你打开 Linux 内核的 TCP/IP 协议栈实现，几万行代码扑面而来，根本不知道从哪入手。

build-your-own-x 收录的教程换了一种方式：

```text
学习理论 → 从零实现简化版本 → 对比官方实现 → 理解设计权衡
```

每篇教程给你「做什么」和「怎么做」的完整路径，你自己动手解决其中的细节。主动构建知识比被动接收知识的留存率更高，这是 Problem-Based Learning 的基本结论。

## 30 个技术方向，从入门到大师

仓库按技术方向归类教程。以下是几个代表性方向及其收录的知名教程：

| 方向 | 代表教程 | 语言 |
|------|----------|------|
| Git | [Write yourself a Git（wyag）](https://wyag.thb.lt/)、[Gitlet](http://gitlet.maryrosecook.com/docs/gitlet.html)、[ugit](https://www.leshenko.net/p/ugit/) | Python / JavaScript |
| Docker | [Linux containers in 500 lines of code](https://blog.lizzie.io/linux-containers-in-500-loc.html)、[bocker（约 100 行 bash）](https://github.com/p8952/bocker) | C / Shell |
| 数据库 | [Let's Build a Simple Database](https://cstack.github.io/db_tutorial/)、[Build Your Own Redis from Scratch](https://build-your-own.org/redis)、[Build Your Own Database from Scratch](https://build-your-own.org/database/) | C / C++ / Go |
| BitTorrent | [Building a BitTorrent client from the ground up in Go](https://blog.jse.li/posts/torrent/)、[A BitTorrent client in Python 3.5](http://markuseliasson.se/article/bittorrent-in-python/) | Go / Python |
| 编程语言 | [Build Your Own Lisp](http://www.buildyourownlisp.com/)、[Crafting Interpreters](http://www.craftinginterpreters.com/)、[Write Yourself a Scheme in 48 Hours](https://en.wikibooks.org/wiki/Write_Yourself_a_Scheme_in_48_Hours) | C / Java / Haskell |
| 操作系统 | [os-tutorial](https://github.com/cfenollosa/os-tutorial)、[Writing an OS in Rust](https://os.phil-opp.com/)、[Operating Systems: From 0 to 1](https://tuhdo.github.io/os01/) | C / Rust |
| 3D 渲染 | [Ray Tracing in One Weekend](https://raytracing.github.io/books/RayTracingInOneWeekend.html)、[tinyrenderer](https://github.com/ssloy/tinyrenderer/wiki) | C++ |
| 前端框架 | [Build your own React（pomb.us）](https://pomb.us/build-your-own-react/)、[Redux: Implementing Store from Scratch](https://egghead.io/lessons/react-redux-implementing-store-from-scratch) | JavaScript |

完整分类清单（3D Renderer、AI Model、Blockchain、Database、Docker、Emulator、Game、Git、Network Stack、Neural Network、Operating System、Programming Language、Shell、Web Browser、Web Server 等）见仓库 README 顶部的目录。

## 项目组织方式

这个仓库的取舍值得拆开看。

**按主题归类，每个主题配多个语言版本。** 想深入数据库底层，可以按 C → C++ → Go 的顺序读三篇不同实现，看到的是同一问题在不同语言里的不同解法。

**链接外部教程，不自建教程。** 仓库维护者只负责筛选和归类，内容质量由社区和原文作者背书。代价是链接可能失效、教程深度参差；好处是能收录不同作者的视角，避开单一团队的「标准答案」。

**和 Codecrafters 付费平台互补。** 同一个团队维护的 [Codecrafters 平台](https://codecrafters.io) 把这套「从零实现」做成了带自动化测试的挑战：你在本地写代码，`git push` 后平台跑测试给反馈。GitHub 仓库是免费的教程索引，平台是付费的练习场。

## 深入两个典型教程的架构

### 从 wyag 理解 Git 的内容寻址

[Write yourself a Git（wyag）](https://wyag.thb.lt/) 用 Python 从零实现 Git 的核心命令。它带出的 Git 内部架构大致分这几层：

```text
┌─────────────────────────────────────────┐
│ 用户命令层（git init / add / commit）       │
├─────────────────────────────────────────┤
│ 命令分派层（解析子命令、参数与帮助）          │
├─────────────────────────────────────────┤
│ 对象模型层（Blob / Tree / Commit / Tag）    │
├─────────────────────────────────────────┤
│ 仓库层（.git 目录、refs、HEAD、索引）         │
├─────────────────────────────────────────┤
│ 存储层（对象文件、压缩与哈希）                │
└─────────────────────────────────────────┘
```

跟着教程实现一遍后，你会对 Git 产生全新的理解：

- **Git 的对象模型是 DAG（有向无环图）**。blob 存文件内容，tree 存目录结构，commit 存提交信息。三者通过 SHA-1 哈希互相引用，构成一个不可变的历史链。
- **分支只是一个指向 commit 的引用**。在 `.git/refs/heads/` 下，分支就是一个包含 40 位哈希的文本文件。创建分支只是写一个小文件，所以分支操作接近 O(1)——不是 Git 做了魔法优化，而是数据模型本来就是这样设计的。
- **`git push` 传输的不是文件差异，而是对象**。Git 会把对象打包、增量压缩后传输。这也是为什么 Git 处理大型二进制文件很慢——它针对文本场景做了优化。

### 从 500 行 C 代码理解容器本质

[Linux containers in 500 lines of code](https://blog.lizzie.io/linux-containers-in-500-loc.html) 用一段 500 行的 C 代码，展示了容器和虚拟机的根本区别：

```text
传统虚拟机：
┌─────────┐ ┌─────────┐ ┌─────────┐
│ App A   │ │ App B   │ │ App C   │
├─────────┤ ├─────────┤ ├─────────┤
│ Guest   │ │ Guest   │ │ Guest   │
│ OS      │ │ OS      │ │ OS      │
├─────────┤ ├─────────┤ ├─────────┤
│ Hypervisor（硬件抽象层）                │
├───────────────────────────────────────┤
│ Host Hardware                         │
└───────────────────────────────────────┘

容器化：
┌─────────┐ ┌─────────┐ ┌─────────┐
│ App A   │ │ App B   │ │ App C   │
├─────────┤ ├─────────┤ ├─────────┤
│ Libs    │ │ Libs    │ │ Libs    │
├─────────┤ ├─────────┤ ├─────────┤
│ Namespaces（PID/Net/Mount/...）        │
├───────────────────────────────────────┤
│ Cgroups（资源限制）                     │
├───────────────────────────────────────┤
│ Host Kernel                           │
└───────────────────────────────────────┘
```

关键区别：**虚拟机虚拟化硬件，容器虚拟化操作系统接口。**

虚拟机通过 Hypervisor 模拟完整的硬件层，每个 Guest OS 运行在自己的虚拟硬件上，隔离彻底但代价重——每个 VM 包含完整操作系统，启动以分钟计。

容器通过 Linux 的 namespace 和 cgroup 实现隔离。namespace 让进程「看到」不同的系统视图（PID、网络、挂载点），cgroup 限制进程能使用的资源（CPU、内存、磁盘 I/O）。它们共享 Host Kernel，所以启动是毫秒级的。

这篇教程带你实现的关键功能：

1. 用 `unshare` 创建隔离的进程视图（namespaces）
2. 用 `chroot` / `pivot_root` 切换根文件系统
3. 用 cgroup 限制 CPU 和内存
4. 处理 pid 1 的孤儿进程回收问题

做完这些，你就明白 Docker 容器比虚拟机轻量不是优化问题，而是架构问题。

## 按能力和方向选择

### 按难度梯度

仓库本身不标难度，以下是一般认为的进阶顺序：

**入门级（适合 1-2 年经验）**
- 写一个 Web Server → 理解 HTTP 与并发基础
- 写一个 Shell → 理解进程与系统调用
- 写一个 Text Editor → 理解终端与缓冲

**进阶级（适合 2-4 年经验）**
- 写一个 BitTorrent 客户端 → 理解 P2P 网络
- 写一个 Git → 理解版本控制设计
- 写一个 Redis 原型 → 理解内存数据存储

**高级（适合 4+ 年经验）**
- 写一个 Docker / 容器 → 理解隔离与内核接口
- 写一个数据库 → 理解存储引擎
- 写一个 3D Renderer → 理解图形管线

**大师级（适合想深入系统底层的人）**
- 写一个编程语言（Lisp / 解释器）→ 理解语言设计
- 写一个操作系统 → 理解系统编程
- 写一个 Network Stack → 理解协议栈

### 按职业方向

**后端工程师：** 数据库 → Git → Web Server → BitTorrent → Network Stack。

**前端工程师：** 前端框架（React/Redux）→ Web Browser → Shell，选做 Template Engine、Regex Engine。

**基础架构工程师：** Docker → 操作系统 → Network Stack → 数据库，选做 Processor、Memory Allocator。

**安全工程师：** 从 Blockchain / Cryptocurrency 方向的教程入手，理解哈希与共识机制，再结合 Network Stack 方向理解协议攻击面。

## 使用建议

### 学习流程

以 wyag 为例，一篇教程通常这样推进：

1. 通读教程，先画出你要实现的核心数据结构（对 Git 来说就是对象模型）
2. 按依赖顺序实现子命令：`init` → `hash-object` → `cat-file` → `write-tree` → `commit-tree`
3. 每实现一步，用官方 `git` 对照验证输出是否一致
4. 完成后再看官方源码，思考你的实现和真实实现之间的差距

**不要**直接抄别人的实现。照抄能通过测试，但什么都学不到。卡住 20 分钟以上再翻提示，看完后合上自己重写一遍。

### 以 Git 为例的验证方法

wyag 教程的建议是：实现后用你自己的命令重建一次提交，再让官方 Git 读取你生成的对象。

```bash
./wyag init test-repo
cd test-repo
# 实现 hash-object 后：
../wyag hash-object -w README.md
# 期望：输出一个 40 位 SHA-1，且官方 git cat-file 能读到它
git cat-file -p <上一步的输出>
```

验证通过，说明你的对象格式和官方一致——这比任何单元测试都更能证明你理解了 Git。

### 和 Codecrafters 付费平台互补

| 维度 | GitHub 仓库 | Codecrafters 平台 |
|------|-------------|-------------------|
| 内容 | 外部教程索引 | 自建的分阶段挑战 |
| 测试反馈 | 无，靠自我对照 | ✅ 自动化测试 |
| 进度追踪 | ❌ | ✅ |
| 官方解答 | ❌（需自行对比） | ✅ |
| 成本 | 免费 | 免费试用 + 付费订阅 |

先用 GitHub 仓库找到感兴趣的方向，如果某个项目想系统性练透，再考虑用平台获得自动化反馈。

## 从实现 BitTorrent 客户端理解 P2P 协议

用 [Building a BitTorrent client from the ground up in Go](https://blog.jse.li/posts/torrent/) 做一个完整拆解，直观感受「从零构建」的过程。

### .torrent 文件结构

```json
{
  "announce": "http://tracker.example.com:6969/announce",
  "info": {
    "name": "ubuntu-22.04.iso",
    "length": 3758096384,
    "piece length": 524288,
    "pieces": "a8f3e2d1..."
  }
}
```

文件被切分成固定大小的 piece（通常 512KB），每个 piece 有 SHA-1 哈希。下载时，你可以从不同 peer 下载不同 piece，最后组装成完整文件。

### Tracker 协议

Tracker 是一个中心化的目录服务，维护着所有 peer 的列表：

```text
请求：announce?info_hash=XXX&peer_id=XXX&port=6881&uploaded=0&downloaded=0&left=1234567
响应：{"interval": 1800, "peers": [{"ip": "1.2.3.4", "port": 6881}, ...]}
```

### Piece 选择算法

Rarest First 是 BitTorrent 的核心算法之一。统计每个 piece 在所有 peer 中的分布，优先下载拥有者最少的 piece。这样做有两个好处：

1. 稀有 piece 尽快扩散，降低「所有 peer 都缺同一块」的概率
2. 不会在下载最后阶段才发现某个 piece 只剩一台机器持有，而它刚好掉线

```python
from collections import Counter

def select_piece_to_download(available_pieces, peer_pieces):
    piece_rarity = Counter()
    for peer in peer_pieces:
        for piece in peer:
            piece_rarity[piece] += 1
    return min(available_pieces, key=lambda p: piece_rarity.get(p, float('inf')))
```

### B 编码

BitTorrent 使用 B 编码（Bencode）作为数据序列化格式，只包含四种类型：

```text
字符串：4:spam    → "spam"
整数：  i3e       → 3
列表：  li3e4:spame → [3, "spam"]
字典：  d3:foo3:bare → {"foo": "bar"}
```

## 局限与价值

这个仓库的价值和局限来自同一个事实：它收录的教程构建的是**简化版本**。

你按教程实现的 Redis 不会像真正的 Redis 那样处理几十万个并发连接，你写的容器不会生产级地管理 overlay network。但如果你亲手实现过跳表、事件循环、RESP 协议解析，你对「Redis 为什么这么快」的理解就不再是背诵面试答案，而是基于每一步时间复杂度的直觉。

同样的，如果你亲手实现过 `unshare` 和 `pivot_root`，理解了 namespace 和 cgroup 的关系，Docker 在你眼里就不再是一个「运行容器的工具」，而是一个「使用 Linux 内核特性进行进程隔离的封装」。

从零构建的真正价值，是把你和工具之间的关系，从使用者变成理解者。

## 延伸阅读

**官方资源**
- [build-your-own-x GitHub](https://github.com/codecrafters-io/build-your-own-x)
- [Codecrafters 官网](https://codecrafters.io)
- [codecrafters-io/interview](https://github.com/codecrafters-io/interview) - 系统设计面试题

**相关资源**
- [danistefanovic/build-your-own-x](https://github.com/danistefanovic/build-your-own-x) - 本仓库的原地址，创建者 Daniel Stefanovic 在 2022 年将其转交给 Codecrafters 组织
- [open-source-ideas/open-source-ideas](https://github.com/open-source-ideas/open-source-ideas) - 新项目创意

**书籍推荐**

| 书籍 | 关联方向 | 你会学到 |
|------|----------|----------|
| 《Linux 高性能服务器编程》 | Web Server / 网络编程 | 深入理解网络编程 |
| 《Redis 设计与实现》 | 数据库（Redis） | 理解 Redis 内部原理 |
| 《自己动手写 Docker》 | Docker / 容器 | 理解容器化技术 |
| 《操作系统真象还原》 | 操作系统 | 系统编程入门 |
| 《编译原理》龙书 | 编程语言 | 编译器基础 |

---

*本文基于 [codecrafters-io/build-your-own-x](https://github.com/codecrafters-io/build-your-own-x)（2026 年 8 月约 53 万 Stars，CC0 许可）编写。*
