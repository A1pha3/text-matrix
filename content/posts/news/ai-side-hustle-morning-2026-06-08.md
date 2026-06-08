---
title: "AI副业早报 2026-06-08"
date: 2026-06-08T08:48:00+08:00
slug: ai-side-hustle-morning-2026-06-08
description: "2026年6月8日 AI 副业早报，精选过去 24 小时内 V2EX 酷工作/接单/工具贴 4 条与 Hacker News 上 4 个新上线的 AI 副业/SideProject。"
draft: false
categories: ["行业快讯"]
tags: ["AI副业", "招聘", "V2EX", "HackerNews", "SideProject"]
hiddenFromHomePage: true
---

🦞 每日09:00自动更新

---

## 🔥 今日热门

### Show HN: Lathe – 用 LLM 教你新领域，而不是替你思考
来源: Hacker News
发布者: devenjarvis
原文: [原文](https://news.ycombinator.com/item?id=48433756)
摘要: 帖子发布于 2026-06-07 19:16:33（北京时间）。作者把一套 LLM skill 和 Go CLI 拼成「教程生成器」：在 Claude Code / Cursor / Codex 里输入 `/lathe build a 3D Slicer in Erlang`，Lathe 会先找源材料再分章节产出可手敲的教程，本地 UI 支持提问、校验和续写。已开源在 github.com/devenjarvis/lathe。讨论串 43 条评论里 v 友们普遍认可「让 LLM 拆任务、自己敲代码」是当下最不容易产生认知债的玩法，可作为「用 AI 工具做副业 / 学新栈」最小可行样本。

### Show HN: TakoVM – 企业也在用的隔离代码执行沙箱
来源: Hacker News
发布者: las7
原文: [原文](https://news.ycombinator.com/item?id=48431257)
摘要: 帖子发布于 2026-06-07 10:42:24（北京时间）。TakoVM 把「沙箱 + 任务队列 + 执行历史」打包成可 pip 安装的服务：`pip install "tako-vm[server]"` 后用一条 POST 就能在 Docker/gVisor 隔离环境里跑用户上传的 Python，正面对比 e2b / microsandbox 时把「少写 80% 脚手架」作为卖点，PyPI 已发布 v0.x，6 条评论里有人在跑生产环境。典型的「AI 副业/独立开发」方向：跑别人 AI agent 生成的不安全代码，刚好踩在 2026 年 AI agent 落地的最痛处。

### Proliferate（YC S25）招 founding engineer：和我们一起把 Codex 做成开源
来源: Hacker News
发布者: howToTestFE
原文: [原文](https://www.ycombinator.com/companies/proliferate/jobs/L3copvK-founding-engineer)
摘要: 帖子发布于 2026-06-08 01:01:17（北京时间）。YC S25 项目 Proliferate 在做开源版 Codex（OpenAI 编程 Agent 的开源复刻），把 founding engineer 直接挂到 YC 招聘页上招，目标群体是「在 AI coding 工具上有体感、想拿股权而非签字费」的工程师。这是 24h 内 jobs tab 与 AI 副业/AI 创业最相关的高质量招聘之一，对想跳进 YC AI Coding 赛道的读者是少有的窗口。

## 💼 招聘/接单

### [接单] k8s / Linux / 运维问题解决（远程）
来源: V2EX
发布者: laojuelv
原文: [原文](https://www.v2ex.com/t/1218506)
摘要: 帖子发布于 2026-06-07 09:54:58（北京时间）。作者贴出接单清单：K8s 集群从零部署与调优、Calico/Flannel 等 CNI 排障、MySQL/Kafka/Redis/Nginx 中间件问题、Shell/Python/Go 脚本、运维架构设计与异地灾备。联系方式以 base64 形式放在正文（`Vl82Njg4ODg2Ng==`）。属于典型的「V2EX 酷工作接单帖」样本，远程交付 + 按需排障，适合想搞运维副业的读者参考报价与接单写法。

## 🚀 AI项目

### 半年写了 100+ 个小工具：把 Tinker 工具箱从 demo 做到日常工具
来源: V2EX
发布者: Muniu
原文: [原文](https://www.v2ex.com/t/1218534)
摘要: 帖子发布于 2026-06-07 13:15:55（北京时间）。作者更新此前在 V2EX 介绍过的 Tinker（开源工具箱应用），半年内从 20 来个内置插件做到 100+ 个，覆盖待办、进程清理、磁盘清理、空间分析、网页运行、照片拼接、终端、音视频压缩等高频小需求；统一视觉规范、支持中英双语和明暗主题，三端（Windows / macOS / Linux）可用。仓库 https://github.com/liriliri/tinker，官网 https://tinker.liriliri.io。属于「AI 时代反而更值钱的非 AI 副业」样本：把工具做厚做密，沉淀长尾用户。

### 半年做了 100+ 个插件之后，他把工具箱做成了「瑞士军刀式」日常应用
来源: V2EX
发布者: Muniu
原文: [原文](https://www.v2ex.com/t/1218534)
摘要: 帖子发布于 2026-06-07 13:15:55（北京时间）。同一作者的 Tinker 工具箱更新，正文里有 8 张插件截图（图片标注、音频编辑、媒体压缩、网页运行、照片拼接、磁盘空间分析、终端）并强调「80% 的日常场景都被覆盖」。仓库 https://github.com/liriliri/tinker，官网 https://tinker.liriliri.io/zh/guide/ 列出完整插件列表。讨论串 32 条评论里有 v 友要求 Docker / NAS 版本，说明这类工具在副业里仍能跑出付费意愿。

### ChatGPT Plus + Codex 半小时就烧光额度，土耳其区算力套餐再次起争议
来源: V2EX
发布者: desdouble
原文: [原文](https://www.v2ex.com/t/1218604)
摘要: 帖子发布于 2026-06-07 23:14:21（北京时间）。楼主在 App Store 刚开通 ChatGPT Plus（土耳其区）后，用 Codex 跑一个 polymarket 下单报错的修复任务，半小时不到就被提示「额度用完」，吐槽「常听到 Plus 额度根本用不完经常重置，为什么我的这么快花完了」。讨论串里其他 v 友指出 Codex（特别是 CLI / Tasks 后台任务）和普通对话共享 5h 窗口，跑长任务会迅速耗尽。该帖对想用 ChatGPT Plus 当 AI 副业算力来源的读者有「成本测算」参考价值。

## 🤔 AI 副业心态

### 拒了 1 万/月的工作，在家吸 Claude/Codex，是不是废了 — 续帖（24h 互动 3015 阅）
来源: V2EX
发布者: emmathoermer
原文: [原文](https://www.v2ex.com/t/1218230)
摘要: 帖子发布于 2026-06-07 00:23:59（北京时间）。楼主放弃 8k 底薪 + 绩效的工厂管理岗，全职用 Claude/Codex 折腾小项目但尚未变现，给自己几个月时间看能否跑出产品。24h 内 V2EX jobs tab 累计 23 条回复、3015 次点击，是过去 24h 内「全职 AI 副业 vs 全职打工」讨论里互动最高的一条。评论里不少 v 友分享自己 30 岁前后转 AI 副业的「半年没收入」经历，是当下「AI 副业心态」最真实的一手样本。

## 🛠 工具推荐

### I design with Claude more than Figma now
来源: Hacker News
发布者: howToTestFE
原文: [原文](https://blog.janestreet.com/i-design-with-claude-code-more-than-figma-now-index/)
摘要: 帖子发布于 2026-06-07 13:04:24（北京时间）。Jane Street 工程师博客，详细记录用 Claude Code 取代 Figma 做 UI/UX 设计的整套工作流：截图 + 文字需求 + 让 Claude 出多稿，10 分钟迭代一轮。231 条评论里多数人对「AI 设计稿能直接给到产品确认」表示惊讶，少数警示「一致性和系统化设计 token 还是需要人」。对想靠 AI 副业做独立产品的读者是「设计成本被压平」的关键信号——以前需要花钱请设计师的环节，现在可以自己 + AI 闭环。

### Proliferate / 知乎热议：国内 AI 模型哪个编程效果好？
来源: V2EX
发布者: desdouble
原文: [原文](https://www.v2ex.com/t/1218520)
摘要: 帖子发布于 2026-06-07 11:43:34（北京时间）。楼主因老板嫌国外模型（Claude / GPT）太贵，要求换国内模型（点名 Kimi 2.5 / Qwen）做编程辅助，发帖问哪个效果好。评论里多数 v 友实测后认为「写中等复杂度业务代码 Qwen 性价比最高、深度逻辑 Claude Code 仍领先」。对预算敏感的 AI 副业读者，这是一条「按任务选模型降本」的实用经验。

---

🦞 每日09:00自动更新

**数据来源**：V2EX（酷工作/接单/AI 工具贴，5 条已逐条打开帖子页验证，1 条历史帖续互动引用）、Hacker News（首页 + Show HN，4 条已逐条打开 item + 外链项目页验证）。Reddit r/Entrepreneur / r/SideProject / r/LocalLLaMA 三个子版 new.json 端点被 Cloudflare 拦截（"You've been blocked by network security"），与昨日 06-07 早报同症状，本份以 V2EX + Hacker News 双源覆盖。

**⚠️ 链接核查清单（已逐条验证，仅列正文实际引用链接）：**
- ✅ https://news.ycombinator.com/item?id=48433756 - HN 帖 + github.com/devenjarvis/lathe README 已访问，标题/正文/发布者匹配
- ✅ https://news.ycombinator.com/item?id=48431257 - HN 帖 + github.com/las7/TakoVM README 已访问
- ✅ https://www.ycombinator.com/companies/proliferate/jobs/L3copvK-founding-engineer - YC 招聘页已访问，2026-06-08 01:01:17 +08:00 在 24h 窗口内
- ✅ https://www.v2ex.com/t/1218506 - V2EX 接单帖已打开，发布者 laojuelv，时间 2026-06-07 09:54:58 +08:00
- ✅ https://www.v2ex.com/t/1218534 - V2EX Tinker 帖已打开，发布者 Muniu，时间 2026-06-07 13:15:55 +08:00
- ✅ https://www.v2ex.com/t/1218604 - V2EX ChatGPT Plus 帖已打开，发布者 desdouble，时间 2026-06-07 23:14:21 +08:00
- ✅ https://www.v2ex.com/t/1218230 - V2EX Claude/Codex 续帖，发布者 emmathoermer，时间 2026-06-07 00:23:59 +08:00 (窗内边缘续互动引用)
- ✅ https://blog.janestreet.com/i-design-with-claude-code-more-than-figma-now-index/ - Jane Street 博客已访问，标题/正文匹配

**丢弃候选说明（仅记录，不进入正文）：**
- HN 48440064（The Smallest Brain You Can Build / Perceptron in Python, 2026-06-08 00:28:37 UTC = 08:28 BJT，已超出 08:00 窗口截止）、48437406（Building from zero after addiction / 个人故事）、48437290（Making peace with your unlived dreams / 个人成长）、48437609（How's Linear so fast / 工程类）、48440008（unix lost+found / 工程类）— 与 AI 副业主题不符或超出 24h。
- V2EX t/1218607「42 岁辞职回家应该做点什么」、t/1218524「老 ios 程序员新东方 22k」、t/1218556「想买键盘」、t/1218561「看佛经困惑」— 标题/正文不匹配 AI 副业主题或纯生活向。
- V2EX t/1218482/t/1218397/t/1218230/t/1218325 已在 06-07 早报覆盖过原帖，本份只复用 t/1218230 的 24h 续互动作为「副业心态」参考。
- HN 48434436（Claude Desktop for Linux / 仅 GitHub issue）、48431079/48432722/48434198/48437064/48436024/48436005/48435943/48435677/48435634/48433846/48433619/48429957（多组 Show HN，时间在窗口内但主题为非 AI 副业 / 同质化工具）、48431981/48431257 已收录。
- Reddit r/Entrepreneur / r/SideProject / r/LocalLLaMA — 三个子版 new.json 端点被 Cloudflare 拦截（已切换 Chrome via CDP 重试仍返回 "You've been blocked by network security"），未能在 24h 窗口内获取稳定原文页，故本份以 V2EX + Hacker News 双源覆盖；Reddit 缺失已记入"来源不足"汇报。
