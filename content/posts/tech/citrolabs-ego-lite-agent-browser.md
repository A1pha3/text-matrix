---
title: "ego lite：让代理住进你的浏览器，而不是再造一个浏览器"
date: 2026-08-02T02:59:48+08:00
slug: "citrolabs-ego-lite-agent-browser"
github_repo: "citrolabs/ego-lite"
source_key: "gh:citrolabs/ego-lite"
description: "citrolabs/ego-lite 是一款 Chromium 系 macOS 浏览器，让人和 AI 代理共用同一份登录态：代理在自己的 Space 里跑任务，不抢你的标签页，并通过 ego-browser 这组页面内 JavaScript 工具直接干活。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Browser Automation", "browser-use", "Mac 工具", "浏览器自动化"]
---

## 一句话判断

`citrolabs/ego-lite`（16,723 stars，2026-10-01 读数）的出发点很直接：**别给代理再造一个浏览器，让它住进你正在用的这个**。它是款 macOS 上的 Chromium 系浏览器——人的标签页在前台，代理的标签页在各自的 Space（浏览器内部的隔离工作区）里跑，双方共用你的真实登录态。代理侧通过 `ego-browser` 这个 skill 接入：它把浏览器暴露成一组页面内 JavaScript 工具，任何 agent CLI 都能直接调用。

这个方向和主流做法相反。过去一年 browser-use 类项目的努力都花在"让代理能控制一个浏览器"上；ego lite 把浏览器本身改了，让浏览器主动给代理腾出位置。

## 系统地图：一个浏览器，三层分工

在看机制之前，先分清这个东西由什么组成。仓库里开源的只有第三层，前两层随 app 免费下载但不开源：

| 层 | 是什么 | 状态 |
|---|---|---|
| **浏览器本体** | Chromium 系 macOS 应用，可从 Chrome 迁移登录、cookie、扩展、书签 | 免费下载，闭源 |
| **ego 运行时** | 浏览器内置的 `globalThis.ego`，管标签页、CDP、快照、Task Space | 免费下载，闭源 |
| **ego-browser skill** | agent 侧的 CLI 和 Node.js 帮助层，把上面两层包装成 agent 能调的 API | 开源，MIT |

官方对架构链路的表述是：`ego-browser (Chromium) → globalThis.ego → helper functions → agent heredoc`。仓库 LICENSE 是 MIT，但 README 结尾专门补了一句："The ego lite browser is a separate, free download."——评估源码可审计性时要注意这个边界。

## 它要替换的是什么

README 开头点名了对手：

> Existing tools like browser-use and agent-browser are a bridge to the browser, not a browser of their own: they need a separate one to drive, your browser data rarely carries over intact, the connection is unstable, and you and the agent end up fighting over control of the browser.

拆开是三重摩擦，都出在"桥接"这个架构选择上：

1. **要另找一个浏览器来驱动**。browser-use 这类框架自己不带浏览器，通常启动独立 Chromium 实例，cookies 不在你的常规会话里。
2. **浏览器数据带不过去**。银行、Notion、Slack 这类对会话敏感的站点发现浏览器画像对不上就拦截，代理只能重来一遍登录，碰上 MFA 直接卡死。
3. **抢控制权**。代理在后台开一堆标签页时，你的前台被挤占；或者反过来，你一切前台，代理的自动化就断了。

ego lite 的回答是砍掉"桥"：一个浏览器进程，人和代理各用各的 Space，登录态天然共享，没有迁移和同步问题。

## 核心机制一：Space 是浏览器内部的隔离工作区

Space 不是操作系统的多窗口，而是同一个浏览器里划出来的隔间。README 的定义是 "isolated workspaces inside the same browser"。

- **每个代理任务一个 Space**。你浏览你的，代理在它的 Space 里开页面、点击、抓取，互不可见对方的标签页。
- **多 Space 并行**。README 给的例子：Claude Code 在 10 个并行 Space 里富化 10 条销售线索，Codex 同时在另外 5 个 Space 抓 5 个竞品网站，互不冲突，也不动你的标签页。
- **随时可接管**。浏览器界面上能看到哪个 Space 正有代理在跑，你可以随时接管或叫停。

注意这里没有任何"macOS 系统层资源隔离"的成分——隔离发生在浏览器内部，系统层面它就是一个普通应用。

## 核心机制二：ego-browser 把浏览器变成一组 JS 工具

`ego-browser` 是 agent 和浏览器之间的连接层。README 的定义：

> It exposes the browser as a set of in-page JavaScript tools: snapshot, fill, click, wait, navigate, capture. The agent writes a JavaScript snippet calling those tools, and `ego-browser` runs it on the page in one pass.

它面向"任何 agent CLI"——Claude Code、Codex、Cursor 或自研的都行。安装 ego lite 时，安装器会把 `ego-browser` skill 写进机器上每个 agent 的 skill 目录。

**运行模型**值得单独说，因为它决定了 token 消耗。代理不是一条条下命令，而是写一段 Node.js 脚本，通过 heredoc 喂给 CLI：

```bash
ego-browser nodejs <<'EOF'
const task = await taskSpace("inspect example page");
const page = task.page("p1");
await page.goto("https://example.com");
console.log(await page.snapshot());
EOF
```

这段脚本跑在 Node.js 里而不是页面里，想读 DOM 得走 `page.evaluate()`。关键在于：**多步操作合进一次脚本执行**。传统 CLI 方式是"调两个命令、看结果、再调两个命令"，每一步都要过一遍模型；脚本方式把一个多步任务压成一次输出。README 称复杂工作流因此完成得更快、成功率更高、单任务工具调用次数和成本大幅下降。

**API 面貌**是刻意收窄的。SKILL.md 原话："Ego-browser deliberately exposes a small custom API. It is not Playwright, even where method names and options look similar."——方法名看着眼熟，但它明确禁止 `import Playwright` 或另开浏览器。核心对象就五个：

- **TaskSpace**：一个任务一个空间，有 `spaceId`，跨轮次持久。每次 CLI 调用都是新的 Node 进程，JS 变量不保留，但 Space、标签页和 Page 标签（`p1`、`p2`……）都在。下一轮拿 `taskSpace(7)` 恢复现场。
- **Page**：观察有 `snapshot()` / `screenshot()`，导航有 `goto()` / `waitForURL()`，操作有 `fill()` / `click()` / `press()`，逃生舱有 `evaluate()` 和 `cdp()`。
- **FileChooser、mouse、keyboard**：canvas、富文本、电子表格这类没有 DOM 语义的界面，退回截图加坐标点击的模式。

**快照系统是它下功夫最深的地方**。README 声称"thanks to customization inside the browser engine"，ego lite 能产出市面上质量最高的页面快照，可靠处理深层嵌套 iframe——这恰好是外挂方案经常翻车的地方。快照输出的是无障碍角色树加节点引用（`@21` 这样的 ref），模型拿 ref 定位元素，语义选择器（`loc=role:button[name='Sign in']`、`text=`、`loc=css:`）做兜底。iframe 有专门的子树快照：`snapshot({ scope: "subtree", root: "@12" })`，返回的 ref 可以直接在框架内操作。

**CDP 没有藏起来，但排在最后**。常规操作走上面的高层 API；封装不住的时候，`page.cdp()` 可以直接发 DevTools Protocol 命令（Page、Runtime、DOM、Network 等），跨标签页的 Target/Browser 命令走 `task.cdp()`。文档同时警告：raw CDP 会让已发的 refs 失效，别把 `targetId` 带到下一轮。

**人机交接是写进协议里的**。代理卡在权限弹窗、设备选择这类只有人能处理的环节时，调 `handOff()` 把控制权交还，结束本轮，等用户在浏览器里做完再恢复同一空间。反过来，用户随时接管时 agent 必须停手，不许绕路重试。任务完成后默认 `finish({ keep: [] })` 收尾——代理创建的页面全关，用户自己开的标签页受保护不动，结果页想留给用户看就 `keep: ["p2"]`。

## 一次真实任务流：让代理帮你下载供应商合同

把"从供应商门户下载 2024 年全部合同 PDF"当成样本，走一遍上面这套机制：

1. 你已经在 ego lite 里登录了供应商门户，MFA 早就完成了。代理什么都不用重新认证。
2. 你在 Claude Code 里说："帮我下载门户上 2024 年全部合同，存到 `~/Contracts/2024/`。"
3. Claude Code 拾取 `ego-browser` skill，开一个 TaskSpace，在自己的 Space 里打开门户页面——你的前台标签页纹丝不动。
4. 第一轮：`page.goto()` 到合同列表页，`snapshot()` 拿到结构化快照，从里面数出 20 份合同的链接。
5. 第二轮：一个脚本里循环处理——逐个点击下载链接，`waitForEvent("download")` 接住下载，`download.saveAs()` 存到目标目录并等写完。
6. 中途门户弹了个二次验证，代理调 `handOff()`，你顺手点掉，它接着跑。
7. 任务完成：`finish({ keep: [] })`，Space 里代理开的页面全部关闭。你从头到尾只看到一次验证弹窗。

换成 browser-use，第 1 步就过不去：它要驱动一个新浏览器，登录态带不过去，MFA 得你来一遍。

## Benchmark 解读：官方自测，看趋势别看绝对值

README 附了 ego lite 对 Vercel agent-browser 的对比：四个复杂浏览器自动化任务，"ego lite finished each task up to 2.5× faster, with substantially fewer tokens. The harder the task, the bigger the gap."数据以图片形式发布，没有公开逐任务的原始数字。

按三步读它：

- **测的是什么**：同一批复杂自动化任务上，两家的端到端耗时和 token 消耗。ego lite 的快来自两处——省掉桥接层的往返（脚本一次执行多步），以及登录态直接复用。
- **数字反映系统的哪部分**：差距主要来自架构差异（浏览器内置 vs 外挂驱动），任务越复杂、步骤越多，往返次数差得越多，所以"越难差距越大"和它的架构叙事是自洽的。
- **不能推出什么**：这是厂商自测，任务集由官方挑选，没有第三方复现；"快 2.5×"不能外推到所有场景，尤其不能推到简单任务（往返开销占比小）。把它当方向性证据就好。

README 还给了一张能力对照表，横向是五款产品（ego lite / Browser-Use / Vercel agent-browser / ChatGPT Atlas / Perplexity Comet）。格局很清楚：Browser-Use 和 agent-browser 是自动化框架，不带浏览器；Atlas 和 Comet 是 AI 浏览器，带浏览器但只认自家内置 agent；「并行多任务」和「可被外部 agent 驱动」两项同时打勾的只有 ego lite。

## 数据留在哪，代理会「变熟练」吗

既然卖点是代理共用你的真实登录态，数据去向是绕不开的问题。README 的口径：浏览数据、cookie 和浏览器持有的一切都留在本机；数据收集刻意收窄，只取简单产品信号，比如「你是否把 ego lite 设成了默认浏览器」。这条声明与「闭源浏览器」叠在一起读更准：承诺无法靠源码审计验证，信不信取决于你对发行方的判断。

另一个值得盯着的方向是经验复用。README 把「experience accumulation」标为 coming soon：官方 skill 会把每次成功的动作提炼成可复用的工具和工作流，同类任务最高提速 5 倍。不过复用的底子已经在代码里了——`ego-browser` 的运行时会从 `learnings/<站点>/` 目录读取站点经验，且每次调用都会生效。也就是说，「代理在这个站点踩过的坑，下一次直接绕开」的机制已有雏形，缺的是把它自动化沉淀的那一层。

## 安装与平台

三种方式，选一个：

```bash
# 方式一：npx 只装 skill，首次跑浏览器任务时引导装 app
npx skills add citrolabs/ego-lite

# 方式二：让 agent 自己装
# 把 https://github.com/citrolabs/ego-lite 丢给 agent，
# 它会读 skills/ego-browser/references/install.md 照做
```

方式三是直接下载 DMG（Apple Silicon / x64 两个架构，链接见仓库 README）。`scripts/install.sh` 做的事：下载对应架构的 DMG、装进 `/Applications`、去掉 quarantine 属性、启动应用。

首次启动有两件事：选择是否从 Chrome（或其他浏览器）迁移数据——同意之后代理继承你的登录、cookie、扩展和书签；onboarding 会把 `ego-browser` 命令注册到 PATH（通常在 `~/.local/bin`）。装完用一句 `command -v ego-browser` 确认。

当前仅支持 macOS。README 口径是 Windows 内测即将开放，Linux 在[路线图](https://lite.ego.app/roadmap)上。完整文档在 [lite.ego.app/document](https://lite.ego.app/document/)。

装好后，使用形态就是在你顺手的 agent CLI 里说人话，比如 README 的示例：`ego-browser follow @ego_agent on x.com for me`。agent 会拾取 skill、在自己的 Space 里打开页面、读快照、执行关注，全程不动你手头的标签页。

## 适用边界

**适合**：

- 已经在用 browser-use / agent-browser，被登录态迁移和 MFA 反复卡住的团队
- 运营、采购、财务这类"让代理帮我在系统里点一堆按钮"的日常诉求
- 想要多个代理并行干活、又不想让它们挤掉自己前台工作的人

**不适合**：

- Windows / Linux 工作站（等 Windows 内测和 Linux roadmap）
- 纯无人值守的 RPA 场景——没有真人要共享登录态时，Playwright 加 headless 更简单
- 期待内置 agent 大脑的人：ego lite 只提供浏览器和接口，不负责"让代理知道该干什么"，大脑是你带的那个 CLI
- 要求全链路开源的团队：skill 是 MIT，浏览器本体是免费但闭源的二进制

## 结尾判断

ego lite 的位置值得记一下。浏览器自动化框架证明了"模型加工具能操作网页"，AI 浏览器证明了"浏览器可以长一个内置大脑"，两条路线各有一块天然短板：框架碰不到你的真实会话，AI 浏览器只认自家大脑。ego lite 选了第三条：浏览器本身给代理腾地方，大脑由用户自带。

要不要现在上，可以按这个顺序判断：如果你的代理工作流已经在跑、且反复被登录态卡住，它解决的问题恰好是你的日常，值得立刻试；如果只是偶尔跑点爬取，现有 headless 方案够用，先等等 Windows 版和生态成熟；如果要评估生产采用，把"浏览器闭源"这一条放进风险清单——skill 层可审计，浏览器本体目前只能信发行版。
