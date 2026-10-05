---
title: "AutoCLI：一条命令抓遍 55 个网站的 Rust 命令行工具"
slug: "autocli-ai-command-line-generator-guide"
github_repo: "nashsu/AutoCLI"
source_key: "gh:nashsu/AutoCLI"
date: "2026-04-08T12:50:00+08:00"
lastmod: 2026-09-28T12:00:00+08:00
categories: ["技术笔记"]
tags: ["CLI", "Rust", "数据抓取", "AI Agent"]
description: "AutoCLI 是 TypeScript 项目 OpenCLI 的 Rust 重写：把 Twitter/X、Reddit、YouTube、B 站、知乎、小红书等 55 个网站、333 条抓取命令装进一个 4.7 MB 的单文件二进制，零运行时依赖。登录站点靠 Chrome 扩展复用会话，新站点靠 autocli.ai 生成适配器，为 AI Agent 提供全网实时数据。"
draft: false
---

AutoCLI 用 Rust 编写，前身是 opencli-rs，从 v0.2.4 起改名；它是对 TypeScript 项目 [OpenCLI](https://github.com/jackwener/OpenCLI) 的完整重写。它把 Twitter/X、Reddit、YouTube、Bilibili、知乎、小红书等 55 个网站的抓取逻辑封装成 333 条命令，编成一个 4.7 MB 的静态二进制，零运行时依赖。AutoCLI 适合需要频繁从公开网页拿数据的开发者和数据爱好者，不适合当生产级数据管道的核心组件——优势在覆盖广度、启动速度和零依赖部署，边界在浏览器会话依赖和站点改版风险。

## 快速信息卡

> **GitHub 仓库**: [nashsu/AutoCLI](https://github.com/nashsu/AutoCLI)
>
> | 指标 | 数值 |
> |------|------|
> | ⭐ Stars | 2,997 |
> | 🍴 Forks | 274 |
> | 📜 License | Apache-2.0 |
> | 💻 主要语言 | Rust |
> | 📅 最新版本 | v0.3.8（2026-04-20 发布） |
> | 🔗 在线服务 | [AutoCLI.ai](https://autocli.ai) |
>
> 指标取自 GitHub API，2026-09-28。

---

## 学习目标

读完本文你会了解：

- AutoCLI 解决什么问题，边界在哪里
- 命令层、适配器层、AI 服务如何分工
- Public / Browser / Desktop 三种模式各要什么前置条件
- 用 `explore`、`generate`、`cascade`、`search` 为新站点生成适配器
- 媒体下载和本地 CLI 透传这两个容易被忽略的能力
- 把 AutoCLI 接入 AI Agent 的三种方式

---

## 目录

- [快速信息卡](#快速信息卡)
- [学习目标](#学习目标)
- [总览地图](#总览地图)
- [架构深度解析](#架构深度解析)
- [任务流案例：从安装到抓取 B 站热门](#任务流案例从安装到抓取-b-站热门)
- [两个容易漏掉的能力](#两个容易漏掉的能力)
- [AI 能力实战](#ai-能力实战)
- [在 AI Agent 中集成](#在-ai-agent-中集成)
- [实践建议](#实践建议)
- [常见问题](#常见问题)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [总结](#总结)
- [参考与数据口径](#参考与数据口径)

---

## 总览地图

### 它是什么，不是什么

AutoCLI 的核心能力是用命令行从网站抓取结构化数据。每条命令对应一个网站的一个动作，例如 `autocli bilibili hot` 拉取 B 站热门，`autocli twitter search "rust lang"` 搜索推特。它的定位是网站数据的命令行封装层，介于通用爬虫框架和手写脚本之间——前者太重，后者太碎。

和原版 OpenCLI 的关系需要说清：AutoCLI 不是 fork，而是读完 OpenCLI（TypeScript，约 2.97 万 stars）之后的纯 Rust 重写，README 明确致谢原项目。功能对齐的前提下，官方口径是最快 12 倍、内存省一个数量级、单文件分发。

### 与原版 OpenCLI 的对照

| 指标 | AutoCLI（Rust） | OpenCLI（Node.js） |
|------|-----------------|--------------------|
| 内存占用（Public 命令） | 15 MB | 99 MB |
| 内存占用（Browser 命令） | 9 MB | 95 MB |
| 二进制体积 | 4.7 MB | ~50 MB（含 node_modules） |
| 运行时依赖 | 无 | Node.js 20+ |
| 测试通过率 | 103/122（84%） | 104/122（85%） |

| 命令 | AutoCLI | OpenCLI | 提速 |
|------|---------|---------|------|
| `bilibili hot` | 1.66s | 20.1s | 12x |
| `zhihu hot` | 1.77s | 20.5s | 11.6x |
| `xueqiu search 茅台` | 1.82s | 9.2s | 5x |
| `xiaohongshu search` | 5.1s | 14s | 2.7x |

两组数据都出自 AutoCLI README 的官方自测：对 55 个站点的 122 条命令做自动化测试，macOS Apple Silicon 环境。测试通过率说明两者功能覆盖基本对齐，差异在统计噪声内；耗时差距主要来自省掉 Node.js 启动和编译期内嵌的适配器（命令注册零文件 I/O）。注意这是项目方自述数据，本文未独立复测；原版 OpenCLI 也在活跃开发，对比是特定时点的快照。

### 分层结构怎么协作

按 README 的 Architecture 一节，AutoCLI 内部分四层，对外可以简化成「命令 → 适配器 → AI 服务」的心智模型：

```text
命令层      clap 动态子命令：autocli <site> <action> [--format json]
            内置命令（doctor、explore）+ 站点适配器命令 + 外部 CLI 透传
  │
执行引擎    参数校验 → 能力路由 → 超时控制
  │
YAML Pipeline 引擎              浏览器桥
fetch / select / map 等         Daemon（axum，默认端口 19825）
14 种步骤 + ${{ }} 模板表达式    ⇄ Chrome 扩展（chrome.debugger / CDP）
  │
AI 能力    autocli.ai 云服务：explore / generate / cascade / search
```

- **命令层**：解析参数，路由到对应适配器命令，按 `--format` 输出 table / JSON / YAML / CSV / Markdown
- **执行引擎**：校验参数、决定这条命令走 HTTP 还是走浏览器、控制超时
- **适配器层**：每条站点命令对应一份 YAML 声明的抓取流程；公开站点直接调 API，需登录站点经浏览器桥复用会话
- **浏览器桥**：本地 Daemon（默认端口 19825）与 Chrome 扩展之间用 HTTP + WebSocket 通信，扩展通过 chrome.debugger API 复用你已登录的页面
- **AI 层**：探索、生成、探测认证、搜社区适配器，全部由 autocli.ai 云端完成

仓库代码也按这个划分组织：`crates/` 下 8 个 crate（core、pipeline、browser、output、discovery、external、ai、cli），内置适配器经 build.rs 在编译期内嵌进二进制。

## 架构深度解析

### 命令模式：Public / Browser / Desktop

AutoCLI 把 55 个站点按认证方式分成三类，理解这个划分是使用的前提：

| 模式 | 含义 | 典型站点 | 前置条件 |
|------|------|---------|---------|
| Public | 直接调用公开 API，无需浏览器 | hackernews、devto、stackoverflow | 无 |
| Browser | 需要登录态，通过 Chrome 扩展复用会话 | twitter、bilibili、zhihu、xiaohongshu | Chrome + 扩展 |
| Desktop | 控制本地桌面应用 | cursor、codex、notion、discord-app | 桌面应用运行中 |

有两点容易忽略。其一，google、v2ex、bloomberg 的部分命令是 Public / Browser 混合：热榜类公开接口就能拿，搜索、个人通知类要登录。其二，Mode 是用户视角（要不要开浏览器），适配器内部还有一层更细的认证策略：`public`、`cookie`、`header`、`intercept`（网络拦截）、`ui`（UI 自动化）五种。Browser 模式的站点分别落在 cookie 到 ui 之间的不同策略上，这也解释了为什么 Desktop 模式最脆弱——它完全依赖目标应用的 UI 结构。

### 适配器层：声明式 YAML Pipeline

每条站点命令背后是一份 YAML 文件，声明站点名、命令名、认证策略、参数、输出列和 pipeline。pipeline 由 14 种步骤组成：`fetch`、`evaluate`、`navigate`、`click`、`type`、`wait`、`select`、`map`、`filter`、`sort`、`limit`、`intercept`、`tap`、`download`，覆盖从发请求、驱动页面到清洗数据的完整链路。

字段映射用 `${{ }}` 模板表达式，底层是 pest PEG 解析器——原版 OpenCLI 在这里用 JS eval，有注入风险，Rust 重写换成了类型安全的解析器。表达式支持比较、三元、管道过滤器，内置 16 个过滤器（`truncate`、`join`、`slugify`、`basename` 等）。

自定义适配器放进 `~/.autocli/adapters/` 即生效，这是官方文档给出的最小可用例子：

```yaml
# ~/.autocli/adapters/mysite/hot.yaml
site: mysite
name: hot
description: My site hot posts
strategy: public
browser: false

args:
  limit:
    type: int
    default: 20
    description: Number of items

columns: [rank, title, score]

pipeline:
  - fetch: https://api.mysite.com/hot
  - select: data.posts
  - map:
      rank: "${{ index + 1 }}"
      title: "${{ item.title }}"
      score: "${{ item.score }}"
  - limit: "${{ args.limit }}"
```

声明式结构带来两个直接后果：社区可以共享适配器文件，AI 生成适配器也只需要产出一段 YAML——这两点正是下一节 AI 层的基础。

### 浏览器桥：Daemon 与 Chrome 扩展

Browser 模式命令不走独立爬虫，链路是：命令 → 本地 Daemon（axum 实现，默认端口 19825）→ Chrome 扩展 → chrome.debugger API（CDP）。扩展复用的是你当前浏览器里已登录的会话，所以不需要导出、刷新、保管任何 token——这是 AutoCLI 区别于传统爬虫框架的关键设计，代价是命令执行时 Chrome 必须开着。

相关环境变量：

| 变量 | 默认值 | 作用 |
|------|--------|------|
| `OPENCLI_DAEMON_PORT` | `19825` | Daemon 端口 |
| `OPENCLI_CDP_ENDPOINT` | - | 直连 CDP 端点，绕过 Daemon（无头或远程浏览器场景） |
| `OPENCLI_BROWSER_COMMAND_TIMEOUT` | `60` | 命令超时（秒） |
| `OPENCLI_BROWSER_CONNECT_TIMEOUT` | `30` | 浏览器连接超时（秒） |
| `OPENCLI_VERBOSE` | - | 输出详细日志 |

### AI 层：探索三件套与社区市场

AI 能力由 autocli.ai 云端提供，本地命令调用云端接口：

| 命令 | 作用 | 典型场景 |
|------|------|---------|
| `autocli explore <url>` | 探测网站 API 面：端点、框架、状态 store | 不确定站点是否有公开接口 |
| `autocli generate <url> --goal <目标> --ai` | 先搜社区适配器，没有再让 LLM 分析页面生成 | 站点不在内置 55 个之列 |
| `autocli cascade <url>` | 按 PUBLIC → COOKIE → HEADER 探测认证策略 | 需要登录但不确定方式 |
| `autocli search <url>` | 搜社区共享适配器，交互列表选中即下载 | 别人可能已经写好 |

`explore` 的探测手段值得单独一提：`.json` 后缀探测（Reddit 式 REST 发现）、`__INITIAL_STATE__` 提取（B 站、小红书这类 SSR 站点）、Pinia/Vuex store 识别、框架检测（Vue/React/Next.js/Nuxt），加 `--auto --click` 还能交互式点按钮触发隐藏 API。不带 `--ai` 的 `generate` 是纯规则推理，不调云端。

云端同时运营适配器市场：生成的适配器保存到本地的同时同步到 autocli.ai，其他用户搜索就能复用。

## 任务流案例：从安装到抓取 B 站热门

下面用一个完整案例串起各层。目标：抓取 B 站热门视频，输出 JSON。

### 第一步：安装

**一键脚本（推荐）**：

```bash
# macOS / Linux，自动检测架构，装到 /usr/local/bin/
curl -fsSL https://raw.githubusercontent.com/nashsu/autocli/main/scripts/install.sh | sh
```

**手动下载**：从 [GitHub Releases](https://github.com/nashsu/autocli/releases/latest) 下载对应平台压缩包，解压后放进 PATH：

| 平台 | 文件 |
|------|------|
| macOS（Apple Silicon） | `autocli-aarch64-apple-darwin.tar.gz` |
| macOS（Intel） | `autocli-x86_64-apple-darwin.tar.gz` |
| Linux（x86_64） | `autocli-x86_64-unknown-linux-musl.tar.gz` |
| Linux（ARM64） | `autocli-aarch64-unknown-linux-musl.tar.gz` |
| Windows（x64） | `autocli-x86_64-pc-windows-msvc.zip` |

**源码编译**：

```bash
git clone https://github.com/nashsu/autocli.git
cd autocli
cargo build --release
cp target/release/autocli /usr/local/bin/   # macOS / Linux
```

更新就是重跑安装命令或覆盖二进制，没有额外迁移步骤。

### 第二步：配置 Chrome 扩展（Browser 模式必需）

B 站属于 Browser 模式，需要 Chrome 扩展复用登录会话：

1. 从 GitHub Releases 下载 `autocli-chrome-extension.zip`
2. 解压到任意目录
3. Chrome 打开 `chrome://extensions`
4. 开启右上角「开发者模式」
5. 点击「加载已解压的扩展程序」，选择解压目录
6. 扩展会自动连接本地 autocli Daemon

Public 模式命令（hackernews、devto、lobsters 等）跳过这一步直接可用。

### 第三步：运行命令

```bash
# 抓取 B 站热门，限制 20 条（需要浏览器已登录 B 站）
autocli bilibili hot --limit 20

# 输出 JSON，便于管道处理
autocli bilibili hot --limit 20 --format json
```

执行链路：命令层解析参数并路由到 bilibili 适配器 → 执行引擎校验参数、确认走浏览器通道 → 浏览器桥经 Daemon 把请求转给 Chrome 扩展，扩展用登录态发请求 → 适配器 pipeline 提取字段 → 按 `--format` 渲染输出。

### 第四步：诊断与补全

```bash
# 运行诊断，排查环境问题的第一步
autocli doctor

# 生成 shell 补全
autocli completion zsh >> ~/.zshrc
autocli completion fish > ~/.config/fish/completions/autocli.fish
```

### 配置文件与环境变量

AutoCLI 的用户级配置集中在 `~/.autocli/` 下：

| 路径 | 用途 |
|------|------|
| `~/.autocli/config.json` | autocli.ai 认证 token |
| `~/.autocli/adapters/` | 用户自定义适配器 |
| `~/.autocli/external-clis.yaml` | 用户注册的外部 CLI |

云端服务地址可用环境变量 `AUTOCLI_API_BASE` 覆盖，默认 `https://www.autocli.ai`；Daemon 端口和各类超时见[浏览器桥](#浏览器桥daemon-与-chrome-扩展)一节的 `OPENCLI_*` 变量表。

## 两个容易漏掉的能力

### 媒体与文章下载

抓取之外，AutoCLI 还封装了下载链路：

```bash
# B 站视频，走 yt-dlp，cookie 从浏览器自动提取
autocli bilibili download BV1xxx --output ./videos --quality 1080p

# 知乎专栏文章转 Markdown，图片本地化
autocli zhihu download "https://zhuanlan.zhihu.com/p/xxx" --output ./articles

# 微信公众号文章
autocli weixin download "https://mp.weixin.qq.com/s/xxx" --output ./articles
```

文章类下载会生成带 YAML front matter（标题、作者、日期、来源）的 Markdown，远程图片替换为本地路径，输出目录形如 `output/article_title/title.md` + `output/article_title/images/`。

### 本地 CLI 透传

AutoCLI 内置了六个外部 CLI 的透传：`gh`、`docker`、`kubectl`、`obsidian`、`readwise`、`gws`（Google Workspace）。

```bash
autocli gh repo list
autocli kubectl get pods
```

对 AI Agent 来说这是个省事的收口：Agent 只需要认得 `autocli` 一个入口，网页数据和本地 DevOps 工具都能调。

## AI 能力实战

### 认证 autocli.ai

```bash
autocli auth
```

命令会打开浏览器到 `https://autocli.ai/get-token`，输入 token 后经服务端校验，保存到 `~/.autocli/config.json`。

### 用 Chrome 扩展可视化生成适配器

v0.3.2 引入的选择器工具是生成适配器的主要入口：

1. 打开目标网站，点击 Chrome 扩展图标
2. 用鼠标框选需要的数据区域，扩展生成精确的 CSS 选择器
3. 点击 Generate，AI 基于选区自动扩展发现相关字段，生成完整抓取规则
4. 适配器保存到本地，同时同步到 autocli.ai，立即可用

手写选择器和解析逻辑的活儿交给 AI，用户的工作量集中在框选目标数据。

### 搜索社区适配器

```bash
# 按 URL 搜索
autocli search https://www.example.com

# 域名也行，自动补 https://
autocli search example.com
```

搜索范围是 autocli.ai 的社区适配器库，从交互列表选中后下载到本地即可使用。生成前先搜一遍，经常能省掉整个生成步骤。

## 在 AI Agent 中集成

README 把 AutoCLI 定位成 Agent 的信息获取外挂，给了三种接法：

**方式一：把 `autocli list` 写进 Agent 配置。** 在项目的 `AGENT.md` 或 `.cursorrules` 里配置 `autocli list`，AI Agent 启动时即可发现全部 333 条命令，按用户请求挑着调用。

**方式二：注册本地 CLI。**

```bash
autocli register mycli
```

注册信息落在 `~/.autocli/external-clis.yaml`，Agent 通过 AutoCLI 的统一入口调用你自己的工具。

**方式三：一键安装 Skill。**

```bash
npx skills add https://github.com/nashsu/autocli-skill
```

技能仓库单独维护，面向 Claude Code、OpenClaw 等 Agent，安装后 Agent 即获得跨站点的实时数据获取能力。

## 实践建议

### 采用顺序

1. **先跑 Public 命令**：装完直接 `autocli hackernews top --limit 10`，验证安装成功
2. **再配 Chrome 扩展**：解锁 Browser 模式，覆盖大部分中文站点
3. **尝试 AI 生成**：内置 55 站之外的需求，用 `generate` 或扩展选择器
4. **接入 Agent**：稳定使用后，把 `autocli list` 写进 Agent 配置

### 站点选择策略

| 场景 | 推荐命令 | 理由 |
|------|---------|------|
| 技术资讯 | `hackernews top`、`v2ex hot` | Public 模式，零配置 |
| 中文社区 | `zhihu hot`、`xiaohongshu search` | Browser 模式，需扩展 |
| 视频内容 | `bilibili hot`、`youtube search` | Browser 模式，支持下载 |
| 学术资料 | `arxiv search` | Public 模式，结构化数据 |
| 桌面自动化 | `cursor send`、`notion read` | Desktop 模式，需应用运行 |

### 安全考虑

| 风险 | 缓解措施 |
|------|---------|
| 登录态暴露 | 扩展经本地 Daemon（127.0.0.1:19825）通信，登录态留在本机 Chrome；用重要账号跑高频抓取前想清楚代价 |
| 触发站点风控 | 控制请求频率，避免高频抓取 |
| 适配器失效 | 站点改版后用 `generate` 重新生成 |
| API token 管理 | token 存在 `~/.autocli/config.json`，注意文件权限 |

### 已知边界

- **站点改版风险**：适配器依赖 API 路径和选择器，站点改版会失效，需要重新生成
- **Browser 模式绑定 Chrome**：扩展走 chrome.debugger，Firefox / Safari 没有对应方案；无头或远程浏览器可用 `OPENCLI_CDP_ENDPOINT` 直连 CDP
- **Desktop 模式脆弱**：依赖目标应用的 UI 自动化，cursor、notion 这类更新频繁的应用随时可能破坏兼容
- **全程联网**：Public 命令要访问目标站点，AI 生成依赖 autocli.ai，离线场景不适用
- **非生产级**：单机工具，无分布式调度、重试、监控

## 常见问题

**Q：AutoCLI 生成的适配器可以直接用于生产吗？**

A：不建议。它的定位是个人工具和 Agent 能力扩展，缺少生产环境需要的重试、监控、告警机制，适配器还会随站点改版失效。生产场景应配合任务调度系统和错误处理流程，用 AutoCLI 先验证可行性。

**Q：AI 功能背后是什么模型？**

A：README 没有披露。可以确认的是 AI 能力全部由 autocli.ai 云端提供，用户侧唯一相关的配置是服务地址（`AUTOCLI_API_BASE`），没有切换本地模型或第三方模型的入口。

**Q：生成的适配器使用什么许可证？**

A：AutoCLI 本身是 Apache-2.0。社区适配器的授权条款以 autocli.ai 市场页面为准，商用前先确认。

**Q：怎么调试一个不工作的适配器？**

A：`autocli doctor` 查环境，`--format json` 看原始字段，`autocli explore <url>` 看站点 API 面是否变化。站点改版导致的失效，重新 `generate` 一份通常比手补选择器快；想手改，适配器就是 `~/.autocli/adapters/` 下的一段 YAML。

## 自测题

1. **一条 `autocli bilibili hot` 从回车到输出要经过哪些环节？**
   - 参考答案：命令层用 clap 解析参数并路由到 bilibili 适配器命令；执行引擎校验参数、确认走浏览器通道；浏览器桥经 Daemon（19825 端口）把请求转给 Chrome 扩展，扩展用登录态发请求；适配器的 YAML pipeline 完成 fetch、select、map 等步骤；最后按 `--format` 渲染输出。

2. **为什么用 AutoCLI 抓登录站点不需要管理 token？**
   - 参考答案：Browser 模式复用 Chrome 里已登录的会话。命令经 Daemon 转给 Chrome 扩展，扩展通过 chrome.debugger（CDP）以当前登录态发请求，token 的保管方是浏览器本身。代价是执行命令时 Chrome 必须在运行。

3. **要为一个内置清单之外的网站添加支持，流程是什么？**
   - 参考答案：先 `autocli search <域名>` 看社区有没有现成适配器；没有就 `autocli explore <url>` 探测 API 面，再 `autocli generate <url> --goal <目标> --ai` 生成；拿不准认证方式时用 `autocli cascade` 探测。生成的 YAML 落在 `~/.autocli/adapters/`，可手动修改。

4. **AutoCLI 适合作为生产级数据管道的核心组件吗？**
   - 参考答案：不适合。它没有分布式调度、重试、监控这些生产组件，适配器还会随站点改版失效。合理用法是个人数据获取和 Agent 能力扩展；团队要采集，先用它验证可行性，关键链路再用生产级方案重写。

5. **怎么让 Claude Code 这类 Agent 用上 AutoCLI？**
   - 参考答案：把 `autocli list` 的输出写进 `AGENT.md` 或 `.cursorrules`，Agent 就能发现全部命令并按需调用，比如用 `autocli zhihu hot` 拿热榜、`autocli bilibili search` 找视频，把 JSON 结果喂回上下文再处理。也可以用 `npx skills add` 安装官方技能，或用 `autocli register` 把本地工具挂进统一入口。

## 进阶路径

**路径一：把它用成日常数据入口。** 先把 Public 命令跑熟——hackernews、arxiv、v2ex 都零配置；再配 Chrome 扩展解锁 Browser 命令；最后按需用 download 系命令把视频和文章落盘。到这一步，AutoCLI 的日常价值已经全部兑现。

**路径二：为新站点造适配器。** 挑一个内置 55 站之外的目标，走完 search → explore → generate → cascade 的完整流程，再打开生成的 YAML，对照 14 种 pipeline 步骤逐字段理解。能独立调通一个新站点，就掌握了 AutoCLI 的扩展机制。

**路径三：读源码、提适配器。** 仓库按 8 个 crate 划分，内置适配器经 build.rs 编译期内嵌，`cargo test --workspace` 跑 166 个测试。想贡献，从 `adapters/` 目录下的 YAML 入手门槛最低——补一条命令或修一个失效适配器，不需要碰 Rust 代码。

**进阶资源**：
- [AutoCLI GitHub 仓库](https://github.com/nashsu/AutoCLI)
- [AutoCLI.ai 在线服务](https://autocli.ai)
- [OpenCLI 原版项目](https://github.com/jackwener/OpenCLI)
- [autocli-skill 技能仓库](https://github.com/nashsu/autocli-skill)

## 总结

AutoCLI 的价值集中在三点：单二进制零依赖的部署体验、55 站 333 命令的覆盖广度、AI 生成适配器的扩展能力。作为 OpenCLI 的 Rust 重写，它把启动开销和内存占用压低了一个量级，代价是绑定 Chrome、依赖站点结构稳定。个人开发者和数据爱好者可以把它当网页数据瑞士军刀，配合 AI Agent 扩展信息获取能力；团队场景下先当采集的探索工具，确认可行后再用生产级方案重写关键链路。

---

## 参考与数据口径

- 功能、命令、配置、架构描述均出自 [nashsu/AutoCLI](https://github.com/nashsu/AutoCLI) 的 README（main 分支，2026-09-28 取）；最新 release 为 v0.3.8（2026-04-20 发布）
- 仓库指标（stars、forks、许可证、语言、时间戳）取自 GitHub API，2026-09-28
- 性能对照与耗时数据出自 README「Performance Comparison」一节，为项目方自测口径（122 条命令自动化测试，macOS Apple Silicon 环境），本文未独立复测
- 原版项目：[jackwener/OpenCLI](https://github.com/jackwener/OpenCLI)（TypeScript），AutoCLI 基于它重写，README 致谢节有明确说明
