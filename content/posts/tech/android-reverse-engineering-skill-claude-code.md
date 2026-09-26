---
title: "Android逆向工程Skill：7.9K Stars的Claude Code插件——从APK提取HTTP API完整指南"
date: "2026-04-17T16:45:00+08:00"
lastmod: "2026-09-26T10:00:00+08:00"
slug: "android-reverse-engineering-skill-claude-code"
github_repo: "SimoneAvogadro/android-reverse-engineering-skill"
source_key: "gh:SimoneAvogadro/android-reverse-engineering-skill"
description: "7.9K Stars的Android逆向工程Claude Code Skill。反编译APK/XAPK/JAR/AAR，提取Retrofit/OkHttp/Ktor/Apollo API端点、硬编码URL与认证模式，从Kotlin元数据恢复R8混淆前的类名，支持jadx/Vineflower双引擎对比与调用链追踪。"
draft: false
categories: ["技术笔记"]
tags: ["Android", "Claude Code", "安全研究"]
---

# Android 逆向工程 Skill：把 APK 反编译和 API 提取压缩成一句话

> **快速信息卡** |
> Stars: 7.9K+ |
> Forks: 897+ |
> License: Apache 2.0 |
> Language: Shell |
> 版本锚点：plugin v1.5.0（2026-09-26 核对）

Android 逆向工程的瓶颈不在单点工具，而在工具链割裂：jadx 反编译、dex2jar 转码、grep 抓接口、人工拼调用链，每一步单独看都简单，串起来却处处出错——命令记不住、引擎切换丢上下文、混淆代码让 grep 失效。`android-reverse-engineering-skill`（GitHub 7.9K+ Stars）把这条链路封装成 Claude Code Skill：一句 `/decompile app.apk` 完成依赖检查、反编译、结构分析，之后用自然语言继续触发调用链追踪与 API 提取。完整工作流从指纹甄别到文档产出共七步（Phase 0–5），本文以 v1.5.0 为口径拆解。

本文覆盖这条链路上的几个关键判断：反编译前先用指纹脚本判断这个 APK 值不值得反编译，jadx 与 Vineflower 两套引擎各自的边界，从 R8 混淆后的字节码里恢复原始 Kotlin 类名，以及 Retrofit、OkHttp、Ktor、Apollo 多套 HTTP 栈的提取特征。

## 学习目标

读完后，你应该能独立回答：

1. **一个 APK 值不值得反编译**：用 Phase 0 指纹脚本识别 Flutter、React Native 等框架应用，避免在反编译 Java 上白费时间
2. **jadx 与 Vineflower 各自擅长什么**：什么场景用哪个引擎，什么时候值得开双引擎对比
3. **从混淆代码里恢复可读类名**：理解 Kotlin 元数据恢复为什么比 `--deobf` 更可靠，能跑通恢复与查询脚本
4. **提取多套 HTTP 栈的 API**：Retrofit、OkHttp 之外，还能处理 Ktor、Apollo（GraphQL）、Volley 和硬编码 URL，混淆场景下会用 `--paths` 兜底
5. **追踪完整的调用链**：从 Activity 出发，穿过 ViewModel、Repository，定位到具体的 HTTP 请求端点
6. **合规使用逆向技术**：明确法律边界，知道什么场景允许逆向，什么场景禁止

## 本文覆盖

1. DEX→Java 反编译的两条路径与引擎选择
2. Phase 0–5 完整工作流，包括反编译前的指纹甄别
3. jadx 与 Vineflower 的能力边界与适用场景
4. Kotlin 元数据恢复：绕过 R8 混淆拿回原始类名
5. Retrofit/OkHttp/Ktor/Apollo/硬编码 URL 的提取特征与两层文档结构
6. 从 UI 点击到 HTTP 请求的调用链追踪
7. 逆向工程的法律合规边界与采用建议

## 目录

- [一、为什么需要把逆向工程脚本化](#一为什么需要把逆向工程脚本化)
  - [1.1 应用场景](#11-应用场景)
  - [1.2 传统手工流程的断点](#12-传统手工流程的断点)
  - [1.3 Skill 的解法把流程压成一句命令](#13-skill-的解法把流程压成一句命令)
- [二、核心工作流 Phase 0–5](#二核心工作流-phase-05)
  - [2.1 整体架构](#21-整体架构)
  - [2.2 Phase 0 指纹甄别先判断值不值得反编译](#22-phase-0-指纹甄别先判断值不值得反编译)
  - [2.3 支持的文件格式](#23-支持的文件格式)
- [三、工具链详解 jadx 与 Vineflower 的边界](#三工具链详解-jadx-与-vineflower-的边界)
  - [3.1 jadx 默认反编译器](#31-jadx-默认反编译器)
  - [3.2 Vineflower 复杂结构的备选](#32-vineflower-复杂结构的备选)
  - [3.3 双引擎对比什么时候值得多花一倍时间](#33-双引擎对比什么时候值得多花一倍时间)
  - [3.4 辅助工具](#34-辅助工具)
- [四、混淆对抗从 Kotlin 元数据恢复类名](#四混淆对抗从-kotlin-元数据恢复类名)
- [五、API 提取模式](#五api-提取模式)
  - [5.1 Retrofit 接口识别](#51-retrofit-接口识别)
  - [5.2 OkHttp 调用识别](#52-okhttp-调用识别)
  - [5.3 Ktor 与 Apollo Kotlin 应用的主流栈](#53-ktor-与-apollo-kotlin-应用的主流栈)
  - [5.4 硬编码 URL 和密钥](#54-硬编码-url-和密钥)
  - [5.5 路径字面量兜底混淆场景的最后手段](#55-路径字面量兜底混淆场景的最后手段)
  - [5.6 两层文档结构](#56-两层文档结构)
- [六、调用链追踪](#六调用链追踪)
  - [6.1 追踪原理](#61-追踪原理)
  - [6.2 追踪命令](#62-追踪命令)
  - [6.3 代码结构分析](#63-代码结构分析)
  - [6.4 混淆代码的导航策略](#64-混淆代码的导航策略)
- [七、安装与配置](#七安装与配置)
  - [7.1 环境要求](#71-环境要求)
  - [7.2 Claude Code 安装](#72-claude-code-安装)
  - [7.3 手动脚本使用](#73-手动脚本使用)
- [八、实战案例提取某 App 的登录 API](#八实战案例提取某-app-的登录-api)
- [九、法律合规](#九法律合规)
- [十、故障排除](#十故障排除)
- [十一、采用建议](#十一采用建议)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [相关资源](#相关资源)
- [参考来源与口径说明](#参考来源与口径说明)

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

断点出现在四个位置：

- **命令记忆成本**：每个工具都有自己的参数体系，跨引擎切换时容易遗漏依赖（如 Vineflower 处理 APK 前必须先跑 dex2jar）。
- **框架错判**：Flutter、React Native、Cordova、Xamarin 应用的业务逻辑根本不在 Java 层，对它们做 DEX 反编译基本是白费时间——但 APK 外观上看不出来。
- **混淆对抗**：ProGuard/R8 混淆后，类名变成 `a.b.c`，`grep 'LoginActivity'` 直接失效，需要先做反混淆映射。
- **调用链断裂**：从 `Activity` 到 HTTP 请求要穿过 ViewModel、Repository、ApiService 多层，手工追踪容易在某一层断掉。

### 1.3 Skill 的解法：把流程压成一句命令

```bash
/decompile app.apk
```

这句命令实际触发三步：依赖检查（Java/jadx 是否就绪，缺了自动装）→ 反编译（单引擎或双引擎对比）→ 结构分析（Manifest、包结构、入口 Activity、架构模式），最后给出下一步建议。调用链追踪和 API 提取是命令跑完之后，用自然语言继续触发的。

如果不用斜杠命令而是直接说"反编译这个 APK"或"提取这个应用的 API 端点"，Skill 会走完整工作流——在依赖检查之前先加一步指纹甄别（Phase 0），判断这个 APK 是原生 Java/Kotlin 应用还是 Flutter/RN 壳，再决定要不要往下走。

## 二、核心工作流：Phase 0–5

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│ Android Reverse Engineering Skill                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Phase 0: 指纹甄别（推荐先行）                                │
│ ├── 框架判断：Flutter/RN/Cordova/Xamarin/原生 Kotlin        │
│ ├── HTTP 栈探测：Retrofit/OkHttp/Ktor/Apollo/Volley         │
│ ├── 混淆级别估计与第三方 SDK 识别                            │
│ └── 结论：原生应用继续，框架应用换工具                       │
│                                                             │
│ Phase 1: 依赖检查与安装                                     │
│ ├── Java JDK 17+、jadx（必需）                              │
│ └── Vineflower、dex2jar（推荐，可自动安装）                  │
│                                                             │
│ Phase 2: 反编译                                             │
│ ├── jadx（默认）→ DEX→Java，含资源                          │
│ ├── Vineflower → DEX→JAR→Java（dex2jar 中转）              │
│ └── 双引擎对比 → jadx/ 与 fernflower/ 两个目录              │
│                                                             │
│ Phase 3: 结构分析                                           │
│ ├── AndroidManifest.xml 入口与组件                          │
│ ├── 包结构普查，定位 api/、network/ 等包                    │
│ ├── BuildConfig.java 常量提取（几乎不混淆）                  │
│ └── 架构模式识别（MVP/MVVM/Clean）                          │
│                                                             │
│ Phase 3.5: Kotlin 类名恢复（仅混淆的 Kotlin 应用）           │
│ └── @DebugMetadata/@Metadata → 混淆名到原始名映射            │
│                                                             │
│ Phase 4: 调用链追踪                                         │
│ └── Activity → ViewModel → Repository → API                │
│                                                             │
│ Phase 5: API 提取与文档化                                   │
│ ├── find-api-calls.sh 全栈扫描                              │
│ └── Tier 1 全量清单 + Tier 2 高价值端点明细                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

七个阶段串行依赖：Phase 0 的结论决定要不要反编译；Phase 4 的调用链追踪依赖 Phase 3 定位到的结构；Phase 5 的 API 提取用脚本全量扫描后，结合 Phase 4 的调用关系整理成文档。注意顺序——先追踪调用链，再整理 API 文档，这样每个端点都能带上它的调用来源。每一步的输出落盘成文件，出问题时能定位到具体阶段。

### 2.2 Phase 0 指纹甄别：先判断值不值得反编译

这是整个工作流里最省钱的一步。反编译之前花几秒跑一次：

```bash
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/fingerprint.sh app.apk
```

一屏输出里最关键的结论是**框架判断**：应用是 Flutter、React Native、Cordova、Xamarin 还是原生 Kotlin。判断依据是文件标记（比如 Flutter 的 `libapp.so`、RN 的 `index.android.bundle`），即使类名被混淆也不影响。SKILL.md 里说得很直白：对这四类框架应用反编译 Java 基本没用，真正的逻辑在别处——Flutter 应用该去看 `libapp.so`（脚本会建议 `blutter` 或 `strings`），而不是 jadx。

除框架外，指纹还包括：HTTP 栈探测（对 DEX 做字符串扫描，类名混淆了也有效）、DI 与序列化框架信号（Hilt、Dagger、Koin、kotlinx.serialization、Moshi、Gson）、基于短包名占比的混淆级别估计、值得注意的第三方 SDK（AppsFlyer、Datadog、Sentry、Firebase、支付与客服 SDK），以及 base APK 与所有 split APK 合并后的 native 库清单——XAPK 的 split 包经常把 `.so` 文件放在 `config.<abi>.apk` 而不是 `base.apk` 里。

### 2.3 支持的文件格式

| 格式 | 说明 | 处理方式 |
|------|------|----------|
| **APK** | Android 应用包 | jadx 直接处理；Vineflower 需 dex2jar 中转 |
| **XAPK** | 多 APK 打包（APKPure 等商店格式） | 脚本自动解包，逐个 APK 反编译 |
| **JAR** | Java 库 | 双引擎都直接处理 |
| **AAR** | Android 库 | jadx 直接处理；Vineflower 需 dex2jar 中转 |

三点说明：

- **XAPK 的拆分是脚本做的，不是 jadx 的能力**。`decompile.sh` 遇到 `.xapk` 先解压，找出里面所有 APK（base + split），逐个反编译到独立子目录，manifest 复制为 `xapk-manifest.json` 供参考，OBB 数据文件只列出不反编译。所以双引擎都能处理 XAPK。
- **脚本入口只接受这四种扩展名**。单独的 `.dex` 文件不在其中——要处理 DEX，直接用 `jadx -d output classes.dex`（jadx 本身支持），或把它交给 dex2jar。
- **split/bundled APK 自动检测**。有些 APK 本身是壳：外层 APK 的 resources 目录里嵌着 `base.apk` 和 `split_config.*.apk`。jadx 反编译这种壳只会得到十来个 Java 文件。脚本检测到这种情况（Java 文件 ≤10 且内嵌 APK 存在）会自动反编译 `base.apk` 到 `<output>/base/` 子目录，非配置类的 split APK 也逐个处理，ABI/语言/密度等 config split 跳过。主代码在 `<output>/base/sources/`。

## 三、工具链详解：jadx 与 Vineflower 的边界

### 3.1 jadx：默认反编译器

jadx 直接处理 APK/DEX，跳过 JAR 中间层，这是它成为默认引擎的原因。社区活跃、持续更新，支持反混淆（deobfuscation）。

常用选项：

```bash
# 基本用法（默认就会导出资源到 output/resources/）
jadx -d output app.apk

# 指定线程数（加速）
jadx -j 8 -d output app.apk

# 增加堆内存（大 APK）
jadx -Xmx4g -d output app.apk

# 显示"坏代码"（混淆严重时的残缺代码）
jadx --show-bad-code -d output app.apk

# 开启反混淆
jadx --deobf -d output app.apk

# 只反编译代码，跳过资源解码（更快）
jadx --no-res -d output app.apk

# 只解码资源，跳过代码反编译
jadx --no-src -d output app.apk
```

两个容易混淆的点：

- `--show-bad-code` 控制无法完整还原的方法怎么输出：不带它，jadx 在出错位置放一条注释跳过方法体；带上它，残缺代码也会输出。`decompile.sh` 调用 jadx 时固定带上了这个选项，所以走脚本时无需手动加。
- `--deobf` 生成的可读名是合成名（`p001a`、`C0123Foo` 这类），用于消歧，不是原始类名。要拿回开发者真正写的名字，看第四节。另外，如果手里有 ProGuard 的 mapping.txt（有时随构建产物分发），可以用 `--deobf-map mapping.txt` 直接按原始映射还原。

### 3.2 Vineflower：复杂结构的备选

Fernflower 是 JetBrains 的分析式反编译器，作为独立工具已不再发版（现在内置于 IntelliJ IDEA）。Vineflower 是活跃维护的社区 fork，在 GitHub 和 Maven Central 发布，对 records、sealed classes、模式匹配、lambda 和 switch 表达式的还原比上游更准，CLI 接口与 Fernflower 完全一致，可当作 drop-in 替换。

代价是工作流多一步：Vineflower 不直接读 DEX，必须先用 dex2jar 把 DEX 转成 JAR。

```bash
# Step 1: DEX → JAR
d2j-dex2jar -f -o output.jar app.apk

# Step 2: JAR → Java
java -jar ~/vineflower/vineflower.jar output.jar decompiled/

# 参数调优
java -Xmx4g -jar vineflower.jar -dgs=1 -mpm=60 output.jar decompiled/
# -dgs=1：反编译泛型签名（推荐）
# -mpm=60：单个方法最长处理 60 秒
```

`-mpm` 控制单方法反编译的最长处理时间（秒）。混淆严重时某些方法会让反编译器卡住，这个参数避免整个流程被一个方法拖死。`decompile.sh` 走 Vineflower 时固定带 `-dgs=1 -mpm=60`，开启 `--deobf` 时追加 `-ren=1`（重命名混淆标识符）。Vineflower 进程还有一层总超时兜底：`FERNFLOWER_TIMEOUT_SECONDS` 环境变量控制，默认 900 秒。

### 3.3 双引擎对比：什么时候值得多花一倍时间

```bash
# 使用双引擎并对比输出
bash decompile.sh --engine both --deobf app.apk

# 输出：
# output/jadx/        ← jadx 版本
# output/fernflower/  ← Vineflower 版本
```

双引擎默认不开启，因为耗时翻倍。跑完后脚本会给一份对比摘要：两边各反编译出多少 Java 文件、jadx 输出里带警告的文件数，结论靠人工逐类比较——SKILL.md 的建议是把有 jadx 警告的类拿到 Vineflower 输出里对照着看。

值得用双引擎的三种情况：

- 单引擎输出大量错误注释，反编译质量不可用
- 需要交叉验证关键方法的还原正确性（如涉及金额计算的逻辑）
- 混淆严重，单引擎的反混淆映射可能出错

SKILL.md 还给了一张引擎选择速查表，比"三种情况"更细：APK 首选 jadx（快、带资源）、JAR/AAR 库分析首选 Vineflower（Java 输出质量高）、lambda/泛型/Stream 密集的代码选 Vineflower、大 APK 快速概览用 `jadx --no-res`。

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

## 四、混淆对抗：从 Kotlin 元数据恢复类名

这是 v1.5 最值钱的一项能力。现代 Android 应用几乎都是 Kotlin 写的，发布前过一道 R8。R8 会重命名 JVM 符号——类名、方法名、字段名全部变成 `a`、`b`、`c`——但它**剥不掉 Kotlin 元数据字符串**：Kotlin 运行时的反射、协程、data class 特性在运行时依赖原始全限定名，所以这些字符串必须留在字节码里。泄漏点有两个注解：

- `@DebugMetadata`——几乎每个协程 `SuspendLambda`（也就是几乎每个 `suspend` 函数）都带，`c =` 字段写着原始类的全限定名；带 `$` 后缀（`AccountRepositoryImpl$fetch$1`），截到第一个 `$` 就是声明它的外层类；
- `@Metadata` 的 `d2` 数组——每个 Kotlin 类都有，按 JVM 类型描述符格式（`Lcom/example/Foo;`）列出内部类引用，其中第一个非标准库描述符通常就是该文件的 primary class。

Skill 用两个脚本开采这些字符串：

```bash
# 1. 从反编译源码构建映射：混淆名 → 原始名
bash scripts/recover-kotlin-names.sh output/sources/ output/names/
#    → output/names/mapping.tsv、mapping.json、by_package/

# 2. 查询映射：按真实名搜、按混淆名解、列包、带注解 grep
bash scripts/lookup-name.sh output/names/ LoginRepository
bash scripts/lookup-name.sh output/names/ -o a.b.c
bash scripts/lookup-name.sh output/names/ -p com.example.feature
bash scripts/lookup-name.sh output/names/ --grep 'login' output/sources/
```

`--grep` 模式最实用：对反编译源码做普通 grep，但每个命中行尾会附上所属类的真实名（`// com.example.data.LoginRepositoryImpl`），混淆代码的阅读体验立刻不一样。

恢复率要按口径说：真实世界的混淆 Kotlin 应用上，脚本大约恢复 30–50% 的类——但其中包含你真正想读的那部分：`*Repository`/`*Impl`、`*ViewModel`、`*UseCase`/`*Interactor` 几乎 100% 恢复，普通 data class DTO 约 80%。纯 Java 类没有 `@Metadata`，不在覆盖范围。

对照一下前面提到的 `jadx --deobf`：它只是给混淆符号编合成名，输出仍然是 `p001a` 这种占位符。两者是互补关系——`--deobf` 管没有元数据来源的字段和方法名，元数据恢复管类名。

边界也要交代清楚：方法名和字段名不在恢复范围（元数据只保类级全限定名和少量签名）；`@JvmInline value class` 和编译进 `*Kt.class` 合成类的顶层函数偶尔会挂错文件名——把结果当强提示，不当铁证。

## 五、API 提取模式

### 5.1 Retrofit 接口识别

Retrofit 仍是 Android 最常见的 HTTP 客户端，接口以注解方式声明。识别特征是 HTTP 方法注解（`@GET`/`@POST`/`@PUT` 等）出现在 interface 上：

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
# HTTP 方法注解（脚本另含 @OPTIONS 与动态 @HTTP）
grep -rn '@GET\|@POST\|@PUT\|@DELETE\|@PATCH\|@HEAD' sources/

# 参数注解（全集还有 @FieldMap、@Part、@PartMap、@HeaderMap、@Url）
grep -rn '@Query\|@QueryMap\|@Path\|@Body\|@Field\|@Header' sources/

# Base URL 配置
grep -rn 'baseUrl\|\.baseUrl(' sources/
```

为什么先抓 HTTP 方法注解：Retrofit 接口的方法一定带方法注解，这是最稳定的特征。参数注解（`@Query`/`@Body` 等）帮助还原请求结构，Base URL 配置定位服务端域名。

### 5.2 OkHttp 调用识别

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

### 5.3 Ktor 与 Apollo：Kotlin 应用的主流栈

v1.5 之后，提取范围不再限于 Retrofit/OkHttp。现代 Android 应用是 Kotlin/KMP 的天下：Ktor 是 Kotlin Multiplatform 和现代 Kotlin 独占应用的主流 HTTP 客户端，GraphQL 走 Apollo，老应用里还有 Volley。

**Ktor 不用注解**。端点是传给 `client.get(...)`/`client.post(...)` 的普通字符串参数：

```java
// 反编译后的典型 Ktor 调用
client.get("api/v1/users/profile") {
    parameter("locale", "en-US");
}
```

```bash
# Ktor 调用
grep -rn '\b(client|httpClient|HttpClient)\.(get|post|put|delete|patch|head|request)' sources/

# Base URL 通常在 defaultRequest { url { host = "..." } } 里配置
grep -rn 'HttpRequestBuilder\|defaultRequest\|URLBuilder\|URLProtocol' sources/

# 认证插件（bearer + 自动刷新）
grep -rn '\bbearer\s*{\|BearerTokens\s*(\|loadTokens\s*{\|refreshTokens\s*{' sources/
```

**Apollo（GraphQL）**：

```bash
# 客户端与端点
grep -rn 'ApolloClient\|\.serverUrl(\|HttpNetworkTransport' sources/

# 操作（查询/变更/订阅）
grep -rn '\.query(\s*[A-Z]\|\.mutation(\s*[A-Z]\|\.subscription(\s*[A-Z]' sources/
```

Apollo 为每个操作生成一个类，类里带着完整的 GraphQL 文本（`OPERATION_DOCUMENT`）——找到这些类，文档就现成了。

**Volley**：

```bash
grep -rn 'StringRequest\|JsonObjectRequest\|JsonArrayRequest\|Volley\.newRequestQueue\|RequestQueue' sources/
```

这些都封装进了 `find-api-calls.sh`：不带参数跑一次全量扫描，先给一屏摘要——Retrofit/OkHttp/Ktor/Apollo/Volley 各命中多少、Hilt/Dagger 与 Koin 各多少、Bearer 与 HMAC 签名各多少——再按栈分节列出 `file:line:match`；`--retrofit`/`--ktor`/`--apollo`/`--volley`/`--okhttp`/`--urls`/`--auth`/`--paths` 可以单查一类。

### 5.4 硬编码 URL 和密钥

```bash
# HTTP/HTTPS URL
grep -rn '"https\?://[^"]*"' sources/

# API 密钥/Token
grep -rni 'api[_-]\?key\|api[_-]\?secret\|auth[_-]\?token\|bearer' sources/

# Base URL 常量
grep -rni 'BASE_URL\|API_URL\|SERVER_URL\|ENDPOINT' sources/
```

硬编码 URL 的价值在于发现 Retrofit/OkHttp 之外的请求：第三方 SDK（如友盟、Bugly）的上报地址、WebView 内嵌页面、配置拉取地址。这些通常不出现在 Retrofit 接口里。

直接 grep URL 的痛点是噪音：压缩字典字符串、第三方 SDK 域名会把结果淹没。`--urls` 模式做了三层过滤：先用严格正则要求主机名语法成立，再用 awk 决策表保留高信号形态（IPv4 字面量、三段以上域名、带端口或路径的主机、真实 TLD 的裸域名），最后按 `third_party_hosts.txt` 黑名单（Google/Firebase/统计 SDK 等八十余条模式）把结果分成"第一方候选"（按出现频次排序）和"第三方"两桶。输出末尾还带 HttpURLConnection 和 WebView URL 两节，覆盖不走 HTTP 库的老代码和 JS 桥。

`--auth` 模式把认证相关的一网打尽：API key/token 模式之外，还有请求签名方案（`HmacSHA256`、`SecretKeySpec`、`x-signature` 头等）和疑似硬编码密钥（`app_secret`、`signing_key` 这类赋值）。APK 里出现硬编码 HMAC 密钥本身就是一条值得写进报告的安全发现。

### 5.5 路径字面量兜底：混淆场景的最后手段

重度 R8 应用里，调用点经常被内联成 `aVar.a(dVar, "path")`，按客户端语法写的 grep 全部失效。但 R8 不会混淆字符串常量的内容——路径字符串原样留在字节码里。

`--paths` 模式直接抽取长得像 API 路径的字符串字面量：以 `/` 开头且至少两段，或以 `api`、`v1`、`auth`、`order` 这类 API 根词开头的相对路径，同时排除 MIME 类型和 `/proc` 这类误报。输出两份：去重后的端点清单（这是文档化的最好起点），以及每个路径的调用点位置。官方 references 里给的经验值：真实 Kotlin 应用上这一条命令通常能抽出 100–300 个去重端点路径。

### 5.6 两层文档结构

对发现的端点，SKILL.md 规定了两层文档结构——对上百个端点逐个写明细不现实，也没必要：

**Tier 1——全量清单，必做**。一张表覆盖每个端点，一行一个，查不出的列就写 `?`：

| Host | Method | Path | Auth | Source file |
|------|--------|------|------|-------------|
| `api.example.com` | GET | `/v1/users/profile` | Bearer | `com/example/api/UserApi.java` |
| `api.example.com` | POST | `/v1/auth/login` | none | `com/example/api/AuthApi.java` |

这张表回答"后端长什么样"，从 `--paths` 的输出整理，大应用也就五分钟。

**Tier 2——高价值端点明细，按需**。只给真正重要的端点写：整个认证流（登录、刷新、登出、OTP）、支付/下单端点、用户点名要查的、扫描中看着异常的（自定义签名、没见过的头）。默认不超过 10 个：

```markdown
### `POST /v1/auth/login`

- **Source**: `com.example.api.ApiService` (ApiService.java:42)
- **Base URL**: `https://api.example.com/v1`
- **Path 参数**: 无
- **Query 参数**: 无
- **Headers**:
  - `Content-Type: application/json`
- **Request Body**: `LoginRequest { email: String, password: String }`
- **Response**: `ApiResponse<TokenResponse>`
- **调用来源**: `LoginActivity.onLoginClicked()` → `AuthViewModel.login()`
```

`Source` 字段是回溯的关键：它把抽象的端点定位到具体文件和行号，后续追踪调用链时从这一行反向查找调用方。

## 六、调用链追踪

### 6.1 追踪原理

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

两个容易被忽略的中间站：**Application 类**的 `onCreate()` 通常初始化 HTTP 客户端、配置 Base URL 和 DI 框架，值得先读；**DI 绑定**决定了接口到实现的映射——Dagger/Hilt 找 `@Module`/`@Provides`/`@Binds`，Koin 找 `single { }`/`factory { }` 块，找到谁创建了实现，调用链才接得上。

### 6.2 追踪命令

```bash
# 追踪从 LoginActivity 开始的完整调用链
/decompile app.apk
# 然后使用 Skill 的对话式追踪
"Follow the call flow from LoginActivity"
```

Skill 的追踪逻辑：先定位 `LoginActivity`，找它的字段引用（通常是 ViewModel），再找 ViewModel 的方法调用（通常是 Repository），层层下钻直到 ApiService 的注解方法。README 列出的等效触发语还有 "Extract API endpoints from this app" 和 "Analyze this AAR library"；SKILL.md 的 frontmatter 里还注册了中文触发词（反编译APK、安卓逆向、提取API、追踪调用链等）。

### 6.3 代码结构分析

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

这些命令帮助建立应用的结构地图。还有一条官方特别强调的：把每个 `BuildConfig.java` 都读一遍——

```bash
find output/sources -name BuildConfig.java -exec grep -H '=' {} \;
```

Gradle 构建配置类几乎从不被混淆，却经常泄漏整个 APK 里信号最高的常量：Base URL、flavor 名、构建类型、第三方 API key、feature 开关。每个 Gradle 模块各生成一份，命中可能不止一处，全读。

### 6.4 混淆代码的导航策略

混淆改变的是类名、方法名、字段名，有几样东西动不了：

- **字符串字面量**——URL、key、错误消息原样保留
- **Android 框架类**——`Activity`、`Fragment`、`Intent` 必须保留原名
- **库的公共 API**——Retrofit 注解、OkHttp builder 保留原名
- **AndroidManifest 条目**——组件名必须是真实的

导航策略因此清晰：从字符串入手（URL、错误消息、已知常量），从 Manifest 里名字真实的 Activity 入手，跟着库调用走（`@GET` 注解在接口类名被混淆后依然可读），再用第四节的 Kotlin 元数据恢复把类名批量还原——官方 references 的原话是，这是混淆 Kotlin 应用上"唯一可靠"的还原开发者原始类名的方式，且成本几乎为零。第四节的 `lookup-name.sh --grep` 优先于裸 grep，命中行自带真实类名。

## 七、安装与配置

### 7.1 环境要求

**必需**：

- Java JDK 17+
- jadx CLI

**推荐**：

- Vineflower（复杂 Java 结构的反编译质量更好）
- dex2jar（使用 Vineflower 处理 APK/AAR 时必需）
- apktool（资源解码）
- adb（从设备拉取 APK）

### 7.2 Claude Code 安装

```bash
# 从 GitHub 安装（推荐）
/plugin marketplace add SimoneAvogadro/android-reverse-engineering-skill
/plugin install android-reverse-engineering@android-reverse-engineering-skill

# 从本地克隆安装
git clone https://github.com/SimoneAvogadro/android-reverse-engineering-skill.git
/plugin marketplace add /path/to/android-reverse-engineering-skill
/plugin install android-reverse-engineering@android-reverse-engineering-skill
```

安装后 Skill 在后续所有会话中可用。除 `/decompile` 斜杠命令外，自然语言短语（"Decompile this APK"、"Extract API endpoints from this app"）和中/英文关键词都能触发。

### 7.3 手动脚本使用

```bash
# 检查依赖
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/check-deps.sh

# 安装缺失依赖（自动检测 OS 和包管理器）
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/install-dep.sh jadx
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/install-dep.sh vineflower

# 指纹甄别（Phase 0，反编译前先跑）
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/fingerprint.sh app.apk

# 反编译 APK（jadx 默认）
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/decompile.sh app.apk

# 反编译 XAPK（自动解包，逐个 APK 处理）
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

两个命名说明：

- 引擎参数的三个合法值是 `jadx`、`fernflower`、`both`。没有 `vineflower` 这个值——Vineflower 与 Fernflower 共用同一套 CLI，脚本把它挂在 `fernflower` 名下，推荐装的 JAR 也是 Vineflower 的。
- `FERNFLOWER_JAR_PATH` 环境变量同理，接受 `fernflower.jar` 或 `vineflower.jar`；不设置时脚本会探测若干常见位置（`~/.local/share/vineflower/vineflower.jar` 等）。

`install-dep.sh` 支持六个包：java、jadx、vineflower、dex2jar、apktool、adb。行为上优先免 sudo 的用户级安装（下载到 `~/.local/share/`，符号链接到 `~/.local/bin/`），必要时才用系统包管理器加 sudo；sudo 不可用或用户拒绝时，打印确切的手动安装命令并以退出码 2 结束。

Windows 用户有另一套 PowerShell 脚本（`check-deps.ps1`、`install-dep.ps1`、`decompile.ps1`、`find-api-calls.ps1`），社区贡献、README 标注为实验性，问题提到本仓库而非贡献者的 fork。

## 八、实战案例：提取某 App 的登录 API

### 8.1 场景描述

目标：提取某 Android 应用的登录 API，用于授权范围内的安全测试。

### 8.2 执行流程

```bash
# Step 0: 指纹甄别——确认是原生应用，HTTP 栈显示 Retrofit
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/fingerprint.sh target-app.apk

# Step 1: 一句话反编译
/decompile target-app.apk

# Step 2: 全量扫描 API（先看摘要，再按需单查）
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/find-api-calls.sh target-app-decompiled/sources/

# Step 3: 追踪登录调用链
"Follow the call flow from LoginActivity to the HTTP request"

# Step 4: 提取认证信息
bash plugins/android-reverse-engineering/skills/android-reverse-engineering/scripts/find-api-calls.sh target-app-decompiled/sources/ --auth
```

### 8.3 脚本输出与文档产物

以下按演示场景整理，产物形态以仓库真实机制为准。

`find-api-calls.sh` 的原始输出是逐行的 `文件:行号:匹配内容`，按栈分节，开头有一屏摘要（本例中 Retrofit 与 OkHttp 有命中、Ktor/Apollo/Volley 为零）。它不直接产出人类可读的 API 文档——整理成 Tier 1 清单和 Tier 2 明细是 Skill（Claude）在 Phase 5 里做的：

```
Base URL: https://api.target-app.com/v2        ← 从 BuildConfig.java 的 BASE_URL 常量确认

=== Tier 1 清单（节选）===

Host                  Method  Path          Auth    Source file
api.target-app.com    POST    /auth/login   none    com/target/app/data/api/AuthApi.java
api.target-app.com    GET     /users/me     Bearer  com/target/app/data/api/UserApi.java

=== Tier 2 明细：POST /auth/login ===

Source: com.target.app.data.api.AuthApi (AuthApi.java:23)
Headers: Content-Type: application/json, X-App-Version: 1.0.0
Body: { email, password, device_id }
Response: { access_token, refresh_token, expires_in }

=== 调用链 ===

LoginActivity.onLoginClicked()
  → LoginViewModel.login(email, password)
  → AuthRepository.login(request)
  → AuthApi.login(request)         @POST("auth/login")
  → OkHttpClient.newCall(request).enqueue(callback)
```

从这份产物里能读出几个值得写进安全测试报告的信号：`device_id` 出现在请求体里，设备绑定逻辑在前端，可被伪造；`X-App-Version` 暴露在 Header 里，服务端兼容的客户端版本范围可被推断；refresh token 的存储方式要看 `SharedPreferences` 相关代码确认是否加密、密钥从哪来。至于证书锁定（certificate pinning）是否存在，需要检查 OkHttp 的 `CertificatePinner` 配置或网络层配置——这是分析者要补的人工步骤，脚本不会自动下这个结论。

这个案例的完整流程是一条铁律的体现：脚本负责穷举和定位（哪一行有 `@POST`、哪个类引用了它），判断和文档化留给人或模型。两层分工，各自的输出都可核查。

## 九、法律合规

### 9.1 合法使用场景

- ✅ 安全研究和授权渗透测试
- ✅ DMCA §1201(f) 允许的互操作性分析
- ✅ EU Directive 2009/24/EC 允许的逆向工程
- ✅ 恶意软件分析和应急响应
- ✅ CTF 比赛和教育用途

### 9.2 禁止使用场景

- ❌ 未经授权分析他人应用
- ❌ 绕过付费墙或 DRM
- ❌ 窃取知识产权或商业机密
- ❌ 开发侵权应用

### 9.3 合规建议

1. 仅分析你拥有或被授权分析的应用
2. 不传播反编译后的源代码
3. 发现的漏洞遵循 responsible disclosure
4. 遵守应用的服务条款

法律边界因司法管辖区而异。DMCA §1201(f) 和 EU Directive 2009/24/EC 是互操作性例外的常见引用依据，但具体适用需要结合当地法律判断。仓库 README 的 Disclaimer 也写明：工具使用者对合规性负全责，作者对滥用不承担责任。

## 十、故障排除

| 问题 | 解决方案 |
|------|----------|
| `jadx: command not found` | 确保 jadx 的 `bin/` 目录在 `$PATH` 中 |
| `Could not find or load main class` | Java 缺失或版本不对，运行 `java -version` 检查 |
| 大 APK 内存不足 | 增加堆：`jadx -Xmx4g -d output app.apk`，或设 `JAVA_OPTS="-Xmx4g"` |
| 反编译代码多 `// Error` / `JADX WARNING` 注释 | 脚本已默认带 `--show-bad-code`；手动跑 jadx 时加它或用 `--deobf` |
| Vineflower 单方法卡住 | `-mpm=60` 设置每方法 60 秒超时 |
| Vineflower 整体超时 | `FERNFLOWER_TIMEOUT_SECONDS` 环境变量调整总超时（默认 900 秒） |
| Vineflower JAR 找不到 | 设置 `FERNFLOWER_JAR_PATH` 环境变量（fernflower.jar/vineflower.jar 均可） |
| dex2jar 失败（ZipException） | APK 可能非标准 ZIP 结构，尝试 jadx |
| 反编译只出十来个 Java 文件 | 可能是 split/bundled 壳 APK，脚本会自动检测并反编译内嵌 base.apk |
| jadx 退出码非 0 但有输出 | 属部分成功：脚本会提示警告并继续使用已产出的文件 |

## 十一、采用建议

按以下顺序引入这个 Skill：

1. **先跑指纹甄别**：拿到 APK 先 `fingerprint.sh`，是 Flutter/RN/Cordova/Xamarin 就此打住换工具，是原生应用再往下。
2. **跑通 jadx 单引擎**：在熟悉的 APK 上验证依赖检查、反编译、API 提取，确认输出符合预期。
3. **再试调用链追踪**：选一个已知结构的 App（如开源应用编译的 APK），验证追踪结果与实际代码一致。
4. **混淆应用加一步 Kotlin 名字恢复**：`recover-kotlin-names.sh` 成本几乎为零，先把类名地图建出来再读代码。
5. **按需引入 Vineflower**：只在 jadx 输出错误注释过多或关键方法还原不准时切换。
6. **双引擎对比留作疑难场景**：常规分析不必开启，耗时翻倍且对比需要人工判断。

适用边界：这个 Skill 解决的是"流程编排"问题，混淆对抗只解决了一半——Kotlin 元数据能恢复类名，但方法名、字段名、字符串加密、native 层分析仍然要人工介入（IDA Pro、Frida 在进阶路径里等着）。它的价值在于把可自动化的部分压成一句命令，把人工时间留给真正需要判断的环节。

## 自测题

### 基础题

1. **jadx 和 Vineflower 的核心区别是什么？什么场景下应该选哪个？**
2. **传统手工逆向的断点有哪些？这个 Skill 如何解决这些问题？**
3. **Retrofit 接口的特征识别模式是什么？应该用什么样的 grep 命令提取？**
4. **从 Activity 到 HTTP 请求的调用链通常经过哪些层？如何用 grep 追踪？**
5. **什么场景下值得开启双引擎对比？开启后输出在哪里？**

### 进阶题

1. **为什么 R8 剥不掉 Kotlin 元数据？`recover-kotlin-names.sh` 利用的是哪两个注解？**
2. **`jadx --deobf` 和 Kotlin 元数据恢复的输出有什么本质区别？**
3. **XAPK 格式是怎么被处理的？拆分工作由谁完成？**
4. **`--paths` 模式为什么在重度混淆的应用上依然有效？它排除哪类误报？**
5. **在法律层面，DMCA §1201(f) 和 EU Directive 2009/24/EC 分别允许什么场景的逆向？**

### 参考答案要点

**基础题**：

1. jadx 直接处理 DEX，Vineflower 需要先转 JAR；Vineflower 在 lambda/泛型/records 等复杂结构还原更好
2. 命令记忆成本、框架错判、混淆对抗、调用链断裂；Skill 用 Phase 0–5 串行工作流 + 文件落盘解决
3. HTTP 方法注解（`@GET`/`@POST` 等）；`grep -rn '@GET\|@POST' sources/`
4. Activity → ViewModel → Repository → ApiService → OkHttpClient；grep 继承关系和字段引用，DI 绑定处注意 Hilt/Koin 两种形态
5. 单引擎输出大量错误注释、需要交叉验证关键方法、混淆严重可能映射出错；输出在 `output/jadx/` 和 `output/fernflower/`

**进阶题**：

1. Kotlin 运行时的反射、协程、data class 特性运行时依赖原始全限定名；`@DebugMetadata` 的 `c` 字段和 `@Metadata` 的 `d2` 数组
2. `--deobf` 生成合成占位名（`p001a`），元数据恢复还原开发者写的原始类名
3. `decompile.sh` 解压 XAPK、找出全部 APK 逐个反编译；拆分是脚本做的，不是 jadx 的能力
4. R8 不混淆字符串常量内容，路径字符串原样保留；MIME 类型和 `/proc` 等系统路径被排除
5. 前者覆盖互操作性分析（美国），后者覆盖为实现互操作所必需的逆向（欧盟）；具体适用需结合当地法律

## 进阶路径

### 阶段一：熟练使用单引擎（1-2 周）

- [ ] 在自己熟悉的 APK 上跑通指纹甄别 + jadx 单引擎全流程
- [ ] 验证依赖检查、反编译、结构分析、API 提取各阶段的输出
- [ ] 手动追踪一个已知 App 的调用链，对比 Skill 输出

### 阶段二：掌握双引擎与混淆对抗（2-3 周）

- [ ] 在一个混淆严重的 APK 上对比 jadx 和 Vineflower 的输出质量
- [ ] 跑通 `recover-kotlin-names.sh` + `lookup-name.sh`，统计目标类恢复率
- [ ] 理解 `--deobf` 合成名与元数据恢复原始名的分工

### 阶段三：深入逆向工程（1-2 个月）

- [ ] 学习 ProGuard/R8 混淆原理，理解哪些符号被保留、为什么
- [ ] 掌握 native 层分析（IDA Pro、Frida），理解 Skill 覆盖不到的场景
- [ ] 阅读 jadx 源码，理解 DEX→Java 的反编译原理

### 阶段四：贡献和扩展（持续）

- [ ] 为 Skill 贡献新的 API 提取模式（如 gRPC、protobuf-wire）
- [ ] 扩展支持的文件格式（如 `.apkm`、`.apks` 变体）
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
- **dex2jar**（社区维护 fork）：https://github.com/ThexXTURBOXx/dex2jar
- **apktool**：https://apktool.org/

## 参考来源与口径说明

本文数据与机制描述以以下来源为准，核对日期 2026-09-26：

- **版本锚点**：plugin v1.5.0（`plugin.json`/`marketplace.json` 的 version 字段；仓库最后推送 2026-09-08，其后无新版本）。
- **仓库数据**：Stars 7,906、Forks 897、语言 Shell、许可证 Apache-2.0，来自 GitHub API 当日读数；仓库创建于 2026-02-02。
- **机制描述**：Phase 0–5 工作流、XAPK/split APK 处理、双引擎输出目录、部分成功语义、`FERNFLOWER_TIMEOUT_SECONDS` 默认值，逐条对照 `SKILL.md` 与 `scripts/` 下 bash 脚本源码（`decompile.sh`、`find-api-calls.sh`、`check-deps.sh`、`install-dep.sh`、`fingerprint.sh`、`recover-kotlin-names.sh`、`lookup-name.sh`）；grep 模式与提取注解全集对照 `references/api-extraction-patterns.md` 等参考文档。
- **能力演进**：Kotlin 名字恢复、Ktor/Apollo/Koin/HMAC 提取、`--paths` 模式、Phase 0 指纹、PowerShell 支持分别由 PR #16、#8、#4 等引入（2026-04-27/28 合并），dex2jar 迁移至社区维护 fork（PR #12）。本文所述均为 v1.5.0 现状，不涉及这些 PR 之前的旧口径。
- **恢复率与经验数字**：类名恢复率（总体 30–50%、目标类近 100%、DTO 约 80%）与"`--paths` 通常抽出 100–300 条端点"来自仓库 `references/kotlin-name-recovery.md` 与 `api-extraction-patterns.md` 的官方口径，属作者经验值而非本文实测。
- **法律依据**：合法使用场景与免责条款对照 README 的 Disclaimer 节；具体法律适用请咨询当地专业人士。
