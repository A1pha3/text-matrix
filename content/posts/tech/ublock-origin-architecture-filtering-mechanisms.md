---
title: "uBlock Origin 架构解析：十余万条规则下，每次请求判定如何保持廉价"
date: "2026-04-30T10:07:00+08:00"
slug: "ublock-origin-architecture-filtering-mechanisms"
github_repo: "gorhill/uBlock"
source_key: "gh:gorhill/uBlock"
description: "对照源码拆解 uBlock Origin 的过滤体系：动态规则、静态引擎与页面层过滤的优先级链，token 索引、BidiTrie 与 WASM 如何让单次 URL 判定与规则库总量基本无关，并给出平台现状与规则编写建议。"
draft: false
categories: ["技术笔记"]
tags: ["开源", "性能优化"]
---

## 这篇文章在讲什么

拦截广告这件事，AdBlock Plus 十多年前就做熟了。uBlock Origin 真正下功夫的地方在别处：**当规则库膨胀到十余万条、一次页面加载要触发成百上千次网络请求判定时，让每一次判定依然便宜，内存占用依然克制。** 这不是靠堆机器得来的，而是过滤引擎的数据组织和判定顺序共同作用的结果。

这篇文章对照 uBO 的实际源码（2026 年 9 月的 master 分支，最新发布版 1.74.0），讲清三件事：

- 一次网络请求从发起到放行或拦截，在 uBO 内部真实经过的判定顺序；
- 静态过滤引擎怎么做到单次判定成本与规则库总量基本无关——这是它性能口碑的来源，也是这个项目里最值得借鉴的工程设计；
- 在默认规则不够用时，怎么用动态过滤和 scriptlet 写出精确的规则。

文中引用的文件路径都可以在 [gorhill/uBlock](https://github.com/gorhill/uBlock) 仓库中找到，机制描述以源码为准。

### 学习目标

按你的情况选一条路径：

- **想知道全貌**：读「系统总览」和「一个请求的完整流转」。
- **想读懂源码**：按「源码结构一览」的表格定位文件，配合「静态引擎的性能设计」逐层读。
- **想借鉴性能设计**：重点读「token 索引」和「hostname 匹配」两节，uBO 的核心取舍都在那里。
- **想自己写规则**：直接跳到「安装与平台现状」和「进阶：写一条高质量的过滤规则」。

### 目录

1. [系统总览：两个判定域，四种引擎](#系统总览两个判定域四种引擎)
2. [一个请求的完整流转](#一个请求的完整流转)
3. [源码结构一览](#源码结构一览)
4. [静态引擎的性能设计](#静态引擎的性能设计)
   - [token 索引：把逐条比对变成按词取候选](#token-索引把逐条比对变成按词取候选)
   - [hostname 匹配：BidiTrie 与 WASM](#hostname-匹配biditrie-与-wasm)
   - [结果缓存：网络层与页面层各一条](#结果缓存网络层与页面层各一条)
5. [动态过滤：用户自己的规则层](#动态过滤用户自己的规则层)
6. [页面层过滤：元素隐藏与 scriptlet 注入](#页面层过滤元素隐藏与-scriptlet-注入)
7. [资源重定向：不能直接拦的请求](#资源重定向不能直接拦的请求)
8. [安装与平台现状](#安装与平台现状)
9. [进阶：写一条高质量的过滤规则](#进阶写一条高质量的过滤规则)
10. [常见问题](#常见问题)
11. [自测](#自测)
12. [采用建议](#采用建议)
13. [资料口径说明](#资料口径说明)
14. [参考资源](#参考资源)

## 系统总览：两个判定域，四种引擎

uBO 的过滤体系按介入时机分成两个判定域：**网络域**在请求发出前做判定，**页面域**在文档解析和脚本执行阶段介入。每个域里有各自独立的引擎：

| 判定域 | 引擎 | 规则来源 | 介入时机 | 源码入口 |
|--------|------|----------|----------|----------|
| 网络 | 动态 URL 规则 | 用户手工添加 | 请求发出前，优先级最高 | `url-net-filtering.js` |
| 网络 | 动态主机防火墙 | 用户在弹出面板点选 | 请求发出前，次于 URL 规则 | `dynamic-net-filtering.js` |
| 网络 | 静态过滤引擎 | EasyList、EasyPrivacy 等社区列表 | 请求发出前，优先级最低 | `static-net-filtering.js` |
| 页面 | 元素隐藏（cosmetic） | `##` 选择器规则 | DOM 解析与变更时 | `cosmetic-filtering.js` |
| 页面 | scriptlet 注入 | `##+js()` 规则 | 页面脚本执行前 | `scriptlet-filtering.js` |

这几种引擎是叠加关系，不是三选一。同一个请求会依次穿过网络域的三层判定，任何一层给出明确结论就停止；页面域的规则则挂在所有通过了网络判定的请求背后。很多资料把 uBO 概括成「一张黑名单」，这个说法漏掉了动态层和页面层，也就解释不了它最实用的两个功能：单站点放行，和对反拦截脚本的精确反制。

## 一个请求的完整流转

用一个具体场景串起来：你在地址栏打开 `news.example.com`，这个页面要加载 `ad.doubleclick.net/ads.js`。

### 网络域：三层判定，从具体到通用

`webRequest` 的 `onBeforeRequest` 事件触发后，主进程里的 `filterRequest`（`src/js/pagestore.js`）开始工作。判定顺序写死在代码里，从最具体的规则层走向最通用的规则层：

**第一层，动态 URL 规则。** 用户在「我的规则」里写过的精确 URL 规则最先被查。命中且结果为拦截，请求到此结束。

**第二层，动态主机防火墙。** 这是弹出面板里那格矩阵背后对应的引擎——不过它只在设置里勾选「我是高级用户」后才参与判定，普通用户模式会跳过这一层。判定对象是三元组「来源站点、目标域名、请求类型」，命中 block 就拦，命中 allow 就放行，命中 noop 则不做结论，降级给下一层。

**第三层，静态过滤引擎。** 代码注释里写得很直白：`Static filtering has lowest precedence`。前面两层都没有给出结论（或结论是 noop），才会轮到 EasyList 这些社区规则。这一层的内部机制复杂得多，单独放到下一节细讲。

三层中任何一层给出 block，请求被拦截——或者被重定向替换（见「资源重定向」）；给出 allow，请求直接放行。整个网络判定在 `onBeforeRequest` 里同步完成，浏览器等结果出来才决定发不发这个请求，所以这一层的耗时直接叠加在页面加载上。

### 静态引擎内部：分词、取候选、精确匹配

假设请求走到了第三层。以规则 `||ad.doubleclick.net^` 为例，看引擎怎么判定：

**第一步，URL 分词。** 引擎把请求 URL 转成小写，按 `[0-9a-z%]` 字符集切成一个个 token（`urlTokenizer`，实现在 `static-net-filtering.js` 内部）。`https://ad.doubleclick.net/ads.js` 会切出 `https`、`ad`、`doubleclick`、`net`、`ads`、`js` 等词，每个词用 djb2 变体哈希压成一个整数——参与哈希的字符最多 7 个（源码里的 `MAX_TOKEN_LENGTH`），结果只保留低 28 位。

**第二步，按 token 取候选。** 关键的预处理发生在规则列表编译阶段：每条规则会从自己的匹配模式里挑出一个「信息量最大」的 token 作为索引键，挂到这个 token 的哈希桶下。匹配请求时，引擎拿 URL 的每个 token 去查桶，把可能匹配这条 URL 的少量规则捞出来。一个具体 token 的桶里通常只有几条规则；URL 里所有 token 都查不到桶的请求，一条候选规则都没有，直接放行。另外有一小部分规则模式太泛、提不出有效 token，它们被归入一个「无 token」集合，每次都要检查——这类规则在列表里是少数。

**第三步，逐条精确匹配。** 候选规则逐条做真正的匹配验证：模式在 URL 里定位，锚点语义逐个核验。对 `||ad.doubleclick.net^`，引擎先在 URL 里找到 hostname 区间的起点（`://` 之后），确认匹配位置落在 hostname 里、且前一个字符是 `.` 或恰好是起点——这样 `notad.doubleclick.net` 就不会被误判。多数候选在这一步被排除。正则规则同样先吃 token 红利——编译时尝试从正则模式里提取一个边界安全的 token 参与索引，URL 不含这个词就轮不到正则求值；带 `domain=` 这类限定的慢规则，域名检查还会排在正则求值之前，先筛掉明显不匹配的请求。

判定结果出来后走两个出口之一：拦截，或放行并允许请求发出。如果规则带了 `redirect=` 选项，拦截的形态不是断开，而是替换（见后文）。

### 页面域：拦截之后还有一轮

网络判定管不到页面内部的动作。页面开始解析时，uBO 的内容脚本已经注入（时机是 `document_start`，早于页面自己的脚本执行），它按当前 hostname 取出适用的 `##` 元素隐藏规则和 `##+js()` scriptlet 规则。假设这个站点还用一个内联脚本检测广告拦截器——那个脚本不产生网络请求，网络域对它无能为力，能制住它的是 scriptlet 注入。

一次页面加载走完，弹出面板上的拦截计数就是这些判定结果的累计。

## 源码结构一览

uBO 最初发布于 2015 年，GPLv3 协议，主体由 JavaScript 写成；少数计算密集的模块有 WebAssembly 版本（由 C 编译，见 `src/js/wasm/`），运行时优先加载。截至 2026 年 9 月，仓库 [gorhill/uBlock](https://github.com/gorhill/uBlock) 约有 6.8 万颗 Stars，最新发布版为 1.74.0（2026 年 8 月 25 日），主分支仍在活跃提交。

克隆仓库后，核心代码在 `src/` 下：

| 路径 | 做了什么 | 建议先读 |
|------|---------|---------|
| `src/js/background.js` | 扩展主进程，模块启动与生命周期 | ⭐ 入口 |
| `src/js/pagestore.js` | 每个标签页的判定入口，`filterRequest` 在这里 | ⭐ |
| `src/js/static-net-filtering.js` | 静态引擎主体，含 `urlTokenizer` 与全部 Filter 类 | ⭐⭐ |
| `src/js/static-filtering-parser.js` | 把 EasyList 文本规则解析成可编译结构 | ⭐ |
| `src/js/static-filtering-io.js` | 编译产物的序列化与磁盘加载 | |
| `src/js/url-net-filtering.js` | 动态 URL 规则 | |
| `src/js/dynamic-net-filtering.js` | 动态主机防火墙（弹出面板矩阵） | ⭐ |
| `src/js/cosmetic-filtering.js` | `##` 元素隐藏 | |
| `src/js/scriptlet-filtering.js` | `##+js()` scriptlet 注入 | ⭐ |
| `src/js/redirect-engine.js` | 被拦请求的重定向替换 | |
| `src/js/biditrie.js` | 双向 trie，hostname 与 pattern 的联合匹配 | ⭐⭐ |
| `src/js/hntrie.js` | hostname 集合 trie，服务 `domain=` 选项判断 | |
| `src/js/mrucache.js` | 页面层的 hostname 结果缓存 | |
| `src/js/lz4.js` | LZ4 压缩，用于缓存数据落盘 | |
| `src/js/resources/` | 内置 scriptlet 库（`set-constant.js` 等约 30 个） | |
| `src/web_accessible_resources/` | 重定向替身资源（`noop.js` 等） | |
| `src/js/wasm/` | WASM 模块（`hntrie.wasm`、`biditrie.wasm`） | |

想从源码理解性能设计，从 `static-net-filtering.js` 的 `urlTokenizer` 入手是效率最高的路径——整个静态引擎的取舍都围绕它展开。

## 静态引擎的性能设计

静态引擎要解决的问题规模是固定的：十余万条规则（EasyList、EasyPrivacy、Peter Lowe's Blocklist、Online Malicious URL Blocklist、uBO filters 这几套默认列表合计的量级，随列表更新浮动），每个页面加载几百上千次判定，全部同步执行。任何「对每条规则跑一遍正则」的方案在这里都直接出局。uBO 的答案分三部分。

### token 索引：把逐条比对变成按词取候选

静态引擎快，首先不是因为某个精巧的树结构，而是因为它**根本不给绝大多数规则参与判定的机会**。

规则编译阶段，每条规则从自己的匹配模式里提取 token 并注册到「token → 规则列表」的倒排索引里。提取逻辑偏向信息量：模式里越具体、越少见于其他规则的词，越适合做这条规则的索引键。这样做的效果是，匹配一个请求时，用 URL 里十来个 token 去查索引，捞出来的候选规则通常只有个位数。

对比一下两种朴素方案就明白这个设计的分量：

- 全量正则：十余万条规则 × 每次请求几百次调用，每次匹配都是全量扫描，成本与规则库总量成正比。
- 哈希表存完整 URL：精确但只对「逐字符写死」的规则有效，而广告规则的主要形态是「域名前缀 + 模式」，同一域名下有无数路径变体，穷举不完。

token 索引击中的正是规则库的真实形态：绝大多数规则的模式里都包含具体词。一次判定的成本约等于「URL 的 token 数 × 平均每桶候选数 + 少量精确匹配」，与规则库总量基本无关——规则从 10 万涨到 20 万，只要 token 桶不塌缩，单次判定耗时几乎不动。这是 uBO 相对早期拦截器最实质的架构优势。

### hostname 匹配：BidiTrie 与 WASM

token 索引解决「哪些规则值得看」，hostname 匹配解决「这条规则到底命中没有」里最费劲的一类判断。广告规则大量使用 `||域名` 形式，要求「模式锚定在 hostname 的左边界」，比如 `||ad.doubleclick.net^` 不该匹配 `evil-ad.doubleclick.net.evil.com` 里恰好出现的子串。

uBO 对这类判断有两件工具：

**`FilterAnchorHnLeft` / `FilterAnchorHn`**（`static-net-filtering.js`）：对单纯的 hostname 锚定，引擎在请求 URL 里定位 hostname 区间的起止（`://` 之后到第一个 `/` 之前），然后检查 pattern 的匹配位置是否落在区间内、且左邻字符是 `.` 或恰为区间起点。判断本身是几次字符比较，配合 token 索引筛过的候选，成本很低。

**BidiTrie**（`biditrie.js`）：对付更麻烦的 `||域名/路径` 形式——hostname 要从右往左对，路径要从左往右对，两头都要锚住。BidiTrie 的做法是把这两段放进同一块类型化数组缓冲区，hostname 按字符反向存储、pattern 正向存储，匹配时从两头的锚点向中间推进，任意一侧失配即失败。字符级比对被压缩成整数单元上的查表与比较，这是它比朴素字符串匹配快的原因。

这个模块还有一处工程取舍：同一算法有 JavaScript 和 WebAssembly 两个实现（`biditrie.js` 与 `src/js/wasm/biditrie.wasm`，后者由 C 编译），运行时优先加载 WASM 版本。hostname 匹配是整个引擎里单位时间执行次数最高的路径之一，值得为它维护一套 WASM 构建链——这也是「uBO 纯 JavaScript 项目」这个常见说法不准确的地方。

`hntrie.js` 则是另一个容器：把一组 hostname 按字符反向插入 trie，回答「某 hostname 是否属于这个集合」。它服务于规则的 `domain=` 选项这类集合归属判断，和 BidiTrie 分工不同。

### 结果缓存：网络层与页面层各一条

第三层节省来自「同样的判定不做第二遍」。

网络层，`pagestore.js` 对子框架（sub frame）这类请求缓存判定结果——同一页面里 iframe 的判定往往反复出现，缓存让重复判定变成一次哈希查找。范围是刻意收窄的：脚本、图片这些类型的判定本身已经很快，缓存收益抵不过管理成本。

页面层的缓存更重。一个页面在加载过程中会因 DOM 变更反复查询「当前 hostname 适用的选择器/scriptlet 集合」，而编译规则集合的开销不小。`mrucache.js` 提供的缓存让同一 hostname 的编译结果只算一次。顺带一个考据：这个文件名叫 MRU Cache，但实现上是「命中即把条目提到队首、队满从队尾淘汰」，行为上是标准 LRU——读源码时别被名字带偏。

## 动态过滤：用户自己的规则层

静态规则再精确，也是别人替你做的决定：列表不知道你是在看新闻还是登录网银，只能按域名一刀切。动态过滤把决定权交给用户，而且不需要写任何语法。

弹出面板的防火墙矩阵（需开启「我是高级用户」）按「来源站点 × 目标域名 × 请求类型」三要素组织。行是域名（当前站点、具体目标域、通配），列是请求类型（全部、内联脚本、第三方请求、第三方脚本、第三方框架）。每个格子有三种基本取值：

- **block**：拦掉这个方向的对应请求；
- **allow**：放行，且不再受更宽规则的拦截——包括静态规则，后续判定整段跳过；
- **noop**：本格不做结论，降级给更宽的规则或静态引擎处理。

格子的语义随具体程度递进：对 `example.com` 整站设的 block，会被对 `bank.example.com` 设的 allow 在那个子域上覆盖。这套机制的实际价值在于**可逆的例外**：某站坏了，面板里点一下放行它的脚本，不用碰规则文件，不用等列表更新，随时点回去。

实现上它非常轻：规则就是嵌套的键值映射，一次判定是一次哈希查找，规则总量通常不过几十条。这也是它敢排在静态引擎之前判定的底气——更具体的层判定成本反而更低，先走它不吃亏。

## 页面层过滤：元素隐藏与 scriptlet 注入

网络域管不到页面内部的两个场景：广告是 HTML 内联的（没有独立请求可拦），或者广告代码藏在页面自己的脚本行为里。页面域的两个引擎分别对应这两类问题。

**元素隐藏（cosmetic filtering，`cosmetic-filtering.js`）** 处理最常见的形态：广告内容已经在页面里了，把它隐藏掉。规则形如：

```text
! 在 example.com 上隐藏 class 为 ad-banner 的元素
example.com##.ad-banner
```

内容脚本按当前 hostname 取出适用的选择器，在 DOM 上应用 `display: none`。选择器按 hostname 建了索引，编译结果有 MRU 缓存，DOM 每次变更后的复查不用重新编译。这是 uBO 规则里使用频率最高的一类语法，也是多数用户感知「广告不见了」的直接原因。

**scriptlet 注入（`scriptlet-filtering.js`）** 处理更隐蔽的形态：页面脚本在运行时做的事，比如劫持函数、改写对象属性、检测拦截器。scriptlet 规则在页面脚本执行前（`document_start`）把预定义的脚本片段注入页面，替掉目标行为：

```text
! 在 example.com 上把 window.adBlockDetected 固定为 false，
  让反拦截检测读到「没装拦截器」
example.com##+js(set-constant, adBlockDetected, false)
```

`set-constant` 是内置 scriptlet 之一，全部内置实现放在 `src/js/resources/`，共约 30 个，各有固定名字和参数表。这里有一个容易写错的语法点：`##+js()` 的第一个参数是 **scriptlet 名字**，不是域名——`##+js(example.com, alert, 1)` 这种写法不合法，域名应该写在规则左侧的站点限定里。

不让用户直接写任意 JS 是安全设计：任意脚本能力意味着 `eval` 注入面，而 scriptlet 模板是经过审核的固定集合，参数再怎么组合也逃不出预设的行为。

页面域的能力边界也要说清：scriptlet 注入改不了**外部脚本文件**的执行上下文。如果广告代码是一个外部 JS 文件，网络域没拦住它，scriptlet 也无法介入它的内部逻辑——那种场景的对策是下一节的重定向。

## 资源重定向：不能直接拦的请求

有一类请求，拦截本身就是失败：站点加载 `detect-adblock.js` 来探测拦截器，直接拦截会让脚本加载失败，站点立刻弹窗要求你关闭拦截器。uBO 的对策在 `redirect-engine.js`：**不拦截，替换**。把响应换成内置的无害资源，脚本「加载成功」，内容是空操作。

```text
||ads.example.com/detect-adblock.js$script,redirect=noop.js
```

`noop.js` 就是一个空脚本。内置替身资源放在 `src/web_accessible_resources/`，除 `noop.js` 外还有 `1x1.gif`、`noop.css`、`noop.html` 等，覆盖常见的广告 SDK 探测和统计打点场景。

重定向的能力边界同样明确：它只作用于网络请求层面。检测逻辑如果写在页面自身的内联 JS 里（比如检查某个全局变量的值），重定向引擎碰不到它——那要靠 scriptlet 注入去改写那个变量。实际规则里常见的手法是把两者组合：`redirect=` 应付网络层的探测脚本，`set-constant` 应付页面层的检测结果。

## 安装与平台现状

这一节的内容有较强的时效性（写作时点：2026 年 9 月）。

- **Firefox**：目前体验最完整的平台，[AMO 扩展商店](https://addons.mozilla.org/firefox/addon/ublock-origin/)可装。uBO 官方 README 明确写着「works best on Firefox」——Firefox 保留了 `webRequest` 的阻塞式拦截能力，上面讲的引擎机制在 Firefox 上完整可用。
- **Chromium 系（Chrome / Edge 等）**：Chrome 自 2025 年起全面停用 Manifest V2 扩展，原版 uBO 依赖的阻塞式 `webRequest` API 在 MV3 中被移除，**原版 uBO 在 Chrome 上已被禁用**。官方的 MV3 替代品是 [uBlock Origin Lite](https://github.com/uBlockOrigin/uBOL-home)，用声明式规则（`declarativeNetRequest`）实现过滤；代价是本文讲的动态防火墙和完整规则语法都不可用，过滤能力明显收窄。Edge 等其他 Chromium 浏览器也在跟进同样的 MV2 淘汰节奏。
- **Opera**：同样基于 Chromium，受 MV2 停用影响，情况与 Chrome 相同。

安装后，工具栏图标的弹出面板显示当前页面的拦截计数。日常使用三步：电源按钮控制开关；点面板底部的域名区可以把当前站点加入白名单；默认启用的几套列表（EasyList、EasyPrivacy 等）对多数人已经够用。

勾选「我是高级用户」后解锁本文提到的进阶能力：弹出面板的防火墙矩阵、实时日志查看器（Logger，能看到每个请求命中了哪条规则、被哪层判定处理）、以及「我的规则」手动编辑。

## 进阶：写一条高质量的过滤规则

会写规则之后，你面对「这个怎么还在」的时刻就不必等列表更新了。三个从简到繁的例子：

### 例 1：限定条件拦一个域名

```text
||annoying-widget.com^$script,domain=example.com
```

- `||` 锚定域名及其子域名的左边界；
- `^` 匹配分隔符（`/`、`?`、URL 结尾等）；
- `$script` 只对脚本请求生效；
- `domain=example.com` 只在 `example.com` 上生效。

### 例 2：白名单例外

```text
@@||cdn.example.com^$script,domain=example.com
```

`@@` 开头表示例外规则：即使其他规则拦了 `cdn.example.com` 的脚本，这条会放行它。误杀修复基本都靠这个语法。

### 例 3：用 scriptlet 制住页面内行为

```text
example.com##+js(set-constant, adBlockDetected, false)
```

在 `example.com` 的页面里，把 `window.adBlockDetected` 固定为 `false`。适合对付不产生网络请求、纯靠页面内变量传递结果的检测逻辑。选 scriptlet 前先到 `src/js/resources/` 看有哪些现成实现，多数需求不用自己造。

### 三条书写原则

1. **限定条件给足**：能加 `$script` 就不裸写域名，能加 `domain=` 就不全局生效。限定越具体，误杀概率越低，也越容易被 token 索引高效处理。
2. **少用正则**：正则求值本身比字符串定位贵得多；能安全提取 token 的正则虽然也走索引，但落进候选后每条都要真跑一遍正则引擎。`||` 和 `^` 能表达清楚的不要上 `/regex/`。
3. **用 Logger 验证**：规则写完打开 Logger 访问目标页面，看它是否命中、命中在哪一层。肉眼猜规则行为几乎必然出错。

## 常见问题

**Q：uBO 和 AdBlock Plus 有什么本质区别？**

两个层面。产品层面，ABP 参与「可接受广告」计划——给广告费就能进白名单；uBO 不参与任何广告资助，README 原话是「Free. Open-source. For users by users. No donations sought.」。工程层面，uBO 的判定顺序和 token 索引是为「规则库很大」这个前提专门设计的，同样的社区列表在 uBO 上的 CPU 与内存开销更低——这是官方 README「CPU and memory-efficient」的自述方向，也是社区反复对比过的定性结论；至于具体低多少，没有可靠的统一数字，取决于规则集和页面，别轻信任何精确的倍数。

**Q：开了 uBO，为什么有些广告还是拦不掉？**

三种常见原因。广告是页面内联的，不产生网络请求——开 Logger 看不到对应记录，对策是 `##` 元素隐藏规则。广告域名不在你启用的列表里——检查设置里的列表勾选。站点用了动态生成的广告域名——写更宽的通配规则，或者用 scriptlet 从页面行为层面处理。

**Q：uBO 会不会拖慢浏览器？**

任何内容拦截器都要为每个请求做判定，增量是必然存在的，问题只是大小。uBO 的设计目标就是把这个增量压到不可感知——上面讲的 token 索引、trie、缓存都是为此服务的。多数页面上，它拦掉的追踪脚本原本要消耗的 CPU 远高于它自身的判定开销，净效果是页面变快。

**Q：为什么弹出面板的计数不动？**

先确认没有对该站点或全局设置暂停。然后注意计数只统计真实发生的请求：命中的是浏览器缓存或 Service Worker 的资源不触发新的判定，计数自然不变。

**Q：怎么排查一条规则为什么没生效？**

开启高级用户模式，打开 Logger（弹出面板的日志图标），访问目标页面。Logger 会列出每个请求经过的判定链路：被哪层、哪条规则处理，还是一路放行。如果目标请求根本没出现在列表里，说明它在更早的阶段被处理，或者压根没有发出。

## 自测

不看原文回答下面的题目，答不出的回到对应小节重读。

1. **uBO 对一个网络请求的判定顺序是什么？为什么静态引擎排在最后？**
   <details>
   <summary>参考答案</summary>
   动态 URL 规则 → 动态主机防火墙（仅高级用户模式）→ 静态过滤引擎。静态规则最通用也最「他不认识你」，而动态规则更具体、量更小、判定更便宜，先判具体层既尊重用户意图又几乎不增加成本；静态引擎垫底保证社区规则不会覆盖用户明确表达的意图。
   </details>

2. **静态引擎怎么做到单次判定成本与规则库总量基本无关？**
   <details>
   <summary>参考答案</summary>
   规则编译期从模式提取 token 建倒排索引；匹配时用请求 URL 的 token 查索引，只有命中桶的少数候选规则进入精确匹配。判定成本取决于 URL 的 token 数和桶的平均大小，规则库总量翻倍并不直接增加任何一次判定的开销。
   </details>

3. **`||ad.doubleclick.net^` 为什么不会误匹配 `notad.doubleclick.net.evil.com`？锚定判断是怎么做的？**
   <details>
   <summary>参考答案</summary>
   引擎在请求 URL 里定位 hostname 区间（`://` 之后），要求模式匹配位置落在区间内、且左邻字符是 `.` 或恰为区间起点——`notad...` 的匹配位置左邻是 `t`，不满足；`.evil.com` 结尾则意味着匹配位置虽在 hostname 里但整体前缀不成立。复杂形态的「hostname + 路径」联合锚定由 BidiTrie 完成：两段字符存进同一缓冲区，hostname 反向、pattern 正向，从两个锚点向中间推进匹配。
   </details>

4. **动态过滤的 block / allow / noop 各是什么语义？noop 存在的意义是什么？**
   <details>
   <summary>参考答案</summary>
   block 拦截对应方向的请求；allow 放行并免受动态层更宽规则影响；noop 表示本格不做结论，判定降级给更宽的动态规则或静态引擎。noop 的意义是「在这个具体维度上我不表态」——让管理员设的全局规则继续管，而不用为了放开某格删掉整条规则。
   </details>

5. **`##+js(example.com, alert, 1)` 这条规则错在哪里？scriptlet 对外部脚本文件有效吗？**
   <details>
   <summary>参考答案</summary>
   `##+js()` 的第一个参数必须是内置 scriptlet 的名字（如 `set-constant`），域名应写在规则左侧的站点限定位置，这条规则把域名当 scriptlet 名，不合法。scriptlet 注入改不了外部脚本文件的执行上下文——外部脚本要在加载环节用网络层规则拦截或重定向替换。
   </details>

6. **元素隐藏和资源重定向各解决什么问题？两者的盲区分别在哪？**
   <details>
   <summary>参考答案</summary>
   元素隐藏处理「内容已在页面里」的广告，靠选择器隐藏节点，盲区是内容以脚本行为存在（不渲染成固定节点）的情况；重定向处理「拦截会触发反拦截检测」的请求，靠替换响应体瞒过检测，盲区是写在页面内联脚本里的检测逻辑——那要靠 scriptlet 改写变量。三者组合才是完整对策。
   </details>

## 采用建议

- **Firefox 用户**：直接装 uBO，默认配置即可。想进阶，先开高级用户模式玩几天防火墙矩阵，再学写规则。
- **Chrome 用户**：原版 uBO 已无法使用。想要过滤能力就装 uBlock Origin Lite，接受它的能力收窄；如果 MV2 级别的过滤和动态规则对你很重要，换 Firefox 是比折腾替代品更省力的路线。
- **受管环境**：企业策略锁了扩展安装就别纠结，这不是软件能解决的问题。
- **想读源码的工程师**：uBO 值得精读的不是广告拦截本身，而是「规模固定的冷数据 + 海量重复查询」这类问题的通用解法——倒排索引、紧凑 trie、判定顺序、缓存收窄。建议顺序：`pagestore.js` 的 `filterRequest` 看清判定链 → `static-net-filtering.js` 的 `urlTokenizer` 与 Filter 类看懂主路径 → `biditrie.js` 与 `src/js/wasm/` 看 WASM 落点 → `cosmetic-filtering.js`、`scriptlet-filtering.js` 看页面层的同类取舍。

## 资料口径说明

1. **事实来源**：本文机制描述对照 gorhill/uBlock 主分支源码（2026-09-12 提交），版本号与 Stars 数取自 GitHub（release 1.74.0，2026-08-25；Stars 约 6.8 万，2026-09-13 查询）。初稿发布于 2026-04-30，2026-09-13 按源码全面核实修订。
2. **未实测的部分**：本文未做系统性能测试，判定顺序、数据结构、缓存范围均以源码为准；涉及性能的说法只到定性层面，未给出量化数字。
3. **时效边界**：Chrome 对 MV2 的停用状态、uBO Lite 的功能范围都在演进中，阅读时请以官方仓库与 Chrome 开发者文档的最新说明为准。
4. **规则语法**：本文只覆盖常用子集，完整语法以 [官方 Wiki 的过滤语法页](https://github.com/gorhill/uBlock/wiki/Static-filter-syntax) 为准。

## 参考资源

- [gorhill/uBlock 官方仓库](https://github.com/gorhill/uBlock)
- [uBlock Origin Wiki — Static Filter Syntax](https://github.com/gorhill/uBlock/wiki/Static-filter-syntax)
- [uBlock Origin Wiki — Dynamic Filtering: Quick Guide](https://github.com/gorhill/uBlock/wiki/Dynamic-filtering:-quick-guide)
- [uBlock Origin Lite（MV3 版）仓库](https://github.com/uBlockOrigin/uBOL-home)
- [EasyList 规则列表](https://easylist.to/)
- [Peter Lowe's Blocklist](https://pgl.yoyo.org/adservers/)
