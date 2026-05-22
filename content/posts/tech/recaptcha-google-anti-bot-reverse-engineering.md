---
title: "reCAPTCHA逆向工程：Google反爬虫机制的技术剖析"
date: 2026-05-22T20:10:00+08:00
slug: "recaptcha-reverse-engineering-google-anti-bot-analysis"
description: "elelysiox/recaptcha是一个reCAPTCHA逆向工程文档项目，详细记录了Google reCAPTCHA的Payload结构、指纹识别技术、代码混淆方法和反调试技术。"
draft: false
categories: ["技术笔记"]
tags: ["reCAPTCHA", "逆向工程", "JavaScript", "反爬虫", "安全研究"]
---

# reCAPTCHA逆向工程：Google反爬虫机制的技术剖析

elelysiox/recaptcha 是一个 reCAPTCHA 逆向工程文档，记录了 Google reCAPTCHA v2/v3 的内部机制。2026-05-22创建，30星。

## 核心判断

reCAPTCHA 是目前最复杂的浏览器反机器人系统之一。它的防护不靠单一技术，而是多层混淆叠加：代码混淆（AST级）、控制流扁平化、加密字符串池、状态机逃逸、异步生成器链、运行时值加密。每层都可以被单独分析，但组合在一起使得静态分析和 LLM-based 反向工程变得极其困难。

## 混淆技术全景

### 1. 序列表达式（Sequence Expressions）

代码被扁平化为连续的逗号分隔表达式，出现在 if 语句、函数参数、甚至对象内部：

```javascript
// 扁平前
if (condition) {
    doSomething();
    doAnother();
}

// 扁平后（混淆后）
condition && (doSomething(), doAnother())
```

### 2. 混合布尔运算（Mixed Boolean Arithmetic）

算术运算（加减乘）和位运算（AND/OR/XOR/NOT）交织在一起：

```javascript
-2 * ~(h & H) + -2 + (h ^ H)
```

### 3. 间接函数表

每个函数在表中构建，通过索引调用：

```javascript
functions[index](args)
```

### 4. 内联常量数组

常量（数字、字符串）在表达式中间内联赋值，通过索引访问复用：

```javascript
// b = [14, 1, "call"] assigned inline
function(Y, Q, c, l, G, X, W, J, b, P) {
    (Y & 94) == Y && (b = [14, 1, "call"], ...)
    W[b[2]](J, G)   // → W.call(J, G)
    Y >> b[1] & b[0]  // → Y >> 1 & 14
}
```

### 5. 函数复用（Function Multiplexing）

多个逻辑上不同的函数合并为一个，用数字参数作为分块选择器：

```javascript
function(N, y, U, Y, h, H, m, C, u) {
    C = [26, 47, 6];

    // block 1
    if ((N - 2 ^ 14) < N && (N - C[2] | 28) >= N) {
        // convert value to string logic
    }

    // block 2
    if ((N + 4 & 40) >= N && (N + 5 & C[0]) < N) {
        Y = bB();
        throw Error(Y === void 0 ? "unexpected value " + U + y : Y);
    }

    return u;
}
```

### 6. 逻辑运算符分支

用逻辑运算符短路求值替代 if/else，控制流变成表达式：

```javascript
// if (a) { block }
a && (block)

// if (!a) { block }
a || (block)

// if (a) { x } else { y }
a ? x : y
```

### 7. 原生方法常量绑定

把原生浏览器方法绑定到原始接收者，存为常量防止篡改：

```javascript
LO = (Tw = self) == null ? void 0 :
     (K9 = Tw.Math) == null ? void 0 :
     (v4 = K9.floor) == null ? void 0 :
     (mF = v4.bind) == null ? void 0 :
     mF.call(v4, Math)  // Math.floor.bind(Math)

LO(x)           // Math.floor(x)
U4()            // Math.random()
Ge(obj, prop)   // Object.defineProperty(obj, prop)
```

### 8. 控制流扁平化（Control Flow Flattening）

每个代码块变成状态机，经过中央调度器路由：

```
dispatcher(state) → case 0 → block 0 → dispatcher(state)
                 → case 1 → block 1 → dispatcher(state)
                 → case 2 → block 2 → dispatcher(state)
```

### 9. 加密字符串池

所有字符串字面量（DOM API、浏览器属性、CSS 值、错误消息）加密成一个大字符串池，解密函数使用种子和基于 LCG 的 XOR 密码：

```javascript
// 1990+ 调用点，解密函数使用运行密钥
Z[23](64, 4, 54961, 103)()  // → "lang"
Z[23](66, 4, 54961, 103)()  // → "addEventListener"
```

### 10. 有状态值迭代器

一个带状态迭代器按固定顺序返回运行时对象，调用sequence或超时都会导致状态损坏：

```javascript
c()  // → window
c()  // → document.body
c()  // → 123
c()  // → null (timeout expired)
```

### 11. 计算函数表

函数索引在运行时用种子计算（XOR 和模运算）：

```javascript
c = ((Q ^ no | U[1]) >> 5) + no
A = mN[(c % U[2] + U[2]) % U[2]]  // mN 是50+函数的函数表

q[29](5, 6977)   // seed=6977  → 索引解析为 mN[X]
q[29](53, 6187)  // seed=6187  → 不同索引，不同函数
```

### 12. 运行时值加密

有些值（验证码配置参数、锚点参数）从不以明文存储，收集后立即加密，使用时解密，值以 `B` 开头：

```javascript
Bxxxxxxxxxx  // 加密的配置参数
```

### 13. 异步控制流混淆

同步逻辑转换为基于生成器的状态机，包装在递归 Promise 链中，调试器追踪任何值都强制逐步执行多个异步处理程序。

## Payload 结构

### Anchor Payload

```
ar:         <WidgetInit?>
k:          <Website Key>
co:         <Website URL Base64-Encoded>
hl:         <Browser Main Language>
v:          <Recaptcha Version>
size:       <Type>
sa:         <Site Action>
anchor-ms:  <Widget Load Timeout>
execute-ms: <Execution Timeout>
cb:         <CallBack ID>
```

## 适用边界

**适合：**
- 安全研究
- 反爬虫机制学习
- 浏览器指纹识别研究

**不适合：**
- 用于绕过 reCAPTCHA（违法）
- 用于构建商业反爬虫产品（可能侵权）

## 结论

reCAPTCHA 的混淆设计代表了浏览器端反机器人技术的最高水平。它的多层防御机制使得即使有工具也很难完整分析。这个项目更适合作为安全研究学习材料，而不是实战工具。