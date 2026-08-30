---
title: "googletest：C++ 测试与模拟框架的常青树，1.18 起进入 C++17 时代"
date: 2026-08-31T03:55:00+08:00
slug: "googletest-cpp-testing-mocking-guide"
github_repo: "google/googletest"
source_key: "gh:google/googletest"
description: "GoogleTest 是 Google 的 C++ 测试与模拟框架，GoogleTest 与 GoogleMock 合一维护，39k Stars、1.18.0 起要求 C++17。本文梳理其核心能力、版本演进与上手路径，并说明它近期为何重回 GitHub 趋势榜。"
draft: false
categories: ["技术笔记"]
tags: ["C++", "单元测试", "GoogleTest", "开源"]
---

# googletest：C++ 测试与模拟框架的常青树，1.18 起进入 C++17 时代

## 核心判断

一个 2011 年开源、至今 39,377 Stars 的测试框架，在 2026 年 8 月重新出现在 GitHub 月度趋势榜上——原因不是情怀，而是它在做一轮实打实的现代化：**1.18.0 要求 C++17，官方文档迁到 GitHub Pages，并且计划引入 Abseil 依赖**。对大量还在 C++11/14 上"能用就行"的存量项目来说，这是一次绕不开的升级决策点。

本文回答三个问题：它凭什么常青；1.18 这一代变了什么；新项目或升级项目该怎么上手。

## 它是什么：一套测试 + 一套模拟

这个仓库是原 GoogleTest（测试框架）与 GoogleMock（模拟框架）的合并体——两者本就高度耦合，官方干脆放进同一仓库统一发布。核心能力：

- **xUnit 架构**：业界单元测试的主流骨架，学习成本低；
- **自动测试发现**：测试自动注册，无需手工维护测试清单；
- **断言体系**：相等、不等、异常、浮点等各类断言齐全，且支持用户自定义断言；
- **死亡测试（death test）**：验证代码以预期方式崩溃/退出——C++ 项目特有的刚需，别的语言框架很少专门做；
- **致命与非致命失败分离**：`EXPECT_*` 记录失败继续跑，`ASSERT_*` 立即中止，粒度由你控制；
- **GoogleMock**：用简洁的 DSL 写 mock 类与期望，解决 C++ 依赖注入的样板代码问题；
- **值参数化测试与类型参数化测试**：一套测试逻辑跑多组数据/多种类型。

## 1.18 这一代变了什么

三个来自官方 README 与 release 记录的事实：

1. **C++17 起步**：1.18.x 分支要求至少 C++17，与 Google 内部的 C++ 语言标准支持政策对齐。C++17 的 `std::optional`、结构化绑定等将逐步渗透进 API。
2. **文档新家**：官方文档已上线 GitHub Pages（google.github.io/googletest），推荐直接读站而不是翻仓库目录。入门首选 GoogleTest Primer。
3. **Abseil 在路上**：官方"Coming Soon"明确列出计划依赖 Abseil（Google 的 C++ 基础库）。这对构建系统是信号：未来集成成本里要算上 Abseil。

近期提交也保持高频率（写作时最近一周内仍有针对 `UnorderedElementsAre()` 匹配 sentinel 容器、MSVC 兼容性的修复），维护状态健康。版本节奏：v1.16.0（2025-02）→ v1.17.0（2025-04）→ v1.18.0（2026-08-10）。

## 快速上手：五分钟跑起第一个测试

文档推荐从 [GoogleTest Primer](https://google.github.io/googletest/primer.html) 开始。最简路径（CMake 集成）：

```bash
# 方式一：FetchContent 拉取（推荐新项目）
# CMakeLists.txt 中
# include(FetchContent)
# FetchContent_Declare(googletest
#   GIT_REPOSITORY https://github.com/google/googletest.git
#   GIT_TAG v1.18.0)
# FetchContent_MakeAvailable(googletest)
```

一个测试的样貌：

```cpp
#include <gtest/gtest.h>

TEST(AdditionTest, HandlesPositiveNumbers) {
  EXPECT_EQ(1 + 1, 2);        // 非致命：失败继续
  ASSERT_EQ(2 * 2, 4);        // 致命：失败即停
}
```

配合 GoogleMock 打桩：

```cpp
class MockRepo : public Repo {
 public:
  MOCK_METHOD(std::string, Get, (int id), (override));
};

TEST(FooTest, UsesMock) {
  MockRepo repo;
  EXPECT_CALL(repo, Get(42)).WillOnce(testing::Return("answer"));
  // ... 被测代码调用 repo.Get(42)
}
```

具体构建命令以官方文档为准，此处只示意形态。

## 为什么现在还在趋势榜上

合理推测有三个推力：一是 1.18.0 刚于 2026-08-10 发布，C++17 门槛引发存量项目升级讨论；二是 AI 编程智能体大量生成 C++ 代码，测试框架作为配套被高频拉取；三是 Abseil 依赖预告带来的迁移预期。无论哪个，结论一致：**这套工具在 2026 年仍是 C++ 测试的事实标准之一**，与 Catch2 各占生态位。

## 适用边界与采用建议

- 新 C++ 项目：直接上 v1.18.0，按官方文档用 FetchContent 或包管理器（vcpkg/Conan）集成，一步到位 C++17。
- 存量 C++11/14 项目：先评估编译器工具链能否切 C++17；能切则升，不能切可暂留 1.17.x，但需排入升级计划——Abseil 依赖落地后跳跃成本只会更大。
- 偏好单头文件、BDD 风格或不想引 Google 系依赖的团队：Catch2 仍是合理替代，两者断言能力差距已不大；GoogleTest 的差异优势在死亡测试与 GoogleMock 的深度集成。
- 追求更快编译的模板重项目：注意 GoogleTest 本身以模板实现，超大规模测试套件的编译耗时需要纳入评估。

一句话：如果你在写 C++ 且还没定测试框架，googletest 是默认答案里最安全的那一个；已经在用的，把 1.18 的 C++17 要求当成今年的一次例行升级来做。
