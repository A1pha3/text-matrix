---
name: headline-cross-publisher
description: |
  早报跨平台自动发布工具。把 text-matrix 早报自动填到今日头条微头条 + 微博发微博弹窗，**AI 自动点发布按钮**，发布成功后用飞书通知师父审阅。
  触发词:"发早报到头条""同步到微博""跨平台发布""publish-toutiao""publish-weibo""cross-publisher"。
  依赖:chrome-cdp 技能（端口 9224 已接管用户已登录 Chrome）、ProseMirror + WB Textarea 适配、6-12 跨平台铁律。
metadata:
   version: 1.2.0
   tags: ["cross-publisher", "toutiao", "weibo", "morning-news", "headline", "auto-publish"]
   dependencies: ["chrome-cdp"]
---

# 早报跨平台自动发布 Skill

## 核心目标

把 text-matrix 推送的 4 份早报，**自动填 + 自动发布**到：
- 今日头条微头条（草稿存 → **AI 点发布按钮** → 飞书通知）
- 微博发微博弹窗（弹窗填入 → **AI 点发送按钮** → 飞书通知）

**两平台统一用 chrome-cdp**（不依赖 weibo-crowd、Make.com、API 申请）。

## 6-12 跨平台铁律（2026-06-12 00:34 师父裁决）

1. **AI 自动点"发布/发送"**——头条 byte-btn-primary + 微博"发送" 按钮变 enabled 时 AI 自动点
2. **自动勾选"引用AI"声明**（头条）——早报是 AI 整理的，合规必要
3. **发布成功后飞书通知师父**——用 message 工具发飞书 message（含 commit / 链接 / 发布时间 / 状态 JSON）
4. **Chrome 9224 进程不杀**——debug Chrome 持续运行供多次发布用

## 工具栈

| 步骤 | 工具 | 角色 |
|------|------|------|
| 抓早报 | text-matrix git/RSS | 读 |
| 解析 frontmatter | bash + grep | 处理 |
| 接管 Chrome | chrome-cdp 技能（cdp.mjs）| 接管已登录 Chrome |
| 头条导航 | cdp.mjs nav | 跳转到微头条发文页 |
| 头条填正文 | cdp.mjs click + type | 填到 ProseMirror 编辑器 |
| 头条选声明 | cdp.mjs eval + click | 勾选"引用AI" |
| **头条点发布** | **cdp.mjs click `button.byte-btn-primary`** | **AI 自动发布** |
| 微博 click | cdp.mjs click `button[title="发微博"]` | 触发弹窗 |
| 微博聚焦 | cdp.mjs eval | 聚焦第二个 textarea |
| 微博填正文 | cdp.mjs type | 填到弹窗 |
| **微博点发送** | **cdp.mjs eval 找 enabled 按钮 .click()** | **AI 自动发布** |
| **飞书通知** | **message 工具** | **发布成功后发飞书给师父** |

## 关键配置

### Chrome 9224 启动

```bash
# 一次性：kill 所有 Chrome，复制 Profile 2 登录态到 debug profile
bash ~/.openclaw/workspace/start-chrome-debug.sh
```

### 脚本入口

```bash
# 头条单篇（自动发布）
bash ~/.openclaw/workspace/scripts/cross-publisher/publish-toutiao.sh \
  ~/.openclaw/workspace/github/text-matrix/content/posts/news/web3-morning-news-2026-06-11.md

# 微博单篇（自动发送）
bash ~/.openclaw/workspace/scripts/cross-publisher/publish-weibo.sh \
  ~/.openclaw/workspace/github/text-matrix/content/posts/news/web3-morning-news-2026-06-11.md

# 4 份 × 2 平台批量（自动发布 + 飞书通知）
bash ~/.openclaw/workspace/scripts/cross-publisher/publish-all.sh 2026-06-11
```

## 关键发现

### 1. Chrome 149+ 限制

- 带 `--remote-debugging-port` 必须用**非默认** `--user-data-dir`
- 本 skill 用 `~/.openclaw/workspace/chrome-debug-profile/` 作为 debug user data dir
- 首次运行从 `~/Library/Application Support/Google/Chrome/Profile 2/` 复制登录态

### 2. Profile 2 不是 Default

- 用户真实登录态在 `Profile 2/`，**不在 `Default/`**
- Default 目录只有 23 字节 DevToolsActivePort（陷阱）

### 3. 头条 ProseMirror 编辑器适配

- 用 `cdp.mjs type` 不能直接输入到 ProseMirror
- **必须先 `cdp.mjs click '.ProseMirror'` 聚焦**
- 然后 `cdp.mjs eval 'document.execCommand("selectAll"); document.execCommand("delete");'`
- 再 `cdp.mjs type` 输入内容

### 4. 头条微头条 vs 文章页

- **微头条** `weitoutiao/publish`：2 个 contenteditable + 9 个 input，**好填**
- **文章页** `article/publish`：React lazy load 没完成，**主区域空白**，暂未适配

### 5. 头条发布按钮

- 存草稿按钮 class=`byte-btn-default`（之前用）
- **发布按钮 class=`byte-btn-primary`**（现在 AI 自动点这个）
- 头条 AI 发文助手实时检测"暂无建议"——合规无警告

### 6. 微博发微博弹窗

- "发微博"按钮：`<button title="发微博">` —— 用 `[title="发微博"]` 选中
- 弹窗第二个 textarea（class 含 `focus`）
- 微博"发送"按钮 class=`woo-button-main woo-button-flat woo-button-primary woo-button-m woo-button-round` —— 填了内容后变 enabled
- **微博无"引用AI"声明选项**

## 6-12 跨平台铁律（2026-06-12 00:34 师父裁决）

1. **AI 自动点"发布/发送"**——头条 byte-btn-primary + 微博"发送" 按钮变 enabled 时 AI 自动点
2. **自动勾选"引用AI"声明**（头条）——早报是 AI 整理的，合规必要
3. **发布成功后飞书通知师父**——用 message 工具发飞书 message
4. **Chrome 9224 进程不杀**——debug Chrome 持续运行供多次发布用

## 发布状态文件

发布成功后，脚本会写状态文件到：
```
~/.openclaw/workspace/state/cross-publisher-YYYYMMDD-HHMMSS.json
```
包含字段：`platform` / `status: "published"` / `title` / `url` / `publish_url_after` / `shot_draft` / `shot_final` / `published_at`

主代理扫到这个文件后用 message 工具发飞书通知。

## 异常处理

| 情况 | 处理 |
|------|------|
| Chrome 9224 不在线 | 提示跑 `start-chrome-debug.sh` |
| 头条 ProseMirror 未找到 | 重试 click，3 次失败则 abort |
| 头条 type 字符数 < 50 | abort 并截图 |
| 头条 AI 检测有违规警告 | 不点发布，飞书告警师父 |
| 头条发布按钮持续 disabled 30 秒 | 飞书告警 + 截图 |
| 微博"发微博"按钮未找到 | 重新 nav 到 weibo.com/ |
| 微博弹窗未展开 | 重试 click，3 次失败则 abort |
| 微博"发送"按钮 disabled | 检查内容是否真填入，abort |

## 验证清单

- [x] Chrome 9224 接管用户已登录 Chrome
- [x] 头条微头条 ProseMirror 编辑器聚焦 + 输入
- [x] "引用AI"声明自动勾选
- [x] 头条 AI 发文助手检测"暂无建议"
- [x] 草稿成功存入头条草稿箱
- [x] 头条 AI 自动点发布按钮
- [x] 人工点"发布"成功（2026-06-12 00:16 师父确认）
- [x] 微博"发微博"按钮 click 触发弹窗
- [x] 弹窗第二个 textarea 接受 cdp.mjs type
- [x] 微博 AI 自动点"发送"按钮（待明早首次实战验证）
- [ ] 飞书通知发布成功（待明早首次实战验证）
- [ ] GitHub Actions 监听 content/posts/news push 自动触发

## 未来优化

- 适配头条文章页（`article/publish`，需等 React lazy load）
- 加封面图自动上传（头条必填）
- 加话题标签自动选择（4 份早报每天 2-3 个固定话题）
- 微博超话发帖（10 条/天限制——如需走超话再适配）
- GitHub Actions 监听 content/posts/news push 自动触发
- 飞书通知模板（带早报标题 + 平台 + 链接 + 发布时间 + 截图链接）
