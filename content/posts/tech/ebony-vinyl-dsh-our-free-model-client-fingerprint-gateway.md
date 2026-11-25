---
title: "dsh-our-free-model：一份把「免密免费模型」当协议工程来做的东西"
date: "2026-11-25T13:34:32+08:00"
slug: "ebony-vinyl-dsh-our-free-model-client-fingerprint-gateway"
description: "dsh-our-free-model 是 DeepSeek Harness 的插件，用免登录通道提供前沿模型，并把免费车道的客户端指纹逆向到逐字节级别。本文拆解它的指纹门控、额度断路器、降级链与 RTK 压缩。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "LLM 网关", "逆向工程", "JavaScript"]
github_repo: "Ebony-Vinyl/dsh-our-free-model"
source_key: "gh:Ebony-Vinyl/dsh-our-free-model"
---

## 核心判断

GitHub 上「免费用前沿模型」的插件不少，但大多数止步于「代理转发 + 改 base URL」。这个项目（[Ebony-Vinyl/dsh-our-free-model](https://github.com/Ebony-Vinyl/dsh-our-free-model)）不一样的地方在于：**它把上游的客户端指纹当协议来逆向，并且把逆向结果写成了一份逐字节可复现的规格。**

上游 OpenCode 的免费车道不对普通 HTTP 客户端开放，只认「长得像官方客户端」的请求。2026 年 10 月 13 到 14 日之间，上游全线返回 `403 {"type":"error","error":{"type":"FreeTierError"}}`——但官方客户端照常可用。

项目的应对方式不是换 Key、不是加代理，而是**用 TLS 中间人抓官方客户端的真实请求，再做逐字节重放做单变量对照**：从真实请求出发，每次只删或改一项，记录 200 还是 403。

文档 `docs/free-lane-wire.md` 记录了 v1 时代的结论：

| 维度 | 实测结论 |
|---|---|
| 端点 | `https://opencode.ai/inference/v1/chat/completions`（`/zen/v1/…` 即使其余全对也 403） |
| 会话头 | `x-opencode-session-id` 必须存在，值与 `x-opencode-session` 相同 |
| 会话 id 形状 | `ses_` + 12 位 hex 必须呈现**铸造**形状（低 12 位约 `0xFFE`），sha256 派生或随机 hex → 403 |
| 工具指纹 | `bash` 与 `read` 必须同时声明，且各自参数 schema 至少有一个 property |
| User-Agent | 含 `deepseek-harness` → 403 |

上游在 10 月 14 日前后把免费车道换成了 OpenCode v2 客户端的形状，v1 的四项特征**逐一失效**；项目在 10 月 16 日按 v2 重做，两侧实现（`src/upstream.js` 与 vendored 的 `vendor/channel-pack/src/opencode*.ts`）保持同一套形状。v2 的变化是：UA 必须是完整的 `opencode/latest/2.0.26/cli`（整串匹配，不接受前后缀）、去掉 `x-opencode-request` 改带 `x-session-affinity` / `x-session-id`、工具门从四个名字变成 `read` 与 `shell` 两个且**描述与参数 schema 必须与官方客户端逐字一致**、以及 `tool_choice: 'none'` 直接 403。

这份文档还诚实地标注了证据来源的差异：v2 的逐项对照「以 9router 的实测为准，本机未重测」——因为本机复测时对话请求恰好被 `429 FreeUsageLimitError` 挡住（retry-after 约 12 小时）。这种把「我验证了什么、没验证什么」分开写的做法，在开源项目里不多见。

需要说清楚的边界，这一条最重要：**这个项目做的是「用官方客户端的形状访问官方给的免费通道」，不是绕过付费墙**。免费车道是上游公开提供的，闸门只是防止非官方客户端滥用。仓库自己的免责声明把项目定性为「个人学习与技术研究项目」，并明确列出了不提供的渠道和用户责任。

截至 2026 年 11 月 25 日，这个仓库有 86384 stars、2444 forks，JavaScript 为主，41 位贡献者，57 个 tag。根目录 LICENSE 是 MIT，但 GitHub 的许可证识别把它归为 `NOASSERTION`（因为该文件还内联了第三方许可证全文），`gh repo view` 里的 license 字段因此显示 "Other"。2026 年 9 月 24 日创建，11 月 24 日仍有合并提交。

## 它到底是什么：一个 dsh 插件，不是一个独立应用

先把形态说清楚，否则后面所有的机制都看不懂。

**dsh** 是 DeepSeek Harness——一个开源的终端 agent 宿主。插件清单 `catalog/dsh-plugin.json` 里的 schema 地址指向 `Yan-Zero/dsh-std`（该仓库现重定向到 `T-Auto/dsh-std`，正式名是 DSH Plugin Interoperability Meta-Protocol，即 DSH 插件互操作元协议）。这个项目是**挂在 dsh 上的插件**，不是独立应用。装到 dsh 里，dsh 的模型选择器就会多出一个分组。

但它同时在做两件额外的事：

一是提供了 `packages/standalone`——不需要 dsh 的独立本地服务（`npm run start:standalone`，默认端口 18900，数据目录 `~/.our-free-model`，自己生成 API Key）。仓库的 README 明确标注：**独立安装制品尚未发布**，目前只能从完整源码仓库运行。

二是把一个 Go 写的引擎（magpie）作为**固定版本**嵌进来。`vendor/magpie/engine.json` 记录了上游 revision `3bf298e70a59`、构建命令和 Go 版本，NOTICE 里写明只打了一个补丁（`0001-agent-sync-skip-an-empty-catalog.patch`：目录为空时跳过写入，而不是清空 agent 的模型列表——一个没有 provider 的引擎绝不该把已接线的 agent 的选择器清掉）。

这一点值得单独指出：这个仓库把另一个 4 万 star 的 Go 项目的**二进制**作为 vendored 依赖带进来，并且自己打补丁控制它。这在开源项目里是少见的做法，也直接决定了本文后面要讲的安全边界。

## 三层结构

| 层 | 职责 | 位置 |
|---|---|---|
| 车道（lane） | 每个具体上游来源：匿名免费道、EAC、Kilo、十个账号渠道、77 家自带 Key 的聚合渠道 | `src/accounts/`、`src/providers/`、`vendor/channel-pack/` |
| 适配层 | 把统一的请求形状翻译成各上游要求的形状 | `src/o2a/`、`src/upstream.js`、`src/http.js` |
| 网关层 | 本地 HTTP 服务，暴露 OpenAI 兼容 + Anthropic Messages 接口 | `src/forward.js`、`src/gateway-keys.js` |

三个值得展开的机制在下面。

## 机制一：客户端指纹闸门

这是项目的技术核心。前面表格里的规则，最终都要落到两个函数上：

**`mintSessionId()`** 负责造会话 id。规则是 `ses_` + 12 位 hex + 14 位 base62。那 12 位 hex 不是随机的——上游会解码它，检查里面的 seq 必须很小（实测 0–16 通过，≥100 拒绝），且低位要呈铸造形状。实现用 `~(ms·0x1000+seq)` 这样的位运算生成，每毫秒归零，天然满足。

**`applyFingerprint()`** 负责注入工具定义。v2 的做法是：注入官方 `read` / `shell` 的定义（逐字，一字不改），把调用方自己同名但定义不同的工具改名成 `<name>_client[N]`，在响应侧还原回来，历史里的同名调用一起改名，注入后补一句「别调它们」的系统提示，并兜底清除 `tool_choice: 'none'`。

仓库的 LICENSE 附录解释了这套资产从哪来：

> 「免费车道必须逐字复现官方 OpenCode 客户端的请求体，因为免费层对它做指纹识别。因此有两个资产从一个固定的上游 tag 逐字生成并内联进 `src/o2a.js`」

分别是 `packages/core/src/session/runner/prompt/system.txt` 和 13 个 `packages/core/src/tool/plugin/` 下的文件，来源 tag `v2.2.3`，由 `scripts/fetch-opencode-assets.mjs` 拉取。LICENSE 里有一句警告很实在：

> 「不要手工编辑它们——被改写过的描述会得到 `429 FreeUsageLimitError`，那读起来像配额墙，而不是形状错误。」

也就是说，形状错了不报形状错，报配额错。这也是这类逆向工作的真实处境。

## 机制二：额度断路器

免费车道按**出口 IP** 计配额。撞到 429 之后的正确做法是停下来，而不是继续撞墙。

项目的行为（README 与 issue #708/#767 的完整回答一节）：

- 一次真实 429 即**开窗**，`Retry-After` 缺省 6 小时
- 窗口内本地拒绝新回合，不再向墙上送请求
- `FreeTierError` 单独锁道
- 状态从**真实回合被动学习**——手动测试全部保留（清单刷新、单模型检测、测速），但自动探测禁用
- 车道可配独立出口代理（http/https/socks5），也认 `HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY`
- 「换出口后重试一次」一键清窗，「测试出口」打第三方回显不花配额

「从真实回合被动学习」这条设计很聪明——自动探测会把配额烧光，所以状态只能从真实流量里长出来。

## 机制三：降级链与 RTK 压缩

**降级链**把任意车道的模型串成一条命名链，以 `combo:<name>` 作为虚拟模型出现在选择器和网关上。两种策略：`fallback` 固定从链首开始，`round-robin` 轮换起点并连续 N 轮粘滞。

一个关键细节：

> 「链接在输出任何正文之前失败会被整段丢弃，切换对调用方不可见；思考增量不算正文，因此『想了很久才撞上配额墙』正是降级最有价值的场景。」

思考增量不算正文——这意味着一个 agent 思考了 30 秒然后撞墙，此时切换到另一个模型接管，agent 那边看不到任何断裂。

**RTK（工具输出压缩）**在请求发出前就地重写 `tool_result`：git diff / status / log、grep、find、ls、tree、构建日志、编号转储、搜索清单、重复日志行。README 给了一个实测数字：**40 KB 的 `git diff` 移除 90% 的字节，且模型仍能就它作答**。

「模型仍能就它作答」这半句是关键——压缩不是无损的，但压缩后的 diff 仍然可回答问题。这个数字来自项目自己的测量，不是第三方基准。

除此之外还有提示词瘦身（caveman 与 ponytail 两族，默认全关）和五个不占用上游请求的本地应答。

## 一个请求的完整旅程

假设你在 dsh 里选了一个模型，输入「帮我看看这个 diff」。

**第一步：模型选择器分组。** 选择器按来源分组：`Our Free Model`（当前出口可直接用）、`Our Free Model · region-limited`（上游对本地地区不放行但保留可见）、`不在选择器中`（上游声明了但网关明确拒绝路由，保留记录并注明拒因）。

**第二步：决定思考强度。** 声明了思考档位的模型（DeepSeek V4.1 Flash、GLM 5.3 Flash）给出自己的档位菜单（Off / Low / High / Max 等），选中值按原值下发到上游 `reasoning_effort`——上游会校验这个字段，集合外的取值直接 400。没有档位菜单的模型走预算阶梯：Light / Balanced / Deep 对应输出 token 预算 2048 / 8192 / 模型上限。

**第三步：出口检查。** 如果当前出口 IP 在断路器窗口内，本地直接拒绝，不发请求。

**第四步：指纹装配。** 请求形状按 v2 规格组装：UA 用 `opencode/latest/2.0.26/cli`（整串，不拼接归属信息），带 `x-opencode-session` / `x-opencode-session-id` / `x-session-affinity` / `x-session-id` 四个同值头，`authorization: Bearer public` 保留，`tool_choice` 绝不下发 `none`。

**第五步：工具定义注入。** 调用方的工具里如果有 `read` 或 `shell` 同名但定义不同，注入的官方定义会把它们改名成 `read_client0` 之类；响应侧再改回来。历史里的同名调用也一起改名。

**第六步：SSE 嗅探。** 网关在高负载下会以 `application/json` 的 content-type 返回完整的 SSE 帧序列。插件按**响应体形状**判定，把已嗅探的字节重新注入流——不会导致整轮失败，也不会因 header 与实际内容不符而把可用模型判为不可用。

**第七步：RTK 压缩。** 如果这次请求带了工具结果，`tool_result` 在发出前被就地重写。

**第八步：记账。** Token 热力图、总量曲线、输出速度、首字延迟，全部留在本机。

## 三个绕不开的边界

### 一、免费不等于没有代价

上游在自己的模型卡里声明：**prompt 可能被记录用于改进服务**。README 明确提醒「请勿发送敏感内容」。

项目的应对是隐私遮蔽和本地转发（凭据不出宿主进程），但这些解决的是「你的 Key 会不会泄漏」，解决不了「你的 prompt 会不会被上游拿去训练」。这两件事必须分开看。

### 二、指纹随时会失效

这不是一个能长期稳定的接口。v1 的四项特征在 10 月 14 日前后全部失效，v2 的实现依据是另一个项目（9router v0.5.104）的实测，且**本机未重测**。上游改一次指纹，这份代码就要跟一次。

从工程角度看这不是缺陷——项目把每次形状变化都写成了带日期的文档（`docs/free-lane-wire.md` 的 v1 段标 2026-10-14，v2 段标 2026-10-16），这本身就是应对方式。但读者要清楚：**你在依赖一个随时会变的接口**。

### 三、LICENSE 里的那段自白

仓库的 LICENSE 有一段关于第三方材料的说明，值得原样看：

> 「本项目自己的验证记录也是同样的说法：`src/o2a/SYNC.md` 记录了历史源码被阅读过，因此不能声称是 clean-room——这些重写是由读过先前实现的人写的。正因如此，这一段把这种关系直白地讲出来，而不是声称独立于先前的阅读。」

这是一段罕见的技术诚实：项目没有掩饰自己的实现路径，而是把它写进了 LICENSE。

项目自身的定性也写在 `src/disclaimer.js` 里：

> 「本插件是一个个人学习与技术研究项目，用于学习模型网关、协议适配与本地路由的实现方式，按『现状』提供，不构成任何商业服务或产品承诺。」

同一份代码里还写明：**不提供 WorkBuddy 国内版、WorkBuddy 国际版、华为云 Huawei Cloud MaaS** 三个渠道，并说明这是在管理边界机械排除的，不是故障，后续更新不会重新引入。

## 适合谁

**值得看的原因**：如果你在做 agent 网关、协议适配或多账号路由，这个项目的指纹逆向方法论（TLS 中间人 + 逐字节重放 + 单变量对照）本身就是一份可复用的技术文档；它的断路器设计和「从真实回合被动学习」的状态机思路可以直接借鉴。

**可以照抄的部分**：RTK 的工具输出压缩思路（模型仍能就压缩后的 diff 作答）、降级链里「思考增量不算正文」的切换时机、指纹探针的测试写法。

**不建议直接依赖的部分**：免费通道本身的可用性（取决于上游和你的出口 IP）；把它当生产环境的模型来源。

**需要先想清楚再装的**：它会读你的 dsh 配置、会管理你的账号凭据、会嵌入并打补丁一个第三方二进制引擎。

## 装起来要做什么

插件装进 dsh 后重启一次应用就行。命令行装法：

```sh
dsh plugin --profile web add /绝对路径/dsh-our-free-model
```

`--profile` 填实际在用的 profile 名。

**但先看这条警告**：npm 上那个裸包的 `dsh-our-free-model` **不是本仓库发布的**。它由第三方打包，`index.js`、`client.js` 被改动，还多出一个本仓库从来没有过的 `src/channel-visibility.js`——装到它拿不到审核过的构建，也拿不到签名清单校验与应用内升级。本仓库发布的是带 scope 的 `@ebony-vinyl/dsh-our-free-model`，与 Release 的 `dsh-our-free-model-<版本>.tgz` 同源同版本：

```sh
dsh plugin --profile web add @ebony-vinyl/dsh-our-free-model@2.9.0
```

包名带 scope，所以挂载条目是 `@ebony-vinyl/dsh-our-free-model`，跟上面的裸包名本地安装方式不能混用（同一个 profile 里只选一种）。

不想装插件、只想要服务，那走独立版：

```sh
npm run start:standalone
# 也可指定端口和数据目录
npm run start:standalone -- --port 18900 --data-dir /path/to/ofm-data
```

启动会打印一次性的管理链接（10 分钟内有效、只能兑换一次）、实际 API 地址和密钥文件位置，**不打印 API Key**。

## 维护节奏：版本号里的信息

项目的发版节奏是「小版本 + 频繁迭代」：写作时点最新的是 v2.9.0，往前是 v2.8.9（11-20）、v2.8.6（11-18）——三天两个版本。每个 release 的标题直接写着这次改了什么，比如 v2.9.0 是「免费车道出口池、429 窗口封顶、官方工具名收紧」，v2.8.9 是「反馈页验证地址收紧、渠道风控止损与流式修复」。

这个节奏本身就说明了一件事：**上游的指纹一变，这个项目就得跟一次**。v2.9.0 标题里的「官方工具名收紧」正是指纹层的调整。所以升级它不只是拿新功能，更是追上游。

另外注意 release 列表里还有一类标注：「非官方社区构建 / unofficial community build」——那是为 macOS arm64 单独做的社区打包，与上游发布线分开。选构建时要认准版本线。

仓库的 `docs/` 下有 `ci-required-checks.md` 和 `contributor-ci-signing.md`，说明贡献链路上有 CI 检查和签名要求，这对参与修改的人是有用的信息。

## 排查：按现象定位

| 现象 | 先查这里 |
|---|---|
| 请求返回 403 `FreeTierError` | 不是配额，是形状不对；对照 `docs/free-lane-wire.md` 查端点路径、会话头、会话 id 形状、工具指纹、UA |
| 请求返回 429 `FreeUsageLimitError` | 有两种可能：真配额耗尽，或资产被改写过（描述变了会报得像配额墙）；先确认 `src/o2a/assets/` 里的文件与上游 tag 一致 |
| 模型能选但选不上 | 看它在「不在选择器中」分组里的拒因；上游声明了但网关拒绝路由的模型会移到那里 |
| 地区的模型全被拒 | 属于 region-limited 分组，可见但被隔离 |
| 自动探测不跑了 | 这是设计：断路器状态从真实回合被动学习，自动探测会烧配额；手动测试（清单刷新、单模型检测、测速）仍可用 |
| 换个出口还是 429 | 断路器按出口 IP 计配额，换 IP 不会自动清窗；用「换出口后重试一次」手动清 |
| 思考强度选了没生效 | 走预算阶梯的模型看的是输出 token 上限（设置页每张模型卡都标了实际下发的上限）；走档位菜单的模型才有 `reasoning_effort` |
| 某些模型没有 Off 档 | 上游强制思考（关闭请求返回 400）或自动路由不透传关闭，菜单里就不含 Off |
| SSE 解析失败 | 上游高负载下会用 `application/json` 的 content-type 返回 SSE 帧序列；插件按响应体形状嗅探，如果仍失败先查版本 |
| npm 上装的包内容不对 | 裸包名 `dsh-our-free-model` 不是本仓库发布的，要装带 scope 的 `@ebony-vinyl/dsh-our-free-model` |
| 独立服务启动不了 | 默认端口 18900、数据目录 `~/.our-free-model`；异常退出后锁文件残留时先确认旧进程已停 |

## 参考

- 仓库：<https://github.com/Ebony-Vinyl/dsh-our-free-model>
- 指纹规格文档：仓库 `docs/free-lane-wire.md`（v1 段标 2026-10-14，v2 段标 2026-10-16）
- 官方客户端资产说明：`docs/opencode-assets.md`
- 插件市场仓库：<https://github.com/Ebony-Vinyl/ofm-extensions>
- 独立服务说明：仓库 `packages/standalone/README.md`
- 宿主 dsh 互操作元协议：<https://github.com/T-Auto/dsh-std>（插件清单里的 schema 地址仍指向旧名 `Yan-Zero/dsh-std`，会重定向过去）
- 本仓库其它相关文章：`9router`（给 AI 编程工具套一层免费用量的路由）——同为免费用量路由，但形态是单点中转，本文讲的是「逆向客户端指纹 + 免登录多渠道 + dsh 插件形态」；`anomalyco/opencode` 是官方客户端本身
