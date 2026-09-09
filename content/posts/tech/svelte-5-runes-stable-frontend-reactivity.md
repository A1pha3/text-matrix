---
title: "Svelte 5 Runes：稳定版两年后，前端响应式范式走到哪了"
date: "2026-06-07T12:50:00+08:00"
slug: "svelte-5-runes-stable-frontend-reactivity"
github_repo: "sveltejs/svelte"
aliases:
  - "/posts/tech/svelte-5-runes-stable-frontend-reactivity/"
description: "Svelte 5 自 2024 年发布稳定版以来已是主流选择之一。runes 让响应式从隐式魔法变为显式语言能力。本文回顾 runes 的核心机制与完整 rune 族谱、5.56 系列新增的声明标签与 TypeScript 6 支持，以及与 React/Vue/Solid 的对照。"
draft: false
categories: ["技术笔记"]
tags: ["Svelte", "JavaScript", "响应式"]
---

# Svelte 5 Runes：稳定版两年后，前端响应式范式走到哪了

> **目标读者**：在评估前端框架的工程师；对响应式编程范式感兴趣的人
> **核心问题**：Svelte 5 的 Runes 范式解决了什么？稳定两年后，它凭什么还在持续吸引新用户？
> **难度**：⭐⭐（中级）
> **来源**：GitHub [sveltejs/svelte](https://github.com/sveltejs/svelte)，88,000+ ★ / MIT / 2026-06-07

## 快速信息卡

| 指标 | 数值 |
|------|------|
| 仓库 | [sveltejs/svelte](https://github.com/sveltejs/svelte) |
| Stars | 88,000+（2026-06 约 87k，持续增长） |
| Forks | 5,200+ |
| License | MIT |
| 主要语言 | JavaScript/TypeScript |
| 当前稳定版 | Svelte 5.56.x（runes 范式） |

## 学习目标

读完本文后，你应该能够：

- 理解 Svelte 5 引入的 Runes 范式解决了什么、与 Svelte 4 的差异
- 掌握核心 rune 的用法：`$state`、`$derived`、`$effect` 及其变体
- 使用 `$props`／`$bindable` 声明组件接口，读懂 `$state.raw`／`$state.snapshot` 的边界
- 认识 5.56 系列带来的声明标签（`{const ...}`、`{let ...}`）与 TypeScript 6 支持
- 对照 Svelte Runes 与 React Hooks ／ Vue / Solid 的心智模型差异
- 判断 Svelte 5 是否适合你的项目（适用边界）

## 目录

- [快速信息卡](#快速信息卡)
- [学习目标](#学习目标)
- [一、为什么 Svelte 还在持续吸新](#一为什么-svelte-还在持续吸新)
- [二、runes 到底是什么](#二runes-到底是什么)
- [三、完整 rune 族谱：从三个到一族](#三完整-rune-族谱从三个到一族)
- [四、两个容易踩的边界](#四两个容易踩的边界)
- [五、声明标签与 TypeScript 6：5.56 在补什么](#五声明标签与-typescript-656-在补什么)
- [六、Svelte 4 → 5 迁移对照](#六svelte-4--5-迁移对照)
- [七、为什么 2026 年还有人选 Svelte](#七为什么-2026-年还有人选-svelte)
- [八、上手路径](#八上手路径)
- [FAQ](#faq)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [相关链接](#相关链接)

---

## 一、为什么 Svelte 还在持续吸新

Svelte 是 GitHub 上少有的"老牌且仍在细水长流"的项目。它没有 React 3 时代那种每隔几年"破坏性回归 + 爆点营销"的节奏，但几乎每个 minor 版本都会带来范式层面的小改动，让社区持续讨论。

2026 年 6 月初，`sveltejs/svelte` 又一次进入 GitHub Daily Top 10（当日约 87k star）。直接触发这次关注的是 **Svelte 5.56.0**（2026-05-30）：它给模板语言补上了**声明标签**（declaration tags），并让整条工具链切换到 **TypeScript 6**。随后 5.56.2（2026-06-05）等 patch 跟进，到 7 月底已经迭代到 5.56.8。

与其说是"上新"，不如说这套组合拳说明了一件事：**Svelte 5 的范式主结构已经稳定，团队在认真打磨大型代码库里的边界情况与工具链现代化。**

## 二、runes 到底是什么

Svelte 4 的响应式是"魔法"——编译器自动追踪哪些顶层 `let` 变量被模板引用，一旦赋值就触发重渲染。它简单，但代价是**隐式**：在复杂的组件里，你很难判断"这个变量改了会不会触发更新"，而且响应式只作用于组件顶层，一旦你想把逻辑抽到组件外、或放进函数/类里，就得改造心智模型（引入 store）。

Svelte 5 引入 **runes**（符文），把响应式变成显式的语言关键字。runes 是以 `$` 开头的编译器指令，不是运行时导入，也不能被别名、导入或条件调用。最基本的对照是：

```svelte
<script>
  let count = $state(0);          // Svelte 4 的 let count = 0 → 显式声明响应式
  let doubled = $derived(count * 2); // Svelte 4 的 $: doubled = count * 2

  function increment() {
    count += 1;                   // 直接改，框架会自动更新
  }
</script>

<button onclick={increment}>
  {count} → {doubled}
</button>
```

三个最核心的 rune：

- **`$state`**：声明一个响应式变量。基本类型直接读写；对象和数组会被包成深响应式代理（Proxy），增删改都能被追踪。
- **`$derived`**：声明派生值，自动追踪依赖、依赖变化时重算。它必须保持纯净——不要在派生表达式里写副作用。
- **`$effect`**：声明副作用，在依赖变化后执行，通常用来同步 DOM 之外的效果。它不需要依赖数组（这是与 `useEffect` 最大的差别），也是 `onMount`／`afterUpdate`／`beforeUpdate` 等旧生命周期钩子的统一替代。

对比 React 的 Hooks 哲学：Hooks 把组件当成"函数 + 状态机"，runes 把组件当成"模板 + 显式响应式图"。前者偏函数式，后者偏数据流。这也是 2026 年 Runes 重新被讨论的核心原因——它和 Solid 一起，把"响应式"从框架的 runtime 概念上移，变成了可复用的语言级能力。

## 三、完整 rune 族谱：从三个到一族

上面三个是入门核心，但要真正用好，还需要认识这个家族：

| Rune | 作用 | 一句话记忆 |
|------|------|-----------|
| `$state` | 声明响应式状态 | 显式 `let` |
| `$state.raw` | 浅层状态，只跟踪整体重赋值 | 大数据不改字段时用它 |
| `$state.snapshot` | 取响应式状态的普通副本 | 传外部 API 时用 |
| `$derived` | 派生值（纯计算） | 显式 `$:` |
| `$derived.by` | 传函数的派生值（多行逻辑） | 复杂派生用函数体 |
| `$effect` | 副作用，自动跟踪依赖 | 显式 `onMount`+`afterUpdate` |
| `$props` | 声明组件 props | 取代 `export let` |
| `$bindable` | 声明可双向绑定的 prop | 取代 `bind:` 到组件 |
| `$inspect` | 开发期打印响应式值 | 只在 dev 生效 |

对于入门，重点讲清楚三个最容易困惑的点：

**1. `$state.raw` 不是必须，但能规避性能黑洞。** 深响应式代理对很大、很平的 JSON 数据（比如接口返回的大对象、配置表）有逐属性的描述符开销。`$state.raw` 不建代理，只跟踪"整体重新赋值"：

```js
let payload = $state.raw(largeApiResponse);
payload.foo = 'x';            // 不会触发更新
payload = { ...payload, foo: 'x' }; // 触发更新
```

**2. `$derived.by` 处理多行逻辑。** 单行用 `$derived`，一旦派生逻辑复杂到要循环／中间变量，就交给函数体：

```js
let numbers = $state([1, 2, 3]);
let total = $derived.by(() => {
  let sum = 0;
  for (const n of numbers) sum += n;
  return sum;
});
```

**3. 用 `$props` 与 `$bindable` 声明组件接口。** 旧 Svelte 里"顶层 `export let` 就是 prop"的约定被彻底取代，且没有了 `$$restProps` 之类的怪癖：

```svelte
<script>
  // $bindable 表示这个 prop 允许父组件 bind: 回写
  let { title, count = $bindable(0) } = $props();
</script>
```

> 注意：runes 不能被解构后当普通变量传递（会切断响应式绑定）。跨函数传状态，正确姿势是传**Getter 函数**让读取实时进行，例如传 `() => count` 而不是 `count`。

## 四、两个容易踩的边界

深响应式代理不是万能的，有两个反直觉的边界：

**边界一：代理止步于 class 实例。** 普通对象和数组会被深代理；但一个 `new` 出来的 class 实例**不会**被代理。想让类字段也响应式，字段本身得用 `$state` 声明：

```js
class Todo {
  done = $state(false);   // 字段级别声明，才响应式
  text = $state('');
}
```

**边界二：端到端共享要当心 SSR 泄漏。** 在 `.svelte.ts` 模块顶层声明 `$state`，在 SvelteKit 服务端意味着"每个进程共享一份单例"，会被不同用户串数据。跨请求的状态应放在 `load` 里创建，再用 `setContext`／`getContext` 下发给组件。这也是"runes 是显式能力、不是银弹"的典型场景。

## 五、声明标签与 TypeScript 6：5.56 在补什么

**5.56.0（2026-05-30）加入声明标签（declaration tags）**。这是模板语法的一个补全：过去你想在模板里定义局部变量，只能用 `{@const ...}`，且只能写在 `{#if}`/`{#each}`/`{#snippet}` 等块的直接子节点。现在模板里可以直接用 `{const ...}` 或 `{let ...}`：

```svelte
{#each boxes as box}
  {const area = box.width * box.height}
  {const label = `${box.width} × ${box.height} = ${area}`}
  <p>{label}</p>
{/each}
```

*注意：是 `{const ...}` / `{let ...}`，不是 `{#declare ...}`（网上不少旧资料和教程把这写法记错了）。*

声明标签不只是更顺手的语法糖：
- `{@const}` 被官方标记为 **legacy**——兼容保留，但新代码推荐用声明标签。
- 标签的值还可以是响应式的，比如模板内配合 `$state`／`$derived` 写局部响应式状态。
- 它作用域清晰：同词法作用域内的兄弟节点和子节点都可见，且会自然遮蔽外层同名变量。

**5.56 系列同步推进 TypeScript 6 工具链。** `svelte-language-server@0.18.0`、`svelte2tsx@0.7.55`、`svelte-check@4.4.8`、`svelte-preprocess@6.0.4` 与 `SvelteKit@2.21.x` 一起升级。其中最重要的行为变化是 **TypeScript 从内置依赖改为 `peerDependency`**：官方 VS Code 扩展会自动装好，通常无感；但如果你在 `settings.json` 里配置了 `svelte.language-server.ls-path` 指向自定义语言服务器，升级后需要在项目里显式装一次 `typescript`。

对绝大多数用户，整个 5.56 系列就像一句话：**范式没变，边界在收紧、工具在现代化。** 这也是一个成熟框架该有的样子。

## 六、Svelte 4 → 5 迁移对照

| Svelte 4 | Svelte 5（runes） |
|----------|-------------------|
| `let count = 0` | `let count = $state(0)` |
| `$: double = count * 2` | `const double = $derived(count * 2)` |
| `$: console.log(double)` | `$effect(() => console.log(double))` |
| `export let foo = true` | `let { foo = true } = $props()` |
| `bind:` 到组件需 `export` + 子组件配合 | `$bindable()` 显式声明 |
| `<button on:click={...}>` | `<button onclick={...}>` |
| `<slot>` / `<Component let:x>` | `{#snippet}` 命名代码片段 |
| 顶层 `let` 隐式响应式 | `$state` 显式，任何位置可用 |

迁移本身是**渐进式**的：Svelte 5 同时支持新旧两种语法，可以在一个组件树里混用。官方提供 `npx sv migrate`（迁移脚本）能自动完成大部分重复改动，但事件修饰符、`$$props` 等少数项仍要手改。Svelte 团队已经明确，旧的"魔法语法"和 store 兼容终将从某个未来 major 版本移除，新代码值得直接上 runes。

## 七、为什么 2026 年还有人选 Svelte

三个分量最重的理由：

1. **编译时优化没有运行时税。** Svelte 把组件编译成由编译器编排的近似手写 DOM 更新代码，没有 virtual DOM diff，也没有一个必须打进 bundle 的大型 runtime。对中型应用，同样的代码首屏更快、bundle 更小；这也是为什么在很多前端 benchmark 里 Svelte 稳定出现在"小体积 + 高性能"一侧。代价是编译结果不如"运行时解释"那样容易做动态热替换，但这点在工程上几乎无感。

2. **响应式成为语言能力，抽得出去。** 因为 `$state`／`$derived` 不再依赖组件顶层位置，你能把它们放进普通 `.svelte.ts` 模块、函数、类字段里复用。对想剥离框架 API、专注数据流的团队，这是实打实的心智简化。

3. **走向稳定，而不是走向新 major。** Svelte 团队公开表态重点在成熟 Svelte 5，而非规划 Svelte 6。对要控制长期维护成本的公司，这比"每年一次破坏性重大升级"更友好。工具链也在向前走（Node 24、Vite 8、TypeScript 6、Cloudflare Workers 都已覆盖）。

客观的短板也要讲清楚：**生态仍比 React 小**。高质量组件库、AI/LLM 生态工具链、成熟的调试器（虽然 Svelte DevTools 进步很大）都还差一截；实验性的 **Async Svelte**（异步响应式）和 SvelteKit 的 **remote functions** 也还处于快速变化状态。如果项目重度依赖某个 React-only 库，或团队里没人熟悉 Svelte，它不一定是第一选择。

## 八、上手路径

```bash
# 5 分钟启动一个 Svelte 5 项目（官方 CLI）
npx sv create my-app
cd my-app
npm install
npm run dev
```

`sv create` 会引导你选择 SvelteKit（全栈 meta-framework）、Vite 或 demo 等模板。**SvelteKit** 是官方推荐的生产路径，默认集成 SSR、SSR streaming、路由与表单 action；如果想验证"runes 响应式"本身，装一个纯 Vite + Svelte 模板更快。

---

## FAQ

**Q1：Runes 和 React Hooks 有什么区别？**

心智模型不同。Hooks 把组件当"函数 + 状态机"，Runes 把组件当"模板 + 显式响应式图"。Runes 不需要依赖数组：`$effect` 在运行时自动收集依赖，`$derived` 自动跟踪。Runes 是语言关键字而非导入的函数，不能别名、不能条件调用。

**Q2：`$derived` 和 `$derived.by` 什么时候分开用？**

单行表达式用 `$derived`，多行／带循环或中间变量的逻辑用 `$derived.by(() => { ... })`。两者都要求纯计算，副作用请放进 `$effect`。

**Q3：5.56 系列的声明标签和 `{@const}` 是什么关系？**

`{@const}` 是旧写法，已标记为 legacy；5.56 起模板里可直接写 `{const ...}` / `{let ...}`（不是 `{#declare}` 的写法）。声明标签同词法作用域内可见，能天然遮蔽外层，也能参与 `$state`／`$derived`。旧代码不会因此坏，新代码推荐新写法。

**Q4：Svelte 5 适合生产环境吗？**

适合。稳定版自 2024 年 10 月发布已近两年，runes 范式与工具链（含 TypeScript 6）都在持续打磨，团队也没有新 major 计划。评估时真正要看的变量是**团队熟悉度与生态**：若重度依赖某个 React-only 库，它不是好选择。

**Q5：深响应式会拖慢性能吗？**

对绝大多数数据量，深度代理的开销可忽略；但对"很大、平、只整体替换"的数据（大接口响应、配置表），用 `$state.raw` 跳过代理；需要传给外部 API 时用 `$state.snapshot` 取普通副本。

**Q6：`$state` 能放进 class 吗？**

能，但注意边界：class 实例本身不会被深代理，字段需用 `$state(0)` 显式声明才算响应式。用 Getter 函数而非被解构的值跨函数传参，可保住响应式。

---

## 自测题

**问题 1**：Svelte 5 的三个核心 rune 是什么？分别有什么作用？

<details>
<summary>参考答案</summary>
`$state`：声明响应式状态；`$derived`：声明纯派生值（自动跟踪依赖）；`$effect`：声明副作用（替代 onMount/afterUpdate，无需依赖数组）。组件接口层面还有 `$props`、`$bindable`。
</details>

**问题 2**：Runes 和 React Hooks 的核心差异是什么？

<details>
<summary>参考答案</summary>
心智模型不同：Hooks 偏函数式（"函数 + 状态机"），Runes 偏数据流（"模板 + 显式响应式图"）。`$effect`／`$derived` 不需要依赖数组；Runes 是编译器识别、以 `$` 开头的语言关键字，不能别名或条件调用。
</details>

**问题 3**：5.56 系列的主要改动是什么？

<details>
<summary>参考答案</summary>
5.56.0（2026-05-30）加入声明标签 `{const ...}`／`{let ...}`（`{@const}` 转 legacy），并让工具链支持 TypeScript 6；TypeScript 从内置依赖改为 peerDependency。整个 5.56 系列在补模板边界并推进工具链现代化，而非改动范式本身。
</details>

**问题 4**：为什么 2026 年还有人选择 Svelte？

<details>
<summary>参考答案</summary>
三个理由：编译时优化没有运行时税（无 virtual DOM、bundle 更小）；runes 让响应式成为可抽出到模块/函数/类字段的语言能力；团队专注于成熟 Svelte 5 而非规划新 major，长期维护成本可控。代价是生态比 React 小。
</details>

**问题 5**：SvelteKit 是什么？它提供了哪些功能？

<details>
<summary>参考答案</summary>
SvelteKit 是 Svelte 5 的官方 meta-framework，默认集成 SSR、SSR streaming、路由、表单 action 与（较新的）服务端函数。跨请求状态用 `load` 创建 + `setContext`/`getContext` 下放，避免顶层 `.svelte.ts` 的 `$state` 造成 SSR 状态串扰。
</details>

---

## 进阶路径

### 阶段 1：基础使用（1-2 周）

- [ ] 运行 `npx sv create my-app` 创建第一个 Svelte 5 项目
- [ ] 掌握三个核心 rune：`$state`、`$derived`、`$effect`
- [ ] 用 `$props`／`$bindable` 重写一个旧组件，感受接口显式化
- [ ] 阅读官方文档：https://svelte.dev/docs

### 阶段 2：生产应用（2-4 周）

- [ ] 用 SvelteKit 构建全栈应用（SSR、路由、表单 action）
- [ ] 把共享状态抽到 `.svelte.ts` 模块，验证深响应与 SSR 边界
- [ ] 针对大 JSON 用 `$state.raw`，传外部 API 用 `$state.snapshot`
- [ ] 用 `$derived.by(() => { ... })` 重构复杂派生逻辑
- [ ] 集成 UI 组件库并做一次 bundle 分析（编译时路线的体积优势）

### 阶段 3：高级功能（1-2 个月）

- [ ] 深入编译器的响应式图实现：runes 如何编译成高效 DOM 更新
- [ ] 用声明标签 `{const ...}` 整理复杂模板，减少 `{#each}` 内的重复计算
- [ ] 评估 Async Svelte 与 remote functions 的实验能力是否适合你的场景
- [ ] 研究 `$effect` 的依赖收集与 `$inspect` 在开发调试里的实际用法

### 阶段 4：生态贡献（持续优化）

- [ ] 为 `sveltejs/svelte` 提交 issue 或 PR（边界 Bug、文档）
- [ ] 参与社区讨论（Discord、GitHub Discussions）
- [ ] 帮助新用户解答 runes 迁移与边界问题
- [ ] 维护或创建一个示例项目验证最佳实践

**进阶资源**：

- runes 官方文档：https://svelte.dev/docs/svelte/what-are-runes
- 5.56 changelog：https://github.com/sveltejs/svelte/blob/main/packages/svelte/CHANGELOG.md
- SvelteKit 文档：https://svelte.dev/docs/kit
- demo / REPL：https://svelte.dev/playground
- 仓库：https://github.com/sveltejs/svelte
- Discord 社区：https://discord.gg/svelte

---

## 相关链接

- runes 官方文档：https://svelte.dev/docs/svelte/what-are-runes
- SvelteKit：https://svelte.dev/docs/kit
- 5.56 changelog：https://github.com/sveltejs/svelte/blob/main/packages/svelte/CHANGELOG.md
- 仓库：https://github.com/sveltejs/svelte