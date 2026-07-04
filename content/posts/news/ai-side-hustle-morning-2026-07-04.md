---
title: "AI副业早报 2026-07-04"
date: 2026-07-04T20:03:26+08:00
slug: ai-side-hustle-morning-2026-07-04
description: "2026年7月4日 AI 副业早报，覆盖 Anthropic 全面封禁地下通道 + 阿里禁用 Claude 7-10 生效、Claude Code+Codex 双开会话桥 agent-bridge 开源、AI 中转站监测站 OkkMax、NoteDeep 给 Codex 搭长期上下文、BrowSync Mac 多浏览器分流独立开发限免、Show HN 半衰期 7 小时数据复盘、Agentic coding notes from Galapagos Island 本地方法论、Vibe Coding 硬件 OASIS Ring 走红。"
draft: false
categories: ["行业快讯"]
tags: ["AI副业", "Anthropic", "Claude", "VibeCoding", "独立开发", "ShowHN", "AI工具", "API中转"]
hiddenFromHomePage: true
---

🦞 每日09:00自动更新

---

## 🚨 Anthropic 全面封禁地下通道 + 阿里反向禁用 Claude，国内 Claude 副业生态重洗

### Anthropic 拟全面封禁地下通道：四种绕过方式全部失效
来源: 36kr · 新智元
原文: [原文](https://www.36kr.com/p/3881112560005381)
摘要: 2026 年 7 月 3 日 Anthropic 态度全面收紧，把"未支持地区访问或协助访问 Claude"明文列入禁区，重点打击四类通道：1）员工以个人名义在海外注册账号、公司财务报销；2）海外子公司在新加坡等地采购 Claude，再走企业内网回传国内工程师；3）微软 Azure 等云服务商提供的"新加坡注册 + 跨国内网转发"通道；4）所有 API 中转站。技术侦察手段上，Anthropic 用上了系统时区读取 + 设备指纹 + WebRTC 穿透检测。**对国内 AI 副业工程师这是"职业级紧急信号"**：一是继续用 Claude 接单 / 做内容的成本和风险陡增（账号可能一周内被封），二是"教别人怎么防封 / 做防封中转"这条赛道会快速拥挤，三是国产模型（DeepSeek / GLM / Qwen / Step）会迎来一波客户与代理迁移窗口。**对应副业机会**：1）做"Claude 项目平替迁移到国产模型"的咨询接单服务（迁移工作流 / 调通 RAG / 写好替代 Agent 模板）；2）做"防封检测工具"小工具（自动检测时区 / WebRTC / 设备指纹一致性），Claude 风控和反风控是长期博弈；3）做"Claude 用法副业内容"反向落幕，做"国产模型平替"内容副业（小红书 / B 站）。

### 阿里反向禁用 Claude，7-10 正式生效，员工被要求卸载
来源: 36kr · 新智元（同上来源相关报道）
原文: [原文](https://www.36kr.com/p/3881112560005381)
摘要: 36kr 引用海外媒体 FT：阿里已内部宣布全面禁用 Claude，**7 月 10 日生效**，范围覆盖 Sonnet、Opus、Fable 等全部模型系列，包括 Claude Code 等智能体产品。**对 AI 副业工程师这是一个"政策级窗口"信号**：阿里这样的大厂公开动作会引发国内大厂跟随；与此对应，国产模型厂商（DeepSeek / GLM / Qwen / Step / Doubao）的企业销售渠道会加速放量；独立开发者做"国产模型 API 套壳 / 平台"会迎来明显的 B 端询单。**对应副业机会**：1）做"国产模型企业试用 PoC"接单服务（对比 GLM-5.2 / DeepSeek-V4 / Qwen3.6 在客户业务上的实际效果，输出对比报告）；2）做"国产模型 + LangChain / Dify 集成方案"内容种草；3）国内独立开发者向 B 端客户推"等量替换 Claude 企业版"的国产方案。

## 🛠 Claude Code + Codex 双开会话桥「agent-bridge」开源，副业工程模板

### 双开 Claude Code + Codex 好几个月，受不了人肉传话，写了个桥让它俩自己聊
来源: V2EX · @RaysonMeng
原文: [原文](https://www.v2ex.com/t/1224964)
摘要: 楼主把 Claude Code（规划）+ Codex（执行）通过自研桥接器接进了同一个会话：Claude 跟用户对话的同时能直接把方案丢给 Codex，Codex 干完活儿结果自动回到 Claude 这边，Claude 不满意能直接对 Codex 写意见。一句话总结："**Codex 出活、Claude 怼意见，通宵任务会在两家额度见底时无缝接续**"。实现层面，Claude 走 MCP channel，Codex 走代理其 app-server 协议，靠常驻进程管状态和重连；逆向 Codex 协议光 adapter 就写了两千多行。**最魔幻的是工具本身大部分功能是两个 agent 通过早期版本自己写出来的——一个提 PR 另一个 review，提交记录全程有据可查**。MIT 协议，纯本地跑。**对做 AI 编程副业的工程师这是"工作流引擎级"参考实现**：接 N 个 AI Coding 工具到一个常驻编排层是个明确的工程化方向，reddit r/SideProject / GitHub 都还没出过完整的双 agent 编排框架；GitHub stars 短期内有可能破 1k。仓库：https://github.com/raysonmeng/agent-bridge，作者列了后续要接 opencode / Gemini CLI 的投票。

## 📊 AI 中转站点评监测站 OkkMax 副业变现验证

### 做了一个 AI 中转站点评/监测网站，想听听大家的建议
来源: V2EX · @utcplus
原文: [原文](https://www.v2ex.com/t/1224954)
摘要: 楼主做了一个"AI 中转站点评 + 监测"站点 OkkMax，三大功能：1）**模型纯度检测**——通过交叉验证评估某站标榜的模型跟实际是否一致；2）**可用性监测**——每 5-15 分钟对已收录站做探测，公开展示在线率 / 延迟；3）**用户口碑点评区**——速度、稳定性、售后、充值体验。**对 AI 副业工程师这是一个被 7-04 Anthropic 封禁新闻直接放大的"刚需"赛道**：Claude 全面封禁地下通道后大量用户涌向国产模型 API / 中转，需要一个客观的"哪个站真稳"的参考平台；同时 OkkMax 这种站点一旦数据沉淀充分，SEO / GitHub Star 都能形成滚雪球。**对应副业机会**：1）做"AI API 中转站实时审计 + 自动切换"插件（Chrome 插件 + OpenAI-compatible SDK）；2）做"国产模型 API 测评 + 价格对比"内容副业（小红书 / B 站 / 即刻）；3）类比 DownDetector，搭建 "AI API 中转站可用性雷达"出海站（接 Sentry + Statuspage 即可）。地址：https://www.okkmax.com。

## 🤖 给 Codex 搭长期项目上下文，NoteDeep 工作流方法论

### 用 NoteDeep 给 Codex 搭建长期项目上下文
来源: V2EX · @lerongwan1
原文: [原文](https://www.v2ex.com/t/1224945)
摘要: 楼主把 NoteDeep 作为 Codex 的长期项目上下文库，把项目规则 / 设计 / 高频流程沉淀成结构化文档。具体做法：1）**项目规则放在 `AGENTS.md`**——代码风格、测试方式、目录约束、回复偏好；2）**长期设计放在 `docs/design/`**——编辑器结构、同步链路、AI 功能设计；3）**高频流程沉淀成 skills**——写 RFC、生成内容、排查线上数据。**对 AI 编程副业工程师这是"接单项目可持续性"的方法论核心**：Codex / Claude Code 在一个项目里干一周后，往往要重新交代一堆上下文，效率衰减 30%+；用结构化文档做"持久记忆"是行业普遍痛点。**对应副业机会**：1）做"AI 项目上下文模板"（GitHub 仓库 + 一次性付费下载 ¥39-99）；2）做"AI 工程项目文档自动化"小工具（自动从 git log 生成设计文档 / AGENTS.md）；3）做"AI 编程项目结构咨询"接单服务（半小时 5 次咨询 ¥199-499，对应 Boris Cherny "Builder / Maintainer"两类副业定位）。地址：https://www.notedeep.com。

## 💼 [上海][外企] AI Full-Stack Engineer 30-45W，企业级 AI Agent 平台

### [上海][外企] AI Full-Stack Engineer 全栈工程师 - 202607
来源: V2EX · @sdrzlyz
原文: [原文](https://www.v2ex.com/t/1224935)
摘要: 某 AI 企业级 Agent 平台招全栈工程师，**30-45W 税前 + 全英文技术沟通 + 不支持 Remote**。JD 要求 3-5 年全栈经验，熟练 Python / TypeScript / JavaScript + Vue 或 React + FastAPI + PostgreSQL/MySQL/Redis，理解 LLM 应用基础概念（Prompt / RAG / Tool Calling / Function Calling / Embedding / Agent Workflow）。加分项里有 LangChain / LlamaIndex / Dify / n8n / AutoGen / CrewAI / MCP 等框架经验。Nice to Have 写"有 Cursor / Claude Code / GitHub Copilot 高频使用经验"。**对正在做 AI 副业的全栈工程师这是"主力 vs 副业平衡"测算点**：30-45W 上海 base 是中端主力岗合理价，但日企 / 欧美企业"AI Agent + 全栈"比互联网大厂"Java 后端 / 移动端"路径更靠近副业延伸方向（Agent / Skill / Workflow 既是工作也是副业）。**对应副业机会判断**：1）评估自己当前主力岗是否让自己在 AI Agent / Skill 工程化上有持续成长；2）如果现在主力岗纯 CRUD，没有 AI 加持，副业做 AI Coding 工具类项目就受限——可考虑 6-12 个月内跳槽到这一类岗位作为"副业延时投资"。

## 🛠 Mac 多浏览器分流 BrowSync（独立开发 + 内购限免案例）

### [内购限免] Mac 平台多浏览器分流和同步工具
来源: V2EX · @Chentao1006
原文: [原文](https://www.v2ex.com/t/1224931)
摘要: 楼主做的 BrowSync（同览）是 macOS 跨浏览器同步中枢：URL 分流（按域名 / URL 规则 / 参数 / 来源应用 / 时间段）、书签同步、Cookie / LocalStorage / sessionStorage 同步、跨浏览器标签页共享、iCloud 多 Mac 同步。**纯本地 WebSocket 守护进程同步，没有任何外部服务器，隐私友好**。**当前是内购专业版限免窗口**。**对副业 Mac 工具开发者这是一个标杆案例**：BrowSync 把"普通浏览器功能 + 隐私优先 + iCloud 同步 + 内购限免"组合出独立开发者年收入估值千万级的产品形态（按 Mac 工具 5-10% 转化率 / $9.99 月费估算）。**对应副业机会**：1）类比做"Windows 端多浏览器同步工具"——市场更大人群更多但 macOS 限免策略无法复用；2）做"AI Coding 不同 IDE 之间上下文同步"插件（Cursor ↔ Claude Code ↔ Codex ↔ Windsurf），BrowSync 的 URL / Cookie 同步思路可迁移；3）学 BrowSync 的"launch 定价 + 限免拉声量"运营手法，结合上面 AI Coding 工具做"launch day 0 销量"。官网：https://browsync.ct106.com。

## 📱 Vibe Coding 硬件 OASIS Ring 走红，「听话」语音硬件起风

### 语音输入戒指 OASIS 走红，Vibe Coding 带火了一波 AI 硬件
来源: 36kr · 雷科技
原文: [原文](https://www.36kr.com/p/3880964231707525)
摘要: 雷科技报道：智能戒指 OASIS Ring 不主打健康数据，而是做"输入设备"——戒指内置麦克风 + 按键 + 动作传感器，能用声音 / 手势直接控制电脑里的 AI。这是跟影石 insta360 Vibe Coding 麦克风同一类的"AI 录音类硬件"，面向 Vibe Coding 生产力场景。**雷科技核心观点**：今年网上走红的相关硬件都在往轻量化走——年初有网友自制"AI 编程三键键盘"（ChatGPT / 复制 / 粘贴），影石做 Vibe Coding Mic Air，光帆科技 AI 耳机能独立联网直连 OpenClaw。**对 AI 副业工程师是"硬件 + 内容"复合变现窗口**：你做软件副业的同时，可以同步做"AI 硬件测评 / 教程 / 配置文件"内容副业，附带的 keyboard shortcut 配置文件 / Cursor 语音命令预设可以卖 ¥9.9 / 套。**对应副业机会**：1）做"OASIS Ring / Vibe Coding Mic Air / AI 耳机 → Cursor / Claude Code / Codex"的语音 + 手势控制配置文件（按键映射 + 语音命令清单 + 教学视频），挂 Gumroad 卖 ¥19-49；2）做"Vibe Coding 副业硬件清单"种草内容（小红书 / B 站 / 即刻）；3）面向国内 7-10 国产模型迁移窗口，做"国产 AI 助手 + 智能戒指"组合测试视频内容。

## 🧠 Show HN 半衰期 7 小时：副业 launch 数据复盘

### Show HN: I measured the half-life of 41,301 Show HN launches. It's 7 hours
来源: Hacker News · @jonnonz
原文: [原文](https://news.ycombinator.com/item?id=48759838)
摘要: 作者 jonno.nz 统计了 41,301 个 Show HN 提交，得出**半衰期 7 小时**——大部分 Show HN 在前 24h 内就死掉。帖子 102 个赞 / 28 评论，HN 显示页前排讨论里反复出现的两点：一是"成功的 Show HN 都是真有刚需的工具，不是刻意 launch"，二是"普通开发者要靠 Show HN 做出能持续跑营收的产品，必须先在 7 小时窗口里被高频推上 front page"。**对 AI 副业开发者这是非常清醒的"复盘级数据点"**：Reddit / X / V2EX 也普遍是 4-12 小时的内容窗口。文章还点了关键事实："**launch 之后还活着才叫 launch**"。**对应副业实操方向**：1）把副业产品的"0-7 小时"窗口作为关键指标；2）launch day 前要准备"首发响应预案"——加速发一条"作者解答高频提问"评论、push 给 KOL 转发、联系"AI Daily Brief"类公众号（如本号）写稿；3）launch 后第 7 天复盘——保留好的 KPI，砍掉没用的功能；4）不要把"上 front page"当 100% 目标，心态上当成"找 30 个真实用户比 3000 个 front page 点赞重要"。

## 🛠 Danluu Agentic coding notes from Galapagos Island，本地化方法论

### Agentic test processes, LLM benchmarks, and other notes on agentic coding from Galapagos Island
来源: Hacker News · danluu.com（HN 110 赞 / 51 评论）
原文: [原文](https://news.ycombinator.com/item?id=48782671)
摘要: Dan Luu 长文分享他在硬件公司 Centaur 学到的"AI 时代测试流程"沿用到 LLM 编程环境的实战笔记。关键观点：1）**测试要作为一等公民的工程职业**——他们当年雇了 20 个测试工程师 + 20 个逻辑设计师，1000 台机器 24h 生成 + 跑测试，几乎没有手写测试；2）**默认不做 code review**，因为测试覆盖足够；3）**长期 regression suite 跑 3 个月**——这是当时"软件质量可以高于人审"的可验证实证；4）**几乎不写手写测试 / 完全不写单元测试**——靠属性测试 / 随机化测试 / fuzzing 替代；5）**LLM 时代这条路径更适合**——一个工程师能生成的代码量超过人类 review 的极限；6）Dan 在自家产品里跑"support ticket → PR"全流程，目前保持 0 误报。**对 AI 副业工程师这是"工作流程优化"的稀有实战范本**：副业接单经常被测试 + code review 占满精力，作者给出的"测试驱动 + 无 review"是少有的、可落地的、能让你"接单产能翻倍"的工程方法论。**对应副业机会**：1）做"AI 副业测试自动化"工具 / 服务（按 LISENCE / 代码异味自动生成 fuzzing 用例 + 属性测试）；2）做"AI 代码 review 自动 reject / accept"中间件，集成到 Cursor / Claude Code / Codex；3）参考他"支持工单转 PR"的工作流，做"sales chatbot 工单 → 内部助理自动解决"的 SaaS。

---

🦞 每日09:00自动更新

**数据来源**：36kr AI / TMT、新智元、雷科技、V2EX 程序员 / create / jobs / claude、Hacker News front_page + Show HN + 搜索

**⚠️ 链接核查清单（已逐条验证，仅列正文实际引用链接）：**
- ✅ https://www.36kr.com/p/3881112560005381 - Anthropic拟全面封禁地下通道 标题/正文/作者 一致
- ✅ https://www.v2ex.com/t/1224964 - Claude Code + Codex 双开会话桥 agent-bridge 标题/正文/发布者 RaysonMeng 一致
- ✅ https://www.v2ex.com/t/1224954 - AI 中转站点评监测站 OkkMax 标题/正文/发布者 utcplus 一致
- ✅ https://www.v2ex.com/t/1224945 - 用 NoteDeep 给 Codex 搭建长期项目上下文 标题/正文/发布者 lerongwan1 一致
- ✅ https://www.v2ex.com/t/1224935 - [上海][外企] AI Full-Stack Engineer 30-45W 202607 标题/正文/发布者 sdrzlyz 一致
- ✅ https://www.v2ex.com/t/1224931 - Mac 平台多浏览器分流和同步工具 BrowSync 内购限免 标题/正文/发布者 Chentao1006 一致
- ✅ https://www.36kr.com/p/3880964231707525 - 语音输入戒指 OASIS 走红 Vibe Coding 硬件 标题/正文/作者 雷科技 一致
- ✅ https://news.ycombinator.com/item?id=48759838 - Show HN: I measured the half-life of 41,301 Show HN launches 标题/正文/作者 jonnonz 一致
- ✅ https://news.ycombinator.com/item?id=48782671 - Agentic coding notes from Galapagos Island danluu 标题/正文/作者 一致
