---
title: "uBlock Origin：高效广告拦截的技术架构与多层次过滤机制解析"
date: 2026-04-30T10:07:00+08:00
slug: "ublock-origin-architecture-filtering-mechanisms"
description: "uBlock Origin 是如何实现 CPU 和内存高效广告拦截的？本文从源码结构出发，深入解析其静态过滤、动态过滤、脚本注入过滤三大引擎的架构设计，以及 BitTrie、Bloom Filter 等数据结构如何支撑其高性能。"
draft: false
categories: ["技术笔记"]
tags: ["uBlock Origin", "广告拦截", "浏览器扩展", "过滤规则", "开源"]
---

uBlock Origin（通常简称 uBO）是一款面向 Chromium 和 Firefox 的广谱内容拦截扩展，由独立开发者 Raymond Hill（gorhill）维护。截至本文写作时，GitHub 仓库 [gorhill/uBlock](https://github.com/gorhill/uBlock) 拥有约 64,000 颗 Stars 和 4,000 多个 Fork，最新稳定版本为 v1.70.0。与同类扩展相比，uBO 以"CPU 和内存高效"（CPU and memory efficient）著称，本文从源码结构出发，解析其背后的架构设计。

## 项目概览

uBlock Origin 最早发布于 2015 年，采用 GPLv3 开源协议，代码完全由 JavaScript 编写。README 开篇即点明项目定位：

> uBlock Origin is a CPU and memory efficient wide-spectrum content blocker for Chromium and Firefox.

默认状态下，uBO 启用以下过滤器列表（filter lists）：

- **EasyList**：去除广告的标准规则，被业界广泛采用
- **EasyPrivacy**：反追踪规则，阻断常见分析脚本和追踪器
- **Peter Lowe's Blocklist**：第三方追踪域名列表
- **Online Malicious URL Blocklist**：在线恶意 URL 黑名单
- **uBO Filters**：维护者自建规则集

用户也可以按需启用更多列表，甚至完全自定义过滤规则。uBO 的一个设计哲学是：默认配置已足够大多数用户使用，无需深度调优；但它也提供了强大的高级功能，供有需求的用户自行配置。

## 源码结构一览

克隆仓库后，核心代码位于 `src/` 目录下。按功能划分，主要文件如下：

| 路径 | 职责 |
|------|------|
| `src/js/background.js` | 扩展主进程，管理各模块生命周期 |
| `src/js/contentscript.js` | 内容脚本，注入到每个页面执行 |
| `src/js/static-filtering-parser.js` | 静态过滤规则解析器（EasyList 语法） |
| `src/js/static-filtering-io.js` | 静态过滤的 I/O 和合并逻辑 |
| `src/js/dynamic-net-filtering.js` | 动态网络过滤（per-site 防火墙） |
| `src/js/cosmetic-filtering.js` | CSS cosmetic 过滤（隐藏页面元素） |
| `src/js/scriptlet-filtering.js` | 脚本注入过滤（snippet） |
| `src/js/redirect-engine.js` | 资源重定向引擎 |
| `src/js/biditrie.js` | BitTrie——位图前缀树，用于高效 URL 匹配 |
| `src/js/hntrie.js` | HN-Trie——层级名称前缀树 |
| `src/js/bloom-filter.js` | Bloom Filter 实现 |
| `src/js/mrucache.js` | MRU（最近最少使用）缓存 |
| `src/js/lz4.js` | LZ4 压缩，用于缓存序列化 |

理解 uBO 的架构，关键是理解它如何分层处理一个网络请求或页面渲染事件。

## 三大过滤引擎

### 静态过滤（Static Filtering）

静态过滤是 uBO 最基础的一层，基于 EasyList 及其扩展规则。规则以文本形式存储，后缀名为 `.txt`（如 `easyList.txt`），每行一条规则，支持注释。

静态过滤解析器在 `src/js/static-filtering-parser.js` 中实现。它将文本规则转换为内部数据结构，供过滤引擎在网络请求阶段查询。EasyList 语法支持多种规则类型：

- **网络拦截规则**：`||example.com^` 拦截来自 `example.com` 的所有请求
- **类型限定**：`||ads.example.com^$script,third-party` 仅拦截脚本类型和第三方请求
- **白名单**：`@@||example.com^` 对特定规则解除拦截
- **正则规则**：`/正则表达式/` 用于复杂模式匹配

静态过滤引擎在浏览器发出网络请求时，通过查询预处理好的规则集合决定是否拦截。整个匹配过程需要极快，因为它是阻塞性的——匹配耗时直接反映为页面加载延迟。

### 动态过滤（Dynamic Filtering）

动态过滤是 uBO 区别于传统广告拦截器的核心特性之一。在 `src/js/dynamic-net-filtering.js` 中实现，它允许用户为每个域名单独设置"防火墙"规则，且支持点选式（point-and-click）配置，无需手动编写规则语法。

动态过滤的基本模型是四层权限：

1. **白名单（Allow）**：`no large media elements`、`no Cosemtic filtering`
2. **灰名单（Noop）**：不做任何处理
3. **拦截（Block）**：拦截特定类型的请求
4. **noop 规则**：覆盖全局规则中的拦截行为

用户可以在弹出面板（popup）中，针对当前站点的 `popup`、`inline script`、`frame`、`object` 等 8 种请求类型分别设置权限。这使得 uBO 不是一个"一刀切"的工具，而是可以根据每个站点的实际需求精细控制。

### 脚本注入过滤（Scriptlet Filtering）

第三层是脚本注入过滤，对应 `src/js/scriptlet-filtering.js`。这一层处理的是 JavaScript 层面的拦截与替换。

很多现代广告并非简单地从广告域名拉取资源，而是在页面内通过 JavaScript 动态注入脚本、执行挖矿代码或弹出窗口。uBO 的应对方式是：将恶意或侵入性脚本的调用直接替换为空操作（no-op），使得广告代码虽然存在，但实际不执行。

这种能力依赖于 uBO 自研的 [Extended Syntax](https://github.com/gorhill/uBlock/wiki/Static-filter-syntax#extended-syntax)（扩展语法），其中最核心的是 `##+js()` 语法。例如：

```
##+js(googlesyndication.com, alert, 1)
```

这条规则会将 `googlesyndication.com` 相关的 alert 调用替换掉，达到拦截效果。脚本注入过滤的优势在于：即使广告脚本已经存在于页面 DOM 中，它也不会真正执行，保持了页面的干净。

## 高效数据结构：BitTrie 与 Bloom Filter

uBO 之所以能以"CPU 和内存高效"著称，很大程度上归功于其精心选择的数据结构。

### BitTrie

`src/js/biditrie.js` 实现了 BitTrie（位图前缀树）。Trie（前缀树）是一种树形数据结构，用于高效存储和检索字符串集合中的键。BitTrie 的特别之处在于它使用位操作（bit-level operations）来加速查找，对于大量 URL 的前缀匹配场景，比传统的哈希表或线性搜索效率高出几个数量级。

在 uBO 中，BitTrie 用于存储网络过滤规则中的域名前缀集合。当浏览器发起一个请求时，系统只需从请求 URL 中提取域名，然后在 BitTrie 中查找是否有匹配的前缀规则——这个查找过程是 O(k)，其中 k 是域名的段数（通常是 3-5），而不是 URL 总长度。

### Bloom Filter

Bloom Filter（布隆过滤器）是一种空间效率极高的概率数据结构，用于快速判断一个元素"可能存在"或"一定不存在"于集合中。Bloom Filter 会有一定的假阳性率（误判为存在），但绝不会出现假阴性（漏掉真实存在的元素）。

在 uBO 中，Bloom Filter 用于快速判断某个请求是否值得进一步查询详细规则。如果 Bloom Filter 返回"不存在"，则直接放行，省去了完整规则库的查询开销。如果返回"可能存在"，才进入 BitTrie 等精确匹配逻辑。这一层预判将大量无效查询拦截在最早阶段，显著降低了 CPU 开销。

### MRU 缓存

`src/js/mrucache.js` 实现了最近最少使用（Most Recently Used）缓存。当过滤规则被查询时，最近命中的结果会被缓存；缓存满时，最久未使用的条目被淘汰。由于互联网访问的局部性原理（temporal locality），同一域名或相似 URL 在短期内被重复访问的概率很高，MRU 缓存能大幅减少重复计算。

## 资源重定向引擎

`src/js/redirect-engine.js` 是 uBO 另一个重要的技术组件。当某些请求无法直接拦截（例如跨域脚本必须存在才能运行），uBO 采取的策略是"重定向"——将请求目标替换为一个空的或安全的资源。

典型的应用场景是绕过反广告拦截检测。很多网站会检测浏览器是否安装了广告拦截器，uBO 通过将检测脚本重定向到自己的安全版本（即 `web_accessible_resources/` 目录下的文件），使检测失效，同时不影响页面正常运行。

重定向规则同样使用 Extended Syntax 描述，存储在 `src/assets/resources/` 目录下。

## 安装与基本使用

uBO 支持主流桌面浏览器：

- **Firefox**：从 [AMO（Add-ons Mozilla）](https://addons.mozilla.org/en-US/firefox/addon/ublock-origin/) 安装
- **Chromium/Chrome**：从 [Chrome Web Store](https://chrome.google.com/webstore/detail/ublock-origin/cjpalhdlnbpafiamejdnhcphjbkeiagm) 安装
- **Edge**：从 [Microsoft Store](https://microsoftedge.microsoft.com/addons/detail/odfafepnkmbhccpbejgmiehpchacaeak) 安装
- **Opera**：从 Opera 扩展商店安装

安装完成后，扩展图标会出现在浏览器工具栏。点击图标即可看到弹出面板，显示当前页面的拦截统计。最基础的用法是：点击扩展图标中的电源按钮，开启或关闭全局拦截；点击特定域名的 `Allow` 按钮，可以将该域名加入白名单。

对于进阶用户，推荐开启**高级模式**（Advanced Mode）：在设置中启用"我现在是一个高级用户"，即可访问动态过滤面板、手动编辑过滤规则、使用日志查看器（Logger）调试规则匹配过程。

## 架构亮点总结

回顾 uBO 的整体设计，有几个值得注意的技术决策：

**分层防御，而非单一黑名单。** 静态过滤处理已知规则，动态过滤处理动态行为，脚本注入过滤处理运行时劫持——三层互相配合，覆盖了广告和追踪的不同入口。

**数据结构的极致优化。** BitTrie、Bloom Filter、MRU 缓存不是炫技，而是针对网络拦截这个场景的实际需求精心选择的。在每次页面加载可能触发数千次 URL 检查的场景下，这些结构将单次查询的时间复杂度从 O(n) 降到了 O(1) 或 O(k)。

**用户可控制粒度极细。** 动态过滤的 per-site 权限模型和 Extended Syntax 赋予用户远超平均水平的定制能力，同时默认配置对大多数用户开箱即用——这是用户体验和灵活性之间的精心平衡。

**完全独立维护。** 不同于依赖广告资助的浏览器，uBO 由独立开发者维护，没有商业利益驱动，这使其隐私政策和使用逻辑保持了最大程度的用户友好。

## 参考资源

- [gorhill/uBlock 官方仓库](https://github.com/gorhill/uBlock)
- [uBlock Origin Wiki — Extended Syntax](https://github.com/gorhill/uBlock/wiki/Static-filter-syntax#extended-syntax)
- [uBlock Origin Wiki — Dynamic Filtering](https://github.com/gorhill/uBlock/wiki/Dynamic-filtering:-quick-guide)
- [EasyList 官方规则库](https://easylist.to/)
- [Peter Lowe's Blocklist](https://pgl.yoyo.org/adservers/)
