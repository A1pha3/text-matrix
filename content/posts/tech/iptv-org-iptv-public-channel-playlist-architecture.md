---
title: "iptv-org/iptv 架构拆解：一个 12 万星仓库如何用 GitHub Issues + Actions 当 CMS"
date: "2026-06-13T18:07:17+08:00"
slug: "iptv-org-iptv-public-channel-playlist-architecture"
description: "拆解 iptv-org/iptv 的数据流水线：用 GitHub Issues 当 CMS、Actions 当 ETL 引擎，每日生成 600+ 个公开 m3u 播放列表。"
draft: false
categories: ["技术笔记"]
tags: ["GitHub", "TypeScript", "IPTV", "GitHub Actions", "开源"]
---

# iptv-org/iptv 架构拆解：一个 12 万星仓库如何用 GitHub Issues + Actions 当 CMS

> 一句话核心判断：**iptv-org/iptv 把 GitHub Issues 当作无服务器 CMS，用 GitHub Actions 当 ETL（Extract-Transform-Load）引擎，每天自动生成 600+ 个公开 m3u 播放列表，整个仓库不存任何视频文件，只存频道链接元数据**。这是一个用 Git 原生能力拼出"自动化内容运营"的典型案例，比传统 CMS 方案轻量得多，但代价是把"数据完整性"和"链接存活率"全部押注在社区贡献者的提交习惯上。
## 一、项目坐标

| 字段 | 值 |
|------|------|
| 仓库 | [iptv-org/iptv](https://github.com/iptv-org/iptv) |
| 主语言 | TypeScript |
| Stars / Forks | 约 118k / 6.3k（截至 2026-06） |
| License | 代码 MIT，频道元数据 CC0 |
| 协议 | Unlicense（GitHub API 显示），与 README 一致 |
| 维护形态 | 社区驱动 + iptv-bot 自动提交 |
| 调度频率 | 每天 UTC 0 点（北京时间 8 点）一次完整 ETL |

和它形成完整生态的姊妹仓库有三个：

- **[iptv-org/database](https://github.com/iptv-org/database)**（1.4k ★，JavaScript）：可用户编辑的频道元数据库（频道名、国家、Logo、官网、分类），核心数据源。
- **[iptv-org/epg](https://github.com/iptv-org/epg)**（3k ★，HTML）：从数百个来源下载 EPG（电子节目指南）。
- **[iptv-org/api](https://github.com/iptv-org/api)**（735 ★）：给第三方提供的 GraphQL / REST API。

这四个仓库加起来构成了一个完整的开源电视指南基础设施，而 `iptv` 是其中**面向终端用户**的那个（直接给 VLC、Kodi、IPTV 播放器用）。

## 二、系统地图：从 Issue 到播放列表

整个流水线可以分成 5 段，每一段都有清晰的代码边界：

```
┌─────────────────┐   ┌──────────────────┐   ┌─────────────────┐
│ 1. 数据加载       │ → │ 2. Issue 解析     │ → │ 3. 流合并与校验  │
│ (api:load)       │   │ (playlist:update) │   │ (内置在 update) │
└─────────────────┘   └──────────────────┘   └─────────────────┘
                                                      ↓
┌─────────────────┐   ┌──────────────────┐   ┌─────────────────┐
│ 6. README 同步    │ ← │ 5. 公开播放列表生成 │ ← │ 4. lint+validate│
│ (readme:update)  │   │ (playlist:generate)│   │  (preflight)    │
└─────────────────┘   └──────────────────┘   └─────────────────┘
```

对应到 `package.json` 的 npm scripts：

| 脚本 | 阶段 | 说明 |
|------|------|------|
| `api:load` | 1 | 拉取 `iptv-org/api` 的 GraphQL 数据到本地 `.api/` 目录 |
| `playlist:update` | 2 + 3 | 加载 Issues、合并流、保存到 `streams/{country}.m3u` |
| `playlist:lint` | 4 | 用 `m3u-linter` 校验内部分片 m3u 的格式 |
| `playlist:validate` | 4 | 跑测试验证更新逻辑本身没回退 |
| `playlist:generate` | 5 | 生成 600+ 个公开播放列表（按国家/语言/分类/地区/城市/源） |
| `playlist:export` | 5 | 输出 `.api/streams.json` 给 API 仓库用 |
| `readme:update` | 6 | 自动更新 `README.md` 和 `PLAYLISTS.md` 中的频道计数表 |

`scripts/commands/playlist/update.ts` 是整个流水线最核心的入口，下面是它的高层流程（删减了日志和异常处理）：

```typescript
async function main() {
  logger.info('loading data from api...');        // ① 加载频道元数据
  await loadData()

  logger.info('loading issues...');                // ② 加载未处理的 PR/Issue
  const issues = await loadIssues()

  logger.info('loading streams...');               // ③ 读已有的 streams/*.m3u
  await loadStreams()

  logger.info('processing issues...');             // ④ 解析、新增、关闭 Issue
  await processIssues(issues)

  logger.info('saving streams...');                // ⑤ 按 country 写回 m3u
  await saveStreams()
}
```

> 关键点：**仓库里 600+ 个 m3u 文件全部是 ETL 产物，源码里完全没有手工维护的播放列表**。这是它能保持日更的关键——README 里那个频道计数表（比如 `Animation: 85 channels`）是 `readme:update` 跑完生成的，不是谁手敲的。

## 三、Issue 作为 CMS：核心抽象

iptv-org 没有用任何传统的数据库或后台，整个"添加频道"的流程就是：

1. 用户在 [iptv-org/database](https://github.com/iptv-org/database) 里改 `channels.csv`（PR）。
2. 用户在 [iptv-org/iptv](https://github.com/iptv-org/iptv) 提一个 Issue，标题里贴上频道流链接。
3. Actions 每天跑一次：
   - `playlist:update` 找到所有 `state:open` 且标签为频道添加的 Issue
   - 用流链接去查 `iptv-org/api` 的频道元数据（频道名、国家、Logo）
   - 把流追加进 `streams/{country_code}.m3u`
   - Issue 自动关闭 + 留言

这意味着 **GitHub Issues 就是 ETL 的"输入队列"**，而 `iptv-bot[bot]`（`84861620+iptv-bot[bot]@users.noreply.github.com`）就是后端 worker。代码里负责读取 Issue 的工具函数是 `scripts/utils.ts` 里的 `loadIssues()`，背后是 `@octokit/plugin-paginate-rest`。

这种设计的代价：

- **链接失效是常态**：`m3u` 文件里的链接第三方能随便下架，所以仓库只能尽力去重和去死链，没法承诺 SLA。
- **Issue 噪音会污染评论**：项目 FAQ 第一条就是"我喜欢的频道不在列表里"，侧面说明很多用户把 Issue 当成贴吧用。
- **不能批量操作**：每次贡献只能加一个频道，要加 50 个频道得提 50 个 Issue 或一个 PR（但 PR 不在主流程里，走的是 data 仓库的 CSV）。

但反过来，它也有几个 Git 原生方案独有优势：

- **零运维成本**：不需要数据库、不需要后台进程、不需要缓存服务。
- **完全审计可追溯**：每条流的加入都对应一个 Issue，可点击查看。
- **贡献门槛极低**：用户只要会提 Issue 就能贡献，10 秒上手。
- **Bot 触发可控**：用 `permissions: contents: read` + GitHub App Token 限定 bot 只能推 `streams/`，不能碰其他文件。

## 四、生成器矩阵：从一份源数据切出 600+ 个播放列表

`playlist:generate` 阶段是仓库最有工程亮点的地方。它把同一份原始 `streams/*.m3u` 数据，按 **9 个维度**分别切出独立的 m3u 文件：

| 维度 | 示例 URL | 生成器 |
|------|---------|--------|
| 全量 | `index.m3u` | `IndexGenerator` |
| 全量（含每条频道的 EPG） | `index.m3u` | `IndexGenerator` + `@iptv-org/sdk` |
| 按国家 | `countries/cn.m3u` | `CountriesGenerator` |
| 按国家子区域（如省/州） | `subdivisions/us-ca.m3u` | `SubdivisionsGenerator` |
| 按城市 | `cities/berlin.m3u` | `CitiesGenerator` |
| 按地区（洲） | `regions/europe.m3u` | `RegionsGenerator` |
| 按语言 | `languages/zho.m3u` | `LanguagesGenerator` |
| 按分类 | `categories/news.m3u` | `CategoriesGenerator` |
| 按源头域名 | `sources/youtube.com.m3u` | `SourcesGenerator` |
| 按类别聚合索引 | `index.category.m3u` | `IndexCategoryGenerator` |

每个 generator 的实现风格都很像：

```typescript
// scripts/generators/categories.ts（伪代码示意）
async function generate() {
  const groupedStreams = streams.groupBy(s => s.category)
  for (const [category, streamList] of groupedStreams) {
    const playlist = new Playlist(streamList)
    await storage.save(`categories/${category}.m3u`, playlist.toString())
  }
}
```

核心数据模型是 `Stream` 类（在 `scripts/models/stream.ts` 里），它承担了所有维度字段（国家、城市、语言、分类、EPG ID、垂直分辨率）。`generate.ts` 还会先做一次排序去重：

```typescript
// 先按 id 升序，再按垂直分辨率降序，最后按 label 降序
streams = streams.sortBy(
  [s => s.getId(), s => s.getVerticalResolution(), s => s.label],
  ['asc', 'desc', 'desc']
)
// 同 id 只保留一条
streams = streams.uniqBy(s => s.getId() || uniqueId())
```

这就是为什么同一个频道在按国家分片里出现 100 次（每个国家都收录），但在按频道去重的全量播放列表里只出现一次。

## 五、一个频道从 Issue 到播放列表的完整生命周期

为了让上面的抽象有体感，下面用一个**虚构的频道流提交**走一遍全流程：

```
T+0  用户提交 Issue: "https://example.com/live/stream.m3u8 这是 CCTV-1 的流"
T+8h GitHub Actions 定时触发（cron '0 0 * * *' UTC）
     ↓
     ① api:load    → 拉取 iptv-org/api 的 GraphQL 频道元数据
                      查到 CCTV-1 的 channel_id, country='CN', languages=['zho'],
                      categories=['news'], logo='https://...'
     ↓
     ② playlist:update → loadIssues() 拿到上面这个 Issue
                          从 Issue body 解析出 URL
                          调用 getStreamInfo() 拿到流元数据（分辨率、HLS/DASH）
                          new Stream({ channel: 'CCTV-1', url: 'https://...', country: 'CN', ... })
                          写入 streams/cn.m3u
                          关闭 Issue 并留言
     ↓
     ③ playlist:lint   → m3u-linter 检查格式（必须包含 #EXTINF 行）
     ④ playlist:validate → 跑 jest 测试，确认 update 逻辑没回退
     ↓
     ⑤ playlist:generate → 9 个 generator 并行（实际上是 await 串行）输出
                            countries/cn.m3u（+1 条 CCTV-1）
                            categories/news.m3u（+1 条）
                            languages/zho.m3u（+1 条）
                            index.m3u（+1 条，已去重）
     ↓
     ⑥ playlist:export  → 写 .api/streams.json 给 iptv-org/api
     ⑦ readme:update    → 更新 README.md 和 PLAYLISTS.md 里的计数表
     ↓
     ⑧ iptv-bot commit + push (用 GitHub App Token)
T+10h 用户刷新 https://iptv-org.github.io/iptv/countries/cn.m3u
       看到 CCTV-1 已就位
```

整条链路不依赖任何外部服务，只有 GitHub 本身的 API（Octokit）+ GitHub Actions（runner）+ 一个可选的 SOCKS 代理（`socks-proxy-agent`，用于绕过某些地区的网络限制）。

## 六、Bot 与权限边界

`.github/workflows/update.yml` 里有一段很关键的权限设计：

```yaml
permissions:
  contents: read  # 默认仅读

jobs:
  main:
    steps:
      - uses: tibdex/github-app-token@v1.8.2   # 创建 App Token
        with:
          app_id: ${{ secrets.APP_ID }}
          private_key: ${{ secrets.APP_PRIVATE_KEY }}
      - uses: actions/checkout@v6
        with:
          token: ${{ steps.create-app-token.outputs.token }}   # 用 App Token 重新 checkout
      # ...
      - name: Commit changes to /streams
        if: steps.playlist-update.outputs.processed_issues != 0
        run: |
          git add streams/
          git commit -m "updates channels"
          git push
```

关键点：

1. **默认 workflow token 只有 read 权限**，需要写入时切换到 **GitHub App Token**（`tibdex/github-app-token`），Token 的 scope 由 App 本身决定，最小化授权。
2. **`gh act` 本地调试路径**：所有 step 都加了 `if: ${{ !env.ACT }}`，意味着用 [ PROTECTED_69 ](https://github.com/nektos/act) 在本地跑 workflow 时会自动跳过 token 切换，方便开发者本地复现。
3. **commit 作者固定为 `iptv-bot[bot]`**：保证审计一致性，不会出现"是谁提交了这一批流"的多人歧义。
4. **只在有变更时才 commit**：`if: steps.playlist-update.outputs.processed_issues != 0` 避免每天空 commit。

这是 GitHub Actions 安全实践里一个非常干净的范例：**用 App Token 替代默认 GITHUB_TOKEN，把"权限边界"和"逻辑边界"绑在一起**。

## 七、为什么不存视频文件，以及法律边界

这是项目 FAQ 里被反复问的问题，README 的 "Legal" 段说得最清楚：

> **No video files are stored in this repository.** The repository simply contains user-submitted links to publicly available video stream URLs...

翻译成人话：

- 仓库只存**流媒体链接**（m3u8、ts、mpd 等），不存视频本身。
- 链接是用户提交的，由维护者社区人工/自动验证。
- 如果某个链接侵犯版权，可以开 Issue 申请移除（`6_copyright-claim.yml` 模板），但 GitHub DMCA 流程不适用于此场景。
- 仓库本身用 **CC0 / Unlicense** 声明元数据放弃所有权利（CC0 for data, MIT for code），这也是为什么第三方可以自由 fork 和分发。

这种"链接集合 + 不存储内容"的模式在版权法里属于链接服务（linking service），和 YouTube、Reddit 这种 UGC 平台性质类似——平台不承担内容责任，但需要响应移除请求。iptv-org 把这个边界划得很清楚，是它能运行 10+ 年不被 GitHub 整体下架的根本原因。

## 八、采用建议与边界

适合引入的团队：

- **媒体聚合类应用**（直播电视、IPTV、OTT 盒子）需要一个高质量、可维护的频道源。
- **研究/教学场景**：需要真实的"链接即服务"数据集做流媒体协议（HLS、DASH）实验。
- **企业内部知识库**：想用 Issue 当 CMS 又不想自建后台的小团队（10–100 人规模），这个仓库是绝佳的参考实现。

不适合的：

- **需要 SLA 的商业播放**：流链接随时可能死，必须有自己的心跳检测和容错。
- **需要付费内容**：iptv-org 只收录公开免费流，付费频道不在范围。
- **大并发拉取**：`iptv-org.github.io/iptv/index.m3u` 这个文件本身就 50+ MB，加载所有频道需要稳定网络。

二次开发建议：

1. **不要 fork 整个仓库做镜像**，直接用它的 `index.country.m3u` 等切片文件作为数据源即可。
2. **如果要写 EPG 解析器**，用 `@iptv-org/sdk`（已被 iptv 自身用），里面封装了 stream-id → EPG-id 的映射。
3. **如果要贡献**，必须遵守 CONTRIBUTING.md 的字段规范（比如国家用 ISO 3166-1 alpha-2 代码 `cn` 而非 `CN` 或 `China`），否则 lint 阶段会被拒绝。

## 九、总结

iptv-org/iptv 是一个**用 Git 原生能力做 ETL** 的典型案例：

- **GitHub Issues** = 内容输入队列（CMS）
- **GitHub Actions** = ETL 调度器（cron + 容器）
- **GitHub App Token** = 安全边界（最小权限写入）
- **`/streams/*.m3u`** = 数据湖（按国家分片的原始层）
- **9 个 Generator** = 数据加工（按维度切片的派生层）
- **`iptv-org.github.io`** = 数据发布（GitHub Pages 静态托管）

这种架构的优势是**零运维、完全可审计、社区友好**，代价是**强依赖贡献者质量和 GitHub 平台稳定性**。对于一个面向公众、链接存活率本身就是变量的电视指南项目来说，这个 trade-off 是值得的。

---

> **来源**：GitHub [iptv-org/iptv](https://github.com/iptv-org/iptv)，约 118k ★ / MIT (代码) + CC0 (数据) / 2026-06-13