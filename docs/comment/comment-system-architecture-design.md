---
title: "Text Matrix 的 Giscus 评论实施方案"
date: 2026-04-03T00:00:00+08:00
lastmod: 2026-08-26T00:00:00+08:00
draft: false
tags: ["评论系统", "Hugo", "Giscus", "GitHub Discussions"]
categories: ["系统基建"]
---

> 本文的 V1 结论：先使用 **Giscus + 独立公开的 GitHub comments 仓库 + GitHub Discussions**。只在 `txtmix.com` 的生产文章页显示评论；Cloudflare Preview、GitHub Pages 镜像、本地环境和普通页面一律不加载。
>
> Giscus 不适合隐藏评论仓库。它一定会公开暴露绑定的 `owner/repo`；独立 comments 仓库只能隔离主站源码仓库，不能让评论后端隐身。

本文是 Text Matrix 的 Giscus 接入说明，面向维护者。它优先解决三件事：以最小运维成本上线可治理的评论、避免预览页产生脏讨论、为以后迁移到 Waline 保留清楚边界。

## 1. 为什么先选 Giscus

Giscus 将每篇文章的讨论存入 GitHub Discussions。读者需要 GitHub 账号，并在首次评论时授权第三方 Giscus GitHub App 代表自己发布；评论、回复、审核、锁定和通知都在 GitHub 中完成，因此 Hugo 和 Cloudflare Pages 不需要新增后端、数据库或密钥。

这很适合作为当前 V1：

| 目标 | V1 的取舍 |
| --- | --- |
| 尽快上线评论 | 使用 LoveIt 已内置的 Giscus 支持 |
| 降低垃圾评论 | GitHub 登录是第一层门槛 |
| 不暴露主站源码 | 绑定独立 comments 仓库 |
| 数据长期可查 | 讨论保存在 GitHub Discussions |
| 点赞 | 关闭 Discussion 主帖 reaction 的展示；不把任何 GitHub reaction 当作可信或长期的站内点赞指标 |
| 未来改用 Waline | 保留文章 URL 与独立评论仓库；迁移时另行导出或归档 Discussions |

Giscus 的公开托管版本没有自建数据库，讨论由 GitHub 承载。页面加载时，它会按映射规则查找对应 Discussion；首次评论或 reaction 时才自动创建新的 Discussion。[Giscus 官方说明](https://giscus.app/)

以下情况不要选择 Giscus：需要匿名或邮箱评论、不能接受 GitHub 登录、不能接受任何 GitHub 仓库被访客识别，或评论数据必须完全由自己控制。这些需求成立时，直接进入 [Waline 实施方案](./waline-comment-system-implementation-guide.md)。

## 2. 本仓库的实际边界

| 观察项 | 当前现状 | 实施含义 |
| --- | --- | --- |
| 站点 | Hugo + LoveIt 静态站 | 评论只能作为浏览器端嵌入 |
| 文章模板 | `layouts/posts/single.html` 调用 `comment.html` | 可让文章默认显示 Giscus |
| 其他模板 | `layouts/_default/single.html`、`layouts/topic/single.html` 也调用 `comment.html` | 必须显式关闭，避免全站出现评论 |
| 构建环境 | Cloudflare Pages 主分支为 `production`；预览为 `preview`；GitHub Pages 为 `github-pages` | LoveIt 仅在 `production` 注入评论配置 |
| LoveIt 内置实现 | 会加载 `https://giscus.app/client.js`，并自动同步深浅色主题 | 不需要自写 Giscus 脚本 |

当前 LoveIt 有两个会影响配置策略的限制：

1. 对非文章页写 `comment: true` 时，主题会读取 `params.comment` 而非 `params.page.comment`。本方案不依赖这个行为；V1 仅开放文章页。
2. 主题在切换深浅色时会向 Giscus 发送 `reactionsEnabled: false`。该参数只控制 Discussion 主帖 reaction 的展示；为避免其状态前后不一致，V1 将 `reactionsEnabled` 固定为 `"0"`。GitHub 对评论回复本身的 reaction 行为不等于站内点赞能力，也不作为任何统计依据。

不要启用 `[params.page.comment.waline]` 或其他评论系统；同一页面只能保留一套评论初始化。

## 3. 先准备独立 comments 仓库

### 3.1 创建公开仓库

创建一个只承载评论的公开仓库，例如 `<owner>/text-matrix-comments`。它不应包含主站源码、构建脚本、部署密钥或私有运营资料。

README 可以只有一句：

```text
GitHub Discussions used for comments on https://txtmix.com.
```

独立仓库减少主站源码的暴露面，也让未来迁移只涉及评论数据。它**不会**隐藏仓库：`repo` 和 `repoId` 会进入页面配置，Discussion 也可以从评论区跳转访问。

### 3.2 启用 Discussions 与最小授权

在 comments 仓库中：

1. 到 `Settings` → `General` → `Features`，开启 `Discussions`。
2. 安装 [Giscus GitHub App](https://github.com/apps/giscus)。
3. 选择 `Only select repositories`，只授权这个 comments 仓库。
4. 在 `Discussions` 中创建分类：名称 `Comments`，格式选择 **Announcements**。

Announcements 分类只允许具有维护权限的人和 Giscus 创建新的 Discussion，普通访客仍能在已创建的 Discussion 下评论；这能避免访客绕开文章页随意新开讨论。[GitHub Discussions 分类说明](https://docs.github.com/en/discussions/managing-discussions-for-your-community/managing-categories-for-discussions)

### 3.3 限制可加载的站点来源

在 comments 仓库根目录提交 `giscus.json`：

```json
{
  "origins": ["https://txtmix.com"],
  "defaultCommentOrder": "oldest"
}
```

这会让 Giscus 只在精确匹配的生产 origin 上加载，阻止 Cloudflare Preview、GitHub Pages 镜像和本地页面使用正式 Discussions。不要把 `localhost`、`pages.dev`、GitHub Pages 或通配正则加入这个文件。Giscus 的来源限制是嵌入层防护，不是 GitHub 帐号权限的替代。[Giscus 高级配置](https://github.com/giscus/giscus/blob/main/ADVANCED-USAGE.md)

提交前先确认仓库公开、App 已安装、Discussions 已启用；否则 Giscus 配置页无法生成有效的 ID，读者也无法正常查看或评论。[Giscus 配置要求](https://giscus.app/)

## 4. 从 Giscus 配置页取得四个值

打开 [giscus.app](https://giscus.app/)，选择：

| 项目 | 选择 |
| --- | --- |
| Repository | `<owner>/text-matrix-comments` |
| Mapping | `pathname` |
| Category | `Comments` |
| Category-only search | 开启 |
| Reactions | 关闭 |
| Emit metadata | 关闭 |
| Input position | `bottom` |
| Language | `zh-CN` |
| Lazy loading | 开启 |

记录配置页生成的四个值：`repo`、`repoId`、`category`、`categoryId`。其中 `repoId` 与 `categoryId` 不是秘密，可以提交到 Hugo 配置；不要手工猜测或改写它们。

选择 `pathname` 的原因是它不依赖文章标题。把已发布文章的 URL 视为评论线程的主键：改标题、摘要、标签不会改变线程；改 slug、文件路径、URL 规则或域名则可能生成新线程，见第 7 节。

不要开启 Giscus 的 strict matching。当前 LoveIt 内置模板没有透传 `data-strict`，而 strict matching 对已有 Discussion 还要求维护标题哈希；这会把 V1 变成不完整的半配置。

## 5. Hugo 配置与页面范围

### 5.1 在 `hugo.toml` 增加 Giscus 配置

把下面配置加入根 [hugo.toml](../../hugo.toml) 的 `[params]` 下。将尖括号替换为 Giscus 配置页生成的真实值。

```toml
[params.page.comment]
  enable = true

  [params.page.comment.giscus]
    enable = true
    repo = "<owner>/text-matrix-comments"
    repoId = "<repoId>"
    category = "Comments"
    categoryId = "<categoryId>"
    lang = "zh-CN"
    mapping = "pathname"
    reactionsEnabled = "0"
    emitMetadata = "0"
    inputPosition = "bottom"
    lazyLoading = true
    lightTheme = "light"
    darkTheme = "dark"
```

这些值中没有服务端 secret；不要向 Hugo 仓库、GitHub Actions 或 Cloudflare Pages 添加 GitHub token。

### 5.2 只允许文章页调用评论 partial

保留 [layouts/posts/single.html](../../layouts/posts/single.html) 中现有的：

```go-html-template
{{- partial "comment.html" . -}}
```

然后从以下两个文件删除 `partial "comment.html" .` 这一行：

- [layouts/_default/single.html](../../layouts/_default/single.html)
- [layouts/topic/single.html](../../layouts/topic/single.html)

不要试图仅靠各页面的 `comment: false` 来补救。模板默认不渲染，才是可长期维护的边界：V1 只允许 `content/posts/**` 出现评论；About、Contact、Privacy、Search、文档页和专题页均不出现。

未来若确实要让某个文档页评论，不要直接写 `comment: true`。应先用项目级 `layouts/partials/comment.html` 修复或替换 LoveIt 的覆盖逻辑，并针对该页面做生产构建验证。

### 5.3 预览环境不显示正式评论

不需要为 Cloudflare Preview、GitHub Pages 或本地环境添加额外判断。当前主题只在 `hugo.Environment == "production"` 时把评论配置写入页面；本仓库的 Cloudflare 构建脚本也只将 main 分支设为 `production`。

因此必须保留以下约束：

- Cloudflare Preview 使用 `preview` 环境。
- GitHub Pages 镜像保持 `github-pages` 环境。
- 不要为了本地验证把环境改为 `production`，更不要把这些 origin 加进 `giscus.json`。
- 真正的写入测试只在 `https://txtmix.com` 的受控测试文章完成。

## 6. 隐私、治理与通知

在启用配置的同一次发布中更新 [隐私政策](../../content/privacy-policy.md)，至少说明：

- 评论由 Giscus 嵌入并存储在公开的 GitHub Discussions 中。
- 打开评论区会加载 `giscus.app` 及 GitHub 相关资源；评论者首次发布时，需要授权第三方 Giscus GitHub App 代表其在该 comments 仓库中发布。
- 使用评论功能时，同时适用 GitHub 与 Giscus 的条款和隐私政策；评论者的 GitHub 用户名、头像和公开资料会随公开评论显示。
- 评论、回复和 reaction 属于公开内容；不要在评论中提交敏感信息。
- 删除、隐藏、锁定或举报评论由 comments 仓库的维护者在 GitHub Discussions 中处理；提供站点联系渠道。

上线前为至少两位维护者授予 comments 仓库的 `Write` 或更高权限；若仓库属于组织，可按职责使用 `Maintain` 或 `Admin`。两位维护者都订阅 Discussions 通知。comments 仓库还应放置简短的 `CODE_OF_CONDUCT.md`，并在 README 写明举报与联系渠道。明确以下规则：

| 场景 | 处理 |
| --- | --- |
| 垃圾、诈骗或恶意链接 | 删除评论，必要时向 GitHub 举报并锁定 Discussion |
| 人身攻击或争议失控 | 锁定 Discussion，保留简短的处理说明 |
| 内容更正 | 回复更正来源；需要时编辑文章正文 |
| 读者要求删除 | 核对对应 GitHub 身份后删除其 Discussion 回复；无法核验时要求其从原 GitHub 账号发起请求 |

遇到短期垃圾评论攻击时，先隐藏或删除违规回复，再按 GitHub 的 interaction limits 限制新账号或近期贡献者互动；不要因为 Announcements 分类而误以为评论回复不会被滥用。

Giscus 不会把讨论内容纳入 Hugo 生成的 HTML，因此 Pagefind 不会检索评论。这是 V1 的刻意边界，不要为了显示评论数或评论搜索在构建期引入 GitHub token 与 API 同步。当前项目没有内容安全策略（CSP）；若以后在 Cloudflare 或应用层添加 CSP，必须显式允许 `https://giscus.app` 作为 `script-src` 与 `frame-src` 来源，否则评论区会被浏览器拦截。

## 7. URL、迁移与数据保留

### 7.1 URL 必须稳定

`pathname` 将文章路径作为 Discussion 检索依据。改标题不会影响既有讨论；改 URL 会让新 URL 搜到新线程。

URL 必须迁移时：

1. 在旧页面仍可访问时，在旧 Discussion 中置顶一条迁移说明和新链接。
2. 为文章添加 Hugo `aliases`，使旧链接仍可到达新页面。Hugo 默认生成的是 HTML `meta refresh` 跳转，并不保证 HTTP `301`；如果迁移要求搜索引擎或客户端收到真正的 `301`，再额外配置 Cloudflare Redirect Rule 或生成并部署 `_redirects` 规则。
3. 接受新 URL 开始新的 Giscus Discussion；不要伪造、复制或手改既有 Discussion 标题来“合并”线程。
4. 在迁移记录中保存旧路径、旧 Discussion URL、新路径和迁移日期。

### 7.2 以后迁移到 Waline

Giscus Discussions 不能被 Waline 自动读取。迁移时有两个安全选项：

1. **保留归档**：关闭 Giscus 嵌入，并逐条关闭旧 Discussion，才可把公开 Discussions 作为只读归档；Waline 从新评论开始。可再卸载 Giscus App，并用 interaction limits 作为防御补充；仅关闭嵌入或仅设置 interaction limits，都不能阻止读者直接在 GitHub 回复。
2. **受控导入**：用 GitHub API 导出主帖、评论与回复层级、作者、时间、编辑/删除状态、原 Discussion URL、Markdown 与附件引用；明确 reaction 是否舍弃。转换脚本必须可重复、可审计，并对涉及个人资料的导出限定访问者与保留期限；先在隔离数据库试跑，绝不直接写生产库。

V1 推荐第一种。除非历史评论具有明确业务价值，否则不要为了迁移少量评论而提前引入导入脚本和身份映射风险。

## 8. 发布验收

按以下顺序上线：

1. 创建公开 comments 仓库，开启 Discussions，安装 Giscus App，创建 `Comments` / Announcements 分类。
2. 提交 `giscus.json`，只允许 `https://txtmix.com`。
3. 在 giscus.app 取得 ID，并在 `hugo.toml` 写入配置。
4. 删除默认单页和专题页的评论 partial 调用，只保留文章页调用。
5. 更新隐私政策、维护者权限、`CODE_OF_CONDUCT.md`、举报渠道和 Discussions 通知。
6. 部署生产主站；先在一篇受控测试文章登录 GitHub 并评论。
7. 验收通过后，评论对全部文章页生效；不需要给每篇文章单独创建 Discussion。

| 检查 | 预期结果 |
| --- | --- |
| 文章页首次评论 | 自动在 `Comments` 分类创建一条 Discussion |
| 第二篇文章评论 | 创建独立 Discussion，不串线 |
| 同一文章改标题 | 仍加载原 Discussion |
| Cloudflare Preview / GitHub Pages / 本地 | 没有 `#giscus` 容器、Giscus 页面配置或 iframe |
| About、Contact、Privacy、Search、专题、文档页 | 没有 `#giscus` 容器、Giscus 页面配置或 iframe |
| 深浅色切换 | iframe 主题同步；主帖 reaction 展示保持关闭 |
| `giscus.json` 域名外页面 | Giscus 拒绝加载 Discussions |
| 禁用 JavaScript 或 Giscus 故障 | 正文与站点导航正常可用 |

建议运行：

```bash
npm run build
CF_PAGES_URL=https://txtmix.com \
  CF_PAGES_BRANCH=main \
  npm run build:cloudflare-pages
```

`npm run build` 和 Cloudflare main 构建会走 `production` 环境，能够验证 Giscus 容器与页面配置是否被输出。构建完成后，在 `public` 中检查：文章页仅有一个 `id="giscus"`，其 `window.config` 含 Giscus 配置；非文章页两者都不存在。不要以静态文件中是否出现 `giscus.app` 判断页面范围：LoveIt 的共享主题脚本包含这段运行时代码。再在生产站的受控测试文章中，用浏览器检查运行后生成的 Giscus script 与 iframe；非文章页不应生成容器、script 或 iframe。

## 9. 常见故障

| 现象 | 优先检查 |
| --- | --- |
| Giscus 提示仓库不可用 | 仓库必须公开；Discussions 已开启；Giscus App 已安装在正确仓库 |
| 页面没有评论区 | 是否为 `production` 构建；配置是否在 `[params.page.comment]`；文章是否走 `layouts/posts/single.html` |
| 普通页面也出现评论 | 是否仍在 `_default/single.html` 或 `topic/single.html` 调用了 `comment.html` |
| 提示 origin 不允许 | `giscus.json` 是否精确包含 `https://txtmix.com`；不要包含末尾 `/` |
| 一篇文章出现新线程 | 检查 URL 是否变化；确认仍使用 `mapping = "pathname"` |
| 深浅色模式异常 | 使用 Giscus 内置的 `light` / `dark`；不要使用 LoveIt/Utterances 的 `github-light` / `github-dark` |
| 评论不能发布 | 检查评论者已授权 Giscus App，且 Discussion 未被锁定；确认不是 GitHub interaction limits 拦截 |
| 看不到主帖 reaction | 这是 V1 的预期：主帖 reaction 展示已关闭；不要将评论回复的 GitHub reaction 视为站内点赞 |

## 10. 最终建议

Text Matrix 当前应先使用：**独立公开 comments 仓库 + GitHub Discussions + Giscus + 仅生产文章页 + origin 白名单**。

这条路径没有服务器费用、没有评论数据库、没有前端 secret，也不会把主站源码仓库作为评论后端直接暴露。它的代价同样明确：读者必须登录 GitHub，评论数据公开，并且 GitHub comments 仓库可被发现。等这些边界妨碍真实运营时，再迁移到 Waline，而不是在评论量尚未出现前维护两套系统。
