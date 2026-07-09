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
1. 抓取 GitHub 趋势榜 3 个维度（curl UA 直连 https://github.com/trending）
2. 合并 3 个榜单项目（去重），进入唯一正确路径
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