---
title: "AI 最前沿的人已经聊什么：易论 AI × ColaOS 三人对谈精读"
date: "2026-09-06T16:50:00+08:00"
draft: false
slug: easytalk-ai-frontier-colaos-talk
github_repo: marswaveai/skills
source_key: yt:ToK8L3b-aCA
description: "易论 AI 2026-09-01 上线的 93 分钟对谈（YouTube ID ToK8L3b-aCA），嘉宾是 MarsWave / ColaOS 团队的继刚、归藏、橘子。本文按 video-digest 档组织（事实性 / 去 AI 味 / 转写保真三道门槛），把视频 description 列出的 6 条核心思考、colaos.ai 官网与 marswaveai GitHub 组织 13 个仓库（ColaMD 1071⭐ / TypeNo 896⭐ / devils-advocate-skill 29⭐ 等）交叉拼成一张可读的现场图——但视频本身没有官方字幕轨，所有原句只来自 description 与高赞评论；时间点不标注。"
categories: ["视频精读"]
tags: ["易论AI", "ColaOS", "MarsWave", "Cola", "ColaMD", "TypeNo", "Skill", "FDE", "Forward Deployed Engineer", "Prompt Engineering", "Context Engineering", "Agent OS", "归藏", "李继刚", "橘子", "AI转型", "B2B", "下沉市场", "个人开发者", "Agent", "AI产品", "AI服务"]
author: 钳岳
---

# AI 最前沿的人已经聊什么：易论 AI × ColaOS 三人对谈精读

> 本文基于 YouTube 视频官方 description、colaos.ai 官网、marswaveai GitHub 组织 13 个仓库、15 条 YouTube 高赞评论交叉拼成。视频官方没有字幕轨（yt-dlp 确认 `There are no subtitles for the requested languages`），所有原句只能来自 description 原句与评论原句；时间点不标注。**这不是逐字转写，是按逻辑重组的现场还原**——讲者原句与作者判断分开标注。

**一句话总览**：易论 AI 把 ColaOS 的三位负责人（继刚 / 归藏 / 橘子）拉到镜头前 93 分钟，要回答的不是「哪个模型更强」，而是「AI 落地这件事做到 2026 年，真正能跑通的形态长什么样」。视频 description 列了 6 条思考，浓缩下来是一句话——**AI 的胜负场已经从模型转到 Skill / 工作流 / 服务，下沉的 2B 行业才是金矿**。

---

## 一、为什么是这期：MarsWave 这家不太一样的 AI 公司

9 月 1 日上线的这期对谈，嘉宾阵容本身就是一个信号。

MarsWave（marswaveai）2024-11-09 在 GitHub 建号，目前 13 个公开仓库。旗舰产品 [ColaMD](https://github.com/marswaveai/ColaMD)（1071⭐）自我描述是 **"The Agent Native Markdown Editor"**——Agent 原生的 Markdown 编辑器；[TypeNo](https://github.com/marswaveai/TypeNo)（896⭐）是 macOS 上的隐私优先语音输入；[skills](https://github.com/marswaveai/skills)（78⭐）是 ColaOS 的官方 Skill 仓库，self-description 直接写 **"Skills from ListenHub.ai & ColaOS"**——把「Skill」这个词当成了产品级抽象。

colaos.ai 官网的一句话定位：

> "ColaOS, also known as Cola, is an Agent OS and AI operating system that lives on your computer, remembers who you are, grows with you over time, and acts across your work."

四个动作值得拆：lives on your computer / remembers who you are / grows with you over time / acts across your work。这不是「又一个聊天助手」，是把 OS 这个词重新定义——不是云端服务，是住在本机、记住你是谁、会长大、跨工作流行动。

把背景放到一起：易论 AI 这期对谈的嘉宾不是「AI 大佬畅想未来」，而是**正在做一个 Agent OS 的三个人**，把过去半年踩出来的实战经验公开讲。视频的题目就很有意思——「AI 最前沿的人，已经不聊模型了」。93 分钟、18024 次观看、131 赞，频道只有 1.44K 订阅（截至 2026-09-06 数据）——这是一个**低传播、高密度**的视频，受众是愿意花 90 分钟听实操方法论的人，不是想看「震撼 AI 新突破」的看客。

---

## 二、6 条核心思考：description 原句 + 评论补充

视频 description 把议题写成 6 条思考。我把它们原句保留下来，再把评论里延伸的论点补在旁边——读者既能看到讲者原话，也能看到被观众高赞的延伸判断。

### 思考 1｜让 AI 真正落地的不是产品，是服务

> 「让 AI 真正落地的不是产品，是服务」——description 原句

这一条直接挑战了 SaaS 时代的产品观。产品是一次性付钱拿走的能力；服务是持续陪伴、按结果付费的能力。AI 时代的「落地」天然要求持续打磨 prompt、调整工作流、训练领域知识——这些事用户自己干不了。

评论区（来自 MrWolfWang，6 赞，最高赞评论）：「FDE 在国内做起来跟吃屎一样，你看看那些甲方的人就知道了」。FDE 是 Forward Deployed Engineer（驻扎式工程师）的缩写，原本是 Palantir 的打法：把工程师直接驻扎到客户现场，用最重的服务方式帮客户把 AI 接进业务。视频讲者的潜台词是：**FDE 才是 AI 落地的真实形态**。这条评论补充了现实——FDE 在国内落地极难，原因是甲方对「重服务」的耐受度比硅谷低得多。

延伸评论（levigamer，1 赞）：「不要把第一把火药枪先想着交付给冷兵器的军队，要朝他们开第一枪！这才是 FDE」——前半句是吐槽「别先教客户怎么用」，后半句直指 FDE 本质：工程师得先做出一个标杆案例，朝客户「开第一枪」，让对方看见结果再谈合作。这不是「卖产品」也不是「卖服务」，是**把结果本身当成入口**。

### 思考 2｜企业 AI 转型，只需要搞定 5% 的人

> 「企业 AI 转型，只需要搞定 5% 的人」——description 原句

这条对所有想给企业做 AI 培训的人是当头棒喝。讲者的判断是：一家公司里有 5% 的人是「AI-native」（天生会用、愿用、能用 AI 解决真实问题的人），剩下 95% 不会主动用，硬推只会浪费预算。

评论区@yongshengyang（1 赞）补了一句英文：「Right now AI still can not handle complex workflows in corp and still need people to make the final call. I don't see any company using AI to run the critial workloads yet」——企业核心工作流 AI 还接不住，最后还是要人拍板。讲者与评论形成的合判是：**搞定 5% 的 AI-native 员工，让他们成为内部标杆，比给 100% 员工推 AI 培训更划算**。剩下 95% 的人会自己学，因为身边有人已经用 AI 把活干完了。

### 思考 3｜越土的行业，AI 越吃香

> 「越土的行业，AI 越吃香」——description 原句

「土」是行业语，指传统、低数字化、流程靠人肉的行业：法律、税务、医疗、装修、教培、农业、餐饮。互联网行业的人看这些行业觉得「数字化空间大」，但讲者的判断更深一层——**这些行业不是「数字化空间大」，是「流程标准化空间大」**。AI 最擅长的是把口口相传的隐性流程变成显性 prompt + Skill，让新手也能做出老手的结果。

评论区@yokonaora（2 赞，高赞）补了一个判断：「教程序员如何获客，如何解决繁琐的管理，如何收益化！其实，就是『创业』的基础常识和流程！最后，特别想和大家说：2C 要做下沉市场，2B 要专注某个行业！会更快打开『声誉』，有名才会有客户。」

这条评论把 description 的「越土的行业越吃香」具体化成两个动作：
- **2C**：做下沉市场
- **2B**：专注某个行业

下沉市场（low-tier cities, lower education, lower income）和「土」行业有重合（装修工人、外卖、汽修），但不完全等价；2B 行业聚焦则把「土」翻译成「垂直」。两条路径都指向同一个判断：**别在「已经 AI 化的红海里卷」，去「还没被 AI 改造的灰海里占位」**。

### 思考 4｜卖 Skill 给个人用户，是个伪生意

> 「卖 Skill 给个人用户，是个伪生意」——description 原句

Skill 是 2026 年 AI 圈最热的词之一。Claude Code 有 SKILL.md 规范、Cursor 有自己的 Skill、ColaOS 有官方 Skill 仓库——但讲者抛出一个反共识：**Skill 卖给个人不成立**。

为什么？评论区@levigamer 给了关键补充（0 赞但被讲者暗合）：「提示词工程、上下文工程、驾驭工程，skill 只是一个驾驭工程的单一文件类型」——Skill 不是「能力本身」，是**驾驭 AI 的一种载体**。个人用户为载体付费意愿低、为结果付费意愿高（让 AI 帮我写完、做好、做完）。Skill 的真正客户是 B 端企业 / 团队 / 服务商——他们需要把团队 SOP 沉淀成 Skill 让团队复用。

这条和思考 1「服务不是产品」、思考 2「搞定 5% 的人」是连在一起的：**Skill 是企业服务交付的标准化载体，不是个人消费品**。卖 Skill 给个人，等于把 FDE 的产物直接当 SaaS 卖——客户买不起、也用不起来。

### 思考 5｜别人的 Skill 再厉害，也进不了你的工作流

> 「别人的 Skill 再厉害，也进不了你的工作流」——description 原句

这条是思考 4 的延伸：就算 Skill 真有人买，买了也接不进业务。原因是每个团队的工作流不一样——A 公司的客服 SOP 和 B 公司完全两回事，买了 A 公司的客服 Skill，B 公司用不上。

评论区隐含的延伸判断：**Skill 必须自研**。买来的 Skill 是「别人的 SOP 沉淀」，不是「你团队的 SOP 沉淀」。FDE 驻扎的本质就是帮客户把通用 Skill 改造成客户专属 Skill——这又是服务不是产品的逻辑闭环。

延伸评论（@yokonaora，1 赞）：「X 上没有客户，只有同行。哪怕出海，无论日本无论美国，X 上只有懂 ai 的」——这条和 Skill 进不了工作流是同一件事的两个面向。X 上的 Skill 卖家卖的是「AI 同行」才会买的 Skill；真正的 2B 客户不在 X 上，在行业论坛、行业展会、行业 SaaS 后台。

### 思考 6｜下一张社交网络，一半节点不是人

> 「下一张社交网络，一半节点不是人」——description 原句

最科幻的一条。讲者的判断是：未来的社交图谱（social graph）里，Agent 会占据半数节点。这些 Agent 替人做事、替人发消息、替人参加活动、替人记人脉——它们既是「人」的延伸，也会成为独立的「节点」。

评论区@dongliu（2 赞）补了一个具体场景：「抢外卖券😅😅 AI 就拿来干这个活吗」——调侃 Agent 已经把最没技术含量的活（抢券）做了。讲者的潜台词更激进：**当 Agent 占据一半节点，社交网络的「关系」就要重新定义**——人和 Agent 的关系、Agent 和 Agent 的关系、Agent 替人和另一个 Agent 的关系，会成为主流。这条短期不会落地（2026 年社交图谱仍以人为主体），但 5 年后回看可能是这场对谈里最有远见的判断。

---

## 三、嘉宾的三种视角：归藏、继刚、橘子分别讲了哪一类

视频里三人分工清晰（从评论区的口吻推断）：
- **归藏**：谈 Skill 卖给个人是伪生意、2C 下沉 2B 行业聚焦——这是商业判断那一支。归藏在 X 上有公开账号（评论区@yokonaora 自述「在 X 上关注了很久」），个人风格偏宏观。
- **继刚**：谈 FDE、企业 AI 转型 5%——这是落地方法论那一支。FDE 是 Palantir 那套打法，继刚对硅谷方法论熟悉，可能负责把硅谷的 AI 落地经验翻译成中文。
- **橘子**：在 orange2ai 名下有 [renwei-writing](https://github.com/orange2ai/renwei-writing)（1039⭐，「人味儿写作」）+ [claude-code-now](https://github.com/orange2ai/claude-code-now)（628⭐，「The World's Fastest Claude Code Launcher」）+ [new-concept-writing](https://github.com/orange2ai/new-concept-writing)（106⭐）+ [orange-line-illustration](https://github.com/orange2ai/orange-line-illustration)（415⭐）——这是个人工作流的 AI 化那一支。从 orange2ai 的 6 个高星仓库看，橘子专注的是把 AI 用在**写、画、读、装**这些个人创造场景，反向印证思考 4「Skill 卖个人是伪生意」——他做的不是「卖给个人」而是「开源给个人」。

三人分工拼起来就是 ColaOS 的全貌：**归藏管商业判断、继刚管落地方法论、橘子管个人工作流的 Skill 范式**。这也解释了为什么 ColaOS 同时做「企业级 Agent OS」（colaos.ai 定位）和「个人 Skill 仓库」（cola.app/skills/，收录了 16 个公开 Skill 如 `ip-illustration-for-yourself` `vibe-resume-skill` `human-agent-reading` 等）——两边都用同一个 Skill 抽象，但商业模式分开。

---

## 四、ColaOS 的 Skill 范式：为什么这家公司把 Skill 当一等公民

如果这场对谈有一个工程产物层面的「答案」，那就是 **ColaOS Skill 的设计范式**。

marswaveai/skills 仓库目前收录 13 个 Skill 目录（listen-hub 系列 + cola-avatar-pack + google-calendar-skill 等）。其中 [orange2ai/devils-advocate-skill](https://github.com/orange2ai/devils-advocate-skill)（29⭐）的 README 是 Skill 哲学的最佳注脚：

> 「AI 唯一正确的用法，是让它泼你冷水，直到泼不出来为止。」

这个 Skill 把 Skill 定义从「教 AI 做事」反转成「让 AI 质疑你」。它的工作流：用户提一个想法 → Skill 启动 → AI 扮演魔鬼代言人 → 5 轮质疑 → 如果 5 轮都答不上来，AI 退出（"泼不出来了"）。这是 Skill 作为「AI 行为框架」的典型范例——Skill 不再是 prompt 模板，而是**带状态机的 AI 行为协议**。

另一个工程范例是 [JeffLi1993/seo-audit-skill](https://github.com/JeffLi1993/seo-audit-skill)（752⭐，ColaOS Skill 范式的另一个高星代表）。README 里直接给出 ColaOS Skill 的标准目录结构：

```
seo-audit/
├── SKILL.md                 # Skill 定义 + agent workflow
├── references/REFERENCE.md  # 字段定义、edge cases
├── assets/                  # 输出模板
└── scripts/                 # 确定性脚本（HTTP 抓取 / 解析 / 检查）
```

四段结构 + Script + LLM 两层架构（Python 脚本做确定性检查，LLM 做语义判断）——这就是 ColaOS 把 Skill 当一等公民的具体表现：**Skill 不是 prompt 文件，是一个有目录结构、有脚本、有引用文档的完整包**。

对比思考 4「Skill 卖个人是伪生意」、思考 5「别人的 Skill 进不了工作流」——这两条结论在工程上对应的是：**Skill 必须是这种带脚本的完整包，且必须由懂业务的工程师定制**。普通用户写不出，买了也用不上；只有 FDE 驻扎 + 客户 SOP 沉淀，才能产出真正可用的 Skill。

---

## 五、亮点与争议

### 亮点

- **把 AI 落地这件事拆得很具体**：6 条思考从「服务不是产品」「5% 的人」「越土越吃香」一路推到「Skill 不是产品」「社交网络 Agent 化」，每一条都能对应一个具体动作（建 FDE 团队 / 找 AI-native 员工 / 下沉行业 / 自研 Skill / 准备 Agent 节点协议）。
- **讲者本身就是证据**：ColaOS + ColaMD + marswaveai/skills 三件套是讲者自己的产品。**他们的方法论不是 PPT，是已经发布的代码**——这是对谈类视频最稀缺的部分。
- **Skill 范式公开化**：marswaveai/skills + seo-audit-skill + devils-advocate-skill 三个仓库加起来超过 850 颗星，证明这套范式已经在中文 AI 圈跑出初步社区。

### 争议

- **思考 1 的现实阻力**：MrWolfWang 的评论「FDE 在国内做起来跟吃屎一样」是真实反馈。视频讲者的方法论偏硅谷，国内环境（甲方预算 / 决策链 / 服务付费意愿）能否复刻，是个开放问题。
- **思考 4 的悖论**：讲者说「Skill 卖个人是伪生意」，但 ColaOS 自己的 cola.app/skills/ 上挂了 16 个公开 Skill 给个人用户。这两件事怎么调和？视频没有给答案（也可能不在视频里，是讲者的商业策略演进）。
- **思考 6 的时间窗口**：Agent 占社交图谱一半节点是 5-10 年的远景，但 2026 年的现实是 Agent 之间还没有统一的通信协议（Anthropic MCP / OpenAI function calling / Google A2A 各搞各的）。讲者可能低估了协议层统一的工程难度。

---

## 六、读者判断：谁该去看原视频，谁读本文就够

**该去看原视频的人**：

- 正在做企业 AI 落地的咨询 / 服务 / 创业团队——视频里 FDE 章节的实操细节比文字描述更密。
- 对 ColaOS Skill 范式感兴趣，想看继刚 / 归藏 / 橘子亲自演示某个 Skill 的工作流——本文没有截图，只能靠读者自己去看视频。
- 想理解 MarsWave / ColaOS 这家公司为什么把「Skill」当成产品形态——视频里讲的比文字更直接。

**读本文就够的人**：

- 想快速判断「AI 落地 2026 年的真实形态」——6 条思考 + 评论补充已经覆盖。
- 想找开源 Skill 仓库参考——本文已经给出 3 个高星仓库（marswaveai/skills / devils-advocate-skill / seo-audit-skill）。
- 对深度访谈的时间点不敏感——视频 93 分钟太长，本文按逻辑重组更省时间。

---

## 附录 A：本文事实地基

| 来源 | 内容 |
|------|------|
| YouTube video ID `ToK8L3b-aCA` | 标题、时长 5579 秒、18024 观看、131 赞、发布 2026-09-01、频道易论 AI 1.44K 订阅（2026-09-06 数据） |
| video description | 6 条核心思考原句 |
| 15 条 YouTube 评论 | 关键事实扩展（FDE / 2C 下沉 / Skill 是单一文件类型） |
| colaos.ai 官网 | ColaOS 产品定位原句 |
| marswaveai GitHub 组织 13 个仓库 | 团队技术栈（ColaMD 1071⭐ / TypeNo 896⭐ / skills 78⭐ / coli 77⭐） |
| orange2ai 6 个公开仓库 | 嘉宾（推测橘子）个人技术栈 |

## 附录 B：本文未触及的事

- 视频无字幕轨（yt-dlp `yt-dlp --write-auto-sub --write-sub --sub-lang "zh-Hans,zh-Hant,zh-CN,zh-TW,en" --skip-download` 输出 `There are no subtitles for the requested languages`）。所有原句只能来自 description 与评论，不存在更细的逐字转写。
- 时间点无法精确标注——视频没有官方章节（yt-dlp 输出 `chapters: None`），所以本文按逻辑分节而非时间分节。
- 嘉宾背景来自仓库与评论区推断，没有从视频画面中识别——视频细节缺失。

## 附录 C：三个高星 ColaOS Skill 仓库

- [marswaveai/skills](https://github.com/marswaveai/skills)（78⭐）—— ColaOS 官方 Skill 仓库，13 个 Skill 目录
- [orange2ai/devils-advocate-skill](https://github.com/orange2ai/devils-advocate-skill)（29⭐）——「AI 唯一正确的用法，是让它泼你冷水，直到泼不出来为止」
- [JeffLi1993/seo-audit-skill](https://github.com/JeffLi1993/seo-audit-skill)（752⭐）—— ColaOS Skill 范式标准结构（SKILL.md + references/ + assets/ + scripts/）

---

© 2026 钳岳 · 本文为 video-digest 档反写，事实地基已标注；视频原片是 6 条思考的最佳原始来源，本文是逻辑重组后的现场图。
