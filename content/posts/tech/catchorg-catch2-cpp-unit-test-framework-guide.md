---
title: "Catch2 v3 深度拆解：C++ 单元测试框架的自然选择"
slug: catchorg-catch2-cpp-unit-test-framework-guide
date: 2026-07-11T02:50:00+08:00
lastmod: 2026-07-11T02:50:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["C++", "测试框架", "unit-testing", "TDD", "BDD"]
description: "Catch2 v3 是 C++ 单文件 header-only 测试框架的主力替代品。本文拆解其 TEST_CASE / SECTION 嵌套、Matchers、BDD 风格宏、微基准测试能力，并对比 GoogleTest / doctest 的工程取舍。"
---

# Catch2 v3 深度拆解：C++ 单元测试框架的自然选择

## 核心判断

Catch2 v3 的核心价值不是"测试框架"本身，而是**让测试代码读起来像测试意图**。它通过 TEST_CASE + SECTION 嵌套的命名约定，把"测试场景的层级"映射成"测试代码的物理缩进"，你不需要看代码就知道每个 SECTION 在测什么。这点和 GoogleTest 的"扁平的 TEST_F + 多个 EXPECT"风格有根本性的差异。

## 项目坐标

| 维度 | 数据 |
|------|------|
| 仓库 | catchorg/Catch2 |
| Stars | 约 20.5k |
| 主语言 | 现代 C++（C++14 / C++17 / C++20） |
| License | BSL-1.0（业务源码使用免费，分发限制很少） |
| 当前主版本 | v3（v2.x 已进入维护期） |
| 文档 | https://catch2-docs.readthedocs.io |

## 一个最小测试

```cpp
#define CATCH_CONFIG_MAIN
#include <catch2/catch_test_macros.hpp>

uint32_t factorial(uint32_t n) {
    return n <= 1 ? 1 : n * factorial(n - 1);
}

TEST_CASE("Factorials are computed", "[factorial]") {
    REQUIRE(factorial(0) == 1);
    REQUIRE(factorial(1) == 1);
    REQUIRE(factorial(2) == 2);
    REQUIRE(factorial(3) == 6);
    REQUIRE(factorial(10) == 3628800);
}
```

运行：

```bash
./my_test               # 跑全部
./my_test Factorials    # 按名字过滤
./my_test [factorial]   # 按 tag 过滤
./my_test --list-tests  # 列出全部测试
```

输出是**人类可读**的——失败的断言会显示期望值/实际值/源码位置，不需要额外配置。

## TEST_CASE + SECTION：嵌套场景

这是 Catch2 最具辨识度的设计。SECTION 在 TEST_CASE 内部嵌套，每个 SECTION 是一个独立的测试上下文：

```cpp
TEST_CASE("Vector can be sized and resized", "[vector]") {
    std::vector<int> v(5);
    
    REQUIRE(v.size() == 5);
    REQUIRE(v.capacity() >= 5);
    
    SECTION("resizing bigger changes size and capacity") {
        v.resize(10);
        REQUIRE(v.size() == 10);
        REQUIRE(v.capacity() >= 10);
    }
    
    SECTION("resizing smaller changes size but not capacity") {
        v.resize(0);
        REQUIRE(v.size() == 0);
        REQUIRE(v.capacity() >= 5);
    }
    
    SECTION("reserving bigger does not change size or capacity") {
        v.reserve(10);
        REQUIRE(v.size() == 5);
        REQUIRE(v.capacity() >= 10);
    }
}
```

执行时每个 SECTION 会**重新执行一遍** TEST_CASE 的前置代码（直到 SECTION 之前的代码），这让你可以用"共享前置 + 独立场景"的方式组织测试。GoogleTest 用 `TEST_F` + 多个 `EXPECT_*` 是反过来的——一组前置，多组断言。

Catch2 风格的取舍：

- **优点**：每个场景独立，前置代码自动复用，物理缩进和逻辑层级一致。
- **代价**：SECTION 嵌套深度多时执行时间线性增长（每层都重跑前置）；不能共享 SECTION 之间的局部变量。
- **陷阱**：在 SECTION 里**修改**了前置代码创建的对象，会影响兄弟 SECTION——因为它们是**各自独立的一遍运行**，但 SECTION 之间不会相互污染。

## Matchers：声明式断言

Catch2 v3 引入了完整的 Matchers 体系，把断言写成"声明性匹配"：

```cpp
#include <catch2/matchers/catch_matchers.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>
#include <catch2/matchers/catch_matchers_vector.hpp>

TEST_CASE("Matchers example") {
    std::vector<int> v = {1, 2, 3, 4, 5};
    std::string s = "hello world";
    
    REQUIRE_THAT(v, Catch::Matchers::Contains(3));
    REQUIRE_THAT(v, Catch::Matchers::AllOf(
        Catch::Matchers::SizeIs(5),
        Catch::Matchers::Contains(2),
        Catch::Matchers::Contains(4)
    ));
    REQUIRE_THAT(s, Catch::Matchers::StartsWith("hello"));
}
```

Matcher 在断言失败时会**展开匹配表达式**，告诉你"哪些部分不匹配"——比"expected 3, got 4"友好得多。

## BDD 风格宏

Catch2 提供 SCENARIO / GIVEN / WHEN / THEN 宏，本质上就是 TEST_CASE + SECTION 的别名：

```cpp
SCENARIO("Customer withdrawals", "[bank]") {
    GIVEN("A customer with $100") {
        Account acc(100);
        
        WHEN("they withdraw $30") {
            acc.withdraw(30);
            
            THEN("the balance is $70") {
                REQUIRE(acc.balance() == 70);
            }
        }
        
        WHEN("they withdraw $200") {
            bool ok = acc.withdraw(200);
            
            THEN("the withdrawal fails") {
                REQUIRE_FALSE(ok);
            }
        }
    }
}
```

对业务/QA 团队协作友好——可以拿 GIVEN/WHEN/THEN 当模板填测试场景。

## Approx：浮点比较

浮点比较的经典痛点（`0.1 + 0.2 != 0.3`）Catch2 直接给出 `Approx` 解决方案：

```cpp
TEST_CASE("Floating point") {
    REQUIRE(0.1 + 0.2 == Approx(0.3));      // 默认 epsilon = 0
    REQUIRE(0.1 + 0.2 == Approx(0.3).margin(0.001));   // 绝对误差
    REQUIRE(0.1 + 0.2 == Approx(0.3).epsilon(0.01));   // 相对误差
}
```

## 微基准测试

Catch2 提供 `BENCHMARK` 宏，可以做简单基准（不替代专用库如 Google Benchmark）：

```cpp
TEST_CASE("Benchmark vector vs list") {
    std::vector<int> v(1000);
    std::list<int> l(1000);
    
    BENCHMARK("vector push_back") {
        for (int i = 0; i < 1000; ++i) v.push_back(i);
        return v.size();
    };
    
    BENCHMARK("list push_back") {
        for (int i = 0; i < 1000; ++i) l.push_back(i);
        return l.size();
    };
}
```

跑：

```bash
./my_test --benchmark-samples=100
```

输出会给出每次操作的纳秒级耗时和置信区间。够日常性能对比用——真要严格基准用 Google Benchmark。

## CMake 集成

Catch2 v3 通过 CMake config 文件导出 target：

```cmake
# 方式一：find_package（已安装）
find_package(Catch2 REQUIRED)
target_link_libraries(my_tests PRIVATE Catch2::Catch2WithMain)

# 方式二：FetchContent
include(FetchContent)
FetchContent_Declare(
    Catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG v3.5.0
)
FetchContent_MakeAvailable(Catch2)
```

> Catch2 有两个 target：`Catch2::Catch2`（无 main）和 `Catch2::Catch2WithMain`（含 main，自己不写 `CATCH_CONFIG_MAIN`）。

## 与 GoogleTest 的取舍

| 维度 | Catch2 v3 | GoogleTest |
|------|-----------|------------|
| 学习曲线 | 低 | 中 |
| 单 header 部署 | 历史上 v1 是；v3 是库 | 库 |
| 嵌套场景 | SECTION（自动重跑前置） | TEST_F + 子测试需手动 fixture |
| Matchers | 内置 | 部分支持，gMock 强在 mock |
| Mock | 弱（外部库 Catch2::Catch2WithMocks 提供） | 强（gMock 完整体系） |
| 死亡测试 | REQUIRE_THROWS 等 | ASSERT_DEATH 等 |
| 集成到 IDE | 中（CLI 友好） | 强（VS/xcode 原生） |
| 性能/启动开销 | 中 | 中 |
| 文档质量 | 高（官网 + 教程） | 高 |

**决策建议**：

- **纯单元测试为主，团队偏好可读性** → Catch2 v3
- **需要复杂 mock（接口模拟）** → GoogleTest + gMock
- **项目要嵌入到现有 gtest 工程** → 继续用 GoogleTest
- **新项目、测试场景多是"行为驱动"** → Catch2 BDD

## 常见坑

### 1. SECTION 里改共享对象

```cpp
TEST_CASE("shared counter") {
    int counter = 0;
    
    SECTION("increment once") {
        counter++;
        REQUIRE(counter == 1);
    }
    
    SECTION("increment twice") {
        counter += 2;
        REQUIRE(counter == 2);
    }
}
```

每个 SECTION 各自执行一次 TEST_CASE 的前置——`counter` 永远从 0 开始，不会"加一后变 1 再加二变 3"。

### 2. v2 → v3 迁移

v3 砍掉了所有 v2 的 header-only 入口，需要作为库链接。`CATCH_CONFIG_MAIN` 仍然可用，但更推荐链接 `Catch2::Catch2WithMain`。Matcher's 头文件路径也变了。

### 3. 编译时间

完整 Catch2 单文件编译可能让首次构建慢几秒——CMake 端可以拆出 `Catch2::Catch2`（无 main）并预编译。

## 何时不用 Catch2

- 需要 Google Mock 那样的复杂 mock 链——用 GoogleTest。
- 项目要求 100% 静态链接、单文件部署——选 Catch2 v1.x（已停止维护，不推荐）或 doctest。
- 嵌入式目标（编译时间敏感）——选 doctest，编译开销更小。

## 参考资源

- 仓库：[https://github.com/catchorg/Catch2](https://github.com/catchorg/Catch2)
- 官方文档：[https://catch2-docs.readthedocs.io](https://catch2-docs.readthedocs.io)
- 从 GoogleTest 迁移指南：仓库 wiki 有详细章节
- 替代方案 doctest：[https://github.com/doctest/doctest](https://github.com/doctest/doctest)