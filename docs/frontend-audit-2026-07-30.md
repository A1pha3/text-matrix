# Text Matrix 前端界面优化审查报告

> 审查日期：2026-07-30 · 基于本地构建产物（`public/`）与模板源码（`layouts/`、`assets/`、LoveIt 主题）

## 结论概览

有优化空间，且集中在**第三方静态资源**上。站点本身的设计系统（纸墨编辑风、teal/stone 双主题、hairline 分区）已经成熟，HTML 结构干净（首页仅 16KB），自定义 CSS 质量高。问题不在"界面"，而在"界面背后的资源管线"。

当前每页固定开销：

| 资源 | 体积 | 加载方式 | 评价 |
|---|---|---|---|
| style.min.css | 99 KB | 渲染阻塞 | 合理（LoveIt 基座） |
| fontawesome all.min.css | 75 KB | preload 异步 | 浪费严重 |
| FA webfonts | 242 KB | 按需 | 浪费严重 |
| animate.min.css | 71 KB | preload 异步 | 可裁剪 |
| theme.min.js | 24 KB | 页面底部 | 良好 |
| mermaid.min.js | 2.64 MB | 仅 185 篇图表面页 | 最大单项负载 |

## P0 — 高收益优化

### 1. Font Awesome 全量引入（约 -300 KB）

模板实际引用的 FA 图标类约 62 个（其中大量是分享按钮图标，如 diaspora、evernote、get-pocket 等，分享功能未必全开）。真实渲染所需估计不足 20 个，却加载了整套 75 KB CSS + 242 KB 字体。

**方案**（按收益排序）：
- 内联 SVG 图标替换 `<i class="fas fa-...">`，彻底移除 FA 依赖（头部搜索/主题切换/返回顶部/评论等图标都是简单图形）
- 或用 [fontawesome-subsetter](https://www.npmjs.com/package/fontawesome-subsetter) 生成子集字体，CSS 裁到 <10 KB

**涉及文件**：`layouts/partials/head/link.html`（第 49-57 行）、`themes/LoveIt/layouts/partials/assets.html`

### 2. Mermaid 延迟初始化（185 篇文章受益）

`<script src="/lib/mermaid/mermaid.min.js">` 无 `defer`，2.64 MB 在页面底部同步加载解析。虽然只在 frontmatter 标了 `mermaid: true` 的页面加载，但对这些页面仍是沉重的 TTI 负担。

**方案**：
- 短期：给 script 标签加 `defer`，并改为 IntersectionObserver 进入视口后再 `mermaid.init()`
- 长期最优：构建期把 mermaid 代码块渲染成内联 SVG（ Hugo render hook + mermaid-cli），运行时零 JS，顺带解决暗色主题切换时图表配色问题

**涉及文件**：`themes/LoveIt/layouts/partials/assets.html`（第 132-136 行，建议复制到 `layouts/partials/` 覆盖而非改主题）

### 3. animate.css 裁剪（约 -60 KB）

71 KB 全量动画库，实际用到的关键帧估计只有 `fadeIn`/`fadeInUp` 等少数几个。且站点已声明 `prefers-reduced-motion` 降级，动画本就是装饰层。裁到实际用量或改手写 20 行 keyframes。

**涉及文件**：`layouts/partials/head/link.html`（第 59-62 行）

## P1 — 中等收益

### 4. 缺少 preconnect / dns-prefetch

全站 0 条资源提示。AdSense（autoAds 开启）至少涉及 3 个第三方域名：

```html
<link rel="preconnect" href="https://pagead2.googlesyndication.com" crossorigin>
<link rel="preconnect" href="https://googleads.g.doubleclick.net" crossorigin>
<link rel="dns-prefetch" href="https://fundingchoicesmessages.google.com">
```

**涉及文件**：`layouts/partials/adsense/head.html`（在脚本注入前加提示）

### 5. AdSense autoAds 的 CLS 风险

`autoAds = true` 让 Google 自动决定广告插入位置，是内容站 CLS 超标的最常见原因。建议改为手动广告单元 + CSS 预留 `min-height` 容器，把布局抖动锁在广告槽内。

**涉及文件**：`hugo.toml`（`params.adsense`）、`layouts/shortcodes/adsense.html`

### 6. theme-color 与品牌不符

当前 `<meta name="theme-color" content="#ffffff">`，与品牌色 `#faf9f7`（亮）/ `#131211`（暗）不符，且没有暗色变体：

```html
<meta name="theme-color" content="#faf9f7" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#131211" media="(prefers-color-scheme: dark)">
```

影响移动端浏览器地址栏/PWA 沉浸式体验。**涉及文件**：主题 `head/meta.html`（复制到 `layouts/partials/head/` 覆盖）

### 7. 部署瘦身：mermaid lib 全目录发布

`public/lib/mermaid/` 占 13 MB，运行时只需要 `mermaid.min.js`。可在部署流程中排除其余文件（构建后清理或 CI 瘦身），不影响运行时但显著减少上传/CDN 同步时间。

## P2 — 打磨项

### 8. 可访问性补强

- **缺 skip-to-content 链接**：`baseof.html` 的 `<body>` 起始处没有跳转到主内容的链接，键盘用户每页都要 Tab 穿过整个导航
- 移动端菜单展开状态建议加 `aria-expanded` 同步
- 检查项：搜索框展开后焦点是否自动落入 input

### 9. SEO 细节

- `og:locale` 输出为 `zh`，规范值应为 `zh_CN`
- 考虑给文章页 JSON-LD 补 `BlogPosting`/`TechArticle` 类型（当前只有全站 `WebSite`），对 1300+ 篇文章的富摘要展示有直接帮助

### 10. 图片现代化（低优先级）

全站图片仅 380 KB，且已有 lazysizes 懒加载，现状良好。若后续配图增多，可在 render hook 里统一输出 `loading="lazy" decoding="async"` 并逐步转 WebP。

## 一个流程提醒

当前 `public/` 是由 `hugo server` 生成的（首页 HTML 内含 `livereload.js`）。对外部署前务必用 `sh scripts/build_hugo.sh` 重新构建生产版本，否则 dev 脚本会发布上线。

## 实施建议顺序

1. **FA 子集化 + animate.css 裁剪**（纯减重量，无行为变化，约 -360 KB）
2. **mermaid defer + 视口初始化**（185 页 TTI 立刻改善）
3. **preconnect + theme-color + skip link**（半小时工作量）
4. **AdSense 手动槽位**（需要观察广告收入变化，单独做）
5. **构建期 mermaid→SVG**（架构级优化，可作为下个大版本目标）

完成 1-3 后，Lighthouse Performance 预计可达 95+（无广告页），CLS 风险显著下降。

---

## 实施状态（2026-07-30 当日完成）

| 项目 | 状态 | 结果 |
|---|---|---|
| P0-1 FA 子集化 | ✅ 完成 | 314KB → 21KB，收编本地（`scripts/subset_fontawesome.py`） |
| P0-2 mermaid 懒加载 | ✅ 完成 | 2.6MB 移出首载，stub 代理零侵入 + 收编本地（实测 jsDelivr 需 11.7s） |
| P0-3 animate.css 裁剪 | ✅ 完成 | 70KB → 6.2KB，收编本地（`scripts/subset_animatecss.py`） |
| P1-4 preconnect | ✅ 完成 | AdSense 4 条 preconnect/dns-prefetch |
| P1-6 theme-color | ✅ 完成 | 单标签 + MutationObserver 同步（含手动切换），品牌双色 |
| P2-8 skip-to-content | ✅ 完成 | 首个 Tab 聚焦即达，目标 #main-content |
| P2-9 og:locale | ✅ 完成 | `zh` → `zh_CN`（hugo.toml 顶层 locale 字段） |
| P2-9 文章页 JSON-LD | ⏭️ 无需做 | 主题已内置 BlogPosting（headline/datePublished/description 齐全，已验证有效） |
| P1-5 AdSense 手动槽位 | ⏸️ 冻结 | 见下方评估 |
| 构建期 mermaid→SVG | 📋 长期项 | 下个大版本 |

### AdSense CLS 评估（保持 autoAds 的决策依据）

- **不动收入配置是安全底线**：手动槽位需要在 AdSense 后台创建广告单元、改 hugo.toml、布点 shortcode，且自动广告的填充率和位置优化通常优于手工布点，贸然切换有收入下行风险。
- **当前无 CLS 异常证据**：没有 Search Console / CrUX 实测数据表明确诊 CLS 超标；该站正文以文字为主，自动广告插入频率受 Google 密度控制。
- **已做的缓解**：preconnect 缩短广告脚本加载，间接降低迟滞插入概率。
- **触发条件**：若 Search Console「核心网页指标」报告文章页 CLS 超标（>0.1），再启手动槽位方案（广告容器 `min-height` 预留 + 禁用内容内自动插入，仅保留锚定/穿插）。
