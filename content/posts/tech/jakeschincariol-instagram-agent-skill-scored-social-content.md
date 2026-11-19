---
title: "Instagram Agent Skill：给短视频创作装上评分器，把「这条 hook 好不好」变成可测量的数字"
date: "2026-11-20T01:27:19+08:00"
slug: "jakeschincariol-instagram-agent-skill-scored-social-content"
description: "Instagram Agent Skill 是 13 个 Claude 技能组成的账号运营工具包，核心是两个真能跑起来的评分器：26 个 hook 公式的排序脚本与语速节拍表，外加一份五维 AI 味检测面板。本文拆解它的双 hook 设计、评分模型的短板联动机制与语料可编辑设计，并指出它的真实边界。"
draft: false
categories: ["技术笔记"]
tags: ["社交媒体", "AI Agent", "Claude Skills", "内容创作", "文本检测"]
github_repo: "Jakeschincariol/instagram-agent-skill"
source_key: "gh:Jakeschincariol/instagram-agent-skill"
---

## 核心判断

这个项目的 README 有一句话，坦率得少见：

> **十三 Claude 技能来运营一个 Instagram 账号。** 其中一个根据 26 个 hook 公式写你的 Reels，**并在浪费一个 take 之前先给 hook 打分**。

这句话点出了整件事的核心设计取向：**创作类 AI 工具的真正瓶颈不是生成，是判断**。

「给我 10 个开头」很容易，LLM 一秒钟给你 10 个。但哪个能留、哪个是废话、哪个踩了平台雷区 —— 这个判断过去只能靠创作者的直觉，而直觉是不稳定的、不可复盘的、也没法教的。

这个项目的做法是：**把判断外化成能跑的脚本**。

- 26 个 hook 公式不只是模板库，每个都带 `match` 正则，能识别真实世界里找到的 hook，也能写新的；
- `hookscore.py` 给你的候选开头打分排序，指出最弱的那一维；
- `beats.py` 估算每句话念完要多久，堆成时间轴，标出四个「会把 Reel 拍死」的地方；
- `detect.py` 用五个维度给文本的 AI 味打分。

而且它对自己的边界很诚实：**「Nothing gets posted until you say yes. These skills write. You post.」** —— 技能只写稿，发布永远要人确认。

截至 2026 年 11 月 20 日，这个仓库有 7270 stars、1408 forks，Python 为主，MIT 许可，2026 年 9 月创建，11 月 19 日仍在更新。

## 核心洞察：一条 Reel 有两个 hook

这是整个项目最有价值的观察，写在 `hooks.json` 的注释里：

> 一个 Reel 有**两个同时触发的 hook**，而它们不是同一句话：**你开口说的第一句**，和**屏幕上出现的第一句**。口语 hook 大约两秒，画面 hook 大约一秒 —— 因为画面是**先读后听**的。

这个区分改变了写作方式。大多数人写短视频脚本时，开头那句话同时承担「说给谁听」和「让眼睛看」两个任务，结果两头都不讨好：口播太长、字幕太文艺。

这个项目要求**分开写**：

> 口播行和画面行分别写。画面上的那句更短、更直接，**六个词以内**，且不带它不需要的标点。

配套的还有一条容易被忽略的：**第一帧本身也是 hook**。开头 0:00 一个不动的说话脑袋、没有文字没有动效 —— 那是浪费了三个 hook。

`hooks.json` 里 26 个公式的结构也印证了这个思路。每个公式包含：

| 字段 | 含义 |
|---|---|
| `template` | 句式模板 |
| `example` | 填好的例子 |
| `on_screen` | 画面版本 |
| `best_for` | 适合什么场景 |
| `trap` | **它通常是怎么被搞砸的** |
| `match` | 正则，能匹配野外发现的 hook |

`trap` 字段是设计上的一处精妙 —— 它记录的是**失败模式**而不是成功模式。比如「Cost Confession」公式的陷阱是：「假的代价。『它毁了我的Peace of mind』不是数字，人人都听得出来。」

学一个公式，只看模板是不够的 —— 你得知道它什么时候会失败。

## 评分器：短板决定结论

`hookscore.py` 的输出长这样：

```
HOOK RANKING
==============================================================================
->  85.6 STRONG  Nobody tells you that your first 30 reels are supposed to f...
        weakest: SPECIFICITY (75)
    81.4 STRONG  I lost $18,000 because of one missing contract.
        weakest: ADDRESS (70)
    54.4 OK      Stop scrolling if you want to grow on Instagram in 2026 🔥
        weakest: STAKES (70)
        dealbreaker: Opens with "stop scrolling". Asking for attention proves
                     you have not earned it.
     9.6 WEAK    Hey guys, today I wanted to talk about content strategy
        weakest: FRONTLOAD (0)
        dealbreaker: Greeting. Nobody came to the feed to be greeted.
```

输出里有三个东西值得注意：

**第一，评级不是单一分数。** 每个 hook 标出 `weakest` 维度 —— 最弱的那一环。知道「这条 hook 具体弱在哪」比知道「这条 85 分」有用得多。

**第二，有 `dealbreaker` 一类。** 这不是扣分，是**一票否决**。「Stop scrolling...」这条得了 54.4 分（OK），但 dealbreaker 明确写了：以「停下别划了」开头，**要求注意力本身就证明你还没挣到它**。

**第三，`FRONTLOAD (0)`。** 「Hey guys, today I wanted to talk about...」在「前置」这一维直接 0 分，理由是「打招呼。没人是来被打招呼的。」

这三条合起来构成一个有意思的设计：**分数告诉你「有多好」，dealbreaker 告诉你「能不能用」**。这两件事被分开处理了。

## 节拍表：时间轴上的四个杀手

`beats.py` 估算每行的朗读时长，堆成时间轴，标出四个「会把 Reel 拍死」的地方：

1. **hook 超过三秒** —— 前三秒没抓住，后面的都白搭
2. **某个 beat 长到观众会离开**
3. **连续几行没有任何具体内容**
4. **没有回到第一行的 loop**

输出示例：

```
BEAT SHEET  ·  73 words  ·  ~26.6s at 165 wpm  ·  target 30.0s
```

它接受 `--target`（目标时长）和语速参数。**把「这条脚本念完多长」从估算变成计算**，这件事本身就消掉了一整类返工。

## 五维 AI 味检测

`ig-human` 技能里有两个脚本：

```bash
python3 humanize.py draft.txt --report        # 清理并展示改了什么
python3 detect.py draft.txt                    # 五维打分
python3 detect.py before.txt after.txt         # 证明改动量
```

五个维度：

```python
CHECKS = ["BURSTINESS", "SPECIFICITY", "SLOP DENSITY", "FINGERPRINT", "VOICE"]
```

评分逻辑是这段：

```python
overall = statistics.mean(scores) * 0.6 + min(scores) * 0.4
verdict = "PASS" if overall >= 70 and min(scores) >= 55 else (
    "REVIEW" if overall >= 50 else "FLAGGED")
```

**平均分只占 60%，最弱项占 40%。** 代码注释解释了原因：「最弱的那一项拖住结论：一个检测器只需要一个信号就够了。」

这个公式设计比纯平均合理得多。纯平均分会让「其它维度都 90 分、一项 20 分」的文本拿到 74 分通过，但那种文本在现实里恰恰是最容易被识别的 —— 因为那一项就是破绽。**加上 `min(scores) >= 55` 的硬门槛**（PASS 需要所有维度都不低于 55），短板就无法被平均掉了。

底层词库 `slop.json` 的规模值得记一下：**154 个套话词和短语**（含plain-English 替换）、**18 类不可见字符**、**11 种排版替换**、**16 种结构性破绽**。每一类的最后一块是 Instagram 专属的 —— 只在字幕和口播里出现的词汇。

不可见字符那一项值得单说。零宽空格、word joiner、软连字符、BOM、Unicode tag 字符、不可见分隔符、不换行空格、窄空格 —— 键盘不会产生这些字符，但它们能**在复制粘贴中存活，在每个编辑器里都不可见**。这是生成文本里最机械、最容易被查出的痕迹。

`humanize.py` 会把它们全删掉。

## 语料是设计给用户改的

`ig-human` 的 SKILL.md 里有一段很有意思：

> 这个词库**就是用来被你编辑的**。如果用户有某个总是用、但被词库剥掉的词，把它从文件里拿出去。

同样地，`ig-reel` 要求每个用户先建一个 `~/.claude/instagram/voice.md`（语气档案），或者给 AI 三条自己的 Reel 让它反推出来。README 强调：

> 这在其它平台上没那么重要，但在 Instagram 上很重要 —— **因为这些词你得真的念出来**。

`/ig-viral` 技能会写 `~/.claude/instagram/swipe.md`，记录**这个用户自己在当前细分赛道里哪些公式真的有效**。`ig-reel` 的优先级规则是：**这个文件优先于技能内置的默认值**。

这是一条很聪明的降级路径 —— 通用公式库是冷启动，用户自己的数据是长期最优。

## 13 个技能

| 命令 | 做什么 |
|---|---|
| `/ig-reel` | 一个想法变成一条 Reel。三个 hook（来自 26 个公式），打分，然后是脚本、画面文字和带时间的节拍表 |
| `/ig-viral` | 去找出你赛道里真正在跑的东西，按「超过自己账号中位数的倍数」排序，点名公式，写 swipe 文件 |
| `/ig-caption` | 写字幕并 lint。**显示 feed 里实际可见的那 125 个字符**（折叠前） |
| `/ig-carousel` | 轮播贴。封面（决定有没有人划）、逐页文案、1080x1350 文件 |
| `/ig-story` | 每日 story 序列，哪个贴纸干什么活，以及从「先动起来」开始的私信漏斗 |
| `/ig-profile` | 按 12 部分评分表给主页打 100 分制，然后**按「先修哪个」的顺序**重写 |
| `/ig-plan` | 一周计划。发什么、什么形式、什么时候、以及要互动的 10 个账号 |
| `/ig-human` | 去 AI 味。两个真能跑的脚本 |
| `/ig-comment` | 评论别人。九种类型，按帖子实际是什么来选。**绝不「🔥🔥🔥」** |
| `/ig-reply` | 自己帖子下的评论。分成关键词 / 线索 / 实质 / 提问 / 支持 / 噪音六类，然后**按这个顺序**写 |
| `/ig-dm` | 关键词投放、第一条消息、合作邀约，以及**两个**跟进 |
| `/ig-repurpose` | 一个视频 / 播客 / newsletter，变成一周的 Reels 和轮播，每条独立成立 |
| `/ig-audit` | 对已发布内容的复盘。按异常倍数排序，**按触达而不是播放量**发送 |

几个细节体现了作者对平台的实际理解：

- `/ig-caption` 显示的是 **feed 里实际可见的 125 个字符** —— 也就是「展开更多」之前观众真正能看到的部分。
- `/ig-audit` **按触达排序而不是按播放量** —— 因为播放量会被推荐算法放大，触达才是真实的分发效率。
- `/ig-reply` 把评论分成六类并**按这个顺序**写 —— 先回有实质内容的，再回噪音。

## 安装

三种方式：

```bash
# A. 在 Claude 里粘贴
https://github.com/Jakeschincariol/instagram-agent-skill
# 然后说：安装这个技能，确认 /ig-reel 能用。

# B. 手动
git clone https://github.com/Jakeschincariol/instagram-agent-skill.git
cp -r instagram-agent-skill/skills/ig-* ~/.claude/skills/

# C. 作为插件
/plugin marketplace add Jakeschincariol/instagram-agent-skill
/plugin install instagram-agent
```

项目级安装则是把同样的文件夹复制到你自己仓库的 `.claude/skills/`。

**没有 Claude Code 也能用**：把任意单个 `SKILL.md` 粘在聊天框顶部，它就作为一个模式运行。代价是**失去五个 Python 工具** —— 而这正是 `/ig-reel` 和 `/ig-human` 的核心。

## 边界

**它不发布。** 这是设计，也是边界。技能只写稿，发布是你自己的事。

**它不连 Instagram API。** 没有账号接入、没有数据回传、没有自动发布。所谓「运营一个账号」指的是**产出决策辅助**，不是账号自动化。

**评分器测的是形式，不是效果。** `hookscore.py` 评估的是 hook 的结构特征（前置、具体性、赌注、针对感）；`detect.py` 评估的是 AI 味的文本特征。**两者都不预测这条视频会不会爆。** 实际的留存曲线需要真实的发布数据才知道 —— 这也是 `/ig-viral` 和 `/ig-audit` 存在的原因：它们是这套系统里唯一接真实反馈的两个环节。

**公式库会过时。** 26 个公式是作者的经验沉淀，不是永恒真理。平台算法一改，某个公式可能失效。所以 `/ig-viral` 生成的 swipe 文件优先级更高。

**语速估算基于词数。** `beats.py` 用 165 wpm 这类参数估算，实际念稿速度因人而异。它抓的是「这明显太长了」这类量级问题，不是逐帧对齐。

**它带有强烈的个人风格取向。** `voice.md` 机制正是为了让这些默认取向被你的风格覆盖。不建 `voice.md` 就直接用，出来的稿子会带着作者的腔调。

## 采用顺序

1. **先建 `voice.md`**（10 分钟）。复制模板到 `~/.claude/instagram/voice.md` 填好，或者给 AI 三条自己的 Reel 让它写。这步跳过，后面所有产出都是别人的腔调。
2. **先试 `ig-human`**，因为它独立于任何内容类型。拿一段你以前写的文案跑 `detect.py`，看看五维里哪一维最弱 —— 这是最快建立基线的方式。
3. **再玩 `ig-reel`**，用 `hookscore.py --hook "..."` 单独给一句打分，先熟悉评分口径。
4. **然后建 `voice.md` 之外的第二个文件**：`swipe.md` 由 `/ig-viral` 生成。这是让系统越用越准的地方。
5. **最后才上 `/ig-plan` 和 `/ig-audit`**。这两个依赖前面几个产生的真实数据。

## 排查：按现象定位

| 现象 | 先查这里 |
|---|---|
| 脚本跑不起来 | 没有 Claude Code 的话你少了五个 Python 工具；至少要有 `python3` |
| hook 分数总是偏低 | `hookscore.py` 的 `dealbreaker` 行是最有信息量的部分，别只看总分 |
| beat sheet 说时长超了 | `beats.py --target` 显式给目标时长；默认会按速度调整，但先确认你是要 cut 还是要 retime |
| 字幕开头被截断 | `/ig-caption` 显示的就是 feed 实际可见的 125 字符，把关键信息往前放 |
| `detect.py` 报 FLAGGED 但你觉得没问题 | 看 `min(scores)` 是哪一维触发的；PASS 要求所有维度 ≥55，短板无法被平均掉 |
| 词库误伤了你常用的词 | 直接编辑 `slop.json` 把它拿掉 —— 这个文件就是设计给你改的 |
| 内容风格不像你 | `~/.claude/instagram/voice.md` 没建或没填 |
| 评分和你账号的实际表现对不上 | 跑 `/ig-audit` 看真实触达倍数，用它校准 `/ig-viral` 写的 swipe 文件 —— 它优先于内置默认值 |

## 参考

- 仓库：<https://github.com/Jakeschincariol/instagram-agent-skill>
- 技能清单：仓库内 `skills/` 目录（13 个 `ig-*`）
- hook 公式：仓库内 `skills/ig-reel/hooks.json`
- AI 味词库：仓库内 `skills/ig-human/slop.json`
