---
title: "ryanmcdermott/clean-code-javascript 精读：把 Clean Code 原则落到 JavaScript 工程实践"
date: "2026-07-02T21:02:26+08:00"
lastmod: "2026-07-02T21:02:26+08:00"
draft: false
categories: ["技术笔记"]
tags: ["JavaScript", "Clean Code", "代码风格", "工程实践", "SOLID"]
description: "Ryan McDermott 把《Clean Code》原则落到 JavaScript 的开源笔记，94k Star，12 章节覆盖命名、函数、对象、类、SOLID 与错误处理。"
weight: 1
author: text-matrix
---

# ryanmcdermott/clean-code-javascript 精读：把 Clean Code 原则落到 JavaScript 工程实践

> 一句话定位：把 Robert C. Martin 的《Clean Code》核心原则按 JavaScript 工程语境重写的开源手册，仓库 12 个章节、几十条反例/正例对比，已经被翻译成 19 种语言。

## 项目是什么

`ryanmcdermott/clean-code-javascript`（仓库地址：<https://github.com/ryanmcdermott/clean-code-javascript>）当前 ★94,480（+11 today），License MIT，主分支只有一份 `README.md`——这是一份被社区当成"参考书"反复引用的工程笔记。它的副标题说得很克制：

> Software engineering principles, from Robert C. Martin's book *Clean Code*, adapted for JavaScript. This is not a style guide. It's a guide to producing readable, reusable, and refactorable software in JavaScript.

作者明确了两点：这不是 lint 规则集，不会在 CI 里和你的代码吵架；它关心的是代码能不能被下一个读它的人（含三个月后的你自己）读懂、重用、修改。

## 目录结构：12 章

整本手册按下面 12 个主题组织，从局部命名一路写到系统层面的错误处理和并发：

1. **Introduction** — 总论，软件工程作为手艺的边界。
2. **Variables** — 命名、可搜索性、解释性变量、心算映射、默认参数。
3. **Functions** — 参数上限、单一职责、短小紧凑、对象传参、避免副作用。
4. **Objects and Data Structures** — getter/setter、私有成员、不可变优先。
5. **Classes** — ES2015/ES6 优于 ES5、method chaining、组合优先于继承。
6. **SOLID** — SRP / OCP / LSP / ISP / DIP 五条原则的 JS 表达。
7. **Testing** — 测试的单一原则、TDD 节奏、整洁测试的几个反模式。
8. **Concurrency** — 回调 vs Promise / `async-await`、命名约定、避免 `await` 串行化。
9. **Error Handling** — 抛错优于返回错误码、不要忽略 catch。
10. **Formatting** — 垂直/水平格式化、团队一致性优于个人偏好。
11. **Comments** — 注释只解释"为什么"、不写 journal comments、不留注释掉的代码。
12. **Translation** — 19 种语言翻译索引（含简/繁中文）。

每一节都是"反例 → 正例 → 一句话说明 → 回到顶部"的固定节奏，作者用 `**Bad:**` / `**Good:**` 给出可直接对比的代码片段。这种结构对工程师很友好——读一段、改一段，比读一段理论再回去摸索代码高效得多。

下面挑出 7 个在工程里最高频踩坑的章节，附上原文片段和落地判断。

## 第一节：Variables（命名是免费的可读性）

命名是这本书最朴素、却最容易拉开代码质量的章节。三个高频原则：

### 1. 用"可发音、可搜索"的命名

反例：

```javascript
// What the heck is 86400000 for?
setTimeout(blastOff, 86400000);
```

正例：

```javascript
const MILLISECONDS_PER_DAY = 60 * 60 * 24 * 1000;
setTimeout(blastOff, MILLISECONDS_PER_DAY);
```

工程判断：常量命名不是为了让 IDE 自动补全，而是为了让 grep 一次就能定位到全工程所有用法。`buddy.js` 和 ESLint 的 `no-magic-numbers` 规则可以直接机械化发现"裸数字"。

### 2. 别让读者做心算映射

反例：

```javascript
const locations = ["Austin", "New York", "San Francisco"];
locations.forEach(l => {
  doStuff();
  doSomeOtherStuff();
  dispatch(l); // l 是什么？
});
```

正例：

```javascript
locations.forEach(location => {
  doStuff();
  doSomeOtherStuff();
  dispatch(location);
});
```

工程判断：单字母 `l`、`i`、`j` 在循环里是 JS 历史遗留习惯，在多层闭包里几乎一定会引起"心算"。`forEach` / `map` / `filter` 这种高阶调用，把参数名字写长一点，是 0 成本的改进。

### 3. 默认参数替代短路或三元

```javascript
function createMicrobrewery(name = "Hipster Brew Co.") { /* ... */ }
```

注意一个容易踩的边界：默认参数只对 `undefined` 生效，对 `''`、`null`、`0`、`NaN` 不会替换。如果业务里要"任何 falsy 都用默认值"，仍要写 `name ?? "Hipster Brew Co."`。

## 第二节：Functions（短小 + 单一职责）

函数章节的核心命题是"函数应该做一件事"。支撑这条命题的还有几条具体规则。

### 1. 参数上限 2 个，3 个开始考虑封装

```javascript
function createMenu({ title, body, buttonText, cancellable }) { /* ... */ }

createMenu({ title: "Foo", body: "Bar", buttonText: "Baz", cancellable: true });
```

传对象的好处不只是"避免 4 个位置参数记错顺序"，还包括：

- 函数签名一眼看到用了哪些属性。
- 在 JS 里能模拟"命名参数"。
- 解构出的原始值是值拷贝，可以避免一部分副作用。
- ESLint 之类的工具可以警告"有未使用的属性"。

### 2. 函数只做一件事

原文："This is by far the most important rule in software engineering. When functions do more than one thing, they are harder to compose, test, and reason about."

工程判断：判断"一件事"的标准不是看函数多短，而是看函数是否还能再被有意义地拆分。如果一段函数里有"解析输入 → 校验 → 计算 → 持久化 → 通知"等明显的步骤，它就不是一件事。拆开后单独测试的成本会下降一个量级。

### 3. 函数名要描述"它做了什么"

`addDate` 比 `add` 好，`postPayment` 比 `post` 好。动词 + 宾语比动词单独命名更利于 IDE 搜索和阅读心智模型。

## 第三节：Objects and Data Structures（避免副作用、不可变优先）

这条原则对函数式背景的读者并不陌生，但 JavaScript 工程师最容易踩坑。

### 1. 避免对入参做 in-place 修改

反例：

```javascript
const addItemToCart = (cart, item) => {
  cart.push({ item, date: Date.now() });
};
```

正例：

```javascript
const addItemToCart = (cart, item) => {
  return [...cart, { item, date: Date.now() }];
};
```

工程判断：入参数组/对象如果是上层持有的引用，原地修改会悄悄影响所有持有者。文中举的"购物车在断网重试时被用户误加了一条商品"的场景，是这种 bug 在生产里最经典的形态。

### 2. 不要污染全局

反例：

```javascript
Array.prototype.diff = function diff(comparisonArray) { /* ... */ };
```

正例：

```javascript
class SuperArray extends Array {
  diff(comparisonArray) { /* ... */ }
}
```

工程判断：改写原生 prototype 的库 5 年前就被社区认定为反模式，TypeScript 引入 `declare global` 之后这条更显眼。一旦某个依赖偷偷在 `Array.prototype` 上加方法，全工程的 `for...in`、JSON 序列化都会受到污染。

### 3. 优先函数式风格

```javascript
const totalOutput = programmerOutput.reduce(
  (totalLines, output) => totalLines + output.linesOfCode,
  0
);
```

`reduce` / `map` / `filter` / `find` 写出来的代码副作用更少、测试更简单，`for (let i = 0; ...)` 这种命令式累加在新代码里基本可以淘汰。

## 第四节：Classes（ES2015/ES6 优于 ES5）

作者对 ES5 时代的"函数 + prototype"继承写法直接给出了"反例"，理由是阅读门槛高、出错率高：

```javascript
const Animal = function (age) {
  if (!(this instanceof Animal)) throw new Error("Instantiate Animal with `new`");
  this.age = age;
};
Animal.prototype.move = function move() {};
const Mammal = function (age, furColor) { /* ... */ };
Mammal.prototype = Object.create(Animal.prototype);
Mammal.prototype.constructor = Mammal;
```

正例：

```javascript
class Animal {
  constructor(age) { this.age = age; }
  move() { /* ... */ }
}
class Mammal extends Animal {
  constructor(age, furColor) { super(age); this.furColor = furColor; }
  liveBirth() { /* ... */ }
}
```

工程判断：这条不只是"用 class 语法糖"，而是顺带引入 `extends` / `super` 这种语义清晰的继承表达。如果团队还没升级到 ES2015+，这条原则带来的可读性差距会非常大。

但作者也明确：组合优先于继承。在没有强需求时不要轻易引入继承——能用一个小对象持有另一个对象解决的，就别让两者形成 `instanceof` 关系。

## 第五节：Error Handling（抛错，不是返回错误码）

错误处理是这本手册里被低估的章节。

### 1. 抛错优于返回错误码

反例：

```javascript
function addShopper(shopper) {
  if (shopper.status !== "active") return false;
  // ...
}
```

正例：

```javascript
function addShopper(shopper) {
  if (shopper.status !== "active") {
    throw new Error(`Shopper ${shopper.id} is not active`);
  }
  // ...
}
```

工程判断：返回值是 `boolean` 还是 `error object` 这种约定很难在所有调用点保持一致，几个月后就会有调用者忘记检查返回值，导致错误悄无声息地传播。抛错 + 类型系统的 `Result` 风格，是更可控的现代方案。

### 2. 不要忽略 catch

反例：

```javascript
try {
  functionThatMightThrow();
} catch (error) {
  console.log(error);
}
```

正例：要么 throw 出去，要么在 catch 里做有意义的恢复或上报；不要吞掉错误又不留任何提示。

工程判断：吞错误是大型前端项目里最难定位的问题之一，作者给的最小修复至少是"显式说明为什么吞"——比如 `// 已重试过 N 次仍失败，此处忽略以避免阻塞 UI 渲染`，而不是一行 `catch (e) {}`。

## 第六节：Comments（注释只解释"为什么"）

注释章节是最反直觉的一章，作者认为：**大多数注释是坏味道**。

### 1. 不要写 journal comments

反例：

```javascript
/**
 * 2016-12-20: Removed monads, didn't understand them (RM)
 * 2016-10-01: Improved using special monads (JP)
 * ...
 */
function combine(a, b) { return a + b; }
```

正例：什么都不写。版本控制系统自带日志。

### 2. 不要留注释掉的代码

`git log` 是历史，`// doOtherStuff();` 不是。注释掉的代码既不执行也不删除，会让读者怀疑它是否在某些边界场景里仍然生效。

### 3. 位置标记不是结构

```javascript
////////////////////////////////////////////////////////////////////////////////
// Scope Model Instantiation
////////////////////////////////////////////////////////////////////////////////
```

这种装饰条只是噪音。函数和缩进已经在视觉上给出了结构。

工程判断：注释只解释**why**，不解释**what**——`what` 由代码自身表达。`TODO` / `FIXME` / 关键业务约束的注释是允许的，但代码内部状态变更的"日志注释"、注释掉的代码、用 `=====` 切的伪章节，全部应该删除。

## 第七节：Concurrency（async/await 不是同步）

并发章节只有几条短规则，但工程含义重要：

- 用 `Promise` 替代回调地狱，但**不要所有异步都 `await`**——能并行的并行（`Promise.all`），不要串行。
- `async` 函数永远返回 `Promise`，调用方要么 await 要么继续传。
- 命名上建议区分 `xxxAsync` / `xxxSync`，避免混淆。

工程判断：JS 里"async 函数让异步代码看起来像同步代码"是个陷阱，写 5 个连续的 `await` 会自动把 5 个独立的网络请求变成串行执行。`Promise.all` / `Promise.allSettled` 是任何超过一个并行的异步场景都应该首先考虑的写法。

## 阅读路径建议

12 章不必一次读完。推荐两层读法：

**第一遍（1-2 小时，速读）**：Introduction → Variables → Functions → Objects → Classes → Comments。这一层是"命名 + 短小 + 注释"。改这一层的代码风险最低、收益最高，几乎所有团队都能在不引入新依赖的前提下落地。

**第二遍（2-3 小时，深读）**：SOLID → Testing → Concurrency → Error Handling → Formatting。这一层涉及设计取舍和工程节奏，需要和团队一起讨论"做到什么程度"。SOLID 五条不必五条都做，先看 Single Responsibility 和 Dependency Inversion 通常就够了。

读完之后把它当成**参考书**而不是**学习手册**——遇到 lint 规则触发时翻一节，遇到 PR review 卡住时翻一节，比一次性通读更可持续。

## 与本地翻译版的差异

仓库自带 19 种语言翻译索引，其中简体中文有两个并行版本：

- [alivebao/clean-code-js](https://github.com/alivebao/clean-code-js)
- [beginor/clean-code-javascript](https://github.com/beginor/clean-code-javascript)

繁体中文版是 [AllJointTW/clean-code-javascript](https://github.com/AllJointTW/clean-code-javascript)。翻译版能降低英文阅读门槛，但**反例/正例代码不翻译**，代码片段仍然是英文。把它和英文原版一起对照阅读效果更好——尤其是想确认某个 JS 惯用法（比如解构、扩展运算符、class 字段）是不是被中文翻译准确表达。

## 适用边界

适合：

- 团队希望统一一份"轻量级代码风格共识"，但又不想上 ESLint 全套规则集。
- 工程师从其他语言转 JS，希望一份"过来人"的工程笔记作为入门参考。
- Code review 卡在某条具体规则上，需要引用权威段落时。

不适合：

- 把它当 lint 规则集——仓库明确说"this is not a style guide"。
- 直接把所有反例当"硬错误"——比如 `for (let i = 0; i < ...)` 在某些性能敏感的 hot path 里仍然是首选写法。
- 把它当完整设计手册——SOLID 五条只用了很短篇幅，更深入的设计内容需要回到《Clean Code》原书或 Martin Fowler 的《Refactoring》。

## 结语

`clean-code-javascript` 的价值不在"教你新东西"，而在**给团队一份共同的代码语汇**：当两个人对"这个函数该不该拆"有分歧时，引一句"Functions should do one thing"比争论 5 分钟更快收敛。它已经成为 JavaScript 社区里事实上的入门必读手册之一，94k Star 和 19 种翻译版本本身就是它的影响力证明。

如果团队里还没有一份"代码审美基线"，它是一个起点；如果已经有了，可以把它当成新人 onboarding 的第一份参考资料。