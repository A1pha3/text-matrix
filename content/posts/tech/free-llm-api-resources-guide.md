---
title: "免费额度三个月换一次血，记录它们的清单先删了库"
date: "2026-05-06T20:05:34+08:00"
lastmod: "2026-10-05T12:00:00+08:00"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "API", "开源项目", "资源清单"]
description: "cheahjs/free-llm-api-resources 曾是 GitHub 上最较真的免费 LLM API 清单，2026-08-06 至 09-26 之间被作者删除。本文整理它两年多的完整时间线、2026 年 5 月快照里 13 家免费层与 13 家试用积分层的全部限额数字、清单三个月一轮的换血记录，以及删库之后查免费额度信息的可行路径。"
slug: "free-llm-api-resources-guide"
github_repo: "cheahjs/free-llm-api-resources"
source_key: "gh:cheahjs/free-llm-api-resources"
---

# 免费额度三个月换一次血，记录它们的清单先删了库

GitHub 上最较真的免费 LLM API 清单 cheahjs/free-llm-api-resources 已经删库了。2026 年 10 月 5 日访问仓库地址返回 404，没有留下跳转——不是改名，是删除。删除窗口可以钉在两个快照之间：2026-08-06 的最后一次正常快照显示 29,355 星，2026-09-26 的下一次快照已经是 404。作者账号 cheahjs 仍在活跃，仓库没有留下删除声明或迁移地址，截至本文复核当天，多数搜索引擎还把它收录成"活着"的状态。

这份清单存世两年多，比任何转述都完整地勾勒了"免费 LLM API"这个品类的基本形状：十几家服务商长期提供能走 API 的免费额度，每家的限额以月为单位在变，而记录这些限额的清单自己也没能一直在线。本文整理它的存续时间线、2026 年 5 月快照里的免费层与试用积分层全景、清单换血的节奏，以及删库之后去哪里查这些信息。

## 目录

- [仓库的生卒时间线](#仓库的生卒时间线)
- [它生前为什么值得读](#它生前为什么值得读)
- [免费层全景：13 家服务商](#免费层全景13-家服务商)
- [试用积分层：13 家服务商](#试用积分层13-家服务商)
- [清单三个月换一次血](#清单三个月换一次血)
- [删库之后，去哪里查](#删库之后去哪里查)
- [现在该怎么用免费层](#现在该怎么用免费层)

## 仓库的生卒时间线

| 时间 | 状态 | 出处 |
|------|------|------|
| 不晚于 2024-08-29 | 仓库已创建，当天 45 星 | [现存最早的 Wayback 快照](http://web.archive.org/web/20240829/https://github.com/cheahjs/free-llm-api-resources) |
| 2026-05-04 | 19,747 星 | [Wayback 快照](http://web.archive.org/web/20260504165852/https://github.com/cheahjs/free-llm-api-resources) |
| 2026-08-06 | 29,355 星 | [Wayback 快照](http://web.archive.org/web/20260806034947/https://github.com/cheahjs/free-llm-api-resources) |
| 2026-08-06 至 2026-09-26 之间 | 某日：仓库被删除 | 2026-09-26 快照已 404 |
| 2026-10-05（本文复核日） | GitHub API 返回 404，无重定向 | 作者账号仍在，其余仓库照常 |

两点补充。增长曲线：从 45 星到近两万星走了约二十个月，最后三个月又涨了约一万星，删库时它正处在热度高位。删除方式：GitHub API 返回 404 且无 301 跳转，说明仓库被整体移除而非改名；作者名下仍有几十个公开仓库，2026 年 5 月还有推送记录，账号注销的可能性可以排除。删除的原因，作者没有在任何公开渠道说明，本文不做推测。

## 它生前为什么值得读

免费 API 这个领域一直鱼龙混杂：逆向官网聊天接口拼出来的"免费 GPT"、来路不明的共享 Key、跑路风险极高的"公益站"，都爱用"免费"当招牌。这份清单 README 的第一句话就是准入门槛：

> This list explicitly excludes any services that are not legitimate (eg reverse engineers an existing chatbot)

第二句是它的生存逻辑，也算是对读者的请求：

> Please don't abuse these services, else we might lose them.

它只收录两类东西：服务商官方的永久免费层，和服务商官方发放的注册试用积分。每个条目都写清可核对的限额——每分钟多少请求、每天多少请求、要不要手机号验证、输入数据会不会被拿去训练。比起翻十几家服务商散落的官方文档，它的价值在于口径统一、逐项可比。

结构上是两层：免费层（Free Providers）在 2026 年 5 月收录 13 家，试用积分层（Providers with trial credits）同样 13 家。下文两份全景表的数字，除特别说明外都取自 2026-05-04 的 [Wayback 快照](http://web.archive.org/web/20260504165852/https://github.com/cheahjs/free-llm-api-resources)——这是本文发表时点的清单标准版。

## 免费层全景：13 家服务商

| 服务商 | 限额（2026-05 快照） | 条件与备注 |
|--------|----------------------|-----------|
| OpenRouter | 20 请求/分钟、50 请求/天；$10 一次性充值后升至 1,000 请求/天 | 各免费模型共享同一配额；当时免费模型有 29 个 |
| Google AI Studio | Gemini Flash 线：25 万 tokens/分钟、20 请求/天；Gemma 3 全系：1.5 万 tokens/分钟、14,400 请求/天 | 英国/瑞士/欧经区/欧盟以外使用，输入数据用于训练 |
| Mistral La Plateforme | 每秒 1 请求、50 万 tokens/分钟、10 亿 tokens/月 | Experiment 免费计划需同意数据训练，需手机号验证 |
| Cerebras | 30 请求/分钟、14,400 请求/天、100 万 tokens/天 | 型号 gpt-oss-120b 与 Llama 3.1 8B，两款同限额 |
| Groq | Llama 3.1 8B：14,400 请求/天；Llama 3.3 70B：1,000 请求/天、12,000 tokens/分钟 | 另有 Llama 4 Scout、Whisper、gpt-oss 系列等分档 |
| Mistral Codestral | 30 请求/分钟、2,000 请求/天 | README 并列写着"当前免费"与"按月订阅"两行，需手机号验证 |
| Cohere | 20 请求/分钟、1,000 请求/月 | command-r 系列等，全部模型共享月度配额 |
| NVIDIA NIM | 40 请求/分钟 | 需手机号验证；模型普遍受上下文窗口限制 |
| GitHub Models | 限额随 Copilot 订阅档（Free 至 Enterprise）浮动 | 输入/输出 token 限制极紧；模型阵容含 GPT-4.1、o3、Grok 3、DeepSeek-R1 等 |
| Cloudflare Workers AI | 每天 10,000 neurons | 计量单位是计算单元 neuron，不是 token |
| HuggingFace Inference Providers | 每月 $0.10 额度 | Serverless 推理仅限 10GB 以下模型，热门模型例外 |
| Vercel AI Gateway | 每月 $5 额度 | 按需转发到各家受支持的 provider |
| OpenCode Zen | 未公布统一限额 | 策展型网关；README 注明免费模型可能用数据做改进 |

几个值得单独说的条目。

**额度最大的是 Mistral La Plateforme**：每月 10 亿 tokens，一家把其余十二家甩开一个数量级。代价也写在明面上——要用免费层就得加入 Experiment 计划，同意把数据用于训练，另外要交手机号。把它当个人项目的批处理引擎可以，喂公司业务数据不行。

**Cerebras 的价值在吞吐**：每天 100 万 tokens、每分钟 60,000 tokens，配的是 gpt-oss-120b 这一级的模型，做吞吐型实验比多数免费层都宽裕。

**OpenRouter 是唯一需要花钱的免费层**：不充值每天 50 次请求，只够摸一摸接口；$10 一次性充值（README 原话 lifetime topup，终身有效）把额度提到每天 1,000 次。它收录了当时最多的免费模型——29 个，从 Gemma 3 全系、Llama 3.3 70B 到 Hermes 3 Llama 3.1 405B，适合当横评的入口，代价是所有模型挤同一个配额池。

**HuggingFace 的 $0.10 是象征性的**：每月一毛钱的推理额度，摆明了立场——这里是让你试模型的，不是让你用的。

## 试用积分层：13 家服务商

这一层不提供长期免费，而是注册时发放一次性额度，适合短期验证：

| 服务商 | 额度（2026-05 快照） | 备注 |
|--------|----------------------|------|
| Baseten | $30 | 按算力时长计费，任意受支持模型 |
| Alibaba Cloud 国际站 Model Studio | 每个模型 100 万 tokens | Qwen 系列开源与闭源型号 |
| Scaleway Generative APIs | 100 万免费 tokens | 含 Gemma 3 27B、Llama 3.3 70B、qwen3 系列等 |
| NLP Cloud | $15 | 需手机号验证 |
| AI21 | $10，3 个月有效 | Jamba 系列 |
| Upstage | $10，3 个月有效 | Solar Pro/Mini |
| SambaNova Cloud | $5，3 个月有效 | 含 Llama 3.3 70B、DeepSeek-V3.2、gpt-oss-120b 等 |
| Modal | 注册送每月 $5，绑卡后每月 $30 | 按算力时长计费，任意受支持模型 |
| Novita | $0.5，1 年有效 | 各类开源模型 |
| Fireworks | $1 | 各类开源模型 |
| Nebius | $1 | 各类开源模型 |
| Inference.net | $1，回复邮件调查再加 $25 | 各类开源模型 |
| Hyperbolic | $1 | 含 DeepSeek V3 0324、qwen3-coder-480b 等大型号 |

这张表里最值得注意的是分布：额度从 $0.5 到 $30 差 60 倍，大额度的（Baseten、Modal）按算力时长计费、适合短时间密集测试，小额度的够跑通一次 API 调用。三个月内要用完的（AI21、Upstage、SambaNova）别当长期规划。

## 清单三个月换一次血

免费层的数字保质期有多短，把同一份清单相隔三个月的两个快照放在一起就能看到。2026-05-04 与 2026-08-06 两版对照：

**免费层名单动了刀**：5 月的 13 家里，GitHub Models 在 8 月版中消失（README 对它的备注一直是"限额随 Copilot 档位浮动、token 限制极紧"）；一个新面孔 Kilo Gateway 顶了进来，其余 12 家保留。

**OpenRouter 的免费模型几乎换了一遍**：5 月收录 29 个，8 月只剩 14 个。掉出去的包括 Gemma 3 系列、Llama 3.3 70B、Qwen3 Coder、GLM-4.5-Air、MiniMax M2.5、gpt-oss-120b 和 Hermes 3 Llama 3.1 405B；新进来的有 Nemotron 3 Ultra 550B、Cohere North Mini Code、Poolside Laguna 系列和 Ling 3.0 Flash。三个月前写的任何一份"OpenRouter 免费模型清单"，到 8 月已经对不上号。

**Google AI Studio 的型号线整体上移**：5 月的 Gemini 免费档是 3 Flash、3.1 Flash-Lite、2.5 Flash 与 2.5 Flash-Lite 两代同堂；8 月变成了 3.6、3.5、3 三代 Flash 并列，Gemma 4 的 31B 与 26B A4B 两个型号新增进免费列表（16,000 tokens/分钟），Gemma 3 四档仍在。

额度数字也有变动：Flash-Lite 线从"3.1 一款 500 请求/天"变成"3.5 与 3.1 两款都是 500 请求/天"。方向上 generosity 在涨，但你今天抄下的任何一个数字，都不保证活过下一次模型换代。

这份清单真正的价值也在这里：它每更新一次，就把全行业的免费额度重新盘点一遍。它死了以后，这项工作暂时没有人按同样的节奏做。

## 删库之后，去哪里查

假设你今天想接入免费 LLM API，还按老习惯去搜这份清单，会撞上 404。实际可行的路径是下面几条，按可靠程度排序：

1. **服务商官方定价页**。免费额度的一手来源从来都是各家官网的 pricing 或 rate limits 页面。清单是二手聚合，聚合者的更新永远慢于源头——这是这份清单存在两年也没能解决的问题，只是它死后问题变得更刺眼。
2. **Wayback 快照**。本文引用的两个快照（[2026-05-04](http://web.archive.org/web/20260504165852/https://github.com/cheahjs/free-llm-api-resources)、[2026-08-06](http://web.archive.org/web/20260806034947/https://github.com/cheahjs/free-llm-api-resources)）都在线，可以看到删库前的完整清单。查历史限额、对比某家免费层的变化，它仍是最好的档案。
3. **接棒者清单**。截至 2026 年 10 月，同类项目里 star 最高的是 [mnfst/awesome-free-llm-apis](https://github.com/mnfst/awesome-free-llm-apis)（9,183 星，2026-10-04 仍有提交），此外还有 CYBIRD-D/FREE-LLM-API-Provider（112 星）、nherx/free-llm-api-resources（31 星）等在活跃更新。它们与原清单没有 fork 关系，收录口径也更宽松，用之前值得先读一遍它们的收录标准。
4. **早期形态的 fork 残留**。GitHub 上还有一个 [jtig37/free-llm-api-resources](https://github.com/jtig37/free-llm-api-resources)（86 星），是原仓库 2024 年 8 月的 fork——原仓库删除后，fork 关系解除，它成了独立仓库停留在原地。想看这份清单刚起步时的样子（当时还是 Groq 主导的表格形态），只有这里能看。

## 现在该怎么用免费层

把上面的事实压成几条可执行的建议：

1. **免费层当评测台，别当生产资源**。最大的免费额度（Mistral 10 亿 tokens/月、Cerebras 每天 100 万 tokens）够个人项目跑批，但都拴着条件：数据训练条款、手机号验证、严格的速率限制。生产流量走付费层。
2. **任何具体数字只信你读到的那一天**。本文的数字标了"2026-05 快照"的就是那个时点的口径，接棒清单的数字同理。额度表的生命周期以月计。
3. **试用积分用于一次性验证**。三个月内烧完的额度（AI21、Upstage、SambaNova）适合集中做一轮模型选型，别把业务流程搭在上面。
4. **看清楚"免费"的对价**。Google AI Studio、Mistral Experiment、OpenCode Zen 的免费层都以数据训练为条件，NIM 和 NLP Cloud 要手机号。敏感数据不过免费层，这一条没有例外。
5. **定期回官方渠道核对**。免费层条款随时会动，本文写作时点的快照只是入口，不是担保。

最后回到这份清单本身。它生前是品类里最较真的一个：只收官方渠道、逐项写限额、明确标注数据训练条款，两年攒下近三万星。它用删库证明了自己反复提醒读者的那件事——免费的东西随时会消失，包括免费信息的聚合者。往后查免费额度，官方定价页是唯一的稳定锚点；任何清单，包括本文，都只是某个时间点的快照。

## 参考资料

- [Wayback 快照 2024-08-29（45 星，最早存世快照）](http://web.archive.org/web/20240829/https://github.com/cheahjs/free-llm-api-resources)
- [Wayback 快照 2026-05-04（19,747 星，本文引用的主要口径）](http://web.archive.org/web/20260504165852/https://github.com/cheahjs/free-llm-api-resources)
- [Wayback 快照 2026-08-06（29,355 星，删库前最后正常快照）](http://web.archive.org/web/20260806034947/https://github.com/cheahjs/free-llm-api-resources)
- [jtig37/free-llm-api-resources（原仓库 2024-08 的 fork 残留）](https://github.com/jtig37/free-llm-api-resources)
- [mnfst/awesome-free-llm-apis（当前品类 star 最高的接棒清单）](https://github.com/mnfst/awesome-free-llm-apis)
