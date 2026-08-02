# 早报系统铁律铁门（morning-report 共用）

**最后更新**：2026-07-09 17:35 GMT+8（铁律外移）
**适用范围**：所有 4 份早报 cron（AI 新闻 / 经济财经 / Web3 / AI 副业）
**目的**：从 cron payload 中外移历史铁律档案，节约 ~30% input token

---

## 📚 铁律总览（按时间线）

| 编号 | 触发日期 | 铁律内容 | 来源飞书 |
|------|---------|---------|----------|
| 6-9 | 2026-06-09 | 隐私铁律：早报正文严禁暴露 CDP/PID/JSON 路径等采集实现细节 | om_x100b6b... |
| 6-10 | 2026-06-10 | 早报自动 push + verify gate：AI 验证通过即可 push，不等师父确认 | om_x100b6b... |
| 6-19 | 2026-06-19 | Web3 早报事件级去重：采集后必须先跑 dedup.sh 剔除严重复用 URL | om_x100b6c7e... |
| 6-30 | 2026-06-30 | pre-commit 钩子激活（双层防御，仓库级 .git/config 已生效） | om_x100b6b03... |
| 7-06 | 2026-07-06 | quota-guard Step 0：连续错误 > 2 自动跳过本 run | om_x100b6b86... |

---

## ⚠️ 6-9 隐私铁律（永久）

> **早报正文严禁暴露采集实现细节。**

**适用范围**：content/posts/news/*-morning-news-YYYY-MM-DD.md 全部文章

**严禁出现在文章正文**（per 6-09 隐私铁律）：
- ❌ CDP 端口（9222 / 9224 等）
- ❌ PID（进程号）
- ❌ API URL（任何 /api/ 路径）
- ❌ 原始 JSON 路径（candidates-*.json 路径）
- ❌ 反爬墙说明（"绕过 Cloudflare" / "绕过验证"）
- ❌ og:description 内部元数据
- ❌ 任何暴露"这是 AI 自动采集"的实现细节

**唯一允许**：使用 web_fetch / web_search / Brave Search / 公开 RSS / 公开 API（cmc 等）

**记忆来源**：2026-06-09 师父飞书质询后确立

---

## ⚠️ 6-10 自动 push + 投递归 reconcile 铁律（永久，2026-08-02 方向1：单一投递路径）

> **verify 通过 = 早报价值已生成。git push best-effort（失败告警不挂任务，根治 commit/push 竞态误判）。飞书正文投递由 `早报自动收口` reconcile cron 统一负责——agent 不自投递正文。**

**为什么投递归 reconcile 而非 agent**（2026-08-02 对抗审查第四轮发现）：
- 曾尝试"agent verify 通过即自投递正文"（②），但与 reconcile 补投**功能重叠且冲突**——agent 自投递不更新 morning-fix state → reconcile 30min 后又投一次 → **用户收两份正文**（状态分裂）。
- reconcile 是确定性 bash，比 LLM agent 可靠执行投递；单一投递路径消除分裂；早报非实时，30min 内送达可接受。
- 故**投递正文唯一路径 = reconcile cron**（检测"文件在 + state.delivered=false" → 补投 → 更新 state），agent 只负责"生成 + push"。

**实施**：
1. ✅ `bash scripts/morning-news-verify.sh <目标文件绝对路径>` exit 0 才继续
2. ✅ exit 0 → git push origin main（**best-effort**：失败发飞书告警，但任务不因此 error）
3. ✅ git push 后核对 `gh run list --limit 1`（失败仅告警）
4. ✅ exit ≠ 0 → 飞书告警（失败原因+文件路径）→ 不 push，等处理
5. ✅ agent 最终回复 = 简短汇报（供框架 post-delivery 作"任务完成"信号；**正文不在此发**）
6. ✅ **飞书正文投递 = `早报自动收口` reconcile cron（7e6c42fe，每30min）自动检测补投**，agent 不自投递（防重复）

**工具强制**：verify.sh 包含 4 项检查：
- date ≤ now（不是未来时间）
- 隐私脱敏禁词 19 个
- 链接 200 验证（User-Agent 模拟真浏览器，最多 50 条 / 8 条失败容忍）
- 新闻条数 ≥ 6

**记忆来源**：2026-06-10 14:33 师父裁决（自动 push）；2026-08-02 对抗审查（push best-effort 治竞态 + 投递归 reconcile 单一路径；曾试 agent 自投递②因与 reconcile 冲突→用户收两份正文→回退）

---

## ⚠️ 6-19 Web3 去重铁律（NEW）

> **Web3 早报采集到候选 URL 后、动笔前必须先跑事件级去重脚本，命中严重复用（跨 ≥ 3 天）的 URL 直接丢弃。**

**实施**：
```bash
bash scripts/morning-news-web3-dedup.sh --threshold 3 --window 14 <url1> <url2> ...
```

**退出码**：
- `exit 0` → 无严重复用，正常进入下一步
- `exit 1` → 有严重复用，把"严重复用"URL 从候选清单剔除后进入下一步

**双层去重**：
- A 重：state file `~/.openclaw/workspace/state/web3-event-fingerprint.json`（135 个 event 库）
- B 重：扫 `content/posts/news/web3-morning-news-*.md` 全部历史早报

**auto-recovery 也必须跑**（6-19 早报 auto-recovery 漏跑导致 3 条 14 天/5 天/3 天旧闻）

**详细参考**：`skills/morning-report/references/web3-event-dedup.md`

**记忆来源**：2026-06-19 10:12 + 10:23 师父飞书 message `om_x100b6c7e144374a4b2ecba680b40b9b` / `om_x100b6c7ece4678a4b3bee5d58efd67f`

---

## ⚠️ 6-30 pre-commit 钩子激活（永久，仓库级）

> **text-matrix 仓库内任何 git commit 必须走 pre-commit 钩子。**

**当前激活状态**：
- ✅ 仓库级 `.git/config` 已激活（`core.hooksPath=.githooks`，commit 5e0da6b7 验证真在跑）
- 7 cron payload 这条已删除（2026-07-09 17:35 铁律外移时清理冗余）

**钩子功能**：
- frontmatter-lint：扫 commit 中所有 *.md 文件的 frontmatter，校验 date ≤ now / categories / tags 等

**7-06 5 个 cron + 3 个 trending cron 已纳入双层防御**（7-06 11:39 师父批准）

**记忆来源**：2026-06-30 15:49 师父飞书 message `om_x100b6b031e66dc80b2f6c0626a82a92`

---

## ⚠️ 7-06 quota-guard Step 0（永久）

> **失败 run 守护：连续错误 > 2 自动跳过本 run，避免空跑浪费 token。**

**实施**（cron payload 开头固定单行）：
```bash
bash ~/.openclaw/workspace/scripts/quota-guard.sh <jobId> 2
```

**退出码**：
- `exit 0` → 继续后续步骤
- `exit 100` → 跳过本 run（节约 4-6M tokens）

**覆盖 cron**（5 个）：
- 4 早报：AI新闻 878d492b / 经济财经 27e08237 / Web3 28270175 / AI副业 abd75bdf
- 1 健康检查：850cf6e9

**state 重置**：单次成功自动重置 consecutiveErrors 计数器

**记忆来源**：2026-07-06 11:37 师父飞书批准 `om_x100b6b8661b548acb17fe56a5dd9f83`

---

## 🛠️ cron payload 精简模板（外移后标准格式）

```bash
# Step 0: quota-guard（固定单行）
bash ~/.openclaw/workspace/scripts/quota-guard.sh <JOB_ID> 2

# Step 1: 任务执行指令
使用 morning-report skill 生成 <CRON_NAME>。
目标路径：~/.openclaw/workspace/github/text-matrix/content/posts/news/<FILE_NAME>.
时间窗口：昨天08:00到今天08:00。

# Step 2: 采集源（任务相关）
Chrome CDP 采集 <SOURCE_LIST>，逐条打开原文验证。

# Step 3: 铁律检查（外部引用）
⚠️ 铁律铁门：详见 skills/morning-report/references/iron-laws.md
   - 6-9 隐私铁律 + 6-10 自动 push + 6-19 Web3 去重（如适用） + 6-30 pre-commit（仓库级已激活）

# Step 4: push（best-effort，2026-08-02 方向1；正文投递归 reconcile，不在此发）
1. bash scripts/morning-news-verify.sh <目标文件绝对路径>，exit 0 才继续
2. exit 0 → git push origin main（best-effort，失败告警不挂任务）
3. git push 后核对 gh run list --limit 1（失败仅告警）
4. exit ≠ 0 → 飞书告警 → 不 push

# Step 5: agent 最终回复 = 简短汇报（供框架 post-delivery 作完成信号；正文由 reconcile cron 投，agent 不自投递防重复）
```

---

## 📊 外移效果

| 维度 | 外移前 | 外移后 | 节约 |
|------|-------|-------|------|
| 4 早报 cron payload 总字符 | 5099 | ~2480 | **-2619 chars (-51%)** |
| 周均 input token 节约 | — | — | ~150-300K tokens |

**记忆来源**：2026-07-09 16:35-17:35 师父飞书批准铁律外移（`om_x100b6bc2e9c568a0b4cd454ede2c417`），备案 `state/cron-backups/iron-law-externalization-20260709-1731/`