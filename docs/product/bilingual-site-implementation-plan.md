# Text Matrix 双语网站实施计划

## 文档信息

- 文档名称：Text Matrix 双语网站（中英）实施计划
- 适用范围：站点多语言架构、URL 结构、内容约定、模板改造、SEO、搜索、翻译工作流
- 当前版本：V1.0
- 撰写时间：2026-08-19
- 对应项目：`text-matrix`
- 文档状态：评审稿（审阅通过后再执行）

---

## 1. 背景与目标

### 1.1 背景

站点目前全部为中文内容（约 1726 篇 Markdown 文章），目标用户限定在中文开发者群体。为扩大流量来源，需要增加英文版本，将站点升级为中英双语网站。

### 1.2 目标

- **简洁**：不迁移、不重命名任何现有中文内容文件，改动面最小
- **优雅**：语言切换、译文配对、hreflang、fallback 全部由 Hugo 原生机制 + 主题既有能力承担
- **高效**：框架一次搭好，后续每篇英文文章的增量成本 = 只新增一个 `.en.md` 文件
- **强大**：双语搜索、双语 RSS、双语 sitemap、SEO 互指全部就位
- **强壮**：无译文的页面有明确 fallback；中文站现有 URL 与 SEO 零损失；构建与验证链路不破坏

### 1.3 非目标（本期不做）

- 不做 1726 篇存量文章的批量翻译（已确认：只搭框架，按需逐篇翻译）
- 不引入翻译平台、不做机器翻译后处理流水线
- 不增加中文之外的第三种语言（架构预留，见 §10）

---

## 2. 现状勘察结论

### 2.1 有利条件

| 事项 | 现状 | 结论 |
|---|---|---|
| 主题语言切换器 | LoveIt 主题 `themes/LoveIt/layouts/partials/header.html` 第 61-75 行（桌面端）与 154-167 行（移动端）已内置 language-select 下拉框 | 配置多语言后自动启用，UI 零开发 |
| 无译文 fallback | 主题 header 中，当前页无对应译文时下拉框指向 `{LanguagePrefix}/404.html` | fallback 行为主题已内置 |
| sitemap hreflang | `themes/LoveIt/layouts/sitemap.xml` 第 32 行已遍历 `.Translations` 输出 `xhtml:link` | 无需改动 |
| 主题 i18n 词条 | `themes/LoveIt/i18n/` 已含 `en.toml` 与 `zh-CN.toml`（共 26 语言） | 主题内置文案（"阅读时长"等）自动切换 |
| Hugo 原生多语言 | Hugo multilingual mode 成熟稳定 | 无需插件 |

### 2.2 需要改造的点

| 事项 | 位置 | 问题 |
|---|---|---|
| 站点配置 | `hugo.toml` | 无 `[languages]` 结构；`[menu]` 为中文写死 |
| 自定义布局硬编码中文 | `layouts/index.html`、`layouts/search/single.html`、`layouts/_default/section.html`、`layouts/taxonomy/terms.html`、`layouts/partials/single/footer.html`、`layouts/partials/head/meta.html`、`layouts/partials/header.html`（共 7 个文件） | 含"技术笔记""本周重点""全部 →"等中文硬编码 |
| 首页分类路径 | `layouts/index.html` | `GetPage "/categories/技术笔记"` 等 4 处中文 term 路径写死 |
| head hreflang | `layouts/partials/head/link.html`（站点已覆写主题文件） | 缺 `<link rel="alternate" hreflang>` |
| 搜索页 | `content/search.md` | 只有中文版，需补英文搜索页 |
| 分类体系 | 文章 frontmatter | 分类为中文名（技术笔记等），英文文章需英文分类名 |

---

## 3. 方案选型

### 3.1 内容组织方式对比

| 方案 | 做法 | 优点 | 缺点 | 结论 |
|---|---|---|---|---|
| **A. 文件名后缀（选用）** | 同目录 `foo.md`（中文）+ `foo.en.md`（英文） | 现有 1726 个文件零移动；Hugo 自动配对译文；git diff 友好；增量翻译只新增文件 | 目录里中英文文件混排 | **采用** |
| B. contentDir 分目录 | `content/zh-cn/...` + `content/en/...` | 目录按语言隔离 | 需移动全部现有文件，破坏 git 历史与所有引用路径，迁移风险极高 | 否决 |
| C. 独立仓库/子域名 | `en.txtmix.com` 独立站点 | 完全隔离 | 两套构建、两份主题维护、内容同步困难 | 否决 |

### 3.2 URL 结构（已定）

- `defaultContentLanguageInSubdir = false`
- 中文（默认语言）：`https://txtmix.com/posts/...` —— **与现状完全一致，零 SEO 损失**
- 英文：`https://txtmix.com/en/posts/...`
- 双语文章 URL 除 `/en/` 前缀外完全对应（通过保持相同 slug 实现，见 §6.2）

### 3.3 翻译策略（已确认）

- 只搭双语框架，不做批量翻译
- 英文译文由 coding agent 按需逐篇生成：指定一篇中文文章 → 生成同目录 `.en.md`
- 无译文的文章：语言切换器指向英文站 404（主题内置行为），不影响阅读

---

## 4. 详细设计

### 4.1 hugo.toml 多语言配置

将顶层语言配置收敛进 `[languages]`，菜单按语言拆分：

```toml
baseURL = 'https://txtmix.com/'
hasCJKLanguage = true
defaultContentLanguage = "zh-cn"
defaultContentLanguageInSubdir = false
theme = "LoveIt"

[languages]
  [languages.zh-cn]
    weight = 1
    languageCode = "zh-CN"
    languageName = "简体中文"
    title = "Text Matrix"
    [languages.zh-cn.params]
      description = "面向中文开发者的 AI Agent、AI 开发工作流与开源工具知识库。"
    # 现有 5 个中文菜单项原样迁入
    [[languages.zh-cn.menu.main]]
      identifier = "tech"
      name = "技术笔记"
      url = "/categories/技术笔记/"
      weight = 1
    # ... news / video / wealth / thoughts 同理

  [languages.en]
    weight = 2
    languageCode = "en"
    languageName = "English"
    title = "Text Matrix"
    [languages.en.params]
      description = "A knowledge base of AI agents, AI dev workflows and open-source tools."
    [[languages.en.menu.main]]
      identifier = "tech"
      name = "Tech Notes"
      url = "/categories/tech-notes/"
      weight = 1
    # ... 其余 4 项见 §4.2 映射表
```

注意事项：

- 顶层保留 `locale = 'zh_CN'`（LoveIt 主题参数，控制日期格式等）不变；英文站该参数由语言上下文自动处理，无需单独设置
- `[params]` 其余全局配置（adsense、gtag、pagefind、paginate 等）保持顶层不动，双语共享
- `enableGitInfo = true` 对英文 `.en.md` 同样生效（git 历史从首次提交起算）

### 4.2 分类/菜单映射表（固定约定）

| 中文分类 | 英文菜单名 | 菜单 URL（Hugo 对 term 名自动 slug 化） |
|---|---|---|
| 技术笔记 | Tech Notes | `/categories/tech-notes/` |
| 行业快讯 | AI News | `/categories/ai-news/` |
| 视频精读 | Video Deep Dives | `/categories/video-deep-dives/` |
| 财富自由 | Wealth & Freedom | `/categories/wealth-freedom/` |
| 思考与随笔 | Essays & Thoughts | `/categories/essays-thoughts/` |

说明：

- 英文文章 frontmatter `categories` 使用右列英文名，Hugo 自动生成英文 term 页
- Hugo multilingual 下 taxonomy 按语言站点隔离，中英 term 页互不干扰
- 本期不为中英 term 页建立 translationKey 关联（收益低；后续可加，见 §10）
- 英文菜单在首篇英文文章发布前指向空列表页，属预期行为

### 4.3 自定义布局语言感知改造

策略：新建项目级 i18n 词条文件，用 Hugo `T` 函数替换硬编码中文，主题词条与项目词条自动合并。

**新建文件：**

- `i18n/zh-cn.toml`（项目级，与 `defaultContentLanguage` 对应）
- `i18n/en.toml`

**词条清单（初版，实施时可增补）：**

| key | zh-cn | en | 使用位置 |
|---|---|---|---|
| `homeFeaturedLabel` | 本周重点 | Featured This Week | index.html |
| `homeMore` | 全部 → | All → | index.html |
| `homeReadMinutes` | 分钟阅读 | min read | index.html |
| `homeTopicLabel` | 专题 | Topics | index.html |
| `homeTopicAiAgent` | AI Agent 学习路径 | AI Agent Learning Path | index.html |
| `homeTopicCodingAgent` | Coding Agent 工作流 | Coding Agent Workflow | index.html |
| `homeTopicTools` | 开源 AI 工具 | Open-Source AI Tools | index.html |
| `catTech` | 技术笔记 | Tech Notes | index.html 板块标题 |
| `catVideo` | 视频精读 | Video Deep Dives | index.html 板块标题 |
| `catNews` | 行业快讯 | AI News | index.html 板块标题 |
| `catThoughts` | 思考与随笔 | Essays & Thoughts | index.html 板块标题 |
| `searchTitle` | 站内搜索 | Site Search | search/single.html |
| 其余（section.html / terms.html / footer.html / meta.html / header.html 中的中文） | 逐个提取 | 逐个翻译 | 对应文件 |

**7 个文件的具体改法：**

1. `layouts/index.html`
   - 4 个板块标题、"本周重点"、"全部 →"、"分钟阅读"、"专题"栏 → `{{ T "key" }}`
   - 分类过滤：`where $visiblePosts "Params.categories" "intersect" (slice "技术笔记")` 改为按语言取分类名：
     ```
     {{- $catTech := cond (eq .Lang "en") "Tech Notes" "技术笔记" -}}
     ```
     （`where .Site.RegularPages` 在多语言下天然只含当前语言页面，无需额外过滤）
   - `GetPage "/categories/技术笔记"` 同理改为语言分支取 term 路径
   - 专题栏（ai-agent / coding-agent / open-source-ai-tools 三页）暂无英文版：整栏包 `{{ if eq .Lang "zh-cn" }} ... {{ end }}`，待英文专题页建立后放开
2. `layouts/search/single.html`：文案走 `T`
3. `layouts/_default/section.html`：文案走 `T`
4. `layouts/taxonomy/terms.html`：文案走 `T`
5. `layouts/partials/single/footer.html`：文案走 `T`
6. `layouts/partials/head/meta.html`：中文硬编码（如 og:locale 相关）按 `.Lang` 分支
7. `layouts/partials/header.html`：文案走 `T`

原则：每个文件改动前先读一遍全文，只替换中文硬编码，不动结构与逻辑；改完后中文站渲染结果必须与改造前逐字节等价（文案值相同）。

### 4.4 hreflang SEO

在站点已覆写的 `layouts/partials/head/link.html` 中追加：

```html
{{- if .IsTranslated -}}
    {{- range .Translations -}}
    <link rel="alternate" hreflang="{{ .Language.Lang }}" href="{{ .Permalink }}">
    {{- end -}}
    <link rel="alternate" hreflang="x-default" href="{{ .Permalink }}">
{{- end -}}
```

配合主题 sitemap 已有的 `xhtml:link` 输出，搜索引擎可正确识别双语对应关系。

### 4.5 英文搜索页

新建 `content/search.en.md`：

```yaml
---
title: "Site Search"
date: 2026-04-02T18:00:00+08:00
type: "search"
url: "/search/"
description: "Full-text site search powered by Pagefind."
---

Enter a title, tag or keyword to search.
```

说明：

- `url: "/search/"` 在英文站点下实际渲染为 `/en/search/`，与中文版 `/search/` 对应
- Pagefind 默认索引 `public/` 全部页面，按页面 `<html lang>` 属性识别语言，中英混合索引开箱即用；`scripts/run_pagefind.sh` 无需改动
- 搜索结果页 UI 文案随 `.Lang` 切换（`layouts/search/single.html` 已按 §4.3 改造）

### 4.6 RSS

Hugo 按语言分别生成 `/index.xml`（中文）与 `/en/index.xml`（英文），主题 head 中 RSS alternate 链接自动指向当前语言的 feed，无需改动。footer 自定义 HTML 中的 RSS 链接保持指向中文 feed（footer 为全局配置；如需按语言区分可在实施时顺带处理，非阻塞项）。

---

## 5. 内容规范（英文文章约定）

### 5.1 命名与位置

- 英文文件 = 中文文件同目录、同名、加 `.en.md` 后缀
- 例：`content/posts/tech/12-factor-agents-llm-principles.md`（中）→ `content/posts/tech/12-factor-agents-llm-principles.en.md`（英）
- Hugo 据此自动建立 `.Translations` 配对，语言切换器、hreflang、sitemap 全部自动生效

### 5.2 Frontmatter 模板

```yaml
---
title: "<英文标题>"
date: "<与中文原文完全一致>"
slug: "<与中文原文完全一致>"        # 保证双语 URL 除 /en/ 前缀外完全对应
github_repo: "<与中文原文一致，如有>"
description: "<英文描述>"
categories: ["Tech Notes"]          # 用 §4.2 映射表英文名
tags: ["AI Agent", "LLM"]           # 中文 tag 译为英文（如"工程实践"→"Engineering Practice"）
---
```

约定细则：

- `date`、`slug` 必须与中文原文一致（URL 对应 + 排序一致）
- 不写 `translationKey`（同名后缀方案下 Hugo 自动配对）
- 不写 `draft: false`（与站点既有 frontmatter 精简决策一致）
- tags 翻译就高不就低：原文已是英文的 tag（"AI Agent"、"LLM"）原样保留

### 5.3 正文翻译要求（coding agent 执行）

- 忠实转译，不增删事实、不改技术结论
- 代码块、命令行、URL、GitHub 链接原样保留
- 中文专有名词处理：产品名/公司名保留原文；成语、梗用意译
- 中文文章内的锚点目录（`[核心判断](#核心判断)`）需同步改为英文锚点
- 图片、附件路径不变（static 资源双语共享）

---

## 6. 翻译工作流（按需逐篇）

1. 用户指定一篇中文文章（如"把 xxx 翻成英文"）
2. coding agent 读取中文原文，按 §5 规范生成同目录 `.en.md`
3. `hugo server` 本地预览：英文文章页、语言切换器双向跳转、英文分类页收录
4. 通过后随常规发布流程提交

后续若需提速，可在此流程之上加批量脚本（见 §10），本期不做。

---

## 7. 实施步骤（执行顺序）

| 步骤 | 内容 | 涉及文件 |
|---|---|---|
| S1 | hugo.toml 多语言配置重构（§4.1 + §4.2 菜单） | `hugo.toml` |
| S2 | 新建项目级 i18n 词条 | `i18n/zh-cn.toml`、`i18n/en.toml` |
| S3 | 7 个自定义布局语言感知改造（§4.3） | `layouts/` 下 7 个文件 |
| S4 | head 追加 hreflang（§4.4） | `layouts/partials/head/link.html` |
| S5 | 英文搜索页（§4.5） | `content/search.en.md` |
| S6 | 双语写作规范文档（§5、§6） | `docs/bilingual-content-guide.md` |
| S7 | 试点翻译 1 篇文章生成 `.en.md`（建议选 tech 分类下一篇中等长度文章） | `content/posts/tech/*.en.md` |
| S8 | 全链路验证（§8）+ 修复验证脚本误报 | 按需 |

依赖关系：S1 → S2/S3/S4/S5 可并行 → S7 依赖 S1-S5 → S8 收尾。S6 独立。

---

## 8. 验证计划（验收清单）

### 8.1 中文站回归（最高优先级）

- [ ] `hugo server` 下中文首页、文章页、分类页、搜索页与改造前视觉、文案、链接一致
- [ ] 中文 URL 无任何变化（抽样 10 篇 + 4 个分类页 + 3 个专题页）

### 8.2 英文站功能

- [ ] `/en/` 首页正常渲染（英文菜单、英文文案；无英文文章时板块为空属预期）
- [ ] 试点英文文章页正常，语言切换器可在中英之间双向跳转
- [ ] 无译文的中文页：切换器指向 `/en/404.html`（主题内置 fallback）
- [ ] 英文分类页 `/en/categories/tech-notes/` 收录试点文章
- [ ] `/en/search/` 可用，能搜到英文文章

### 8.3 SEO 与产物

- [ ] `npm run build` 成功；`public/en/` 存在；构建耗时记录在案（预计约翻倍）
- [ ] 试点文章 HTML head 含成对 hreflang + x-default
- [ ] `sitemap.xml` 含中英互指的 xhtml:link
- [ ] `/index.xml` 与 `/en/index.xml` 分别只含对应语言文章
- [ ] `sh scripts/run_pagefind.sh public` 成功，索引含英文页面

### 8.4 现有验证脚本

- [ ] `npm run validate:frontmatter` 通过
- [ ] `npm run validate:internal-links` 通过（如脚本对 `/en/` 链接有误报则修复脚本）
- [ ] `npm run validate:future-dates`、`validate:topic-pages`、`validate:release-assets` 通过

---

## 9. 风险与回滚

| 风险 | 影响 | 对策 |
|---|---|---|
| 布局改造引入中文站回归 | 中文站文案/链接错乱 | §8.1 回归清单逐项验收；改造坚持"只换文案不动结构" |
| 构建时间翻倍（1726 篇 × 2 语言） | CI/部署变慢 | 属预期；Hugo 构建本身极快，先实测再评估是否需要增量构建优化 |
| 验证脚本对多语言产物误报 | 发布流程受阻 | S8 中修复脚本，不动校验原则 |
| Hugo 语言 key `zh-cn` 与主题 i18n 文件名 `zh-CN.toml` 大小写差异 | 主题中文词条加载失败 | Hugo i18n 查找大小写不敏感；S8 中实测确认，若有问题将语言 key 改为 `zh-CN` 并同步调整 `defaultContentLanguage` |
| 英文 term 页在无文章时为空 | 英文菜单点进空页 | 预期行为；首篇英文文章发布后自然填充 |
| 回滚 | — | 全部改动集中在 hugo.toml、i18n/、layouts/、content/search.en.md 与试点 .en.md；`git revert` 单个提交即可完整回滚 |

## 10. 后续可扩展方向（本期不做）

- **批量翻译脚本**：`scripts/translate_article.py` 调 LLM API 批量处理存量文章（带术语表、断点续传），框架就绪后随时可加
- **term 页关联**：为中英分类页加 `translationKey`，使分类页也进入语言切换器
- **英文专题页**：翻译 ai-agent / coding-agent / open-source-ai-tools 三个专题页后放开首页专题栏的英文分支
- **第三语言**：后缀方案天然支持（如 `.ja.md`），只需在 `[languages]` 加一段配置
- **hreflang 自动化测试**：在 validate_site.py 中增加 hreflang 配对断言
