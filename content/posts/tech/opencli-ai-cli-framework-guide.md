---
title: "OpenCLI：把 Agent 的工具入口收成一棵命令树"
date: "2026-05-17T09:10:00+08:00"
lastmod: "2026-09-19T10:40:00+08:00"
slug: "opencli-ai-agent-browser-cli-framework"
github_repo: "jackwener/OpenCLI"
source_key: "gh:jackwener/OpenCLI"
description: "OpenCLI 把站点适配器、登录态浏览器、Electron 应用和本地 CLI 收进同一棵命令树。理解它，要先看命令优先、Browser Bridge、三层会话模型，以及哪些场景其实不该用它。"
summary: "OpenCLI 不只是 browser 子命令。更顺的用法是先查适配器命令，缺口再退到 browser 原语；用 profile、browser session、siteSession 分别处理身份、流程和站点页生命周期；重复出现的流程，再沉淀成 adapter、plugin 或 external CLI。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "CLI", "浏览器自动化", "Electron"]
---

<!-- markdownlint-disable-file MD003 MD041 -->

## 快速信息卡

| 项目 | 信息 |
|------|------|
| 仓库 | [jackwener/OpenCLI](https://github.com/jackwener/OpenCLI) |
| Stars / Forks | 29,441 / 2,875（2026-09-19 取自仓库元数据） |
| License | Apache-2.0 |
| 语言 | JavaScript（TypeScript 源码，发布产物在 `dist/`） |
| 包名 | `@jackwener/opencli`，可执行文件 `opencli` |
| 命令规模 | 官方适配器覆盖 179 个站点，`cli-manifest.json` 收录 1,366 条命令 |
| 本文核对版本 | v1.7.22（2026-05-15 发布）与 v1.8.8（2026-08-31 主干）双向比对 |

OpenCLI 把三类原本分散的能力收进同一棵命令树：站点网页操作、Electron 桌面应用、本机已有的二进制工具。入口收在一起之后，正确用法就有了顺序——先查现成命令，有缺口再退到浏览器原语，最后把重复出现的流程写回命令面。

它和 Playwright 的分工也在这里拉开。Playwright 擅长测试、断言、隔离环境和可重复的浏览器脚本；OpenCLI 处理另一类问题：真实登录态里已经能做的事，怎样变成一条人和 Agent（智能体）都能调用的命令。前者把浏览器当测试运行时，后者把浏览器、桌面应用和本地二进制工具收进同一个调用面。

把 OpenCLI 放进工具链前，与其背浏览器子命令，不如先回答 4 个问题：这件事有没有现成适配器命令？什么时候才退到 `browser` 原语？`--profile`、`browser <session>`、`siteSession` 三层状态各管什么？它和官方 API（应用程序接口）、Playwright、外部 CLI（命令行工具）的职责边界在哪里？

## 目录

1. [先看系统地图](#先看系统地图)
2. [命令优先是核心设计](#命令优先是核心设计)
3. [三层状态模型](#三层状态模型)
4. [Browser Bridge 的边界](#browser-bridge-的边界)
5. [一次任务怎样从网页动作沉淀成命令](#一次任务怎样从网页动作沉淀成命令)
6. [排障先看边界](#排障先看边界)
7. [适用边界](#适用边界)
8. [推进顺序](#推进顺序)
9. [接手前先验这五件事](#接手前先验这五件事)
10. [结语](#结语)

## 先看系统地图

OpenCLI 收拢的是工具入口和调用顺序，底层协议并不只有一种。

| 你面对的能力 | 首选入口 | 保留的状态 | 更适合谁 |
| --- | --- | --- | --- |
| 已有站点命令 | `opencli <site> <command>` | 命令 schema（模式）、输出列、退出码 | 人和 Agent |
| 临时网页操作或站点缺口 | `opencli browser <session> ...` | 命名 browser session、tab lease、当前目标页 | Agent，也适合调试 |
| 本机已有命令行工具 | `opencli gh ...`、`opencli docker ...` | 原生 stdio、原生退出码、统一发现面 | 人和 Agent |
| Electron / 桌面应用 | `opencli cursor ...`、`opencli codex ...` | CDP（Chrome DevTools Protocol）目标、桌面应用当前状态 | 人和 Agent |

这张表最该看的是"首选入口"这一列。OpenCLI 的推荐顺序是先找现成命令，命令有缺口才退到浏览器，再把反复出现的浏览器流程收敛成新命令。跳过第一步直接从 `browser` 原语开始，得到的就是一组跟着站点前端改版一起失效的脚本。

## 命令优先是核心设计

OpenCLI 把命令发现做成了运行时可查询的注册表，而不是藏在 README 里的功能清单。对 Agent 来说差别很实际：先枚举，再调用，少靠猜。

安装分两条路。npm 装的是纯 CLI，要求 Node.js >= 20.18.1；macOS / Windows 还可以装 OpenCLIApp 桌面端，由它在系统托盘里托管 `opencli` 命令的安装、诊断、更新、浏览器登录保活和网页转 Markdown。CI 和服务器一般走 npm。CLI 就位后装上 Browser Bridge 扩展，再验证连通性：

```bash
node --version
npm install -g @jackwener/opencli
opencli doctor
```

多 Chrome profile 的环境下，下一步是给 profile 起别名（见后文三层状态模型）。之后先看命令面：

```bash
opencli list
opencli list -f json
opencli hackernews top --limit 5 -f json
```

`opencli list -f json` 输出的是注册表本身。每一条命令都由 `serializeCommand()` 展开成固定字段：`command`、`site`、`name`、`aliases`、`description`、`access`、`strategy`、`browser`、`args`、`columns`、`domain`、`example`、`defaultFormat`、`siteSession`。下面挑出其中几项，看 `1688/assets` 这条：

```json
{
  "command": "1688/assets",
  "strategy": "cookie",
  "browser": true,
  "domain": "www.1688.com",
  "columns": ["offer_id", "title", "main_count", "sku_count", "detail_count", "video_count"]
}
```

`strategy` 说明这条命令靠什么拿数据（`cookie` 表示需要站点登录态），`browser` 说明它是否要拉起浏览器，`columns` 提前给出输出列名。这三个字段合起来，等于在调用之前就告诉调用方：这条命令要登录、要开浏览器、返回这 6 个字段。命令存在，就意味着认证方式、页面依赖、输出字段和失败形态已经被适配器作者收敛过：把一个站点包装成一条命令的那层代码，OpenCLI 叫它 adapter。拿到的结果不再是"Agent 点完页面后的临时截图"，而是一份能进脚本、能接下游的结构化输出。

公开站点的命令同样规整。`opencli hackernews top --limit 3 -f json` 返回的行数据字段固定为 `rank`、`id`、`title`、`score`、`author`、`comments`、`url`，其中一行是 2026 年 5 月 19 日抓到的快照：

```json
{
  "rank": 1,
  "id": 48175820,
  "title": "Why bambu_networking violates the AGPL in Bambu Studio",
  "score": 43,
  "author": "marcosscriven",
  "comments": 13,
  "url": "https://github.com/jarczakpawel/OrcaSlicer-bambulab/blob/main/bambu_agpl.md"
}
```

这七个字段与 `opencli list -f json` 里 `hackernews/top` 声明的 `columns` 一一对应。标题和分数会变——同一个 `id` 到 2026-09-19 在 HN 上已经涨到 105 分、标题也换了一种表述——不变的是字段结构。所以这个例子能验证的是 schema，不是某一天的排名。浏览器脚本也能拿数据，但每次都从 DOM、截图和选择器开始，Agent 的工作会停在一次性操作层，很难变成团队里的公共工具。

## 三层状态模型

OpenCLI 的状态不止一层。`--profile`、`browser <session>` 和 `siteSession` 名字相近，管的却是三件不同的事。

| 概念 | 你在命令里看到什么 | 它决定什么 | 常见误解 |
| --- | --- | --- | --- |
| Browser profile | `--profile work`、`OPENCLI_PROFILE=work` | 这条命令路由到哪个 Chrome 身份 | 把它当成浏览器流程名 |
| Browser session | `opencli browser inbox ...` | 多步 browser 原语复用哪条 tab lease 和默认目标页 | 以为它等于某个站点账号 |
| Adapter `siteSession` | `--site-session persistent` / `ephemeral` | 浏览器型适配器沿用稳定站点 tab，还是一次性开 tab | 以为它就是通用 browser session |

一句话对齐：`--profile` 管哪个 Chrome 身份，`browser <session>` 管一段浏览器流程，`siteSession` 管浏览器型适配器是否延续同一站点页。

### 先给 Chrome 身份起别名

每个 Chrome profile 跑一份独立的扩展实例。只有一个 profile 连着时 OpenCLI 自动用它；连着多个又没有设默认值时，它会要求你指定，而不是替你猜。

```bash
opencli profile list
opencli profile rename <contextId> work
opencli profile use work
opencli --profile work browser work state
```

这一步不是整理洁癖。每个 Chrome profile 跑各自独立的扩展实例，profile 选错，selector、cookie 和页面上下文就全落在另一个身份下，表现出来像是命令偶发失效。

### 给一段浏览器流程命名

`opencli browser *` 要求 `<session>` 作为位置参数紧跟在 `browser` 后面：

```bash
opencli browser work open https://example.com
opencli browser work state
opencli browser work extract "main"
```

v1.7.19 之后写法就统一了：v1.7.22 的中英文 README、v1.8.8 的 Browser Bridge 文档和 `opencli-browser` skill 里，`--session` 一次都没有出现。但翻早期资料会撞见 `opencli browser --session work ...`，那是同一条命令树的旧形态，不是并存的两套语法：

| 版本 | 变更 |
| --- | --- |
| v1.7.17 | 用显式 `--session <name>` 取代原来的 `--workspace` 模型，browser 命令开始要求给出会话名（#1461） |
| v1.7.18 | `--session` 提升为 requiredOption，缺参由 Commander 直接拒绝（#1485） |
| v1.7.19 | 改用 `<session>` 位置参数，`opencli browser work click 12` 取代 `opencli browser --session work click 12`（#1505） |

v1.7.19 的改动理由写得很明白。必需参数的语义已经被位置参数结构化表达了，再留一个 required flag 属于重复。改完即对齐 Docker、git 那种"操作对象紧跟子命令"的惯例。内部协议里 `--session` 仍然存在，daemon 通信和直接调用 `program.parseAsync()` 的代码还在用它，只是不再出现在用户面上。所以看到 `--session` 的正确判断是"这份资料早于 v1.7.19"，而不是"这个版本两种写法都行"。

同一命令族里还有第三个易混参数 `--site-session`，它跟上面这个历史 flag 没有关系，管的是适配器的站点页生命周期，见本节末尾。

owned session（由 OpenCLI 自己创建的会话）持有交互式 tab lease，空闲超时是 10 分钟，提前释放要显式关闭：

```bash
opencli browser work close
```

它适合一段需要连续上下文的临时网页工作：打开页面、读取状态、点击、再读取状态。默认窗口模式是前台，能看着它操作；`--window background` 可以把自动化窗口挪到背后。

另一个常见误判来自 `tab new`。它只创建新 tab，不会自动成为后续命令的默认目标：

```bash
opencli browser work tab list            # 拿到 targetId
opencli browser work eval --tab <targetId> 'document.title'   # 单条命令打到指定 tab
opencli browser work tab select <targetId>                    # 改默认目标
```

`opencli browser <session> open <url>` 和 `tab new [url]` 都会返回 `targetId`；`--tab <targetId>` 只影响当前这一条命令；`tab select` 才改默认目标；`tab close` 关掉的如果正是默认目标，存储的默认值会被清空。漏掉 `tab select` 这一步，后续命令看起来像"跑错页"，实际是 session 仍指向旧目标。

### 把已打开的真实标签页借给会话

登录、SSO（单点登录）、验证码、复杂跳转已经由人手工完成时，重新让 OpenCLI 开一页并不划算。`bind` 做的事很简单：把当前真实 tab 显式交给某个 session。

```bash
opencli browser gmail bind
opencli browser gmail state
opencli browser gmail click "Search"
opencli browser gmail unbind
```

`bind` 不复制用户 tab，只是把已有 tab 设为这个 session 的操作对象。bound session 不拥有用户窗口，不会替你关闭用户 tab，也没有 owned session 的 10 分钟空闲计时器；绑定一直持续到 `unbind`、tab 关闭、窗口关闭或 daemon 重启。

边界也很直白：页面导航和普通操作可以做，`tab new`、`tab select`、`tab close` 这三个会改 tab 生命周期的动作在 bound session 上会被拒，报 `bound_tab_mutation_blocked`，提示要管标签页生命周期就换成 owned session。借来的 tab 不该被工具擅自管理。

还有一处容易踩的分区：`OpenCLI Browser` 和 `OpenCLI Adapter` 这两个标签页分组由扩展托管，用来放自动化容器。自己的长期标签页不要塞进去，也别改它们的名字。

### 适配器是一次性页，还是持续站点页

浏览器型适配器和 `browser <session>` 的默认策略不同。browser session 给交互流程复用，默认前台窗口；浏览器型适配器默认后台运行，命令结束就释放一次性 tab lease。需要连续上下文的交互式站点命令，才在适配器元数据里声明 `siteSession: 'persistent'`。

覆盖它的入口有两级：单次命令用 `--site-session ephemeral|persistent`，全局默认用环境变量 `OPENCLI_SITE_SESSION`，命令行优先。

这类 persistent 命令集中在对话型站点。Doubao 适配器下 `ask`、`read`、`detail`、`history`、`send` 等全部命令都声明了 `siteSession: 'persistent'`，所以连续执行会自然留在同一个对话页；`xiaohongshu` 则只有 `login` 和 `whoami` 是 persistent，`notifications`、`feed`、`search` 走默认的一次性 tab。同样是站点命令，连续执行会不会停在同一页，取决于适配器声明，不是产品行为"飘"。

## Browser Bridge 的边界

Browser Bridge 常被概括成 CLI 和浏览器之间的桥。方向对，但太粗。一条网页命令实际穿过这几层：

```text
opencli --profile work browser inbox open <url>
        │
        ├─ --profile work：选择哪个 Chrome 身份
        └─ browser inbox：选择哪条交互式 browser session

CLI（Node.js）
  <- WebSocket localhost:19825 ->  micro-daemon（首次浏览器命令自动拉起）
  <- Chrome 扩展 API ->  Browser Bridge 扩展
  <- 当前 tab / 绑定 tab / OpenCLI 拥有的 tab lease
```

这条链路带来四个工程后果。

登录态留在浏览器里。不必把 cookie 手工抄进 CLI 配置，也不必为了消费级网页流程去伪造一套并不存在的服务端认证。

多 profile 是一等场景。`--profile` 和 `OPENCLI_PROFILE` 把"这次命令到底使用哪个 Chrome 身份"变成显式输入。

页面所有权被区分出来。owned session、bound session、适配器后台窗口，生命周期和权限各不相同，前文 10 分钟空闲计时器的差异就是这么来的。

扩展权限各有明确用途。清单里除 `debugger`、`tabs`、`tabGroups`、`cookies`、`downloads` 之外还有 `activeTab`、`alarms`、`storage`。

| 权限 | 在 OpenCLI 链路里的作用 |
| --- | --- |
| `debugger` | 向目标 tab 发送 CDP 命令 |
| `tabs` / `tabGroups` | 管理自动化容器和 tab 元数据 |
| `cookies` | 服务以 cookie 方式取数的适配器 |
| `downloads` | 让 `opencli browser wait download` 感知 Chrome 的下载生命周期，而不是盲等文件系统 |

剩下三项能直接从源码读出用途，而且都绕不开 Manifest V3 的 service worker（服务工作线程）会被回收这件事。`storage` 分两层：tab lease 注册表写 `chrome.storage.session`，注释解释了为什么不写 `local`——注册表里的 window、tab、group 都是 Chrome 运行时编号，只在一次浏览器会话内有效，跨重启恢复反而会让复用的编号撞上用户新建的窗口并被误认领；profile 身份 `contextId` 才存在 `storage.local`。`alarms` 负责持久唤醒：生产环境的 Chrome 把 alarm 最小间隔压到约 30 秒，所以 worker 被回收后靠 alarms 叫起来，worker 还活着时用 setTimeout 走 1s 起步、封顶 15s 的指数退避重连。`activeTab` 只在 `manifest.json` 里声明，仓库里检索不到调用点。

daemon 是常驻的：首次执行浏览器命令时自启，之后一直活着，直到 `opencli daemon stop` 或卸载包。排障时可以直接看它的日志。

```bash
curl localhost:19825/logs
opencli daemon stop
```

全局重装后 CLI 与 daemon 版本不一致时，CLI 会先请求 `/shutdown`，3 秒内端口没释放再退到 `SIGKILL`；只有跨用户或跨机器的 PID 文件才会要求手工 `daemon stop`。

桌面应用适配器走另一条路径。Cursor、Codex、ChatGPT App 这类 Electron 应用不经过 Browser Bridge 扩展，而是由应用自己暴露 CDP 端点：

```bash
/Applications/AppName.app/Contents/MacOS/AppName --remote-debugging-port=<port>
export OPENCLI_CDP_ENDPOINT="http://127.0.0.1:<port>"
curl http://127.0.0.1:<port>/json/version    # 验证端点可达
```

OpenCLI 收拢的是上层命令树，底层 transport 可以不同。这条路径也有硬前提：目标应用是 Electron，或者至少能开出一个可用的 CDP 端点。两者都不满足的桌面应用，官方给的方向是改用原生桌面自动化（例如 AppleScript），而不是硬套 CDP。

## 一次任务怎样从网页动作沉淀成命令

只看静态结构，很容易把 OpenCLI 读成"能开浏览器的 CLI"。看一条任务怎么流过系统，更接近它的设计意图。

目标是"检查工作账号里的小红书通知，并把结果交给下游 Agent 处理"，顺序是：

```text
先找现成命令
  -> 命令有缺口时退到 browser 原语
  -> 确认流程会重复发生
  -> 沉淀成 user adapter / plugin / external CLI
```

第一步，直接找站点命令：

```bash
opencli xiaohongshu notifications -f json
```

这条命令的输出列固定为 `rank`、`user`、`action`、`content`、`note`、`time`。字段够用，任务到这里就结束了，留下来的是结构化输出。

第二步，命令缺一个细节时才退到 browser 层。例如只看某个筛选条件下的未读通知：

```bash
opencli --profile work browser xhs-inbox open https://www.xiaohongshu.com/
opencli --profile work browser xhs-inbox state          # 列出可操作元素及其 [N] 编号
opencli --profile work browser xhs-inbox click 17       # target 用 state 给的数字 ref
opencli --profile work browser xhs-inbox extract "main"
opencli --profile work browser xhs-inbox network        # 看页面实际打了哪些接口
```

每个交互命令的 `<target>` 有两种写法：`state` / `find` 快照里的数字 ref，或者一条 CSS 选择器；CSS 命中多个时要配 `--nth <n>` 才不会被判歧义。`opencli-browser` skill 给的建议是拿到 ref 就优先用 ref——CLI 会对每个被标记的元素做指纹，轻微 DOM 变动下仍能对上，而手写的 CSS 在站点重新渲染的那一次就断。同理，导航、表单提交和 SPA（单页应用）路由切换会让 ref 失效，页面变了就要重新 `state`，不能沿用上一轮的编号。

browser 原语在这里负责探索和补洞：定位页面、确认字段、观察网络请求。长期运行的自动化不适合停在这一层。

第三步，流程开始重复后，把它写回命令面：

```bash
opencli browser init xiaohongshu/unread-notices
# 编辑 ~/.opencli/clis/xiaohongshu/unread-notices.js
opencli browser verify xiaohongshu/unread-notices
opencli xiaohongshu unread-notices
```

`init` 生成的骨架落在 `~/.opencli/clis/`，`verify` 负责把它跑通：真实执行一次适配器并校验输出，如果 `~/.opencli/sites/<site>/verify/<command>.json` 有 fixture（测试夹具），就按它做值级比对，没有则可用 `--write-fixture` 先生成一份起步用。跑通之后，这条命令就出现在 `opencli list` 里。浏览器自动化仍然存在，只是它已经变成适配器生成过程的一部分；最后留下的是一条能被别人发现、复查和复用的命令。

往哪一层扩展，官方按"源码放哪、怎么共享"分成五条路径：

| 需求 | 路径 | 源码位置 | 命令形态 |
| --- | --- | --- | --- |
| 本机快速起一个私有适配器 | User adapter | `~/.opencli/clis/<site>/<command>.js` | `opencli <site> <command>` |
| 个人站点命令想留在自己的 Git 仓库 | Local plugin | 项目目录，符号链接到 `~/.opencli/plugins/` | `opencli <plugin> <command>` |
| 发布或安装第三方命令 | Plugin | 装进 `~/.opencli/plugins/` 的 Git 仓库 | `opencli <plugin> <command>` |
| 本地改官方适配器 | Adapter override | `~/.opencli/clis/<site>/` | `opencli <site> <command>` |
| 只是包住一个已有二进制 | External CLI | `~/.opencli/external-clis.yaml` | `opencli <tool> ...` |

```bash
opencli plugin create my-cnn
cd my-cnn && git init
opencli plugin install file://$(pwd)
opencli my-cnn hello

opencli adapter eject <site>   # 复制一份官方适配器到本地覆盖
opencli adapter reset <site>   # 撤回覆盖
```

`plugin install file://...` 建的是符号链接，源文件仍留在项目目录，编辑和提交都在原处。要长期自己维护的命令走这条，比 user adapter 更适合进版本控制。

浏览器动作是中间态，命令才是长期形态。用 OpenCLI 时最好一直记着这条线。

## 排障先看边界

OpenCLI 的常见坑多半落在状态、页面上下文和文档版本上，未必出在 parser 或桥接层。

先把退出码拿到手，它能把"看起来失败了"变成"按分支处理"：

| 退出码 | 含义 | 触发条件 |
| --- | --- | --- |
| `0` | 成功 | 正常完成 |
| `1` | 通用错误 | 未分类的意外失败 |
| `2` | 用法错误 | 参数不合法或命令不存在 |
| `66` | 空结果 | 没拿到数据（`EX_NOINPUT`） |
| `69` | 服务不可用 | Browser Bridge 未连接（`EX_UNAVAILABLE`） |
| `75` | 临时失败 | 命令超时，可重试（`EX_TEMPFAIL`） |
| `77` | 需要登录 | 目标站点未登录（`EX_NOPERM`） |
| `78` | 配置错误 | 缺凭据或配置不合法（`EX_CONFIG`） |
| `130` | 被中断 | Ctrl-C |

这套码遵循 Unix `sysexits.h`，v1.7.22 的 `dist/src/errors.js` 里就已经是 66 / 69 / 75 / 77 / 78 这组值。于是脚本可以写成"未登录就顺手登录再重试"：

```bash
opencli gh issue list 2>/dev/null
[ $? -eq 77 ] && opencli gh auth login
```

### doctor 只证明桥接连通

`opencli doctor` 在帮助里的自述是 "Diagnose opencli browser bridge connectivity"。它先做一次活体连通性探测（这一步顺带充当 daemon 自启和端到端校验），再读 daemon 状态、扩展是否 ready、CLI 与 daemon 版本是否错配、连接了哪些 profile、扩展版本号，以及被官方适配器遮蔽的本地 user adapter——刚用 `adapter eject` 改过某个适配器时，最后这项能告诉你生效的到底是哪一份。

它不验证任何一条适配器命令能否真的取到数据，也不覆盖 plugin 和 external CLI。

因此 `doctor` 不绿时，`opencli list`、`opencli hackernews top`、`opencli gh pr list` 这类命令仍可能正常；反过来 `doctor` 全绿，也不代表某个浏览器型适配器已经读到当前页面上下文。官方排障文档把这句话写得很直接：桥接健康不保证当前页面目标暴露了适配器需要的数据。

### 空数据和权限错误先查身份与页面上下文

浏览器型适配器返回空数据、报 `Unauthorized`，或者"页面开着却读不到上下文"时，按顺序查四件事，每件事都带一个可执行的下一步：

| 检查项 | 下一步动作 |
| --- | --- |
| 命令是否路由到正确的 Chrome profile | `opencli profile list`，必要时加 `--profile` |
| 目标站点是否在该 profile 里登录 | 在普通 Chrome 标签页打开站点重新登录，或刷新页面 |
| 当前 tab 是否落在适配器预期的 host / page context | 收窄目标页，见下方 `OPENCLI_CDP_TARGET` |
| 是否被登录墙、同意弹窗、地理限制或风控页挡住 | 先手工过掉拦截页；Bilibili、Zhihu 在境外访问会命中地理限制 |

以 `opencli 1688 item` 为例，页面已经打开不等于商品上下文可读，目标页过宽时会报 `did not expose product context`。修复办法是把 CDP 目标限定到详情页域名：

```bash
OPENCLI_CDP_TARGET=detail.1688.com opencli 1688 item 841141931191 -f json
```

### 版本边界以包元数据和 CLI 帮助为准

迭代快的项目里，同一份说明的不同页面会落后于代码。Node.js 下限是个典型样本：

| 版本 | 状态 |
| --- | --- |
| v1.7.0 | `engines.node` 为 `>=20.0.0` |
| v1.7.1 | 抬到 `>=21.0.0`，README 同步写 `>=21` |
| v1.7.19 | 降回 `>=20.0.0`，理由是让 Node v20 到 v21.6 的用户不再在模块加载时崩溃；README 没跟着改 |
| v1.7.22 | `package.json` 写 `>=20.0.0`，README 仍写 `>=21` |
| v1.8.1（2026-05-31） | PR #1705 修正 README 的 Node 下限 |
| v1.8.8 主干 / npm 1.8.7 | 主干 `package.json` 为 `>=20.18.1`，README 与之一致；npm 上最新发布版本仍写 `>=20.0.0` |

同一条线索上还剩一处没对齐：v1.8.8 的排障文档仍写 `Node.js >= 20`。写教程或 CI 配置时，别只取一份文档当真相，`package.json` 的 `engines`、`opencli --help` 和 release note 三个来源交叉核对，冲突时以包元数据和实际 CLI 帮助为准。

## 适用边界

判断 OpenCLI 时，先看它该不该出现在这条链路里。

| 任务类型 | 更合适的工具 | 判断理由 |
| --- | --- | --- |
| 官方 API 完整、服务端认证清晰 | API / SDK（软件开发包） | 少一层浏览器状态，更轻、更稳 |
| 端到端测试、断言、隔离回归 | Playwright | 测试语义、断言模型、隔离环境更成熟 |
| 需要复用真实网页登录态 | OpenCLI | 不必外搬 cookie，也不必重写认证流程 |
| 需要把消费级网页能力沉淀成命令 | OpenCLI | 先用浏览器原语探索，再固化成适配器 |
| 想统一调用本地 CLI、网站和桌面应用 | OpenCLI | 同一命令树对人和 Agent 都更友好 |
| 目标桌面应用既非 Electron 也不暴露 CDP | 原生桌面自动化 | OpenCLI 的 CDP 路径在这里没有入口 |

面对官方 API、后端服务账户和 CI 回归测试时，OpenCLI 通常不是最经济的第一层。问题落在消费级网站、真人登录态、桌面客户端、高频但缺少官方接口的操作上，它的优势才明显。

另一侧的代价也要看清：网页链路依赖选择器和站点接口，站点改版会让适配器失效，所以浏览器型命令后面要有人维护。官方把这个回路做成了 skill——`opencli-autofix` 在命令失败时引导收集 trace 产物、给适配器打补丁、重试，并在验证修好之后往上游提 GitHub issue。六个 `opencli-*` skill 可以整包安装，也可以只挑需要的：

```bash
npx skills add jackwener/opencli
npx skills add jackwener/opencli --skill opencli-adapter-author
npx skills add jackwener/opencli --skill opencli-autofix
```

## 推进顺序

团队里落地 OpenCLI，可以按下面顺序推进：

1. 先跑 `opencli list`，确认能力是否已经存在。需要接脚本时改用 `opencli list -f json`，直接读 `columns` 和 `args`。
2. 涉及浏览器型命令时，再跑 `opencli doctor`、`opencli profile list`，多身份环境先 `opencli profile use <name>`。
3. 适配器没覆盖时，用 `opencli browser <session> ...` 做临时探索、字段定位和页面校准，并靠退出码判断卡在哪一层。
4. 某个流程开始重复，就升格为 user adapter、plugin 或 external CLI。先本地起，验证稳定后再考虑共享。
5. 写入文档或自动化脚本前，用 `opencli <command> --help` 和当前包元数据复核命令写法。
6. 有通用价值的适配器往上游提 PR，私有价值的收进 local plugin，避免两类代码混在一台机器的 `~/.opencli/clis/` 里。

这套顺序的落点在运行面：能被下一个人查到、复查、复用的是注册表里的命令，页面细节留在适配器内部，不渗到脚本里。

## 接手前先验这五件事

按顺序做完，能确认你对这个工具的理解和它当前的行为对得上：

1. `opencli list -f json` 里随便挑一条浏览器型命令，能不能只靠 `strategy`、`browser`、`columns` 三个字段就说清它要登录、要开页、返回几列？
2. 你的环境连着几个 Chrome profile？两个以上时，脚本里每一条 browser 命令有没有带上 `--profile`？
3. 手上一段多步网页操作，session 名是否固定？如果中途用了 `tab new`，后面有没有 `tab select`？
4. 一条命令返回空结果时，`$?` 给的是 66 还是 77？前者是页面没数据，后者是登录态问题，处理方式不同。
5. 需要连续停留在同一站点页的命令，它声明了 `siteSession: 'persistent'` 吗？没有的话，单次 `--site-session persistent` 能否解决，还是应该退回 browser 原语？

## 结语

OpenCLI 把登录态网页、桌面应用、本地 CLI 放回一棵确定性的命令树里。对 Agent 来说，命令有固定的 `columns` 和退出码，失败能被脚本接住，不必每次从 DOM 和选择器重新摸索；对写脚本的人来说，一套能力不再分散在 API 文档、桌面端界面和网页操作三种交互模型里。

需要测试隔离、回归断言或官方 API 编排时，它不该排在第一层。需要处理真实会话、消费级网站、桌面客户端，以及高频但难以接口化的操作时，OpenCLI 补上的正是那层命令面。

## 参考资料

- [OpenCLI GitHub 仓库](https://github.com/jackwener/OpenCLI)
- [package.json](https://raw.githubusercontent.com/jackwener/opencli/main/package.json)
- [README 中文版](https://github.com/jackwener/OpenCLI/blob/main/README.zh-CN.md)
- [Getting Started](https://opencli.info/docs/guide/getting-started.html)
- [Browser Bridge 设置指南](https://opencli.info/docs/guide/browser-bridge.html)
- [Exit Codes](https://opencli.info/docs/guide/exit-codes.html)
- [Extending OpenCLI](https://opencli.info/docs/guide/extending-opencli.html)
- [Add a New Electron App CLI](https://opencli.info/docs/guide/electron-app-cli.html)
- [Troubleshooting](https://opencli.info/docs/guide/troubleshooting.html)
- [opencli-browser skill](https://github.com/jackwener/opencli/blob/main/skills/opencli-browser/SKILL.md)
- [Doubao adapter 文档](https://opencli.info/docs/adapters/browser/doubao.html)
- [CHANGELOG（session 参数与 Node 下限变更）](https://github.com/jackwener/OpenCLI/blob/main/CHANGELOG.md)
- [Chrome Web Store 扩展页](https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk)
