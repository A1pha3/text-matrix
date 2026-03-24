---
title: "Hugo 静态网站如何查看访问数据？三种主流方案全解析"
date: 2026-03-23T10:00:00+08:00
draft: false
tags: ["Hugo", "网站统计", "LoveIt", "教程"]
categories: ["技术分享"]
---

> **🎯 学习目标**
> 
> 读完本文，你将了解：
> 1. 静态网站获取访问数据的基本原理。
> 2. 如何利用部署平台（如 Vercel、Cloudflare、GitHub）的自带功能查看流量。
> 3. 如何在 Hugo（特别是 LoveIt 主题）中配置 Google Analytics (GA4)。
> 4. 如何利用 Hugo 的“模板覆盖”机制，优雅地接入未被原生支持的工具（如百度统计）。

当你用 Hugo 精心搭建好自己的静态网站（比如使用漂亮的 LoveIt 主题），写下几篇得意的文章后，一定会产生一个自然的好奇心：**“到底有多少人看了我的文章？他们是从哪里来的？”**

传统动态网站（如 WordPress）通常有自带的后台数据库来记录访问日志，但**纯静态网站（HTML + CSS + JS）本身并没有后台服务器**。

别担心，静态网站不仅能看访问数据，而且有比传统网站更轻量、更优雅的解决方案。今天，我们就来盘点 3 种最好用、最主流的查看网站访问数据的方法。无论你是“伸手党”还是“数据控”，总有一款适合你。

---

## 方案一：部署平台自带的“零配置”统计（懒人首选）

如果你不想在代码里加任何东西，也不想让读者被各种追踪脚本拖慢网页加载速度，那么**部署平台自带的统计分析（Web Analytics）**是你的最佳选择。

### 为什么推荐？
- **零配置**：不需要修改任何代码，一键开启。
- **数据精准**：因为是在边缘节点直接统计网络请求，**不会被浏览器的“广告拦截插件”（如 AdBlock）屏蔽**。
- **隐私友好**：通常不需要收集用户的 Cookie，符合 GDPR 等隐私法规。

### 常见平台如何查看：

1. **Cloudflare Pages / Vercel / Netlify**
   如果你把网站托管在这些现代平台上，登录它们的控制台，找到你的项目，点击 **Analytics**（分析）选项卡。点击开启（Enable）后，你就能看到非常直观的访问量（PV）、独立访客数（UV）和来源页面了。
2. **GitHub Pages**
   如果你的网站直接托管在 GitHub 的 `gh-pages` 分支上，可以在对应代码仓库的页面，点击顶部的 **Insights**（洞察），再点击左侧的 **Traffic**（流量）。这里会显示最近 14 天内的克隆数和访客数据。

> 💡 **一句话总结**：适合只想看个大致访问量、不想折腾代码的同学。

---

## 方案二：配置 Google Analytics 4（数据控最爱）

如果你想知道非常详尽的数据：访客用的什么手机？停留了多少秒？从哪个搜索引擎搜了什么关键词进来的？那么老牌霸主 **Google Analytics（GA4）** 绝对是首选。

幸运的是，如果你使用的是 **LoveIt** 主题，它已经**原生内置**了 Google Analytics，配置起来易如反掌。

### 操作步骤：

1. **获取衡量 ID**
   前往 [Google Analytics 官网](https://analytics.google.com/) 注册并创建一个“媒体资源”（Property）。完成基础设置后，你会获得一个以 `G-` 开头的**衡量 ID**（例如 `G-ABC123XYZ`）。

2. **修改 Hugo 配置文件**
   打开你网站根目录下的 `hugo.toml`（或 `config.toml`），找到关于 `[params.analytics]` 的配置区块（LoveIt 主题一般在文件靠后的位置）。将你的 ID 填入并开启即可：

   ```toml
   # 网站分析配置
   [params.analytics]
     enable = false # 注意：这里的 enable 通常用于控制是否在页面底部显示可见的计数器UI，建议保持 false 即可。
     
     # Google Analytics 配置
     [params.analytics.google]
       id = "G-ABC123XYZ" # 在这里替换为你的衡量 ID
       # 是否遵循浏览器的 “Do Not Track” 设置
       respectDoNotTrack = false
   ```

3. **重新部署**
   保存文件，重新生成并部署你的网站。过几个小时后，你就能在 GA 后台看到实时的访问数据了。

> 📌 **扩展知识**：LoveIt 主题不仅支持 Google Analytics，还原生支持 `Fathom`、`Plausible` 和 `Yandex Metrica`。如果你偏爱这些更注重隐私的第三方服务，只需在 `hugo.toml` 的对应字段下填入 ID 即可。

---

## 方案三：手工接入“百度统计”（国内特化版）

如果你的网站受众主要在国内，Google Analytics 有时加载会比较慢，甚至部分地区访问不畅。这时候，**百度统计**是一个很好的平替。

虽然 LoveIt 主题的配置文件里没有直接提供百度统计的填写位置，但我们可以利用 Hugo 强大的**“模板覆盖（Template Override）机制”**来优雅地解决这个问题。

### 什么是“模板覆盖”？
Hugo 有一个非常棒的特性：如果在项目根目录的 `layouts/` 下创建了与 `themes/主题名/layouts/` 结构完全相同的文件，**Hugo 编译时会优先使用根目录下的文件**。这样我们就不用去修改主题源码（方便以后主题升级），又能加入自己的定制代码。

### 操作步骤：

1. **创建覆盖文件**
   在你的项目根目录下，按照 LoveIt 主题的目录结构，新建多层文件夹和文件，路径如下：
   `layouts/partials/plugin/analytics.html`

2. **复制并修改代码**
   打开主题里的原文件：`themes/LoveIt/layouts/partials/plugin/analytics.html`，将其中的所有代码复制到你刚刚新建的空文件中。

3. **贴入百度统计代码**
   去 [百度统计后台](https://tongji.baidu.com/) 添加你的网站，获取它提供给你的追踪代码（一段包含 `<script>...</script>` 的 HTML 代码）。
   
   将这段代码直接粘贴到你新建的 `analytics.html` 文件的**最底部**。例如：

   ```html
   {{- /* 上面是复制过来的原有代码，保持不动 */ -}}
   
   {{- /* 下面是新加的百度统计代码 */ -}}
   <script>
   var _hmt = _hmt || [];
   (function() {
     var hm = document.createElement("script");
     hm.src = "https://hm.baidu.com/hm.js?你的百度统计特征码";
     var s = document.getElementsByTagName("script")[0]; 
     s.parentNode.insertBefore(hm, s);
   })();
   </script>
   ```

4. **大功告成**
   保存文件并部署网站。你的页面就同时拥有了原有的统计功能和百度统计了！

---

## 🏆 总结建议：怎么选最适合你？

- **如果你是极简主义者**：用 Vercel / Cloudflare 部署，直接看平台自带的控制台，干净清爽。
- **如果你想看深度数据，且受众偏海外**：使用 **Google Analytics 4**，只需在 `hugo.toml` 改两行配置。
- **如果你主要面向国内读者，需要加载快**：利用 Hugo 模板覆盖机制，手工接入**百度统计**。

为网站添加统计不仅能让你知道“有多少人来看”，更能给你带来持续创作的成就感。赶快动手给你的 Hugo 博客加上数据追踪吧！
