---
title: Dioxus 拆解：Rust 全栈框架的架构、性能与采用决策
date: 2026-07-22 03:00:00
category: tech
repo: DioxusLabs/dioxus
stars: 39062
slug: dioxuslabs-dioxus-rust-fullstack-framework-guide
github_repo: "DioxusLabs/dioxus"
source_key: "gh:DioxusLabs/dioxus"
categories: [技术笔记]
description: "Dioxus 是 Rust 生态的全栈 UI 框架：React 式声明、Copy 的信号状态、一套组件覆盖 Web、桌面、移动与 SSR。本文基于 0.7 稳定版拆解其架构、性能来源与采用取舍。"
tags: ["Rust", "全栈框架", "UI", "SSR"]

---

# Dioxus 拆解：Rust 全栈框架的架构、性能与采用决策

Dioxus 用一个代码库同时覆盖 Web、桌面、移动端和服务端渲染。这个目标本身并不新鲜——Flutter、React Native 都在做。真正让它区别于其他 Rust UI 框架的，是它在 0.5 之后砍掉了一条根深蒂固的旧设计：组件作用域（Scope）和生命周期参数。移除它们之后，Signals 接管状态，组件签名变得和普通函数一样简洁，异步和跨线程共享状态不再需要到处 clone。这篇文章基于 Dioxus 0.7 稳定版（0.8 已进入 alpha）拆解这套设计。

读完你会带走四样东西：说清 Dioxus 与 React / Yew 在状态模型上的取舍，而不是复述功能列表；能解释 0.5 移除 Scope 解决的到底是哪一类异步与跨线程问题；知道 `rsx!` 的编译期检查边界；以及一套虚拟 DOM 如何在 Web、桌面、Native、SSR 四种渲染器上落地，选型时该盯住哪个约束。

## 全景：Dioxus 到底由哪几层组成

在进入细节前，先给一张分层地图，后面所有机制都落在这些层里。

| 层级 | 职责 | 代表实现 |
|------|------|----------|
| 声明层 | 用类 HTML 语法描述界面 | `rsx!` 宏 |
| 状态层 | 响应式状态与派生计算 | Signals（`use_signal`、`use_memo`） |
| 核心层 | 虚拟 DOM、调度、组件树 | `dioxus-core` |
| 渲染层 | 把虚拟 DOM 落到具体平台 | Web (WASM)、Desktop (Wry)、Native (Blitz)、SSR |

一次界面更新的数据流，横穿这四层，只有一行：

```text
状态写入 (Signal.set) → 调度器收集变更 → diff 虚拟 DOM → 渲染器落真控件 → 下次读取重新订阅
```

记住这条线，后面讲调用顺序时不会再乱：状态层负责"值变了"，核心层负责"算最小的差"，渲染层负责"把它画出来"。

## 一、Dioxus 要解决的问题

Rust 社区写 UI，长期面临一个选择：要么用 Yew 这类框架但受限于作用域和生命周期带来的样板代码，要么自己拼接渲染、状态和路由。Dioxus 的定位是"类 React 的声明式 API + Rust 的类型安全"，并承诺一次编写、多端运行。

它解决的是三类具体问题：

- **跨平台一致**：Web、桌面、移动端共用一套组件和状态模型，不用各自维护一套。
- **状态管理简化**：0.5 起用 Signals 替代旧 hook，`use_state` 依赖作用域的历史问题消失，状态可以在异步闭包里自由使用。
- **全栈打通**：Server Functions 把服务端接口包装成普通函数调用，前后端共享同一份 Rust 类型。

状态模型上和近邻的对照，是理解 Dioxus 的钥匙，后面章节会反复用到：

| 框架 | 状态载体 | 异步代码体验 | 跨组件共享 |
|------|----------|--------------|-----------|
| React | hooks（闭包捕获 + 依赖数组） | 依赖数组漏了会出 stale 闭包 | context / 外部状态库 |
| Yew | 类似早期 React 的 Scope + 生命周期参数 | `'static` 下要 clone | context |
| Dioxus | `Copy` 的 `Signal<T>` | 免 clone 进 `async move` | 上下文 或全局 `GlobalSignal` |

这张表只想说明一点：Dioxus 值钱的不是多了一个状态库，而是把状态做成了 `Copy` 值，顺手消掉了异步和跨组件共享这两处最常见的样板。

## 二、Signals：状态层如何工作

### 从 Scope 到 Signals

Dioxus 0.4 及之前的组件签名长这样：

```rust
fn OldComponent(cx: Scope) -> Element {
    let mut state = use_state(cx, || 0);
    cx.render(rsx! {
        button { onclick: move |_| *state += 1, "Increment" }
    })
}
```

问题在于 `Scope` 携带 `'bump` 生命周期：状态在事件闭包里免 clone，但一进异步（future 必须 `'static`）就要手动 clone，心智负担集中在这里。

0.5 彻底移除 Scope 和生命周期参数，组件签名不再携带 `cx`，写起来跟普通函数一致：

```rust
fn App() -> Element {
    let mut count = use_signal(|| 0);
    rsx! {
        button { onclick: move |_| count += 1, "Count: {count}" }
    }
}
```

为什么换成 Signals 而不是继续缝补 hooks？hooks 的问题在根源：它们需要 `cx` 来定位组件和绑定生命周期，这个参数被一路传递，一进异步就成了 `'static` 的拦路虎。`Signal<T>` 是 `Copy` 类型，本质是"为 UI 设计的 `Rc<RefCell<T>>` 的 Copy 版"。它自带读写守卫和借用检查，读取时自动记录依赖、写入时通知订阅者重渲染。因为自身是 `Copy`，它可以被直接送进 `async move` 闭包，不再需要手动 clone 或标注生命周期——这正是 0.5 改动的落点。

### 常用 API

```rust
// 局部状态
let mut count = use_signal(|| 0);

// 读取值（像函数一样调用会 clone 内部值）
let current: i32 = count();

// 派生计算（依赖变化时自动重算）
let doubled = use_memo(move || count() * 2);

// 副作用
use_effect(move || println!("count changed: {}", count()));

// 全局状态（任意组件可用）
static THEME: GlobalSignal<String> = Signal::global(|| "light".to_string());
```

`GlobalSignal` 通过 `static` 声明，首次使用自动初始化，不需要显式提供上下文。它和"上下文注入"的区别在于：上下文是每个组件都能读自己那棵子树注入的值，`GlobalSignal` 则是全局一份，读哪个组件都拿到同一个值。

Signals 之外，0.7 还补了一个新原语 Stores，面向嵌套响应式状态——深层结构里的字段更新可以做到细粒度订阅，不必为整棵数据结构重渲染。深层数据多的应用值得单独研究一下它。

### 读写规则

Signals 在运行时检查借用：读和写不能重叠。异步代码里尤其要小心——不要在 `await` 期间持有读或写守卫：

```rust
use_future(move || async move {
    // 错误：await 期间 write 仍被持有
    // let mut w = signal.write();
    // do_something(&mut w).await;

    // 正确：先克隆值，await 后再写回
    let current = signal();
    let new_val = do_something(current).await;
    signal.set(new_val);
});
```

这里有一条直观的边界：`Signal` 的 `Copy` 只解决"值怎么在闭包和环境之间流动"，不解决"守卫在 await 期间不能被占着不放"这个问题。前者靠类型，后者靠运行时借用检查，两者是两回事，别混淆。

## 三、rsx!：声明层如何把 HTML 语法编译成 Rust

`rsx!` 是 Dioxus 的模板宏，语法接近 JSX，但类型检查发生在编译期：

```rust
fn UserProfile() -> Element {
    let user = use_signal(User::default);
    rsx! {
        div { class: "profile-card",
            img { src: "{user().avatar}", alt: "Avatar" }
            h2 { "{user().name}" }
            p { "{user().bio}" }
            button {
                onclick: move |_| follow(user()),
                "Follow"
            }
        }
    }
}
```

宏在编译期做几件事：把类 HTML 语法解析成 Rust AST，检查 props 类型和事件处理器签名，然后生成虚拟 DOM 节点构建代码。属性名、事件名拼错会在编译时报错，而不是运行时报 undefined。

生成物有一个对性能影响很大的特性：模板机制。静态不变的子树只在首次构建一次，之后每次 diff 都整段跳过，只有动态部分（插值文本、绑定的属性）参与比较。这意味着 `rsx!` 写出来的界面，diff 成本主要跟动态内容的多少挂钩，而不是整个界面树的大小。

要分清 `rsx!` 能检查什么、不能检查什么。它检查的是**结构**：标签名、属性名、事件回调签名、props 类型，都在编译期被 Rust 编译器盯住，拼错一个事件名字立刻报错。它**不**检查的是**内容**：`"{user().name}"` 取到的字段是否真的存在、事件回调里写的业务逻辑对不对，仍是运行时的事。把这两层边界记住，"宏很神奇"就不会被夸大成"宏替我写好了逻辑"。

## 四、渲染层：同一棵树，不同的落地方式

虚拟 DOM 是跨平台的桥。渲染层把它翻译成各平台的真实控件：

| 渲染器 | 目标 | 底层 |
|--------|------|------|
| `dioxus-web` | 浏览器 | WASM + web-sys |
| `dioxus-desktop` | 桌面 | Wry（tao 窗口 + 系统 WebView） |
| `dioxus-mobile` | Android/iOS | Wry（系统 WebView） |
| `dioxus-ssr` | 服务端 | 输出 HTML 字符串 |
| `dioxus-native` | 桌面（0.7 新增） | Blitz（WGPU 渲染 + stylo，Firefox 同源的 CSS 引擎） |

选择渲染器不是改业务代码，而是换一个后端 crate。业务组件、Signals、`rsx!` 全部复用，只有 `main` 里的启动入口和一个 feature 标志不同——0.5 起连启动函数也统一了，一个 `launch` 可以跑任何平台。

### 更新流程

渲染器收到虚拟 DOM 的变更后，通过 diff 找出最小变化集，再应用到真实平台。Web 端是操作 DOM 节点，桌面端是传给 WebView，Native 端是驱动 WGPU 绘制。这里的 diff 是核心层的职责，各渲染器只负责"把 diff 描述的最小操作落到自己的控件"——这解释了为什么日志里桌面端能复用一个 Web 端的调试思路，机制上是同一套虚树。

## 五、全栈：Server Functions

全栈场景下，Dioxus 把服务端逻辑包装成普通异步函数。客户端调用它就像调用本地函数，实际是一个 HTTP 请求。0.7 重构了这套机制，与 Axum 深度集成（0.7 基于 Axum 0.8），服务端就是一个标准的 Axum 应用：

```rust
// 客户端调用
fn fetch_data() -> Element {
    let data = use_resource(|| async move {
        get_data().await
    });
    rsx! { div { "Data: {data:?}" } }
}

// 服务端实现：默认只在 server feature 下编译
#[server]
async fn get_data() -> Result<Vec<Data>, ServerFnError> {
    // 这里可以使用 sqlx、tokio::fs 等服务端依赖
    let pool = get_db_pool().await;
    Ok(query_all(&pool).await?)
}
```

一个 fullstack Dioxus 应用由两个构建目标组成：客户端 binary（跑 Web/桌面/移动）和服务端 binary（负责 SSR 与执行 Server Functions）。依赖划分是关键——`tokio`、`sqlx` 这类库通常只挂在 `server` feature 下，否则 WASM 构建会被拖垮：

```toml
[features]
web = ["dioxus/web"]
desktop = ["dioxus/desktop"]
server = ["dioxus/server", "dep:tokio", "dep:sqlx"]
```

注意 `#[server]` 函数是编译期"摊开成两半"的：在服务端目标里它是真正的函数体，在客户端目标里它被转成一段负责序列化请求参数、发出 HTTP 请求并反序列化结果的调用壳。所以服务端依赖只要没挂到 `server` feature 下，客户端目标照样能编译——这既是优点（前后端类型对齐），也是坑点（忘了 feature 分区，WASM 包直接被不需要的依赖撑大）。

## 六、任务流案例：一次登录请求如何穿过系统

把上面的机制串起来看一个具体场景：用户点击"登录"按钮。

1. 客户端组件里 `use_signal` 持有表单状态，`rsx!` 把输入框绑定到信号。
2. 用户点按钮，事件处理器调用 `login(user, pass)`——这是一个 `#[server]` 函数。
3. 客户端把它序列化成 POST 请求，发到服务端 binary。
4. 服务端执行函数体（校验、查库、发 token），把结果序列化回传。
5. 客户端 `use_resource` 拿到结果，写入信号，组件重渲染，界面切换到登录态。

整个链路前后端共享同一套 Rust 结构体定义，类型在编译期对齐。但第 3 到第 4 步是真实的网络往返，失败路径和你手写 REST 时一样存在：服务端 500、超时、token 无效。0.7 的 `use_resource` 读取时拿到的是一个 `Option`：`None` 表示请求还在路上，`Some(Ok(...))` 是成功，`Some(Err(...))` 是失败。把这三个状态都映射到界面，是这个流程里最容易漏掉的环节：

```rust
let data = use_resource(|| async move { get_data().await });

match &*data.read() {
    Some(Ok(rows)) => rsx! { div { "Data: {rows:?}" } },
    Some(Err(err)) => rsx! { p { "请求失败：{err}" } },
    None => rsx! { p { "加载中……" } },
}
```

请求返回 `Result` 且需要跟 Suspense、Error Boundary 联动时，0.7 还提供了专门的 `use_loader`，可以直接接入 SSR 渲染流程，比手工处理 Resource 状态省事。

## 七、性能：0.5 与 0.7 各自改了什么

Dioxus 的性能提升分两段，每段解决的问题不同，不宜笼统比较。

**0.5 的桌面端优化**：官方发布说明给出"桌面端 reconciliation 快约 5 倍"的数字，来源很具体——核心层与桌面渲染器之间传输变更的协议从 JSON 换成了 sledgehammer 二进制协议，变更应用时间降到原来的约五分之一、延迟减半；再叠加 rsx! 的模板机制，静态子树在 diff 时整段跳过。这是"实现层变快"，不是"跑得比 React 快"的说法。

**0.7 的开发体验**：Subsecond 实现 Rust 代码热补丁，改代码不丢运行状态；WASM-Split 做 WebAssembly 的代码分割与按需加载，压低首包体积。这两项改善的是迭代速度和加载体验，不是渲染吞吐。

服务端性能有一个可核查的外部基准：Rullst Benchmarks 2026（2026 年 6 月更新）。这套测试用 Docker 在一台 Ryzen 7 5700U、8GB 内存的机器上对 23 个 Web 框架跑了四层压测，官方排名按效率分（JSON RPS ÷ 峰值内存）排序。Dioxus 0.7.x 通过全部压测，排第 7：JSON 接口约 8.8 万 RPS，平均延迟 2.79 ms，峰值内存 25.42 MiB。排在它前面的清一色是纯 Rust 服务框架（Actix-Web、Axum、Poem、Rullst、Salvo）和 Go-Fiber——对一个自带虚拟 DOM 与响应式层的全栈框架来说，这个位置说明服务端开销没有拖后腿。

理解这组数字要盯两件事。其一，它测的是给定 JSON 接口的并发吞吐；0.7 的 fullstack 服务端跑在 Axum 上，数字更可能反映路由与序列化这条链路的开销，而不是 `dioxus-ssr` 渲染 HTML 字符串的成本。其二，从这组数字推不出客户端交互帧率、WASM 首包体积或桌面端手感——项目真正在意的是桌面端手感的话，这个基准帮不上忙，得自行跑交互基准。

## 八、真实用户与生态

能确认的 Dioxus 桌面端真实项目：

- **Ebou**：跨平台 Mastodon 客户端（macOS 稳定、Windows beta），作者 terhechte 用 Dioxus 写的；支撑它的 Navicula 是一套 TCA（Elm 架构）风格的状态管理库，reducers、actions、子 reducer 嵌套都在，也算 Dioxus 上做复杂状态的一种参考实现。

生态系统里还有一批社区项目：`freya`（基于 Dioxus 的 Skia 原生渲染 GUI 库，官方清单归类为独立渲染器）、`kopuz`（Dioxus 构建的音乐播放器）、`Floneum`（本地 AI 工作流的图形编辑器）。它们选了不同的渲染后端，说明渲染层抽象确实让"换后端不换业务代码"成立。

选型时这张图的用处在于：生态里每个项目的成熟度和关注点都挂在**渲染后端**上，而不是挂在 Dioxus 本身。想判断某个能力靠不靠谱，先看它用的后端是哪条线。

## 九、采用建议：谁该用，谁该等

**先看你的约束，再看 Dioxus 是否匹配。**

适合采用：

- 团队已熟悉 Rust，且目标平台不止一个（Web + 桌面，或 Web + 移动）。
- 对包体积和启动性能有硬要求，愿意接受 WASM 构建。
- 想统一前后端语言，减少 API 契约的双份维护。

暂时不急着用：

- 纯 Web 快速原型——React/Vue 生态更成熟，调试工具更完善。
- 团队没有 Rust 经验——学习曲线的起点在 Rust 本身，不在 Dioxus。
- 需要深度依赖某个 Web 生态——Dioxus 没有 npm 生态那样庞大的组件库。

**从哪开始**：

1. 安装 CLI（一行命令 `curl https://dioxus.dev/install.sh | sh`，之后可用 `dx self-update` 升级），用 `dx new` 生成项目模板。
2. 跑通官方 quickstart，`dx serve` 启动开发服务，感受 `rsx!` + Signals 的写法——验收标准很直接：改一行代码，浏览器里的界面自动更新。
3. 做一个小桌面应用（Dioxus 桌面端最成熟），验证跨平台是否如宣传一致。
4. 需要前后端时再引入 Server Functions，先保持单端，降低一次引入的复杂度。

## 十、常见坑位与排查

这一节是实际操作里最容易卡住的地方，按出现频率排。

- **运行时借用 panic**：读取和写入重叠会触发 `Signal` 的借用检查，报错形如 `already borrowed`。最常发生在 `await` 前后。对策是异步里先 `let current = signal()` 取当前值，等待完成后用 `signal.set(...)` 写回，别在 `await` 期间持有 `write()` 守卫。
- **编译越来越慢**：`rsx!` 宏加泛型会显著拉长编译时间。大项目先上 `sccache` 或开启增量编译；多平台 try-build 时，几个 target 分开增量做，别一次编译所有 feature。
- **WASM 构建失败或包体暴涨**：几乎都是 server-only 依赖没隔离开。检查 `Cargo.toml` 里 `tokio`、`sqlx` 之类是不是只挂在 `server` feature 下，客户端目标别 pull 进来。
- **热补丁（Subsecond）没生效**：Subsecond 由 `dx serve` 驱动，CLI 把补丁打进运行中的进程；直接 `cargo run` 不会有热补丁。改的是 `Cargo.toml`、配置或静态资源时，仍会走完整重建或整页刷新。
- **Native 渲染器表现不稳**：Blitz 官方定位是 beta——能渲染不少无 JS 的真实网站，适合愿意待在前沿的早期采用者，但 bug 和缺失特性都还在。要原生渲染，先对照 Blitz 的 status 页确认目标能力覆盖，否则用 Wry/WebView 后端更稳。

## 十一、当前状态与风险

截至 2026 年 9 月，Dioxus 稳定版是 0.7.x（最新 0.7.10，2026 年 7 月底发布），0.8 已放出两个 alpha。几个需要留意的点：

- **版本节奏**：0.5（2024 年 3 月）到 0.7（2025 年 10 月）约 19 个月里跨了两个大版本，期间 API 多次伤筋动骨——Scope 移除、signals 重写、`use_resource` 语义调整。0.7 已趋稳，但 0.8 仍在 alpha、未承诺 API 冻结，生产项目要锁版本。
- **渲染器成熟度**：Blitz/Native 在 0.7 随版本发布，但整体仍是 beta（见第十节的排查建议），生产路径先走 Wry/WebView。
- **调试工具**：0.7 内置了 CodeLLDB 一键调试，但整体 DevTools 生态仍不如前端社区成熟。
- **编译时间**：复杂 `rsx!` 加泛型的项目编译偏慢，对策见第十节。

## 十二、读后自测

能独立回答下面几个问题，说明这篇拆解你已经吸收，而不只是看过：

1. 0.5 移除 Scope 为什么能让状态免 clone 地进入 `async move` 闭包？`Copy` 和 `'static` 在这里各解决了什么？
2. `rsx!` 在编译期保证的是哪些检查？哪些是它管不到的？
3. 一条状态更新如何穿过状态层、核心层、渲染层？diff 属于哪一层的职责？
4. 0.7 的 `use_resource` 读到 `None`、`Some(Err)` 时各该渲染什么？为什么这三个状态都要照顾到？
5. 桌面端想用原生渲染时，为什么社区建议先确认 Blitz 的覆盖情况，而不是直接切后端？

## 十三、参考资源

- 仓库：<https://github.com/DioxusLabs/dioxus>
- 官方文档：<https://dioxuslabs.com/learn/>
- 0.5 发布说明（Scope 移除、Signals、桌面端二进制协议）：<https://dioxuslabs.com/blog/release-050>
- 0.7 发布说明（Subsecond、Native、Axum 集成、WASM-Split）：<https://github.com/DioxusLabs/dioxus/releases/tag/v0.7.0>
- Blitz 渲染引擎与状态页：<https://github.com/DioxusLabs/blitz>
- Rullst 服务端基准：<https://github.com/Rullst/Benchmarks>
- Ebou（Mastodon 客户端示例）：<https://github.com/terhechte/Ebou>
