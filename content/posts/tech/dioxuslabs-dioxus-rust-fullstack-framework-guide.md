---
title: Dioxus - Rust 全栈框架深度技术拆解与实战指南
date: 2026-07-22 03:00:00
category: tech
repo: DioxusLabs/dioxus
stars: 37575
slug: dioxuslabs-dioxus-rust-fullstack-framework-guide
github_repo: "DioxusLabs/dioxus"
categories: [技术笔记]
description: "Dioxus 是 Rust 生态的全栈 UI 框架，采用 React 式声明编程、类型安全组件与跨平台一致性。本文拆解其架构设计、响应式模型与性能优化路径。"
tags: ["Rust", "全栈框架", "UI", "SSR"]

---

# Dioxus - Rust 全栈框架深度技术拆解与实战指南

Dioxus 用一个代码库同时覆盖 Web、桌面、移动端和服务端渲染，这个目标本身并不新鲜——Flutter、React Native 都在做。真正让它区别于其他 Rust UI 框架的，是它在 0.5 之后砍掉了一条根深蒂固的旧设计：组件作用域（Scope）和生命周期参数。移除它们之后，Signals 接管状态，组件签名变得和普通函数一样简洁，异步和跨线程共享状态不再需要到处 clone。这篇文章基于 Dioxus 0.7 稳定版（0.8 已进入 alpha）拆解这套设计。

## 全景：Dioxus 到底由哪几层组成

在进入细节前，先给一张分层地图，后面所有机制都落在这些层里。

| 层级 | 职责 | 代表实现 |
|------|------|----------|
| 声明层 | 用类 HTML 语法描述界面 | `rsx!` 宏 |
| 状态层 | 响应式状态与派生计算 | Signals（`use_signal`、`use_memo`） |
| 核心层 | 虚拟 DOM、调度、组件树 | `dioxus-core` |
| 渲染层 | 把虚拟 DOM 落到具体平台 | Web (WASM)、Desktop (Wry)、Native (Blitz)、SSR |

## 一、Dioxus 要解决的问题

Rust 社区写 UI，长期面临一个选择：要么用 Yew 这类框架但受限于作用域和生命周期带来的样板代码，要么自己拼接渲染、状态和路由。Dioxus 的定位是"类 React 的声明式 API + Rust 的类型安全"，并承诺一次编写、多端运行。

它解决的是三类具体问题：

- **跨平台一致**：Web、桌面、移动端共用一套组件和状态模型，不是各自维护一套。
- **状态管理简化**：0.5 起用 Signals 替代旧 hook，`use_state` 依赖作用域的历史问题消失，状态可以在异步闭包里自由使用。
- **全栈打通**：Server Functions 把服务端接口包装成普通函数调用，前后端共享同一份 Rust 类型。

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

0.5 彻底移除 Scope 和生命周期参数，组件变成无参数函数：

```rust
fn App() -> Element {
    let mut count = use_signal(|| 0);
    rsx! {
        button { onclick: move |_| count += 1, "Count: {count}" }
    }
}
```

`Signal<T>` 是 `Copy` 类型，本质是"为 UI 设计的 `Rc<RefCell<T>>` 的 Copy 版"。它自带读写守卫和借用检查，读取时自动记录依赖、写入时通知订阅者重渲染。

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

注意 `GlobalSignal` 通过 `static` 声明，首次使用自动初始化，不需要显式提供上下文。

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

编译产出的是一棵虚拟节点树，类似：

```rust
// 简化示意：rsx! 展开后的结构
VNode::new([
    VElement::new(
        "div",
        [Attribute::new("class", "profile-card")],
        [VElement::new("img", [Attribute::new("src", avatar)], [])]
    )
])
```

## 四、渲染层：同一棵树，不同的落地方式

虚拟 DOM 是跨平台的桥。渲染层把它翻译成各平台的真实控件：

| 渲染器 | 目标 | 底层 |
|--------|------|------|
| `dioxus-web` | 浏览器 | WASM + web-sys |
| `dioxus-desktop` | 桌面 | Wry（基于 tao + webview） |
| `dioxus-mobile` | Android/iOS | Wry + NDK/UIKit |
| `dioxus-ssr` | 服务端 | 输出 HTML 字符串 |
| `dioxus-native` | 桌面（0.7 新增） | Blitz（WGPU + Gecko 引擎） |

### 更新流程

渲染器收到虚拟 DOM 的变更后，通过 diff 找出最小变化集，再应用到真实平台。Web 端是操作 DOM 节点，桌面端是传给 WebView，Native 端是驱动 WGPU 绘制。

## 五、全栈：Server Functions

全栈场景下，Dioxus 把服务端逻辑包装成普通异步函数。客户端调用它就像调用本地函数，实际是一个 HTTP 请求：

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

## 六、任务流案例：一次登录请求如何穿过系统

把上面的机制串起来看一个具体场景：用户点击"登录"按钮。

1. 客户端组件里 `use_signal` 持有表单状态，`rsx!` 把输入框绑定到信号。
2. 用户点按钮，事件处理器调用 `login(user, pass)`——这是一个 `#[server]` 函数。
3. 客户端把它序列化成 POST 请求，发到服务端 binary。
4. 服务端执行函数体（校验、查库、发 token），把结果序列化回传。
5. 客户端 `use_resource` 拿到结果，写入信号，组件重渲染，界面切换到登录态。

整个链路前后端共享同一套 Rust 结构体定义，类型在编译期对齐。

## 七、性能：0.5 与 0.7 各自改了什么

Dioxus 的性能提升分两段，每段解决的问题不同，不宜笼统比较。

**0.5 的桌面端优化**：官方 release note 声称桌面端 reconciliation 快约 5 倍，来自移除 Scope 后核心层简化、以及新的调度。这部分是"实现层变快"，不是"跑得比 React 快"的说法。

**0.7 的开发体验**：引入 Rust 代码热补丁（Subsecond），改 Rust 代码无需整页刷新；WASM-Split 做代码分割与 tree shaking，降低首包体积。

服务端性能有一个外部基准可以参考：Rullst Benchmarks 2026 中，Dioxus（服务端渲染）JSON RPS 约 8.7 万、峰值内存约 25 MiB、平均延迟约 2.8 ms，排在 Rust 服务端框架的中间梯队（排名第 7）。注意这个基准测的是服务端吞吐，**不能**推出客户端渲染性能结论——那是另一套衡量体系。

## 八、真实用户与生态

能确认的 Dioxus 桌面端真实项目：

- **Ebou**：跨平台 Mastodon 客户端（macOS 稳定、Windows beta），作者 terhechte 用 Dioxus 写的，还为此设计了 reducer 架构层 Navicula。

生态系统里还有一批社区 crate：`freya`（Skia 渲染的非 Web GUI）、`kalosm`（本地 AI 模型）、`kopuz`（音乐播放器）等，它们用 Dioxus 但各自选了不同的渲染后端，说明渲染层抽象确实让"换后端不换业务代码"成立。

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

1. 先跑通官方 quickstart，感受 `rsx!` + Signals 的写法。
2. 做一个小桌面应用（Dioxus 桌面端最成熟），验证跨平台是否如宣传一致。
3. 需要前后端时再引入 Server Functions，先保持单端，降低一次引入的复杂度。

## 十、当前状态与风险

截至 2026 年 8 月，Dioxus 稳定版是 0.7.x（0.7.10），0.8 进入 alpha 阶段。几个需要留意的点：

- **版本节奏**：0.5 到 0.7 两年间 API 变动较大（Scope 移除、signals 迁移）。0.7 已相对稳定，但 0.8 仍未承诺 API 冻结，生产项目要锁版本。
- **渲染器成熟度**：Blitz/Native 渲染器在 0.7 发布，但滚动等交互仍在补全（社区报告过 scrolling 和部分平台空白窗口问题），需要原生渲染建议先用 Wry/WebView 后端。
- **调试工具**：DevTools 生态仍在完善，不如前端社区成熟。
- **编译时间**：`rsx!` 宏加泛型会让编译变慢，大项目建议用 `sccache` 或增量编译。

## 十一、参考资源

- 仓库：<https://github.com/DioxusLabs/dioxus>
- 官方文档：<https://dioxuslabs.com/learn/>
- 0.5 发布说明（Scope 移除、Signals）：<https://dioxuslabs.com/blog/release-050>
- 0.7 发布说明（Native、Blitz、热补丁）：<https://github.com/DioxusLabs/dioxus/releases>
- Rullst 服务端基准：<https://github.com/Rullst/Benchmarks>
- Ebou（Mastodon 客户端示例）：<https://github.com/terhechte/Ebou>
