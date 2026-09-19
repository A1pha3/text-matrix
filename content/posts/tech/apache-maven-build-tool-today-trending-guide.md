---
title: "Apache Maven 4：打破 POM 冻结的 20 年最大一次大版本"
date: "2026-07-03T20:57:00+08:00"
lastmod: "2026-09-18T00:00:00+08:00"
draft: false
slug: "apache-maven-build-tool-today-trending-guide"
description: "Maven 4 的第一个判断：它真正解决的不是构建速度，而是 POM 模型 4.0.0 被冻结近二十年、无法演进的问题。本文拆解 consumer POM、模型 4.1.0、subprojects、生命周期改树结构、mvnup 迁移工具，以及当前 RC 阶段的采用边界。"
categories: ["技术笔记"]
tags: ["Java", "Apache"]
author: "text-matrix"
---

Maven 4 的贡献不在快，而在格式。`pom.xml` 的模型版本 4.0.0 自 2005 年 Maven 2 引入以来用到了今天，近二十年没有动过。Maven 团队想改 schema 都改不动，因为整个 Java 生态——Maven Central、IDE、其他构建工具——都绑死在它上面。Maven 4 是第一次真正打破这层冻结的大版本，方法是不动消费者看到的 POM，只在构建侧放开。

截至 2026 年 9 月，Maven 4.0.0 尚未发布正式版，最新候选版是 4.0.0-rc-6（2026-08-04，见官方版本历史）。依赖解析内核已经换成 Maven Resolver 2.0.x——这属于整条 4.x 主线，不是某一份候选版单独引入的。本文基于官方 "What's new in Maven 4"、迁移指南和升级工具文档，拆解 4.x 主线到底改了什么、和 Maven 3 的边界在哪、现在能不能用。文中所有数字与引用均以官方文档为准。

## 目录

- [一、先给判断](#一先给判断)
- [二、总览：三条并行主线](#二总览三条并行主线)
- [三、仓库结构：核心模块与插件分离](#三仓库结构核心模块与插件分离)
- [四、问题起点：POM 为什么被冻结](#四问题起点pom-为什么被冻结)
- [五、模型层：consumer POM 与模型 4.1.0](#五模型层consumer-pom-与模型-410)
- [六、生命周期层：从列表到树](#六生命周期层从列表到树)
- [七、工程层：Java 17、mvnup 与插件兼容](#七工程层java-17mvnup-与插件兼容)
- [八、一个具体案例：库作者迁移到 Maven 4](#八一个具体案例库作者迁移到-maven-4)
- [九、如何看待性能数字](#九如何看待性能数字)
- [十、采用顺序与适用边界](#十采用顺序与适用边界)
- [最小可运行示例](#最小可运行示例)
- [自测题](#自测题)
- [练习](#练习)
- [进阶路径](#进阶路径)
- [常见问题 FAQ](#常见问题-faq)

## 一、先给判断

Maven 4 是一个大版本，但它的价值不在性能，而在格式解冻。三句话概括这条主线：

- **模型升级**：构建侧 POM 升级到模型 4.1.0，消费者侧仍保持 4.0.0，生态不破。
- **生命周期重构**：生命周期从线性列表改成树，新增 `before:` / `after:` 阶段，执行顺序可控。
- **工程配套**：运行要求 Java 17，内置 `mvnup` 迁移工具，部分插件需要升级。

## 二、总览：三条并行主线

Maven 4 的改动可以拆成三条相对独立的主线，先分清边界再进入细节：

| 主线 | 改了什么 | 谁受益 |
|------|----------|--------|
| 模型层 | consumer POM、模型 4.1.0、`<subprojects>`、bom 打包类型 | 库作者、多模块项目 |
| 生命周期层 | 线性列表 → 树、`before:` / `after:` 阶段、条件式 profile 激活 | 插件开发者、复杂构建 |
| 工程层 | Java 17 要求、`mvnup` 迁移工具、插件兼容性清理 | 所有升级用户 |

三条主线可以独立采用：只用模型层特性不碰生命周期，反之亦然。迁移指南也按这个思路分步骤。

## 三、仓库结构：核心模块与插件分离

`apache/maven` 主仓库只包含 Maven 核心，插件是独立的 `apache/maven-*` 仓库，各自按 release train 发版。这是 Maven 的架构约定，也是 4.x 能独立于插件演进的前提。

| 模块 | 职责 |
| --- | --- |
| `maven-core` | 核心执行引擎（lifecycle、phase、goal） |
| `maven-model` | POM 数据结构（4.x 引入模型 4.1.0） |
| `maven-resolver` | 依赖解析（基于 Maven Artifact Resolver） |
| `maven-settings` | 用户 / 全局 settings.xml 处理 |
| `maven-embedder` | 把 Maven 嵌入 IDE / CI 的 API |
| `maven-cli` | 命令行入口（4.x 起独立成模块） |

插件（compiler、surefire、jar、war、deploy 等）不在主仓库。核心发版与插件发版互不牵制，插件当前承诺 API 兼容到 Maven 3.9.0。

## 四、问题起点：POM 为什么被冻结

Maven 之所以停在小版本迭代那么多年，根因在 POM 承担了两种职责：构建自己的信息和消费方需要的信息。产物发布后，构建配置对消费者没有意义，但两者挤在同一个 `pom.xml` 里，任何 schema 改动都会逼着整个生态适配。

Maven 核心开发者 Hervé Boutemy 在 2021 年 Java Advent 上把这种状态称为"模型被冻在琥珀里"：

> 构建模型被彻底固定后，我们很难再做迭代优化，只能停留在 Maven 3 小版本迭代，无法落地那些需要大幅调整 POM 结构的改进方案。

Maven 4 的解法是先把这两种信息拆开：构建信息留在本地 `pom.xml`（模型 4.1.0），消费信息单独生成一份扁平化的 consumer POM 发布到仓库（模型 4.0.0）。下游依赖者看到的还是 4.0.0，生态不用跟着改。

## 五、模型层：consumer POM 与模型 4.1.0

### 5.1 构建 POM 与 consumer POM 分离

Maven 4 部署到远程仓库的不再是源码 `pom.xml`，而是构建时生成的 consumer POM，模型版本固定为 4.0.0。这一步自动发生，不需要任何配置，目的是保证产物仍能被 Maven 3 和其他构建工具消费。

consumer POM 的"扁平程度"由属性 `maven.consumer.pom.flatten` 控制，默认关闭。关闭时，consumer POM 保留 `<parent>` 引用等结构，继承链仍需可解析；开启后才会深度扁平化：去掉 parent 引用（继承的元素直接展开）、把 BOM 导入摊平成依赖列表、剔除属性和插件配置，只留消费方需要的依赖信息：

```xml
<properties>
  <maven.consumer.pom.flatten>true</maven.consumer.pom.flatten>
</properties>
```

也可以写在 reactor 根目录的 `.mvn/maven-user.properties` 里统一生效。

扁平化开启后，两类 POM 的内容差异如下：

| 内容 | 构建 POM | consumer POM |
|------|:---:|:---:|
| 模型版本 | 4.1.0 | 4.0.0 |
| 第三方依赖信息 | ✅ | ✅ |
| POM 属性 | ✅ | ❌ |
| 插件配置 | ✅ | ❌ |
| 仓库信息 | ✅ | ✅ |

注意这张表只描述扁平化后的 consumer POM；`pom` 打包类型的构件不适用，它们的 consumer POM 本来就要承载构建信息（这一点在 7.3 节还会再遇到）。

### 5.2 模型版本 4.1.0 只用于构建侧

源码库中的构建 POM 可升级到模型版本 4.1.0（命名空间 `http://maven.apache.org/POM/4.1.0`），consumer POM 仍生成 4.0.0。这意味着不升级到 4.1.0 也能用 Maven 4 构建，只是用不了新模型特性。

### 5.3 模块改名 subprojects

Java 9 引入模块系统后，`<modules>` 里的 "module" 和 JPMS 的 "module" 概念冲突。Maven 4 把模块改名为子项目，4.1.0 模型新增 `<subprojects>` 元素，`<modules>` 仍可用但已废弃。

```xml
<subprojects>
  <subproject>service</subproject>
  <subproject>dao</subproject>
  <subproject>web</subproject>
</subprojects>
```

### 5.4 子项目自动发现

父 POM 是 `pom` 打包类型、且没有声明 `<modules>` / `<subprojects>` 时，Maven 4 会自动发现子目录里含 `pom.xml` 的项目。新增子项目不再需要改父 POM，少一处 merge 冲突源。

### 5.5 父版本自动推断

这是 2005 年就提出的需求（issue MNG-624）。使用模型 4.1.0 时，子项目 `<parent>` 里的 `version`、`groupId`、`artifactId` 都可以省略，Maven 沿相对路径向上找父 POM 推断坐标，`<parent/>` 是等价的简写；同 reactor 内跨子项目的依赖版本也可省略。升级父版本只改父 POM 一处。

### 5.6 bom 打包类型

Maven 4 新增 `bom` 打包类型，把"管理依赖清单"的 BOM 与"作为父 POM"的角色区分开：

```xml
<packaging>bom</packaging>
```

BOM 的依赖导入支持 exclusion，依赖管理更精确。

### 5.7 新构件类型

4.0 新增 `classpath-jar`、`modular-jar` 等构件类型，在 `<dependency>` 声明里明确控制构件进 classpath 还是 module path，对 JPMS 项目更友好。插件支持有边界：按官方文档 2025 年 10 月的标注，只有 Compiler Plugin 4.0.0-beta-3 及以上版本遵循这些新类型，其余插件在逐步跟进。CI 友好版本变量（`${revision}` 等）不再需要 flatten-maven-plugin 的额外配置，开启 consumer POM 扁平化即可由 Maven 4 原生处理。注意边界：未开启扁平化的项目使用 `${revision}` 仍可能遇到缺失版本错误，这是 RC-6 官方列出的已知问题。

## 六、生命周期层：从列表到树

Maven 3 的生命周期是一条按顺序排列的 phase 列表；Maven 4 把它重新定义成树，phase 之间有了父子关系，下游项目不必等上游跑完整条生命周期。要吃到这个细粒度执行，需要启用并发构建器（`-b concurrent`）；不开的话，默认执行行为和 Maven 3 基本一致，升级本身不会改变构建顺序。

树结构之上，Maven 4 给每个 phase 配了一组钩子：

- `before:` / `after:`：每个生命周期阶段都有对应的前置、后置阶段，插件可以绑定上去；同一阶段内的多个执行还能用 `before:compile[100]`、`before:compile[200]` 这样的序号语法规定先后。
- `before:all` / `after:all`：包裹整个项目的构建（含全部子项目层级），多项目构建中父项目的 `before:all` 最先执行，子项目的 `after:all` 先于父项目执行。
- `before:each` / `after:each`：包裹单个项目里的每个标准阶段（validate、compile、test……），适合做每个阶段统一的准备和清理。

Maven 3 里只有部分阶段才有的 `pre-*` / `post-*` 阶段已废弃为 `before:` / `after:` 的别名，官方建议不要再绑定到它们。

profile 激活也支持条件表达式（`<activation>` 下新增 `<condition>` 元素），可以判断文件是否存在、比较属性值、用逻辑运算符组合条件，替代一部分需要在 `pom.xml` 里写脚本的旧做法。

## 七、工程层：Java 17、mvnup 与插件兼容

### 7.1 运行要求 Java 17

Maven 4 运行本身要求 Java 17。注意这只是运行 Maven 的要求：项目仍可用 `-source 8 -target 8` 编译旧版 Java，编译目标不受限制。

### 7.2 mvnup 迁移工具

Maven 4.0.0-rc-4 起发行包内置升级工具，两阶段使用：

```bash
# 检测项目里的潜在问题
mvnup check

# 自动应用推荐的修复
mvnup apply
```

工具覆盖插件版本升级、POM 结构调整、被废弃属性的替换等常见问题。关键在它默认只把模型升级到 **4.0.0**——这一步产物仍能被 Maven 3 构建，属于纯兼容修复；只有显式指定目标模型 `4.1.0`，才会引入仅 Maven 4 支持的特性：

```bash
# 默认目标 4.0.0，保持 Maven 3 兼容
mvnup check
mvnup apply

# 显式指定目标 4.1.0，启用新模型特性
mvnup apply --model-version 4.1.0
```

这样三条主线可以按迁移意愿分步落地：先 `apply` 到 4.0.0 保证可回退，等确认无误后再单独把模型推到 4.1.0。

### 7.3 插件兼容性与依赖解析内核

Maven 4 的目标是运行所有遵循 Maven 3.9 兼容写法、不依赖 Maven 2 旧 API 的插件，但部分插件和扩展仍需要升级到特定版本。以 4.0.0-rc-6 官方已知问题为例：Tycho 5.0 以下、Quarkus 3.20 以下与 Maven 4 的依赖注入机制不兼容；`pgpverify-maven-plugin` 1.20 以下会抛 `ClassCastException`。`maven-shade-plugin` 的 `dependency-reduced-pom.xml` 曾在早期 RC 触发 parent cycle 报错，rc-6 已修复（#12074）。另外，Maven 4 升级了 Super POM 里核心插件的默认版本，即使你没改任何配置，构建行为也可能变化——官方建议在 POM 里显式固定所有插件版本，把控制权留在自己手里。依赖 Maven extensions 的项目可能要等扩展作者适配，官方建议直接联系扩展维护者确认计划。

依赖解析层面，Maven 4 主线换用了 Resolver 2.0.x，包含 150 多项修复与改进（例如 Java 原生 HTTP 客户端）。Resolver 2.0 与 1.x 的 API 不向后兼容，第三方依赖解析相关的扩展需要对应升级。

两个明确的破坏性变化值得注意：

- **install / deploy 移到构建末尾**：install 和 deploy 插件的 `installAtEnd`、`deployAtEnd` 参数默认值在 Maven 4 改为 `true`（官方迁移指南列为 breaking change）。不再随各子项目构建逐个执行，而是等整次构建结束、全部子项目成功后统一处理。依赖旧默认值 `false` 的项目需要在插件配置里显式声明。
- **目录属性有增有删**：新增官方根目录属性 `${project.rootDirectory}`、`${session.rootDirectory}`、`${session.topDirectory}`；过去用于定位根目录的内部属性 `executionRootDirectory`、`multiModuleProjectDirectory` 被废弃或移除（MNG-7038）。`${project.basedir}` 仍指向子项目自身目录，不受影响。

还有一个隐形但重要的边界：**consumer POM 并不总是能降到 4.0.0**。对 `pom` 打包的父项目，consumer POM 会保留 `<parent>` 引用，且部分 4.1.0 特性无法被剥离，模型版本可能停在 4.1.0。rc-6 起官方加了快速失败校验（fail-fast consumer POM validation），构建时会直接报错，不再把 4.1.0 的 POM 静默发到仓库；但风险本身有真实先例——JLine 4.0.0 用模型 4.1.0 构建，其 parent POM 留在了 Central 上，下游用 Maven 3 或 Gradle 解析即失败（官方 issue #11772）。判断是否启用 4.1.0 时，要把"下游是否只有 Maven 4"一并考虑进去。

## 八、一个具体案例：库作者迁移到 Maven 4

把上面的机制串成一个真实任务：一个发布到 Maven Central 的多模块库，从 Maven 3.9 迁移到 Maven 4。

1. **准备（Maven 3 侧）**：把插件升到最新 3.x 版本（可用 versions-maven-plugin 的 `display-plugin-updates` 目标检查），确认运行环境支持 Java 17。
2. **测试（并行构建）**：安装 4.0.0-rc-6，跑 `mvn clean verify` 对比结果。这一步用 Maven 4 的最小改动模式，POM 不动也能构建，目的是暴露不兼容插件。
3. **迁移（启用新特性）**：跑 `mvnup check` / `mvnup apply` 处理已知问题；再升级到模型 4.1.0，把 `<modules>` 改成 `<subprojects>`，删掉子项目里的父版本号，启用 consumer POM 扁平化。
4. **发布**：确认 `install` 在构建末尾执行后产物齐全，发布到 Central，检查仓库里落的是扁平化 consumer POM 而不是原始 `pom.xml`。

这条路径里，第 1、2 步是 Maven 4 的兼容保证，第 3 步是模型层和工程层特性，第 4 步验证的是构建 POM 与 consumer POM 分离是否真正生效。

## 九、如何看待性能数字

关于 Maven 4 性能的讨论很多，但需要先厘清一件事：**Maven 官方没有发布统一的 benchmark**。社区流传的"性能提升百分之几十"大多来自个别项目、特定机器、特定构建的复现，口径不一，不能当作选型依据。

能从官方信息确定的是：Maven 4 换用的 Resolver 2.0 包含 150 多项修复与改进；生命周期树化配合 `-b concurrent` 提供了官方的并行执行机制。但官方没有发布可复现的基准数字。要验证自己的项目是否变快，正确做法是在同一台机器上分别用 Maven 3.9.16 和 Maven 4 RC 跑同一构建，比较实测耗时，而不是引用别人的结论。

另外，构建缓存不是 Maven 4 核心自带的功能，而是独立扩展 `maven-build-cache-extension`（要求 Maven 3.9.0+，含 4.x），本地和远程缓存都支持。想缩短 CI 时间，直接评估这个扩展，不必等 Maven 4。

## 十、采用顺序与适用边界

**谁可以先上**：库作者和开源项目维护者。consumer POM 扁平化、bom 打包类型、父版本推断对发布方收益最直接，且 Maven 4 的兼容保证让低风险试水成为可能。官方也鼓励 OSS 项目用 RC 版发布到 Central，为 GA 前积攒真实反馈。

**谁可以等**：生产环境的大型私有项目。4.0.0 尚未 GA，RC 阶段不适合直接上生产；建议先在分支上做并行验证，等 GA 后再切换。

**谁不必着急**：只用 Maven 做内部构建、对 POM 格式无痛点的团队。3.x 线仍在演进——3.9.16 是最新 GA，3.10 已进入 RC（3.10.0-rc-1，2026-07-09，仍要求 Java 8）——不升级不影响日常使用。不过要注意官方迁移指南的表态：模型版本 4.1.0（或更高）会在未来的 Maven 版本里成为必需，4.1.0 这一步迟早要走，只是不必在 RC 阶段赶。

**升级顺序建议**：先 Maven 3.9 升级插件 → 并行用 Maven 4 RC 验证 → `mvnup` 处理兼容 → 再逐步启用 4.1.0 模型特性。不要一步到位全量改造。

Maven 4 的定位很清楚：它是给"POM 被冻住"的 Java 生态开的锁，不是一次性能翻新。判断现在要不要动手，只需要回答一个问题：你的项目是否发布构件、是否多模块——是，就按上面的顺序开始准备；不是，可以等 GA。

## 最小可运行示例

把一个 Maven 3 多模块项目切成 Maven 4 可用的最小形态。

```bash
# 1) 用 Maven 4 RC 构建现有项目（POM 不用改，先验证兼容）
./mvn -version            # 确认运行环境 Java 17+
./mvn clean verify        # 发现不兼容插件并逐个升级

# 2) 运行内置迁移工具
mvnup check               # 检测潜在问题
mvnup apply               # 自动修复已知问题
```

```xml
<!-- 父 POM：启用 consumer POM 扁平化，声明根目录 -->
<project xmlns="http://maven.apache.org/POM/4.1.0" root="true">
  <modelVersion>4.1.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>parent</artifactId>
  <version>1.0.0</version>
  <packaging>pom</packaging>
  <properties>
    <maven.consumer.pom.flatten>true</maven.consumer.pom.flatten>
  </properties>
  <!-- 不写 <modules>，让 Maven 4 自动发现子项目 -->
</project>
```

```xml
<!-- 子项目：模型 4.1.0，父版本自动推断，不用写 version -->
<project xmlns="http://maven.apache.org/POM/4.1.0">
  <modelVersion>4.1.0</modelVersion>
  <parent>
    <relativePath>..</relativePath>
  </parent>
  <artifactId>service</artifactId>
</project>
```

这条链里，自动发现解决"加模块要改父 POM"的问题，父版本推断解决"升级父版本要全项目改"的问题，consumer POM 扁平化解决"发布内容带无关构建信息"的问题。

## 自测题

1. **Maven 4 为什么要把构建 POM 和 consumer POM 分开？**
   <details><summary>查看答案</summary>POM 同时承担构建信息和消费信息，schema 一改就逼整个生态适配，导致格式冻结。拆开后构建侧可以用新模型 4.1.0，消费侧仍发布 4.0.0，生态不受影响。</details>

2. **Maven 4 的模型版本 4.1.0 用在哪些文件上？consumer POM 用什么版本？**
   <details><summary>查看答案</summary>4.1.0 只用于源码库中的构建 POM；发布到远程仓库的 consumer POM 仍是 4.0.0。</details>

3. **`<modules>` 和 `<subprojects>` 什么关系？子项目自动发现的条件是什么？**
   <details><summary>查看答案</summary>`<subprojects>` 是 4.1.0 里取代 `<modules>` 的新元素，后者已废弃但可用。父 POM 为 pom 打包类型且不声明这两个元素时，Maven 自动发现子目录中含 `pom.xml` 的项目。</details>

4. **Maven 4 运行要求什么 Java 版本？这是否限制项目的编译目标？**
   <details><summary>查看答案</summary>运行 Maven 本身要求 Java 17。不限制编译目标，项目仍可编译 Java 8 等旧版本。</details>

5. **mvnup 工具做什么？迁移分哪几步？**
   <details><summary>查看答案</summary>`mvnup check` 检测问题，`mvnup apply` 自动修复。官方建议三步：先在 Maven 3.9 升级插件，再并行用 Maven 4 RC 验证，最后启用可选的新特性。</details>

6. **"Maven 4 比 Maven 3 快百分之几十"这类说法为什么不能直接信？**
   <details><summary>查看答案</summary>Maven 官方没有发布统一 benchmark，社区数字来自不同项目、不同机器的实测，口径不一。要验证应在同一台机器分别跑两个版本比较。</details>

7. **`before:each` 和 `before:all` 分别在什么范围触发？**
   <details><summary>查看答案</summary>`before:each` 在单个项目生命周期的每个标准阶段（validate、compile、test 等）之前触发；`before:all` 在整个项目（含全部子项目层级）构建开始前触发一次。</details>

## 练习

1. 用 Maven 4 RC 构建一个现有 Maven 3 项目，记录 `mvnup check` 报出的问题类别，确认你的项目主要属于哪一类。
2. 把一个小型多模块项目升级到模型 4.1.0，删除 `<modules>` 声明验证自动发现是否生效。
3. 启用 `maven.consumer.pom.flatten` 后把构件 deploy 到一个本地目录仓库（例如 `mvn deploy -DaltDeploymentRepository=local::file:///tmp/repo`），检查落盘的 POM 与源码 `pom.xml` 的差异，确认插件配置等构建信息已被剔除。
4. 在多模块项目里分别绑定 `before:compile` / `after:test` 和 `before:all` / `after:all` 的插件执行，观察阶段级钩子与构建级钩子的触发范围差异。
5. 在 CI 里评估 `maven-build-cache-extension`，对比开启前后二次构建耗时。

## 进阶路径

- **从"构建"到"发布"**：consumer POM 扁平化、bom 打包类型、CI 友好版本变量，把发布产物的干净度做到位。
- **从"单模块"到"多模块"**：subprojects 自动发现、父版本推断、reactor 行为变化，理解多模块构建的新边界。
- **从"用户"到"开发者"**：生命周期树结构、`before:` / `after:` 阶段、新插件 API，这是插件开发者迁移 Maven 4 的必修课。
- **从"Maven"到"生态"**：对比 Gradle 的 task graph 与 Bazel 的规则，Maven 4 在哪个规模区间依然是最稳的选择。

## 常见问题 FAQ

1. **Maven 4.0.0 正式版什么时候发布？现在能用吗？**
   官方未给具体日期，截至 2026-09 最新候选版为 4.0.0-rc-6（2026-08-04），官方明确 RC 不适合生产。可以在分支上验证兼容，等 GA 再上生产。

2. **升级到 4 后老插件报错怎么办？**
   先升级到插件的 Maven 4 兼容版本——以 RC-6 已知问题为例，Tycho 需 5.0.3+、Quarkus 需 3.20+、pgpverify 需 1.20+；shade 的 reduced POM 报错在 rc-6 已修复，换新版即可。想提前暴露隐患，可以加 `--fail-on-severity WARN` 让构建在出现警告时就失败。仍报错就运行 `mvn -e` 拿完整堆栈，按 issue 模板反馈。

3. **不升级到模型 4.1.0 能用 Maven 4 吗？**
   可以。4.0.0 模型的 POM 在 Maven 4 下正常构建，4.1.0 只是可选的新特性入口。

4. **构建还是太慢，从哪里入手？**
   先在同一台机器实测 Maven 3.9.16 与 Maven 4 RC 的差异，再评估 `maven-build-cache-extension`（要求 Maven 3.9.0+）。不要根据无出处的性能数字做决定。

5. **消费者收到新格式 POM 会不会出问题？**
   发布到仓库的 consumer POM 目标版本是 4.0.0，扁平的子构件正常构建即可被 Maven 3 / Gradle 解析。**但存在例外**：`pom` 打包的父项目（`packaging=pom`）的 consumer POM 会保留 `<parent>` 引用，部分 4.1.0 特性无法剥离时模型版本停在 4.1.0——rc-6 起构建会对这种情况快速失败报错，但 JLine 4.0.0 的 parent POM 已经以 4.1.0 落在 Central 上（官方 issue #11772），下游 Maven 3 / Gradle 解析它即失败。公开多模块库启用 4.1.0 前，要把下游工具的兼容性一并评估。

6. **用了 Maven 4 还能换回 Maven 3 吗？**
   只改到模型 4.0.0、未启用新特性时，项目可双向切换。一旦升级到 4.1.0 模型并用上 `root="true"`、`<subprojects>` 等新元素，换回 Maven 3 需要回退这些改动。
