---
title: "Android逆向工程Skill：2.5K Stars的Claude Code智能体——从APK提取Retrofit API完整指南"
date: 2026-04-17T16:45:00+08:00
slug: "android-reverse-engineering-skill-claude-code"
description: "2,460 Stars的Android逆向工程Claude Code Skill。反编译APK/XAPK/JAR/AAR，提取Retrofit/OkHttp API端点、硬编码URL、认证模式，支持jadx/Vineflower双引擎对比，可追踪Activity→ViewModel→HTTP调用完整链路。"
draft: false
categories: ["技术笔记"]
tags: ["Android", "逆向工程", "APK", "反编译", "Claude Code", "Retrofit", "OkHttp", "安全研究"]
---

# Android逆向工程Skill：2.5K Stars的Claude Code智能体

> **目标读者**：移动安全工程师、渗透测试工程师、Android开发者、安全研究者
> **前置知识**：Android基础、HTTP协议、命令行操作
> **技术栈**：Java JDK 17+ / jadx / Vineflower / dex2jar
> **难度定位**：⭐⭐⭐⭐ 专家设计

---

## §1 学习目标

完成本篇文章后，你将能够：

1. **理解Android逆向工程的基本原理**：DEX→Java反编译流程
2. **掌握jadx和Vineflower两大引擎**：各自优势和适用场景
3. **能够使用Claude Code Skill**：一句话完成APK反编译和API提取
4. **理解API提取模式**：Retrofit/OkHttp/Volley的特征识别
5. **掌握调用链追踪技术**：从UI到网络请求的完整追踪
6. **了解法律合规边界**：确保逆向工程行为合法

---

## §2 背景与动机：为何需要Android逆向工程

### 2.1 应用场景

| 场景 | 说明 |
|------|------|
| **安全研究** | 分析应用安全性，发现潜在漏洞 |
| **渗透测试** | 验证授权安全测试的深度 |
| **API文档** | 复现没有文档的API接口 |
| **兼容性分析** | 理解第三方SDK的调用行为 |
| **恶意软件分析** | Malware分析应急响应 |
| **互操作性研究** | EU指令1201(f)/DMCA豁免分析 |

### 2.2 传统逆向工程的痛点

```bash
# 传统方式：手动一步步操作
1. 下载APK
2. 解压（unzip）
3. 使用apktool反编译资源
4. 使用dex2jar转换DEX→JAR
5. 使用jadx或Fernflower反编译JAR→Java
6. 手动搜索API端点
7. 手动追踪调用链

# 问题：
# - 命令繁多，难以记忆
# - 多引擎切换复杂
# - 调用链追踪困难
# - 无法批量处理
```

### 2.3 Claude Code Skill的解决

**一句话完成全流程**：

```bash
/decompile app.apk
# 自动执行：
# 1. 依赖检查（jadx/Vineflower）
# 2. 反编译（jadx或双引擎对比）
# 3. 结构分析（包名/Activity/ViewModel）
# 4. API提取（Retrofit/OkHttp/URL）
# 5. 调用链追踪（Activity→HTTP）
```

---

## §3 核心功能：五阶段工作流

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│            Android Reverse Engineering Skill                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Phase 1: 依赖检查                                           │
│  ├── jadx 是否安装？                                         │
│  ├── Vineflower 是否安装？                                   │
│  └── Java JDK 17+ 是否可用？                                  │
│                                                              │
│  Phase 2: 反编译                                             │
│  ├── jadx（默认）→ DEX/DEX→Java                             │
│  ├── Vineflower → DEX→JAR→Java（需dex2jar转换）             │
│  └── 双引擎对比 → 输出两个版本供比较                         │
│                                                              │
│  Phase 3: 结构分析                                           │
│  ├── AndroidManifest.xml 解析                               │
│  ├── 包名/Activity/Service/Receiver 提取                    │
│  └── 架构模式识别（MVC/MVVM/Clean）                          │
│                                                              │
│  Phase 4: API提取                                           │
│  ├── Retrofit 接口识别                                        │
│  ├── OkHttp 调用识别                                         │
│  ├── 硬编码URL提取                                          │
│  └── 认证头/Token识别                                        │
│                                                              │
│  Phase 5: 调用链追踪                                         │
│  ├── Activity → ViewModel → Repository → API                │
│  └── 完整调用路径输出                                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 支持的文件格式

| 格式 | 说明 | jadx直接支持 | Fernflower支持 |
|------|------|-------------|---------------|
| **APK** | Android应用包 | ✅ | ✅（需dex2jar） |
| **XAPK** | APKs应用包（含多APK） | ✅（自动拆分） | ❌ |
| **JAR** | Java库 | ✅ | ✅ |
| **AAR** | Android库 | ✅ | ✅（需dex2jar） |
| **DEX** | Dalvik字节码 | ✅ | ✅（需dex2jar） |

---

## §4 工具链详解

### 4.1 jadx - 首选反编译器

**优势**：
- 直接处理APK/DEX，无需中间转换
- 社区活跃，持续更新
- 支持代码混淆（deobfuscation）

**常用选项**：

```bash
# 基本用法
jadx -d output app.apk

# 指定线程数（加速）
jadx -j 8 -d output app.apk

# 增加堆内存（大APK）
jadx -Xmx4g -d output app.apk

# 显示"坏代码"（混淆严重时的残缺代码）
jadx --show-bad-code -d output app.apk

# 开启反混淆
jadx --deobf -d output app.apk

# 导出资源（XML/AndroidManifest）
jadx -r -d output app.apk
```

### 4.2 Vineflower - 更强的反编译器

**优势**：
- JetBrains自研，分析能力更强
- 对复杂Java结构（lambda/泛型）支持更好
- 生成的代码更接近原始源码

**工作流程**（需要dex2jar）：

```bash
# Step 1: DEX → JAR
d2j-dex2jar -f -o output.jar app.apk

# Step 2: JAR → Java
java -jar ~/vineflower/vineflower.jar output.jar decompiled/

# 参数调优
java -Xmx4g -jar vineflower.jar -mpm=60 output.jar decompiled/
# -mpm=60：每个方法超时60秒
```

### 4.3 双引擎对比

```bash
# 使用双引擎并对比输出
bash decompile.sh --engine both --deobf app.apk

# 输出：
# output/jadx/    ← jadx版本
# output/vineflower/  ← Vineflower版本
```

**何时用双引擎**：
- 单引擎反编译失败
- 需要对比反编译质量
- 混淆严重需交叉验证

### 4.4 辅助工具

**apktool** - 资源解码：
```bash
apktool d app.apk -o resources/
# 输出：AndroidManifest.xml、布局XML、字符串资源等
```

**adb** - 从设备拉取APK：
```bash
# 查找包名
adb shell pm list packages | grep <keyword>

# 获取APK路径
adb shell pm path com.example.app

# 拉取APK
adb pull /data/app/com.example.app-xxxx/base.apk ./app.apk
```

---

## §5 API提取模式

### 5.1 Retrofit接口识别

Retrofit是最常见的Android HTTP客户端，接口以注解方式声明：

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

**提取命令**：

```bash
# HTTP方法注解
grep -rn '@GET\|@POST\|@PUT\|@DELETE\|@PATCH\|@HEAD' sources/

# 参数注解
grep -rn '@Query\|@QueryMap\|@Path\|@Body\|@Field\|@Header' sources/

# Base URL配置
grep -rn 'baseUrl\|\.baseUrl(' sources/
```

### 5.2 OkHttp调用识别

OkHttp通常直接构建请求：

```java
// 特征代码
Request request = new Request.Builder()
    .url("https://api.example.com/v1/users")
    .addHeader("Authorization", "Bearer " + token)
    .build();

OkHttpClient client = new OkHttpClient();
client.newCall(request).enqueue(callback);
```

**提取命令**：

```bash
# Request构建
grep -rn 'Request\.Builder\|Request.Builder\|\.url(\|\.post(' sources/

# Interceptors（常含认证逻辑）
grep -rn 'Interceptor\|addInterceptor\|addNetworkInterceptor' sources/

# 执行方式
grep -rn '\.execute()\|\.enqueue(' sources/
```

### 5.3 硬编码URL和密钥

```bash
# HTTP/HTTPS URL
grep -rn '"https\?://[^"]*"' sources/

# API密钥/Token
grep -rni 'api[_-]\?key\|api[_-]\?secret\|auth[_-]\?token\|bearer' sources/

# Base URL常量
grep -rni 'BASE_URL\|API_URL\|SERVER_URL\|ENDPOINT' sources/
```

### 5.4 API文档模板

对每个发现的端点，记录：

```markdown
### `POST /v1/auth/login`

- **Source**: `com.example.app.api.AuthService` (AuthService.java:42)
- **Base URL**: `https://api.example.com`
- **Full URL**: `https://api.example.com/v1/auth/login`
- **Path参数**: 无
- **Query参数**: 无
- **Headers**:
  - `Content-Type: application/json`
- **Request Body**: `LoginRequest { email: String, password: String }`
- **Response**: `ApiResponse<TokenResponse>`
- **调用来源**: `LoginActivity.onLoginClicked()` → `AuthViewModel.login()`
```

---

## §6 调用链追踪

### 6.1 追踪原理

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
    │ 发起HTTP请求
    ▼
网络响应
```

### 6.2 追踪命令

```bash
# 追踪从LoginActivity开始的完整调用链
/decompile app.apk
# 然后使用Skill的对话式追踪
"Follow the call flow from LoginActivity"
```

### 6.3 代码结构分析

```bash
# 列出所有Activity
grep -rn 'extends Activity\|extends AppCompatActivity' sources/ | head -20

# 列出所有ViewModel
grep -rn 'extends ViewModel\|class.*ViewModel' sources/ | head -20

# 列出所有Repository
grep -rn 'class.*Repository' sources/ | head -20

# 查找LiveData/StateFlow观察
grep -rn 'observe\|LiveData\|StateFlow\|MutableLiveData' sources/
```

---

## §7 安装与配置

### 7.1 环境要求

**必需**：
- Java JDK 17+
- jadx CLI

**推荐**：
- Vineflower（更好的反编译质量）
- dex2jar（使用Fernflower处理APK时必需）
- apktool（资源解码）
- adb（从设备拉取APK）

### 7.2 Claude Code安装

```bash
# 从GitHub安装（推荐）
/plugin marketplace add SimoneAvogadro/android-reverse-engineering-skill
/plugin install android-reverse-engineering@android-reverse-engineering-skill

# 从本地克隆安装
git clone https://github.com/SimoneAvogadro/android-reverse-engineering-skill.git
/plugin marketplace add /path/to/android-reverse-engineering-skill
/plugin install android-reverse-engineering@android-reverse-engineering-skill
```

### 7.3 手动脚本使用

```bash
# 检查依赖
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/check-deps.sh

# 安装缺失依赖（自动检测OS和包管理器）
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/install-dep.sh jadx
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/install-dep.sh vineflower

# 反编译APK（jadx默认）
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/decompile.sh app.apk

# 反编译XAPK（自动处理多APK）
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/decompile.sh app.xapk

# 使用Fernflower
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/decompile.sh --engine fernflower library.aar

# 双引擎对比
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/decompile.sh --engine both --deobf app.apk

# 查找API调用
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/find-api-calls.sh output/sources/
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/find-api-calls.sh output/sources/ --retrofit
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/find-api-calls.sh output/sources/ --urls
```

---

## §8 实际案例：提取某App的登录API

### 8.1 场景描述

目标：提取某Android应用的登录API，用于安全测试。

### 8.2 执行流程

```bash
# Step 1: 一句话反编译
/decompile target-app.apk

# Step 2: 查找Retrofit接口
/decompile target-app.apk
"Find all Retrofit interfaces and their endpoints"

# Step 3: 追踪登录调用链
"Follow the call flow from LoginActivity to the HTTP request"

# Step 4: 提取认证信息
"Find all authentication headers and token patterns"
```

### 8.3 输出示例

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

---

## §9 法律合规

### 9.1 合法使用场景

✅ **安全研究和授权渗透测试**
✅ **DMCA §1201(f) 允许的互操作性分析**
✅ **EU Directive 2009/24/EC 允许的逆向工程**
✅ **恶意软件分析和应急响应**
✅ **CTF比赛和教育用途**

### 9.2 禁止使用场景

❌ **未经授权分析他人应用**
❌ **绕过付费墙或DRM**
❌ **窃取知识产权或商业机密**
❌ **开发侵权应用**

### 9.3 合规建议

1. **仅分析你拥有或被授权分析的应用**
2. **不传播反编译后的源代码**
3. **发现的漏洞遵循responsible disclosure**
4. **遵守应用的服务条款**

---

## §10 故障排除

| 问题 | 解决方案 |
|------|----------|
| `jadx: command not found` | 确保jadx的`bin/`目录在`$PATH`中 |
| `Could not find or load main class` | Java缺失或版本不对，运行`java -version`检查 |
| 大APK内存不足 | 增加堆：`jadx -Xmx4g -d output app.apk` |
| 反编译代码多`// Error`注释 | 使用`--show-bad-code`或`--deobf`选项 |
| Fernflower方法超时 | 使用`-mpm=60`设置60秒超时 |
| Fernflower JAR找不到 | 设置`FERNFLOWER_JAR_PATH`环境变量 |
| dex2jar失败(ZipException) | APK可能非标准ZIP结构，尝试jadx |

---

## 相关资源

- **GitHub仓库**：https://github.com/SimoneAvogadro/android-reverse-engineering-skill
- **jadx**：https://github.com/skylot/jadx
- **Vineflower**：https://github.com/Vineflower/vineflower
- **dex2jar**：https://github.com/pxb1988/dex2jar
- **apktool**：https://apktool.org/
