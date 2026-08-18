---
name: x-timeline
description: |
  采集 X（Twitter）「正在关注」时间线过去 24 小时内容并生成中文精选日报。
  触发词："X 精选""时间线摘要""x digest""刷一下 X""X 日报"。
  本地真实 Chrome + CDP，GraphQL 响应拦截为主路径（窗口必然闭合），DOM 滚动为兜底。
  强制双时间轴语义（入场时间判窗）、广告/墓碑硬过滤、LLM 三分类（宁松勿枉）、
  两级排序、非中文条目译文+details 原文、Hugo frontmatter 输出。
metadata:
  version: 1.0.0
  tags: ["x-timeline", "digest", "hugo", "cdp", "workflow"]
---

# X Timeline Skill

设计文档：`docs/product/x-timeline-skill-design.md`（v1.2，所有取舍依据以该文档为准）。

## 核心原则

**不漏、省时、可溯源**（三者冲突时按此顺序裁决）：

1. **不漏** — 24h 窗口内符合条件内容全部收录；主路径窗口必须闭合，"窗口未闭合"只能是故障态且必须在文内标注。
2. **省时** — 读者只看分类排序后的中文摘要；摘要 2-3 句实质提炼，不堆砌套话。
3. **可溯源** — 每条含原文链接（由采集数据构造，禁止猜测）+ 原文摘录，一键跳转核实。

## ⚠️ 双时间轴硬性规则（v1.2 定稿，违反即漏采）

- **收录与翻页边界一律按「入场时间」**：普通推 = 发布时间；转推 = 转推动作时间（外层 `created_at`）。
- **原推发布时间仅用于展示**（标注「原帖发布于 X 前」），不参与窗口判定。
- 原因：X 时间线按内容入场时间排序但显示原推时间；若按原推时间判定，"旧帖新转"既会被误裁，又会让翻页边界提前误判闭合而漏采后续全部新帖。

## ⚠️ frontmatter `date` 硬性规则（沿用 morning-report 约定）

- **绝对禁止**把「计划发布时刻」作为 `date`；`date` = 实际写入磁盘时刻 − 5 分钟。
- 推荐公式：`TZ=Asia/Shanghai date -v-5M "+%Y-%m-%dT%H:%M:%S+08:00"`。
- 原因：`date` 晚于 Hugo 构建时间的页面会被判为「未来页面」整篇排除。

## 执行流程

### Step 1 — 采集（输入：用户触发 → 输出：raw JSON）

```bash
cd <repo>   # text-matrix 仓库根目录
bun skills/x-timeline/scripts/collect-timeline.ts \
  --profile ./.chrome-profile \
  --out .workbuddy/tmp/x-digest/raw-$(date +%F).json
```

- 脚本自动：启动/复用 Chrome（`.chrome-profile` 登录态）→ 登录态检查 → 切「正在关注」Tab → 拦截 `HomeLatestTimeline` GraphQL 响应 → 按入场时间翻页至窗口闭合 → raw JSON 逐页增量落盘。
- **退出码约定**：`0` 窗口闭合；`3` 窗口未闭合（有数据，文内必须标注覆盖时长）；`2` 需人工登录（脚本会保持 Chrome 窗口打开，等用户登录后重跑）；`4` 风控/验证码拦截；`1` 其他错误（含无法确认「正在关注」Tab、页面加载超时）。
- **闭合语义**：raw JSON 的 `closed_reason` 为 `window_reached`（滚过 24h 边界）或 `timeline_exhausted`（关注时间线已滚到底，无底部游标）——两者均视为窗口闭合。
- GraphQL 拦截连续失败时脚本自动降级 DOM 滚动兜底路径（`--force-fallback` 可强制）；降级前会强制校验当前处于「正在关注」Tab，无法确认则中止，**绝不静默采集「For you」推荐流**。
- **绝不自动输入账号密码**；登录、验证码一律停下等人工。
- 脚本结束后 Chrome 窗口驻留以保持登录态（可手动关闭，不影响产物）。

### Step 2 — 结构规整（输入：raw JSON → 输出：候选清单）

按 `references/filter-rules.md` 第一节执行：

1. thread 链式合并（`in_reply_to_status_id`，同作者连续回复 → 一条，链接指串首）；
2. 重复转推去重（同原推保留关注层级最高的转推者）；
3. 引用对撞（保留原推，除非引用有独立增量）；
4. 跨日指纹去重（对照 `seen-post-ids.json`，滚动保留 90 天，命中即丢弃并计数）。

### Step 3 — 过滤（输入：候选清单 → 输出：通过条目 + 待复核清单）

1. **L1 硬过滤**：广告、入场时间窗外、无有效 permalink、墓碑条目；
2. **廉价预筛**（保守）：纯表情、无链接超短文本直接丢弃，拿不准一律放行；
3. **L2 LLM 三分类**（分批，每批约 50 条）：收录 / 待复核 / 丢弃，判定标准见 `references/filter-rules.md`。
4. **宁松勿枉**：拿不准的进「待人工复核」清单，文末单列，禁止静默丢弃。

### Step 4 — 分类与排序（输入：通过条目 → 输出：分组排序结果）

1. 按 `references/categories.md` 的 7 类归组（空分类不输出）；
2. 两级排序键：**作者层级**（`references/profile.json` tier1 > tier2 > tier3 > 陌生）为主键，**信息密度**（数据/结论/链接/代码 > 独立观点 > 转述）为次键；
3. **今日头条**：从「核心关注作者 + 高信息密度」条目中推选最多 3 条置于文首。

### Step 5 — 翻译与撰写（输入：排序结果 → 输出：草稿）

- 非中文条目：摘要与主摘录用中文译文，`<details>` 折叠块保留原文原貌（`profile.json` 的 `show_original_in_details` 可关闭）；
- 专有名词保留原文，首次出现括注中文；业界通用名（GitHub、Chrome 等）不译；
- 翻译忠实，**禁止增补原文没有的事实、数字、判断**；
- 每条三要素齐备：摘要（2-3 句）+ 原文摘录（≤3 行）+ `[原文](url)`。

### Step 6 — 输出与自检（输入：草稿 → 输出：Hugo 文章）

1. 按 `references/template.md` 渲染，写入 `content/posts/news/x-timeline-YYYY-MM-DD.md`；
2. frontmatter：`date` = 写入时刻 − 5min、`slug: x-timeline-YYYY-MM-DD`、`draft: false`、`categories: ["行业快讯"]`、`hiddenFromHomePage: true`；
3. 更新 `seen-post-ids.json`（本次收录条目入指纹库）；
4. 执行下方「输出前自检」，任一失败回到对应步骤重做；
5. 链接抽查：Browser 实开任意 3 条 `[原文](url)` 确认跳转正确（permalink 由采集数据构造，无需逐条核验）；
6. `git push`（失败则 `git pull --rebase` 后重试），push 成功才回报完成。

## 输出前自检

| 检查项 | 要求 |
| ------ | ------ |
| 时间窗口 | 主路径必须闭合；未闭合时文内显式标注覆盖时长 |
| 时间基准 | 收录与边界均按入场时间；旧帖新转未被误裁 |
| 广告清零 | 正文无任何 Promoted/推广内容 |
| 要素完整 | 每条含摘要 + 原文摘录 + 原文链接；非中文条目附 details 原文 |
| 翻译质量 | 非中文全部翻译；无臆造事实 |
| frontmatter | date ≤ 写入时刻 − 5min；含 `draft: false` 与 `hiddenFromHomePage: true`；slug 固定模式 |
| 只读承诺 | 全程无点赞/关注/发帖等写操作 |
| 统计一致 | 采集报告数字与正文条目数一致 |

## 禁止项

- 编造推文内容、作者、链接、时间；permalink 必须来自采集数据。
- 自动输入账号密码、绕过验证码、绕过登录墙。
- 任何账号写操作（点赞/关注/发帖/私信）。
- 把 `x.com/home` 等聚合页当作原文链接；输出裸 URL。
- 静默丢弃「拿不准」条目（必须进待复核清单）。
- 按原推发布时间判定窗口或翻页边界。
- 修改 slug 命名规则；`date` 填计划发布时刻。

## 安全边界

- 凭据：不存储/不读取/不传输密码与 Cookie；登录态仅存于本地 `.chrome-profile/`（`.gitignore` 已覆盖，新环境部署必须复核）。
- 数据出站：LLM 分类/翻译仅发送推文文本，禁止附带凭据；raw/filtered JSON 仅存本地 `.workbuddy/tmp`，不入 Git。
- 账号：只读 + 拟人化节奏（翻页间隔 2–5 秒随机，看门狗 10 分钟）；默认每日 1 次。
- 合规：若 X 明确禁止此类访问或账号收到警告，停用并改用官方 API/RSS。

## 完成汇报格式

- 文章文件名与收录条目数；各分类条目数；今日头条条数。
- 采集统计：总数、合并数、过滤数（广告/低价值/超窗/墓碑分项）、待复核数。
- 窗口状态：闭合（时间区间）或未闭合（实际覆盖时长 + 原因）。
- 是否执行了 git push；若用户只要草稿，明确说明未发布。

## 异常处理

详见 `references/troubleshooting.md`。关键原则：登录/验证码 → 停下等人工；拦截失败 → 降级兜底路径；定时失败 → 30 分钟后重试 1 次，二次失败仅报告不产出文章；零有效内容 → 仍生成文章如实报告，不硬凑。
