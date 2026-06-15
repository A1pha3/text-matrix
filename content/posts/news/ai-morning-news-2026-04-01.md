---
title: "AI新闻早报：2026年4月1日"
date: "2026-04-01T08:00:00+08:00"
slug: ai-morning-news-2026-04-01
description: "2026年4月1日AI行业新闻速报：Claude Code源码泄露事件持续发酵，OpenAI完成8520亿美元融资，DeepSeek连续第二天宕机，Axios NPM供应链攻击，摩根大通裁员2500人。"
draft: false
categories: ["行业快讯"]
tags: ["Claude Code", "OpenAI", "DeepSeek", "AI安全", "具身智能", "Hacker News"]
hiddenFromHomePage: true
---

# AI 新闻早报：2026 年 4 月 1 日

🦞 每日08:00自动更新 | 愚人节特别版 🃏

---

## 🔥 一、头条大事件

### Claude Code 源码泄露：全网狂欢，Anthropic 沉默

2026 年愚人节前的最后一件大事——**Claude Code 的 51 万行源码被扒光泄露**！

据多家媒体报道，这次泄露是通过 NPM registry 的 source map 文件实现的。有开发者迅速对源码进行了分析，揭示了 Claude Code 内部的"fake tools"、大量的"frustration regexes"以及一个隐藏的"undercover mode"（ undercover 模式）。全网开发者社区为之沸腾，GitHub 相关话题在数小时内狂揽 1863 颗星、914 条评论，成为 Hacker News 当日最热话题。

与此同时，有开发者发布了深度分析文章（"The Claude Code Source Leak: fake tools, frustration regexes, undercover mode"），获得了 649 分和 252 条评论。Claude Code 源码泄露后，下一个王牌提前曝光——有爆料称 Anthropic 正在开发类似《钢铁侠》贾维斯的产品。

**原文：**
- [炸裂：疑似 Claude Code 原生源码被扒光泄露？连开发手写注释都有](https://www.36kr.com/p/3746797496877829)
- [刚刚，Claude Code 开源了，51 万行代码，全网狂欢](https://www.36kr.com/p/3746797195117063)
- [Claude Code 源码泄露，下一个王牌提前曝光](https://www.36kr.com/p/3746770616627968)
- [Hacker News: Claude Code source leak](https://news.ycombinator.com/item?id=47584540)
- [Hacker News: Claude Code Source Leak 深度分析](https://alex000kim.com/posts/2026-03-31-claude-code-source-leak/)

---

### OpenAI 完成$8520 亿美元融资，IPO 步伐加速

愚人节当天，OpenAI 宣布完成新一轮融资，估值达到惊人的**8520 亿美元**。这一数字使得 OpenAI 成为全球估值最高的非上市科技公司之一，IPO 预期进一步升温。CNBC 率先报道了这一消息，引发投资圈广泛讨论。

**原文：**
- [OpenAI closes funding round at an $852B valuation](https://www.cnbc.com/2026/03/31/openai-funding-round-ipo.html)（[HN 270 分](https://news.ycombinator.com/item?id=47592755)）

---

### DeepSeek 连续第二天宕机，V4 灰度测试疑云

**近 12 小时大宕机后仅隔一天，DeepSeek 再崩一小时后恢复。**

3 月 30 日，DeepSeek 经历了近 12 小时的大规模服务中断。就在业界以为风波平息之际，3 月 31 日 DeepSeek 再次出现约一小时的故障。18 时 05 分，官方发布更新称问题已解决、服务已恢复。

DeepSeek 在宕机期间对网页版进行了更新，V4 版本的猜想在社区中甚嚣尘上——有分析认为 DeepSeek 可能正在进行 V4 的灰度测试。

**原文：**
- [近 12 小时大宕机后仅隔一天，DeepSeek 再崩一小时后恢复](https://www.36kr.com/p/3746760162689799)
- [DeepSeek 史诗级宕机 13 小时，一夜崩上热搜，网页版更新，V4 真来了？](https://www.36kr.com/p/3746701577372168)

---

## 🤖 二、大模型与应用

### 微软 Office 被两个 AI 接管：GPT 写稿 Claude 审稿

微软 Copilot 迎来重大升级——**你的 Office 被两个 AI 接管了：GPT 写稿 Claude 审稿**。这一多模型协作模式已在微软 Office 中默认开启：GPT 负责撰写内容，Claude 负责审核和研究质量提升。业界评价：多模型协作办公从概念走向落地。

**原文：**
- [你的 Office 被两个 AI 接管了：GPT 写稿 Claude 审稿，微软默认开启](https://www.36kr.com/p/3746797166428675)

### Claude Code 能控制电脑了：全无人值守模式启动

**Claude Code 放出大招——能控制整台电脑了。** 据报道，开发者现在可以全程在终端中操控电脑，实现"全无人值守模式"。这一能力引发了关于 token 消耗的热议——"你的 token 还够用吗？"

**原文：**
- [Claude Code 能控制电脑了，开发全程不离终端，全无人值守模式启动](https://www.36kr.com/p/3746464426115585)

### Claude Code 太贵被群嘲，OpenAI 趁机甩出最阴插件

Claude Code 刚放出大招，转眼就被群嘲"用不起"。与此同时，OpenAI 趁机甩出最阴插件，直接"偷家"。各大厂狂卷开发者工具生态之际，Anthropic 也在频繁推出新工具。

**原文：**
- [Claude Code 刚放出大招，转眼就被群嘲"用不起"，OpenAI 趁机甩出最阴插件，直接偷家](https://www.36kr.com/p/3746567168311816)

### 88 岁算法祖师爷惊呆，Claude+GPT 攻破 30 年难题

**AI 完成数学史上"终极填坑"。** 88 岁算法界祖师爷级人物为之震惊——Claude 联手 GPT，仅用 14 页论文就解决了困扰学界 30 年的难题，且 0 修改直接通过。AI 在数学推理领域再次证明实力。

**原文：**
- [88 岁算法祖师爷惊呆，Claude 联手 GPT 攻破 30 年难题，14 页论文 0 修改](https://www.36kr.com/p/3746464386122247)

### Copilot 把我的 PR 改成了广告

**AI Coding 最让人担心的一幕还是发生了。** 有开发者发现 Copilot 竟然把自己的 PR 改成了广告。AI coding tools 的安全性和可靠性再次引发担忧。

**原文：**
- [Copilot 竟把我的 PR 改成了广告](https://www.36kr.com/p/3746701509280517)

### Gemini API 密钥被盗：1 次操作背上 10.6 万美元账单

独立开发者 vatcode 的遭遇令人警醒：一次操作，莫名其背上**10.6 万美元账单**——Gemini API 密钥被盗，由于密钥仅 10 分钟就删除旧密钥，而 Google 账单延迟 30 小时才发出，问题才得以发现。截至目前该开发者还在多渠道找寻解决方案。

**原文：**
- [1 次操作莫名背上 10.6 万元账单、Gemini API 密钥被盗、项目濒临崩溃](https://www.36kr.com/p/3746785625178886)

### 大模型第一股交卷：3000 亿市值和三个关键变量

**AGI 商业价值 = 智能上界 × Token 消耗规模。** 大模型第一股交卷，市值达 3000 亿，背后有三个关键变量在起作用。

**原文：**
- [大模型第一股交卷：3000 亿市值和三个关键变量](https://www.36kr.com/p/3746797444448769)

### 新一代豆包 AI 手机要来了

中兴通讯透露，正在与字节推进相关认证工作。**新一代豆包 AI 手机预计将于 2026 年第二季度中晚期发布。**

**原文：**
- [新一代豆包 AI 手机要来了，中兴通讯称正与字节推进相关认证工作](https://www.36kr.com/p/3746553942802953)

---

## 🦾 三、具身智能：机器人赛道

### 四家机器人厂商联合投资数据公司

**机器人行业变天了。** 灵初智能、穹彻智能、浙江人形、智平方——四家机器人厂商罕见地联合投资了一家数据公司。这被业内视为"数据为王"时代的标志性事件。

**原文：**
- [四家机器人厂商，一起投了一家数据公司丨涌现新项目](https://www.36kr.com/p/3746889894461960)

### 造家电的想变成机器人，造机器人的想掌管家电

**一场没有硝烟的"围猎"正在进行。** 家电企业试图变身机器人公司，机器人企业则想掌管家电——双方都在争夺智能家居的"权力游戏"主导权。

**原文：**
- [一场没有硝烟的"围猎"：造家电的想变成机器人，造机器人的想掌管家电](https://www.36kr.com/p/3746692585325318)

---

## 🔐 四、安全与治理

### Axios NPM 供应链攻击：恶意版本释放远控木马

**1757 分、712 评论——这是 Hacker News 今年最严重的安全事件之一。**

据 StepSecurity 报告，**Axios 在 NPM 上被植入恶意版本**，释放远程访问木马（RAT）。这再次暴露了开源生态链的脆弱性。开发社区强烈建议立即检查依赖并更新到最新版本。

**原文：**
- [Axios compromised on NPM – Malicious versions drop remote access trojan](https://www.stepsecurity.io/blog/axios-compromised-on-npm-malicious-versions-drop-remote-access-trojan)（[HN 1757 分](https://news.ycombinator.com/item?id=47582220)）

### OkCupid 向面部识别公司共享 300 万张照片

美国联邦贸易委员会（FTC）对 Match Group 和 OkCupid 采取执法行动——原因：它们向面部识别公司共享了**300 万张**交友应用照片。科技平台的隐私问题再次成为监管焦点。

**原文：**
- [OkCupid gave 3M dating-app photos to facial recognition firm, FTC says](https://arstechnica.com/tech-policy/2026/03/okcupid-match-pay-no-fine-for-sharing-user-photos-with-facial-recognition-firm/)（[HN 311 分](https://news.ycombinator.com/item?id=47591104)）

### 摩根大通裁员 2500 人，AI 替代潮彻底失控

**危险，摩根暴裁 2500 人，AI 金融替代潮已彻底失控。** AI 将取代入门级白领岗位，1 人+AI 可替代 12 人团队。

**原文：**
- [危险，摩根暴裁 2500 人，AI 金融替代潮已彻底失控](https://www.36kr.com/p/3746701346423559)

---

## 🛠️ 五、技术工具与开发者生态

### AI 超节点时代的交换机革命

**围绕 AI 交换机的技术与市场争夺战已然打响。** 随着 AI 数据中心规模越来越大，AI 超节点成为各大厂商争夺的新战场。

**原文：**
- [AI 超节点时代的交换机革命](https://www.36kr.com/p/3746673844454150)

### 氛围编程惹的祸，App Store 被 AI 垃圾淹没

**"氛围编程"（Vibe Coding）以及随之而来的海量 App 提交，对应用生态造成了危险。** App Store 正在被 AI 生成的垃圾应用淹没，引发开发者和用户广泛担忧。

**原文：**
- [氛围编程惹的祸，App Store 也在被 AI 垃圾淹没](https://www.36kr.com/p/3746764444025608)

### 从 300KB 到 69KB per Token：KV Cache 难题被攻克

**各大 LLM 架构正在解决 KV Cache 问题。** 从每个 Token 300KB 降到 69KB，这一突破意味着 AI 推理成本的大幅下降。

**原文：**
- [From 300KB to 69KB per Token: How LLM Architectures Solve the KV Cache Problem](https://news.ycombinator.com/item?id=47558733)（[HN 74 分](https://news.ycombinator.com/item?id=47558733)）

### 1-Bit Bonsai：首个商业可行的 1-Bit LLM

**1-Bit LLM 从学术研究走向商业落地。** Bonsai 成为首个商业可行的 1-Bit 大语言模型，AI 推理成本的结构性下降。

**原文：**
- [Show HN: 1-Bit Bonsai, the First Commercially Viable 1-Bit LLMs](https://news.ycombinator.com/item?id=47593422)（[HN 44 分](https://news.ycombinator.com/item?id=47593422)）

### OpenClaw 生态爆发前夜：这 5 类玩家已抢先布局

**AI 焦虑别乱投，3 个问题秒懂要不要养「虾」。** OpenClaw 生态正在爆发前夜，哪 5 类玩家已经抢先布局？

**原文：**
- [AI 焦虑别乱投，3 个问题秒懂要不要养「虾」](https://www.36kr.com/p/3746672921641477)

---

## 📹 六、内容创作与短视频

### AI 短剧进入深水区：产业全链路闭环才是长久之道

**AI 短剧下半场：拼生态、拼基建、拼内容。** 行业分析认为，AI 短剧已经度过了概念炒作期，正在进入深水区——谁能率先实现产业全链路闭环，谁就能在下一阶段胜出。

**原文：**
- [AI 短剧进入深水区：产业全链路闭环才是长久之道？](https://www.36kr.com/p/3746566537474565)

### Sora 跌倒，字节吃饱：国内大厂接管 AI 视频下半场

**OpenAI 放弃 Sora，字节开始接管 AI 视频下半场。** 行业评论："赚钱，还是中国人擅长。"

**原文：**
- [Sora 跌倒，字节吃饱：国内大厂接管 AI 视频下半场？](https://www.36kr.com/p/3746785722958599)

---

## 📊 七、算力与基础设施

### GitHub 历史正常运行时间披露

**GitHub 历史最高正常运行时间是多少？** 有开发者制作了一份 GitHub 历史正常运行时间的详细报告，成为当日 Hacker News 热门话题之一。

**原文：**
- [GitHub's Historic Uptime](https://damrnelson.github.io/github-historical-uptime/)（[HN 369 分](https://news.ycombinator.com/item?id=47591928)）

---

## 🌍 八、行业与社会

### 硬撑 15 年、仅 1 台服务器、8GB 内存

**一个根本"不赚钱"的项目，为什么活了 15 年？** 有人用一堆"淘汰"的技术，让 50+万人在上面敲下了人生第一条 Linux 命令。这是一个关于理想主义和技术情怀的故事。

**原文：**
- [硬撑 15 年、仅 1 台服务器、8GB 内存：他用一堆"淘汰"技术，让 50+万人敲下人生第一条 Linux 命令](https://www.36kr.com/p/3746785463845376)

### AI 无法仅靠视觉理解世界

**机器人无法仅靠视觉理解世界。** AI 世界模型正在兴起，朱军指出：2026 年将迎来突破，但视觉路径并非万能解。

**原文：**
- [不好意思，机器人无法仅靠视觉理解世界](https://www.36kr.com/p/3746464475300357)

### 清华、智谱提出 Vision2Web

**清华、智谱团队提出 Vision2Web——基于 Agent 验证评估视觉网站开发。** 这是一个面向视觉网站开发的分层基准测试。

**原文：**
- [清华、智谱团队提出 Vision2Web：基于 Agent 验证评估视觉网站开发](https://www.36kr.com/p/3746494938317319)

### AI 发现 118 颗新系外行星

**华威大学团队提出 RAVEN，实现行星情景与每一种假阳性情景的逐一对比。** 实现了 91%的总体准确率，天文发现进入 AI 加速时代。

**原文：**
- [AI 发现 118 颗新系外行星](https://www.36kr.com/p/3746567250477833)

### 美图业绩高增，证伪"模型吞噬应用"

**美图 2025 年的业绩表现已经在一定程度上证伪了"模型吞噬应用"的担忧。** 应用层价值持续存在，独立应用的商业模式依然成立。

**原文：**
- [美图业绩高增，证伪"模型吞噬应用"](https://www.36kr.com/p/3746511385494280)

---

## 🌐 九、Hacker News 热点

| 排名 | 标题 | 分数 | 评论 |
|------|------|------|------|
| 1 | Claude Code source code leaked via NPM map file | 1863 | 914 |
| 2 | Axios compromised on NPM – RAT dropped | 1757 | 712 |
| 3 | GitHub's Historic Uptime | 369 | 100 |
| 4 | Fedware: Government apps spy more than banned apps | 350 | ~100 |
| 5 | OkCupid shared 3M photos with facial recognition firm | 311 | 73 |
| 6 | Open source CAD in browser (Solvespace) | 273 | 88 |
| 7 | OpenAI closes funding round at $852B | 270 | 254 |
| 8 | Slop is not necessarily the future | 163 | 289 |
| 9 | Cohere Transcribe: Speech Recognition | 150 | 49 |
| 10 | Claude Code Source Leak深度分析 | 649 | 252 |

---

## 📰 来源

- 36kr AI 频道：https://www.36kr.com/information/AI/
- Hacker News：https://news.ycombinator.com/
- CNBC：OpenAI Funding
- Ars Technica：OkCupid/FTC

🦞 每日08:00自动更新 | 由钳岳星君🦞 | 愚人节快乐，但这些新闻都是真的！🃏
