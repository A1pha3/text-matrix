---
title: "Android逆向工程Skill：6.2K Stars的Claude Code智能体——从APK提取Retrofit API完整指南"
date: "2026-04-17T16:45:00+08:00"
slug: "android-reverse-engineering-skill-claude-code"
description: "6.2K Stars的Android逆向工程Claude Code Skill。反编译APK/XAPK/JAR/AAR，提取Retrofit/OkHttp API端点、硬编码URL、认证模式，支持jadx/Vineflower双引擎对比，可追踪Activity→ViewModel→HTTP调用完整链路。"
draft: false
categories: ["技术笔记"]
tags: ["Android", "逆向工程", "APK", "反编译", "Claude Code", "Retrofit", "OkHttp", "安全研究"]
---

# Android 逆向工程 Skill：把 APK 反编译和 API 提取压缩成一句话

> **快速信息卡** |
> Stars: 6,2K+ |
> Forks: 701+ |
> License: Apache 2.0 |
> Language: Shell |

Android 逆向工程的真正瓶颈在工具链割裂。jadx 反编译、dex2jar 转码、grep 抓接口、人工拼调用链——每一步单独看都简单，串起来却容易出错：命令记不住、引擎切换丢上下文、混淆代码让 grep 失效。`android-reverse-engineering-skill`（GitHub 6.2K+ Stars）把这条链路封装成 Claude Code Skill，用一句 `/decompile app.apk` 触发依赖检查、反编译、结构分析、API 提取、调用链追踪五个阶段。

本文拆解这条链路上的两套并行反编译引擎（jadx 与 Vineflower）边界、API 提取的特征识别逻辑，以及一个从 `LoginActivity` 追到 HTTP 请求的完整任务流案例。

## 学习目标

阅读本文后，你应该能够：

1. **理解逆向工程脚本化的价值**：说清楚传统手工逆向的三个断点，以及 Skill 如何解决这些问题
2. **区分 jadx 与 Vineflower 的能力边界**：知道什么场景下用哪个引擎，什么时候值得开双引擎对比
3. **掌握 API 提取的特征识别模式**：能用 grep 命令从反编译代码中提取 Retrofit 接口、OkHttp 调用和硬编码 URL
4. **追踪完整的调用链**：从 Activity 出发，穿过 ViewModel、Repository，定位到具体的 HTTP 请求端点
5. **合规使用逆向技术**：明确法律边界，知道什么场景允许逆向，什么场景禁止

## 本文覆盖

1. DEX→Java 反编译的两条路径与引擎选择
2. jadx 与 Vineflower 的能力边界与适用场景
3. Claude Code Skill 的五阶段工作流
4. Retrofit/OkHttp/硬编码 URL 的提取特征
5. 从 UI 点击到 HTTP 请求的调用链追踪
6. 逆向工程的法律合规边界与采用建议

## 目录

- [一、为什么需要把逆向工程脚本化](#一为什么需要把逆向工程脚本化)
  - [1.1 应用场景](#11-应用场景)
  - [1.2 传统手工流程的断点](#12-传统手工流程的断点)
  - [1.3 Skill 的解法把流程压成一句命令](#13-skill-的解法把流程压成一句命令)
- [二、核心功能五阶段工作流](#二核心功能五阶段工作流)
  - [2.1 整体架构](#21-整体架构)
  - [2.2 支持的文件格式](#22-支持的文件格式)
- [三、工具链详解 jadx 与 Vineflower 的边界](#三工具链详解 jadx 与 Vineflower 的边界)
  - [3.1 jadx 默认反编译器](#31-jadx 默认反编译器)
  - [3.2 Vineflower 复杂结构的备选](#32-vineflower 复杂结构的备选)
  - [3.3 双引擎对比什么时候值得多花一倍时间](#33-双引擎对比什么时候值得多花一倍时间)
  - [3.4 辅助工具](#34-辅助工具)
- [四、API 提取模式](#四 api 提取模式)
  - [4.1 Retrofit 接口识别](#41-retrofit-接口识别)
  - [4.2 OkHttp 调用识别](#42-okhttp-调用识别)
  - [4.3 硬编码 URL 和密钥](#43-硬编码 url 和密钥)
  - [4.4 API 文档模板](#44-api-文档模板)
- [五、调用链追踪](#五调用链追踪)
  - [5.1 追踪原理](#51-追踪原理)
  - [5.2 追踪命令](#52-追踪命令)
  - [5.3 代码结构分析](#53-代码结构分析)
- [六、安装与配置](#六安装与配置)
  - [6.1 环境要求](#61-环境要求)
  - [6.2 Claude Code 安装](#62-claude-code-安装)
  - [6.3 手动脚本使用](#63-手动脚本使用)
- [七、实战案例提取某 App 的登录 API](#七实战案例提取某 app 的登录 api)
- [八、法律合规](#八法律合规)
- [九、故障排除](#九故障排除)
- [十、采用建议](#十采用建议)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [相关资源](#相关资源)

## 一、为什么需要把逆向工程脚本化

### 1.1 应用场景

| 场景 | 说明 |
|------|------|
| 安全研究 | 分析应用安全性，发现潜在漏洞 |
| 渗透测试 | 验证授权安全测试的深度 |
| API 文档复现 | 还原没有文档的内部 API |
| 兼容性分析 | 理解第三方 SDK 的调用行为 |
| 恶意软件分析 | 应急响应中的样本剖析 |
| 互操作性研究 | EU 指令 2009/24/EC、DMCA §1201(f) 允许的逆向 |

### 1.2 传统手工流程的断点

手工逆向的标准流程是：下载 APK → `unzip` 解压 → `apktool` 反编译资源 → `dex2jar` 转换 DEX→JAR → `jadx` 或 Fernflower 反编译 JAR→Java → 手动 `grep` API 端点 → 人工追踪调用链。

断点出现在三个位置：

- **命令记忆成本**：每个工具都有自己的参数体系，跨引擎切换时容易遗漏依赖（如 Vineflower 处理 APK 前必须先跑 dex2jar）。
- **混淆对抗**：ProGuard/R8 混淆后，类名变成 `a.b.c`，`grep 'LoginActivity'` 直接失效，需要先做反混淆映射。
- **调用链断裂**：从 `Activity` 到 HTTP 请求要穿过 ViewModel、Repository、ApiService 多层，手工追踪容易在某一层断掉。

### 1.3 Skill 的解法：把流程压成一句命令

```bash
/decompile app.apk
```

这一句背后触发五个阶段：依赖检查（jadx/Vineflower 是否就绪）→ 反编译（单引擎或双引擎对比）→ 结构分析（包名/Activity/ViewModel）→ API 提取（Retrofit/OkHttp/URL）→ 调用链追踪（Activity→HTTP）。每个阶段的输出落盘成文件，下一阶段可读取，避免上下文丢失。

## 二、核心功能：五阶段工作流

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│ Android Reverse Engineering Skill                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Phase 1: 依赖检查                                           │
│ ├── jadx 是否安装？                                         │
│ ├── Vineflower 是否安装？                                   │
│ └── Java JDK 17+ 是否可用？                                 │
│                                                             │
│ Phase 2: 反编译                                             │
│ ├── jadx（默认）→ DEX/DEX→Java                              │
│ ├── Vineflower → DEX→JAR→Java（需 dex2jar 转换）           │
│ └── 双引擎对比 → 输出两个版本供比较                         │
│                                                             │
│ Phase 3: 结构分析                                           │
│ ├── AndroidManifest.xml 解析                                │
│ ├── 包名/Activity/Service/Receiver 提取                     │
│ └── 架构模式识别（MVC/MVVM/Clean）                          │
│                                                             │
│ Phase 4: API 提取                                           │
│ ├── Retrofit 接口识别                                       │
│ ├── OkHttp 调用识别                                         │
│ ├── 硬编码 URL 提取                                         │
│ └── 认证头/Token 识别                                       │
│                                                             │
│ Phase 5: 调用链追踪                                         │
│ ├── Activity → ViewModel → Repository → API                 │
│ └── 完整调用路径输出                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

五个阶段是串行依赖关系：Phase 2 必须等 Phase 1 通过，Phase 4 的 API 提取依赖 Phase 3 的结构分析定位到 `api/` 包，Phase 5 的调用链追踪依赖 Phase 4 的端点位置反推入口。这种串行设计让每一步的输出可独立检查，出问题时能定位到具体阶段。

### 2.2 支持的文件格式

| 格式 | 说明 | jadx 直接支持 | Vineflower 支持 |
|------|------|-------------|---------------|
| **APK** | Android 应用包 | ✅ | ✅（需 dex2jar） |
| **XAPK** | APKs 应用包（含多 APK） | ✅（自动拆分） | ❌ |
| **JAR** | Java 库 | ✅ | ✅ |
| **AAR** | Android 库 | ✅ | ✅（需 dex2jar） |
| **DEX** | Dalvik 字节码 | ✅ | ✅（需 dex2jar） |

XAPK 是个特例：它本质是多个 APK 的压缩包，jadx 能自动拆分，Vineflower 走 dex2jar 路径时需要先手动解包。处理 XAPK 时优先选 jadx。

## 三、工具链详解：jadx 与 Vineflower 的边界

### 3.1 jadx：默认反编译器

jadx 直接处理 APK/DEX，跳过 JAR 中间层，这是它成为默认引擎的原因。社区活跃、持续更新，支持反混淆（deobfuscation）。

常用选项：

```bash
# 基本用法
jadx -d output app.apk

# 指定线程数（加速）
jadx -j 8 -d output app.apk

# 增加堆内存（大 APK）
jadx -Xmx4g -d output app.apk

# 显示"坏代码"（混淆严重时的残缺代码）
jadx --show-bad-code -d output app.apk

# 开启反混淆
jadx --deobf -d output app.apk

# 导出资源（XML/AndroidManifest）
jadx -r -d output app.apk
```

`--show-bad-code` 在混淆严重的场景下有用：jadx 会把无法完整还原的方法用 `// Error` 标注后输出，避免整个类被跳过。`--deobf` 会生成 `deobf` 映射表，把 `a.b.c` 还原成可读名称（基于字符串启发式，不保证与原始类名一致）。

### 3.2 Vineflower：复杂结构的备选

Vineflower 是 Fernflower 的社区继任者（Fernflower 原由 JetBrains 维护，已停止更新，Vineflower 社区 fork 后继续开发）。它在 lambda、泛型、Stream API 等复杂 Java 结构上的还原能力比 jadx 更接近原始源码。

代价是工作流多一步：Vineflower 不直接读 DEX，必须先用 dex2jar 把 DEX 转成 JAR。

```bash
# Step 1: DEX → JAR
d2j-dex2jar -f -o output.jar app.apk

# Step 2: JAR → Java
java -jar ~/vineflower/vineflower.jar output.jar decompiled/

# 参数调优
java -Xmx4g -jar vineflower.jar -mpm=60 output.jar decompiled/
# -mpm=60：每个方法超时 60 秒
```

`-mpm`（minutes per method）控制单方法反编译超时。混淆严重时某些方法会让反编译器卡住，这个参数避免整个流程被一个方法拖死。

### 3.3 双引擎对比：什么时候值得多花一倍时间

```bash
# 使用双引擎并对比输出
bash decompile.sh --engine both --deobf app.apk

# 输出：
# output/jadx/        ← jadx 版本
# output/vineflower/  ← Vineflower 版本
```

双引擎默认不开启，因为耗时翻倍。值得用双引擎的三种情况：

- 单引擎输出大量 `// Error`，反编译质量不可用
- 需要交叉验证关键方法的还原正确性（如涉及金额计算的逻辑）
- 混淆严重，单引擎的反混淆映射可能出错

### 3.4 辅助工具

**apktool** —— 资源解码：

```bash
apktool d app.apk -o resources/
# 输出：AndroidManifest.xml、布局 XML、字符串资源等
```

jadx 也能导出资源，但 apktool 对资源引用关系的还原更完整（如 `@string/xxx` 的跨文件引用）。

**adb** —— 从设备拉取 APK：

```bash
# 查找包名
adb shell pm list packages | grep <keyword>

# 获取 APK 路径
adb shell pm path com.example.app

# 拉取 APK
adb pull /data/app/com.example.app-xxxx/base.apk ./app.apk
```

设备拉取的场景：应用商店分发的 APK 可能与官方下载的不同（签名、分包差异），从目标设备直接拉取能拿到真实运行版本。

## 四、API 提取模式

### 4.1 Retrofit 接口识别

Retrofit 是 Android 最常见的 HTTP 客户端，接口以注解方式声明。识别 Retrofit 接口的特征是 HTTP 方法注解（`@GET`/`@POST`/`@PUT` 等）出现在 interface 上：

```java
// 特征代码
public interface ApiService {
    @GET("users/{id}")
    Call<User> getUser(@Path("id") String userId);

    @POST("auth/login")
    @Headers({"Content-Type: application/json"})
    Call<LoginResponse> login(@Body LoginRequest request);
}
```

提取命令：

```bash
# HTTP 方法注解
grep -rn '@GET\|@POST\|@PUT\|@DELETE\|@PATCH\|@HEAD' sources/

# 参数注解
grep -rn '@Query\|@QueryMap\|@Path\|@Body\|@Field\|@Header' sources/

# Base URL 配置
grep -rn 'baseUrl\|\.baseUrl(' sources/
```

为什么先抓 HTTP 方法注解：Retrofit 接口的方法一定带方法注解，这是最稳定的特征。参数注解（`@Query`/`@Body` 等）帮助还原请求结构，Base URL 配置定位服务端域名。

### 4.2 OkHttp 调用识别

OkHttp 直接构建请求，没有注解，识别特征是 `Request.Builder` 链式调用：

```java
// 特征代码
Request request = new Request.Builder()
    .url("https://api.example.com/v1/users")
    .addHeader("Authorization", "Bearer " + token)
    .build();

OkHttpClient client = new OkHttpClient();
client.newCall(request).enqueue(callback);
```

提取命令：

```bash
# Request 构建
grep -rn 'Request\.Builder\|Request.Builder\|\.url(\|\.post(' sources/

# Interceptors（常含认证逻辑）
grep -rn 'Interceptor\|addInterceptor\|addNetworkInterceptor' sources/

# 执行方式
grep -rn '\.execute()\|\.enqueue(' sources/
```

Interceptor 是 OkHttp 的认证逻辑集中地：很多应用把 Token 注入、签名计算统一放在 Interceptor 里，避免每个请求重复写。抓 Interceptor 往往能一次性拿到全局认证策略。

### 4.3 硬编码 URL 和密钥

```bash
# HTTP/HTTPS URL
grep -rn '"https\?://[^"]*"' sources/

# API 密钥/Token
grep -rni 'api[_-]\?key\|api[_-]\?secret\|auth[_-]\?token\|bearer' sources/

# Base URL 常量
grep -rni 'BASE_URL\|API_URL\|SERVER_URL\|ENDPOINT' sources/
```

硬编码 URL 的价值在于发现 Retrofit/OkHttp 之外的请求：第三方 SDK（如友盟、Bugly）的上报地址、WebView 内嵌页面、配置拉取地址。这些通常不出现在 Retrofit 接口里。

### 4.4 API 文档模板

对每个发现的端点，按以下模板记录：

```markdown
`POST /v1/auth/login`

- **Source**: `com.example.app.api.AuthService` (AuthService.java:42)
- **Base URL**: `https://api.example.com`
- **Full URL**: `https://api.example.com/v1/auth/login`
- **Path 参数**: 无
- **Query 参数**: 无
- **Headers**:
  - `Content-Type: application/json`
- **Request Body**: `LoginRequest { email: String, password: String }`
- **Response**: `ApiResponse<TokenResponse>`
- **调用来源**: `LoginActivity.onLoginClicked()` → `AuthViewModel.login()`
```

`Source` 字段是回溯的关键：它把抽象的端点定位到具体文件和行号，后续追踪调用链时从这一行反向查找调用方。

## 五、调用链追踪

### 5.1 追踪原理

Android 应用的典型调用链是分层架构：

```
用户交互 (点击按钮)
    │
    ▼
Activity / Fragment
    │ onClick()
    ▼
ViewModel
    │ login(email, password)
    ▼
Repository
    │ authApi.login(request)
    ▼
ApiService (Retrofit Interface)
    │ @POST("auth/login")
    ▼
OkHttpClient
    │ 发起 HTTP 请求
    ▼
网络响应
```

这条链路的每一层都有可识别的特征：Activity 看 `extends AppCompatActivity`，ViewModel 看 `extends ViewModel`，Repository 看类名包含 `Repository`，ApiService 看 Retrofit 注解。追踪的本质是从 HTTP 请求端点出发，反向查找每一层的调用方。

### 5.2 追踪命令

```bash
# 追踪从 LoginActivity 开始的完整调用链
/decompile app.apk
# 然后使用 Skill 的对话式追踪
"Follow the call flow from LoginActivity"
```

Skill 的追踪逻辑：先定位 `LoginActivity`，找它的字段引用（通常是 ViewModel），再找 ViewModel 的方法调用（通常是 Repository），层层下钻直到 ApiService 的注解方法。

### 5.3 代码结构分析

```bash
# 列出所有 Activity
grep -rn 'extends Activity\|extends AppCompatActivity' sources/ | head -20

# 列出所有 ViewModel
grep -rn 'extends ViewModel\|class.*ViewModel' sources/ | head -20

# 列出所有 Repository
grep -rn 'class.*Repository' sources/ | head -20

# 查找 LiveData/StateFlow 观察
grep -rn 'observe\|LiveData\|StateFlow\|MutableLiveData' sources/
```

这些命令帮助建立应用的结构地图。混淆场景下类名不可读，但 `extends ViewModel` 这类继承关系不会被混淆掉（ProGuard 默认保留继承链），因此结构分析在混淆下仍然有效。

## 六、安装与配置

### 6.1 环境要求

**必需**：

- Java JDK 17+
- jadx CLI

**推荐**：

- Vineflower（复杂 Java 结构的反编译质量更好）
- dex2jar（使用 Vineflower 处理 APK 时必需）
- apktool（资源解码）
- adb（从设备拉取 APK）

### 6.2 Claude Code 安装

```bash
# 从 GitHub 安装（推荐）
/plugin marketplace add SimoneAvogadro/android-reverse-engineering-skill
/plugin install android-reverse-engineering@android-reverse-engineering-skill

# 从本地克隆安装
git clone https://github.com/SimoneAvogadro/android-reverse-engineering-skill.git
/plugin marketplace add /path/to/android-reverse-engineering-skill
/plugin install android-reverse-engineering@android-reverse-engineering-skill
```

### 6.3 手动脚本使用

```bash
# 检查依赖
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/check-deps.sh

# 安装缺失依赖（自动检测 OS 和包管理器）
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/install-dep.sh jadx
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/install-dep.sh vineflower

# 反编译 APK（jadx 默认）
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/decompile.sh app.apk

# 反编译 XAPK（自动处理多 APK）
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/decompile.sh app.xapk

# 使用 Vineflower
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/decompile.sh --engine fernflower library.aar

# 双引擎对比
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/decompile.sh --engine both --deobf app.apk

# 查找 API 调用
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/find-api-calls.sh output/sources/
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/find-api-calls.sh output/sources/ --retrofit
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/find-api-calls.sh output/sources/ --urls
```

`--engine fernflower` 这个参数名是历史遗留：脚本早期只支持 Fernflower，Vineflower 接替后保留了原参数名以兼容旧调用。

## 七、实战案例：提取某 App 的登录 API

### 7.1 场景描述

目标：提取某 Android 应用的登录 API，用于授权范围内的安全测试。

### 7.2 执行流程

```bash
# Step 1: 一句话反编译
/decompile target-app.apk

# Step 2: 查找 Retrofit 接口
/decompile target-app.apk
"Find all Retrofit interfaces and their endpoints"

# Step 3: 追踪登录调用链
"Follow the call flow from LoginActivity to the HTTP request"

# Step 4: 提取认证信息
"Find all authentication headers and token patterns"
```

### 7.3 输出示例

```
=== API Extraction Report ===

Base URL: https://api.target-app.com/v2

=== Endpoints ===

[POST] /auth/login
  Source: com.target.app.data.api.AuthApi (AuthApi.java:23)
  Headers: Content-Type: application/json, X-App-Version: 1.0.0
  Body: { email: String, password: String, device_id: String }
  Response: { access_token: String, refresh_token: String, expires_in: Int }

[GET] /users/me
  Source: com.target.app.data.api.UserApi (UserApi.java:15)
  Headers: Authorization: Bearer <token>
  Response: { id: String, email: String, name: String, avatar: String }

=== Call Chain ===

LoginActivity.onLoginClicked()
  → LoginViewModel.login(email, password)
  → AuthRepository.login(request)
  → AuthApi.login(request)
  → OkHttpClient.newCall(request).enqueue(callback)

=== Security Notes ===

- Device ID hardcoded in LoginRequest
- No certificate pinning detected
- Refresh token stored in SharedPreferences (encrypted)
- API version exposed in headers
```

这份报告暴露出四个安全问题：

- `device_id` 硬编码在请求体里，意味着设备绑定逻辑在前端，可被伪造。
- 未检测到证书锁定（certificate pinning），中间人攻击面存在。
- Refresh token 加密存储在 SharedPreferences，但 SharedPreferences 的加密密钥本身可能被逆向提取。
- `X-App-Version` 暴露在 Header 里，攻击者可据此推断服务端兼容的客户端版本范围。

## 八、法律合规

### 8.1 合法使用场景

- ✅ 安全研究和授权渗透测试
- ✅ DMCA §1201(f) 允许的互操作性分析
- ✅ EU Directive 2009/24/EC 允许的逆向工程
- ✅ 恶意软件分析和应急响应
- ✅ CTF 比赛和教育用途

### 8.2 禁止使用场景

- ❌ 未经授权分析他人应用
- ❌ 绕过付费墙或 DRM
- ❌ 窃取知识产权或商业机密
- ❌ 开发侵权应用

### 8.3 合规建议

1. 仅分析你拥有或被授权分析的应用
2. 不传播反编译后的源代码
3. 发现的漏洞遵循 responsible disclosure
4. 遵守应用的服务条款

法律边界因司法管辖区而异。DMCA §1201(f) 和 EU Directive 2009/24/EC 是互操作性例外的常见引用依据，但具体适用需要结合当地法律判断。

## 九、故障排除

| 问题 | 解决方案 |
|------|----------|
| `jadx: command not found` | 确保 jadx 的 `bin/` 目录在 `$PATH` 中 |
| `Could not find or load main class` | Java 缺失或版本不对，运行 `java -version` 检查 |
| 大 APK 内存不足 | 增加堆：`jadx -Xmx4g -d output app.apk` |
| 反编译代码多 `// Error` 注释 | 使用 `--show-bad-code` 或 `--deobf` 选项 |
| Vineflower 方法超时 | 使用 `-mpm=60` 设置 60 秒超时 |
| Vineflower JAR 找不到 | 设置 `FERNFLOWER_JAR_PATH` 环境变量 |
| dex2jar 失败（ZipException） | APK 可能非标准 ZIP 结构，尝试 jadx |

`FERNFLOWER_JAR_PATH` 这个环境变量名也是历史遗留，实际指向 Vineflower JAR。

## 十、采用建议

按以下顺序引入这个 Skill：

1. **先跑通 jadx 单引擎**：在熟悉的 APK 上验证依赖检查、反编译、API 提取三个阶段，确认输出符合预期。
2. **再试调用链追踪**：选一个已知结构的 App（如开源应用编译的 APK），验证追踪结果与实际代码一致。
3. **按需引入 Vineflower**：只在 jadx 输出 `// Error` 过多或关键方法还原不准时切换。
4. **双引擎对比留作疑难场景**：常规分析不必开启，耗时翻倍且对比需要人工判断。

适用边界：这个 Skill 解决的是"流程编排"问题，对"混淆对抗"无能为力。重度混淆的 App（如金融类应用）仍需要人工介入做反混淆映射、字符串解密、native 层分析。Skill 的价值在于把可自动化的部分压成一句命令，把人工时间留给真正需要判断的环节。

## 自测题

### 基础题

1. **jadx 和 Vineflower 的核心区别是什么？什么场景下应该选哪个？**
2. **传统手工逆向的三个断点是什么？这个 Skill 如何解决这些问题？**
3. **Retrofit 接口的特征识别模式是什么？应该用什么样的 grep 命令提取？**
4. **从 Activity 到 HTTP 请求的调用链通常经过哪些层？如何用 grep 追踪？**
5. **什么场景下值得开启双引擎对比？开启后输出在哪里？**

### 进阶题

1. **混淆后的代码如何让 grep 失效？有哪些对抗混淆的策略？**
2. **OkHttp 的 Interceptor 为什么是提取认证逻辑的关键位置？**
3. **XAPK 格式和 APK 格式有什么区别？为什么 jadx 能直接处理 XAPK？**
4. **在法律层面，DMCA §1201(f) 和 EU Directive 2009/24/EC 分别允许什么场景的逆向？**
5. **如果反编译输出大量 `// Error`，应该如何排查是 jadx 的问题还是 APK 本身的问题？**

### 参考答案要点

1. jadx 直接处理 DEX，Vineflower 需要先转 JAR；Vineflower 在 lambda/泛型还原更好
2. 命令记忆成本、混淆对抗、调用链断裂；Skill 用五阶段串行工作流 + 文件落盘解决
3. HTTP 方法注解（`@GET`/`@POST` 等）；`grep -rn '@GET\|@POST' sources/`
4. Activity → ViewModel → Repository → ApiService → OkHttpClient；grep 继承关系和字段引用
5. 单引擎输出大量 Error、需要交叉验证关键方法、混淆严重可能映射出错；输出在 `output/jadx/` 和 `output/vineflower/`

## 进阶路径

### 阶段一：熟练使用单引擎（1-2 周）

- [ ] 在自己熟悉的 APK 上跑通 jadx 单引擎全流程
- [ ] 验证依赖检查、反编译、结构分析、API 提取四个阶段的输出
- [ ] 手动追踪一个已知 App 的调用链，对比 Skill 输出

### 阶段二：掌握双引擎对比（2-3 周）

- [ ] 在一个混淆严重的 APK 上对比 jadx 和 Vineflower 的输出质量
- [ ] 理解 `--deobf` 和反混淆映射表的局限性
- [ ] 学会用 `-mpm` 参数避免 Vineflower 卡死

### 阶段三：深入逆向工程（1-2 个月）

- [ ] 学习 ProGuard/R8 混淆原理，理解为什么继承关系不会被混淆
- [ ] 掌握 native 层分析（IDA Pro、Frida），理解 Skill 覆盖不到的场景
- [ ] 阅读 jadx 源码，理解 DEX→Java 的反编译原理

### 阶段四：贡献和扩展（持续）

- [ ] 为 Skill 贡献新的 API 提取模式（如 GraphQL、gRPC）
- [ ] 扩展支持的文件格式（如 `.apkm`、`.xapk` 变体）
- [ ] 集成动态分析能力（Frida hook、adb 注入）

### 进阶资源

- **jadx 源码**：https://github.com/skylot/jadx - 理解反编译器原理
- **Android 逆向实战**：《Android 软件安全权威指南》- 系统学习逆向工程
- **Frida 官方文档**：https://frida.re/docs/home/ - 动态分析工具
- **OWASP Mobile Top 10**：https://owasp.org/www-project-mobile-top-10/ - 移动安全测试指南

## 相关资源

- **GitHub 仓库**：https://github.com/SimoneAvogadro/android-reverse-engineering-skill
- **jadx**：https://github.com/skylot/jadx
- **Vineflower**：https://github.com/Vineflower/vineflower
- **dex2jar**：https://github.com/pxb1988/dex2jar
- **apktool**：https://apktool.org/
