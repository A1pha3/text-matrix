---
title: "Axios：Promise HTTP 客户端完全指南"
date: "2026-04-03T01:25:00+08:00"
slug: "axios-promise-http-client-guide"
description: "Axios 是基于 Promise 的 HTTP 客户端，支持浏览器和 Node.js 环境。本文覆盖安装配置、基本使用、拦截器、错误处理、请求取消、数据序列化、推荐做法和常见问题。"
draft: false
categories: ["技术笔记"]
tags: ["JavaScript", "HTTP", "Axios", "Node.js", "前端开发"]
---

# Axios：Promise HTTP 客户端完全指南

> **快速信息卡**
> - **GitHub**: [axios/axios](https://github.com/axios/axios)
> - **Stars**: 109k+
> - **Forks**: 11.6k+
> - **License**: MIT
> - **语言**: JavaScript/TypeScript
> - **最后更新**: 2026-06-26

## 学习目标

读完本指南，你会掌握：

1. Axios 的核心特性，以及它相比 fetch API 的优势和适用边界
2. 安装配置、实例创建、拦截器、错误处理、请求取消的完整用法
3. 在实际项目中引入 Axios 的采用顺序和常见陷阱
4. 如何通过拦截器统一错误处理、添加认证头、实现请求重试
5. Axios 的适用场景和不适用场景，以及迁移到 fetch 的考量

## 本文覆盖范围

读完本指南，你会了解：

1. 什么是 Promise-based HTTP 客户端、为什么选 Axios、以及它与 fetch API 的区别
2. Axios 的安装和配置方式（浏览器、Node.js）
3. GET、POST、PUT、PATCH、DELETE 等请求方法，以及参数和请求体的传递
4. 请求拦截器和响应拦截器的使用场景和用法
5. Axios 的错误处理机制，网络错误和超时的处理
6. AbortController 和 CancelToken 的用法
7. 常用的请求配置项和配置优先级规则
8. 创建 Axios 实例、编写自定义适配器、实现请求限流等扩展

## 目录

- [一、项目概述](#一项目概述)
- [二、安装与环境配置](#二安装与环境配置)
- [三、基本使用](#三基本使用)
- [四、Axios API 详解](#四axios-api-详解)
- [五、创建 Axios 实例](#五创建-axios-实例)
- [六、拦截器](#六拦截器)
- [七、错误处理](#七错误处理)
- [八、请求取消](#八请求取消)
- [九、数据序列化](#九数据序列化)
- [十、配置默认值](#十配置默认值)
- [十一、速率限制](#十一速率限制)
- [十二、实践建议](#十二实践建议)
- [十三、常见问题](#十三常见问题)
- [十四、采用顺序与总结](#十四采用顺序与总结)
- [进阶路径](#进阶路径)
- [自测题](#自测题)

---

## 一、项目概述

### Axios 是什么

**Axios** 是一个基于 Promise 的 HTTP 客户端，用于浏览器和 Node.js 环境。它提供了简洁易用的 API，能够轻松发送异步 HTTP 请求。

**官方网站**：[https://axios-http.com](https://axios-http.com)
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

| 指标 | 数值 |
|------|------|
| GitHub Stars | 109k |
| Forks | 11.6k |
| Commits | 1,888 |
| Issues | 187 |
| Pull Requests | 168 |
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

如果你需要统一错误处理、请求拦截器、超时控制和更直接的请求配置接口，Axios 往往比原生 `fetch` 更省心。

如果你的项目对额外依赖极度敏感，且只需要少量基础请求，直接使用 `fetch` 也完全合理。

---

## 二、安装与环境配置

### 支持的环境

**浏览器支持**：Chrome、Firefox、Safari、Opera、Edge（最新版）

**Node.js 环境**：官方同时覆盖浏览器和 Node.js 运行场景，具体兼容范围以当前版本发布说明为准。

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
<script src="https://cdn.jsdelivr.net/npm/axios@1.13.2/dist/axios.min.js"></script>
```

**使用 unpkg**：

```html
<script src="https://unpkg.com/axios@1.13.2/dist/axios.min.js"></script>
```

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
| xsrfCookieName | string | XSRF token 读取的 cookie 名，默认 `XSRF-TOKEN` |
| xsrfHeaderName | string | XSRF token 写入的请求头名，默认 `X-XSRF-TOKEN` |

XSRF 防护由 `xsrfCookieName` 和 `xsrfHeaderName` 两个配置项共同完成：Axios 会从 `xsrfCookieName` 指定的 cookie 中读取 token，再写入 `xsrfHeaderName` 指定的请求头里发给后端。两者默认值分别是 `XSRF-TOKEN` 和 `X-XSRF-TOKEN`，如果后端约定了不同的字段名，需要在创建实例时显式覆盖。

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
const uri = instance.getUri({ params: { ID: 123 } });
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

### 移除拦截器

```javascript
const myInterceptor = axios.interceptors.request.use(function () {/*...*/});

// 移除拦截器
axios.interceptors.request.eject(myInterceptor);
```

### 多个拦截器

多个请求拦截器按添加顺序执行（先添加先执行）：

```javascript
axios.interceptors.request.use(fn1, fn2); // 先执行 fn1
axios.interceptors.request.use(fn3);     // 后执行 fn3
// fn1 -> fn3 -> 请求发送
```

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

---

## 八、请求取消

### AbortController（推荐方式）

现代浏览器原生支持的方式：

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
    const now = Date.now();
    // 清理过期的请求记录
    this.requests = this.requests.filter(t => now - t < this.intervalMs);

    if (this.requests.length >= this.maxRequests) {
      const oldest = this.requests[0];
      const waitTime = this.intervalMs - (now - oldest);
      await new Promise(r => setTimeout(r, waitTime));
    }

    this.requests.push(now);
    return fn();
  }
}

const limiter = new RateLimiter(5, 1000); // 1 秒最多 5 个请求

for (const id of userIds) {
  await limiter.execute(() => axios.get(`/user/${id}`));
}
```

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

    // 只重试网络错误和 5xx 错误
    if (!error.response && !config._retry) {
      config._retry = 0;
    }

    if (config._retry < 3) {
      config._retry++;
      await new Promise(r => setTimeout(r, 1000 * config._retry));
      return axios(config);
    }

    return Promise.reject(error);
  }
);
```

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
3. 配置 `withCredentials: true` 发送跨域 cookies

### Q：如何处理文件下载？

```javascript
// 浏览器端文件下载
async function downloadFile(url, filename) {
  const response = await axios.get(url, {
    responseType: 'blob'
  });

  const link = document.createElement('a');
  link.href = URL.createObjectURL(new Blob([response.data]));
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}
```

### Q：如何处理大文件上传？

```javascript
const formData = new FormData();
formData.append('file', largeFile);

// 使用 onUploadProgress 监控进度
await axios.post('/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
  onUploadProgress: (progressEvent) => {
    const percentCompleted = Math.round(
      (progressEvent.loaded * 100) / progressEvent.total
    );
    console.log(`上传进度: ${percentCompleted}%`);
  }
});
```

### Q：如何设置代理？

```javascript
const proxyAgent = new https-proxyagent('http://proxy-server:8080');

axios.get('/user', {
  httpAgent: proxyAgent,  // Node.js 环境
  httpsAgent: proxyAgent
});
```

---

## 十四、采用顺序与总结

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

Axios 是目前最流行的 HTTP 客户端库之一。根据 [npm trends](https://npmtrends.com/axios-vs-got-vs-node-fetch-vs-ky) 的公开数据，Axios 的周下载量长期保持在 5000 万次以上，在浏览器侧 HTTP 客户端类别里下载量排名第一；GitHub 上 109k Stars、11.6k Forks，是 [axios/axios](https://github.com/axios/axios) 仓库的统计口径。

它被广泛用于以下场景：

- 前端框架（React、Vue、Angular）的 SPA 项目
- 移动端开发（React Native、Ionic）
- Node.js 服务端调用第三方 API
- Electron 桌面应用

需要说明的是，在 Node.js 18+ 环境下，原生 `fetch` 已经稳定，部分纯服务端项目开始用 `fetch` 或 [ky](https://github.com/sindresorhus/ky)、[got](https://github.com/sindresorhus/got) 替代 Axios；但在浏览器侧，Axios 的拦截器、超时、取消三件套仍然是最省心的选择。

### 相关资源

| 资源 | 链接 |
|------|------|
| 官方文档 | [https://axios-http.com/docs/intro](https://axios-http.com/docs/intro) |
| GitHub | [https://github.com/axios/axios](https://github.com/axios/axios) |
| npm | [https://www.npmjs.com/package/axios](https://www.npmjs.com/package/axios) |
| 官方博客 | [https://axios-http.com/blog](https://axios-http.com/blog) |
| npm trends | [https://npmtrends.com/axios](https://npmtrends.com/axios) |

---

## 进阶路径

把基础用法用熟之后，可以往这几个方向延伸：

- **自定义适配器**：Axios 的 `adapter` 配置项允许你接管底层请求逻辑。比如在测试环境用 `axios-mock-adapter` 拦截请求返回 mock 数据，在 Electron 主进程里把 HTTP 请求转发到原生 net 模块。
- **TypeScript 类型扩展**：给 `axios.create` 返回的实例加泛型，让 `api.get<User>('/users/1')` 直接返回 `User` 类型，避免业务层再做类型断言。
- **配合 OpenAPI 代码生成**：用 [openapi-generator](https://openapi-generator.tech/) 把后端 OpenAPI 规范直接生成基于 Axios 的类型化客户端，省掉手写接口定义。
- **请求编排**：在拦截器里实现请求去重（相同 URL 的并发请求合并成一个）、请求队列、断网重连，这些是中大型 SPA 的常见诉求。
- **迁移到 fetch + 包装层**：如果你的项目对包体积极度敏感，可以参考 Axios 的拦截器设计，在 fetch 上封装一层薄包装，保留统一错误处理能力，同时把 bundle 体积降到接近 0。

---

## 自测题

回答以下问题，检验你对 Axios 的掌握程度：

1. Axios 的配置优先级从高到低是什么？给一个具体例子说明三层配置如何叠加。
2. `xsrfCookieName` 和 `xsrfHeaderName` 各自的作用是什么？为什么需要两个配置项而不是一个？
3. 请求拦截器和响应拦截器的执行顺序是怎样的？多个请求拦截器之间是按什么顺序执行？
4. 用 `AbortController` 取消请求时，被取消的请求会进入 `catch` 分支还是 `then` 分支？如何区分"被取消"和"网络错误"？
5. 假设你要给一个 React 项目引入 Axios，团队要求"所有 401 都跳登录页、所有 5xx 都重试 2 次、所有请求都带 traceId"，你会怎么设计拦截器？画出大致结构。
6. 在 Node.js 18+ 环境下，什么场景下你会选择 Axios 而不是原生 fetch？说出至少两个理由。

---

🦞 文档版本：2026-04-03 | Axios 版本：v1.x | 来源：[GitHub](https://github.com/axios/axios)
