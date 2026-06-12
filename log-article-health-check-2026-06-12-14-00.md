# 文章健康检查 #88 (cron 850cf6e9 heartbeat)

**检查时间**: 2026-06-12 14:00 (Asia/Shanghai)
**距上次 #87 (13:30)**: 30 分钟（午后稳态窗口节奏正常）
**HEAD commit**: 2f69ccb（#87 自身 log commit）

## 关键变化（vs #87）🆕

**重大发现：baea40e commit 部署生效，但 aliases 实现存在设计缺陷**

1. ✅ **`/categories/news/` 现在 200**（#87 时 404），但实际命中的是 web3-morning-news-2026-06-12（alias 冲突随机胜出者）
2. ✅ **`ai-morning-news-2026-06-12.md` categories 已修正**为 `["行业快讯"]`（#87 报"残余 bug"，实际 baea40e 已一并修了）
3. ⚠️ **84 份文件仍缺 aliases**（#87 报告 94 份，实际更准的统计：300 总 - 216 已加 = 84 缺）
4. ⚠️ **aliases 实现逻辑缺陷**：baea40e 给 216 份文件全设为 `aliases: ["/categories/news/"]`（单路径，无 slug），导致：
   - 226 篇文章同时声明 `/categories/news/` alias → Hugo 只能任选一篇作为命中目标
   - 用户期望的 `/categories/news/<文章slug>/` 路径仍 404
   - 这意味着 #85 异常 1 实际上**没真正修复**用户的核心需求

## 检查范围

- 4 早报 06-12 部署实时 HTTP 验证
- aliases 修复落地验证（baea40e commit）
- TXTmix 域名 + 关键 URL 抽样
- 异常 1（英文 URL）实际功能验证
- 异常 2（web3 6-10 summary）延续盘点
- 84 份缺 aliases 文件分类
- cron 状态盘点

## 检查结果

### ✅ 正常项

| 检查项 | 结果 |
|--------|------|
| 4 早报 06-12 部署 HTTP | ✅ 4/4 全 200 |
| TXTmix 首页 | ✅ HTTP 200 |
| ai-morning-news-2026-06-12.md categories | ✅ `["行业快讯"]`（与同日其他 3 份一致，#85 异常 2 已修复） |
| ai-morning-news-2026-06-12.md aliases | ✅ `["/categories/news/"]` |
| financial-morning-news-2026-06-12.md aliases | ✅ 有 |
| web3-morning-news-2026-06-12.md aliases | ✅ 有 |
| /categories/news/ 实际服务内容 | ✅ 返回 web3-morning-news-2026-06-12（alias 冲突下的胜出者）|
| GitHub Actions 最近 6 次 | ✅ 全 success |
| HEAD = origin/main | ✅ ahead=0 / behind=0 |

### ⚠️ 发现异常（4 项）

#### 异常 1（critical）：aliases 实现逻辑缺陷 — 226 份共用单路径 alias ⚠️⚠️

**现象**:
- `baea40e` commit 给 216 份早报全部加 `aliases: ["/categories/news/"]`
- Hugo 处理 aliases 冲突：取某篇（实测为 web3-morning-news-2026-06-12，最新 deploy 胜出）
- `/categories/news/` 现在 200 ✓，但**只是该单篇文章的 alias 跳转**，其他 225 篇无法通过英文 URL 访问
- `/categories/news/<文章slug>/` 仍 404 ❌（slug 级路径未生效）

**实测**:
```
GET /categories/news/ → 200 (web3-morning-news-2026-06-12 内容)
GET /categories/news/ai-morning-news-2026-06-12/ → 404
GET /categories/news/ai-side-hustle-morning-2026-06-12/ → 404
GET /categories/行业快讯/ → 200 (中文分类页正常工作)
```

**根因**:
- `aliases: ["/categories/news/"]` 是单字符串路径，与 226 篇文章冲突
- Hugo 没有"按 slug 区分"的机制——aliases 是该文章 URL 的别名映射，不是分类 taxonomy 别名

**#85 异常 1 实际未修复**:
- #85 报告"/categories/news/ 404" → baea40e 让它 200 ✓
- 但用户实际期望（推测）：每篇早报都能通过 `/categories/news/<slug>/` 访问
- 当前实现只让 226 篇文章中的 1 篇（实际是 deploy 顺序中最新的）能通过 `/categories/news/` 访问

**修复方案对比**:

| 方案 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **A. 撤销 baea40e 的单路径 aliases** | 还原原状（让 /categories/news/ 仍 404） | 一行 revert，最简洁 | SEO 外链 404 仍在（与 #85 状态等价）|
| **B. 给每篇单独设置 slug 级 aliases** | `aliases: ["/categories/news/ai-morning-news-2026-06-12/"]` | 真正实现英文 URL 访问 | 需要 226 个文件单独 patch，无法批量（除非用脚本）|
| **C. Hugo 配置 permalinks** | 在 hugo.toml 加 `[permalinks] news = "/:section/:filename/"` | 全局生效，一次配置 | 改动 taxonomy 行为，影响其他分类页 |
| **D. 添加英文分类 taxonomy** | 新建 taxonomy "news" 并给文章加 `news: ["news"]` | 真正的英文 URL 结构 | 改动 frontmatter 字段，影响范围大 |
| **E. 接受当前状态** | /categories/news/ 命中最新文章即可 | 0 改动 | 与用户实际需求不符 |

**师父待裁决**: B/C/D 中选一，或保持 E。

#### 异常 2（major）：84 份文件仍缺 aliases（vs baea40e 描述"226 份全加"）

**实测统计**:
```
总文件: 300
有 aliases: 216
缺 aliases: 84
```

**缺 aliases 分布**:
- **73 份 ai-side-hustle 系列**（2026-03-27 ~ 2026-06-12）
- **10 份 morning-news 零星**（ai-morning-news 04-14/04-15/05-26 + financial 04-14/04-15 + web3 04-14/04-15/05-05/05-26/05-27）
- **1 份 evening-news**（ai-evening-news-2026-03-24）

**根因**:
- baea40e 的批量脚本 glob 模式有误，漏匹配 `ai-side-hustle-morning-*`（文件名不含 `news`）
- commit 描述"226 份全部"与实际不符（master 描述过度乐观）

**修复方案**:
- 给 84 份文件补 `aliases: ["/categories/news/<文章slug>/"]`（如异常 1 选 B）或 `["/categories/news/"]`（如选 A）
- 一行 fix，参考 baea40e 同样做法批量提交

#### 异常 3（minor，#87 延续）：web3-morning-news-2026-06-10.md 用 `summary` 而非 `description`

**现象**:
- 文件 frontmatter: `summary: "Web3 行业日报：..."`
- 全库其他 287 份用 `description:`, 1 份两者都有, 11 份都没有
- 当天 Web3 早报 cron 撰写时 frontmatter_autofill 工具未触发 description 回填

**影响**: Hugo 回退使用 summary，OG/Twitter meta 可能不一致。严重程度低。

**修复**: 一行 fix: `summary:` → `description:`（如要规范，可同时保留 summary 副本）

#### 异常 4（continuing）：cron 850cf6e9 delivery fail-closed

- 飞书 target 待配，所有 announce cron 无法向飞书推送
- 本报告仍按 cron 850cf6e9 heartbeat 流程在隔离 session 中完成
- 数据完整性 100%，仅通知链路缺

## 文章库 + Git 状态

- 文章库：300 markdown 文件
- HEAD：**2f69ccb**（#87 自身 log commit）
- HEAD 时间：2026-06-12 13:39 CST，距今 21m（节奏正常）
- HEAD = origin/main 同步
- 30m 静默窗口：4/30 静默延续（baea40e 后稳态，无新文章/新 push）
- GitHub Actions 最近 6 次：全 success（05:39 / 05:13 / 05:08 / 04:36 / 04:07 / 03:48）

## cron 状态盘点

| ID | 名称 | Last | Status | 备注 |
|----|------|------|--------|------|
| 850cf6e9 | 文章健康检查 | 30m ago | running | ✅ 14:00 heartbeat 触发本 session ✓ |
| 87f06cc6 | 心跳任务健康检查 | 45m ago | running | |
| b07f03b1 | 验证isolated-HEARTBEAT | 41m ago | running | |
| 178f0649 | 心跳触发器 | 53m ago | ok | |
| ad2640c0 | 心跳保活 | 1h27m ago | ok | |
| 878d492b | AI 新闻早报 | 6h30m ago | **error** | 06-12 文章 commit 41fdc9c + 部署 200 ✓ |
| 27e08237 | 经济财经早报 | 5h30m ago | ok | ✅ |
| 28270175 | Web3 早报 | 5h30m ago | ok | ✅ |
| abd75bdf | AI 副业早报 | 5h30m ago | **error** | 06-12 文章 commit dc0a3e6 + 部署 200 ✓ |
| 0045a8a5/abe31cfa/bf7472fd | GitHub 趋势榜 (15/18/21点) | 16–22h ago | ok/error | 06-09 disable 后延续 |

**⚠️ delivery fail-closed 延续**：所有 announce cron 仍 fail-closed（feishu target 待配）。

## 异常延续盘点（vs #85/#87）

延续 5 项（#81~#87 一致）：
1. 4 早报 frontmatter 偶发 YAML 转义（今日仍 0 例）
2. cron 850cf6e9 delivery fail-closed（飞书 target 待配）
3. AI 早报 / AI 副业早报 cron status=error 但文章已交付（cron step 日志待查）
4. ai-side-hustle 5## 阈值豁免已加（184fbb7），06-10 历史欠账 1 篇未补
5. skills/morning-report/ 下 debug 临时脚本 untracked 累积

**#85 新增 2 项 状态变化**：
- ~~6. `/categories/news/` 等英文 URL 全部 404~~ → **部分修复**（现 200，但实现有缺陷）
- ~~7. `ai-morning-news-2026-06-12.md` categories `["新闻"]` 6-11 同款 bug 残余~~ → **已修复**（baea40e 一并修）

**#88 新发现 2 项**：
- 8. **aliases 实现逻辑缺陷**（异常 1，critical）：226 篇共用单路径 alias，无法实现英文 URL 逐篇访问
- 9. **84 份文件仍缺 aliases**（异常 2，major）：baea40e glob 漏匹配

## 未追踪文件盘点

- 59 个（vs #85 报 63，#87 报 59 — 实测 #87=#88 一致）
- 30m 内 0 新增
- 继续遵循 #55 隔离铁律，不 add/commit/动

## 结论与建议

1. **TXTmix 健康**：双条件全过，4 早报 06-12 部署 4/4 全 200
2. **#85 异常 2 已修复**：ai-morning-news-2026-06-12.md categories 修正到位
3. **#85 异常 1 部分修复但功能不完整**：
   - 当前 /categories/news/ 200，但只能命中 1 篇文章
   - 用户实际需求（slug 级英文 URL）未实现
   - 建议师父从 B/C/D 三方案中裁决，或确认接受 E（当前状态）
4. **84 份缺 aliases 待补**：
   - 73 ai-side-hustle + 10 morning-news + 1 evening-news
   - 修复时机取决于异常 1 的方案选择（决定 aliases 值的形式）
5. **verify gate 状态**：4 早报 06-12 部署 4/4 全 200（实时 HTTP 验证，verify gate 脚本未跑但部署健康）
6. **delivery fail-closed 延续**：本次报告仍无法向飞书推送

## 记忆铁律复用

- TXTmix 双条件：dig 198.18.0.0/15 段 + HTTP 200 ✓
- 6-10 早报自动 push + verify gate 铁律 ✓
- 6-12 cron 飞书通知铁律：本日志完成后调用 `openclaw message send`（fail-closed 延续）
- 早报主 cron fail 时自动 backup 子代理补做 ✓
- untracked 隔离铁律 #55：不 add/commit/动 ✓
- 不硬编码单 IP，CIDR 段判断 ✓
- Hugo 分类 URL 用中文名（已加 HEARTBEAT.md）✓
- **新铁律候选**：aliases 字段不能用单路径覆盖多文件（会冲突），要么不用，要么按 slug 唯一 ✓（待师父确认后正式化）

## 下一步动作

- 14:30 cron 自动再触发 → 届时观察 aliases 实现是否被师父裁决修复
- 等师父回复 #85/#88 异常 1 的方案选择（B/C/D）
- 等师父回复 84 份补 aliases 的执行时机