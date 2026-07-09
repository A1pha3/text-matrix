# 跨平台发布铁律铁门（headline-cross-publisher）

**最后更新**：2026-07-09 17:35 GMT+8（铁律外移）
**适用范围**：cron 0551c89f 早报跨平台发布
**目的**：从 cron payload 中外移 6-21 + 6-22 落地清单，节约 ~12% input token

---

## ⚠️ 6-12 自动点发布铁律（永久）

> **AI 自动点"发布/发送"——头条 byte-btn-primary + 微博"发送" 按钮变 enabled 时 AI 自动点击。**

**不变项**（2026-06-12 00:34 师父裁决 + 2026-06-14 12:00 补 2 条）：
1. **AI 自动点"发布/发送"**——头条 byte-btn-primary + 微博"发送" 按钮变 enabled 时 AI 自动点
2. **自动勾选"引用AI"声明**（头条）——早报是 AI 整理的，合规必要
3. **发布成功后飞书通知师父**——用 message 工具发飞书，含 commit / 链接 / 发布时间
4. **Chrome 9224 进程不杀**——debug Chrome 持续运行
5. **头条发布取消勾选"头条首发"**（2026-06-14 12:00 师父拍板补）——publish-toutiao.sh step 12.5 已实现
6. **失败也必须飞书告警**（2026-06-14 12:00 师父拍板补）——publish-all.sh 末尾+每份失败 飞书通知，**不静默**

**记忆来源**：2026-06-12 00:34 师父裁决 "我要改成，徒儿你帮我点发布..."

---

## ⚠️ 6-14 第七条铁律（架构变更审批）

> **架构级变更（改动 > 10 行 / 改 publish-all.sh / 影响多份早报）必须先呈报主 session 等师父批准后才能动手。**

**触发场景**：2026-06-14 13/14 号补发 0 进度根因 + 3 个隐藏 bug

**子代理判断为 "可改 bug" 的条件**：
- 不修 = 任务 0 进度（发布失败、head/grep 0 匹配退出）
- 修 = 1-3 行小改动，不涉及架构/逻辑大改
- 修完能立刻验证（bash -n syntax + 1 份试水）

**子代理判断为 "必须先问主 session" 的条件**：
- 改动 > 10 行
- 影响多份早报（架构级）
- 涉及锁/去重/并发逻辑
- 改 publish-all.sh（核心调度器）

**记忆来源**：2026-06-14 12:50 师父飞书裁决 `om_x100b6dd748ee2ca0b34500d8e494b13`

---

## ⚠️ 6-21 Profile 2 复制铁律（永久）

> **start-chrome-debug.sh 必须复制 Profile 2 登录态，否则 Chrome 9224 重启后无登录态。**

**6-21 漏发根因**：
- start-chrome-debug.sh L34-L36 只复制 `Default + Profile 1`，不复制 Profile 2
- 但师父真实微博/头条登录态在 Profile 2 目录下
- 每次启动 Chrome debug 都是"光 Chrome 无登录态"

**修复**（已落地）：
- ✅ `start-chrome-debug.sh` L34 已补 `cp -R "$DEFAULT_USER_DATA_DIR/Profile 2"`

**记忆来源**：2026-06-21 11:53 师父飞书 message `om_x100b6c424d08cca0b2f6b55e889f9f3` 质问 "为什么早报没有推送到微博"

---

## ⚠️ 6-22 Chrome 稳定性 flags（永久）

> **start-chrome-debug.sh 加 Chrome 稳定性 flags，防止长时间运行 Chrome 自动 update 清空 tab。**

**flags**：
- `--disable-gpu`
- `--disable-dev-shm-usage`

**6-22 漏发根因**：
- Chrome 9224 进程在线但所有微博/头条 tab 被清空
- 4 个 tab 全是 `Omnibox Popup` + `chrome://newtab/`
- cron 自认为 ok → 静默失败

**修复**（已落地）：
- ✅ start-chrome-debug.sh 加 `--disable-gpu --disable-dev-shm-usage`
- ✅ cron payload 加 weibo tab 强制 open + Profile 2 登录态验证

**记忆来源**：2026-06-22 11:53 师父飞书 message `om_x100b6cbf54cc9cb4b206fa3f3265286`

---

## ⚠️ 6-22 静默失败防御（永久）

> **state 文件 < 4 必须 exit 1，即使 publish-all.sh exit 0，不允许 status=ok 静默成功。**

**实施**：
- Step 2.1: 验证 state 文件数 ≥ 4
- Step 2.2: 验证每份都 status="published"
- 任一不满足 → 主动飞书告警 + exit 1

**6-22 漏发根因**：
- cron 父任务把 isolated session summary 视为最终结果
- summary 报 "Chrome 挂" 也被算作 "ok"
- 0 state 文件 → 主 session 11:53 才知道（3h23m 盲区）

**记忆来源**：2026-06-22 11:53 + 12:59 师父飞书质询

---

## ⚠️ 6-14 Chrome tab 健康度（永久）

> **Chrome 9224 tab 数 > 50 → 自动关掉所有 tab + 重启 Chrome（start-chrome-debug.sh）。**

**触发位置**：`publish-toutiao.sh` / `publish-weibo.sh` step 0.1

**为什么是 50 不是 100**：
- 13 号 4 份全失败时 Chrome 有 85 tabs，WS 慢是隐性根因
- 50 阈值更安全（早发现早重启，避免 WS 慢导致发布失败）

**记忆来源**：2026-06-14 12:48 师父飞书 message `om_x100b6dd764c050b0b346a99dc3e9182`

---

## ⚠️ 6-19 头条战略终局（永久）

> **早报取消发布到今日头条微头条，只发微博端（每日 4 份）。**

**已落地**：
- ✅ publish-toutiao.sh 归档为 `.disabled`
- ✅ publish-all.sh L158 头条调用改为 `if false`
- ✅ 微博端保留 Chrome 9224 + Profile 2 登录态

**记忆来源**：2026-06-19 战略终局拍板

---

## ⚠️ 6-14 试水协议（重要）

> **未来任何手动/AI 跑 publish-toutiao.sh / publish-weibo.sh 前，必须先 grep state 确认未发。**

```bash
# 跑前查重
FILE_BASE="financial-morning-news-2026-06-14"
if grep -l "$FILE_BASE" ~/.openclaw/workspace/state/cross-publisher-$(date +%Y%m%d)-*.json 2>/dev/null | head -1; then
  echo "⚠️ $FILE_BASE 今日已发过，跳过"
  exit 0
fi
```

**触发背景**：2026-06-14 12:38 弟子试水 IIFE 包装时**忘查 state** → 头条号后台 2 条 financial-14 早报 → 需师父手动去头条后台删 1 条

---

## 📊 外移效果

| 维度 | 外移前 | 外移后 | 节约 |
|------|-------|-------|------|
| 跨平台 cron payload 总字符 | 5878 | ~5000 | **-878 chars (-15%)** |
| 周均 input token 节约 | — | — | ~50-100K tokens |

**记忆来源**：2026-07-09 16:35-17:35 师父飞书批准铁律外移 `om_x100b6bc2e9c568a0b4cd454ede2c417`