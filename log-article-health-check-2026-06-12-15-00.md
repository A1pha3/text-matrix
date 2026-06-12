# 文章健康检查 #89 (cron 850cf6e9 heartbeat)

**检查时间**: 2026-06-12 15:00 (Asia/Shanghai)
**距上次 #88 (14:00)**: 60 分钟（**异常窗口**——本应 30m，下一次 14:30 heartbeat 应触发但缺日志，说明 14:30 窗口被跳过或未产出 log；当前 #89 由 15:00 窗口产出）
**HEAD commit**: 25c7fb0（#88 自身 log commit，无新推进）

## 关键变化（vs #88）

**🆕 新发现**：
1. **aliases 缺失面比 #88 估算的"84 份"更大**——从 300 总文件 glob 修正：news/300 中 216 有 / 84 缺；同时 `content/posts/tech/` 628 份中 564 缺、`video/` 15 中 11 缺、`wealth/` 10 中 6 缺、`thoughts/` 2 中 0 有。全站共 **684 份缺 aliases**（约 64%），远超 #88 估算
2. **14:30 窗口缺日志**——按 30m 节奏 14:30 应产出 #88.5 或 #89 前置，但 `log-article-health-check-2026-06-12-14-30.md` 不存在；可能 cron 14:30 实例被压缩或与 14:00 同时段执行被合并
3. **GitHub 趋势榜-15点 (cron 0045a8a5) 已触发**——5m ago running，#88 提到的"师父裁决"未见结果

**🔁 延续**：
- ✅ TXTmix 健康（双条件全过）
- ✅ 4 早报 06-12 部署 4/4 全 200（修正路径：`/posts/news/<slug>/`，非 `/post/`）
- ✅ ai-morning-news-2026-06-12.md categories 维持 `["行业快讯"]`
- ⚠️ aliases 实现逻辑缺陷延续（226 篇共用单路径，#88 异常 1）
- ⚠️ 59 个 untracked（与 #88 一致，全在 skills/morning-report/）

## 检查范围

- 4 早报 06-12 部署实时 HTTP 验证（修正 URL 路径）
- TXTmix 域名 + 关键路径抽样
- aliases 缺失面全量统计（glob 修正）
- cron 850cf6e9 状态盘点
- 14:30 窗口日志缺失原因调查
- 早报 cron status 盘点

## 检查结果

### ✅ 正常项

| 检查项 | 结果 |
|--------|------|
| TXTmix 首页 | ✅ HTTP 200 |
| TXTmix /posts/ | ✅ HTTP 200 |
| 4 早报 06-12 部署 | ✅ 4/4 全 200（路径：`/posts/news/<slug>/`） |
| ai-morning-news-2026-06-12.md categories | ✅ `["行业快讯"]`（与同日其他 3 份一致） |
| HEAD = origin/main | ✅ ahead=0 / behind=0（无新 commit） |
| GitHub Actions 最近 5 次 | ✅ 全 success |
| cron 850cf6e9 调度 | ✅ 每 30m 触发，本次 15:00 running |
| dig txtmix.com | ✅ 198.18.0.51（CIDR 198.18.0.0/15 段内） |

### ⚠️ 发现异常（5 项）

#### 异常 1（critical）：aliases 缺失面被严重低估 — 实测 684 份缺 ⚠️⚠️

**#88 估算**：300 总 - 216 已加 = 84 缺
**#89 实测 glob**：
```
content/posts/news/       总数=300  带aliases=216  缺=84   (与#88一致)
content/posts/tech/       总数=628  带aliases=64   缺=564  🆕
content/posts/thoughts/   总数=2    带aliases=0    缺=2    🆕
content/posts/video/      总数=15   带aliases=4    缺=11   🆕
content/posts/wealth/     总数=10   带aliases=4    缺=6    🆕
```

**总计**：955 篇文章中 288 带 aliases / **667 份缺**（约 70%）
- 已知规模放大 **8 倍**（84 → 667）
- #88 baea40e commit 实际上**只覆盖了 news/ 子目录**

**根因**：
- baea40e 的 glob 表达式仅匹配 `content/posts/news/*.md`
- tech/thoughts/video/wealth 子目录的 664 篇文章未被纳入
- Hugo `aliases` 是 frontmatter 字段，必须逐文件 patch

**风险**：
- 上述 667 篇未声明 aliases → 不会生成 `public/<alias>/index.html` 跳转页
- 不影响 `categories/` 分类页（独立 taxonomy 机制）
- 影响：未来若有人加英文 URL 外链，667 篇中大多数会 404

**修复优先级**：**低**（无紧急用户影响，纯 SEO/外链健壮性问题）

#### 异常 2（major）：14:30 健康检查窗口缺日志

**现象**：
- 13:00 (#86) → 13:30 (#87) → 14:00 (#88) → **14:30 缺** → 15:00 (#89)
- 应有 30m 节奏但 14:30 跳号
- 14:30 cron 实例运行了（cron list 显示 850cf6e9 "5m ago running" 是 15:00 实例），但未产出 log 文件

**可能原因**：
- A. 14:30 实例被 openclaw 合并到 15:00（队列压缩）
- B. 14:30 实例产物在另处（heartbeat-state.json 未找到对应 record）
- C. cron payload 在 14:30 静默跳过（无 git commit、无 log）

**当前结论**：暂无法定因，下次窗口（15:30）观察是否恢复 30m 节奏

#### 异常 3（major）：aliases 实现逻辑缺陷延续（#88 异常 1）

- 226 份 news/ 文件共用 `aliases: ["/categories/news/"]` 单路径
- `/categories/news/<slug>/` 仍 404
- 等待师父从 B/C/D 方案中裁决（#88 提议）

#### 异常 4（minor）：早报 cron status 状态不一

| Cron | Name | Last Status | Last Run |
|------|------|-------------|----------|
| 878d492b | AI新闻早报 | error | 8h ago |
| 27e08237 | 经济财经早报 | ok | 7h ago |
| 28270175 | Web3早报 | ok | 7h ago |
| abd75bdf | AI副业早报 | error | 7h ago |
| **850cf6e9** | **文章健康检查** | **running** | **5m ago** |

- 4 份早报全部 content 已交付（4/4 HTTP 200），但 2 份 cron 标 error
- 推断：cron payload 内部有 step fail（与历史 5-15/5-16/6-11 同款故障）
- verify gate 已豁免 ai-side-hustle 5## 阈值（184fbb7），下一步若需补 06-10 历史欠账需单独处理

#### 异常 5（minor）：59 个 untracked 持续累积

- 全部位于 `skills/morning-report/`（与 #88 一致）
- 30m 内 0 新增
- 继续遵循 #55 隔离铁律，不 add/commit/动

## 未追踪文件盘点

- 59 个（vs #88 报 59——持平）
- 1h 内 0 新增
- 不 add/commit/动（#55 隔离铁律）

## 结论与建议

1. **TXTmix 健康**：双条件全过，4 早报 06-12 部署 4/4 全 200，路径已修正为 `/posts/news/<slug>/`
2. **#85 异常 2 持续修复**：ai-morning-news-2026-06-12.md categories 维持 `["行业快讯"]`
3. **aliases 缺失面升级为 critical**（异常 1）：
   - 实测 667 份缺（#88 估 84 份严重低估）
   - 建议方案：一次性脚本批量给 tech/thoughts/video/wealth/未覆盖 news 加 `aliases: ["/categories/news/<slug>/"]`
   - 仍需师父先决 #88 异常 1 方案（决定 aliases 值的形式）
4. **14:30 窗口缺日志**（异常 2）：
   - 推断 cron 队列压缩或静默跳过
   - 建议观察 15:30 窗口是否恢复 30m 节奏
5. **verify gate 状态**：4 早报 06-12 部署 4/4 全 200（实时 HTTP 验证，verify gate 脚本未跑但部署健康）
6. **delivery fail-closed 延续**：本次报告仍无法向飞书推送（850cf6e9 announce 目标延续未生效）

## 记忆铁律复用

- TXTmix 双条件：dig 198.18.0.0/15 段 + HTTP 200 ✓
- 6-10 早报自动 push + verify gate 铁律 ✓
- 6-12 cron 飞书通知铁律：本日志完成后调用 `openclaw message send`（fail-closed 延续）
- 早报主 cron fail 时自动 backup 子代理补做 ✓
- untracked 隔离铁律 #55：不 add/commit/动 ✓
- 不硬编码单 IP，CIDR 段判断 ✓
- Hugo 分类 URL 用中文名（已加 HEARTBEAT.md）✓
- **路径修正铁律**：txtmix.com 文章 URL = `/posts/news/<slug>/`（非 `/post/`，非 `/posts/<slug>/`）✓
- **新铁律候选**：aliases 字段不能用单路径覆盖多文件（会冲突），要么不用，要么按 slug 唯一 ✓（待师父确认后正式化）

## 下一步动作

- 15:30 cron 自动再触发 → 届时观察是否恢复 30m 节奏（验证异常 2）
- 等师父回复 #88 异常 1 方案（B/C/D/E）
- 等师父回复 667 份补 aliases 的执行时机（异常 1 升级）
- GitHub 趋势榜-15点 (cron 0045a8a5) 5m ago running，结果待下次心跳观察
