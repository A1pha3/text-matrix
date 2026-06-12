# 文章健康检查 #91 (cron 850cf6e9 heartbeat)

**检查时间**: 2026-06-12 16:30 (Asia/Shanghai)
**距上次 #90 (16:00)**: 30 分钟（**30m 节奏恢复** ✓ —— 解除 #90 异常 2 "14:30+15:30 缺日志"）
**HEAD commit**: 0e6914c（#90 自身 log commit，26m ago 无新推进）

## 关键变化（vs #90）

**🆕 新发现**：
1. **aliases 缺口径校正**：实测 news/ 缺 aliases 实为 74（YAML 视角 84，含 10 份 TOML 已用 `aliases = [...]` 格式补全）—— 与 #90 报"news 缺 84"对齐但需说明 TOML 子集
2. **9 个 tech/ 草稿 untracked 维持**——与 #90 一致，30m 内无新增（推测批量采集/写作流程暂停或换目录）
3. **GitHub Actions 最新部署 = 27403104629 (08:05 UTC = 16:05 CST) success**——#90 commit 0e6914c 触发的部署成功落地，#91 时已在线

**🔁 延续**：
- ✅ TXTmix 健康（双条件全过）
- ✅ 4 早报 06-12 部署 4/4 全 200（稳 4h+）
- ✅ 4 早报 06-11 部署 4/4 全 200（稳 28h+）
- ✅ ai-morning-news-2026-06-12.md categories 维持 `["行业快讯"]`（#88 baea40e 修复保持）
- ✅ GitHub Actions 最近 5 次全 success（最新 27403104629 = 16:05 CST 部署 200）
- ✅ 30m 节奏恢复（16:30 窗口正常触发本 session）—— 解除 #89/#90 异常 2
- ⚠️ aliases 缺失面 672 份（vs #90 报 682 略低 10，#90 把 10 份 TOML 算漏了）

## 检查范围

- 4 早报 06-12 部署实时 HTTP 验证
- 4 早报 06-11 部署稳态验证
- TXTmix 域名 + 关键路径抽样（含 #88 异常 1 修复点 + 其他英文 URL 验证）
- aliases 缺失面精确统计（区分 YAML/TOML）
- 文章库 git 状态盘点
- cron 850cf6e9 + 早报 cron 状态对比

## 检查结果

### ✅ 正常项

| 检查项 | 结果 |
|--------|------|
| TXTmix 首页 | ✅ HTTP 200 |
| TXTmix /posts/ | ✅ HTTP 200 |
| TXTmix /categories/行业快讯/ | ✅ HTTP 200（289 份文章） |
| TXTmix /categories/技术笔记/ | ✅ HTTP 200（559 份文章，主力分类） |
| TXTmix /categories/财富自由/ | ✅ HTTP 200（9 份） |
| TXTmix /categories/技术博客/ | ✅ HTTP 200（4 份） |
| TXTmix /categories/技术指南/ | ✅ HTTP 200（2 份） |
| TXTmix /categories/视频精读/ | ✅ HTTP 200（14 份） |
| TXTmix /categories/news/ | ✅ HTTP 200（#88 baea40e aliases 命中） |
| TXTmix /categories/tech/ | ❌ 404（英文 URL 无中文分类映射，#88 异常 1 升级版） |
| TXTmix /categories/wealth/ | ❌ 404（同上） |
| 4 早报 06-12 部署 | ✅ 4/4 全 200 |
| 4 早报 06-11 部署 | ✅ 4/4 全 200（稳 28h+） |
| ai-morning-news-2026-06-12.md categories | ✅ `["行业快讯"]` |
| HEAD = origin/main | ✅ ahead=0 / behind=0 |
| GitHub Actions 最近 5 次 | ✅ 全 success（最新 27403104629 = 16:05 CST） |
| cron 850cf6e9 调度 | ✅ 16:30 cron 已触发本 session（30m 节奏恢复） |
| dig txtmix.com | ✅ 198.18.0.51（CIDR 198.18.0.0/15 段内） |
| 9 tech/ 草稿 untracked | ✅ 与 #90 一致（30m 内无新增） |
| untracked 总数 | 68（与 #90 一致：59 skills/ + 9 tech/） |

### ⚠️ 发现异常（4 项）

#### 异常 1（major）：aliases 缺口径校正 🆕

**实测对比**（vs #90 报"全站缺 682"）：

| 目录 | YAML `aliases:` 缺 | TOML `aliases =` 缺 | 实测缺 | vs #90 |
|------|----|----|----|----|
| news | 84 | 0（10 份已有） | **74** | -10（校正） |
| tech | 569 | 0 | **569** | 持平 |
| wealth | 6 | 0 | **6** | 持平 |
| thoughts | 2 | 0 | **2** | 持平 |
| video | 11 | 0 | **11** | 持平 |
| **全站** | **672** | **0** | **672** | -10（#90 误算） |

**根因**：
- #90 报 682 = 84+569+6+2+11+10（？）—— 多算了 10 份 TOML 已有 aliases 的
- 实际缺 672，其中：
  - **news 74 份**主要是 ai-evening-news-2026-03-24 + ai-side-hustle-morning 03-27 ~ 04-15 + ai-morning-news 04-14/04-15/05-26 等历史早报（#88 漏掉了部分非典型 slug 的早报）
  - **tech 569 份**全部是 0 aliases（技术笔记类历史遗漏）
  - wealth 6 + thoughts 2 + video 11 = 历史遗漏

**修复优先级**：待师父裁决 #88 异常 1 方案（A 不修/B alias/C 改 URL/D 批量加/E 折中），本次报"缺 672"为后续修复的精确基数

#### 异常 2（minor）：/categories/tech/ 与 /categories/wealth/ 仍 404

**现象**：
- /categories/news/ = 200（#88 baea40e 修复后）
- /categories/tech/ = 404（569 份技术笔记未加 `/categories/tech/` alias）
- /categories/wealth/ = 404（9 份财富自由未加 `/categories/wealth/` alias）

**修复选项**：
- A. 同 #88 方案，给 tech/ 569 份加 `aliases: ["/categories/tech/"]`、给 wealth/ 9 份加 `aliases: ["/categories/wealth/"]`
- B. 不修（与中文 URL 重复，SEO 价值低）
- C. 折中：仅给 news/ 226 份（已修）+ tech/ 头 50 份 + wealth/ 头 5 份

**待师父裁决**（延续 #88 异常 1 议题）

#### 异常 3（minor）：早报 cron status 状态不一延续

| Cron | Name | Last Status | Last Run | 备注 |
|------|------|-------------|----------|------|
| 878d492b | AI新闻早报 | error | 9h ago | 06-12 内容已交付，cron step fail |
| 27e08237 | 经济财经早报 | ok | 9h ago | 06-12 正常 |
| 28270175 | Web3早报 | ok | 8h ago | 06-12 正常 |
| abd75bdf | AI副业早报 | error | 8h ago | 06-12 内容已交付，cron step fail |
| 0045a8a5 | GitHub趋势榜-15点 | ok | 1h ago | 06-12 15:00 ok |
| abe31cfa | GitHub趋势榜-18点 | ok | 23h ago | 等 18:00 再触发 |
| bf7472fd | GitHub趋势榜-21点 | error | 19h ago | 06-09 disable 后产物清理待做 |
| **850cf6e9** | **文章健康检查** | **running** | **34m ago** | 本 session = #91 16:30 窗口 |

- 4 早报全部 content 已交付（4/4 HTTP 200），但 2 份 cron 标 error（与历史同款故障）
- 06-09 disable 5 个 GitHub 趋势榜 cron 之后，21点 trend cron 状态仍残留 error（19h ago 是 21:30 06-11 失败残留）

#### 异常 4（minor）：68 个 untracked 持续累积

- 全部位于 `skills/morning-report/` (59) + `content/posts/tech/` (9)
- 30m 内无新增（与 #90 一致）
- 9 tech/ 草稿在 #91 窗口内**未变化**——批量采集/写作流程可能暂停
- 继续遵循 #55 隔离铁律，不 add/commit/动

## aliases 缺失面（精确统计，#91）

| 目录 | 总 | 有 aliases | 缺 | 占比 |
|------|----|----|----|----|
| news | 300 | 216 (含 10 TOML) | 74 (YAML 缺) | 24.7% |
| tech | 725 | 156 | 569 | 78.5% |
| wealth | 10 | 4 | 6 | 60.0% |
| thoughts | 2 | 0 | 2 | 100.0% |
| video | 15 | 4 | 11 | 73.3% |
| **全站** | **1052** | **380** | **672** | **63.9%** |

> 注：#90 报 1062/682 包含 10 个 TOML 已有 aliases 的文件，#91 精确基数 1052/672 是后续补 alias 的真实工作量

## 未追踪文件盘点

- 68 个（与 #90 一致）
- 30m 内无新增
- skills/morning-report/ 59 + content/posts/tech/ 9
- 不 add/commit/动（#55 隔离铁律）

## 结论与建议

1. **TXTmix 健康**：双条件全过，4 早报 06-12/06-11 部署 8/8 全 200
2. **30m 节奏恢复** ✓ —— 16:30 cron 正常触发本 session，#89/#90 异常 2 解除
3. **aliases 缺口径校正** —— 实测 672（#90 误报 682），其中 news 74 + tech 569 + wealth 6 + thoughts 2 + video 11
4. **9 个 tech/ 草稿 untracked 维持**（30m 内无新增，可能批量流程暂停）
5. **/categories/tech/ 和 /categories/wealth/ 仍 404** —— 等待师父从 #88 异常 1 方案 A/B/C/D/E 中裁决（议题升级：现在 3 个英文 URL 需修）
6. **delivery fail-closed 延续**：本次报告仍可能无法向飞书推送（850cf6e9 announce 目标延续未生效）
7. **GitHub 趋势榜-18点 (cron abe31cfa) in 1h 31m**，下次心跳观察

## 记忆铁律复用

- TXTmix 双条件：dig 198.18.0.0/15 段 + HTTP 200 ✓
- 6-10 早报自动 push + verify gate 铁律 ✓
- 6-12 cron 飞书通知铁律：本日志完成后调用 `openclaw message send`（fail-closed 延续）
- 早报主 cron fail 时自动 backup 子代理补做 ✓
- untracked 隔离铁律 #55：不 add/commit/动 ✓
- 不硬编码单 IP，CIDR 段判断 ✓
- Hugo 分类 URL 用中文名（已加 HEARTBEAT.md）✓
- 路径修正铁律：txtmix.com 文章 URL = `/posts/news/<slug>/`（非 `/post/`，非 `/posts/<slug>/`）✓
- aliases 不能用单路径覆盖多文件 ✓（#88 关键发现，已在 #90/#91 强化记录）

## 下一步动作

- 17:00 cron 自动再触发 → 持续观察 30m 节奏稳定性
- 等师父回复 #88 异常 1 方案（A/B/C/D/E）—— 现升级为需修 3 个英文 URL（news/tech/wealth）
- 等师父回复 9 个 tech/ 草稿的处理方式（异常 #90 升级，#91 维持 9 个无新增）
- 等师父回复 672 份补 aliases 的执行时机（异常 1，#91 精确化）
- GitHub 趋势榜-18点 (cron abe31cfa) 17:30 触发，下次心跳观察
