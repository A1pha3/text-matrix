# 文章健康检查 #87 (cron 850cf6e9 heartbeat)

**检查时间**: 2026-06-12 13:30 (Asia/Shanghai)
**距上次 #86**: 30 分钟（午后稳态窗口，节奏正常）
**HEAD commit**: baea40e（#85 修复 commits）

## 检查范围

- 6-12 当天 4 份早报存在性 / frontmatter
- 最近 7 天文章 frontmatter 完整性
- 6-12 早报隐私敏感词扫描
- Hugo 全站 build 状态
- Cloudflare Pages 最近部署状态

## 检查结果

### ✅ 正常项

| 检查项 | 结果 |
|--------|------|
| 6-12 AI 新闻早报 | ✅ 存在 (16066 字节 / 117 行) |
| 6-12 AI 副业早报 | ✅ 存在 (21104 字节 / 172 行) |
| 6-12 经济财经早报 | ✅ 存在 (13455 字节 / 104 行) |
| 6-12 Web3 早报 | ✅ 存在 (6340 字节 / 92 行) |
| 4 份 categories 字段 | ✅ 全部 `["行业快讯"]` |
| 4 份隐私敏感词 (CDP/端口/API URL) | ✅ 无 |
| Hugo build | ✅ 5371 页 / 2582 aliases / 24.6s |
| 6-12 4 份 HTML 生成 | ✅ 全部在 public/posts/news/ |
| 最近 7 天 frontmatter | ✅ 完整 (categories/tags/desc/title/date) |
| Cloudflare Pages 最近 3 次部署 | ✅ 全部 success |
| 总文章数 | 300（无 draft=true） |

### ⚠️ 发现异常

#### 异常 1: aliases 字段缺失（94 份文件）

**现象**: baea40e commit 描述为"226 份早报全部加 aliases"，但实际只成功给 432 份加了 aliases，**仍有 94 份缺失**。/categories/news/ 兼容路径访问这些文章时 301 跳转失败（首页/分类页仍走 /categories/行业快讯/ 不受影响）。

**漏配文件分类**:
1. **ai-side-hustle-morning 整系列 82 份** (2026-03-27 ~ 2026-06-12)
2. **零星早期 12 份**:
   - ai-morning-news-2026-04-14 / 04-15 / 05-26
   - financial-morning-news-2026-04-14 / 04-15
   - web3-morning-news-2026-04-14 / 04-15 / 05-05 / 05-26 / 05-27

**根因**: baea40e 全局扫描 glob 模式有误，`ai-side-hustle-morning-*` 文件名不含 `news`，被 shell glob 漏匹配。

**今日 6-12 命中**: `content/posts/news/ai-side-hustle-morning-2026-06-12.md`

**修复建议**: 一行 fix，给 94 份文件补 `aliases: ["/categories/news/"]`，可参考 baea40e 同样做法批量提交。

#### 异常 2: web3-morning-news-2026-06-10.md 用 summary 而非 description

**现象**: 6-10 Web3 早报 frontmatter 使用 `summary:` 字段（其余 287 份用 `description:`, 1 份两者都有, 11 份都没有）。

**根因**: 当天 Web3 早报 cron 撰写时 frontmatter_autofill 工具未触发 `description` 回填。

**影响**: Hugo 在没有 description 时会回退使用 summary，两者在内容渲染上等价，但 OpenGraph / Twitter Card meta 标签可能不一致。严重程度低。

## 下一步

- **师父裁决后**: 补做 94 份 aliases 全量修复（一行 fix，参考 baea40e 做法），自动 push。
- **异常 2**: 可忽略或顺手 fix。
- 维持 30 分钟一次的 heartbeat 节奏，下次 #88 预计 14:00。