---
title: "uBlock Origin 架构解析：一套把性能压到极致的多层过滤系统"
date: "2026-04-30T10:07:00+08:00"
slug: "ublock-origin-architecture-filtering-mechanisms"
description: "深入拆解 uBlock Origin 的静态过滤、动态过滤和脚本注入三大引擎，以及 BitTrie、Bloom Filter、MRU 缓存如何联手把单次 URL 匹配从 O(n) 压到 O(k)。附带完整请求流转案例和源码阅读路径。"
draft: false
categories: ["技术笔记"]
tags: ["uBlock Origin", "广告拦截", "浏览器扩展", "过滤规则", "开源", "性能优化"]
---

## 这篇文章在讲什么

uBlock Origin 真正解决的问题不是「拦截广告」—— AdBlock Plus 十年前就在做这个了。它做的是另一件事：**在拦截规则膨胀到数万条之后，让每次页面加载触发的数千次 URL 检查仍然跑在微秒级别，且内存开销不超过几十 MB。** 读完这篇文章，你会对 uBO 的三层过滤分工、每次网络请求从拦截规则到放行的完整路径，以及它把 O(n) 碾成 O(k) 的数据结构组合有一个能用的理解。

### 学习目标

按你自己的情况选一条路径：

- **如果你想快速知道全貌**：读「三层过滤的分工」和「一个请求的完整流转」。
- **如果你想看懂源码**：按「源码结构一览」的表格定位文件，配合「三大过滤引擎」逐层读。
- **如果你想借鉴性能优化思路**：重点读「从 O(n) 到 O(k)」这一节和 Bloom Filter 的预判逻辑。
- **如果你想自己写过滤规则**：直接跳到「进阶：写一条高质量过滤规则」。

### 目录

1. [三层过滤的分工](#三层过滤的分工)
2. [一个请求的完整流转（案例）](#一个请求的完整流转案例)
3. [源码结构一览](#源码结构一览)
4. [三大过滤引擎详解](#三大过滤引擎详解)
   - [静态过滤](#静态过滤)
   - [动态过滤](#动态过滤)
   - [脚本注入过滤](#脚本注入过滤)
5. [从 O(n) 到 O(k)：数据结构组合](#从-on-到-ok数据结构组合)
   - [BitTrie：用位操作加速前缀匹配](#bittrie用位操作加速前缀匹配)
   - [Bloom Filter：在查规则之前先筛一遍](#bloom-filter在查规则之前先筛一遍)
   - [MRU 缓存：靠时间局部性省掉重复计算](#mru-缓存靠时间局部性省掉重复计算)
6. [资源重定向：那些不能直接拦截的请求](#资源重定向那些不能直接拦截的请求)
7. [安装与日常使用](#安装与日常使用)
8. [进阶：写一条高质量过滤规则](#进阶写一条高质量过滤规则)
9. [常见问题](#常见问题)
10. [自测：你能不能解释这些？](#自测你能不能解释这些)
11. [谁该用、谁可以等等](#谁该用谁可以等等)
12. [参考资源](#参考资源)

## 三层过滤的分工

uBO 不像传统拦截器那样只维护一张黑名单，它把过滤拆成了三层。每一层管一类问题，互不越界。理解这个分工比理解任何一行代码都重要。

| 层 | 负责什么 | 触发时机 | 查什么 |
|----|---------|---------|--------|
| 静态过滤 | 已知广告 / 追踪域名和 URL 模式 | 浏览器发起网络请求时 | EasyList 等社区规则，约 8 万条 |
| 动态过滤 | 按站点粒度的细粒度权限 | 同一网络请求阶段，优先于静态规则 | 用户针对当前域设置的 allow / block / noop |
| 脚本注入过滤 | 页面内 JS 层面的劫持和注入 | DOM 构建完成后，页面脚本执行前 | Extended Syntax 规则，如 `##+js()` |

三层是串联的，不是三选一。一个网络请求要全部通过静态和动态两层才能发出；一个页面脚本要躲过脚本注入过滤才算安全。

## 一个请求的完整流转（案例）

下面是一个真实场景：用户在浏览器地址栏输入 `news.example.com`，这个网站嵌了来自 `ad.doubleclick.net` 的广告脚本。

### 第一步：动态过滤先判定

请求 `ad.doubleclick.net/ads.js` 准备发出。uBO 先查动态过滤规则——当前站点 `news.example.com` 下，用户是否对 `ad.doubleclick.net` 设置了 allow / block / noop？

- 如果查到 **block**：请求直接拦截，不再走静态过滤。结束。
- 如果查到 **allow**：请求放行，跳过后续所有检查。结束。
- 如果查到 **noop** 或没查到：进入静态过滤。

这一步很快，因为动态规则是 per-site 的哈希表，key 是 `(源站点, 目标域名, 请求类型)`。

### 第二步：Bloom Filter 预判

进入静态过滤后，uBO 不直接去查那 8 万条规则。它先把 `ad.doubleclick.net` 丢进 Bloom Filter。

- Bloom Filter 返回「**一定不存在**」：直接放行。结束。
- Bloom Filter 返回「**可能存在**」：进入 BitTrie 精确匹配。

这一步的关键价值：大多数正常请求在这一步就被放走了，不会触及后面的 BitTrie 查找。Bloom Filter 只用几百 KB 内存就把无效查询拦在了最外层。

### 第三步：BitTrie 精确匹配

Bloom Filter 说「可能存在」，就要真查了。uBO 用 BitTrie（位图前缀树）来匹配域名前缀规则。

以 `||ad.doubleclick.net^` 为例：uBO 把域名拆成 `["ad", "doubleclick", "net"]`，在 BitTrie 中逐段查找。每段都是一次位操作，三段三次查完。整个过程是 O(k)，k 是域名段数（通常 3-5），跟规则库总大小无关。

命中规则 `||ad.doubleclick.net^`：拦截。结束。

BitTrie 查完没命中：放行。结束。

### 第四步：脚本注入过滤补刀

页面 HTML 已加载完成，浏览器准备执行页面里的脚本。uBO 的内容脚本扫描 DOM，检查是否有匹配 `##+js()` 规则的 script 节点。

假设页面里有这样一行：

```html
<script>
  // Google ad syndication 注入的脚本
  googlesyndication.push({ ... });
</script>
```

uBO 的脚本注入过滤匹配到规则 `##+js(googlesyndication.com, push, 1)`，把 `push` 调用替换成空操作。脚本还在 DOM 里，但执行到 `push` 时什么都不发生。

### 这个案例说明了什么

- 三层不是互相替代，而是**拦截深度递增**：网络层拦不住的，页面层补。
- Bloom Filter 不是可有可无的优化——8 万条规则下，没有预判，每个请求都要走 BitTrie，CPU 开销会翻几个数量级。
- 动态过滤的优先级决定了用户可以在单个站点上推翻全局规则，不需要改社区规则列表。

## 源码结构一览

uBlock Origin 最早发布于 2015 年，使用 GPLv3 开源协议，代码全部由 JavaScript 编写。截至本文写作时，GitHub 仓库 [gorhill/uBlock](https://github.com/gorhill/uBlock) 拥有约 64,000 颗 Stars，最新稳定版本为 v1.70.0。

克隆仓库后，核心代码在 `src/` 目录下：

| 路径 | 做了什么 | 建议先读 |
|------|---------|---------|
| `src/js/background.js` | 扩展主进程，管所有模块的启动和生命周期 | ⭐ 入口 |
| `src/js/contentscript.js` | 注入到每个页面的内容脚本 | ⭐ |
| `src/js/static-filtering-parser.js` | 把 EasyList 文本规则解析成内部数据结构 | ⭐ |
| `src/js/static-filtering-io.js` | 规则的 I/O、合并、从磁盘加载 | |
| `src/js/dynamic-net-filtering.js` | per-site 动态防火墙 | ⭐ |
| `src/js/cosmetic-filtering.js` | CSS cosmetic 过滤，隐藏页面元素 | |
| `src/js/scriptlet-filtering.js` | `##+js()` 脚本注入过滤 | ⭐ |
| `src/js/redirect-engine.js` | 把被拦截的请求重定向到安全资源 | |
| `src/js/biditrie.js` | BitTrie：位图前缀树 | ⭐⭐ |
| `src/js/hntrie.js` | HN-Trie：层级名称前缀树 | |
| `src/js/bloom-filter.js` | Bloom Filter 实现 | ⭐⭐ |
| `src/js/mrucache.js` | MRU 缓存 | |
| `src/js/lz4.js` | LZ4 压缩，用于缓存序列化 | |

⭐⭐ 标注的是这篇文章重点拆解的模块。如果你想从源码级理解 uBO 的性能秘诀，从 `biditrie.js` 和 `bloom-filter.js` 入手是最高效的路径。

## 三大过滤引擎详解

### 静态过滤

静态过滤处理的是「已知的坏域名」。规则来源是 EasyList、EasyPrivacy、Peter Lowe's Blocklist 等社区维护的列表，总计约 8 万条，以 `.txt` 格式存储，一行一条。

`src/js/static-filtering-parser.js` 负责把这些文本规则翻译成内部查询结构。EasyList 的语法并不复杂，但覆盖了相当多的匹配维度：

```text
# 拦截来自 example.com 的任何请求
||example.com^

# 只拦截来自 example.com 的脚本，且必须是第三方请求
||ads.example.com^$script,third-party

# 把 example.com 从拦截规则中排除
@@||example.com^

# 正则匹配——性能最差，尽量少用
/analytics\.js$/
```

**为什么不用纯正则处理所有规则？** 8 万条规则如果都用正则匹配，每个请求要做 8 万次正则求值，页面加载会直接卡死。静态过滤的真正工作量不在正则，而在前缀匹配——而前缀匹配正好是 Trie 结构的甜区。

静态过滤是在浏览器网络请求阶段介入的，它是阻塞性的：匹配耗时直接反映为用户感知到的页面延迟。uBO 对这一层的优化投入最大，后面的数据结构选择基本都围绕它展开。

### 动态过滤

动态过滤是 uBO 区别于传统拦截器的关键——它让用户可以对单个域名设置独立规则，而且不需要手写规则语法。

它的权限模型很简单，四层：

1. **block**：拦截该域名的特定类型请求。
2. **allow**：对该域名不做任何拦截。
3. **noop**：不做处理，交给全局规则决定。
4. **覆盖**：noop 可以从全局 block 规则中把该域名捞出来。

在弹出面板（popup）里，用户对着当前站点，从 8 种请求类型——`images`、`scripts`、`frames`、`xhr` 等——中逐项点选权限。这不是图形化 API，它就是 API 本身：点击即规则。

**为什么动态过滤比只靠社区规则更安全？** 社区规则是全省略式的一刀切。`easyList.txt` 不知道你是在看新闻还是在用网银，它只能按域名全局拦截。动态过滤给了用户一个退出机制：全局规则把 `example.com` 拦了，但你可以对 `bank.example.com` 设 allow，不需要改规则文件，不需要等列表更新。

实现上，动态规则存在 per-site 哈希表里，查找 O(1)。因为规则量小（单个站点通常不超过 10 条），它在我们讨论过的三层中开销最低，优先级却最高。

### 脚本注入过滤

现代广告早就不再简单地 `<script src="ad.com/banner.js">` 了。更常见的做法是页面内的 JS 动态创建 iframe、调用 `eval`、劫持 `XMLHttpRequest`、或在 `window` 上挂监听器。这些行为不产生独立的网络请求，静态过滤和动态过滤都看不见。

uBO 的应对是脚本注入过滤，对应 `src/js/scriptlet-filtering.js`。核心机制：在页面脚本执行之前，把目标函数替换成空操作（no-op）。

```text
# 把 googlesyndication.com 相关上下文中的 alert 替换为 no-op
##+js(googlesyndication.com, alert, 1)
```

替换发生在内容脚本注入阶段，早于页面自己的 JS 执行。广告代码照常存在于 DOM 中，但 `alert` 已经变成了一个什么都不做的函数。

**为什么不让用户直接写 JS 来拦截？** 安全。脚本注入使用 uBO 自研的 Extended Syntax，不支持任意 JS，用户写不出 `eval(location.hash)` 这种东西。替代方案是预先定义好的 scriptlet 模板，存放在 `src/assets/resources/` 下。

这里需要说明一个不能推的边界：脚本注入过滤对「内联脚本」效果最好，对 `src` 加载的外部脚本只能靠网络层拦截。如果外部脚本已经通过静态或动态过滤被放行了，脚本注入过滤无法再介入——它改不了远程文件的执行上下文。

## 从 O(n) 到 O(k)：数据结构组合

uBO 的性能口碑不是凭空来的。如果你只从这一个项目里学一样东西，就学它如何用三个数据结构组合把匹配从线性降到常数。

### BitTrie：用位操作加速前缀匹配

Trie（前缀树）按字符拆分 key，路径即内容。BitTrie 在此基础上多做了一步：用位操作（bit-level AND、移位、掩码）替代字符串比较。

在 uBO 中，BitTrie 存的是域名前缀，如 `ad.doubleclick`。查找时：

1. 域名按 `.` 拆成段，如 `["ad", "doubleclick", "com"]`。
2. 每段做一次位掩码匹配，判断当前节点是否有该前缀。
3. 逐段向下，三段查完即出结果。

复杂度是 O(k)，k 为域名段数。8 万条规则和 800 万条规则，只要 k 不涨（域名段数不会超过 10），查找时间就不涨。

对比一下：如果用哈希表存所有规则的完整 URL，每次查找的 key 组合爆炸（同一域名可能有几百条路径变体）；如果用线性扫描，查找时间直接跟规则数量成正比。BitTrie 踩中了广告拦截的唯一甜区——按域名前缀匹配是最频繁的操作。

### Bloom Filter：在查规则之前先筛一遍

Bloom Filter 的输入是一个域名字符串，输出是两种结果之一：

- **一定不存在**（概率 100%）：这个域名不在任何规则里，直接放行。
- **可能存在**（有一定假阳性）：需要进一步精确匹配。

假阳性意味着 Bloom Filter 偶尔会说「可能有」，但去 BitTrie 查了一圈发现其实没有。这个误差 uBO 可以接受，因为代价只是一次多余的 BitTrie 查找。假阴性是不存在的——Bloom Filter 永远不会漏掉一个真实匹配。

在 uBO 中，Bloom Filter 的位数组大小是规则总数乘以一个可调系数（默认约 10 bit/key），假阳性率控制在 1% 左右。内存开销：8 万条规则 × 10 bit ≈ 100 KB。

**为什么不用哈希集合？** 哈希集合精确但占内存。8 万条完整 URL，平均 80 字节一条，需要约 6.4 MB。Bloom Filter 用 100 KB 完成了 99% 的初筛——那些命中的 1% 再去走 BitTrie 精确匹配，总成本比每条都查哈希集合低得多。

### MRU 缓存：靠时间局部性省掉重复计算

浏览器的网络请求有很强的局部性：同一域名下的资源（CSS、JS、图片）在短时间内被连续请求。MRU（Most Recently Used）缓存把最近查过的域名和匹配结果存下来。

缓存满时，最久未使用的条目被淘汰——实现源码在 `src/js/mrucache.js`，简单直接。一个页面加载过程中，同一域名的资源请求可以多达数十次，MRU 缓存让除第一次之外的所有同类请求都变成 O(1) 缓存命中。

**为什么用 MRU 而不是 LRU？** 对于广告拦截场景，最近访问的条目最可能被再次访问。LRU 在淘汰策略上更「公平」，但 MRU 对这个访问模式更吻合——而且实现简单，不需要维护双向链表。

## 资源重定向：那些不能直接拦截的请求

`src/js/redirect-engine.js` 处理一类特殊情况：某些脚本不能直接拦截，因为拦了页面会报错，甚至触发反广告拦截检测。

uBO 的策略是把请求目标替换成一个「无害版本」。典型场景：

1. 网站加载了 `ads.example.com/detect-adblock.js` 来检测拦截器。
2. 直接拦截这个脚本 → 网站检测到脚本加载失败 → 弹出提示要求关闭拦截器。
3. uBO 的重定向方案：不拦截这个请求，但把它的响应替换为 `web_accessible_resources/` 下的一个空 JS 文件。脚本「加载成功」了，但什么都不做。

重定向规则同样用 Extended Syntax 描述：

```text
||ads.example.com/detect-adblock.js$script,redirect=noop.js
```

`noop.js` 就是一个空脚本。uBO 内置了几十个这样的「替身资源」，覆盖常见的广告 SDK 和检测脚本。

有一点要说清楚：重定向不是万能的反检测方案。如果网站的检测逻辑写在页面自身的 JS 里（例如检查 `window.adBlockDetected` 变量），重定向引擎插手不了——它只能作用于网络请求层面。

## 安装与日常使用

### 安装

- **Firefox**：[AMO 扩展商店](https://addons.mozilla.org/en-US/firefox/addon/ublock-origin/)
- **Chromium / Chrome**：[Chrome Web Store](https://chrome.google.com/webstore/detail/ublock-origin/cjpalhdlnbpafiamejdnhcphjbkeiagm)
- **Edge**：[Microsoft Store](https://microsoftedge.microsoft.com/addons/detail/odfafepnkmbhccpbejgmiehpchacaeak)
- **Opera**：Opera 扩展商店

安装后工具栏会出现 uBO 图标。点击图标看弹出面板，上面的数字是当前页面已拦截的请求数。

### 基础用法三步

1. **开关**：点击电源按钮，蓝色为开启。
2. **单站白名单**：点击大电源按钮旁边的域名区域，当前站点加入白名单。
3. **快速调优**：弹出面板底部有「打开设置」入口，默认启用 EasyList + EasyPrivacy + uBO Filters 就够大多数人用。

### 进阶模式

在设置里勾选「我是高级用户」，解锁：

- **动态过滤面板**：上面提到的 per-site 权限配置。点击弹出面板中每个请求类型对应的格子即可设置。
- **日志查看器（Logger）**：实时显示每个请求的匹配路径——进了哪个规则、被哪层过滤拦的、耗时多少。查规则冲突时比盲猜有效得多。
- **我的规则**：手动编辑用户规则文件，支持静态语法和动态语法。

## 进阶：写一条高质量过滤规则

学会写规则，你就不再是 uBO 的「默认配置用户」了。以下是从简单到完整的三个例子。

### 例 1：拦截特定域名下的脚本

```text
||annoying-widget.com^$script,domain=example.com
```

- `||` 匹配域名及其子域名
- `^` 匹配分隔符（`/`、`?`、行尾等）
- `$script` 限定只拦截脚本请求
- `domain=example.com` 限定只在 `example.com` 上生效

### 例 2：白名单例外

```text
@@||cdn.example.com^$script,domain=example.com
```

`@@` 开头表示这是白名单规则。即使全局规则拦了 `cdn.example.com`，这条规则会把它放行。

### 例 3：用脚本注入补刀

```text
example.com##+js(no-setTimeout-if, /ads\./)
```

这条规则在 `example.com` 页面里，把参数中匹配 `/ads\./` 的 `setTimeout` 调用全部替换为空操作。适用于那些不产生网络请求、只在页面内部定时弹窗的广告。

### 规则书写原则

1. **越具体越好**：能加 `$script` 就不裸写域名，能加 `domain=` 就不全局生效。
2. **尽量不用正则**：`/regex/` 的匹配成本比前缀匹配高一个数量级。能用 `||` 和 `^` 搞定的不要上正则。
3. **测试规则**：开 Logger，访问目标页面，看规则是否命中。没命中就改，比猜完就放着靠谱。

## 常见问题

**Q：uBO 和 AdBlock Plus 有什么本质区别？**

ABP 用的是一个更重的匹配模型——每条规则可能触发多次正则求值。uBO 把匹配拆成了三层，前缀匹配走 BitTrie，动态规则走哈希表，只把极小部分交给正则。这导致同一组 EasyList 规则，uBO 的 CPU 和内存开销大约是 ABP 的 1/3 到 1/5。另一个区别是 ABP 有「可接受广告」计划，uBO 没有——Raymond Hill 明确表示不接广告资助。

**Q：开了 uBO，为什么有些广告还是拦不掉？**

三种可能：

1. 广告是页面 HTML 内联的，不产生网络请求。开 Logger 看不到拦截记录。这种情况需要自己写 `##` 规则或用元素选择器模式手动隐藏。
2. 广告域名不在你启用的规则列表里。在设置里检查启用了哪些列表，EasyList + uBO Filters 是最低配置。
3. 网站用了动态域名（每次加载换一个子域名）。需要写通配规则或升级到脚本注入过滤。

**Q：uBO 会影响浏览器性能吗？**

所有内容拦截器都会增加额外的网络请求检查。但 uBO 的设计目标是把增量压到不可感知的程度。在一般页面上，uBO 的 CPU 开销远低于它拦截的那些追踪脚本原本会消耗的 CPU。实际效果是页面变快了。

**Q：为什么我的 uBO 图标数字不更新？**

检查是否开启了「暂停在此站点上」或全局暂停。如果都没开，尝试刷新页面——uBO 只在请求发生时计数，缓存和 Service Worker 不会触发新的计数。

**Q：如何排查某条规则为什么没生效？**

开 Logger（设置 → 我是高级用户 → 弹出面板的日志图标），访问目标页面。Logger 会显示每个网络请求的匹配链路：被哪条规则拦的、通过了哪层过滤。如果看不到相关请求，说明请求在更早的阶段被拦截或根本没有发出。

## 自测：你能不能解释这些？

不看原文，试试回答：

1. uBO 的三层过滤分别在哪三个阶段介入？它们中间谁先谁后？
2. Bloom Filter 在这个系统里解决的具体问题是什么？如果没有它，性能会怎么变？
3. 为什么 BitTrie 的查找复杂度是 O(k)，而规则总数不影响它？
4. 动态过滤的 allow / block / noop 分别对后续的静态过滤产生什么影响？
5. 脚本注入过滤和静态过滤各有什么覆盖不到的盲区？
6. MRU 缓存和 Bloom Filter 都用来减少「不必要的工作」，它们各自的适用条件有什么不同？

能回答 4 个以上，这篇文章没有白读。

如果卡在哪题上，回头找对应的小节重读。读第二遍通常比第一遍收获大得多。

## 谁该用、谁可以等等

### 直接用 uBO，不做任何配置

覆盖 95% 的用户。安装后默认的三套列表（EasyList + EasyPrivacy + uBO Filters）已经能拦截绝大多数广告和追踪器。

### 开高级模式，学写规则

覆盖 4% 的用户，典型特征是：

- 你访问的某些网站（如视频站、网盘）反拦截做得狠，默认规则不够。
- 你对某些网站的追踪行为特别在意，想把权限粒度压到单个脚本级别。
- 你想看懂 Logger 里的匹配日志，自己能排查「这条为什么没拦」。

### 暂时不用也没关系

**如果你的浏览器在受管环境中运行**（企业策略锁定了扩展安装），那装不了的东西不用纠结。**如果你主要用移动端浏览器**，Firefox Android 版支持扩展，但 Chrome Android 版不支持——换浏览器比折腾规则更实际。

### 从源码入手

如果你关心的不是怎么用 uBO，而是一个高性能浏览器扩展写好之后能踩到什么程度的性能底线，从 `biditrie.js` → `bloom-filter.js` → `static-filtering-parser.js` → `dynamic-net-filtering.js` 的顺序通读，会比按文件名字母顺序翻源码效率高一个数量级。

## 参考资源

- [gorhill/uBlock 官方仓库](https://github.com/gorhill/uBlock)
- [uBlock Origin Wiki — Extended Syntax](https://github.com/gorhill/uBlock/wiki/Static-filter-syntax#extended-syntax)
- [uBlock Origin Wiki — Dynamic Filtering Quick Guide](https://github.com/gorhill/uBlock/wiki/Dynamic-filtering:-quick-guide)
- [EasyList 官方规则库](https://easylist.to/)
- [Peter Lowe's Blocklist](https://pgl.yoyo.org/adservers/)
- [gorhill/uBlock 源码阅读指南（非官方）](https://github.com/gorhill/uBlock/wiki/Code-review)
