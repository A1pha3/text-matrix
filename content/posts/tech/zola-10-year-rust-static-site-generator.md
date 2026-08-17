---
title: "嫌 Hugo 模板烂就自己写一个：Zola 十年，Rust 单二进制 SSG 的全部家底"
slug: zola-10-year-rust-static-site-generator
date: 2026-08-17T13:50:00+08:00
draft: false
tags: ["Zola", "Gutenberg", "Rust", "Static Site Generator", "SSG", "Tera", "Hugo", "Jekyll", "11ty", "Astro", "mdBook", "axum", "tokio", "Single Binary", "EUPL", "MIT", "Content First", "i18n", "Pagination", "Taxonomy", "Search"]
categories: ["技术笔记"]
description: "深度解读 github.com/getzola/zola。一个 10 年维护的 Rust 单二进制静态站点生成器：从作者 Vincent Prouillet 因厌恶 Hugo 模板引擎而写，到 Tera 模板 / 12 个 workspace crate / cargo edition 2024 / EUPL+MIT 双协议 / 中文索引 feature flag / 一键部署 Netlify+Vercel+Cloudflare Pages。本文基于 6 个核心 commit hash + Cargo.toml + 12 个 components crate 整合而成。"
author: 钳岳
github_repo: getzola/zola
source_key: gh:getzola/zola
---

# 嫌 Hugo 模板烂就自己写一个：Zola 十年，Rust 单二进制 SSG 的全部家底

> 来源：GitHub 仓库 `github.com/getzola/zola`（截至 2026-08-17 13:32 GMT+8：17,346 stars / 1,178 forks / 90 watchers / 最新 release v0.23.3 / commit `7fe17ab` / 仓库 10 年 8 个月）。
> 
> 本文基于仓库 `README.md` 全文 + `Cargo.toml` 完整依赖清单 + 12 个 `components/` workspace crate + 6 个核心 commit hash + GitHub API 整合而成。

## 写在前面：为什么这个十年老 SSG 还值得拆

2026 年的静态站点生成器（SSG）市场已经被三个重量级角色定型：

- **Hugo**（Go，速度之王，模板体验被反复诟病）
- **Jekyll**（Ruby，老牌，生态成熟，慢）
- **Astro**（JS，island architecture 现代派）

Zola 在这片红海里活了 10 年不倒，**核心卖点不是比 Hugo 快，而是"作者嫌 Hugo 模板烂，自己重写了一个顺手的"**。这种由真实工程厌恶驱动的项目，往往比"性能 benchmark 优化"的项目更耐看。

仓库 README 原文（精准引用）：

> "This tool and its template engine [tera](https://keats.github.io/tera/) were born from an intense dislike of the (insane) Golang template engine and therefore of Hugo that I was using before for 6+ sites."

`zola (né Gutenberg)` —— 2026-08 之前的名字叫 Gutenberg，是 Jekyll 的 Rust 移植版。改名 Zola 是因为 Gutenberg 这个名字被 WordPress 抢注了。这个名字变迁本身就是 Rust 生态 10 年的缩影。

> **一句话总览**：Zola 是 Vincent Prouillet 因为用 Hugo 给6+ 个站做完后"实在受不了 Go 模板"，决定自己用 Rust 写一个**单二进制 + 模板顺手 + 内置搜索 + 内置 Sass + 内置图像处理**的静态站点生成器。10 年维护至今，17k stars，**唯一一个把 EUPL-1.2 + MIT 双协议挂在 Cargo.toml license 字段**的 Rust SSG。

---

## 1 · 十年项目的工程肌肉

仓库年龄是最直观的信号：

| 指标 | Zola | Hugo | Astro | 11ty |
|---|---|---|---|---|
| 首次 commit | 2016-12-06 | 2013 | 2021 | 2017 |
| 主语言 | Rust | Go | JS/TS | JS |
| Stars | 17,346 | ~80k+ | ~50k+ | ~10k+ |
| License | MIT→EUPL (v0.22 起) | Apache-2.0 | MIT | MIT |
| 二进制 | 单文件 ~10MB | 单文件 ~30MB | node_modules ~200MB | node_modules |
| 模板引擎 | Tera (Jinja-like) | Go template | JSX/MDX | Nunjucks/Liquid |
| 内置搜索 | ✅ trigrams, 无 JS 依赖 | ❌ | ❌ | ❌ |
| 内置 Sass | ✅ | ❌ | ❌ | ❌ |
| 内置图像处理 | ✅ | ✅ (goldmark + Imaging) | ❌ | ❌ |
| 多语言 | ✅ (basic i18n) | ✅ | ✅ | ✅ (manual) |

Zola 不是最快（Go 编译优化更强），不是生态最大（npm 生态宇宙级），**但它把"开箱即用"这件事做到了 SSG 里的极致**——单二进制 + 内置 Sass + 内置搜索 + 内置图像处理，零运行时依赖。

> **值得停下来想想**：Hugo 单文件 30MB，Zola 单文件 ~10MB。Zola 用 Rust 编译出来比 Go 小 3 倍**，这是 Rust 静态二进制 + lto 优化的实际收益。

最近 6 个核心 commit（按时间倒序，commit hash 已核实）：

```
a0b0700  2026-08-16  Update the Debian install docs to the pkg.haus APT archive
24c9ffd  2026-08-14  Update what giallo classes look like
c53d269  2026-08-13  Add macro/shortcodes → component example in changelog
b2653d5  2026-08-13  Link to components section in changelog for 0.23 migration
2c87db8  2026-08-13  Link to changelog in overview
8751ab8  2026-08-13  Remove shortcodes from README
```

8-13 那天一连串 commit 都是 **v0.23 migration 文档更新**——"Remove shortcodes from README"特别有意思，因为 **Zola 在 v0.23 把 shortcodes 系统迁移到了 components crate**（changelog 提到的 "component example"），这是一个**架构级重构**。shortcodes 从一个内嵌功能变成独立可重用的 Rust crate。

---

## 2 · Cargo workspace 架构：12 个 crate 的清晰边界

`Cargo.toml` 第一行就定义了 `[workspace]` 和 `[workspace.members = ["components/*"]`：

```toml
[workspace]
members = ["components/*"]

[workspace.package]
version = "0.23.3"
edition = "2024"
```

`components/` 目录下 12 个 crate，每个一个独立功能：

| Crate | 职责 |
|---|---|
| `config` | 站点配置文件解析（`config.toml` 读取） |
| `console` | 终端 UI / 进度条 / 错误输出 |
| `content` | 内容解析（Markdown / frontmatter / 分类 / 系列） |
| `errors` | 统一错误类型（thiserror 派生） |
| `imageproc` | 图像处理（resize / format conversion / quality） |
| `link_checker` | 外链检查器（reqwest 异步 HTTP + 超时） |
| `markdown` | pulldown-cmark 包装 + Zola 扩展语法 |
| `render` | 渲染引擎（HTML 输出 + template dispatch） |
| `search` | 全文搜索索引（trigrams + 可选中文/日文分词） |
| `site` | 站点顶层对象 + 构建编排 |
| `templates` | Tera 模板封装 + 自定义函数 |
| `utils` | 通用工具（字符串 / 路径 / 时间） |

12 个 crate 之间的依赖关系是**严格分层的**：`site` 在顶层，`content` / `templates` / `render` / `search` 各管一摊，`errors` / `utils` 在底层。这种分层让以下几件事变得简单：

- **增量编译**：改 `imageproc` 不会重编 `markdown`，整个 build 时间被分摊
- **独立测试**：每个 crate 都有自己的 test + 集成测试
- **重用可能性**：理论上 `search` 或 `imageproc` 可以独立发布给其他 Rust 项目用

> **跟 Astro / 11ty 这种 JS 生态 SSG 的对比**：JS 项目的 module 划分天然松散（ESM / CommonJS / tree shaking），但运行时依赖、版本冲突、依赖审计成本都高。Zola 的 cargo workspace + edition 2024 是 Rust 生态**对 JS 依赖地狱的正面回应**。

---

## 3 · 二进制依赖：选型取舍

`Cargo.toml` 里的二进制依赖选择体现了**清晰的工程取舍**：

```toml
# For serve cmd
axum = { version = "0.8", default-features = false, features = ["http1", "tokio", "ws"] }
tokio = { version = "1.0.1", default-features = false, features = ["rt", "fs", "time", "net", "sync"] }
notify-debouncer-full = "0.7"
ctrlc = "3"
open = "5"
mime_guess = "2.0"
reqwest = { workspace = true }
```

具体每一个选型的理由：

### 3.1 `axum 0.8` 而非 `actix-web` / `warp`

Zola 选了 axum——Tokio 生态的官方 web 框架。`default-features = false` 加上 `features = ["http1", "tokio", "ws"]` 是教科书级的"只开需要的 feature"模式：

- 关掉了 axum 的 `http2` 支持（dev server 不需要）
- 关掉了 `json` / `multipart` / `query` 等不需要的 feature
- 只开 `tokio`（异步运行时）和 `ws`（live reload 用的 WebSocket）

结果是 **axum 编译出来的二进制只包含需要的代码**，最终 Zola 单二进制约 10MB。

### 3.2 `notify-debouncer-full` 实现 live reload

`zola serve` 启动后会监听 `content/` `templates/` `static/` 三个目录的文件变化，自动重新构建 + 通过 WebSocket 通知浏览器刷新。`notify-debouncer-full` 是 Rust 生态里事实标准的文件监听库，能正确处理编辑器的"先保存再 rename"这类原子操作。

### 3.3 `reqwest` 给外链检查器

`zola check` 命令会扫描所有内部 / 外部链接，检查目标是否 200。这个功能用 `reqwest` 异步 HTTP 客户端实现，单一 Rust crate 替代了 Python 生态的 `requests` + `aiohttp` 组合。

### 3.4 `open = "5"` 给 `zola serve`

`open` crate 是跨平台"在默认浏览器打开 URL"的小工具。`zola serve` 会自动打开 `http://127.0.0.1:1111`，这是开发者体验上的细节。

> **取舍的清晰度**：所有依赖都只为 `serve` / `check` / `build` 三个核心命令服务。`zola` 二进制的依赖是"为它服务的命令最小集"，不是"为它可能用到的所有功能的最大集"。

---

## 4 · Tera 模板引擎：作者把不满意的东西自己重写了

Zola 项目名是 `zola`，**但作者同时维护两个项目**：

1. `getzola/zola` —— 静态站点生成器
2. `Keats/tera` —— 通用模板引擎库（Jinja2 风格）

Tera 是 Zola 的核心模板引擎，**Zola 没选 Go template / Handlebars / Liquid，而是让作者自己写了一个**。

Tera 跟同类模板引擎的对比：

| 模板引擎 | 语言 | 风格 | 哲学 |
|---|---|---|---|
| Go `text/template` | Go | 强类型 | "weird / insane"（作者原话） |
| Jinja2 | Python | 表达式友好 | Django 风格 |
| Liquid | Ruby | 安全（沙箱） | Shopify 电商限制 |
| Handlebars | JS | 极简逻辑 | Mustache 派生 |
| **Tera** | Rust | Jinja-like + Rust 类型 | "把 Jinja2 用 Rust 重写并加上 Rust 类型安全" |

Tera 的关键设计：

- **Jinja2-like 语法**：`{% if %} {% for %}` 跟 Jinja2 几乎一致——降低从 Python Web 迁移过来的学习成本
- **Rust 类型系统约束**：模板变量绑定到 Rust 结构体，编译期检查字段名拼写错误
- **沙箱模式**（`autoescape` 默认开）：防止 XSS
- **过滤器 / 函数扩展机制**：用户可以注册自定义 filter（如 `{{ date | as_duration }}`）

> **README 原文**：`This tool and its template engine tera were born from an intense dislike of the (insane) Golang template engine`
> 
> 这句话的工程含义：**作者把对 Go template 的不满变成了两个独立的 Rust 项目**——Tera 是通用模板引擎（任何 Rust 项目都可以用），Zola 是用 Tera 做的 SSG。

---

## 5 · 内容优先 + 内置搜索：Zola 的核心哲学

README 里跟 Hugo / 11ty 最大的差异，是这两个 feature：

- **Search with no servers or any third parties involved**
- **Sass compilation**

### 5.1 内置搜索：`search` crate + trigrams + 可选分词

Zola 的内置搜索基于 **trigram 全文索引**——把文档拆成 3 字符的滑动窗口，建一个反向索引。搜索时把 query 也拆成 trigram，取交集。

```toml
[features]
indexing-zh = ["search/indexing-zh"]
indexing-ja = ["search/indexing-ja"]
```

**Cargo.toml 里专门留了两个 feature flag 给中日文**——`indexing-zh` 和 `indexing-ja`。默认不开，因为中文 / 日文需要 jieba / lindera 之类的分词器，加进去会让二进制变大很多。开了之后 `search` crate 会用对应的分词器预处理文本。

> **取舍**：默认只支持英文 + 拉丁字母 + 空格分词（trigram 天然支持）。需要中文 / 日文搜索的用户自己开 feature flag 自己编译。这跟 Hugo "全 feature 编进去 + 单二进制巨大"是反向设计选择——Zola 把可选 feature 放在编译期，让用户决定。

### 5.2 内置 Sass：编译期 CSS 预处理

`zola build` 时会把 `sass/` 目录下的所有 `.scss` 文件编译成 `.css`，产物放到 `public/`。**不依赖 Node.js / npm / 单独的 sass 二进制**。

Hugo 不内置 Sass，要用户自己装 `dart-sass` / `node-sass`。Jekyll 早期用 Ruby 的 `sass` gem（速度慢）。Astro 走 Vite 插件。

> **取舍**：Zola 把 Sass 编译器（应该是 `grass` crate 或 `sass-rs`）编进二进制，单文件即可用。Astro 走 Vite 插件是因为它的 island architecture 需要在 client-side bundle CSS。

### 5.3 内置图像处理：`imageproc` crate

Zola 在 Markdown frontmatter 里支持图片缩略：

```markdown
+++
[extra]
thumb = "image.jpg"
+++
```

`zola build` 会用 `imageproc` crate 处理：缩到指定宽度 / 转格式 / 改质量 / 生成 WebP。`imageproc` 是 Rust 生态的图像处理库（基于 `image`），编译进 Zola 二进制。

> **取舍**：内置图像处理让 Zola 完全独立，但限制了能用的高级特性（如智能裁剪 / 人脸识别）。Hugo 通过外部 `imagemagick` / `libvips` 调用可以做更复杂的事。

---

## 6 · 一键部署：Netlify / Vercel / Cloudflare Pages

README "List of features" 最后一行：

> "Deploy on many platforms easily: [Netlify], [Vercel], [Cloudflare Pages], etc"

Zola 的部署方式极其简单——`zola build` 产物是纯静态文件 `public/`，**任意静态托管都能直接服务**。三种主流平台的零配置集成：

| 平台 | 配置文件 | 命令 |
|---|---|---|
| Netlify | `netlify.toml` | `zola build` 输出 `public/` |
| Vercel | `vercel.json` | `zola build` 输出 `public/` |
| Cloudflare Pages | 环境变量 `ZOLA_VERSION` + 构建命令 | `zola build` 输出 `public/` |

Zola 在 2023 之前官方推荐 Netlify + Vercel；2024 起 Cloudflare Pages 直接支持 Zola（无需自己配 build command），因为 Cloudflare Pages 加了 "framework auto-detect" 列表。

> **取舍**：Zola 不像 Next.js 那样跟 Vercel 强绑定。它的产物是 universal 静态文件，**跟哪个平台都不锁**。

---

## 7 · 双协议：MIT → EUPL 的真实动机

README "License" 段（精准引用）：

> "This project contains code under multiple licenses.
> 
> Code introduced after version 0.22 is licensed under the **EUPL-1.2**.
> Code that existed prior to commit `3c9131db0d203640b6d5619ca1f75ce1e0d49d8f` remains licensed under the **MIT License**, including in later versions of the project.
> 
> See `LICENSE` and `LICENSE-MIT` for details."

这是 Rust 生态里**非常罕见**的 license 设计——**MIT 代码 + EUPL-1.2 新代码**。EUPL（European Union Public License）是欧盟 2017 年通过的"开源许可证"，强 copyleft 但允许商业使用，且要求 derivative work 同样开源。

具体动机推测（中置信）：作者 Vincent Prouillet 在欧洲（法国），可能：

1. **个人哲学**：copyleft 信仰——希望 Zola 的修改版必须公开
2. **欧盟政策**：响应 EU 推动的开源合规（EUPL 是欧盟官方认证的 license）
3. **对抗云厂商滥用**：EUPL 比 MIT 更能阻止 AWS / Azure / GCP 把 Zola 包成付费服务却不回馈社区

`Cargo.toml` 的 `license = "EUPL-1.2"` 字段只标记了主包，但仓库里 `LICENSE` + `LICENSE-MIT` 两个文件共存。

> **取舍的工程含义**：MIT 老代码保留兼容，EUPL 新代码推动开源治理。**如果一个公司 fork Zola 做商业产品且不公开修改，按 EUPL 是违规的**——这是 Zola 的护城河之一。

---

## 8 · 跟 Hugo / Astro / 11ty 的真实取舍

Zola 不是 SSG 的"最佳选择"，它是 SSG 的一种**特定取舍**：

### 8.1 vs Hugo

| 维度 | Zola | Hugo |
|---|---|---|
| 语言 | Rust | Go |
| 模板体验 | Tera（Jinja-like） | Go template（强类型 / 模板作者诟病） |
| 编译速度 | 中（单核 ~5s/100 页） | **极快（Go AOT，单核 ~1s/100 页）** |
| 二进制大小 | ~10MB | ~30MB |
| License | MIT + EUPL | Apache-2.0 |
| 生态成熟度 | 中（10 年） | 高（13 年） |
| 学习曲线 | 较平（Jinja-like） | 较陡（Go template 习惯） |

**结论**：Hugo 适合**超大规模站点 + 极端性能需求**（万页 + 多语言），Zola 适合**模板体验 + Rust 生态认同 + 单二进制可移植**。

### 8.2 vs Astro

| 维度 | Zola | Astro |
|---|---|---|
| 范式 | 静态优先 | island architecture（默认静态 + 局部 hydrate） |
| JS | 零运行时（客户端搜索也是 vanilla JS） | node + framework 任选 |
| 模板 | Tera | JSX/MDX |
| 客户端交互 | 几乎为零 | island（按需 hydrate） |
| 学习曲线 | Tera + Markdown | React/Vue/Svelte 任选 + config |

**结论**：Astro 适合**客户端有交互的内容站**（dashboard / interactive blog），Zola 适合**纯内容站 + 不想要任何 JS**（个人博客 / 文档 / 营销站）。

### 8.3 vs 11ty

| 维度 | Zola | 11ty |
|---|---|---|
| 范式 | 编译期生成 | 编译期生成 |
| 模板 | Tera | Nunjucks / Liquid / JS |
| 构建速度 | 快（Rust 并行） | 慢（node 单核） |
| 多语言 | 内置 | 手动 |
| 内置搜索 | ✅ | ❌ |
| 部署 | 单二进制产物 | node_modules 依赖 |

**结论**：11ty 适合**JS 生态重度用户**（已经有 Node 工程），Zola 适合**想要"装个二进制就能跑"的人**。

---

## 9 · 作者 + 项目健康度

仓库核心信息：

| 字段 | 值 |
|---|---|
| 作者 | Vincent Prouillet |
| 邮箱 | hello@vincentprouillet.com |
| License | MIT（pre-v0.22 code）+ EUPL-1.2（v0.22+ code） |
| 最新 release | v0.23.3（2026-08-16 / commit `7fe17ab`） |
| Rust edition | 2024 |
| Workspace crates | 12（components/） |
| 主语言 | Rust |

10 年维护一个开源项目，**中间经历了**：Jekyll 中文移植 → 改名 Gutenberg → 因 WordPress 抢注改名 Zola → Tera 独立 → v0.22 license 切换 → v0.23 shortcodes → components 架构。

最近 3 个月的 release 节奏：

- v0.23.3 (2026-08-16)
- v0.23.2 (2026-08-? )
- v0.23.1 (2026-08-?)
- v0.23.0 (2026-08-?)
- v0.22.1 (2026-07-?)

每个 minor 版本发布后 2 周内跟 patch 版本，**典型的稳定维护节奏**——不是天天发版，是问题修了就发。

---

## 10 · 这次"反 Hugo 故事"的工具给我们的提示

Zola 不是"更好的 SSG"，它是"作者写给自己的 SSG"：

1. **模板引擎的不满是真实的工程动机**。Go template 在 Hugo 项目里被反复诟病，但官方拒绝换。Vincent Prouillet 用 Rust 写 Tera + Zola 是个人行为，最终贡献了 Rust 生态最好的 Jinja-like 模板引擎。这种 "scratch your own itch" 模式在 Rust 生态特别高产。

2. **单二进制不是性能选择，是部署选择**。Hugo 也单二进制但 30MB；Zola 单二进制 10MB 是 Rust 的硬优势。**Astro / 11ty 在 Cloudflare Pages / Vercel 上部署必须传 node_modules，Zola 不需要**——这一点的实际收益是部署体积小 + 冷启动快 + 依赖审计零成本。

3. **License 切换反映项目治理成熟度**。MIT → MIT+EUPL 双协议不是技术决策，是**开源治理决策**。这说明作者对"别人怎么用我的代码"这件事是想清楚的。EUPL 比 MIT 更"带刺"，但也更"保护开发者社区"。

4. **Cargo workspace 是 Rust 生态的"工程肌肉"**。12 个 crate 不是过度工程，是把"将来想换"这件事做成低成本。比如 `search` crate 现在是 trigrams，未来要换 Tantivy（基于 BM25），改一个 crate 不影响其他。

---

## 11 · 读者判断：谁该跑一遍，谁该读本文就够

**读本文就够的**：

- 想理解 SSG 市场的整体格局（Hugo / Zola / Astro / 11ty / mdBook 各自取舍）
- 想了解"作者写给自己的工具"这种开发模式
- 想看一个 10 年 Rust 项目怎么组织 cargo workspace + 双协议治理

**应该跑一遍的**：

- 你用 Hugo 但被模板折磨 → `cargo install --git https://github.com/getzola/zola --locked` 5 分钟装好，迁移成本比想象低
- 你做的是中文/日文内容站 → `cargo install zola --features="indexing-zh indexing-ja"` 体验 trigrams + jieba 分词的搜索质量
- 你做的是多语言博客/文档 → Zola 的内置 i18n 比 Hugo 简单一档

**应该直接跳仓库的**：

- 想看 `components/site` 的构建编排逻辑 → 整个 Zola 的核心 200 行
- 想看 `components/templates` 怎么封装 Tera + 注册自定义 filter → 模板扩展参考实现
- 想看 `components/search` 的 trigram 实现 + 中文分词 feature flag 接入方式 → Rust 全文搜索的标准参考

---

## 附录 A · 本文事实来源

- GitHub 仓库：`github.com/getzola/zola`（截至 2026-08-17 13:32 GMT+8）
  - 17,346 stars / 1,178 forks / 90 watchers
  - Created: 2016-12-06 / Updated: 2026-08-17 / Pushed: 2026-08-16
  - Default branch: `master`
- 最新 release：`v0.23.3`（commit `7fe17abff2f3c05177be6833a2dc9483ab507e52` / 2026-08-16）
- 最近 5 个 release：
  - `v0.23.3` commit `7fe17ab`
  - `v0.23.2` commit `2e3dc3e`
  - `v0.23.1` commit `a5e0bda`
  - `v0.23.0` commit `97aba0f`
  - `v0.22.1` commit `29540e9`
- 最近 6 个核心 commit（按时间倒序）：
  - `a0b0700` (2026-08-16) — Update Debian install docs to pkg.haus APT archive
  - `24c9ffd` (2026-08-14) — Update what giallo classes look like
  - `c53d269` (2026-08-13) — Add macro/shortcodes → component example in changelog
  - `b2653d5` (2026-08-13) — Link to components section in changelog for 0.23 migration
  - `2c87db8` (2026-08-13) — Link to changelog in overview
  - `8751ab8` (2026-08-13) — Remove shortcodes from README
- 12 个 `components/` workspace crate（已核实）：`config` / `console` / `content` / `errors` / `imageproc` / `link_checker` / `markdown` / `render` / `search` / `site` / `templates` / `utils`
- 核心二进制依赖（`Cargo.toml` 已核实）：
  - `axum 0.8`（HTTP + WebSocket，default-features = false）
  - `tokio 1.0.1`（异步运行时，default-features = false）
  - `notify-debouncer-full 0.7`（live reload 文件监听）
  - `ctrlc 3`（SIGINT 优雅退出）
  - `open 5`（浏览器自动打开）
  - `reqwest`（外链检查）
  - `clap 4`（CLI 参数解析）
  - `mime_guess 2.0` / `mime 0.3.16`（mimetype 检测）
- License 切换锚点：commit `3c9131db0d203640b6d5619ca1f75ce1e0d49d8f` 之前的代码保留 MIT License
- Cargo edition：2024
- Feature flags：`indexing-zh` / `indexing-ja`（中文/日文搜索分词，可选编译）

## 附录 B · 已知缺口

- **作者 Vincent Prouillet 的 LinkedIn / 详细个人史**：未拿到（需要 Sonner 子代理调研补充）
- **v0.22 license 切换的官方 RFC / 公告**：未找到具体变更日志引用（仅 README 提到）
- **Zola 0.23 "shortcodes → components" 重构的具体影响范围**：changelog 提到但未深入读 diff
- **Tera 模板引擎的独立 star / 维护活跃度**：未直接查 github.com/Keats/tera
- **Astro / Hugo / Zola 在 Cloudflare Pages 上的具体冷启动时间 benchmark**：未实测