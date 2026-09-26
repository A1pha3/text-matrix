---
title: "智谱 GLM Coding 抢购助手拆解：一千行油猴脚本里的并发工程学"
date: 2026-06-30T10:45:00+08:00
lastmod: 2026-09-21T12:00:00+08:00
draft: false
slug: "glm-rush-buying-assistant-concurrency-engineering-deep-dive"
github_repo: "qtaxm/glm-rush"
source_key: "gh:qtaxm/glm-rush"
categories: ["技术笔记"]
tags: ["并发编程", "JavaScript", "前端工程", "浏览器脚本"]
description: 逐行读 qtaxm/glm-rush v4.6：1081 行入口脚本只有一条设计主线——把页面读到的东西和自己读到的东西分开。据此讲清 JSON.parse 覆写、fetch/XHR 回喂、自建 winner 并发引擎、Vue 组件兜底、四层支付恢复与服务器校时定时，并标出 README 与代码不一致的四处。
---

## 一、这篇要回答的问题

`qtaxm/glm-rush` 是给智谱 GLM Coding 套餐整点抢购用的油猴脚本，当前 HEAD 停在 2026-04-10 的 v4.6。这篇的目标不是教你抢，而是回答另一个问题：**当页面本身不接受你改的时候，一个只有两千行的浏览器脚本能把自己塞进哪几个位置**。

读完源码，我的判断是：这个脚本只有一条设计主线——**把"页面读到的东西"和"脚本自己读到的东西"彻底分开**。

- 对页面：覆写 `JSON.parse`、`window.fetch` 和 `XMLHttpRequest.prototype` 的三个方法，让页面以为按钮没售罄、请求已经成功。
- 对自己：脚本启动时先把原生实现存成 `_parse`（`:115`）和 `_fetch`（`:142`），之后所有并发请求都用这两个引用发出去、用它们解析。

顺序很关键。`_parse` 存在第 115 行，`JSON.parse` 到第 132 行才被替换；`_fetch` 存在第 142 行，`window.fetch` 到第 352 行才被替换。也就是说，脚本先记住"原来的世界"，再改掉"页面的世界"。没有这一步，它自己发出的 preview 请求会再次撞进自家拦截器，并发引擎递归套娃；它的成功判定也会被自己刚写进去的 `soldOut = false` 污染。

讲这类脚本的文章大多停在"高并发 + 反检测"，恰好漏掉了让这套东西不至于自毁的另外半边。下面按四个注入点、一个并发引擎、一条时间线拆开，每处都给出 `glm-rush-v4.user.js` 的行号。

## 目录

- [一、这篇要回答的问题](#一这篇要回答的问题)
- [二、仓库坐标：2088 行、17 次提交、四处不一致](#二仓库坐标2088-行17-次提交四处不一致)
- [三、注入点一：覆写 JSON.parse 解除禁用态](#三注入点一覆写-jsonparse-解除禁用态)
- [四、注入点二：覆写 fetch 与 XHR，先捕获再回喂](#四注入点二覆写-fetch-与-xhr先捕获再回喂)
- [五、并发引擎 retry()：一轮一批，成功即掐](#五并发引擎-retry一轮一批成功即掐)
- [六、getDelay：三段退避，单位是轮不是次](#六getdelay三段退避单位是轮不是次)
- [七、preview 与 check：两道校验各自判什么](#七preview-与-check两道校验各自判什么)
- [八、注入点三：Vue 组件实例层的两个兜底](#八注入点三vue-组件实例层的两个兜底)
- [九、注入点四：支付恢复的四层降级](#九注入点四支付恢复的四层降级)
- [十、定时：服务器 Date 头校时、10ms 轮询与预热](#十定时服务器-date-头校时10ms-轮询与预热)
- [十一、面板：closed Shadow DOM 与 rAF 合帧](#十一面板closed-shadow-dom-与-raf-合帧)
- [十二、示例：一次 10:00:00 的完整流转](#十二示例一次-100000-的完整流转)
- [十三、可迁移的模式与代码定位](#十三可迁移的模式与代码定位)
- [十四、这份代码不能证明什么](#十四这份代码不能证明什么)
- [十五、常见故障与排查](#十五常见故障与排查)
- [十六、适用边界与红线](#十六适用边界与红线)
- [十七、自测题](#十七自测题)
- [十八、下一步读什么](#十八下一步读什么)

## 二、仓库坐标：2088 行、17 次提交、四处不一致

四个文件，没有测试、没有构建、没有 LICENSE 文件：

| 文件 | 行数 | 作用 |
|------|------|------|
| `glm-rush-v4.user.js` | 1081 | 全部逻辑，标题里"一千行"说的是它 |
| `inject.js` | 1007 | 入口脚本的一份旧副本，见下文 |
| `README.md` | 135 | 功能说明、参数表、更新日志 |
| `.gitignore` | 3 | 三行：`inject.js`、`node_modules/`、`.DS_Store` |

提交历史 17 条，从 2026-04-08 11:17 的 `feat: GLM Coding 抢购助手 v4.0` 到 2026-04-10 的 `docs: README 更新到 v4.6`，跨三天。版本号不是单调往前走的：中间出现过标着 `v4.3`、`v4.7`、`v4.8` 的提交，紧接着是一条 `fix: v4.5 回退到v4.4逻辑 + 修复findBuyButton, 删除v4.5-4.7错误版本`，最后重新以 v4.6 收尾。留下的痕迹是入口脚本里五个版本字符串互相不认识：

```js
// @name         智谱 GLM Coding 抢购助手 v4.0    // 第 2 行
// @version      4.6                             // 第 4 行
// <div class="hd" id="drag"><b>GLM v4.6</b>     // 第 928 行，面板标题
log('v4.5 已加载 (极速并发+时间同步+全自动抢购)'); // 第 989 行，加载日志
console.log('[GLM] v4.0 已注入');                 // 第 1075 行
```

`inject.js` 是这个仓库里最容易读错的文件。`.gitignore` 的第一行就是它，`git check-ignore` 也判命中。时间线是这样的：`inject.js` 在 2026-04-08 11:25 以 `Create inject.js` 进了版本库，同一天的 11:29 作者才补上忽略规则。已跟踪的文件不受新规则影响，于是它一直留在树里。作者对它做的最后一个决定，是把它排除出版本管理。

它是整脚本的一份 v4.4 时期快照：没有 `==UserScript==` 头，面板标题写着 `GLM v4.4`，加载日志写着 `v4.4 已加载`，而入口脚本里没有任何一处引用它。逐处 diff 能看到它比入口脚本少了 `patchVueServerBusy` 和 `forcePayDialog` 两个函数，`patchSoldOut` 里少了 `isServerBusy` 那一行，`autoRecover` 里少了"支付弹窗已出现就跳过"的守卫，`dismissDialog` 还是会把整个 `document` 一起扫的暴力版本。

它也不是"注入到 main world 的副本"。`@grant none` 恰恰说明这一步多余。按 Tampermonkey 文档，`@grant none` 表示脚本不进沙箱、直接跑在页面上下文里，这正是第 352 行覆写 `window.fetch` 能被页面看见的前提。反倒是声明了 `GM_*` 权限时脚本才会被关进沙箱，那时才需要另想办法摸到主世界。所以两个文件的关系只剩一种解释：**忘记删的旧副本**。读代码只认 `glm-rush-v4.user.js`。

README 与代码另有四处对不上，后面各节会展开：

| README 的说法 | 代码的实际情况 |
|---------------|----------------|
| 并发模型是"Promise.race 变体" | 手写 winner Promise 加 `AbortController` 主动取消，全文件没有一处 `Promise.race`（`:240`） |
| 高精度定时"requestAnimationFrame + performance.now，精度 ±2ms" | rAF 只用于 UI 合帧（`:1013`）；定时是 `setInterval(…, 10)` 加服务器时间校准（`:771`），±2ms 无出处 |
| 反检测包含"fetch/XHR toString 伪装" | 只有 `fetch` 伪装了 `toString`（`:411`），被覆写的 XHR 三个方法没有任何伪装 |
| 参数表"爆发次数 20：前 N 次零延迟" | 传给判据的是轮次不是请求数，实际覆盖前 100 次以上（`:88`、`:332`） |

脚本头 `@author` 一栏写的是 `Assistant`。

## 三、注入点一：覆写 JSON.parse 解除禁用态

页面上的"售罄"不是一段静态 HTML，而是接口返回的布尔字段驱动的反应式渲染。你改 DOM，它下一帧就按数据改回来。脚本的处理方式是直接在反序列化层动手：

```js
// :115-137
const _parse = JSON.parse;

function patchSoldOut(obj, visited = new WeakSet()) {
    if (!obj || typeof obj !== 'object' || visited.has(obj)) return;
    visited.add(obj);
    if (obj.isSoldOut === true) obj.isSoldOut = false;
    if (obj.soldOut === true) obj.soldOut = false;
    if (obj.isServerBusy === true) obj.isServerBusy = false;
    if (obj.disabled === true && (obj.price !== undefined || obj.productId || obj.title)) obj.disabled = false;
    if (obj.stock === 0) obj.stock = 999;
    for (const k of Object.keys(obj)) {
        if (k === '__proto__' || k === 'constructor' || k === 'prototype') continue;
        if (obj[k] && typeof obj[k] === 'object') patchSoldOut(obj[k], visited);
    }
}

// 全局 patch: 页面加载时也需要解除售罄状态，否则按钮不可点击
JSON.parse = function (text, reviver) {
    const result = _parse(text, reviver);
    try { patchSoldOut(result); } catch {}
    return result;
};
Object.defineProperty(JSON.parse, 'toString', { value: () => 'function parse() { [native code] }' });
```

三个点和常见写法不一样。

**它不返回新对象。** `patchSoldOut` 就地改字段，改的是页面自己拿到的那一份数据。所以外层不需要知道哪些接口会返回售罄态——脚本压根没打算匹配 URL，第 132 行起页面每一次 `JSON.parse` 的结果都会过一遍递归。

**改写目标是一份字段白名单，不是"把失败改成成功"。** 五个判据分别是 `isSoldOut`、`soldOut`、`isServerBusy`、`disabled`（还要求同层带 `price`/`productId`/`title`，避免误改无关按钮）、`stock === 0`。它不碰 `code`，也不伪造 `bizId`：支付链路的有效性判定全部留给真实接口，见第七节。

**递归遍历所有对象的风险被显式处理了。** `visited` 是 `WeakSet`，挡的是自引用结构造成的死循环；跳过 `__proto__`/`constructor`/`prototype` 三个键，挡的是把响应字段当成污染载荷写进原型链。README 把这条记在 v4.1 的"修复原型链污染风险（Object.keys + WeakSet）"。`Object.keys` 只取自身可枚举属性，是前两道防线成立的前提。

代价同样明确：每次解析多一次深度遍历，页面上所有接口的 `isSoldOut`、`stock`、`disabled` 都会被改，包括你不想改的那些。`@run-at document-start`（`:9`）保证替换发生在页面第一次解析之前——如果晚于首屏那次 `JSON.parse`，按钮已经按真实数据渲染成禁用态，得等下一轮数据更新才有机会被解除。

## 四、注入点二：覆写 fetch 与 XHR，先捕获再回喂

第二个注入点不改响应内容，改的是"这个请求到底要不要发出去"。入口在第 352 行：

```js
// :352-411（节选）
window.fetch = async function (input, init) {
    const url = typeof input === 'string' ? input : input?.url;

    if (url && url.includes(CFG.PREVIEW)) {
        const captured = {
            url,
            method: init?.method || 'POST',
            body: init?.body,
            headers: extractHeaders(init?.headers),
        };
        setState({ captured });
        try { sessionStorage.setItem('glm_rush_captured', JSON.stringify(captured)); } catch {}

        if (state.status === 'success' && state.lastSuccess) {
            log('已抢到, 返回成功响应');
            return new Response(state.lastSuccess.text, { status: 200, headers: { 'Content-Type': 'application/json' } });
        }
        if (state.cache) {
            log('返回缓存响应');
            const c = state.cache;
            setState({ cache: null });
            recoveryAttempts = 0;
            return new Response(c.text, { status: 200, headers: { 'Content-Type': 'application/json' } });
        }
        if (state.proactive || state.status === 'retrying') {
            log('抢购中, 启动重试...');
            const result = await retry(url, {
                method: init?.method || 'POST',
                body: init?.body,
                headers: extractHeaders(init?.headers),
            });
            if (result.ok) {
                return new Response(result.text, { status: result.status, headers: { 'Content-Type': 'application/json' } });
            }
            return _fetch.apply(this, [input, init]);
        }

        log('已捕获请求参数, 等待抢购时间...');
        autoScheduleIfNeeded();
        return _fetch.apply(this, [input, init]);
    }

    if (url && url.includes(CFG.CHECK) && url.includes('bizId=null')) {
        log('拦截 check(bizId=null)');
        return new Response('{"code":-1,"msg":"等待有效bizId"}', {
            status: 200, headers: { 'Content-Type': 'application/json' },
        });
    }

    return _fetch.apply(this, [input, init]);
};
window.fetch.toString = () => 'function fetch() { [native code] }';
```

这段控制流承担四件事：

1. **捕获。** 用户手动点一次真实购买按钮，页面发出的 preview 请求被完整记成 `captured`（含 `method`、`body`、`headers`），写进 `sessionStorage`。之后所有并发请求复用这一份，因为下单参数少任何一个字段后端都不认。
2. **回喂。** 一旦状态对象 `state.status === 'success'`，页面自己发出的 preview 不再出网，直接拿到用 `lastSuccess.text` 造的 `Response`。`state.cache` 是同一机制的单发版本：消费时置 `null`，免得后续所有请求都吃同一份缓存。
3. **接进并发引擎。** 主动模式或正在重试时，页面这一次调用会被换成 `retry()` 的结果。
4. **挡掉无意义的 check。** 页面在还没有 `bizId` 时会发 `check?bizId=null`，这里直接返回一条 `code:-1` 的假响应，不占连接也不产生服务端日志。

XHR 那份（`:416-473`）是同样四条分支，只是把"返回假响应"换成"伪造一个实例"：

```js
// :475-488
function fakeXHR(xhr, text) {
    setTimeout(() => {
        const dp = (k, v) => Object.defineProperty(xhr, k, { value: v, configurable: true });
        dp('readyState', 4); dp('status', 200); dp('statusText', 'OK');
        dp('responseText', text); dp('response', text);
        const ev = new Event('readystatechange');
        if (typeof xhr.onreadystatechange === 'function') xhr.onreadystatechange(ev);
        xhr.dispatchEvent(ev);
        const ld = new ProgressEvent('load');
        if (typeof xhr.onload === 'function') xhr.onload(ld);
        xhr.dispatchEvent(ld);
        xhr.dispatchEvent(new ProgressEvent('loadend'));
    }, 0);
}
```

为什么要同时接两套：仓库里没有证据说明页面用哪种方式发请求，两条路径都写才能不看页面实现。`open`/`send`/`setRequestHeader` 被覆写只是为了攒出 `captured`（记下 `_m`、`_u`、`_h`），跟 `toString` 伪装无关——README 里"XHR toString 伪装"这半句，代码里没有对应实现。

`window.fetch.toString = () => 'function fetch() { [native code] }'`（`:411`）解决的是另一件事：函数被覆写之后 `fetch.toString()` 默认会吐出替换函数的源码，一眼能看出不是原生实现，于是补一个同名方法。它只覆盖 `fetch` 这一个入口，`JSON.parse` 用的是 `Object.defineProperty`（`:137`），XHR 那三个原型方法完全没做伪装。把这行读成"整套反检测体系"会高估它。

## 五、并发引擎 retry()：一轮一批，成功即掐

真正的并发在第 202 到 347 行，函数名是 `retry`。它一次批量发起 `batchSize` 个请求，等这一批的结果，再决定下一轮间隔：

```js
// :219-256（节选）
while (totalAttempt < CFG.maxRetry && !stopRequested) {
    const elapsedMs = performance.now() - state.stats.startTime;
    const isTurbo = elapsedMs < CFG.turboSec * 1000;
    const curConcurrency = isTurbo ? CFG.turboConcurrency : CFG.concurrency;
    const batchSize = Math.min(curConcurrency, CFG.maxRetry - totalAttempt);
    const controllers = [];
    const promises = [];

    for (let j = 0; j < batchSize; j++) {
        totalAttempt++;
        const ac = new AbortController();
        controllers.push(ac);
        promises.push(
            singleAttempt(url, { ...opts, signal: ac.signal }, totalAttempt)
        );
    }
    setState({ count: totalAttempt });

    // 任一成功即取消其余
    const winner = await new Promise(resolve => {
        let settled = false;
        let doneCount = 0;
        promises.forEach((p, idx) => {
            p.then(r => {
                if (r.ok && !settled) {
                    settled = true;
                    controllers.forEach((ac, i) => { if (i !== idx) try { ac.abort(); } catch {} });
                    resolve(r);
                }
                if (++doneCount === promises.length && !settled) resolve(null);
            });
        });
    });

    const results = await Promise.all(promises.map(p => p.catch(() => ({ ok: false, reason: '已取消' }))));
```

**这里最容易被误读的是"为什么不直接 `Promise.race`"。** 因为 `singleAttempt` 从不 reject：网络错误、HTTP 429、售罄、EXPIRE 全被包成 `{ ok: false, reason }` 正常返回（`:191-199`）。`Promise.race` 比的是谁先落地、不问落地内容，结果就是第一个失败响应会赢下整轮，并把已经快成功的那几路取消掉。作者用 `settled` 标志加 `doneCount` 手写的正是"第一个 `ok === true` 的"这个语义，收尾条件是"全批都回来且无人成功"。

赢家确定后其余请求走 `ac.abort()` 主动取消，被取消的那批在 `singleAttempt` 里以 `AbortError` 落到 `reason: '已取消'`（`:197`）。不是等它们自然结束交给 GC。取消完还要 `Promise.all` 收一次全批结果，因为后面的失败分类需要完整的 `reasons` 数组。

`_retryLock`（`:203-206`、`:345-346`）是另一处不起眼的防御：如果用户在重试进行中又点了一次购买按钮，页面新发出的请求会再次进拦截器并调用 `retry`。这时不新建引擎，而是 `log('合并到当前重试...')` 并返回在飞的那个 Promise。

失败分类才是这个循环的主体：

| 现象 | 判据 | 脚本动作 |
|------|------|----------|
| 会话过期 | HTTP 401/403（`:158`） | 记 `HTTP 401 会话过期`，停整个循环并置 `failed`（`:287-291`） |
| 被限流 | HTTP 429（`:161`） | `throttleCount++`，退避 `min(2000 × 2^min(n,4), 16000)` ms；未命中 429 时计数归零（`:294-301`） |
| 网络层全挂 | 一批里 `reason` 全以"网络"开头，且连续 3 批 | `sleep(3000)`（`:276-284`） |
| 单子过期 | `reason` 全是 `EXPIRE` | `continue`，零等待直接下一轮（`:304`） |
| 真没货 | 开抢超过 20 秒且连续 10 轮全售罄 | `sleep(2000)` 降速继续（`:309-323`） |
| 系统繁忙 | `data.code === 555` | 归成 `系统繁忙`，走普通退避（`:192`） |

前 20 秒内即使全售罄也不降速（`:306-309`，注释原话是 `前20秒全速冲`）。日志另有节流：只在 `totalAttempt <= 5 × 并发` 或每满 `20 × 并发` 次时写一条（`:326-329`），否则两千次重试会把面板那 100 条日志窗口刷成噪声。

## 六、getDelay：三段退避，单位是轮不是次

```js
// :86-92
const jitteredDelay = base => Math.round(base * (1 + (Math.random() * 2 - 1) * CFG.jitter));

function getDelay(attempt) {
    if (attempt <= CFG.burstCount) return 0;
    if (attempt <= 50) return jitteredDelay(CFG.fastDelay);
    return jitteredDelay(CFG.slowDelay);
}
```

调用点只有一处，而且传参值得盯一眼：

```js
// :332
const d = getDelay(totalAttempt / CFG.concurrency);
```

`getDelay` 拿到的不是"第几个请求"，而是"第几轮"，且分母固定是 `CFG.concurrency`（并发性，脚本里指每轮并发路数，取值 5），不是极速档的 10。代入 `burstCount: 20`：普通模式下前 100 个请求零延迟；极速模式下每轮发 10 个请求、轮次却只涨 2，前 20 轮实际吃掉 200 个请求。README 参数表里"爆发次数 20：前 N 次零延迟"省略了这个换算。

另外两档的边界是轮次 50，`CFG.fastDelay`（30ms）与 `CFG.slowDelay`（100ms）**都**过 `jitteredDelay`，也就是都带 ±30% 抖动（`CFG.jitter: 0.3`）；README 只在慢速那一档标了抖动。抖动表达式是 `round(base × (1 + (rand×2−1) × 0.3))`，得到 `[21, 39]` 和 `[70, 130]` 两个区间。

三段而不是固定值，理由在时间轴上：

```text
轮次          每轮间隔        这一档在等什么
1   ~ 20     0ms            刚开闸，服务端队列还没堆起来
21  ~ 50     30ms ±30%      限流开始生效，硬撞没有收益
51  ~ ...    100ms ±30%     等窗口过去，同时别把到达序列打成等差数列
```

随机化的动机是时间序列的形状：固定 100ms 会让服务端看到一条几乎等差的到达间隔，用抖动摊开方差是常见做法。至于 `±30%` 这个幅度为什么不是 `±10%` 或 `±50%`，仓库里没有实测记录，只有 `jitter: 0.3` 这一个数字。

顺带一条真实存在的浏览器约束：Chrome 对同一主机的 HTTP/1.1 并发连接上限是 6。极速档一次发 10 个请求，其中 4 个会在连接池排队。所以"10 路"的含义不是"同时有 10 条 TCP 在跑"，而是"同一时刻有 10 个请求挂在脚本手里"——只有在 HTTP/2 上两者才重合。脚本自己的 `batchSize` 并没有按连接上限调整。

## 七、preview 与 check：两道校验各自判什么

`singleAttempt` 是并发引擎唯一的出网单元，一次调用串两个接口：

```js
// :155-188（节选）
const resp = await _fetch(url, { ...opts, headers: randHeaders, credentials: 'include' });
// …状态码分类略，见第五节…
const text = await resp.text();
let data;
try { data = _parse(text); } catch { data = null; }

if (data && data.code === 200 && data.data && data.data.bizId) {
    const bizId = data.data.bizId;
    try {
        const checkUrl = `${location.origin}${CFG.CHECK}?bizId=${encodeURIComponent(bizId)}`;
        const checkResp = await _fetch(checkUrl, { credentials: 'include' });
        const checkText = await checkResp.text();
        let checkData;
        try { checkData = _parse(checkText); } catch { checkData = null; }

        if (checkData && checkData.data === 'EXPIRE') {
            return { ok: false, reason: 'EXPIRE', attempt: attemptNum };
        }
        return { ok: true, text, data, bizId, status: resp.status, attempt: attemptNum };
    } catch (e) {
        return { ok: false, reason: `check异常: ${e.message}`, attempt: attemptNum };
    }
}
```

判据有三处细节值得记住：

- preview 成功的标志是 `data.code === 200` **且** `data.data.bizId` 非空。
- check 是 GET，参数拼在查询串里（`?bizId=…`，做了 `encodeURIComponent`），不是 POST body。
- 失效判据挂在 `checkData.data === 'EXPIRE'` 上，不是 `code`。而 preview 返回 `data.bizId === null` 会被归成"售罄"、`code === 555` 归成"系统繁忙"（`:191-194`）——这三类失败走完全不同的退避路径。

两条通路都用 `_fetch` 和 `_parse`，也就是第一节说的"绕开自己改过的世界"。这里还多一层意义：并发请求解析响应时不希望被 `patchSoldOut` 改写过，否则脚本拿到的原始文本和它自己的判定依据会变成两套。

为什么要多一次 check，而不是拿到 `bizId` 直接付？从代码判据看，preview 给的是"这单落到我名下了"，check 给的是"这单现在还能付"。两者之间存在一个判定过期的窗口。中间只隔了一次往返，说明作者认为窗口内失效不罕见——`EXPIRE` 那一档被单独给了零等待待遇，`continue` 回到循环顶重新发一批。至于服务端用什么机制让 `bizId` 过期（锁、租约还是超时队列），仓库里没有依据。

## 八、注入点三：Vue 组件实例层的两个兜底

README 的 v4.6 更新日志把支付弹窗不出的根因写成"前端 `payComponent.isServerBusy=true` 阻止 `payPreviewFn` 发请求"。第三节的 `JSON.parse` 改写已经能解掉接口里带 `isServerBusy` 的情况，但如果这个标志位在脚本注入之前就被页面置成了 `true`，反序列化层再也碰不到它。于是有了第二份兜底：

```js
// :829-852
function patchVueServerBusy() {
    let attempts = 0;
    const tid = setInterval(() => {
        attempts++;
        if (attempts > 30) { clearInterval(tid); return; } // 15秒后放弃
        const app = document.querySelector('#app');
        const vue = app && app.__vue__;
        if (!vue) return;
        let patched = 0;
        const walk = (vm, depth) => {
            if (depth > 8) return;
            if (vm.$data && vm.$data.isServerBusy === true) {
                vm.isServerBusy = false;
                patched++;
            }
            for (const child of (vm.$children || [])) walk(child, depth + 1);
        };
        walk(vue, 0);
        if (patched > 0) {
            log(`已解除 isServerBusy (${patched}个组件)`);
            clearInterval(tid);
        }
    }, 500);
}
```

约束全写在代码里：500ms 一次、最多 30 次（15 秒后彻底放弃）、从 `#app` 起递归、深度超过 8 层不下探、`$data.isServerBusy === true` 才动、改成功一次就停。它在 `createPanel()` 的启动序列里被调用（`:994`），属于"补一次窗口期"而非常驻。

入口用的是 `app.__vue__` 配 `vm.$children`、`vm.$data`——这是 Vue 2 的实例接口。Vue 3 挂的是 `__vueParentComponent` / `__vue_app__`，`$children` 在 3.0 里已被移除。所以准确说法是：**这份脚本只认 Vue 2 的组件树**。页面实际跑哪个版本，仓库里没有可核实的证据（`@match` 只写了域名）；如果页面已经是 Vue 3，这两个兜底函数会在 `if (!vue) return` 处静默退出。

第二个兜底是直接开弹窗：

```js
// :855-881（节选）
function forcePayDialog(responseData) {
    const app = document.querySelector('#app');
    const vue = app && app.__vue__;
    if (!vue) return;
    let payComp = null;
    const findComp = (vm, depth) => {
        if (depth > 8) return;
        if (vm.$data && 'payDialogVisible' in vm.$data) { payComp = vm; return; }
        for (const child of (vm.$children || [])) { findComp(child, depth + 1); if (payComp) return; }
    };
    findComp(vue, 0);
    if (!payComp) { log('未找到支付组件'); return; }
    if (payComp.payDialogVisible) { log('支付弹窗已显示'); return; }
    const data = responseData && responseData.data;
    if (data) {
        payComp.priceData = data;
        payComp.payDialogVisible = true;
        log('兜底: 已直接设置 payDialogVisible=true');
    }
}
```

调用点在 `startProactive` 成功分支的末尾（`:667-669`）：`await sleep(1500)` 之后执行。这 1.5 秒不是随手写的——同一个函数在第 500ms 已经把控制权交给了 `autoRecover`（`:267`），要等前三层降级试过，再决定要不要绕过组件逻辑硬拧标志位。

## 九、注入点四：支付恢复的四层降级

抢到 `bizId` 之后还要让支付弹窗真的出现。`autoRecover`（`:526-595`）是四段顺序执行的降级，README 管它叫"4 层支付恢复"：

```js
// :526-554（节选）
async function autoRecover() {
    if (recovering || recoveryAttempts >= CFG.recoveryMax || !state.lastSuccess) return;

    // 如果页面上有支付相关弹窗，不要干扰
    const payEl = document.querySelector('[class*="pay"], [class*="qrcode"], [class*="wechat"], [class*="alipay"], [class*="cashier"], iframe[src*="pay"]');
    if (payEl && (payEl.offsetParent !== null || window.getComputedStyle(payEl).position === 'fixed')) {
        log('支付弹窗已出现, 跳过恢复');
        return;
    }

    // 只处理明确的错误弹窗，不暴力清理所有弹窗
    const dialog = findErrorDialog();
    if (!dialog) return;

    recovering = true;
    recoveryAttempts++;
    try {
        log('检测到错误弹窗, 清理中...');
        dismissDialog(dialog);
        await sleep(300);

        // 策略2: 缓存响应 + 重新点购买按钮
        setState({ cache: state.lastSuccess });
        const btn = findBuyButton();
        if (btn) {
            btn.click();
            log('已重新点击购买按钮 (策略2)');
            await sleep(2000);
        }
```

四段按成本递增排列：

1. **清错误弹窗。** `findErrorDialog()`（`:493-508`）先用一组选择器（`.el-dialog`、`.ant-modal`、`[class*="modal"]`、`[role="dialog"]` 等）筛出可见元素，再按文案正则 `/购买人数过多|系统繁忙|稍后再试|请重试|繁忙|失败|出错|异常/` 判定这是错误弹窗。`dismissDialog()`（`:510-524`）只在这个弹窗**内部**找关闭按钮——注释写明"不 fallback 到 document（避免关掉支付弹窗）"——找不到就在该 `dialog` 上直接 `display: none`。
2. **回喂缓存 + 重点击。** `setState({ cache: state.lastSuccess })` 之后 `findBuyButton().click()`。这次点击产生的 preview 请求会命中第四节的缓存分支，页面拿到的是已经成功的那份响应，于是走它自己的正常渲染路径。等 2 秒看结果。
3. **绕过界面拿支付入口。** 若仍无支付弹窗，用 `bizId` 直接 GET check，按返回内容分三路（`:556-579`）：`data` 是以 `http` 开头的字符串就 `window.open`；有 `data.payUrl` 就 `window.open`；有 `data.qrCode` 就交给 `showQRCodeFallback()`（`:598-609`），在页面正中插一个 200×200 的二维码浮层。
4. **兜底提示。** 仍然没有支付元素就 `alert`（告警弹窗）弹出 `bizId`，让用户刷新后自己点。

这四段**不是**"任一成功就 return"的结构，层间没有退出语句，靠的是每次动作前后对支付元素的复查，加上开头的守卫。真正的闸门是 `recoveryAttempts >= CFG.recoveryMax`（默认 3）和 `recovering` 标志。开头那条"支付弹窗已出现就跳过"是这一轮里最贵的教训：被删掉的 v4.7 提交信息原话是 `fix: 修复支付弹窗弹出后被 autoRecover 关掉`——恢复逻辑自己关掉了它要保护的东西。

`findBuyButton()`（`:625-637`）同样是修出来的：先找 `button.buy-btn`，找不到才泛匹配 `/购买|抢购|下单|特惠/` 且文案短于 15 字符且可见。v4.5 的提交信息写着"找错按钮（匹配到'即刻订阅'导航按钮）"，而 `inject.js` 那份旧副本用的还是泛匹配一条路。

`MutationObserver`（`:612-620`）在这里只负责"弹窗什么时候冒出来"：回调不看变更节点，直接调 `findErrorDialog()`，命中且还有恢复次数才触发 `autoRecover`，注释写着"替代 setInterval"。观察者常驻，`childList + subtree` 覆盖整个 body，页面每次增删节点都要跑一遍那组选择器。这是全脚本最不省钱的一处轮询——它换来的收益是弹窗一出现就被处理，而不是等下一个定时器边界。

## 十、定时：服务器 Date 头校时、10ms 轮询与预热

README 把高精度定时写成"requestAnimationFrame + performance.now，精度 ±2ms"。代码里的定时实现跟这两个词关系不大。真正解决起跑点漂移的是**校时**：

```js
// :685-719（节选）
async function syncServerTime() {
    // 用服务器响应头的 Date 字段同步时间
    try {
        const t0 = Date.now();
        const resp = await _fetch(location.origin + '/api/biz/pay/check?bizId=sync', { credentials: 'include' }).catch(() => null);
        const t1 = Date.now();
        const rtt = t1 - t0;
        if (resp && resp.headers.get('date')) {
            const serverTime = new Date(resp.headers.get('date')).getTime();
            // 服务器时间 ≈ 发送时间 + RTT/2
            serverTimeOffset = serverTime - (t0 + rtt / 2);
            log(`时间同步: 服务器偏差 ${serverTimeOffset > 0 ? '+' : ''}${serverTimeOffset}ms (RTT=${rtt}ms)`);
            return;
        }
    } catch {}

    // 备用: 用 worldtimeapi
    try {
        const resp = await fetch('https://worldtimeapi.org/api/timezone/Asia/Shanghai');
        const data = await resp.json();
        const serverTime = new Date(data.datetime).getTime();
        serverTimeOffset = serverTime - Date.now();
    } catch {
        log('时间同步失败, 使用本地时钟');
        serverTimeOffset = 0;
    }
}

function getServerNow() {
    return Date.now() + serverTimeOffset;
}
```

它发一次任意请求，只为读响应头的 `Date`，然后按"服务器时间 ≈ 本地发送时刻 + 半程 RTT"估一个偏移。`Date` 头只有秒级精度，所以这个方法的固有误差量级在 ±500ms 加上 RTT 估计偏差；脚本在 `createPanel()` 里调一次（`:997`），此后不再重测。它真正的收益不是精度而是**基准**——目标从"我的 10:00:00"换成"服务器的 10:00:00"，用户本地时钟慢两秒这件事被消掉了。第二级退化用的是覆写后的全局 `fetch`（也就是会走自家拦截器的那条路），失败才退回本地时钟。

到了定点这一步很朴素：

```js
// :762-790（节选）
if (ms > 4000) {
    setTimeout(() => {
        log('定时前3秒, 自动预热...');
        preheat();
    }, Math.max(0, ms - 3000));
}
const tid = setInterval(() => {
    const remaining = target.getTime() - getServerNow();
    if (remaining > 0 && remaining < 60000) {
        const sec = (remaining / 1000).toFixed(1);
        const timerEl = _shadowRef?.getElementById('timer-info');
        if (timerEl) timerEl.textContent = `-${sec}s`;
    }
    if (remaining <= 0) {
        clearInterval(tid);
        setState({ timerId: null });
        log('时间到! 自动启动抢购!');
        startProactive();
    }
}, 10);
```

`setInterval(…, 10)` 每次比较目标时间与校准后的当前时间，剩余 60 秒内把倒计时写进面板。所谓"高精度"就是这 10ms 的轮询粒度，最后一跳的抖动来自事件循环是否被占满，而不是 rAF。

`preheat`（`:793-808`）是这条时间线上最实用的一段：定时前三秒发 3 个 check 预热请求（每次间隔 200ms），再对 preview 补一个 `HEAD`。注释写着目的"确保连接池暖好"——把 DNS 解析、TCP 握手、TLS 协商这些一次性成本挪到开闸之前，10:00:00 那一下少一次往返。

三个约束决定这套定时的可信边界，都落在浏览器行为上：

- `performance.now()` 在 Chrome 里对非跨源隔离页面钳到 100μs 粒度。我在本机 Chromium 实测最小可观测步进为 0.1ms，该页 `crossOriginIsolated === false`。
- HTML 规范把嵌套超过 5 层的定时器下限钳到 4ms，所以深层回调里的 `setTimeout(fn, 0)` 不是 0。
- 页面不可见时 rAF 不再出帧，定时器同样会被节流。而这个脚本对"切走"没有任何防护：全文件没有 `visibilitychange` 监听，README v4.0 提到的"离开保护"实现是 `:1065` 的 `beforeunload` 确认框，只拦刷新和关标签页。倒计时期间切后台，起跑点就会漂。

顺带一提，脚本里 rAF 唯一的用途是第十一节要谈的 UI 合帧。

## 十一、面板：closed Shadow DOM 与 rAF 合帧

面板挂在一个 host 元素上，隔离靠 shadow root：

```js
// :886-893
function createPanel() {
    const host = document.createElement('div');
    host.id = 'glm-rush-host';
    const shadow = host.attachShadow({ mode: 'closed' });

    shadow.innerHTML = `
<style>
:host{all:initial;position:fixed;top:10px;right:10px;z-index:999999;font-family:Consolas,'Courier New',monospace}
```

`mode: 'closed'` 让外部脚本拿不到 `host.shadowRoot`，代价是脚本自己也要留引用——`_shadowRef`（`:78` 声明、`:987` 赋值）是模块级变量，`refreshUI()`、`appendLogDOM()`、倒计时写入都通过它取节点。选 closed 的收益在运行时——页面自己的脚本遍历不到面板内部——不在调试上，DevTools 看得见它。

样式里最省事的是 `all:initial`：一行把 host 上的继承与级联属性全部复位，页面全局 CSS 就污染不到面板配色和字体。定位（`position:fixed;top:10px;right:10px`）与层叠顺序写在 shadow 内部的 `:host` 规则里，不是 `host.style`。面板还带一个 `#drag` 标题栏，`mousedown` 后在 `document` 上挂 `mousemove`/`mouseup` 实现拖动，松手即解绑（`:974-984`）。

重试期间 `setState` 每轮都会被调用（`:237`、`:259`、`:274`），每次都要刷状态色、三个计数器和按钮可见性。`refreshUI` 用一帧一次合掉：

```js
// :1010-1027（节选）
let uiPending = false;

function refreshUI() {
    if (uiPending) return;
    uiPending = true;
    requestAnimationFrame(() => {
        uiPending = false;
        const shadow = _shadowRef;
        if (!shadow) return;
        const $ = id => shadow.getElementById(id);

        const stEl = $('st');
        if (stEl) {
            stEl.className = 'st st-' + state.status;
            const isTurbo = state.stats.startTime && (performance.now() - state.stats.startTime) < CFG.turboSec * 1000;
            stEl.textContent = state.status === 'idle' ? '等待中'
                : state.status === 'retrying' ? `${isTurbo ? '⚡极速' : ''}重试中... ${state.count}/${CFG.maxRetry}`
                : state.status === 'success' ? `成功! bizId=${state.bizId}`
                : `失败 (${state.count}次)`;
        }
```

`uiPending` 是标准的合帧写法：一帧内无论被请求多少次刷新，只执行一次。状态文本里那个 `⚡极速` 前缀由 `performance.now()` 减 `state.stats.startTime` 现算，所以面板是极速模式唯一可见的证据。

日志走两条互不相干的裁剪路径：`state.logs` 在 `log()` 里用 `splice` 保留最后 `CFG.logMax`（100）条（`:94-101`），DOM 侧在 `appendLogDOM()` 里 `while (el.children.length > CFG.logMax) el.removeChild(el.firstChild)`（`:1049-1060`）。前者其实没被读过——面板日志区是逐条追加 DOM，不从 `state.logs` 重建，这个数组是留着没接上。

快捷键监听挂在 `document` 的 `keydown` 上（`:813-824`），判 `e.altKey` 加 `e.key` 为 `s`/`x`/`h`，`Alt+H` 直接翻 `#bd` 的 `display`。README 把"Alt+H 快捷键在 Shadow DOM 中失效"记成 v4.1 的一项修复，但仓库里看不到修复前的写法，成因无法核实。

## 十二、示例：一次 10:00:00 的完整流转

把前面几节串起来，看一次真实抢购经过哪些行号：

1. `document-start` 注入。第 115、132 行替换 `JSON.parse`；第 352、411 行替换 `window.fetch`；第 416-428 行替换 XHR 的三个原型方法。此后页面拿到的一切解析结果都要过 `patchSoldOut`。
2. `DOMContentLoaded` → `createPanel()`。面板出现，`patchVueServerBusy()` 开始 500ms 轮询，`syncServerTime()` 发出校时请求（`:991-997`）。
3. 用户点一次"特惠订阅"。页面的 preview 请求被记下 `captured` 并写进 `sessionStorage`，然后原样放行；`autoScheduleIfNeeded()` 判断今天 `10:00:00` 还没到，设定定时（`:395-397`）。
4. 09:59:57，`scheduleAt` 里那个 `setTimeout` 触发 `preheat()`：3 个 check 加 1 个 `HEAD` preview，连接池就位。
5. 10:00:00 之后第一个 10ms 边界，`setInterval` 发现 `remaining <= 0`，清掉定时器，调 `startProactive()`。
6. `startProactive` 从 `state.captured` 取出 `url/method/body/headers` 调 `retry()`。中途刷新过页面也没关系，第 70-73 行会从 `sessionStorage` 把 `captured` 恢复回来。
7. 第一轮极速：10 个 `AbortController`、10 个 `singleAttempt`。每个请求带上随机化的 `X-Request-Id`、`X-Timestamp` 和 `Accept-Language` 权重（`:147-153`），用 `_fetch` 出网。
8. 某一路拿到 `code === 200` 且 `data.bizId` 非空，它自己再 GET 一次 check；返回不是 `EXPIRE` 就成为 winner，另外九路被 `ac.abort()`，各自落到 `reason: '已取消'`。
9. `setState({ status: 'success', bizId, lastSuccess })`，同时 `setTimeout(autoRecover, 500)`（`:258-267`）。`startProactive` 那边继续往下：清错误弹窗、`findBuyButton().click()`、`await sleep(1500)`。
10. 第 500ms，页面上还挂着"购买人数过多"。`autoRecover` 关掉它，把 `lastSuccess` 塞进 `state.cache`，再点一次购买按钮。这次 preview 被拦截器直接回喂缓存响应，页面按自己的正常逻辑渲染出支付弹窗。
11. 第 1500ms，如果支付弹窗仍未出现，`forcePayDialog(result.data)` 在组件树上找带 `payDialogVisible` 的那个实例，写 `priceData` 并把它置为 `true`。
12. 之后页面上任何多余的 preview 都会命中第 8 步留下的 `state.status === 'success'` 分支，一律返回同一份 `lastSuccess.text`，不再出网（`:367-370`）。

第 10 与第 11 步是并行的两条兜底，不是串行方案：谁先把弹窗打开，另一个就因为"支付弹窗已出现"或 `payDialogVisible` 已为 `true` 而不动作。

## 十三、可迁移的模式与代码定位

下面每一条都能在 `glm-rush-v4.user.js` 里翻到，行号对应 2026-04-10 的 HEAD。README 更新日志只标过部分改动的版本，其余版本归属需要看提交信息，不确定的这里就不写。

| 模式 | 代码定位 | 换到什么场景成立 |
|------|----------|------------------|
| 先存原生引用再覆写全局：自家用旧的，页面用新的 | `:115`、`:132`、`:142`、`:352` | 任何覆写页面全局对象、自己又要发请求的脚本 |
| 在反序列化层解除前端禁用态，而不是改 DOM | `:117-137` | 页面按接口布尔字段决定按钮能否点 |
| 递归改写响应载荷时用 WeakSet 防环、跳过原型链键 | `:118-127` | 任何把外部 JSON 当对象图遍历的代码 |
| 拦截器回喂缓存响应，让页面走自己的正常渲染路径 | `:367-379`、`:547-554` | 需要"重新触发一次成功"又不想复制业务逻辑 |
| 手写 winner 语义，区分"谁先回来"和"谁先成功" | `:240-253` | 并发分支会正常返回失败值的场景 |
| 成组 `AbortController`，赢家确定后取消其余 | `:230-247`、`:197` | 任何多路重试，省掉无用的服务端配额 |
| 一次在飞的锁，合并重复触发 | `:203-206`、`:345-346` | 用户会连点、事件会重复触发的入口 |
| 按失败原因分派的退避（429 指数、EXPIRE 零等待、连续售罄降速） | `:287-323` | 任何带限流与资源有效期的轮询 |
| 三段退避加双侧抖动 | `:86-92`、`:332` | 需要让到达间隔不像等差数列的轮询 |
| 用响应 `Date` 头加 RTT/2 估服务端时钟，第三方时间作退化 | `:685-715` | 所有整点触发的场景，含秒杀与抢课 |
| 定时前几秒预热 DNS/TCP/TLS | `:793-808` | 首字延迟敏感的一次性请求 |
| 关闭按钮只在容器内部查找，不 fallback 到 document | `:510-524` | 任何"清理干扰元素"的自动化 |
| `mode: 'closed'` 的 Shadow DOM 配 `all:initial` 与模块级引用 | `:886-893`、`:987` | 注入式面板，防页面全局样式与遍历 |
| `uiPending` 加 rAF 合帧节流 | `:1010-1046` | 高频状态更新下的界面渲染 |

表里最值得抄走的是第一条和第三条。覆写全局对象的人很多，覆写之后还记得用原生引用发自己的请求、还在遍历外部数据时防住原型链污染，这两处都不起眼，也都不出现在任何 README 里。

## 十四、这份代码不能证明什么

写到这里需要划清这篇能支撑哪些结论：

- **没有任何性能证据。** 仓库里没有测试、没有测量脚本、没有一次成功率记录。README 的"精度 ±2ms"在代码里找不到对应实现（见第十节）。凡是"这样写能快多少""能不能抢到"的问题，这篇一个都答不了。
- **没有 LICENSE 文件。** README 结尾写 MIT，GitHub 也识别不出许可证，仓库里只有那四个文件。要引用或改写这些代码，按许可未声明处理更稳妥。
- **对端的设定全是推测。** 页面是不是 Vue 3、有没有 `fetch.toString()` 风控、限流阈值多少、额度几秒放完，仓库里都没有证据。第八节能确定的只是"脚本自己认 Vue 2 的接口"。
- **静默失败是这套设计的固有属性。** 页面若把 `isSoldOut` 改名成 `sold_out`，`patchSoldOut` 不再命中，面板照样显示"重试中"，只是每一轮都归到 `code=…`；check 换了返回结构，策略 3 会读不到 `payUrl` 而落到 `alert`。拦截器的四类判据是硬编码字符串，页面改版一次就悄悄失效，报错方式是没有报错。
- **`inject.js` 不是第二套实现。** 它是落后两个版本的副本，读它得到的结论会错（第二节）。
- **一次抢购的净请求量。** 默认 `maxRetry: 2000` 限的是请求总数，极速档每轮 10 个请求，几十轮就会撞满；每一次成功的 preview 后面还跟着一次 check。这个量级本身就是服务端限流要处理的东西，也是下一节的边界由来。

## 十五、常见故障与排查

这份代码的日志文案是现成的排查表——`log()` 输出的字符串直接对应到具体分支。按常见程度排：

| 面板出现的话 | 位置 | 说明什么 | 能做什么 |
|--------------|------|----------|----------|
| `请先手动点一次购买按钮` | `:641-643` | `captured` 为空，页面从未发出可匹配的 preview | 真的去点一次；确认接口路径仍是 `CFG.PREVIEW` |
| `已捕获请求参数, 等待抢购时间...` | `:396` | 捕获成功，已自动设定时 | 等，或按 `Alt+S` 立刻抢 |
| `会话已过期, 请重新登录!` | `:288` | 收到 401/403，循环已停 | 重新登录，再点一次购买 |
| `限流, 退避16000ms...` | `:297` | 连续吃 429，退避已到上限 | 把极速档的 10 路降下来，16 秒已经是最大退避 |
| `网络异常, 暂停3秒...` | `:281` | 一整批请求全落到"网络"分类 | 查本地网络与代理 |
| `连续售罄, 可能已抢完, 降速 (2s)...` | `:319` | 开抢 20 秒后连续 10 轮全售罄 | 这一档基本没戏，留着等下一轮 |
| `支付弹窗已出现, 跳过恢复` | `:532` | 正常，说明前几层已生效 | 别期待还有第二次动作 |
| `未找到支付组件` | `:867` | 组件树里没有带 `payDialogVisible` 的 `$data` | 页面改版或不是 Vue 2，`forcePayDialog` 失效 |
| `时间同步失败, 使用本地时钟` | `:712` | 两级校时都失败，起跑点退回本地 | 自己保证系统时间同步 |
| `达到上限 2000 次` | `:338` | 走完 `maxRetry`，状态置 `failed` | 面板"上限"输入框可改，范围 10 到 9999 |

面板根本不出现时先查 `@match`。仓库同时写了 `*://www.bigmodel.cn/*` 和 `*://bigmodel.cn/*`（`:7-8`），README v4.1 里记着"修复 `@match` 规则不匹配 `bigmodel.cn`（无 www）"。只写带 www 的那一条，就会漏掉一半入口。

## 十六、适用边界与红线

可以迁移的部分，是"页面不接受你改"时的四个落点加一套退避：数据反序列化层、请求发送层、组件实例层、渲染层，以及一个把自己摘出去的并发引擎。做灰度开关误关的临时自救、写内部系统的批量重试、给轮询加退避，都能直接借鉴。

不该迁移的是它的对抗前提：

- 对公众票务、电商大促、限量商品做同样的事，代价是别人抢不到。这不是技术问题，是公平性问题。
- 想压测就别用它。要测吞吐该用 k6、wrk、Locust 这类有并发模型和统计输出的工具。这个脚本连一次总耗时都没记录——`stats.avgMs` 字段在 `:61` 声明，全文没有任何地方写它；同样没被使用的还有 `:85` 的 `rand()`。
- 平台条款的风险不在这个仓库里。脚本只提供客户端逻辑，服务条款是否禁止自动化下单无从由仓库判断；它操作的是你自己的登录会话，高频并发被风控之后账号承担什么后果，代码里没有任何提示。
- 还有一个不那么显眼的点：这类脚本每多一个人用，服务端的限流阈值就往上抬一格，最后所有使用者的到达间隔都被压得更长。它优化的正是别人依赖的那个资源。

我读这份源码的收获不在"抢购"，在两个具体习惯：改全局对象之前先把原生引用存下来；遍历外部数据之前先想清楚 `__proto__` 和环。这两条在任何前端工程里都用得上，而且都不会有 README 替你写。

## 十七、自测题

1. 把第五节的 winner 判定换成 `Promise.race(promises)` 会出什么问题？为什么这里的分支不能 reject？
2. `getDelay(totalAttempt / CFG.concurrency)` 的分母固定是 `CFG.concurrency`。极速阶段每轮实际发 10 个请求，这会让"前 20 次零延迟"覆盖到第几个请求？
3. `patchSoldOut` 为什么必须带 `WeakSet` 并跳过 `__proto__`/`constructor`/`prototype`？少掉任何一条会怎样？
4. 第四节的缓存回喂分支消费 `state.cache` 时立刻把它置 `null`。如果不清空，后续请求会出什么问题？
5. `autoRecover` 在第 500ms 启动，`forcePayDialog` 在第 1500ms 执行。这个先后关系如果反过来会怎样？
6. 页面改版后把 `isSoldOut` 改成 `sold_out`，第三节和第十四节给出的机制里哪一条最先失效？面板上会看到什么？
7. README 写"反检测：fetch/XHR toString 伪装"，按第四节，这句话里哪一半在代码中找不到实现？

<details>
<summary>参考答案要点</summary>

1. `singleAttempt` 把所有失败都包成正常返回值（`:191-199`），`Promise.race` 比谁先落地，第一个失败就会赢下整轮并触发 `ac.abort()`，把可能快成功的那几路掐掉。这里的分支必须"正常返回失败"，否则收集链路没有 `.catch` 可用（`:243`）。
2. 轮次到 20 时 `totalAttempt` 已经到 200——极速档每轮 10 个请求，而 `totalAttempt / 5` 每轮涨 2。普通档是前 100 个请求。
3. `WeakSet` 挡自引用结构的无限递归；跳过三个原型链键挡响应字段被当成污染载荷写进原型。少前者会卡死主线程，少后者是真实的数据注入面。
4. 后续所有 preview 会永久吃到同一份旧缓存，包括用户改了套餐之后发出的真实请求。
5. 反过来会让 `forcePayDialog` 抢在页面自己的渲染路径之前硬拧标志位，也就绕开了"让页面自己弹窗"这个更稳的选择。开头那条支付弹窗守卫正是为此存在。
6. `patchSoldOut` 的五个判据不再命中，按钮维持禁用态。面板仍显示"重试中"并每轮记 `code=…`，因为并发引擎走的是真实接口、不依赖按钮能不能点。
7. XHR 那一半。`open`/`send`/`setRequestHeader` 被覆写后没有任何 `toString` 伪装，脚本只给 `fetch`（`:411`）和 `JSON.parse`（`:137`）做了。

</details>

## 十八、下一步读什么

想接着往下读源码，这三段密度最高：

- `:202-347`，`retry()` 全函数。146 行里塞了并发批量、取消、六类失败分派和日志节流，是这份脚本真正的工程量所在。
- `:352-488`，fetch 与 XHR 两条拦截路径加 `fakeXHR`。看同一个语义怎么在两套接口上各实现一遍。
- `:526-609`，`autoRecover` 与 `showQRCodeFallback`。四段降级和它的守卫条件都在这 84 行里。

外部资料按用途取三份：

- Tampermonkey 的脚本文档，管 `@grant`、`@run-at`、`@match` 的准确语义；
- MDN 的 `AbortController` 与 `Response` 构造；
- HTML 规范的定时器一节，管 4ms 钳制与嵌套层级。

上面所有关于浏览器行为的断言都出自这三份。

想验证"回喂缓存"这套机制而不碰真实站点，可以在本地起一个返回 `code: 200` 和一个 `bizId` 的接口，把 `DEFAULT_CFG` 里的 `PREVIEW`/`CHECK` 两个常量改成自己的路径，再把 `@match` 指到那个本地域名。脚本对页面的全部假设都收在这两行常量里，改完就能观察第四节那四条分支各自什么时候命中。

---

**仓库**：<https://github.com/qtaxm/glm-rush>
**核对版本**：v4.6（提交 `9d5e454`，2026-04-10）
**许可**：README 声明 MIT，仓库内无 LICENSE 文件
**源码规模**：入口 `glm-rush-v4.user.js` 1081 行，另有旧副本 `inject.js` 1007 行

**参考**

- [qtaxm/glm-rush](https://github.com/qtaxm/glm-rush)
- [Tampermonkey 脚本元数据文档](https://www.tampermonkey.net/documentation.php)
- [MDN 应用程序接口文档：AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)
- [HTML 规范：定时器与嵌套层级钳制](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers)
