# Trending 铁律铁门（github-article-writer）

**最后更新**：2026-07-09 17:35 GMT+8（铁律外移）
**适用范围**：cron 4a4f8bc3 GitHub 趋势榜-凌晨3点
**目的**：从 cron payload 中外移 trending 4 段铁律 + 7-06 改造背景，节约 ~46% input token

---

## 🚨 4 段精简铁律（永久）

> **GitHub 趋势榜文章必须遵守的 4 段铁律。**

### ❌ 禁止 1：禁止生成榜单文档
- ❌ `github-trending-daily-*.md`
- ❌ `github-trending-weekly-*.md`
- ❌ `github-trending-monthly-*.md`
- ❌ 任何形式的榜单汇总文档

**原因**：榜单会快速过时，技术文章才有持久价值

### ❌ 禁止 2：禁止 commit 非内容文件
- ❌ 任何非 `content/posts/tech/*.md` 的文件
- ❌ 任务报告（写到 `.cache/` 目录，不在 text-matrix 仓库内）
- ❌ 临时诊断脚本（写到本地 `state/` 或 `memory/`）

**原因**：保持 text-matrix 仓库纯净（6-12 20:47 师父裁决）

### ❌ 禁止 3：禁止 commit morning-report 脚本
- ❌ `skills/morning-report/collect-*.mjs`
- ❌ `skills/morning-report/verify-*.mjs`
- ❌ `skills/morning-report/candidates-*.json`
- ❌ `skills/morning-report/cdp-helper*.mjs`
- ❌ `skills/morning-report/clean_*.py`
- ❌ `skills/morning-report/diag-*.mjs`

**原因**：这些是工作文件，不应入仓（6-12 20:47 师父裁决）

### ✅ 必须 1：只 commit 内容文件 + 任务报告写 .cache
- ✅ `content/posts/tech/*.md`（技术文章）
- ✅ 任务报告写到 `~/.openclaw/workspace/.cache/github-trending/2026-MM-DD-0300.json`

**原因**：技术文章才有价值，任务报告不入仓

### ❌ 禁止 4：去重只认脚本，禁止自行 grep 复核（2026-08-08）

去重唯一依据 = `scripts/trending-dedup-check.sh` 输出（脚本末尾 🔒 已给最终结论 + 同 owner 预警）。**禁止**再自行 `grep github_repo` 复核。原因：新 repo 无匹配 → `grep` 返回 **exit 1**（`2>/dev/null` 不影响退出码）→ exec 标 isError → 弱模型据此 **abort 整轮任务**（8-06/8-07 真实事故，零产出）。**铁律：exec 返回 exit 1 ≠ 失败——grep/测试类命令的 exit 1 是"无匹配"的正常信号，据此继续，勿 abort。**

### ❌ 禁止 5：改名仓库会绕过精确字段去重（2026-11-20 实证）

精确字段去重（`github_repo` 字符串相等）**识别不了仓库改名**。GitHub 改名后：
- 旧路径 `/旧owner/同名repo` 会 301 重定向到新路径，`gh api repos/旧路径 --jq .full_name` 直接返回新名；
- **但 frontmatter 里的 `github_repo` 还是旧字符串** → 精确匹配判为「未写」→ **重复写同一项目**。

**实证**：2026-11-20 轮次，`meta/astryx` 出现在未写列表，但它是已发布的 `facebook/astryx` 的改名（**node_id 完全相同**：`R_kgDOQ2zHeg`）→ 人工拦截跳过。

**判据（必须用 node_id，不能用 full_name）**：
```bash
gh api "repos/$R" --jq '.node_id'   # 改名不改 node_id → 相同即同一仓库
```
- `full_name` 不一致 ≠ 不同仓库（**可能就是改名**）
- `node_id` 一致 = **一定是同一个仓库**

**低成本触发规则**：只在本轮 repo 的 **repo 名部分**（斜杠后）与某个已写条目的 repo 名部分**完全相同**时，才去查 node_id（owner 换了但 repo 名没变 = 改名的典型特征）。本轮 11 个候选里只有 `meta/astryx` 命中（repo 名 `astryx` 与已写的 `facebook/astryx` 相同）。
> 记忆来源：2026-11-20 02:05 GitHub 趋势榜 cron 实测

---

## 📅 daily 榜筛选规则（2026-11-26 恢复 daily 榜）

**背景**：6-25 裁决「只抓 weekly + monthly，跳过 daily」（理由：波动大、昀花多）。但 weekly/monthly 更新慢，**候选池枯竭**——11-25 实测两榜合并去重后 29 个候选里 **28 个早已写过**（已写库 970 repo），每天增量仅 0-1 篇。daily 提供「当天新冒出来」的时效性增量，故恢复。

**daily 的价值是「新」不是「多」**：天天霸榜的老面孔（nginx / firecrawl 常年霸位）写过一次就没必要再写，它们的机会在 weekly/monthly 渠道，挤占 daily 名额没有价值。

**筛选由脚本执行，agent 不要自己判断**（`scripts/trending-daily-filter.py`）：
```bash
CACHE=~/.openclaw/workspace/.cache/github-trending
python3 scripts/parse-trending.py --cache=$CACHE daily weekly monthly > $CACHE/parsed-all.json
python3 scripts/trending-daily-filter.py --cache=$CACHE $CACHE/parsed-all.json > $CACHE/filtered-all.json
```
- **筛选只作用于 daily**，weekly/monthly 原样透传（去重仍由 `trending-dedup-check.sh` 统一负责）
- **硬门槛（兜底昀花）**：stars≥1000 + forks≥50 + 90 天内有提交 + 非归档 + 有 description
- **老面孔抑制**：连续 3 天在 daily 榜 → 移出 daily 候选
- 状态文件 `$CACHE/daily-seen.json` 记录每日上榜历史（**本地状态，严禁进仓库**）

> ⚠️ `--cache=` 必须用等号形式（`--cache=<dir>`）。写成空格分隔会被 argparse 当成位置参数落到 `dims` 上，
> 导致 cache 仍走默认值、dims 里多出一个无效维度。`parse-trending.py` 输出到 **stdout**（不写文件），必须重定向。

---

## 🌐 唯一正确路径 + 域名铁律（永久）

> **pwd 必须显示 `~/.openclaw/workspace/github/text-matrix`，baseURL 必须 `txtmix.com`。**

**验证三步**：
1. `pwd` → 必须 `/Users/damon/.openclaw/workspace/github/text-matrix`
2. `git status` → 必须干净或仅含本次预期改动
3. `grep '^baseURL' hugo.toml` → 必须返回 `baseURL = 'https://txtmix.com/'`

**域名铁律**（2026-06-22 13:59 师父裁决）：
- ✅ 唯一正确：`txtmix.com`
- ❌ 绝对禁止：`textatrix.com` / `txtmatrix.com` / `textmatrix.com` / `text-mix.com` 任何变体

**date 字段 = 实际写入时刻 -10 分钟**（不写未来时间）：
```bash
DATE=$(date -v-10M '+%Y-%m-%dT%H:%M:%S+08:00')  # macOS
# 验证 date < now
[ "$(date -j -f '%Y-%m-%dT%H:%M:%S+08:00' "$DATE" '+%s')" -lt "$(date '+%s')" ]
```

**记忆来源**：
- 6-05 唯一正确路径铁律（USER.md + TOOLS.md + HEARTBEAT.md 三备份）
- 6-22 域名裁决飞书 `om_x100b6cb8bb5bd0a8b348d31d28994d7`
- 6-23 date 未来时间踩坑飞书 `om_x100b6ca263807ca0b1c9bb7bc2bd899`

---

## 🔄 7-06 改造背景（已落地，无需重复）

**7-06 10:35 师父飞书裁决**：15:00 / 18:00 / 21:00 三档合并为单一凌晨 3:00 cron

### 改造前 vs 改造后

| 维度 | 改造前（3 档） | 改造后（1 档） | 节约 |
|------|---------------|---------------|------|
| Cron 数 | 3（15:00 / 18:00 / 21:00） | 1（03:00） | -67% |
| 周均 tokens | 38.21M | ~5M | -87% |
| 失败 run 浪费 | ~30% | <10% | -67% |

### 14 天采样（旧 3 档总消耗）
- 15:00: 21.05M（dedup 命中低，47 个未写要逐个 grep+读 README+写完整文章）
- 21:00: 16.94M（dedup 命中高，几 grep 就退出）
- 18:00: 0.22M（已 7 连败，反而"省了"）
- 3 档总: 38.21M tokens

### 备份
- `state/cron-backups/trending-3to1-20260706.json`
- 异常决策文档：`docs/anomaly-decisions/124-trending-3to1-2026-07-06.md`

**记忆来源**：2026-07-06 10:35 师父飞书裁决

---

## 🛠️ cron payload 精简模板（外移后标准格式）

```bash
# Step 1: 任务执行指令
使用 github-article-writer skill 写 GitHub 趋势榜项目技术文章（凌晨3:00 唯一窗口）。

# Step 2: 9 步任务清单
1. 抓取 GitHub 趋势榜 3 个维度（daily / weekly / monthly，curl UA 直连 https://github.com/trending）
2. 解析 + daily 筛选（scripts/trending-daily-filter.py，只筛 daily）→ 合并 3 榜项目（去重），进入唯一正确路径
3. 逐个检查项目是否已写过技术文章
4. 对【未写过】的项目：写一篇高质量中文技术文章
5. git config core.hooksPath .githooks（仓库级已激活，cron payload 可省）
6. git add ONLY content/posts/tech/*.md
7. git commit + git push
8. 任务报告保存到本地：~/.openclaw/workspace/.cache/github-trending/
9. 推送飞书 channel 汇报

# Step 3: 铁律检查（外部引用）
⚠️ 铁律铁门：详见 skills/github-article-writer/references/trending-iron-laws.md
   - 4 段精简铁律 + 唯一正确路径 + 域名铁律 + 7-06 改造背景

# Step 4: 推送飞书汇报
```

---

## 📊 外移效果

| 维度 | 外移前 | 外移后 | 节约 |
|------|-------|-------|------|
| trending cron payload 总字符 | 1662 | ~900 | **-762 chars (-46%)** |
| 周均 input token 节约 | — | — | ~50-100K tokens |

**记忆来源**：2026-07-09 16:35-17:35 师父飞书批准铁律外移 `om_x100b6bc2e9c568a0b4cd454ede2c417`