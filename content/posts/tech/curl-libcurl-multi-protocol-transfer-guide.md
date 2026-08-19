---
title: "curl 与 libcurl：互联网数据传输基石的架构解析"
date: "2026-04-27T15:00:00+08:00"
slug: "curl-libcurl-multi-protocol-transfer-guide"
github_repo: "curl/curl"
description: "curl 是互联网数据传输领域最不可或缺的基础设施之一。本文从架构视角解析 curl 命令行工具与 libcurl 库的设计关系，介绍 easy / multi / share 三种编程接口的区别与应用场景、curl_url 的独立设计，并用一次完整请求串起整个调用链，最后附自测与进阶路径。"
categories: ["技术笔记"]
tags: ["HTTP", "C语言", "开源"]
draft: false
---

# curl 与 libcurl：互联网数据传输基石的架构解析

## 目录

- [项目概览与架构总览](#项目概览与架构总览)
- [curl 命令行与 libcurl 库：两个层级的抽象](#curl-命令行与-libcurl-库两个层级的抽象)
- [libcurl 三种编程接口](#libcurl-三种编程接口)
- [curl_url：为什么要自己做 URL 解析](#curl_url为什么要自己做-url-解析)
- [协议支持：27 种协议是如何实现的](#协议支持27-种协议是如何实现的)
- [一次请求如何流过 libcurl](#一次请求如何流过-libcurl)
- [SSL/TLS 支持](#ssltls-支持)
- [适用场景、优势与边界](#适用场景优势与边界)
- [常见问题排查](#常见问题排查)
- [采用建议](#采用建议)
- [自测](#自测)
- [练习](#练习)
- [进阶路径](#进阶路径)

> **项目地址**：[curl/curl](https://github.com/curl/curl)
> **维护者**：Daniel Stenberg
> **许可证**：curl License / MIT License（双许可）
> **支持协议**：27 种（DICT, FILE, FTP, FTPS, GOPHER, GOPHERS, HTTP, HTTPS, IMAP, IMAPS, LDAP, LDAPS, MQTT, MQTTS, POP3, POP3S, RTSP, SCP, SFTP, SMB, SMBS, SMTP, SMTPS, TELNET, TFTP, WS, WSS）

---

curl 有两个名字。命令行工具叫 `curl`，承载传输逻辑的 C 库叫 `libcurl`，两者共用同一套协议实现。多数人只把 curl 当成一个发 HTTP 请求的命令，真正被长期链接进应用的是 libcurl。搞清这层关系，才能判断什么时候用命令行、什么时候嵌库、嵌库时用哪套接口。

读完本文，你应该能：说清命令行工具与 libcurl 的分工；在 easy / multi / share 里为手头的并发场景选对接口；解释 curl_url 为什么独立成组件、27 种协议如何挂进一张表；最后能跟着一次请求的完整路径，把上面这些机制串起来。

顺着这条线，下面拆几个平时不会细想的问题：

- easy / multi / share 三种接口差在哪，为什么有了 easy 还要有 multi、有了 multi 还要有 share
- curl 支持 27 种协议，每个协议怎么接进来，加新协议要不要动主循环
- URL 解析为什么不依赖系统库，要自己做一套 curl_url

---

## 项目概览与架构总览

curl 的价值不在命令行本身，而在它把二十多种协议的传输逻辑收敛进一套可复用的 C 库里。命令行工具只是这套库的最薄一层前端，真正被 Git、PHP 的 cURL 扩展、各类下载器依赖的是底层的 libcurl。理解这套分层，对网络编程、协议调试、嵌入式开发都有直接帮助。

curl 由瑞典开发者 Daniel Stenberg 于 1998 年发起，最初只是给 IRC 频道上传文件的工具。二十多年过去，它出现在几乎每一台服务器和每一条自动化脚本里，Daniel 至今保持持续提交，项目没有常见的“完成后失修”问题。

| 指标 | 数值 |
|------|------|
| 主要语言 | C |
| 维护者 | Daniel Stenberg 主导 |
| 支持协议 | 27 种（见标题下方项目信息） |

### 架构分层

curl 项目分两层：上层是命令行工具 `curl`，下层是 C 库 `libcurl`。libcurl 内部又拆成三个正交子系统——传输接口（easy / multi / share）、协议 handler 表、URL 解析引擎（curl_url）。命令行工具不直接处理协议，它把参数翻译成 libcurl API 调用，所有传输逻辑都走 handler 表分发。

```text
┌─────────────────────────────────────────────────┐
│               curl 命令行工具                    │
│  参数解析、输出格式化、配置文件读取               │
└─────────────────┬───────────────────────────┘
                  │ 调用 libcurl API
                  ↓
┌─────────────────────────────────────────────────┐
│                  libcurl 库                     │
│  ┌──────────────────────────────────────────┐  │
│  │  传输接口                                  │  │
│  │  easy（同步）/ multi（并发）/ share（共享）│  │
│  └──────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────┐  │
│  │  协议 handler 注册表                        │  │
│  │  HTTP / HTTPS / FTP / SFTP / ...        │  │
│  └──────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────┐  │
│  │  curl_url（URL 解析引擎）                  │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

命令行能做的，libcurl 都能做；但 libcurl 能做的（比如在多线程里共享 DNS 缓存），命令行没法直接暴露。后面讲接口、协议接入和一次请求的完整路径，都落在这张图上。

---

## curl 命令行与 libcurl 库：两个层级的抽象

### 命令行工具 curl

命令行 curl 是 libcurl 的前端消费者。它把用户参数翻译成 libcurl API 调用，再格式化输出结果。

前置条件：本机装有 curl。先跑 `curl --version` 确认版本；`curl -V` 能列出当前构建启用的协议和特性，后面讲协议支持时会用到。

```bash
# 最常见的 HTTP GET 请求
curl https://example.com

# 带 header 的 POST 请求
curl -X POST https://api.example.com \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'

# 跟随重定向，下载文件并保存
curl -L -o output.bin https://example.com/file.bin

# 显示完整传输过程（调试必备）
curl -v https://example.com
```

命令行工具的内部流程：

1. 解析用户传入的参数和选项（写在 `tool_getparam.c` 里）
2. 初始化 libcurl easy handle
3. 把命令行选项翻译成 `curl_easy_setopt()` 调用
4. 执行传输（`curl_easy_perform()` 或 multi 接口）
5. 格式化输出（返回给 stdout 或保存到文件）

### libcurl 库

libcurl 是承担传输逻辑的底层库，提供 C 语言 API，可以嵌入到任何应用中。Git 的 HTTP 传输、PHP 的 cURL 扩展、大量下载器和命令行工具都直接链接它。它被广泛选用，是因为一套代码覆盖二十多种协议，且经过多年生产环境验证。

```c
#include <curl/curl.h>

int main(void) {
  CURL *curl = curl_easy_init();
  if(curl) {
    curl_easy_setopt(curl, CURLOPT_URL, "https://example.com");
    curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
    CURLcode res = curl_easy_perform(curl);
    if(res != CURLE_OK)
      fprintf(stderr, "curl_easy_perform() failed: %s\n",
              curl_easy_strerror(res));
    curl_easy_cleanup(curl);
  }
  return 0;
}
```

`curl_easy_perform()` 返回 `CURLcode` 枚举，生产代码应该检查返回值并处理错误，而不是直接忽略。上面这个示例是正确处理。

---

## libcurl 三种编程接口

libcurl 提供三层接口，适用不同的并发诉求。选错接口不会让功能做不出来，但会让代码更复杂或性能更差。

### Easy Interface（同步接口）

最常用的接口。`curl_easy_perform()` 会阻塞，直到整个传输完成。

**适用场景**：

- 单个文件的下载或上传
- 简单的 HTTP 请求
- 脚本和命令行工具
- 不需要并发的桌面应用

```c
CURL *curl = curl_easy_init();
curl_easy_setopt(curl, CURLOPT_URL, "https://httpbin.org/get");
curl_easy_setopt(curl, CURLOPT_TIMEOUT, 10L);
curl_easy_setopt(curl, CURLOPT_VERBOSE, 1L);  // 调试时打开
CURLcode res = curl_easy_perform(curl);
curl_easy_cleanup(curl);
```

Easy 接口一次只能处理一个传输，要并发得换 multi 接口。

### Multi Interface（并发接口）

需要同时处理多个传输时，easy 接口就不够用了。multi 接口让你在一个线程里并发管理多个 easy handle。

**适用场景**：

- 同时下载多个文件
- 并发 HTTP 请求（比逐个串行快）
- 需要非阻塞 I/O 的应用
- 自己实现异步 HTTP 客户端

```c
CURLM *multi = curl_multi_init();

// 添加多个 easy handle 到 multi
CURL *curl1 = curl_easy_init();
CURL *curl2 = curl_easy_init();
curl_easy_setopt(curl1, CURLOPT_URL, "https://example.com/1");
curl_easy_setopt(curl2, CURLOPT_URL, "https://example.com/2");
curl_multi_add_handle(multi, curl1);
curl_multi_add_handle(multi, curl2);

// 事件驱动主循环
int still_running;
do {
  CURLMcode mc = curl_multi_perform(multi, &still_running);

  // 等待任意 handle 就绪（避免忙等）
  if(still_running)
    curl_multi_poll(multi, NULL, 0, 1000, NULL);

  // 检查是否有传输完成
  CURLMsg *msg;
  int msgs_left;
  while((msg = curl_multi_info_read(multi, &msgs_left))) {
    if(msg->msg == CURLMSG_DONE) {
      printf("Transfer completed with status %d\n", msg->data.result);
    }
  }
} while(still_running);

// 清理 multi 前需先移除并清理各 easy handle
curl_multi_remove_handle(multi, curl1);
curl_multi_remove_handle(multi, curl2);
curl_easy_cleanup(curl1);
curl_easy_cleanup(curl2);
curl_multi_cleanup(multi);
```

`curl_multi_poll()` 底层用 `poll()`（或 `select()`、`epoll()`，取决于平台和编译选项），能在单个线程里高效处理大量并发连接。这是 libcurl 比“每个连接一个线程”更省资源的原因。

### Share Interface（共享接口）

Share 接口让多个 curl handle 共享数据，避免重复初始化，降低开销。

**适用场景**：

- 多线程应用中共享 DNS 缓存（减少 DNS 查询次数）
- 复用 SSL session（减少 TLS 握手开销）
- 多 handle 共享 cookie jar

```c
CURLSH *share = curl_share_init();

// 共享 DNS 缓存和 cookie
curl_share_setopt(share, CURLSHOPT_SHARE, CURL_LOCK_DATA_DNS);
curl_share_setopt(share, CURLSHOPT_SHARE, CURL_LOCK_DATA_COOKIE);

// 两个 easy handle 共享同一份缓存
CURL *curl1 = curl_easy_init();
CURL *curl2 = curl_easy_init();
curl_easy_setopt(curl1, CURLOPT_SHARE, share);
curl_easy_setopt(curl2, CURLOPT_SHARE, share);

// 先清理 easy handle，再清理 share
curl_easy_cleanup(curl1);
curl_easy_cleanup(curl2);
curl_share_cleanup(share);
```

多线程环境下用 share 接口，需要设置 `CURLSHOPT_LOCKFUNC` 和 `CURLSHOPT_UNLOCKFUNC` 提供锁机制，否则会有数据竞争。

---

## curl_url：为什么要自己做 URL 解析

从 curl 7.62.0 开始，项目引入了独立的 **curl_url** API，作为 URL 解析和操作的标准接口。它独立于传输逻辑之外，可以单独使用（不需要初始化 libcurl）。

### 为什么要自己做

URL 解析看起来简单，陷阱不少：

- 不同协议对 URL 各部分的规则不同（HTTP 的 `//` 前缀、mailto 没有 `//`、file 的路径规则）
- IPv6 地址用方括号包裹（`[::1]:8080`），解析时要特殊处理
- 端口号、认证信息（user:password）、query string 编码等边界情况繁多
- 系统不提供行为一致的 URL 解析函数——Windows 的解析接口与 POSIX 侧各不相同，curl 要跨平台行为一致，就得自己实现

自己实现 URL 解析，能换来三样东西：

1. **跨协议行为一致**：不管什么协议，URL 各部分的提取规则统一
2. **不依赖系统库**：避免不同 OS 上行为不一致
3. **便于安全审计**：URL 直接接触不可信输入，是安全高发区，自己实现可以针对性审计

### curl_url API 用法

```c
CURLU *u = curl_url();

// 解析一个 URL
curl_url_set(u, CURLUPART_URL,
             "https://user:pass@example.com:8080/path?query=1#frag", 0);

// 逐个提取组件
char *host = NULL;
char *port = NULL;
char *path = NULL;
curl_url_get(u, CURLUPART_HOST, &host, 0);
curl_url_get(u, CURLUPART_PORT, &port, 0);
curl_url_get(u, CURLUPART_PATH, &path, 0);
printf("host=%s, port=%s, path=%s\n", host, port, path);

// 修改 URL 的某个部分
curl_url_set(u, CURLUPART_SCHEME, "http", 0);
curl_url_set(u, CURLUPART_QUERY, "newquery=2", 0);

// 重新组装成字符串
char *url = NULL;
curl_url_get(u, CURLUPART_URL, &url, 0);
printf("Modified URL: %s\n", url);

curl_free(host);
curl_free(port);
curl_free(path);
curl_free(url);
curl_url_cleanup(u);
```

给定一个 URL 字符串，可以安全地提取各组件，也可以逐步构造一个 URL。格式不合法时 `curl_url_set()` 会返回错误码，不会静默成功。

命令行场景想直接调用这套解析能力，同源的 [trurl](https://github.com/curl/trurl) 工具把它暴露给了 shell——它内部复用的正是 libcurl 的 curl_url 实现。

---

## 协议支持：27 种协议是如何实现的

curl 支持 27 种协议，靠的是协议插件式架构：每个协议实现一组函数指针，注册到全局 handler 表，传输时按 URL scheme 查表分发。

### 协议注册机制

libcurl 内部维护一张协议 handler 表。每个协议实现以下函数指针（简化版）：

```c
struct Curl_handler {
  const char *scheme;              // 协议名，如 "http", "ftp"
  CURLcode (*setup)(struct Curl_easy *data);
  CURLcode (*connect_it)(struct Curl_easy *data, bool *done);
  CURLcode (*do_it)(struct Curl_easy *data, bool *done);
  CURLcode (*done)(struct Curl_easy *data, CURLcode, bool);
  Curl_send *send;                 // 发送数据
  Curl_recv *recv;                 // 接收数据
  /* ... 更多函数指针 ... */
};
```

真实源码里的字段比这多，`Curl_handler` 还包含 `readwrite`、`connection_check`、`disconnect` 等回调，用于传输中读写、连接状态检查和清理。这里保留发送 / 接收两个核心入口，便于理解分发逻辑。

接入一个新协议只需要：

1. 实现 `struct Curl_handler` 里的一组函数，放在 `lib/` 下对应协议的文件（如 `http.c`、`ftp.c`）里
2. 在 libcurl 的协议注册表中登记该 handler，按 scheme 关联
3. 在构建系统里启用对应的编译开关

不需要改动传输主循环。新协议的接入点明确，维护边界清晰。这是 curl 能持续增加协议而代码不失控的原因——每个协议自己负责自己的实现，主循环只管查表分发。

需要说明的是，27 种协议是 curl 源码支持的完整清单，某个具体构建未必全部启用——SMB/SMBS、GOPHERS 这类协议在部分平台或发行版的默认配置里可能没有编译进去。实际能力以 `curl -V` 输出为准。

### 代理与 HTTP 版本选择

curl 通过代理和 HTTP 版本开关控制请求路径。调试链路或锁定协议版本时常用：

```bash
# 使用 HTTP 代理
curl -x http://proxy:8080 https://example.com

# 使用 SOCKS5 代理
curl --socks5 socks5://proxy:1080 https://example.com

# 仅允许 HTTP/1.1，不使用 HTTP/2
curl --http1.1 https://example.com

# 强制使用 HTTP/2（如果服务器支持）
curl --http2 https://example.com
```

`--http2` / `--http3` 要求 curl 在编译时启用对应支持（HTTP/2 通常依赖 nghttp2，HTTP/3 依赖 quiche 或 ngtcp2），否则会直接报错。先 `curl -V` 确认当前构建支持哪些。

---

## 一次请求如何流过 libcurl

把前面的机制串起来看一次实际请求。下面这个最小程序用 easy 接口下载一个文件，它走完的路径基本覆盖了 libcurl 的核心调用链。

```c
#include <stdio.h>
#include <curl/curl.h>

static size_t write_cb(void *ptr, size_t size, size_t nmemb, void *userdata) {
  return fwrite(ptr, size, nmemb, (FILE *)userdata);
}

int main(void) {
  FILE *out = fopen("index.html", "wb");
  CURL *curl = curl_easy_init();
  if (curl) {
    curl_easy_setopt(curl, CURLOPT_URL, "https://example.com");
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_cb);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, out);
    CURLcode res = curl_easy_perform(curl);
    if (res != CURLE_OK)
      fprintf(stderr, "failed: %s\n", curl_easy_strerror(res));
    curl_easy_cleanup(curl);
  }
  fclose(out);
  return 0;
}
```

`curl_easy_perform()` 内部大致分五步：

1. **解析 URL**。`curl_easy_setopt(curl, CURLOPT_URL, ...)` 并不立刻联网，它把 URL 字符串交给 curl_url 引擎解析，拆出 scheme、host、port、path。解析失败（比如 `htp://` 拼错）会直接返回错误，不会发起连接。
2. **按 scheme 查表**。libcurl 用解析出的 scheme 在协议 handler 表里查找对应的 `Curl_handler`，拿到 http 对应的 `do_it`、`send`、`recv` 等函数指针。
3. **建立连接**。DNS 解析 → TCP 握手 → TLS 协商（HTTPS 时）。如果启用了 share 接口，DNS 结果和 SSL session 会先查共享缓存。
4. **执行传输**。调用 handler 里的发送 / 接收回调，把响应数据交给 `CURLOPT_WRITEFUNCTION`（上面示例里是写进文件）。重定向、断点续传这类逻辑也在这个阶段处理。
5. **收尾**。`done` 回调清理传输状态，连接放回连接池（保持 keep-alive），`curl_easy_perform()` 返回 `CURLcode`。

这个调用链里值得注意的一点：URL 解析发生在协议查表之前，所以 curl_url 对全部 27 种协议都适用——这正好回答了前面的问题，为什么 URL 解析要独立成一套组件而不是散在各协议里。

---

## SSL/TLS 支持

curl 支持多种 SSL 后端：OpenSSL、GnuTLS、mbedTLS、WolfSSL、BearSSL、rustls，以及 macOS 上的 Secure Transport、Windows 上的 Schannel。编译时选择后端（autotools 用 `--with-ssl` 等选项，CMake 构建用对应开关），同一个二进制通常静态链接一个后端，也可以通过动态库同时支持多个。当前启用的是哪一个，看 `curl -V` 中 TLS 一行的输出。

### 关键配置项

```bash
# 指定 CA 证书路径（调试自签名证书时有用）
curl --cacert /path/to/ca-bundle.crt https://example.com

# 跳过证书验证（仅用于测试，生产环境禁止）
curl -k https://invalid-cert.example.com

# 客户端证书认证
curl --cert client.pem --key client.key https://secure.example.com

# 查看服务器证书详情
curl -v https://example.com 2>&1 | grep -A 20 "SSL certificate"
```

```c
// libcurl 中配置 SSL 选项
curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 1L);  // 验证对等证书
curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 2L);  // 验证主机名
curl_easy_setopt(curl, CURLOPT_CAINFO, "/path/to/ca-bundle.crt");
```

`CURLOPT_SSL_VERIFYPEER` 设为 0 会接受任意证书，包括中间人攻击的证书，HTTPS 的加密保护形同虚设。生产代码永远不应该关掉证书验证。

---

## 适用场景、优势与边界

### curl 的优势

1. **无处不在**：Linux/macOS/Windows 均内置或极易安装，容器镜像里也几乎都有
2. **协议覆盖广**：一个工具覆盖 27 种协议，不需要为每种协议换工具
3. **生产验证**：二十多年、无数生产环境的使用，可靠性经过充分验证
4. **libcurl 可嵌入**：应用可以复用这套成熟的网络栈，不必自己实现协议
5. **漏洞响应成熟**：curl 有独立的安全团队和披露流程，高危 CVE 通常会在公开披露前给出修复版本

### curl 的边界

1. **不是浏览器**：不支持 JavaScript、CSS 渲染、DOM 操作，无法处理需要 JS 渲染的单页应用
2. **非交互式**：无法填表、点击按钮，模拟表单提交得自己构造 POST 请求
3. **没有内置重试**：大文件传输失败需要自己实现重试（用脚本循环或 `curl --retry`）
4. **单连接原始性能**：单连接吞吐不如专攻 HTTP 的专用客户端，但并发靠 multi 接口多路复用弥补

### 与替代工具对比

| 工具 | 适用场景 | 与 curl 的区别 |
|------|----------|---------------|
| wget / wget2 | 递归下载、网站镜像 | wget 更适合整站下载；curl 更适合 API 调试和嵌入式场景 |
| httpie / xh | 交互式 HTTP 客户端 | 命令行体验更好，输出自动格式化；但不适合脚本，也不提供库 |
| fetch / fetchurl | BSD 原生工具 | 仅支持 HTTP/HTTPS，功能少，跨平台性差 |
| Postman / Insomnia | API 测试（带 GUI） | 适合手工测试；curl 适合脚本化和自动化 |

---

## 常见问题排查

| 现象 | 可能原因 | 处理方式 |
|------|----------|----------|
| `curl: (6) Could not resolve host` | DNS 解析失败 | 检查网络；试 `nslookup example.com`；检查 `/etc/resolv.conf` |
| `curl: (60) SSL certificate problem` | CA 证书过期或自签名 | 用 `--cacert` 指定正确 CA；测试环境可临时用 `-k` |
| 请求卡住不动 | 服务器不响应或防火墙丢包 | 用 `-v` 看卡在哪一步；用 `--max-time 10` 设超时 |
| 返回 403 | 缺认证 header 或被 WAF 拦截 | 检查 `-H "Authorization: ..."`；对比浏览器请求的真实 header |
| 大文件下载中断 | 网络不稳定或服务器超时 | 用 `-C -` 断点续传；用 `--retry 3` 自动重试 |
| HTTPS 通过代理失败 | 代理不支持 HTTPS 隧道 | 确认代理支持 `CONNECT` 方法；SOCKS5 代理无需此步骤 |
| `curl_easy_perform()` 返回 `CURLE_OPERATION_TIMEDOUT` | 超时 | 检查 `CURLOPT_TIMEOUT` 和 `CURLOPT_CONNECTTIMEOUT` 的设置 |
| `curl: (35) SSL connect error` | TLS 握手失败（服务器不支持该版本、SNI 缺失或中间设备拦截） | 用 `-v` 看握手卡在哪一步；确认服务器的 TLS 版本，必要时用 `--tls-max` 限定 |

---

## 采用建议

curl 的命令行工具只是 libcurl 的前端。libcurl 作为底层库，让无数应用直接复用了 curl 二十多年积累的协议实现，不必各自重写传输逻辑。

上手顺序可以这样走：

1. **命令行调试**：直接用 `curl -v` 排查 HTTP 请求、证书、代理问题，零成本上手
2. **脚本化传输**：在 shell 脚本里用 curl 做定时下载、API 调用、健康检查
3. **嵌入 libcurl**：在 C/C++ 应用里链接 libcurl，从 easy 接口起步，需要并发再上 multi 接口
4. **多线程共享**：多线程场景下用 share 接口共享 DNS 和 SSL session，避免重复初始化
5. **独立 URL 解析**：只需要 URL 解析不需要传输时，单独用 curl_url，不引入完整传输栈

想深入源码，Daniel Stenberg 写的 [Everything curl](https://everything.curl.dev/) 是最完整的 curl 参考书，官方在线版免费阅读，重点看 “How curl works” 和 “libcurl internals” 两章。[libcurl API 参考](https://curl.se/libcurl/c/) 和 [curl 官方文档](https://curl.se/docs/) 适合按需查。

---

## 自测

1. 命令行 curl 和 libcurl 是什么关系？
   <details><summary>查看答案</summary>命令行 curl 是 libcurl 的前端消费者，把参数翻译成 libcurl API 调用；真正承载传输逻辑的是 libcurl 库。</details>

2. 一次只能处理一个传输、要并发换什么接口？多线程里共享 DNS 缓存用什么接口？
   <details><summary>查看答案</summary>单个传输用 easy 接口；并发多传输用 multi 接口（一个线程内管理多个 easy handle）；多线程共享数据用 share 接口。</details>

3. curl_url 是什么时候引入的？它解决的问题是什么？
   <details><summary>查看答案</summary>从 curl 7.62.0 开始引入，是独立的 URL 解析 API。解决不同协议 URL 规则不同、系统库跨平台行为不一致、以及安全审计需要统一入口的问题。</details>

4. 新协议接入 libcurl，要不要改传输主循环？
   <details><summary>查看答案</summary>不用。每个协议实现 `Curl_handler` 的一组函数指针并注册到 handler 表，主循环按 scheme 查表分发即可。</details>

5. `curl -k` 关闭了什么校验？生产环境为什么禁止？
   <details><summary>查看答案</summary>关闭对端证书验证（`CURLOPT_SSL_VERIFYPEER`）。关闭后 HTTPS 会接受任意证书，包括中间人攻击的证书，加密保护形同虚设，生产环境永远不应关闭。</details>

## 练习

1. 跑一次 `curl -v https://example.com`，把输出按“URL 解析 → DNS → TCP → TLS → HTTP 请求/响应”五段标注出来，对照本文的调用链。
2. 写一个 C 程序，用 easy 接口下载两个文件；再改成 multi 接口并发下载，对比两者的完成时间。
3. 用 `curl_url` API 解析 `https://user:pass@example.com:8080/path?query=1#frag`，分别取出 host、port、path，再把 scheme 改成 `http` 看结果变化。
4. 在脚本里用 `curl --retry 3 --retry-delay 2` 下载一个会间歇失败的 URL，观察重试日志，理解“没有内置重试”这条边界如何被弥补。

## 进阶路径

- **从命令行到源码**：读完 Everything curl 的 “How curl works”，再对照 libcurl 源码里 `http.c`、`urlapi.c` 的实现，看 handler 表和 curl_url 的实际代码。
- **从 easy 到 multi**：把单线程下载器改造成事件驱动并发下载器，理解 `curl_multi_poll` 如何用单个线程管理大量连接。
- **从客户端到协议**：用 `curl -v` 对比 HTTP/1.1 与 HTTP/2 的帧交互，再进一步看 QUIC/HTTP/3 的传输差异。
- **从使用到安全**：研究 curl 历年的 CVE 公告，看 URL 解析、TLS 校验相关的漏洞是如何被发现和修复的，理解安全披露流程。