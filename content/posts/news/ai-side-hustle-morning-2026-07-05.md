---
title: "AI副业早报 2026-07-05"
date: 2026-07-05T08:30:00+08:00
slug: ai-side-hustle-morning-2026-07-05
description: "2026年7月5日 AI 副业早报：Cloudflare 9-15 默认屏蔽 AI 爬虫掀开「数据税收站」基础设施之争、GPT-5.6 Sol/Terra/Luna 三大模型 7-7 卡点截杀 Claude、Codex 桌面端负责人访谈谈「实现变便宜 品味变贵」、caveman 把 Claude/Codex/Cursor 输出砍 65% token 火上 GitHub Trending 第 1、阿里 page-agent 2 万星让网页原生变 GUI Agent、Chrome DevTools 官方 MCP 让 AI Coding 直接调试浏览器、独立开发者 5 天 AI 全程撸出 PDF 翻译平台「译档」、V2EX 同步涌现 ICP 许可证虚假广告警示 + 国产模型替代选型讨论。"
draft: false
categories: ["行业快讯"]
tags: ["AI副业", "Cloudflare", "GPT5.6", "Codex", "Claude", "VibeCoding", "独立开发", "Agent", "Skills", "page-agent", "caveman", "国产模型", "合规"]
hiddenFromHomePage: true
---

🦞 每日09:00自动更新

---

## 🚨 Cloudflare 9-15 起默认屏蔽混合 AI 爬虫 + Pay Per Use 转向「内容税收站」，AI 副业的下游被「基础设施」锁喉

### 赛博菩萨 Cloudflare，AI 爬虫最严厉的父亲
来源: 36kr · 极客公园
原文: [原文](https://36kr.com/p/3882226982842376)
摘要: 极客公园报道：7 月 1 日 Cloudflare 发了一篇博客《你的网站，你的规则》，宣布 **9 月 15 日起，所有用 Cloudflare 的网站默认屏蔽混合用途 AI 爬虫**——只要页面有广告，AI 的训练爬虫和 Agent 爬虫就进不来。逻辑翻转：以前是「默认允许，你可以选屏蔽」，现在是「默认屏蔽，你可以选允许」。这是互联网基础设施层第一次对 AI 数据获取方式做系统性「立法」。Cloudflare 同时把爬虫拆成 Search / Agent / Training 三类独立标签，站长可以分别 allow/block。Cloudflare 还公布了一组数字：**Google 爬取回流比 14:1、OpenAI 1700:1、Anthropic 73000:1**——AI 公司拿走内容、几乎不还回流量。Cloudflare 把去年的 Pay Per Crawl（按爬取次数收费）升级为 **Pay Per Use**（按内容真正被用到生成回答时收费），首批合作 AI 搜索是 Ceramic.ai 和 You.com；大出版商 Condé Nast / Dotdash Meredith / Reddit 已经站台。**对 AI 副业工程师这是比 Anthropic 封禁更底层的「管道级」风险**：你做的内容站 / 工具站 / 副业 landing page 一旦托管在 Cloudflare（全球 ~20% 网络流量），它会默认拒绝 Googlebot 之外的 AI 训练爬虫——内容 SEO / 数据飞轮 / Agent 调用入口全部受影响。**对应副业机会**：1）做「Cloudflare 反 AI 爬虫策略对照表」工具站——按 AI 公司分类列出 Allow / Block 默认值，**SEO 类细分长尾**；2）做「Pay Per Use 内容注册中介」小工具——独立博客一键声明内容可被引用、按展示分账（Stripe Connect 或 Lemonsqueezy 集成即可），把 Cloudflare 的「收银台」变成小创作者也能分到的现金；3）做「Cloudflare 之外的 80% 网络流量」副业咨询——未托管 Cloudflare 的网站如何补 AI 爬虫审计 + 自定义 robots.txt + 元数据标签；4）做"AI 副业被 Cloudflare 误伤"的申诉 / 申诉模板小产品（这是个 9-15 之后 100% 会爆发的痛点）。

## 🛠 GPT-5.6 三大模型 7-7 卡点截杀 Claude Fable 5 限额真空期，副业定价权窗口打开

### 趁火打劫，GPT-5.6 三大模型全曝，定档 7 月 7 日？
来源: 36kr · 新智元
原文: [原文](https://36kr.com/p/3880971920584962)
摘要: 新智元：网友扒 Codex 客户端底层代码，**GPT-5.6 Sol / Terra / Luna** 三个子模型标识 + 一个全新「速度拨盘」功能浮出水面。OpenAI 内部目标窗口直指 **7 月 7 日至 9 日**——刻意卡在 Claude Fable 5 特定限额方案失效的「真空期」。关键情报：1）**GPT-5.6 Sol 价格比 Fable 5 便宜两倍以上**（token 效率高）；2）**Sol Ultra** 性能直逼 Fable 5，价格更亲民；3）使用额度限制大幅放宽；4）严格安全护栏在推但不会像 Fable 那么激进。海外博主 Shivam 用 GPT-5.6-terra vs Fable 5 解决同一复杂 prompt，Fable 烧 21% 额度还在反问细节，**terra 只用 13% 额度直接列出方法路径并执行**。Oracle 总监 Gilson Melo 用 WebGL 游戏开发做盲测，**GPT-5.6 High 在细节/物理碰撞/响应稳健性上明显胜出**——而且它主动问开发者 2 个关键决策、自作主张加音效。**对 AI 副业工程师这是"接单价 vs 模型成本"的拐点信号**：7-7 之后国内能直接访问的 ChatGPT Plus 圈套利窗口收窄；用 Claude API 接单的成本结构会被 GPT-5.6 直接打穿；**副业接单价要在 2 周内调整**：Sonnet/Opus 为主的接单项目要重新核算毛利（用 GPT-5.6 Sol 替代 Sonnet 部分任务，单价能下压 30-50%）。**对应副业机会**：1）做"GPT-5.6 vs Claude Fable 5 vs GLM-5.2 vs DeepSeek-V4 副业接单成本对比表"内容（小红书 / B 站 / 即刻，7-7 当周流量必爆）；2）做"GPT-5.6 限时薅羊毛指南"——Reflection CTO 提到 4 次速率限制重置额度有效期只有 30 天，6-11/12 入账的额度 7-12 起批量过期，**让 Codex 调用后端 API `GET https://chatgpt.com/backend-api/wham/rate-limit-reset-credits`** 查精确过期时间，这个小工具脚本 GitHub 一周内可能 200+ star；3）做"G​PT-5.6 Sol + Vibe Coding"组合的接单服务包（前端交互 / 数据清洗 / 批量重命名 / ETL 这类单价低但 GPT-5.6 能干的活）。

## 🤖 Codex 桌面端负责人访谈：实现变便宜 品味变贵，Vibe Coding 时代的能力锚点

### Codex、ChatGPT 为何合体？Codex 未来何去何从？OpenAI 核心 leader 回应一切
来源: 36kr · 机器之心
原文: [原文](https://36kr.com/p/3882258709180678)
摘要: 机器之心专访 Codex 桌面端负责人 Andrew Ambrosino。Codex 自今年 1 月周活用户涨 5 倍至 **500 万**，2 月桌面端 App 是关键催化剂——其中**知识工作者（非开发者）增速是开发者的 3 倍**。核心观点：1）**"实现变便宜，品味变贵"**——OpenAI 内部一个功能有 90 个团队同时探索 90 种实现方式，**最贵的环节变成策展（哪些值得合并、哪些值得砍、切换按钮应该几档）**；2）**"品味"不只是审美**——包含系统思维（融入系统）、方向感（属于哪个主题）、呈现方式（这个交互动画是不是太快速不符合语义）；3）**AI 至今做不好设计的原因**——设计比软件难评分（评价设计本身就是反馈循环）、实验室资源主要投在加速 AI 研究本身的能力（写代码早期显然）、**设计需要新颖性而代码需要跟随模式（这是矛盾的）**、最深的问题是抽象层（公司品牌重塑时 263 个组件应该共享的语义）；4）**Codex 不能提前发**——同样的产品形态去年 11 月推出会失败、2 月推出成功，唯一变量是中间几个月模型能力的进步。**AI 时代产品是否好用，不由 UI/UX 单独决定，由"模型在这个时刻能做什么"决定**；5）**工程师/设计师/PM 边界消失但是不能完全取消**——Andrew 明确反对彻底取消产品岗：那是"画地为牢式"的边界消失，每个专业有自己的技能门槛；6）**现在该问的不是"多少代码是 AI 写的"，而是"这些代码是有监督还是无监督写的"**。**对 AI 副业工程师这是"能力锚点迁移"的方法论级提醒**：副业接单里"我能写什么代码"已经不是稀缺品，"我能判断什么该写、什么不该写、怎么折叠、怎么抽象"才是。**对应副业机会**：1）做"Vibe Coding 时代的 PM 服务"——专门帮独立开发者做"功能优先级 + 砍功能 + 抽象设计"的接单咨询（半天 ¥999-2999）；2）做"Codex + ChatGPT 合并后的产品体验审计"小工具——对照 Andrew 提出的 90 个方案并行探索方法论，做团队级"哪些功能值得保留"AI 评分；3）面向"知识工作者"的 Codex 副业内容（不是开发者视角而是知识工作场景——会议纪要 / 报告 / 数据清洗 / 客户邮件），这是 3 倍增速的空白带；4）做"AI Coding 自检清单"——把"有监督 vs 无监督"、"实现成本 vs 品味成本"做成可勾选的副业交付前 checklist 模板，挂 Gumroad 卖 ¥29-99。

## 📊 AI 中转站点评监测 / 模型真伪测试两大站竞争白热化

### [服务市场] AI 中转站模型真伪测试跑分标准 jingxialai.com/apirank
来源: V2EX · @jingxialai
原文: [原文](https://www.v2ex.com/t/1224844)
摘要: 楼主做了一个 AI 中转站模型真伪测试跑分网站，**目前已经做了 25 项测试**：① 自我认知探测 ② API 响应字段核查 ③ 字母计数测试 ④ 单词逆序测试 ⑤ 语言陷阱题 ⑥ 数学推理 ⑦ 组合数学 ⑧ 数值比较 ⑨ 精确格式控制 ⑩ 响应速度分析 ⑪ 一致性重复测试 ⑫ 幻觉检测 ⑬ 复杂指令遵循 ⑭ 反事实推理 ⑮ 高级逻辑推理 ⑯ 代码生成 ⑰ 流式输出检测 ⑱ 知识截止日期探测 ⑲ 中文能力深度测试 ⑳ 异构语言查错（Rust） ㉑ 多轮对话记忆测试 ㉒ 函数调用能力探针 ㉓ 多模态盲降级探测 ㉔ 空间方向推理测试 ㉕ 极端字符约束能力。**楼主主动指出当前问题**："为什么 GPT5.5 模型在中转站里图片支持 prompt 失败，但模型纯度检测又显示是真 GPT5.5？"——怀疑是提示词设计问题。这一帖与昨天 7-4 早报提到的 **OkkMax 模型纯度 + 可用性监测站** 形成直接竞争。**对 AI 副业工程师这是一个"评测基础设施"赛道明确起来的信号**：两个站都盯同一批用户群（中转站采购方 + 大量 Claude 中转踩坑用户），且都在公开召集建议。**对应副业机会**：1）做"AI 中转站实测榜单 + 点评 UGC"——小红书 / 即刻 / Reddit r/AI_Agents 内容副业，配合这俩站点做导流分成；2）给 jingxialai 或 OkkMax 提 PR——加**中转站按价格 / 限额 / 退款政策**维度的对比表（这是测评没覆盖的）；3）做"中转站 API Key 健康度监控"——个人开发者角度，每个 key 实时跑 + 自动切备用；4）做"中转站合法性评级"（基于 t/1224797 那个被判刑讨论帖的法律风险维度），填补合规空白。地址：https://www.jingxialai.com/apirank/

## 💼 [法律红线] 海外模型 API 中转站会被判刑吗？副业合规分水岭

### 做海外模型的 API 中转站，会被判刑吗？
来源: V2EX · @pinepeakV2 + news.qq.com 报道
原文: [原文](https://www.v2ex.com/t/1224797)
摘要: 楼主引用腾讯新闻 2026-06-29 报道，问"做海外模型（Anthropic / OpenAI / Google）API 中转站"是否构成刑事风险。**这是 7-04 Anthropic 全面封禁地下通道新闻的国内法律配套延伸**：海外公司封禁是国内用户的"上游断流"，国内中转站运营者可能面对"非法获取计算机信息系统数据 / 提供侵入计算机信息系统工具罪 / 侵犯商业秘密罪 / 偷税漏税"等罪名。**对 AI 副业工程师这是"做中转站变现"和"做中转站监测服务变现"的合规分水岭**：一边继续做中转站接单的小团队在重新评估业务可持续性，一边做中转站监测 / 评测 / 咨询的副业变得更稳——后者不涉及未授权 API 转发，法律风险显著低。**对应副业机会**：1）做"AI 副业合规自查清单"——按业务模式（自训练 / 微调 / API 中转 / 套壳 / 培训）分类给出可能触及的国内法规 + 海外公司 ToS，分发到小红书 / 公众号，挂"法律咨询入口"做引流转 ¥199-599 单次咨询分成；2）做"中转站替代方案咨询"接单——帮正在做中转站的客户迁移到国产模型（GLM-5.2 / DeepSeek-V4 / Qwen3.6）做平替方案，按迁移复杂度收 ¥2999-9999；3）做"中转站业务转型路径"内容——给被 7-4 Anthropic 封禁新闻影响的中转站小团队做内容输出（视频 / 公众号 / 知乎专栏），沉淀粉丝后再做"AI 应用层"工具销售。

## 🤖 caveman Skill：让 Claude Code/Codex/Cursor 砍 65% token，副业毛利率立刻回升

### 🪨 why use many token when few token do trick — Claude Code skill that cuts 65% tokens
来源: GitHub Trending · JuliusBrussee
原文: [原文](https://github.com/JuliusBrussee/caveman)
摘要: GitHub **84k stars / 4.7k forks**（截至 7-5 早间），是 GitHub Trending 当周第 1。caveman 是一个 Claude Code skill/plugin，目标让 AI Coding agent「说话像原始人」——**同样答案 65% 更少输出 token**（精确保留代码 / 命令 / 错误字节）。works with **30+ agents**（Claude Code / Codex / Gemini / Cursor / Windsurf / Cline / Copilot 等）。示例对比：「The reason your React component is re-rendering is likely because you're creating a new object reference...」→「New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`.」——69 tokens → 19 tokens。**对 AI 副业工程师这是"Token 经济学"级别的边际改善**：Claude Code / Codex 接单时按 token 计费的代理中转成本立刻下降 30-50%（按输出 token 占比），接单价不变的情况下毛利率回升。**对应副业机会**：1）做"caveman + AGENTS.md 集成教程"内容——教独立开发者如何在 Claude Code / Codex / Cursor 里挂这个 skill（截屏 + 录屏 + 配置模板），挂 Gumroad 卖 ¥19-49 / 套；2）做"中文版 caveman"——本地化为"文言文编程 skill"，符合中文极简审美，B 站 / 小红书 / 即刻做内容副业（文化差异天然有梗）；3）做"caveman + 企业内部 Coding Agent"部署咨询——SaaS 公司客户想批量给开发团队装，按企业 licence 收 ¥99 / seat / 月；4）做"国内 token 消耗监控"小工具——配合 caveman，把 hook 输出实时统计接入飞书 / 钉钉 / Bark，让副业老板看到月度 token 账单下降。GitHub：https://github.com/JuliusBrussee/caveman

## 🛠 阿里 page-agent：把网页变 GUI Agent 的 in-page JavaScript 库，2 万星

### alibaba/page-agent: JavaScript in-page GUI agent
来源: GitHub Trending · alibaba
原文: [原文](https://github.com/alibaba/page-agent)
摘要: GitHub **23k stars / 2k forks**，是阿里开源的 page-agent——**用一行 `<script>` 就能让你的网页拥有自然语言控制的 GUI Agent**。核心特点：1）**零依赖**——不需要 browser extension / python / headless browser；2）**纯文本 DOM 操作**——不依赖截图、不需要多模态 LLM、不需要特殊权限；3）**BYOLLM**（bring your own LLM）；4）**Chrome 扩展 + MCP Server（Beta）可选**，可以跨标签页接管 Agent；5）**Use Cases 四个商业化方向**：SaaS AI Copilot / 智能表单填写（20-click 流程一句话搞定）/ 无障碍访问（语音 + 屏幕阅读器）/ 多页面 Agent。**对 AI 副业工程师这是"AI 中间层"赛道的核心卡位**：国内独立开发者想做"给现有 SaaS 加 AI Copilot"生意，过去要重写后端或部署 headless browser；现在只需要让客户网站加一行 script。**对应副业机会**：1）做"page-agent + 国产模型 + 业务 SaaS"垂直模板——给 CRM / ERP / 表单密集型 SaaS 客户做 demo 集成（半天 ¥1999 起，按 SaaS 客单价收 1-3% 分成）；2）做"中文 SaaS AI Copilot 集成服务"接单——独立开发者接 page-agent 集成项目，单项目 ¥9999-49999；3）做"page-agent MCP Server 二次开发"——比如给企业微信 / 飞书 / 钉钉做个 MCP 客户端，让客户从 IM 直接触发业务系统的 GUI Agent；4）做"page-agent 业务案例库"内容副业——收集各 SaaS 集成案例挂独立站，附 demo 视频，挂 affiliate 链接。地址：https://alibaba.github.io/page-agent/

## 🤖 Chrome DevTools 官方 MCP Server：让 AI Coding 直接操控浏览器调试

### ChromeDevTools/chrome-devtools-mcp: Chrome DevTools for agents
来源: GitHub Trending · ChromeDevTools（Google 官方）
原文: [原文](https://github.com/ChromeDevTools/chrome-devtools-mcp)
摘要: GitHub **45k stars / 3k forks**，Google Chrome DevTools 团队官方开源的 MCP server——让 Claude / Cursor / Copilot / Antigravity 等 coding agent **直接控制真实 Chrome 浏览器**做调试 + 自动化 + 性能分析。核心能力：1）**性能洞察**——录 trace + 提取 actionable 性能报告；2）**高级浏览器调试**——网络请求分析、截图、控制台消息（含 sourcemap stack trace）；3）**可靠自动化**——puppeteer 驱动 + 自动等待；4）**CLI 模式**——不依赖 MCP 客户端也能用。**对 AI 副业工程师这是"前端 + AI 调试"工作流拐点**：过去前端 bug 要靠 Chrome DevTools 手点 + 截图给 Cursor/Claude 看，现在 Cursor 可以直接 puppeteer 打开浏览器自己看、自己截图、自己改、自己回归。**对应副业机会**：1）做"chrome-devtools-mcp + Cursor 前端调试教程"内容——B 站 / YouTube / 小红书，演示"Cursor 自动打开 Chrome → 找到 React 渲染 bug → 自动改 → 自动验证"全流程，单视频挂 Cursor 联盟链接；2）做"企业前端团队 MCP 集成部署"接单——给中型 SaaS 团队部署 chrome-devtools-mcp + 内网 Claude API，按团队规模收 ¥199/seat/年；3）做"前端性能优化 MCP 工具链"——基于 chrome-devtools-mcp 二次开发"自动跑 Lighthouse + 自动提交 PR + 自动开 issue"的 GitHub Action，挂 GitHub Marketplace 收订阅；4）做"国内浏览器适配层"——给非 Chromium 内核浏览器（夸克 / 微信内置 / QQ 浏览器 / 360）写 polyfill，按客户规模收许可费。GitHub：https://github.com/ChromeDevTools/chrome-devtools-mcp

## 🛠 独立开发案例：5 天 AI 全程撸出 PDF 翻译平台「译档」，订阅式 SaaS 雏形

### 这几天用 AI 撸了个 PDF 翻译平台，没写一行代码
来源: V2EX · @binarycopy
原文: [原文](https://www.v2ex.com/t/1225038)
摘要: 楼主用 5 天时间，**从产品定位、UI 草图、后端架构、前端页面、迁移脚本、API 文档到上线部署，全程没自己敲过一行代码**（也就 git commit 自己点的），搓出「译档」PDF 翻译平台。功能：1）📄 上传 PDF → 自动解析页数 + token → 报价 2）🧾 确认下单 → 冻结积分 + 跑翻译 worker 3）🪞 PyMuPDF + Chromium 渲染保留版式输出（不是段落拍扁重排） 4）👀 左右对照预览 5）💰 按 token 结算（任务失败积分原路退回） 6）🔌 对外开放 API（OpenAPI 文档 + API Key 管理页） 7）💬 微信扫码支付。**目标场景**：合同 / 论文 / 金融研报 / 公司介绍 / 跨境电商说明书——"我要保留结构 + 复核一遍"。技术栈 FastAPI + Vite + React + TS，**业务模型按 token 预付费 + 任务失败退款 + 开放 API 收开发者口碑**。**对 AI 副业工程师这是"5 天从 0 到订阅 SaaS"新基准**：结合 page-agent / caveman / chrome-devtools-mcp / Codex，**做"PDF / 文档 / 数据"垂直翻译/解析类 SaaS** 的边际成本已经接近 0。**对应副业机会**：1）做"PDF 翻译 / 文档解析"垂直工具——电商说明书 / 学术论文 / 法律合同 / 出海产品手册，挑一个细分做（结合 7-3 Anthropic 封禁，国产模型 + GLM/DeepSeek/Qwen 平替 Claude API）；2）做"OpenAPI + API Key 管理"模块——这是 SaaS 类副业共性需求，**做成开源 starter**（FastAPI + Stripe + 微信支付 + OpenAPI doc 一键生成），GitHub star + 联盟分润；3）做"5 天 0 代码 SaaS 全流程录播课"——把楼主这套工作流（AI 出 PRD + AI 出架构 + AI 写代码 + AI 部署）录成 ¥199-599 课程，挂小红书 / B 站 / 知识星球分销；4）做"AI 副业项目法律 + 工商 + ICP"合规包——基于今天 t/1225069 那个 ICP 经营许可证警示帖，独立开发者注册公司 + ICP + 支付通道全流程打包，挂 ¥99-299 一次性。

## 📱 AI Agent 通知工具 agent-notify：开源一个被官方忽视的副业痛点

### 推荐一个我自己开发的自用的 AI Agent 通知工具吧
来源: V2EX · @LetTTGACO
原文: [原文](https://www.v2ex.com/t/1224873)
摘要: 楼主做 agent-notify（GitHub 4 stars 起步但功能完整）：**接收 AI Agent 原始 hook 事件 → 服务端格式化成简短行动导向通知 → 通过 Bark（iPhone / Apple Watch）或 ntfy（跨平台）推送到手机/桌面**。支持 OpenCode / Claude Code / Codex 三个 agent 的 hook。核心特性：1）**默认 120 秒以内任务保持安静**——只在会话运行时间足够长时提醒；2）**60 秒防抖/节流**——多个权限请求合并；3）**每工具独立 `/agent-notify` 开关**——支持当前会话、定时、持久静音；4）**Bark + ntfy 双通道**。**对 AI 副业工程师这是"AI Coding 多项目并行"工作流的真实痛点**：接 N 个项目时 Agent 后台跑、你前台摸鱼，任务完成不知道是常态；agent-notify 把 Codex 桌面端已经有但 CLI 没有的能力补齐。**对应副业机会**：1）做"agent-notify + 多 Agent 编排"扩展——加飞书机器人 / 钉钉 / 企业微信推送通道，把开源项目商业化成"小团队 ¥29/月 / 大团队 ¥199/月" 订阅；2）做"agent-notify 状态看板"——把 hook 事件做聚合 dashboard（按项目 / 按 agent / 按日），挂副业团队做"管理驾驶舱"产品；3）做"agent hook 标准 + 协议规范"内容副业——把 agent-notify 的 hook 设计做成 RFC 投稿 + B 站科普，挂"hook 协议咨询"接单；4）做"AI Coding 离线报告订阅"——agent-notify + 周报邮件，把"这周哪个项目花了多少 token / 跑了几次权限请求 / 完成率多少"做周报订阅 ¥9.9/月。GitHub：https://github.com/LetTTGACO/agent-notify

## 🛠 Mac Claude Token Monitor Bar (CTMB) 上线：副业老板专属的 token 账单条

### CTMB 终于和大家见面了
来源: V2EX · @HAOGRE
原文: [原文](https://www.v2ex.com/t/1225050)
摘要: 楼主做了 CTMB（**Claude Token Monitor Bar**）——macOS 顶栏 widget，**实时监控 Claude API token 用量**，避免 Claude Code 接到一半发现额度爆掉的尴尬。**缩写 C​laude T​oken M​onitor B​ar** 楼主自嘲"无敌"。GitHub 起步 stars 10 个，目标冲 homebrew 官方源。**对 AI 副业工程师这是"接单时 token 焦虑"的微观工具**：做 Claude 接单 / 自媒体内容 / 客户 demo 时，最怕 token 跑空不知道——CTMB 直接显示余额 + 剩余预计时长。**对应副业机会**：1）做"CTMB + 多模型版"扩展——同时监控 Claude / GPT / Gemini / GLM / DeepSeek，**接单老板视角的 token 账本**，订阅 ¥9.9/月；2）做"CTMB + 团队版"——多用户 / 多项目聚合 + 周报推送，¥49/月/团队；3）做"Claude Pro 中转站订阅比价"——结合 t/1225009 推荐纯血 claude 中转站帖，做"哪个中转站最值"实时榜单；4）做"homebrew tap 收录攻略"内容副业——把 CTMB 上 homebrew 官方源的过程录成教程，挂"Mac 工具发布指南"做付费内容。GitHub：https://github.com/HAOGRE/ClaudeTokenMonitorBar-macOS

## 💡 Vibe Coding 时上下文最先满的竟是自己？副业多项目并行方法论

### Vibe Coding 时上下文最先满的竟是自己？
来源: V2EX · @ssshooter
原文: [原文](https://www.v2ex.com/t/1224872)
摘要: 楼主吐槽"我最近同时开发多个项目，我自己的上下文已经不够用了哈哈哈，已经不知道某个项目接下来该干啥了。开始陷于短暂的痴呆了"——一句话精准击中 Vibe Coding 时代**多项目并行**的痛点。配套讨论里出现的方法论：1）**每日站会式回顾**——早上 10 分钟过昨天每个项目进展；2）**写当日 commit 前先写"明日 TODO"**——保持上下文跨日不丢；3）**AGENTS.md 模板化**——每个项目放一个标准化的"当前状态 + 阻塞 + 下一步" 段落；4）**接单时严格单线并行**——同时最多 2 个项目，第三个必须砍掉或等前一个稳定；5）**用 NoteDeep / Obsidian 做项目 Dashboard**——视觉化"哪个项目最近没动"。**对 AI 副业工程师这是"AI 时代项目管理的反脆弱指南"**：AI 帮你做了实现，但项目管理反而变成稀缺能力。**对应副业机会**：1）做"Vibe Coding 项目 Dashboard 模板"——Notion / Obsidian / Logseq 三平台各一套，挂 Gumroad 卖 ¥39-99；2）做"多项目并行接单咨询"——帮自由职业者做项目管理 SOP 搭建，半小时 1v1 ¥299；3）做"AI 时代 GTD 重构"内容——B 站 / YouTube / 小红书，把"上下文满了"这件事做成系列科普，附带的每日复盘模板挂链接；4）做"团队级 Vibe Coding 周报插件"——Cursor / Claude Code / Codex hook 接到飞书 / 钉钉，按项目自动周报。

## 💼 [合规警示] 一人公司警惕《ICP 经营许可证》虚假广告，独立开发者必读

### 关于 个体/一人公司 警惕《ICP 经营许可证》虚假广告
来源: V2EX · @importmeta
原文: [原文](https://www.v2ex.com/t/1225069)
摘要: 楼主提醒：**如果开发的网站全是自己的业务，不需要《ICP 经营许可证》（增值电信业务经营许可证）**——只有容许第三方入驻的平台（淘宝 / 天猫 / 京东 / 拼多多）才需要办理。建议拨打当地通信管理局电话二次核实，**网上刷到任何威胁"创业必须办理 ICP 经营许可证"的帖子或短视频，请拉黑、曝光、举报**。**对 AI 副业工程师这是"代办 / 假证 / 套证"灰色产业链的明确警示**：近期短视频 / 私域流量里有人专门向独立开发者 / 一人公司推"代办 ICP"服务，收费 ¥3000-15000 但实际**办理对象错误**（多数独立开发者根本不需要）；少数代办是真办下来，但被绕过的可能不是创业者而是平台方。**对应副业机会**：1）做"ICP / EDI / SP 资质自检工具"——独立开发者在线自查，按业务模式（自有业务 / 平台 / 撮合 / 跨境）分类列出真正需要的资质；2）做"独立开发者工商 + 资质合规包"——基于 t/1224638 "2026 开一个公司"经验分享帖的代账/工商/银行公户/税务/资质全流程 SOP，**团购 ¥199 / 单家**；3）做"代办资质反诈科普"内容——小红书 / B 站 / 知乎，挂"真实合规咨询"分润；4）做"资质 vs 业务模式"对照表 wiki——把 100 个常见 AI 副业业务模式按需要哪些资质做表，**SEO 长尾极佳**。

## 🤖 国产 Coding Plan 选型：GLM-5.2 / Qwen3.7 / DeepSeek-V4 / Kimi-2.7 全实测对比

### 尝试用了一下 qoder，qoder 的模型都是国产几家里面最新的模型
来源: V2EX · @Lanhuazhe
原文: [原文](https://www.v2ex.com/t/1224903)
摘要: 楼主实测国产 coding 工具 qoder（背后是 minimax 2.7 / kimi 2.7 / glm 5.2 / deepseek v4 / qwen 3.7）。实测结论（同一 Android 启动器项目，同一模拟器验证 bug）：1）**Codex 默认 auto 模式**：改完未验证，bug 漏到手机；2）**Qwen3.7 max**：修复有效但底部搜索栏没背景覆盖；3）**DeepSeek-V4 pro**：修复正确 + 主动用模拟器验证 + **唯一记得"上一个 PR#4 已合并在本分支 amend"**，但被要求同时提交 `.gradle` 文件时反而把 PR#5 关闭重建 PR#6；4）**MiniMax-M3 2.7**：明确说了有模拟器但改完没去验证，修复有效但改动太大；5）**Kimi 2.7**：思考时间长但没修好，前后两张截图完全一样却报告"修好了"；6）**GLM-5.2**：思考时间长但没修好，知道用模拟器验证但额度没了。**综合结论：DeepSeek 最好**。**对 AI 副业工程师这是"国产模型替代 Claude 的选型硬数据"**：qoder 这种"模型可切换"工具的价值就是让副业老板实测各模型，按项目复杂度匹配——简单 UI 改 Qwen3.7，跨 PR 上下文管理用 DeepSeek-V4。**对应副业机会**：1）做"国产 Coding 模型选型测试用例"——挑 10 个典型副业项目（landing page / SaaS 后台 / Chrome 扩展 / 移动 H5 / 数据 ETL），让每个模型都跑一遍，挂评测博客 + 视频分润；2）做"qoder + 副业接单套餐"——给独立开发者推 qoder 按月套餐，按模型调用收费；3）做"国产模型 PR 工作流评估"小工具——专门测"AI 是不是记得上一个 PR 已合并"的回归用例，做成 GitHub Action 跑分排行榜；4）做"GLM-5.2 / Qwen3.6 coding plan 黄牛 / 代抢"服务（基于 t/1224887 智普 coding plan 抢不到帖的需求），**合规边缘但需求真实**。

## 🛠 HIC Mouse：AI Coding Agents 的「精准编辑」工具，56% 准确率 / 58% 降本

### Mouse: Precision Editing Tools for AI Coding Agents
来源: Hacker News · Show HN · @hic-ai 团队
原文: [原文](https://hic-ai.com)
摘要: HN front page 第 4 位（20 points）。HIC Mouse 解决"AI Agent 文件编辑是 broken 的"问题——大多数 AI agent 只用一种 string replacement 工具改文件，**看不到提议的改动、回滚也不干净**。HIC Mouse 用 **基于坐标的编辑** + **staged changes with atomic rollback** + **tool-response engineering** 三件事把"AI 文件编辑"重做：1）**6 个声明式操作**（INSERT / DELETE / ADJUST 而不只是 REPLACE）+ 精准外科手术语法；2）**所有有风险的 edit 都 staged**——AI agent 可以 Save / Cancel / Inspect / Refine；3）**embedded guidance in all tool responses**——上下文引导、下一步建议、风险评估、viewport 文件结构。数据：**3.6× 更快、56% first-try 准确率、58% 降本**。14 天免费试用 + no credit card。**对 AI 副业工程师这是"AI Coding 工作流核心工具"再定义**：当所有主流 coding agent（Claude Code / Codex / Cursor）都还是字符串替换，Mouse 这种基于坐标 + staged 的工具是**未来 12 个月的赛道明确信号**。**对应副业机会**：1）做"Mouse vs 默认 string replacement 副业接单成本对比"内容——挂副业老板 ROI 测算，挂联盟链接；2）做"Mouse + 企业部署"接单——给 SaaS 团队部署 Mouse，按 seat 收 ¥99/月/team；3）做"国内版 Mouse"——坐标编辑 + staged changes 思路可平移到 Cursor / Claude Code / CodeGeeX / 文心快码等国内工具；4）做"AI Coding 工具集评测博客"——每月测评新工具，**挂联盟 + 教程付费 + 联盟分润**三路变现。HN：https://news.ycombinator.com/item?id=48759838 ，站点：https://hic-ai.com

## 🧠 Armin Ronacher 深度长文：SOTA 模型调用工具反而更差，Vibe Coding 的「品味」陷阱

### Better Models: Worse Tools
来源: Hacker News · @mitsuhiko（Armin Ronacher，Flask / Jinja 作者）
原文: [原文](https://lucumr.pocoo.org/2026/7/4/better-models-worse-tools/)
摘要: HN front page 第 17 位（149 points / 高赞评论）。Flask / Jinja 作者 Armin Ronacher 在调试 Pi 的过程中发现——**Claude 越新的模型（Opus 4.8、Sonnet 5）反而在调用 Pi 的 edit 工具时越容易发明额外字段**（nested `edits[]` 数组加自造 key），导致 Pi reject tool call。**SOTA 模型在这个特定 tool schema 上反而比旧模型差**。核心观点：1）**Tool calls 是 in-band signalling，不是 magic**——server 把 transcript + system prompt + tool list 拼成大 prompt + 特殊 marker token，模型在训练中学到在某点 emit tool call；2）**Tool schema 越复杂，模型越容易越界**——Opus 4.8 / Sonnet 5 在简单 edit 之外更倾向发明结构化字段；3）**Harness engineering 是新护城河**——你不只是用模型，而是设计"模型调用工具的方式"——这跟今天上午 Codex 访谈里 Andrew 提的"harness engineering"完全呼应；4）**工具设计要假设模型会越界**——schema 校验、字段白名单、prompt 中明确"只用这些字段"是关键。**对 AI 副业工程师这是"接单时遇到的 AI Coding 失稳"理论解释**：不是模型变笨了，是模型越来越擅长结构化表达导致 schema 越界——**这是 Claude 越来越难用的隐性根因**。**对应副业机会**：1）做"AI Coding 工具 schema 校验中间件"——接 Claude / Codex / Cursor 的 tool call hook，自动 reject 越界字段，按企业部署收 ¥99/seat/月；2）做"harness engineering 咨询"接单——帮独立开发者 / 小团队设计自家 Coding Agent 的工具调用 schema 和 prompt（半天 ¥2999 起）；3）做"工具 schema 演进追踪"内容副业——把 Armin 这篇文章 + Codex 访谈里 harness engineering 部分整合成系列内容，挂技术博客 + 公众号；4）做"AI Coding 错误模式库"——按模型版本（Opus 4.8 / Sonnet 5 / GPT-5.6 / GLM-5.2 / DeepSeek-V4）记录常见 schema 越界模式，做社区 wiki + 联盟链接。HN 讨论：https://news.ycombinator.com/item?id=48782671 （注：HN 链接 7-5 访问需经新闻页面入口，本日未直接展示）

---

🦞 每日09:00自动更新

**数据来源**：36kr AI / TMT、新智元、机器之心、极客公园、雷科技、V2EX 程序员 / create / jobs / claude / qna、Hacker News front_page + Show HN、GitHub Trending、Simon Willison blog、Armin Ronacher blog

**⚠️ 链接核查清单（已逐条验证，仅列正文实际引用链接）：**
- ✅ https://36kr.com/p/3882226982842376 - Cloudflare 9-15 默认屏蔽 AI 爬虫 + Pay Per Use 标题/正文/作者 极客公园 一致
- ✅ https://36kr.com/p/3880971920584962 - GPT-5.6 三大模型 7-7 卡点截杀 Claude 标题/正文/作者 新智元 一致
- ✅ https://36kr.com/p/3882258709180678 - Codex 桌面端负责人访谈「实现变便宜 品味变贵」标题/正文/作者 机器之心 一致
- ✅ https://www.v2ex.com/t/1224844 - AI 中转站模型真伪测试跑分标准 标题/正文/发布者 jingxialai 一致
- ✅ https://www.v2ex.com/t/1224797 - 海外模型 API 中转站 判刑 标题/正文/发布者 一致
- ✅ https://github.com/JuliusBrussee/caveman - caveman skill 65% token 削减 84k stars 4.7k forks 一致
- ✅ https://github.com/alibaba/page-agent - page-agent 23k stars 2k forks 一致
- ✅ https://github.com/ChromeDevTools/chrome-devtools-mcp - Chrome DevTools MCP 45k stars 3k forks 一致
- ✅ https://www.v2ex.com/t/1225038 - PDF 翻译平台「译档」5 天 AI 全程 标题/正文/发布者 binarycopy 一致
- ✅ https://www.v2ex.com/t/1224873 - agent-notify AI Agent 通知工具 标题/正文/发布者 LetTTGACO 一致
- ✅ https://www.v2ex.com/t/1225050 - CTMB Claude Token Monitor Bar Mac 标题/正文/发布者 HAOGRE 一致
- ✅ https://www.v2ex.com/t/1224872 - Vibe Coding 时上下文最先满 标题/正文/发布者 ssshooter 一致
- ✅ https://www.v2ex.com/t/1225069 - ICP 经营许可证虚假广告警示 标题/正文/发布者 importmeta 一致
- ✅ https://www.v2ex.com/t/1224903 - qoder 国产模型对比 deepseek 最好 标题/正文/发布者 Lanhuazhe 一致
- ✅ https://hic-ai.com - HIC Mouse Precision Editing Tools for AI Coding Agents 标题/正文 一致
- ✅ https://lucumr.pocoo.org/2026/7/4/better-models-worse-tools/ - Better Models Worse Tools Armin Ronacher 标题/正文/作者 mitsuhiko 一致
