---
name: headline-cross-publisher
description: |
  早报跨平台发布工具。把 text-matrix 早报自动填到今日头条微头条草稿箱（自动选"引用AI"声明、自动存草稿），供人工最后点"发布"。
  触发词:"发早报到头条""同步到头条""跨平台发布""publish-toutiao""cross-publisher"。
  依赖:chrome-cdp 技能（端口 9224 已接管用户已登录 Chrome）、ProseMirror 编辑器协议适配、6-12 跨平台铁律。
metadata:
   version: 1.0.0
   tags: ["cross-publisher", "toutiao", "morning-news", "weibo", "headline"]
   dependencies: ["chrome-cdp"]
---

# 早报跨平台发布 Skill

## 核心目标

把 text-matrix 推送的 4 份早报，**自动填到**今日头条微头条草稿箱（自动选"引用AI"声明 + 自动存草稿），**人工最后点"发布"**。

## 工具栈

| 步骤 | 工具 | 角色 |
|------|------|------|
| 抓早报 | text-matrix git/RSS | 读 |
| 解析 frontmatter | bash + grep | 处理 |
| 接管 Chrome | chrome-cdp 技能（cdp.mjs）| 接管已登录 Chrome |
| 导航 | cdp.mjs nav | 跳转到微头条发文页 |
| 填正文 | cdp.mjs click + type | 填到 ProseMirror 编辑器 |
| 选声明 | cdp.mjs eval + click | 勾选"引用AI" |
| 存草稿 | cdp.mjs click | 点 byte-btn-default |

## 关键配置

### Chrome 9224 启动

```bash
# 一次性：kill 所有 Chrome，复制 Profile 2 登录态到 debug profile
bash ~/.openclaw/workspace/start-chrome-debug.sh
```

### 脚本入口

```bash
# 单篇
bash ~/.openclaw/workspace/scripts/cross-publisher/publish-toutiao.sh \
  ~/.openclaw/workspace/github/text-matrix/content/posts/news/web3-morning-news-2026-06-11.md

# 4 份批量
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

### 3. ProseMirror 编辑器适配

- 用 `cdp.mjs type` 不能直接输入到 ProseMirror
- **必须先 `cdp.mjs click '.ProseMirror'` 聚焦**
- 然后 `cdp.mjs eval 'document.execCommand("selectAll"); document.execCommand("delete");'`
- 再 `cdp.mjs type` 输入内容

### 4. 微头条 vs 文章页

- **微头条** `weitoutiao/publish`：2 个 contenteditable + 9 个 input，**好填**
- **文章页** `article/publish`：React lazy load 没完成，**主区域空白**，暂未适配

### 5. 头条 AI 发文助手

- 填完内容立即返回"检测成功，暂无建议"——**无违规警告**
- 发布按钮未被禁用——**可发布**
- 存草稿按钮 class=`byte-btn-default`，发布按钮 class=`byte-btn-primary`

## 6-12 跨平台铁律

详见 USER.md/TOOLS.md/HEARTBEAT.md 三备份。核心 4 条：

1. **不替师父点"发布"**——头条是主账号，必须人工最后点
2. **自动选"引用AI"声明**——早报是 AI 整理的，合规必要
3. **草稿存完不通知 AI**——除非发布成功才发飞书
4. **Chrome 9224 进程不杀**——debug Chrome 持续运行供多次发布用

## 异常处理

| 情况 | 处理 |
|------|------|
| Chrome 9224 不在线 | 提示跑 `start-chrome-debug.sh` |
| ProseMirror 未找到 | 重试 click，3 次失败则 abort |
| type 字符数 < 50 | abort 并截图 |
| 头条检测有违规警告 | 不存草稿，飞书告警师父 |
| 草稿箱被屏蔽/异常 | 飞书告警，不影响 text-matrix 主 push |

## 微博端（规划中）

weibo-crowd 技能（已装）支持 10 条/天发帖限制。微头条体验跑通后，下一步适配：

```bash
# 一次性配 weibo-crowd 凭证
node ~/.openclaw/extensions/weibo-openclaw-plugin/skills/weibo-crowd/scripts/weibo-crowd.js login

# 发微博（必须在超话）
node ~/.openclaw/extensions/weibo-openclaw-plugin/skills/weibo-crowd/scripts/weibo-crowd.js post \
  --topic="AI早报" --status="..." --model="minimax"
```

注：微博发帖必须用 `weibo-crowd`（已装 CLI），不能直接用 `chrome-cdp` 操作微博发文（反爬更强）。

## 验证清单

- [x] Chrome 9224 接管用户已登录 Chrome
- [x] 头条微头条 ProseMirror 编辑器聚焦 + 输入
- [x] "引用AI"声明自动勾选
- [x] 头条 AI 发文助手检测"暂无建议"
- [x] 草稿成功存入头条草稿箱
- [x] 人工点"发布"成功
- [ ] 微博端 4 份早报自动发帖（待师父批准 weibo-crowd 凭证配置）
- [ ] GitHub Actions 监听 content/posts/news push 自动触发

## 未来优化

- 适配头条文章页（`article/publish`，需等 React lazy load）
- 加封面图自动上传（头条必填）
- 加话题标签自动选择（4 份早报每天 2-3 个固定话题）
- 微博端 weibo-crowd 凭证 + 超话选择
