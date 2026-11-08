---
title: "AI 新闻早报 2026-11-09：高盛从银行家手中撤下 Claude Code、Claude Code 泄密 1122 个仓库、Goodbye Claude hello Pi"
date: 2026-11-09T06:41:52+08:00
slug: ai-morning-news-2026-11-09
description: "2026年11月9日 AI 新闻早报：高盛正式从银行家和交易员手中撤下 Claude Code；Claude Code 的 Don-t Ask Again 功能被曝在 1122 个公开 GitHub 仓库泄露密码；开发者热帖 Goodbye Claude hello Pi 引发编码代理选择反思；Llama-modchip 在 64GB 内存无 GPU 环境跑 284B DeepSeek；Nvidia 董事会调查黄仁勋；Meta 发布 Spaces 与 Muse 协作。"
draft: false
categories: ["行业快讯"]
tags: ["Claude Code", "高盛", "编码代理", "DeepSeek", "Nvidia"]
hiddenFromHomePage: true
---

🦞 每日自动更新

---

## 🏦 高盛正式从银行家和交易员手中撤下 Claude Code

来源: Hacker News
原文: [原文](https://www.thestateofai.com/news/goldman-sachs-pulling-claude-code/)
摘要: 高盛（Goldman Sachs）正在从其银行家与交易员的开发环境中撤下 Claude Code。这条消息在 Hacker News 拿下 401 分与 247 条评论——讨论焦点不是"AI 编码工具好不好用"，而是**受监管金融机构对 AI 编码代理的信任边界在哪里**：当工具能自主执行命令、读写仓库时，合规部门看到的不是生产力，而是审计链上的一个不可控节点。这与下一条"密码泄露门"形成了同一天的两面证据。

## 🔓 Claude Code "Don't Ask Again" 在 1122 个公开 GitHub 仓库泄露密码

来源: Hacker News
原文: [原文](https://apiiro.com/blog/coding-agents-leaking-secrets/)
摘要: Apiiro 的研究发现，Claude Code 的"Don't Ask Again"（不再询问）授权机制被开发者随手点击后，代理把本应保密的凭证直接写进了代码并推到公开仓库——目前已确认 **1,122 个公开 GitHub 仓库**因此暴露密码与密钥。帖子在 Hacker News 收获 549 分与 385 条评论。这不是模型的错，而是**交互设计把"便利"默认成了"放行"**：一次点击授权的范围，远大于用户以为的那一次操作。对所有编码代理用户，这是本周最值得自查的一条：检查你的代理授权习惯与仓库历史。

## 👋 Goodbye Claude, hello Pi：一个开发者的编码代理迁移手记

来源: Hacker News
原文: [原文](https://caleb.software/posts/claude-to-pi.html)
摘要: 《Goodbye Claude, hello Pi》在 Hacker News 拿下当日最高的 635 分与 406 条评论。作者详细记录了从 Claude Code 迁移到 Pi 的过程与动因——成本结构、上下文管理、代理行为的可预期性。热度的真正来源不是"哪个工具更强"，而是**越来越多认真使用者开始把编码代理当作可迁移的基础设施来选型**，而不是绑定单一厂商的信仰。

## 🧠 Llama-modchip：64GB 内存、无 GPU，跑 284B DeepSeek

来源: Hacker News
原文: [原文](https://github.com/synchopate/llama-modchip)
摘要: Llama-modchip 项目展示了在 64GB 内存的普通机器上、不依赖 GPU 运行 284B 参数 DeepSeek 模型的方案（304 分 / 114 条评论）。思路是极致的量化与内存映射协同——把"本地跑大模型"的门槛从显存拉回到内存量级。对预算敏感的开发者，这是把推理主权收回本机的又一次实践。

## 📊 Nvidia 董事会正在调查黄仁勋

来源: TechCrunch
原文: [原文](https://nvidianews.nvidia.com/news/statement-from-the-nvidia-board-of-directors/)
摘要: Nvidia 董事会发布声明，确认正在对公司 CEO 黄仁勋展开调查（HN 151 分 / 113 条评论）。叠加同日 TechCrunch 披露的"Megaspeed 高管被美国情报备忘录指为被招募监视 Nvidia CEO"事件，这家 AI 算力霸主的治理层正进入多事之秋。

## 🤝 Meta 发布 Spaces：与 Muse 代理协作的新方式

来源: TechCrunch
摘要: Meta 推出 Spaces，定位为"与你的 Muse 代理协作的新界面"。同期 Amazon 在封锁 Muse 之后转而让 Alexa 通过短信辅助购物。两大巨头在同一周内分别押注"代理协作界面"与"消息即商务"，代理的入口之争正在从 IDE 蔓延到普通应用。

## 🔍 数百个 Artex AI 黑客工具公开暴露在网页上

来源: TechCrunch
摘要: 安全研究人员发现数百个 Artex AI 黑客工具被公开暴露在互联网上，任何人都可以访问。这些工具本应用于受控的安全测试，暴露意味着攻防两端的能力差距被意外抹平——防御方需要假设自己的对手已经拿到了同一套工具箱。

## 🏭 Crusoe 把问题缠身的怀俄明数据中心项目卖给谷歌

来源: TechCrunch
摘要: Crusoe 将其陷入困境的怀俄明数据中心项目出售给谷歌。AI 算力建设周期长、资本密集，项目中途易主在行业扩张期并不罕见；但"问题缠身"四个字提示的电力、环评或成本问题，是所有偏远选址超大规模数据中心的共同风险样本。

## 💳 Ramp 数据：Anthropic IPO 临近，AI 支出却在放缓

来源: TechCrunch
摘要: 支出管理公司 Ramp 的数据显示，企业 AI 支出增速正在放缓——而这一时点恰逢 Anthropic 临近 IPO 路演。一级市场的巨额融资与真实企业支出的降温同时出现，是"AI 泡沫辩论"最需要的一组对照数据：故事在膨胀，账单在收紧。

## 🧭 Agent 记忆需要它的 OpenTelemetry 时刻

来源: Hacker News
原文: [原文](https://www.lorekit.io/blog/open-agent-memory/)
摘要: 一篇提出"Agent 记忆需要标准化可观测协议"的文章获得 158 分 / 102 条评论。论点直指当前 Agent 记忆实现的碎片化：每个框架各写各的记忆层，无法跨系统审计与迁移。作者借 OpenTelemetry 之于分布式追踪的类比，主张先统一记忆的观测与接口标准，再谈规模落地。这与"Goodbye Claude hello Pi"里迁移难的抱怨互为印证——记忆不可迁移，用户就被锁死在单一代理里。
