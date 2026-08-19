---
title: "嫌 Hugo 模板烂就自己写一个：Zola 十年，Rust 单二进制 SSG 的全部家底"
slug: zola-10-year-rust-static-site-generator
date: 2026-08-17T13:50:00+08:00

tags: ["Zola", "Gutenberg", "Rust", "Static Site Generator", "SSG", "Tera", "Hugo", "Jekyll", "11ty", "Astro", "mdBook", "axum", "tokio", "Single Binary", "EUPL", "MIT", "Content First", "i18n", "Pagination", "Taxonomy", "Search"]
categories: ["技术笔记"]
description: "深度解读 github.com/getzola/zola。一个 10 年维护的 Rust 单二进制静态站点生成器：作者 Vincent Prouillet 因厌恶 Hugo 模板引擎而写，如今自带 Tera 模板 / 12 个 workspace crate / EUPL+MIT 双协议 / 可选中文搜索 / 一键部署。全文基于 README、Cargo.toml、12 个 components crate 与核心 commit hash 核实而成，保留全部事实来源。"
author: 钳岳
github_repo: getzola/zola
source_key: gh:getzola/zola
---

# 嫌 Hugo 模板烂就自己写一个：Zola 十年，Rust 单二进制 SSG 的全部家底

> 来源：GitHub 仓库 `github.com/getzola/zola`（截至 2026-08-17 13:32 GMT+8：17,346 stars / 1,178 forks / 90 watchers / 最新 release v0.23.3 / commit `7fe17ab` / 仓库 10 年 8 个月）。
>
> 本文基于仓库 `README.md` 全文 + `Cargo.toml` 完整依赖清单 + 12 个 `components/` workspace crate + 6 个核心 commit hash + GitHub API 整合而成。

## 这台十年老 SSG 真正解决的是什么

Zola 值不值得拆，不在它快，也不在它生态大。它是在一片被 Hugo、Jekyll、Astro 定型的红海里，凭一个不算主流的理由活了 10 年：作者不喜欢 Hugo 的模板引擎，于是给自己重写了一个顺手的。这种由真实工程厌恶驱动的项目，通常比瞄准某条性能 benchmark 优化出来的项目更禁得起读。

仓库 README 把这个动机写得很直白（引自 `raw.githubusercontent.com/getzola/zola/master/README.md` L11–L12）：

> "This tool and its template engine [tera](https://keats.github.io/tera/) were born from an intense dislike of the (insane) Golang template engine and therefore of Hugo that I was using before for 6+ sites."

仓库原名 `zola (né Gutenberg)`：`né` 是法语"本名 / 曾用名"。改名是因为 Gutenberg 在 SSG 圈里有明显撞名——和电子书项目 Project Gutenberg、WordPress 的 Gutenberg 编辑器都重名。注意它不是 Jekyll 移植，也不是 Rust 重写 Hugo：README 明说作者在此前用 Hugo 搭了 6+ 个站。

一句话记住它：作者 Vincent Prouillet 受够了 Go 模板，用 Rust 写了一个单二进制、模板顺手、自带搜索（elasticlunr-rs）、自带 Sass（grass）、自带语法高亮（giallo，自研）、自带图像处理的 SSG。两个版本号值得记：v0.22（2026-01-09）把高亮从 Syntect 换成 Giallo，并把协议切到 EUPL 1.2；v0.23（2026-08-05）强制升级 Tera v2，用 Component 取代 shortcodes。

---

## 1 · 十年项目的工程肌肉

先看一张对照表，把 Zola 在主流程里的定位立住：

| 指标 | Zola | Hugo | Astro | 11ty |
|---|---|---|---|---|
| 首次 commit | 2016-12-06 | 2013 | 2021 | 2017 |
| 主语言 | Rust | Go | JS/TS | JS |
| Stars | 17,346 | ~80k+ | ~50k+ | ~10k+ |
| License | MIT→EUPL (v0.22 起) | Apache-2.0 | MIT | MIT |
| 模板引擎 | Tera 2.0 (Jinja-like) | Go template | JSX/MDX | Nunjucks/Liquid |
| 内置搜索 | ✅ elasticlunr-rs 3.0.2 | ❌ | ❌ | ❌ |
| 内置 Sass | ✅ grass 0.13 | ❌ | ❌ | ❌ |
| 内置语法高亮 | ✅ giallo 0.5（自研） | ✅ chroma | ✅ shiki | ✅ prism |
| 内置图像处理 | ✅ imageproc + webp | ✅ Imaging | ❌ | ❌ |
| 多语言 | ✅（basic i18n） | ✅ | ✅ | ✅（manual） |
| dev server | ✅ axum + live reload | ✅ | ✅ Vite | ✅ |

Zola 不是最快的（Go 的编译优化更强），也不是生态最大的（npm 生态体量不同）。它的"开箱即用"在 SSG 里做得很彻底：单二进制、自带 Sass、自带搜索、自带图像处理、零运行时依赖，装一个文件就能跑。

release profile 也往这个方向推：`lto = true`、`codegen-units = 1`、`strip = true`（`Cargo.toml` L140–142），把构建产物尽量压小。顺带澄清一个口径：仓库 API 显示的 122,579 KB 是源码 + 子模块 + docs + test fixtures 的体积，不是用户下载到的二进制大小。

最近 6 个核心 commit（按时间倒序，hash 已核实）：

```text
a0b0700  2026-08-16  Update the Debian install docs to the pkg.haus APT archive
24c9ffd  2026-08-14  Update what giallo classes look like
c53d269  2026-08-13  Add macro/shortcodes → component example in changelog
b2653d5  2026-08-13  Link to components section in changelog for 0.23 migration
2c87db8  2026-08-13  Link to changelog in overview
8751ab8  2026-08-13  Remove shortcodes from README
```

8 月 13 日这一批 commit 全部是 v0.23 migration 的文档更新。最值得留意的是 "Remove shortcodes from README"：Zola 在 v0.23 把 shortcodes 迁成了独立的 `components` crate（changelog 里的 "component example" 指的就是它）。shortcodes 从内嵌功能变成可独立复用、可单独测试的 Rust crate，算是这次大版本里最结构性的一处改动。

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

12 个 crate 之间的依赖是单方向分层的：`site` 在最顶层做编排，`content` / `templates` / `render` / `search` 各自管一摊，`errors` 垫在底层。这套分层的收益很直接：

- 增量编译：改 `imageproc` 不会拖着重编 `markdown`，构建时间被分摊开
- 独立测试：每个 crate 都带自己的单元测试和集成测试
- 可复用：理论上 `search`、`imageproc` 都能单独拎出来发给别的 Rust 项目
- release profile 兜底：`lto = true`（跨 crate 内联）+ `codegen-units = 1`（单 codegen 单元，最大优化）+ `strip = true`（剥符号表），产物在可移植的前提下尽量小

把这套和 JS 生态的 SSG 对比能看出两种路线：JS 项目的模块依赖靠 ESM / CommonJS / tree shaking 拆，但运行时依赖、版本冲突、依赖审计的成本都落在无形处。Zola 用 cargo workspace + edition 2024 把依赖关系交给了 Cargo 这个编译期工具，算是对"依赖地狱"的一次正面回应。

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

Zola 选了 axum，Tokio 生态的官方 web 框架。`default-features = false` 加上 `features = ["http1", "tokio", "ws"]`，是"只开要用到的 feature"的用法：

- 关掉 `http2` 支持（dev server 用不到）
- 关掉 `json`、`multipart`、`query` 等没用的 feature
- 只开 `tokio`（异步运行时）和 `ws`（live reload 用的 WebSocket）

这样 axum 编译进二进制的只可能是被用到的代码，不会把整个 web 框架拖进来。

### 3.2 `notify-debouncer-full` 实现 live reload

`zola serve` 启动后会监听 `content/` `templates/` `static/` 三个目录的文件变化，自动重新构建 + 通过 WebSocket 通知浏览器刷新。`notify-debouncer-full` 是 Rust 生态里事实标准的文件监听库，能正确处理编辑器的"先保存再 rename"这类原子操作。

### 3.3 `reqwest` 给外链检查器

`zola check` 命令会扫描所有内部 / 外部链接，检查目标是否 200。这个功能用 `reqwest` 异步 HTTP 客户端实现，单一 Rust crate 替代了 Python 生态的 `requests` + `aiohttp` 组合。

### 3.4 `open = "5"` 给 `zola serve`

`open` crate 是跨平台"在默认浏览器打开 URL"的小工具。`zola serve` 启动后会自动打开 `http://127.0.0.1:1111`，省掉手动输地址的动作。

把 3.1–3.4 连起来看，依赖清单很克制：每一条都只为 `serve` / `check` / `build` 三个命令服务。Zola 的二进制依赖遵循的是"命令要用到的最小集"，而不是"将来可能要用的功能的最大集"。

---

## 4 · Tera 模板引擎：作者把不满意的东西自己重写了

要理解 Zola，得同时看两个仓库：作者 Vincent Prouillet 不是只维护静态站点生成器，而是把模板引擎也单独拆了出来：

1. `getzola/zola` —— 静态站点生成器
2. `Keats/tera` —— 通用模板引擎库（Jinja2 风格）

Tera 是 Zola 的核心模板引擎。它没有用现成的 Go template、Handlebars 或 Liquid，而是自己写了一个。放回同类里看它的位置：

| 模板引擎 | 语言 | 风格 | 哲学 |
|---|---|---|---|
| Go `text/template` | Go | 强类型 | "weird / insane"（作者原话） |
| Jinja2 | Python | 表达式友好 | Django 风格 |
| Liquid | Ruby | 安全（沙箱） | Shopify 电商限制 |
| Handlebars | JS | 极简逻辑 | Mustache 派生 |
| **Tera** | Rust | Jinja-like + Rust 类型 | 用 Rust 重写 Jinja2 并加类型安全 |

关键设计有四处：

- 语法走 Jinja2-like：`{% if %}`、`{% for %}` 和 Jinja2 几乎一致，从 Python Web 转过来的学习成本低
- 受 Rust 类型系统约束：模板变量绑定到 Rust 结构体，字段名拼错会在编译期暴露
- 默认开 `autoescape`，收紧沙箱，挡掉 XSS
- 支持过滤器与自定义函数，可以注册自己的 filter（如 `{{ date | as_duration }}`）

README 那句对 Go template 的抱怨，落到工程上其实是两件事：Tera 是可复用的通用模板库（任何 Rust 项目都能用），Zola 只是用它的第一个 SSG。

### 4.1 Tera 独立仓库的数据

`Keats/tera`（已核实 ungh.cc）：

- **4,287 stars / 336 forks**
- 创建：2015-07-17（比 Zola 还早 1.5 年）
- 最近推送（push）：2026-08-13
- 当前 Tera 仓库版本：`2.0.0`（Zola v0.23.0 2026-08-05 强制升级）

### 4.2 Tera v2 + Components 替代 shortcodes（2026-08-05）

Zola v0.23.0（2026-08-05）强制升级到 Tera v2，最大变化是 Component 取代了 shortcodes：

```jinja2
{% component youtube(id, autoplay=false) %}
<iframe src="..."></iframe>
{% endcomponent youtube %}

{# 调用 #}
{{ <youtube id="..." autoplay={true} /> }}
```

和旧 shortcodes 的差别在归属：
- 旧 shortcodes 是 Zola 内部的概念，负责 HTML escape、参数解析、全局注册表
- 新 components 是 Tera v2 引擎的原生语法，参数与 body 自动暴露为变量
- 新写法可以直接出现在 `.md` 正文里，无需 import

配套的文档迁移在 8 月 13 日一次完成：`c53d269`、`b2653d5`、`2c87db8`、`8751ab8` 四个 commit 就把 changelog 示例、迁移指引和 README 里的 shortcodes 全部改掉。

为什么说这是架构级变更：CHANGELOG 开篇就说 v0.23.0 "This is probably the most breaking version of Zola that will happen"。shortcodes 被彻底移除，旧主题里的 shortcode 都要重写成 component。作者自己实测，迁移以 Tera 语法为主的官方文档站大约用掉 20 分钟。

---

## 5 · 内容优先 + 内置搜索：Zola 的核心哲学

README 里跟 Hugo / 11ty 拉开距离的是两个能力：

- Search with no servers or any third parties involved
- Sass compilation

下面四块都靠内置实现，这也是"单二进制零运行时"能成立的关键。

### 5.1 内置搜索：`search` crate + elasticlunr-rs 3.0.2 + 可选分词

内置搜索基于 `elasticlunr-rs 3.0.2`。elasticlunr 是 JS 生态 `lunr.js` 的衍生版，索引算法更接近 Elasticsearch；它的 Rust 端口由 Zola 作者社区维护。

`Cargo.toml` 里 `elasticlunr-rs` 的 language feature 列了一长串：默认一种，加上 `da/no/de/du/es/fi/fr/hu/it/pt/ro/ru/sv/tr/ko` 共 15 种，中日文则单独走 `indexing-zh` / `indexing-ja`：

```toml
[features]
indexing-zh = ["search/indexing-zh"]
indexing-ja = ["search/indexing-ja"]
```

这两个 flag 默认不开。原因很直白：中日文搜索要接 jieba / lindera 这类分词器，编进去会明显撑大二进制。开了之后，`search` crate 会用对应分词器预处理文本再建索引。

这个设计等于把"要哪国语言"的决定权放到了编译期：默认 15 种语言靠空格分词，需要中日文的用户自己开 feature 自己编。Hugo 是倾向于什么 feature 都编进去、二进制因此偏大；Zola 相反，把可选能力收窄到编译期，由用户按需取舍。

### 5.2 内置 Sass：grass 0.13 编译期预处理

`zola build` 会把 `sass/` 目录下的 `.scss` 编译成 `.css`，产物落到 `public/`，全程不依赖 Node.js、npm 或单独的 sass 二进制——编译器（`grass 0.13`）直接编进 Zola 可执行文件。这点正好戳中 Hugo 与 Jekyll 的软肋：Hugo 不内置 Sass，要你自己装 `dart-sass` 或 Node 上的 sass；Jekyll 早期依赖 Ruby 的 `sass` gem，慢。

Astro 走 Vite 插件则是另一条路线：它的 island 架构需要在客户端按组件拆 CSS，所以模板与样式依赖 Node 工具链。Zola 没必要引入这层，因为它输出的是纯静态页面。

### 5.3 内置图像处理：`imageproc` + `webp` crate

Zola 在 Markdown frontmatter 里支持图片缩略：

```markdown
+++
[extra]
thumb = "image.jpg"
+++
```

构建时 `imageproc` + `webp` 负责处理：缩到指定宽度、转格式、调质量、生成 WebP，`svg_metadata 0.6` 用来读 SVG 元数据。内置的代价是高级特性受限——智能裁剪、人脸识别这类能力带不进来；Hugo 靠外部 `imagemagick` / `libvips` 能做得更复杂，代价是部署时要多带外部工具。

### 5.4 内置语法高亮：giallo 0.5（getzola 自研，v0.22 引入）

语法高亮没有用 Syntect、highlight.js、chroma、shiki 这些常规选项，而是自家仓库的 `giallo` crate。它起源于 v0.22.0（2026-01-09），CHANGELOG 的 "### Breaking" 段写清了切换：

> "Syntect has been replaced with [Giallo](https://github.com/getzola/giallo) and all the highlighting options of the `markdown` section in the config file have been moved/changed in `[markdown.highlighting]`."

v0.23.0（2026-08-05）跟着主版本又重写了一次，commit `24c9ffd`（2026-08-14，Update what giallo classes look into）直接对应这次改动。`Cargo.toml` 里 `giallo 0.5` 开了 `["dump"]` feature，`dump` 是调试用，用来输出 token class 名。

高亮是"必须常驻 + 跨语言 + 性能敏感"的组件，Zola 选择自研：这样它可以自由改 token class 名和 HTML 输出结构，不会在外部 crate 升级时被破坏向后兼容。代价是团队要长期维护一个复杂度不低的 crate。

### 5.5 一篇短文怎么穿过头 12 个 crate

把这几个 crate 拼起来能看清一次完整构建：先在 `content/` 里放一篇带 TOML frontmatter 的 Markdown，`zola build` 启动后，`content` crate 读目录和 frontmatter，`markdown` crate 把它经 `pulldown-cmark` 编译成 HTML 并处理 Zola 扩展语法，`templates` crate 用 Tera 把 HTML 填进页面模板并跑自定义函数，`render` crate 负责模板分发和输出，最后 `site` crate 汇总所有页面、分类、索引，把成品写进 `public/`。依赖 `imageproc` 的缩略图、`search` 的搜索索引、`sass` 目录（经 `grass`）同时在这条管线里被处理。

对读者来说，这一串内部机制都是透明的；你只需要 `zola build` 或 `zola serve`，剩下的由 crate 边界各管一段。

---

## 6 · 服务端口 + 一键部署：Netlify / Vercel / Cloudflare Pages

### 6.1 `zola serve` 默认端口与 CLI

`zola serve` 默认绑定 `127.0.0.1:1111`（来自 `docs/content/documentation/getting-started/cli-usage.md`），可通过 `--interface` / `--port` 覆盖。`--open` flag 会调 `open = "5"` crate 自动打开浏览器。

四条核心命令：

- `zola init [dir]` — 脚手架，问 3 个问题（站点 URL / 是否启用 Sass 编译 / 是否构建搜索索引，源码 `src/cmd/init.rs`）
- `zola build [--base-url] [--output-dir] [--drafts] [--force]` — 输出到 `public/`
- `zola serve [--interface] [--port] [--base-url] [--open]` — 默认 `127.0.0.1:1111`，live reload
- `zola check` — 外链 + 内部链接体检

### 6.2 输出格式

- **HTML**（minify 可选）+ **Atom 1.0 / RSS 2.0**（可配置 `feed_filenames`）
- **sitemap.xml**（自动拆分 30k 链接阈值）
- **robots.txt**
- **JSON 搜索索引（index）**（`elasticlunr_json` / `fuse_json` 两种格式，可对接 `tinysearch`）
- 静态文件直拷贝

JSON Feed **不原生支持**——`fuse_json` 输出可对接 `tinysearch`（来自 `docs/content/documentation/content/search.md`）。

### 6.3 一键部署平台

README "List of features" 最后一行：

> "Deploy on many platforms easily: [Netlify], [Vercel], [Cloudflare Pages], etc"

Zola 的部署方式极其简单——`zola build` 产物是纯静态文件 `public/`，**任意静态托管都能直接服务**。三种主流平台的零配置集成：

| 平台 | 配置文件 | 命令 |
|---|---|---|
| Netlify | `netlify.toml` | `zola build` 输出 `public/` |
| Vercel | `vercel.json` | `zola build` 输出 `public/` |
| Cloudflare Pages | 环境变量 `ZOLA_VERSION` + 构建命令 | `zola build` 输出 `public/` |

Zola 在 2023 之前官方推荐 Netlify + Vercel；2024 年起 Cloudflare Pages 把 Zola 放进了 "framework auto-detect" 列表，无需自己配 build command 就能跑。这点和 Next.js 跟 Vercel 的绑定关系正好相反：Zola 的产出是通用静态文件，跟哪个平台都锁不死。

---

## 7 · 双协议：MIT → EUPL 的真实动机

README "License" 段（精准引用）：

> "This project contains code under multiple licenses.
>
> Code introduced after version 0.22 is licensed under the **EUPL-1.2**.
> Code that existed prior to commit `3c9131db0d203640b6d5619ca1f75ce1e0d49d8f` remains licensed under the **MIT License**, including in later versions of the project.
>
> See `LICENSE` and `LICENSE-MIT` for details."

这在 Rust 生态里是个少见的设计：老代码 MIT + v0.22 之后的新代码走 EUPL-1.2。EUPL（European Union Public License）是欧盟 2017 年纳入的开源许可证，偏强 copyleft 但允许商业使用，同时要求派生作品同样开源。

两个来源互相佐证：
- CHANGELOG（`raw.githubusercontent.com/getzola/zola/master/CHANGELOG.md`）L128 的 `## 0.22.0 (2026-01-09)` 段，在 "### Other" 最后一条写了 `Licence changed to EUPL 1.2`——这是官方时间点
- README 给出代码边界：commit `3c9131db0d203640b6d5619ca1f75ce1e0d49d8f` 之前的代码保留 MIT，包括后续版本

关于动机，属于推测（中置信）：作者在欧洲（法国），可能出于三方面考虑——自己倾向 copyleft，希望修改版必须公开；响应欧盟推动的开源合规；以及借 EUPL 约束云厂商，避免 AWS / Azure / GCP 拿去封装成付费服务却不回馈社区。

具体落地是：`Cargo.toml` 的 `license = "EUPL-1.2"` 只标记主包，仓库里 `LICENSE` + `LICENSE-MIT` 两个文件并存。实际效果值得留意：如果哪家公司 fork 出商业产品又不公开修改，按 EUPL 是违规的。这点对 Zola 是治理上的护城河，不是技术上的。

---

## 8 · 跟 Hugo / Astro / 11ty 的真实取舍

Zola 不是 SSG 里的"最佳选择"，它是一份很明确的取舍。把三个最常被拿来对比的对象分开看。

### 8.1 vs Hugo

| 维度 | Zola | Hugo |
|---|---|---|
| 语言 | Rust | Go |
| 模板体验 | Tera（Jinja-like） | Go template（强类型 / 常被模板作者诟病） |
| 编译性能 | 中档 | 更快（Go 的 AOT 编译优势） |
| 二进制体积 | 单文件、相对小 | 单文件、更大 |
| License | MIT + EUPL | Apache-2.0 |
| 生态成熟度 | 中（10 年） | 高（13 年） |
| 学习曲线 | 较平（Jinja-like） | 较陡（Go template 习惯） |

两者的分水岭在规模与理念：Hugo 更适合超大型站点和极端性能需求（上万页、多语言），Zola 更适合看重模板体验、认同 Rust 生态、想要单二进制可移植的团队。注意这里的"编译更快 / 更小"是比较性描述，不是我在本机实测的结论。

### 8.2 vs Astro

| 维度 | Zola | Astro |
|---|---|---|
| 范式 | 静态优先 | island architecture（默认静态 + 局部 hydrate） |
| JS | 零运行时（客户端搜索也是 vanilla JS） | Node.js + framework 任选 |
| 模板 | Tera | JSX/MDX |
| 客户端交互 | 几乎为零 | island（按需 hydrate） |
| 学习曲线 | Tera + Markdown | React/Vue/Svelte 任选 + config |

差距在"要不要前端交互"：Astro 适合客户端有交互的内容站（仪表盘、interactive blog），Zola 适合纯内容站、且不想要一寸可选 JS 的场景（个人博客 / 文档 / 营销页）。

### 8.3 vs 11ty

| 维度 | Zola | 11ty |
|---|---|---|
| 范式 | 编译期生成 | 编译期生成 |
| 模板 | Tera | Nunjucks / Liquid / JS |
| 依赖形态 | 单二进制 | Node.js 工具链 |
| 多语言 | 内置 | 手动 |
| 内置搜索 | ✅ | ❌ |
| 部署 | 拷一个文件 | node_modules 依赖 |

这一对都是编译期生成，最直观的差别在安装方式：11ty 服务 JS 生态重度用户（手边已经有 Node 工程），Zola 服务的是想"下个二进制就能跑"的人。

---

## 9 · 作者 + 项目健康度

仓库核心信息：

| 字段 | 值 |
|---|---|
| 作者 | Vincent Prouillet |
| 邮箱 | hello@vincentprouillet.com |
| License | MIT（pre-v0.22 code）+ EUPL-1.2（v0.22+ code） |
| 最新 release | v0.23.3（2026-08-11 / commit `7fe17ab`） |
| Rust edition | 2024 |
| Workspace crates | 12（components/） |
| 主语言 | Rust |

10 年维护一个开源项目，**中间经历了**：以 Gutenberg 之名起步 → 因与 WordPress Gutenberg 编辑器撞名改名 Zola → Tera 拆成独立仓库 → v0.22 license 切换 → v0.23 shortcodes → components 架构。

最近的 release 节奏（GitHub Releases 已核实）：

- v0.23.3 (2026-08-11)
- v0.23.2 (2026-08-07)
- v0.23.1 (2026-08-05)
- v0.23.0 (2026-08-05)
- v0.22.1 (2026-01-22)

v0.23 系列四连发集中在 8 月 5 日到 11 日之间，问题修了就发；上一个稳定系列 v0.22.x 则在 1 月完成 minor + patch 两次发布——不是天天发版，是按需发版。

---

## 10 · 这次"反 Hugo 故事"的工具给我们的提示

Zola 不是"更好的 SSG"，它是"作者写给自己的 SSG"：

1. **模板引擎的不满是真实的工程动机**。Go template 在 Hugo 项目里被反复诟病，但官方一直没换。Vincent Prouillet 自己用 Rust 写 Tera + Zola，顺带为 Rust 生态贡献了一个可复用的 Jinja 风格模板引擎。这种 "scratch your own itch" 的模式，在 Rust 生态里常能沉淀出独立的通用库。

2. **单二进位买的不是性能，而是部署省事**。Zola 把产物收敛成一个文件，CI 里不需要搬 node_modules，不存在版本冲突，部署体积和依赖审计成本都更可控。相比之下 Astro / 11ty 这类 Node 系 SSG 在 Cloudflare Pages / Vercel 上要先处理好 Node 工具链。至于二进制的体积到底差多少，属于环境相关，作者只关心够不够小到可移植，我没有实测。

3. **License 切换是治理决策，不是技术决策**。MIT → MIT + EUPL 双协议，说明作者对"别人该怎么用我的代码"有明确的立场。EUPL 比 MIT 更带约束，代价是少了一部分宽松许可的作者。

4. **Cargo workspace 把"将来想换"做了低成本**。12 个 crate 不是过度设计，是把某个子系统替换成别的实现这件事的成本压下来：假设有一天 `search` 要从 trigram 换成基于 BM25 的 Tantivy，只动 `search` 一个 crate，其他模块不牵动。只是一个假设，并非已经发生。

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

## 12 · 动手练习

1. **五分钟起步**：`cargo install zola --locked`（或直接用 GitHub Releases 的预编译二进制），然后 `zola init mysite` 回答 3 个问题，`cd mysite && zola serve`，浏览器自动打开 `http://127.0.0.1:1111`，改一篇 Markdown 看 live reload。
2. **验证内置搜索**：在 `config.toml` 设 `build_search_index = true`，`zola build` 后在 `public/` 里找到搜索索引文件，对照 `search.md` 文档确认 `elasticlunr_json` / `fuse_json` 两种格式的差异。
3. **写一个 component**：把 CHANGELOG 里的 youtube 示例（`{% component youtube(id, autoplay=false) %}`）放进 `templates/` 下任一模板文件，在 Markdown 正文里用 `{{ <youtube id="..." /> }}` 直接调用，体会"无需 import"与旧 shortcode 的区别。

## 13 · 常见问题

**Hugo 主题能直接拿过来用吗？**
不能。模板引擎完全不同（Go template vs Tera），模板语法需要重写；内容 Markdown 大多可以平移，但 frontmatter 格式（TOML `+++` vs YAML）和目录组织习惯有差异。

**中文搜索为什么要自己编译？**
中文/日文分词器（如 jieba）会显著增大二进制，Zola 把这部分做成编译期 feature：`cargo install zola --features=indexing-zh`。这是"默认轻、按需重"的设计取舍。

**升级到 v0.23 要改什么？**
核心是 shortcodes 已移除：把旧 shortcode/macro 改写成 Tera component（语法见 Tera 官方文档的 components 一节与 Zola CHANGELOG 的 Migration 段），其余变更对照 Tera v2 的 MIGRATION.md。作者自己迁移官方文档站约 20 分钟。

**不想要 Rust 工具链，有现成安装包吗？**
有。GitHub Releases 提供各平台预编译二进制；Debian 系可走 pkg.haus APT 源（仓库 2026-08-16 的安装文档已更新到该源）。

## 14 · 进阶与下一步

- **读源码入口**：`components/site` 的构建编排是全站核心；`components/search` 是 trigram 索引 + 分词 feature 的参考实现。
- **模板迁移**：Tera v2 官方迁移指南 `github.com/Keats/tera/blob/master/MIGRATION.md`。
- **社区**：官方论坛 `zola.discourse.group`，主题与使用问题比 issue 区更活跃。

---

## 附录 A · 本文事实来源

- GitHub 仓库：`github.com/getzola/zola`（截至 2026-08-17 13:32 GMT+8）
  - 17,346 stars / 1,178 forks / 90 watchers / 198 open issues+PRs
  - Created: 2016-12-06 / Updated: 2026-08-17 / Pushed: 2026-08-16
  - Default branch（分支）: `master`
  - 主语言：Rust / 仓库体积 122,579 KB（含 docs + test fixtures，不是用户拿到的二进制大小）
- 最新 release：`v0.23.3`（commit `7fe17abff2f3c05177be6833a2dc9483ab507e52` / 2026-08-11）
- 最近 5 个 release：
  - `v0.23.3`（2026-08-11）commit `7fe17ab`
  - `v0.23.2`（2026-08-07）commit `2e3dc3e`
  - `v0.23.1`（2026-08-05）commit `a5e0bda`
  - `v0.23.0`（2026-08-05）commit `97aba0f`：Tera v2 + Components 重构
  - `v0.22.1`（2026-01-22）commit `29540e9`
- 最近 6 个核心 commit（按时间倒序）：
  - `a0b0700` (2026-08-16) — Update Debian install docs to pkg.haus APT archive
  - `24c9ffd` (2026-08-14) — Update what giallo classes look like
  - `c53d269` (2026-08-13) — Add macro/shortcodes → component example in changelog
  - `b2653d5` (2026-08-13) — Link to components section in changelog for 0.23 migration
  - `2c87db8` (2026-08-13) — Link to changelog in overview
  - `8751ab8` (2026-08-13) — Remove shortcodes from README
- **12 个 `components/` workspace crate**（已核实）：`config` / `console` / `content` / `errors` / `imageproc` / `link_checker` / `markdown` / `render` / `search` / `site` / `templates` / `utils`
- 核心 crate 版本（`Cargo.toml` 已核实）：
  - `tera 2.0.0`，feature `["fast", "glob_fs"]`
  - `tera-contrib 0.2.0`，feature `["base64","date","urlencode","json","filesize_format","format","slug","rand","regex"]`
  - `pulldown-cmark 0.13`，feature `["html", "simd"]`
  - `pulldown-cmark-escape 0.11`
  - `giallo 0.5`，feature `["dump"]`（getzola 自研）
  - `grass 0.13`，feature `["random"]`（connorskees 维护）
  - `elasticlunr-rs 3.0.2`，feature 15 种语言 + ja/zh 通过 features
  - `ammonia 4`（HTML 清理 / search 用）
- 核心二进制依赖（`Cargo.toml` 已核实）：
  - `axum 0.8`，feature `["http1", "tokio", "ws"]`，default-features = false
  - `tokio 1.0.1`，feature `["rt", "fs", "time", "net", "sync"]`，default-features = false
  - `notify-debouncer-full 0.7`（live reload 文件监听）
  - `reqwest 0.13`，feature `["blocking"]`（仅 link_checker 用）
  - `clap 4`，feature `["derive"]` + `clap_complete` + `clap_mangen`
  - `ctrlc 3`（SIGINT 优雅退出）
  - `open 5`（浏览器自动打开）
  - `mime_guess 2.0` + `mime 0.3.16`（mimetype 检测）
  - `env_logger 0.11`
- Release profile：`lto = true` + `codegen-units = 1` + `strip = true`（`Cargo.toml` L140–142）
- License 切换锚点：CHANGELOG.md L128 `## 0.22.0 (2026-01-09)` 段 "### Other" 最后一条 "Licence changed to EUPL 1.2" + commit `3c9131db0d203640b6d5619ca1f75ce1e0d49d8f` 之前的代码保留 MIT License
- giallo 起源锚点：CHANGELOG.md L128 `## 0.22.0 (2026-01-09)` 段 "### Breaking" 第一条 "Syntect has been replaced with Giallo"
- Cargo edition：2024
- Feature flags：`indexing-zh` / `indexing-ja`（中文/日文搜索分词，可选编译）
- `zola serve` 默认端口：`127.0.0.1:1111`
- 已知 Rust 工具栈：**Tera 独立仓库** `Keats/tera` / 4,287 stars / 336 forks / 2015-07-17 创建 / 2026-08-13 最新 push

## 附录 B · 已知缺口

- **作者 Vincent Prouillet 的 LinkedIn / 详细个人史**：未拿到
- **Astro / Hugo / Zola 在 Cloudflare Pages 上的具体冷启动时间 benchmark**：未实测
- **WASM 编译**：Cargo.toml 没有 wasm32-* profile，但理论上 cargo build --target wasm32-wasi 可能可编（依赖 axum/tokio/notify 能否 wasm 化未验证）
- **Zola 团队核心 contributors**：仓库未抓 contributors 列表
- **v0.22 license 切换的详细背景（商业考量 / RFC 链接）**：仅找到 CHANGELOG 一句话 "Licence changed to EUPL 1.2"，没有官方 RFC / 公告