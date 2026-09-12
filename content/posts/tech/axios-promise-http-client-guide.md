---
title: "Axios：Promise HTTP 客户端完全指南"
date: "2026-04-03T01:25:00+08:00"
slug: "axios-promise-http-client-guide"
github_repo: "axios/axios"
source_key: "gh:axios/axios"
description: "Axios 是基于 Promise 的 HTTP 客户端，支持浏览器和 Node.js 环境。本文覆盖安装配置、基本使用、拦截器、错误处理、请求取消、数据序列化、推荐做法和常见问题。"
draft: false
categories: ["技术笔记"]
tags: ["JavaScript", "HTTP", "Node.js"]
---

# Axios：Promise HTTP 客户端完全指南

> **快速信息卡**
> - **GitHub**: [axios/axios](https://github.com/axios/axios)
> - **Stars**: 109k+
> - **Forks**: 11.8k+
> - **License**: MIT
> - **语言**: JavaScript/TypeScript
> - **最后更新**: 2026-09-08

---

## 阅读地图

- [一、项目概述](#一项目概述)：Axios 是什么、核心特性、与 fetch 的取舍
- [二、安装与环境配置](#二安装与环境配置)：npm / CDN 安装，环境与导入方式
- [三、基本使用](#三基本使用)：GET / POST、并发、async/await、response 结构
- [四、Axios API 详解](#四axios-api-详解)：请求方式与配置项
- [五、创建 Axios 实例](#五创建-axios-实例)：实例的作用与默认值继承
- [六、拦截器](#六拦截器)：请求/响应拦截器
- [七、错误处理](#七错误处理)：AxiosError 分层判断
- [八、请求取消](#八请求取消)：AbortController 替代 CancelToken
- [九、数据序列化](#九数据序列化)：URL 编码与 FormData
- [十、配置默认值](#十配置默认值)：请求、实例、全局的覆盖顺序
- [十一、速率限制](#十一速率限制)：请求间隔控制
- [十二、实践建议](#十二实践建议)：统一错误、重试、监控封装
- [十三、常见问题](#十三常见问题)、[十四、自测与采用顺序](#十四自测与采用顺序)

适合已经有 JavaScript 基础、会用 `async/await` 的读者。读完后你应该能独立完成下列事情：跑通一次 GET 与 POST 请求；用一个 `axios.create` 实例收敛 baseURL 与超时；通过拦截器统一注入请求头并归一错误；用 `AbortController` 在页面切换或超时时取消请求；最后把这一套封装成一个可直接接入项目、带重试和监控的客户端。

---

## 一、项目概述

### Axios 是什么

**Axios** 是一个基于 Promise 的 HTTP 客户端，走一套同时跑在浏览器和 Node.js 的 API。它没有带来新的网络概念，更多是把你常写的那段"发请求、等响应、判错误、拆数据"样板代码收拢进库，再用拦截器、实例和超时这些约定把重复逻辑抽走。它的价值几乎都落在"省包装"上：用 `fetch` 得自己封装错误判断和拦截，而 Axios 把这些写进了库本身。

**官方网站**：[https://axios-http.com](https://axios-http.com)
**官方文档**：[https://axios.rest](https://axios.rest)（2026 年起，axios-http.com/docs 已整体迁移并重定向到新文档站）
**GitHub 仓库**：[https://github.com/axios/axios](https://github.com/axios/axios)

### 主要特性

| 特性 | 说明 |
|------|------|
| 浏览器请求 | 从浏览器使用 XMLHttpRequest 发送请求 |
| Node.js 请求 | 在 Node.js 环境中发送 http 请求 |
| Promise API | 完整支持 Promise API，async/await 友好 |
| 拦截器 | 拦截请求和响应，可添加自定义逻辑 |
| 数据转换 | 自动转换请求和响应数据 |
| 请求取消 | 支持使用 AbortController 取消请求 |
| 自动 JSON 处理 | 自动序列化/解析 JSON 数据 |
| 表单序列化 | 支持 application/x-www-form-urlencoded 和 multipart/form-data |
| XSRF 防护 | 内置跨站请求伪造防护机制 |

### 仓库统计

| 指标 | 数值（2026-09-08） |
|------|------|
| GitHub Stars | 109.2k |
| Forks | 11.8k |
| Open Issues | 88（GitHub API 口径，含 PR） |
| 最新版本 | 1.20.0（npm latest） |
| 默认分支 | v1.x |
| 许可证 | MIT |

### Axios vs fetch API

| 对比项 | Axios | fetch API |
|--------|-------|-----------|
| JSON 自动处理 | ✅ 自动 | ❌ 需要手动调用 .json() |
| 请求取消 | ✅ 简单易用 | ⚠️ AbortController（较复杂） |
| 超时控制 | ✅ 内置 timeout 配置 | ❌ 需要额外实现 |
| 拦截器 | ✅ 简洁易用 | ❌ 需要包装 fetch |
| 错误处理 | ✅ 统一处理 4xx/5xx | ⚠️ 仅在网络错误时 reject |
| 浏览器兼容 | ✅ 广泛兼容 | ⚠️ 现代浏览器 |
| 请求/响应转换 | ✅ 易于配置 | ❌ 需要手动处理 |

### 什么时候优先选 Axios

如果业务里常见"同一个 baseURL、统一加请求头、统一处理 4xx/5xx、控制超时"这类重复逻辑，Axios 的实例、拦截器和 `AxiosError` 分层判断能少写不少样板；这类需求出现得越多，省下的代码越明显。反过来，如果项目对依赖数量很敏感，或只是偶尔发一两个基础请求，原生 `fetch` 加上一两个小封装就够，不必为这些场景引入一个库。

---

## 二、安装与环境配置

### 支持的环境

**浏览器支持**：Chrome、Firefox、Safari、Opera、Edge（最新版）

**Node.js 环境**：跟随当前活跃的 Node.js 发布线，具体兼容范围以各版本发布说明为准。

### 安装方式

**使用 npm**：

```bash
npm install axios
```

**使用 yarn**：

```bash
yarn add axios
```

**使用 pnpm**：

```bash
pnpm add axios
```

**使用 bun**：

```bash
bun add axios
```

**使用 bower**（已过时）：

```bash
bower install axios
```

### CDN 引入

**使用 jsDelivr（推荐）**：

```html
<script src="https://cdn.jsdelivr.net/npm/axios@1/dist/axios.min.js"></script>
```

**使用 unpkg**：

```html
<script src="https://unpkg.com/axios@1/dist/axios.min.js"></script>
```

上面的 `@1` 会始终解析到当前最新的 1.x 版本。若想锁定某个具体稳定版，把 `@1` 换成对应版本号即可，例如 `axios@1.7.7`。

### ESM 导入方式

**现代 ES6 导入**：

```javascript
import axios, { isCancel, AxiosError } from 'axios';
```

**默认导出方式**：

```javascript
import axios from 'axios';
console.log(axios.isCancel('something'));
```

**CommonJS 导入**（Node.js 传统方式）：

```javascript
const axios = require('axios');
console.log(axios.isCancel('something'));
```

---

## 三、基本使用

### GET 请求

**基础 GET 请求**：

```javascript
import axios from 'axios';

try {
  const response = await axios.get('/user?ID=12345');
  console.log(response);
} catch (error) {
  console.error(error);
}
```

**带参数的 GET 请求**：

```javascript
const response = await axios.get('/user', {
  params: {
    ID: 12345,
    name: 'John'
  }
});
```

### POST 请求

**基础 POST 请求**：

```javascript
const response = await axios.post('/user', {
  firstName: 'Fred',
  lastName: 'Flintstone'
});
console.log(response);
```

### 并发请求

```javascript
function getUserAccount() {
  return axios.get('/user/12345');
}

function getUserPermissions() {
  return axios.get('/user/12345/permissions');
}

Promise.all([getUserAccount(), getUserPermissions()])
  .then(function (results) {
    const acct = results[0];
    const perm = results[1];
    console.log('Account:', acct);
    console.log('Permissions:', perm);
  });
```

### async/await 用法

```javascript
async function getUser() {
  try {
    const response = await axios.get('/user?ID=12345');
    console.log(response);
  } catch (error) {
    console.error(error);
  }
}

getUser();
```

> **注意**：async/await 是 ECMAScript 2017 的一部分，Internet Explorer 和旧版浏览器不支持，使用时需注意兼容性。

### 理解 response 对象

Axios 请求成功时 resolve 的不是裸数据，而是一个 `response` 对象，最常用的三个字段是 `data`、`status`、`headers`：

| 字段 | 说明 |
|------|------|
| `data` | 服务端返回的响应体，JSON 已自动解析成对象或数组 |
| `status` | HTTP 状态码，如 200、404 |
| `statusText` | 状态文本，如 `OK` |
| `headers` | 响应头对象，键名统一为小写 |
| `config` | 本次请求实际使用的配置对象 |
| `request` | 底层请求对象（浏览器是 XMLHttpRequest，Node.js 是 ClientRequest） |

所以取数据时要写 `response.data`，而不是 `response` 本身。如果嫌每个调用点都多一层 `.data` 麻烦，可以在响应拦截器里先剥掉外壳：

```javascript
// 全局生效
axios.interceptors.response.use(response => response.data);
```

若你用的是上一节创建的实例，把拦截器注册在实例上，只影响该实例的请求：

```javascript
const apiClient = axios.create({ baseURL: 'https://api.example.com' });
apiClient.interceptors.response.use(response => response.data);
```

之后业务代码拿到的就是解析后的数据：

```javascript
const users = await apiClient.get('/users'); // users 直接是数组
```

---

## 四、Axios API 详解

### 请求方式

Axios 提供了多种请求方式：

```javascript
// 通用请求方式
axios({
  method: 'post',
  url: '/user/12345',
  data: {
    firstName: 'Fred',
    lastName: 'Flintstone'
  }
});

// GET 请求
axios.get('/user/12345');

// POST 请求
axios.post('/user', {
  firstName: 'Fred',
  lastName: 'Flintstone'
});

// DELETE 请求
axios.delete('/user/12345');

// PUT 请求
axios.put('/user/12345', {
  firstName: 'Fred'
});

// PATCH 请求
axios.patch('/user/12345', {
  firstName: 'Fred'
});

// HEAD 请求
axios.head('/user/12345');

// OPTIONS 请求
axios.options('/user/12345');
```

### 请求配置

**常用配置项**：

```javascript
const response = await axios({
  baseURL: 'https://api.example.com',
  timeout: 5000,
  headers: {
    'X-Custom-Header': 'foobar',
    'Content-Type': 'application/json'
  },
  params: {
    ID: 12345
  },
  auth: {
    username: 'admin',
    password: 'secret'
  }
});
```

### 配置项详解

| 配置项 | 类型 | 说明 |
|--------|------|------|
| url | string | 请求 URL，必填 |
| method | string | 请求方法，默认为 GET |
| baseURL | string | 基础 URL，将自动拼接在 url 前 |
| timeout | number | 超时时间（毫秒），默认为 0（无超时） |
| headers | object | 自定义请求头 |
| params | object | URL 参数，会自动序列化为 ?key=value |
| data | any | 请求体数据 |
| auth | object | HTTP Basic 认证 {username, password} |
| responseType | string | 响应类型：json/blob/document/stream/text |
| withCredentials | boolean | 是否携带跨域 cookies |
| validateStatus | function | 定义哪些状态码算成功，返回 false 时拒绝该请求 |
| maxContentLength | number | 响应体体积上限（字节），超限直接抛错 |
| maxBodyLength | number | 请求体体积上限（字节），主要用于 Node.js |
| onDownloadProgress | function | 下载进度回调 |
| xsrfCookieName | string | XSRF token 读取的 cookie 名，默认 `XSRF-TOKEN` |
| xsrfHeaderName | string | XSRF token 写入的请求头名，默认 `X-XSRF-TOKEN` |

`validateStatus` 默认是「200-299 都算成功」，想放宽或收紧就覆盖它，例如把 304 也归入成功：

```javascript
const resp = await axios.get('/page', {
  validateStatus: (status) => status >= 200 && status < 300 || status === 304
});
```

`responseType` 若设为 `stream`，只在 Node.js 环境生效；浏览器端可选值受 XMLHttpRequest 限制，只有 `json`、`text`、`blob`、`arraybuffer`、`document`。

XSRF 防护由 `xsrfCookieName` 和 `xsrfHeaderName` 两个配置项共同完成：Axios 会从 `xsrfCookieName` 指定的 cookie 中读取 token，再写入 `xsrfHeaderName` 指定的请求头里发给后端。两者默认值分别是 `XSRF-TOKEN` 和 `X-XSRF-TOKEN`，如果后端约定了不同的字段名，需要在创建实例时显式覆盖。要注意边界：cookie 只能被同源页面读取，跨域请求通常碰不到那个 token，所以 XSRF 这套只对同源请求有意义，不能拿来当作跨域安全机制。

---

## 五、创建 Axios 实例

### 为什么需要实例

创建实例可以设置默认配置，适用于需要多个不同配置的 API 场景：

```javascript
const apiClient = axios.create({
  baseURL: 'https://api.example.com',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 使用实例发送请求
const response = await apiClient.get('/users');
```

### 实例方法

实例拥有与 axios 相同的方法别名：

```javascript
const instance = axios.create({
  baseURL: 'https://api.example.com'
});

// 等价于 axios.get()
instance.get('/users');

// 等价于 axios.post()
instance.post('/users', { name: 'John' });

// 获取完整 URL
const uri = instance.getUri({ url: '/users', params: { ID: 123 } });
// -> https://api.example.com/users?ID=123
```

---

## 六、拦截器

### 请求拦截器

请求拦截器用于在请求发送前修改配置或添加通用逻辑：

```javascript
axios.interceptors.request.use(
  function (config) {
    // 在发送请求之前做些什么
    console.log('请求发送:', config.url);
    return config;
  },
  function (error) {
    // 对请求错误做些什么
    return Promise.reject(error);
  }
);
```

### 响应拦截器

响应拦截器用于在处理响应前统一处理：

```javascript
axios.interceptors.response.use(
  function (response) {
    // 对响应数据做点什么
    console.log('响应成功:', response.status);
    return response;
  },
  function (error) {
    // 对响应错误做点什么
    console.error('响应错误:', error.message);
    return Promise.reject(error);
  }
);
```

### 移除与清空拦截器

`use()` 的返回值是这条拦截器的编号，把它传给 `eject()` 就能移除；`clear()` 则一次清空同类拦截器：

```javascript
const logger = axios.interceptors.request.use(config => {
  console.log('发送:', config.url);
  return config; // 不返回 config，后续拿到的请求头会是 undefined
});

axios.interceptors.request.eject(logger);
```

```javascript
const apiClient = axios.create();

// 清空该实例上所有请求/响应拦截器
apiClient.interceptors.request.clear();
apiClient.interceptors.response.clear();
```

`eject` 与 `clear` 对全局 `axios` 和 `axios.create` 的实例都有效。开发热更新场景下，先用 `clear()` 清场再注册，比让旧拦截器反复叠加要可靠。

### 多个拦截器的执行顺序

两类拦截器的方向相反，这是官方文档明确约定的行为：**请求拦截器后添加先执行（LIFO）**，**响应拦截器先添加先执行（FIFO）**：

```javascript
axios.interceptors.request.use(fn1);
axios.interceptors.request.use(fn3);
// 执行顺序：fn3 -> fn1 -> 请求发出（后添加的先执行）

axios.interceptors.response.use(fn4);
axios.interceptors.response.use(fn5);
// 执行顺序：fn4 -> fn5 -> 业务代码（先添加的先执行）
```

LIFO 有个容易踩的实际影响：请求拦截器有依赖关系时（先取 token、再把 token 写进 header），被依赖的那个要**最后注册**——它会最先执行。注册顺序写反，写 header 的那一步拿到的就是空 token。

### 一次请求的完整流转

把本节的机制串起来，一次 `apiClient.get('/users')` 从发到收会经过这些站：

1. 合并配置：请求级 config 优先于实例 defaults，实例 defaults 优先于全局 defaults；
2. 请求拦截器按注册的逆序依次通过，后添加的先碰 config；
3. 适配器发出请求：默认按 xhr → http → fetch 的顺序选环境支持的第一个，浏览器走 XMLHttpRequest，Node.js 走 http，Cloudflare Workers、Deno 这类环境走 fetch；需要时可用 `adapter` 配置显式指定；
4. 响应返回，`validateStatus` 判定这个状态码算不算成功；
5. 响应拦截器按注册顺序依次通过，先添加的先碰 response；
6. `then` 里的业务代码拿到 `response` 对象。

任何一环抛出的错误都会跳进同一条 rejection 链，最后在 `catch` 里以 `AxiosError` 的形式被接住——这正是下一节错误处理的地基。

---

## 七、错误处理

### 错误类型

```javascript
async function fetchData() {
  try {
    const response = await axios.get('/user/12345');
    console.log(response.data);
  } catch (error) {
    if (axios.isCancel(error)) {
      console.log('请求被取消');
    } else if (error.code === 'ECONNABORTED') {
      console.log('请求超时');
    } else if (error.response) {
      // 服务器返回错误状态码
      console.log('服务器错误:', error.response.status);
      console.log('错误数据:', error.response.data);
    } else {
      // 请求配置错误或网络问题
      console.log('请求错误:', error.message);
    }
  }
}
```

### 获取错误信息

```javascript
try {
  await axios.get('/user/12345');
} catch (error) {
  if (error.response) {
    console.log('状态码:', error.response.status);
    console.log('响应数据:', error.response.data);
    console.log('请求配置:', error.config);
  } else {
    console.log('错误信息:', error.message);
  }
}
```

### AxiosError 的结构

Axios v1 抛出的错误是 `AxiosError` 实例，用 `error.response`、`error.request`、`error.config`、`error.code` 四个字段就能区分出错误发生在哪一层：

| 字段 | 含义 | 典型场景 |
|------|------|----------|
| `error.response` | 服务端返回了响应（4xx/5xx） | 服务器正常响应但状态码非 2xx |
| `error.request` | 已发出请求但没收到响应 | 网络中断、DNS 失败、服务端无响应 |
| `error.config` | 触发错误的请求配置 | 排查时回溯请求参数 |
| `error.code` | 错误代号字符串 | 超时是 `ECONNABORTED`，取消是 `ERR_CANCELED` |

判断顺序应固定为：先看 `error.response`，再看 `error.request`，最后才用 `error.message`。因为 `error.response` 和 `error.request` 一旦存在就说明请求确实发出了，剩下的 `message` 才是配置或其它问题。若需要完整错误快照用于上报，可直接调用 `error.toJSON()`。

---

## 八、请求取消

### AbortController（推荐方式）

浏览器与 Node.js 15+ 都原生支持：

```javascript
const controller = new AbortController();

async function fetchData() {
  try {
    const response = await axios.get('/user/12345', {
      signal: controller.signal
    });
    console.log(response);
  } catch (error) {
    if (axios.isCancel(error)) {
      console.log('请求被取消');
    } else {
      console.error(error);
    }
  }
}

// 取消请求
controller.abort();
```

### 取消多个请求

```javascript
const controller = new AbortController();

Promise.all([
  axios.get('/user/1', { signal: controller.signal }),
  axios.get('/user/2', { signal: controller.signal }),
  axios.get('/user/3', { signal: controller.signal })
]).then(function (results) {
  console.log(results);
});

// 批量取消
controller.abort();
```

### v0.x 的 CancelToken 与 v1.x 的差异

如果你在旧代码里见过 `CancelToken`，它基于已被撤回的 Promise 提案设计，自 v0.22.0 起官方就标记为废弃，并推荐改用标准化的 `AbortController`。二者并不等价：`CancelToken` 在 v1 中仍可用，但官方不建议在新项目里使用，新代码应统一用 `signal`。`isCancel(error)` 对两种取消方式产生的错误都返回 `true`，所以上文错误处理里的取消分支无需改动。

升级时不必依赖错误对象的 `code` 字符串去区分取消来源——以 `axios.isCancel(error)` 为准即可，`code` 在不同版本或不同取消方式下并不稳定。

---

## 九、数据序列化

### URLSearchParams

```javascript
const params = new URLSearchParams();
params.append('username', 'john');
params.append('password', 'secret');

await axios.post('/login', params);
```

### 自动序列化

Axios v1.x 支持自动将对象序列化为 URL 编码格式：

```javascript
await axios.post('/user', {
  username: 'john',
  password: 'secret',
  // 自动序列化为 username=john&password=secret
}, {
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded'
  }
});
```

### FormData 上传

```javascript
const formData = new FormData();
formData.append('file', fileObject);
formData.append('name', 'my-file');

await axios.post('/upload', formData, {
  headers: {
    'Content-Type': 'multipart/form-data'
  }
});
```

### 自动 FormData 序列化

Axios 支持直接将对象转换为 FormData：

```javascript
await axios.post('/upload', {
  name: 'my-file',
  file: fileObject
}, {
  headers: {
    'Content-Type': 'multipart/form-data'
  }
});
```

---

## 十、配置默认值

### 全局默认值

```javascript
axios.defaults.baseURL = 'https://api.example.com';
axios.defaults.timeout = 5000;
axios.defaults.headers.common['Authorization'] = 'Bearer token';
```

### 实例默认值

```javascript
const api = axios.create({
  baseURL: 'https://api.example.com'
});

api.defaults.timeout = 10000;
```

### 配置优先级

配置项优先级从高到低：

1. **请求的 config**
2. **实例的 defaults**
3. **全局的 defaults**

```javascript
// 全局设置 timeout 为 5000
axios.defaults.timeout = 5000;

// 实例设置 timeout 为 1000
const api = axios.create();
api.defaults.timeout = 1000;

// 此次请求设置 timeout 为 2000（优先）
api.get('/user', { timeout: 2000 });
// 此次请求使用 2000
```

---

## 十一、速率限制

### 请求间隔控制

```javascript
class RateLimiter {
  constructor(maxRequests, intervalMs) {
    this.requests = [];
    this.maxRequests = maxRequests;
    this.intervalMs = intervalMs;
  }

  async execute(fn) {
    // 窗口满了就等到最早的请求滑出窗口，再重新检查，而不是只等一次
    for (;;) {
      const now = Date.now();
      this.requests = this.requests.filter(t => now - t < this.intervalMs);

      if (this.requests.length < this.maxRequests) {
        this.requests.push(now);
        return fn();
      }

      const oldest = this.requests[0];
      await new Promise(r => setTimeout(r, this.intervalMs - (now - oldest) + 1));
    }
  }
}

const limiter = new RateLimiter(5, 1000); // 1 秒最多 5 个请求

for (const id of userIds) {
  await limiter.execute(() => axios.get(`/user/${id}`));
}
```

这套实现只管单个进程内的请求。服务一旦横向扩成多个实例，各进程的计数器互不知情，真正的限流要挪到网关或 Redis 这类共享存储上做。

---

## 十二、实践建议

### 统一错误处理

```javascript
// 创建封装函数
async function apiRequest(method, url, data = null, config = {}) {
  try {
    const response = await axios({
      method,
      url,
      data,
      ...config
    });
    return { success: true, data: response.data };
  } catch (error) {
    if (error.response) {
      return {
        success: false,
        status: error.response.status,
        message: error.response.data?.message || '服务器错误'
      };
    } else if (error.request) {
      return {
        success: false,
        message: '网络连接失败'
      };
    } else {
      return {
        success: false,
        message: error.message
      };
    }
  }
}

// 使用
const result = await apiRequest('get', '/users');
if (result.success) {
  console.log(result.data);
} else {
  console.error(result.message);
}
```

### 请求重试机制

```javascript
axios.interceptors.response.use(
  response => response,
  async error => {
    const config = error.config;

    // 被取消的请求不算失败；配置阶段就出错的请求没有 config，都无法也不该重试
    if (axios.isCancel(error) || !config) {
      return Promise.reject(error);
    }

    // 只重试网络错误（无响应）和 5xx，最多 3 次
    if (!config._retry) {
      config._retry = 0;
    }

    const shouldRetry = (!error.response || error.response.status >= 500) && config._retry < 3;
    if (shouldRetry) {
      config._retry++;
      await new Promise(r => setTimeout(r, 1000 * config._retry));
      return axios(config);
    }

    return Promise.reject(error);
  }
);
```

两个边界要守住：`axios.isCancel(error)` 挡在重试之前，否则调用方明明主动取消的动作还会被偷偷重发；重放用的 `axios(config)` 是全局实例，如果请求走的是 `axios.create` 创建的客户端，重放要改成同一个实例的调用，否则实例上的默认值和拦截器会被绕开。

### 请求日志

```javascript
axios.interceptors.request.use(config => {
  console.group(`🚀 ${config.method?.toUpperCase()} ${config.url}`);
  console.log('参数:', config.params);
  console.log('数据:', config.data);
  console.log('时间:', new Date().toISOString());
  console.groupEnd();
  return config;
});

axios.interceptors.response.use(
  response => {
    console.group(`✅ ${response.status} ${response.config.url}`);
    console.log('响应:', response.data);
    console.groupEnd();
    return response;
  },
  error => {
    console.group(`❌ ${error.config?.url}`);
    console.error('错误:', error.message);
    console.groupEnd();
    return Promise.reject(error);
  }
);
```

---

## 十三、常见问题

### Q：Axios 和 fetch 哪个更好？

**取决于使用场景**：

- **选择 Axios**：需要简洁的 API、良好的错误处理、内置拦截器、请求取消、JSON 自动处理
- **选择 fetch**：项目不想引入额外依赖、现代浏览器环境、需要更底层的控制

### Q：如何处理 CORS 跨域？

Axios 本身不处理 CORS，CORS 需要后端配置。如果遇到 CORS 问题：

1. 确认后端设置了正确的 `Access-Control-Allow-Origin` 头
2. 使用代理服务器转发请求
3. 需要携带跨域 cookies 时，客户端配置 `withCredentials: true`，服务端同时返回 `Access-Control-Allow-Credentials: true`，两端缺一不可

### Q：如何处理文件下载？

```javascript
// 浏览器端文件下载
async function downloadFile(url, filename) {
  const response = await axios.get(url, {
    responseType: 'blob',
    onDownloadProgress: (progressEvent) => {
      if (!progressEvent.total) return; // 没有 Content-Length 时 total 为 0，百分比无意义
      const percentCompleted = Math.round(
        (progressEvent.loaded * 100) / progressEvent.total
      );
      console.log(`下载进度: ${percentCompleted}%`);
    }
  });

  const link = document.createElement('a');
  link.href = URL.createObjectURL(new Blob([response.data]));
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}
```

下载时要把 `responseType` 设为 `blob`，进度通过 `onDownloadProgress` 监听；当响应没有 `Content-Length`（比如走 chunked 传输）时 `total` 为 0，此时只能拿到已传输字节数，算不出百分比。

### Q：如何处理大文件上传？

```javascript
const formData = new FormData();
formData.append('file', largeFile);

// 使用 onUploadProgress 监控进度
await axios.post('/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
  onUploadProgress: (progressEvent) => {
    if (!progressEvent.total) return;
    const percentCompleted = Math.round(
      (progressEvent.loaded * 100) / progressEvent.total
    );
    console.log(`上传进度: ${percentCompleted}%`);
  }
});
```

### Q：如何设置代理？

Node.js 环境下，Axios v1.x 通过 `proxy` 配置项直接指定代理，不需要手写 agent：

```javascript
await axios.get('/user', {
  proxy: {
    protocol: 'http',
    host: 'proxy-server',
    port: 8080,
    auth: {
      username: 'user',
      password: 'pass'
    }
  }
});
```

代理地址也可以放进 `HTTP_PROXY` / `HTTPS_PROXY` 环境变量，Axios 在 Node.js 环境会自动读取并应用。

---

## 十四、自测与采用顺序

### 自测清单

对照下面的问题检查自己理解到了哪一层，答不出的回到对应章节再看一遍：

1. 为什么 `axios.get()` 成功时得到的不是数据本身，而是 `response`？如何让调用方直接拿到数据？
2. `axios.create()` 的实例、全局 `axios.defaults` 和单次请求的 config 三者，优先级谁最高？
3. 往同一个实例注册三个请求拦截器，执行顺序是什么？换成响应拦截器呢？一个拦截器要依赖另一个的产出时，注册顺序该怎么排？
4. 响应拦截器里如何区分"拿到了 4xx 响应"和"根本没收到响应"？依据是哪两个字段？
5. 用 `AbortController` 取消请求后，错误对象有哪些特征？`axios.isCancel()` 为什么比看 `error.code` 可靠？
6. 上传和下载进度分别由哪两个回调监听？什么情况下拿不到百分比？

### 采用顺序建议

把 Axios 引入一个新项目时，建议按下面的顺序推进，避免一上来就堆拦截器和重试逻辑：

1. **先跑通基础请求**：直接用 `axios.get` / `axios.post` 发一两个请求，确认 baseURL、超时、JSON 自动解析符合预期。这一步只验证"能不能用"。
2. **创建实例收敛配置**：把 baseURL、timeout、公共 headers 收敛到一个 `axios.create` 实例里，业务代码只引用实例，不再用全局 `axios`。
3. **加请求拦截器**：在请求拦截器里统一注入 Authorization、traceId 等公共头，避免每个调用点重复写。
4. **加响应拦截器做错误归一**：把 4xx/5xx/网络错误/超时归一成统一结构，业务层只判断 `result.success`，不再各自 try/catch。
5. **按需加取消和重试**：在容易出现"快速连点"或"长轮询"的场景引入 AbortController；在调用第三方不稳定接口时引入有限重试。不要全局开重试，否则会放大下游压力。
6. **加监控和日志**：在拦截器里打请求耗时、状态码、错误类型，接入团队的监控上报通道。

这个顺序背后的逻辑是：先把"能用"跑通，再做"统一"，最后才做"加固"。跳过中间步骤直接加重试和监控，往往会让代码在还没收敛时就堆满分支。

### 生态现状

Axios 是浏览器侧使用最广的 HTTP 客户端。根据 [npm trends](https://npmtrends.com/axios-vs-got-vs-node-fetch-vs-ky) 的公开数据，它的周下载量长期处在本类别的第一梯队；GitHub 上 109.2k Stars、11.8k Forks（[axios/axios](https://github.com/axios/axios)，2026-09-08）。

它被广泛用于以下场景：

- 前端框架（React、Vue、Angular）的 SPA 项目
- 移动端开发（React Native、Ionic）
- Node.js 服务端调用第三方 API
- Electron 桌面应用

在 Node.js 18+ 环境下，原生 `fetch` 已经稳定，部分纯服务端项目开始用 `fetch` 或 [ky](https://github.com/sindresorhus/ky)、[got](https://github.com/sindresorhus/got) 替代 Axios；但在浏览器侧，Axios 的拦截器、超时、取消三件套仍然是最省心的选择。

### 相关资源

| 资源 | 链接 |
|------|------|
| 官方文档 | [https://axios.rest](https://axios.rest)（axios-http.com/docs 已重定向至此） |
| GitHub | [https://github.com/axios/axios](https://github.com/axios/axios) |
| npm | [https://www.npmjs.com/package/axios](https://www.npmjs.com/package/axios) |
| npm trends | [https://npmtrends.com/axios](https://npmtrends.com/axios) |

