---
title: "Apache Maven 4：打破 POM 冻结的 20 年最大一次大版本"
date: "2026-07-03T20:57:00+08:00"
lastmod: "2026-08-20T00:00:00+08:00"
draft: false
slug: "apache-maven-build-tool-today-trending-guide"
description: "Maven 4 的第一个判断：它真正解决的不是构建速度，而是 POM 模型 4.0.0 被冻结近二十年、无法演进的问题。本文拆解 consumer POM、模型 4.1.0、subprojects、生命周期改树结构、mvnup 迁移工具，以及当前 RC 阶段的采用边界。"
categories: ["技术笔记"]
tags: ["Java", "Apache"]
author: "text-matrix"
---

Maven 4 的贡献不在快，而在格式。`pom.xml` 的模型版本 4.0.0 自 2005 年 Maven 2 引入以来用到了今天，近二十年没有动过。Maven 团队想改 schema 都改不动，因为整个 Java 生态——Maven Central、IDE、其他构建工具——都绑死在它上面。Maven 4 是第一次真正打破这层冻结的大版本，方法是不动消费者看到的 POM，只在构建侧放开。

截至 2026 年 8 月，Maven 4.0.0 尚未发布正式版，最新候选版是 4.0.0-rc-6（2026-08-04）。本文基于官方发布说明和文档，拆解 4.x 主线到底改了什么、和 Maven 3 的边界在哪、现在能不能用。

## 目录

- [一、先给判断](#一先给判断)
- [二、总览：三条并行主线](#二总览三条并行主线)
- [三、仓库结构：核心模块与插件分离](#三仓库结构核心模块与插件分离)
- [四、问题起点：POM 为什么被冻结](#四问题起点pom-为什么被冻结)
- [五、模型层：consumer POM 与模型 4.1.0](#五模型层consumer-pom-与模型-410)
- [六、生命周期层：从图到树](#六生命周期层从图到树)
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
- **生命周期重构**：生命周期从图改成树，新增 `before:` / `after:` 阶段，执行顺序可控。
- **工程配套**：运行要求 Java 17，内置 `mvnup` 迁移工具，部分插件需要升级。

## 二、总览：三条并行主线

Maven 4 的改动可以拆成三条相对独立的主线，先分清边界再进入细节：

| 主线 | 改了什么 | 谁受益 |
|------|----------|--------|
| 模型层 | consumer POM、模型 4.1.0、`<subprojects>`、bom 打包类型 | 库作者、多模块项目 |
| 生命周期层 | 图 → 树、`before:` / `after:` 阶段、条件式 profile 激活 | 插件开发者、复杂构建 |
| 工程层 | Java 17 要求、`mvnup` 迁移工具、插件兼容性清理 | 所有升级用户 |

三条主线可以独立采用：只用模型层特性不碰生命周期，反之亦然。迁移指南也按这个思路分步骤。

## 三、仓库结构：核心模块与插件分离

`apache/maven` 主仓库只包含 Maven 核心，插件是独立的 `apache/maven-*` 仓库，各自按 release train 发版。这是 Maven 的架构约定，也是 4.x 能独立于插件演进的前提。

| 模块 | 职责 |
| --- | --- |
| `maven-core` | 核心执行引擎（lifecycle、phase、goal） |
| `maven-model` | POM 数据结构（4.x 引入模型 4.1.0） |
| `maven-resolver` | 依赖解析（基于 Apache Resolver） |
| `maven-settings` | 用户 / 全局 settings.xml 处理 |
| `maven-embedder` | 把 Maven 嵌入 IDE / CI 的 API |
| `maven-cli` | 命令行入口（4.x 起独立成模块） |

插件（compiler、surefire、jar、war、deploy 等）不在主仓库。核心发版与插件发版互不牵制，插件只承诺 API 兼容到 Maven 3.9.0。

## 四、问题起点：POM 为什么被冻结

Maven 之所以停在小版本迭代那么多年，根因在 POM 承担了两种职责：构建自己的信息和消费方需要的信息。产物发布后，构建配置对消费者没有意义，但两者挤在同一个 `pom.xml` 里，任何 schema 改动都会逼着整个生态适配。

Maven 核心开发者 Hervé Boutemy 在 2021 年 Java Advent 上把这种状态称为"模型被冻在琥珀里"：

> 构建模型被彻底固定后，我们很难再做迭代优化，只能停留在 Maven 3 小版本迭代，无法落地那些需要大幅调整 POM 结构的改进方案。

Maven 4 的解法是先把这两种信息拆开：构建信息留在本地 `pom.xml`（模型 4.1.0），消费信息单独生成一份扁平化的 consumer POM 发布到仓库（模型 4.0.0）。下游依赖者看到的还是 4.0.0，生态不用跟着改。

## 五、模型层：consumer POM 与模型 4.1.0

### 5.1 构建 POM 与 consumer POM 分离

Maven 4 在构建时生成一份精简的 consumer POM，只保留消费者需要的依赖信息，去掉插件配置、profile、父 POM 引用等构建细节。发布到远程仓库的是这份 consumer POM，而不是原始 `pom.xml`。

consumer POM 的扁平化默认关闭，避免意外改变发布行为。需要开启时设置属性：

```xml
<properties>
  <maven.consumer.pom.flatten>true</maven.consumer.pom.flatten>
</properties>
```

也可以写在 reactor 根目录的 `.mvn/maven-user.properties` 里统一生效。

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

这是 2005 年就提出的需求（issue MNG-624）。使用模型 4.1.0 时，子项目可以不写父 POM 的 `version`，Maven 沿相对路径向上推断；同 reactor 内跨子项目的依赖版本也可省略。升级父版本只改父 POM 一处。

### 5.6 bom 打包类型

Maven 4 新增 `bom` 打包类型，把"管理依赖清单"的 BOM 与"作为父 POM"的角色区分开：

```xml
<packaging>bom</packaging>
```

BOM 的依赖导入支持 exclusion，依赖管理更精确。

### 5.7 新构件类型

4.0 新增 `classpath-jar`、`modular-jar` 等构件类型，明确控制构件进 classpath 还是 module path，对 JPMS 项目更友好。CI 友好版本变量（`${revision}` 等）不再需要 flatten-maven-plugin 的额外配置，开启 consumer POM 扁平化即可由 Maven 4 原生处理。注意边界：未开启扁平化的项目使用 `${revision}` 仍可能遇到缺失版本错误，这是 RC-6 官方列出的已知问题。

## 六、生命周期层：从图到树

Maven 3 的生命周期是一个有向图，执行顺序存在歧义。Maven 4 把生命周期改成树结构，执行顺序确定，同时新增一组阶段钩子：

- `before:all` / `after:all`：在整次构建前后执行。
- `before:each` / `after:each`：在每个子项目执行前后触发。
- 插件执行可以用 `before:` / `after:` 精确指定相对某个 phase 的位置。

profile 激活也支持条件表达式（基于属性、JDK 版本等），替代部分需要在 `pom.xml` 里写脚本的旧做法。

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

工具覆盖插件版本升级、POM 结构调整、被废弃属性的替换等常见问题。

### 7.3 插件兼容性

Maven 4 优先保证与 Maven 3 的兼容，但部分插件和扩展需要特定版本才能配合。以 4.0.0-rc-6 官方已知问题为例：Tycho 5.0 以下、Quarkus 3.20 以下与 Maven 4 的依赖注入机制不兼容；`pgpverify-maven-plugin` 1.20 以下会抛 `ClassCastException`；`maven-shade-plugin` 的 `dependency-reduced-pom.xml` 可能触发 parent cycle 报错。依赖 Maven extensions 的项目可能要等扩展作者适配，官方建议直接联系扩展维护者确认计划。

两个明确的破坏性变化值得注意：

- **install / deploy 移到构建末尾**：不再按模块逐个安装，而是整次构建结束后统一执行（rc-4 起）。
- **部分目录属性被替换**：`${project.basedir}` 等引用方式有调整，迁移文档列了替换清单。

## 八、一个具体案例：库作者迁移到 Maven 4

把上面的机制串成一个真实任务：一个发布到 Maven Central 的多模块库，从 Maven 3.9 迁移到 Maven 4。

1. **准备（Maven 3 侧）**：把插件升到最新 3.x 版本，确认运行环境支持 Java 17。
2. **测试（并行构建）**：安装 4.0.0-rc-6，跑 `mvn clean verify` 对比结果。这一步用 Maven 4 的最小改动模式，POM 不动也能构建，目的是暴露不兼容插件。
3. **迁移（启用新特性）**：跑 `mvnup check` / `mvnup apply` 处理已知问题；再升级到模型 4.1.0，把 `<modules>` 改成 `<subprojects>`，删掉子项目里的父版本号，启用 consumer POM 扁平化。
4. **发布**：确认 `install` 在构建末尾执行后产物齐全，发布到 Central，检查仓库里落的是扁平化 consumer POM 而不是原始 `pom.xml`。

这条路径里，第 1、2 步是 Maven 4 的兼容保证，第 3 步是模型层和工程层特性，第 4 步验证的是构建 POM 与 consumer POM 分离是否真正生效。

## 九、如何看待性能数字

关于 Maven 4 性能的讨论很多，但需要先厘清一件事：**Maven 官方没有发布统一的 benchmark**。社区流传的"性能提升百分之几十"大多来自个别项目、特定机器、特定构建的复现，口径不一，不能当作选型依据。

能从官方信息确定的是：Maven 4 在模型构建、依赖解析等环节有大量内部优化提交，方向是减少内存分配和提升并行度，但没有可复现的公开基准数字。要验证自己的项目是否变快，正确做法是在同一台机器上分别用 Maven 3.9.16 和 Maven 4 RC 跑同一构建，比较实测耗时，而不是引用别人的结论。

另外，构建缓存不是 Maven 4 核心自带的功能，而是独立扩展 `maven-build-cache-extension`（要求 Maven 3.9.0+，含 4.x），本地和远程缓存都支持。想缩短 CI 时间，直接评估这个扩展，不必等 Maven 4。

## 十、采用顺序与适用边界

**谁可以先上**：库作者和开源项目维护者。consumer POM 扁平化、bom 打包类型、父版本推断对发布方收益最直接，且 Maven 4 的兼容保证让低风险试水成为可能。官方也鼓励 OSS 项目用 RC 版发布到 Central，为 GA 前积攒真实反馈。

**谁可以等**：生产环境的大型私有项目。4.0.0 尚未 GA，RC 阶段不适合直接上生产；建议先在分支上做并行验证，等 GA 后再切换。

**谁不必着急**：只用 Maven 做内部构建、对 POM 格式无痛点的团队。Maven 3.9.16 仍在维护，4.x 的多数收益集中在多模块和发布场景，不升级不影响日常使用。

**升级顺序建议**：先 Maven 3.9 升级插件 → 并行用 Maven 4 RC 验证 → `mvnup` 处理兼容 → 再逐步启用 4.1.0 模型特性。不要一步到位全量改造。

Maven 4 的定位很清楚：它是给"POM 被冻住"的 Java 生态开的锁，不是一次性能翻新。理解这一点，就明白为什么它值得关注，也明白哪些项目现在就该开始准备。

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

## 练习

1. 用 Maven 4 RC 构建一个现有 Maven 3 项目，记录 `mvnup check` 报出的问题类别，确认你的项目主要属于哪一类。
2. 把一个小型多模块项目升级到模型 4.1.0，删除 `<modules>` 声明验证自动发现是否生效。
3. 启用 `maven.consumer.pom.flatten` 后发布一个构件，对比 Central 上 consumer POM 与本地 `pom.xml` 的差异，确认构建配置已被剔除。
4. 写一个带 `before:each` / `after:each` 插件执行的多模块构建，观察执行顺序是否符合预期。
5. 在 CI 里评估 `maven-build-cache-extension`，对比开启前后二次构建耗时。

## 进阶路径

- **从"构建"到"发布"**：consumer POM 扁平化、bom 打包类型、CI 友好版本变量，把发布产物的干净度做到位。
- **从"单模块"到"多模块"**：subprojects 自动发现、父版本推断、reactor 行为变化，理解多模块构建的新边界。
- **从"用户"到"开发者"**：生命周期树结构、`before:` / `after:` 阶段、新插件 API，这是插件开发者迁移 Maven 4 的必修课。
- **从"Maven"到"生态"**：对比 Gradle 的 task graph 与 Bazel 的规则，Maven 4 在哪个规模区间依然是最稳的选择。

## 常见问题 FAQ

1. **Maven 4.0.0 正式版什么时候发布？现在能用吗？**
   官方未给具体日期，截至 2026-08 最新候选版为 4.0.0-rc-6，官方明确 RC 不适合生产。可以在分支上验证兼容，等 GA 再上生产。

2. **升级到 4 后老插件报错怎么办？**
   先升级到插件的 Maven 4 兼容版本——以 RC-6 已知问题为例，Tycho 需 5.0.3+、Quarkus 需 3.20+、pgpverify 需 1.20+，shade 的 reduced POM 报错需处理。仍报错就运行 `mvn -e` 拿完整堆栈，按 issue 模板反馈。

3. **不升级到模型 4.1.0 能用 Maven 4 吗？**
   可以。4.0.0 模型的 POM 在 Maven 4 下正常构建，4.1.0 只是可选的新特性入口。

4. **构建还是太慢，从哪里入手？**
   先在同一台机器实测 Maven 3.9.16 与 Maven 4 RC 的差异，再评估 `maven-build-cache-extension`（要求 Maven 3.9.0+）。不要根据无出处的性能数字做决定。

5. **消费者收到新格式 POM 会不会出问题？**
   不会。发布到仓库的 consumer POM 仍是模型 4.0.0，依赖解析结果与 Maven 3 兼容。扁平化功能默认关闭，只有显式开启才改变发布内容。

6. **用了 Maven 4 还能换回 Maven 3 吗？**
   只改到模型 4.0.0、未启用新特性时，项目可双向切换。一旦升级到 4.1.0 模型并用上 `root="true"`、`<subprojects>` 等新元素，换回 Maven 3 需要回退这些改动。
