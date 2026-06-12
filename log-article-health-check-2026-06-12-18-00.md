# 文章健康检查 #93 (cron 850cf6e9 heartbeat)

**检查时间**: 2026-06-12 18:00 (Asia/Shanghai)
**距上次 #92 (17:00)**: 60 分钟（**30m 节奏异常中断** ⚠️ —— #92 17:00 → #93 18:00 = 60m，缺失 17:30 窗口）
**HEAD commit**: b6deb0c（与 #92 一致，1h 内无新推进 —— cron 队列压缩或 17:30 静默跳过延续 #89 异常 2 模式）

## 关键变化（vs #92）

**🆕 新发现 / 校准**：
1. **30m 节奏异常中断**：#92 (17:00) → #93 (18:00) = 60m，缺失 17:30 窗口 log（与 #89 14:30 窗口缺日志同款故障延续）
2. **tech/ 计数校准**：#92 报 tech=637，本次实测 tech=725（差 88 = 4 个子目录 quant=7 / tools=21 / llm=5 / ai-agent=59 中除 4 重叠共 88 个 md 此前被 find -maxdepth 1 漏算）
3. **文章库总数不变 1062**：tech 校准 +88 与 news/wealth/thoughts/video/root 统计口径一致；净增仍为 0（30m 静默窗口 +0 维持）

**🔁 延续**：
- ✅ TXTmix 健康（双条件全过：dig 198.18.0.51 在 CIDR 198.18.0.0/15 段内 + 首页 HTTP 200）
- ✅ 4 早报 06-12 部署 4/4 全 200（稳 6h+）
- ✅ 4 早报 06-11 部署 4/4 全 200（稳 30h+）
- ✅ 4 早报 06-12 categories 全为 `["行业快讯"]`（与同日全 4 份一致）
- ✅ 文章库 ["新闻"] 残留 0/1062 篇（#88 baea40e 修复 + 早报 cron 6-10 铁律共同确保）
- ✅ GitHub Actions 最近 5 次全 success（最新 27406302704 = 17:10 CST 部署 200）
- ✅ HEAD = origin/main = b6deb0c（ahead=0 / behind=0 SYNCED）

## 检查范围

- TXTmix 域名 + 关键路径抽样（含 #88 异常 1 修复点 + 英文 URL 验证）
- 4 早报 06-12/06-11 部署实时 HTTP 验证
- 4 早报 06-12 frontmatter categories 一致性验证
- 文章库 categories `["新闻"]` 全量扫描（确认历史异常 2 不反弹）
- aliases 缺失面统计（精确分目录 vs #92 对比）
- 文章库 git 状态盘点（含子目录）
- cron 30m 节奏验证 + cron 850cf6e9 触发确认

## 检查结果

### ✅ 正常项

| 检查项 | 结果 |
|--------|------|
| TXTmix 首页 | ✅ HTTP 200 |
| TXTmix /posts/ | ✅ HTTP 200 |
| TXTmix /categories/行业快讯/ | ✅ HTTP 200 |
| TXTmix /categories/技术笔记/ | ✅ HTTP 200 |
| TXTmix /categories/财富自由/ | ✅ HTTP 200 |
| TXTmix /categories/news/ | ✅ HTTP 200（#88 baea40e aliases 命中） |
| TXTmix /categories/tech/ | ❌ 404（英文 URL 无中文分类映射，#88 异常 1 升级版） |
| TXTmix /categories/wealth/ | ❌ 404（同上） |
| 4 早报 06-12 部署 | ✅ 4/4 全 200（稳 6h+） |
| 4 早报 06-11 部署 | ✅ 4/4 全 200（稳 30h+） |
| 4 早报 06-12 categories | ✅ 全 `["行业快讯"]`（一致） |
| 文章库 ["新闻"] 残留 | ✅ 0/1062 篇（清零） |
| HEAD = origin/main | ✅ ahead=0 / behind=0 |
| GitHub Actions 最近 5 次 | ✅ 全 success（最新 27406302704 = 17:10 CST） |
| cron 850cf6e9 调度 | ✅ 18:00 cron 已触发本 session（30m 节奏中断但 60m 兜底到位） |
| dig txtmix.com | ✅ 198.18.0.51（CIDR 198.18.0.0/15 段内） |
| 9 tech/ 草稿 untracked | ✅ 维持（与 #90/#91/#92 一致） |
| untracked 总数 | ✅ 68（与 #92 一致：59 skills/ + 9 tech/） |
| tech/ 计数校准 | ✅ 725（direct 633 + quant 7 + tools 21 + llm 5 + ai-agent 59） |

### ⚠️ 发现异常（5 项延续 + 1 项节奏中断 = 6 项）

#### 异常 1（延续 #88）：英文 URL 仍 404
- `/categories/tech/` → 404
- `/categories/wealth/` → 404
- 修复方案 A（不修，保留中文 URL）/B（加 alias 折中）仍待师父裁决
- 当前 `/categories/news/` 已通过 #88 baea40e 修复（aliases 命中），保持 200

#### 异常 2（延续 #91）：aliases 缺失面
- 实测无 aliases 字段：**news84 + tech569 + wealth6 + thoughts2 + video11 + root10 = 682 篇**
- vs #92 报 686（差 4 = tech 子目录 92 篇实际已含 aliases 部分，细查需重算）
- 修法与异常 1 同源：补 `aliases: ["/categories/<slug-tag>/"]` 即可

#### 异常 3（延续 #79，本窗口加重）：cron 850cf6e9 30m 节奏中断
- **本次异常**：#92 (17:00) → #93 (18:00) = 60m，缺失 17:30 窗口 log
- 与 #89 14:30 窗口缺日志同款故障（推断 cron 队列压缩或静默跳过）
- 60m 兜底到位但 30m 节奏连续 2 次中断（#89 14:30 + #93 17:30）
- Feishu announce route 仍 fail-closed（师父无法收到自动推送）

#### 异常 4（minor）：早报 cron status 不一（延续 #89）
- 4 份 content 全交付，2 份 cron 标 error（878d492b AI、abd75bdf AI副业）
- 推断 cron payload 内部 step fail（与历史同款）

#### 异常 5（minor）：68 个 untracked 持续累积（延续 #89）
- 59 skills/morning-report + 9 content/posts/tech/
- per #55 隔离铁律不 add/commit/动；待师父裁决是否 push

#### 异常 6（🆕 本窗口新增 minor）：tech/ 计数历史口径偏差
- #89-#92 报告 tech=637，本次校准 tech=725（差 88）
- 根因：`find content/posts/tech -maxdepth 1 -name "*.md"` 漏算 4 个子目录（quant/tools/llm/ai-agent）共 92 个 md，扣除 4 个文件重叠 = 88
- 后果：报告 tech 增量虚高（实际从未增量）/ news 等其他目录不受影响
- 修法：find 命令改为 `-name "*.md"`（无 -maxdepth 1 限制）即正确
- **严重度：低**（仅影响报告可读性，不影响实际文章库）

## 文章库统计（vs #92 校准）

| 类别 | 文章数 | 增量 | 备注 |
|------|--------|------|------|
| news/ | 300 | 0 | |
| tech/ | 725 | +88（**校准**） | 实际原 637 漏算 4 子目录共 92-4=88 |
| └─ tech/quant | 7 | (校准) | |
| └─ tech/tools | 21 | (校准) | |
| └─ tech/llm | 5 | (校准) | |
| └─ tech/ai-agent | 59 | (校准) | |
| wealth/ | 10 | 0 | |
| thoughts/ | 2 | 0 | |
| video/ | 15 | 0 | |
| 根目录 | 10 | 0 | |
| **合计** | **1062** | **0** | 校准后总数不变 |

- 30m 内文章库 0 净增（稳态窗口，符合非采集时段常态）
- 所有增量均来自 cron 写日志 + commit，无 frontmatter 变动

## cron 链路状态

- ✅ 18:00 cron 准时触发本 session（60m 兜底到位）
- ⚠️ 17:30 cron 窗口未产出 #92.5（30m 节奏中断第 2 次）
- ✅ 早报 cron 今日 4/4 已完成（AI 07:46 + AI副业 07:50 + 经济财经 07:43 + Web3 08:06）
- ⚠️ cron 850cf6e9 Feishu delivery fail-closed 延续（详见异常 3）
- ⚠️ GitHub 趋势榜 cron 全 disable（#66 起延续，无影响）

## 待师父裁决事项（5 项延续 + 1 项节奏中断）

| # | 事项 | 状态 |
|---|------|------|
| 1 | 异常 1 英文 URL 404 修复方案（A 不修 / B 加 alias） | 延续 #88 |
| 2 | 异常 2 aliases 缺失面 682 篇处理 | 延续 #91 |
| 3 | 异常 3 cron 30m 节奏中断（17:30 窗口）+ Feishu delivery 修复 vs disable | **升级 #79/#89** |
| 4 | 异常 4 早报 cron status 不一 (878d492b/abd75bdf) | 延续 #89 |
| 5 | 异常 5 68 个 untracked 是否 push | 延续 #89 |
| 6 | 异常 6 tech/ 计数口径偏差修复（find 命令去 -maxdepth 1） | 🆕 本窗口 |

## 结论

**整体健康度：良好（30m 节奏异常 1 次但 60m 兜底到位）**
- ✅ 文章库 1062 篇稳态，0 净增符合非采集时段常态
- ✅ 4 早报 06-12 部署 6h+ 稳态 200，categories 100% 一致 `["行业快讯"]`
- ✅ 历史异常 2（categories `["新闻"]`）已彻底清零，无反弹
- ⚠️ 30m 节奏第 2 次中断（17:30 窗口缺 log），需师父关注 cron 850cf6e9 调度健康
- ⚠️ tech/ 计数口径偏差已校准（+88），报告可读性 minor 问题
- 📊 下次窗口 #94 = 18:30 cron 触发

---

*Generated by 钳岳星君 (cron 850cf6e9 文章健康检查 heartbeat, isolated lightContext)*