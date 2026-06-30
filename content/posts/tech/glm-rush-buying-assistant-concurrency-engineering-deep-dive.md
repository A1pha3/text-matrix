---
title: "智谱 GLM Coding 抢购助手深度拆解：一千行油猴脚本里的并发工程学"
date: 2026-06-30T10:45:00+08:00
lastmod: 2026-06-30T11:00:00+08:00
draft: false
slug: "glm-rush-buying-assistant-concurrency-engineering-deep-dive"
categories: ["技术剖析", "前端工程", "抢购脚本"]
tags: ["tampermonkey", "userscript", "并发重试", "反检测", "shadow-dom", "vue-hook", "json.parse-hook", "高精度定时", "智谱glm", "抢购脚本"]
description: "把智谱GLM Coding抢购助手v4.6的两千行油猴脚本逐层拆开——双模式并发引擎、JSON.parse定向拦截、Shadow DOM UI隔离、Vue组件深度hook、4层支付恢复、高精度定时——讲清楚每一行背后在对抗什么、保护什么、放弃什么。
---

## 一、抢购工程学为什么难

抢购脚本听起来很"灰产"，但当你真的动手去写，会发现这件事的工程难度被严重低估了。

第一层难度是**时间窗口的稀缺性**。智谱 GLM Coding Plan 每天 10:00:00 整点放出当日额度，5 秒内大概率售罄——也就是说，从你按下"开始"按钮到你应该收到支付链接，**整个系统的端到端延迟必须控制在秒级以内**。一个常见误区是"反正并发够高就行"，但现实是：HTTP/1.1 同域连接池默认只有 6 路并发（Chrome 实际值），并发数从 5 提升到 10 之后真正起作用的是前 6 路，后面的都在排队。**盲目堆并发数只会让连接池排队更长，反而拖慢平均响应时间**。

第二层难度是**对端的反制**。服务端知道你大概会来并发，所以会有限流；前端知道有人会改 DOM，所以会有 DOM 完整性校验；风控知道你大概会改 fetch，所以会检查 `fetch.toString()`。**这不是一个无防御的目标，而是一个会进化的对手**。一个新手抢购脚本在第一周可能跑得通，第二周被风控升级拦截是常态。

第三层难度是**前端框架的屏障**。你要 hook 的页面运行在 Vue 3 之上，弹窗逻辑、按钮状态、组件可见性都通过 Vue 的响应式系统驱动。你改 DOM 没用，Vue 一帧之内会重写回来——这是为什么仓库作者选择在 `JSON.parse` 层定向拦截，而不是 hook fetch 改响应体。

`qtaxm/glm-rush` 是一个用 Tampermonkey 跑的油猴脚本，v4.6，2026-04-10 发布。它用 2088 行代码把上面三层难度**逐一拆解、逐一拆穿**。这篇文章要做的是把这 2088 行背后的工程取舍**逐层拆给你看**——读完之后你应该能回答"在对抗性前端环境里做高并发，工程上能做到什么程度"。

## 二、对比一下：v3.2 原版 vs v4.6 当前

在进入细节之前，先看一张演进对比——这张表基本就是抢购工程学的"问题清单"，也是 v4.6 相比原版的全部增量：

| 维度 | v3.2 原版 | v4.6 当前 | 解决了什么 |
|------|-----------|-----------|-----------|
| 并发模型 | 单线程串行 | 10+5 双模式 Promise.race | 串行太慢 |
| 重试间隔 | 固定 100ms | 爆发→快速→慢速三段+±30%抖动 | 规律易被检测 |
| 时间精度 | setTimeout ±10ms | rAF+perf.now ±2ms | 起跑点漂移 |
| UI 隔离 | 普通 DOM | Shadow DOM closed 模式 | 被全局 CSS 污染 |
| 按钮响应 | 无法绕过售罄态 | JSON.parse 定向拦截 | 售罄后按钮死锁 |
| 弹窗拦截 | 完全靠用户 | MutationObserver 自动恢复 | 错误弹窗阻塞 |
| 支付弹窗 | 不弹出=结束 | 4 层渐进降级恢复 | 弹窗被多层拦截 |
| 反检测 | 无 | toString Proxy 伪装 | fetch 被检测 |
| 持久化 | 无 | localStorage+sessionStorage 分层 | 配置/参数丢失 |
| 快捷键 | 无 | Alt+S/X/H | 抢购期手动操作慢 |
| 离开保护 | 无 | visibilitychange 挂起 | 后台被节流丢精度 |

短短 7 天（2026-04-03 至 2026-04-10）、5 个版本、约 20 个独立修复，把"能在浏览器里抢到东西"升级成了"在对抗性前端环境里稳定抢到东西"。

## 三、如何阅读本文

如果你只想看结论：直接跳到第十八节"一句话总结"+ 第十五节"工程模式表"。

如果你想理解设计动机：建议按节序读，重点关注每节的"为什么这样设计"。

如果你想动手复现：按第十五节表格里的"代码定位"列，在源码里搜对应函数名。

下面进入正题——11 个子系统的逐层拆解。

## 四、架构总览：11 个子系统

仓库两个文件：入口 `glm-rush-v4.user.js`（1081 行）+ 注入 `inject.js`（1007 行）。所有业务逻辑都在入口脚本里，inject.js 是反检测层的 main world 注入副本——为什么要分两个文件？因为 `@grant none` 模式下油猴脚本默认运行在 page world（与页面 JS 隔离），但风控会检测 `window.fetch !== nativeFetch`，所以需要把 fetch 包装代码注入到 main world 才能与原生 fetch 同源。

11 个子系统按依赖关系排列：

```
┌────────────────────────────────────────────────────────────────┐
│  1. 配置层  localStorage 持久化 + DEFAULT_CFG 默认值           │
│  2. 状态层  不可变更新 + 单一 state 对象                        │
│  3. 并发引擎  双模式: 极速 10 路 / 普通 5 路 + Promise.race    │
│  4. 自适应间隔  爆发(零延迟) → 快速(30ms) → 慢速(100ms±30%)   │
│  5. preview + check 双校验  EXPIRE 即重试                      │
│  6. 反检测层  fetch/XHR toString 伪装 + JSON.parse 定向拦截    │
│  7. UI 隔离  Shadow DOM 浮动面板，不被页面 CSS 污染            │
│  8. Vue 组件 hook  拦截 isServerBusy / payDialogVisible        │
│  9. 4 层支付恢复  清弹窗 → 缓存重点击 → 取支付链接 → 兜底提醒  │
│ 10. 高精度定时  requestAnimationFrame + performance.now ±2ms   │
│ 11. 持久化 + 快捷键 + MutationObserver 弹窗监控                 │
└────────────────────────────────────────────────────────────────┘
```

## 五、配置与状态：不可变更新避免渲染抖动

油猴脚本最容易写坏的地方就是状态管理——脚本可能跑几十分钟、用户可能刷新页面、可能被注入多次。仓库的状态层非常克制：

```js
let state = {
    status: 'idle',      // idle | retrying | success | failed
    count: 0,
    bizId: null,
    captured: null,      // 捕获的请求参数
    cache: null,         // 成功响应缓存
    lastSuccess: null,
    proactive: false,
    timerId: null,
    logs: [],
    stats: { total: 0, success: 0, errors: 0, avgMs: 0, startTime: 0 },
};
```

整个文件看不到 `state.foo = bar` 这种直接赋值。每次更新都构造新对象：

```js
function setState(patch) {
    state = { ...state, ...patch };
    if (panel) renderPanel();
}
```

**为什么这样设计？** 并发重试会在毫秒级触发几十次渲染。如果直接改 `state` 然后同步 `renderPanel()`，会在浏览器里出现一帧里多次 layout 的情况——Shadow DOM 里的日志顺序错乱就是 v3.2 时代的 bug。不可变更新让"当前状态快照"始终是一个不可变引用，渲染层只需对比引用就能跳过重渲染。

配置层也一样——`loadCfg()` 从 localStorage 读，`saveCfg()` 写，运行时所有地方都从 `CFG` 这个冻结常量读，不存在"读到一半被改了"的问题。

## 六、并发引擎：双模式为什么比纯并发更聪明

抢购脚本的核心永远是并发，但**所有请求同时打出去**这件事没那么美好：

- 服务端识别到 10 路并发直接限流，所有请求返回 429，**一次成功机会都没有**
- 但 1 路串行又太慢，等到第 5 秒黄花菜都凉了

仓库的解法是"两段式"：

```js
const turboConcurrency = 10;  // 前 turboSec 秒（默认 5s）
const concurrency      = 5;   // 之后
```

```js
async function rush() {
    const start = performance.now();
    const isTurbo = () => (performance.now() - start) < CFG.turboSec * 1000;
    const N = () => isTurbo() ? CFG.turboConcurrency : CFG.concurrency;

    while (state.count < CFG.maxRetry && state.status === 'retrying') {
        const tasks = Array.from({ length: N() }, (_, i) => doOne(i));
        const result = await Promise.race(tasks.map(p => p.catch(e => e)));
        if (result?.bizId) { setState({ status: 'success', bizId: result.bizId }); return; }
        await sleep(adaptiveDelay(state.count));
        setState({ count: state.count + 1 });
    }
}
```

**为什么这样设计？** 这里的 `Promise.race` 不是 10 路并发一起发完然后等，而是 10 路并发只要有任何一路成功就立刻取消其余。剩下的 Promise 会被 GC 回收（如果业务实现里没有挂 finally 的话）。

为什么"前 5 秒极速"是合理的？因为抢购的时间窗口本身就是前 5 秒——10:00:00 整点放出第一批，5 秒内大概率售罄。**极速模式赌的就是前 5 秒的服务端还来不及反应限流**，5 秒之后自动退到 5 路温和模式，避免触发风控。这是用"概率窗口"换"成功率"的经典做法。

**常见误用**：把 `turboSec` 调到 30 秒甚至更长——这等价于全程 10 路并发，会被风控当作攻击直接封 IP。仓库默认 5 秒是经过实测的平衡点。

## 七、自适应间隔：三段退避背后的概率学

光有并发路数还不够。**间隔**才是真正决定"能不能抢到"和"会不会被封"的旋钮。仓库把它拆成三个阶段：

```js
function adaptiveDelay(count) {
    if (count < CFG.burstCount) return 0;               // 爆发：前 20 次零延迟
    if (count < CFG.burstCount + 100) return CFG.fastDelay;  // 快速：30ms
    return CFG.slowDelay * (1 + (Math.random() - 0.5) * 2 * CFG.jitter);  // 慢速：100ms ±30%
}
```

```text
重试次数     间隔
─────────────────────────────────
0   ~  20   0ms    （爆发：刚开闸就压满）
21  ~ 120   30ms   （快速：服务器开始限流前的缓冲）
121 ~ ...   100ms ±30%  （慢速：等限流窗口过去）
```

**为什么是 20 次零延迟而不是 50 次？** 浏览器 HTTP/1.1 同域连接池默认 6 个并发，多了也是排队。0ms 间隔在前 6 个请求上才有意义（剩下的都在排队），超过这个数只是徒增调度开销。20 次刚好把"前 6 路压满 + 6 路排队 + 8 路排队余量"用完。

**±30% 抖动是反检测的关键**。如果每次间隔都是精确的 100ms，服务端拿到的请求时间序列就是一条完美的等差数列，任何"等差数列模式"检测器一眼就能识别。`100ms ±30%` 之后，请求间隔变成 `[70, 130]` 区间里的伪随机序列——人类看不出规律，简单的模式识别也抓不到。

**为什么抖动幅度是 ±30% 不是更大或更小？** 经验值：±10% 太规律容易被检测；±50% 方差过大反而拖慢节奏（运气不好连着几次抽到 150ms）。±30% 是一个"既能骗过模式识别、又不至于拖慢平均间隔"的甜点。

## 八、preview + check 双校验：两个 API 都不能省

这是抢购脚本里**最反直觉的设计**——很多脚本拿到 bizId 就直接调支付，但其实支付链路里的两个 API 各自有独立的状态机：

```
preview → 返回 bizId (可能已 EXPIRE)
check   → 校验 bizId 是否仍可支付
        ├── 通过 → 触发支付
        └── EXPIRE → 立即重试 preview
```

```js
async function doOne(idx) {
    const captured = state.captured;
    if (!captured) throw new Error('no captured');

    const previewRes = await fetch('/api/biz/pay/preview', {
        method: 'POST',
        body: JSON.stringify(captured.body),
    });
    const previewData = await safeJSON(previewRes);
    if (previewData?.code !== 0 || !previewData?.data?.bizId) throw new Error('preview fail');
    const bizId = previewData.data.bizId;

    const checkRes = await fetch('/api/biz/pay/check', {
        method: 'POST',
        body: JSON.stringify({ bizId }),
    });
    const checkData = await safeJSON(checkRes);
    if (checkData?.code === 'EXPIRE') throw new Error('expire');
    if (checkData?.code !== 0) throw new Error('check fail');

    return { bizId };
}
```

**为什么不能省掉 check？** 因为智谱后端里 bizId 是**乐观锁**——preview 给你一个 bizId 的时候它还是"未占用"的，但到你发起支付的几十毫秒里，别人可能已经抢先支付了。check 就是给你一个"现在还有效吗"的机会。

很多脚本栽就栽在这里：拿到 bizId 立刻跳支付，结果 90% 的支付请求都是 EXPIRE，回头看日志才发现全白跑了。**双校验的本质是用一次额外的 round-trip 换掉绝大多数注定失败的支付请求**。

## 九、反检测层：在 JSON.parse 层定向拦截

这是整个仓库**最工程化**的部分——它不是简单"伪装 fetch"，而是**定向 hook 在 JSON 反序列化那一层**，因为现代前端框架的所有状态判断都依赖 JSON.parse 的返回值。

### 9.1 为什么 hook 在 JSON.parse 而不是 fetch

直觉上是 hook fetch，把响应里的 `code: 'SOLD_OUT'` 改成 `code: 0`。但现代前端是这么用的：

```js
const data = await res.json();  // 内部调 JSON.parse
if (data.code === 'SOLD_OUT') {
    button.disabled = true;
    return;
}
```

你 hook fetch 把响应体改了，但**响应体的字符串已经被传给 `res.json()` 了**。如果响应已经被框架读完（比如另一个组件先读了 res.body），你改 fetch 已经晚了。

更稳的办法是 hook 在 `JSON.parse` 本体：

```js
const _JSONparse = JSON.parse;
JSON.parse = function (text, reviver) {
    const obj = _JSONparse.call(this, text, reviver);
    // 只针对支付相关 API 定向改写
    if (obj && typeof obj === 'object' && 'code' in obj) {
        if (text.includes('pay/preview') || text.includes('pay/check')) {
            return patchPayResponse(obj);  // 改 isServerBusy / payDialogVisible
        }
    }
    return obj;
};
```

这种"在序列化层定向 patch"的思路在 v4.1 之后就固化了，v4.6 加了 `isServerBusy` 拦截，逻辑是同一套：

```js
function patchSoldOut(obj) {
    // 把限流响应改成成功响应
    if (obj?.code === 'RATE_LIMIT') return { ...obj, code: 0, data: { bizId: 'fake' } };
    return obj;
}
function patchVueServerBusy() {
    // 定时扫描 Vue 组件实例，把 isServerBusy 强制改 false
    setInterval(() => {
        document.querySelectorAll('*').forEach(el => {
            const vnode = el.__vueParentComponent;
            if (vnode?.ctx?.isServerBusy) vnode.ctx.isServerBusy = false;
        });
    }, 100);
}
```

### 9.2 fetch / XHR toString 伪装

前端风控不仅看请求频率，还会检查 `window.fetch.toString()` 是否等于原生实现。油猴脚本 hook 之后 `fetch.toString()` 会变成 `"function fetch() { [native code] }"`——一眼假。

仓库的解法是**保留原函数引用 + 用 Proxy 包装**：

```js
const _fetch = window.fetch;
window.fetch = new Proxy(_fetch, {
    apply(target, thisArg, args) {
        return Reflect.apply(target, thisArg, args).then(res => {
            // ... 拦截响应
            return res;
        });
    },
    get(target, prop) {
        if (prop === 'toString') return () => 'function fetch() { [native code] }';
        return Reflect.get(target, prop);
    },
});
```

XHR 同理，对 `XMLHttpRequest.prototype.open` 做 Proxy wrap。toString 调用被拦下来返回 native code 字符串，绕过风控的反射检查。

## 十、Shadow DOM 浮动面板：硬隔离的代价

抢购脚本的面板要常驻在页面上，但又**不能**让 bigmodel.cn 的全局 CSS 影响按钮颜色和位置。仓库用 Shadow DOM 做硬隔离：

```js
const host = document.createElement('div');
host.id = 'glm-rush-host';
host.style.cssText = 'position:fixed;top:10px;right:10px;z-index:2147483647;';
document.body.appendChild(host);

const shadow = host.attachShadow({ mode: 'closed' });
shadow.innerHTML = `
    <style>
        .panel { background:#1a1a1a;color:#fff;font:13px monospace; ... }
        button { background:#0a84ff;color:#fff;border:none;padding:4px 8px; }
    </style>
    <div class="panel">...</div>
`;
```

`mode: 'closed'` 让外部 JS 拿不到 shadow root 引用，进一步隔离。`z-index: 2147483647`（int32 最大值）保证不被任何 z-index 盖住。

**关键细节**：`Alt+H` 快捷键在 v4.1 之前是失效的——因为快捷键监听挂在普通 DOM 的 button 上，Shadow DOM 里的 button click 不会冒泡到普通 DOM。修复方案是把监听挂在 `document` 上，捕获阶段拦截：

```js
document.addEventListener('keydown', (e) => {
    if (e.altKey && e.code === 'KeyH') togglePanel();
}, true);  // 第三个参数 true = capture
```

**取舍说明**：`mode: 'closed'` 在反检测层面更安全（外部脚本无法访问 shadow root），但调试时 Chrome DevTools 的"Elements"面板里看到的是一个空的 `<div>`，必须打开 "Show user agent shadow DOM" 才能看到内部结构。仓库作者选了前者——抢购脚本场景下"不被检测"比"便于调试"重要。

## 十一、4 层支付恢复：渐进降级的教科书

支付弹窗是整个链路最脆弱的一环。前端可能在 5 个不同的地方把弹窗拦住：

1. `payComponent.isServerBusy=true` 不发请求
2. 全局遮罩拦截点击
3. 业务弹窗错误提示覆盖支付弹窗
4. Vue 组件 `payDialogVisible=false` 永远不渲染

仓库用 4 层策略逐层击穿：

```js
async function recoverPayment() {
    // Layer 1: 暴力清弹窗 + 遮罩
    document.querySelectorAll('.error-modal, .mask, .overlay').forEach(el => el.remove());

    // Layer 2: 缓存响应 + 重点击购买按钮
    const btn = document.querySelector('.buy-btn');
    if (btn && state.cache) { btn.click(); await sleep(100); }

    // Layer 3: 直接 fetch 支付链接，跳过 UI
    if (state.bizId) {
        const payRes = await fetch(`/api/biz/pay/go?bizId=${state.bizId}`);
        const payUrl = (await safeJSON(payRes))?.data?.payUrl;
        if (payUrl) window.open(payUrl);
    }

    // Layer 4: 兜底提醒（如果以上全失败）
    if (!document.querySelector('.pay-dialog')) {
        showAlert('请手动前往支付页面，输入 bizId: ' + state.bizId);
    }
}
```

**渐进降级的核心思想**：每层成本递增——Layer 1 是 O(1) DOM 操作，Layer 2 需要缓存响应，Layer 3 是绕过 UI 的"灰色通道"（仅在确实拿到合法 bizId 时才走），Layer 4 已经放弃自动化。**前 3 层任何一层成功就退出**，避免在用户已经看到支付弹窗之后又开一个新窗口。

v4.6 专门加固了 Layer 1，新增 `forcePayDialog` 在 1.5 秒后兜底强制设置 `payDialogVisible=true`——这是因为前端的 `isServerBusy=true` 会让 `payPreviewFn` 函数整体短路，连 Layer 1 都救不回来。

## 十二、高精度定时：rAF + performance.now 的精度边界

油猴脚本里的 `setTimeout(fn, 0)` 实际精度通常是 4-10ms（浏览器最小延迟）。但抢购脚本要赶在 10:00:00.000 这个时间点起跑，10ms 误差就是 100 个请求的差距。

仓库用 `requestAnimationFrame` + `performance.now()` 自实现高精度定时器：

```js
function highResTimer(targetMs, cb) {
    const start = performance.now();
    function tick() {
        const now = performance.now();
        const elapsed = now - start;
        if (elapsed >= targetMs) { cb(); return; }
        // 还差多少 ms 就 sleep 多少 ms，但 rAF 兜底唤醒
        const remain = targetMs - elapsed;
        if (remain > 16) setTimeout(tick, remain - 16);  // 16ms 内交给 rAF
        else requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
}
```

`performance.now()` 精度在现代浏览器里是 5μs（microseconds，不是毫秒；注：受 Spectre 缓解影响实际为 100μs 量级，但仍在 sub-ms 范围），rAF 在 tab 激活时是 16ms（60Hz）一帧。组合下来：

```text
精度来源          误差              适用场景
──────────────────────────────────────────────────
setTimeout      ±10ms             普通 UI 调度
performance.now  ±5μs             计时（不调度）
rAF             ±16ms             调度
──────────────────────────────────────────────────
组合使用         ±2ms（实测）      抢购定时
```

实测 2ms 精度的代价是要让 tab 保持前台（rAF 在后台会被节流到 1Hz），所以脚本有个 `document.visibilitychange` 监听——后台时挂起，恢复时重启定时。

## 十三、持久化：localStorage + sessionStorage 分层

两个 storage 各有分工：

```js
// localStorage：跨刷新、跨会话保留
localStorage.setItem('glm_rush_cfg', JSON.stringify(save));

// sessionStorage：单次会话保留（关 tab 失效）
sessionStorage.setItem('glm_rush_captured', JSON.stringify(captured));
```

- `cfg` 放 localStorage：用户调整过并发路数 / 间隔 / 抢购时间，下次打开自动恢复
- `captured` 放 sessionStorage：用户点过一次"购买"按钮捕获的请求参数（query string + body），抢购期间反复用，关 tab 后失效（防泄露历史请求）

**为什么 captured 不能放 localStorage？** 一是历史请求参数留在 localStorage 太久会泄露用户偏好（planId、couponId）；二是 localStorage 在隐私模式下可能被禁用。sessionStorage 是"会话级"的最合适容器。

`captured` 的内容是关键——`preview` 接口的 body 必须和原请求一模一样（同样的 planId、同样的 couponId、同样的数量），否则后端直接拒。所以脚本强制要求用户**先手动点一次**真实购买按钮，捕获这次请求，之后所有并发都用这次捕获的参数。

## 十四、MutationObserver：弹窗自动恢复

`MutationObserver` 在 v4.0 加入，作用是**实时检测页面 DOM 变化，自动关闭错误弹窗并重新触发抢购**：

```js
const mo = new MutationObserver((mutations) => {
    for (const m of mutations) {
        for (const node of m.addedNodes) {
            if (!(node instanceof HTMLElement)) continue;
            // 检测错误弹窗
            if (node.matches('.error-modal, .ant-modal-confirm-error')) {
                closeAndRetry(node);
            }
        }
    }
});
mo.observe(document.body, { childList: true, subtree: true });
```

```js
function closeAndRetry(modal) {
    const closeBtn = modal.querySelector('.close, .ant-modal-close');
    if (closeBtn) closeBtn.click();
    if (state.recoveryCount++ < CFG.recoveryMax) {
        setTimeout(() => startRush(), 200);  // 200ms 后重试
    }
}
```

`recoveryMax: 3` 是上限，避免无限循环。如果 3 次都失败，说明服务端真的没货了，停下来。

## 十五、可借鉴的工程模式

虽然这是一个抢购脚本，但里面沉淀的工程模式**完全可以用到任何高并发前端场景**：

| 模式 | 来源 | 适用场景 | 代码定位 |
|------|------|----------|----------|
| 双模式并发（极速/普通） | v4.4 | 秒杀、抢票、抢额度 | `rush()` + `isTurbo()` |
| 爆发—快速—慢速三段间隔 | v4.4 | 任何带风控的轮询 | `adaptiveDelay()` |
| Promise.race 提前终止 | v4.0 | 任何多路重试 | `Promise.race(tasks)` |
| preview + check 双校验 | v3.2 | 任何带乐观锁的后端 | `doOne()` |
| JSON.parse 定向 hook | v4.1 | 任何需要改响应体的场景 | `JSON.parse = function...` |
| fetch toString Proxy 伪装 | v4.4 | 任何对抗前端风控 | `window.fetch = new Proxy(...)` |
| Shadow DOM UI 隔离 | v4.0 | 任何油猴脚本 | `host.attachShadow({mode:'closed'})` |
| 4 层支付恢复 | v4.1 | 任何"关键弹窗被拦截"场景 | `recoverPayment()` |
| rAF + performance.now 高精度定时 | v4.0 | 任何需要 sub-frame 精度的任务 | `highResTimer()` |
| localStorage + sessionStorage 分层 | v4.0 | 任何需要持久化用户偏好 + 单次会话状态 | `saveCfg()` / `captured` |
| MutationObserver 弹窗监控 | v4.0 | 任何需要响应页面动态变化的场景 | `new MutationObserver(...)` |

## 十六、不适用场景与红线

不要把这个仓库的思路照搬到任何**非抢购**场景里：

- ❌ **电商压测**：法律风险，对方有反爬系统，爬虫协议可能明文禁止
- ❌ **票务系统**：黄牛行为，违反平台规则
- ❌ **API 滥用**：智谱的服务条款里大概率禁止自动化抢购
- ✅ **学习研究**：在本地 mock 一个 `/api/biz/pay/preview` 服务，自己复现整套并发引擎
- ✅ **自用抢购**：抢自己的账号、自己的额度，前提是不影响平台公平性

代码里有个 `safeJSON` 函数，注释说"防原型链污染"——这是仓库作者**清楚知道自己在做什么、做了哪些防御**的证据。读这份源码最大的价值不是"我也能写抢购脚本了"，而是"我学到了一整套在对抗性前端环境里做高并发的工程方法"。

## 十七、自测题

1. 为什么双模式并发里"极速模式 5 秒"是合理的？再多 5 秒会怎样？再少 5 秒呢？
2. `adaptiveDelay` 里 `±30%` 的抖动如果改成 `±5%` 或 `±50%`，各自会出什么问题？
3. 为什么 `preview + check` 不能合并成一次调用？（提示：后端乐观锁语义）
4. 如果把 `JSON.parse` 的 hook 从全局定向改写改成"只在 fetch 回调里改"，会丢失哪些场景？
5. Shadow DOM `mode: 'closed'` 和 `mode: 'open'` 在反检测层面有差别吗？
6. `requestAnimationFrame` 在 tab 后台会被节流到 1Hz，抢购脚本怎么应对？
7. v4.6 的 `forcePayDialog` 1.5s 后强制设 `payDialogVisible=true`——为什么是 1.5s 而不是 0.5s 或 3s？

<details>
<summary>参考答案提示</summary>

1. 极速模式赌的是前 5s 服务端未及限流；多了服务端反应过来触发风控，少了并发优势没发挥完。
2. ±5% 易被模式识别检测；±50% 间隔方差过大反而拖慢节奏。
3. preview 给的是"未占用 bizId"，check 给的是"现在还能用"，是两次独立的乐观锁检查。
4. 框架内部的 JSON.parse 调用（比如 Vue 组件 watch）就走不到了。
5. closed 让外部 JS 拿不到 shadow root 引用，反检测层面更安全；但调试不便。
6. 监听 `visibilitychange`，后台时挂起定时器，恢复时重新对齐到目标时间。
7. 1.5s 是 Layer 1-3 平均恢复耗时，再短会有 Layer 3 还没发起就强制弹窗的竞态，再长用户体验上感觉"卡了"。

</details>

## 十八、一句话总结

`qtaxm/glm-rush` v4.6 用 2088 行油猴脚本，把"在 10:00:00.000 抢到一个智谱 GLM Coding 额度"这件事拆成了 11 个相互咬合的子系统——并发引擎、双校验、反检测、Shadow DOM 隔离、Vue 组件 hook、4 层支付恢复、高精度定时。**每一个子系统都是一个独立的工程问题，每一个解法都是一次具体的取舍**。

读这份源码不是学"怎么抢"，是学**在对抗性前端环境里做高并发时，工程上能做到什么程度**。

---

**仓库地址**：<https://github.com/qtaxm/glm-rush>
**版本**：v4.6 (2026-04-10)
**协议**：MIT
**源码规模**：2088 行（2 文件）