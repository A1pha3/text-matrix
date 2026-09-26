---
title: "Cypress：测试代码跑在浏览器内部，而 16 版把网络层还给了浏览器"
date: "2026-06-15T15:01:13+08:00"
lastmod: "2026-09-20T11:30:00+08:00"
slug: "cypress-e2e-component-testing-real-browser-architecture-guide"
github_repo: "cypress-io/cypress"
source_key: "gh:cypress-io/cypress"
description: "对照 cypress-io/cypress develop 分支与 npm cypress@16.1.0 拆解 Cypress：测试代码为什么必须在浏览器里执行、Chromium 走 CDP 而 Firefox 走 WebDriver BiDi 的双通道驱动层、16 版把 Chrome 系流量交还浏览器原生网络之后 cy.intercept 的九处行为差异，以及自动等待、Studio、Cypress Cloud 编排的真实边界。"
draft: false
categories: ["技术笔记"]
tags: ["JavaScript", "测试框架", "前端工程", "CI"]
---

> **目标读者**：在前端 / 全栈工程里负责回归测试的工程师和测试负责人，以及在 Cypress、Playwright、Selenium 之间做选型的架构师。
> **核心问题**：Cypress 十一年没变过的那句架构承诺，到底换来了什么、赔上了什么；16 版改掉网络层之后，哪些写法会直接撞到新边界。
> **事实边界**：本文核对的是 `cypress-io/cypress` 的 `develop` 分支提交 `61aeb9d`（2026-09-19）、npm `cypress@16.1.0`（16.0.0 发布于 2026-09-01）以及 docs.cypress.io 在 2026-09-20 的公开内容。配置默认值一律从仓库 `packages/config/src/options.ts` 读取，不引用二手总结；性能部分只搬官方给出的时长区间，不给加速比。

## 一句话判断

Cypress 的架构承诺一直只有一句话：测试代码和被测应用跑在同一个浏览器里，中间不做对象序列化。为了守住这句话，它赔上了多浏览器并行控制、跨域 iframe 和非 JavaScript 语言三样东西，十一年没有松动。

16 版做了一次反向动作：Chrome、Chromium、Edge 的测试流量不再经过 Cypress 自己的代理，改走浏览器原生网络栈。测试执行仍然在浏览器内，但「所有网络请求都过一遍 Cypress」这条隐含前提从此不成立。`cy.intercept()` 的 API（应用程序接口）一个字没改，行为差异却列了九条——踩到的是写压缩头断言、`httpVersion` 断言和缓存断言的那批人。

选型的结论也跟着这句话收窄：回归对象是你自己的 web 应用，Cypress 的调试体验仍然在最高一档；需要同时驱动多个浏览器上下文、需要移动真机、需要 WebDriver 的跨语言绑定，Playwright 与 Selenium 占住的位置没有变化。

## 项目坐标（2026-09-20 核对）

| 字段 | 值 |
|------|------|
| 仓库 | [cypress-io/cypress](https://github.com/cypress-io/cypress)，默认分支 `develop`，最近提交 2026-09-19 |
| Stars / Forks | 51,016 / 3,640（GitHub API 当日读数） |
| 建仓时间 | 2015-03-04 |
| License | MIT |
| npm | latest 为 `cypress@16.1.0`，历史发布 293 个版本 |
| Node.js（节点式运行时）版本要求 | `^22.0.0`、`^24.0.0` 或 `>=26.0.0`；16.0.0 起去掉 20 与 25 两条线 |
| 内嵌运行时 | 16.0.0 把 Electron 从 37.6.0 升到 41.7.0，内嵌 Chromium 升到 146.0.7680.216 |
| 产物划分 | Cypress App（开源、本地安装）+ Cypress Cloud（付费）+ UI Coverage（界面覆盖率统计）、Cypress Accessibility（无障碍检查） |
| 仓库结构 | 单一 monorepo（单仓库），`packages/` 下 40 余个子包，`npm/` 下是对外发布的框架适配包 |

`packages/` 的划分本身就是一张系统地图，值得在深入之前看一眼。执行侧是 `driver`（注入浏览器的测试运行时）、`runner` 与 `reporter`（命令队列与命令日志）、`app`（Cypress App 界面）。服务侧是 `server`（Node.js 侧的服务与生命周期）、`launcher`、`electron`、`extension`（把真实浏览器拉起来）。网络侧最厚：`proxy`（代理）、`https-proxy`、`net-stubbing`、`network`、`network-interception` 五个包并存。最后这一组在 16 版里同时存在两条路径，不是重构遗留，是它们真的都还在被用。

## 测试内核是一组内嵌库，不是项目依赖

官方把这一页叫做 Bundled Libraries，值得整段搬过来，因为它解释了为什么 `describe`、`expect` 这些全局函数不需要 import。

| 库 | 在 Cypress 里承担什么 | 怎么拿到 |
|------|------|------|
| Mocha | 测试框架与运行器语法 | `describe()` `it()` `beforeEach()` `.only()` `.skip()` |
| Chai | 断言 | `expect()` `assert()`，以及链式 `.should()` |
| Chai-jQuery | DOM 专用断言 | `have.class`、`be.visible` 这类链式判断 |
| Sinon | 间谍、桩与假计时器 | `cy.spy()`、`cy.stub()`、`cy.clock()`、`Cypress.sinon` |
| Sinon-Chai | 对间谍和桩做断言 | `have.been.calledOnce` |
| Lodash / jQuery | 工具函数与 DOM 遍历 | `Cypress._`、`Cypress.$` |
| minimatch / blob-util / Buffer / Bluebird | 通配匹配、二进制、Promise | `Cypress.minimatch`、`Cypress.Blob`、`Cypress.Buffer`、`Cypress.Promise` |

源码侧能对上：`packages/server/package.json` 把 Mocha 钉成 `"mocha-7.2.0": "npm:mocha@7.2.0"`，`packages/driver/package.json` 里是 `chai@4.5.0`、`sinon@8.1.1`、`jquery@3.7.1`。官方明确写着 Cypress 永远用自己内嵌的那一份，你在项目里另装什么版本不影响它跑测试。

这条约束有一个副作用容易咬人：TypeScript 项目如果同时装了 `@types/chai` 或 `@types/jquery`，或者同一个仓库里还跑 Jest，全局类型会打架。官方给的处理办法是在 `tsconfig.json` 里显式圈定 `types`，而不是去掉某一方。

## 两套通道在合作：执行层与驱动层

把 Cypress 讲成「三层进程模型」会漏掉关键一半：它真正不对称的地方在于，**测试代码的执行**和**浏览器的控制**走的是两条完全独立的通道。

```text
浏览器里的一个 tab（Cypress App 页面）
├─ AUT iframe            被测应用 + 注入进来的 driver
├─ spec iframe           你的 spec 源码在这里求值
├─ snapshot iframes      Time Travel 用的历史 DOM 快照
└─ spec-bridge iframe    只在跨 origin（cy.origin）时出现
        │
        ▼  ① 自动化通道，按浏览器分叉
           Chromium 系   CDP（chrome-remote-interface）
           Firefox       geckodriver + WebDriver BiDi
           WebKit        playwright-webkit 的 launchServer
        │
        ▼  ② Node.js 侧 server
           拉起与回收浏览器、读 fixture、截图、Test Replay 录制、Cloud 上报
        │
        ▼  ③ 网络通道，16 版起分叉
           Chrome / Chromium / Edge     浏览器原生网络（HTTP/2、HTTP/3）
           Firefox / WebKit / Electron  Cypress 代理（旧路径）
           forceHttp1: true             全部退回旧路径
        │
        ▼  ④ Cypress App UI
           Launchpad、Command Log、Time Travel、Studio
```

对应到代码：`packages/app/src/runner/index.ts`（runner 的索引入口）的 `runSpecE2E()` 先建 AUT iframe，再往同一个容器里追加一个 `class` 为 `spec-iframe` 的 frame，最后调用 `initialize({ $autIframe, ... })` 把 driver 接到 AUT 上；只有 `cy.origin()` 触发时才会通过 `addCrossOriginIframe()` 追加 `spec-bridge-iframe`，其 `src` 指向服务端路由 `/<namespace>/spec-bridge-iframes`，其中的 `namespace` 是 Cypress 内部路由的命名空间前缀。Time Travel 用的快照 iframe 由 `autIframe.create()` 一并返回，和 AUT 平级。最下面那个 ④ 的宿主并不固定：Electron 只是其中一种，16 版在 Chrome、Chromium、Edge 下 App 界面直接是浏览器的一个 tab——16.1.0 修的一个回归正是被测站点注册的 origin 级 service worker（服务工作线程）去应答了 Cypress 自己的页面与资源。

### 「不走 WebDriver」这句话半对半错

Why Cypress 页面至今写着「Our architecture doesn't use Selenium or WebDriver」。这句话在**测试命令的传递模型**上成立：Cypress 不把一条 `click` 编码成 WebDriver 命令发给远端。但在**浏览器控制通道**上，它不准确，而且这几年越来越不准确。

| 浏览器家族 | 控制通道 | 仓库证据 |
|------|------|------|
| Chrome / Chromium / Edge | CDP | `packages/server/lib/browsers/cdp-protocol/`、`browser-cri-client.ts`，依赖 `chrome-remote-interface@0.33.3` |
| Firefox | WebDriver BiDi（经 geckodriver） | `packages/server/lib/browsers/bidi_automation.ts`，依赖 `webdriver@9.28.0` |
| WebKit（实验性） | Playwright 的 WebKit + CDP 桥 | `webkit.ts`、`webkit-automation.ts`、`webkit-cdp-bridge.ts` |
| Electron（已弃用） | 同 Chromium | `electron.ts` |

时间线是可查的：13.15.1（2024-10-24）起 Cypress 引入 `webdriver` 包与 `firefox-profile`；14.1.0（2025-02-25）让 Firefox 135 以上改用 WebDriver BiDi。当前文档写的可启动下限是 Firefox 140，并注明 15.0.0 到 15.18.1 期间的下限是 135；仓库里那份 Firefox 自动化说明写的口径是「自 Firefox 141 与 Cypress 15 起，WebDriver BiDi 用于完整自动化 Firefox」。两处版本号差 1，取哪一个取决于你读的是发布说明还是浏览器支持页。

`packages/server/lib/browsers/firefox_automation.md` 把细节交代得很清楚。Firefox 是通过 WebDriver 的 `newSession` 命令启动的，geckodriver 同时承担 Marionette 协议，用来安装 Cypress 自己的 WebExtension；文档原话是这一步「critical to automating Firefox」。Chrome 一侧完全不需要这层扩展。同一个 `cy.click()` 落到不同浏览器家族时，走的是两套不同的控制协议，只是被 `protocol.ts` 收敛成同一个接口。

这条分叉还有一个可观测的后果。15.0.0 起，`cy.url()`、`cy.hash()`（取地址栏片段哈希）、`cy.go()`、`cy.reload()`、`cy.title()`、`cy.location()` 不再读 `window` 对象，改用自动化客户端取值：Chromium 走 CDP，Firefox 走 WebDriver BiDi。官方给的原因是绕开 `cy.origin()` 带来的跨 origin 访问限制。实验性 WebKit 仍走 `window`。另一条更早的分叉在 13.9.0（2024-05-07）：Electron 开始接收与 Chrome 相同的一组默认启动参数，副作用是在 Electron 里测试时 `navigator.webdriver` 会如实地取 `true`。依赖这个属性做反自动化判断的应用，在 Cypress 里会走到另一条分支。

### 网络通道为什么单独拎出来

旧路径下，浏览器发出的每个请求都会落到 Cypress 的代理上：Cypress 自己充当 CA、给被测 origin 动态签发证书、逐条改写流量，因此它天然知道 `httpVersion`、`content-encoding` 这些字段，代价是只能讲 HTTP/1.1。

16 版把这条链路从 Chrome 系上摘掉了。现在被测应用直连你的服务器，协商到的就是生产里那套协议——HTTP/2、HTTP/3 不再被降级，单连接复用取代了每域名六连接的天花板，浏览器校验的也是你真实颁发的证书而不是 Cypress 生成的那一张。改动的价值主张很直接：**测的协议和跑的协议终于一致**。

代价列在官方页面上，九条，逐条有前后对照示例：

| 行为 | 旧路径 | 原生路径（Chrome / Chromium / Edge） |
|------|------|------|
| `req.httpVersion` | `'1.1'` | `undefined`（`res.httpVersion` 为 `null`） |
| `content-encoding` / `content-length` / `transfer-encoding` | 存在于响应头 | 不在响应头里，响应体已解码 |
| 浏览器自己拒绝的响应 | 状态码与头可见 | 请求可捕获，`interception.response` 为 `undefined` |
| 无网络请求即返回的响应 | 不重复触发拦截 | 第二次导航会再次命中拦截 |
| 重校验命中缓存的响应 | 304 | 报 200 |
| `responseTimeout` | 适用于响应处理 | 不再约束响应处理，超时要在 `cy.wait()` 上自己给 |
| 请求 `content-length` | 会上报 | 不上报 |
| 桩响应体的解码 | 按声明的编码解码 | 仍解码，因此声明的编码必须与真实字节一致，否则拿到乱码 |
| 不安全来源的压缩文档 | visit 本身失败 | 能加载，原先断言导航失败的测试要改 |

迁移期给了一个逃生阀：`forceHttp1: true` 让所有浏览器都退回旧路径。但这个选项在引入的同时就被标了弃用，设置它每次都会打警告，官方明确写了不要只为了不修测试就长期挂着。另外 `blockHosts` 在 16.0.0 曾一度在 Chrome 系失效（被拦截的主机照常发出请求而不是返回 503），16.1.0 修掉——如果你正好卡在 16.0.0，这是一条值得核对的已知回归。

还有一条与网络无关但同样容易漏的：WebSocket 连接在测试里正常收发，但 Cypress 不拦截它，因此无法对帧或消息做桩。要测实时协作，官方的建议是把「另一参与方」用服务端注入或一个独立的背景进程模拟出来，而不是开第二个浏览器。

## 一条命令如何流过系统

以 `cy.get('.submit').click()` 为例，同一 origin 下和跨 origin 下的路径并不一样，这个差异恰好是「同运行时」承诺的边界所在。

**同 origin（绝大多数用例）**

1. spec iframe 里的测试代码调用 `cy.get('.submit')`，driver 把这条命令挂到命令队列上。
2. 队列调度器在 AUT 的真实 document 上执行选择器查询。这一步和 jQuery 的 `$()` 行为一致，`cy.get()` 是一个 query。
3. 命中元素后交给 `.click()`。`.click()` 是非 query 命令，执行前会跑一整套可执行性检查：元素存在、可见、未被遮挡、可交互、位置稳定（动画结束）。
4. 检查通过后派发真实的浏览器事件，应用自己的事件处理器在同一事件循环里响应。
5. 命令日志与 DOM 快照写进 snapshot iframe，Time Travel 侧边栏出现一条可悬停的记录。

**跨 origin（`cy.origin()` 内部）**

1. driver 发现目标命令属于另一个 origin，为该 origin 追加一个 `spec-bridge-iframe`。
2. 命令与结果改由 `postMessage` 传递。`packages/driver/src/cross-origin/communicator.ts` 把每次往返包成 Promise，默认超时 1000ms，日志和快照在越过这条边界前都要先序列化（`preprocessLogForSerialization`、`preprocessSnapshotForSerialization`）。
3. 也就是说，「没有对象序列化」这句架构承诺在跨 origin 段落里并不成立——那里确实有序列化，只是它被封装在同一个浏览器进程内的 frame 之间，而不是像 WebDriver 那样跨进程、跨机器。

这段对比决定了 Cypress 与 Playwright 的实质差异：Playwright 的 `page.click('.btn')` 在测试进程里执行，每条命令都要编码后发给浏览器再等结果回传（Chromium 上就是 CDP）；Cypress 在单 origin 用例里省掉了这趟往返，重试循环因此可以做得又短又密。Playwright 换到的是另一个方向的好处：它可以同时握着多个浏览器上下文。

## 自动等待的真实语义：query 会重跑，非 query 只跑一次

官方把 retry-ability 归到核心概念里，判据比「自动等待」这四个字严格得多：

- **query 之间会串联重试**。`cy.get('.todoapp').find('.todo-list li').should('have.length', 1)` 是一条链：断言失败时，Cypress 从链顶重新发起查询，再跑断言，直到通过或超时。
- **assertion 是一种特殊显示的 query**。`.should()` 和它的别名 `.and()` 都算。
- **非 query 命令只执行一次**。`.type()`、`.click()`、`cy.visit()` 不参与重试。

理解到这一层，很多「明明元素在却超时」的现象就有了统一解释：不是等待机制坏了，而是断言被写在了只执行一次的位置上。

```js
// 只跑一次：执行到时若仍是 4 个 li，直接失败
cy.get('.list').then(($el) => {
  expect($el.find('li').length).to.eq(5)
})

// 作为链上的断言参与重试，直到通过或 defaultCommandTimeout
cy.get('.list').should(($el) => {
  expect($el.find('li').length).to.eq(5)
})
```

相关默认值全部可以在 `packages/config/src/options.ts` 里读到：

| 配置项 | 默认值 | 说明 |
|------|------|------|
| `defaultCommandTimeout` | 4000 | query 重试的上限 |
| `requestTimeout` | 5000 | `cy.wait()` 等待请求发出的时长 |
| `responseTimeout` | 30000 | `cy.request()`、`cy.wait()`、`cy.fixture()`（测试夹具文件）、Cookie 系列命令与 `cy.screenshot()` 等待响应的时长；16 版的原生路径下不再约束响应处理函数 |
| `pageLoadTimeout` | 60000 | `cy.visit()`、`cy.go()`、`cy.reload()` 等待页面加载事件的时长 |
| `numTestsKeptInMemory` | open 模式 50，run 模式 0 | 内存里保留多少个用例的快照与命令数据 |
| `screenshotOnRunFailure` | true | 失败截图仍然默认开启 |
| `video` | **false** | 13.0.0（2023-08-29）起关闭，官方指向 Test Replay |
| `retries` | `{ runMode: 0, openMode: 0 }` | 失败重试默认关闭 |
| `keystrokeDelay` | **0** | 16.0.0 从 10 改为 0 |
| `visibilityStrategy` | `'modern'` | 16.0.0 用浏览器原生 `Element.checkVisibility()` 替换旧算法；该选项自身已标弃用 |
| `manageBrowserMemory` | true | 16.0.0 由 `experimentalMemoryManagement` 转正 |

`video` 从默认开改为默认关，是这几年被误解最多的一项。很多既有 CI 脚本还在上传 `cypress/videos/`，而那个目录在默认配置下是空的；官方的替代方案是 Test Replay，它能重放到命令粒度的执行现场，而不是一段只能看的录屏。

16 版还顺手扩大了可重试命令的范围：`cy.getCookie()`、`cy.getCookies()`、`cy.getAllCookies()`、`cy.getAllLocalStorage()`、`cy.getAllSessionStorage()` 现在都是 query，会重读并串联重试，受 `defaultCommandTimeout` 约束。附带一个迁移坑——它们不再允许用 `Cypress.Commands.overwrite()` 覆写，要改写成 `Cypress.Commands.overwriteQuery()`。

## 安装与最小示例

### 安装：真正的坑不在下载，在包管理器放行

`npm install cypress --save-dev` 之所以能直接用，是因为 npm 包的 postinstall 脚本会去下载平台对应的 Cypress 二进制并放进全局缓存。**不是首次运行时才下载**，也不是下载 Chrome——浏览器需要你自己在系统或 CI 里装好。

这一步现在会被包管理器的安全策略挡下来，而报错信息不会直接指向这里：

| 管理器 | 版本节点 | 放行方式 |
|------|------|------|
| npm | 11.16.0 起告警，12.0.0 起默认拦截 | `npm install-scripts approve cypress` 后 `npm rebuild cypress`，或在 `package.json` 里加 `allowScripts.cypress` |
| Yarn Modern | 4.14.0 起 `enableScripts` 默认 false | `.yarnrc.yml` 里设 `enableScripts: true` 并把 `cypress` 加进 `npmPreapprovedPackages` |
| pnpm | v10 起要求白名单 | `pnpm --allow-build=cypress add --save-dev cypress`；同时建议关掉 pnpm 的副作用缓存（side-effects cache） |
| Bun | 从 lockfile 可自动识别 | `bun install` 场景需 `bun pm trust cypress` 或写 `trustedDependencies` |

最省事的通用做法是跳过生命周期脚本、显式安装二进制：`bun install --ignore-scripts && bunx cypress install`，其他管理器同理用 `npx cypress install`。CI 里若要把缓存目录挪位置，用 `CYPRESS_CACHE_FOLDER`；`cypress cache path` / `list --size` / `prune` / `clear` 可以直接查和清。默认缓存路径按平台不同：macOS 是 `~/Library/Caches/Cypress`，Linux 是 `~/.cache/Cypress`，Windows 在 `AppData/Local/Cypress/Cache`——把 Linux 那一条当通用值写进缓存 key，是多平台矩阵里常见的失效原因。

系统与环境要求的硬边界：Node.js 22.x / 24.x / >=26.x；macOS 13.5 以上；Ubuntu 22.04、Debian 11、Fedora 43 以上；Windows 10/11 x64。浏览器方面官方只保证 Chrome、Firefox、Edge 的最新三个大版本。

### 第一次运行

```bash
npx cypress open     # 打开 Cypress App，Launchpad 引导选测试类型
npx cypress run      # 无头执行，默认 headless
npx cypress run --browser chrome --spec "cypress/e2e/login.cy.js"
```

`cypress open` 会拉起 Launchpad，依次让你选 E2E 还是组件测试、生成配置文件与目录、挑浏览器。已有配置的项目只需两次点击就能回到测试列表，也可以在命令行里跳过这些提示。

E2E 用例的默认匹配模式是 `cypress/e2e/**/*.cy.{js,jsx,ts,tsx}`；组件测试的默认模式是 `**/*.cy.{js,jsx,ts,tsx}`，也就是**和组件源码就近放置**，不要求集中到某个目录。

### 最小 E2E 用例

```js
// cypress/e2e/login.cy.js
describe('用户登录', () => {
  it('用合法凭证登录后跳转到首页', () => {
    cy.intercept('POST', '/api/session').as('login')

    cy.visit('/login')
    cy.get('input[name=email]').type('alice@example.com')
    cy.get('input[name=password]').type('Sup3rSecret!{enter}')

    cy.wait('@login').its('response.statusCode').should('eq', 200)
    cy.url().should('include', '/dashboard')
    cy.contains('h1', '欢迎回来，Alice').should('be.visible')
  })
})
```

`{enter}` 是 `cy.type()` 的修饰键语法。`cy.visit()` 与 `cy.get()` 分属非 query 与 query 两类，前者只执行一次，后者参与重试——这也是为什么登录态复用要交给 `cy.session()` 而不是在 `before` 里硬写。

### 最小组件测试用例

组件测试的入口是 `cy.mount()`，由框架适配包注册成命令，不需要（也不能）自己 import 一个裸的 `mount` 函数。仓库里这些包的名字是 `@cypress/react`、`@cypress/vue`、`@cypress/svelte`、`@cypress/angular`。

```js
// src/Button.cy.js
import Button from './Button'

describe('<Button />', () => {
  it('点击时触发 onClick', () => {
    const onClick = cy.stub().as('onClick')

    cy.mount(<Button label="保存" onClick={onClick} />)
    cy.contains('button', '保存').click()
    cy.get('@onClick').should('have.been.calledOnce')
  })
})
```

官方当前支持的框架与构建工具组合是有明确版本带的：React 18-19 配 Vite 8 或 Webpack 5；Next.js 15-16（14 已在 16.0.0 被移除）；Vue 3；Angular 21-22（18、19、20 已移除，走 Webpack 5）；Svelte 5 仍是 Alpha。走 Vite 的那几条路径最低版本统一抬到 8。Qwik 与 Lit 属于社区维护的适配。16.0.0 还把 `cypress/angular-zoneless` 合并回 `cypress/angular` 并把 zoneless 设为默认，`zone.js` 不再是必装依赖。

组件测试与 E2E 共用同一个项目、同一套命令日志和 Time Travel。它相对 Jest + React Testing Library 的真正差异在这里：组件挂在真实浏览器的真实 DOM 上，`ResizeObserver`、`getBoundingClientRect`、CSS 过渡、Canvas 都是原生行为，不是被打桩的对象。

## Cypress Cloud 付费的到底是哪几件事

先划清开源与商业的界线：Cypress App 本身免费开源，写、跑、调试、组件测试都在本地；Cloud 是记录测试结果之后的那层能力。免费层（Starter）不是演示账号，而是有真实额度：数据保留 30 天、每个计费周期 500 条测试结果、组织内 10 名用户。测试结果超过上限时，带 `--record` 的运行照常执行，但并行会被关掉、新结果在面板里不可见。

Cloud 侧的能力现在收在 Smart Orchestration 这个名字下，一共五件：

| 能力 | 做什么 | 前提 |
|------|------|------|
| Parallelization | 跨多台 CI 机器分发 spec | 必须同时带 `--record` 与 `--parallel` |
| Load Balancing（负载均衡） | 按预估时长逐个派活，压缩总时长 | 与并行同时生效 |
| Spec Prioritization | 上次失败的 spec 先跑 | 文档页标注 Business Plan |
| Auto Cancellation | 失败数越阈即停 | 文档页标注 Business Plan |
| Re-run Optimization | 重跑只跑失败项（实验性） | Business / Enterprise 或试用期 |

注意「并行按文件分发」这条实现事实：一个装了 50 个用例、单跑 10 分钟的 spec，并行帮不上任何忙，其余机器会空等它。拆文件是前置工作，不是配置项。

Flaky Test Management 是另一件常被误解的事。它不是云端自动重跑——重试用例是本地配置，`retries: { runMode: 2, openMode: 0 }`；Cloud 做的是从这些带重试的记录里识别「同一份代码上先失败后通过」的用例，打分、标记、告警。也就是说，不在配置里打开重试，云端就没有 flake 数据可算；而检测、分析与告警这几项本身要 Team 及以上计划。

```yaml
# .github/workflows/e2e.yml（官方示例的骨架，action 建议锁 v7）
jobs:
  cypress-run:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v7
      - uses: cypress-io/github-action@v7
        with:
          build: npm run build
          start: npm start
          browser: chrome
        env:
          CYPRESS_RECORD_KEY: ${{ secrets.CYPRESS_RECORD_KEY }}
```

GitHub 托管 runner 的 ubuntu 与 windows 镜像自带 Chrome、Firefox、Edge，macOS 镜像另有 Safari。如果不想让 runner 镜像的浏览器升级影响结果，官方推荐 Chrome for Testing：不自动升级、每个版本都有对应构建、不受企业 Chrome 策略约束。另一条路是直接用 `cypress/browsers` 或 `cypress/included` 镜像，标签里把 Node.js、Chrome、Firefox、Edge 的版本写死。

## Studio 没有死，它换了方向

Cypress Studio 的完整时间线，恰好是「别凭印象写现状」的一个样本：

- 10.7.0（2022-08-30）：以 `experimentalStudio` 引入录制能力。
- 此后多年停在实验状态，社区里「Studio 已被放弃」的说法大致从这段空窗来。
- **15.4.0（2025-10-07）：Studio 默认可用，不再需要开实验开关**，并支持在 Cypress 面板内直接改测试代码。16 版里 `experimentalStudio` 这个配置项本身被移除（写了只会收到一条警告）。
- 15.13.0（2026-03-24）：`cy.prompt()` 进入 beta 且无需任何配置，把自然语言提示词描述的步骤编译成命令；元素定位失败时它会尝试自愈，并在命令日志上留下「Self-healed」标记。

Studio 需要外网访问和 sourcemap（源映射），多数配置下源映射是默认打开的。回到应用里能看到的东西：录制支持的交互是 `.click()`、`.type()`、`.check()`、`.uncheck()`、`.select()`；选择器按 `data-cy` → `data-test` → `data-testid` → `data-qa` → `name` → `id` → `class` → tag → attributes → `nth-child` 的优先级挑选，可以用 `Cypress.ElementSelector` 改这个顺序。Studio AI 在你每步录制后比较 DOM 变化并推荐断言，接受、拒绝、逐条编辑都在面板里完成；密码框、信用卡字段和隐藏 input 的值在进入模型前会被剔除。AI 推荐需要关联 Cloud 项目，未登录可用前 6 条推荐；Studio 本身的录制与手工断言不需要账号。

限制也要说清楚：Studio 只服务 E2E，组件测试里不出现；测试处于失败状态时录制与推荐都被禁用；AI 看不到你的业务逻辑和后端规则，它推荐的断言只反映可见 UI 的变化。

还有一条 2026 年才出现的新通道值得单独记一笔，因为它改变的不是「人怎么写测试」而是「编码 agent（智能体）怎么写测试」。15.21.0 加入了 `cypress tap` 命令组：它挂到一个正在 `cypress open` 的会话上，让编码 agent 自己跑 spec，再读回命令日志、错误和当时的 DOM——也就是让 agent 能验证自己改的测试是否真的通过，而不是只报一个结论。配套的还有 Cloud MCP（把 Cloud 的运行数据与 Test Replay 喂给集成开发环境里的 agent）与 Cloud CLI（命令行工具，同样的数据以 JSON 输出到终端）。Cypress 官方把 AI 的用法分成「AI 帮你写测试」和「把你的 agent 喂饱 Cypress 上下文」两类，`cypress tap` 属于后者。

## benchmark 怎么读：官方给的是时长区间，不是加速比

Cypress 官方文档里没有跨工具加速比，给出的是一份诊断用的时长带，出处是《Optimizing test performance》。这组数字的口径值得先说清：**它测的是单个用例和一个 spec 文件的墙钟时间，前提是「你的 suite 现在处于什么健康度」，不是「Cypress 比谁快」**。因此它能支撑的判断是内部诊断，不能支撑跨工具的比较。

| 单个用例时长 | 官方判断 |
|------|------|
| < 3 秒 | 优秀，典型于用桩和程序化准备数据的用例 |
| 3–10 秒 | 可接受，常见于打真实服务端端到端测试 |
| 10–30 秒 | 需要排查，多半有不必要的等待或过重的 UI 准备 |
| > 30 秒 | 差，几乎肯定存在结构问题 |

组件测试另有一条：每个用例应稳定跑在 2 秒以内。

| 单个 spec 时长 | 官方判断 |
|------|------|
| < 1 分钟 | 优秀，内存压力低且并行友好 |
| 1–3 分钟 | 可接受 |
| 3–5 分钟 | 需要排查，可能成为并行瓶颈 |
| > 5 分钟 | 差，应拆分或减少共享准备 |

由此可以反推出几件实操：并行的收益上限由最长的 spec 决定，而不是 spec 数量；而反向地，小于 10 秒的 spec 再拆通常不划算，因为每个 spec 都有浏览器启动这类固定开销。16 版在这条路上继续降开销——`cy.type()` 的默认按键间隔从 10ms 归零、可见性判定换算法、Cookie 与存储命令改为可重试 query、内嵌 `dayjs` 从 1.10.4 升到 1.11.23。这些是可以在自己项目里量出来的改动，而「16 更快」这个笼统说法不能直接搬到你的 suite 上：走 HTTP/2 的页面会明显变快，仍靠 `forceHttp1` 的则完全没有变化。

从这些区间**不能推出**的结论同样重要：不能推出 Cypress 与 Playwright 谁更快；不能推出你观察到的耗时是框架开销还是应用本身慢；也不能把 Cloud Load Balancing 的时长预估当成测量精度。

## 适用边界

### 适合

- **回归对象是自己的 web 应用**，尤其是 SPA（单页应用）、动效密集、组件依赖真实布局的界面。
- **本地开发循环优先**：Time Travel 快照 + 自动等待 + 失败截图把「失败时应用是什么状态」这个问题压到一次悬停。
- **技术栈是 JavaScript / TypeScript**，组件测试要覆盖 React / Vue / Angular / Svelte。
- **需要控制网络响应来造边界条件**：500、超时、弱网、延迟，都直接在 `cy.intercept()` 里造。

### 不适合

- **要同时驱动多个浏览器或上下文**。官方把这条列为永久取舍：不能控制两个同时打开的浏览器；多标签页需要 `@cypress/puppeteer` 这类插件绕。
- **跨域 iframe 是核心场景**。Stripe 或 Braintree 的卡片表单、Auth0 的嵌入登录框、Disqus 评论这类内嵌第三方 frame 无法被自动化；同源 iframe 可以直接查，但「切入 iframe」的命令至今仍是 open proposal。
- **移动真机**。原生或混合 App 该用 Playwright、Appium 或其他工具。
- **测试代码需要在浏览器外运行**。测试代码就是在浏览器里求值的，服务端库不能直接 import；访问数据库或后端要靠 `cy.task()` 与 `cy.request()`。
- **爬虫、索引、性能压测**。官方在 Trade-offs 里逐条点名这些不是 Cypress 的适用范围。
- **非 JS 语言写用例**。Cypress 声明的唯一长期支持语言就是 JavaScript；Gherkin 之类要靠插件引入额外一层。

### 选型口诀

真浏览器里的调试体验和用例内可读的错误信息 → Cypress；多上下文、多标签页、移动仿真、跨语言绑定 → Playwright；WebDriver 标准与既有跨语言资产 → Selenium。

## 五个自测问题

**1. `cy.get('.submit').click()` 在单 origin 与 `cy.origin()` 内部，执行路径差在哪一步？**

<details>
<summary>参考答案</summary>

单 origin 下，spec iframe 里的测试代码通过注入的 driver 直接查 AUT 的 document，可执行性检查与事件派发都发生在同一浏览器内，不需要把命令编码成线协议。跨 origin 时，runner 会追加一个 `spec-bridge-iframe`，命令与结果改由 `postMessage` 往返传递，日志和快照要先序列化，默认单次往返超时 1000ms。所以「没有对象序列化」这句承诺的适用范围是单 origin 链路；跨 origin 段落里存在序列化，只是它发生在同一浏览器的 frame 之间。
</details>

**2. 同一个断言写在 `.should(cb)` 里能通过、写进 `.then(cb)` 偶尔失败，机制上的差别是什么？**

<details>
<summary>参考答案</summary>

`.should()` 属于 query 链的一环：失败时 Cypress 会从这条 query 链的顶部重新发起 DOM 查询并重跑断言，直到通过或撞到 `defaultCommandTimeout`（默认 4000ms）。`.then()` 是非 query 回调，只执行一次，里面的 `expect` 不在重试范围内，执行时刻数据没到位就直接失败。原则是需要等待状态的判断留在链上作为断言，`.then()` 只用于状态已经确定后的一次性计算或副作用。
</details>

**3. 测试从 `app.example.com` 跳到 `checkout.stripe.com` 填卡，直接 `cy.get('input[name=card]')` 会失败。给出两种修复方案和各自代价。**

<details>
<summary>参考答案</summary>

先分清两种「跨域」。若是**页面跳转**到另一个 origin，用 `cy.origin('https://checkout.stripe.com', ...)` 包裹；回调里不能闭包捕获外部变量，要靠 `{ args }` 显式传参，而且 `cy.origin()` 内部禁用 `cy.intercept()`、`cy.session()`、`Cypress.session` 以及嵌套 `cy.origin()`——这四类调用会直接抛错，拦截和会话必须写在 origin 块外面。若是**页面内嵌**的第三方 iframe（Stripe Elements、Auth0 登录框），`cy.origin()` 帮不上忙，跨域 iframe 至今不被支持，只能改写成同域桩页面或关掉 web security（后者测的已经不是真实行为）。另有一条容易被忽略的历史变更：14.0.0 起默认不再注入 `document.domain`，跨子域导航（`www` 与 `docs`）也需要 `cy.origin()` 了。
</details>

**4. 团队用 Jest + RTL 跑组件单测，覆盖率达到 80% 却漏掉 `ResizeObserver` 相关的缺陷。改用 Cypress 组件测试能否补上，代价是什么？**

<details>
<summary>参考答案</summary>

能补上。Jest 默认在 JSDOM（一种 DOM 模拟实现）里跑，没有真实布局引擎，尺寸与可见性都是造出来的，因此 `ResizeObserver`、`IntersectionObserver`、`getBoundingClientRect`、CSS 过渡相关的问题结构上就测不到。Cypress 组件测试把组件挂到真实浏览器的真实 DOM，这些 API 都是原生行为。

代价是三类：一是官方给组件测试的时长预期是每个用例 2 秒以内，而组件测试要拉起浏览器，套件规模上来以后总时长和 CI 机器数都要重估；二是框架版本带被绑得更紧，React 18-19、Angular 21-22、Vite 8、Next.js 15+ 是 16 版当前的支持面，升级链路会互相牵制；三是写法要换，`cy.mount()` 加命令链和 `render()` 加 `fireEvent` 是两套肌肉记忆。更稳的分工是：纯逻辑与渲染树断言留在 Jest / Vitest，涉及布局、动画、浏览器原生 API 的组件走组件测试。
</details>

**5. CI 上套件跑 40 分钟，团队决定上 Cypress Cloud 做并行。除了订阅费用，还有哪些成本要先估？**

<details>
<summary>参考答案</summary>

第一是拆分工作量。并行按 spec 文件分发，长 spec 会让其他机器空等，所以要先按官方时长带（单 spec 目标 1–3 分钟）把大文件拆开，拆的时候处理 `before` 里的共享准备。第二是数据隔离。多个 spec 同时打同一套后端，「创建订单 → 查询订单」这类顺序依赖会互相踩，需要独立账号或数据命名空间。第三是 flake 判定权重要重新校准：Cloud 的 flake 识别依赖本地 `retries` 配置，`runMode: 2` 意味着最多三次通过记录里只要有一次侥幸通过就会被判为 flake，不 review 就会把真实缺陷藏起来。第四是额度，免费 Starter 是每周期 500 条结果、10 名用户、30 天保留，超限后并行会被直接关闭。第五是能力分档：Auto Cancellation 与 Spec Prioritization 的文档页直接署名 Business Plan，Re-run Optimization 需要 Business / Enterprise 或试用期，报价单上的那一档才是最终成本。
</details>

## 排查：五类常见失败

按现象分类，每类给出根因方向而不是逐条错误码。最常见的两类是安装期拿不到二进制与浏览器连不上。

**装完跑不起来，报找不到二进制或 verify 失败。** 根因几乎都在包管理器拦了 postinstall 生命周期脚本（见安装一节的版本节点）。判定方法是 `npx cypress cache list` 有没有内容；修复是显式 `npx cypress install`，或在配置里放行 `cypress`。离线环境用 `CYPRESS_INSTALL_BINARY` 指向内网镜像或本地 zip，构建基础镜像时用 `CYPRESS_INSTALL_BINARY=0` 把下载与安装拆开。

**`cypress run` 卡在启动 Chrome，最终报 ECONNREFUSED，错误标题是连不上 Chrome DevTools Protocol。** 这是企业策略场景：Chrome 策略里的 `RemoteDebuggingAllowed` 被置为 false 时 CDP 端口不存在。先开 `chrome://policy` 核对，或改用不受品牌 Chrome 策略约束的 Chromium / Chrome for Testing。同一类问题在容器里表现为缺 `libnss3`、`libatk`、`libgtk-3-0` 等共享库，用 `cypress/browsers` 或 `cypress/included` 镜像可以整段跳过。

**`cy.intercept()` 注册了却等不到，`cy.wait('@alias')` 超时。** 先分清三种可能：一是拦截确实晚于请求注册，把它挪到 `cy.visit()` 之前或 `beforeEach` 里；origin 块内部不允许调用 `cy.intercept()`，这类拦截必须写在块外。二是请求根本没走被匹配的那条路径，例如跨域 iframe 发出的请求。三是 16 版原生网络下的行为差异——被浏览器自行拒绝的响应现在只留得下请求，`interception.response` 是 `undefined`，此时断言要改成检查应用渲染出的错误态。

**元素肉眼可见，命令却报 Timed out retrying。** 逐个排除：`cy.get()` 本身不要求元素可见，要求可见的是动作命令的可执行性检查和 `should('be.visible')`，所以先确认报的是「找不到」还是「不可交互」；不可交互通常来自遮挡、`pointer-events` 或动画未停；元素在 shadow DOM（影子 DOM）里时要看 `includeShadowDom`；断言写在 `.then()` 里则回到自测问题 2。`{ force: true }` 会同时跳过这些检查，属于诊断手段而不是长期方案。

**升 16 后一批断言莫名变红。** 顺序核对这些改名与删除：`Cypress.env()` 拆成 `Cypress.expose()`（浏览器侧可读的非敏感值）与 `cy.env()`（只留在 Node.js 侧的敏感值）；`cy.exec()` 与 `execTimeout` 删除，改用 `cy.task()` 与 `taskTimeout`；`cy.end()` 删除；`experimentalMemoryManagement` 变 `manageBrowserMemory`；`experimentalFastVisibility` 变 `visibilityStrategy`；`experimentalSourceRewriting` 移除且默认正则改写已覆盖原场景；`viewportWidth` / `viewportHeight` / `blockHosts` 不再允许在测试执行中通过 `Cypress.config()` 修改，要放到 `describe` / `it` 的测试配置里。Electron 作为测试浏览器已弃用，仍隐式依赖它默认回退的脚本应显式设 `defaultBrowser` 或传 `--browser`。

## 下一步读什么

按目的选，不按顺序：

- 想验证本文的执行层描述：从 `packages/app/src/runner/index.ts` 的 `runSpecE2E()` 读起，看 iframe 是怎么搭起来的，再顺着 `packages/driver/src/cypress/cy.ts` 的 `initialize($autIframe)` 看 driver 怎么接上 AUT。
- 想理解重试：`packages/driver/src/cypress/command_queue.ts` 加官方 Retry-ability 页，两遍对照读。
- 想知道 16 改了什么：16 版迁移指南（Migration Guide）与原生网络拦截（Native Network Interception）页，后者每条差异都带前后代码。
- 想把编码 agent 接进测试回路：`app/ai/overview` 与 `cypress tap` 工具页。
- 想评估 CI 成本：先照时长带做一轮诊断，再决定要不要上并行。

和 [Puppeteer 浏览器自动化事实标准]({{< relref "puppeteer-chrome-firefox-automation-devtools-api-guide.md" >}}) 对照读，能看清「测试自己的应用」与「驱动别人的页面」在协议选择上的分岔。Cypress 与 Puppeteer 共用 CDP 这一层，但前者把测试代码送进浏览器，后者把控制权留在 Node.js 侧。
